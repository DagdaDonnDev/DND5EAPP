"""Things you throw -- flasks and explosives -- for the Combat page's Ready
to throw list, the same on both apps.

A throwable you carry can be marked ready (char["ready_throw"]: names): on
a belt or a bandolier, to hand without taking up a hand's weapon. The
Combat page lists the ready ones you still have, each with its roll -- an
attack bonus for a flask (thrown as an improvised weapon: your DEX, plus
proficiency only with Tavern Brawler) or a save DC for an explosive -- and
what it does. Throwing one is an action.

    THROWABLES[name] -> {"roll": "attack" | "save" | "", "dc": int,
                         "what": short line, "range": "20 ft"}
    is_throwable(name), ready(char) -> [name], set_ready(char, name, on)
    rows(char) -> [{"name", "label", "qty", "roll", "what", "range"}]
    attack_row(char, name): a flask's throw for the attack popup
    save_report(char, name): an explosive's popup (its DC and damage)
    use_one(char, name) -> how many are left
    carried(char) -> [{"name", "label", "qty", "ready"}]: for the Loadout
"""

THROWABLES = {
    # a flask: a ranged attack with it as an improvised weapon
    "Acid (vial)": {"roll": "attack", "die": "2d6", "type": "acid", "what": "2d6 acid", "range": "20 ft"},
    "Alchemist's Fire (flask)": {"roll": "attack", "die": "1d4", "type": "fire",
                                 "note": "It keeps burning: 1d4 fire at the start of each of its turns, until it "
                                         "or someone next to it uses an action to put it out (DC 10 DEX check).",
                                 "what": "1d4 fire, then each turn until put out (DC 10 DEX)", "range": "20 ft"},
    "Holy Water (flask)": {"roll": "attack", "die": "2d6", "type": "radiant",
                           "note": "Only a fiend or an undead takes it.",
                           "what": "2d6 radiant to a fiend or undead", "range": "20 ft"},
    "Oil (flask)": {"roll": "attack", "die": "", "type": "",
                    "note": "Covered in oil: if it takes fire damage in the next minute, it takes 5 more fire.",
                    "what": "Covered in oil: 5 fire if it's lit within a minute", "range": "20 ft"},
    # an explosive: each creature near where it lands makes a DEX save
    "Bomb": {"roll": "save", "dc": 12, "die": "3d6", "type": "fire", "area": "within 5 ft of where it lands",
             "half": False, "what": "3d6 fire within 5 ft of where it lands", "range": "60 ft"},
    "Dynamite (stick)": {"roll": "save", "dc": 12, "die": "3d6", "type": "bludgeoning",
                         "area": "within 5 ft of where it lands", "half": True,
                         "what": "3d6 bludgeoning within 5 ft (half on a save)", "range": "60 ft"},
    "Grenade, Fragmentation": {"roll": "save", "dc": 15, "die": "5d6", "type": "piercing",
                               "area": "within 20 ft of where it lands", "half": True,
                               "what": "5d6 piercing within 20 ft (half on a save)", "range": "60 ft"},
    "Grenade, Smoke": {"roll": "", "die": "", "type": "",
                       "note": "A round after it lands, a 20-ft cloud of smoke: heavily obscured, for a minute "
                               "(a strong wind clears it).",
                       "what": "A 20-ft cloud of smoke, heavily obscured, a round after it lands",
                       "range": "60 ft"},
}

# the short names on the Combat page
_LABEL = {"Acid (vial)": "Acid", "Alchemist's Fire (flask)": "Alchemist's Fire", "Holy Water (flask)": "Holy Water",
          "Oil (flask)": "Oil", "Dynamite (stick)": "Dynamite", "Grenade, Fragmentation": "Fragmentation grenade",
          "Grenade, Smoke": "Smoke grenade"}


def _key(name: str) -> str:
    """The THROWABLES name for an item's name, whatever its case ("" if it
    isn't one)."""
    n = (name or "").strip().lower()
    return next((k for k in THROWABLES if k.lower() == n), "")


def is_throwable(name: str) -> bool:
    return bool(_key(name))


def ready(char: dict) -> list:
    return list(char.get("ready_throw") or [])


def set_ready(char: dict, name: str, on: bool) -> None:
    k = _key(name)
    if not k:
        return
    have = [n for n in ready(char) if n != k]
    char["ready_throw"] = have + ([k] if on else [])


def attack_bonus(char: dict) -> int:
    from dnd_app.core.character import ability_mod
    from dnd_app.core.calculator import get_prof_bonus
    bonus = ability_mod(char, "DEX")
    if "Tavern Brawler" in (char.get("feats") or []):      # proficient with improvised weapons
        bonus += get_prof_bonus(char)
    return bonus


def rows(char: dict) -> list:
    """The ready throwables you still have, in the order they were readied."""
    out = []
    atk = attack_bonus(char)
    for k in ready(char):
        qty = sum(e.get("qty", 1) for e in char.get("equipment", [])
                  if isinstance(e, dict) and _key(e.get("name", "")) == k)
        if qty <= 0:
            continue
        t = THROWABLES[k]
        roll = (f"{atk:+d}" if t["roll"] == "attack" else f"DC {t['dc']}" if t["roll"] == "save" else "")
        out.append({"name": k, "label": _LABEL.get(k, k), "qty": qty, "roll": roll,
                    "what": t["what"], "range": t["range"]})
    return out


def _qty(char: dict, k: str) -> int:
    return sum(e.get("qty", 1) for e in char.get("equipment", [])
               if isinstance(e, dict) and _key(e.get("name", "")) == k)


def carried(char: dict) -> list:
    """Every throwable you carry, ready or not (the Loadout's toggles)."""
    on = set(ready(char))
    out = []
    for k in THROWABLES:
        q = _qty(char, k)
        if q > 0:
            out.append({"name": k, "label": _LABEL.get(k, k), "qty": q, "ready": k in on})
    return out


def label(name: str) -> str:
    k = _key(name)
    return _LABEL.get(k, k)


def attack_row(char: dict, name: str) -> dict:
    """A flask's throw as an attack row for the attack popup (core/attacks.py,
    the same as a weapon's): a ranged attack with it as an improvised
    weapon -- your DEX, your proficiency only with Tavern Brawler -- and
    its damage as it is, no modifier. One of the Attack action's attacks."""
    from .attacks import _attack
    k = _key(name)
    t = THROWABLES[k]
    row = _attack(char, label(k), t["die"] or "0", t["type"], "DEX", badge="Thrown", kind="improvised",
                  melee=False, ranged=True, no_mod=True, thrown=True,
                  note=f"Thrown, range {t['range']}: an improvised weapon")
    row["atk"] = attack_bonus(char)
    row["hit_note"] = t.get("note", "")
    if not t["die"]:
        row["damage"] = ""
    row["cost"] = "Action"
    row["throwable"] = k
    return row


def save_report(char: dict, name: str) -> dict:
    """An explosive's popup, laid out as the attack popup is: its save DC
    where an attack's total would be, who makes the save, and the damage to
    roll -- with Throw it and Cancel."""
    k = _key(name)
    t = THROWABLES[k]
    lab = label(k)
    if t["roll"] == "save":
        roll = {"total": f"DC {t['dc']}", "line": "Dexterity saving throw",
                "note": f"Each creature {t['area']}", "verdict": "Half damage on a save" if t.get("half")
                else "No damage on a save"}
        hit = [{"dice": t["die"], "type": t["type"], "source": lab,
                "note": f"Range {t['range']}. Throwing it takes your action.", "apart": False}]
        title_hit = "EACH ONE THAT FAILS, ROLL"
    else:
        roll = {"total": "—", "line": f"Range {t['range']}", "note": "No roll", "verdict": ""}
        hit = [{"dice": "", "type": "", "source": t.get("note", t["what"]), "note": "Throwing it takes your action.",
                "apart": False}]
        title_hit = "WHAT IT DOES"
    text = f"{lab}: {roll['line']}, {roll['total']}. " + (f"{t['die']} {t['type']}. " if t["die"] else "") + \
        (t.get("note") or "")
    return {"title": lab, "kind": "throw", "total_label": "save DC" if t["roll"] == "save" else "",
            "roll": roll, "hit_title": title_hit, "hit": hit, "attacks": "", "options": [], "sections": [],
            "hit_button": "Throw it", "miss_button": "Cancel", "message": text.strip()}


def use_one(char: dict, name: str) -> int:
    """One used up (thrown); returns how many are left."""
    from dnd_app.core.inventory import remove_items
    k = _key(name)
    entry = next((e for e in char.get("equipment", [])
                  if isinstance(e, dict) and _key(e.get("name", "")) == k and e.get("qty", 1) > 0), None)
    if entry is None:
        return 0
    remove_items(char, entry, 1)
    return _qty(char, k)


def throw(char: dict, name: str) -> str:
    """Throw one: it's used up, and what happens is returned to show -- a
    flask's attack roll (the d20 rolled here) and its damage to roll on a
    hit, or an explosive's save and damage. "" if you have none left."""
    import random
    from dnd_app.core.inventory import remove_items
    k = _key(name)
    entry = next((e for e in char.get("equipment", [])
                  if isinstance(e, dict) and _key(e.get("name", "")) == k and e.get("qty", 1) > 0), None)
    if not k or entry is None:
        return ""
    remove_items(char, entry, 1)
    t = THROWABLES[k]
    label = _LABEL.get(k, k)
    left = sum(e.get("qty", 1) for e in char.get("equipment", [])
               if isinstance(e, dict) and _key(e.get("name", "")) == k)
    if t["roll"] == "attack":
        d20, atk = random.randint(1, 20), attack_bonus(char)
        head = f"{label}: {d20 + atk} to hit ({d20} {atk:+d})"
        if d20 == 20:
            head += " -- a critical hit"
        elif d20 == 1:
            head += " -- a miss"
        said = f"{head}. On a hit: {t['what']}."
    elif t["roll"] == "save":
        said = f"{label} thrown: DC {t['dc']} DEX save. {t['what'][0].upper() + t['what'][1:]}."
    else:
        said = f"{label} thrown. {t['what']}."
    return said + f" {left} left."
