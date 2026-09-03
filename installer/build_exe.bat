@echo off
setlocal enabledelayedexpansion
REM Run from the repo root regardless of where this script is invoked
REM from. (The spec file itself -- packaging\DnD5eCharacterCreator.spec --
REM resolves its own paths via SPECPATH, so it doesn't actually depend on
REM this cd; but --distpath/--workpath below are plain CLI args resolved
REM against CWD, so this still matters for dist\ and build\ landing at
REM the repo root.)
cd /d "%~dp0.."
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
REM --clean wipes PyInstaller's own incremental analysis cache (the build\
REM folder) and forces it to redo the entire Analysis phase from scratch —
REM including collect_all('PySide6') re-walking the whole PySide6 install
REM dir — every single time. That's the right thing to do after changing
REM the spec file or upgrading a dependency, but NOT on every routine
REM build; pass "clean" as an argument (installer\build_exe.bat clean) when you
REM actually need it. Default here now leaves the cache in place, which is
REM what gets subsequent builds down to the ~1 minute BUILD_EXE.md
REM describes instead of always paying the from-scratch cost.
set PYI_CLEAN_FLAG=
if /I "%~1"=="clean" set PYI_CLEAN_FLAG=--clean
echo [3/3] Building...
if defined PYI_CLEAN_FLAG (
    echo   Clean build requested - this takes 2-5 minutes.
) else (
    echo   Incremental build - ~1 minute unless the spec changed.
    echo   Run "installer\build_exe.bat clean" to force a full rebuild.
)
echo.
python -m PyInstaller %PYI_CLEAN_FLAG% --noconfirm --distpath dist --workpath build packaging\DnD5eCharacterCreator.spec
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed. Common causes:
    echo   - Missing icon file: make sure dnd_app\ui\icon.ico exists
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
