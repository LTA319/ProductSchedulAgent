block_cipher = None

a = Analysis(
    ['ui/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data_layer', 'data_layer'),
        ('business_logic', 'business_logic'),
        ('ui', 'ui'),
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'streamlit',
        'ortools',
        'pandas',
        'plotly',
        'openpyxl',
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ProductionScheduler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)