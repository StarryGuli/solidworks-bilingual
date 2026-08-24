# -*- coding: utf-8 -*-
"""Read a PE file's VERSIONINFO without loading it.

Pure file parsing, no Windows API, so the build-number check also works when
the packs are inspected from another machine. Used to refuse a merge between
an English and a Chinese pack from different SOLIDWORKS builds - their
resource IDs do not line up and the result would be garbage.
"""
import os
import struct

RT_VERSION = 16
VS_FFI_SIGNATURE = 0xFEEF04BD


class NotAPEFile(Exception):
    pass


def _u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def _u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def _sections(blob):
    """-> (list of (va, vsize, raw_ptr, raw_size), resource_dir_rva)"""
    if blob[:2] != b'MZ':
        raise NotAPEFile('not an MZ image')
    pe = _u32(blob, 0x3C)
    if blob[pe:pe + 4] != b'PE\0\0':
        raise NotAPEFile('no PE signature')
    coff = pe + 4
    n_sections = _u16(blob, coff + 2)
    opt_size = _u16(blob, coff + 16)
    opt = coff + 20
    magic = _u16(blob, opt)
    if magic == 0x20B:                      # PE32+
        dir_off = opt + 112
    elif magic == 0x10B:                    # PE32
        dir_off = opt + 96
    else:
        raise NotAPEFile('unknown optional header magic 0x%X' % magic)
    n_dirs = _u32(blob, dir_off - 4)
    rsrc_rva = _u32(blob, dir_off + 8 * 2) if n_dirs > 2 else 0

    secs = []
    st = opt + opt_size
    for i in range(n_sections):
        s = st + 40 * i
        secs.append((_u32(blob, s + 12), _u32(blob, s + 8),
                     _u32(blob, s + 20), _u32(blob, s + 16)))
    return secs, rsrc_rva


def _to_offset(secs, rva):
    for va, vsize, ptr, raw in secs:
        if va <= rva < va + max(vsize, raw):
            return ptr + (rva - va)
    return None


def _walk(blob, base, off, want_type, depth=0):
    """Descend type -> name -> language, return the first data entry found."""
    n_named = _u16(blob, off + 12)
    n_id = _u16(blob, off + 14)
    for i in range(n_named + n_id):
        e = off + 16 + 8 * i
        name = _u32(blob, e)
        entry = _u32(blob, e + 4)
        if depth == 0 and name != want_type:      # named types included
            continue
        if entry & 0x80000000:
            found = _walk(blob, base, base + (entry & 0x7FFFFFFF), want_type, depth + 1)
            if found:
                return found
        else:
            return _u32(blob, base + entry), _u32(blob, base + entry + 4)
    return None


def file_version(path):
    """-> 'a.b.c.d', or None when the file carries no VERSIONINFO."""
    with open(path, 'rb') as f:
        blob = f.read()
    secs, rsrc_rva = _sections(blob)
    if not rsrc_rva:
        return None
    base = _to_offset(secs, rsrc_rva)
    if base is None:
        return None
    hit = _walk(blob, base, base, RT_VERSION)
    if not hit:
        return None
    data_rva, size = hit
    start = _to_offset(secs, data_rva)
    if start is None:
        return None
    chunk = blob[start:start + size]
    sig = struct.pack('<I', VS_FFI_SIGNATURE)
    i = chunk.find(sig)
    if i < 0:
        return None
    ms, ls = _u32(chunk, i + 8), _u32(chunk, i + 12)
    return '%d.%d.%d.%d' % (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)


# The version of this file is the version SOLIDWORKS reports for the pack.
ANCHOR = 'sldresu.dll'


def pack_version(directory):
    """Version of a language pack directory, read from its anchor DLL."""
    p = os.path.join(directory, ANCHOR)
    if not os.path.exists(p):
        for f in sorted(os.listdir(directory)):
            if f.lower() == ANCHOR:
                p = os.path.join(directory, f)
                break
        else:
            return None
    try:
        return file_version(p)
    except (NotAPEFile, OSError, struct.error):
        return None


if __name__ == '__main__':
    import sys
    for d in sys.argv[1:]:
        print('%-40s %s' % (d, pack_version(d) or '(unknown)'))
