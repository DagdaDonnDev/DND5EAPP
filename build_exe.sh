#!/bin/bash
set -e
echo "=== MIMIC — EXE Builder ==="
echo

echo "Step 1: Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install PySide6 pyinstaller

echo
echo "Step 2: Verifying PySide6..."
python3 -c "import PySide6; print('PySide6', PySide6.__version__, 'OK')"

echo
echo "Step 3: Building app using spec file..."
python3 -m PyInstaller --clean DnD5eCharacterCreator.spec

echo
echo "=== Done! ==="
echo "App is in: dist/MIMIC/"
SIZE=$(du -sh dist/MIMIC/ 2>/dev/null || du -sh dist/MIMIC.exe 2>/dev/null | cut -f1 || echo "unknown")
echo "Build size: $SIZE"
