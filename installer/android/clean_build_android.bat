@echo off
REM Clean release build of the MIMIC APK: kills leftover build processes,
REM clears previous build outputs and staging, pre-flights p4a_hook.py,
REM stages main.py + dnd_app/, runs buildozer android release and converts
REM the AAB to an APK in dist\. Keeps the expensive compiled caches
REM (libs/arm64-v8a, _python_bundle*, other_builds).
REM
REM Runs in an interactive bash (-ic) so ~/.bashrc is read and pyenv's
REM python3.11, java, adb etc. resolve exactly as in a WSL terminal;
REM -lc skips the pyenv setup in ~/.bashrc. "%~dp0." not "%~dp0": a
REM trailing backslash would escape the closing quote.
title MIMIC clean Android build
for /f "usebackq delims=" %%P in (`wsl.exe wslpath -a "%~dp0."`) do set "WSL_PATH=%%P"
if not defined WSL_PATH (
    echo ERROR: could not resolve this folder to a WSL path - is WSL installed?
    pause
    exit /b 1
)
wsl.exe bash -ic "cd '%WSL_PATH%' && bash ./clean_build_android.sh"
if errorlevel 1 (
    echo.
    echo FAILED - see the error above.
) else (
    echo.
    echo Finished OK.
)
pause
