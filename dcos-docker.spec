# -*- mode: python -*-

block_cipher = None

datas = []
with open('MANIFEST.in') as manifest_file:
    for line in manifest_file.readlines():
        if line.startswith('recursive-include'):
            _, path, _ = line.split()
        else:
            _, path = line.split()
        if path.startswith('src/'):
            path_without_src = path[len('src/'):]
            datas.append((path, path_without_src))

a = Analysis(['bin/dcos-docker'],
             pathex=['/Users/Adam/Documents/mesosphere/dcos/dcos-e2e'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='dcos-docker',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
