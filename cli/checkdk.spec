# -*- mode: python ; coding: utf-8 -*-
#
# checkdk.spec — PyInstaller build specification
#
# Build a single-file standalone executable:
#
#   cd cli
#   pip install pyinstaller
#   pyinstaller checkdk.spec
#
# Output: cli/dist/checkdk  (or cli/dist/checkdk.exe on Windows)

import sys

block_cipher = None

# Hidden imports are required because:
#   - `dotenv` is imported inside a try/except in main.py → not found by analysis
#   - `websocket` is imported inside a try/except in commands/monitor.py
#   - `yaml` (pyyaml) uses a C extension that PyInstaller sometimes misses
#   - Various rich sub-modules are loaded lazily at runtime
HIDDEN_IMPORTS = [
    # click
    "click",
    # rich sub-modules (loaded lazily via importlib inside rich itself)
    "rich",
    "rich.console",
    "rich.panel",
    "rich.table",
    "rich.live",
    "rich.text",
    "rich.progress",
    "rich.rule",
    "rich.syntax",
    "rich.markup",
    "rich.logging",
    "rich._extension",
    # requests / urllib3 stack
    "requests",
    "urllib3",
    "urllib3.contrib",
    "charset_normalizer",
    "certifi",
    "idna",
    # pyyaml
    "yaml",
    "_yaml",
    # python-dotenv (deferred import in main.py)
    "dotenv",
    "dotenv.main",
    # websocket-client (deferred import in monitor.py)
    "websocket",
    "websocket._abnf",
    "websocket._core",
    "websocket._exceptions",
    "websocket._handshake",
    "websocket._http",
    "websocket._logging",
    "websocket._socket",
    "websocket._ssl_compat",
    "websocket._utils",
    # stdlib modules used by auth.py / chaos.py / monitor.py that
    # PyInstaller can miss (especially webbrowser with its dynamic
    # browser-backend imports)
    "webbrowser",
    "http",
    "http.server",
    "socket",
    "subprocess",
    "threading",
]

a = Analysis(
    ["checkdkcli/main.py"],
    pathex=["checkdkcli"],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Dev/test dependencies — do not bundle these
        "pytest",
        "black",
        "ruff",
        "setuptools",
        "wheel",
        "pip",
    ],
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
    name="checkdk",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,         # compress if UPX is available (reduces binary size)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,   # macOS: keep False for CLI tools
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
