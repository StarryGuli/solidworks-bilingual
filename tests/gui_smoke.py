# -*- coding: utf-8 -*-
"""Start the desktop interface, exercise it, and close it.

Not collected by `unittest discover`, which only picks up test*.py: this needs a
graphical session and is run on its own from the Windows job in CI. It builds
every widget, renders the interface in both languages, runs the pre-flight check
against a folder pair that must fail, and leaves the window on screen long
enough to be photographed.

    python tests/gui_smoke.py [--hold SECONDS]
"""
import argparse
import importlib.util
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))


def load_gui():
    path = os.path.join(ROOT, 'swbilingual-gui.py')
    spec = importlib.util.spec_from_file_location('swbilingual_gui', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hold', type=float, default=0.0,
                        help='keep the window on screen for this many seconds')
    parser.add_argument('--language', default='en', choices=['en', 'zh'])
    parser.add_argument('--geometry', default='780x660+40+20',
                        help='window size and position while holding')
    args = parser.parse_args()

    import tkinter as tk
    from tkinter import messagebox

    gui = load_gui()
    checks = []

    # The pre-flight check reports failures through a modal dialog, which would
    # wait for a click that is never coming. Record the calls instead.
    messagebox.showerror = lambda title, message, **kw: checks.append(('error', message))
    messagebox.showinfo = lambda title, message, **kw: checks.append(('info', message))

    root = tk.Tk()
    app = gui.App(root)

    missing = [k for k in gui.UI['en'] if k not in gui.UI['zh']]
    missing += [k for k in gui.UI['zh'] if k not in gui.UI['en']]
    if missing:
        raise SystemExit('interface strings are not paired: %s' % missing)

    for language in ('en', 'zh', 'en', 'zh'):
        app.lang.set(language)
        app.on_language_change()
        root.update()

    for index in range(3):
        app.notebook.select(index)
        root.update()
    app.notebook.select(0)

    empty = tempfile.mkdtemp()
    app.var_en.set(empty)
    app.var_cn.set(empty)
    app.do_check()
    root.update()
    if not any(kind == 'error' for kind, _ in checks):
        raise SystemExit('the pre-flight check accepted two empty folders')

    app.clear_log()
    app.lang.set(args.language)
    app.on_language_change()
    app.var_en.set(r'C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\english')
    app.var_cn.set(r'C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\chinese')
    app.var_out.set(r'D:\bilingual')
    app.log('SOLIDWORKS bilingual language pack builder')
    app.log('Interface smoke test: every widget built, both languages rendered.')
    if args.hold:
        # Keep the window clear of the taskbar so a capture of its rectangle
        # contains the window and nothing else.
        root.geometry(args.geometry)
    root.update()

    deadline = time.monotonic() + args.hold
    while time.monotonic() < deadline:
        root.update()
        time.sleep(0.05)

    root.destroy()
    print('GUI smoke test passed: widgets built, both languages rendered, '
          'pre-flight check rejected an invalid pair.')


if __name__ == '__main__':
    main()
