from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


SPEC_PATH = globals().get("SPEC")
ROOT = Path(SPEC_PATH).resolve().parent if SPEC_PATH else Path.cwd()
CONFIGS_DIR = ROOT / "configs"

datas = collect_data_files("keysight_software")
hiddenimports = collect_submodules("keysight_software")
hiddenimports += [
    "matplotlib.backends.backend_qtagg",
]

if CONFIGS_DIR.exists():
    for path in CONFIGS_DIR.glob("*"):
        if path.is_file():
            datas.append((str(path), "configs"))

for filename in ("config.txt",):
    path = ROOT / filename
    if path.exists():
        datas.append((str(path), "."))


a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    exclude_binaries=False,
    name="KeysightSoftware",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
