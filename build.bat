@echo off
setlocal enabledelayedexpansion
title AeroMouse — Build Tool

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║    AERO MOUSE — Production Build Tool       ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ── Check prerequisites ────────────────────────────────────────────────────
echo [1/6] Checking prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.9-3.11 and add to PATH.
    goto :error
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from nodejs.org
    goto :error
)

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing PyInstaller...
    pip install pyinstaller
)

pip show mediapipe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dependencies not installed. Run: pip install -r requirements.txt
    goto :error
)

echo [OK] All prerequisites found.

:: ── Step 1: Install Python deps ────────────────────────────────────────────
echo.
echo [2/6] Installing Python dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    goto :error
)
echo [OK] Python dependencies ready.

:: ── Step 2: Build frontend ─────────────────────────────────────────────────
echo.
echo [3/6] Building React frontend...
cd frontend

call npm install --silent
if errorlevel 1 (
    echo [ERROR] npm install failed.
    cd ..
    goto :error
)

call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed.
    cd ..
    goto :error
)

cd ..
echo [OK] Frontend built → frontend\dist\

:: ── Check frontend dist exists ─────────────────────────────────────────────
if not exist "frontend\dist\index.html" (
    echo [ERROR] frontend\dist\index.html not found after build.
    goto :error
)

:: ── Step 3: Ensure data dirs exist ────────────────────────────────────────
echo.
echo [4/6] Preparing data directories...
if not exist "data\signatures" mkdir "data\signatures"
if not exist "data\signature_profiles" mkdir "data\signature_profiles"

:: Create .gitkeep files so dirs are included
if not exist "data\signatures\.gitkeep" type nul > "data\signatures\.gitkeep"
if not exist "data\signature_profiles\.gitkeep" type nul > "data\signature_profiles\.gitkeep"
echo [OK] Data directories ready.

:: ── Step 4: Clean previous build ──────────────────────────────────────────
echo.
echo [5/6] Cleaning previous build artifacts...
if exist "dist\AeroMouse" rmdir /s /q "dist\AeroMouse"
if exist "build\AeroMouse" rmdir /s /q "build\AeroMouse"
echo [OK] Clean done.

:: ── Step 5: Run PyInstaller ────────────────────────────────────────────────
echo.
echo [6/6] Running PyInstaller (this takes 2-5 minutes)...
pyinstaller AeroMouse.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    goto :error
)

:: ── Step 6: Post-Build Cleanup ──────────────────────────────────────────────
echo.
echo [POST] Distribution package ready.
echo [OK] Real credentials bundled seamlessly.

:: ── Package as ZIP ────────────────────────────────────────────────────────
echo.
echo [ZIP] Creating AeroMouse.zip...
powershell -Command "Compress-Archive -Path 'dist\AeroMouse\*' -DestinationPath 'dist\AeroMouse.zip' -Force"
if errorlevel 1 (
    echo [WARN] ZIP creation failed — distribute the dist\AeroMouse\ folder manually.
) else (
    echo [OK] Created dist\AeroMouse.zip
)

:: ── Summary ───────────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║  BUILD COMPLETE!                                    ║
echo  ║                                                     ║
echo  ║  Output: dist\AeroMouse\AeroMouse.exe              ║
echo  ║  Upload: dist\AeroMouse.zip → GitHub Releases      ║
echo  ║                                                     ║
echo  ║  Next steps:                                        ║
echo  ║  1. Test: double-click dist\AeroMouse\AeroMouse.exe ║
echo  ║  2. Upload dist\AeroMouse.zip to GitHub Releases   ║
echo  ║  3. Update DOWNLOAD_URL in Hero.tsx                ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
goto :end

:error
echo.
echo [FAILED] Build did not complete. Check errors above.
echo.
pause
exit /b 1

:end
pause
