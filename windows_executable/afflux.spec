# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import get_package_paths

block_cipher = None
# Just use this to get the site-packages directory for python-snappy dlls we need.
snappy_libs = get_package_paths('setuptools')[0] + "python_snappy.libs"

a = Analysis(['..\\afflux.py'],
             pathex=[],
             binaries=[],
             datas=[('..\\plugins\\*.py', '.\\plugins'),(snappy_libs, '.\\python_snappy.libs')],
             hiddenimports=['adb_shell.adb_device',
                            'adb_shell.transport.usb_transport',
                            'adb_shell.auth.keygen',
                            'adb_shell.auth.sign_pythonrsa',
                            'adb_shell.exceptions',
                            'pymobiledevice3.lockdown',
                            'pymobiledevice3.services.afc',
                            'pysftp',
                            'smbprotocol',
                            'smbclient',
                            'bs4',
                            'requests'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['PyQt5', 'tk', 'tkinter', 'tcl', 'PIL'],
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
          name='afflux',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='..\\gui\\command.ico')
