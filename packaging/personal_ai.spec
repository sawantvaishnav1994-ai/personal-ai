# -*- mode: python ; coding: utf-8 -*-
a=Analysis(['app/main.py'],pathex=['.'],binaries=[],datas=[],hiddenimports=['keyring.backends','uvicorn.logging','uvicorn.loops.auto','uvicorn.protocols.http.auto','uvicorn.protocols.websockets.auto'],hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False)
pyz=PYZ(a.pure);exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='PersonalAI',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False);coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,upx_exclude=[],name='PersonalAI')
