# -*- coding: utf-8 -*-
"""Generate a small pair of sample language packs.

SOLIDWORKS language packs cannot be redistributed, so this writes a synthetic
pair instead: two resource-only DLLs holding invented English and Chinese
labels, with a version resource so the build-number check has something to
compare. It is enough to run `check` and `preview` end to end and see what the
merge produces, without a SOLIDWORKS installation.

    python tools/make_sample_pack.py samples

The labels below are written for this project and describe an imaginary
modelling program. They are not taken from SOLIDWORKS.
"""
import os
import struct
import sys

VERSION = (1, 0, 0, 1234)
ANCHOR = 'sldresu.dll'

# Invented labels: an imaginary CAD program, so nothing here is anyone's
# translation but ours.
LABELS = [
    ('Extrude Shape', '拉伸形体'),
    ('Round Edge', '圆化边线'),
    ('Bevel Edge', '倒角边线'),
    ('Mirror Body', '镜像实体'),
    ('Hollow Out', '抽壳'),
    ('New Sketch', '新建草图'),
    ('Close Sketch', '关闭草图'),
    ('Measure Distance', '测量距离'),
    ('Front View', '前视图'),
    ('Section View', '剖视图'),
    ('&Save Copy', '保存副本(&S)'),
    ('Rebuild All', '全部重建'),
    ('Material Table', '材质表'),
    ('Show Origin', '显示原点'),
    ('Lock Component', '锁定零部件'),
    # Entries the rules must refuse, so a preview shows the filtering at work.
    ('Saved %s to %s', '已将 %s 保存到 %s'),
    ('Model Files (*.model)', '模型文件 (*.model)'),
    ('https://example.invalid/help', 'https://example.invalid/help'),
    ('The selected geometry cannot be rebuilt because a parent feature is '
     'suppressed.', '所选几何体无法重建，因为其父特征已被压缩。'),
    ('Reset', 'Reset'),
]

RT_STRING = 6
RT_VERSION = 16


def string_blocks(index):
    """-> {block_id: [16 strings]} taking one side of each label pair."""
    blocks = {}
    for position, pair in enumerate(LABELS):
        block_id = position // 16 + 1
        blocks.setdefault(block_id, [''] * 16)[position % 16] = pair[index]
    return blocks


def build_string_block(strings):
    out = bytearray()
    for s in strings:
        encoded = s.encode('utf-16-le')
        out += len(s).to_bytes(2, 'little') + encoded
    return bytes(out)


def build_version_resource():
    """A minimal VS_VERSIONINFO carrying VS_FIXEDFILEINFO."""
    key = 'VS_VERSION_INFO\0'.encode('utf-16-le')
    ms = (VERSION[0] << 16) | VERSION[1]
    ls = (VERSION[2] << 16) | VERSION[3]
    fixed = struct.pack(
        '<13I', 0xFEEF04BD, 0x00010000, ms, ls, ms, ls,
        0x3F, 0, 0x40000, 2, 0, 0, 0)          # DLL, VOS_NT_WINDOWS32
    head = struct.pack('<HHH', 0, len(fixed), 0) + key
    while len(head) % 4:
        head += b'\0'
    body = head + fixed
    # wLength is the first field and is only known once the body is assembled.
    return struct.pack('<H', len(body)) + body[2:]


def _dir(entries, offsets):
    """One IMAGE_RESOURCE_DIRECTORY with its entries."""
    named = 0
    out = struct.pack('<IIHHHH', 0, 0, 0, 0, named, len(entries))
    for (identifier, _), target in zip(entries, offsets):
        out += struct.pack('<II', identifier, target)
    return out


def build_resource_section(resources, section_rva):
    """Lay out a three-level resource directory.

    resources: [(type_id, name_id, language, bytes)]
    """
    by_type = {}
    for type_id, name_id, language, data in resources:
        by_type.setdefault(type_id, []).append((name_id, language, data))

    type_ids = sorted(by_type)
    root_size = 16 + 8 * len(type_ids)
    name_dirs_size = sum(16 + 8 * len(by_type[t]) for t in type_ids)
    lang_dirs_size = sum(16 + 8 for t in type_ids for _ in by_type[t])
    data_entries_count = sum(len(by_type[t]) for t in type_ids)

    name_dirs_start = root_size
    lang_dirs_start = name_dirs_start + name_dirs_size
    data_entries_start = lang_dirs_start + lang_dirs_size
    payload_start = data_entries_start + 16 * data_entries_count
    payload_start = (payload_start + 7) & ~7

    root = bytearray(struct.pack('<IIHHHH', 0, 0, 0, 0, 0, len(type_ids)))
    name_dirs = bytearray()
    lang_dirs = bytearray()
    data_entries = bytearray()
    payload = bytearray()

    name_cursor = name_dirs_start
    lang_cursor = lang_dirs_start
    data_cursor = data_entries_start

    for type_id in type_ids:
        root += struct.pack('<II', type_id, 0x80000000 | name_cursor)
        items = sorted(by_type[type_id])
        name_dirs += struct.pack('<IIHHHH', 0, 0, 0, 0, 0, len(items))
        for name_id, language, data in items:
            name_dirs += struct.pack('<II', name_id, 0x80000000 | lang_cursor)
            lang_cursor += 16 + 8
        name_cursor += 16 + 8 * len(items)

    for type_id in type_ids:
        for name_id, language, data in sorted(by_type[type_id]):
            lang_dirs += struct.pack('<IIHHHH', 0, 0, 0, 0, 0, 1)
            lang_dirs += struct.pack('<II', language, data_cursor)
            data_cursor += 16

    for type_id in type_ids:
        for name_id, language, data in sorted(by_type[type_id]):
            offset = payload_start + len(payload)
            data_entries += struct.pack('<IIII', section_rva + offset, len(data), 0, 0)
            payload += data
            while len(payload) % 8:
                payload += b'\0'

    section = bytearray(root + name_dirs + lang_dirs + data_entries)
    while len(section) < payload_start:
        section += b'\0'
    section += payload
    return bytes(section)


def build_dll(resources):
    """A resource-only PE32+ image: headers, one .rsrc section, no code."""
    file_alignment = 0x200
    section_alignment = 0x1000
    headers_size = 0x200
    rsrc_rva = section_alignment

    section = build_resource_section(resources, rsrc_rva)
    raw_size = (len(section) + file_alignment - 1) // file_alignment * file_alignment
    virtual_size = len(section)
    image_size = section_alignment + \
        (virtual_size + section_alignment - 1) // section_alignment * section_alignment

    dos = bytearray(b'\0' * 0x80)
    dos[0:2] = b'MZ'
    struct.pack_into('<I', dos, 0x3C, 0x80)

    coff = struct.pack('<HHIIIHH', 0x8664, 1, 0, 0, 0, 240, 0x2022)

    optional = struct.pack(
        '<HBBIIIIIQ', 0x20B, 14, 0, 0, 0, 0, 0, 0, 0x180000000)
    optional += struct.pack('<II', section_alignment, file_alignment)
    optional += struct.pack('<HHHHHH', 6, 0, 0, 0, 6, 0)
    optional += struct.pack('<III', 0, image_size, headers_size)
    optional += struct.pack('<IHH', 0, 0x2000, 0)       # DLL characteristics
    optional += struct.pack('<QQQQ', 0x100000, 0x1000, 0x100000, 0x1000)
    optional += struct.pack('<II', 0, 16)               # LoaderFlags, dir count
    directories = [(0, 0)] * 16
    directories[2] = (rsrc_rva, virtual_size)
    for rva, size in directories:
        optional += struct.pack('<II', rva, size)

    section_header = struct.pack(
        '<8sIIIIIIHHI', b'.rsrc\0\0\0', virtual_size, rsrc_rva,
        raw_size, headers_size, 0, 0, 0, 0, 0x40000040)

    image = bytearray(dos + b'PE\0\0' + coff + optional + section_header)
    if len(image) > headers_size:
        raise SystemExit('headers do not fit in %d bytes' % headers_size)
    image += b'\0' * (headers_size - len(image))
    image += section + b'\0' * (raw_size - len(section))
    return bytes(image)


def write_pack(directory, index, language_id):
    os.makedirs(directory, exist_ok=True)
    resources = [(RT_VERSION, 1, 0x409, build_version_resource())]
    for block_id, strings in sorted(string_blocks(index).items()):
        resources.append((RT_STRING, block_id, language_id,
                          build_string_block(strings)))
    path = os.path.join(directory, ANCHOR)
    with open(path, 'wb') as f:
        f.write(build_dll(resources))
    return path


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'samples'
    english = write_pack(os.path.join(root, 'english'), 0, 0x409)
    chinese = write_pack(os.path.join(root, 'chinese'), 1, 0x804)
    print('Wrote %s' % english)
    print('Wrote %s' % chinese)
    print('Try:  python swbilingual-cli.py preview %s %s'
          % (os.path.join(root, 'english'), os.path.join(root, 'chinese')))


if __name__ == '__main__':
    main()
