# -*- coding: utf-8 -*-
"""Count resources by type for a DLL."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swbilingual as sb

NAMES = {1: 'CURSOR', 2: 'BITMAP', 3: 'ICON', 4: 'MENU', 5: 'DIALOG', 6: 'STRING',
         9: 'ACCELERATOR', 10: 'RCDATA', 12: 'GROUP_CURSOR', 14: 'GROUP_ICON',
         16: 'VERSION', 23: 'HTML', 24: 'MANIFEST'}

h = sb._load(sys.argv[1])
types = []
def cb(hm, t, p):
    types.append(sb._id(t))
    return True
sb.k.EnumResourceTypesW(h, sb.ENUMRESTYPEPROC(cb), 0)
for t in types:
    if isinstance(t, int):
        n = len(sb._names(h, t))
        print(f'  {NAMES.get(t, t):<14} {n}')
    else:
        print(f'  {t!r:<14} (named type)')
