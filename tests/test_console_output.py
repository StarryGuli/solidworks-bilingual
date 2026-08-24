# -*- coding: utf-8 -*-
"""Output must survive a console that cannot represent Chinese.

A Windows console runs on a legacy code page unless told otherwise. Writing a
Chinese character to it raises UnicodeEncodeError and ends the program. This is
not limited to the Chinese interface: the English text contains the phrase
"English 中文", so `--help` used to fail on any Western Windows install.

Setting PYTHONIOENCODING to a legacy code page reproduces that console on any
operating system.
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(ROOT, 'swbilingual-cli.py')

LEGACY_CODE_PAGES = ('cp1252', 'cp437', 'ascii')


def run(args, encoding):
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = encoding
    env.pop('SWBILINGUAL_LANG', None)
    return subprocess.run([sys.executable, CLI] + args, cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ConsoleOutput(unittest.TestCase):

    def test_help_survives_a_console_without_chinese(self):
        for encoding in LEGACY_CODE_PAGES:
            for args in (['--help'], ['--lang', 'zh', '--help']):
                result = run(args, encoding)
                self.assertEqual(
                    result.returncode, 0,
                    '%s under %s failed:\n%s'
                    % (' '.join(args), encoding,
                       result.stderr.decode('utf-8', 'replace')))

    def test_reports_survive_a_console_without_chinese(self):
        # A failing check prints an error message; in Chinese it is all CJK.
        missing = os.path.join(ROOT, 'no-such-pack')
        for encoding in LEGACY_CODE_PAGES:
            result = run(['--lang', 'zh', 'check', missing, missing], encoding)
            self.assertEqual(
                result.returncode, 1,
                'expected a rejection, not a crash, under %s:\n%s'
                % (encoding, result.stderr.decode('utf-8', 'replace')))
            self.assertNotIn(b'UnicodeEncodeError', result.stderr)

    def test_no_deprecation_warnings_are_printed(self):
        result = run(['--help'], 'utf-8')
        self.assertNotIn(b'DeprecationWarning', result.stderr)


if __name__ == '__main__':
    unittest.main()
