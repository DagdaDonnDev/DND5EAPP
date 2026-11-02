#!/usr/bin/env bash
# First-time setup for the Android build, inside WSL: every step of
# packaging/android/README.md's "First-time setup", in one go.
# packaging\setup_new_computer.bat runs it; it also runs from a WSL terminal.
# Safe to run again: a step that's already done is skipped.
#
#   1. Linux packages: compilers, Java 17, unzip, rsync... (asks for the
#      Linux password)
#   2. Python 3.11.9 through pyenv, as the old build machine had it
#   3. buildozer and cython for that Python
#   4. the Android SDK: command-line tools, platform-tools, the platform
#      buildozer.spec targets, build-tools -- licences accepted
#   5. the Android NDK r28c
#   6. the debug key that signs the APK (the old computer's, if it's been
#      put next to this script)
#   7. setup_buildozer_spec.sh: the wheels, the p4a recipes, the Qt jars and
#      buildozer.spec's paths
#
# The SDK and NDK go where the old machine kept them
# (~/.pyside6_android_deploy/), which setup_buildozer_spec.sh looks in.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SPEC="$ROOT/dnd_app/ui_android/buildozer.spec"
BASE="$HOME/.pyside6_android_deploy"
SDK="$BASE/android-sdk"
NDK_VER="r28c"
NDK="$BASE/android-ndk/android-ndk-$NDK_VER"
# the command-line tools buildozer and PySide6's own installer use: they
# unpack to android-sdk/tools/, where buildozer looks for sdkmanager
CLT_URL="https://dl.google.com/android/repository/commandlinetools-linux-6514223_latest.zip"
NDK_URL="https://dl.google.com/android/repository/android-ndk-$NDK_VER-linux.zip"
BUILD_TOOLS="34.0.0"
PY_VER="3.11.9"
CACHE="$HOME/.cache/mimic"
API="$(sed -nE 's/^android\.api[[:space:]]*=[[:space:]]*([0-9]+).*/\1/p' "$SPEC" | head -1)"
API="${API:-33}"

step() { echo; echo "=== $* ==="; }
die()  { echo "ERROR: $*" >&2; exit 1; }
download() {  # download <url> <file> -- picks up a download that was cut off
    mkdir -p "$(dirname "$2")"
    [ -f "$2" ] && return
    curl -fL --retry 3 -C - -o "$2.part" "$1" || die "download failed: $1"
    mv "$2.part" "$2"
}
# Same lookup as clean_build_android.sh and setup_buildozer_spec.sh
find_python311() {
    local root="${PYENV_ROOT:-$HOME/.pyenv}" c
    for c in "$(command -v python3.11 2>/dev/null)" "$root"/versions/3.11*/bin/python3.11 \
             "$root/shims/python3.11" /usr/local/bin/python3.11 /usr/bin/python3.11; do
        [ -n "$c" ] && [ -x "$c" ] && "$c" -c 'import sys' >/dev/null 2>&1 \
            && { echo "$c"; return; }
    done
    return 1
}

echo "=== MIMIC: first-time setup for the Android build ==="
echo "Project: $ROOT"
[ -f "$SPEC" ] || die "buildozer.spec not found at $SPEC"
[ "$(uname -m)" = "x86_64" ] || die "the Android NDK runs on x86_64 Linux only; this is $(uname -m)"
command -v apt-get >/dev/null || die "this needs Ubuntu (or Debian) in WSL"
case "$ROOT" in
    *" "*) die "the project's folder has a space in its path ($ROOT); the Android build can't handle that -- move it (C:\\Dev\\DND5EAPP, say) and run this again" ;;
esac

step "1/7 Linux packages"
PKGS=(build-essential git zip unzip curl ca-certificates rsync openjdk-17-jdk-headless
      autoconf automake libtool libltdl-dev pkg-config cmake
      zlib1g-dev libncurses-dev libffi-dev libssl-dev libbz2-dev libreadline-dev
      libsqlite3-dev liblzma-dev xz-utils)
MISSING=()
for p in "${PKGS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [ ${#MISSING[@]} -eq 0 ]; then
    echo "  all there"
else
    echo "  installing: ${MISSING[*]}"
    echo "  (sudo asks for the Linux password you picked when Ubuntu first opened)"
    sudo apt-get update
    sudo apt-get install -y "${MISSING[@]}"
fi
java -version 2>&1 | grep -q 'version "17\.' \
    || echo "  WARNING: java isn't version 17 -- pick 17 with: sudo update-alternatives --config java"

step "2/7 Python $PY_VER (pyenv)"
if PY="$(find_python311)"; then
    echo "  have $PY"
else
    export PYENV_ROOT="$HOME/.pyenv"
    [ -d "$PYENV_ROOT" ] || git clone --depth 1 https://github.com/pyenv/pyenv.git "$PYENV_ROOT"
    echo "  building Python $PY_VER (a few minutes)"
    "$PYENV_ROOT/bin/pyenv" install -s "$PY_VER"
    "$PYENV_ROOT/bin/pyenv" global "$PY_VER"
    PY="$(find_python311)" || die "Python $PY_VER didn't install -- see the messages above"
    echo "  $PY"
fi
# new terminals, and the build's .bat (an interactive bash), find it too
if ! grep -q 'pyenv init' "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" <<'EOF'

# pyenv: the Python 3.11 MIMIC's Android build uses (packaging/android/first_time_setup.sh)
export PYENV_ROOT="$HOME/.pyenv"
[ -d "$PYENV_ROOT/bin" ] && export PATH="$PYENV_ROOT/bin:$PATH"
command -v pyenv >/dev/null && eval "$(pyenv init -)"
EOF
    echo "  added pyenv to ~/.bashrc"
fi

step "3/7 buildozer and cython"
BZ="$("$PY" -m buildozer --version 2>/dev/null | head -1 || true)"
if [ -n "$BZ" ]; then
    echo "  have $BZ"
else
    # into ~/.local; an Ubuntu Python that's "externally managed" needs the
    # flag that allows it (pyenv's doesn't)
    "$PY" -m pip install --user buildozer cython \
        || "$PY" -m pip install --user --break-system-packages buildozer cython \
        || die "couldn't install buildozer and cython for $PY"
    "$PY" -m buildozer --version | head -1
fi

step "4/7 Android SDK ($SDK)"
SM="$SDK/tools/bin/sdkmanager"
if [ ! -x "$SM" ]; then
    download "$CLT_URL" "$CACHE/$(basename "$CLT_URL")"
    mkdir -p "$SDK"
    unzip -q -o "$CACHE/$(basename "$CLT_URL")" -d "$SDK"
fi
[ -x "$SM" ] || die "no sdkmanager at $SM after unpacking the command-line tools"
# every licence accepted once, so neither this nor buildozer stops to ask
set +o pipefail
yes 2>/dev/null | "$SM" --sdk_root="$SDK" --licenses >/dev/null || die "sdkmanager couldn't accept the licences"
set -o pipefail
for PKG in "platform-tools" "platforms;android-$API" "build-tools;$BUILD_TOOLS"; do
    if [ -d "$SDK/${PKG//;//}" ]; then
        echo "  have $PKG"
    else
        echo "  installing $PKG"
        "$SM" --sdk_root="$SDK" "$PKG"
    fi
done

step "5/7 Android NDK $NDK_VER ($NDK)"
if [ -f "$NDK/source.properties" ]; then
    echo "  have it"
else
    echo "  downloading (about 700 MB)"
    download "$NDK_URL" "$CACHE/$(basename "$NDK_URL")"
    mkdir -p "$(dirname "$NDK")"
    unzip -q -o "$CACHE/$(basename "$NDK_URL")" -d "$(dirname "$NDK")"
    [ -f "$NDK/source.properties" ] || die "the NDK didn't unpack to $NDK"
    rm -f "$CACHE/$(basename "$NDK_URL")"
fi

step "6/7 The debug key that signs the APK"
KS="$HOME/.android/debug.keystore"
if [ -f "$KS" ]; then
    echo "  have $KS"
elif [ -f "$HERE/debug.keystore" ]; then
    mkdir -p "$HOME/.android"
    cp "$HERE/debug.keystore" "$KS"
    echo "  copied packaging/android/debug.keystore to $KS"
else
    echo "  none yet -- the first build makes a new one. A phone only updates MIMIC"
    echo "  from an APK signed with the same key as the one it has, so either:"
    echo "    - copy debug.keystore from the old computer into packaging\\android\\ and"
    echo "      run this again (on the old computer it's in WSL, ~/.android/debug.keystore;"
    echo "      from Windows: \\\\wsl\$\\Ubuntu\\home\\<your Linux name>\\.android\\), or"
    echo "    - uninstall MIMIC from the phone once before installing the new APK"
    echo "      (saved characters are in Documents\\MIMIC Characters and stay)."
fi

step "7/7 buildozer.spec: wheels, p4a recipes, Qt jars and paths"
bash "$HERE/setup_buildozer_spec.sh"

echo
echo "=== The Android build is set up ==="
echo "Make the APK: double-click packaging\\android\\clean_build_android.bat"
echo "(the first build takes 20-40 minutes; after that, a couple of minutes)"
