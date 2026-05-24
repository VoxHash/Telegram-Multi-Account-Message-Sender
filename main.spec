# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Telegram Multi-Account Message Sender.
This ensures all modules, including telegram_selector, are properly included.
"""

import os

block_cipher = None

# Bundle each translation JSON explicitly (reliable for one-file PyInstaller builds)
_translation_datas = [
    (os.path.join("app", "translations", name), os.path.join("app", "translations"))
    for name in os.listdir(os.path.join("app", "translations"))
    if name.endswith(".json")
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=_translation_datas + [
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'app.gui.widgets.telegram_selector',  # Module is included via direct import, but keep as backup
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'telethon',
        'sqlmodel',
        'pydantic',
        'pandas',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='telegram-multi-account-sender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for Windows console, False for windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/favicon.ico' if os.path.exists('assets/icons/favicon.ico') else None,
)

