"""
Apply magic item effects from data/magic_items.py onto character state.
All item definitions and effect payloads live in the data layer.

Author: Ethan O'Brien
Date: 2026-08-20
"""

from __future__ import annotations

from dnd_app.data.magic_items import get_item_effect, get_magic_item
import re as _re


SPELLCASTING_CLASSES = ("Bard", "Cleric", "Druid", "Paladin", "Ranger",
                         "Sorcerer", "Warlock", "Wizard", "Artificer")
CLASS_NAMES = ("Artificer", "Barbarian", "Bard", "Blood Hunter", "Cleric",
               "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue",
               "Sorcerer", "Warlock", "Wizard")

# The 6 classic DMG "manual"/"tome" magic items: studying one for 48 hours
# over 6 days or fewer permanently raises the named ability score by 2
# (PHB p.140 rule: no hard 20 cap on this kind of magical increase). This
# is a one-time consumption effect on char["abilities"] directly, not an
# equip-based MAGIC_ITEM_EFFECTS entry -- the book is used up and removed
# from magic_items, not worn/attuned, so the normal reapply-on-refresh
# effect model doesn't fit it.
ABILITY_SCORE_MANUALS = {
    "Manual of Bodily Health": "CON",
    "Manual of Gainful Exercise": "STR",
    "Manual of Quickness of Action": "DEX",
    "Tome of Clear Thought": "INT",
    "Tome of Leadership and Influence": "CHA",
    "Tome of Understanding": "WIS",
}


def attunement_prereq_met(char: dict, item_name: str) -> tuple[bool, str]:
    """Checks a magic item's 'requires attunement by X' restriction (a
    class, race/species, or alignment, or the catch-all 'a spellcaster')
    against the character's real data — same shape and same reasoning as
    core/choices.py's feat_prereq_met(). Returns (met, reason_if_not_met);
    complex/narrative requirements this can't parse (e.g. "a creature that
    has slain a dragon") are left unenforced, same as feat_prereq_met
    leaves campaign-specific feat prereqs unenforced — the requirement
    still reads in the item's own description for the player/DM to
    adjudicate by hand."""
    item = get_magic_item(item_name)
    if not item:
        return True, ""
    req = item.get("attune_req", "")
    if not req:
        return True, ""
    if not char.get("optional_rules", {}).get("attunement_prereqs", True):
        return True, ""
    req_low = req.lower()

    if "spellcaster" in req_low:
        classes_held = {c.get("class", "") for c in char.get("classes", []) if c.get("level", 0) > 0}
        if any(c in SPELLCASTING_CLASSES for c in classes_held):
            return True, ""
        return False, req

    matched_classes = [c for c in CLASS_NAMES if c.lower() in req_low]
    if matched_classes:
        classes_held = {c.get("class", "") for c in char.get("classes", []) if c.get("level", 0) > 0}
        if any(c in classes_held for c in matched_classes):
            return True, ""
        return False, req

    # Single-word alignment gates ("a good creature", "a lawful creature").
    # Skip compound/negated phrasing ("neither good nor evil", "non-evil")
    # this simple check would get wrong.
    if "neither" not in req_low and "non-" not in req_low:
        align_words = [w for w in ("good", "evil", "lawful", "chaotic") if w in req_low]
        if len(align_words) == 1:
            alignment = char.get("alignment", "").lower()
            if align_words[0] in alignment:
                return True, ""
            return False, req

    race = (char.get("species") or char.get("race", "")).lower()
    subrace = char.get("subrace", "").lower()
    RACE_WORDS = ("warforged", "dwarf", "elf", "gnome", "halfling", "human",
                  "dragonborn", "tiefling", "half-orc", "half-elf", "orc",
                  "goliath", "tabaxi", "aasimar", "genasi", "tortle", "kenku",
                  "satyr", "triton", "firbolg", "fairy", "harengon",
                  "changeling", "shifter", "kalashtar", "goblin", "hobgoblin",
                  "bugbear", "lizardfolk", "yuan-ti", "centaur", "loxodon",
                  "minotaur", "githyanki", "githzerai", "plasmoid",
                  "thri-kreen", "autognome", "giff", "hexblood", "owlin",
                  "vedalken", "verdan", "reborn", "locathah")
    for w in RACE_WORDS:
        if w not in req_low:
            continue
        if w in race or w in subrace:
            return True, ""
        # Only hard-fail when the requirement IS just that race (e.g. "a
        # warforged") — a race word appearing inside a more elaborate
        # phrase ("a creature with the Mark of Warding") isn't something
        # this parser actually understood, so it shouldn't block.
        if req_low.strip() in (w, f"a {w}", f"an {w}"):
            return False, req
        break

    return True, ""


def parse_magic_suffix(name: str) -> tuple[str, int]:
    """
    Split 'Longsword +1' -> ('Longsword', 1). Returns (name, 0) if no suffix.
    Recognizes a trailing ' +1', ' +2', or ' +3'.
    """
    m = _re.match(r'^(.*) \+([123])$', name.strip())
    if m:
        return m.group(1).strip(), int(m.group(2))
    return name, 0


def parse_material_prefix(name: str) -> tuple[str, str]:
    """
    Split 'Silvered Dagger' -> ('Dagger', 'Silvered'), or
    'Adamantine Longsword' -> ('Longsword', 'Adamantine').
    Returns (name, "") if no recognized prefix.

    Needed because the weapon-name lookup only recognizes the
    "+1"/"+2"/"+3" suffix on its own — without stripping this prefix
    first, "Silvered X"/"Adamantine X" falls through to the generic
    named-magic-weapon fallback and gets corrupted stats — e.g. a
    Silvered Dagger would render with the fallback's flat 1d8 slashing
    damage and no properties, instead of the real dagger's 1d4
    piercing with Finesse/Light/Thrown.
    """
    stripped = name.strip()
    for prefix in ("Adamantine ", "Silvered "):
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip(), prefix.strip()
    return name, ""


def _active_item_names(char: dict) -> list[str]:
    """Items that apply mechanical effects: attuned items must ALSO be
    equipped (not just sitting attuned in a backpack — the attunement
    toggle itself never requires "equipped" either), and non-attunement
    items just need to be equipped."""
    names: list[str] = []
    attuned = set(char.get("attuned_items", []))
    equipped_lookup = {}
    for entry in char.get("magic_items", []):
        if isinstance(entry, dict):
            equipped_lookup[entry.get("name", "")] = entry.get("equipped", False)

    for n in attuned:
        if n and n not in names and equipped_lookup.get(n, False):
            names.append(n)

    for entry in char.get("magic_items", []):
        if isinstance(entry, str):
            name = entry
            entry = {"name": name, "equipped": True, "attunement": False}
        else:
            name = entry.get("name", "")
        if not name or name in names:
            continue
        if not entry.get("equipped", False):
            continue
        catalog = get_magic_item(name)
        requires_attune = bool(catalog.get("attunement")) if catalog else False
        if requires_attune:
            if name in attuned:
                names.append(name)
        else:
            names.append(name)
    return names


def reset_magic_item_modifiers(char: dict) -> None:
    """Clear transient modifiers before reapplying item effects."""
    char["ability_overrides"] = {}
    char["skill_advantages"] = []
    char["skill_disadvantages"] = []
    char["_skill_advantage_sources"] = {}     # {skill: [reason, ...]}
    char["_skill_disadvantage_sources"] = {}  # {skill: [reason, ...]}
    char["item_granted_spells"] = []
    char["item_spell_uses"] = {}
    char["item_actions"] = []
    char["item_granted_spell_details"] = []
    char["spell_dc_bonus"] = 0
    char["spell_attack_bonus"] = 0
    char["magic_ac_bonus"] = 0
    char["magic_save_bonus"] = 0
    char["magic_speed_bonus"] = 0
    char["_blackrazor_spellcasting"] = False
    char["_named_weapon_bonuses"] = {}  # {item_name: bonus_value}
    # Source-tracked breakdowns, used to build tooltips
    char["_ac_bonus_sources"] = []        # [(item_name, value), ...]
    char["_save_bonus_sources"] = []      # [(item_name, value), ...]
    char["_speed_bonus_sources"] = []     # [(item_name, value), ...]
    # Resistances / immunities granted by equipped+attuned items
    char["damage_resistances"] = []       # [(damage_type, item_name), ...]
    char["damage_immunities"] = []        # [(damage_type, item_name), ...]
    char["condition_immunities_magic"] = []  # [(condition, item_name), ...]
    char["advantage_saves_magic"] = []    # [(ability_or_'all', item_name), ...]
    char["initiative_advantage_magic"] = []  # [item_name, ...]
    # Additive ability-score/proficiency bonuses (Ioun Stones) — kept separate
    # from ability_overrides (a floor, e.g. Belt of Giant Strength) and from
    # char["ability_bonuses"] (owned/rebuilt by builder.py for racial/ASI
    # bonuses) so applying or removing an item can never clobber either.
    char["magic_ability_bonuses"] = {}    # {"STR": 2, ...}
    char["magic_prof_bonus"] = 0
    char["magic_senses"] = {}     # {"darkvision": 60, ...} from equipped/attuned items
    char["magic_hp_max_bonus"] = 0


def apply_magic_item_effect(char: dict, item_name: str) -> None:
    """Apply a single item's effect to char (lookup from data)."""
    effect = get_item_effect(item_name)
    if not effect:
        return

    # An item can grant multiple simultaneous effects (e.g. an ability score
    # bonus AND a damage immunity) — represented as a list of effect dicts.
    if isinstance(effect, list):
        for sub_effect in effect:
            _apply_single_effect(char, item_name, sub_effect)
        return

    _apply_single_effect(char, item_name, effect)


def _apply_single_effect(char: dict, item_name: str, effect: dict) -> None:
    etype = effect["type"]
    if etype == "set_ability":
        ab = effect["ability"]
        val = effect["value"]
        overrides = char.setdefault("ability_overrides", {})
        current = overrides.get(ab, 0)
        overrides[ab] = max(current, val) if current else val

    elif etype == "skill_advantage":
        skills = char.setdefault("skill_advantages", [])
        sk = effect["skill"]
        if sk not in skills:
            skills.append(sk)
        char.setdefault("_skill_advantage_sources", {}).setdefault(sk, []).append(item_name)

    elif etype == "skill_disadvantage":
        skills = char.setdefault("skill_disadvantages", [])
        sk = effect["skill"]
        if sk not in skills:
            skills.append(sk)
        char.setdefault("_skill_disadvantage_sources", {}).setdefault(sk, []).append(item_name)

    elif etype == "grant_spell":
        # NOTE: item-granted spells are intentionally NOT added to spells_known —
        # they appear only in the Action/Bonus Action/Reaction quick-access tabs,
        # since they're cast via the item, not part of the character's own
        # spell list or spellbook.
        spell = effect["spell"]
        granted = char.setdefault("item_granted_spells", [])
        if spell not in granted:
            granted.append(spell)
        uses = effect.get("uses", 0)
        if uses:
            char.setdefault("item_spell_uses", {})[spell] = uses
        # Track per-item metadata so the action tabs can build a proper row
        char.setdefault("item_granted_spell_details", []).append({
            "spell": spell,
            "source": item_name,
            "uses": uses,
            "recharge": effect.get("recharge", "dawn"),
            "action_type": effect.get("action_type", "Action"),
            "dc": effect.get("dc"),
        })

    elif etype == "grant_action":
        actions = char.setdefault("item_actions", [])
        actions.append({
            "name": effect.get("action", "Special"),
            "source": item_name,
            "description": effect.get("description", ""),
            "action_type": effect.get("action_type", "Passive"),
        })
        if effect.get("spellcasting_weapon"):
            char["_blackrazor_spellcasting"] = True

    elif etype == "spell_dc_bonus":
        char["spell_dc_bonus"] = char.get("spell_dc_bonus", 0) + effect.get("value", 0)
        # Some items (Rod of Pact Keeper, Wand of War Mage) also boost spell attack
        atk = effect.get("atk_bonus", 0)
        if atk:
            char["spell_attack_bonus"] = char.get("spell_attack_bonus", 0) + atk

    elif etype == "spell_attack_bonus":
        char["spell_attack_bonus"] = char.get("spell_attack_bonus", 0) + effect.get("value", 0)

    elif etype == "ac_bonus":
        val = effect.get("value", 0)
        char["magic_ac_bonus"] = char.get("magic_ac_bonus", 0) + val
        char.setdefault("_ac_bonus_sources", []).append((item_name, val))
        # Some items give both AC and save bonus (Cloak/Ring of Protection)
        sb = effect.get("save_bonus", 0)
        if sb:
            char["magic_save_bonus"] = char.get("magic_save_bonus", 0) + sb
            char.setdefault("_save_bonus_sources", []).append((item_name, sb))

    elif etype == "save_bonus":
        val = effect.get("value", 0)
        char["magic_save_bonus"] = char.get("magic_save_bonus", 0) + val
        char.setdefault("_save_bonus_sources", []).append((item_name, val))

    elif etype == "weapon_damage_bonus":
        char.setdefault("_weapon_damage_bonuses", []).append({
            "source": item_name,
            "weapon_type": effect.get("weapon_type", ""),
            "value": effect.get("value", 0),
        })

    elif etype == "weapon_attack_bonus":
        # A named magic weapon grants +N to attack AND damage when equipped.
        # Store keyed by item_name so the weapon row can look it up.
        val = effect.get("value", 0)
        if val > 0:
            char.setdefault("_named_weapon_bonuses", {})[item_name] = val

    elif etype == "resistance":
        dmg_type = effect.get("damage_type", "")
        char.setdefault("damage_resistances", []).append((dmg_type, item_name))

    elif etype == "immunity":
        dmg_type = effect.get("damage_type", "")
        char.setdefault("damage_immunities", []).append((dmg_type, item_name))

    elif etype == "resistance_choice":
        # The specific damage type is fixed per-copy of the item (set when
        # it was created/found), represented here as a one-time player
        # choice rather than a guessed default. No resistance is applied
        # until the player actually picks one via the item's row in the
        # Gear tab.
        picks = char.get("_choices", {}).get(f"item_dmgtype_{item_name}", [])
        if picks:
            char.setdefault("damage_resistances", []).append((picks[0].lower(), item_name))

    elif etype == "condition_immunity":
        cond = effect.get("condition", "")
        char.setdefault("condition_immunities_magic", []).append((cond, item_name))

    elif etype == "speed_bonus":
        val = effect.get("value", 0)
        char["magic_speed_bonus"] = char.get("magic_speed_bonus", 0) + val
        char.setdefault("_speed_bonus_sources", []).append((item_name, val))

    elif etype == "min_speed":
        # "Your speed becomes X, unless it's already higher" (Boots of Striding, etc.)
        floor = effect.get("value", 0)
        base_speed = char.get("speed", 30)
        if base_speed < floor:
            bump = floor - base_speed
            char["magic_speed_bonus"] = char.get("magic_speed_bonus", 0) + bump
            char.setdefault("_speed_bonus_sources", []).append((item_name, bump))

    elif etype == "advantage_save":
        ability = effect.get("ability", "all")
        char.setdefault("advantage_saves_magic", []).append((ability, item_name))

    elif etype == "initiative_advantage":
        lst = char.setdefault("initiative_advantage_magic", [])
        if item_name not in lst:
            lst.append(item_name)

    elif etype == "ability_bonus":
        # Additive, e.g. Ioun Stones — stacks on top of the character's own
        # score, unlike set_ability's "becomes X unless already higher".
        # Ioun Stones' real text caps the result ("...to a maximum of 20"),
        # unlike set_ability items (Belt of Giant Strength etc.), which
        # deliberately go higher — so the cap is per-effect, not global.
        ab = effect["ability"]
        val = effect.get("value", 0)
        cap = effect.get("cap")
        if cap is not None:
            current = char["abilities"].get(ab, 10) + char.get("ability_bonuses", {}).get(ab, 0)
            val = max(0, min(val, cap - current))
        bonuses = char.setdefault("magic_ability_bonuses", {})
        bonuses[ab] = bonuses.get(ab, 0) + val

    elif etype == "prof_bonus":
        char["magic_prof_bonus"] = char.get("magic_prof_bonus", 0) + effect.get("value", 0)

    elif etype == "senses":
        senses = char.setdefault("magic_senses", {})
        sense = effect["sense"]
        senses[sense] = max(senses.get(sense, 0), effect.get("value", 0))

    elif etype == "hp_max_bonus":
        formula = effect.get("formula")
        if formula == "10_plus_level":
            from .calculator import total_level
            val = 10 + total_level(char)
        elif formula == "per_level":
            from .calculator import total_level
            val = total_level(char)
        else:
            val = effect.get("value", 0)
        char["magic_hp_max_bonus"] = char.get("magic_hp_max_bonus", 0) + val


def apply_equipment_skill_effects(char: dict) -> None:
    """
    Apply baseline equipment rules that grant advantage/disadvantage on
    specific skills — distinct from magic item effects, since these come
    from mundane armor properties (PHB p.144: armor that imposes Stealth
    disadvantage does so for ANY wearer, not just magic armor).
    """
    from dnd_app.data.items import ARMOR_DICT

    armor_name = char.get("armor_worn", "No Armor")
    base_armor_name, _ = parse_magic_suffix(armor_name)
    armor = ARMOR_DICT.get(base_armor_name)
    if armor and armor.get("stealth"):
        dis = char.setdefault("skill_disadvantages", [])
        if "Stealth" not in dis:
            dis.append("Stealth")
        char.setdefault("_skill_disadvantage_sources", {}).setdefault("Stealth", []).append(
            f"{base_armor_name} (armor imposes Stealth disadvantage)"
        )


def _is_infusion_target_equipped(char: dict, target_item: str, infusion_name: str) -> bool:
    """Whether the specific item an infusion was applied to is actually
    equipped right now, using the correct mechanism for its slot type
    (weapon/armor/shield each track "equipped" completely differently)."""
    from dnd_app.data.classes import ARTIFICER_INFUSION_TARGETS
    target_type = ARTIFICER_INFUSION_TARGETS.get(infusion_name)
    if target_type == "weapon":
        return target_item in char.get("equipped_weapons", [])
    if target_type == "armor":
        return char.get("armor_worn", "No Armor") == target_item
    if target_type == "shield":
        return bool(char.get("shield", False))
    if target_type == "armor_or_shield":
        return (char.get("armor_worn", "No Armor") == target_item
                or bool(char.get("shield", False)))
    return True  # standalone infusions have no separate equip check


def sync_item_charges(char: dict) -> None:
    """
    Ensure every active item with a chargeable grant_spell effect has a
    tracked entry in char['item_charges']. Existing current values are
    preserved across refreshes (so spending charges sticks); only the max
    and recharge condition are kept in sync with the catalog.

    Also covers infusion-based charge items (Armor of Magical Strength,
    Mind Sharpener, Radiant Weapon, Repulsion Shield) — a completely
    separate data path from the catalog-based magic_items system since
    they enchant an existing equipment item rather than creating a
    standalone entry. Correctly requires the specific infused item to
    be equipped (not just the infusion being known/active), using each
    slot type's real equipped-status mechanism.
    """
    tracked = char.setdefault("item_charges", {})
    active = set(_active_item_names(char))

    for name in active:
        effect = get_item_effect(name)
        if not effect:
            continue
        effect_list = effect if isinstance(effect, list) else [effect]
        for sub in effect_list:
            # grant_spell: a single fixed spell with its own charge pool
            # (Wand of Fireballs). charges: a general charge pool for
            # items whose reference text describes multiple charge-
            # costed abilities that don't fit the single-spell
            # grant_spell model (Staff of Power, Blackstaff, etc.).
            if sub.get("type") not in ("grant_spell", "charges"):
                continue
            uses = sub.get("uses") if sub["type"] == "grant_spell" else sub.get("max", 0)
            if not uses:
                continue
            recharge = sub.get("recharge", "dawn")
            existing = tracked.get(name)
            if existing:
                existing["max"] = uses
                existing["recharge"] = recharge
                existing["current"] = min(existing.get("current", uses), uses)
            else:
                tracked[name] = {"current": uses, "max": uses, "recharge": recharge}

    from dnd_app.data.classes import ARTIFICER_INFUSION_CHARGES
    infusion_charge_keys = set()
    for inf in char.get("active_infusions", []):
        name = inf.get("infusion", "")
        charge_info = ARTIFICER_INFUSION_CHARGES.get(name)
        if not charge_info:
            continue
        target_item = inf.get("target_item")
        if not target_item or not _is_infusion_target_equipped(char, target_item, name):
            continue
        max_charges, recharge_dice, recharge_timing = charge_info
        key = f"{name} ({target_item})"
        infusion_charge_keys.add(key)
        existing = tracked.get(key)
        if existing:
            existing["max"] = max_charges
            existing["recharge"] = recharge_timing
            existing["current"] = min(existing.get("current", max_charges), max_charges)
        else:
            tracked[key] = {"current": max_charges, "max": max_charges, "recharge": recharge_timing}

    # Drop tracking for items no longer active, so removed/unattuned items
    # don't linger in the Other tab.
    for stale in [n for n in tracked if n not in active and n not in infusion_charge_keys]:
        del tracked[stale]


def apply_all_magic_item_effects(char: dict) -> None:
    """Reapply all magic item effects from attuned/equipped items."""
    reset_magic_item_modifiers(char)
    for name in _active_item_names(char):
        apply_magic_item_effect(char, name)
    apply_equipment_skill_effects(char)
    sync_item_charges(char)
    _apply_infusion_bonuses(char)


def _apply_infusion_bonuses(char: dict) -> None:
    """Apply the numerical bonus from standalone-target Artificer
    infusions (Enhanced Arcane Focus -> spell attack, Enhanced Defense/
    Repulsion Shield -> AC). Needed since the magic item catalog entries
    for them are flavor text only with no effects list, and unlike
    weapon infusions they don't get a "+N" name suffix to parse.
    Weapon-targeting infusions (Enhanced Weapon, Radiant Weapon,
    Repeating Shot, Returning Weapon) are handled separately at the
    point each weapon row is built, since their bonus is per-weapon,
    not global."""
    from .calculator import get_infusion_bonus, class_levels
    art_lvl = class_levels(char).get("Artificer", 0)
    for inf in char.get("active_infusions", []):
        name = inf.get("infusion", "")
        bonus = get_infusion_bonus(name, art_lvl)
        if not bonus:
            continue
        if name == "Enhanced Arcane Focus":
            char["spell_attack_bonus"] = char.get("spell_attack_bonus", 0) + bonus
        elif name in ("Enhanced Defense", "Repulsion Shield (+1)"):
            char["magic_ac_bonus"] = char.get("magic_ac_bonus", 0) + bonus


def concentration_save(char: dict, damage: int) -> tuple[bool, int]:
    """
    Roll concentration save after taking damage.
    Returns (maintained, roll_total).
    """
    import random
    from .calculator import get_saving_throw_bonus

    conc = char.get("concentration", {})
    if not conc or not conc.get("spell"):
        return True, 0

    dc = max(10, damage // 2)
    con_save = get_saving_throw_bonus(char, "CON")
    # War Caster: advantage on CON saves made to maintain concentration.
    if "War Caster" in char.get("feats", []):
        roll = max(random.randint(1, 20), random.randint(1, 20))
    else:
        roll = random.randint(1, 20)
    total = roll + con_save
    if total >= dc:
        return True, total
    conc["spell"] = None
    conc["since_round"] = 0
    return False, total


def start_concentration(char: dict, spell_name: str, *, round_num: int = 0) -> None:
    char.setdefault("concentration", {"spell": None, "since_round": 0})
    # concentrating on a new spell ends the old one, and its effect with it
    old = char["concentration"].get("spell")
    if old and old != spell_name:
        _end_concentration_effects(char, old)
    char["concentration"]["spell"] = spell_name
    char["concentration"]["since_round"] = round_num


def drop_concentration(char: dict) -> None:
    conc = char.setdefault("concentration", {"spell": None, "since_round": 0})
    if conc.get("spell"):
        _end_concentration_effects(char, conc["spell"])
    conc["spell"] = None
    conc["since_round"] = 0


def _end_concentration_effects(char: dict, spell_name: str) -> None:
    """The spell's concentration effects come off Active Effects (Divine
    Favor's extra radiant leaves the weapon rows when it ends)."""
    from dnd_app.core.effects import EFFECT_TABLE
    from dnd_app.core.spell_effects import effect_names
    ending = {n for n in effect_names(spell_name) if EFFECT_TABLE.get(n, {}).get("conc")}
    if ending:
        char["active_effects"] = [n for n in char.get("active_effects", []) if n not in ending]
        for n in ending:
            (char.get("effect_details") or {}).pop(n, None)


# ── Owned magic items: one entry per copy ──────────────────────────────
# Each copy you own is its own entry in char["magic_items"] with a short
# "uid", so two Manuals of Bodily Health are two books (each studied once)
# and removing one copy leaves the other. Only magic ammunition stacks,
# as a "qty" on a single entry.
import uuid as _uuid

_AMMO_RE = _re.compile(r"\b(ammunition|arrows?|bolts?|bullets?|needles?)\b", _re.I)


def is_magic_ammunition(name: str) -> bool:
    """+1 Ammunition, Arrow of Slaying, Walloping Ammunition... -- the
    magic items that come (and stack) by the handful."""
    catalog = get_magic_item(name) or {}
    return catalog.get("type") == "Weapon" and bool(_AMMO_RE.search(name or ""))


def owned_magic_items(char: dict) -> list[dict]:
    """char["magic_items"] as dicts, each with a uid and its own "attuned"
    flag. Older saves (plain names, no uids, attunement only in
    attuned_items) are upgraded in place; safe to call repeatedly.

      1. every entry becomes a dict (an old save might hold a bare name)
      2. every entry gets a uid if it hasn't one -- that's what the UIs
         use to say WHICH copy to equip/attune/study/remove
      3. attunement: attuned_items (names) is the source of truth, and
         only one copy of a name can be attuned. A copy keeps its
         "attuned" flag only if its name is still attuned and no earlier
         copy already has it; an attuned name with no flagged copy (an
         older save) is given to its first copy."""
    items = []
    for e in char.get("magic_items", []):
        if not isinstance(e, dict):
            e = {"name": str(e), "attunement": False, "equipped": True, "notes": ""}
        if not e.get("uid"):
            e["uid"] = _uuid.uuid4().hex[:10]
        items.append(e)
    char["magic_items"] = items
    # attunement belongs to one copy: keep a copy's flag only while its name
    # is attuned, then give any attuned name without a flagged copy to its
    # first copy
    attuned = set(char.get("attuned_items", []))
    flagged = set()
    for e in items:
        n = e.get("name", "")
        if e.get("attuned") and (n not in attuned or n in flagged):
            e["attuned"] = False
        if e.get("attuned"):
            flagged.add(n)
    for e in items:
        n = e.get("name", "")
        if n in attuned and n not in flagged:
            e["attuned"] = True
            flagged.add(n)
    return items


def find_magic_item(char: dict, uid: str) -> dict | None:
    return next((e for e in owned_magic_items(char) if e.get("uid") == uid), None)


def add_owned_magic_item(char: dict, name: str, qty: int = 1) -> dict:
    """Add a copy (or, for ammunition, `qty` more of an existing stack)."""
    items = owned_magic_items(char)
    if is_magic_ammunition(name):
        stack = next((e for e in items if e.get("name") == name), None)
        if stack:
            stack["qty"] = stack.get("qty", 1) + qty
            return stack
    entry = {"name": name, "attunement": False, "equipped": True, "notes": "",
             "uid": _uuid.uuid4().hex[:10]}
    if is_magic_ammunition(name):
        entry["qty"] = max(1, qty)
    items.append(entry)
    return entry


def _copies_left(char: dict, name: str) -> list[dict]:
    return [e for e in owned_magic_items(char) if e.get("name") == name]


def remove_owned_magic_item(char: dict, uid: str) -> dict | None:
    """Remove one copy. Returns it (None if not found). Attunement and the
    equipped-weapon/armor slot only go if no other copy keeps them."""
    entry = find_magic_item(char, uid)
    if not entry:
        return None
    char["magic_items"] = [e for e in char["magic_items"] if e.get("uid") != uid]
    name = entry.get("name", "")
    if entry.get("attuned"):
        attuned = char.get("attuned_items", [])
        while name in attuned:
            attuned.remove(name)
    if entry.get("equipped") and not any(e.get("equipped") for e in _copies_left(char, name)):
        _unequip_slot(char, name)
    return entry


def set_owned_magic_item_qty(char: dict, uid: str, qty: int):
    """Ammunition stacks: set how many; 0 removes the stack."""
    entry = find_magic_item(char, uid)
    if not entry:
        return
    if qty <= 0:
        remove_owned_magic_item(char, uid)
    else:
        entry["qty"] = qty


def _unequip_slot(char: dict, name: str):
    itype = (get_magic_item(name) or {}).get("type", "")
    if itype == "Weapon":
        wpns = char.get("equipped_weapons", [])
        if name in wpns:
            wpns.remove(name)
    elif itype == "Armor":
        if char.get("armor_worn") == name:
            char["armor_worn"] = "No Armor"
    elif itype == "Shield":
        char["shield"] = False


def set_owned_magic_item_equipped(char: dict, uid: str, on: bool):
    """Equip/unequip one copy, syncing equipped_weapons / armor_worn /
    shield (a weapon stays in hand while any copy of it is equipped)."""
    entry = find_magic_item(char, uid)
    if not entry:
        return
    entry["equipped"] = on
    name = entry.get("name", "")
    itype = (get_magic_item(name) or {}).get("type", "")
    if on:
        if itype == "Weapon":
            wpns = char.setdefault("equipped_weapons", [])
            if name not in wpns:
                wpns.append(name)
        elif itype == "Armor":
            char["armor_worn"] = name
        elif itype == "Shield":
            char["shield"] = True
    elif not any(e.get("equipped") for e in _copies_left(char, name)):
        _unequip_slot(char, name)


def attunement_limit(char: dict) -> int:
    from dnd_app.core.calculator import class_levels
    art_lvl = class_levels(char).get("Artificer", 0)
    limit = 6 if art_lvl >= 18 else 5 if art_lvl >= 14 else 4 if art_lvl >= 10 else 3
    if "Mystic Conflux" in char.get("feats", []):
        limit = max(limit, 4)
    return limit


def set_owned_magic_item_attuned(char: dict, uid: str, on: bool) -> str:
    """Attune/end attunement for one copy. Returns "" on success, else the
    reason it can't (you can't attune to two copies of the same item --
    XGtE p.136 -- plus the prerequisite and the attunement limit)."""
    entry = find_magic_item(char, uid)
    if not entry:
        return ""
    name = entry.get("name", "")
    attuned = char.setdefault("attuned_items", [])
    if on:
        if entry.get("attuned"):
            return ""
        if name in attuned:
            return f"You're already attuned to another {name} -- you can't attune to two of the same item."
        met, reason = attunement_prereq_met(char, name)
        if not met:
            return f"{name} requires attunement by {reason} -- this character doesn't qualify."
        limit = attunement_limit(char)
        if len(attuned) >= limit:
            return f"Maximum {limit} attuned items (PHB p.138)."
        attuned.append(name)
        entry["attuned"] = True
    else:
        entry["attuned"] = False
        while name in attuned:
            attuned.remove(name)
    entry["attunement"] = bool(entry.get("attuned"))
    return ""


def can_study_manual(entry: dict) -> bool:
    """A manual or tome works once: after its 48 hours of study it's spent
    (DMG: its magic is gone for a century)."""
    return bool(entry) and entry.get("name") in ABILITY_SCORE_MANUALS and not entry.get("studied")


def study_owned_manual(char: dict, uid: str) -> tuple[str, int] | None:
    """Study one copy: +2 to its ability score, and that book is marked
    studied (kept, but it can't be studied again). Returns (ability, new
    score), or None if this copy can't be studied."""
    entry = find_magic_item(char, uid)
    if not can_study_manual(entry):
        return None
    ability = ABILITY_SCORE_MANUALS[entry["name"]]
    abilities = char.setdefault("abilities", {})
    abilities[ability] = abilities.get(ability, 10) + 2
    # "...increases by 2, as does your maximum for that score" -- the
    # builder's 20 (or 24) cap reads this, so the +2 survives a rebuild
    max_bonus = char.setdefault("ability_max_bonus", {})
    max_bonus[ability] = max_bonus.get(ability, 0) + 2
    entry["studied"] = True
    entry["equipped"] = False
    return ability, abilities[ability]


# ── Item charges and once-a-day uses ──────────────────────────────────────
# char["item_charges"]: {item: {"current", "max", "recharge"}} (sync_item_charges)
# char["item_uses"]:    {action card: {"current", "max", "recharge"}} -- an
#                       item's once-a-day action that has no charges
_REGAIN_RE = _re.compile(r"regains?\s+(all|\d+d\d+(?:\s*[+-]\s*\d+)?|\d+)\s+(?:of its\s+)?"
                         r"(?:expended\s+)?charges?", _re.I)


def _roll(expr: str, rng) -> int:
    m = _re.fullmatch(r"(\d+)d(\d+)(?:\s*([+-])\s*(\d+))?", expr.strip())
    if not m:
        return int(expr) if expr.strip().isdigit() else 0
    total = sum(rng.randint(1, int(m.group(2))) for _ in range(int(m.group(1))))
    if m.group(3):
        total += int(m.group(4)) * (1 if m.group(3) == "+" else -1)
    return max(0, total)


def charges_at_dawn(char: dict, rng=None) -> list:
    """A long rest's dawn: each item gets its charges back the way its own
    rules say ("regains 1d6 + 1 expended charges daily at dawn" -- rolled,
    and the roll is in what this returns; "regains all", or nothing said,
    fills it), and once-a-day item uses come back. Returns what came back,
    one plain line per item, for the rest's toast."""
    import random
    rng = rng or random
    out = []
    for name, data in char.get("item_charges", {}).items():
        mx, cur = data.get("max", 0), data.get("current", 0)
        if data.get("recharge", "dawn") not in ("dawn", "dusk") or cur >= mx:
            continue
        catalog = get_magic_item(name) or {}
        m = _REGAIN_RE.search(catalog.get("desc", "") or "")
        if not m or m.group(1).lower() == "all":
            data["current"] = mx
            out.append(f"{name}: back to {mx}/{mx} charge{'s' if mx != 1 else ''}")
            continue
        got = _roll(m.group(1), rng)
        data["current"] = min(mx, cur + got)
        out.append(f"{name}: rolled {got} on {m.group(1).replace(' ', '')}, "
                   f"{data['current']}/{mx} charges")
    for name, data in char.get("item_uses", {}).items():
        if data.get("current", 0) < data.get("max", 1):
            data["current"] = data.get("max", 1)
            out.append(f"{name}: ready again")
    return out
