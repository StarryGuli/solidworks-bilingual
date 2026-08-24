# -*- coding: utf-8 -*-
"""Command line interface for the SOLIDWORKS bilingual language pack builder.

    python swbilingual-cli.py check   <english> <chinese>
    python swbilingual-cli.py preview <english> <chinese> [-n 25] [-t Fillet]
    python swbilingual-cli.py build   <english> <chinese> <output>
    python swbilingual-cli.py verify  <english> <output>
    python swbilingual-cli.py install <output> <solidworks-lang-english>
    python swbilingual-cli.py restore <backup> <solidworks-lang-english>
    python swbilingual-cli.py locate

Add --lang zh for Chinese output. Run a command with --help for its options.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import pipeline
from pipeline import PipelineError, text

BAR_WIDTH = 32

STRINGS = {
    'en': {
        'description': 'Build a bilingual "English 中文" SOLIDWORKS language pack.',
        'epilog': 'The check, preview and locate commands run anywhere; building and\ninstalling require Windows.',
        'quiet': 'suppress the progress bar',
        'lang': 'language of the messages printed by this tool',
        'check': 'compare two language packs without writing anything',
        'preview': 'show what the merge would produce, without writing anything',
        'p_limit': 'how many examples to print',
        'p_term': 'only show entries whose English text contains this word',
        'p_file': 'restrict the preview to one DLL',
        'p_header': 'Examined %d files, %d matched string pairs, %d would become bilingual.',
        'p_none': 'No entry matched.',
        'build': 'produce a bilingual language pack',
        'verify': 'check a built pack against the English original',
        'install': 'back up an installed language folder and replace it',
        'restore': 'put a backup back in place',
        'locate': 'list the SOLIDWORKS language folders on this computer',
        'a_english': 'the English language pack folder',
        'a_chinese': 'the Chinese language pack folder of the same build',
        'a_output': 'the folder to write the bilingual pack into',
        'a_source': 'the bilingual pack produced by the build command',
        'a_target': 'the SOLIDWORKS lang\\english folder to replace',
        'a_backup': 'a backup folder created by the install command',
        'no_copy': 'assume the output folder already holds a copy of the English pack',
        'no_verify': 'skip the checks that normally follow a build',
        'yes': 'do not ask for confirmation',
        'r_english': 'English pack : %s DLLs, build %s',
        'r_chinese': 'Chinese pack : %s DLLs, build %s',
        'r_paired': 'Matched pairs: %s DLLs',
        'r_xaml': 'XAML dicts   : %s',
        'r_warning': 'Warning: %s',
        'r_error': 'Error  : %s',
        'r_can': 'Result: the packs can be merged.',
        'r_cannot': 'Result: the packs cannot be merged.',
        'unknown': 'unknown',
        's_strings': 'Strings merged : %d',
        's_dialogs': 'Dialogs merged : %d',
        's_xaml': 'XAML entries   : %d',
        's_output': 'Output folder  : %s',
        'i_warn': 'This replaces the contents of:\n  %s',
        'i_backup': 'A timestamped backup of that folder is made first.',
        'i_prompt': 'Continue? [y/N] ',
        'i_cancel': 'Cancelled.',
        'i_kept': 'Backup kept at: %s',
        'l_none': 'No SOLIDWORKS language folder was found in the standard locations.',
        'l_row': '%-12s %s  (build %s)',
        'v_load': '  %s: failed to load, Windows error %s',
        'interrupted': 'Interrupted.',
    },
    'zh': {
        'description': '构建「English 中文」双语 SOLIDWORKS 语言包。',
        'epilog': 'check、preview、locate 可在任意系统运行；构建与安装需要 Windows。',
        'quiet': '不显示进度条',
        'lang': '本工具输出信息所用的语言',
        'check': '比对两个语言包，不写入任何文件',
        'preview': '预览合并结果，不写入任何文件',
        'p_limit': '打印多少条示例',
        'p_term': '只显示英文原文包含该词的条目',
        'p_file': '只预览指定的一个 DLL',
        'p_header': '已检查 %d 个文件，匹配字符串 %d 对，其中 %d 条将变为双语。',
        'p_none': '没有匹配的条目。',
        'build': '生成双语语言包',
        'verify': '将生成的语言包与英文原包对照校验',
        'install': '备份已安装的语言文件夹并替换它',
        'restore': '将备份还原回原位',
        'locate': '列出本机的 SOLIDWORKS 语言文件夹',
        'a_english': '英文语言包文件夹',
        'a_chinese': '同一构建号的中文语言包文件夹',
        'a_output': '写入双语语言包的目标文件夹',
        'a_source': 'build 命令生成的双语语言包',
        'a_target': '要替换的 SOLIDWORKS lang\\english 文件夹',
        'a_backup': 'install 命令创建的备份文件夹',
        'no_copy': '认为输出文件夹中已有一份英文语言包副本',
        'no_verify': '构建后不自动执行校验',
        'yes': '不询问，直接执行',
        'r_english': '英文语言包：%s 个 DLL，构建 %s',
        'r_chinese': '中文语言包：%s 个 DLL，构建 %s',
        'r_paired': '匹配文件数：%s 个 DLL',
        'r_xaml': 'XAML 字典  ：%s',
        'r_warning': '警告：%s',
        'r_error': '错误：%s',
        'r_can': '结论：两个语言包可以合并。',
        'r_cannot': '结论：两个语言包不能合并。',
        'unknown': '未知',
        's_strings': '合并字符串  ：%d 条',
        's_dialogs': '合并对话框  ：%d 个',
        's_xaml': 'XAML 条目   ：%d 条',
        's_output': '输出文件夹  ：%s',
        'i_warn': '此操作将替换以下文件夹的内容：\n  %s',
        'i_backup': '操作前会先对该文件夹做一份带时间戳的备份。',
        'i_prompt': '是否继续？[y/N] ',
        'i_cancel': '已取消。',
        'i_kept': '备份保存在：%s',
        'l_none': '在常见安装位置没有找到 SOLIDWORKS 语言文件夹。',
        'l_row': '%-12s %s（构建 %s）',
        'v_load': '  %s：加载失败，Windows 错误码 %s',
        'interrupted': '已中断。',
    },
}


def detect_language(argv):
    """--lang wins, then SWBILINGUAL_LANG, then the system locale."""
    for i, a in enumerate(argv):
        if a in ('--lang', '-l') and i + 1 < len(argv):
            return argv[i + 1] if argv[i + 1] in pipeline.LANGUAGES else 'en'
        if a.startswith('--lang='):
            v = a.split('=', 1)[1]
            return v if v in pipeline.LANGUAGES else 'en'
    return pipeline.preferred_language()


class ConsoleProgress(pipeline.Progress):
    """A single-line progress bar with a scrolling log above it."""

    def __init__(self, lang='en', quiet=False):
        pipeline.Progress.__init__(self, self._write, self._bar, lang=lang)
        self.quiet = quiet
        self._open = False

    def _clear(self):
        if self._open:
            sys.stdout.write('\r' + ' ' * (BAR_WIDTH + 46) + '\r')
            self._open = False

    def _write(self, line):
        self._clear()
        sys.stdout.write(line + '\n')
        sys.stdout.flush()

    def _bar(self, done, total, label=''):
        if self.quiet or not total:
            return
        filled = int(BAR_WIDTH * done / total)
        sys.stdout.write('\r  [%s%s] %5.1f%%  %s'
                         % ('#' * filled, '.' * (BAR_WIDTH - filled),
                            100.0 * done / total, label[:40]))
        sys.stdout.flush()
        self._open = True
        if done >= total:
            self._clear()


def cmd_check(args, s, lang):
    report = pipeline.inspect(args.english, args.chinese)
    unknown = s['unknown']
    print(s['r_english'] % (report.get('en_dll_count', '?'),
                            report.get('en_version') or unknown))
    print(s['r_chinese'] % (report.get('cn_dll_count', '?'),
                            report.get('cn_version') or unknown))
    print(s['r_paired'] % report.get('paired_dll_count', 0))
    if report.get('xaml'):
        print(s['r_xaml'] % ', '.join(report['xaml']))
    for w in report.get('warnings', []):
        print(s['r_warning'] % text(w, lang))
    for e in report.get('errors', []):
        print(s['r_error'] % text(e, lang))
    print('-' * 58)
    print(s['r_can'] if report['ok'] else s['r_cannot'])
    return 0 if report['ok'] else 1


def cmd_preview(args, s, lang):
    result = pipeline.preview(args.english, args.chinese, args.limit,
                              args.term, [args.file] if args.file else None)
    c = result['counts']
    print(s['p_header'] % (c['files'], c['pairs'], c['mergeable']))
    print('-' * 58)
    if not result['samples']:
        print(s['p_none'])
        return 1
    for sample in result['samples']:
        print(sample['merged'].replace('\n', '  |  '))
    return 0


def cmd_build(args, s, lang):
    progress = ConsoleProgress(lang, args.quiet)
    result = pipeline.build(args.english, args.chinese, args.output,
                            progress, do_copy=not args.no_copy)
    print(s['s_strings'] % result['strings']['merged'])
    print(s['s_dialogs'] % result['dialogs']['dialogs'])
    print(s['s_xaml'] % result['xaml']['entries'])
    print(s['s_output'] % result['output'])
    if not args.no_verify:
        print('-' * 58)
        return 0 if pipeline.verify(args.english, args.output, progress)['passed'] else 1
    return 0


def cmd_verify(args, s, lang):
    result = pipeline.verify(args.english, args.output, ConsoleProgress(lang, args.quiet))
    for f, why in result['problems']:
        print('  %s: %s' % (f, why))
    for f, err in result['load_failures']:
        print(s['v_load'] % (f, err))
    return 0 if result['passed'] else 1


def cmd_install(args, s, lang):
    if not args.yes:
        print(s['i_warn'] % args.target)
        print(s['i_backup'])
        if input(s['i_prompt']).strip().lower() not in ('y', 'yes'):
            print(s['i_cancel'])
            return 1
    result = pipeline.deploy(args.source, args.target, ConsoleProgress(lang, args.quiet))
    print(s['i_kept'] % result['backup'])
    return 0


def cmd_restore(args, s, lang):
    pipeline.restore(args.backup, args.target, ConsoleProgress(lang, args.quiet))
    return 0


def cmd_locate(args, s, lang):
    found = pipeline.find_installed_lang_dirs()
    if not found:
        print(s['l_none'])
        return 1
    for name, path in sorted(found.items()):
        print(s['l_row'] % (name, path,
                            pipeline.pe_version.pack_version(path) or s['unknown']))
    return 0


def build_parser(s):
    p = argparse.ArgumentParser(
        prog='swbilingual-cli', description=s['description'], epilog=s['epilog'],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('-q', '--quiet', action='store_true', help=s['quiet'])
    p.add_argument('-l', '--lang', choices=pipeline.LANGUAGES, help=s['lang'])
    sub = p.add_subparsers(dest='command')

    c = sub.add_parser('check', help=s['check'], description=s['check'])
    c.add_argument('english', help=s['a_english'])
    c.add_argument('chinese', help=s['a_chinese'])
    c.set_defaults(func=cmd_check)

    pv = sub.add_parser('preview', help=s['preview'], description=s['preview'])
    pv.add_argument('english', help=s['a_english'])
    pv.add_argument('chinese', help=s['a_chinese'])
    pv.add_argument('-n', '--limit', type=int, default=25, help=s['p_limit'])
    pv.add_argument('-t', '--term', help=s['p_term'])
    pv.add_argument('-f', '--file', help=s['p_file'])
    pv.set_defaults(func=cmd_preview)

    b = sub.add_parser('build', help=s['build'], description=s['build'])
    b.add_argument('english', help=s['a_english'])
    b.add_argument('chinese', help=s['a_chinese'])
    b.add_argument('output', help=s['a_output'])
    b.add_argument('--no-copy', action='store_true', help=s['no_copy'])
    b.add_argument('--no-verify', action='store_true', help=s['no_verify'])
    b.set_defaults(func=cmd_build)

    v = sub.add_parser('verify', help=s['verify'], description=s['verify'])
    v.add_argument('english', help=s['a_english'])
    v.add_argument('output', help=s['a_output'])
    v.set_defaults(func=cmd_verify)

    i = sub.add_parser('install', help=s['install'], description=s['install'])
    i.add_argument('source', help=s['a_source'])
    i.add_argument('target', help=s['a_target'])
    i.add_argument('-y', '--yes', action='store_true', help=s['yes'])
    i.set_defaults(func=cmd_install)

    r = sub.add_parser('restore', help=s['restore'], description=s['restore'])
    r.add_argument('backup', help=s['a_backup'])
    r.add_argument('target', help=s['a_target'])
    r.set_defaults(func=cmd_restore)

    l = sub.add_parser('locate', help=s['locate'], description=s['locate'])
    l.set_defaults(func=cmd_locate)
    return p


def main(argv=None):
    pipeline.use_unicode_console()
    argv = list(sys.argv[1:] if argv is None else argv)
    lang = detect_language(argv)
    s = STRINGS[lang]
    parser = build_parser(s)
    args = parser.parse_args(argv)
    if not getattr(args, 'command', None):
        parser.print_help()
        return 2
    try:
        return args.func(args, s, lang)
    except PipelineError as exc:
        print('\n%s' % exc.localized(lang), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\n%s' % s['interrupted'], file=sys.stderr)
        return 130


if __name__ == '__main__':
    sys.exit(main())
