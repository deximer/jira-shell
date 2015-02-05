# -*- mode: python -*-
a = Analysis(['jira.py'],
             pathex=['/Users/jstark/wrk/jira-shell/jira'],
             hiddenimports=['scipy.special._ufuncs_cxx', 'interface'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='jira',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='jira')
