"""The official 5e character sheet (data/5E_CharacterSheet_Fillable.pdf):
exporting a character onto it, and importing a filled-in one back. Both
directions read the same field map, kept once at the top of the export
section.
"""
from __future__ import annotations

import os
import textwrap
import re


# ═══════════════════════════════════════════════════════════════════════════
# Export: a character onto the official sheet
# ═══════════════════════════════════════════════════════════════════════════
# Fill the official WotC 5E fillable character sheet PDF (2014 PHB, the
# free 3-page "5E_CharacterSheet_Fillable.pdf" WotC distributes for
# personal use — bundled at dnd_app/data/5E_CharacterSheet_Fillable.pdf)
# with a character's real, computed data.
#
# Field-name mapping was reverse-engineered once from the template's own
# form fields (pypdf's field introspection) plus a coordinate-based sort
# to resolve the many fields whose real names are opaque Acrobat-assigned
# IDs (skill/save proficiency checkboxes, and every spell-slot row on the
# spellcasting page) — see the STR_SAVE_CHECKBOXES / SKILL_CHECKBOXES /
# DEATH_SAVE_CHECKBOXES / SPELL_LEVEL_FIELDS tables below. The template's
# own field IDs are stable (it's a fixed, versioned asset), so this
# mapping is hardcoded rather than re-derived at runtime.
#
# Author: Ethan O'Brien

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TEMPLATE_PATH = os.path.join(DATA_DIR, "5E_CharacterSheet_Fillable.pdf")

# ── Page 1: saving throw proficiency checkboxes, in STR/DEX/CON/INT/WIS/CHA order ──
SAVE_CHECKBOXES = {
    "STR": "Check Box 11", "DEX": "Check Box 18", "CON": "Check Box 19",
    "INT": "Check Box 20", "WIS": "Check Box 21", "CHA": "Check Box 22",
}

# ── Page 1: skill proficiency checkboxes (alphabetical, matching the sheet's own order) ──
SKILL_CHECKBOXES = {
    "Acrobatics": "Check Box 23", "Animal Handling": "Check Box 24",
    "Arcana": "Check Box 25", "Athletics": "Check Box 26",
    "Deception": "Check Box 27", "History": "Check Box 28",
    "Insight": "Check Box 29", "Intimidation": "Check Box 30",
    "Investigation": "Check Box 31", "Medicine": "Check Box 32",
    "Nature": "Check Box 33", "Perception": "Check Box 34",
    "Performance": "Check Box 35", "Persuasion": "Check Box 36",
    "Religion": "Check Box 37", "Sleight of Hand": "Check Box 38",
    "Stealth": "Check Box 39", "Survival": "Check Box 40",
}

# ── Page 1: skill bonus text fields (the sheet's own field names, some with
# stray trailing/double spaces baked into the real template — must match exactly) ──
SKILL_TEXT_FIELDS = {
    "Acrobatics": "Acrobatics", "Animal Handling": "Animal",
    "Arcana": "Arcana", "Athletics": "Athletics",
    "Deception": "Deception ", "History": "History ",
    "Insight": "Insight", "Intimidation": "Intimidation",
    "Investigation": "Investigation ", "Medicine": "Medicine",
    "Nature": "Nature", "Perception": "Perception ",
    "Performance": "Performance", "Persuasion": "Persuasion",
    "Religion": "Religion", "Sleight of Hand": "SleightofHand",
    "Stealth": "Stealth ", "Survival": "Survival",
}

SAVE_TEXT_FIELDS = {
    "STR": "ST Strength", "DEX": "ST Dexterity", "CON": "ST Constitution",
    "INT": "ST Intelligence", "WIS": "ST Wisdom", "CHA": "ST Charisma",
}

ABILITY_SCORE_FIELDS = {"STR": "STR", "DEX": "DEX", "CON": "CON", "INT": "INT", "WIS": "WIS", "CHA": "CHA"}
ABILITY_MOD_FIELDS = {"STR": "STRmod", "DEX": "DEXmod ", "CON": "CONmod",
                       "INT": "INTmod", "WIS": "WISmod", "CHA": "CHamod"}

# Death saves: successes then failures, left-to-right on the sheet.
DEATH_SAVE_SUCCESS_CHECKBOXES = ["Check Box 12", "Check Box 13", "Check Box 14"]
DEATH_SAVE_FAILURE_CHECKBOXES = ["Check Box 15", "Check Box 16", "Check Box 17"]

WEAPON_FIELDS = [
    ("Wpn Name", "Wpn1 AtkBonus", "Wpn1 Damage"),
    ("Wpn Name 2", "Wpn2 AtkBonus ", "Wpn2 Damage "),
    ("Wpn Name 3", "Wpn3 AtkBonus  ", "Wpn3 Damage "),
]

# ── Page 3: spellcasting. Row field IDs per spell level, derived by sorting
# the template's own (opaque, Acrobat-assigned) field rects into the visual
# 3-column layout (0/1/2 = cantrips+1+2, 3+4+5, 6+7+8+9) and matching each
# spell-name row to its nearest "prepared" checkbox on the same line.
# Level 0 (cantrips) has no prepared checkbox on the real sheet — every
# cantrip a character knows is simply always available, no prep needed.
SPELL_LEVEL_FIELDS = {
    0: [("Spells 1014", None), ("Spells 1016", None), ("Spells 1017", None),
        ("Spells 1018", None), ("Spells 1019", None), ("Spells 1020", None),
        ("Spells 1021", None), ("Spells 1022", None)],
    1: [("Spells 1015", "Check Box 251"), ("Spells 1023", "Check Box 309"),
        ("Spells 1024", "Check Box 3010"), ("Spells 1025", "Check Box 3011"),
        ("Spells 1026", "Check Box 3012"), ("Spells 1027", "Check Box 3013"),
        ("Spells 1028", "Check Box 3014"), ("Spells 1029", "Check Box 3015"),
        ("Spells 1030", "Check Box 3016"), ("Spells 1031", "Check Box 3017"),
        ("Spells 1032", "Check Box 3018"), ("Spells 1033", "Check Box 3019")],
    2: [("Spells 1046", "Check Box 313"), ("Spells 1034", "Check Box 310"),
        ("Spells 1035", "Check Box 3020"), ("Spells 1036", "Check Box 3021"),
        ("Spells 1037", "Check Box 3022"), ("Spells 1038", "Check Box 3023"),
        ("Spells 1039", "Check Box 3024"), ("Spells 1040", "Check Box 3025"),
        ("Spells 1041", "Check Box 3026"), ("Spells 1042", "Check Box 3027"),
        ("Spells 1043", "Check Box 3028"), ("Spells 1044", "Check Box 3029"),
        ("Spells 1045", "Check Box 3030")],
    3: [("Spells 1048", "Check Box 315"), ("Spells 1047", "Check Box 314"),
        ("Spells 1049", "Check Box 3031"), ("Spells 1050", "Check Box 3032"),
        ("Spells 1051", "Check Box 3033"), ("Spells 1052", "Check Box 3034"),
        ("Spells 1053", "Check Box 3035"), ("Spells 1054", "Check Box 3036"),
        ("Spells 1055", "Check Box 3037"), ("Spells 1056", "Check Box 3038"),
        ("Spells 1057", "Check Box 3039"), ("Spells 1058", "Check Box 3040"),
        ("Spells 1059", "Check Box 3041")],
    4: [("Spells 1061", "Check Box 317"), ("Spells 1060", "Check Box 316"),
        ("Spells 1062", "Check Box 3042"), ("Spells 1063", "Check Box 3043"),
        ("Spells 1064", "Check Box 3044"), ("Spells 1065", "Check Box 3045"),
        ("Spells 1066", "Check Box 3046"), ("Spells 1067", "Check Box 3047"),
        ("Spells 1068", "Check Box 3048"), ("Spells 1069", "Check Box 3049"),
        ("Spells 1070", "Check Box 3050"), ("Spells 1071", "Check Box 3051"),
        ("Spells 1072", "Check Box 3052")],
    5: [("Spells 1074", "Check Box 319"), ("Spells 1073", "Check Box 318"),
        ("Spells 1075", "Check Box 3053"), ("Spells 1076", "Check Box 3054"),
        ("Spells 1077", "Check Box 3055"), ("Spells 1078", "Check Box 3056"),
        ("Spells 1079", "Check Box 3057"), ("Spells 1080", "Check Box 3058"),
        ("Spells 1081", "Check Box 3059")],
    6: [("Spells 1083", "Check Box 321"), ("Spells 1082", "Check Box 320"),
        ("Spells 1084", "Check Box 3060"), ("Spells 1085", "Check Box 3061"),
        ("Spells 1086", "Check Box 3062"), ("Spells 1087", "Check Box 3063"),
        ("Spells 1088", "Check Box 3064"), ("Spells 1089", "Check Box 3065"),
        ("Spells 1090", "Check Box 3066")],
    7: [("Spells 1092", "Check Box 323"), ("Spells 1091", "Check Box 322"),
        ("Spells 1093", "Check Box 3067"), ("Spells 1094", "Check Box 3068"),
        ("Spells 1095", "Check Box 3069"), ("Spells 1096", "Check Box 3070"),
        ("Spells 1097", "Check Box 3071"), ("Spells 1098", "Check Box 3072"),
        ("Spells 1099", "Check Box 3073")],
    8: [("Spells 10101", "Check Box 325"), ("Spells 10100", "Check Box 324"),
        ("Spells 10102", "Check Box 3074"), ("Spells 10103", "Check Box 3075"),
        ("Spells 10104", "Check Box 3076"), ("Spells 10105", "Check Box 3077"),
        ("Spells 10106", "Check Box 3078")],
    9: [("Spells 10108", "Check Box 327"), ("Spells 10107", "Check Box 326"),
        ("Spells 10109", "Check Box 3079"), ("Spells 101010", "Check Box 3080"),
        ("Spells 101011", "Check Box 3081"), ("Spells 101012", "Check Box 3082"),
        ("Spells 101013", "Check Box 3083")],
}

# The template's own field ID says "SlotsRemaining", but the text actually
# PRINTED on the page above that box reads "SLOTS EXPENDED" — verified by
# rendering a filled test PDF and checking a level with slots already used;
# the field ID is simply misnamed in the real WotC template. This holds the
# USED count, not what's left.
# Fields with the template's own "multiline" flag set (freeform boxes meant
# to hold several sentences, not a short value) render with the template's
# default "auto" font size (0 in its /DA) otherwise — which a PDF viewer
# expands to fill the field's full height, producing absurdly large text
# for anything longer than a couple of words. Explicit small size needed;
# the many short single-line fields (ability scores, skill bonuses, etc.)
# render fine at the default auto size and are left alone.
MULTILINE_FONT_SIZE = 8
# pypdf only auto-wraps-to-width when font_size is left at 0 ("auto") — but
# auto mode is what produced the wildly oversized text in the first place
# (see the set_need_appearances_writer note in export_official_pdf below).
# With an explicit font_size, pypdf's own appearance-stream generator only
# breaks lines on characters already IN the string, so long paragraph-style
# values need to be pre-wrapped in Python first — hence a known width per
# multiline field (points, from the template's own field rects) rather than
# just a set of field names.
MULTILINE_FIELDS = {
    "PersonalityTraits ": 152.8, "Ideals": 152.8, "Bonds": 152.8, "Flaws": 152.8,
    "AttacksSpellcasting": 165.6, "ProficienciesLang": 165.6, "Equipment": 119.9,
    "Features and Traits": 165.1, "Allies": 175.6, "Feat+Traits": 353.7,
    "Backstory": 164.4, "Treasure": 353.7,
}


def _wrap_multiline(text_val: str, field_width: float, font_size: float) -> str:
    """Pre-wrap text to fit field_width at font_size, preserving existing
    line breaks (each treated as its own paragraph) rather than merging
    them — callers that already join distinct items with "\\n" (a resource
    list, multiple magic items) want each kept on its own line, not
    reflowed together with its neighbors."""
    # Helvetica's average character width is roughly half its point size for
    # ordinary mixed-case English text — an approximation, not exact glyph
    # metrics, but a reasonable margin of safety against overflow.
    max_chars = max(10, int(field_width / (font_size * 0.5)))
    wrapped_paragraphs = [
        "\n".join(textwrap.wrap(line, max_chars)) if line.strip() else ""
        for line in text_val.splitlines()
    ]
    return "\n".join(wrapped_paragraphs)

# Narrow single-line fields where auto-size (0) doesn't shrink enough to
# keep longer real values (e.g. "Quarterstaff", a multiclass "ClassLevel")
# from clipping against the field's edge — verified by rendering a test
# PDF with a weapon name at the edge of this field's width.
SMALL_FONT_SIZE = 8
SMALL_FONT_FIELDS = {
    "ClassLevel", "Wpn Name", "Wpn Name 2", "Wpn Name 3",
    "Wpn1 AtkBonus", "Wpn2 AtkBonus ", "Wpn3 AtkBonus  ",
    "Wpn1 Damage", "Wpn2 Damage ", "Wpn3 Damage ",
}

SLOT_FIELDS = {
    1: ("SlotsTotal 19", "SlotsRemaining 19"), 2: ("SlotsTotal 20", "SlotsRemaining 20"),
    3: ("SlotsTotal 21", "SlotsRemaining 21"), 4: ("SlotsTotal 22", "SlotsRemaining 22"),
    5: ("SlotsTotal 23", "SlotsRemaining 23"), 6: ("SlotsTotal 24", "SlotsRemaining 24"),
    7: ("SlotsTotal 25", "SlotsRemaining 25"), 8: ("SlotsTotal 26", "SlotsRemaining 26"),
    9: ("SlotsTotal 27", "SlotsRemaining 27"),
}

# Classes whose spell list works as "prepare a subset each day" rather than
# "everything you know is always usable" — determines whether a spell's
# "prepared" checkbox reflects char["spells_prepared"] specifically, or is
# simply checked for every known spell (Sorcerer, Bard, Warlock, Ranger,
# etc. don't have a separate prepared list at all; the whole known list is
# always available).
PREPARED_CASTER_CLASSES = {"Cleric", "Druid", "Paladin", "Artificer", "Wizard"}


def _sign(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    return f"+{n}" if n >= 0 else str(n)


def _weapon_summary(char: dict, wname: str):
    """(to_hit_str, damage_str) for one equipped weapon name, same
    simplified logic as save_load.export_character_text()'s weapon
    section — doesn't chase every situational toggle/effect."""
    from dnd_app.data.items import WEAPON_DICT
    from .magic_items import parse_magic_suffix
    from .calculator import get_weapon_attack_bonus

    base_name, magic_bonus = parse_magic_suffix(wname)
    wdata = WEAPON_DICT.get(base_name, {})
    props = " ".join(wdata.get("properties", []) or [])
    ranged = "ranged" in wdata.get("category", "").lower()
    finesse = "finesse" in props.lower()
    to_hit = get_weapon_attack_bonus(char, base_name, finesse_dex=finesse, ranged=ranged) + magic_bonus
    dmg = wdata.get("damage", "")
    dmg_type = wdata.get("dmg_type", "")
    magic_dmg = f"+{magic_bonus}" if magic_bonus else ""
    return _sign(to_hit), f"{dmg}{magic_dmg} {dmg_type}".strip()


def build_field_values(char: dict) -> dict:
    """Compute {field_id: value} for every field this module knows how
    to fill, given a character dict. Checkbox values are the template's
    own "/Yes" checked_value; every other value is a plain string."""
    from .character import ability_mod, ability_score
    from .calculator import (
        get_ac, get_initiative, get_prof_bonus, get_spell_save_dc,
        get_spell_attack_bonus, get_passive_perception, all_skill_bonuses,
        all_saving_throw_bonuses, get_character_senses,
    )

    values = {}
    CHECKED = "/Yes"

    def text(field_id, val):
        if val not in (None, ""):
            if field_id in MULTILINE_FIELDS:
                wrapped = _wrap_multiline(str(val), MULTILINE_FIELDS[field_id], MULTILINE_FONT_SIZE)
                values[field_id] = (wrapped, "/Helv", MULTILINE_FONT_SIZE)
            elif field_id in SMALL_FONT_FIELDS:
                values[field_id] = (str(val), "/Helv", SMALL_FONT_SIZE)
            else:
                values[field_id] = str(val)

    def check(field_id, on):
        if field_id and on:
            values[field_id] = CHECKED

    # ── Identity ──────────────────────────────────────────────────────────
    # Subclass name deliberately left out of the CLASS & LEVEL header field
    # (kept to just "Wizard 5 / Cleric 2"-style class+level, matching how a
    # player would actually write it on paper) — the field's too narrow for
    # "Wizard 5 (School of Evocation)" to fit even at the smallest readable
    # size. Subclass is listed in Features & Traits instead.
    classes = char.get("classes", [])
    cls_str = " / ".join(f"{c['class']} {c['level']}" for c in classes)
    text("ClassLevel", cls_str)
    text("Background", char.get("background", ""))
    text("PlayerName", char.get("player_name", ""))
    text("CharacterName", char.get("name", ""))
    text("CharacterName 2", char.get("name", ""))
    # "High Elf", "Hill Dwarf" -- the subrace too, as a player writes it
    race = char.get("species") or char.get("race", "")
    sub_race = char.get("subrace", "")
    text("Race ", f"{sub_race} {race}".strip() if sub_race and sub_race.lower() not in race.lower() else race)
    text("Alignment", char.get("alignment", ""))
    text("XP", char.get("experience", 0))
    text("Inspiration", "X" if char.get("inspiration") else "")

    # ── Ability scores ───────────────────────────────────────────────────
    for ab, field_id in ABILITY_SCORE_FIELDS.items():
        text(field_id, ability_score(char, ab))
    for ab, field_id in ABILITY_MOD_FIELDS.items():
        text(field_id, _sign(ability_mod(char, ab)))

    # ── Saving throws ────────────────────────────────────────────────────
    for ab, bonus in all_saving_throw_bonuses(char).items():
        text(SAVE_TEXT_FIELDS[ab], _sign(bonus))
        check(SAVE_CHECKBOXES.get(ab), char.get("saving_throws", {}).get(ab))

    # ── Skills ────────────────────────────────────────────────────────────
    for skill, bonus in all_skill_bonuses(char).items():
        field_id = SKILL_TEXT_FIELDS.get(skill)
        if field_id:
            text(field_id, _sign(bonus))
        level = char.get("skills", {}).get(skill, 0)
        check(SKILL_CHECKBOXES.get(skill), level >= 2)

    # ── Combat block ──────────────────────────────────────────────────────
    text("AC", get_ac(char))
    text("Initiative", _sign(get_initiative(char)))
    text("Speed", f"{char.get('speed', 30)} ft")
    text("ProfBonus", _sign(get_prof_bonus(char)))
    text("HPMax", char.get("max_hp", 0))
    text("HPCurrent", char.get("current_hp", 0))
    text("HPTemp", char.get("temp_hp", 0) or "")
    text("Passive", get_passive_perception(char))

    # Hit dice: "Total" line gets the die notation (e.g. "5d10" for a
    # single-class character, or each class's own die for a multiclass one);
    # the big "HIT DICE" box gets the remaining/total count.
    hit_dice = char.get("hit_dice", {})
    if hit_dice:
        total_notation = " + ".join(f"{d.get('total', 0)}{die}" for die, d in hit_dice.items())
        remaining = " + ".join(f"{d.get('remaining', 0)}{die}" for die, d in hit_dice.items())
        text("HDTotal", total_notation)
        text("HD", remaining)

    # Death saves
    death = char.get("death_saves", {})
    for i in range(int(death.get("successes", 0) or 0)):
        if i < len(DEATH_SAVE_SUCCESS_CHECKBOXES):
            check(DEATH_SAVE_SUCCESS_CHECKBOXES[i], True)
    for i in range(int(death.get("failures", 0) or 0)):
        if i < len(DEATH_SAVE_FAILURE_CHECKBOXES):
            check(DEATH_SAVE_FAILURE_CHECKBOXES[i], True)

    # ── Personality ───────────────────────────────────────────────────────
    text("PersonalityTraits ", char.get("personality_traits", ""))
    text("Ideals", char.get("ideals", ""))
    text("Bonds", char.get("bonds", ""))
    text("Flaws", char.get("flaws", ""))

    # ── Weapons (first 3 equipped) ────────────────────────────────────────
    equipped = char.get("equipped_weapons", [])
    for (name_field, atk_field, dmg_field), wname in zip(WEAPON_FIELDS, equipped[:3]):
        text(name_field, wname)
        to_hit, dmg = _weapon_summary(char, wname)
        text(atk_field, to_hit)
        text(dmg_field, dmg)

    # ── Attacks & Spellcasting (freeform box): overflow weapons beyond the
    # 3 named slots, plus a one-line spellcasting summary if applicable ────
    extra_lines = []
    for wname in equipped[3:]:
        to_hit, dmg = _weapon_summary(char, wname)
        extra_lines.append(f"{wname}: {to_hit} to hit, {dmg}")
    if any(m > 0 for m in char.get("spell_slots_max", [])) or char.get("pact_slots_max", 0):
        dc = get_spell_save_dc(char)
        atk = get_spell_attack_bonus(char)
        extra_lines.append(f"Spell save DC {dc}, spell attack {_sign(atk)}")
    text("AttacksSpellcasting", "\n".join(extra_lines))

    # ── Proficiencies & languages ─────────────────────────────────────────
    prof_lines = []
    if char.get("languages"):
        prof_lines.append("Languages: " + ", ".join(sorted(set(char["languages"]))))
    if char.get("armor_proficiencies"):
        prof_lines.append("Armor: " + ", ".join(char["armor_proficiencies"]))
    if char.get("weapon_proficiencies"):
        prof_lines.append("Weapons: " + ", ".join(char["weapon_proficiencies"]))
    if char.get("tool_proficiencies"):
        prof_lines.append("Tools: " + ", ".join(char["tool_proficiencies"]))
    senses = {k: v for k, v in get_character_senses(char).items() if v}
    if senses:
        prof_lines.append("Senses: " + ", ".join(f"{k.capitalize()} {v} ft" for k, v in senses.items()))
    text("ProficienciesLang", "\n".join(prof_lines))

    # ── Equipment (items + currency box separately) ──────────────────────
    eq_lines = [f"{e.get('qty', 1)}x {e.get('name', '')}".strip() for e in char.get("equipment", [])]
    text("Equipment", "\n".join(eq_lines))
    currency = char.get("currency", {})
    text("CP", currency.get("CP", 0))
    text("SP", currency.get("SP", 0))
    text("EP", currency.get("EP", 0))
    text("GP", currency.get("GP", 0))
    text("PP", currency.get("PP", 0))

    # ── Features and Traits (subclass, feats, fighting styles, resources, magic items) ──
    feat_lines = []
    subclass_str = " / ".join(f"{c['class']}: {c['subclass']}" for c in classes if c.get("subclass"))
    if subclass_str:
        feat_lines.append(subclass_str)
    if char.get("feats"):
        feat_lines.append("Feats: " + ", ".join(char["feats"]))
    if char.get("fighting_styles"):
        feat_lines.append("Fighting Style: " + ", ".join(char["fighting_styles"]))
    visible_resources = [r for r in char.get("resources", [])
                          if not isinstance(r.get("current_max"), (int, float)) or r.get("current_max", 0) > 0]
    for r in visible_resources:
        feat_lines.append(f"{r.get('name', '?')}: {r.get('current', 0)}/{r.get('current_max', 0)} ({r.get('reset', '')})")
    for item in char.get("magic_items", []):
        tags = []
        if item.get("attunement"): tags.append("attuned")
        if item.get("equipped"): tags.append("equipped")
        tag_str = f" ({', '.join(tags)})" if tags else ""
        feat_lines.append(f"{item.get('name', 'Unknown')}{tag_str}")
    text("Features and Traits", "\n".join(feat_lines))

    # ── Page 2: personal details ─────────────────────────────────────────
    text("Age", char.get("age", ""))
    text("Height", char.get("height", ""))
    text("Weight", char.get("weight", ""))
    text("Eyes", char.get("eyes", ""))
    text("Skin", char.get("skin", ""))
    text("Hair", char.get("hair", ""))
    text("Allies", char.get("allies_and_organizations", ""))
    text("Feat+Traits", char.get("additional_features", ""))
    text("Backstory", char.get("backstory", ""))
    text("Treasure", char.get("treasure", ""))

    # ── Page 3: spellcasting ──────────────────────────────────────────────
    _fill_spells(char, values, text, check)

    return values


def _detect_spell_class(char: dict) -> str:
    """The class name _detect_spell_ability() would derive its answer
    from — same iteration/special-casing, just returning the class name
    instead of the ability, for the sheet's "Spellcasting Class" field."""
    from dnd_app.data.classes import CLASS_DICT
    for c in char.get("classes", []):
        cls_name = c["class"]
        sub = c.get("subclass", "").lower()
        cls = CLASS_DICT.get(cls_name, {})
        if cls_name == "Fighter" and "eldritch knight" in sub:
            return cls_name
        if cls_name == "Rogue" and "arcane trickster" in sub:
            return cls_name
        if cls.get("spell_ability"):
            return cls_name
    return ""


def _fill_spells(char, values, text, check):
    from .calculator import class_levels, get_spell_save_dc, get_spell_attack_bonus, _detect_spell_ability
    from dnd_app.data.spells import get_spell

    cl = class_levels(char)
    primary_caster = _detect_spell_class(char)
    if primary_caster:
        text("Spellcasting Class 2", primary_caster)
        text("SpellcastingAbility 2", _detect_spell_ability(char))
        text("SpellSaveDC  2", get_spell_save_dc(char))
        text("SpellAtkBonus 2", _sign(get_spell_attack_bonus(char)))

    slots_max = char.get("spell_slots_max", [0] * 9)
    slots_used = char.get("spell_slots_used", [0] * 9)
    for lvl in range(1, 10):
        mx = slots_max[lvl - 1] if lvl - 1 < len(slots_max) else 0
        if mx <= 0:
            continue
        us = slots_used[lvl - 1] if lvl - 1 < len(slots_used) else 0
        total_field, expended_field = SLOT_FIELDS[lvl]
        text(total_field, mx)
        text(expended_field, us)

    known = list(dict.fromkeys(char.get("spells_known", []) + char.get("cantrips", [])))
    prepared = set(char.get("spells_prepared", []))
    is_prepared_class = bool(set(cl) & PREPARED_CASTER_CLASSES)
    by_level = {}
    for sp in known:
        data = get_spell(sp)
        lvl = data.get("level", 0) if data else None
        if lvl is None:
            continue
        by_level.setdefault(lvl, []).append(sp)

    for lvl, rows in SPELL_LEVEL_FIELDS.items():
        # a prepared caster's prepared spells first: the sheet has room for
        # only 7-13 per level, and those are the ones that matter in play
        names = sorted(by_level.get(lvl, []),
                       key=lambda n: (is_prepared_class and n not in prepared, n))
        for (text_field, check_field), name in zip(rows, names):
            text(text_field, name)
            if check_field:
                show_prepared = (name in prepared) if is_prepared_class else True
                check(check_field, show_prepared)


def export_official_pdf(char: dict, output_path: str, template_path: str = None) -> None:
    """Fill the official WotC fillable sheet with this character's data
    and write it to output_path. Raises FileNotFoundError if the
    template asset is missing, and any pypdf error uncaught (callers
    should surface it — a partially-filled PDF isn't a silent failure
    mode worth swallowing)."""
    from pypdf import PdfReader, PdfWriter

    template_path = template_path or TEMPLATE_PATH
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"PDF template not found: {template_path}")

    values = build_field_values(char)
    reader = PdfReader(template_path)
    writer = PdfWriter(clone_from=reader)
    for page_index in range(len(writer.pages)):
        writer.update_page_form_field_values(writer.pages[page_index], values, auto_regenerate=False)
    # Deliberately NOT calling set_need_appearances_writer(True) here: doing
    # so tells PDF viewers to discard pypdf's own generated appearance
    # streams (which correctly honor the explicit MULTILINE_FONT_SIZE) and
    # regenerate their own from each field's /DA instead — which is still
    # the template's original "0 Tf" (auto-size), producing wildly oversized
    # text in every multi-sentence box. pypdf's own appearance streams
    # render correctly as-is.

    with open(output_path, "wb") as f:
        writer.write(f)


# ═══════════════════════════════════════════════════════════════════════════
# Import: a filled-in sheet back into a character
# ═══════════════════════════════════════════════════════════════════════════
# Import a character from a filled-in official WotC 5E character sheet PDF
# (the 3-page "5E_CharacterSheet_Fillable.pdf" -- the same template
# pdf_export.py fills, so its field IDs are known).
#
# Two ways a typed sheet can arrive:
#   * still fillable (typed in Acrobat, a phone PDF app, or exported by
#     this app or another tool that fills the same form) -- the form fields
#     hold the values, read directly;
#   * flattened ("printed to PDF", or a viewer that bakes the form in) --
#     no form fields left, so the text drawn on each page is matched to the
#     template's own field boxes by position. Checkboxes can't be read this
#     way (they're only drawn shapes), so proficiencies are worked out from
#     the skill/save bonuses instead.
#
# A scanned or photographed sheet has no text at all -- that would need OCR
# and isn't handled here.
#
# The sheet only holds what's written on it, so the character is rebuilt the
# same way a new one is (race/class/background grants), and the sheet's own
# numbers are then laid over the top: ability scores (racial bonuses
# subtracted back out), proficiencies and expertise, max HP, spells, gear.
# Anything that couldn't be matched to the app's data is kept, word for
# word, in a "Imported from PDF" notes page so nothing typed is lost.

ABILITIES = ("STR", "DEX", "CON", "INT", "WIS", "CHA")

ALIGNMENTS = {
    "lg": "Lawful Good", "ng": "Neutral Good", "cg": "Chaotic Good",
    "ln": "Lawful Neutral", "n": "True Neutral", "tn": "True Neutral", "cn": "Chaotic Neutral",
    "le": "Lawful Evil", "ne": "Neutral Evil", "ce": "Chaotic Evil",
    "neutral": "True Neutral", "true neutral": "True Neutral",
}


# Shown before the player picks a file (both apps), so they know what to
# expect from a PDF import.
PDF_IMPORT_INTRO = ("A filled-in official 5e character sheet PDF (the 3-page Wizards of the "
                    "Coast sheet) becomes a character: ability scores, proficiencies, HP, "
                    "spells, gear, magic items, money and your notes.")
PDF_IMPORT_LIMITS = [
    "Only the official 5e sheet -- other layouts (D&D Beyond's PDF, homemade sheets) can't be read.",
    "It has to be typed: a scanned, photographed or handwritten sheet has no text to read.",
    "A \"printed to PDF\" (flattened) sheet loses its tick boxes, so proficiencies are worked "
    "out from the bonuses -- check prepared spells and death saves.",
    "The sheet only has room for so many spells per level; any that didn't fit aren't there to bring in.",
    "Anything it can't match is kept, word for word, on an \"Imported from PDF\" notes page, "
    "along with a list of things to check.",
]


class SheetImportError(ValueError):
    """The file isn't a readable official character sheet."""


# ── Reading the PDF ──────────────────────────────────────────────────────
_TEMPLATE_RECTS = None


def _template_rects() -> dict:
    """{field id: (page index, (x0, y0, x1, y1))} from the bundled template."""
    global _TEMPLATE_RECTS
    if _TEMPLATE_RECTS is None:
        from pypdf import PdfReader
        rects = {}
        for pi, page in enumerate(PdfReader(TEMPLATE_PATH).pages):
            for annot in page.get("/Annots") or []:
                a = annot.get_object()
                name = a.get("/T")
                if name is None and a.get("/Parent") is not None:
                    name = a["/Parent"].get_object().get("/T")
                if name is None or a.get("/Rect") is None:
                    continue
                x0, y0, x1, y1 = (float(v) for v in a["/Rect"])
                rects.setdefault(str(name), (pi, (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))))
        _TEMPLATE_RECTS = rects
    return _TEMPLATE_RECTS


def _is_checked(v) -> bool:
    return v not in (None, "", "/Off", "Off", "/No", "No", "0", "/0", False)


def _form_values(reader) -> dict:
    """Field id -> value (str, or bool for checkboxes) from a fillable PDF."""
    fields = reader.get_fields() or {}
    out = {}
    for name, f in fields.items():
        v = f.get("/V")
        if f.get("/FT") == "/Btn":
            out[name] = _is_checked(v)
        elif v is not None:
            out[name] = str(v)
    return out


def _flattened_values(reader) -> dict:
    """Text drawn inside each template field box, for a flattened sheet.

      for each of the 3 pages:
        collect every piece of text pypdf finds, with where it was drawn
        work out each piece's real position on the page (see the note on
          form XObjects below)
        drop each piece into the template field box it lands in
        join each box's pieces top-to-bottom into lines"""
    rects = _template_rects()
    by_page = {}
    for name, (pi, r) in rects.items():
        by_page.setdefault(pi, []).append((name, r))
    out = {}
    for pi, page in enumerate(reader.pages[:3]):
        boxes = by_page.get(pi, [])
        calls = []

        def visit(text, cm, tm, font, size, calls=calls):
            if text and text.strip():
                calls.append((text, list(cm), list(tm)))

        try:
            page.extract_text(visitor_text=visit)
        except Exception:
            continue
        # Text in a form XObject (how flattened fields are usually drawn) is
        # reported twice by pypdf: first piece by piece at its position
        # inside the field box (no page offset), then all together with the
        # box's placement as `cm` but a stale text matrix. So when a placed
        # report arrives, the run of local reports just before it that spells
        # the same text is moved by that cm, and the combined one dropped.
        squash = lambda t: re.sub(r"\s+", "", t)
        placed, local_run = [], []      # local_run: indexes into placed
        for text, cm, tm in calls:
            identity = cm[:4] == [1, 0, 0, 1] and cm[4] == 0 and cm[5] == 0
            if not identity:
                target, joined, k = squash(text), "", None
                for n in range(len(local_run), 0, -1):
                    joined = "".join(squash(placed[idx][0]) for idx in local_run[-n:])
                    if joined == target:
                        k = n
                        break
                if k:
                    for idx in local_run[-k:]:
                        t0, lx, ly = placed[idx]
                        placed[idx] = (t0, cm[4] + lx, cm[5] + ly)
                    local_run = []
                    continue
                local_run = []
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            placed.append((text, x, y))
            if identity:
                local_run.append(len(placed) - 1)
        pieces = {}
        for text, x, y in placed:
            for name, (x0, y0, x1, y1) in boxes:
                if x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1:
                    pieces.setdefault(name, []).append((-y, x, text))
                    break
        for name, parts in pieces.items():
            parts.sort()
            lines, last_y = [], None
            for ny, _x, t in parts:
                if last_y is None or abs(ny - last_y) > 2:
                    lines.append(t)
                else:
                    lines[-1] += t
                last_y = ny
            out[name] = "\n".join(l.strip() for l in lines if l.strip())
    return out


def read_sheet_values(path_or_stream) -> tuple[dict, str]:
    """(values, how) where how is "form" or "flattened". Raises
    SheetImportError if it isn't the official sheet or has nothing typed.

      open the PDF (an unlocked one; a password stops here)
      if it has form fields:
        mostly the template's own field ids -> read them ("form"),
          unless every one is blank (an empty sheet)
        otherwise -> some other form, not the official sheet
      no form fields (flattened):
        no text at all -> a scan or photo, can't be read
        page 1 lacks the sheet's printed labels -> not the official sheet
        else -> read the text by position ("flattened")"""
    from pypdf import PdfReader
    try:
        reader = PdfReader(path_or_stream)
    except Exception as e:
        raise SheetImportError(f"Couldn't read the PDF ({e}).")
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            raise SheetImportError("The PDF is password protected.")
    known = set(_template_rects())
    values = _form_values(reader)
    if values and len(set(values) & known) >= 0.5 * len(known):
        if any(v for k, v in values.items() if isinstance(v, str) and v.strip()):
            return values, "form"
        raise SheetImportError("The character sheet is empty -- nothing has been typed into it.")
    if values:
        raise SheetImportError("This PDF has a form, but it isn't the official 5e character sheet.")
    flat = _flattened_values(reader)
    page1 = (reader.pages[0].extract_text() or "").upper() if reader.pages else ""
    if not flat or ("CLASS & LEVEL" not in page1 and "CHARACTER NAME" not in page1):
        if not page1.strip():
            raise SheetImportError("This PDF has no text in it (a scan or photo?) -- "
                                   "only typed, digital sheets can be imported.")
        raise SheetImportError("This doesn't look like the official 5e character sheet.")
    return flat, "flattened"


# ── Matching what's written to the app's data ────────────────────────────
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9+]+", " ", (s or "").lower()).strip()


def _int(s, default=None):
    m = re.search(r"[-+]?\d+", str(s or "").replace(",", ""))
    return int(m.group()) if m else default


def _best_match(text: str, names, min_len: int = 3):
    """The longest catalogue name found inside `text` (case/punctuation
    insensitive, whole words), else None."""
    t = f" {_norm(text)} "
    best = None
    for n in names:
        nn = _norm(n)
        if len(nn) >= min_len and f" {nn} " in t and (best is None or len(nn) > len(_norm(best))):
            best = n
    return best


def _exact(text: str, names):
    t = _norm(text)
    return next((n for n in names if _norm(n) == t), None)


def _race_and_subrace(text: str):
    from dnd_app.data.races import RACE_DICT, RACE_NAMES
    if not text.strip():
        return "", ""
    race = _best_match(text, RACE_NAMES)
    if not race:
        return "", ""
    subrace = ""
    rest = f" {_norm(text)} "
    for sub_str in RACE_DICT.get(race, {}).get("subraces", []):
        sub = sub_str.split("(")[0].strip()
        if sub and f" {_norm(sub)} " in rest and len(sub) > len(subrace):
            subrace = sub
    return race, subrace


def _classes(text: str):
    """"Wizard 5 / Cleric 2", "Fighter 3, Rogue 2", "Lvl 4 Bard" ->
    [(class, level), ...]."""
    from dnd_app.data.classes import CLASS_NAMES
    out = []
    names = sorted(CLASS_NAMES, key=len, reverse=True)
    t = text or ""
    for n in names:
        for m in re.finditer(re.escape(n), t, re.I):
            if any(m.start() < e and m.end() > s for _, _, s, e in out):
                continue
            after = re.match(r"\s*(?:\([^)]*\))?\s*(?:lvl\.?|level)?\s*(\d{1,2})", t[m.end():], re.I)
            before = re.search(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:lvl\.?|level)?\s*$", t[:m.start()], re.I)
            lvl = int(after.group(1)) if after else (int(before.group(1)) if before else 1)
            out.append((n, max(1, min(20, lvl)), m.start(), m.end()))
    out.sort(key=lambda x: x[2])
    return [(n, l) for n, l, _, _ in out]


def _subclass_for(class_name: str, text: str) -> str:
    from dnd_app.data.classes import CLASS_DICT
    from .character import clean_subclass_name
    best = ""
    for raw in CLASS_DICT.get(class_name, {}).get("subclasses", []):
        name = clean_subclass_name(raw)
        # "School of Evocation" is also written "Evocation"
        short = re.sub(r"^(school|college|circle|oath|path|way|domain|order|"
                       r"conclave|archetype|patron|tradition|the)\s+of\s+(the\s+)?", "", name, flags=re.I)
        for cand in {name, short}:
            if len(cand) > 3 and f" {_norm(cand)} " in f" {_norm(text)} " and len(name) > len(best):
                best = name
    return best


def _lines(text: str) -> list[str]:
    parts = []
    for line in (text or "").replace("\r", "\n").split("\n"):
        line = line.strip(" •-*\t")
        if not line:
            continue
        # a "(...)" wrapped onto its own line by a narrow box -- "Cloak of
        # Protection (equipped)" -- belongs to the line above
        if parts and line.startswith("(") and line.endswith(")") and not parts[-1].endswith((".", ":")):
            parts[-1] += " " + line
        else:
            parts.append(line)
    return parts


_QTY_PATTERNS = (
    re.compile(r"^(\d+)\s*[x×]\s*(.+)$", re.I),       # 2x Torch
    re.compile(r"^(.+?)\s*[x×]\s*(\d+)$", re.I),       # Torch x2
    re.compile(r"^(.+?)\s*\((\d+)\)$"),                # Torch (2)
    re.compile(r"^(\d+)\s+(.+)$"),                     # 10 Torches
)


def _split_qty(line: str):
    for i, pat in enumerate(_QTY_PATTERNS):
        m = pat.match(line)
        if m:
            a, b = m.groups()
            return (int(a), b.strip()) if i in (0, 3) else (int(b), a.strip())
    return 1, line.strip()


def _spell_scroll_line(name: str, spells) -> str | None:
    """"Scroll of Fireball", "Spell scroll: Bless", "Spell Scroll (Shield)",
    "Spell Scroll (1st level) — Bless" -> the app's bound scroll name
    ("Spell Scroll (3rd level) — Fireball"); None if it isn't one."""
    from .spellcasting import parse_spell_scroll, bound_scroll_name
    parsed = parse_spell_scroll(name)
    if parsed and parsed[1]:
        sp = _exact(parsed[1], spells)
        return bound_scroll_name(spells[sp].get("level", 0), sp) if sp else None
    m = re.match(r"^(?:spell\s+)?scroll\s*(?:of|:|-|—|–|\()\s*(?:the\s+)?(.+?)\)?$", name.strip(), re.I)
    if not m:
        return None
    sp = _exact(m.group(1), spells)
    if not sp:
        return None        # "Scroll of Protection" etc. -- a magic item, not a spell
    return bound_scroll_name(spells[sp].get("level", 0), sp)


def _loose_match(name: str, names):
    """"Hempen rope (50 feet)" -> "Rope, Hempen (50 ft)": same words in
    any order (feet/ft, plurals folded)."""
    def words(x):
        x = _norm(x).replace("feet", "ft").replace("foot", "ft")
        return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in x.split()}
    target = words(name)
    if not target:
        return None
    return next((n for n in names if words(n) == target), None)


def _item_catalogue():
    from dnd_app.data.items import WEAPON_DICT, ARMOR_DICT, ADVENTURING_GEAR, ALL_TOOLS
    weights = {}
    for n, d in WEAPON_DICT.items():
        weights[n] = float(d.get("weight", 0) or 0)
    for n, d in ARMOR_DICT.items():
        weights[n] = float(d.get("weight", 0) or 0)
    for row in ADVENTURING_GEAR:
        weights[row[0]] = float(row[1]) if len(row) > 1 and row[1] is not None else 0.0
    for t in ALL_TOOLS:
        weights.setdefault(t, 0.0)
    return weights


def _ability_scores(values: dict) -> tuple[dict, str]:
    """{ability: score} from the sheet's two boxes per ability. People
    write the score in either the big box or the small one (the official
    sheet is ambiguous about which is which), so it's worked out per
    ability: a score is always larger than its own modifier (even a 30's
    is +10), so of the two numbers the larger is the score. Where only one
    box is filled, the way round the other abilities were written decides;
    with nothing to go on, a number written with a sign (+3, -1) or of 5
    or less counts as a modifier. Abilities with only a modifier get an
    estimated score (10 + 2 x modifier) and the player is told."""
    def read(fid):
        raw = values.get(fid) if isinstance(values.get(fid), str) else ""
        n = _int(raw)
        return (n, bool(re.match(r"\s*[+\-\u2212]", raw or ""))) if n is not None else None

    pairs = {ab: (read(ABILITY_SCORE_FIELDS[ab]), read(ABILITY_MOD_FIELDS[ab])) for ab in ABILITIES}
    votes = {"big": 0, "small": 0}
    for big, small in pairs.values():
        if big and small and big[0] != small[0]:
            votes["big" if big[0] > small[0] else "small"] += 1
    lean = "big" if votes["big"] >= votes["small"] else "small"
    if not any(votes.values()):
        lean = None

    scores, estimated = {}, []
    for ab, (big, small) in pairs.items():
        if big and small:
            scores[ab] = max(big[0], small[0])
            continue
        one, box = (big, "big") if big else (small, "small")
        if not one:
            continue
        n, signed = one
        is_score = (box == lean) if lean else (not signed and n > 5)
        if is_score:
            scores[ab] = n
        else:
            scores[ab] = 10 + 2 * n
            estimated.append(ab)

    notes = []
    if votes["small"] > votes["big"]:
        notes.append("Ability scores were in the small boxes (modifiers in the big ones) -- read them that way round.")
    if estimated:
        notes.append(f"Only a modifier was written for {', '.join(estimated)}, so "
                     f"{'that score is an estimate' if len(estimated) == 1 else 'those scores are estimates'} "
                     "(10 + 2 x modifier) -- set the real score on the sheet.")
    if not scores:
        notes.append("No ability scores were found.")
    return {ab: n for ab, n in scores.items() if 1 <= n <= 30}, " ".join(notes)


# ── Building the character ───────────────────────────────────────────────
def character_from_values(values: dict, how: str = "form") -> tuple[dict, list[str]]:
    """(character dict, notes on what was and wasn't imported).

    `values` is {sheet field id: text, or True/False for a tick box}, from
    read_sheet_values(). In order:

      1. Identity -- name, race + subrace, background, alignment, XP, and
         each "Wizard 5 / Cleric 2" class with its level and subclass.
      2. Ability scores -- read from whichever box holds them
         (_ability_scores), then rebuild() so the race/class grants exist,
         and subtract the racial/ASI bonuses back out to get base scores.
      3. Proficiencies -- saves and skills from their tick boxes (or, on a
         flattened sheet, from the bonus being at least mod + proficiency);
         a skill bonus of mod + 2 x proficiency means expertise. Recorded
         as _choices so the next rebuild() keeps them. Languages, feats and
         fighting styles come from the text boxes.
      4. Spells -- each line on page 3 matched to a spell; cantrips vs
         levelled spells; ticked ones are prepared.
      5. Gear -- each Equipment line split into quantity + name, then:
         a spell scroll -> bound scroll; a catalogue item -> that item;
         "+1 Longsword" -> the base item plus an enchanted magic item;
         a magic item -> owned copy (attuned automatically if it needs it);
         anything else -> a custom item. Best armour and a shield go on.
      6. Money, personality, appearance and backstory.
      7. update_all() works out everything derived; then the sheet's own
         max HP (kept as an override if rolled), current HP, spent slots,
         hit dice and death saves are laid over the top.
      8. Checks -- AC and over-maximum scores that don't match what the
         app works out become notes, and every note plus any text that
         wasn't broken down goes on an "Imported from PDF" notes page."""
    from .character import new_character, ability_mod
    from .builder import rebuild
    from .calculator import update_all, get_prof_bonus, SKILL_ABILITY
    from .magic_items import add_owned_magic_item
    from dnd_app.data.classes import CLASS_DICT
    from dnd_app.data.backgrounds import BACKGROUND_NAMES
    from dnd_app.data.feats import FEAT_NAMES
    from dnd_app.data.spells import SPELL_DICT
    from dnd_app.data.magic_items import MAGIC_ITEM_NAMES, get_magic_item
    from dnd_app.data.items import WEAPON_DICT
    from dnd_app.data.feature_ui_interactions import LANGUAGES

    v = lambda k: values.get(k) if isinstance(values.get(k), str) else ""
    checked = lambda k: values.get(k) is True
    report, leftovers = [], []

    char = new_character()
    char["name"] = (v("CharacterName") or v("CharacterName 2")).strip()
    char["player_name"] = v("PlayerName").strip()

    # identity
    race, subrace = _race_and_subrace(v("Race "))
    if race:
        char["race"], char["subrace"] = race, subrace
    elif v("Race ").strip():
        report.append(f"Race \"{v('Race ').strip()}\" isn't one this app knows -- pick it on the Race step.")
    bg = _exact(v("Background"), BACKGROUND_NAMES) or _best_match(v("Background"), BACKGROUND_NAMES)
    if bg:
        char["background"] = bg
    elif v("Background").strip():
        report.append(f"Background \"{v('Background').strip()}\" wasn't recognised.")
    al = v("Alignment").strip()
    char["alignment"] = ALIGNMENTS.get(al.lower()) or ALIGNMENTS.get(_norm(al)) or \
        next((a for a in ALIGNMENTS.values() if _norm(a) == _norm(al)), "True Neutral")
    char["experience"] = _int(v("XP"), 0) or 0
    char["inspiration"] = bool(v("Inspiration").strip())

    all_text = "\n".join(str(x) for x in values.values() if isinstance(x, str))
    classes = _classes(v("ClassLevel"))
    for cname, lvl in classes:
        hd = CLASS_DICT.get(cname, {}).get("hit_die", 8)
        char["classes"].append({"class": cname, "level": lvl, "hit_die": hd,
                                "subclass": _subclass_for(cname, v("ClassLevel") + "\n" + all_text)})
    if not classes:
        report.append("No class was found in CLASS & LEVEL -- add one before playing.")

    # ability scores as written (final, racial bonuses included)
    sheet_scores, note = _ability_scores(values)
    if note:
        report.append(note)
    char["abilities"].update(sheet_scores)

    choices = char["_choices"]
    rebuild(char)
    # put the racial/ASI bonuses back the other side: base = written - bonus
    for ab, score in sheet_scores.items():
        char["abilities"][ab] = max(1, score - char["ability_bonuses"].get(ab, 0))
    rebuild(char)
    for ab, score in sheet_scores.items():          # a cap trimmed a bonus
        diff = score - (char["abilities"][ab] + char["ability_bonuses"].get(ab, 0))
        if diff:
            char["abilities"][ab] += diff

    prof = get_prof_bonus(char)

    # saving throws: the boxes, or (flattened sheet) the bonus itself
    extra_saves = []
    for ab in ABILITIES:
        on = checked(SAVE_CHECKBOXES[ab])
        if how == "flattened":
            bonus = _int(v(SAVE_TEXT_FIELDS[ab]))
            on = bonus is not None and bonus - ability_mod(char, ab) >= prof
        if on and not char["saving_throws"].get(ab):
            extra_saves.append(ab)
    if extra_saves:
        choices["extra_save_profs"] = extra_saves

    # skills: the boxes for proficiency, the written bonus for expertise
    profs, experts = [], []
    for skill, text_id in SKILL_TEXT_FIELDS.items():
        ab = SKILL_ABILITY.get(skill)
        bonus = _int(v(text_id))
        over = (bonus - ability_mod(char, ab)) if (bonus is not None and ab) else None
        on = checked(SKILL_CHECKBOXES[skill]) or (over is not None and over >= prof)
        if over is not None and over >= 2 * prof:
            experts.append(skill)
        elif on:
            profs.append(skill)
    choices["class_skill_profs"] = sorted(set(profs + experts))
    # the sheet's own picks, so a later level down never mistakes them
    # for a removed class's (core/builder.forget_choice_picks)
    choices["pdf_skill_profs"] = sorted(set(profs + experts))
    if experts:
        choices["class_skill_expertise"] = experts
        choices["pdf_skill_expertise"] = experts

    # languages / tools from PROFICIENCIES & LANGUAGES
    langs = [l for l in LANGUAGES if re.search(rf"\b{re.escape(l)}\b", v("ProficienciesLang"), re.I)]
    if langs:
        choices["extra_languages"] = sorted(set(langs) | {"Common"})

    # feats and fighting styles named anywhere in Features & Traits
    feats_text = v("Features and Traits") + "\n" + v("Feat+Traits")
    for f in FEAT_NAMES:
        if re.search(rf"(?<![\w']){re.escape(f)}(?![\w'])", feats_text) and f not in char["feats"]:
            char["feats"].append(f)
    from dnd_app.data.classes import FIGHTING_STYLES
    for raw in FIGHTING_STYLES:
        style = raw.split("\u2013")[0].split(" - ")[0].strip()
        if re.search(rf"fighting style[^\n]*\b{re.escape(style)}\b", feats_text, re.I):
            char.setdefault("fighting_styles", []).append(raw)

    rebuild(char)

    # spells (page 3)
    cantrips, known, prepared, unknown_spells = [], [], [], []
    for lvl, rows in SPELL_LEVEL_FIELDS.items():
        for text_id, check_id in rows:
            name = v(text_id).strip()
            if not name:
                continue
            match = _exact(name, SPELL_DICT) or _best_match(name, SPELL_DICT, min_len=4)
            if not match:
                unknown_spells.append(name)
                continue
            (cantrips if SPELL_DICT[match].get("level", 0) == 0 else known).append(match)
            if check_id and checked(check_id):
                prepared.append(match)
    char["cantrips"] = list(dict.fromkeys(cantrips))
    char["spells_known"] = list(dict.fromkeys(known))
    char["spells_prepared"] = list(dict.fromkeys(prepared))
    if unknown_spells:
        report.append("Spells not recognised: " + ", ".join(unknown_spells))
        leftovers.append("Spells: " + ", ".join(unknown_spells))

    # weapons, gear, magic items
    weights = _item_catalogue()
    weapon_rows = [v(n).strip() for n, _a, _d in WEAPON_FIELDS if v(n).strip()]
    eq_lines = _lines(v("Equipment"))
    if len(eq_lines) == 1 and "," in eq_lines[0]:
        eq_lines = [p.strip() for p in eq_lines[0].split(",") if p.strip()]
    unknown_items = []
    for line in eq_lines + weapon_rows:
        qty, name = _split_qty(line)
        scroll = _spell_scroll_line(name, SPELL_DICT)
        if scroll:
            # a spell scroll, bound to its spell ("Scroll of Fireball")
            existing = next((e for e in char["equipment"] if e["name"] == scroll), None)
            if existing:
                existing["qty"] += qty
            else:
                base = get_magic_item(scroll.split(" — ")[0]) or {}
                char["equipment"].append({"name": scroll, "qty": qty, "weight": 0.5, "notes": "",
                                          "magic": True, "rarity": base.get("rarity", "")})
            continue
        known_item = _exact(name, weights) or _exact(re.sub(r"s$", "", name), weights)
        mi = None if known_item else (_exact(name, MAGIC_ITEM_NAMES) or _loose_match(name, MAGIC_ITEM_NAMES))
        if mi and not known_item:
            if (get_magic_item(mi) or {}).get("type") in ("Potion", "Scroll"):
                char["equipment"].append({"name": mi, "qty": qty, "weight": 0.5, "notes": "", "magic": True,
                                          "rarity": get_magic_item(mi).get("rarity", "")})
            else:
                add_owned_magic_item(char, mi, qty)
            continue
        if not known_item:
            known_item = _loose_match(name, weights)
        # "+1 Longsword" / "Longsword +1": enchanted gear the way the app
        # tracks it -- the base item carried, plus a "Longsword +1" magic item
        plus = re.match(r"^\+([1-3])\s+(.+)$", name) or re.match(r"^(.+?)\s*\+([1-3])$", name)
        if plus and not known_item and not mi:
            bonus, base = (plus.group(1), plus.group(2)) if name.startswith("+") else (plus.group(2), plus.group(1))
            base = _exact(base, weights) or _loose_match(base, weights)
            from dnd_app.data.items import ARMOR_DICT as _AD
            if base and (base in WEAPON_DICT or base in _AD):
                enchanted = f"{base} +{bonus}"
                add_owned_magic_item(char, enchanted)
                if base in WEAPON_DICT:
                    char["equipped_weapons"].append(enchanted)
                elif _AD[base].get("type") == "shield":
                    char["shield"] = True
                    char["shield_magic_bonus"] = max(int(bonus), char.get("shield_magic_bonus", 0))
                else:
                    char["_imported_magic_armor"] = enchanted
                if not any(e["name"] == base for e in char["equipment"]):
                    char["equipment"].append({"name": base, "qty": 1, "weight": weights.get(base, 0.0), "notes": ""})
                continue
        item = known_item or name
        if not known_item:
            unknown_items.append(name)
        existing = next((e for e in char["equipment"] if e["name"] == item), None)
        if existing:
            if line not in weapon_rows:
                existing["qty"] += qty
        else:
            char["equipment"].append({"name": item, "qty": qty, "weight": weights.get(item, 0.0), "notes": ""})
        if line in weapon_rows and item in WEAPON_DICT and item not in char["equipped_weapons"]:
            char["equipped_weapons"].append(item)
    # magic items listed in Features & Traits (this app's own export puts them there)
    for line in _lines(v("Features and Traits")):
        name = re.sub(r"\s*\((attuned|equipped|attuned, equipped)\)$", "", line)
        mi = _exact(name, MAGIC_ITEM_NAMES) or _loose_match(name, MAGIC_ITEM_NAMES)
        if mi and not any(e["name"] == mi for e in char["magic_items"]):
            entry = add_owned_magic_item(char, mi)
            tagged = re.search(r"\((attuned|equipped|attuned, equipped)\)$", line)
            if tagged:
                # this app's own export says exactly what's attuned/equipped
                entry["_attune_known"] = True
                entry["equipped"] = "equipped" in tagged.group(1)
            if "attuned" in line:
                char.setdefault("attuned_items", []).append(mi)
                entry["attuned"] = True
    # a typed sheet rarely says what's attuned -- attune what needs it, up
    # to the limit, and say so
    from .magic_items import set_owned_magic_item_attuned
    auto = []
    for e in char["magic_items"]:
        if e.pop("_attune_known", False):
            continue
        if (get_magic_item(e["name"]) or {}).get("attunement") and not e.get("attuned"):
            if not set_owned_magic_item_attuned(char, e["uid"], True):
                auto.append(e["name"])
    if auto:
        report.append("Attuned to " + ", ".join(auto) + " (they need attunement) -- end it on the "
                      "Equipment screen for any you aren't attuned to.")
    if unknown_items:
        report.append("Added as custom items (not in the app's lists): " + ", ".join(unknown_items))

    # wear the best armour and a shield from what's carried
    from dnd_app.data.items import ARMOR_DICT
    owned = [e["name"] for e in char["equipment"]]
    armours = [n for n in owned if n in ARMOR_DICT and ARMOR_DICT[n].get("type") in ("light", "medium", "heavy")]
    if armours:
        char["armor_worn"] = max(armours, key=lambda n: ARMOR_DICT[n].get("ac", 0))
    if char.get("_imported_magic_armor"):
        char["armor_worn"] = char.pop("_imported_magic_armor")
    if any(n in ARMOR_DICT and ARMOR_DICT[n].get("type") == "shield" for n in owned):
        char["shield"] = True

    for c in ("CP", "SP", "EP", "GP", "PP"):
        char["currency"][c] = max(0, _int(v(c), 0) or 0)

    # personality, page 2
    for key, fid in (("personality_traits", "PersonalityTraits "), ("ideals", "Ideals"),
                     ("bonds", "Bonds"), ("flaws", "Flaws"), ("age", "Age"), ("height", "Height"),
                     ("weight", "Weight"), ("eyes", "Eyes"), ("skin", "Skin"), ("hair", "Hair"),
                     ("allies_and_organizations", "Allies"), ("backstory", "Backstory"),
                     ("treasure", "Treasure")):
        char[key] = v(fid).strip()
    char["additional_features"] = v("Feat+Traits").strip()

    # derive everything else (slots, resources, AC, hit dice...)
    update_all(char)

    # HP: the sheet's max (rolled HP differs from the average) and current
    hp_max = _int(v("HPMax"))
    if hp_max and hp_max > 0 and hp_max != char.get("max_hp"):
        char["hp_max_override"] = hp_max
        update_all(char)
    hp_cur = _int(v("HPCurrent"))
    char["current_hp"] = hp_cur if hp_cur is not None else char.get("max_hp", 0)
    char["temp_hp"] = max(0, _int(v("HPTemp"), 0) or 0)

    # spent slots / hit dice
    for lvl, (_total_id, used_id) in SLOT_FIELDS.items():
        used = _int(v(used_id))
        if used and lvl - 1 < len(char.get("spell_slots_used", [])):
            char["spell_slots_used"][lvl - 1] = min(used, char["spell_slots_max"][lvl - 1])
    hd_left = {f"d{d}": int(n) for n, d in re.findall(r"(\d+)\s*d\s*(\d+)", v("HD"))}
    for die, d in char.get("hit_dice", {}).items():
        if die in hd_left:
            d["remaining"] = min(d.get("total", 0), hd_left[die])
    char["death_saves"] = {
        "successes": sum(checked(b) for b in DEATH_SAVE_SUCCESS_CHECKBOXES),
        "failures": sum(checked(b) for b in DEATH_SAVE_FAILURE_CHECKBOXES),
    }

    # keep the free text this importer doesn't break down, word for word
    for label, fid in (("Features & Traits", "Features and Traits"),
                       ("Attacks & Spellcasting", "AttacksSpellcasting"),
                       ("Proficiencies & Languages", "ProficienciesLang")):
        if v(fid).strip():
            leftovers.append(f"{label}:\n{v(fid).strip()}")
    if unknown_items:
        leftovers.append("Equipment as written:\n" + v("Equipment").strip())

    # numbers worth checking: the sheet vs what the app works out
    from .character import ability_score as _score
    # the most a score can naturally be: 20, or 24 for a 20th-level
    # Barbarian's STR and CON (Primal Champion)
    primal = any(c["class"] == "Barbarian" and c["level"] >= 20 for c in char["classes"])
    cap = lambda ab: ((24 if primal and ab in ("STR", "CON") else 20)
                      + (char.get("ability_max_bonus") or {}).get(ab, 0))
    over = [f"{ab} {sc}" for ab, sc in sheet_scores.items() if sc > cap(ab) and _score(char, ab) < sc]
    if over:
        report.append(f"{', '.join(over)} {'is' if len(over) == 1 else 'are'} above the natural maximum -- "
                      "add the magic item or feature that raises it (e.g. a Belt of Giant Strength) "
                      "and the app will count it.")
    from .calculator import get_ac
    ac = _int(v("AC"))
    if ac and ac != get_ac(char):
        report.append(f"The sheet says AC {ac}, the app works out {get_ac(char)} -- check armour/shield.")
    if how == "flattened":
        report.append("This sheet was flattened, so its tick boxes couldn't be read -- proficiencies "
                      "were worked out from the bonuses; check death saves and prepared spells.")
    # the notes page: what to check, then the sheet's own words
    page = []
    if report:
        page.append("Things to check:\n" + "\n".join(f"- {r}" for r in report))
    page += leftovers
    if page:
        char["notes_pages"] = [{"title": "Imported from PDF", "text": "\n\n".join(page)}]
    return char, report


def import_character_pdf(path_or_stream) -> tuple[dict, list[str]]:
    """Read a filled official 5e sheet and build a character from it.
    Returns (character, notes for the player). Raises SheetImportError."""
    values, how = read_sheet_values(path_or_stream)
    return character_from_values(values, how)
