# -*- mode: python ; coding: utf-8 -*-
"""
AeroMouse PyInstaller Spec File
Bundles: Python backend + MediaPipe models + pre-built React frontend
Output: dist/AeroMouse/ folder (zip this for distribution)

Usage:
    pyinstaller AeroMouse.spec
"""

import os
import sys
import mediapipe

# ── Paths ─────────────────────────────────────────────────────────────────────
SPEC_DIR       = os.path.dirname(os.path.abspath(SPEC))          # project root
BACKEND_DIR    = os.path.join(SPEC_DIR, 'backend')
FRONTEND_DIST  = os.path.join(SPEC_DIR, 'frontend', 'dist')
MEDIAPIPE_DIR  = os.path.dirname(mediapipe.__file__)

# ── Collect all mediapipe data files ──────────────────────────────────────────
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

mp_datas       = collect_data_files('mediapipe')
mp_binaries    = collect_dynamic_libs('mediapipe')

# ── Extra datas to bundle ──────────────────────────────────────────────────────
extra_datas = [
    # Pre-built React frontend
    (FRONTEND_DIST, 'frontend/dist'),
    # Actual environment variables (so end users don't have to configure anything)
    (os.path.join(BACKEND_DIR, '.env'), '.'),
    # Data directories (for local signature fallback)
    (os.path.join(SPEC_DIR, 'data', 'signatures'),    'data/signatures'),
    (os.path.join(SPEC_DIR, 'data', 'signature_profiles'), 'data/signature_profiles'),
]

a = Analysis(
    [os.path.join(BACKEND_DIR, 'app.py')],
    pathex=[BACKEND_DIR, SPEC_DIR],
    binaries=mp_binaries,
    datas=mp_datas + extra_datas,
    hiddenimports=[
        # MediaPipe
        'mediapipe',
        'mediapipe.python',
        'mediapipe.python.solutions',
        'mediapipe.python.solutions.hands',
        'mediapipe.python.solutions.face_mesh',
        'mediapipe.tasks',
        # OpenCV
        'cv2',
        # Flask ecosystem
        'flask',
        'flask_cors',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.middleware',
        'werkzeug.middleware.proxy_fix',
        'jinja2',
        'click',
        'itsdangerous',
        # Input control
        'pyautogui',
        'pynput',
        'pynput.mouse',
        'pynput.keyboard',
        'pynput.mouse._win32',
        'pynput.keyboard._win32',
        # Database
        'psycopg2',
        'psycopg2._psycopg',
        'psycopg2.extensions',
        'psycopg2.pool',
        # Cloudinary
        'cloudinary',
        'cloudinary.uploader',
        'cloudinary.api',
        # Scientific / ML
        'numpy',
        'scipy',
        'scipy.spatial',
        'scipy.spatial.distance',
        'fastdtw',
        # Image processing
        'PIL',
        'PIL.Image',
        # Utilities
        'dotenv',
        'python_dotenv',
        'certifi',
        'urllib3',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'test',
        'unittest',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AeroMouse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # Keep console for startup logs & error visibility
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='frontend/public/favicon.ico',  # Uncomment if you have an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AeroMouse',
)
