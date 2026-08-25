# -*- coding: utf-8 -*-
"""The pre-flight check is what stops a wrong pair of folders from being merged."""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pipeline


class Inspect(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _dir(self, name, files=()):
        path = os.path.join(self.tmp, name)
        os.makedirs(path)
        for f in files:
            with open(os.path.join(path, f), 'wb'):
                pass
        return path

    def test_missing_folder_is_an_error(self):
        report = pipeline.inspect(os.path.join(self.tmp, 'nope'), self._dir('cn'))
        self.assertFalse(report['ok'])
        self.assertTrue(report['errors'])

    def test_empty_folder_is_an_error(self):
        report = pipeline.inspect(self._dir('en'), self._dir('cn'))
        self.assertFalse(report['ok'])

    def test_folders_without_a_common_dll_are_an_error(self):
        report = pipeline.inspect(self._dir('en', ['a.dll']), self._dir('cn', ['b.dll']))
        self.assertFalse(report['ok'])

    def test_errors_carry_both_languages(self):
        report = pipeline.inspect(self._dir('en', ['a.dll']), self._dir('cn', ['b.dll']))
        for message in report['errors']:
            self.assertTrue(pipeline.text(message, 'en'))
            self.assertTrue(pipeline.text(message, 'zh'))
            self.assertNotEqual(pipeline.text(message, 'en'), pipeline.text(message, 'zh'))

    def test_matching_names_without_version_info_still_pass_with_a_warning(self):
        report = pipeline.inspect(self._dir('en', ['a.dll']), self._dir('cn', ['a.dll']))
        self.assertTrue(report['ok'])
        self.assertTrue(report['warnings'])
        self.assertIsNone(report['version_match'])

    def test_pipeline_error_is_bilingual(self):
        error = pipeline.PipelineError('English wording', '中文措辞')
        self.assertEqual(error.localized('en'), 'English wording')
        self.assertEqual(error.localized('zh'), '中文措辞')
        self.assertEqual(error.localized(), 'English wording')


if __name__ == '__main__':
    unittest.main()
