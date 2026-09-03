#!/bin/bash
set -e
# Run from the repo root regardless of where this script is invoked from.
# (The spec file itself -- packaging/DnD5eCharacterCreator.spec -- resolves
# its own paths via SPECPATH, so it doesn't actually depend on this cd; but
# --distpath/--workpath below are plain CLI args resolved against CWD, so
# this still matters for dist/ and build/ landing at the repo root.)
cd "$(dirname "${BASH_SOURCE[0]}")/.."
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
# --clean wipes PyInstaller's own incremental analysis cache (the build/
# folder) and forces the whole Analysis phase from scratch every time —
# including collect_all('PySide6') re-walking the entire PySide6 install
# dir. Only do that after changing the spec file or upgrading a
# dependency: pass "clean" as an argument (./installer/build_exe.sh clean) when you
# actually need it; the default now leaves the cache in place.
CLEAN_FLAG=""
if [ "$1" = "clean" ]; then
    CLEAN_FLAG="--clean"
    echo "Clean build requested - this takes 2-5 minutes."
else
    echo "Incremental build - ~1 minute unless the spec changed."
    echo "Run './installer/build_exe.sh clean' to force a full rebuild."
fi
python3 -m PyInstaller $CLEAN_FLAG --distpath dist --workpath build packaging/DnD5eCharacterCreator.spec

echo
echo "=== Done! ==="
echo "App is in: dist/MIMIC/"
SIZE=$(du -sh dist/MIMIC/ 2>/dev/null || du -sh dist/MIMIC.exe 2>/dev/null | cut -f1 || echo "unknown")
echo "Build size: $SIZE"
