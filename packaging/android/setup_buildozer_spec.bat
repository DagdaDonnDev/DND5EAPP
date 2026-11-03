@echo off
REM One-time (re-runnable) setup: finds the Android SDK/NDK, the PySide6
REM wheels and the Qt Android jars, and writes their paths -- and the p4a
REM recipes' -- into dnd_app\ui_android\buildozer.spec. Logic is in
REM setup_buildozer_spec.sh. (A new computer: packaging\setup_new_computer.bat.)
REM
REM Runs in an interactive bash (-ic) so ~/.bashrc is read and pyenv's
REM python3.11, java, adb etc. resolve exactly as in a WSL terminal;
REM -lc skips the pyenv setup in ~/.bashrc. "%~dp0." not "%~dp0": a
REM trailing backslash would escape the closing quote.
title MIMIC buildozer.spec setup
wsl.exe -e true <nul >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: WSL has no Linux to run this in yet - double-click
    echo packaging\setup_new_computer.bat first.
    pause
    exit /b 1
)
for /f "usebackq delims=" %%P in (`wsl.exe wslpath -a "%~dp0."`) do set "WSL_PATH=%%P"
if not defined WSL_PATH (
    echo ERROR: could not resolve this folder to a WSL path - is WSL installed?
    pause
    exit /b 1
)
wsl.exe bash -ic "cd '%WSL_PATH%' && bash ./setup_buildozer_spec.sh"
if %errorlevel% neq 0 (
    echo.
    echo FAILED - see the error above.
) else (
    echo.
    echo Finished OK.
)
pause
