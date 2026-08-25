# -*- coding: utf-8 -*-
"""The sample pack is how someone without SOLIDWORKS sees the tool work.

It is generated rather than copied, because real language packs cannot be
redistributed. These tests keep the generator honest: the files it writes must
be readable by the same code that reads a real pack, and the merge must both
produce the bilingual labels and refuse the entries it is supposed to refuse.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pe_version
import pipeline

GENERATOR = os.path.join(ROOT, 'tools', 'make_sample_pack.py')


class SamplePack(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        subprocess.run([sys.executable, GENERATOR, cls.tmp],
                       check=True, stdout=subprocess.DEVNULL)
        cls.english = os.path.join(cls.tmp, 'english')
        cls.chinese = os.path.join(cls.tmp, 'chinese')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_generated_files_carry_a_readable_version(self):
        self.assertEqual(pe_version.pack_version(self.english), '1.0.0.1234')
        self.assertEqual(pe_version.pack_version(self.chinese), '1.0.0.1234')

    def test_the_pair_passes_the_pre_flight_check(self):
        report = pipeline.inspect(self.english, self.chinese)
        self.assertTrue(report['ok'], report['errors'])
        self.assertTrue(report['version_match'])
        self.assertEqual(report['paired_dll_count'], 1)

    def test_the_preview_merges_the_short_labels(self):
        merged = {s['merged'] for s in
                  pipeline.preview(self.english, self.chinese, limit=100)['samples']}
        self.assertIn('Extrude Shape 拉伸形体', merged)
        self.assertIn('Measure Distance 测量距离', merged)
        self.assertIn('&Save Copy 保存副本', merged)   # accelerator marker removed

    def test_the_preview_refuses_what_the_rules_exclude(self):
        result = pipeline.preview(self.english, self.chinese, limit=100)
        merged = ' | '.join(s['merged'] for s in result['samples'])
        self.assertNotIn('%s', merged)              # format string
        self.assertNotIn('*.model', merged)         # file filter
        self.assertNotIn('example.invalid', merged)  # url
        self.assertNotIn('cannot be rebuilt', merged)  # long sentence
        self.assertNotIn('Reset', merged)           # identical on both sides

    def test_the_counts_are_the_documented_ones(self):
        counts = pipeline.preview(self.english, self.chinese, limit=100)['counts']
        self.assertEqual(counts['pairs'], 20)
        self.assertEqual(counts['mergeable'], 15)

    def test_the_pack_committed_to_the_repository_is_current(self):
        committed = os.path.join(ROOT, 'samples', 'english', 'sldresu.dll')
        if not os.path.exists(committed):
            self.skipTest('the sample pack has not been generated yet')
        with open(committed, 'rb') as f:
            stored = f.read()
        with open(os.path.join(self.english, 'sldresu.dll'), 'rb') as f:
            fresh = f.read()
        self.assertEqual(stored, fresh,
                         'samples/ is stale: run python tools/make_sample_pack.py samples')


if __name__ == '__main__':
    unittest.main()
