"""Weapons -- rules both apps use: which weapons are in hand (char
["equipped_weapons"] names each one held, so three daggers with one in hand
list "Dagger" once, and the inventory says "1 of 3 equipped"), and monk
weapons with Martial Arts."""
from dnd_app.core.magic_items import parse_magic_suffix
from dnd_app.data.items import WEAPON_DICT


def _props(name: str) -> list:
    # a magic weapon ("Longsword +1") has its base weapon's properties
    base, _ = parse_magic_suffix(name)
    w = WEAPON_DICT.get(base) or {}
    return w.get("properties", []) if isinstance(w, dict) else []


def equip_weapon(char: dict, name: str) -> None:
    """Take `name` in hand, following the PHB's hands:
      1. a two-handed weapon needs both hands -- every other weapon (and a
         shield) is put away
      2. with a shield there's one hand free -- any weapon already in it is
         put away
      3. otherwise two weapons if this one is light (or with Dual Wielder),
         one if not -- the longest-held is put away to make room, and a
         two-handed weapon already held always is"""
    equipped = char.setdefault("equipped_weapons", [])
    others = [w for w in equipped if w != name]
    props = _props(name)
    if "Two-handed" in props:
        drop = others
        char["shield"] = False
    elif char.get("shield"):
        drop = others
    else:
        drop = [w for w in others if "Two-handed" in _props(w)]
        room = 2 if ("Light" in props or "Dual Wielder" in char.get("feats", [])) else 1
        keep = [w for w in others if w not in drop]
        drop += keep[:max(0, len(keep) - (room - 1))]
    for w in drop:
        if w in equipped:
            equipped.remove(w)
    if name not in equipped:
        equipped.append(name)


def unequip_weapon(char: dict, name: str) -> None:
    equipped = char.setdefault("equipped_weapons", [])
    if name in equipped:
        equipped.remove(name)


def equipped_note(char: dict, name: str, qty: int) -> str:
    """"1 of 3 equipped" for a stack with one in hand, else ""."""
    return f"1 of {qty} equipped" if qty > 1 and name in char.get("equipped_weapons", []) else ""


# ── Monk weapons (Martial Arts) ───────────────────────────────────────────
# A monk weapon is a shortsword or a simple melee weapon that isn't
# two-handed or heavy; a Way of the Kensei monk's kensei weapons and a
# Dedicated Weapon (Tasha's optional feature) count as monk weapons too --
# and either can be a gun.
# Martial Arts, for an attack with one -- while wearing no armour, holding
# no shield and wielding only monk weapons:
#   * DEX instead of STR for the attack and damage, if it's higher
#   * the Martial Arts die in place of the weapon's damage, if it's bigger
# A Kensei monk's kensei weapons also count as magical from 6th level.

def _weapon(name: str):
    """(base name, its WEAPON_DICT entry) -- "Silvered Longsword +1" is a Longsword."""
    from dnd_app.core.magic_items import parse_material_prefix
    base, _ = parse_magic_suffix(name or "")
    base, _ = parse_material_prefix(base)
    return base, (WEAPON_DICT.get(base) or {})


def weapon_base(name: str) -> str:
    """The plain weapon a name is: "Silvered Longsword +1" -> "Longsword"."""
    return _weapon(name)[0]


def inventory_notes(char: dict, name: str, qty: int) -> list:
    """What a weapon's inventory row says beside its name: how many are in
    hand, and whether it's the Dedicated Weapon."""
    notes = [equipped_note(char, name, qty)]
    if dedicated_weapon(char) and weapon_base(name) == dedicated_weapon(char):
        notes.append("dedicated weapon")
    return [n for n in notes if n]


def _lower_props(w: dict) -> list:
    return [str(p).lower() for p in w.get("properties", [])]


def _kensei_eligible(w: dict, base: str) -> bool:
    """Any simple or martial weapon lacking the heavy and special properties
    -- guns included, from the pistol to the antimatter rifle -- or a
    longbow (XGE). Dedicated Weapon uses the same test."""
    if base == "Longbow":
        return True
    props = _lower_props(w)
    cat = str(w.get("category", "")).lower()
    return (("simple" in cat or "martial" in cat)
            and not any(p == "heavy" or p.startswith("special") for p in props))


def kensei_weapon_options() -> list:
    """Every weapon that can be a kensei weapon, by name."""
    return [n for n, w in WEAPON_DICT.items() if n != "Unarmed Strike" and _kensei_eligible(w, n)]


def _monk_level(char: dict) -> int:
    from dnd_app.core.calculator import class_levels
    return class_levels(char).get("Monk", 0)


def kensei_weapons(char: dict) -> set:
    """The weapon types a Way of the Kensei monk has picked (3rd level on)."""
    from dnd_app.core.calculator import subclasses
    if _monk_level(char) < 3 or "kensei" not in subclasses(char).get("Monk", "").lower():
        return set()
    return set(char.get("_choices", {}).get("kensei_weapons", []) or [])


def dedicated_weapon_on(char: dict) -> bool:
    """Dedicated Weapon (Monk 2nd level, Tasha's optional feature) is in use."""
    if _monk_level(char) < 2:
        return False
    if char.get("_choices", {}).get("optional_features", {}).get("Dedicated Weapon"):
        return True
    return bool(char.get("optional_rules", {}).get("dedicated_weapon"))


def dedicated_weapon(char: dict) -> str:
    """The base name of the weapon picked with Dedicated Weapon, or ""."""
    if not dedicated_weapon_on(char):
        return ""
    return _weapon(char.get("dedicated_weapon", ""))[0] if char.get("dedicated_weapon") else ""


def _is_base_monk_weapon(base: str, w: dict) -> bool:
    if base == "Shortsword":
        return True
    props = _lower_props(w)
    return w.get("category") == "Simple Melee" and "two-handed" not in props and "heavy" not in props


def is_monk_weapon(char: dict, name: str) -> bool:
    if _monk_level(char) < 1:
        return False
    base, w = _weapon(name)
    if not w:
        return False
    return (_is_base_monk_weapon(base, w) or base in kensei_weapons(char)
            or (base and base == dedicated_weapon(char)))


def can_dedicate(char: dict, name: str) -> bool:
    """Whether Dedicated Weapon could be used on this weapon: a simple or
    martial weapon without the heavy or special property, that the monk is
    proficient with and isn't already a monk weapon for them."""
    if not dedicated_weapon_on(char):
        return False
    base, w = _weapon(name)
    if not w or base == "Longbow" or not _kensei_eligible(w, base):
        return False
    from dnd_app.core.calculator import has_weapon_proficiency
    if not has_weapon_proficiency(char, base, w.get("category", "")):
        return False
    return not (_is_base_monk_weapon(base, w) or base in kensei_weapons(char))


def _average(dice: str) -> float:
    import re
    m = re.match(r"\s*(\d*)d(\d+)", dice or "")
    if not m:
        try:
            return float(dice)
        except (TypeError, ValueError):
            return 0.0
    return int(m.group(1) or 1) * (int(m.group(2)) + 1) / 2


def martial_arts(char: dict, name: str):
    """What Martial Arts changes for an attack with `name`, or None if it
    doesn't apply: {"dex": True, "die": the damage die to use instead (or
    None), "magical": a kensei weapon at 6th level, "kensei": it's one}."""
    if not is_monk_weapon(char, name):
        return None
    armor = char.get("armor_worn") or "No Armor"
    if armor not in ("No Armor", "Mage Armor (spell)") or char.get("shield"):
        return None
    if any(not is_monk_weapon(char, other) for other in char.get("equipped_weapons", [])
           if other != name and _weapon(other)[1]):
        return None
    from dnd_app.core.calculator import get_martial_arts_die
    base, w = _weapon(name)
    die = get_martial_arts_die(char)
    kensei = base in kensei_weapons(char)
    return {"dex": True,
            "die": die if _average(die) > _average(w.get("damage", "")) else None,
            "magical": kensei and _monk_level(char) >= 6,
            "kensei": kensei}
