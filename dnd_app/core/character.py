"""
Character module.

Defines the character model — the single source of truth for all
character state. A character is a plain dataclass-style dict that can
be serialized to JSON, plus accessor/mutator helpers (ability_score,
ability_mod, class_levels, subclasses, add_equipment, spend_spell_slot,
etc.) used throughout the rest of the app.

Author: Ethan O'Brien
Date: 2026-08-20
"""

import math
import copy
from dataclasses import dataclass, field
from typing import Optional


def clean_subclass_name(sub_str: str) -> str:
    """Canonical display/storage name for a subclass.

    Raw CLASS_DICT subclass strings look like:
      'College of Eloquence (MOT/TCE) – silver tongue; near-perfect Persuasion'
      'College of Lore – Cutting Words, Bonus Magical Secrets at 6'   (no source tag)
    Strips BOTH the em/en-dash feature summary AND the parenthetical source
    tag, in that order, so every UI (Choices-tab combo, level-up radio picker,
    Features-tab lookup) agrees on the same string. Splitting dash-first
    matters: some non-tagged core subclasses only have a dash to strip.
    """
    if not sub_str:
        return ""
    name = sub_str.split("\u2013")[0].split("\u2014")[0]  # – or —
    name = name.split("(")[0]
    return name.strip()


def default_abilities():
    return {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}


def default_skills():
    """All 18 skills → proficiency level: 0=none, 1=half, 2=proficient, 3=expertise"""
    return {
        "Acrobatics": 0, "Animal Handling": 0, "Arcana": 0, "Athletics": 0,
        "Deception": 0, "History": 0, "Insight": 0, "Intimidation": 0,
        "Investigation": 0, "Medicine": 0, "Nature": 0, "Perception": 0,
        "Performance": 0, "Persuasion": 0, "Religion": 0, "Sleight of Hand": 0,
        "Stealth": 0, "Survival": 0,
    }


def default_saving_throws():
    return {"STR": False, "DEX": False, "CON": False, "INT": False, "WIS": False, "CHA": False}


def default_death_saves():
    return {"successes": 0, "failures": 0}


def new_character() -> dict:
    """Return a fresh blank character dict."""
    return {
        # ── Identity ──────────────────────────────────────────────────────────
        "name": "",
        "player_name": "",
        # Which campaign/folder this save is organized under in the Load
        # Character list ("" = Uncategorized) -- purely organizational,
        # never read by any game-logic calculation.
        "folder": "",
        "edition": "2014",          # "2014" or "2024"
        "alignment": "True Neutral",
        "experience": 0,
        "leveling_mode": "milestone",  # "milestone" (DM decides) or "xp" (tracked XP)
        "inspiration": False,

        # ── Classes (multiclass support) ──────────────────────────────────────
        # List of {"class": str, "level": int, "subclass": str, "hit_die": int}
        "classes": [],

        # ── Species / Race ────────────────────────────────────────────────────
        "species": "",              # 2024 term
        "race": "",                 # 2014 term (same field, different label by edition)
        "subrace": "",
        "species_traits": [],       # list of applied trait strings

        # ── Background ────────────────────────────────────────────────────────
        "background": "",
        "background_feature": "",
        "background_notes": "",
        "origin_feat": "",          # 2024 only

        # ── Ability Scores ────────────────────────────────────────────────────
        "abilities": default_abilities(),
        # Bonus from feats/race on top of base (tracked separately)
        "ability_bonuses": {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0},
        # ASI/Feat choices (list of dicts describing each choice)
        "asi_choices": [],

        # ── Skills ────────────────────────────────────────────────────────────
        "skills": default_skills(),
        "saving_throws": default_saving_throws(),

        # ── Combat ────────────────────────────────────────────────────────────
        "max_hp": 0,
        "current_hp": 0,
        "temp_hp": 0,
        "hit_dice": {},             # {"d10": {"total": 5, "remaining": 5}}
        "death_saves": default_death_saves(),
        "armor_worn": "No Armor",
        "shield": False,
        "ac_override": None,        # manual override
        "initiative_bonus": 0,      # extra beyond DEX mod
        "speed": 30,
        "speed_overrides": {},      # {"fly": 30, "swim": 20, "climb": 0, "burrow": 0}

        # ── Spells ────────────────────────────────────────────────────────────
        "spell_slots_max": [0]*9,   # indices 0-8 = spell levels 1-9
        "spell_slots_used": [0]*9,
        "pact_slots_max": 0,
        "pact_slots_used": 0,
        "pact_slot_level": 0,
        "spells_known": [],         # list of spell name strings
        "spells_prepared": [],      # list of spell name strings marked prepared
        "cantrips": [],             # list of cantrip name strings

        # ── Class Resources ───────────────────────────────────────────────────
        # List of {"key": str, "name": str, "current": int, "max": int,
        #           "reset": "SR"|"LR", "source_class": str}
        "resources": [],

        # ── Feats ─────────────────────────────────────────────────────────────
        "feats": [],                # list of feat name strings
        "fighting_styles": [],      # list of fighting style strings

        # ── Equipment & Inventory ─────────────────────────────────────────────
        "currency": {"CP": 0, "SP": 0, "EP": 0, "GP": 0, "PP": 0},
        "equipment": [],            # list of {"name": str, "qty": int, "weight": float, "notes": str}
        "magic_items": [],          # list of {"name": str, "attunement": bool, "equipped": bool, "notes": str}
        "attuned_items": [],        # max 3 (or 4-6 with Artificer/feats) — item name strings
        "equipped_weapons": [],     # weapon name strings on character sheet
        "weapons": [],              # list of {"name": str, "attack_bonus": int, "damage": str, "notes": str}

        # ── Magic item modifiers (recomputed from attuned items) ───────────────
        "ability_overrides": {},    # {"STR": 19} — set ability to minimum value
        "skill_advantages": [],     # skills with advantage from items
        "skill_disadvantages": [],  # skills with disadvantage from items/armor
        "item_charges": {},         # {item_name: {current, max, recharge}}
        "item_granted_spells": [],
        "item_spell_uses": {},      # {"Fireball": 7}
        "item_actions": [],         # granted actions from items
        "spell_dc_bonus": 0,
        "spell_attack_bonus": 0,
        "magic_ac_bonus": 0,
        "magic_save_bonus": 0,

        # ── Concentration ─────────────────────────────────────────────────────
        "concentration": {"spell": None, "since_round": 0},

        # ── Player choices (persisted) ────────────────────────────────────────
        "_choices": {},
        "_grants": {},

        # ── Personality ───────────────────────────────────────────────────────
        "personality_traits": "",
        "ideals": "",
        "bonds": "",
        "flaws": "",
        "backstory": "",

        # ── Appearance ────────────────────────────────────────────────────────
        "age": "",
        "height": "",
        "weight": "",
        "eyes": "",
        "skin": "",
        "hair": "",
        "appearance_notes": "",

        # ── Notes ─────────────────────────────────────────────────────────────
        "notes": "",                # legacy flat field -- migrated into notes_pages on first sheet open
        "notes_pages": [],          # list of {"title": str, "text": str} -- the Traits & Notes tab's Campaign Notes pages
        "allies_and_organizations": "",
        "additional_features": "",
        "treasure": "",

        # ── Conditions ───────────────────────────────────────────────────────
        "conditions": [],           # active conditions: "Poisoned", "Grappled", etc.
        "exhaustion": 0,            # 0-6

        # ── Languages & Proficiencies ─────────────────────────────────────────
        "languages": ["Common"],
        "tool_proficiencies": [],
        "weapon_proficiencies": [],
        "armor_proficiencies": [],
        "other_proficiencies": [],

        # ── Metadata ──────────────────────────────────────────────────────────
        "version": "1.0",
        "created": "",
        "modified": "",
    }


def total_level(char: dict) -> int:
    return sum(c.get("level", 0) for c in char.get("classes", []))


# PHB standard XP-by-level table (identical in the 2014 and 2024 rules).
# Index i = cumulative XP required to REACH character level i+1.
XP_THRESHOLDS = [
    0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000,
    85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000,
]


def xp_for_level(level: int) -> int:
    """Cumulative XP required to reach `level` (1-20). Clamps out-of-range
    levels to the nearest end — there's no level 0 or level 21 threshold."""
    level = max(1, min(level, 20))
    return XP_THRESHOLDS[level - 1]


def xp_implied_level(xp: int) -> int:
    """Highest level (1-20) whose XP threshold this much XP has met."""
    level = 1
    for i, threshold in enumerate(XP_THRESHOLDS):
        if xp >= threshold:
            level = i + 1
    return level


def xp_progress(char: dict) -> dict:
    """XP progress toward the character's NEXT class level, keyed to
    total_level (the level they'd actually gain) rather than whatever
    level their raw XP total alone would imply — a character sitting on
    a huge XP surplus is only ever "ready" for the levels right above
    where they actually are, never further.

    A big enough surplus (e.g. a large one-time award, or importing an
    XP total from another tracker) can span more than one level at once
    — that carries over just like it does at the table, so `levels_due`
    counts how many levels are actually owed, not just whether one is.

    Returns {"xp", "floor", "next", "pct", "eligible", "level", "levels_due"}:
    floor/next are the XP thresholds bracketing the current level, pct is
    0-100 progress through that band, eligible is True once accumulated
    XP has crossed the threshold for the next level (already at max level
    is never eligible), and levels_due is the number of levels currently
    owed (0 when not eligible)."""
    level = total_level(char)
    xp = char.get("experience", 0)
    if level <= 0 or level >= 20:
        floor = xp_for_level(max(level, 1))
        return {"xp": xp, "floor": floor, "next": floor, "pct": 100,
                "eligible": False, "level": level, "levels_due": 0}
    floor = xp_for_level(level)
    nxt = xp_for_level(level + 1)
    span = nxt - floor
    pct = 100 if span <= 0 else max(0, min(100, round((xp - floor) * 100 / span)))
    levels_due = max(0, min(xp_implied_level(xp), 20) - level)
    return {"xp": xp, "floor": floor, "next": nxt, "pct": pct,
            "eligible": levels_due > 0, "level": level, "levels_due": levels_due}


def class_levels(char: dict) -> dict:
    """Return {class_name: level} dict."""
    return {c["class"]: c["level"] for c in char.get("classes", []) if c.get("level", 0) > 0}


def subclasses(char: dict) -> dict:
    """Return {class_name: subclass} dict."""
    return {c["class"]: c.get("subclass", "") for c in char.get("classes", []) if c.get("level", 0) > 0}


def ability_score(char: dict, ability: str, ignore_wildshape: bool = False) -> int:
    """Get total ability score including bonuses and item overrides."""
    # Wild Shape: STR/DEX/CON are strictly replaced by the beast form's
    # score while transformed — not a floor like ability_overrides below
    # (that mechanism is for effects like Belt of Giant Strength, which
    # only helps if your own score is lower). A beast's STR fully replaces
    # yours even if yours was higher. INT/WIS/CHA are deliberately left
    # alone: you keep your own mental stats while shapeshifted, per the
    # real rule. ignore_wildshape exists for callers like max HP
    # calculation, which needs the character's OWN CON regardless of
    # transformation — your own hit point maximum doesn't change while
    # wild shaped, you use the beast's separate HP pool instead.
    active_beast = char.get("_wildshape_active")
    if active_beast and not ignore_wildshape and ability in ("STR", "DEX", "CON"):
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(active_beast)
        if beast and ability in beast.get("abilities", {}):
            return beast["abilities"][ability]
    override = char.get("ability_overrides", {}).get(ability)
    base = char["abilities"].get(ability, 10)
    bonus = char["ability_bonuses"].get(ability, 0)
    # Ioun Stones etc. — additive on top of everything else, tracked
    # separately from ability_bonuses (which builder.py rebuilds from
    # scratch each call) so a magic item's contribution can never be wiped
    # by the next racial/ASI recompute or vice versa.
    item_bonus = char.get("magic_ability_bonuses", {}).get(ability, 0)
    total = base + bonus + item_bonus
    if override is not None:
        return max(total, override)
    return total


def ability_mod(char: dict, ability: str, ignore_wildshape: bool = False) -> int:
    return (ability_score(char, ability, ignore_wildshape) - 10) // 2


def get_class_entry(char: dict, class_name: str) -> Optional[dict]:
    for c in char.get("classes", []):
        if c["class"] == class_name:
            return c
    return None


def _lookup_hit_die(class_name: str, fallback: int = 8) -> int:
    """Authoritative hit die from class data — callers can't get it wrong."""
    try:
        from dnd_app.data.classes import CLASS_DICT
        return CLASS_DICT.get(class_name, {}).get("hit_die", fallback)
    except Exception:
        return fallback


def add_class(char: dict, class_name: str, level: int = 1,
              subclass: str = "", hit_die: int = 0) -> None:
    # hit_die param kept for API compatibility, but the class data is the
    # source of truth: a passed value is only used if the lookup fails.
    resolved_hd = _lookup_hit_die(class_name, hit_die or 8)
    existing = get_class_entry(char, class_name)
    if existing:
        existing["level"] = level
        existing["hit_die"] = resolved_hd   # self-heal stale entries
        if subclass:
            existing["subclass"] = subclass
    else:
        char["classes"].append({
            "class": class_name,
            "level": level,
            "subclass": subclass,
            "hit_die": resolved_hd,
        })


def remove_class(char: dict, class_name: str) -> None:
    char["classes"] = [c for c in char["classes"] if c["class"] != class_name]


def set_class_level(char: dict, class_name: str, level: int) -> None:
    entry = get_class_entry(char, class_name)
    if entry:
        entry["level"] = level
    else:
        add_class(char, class_name, level)


def level_up_block_reason(char: dict, class_name: str = "") -> str:
    """Why the character can't gain a level (in `class_name`, if given):
    character level 20 is the most there is, across every class combined,
    and no single class goes past 20 either; a new class needs the
    multiclassing ability scores (core/multiclass.py). "" when a level is
    fine."""
    if total_level(char) >= 20:
        return "you're at character level 20, the maximum"
    entry = get_class_entry(char, class_name) if class_name else None
    if entry and entry.get("level", 0) >= 20:
        return f"{class_name} is already at level 20"
    if class_name and not entry:
        from dnd_app.core.multiclass import multiclass_block_reason
        return multiclass_block_reason(char, class_name)
    return ""


def _subclass_levels(char: dict) -> dict:
    """{class: the level its subclass comes at}, for the character's edition."""
    from dnd_app.data.classes import CLASS_DICT as _D14
    try:
        from dnd_app.data.phb2024.classes_2024 import CLASS_DICT_2024 as _D24
    except Exception:
        _D24 = {}
    table = _D24 if char.get("edition") == "2024" else _D14
    return {name: data.get("subclass_level", 3) for name, data in table.items()}


def drop_subclasses_below_level(char: dict) -> list:
    """After a level down: a class that's now below the level it gets its
    subclass at (Fighter 3, Wizard 2, ...) can't keep one -- a "Fighter 2,
    Champion" contradicts itself. Sets those subclasses aside and returns
    [(class, the subclass it had, the level it comes back at)], so the
    caller can say so. The pick stays in _choices ("Fighter_subclass"),
    so levelling back up brings the same subclass back
    (restore_set_aside_subclasses, run by every rebuild)."""
    levels = _subclass_levels(char)
    dropped = []
    for entry in char.get("classes", []):
        sub = entry.get("subclass", "")
        need = levels.get(entry.get("class", ""), 3)
        if sub and entry.get("level", 1) < need:
            dropped.append((entry["class"], sub, need))
            char.setdefault("_choices", {})[f"{entry['class']}_subclass"] = [sub]
            entry["subclass"] = ""
    return dropped


def restore_set_aside_subclasses(char: dict) -> list:
    """A class back at its subclass level with no subclass, whose pick is
    still in _choices (set aside by a level down): give it back. Returns
    [(class, subclass)] restored."""
    levels = _subclass_levels(char)
    restored = []
    for entry in char.get("classes", []):
        cn = entry.get("class", "")
        pick = (char.get("_choices", {}).get(f"{cn}_subclass") or [""])[0]
        if pick and not entry.get("subclass") and entry.get("level", 1) >= levels.get(cn, 3):
            entry["subclass"] = clean_subclass_name(pick)
            restored.append((cn, entry["subclass"]))
    return restored


# Classes that prepare from their whole list (rebuild() adds the list to
# spells_known by level) -- the rest pick their spells one by one.
FULL_LIST_CLASSES = ("Cleric", "Druid", "Paladin", "Artificer")


def _spell_lists_of(entry: dict) -> set:
    """The class spell lists a class entry learns spells from: its own,
    the Wizard's for an Eldritch Knight or Arcane Trickster, and the
    Cleric's as well for a Divine Soul sorcerer."""
    cn = entry.get("class", "")
    sub = (entry.get("subclass") or "").lower()
    if cn == "Fighter":
        return {"Wizard"} if "eldritch knight" in sub else set()
    if cn == "Rogue":
        return {"Wizard"} if "arcane trickster" in sub else set()
    if cn == "Sorcerer" and "divine soul" in sub:
        return {"Sorcerer", "Cleric"}
    return {cn}


def picking_spell_lists(char: dict) -> set:
    """Spell lists of the character's classes that pick spells one by one
    (Wizard, Sorcerer, Bard, Warlock, Ranger, Eldritch Knight...)."""
    out = set()
    for entry in char.get("classes", []):
        if entry.get("class") not in FULL_LIST_CLASSES:
            out |= _spell_lists_of(entry)
    return out


def protected_spells(char: dict) -> set:
    """Spells something other than a class's own list gives the character,
    so taking a class away (or a level of one) never takes them:
      * granted spells -- race, feat, subclass, fighting style, invocation
        (char["bonus_spells"])
      * anything a race or feat lets them cast for free (core/spellcasting.py)
      * any spell picked through a race or feat choice"""
    out = set(char.get("bonus_spells", []))
    from .spellcasting import free_spells_of
    for res in char.get("resources", []):
        out |= set(free_spells_of(char, res))
    for key, picked in char.get("_choices", {}).items():
        if key.startswith(("feat_", "race_", "racial_", "astral_elf_")) and isinstance(picked, list):
            out |= {p for p in picked if isinstance(p, str)}
    return out


def drop_spells_of_removed_class(char: dict, removed: dict) -> list:
    """After a class is removed from char["classes"]: the known spells that
    came with it and that nothing left could give -- a Fighter who drops
    their Wizard levels doesn't keep Fireball. Takes them out of
    spells_known and returns their names (the rebuild that follows trims
    the prepared and quick lists to match). Call it before the removed
    class's choices are pruned, so its Magical Secrets picks still show.
      1. Lists the removed class learned from, and the lists still left.
         A spell on a list that's left stays (shared lists, like Fireball
         for a Sorcerer/Wizard).
      2. Its any-list picks (Magical Secrets) went with a removed Bard.
      3. A Bard who stays (Magical Secrets at 10, Lore at 6) could have
         picked a spell from any list, so nothing is taken from them.
      4. Spells from a race, feat or subclass are never touched."""
    from dnd_app.data.spells import get_spell
    gone = _spell_lists_of(removed)
    left = set()
    for entry in char.get("classes", []):
        left |= _spell_lists_of(entry)
    secrets = set()
    if removed.get("class") == "Bard":
        secrets |= set(char.get("magical_secrets_spells", []))
        for key, picked in char.get("_choices", {}).items():
            if key.startswith(("bard_magical_secrets", "bard_lore_secrets")):
                secrets |= set(picked)
        char.pop("magical_secrets_spells", None)
    for entry in char.get("classes", []):
        sub = (entry.get("subclass") or "").lower()
        lvl = entry.get("level", 0)
        if entry.get("class") == "Bard" and (lvl >= 10 or ("lore" in sub and lvl >= 6)):
            return []
    keep = protected_spells(char)
    lost = []
    for name in char.get("spells_known", []):
        if name in keep:
            continue
        sp = get_spell(name)
        lists = set(sp.get("classes", [])) if sp else set()
        came_with_it = bool(lists & gone) or name in secrets
        if came_with_it and not (lists & left):
            lost.append(name)
    if lost:
        char["spells_known"] = [n for n in char.get("spells_known", []) if n not in lost]
    return lost


def name_list(names: list, limit: int = 3) -> str:
    """"Fireball, Shield and Sleep" / "Fireball, Shield, Sleep and 2 more"."""
    names = list(names)
    if not names:
        return ""
    if len(names) <= limit + 1:
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    return ", ".join(names[:limit]) + f" and {len(names) - limit} more"


def set_subclass(char: dict, class_name: str, subclass: str) -> None:
    entry = get_class_entry(char, class_name)
    if entry:
        entry["subclass"] = clean_subclass_name(subclass)
        # the pick a level down sets aside and a level up brings back --
        # cleared with the subclass, so a cleared one stays cleared
        choices = char.setdefault("_choices", {})
        if entry["subclass"]:
            choices[f"{class_name}_subclass"] = [entry["subclass"]]
        else:
            choices.pop(f"{class_name}_subclass", None)


def add_feat(char: dict, feat_name: str) -> None:
    if feat_name not in char["feats"]:
        char["feats"].append(feat_name)


def remove_feat(char: dict, feat_name: str) -> None:
    char["feats"] = [f for f in char["feats"] if f != feat_name]


def set_skill_prof(char: dict, skill: str, level: int) -> None:
    """0=none, 1=half, 2=proficient, 3=expertise -- the player's own
    setting, kept as an override on top of what's granted (rebuild()
    rebuilds the rest; core/builder.set_skill_level drops an override
    that matches the granted level)."""
    level = max(0, min(3, level))
    char.setdefault("skill_overrides", {})[skill] = level
    char["skills"][skill] = level


def add_equipment(char: dict, name: str, qty: int = 1,
                  weight: float = 0.0, notes: str = "") -> None:
    char["equipment"].append({"name": name, "qty": qty, "weight": weight, "notes": notes})


def add_magic_item(char: dict, name: str, attunement: bool = False, notes: str = "") -> None:
    char["magic_items"].append({"name": name, "attunement": attunement, "notes": notes})


def add_weapon(char: dict, name: str, attack_bonus: int = 0,
               damage: str = "", damage_type: str = "", notes: str = "") -> None:
    char["weapons"].append({
        "name": name, "attack_bonus": attack_bonus,
        "damage": damage, "damage_type": damage_type, "notes": notes,
    })


def spend_spell_slot(char: dict, level: int) -> bool:
    idx = level - 1
    if 0 <= idx < 9 and char["spell_slots_used"][idx] < char["spell_slots_max"][idx]:
        char["spell_slots_used"][idx] += 1
        return True
    return False


def restore_spell_slot(char: dict, level: int) -> bool:
    idx = level - 1
    if 0 <= idx < 9 and char["spell_slots_used"][idx] > 0:
        char["spell_slots_used"][idx] -= 1
        return True
    return False


def long_rest_block_reason(char: dict) -> str:
    """Why a long rest can't happen right now ("" if it can). A character
    needs at least 1 hit point when the rest starts to gain its benefits
    (PHB p.186) -- one at 0 HP is dying or stable, not resting."""
    if char.get("is_dead"):
        return "you're dead"
    if char.get("current_hp", 0) <= 0 and not char.get("_wildshape_active"):
        return "you need at least 1 HP to start one"
    return ""


def long_rest(char: dict) -> None:
    """Reset all LR resources."""
    char["current_hp"] = char["max_hp"]
    char["temp_hp"] = 0
    char["spell_slots_used"] = [0] * 9
    char["pact_slots_used"] = 0
    char["death_saves"] = default_death_saves()
    # Companions that died mid-adventure (Steel Defender, Beast of the
    # Land/Sea/Sky) become available to recreate again at the end of a
    # long rest, matching the real rule — clear both the pending flag
    # and the stale HP tracking entry, so it doesn't reappear still
    # showing 0 HP from before it died.
    pending = char.get("companion_pending_replacement", [])
    if pending:
        tracking = char.get("summon_hp_tracking", {})
        for key in pending:
            tracking.pop(f"companion_{key}", None)
        char["companion_pending_replacement"] = []
    conc = char.setdefault("concentration", {"spell": None, "since_round": 0})
    conc["spell"] = None
    conc["since_round"] = 0
    # Reset LR resources
    for res in char.get("resources", []):
        if res.get("reset") in ("LR", "SR/LR"):
            res["current"] = res.get("current_max") or res.get("max", 0)
    # a Diviner's Portent: the unused rolls are lost and new ones rolled
    from dnd_app.core.action_use import roll_portent
    roll_portent(char)
    # Restore hit dice up to half total (rounded up, min 1) — PHB p.186
    # Restore is a shared POOL distributed across all die types
    total = total_level(char)
    pool = max(1, math.ceil(total / 2))
    hd_dict = char.get("hit_dice", {})
    # Prioritise the primary class die (first entry in classes)
    ordered_keys = []
    for cls_entry in char.get("classes", []):
        hd_key = f"d{cls_entry.get('hit_die', 8)}"
        if hd_key in hd_dict and hd_key not in ordered_keys:
            ordered_keys.append(hd_key)
    for k in hd_dict:
        if k not in ordered_keys:
            ordered_keys.append(k)
    for hd_key in ordered_keys:
        if pool <= 0:
            break
        hd_data = hd_dict[hd_key]
        deficit = hd_data["total"] - hd_data["remaining"]
        give = min(deficit, pool)
        hd_data["remaining"] += give
        pool -= give


def short_rest(char: dict) -> None:
    """Reset SR resources (SR resets do NOT reset LR resources)."""
    char["pact_slots_used"] = 0
    # Wild Shape (key "wild_shape") recovers here too via the generic
    # "SR"/"SR/LR" resource-reset loop below, through its shared
    # char["resources"] entry (see the reset="SR/LR" note on its
    # definition in classes.py/classes_2024.py) rather than a separate
    # ad hoc counter.
    for res in char.get("resources", []):
        if res.get("reset") in ("SR", "SR/LR"):
            res["current"] = res.get("current_max") or res.get("max", 0)
    # Cleric Channel Divinity recovers 1 on SR (2024)
    for res in char.get("resources", []):
        if res.get("key") == "channel_divinity" and res.get("reset") == "LR":
            sr_recover = res.get("sr_recover", 0)
            if sr_recover:
                res["current"] = min(res["max"], res.get("current", 0) + sr_recover)


def deep_copy(char: dict) -> dict:
    return copy.deepcopy(char)


# ── Rest options and preview (both apps' rest dialogs) ──────────────────────

def rest_options(char: dict, rest_type: str) -> list:
    """What a rest lets the character re-pick, for both apps' rest dialogs:
    re-preparing spells, an Armorer's armour model, Arcane Recovery, an
    Eladrin's season, a pact boon's bonded item or book... (long or short
    rest, as each allows). [{"kind", "label", "detail"}, ...]"""
    opts = []
    # Unprepare all spells — any prepared caster, long rest only (this
    # is the normal way of re-choosing prepared spells: 1 minute per
    # spell level during a long rest, PHB p.201-202).
    if rest_type == "long":
        from dnd_app.core.spellcasting import spell_progression_tables
        _, _, _, prep_ab = spell_progression_tables()
        if any(cn in prep_ab for cn in {c["class"] for c in char.get("classes", [])}):
            if char.get("spells_prepared"):
                opts.append({
                    "kind": "unprepare_all",
                    "label": "Unprepare all spells (choose new ones afterward)",
                    "detail": "Clears every non-bonus prepared spell so you can pick a "
                              "different set from the Spells tab.",
                })
    # Armorer's Arcane Armor model is changeable on either rest type with smith's tools in hand.
    is_armorer = any(
        c.get("class") == "Artificer" and "armorer" in c.get("subclass", "").lower()
        for c in char.get("classes", [])
    )
    if is_armorer and char.get("_choices", {}).get("armorer_model_3"):
        opts.append({
            "kind": "armorer_model",
            "label": "Change Arcane Armor model (Guardian / Infiltrator)",
            "detail": "Requires smith's tools in hand.",
        })
    # Arcane Recovery (Wizard 1+): short rest only (the rule triggers
    # "when you finish a short rest"), once per day (checked via the
    # resource added in update_all), only if there's actually
    # something expended to recover.
    if rest_type == "short":
        arcane_recovery_res = next(
            (r for r in char.get("resources", []) if r.get("key") == "arcane_recovery"), None)
        if arcane_recovery_res and arcane_recovery_res.get("current", 0) > 0:
            if any(char.get("spell_slots_used", [])):
                opts.append({
                    "kind": "arcane_recovery",
                    "label": "Arcane Recovery — recover expended spell slots",
                    "detail": "Once per day: recover slots totaling \u2264 half your Wizard "
                              "level (rounded up), max slot level 5.",
                })
    # Natural Recovery (Circle of the Land 2+): the same, for a Druid --
    # "during a short rest", once a day, slots totaling <= half your Druid
    # level (rounded up), none 6th level or higher.
    if rest_type == "short":
        nr = next((r for r in char.get("resources", []) if r.get("key") == "use_natural_recovery"), None)
        if nr and nr.get("current", 0) > 0 and any(char.get("spell_slots_used", [])[:5]):
            opts.append({
                "kind": "natural_recovery",
                "label": "Natural Recovery — recover expended spell slots",
                "detail": "Once per day: recover slots totaling \u2264 half your Druid level "
                          "(rounded up), none 6th level or higher.",
            })
    # Eladrin season changes only on a long rest ("you can change your chosen season after a long rest").
    race = char.get("species") or char.get("race", "")
    if rest_type == "long" and "eladrin" in race.lower() and char.get("_choices", {}).get("eladrin_season"):
        opts.append({
            "kind": "eladrin_season",
            "label": "Change Eladrin season",
            "detail": "Changes which additional effect your Fey Step bonus action has.",
        })
    # Githyanki (MPMM)'s Astral Knowledge / Astral Elf's Astral Trance:
    # both grant "proficiency in one skill and with one weapon or tool
    # of your choice ... until the end of your next long rest" —
    # re-chosen every long rest, not a one-time pick.
    if rest_type == "long" and race in ("Githyanki (MPMM)", "Astral Elf") and \
            char.get("_choices", {}).get("astral_knowledge_skill"):
        trait_name = "Astral Knowledge" if race == "Githyanki (MPMM)" else "Astral Trance"
        opts.append({
            "kind": "astral_knowledge_swap",
            "label": f"Re-choose {trait_name}'s skill and weapon/tool proficiencies",
            "detail": "Changes which skill and which weapon or tool proficiency you currently "
                      "have from this trait.",
        })
    # Pact Boon 1-hour rituals are available on short rest (and long rest), since a short rest is defined as being at least an hour.
    pact_choice = char.get("_choices", {}).get("warlock_pact_boon", [])
    pact_name = pact_choice[0].lower() if pact_choice else ""
    if "blade" in pact_name:
        opts.append({
            "kind": "pact_blade_bond",
            "label": "Bond a magic weapon to become your pact weapon",
            "detail": "1-hour ritual, performable during a short rest. The weapon becomes "
                      "your pact weapon until you die, bond a different weapon, or break "
                      "the bond (also a 1-hour ritual).",
        })
    if "tome" in pact_name:
        opts.append({
            "kind": "pact_tome_replace",
            "label": "Replace a lost Book of Shadows",
            "detail": "1-hour ceremony, performable during a short or long rest. Destroys "
                      "the previous book.",
        })
    if "talisman" in pact_name:
        opts.append({
            "kind": "pact_talisman_replace",
            "label": "Replace a lost Talisman",
            "detail": "1-hour ceremony, performable during a short or long rest. Destroys "
                      "the previous amulet.",
        })
    # Whispers of the Dead (Rogue, Phantom) resets on either rest type.
    if char.get("_choices", {}).get("whispers_of_the_dead_prof"):
        opts.append({
            "kind": "whispers_dead_swap",
            "label": "Channel a different Whispers of the Dead proficiency",
            "detail": "Changes which skill or tool proficiency you currently have from this feature.",
        })
    if rest_type == "long" and char.get("_choices", {}).get("lunar_phase"):
        opts.append({
            "kind": "lunar_phase_swap",
            "label": "Change your Lunar Embodiment phase",
            "detail": "Choose Full Moon, New Moon, or Crescent Moon.",
        })
    return opts


def _has_trait(char: dict, name: str) -> bool:
    """The character's race has this trait (its traits start with their name)."""
    from dnd_app.data.races import race_traits_for
    return any(str(t).startswith(name) for t in race_traits_for(char))


def hit_die_heal(char: dict, sides: int, roll: int, rng=None) -> tuple:
    """One Hit Die spent, for both apps (a rest's dice, the Spend button):
    (the roll as it counts, the HP it heals) -- the roll plus your CON
    modifier, never below 0, and what changes that:
      Black Blood Healing        (Verdan) a 1 or 2 is rolled again, once
      Durable                    the roll is at least twice your CON modifier (min 2)
      Dwarven Fortitude          at least 1 HP
      Vigor of the Hill Giant    + your CON modifier and proficiency bonus
      Periapt of Wound Closure   (attuned) the hit points it restores, doubled
    rng: what rolls a die again (the random module unless a test gives one)."""
    import random as _random
    con = ability_mod(char, "CON")
    feats = char.get("feats", [])
    if roll <= 2 and _has_trait(char, "Black Blood Healing"):
        roll = (rng or _random).randint(1, sides)
    if "Durable" in feats:
        roll = max(roll, 2 * con, 2)
    heal = max(0, roll + con)
    if "Dwarven Fortitude" in feats:
        heal = max(heal, 1)
    if "Vigor of the Hill Giant" in feats:
        from dnd_app.core.calculator import get_prof_bonus
        heal += con + get_prof_bonus(char)
    if "Periapt of Wound Closure" in char.get("attuned_items", []):
        heal *= 2
    return roll, heal


def hit_die_notes(char: dict) -> list:
    """What changes this character's Hit Dice (hit_die_heal), in words, for
    the rest dialogs: ["Durable: each die counts as at least 4", ...]."""
    con = ability_mod(char, "CON")
    feats = char.get("feats", [])
    notes = []
    if _has_trait(char, "Black Blood Healing"):
        notes.append("Black Blood Healing: a 1 or 2 is rolled again")
    if "Durable" in feats:
        notes.append(f"Durable: each die counts as at least {max(2 * con, 2)}")
    if "Dwarven Fortitude" in feats:
        notes.append("Dwarven Fortitude: at least 1 HP each")
    if "Vigor of the Hill Giant" in feats:
        from dnd_app.core.calculator import get_prof_bonus
        notes.append(f"Vigor of the Hill Giant: +{con + get_prof_bonus(char)} each")
    if "Periapt of Wound Closure" in char.get("attuned_items", []):
        notes.append("Periapt of Wound Closure: doubled")
    return notes


def _celestial_resilience(char: dict) -> str:
    lvl = class_levels(char).get("Warlock", 0)
    cha = ability_mod(char, "CHA")
    return (f"When you finish the rest, you gain {max(0, lvl + cha)} temporary hit points, and up to five "
            f"creatures you can see gain {max(0, lvl // 2 + cha)} each.")


# ── What a character can do on a rest, besides what it gives back ─────────
# The class features' own (their descriptions here are short summaries,
# so these are written out from the books): feature name -> [(the rests
# it's on, what you can do)]. "both" = a short or a long rest; the text can
# be a function of the character, for its numbers.
_CLASS_REST_ACTIVITIES = {
    "Song of Rest": [("short", "Perform during the rest: anyone friendly who hears it (you too) and spends "
                               "Hit Dice at its end regains an extra 1d6 HP (1d8 at 9th level, 1d10 at "
                               "13th, 1d12 at 17th).")],
    "Hearth of Moonlight and Shadow": [("both", "At the start of the rest, touch a point to make an invisible "
                                                "30-foot-radius sphere: inside it you and your allies get +5 to "
                                                "Stealth and Perception checks, and light from open flames can't "
                                                "be seen from outside. It ends with the rest, or when you leave it.")],
    "Walker in Dreams": [("short", "When you finish the rest, cast Dream (as the messenger), Scrying or "
                                   "Teleportation Circle (to where you last finished a long rest, on this "
                                   "plane) without a spell slot or material components. Once a long rest.")],
    "Star Map": [("both", "If you've lost your star map, a 1-hour ceremony during the rest makes a new one "
                          "(the old one is destroyed).")],
    "Cosmic Omen": [("long", "When you finish the rest, consult your star map and roll a die for your omen "
                             "until your next long rest: even is Weal (your reaction adds a d6 to a roll), "
                             "odd is Woe (it takes a d6 off).")],
    "Blessing of the Forge": [("long", "At the end of the rest, touch a nonmagical suit of armour or a simple "
                                       "or martial weapon: until the end of your next long rest it's a +1 "
                                       "magic item (+1 AC, or +1 to attack and damage rolls).")],
    "Infuse Item": [("long", "When you finish the rest, touch nonmagical objects and infuse them, up to "
                             "your number of infused items (the Infusions tab).")],
    "Spell-Storing Item": [("long", "When you finish the rest, store a 1st- or 2nd-level artificer spell "
                                    "with a casting time of 1 action in a weapon or spellcasting focus you "
                                    "touch (uses: twice your INT modifier, at least 2).")],
    "Experimental Elixir": [("long", "When you finish the rest, with alchemist's supplies on you, produce an "
                                     "experimental elixir in an empty flask you touch (two at 6th level, three "
                                     "at 15th): roll a d6 for each one's effect.")],
    "The Right Tool for the Job": [("both", "With thieves' or artisan's tools in hand, make one set of "
                                            "artisan's tools: an hour's work, which can be done during the "
                                            "rest. The last set you made vanishes.")],
    "Steel Defender": [("long", "At the end of the rest, with smith's tools, make a new steel defender "
                                "(the old one, if any, dies).")],
    "Weapon Bond": [("short", "Bond with a weapon (up to two): a 1-hour ritual, which can be done during "
                              "a short rest.")],
    "Rune Carver": [("long", "When you finish the rest, inscribe each rune you know on a different weapon, "
                             "armour, shield, piece of jewellery or other thing you wear or hold, until "
                             "your next long rest.")],
    "Ranger's Companion": [("long", "If your companion is a primal beast, you can summon a different one "
                                    "when you finish the rest (the old one vanishes).")],
    "Death's Friend": [("long", "If you have no soul trinkets, one appears in your hand when you finish "
                                "the rest.")],
    "Hex Warrior": [("long", "Whenever you finish a long rest, touch a weapon you're proficient with that "
                             "isn't two-handed: you use CHA for its attack and damage rolls (any pact "
                             "weapon, too).")],
    "Genie's Vessel": [("both", "If your vessel is lost or destroyed, a 1-hour ceremony during the rest gets "
                                "you a new one from your patron (the old one is destroyed).")],
    "Celestial Resilience": [("both", _celestial_resilience)],
    "Master Scrivener": [("long", "When you finish the rest, touch your Wizardly Quill to blank paper to copy "
                                  "a 1st- or 2nd-level spell (1 action to cast) from your Awakened Spellbook, "
                                  "within 5 feet, onto a scroll. It's cast a level higher, and lasts until "
                                  "you use it or finish your next long rest.")],
    "Mutagencraft": [("both", "When you finish the rest, concoct mutagens from the formulas you know "
                              "(more as your level grows).")],
}

# Invocations' own (a warlock's chosen ones)
_INVOCATION_REST_ACTIVITIES = {
    "Aspect of the Moon": [("long", "You don't need to sleep: all 8 hours can be light activity, such as "
                                    "reading your Book of Shadows and keeping watch.")],
}

# the features already offered as an option to tick (rest_options): not
# listed again
_OPTION_SOURCES = {
    "arcane_recovery": ("Arcane Recovery",), "natural_recovery": ("Natural Recovery",),
    "pact_blade_bond": ("Pact of the Blade", "Pact Boon"), "pact_tome_replace": ("Pact of the Tome",),
    "pact_talisman_replace": ("Pact of the Talisman",), "eladrin_season": ("Fey Step", "Eladrin"),
    "whispers_dead_swap": ("Whispers of the Dead",), "lunar_phase_swap": ("Lunar",),
    "armorer_model": ("Armor Model", "Arcane Armor"), "astral_knowledge_swap": ("Astral Knowledge", "Astral Trance"),
}

# what the Hit Dice already do for you (hit_die_heal): not listed again
_APPLIED_ON_HIT_DICE = ("Black Blood Healing", "Vigor of the Hill Giant", "Durable", "Dwarven Fortitude",
                        "Periapt of Wound Closure")

_REST_WORDS = r"(short or long|short/long|short|long|sr|lr) rest"
# what makes a sentence about a rest something you do on it: you can, may
# or must do something, or choose
_YOU_DO = r"\byou (?:can|may|must)\b(?!['’]t|not)|\bchoose\b|\byour choice\b|\byou spend\b"


def _rest_sentences(text: str, rest_type: str) -> list:
    """The sentences in a rules text that say what you can do on `rest_type`
    ("When you finish a long rest, you can...", "During a short rest...",
    "As part of a short rest...", "Whenever you finish a long rest, choose...",
    how a rest goes for you: "you can finish a long rest in 4 hours"), not the
    ones that only say when a use comes back."""
    import re as _re
    # (pattern, whether what follows it in the clause must be something you do)
    pats = [
        (rf"\b(?:when|whenever|after|once) you finish (?:a|your|each) {_REST_WORDS}\b", True),
        (rf"\b(?:on|upon) finishing (?:a|your) {_REST_WORDS}\b", True),
        (rf"\bat the end of (?:a|your|each) {_REST_WORDS}\b", True),
        (rf"\bafter each {_REST_WORDS}\b", True),
        (rf"(?<!before )\b(?:take|takes|taking) a {_REST_WORDS}\b", True),
        (rf"\b(?:as part of|during) (?:a|your) {_REST_WORDS}\b", False),
        (rf"\bspend(?:s|ing)? (?:a|one) {_REST_WORDS}\b", False),
        (rf"\bfinish a {_REST_WORDS} in \d+ hours\b", False),
    ]
    out = []
    for sentence in _re.split(r"(?<=[.!?])\s+", text or ""):
        low = sentence.strip().lower()
        for pat, needs_doing in pats:
            m = _re.search(pat, low)
            if not m:
                continue
            if needs_doing and not _re.search(_YOU_DO, _re.split(r"[;.]", low[m.end():])[0]):
                continue
            which = m.group(1)
            if which not in ("short or long", "short/long") and not which.startswith(rest_type[0]):
                continue        # the other rest (the sentence may name both)
            # (on its own, without the text around it: no "Additionally, ...")
            s = _re.sub(r"^(?:additionally|in addition|also|however),\s*", "",
                        sentence.strip(), flags=_re.I).rstrip(" ;,")
            out.append(s[:1].upper() + s[1:] + ("" if s[-1:] in ".!?" else "."))
            break
    return out


def _trait_parts(trait: str) -> tuple:
    """A race trait's (name, text): "Cunning Artisan – as part of..." ->
    ("Cunning Artisan", "as part of..."); ("", trait) if it has no name."""
    import re as _re
    m = _re.match(r"\s*([^–:;(]{2,48}?)\s*(?:–|:| - )\s*(.+)$", trait, _re.S)
    return (m.group(1).strip(), m.group(2)) if m else ("", trait)


def rest_activities(char: dict, rest_type: str) -> list:
    """Everything this character can do on a short or long rest, besides
    what it gives back (the preview) and what can be ticked to do now
    (rest_options) -- for both apps' rest dialogs. [{"source", "text"}]:
      1. their class features' and invocations' (_CLASS_REST_ACTIVITIES...)
      2. what their feats, race and subrace traits and magic items' own
         texts say they can do on it (a Chef's food, a Deck of Oracles'
         omen, a warforged's Sentry's Rest...)
      3. the rules everyone has: attuning to a magic item (a short rest
         focused on it), ending an attunement, identifying an item"""
    out, seen = [], set()

    def add(source, text):
        if (source, text) not in seen:
            seen.add((source, text)); out.append({"source": source, "text": text})

    def add_catalogued(source, entries):
        for which, text in entries:
            if which in ("both", rest_type):
                add(source, text(char) if callable(text) else text)

    covered = [w for kind in (o["kind"] for o in rest_options(char, rest_type))
               for w in _OPTION_SOURCES.get(kind, ())]
    skip = lambda name: any(w in name for w in covered) or any(w in name for w in _APPLIED_ON_HIT_DICE)

    # class features, invocations, and the optional class features this
    # table uses (Tasha's Cantrip Formulas, Deft Explorer's Tireless)
    from dnd_app.data.class_features import get_class_features
    for cls, names in get_class_features(char).items():
        for name in names:
            if not skip(name):
                add_catalogued(name, _CLASS_REST_ACTIVITIES.get(name, ()))
    for inv in char.get("eldritch_invocations", []):
        for name, entries in _INVOCATION_REST_ACTIVITIES.items():
            if str(inv).startswith(name):
                add_catalogued(name, entries)
    levels = class_levels(char)
    rules = char.get("optional_rules", {})
    if rules.get("cantrip_formulas") and levels.get("Wizard", 0) >= 3:
        add_catalogued("Cantrip Formulas", [("long", "When you finish the rest, replace one wizard cantrip "
                                                     "you know with another from the wizard spell list.")])
    if levels.get("Ranger", 0) >= 10:
        from dnd_app.core.actions import _optional_feature_enabled
        if _optional_feature_enabled(char, "Deft Explorer"):
            add_catalogued("Tireless", [("short", "When you finish the rest, take a level of exhaustion "
                                                  "off, if you have any.")])

    # feats: their description, or the feat list's own summary
    from dnd_app.data.feature_tooltips import FEATURE_DESCS
    from dnd_app.data.feats import get_feat
    for feat in char.get("feats", []):
        if skip(feat):
            continue
        text = FEATURE_DESCS.get(feat) or (get_feat(feat) or {}).get("special", "")
        for sentence in _rest_sentences(text, rest_type):
            add(f"{feat} (feat)", sentence)

    # race and subrace traits (a subrace's are "Name (+X 2; Trait: text; ...)")
    from dnd_app.data.races import race_traits_for, RACE_DICT
    traits = [str(t) for t in race_traits_for(char)]
    race = char.get("species") or char.get("race", "")
    sub = char.get("subrace") or ""
    sub_str = next((s for s in RACE_DICT.get(race, {}).get("subraces", [])
                    if sub and s.split("(")[0].strip() == sub), "")
    if "(" in sub_str:
        traits += [p.strip() for p in sub_str[sub_str.find("(") + 1:sub_str.rfind(")")].split(";")[1:]]
    for trait in traits:
        name, text = _trait_parts(trait)
        if skip(name or trait):
            continue
        if name == "Trance" and rest_type == "long" and "rest" not in text.lower():
            add("Trance", "Meditate for 4 hours instead of sleeping, aware of your surroundings (the "
                          "rest still takes 8 hours).")
        # a trait is a run of clauses: each one on its own
        for clause in text.split(";"):
            for sentence in _rest_sentences(clause.strip(), rest_type):
                add(name or "Your race", sentence)

    # the magic items you have
    from dnd_app.data.magic_items import ALL_MAGIC_ITEMS
    owned = {m.get("name") for m in char.get("magic_items", [])}
    for item in ALL_MAGIC_ITEMS:
        if item["name"] in owned and not skip(item["name"]):
            for sentence in _rest_sentences(item.get("desc", ""), rest_type):
                add(item["name"], sentence)

    if rest_type == "short":
        from dnd_app.core.magic_items import attunement_limit
        limit = attunement_limit(char)
        attuned = set(char.get("attuned_items", []))
        needing = [m["name"] for m in ALL_MAGIC_ITEMS
                   if m["name"] in owned and m.get("attunement") and m["name"] not in attuned]
        if needing and len(attuned) < limit:
            add("Attunement", f"Spend the rest focused on one item that needs attuning, touching it, to "
                              f"attune to it: {', '.join(sorted(needing))} (you have {limit - len(attuned)} "
                              f"of {limit} attunement slots free).")
        if attuned:
            add("Attunement", "Spend the rest focused on an item you're attuned to, to end its attunement.")
        add("Identify an item", "Spend the rest focused on one magic item, touching it, to learn its "
                                "properties and how to use them.")
    return out


def rest_preview_lines(rest_type: str, preview: dict, dice_below: bool = False) -> list:
    """The lines a rest preview shows (HP, hit dice, slots, resources, what
    fades), for both apps' rest dialogs. dice_below: the dialog has its own
    hit dice picker, under the preview (the desktop's Rest dialog)."""
    lines = []
    if rest_type == "short":
        if preview["hp"] >= preview["max_hp"]:
            lines.append(f"HP: already full ({preview['max_hp']})")
        elif preview["hit_dice_available"] > 0:
            lines.append(f"HP: {preview['hp']}/{preview['max_hp']}  —  "
                          f"{preview['hit_dice_available']} hit dice available, "
                          + ("spend them below" if dice_below else
                             "you'll choose how many to spend next"))
        else:
            lines.append(f"HP: {preview['hp']}/{preview['max_hp']}  —  no hit dice remaining")
    else:
        heal = preview["max_hp"] - preview["hp"]
        if heal > 0:
            lines.append(f"HP: {preview['hp']} → {preview['max_hp']} (full heal, +{heal})")
        else:
            lines.append(f"HP: already full ({preview['max_hp']})")
        if preview["temp_hp"] > 0:
            lines.append(f"Temporary HP: {preview['temp_hp']} → 0 (lost)")
        if preview["hit_dice_restored"] > 0:
            lines.append(f"Hit Dice: +{preview['hit_dice_restored']} restored")
        if preview["exhaustion"] > 0:
            lines.append(f"Exhaustion: level {preview['exhaustion']} → {preview['exhaustion_after']}")
        if preview["death_reset"]:
            lines.append("Death saves: cleared")
        if preview["was_concentrating"]:
            lines.append(f"Concentration on {preview['was_concentrating']}: will end")

    if preview.get("slot_levels_reset"):
        levels = ", ".join(f"Lv{lvl}" for lvl in preview["slot_levels_reset"])
        lines.append(f"Spell slots restored: {levels}")
    if preview.get("pact_restore"):
        lines.append("Pact Magic slots: restored")
    if preview.get("resets"):
        lines.append("")
        lines.append("Resources restored:")
        lines.extend(f"  • {name}: {cur} → {tgt}" for name, cur, tgt in preview["resets"])
    if preview.get("fading"):
        lines.append("")
        lines.append("Will fade/end:")
        lines.extend(f"  • {n}" for n in preview["fading"])
    return lines
