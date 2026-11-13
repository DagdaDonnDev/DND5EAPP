"""How long an effect or a condition has left, in rounds, and what ends
concentration -- the same for both apps.

Rounds left
    char["durations"] = {"effect:Bless": 10, "condition:Poisoned": 3}
    (saved with the character). A spell that lasts a minute or less sets
    its own when it's cast (cast_rounds); anything else can be given a
    count by hand (set_rounds), a condition included. New Turn takes a
    round off each (tick) and ends what has run out: the effect comes off,
    and with it the concentration that held it; a condition is taken off.
    Longer spells (10 minutes, an hour) aren't counted in rounds: they end
    when you say so, as before.

What ends concentration
    You can't concentrate while incapacitated (and so not while paralyzed,
    petrified, stunned or unconscious -- asleep included), while raging, at
    0 hit points, or dead. concentration_block_reason says which applies;
    break_concentration ends the spell if one does, and returns what to
    tell the player. Both apps call it when a condition goes on; a Rage
    starting (core/calculator.py on_effect_started) and dropping to 0 hit
    points (core/dying.py) already end it themselves. The save for taking
    damage is core/checks.py's.
"""
import re

# The conditions you can't concentrate under: incapacitated, and the ones
# that make you so (PHB p.203, appendix A).
NO_CONCENTRATION = ("Incapacitated", "Paralyzed", "Petrified", "Stunned", "Unconscious")
_SAY = {"Incapacitated": "you're incapacitated", "Paralyzed": "you're paralyzed",
        "Petrified": "you're petrified", "Stunned": "you're stunned", "Unconscious": "you're unconscious"}


# A class's or race's own effect that lasts a minute: counted when it's
# switched on (core/calculator.py on_effect_started).
EFFECT_ROUNDS = {"Rage": 10, "Bladesong": 10, "Shifting": 10, "Vow of Enmity": 10,
                 "Sacred Weapon": 10, "Giant's Might": 10}


# ── What ends concentration ───────────────────────────────────────────────
def concentration_block_reason(char: dict) -> str:
    """Why this character can't concentrate right now ("" if they can)."""
    if char.get("is_dead"):
        return "you're dead"
    conditions = char.get("conditions", [])
    for cond in NO_CONCENTRATION:
        if cond in conditions:
            return _SAY[cond]
    if "Rage" in char.get("active_effects", []):
        return "you're raging"
    if char.get("max_hp", 0) > 0 and char.get("current_hp", 1) <= 0 and not char.get("_wildshape_active"):
        return "you're at 0 hit points"
    return ""


def break_concentration(char: dict) -> str:
    """If the character is concentrating and can't be, the spell ends.
    Returns what to tell the player ("" if nothing ended)."""
    spell = (char.get("concentration") or {}).get("spell")
    why = concentration_block_reason(char) if spell else ""
    if not why:
        return ""
    from dnd_app.core.magic_items import drop_concentration
    drop_concentration(char)
    forget_ended(char)
    return f"Concentration on {spell} ends: {why}"


# ── Rounds left ───────────────────────────────────────────────────────────
def _key(kind: str, name: str) -> str:
    return f"{kind}:{name}"


def _on(char: dict, kind: str, name: str) -> bool:
    """Is it still on? kind: "effect", "condition", or "concentration" (the
    spell being concentrated on, whether or not it has an effect of its own
    on the sheet -- Hold Person has none)."""
    if kind == "concentration":
        return (char.get("concentration") or {}).get("spell") == name
    return name in char.get("active_effects" if kind == "effect" else "conditions", [])


def forget_ended(char: dict) -> None:
    """Counts for effects and conditions that are no longer on go (so one
    put back on later starts uncounted). Both apps call it wherever an
    effect or a condition comes off."""
    kept = char.get("durations")
    if not kept:
        return
    for key in [k for k in kept if not _on(char, *k.split(":", 1))]:
        del kept[key]


def cast_rounds(spell: dict) -> int:
    """The rounds a spell lasts, when that's a minute or less: 10 for "1
    minute" (or "Concentration, up to 1 minute"), 1 for "1 round", N for "N
    rounds" -- else 0 (longer, instantaneous, or until dispelled)."""
    text = ((spell or {}).get("duration") or "").lower()
    m = re.search(r"(\d+)\s*round", text)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*min", text)
    if m and int(m.group(1)) == 1:
        return 10
    return 0


def set_rounds(char: dict, kind: str, name: str, rounds: int) -> None:
    """Give an effect ("effect"), a condition ("condition") or the spell
    being concentrated on ("concentration") this many rounds left; 0 takes
    the count off (it then lasts until ended)."""
    kept = char.setdefault("durations", {})
    if rounds and rounds > 0 and _on(char, kind, name):
        kept[_key(kind, name)] = int(rounds)
    else:
        kept.pop(_key(kind, name), None)


def rounds_left(char: dict, kind: str, name: str) -> int:
    """Rounds left on it (0: it isn't counted)."""
    if not _on(char, kind, name):
        return 0
    return int((char.get("durations") or {}).get(_key(kind, name), 0) or 0)


def condition_changed(char: dict, name: str) -> str:
    """A condition was just put on or taken off by hand: its old count
    goes, and one you can't concentrate under ends the spell. Returns what
    to tell the player ("" if nothing ended)."""
    set_rounds(char, "condition", name, 0)
    forget_ended(char)
    return break_concentration(char)


def rounds_text(rounds: int) -> str:
    """ "9 rounds left", "last round", or "" when it isn't counted."""
    if rounds <= 0:
        return ""
    return "last round" if rounds == 1 else f"{rounds} rounds left"


def tick(char: dict) -> list:
    """New Turn: a round comes off everything that's counted, and what has
    run out ends -- an effect comes off (and the concentration holding it
    with it), a condition is taken off. Returns what to tell the player,
    one line for each thing that ended."""
    forget_ended(char)
    kept = char.get("durations") or {}
    said = []
    # (the spell being concentrated on first: its effects go with it, and
    # are then said once)
    for key in sorted(kept, key=lambda k: not k.startswith("concentration:")):
        kind, name = key.split(":", 1)
        if key not in kept or not _on(char, kind, name):
            kept.pop(key, None)           # (ended by something else this turn)
            continue
        kept[key] -= 1
        if kept[key] > 0:
            continue
        del kept[key]
        if kind == "concentration":
            from dnd_app.core.magic_items import drop_concentration
            drop_concentration(char)
            said.append(f"Concentration on {name} ends: its time is up")
        elif kind == "effect":
            from dnd_app.core.action_use import end_effects
            from dnd_app.core.spell_effects import effect_names
            end_effects(char, [name])
            conc = (char.get("concentration") or {}).get("spell")
            if conc and (conc == name or name in effect_names(conc)):
                from dnd_app.core.magic_items import drop_concentration
                drop_concentration(char)
            said.append(f"{name} ends: its time is up")
        else:
            char["conditions"] = [c for c in char.get("conditions", []) if c != name]
            said.append(f"No longer {name.lower()}: its time is up")
    forget_ended(char)
    return said
