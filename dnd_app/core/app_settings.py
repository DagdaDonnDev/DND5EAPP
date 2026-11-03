"""
App-level settings persisted outside any character file.

The Start Menu (and an in-progress wizard, before a character exists
to attach a theme to) needs its own remembered theme, independent of
whatever theme a specific character happens to have saved -- opening
"Arcane Scroll" character shouldn't leave the app on Arcane Scroll
once you go back to the menu; it should return to whatever theme the
menu itself was last set to (e.g. "Blood Moon"), same as before that
character was ever opened.

Author: Ethan O'Brien
Date: 2026-09-10
"""

import json
import os
from .save_load import SAVE_DIR

APP_SETTINGS_PATH = os.path.join(SAVE_DIR, "app_settings.json")
DEFAULT_THEME = "(Dark) Obsidian"


def _load() -> dict:
    try:
        with open(APP_SETTINGS_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(APP_SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_app_theme() -> str:
    return _load().get("theme", DEFAULT_THEME)


def set_app_theme(name: str) -> None:
    data = _load()
    data["theme"] = name
    _save(data)


def get_custom_save_dir() -> str:
    """The character folder chosen in Settings ("" = the default)."""
    return _load().get("save_dir", "") or ""


def set_custom_save_dir(path: str) -> None:
    data = _load()
    if path:
        data["save_dir"] = path
    else:
        data.pop("save_dir", None)
    _save(data)


IMMERSIVE_MODES = ("Full", "Reduced", "Off")


def get_immersive(kind: str) -> str:
    """Immersive Health ("health") or Immersive Exhaustion ("exhaustion"):
    "Full" (the default), "Reduced" or "Off". See core/immersive.py."""
    value = _load().get(f"immersive_{kind}", "Full")
    return value if value in IMMERSIVE_MODES else "Full"


def set_immersive(kind: str, value: str) -> None:
    if value not in IMMERSIVE_MODES:
        return
    data = _load()
    data[f"immersive_{kind}"] = value
    _save(data)


def get_flag(key: str) -> bool:
    return bool(_load().get(key, False))


def set_flag(key: str, value: bool) -> None:
    data = _load()
    data[key] = bool(value)
    _save(data)
