# installer/android

Android build scripts — same split as `installer/windows/` for the
desktop EXE. Double-click a `.bat` on Windows; it opens WSL and runs the
`.sh` of the same name next to it (you can also run the `.sh` directly
from a WSL terminal).

| Script | What it does |
|---|---|
| `clean_build_android.bat` | Clean `buildozer android release`: kills leftover build processes, clears old outputs and `/tmp/mimic-app-staging`, re-stages `main.py` + `dnd_app/`, builds, and writes `dist/MIMIC-<version>-arm64-v8a-release.apk` to copy to your phone |

First time only (or after moving the repo / reinstalling the SDK or
NDK), run `packaging\android\setup_buildozer_spec.bat` to write
`buildozer.spec`'s machine-specific paths.

See [`../../packaging/android/BUILD_APK.md`](../../packaging/android/BUILD_APK.md)
for the full build guide.
