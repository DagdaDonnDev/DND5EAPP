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
    carried(char) -> [{"name", "label", "qty", "ready"}]: for the Loadout
"""

THROWABLES = {
    "Acid (vial)": {"roll": "attack", "what": "2d6 acid", "range": "20 ft"},
    "Alchemist's Fire (flask)": {"roll": "attack", "what": "1d4 fire, then each turn until put out (DC 10 DEX)",
                                 "range": "20 ft"},
    "Holy Water (flask)": {"roll": "attack", "what": "2d6 radiant to a fiend or undead", "range": "20 ft"},
    "Oil (flask)": {"roll": "attack", "what": "Covered in oil: 5 fire if it's lit within a minute", "range": "20 ft"},
    "Bomb": {"roll": "save", "dc": 12, "what": "3d6 fire within 5 ft of where it lands", "range": "60 ft"},
    "Dynamite (stick)": {"roll": "save", "dc": 12, "what": "3d6 bludgeoning within 5 ft (half on a save)",
                         "range": "60 ft"},
    "Grenade, Fragmentation": {"roll": "save", "dc": 15, "what": "5d6 piercing within 20 ft (half on a save)",
                               "range": "60 ft"},
    "Grenade, Smoke": {"roll": "", "what": "A 20-ft cloud of smoke, heavily obscured, a round after it lands",
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
