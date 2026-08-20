"""
Builder module.

Auto-applies grants from race, background, and class selections. Call
rebuild(char) whenever race/background/class changes to re-derive all
automatically-granted proficiencies, ASIs, skill profs, and bonus
spells.

Separates:
  - GRANTED (automatic, from race/bg/class)  -> stored in char['_grants']
  - CHOSEN   (player decision, skill picks etc) -> stored in char['_choices']

dnd_app.core.calculator then uses both when computing totals.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from .character import ability_mod, total_level
from dnd_app.data.backgrounds import get_background

ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]

RACE_SKILL_GRANTS = {
    "Elf":          ["Perception"],   # covers every Elf subrace (High/Wood/Drow/Eladrin/Sea/Shadar-kai/Pallid/Mark of Shadow) — the lookup is by species alone, not combined with subrace
    "Astral Elf":   ["Perception"],   # separate top-level race, not an Elf subrace, but has its own Keen Senses trait
    "Half-Elf":     [],          # player picks 2 — handled via choice
    "Half-Orc":     ["Intimidation"],
    "Gnome":        [],
    "Dwarf":        [],
}

RACE_TOOL_GRANTS = {
    "Dwarf":          ["choice:smith's tools,brewer's supplies,mason's tools"],
    "Mountain Dwarf": ["choice:smith's tools,brewer's supplies,mason's tools"],
    "Hill Dwarf":     ["choice:smith's tools,brewer's supplies,mason's tools"],
}

BACKGROUND_SKILL_CHOICES = {
    # backgrounds that let you pick from a broad list
}

def get_race_asi(race_name: str) -> dict:
    from dnd_app.data.races import RACE_DICT
    race = RACE_DICT.get(race_name, {})
    return dict(race.get("asi", {}))

def get_race_skills(race_name: str) -> list:
    """Return skill proficiencies granted automatically by race."""
    return list(RACE_SKILL_GRANTS.get(race_name, []))

def get_background_skills(bg_name: str) -> list:
    """Return the 2 skill proficiencies granted by a background."""
    from dnd_app.data.backgrounds import get_background
    bg = get_background(bg_name)
    if not bg:
        return []
    return list(bg.get("skills", []))

def get_background_tools(bg_name: str) -> list:
    from dnd_app.data.backgrounds import get_background
    bg = get_background(bg_name)
    if not bg:
        return []
    return list(bg.get("tools", []))

def get_class_save_profs(class_name: str, edition: str = "2014") -> list:
    """Return the two saving throw proficiencies for a class."""
    if edition == "2024":
        from dnd_app.data.classes_2024 import CLASS_DICT_2024 as D
    else:
        from dnd_app.data.classes import CLASS_DICT as D
    cls = D.get(class_name, {})
    return list(cls.get("save_profs", []))

def get_class_armor_profs(class_name: str, edition: str = "2014") -> str:
    if edition == "2024":
        from dnd_app.data.classes_2024 import CLASS_DICT_2024 as D
    else:
        from dnd_app.data.classes import CLASS_DICT as D
    cls = D.get(class_name, {})
    return cls.get("armor", "") or ""

def get_class_weapon_profs(class_name: str, edition: str = "2014") -> str:
    if edition == "2024":
        from dnd_app.data.classes_2024 import CLASS_DICT_2024 as D
    else:
        from dnd_app.data.classes import CLASS_DICT as D
    cls = D.get(class_name, {})
    return cls.get("weapons", "") or ""

# Unlike armor and weapon proficiencies, which have a working getter
# function wired into rebuild() below, tool proficiencies are applied
# here — e.g. a Rogue's "Thieves' tools" entry in the class dict.
# The "of your choice" portions (Bard's 3 musical instruments,
# Monk's and Artificer's one remaining artisan's-tool-or-instrument
# pick) are handled as a real player choice card instead, via
# CLASS_TOOL_CHOICES in levelup_panel.py.
_CLASS_FIXED_TOOL_PROFS = {
    "Rogue": ["Thieves' tools"],
    "Druid": ["Herbalism kit"],
    "Artificer": ["Thieves' tools", "Tinker's tools"],
}

def get_class_tool_profs(class_name: str, edition: str = "2014") -> list:
    return list(_CLASS_FIXED_TOOL_PROFS.get(class_name, []))

def get_class_skill_pool(class_name: str, edition: str = "2014") -> tuple:
    """Return (skill_pool: list, skill_count: int) for the class."""
    if edition == "2024":
        from dnd_app.data.classes_2024 import CLASS_DICT_2024 as D
    else:
        from dnd_app.data.classes import CLASS_DICT as D
    cls = D.get(class_name, {})
    pool = cls.get("skill_choices", [])
    count = cls.get("skill_count", 2)
    return pool, count

def get_level_gains(class_name: str, level: int, edition: str = "2014") -> list:
    """Return list of things gained at this exact level (not cumulative)."""
    if edition == "2024":
        from dnd_app.data.classes_2024 import CLASS_DICT_2024 as D
    else:
        from dnd_app.data.classes import CLASS_DICT as D
    cls = D.get(class_name, {})
    choices = cls.get("level_choices", {})
    features = cls.get("features", {})
    
    gains = []
    for feat_name in features.get(level, []):
        gains.append({"type": "feature", "name": feat_name})
    for choice_text in choices.get(level, []):
        gains.append({"type": "choice", "text": choice_text})
    return gains

def _get_subrace_asi(race_name: str, subrace_name: str) -> dict:
    """Parse subrace ASI from string like 'Hill (+CON 2, +WIS 1, Dwarven Toughness)'."""
    import re as _re
    from dnd_app.data.races import RACE_DICT
    rdata = RACE_DICT.get(race_name, {})
    for sub_str in rdata.get("subraces", []):
        name = sub_str.split("(")[0].strip()
        if name.lower() == subrace_name.lower():
            inner = sub_str[sub_str.find("(")+1:sub_str.rfind(")")]
            return {ab: int(n) for ab, n in _re.findall(r"\+([A-Z]{3})\s+(\d+)", inner)}
    return {}

def rebuild(char: dict) -> None:
    """
    Re-derive all automatically-granted properties from race/background/class.
    Writes into char['_grants'] — a dict of auto-applied values.
    Does NOT overwrite user choices stored in char['_choices'].
    Then merges grants + choices into the live char fields.
    """
    edition = char.get("edition", "2014")
    race_name = char.get("species") or char.get("race", "")
    bg_name = char.get("background", "")
    classes = char.get("classes", [])

    grants = {
        "skill_profs": [],      # skills granted (no choice needed)
        "skill_prof_set": set(),
        "save_profs": set(),
        "asi": {ab: 0 for ab in ABILITIES},
        "armor_profs": [],
        "weapon_profs": [],
        "tool_profs": [],
        "languages": ["Common"],
        "hp_die": {},           # {class_name: hit_die}
    }

    # ── 2024 background origin feat ──────────────────────────────────────────
    # 2024 PHB backgrounds each grant exactly one origin feat. We auto-add the
    # base feat name to char["feats"] (same list ordinary chosen feats live
    # in, so it renders with full mechanics via the existing Feats section
    # and participates in ASI/flex-ASI resolution normally). Tracked via
    # _auto_origin_feat so switching backgrounds swaps the feat instead of
    # accumulating one per background ever selected.
    bg_data = get_background(bg_name)
    origin_feat_full = bg_data.get("origin_feat", "") if bg_data else ""
    origin_base = origin_feat_full.split("(")[0].strip() if origin_feat_full else ""
    prev_auto = char.get("_auto_origin_feat", "")
    feats_list = char.setdefault("feats", [])
    if prev_auto and prev_auto != origin_base and prev_auto in feats_list:
        feats_list.remove(prev_auto)
    if origin_base and origin_base not in feats_list:
        feats_list.append(origin_base)
    char["_auto_origin_feat"] = origin_base
    char["origin_feat"] = origin_feat_full   # full string incl. suggested list, e.g. "Magic Initiate (Cleric)"

    # ── Background feat choice (Rewarded / Ruined BOMT, etc.) ─────────────────
    # Parallel to origin_feat, but player-selected from feat_choices on the
    # background. Tracked via _auto_bg_feat so swapping backgrounds swaps
    # the feat instead of stacking.
    bg_feat = ""
    if bg_data:
        allowed = bg_data.get("feat_choices") or []
        chosen = char.get("_choices", {}).get("background_feat", "")
        if allowed and chosen in allowed:
            bg_feat = chosen
    prev_bg_feat = char.get("_auto_bg_feat", "")
    if prev_bg_feat and prev_bg_feat != bg_feat and prev_bg_feat in feats_list:
        feats_list.remove(prev_bg_feat)
    if bg_feat and bg_feat not in feats_list:
        feats_list.append(bg_feat)
    char["_auto_bg_feat"] = bg_feat

    # ── Race grants ───────────────────────────────────────────────────────────
    if race_name:
        # ASI — subrace string defines the COMPLETE bonus (it includes the base race bonus).
        # When a subrace is chosen, use its ASI directly. Without a subrace, use the base race ASI.
        race_asi = get_race_asi(race_name)
        subrace_name = char.get("subrace", "")
        if subrace_name:
            sub_asi = _get_subrace_asi(race_name, subrace_name)
            if sub_asi:
                race_asi = sub_asi   # subrace string encodes the TOTAL, not an addend
        tashas_reassign = char.get("_choices", {}).get("tashas_asi_reassign", {})
        if tashas_reassign:
            # Use player's redistribution instead of fixed racial ASI.
            # The total points must equal the original pool (validated in wizard).
            for ab, val in tashas_reassign.items():
                grants["asi"][ab] = grants["asi"].get(ab, 0) + val
        else:
            for ab, val in race_asi.items():
                grants["asi"][ab] = grants["asi"].get(ab, 0) + val

        # Auto-granted skills
        for skill in get_race_skills(race_name):
            if skill not in grants["skill_prof_set"]:
                grants["skill_profs"].append(skill)
                grants["skill_prof_set"].add(skill)

    # ── Background grants ─────────────────────────────────────────────────────
    if bg_name:
        # Apply starting gold from background equipment string (first time only)
        from dnd_app.data.backgrounds import get_background as _get_bg
        import re as _re_bg
        _bg = _get_bg(bg_name) or {}
        _equip = _bg.get("equipment","")
        _m = _re_bg.search(r"(\d+)\s*gp", _equip, _re_bg.IGNORECASE)
        if _m and not char.get("_bg_gold_applied"):
            _gp = int(_m.group(1))
            _cur = char.setdefault("currency",{})
            if not _cur.get("gp"):          # only if player hasn't set it
                _cur["gp"] = _gp
            char["_bg_gold_applied"] = True
        for skill in get_background_skills(bg_name):
            if skill not in grants["skill_prof_set"]:
                grants["skill_profs"].append(skill)
                grants["skill_prof_set"].add(skill)
        for tool in get_background_tools(bg_name):
            grants["tool_profs"].append(tool)

    # ── Class grants ──────────────────────────────────────────────────────────
    for i, cls_entry in enumerate(classes):
        cname = cls_entry.get("class", "")
        clvl  = cls_entry.get("level", 1)
        hd    = cls_entry.get("hit_die", 8)
        grants["hp_die"][cname] = hd

        # Save profs: only from first class (multiclass doesn't add save profs)
        if i == 0:
            for ab in get_class_save_profs(cname, edition):
                grants["save_profs"].add(ab)

        # Armor / weapon profs (only first class; multiclass has reduced list)
        if i == 0:
            ap = get_class_armor_profs(cname, edition)
            if ap: grants["armor_profs"].append(ap)
            wp = get_class_weapon_profs(cname, edition)
            if wp: grants["weapon_profs"].append(wp)

        # Class-granted fixed tool proficiencies (Rogue's Thieves' tools,
        # Druid's Herbalism kit, Artificer's Thieves'/Tinker's tools).
        # Per the real multiclassing proficiencies table, Rogue and
        # Artificer grant their tools even as a secondary/multiclass
        # entry, but Druid's Herbalism kit is only part of Druid's
        # primary-class grant, not its multiclass grant — so Druid stays
        # gated to i==0 while Rogue/Artificer apply for every class entry.
        if i == 0 or cname in ("Rogue", "Artificer"):
            for tool in get_class_tool_profs(cname, edition):
                grants["tool_profs"].append(tool)

        # Hex Warrior (Warlock, The Hexblade, 1st level): proficiency with
        # medium armor, shields, and martial weapons. Previously missing
        # entirely — a Hexblade had no way to gain these at all.
        if cname == "Warlock" and "hexblade" in cls_entry.get("subclass", "").lower():
            grants["armor_profs"].append("Medium armor, shields")
            grants["weapon_profs"].append("Martial weapons")

        # Cleric Divine Domain 1st-level armor/weapon proficiency
        # grants — covers every domain that grants one (e.g. Life
        # Domain's heavy armor proficiency).
        if cname == "Cleric":
            cleric_sub = cls_entry.get("subclass", "").lower()
            heavy_armor_domains = ("life domain", "nature domain", "tempest domain", "war domain",
                                   "forge domain", "order domain", "twilight domain",
                                   "solidarity domain", "strength domain", "zeal domain")
            martial_weapon_domains = ("tempest domain", "war domain", "order domain",
                                      "twilight domain", "zeal domain")
            if any(d in cleric_sub for d in heavy_armor_domains):
                grants["armor_profs"].append("Heavy armor")
            if any(d in cleric_sub for d in martial_weapon_domains):
                grants["weapon_profs"].append("Martial weapons")

    # ── Feats with a FIXED (non-player-chosen) proficiency grant ─────────────
    # Feats granting a player-CHOSEN proficiency (Weapon Master, Skilled,
    # Skill Expert, Prodigy, Artificer Initiate) need UI selection support
    # and aren't covered by this fixed table.
    FEAT_FIXED_ARMOR_PROFS = {
        "Heavily Armored": "Heavy armor",
        "Lightly Armored": "Light armor",
        "Moderately Armored": "Medium armor, shields",
    }
    FEAT_FIXED_WEAPON_PROFS = {
        "Gunner": "Firearms",
    }
    FEAT_FIXED_TOOL_PROFS = {
        "Chef": "Cook's utensils",
        "Poisoner": "Poisoner's kit",
    }
    for fname in feats_list:
        if fname in FEAT_FIXED_ARMOR_PROFS:
            grants["armor_profs"].append(FEAT_FIXED_ARMOR_PROFS[fname])
        if fname in FEAT_FIXED_WEAPON_PROFS:
            grants["weapon_profs"].append(FEAT_FIXED_WEAPON_PROFS[fname])
        if fname in FEAT_FIXED_TOOL_PROFS:
            grants["tool_profs"].append(FEAT_FIXED_TOOL_PROFS[fname])

    # Spirit Medium (DM Reward): proficiency bonus to checks with a
    # custom divining tool — functionally identical to tool proficiency.
    if "Spirit Medium" in char.get("dm_rewards", []):
        grants["tool_profs"].append("Divining Tool (Spirit Medium)")

    # Weapon Master: 4 player-chosen weapons — read fresh from _choices
    # every rebuild (weapon_proficiencies is fully overwritten from grants
    # below, so a one-time application elsewhere would be wiped on the
    # next refresh). Reuses has_weapon_proficiency()'s existing named-
    # weapon substring matching, so no changes needed there.
    if "Weapon Master" in feats_list:
        chosen_weapons = char.get("_choices", {}).get("feat_weapon_master_weapons", [])
        for wname in chosen_weapons:
            grants["weapon_profs"].append(wname)

    # ── Write grants back to char ─────────────────────────────────────────────
    char["_grants"] = grants

    # Apply saving throw profs (grants only — user can override in _choices)
    choices = char.get("_choices", {})
    all_save_profs = set(grants["save_profs"]) | set(choices.get("extra_save_profs", []))
    for ab in ABILITIES:
        char["saving_throws"][ab] = ab in all_save_profs

    # Rebuild ability_bonuses from scratch each call to avoid double-add
    base_bonuses = {ab: 0 for ab in ABILITIES}
    # 1. Race ASI
    for ab, val in grants["asi"].items():
        base_bonuses[ab] = base_bonuses.get(ab,0) + val
    # 2. Per-ASI-choice entries: stored as Fighter_asi_4=[asi:STR:2] etc.
    for key, vals in choices.items():
        if isinstance(vals, list) and any(isinstance(v,str) and v.startswith("asi:") for v in vals):
            for item in vals:
                if isinstance(item,str) and item.startswith("asi:"):
                    _, ab, val = item.split(":")
                    base_bonuses[ab] = base_bonuses.get(ab,0) + int(val)
    # Compute per-ability caps BEFORE clamping:
    #   Normal cap: 20 (PHB p.173)
    #   Barbarian Lv20 Primal Champion: STR and CON cap raised to 24
    #   Magic items that SET a score (Gauntlets, Belt of Giant Strength etc.)
    #     use ability_overrides and are applied AFTER builder — they bypass this cap.
    primal_champion = (
        any(c.get("class") == "Barbarian" and c.get("level", 0) >= 20 for c in classes)
    )
    for ab in ABILITIES:
        # Determine the effective cap for this ability
        if primal_champion and ab in ("STR", "CON"):
            cap = 24  # Primal Champion raises STR/CON max to 24
        else:
            cap = 20
        # Defensive clamp on the base score itself, not just the bonus on
        # top of it — the check below only ever protected against
        # base+bonus exceeding the cap, never an oversized base score
        # sneaking in from another source (a loaded/edited save file, a
        # different UI entry path, etc.).
        if char["abilities"].get(ab, 10) > cap:
            char["abilities"][ab] = cap
        base  = char["abilities"].get(ab, 10)
        bonus = base_bonuses.get(ab, 0)
        if base + bonus > cap:
            base_bonuses[ab] = max(0, cap - base)

    # Apply Primal Champion flat bonus (+4 STR/CON) as part of ability_bonuses
    if primal_champion:
        for ab in ("STR", "CON"):
            base = char["abilities"].get(ab, 10)
            cap  = 24
            current_bonus = base_bonuses.get(ab, 0)
            # Add the Primal Champion +4, capped at 24
            primal_bonus = min(4, cap - base - current_bonus)
            if primal_bonus > 0:
                base_bonuses[ab] = current_bonus + primal_bonus

    char["ability_bonuses"] = base_bonuses

    # Apply skill profs: grants set level to 2 (proficient), but don't DOWNGRADE
    # user choices that are set to 3 (expertise)
    for skill in grants["skill_profs"]:
        current = char["skills"].get(skill, 0)
        if current < 2:
            char["skills"][skill] = 2

    # Apply chosen skill profs from _choices
    for skill in choices.get("class_skill_profs", []):
        current = char["skills"].get(skill, 0)
        if current < 2:
            char["skills"][skill] = 2

    # Apply chosen skill expertise from _choices — completes the same
    # root-cause fix as class_skill_profs above, so expertise choices
    # made through the normal UI flow are actually re-derivable.
    for skill in choices.get("class_skill_expertise", []):
        char["skills"][skill] = 3

    # Apply proficiency lists for display
    char["armor_proficiencies"]  = grants["armor_profs"]
    char["weapon_proficiencies"] = grants["weapon_profs"]
    char["tool_proficiencies"]   = grants["tool_profs"] + choices.get("tool_profs", [])
    # Spirit Medium (DM reward): fixed, automatic proficiency with a
    # custom divining tool (spirit board, tarokka deck, etc. — the
    # player's flavor choice doesn't change the mechanic).
    if "Spirit Medium" in char.get("dm_rewards", []) and "Divining Tool (Spirit Medium)" not in char["tool_proficiencies"]:
        char["tool_proficiencies"].append("Divining Tool (Spirit Medium)")
    char["languages"] = list(set(grants["languages"] + choices.get("extra_languages", ["Common"])
                                  + choices.get("knowledge_domain_languages", [])))
    # Littlest Yeti (DM reward): fixed, automatic "speak Yeti" grant —
    # not a player choice like most other language grants in this app.
    if "Littlest Yeti" in char.get("dm_rewards", []) and "Yeti" not in char["languages"]:
        char["languages"].append("Yeti")

    # ── Class feature mechanics ────────────────────────────────────────────────
    _apply_class_feature_mechanics(char, classes, edition)

    # ── Bonus spells (domain spells, circle spells, etc.) ──────────────────
    # These are always known/prepared once you reach the required
    # level. Tracked separately in char["bonus_spells"] so the UI can
    # badge them distinctly and so they're never mistaken for (or
    # overwritten by) the player's own chosen known/prepared spells.
    from dnd_app.data.spells import get_bonus_spells
    old_bonus = set(char.get("bonus_spells", []))
    bonus = get_bonus_spells(char)
    char["bonus_spells"] = bonus
    # Remove any spell that WAS bonus-granted but no longer is (e.g. switching
    # Circle of the Land terrain) — otherwise stale spells from the previous
    # choice stick around forever. Small accepted risk: if a player also
    # separately hand-picked the exact same spell name, this could remove
    # that too, since spells_known/prepared don't track provenance per-entry.
    stale = old_bonus - set(bonus)
    if stale:
        char["spells_known"] = [s for s in char.get("spells_known", []) if s not in stale]
        char["spells_prepared"] = [s for s in char.get("spells_prepared", []) if s not in stale]
    for sp in bonus:
        if sp not in char.get("spells_known", []):
            char.setdefault("spells_known", []).append(sp)
        if sp not in char.get("spells_prepared", []):
            char.setdefault("spells_prepared", []).append(sp)

    # ── Full-list prepared casters: Cleric, Druid, Paladin, Artificer ──────
    # These classes don't "learn" a limited set of LEVELED spells at all —
    # per their real text ("You prepare the list of [class] spells...
    # choosing from the [class] spell list"), the entire leveled-spell list
    # is available every day, and preparing a subset of it is the only
    # choice involved. So leveled spells are auto-populated into
    # spells_known here. Cantrips are different: these classes know only a
    # small, limited number of cantrips (2 for a 1st-level Druid, not all
    # 18+ on the list), chosen by the player the same way a known-caster
    # picks their spells — so cantrips are NOT auto-granted here at all;
    # the player adds them via the spell browser's "+ Add to My Spells"
    # button, which already enforces the correct per-class cantrip cap
    # (see _all_caster_classes/_add_spell_from_browser in sheet.py).
    #
    # The max leveled-spell level each class can access must be computed
    # from THAT CLASS'S OWN individual level, not the combined multiclass
    # spell-slot table — 5e multiclass rules determine what a class can
    # prepare "as if you were a single-classed member of that class" (PHB
    # p.164), even though the slots used to actually CAST are shared. Using
    # the combined table here was letting e.g. a 1st-level Paladin (not
    # even a spellcaster yet on its own) multiclassed with a high-level
    # Sorcerer gain access to 2nd-level Paladin spells, since the combined
    # pool crossed that threshold even though Paladin's own level didn't.
    from dnd_app.data.spells import spells_for_class
    from dnd_app.core.multiclass import (get_multiclass_spell_slots,
                                          FULL_CASTERS, HALF_CASTERS, ARTIFICER_CLASSES)
    FULL_LIST_CLASSES = ("Cleric", "Druid", "Paladin", "Artificer")
    cl_now = {c.get("class",""): c.get("level",0) for c in char.get("classes", [])}
    subs_now = {c.get("class",""): c.get("subclass","") for c in char.get("classes", [])}
    for cname in FULL_LIST_CLASSES:
        lvl = cl_now.get(cname, 0)
        if lvl <= 0:
            continue
        if cname in FULL_CASTERS:
            own_caster_lvl = lvl
        elif cname in HALF_CASTERS or cname in ARTIFICER_CLASSES:
            own_caster_lvl = lvl // 2
        else:
            own_caster_lvl = 0
        own_slots = get_multiclass_spell_slots(own_caster_lvl)
        max_lvl = 0
        for i, count in enumerate(own_slots):
            if count > 0:
                max_lvl = i + 1
        for sp in spells_for_class(cname):
            if sp.get("level", 0) > 0 and sp["level"] <= max_lvl:
                if sp["name"] not in char.get("spells_known", []):
                    char.setdefault("spells_known", []).append(sp["name"])

    # ── Known casters: Sorcerer, Bard, Warlock, Ranger, and Eldritch
    # Knight/Arcane Trickster's limited Wizard-list spells ─────────────────
    # These classes choose a small, fixed number of spells known, and once
    # a spell is known it's simply usable — there's no separate daily
    # "prepare a subset of what you know" step distinct from knowing it,
    # unlike Cleric/Druid/Paladin/Artificer above or Wizard's spellbook.
    # So every spell already in spells_known for these classes should
    # always be treated as prepared too, with no player action required.
    KNOWN_CASTER_CLASSES = ("Sorcerer", "Bard", "Warlock", "Ranger")
    is_known_caster_present = any(cl_now.get(c, 0) > 0 for c in KNOWN_CASTER_CLASSES)
    ek_at_present = ("fighter" in " ".join(subs_now.values()).lower() and cl_now.get("Fighter", 0) >= 3
                     and "arcane" in subs_now.get("Fighter", "").lower()) or \
                    ("rogue" in " ".join(subs_now.values()).lower() and cl_now.get("Rogue", 0) >= 3
                     and "arcane" in subs_now.get("Rogue", "").lower())
    if is_known_caster_present or ek_at_present:
        known_caster_spell_names = set()
        for cname in KNOWN_CASTER_CLASSES:
            if cl_now.get(cname, 0) > 0:
                known_caster_spell_names.update(sp["name"] for sp in spells_for_class(cname))
        if ek_at_present:
            known_caster_spell_names.update(sp["name"] for sp in spells_for_class("Wizard"))
        # spells_known also contains every spell from the full-list
        # prepared-caster dump just above (Cleric/Druid/Paladin/
        # Artificer) and separately, Wizard's own spellbook entries.
        # Any spell shared between those and a known-caster class's
        # theoretical full list (e.g. "Bane" is on both Cleric's and
        # Bard's lists; "Fireball" is on both Wizard's and Sorcerer's)
        # must not be auto-marked prepared for free here, since that
        # would bypass the prepared caster's cap. Exclude anything also
        # on ANY of the character's own prepared-caster class lists
        # (all five: Wizard included, not just the four that get a
        # full-list dump), since those always require explicit
        # preparation regardless of what else happens to share the name.
        PREPARED_CASTER_CLASSES = ("Wizard", "Cleric", "Druid", "Paladin", "Artificer")
        prepared_caster_spell_names = set()
        for cname in PREPARED_CASTER_CLASSES:
            if cl_now.get(cname, 0) > 0:
                prepared_caster_spell_names.update(sp["name"] for sp in spells_for_class(cname))
        for sp_name in char.get("spells_known", []):
            if (sp_name in known_caster_spell_names
                    and sp_name not in prepared_caster_spell_names
                    and sp_name not in char.get("spells_prepared", [])):
                char.setdefault("spells_prepared", []).append(sp_name)


def _apply_class_feature_mechanics(char: dict, classes: list, edition: str):
    """Auto-apply mechanical bonuses from class features based on current level."""
    cl_map = {c.get("class",""): c.get("level",0) for c in classes}
    subs   = {c.get("class",""): c.get("subclass","") for c in classes}

    # ── Diamond Soul (Monk 14+): proficient in all saving throws ───────────────
    if cl_map.get("Monk", 0) >= 14:
        for ab in ABILITIES:
            char["saving_throws"][ab] = True

    # ── Slippery Mind (Rogue 15+): WIS save proficiency ───────────────────────
    if cl_map.get("Rogue", 0) >= 15:
        char["saving_throws"]["WIS"] = True

    # ── Otherworldly Glamour (Bard Glamour 3+): CHA to Persuasion ─────────────
    bard_sub = subs.get("Bard", "")
    if cl_map.get("Bard", 0) >= 3 and "glamour" in bard_sub.lower():
        # Persuasion: at least proficient; upgrade to expertise if already prof
        current = char["skills"].get("Persuasion", 0)
        if current < 2:
            char["skills"]["Persuasion"] = 2
        elif current == 2:
            char["skills"]["Persuasion"] = 3  # expertise

    # ── College of Eloquence (Bard 3+): Persuasion & Deception near-perfect ───
    if cl_map.get("Bard", 0) >= 3 and "eloquence" in bard_sub.lower():
        for skill in ["Persuasion", "Deception"]:
            if char["skills"].get(skill, 0) < 2:
                char["skills"][skill] = 2

    # ── Rogue Scout (3+): Survivalist — proficiency in Nature and Survival
    # (if not already had) AND proficiency bonus doubled for both, always —
    # the doubling isn't conditional on already having the skill beforehand.
    rogue_sub = subs.get("Rogue", "")
    if cl_map.get("Rogue", 0) >= 3 and "scout" in rogue_sub.lower():
        for skill in ["Nature", "Survival"]:
            char["skills"][skill] = 3  # expertise, unconditionally

    # ── Ranger Gloom Stalker (7+): Iron Mind — WIS save proficiency, UNLESS
    # already proficient in WIS saves, in which case it becomes a player
    # choice of INT or CHA instead (handled as a chooser below, not here).
    ranger_sub = subs.get("Ranger", "")
    if cl_map.get("Ranger", 0) >= 7 and "gloom stalker" in ranger_sub.lower():
        if not char["saving_throws"].get("WIS"):
            char["saving_throws"]["WIS"] = True
        else:
            pick = char.get("_choices", {}).get("gloom_stalker_iron_mind", [])
            if pick:
                char["saving_throws"][pick[0]] = True

    # ── Bard Tool Expertise (Bard 2+, if applicable) / Lore Bonus Magical Secrets ─
    # No numeric bonus - just flagged in features

    # ── Monk Unarmored Movement speed bonus ───────────────────────────────────
    monk_lvl = cl_map.get("Monk", 0)
    if monk_lvl >= 2:
        speed_bonus = {2:10, 6:15, 10:20, 14:25, 18:30}.get(
            max(l for l in [2,6,10,14,18] if l <= monk_lvl), 10
        )
        # Store monk speed bonus separately so it stacks with base speed
        char["monk_speed_bonus"] = speed_bonus
    else:
        char["monk_speed_bonus"] = 0

    # ── Beguiling Influence invocation: Deception + Persuasion proficiency ────
    chosen_invocations = char.get("eldritch_invocations", [])
    for inv in chosen_invocations:
        inv_lower = inv.lower()
        if "beguiling influence" in inv_lower:
            for skill in ["Deception", "Persuasion"]:
                if char["skills"].get(skill, 0) < 2:
                    char["skills"][skill] = 2
        elif "eldritch mind" in inv_lower:
            char["_eldritch_mind"] = True   # flag for concentration advantage
        elif "armor of shadows" in inv_lower:
            # Mage Armor at will - note it in char for AC calc
            char["_armor_of_shadows"] = True
        elif "devil's sight" in inv_lower or "devil\u2019s sight" in inv_lower:
            char["_devils_sight"] = True

    # ── Primal Champion (Barbarian 20): +4 STR, +4 CON, raises cap to 24 ────────
    # PHB p.50: 'Your STR and CON scores increase by 4. Your maximum for those scores is now 24.'
    # This is a class feature grant, NOT an ASI choice.
    barb_lvl = cl_map.get("Barbarian", 0)
    if barb_lvl >= 20:
        char.setdefault("_primal_champion", True)
    else:
        char["_primal_champion"] = False

    # ── Reliable Talent flag (Rogue 11+) ──────────────────────────────────────
    char["_reliable_talent"] = cl_map.get("Rogue", 0) >= 11

    # ── Jack of All Trades flag (Bard 2+) ─────────────────────────────────────
    char["_jack_of_all_trades"] = cl_map.get("Bard", 0) >= 2

    # ── Paladin Aura of Protection (Pal 6+): +CHA to all saves ────────────────
    # This is handled dynamically in calculator.get_saving_throw_bonus
    # Just store the flag for UI display
    char["_paladin_aura"] = cl_map.get("Paladin", 0) >= 6


def get_choices_needed(char: dict) -> list:
    """
    Return list of pending choices the player still needs to make.
    Each choice: {
        'id': unique string,
        'source': 'race'|'background'|'class',
        'source_name': str,
        'type': 'skill_prof'|'asi'|'spell'|'expertise'|'language'|'feat'|'subclass',
        'count': int,
        'pool': list | None,   (None = free choice from full list)
        'label': str,
        'already_chosen': list,
    }
    """
    edition = char.get("edition", "2014")
    race_name = char.get("species") or char.get("race", "")
    bg_name = char.get("background", "")
    classes = char.get("classes", [])
    choices_made = char.get("_choices", {})
    
    needed = []

    # Note: race-specific skill/tool proficiency choices (Half-Elf,
    # Kenku, and many others) are handled by RACE_SKILL_CHOICES in
    # levelup_panel.py's _get_race_choices(), which is combined with
    # this function's output everywhere it's called — this function
    # deliberately does not duplicate that handling for any race.

    # ── Background choices ────────────────────────────────────────────────────
    # Check if background gives a language choice
    if bg_name:
        from dnd_app.data.backgrounds import get_background
        bg = get_background(bg_name)
        if bg:
            lang_count = bg.get("languages", 0)
            if isinstance(lang_count, int) and lang_count > 0:
                already = choices_made.get("bg_languages", [])
                if len(already) < lang_count:
                    needed.append({
                        "id": "bg_languages",
                        "source": "background", "source_name": bg_name,
                        "type": "language", "count": lang_count,
                        "pool": ["Abyssal","Celestial","Deep Speech","Draconic","Dwarvish",
                                 "Elvish","Giant","Gnomish","Goblin","Halfling","Infernal",
                                 "Orc","Primordial","Sylvan","Undercommon"],
                        "label": f"Choose {lang_count} language(s) ({bg_name})",
                        "already_chosen": already,
                    })

    # ── Class choices ─────────────────────────────────────────────────────────
    for i, cls_entry in enumerate(classes):
        cname = cls_entry.get("class","")
        clvl  = cls_entry.get("level", 1)

        # Skill proficiency picks at level 1
        skill_pool, skill_count = get_class_skill_pool(cname, edition)
        already_skills = choices_made.get(f"{cname}_skill_profs", [])
        
        # Account for multiclass (multiclassing gives 1-2 skills, not full count)
        effective_count = skill_count if i == 0 else _multiclass_skill_count(cname, edition)
        
        if len(already_skills) < effective_count:
            pool_display = skill_pool if skill_pool and skill_pool != ["Any 4 skills"] else None
            needed.append({
                "id": f"{cname}_skill_profs",
                "source": "class", "source_name": cname,
                "type": "skill_prof",
                "count": effective_count,
                "pool": pool_display,
                "label": f"Choose {effective_count} skill proficiencies ({cname})",
                "already_chosen": already_skills,
            })

        # Expertise choices (Rogue lvl1, Bard lvl1+3, etc.)
        if cname == "Rogue":
            for exp_key, exp_lvl, exp_count in [("rogue_expertise_1", 1, 2), ("rogue_expertise_2", 6, 2)]:
                if clvl >= exp_lvl:
                    already_exp = choices_made.get(exp_key, [])
                    if len(already_exp) < exp_count:
                        needed.append({
                            "id": exp_key, "source": "class", "source_name": cname,
                            "type": "expertise", "count": exp_count,
                            "pool": None,
                            "label": f"Choose {exp_count} skills for Expertise ({cname} Lv{exp_lvl})",
                            "already_chosen": already_exp,
                        })
        elif cname == "Bard":
            for exp_key, exp_lvl, exp_count in [("bard_expertise_1", 3, 2), ("bard_expertise_2", 10, 2)]:
                if clvl >= exp_lvl:
                    already_exp = choices_made.get(exp_key, [])
                    if len(already_exp) < exp_count:
                        needed.append({
                            "id": exp_key, "source": "class", "source_name": cname,
                            "type": "expertise", "count": exp_count,
                            "pool": None,
                            "label": f"Choose {exp_count} skills for Expertise ({cname} Lv{exp_lvl})",
                            "already_chosen": already_exp,
                        })

        # ASI choices — one per ASI level
        # ── ASI choices — one per ASI level, but only if not already taken for THAT LEVEL ──
        if edition == "2024":
            from dnd_app.data.classes_2024 import CLASS_DICT_2024 as D
        else:
            from dnd_app.data.classes import CLASS_DICT as D
        
        cls_data = D.get(cname, {})
        lc = cls_data.get("level_choices", {})
        
        # Get all levels that grant ASI/Feat
        # Skip non-integer keys (e.g. 'totem_3', 'land_terrain') — those are subclass-specific
        asi_levels = []
        for lvl, choices_list in lc.items():
            if not isinstance(lvl, int):
                continue          # skip string keys like 'totem_3', 'land_terrain'
            if lvl <= clvl:
                for choice_text in choices_list:
                    if "ASI" in str(choice_text) or "Feat" in str(choice_text):
                        asi_levels.append(lvl)
                        break
                    
        for asi_lvl in asi_levels:
            key = f"{cname}_asi_{asi_lvl}"
            # Check if choice already exists for THIS SPECIFIC LEVEL
            if key not in choices_made:
                needed.append({
                    "id": key,
                    "source": "class",
                    "source_name": cname,
                    "type": "asi_or_feat",
                    "count": 1,
                    "pool": None,
                    "label": f"ASI or Feat ({cname} Lv{asi_lvl})",
                    "already_chosen": [],
                    "lvl": asi_lvl,
                })

    # ── Artificer Infusions ───────────────────────────────────────────────────
    artificer_lvl = 0
    for c in classes:
        if c.get("class") == "Artificer":
            artificer_lvl = c.get("level", 0)
    if artificer_lvl >= 2:
        # PHB Artificer table: 4 known at 2nd level, 6 at 6th, 8 at 10th,
        # 10 at 14th, 12 at 18th. (The old "+2 every 2 levels" formula grew
        # twice as fast as the real table and hit the level-20 cap by 10th.)
        if artificer_lvl >= 18: known_count = 12
        elif artificer_lvl >= 14: known_count = 10
        elif artificer_lvl >= 10: known_count = 8
        elif artificer_lvl >= 6: known_count = 6
        else: known_count = 4
        already_inf = char.get("artificer_infusions", [])
        if len(already_inf) < known_count:
            needed.append({
                "id": "artificer_infusions",
                "source": "class", "source_name": "Artificer",
                "type": "infusion",
                "count": known_count,
                "pool": None,
                "label": f"Choose {known_count} Artificer Infusions Known (Lv{artificer_lvl})",
                "already_chosen": already_inf,
            })

    # ── Pending subclass choices ─────────────────────────────────────────────
    for c in classes:
        cname = c.get("class", "")
        clvl  = c.get("level", 0)
        current_sub = c.get("subclass", "")
        cdata_sub = D.get(cname, {})
        sub_lvl = cdata_sub.get("subclass_level", 3)
        choice_key = f"{cname}_subclass"
        if clvl >= sub_lvl and not current_sub and choice_key not in choices_made:
            from dnd_app.core.character import clean_subclass_name
            subs = cdata_sub.get("subclasses", [])
            sub_displays = [clean_subclass_name(s) for s in subs]
            needed.append({
                "id": choice_key,
                "source": "class",
                "source_name": cname,
                "type": "subclass",
                "count": 1,
                "pool": sub_displays,
                "label": f"Choose {cname} Subclass (unlocked at Level {sub_lvl})",
                "already_chosen": [],
            })

    # ── Blood Hunter: Mutagen Formulas Known picker ───────────────────────────
    blood_hunter_lvl = 0
    bh_sub = ""
    for c in classes:
        if c.get("class") == "Blood Hunter":
            blood_hunter_lvl = c.get("level", 0)
            bh_sub = c.get("subclass", "").lower()
    if blood_hunter_lvl >= 3 and "mutant" in bh_sub:
        from dnd_app.data.classes import MUTAGENS
        # 4 formulas known at 3rd, 5 at 7th, 6 at 11th, 7 at 15th, 8 at 18th.
        if blood_hunter_lvl >= 18: mut_count = 8
        elif blood_hunter_lvl >= 15: mut_count = 7
        elif blood_hunter_lvl >= 11: mut_count = 6
        elif blood_hunter_lvl >= 7: mut_count = 5
        else: mut_count = 4
        # A few formulas need a minimum level to even be learned/consumed —
        # filtered out until the character actually qualifies.
        MUT_LEVEL_GATES = {"Aether": 11, "Cruelty": 11, "Precision": 11, "Reconstruction": 7}
        eligible_mutagens = []
        for mut in MUTAGENS:
            gate_name = next((name for name in MUT_LEVEL_GATES if mut.startswith(name)), None)
            if gate_name and blood_hunter_lvl < MUT_LEVEL_GATES[gate_name]:
                continue
            eligible_mutagens.append(mut)
        already_mut = char.get("_choices", {}).get("blood_hunter_mutagens", [])
        if len(already_mut) < mut_count:
            needed.append({
                "id": "blood_hunter_mutagens",
                "source": "subclass", "source_name": "Order of the Mutant",
                "type": "metamagic",
                "count": mut_count,
                "pool": eligible_mutagens,
                "label": f"Choose {mut_count} Mutagen Formulas Known (Blood Hunter Lv{blood_hunter_lvl})",
                "already_chosen": already_mut,
            })

    # ── Blood Hunter: Blood Curses picker ─────────────────────────────────────
    if blood_hunter_lvl >= 1:
        from dnd_app.data.classes import BLOOD_CURSES
        # 1 known at 1st, 2 at 6th, 3 at 10th, 4 at 14th, 5 at 18th.
        if blood_hunter_lvl >= 18: bc_count = 5
        elif blood_hunter_lvl >= 14: bc_count = 4
        elif blood_hunter_lvl >= 10: bc_count = 3
        elif blood_hunter_lvl >= 6: bc_count = 2
        else: bc_count = 1
        # Filter out order-specific curses the character isn't eligible for
        # yet (right level AND right Order) — everything else is available
        # to any Blood Hunter regardless of Order.
        ORDER_GATES = {
            "Corrosion": (15, "mutant"),
            "Exorcist": (15, "ghostslayer"),
            "Howl": (18, "lycan"),
            "Soul Eater": (18, "profane soul"),
        }
        eligible_curses = []
        for curse in BLOOD_CURSES:
            gate = next((g for name, g in ORDER_GATES.items() if name in curse), None)
            if gate:
                req_lvl, req_order = gate
                if blood_hunter_lvl < req_lvl or req_order not in bh_sub:
                    continue
            eligible_curses.append(curse)
        already_bc = char.get("_choices", {}).get("blood_hunter_curses", [])
        # A curse the character no longer qualifies for (e.g. respecced away
        # from the Order that granted it) shouldn't silently vanish from
        # "already chosen" — but it also shouldn't block picking replacements.
        if len(already_bc) < bc_count:
            needed.append({
                "id": "blood_hunter_curses",
                "source": "class", "source_name": "Blood Hunter",
                "type": "metamagic",
                "count": bc_count,
                "pool": eligible_curses,
                "label": f"Choose {bc_count} Blood Curses Known (Blood Hunter Lv{blood_hunter_lvl})",
                "already_chosen": already_bc,
            })

    # ── Eldritch Invocations picker ──────────────────────────────────────────
    warlock_lvl = 0
    for c in classes:
        if c.get("class") == "Warlock":
            warlock_lvl = c.get("level", 0)
    # Eldritch Adept (feat): grants 1 more invocation on top of whatever a
    # Warlock class level already grants — added to the same count/pool
    # rather than a separate choice, since the confirmation handler
    # writes directly to char["eldritch_invocations"] (not aggregated
    # from multiple sources the way skills/tools/languages are).
    has_eldritch_adept = "Eldritch Adept" in char.get("feats", [])
    if warlock_lvl >= 2 or has_eldritch_adept:
        inv_count_table = {2:2,3:2,4:2,5:3,6:3,7:4,8:4,9:5,10:5,
                           11:5,12:6,13:6,14:6,15:7,16:7,17:7,18:8,19:8,20:8}
        inv_count = inv_count_table.get(min(warlock_lvl, 20), 0) + (1 if has_eldritch_adept else 0)
        already_inv = char.get("eldritch_invocations", [])
        if len(already_inv) < inv_count:
            src_label = ("Warlock" if warlock_lvl >= 2 else "") + (" + " if warlock_lvl >= 2 and has_eldritch_adept else "") + ("Eldritch Adept" if has_eldritch_adept else "")
            needed.append({
                "id": "eldritch_invocations",
                "source": "class", "source_name": src_label,
                "type": "invocation",
                "count": inv_count,
                "pool": None,
                "label": f"Choose {inv_count} Eldritch Invocations ({src_label})",
                "already_chosen": already_inv,
            })

    # ── Bard Magical Secrets ──────────────────────────────────────────────────
    bard_lvl = 0
    for c in classes:
        if c.get("class") == "Bard":
            bard_lvl = c.get("level", 0)
    if bard_lvl >= 10:
        ms_count = (2 if bard_lvl >= 10 else 0) + (2 if bard_lvl >= 14 else 0) + (2 if bard_lvl >= 18 else 0)
        already_ms = char.get("magical_secrets_spells", [])
        if len(already_ms) < ms_count:
            needed.append({
                "id": "magical_secrets_spells",
                "source": "class", "source_name": "Bard",
                "type": "magical_secrets",
                "count": ms_count,
                "pool": None,
                "label": f"Magical Secrets: choose {ms_count} spells from any class list",
                "already_chosen": already_ms,
            })

    return needed


def _multiclass_skill_count(class_name: str, edition: str) -> int:
    """Skills gained when multiclassing into a class (PHB p.164)."""
    MC_SKILLS = {
        "Barbarian": 0, "Bard": 0, "Cleric": 0, "Druid": 0,
        "Fighter": 0, "Monk": 0, "Paladin": 0, "Ranger": 1,
        "Rogue": 1, "Sorcerer": 0, "Warlock": 0, "Wizard": 0,
        "Artificer": 1, "Blood Hunter": 0,
    }
    return MC_SKILLS.get(class_name, 0)


def apply_choice(char: dict, choice_id: str, selected: list) -> None:
    """Store a player's choice and trigger a rebuild."""
    choices = char.setdefault("_choices", {})
    choices[choice_id] = selected
    
    # Aggregate all class skill prof choices into one list for rebuild
    if choice_id.endswith("_skill_profs") or choice_id == "race_skill_profs":
        all_skill_profs = []
        for k, v in choices.items():
            if k.endswith("_skill_profs") and isinstance(v, list):
                all_skill_profs.extend(v)
        choices["class_skill_profs"] = list(set(all_skill_profs))
    
    rebuild(char)
