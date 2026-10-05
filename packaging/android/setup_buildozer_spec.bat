@echo off
REM One-time (re-runnable) setup: finds the Android SDK/NDK, PySide6
REM wheels and Qt Android jars and writes their paths into
REM dnd_app\ui_android\buildozer.spec. Logic is in setup_buildozer_spec.sh.
REM
REM Runs in an interactive bash (-ic) so ~/.bashrc is read and pyenv's
REM python3.11, java, adb etc. resolve exactly as in a WSL terminal;
REM -lc skips the pyenv setup in ~/.bashrc. "%~dp0." not "%~dp0": a
REM trailing backslash would escape the closing quote.
title MIMIC buildozer.spec setup
for /f "usebackq delims=" %%P in (`wsl.exe wslpath -a "%~dp0."`) do set "WSL_PATH=%%P"
if not defined WSL_PATH (
    echo ERROR: could not resolve this folder to a WSL path - is WSL installed?
    pause
    exit /b 1
)
wsl.exe bash -ic "cd '%WSL_PATH%' && bash ./setup_buildozer_spec.sh"
if errorlevel 1 (
    echo.
    echo FAILED - see the error above.
) else (
    echo.
    echo Finished OK.
)
pause
