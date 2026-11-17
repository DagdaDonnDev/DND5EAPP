@echo off
cd /d "%~dp0.."
if exist "docs\images\android-bestiary.png" del /q "docs\images\android-bestiary.png"
echo Old files removed.
(goto) 2>nul & del "%~f0"
