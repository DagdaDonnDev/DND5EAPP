"""
Multiclass handler for D&D 5e (both 2014 and 2024 rules).

2024 multiclassing rules (from dnd2024.wikidot.com):
- Spell slots: Add levels from each class per caster type, look up combined total
  * Full casters (Bard/Cleric/Druid/Sorcerer/Wizard): all levels count
  * Half casters (Paladin/Ranger): round UP each class separately, then add
  * Third casters (Eldritch Knight Fighter / Arcane Trickster Rogue): round DOWN
  * Artificer: half levels, round UP
  * Warlock (Pact Magic): separate; slots do NOT add into multiclass table
    but Warlock CAN use shared Spellcasting slots for Warlock spells if also Spellcasting
- Spells known/prepared: determined per class individually (as if single-classed)
- Extra Attack: does NOT stack between classes (exception: Fighter Two Extra Attacks/Three Extra Attacks)
- Unarmored Defense: only one method can apply at a time
- Pact Magic slots interoperate with Spellcasting slots (2024: fully bidirectional)

Author: Ethan O'Brien
Date: 2026-08-20
"""

import math

# ── Multiclass Spell Slot Table ───────────────────────────────────────────────
# Index = combined caster level - 1 (so level 1 = index 0)
MULTICLASS_SPELL_SLOTS = {
    1:  [2,0,0,0,0,0,0,0,0],
    2:  [3,0,0,0,0,0,0,0,0],
    3:  [4,2,0,0,0,0,0,0,0],
    4:  [4,3,0,0,0,0,0,0,0],
    5:  [4,3,2,0,0,0,0,0,0],
    6:  [4,3,3,0,0,0,0,0,0],
    7:  [4,3,3,1,0,0,0,0,0],
    8:  [4,3,3,2,0,0,0,0,0],
    9:  [4,3,3,3,1,0,0,0,0],
    10: [4,3,3,3,2,0,0,0,0],
    11: [4,3,3,3,2,1,0,0,0],
    12: [4,3,3,3,2,1,0,0,0],
    13: [4,3,3,3,2,1,1,0,0],
    14: [4,3,3,3,2,1,1,0,0],
    15: [4,3,3,3,2,1,1,1,0],
    16: [4,3,3,3,2,1,1,1,0],
    17: [4,3,3,3,2,1,1,1,1],
    18: [4,3,3,3,3,1,1,1,1],
    19: [4,3,3,3,3,2,1,1,1],
    20: [4,3,3,3,3,2,2,1,1],
}

# ── Solo half-caster spell slot table (Paladin / Ranger) ─────────────────────
# Used when the character has ONLY one half-caster class (no multiclassing).
# Differs from the multiclass combined-caster-level table.
HALF_CASTER_SOLO_SLOTS = {
    1:  [0,0,0,0,0,0,0,0,0],  # Paladin/Ranger Lv1 has no slots
    2:  [2,0,0,0,0,0,0,0,0],
    3:  [3,0,0,0,0,0,0,0,0],
    4:  [3,0,0,0,0,0,0,0,0],
    5:  [4,2,0,0,0,0,0,0,0],
    6:  [4,2,0,0,0,0,0,0,0],
    7:  [4,3,0,0,0,0,0,0,0],
    8:  [4,3,0,0,0,0,0,0,0],
    9:  [4,3,2,0,0,0,0,0,0],
    10: [4,3,2,0,0,0,0,0,0],
    11: [4,3,3,0,0,0,0,0,0],
    12: [4,3,3,0,0,0,0,0,0],
    13: [4,3,3,1,0,0,0,0,0],
    14: [4,3,3,1,0,0,0,0,0],
    15: [4,3,3,2,0,0,0,0,0],
    16: [4,3,3,2,0,0,0,0,0],
    17: [4,3,3,3,1,0,0,0,0],
    18: [4,3,3,3,1,0,0,0,0],
    19: [4,3,3,3,2,0,0,0,0],
    20: [4,3,3,3,2,0,0,0,0],
}

# Solo Artificer table (spellcasting starts at Lv1, but Lv1 slots come at Lv3)
ARTIFICER_SOLO_SLOTS = {
    1:  [0,0,0,0,0,0,0,0,0],
    2:  [2,0,0,0,0,0,0,0,0],
    3:  [3,0,0,0,0,0,0,0,0],
    4:  [3,0,0,0,0,0,0,0,0],
    5:  [4,2,0,0,0,0,0,0,0],
    6:  [4,2,0,0,0,0,0,0,0],
    7:  [4,3,0,0,0,0,0,0,0],
    8:  [4,3,0,0,0,0,0,0,0],
    9:  [4,3,2,0,0,0,0,0,0],
    10: [4,3,2,0,0,0,0,0,0],
    11: [4,3,3,0,0,0,0,0,0],
    12: [4,3,3,0,0,0,0,0,0],
    13: [4,3,3,1,0,0,0,0,0],
    14: [4,3,3,1,0,0,0,0,0],
    15: [4,3,3,2,0,0,0,0,0],
    16: [4,3,3,2,0,0,0,0,0],
    17: [4,3,3,3,1,0,0,0,0],
    18: [4,3,3,3,1,0,0,0,0],
    19: [4,3,3,3,2,0,0,0,0],
    20: [4,3,3,3,2,0,0,0,0],
}


# Warlock pact slots (tracked separately; NOT merged into spell slot table)
WARLOCK_PACT_SLOTS = {
    1:1,  2:2,  3:2,  4:2,  5:2,  6:2,  7:2,  8:2,  9:2, 10:2,
    11:3, 12:3, 13:3, 14:3, 15:3, 16:3, 17:4, 18:4, 19:4, 20:4
}
WARLOCK_PACT_LEVEL = {
    1:1,2:1,3:2,4:2,5:3,6:3,7:4,8:4,9:5,10:5,
    11:5,12:5,13:5,14:5,15:5,16:5,17:5,18:5,19:5,20:5
}

# Caster type per class
FULL_CASTERS = {"Bard","Cleric","Druid","Sorcerer","Wizard"}
HALF_CASTERS = {"Paladin","Ranger"}  # round up per class (2024)
THIRD_CASTERS_SUBCLASS = {"Eldritch Knight","Arcane Trickster"}  # round down
ARTIFICER_CLASSES = {"Artificer"}  # half, round up
PACT_MAGIC_CLASSES = {"Warlock"}   # separate pact slots

# 2024 multiclass prerequisites (minimum ability scores)
MULTICLASS_PREREQS_2024 = {
    "Artificer":   {"INT": 13},
    "Barbarian":   {"STR": 13},
    "Bard":        {"CHA": 13},
    "Cleric":      {"WIS": 13},
    "Druid":       {"WIS": 13},
    "Fighter":     {"STR": 13, "DEX": 13, "_or": True},
    "Monk":        {"STR": 13, "WIS": 13},
    "Paladin":     {"STR": 13, "CHA": 13},
    "Ranger":      {"DEX": 13, "WIS": 13},
    "Rogue":       {"DEX": 13},
    "Sorcerer":    {"CHA": 13},
    "Warlock":     {"CHA": 13},
    "Wizard":      {"INT": 13},
    "Blood Hunter":{"INT": 13, "_or_group": {"STR": 13, "DEX": 13}},
}


def check_multiclass_prereq(class_name: str, ability_scores: dict) -> tuple[bool, str]:
    """
    Check if a character meets the multiclass prerequisite for a class.
    ability_scores: {"STR": 14, "DEX": 12, ...}
    Returns (meets_prereq: bool, reason: str)
    """
    reqs = MULTICLASS_PREREQS_2024.get(class_name, {})
    if not reqs:
        return True, ""

    is_or = reqs.get("_or", False)
    or_group = reqs.get("_or_group")
    failures = []
    passes = []

    for stat, min_val in reqs.items():
        if stat in ("_or", "_or_group"):
            continue
        score = ability_scores.get(stat, 0)
        if score >= min_val:
            passes.append(f"{stat} {score} ≥ {min_val}")
        else:
            failures.append(f"{stat} {score} < {min_val} required")

    # Mixed AND+OR case (Blood Hunter: INT 13 AND (STR 13 OR DEX 13)) —
    # the plain (non-grouped) stats above are still AND'd normally; the
    # _or_group stats need at least one to pass.
    if or_group:
        group_passes = []
        group_failures = []
        for stat, min_val in or_group.items():
            score = ability_scores.get(stat, 0)
            if score >= min_val:
                group_passes.append(f"{stat} {score} ≥ {min_val}")
            else:
                group_failures.append(f"{stat} {score} < {min_val}")
        if not group_passes:
            group_names = "/".join(or_group.keys())
            failures.append(f"need {group_names} 13+ ({'; '.join(group_failures)})")
        elif not failures:
            passes.append(f"meets one of: {'; '.join(group_passes)}")

    if is_or:
        if passes:
            return True, f"Meets one of: {'; '.join(passes)}"
        return False, f"Need STR or DEX 13+. {'; '.join(failures)}"
    else:
        if not failures:
            return True, "All prerequisites met"
        return False, "; ".join(failures)


def prof_bonus(total_level: int) -> int:
    """Return proficiency bonus for a given total character level."""
    return max(2, (total_level - 1) // 4 + 2)


def compute_caster_level(class_levels: dict, subclasses: dict = None) -> int:
    """
    Compute combined spellcasting level for multiclass spell slot table.

    class_levels: {"Wizard": 5, "Paladin": 3, "Warlock": 4}
    subclasses: {"Fighter": "Eldritch Knight", "Rogue": "Arcane Trickster"}

    Returns combined caster level (for non-Warlock slots).
    Warlock is excluded and tracked separately.

    2024 rules: Paladin/Ranger round UP each class's contribution independently.
    """
    if subclasses is None:
        subclasses = {}

    combined = 0

    for cls_name, level in class_levels.items():
        if level <= 0:
            continue

        if cls_name in FULL_CASTERS:
            combined += level

        elif cls_name in ARTIFICER_CLASSES:
            # Artificer uses floor for BOTH single-class and multiclass (TCE p.12)
            # Artificer Lv1 has no spell slots; the table starts at Lv2.
            combined += math.floor(level / 2)

        elif cls_name in HALF_CASTERS:
            # PHB p.164: add half your level in that class, ROUNDED DOWN
            combined += math.floor(level / 2)

        elif cls_name == "Fighter":
            sub = subclasses.get("Fighter", "")
            if sub == "Eldritch Knight":
                combined += math.floor(level / 3)

        elif cls_name == "Rogue":
            sub = subclasses.get("Rogue", "")
            if sub == "Arcane Trickster":
                combined += math.floor(level / 3)

        elif cls_name in PACT_MAGIC_CLASSES:
            pass  # Warlock excluded from combined caster level

    return combined


def get_multiclass_spell_slots(combined_caster_level: int) -> list:
    """
    Returns spell slot list [lvl1, lvl2, ..., lvl9] for given combined caster level.
    Returns 9 zeros if caster level is 0.
    """
    if combined_caster_level <= 0:
        return [0] * 9
    level = min(max(combined_caster_level, 1), 20)
    return list(MULTICLASS_SPELL_SLOTS[level])


def get_warlock_slots(warlock_levels: int) -> dict:
    """
    Returns Warlock Pact Magic slot info.
    {"count": 2, "level": 3, "reset": "SR"}
    """
    if warlock_levels <= 0:
        return {"count": 0, "level": 0, "reset": "SR/LR"}
    wl = min(warlock_levels, 20)
    return {
        "count": WARLOCK_PACT_SLOTS[wl],
        "level": WARLOCK_PACT_LEVEL[wl],
        "reset": "SR/LR",  # Pact Magic slots recover on a short OR long
        # rest — actual reset logic is hardcoded separately in both rest
        # functions; this metadata is currently unused/dead but kept accurate.
    }


def compute_all_spell_slots(class_levels: dict, subclasses: dict = None) -> dict:
    """
    Full spell slot computation for a multiclassed character.

    Returns:
    {
        "combined_caster_level": int,
        "spell_slots": [int × 9],   # standard slots
        "warlock_slots": {count, level, reset} | None,
        "has_spellcasting": bool,
        "has_pact_magic": bool,
        "note": str
    }
    """
    if subclasses is None:
        subclasses = {}

    warlock_lvl = class_levels.get("Warlock", 0)
    combined_caster_level = compute_caster_level(class_levels, subclasses)

    # For a single half-caster or Artificer with no other spellcasting classes,
    # use the class's own progression table (different from the multiclass table)
    non_warlock_casters = {c: lvl for c, lvl in class_levels.items()
                           if c != "Warlock" and lvl > 0
                           and (c in FULL_CASTERS or c in HALF_CASTERS or c in ARTIFICER_CLASSES)}
    if len(non_warlock_casters) == 1:
        solo_cls, solo_lvl = next(iter(non_warlock_casters.items()))
        if solo_cls in HALF_CASTERS:
            slots = list(HALF_CASTER_SOLO_SLOTS.get(solo_lvl, [0]*9))
        elif solo_cls in ARTIFICER_CLASSES:
            slots = list(ARTIFICER_SOLO_SLOTS.get(solo_lvl, [0]*9))
        else:
            slots = get_multiclass_spell_slots(combined_caster_level)
    else:
        slots = get_multiclass_spell_slots(combined_caster_level)
    warlock_info = get_warlock_slots(warlock_lvl)

    # Determine if any Spellcasting feature exists (for Warlock interop)
    has_spellcasting = combined_caster_level > 0
    has_pact_magic = warlock_lvl > 0

    note = ""
    if has_spellcasting and has_pact_magic:
        note = ("Pact Magic slots can be used to cast Spellcasting spells "
                "and vice versa (2024 rules). Both slot pools are tracked.")
    elif has_pact_magic and not has_spellcasting:
        note = "Warlock Pact Magic only; no standard Spellcasting feature."

    return {
        "combined_caster_level": combined_caster_level,
        "spell_slots": slots,
        "warlock_slots": warlock_info if has_pact_magic else None,
        "has_spellcasting": has_spellcasting,
        "has_pact_magic": has_pact_magic,
        "note": note,
    }


def aggregate_resources(class_levels: dict, ability_scores: dict,
                        subclasses: dict = None, choices: dict = None,
                        optional_rules: dict = None) -> list:
    """
    Compute all class resources for a multiclassed character.
    Returns list of resource dicts ready for the UI tracker.
    """
    from dnd_app.data.classes import CLASS_DICT

    if subclasses is None:
        subclasses = {}
    if optional_rules is None:
        optional_rules = {}

    total_level = sum(class_levels.values())
    pb = prof_bonus(total_level)
    resources = []
    ability_mods = {k: (v - 10) // 2 for k, v in ability_scores.items()}

    for cls_name, level in class_levels.items():
        if level <= 0:
            continue
        cls = CLASS_DICT.get(cls_name)
        if not cls:
            continue

        for res in cls.get("resources", []):
            # Only include if class level meets availability
            avail_at = res.get("available_at", 1)
            if level < avail_at:
                continue
            # Optional class features (TCE) are DM-approved opt-in, not
            # automatic — gated by the real Settings-popup "Optional
            # Rules" toggle, the same established mechanism already used
            # for Eldritch Versatility, not a separate ad-hoc one.
            if res.get("optional"):
                opt_key = res.get("name", "").lower().replace(" ", "_")
                if not optional_rules.get(opt_key, False):
                    continue
            # Only include subclass-specific resources if subclass matches
            res_sub = res.get("subclass")
            if res_sub:
                current_sub = subclasses.get(cls_name, "") or ""
                # Flexible match: normalise both to lowercase, check substring
                res_norm = res_sub.lower().split("(")[0].strip()
                cur_norm = current_sub.lower().split("(")[0].strip()
                if res_norm not in cur_norm and cur_norm not in res_norm:
                    continue

            entry = dict(res)
            entry["source_class"] = cls_name
            entry["source_level"] = level

            # Compute current value
            formula = res.get("formula", "")
            by_level = res.get("by_level", {})

            # Find correct value from by_level table
            if by_level:
                val = None
                for lvl_threshold in sorted(by_level.keys()):
                    if isinstance(lvl_threshold, int) and level >= lvl_threshold:
                        val = by_level[lvl_threshold]
                entry["current_max"] = val if val is not None else 0

            # Resolve die_by_level to a 'die' field
            die_by_level = res.get("die_by_level", {})
            if die_by_level:
                die = None
                for lvl_threshold in sorted(die_by_level.keys()):
                    if isinstance(lvl_threshold, int) and level >= lvl_threshold:
                        die = die_by_level[lvl_threshold]
                if die:
                    entry["die"] = die

            if formula:    # NOT elif — die_by_level and formula are independent
                # Evaluate simple formulas via safe arithmetic (no eval)
                try:
                    from dnd_app.core.safe_eval import safe_eval_arith
                    f = formula
                    f = f.replace("level", str(level))
                    f = f.replace("CHA_mod", str(ability_mods.get("CHA", 0)))
                    f = f.replace("WIS_mod", str(ability_mods.get("WIS", 0)))
                    f = f.replace("INT_mod", str(ability_mods.get("INT", 0)))
                    f = f.replace("CON_mod", str(ability_mods.get("CON", 0)))
                    f = f.replace("STR_mod", str(ability_mods.get("STR", 0)))
                    f = f.replace("DEX_mod", str(ability_mods.get("DEX", 0)))
                    val = max(1, int(safe_eval_arith(f)))
                    min_v = res.get("min_val", 1)
                    entry["current_max"] = max(min_v, val)
                except Exception:
                    entry["current_max"] = res.get("min_val", 1)

            # Resolve die_by_level to 'die' field (for formula-based resources too)
            die_by_level = res.get("die_by_level", {})
            if die_by_level and "die" not in entry:
                die = None
                for lvl_threshold in sorted(die_by_level.keys()):
                    if isinstance(lvl_threshold, int) and level >= lvl_threshold:
                        die = die_by_level[lvl_threshold]
                if die:
                    entry["die"] = die

            resources.append(entry)

    # ── Monk Ki / Focus Points ────────────────────────────────────────────────
    monk_lvl = class_levels.get("Monk", 0)
    if monk_lvl >= 2:
        resources.append({
            "name": "Focus Points (Ki)", "key": "ki",
            "source_class": "Monk", "source_level": monk_lvl,
            "current_max": monk_lvl, "reset": "SR", "track": "pool"
        })

    # ── Subclass-specific resources ────────────────────────────────────────────
    _add_subclass_resources(resources, class_levels, subclasses or {}, ability_mods, pb, choices or {})

    # Pact slots tracked in Spells tab
    return resources


def _add_subclass_resources(resources: list, class_levels: dict,
                             subclasses: dict, ability_mods: dict, pb: int, choices: dict = None):
    """Append subclass-specific trackable resources."""""

    def _has(cls, *sub_fragments):
        sub = subclasses.get(cls, "").lower()
        return any(f.lower() in sub for f in sub_fragments)

    def _add(name, key, reset, max_val, track="uses", note="", cls_name="", sub_name=""):
        resources.append({
            "name": name, "key": key,
            "reset": reset, "current_max": max_val,
            "track": track, "note": note,
            "source_class": cls_name, "subclass": sub_name,
        })

    # ── Fighter ──────────────────────────────────────────────────────────────
    fighter_lvl = class_levels.get("Fighter", 0)
    if fighter_lvl > 0:
        # Psi Warrior: Psionic Energy Dice (d6 pool = TWICE proficiency bonus).
        if _has("Fighter", "psi warrior"):
            _add("Psionic Energy Dice (Psi Warrior)", "psionic_dice", "LR",
                 pb * 2, "pool", "d6 pool (d8 at 5th, d10 at 11th, d12 at 17th); 2x proficiency bonus", "Fighter", "Psi Warrior")
        # Rune Knight: Giant's Might uses
        if _has("Fighter", "rune knight"):
            _add("Giant's Might", "giants_might", "LR",
                 pb, "uses", "STR checks / saves; Lv3=1/LR", "Fighter", "Rune Knight")
        # Echo Knight: Manifest Echo (no limited uses, but note it)
        # Samurai: Fighting Spirit
        if _has("Fighter", "samurai"):
            _add("Fighting Spirit", "fighting_spirit", "LR",
                 3, "uses", "Advantage on weapon attacks + temp HP, until end of turn", "Fighter", "Samurai")
        # Cavalier: Unwavering Mark
        if _has("Fighter", "cavalier"):
            _add("Unwavering Mark", "unwavering_mark", "LR",
                 max(1, ability_mods.get("STR", 0)), "uses",
                 "Mark a creature; bonus attack if they attack others", "Fighter", "Cavalier")

    # ── Rogue ─────────────────────────────────────────────────────────────────
    rogue_lvl = class_levels.get("Rogue", 0)
    if rogue_lvl > 0:
        # Soulknife: Psionic Energy Dice (twice proficiency bonus, per the same rule text as Psi Warrior).
        if _has("Rogue", "soulknife"):
            _add("Psionic Energy Dice (Soulknife)", "psionic_dice_rogue", "LR",
                 pb * 2, "pool", "d6 pool (scales at 5th/11th/17th); 2x proficiency bonus", "Rogue", "Soulknife")
        # Phantom: Ghost Walk — 13th level, 1 free use per long rest,
        # reusable by destroying a Soul Trinket. Was missing entirely,
        # meaning there was no way to actually toggle this transformation
        # active despite the mechanic existing in text.
        if rogue_lvl >= 13 and _has("Rogue", "phantom"):
            _add("Ghost Walk", "ghost_walk", "LR",
                 1, "uses",
                 "Bonus action, 10 minutes: fly speed 10 ft (can hover), attack rolls against "
                 "you have disadvantage, move through creatures/objects (1d10 force damage if "
                 "you end your turn inside one)",
                 "Rogue", "Phantom")

    # ── Monk ──────────────────────────────────────────────────────────────────
    # Was entirely absent — no Monk subclass (Kensei, Astral Self, etc.)
    # had any trackable resources at all in this function.
    monk_lvl_res = class_levels.get("Monk", 0)
    if monk_lvl_res > 0:
        # Way of the Astral Self: Arms and Awakened Astral Self are both
        # gated purely by spending ki (a separate, already-tracked pool),
        # with no dedicated use-limit of their own — nominal high count so
        # the toggle has a row to attach to, same pattern as Umbral
        # Form/Otherworldly Wings above.
        if _has("Monk", "astral"):
            _add("Arms of the Astral Self", "arms_of_the_astral_self", "LR",
                 99, "uses",
                 "Bonus action, spend 1 ki: summon spectral arms for 10 minutes — DEX save "
                 "burst on summon, WIS-based unarmed strikes with the arms (+5 ft reach)",
                 "Monk", "Way of the Astral Self")
            if monk_lvl_res >= 17:
                _add("Awakened Astral Self", "awakened_astral_self", "LR",
                     99, "uses",
                     "Bonus action, spend 5 ki: summon arms, visage, and body together for "
                     "10 minutes — +2 AC, extra attack with the astral arms",
                     "Monk", "Way of the Astral Self")
        # Way of the Ascendant Dragon: Aspect of the Wyrm — 11th level, 1
        # free use per long rest, reusable by spending 3 ki. Was missing
        # entirely, meaning there was no way to actually toggle this
        # transformation active despite the mechanic existing in text.
        if monk_lvl_res >= 11 and _has("Monk", "ascendant dragon"):
            _add("Aspect of the Wyrm", "aspect_of_the_wyrm", "LR",
                 1, "uses",
                 "Bonus action, 1 minute: 10-ft aura — choose Frightful Presence (WIS save "
                 "or frightened, renewable) or Resistance (you and allies resist a chosen "
                 "damage type). Free 1/LR, or spend 3 ki to use again",
                 "Monk", "Way of the Ascendant Dragon")
        # Arcane Trickster: doesn't need extra resource (uses spell slots)

    # ── Warlock ───────────────────────────────────────────────────────────────
    warlock_lvl = class_levels.get("Warlock", 0)
    if warlock_lvl > 0:
        # Hexblade: Hexblade's Curse — uses = CHA modifier (min 1), per
        # "you can use this feature a number of times equal to your
        # Charisma modifier (a minimum of once)."
        if _has("Warlock", "hexblade"):
            _add("Hexblade's Curse", "hexblade_curse", "SR/LR",
                 max(1, ability_mods.get("CHA", 0)), "uses",
                 "Bonus to damage = prof bonus; crit on 19-20; kill = regain HP (level + CHA mod)",
                 "Warlock", "Hexblade")
        # Undead: Form of Dread — uses = proficiency bonus, per "you can
        # transform a number of times equal to your proficiency bonus."
        if _has("Warlock", "undead"):
            _add("Form of Dread", "form_of_dread", "LR",
                 max(1, pb), "uses",
                 "Bonus action, 1 min: gain 1d10+Warlock level temp HP, immune to frightened; "
                 "once/turn on a hit, WIS save or target is frightened until end of your next turn",
                 "Warlock", "The Undead")
        # Archfey: Misty Escape (reaction)
        if _has("Warlock", "archfey"):
            _add("Misty Escape", "misty_escape", "SR/LR",
                 1, "uses",
                 "Reaction to taking damage: turn invisible + teleport up to 60 ft; invisibility "
                 "ends at the start of your next turn or if you attack/cast a spell",
                 "Warlock", "The Archfey")
        # Fathomless: Tentacle of the Deep — uses = proficiency bonus per LR
        if _has("Warlock", "fathomless"):
            _add("Tentacle of the Deep", "tentacle_of_the_deep", "LR",
                 pb, "uses",
                 "Bonus action: summon a 10-ft spectral tentacle; melee spell attack 1d8 cold "
                 "(2d8 at 10th) and reduce target's speed by 10 ft until start of your next turn. "
                 "Bonus action on later turns: move it 30 ft and repeat the attack.",
                 "Warlock", "The Fathomless")
        # Undying: Defy Death (6th) and Indestructible Life (14th)
        if _has("Warlock", "undying"):
            if warlock_lvl >= 6:
                _add("Defy Death", "defy_death", "LR",
                     1, "uses",
                     "Regain 1d8 + CON mod HP (min 1) when you succeed a death save or stabilize a "
                     "creature with Spare the Dying",
                     "Warlock", "The Undying")
            if warlock_lvl >= 14:
                _add("Indestructible Life", "indestructible_life", "SR/LR",
                     1, "uses",
                     f"Bonus action: regain 1d8+{warlock_lvl} HP, or reattach/regrow a severed body part",
                     "Warlock", "The Undying")
        # Genie: Bottled Respite — duration is twice proficiency bonus.
        if _has("Warlock", "genie"):
            _add("Bottled Respite", "bottled_respite", "LR",
                 1, "uses", f"Enter vessel for a short rest; lasts up to {2*pb} hours (2x proficiency bonus)",
                 "Warlock", "The Genie")
        # Genie: Elemental Gift — 6th level. Resistance to genie kind's
        # damage type is always-on (not tracked here), but the bonus-action
        # flying speed for 10 minutes needs a trackable resource, which
        # was missing entirely.
        if warlock_lvl >= 6 and _has("Warlock", "genie"):
            _add("Elemental Gift", "elemental_gift", "LR",
                 max(1, pb), "uses",
                 "Bonus action: gain a flying speed of 30 ft for 10 minutes (can hover)",
                 "Warlock", "The Genie")

    # ── Druid ─────────────────────────────────────────────────────────────────
    druid_lvl = class_levels.get("Druid", 0)
    if druid_lvl > 0:
        # Circle of Dreams: Balm of the Summer Court — a d6 dice pool.
        if _has("Druid", "dreams"):
            _add("Balm of the Summer Court", "balm_summer_court", "LR",
                 druid_lvl, "pool",
                 "d6 pool: spend up to half your Druid level (rounded down) worth of dice "
                 "on an ally within 120 ft as a bonus action — roll them, restore that much "
                 "HP, and grant 1 temp HP per die spent",
                 "Druid", "Circle of Dreams")
        # Spores: Symbiotic Entity / Halo of Spores. The real mechanic
        # rolls the Halo of Spores damage die a SECOND time (not a
        # die-size change), plus +1d6 necrotic on melee weapon hits.
        if _has("Druid", "spores"):
            _add("Symbiotic Entity Temp HP", "symbiotic_hp", "Wild Shape use",
                 4 * druid_lvl, "pool",
                 "Use Wild Shape: gain 4×druid level temp HP; while active, roll your Halo of "
                 "Spores die twice, and melee weapon attacks deal +1d6 necrotic",
                 "Druid", "Circle of Spores")
        # Stars: Starry Form expends a use of Wild Shape (same pattern
        # as Symbiotic Entity above), with no separate resource pool of its own.
        if _has("Druid", "stars"):
            _add("Starry Form", "starry_form", "Wild Shape use",
                 99, "uses",
                 "Bonus action, expend a Wild Shape use: transform into starry form "
                 "(Archer/Chalice/Dragon), 10 minutes",
                 "Druid", "Circle of Stars")
        # Shepherd: Spirit Totem — 2nd level, 1 use per short or long rest.
        if _has("Druid", "shepherd"):
            _add("Spirit Totem", "spirit_totem", "SR/LR",
                 1, "uses",
                 "Bonus action, 1 minute: summon a spectral totem animal (Bear, Hawk, or "
                 "Unicorn) in a 30-ft radius with a choice-dependent effect",
                 "Druid", "Circle of the Shepherd")

    # ── Blood Hunter ──────────────────────────────────────────────────────────
    bh_lvl = class_levels.get("Blood Hunter", 0)
    if bh_lvl > 0:
        # Order of the Lycan: Hybrid Transformation
        if _has("Blood Hunter", "lycan"):
            # PHB(BH) p.: 1 use at 3rd level, 2 at 11th (Advanced
            # Transformation), unlimited at 18th (Hybrid Transformation
            # Mastery) — the old "(lvl+1)//2" formula didn't match this at
            # any level (e.g. gave 2 uses at 3rd, 9 at 17th).
            if bh_lvl >= 18:
                _add("Hybrid Transformation", "hybrid_form", "LR",
                     999, "uses",
                     "Unlimited uses; hybrid form lasts until you revert, fall unconscious, or die",
                     "Blood Hunter", "Order of the Lycan")
            else:
                uses = 2 if bh_lvl >= 11 else 1
                _add("Hybrid Transformation", "hybrid_form", "LR",
                     uses, "uses",
                     "Bonus action: transform into werewolf hybrid form for up to 1 hour; enhanced Crimson Rite; feral instincts",
                     "Blood Hunter", "Order of the Lycan")
        # Order of the Mutant: Mutagencraft — two SEPARATE progressions:
        # how many mutagens you can concoct per rest, and how many formulas you know in total.
        if _has("Blood Hunter", "mutant"):
            if bh_lvl >= 15: created = 3
            elif bh_lvl >= 7: created = 2
            else: created = 1
            if bh_lvl >= 18: known = 8
            elif bh_lvl >= 15: known = 7
            elif bh_lvl >= 11: known = 6
            elif bh_lvl >= 7: known = 5
            else: known = 4
            _add("Mutagens", "mutagens", "SR/LR",
                 created, "uses",
                 f"Concoct {created} mutagen(s) per short/long rest (choosing from your {known} known formulas); "
                 f"each lasts until your next short/long rest and has an effect plus a side effect",
                 "Blood Hunter", "Order of the Mutant")
        # Order of the Ghostslayer: Rite of the Dawn is an always-on
        # passive benefit while the rite is active, shown as a Combat-
        # page reminder rather than tracked as a limited resource.

    # ── Wizard ────────────────────────────────────────────────────────────────
    wiz_lvl = class_levels.get("Wizard", 0)
    if wiz_lvl > 0:
        # Bladesinging: Bladesong — uses = proficiency bonus per long rest.
        if _has("Wizard", "bladesing"):
            _add("Bladesong", "bladesong", "LR",
                 pb, "uses",
                 "Bonus action: +INT mod AC, +10 ft speed, adv on Acrobatics, "
                 "extra concentration save bonus, for 1 minute",
                 "Wizard", "Bladesinging")
        # Abjuration: Arcane Ward — a damage-absorbing pool (2x Wizard
        # level + INT mod). Recharges when you cast an Abjuration spell
        # of 1st level or higher (not a rest) — "LR" here just sets the
        # starting value; the player manually restores it via the
        # pool's own +/- control when that trigger happens.
        if _has("Wizard", "abjuration"):
            _add("Arcane Ward", "arcane_ward", "LR",
                 max(0, 2 * wiz_lvl + ability_mods.get("INT", 0)), "pool",
                 "Absorbs damage before it reaches your HP. Recharges (up to its max) by "
                 "twice the level of an Abjuration spell you cast, instead of on a rest.",
                 "Wizard", "Abjuration")
        # Divination: Portent — 2 dice at 2nd level, 3 at 14th (Greater
        # Portent): "you roll three d20s for your Portent feature,
        # rather than two."
        if _has("Wizard", "divination"):
            portent_dice = 3 if wiz_lvl >= 14 else 2
            _add("Portent", "portent", "LR",
                 portent_dice, "uses",
                 f"Roll {portent_dice}d20 after a long rest; replace any attack roll, "
                 f"saving throw, or ability check (yours or a creature you can see) "
                 f"with one of these dice instead of rolling",
                 "Wizard", "Divination")
        # Chronurgy: Chronal Shift and Momentary Stasis each have a per-long-rest use limit.
        if _has("Wizard", "chronurgy"):
            _add("Chronal Shift", "chronal_shift", "LR",
                 2, "uses",
                 "Reaction: force a creature to reroll an attack roll, ability check, "
                 "or saving throw after seeing the result",
                 "Wizard", "Chronurgy Magic")
            if wiz_lvl >= 14:
                _add("Momentary Stasis", "momentary_stasis", "LR",
                     max(1, ability_mods.get("INT", 0)), "uses",
                     "Force a Large or smaller creature within 60 ft to make a CON save or "
                     "be encased until it takes damage or the end of your next turn",
                     "Wizard", "Chronurgy Magic")

    # ── Barbarian ─────────────────────────────────────────────────────────────
    barb_lvl = class_levels.get("Barbarian", 0)
    if barb_lvl > 0:
        # Totem Warrior, Berserker, etc. don't add separate pools
        # Path of the Beast: Form of the Beast (uses Rage)
        # Zealot: Divine Fury (uses Rage)
        # Path of the Giant: Giant's Might — uses = proficiency bonus per
        # long rest. Distinct from Rune Knight's (Fighter) same-named
        # feature, which scales off CON mod instead — tracked separately
        # since the two use different scaling despite sharing a name.
        if _has("Barbarian", "giant"):
            _add("Giant's Might", "giants_might_barb", "LR",
                 pb, "uses", "Bonus action: grow one size larger for 1 min",
                 "Barbarian", "Path of the Giant")

    # ── Bard ──────────────────────────────────────────────────────────────────
    bard_lvl = class_levels.get("Bard", 0)
    if bard_lvl >= 6 and _has("Bard", "creation"):
        # College of Creation: Animating Performance ("Dancing Item") —
        # once per long rest, or spend a 3rd+ level spell slot to reuse early.
        _add("Animating Performance", "dancing_item_summon", "LR",
             1, "uses",
             "Animate a Large or smaller nonmagical item as a temporary ally for 1 hour; "
             "can reuse before a long rest by spending a spell slot of 3rd level or higher",
             "Bard", "College of Creation")
    if bard_lvl > 0 and _has("Bard", "spirits"):
        # College of Spirits: Spirit Session — uses = proficiency bonus per
        # long rest, die scales from d6 up to d12 at 14th (Awakened Spirit).
        # Verified not already covered by classes.py's resource_pools data
        # (unlike Bardic Inspiration, which already was).
        spirit_die = 12 if bard_lvl >= 14 else 10 if bard_lvl >= 10 else 8 if bard_lvl >= 6 else 6
        _add("Spirit Session", "spirit_session", "LR", pb, "uses",
             f"Commune with spirits for a d{spirit_die} Spirit Tale Die (heal/damage/status, story-dependent)",
             "Bard", "College of Spirits")

    # ── Cleric ────────────────────────────────────────────────────────────────
    cleric_lvl = class_levels.get("Cleric", 0)
    if cleric_lvl > 0:
        # Order Domain: Voice of Authority (no uses, passive)
        # Peace Domain: Emboldening Bond
        if _has("Cleric", "peace"):
            _add("Emboldening Bond", "emboldening_bond", "LR",
                 max(1, pb), "uses",
                 f"Bond {pb} creatures: add d4 to attack/save/check 1/turn while within 30 ft",
                 "Cleric", "Peace Domain")
        # War Domain: War Priest — uses = WIS mod per long rest
        if _has("Cleric", "war"):
            _add("War Priest", "war_priest", "LR",
                 max(1, ability_mods.get("WIS", 0)), "uses",
                 "When you take the Attack action, make one weapon attack as a bonus action",
                 "Cleric", "War Domain")
        # Twilight Domain: Steps of Night — 6th level, proficiency bonus
        # uses per long rest. Was missing entirely, meaning there was no
        # way to actually toggle this transformation active despite the
        # mechanic existing in text.
        if cleric_lvl >= 6 and _has("Cleric", "twilight"):
            _add("Steps of Night", "steps_of_night", "LR",
                 max(1, pb), "uses",
                 "Bonus action while in dim light or darkness, 1 minute: flying speed equal "
                 "to your walking speed",
                 "Cleric", "Twilight Domain")

    # ── Paladin ───────────────────────────────────────────────────────────────
    paladin_lvl = class_levels.get("Paladin", 0)
    if paladin_lvl > 0:
        # Ancients: Aura of Warding (passive) - no resource
        # Conquest: Aura of Conquest (passive) - no resource
        # Oathbreaker: Control Undead
        if _has("Paladin", "oathbreaker"):
            _add("Control Undead", "control_undead", "SR/LR",
                 1, "uses",
                 "Command an undead creature you can see (CHA save DC = spell DC)",
                 "Paladin", "Oathbreaker")
        # Crown: Compelled Duel (no extra resource, uses spell slots)
        # Conquest: Invincible Conqueror — a standalone 1/LR capstone,
        # not a Channel Divinity option (unlike Peerless Athlete).
        if paladin_lvl >= 20 and _has("Paladin", "conquest"):
            _add("Invincible Conqueror", "invincible_conqueror", "LR",
                 1, "uses",
                 "Action: become an avatar of conquest for 1 minute — resistance to all "
                 "damage, one additional attack, melee crits on 19-20",
                 "Paladin", "Oath of Conquest")
        # Crown: Exalted Champion — same shape of gap as Invincible
        # Conqueror, also a standalone 1/LR capstone, also missing.
        if paladin_lvl >= 20 and _has("Paladin", "crown"):
            _add("Exalted Champion", "exalted_champion", "LR",
                 1, "uses",
                 "Action: resistance to bludgeoning/piercing/slashing for 1 hour; "
                 "allies within 30 ft get advantage on death saves and WIS saves",
                 "Paladin", "Oath of the Crown")
        # Vengeance: Vow of Enmity — Channel Divinity, 1 min duration, but
        # was missing entirely as a trackable resource (no way to toggle
        # it active despite the mechanic existing in text).
        if paladin_lvl >= 3 and _has("Paladin", "vengeance"):
            _add("Vow of Enmity", "vow_of_enmity", "SR/LR",
                 1, "uses",
                 "Channel Divinity, bonus action: advantage on attack rolls against "
                 "one creature within 10 ft, for 1 minute",
                 "Paladin", "Oath of Vengeance")
        # Glory: Living Legend — 20th-level capstone, 1 min duration.
        if paladin_lvl >= 20 and _has("Paladin", "glory"):
            _add("Living Legend", "living_legend", "LR",
                 1, "uses",
                 "Bonus action, 1 minute: advantage on CHA checks, turn a missed weapon "
                 "attack into a hit once per turn, and reroll a failed save. Free 1/LR, "
                 "or expend a 5th-level spell slot to use it again",
                 "Paladin", "Oath of Glory")
        # Watchers: Mortal Bulwark — 20th-level capstone, 1 min duration,
        # missing entirely.
        if paladin_lvl >= 20 and _has("Paladin", "watchers"):
            _add("Mortal Bulwark", "mortal_bulwark", "LR",
                 1, "uses",
                 "Bonus action, 1 minute: truesight 120 ft, advantage vs extraplanar "
                 "creatures, banish on a hit (CHA save)",
                 "Paladin", "Oath of the Watchers")
        # Ancients: Elder Champion — 20th-level capstone, 1 min duration,
        # missing entirely.
        if paladin_lvl >= 20 and _has("Paladin", "ancients"):
            _add("Elder Champion", "elder_champion", "LR",
                 1, "uses",
                 "Action, 1 minute: regain 10 HP each turn, cast spells as a bonus "
                 "action, enemies within 10 ft have disadvantage vs your spells/CD",
                 "Paladin", "Oath of the Ancients")

    # ── Sorcerer ──────────────────────────────────────────────────────────────
    sorc_lvl = class_levels.get("Sorcerer", 0)
    if sorc_lvl > 0:
        # Aberrant Mind / Clockwork Soul: no extra resource (use sorcery points)
        # Wild Magic: Tides of Chaos
        if _has("Sorcerer", "wild magic"):
            _add("Tides of Chaos", "tides_of_chaos", "LR",
                 1, "uses",
                 "Gain advantage on one attack/check/save; DM may force Wild Magic Surge",
                 "Sorcerer", "Wild Magic")
        # Divine Soul: Favored by the Gods
        if _has("Sorcerer", "divine soul"):
            _add("Favored by the Gods", "favored_by_the_gods", "SR/LR",
                 1, "uses",
                 "Add 2d4 to a failed saving throw or missed attack roll",
                 "Sorcerer", "Divine Soul")
        # Divine Soul: Otherworldly Wings — 14th level, genuinely at-will
        # (no real use limit at all; lasts until dismissed, incapacitated,
        # or dead). Nominal high count so the toggle has a row to attach
        # to without implying a limit that doesn't exist.
        if sorc_lvl >= 14 and _has("Sorcerer", "divine soul"):
            _add("Otherworldly Wings", "otherworldly_wings", "LR",
                 99, "uses",
                 "Bonus action: manifest spectral wings (fly speed 30 ft), no use limit — "
                 "lasts until dismissed, incapacitated, or dead",
                 "Sorcerer", "Divine Soul")
        # Clockwork Soul: Trance of Order — 14th level, 1 free use per
        # long rest, reusable by spending 5 sorcery points (a separate,
        # already-tracked pool).
        if sorc_lvl >= 14 and _has("Sorcerer", "clockwork"):
            _add("Trance of Order", "trance_of_order", "LR",
                 1, "uses",
                 "Bonus action, 1 minute: attack rolls against you can't have advantage, "
                 "treat a roll of 9 or lower on any d20 as a 10. Free 1/LR, or spend 5 "
                 "sorcery points to use again",
                 "Sorcerer", "Clockwork Soul")
        # Shadow Magic: Umbral Form — 18th level, no free use at all,
        # purely gated by spending 6 sorcery points each time (a separate,
        # already-tracked pool) — nominal high count for the same reason
        # as Otherworldly Wings above.
        if sorc_lvl >= 18 and _has("Sorcerer", "shadow"):
            _add("Umbral Form", "umbral_form", "LR",
                 99, "uses",
                 "Bonus action, spend 6 sorcery points: become a shadowy form for 1 minute — "
                 "resistance to all damage except force, move through creatures/objects as "
                 "difficult terrain",
                 "Sorcerer", "Shadow Magic")

    # ── Ranger ────────────────────────────────────────────────────────────────
    ranger_lvl = class_levels.get("Ranger", 0)
    if ranger_lvl > 0:
        # Drakewarden: Drake Companion can't be summoned more than once per long rest.
        if _has("Ranger", "drakewarden"):
            _add("Drake Companion (summon)", "drake_companion_summon", "LR",
                 1, "uses",
                 "Summon your drake companion if it isn't already out",
                 "Ranger", "Drakewarden")
        # Swarmkeeper: Gathered Swarm (passive, once/turn) and Writhing Tide
        # (7th level, a genuine 1-min toggleable transformation — this
        # comment used to reference it but only Gathered Swarm was ever
        # actually added as a resource).
        if _has("Ranger", "swarmkeeper"):
            _add("Gathered Swarm", "gathered_swarm", "SR",
                 1, "uses_per_turn",
                 "Move swarm to move you 5 ft or deal 1d6 piercing or push 15 ft after attack",
                 "Ranger", "Swarmkeeper")
        if ranger_lvl >= 7 and _has("Ranger", "swarmkeeper"):
            _add("Writhing Tide", "writhing_tide", "LR",
                 max(1, pb), "uses",
                 "Bonus action: fly speed 10 ft (can hover) for 1 minute or until incapacitated",
                 "Ranger", "Swarmkeeper")

    # ── Artificer ─────────────────────────────────────────────────────────────
    art_lvl = class_levels.get("Artificer", 0)
    if art_lvl > 0:
        # Flash of Genius (Core, 7th level): add INT mod to an ability
        # check or saving throw you or a creature within 30 ft makes.
        if art_lvl >= 7:
            _add("Flash of Genius", "flash_of_genius", "LR",
                 max(1, ability_mods.get("INT", 0)), "uses",
                 "Add INT mod to an ability check/save you or a creature within 30 ft makes",
                 "Artificer", "")
        # Armorer (Guardian model only): Defensive Field — a
        # proficiency-bonus-limited use count. Gated on the character's
        # actual armor model choice, not just "is an Armorer" —
        # Infiltrator-model characters don't have this at all.
        if _has("Artificer", "armorer"):
            model_picks = (choices or {}).get("armorer_model_3", [])
            if any("guardian" in p.lower() for p in model_picks):
                _add("Defensive Field", "defensive_field", "LR",
                     pb, "uses",
                     "Bonus action: gain temp HP = your Artificer level, replacing any you have. "
                     "Lost if you doff the armor.",
                     "Artificer", "Armorer")
        # Artillerist: Eldritch Cannon
        if _has("Artificer", "artillerist"):
            _add("Eldritch Cannon", "eldritch_cannon", "LR",
                 1, "uses",
                 "Summon flamethrower/force ballista/protector (or spend a spell slot for an extra); "
                 "Fortified Position (15th level) lets you maintain two at once",
                 "Artificer", "Artillerist")
        # Battle Smith: Steel Defender
        if _has("Artificer", "battle smith"):
            defender_ac = 17 if art_lvl >= 15 else 15  # Improved Defender: +2 AC at 15th
            _add("Steel Defender", "steel_defender", "LR",
                 1, "uses",
                 f"AC={defender_ac} (natural armor), HP={2+ability_mods.get('INT',0)+art_lvl*5}",
                 "Artificer", "Battle Smith")
            # Arcane Jolt (9th level): when you or your Steel Defender hits
            # with a weapon attack, channel energy for extra damage or
            # healing (4d6 instead of 2d6 from Improved Defender, 15th).
            if art_lvl >= 9:
                die = "4d6" if art_lvl >= 15 else "2d6"
                _add("Arcane Jolt", "arcane_jolt", "LR",
                     max(1, ability_mods.get("INT", 0)), "uses",
                     f"When you hit with a magic weapon attack, or your Steel Defender hits: extra "
                     f"{die} force damage, or restore {die} HP to a creature/object within 30 ft. "
                     f"Max once per turn.",
                     "Artificer", "Battle Smith")
        # Alchemist: Experimental Elixirs — level-based count (1 from 3rd,
        # 2 from 6th, 3 from 15th). Previously incorrectly used INT
        # modifier as the count, which has nothing to do with the real
        # scaling at all.
        if _has("Artificer", "alchemist"):
            elixir_count = 3 if art_lvl >= 15 else 2 if art_lvl >= 6 else 1
            _add("Experimental Elixirs", "elixirs", "LR",
                 elixir_count, "pool",
                 f"{elixir_count} free elixirs per LR; extra with spell slot",
                 "Artificer", "Alchemist")


def compute_hit_points(class_levels: dict, con_mod: int,
                       use_average: bool = True) -> dict:
    """
    Compute HP for a multiclassed character.
    First class level always gets max HD value.
    Subsequent levels get average (floor(HD/2)+1) or can be rolled.
    """
    from dnd_app.data.classes import CLASS_DICT

    total_level = sum(class_levels.values())
    if total_level == 0:
        return {"base": 0, "con_bonus": 0, "total": 0, "breakdown": []}

    breakdown = []
    base_hp = 0
    first = True

    # Sort by HD descending — most common convention is to use highest HD class first
    sorted_classes = sorted(class_levels.items(), key=lambda x: CLASS_DICT.get(x[0], {}).get("hit_die", 8), reverse=True)

    for cls_name, level in sorted_classes:
        if level <= 0:
            continue
        cls = CLASS_DICT.get(cls_name)
        hd = cls["hit_die"] if cls else 8
        avg_per_level = hd // 2 + 1  # floor(HD/2) + 1

        if first:
            # First level of entire character: max HD
            class_hp = hd + avg_per_level * (level - 1)
            breakdown.append(f"{cls_name} {level}: {hd} (max) + {avg_per_level}×{level-1}")
            first = False
        else:
            class_hp = avg_per_level * level
            breakdown.append(f"{cls_name} {level}: {avg_per_level}×{level}")

        base_hp += class_hp

    con_bonus = con_mod * total_level
    total = base_hp + con_bonus

    return {
        "base": base_hp,
        "con_bonus": con_bonus,
        "total": total,
        "breakdown": breakdown,
        "total_level": total_level,
    }


def get_extra_attacks(class_levels: dict, subclasses: dict = None, char: dict = None) -> int:
    """
    Compute total Extra Attacks per Attack action.
    Per 2024 rules: Extra Attack does NOT stack between classes.
    Exception: Fighter's 'Two Extra Attacks' (lvl 11) and 'Three Extra Attacks' (lvl 20)
    are unique features that replace, not stack.
    Returns total attacks per Attack action (minimum 1).
    """
    if subclasses is None:
        subclasses = {}

    max_attacks = 1
    fighter_lvl = class_levels.get("Fighter", 0)
    monk_lvl = class_levels.get("Monk", 0)

    # Thirsting Blade (Eldritch Invocation, requires Pact of the Blade,
    # 5th level): grants Extra Attack to Warlocks, who otherwise never
    # get it at all. Needs char directly since invocations live there,
    # not in class_levels/subclasses.
    if char is not None and class_levels.get("Warlock", 0) >= 5:
        if any("thirsting blade" in i.lower() for i in char.get("eldritch_invocations", [])):
            max_attacks = max(max_attacks, 2)

    # Fighter is the class with escalating Extra Attacks (PHB p.72):
    # 2 attacks at 5th level, 3 at 11th, 4 at 20th. There is no breakpoint at 17th.
    if fighter_lvl >= 20:
        max_attacks = max(max_attacks, 4)
    elif fighter_lvl >= 11:
        max_attacks = max(max_attacks, 3)
    elif fighter_lvl >= 5:
        max_attacks = max(max_attacks, 2)

    # Other classes with Extra Attack at 5th level (standard martial
    # progression — Barbarian, Paladin, Ranger, Monk, Blood Hunter,
    # Artificer all get it unconditionally at this level).
    for cls_name, level in class_levels.items():
        if cls_name == "Fighter":
            continue
        if level >= 5 and cls_name in {
            "Barbarian", "Paladin", "Ranger", "Monk", "Blood Hunter", "Artificer"
        }:
            max_attacks = max(max_attacks, 2)

    # Bard's Extra Attack is subclass-specific (College of Valor or
    # College of Swords only) and granted at 6th level, not 5th.
    bard_lvl = class_levels.get("Bard", 0)
    if bard_lvl >= 6:
        bard_sub = subclasses.get("Bard", "").lower()
        if "valor" in bard_sub or "swords" in bard_sub:
            max_attacks = max(max_attacks, 2)

    return max_attacks


def sneak_attack_dice(rogue_levels: int) -> str:
    """Returns sneak attack dice string for given Rogue levels."""
    dice = (rogue_levels + 1) // 2
    return f"{dice}d6" if dice > 0 else "None"


def get_saving_throw_profs(class_levels: dict) -> set:
    """Return union of all saving throw proficiencies across classes."""
    from dnd_app.data.classes import CLASS_DICT
    profs = set()
    for cls_name, level in class_levels.items():
        if level <= 0:
            continue
        cls = CLASS_DICT.get(cls_name)
        if cls:
            profs.update(cls.get("save_profs", []))
    return profs


def get_armor_profs(class_levels: dict) -> str:
    """Summarize armor proficiencies across all classes."""
    from dnd_app.data.classes import CLASS_DICT
    all_profs = []
    for cls_name, level in class_levels.items():
        if level <= 0:
            continue
        cls = CLASS_DICT.get(cls_name)
        if cls:
            armor = cls.get("armor", "None")
            if armor and armor != "None":
                all_profs.append(f"{cls_name}: {armor}")
    return "; ".join(all_profs) if all_profs else "None"


def get_skill_choices_for_class(cls_name: str) -> tuple[list, int]:
    """Return (skill_choices_list, count) for a class."""
    from dnd_app.data.classes import CLASS_DICT
    cls = CLASS_DICT.get(cls_name)
    if not cls:
        return [], 0
    return cls.get("skill_choices", []), cls.get("skill_count", 0)


def build_character_summary(class_levels: dict, ability_scores: dict,
                             subclasses: dict = None) -> dict:
    """
    Build a full computed summary for a multiclassed character.
    Returns dict with all derived values.
    """
    if subclasses is None:
        subclasses = {}

    total_level = sum(class_levels.values())
    pb = prof_bonus(total_level)
    con_mod = (ability_scores.get("CON", 10) - 10) // 2

    slot_info = compute_all_spell_slots(class_levels, subclasses)
    resources = aggregate_resources(class_levels, ability_scores, subclasses)
    hp_info = compute_hit_points(class_levels, con_mod)
    save_profs = get_saving_throw_profs(class_levels)
    extra_attacks = get_extra_attacks(class_levels, subclasses)

    prereq_check = {}
    for cls_name in class_levels:
        ok, reason = check_multiclass_prereq(cls_name, ability_scores)
        prereq_check[cls_name] = {"meets": ok, "reason": reason}

    return {
        "total_level": total_level,
        "proficiency_bonus": pb,
        "hp": hp_info,
        "spell_slots": slot_info["spell_slots"],
        "combined_caster_level": slot_info["combined_caster_level"],
        "warlock_slots": slot_info["warlock_slots"],
        "has_spellcasting": slot_info["has_spellcasting"],
        "has_pact_magic": slot_info["has_pact_magic"],
        "resources": resources,
        "save_profs": list(save_profs),
        "extra_attacks": extra_attacks,
        "prereq_check": prereq_check,
        "slot_note": slot_info["note"],
    }
