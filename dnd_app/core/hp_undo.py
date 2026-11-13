"""Undo for the last Damage or Heal: a mistyped number (50 for 5) no longer
costs you your hit points, your temp HP, a death save or -- at worst --
the character.

Both apps use it the same way:

    before = hp_state(char)
    ...the damage or the healing (core/dying.py)...
    remember_hp_change(char, before, "12 damage")

then show an Undo while hp_undo_label(char) says there's something to
undo, and call undo_hp_change(char) when it's pressed.

One step only: each Damage or Heal replaces the one before. What's kept is
only what that change itself altered, and the Undo is there only while
those are still as the change left them: once your hit points change some
other way (you type a new number, rest, drink a potion, start
concentrating on another spell) there's nothing to undo any more, rather
than an old state stamped over a newer one.

Kept under char["_hp_undo"]: a leading underscore, so it isn't written to
the save file. It's there for the session.
"""
import copy

# Everything a Damage or a Heal can alter (core/dying.py): the hit points,
# temp HP, death saves and death itself, Relentless Rage's count, a Wild
# Shape form's own pool, and -- dropped to 0 HP -- concentration, the
# effects that end with it and the rounds they had left.
_KEYS = ("current_hp", "temp_hp", "death_saves", "is_dead", "_relentless_rage_uses",
         "_wildshape_hp", "concentration", "active_effects", "effect_details", "durations")
_ABSENT = object()


def hp_state(char: dict) -> dict:
    """The hit-point side of the character as it is now, to hand to
    remember_hp_change() after a change."""
    return {k: copy.deepcopy(char[k]) for k in _KEYS if k in char}


def remember_hp_change(char: dict, before: dict, label: str) -> bool:
    """Keep what just changed (since `before`, an hp_state()) so it can be
    undone; `label` says what it was ("12 damage", "8 healing"). Returns
    False, keeping nothing, if nothing changed -- and the earlier change is
    then forgotten too: it's no longer the last thing that happened."""
    after = hp_state(char)
    changed = [k for k in _KEYS if before.get(k, _ABSENT) != after.get(k, _ABSENT)]
    if not changed:
        char.pop("_hp_undo", None)
        return False
    char["_hp_undo"] = {
        "label": label, "keys": changed,
        "before": {k: before[k] for k in changed if k in before},
        "after": {k: after[k] for k in changed if k in after},
    }
    return True


def _still_as_left(char: dict, kept: dict) -> bool:
    return all(char.get(k, _ABSENT) == kept["after"].get(k, _ABSENT) for k in kept["keys"])


def hp_undo_label(char: dict) -> str:
    """What an Undo would undo ("12 damage"), or "" if there's nothing --
    nothing was kept, or the hit points have changed some other way since."""
    kept = char.get("_hp_undo")
    return kept.get("label", "") if kept and _still_as_left(char, kept) else ""


def clear_hp_undo(char: dict) -> None:
    """Forget the last change (a rest, a revive, a change of form: after
    those, putting old hit points back would be wrong)."""
    char.pop("_hp_undo", None)


def undo_hp_change(char: dict) -> str:
    """Put back what the last Damage or Heal changed, and return what to
    tell the player ("" if there was nothing to undo: see hp_undo_label)."""
    kept = char.pop("_hp_undo", None)
    if not kept or not _still_as_left(char, kept):
        return ""
    for k in kept["keys"]:
        if k in kept["before"]:
            char[k] = copy.deepcopy(kept["before"][k])
        else:
            char.pop(k, None)
    return f"Undone: {kept['label']}"
