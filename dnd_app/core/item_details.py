"""What an item's details page says, the same on both apps: the desktop
magnifying glasses (browsers, inventory, owned magic items) and Android's
View buttons and press-and-hold.

item_detail(char, name) -> {name, subtitle, facts: [str], desc}, plus
rarity for a magic item or a spell scroll. A scroll with a spell on it
also says whether this character can read it, so it needs the character.
"""
from dnd_app.core.magic_items import parse_magic_suffix, parse_material_prefix
from dnd_app.core.spellcasting import parse_spell_scroll, scroll_base_name, scroll_reading
from dnd_app.data.items import ADVENTURING_GEAR, ALL_TOOLS, ARMOR_DICT, MOUNTS, WEAPON_DICT
from dnd_app.data.magic_items import get_magic_item, magic_item_facts
from dnd_app.data.spells import get_spell


def _gp(cost) -> str:
    return f"{cost:g} gp" if cost >= 1 else f"{round(cost * 100):g} cp" if cost else ""


def item_detail(char: dict, name: str) -> dict:
    scroll = parse_spell_scroll(name)
    if scroll and scroll[1] and get_spell(scroll[1]):
        # a bound scroll: its spell, the scroll's own DC/attack, and
        # whether this character can read it
        sp = get_spell(scroll[1])
        info = scroll_reading(char, scroll[1])
        lvl_txt = "Cantrip" if sp["level"] == 0 else f"Level {sp['level']}"
        facts = [f"{lvl_txt} {sp.get('school', '')}".strip(),
                 f"Casting time: {sp.get('cast_time', '1 action')}", f"Range: {sp.get('range', '')}",
                 f"Duration: {sp.get('duration', '')}" + ("  (concentration)" if sp.get("concentration") else ""),
                 f"Scroll save DC {info['save_dc']}, spell attack +{info['attack']}",
                 ("You can't read this scroll -- the spell isn't on your class's list." if not info["readable"]
                  else f"Above your casting level: {info['check']['ability']} check, DC {info['check']['dc']}, to cast it."
                  if info["check"] else "You can cast this from the scroll.")]
        base = get_magic_item(scroll_base_name(scroll[0])) or {}
        return {"name": name, "subtitle": f"Spell scroll: {scroll[1]}", "facts": facts,
                "desc": sp.get("desc", ""), "rarity": base.get("rarity", "")}
    mi = get_magic_item(name)
    if mi:
        # the rarity goes with the subtitle ("Uncommon magic item"), not here
        facts = [f for f in [mi.get("type", "")] + magic_item_facts(mi) if f]
        return {"name": name, "subtitle": "Magic item", "facts": facts, "desc": mi.get("desc", ""),
                "rarity": mi.get("rarity", "")}
    unprefixed, material = parse_material_prefix(name)
    base, _ = parse_magic_suffix(unprefixed)
    w = WEAPON_DICT.get(base)
    if w:
        facts = [w.get("category", ""), f"{w.get('damage', '')} {w.get('dmg_type', '')}".strip()]
        if w.get("properties"):
            facts.append(", ".join(w["properties"]))
        facts += [f"{w.get('weight', 0):g} lb" if w.get("weight") else "", _gp(w.get("cost", 0))]
        desc = {
            "Silvered": "Silvered: gets past a creature's resistance or immunity to nonmagical "
                        "attacks that aren't silvered, such as a lycanthrope's.",
            "Adamantine": "Adamantine: any hit against an object is a critical hit.",
        }.get(material, "")
        return {"name": name, "subtitle": f"{material} weapon".strip().capitalize(),
                "facts": [f for f in facts if f], "desc": desc}
    a = ARMOR_DICT.get(name)
    if a:
        kind = (a.get("type") or "").title()
        ac = f"+{a.get('ac')} AC" if a.get("type") == "shield" else f"AC {a.get('ac')}" + (
            "" if a.get("dex_cap") == 0 else " + DEX" + (f" (max {a['dex_cap']})" if a.get("dex_cap") else ""))
        facts = [f"{kind} armor" if kind and kind != "Shield" else kind, ac,
                 f"Needs STR {a['str_req']}" if a.get("str_req") else "",
                 "Disadvantage on Stealth" if a.get("stealth") else "",
                 f"{a.get('weight', 0):g} lb" if a.get("weight") else "", _gp(a.get("cost", 0))]
        return {"name": name, "subtitle": "Armor", "facts": [f for f in facts if f], "desc": ""}
    # Background kits word some gear the other way round
    # ("common clothes" for "Clothes, Common").
    words = name.lower().split()
    flipped = f"{words[-1]}, {' '.join(words[:-1])}" if len(words) > 1 else ""
    for row in ADVENTURING_GEAR:
        if row[0].lower() in (name.lower(), flipped):
            facts = [f"{row[1]:g} lb" if row[1] else "", _gp(row[2]) if len(row) > 2 else ""]
            return {"name": row[0], "subtitle": "Adventuring gear", "facts": [f for f in facts if f],
                    "desc": row[3] if len(row) > 3 else ""}
    tool = next((t for t in ALL_TOOLS if t.lower() == name.lower()), None)
    if tool:
        return {"name": tool, "subtitle": "Tool", "facts": [],
                "desc": "Lets you add your proficiency bonus to ability checks made with it, if you're proficient."}
    mount = next((m for m in MOUNTS if m[0].lower() == name.lower()), None)
    if mount:
        return {"name": mount[0], "subtitle": "Mount",
                "facts": [f"Speed {mount[2]} ft", f"Carrying capacity {mount[1]}", _gp(mount[4])],
                "desc": "Adding it puts its stat block on the Companions tab."}
    return {"name": name, "subtitle": "Item", "facts": [],
            "desc": "No rules entry for this item -- it's a flavour or custom item."}
