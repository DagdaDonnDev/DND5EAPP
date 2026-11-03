"""Ammunition -- the shots a ranged weapon has left, counted straight from
the inventory, so a weapon's counter and the Gear tab always agree (both
apps use this).

How the inventory holds it:
  * bundles -- "Ammunition, Arrows (20)", "Crossbow Bolts (20)": the number
    in brackets is how many pieces one holds
  * loose pieces -- "Arrows", "Sling Bullets": one piece each

Firing one shot:
  1. use a loose piece if there is one
  2. otherwise open a bundle: one fewer bundle, and the rest of it goes in
     as loose pieces (19 Arrows), each weighing its share of the bundle
Setting the count (the counter's "how many do you have?"):
  * more -- the extra go in as loose pieces
  * fewer -- they're used up the way shots are, loose pieces first
"""
import re

# The ammunition each ranged weapon fires (thrown weapons fire themselves)
WEAPON_AMMO = {
    "Shortbow": "arrows", "Longbow": "arrows",
    "Light Crossbow": "bolts", "Hand Crossbow": "bolts", "Heavy Crossbow": "bolts",
    "Sling": "sling_bullets", "Blowgun": "needles",
    "Pistol": "firearm_bullets", "Musket": "firearm_bullets", "Revolver": "firearm_bullets",
    "Hunting Rifle": "firearm_bullets", "Automatic Rifle": "firearm_bullets",
    "Laser Pistol": "energy_cells", "Laser Rifle": "energy_cells",
    "Antimatter Rifle": "energy_cells",
}

# kind -> (what the counter calls it, the loose piece's inventory name,
#          the catalog bundle it's priced from, every inventory name it goes by)
AMMO_KINDS = {
    "arrows": ("Arrows", "Arrows", "Ammunition, Arrows (20)",
               {"ammunition, arrows (20)", "arrows (20)", "arrows", "arrow"}),
    "bolts": ("Bolts", "Bolts", "Ammunition, Bolts (20)",
              {"ammunition, bolts (20)", "crossbow bolts (20)", "bolts (20)",
               "crossbow bolts", "crossbow bolt", "bolts", "bolt"}),
    "sling_bullets": ("Sling Bullets", "Sling Bullets", "Ammunition, Bullets (20)",
                      {"ammunition, bullets (20)", "sling bullets (20)",
                       "sling bullets", "sling bullet"}),
    "needles": ("Needles", "Needles", "Ammunition, Needles (50)",
                {"ammunition, needles (50)", "blowgun needles (50)", "needles (50)",
                 "blowgun needles", "needles", "needle"}),
    "firearm_bullets": ("Bullets", "Bullets", "Bullets (10)",
                        {"bullets (10)", "firearm bullets (10)", "bullets (modern)",
                         "firearm bullets", "bullets", "bullet"}),
    "energy_cells": ("Energy Cells", "Energy Cell", "Energy Cell",
                     {"energy cell", "energy cells"}),
}


def ammo_kind(base_weapon: str, ranged: bool, thrown: bool) -> str:
    """The kind of ammunition a weapon fires ("" for none)."""
    return WEAPON_AMMO.get(base_weapon, "") if ranged and not thrown else ""


def ammo_label(kind: str) -> str:
    """"Arrows", "Sling Bullets"... -- what the counter shows."""
    return AMMO_KINDS.get(kind, ("Ammo",))[0]


def _pieces_per(name: str) -> int:
    """How many pieces one inventory item holds: "Arrows (20)" -> 20."""
    m = re.search(r"\((\d+)\)", name)
    return int(m.group(1)) if m else 1


def _entries(char: dict, kind: str) -> list:
    """[(inventory entry, pieces per item)] holding this kind -- loose
    pieces first, so they're used before a bundle is opened."""
    names = AMMO_KINDS.get(kind, ("", "", "", set()))[3]
    found = [(eq, _pieces_per(eq.get("name", "")))
             for eq in char.get("equipment", [])
             if isinstance(eq, dict) and eq.get("name", "").strip().lower() in names]
    return sorted(found, key=lambda e: e[1])


def ammo_count(char: dict, kind: str) -> int:
    """Shots left: every bundle's pieces plus the loose ones."""
    return sum(max(0, int(eq.get("qty", 1) or 0)) * per for eq, per in _entries(char, kind))


def _catalog_piece(kind: str) -> tuple:
    """(weight, cost) of one piece, from the catalog bundle's price."""
    from dnd_app.data.items import ADVENTURING_GEAR
    bundle = AMMO_KINDS[kind][2]
    for name, weight, cost, *_ in ADVENTURING_GEAR:
        if name == bundle:
            per = _pieces_per(name)
            return float(weight or 0) / per, float(cost or 0) / per
    return 0.0, 0.0


def _add_loose(char: dict, kind: str, n: int, weight: float, cost: float) -> None:
    """Put n loose pieces in the inventory (onto the existing loose entry)."""
    if n <= 0:
        return
    loose_name = AMMO_KINDS[kind][1]
    for eq, per in _entries(char, kind):
        if per == 1:
            eq["qty"] = int(eq.get("qty", 0) or 0) + n
            return
    char.setdefault("equipment", []).append(
        {"name": loose_name, "qty": n, "weight": round(weight, 4),
         "cost": round(cost, 4), "notes": ""})


def spend_ammo(char: dict, kind: str) -> bool:
    """Fire one shot. False (and nothing changes) when there's none left."""
    for eq, per in _entries(char, kind):
        qty = int(eq.get("qty", 0) or 0)
        if qty <= 0:
            continue
        # 1. a loose piece, or 2. open one bundle into loose pieces
        eq["qty"] = qty - 1
        if per > 1:
            cat_w, cat_c = _catalog_piece(kind)
            weight = float(eq.get("weight", 0) or 0) / per or cat_w
            cost = float(eq.get("cost", 0) or 0) / per or cat_c
            _add_loose(char, kind, per - 1, weight, cost)
        if eq["qty"] <= 0:
            char["equipment"].remove(eq)
        return True
    return False


def add_ammo(char: dict, kind: str, n: int) -> int:
    """Restock: n more loose pieces. Returns the new count."""
    weight, cost = _catalog_piece(kind)
    _add_loose(char, kind, n, weight, cost)
    return ammo_count(char, kind)


def set_ammo(char: dict, kind: str, n: int) -> int:
    """Make the count n: extra pieces go in loose, and fewer are used up
    like shots (loose first, then a bundle opened). Returns the new count."""
    n, have = max(0, int(n)), ammo_count(char, kind)
    if n > have:
        return add_ammo(char, kind, n - have)
    for _ in range(have - n):
        spend_ammo(char, kind)
    return ammo_count(char, kind)
