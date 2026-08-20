# Building MIMIC (D&D 5e Character Creator) EXE (Windows)

## Quick start

```
build_exe.bat
```

The script handles everything. The finished EXE lands in `dist\MIMIC.exe`.

---

## What the build does

1. Installs PySide6 and PyInstaller via pip  
2. Runs PyInstaller with the included spec file  
3. Produces a **single self-contained EXE** — no Python required on the target machine

First build: **2–5 minutes**. Subsequent builds (no `--clean`): ~1 minute.

---

## Startup time

Onefile EXEs have an inherent cold-start cost: every launch, the bootloader
re-extracts the entire bundle (PySide6's Qt binaries alone are 100+ MB) to a
temp folder before your code can run at all — there's no way to skip that
step while keeping onefile packaging. Two things are in place to make that
wait less painful rather than eliminating it:

- **A native bootloader-level splash** (`Splash()` in the spec, built from
  `dnd_app/assets/splash.png`) shows up *during* that extraction step itself,
  before Python has even started — so the window isn't just a blank/frozen
  frame for several seconds. If you replace `splash.gif`, regenerate
  `splash.png` from its first frame so the two stay visually consistent
  (any image tool works, or `PIL.Image.open(...).convert("RGB").save(...)`).
- The app's own code was reordered so its in-process splash (the animated
  one) shows immediately after extraction finishes, *before* importing all
  the game data and UI modules — previously those heavy imports ran first,
  so the splash didn't appear until they were already done.

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
| Antivirus flags the EXE | False positive from PyInstaller's bootloader — add an exclusion in AV |
| EXE crashes with no message | Re-run with `console=True` in the spec to see the traceback |
| `icon.ico not found` | Ensure `dnd_app/icon.ico` exists before building |
