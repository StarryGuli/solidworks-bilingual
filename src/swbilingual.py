# -*- coding: utf-8 -*-
"""
SOLIDWORKS bilingual language pack builder.

Takes the English resource DLLs and the matching Chinese ones (same build),
and writes a copy of the English DLL whose string table reads "English 中文".
SOLIDWORKS keeps loading lang\english, but the UI shows both languages.

Only short UI labels are merged. Long messages, printf format strings,
multi-line blobs and internal registration strings are left untouched.
"""
import ctypes, os, re, shutil, sys
from ctypes import wintypes

k = ctypes.WinDLL('kernel32', use_last_error=True)

LOAD_LIBRARY_AS_DATAFILE = 0x02
RT_STRING = 6

LPVOID = ctypes.c_void_p
LONG_PTR = ctypes.c_ssize_t

ENUMRESNAMEPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, LPVOID, LPVOID, LPVOID, LONG_PTR)
ENUMRESLANGPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, LPVOID, LPVOID, LPVOID, wintypes.WORD, LONG_PTR)
ENUMRESTYPEPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, LPVOID, LPVOID, LONG_PTR)

k.LoadLibraryExW.restype = LPVOID
k.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, LPVOID, wintypes.DWORD]
k.FreeLibrary.argtypes = [LPVOID]
k.FindResourceExW.restype = LPVOID
k.FindResourceExW.argtypes = [LPVOID, LPVOID, LPVOID, wintypes.WORD]
k.LoadResource.restype = LPVOID
k.LoadResource.argtypes = [LPVOID, LPVOID]
k.LockResource.restype = LPVOID
k.LockResource.argtypes = [LPVOID]
k.SizeofResource.restype = wintypes.DWORD
k.SizeofResource.argtypes = [LPVOID, LPVOID]
k.EnumResourceTypesW.argtypes = [LPVOID, ENUMRESTYPEPROC, LONG_PTR]
k.EnumResourceNamesW.argtypes = [LPVOID, LPVOID, ENUMRESNAMEPROC, LONG_PTR]
k.EnumResourceLanguagesW.argtypes = [LPVOID, LPVOID, LPVOID, ENUMRESLANGPROC, LONG_PTR]
k.BeginUpdateResourceW.restype = LPVOID
k.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
k.UpdateResourceW.argtypes = [LPVOID, LPVOID, LPVOID, wintypes.WORD, LPVOID, wintypes.DWORD]
k.EndUpdateResourceW.argtypes = [LPVOID, wintypes.BOOL]


# ---------------------------------------------------------------- read side

def _id(v):
    v = v or 0
    return ctypes.wstring_at(v) if v >> 16 else int(v)


def _load(path):
    h = k.LoadLibraryExW(path, None, LOAD_LIBRARY_AS_DATAFILE)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    return h


def _has_type(h, rtype):
    found = []
    def cb(hm, t, p):
        if _id(t) == rtype:
            found.append(True)
        return True
    k.EnumResourceTypesW(h, ENUMRESTYPEPROC(cb), 0)
    return bool(found)


def _names(h, rtype):
    out = []
    def cb(hm, t, name, p):
        out.append(_id(name))
        return True
    k.EnumResourceNamesW(h, LPVOID(rtype), ENUMRESNAMEPROC(cb), 0)
    return out


def _langs(h, rtype, name):
    out = []
    def cb(hm, t, n, lang, p):
        out.append(lang)
        return True
    k.EnumResourceLanguagesW(h, LPVOID(rtype), LPVOID(name), ENUMRESLANGPROC(cb), 0)
    return out


def _bytes(h, rtype, name, lang):
    hr = k.FindResourceExW(h, LPVOID(rtype), LPVOID(name), lang)
    if not hr:
        return None
    hg = k.LoadResource(h, hr)
    return ctypes.string_at(k.LockResource(hg), k.SizeofResource(h, hr))


def _parse_block(blob):
    """A string-table block holds 16 length-prefixed UTF-16 strings."""
    out = [''] * 16
    off = 0
    for i in range(16):
        if off + 2 > len(blob):
            break
        ln = int.from_bytes(blob[off:off + 2], 'little')
        off += 2
        if ln:
            out[i] = blob[off:off + ln * 2].decode('utf-16-le', 'surrogatepass')
            off += ln * 2
    return out


def _build_block(strings):
    buf = bytearray()
    for s in strings:
        enc = s.encode('utf-16-le', 'surrogatepass')
        buf += len(s).to_bytes(2, 'little') + enc
    return bytes(buf)


def read_string_blocks(path):
    """-> {(block_name, lang): [16 strings]}"""
    h = _load(path)
    try:
        if not _has_type(h, RT_STRING):
            return {}
        blocks = {}
        for name in _names(h, RT_STRING):
            if not isinstance(name, int):
                continue
            for lang in _langs(h, RT_STRING, name):
                b = _bytes(h, RT_STRING, name, lang)
                if b:
                    blocks[(name, lang)] = _parse_block(b)
        return blocks
    finally:
        k.FreeLibrary(h)


# ------------------------------------------------------------- merge rules

CJK = re.compile('[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef\u3000-\u303f]')
ACCEL_CN = re.compile(r'\s*[（(]&[A-Za-z0-9][）)]\s*')
MAX_EN = 60          # only short UI labels get a Chinese twin
MAX_CN = 40


def mergeable(en, cn):
    if not en or not cn or en == cn:
        return False
    if not CJK.search(cn):          # not actually translated / not text
        return False
    if len(en) > MAX_EN or len(cn) > MAX_CN:
        return False
    if '%' in en or '%' in cn:      # printf format string - never touch
        return False
    if any(c in en or c in cn for c in '\n\r\t'):
        return False
    if '\\' in en or '*.' in en or '://' in en:   # paths, file filters, urls
        return False
    if not re.search(r'[A-Za-z]', en):            # numbers/symbols only
        return False
    return True


def merge(en, cn):
    cn2 = ACCEL_CN.sub('', cn)
    if '&' in en:
        cn2 = cn2.replace('&', '')
    return f'{en} {cn2}'.strip()


def merge_string(en, cn):
    """Bilingual version of one table entry, or None to leave it alone.

    Toolbar labels live in MFC two-part entries, "long description\\nCommand Name",
    so those are handled per segment: the label gets a Chinese twin, the
    description stays English. Anything with more segments is a registration
    blob (file types, ProgIDs) and is never touched.
    """
    if not en or not cn or en == cn:
        return None
    if '%' in en or '%' in cn:
        return None
    if any(c in en or c in cn for c in '\r\t'):
        return None

    if '\n' in en or '\n' in cn:
        pe, pc = en.split('\n'), cn.split('\n')
        if len(pe) != 2 or len(pc) != 2 or not all(pe) or not all(pc):
            return None
        out, changed = [], False
        for a, b in zip(pe, pc):
            if mergeable(a, b):
                out.append(merge(a, b))
                changed = True
            else:
                out.append(a)
        return '\n'.join(out) if changed else None

    return merge(en, cn) if mergeable(en, cn) else None


# ---------------------------------------------------------------- patching

def patch_file(en_path, cn_path, out_path, samples=None, sample_cap=0):
    en_blocks = read_string_blocks(en_path)
    if not en_blocks:
        return 0, 0
    cn_blocks = read_string_blocks(cn_path)
    # Chinese pack may tag resources with a different LANGID - index by block id.
    cn_by_name = {}
    for (name, lang), strs in cn_blocks.items():
        cn_by_name.setdefault(name, strs)

    updates = {}
    merged = total = 0
    for (name, lang), en_strs in en_blocks.items():
        cn_strs = cn_by_name.get(name)
        if not cn_strs:
            continue
        new = list(en_strs)
        changed = False
        for i in range(16):
            en, cn = en_strs[i], cn_strs[i]
            if en:
                total += 1
            m = merge_string(en, cn)
            if m is not None:
                new[i] = m
                changed = True
                merged += 1
                if samples is not None and len(samples) < sample_cap:
                    samples.append(m)
        if changed:
            updates[(name, lang)] = new

    if not updates:
        return 0, total

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    shutil.copy2(en_path, out_path)
    h = k.BeginUpdateResourceW(out_path, False)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        for (name, lang), strs in updates.items():
            data = _build_block(strs)
            buf = ctypes.create_string_buffer(data, len(data))
            if not k.UpdateResourceW(h, LPVOID(RT_STRING), LPVOID(name), lang, buf, len(data)):
                raise ctypes.WinError(ctypes.get_last_error())
    except Exception:
        k.EndUpdateResourceW(h, True)   # discard
        raise
    if not k.EndUpdateResourceW(h, False):
        raise ctypes.WinError(ctypes.get_last_error())
    return merged, total


def main():
    en_dir, cn_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    only = sys.argv[4] if len(sys.argv) > 4 else None

    files = [f for f in os.listdir(en_dir) if f.lower().endswith('.dll')]
    if only:
        files = [f for f in files if f.lower() == only.lower()]
    cn_map = {f.lower(): f for f in os.listdir(cn_dir) if f.lower().endswith('.dll')}

    grand_m = grand_t = 0
    patched = skipped = []
    patched, skipped = [], []
    for f in sorted(files):
        cn_name = cn_map.get(f.lower())
        if not cn_name:
            skipped.append((f, 'no Chinese counterpart'))
            continue
        samples = []
        try:
            m, t = patch_file(os.path.join(en_dir, f), os.path.join(cn_dir, cn_name),
                              os.path.join(out_dir, f), samples, 8 if only else 0)
        except Exception as e:
            skipped.append((f, f'ERROR {e}'))
            continue
        grand_m += m
        grand_t += t
        if m:
            patched.append((f, m, t))
        else:
            skipped.append((f, 'nothing mergeable'))
        if only:
            for s in samples:
                print('   ', s)

    for f, m, t in patched:
        print(f'{f:<34} {m:>6} / {t:<6} strings bilingual')
    print('-' * 60)
    for f, why in skipped:
        print(f'skip {f:<30} {why}')
    print('-' * 60)
    print(f'{len(patched)} DLL patched, {grand_m} strings made bilingual (of {grand_t} non-empty)')


if __name__ == '__main__':
    main()
