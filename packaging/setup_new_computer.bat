@echo off
setlocal enableextensions
title MIMIC - set up this computer to build
REM One click: everything a new computer needs to build MIMIC.
REM   1. Python, for the Windows build (packaging\windows\build_exe.bat)
REM   2. Ubuntu in WSL, for the Android build (and WSL itself, if it's off)
REM   3. inside WSL, packaging/android/first_time_setup.sh: the Linux
REM      packages, Python 3.11, buildozer, Java 17, the Android SDK and NDK,
REM      the debug key, the p4a recipes and buildozer.spec's paths
REM Safe to run again: anything already there is skipped. If Windows has to
REM turn WSL on first, that needs a restart; then run this again to finish.
REM Exit codes are compared exactly (neq 0): wsl.exe fails with negative
REM codes, which "if errorlevel 1" never sees.
echo === MIMIC: set up this computer to build the app ===
echo.

REM -- 1. Python, for the Windows build --------------------------------------
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if %errorlevel% equ 0 goto have_python
echo [1/3] Python, for MIMIC.exe: installing Python 3.12...
where winget >nul 2>&1
if %errorlevel% neq 0 goto no_winget
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    echo   Python 3.12 is installed. New windows find it.
) else (
    echo   WARNING: Python didn't install. Get Python 3.12 from https://www.python.org/downloads/
    echo   and tick "Add python.exe to PATH". The Android part carries on.
)
goto python_done
:no_winget
echo   This Windows has no winget. Install Python 3.12 from https://www.python.org/downloads/
echo   and tick "Add python.exe to PATH". The Android part carries on.
goto python_done
:have_python
for /f "delims=" %%V in ('python --version 2^>^&1') do echo [1/3] Python, for MIMIC.exe: %%V, already there
:python_done
echo.

REM -- 2. Ubuntu in WSL, for the Android build -------------------------------
REM (<nul: a Linux that hasn't made its account yet can't sit waiting for one)
wsl.exe -e true <nul >nul 2>&1
if %errorlevel% equ 0 goto have_wsl
echo [2/3] Ubuntu in WSL, for MIMIC.apk: installing Ubuntu 24.04 (a few minutes)
wsl.exe --install -d Ubuntu-24.04 --no-launch
if %errorlevel% neq 0 (
    echo   Turning WSL on needs administrator rights: Windows asks for permission.
    powershell -NoProfile -Command "Start-Process wsl.exe -ArgumentList '--install','-d','Ubuntu-24.04','--no-launch' -Verb RunAs -Wait"
)
echo.
echo   Ubuntu now opens once, to make your Linux account: type a user name, then a
echo   password twice (typing a password shows nothing - that's normal). When you
echo   see a line ending in $, type exit and press Enter.
echo.
wsl.exe -d Ubuntu-24.04
wsl.exe -e true <nul >nul 2>&1
if %errorlevel% equ 0 goto have_wsl
echo.
echo   Ubuntu isn't ready yet: Windows needs a restart to finish turning WSL on.
echo   Restart, then double-click this file again.
pause
exit /b 0
:have_wsl
echo [2/3] Ubuntu in WSL, for MIMIC.apk: ready
echo.

REM -- 3. The Android build tools, inside WSL ---------------------------------
echo [3/3] The Android build tools, inside WSL. The first time takes 20-40 minutes,
echo   and asks for your Linux password once.
set "WSL_PATH="
for /f "usebackq delims=" %%P in (`wsl.exe wslpath -a "%~dp0android"`) do set "WSL_PATH=%%P"
if not defined WSL_PATH (
    echo ERROR: couldn't find this folder from inside WSL.
    pause
    exit /b 1
)
wsl.exe bash -ic "cd '%WSL_PATH%' && bash ./first_time_setup.sh"
if %errorlevel% neq 0 (
    echo.
    echo FAILED - see the error above. Fix it and double-click this file again:
    echo the steps that finished are skipped.
    pause
    exit /b 1
)
echo.
echo === This computer is ready to build MIMIC ===
echo   MIMIC.exe: double-click packaging\windows\build_exe.bat
echo   MIMIC.apk: double-click packaging\android\clean_build_android.bat
pause
