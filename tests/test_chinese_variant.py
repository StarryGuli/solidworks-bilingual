# -*- coding: utf-8 -*-
"""Telling the two Chinese packs apart.

SOLIDWORKS ships Chinese and Chinese Simplified as separate languages, and
installations disagree about which folder holds which: a folder named `chinese`
may contain Traditional Chinese on one machine and Simplified on another. The
folder name therefore cannot decide it; the content has to.
"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import pipeline

SIMPLIFIED = ['圆角', '边线', '显示视图', '参数设置', '关闭窗口', '选择对齐', '实体图层']
TRADITIONAL = ['圓角', '邊線', '顯示視圖', '參數設置', '關閉窗口', '選擇對齊', '實體圖層']


class Detection(unittest.TestCase):

    def test_simplified_text_is_recognised(self):
        self.assertEqual(pipeline.chinese_variant(SIMPLIFIED), 'simplified')

    def test_traditional_text_is_recognised(self):
        self.assertEqual(pipeline.chinese_variant(TRADITIONAL), 'traditional')

    def test_a_sample_too_small_to_judge_says_so(self):
        self.assertIsNone(pipeline.chinese_variant(['圆角']))

    def test_english_text_says_nothing(self):
        self.assertIsNone(pipeline.chinese_variant(['Fillet', 'Edge', 'Close']))

    def test_a_mixed_sample_says_nothing(self):
        self.assertIsNone(pipeline.chinese_variant(SIMPLIFIED + TRADITIONAL))


class Selection(unittest.TestCase):
    """pick_chinese_pack must go by content, not by folder name."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        import make_sample_pack as generator
        self.generator = generator
        self.original_labels = generator.LABELS

    def tearDown(self):
        self.generator.LABELS = self.original_labels
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pack(self, folder, labels):
        self.generator.LABELS = [('Label %d' % i, text)
                                 for i, text in enumerate(labels * 3)]
        path = os.path.join(self.tmp, folder)
        self.generator.write_pack(path, 1, 0x804)
        return path

    def test_simplified_content_wins_over_a_traditional_folder_name(self):
        # The machine this project was first built on had exactly this shape:
        # the simplified pack sat in a folder called `chinese`.
        simplified = self._pack('chinese', SIMPLIFIED)
        traditional = self._pack('chinese-traditional', TRADITIONAL)
        chosen = pipeline.pick_chinese_pack(
            {'chinese': simplified, 'chinese-traditional': traditional})
        self.assertEqual(chosen, simplified)

    def test_the_simplified_folder_is_chosen_when_chinese_is_traditional(self):
        # And this is the shape reported on a 2022 installation.
        traditional = self._pack('chinese', TRADITIONAL)
        simplified = self._pack('chinese-simplified', SIMPLIFIED)
        chosen = pipeline.pick_chinese_pack(
            {'chinese': traditional, 'chinese-simplified': simplified})
        self.assertEqual(chosen, simplified)

    def test_nothing_chinese_gives_nothing(self):
        self.assertIsNone(pipeline.pick_chinese_pack({'english': '/somewhere'}))


class EmptyFolderGuidance(unittest.TestCase):
    """An empty folder should name the folder that would have worked."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        import make_sample_pack as generator
        generator.write_pack(os.path.join(self.tmp, 'chinese-simplified'), 1, 0x804)
        self.empty = os.path.join(self.tmp, 'chinese')
        os.makedirs(self.empty)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_neighbour_is_named_in_both_languages(self):
        english = os.path.join(self.tmp, 'english')
        os.makedirs(english)
        report = pipeline.inspect(english, self.empty)
        self.assertFalse(report['ok'])
        combined_en = ' '.join(pipeline.text(e, 'en') for e in report['errors'])
        combined_zh = ' '.join(pipeline.text(e, 'zh') for e in report['errors'])
        self.assertIn('chinese-simplified', combined_en)
        self.assertIn('chinese-simplified', combined_zh)

    def test_an_unrelated_language_is_not_suggested(self):
        import make_sample_pack as generator
        generator.write_pack(os.path.join(self.tmp, 'german'), 0, 0x407)
        message = pipeline._empty_folder_message(
            self.empty, 'Chinese', '中文', 'chinese')
        self.assertIn('chinese-simplified', pipeline.text(message, 'en'))
        self.assertNotIn('german', pipeline.text(message, 'en'))


if __name__ == '__main__':
    unittest.main()
