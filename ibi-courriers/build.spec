# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - IBI COURRIERS (onedir, windowed)

import os

from PyInstaller.utils.hooks import collect_all

block_cipher = None

ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")

_icon = "assets/logo.ico" if os.path.isfile("assets/logo.ico") else None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=ctk_binaries,
    datas=[
        *ctk_datas,
        ("assets", "assets"),
    ],
    hiddenimports=[
        *ctk_hiddenimports,
        "PIL",
        "PIL.Image",
        "PIL._tkinter_finder",
        "reportlab",
        "bcrypt",
        "sqlite3",
        "utils.chemin_app",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_exe_kw = {
    "exclude_binaries": True,
    "name": "IBI_COURRIERS",
    "debug": False,
    "bootloader_ignore_signals": False,
    "strip": False,
    "upx": True,
    "console": False,
    "disable_windowed_traceback": False,
    "argv_emulation": False,
    "target_arch": None,
    "codesign_identity": None,
    "entitlements_file": None,
}
if _icon:
    _exe_kw["icon"] = _icon

exe = EXE(
    pyz,
    a.scripts,
    [],
    **_exe_kw,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="IBI_COURRIERS",
)
