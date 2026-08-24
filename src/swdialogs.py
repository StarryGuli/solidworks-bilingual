# -*- coding: utf-8 -*-
"""
Second pass: make DIALOGEX captions bilingual.

Dialog templates carry their own text (window title, button and static labels),
so the string-table pass never sees them. Every template is round-tripped
(parse -> rebuild -> compare bytes) before it is modified; anything that does
not reproduce itself exactly is left alone.
"""
import ctypes, os, sys
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swbilingual as sb

RT_DIALOG = 5
DS_SETFONT = 0x40

BUTTON, EDIT, STATIC, LISTBOX, SCROLLBAR, COMBOBOX = 0x80, 0x81, 0x82, 0x83, 0x84, 0x85
TEXT_CLASSES = {BUTTON, STATIC}


class R:
    def __init__(self, b):
        self.b, self.o = b, 0

    def u16(self):
        v = int.from_bytes(self.b[self.o:self.o + 2], 'little'); self.o += 2; return v

    def i16(self):
        v = int.from_bytes(self.b[self.o:self.o + 2], 'little', signed=True); self.o += 2; return v

    def u32(self):
        v = int.from_bytes(self.b[self.o:self.o + 4], 'little'); self.o += 4; return v

    def sz_or_ord(self):
        first = self.u16()
        if first == 0:
            return ''
        if first == 0xFFFF:
            return self.u16()          # int = ordinal
        chars = [first]
        while True:
            c = self.u16()
            if c == 0:
                break
            chars.append(c)
        return ''.join(map(chr, chars))

    def align(self):
        self.o = (self.o + 3) & ~3


def _sz(v):
    if isinstance(v, int):
        return (0xFFFF).to_bytes(2, 'little') + v.to_bytes(2, 'little')
    return v.encode('utf-16-le', 'surrogatepass') + b'\0\0'


def parse(blob):
    r = R(blob)
    if r.u16() != 1 or r.u16() != 0xFFFF:
        return None                     # plain DLGTEMPLATE: ambiguous extra data, skip
    d = {'helpID': r.u32(), 'exStyle': r.u32(), 'style': r.u32()}
    n = r.u16()
    d['x'], d['y'], d['cx'], d['cy'] = r.i16(), r.i16(), r.i16(), r.i16()
    d['menu'], d['cls'], d['title'] = r.sz_or_ord(), r.sz_or_ord(), r.sz_or_ord()
    if d['style'] & DS_SETFONT:
        d['font'] = (r.u16(), r.u16(), self_byte(r), self_byte(r), r.sz_or_ord())
    else:
        d['font'] = None
    items = []
    for _ in range(n):
        r.align()
        it = {'helpID': r.u32(), 'exStyle': r.u32(), 'style': r.u32()}
        it['x'], it['y'], it['cx'], it['cy'] = r.i16(), r.i16(), r.i16(), r.i16()
        it['id'] = r.u32()
        it['cls'], it['title'] = r.sz_or_ord(), r.sz_or_ord()
        cnt = r.u16()
        it['extra'] = bytes(blob[r.o:r.o + cnt])
        r.o += cnt
        items.append(it)
    d['items'] = items
    return d


def self_byte(r):
    v = r.b[r.o]; r.o += 1; return v


def build(d):
    out = bytearray()
    out += (1).to_bytes(2, 'little') + (0xFFFF).to_bytes(2, 'little')
    out += d['helpID'].to_bytes(4, 'little') + d['exStyle'].to_bytes(4, 'little') + d['style'].to_bytes(4, 'little')
    out += len(d['items']).to_bytes(2, 'little')
    for v in (d['x'], d['y'], d['cx'], d['cy']):
        out += v.to_bytes(2, 'little', signed=True)
    out += _sz(d['menu']) + _sz(d['cls']) + _sz(d['title'])
    if d['font'] is not None:
        ps, wt, it_, cs, tf = d['font']
        out += ps.to_bytes(2, 'little') + wt.to_bytes(2, 'little') + bytes([it_, cs]) + _sz(tf)
    for it in d['items']:
        while len(out) % 4:
            out += b'\0'
        out += it['helpID'].to_bytes(4, 'little') + it['exStyle'].to_bytes(4, 'little') + it['style'].to_bytes(4, 'little')
        for v in (it['x'], it['y'], it['cx'], it['cy']):
            out += v.to_bytes(2, 'little', signed=True)
        out += it['id'].to_bytes(4, 'little')
        out += _sz(it['cls']) + _sz(it['title'])
        out += len(it['extra']).to_bytes(2, 'little') + it['extra']
    return bytes(out)


def _dlu_width(s):
    """Rough text width in horizontal dialog units: ~4 per ASCII char, ~8 per CJK char."""
    w = 0
    for ch in s:
        w += 8 if sb.CJK.match(ch) else 4
    return w


def grow(items, dlg_cx, idx, extra):
    """Widen item idx by up to `extra` DLU, but only into empty space.

    Stops at the left edge of any control sharing its rows, and at the dialog
    border. Controls that sit inside the item (group boxes) do not block it.
    """
    a = items[idx]
    limit = dlg_cx - 3
    for j, b in enumerate(items):
        if j == idx:
            continue
        vertical_overlap = a['y'] < b['y'] + b['cy'] and b['y'] < a['y'] + a['cy']
        if vertical_overlap and b['x'] >= a['x'] + a['cx']:
            limit = min(limit, b['x'] - 2)
    new_cx = min(a['cx'] + extra, limit - a['x'])
    if new_cx > a['cx']:
        a['cx'] = new_cx


def read_dialogs(path):
    """-> {(name, lang): raw bytes}"""
    h = sb._load(path)
    try:
        if not sb._has_type(h, RT_DIALOG):
            return {}
        out = {}
        for name in sb._names(h, RT_DIALOG):
            if not isinstance(name, int):      # named dialog resources: leave alone
                continue
            for lang in sb._langs(h, RT_DIALOG, name):
                b = sb._bytes(h, RT_DIALOG, name, lang)
                if b:
                    out[(name, lang)] = b
        return out
    finally:
        sb.k.FreeLibrary(h)


def merge_dialog(en_blob, cn_blob, stats):
    de, dc = parse(en_blob), parse(cn_blob)
    if de is None or dc is None:
        stats['unparsed'] += 1
        return None
    if build(de) != en_blob:            # we do not fully understand this one
        stats['roundtrip_fail'] += 1
        return None
    if len(de['items']) != len(dc['items']):
        stats['shape_differs'] += 1
        return None

    changed = False
    m = sb.merge_string(de['title'], dc['title']) if isinstance(de['title'], str) and isinstance(dc['title'], str) else None
    if m:
        de['title'] = m
        changed = True
    for i, (a, b) in enumerate(zip(de['items'], dc['items'])):
        if a['id'] != b['id'] or a['cls'] != b['cls']:
            stats['item_mismatch'] += 1
            return None
        if a['cls'] not in TEXT_CLASSES:
            continue
        if not (isinstance(a['title'], str) and isinstance(b['title'], str)):
            continue
        m = sb.merge_string(a['title'], b['title'])
        if m:
            extra = _dlu_width(m) - _dlu_width(a['title'])
            a['title'] = m
            grow(de['items'], de['cx'], i, extra)
            changed = True
    if not changed:
        return None
    stats['merged'] += 1
    return build(de)


def patch(en_path, cn_path, out_path, stats):
    en = read_dialogs(en_path)
    if not en:
        return 0
    cn_by_name = {}
    for (name, lang), b in read_dialogs(cn_path).items():
        cn_by_name.setdefault(name, b)

    updates = {}
    for (name, lang), blob in en.items():
        cb = cn_by_name.get(name)
        if not cb or cb == blob:
            continue
        new = merge_dialog(blob, cb, stats)
        if new:
            updates[(name, lang)] = new
    if not updates:
        return 0

    h = sb.k.BeginUpdateResourceW(out_path, False)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        for (name, lang), data in updates.items():
            buf = ctypes.create_string_buffer(data, len(data))
            if not sb.k.UpdateResourceW(h, sb.LPVOID(RT_DIALOG), sb.LPVOID(name), lang, buf, len(data)):
                raise ctypes.WinError(ctypes.get_last_error())
    except Exception:
        sb.k.EndUpdateResourceW(h, True)
        raise
    if not sb.k.EndUpdateResourceW(h, False):
        raise ctypes.WinError(ctypes.get_last_error())
    return len(updates)


def main():
    en_dir, cn_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    only = sys.argv[4] if len(sys.argv) > 4 else None
    cn_map = {f.lower(): f for f in os.listdir(cn_dir) if f.lower().endswith('.dll')}
    stats = {'merged': 0, 'unparsed': 0, 'roundtrip_fail': 0, 'shape_differs': 0, 'item_mismatch': 0}
    total = 0
    for f in sorted(os.listdir(out_dir)):
        if not f.lower().endswith('.dll'):
            continue
        if only and f.lower() != only.lower():
            continue
        cn = cn_map.get(f.lower())
        if not cn:
            continue
        try:
            n = patch(os.path.join(en_dir, f), os.path.join(cn_dir, cn), os.path.join(out_dir, f), stats)
        except Exception as e:
            print(f'skip {f}: ERROR {e}')
            continue
        if n:
            print(f'{f:<34} {n:>5} dialogs bilingual')
            total += n
    print('-' * 60)
    print(f'{total} dialogs patched;', stats)


if __name__ == '__main__':
    main()
