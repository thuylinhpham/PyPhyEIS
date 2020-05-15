# -*- mode: python -*-

block_cipher = None


a = Analysis(['PyPhyEIS.spec'],
             pathex=['./'],
             binaries=[('C:/Miniconda3/envs/impedanceUI/Lib/site-packages/PyQt5/Qt/bin/QtWebEngineProcess.exe', './')],
             datas=[('C:/Miniconda3/envs/impedanceUI/Lib/site-packages/plotly/package_data/', './plotly/package_data/'), ('C:/Miniconda3/envs/impedanceUI/Lib/site-packages/PyQt5/Qt/resources/', './'), ('./models', './models'), ('./icon.ico', '.'), ('./PyPhyEIS.qml', './'), ('C:/Miniconda3/envs/impedanceUI/Lib/site-packages/scipy/.libs', './'), ('C:/Miniconda3/envs/impedanceUI/Lib/site-packages/plotly/validators', './plotly/validators')],
             hiddenimports=["PyQt5.QtWidgets", "PyQt5.QtQml", "PyQt5.QtCore", "PyQt5.QtGui", "pandas._libs.tslibs.timedeltas", "numpy", "mpmath","scipy._lib.messagestream", "plotly", "plotly.graph_objs"],
             hookspath=[],
             runtime_hooks=[],
             excludes=['matplotlib'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='PyPhyEIS',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='./icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='PyPhyEIS')
