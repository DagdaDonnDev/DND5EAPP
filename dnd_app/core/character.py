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
        "edition": "2014",          # "2014" or "2024"
        "alignment": "True Neutral",
        "experience": 0,
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
        "notes": "",
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


def set_subclass(char: dict, class_name: str, subclass: str) -> None:
    entry = get_class_entry(char, class_name)
    if entry:
        entry["subclass"] = clean_subclass_name(subclass)


def add_feat(char: dict, feat_name: str) -> None:
    if feat_name not in char["feats"]:
        char["feats"].append(feat_name)


def remove_feat(char: dict, feat_name: str) -> None:
    char["feats"] = [f for f in char["feats"] if f != feat_name]


def set_skill_prof(char: dict, skill: str, level: int) -> None:
    """0=none, 1=half, 2=proficient, 3=expertise"""
    char["skills"][skill] = max(0, min(3, level))


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
    # "SR"/"SR/LR" resource-reset loop below -- it used to be tracked by
    # a separate ad hoc counter with its own explicit reset in both this
    # function and long_rest(), now retired in favor of the shared
    # char["resources"] entry (see the reset="SR/LR" note on its
    # definition in classes.py/classes_2024.py).
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
