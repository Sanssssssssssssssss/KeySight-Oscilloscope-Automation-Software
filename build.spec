# build.spec 文件

from PyInstaller.utils.hooks import collect_data_files
import os

# 收集所有数据文件 (如 JSON, PNG)
datas = collect_data_files('.', include_py_files=True)

# 添加其他的静态文件
datas += [
    ('config.txt', '.'),  # 添加 config.txt 文件
    ('measurement_config.json', '.'),  # 添加 measurement_config.json 文件
    ('screenshot.png', '.'),  # 添加 screenshot.png 文件
    ('axis_config.json','.'),
    ('configurations.json','.'),
    ('script.json','.'),
    ('waveform_config.json','.')
]

a = Analysis(
    ['main.py'],  # 你的主脚本文件
    pathex=['C:\\Users\\ROG\\PycharmProjects\\KeysightSoftware'],
    binaries=[],
    datas=datas,  # 包含数据文件
    hiddenimports=[],  # 隐藏导入的模块
    hookspath=[],  # hook 路径
    hooksconfig={},
    runtime_hooks=[],  # 运行时的 hooks
    excludes=[],  # 不包含的模块
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KeysightSoftware',  # 输出的可执行文件名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 如果是 GUI 应用，设置为 False
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KeysightSoftware',
)
