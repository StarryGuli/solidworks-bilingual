# -*- coding: utf-8 -*-
"""Orchestration layer around the three merge passes and the three checks.

The pass implementations in swbilingual.py / swdialogs.py / swxaml.py are used
unchanged; this module only sequences them, reports progress and collects
results, so that the command line and the desktop interface behave identically.

Every message produced here carries an English and a Chinese form. Callers pick
one by setting `lang` on the Progress object they pass in.
"""
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pe_version

IS_WINDOWS = os.name == 'nt'

XAML_FILES = ('DveDictionary.xaml', 'pmdictionary.xaml')
ANCHOR_DLL = 'sldresu.dll'

LANGUAGES = ('en', 'zh')


def use_unicode_console():
    """Make the console able to print Chinese.

    A Windows console runs on a legacy code page unless told otherwise, and
    `charmap` cannot encode Chinese characters: printing one raises
    UnicodeEncodeError and takes the program down. That applies to the English
    output too, which contains the phrase "English 中文". The console is asked
    for UTF-8, and the streams are reconfigured to replace anything that still
    cannot be represented, so output is never fatal.
    """
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass                      # a redirected or absent console: harmless
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass


def system_language():
    """The language this computer is set to, as a locale string."""
    for name in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
        value = os.environ.get(name)
        if value:
            return value
    try:
        import locale
        code = locale.getlocale()[0]
        if not code:
            import warnings
            with warnings.catch_warnings():
                # getdefaultlocale is deprecated from 3.13 but is still the
                # only call that reports the Windows user default.
                warnings.simplefilter('ignore', DeprecationWarning)
                code = locale.getdefaultlocale()[0]
        return code or ''
    except (ImportError, ValueError, TypeError):
        return ''


def preferred_language():
    """'zh' or 'en', from SWBILINGUAL_LANG or the system locale."""
    chosen = os.environ.get('SWBILINGUAL_LANG', '')[:2]
    if chosen in LANGUAGES:
        return chosen
    return 'zh' if system_language().lower().startswith('zh') else 'en'


def message(en, zh):
    return {'en': en, 'zh': zh}


def text(msg, lang='en'):
    """Read one language out of a message dictionary, or pass a string through."""
    if isinstance(msg, dict):
        return msg.get(lang) or msg.get('en') or ''
    return msg


class PipelineError(Exception):
    """An error with an English and a Chinese wording."""

    def __init__(self, en, zh=None):
        Exception.__init__(self, en)
        self.en = en
        self.zh = zh or en

    def localized(self, lang='en'):
        return self.zh if lang == 'zh' else self.en


def _require_windows():
    if not IS_WINDOWS:
        raise PipelineError(
            'Resource patching uses the Windows resource API and only runs on Windows.',
            '资源修补依赖 Windows 资源 API，只能在 Windows 上运行。')


# ------------------------------------------------------------------ inspect

def _dlls(directory):
    return sorted(f for f in os.listdir(directory) if f.lower().endswith('.dll'))


def _is_pack(directory):
    """A language pack is a folder holding the anchor DLL."""
    try:
        return any(f.lower() == ANCHOR_DLL for f in os.listdir(directory))
    except OSError:
        return False


# Characters whose simplified and traditional forms are both common in a CAD
# interface, and where neither form appears in the other script. Counting them
# tells the two Chinese packs apart by content, which is the only reliable way:
# the folder name does not settle it. Installations exist where the simplified
# pack sits in a folder called `chinese`.
SIMPLIFIED_ONLY = '图时实会说边线择应单击关闭开显视转换参数设圆长宽编辑删键类样对齐组确选义计'
TRADITIONAL_ONLY = '圖時實會說邊線擇應單擊關閉開顯視轉換參數設圓長寬編輯刪鍵類樣對齊組確選義計'


def chinese_variant(strings, minimum=8):
    """'simplified', 'traditional', or None when the sample does not say.

    `minimum` is how many distinguishing characters must be seen before the
    answer is reported at all.
    """
    simplified = traditional = 0
    for text_value in strings:
        for character in text_value:
            if character in SIMPLIFIED_ONLY:
                simplified += 1
            elif character in TRADITIONAL_ONLY:
                traditional += 1
    if simplified + traditional < minimum:
        return None
    if simplified > traditional * 3:
        return 'simplified'
    if traditional > simplified * 3:
        return 'traditional'
    return None


def pack_chinese_variant(directory, sample_limit=400):
    """Read a little of a pack and report which Chinese script it is written in."""
    try:
        import res_reader
    except ImportError:
        return None
    path = os.path.join(directory, ANCHOR_DLL)
    if not os.path.exists(path):
        for name in os.listdir(directory):
            if name.lower() == ANCHOR_DLL:
                path = os.path.join(directory, name)
                break
        else:
            return None
    try:
        blocks = res_reader.read_string_blocks(path)
    except Exception:
        return None
    sample = []
    for strings in blocks.values():
        for one in strings:
            if one:
                sample.append(one)
        if len(sample) >= sample_limit:
            break
    return chinese_variant(sample)


def sibling_packs(directory):
    """Language pack folders sitting next to `directory`, by folder name.

    Used to turn "there is nothing here" into "the pack you want is the folder
    next door". SOLIDWORKS names the Simplified Chinese pack
    `chinese-simplified`; the folder called `chinese` holds Traditional Chinese
    and on many installations is empty.
    """
    found = {}
    try:
        parent = os.path.dirname(os.path.abspath(directory.rstrip('\\/')))
        for name in sorted(os.listdir(parent)):
            path = os.path.join(parent, name)
            if os.path.isdir(path) and _is_pack(path):
                found[name] = path
    except OSError:
        pass
    return found


def _empty_folder_message(directory, label_en, label_zh, prefix=None):
    """Say what is wrong, and name the folders that would work instead."""
    neighbours = sibling_packs(directory)
    neighbours.pop(os.path.basename(os.path.abspath(directory.rstrip('\\/'))), None)
    if prefix:
        # Suggest packs for the language that failed, not every pack installed.
        same_language = {n: p for n, p in neighbours.items()
                         if n.lower().startswith(prefix)}
        if same_language:
            neighbours = same_language
    if not neighbours:
        return message(
            'No resource DLLs were found in the %s folder: %s'
            % (label_en, directory),
            '%s文件夹中没有找到资源 DLL：%s' % (label_zh, directory))

    described = []
    for name in sorted(neighbours):
        variant = pack_chinese_variant(neighbours[name])
        if variant == 'simplified':
            described.append('%s (Simplified Chinese / 简体)' % name)
        elif variant == 'traditional':
            described.append('%s (Traditional Chinese / 繁體)' % name)
        else:
            described.append(name)
    names = ', '.join(described)
    hint_en = ('No resource DLLs were found in the %s folder: %s\n'
               'These folders beside it do contain a language pack: %s'
               % (label_en, directory, names))
    hint_zh = ('%s文件夹中没有找到资源 DLL：%s\n'
               '它旁边这些文件夹里确实有语言包：%s' % (label_zh, directory, names))
    if any(n.lower().startswith('chinese') for n in neighbours):
        hint_en += ('\nSOLIDWORKS ships Chinese and Chinese Simplified as separate '
                    'languages, so a folder named "chinese" is not necessarily the '
                    'simplified one. Pick the folder marked Simplified above.')
        hint_zh += ('\nSOLIDWORKS 把「中文」和「简体中文」作为两个独立语言提供，'
                    '所以名为「chinese」的文件夹不一定就是简体。'
                    '请选上面标注为简体的那个文件夹。')
    return message(hint_en, hint_zh)


def inspect(en_dir, cn_dir):
    """Check a pair of language packs before any file is written.

    Returns a report dictionary. `report['ok']` is False when the packs cannot
    be merged safely; `report['errors']` then explains why.
    """
    report = {'ok': False, 'errors': [], 'warnings': []}

    for label_en, label_zh, d in (('English', '英文', en_dir), ('Chinese', '中文', cn_dir)):
        if not d:
            report['errors'].append(message(
                'The %s pack folder is not set.' % label_en,
                '未选择%s语言包文件夹。' % label_zh))
        elif not os.path.isdir(d):
            report['errors'].append(message(
                'The %s pack folder does not exist: %s' % (label_en, d),
                '%s语言包文件夹不存在：%s' % (label_zh, d)))
    if report['errors']:
        return report

    en_files, cn_files = _dlls(en_dir), _dlls(cn_dir)
    report['en_dll_count'] = len(en_files)
    report['cn_dll_count'] = len(cn_files)
    if not en_files:
        report['errors'].append(
            _empty_folder_message(en_dir, 'English', '英文', 'english'))
    if not cn_files:
        report['errors'].append(
            _empty_folder_message(cn_dir, 'Chinese', '中文', 'chinese'))

    en_v = pe_version.pack_version(en_dir)
    cn_v = pe_version.pack_version(cn_dir)
    report['en_version'] = en_v
    report['cn_version'] = cn_v

    if en_v and cn_v:
        report['version_match'] = (en_v == cn_v)
        if en_v != cn_v:
            report['errors'].append(message(
                'Build numbers differ: English %s, Chinese %s. Resource IDs from '
                'different builds do not correspond, so the two packs cannot be '
                'merged. Obtain a Chinese pack of the same build first.' % (en_v, cn_v),
                '构建号不一致：英文 %s，中文 %s。不同构建的资源 ID 无法对应，'
                '两个包不能合并。请先取得同一构建号的中文包。' % (en_v, cn_v)))
    else:
        report['version_match'] = None
        report['warnings'].append(message(
            'Could not read %s in one of the folders, so the build numbers were '
            'not compared.' % ANCHOR_DLL,
            '有一侧文件夹中读不到 %s，因此未能比对构建号。' % ANCHOR_DLL))

    cn_lower = {f.lower() for f in cn_files}
    paired = [f for f in en_files if f.lower() in cn_lower]
    report['paired_dll_count'] = len(paired)
    if not paired and en_files and cn_files:
        report['errors'].append(message(
            'No DLL in the English folder has a counterpart in the Chinese folder. '
            'Check that both paths point at a language pack rather than at an '
            'installation root.',
            '英文文件夹中没有任何 DLL 能在中文文件夹里找到同名文件。'
            '请确认两个路径指向的是语言包目录，而不是安装根目录。'))

    report['cn_variant'] = pack_chinese_variant(cn_dir) if cn_files else None
    if report['cn_variant'] == 'traditional':
        report['warnings'].append(message(
            'The Chinese pack is written in Traditional Chinese. The merge will '
            'work, but the labels will be Traditional. If you want Simplified, '
            'use the pack whose folder is usually named "chinese-simplified".',
            '该中文包的内容是繁体中文。合并本身没有问题，但标签会是繁体。'
            '如果你要的是简体，请改用通常名为「chinese-simplified」的那个包。'))

    report['xaml'] = [n for n in XAML_FILES
                      if os.path.exists(os.path.join(en_dir, n))
                      and os.path.exists(os.path.join(cn_dir, n))]

    report['ok'] = not report['errors']
    return report


# ------------------------------------------------------------------ preview

def preview(en_dir, cn_dir, limit=25, term=None, files=None):
    """Show what the merge would produce, without writing anything.

    Reads the string tables straight out of the files, so this works on any
    operating system and can be run before a build to inspect the result.
    """
    import res_reader
    import rules_access
    sb = rules_access.import_rules()

    if os.path.isfile(en_dir) and os.path.isfile(cn_dir):
        jobs = [(os.path.basename(en_dir), en_dir, cn_dir)]
    else:
        cn_map = {f.lower(): f for f in _dlls(cn_dir)}
        jobs = [(f, os.path.join(en_dir, f), os.path.join(cn_dir, cn_map[f.lower()]))
                for f in _dlls(en_dir) if f.lower() in cn_map]
        if files:
            wanted = {f.lower() for f in files}
            jobs = [j for j in jobs if j[0].lower() in wanted]

    samples, counts = [], {'pairs': 0, 'mergeable': 0, 'files': 0}
    for name, en_path, cn_path in jobs:
        try:
            pairs = res_reader.string_pairs(en_path, cn_path)
        except Exception:
            continue
        counts['files'] += 1
        for sid, en, cn in pairs:
            counts['pairs'] += 1
            merged = sb.merge_string(en, cn)
            if not merged:
                continue
            counts['mergeable'] += 1
            if term and term.lower() not in en.lower():
                continue
            if len(samples) < limit:
                samples.append({'file': name, 'id': sid, 'english': en,
                                'chinese': cn, 'merged': merged})
    return {'samples': samples, 'counts': counts}


# ----------------------------------------------------------------- progress

class Progress:
    """Progress sink shared by the command line and the desktop interface.

    `log` receives one rendered line, `step` receives (done, total, label).
    `cancelled` is polled between files so a running build can be stopped.
    """

    def __init__(self, log=None, step=None, cancelled=None, lang='en'):
        self._log = log or (lambda line: None)
        self._step = step or (lambda done, total, label: None)
        self._cancelled = cancelled or (lambda: False)
        self.lang = lang if lang in LANGUAGES else 'en'

    def log(self, en, zh=None):
        self._log(text(message(en, zh or en), self.lang))

    def step(self, done, total, label_en='', label_zh=None):
        self._step(done, total, text(message(label_en, label_zh or label_en), self.lang))

    def check_cancel(self):
        if self._cancelled():
            raise PipelineError('Cancelled.', '已取消。')


# -------------------------------------------------------------------- build

def copy_pack(en_dir, out_dir, progress):
    """Copy the English pack to the output folder, overwriting existing files."""
    names = sorted(os.listdir(en_dir))
    total = len(names)
    progress.log('Copying %d entries from the English pack.' % total,
                 '正在从英文语言包复制 %d 个条目。' % total)
    for i, name in enumerate(names, 1):
        progress.check_cancel()
        src = os.path.join(en_dir, name)
        dst = os.path.join(out_dir, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            os.makedirs(out_dir, exist_ok=True)
            shutil.copy2(src, dst)
        if i % 20 == 0 or i == total:
            progress.step(i, total, 'Copying files', '复制文件')
    progress.log('Copy complete.', '复制完成。')


def run_string_pass(en_dir, cn_dir, out_dir, progress):
    """Pass 1: command names, menu entries and prompts held in string tables."""
    import swbilingual as sb
    files = _dlls(en_dir)
    cn_map = {f.lower(): f for f in _dlls(cn_dir)}
    merged = total = patched = 0
    failures = []
    for i, f in enumerate(files, 1):
        progress.check_cancel()
        cn_name = cn_map.get(f.lower())
        if cn_name:
            try:
                m, t = sb.patch_file(os.path.join(en_dir, f),
                                     os.path.join(cn_dir, cn_name),
                                     os.path.join(out_dir, f))
                merged += m
                total += t
                if m:
                    patched += 1
            except Exception as exc:
                failures.append((f, str(exc)))
        progress.step(i, len(files), 'Pass 1 of 3: string tables', '第 1/3 步：字符串表')
    progress.log(
        'Pass 1 complete: %d strings across %d files are now bilingual, out of '
        '%d non-empty entries.' % (merged, patched, total),
        '第 1 步完成：%d 个文件中的 %d 条字符串已变为双语，'
        '非空条目共 %d 条。' % (patched, merged, total))
    for f, why in failures:
        progress.log('  Skipped %s: %s' % (f, why), '  已跳过 %s：%s' % (f, why))
    return {'merged': merged, 'total': total, 'files': patched, 'failures': failures}


def run_dialog_pass(en_dir, cn_dir, out_dir, progress):
    """Pass 2: captions carried inside dialog templates."""
    import swdialogs as sd
    files = _dlls(out_dir)
    cn_map = {f.lower(): f for f in _dlls(cn_dir)}
    stats = {'merged': 0, 'unparsed': 0, 'roundtrip_fail': 0,
             'shape_differs': 0, 'item_mismatch': 0}
    dialogs = 0
    failures = []
    for i, f in enumerate(files, 1):
        progress.check_cancel()
        cn_name = cn_map.get(f.lower())
        if cn_name:
            try:
                dialogs += sd.patch(os.path.join(en_dir, f),
                                    os.path.join(cn_dir, cn_name),
                                    os.path.join(out_dir, f), stats)
            except Exception as exc:
                failures.append((f, str(exc)))
        progress.step(i, len(files), 'Pass 2 of 3: dialog templates', '第 2/3 步：对话框模板')
    progress.log('Pass 2 complete: %d dialog templates are now bilingual.' % dialogs,
                 '第 2 步完成：%d 个对话框模板已变为双语。' % dialogs)
    unreadable = stats['unparsed'] + stats['roundtrip_fail']
    mismatched = stats['shape_differs'] + stats['item_mismatch']
    if unreadable or mismatched:
        progress.log(
            '  %d templates were left untouched as a safety measure: %d could not '
            'be re-encoded byte for byte, %d did not match the Chinese layout.'
            % (unreadable + mismatched, unreadable, mismatched),
            '  出于安全考虑保留原样的模板共 %d 个：%d 个无法逐字节还原，'
            '%d 个与中文侧结构不一致。' % (unreadable + mismatched, unreadable, mismatched))
    for f, why in failures:
        progress.log('  Skipped %s: %s' % (f, why), '  已跳过 %s：%s' % (f, why))
    return {'dialogs': dialogs, 'stats': stats, 'failures': failures}


def run_xaml_pass(en_dir, cn_dir, out_dir, progress):
    """Pass 3: the XAML dictionaries behind the PropertyManager."""
    import swxaml
    entries = 0
    done = []
    for name in XAML_FILES:
        progress.check_cancel()
        en_p, cn_p = os.path.join(en_dir, name), os.path.join(cn_dir, name)
        if os.path.exists(en_p) and os.path.exists(cn_p):
            n = swxaml.patch(en_p, cn_p, os.path.join(out_dir, name))
            entries += n
            done.append((name, n))
    progress.step(1, 1, 'Pass 3 of 3: XAML dictionaries', '第 3/3 步：XAML 字典')
    if done:
        for name, n in done:
            progress.log('Pass 3: %s, %d entries are now bilingual.' % (name, n),
                         '第 3 步：%s，%d 个条目已变为双语。' % (name, n))
    else:
        progress.log('Pass 3: this pack contains no XAML dictionaries; skipped.',
                     '第 3 步：该语言包不含 XAML 字典，已跳过。')
    return {'entries': entries, 'files': done}


def build(en_dir, cn_dir, out_dir, progress=None, do_copy=True):
    """Produce a bilingual pack in out_dir. Returns a result dictionary."""
    _require_windows()
    progress = progress or Progress()
    report = inspect(en_dir, cn_dir)
    if not report['ok']:
        raise PipelineError(
            '\n'.join(text(m, 'en') for m in report['errors']),
            '\n'.join(text(m, 'zh') for m in report['errors']))
    for w in report['warnings']:
        progress.log('Warning: %s' % text(w, 'en'), '警告：%s' % text(w, 'zh'))

    out_dir = os.path.abspath(out_dir)
    if os.path.abspath(en_dir) == out_dir or os.path.abspath(cn_dir) == out_dir:
        raise PipelineError(
            'The output folder must be different from both source folders.',
            '输出文件夹必须与两个来源文件夹都不同。')
    os.makedirs(out_dir, exist_ok=True)

    started = time.time()
    progress.log('English pack: %s (build %s)' % (en_dir, report['en_version'] or 'unknown'),
                 '英文语言包：%s（构建 %s）' % (en_dir, report['en_version'] or '未知'))
    progress.log('Chinese pack: %s (build %s)' % (cn_dir, report['cn_version'] or 'unknown'),
                 '中文语言包：%s（构建 %s）' % (cn_dir, report['cn_version'] or '未知'))
    progress.log('Output folder: %s' % out_dir, '输出文件夹：%s' % out_dir)
    progress.log('-' * 58)

    if do_copy:
        copy_pack(en_dir, out_dir, progress)
    result = {'output': out_dir, 'report': report}
    result['strings'] = run_string_pass(en_dir, cn_dir, out_dir, progress)
    result['dialogs'] = run_dialog_pass(en_dir, cn_dir, out_dir, progress)
    result['xaml'] = run_xaml_pass(en_dir, cn_dir, out_dir, progress)
    result['seconds'] = time.time() - started
    progress.log('-' * 58)
    progress.log('Build finished in %d seconds.' % result['seconds'],
                 '构建完成，用时 %d 秒。' % result['seconds'])
    return result


# ------------------------------------------------------------------- verify

def _inventory(sb, path):
    """Resource types present in a file, and how many entries each one holds."""
    h = sb._load(path)
    try:
        types = []

        def cb(hm, t, p):
            types.append(sb._id(t))
            return True
        sb.k.EnumResourceTypesW(h, sb.ENUMRESTYPEPROC(cb), 0)
        inv = {}
        for t in types:
            key = t if isinstance(t, int) else str(t)
            inv[key] = len(sb._names(h, t)) if isinstance(t, int) else None
        return inv
    finally:
        sb.k.FreeLibrary(h)


def _overlaps(a, b):
    ax, ay, acx, acy = a
    bx, by, bcx, bcy = b
    return ax < bx + bcx and bx < ax + acx and ay < by + bcy and by < ay + acy


def verify(en_dir, out_dir, progress=None):
    """Confirm nothing was lost: resources kept, layout sane, DLLs still load."""
    _require_windows()
    progress = progress or Progress()
    import ctypes
    import swbilingual as sb
    import swdialogs as sd

    files = _dlls(out_dir)
    problems, load_failures = [], []
    cjk_total = ok = 0

    progress.log('Check 1 of 3: comparing resource inventories.',
                 '第 1/3 项检查：比对资源清单。')
    for i, f in enumerate(files, 1):
        progress.check_cancel()
        src, dst = os.path.join(en_dir, f), os.path.join(out_dir, f)
        if not os.path.exists(src):
            continue
        try:
            before, after = _inventory(sb, src), _inventory(sb, dst)
        except Exception as exc:
            problems.append((f, 'could not be read: %s' % exc))
            continue
        missing = {k: v for k, v in before.items() if k not in after}
        shrunk = {k: (v, after[k]) for k, v in before.items()
                  if k in after and isinstance(v, int)
                  and after[k] is not None and after[k] < v}
        if missing or shrunk:
            problems.append((f, 'resources missing=%s reduced=%s' % (missing, shrunk)))
            continue
        ok += 1
        for strs in sb.read_string_blocks(dst).values():
            cjk_total += sum(1 for s in strs if s and sb.CJK.search(s))
        progress.step(i, len(files), 'Check 1 of 3: resource inventory', '第 1/3 项检查：资源清单')
    progress.log('  %d files verified, %d with problems, %d string entries now '
                 'contain Chinese.' % (ok, len(problems), cjk_total),
                 '  已校验 %d 个文件，%d 个有问题，当前含中文的字符串条目 %d 条。'
                 % (ok, len(problems), cjk_total))

    progress.log('Check 2 of 3: auditing dialog layout.', '第 2/3 项检查：审查对话框布局。')
    checked = widened = new_overlap = out_of_bounds = 0
    for i, f in enumerate(files, 1):
        progress.check_cancel()
        try:
            before = sd.read_dialogs(os.path.join(en_dir, f))
            after = sd.read_dialogs(os.path.join(out_dir, f))
        except Exception:
            continue
        for key, blob in after.items():
            ob = before.get(key)
            if not ob or ob == blob:
                continue
            do, dn = sd.parse(ob), sd.parse(blob)
            if do is None or dn is None or len(do['items']) != len(dn['items']):
                continue
            checked += 1
            ro = [(it['x'], it['y'], it['cx'], it['cy']) for it in do['items']]
            rn = [(it['x'], it['y'], it['cx'], it['cy']) for it in dn['items']]
            for a in range(len(rn)):
                if rn[a][2] > ro[a][2]:
                    widened += 1
                if rn[a][0] + rn[a][2] > dn['cx'] and ro[a][0] + ro[a][2] <= do['cx']:
                    out_of_bounds += 1
                for b in range(a + 1, len(rn)):
                    if _overlaps(rn[a], rn[b]) and not _overlaps(ro[a], ro[b]):
                        new_overlap += 1
        progress.step(i, len(files), 'Check 2 of 3: dialog layout', '第 2/3 项检查：对话框布局')
    progress.log('  %d modified dialogs checked, %d controls widened, %d new overlaps, '
                 '%d controls past the right edge.'
                 % (checked, widened, new_overlap, out_of_bounds),
                 '  已检查 %d 个被修改的对话框，加宽控件 %d 个，新增重叠 %d 处，'
                 '越过右边界 %d 处。' % (checked, widened, new_overlap, out_of_bounds))

    progress.log('Check 3 of 3: loading every patched DLL.', '第 3/3 项检查：逐个加载已修补的 DLL。')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LoadLibraryW.restype = ctypes.c_void_p
    kernel.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
    kernel.FreeLibrary.argtypes = [ctypes.c_void_p]
    for i, f in enumerate(files, 1):
        progress.check_cancel()
        h = kernel.LoadLibraryW(os.path.join(out_dir, f))
        if not h:
            load_failures.append((f, ctypes.get_last_error()))
        else:
            kernel.FreeLibrary(h)
        progress.step(i, len(files), 'Check 3 of 3: load test', '第 3/3 项检查：加载测试')
    progress.log('  %d of %d DLLs loaded successfully.'
                 % (len(files) - len(load_failures), len(files)),
                 '  %d/%d 个 DLL 加载成功。' % (len(files) - len(load_failures), len(files)))

    result = {
        'files': len(files), 'verified': ok, 'problems': problems,
        'chinese_entries': cjk_total, 'dialogs_checked': checked,
        'controls_widened': widened, 'new_overlaps': new_overlap,
        'out_of_bounds': out_of_bounds, 'load_failures': load_failures,
    }
    result['passed'] = not (problems or load_failures or new_overlap or out_of_bounds)
    progress.log('-' * 58)
    if result['passed']:
        progress.log('Verification passed.', '校验通过。')
    else:
        progress.log('Verification reported problems.', '校验发现问题。')
    return result


# ------------------------------------------------------------------- deploy

def default_backup_name(target):
    return '%s.backup-%s' % (target.rstrip('\\/'), time.strftime('%Y%m%d-%H%M%S'))


def _copy_into(src_dir, dst_dir, progress, label_en, label_zh):
    names = sorted(os.listdir(src_dir))
    for i, name in enumerate(names, 1):
        progress.check_cancel()
        src, dst = os.path.join(src_dir, name), os.path.join(dst_dir, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        if i % 20 == 0 or i == len(names):
            progress.step(i, len(names), label_en, label_zh)
    return len(names)


def deploy(built_dir, target_dir, progress=None):
    """Back up the installed pack, then copy the bilingual pack over it."""
    progress = progress or Progress()
    if not os.path.isdir(built_dir):
        raise PipelineError('The bilingual pack folder does not exist: %s' % built_dir,
                            '双语语言包文件夹不存在：%s' % built_dir)
    if not os.path.isdir(target_dir):
        raise PipelineError('The SOLIDWORKS language folder does not exist: %s' % target_dir,
                            'SOLIDWORKS 语言文件夹不存在：%s' % target_dir)
    if os.path.abspath(built_dir) == os.path.abspath(target_dir):
        raise PipelineError('Source and destination are the same folder.',
                            '来源与目标是同一个文件夹。')

    backup = default_backup_name(os.path.abspath(target_dir))
    progress.log('Backing up the installed pack to %s' % backup,
                 '正在将当前语言包备份到 %s' % backup)
    shutil.copytree(target_dir, backup)
    progress.log('Backup complete.', '备份完成。')

    n = _copy_into(built_dir, target_dir, progress, 'Installing', '安装中')
    progress.log('Installation complete. Restart SOLIDWORKS to see the change.',
                 '安装完成。重启 SOLIDWORKS 后生效。')
    return {'backup': backup, 'installed': n}


def restore(backup_dir, target_dir, progress=None):
    """Put a backup taken by deploy() back in place."""
    progress = progress or Progress()
    if not os.path.isdir(backup_dir):
        raise PipelineError('The backup folder does not exist: %s' % backup_dir,
                            '备份文件夹不存在：%s' % backup_dir)
    progress.log('Restoring from %s' % backup_dir, '正在从 %s 还原' % backup_dir)
    n = _copy_into(backup_dir, target_dir, progress, 'Restoring', '还原中')
    progress.log('Restore complete. Restart SOLIDWORKS to see the change.',
                 '还原完成。重启 SOLIDWORKS 后生效。')
    return {'restored': n}


# ------------------------------------------------------- installed packs

INSTALL_TEMPLATES = (
    r'%s:\Program Files\SOLIDWORKS Corp\SOLIDWORKS',
    r'%s:\Program Files\SolidWorks Corp\SolidWorks',
    r'%s:\Program Files (x86)\SOLIDWORKS Corp\SOLIDWORKS',
)

# The Simplified pack first: `chinese` is Traditional Chinese.
CHINESE_PACK_NAMES = ('chinese-simplified', 'chinese_simplified',
                      'chinese-simplified-gb', 'chinese')


def _registry_install_roots():
    """Installation folders recorded by the SOLIDWORKS installer."""
    roots = []
    try:
        import winreg
    except ImportError:
        return roots
    for path in (r'SOFTWARE\SolidWorks', r'SOFTWARE\WOW6432Node\SolidWorks'):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        except OSError:
            continue
        try:
            index = 0
            while True:
                try:
                    name = winreg.EnumKey(key, index)
                except OSError:
                    break
                index += 1
                if not name.upper().startswith('SOLIDWORKS'):
                    continue
                try:
                    setup = winreg.OpenKey(key, name + r'\Setup')
                    try:
                        value = winreg.QueryValueEx(setup, 'SolidWorks Folder')[0]
                        if value:
                            roots.append(value)
                    finally:
                        winreg.CloseKey(setup)
                except OSError:
                    continue
        finally:
            winreg.CloseKey(key)
    return roots


def _drive_install_roots():
    """The standard installation path, looked for on every drive letter."""
    roots = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        for template in INSTALL_TEMPLATES:
            path = template % letter
            if os.path.isdir(path):
                roots.append(path)
    return roots


def find_installed_lang_dirs():
    """Search for installed language folders. Returns {folder name: path}.

    The registry is consulted first, because an installation does not have to
    live on C: or under Program Files, then every drive letter is tried.
    """
    found = {}
    if not IS_WINDOWS:
        return found
    for root in _registry_install_roots() + _drive_install_roots():
        lang = os.path.join(root, 'lang')
        if not os.path.isdir(lang):
            continue
        try:
            names = sorted(os.listdir(lang))
        except OSError:
            continue
        for name in names:
            path = os.path.join(lang, name)
            if os.path.isdir(path) and _is_pack(path):
                found.setdefault(name.lower(), path)
    return found


def pick_chinese_pack(packs):
    """The Simplified Chinese pack out of {name: path}, or None.

    What the pack contains decides; the folder name is only a tie-breaker,
    because SOLIDWORKS ships Chinese and Chinese Simplified as separate
    languages and installations disagree about which folder holds which.
    """
    candidates = {n: p for n, p in packs.items() if n.lower().startswith('chinese')}
    if not candidates:
        return None
    for name, path in sorted(candidates.items()):
        if pack_chinese_variant(path) == 'simplified':
            return path
    for name in CHINESE_PACK_NAMES:
        if name in candidates:
            return candidates[name]
    return sorted(candidates.values())[0]
