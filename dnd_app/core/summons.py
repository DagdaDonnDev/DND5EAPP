"""Creatures you summon from the Bestiary, the same on both apps: the
spells that conjure, call or raise them (Conjure Animals, Animate Dead,
Find Familiar...) and the magic items that do (Figurines of Wondrous
Power, the Bag of Tricks, the Horn of Valhalla, the elemental bowls and
braziers). Each creature summoned is its own entry in
char["owned_summons"] -- {"creature", "from", "conc"} beside the Tasha's
spirits' {"spell", "level", "form"} -- so each keeps its own hit points
on the Creatures page, and one held by concentration goes when the
concentration does (keep_in_step, from calculator.update_all).

The choice of creature is the player's (the DM's, by the rules, for the
Conjure spells); the dice a summoning rolls (the Horn's berserkers, the
Bag's tuft) are the player's too: the app asks what came.
"""
from __future__ import annotations

_FAMILIARS = ("Bat", "Cat", "Crab", "Frog", "Hawk", "Lizard", "Octopus", "Owl", "Poisonous Snake",
              "Quipper", "Rat", "Raven", "Sea Horse", "Spider", "Weasel")
_CHAIN = ("Imp", "Pseudodragon", "Quasit", "Sprite")


def _mult(level: int, base: int) -> int:
    """Conjure Animals and the like: twice as many from a slot 2 levels up,
    three times 4 up, four times 6 up."""
    return 1 + max(0, (level - base) // 2)


def _groups(level, base):
    m = _mult(level, base)
    return [(1 * m, 2), (2 * m, 1), (4 * m, 0.5), (8 * m, 0.25)]


def _cr_text(cr):
    return {0.25: "1/4", 0.5: "1/2", 0.125: "1/8"}.get(cr, str(int(cr)))


def _many(what, n):
    """"Mummy" -> "Mummies", "Ghoul" -> "Ghouls" (one stays one)."""
    if n == 1:
        return what
    return what[:-1] + "ies" if what.endswith("y") and what[-2:-1] not in "aeiou" else what + "s"


def _plural(n, what="creature"):
    return f"{n} {_many(what, n)}"


# spell: (its level, what it can bring, how many / of what CR, held by concentration)
#   kinds   creature types it picks from, or "names": exactly these
#   groups  level -> [(how many, CR at most)]: "8 of CR 1/4 or lower"...
SUMMON_SPELLS = {
    "Conjure Animals":          {"level": 3, "kinds": ("Beast",), "groups": lambda l: _groups(l, 3), "conc": True},
    "Conjure Woodland Beings":  {"level": 4, "kinds": ("Fey",), "groups": lambda l: _groups(l, 4), "conc": True},
    "Conjure Minor Elementals": {"level": 4, "kinds": ("Elemental",), "groups": lambda l: _groups(l, 4), "conc": True},
    "Conjure Elemental":        {"level": 5, "kinds": ("Elemental",), "groups": lambda l: [(1, l)], "conc": True},
    "Conjure Fey":              {"level": 6, "kinds": ("Fey", "Beast"), "groups": lambda l: [(1, l)], "conc": True},
    "Conjure Celestial":        {"level": 7, "kinds": ("Celestial",), "groups": lambda l: [(1, 5 if l >= 9 else 4)],
                                 "conc": True},
    "Summon Greater Demon":     {"level": 4, "kinds": ("Fiend",), "detail": "Demon",
                                 "groups": lambda l: [(1, 5 + (l - 4))], "conc": True},
    "Summon Lesser Demons":     {"level": 3, "kinds": ("Fiend",), "detail": "Demon",
                                 # twice as many from a 6th-level slot, three times from 8th
                                 "groups": lambda l: [(k * (3 if l >= 8 else 2 if l >= 6 else 1), cr)
                                                      for k, cr in ((2, 1), (4, 0.5), (8, 0.25))],
                                 "conc": True},
    "Infernal Calling":         {"level": 5, "kinds": ("Fiend",), "detail": "Devil",
                                 "groups": lambda l: [(1, 6 + (l - 5))], "conc": True},
    "Giant Insect":             {"level": 4, "names": {"Giant Centipede": 10, "Giant Spider": 3, "Giant Wasp": 5,
                                                       "Giant Scorpion": 1}, "conc": True},
    "Animate Dead":             {"level": 3, "names": ("Skeleton", "Zombie"),
                                 "count": lambda l: 1 + 2 * (l - 3), "conc": False},
    "Danse Macabre":            {"level": 5, "names": ("Skeleton", "Zombie"),
                                 "count": lambda l: 5 + 2 * (l - 5), "conc": True},
    "Create Undead":            {"level": 6, "conc": False,
                                 "by_level": lambda l: ([("Ghoul", 3 + (l - 6))] if l < 8 else
                                                        [("Ghoul", 5 if l == 8 else 6), ("Ghast", 2 if l == 8 else 3),
                                                         ("Wight", 2 if l == 8 else 3)]
                                                        + ([("Mummy", 2)] if l >= 9 else []))},
    "Find Familiar":            {"level": 1, "names": _FAMILIARS, "count": lambda l: 1, "conc": False,
                                 "familiar": True},
    # a steed: one at a time, whichever spell brought it, in your Mounts
    "Find Steed":               {"level": 2, "names": ("Warhorse", "Pony", "Camel", "Elk", "Mastiff"),
                                 "count": lambda l: 1, "conc": False, "steed": True},
    "Find Greater Steed":       {"level": 4, "names": ("Griffon", "Pegasus", "Peryton", "Dire Wolf", "Rhinoceros",
                                                       "Saber-Toothed Tiger"),
                                 "count": lambda l: 1, "conc": False, "steed": True},
}
_STEED_SPELLS = ("Find Steed", "Find Greater Steed")
SPIRIT_KINDS = ("Celestial", "Fey", "Fiend")


def _is_beast(name: str) -> bool:
    from dnd_app.data.bestiary import get_creature
    return ((get_creature(_real(name)) or {}).get("type") or "").lower() == "beast"


def _has_chain_pact(char: dict) -> bool:
    pact = (char.get("_choices") or {}).get("warlock_pact_boon") or [""]
    return "chain" in str(pact[0]).lower()


def caster_numbers(char: dict | None, spell_name: str):
    """(spell attack bonus, spell save DC) a spell of yours uses: the
    class that has it on its list (the best, if more than one does),
    else your best casting class. (None, None) without a caster."""
    if not char:
        return None, None
    from dnd_app.core.spellcasting import spellcasting_rows
    from dnd_app.data.spells import get_spell
    rows = [r for r in spellcasting_rows(char) if r["kind"] == "class" and r["attack"] is not None]
    if not rows:
        return None, None
    classes = set((get_spell(spell_name) or {}).get("classes", []))
    own = [r for r in rows if r["source"].split(" (")[0] in classes]
    best = max(own or rows, key=lambda r: r["attack"])
    return best["attack"], best["dc"]

# The groups the Creatures page shows its creatures in (both apps); one
# can be moved to another. Mounts you buy and vehicles keep their own.
GROUPS = ("Mounts", "Companions", "Familiars", "Summons", "Other")


def group_of(entry: dict) -> str:
    """Which group an owned creature is in: the one it was put in, or by
    what brought it -- a familiar, a steed, a summon, or Other for one
    added from the Bestiary."""
    if entry.get("group") in GROUPS:
        return entry["group"]
    src = entry.get("from") or entry.get("spell") or ""
    if SUMMON_SPELLS.get(src, {}).get("familiar"):
        return "Familiars"
    if src in _STEED_SPELLS:
        return "Mounts"
    if src == "From the Bestiary":
        return "Other"
    return "Summons"


def is_spirit_spell(name: str) -> bool:
    """The Tasha's summons (Summon Beast, Summon Fey...): a spirit whose
    numbers come from the spell's level, in the form you pick."""
    from dnd_app.data.statblocks import SCALING_SUMMONS
    return name in SCALING_SUMMONS

# item: what it brings -- [(creature, how many)], or a choice of them;
# "ask_count": the player rolls how many
ITEM_SUMMONS = {
    "Figurine of Wondrous Power, Bronze Griffon": [("Griffon", 1)],
    "Figurine of Wondrous Power, Ebony Fly": [("Giant Fly", 1)],
    "Figurine of Wondrous Power, Golden Lions": [("Lion", 2)],
    "Figurine of Wondrous Power, Marble Elephant": [("Elephant", 1)],
    "Figurine of Wondrous Power, Obsidian Steed": [("Nightmare", 1)],
    "Figurine of Wondrous Power, Onyx Dog": [("Mastiff", 1)],
    "Figurine of Wondrous Power, Serpentine Owl": [("Giant Owl", 1)],
    "Figurine of Wondrous Power, Silver Raven": [("Raven", 1)],
    "Prehistoric Figurine of Wondrous Power, Carnelian Triceratops": [("Triceratops", 1)],
    "Prehistoric Figurine of Wondrous Power, Jasper Tyrannosaurus Rex": [("Tyrannosaurus Rex", 1)],
    "Prehistoric Figurine of Wondrous Power, Kyanite Pteranodon": [("Pteranodon", 1)],
    "Prehistoric Figurine of Wondrous Power, Pyrite Plesiosaurus": [("Plesiosaurus", 1)],
    "Bowl of Commanding Water Elementals": [("Water Elemental", 1)],
    "Brazier of Commanding Fire Elementals": [("Fire Elemental", 1)],
    "Censer of Controlling Air Elementals": [("Air Elemental", 1)],
    "Stone of Controlling Earth Elementals": [("Earth Elemental", 1)],
    # the d8 a tuft from the bag rolls: which came
    "Bag of Tricks, Gray": {"pick": ("Weasel", "Giant Rat", "Badger", "Boar", "Panther", "Giant Badger",
                                     "Brown Bear", "Giant Elk")},
    "Bag of Tricks, Rust": {"pick": ("Rat", "Owl", "Mastiff", "Goat", "Giant Goat", "Giant Boar", "Lion",
                                     "Brown Bear")},
    "Bag of Tricks, Tan": {"pick": ("Jackal", "Ape", "Baboon", "Axe Beak", "Black Bear", "Giant Weasel",
                                    "Giant Hyena", "Tiger")},
    # the horn's berserkers: as many as the dice say
    "Horn of Valhalla, Silver": {"creature": "Berserker", "ask_count": (2, 8)},
    "Horn of Valhalla, Brass": {"creature": "Berserker", "ask_count": (3, 12)},
    "Horn of Valhalla (Bronze)": {"creature": "Berserker", "ask_count": (4, 16)},
    "Horn of Valhalla, Iron": {"creature": "Berserker", "ask_count": (5, 20)},
}


def is_summon_spell(name: str) -> bool:
    return name in SUMMON_SPELLS or is_spirit_spell(name)


def _creatures(kinds=(), detail="", max_cr=30.0):
    from dnd_app.data.bestiary import bestiary
    out = []
    for n, c in bestiary().items():
        if c.get("type") not in kinds or c.get("cr_value", 0) > max_cr:
            continue
        if detail and detail.lower() not in (c.get("type_detail") or "").lower():
            continue
        out.append(n)
    return sorted(out, key=lambda n: (-bestiary()[n].get("cr_value", 0), n))


def _real(name):
    """A creature's Bestiary name ("Skeleton" may be "Skeleton (version 1)")."""
    from dnd_app.data.statblocks import WILDSHAPE_BEASTS
    from dnd_app.data.bestiary import get_creature
    if get_creature(name):
        return name
    r = WILDSHAPE_BEASTS.resolve(name)
    if get_creature(r):
        return r
    from dnd_app.data.bestiary import bestiary
    return next((n for n in sorted(bestiary()) if n.startswith(f"{name} (")), name)


def add_summons(char, creature, count, source, conc=False, group=""):
    """`count` of `creature` into char["owned_summons"] (in `group` if
    given, else the one what brought it puts it in)."""
    real = _real(creature)
    owned = char.setdefault("owned_summons", [])
    for _ in range(max(1, int(count))):
        e = {"creature": real, "from": source, "conc": bool(conc)}
        if group in GROUPS:
            e["group"] = group
        owned.append(e)
    return real


def set_group(char, index: int, group: str) -> bool:
    """Move an owned creature to another group."""
    owned = char.get("owned_summons", [])
    if not (0 <= index < len(owned)) or group not in GROUPS:
        return False
    owned[index]["group"] = group
    return True


def dismiss(char, source: str) -> int:
    """Every creature `source` brought goes. Returns how many."""
    owned = char.get("owned_summons", [])
    keep = [e for e in owned if e.get("from") != source]
    gone = len(owned) - len(keep)
    char["owned_summons"] = keep
    return gone


def keep_in_step(char: dict) -> None:
    """A summon held by concentration goes when the concentration does."""
    conc = (char.get("concentration") or {}).get("spell")
    owned = char.get("owned_summons", [])
    keep = [e for e in owned if not (e.get("conc") and (e.get("from") or e.get("spell")) != conc)]
    if len(keep) != len(owned):
        char["owned_summons"] = keep


def cast_summon(char, spell_name, level, answers) -> dict:
    """The summoning step of casting one of SUMMON_SPELLS (core/spell_effects
    cast_effect hands it here): how many of what CR, which creature, and
    they're on your Creatures page. Same question protocol as cast_effect."""
    from dnd_app.core.spell_effects import _ask, _result
    if is_spirit_spell(spell_name):
        return _cast_spirit(char, spell_name, level, answers)
    spec = SUMMON_SPELLS[spell_name]
    lvl = max(spec["level"], int(level or spec["level"]))
    conc = spec.get("conc", False)
    if spec.get("by_level"):
        choices = {f"{n} {_many(c, n)}": (c, n) for c, n in spec["by_level"](lvl)}
        if answers.get("which") not in choices:
            return _ask("which", f"{spell_name} at {_nth(lvl)} level: raise which?", list(choices))
        creature, n = choices[answers["which"]]
    elif spec.get("names") is not None:
        names = spec["names"]
        if spec.get("familiar"):
            pact = (char.get("_choices") or {}).get("warlock_pact_boon") or [""]
            if "chain" in str(pact[0]).lower():
                names = tuple(names) + _CHAIN        # Pact of the Chain's special forms
        if answers.get("creature") not in names:
            return _ask("creature", f"{spell_name}: which creature?", list(names))
        creature = answers["creature"]
        n = names[creature] if isinstance(names, dict) else spec.get("count", lambda l: 1)(lvl)
    else:
        groups = spec["groups"](lvl)
        labels = {f"{_plural(k)} of CR {_cr_text(cr)} or lower": (k, cr) for k, cr in groups}
        if len(labels) > 1 and answers.get("group") not in labels:
            return _ask("group", f"{spell_name} at {_nth(lvl)} level: how many?", list(labels))
        n, cr = labels[answers["group"]] if len(labels) > 1 else next(iter(labels.values()))
        opts = _creatures(spec["kinds"], spec.get("detail", ""), cr)
        if not opts:
            return _result(False, f"{spell_name}: no creature in the Bestiary fits")
        if answers.get("creature") not in opts:
            return _ask("creature", f"{spell_name}: {_plural(n)} of which?", opts)
        creature = answers["creature"]
    # a familiar (of a beast) or a steed is a celestial, fey or fiend
    # instead, the caster's pick (Find Familiar; Find Steed and Find
    # Greater Steed, whatever its type)
    kind = ""
    if spec.get("steed") or (spec.get("familiar") and _is_beast(creature)):
        if answers.get("kind") not in SPIRIT_KINDS:
            return _ask("kind", f"{spell_name}: your {creature} is a celestial, a fey or a fiend?", list(SPIRIT_KINDS))
        kind = answers["kind"]
    if spec.get("familiar"):
        dismiss(char, spell_name)            # one familiar at a time: the new one replaces it
    if spec.get("steed"):
        for s_ in _STEED_SPELLS:             # one steed at a time, from either spell
            dismiss(char, s_)
    real = add_summons(char, creature, n, spell_name, conc)
    if kind:
        char["owned_summons"][-1]["kind"] = kind
    held = " while you concentrate" if conc else ""
    return _result(True, f"{spell_name}: {_plural(n, real) if n == 1 else f'{n} × {real}'} on your side{held}. "
                         f"They're on your Creatures page, each with its hit points", refresh=True)


def _cast_spirit(char, spell_name, level, answers):
    """Summon Beast, Summon Fey and the rest: which form; the spirit's
    numbers are the spell's at the level it's cast (data/statblocks.py
    resolve_scaling_summon). Held by concentration, as the spells are."""
    from dnd_app.core.spell_effects import _ask, _result
    from dnd_app.data.statblocks import SCALING_SUMMONS
    from dnd_app.data.spells import get_spell
    spec = SCALING_SUMMONS[spell_name]
    lvl = max(spec["base_level"], int(level or spec["base_level"]))
    forms = list(spec.get("forms", {}))
    if len(forms) > 1 and answers.get("form") not in forms:
        return _ask("form", f"{spell_name}: which form?", forms)
    form = answers.get("form") if len(forms) > 1 else forms[0]
    conc = bool((get_spell(spell_name) or {}).get("concentration", True))
    dismiss(char, spell_name)                # casting it again: the new spirit replaces the old
    char.setdefault("owned_summons", []).append(
        {"spell": spell_name, "level": lvl, "form": form, "from": spell_name, "conc": conc})
    held = " while you concentrate" if conc else ""
    article = "an" if form[:1].upper() in "AEIOU" else "a"
    return _result(True, f"{spell_name}: {article} {form} spirit on your side{held}. "
                         f"It's on your Creatures page with its hit points", refresh=True)


def item_summon_step(char, item, answers):
    """What a summoning item still needs to know before it's used: None
    (not a summoning item), {"ask": ...}, or {"creature", "count"}."""
    spec = ITEM_SUMMONS.get(item)
    if spec is None:
        return None
    if isinstance(spec, list):
        creature, n = spec[0]
        return {"creature": creature, "count": n}
    if spec.get("pick"):
        if answers.get("tuft") not in spec["pick"]:
            return {"ask": {"key": "tuft", "title": f"{item}: what did the tuft become? (roll a d8)",
                            "options": list(spec["pick"])}}
        return {"creature": answers["tuft"], "count": 1}
    lo, hi = spec["ask_count"]
    opts = [str(k) for k in range(lo, hi + 1)]
    if answers.get("count") not in opts:
        return {"ask": {"key": "count", "title": f"{item}: how many berserkers came? (roll the dice)",
                        "options": opts}}
    return {"creature": spec["creature"], "count": int(answers["count"])}


def summon_statblock(entry: dict, char: dict | None = None) -> dict | None:
    """An owned summon as the Creatures page's card shows it -- a Bestiary
    creature, or a Tasha's spirit (data/statblocks.py resolve_scaling_summon)
    with your spell attack bonus and save DC in it when `char` is given.
    A familiar or a steed is the type you picked, with its spell's rules;
    a steed of INT 5 or lower has INT 6 and understands a language of yours."""
    if entry.get("creature"):
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        sb = WILDSHAPE_BEASTS.get(entry["creature"])
        if not sb:
            return None
        out = _bestiary_card(entry, sb)
        src = entry.get("from", "")
        if entry.get("kind"):
            out["creature_type"] = entry["kind"].lower()
        if SUMMON_SPELLS.get(src, {}).get("familiar"):
            chain = char is not None and _has_chain_pact(char)
            out["traits"] = [("Familiar",
                              "It can't attack, but can take other actions. "
                              + ("When you take the Attack action, you can give up one of your attacks "
                                 "for it to make one attack with its reaction (Pact of the Chain). "
                                 if chain else "")
                              + "While it's within 100 feet you talk to it telepathically, and as an "
                              "action you see and hear through it until your next turn. It can deliver "
                              "a touch spell you cast.")] + list(out["traits"])
        elif src in _STEED_SPELLS:
            abil = dict(out["abilities"])
            if abil.get("INT", 10) <= 5:
                abil["INT"] = 6
            out["abilities"] = abil
            langs = out.get("languages") or "—"
            out["languages"] = ("understands one language you speak" if langs in ("—", "-", "")
                                else f"{langs}; understands one language you speak")
            out["traits"] = [("Steed",
                              "You talk to it telepathically within 1 mile. A spell you cast that targets "
                              "only you can target it too while it's within 5 feet of you.")] + list(out["traits"])
        return out
    from dnd_app.data.statblocks import resolve_scaling_summon
    atk, dc = caster_numbers(char, entry.get("spell"))
    return resolve_scaling_summon(entry.get("spell"), entry.get("level"), entry.get("form"),
                                  spell_attack_mod=atk, save_dc=dc)


def _bestiary_card(entry: dict, sb: dict) -> dict:
    """A Bestiary creature of yours, in the card's shape."""
    return {
        "display_name": entry["creature"], "source": entry.get("from", ""),
        "size": sb["size"], "creature_type": (sb.get("type") or "").lower(),
        "ac": str(sb["ac"]) + (f" ({sb['ac_note']})" if sb.get("ac_note") else ""),
        "hp": sb["hp"], "hit_dice": sb["hit_dice"], "speed": sb["speed"],
        "abilities": sb["abilities"], "saves": [], "skills": sb["skills"],
        "damage_resistances": sb.get("damage_resistances", ""),
        "damage_immunities": sb.get("damage_immunities", ""),
        "condition_immunities": sb.get("condition_immunities", ""),
        "senses": sb["senses"], "languages": sb.get("languages", "") or "—",
        "traits": sb["traits"], "actions": sb["actions"] + sb.get("bonus_actions", []),
        "reactions": sb.get("reactions", []),
    }


def _nth(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# ── A creature's maximum hit points: its stat block's, or the one you set
# (rolled from its hit dice, say) -- for any creature card with hit points
def max_hp_of(char: dict, hp_key: str, base) -> int:
    """`base` (the stat block's) unless one was set for this creature."""
    own = (char.get("summon_hp_max") or {}).get(hp_key)
    if isinstance(own, int) and own > 0:
        return own
    return base if isinstance(base, int) else (int(base) if str(base).isdigit() else 1)


def set_max_hp(char: dict, hp_key: str, value) -> None:
    """Set a creature's maximum (None or 0: back to its stat block's).
    Its current hit points stay as they are, but never above the new
    maximum."""
    maxes = char.setdefault("summon_hp_max", {})
    if not value:
        maxes.pop(hp_key, None)
        return
    maxes[hp_key] = int(value)
    cur = (char.get("summon_hp_tracking") or {}).get(hp_key)
    if isinstance(cur, int) and cur > int(value):
        char["summon_hp_tracking"][hp_key] = int(value)


def dice_average(dice: str) -> int:
    """'2d10 + 2' -> 13 (rounded down, as a stat block's are)."""
    from dnd_app.data.bestiary import dice_avg
    try:
        return dice_avg(str(dice or ""))
    except Exception:
        return 0
