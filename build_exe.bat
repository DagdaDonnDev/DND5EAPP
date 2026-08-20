@echo off
setlocal enabledelayedexpansion
echo === MIMIC - Windows Builder ===
echo.

REM ── Step 1: Dependencies ─────────────────────────────────────────────────
echo [1/3] Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install PySide6 pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is in PATH.
    pause & exit /b 1
)

REM ── Step 2: Verify ───────────────────────────────────────────────────────
echo [2/3] Verifying installation...
python -c "import PySide6; print('  PySide6', PySide6.__version__, 'OK')"
python -c "import PyInstaller; print('  PyInstaller', PyInstaller.__version__, 'OK')"

REM ── Step 3: Build ─────────────────────────────────────────────────────────
echo [3/3] Building...
echo   This takes 2-5 minutes on first run.
echo.
python -m PyInstaller --clean --noconfirm DnD5eCharacterCreator.spec
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed. Common causes:
    echo   - Missing icon file: make sure dnd_app\icon.ico exists
    echo   - Antivirus blocking: temporarily disable AV during build
    echo   - Port still running: close any running instance of the app
    pause & exit /b 1
)

REM ── Done ──────────────────────────────────────────────────────────────────
echo.
echo === Build complete! ===
echo Output: dist\MIMIC.exe
for %%F in (dist\MIMIC.exe) do echo Size: %%~zF bytes
echo.
echo To distribute: copy dist\MIMIC.exe to any Windows machine.
echo No Python installation required on the target machine.
pause
