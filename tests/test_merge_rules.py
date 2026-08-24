# -*- coding: utf-8 -*-
"""The merge rules decide which labels get a Chinese twin. These are the cases
that must not regress: anything SOLIDWORKS parses itself has to stay untouched.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import rules_access

sb = rules_access.import_rules()


class MergeRules(unittest.TestCase):

    def test_short_label_is_merged(self):
        self.assertEqual(sb.merge_string('Fillet', '圆角'), 'Fillet 圆角')

    def test_accelerator_marker_is_kept_on_the_english_side(self):
        self.assertEqual(sb.merge_string('&Open', '打开(&O)'), '&Open 打开')

    def test_format_strings_are_never_touched(self):
        self.assertIsNone(sb.merge_string('Saved %s', '已保存 %s'))
        self.assertIsNone(sb.merge_string('Item %1 of %2', '第 %1 项，共 %2 项'))

    def test_paths_filters_and_urls_are_never_touched(self):
        self.assertIsNone(sb.merge_string(r'C:\temp\part.sldprt', r'C:\temp\part.sldprt'))
        self.assertIsNone(sb.merge_string('Part Files (*.sldprt)', '零件文件 (*.sldprt)'))
        self.assertIsNone(sb.merge_string('https://example.com', 'https://example.com'))

    def test_long_sentences_are_left_in_english(self):
        long_en = 'This operation cannot be completed because the selected face ' \
                  'belongs to a body that is currently suppressed.'
        self.assertIsNone(sb.merge_string(long_en, '所选面属于当前被压缩的实体，无法完成该操作。'))

    def test_untranslated_entries_are_left_alone(self):
        self.assertIsNone(sb.merge_string('Fillet', 'Fillet'))
        self.assertIsNone(sb.merge_string('OK', 'OK'))

    def test_entries_without_chinese_are_left_alone(self):
        self.assertIsNone(sb.merge_string('Fillet', 'Congé'))

    def test_entries_without_latin_letters_are_left_alone(self):
        self.assertIsNone(sb.merge_string('1234', '1234 项'))

    def test_two_part_toolbar_entry_merges_the_command_name(self):
        en = 'Extrudes a sketch or selected sketch contours in one or two ' \
             'directions to create a solid feature.\nExtruded Boss/Base'
        cn = '在一个或两个方向上拉伸草图或所选草图轮廓以生成实体特征。\n拉伸凸台/基体'
        head, label = sb.merge_string(en, cn).split('\n')
        # the long tooltip exceeds the length limit and stays in English
        self.assertEqual(head, en.split('\n')[0])
        self.assertEqual(label, 'Extruded Boss/Base 拉伸凸台/基体')

    def test_a_short_description_is_merged_as_well(self):
        en = 'Adds a fillet.\nFillet'
        cn = '添加圆角。\n圆角'
        head, label = sb.merge_string(en, cn).split('\n')
        self.assertEqual(head, 'Adds a fillet. 添加圆角。')
        self.assertEqual(label, 'Fillet 圆角')

    def test_entries_with_more_than_two_segments_are_left_alone(self):
        self.assertIsNone(sb.merge_string('a\nb\nc', '甲\n乙\n丙'))

    def test_tabs_and_carriage_returns_are_left_alone(self):
        self.assertIsNone(sb.merge_string('Name\tValue', '名称\t数值'))

    def test_empty_input_is_left_alone(self):
        self.assertIsNone(sb.merge_string('', '圆角'))
        self.assertIsNone(sb.merge_string('Fillet', ''))

    def test_length_limits_are_the_documented_ones(self):
        self.assertEqual(sb.MAX_EN, 60)
        self.assertEqual(sb.MAX_CN, 40)
        self.assertTrue(sb.mergeable('A' * 60, '短标签'))
        self.assertFalse(sb.mergeable('A' * 61, '短标签'))
        self.assertFalse(sb.mergeable('Label', '汉' * 41))


if __name__ == '__main__':
    unittest.main()
