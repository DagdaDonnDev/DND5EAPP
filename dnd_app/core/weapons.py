"""Weapons in hand -- the rules both apps' Gear/Equipment screens use.
char["equipped_weapons"] names each weapon held, so three daggers with one
in hand list "Dagger" once, and the inventory says "1 of 3 equipped"."""
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
