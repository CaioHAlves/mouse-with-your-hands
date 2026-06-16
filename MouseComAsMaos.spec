# -*- mode: python ; coding: utf-8 -*-
"""Receita do PyInstaller para empacotar o app em um executável (onedir).

Usada tanto na build local quanto no workflow do GitHub Actions. Pontos-chave:

- collect_all('mediapipe'): o MediaPipe traz arquivos de dados (.tflite,
  .binarypb, grafos) que o PyInstaller nao descobre sozinho. Sem isso o
  executavel compila mas quebra ao abrir.
- datas com hand_landmarker.task: empacota o modelo (~8 MB) ao lado do
  executavel, no mesmo lugar onde hand_tracker.py o procura
  (Path(__file__).parent), para o app rodar offline.
- pyautogui como hidden import: ele e importado de forma tardia em
  controller.py, entao o PyInstaller pode nao detecta-lo sozinho.

Modo onedir (exclude_binaries + COLLECT): arranque mais rapido que o onefile
e as configuracoes (settings.json) persistem na pasta do app entre execucoes.
"""

from PyInstaller.utils.hooks import collect_all

datas = [("hand_landmarker.task", ".")]
binaries = []
hiddenimports = ["pyautogui"]

mp_datas, mp_binaries, mp_hiddenimports = collect_all("mediapipe")
datas += mp_datas
binaries += mp_binaries
hiddenimports += mp_hiddenimports


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MouseComAsMaos",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MouseComAsMaos",
)
