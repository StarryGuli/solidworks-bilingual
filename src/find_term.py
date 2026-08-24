# -*- coding: utf-8 -*-
"""Show EN/CN pairs for strings containing a term, with their skip status."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swbilingual import read_string_blocks, mergeable

en_path, cn_path, term = sys.argv[1], sys.argv[2], sys.argv[3]
en_b = read_string_blocks(en_path)
cn_b = {}
for (n, l), s in read_string_blocks(cn_path).items():
    cn_b.setdefault(n, s)

shown = 0
for (name, lang), en_strs in sorted(en_b.items()):
    cn_strs = cn_b.get(name) or [''] * 16
    for i in range(16):
        en, cn = en_strs[i], cn_strs[i]
        if en and term.lower() in en.lower():
            sid = (name - 1) * 16 + i
            print(f'[{sid}] merge={mergeable(en, cn)}')
            print(f'   EN {en[:160]!r}')
            print(f'   CN {cn[:160]!r}')
            shown += 1
            if shown >= 12:
                sys.exit()
