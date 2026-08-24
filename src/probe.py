import ctypes, sys
from ctypes import wintypes

k = ctypes.WinDLL('kernel32', use_last_error=True)
LOAD_LIBRARY_AS_DATAFILE = 0x02
RT_STRING = 6
RT_MENU = 4
RT_DIALOG = 5

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


def load(path):
    h = k.LoadLibraryExW(path, None, LOAD_LIBRARY_AS_DATAFILE)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    return h


def _id(v):
    """Resource id/name: ints < 0x10000 are numeric ids, else pointer to a wide string."""
    v = v or 0
    if v >> 16:
        return ctypes.wstring_at(v)
    return int(v)


def res_types(h):
    out = []
    def cb(hm, t, p):
        out.append(_id(t))
        return True
    k.EnumResourceTypesW(h, ENUMRESTYPEPROC(cb), 0)
    return out


def res_names(h, rtype):
    out = []
    def cb(hm, t, name, p):
        out.append(_id(name))
        return True
    k.EnumResourceNamesW(h, LPVOID(rtype), ENUMRESNAMEPROC(cb), 0)
    return out


def res_langs(h, rtype, name):
    out = []
    def cb(hm, t, n, lang, p):
        out.append(lang)
        return True
    k.EnumResourceLanguagesW(h, LPVOID(rtype), LPVOID(name), ENUMRESLANGPROC(cb), 0)
    return out


def res_bytes(h, rtype, name, lang):
    hr = k.FindResourceExW(h, LPVOID(rtype), LPVOID(name), lang)
    if not hr:
        return None
    hg = k.LoadResource(h, hr)
    ptr = k.LockResource(hg)
    size = k.SizeofResource(h, hr)
    return ctypes.string_at(ptr, size)


def parse_stringtable(blob, block_id):
    """RT_STRING block N holds string ids (N-1)*16 .. (N-1)*16+15"""
    res = {}
    off = 0
    base = (block_id - 1) * 16
    for i in range(16):
        if off + 2 > len(blob):
            break
        ln = int.from_bytes(blob[off:off+2], 'little')
        off += 2
        if ln:
            res[base + i] = blob[off:off+ln*2].decode('utf-16-le', 'replace')
            off += ln * 2
    return res


def dump(path):
    h = load(path)
    types = res_types(h)
    info = {'types': types}
    strings = {}
    if RT_STRING in [t for t in types if isinstance(t, int)]:
        for name in res_names(h, RT_STRING):
            for lang in res_langs(h, RT_STRING, name):
                b = res_bytes(h, RT_STRING, name, lang)
                if b:
                    strings.update(parse_stringtable(b, name))
    info['strings'] = strings
    info['menus'] = len(res_names(h, RT_MENU)) if RT_MENU in [t for t in types if isinstance(t, int)] else 0
    info['dialogs'] = len(res_names(h, RT_DIALOG)) if RT_DIALOG in [t for t in types if isinstance(t, int)] else 0
    k.FreeLibrary(h)
    return info


if __name__ == '__main__':
    en = dump(sys.argv[1])
    cn = dump(sys.argv[2])
    print('EN types:', en['types'])
    print('CN types:', cn['types'])
    print('EN strings:', len(en['strings']), 'menus:', en['menus'], 'dialogs:', en['dialogs'])
    print('CN strings:', len(cn['strings']), 'menus:', cn['menus'], 'dialogs:', cn['dialogs'])
    common = sorted(set(en['strings']) & set(cn['strings']))
    print('common ids:', len(common), 'en-only:', len(set(en['strings']) - set(cn['strings'])), 'cn-only:', len(set(cn['strings']) - set(en['strings'])))
    shown = 0
    for i in common:
        e, c = en['strings'][i], cn['strings'][i]
        if e != c and e.strip() and c.strip():
            print(f'  {i}: {e!r}  ||  {c!r}')
            shown += 1
            if shown >= 15:
                break
