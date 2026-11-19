@echo off
rem Run from the DND5EAPP folder: removes the old copy of splash.gif (it now lives in dnd_app\core).
cd /d "%~dp0"
if exist "dnd_app\ui_desktop\splash\splash.gif" del "dnd_app\ui_desktop\splash\splash.gif"
echo Done.
pause
