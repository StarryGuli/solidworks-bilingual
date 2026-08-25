# -*- coding: utf-8 -*-
"""Desktop interface for the SOLIDWORKS bilingual language pack builder.

Standard library only: the interface is built with tkinter so that a packaged
executable needs nothing installed on the target machine. Long operations run
on a worker thread and report back through a queue, so the window stays
responsive and a running build can be stopped.
"""
import os
import queue
import sys
import threading
import traceback
import webbrowser

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

BASE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(BASE, 'src'), BASE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pipeline
from pipeline import PipelineError, text

APP_VERSION = '1.0.0'
PROJECT_URL = 'https://github.com/StarryGuli/solidworks-bilingual'

# ---------------------------------------------------------------- interface text

UI = {
    'en': {
        'title': 'SOLIDWORKS Bilingual Language Pack Builder',
        'subtitle': 'Merge a Chinese language pack into the English one, so every '
                    'command reads "English 中文".',
        'tab_build': 'Build',
        'tab_install': 'Install',
        'tab_about': 'About',
        'grp_source': 'Source language packs',
        'grp_output': 'Output',
        'lbl_english': 'English pack',
        'lbl_chinese': 'Chinese pack',
        'lbl_output': 'Output folder',
        'browse': 'Browse...',
        'hint_source': r'Both folders live under SOLIDWORKS\lang and must come from '
                       'the same build.',
        'hint_output': 'A new folder. The English pack is copied here first, then '
                       'patched. Nothing in the source folders is modified.',
        'btn_check': 'Check packs',
        'btn_detect_sources': 'Find installed packs',
        'detected_sources': 'Found the installed packs: English at %s',
        'detected_chinese': 'Chinese at %s',
        'no_chinese_found': 'A SOLIDWORKS installation was found, but it has no '
                            'Chinese language pack. Add one through the '
                            'SOLIDWORKS Installation Manager; see the guide '
                            'linked from the About tab.',
        'variant_simplified': 'The Chinese pack contains Simplified Chinese.',
        'variant_traditional': 'The Chinese pack contains Traditional Chinese.',
        'btn_preview': 'Preview',
        'preview_title': 'Preview of the merge',
        'preview_head': 'Examined %d files, %d matched string pairs, %d would become bilingual.',
        'preview_filter': 'Filter',
        'preview_apply': 'Apply',
        'preview_close': 'Close',
        'preview_none': 'No entry matched.',
        'btn_build': 'Build bilingual pack',
        'btn_stop': 'Stop',
        'status_idle': 'Ready.',
        'status_running': 'Working...',
        'status_done': 'Finished.',
        'status_failed': 'Failed.',
        'status_stopped': 'Stopped.',
        'grp_target': 'Installation',
        'lbl_pack': 'Bilingual pack',
        'lbl_target': r'SOLIDWORKS lang\english folder',
        'btn_detect': 'Detect',
        'btn_install': 'Install',
        'btn_restore': 'Restore from backup...',
        'install_note': 'Installing replaces the language folder used by SOLIDWORKS. '
                        'A timestamped backup of the current folder is made first. '
                        'Close SOLIDWORKS and run this program as administrator, '
                        'otherwise the files cannot be written.',
        'confirm_install_t': 'Confirm installation',
        'confirm_install_m': 'The contents of\n\n%s\n\nwill be replaced.\n\n'
                             'A backup is created next to it first. Continue?',
        'restore_pick': 'Select the backup folder to restore',
        'confirm_restore_t': 'Confirm restore',
        'confirm_restore_m': 'Restore\n\n%s\n\nover\n\n%s ?',
        'grp_log': 'Log',
        'btn_clear': 'Clear',
        'btn_save_log': 'Save log...',
        'save_log_title': 'Save the log',
        'lang_label': 'Language',
        'pick_english': 'Select the English language pack folder',
        'pick_chinese': 'Select the Chinese language pack folder',
        'pick_output': 'Select the output folder',
        'pick_pack': 'Select the bilingual pack folder',
        'pick_target': r'Select the SOLIDWORKS lang\english folder',
        'err_title': 'Error',
        'info_title': 'Information',
        'no_lang_found': 'No SOLIDWORKS language folder was found in the standard '
                         'locations. Select it manually.',
        'detected': 'Detected: %s',
        'not_windows': 'This computer is not running Windows. Packs can be checked, '
                       'but building and installing require Windows.',
        'summary': 'Bilingual: %d strings, %d dialogs, %d XAML entries.',
        'verify_pass': 'Verification passed. The pack is ready to install.',
        'verify_fail': 'Verification reported problems. Read the log before installing.',
        'about_body':
            'This tool rewrites the resources of an English SOLIDWORKS language pack '
            'so that each label is followed by its Chinese translation. SOLIDWORKS '
            'keeps loading the English pack and needs no configuration change.\n\n'
            'The merge runs in three passes: string tables (command names, menus, '
            'prompts), dialog templates (window titles, buttons, static text, with '
            'controls widened where needed), and the XAML dictionaries behind the '
            'PropertyManager. Long messages, format strings, paths and registration '
            'entries are left untouched.\n\n'
            'Requires a licensed SOLIDWORKS installation. Language packs are the '
            'property of Dassault Systèmes and must not be redistributed.',
        'about_project': 'Project page',
        'about_version': 'Version %s',
    },
    'zh': {
        'title': 'SOLIDWORKS 双语语言包构建工具',
        'subtitle': '把中文语言包合并进英文语言包，让每个命令都显示为「English 中文」。',
        'tab_build': '构建',
        'tab_install': '安装',
        'tab_about': '关于',
        'grp_source': '来源语言包',
        'grp_output': '输出',
        'lbl_english': '英文语言包',
        'lbl_chinese': '中文语言包',
        'lbl_output': '输出文件夹',
        'browse': '浏览…',
        'hint_source': '两个文件夹都位于 SOLIDWORKS\\lang 下，且必须来自同一构建号。',
        'hint_output': '请选择一个新文件夹。程序会先把英文语言包复制到这里再修补，'
                       '不会改动来源文件夹中的任何文件。',
        'btn_check': '检查语言包',
        'btn_detect_sources': '查找已安装的语言包',
        'detected_sources': '已找到已安装的语言包：英文在 %s',
        'detected_chinese': '中文在 %s',
        'no_chinese_found': '找到了 SOLIDWORKS 安装，但其中没有中文语言包。'
                            '请通过 SOLIDWORKS 安装管理程序添加，'
                            '具体步骤见「关于」页链接的说明。',
        'variant_simplified': '该中文包的内容是简体中文。',
        'variant_traditional': '该中文包的内容是繁体中文。',
        'btn_preview': '预览',
        'preview_title': '合并结果预览',
        'preview_head': '已检查 %d 个文件，匹配字符串 %d 对，其中 %d 条将变为双语。',
        'preview_filter': '筛选',
        'preview_apply': '应用',
        'preview_close': '关闭',
        'preview_none': '没有匹配的条目。',
        'btn_build': '生成双语语言包',
        'btn_stop': '停止',
        'status_idle': '就绪。',
        'status_running': '正在处理…',
        'status_done': '已完成。',
        'status_failed': '失败。',
        'status_stopped': '已停止。',
        'grp_target': '安装',
        'lbl_pack': '双语语言包',
        'lbl_target': 'SOLIDWORKS lang\\english 文件夹',
        'btn_detect': '自动查找',
        'btn_install': '安装',
        'btn_restore': '从备份还原…',
        'install_note': '安装会替换 SOLIDWORKS 正在使用的语言文件夹，'
                        '操作前会先为当前文件夹创建带时间戳的备份。'
                        '请先关闭 SOLIDWORKS，并以管理员身份运行本程序，否则无法写入文件。',
        'confirm_install_t': '确认安装',
        'confirm_install_m': '以下文件夹的内容将被替换：\n\n%s\n\n'
                             '程序会先在同级目录创建备份。是否继续？',
        'restore_pick': '选择要还原的备份文件夹',
        'confirm_restore_t': '确认还原',
        'confirm_restore_m': '将\n\n%s\n\n还原到\n\n%s ？',
        'grp_log': '日志',
        'btn_clear': '清空',
        'btn_save_log': '保存日志…',
        'save_log_title': '保存日志',
        'lang_label': '语言',
        'pick_english': '选择英文语言包文件夹',
        'pick_chinese': '选择中文语言包文件夹',
        'pick_output': '选择输出文件夹',
        'pick_pack': '选择双语语言包文件夹',
        'pick_target': '选择 SOLIDWORKS lang\\english 文件夹',
        'err_title': '错误',
        'info_title': '提示',
        'no_lang_found': '在常见安装位置没有找到 SOLIDWORKS 语言文件夹，请手动选择。',
        'detected': '已找到：%s',
        'not_windows': '当前系统不是 Windows。可以检查语言包，但构建与安装需要在 Windows 上进行。',
        'summary': '双语化结果：字符串 %d 条，对话框 %d 个，XAML 条目 %d 条。',
        'verify_pass': '校验通过，可以安装。',
        'verify_fail': '校验发现问题，安装前请先查看日志。',
        'about_body':
            '本工具改写英文 SOLIDWORKS 语言包中的资源，使每个标签后面跟上对应的中文译文。'
            'SOLIDWORKS 仍然加载英文语言包，无需更改任何设置。\n\n'
            '合并分三步进行：字符串表（命令名、菜单、提示）、对话框模板（窗口标题、按钮、'
            '静态文本，并在需要时加宽控件）、以及 PropertyManager 使用的 XAML 字典。'
            '长句、格式化字符串、路径和注册用条目一律保持原样。\n\n'
            '使用本工具需要已获授权的 SOLIDWORKS 安装。语言包版权归 Dassault Systèmes 所有，'
            '不得再分发。',
        'about_project': '项目主页',
        'about_version': '版本 %s',
    },
}

PAD = 10


class App(object):

    def __init__(self, root):
        self.root = root
        self.lang = tk.StringVar(value=self._initial_language())
        self.queue = queue.Queue()
        self.worker = None
        self.stop_flag = threading.Event()
        self.translatable = []          # (widget, kind, key)

        self.var_en = tk.StringVar()
        self.var_cn = tk.StringVar()
        self.var_out = tk.StringVar()
        self.var_pack = tk.StringVar()
        self.var_target = tk.StringVar()
        self.var_status = tk.StringVar()

        self._build_widgets()
        self.retranslate()
        self.root.after(80, self._drain_queue)
        if not pipeline.IS_WINDOWS:
            self.log(self.t('not_windows'))

    # ---------------------------------------------------------- translation

    @staticmethod
    def _initial_language():
        return pipeline.preferred_language()

    def t(self, key):
        return UI[self.lang.get()][key]

    def track(self, widget, key, kind='text'):
        self.translatable.append((widget, kind, key))
        return widget

    def retranslate(self):
        self.root.title(self.t('title'))
        for widget, kind, key in self.translatable:
            value = self.t(key)
            if kind == 'text':
                widget.configure(text=value)
            elif kind == 'tab':
                self.notebook.tab(widget, text=value)
            elif kind == 'about':
                widget.configure(state='normal')
                widget.delete('1.0', 'end')
                widget.insert('1.0', value)
                widget.configure(state='disabled')
        self.var_status.set(self.t('status_idle'))

    def on_language_change(self):
        self.retranslate()

    # -------------------------------------------------------------- widgets

    def _build_widgets(self):
        root = self.root
        root.minsize(760, 620)
        style = ttk.Style()
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        elif 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('Title.TLabel', font=('Segoe UI', 15, 'bold'))
        style.configure('Sub.TLabel', foreground='#5a5a5a')
        style.configure('Hint.TLabel', foreground='#5a5a5a')
        style.configure('Status.TLabel', foreground='#1a1a1a')
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))

        header = ttk.Frame(root, padding=(PAD + 4, PAD, PAD + 4, 4))
        header.pack(fill='x')
        titles = ttk.Frame(header)
        titles.pack(side='left', fill='x', expand=True)
        self.track(ttk.Label(titles, style='Title.TLabel'), 'title').pack(anchor='w')
        self.track(ttk.Label(titles, style='Sub.TLabel', wraplength=520,
                             justify='left'), 'subtitle').pack(anchor='w', pady=(2, 0))

        langbox = ttk.Frame(header)
        langbox.pack(side='right', anchor='ne')
        self.track(ttk.Label(langbox), 'lang_label').pack(side='left', padx=(0, 6))
        for code, label in (('en', 'English'), ('zh', '中文')):
            ttk.Radiobutton(langbox, text=label, value=code, variable=self.lang,
                            command=self.on_language_change).pack(side='left')

        self.notebook = ttk.Notebook(root, padding=(PAD, 6))
        self.notebook.pack(fill='both', expand=False, padx=PAD, pady=(4, 0))
        self._build_tab(self.notebook)
        self._install_tab(self.notebook)
        self._about_tab(self.notebook)

        self._log_area(root)
        self._status_bar(root)

    def _folder_row(self, parent, row, key, var, title_key):
        self.track(ttk.Label(parent), key).grid(row=row, column=0, sticky='w',
                                                padx=(0, 8), pady=4)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky='ew', pady=4)
        btn = self.track(ttk.Button(parent, width=12,
                                    command=lambda: self._pick(var, title_key)), 'browse')
        btn.grid(row=row, column=2, sticky='e', padx=(8, 0), pady=4)
        parent.columnconfigure(1, weight=1)
        return entry

    def _pick(self, var, title_key):
        initial = var.get() or os.path.expanduser('~')
        chosen = filedialog.askdirectory(title=self.t(title_key),
                                         initialdir=initial, mustexist=True)
        if chosen:
            var.set(os.path.normpath(chosen))

    def _build_tab(self, nb):
        tab = ttk.Frame(nb, padding=PAD)
        nb.add(tab)
        self.track(tab, 'tab_build', 'tab')

        src = ttk.LabelFrame(tab, padding=PAD)
        src.pack(fill='x')
        self.track(src, 'grp_source')
        self._folder_row(src, 0, 'lbl_english', self.var_en, 'pick_english')
        self._folder_row(src, 1, 'lbl_chinese', self.var_cn, 'pick_chinese')
        self.track(ttk.Button(src, width=22, command=self.do_detect_sources),
                   'btn_detect_sources').grid(row=2, column=2, sticky='e', padx=(8, 0),
                                              pady=(6, 0))
        self.track(ttk.Label(src, style='Hint.TLabel', wraplength=520, justify='left'),
                   'hint_source').grid(row=2, column=0, columnspan=2, sticky='w', pady=(4, 0))

        out = ttk.LabelFrame(tab, padding=PAD)
        out.pack(fill='x', pady=(PAD, 0))
        self.track(out, 'grp_output')
        self._folder_row(out, 0, 'lbl_output', self.var_out, 'pick_output')
        self.track(ttk.Label(out, style='Hint.TLabel', wraplength=660, justify='left'),
                   'hint_output').grid(row=1, column=0, columnspan=3, sticky='w', pady=(4, 0))

        actions = ttk.Frame(tab)
        actions.pack(fill='x', pady=(PAD, 0))
        self.btn_check = self.track(ttk.Button(actions, width=18, command=self.do_check),
                                    'btn_check')
        self.btn_check.pack(side='left')
        self.btn_preview = self.track(ttk.Button(actions, width=14, command=self.do_preview),
                                      'btn_preview')
        self.btn_preview.pack(side='left', padx=(8, 0))
        self.btn_build = self.track(ttk.Button(actions, width=24, style='Accent.TButton',
                                               command=self.do_build), 'btn_build')
        self.btn_build.pack(side='left', padx=8)
        self.btn_stop = self.track(ttk.Button(actions, width=10, command=self.do_stop,
                                              state='disabled'), 'btn_stop')
        self.btn_stop.pack(side='left')

    def _install_tab(self, nb):
        tab = ttk.Frame(nb, padding=PAD)
        nb.add(tab)
        self.track(tab, 'tab_install', 'tab')

        grp = ttk.LabelFrame(tab, padding=PAD)
        grp.pack(fill='x')
        self.track(grp, 'grp_target')
        self._folder_row(grp, 0, 'lbl_pack', self.var_pack, 'pick_pack')
        self.track(ttk.Label(grp), 'lbl_target').grid(row=1, column=0, sticky='w',
                                                      padx=(0, 8), pady=4)
        ttk.Entry(grp, textvariable=self.var_target).grid(row=1, column=1, sticky='ew', pady=4)
        bar = ttk.Frame(grp)
        bar.grid(row=1, column=2, sticky='e', padx=(8, 0))
        self.track(ttk.Button(bar, width=12, command=self.do_detect),
                   'btn_detect').pack(side='left')
        self.track(ttk.Button(bar, width=12,
                              command=lambda: self._pick(self.var_target, 'pick_target')),
                   'browse').pack(side='left', padx=(6, 0))
        self.track(ttk.Label(grp, style='Hint.TLabel', wraplength=660, justify='left'),
                   'install_note').grid(row=2, column=0, columnspan=3, sticky='w', pady=(8, 0))

        actions = ttk.Frame(tab)
        actions.pack(fill='x', pady=(PAD, 0))
        self.btn_install = self.track(ttk.Button(actions, width=18, style='Accent.TButton',
                                                 command=self.do_install), 'btn_install')
        self.btn_install.pack(side='left')
        self.track(ttk.Button(actions, width=24, command=self.do_restore),
                   'btn_restore').pack(side='left', padx=8)

    def _about_tab(self, nb):
        tab = ttk.Frame(nb, padding=PAD)
        nb.add(tab)
        self.track(tab, 'tab_about', 'tab')
        body = tk.Text(tab, height=11, wrap='word', relief='flat', borderwidth=0,
                       background=self.root.cget('background'))
        body.pack(fill='both', expand=True)
        self.track(body, 'about_body', 'about')
        row = ttk.Frame(tab)
        row.pack(fill='x', pady=(6, 0))
        ttk.Label(row, text=UI['en']['about_version'] % APP_VERSION).pack(side='left')
        link = self.track(ttk.Label(row, foreground='#0a58ca', cursor='hand2'),
                          'about_project')
        link.pack(side='left', padx=12)
        link.bind('<Button-1>', lambda e: webbrowser.open(PROJECT_URL))

    def _log_area(self, root):
        frame = ttk.LabelFrame(root, padding=PAD)
        frame.pack(fill='both', expand=True, padx=PAD, pady=PAD)
        self.track(frame, 'grp_log')
        self.text = tk.Text(frame, height=12, wrap='none', font=('Consolas', 9),
                            background='#1e1e1e', foreground='#dcdcdc',
                            insertbackground='#dcdcdc', relief='flat')
        yscroll = ttk.Scrollbar(frame, orient='vertical', command=self.text.yview)
        xscroll = ttk.Scrollbar(frame, orient='horizontal', command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set,
                            state='disabled')
        self.text.grid(row=0, column=0, sticky='nsew')
        yscroll.grid(row=0, column=1, sticky='ns')
        xscroll.grid(row=1, column=0, sticky='ew')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky='e', pady=(6, 0))
        self.track(ttk.Button(buttons, width=10, command=self.clear_log), 'btn_clear').pack(side='left')
        self.track(ttk.Button(buttons, width=14, command=self.save_log), 'btn_save_log').pack(side='left', padx=(8, 0))

    def _status_bar(self, root):
        bar = ttk.Frame(root, padding=(PAD, 0, PAD, PAD))
        bar.pack(fill='x')
        self.progress = ttk.Progressbar(bar, mode='determinate', maximum=100)
        self.progress.pack(side='left', fill='x', expand=True)
        ttk.Label(bar, textvariable=self.var_status, style='Status.TLabel',
                  width=42, anchor='w').pack(side='left', padx=(PAD, 0))

    # ------------------------------------------------------------- log sink

    def log(self, line):
        self.text.configure(state='normal')
        self.text.insert('end', line + '\n')
        self.text.see('end')
        self.text.configure(state='disabled')

    def clear_log(self):
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        self.text.configure(state='disabled')

    def save_log(self):
        path = filedialog.asksaveasfilename(
            title=self.t('save_log_title'), defaultextension='.txt',
            initialfile='swbilingual-log.txt',
            filetypes=[('Text file', '*.txt'), ('All files', '*.*')])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.text.get('1.0', 'end'))

    # ---------------------------------------------------------- worker glue

    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == 'log':
                    self.log(payload)
                elif kind == 'step':
                    done, total, label = payload
                    self.progress['value'] = (100.0 * done / total) if total else 0
                    self.var_status.set(label)
                elif kind == 'status':
                    self.var_status.set(payload)
                elif kind == 'done':
                    self._finish(payload)
        except queue.Empty:
            pass
        self.root.after(80, self._drain_queue)

    def _progress(self):
        return pipeline.Progress(
            log=lambda line: self.queue.put(('log', line)),
            step=lambda d, t, l: self.queue.put(('step', (d, t, l))),
            cancelled=self.stop_flag.is_set,
            lang=self.lang.get())

    def _busy(self, running):
        state = 'disabled' if running else 'normal'
        for b in (self.btn_check, self.btn_preview, self.btn_build, self.btn_install):
            b.configure(state=state)
        self.btn_stop.configure(state='normal' if running else 'disabled')

    def _run(self, func):
        if self.worker and self.worker.is_alive():
            return
        self.stop_flag.clear()
        self._busy(True)
        self.progress['value'] = 0
        self.var_status.set(self.t('status_running'))

        def target():
            try:
                func(self._progress())
                self.queue.put(('done', None))
            except PipelineError as exc:
                self.queue.put(('done', exc.localized(self.lang.get())))
            except Exception:
                self.queue.put(('done', traceback.format_exc()))

        self.worker = threading.Thread(target=target, daemon=True)
        self.worker.start()

    def _finish(self, error):
        self._busy(False)
        if error is None:
            self.progress['value'] = 100
            self.var_status.set(self.t('status_done'))
        elif self.stop_flag.is_set():
            self.var_status.set(self.t('status_stopped'))
            self.log(self.t('status_stopped'))
        else:
            self.var_status.set(self.t('status_failed'))
            self.log(error)
            messagebox.showerror(self.t('err_title'), error)

    def do_stop(self):
        self.stop_flag.set()

    # -------------------------------------------------------------- actions

    def do_check(self):
        lang = self.lang.get()
        report = pipeline.inspect(self.var_en.get(), self.var_cn.get())
        self.log('-' * 58)
        self.log('%s: %s DLL, build %s' % (self.t('lbl_english'),
                                           report.get('en_dll_count', '?'),
                                           report.get('en_version') or '?'))
        self.log('%s: %s DLL, build %s' % (self.t('lbl_chinese'),
                                           report.get('cn_dll_count', '?'),
                                           report.get('cn_version') or '?'))
        self.log('Matched pairs: %s' % report.get('paired_dll_count', 0))
        if report.get('cn_variant'):
            self.log(self.t('variant_%s' % report['cn_variant']))
        if report.get('xaml'):
            self.log('XAML: %s' % ', '.join(report['xaml']))
        for w in report.get('warnings', []):
            self.log(text(w, lang))
        for e in report.get('errors', []):
            self.log(text(e, lang))
        if not report['ok']:
            messagebox.showerror(self.t('err_title'),
                                 '\n'.join(text(e, lang) for e in report['errors']))
        else:
            self.var_status.set(self.t('status_done'))

    def do_preview(self):
        en, cn = self.var_en.get(), self.var_cn.get()
        report = pipeline.inspect(en, cn)
        if not report['ok']:
            messagebox.showerror(self.t('err_title'), '\n'.join(
                text(e, self.lang.get()) for e in report['errors']))
            return
        PreviewWindow(self, en, cn)

    def do_detect_sources(self):
        packs = pipeline.find_installed_lang_dirs()
        if not packs:
            messagebox.showinfo(self.t('info_title'), self.t('no_lang_found'))
            return
        english = packs.get('english')
        if english:
            self.var_en.set(english)
            self.log(self.t('detected_sources') % english)
        chinese = pipeline.pick_chinese_pack(packs)
        if not chinese:
            messagebox.showinfo(self.t('info_title'), self.t('no_chinese_found'))
            return
        self.var_cn.set(chinese)
        self.log(self.t('detected_chinese') % chinese)
        variant = pipeline.pack_chinese_variant(chinese)
        if variant:
            self.log(self.t('variant_%s' % variant))

    def do_build(self):
        en, cn, out = self.var_en.get(), self.var_cn.get(), self.var_out.get()

        def job(progress):
            result = pipeline.build(en, cn, out, progress)
            progress.log(UI[progress.lang]['summary']
                         % (result['strings']['merged'], result['dialogs']['dialogs'],
                            result['xaml']['entries']))
            check = pipeline.verify(en, out, progress)
            progress.log(UI[progress.lang]['verify_pass' if check['passed'] else 'verify_fail'])

        self.var_pack.set(out)          # set here, on the interface thread
        self._run(job)

    def do_detect(self):
        found = pipeline.find_installed_lang_dirs()
        if not found:
            messagebox.showinfo(self.t('info_title'), self.t('no_lang_found'))
            return
        english = found.get('english') or sorted(found.values())[0]
        self.var_target.set(english)
        self.log(self.t('detected') % english)

    def do_install(self):
        source, target = self.var_pack.get(), self.var_target.get()
        if not source or not target:
            messagebox.showerror(self.t('err_title'), self.t('pick_target'))
            return
        if not messagebox.askyesno(self.t('confirm_install_t'),
                                   self.t('confirm_install_m') % target):
            return
        self._run(lambda p: pipeline.deploy(source, target, p))

    def do_restore(self):
        target = self.var_target.get()
        if not target:
            messagebox.showerror(self.t('err_title'), self.t('pick_target'))
            return
        backup = filedialog.askdirectory(title=self.t('restore_pick'),
                                         initialdir=os.path.dirname(target) or '/')
        if not backup:
            return
        if not messagebox.askyesno(self.t('confirm_restore_t'),
                                   self.t('confirm_restore_m') % (backup, target)):
            return
        self._run(lambda p: pipeline.restore(backup, target, p))


class PreviewWindow(object):
    """A read-only look at what the merge would produce."""

    def __init__(self, app, en_dir, cn_dir):
        self.app = app
        self.en_dir, self.cn_dir = en_dir, cn_dir
        self.term = tk.StringVar()

        self.top = tk.Toplevel(app.root)
        self.top.title(app.t('preview_title'))
        self.top.geometry('820x520')
        self.top.transient(app.root)

        head = ttk.Frame(self.top, padding=(PAD, PAD, PAD, 4))
        head.pack(fill='x')
        self.head_label = ttk.Label(head, style='Hint.TLabel')
        self.head_label.pack(anchor='w')

        bar = ttk.Frame(self.top, padding=(PAD, 0))
        bar.pack(fill='x')
        ttk.Label(bar, text=app.t('preview_filter')).pack(side='left')
        entry = ttk.Entry(bar, textvariable=self.term, width=28)
        entry.pack(side='left', padx=8)
        entry.bind('<Return>', lambda e: self.refresh())
        ttk.Button(bar, text=app.t('preview_apply'), command=self.refresh).pack(side='left')
        ttk.Button(bar, text=app.t('preview_close'),
                   command=self.top.destroy).pack(side='right')

        body = ttk.Frame(self.top, padding=PAD)
        body.pack(fill='both', expand=True)
        self.text = tk.Text(body, wrap='none', font=('Consolas', 10), relief='flat',
                            background='#ffffff', foreground='#1a1a1a')
        yscroll = ttk.Scrollbar(body, orient='vertical', command=self.text.yview)
        self.text.configure(yscrollcommand=yscroll.set, state='disabled')
        self.text.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')
        self.refresh()

    def refresh(self):
        term = self.term.get().strip() or None
        result = pipeline.preview(self.en_dir, self.cn_dir, limit=400, term=term)
        counts = result['counts']
        self.head_label.configure(
            text=self.app.t('preview_head')
            % (counts['files'], counts['pairs'], counts['mergeable']))
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        if not result['samples']:
            self.text.insert('end', self.app.t('preview_none'))
        for sample in result['samples']:
            self.text.insert('end', sample['merged'].replace('\n', '  |  ') + '\n')
        self.text.configure(state='disabled')


def main():
    root = tk.Tk()
    try:
        root.call('tk', 'scaling', 1.2)
    except tk.TclError:
        pass
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
