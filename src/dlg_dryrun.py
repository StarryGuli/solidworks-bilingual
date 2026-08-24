# -*- coding: utf-8 -*-
"""Dry run: how many dialog templates round-trip cleanly, and what would change."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swbilingual as sb
import swdialogs as sd

en_dir, cn_dir = sys.argv[1], sys.argv[2]
only = sys.argv[3] if len(sys.argv) > 3 else None

cn_map = {f.lower(): f for f in os.listdir(cn_dir) if f.lower().endswith('.dll')}
grand = collections.Counter()
samples = []

for f in sorted(os.listdir(en_dir)):
    if not f.lower().endswith('.dll'):
        continue
    if only and f.lower() != only.lower():
        continue
    cn = cn_map.get(f.lower())
    if not cn:
        continue
    en = sd.read_dialogs(os.path.join(en_dir, f))
    if not en:
        continue
    cn_by = {}
    for (n, l), b in sd.read_dialogs(os.path.join(cn_dir, cn)).items():
        cn_by.setdefault(n, b)
    for (name, lang), blob in en.items():
        grand['dialogs'] += 1
        cb = cn_by.get(name)
        if not cb:
            grand['no cn'] += 1
            continue
        de, dc = sd.parse(blob), sd.parse(cb)
        if de is None or dc is None:
            grand['not DIALOGEX'] += 1
            continue
        if sd.build(de) != blob:
            grand['roundtrip FAIL'] += 1
            continue
        grand['roundtrip ok'] += 1
        if len(de['items']) != len(dc['items']):
            grand['shape differs'] += 1
            continue
        for a, b in zip(de['items'], dc['items']):
            if a['cls'] in sd.TEXT_CLASSES and isinstance(a['title'], str) and isinstance(b['title'], str):
                m = sb.merge_string(a['title'], b['title'])
                if m:
                    grand['captions merged'] += 1
                    if len(samples) < 14:
                        samples.append((f, m, a['cx']))

for k, v in grand.most_common():
    print(f'{k:<18} {v}')
print('--- samples (cx = control width in dialog units) ---')
for f, m, cx in samples:
    print(f'  [{f} cx={cx}] {m}')
