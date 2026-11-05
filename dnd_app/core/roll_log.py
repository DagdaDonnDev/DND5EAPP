"""Every roll the sheet makes, kept with the character -- for both apps'
Dice Roller history: checks, saves, initiative, concentration and attacks
(core/checks.py: logged when the d20 is rolled, brought up to date as
things are added to it, and its outcome once known), hit dice
(core/character.py roll_hit_die), what an action rolls (core/action_use.py
use_action: Second Wind, Healing Light, a Wild Magic surge...), Portent,
potions and spell scrolls, and the Dice Roller's own rolls.

    log_roll(char, kind, label, total, detail, nat, result) -> id
    update_roll(char, id, **fields)
    roll_history(char) -> [entry, ...], the newest first
    clear_roll_history(char)
    on_roll(callback) -> unsubscribe: callback(char, entry) on each new or
                         updated entry (an open Dice Roller keeps up)

An entry: {"id", "time" (ISO), "kind", "label", "total" (or None), "detail",
"nat" (20 or 1 on a natural d20, else 0), "result" ("hit", "missed",
"kept"... or "")}. It's saved with the character ("roll_history"), the
newest HISTORY_MAX of them.
"""
from datetime import datetime

HISTORY_MAX = 200

_listeners = []


def on_roll(callback):
    """callback(char, entry) whenever a roll is logged or brought up to
    date. Returns the function that stops it."""
    _listeners.append(callback)

    def stop():
        if callback in _listeners:
            _listeners.remove(callback)
    return stop


def _tell(char, entry):
    for cb in list(_listeners):
        try:
            cb(char, entry)
        except RuntimeError:           # a window that's gone (its Qt object deleted)
            if cb in _listeners:
                _listeners.remove(cb)


def log_roll(char: dict, kind: str, label: str, total=None, detail: str = "", nat: int = 0,
             result: str = "") -> int:
    """Keep a roll. Returns its id (for update_roll); 0 without a character."""
    if not isinstance(char, dict):
        return 0
    hist = char.setdefault("roll_history", [])
    rid = max((e.get("id", 0) for e in hist), default=0) + 1
    entry = {"id": rid, "time": datetime.now().isoformat(timespec="seconds"), "kind": kind,
             "label": label, "total": total, "detail": detail, "nat": nat, "result": result}
    hist.append(entry)
    del hist[:-HISTORY_MAX]
    _tell(char, entry)
    return rid


def update_roll(char: dict, rid: int, **fields) -> None:
    """Bring a kept roll up to date (a total after something was added to
    it, whether an attack hit)."""
    if not rid or not isinstance(char, dict):
        return
    for entry in reversed(char.get("roll_history", [])):
        if entry.get("id") == rid:
            changed = {k: v for k, v in fields.items() if entry.get(k) != v}
            if changed:
                entry.update(changed)
                _tell(char, entry)
            return


def roll_history(char: dict) -> list:
    """The kept rolls, the newest first."""
    return list(reversed(char.get("roll_history", []))) if isinstance(char, dict) else []


def clear_roll_history(char: dict) -> None:
    if isinstance(char, dict):
        char["roll_history"] = []
        _tell(char, None)


def when(entry: dict, now=None) -> str:
    """"12:04" today, "3 Nov 12:04" another day."""
    try:
        t = datetime.fromisoformat(entry.get("time", ""))
    except (TypeError, ValueError):
        return ""
    now = now or datetime.now()
    return t.strftime("%H:%M") if t.date() == now.date() else f"{t.day} {t.strftime('%b %H:%M')}"
