#!/usr/bin/env bash
# Clean release build of the MIMIC APK (run from WSL, or via
# clean_build_android.bat from Windows).
#
# "Clean" here means: every output and every patched/generated file from
# a previous run is thrown away, but the expensive compiled caches are
# kept -- $DIST/libs/arm64-v8a, $DIST/_python_bundle*, and
# .buildozer/android/platform/build-arm64-v8a/build/other_builds (Qt +
# Python cross-compiled for arm64; regenerating them costs 30-45 min).
#
# Steps:
#   1. kill any leftover buildozer / p4a / Gradle / aapt2 processes
#   2. clear the dist's Gradle outputs, old bin/ artifacts, and the
#      staging dir; reset PythonActivity.java to p4a's pristine template
#      so p4a_hook.py patches it from scratch
#   3. pre-flight p4a_hook.py: run its Java patch against that template
#      and check every marker it asserts on at build time is present
#   4. stage main.py + README.md + dnd_app/ into /tmp/mimic-app-staging (the
#      --private dir buildozer.spec's p4a.extra_args points p4a at)
#   5. buildozer android release, logged to /tmp/mimic-build-*.log
#   6. turn the .aab into an installable universal APK in dist/ via
#      deployment/make-android-apk.sh (bundletool is downloaded to
#      ~/.cache/mimic/ on first use; the debug keystore is created if
#      missing). No APK at the end counts as a failed build.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UI="$ROOT/dnd_app/ui_android"
SPEC="$UI/buildozer.spec"
HOOK="$ROOT/deployment/recipes/p4a_hook.py"
DIST="$UI/.buildozer/android/platform/build-arm64-v8a/dists/mimic"
P4A="$UI/.buildozer/android/platform/python-for-android"
JAVA_REL="src/main/java/org/kivy/android/PythonActivity.java"
TEMPLATE="$P4A/pythonforandroid/bootstraps/qt/build/$JAVA_REL"
STAGE="/tmp/mimic-app-staging"
LOG="/tmp/mimic-build-$(date +%Y%m%d-%H%M%S).log"
# python3.11 is a pyenv install on the build machine; pyenv's PATH setup
# usually lives in ~/.bashrc, which non-interactive shells (wsl.exe
# bash -lc ...) skip. Fall back to pyenv's own paths so this works either way.
find_python311() {
    if [ -n "${PYTHON:-}" ]; then echo "$PYTHON"; return; fi
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

step() { echo; echo "=== $* ==="; }
die()  { echo "ERROR: $*" >&2; exit 1; }

# buildozer.spec hardcodes this tree's absolute path (source.dir, hook,
# recipes, jars, icon). Building from any other checkout would silently
# compile *that* path's code instead of this one's.
SPEC_SRC="$(sed -nE 's/^source\.dir[[:space:]]*=[[:space:]]*//p' "$SPEC" | head -1 | tr -d '\r' | sed 's/[[:space:]]*$//')"
[ "$SPEC_SRC" = "$ROOT" ] || die "buildozer.spec source.dir is '$SPEC_SRC' but this script lives in '$ROOT'"
PY="$(find_python311)" || die "python3.11 not found on PATH or under ${PYENV_ROOT:-$HOME/.pyenv}"
echo "Python: $PY"
command -v rsync >/dev/null || die "rsync not found (sudo apt install rsync)"

step "1/6 Stopping leftover build processes"
PATTERN='buildozer|pythonforandroid|GradleDaemon|aapt2'
# Plain `pkill -f` would also match this script's own parent shell if its
# command line happens to contain e.g. ".buildozer", so skip our ancestry.
ancestors() {
    local p=$$
    while [ -n "$p" ] && [ "$p" -gt 1 ]; do
        echo "$p"
        p="$(ps -o ppid= -p "$p" | tr -d ' ')"
    done
}
leftovers() { pgrep -f "$PATTERN" | grep -vxF -f <(ancestors) || true; }
for sig in TERM KILL; do
    PIDS="$(leftovers)"
    [ -n "$PIDS" ] || break
    # shellcheck disable=SC2086
    kill -s "$sig" $PIDS 2>/dev/null || true
    sleep 2
done
PIDS="$(leftovers)"
if [ -n "$PIDS" ]; then
    # shellcheck disable=SC2086
    ps -o pid=,args= -p $PIDS
    die "processes above are still running"
fi
echo "(clean)"

step "2/6 Clearing previous build outputs"
if [ -d "$DIST" ]; then
    rm -rf "${DIST:?}/build" "${DIST:?}/.gradle"
    if [ -f "$TEMPLATE" ]; then
        # Not just rm: when p4a reuses an existing dist ("mimic has
        # compatible recipes, using this one") it never re-copies the
        # bootstrap's Java sources, so a deleted PythonActivity.java stays
        # deleted and the hook has nothing to patch. Resetting it to the
        # template gives the same from-scratch patch a fresh dist gets.
        cp "$TEMPLATE" "$DIST/$JAVA_REL"
        echo "PythonActivity.java reset to p4a template"
    else
        echo "WARNING: p4a template not found at $TEMPLATE;"
        echo "         keeping the dist's PythonActivity.java (p4a_hook.py migrates it in place)"
    fi
    echo "kept: $(ls -d "$DIST"/libs/arm64-v8a "$DIST"/_python_bundle* 2>/dev/null | xargs -r -n1 basename | tr '\n' ' ')"
else
    echo "no dist yet at $DIST -- p4a will build it from scratch (30-45 min)"
fi
rm -f "$UI"/bin/*.aab "$UI"/bin/*.apk
rm -rf "${STAGE:?}"
echo "cleared: dist build/ + .gradle/, bin/*.aab + *.apk, $STAGE"

step "3/6 Pre-flight check of p4a_hook.py"
"$PY" - "$HOOK" "$TEMPLATE" <<'EOF'
import ast, importlib.util, shutil, sys, tempfile, types
from pathlib import Path

hook_path, template = sys.argv[1], Path(sys.argv[2])
ast.parse(Path(hook_path).read_text(), hook_path)
print("hook parses OK")

# The hook imports pythonforandroid.logger; stub it so this check runs
# without p4a's own dependencies on sys.path.
pkg = types.ModuleType("pythonforandroid")
log = types.ModuleType("pythonforandroid.logger")
log.info = log.warning = lambda *a, **k: None
sys.modules.update({"pythonforandroid": pkg, "pythonforandroid.logger": log})
spec = importlib.util.spec_from_file_location("p4a_hook", hook_path)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

if not template.exists():
    print(f"skipping patch dry-run: no p4a template at {template}")
    sys.exit(0)
with tempfile.TemporaryDirectory() as tmp:
    java = Path(tmp) / "PythonActivity.java"
    shutil.copy(template, java)
    hook._patch_java_file(java)
    first = java.read_text()
    hook._patch_java_file(java)
    if java.read_text() != first:
        sys.exit("FAIL: _patch_java_file is not idempotent")

# Same markers before_apk_assemble asserts on at build time.
needles = ("Qt6Core_arm64-v8a",
           "invoking QtNative.startApplication",
           '__m.invoke(null, "", __mainLib);',
           "QtNative.startApplication returned")
missing = [n for n in needles if n not in first]
if missing:
    sys.exit(f"FAIL: patched PythonActivity.java is missing {missing}")
if 'invoke(null, "org.kivy.android.PythonActivity"' in first:
    sys.exit("FAIL: patched PythonActivity.java still has the swapped startApplication args")
preloads = first.count("System.loadLibrary(qtLib)")
if preloads != 1:
    sys.exit(f"FAIL: expected 1 Qt preload block, found {preloads}")
print("patch dry-run OK:")
for line in first.splitlines():
    if "__mainLib" in line or '"Qt6Core_arm64-v8a"' in line:
        print("   ", line.strip())
EOF

step "4/6 Staging app source into $STAGE"
# Android's icons come from a QML library generated from the desktop's
# icon definitions (dnd_app/ui_desktop/icon_data.py) -- regenerate it so
# the APK always matches.
(cd "$ROOT" && "$PY" -m dnd_app.ui_desktop.icon_data)
mkdir -p "$STAGE"
# The repo-root main.py wrapper, NOT dnd_app/ui_android/main.py: that
# file finds its QML relative to its own location (qml/ next to it), so
# copied to the staging root it looks for $STAGE/qml/App.qml, which
# doesn't exist -- engine.load() produces no root objects and the app
# exits on launch.
cp "$ROOT/main.py" "$STAGE/main.py"
# The Credits screen shows the project README; ui_android/bridge/credits.py
# looks for it at the app root, next to main.py.
cp "$ROOT/README.md" "$STAGE/README.md"
rsync -a --delete \
    --exclude='.buildozer' --exclude='bin' --exclude='build' --exclude='.gradle' \
    --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' \
    --exclude='buildozer.spec*' --exclude='*.sh' \
    "$ROOT/dnd_app/" "$STAGE/dnd_app/"
[ -f "$STAGE/dnd_app/ui_android/qml/App.qml" ] || die "App.qml missing from staging"
[ -f "$STAGE/README.md" ] || die "README.md missing from staging (Credits would show the fallback text)"
echo "$(find "$STAGE" -type f | wc -l) files staged"
STRAY="$(find "$STAGE" \( -name .buildozer -o -name bin -o -name build -o -name .gradle \
    -o -name __pycache__ -o -name '*.pyc' -o -name '*.whl' -o -name '*.apk' -o -name '*.aab' \) -print)"
[ -z "$STRAY" ] || die "stray build files in staging:"$'\n'"$STRAY"

step "5/6 buildozer android release (log: $LOG)"
cd "$UI"
"$PY" -m buildozer android release 2>&1 | tee "$LOG"
AAB="$(ls -t "$UI"/bin/*.aab 2>/dev/null | head -1 || true)"
[ -n "$AAB" ] || die "build finished but no .aab in $UI/bin -- see $LOG"
grep -q "p4a_hook: PythonActivity.java contains all expected patches" "$LOG" \
    || die "p4a_hook.py's PythonActivity.java check never ran -- see $LOG"
echo "AAB: $AAB"

step "6/6 Converting to universal APK"
APP_VERSION="$(sed -nE 's/^version[[:space:]]*=[[:space:]]*//p' "$SPEC" | head -1)"
# /tmp/bt is wiped whenever WSL restarts; keep a copy that survives.
BT_URL="https://github.com/google/bundletool/releases/download/1.18.3/bundletool-all-1.18.3.jar"
if [ ! -f "${BT_JAR:-/tmp/bt/bundletool.jar}" ]; then
    BT_JAR="$HOME/.cache/mimic/bundletool-all-1.18.3.jar"
    if [ ! -f "$BT_JAR" ]; then
        echo "downloading bundletool to $BT_JAR"
        mkdir -p "$(dirname "$BT_JAR")"
        curl -fL --retry 3 -o "$BT_JAR.part" "$BT_URL" && mv "$BT_JAR.part" "$BT_JAR" \
            || echo "WARNING: bundletool download failed"
    fi
fi
export BT_JAR="${BT_JAR:-/tmp/bt/bundletool.jar}"
# make-android-apk.sh signs with the debug keystore. Keep using the same
# one between builds: a phone refuses to update an app signed with a
# different key ("App not installed").
KS="$HOME/.android/debug.keystore"
if [ ! -f "$KS" ] && command -v keytool >/dev/null; then
    echo "creating debug keystore at $KS"
    mkdir -p "$HOME/.android"
    keytool -genkeypair -keystore "$KS" -storepass android -alias androiddebugkey \
        -keypass android -keyalg RSA -keysize 2048 -validity 10000 \
        -dname "CN=Android Debug,O=Android,C=US" >/dev/null
fi
if bash "$ROOT/deployment/make-android-apk.sh"; then
    APK="$(ls -t "$UI"/bin/*-universal.apk | head -1)"
    mkdir -p "$ROOT/dist"
    DEST="$ROOT/dist/MIMIC-${APP_VERSION:-unknown}-arm64-v8a-release.apk"
    cp "$APK" "$DEST"
    echo
    echo "=== BUILD COMPLETE ==="
    echo "APK: $DEST"
    echo "Copy it to the phone (e.g. Google Drive) and tap it to install."
else
    echo "Log: $LOG"
    die "built $AAB but couldn't convert it to an installable APK -- see the message above"
fi
echo "Log: $LOG"
