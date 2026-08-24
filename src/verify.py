# -*- coding: utf-8 -*-
"""Verify every patched DLL still loads and kept all of its resources."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swbilingual as sb

orig_dir, new_dir = sys.argv[1], sys.argv[2]


def inventory(path):
    h = sb._load(path)
    try:
        types = []
        def cb(hm, t, p):
            types.append(sb._id(t))
            return True
        sb.k.EnumResourceTypesW(h, sb.ENUMRESTYPEPROC(cb), 0)
        inv = {}
        for t in types:
            key = t if isinstance(t, int) else str(t)
            inv[key] = len(sb._names(h, t)) if isinstance(t, int) else None
        return inv
    finally:
        sb.k.FreeLibrary(h)


bad, ok, cjk_total = [], 0, 0
for f in sorted(os.listdir(new_dir)):
    if not f.lower().endswith('.dll'):
        continue
    o, n = os.path.join(orig_dir, f), os.path.join(new_dir, f)
    try:
        io_, in_ = inventory(o), inventory(n)
    except Exception as e:
        bad.append((f, f'load failed: {e}'))
        continue
    missing = {k: v for k, v in io_.items() if k not in in_}
    shrunk = {k: (v, in_[k]) for k, v in io_.items()
              if k in in_ and isinstance(v, int) and in_[k] is not None and in_[k] < v}
    if missing or shrunk:
        bad.append((f, f'missing={missing} shrunk={shrunk}'))
        continue
    ok += 1
    # spot-check that Chinese actually landed in the string table
    for strs in sb.read_string_blocks(n).values():
        cjk_total += sum(1 for s in strs if s and sb.CJK.search(s))

print(f'{ok} DLL verified, {len(bad)} problems')
for f, why in bad:
    print(f'  !! {f}: {why}')
print(f'{cjk_total} string entries now contain Chinese')
