"""
Fill the official WotC 5E fillable character sheet PDF (2014 PHB, the
free 3-page "5E_CharacterSheet_Fillable.pdf" WotC distributes for
personal use — bundled at dnd_app/data/5E_CharacterSheet_Fillable.pdf)
with a character's real, computed data.

Field-name mapping was reverse-engineered once from the template's own
form fields (pypdf's field introspection) plus a coordinate-based sort
to resolve the many fields whose real names are opaque Acrobat-assigned
IDs (skill/save proficiency checkboxes, and every spell-slot row on the
spellcasting page) — see the STR_SAVE_CHECKBOXES / SKILL_CHECKBOXES /
DEATH_SAVE_CHECKBOXES / SPELL_LEVEL_FIELDS tables below. The template's
own field IDs are stable (it's a fixed, versioned asset), so this
mapping is hardcoded rather than re-derived at runtime.

Author: Ethan O'Brien
"""
import os
import textwrap

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
    from dnd_app.data.phbCommon.items import WEAPON_DICT
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
    text("Race ", char.get("species") or char.get("race", ""))
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
    from dnd_app.data.phb2014.classes import CLASS_DICT
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
    from dnd_app.data.phbCommon.spells import get_spell

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
        names = sorted(by_level.get(lvl, []))
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
