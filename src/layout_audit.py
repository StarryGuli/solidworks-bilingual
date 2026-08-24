# -*- coding: utf-8 -*-
"""Audit widened dialogs: no control may newly overlap another or leave the dialog."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swdialogs as sd

orig_dir, new_dir = sys.argv[1], sys.argv[2]


def rects(d):
    return [(i['x'], i['y'], i['cx'], i['cy']) for i in d['items']]


def overlaps(a, b):
    ax, ay, acx, acy = a
    bx, by, bcx, bcy = b
    return ax < bx + bcx and bx < ax + acx and ay < by + bcy and by < ay + acy


new_overlap = out_of_bounds = widened = checked = 0
for f in sorted(os.listdir(new_dir)):
    if not f.lower().endswith('.dll'):
        continue
    try:
        o = sd.read_dialogs(os.path.join(orig_dir, f))
        n = sd.read_dialogs(os.path.join(new_dir, f))
    except Exception:
        continue
    for key, blob in n.items():
        ob = o.get(key)
        if not ob or ob == blob:
            continue
        do, dn = sd.parse(ob), sd.parse(blob)
        if do is None or dn is None or len(do['items']) != len(dn['items']):
            continue
        checked += 1
        ro, rn = rects(do), rects(dn)
        for i in range(len(rn)):
            if rn[i][2] > ro[i][2]:
                widened += 1
            if rn[i][0] + rn[i][2] > dn['cx'] and ro[i][0] + ro[i][2] <= do['cx']:
                out_of_bounds += 1        # only count ones we pushed out
            for j in range(i + 1, len(rn)):
                if overlaps(rn[i], rn[j]) and not overlaps(ro[i], ro[j]):
                    new_overlap += 1

print(f'dialogs checked : {checked}')
print(f'controls widened: {widened}')
print(f'new overlaps    : {new_overlap}')
print(f'past right edge : {out_of_bounds}')
