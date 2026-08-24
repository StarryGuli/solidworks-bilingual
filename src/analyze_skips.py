# -*- coding: utf-8 -*-
"""Why did each string get skipped? Sanity-check the merge filters."""
import os, sys, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swbilingual import read_string_blocks, CJK, MAX_EN, MAX_CN

en_path, cn_path = sys.argv[1], sys.argv[2]
en_b = read_string_blocks(en_path)
cn_b = {}
for (n, l), s in read_string_blocks(cn_path).items():
    cn_b.setdefault(n, s)

def reason(en, cn):
    if not en:
        return None
    if not cn:
        return 'no chinese'
    if en == cn:
        return 'identical'
    if not CJK.search(cn):
        return 'cn not translated'
    if '%' in en or '%' in cn:
        return 'format string (%)'
    if any(c in en or c in cn for c in '\n\r\t'):
        return 'multi-line / tab'
    if '\\' in en or '*.' in en or '://' in en:
        return 'path/filter/url'
    if not re.search(r'[A-Za-z]', en):
        return 'no latin letters'
    if len(en) > MAX_EN or len(cn) > MAX_CN:
        return 'too long'
    return 'MERGED'

counts = collections.Counter()
buckets = collections.defaultdict(list)
for (name, lang), en_strs in en_b.items():
    cn_strs = cn_b.get(name) or [''] * 16
    for i in range(16):
        r = reason(en_strs[i], cn_strs[i])
        if r is None:
            continue
        counts[r] += 1
        if len(buckets[r]) < 6:
            buckets[r].append((en_strs[i], cn_strs[i]))

for r, c in counts.most_common():
    print(f'=== {r}: {c}')
    if r == 'MERGED':
        continue
    for en, cn in buckets[r]:
        print(f'    EN {en[:110]!r}')
        print(f'    CN {cn[:110]!r}')
