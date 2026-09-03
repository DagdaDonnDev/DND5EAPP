#!/usr/bin/env python3
"""MIMIC (D&D 5e Character Creator) — launcher."""
import sys
import os
import threading
import time

# ── Resolve base path (works from source AND inside a PyInstaller bundle) ─────
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS          # PyInstaller extraction directory
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

# ── Import guard — show a GUI dialog instead of crashing with no stdin ────────
def _show_import_error(exc, missing_name=""):
    if "PySide6" in missing_name:
        title = "Missing dependency: PySide6"
        msg = (
            "PySide6 is not installed (or not bundled in this EXE).\n\n"
            "If running from source:\n"
            "    pip install PySide6\n\n"
            "If you built an EXE with PyInstaller, rebuild with:\n"
            "    --collect-all PySide6\n\n"
            "See installer/BUILD_EXE.md for the full recommended build command."
        )
    else:
        title = "Import error"
        msg = f"Could not import a required module:\n\n{exc}\n\nCheck that all files are present."
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw()
        messagebox.showerror(title, msg)
        root.destroy()
    except Exception:
        sys.stderr.write(f"\n{title}\n{'─'*40}\n{msg}\n")
    sys.exit(1)

# ── Launch ─────────────────────────────────────────────────────────────────────
# Deliberately sequenced for fast perceived startup: create the QApplication
# and show the splash screen using ONLY the lightweight splash.py module
# (which imports nothing but PySide6 itself) BEFORE importing main_window,
# which transitively pulls in every game-data module (classes, races, feats,
# spells, magic items, subclass features, etc.) plus the full sheet/wizard
# UI code. That heavy import is what was actually taking the 5-12 seconds
# users were seeing as a frozen window before anything appeared on screen —
# moving it to AFTER the splash is already visible fixes that directly,
# rather than just making the heavy part itself faster.
if __name__ == "__main__":
    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError as exc:
        _show_import_error(exc, str(exc))
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("MIMIC")

    try:
        from dnd_app.ui.splash import AnimatedSplash
        splash = AnimatedSplash()
        splash.show()
        app.processEvents()
    except Exception:
        splash = None  # fall back to main()'s own splash creation if this fails

    # Close PyInstaller's own native bootloader splash (the one configured
    # via Splash() in the spec file, which shows a static image during
    # onefile self-extraction) now that our own animated one has taken
    # over. Without this call it never closes on its own — the docs are
    # explicit that it "remains open until this function is called or the
    # Python program is terminated" — so skipping it means BOTH splashes
    # stay visible at once: the native one frozen on its static image,
    # ours animating on top of/alongside it. pyi_splash only exists inside
    # a frozen build that actually has Splash() configured, and its own
    # module-level code can fail in more ways than a plain ImportError
    # (e.g. a KeyError if the bootloader didn't set up its IPC environment
    # variable — seen when the bootloader's splash failed to initialize),
    # so this is intentionally a broad catch-and-ignore: on any platform or
    # environment where the native splash isn't actually there, this is a
    # silent no-op rather than a crash.
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass

    # The import below is a single, synchronous, blocking Python statement —
    # while it runs, NOTHING pumps the Qt event loop, which means the splash
    # GIF's frame-advance timer never fires and it just sits on whatever
    # frame it was on, looking frozen/static for however long the import
    # takes (this is the actual heavy step: every game-data module plus the
    # full sheet/wizard UI code). Running it on a background thread instead,
    # while the main thread keeps calling processEvents(), lets the splash
    # keep animating the whole time.
    _import_result = {}
    def _do_heavy_import():
        try:
            from dnd_app.ui.pages.main_window import main as main_func
            _import_result["main"] = main_func
        except BaseException as exc:  # capture on the thread, re-raise on main
            _import_result["error"] = exc

    _thread = threading.Thread(target=_do_heavy_import, daemon=True)
    _thread.start()
    while _thread.is_alive():
        app.processEvents()
        time.sleep(0.01)
    _thread.join()

    if "error" in _import_result:
        exc = _import_result["error"]
        if isinstance(exc, ModuleNotFoundError):
            _show_import_error(exc, str(exc))
            sys.exit(1)
        raise exc

    main = _import_result["main"]
    main(app, splash)

