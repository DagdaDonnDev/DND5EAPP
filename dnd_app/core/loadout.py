"""What you're holding and wearing -- the Loadout tab, the same on both apps.

    loadout(char) -> {
        "in_hand": [slot, slot, slot]   main hand, off hand, armor
        "worn":    [slot, ...]          head, eyes, neck, cloak, hands, wrists,
                                        waist, feet, ring, ring
        "other":   [slot, ...]          magic items in use with no body slot
                                        (a wand, an ioun stone, a second
                                        cloak with nowhere to go)
        "tattoos": [slot, ...]          magic tattoos, each with where it is
        "ac", "saves", "attuned", "limit"
    }

A slot: {"key", "label", "name" ("" = empty), "uid" (a magic item's, or ""),
"what" (one short line of what it does), "state" ("att" attuned, "wear"
worn or held, "empty"), "needs" (it needs attuning), "attuned", "where" (a
tattoo's place)}.

Which body slot a magic item takes is worked out from its name (Boots ->
feet, Ring -> ring...): the item data doesn't say. One item to a slot, two
rings. Something put on when its slot is taken asks which to swap out
(slot_taken_by / swap_in).
"""
import re

SLOTS = [("head", "Head"), ("eyes", "Eyes"), ("neck", "Neck"), ("cloak", "Cloak"), ("hands", "Hands"),
         ("wrists", "Wrists"), ("waist", "Waist"), ("feet", "Feet"), ("ring", "Ring"), ("ring", "Ring")]
CAPACITY = {"ring": 2}
TATTOO_PLACES = ["Face", "Neck", "Chest", "Back", "Left arm", "Right arm", "Left hand", "Right hand",
                 "Left leg", "Right leg"]

_WORDS = [
    ("tattoo", r"\btattoo"),
    ("ring", r"\bring\b"),
    ("eyes", r"\b(goggles|lenses|spectacles|monocle|eyes of|eye patch|eyepatch)\b"),
    ("head", r"\b(helm|helmet|hat|cap|circlet|crown|headband|diadem|tiara|hood)\b"),
    ("neck", r"\b(amulet|necklace|periapt|medallion|brooch|scarab|torc|choker|pendant|scarf|collar)\b"),
    ("cloak", r"\b(cloak|cape|mantle|robe|wings of flying|shawl)\b"),
    ("hands", r"\b(gloves?|gauntlets?|mittens?)\b"),
    ("wrists", r"\b(bracers|bracelet|armbands?|bangle)\b"),
    ("waist", r"\b(belt|girdle|sash)\b"),
    ("feet", r"\b(boots|slippers|sandals|shoes|greaves)\b"),
]


def item_slot(name: str) -> str:
    """The body slot a worn magic item takes ("" for none: a wand, a bag,
    a weapon or armour -- those are in hand or worn as armour)."""
    from dnd_app.data.magic_items import get_magic_item
    from dnd_app.core.magic_items import is_magic_shield
    data = get_magic_item(name) or {}
    kind = data.get("type", "")
    if kind in ("Weapon", "Armor", "Potion", "Scroll", "Staff", "Wand", "Rod") or is_magic_shield(name):
        return ""
    if kind == "Ring":
        return "ring"
    low = (name or "").lower()
    for slot, pat in _WORDS:
        if re.search(pat, low):
            return slot
    return ""


def _sentence(text: str, limit: int = 70) -> str:
    t = re.sub(r"^\*.*?\n+", "", (text or "").strip())               # "* This generic variant..." notes
    t = re.sub(r"^(requires attunement[^.]*\.)\s*", "", t, flags=re.IGNORECASE)
    t = " ".join(t.split())
    m = re.match(r"(.+?(?<!ft)(?<!lb)[.!?])(\s|$)", t)
    t = m.group(1) if m else t
    if len(t) > limit:
        cut = t[:limit]
        t = (cut[:cut.rfind(" ")] if cut.rfind(" ") > limit * 0.6 else cut).rstrip(".,;: ") + "…"
    return t


def what_it_does(name: str) -> str:
    """One short line for a slot: a weapon's damage, armour's AC, else the
    first sentence of a magic item's text."""
    from dnd_app.data.items import WEAPON_DICT, ARMOR_DICT
    from dnd_app.data.magic_items import get_magic_item
    from dnd_app.core.magic_items import parse_magic_suffix
    base, bonus = parse_magic_suffix(name)
    w = WEAPON_DICT.get(name) or WEAPON_DICT.get(base)
    if w:
        dmg = f"{w.get('damage', '')} {w.get('dmg_type', '')}".strip()
        return dmg + (f", +{bonus} to hit and damage" if bonus else "")
    a = ARMOR_DICT.get(name) or ARMOR_DICT.get(base)
    if a:
        if a.get("type") == "shield":
            return f"+{a.get('ac', 2) + (bonus or 0)} AC"
        cap = a.get("dex_cap", None)
        dex = " + DEX" if cap is None else ("" if cap == 0 else f" + DEX (max {cap})")
        return f"AC {a.get('ac', 10) + (bonus or 0)}{dex}"
    from dnd_app.core.magic_items import is_magic_shield
    if is_magic_shield(name):
        m = re.search(r"\+(\d)", name)
        return f"+{2 + (int(m.group(1)) if m else 0)} AC"
    data = get_magic_item(name) or {}
    return _short(_sentence(data.get("desc", ""), 120))


def _short(t: str, limit: int = 70) -> str:
    """"While you wear this cloak, you gain a +1 bonus to AC." -> "+1 bonus
    to AC": the wearing is said by the slot."""
    t = re.sub(r"^while (?:you(?:'re| are)? )?(?:wear(?:ing)?|hold(?:ing)?|attuned)[^,]*,\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+while (?:you )?(?:wear|are wearing|wearing|hold|holding)[^.]*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^you (?:gain|have|can|are)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(?:the following benefits?:?)\s*[\u2022*-]?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(?:a|an)\s+(?=[+\d])", "", t)
    t = t.rstrip(". ")
    if len(t) > limit:
        cut = t[:limit]
        t = (cut[:cut.rfind(" ")] if cut.rfind(" ") > limit * 0.6 else cut).rstrip(".,;: ") + "\u2026"
    return t[:1].upper() + t[1:]


def _needs(name: str) -> bool:
    from dnd_app.data.magic_items import get_magic_item
    return bool((get_magic_item(name) or {}).get("attunement"))


def _slot(key, label, name="", uid="", attuned=False, where="", what=None):
    if not name:
        return {"key": key, "label": label, "name": "", "uid": "", "what": "", "state": "empty",
                "needs": False, "attuned": False, "where": ""}
    return {"key": key, "label": label, "name": name, "uid": uid,
            "what": what_it_does(name) if what is None else what,
            "state": "att" if attuned else "wear", "needs": _needs(name), "attuned": bool(attuned), "where": where}


def _magic_by_name(char):
    from dnd_app.core.magic_items import owned_magic_items
    out = {}
    for e in owned_magic_items(char):
        out.setdefault(e.get("name", ""), []).append(e)
    return out


def worn_magic(char: dict) -> list:
    """The magic items in use that take a body slot or none at all (not a
    weapon, armour or shield): equipped ones, attuned or not."""
    from dnd_app.core.magic_items import owned_magic_items, is_magic_shield
    from dnd_app.data.magic_items import get_magic_item
    out = []
    for e in owned_magic_items(char):
        n = e.get("name", "")
        if not e.get("equipped"):
            continue
        kind = (get_magic_item(n) or {}).get("type", "")
        if kind in ("Weapon", "Armor") or is_magic_shield(n) or kind in ("Potion", "Scroll"):
            continue
        if not item_slot(n) and not _needs(n):
            continue            # a bag, a deck: carried, in your inventory
        out.append(e)
    return out


def in_inventory(char: dict, entry: dict) -> bool:
    """Is this magic item in your inventory (not in use)? Weapons, armour and
    shields: while not held or worn; anything else: while not equipped."""
    from dnd_app.core.magic_items import is_magic_shield
    from dnd_app.data.magic_items import get_magic_item
    n = entry.get("name", "")
    kind = (get_magic_item(n) or {}).get("type", "")
    if kind == "Weapon":
        return n not in (char.get("equipped_weapons") or [])
    if is_magic_shield(n):
        return not (char.get("shield") and entry.get("equipped"))
    if kind == "Armor":
        return char.get("armor_worn") != n
    if not item_slot(n) and not _needs(n):
        return True
    return not entry.get("equipped")


def loadout(char: dict) -> dict:
    from dnd_app.core.weapons import hands
    from dnd_app.core.magic_items import attunement_limit, owned_magic_items, is_magic_shield
    from dnd_app.data.items import ARMOR_DICT
    by_name = _magic_by_name(char)

    def magic(name):
        copies = by_name.get(name) or []
        e = next((c for c in copies if c.get("equipped")), copies[0] if copies else None)
        return (e.get("uid", ""), bool(e.get("attuned"))) if e else ("", False)

    h = hands(char)
    main, off = h["main"], h["off"]
    shield = ""
    if char.get("shield"):
        shield = next((e.get("name") for e in owned_magic_items(char)
                       if is_magic_shield(e.get("name", "")) and e.get("equipped")), "")
        if not shield:
            shield = next((e.get("name") for e in char.get("equipment", [])
                           if ARMOR_DICT.get(e.get("name", ""), {}).get("type") == "shield"), "Shield")
    off_name = off or shield
    armor = char.get("armor_worn") or ""
    if armor in ("No Armor", "Mage Armor (spell)"):
        armor = ""
    from dnd_app.core.weapons import can_swap_hands, _props
    in_hand = []
    for key, label, n in (("main", "Main hand", main), ("off", "Off hand", off_name), ("armor", "Armor", armor)):
        uid, att = magic(n) if n else ("", False)
        s = _slot(key, label, n, uid, att)
        s["shield"] = key == "off" and bool(n) and not off           # the off hand holds a shield
        s["swap"] = key in ("main", "off") and bool(n) and can_swap_hands(char, n)
        s["versatile"], s["grip"] = False, ""
        in_hand.append(s)
    # a two-handed weapon (or a versatile one held in both hands) takes
    # both hands: the two slots are one
    props = _props(main, char) if main else []
    vers = next((p for p in props if p.startswith("Versatile")), "")
    if main and not off and not char.get("shield") and vers:
        in_hand[0]["versatile"] = True
        in_hand[0]["grip"] = "2H" if char.get("two_handed_grip") else "1H"
    if main and ("Two-handed" in props or in_hand[0]["grip"] == "2H"):
        both = in_hand[0]
        both["key"], both["label"] = "both", "Both hands"
        if in_hand[0]["grip"] == "2H":
            m = re.search(r"\(([^)]+)\)", vers)
            if m:
                both["what"] = re.sub(r"^\S+", m.group(1), both["what"], count=1) + " (two-handed)"
        in_hand = [both, in_hand[2]]

    # worn: into their slots, in the order you put them on
    free = {k: CAPACITY.get(k, 1) for k, _l in SLOTS}
    placed, other, tattoos = {}, [], []
    for e in worn_magic(char):
        n = e.get("name", "")
        slot = item_slot(n)
        s = _slot(slot or "other", "", n, e.get("uid", ""), e.get("attuned"), e.get("where", ""))
        if slot == "tattoo":
            s["label"] = "Tattoo"
            tattoos.append(s)
        elif slot and free.get(slot, 0) > 0:
            free[slot] -= 1
            placed.setdefault(slot, []).append(s)
        else:
            s["label"] = "In use"
            other.append(s)
    worn = []
    for key, label in SLOTS:
        got = placed.get(key) or []
        s = got.pop(0) if got else _slot(key, label)
        s["label"] = label
        s["key"] = key
        worn.append(s)

    attuned = len(char.get("attuned_items") or [])
    from dnd_app.core.calculator import get_ac, class_levels
    saves = ""
    if class_levels(char).get("Artificer", 0) >= 20 and attuned:
        saves = f"+{attuned} to saves"
    return {"in_hand": in_hand, "worn": worn, "other": other, "tattoos": tattoos,
            "ac": get_ac(char), "saves": saves, "attuned": attuned, "limit": attunement_limit(char),
            "places": list(TATTOO_PLACES)}


def _occupants(char: dict, uid: str) -> tuple:
    """(the slot this magic item goes in, what's in it now)."""
    from dnd_app.core.magic_items import find_magic_item
    e = find_magic_item(char, uid)
    if not e:
        return "", []
    slot = item_slot(e.get("name", ""))
    if not slot or slot == "tattoo":
        return slot, []
    return slot, [w for w in worn_magic(char) if item_slot(w.get("name", "")) == slot and w.get("uid") != uid]


def slot_taken_by(char: dict, uid: str) -> list:
    """Putting on this magic item when its slot is full and there's a choice
    of which to take off (two rings on): the items there. [] otherwise --
    a full slot of one (boots, a cloak) just swaps."""
    slot, there = _occupants(char, uid)
    cap = CAPACITY.get(slot, 1)
    return there if cap > 1 and len(there) >= cap else []


def sync_magic_weapons(char: dict) -> None:
    """A magic weapon put down to free a hand is no longer in use (its
    magic stops) -- its copy stops being "equipped" too."""
    from dnd_app.core.magic_items import owned_magic_items
    from dnd_app.data.magic_items import get_magic_item
    held = char.get("equipped_weapons") or []
    for e in owned_magic_items(char):
        if (get_magic_item(e.get("name", "")) or {}).get("type") == "Weapon" and e.get("equipped") \
                and e.get("name") not in held:
            e["equipped"] = False


def put_on(char: dict, uid: str, swap_out: str = "", hand: str = "") -> str:
    """Put a magic item on (equip it). What was in its slot goes back to
    your inventory: swap_out, or the one item a slot of one holds.
    Returns the name of what came off ("" if nothing)."""
    from dnd_app.core.magic_items import set_owned_magic_item_equipped, find_magic_item
    if not swap_out:
        slot, there = _occupants(char, uid)
        if there and len(there) >= CAPACITY.get(slot, 1) and CAPACITY.get(slot, 1) == 1:
            swap_out = there[0].get("uid", "")
    off = ""
    if swap_out:
        old = find_magic_item(char, swap_out)
        off = old.get("name", "") if old else ""
        set_owned_magic_item_equipped(char, swap_out, False)
    e = find_magic_item(char, uid) or {}
    if hand and e:
        # a weapon into the hand chosen (core/weapons.py hand_choice)
        from dnd_app.core.weapons import equip_weapon
        equip_weapon(char, e.get("name", ""), hand=hand)
        e["equipped"] = True
    else:
        set_owned_magic_item_equipped(char, uid, True)
    sync_magic_weapons(char)
    return off


def take_off(char: dict, uid: str) -> None:
    from dnd_app.core.magic_items import set_owned_magic_item_equipped
    set_owned_magic_item_equipped(char, uid, False)


def fits_slot(char: dict, slot: str) -> list:
    """The magic items in your inventory that go in this slot (an empty
    slot clicked: what could go there)."""
    from dnd_app.core.magic_items import owned_magic_items
    return [e for e in owned_magic_items(char)
            if in_inventory(char, e) and item_slot(e.get("name", "")) == slot]


def set_tattoo_place(char: dict, uid: str, where: str) -> None:
    from dnd_app.core.magic_items import find_magic_item
    e = find_magic_item(char, uid)
    if e is not None:
        e["where"] = where


def is_tattoo(name: str) -> bool:
    return item_slot(name) == "tattoo"


# ── Changing a slot (the Loadout's clicks, both apps) ─────────────────────
def _magic_kind(name: str) -> str:
    from dnd_app.data.magic_items import get_magic_item
    from dnd_app.core.magic_items import is_magic_shield
    if is_magic_shield(name):
        return "shield"
    return {"Weapon": "weapon", "Armor": "armor"}.get((get_magic_item(name) or {}).get("type", ""), "")


def _mundane_kind(name: str) -> str:
    from dnd_app.data.items import WEAPON_DICT, ARMOR_DICT
    from dnd_app.core.magic_items import parse_magic_suffix
    base, _ = parse_magic_suffix(name)
    if base in WEAPON_DICT:
        return "weapon"
    a = ARMOR_DICT.get(base)
    if a and name not in ("No Armor", "Mage Armor (spell)"):
        return "shield" if a.get("type") == "shield" else "armor"
    return ""


def slot_options(char: dict, slot: str) -> list:
    """What could go in a slot from your inventory: [{"name", "uid"}] (uid
    "" for an ordinary item). Hands take weapons (the off hand a shield
    too), Armor takes armour, a worn slot the magic items that fit it."""
    from dnd_app.core.magic_items import owned_magic_items
    if slot in ("main", "off", "both", "armor"):
        want = {"main": ("weapon",), "both": ("weapon",), "off": ("weapon", "shield"), "armor": ("armor",)}[slot]
        held = list(char.get("equipped_weapons") or [])
        out = []
        for e in char.get("equipment", []):
            n, kind = e.get("name", ""), _mundane_kind(e.get("name", ""))
            if kind not in want:
                continue
            if kind == "weapon" and held.count(n) >= e.get("qty", 1):
                continue                               # every one of them is in hand
            if kind == "armor" and char.get("armor_worn") == n:
                continue
            if kind == "shield" and char.get("shield"):
                continue
            if all(o["name"] != n for o in out):
                out.append({"name": n, "uid": ""})
        for e in owned_magic_items(char):
            if _magic_kind(e.get("name", "")) in want and in_inventory(char, e):
                out.append({"name": e.get("name", ""), "uid": e.get("uid", "")})
        return out
    return [{"name": e.get("name", ""), "uid": e.get("uid", "")} for e in fits_slot(char, slot)]


def _drop_shield(char):
    from dnd_app.core.magic_items import owned_magic_items, is_magic_shield
    char["shield"] = False
    for e in owned_magic_items(char):
        if is_magic_shield(e.get("name", "")):
            e["equipped"] = False


def take_off_slot(char: dict, slot: str, uid: str = "") -> str:
    """Right-click (press and hold) on a slot: what's there goes back to
    your inventory. Returns its name."""
    from dnd_app.core.weapons import hands
    h = hands(char)
    eq = char.setdefault("equipped_weapons", [])
    if slot == "both":
        gone = h["main"]
        eq[:] = []
    elif slot == "main":
        gone = h["main"]
        if eq:
            eq.pop(0)
    elif slot == "off":
        if h["off"]:
            gone = h["off"]
            eq.pop(1)
        else:
            from dnd_app.core.magic_items import owned_magic_items, is_magic_shield
            gone = next((e.get("name") for e in owned_magic_items(char)
                         if is_magic_shield(e.get("name", "")) and e.get("equipped")), "Shield")
            _drop_shield(char)
    elif slot == "armor":
        gone = char.get("armor_worn", "")
        if uid:
            take_off(char, uid)
        char["armor_worn"] = "No Armor"
    else:
        from dnd_app.core.magic_items import find_magic_item
        e = find_magic_item(char, uid) or {}
        gone = e.get("name", "")
        take_off(char, uid)
    sync_magic_weapons(char)
    return gone or ""


def equip_slot(char: dict, slot: str, name: str, uid: str = "") -> str:
    """Left-click a slot and pick something: it goes there, and whatever was
    there goes back to your inventory. Returns the name of what came off."""
    from dnd_app.core.weapons import hands, equip_weapon
    from dnd_app.core.magic_items import find_magic_item, set_owned_magic_item_equipped
    kind = _magic_kind(name) if uid else _mundane_kind(name)
    h = hands(char)
    eq = char.setdefault("equipped_weapons", [])
    off_name = ""
    if slot in ("main", "off", "both"):
        if kind == "shield":
            if h["off"]:
                off_name = h["off"]
                eq.pop(1)
            from dnd_app.core.weapons import _props
            if eq and "Two-handed" in _props(eq[0], char):
                off_name = eq.pop(0)
            if uid:
                set_owned_magic_item_equipped(char, uid, True)
            char["shield"] = True
        else:
            if slot == "both":
                off_name = h["main"]
                eq[:] = []
                _drop_shield(char) if char.get("shield") else None
                equip_weapon(char, name)
            elif slot == "off" and not h["off"] and char.get("shield"):
                off_name = "Shield"
                _drop_shield(char)
                equip_weapon(char, name)
            elif h[slot] and h["main"] and h["off"]:
                off_name = h[slot]
                eq[:] = [name, h["off"]] if slot == "main" else [h["main"], name]
                from dnd_app.core.weapons import _props
                if "Two-handed" in _props(name, char):
                    eq[:] = [name]
            else:
                if h[slot]:
                    off_name = h[slot]
                    eq.pop(0 if slot == "main" else 1)
                equip_weapon(char, name, another=name in eq)
                if slot == "main" and len(eq) == 2 and eq[1] == name and eq[0] != name:
                    eq.reverse()
            if uid:
                e = find_magic_item(char, uid)
                if e is not None:
                    e["equipped"] = True
        sync_magic_weapons(char)
        return off_name
    if slot == "armor":
        off_name = char.get("armor_worn", "")
        off_name = "" if off_name in ("No Armor", "") else off_name
        if uid:
            set_owned_magic_item_equipped(char, uid, True)
        else:
            from dnd_app.core.magic_items import owned_magic_items
            for e in owned_magic_items(char):           # a magic suit taken off
                if e.get("name") == off_name:
                    e["equipped"] = False
            char["armor_worn"] = name
        return off_name
    # a worn slot: the item that was there comes off (a full slot of one)
    return put_on(char, uid)


def set_two_handed_grip(char: dict, two: bool) -> None:
    """A versatile weapon held in both hands, or in one (how the Loadout
    shows it; the Combat page shows both damage dice either way)."""
    char["two_handed_grip"] = bool(two)
