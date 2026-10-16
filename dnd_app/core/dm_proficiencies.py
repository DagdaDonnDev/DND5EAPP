"""Proficiencies your DM grants outside the normal rules: a weapon, an
armour type, a tool or a language. Both apps' sheets edit them here.

They're kept in char["dm_proficiencies"] ({"weapons": [...], "armor":
[...], "tools": [...], "languages": [...]}) and added to the matching
proficiency list on every rebuild (core/builder.py), so they count
everywhere a granted one does: attack rolls, Dedicated Weapon, feat
prerequisites, tool use and the exported sheet."""

# (key, heading, the proficiency list it adds to)
KINDS = (
    ("weapons", "Weapons", "weapon_proficiencies"),
    ("armor", "Armor", "armor_proficiencies"),
    ("tools", "Tools", "tool_proficiencies"),
    ("languages", "Languages", "languages"),
)
_LIST_FOR = {key: target for key, _, target in KINDS}


def granted(char: dict, kind: str) -> list:
    """What the DM has granted of one kind, in the order it was added."""
    return list((char.get("dm_proficiencies") or {}).get(kind, []))


def add(char: dict, kind: str, name: str) -> bool:
    """Grant one; False if it's empty or already granted (any case)."""
    name = " ".join((name or "").split())
    if kind not in _LIST_FOR or not name:
        return False
    picks = char.setdefault("dm_proficiencies", {}).setdefault(kind, [])
    if any(p.lower() == name.lower() for p in picks):
        return False
    picks.append(name)
    return True


def remove(char: dict, kind: str, name: str) -> None:
    picks = (char.get("dm_proficiencies") or {}).get(kind, [])
    if name in picks:
        picks.remove(name)


def apply_to(char: dict) -> None:
    """Add every DM-granted proficiency to its list (called by rebuild,
    after the race/class/background/feat grants are in)."""
    for kind, target in _LIST_FOR.items():
        have = char.setdefault(target, [])
        lowered = {str(h).lower() for h in have}
        for name in granted(char, kind):
            if name.lower() not in lowered:
                have.append(name)
                lowered.add(name.lower())


def suggestions(kind: str) -> list:
    """What the add list offers (anything else can be typed in)."""
    if kind == "weapons":
        from dnd_app.data.items import WEAPON_DICT
        return (["Simple weapons", "Martial weapons", "Firearms"]
                + sorted(n for n in WEAPON_DICT if n != "Unarmed Strike"))
    if kind == "armor":
        return ["Light armor", "Medium armor", "Heavy armor", "Shields"]
    if kind == "tools":
        from dnd_app.data.items import ALL_TOOLS
        return sorted(ALL_TOOLS, key=str.lower)
    if kind == "languages":
        from dnd_app.data.feature_ui_interactions import LANGUAGES
        return list(LANGUAGES)
    return []
