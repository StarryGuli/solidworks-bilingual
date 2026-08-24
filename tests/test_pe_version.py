# -*- coding: utf-8 -*-
"""Build numbers gate the whole operation: merging packs from different builds
produces nonsense, so reading the version has to be reliable.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pe_version

SAMPLE = os.environ.get('SWBILINGUAL_SAMPLE_PACK')


class Version(unittest.TestCase):

    def test_non_pe_input_is_reported(self):
        self.assertRaises(pe_version.NotAPEFile, pe_version.file_version, __file__)

    def test_missing_anchor_returns_none(self):
        self.assertIsNone(pe_version.pack_version(os.path.dirname(__file__)))

    @unittest.skipUnless(SAMPLE, 'set SWBILINGUAL_SAMPLE_PACK to a language pack folder')
    def test_reads_the_version_of_a_real_pack(self):
        version = pe_version.pack_version(SAMPLE)
        self.assertIsNotNone(version)
        self.assertEqual(len(version.split('.')), 4)
        for part in version.split('.'):
            self.assertTrue(part.isdigit())


if __name__ == '__main__':
    unittest.main()
