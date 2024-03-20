# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['../afflux_gui.py'],
             pathex=[],
             binaries=[],
             datas=[('../plugins/disk_image.py', './plugins'),
                    ('../plugins/android_adb.py', './plugins'),
                    ('../plugins/usb_drive.py', './plugins'),
                    ('../plugins/apple_afc.py', './plugins'),
                    ('../plugins/generic_ftp.py', './plugins'),
                    ('../plugins/generic_smb.py', './plugins'),
                    ('../plugins/generic_ssh.py', './plugins')],
             hiddenimports=['adb_shell.adb_device',
                            'adb_shell.transport.usb_transport',
                            'adb_shell.auth.keygen',
                            'adb_shell.auth.sign_pythonrsa',
                            'adb_shell.exceptions',
                            'pymobiledevice3.lockdown',
                            'pymobiledevice3.services.afc',
                            'pysftp',
                            'smbprotocol',
                            'smbclient'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['tkinter', 'tcl', 'pillow', 'PIL'],
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
          name='afflux_gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='../gui/command.ico')
