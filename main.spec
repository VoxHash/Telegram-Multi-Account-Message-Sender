# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Telegram Multi-Account Message Sender.

- Windows / Linux: one-file windowed (Linux CI may force console=True)
- macOS: onedir + .app bundle with Info.plist document types for .tmas-backup.zip
"""

import os
import sys

block_cipher = None
is_darwin = sys.platform == "darwin"

# Bundle each translation JSON explicitly (reliable for one-file PyInstaller builds)
_translation_datas = [
    (os.path.join("app", "translations", name), os.path.join("app", "translations"))
    for name in os.listdir(os.path.join("app", "translations"))
    if name.endswith(".json")
]

_icon_ico = "assets/icons/favicon.ico"
_icon_icns = "packaging/macos/AppIcon.icns"
_icon_png = "packaging/macos/AppIcon.png"
if is_darwin and os.path.exists(_icon_icns):
    _icon = _icon_icns
elif is_darwin and os.path.exists(_icon_png):
    _icon = _icon_png
elif os.path.exists(_icon_ico):
    _icon = _icon_ico
else:
    _icon = None

_info_plist = {
    "CFBundleName": "Telegram Multi-Account Message Sender",
    "CFBundleDisplayName": "Telegram Multi-Account Message Sender",
    "CFBundleIdentifier": "dev.voxhash.telegram-multi-account-sender",
    "CFBundleShortVersionString": "1.2.23",
    "CFBundleVersion": "1.2.23",
    "CFBundlePackageType": "APPL",
    "LSMinimumSystemVersion": "10.15",
    "NSHighResolutionCapable": True,
    "LSApplicationCategoryType": "public.app-category.productivity",
    "CFBundleDocumentTypes": [
        {
            "CFBundleTypeName": "TMAS Backup Package",
            "CFBundleTypeRole": "Viewer",
            "LSHandlerRank": "Owner",
            "CFBundleTypeExtensions": ["tmas-backup.zip"],
            "LSItemContentTypes": ["dev.voxhash.tmas-backup"],
        }
    ],
    "UTExportedTypeDeclarations": [
        {
            "UTTypeIdentifier": "dev.voxhash.tmas-backup",
            "UTTypeDescription": "Telegram Multi-Account Message Sender backup",
            "UTTypeConformsTo": ["public.zip-archive", "public.data"],
            "UTTypeTagSpecification": {
                "public.filename-extension": ["tmas-backup.zip"],
            },
        }
    ],
}

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=_translation_datas
    + [
        ("assets", "assets"),
        ("packaging/linux/application-x-tmas-backup.xml", "packaging/linux"),
        (
            "packaging/linux/dev.voxhash.telegram-multi-account-sender.desktop",
            "packaging/linux",
        ),
    ],
    hiddenimports=[
        "app.gui.widgets.telegram_selector",
        "app.core.launch_args",
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "telethon",
        "sqlmodel",
        "pydantic",
        "pandas",
    ],
    hookspath=["hooks"],
    hooksconfig={},
    runtime_hooks=["runtime_hook.py"],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if is_darwin:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="telegram-multi-account-sender",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=_icon,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="telegram-multi-account-sender",
    )
    app = BUNDLE(
        coll,
        name="Telegram Multi-Account Message Sender.app",
        icon=_icon,
        bundle_identifier="dev.voxhash.telegram-multi-account-sender",
        info_plist=_info_plist,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="telegram-multi-account-sender",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=_icon,
    )
