# -*- coding: utf-8 -*-
"""Look up how key SOLIDWORKS commands read in a patched DLL."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swbilingual import read_string_blocks

TERMS = ['Extruded Boss', 'Fillet', 'Hole Wizard', 'Mate', 'Smart Dimension', 'Revolved Boss',
         'Sheet Metal', 'Base Flange', 'Sketch', 'Chamfer', 'Linear Pattern', 'Shell', 'Rib',
         'Save As', 'Open', 'Rebuild', 'Section View', 'Front Plane', 'Weldment', 'Draft',
         'Loft', 'Sweep', 'Mirror', 'Assembly', 'Insert Components', 'Measure', 'Mass Properties']

allstr = []
for strs in read_string_blocks(sys.argv[1]).values():
    allstr.extend(s for s in strs if s)

for t in TERMS:
    hits = [s for s in allstr if s.startswith(t) and len(s) < 70]
    hits.sort(key=len)
    print(f'{t:<20} -> ' + (hits[0] if hits else '(no short hit)'))
