# -*- coding: utf-8 -*-
"""
Third pass: the XAML string dictionaries (PropertyManager text).

Plain <sys:String x:Key="...">text</sys:String> entries, merged by key.
The English file's own encoding and line endings are preserved byte for byte
outside the replaced text.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swbilingual as sb

ENTRY = re.compile(r'(<sys:String\s+x:Key="([^"]+)"[^>]*>)(.*?)(</sys:String>)', re.S)


def load(path):
    raw = open(path, 'rb').read()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16'), 'utf-16'
    return raw.decode('utf-8-sig'), 'utf-8-sig'


def patch(en_path, cn_path, out_path):
    en_text, enc = load(en_path)
    cn_text, _ = load(cn_path)

    cn_map = {m.group(2): m.group(3) for m in ENTRY.finditer(cn_text)}
    n = [0]

    def repl(m):
        open_tag, key, text, close = m.groups()
        cn = cn_map.get(key)
        if cn is None or 'NoTranslation' in key:
            return m.group(0)
        if '&' in text or '&' in cn or '<' in text or '<' in cn:   # keep escaped markup as is
            return m.group(0)
        merged = sb.merge_string(text.strip(), cn.strip())
        if not merged:
            return m.group(0)
        n[0] += 1
        return open_tag + merged + close

    out = ENTRY.sub(repl, en_text)
    with open(out_path, 'wb') as f:
        f.write(out.encode(enc if enc != 'utf-8-sig' else 'utf-8-sig'))
    return n[0]


if __name__ == '__main__':
    en_dir, cn_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    for name in ['DveDictionary.xaml', 'pmdictionary.xaml']:
        en, cn = os.path.join(en_dir, name), os.path.join(cn_dir, name)
        if os.path.exists(en) and os.path.exists(cn):
            print(f'{name:<24} {patch(en, cn, os.path.join(out_dir, name)):>4} entries bilingual')
