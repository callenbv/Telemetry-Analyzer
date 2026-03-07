# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# Collect all tkinter data and submodules
try:
    tkinter_datas, tkinter_binaries, tkinter_hiddenimports = collect_all('tkinter')
except:
    tkinter_datas = []
    tkinter_binaries = []
    tkinter_hiddenimports = []

# Also collect submodules as fallback
tkinter_submodules = collect_submodules('tkinter')

# Find Tcl/Tk libraries from base Python installation
if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
    python_dir = sys.base_prefix
else:
    python_dir = os.path.dirname(sys.executable)

# Add Python Lib to path so PyInstaller can find standard library modules like tkinter
python_lib = os.path.join(python_dir, 'Lib')
if os.path.exists(python_lib):
    sys.path.insert(0, python_lib)

tcl_base_dir = os.path.join(python_dir, 'tcl')
tcl_dir = os.path.join(python_dir, 'tcl', 'tcl8.6')
tk_dir = os.path.join(python_dir, 'tcl', 'tk8.6')

# Collect Tcl/Tk data files - PyInstaller's tkinter hook expects specific structure
# Based on the error, it looks for init.tcl in _tcl_data directly
datas = []
if os.path.exists(tcl_dir):
    # The hook expects tcl8.6 directory structure in _tcl_data
    # So _tcl_data/tcl8.6/init.tcl should exist
    datas.append((tcl_dir, '_tcl_data/tcl8.6'))
if os.path.exists(tk_dir):
    # tk8.6 needs to be in both _tcl_data and _tk_data
    datas.append((tk_dir, '_tcl_data/tk8.6'))
    datas.append((tk_dir, '_tk_data/tk8.6'))

a = Analysis(
    ['main.py'],
    pathex=['.', '.\\Configuration', '.\\Tabs', '.\\SQLHelper', python_lib] if os.path.exists(python_lib) else ['.', '.\\Configuration', '.\\Tabs', '.\\SQLHelper'],
    binaries=tkinter_binaries,
    datas=datas + tkinter_datas,
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        '_tkinter',
        'tkinterdnd2',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
    ] + tkinter_hiddenimports + tkinter_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy.distutils', 'PyQt5', 'PySide6'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EarthwardAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Temporarily enable console to see errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
