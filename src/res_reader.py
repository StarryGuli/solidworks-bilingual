# -*- coding: utf-8 -*-
"""Read string tables straight out of a PE file, without the Windows loader.

The build passes use the Windows resource API, which is authoritative and also
the only way to write resources back. This reader is for inspection only: it
lets `preview` and the test suite examine real language packs from any
operating system.
"""
import struct

import pe_version
from pe_version import NotAPEFile, _sections, _to_offset, _u16, _u32

RT_STRING = 6
RT_DIALOG = 5


def _walk_type(blob, base, off, want_type, depth=0, name=None, out=None):
    """Collect (name, language, rva, size) for one resource type."""
    n_named = _u16(blob, off + 12)
    n_id = _u16(blob, off + 14)
    for i in range(n_named + n_id):
        e = off + 16 + 8 * i
        entry_name = _u32(blob, e)
        entry = _u32(blob, e + 4)
        if depth == 0 and entry_name != want_type:
            continue
        if entry & 0x80000000:
            _walk_type(blob, base, base + (entry & 0x7FFFFFFF), want_type,
                       depth + 1, entry_name if depth == 1 else name, out)
        elif depth == 2:
            out.append((name, entry_name,
                        _u32(blob, base + entry), _u32(blob, base + entry + 4)))
    return out


def read_resources(path, rtype):
    """-> {(name, language): bytes} for one resource type."""
    with open(path, 'rb') as f:
        blob = f.read()
    secs, rsrc_rva = _sections(blob)
    if not rsrc_rva:
        return {}
    base = _to_offset(secs, rsrc_rva)
    if base is None:
        return {}
    entries = _walk_type(blob, base, base, rtype, out=[])
    result = {}
    for name, lang, rva, size in entries:
        start = _to_offset(secs, rva)
        if start is not None:
            result[(name, lang)] = blob[start:start + size]
    return result


def parse_string_block(data):
    """A string-table block holds 16 length-prefixed UTF-16 strings."""
    out = [''] * 16
    off = 0
    for i in range(16):
        if off + 2 > len(data):
            break
        ln = int.from_bytes(data[off:off + 2], 'little')
        off += 2
        if ln:
            chunk = data[off:off + ln * 2]
            if len(chunk) < ln * 2:          # truncated or damaged resource
                break
            out[i] = chunk.decode('utf-16-le', 'surrogatepass')
            off += ln * 2
    return out


def read_string_blocks(path):
    """-> {(block_name, language): [16 strings]}, same shape as the build pass."""
    blocks = {}
    for (name, lang), data in read_resources(path, RT_STRING).items():
        if isinstance(name, int) and data:
            blocks[(name, lang)] = parse_string_block(data)
    return blocks


def string_pairs(en_path, cn_path):
    """Line up English and Chinese strings by resource id.

    -> [(string_id, english, chinese)] for every id present on both sides.
    """
    en_blocks = read_string_blocks(en_path)
    cn_by_name = {}
    for (name, lang), strs in read_string_blocks(cn_path).items():
        cn_by_name.setdefault(name, strs)

    pairs = []
    for (name, lang), en_strs in sorted(en_blocks.items()):
        cn_strs = cn_by_name.get(name)
        if not cn_strs:
            continue
        for i in range(16):
            en, cn = en_strs[i], cn_strs[i]
            if en and cn:
                pairs.append(((name - 1) * 16 + i, en, cn))
    return pairs
