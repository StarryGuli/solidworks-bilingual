# -*- coding: utf-8 -*-
"""String-table blocks hold sixteen length-prefixed UTF-16 strings. The reader
used for previews and the writer used by the build pass must agree exactly.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import res_reader
import rules_access

sb = rules_access.import_rules()


class StringBlocks(unittest.TestCase):

    def test_reader_and_writer_agree(self):
        strings = ['Fillet', '', 'Extruded Boss/Base 拉伸凸台/基体', 'OK'] + [''] * 12
        blob = sb._build_block(strings)
        self.assertEqual(res_reader.parse_string_block(blob), strings)
        self.assertEqual(sb._parse_block(blob), strings)

    def test_a_full_block_round_trips(self):
        strings = ['条目 %d' % i for i in range(16)]
        self.assertEqual(res_reader.parse_string_block(sb._build_block(strings)), strings)

    def test_truncated_block_does_not_raise(self):
        blob = sb._build_block(['Fillet'] + [''] * 15)
        self.assertEqual(res_reader.parse_string_block(blob[:3])[0], '')


if __name__ == '__main__':
    unittest.main()
