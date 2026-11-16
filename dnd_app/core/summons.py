"""Creatures you summon from the Bestiary, the same on both apps: the
spells that conjure, call or raise them (Conjure Animals, Animate Dead,
Find Familiar...) and the magic items that do (Figurines of Wondrous
Power, the Bag of Tricks, the Horn of Valhalla, the elemental bowls and
braziers). Each creature summoned is its own entry in
char["owned_summons"] -- {"creature", "from", "conc"} beside the Tasha's
spirits' {"spell", "level", "form"} -- so each keeps its own hit points
on the Bestiary's Yours tab, and one held by concentration goes when the
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
}

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
    return name in SUMMON_SPELLS


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


def add_summons(char, creature, count, source, conc=False):
    """`count` of `creature` into char["owned_summons"]."""
    real = _real(creature)
    owned = char.setdefault("owned_summons", [])
    for _ in range(max(1, int(count))):
        owned.append({"creature": real, "from": source, "conc": bool(conc)})
    return real


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
    keep = [e for e in owned if not (e.get("creature") and e.get("conc") and e.get("from") != conc)]
    if len(keep) != len(owned):
        char["owned_summons"] = keep


def cast_summon(char, spell_name, level, answers) -> dict:
    """The summoning step of casting one of SUMMON_SPELLS (core/spell_effects
    cast_effect hands it here): how many of what CR, which creature, and
    they're on your Yours tab. Same question protocol as cast_effect."""
    from dnd_app.core.spell_effects import _ask, _result
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
    if spec.get("familiar"):
        dismiss(char, spell_name)            # one familiar at a time: the new one replaces it
    real = add_summons(char, creature, n, spell_name, conc)
    held = " while you concentrate" if conc else ""
    return _result(True, f"{spell_name}: {_plural(n, real) if n == 1 else f'{n} × {real}'} on your side{held}. "
                         f"They're in the Bestiary's Yours tab, each with its hit points", refresh=True)


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


def summon_statblock(entry: dict) -> dict | None:
    """An owned summon as the Yours tab's card shows it -- a Bestiary
    creature, or a Tasha's spirit (data/statblocks.py resolve_scaling_summon)."""
    if entry.get("creature"):
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        sb = WILDSHAPE_BEASTS.get(entry["creature"])
        if not sb:
            return None
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
    from dnd_app.data.statblocks import resolve_scaling_summon
    return resolve_scaling_summon(entry.get("spell"), entry.get("level"), entry.get("form"))


def _nth(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
