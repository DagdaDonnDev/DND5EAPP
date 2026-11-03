"""What casting a spell does to your own sheet, past spending the slot --
the one set of rules both apps' cast buttons follow (desktop:
pages/sheet/spells.py _cast_spell, Android: bridge character_sheet.py
castSpell).

    cast_effect(char, spell_name, level, answers) -> result
        Puts the spell's effect on your Active Effects (Haste, Bless,
        Divine Favor, a smite...), asking first what only the player
        knows: who it's on, which weapon (Magic Weapon), which damage
        type (Elemental Weapon). What it adds to your weapon hits shows
        on the weapon rows (core/riders.py).

    weapon_cantrip(char, spell_name, rows, answers) -> result
        Green-Flame Blade and Booming Blade: which melee weapon you swing,
        then what to roll -- the weapon's damage plus the spell's, each
        with its damage type.

A result is {"ok", "toast", "ask", "refresh", "message"}, with the same
question protocol as core/action_use.py: when "ask" is set
({"key", "title", "options"}), show the options, put the answer in
answers[key] and call again. "message" is a longer text to show in a
dialog rather than a toast (the cantrip's damage).
"""
from dnd_app.core.effects import EFFECT_TABLE

# One spell, two effects: ask which
_ALIASES = {"Enlarge/Reduce": ("Enlarge", "Reduce")}


def _result(ok=True, toast="", ask=None, refresh=False, message=""):
    return {"ok": ok, "toast": toast, "ask": ask, "refresh": refresh, "message": message}


def _ask(key, title, options):
    return _result(False, ask={"key": key, "title": title, "options": list(options)})


def _lower_first(text):
    if len(text) > 1 and text[0].isupper() and text[1].islower():
        return text[0].lower() + text[1:]
    return text


def _held(char):
    """The weapons in hand, each once."""
    out = []
    for w in char.get("equipped_weapons", []):
        if w not in out:
            out.append(w)
    return out


def effect_names(spell_name: str) -> tuple:
    """The Active Effects casting this spell can put on you."""
    names = _ALIASES.get(spell_name, (spell_name,))
    return tuple(n for n in names if n in EFFECT_TABLE)


def cast_effect(char: dict, spell_name: str, level: int = 0, answers=None) -> dict:
    """Step by step:
      1. which effect (Enlarge or Reduce)
      2. who it's on -- unless it's only ever on you: a Self spell, or one
         whose effect rides on your own attacks (a smite, Hex)
      3. which weapon, for a spell on one weapon (Magic Weapon)
      4. which damage type, for one that lets you pick (Spirit Shroud)
      5. on it goes, with what it does in the toast"""
    from dnd_app.data.spells import get_spell
    from dnd_app.core.riders import EFFECT_RIDERS
    answers = dict(answers or {})
    names = effect_names(spell_name)
    if not names:
        return _result(True)              # nothing to track for this one
    # 1. which effect
    if len(names) > 1:
        if answers.get("which") not in names:
            return _ask("which", f"{spell_name}: which one?", names)
        name = answers["which"]
    else:
        name = names[0]
    info = EFFECT_TABLE[name]
    # 2. who it's on
    spell = get_spell(spell_name) or {}
    rng = (spell.get("range") or "").strip().lower()
    on_you = info.get("caster") or rng == "self" or rng.startswith("self")
    if not on_you:
        if "target" not in answers:
            return _ask("target", f"Who is {name} on?", ["Yourself", "Someone else"])
        if answers["target"] != "Yourself":
            return _result(True)          # on someone else's sheet, not this one
    details = {"level": int(level or spell.get("level", 0) or 0)}
    extra = (EFFECT_RIDERS.get(name) or (None,) * 6)[5] or {}
    # 3. which weapon
    if extra.get("one") or name in ("Magic Weapon",):
        held = _held(char)
        if not held:
            return _result(False, f"{name}: you have no weapon in hand to put it on")
        if len(held) > 1 and answers.get("weapon") not in held:
            return _ask("weapon", f"{name}: on which weapon?", held)
        details["weapon"] = answers.get("weapon") if answers.get("weapon") in held else held[0]
    # 4. which damage type
    if extra.get("pick"):
        options = [t.title() for t in extra["pick"]]
        if answers.get("type") not in options:
            return _ask("type", f"{name}: which damage type?", options)
        details["type"] = answers["type"].lower()
    # 5. on it goes
    char.setdefault("effect_details", {})[name] = details
    fx = char.setdefault("active_effects", [])
    if name not in fx:
        fx.append(name)
    # a smite and the like: what your next hit carries, at the level it
    # was cast ("an extra 2d6 fire" for Searing Smite at 2nd level)
    from dnd_app.core.riders import effect_note
    told = effect_note(char, name)
    if told:
        return _result(True, f"{name}: {_lower_first(told)}", refresh=True)
    note = _lower_first(info.get("note", "").rstrip("."))
    where = f" (your {details['weapon']})" if details.get("weapon") else ""
    kind = f", {details['type']}" if details.get("type") else ""
    return _result(True, f"{name} on{where}{kind}: {note}" if note else f"{name} added to Active Effects",
                   refresh=True)


# ── Green-Flame Blade and Booming Blade ───────────────────────────────────
WEAPON_CANTRIPS = ("Green-Flame Blade", "Booming Blade")


def _tier(char):
    """Cantrip damage steps up at character level 5, 11 and 17: 0-3."""
    from dnd_app.core.character import total_level
    lv = total_level(char)
    return (lv >= 5) + (lv >= 11) + (lv >= 17)


def _spell_mod(char):
    from dnd_app.core.calculator import _detect_spell_ability
    from dnd_app.core.character import ability_mod
    ab = _detect_spell_ability(char) or "INT"
    return ab, ability_mod(char, ab)


def weapon_cantrip(char: dict, spell_name: str, rows: list, answers=None) -> dict:
    """rows: the melee weapons as each app's weapon rows show them --
    [{"name", "atk": "+7", "damage": "1d8+4", "type": "slashing",
      "melee": True, "riders": "+1d4 radiant (Divine Favor)"}]."""
    answers = dict(answers or {})
    melee = [r for r in rows if r.get("melee")]
    if not melee:
        return _result(False, f"{spell_name} needs a melee weapon in hand")
    names = [r["name"] for r in melee]
    if len(melee) > 1 and answers.get("weapon") not in names:
        return _ask("weapon", f"{spell_name}: which weapon are you attacking with?", names)
    row = next((r for r in melee if r["name"] == answers.get("weapon")), melee[0])
    t = _tier(char)
    weapon = f"{row['damage']} {row['type']}".strip()
    if spell_name == "Green-Flame Blade":
        ab, mod = _spell_mod(char)
        on_hit = weapon + (f" + {t}d8 fire" if t else "")
        leap = f"{t}d8 + {mod} fire" if t else f"{mod} fire (your {ab} modifier)"
        tail = f"The flames leap to a second creature you can see within 5 ft of it: {leap}."
    else:
        on_hit = weapon + (f" + {t}d8 thunder" if t else "")
        tail = (f"If it willingly moves before the start of your next turn, "
                f"it takes {t + 1}d8 thunder.")
    lines = [f"Melee attack with your {row['name']}: {row['atk']} to hit.",
             f"On a hit: {on_hit}."]
    if row.get("riders"):
        lines.append(f"Also on the hit: {row['riders']}.")
    lines.append(tail)
    return _result(True, f"{spell_name} with your {row['name']}: {on_hit} on a hit",
                   message="\n".join(lines))
