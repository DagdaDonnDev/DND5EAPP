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
_ALIASES = {"Enlarge/Reduce": ("Enlarge", "Reduce"), "Shield": ("Shield (spell)",)}


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


def has_cast_step(spell_name: str) -> bool:
    """Does casting it ask or do something here (cast_effect)? An effect,
    False Life's temporary hit points, or a summoning."""
    from dnd_app.core.summons import is_summon_spell
    return bool(effect_names(spell_name)) or spell_name == "False Life" or is_summon_spell(spell_name)


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
    if spell_name == "False Life":
        return _false_life(char, level)
    from dnd_app.core.summons import is_summon_spell, cast_summon
    if is_summon_spell(spell_name):
        return cast_summon(char, spell_name, level, answers)     # Conjure Animals and the like
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
    # Polymorph, True Polymorph, Shapechange: into what (core/forms.py). On
    # you, your sheet becomes the form; on someone else it's in your
    # Effects tab, with the form, while you concentrate on it
    from dnd_app.core.forms import SPELL_FORMS
    form_spell = name in SPELL_FORMS
    if not on_you:
        if "target" not in answers:
            return _ask("target", f"Who is {name} on?", ["Yourself", "Someone else"])
        if answers["target"] != "Yourself" and not form_spell:
            return _result(True)          # on someone else's sheet, not this one
    mine = on_you or answers.get("target") == "Yourself"
    details = {"level": int(level or spell.get("level", 0) or 0)}
    if form_spell:
        from dnd_app.core import forms
        # on you, up to your own level; on someone else, theirs (the DM's call)
        opts = forms.options(char, name) if mine else forms.options(char, name, level=30)
        if answers.get("form") not in opts:
            return _ask("form", f"{name}: {'you become' if mine else 'they become'} which creature?", opts)
        details["form"] = answers["form"]
        if not mine:
            details["target"] = "someone else"
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
    if name == "Armor of Agathys":
        lvl = max(1, details["level"])
        char.setdefault("effect_details", {})[name] = details
        if name not in char.setdefault("active_effects", []):
            char["active_effects"].append(name)
        temp = 5 * lvl
        if temp >= char.get("temp_hp", 0):
            char["temp_hp"] = temp
            return _result(True, f"Armor of Agathys: {temp} temporary hit points. While you have them, "
                                 f"a creature that hits you with a melee attack takes {temp} cold damage", refresh=True)
        return _result(True, f"Armor of Agathys: you keep your {char['temp_hp']} temporary hit points "
                             f"(more than {temp}); a creature that hits you in melee takes {temp} cold damage "
                             f"while you have them", refresh=True)
    if name == "Aid":
        # your hit point maximum and your current hit points both rise:
        # 5, and 5 more for each slot level above 2nd. Cast again, the new
        # casting replaces the old one rather than adding to it.
        from dnd_app.core.calculator import aid_bonus
        before = aid_bonus(char)
        char.setdefault("effect_details", {})[name] = details
        if name not in char.setdefault("active_effects", []):
            char["active_effects"].append(name)
        gain = aid_bonus(char) - before
        if gain > 0 and not char.get("is_dead"):
            char["current_hp"] = char.get("current_hp", 0) + gain
            char["max_hp"] = char.get("max_hp", 0) + gain
    char.setdefault("effect_details", {})[name] = details
    # (cast afresh: it's no longer in the last turn of an earlier casting)
    if name in char.get("_last_turn_effects", []):
        char["_last_turn_effects"].remove(name)
    fx = char.setdefault("active_effects", [])
    if name not in fx:
        fx.append(name)
    # a spell of a minute or less is counted down by New Turn
    # (core/durations.py); the turn-long ones have their own ending
    from dnd_app.core.durations import cast_rounds, set_rounds
    from dnd_app.core.action_use import TURN_EFFECTS, NEXT_TURN_EFFECTS
    if name not in TURN_EFFECTS and name not in NEXT_TURN_EFFECTS:
        set_rounds(char, "effect", name, cast_rounds(spell))
    if form_spell:
        from dnd_app.core import forms
        if mine:
            ok, msg = forms.take_form(char, details["form"], name)
            return _result(ok, msg, refresh=True)
        return _result(True, f"{name} on someone else: they're a {details['form']} while you concentrate "
                             f"(it's in your Effects tab)", refresh=True)
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


def _false_life(char: dict, level: int) -> dict:
    """False Life: 1d4 + 4 temporary hit points, 5 more for each slot level
    above 1st. Temporary hit points don't add up: the higher stands."""
    import random
    lvl = max(1, int(level or 1))
    roll = random.randint(1, 4)
    temp = roll + 4 + 5 * (lvl - 1)
    if temp > char.get("temp_hp", 0):
        char["temp_hp"] = temp
        return _result(True, f"False Life: {temp} temporary hit points (rolled {roll} on the 1d4, "
                             f"+ {4 + 5 * (lvl - 1)})", refresh=True)
    return _result(True, f"False Life: you keep your {char.get('temp_hp', 0)} temporary hit points "
                         f"(more than {temp})", refresh=True)


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


# ── What the Effects tab says about an effect ─────────────────────────────
# A spell's effect does more from a higher slot: the tab says the level it
# was cast at, and the numbers at that level. These say it for the ones
# whose own note can't (the smites, Spirit Shroud and the like work it out
# in core/riders.py effect_note).
def _nth(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _lasts(lvl: int) -> str:
    return "24 hours" if lvl >= 5 else "8 hours" if lvl >= 3 else "1 hour"


_LEVEL_NOTES = {
    "Aid": lambda lvl, d: f"Your hit point maximum and current hit points are {5 * max(1, lvl - 1)} higher, "
                          f"for 8 hours.",
    "Magic Weapon": lambda lvl, d: (f"Your {d.get('weapon') or 'weapon'} is magical: "
                                    f"+{3 if lvl >= 6 else 2 if lvl >= 4 else 1} to attack and damage rolls, for 1 hour."),
    "Elemental Weapon": lambda lvl, d: (
        f"Your {d.get('weapon') or 'weapon'} is magical: +{3 if lvl >= 7 else 2 if lvl >= 5 else 1} to attack rolls and "
        f"an extra {3 if lvl >= 7 else 2 if lvl >= 5 else 1}d4 {d.get('type') or 'acid, cold, fire, lightning or thunder'} "
        f"damage, for 1 hour."),
    "Shadow Blade": lambda lvl, d: (
        f"A blade of shadow in your hand: {5 if lvl >= 7 else 4 if lvl >= 5 else 3 if lvl >= 3 else 2}d8 psychic, "
        f"finesse, light, thrown 20/60; advantage in dim light or darkness. 1 minute."),
    "Armor of Agathys": lambda lvl, d: (f"While you have its temporary hit points, a creature that hits you with a "
                                        f"melee attack takes {5 * max(1, lvl)} cold damage."),
    "Hex": lambda lvl, d: (f"Your attacks against the cursed creature deal an extra 1d6 necrotic damage, and it has "
                           f"disadvantage on checks with the ability you chose. Up to {_lasts(lvl)}."),
    "Hunter's Mark": lambda lvl, d: (f"Your weapon attacks against the marked creature deal an extra 1d6 damage, and "
                                     f"you have advantage on Perception and Survival checks to find it. "
                                     f"Up to {_lasts(lvl)}."),
    "Flame Arrows": lambda lvl, d: (f"{12 + 2 * max(0, lvl - 3)} pieces of ammunition from the quiver you touched deal "
                                    f"an extra 1d6 fire damage on a hit, for up to 1 hour."),
}

# Ones put on you by someone else whose numbers on your sheet change with
# the level it was cast at: adding one asks the level.
ASK_LEVEL_WHEN_ADDED = ("Aid", "Magic Weapon", "Elemental Weapon")


def effect_view(char: dict, name: str) -> dict:
    """An Effects tab row, the same on both apps:
        {"title": "Aid · 4th level", "level": 4, "note": "...at that level"}
    The level shows for a spell cast above its own level (or put on at a
    level asked for); the note is what the effect does at that level."""
    from dnd_app.core.riders import effect_note
    info = EFFECT_TABLE.get(name, {})
    d = (char.get("effect_details") or {}).get(name) or {}
    lvl = int(d.get("level") or 0)
    if name in _LEVEL_NOTES and lvl:
        note = _LEVEL_NOTES[name](lvl, d)
    else:
        note = effect_note(char, name) or info.get("note", "") or "Tracked, with no numbers of its own."
    base = 0
    for spell, names in list(_ALIASES.items()) + [(name, (name,))]:
        if name in names:
            from dnd_app.data.spells import get_spell
            base = int((get_spell(spell) or {}).get("level", 0) or 0)
            if base:
                break
    title = name.replace(" (spell)", "")
    if lvl and base and lvl > base:
        title += f" · {_nth(lvl)} level"
    if d.get("form"):                    # Polymorph and the like: into what, and on whom
        title += f" · {d['form']}" + (" (on someone else)" if d.get("target") else "")
    return {"title": title, "level": lvl, "note": note}


def added_effect_levels(name: str) -> list:
    """The levels to ask about when `name` is put on from the Effects list
    ([] when it doesn't matter): "2nd level" ... "9th level"."""
    if name not in ASK_LEVEL_WHEN_ADDED:
        return []
    from dnd_app.data.spells import get_spell
    base = int((get_spell(name) or {}).get("level", 1) or 1)
    return [f"{_nth(n)} level" for n in range(base, 10)]
