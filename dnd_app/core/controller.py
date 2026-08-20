"""
CharacterController — single entry point for all character mutations.
UI reads from char; all writes go through controller.update() / apply().

Author: Ethan O'Brien
Date: 2026-08-20
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable

from .builder import rebuild
from .calculator import update_all
from .save_load import migrate_character, validate_character

log = logging.getLogger("dnd_app.controller")


class CharacterController:
    """Centralized character management with observer notifications."""

    def __init__(self, char: dict):
        self._char = char
        self._observers: list[Callable[[dict], None]] = []
        self._ui_ready = False

    @property
    def char(self) -> dict:
        return self._char

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        if callback not in self._observers:
            self._observers.append(callback)

    def unsubscribe(self, callback: Callable[[dict], None]) -> None:
        if callback in self._observers:
            self._observers.remove(callback)

    def mark_ui_ready(self) -> None:
        self._ui_ready = True

    def _notify(self) -> None:
        if not self._ui_ready:
            return
        for cb in list(self._observers):
            try:
                cb(self._char)
            except Exception:
                log.exception("Character observer %s failed", getattr(cb, "__name__", cb))

    def update(self, path: str, value: Any, *, rebuild_char: bool = True) -> None:
        """Update a nested path and refresh derived state."""
        self._set_nested(self._char, path, value)
        if rebuild_char:
            rebuild(self._char)
            update_all(self._char)
        self._notify()

    def update_many(self, updates: dict[str, Any], *, rebuild_char: bool = True) -> None:
        for path, value in updates.items():
            self._set_nested(self._char, path, value)
        if rebuild_char:
            rebuild(self._char)
            update_all(self._char)
        self._notify()

    def apply(self, mutator: Callable[[dict], None], *, rebuild_char: bool = False) -> None:
        """
        Run an in-place mutation on the character dict, then optionally
        rebuild derived state and notify observers.

        Prefer this (or update/update_many) over direct self.char[...] writes
        from UI code so refreshes stay consistent.
        """
        mutator(self._char)
        if rebuild_char:
            rebuild(self._char)
            update_all(self._char)
        self._notify()

    def get(self, path: str, default: Any = None) -> Any:
        return self._get_nested(self._char, path, default)

    def refresh(self) -> None:
        """Recompute grants and derived stats without changing values."""
        rebuild(self._char)
        update_all(self._char)
        self._notify()

    def save(self, filepath: str) -> tuple[bool, list[str]]:
        """Save character to JSON after validation."""
        ok, errors = validate_character(self._char)
        if not ok:
            return False, errors
        self._char["modified"] = datetime.now().isoformat()
        if not self._char.get("created"):
            self._char["created"] = self._char["modified"]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._char, f, indent=2, ensure_ascii=False)
        return True, []

    def load(self, filepath: str) -> tuple[bool, list[str]]:
        """Load character from JSON with migration."""
        with open(filepath, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        migrated = migrate_character(loaded)
        ok, errors = validate_character(migrated, strict=False)
        self._char.clear()
        self._char.update(migrated)
        rebuild(self._char)
        update_all(self._char)
        self._notify()
        return ok, errors

    @staticmethod
    def _set_nested(obj: dict, path: str, value: Any) -> None:
        parts = path.split(".")
        cur = obj
        for part in parts[:-1]:
            if part not in cur or not isinstance(cur[part], dict):
                cur[part] = {}
            cur = cur[part]
        cur[parts[-1]] = value

    @staticmethod
    def _get_nested(obj: dict, path: str, default: Any = None) -> Any:
        cur: Any = obj
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur
