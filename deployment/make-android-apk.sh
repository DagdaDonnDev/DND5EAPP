#!/usr/bin/env bash
# deployment/make-android-apk.sh
# Convert the newest .aab in dnd_app/ui_android/bin/ to a signed universal .apk.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$REPO/dnd_app/ui_android/bin"
BT_JAR="${BT_JAR:-/tmp/bt/bundletool.jar}"
KS="${HOME}/.android/debug.keystore"

if [ ! -f "$BT_JAR" ]; then
    echo "bundletool not found at $BT_JAR" >&2
    echo "Download: https://github.com/google/bundletool/releases/download/1.18.3/bundletool-all-1.18.3.jar" >&2
    exit 1
fi
if [ ! -f "$KS" ]; then
    echo "debug keystore not found at $KS" >&2
    exit 1
fi

AAB="$(ls -t "$BIN"/*.aab 2>/dev/null | head -1 || true)"
if [ -z "$AAB" ]; then
    echo "no .aab found in $BIN" >&2
    exit 1
fi
echo "AAB: $AAB"

BASE="$(basename "$AAB" .aab)"
OUT_APK="$BIN/${BASE}-universal.apk"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

java -jar "$BT_JAR" build-apks \
    --bundle="$AAB" \
    --output="$WORK/out.apks" \
    --mode=universal \
    --ks="$KS" \
    --ks-pass=pass:android \
    --ks-key-alias=androiddebugkey \
    --key-pass=pass:android

mv "$WORK/out.apks" "$WORK/out.zip"
unzip -o -q "$WORK/out.zip" -d "$WORK/extracted"
mv "$WORK/extracted/universal.apk" "$OUT_APK"

echo "APK: $OUT_APK"
ls -la "$OUT_APK"
