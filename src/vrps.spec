# -*- mode: python -*-

block_cipher = None


a = Analysis(['vrps.py'],
             pathex=['C:\\code\\vrps\\src'],
             binaries=[],
             datas=[],
             hiddenimports=['ortools.constraint_solver.routing_parameters_pb2'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='vrps',
          debug=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=False )
