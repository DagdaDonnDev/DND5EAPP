#!/usr/bin/env bash
# One-time (re-runnable) setup: finds the Android SDK/NDK, PySide6 wheels
# and Qt Android jars, and writes their paths into
# dnd_app/ui_android/buildozer.spec. Run from WSL, or double-click
# setup_buildozer_spec.bat next to this file.
#
# Only the machine-specific path lines are touched: source.dir,
# android.sdk_path, android.ndk_path, p4a.local_recipes, p4a.hook,
# android.add_jars, android.icon and --icon= inside p4a.extra_args.
# Everything else (p4a.branch especially) is left alone. Paths the spec
# already has are kept if they still exist.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SPEC="$ROOT/dnd_app/ui_android/buildozer.spec"
WHEELS="$ROOT/packaging/android/wheels"

PYSIDE_VER="6.11.2"
WHEEL_TAG="cp311-cp311-android_aarch64"
PYSIDE_URL="https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-$PYSIDE_VER-$PYSIDE_VER-$WHEEL_TAG.whl"
SHIB_URL="https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-$PYSIDE_VER-$PYSIDE_VER-$WHEEL_TAG.whl"
JARS=(Qt6Android.jar Qt6AndroidBindings.jar Qt6AndroidQuick.jar)

die() { echo "ERROR: $*" >&2; exit 1; }
spec_value() {
    sed -nE "s/^$1[[:space:]]*=[[:space:]]*//p" "$SPEC" | head -1 | tr -d '\r' | sed 's/[[:space:]]*$//'
}
# Same lookup as clean_build_android.sh: pyenv's PATH setup normally only
# runs for interactive shells.
find_python311() {
    local root="${PYENV_ROOT:-$HOME/.pyenv}" c
    # Each candidate is test-run: a pyenv shim can exist yet fail
    # ("pyenv: python3.11: command not found") if 3.11 isn't selected.
    for c in "$(command -v python3.11 2>/dev/null)" "$root"/versions/3.11*/bin/python3.11 \
             "$root/shims/python3.11" /usr/local/bin/python3.11 /usr/bin/python3.11; do
        [ -n "$c" ] && [ -x "$c" ] && "$c" -c 'import sys' >/dev/null 2>&1 \
            && { echo "$c"; return; }
    done
    return 1
}
first_dir() {
    local d
    for d in "$@"; do
        [ -n "$d" ] && [ -d "$d" ] && { echo "$d"; return; }
    done
    return 1
}
has_jars() {
    local j
    for j in "${JARS[@]}"; do [ -f "$1/$j" ] || return 1; done
}

echo "=== MIMIC buildozer.spec setup ==="
echo "Project: $ROOT"
echo "Spec:    $SPEC"
[ -f "$SPEC" ] || die "buildozer.spec not found (expected DND5EAPP/dnd_app/ui_android/buildozer.spec)"

echo
echo "[0/6] Python 3.11 + buildozer"
PY="$(find_python311)" || die "python3.11 not found. Install with: pyenv install 3.11.9 && pyenv global 3.11.9"
echo "  Python:    $PY ($("$PY" --version 2>&1))"
BZ="$("$PY" -m buildozer --version 2>/dev/null | head -1 || true)"
[ -n "$BZ" ] || die "buildozer not installed for $PY. Run: $PY -m pip install --user buildozer cython"
echo "  $BZ"

echo "[1/6] Android SDK"
SDK="$(first_dir "$(spec_value 'android\.sdk_path')" \
                 "$HOME/.pyside6_android_deploy/android-sdk" \
                 "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}" "${ANDROIDSDK:-}")" \
    || die "Android SDK not found in the spec, ~/.pyside6_android_deploy/android-sdk, \$ANDROID_HOME, \$ANDROID_SDK_ROOT or \$ANDROIDSDK"
echo "  $SDK"

echo "[2/6] Android NDK"
NDK="$(first_dir "$(spec_value 'android\.ndk_path')" \
                 "$HOME/.pyside6_android_deploy/android-ndk/android-ndk-r28c" \
                 "${ANDROIDNDK:-}" "${ANDROID_NDK_HOME:-}" \
                 $(ls -d "$HOME"/.pyside6_android_deploy/android-ndk/*/ 2>/dev/null | sed 's#/$##'))" \
    || die "Android NDK not found in the spec, ~/.pyside6_android_deploy/android-ndk/, \$ANDROIDNDK or \$ANDROID_NDK_HOME"
echo "  $NDK"

echo "[3/6] PySide6/Shiboken6 wheels ($WHEELS)"
mkdir -p "$WHEELS"
fetch() {  # fetch <glob> <url>
    local hit
    hit="$(ls "$WHEELS"/$1 2>/dev/null | head -1 || true)"
    if [ -n "$hit" ]; then echo "  found $(basename "$hit")"; return; fi
    echo "  downloading $(basename "$2")"
    curl -fL --retry 3 -o "$WHEELS/$(basename "$2").part" "$2" \
        && mv "$WHEELS/$(basename "$2").part" "$WHEELS/$(basename "$2")" \
        || die "download failed: $2 -- download it manually into $WHEELS"
}
fetch "[Pp]y[Ss]ide6-*-android_aarch64.whl" "$PYSIDE_URL"
fetch "shiboken6-*-android_aarch64.whl" "$SHIB_URL"

echo "[4/6] Qt Android jars (${JARS[*]})"
CUR_JARS="$(spec_value 'android\.add_jars' | cut -d, -f1)"
JAR_DIR=""
for d in "${CUR_JARS%/*}" "$ROOT/deployment/jar/PySide6/jar" "$ROOT/packaging/android/jars"; do
    if [ -n "$d" ] && has_jars "$d"; then JAR_DIR="$d"; break; fi
done
if [ -z "$JAR_DIR" ]; then
    JAR_DIR="$ROOT/packaging/android/jars"
    echo "  extracting from the PySide6 wheel into $JAR_DIR"
    mkdir -p "$JAR_DIR"
    WHL="$(ls "$WHEELS"/[Pp]y[Ss]ide6-*-android_aarch64.whl | head -1)"
    "$PY" - "$WHL" "$JAR_DIR" "${JARS[@]}" <<'EOF'
import sys, zipfile
from pathlib import Path
whl, out, wanted = sys.argv[1], Path(sys.argv[2]), set(sys.argv[3:])
with zipfile.ZipFile(whl) as z:
    for name in z.namelist():
        if Path(name).name in wanted and "/jar/" in name:
            (out / Path(name).name).write_bytes(z.read(name))
EOF
    has_jars "$JAR_DIR" || die "the wheel didn't contain all of ${JARS[*]}"
fi
echo "  $JAR_DIR"

echo "[5/6] Updating buildozer.spec"
BACKUP="$SPEC.bak.$(date +%s)"
cp "$SPEC" "$BACKUP"
"$PY" - "$SPEC" "$ROOT" "$SDK" "$NDK" "$JAR_DIR" "${JARS[@]}" <<'EOF'
import re, sys
spec, root, sdk, ndk, jar_dir, *jars = sys.argv[1:]
text = open(spec, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in text else "\n"
icon = f"{root}/packaging/android/icon.png"
hook = f"{root}/deployment/recipes/p4a_hook.py"
values = {
    "source.dir": root,
    "android.sdk_path": sdk,
    "android.ndk_path": ndk,
    "p4a.local_recipes": f"{root}/deployment/recipes",
    "p4a.hook": hook,
    "android.add_jars": ",".join(f"{jar_dir}/{j}" for j in jars),
    "android.icon": icon,
}
for key, val in values.items():
    pat = re.compile(rf"(?m)^{re.escape(key)}[ \t]*=[^\r\n]*")
    if pat.search(text):
        text = pat.sub(lambda m: f"{key} = {val}", text, count=1)
    else:
        sys.exit(f"buildozer.spec has no '{key} =' line -- add one by hand, then re-run")
text = re.sub(r"--icon=\S+", lambda m: f"--icon={icon}", text)
open(spec, "w", encoding="utf-8", newline="").write(text)
EOF
if cmp -s "$SPEC" "$BACKUP"; then
    rm -f "$BACKUP"
    echo "  already up to date (no changes)"
else
    echo "  changed lines (backup: $BACKUP):"
    diff "$BACKUP" "$SPEC" | sed 's/^/    /' || true
fi

echo "[6/6] Verifying"
grep -E '^(source\.dir|android\.(sdk_path|ndk_path|add_jars|icon|apptheme)|p4a\.(local_recipes|branch|hook|extra_args))[[:space:]]*=' "$SPEC" | sed 's/^/  /'
grep -qE '^p4a\.branch[[:space:]]*=[[:space:]]*v2024\.01\.21' "$SPEC" \
    || echo "  WARNING: p4a.branch is not v2024.01.21 -- see BUILD_APK.md before building"
[ -f "$ROOT/deployment/recipes/p4a_hook.py" ] || echo "  WARNING: deployment/recipes/p4a_hook.py is missing"

echo
echo "=== Done ==="
echo "Next: double-click installer\\android\\clean_build_android.bat"
