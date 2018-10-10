# -*- mode: python -*-

block_cipher = None


a = Analysis(['bin/dcos-docker'],
             pathex=['/Users/Adam/Documents/mesosphere/dcos/dcos-e2e'],
             binaries=[],
             datas=[('src/dcos_e2e/backends/_aws/resources', 'dcos_e2e/backends/_aws/resources'), ('src/dcos_e2e/backends/_docker/resources', 'dcos_e2e/backends/_docker/resources'), ('src/dcos_e2e/backends/_vagrant/resources', 'dcos_e2e/backends/_vagrant/resources'), ('src/cli/_vendor', 'cli/_vendor'), ('src/dcos_e2e/_vendor', 'dcos_e2e/_vendor'), ('src/cli/dcos_docker/commands/docker-mac-network-master', 'cli/dcos_docker/commands/docker-mac-network-master'), ('src/cli/dcos_docker/commands/openvpn', 'cli/dcos_docker/commands/openvpn'), ('src/dcos_e2e', 'dcos_e2e')],
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
