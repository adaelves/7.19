
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add project root to path
project_root = Path(r'E:\test\7.19')
sys.path.insert(0, str(project_root))

block_cipher = None

a = Analysis(
    [r'E:\test\7.19\app\main.py'],
    pathex=[r'E:\test\7.19'],
    binaries=[],
    datas=[('E:\\test\\7.19\\app\\ui\\styles', 'app/ui/styles'), ('E:\\test\\7.19\\app\\config', 'app/config'), ('E:\\test\\7.19\\app\\plugins', 'app/plugins'), ('E:\\test\\7.19\\examples', 'examples'), ('E:\\test\\7.19\\README.md', '.')],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtNetwork', 'PySide6.QtMultimedia', 'requests', 'aiohttp', 'urllib3', 'yt_dlp', 'ffmpeg', 'sqlite3', 'asyncio', 'concurrent.futures', 'importlib.util', 'pkgutil', 'app.core', 'app.ui', 'app.services', 'app.plugins', 'app.data'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest', 'doctest', 'pdb', 'pydoc', 'help', 'tkinter', 'turtle', 'curses', 'readline', 'ftplib', 'poplib', 'imaplib', 'nntplib', 'telnetlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VideoDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'',
    version=r'E:\test\7.19\build_scripts\version_info.txt',
)



coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoDownloader',
)

