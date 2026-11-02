# Building MIMIC for Windows (and macOS/Linux)

This folder turns the app into one self-contained program — `dist\MIMIC.exe`
on Windows, `dist/MIMIC` on macOS/Linux — with PyInstaller.

| File | What it's for |
|---|---|
| `build_exe.bat` / `build_exe.sh` | **The build** (Windows / macOS-Linux) |
| `MIMIC.spec` | PyInstaller's config: what goes into the program, the icon, the splash, the version details |

## Quick start

On a new computer, double-click `packaging\setup_new_computer.bat` once
first: it installs Python if there isn't one (and everything the Android
build needs). Then run from the repo root:

```
packaging\windows\build_exe.bat
```

(The script `cd`s to the repo root itself, so running it from inside
`packaging\windows\` also works.) The script handles everything. The finished EXE
lands in `dist\MIMIC.exe`, at the repo root.

---

## What the build does

1. Installs PySide6 and PyInstaller via pip  
2. Runs PyInstaller with `MIMIC.spec`  
3. Produces a **single self-contained EXE** — no Python required on the target machine

First build: **2–5 minutes**. Subsequent builds: **~1 minute** — the default
`packaging\windows\build_exe.bat` / `./packaging/windows/build_exe.sh` no longer force
`--clean`, so PyInstaller reuses its incremental analysis cache (the
`build\` folder) instead of re-walking the entire PySide6 install
directory from scratch every time. Run `packaging\windows\build_exe.bat clean` /
`./packaging/windows/build_exe.sh clean` to force a full rebuild — do this after
editing the `.spec` file or upgrading PySide6/PyInstaller, since a stale
cache can otherwise miss those changes.

---

## Startup time

Onefile EXEs have an inherent cold-start cost: every launch, the bootloader
re-extracts the entire bundle (PySide6's Qt binaries alone are 100+ MB) to a
temp folder before your code can run at all — there's no way to skip that
step while keeping onefile packaging (switching to `--onedir` would remove
it entirely, at the cost of distributing a folder instead of one .exe —
a deliberate tradeoff, not changed here). Three things are in place to
make that wait less painful rather than eliminating it:

- **The payload itself is trimmed aggressively** — the `.spec` file's
  `_DEAD_WEIGHT_MARKERS` filter strips every PySide6 module this app
  doesn't use (WebEngine, QML/Quick, Qt3D, Charts/Graphs/DataVisualization,
  multimedia, SQL, printing, positioning/sensors, SVG, and more) from the
  raw file list `collect_all()` gathers, *before* it ever reaches the
  onefile bundle — smaller payload means less to extract on every launch.
  `QT_EXCLUDES` alone isn't enough for this: PyInstaller's Analysis step
  only consults it for Python-level import tracing, while `collect_all()`
  walks PySide6's install directory independently and grabs plugin/data
  files regardless, so both layers need to agree on what's actually dead
  weight or a module the exclude "removed" keeps sneaking back in as raw
  binaries.

- **A native bootloader-level splash** (`Splash()` in the spec, built from
  `dnd_app/ui_desktop/splash/splash.png`) shows up *during* that extraction step itself,
  before Python has even started — so the window isn't just a blank/frozen
  frame for several seconds. If you replace `splash.gif`, regenerate
  `splash.png` from its first frame so the two stay visually consistent
  (any image tool works, or `PIL.Image.open(...).convert("RGB").save(...)`).
- The app's own code was reordered so its in-process splash (the animated
  one) shows immediately after extraction finishes, *before* importing all
  the game data and UI modules — previously those heavy imports ran first,
  so the splash didn't appear until they were already done.

---

## Version details

Right-click `MIMIC.exe` → Properties → Details shows the product name,
version, publisher and copyright, set in the `.spec` file's version block:

- **The version** is the app's one version number, the `version = ...`
  line in `dnd_app/ui_android/buildozer.spec`, so the EXE and the APK
  always match. Bump it there before a release.
- **The publisher** (company and copyright name) is `_PUBLISHER` in the
  `.spec` file.

Only Windows builds get these; the same spec on Linux/macOS skips them.

---

## Why `strip=False`

`strip` removes Unix debug symbols. On Windows it does nothing useful and  
can cause errors with some PyInstaller versions, so it is disabled in the spec.

---

## Why certain stdlib modules are kept

`ast`, `dis`, and `tokenize` are listed in `hiddenimports` even though the  
app doesn't call them directly. PyInstaller's analysis phase uses them  
internally when scanning imports, and PySide6's shiboken layer pulls them  
in at runtime on some Python versions. Excluding them causes  
`ModuleNotFoundError` at startup.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'ast'` | Spec was wrong — current spec keeps `ast` |
| Antivirus flags the EXE | False positive from PyInstaller's bootloader — report it to Microsoft at https://www.microsoft.com/en-us/wdsi/filesubmission (choose "Software developer"); add an exclusion in AV meanwhile |
| EXE crashes with no message | Re-run with `console=True` in the spec to see the traceback |
| `icon.ico not found` | Ensure `dnd_app/ui_desktop/icon.ico` exists before building |
