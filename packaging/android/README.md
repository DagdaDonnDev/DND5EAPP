# Building MIMIC for Android

This folder turns the app into `dist/MIMIC.apk`, a file you copy to your
phone and tap to install — the Android counterpart of
`packaging\windows\build_exe.bat` making `MIMIC.exe`. The build runs
**buildozer** (a wrapper around
[python-for-android](https://github.com/kivy/python-for-android), "p4a")
inside WSL on Windows. Android needs a fair amount of one-time setup first;
that's Google's build tools, not MIMIC-specific complexity.

These steps match what has worked on a real Windows + WSL machine for this
project. If one doesn't match what you see on yours, adjust as you go — it
doesn't mean you did something wrong.

## What's here

| File | What it's for |
|---|---|
| `clean_build_android.bat` / `.sh` | **The build.** Run it every time you want a new APK |
| `first_time_setup.sh` | Everything a new computer needs, inside WSL — `packaging\setup_new_computer.bat` runs it (see [First-time setup](#first-time-setup-do-this-once)) |
| `setup_buildozer_spec.bat` / `.sh` | Finds the Android SDK/NDK, the wheels and the Qt jars, makes the p4a recipes, and writes their paths into `buildozer.spec` (the first-time setup runs it) |
| `recipes/` | The PySide6/Shiboken6 recipes for p4a, rendered from PySide6's own templates; the setup copies them into `deployment/recipes/` |
| `make-android-apk.sh` | Turns the build's `.aab` into an installable APK (the clean build runs it) |
| `p4a_hook.py` | Build hook p4a runs to fix the Qt bootstrap — see [Why `p4a_hook.py` exists](#why-p4a_hookpy-exists) |
| `icon.png`, `icon_background.png`, `icon_foreground.png` | Launcher icons — see [Icon](#icon) |
| `wheels/` | Any Android PySide6/Shiboken6 wheels the setup had to download (not in git -- the repo's own copies are at the repo root) |

The build config itself is `dnd_app/ui_android/buildozer.spec`. It stays
next to the Android app because buildozer keeps its multi-GB build cache,
`.buildozer/`, beside it.

Each `.bat` opens WSL and runs the `.sh` of the same name in an interactive
bash (so `~/.bashrc`'s pyenv setup applies), and the window stays open at
the end. You can also run the `.sh` directly from a WSL terminal.

## First-time setup (do this once)

**Double-click `packaging\setup_new_computer.bat`.** It does everything
below, skipping anything already there, so it's safe to run again after a
failed step:

1. Python, for the Windows build (`packaging\windows\build_exe.bat`), if
   there isn't one
2. Ubuntu 24.04 in WSL, if there's no Linux there yet (and WSL itself, if
   it's off). Ubuntu opens once in the same window to make your Linux
   account: a user name, then a password twice; at the line ending in `$`,
   type `exit`. Only if Windows has to turn WSL on does it stop: restart,
   then double-click the setup again.
3. inside WSL, `first_time_setup.sh`:
   - the Linux packages: compilers, Java 17, unzip, rsync… (asks for the
     Linux password)
   - Python 3.11.9 through pyenv, and buildozer and cython for it
   - the Android SDK (the command-line tools buildozer expects,
     platform-tools, the platform `buildozer.spec` targets, build-tools)
     and the NDK r28c, in `~/.pyside6_android_deploy/`, licences accepted
   - the debug key that signs the APK — see [Signing](#signing)
   - `setup_buildozer_spec.sh`: the wheels, the p4a recipes, the Qt jars
     and `buildozer.spec`'s paths

The first time takes 20–40 minutes, mostly downloads (the NDK alone is
about 700 MB).

**Coming from another computer?** Before running it, copy two things across
if you still have them, so the new one carries on where the old one left
off:

- **the debug key**: on the old computer it's in WSL at
  `~/.android/debug.keystore` (from Windows,
  `\\wsl$\Ubuntu\home\<your Linux name>\.android\debug.keystore`).
  Put it in `packaging\android\` (git ignores it) and the setup moves it into
  place. Without it, the phone won't take the new APK as an update until
  MIMIC is uninstalled once — your saved characters are in Documents and
  stay.
- **`deployment\recipes\python3\`**, if the old computer has one (the
  hand-patched python3 recipe — see `.gitignore`). Without it p4a uses its
  own, which the pinned `v2024.01.21` builds cleanly.

### Doing it by hand

What the setup does, if you'd rather (or a step needs fixing):

1. **Install WSL** (Windows Subsystem for Linux), if you don't already
   have it: `wsl --install` from an admin Command Prompt, then restart.
2. **Install Python 3.11 inside WSL.** p4a is pinned to `v2024.01.21` in
   `buildozer.spec` (see [Why this p4a version](#why-this-p4a-version)),
   which targets Python 3.11:
   ```bash
   pyenv install 3.11.9 && pyenv global 3.11.9
   # or, where the distro has it: sudo apt install python3.11 python3.11-venv
   ```
3. **Install buildozer and cython for that Python**, inside WSL:
   ```bash
   python3.11 -m pip install --user buildozer cython
   ```
4. **Install a JDK (Java) 17** inside WSL: `sudo apt install openjdk-17-jdk-headless`
   (or [Eclipse Temurin 17](https://adoptium.net/)) — 17 is the
   Qt-recommended version.
5. **Get the Android SDK and NDK for Linux**, into
   `~/.pyside6_android_deploy/android-sdk` and
   `~/.pyside6_android_deploy/android-ndk/android-ndk-r28c` (where the setup
   script looks first): the command-line tools
   `commandlinetools-linux-6514223_latest.zip` unpacked into `android-sdk/`
   (buildozer looks for `android-sdk/tools/bin/sdkmanager`), then
   `sdkmanager --licenses` and `sdkmanager "platform-tools" "platforms;android-33" "build-tools;34.0.0"`;
   and `android-ndk-r28c-linux.zip` unpacked into `android-ndk/`. p4a
   `v2024.01.21` recommends NDK 25b; r28c has worked, with a warning.
6. **Run the setup script:**
   ```
   packaging\android\setup_buildozer_spec.bat
   ```
   It finds the SDK/NDK, uses the Android PySide6/Shiboken6 wheels at the
   repo root (or downloads them into `wheels/` if they're missing; they're cross-compiled for
   `android_aarch64` — not the desktop `pip install PySide6`), makes the p4a
   recipes in `deployment/recipes/` from `recipes/`, extracts the
   Qt Android jars from the wheel, and writes `buildozer.spec`'s
   machine-specific lines: `source.dir`, `android.sdk_path`,
   `android.ndk_path`, `p4a.local_recipes`, `p4a.hook`, `android.add_jars`
   and the icon paths. It's safe to re-run any time a path changes, and it
   backs the spec up first. It never touches `p4a.branch`.

You won't need to repeat any of it unless you move the repo or reinstall
the SDK/NDK. Keep the project in a folder with no spaces in its path
(`C:\Dev\DND5EAPP`, say): the build's arguments can't carry one.

## Every time you want a new build

Double-click **`clean_build_android.bat`**. It:

1. stops leftover buildozer/p4a/Gradle/aapt2 processes, clears the old
   outputs and `/tmp/mimic-app-staging`, and resets the generated
   `PythonActivity.java` so `p4a_hook.py` patches it from scratch
2. dry-runs the hook's Java patch, so a mistake fails in seconds rather
   than 20 minutes in
3. stages the repo-root `main.py`, `README.md` (the Credits screen shows it)
   and `dnd_app/` — without `ui_desktop/`, which the Android app doesn't
   use: it shares only `core/` and `data/` with the desktop app
4. runs `buildozer android release` (log in `/tmp/mimic-build-*.log`)
5. turns the AAB into **`dist/MIMIC.apk`**, replacing the last build, with
   bundletool (downloaded once to `~/.cache/mimic/`) and your debug key

It keeps the expensive compiled parts, so it is not a full rebuild.

**The first build is slow** — p4a downloads and compiles a whole Python
distribution (CPython, OpenSSL, sqlite, libffi, the Qt bootstrap); 20–40
minutes isn't unusual. After that, builds reuse the cache in
`dnd_app/ui_android/.buildozer/` and take a couple of minutes when only
`.py`/`.qml` files changed. Touching `p4a_hook.py` or a recipe makes the
next one slow again.

Then **copy `dist\MIMIC.apk` to your phone** (Google Drive, email, USB —
any way you'd move a file) and tap it to install. Your phone warns about
installing from an unknown source the first time; allow it for this file.
With `adb` and a connected phone, `adb install -r dist/MIMIC.apk` works too.

## How the build works

### The tool

There's no PyInstaller for Android, so Windows and Android use different
packaging tools, not just different config files. PySide6 does ship
`pyside6-android-deploy`, which wraps the same buildozer/p4a machinery, but
this project doesn't use it: on `/mnt/c/` paths it writes `buildozer.spec`,
fails to find the file it just wrote, and silently falls back to a stock
Kivy/SDL2 template — the APKs it made crashed on launch. The hand-written
`dnd_app/ui_android/buildozer.spec` is the one real config, used directly.

### `buildozer.spec` fields worth knowing

The setup script only changes the path lines. The rest, if you ever edit
the spec by hand:

- **`p4a.branch = v2024.01.21`** — load-bearing, see
  [Why this p4a version](#why-this-p4a-version). Never remove it.
- **`p4a.bootstrap = qt`** — the Qt bootstrap, not Kivy's default SDL2
  one. Missing this is exactly what broke the `pyside6-android-deploy`
  APKs.
- **`p4a.hook`** — points at `packaging/android/p4a_hook.py`. The clean
  build checks it does, and stops with a message if not (run the setup
  again).
- **`android.add_jars`** — the Qt Android jars (`Qt6Android.jar`,
  `Qt6AndroidBindings.jar`, `Qt6AndroidQuick.jar`), each listed once.
  Missing the first two fails the Java compile ("package ... does not
  exist"); missing `Qt6AndroidQuick.jar` fails only at runtime —
  `libQt6Quick`'s `JNI_OnLoad` registers natives against
  `org.qtproject.qt.android.QtQuickView`, which lives in that jar, so it
  returns `JNI_ERR` and QtLoader aborts. A duplicate entry breaks Gradle's
  classpath.
- **`android.apptheme`** — must NOT be quoted
  (`android.apptheme = @android:style/Theme.NoTitleBar`). Quotes produce
  invalid manifest XML and fail Gradle at `processDebugMainManifest`.
- **`source.include_patterns`** and **`p4a.extra_args`'s
  `--private=/tmp/mimic-app-staging`** — p4a packages the staging folder
  the clean build fills (step 3 above), rather than trusting buildozer's
  own file globbing to assemble the right tree.
- **`android.qt_libs` / `p4a.extra_args`** — which Qt modules get bundled
  (`Quick,Core,Qml,Gui,QuickControls2,OpenGL,Network`), plus
  `--load-local-libs=plugins_platforms_qtforandroid` (the Qt Android
  platform plugin) and `--icon=` (must match `android.icon`). They all
  need to agree.
- **`p4a.local_recipes`** — `deployment/recipes/` on your machine (not in
  git): the PySide6/Shiboken6 recipes that unpack the wheels instead of
  compiling them — the setup makes them from `packaging/android/recipes/`,
  which is in git — and, on the old build machine, a hand-patched
  `python3` recipe. That one isn't regenerable, so commit it (see the note
  in `.gitignore`). Each wheel recipe names its wheel by full path
  (`wheel_path`); if that file has gone, the clean build points the recipe
  at the same wheel in the repo root or `wheels/`.
- **`version`** — the app's one version number. The Windows EXE reads it
  from here too, so both always match.
- **Package name (`package.domain` + `package.name`)** — changing it
  makes Android treat it as a different app (no update path for existing
  installs).
- **`android.archs`** — `arm64-v8a` alone covers almost every real
  device. Each extra ABI roughly multiplies the bundled Qt/Python size.
- **`android.api` / `android.minapi`** — target whatever's current for
  Play Store submission when you build; that moves roughly yearly.

### Why this p4a version

`buildozer.spec` pins `p4a.branch = v2024.01.21`. p4a's `master` branch
(as of `2026.05.09`) targets Python 3.14, and its `python3` recipe still
carries patches written for 3.7–3.11 that fail to apply on 3.14 — the
build breaks before it compiles anything. `v2024.01.21` targets Python
3.11.5, where they apply cleanly. **Never remove or change
`p4a.branch`**: buildozer re-clones p4a from whatever branch the spec
names on every run, so without the pin it silently resets to `master`.

### Why `p4a_hook.py` exists

p4a runs this hook at two points in the build, and it fixes separate,
otherwise fatal problems with p4a `v2024.01.21`'s Qt bootstrap:

- **`before_apk_build`** copies `libc++_shared.so` from the NDK into the
  dist's `libs/arm64-v8a/` (and removes a stale copy under
  `src/main/jniLibs/arm64-v8a/`) — without it Qt refuses to load and the
  app crashes on launch even though the *build* succeeded, which is easy
  to misread as an app bug. It also flattens every native `.so` the
  PySide6/Shiboken6 bundle needs — `libQt6*.so`, Qt's plugins, every QML
  module's plugin, and the top-level `Qt*.abi3.so`/`Shiboken.abi3.so` —
  into `libs/arm64-v8a/`. That last part is counterintuitive: Qt 6.11's
  Android bootstrap calls `System.loadLibrary("QtQuick")` etc. during
  `onCreate`, so Android's loader has to find those `.abi3.so` files as
  native libraries, not just importable Python modules.
- **`before_apk_assemble`** patches the generated `PythonActivity.java`
  three ways: replaces `QtNative.setEnvironmentVariable(...)` with
  `android.system.Os.setenv(...)` (Qt 6.11 removed the former, but the
  template still calls it — the Java compile fails without this); strips a
  stale reflective `QtNative.startApplication(...)` call left by an
  earlier, wrong attempt at the same fix; and **prepends a
  `System.loadLibrary(...)` loop for the whole Qt Quick chain, in
  dependency order** (`Qt6Core` first, `Qt6Quick` last) to
  `PythonActivity.onCreate`. Without that, Android loads `libQt6Quick`
  first, `Qt6Core`'s `JNI_OnLoad` (which caches the `JavaVM*` that
  `QJniEnvironment::getJniEnv()` needs) hasn't run yet, and the app
  segfaults at `fault addr 0x0`. Loading everything up front, in order,
  means every `JNI_OnLoad` runs with the JVM already cached.
- It also installs the **adaptive icon** — see [Icon](#icon).

A dist regenerated from scratch also needs **`lib2to3/tests/*` in its
`blacklist.txt`** (it lives inside the generated dist, not this repo), or
`compileall` can die compiling the Python 2 test fixtures CPython ships.

Don't change or delete `p4a_hook.py` without testing a full rebuild
afterwards — each hook point runs late, so a mistake only shows up after
the slow path.

### Permissions

Saves go to the shared Documents/MIMIC Characters folder (or a folder
picked in Settings, inside Documents or Download), falling back to the
app's private folder if shared storage can't be written. Sharing a
character goes through the system pickers — **Import…** reads a file from
anywhere, **Save elsewhere…** writes one wherever you choose — which need
no storage permission.

### Icon

`icon.png` is the launcher icon for launchers before Android 8: the amber
d20 on the app's dark background, full-bleed so nothing is padded white.
Android 8+ uses an **adaptive icon** made of two 432 px layers:
`icon_background.png` (the dark backdrop) and `icon_foreground.png` (the
die, inside the 66 dp safe zone so every launcher mask shows all of it).
`p4a_hook.py` copies both into the build and writes
`res/mipmap-anydpi-v26/icon.xml` (p4a's own `--icon-fg/--icon-bg` would
target that folder too, but the Qt bootstrap doesn't have it). Without it,
Android shrinks `icon.png` and pads it with white.

## Good to know

- Don't run `buildozer android clean` or delete
  `dnd_app/ui_android/.buildozer/` — that cache is what keeps builds to a
  couple of minutes instead of 30–50.
- If a build is interrupted (Ctrl+C) while extracting or configuring a
  component, the next run can find it half-extracted and fail
  confusingly. Deleting just that component's folder under
  `dnd_app/ui_android/.buildozer/android/platform/build-*/build/other_builds/`
  is usually enough — no need to wipe the whole cache.
- Installing a new APK over the old one (or `adb install -r`) keeps the
  app's data; don't uninstall between builds unless the package name or
  signing key changed.

## Signing

The APK is signed with your PC's **debug key**
(`~/.android/debug.keystore`; the clean build creates it if it's
missing). Android only installs an update signed with the same key as the
installed app, so **back that file up** — a new PC with a new key means
uninstalling and reinstalling (your saves survive; they're in Documents).
On a new PC, put the old key in `packaging\android\debug.keystore` before
the first-time setup and it's moved into place (git never takes a
`.keystore`).

For a release (sharing the app widely, or the Play Store), make a proper
key once and keep it safe — treat it like a password, never commit it:

1. `keytool -genkey -v -keystore mimic-release.keystore -alias mimic -keyalg RSA -keysize 2048 -validity 10000`
2. Point the build at it (buildozer's keystore settings — check
   `buildozer android release --help` for your version), or sign the APK
   afterwards with `apksigner`.

Switching keys is easiest before 1.0: everyone on the old key reinstalls
once, and nobody has to again.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| The clean build stops with "buildozer.spec source.dir is ... but this script lives in ..." | The spec has another checkout's paths — run `setup_buildozer_spec.bat` |
| The clean build stops with "buildozer.spec p4a.hook is ..." | The spec still points at the hook's old place — run `setup_buildozer_spec.bat` once |
| `git clone -b 'master', ...` in the log even though the spec sets `p4a.branch` | The spec's `p4a.branch` line got removed, or the local p4a checkout's remembered branch drifted — check `dnd_app/ui_android/buildozer.spec` |
| A patch fails to apply deep inside the `python3` recipe | You're on p4a `master` (Python 3.14), not the pinned `v2024.01.21` — see [Why this p4a version](#why-this-p4a-version) |
| `sh.CommandNotFound: .../python3/config.guess` | A half-extracted Python source tree from an interrupted build — delete `other_builds/python3/` under `dnd_app/ui_android/.buildozer/.../build/` |
| "ANDROID_SDK_ROOT is not set" / NDK not found | Re-run `setup_buildozer_spec.bat` — it writes the paths into the spec rather than relying on environment variables |
| Build succeeds but the app crashes instantly on launch | `p4a_hook.py`'s `before_apk_build` step (bundling `libc++_shared.so`) didn't run |
| Java compile fails on `QtNative.setEnvironmentVariable` / "cannot find symbol" | `p4a_hook.py`'s `before_apk_assemble` patch didn't run |
| `SIGSEGV` at `fault addr 0x0` on `qtMainLoopThrea`; the tombstone shows `QJniEnvironment::getJniEnv()` → `libQt6Quick*.so`'s `JNI_OnLoad` | Another Qt library's `JNI_OnLoad` ran before `Qt6Core`'s — the load-order part of [Why `p4a_hook.py` exists](#why-p4a_hookpy-exists) |
| Gradle fails at `processDebugMainManifest` | `android.apptheme`'s value is quoted — it must not be |
| Java compile fails with "package org.qtproject.qt.android.bindings does not exist" | `android.add_jars` is missing, wrong, or lists a jar twice |
| `libQt6Quick_arm64-v8a.so` fails with `JNI_ERR returned from JNI_OnLoad` (runtime only) | `android.add_jars` is missing `Qt6AndroidQuick.jar` |
| `ModuleNotFoundError` for `dnd_app...` on the phone | The staging folder (`/tmp/mimic-app-staging`) is missing that module — check step 3 of the clean build's output |
| `compileall` fails under `lib2to3/tests/` | Add `lib2to3/tests/*` to the dist's `blacklist.txt` |
| Black screen, no crash; logcat shows `dlopen failed: library "org.kivy.android.PythonActivity" not found` | `QtNative.startApplication(params, mainLib)` got its arguments swapped, so Python never started. `p4a_hook.py` passes `("", <nativeLibraryDir>/libmain_arm64-v8a.so)`, migrates the old call in an already-patched dist, and fails the build if the old call survives |
| `:mergeReleaseResources` fails with `AAPT2 ... Daemon startup failed` | Environment, not code — usually transient on WSL from a `/mnt/c/` path. Retry; if it persists, run `./gradlew --stop` in the dist directory first |
