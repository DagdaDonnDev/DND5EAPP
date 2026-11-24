"""Windows: the shortcuts to MIMIC.exe take the theme's d20 too, as the
window does -- a taskbar pin, a Start pin, a desktop or Start menu shortcut.

People run the .exe as it is, so there's no installer whose shortcuts we
know. But every pin and shortcut is a .lnk file in a known folder, so on a
theme change MIMIC looks through those folders for the ones that point at
its own .exe and points their icon at the theme's (an .ico written to the
settings folder, one file per theme -- a new name, so Windows' icon cache
can't keep showing the old one), then tells Explorer to refresh.

The .exe file's own icon (in Explorer) is built into it and never changes.
Only the built .exe on Windows: running from source, or anywhere else,
this does nothing. It runs in the background, so a theme change never
waits on it, and anything that goes wrong is ignored (the shortcuts just
keep the icon they had)."""
import os
import subprocess
import sys
import threading

_SHORTCUT_FOLDERS = (
    r"[Environment]::GetFolderPath('Desktop')",
    r"[Environment]::GetFolderPath('CommonDesktopDirectory')",
    r"[Environment]::GetFolderPath('Programs')",
    r"(Join-Path $env:APPDATA 'Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar')",
    r"(Join-Path $env:APPDATA 'Microsoft\Internet Explorer\Quick Launch\User Pinned\StartMenu')",
)


def _active() -> bool:
    return sys.platform == "win32" and getattr(sys, "frozen", False)


def _ico_for(theme: str) -> str:
    """The theme's d20 as an .ico in the settings folder (written once)."""
    from dnd_app.core.app_icon import slug, DEFAULT, window_icon
    from dnd_app.core.save_load import SAVE_DIR
    folder = os.path.join(SAVE_DIR, "icons")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"mimic_{'default' if theme == DEFAULT else slug(theme)}.ico")
    if not os.path.exists(path):
        if not window_icon(theme).pixmap(256, 256).save(path, "ICO"):
            return ""
    return path


def _q(s: str) -> str:
    """A PowerShell single-quoted string."""
    return "'" + s.replace("'", "''") + "'"


def follow_theme(theme: str) -> None:
    """Point MIMIC's shortcuts at this theme's icon (in the background).
    Done once per theme change: the last theme done is remembered."""
    if not _active():
        return
    try:
        from dnd_app.core import app_settings as S
        data = S._load()
        if data.get("shortcut_icon_theme") == theme:
            return
        ico = _ico_for(theme)
        if not ico:
            return
        data["shortcut_icon_theme"] = theme
        S._save(data)
    except Exception:
        return
    exe = os.path.abspath(sys.executable)
    script = (
        f"$ico = {_q(ico)}; $exe = {_q(exe)}; $sh = New-Object -ComObject WScript.Shell; "
        f"foreach ($d in @({', '.join(_SHORTCUT_FOLDERS)})) {{ "
        "if ($d -and (Test-Path $d)) { "
        "Get-ChildItem -LiteralPath $d -Filter *.lnk -Recurse -ErrorAction SilentlyContinue | ForEach-Object { "
        "try { $l = $sh.CreateShortcut($_.FullName); "
        "if ($l.TargetPath -ieq $exe) { $l.IconLocation = \"$ico,0\"; $l.Save() } } catch {} } } }"
    )

    def run():
        try:
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                            "-Command", script], timeout=60, capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            import ctypes
            # SHCNE_ASSOCCHANGED: Explorer reloads its icons
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            pass
    threading.Thread(target=run, daemon=True).start()
