# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification.

Produces two executables in dist\:

    SWBilingual.exe       the desktop interface, no console window
    swbilingual-cli.exe   the command line interface

Build with:  pyinstaller build\swbilingual.spec --noconfirm
"""
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

HIDDEN = ['pipeline', 'pe_version', 'res_reader', 'rules_access',
          'swbilingual', 'swdialogs', 'swxaml']

# Drop an icon.ico into the build folder to brand the executables.
ICON = os.path.join(ROOT, 'build', 'icon.ico')
if not os.path.exists(ICON):
    ICON = None

gui_analysis = Analysis(
    [os.path.join(ROOT, 'swbilingual-gui.py')],
    pathex=[ROOT, SRC],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN,
    hookspath=[],
    runtime_hooks=[],
    excludes=['numpy', 'PIL', 'pytest', 'setuptools'],
    noarchive=False,
)

cli_analysis = Analysis(
    [os.path.join(ROOT, 'swbilingual-cli.py')],
    pathex=[ROOT, SRC],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN,
    hookspath=[],
    runtime_hooks=[],
    excludes=['numpy', 'PIL', 'pytest', 'setuptools', 'tkinter'],
    noarchive=False,
)

def _pyz(analysis):
    # PyInstaller 5 passes the zipped data alongside the pure modules;
    # version 6 removed that argument.
    if hasattr(analysis, 'zipped_data'):
        return PYZ(analysis.pure, analysis.zipped_data)
    return PYZ(analysis.pure)


gui_pyz = _pyz(gui_analysis)
cli_pyz = _pyz(cli_analysis)

gui_exe = EXE(
    gui_pyz,
    gui_analysis.scripts,
    gui_analysis.binaries,
    gui_analysis.datas,
    [],
    name='SWBilingual',
    console=False,
    icon=ICON,
    upx=False,
    strip=False,
    bootloader_ignore_signals=False,
    disable_windowed_traceback=False,
)

cli_exe = EXE(
    cli_pyz,
    cli_analysis.scripts,
    cli_analysis.binaries,
    cli_analysis.datas,
    [],
    name='swbilingual-cli',
    console=True,
    upx=False,
    strip=False,
    bootloader_ignore_signals=False,
    disable_windowed_traceback=False,
)
