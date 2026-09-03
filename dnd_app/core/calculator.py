"""
Calculator module.

For a given character dict, derive every computed stat the sheet
displays: ability modifiers, proficiency bonus, AC, initiative, speed
(walk/fly/swim/climb, including condition and exhaustion locks),
senses, saving throws, skill checks, spell save DC/attack bonus,
resistances/immunities, and class/racial/feat/magic-item resource
pools. Reads only from the character dict and static game data;
individual getter functions are pure, while update_all() writes the
aggregated results back onto the character dict for the UI to render.

Author: Ethan O'Brien
Date: 2026-08-20
"""

from .character import (
    ability_score, ability_mod, total_level, class_levels, subclasses,
    new_character,
)
from .multiclass import (
    prof_bonus, compute_all_spell_slots, aggregate_resources,
    compute_hit_points, get_extra_attacks, get_saving_throw_profs,
    build_character_summary,
)
from ..data.phbCommon.items import ARMOR_DICT


SKILL_ABILITY = {
    "Acrobatics": "DEX", "Animal Handling": "WIS", "Arcana": "INT",
    "Athletics": "STR", "Deception": "CHA", "History": "INT",
    "Insight": "WIS", "Intimidation": "CHA", "Investigation": "INT",
    "Medicine": "WIS", "Nature": "INT", "Perception": "WIS",
    "Performance": "CHA", "Persuasion": "CHA", "Religion": "INT",
    "Sleight of Hand": "DEX", "Stealth": "DEX", "Survival": "WIS",
}


def get_onhit_damage_bonuses(char: dict) -> list[dict]:
    """Passive 'once per turn when you hit with a weapon attack, deal extra
    damage' features. Returns each as a separate {name, die, damage_type}
    entry rather than a single combined number, since they're genuinely
    different damage types and resistance/immunity can treat each one
    differently — folding them into one number on the weapon row would
    hide that.
    """
    from dnd_app.core.character import class_levels, subclasses
    cl = class_levels(char)
    subs = subclasses(char)
    out = []

    # Divine Strike (Cleric, 8th level, +1d8 -> +2d8 at 14th)
    cleric_lvl = cl.get("Cleric", 0)
    if cleric_lvl >= 8:
        from dnd_app.data.phbCommon.class_features import DIVINE_STRIKE_TYPE
        domain = subs.get("Cleric", "")
        dtype = None
        for dname, t in DIVINE_STRIKE_TYPE.items():
            if dname.lower() in domain.lower():
                dtype = t
                break
        if dtype:
            die = "2d8" if cleric_lvl >= 14 else "1d8"
            if dtype == "weapon":
                out.append({"name": "Divine Strike", "die": die, "damage_type": "(weapon's type)"})
            elif isinstance(dtype, list):
                out.append({"name": "Divine Strike", "die": die,
                             "damage_type": f"{dtype[0]} (choice: {'/'.join(dtype)})"})
            else:
                out.append({"name": "Divine Strike", "die": die, "damage_type": dtype})

    # Divine Fury (Barbarian, Path of the Zealot, 3rd level): first hit
    # each turn while raging deals extra 1d6 + half barbarian level
    # necrotic or radiant damage (player's choice).
    barb_lvl_zealot = cl.get("Barbarian", 0)
    if barb_lvl_zealot >= 3 and "zealot" in subs.get("Barbarian", "").lower():
        if "Rage" in char.get("active_effects", []):
            half_lvl = barb_lvl_zealot // 2
            pick = char.get("_choices", {}).get("divine_fury_dmg_type", [])
            dtype = pick[0] if pick else "necrotic (choice: necrotic/radiant)"
            out.append({"name": "Divine Fury", "die": f"1d6+{half_lvl}", "damage_type": dtype})

    # Hexblade's Curse (Warlock, The Hexblade, 1st level): while a curse
    # is active on a target, hits against it deal extra damage equal to
    # proficiency bonus. Simplified to "while toggled on" rather than
    # tracking a specific cursed target, matching how other toggle-based
    # on-hit bonuses (Divine Fury, Sacred Weapon) are modeled here.
    warlock_lvl_hexblade = cl.get("Warlock", 0)
    if warlock_lvl_hexblade >= 1 and "hexblade" in subs.get("Warlock", "").lower():
        if "Hexblade's Curse" in char.get("active_effects", []):
            out.append({"name": "Hexblade's Curse", "die": f"{get_prof_bonus(char)}",
                        "damage_type": "(same as weapon)"})

    # Genie's Wrath (Warlock, The Genie, once/turn, PB damage matching genie kind)
    warlock_lvl = cl.get("Warlock", 0)
    if warlock_lvl >= 1 and "genie" in subs.get("Warlock", "").lower():
        pick = char.get("_choices", {}).get("genie_kind", [])
        pick_text = " ".join(pick).lower()
        GENIE_TYPES = {"dao": "bludgeoning", "djinni": "thunder",
                        "efreeti": "fire", "marid": "cold"}
        for kind, dtype in GENIE_TYPES.items():
            if kind in pick_text:
                pb = get_prof_bonus(char)
                out.append({"name": "Genie's Wrath", "die": str(pb), "damage_type": dtype})
                break

    # Dreadful Strikes (Ranger, Fey Wanderer, once/turn, WIS mod psychic)
    ranger_lvl = cl.get("Ranger", 0)
    if ranger_lvl >= 3 and "fey wanderer" in subs.get("Ranger", "").lower():
        from dnd_app.core.character import ability_mod
        wis = ability_mod(char, "WIS")
        wis = max(1, wis)  # minimum 1 per the real feature text
        out.append({"name": "Dreadful Strikes", "die": str(wis), "damage_type": "psychic"})

    # Improved Divine Smite (Paladin, 11th level, base class — not oath-
    # specific) — +1d8 radiant on EVERY melee hit, no once-per-turn limit,
    # unlike Divine Strike. Verified against the real Paladin class text.
    paladin_lvl = cl.get("Paladin", 0)
    if paladin_lvl >= 11:
        out.append({"name": "Improved Divine Smite", "die": "1d8", "damage_type": "radiant"})

    # Aura of Hate (Paladin, Oathbreaker, 7th level) — CHA mod (min +1) to
    # melee weapon damage rolls, same type as the weapon (not a separate
    # damage type), so shown with the weapon's own type rather than a
    # fixed element.
    if paladin_lvl >= 7 and "oathbreaker" in subs.get("Paladin", "").lower():
        from dnd_app.core.character import ability_mod
        cha = max(1, ability_mod(char, "CHA"))
        out.append({"name": "Aura of Hate", "die": str(cha), "damage_type": "(weapon's type)"})

    # Giff's Astral Spark — once per turn, extra force damage equal to PB
    # on a hit with a simple or martial weapon. (Not a natural weapon —
    # this replaced a fabricated "Meaty Fists" entry that had no basis in
    # the real trait, which is entirely about empowering an ordinary
    # weapon hit, not an unarmed strike.)
    species = char.get("species") or char.get("race", "")
    if species.strip().lower() == "giff":
        pb = get_prof_bonus(char)
        out.append({"name": "Astral Spark", "die": str(pb), "damage_type": "force"})

    return out


def get_infusion_min_level(infusion_full_text: str) -> int:
    """Parse the "(min level N)" tag from an infusion's full list entry
    (e.g. "Arcane Propulsion Armor – ... (min level 14)"), so the
    infusion chooser can filter out infusions above the character's
    level. Returns 1 if no tag is present (infusions with no level
    prerequisite, learnable from 2nd level when Infuse Item is first
    gained)."""
    import re
    m = re.search(r"\(min level (\d+)\)", infusion_full_text)
    return int(m.group(1)) if m else 1


def get_infusion_bonus(infusion_name: str, artificer_lvl: int) -> int:
    """Numerical +N bonus granted by a given Artificer infusion at the
    character's current level, applied to attack/damage rolls (an
    infused weapon's magic:True flag is cosmetic on its own and carries
    no numerical bonus). Three infusions scale +1->+2 at 10th level;
    four others grant a flat +1 always; everything else returns 0 (no
    numerical combat bonus)."""
    scaling = {"Enhanced Weapon", "Enhanced Defense", "Enhanced Arcane Focus"}
    flat_plus_one = {"Radiant Weapon (+1)", "Repeating Shot",
                      "Returning Weapon (+1)", "Repulsion Shield (+1)"}
    if infusion_name in scaling:
        return 2 if artificer_lvl >= 10 else 1
    if infusion_name in flat_plus_one:
        return 1
    return 0


def get_max_active_infusions(char: dict) -> int:
    """Max number of infusions that can be active (actually applied to an
    item) at once — exactly half the number of infusions known, not the
    same as knowing them. A character can know far more infusions than
    they can have active simultaneously."""
    known = len(char.get("artificer_infusions", []))
    return known // 2


def can_ritual_cast(char: dict, spell: dict) -> bool:
    """Whether the character can cast this spell as a ritual (no slot
    expended, +10 min casting time) per the real 5e rules.

    Bard, Cleric, Druid, Wizard, and Artificer can ritual-cast any ritual
    spell they know/have prepared. Other classes need either the Ritual
    Caster feat (grants ritual casting for a specific chosen list, tracked
    separately in char["_choices"]) or, for Warlocks specifically, the
    Book of Ancient Secrets invocation (lets them ritual-cast spells
    written into their Book of Shadows — approximated here as any ritual
    spell they know, since the app doesn't track a separate "written in
    the book" list)."""
    if not spell.get("ritual"):
        return False
    name = spell.get("name", "")
    my_classes = {c["class"] for c in char.get("classes", [])}
    RITUAL_CASTER_CLASSES = {"Bard", "Cleric", "Druid", "Wizard", "Artificer"}
    if my_classes & RITUAL_CASTER_CLASSES:
        return True
    if "Ritual Caster" in char.get("feats", []):
        chosen = char.get("_choices", {}).get("feat_ritual_caster_spells", [])
        if name in chosen:
            return True
    if "Warlock" in my_classes:
        invocations = char.get("eldritch_invocations", [])
        if any("Book of Ancient Secrets" in inv for inv in invocations):
            return True
    return False


def get_prof_bonus(char: dict) -> int:
    # magic_prof_bonus holds additive proficiency-bonus sources, e.g. Ioun Stone of Mastery.
    return prof_bonus(total_level(char)) + char.get("magic_prof_bonus", 0)


INITIATIVE_ADVANTAGE_SOURCES = [
    {"class_key": "Barbarian", "min_level": 7, "source": "Feral Instinct",
     "conditional": False,
     "note": "Advantage on initiative rolls."},
]


def get_initiative_advantage_status(char: dict) -> dict:
    """Same shape as get_save_advantage_status, for initiative rolls
    specifically, plus disadvantage — initiative is a Dexterity CHECK
    (PHB p.189), so it's affected by the same active-condition sources
    that impose disadvantage on ability checks generally (Exhaustion
    1+, Frightened, Poisoned — same sources as get_skill_advantage_status's
    condition handling), not the save-specific ones. Per RAW, advantage
    and disadvantage from different sources cancel out rather than one
    silently winning.
    Returns {'has_advantage', 'conditional', 'sources', 'has_disadvantage',
    'disadvantage_sources', 'net': 'advantage'|'disadvantage'|'normal'}."""
    sources = []
    for entry in INITIATIVE_ADVANTAGE_SOURCES:
        if "class_key" in entry:
            lvl = class_levels(char).get(entry["class_key"], 0)
            if lvl < entry.get("min_level", 1):
                continue
        sources.append(entry)
    # Magic items (Rod of Alertness, Helm of Awareness) — see
    # initiative_advantage effect type in core/magic_items.py.
    for item_name in char.get("initiative_advantage_magic", []):
        sources.append({"source": item_name, "note": "Advantage on initiative rolls."})

    dis_sources = []
    if char.get("exhaustion", 0) >= 1:
        dis_sources.append("Exhaustion (level 1+)")
    active_conds = set(char.get("conditions", []))
    for cond in ("Frightened", "Poisoned"):
        if cond in active_conds:
            dis_sources.append(cond)

    has_adv = len(sources) > 0
    has_dis = len(dis_sources) > 0
    net = "normal" if (has_adv and has_dis) else ("advantage" if has_adv else ("disadvantage" if has_dis else "normal"))
    return {
        "has_advantage": has_adv,
        "conditional": any(s.get("conditional") for s in sources),
        "sources": sources,
        "has_disadvantage": has_dis,
        "disadvantage_sources": dis_sources,
        "net": net,
    }


def get_initiative(char: dict) -> int:
    dex = ability_mod(char, "DEX")
    bonus = char.get("initiative_bonus", 0)
    pb = get_prof_bonus(char)
    ed = char.get("edition", "2014")
    has_alert = "Alert" in char.get("feats", [])

    # Alert feat: +5 in 2014 PHB (p.165), +prof in 2024 PHB
    if has_alert:
        bonus += pb if ed == "2024" else 5

    # Bard Lv2+ Jack of All Trades: add half-pb to initiative (Xanathar's p.6)
    bard_lvl = class_levels(char).get("Bard", 0)
    if bard_lvl >= 2:
        bonus += pb // 2

    # Aura of the Sentinel (Paladin, Oath of the Watchers, 7th level):
    # +proficiency bonus to initiative for yourself (and allies within
    # range, which isn't tracked here — see resistance/movement pattern).
    pal_lvl = class_levels(char).get("Paladin", 0)
    if pal_lvl >= 7 and "watchers" in subclasses(char).get("Paladin", "").lower():
        bonus += pb

    # Hare-Trigger (Harengon): +proficiency bonus to initiative.
    race_init = char.get("species") or char.get("race", "")
    if race_init == "Harengon":
        bonus += pb

    return dex + bonus


def get_skill_bonus(char: dict, skill: str) -> int:
    ability = SKILL_ABILITY.get(skill, "STR")
    # Forest Sage: substitutes the player's chosen INT/WIS ability for
    # Animal Handling/Arcana/Nature/Survival checks.
    if skill in ("Animal Handling", "Arcana", "Nature", "Survival") and "Forest Sage" in char.get("feats", []):
        fs_ability = char.get("_choices", {}).get("forest_sage_ability")
        if fs_ability:
            ability = fs_ability
    mod = ability_mod(char, ability)
    prof_level = char.get("skills", {}).get(skill, 0)
    # Githyanki (MPMM) Astral Knowledge / Astral Elf Astral Trance: a
    # temporary skill proficiency re-chosen every long rest, not a
    # permanent grant. Checked dynamically here (same technique as
    # Forest Sage's ability substitution above) rather than mutating
    # char["skills"], since that dict is otherwise a permanent,
    # monotonically-increasing store with no way to "expire" an entry
    # when the character re-picks a different skill on a later rest.
    astral_skill = char.get("_choices", {}).get("astral_knowledge_skill")
    if astral_skill and skill == astral_skill[0]:
        prof_level = max(prof_level, 2)
    pb = get_prof_bonus(char)
    cl = class_levels(char)

    # Jack of All Trades: Bard level 2+ gives half prof to non-proficient checks
    jack = cl.get("Bard", 0) >= 2
    # College of Lore: Cutting Words doesn't add to skills, but Eloquence does to Persuasion
    # We handle Glamour/Eloquence via feature_bonuses below

    if prof_level == 0:
        # Check Jack of All Trades
        if jack:
            return mod + pb // 2
        return mod
    elif prof_level == 1:
        return mod + pb // 2
    elif prof_level == 2:
        return mod + pb
    elif prof_level == 3:
        return mod + pb * 2
    return mod


def get_saving_throw_bonus(char: dict, ability: str) -> int:
    mod = ability_mod(char, ability)
    pb = get_prof_bonus(char)
    cl = class_levels(char)

    # Determine proficiency
    is_prof = char.get("saving_throws", {}).get(ability, False)
    class_save_profs = get_saving_throw_profs(cl)

    # Diamond Soul (Monk 14+): proficient in all saves
    diamond_soul = cl.get("Monk", 0) >= 14

    # Slippery Mind (Rogue 15+): proficient in WIS saves
    slippery_mind = cl.get("Rogue", 0) >= 15 and ability == "WIS"

    base_prof = is_prof or ability in class_save_profs or diamond_soul or slippery_mind
    base = mod + pb if base_prof else mod

    # Paladin Aura of Protection (Pal 6+): add CHA mod (min 1) to ALL saves
    pal_lvl = cl.get("Paladin", 0)
    if pal_lvl >= 6:
        cha_mod = ability_mod(char, "CHA")
        base += max(1, cha_mod)

    # Soul of Artifice (Artificer, 20th level): +1 to all saves per
    # attuned magic item.
    if cl.get("Artificer", 0) >= 20:
        base += len(char.get("attuned_items", []))

    return base + char.get("magic_save_bonus", 0)


def has_reliable_talent(char: dict) -> bool:
    """Rogue 11+: treat any roll of 1-9 on a proficient check as 10."""
    return class_levels(char).get("Rogue", 0) >= 11

def has_jack_of_all_trades(char: dict) -> bool:
    return class_levels(char).get("Bard", 0) >= 2

# Known sources of saving throw advantage/disadvantage. Unlike skill
# advantage (which mostly comes from equipment and applies unconditionally
# whenever that skill is checked), a lot of save advantage in 5e is
# conditional on circumstances this app has no way to know about at
# character-build time (was the effect "seen"? are you currently
# incapacitated?). Rather than silently turning conditional advantage into
# an always-on bonus — which would misrepresent the actual rule — each
# entry carries a `conditional` flag and a plain-language note, and the UI
# surfaces this as an indicator with a tooltip rather than folding it into
# the save's numeric total.
#
# This list is intentionally small and will grow as more classes/races are
# reviewed — see the Barbarian implementation-audit conversation this was
# built from. Not attempting to be comprehensive on the first pass.
SAVE_ADVANTAGE_SOURCES = [
    {"class_key": "Barbarian", "min_level": 2, "ability": "DEX",
     "source": "Danger Sense", "conditional": True,
     "note": "Advantage on DEX saves against effects you can see (traps, spells) — "
             "not while blinded, deafened, or incapacitated."},
    {"class_key": "Warlock", "subclass_match": "undying", "min_level": 1, "ability": "CON",
     "source": "Among the Dead", "conditional": True,
     "note": "Advantage on saves against disease specifically, not all CON saves."},
    {"requires_invocation": "eldritch mind", "ability": "CON",
     "source": "Eldritch Mind", "conditional": True,
     "note": "Advantage on Constitution saves specifically to maintain concentration "
             "on a spell — not other CON saves."},

    # Racial save-advantage traits (text-only until now — see the
    # "systematic racial gaps" review entry in KNOWN_IMPLEMENTATION_GAPS.md).
    # Where a trait's real text ties advantage to a condition/damage type
    # rather than a specific ability (e.g. "advantage against poison"),
    # this follows the same convention already used above for Among the
    # Dead/Eldritch Mind: tag it under whichever ability that kind of save
    # customarily uses in 5e (poison/disease -> CON, charmed/frightened ->
    # WIS), and put the real nuance in the note rather than overclaiming
    # it covers every possible save of that ability.
    {"race": "Gnome", "ability": "INT", "source": "Gnome Cunning", "conditional": True,
     "note": "Advantage on INT/WIS/CHA saves against magic specifically, not all saves."},
    {"race": "Gnome", "ability": "WIS", "source": "Gnome Cunning", "conditional": True,
     "note": "Advantage on INT/WIS/CHA saves against magic specifically, not all saves."},
    {"race": "Gnome", "ability": "CHA", "source": "Gnome Cunning", "conditional": True,
     "note": "Advantage on INT/WIS/CHA saves against magic specifically, not all saves."},
    {"race": "Vedalken", "ability": "INT", "source": "Vedalken Dispassion",
     "note": "Advantage on all Intelligence, Wisdom, and Charisma saving throws."},
    {"race": "Vedalken", "ability": "WIS", "source": "Vedalken Dispassion",
     "note": "Advantage on all Intelligence, Wisdom, and Charisma saving throws."},
    {"race": "Vedalken", "ability": "CHA", "source": "Vedalken Dispassion",
     "note": "Advantage on all Intelligence, Wisdom, and Charisma saving throws."},
    {"race": "Kalashtar", "ability": "WIS", "source": "Dual Mind",
     "note": "Advantage on all Wisdom saving throws."},
    {"race": "Dwarf", "ability": "CON", "source": "Dwarven Resilience", "conditional": True,
     "note": "Advantage specifically against poison, not all CON saves."},
    {"race": "Elf", "ability": "WIS", "source": "Fey Ancestry", "conditional": True,
     "note": "Advantage specifically against being charmed, not all WIS saves. "
             "(Magic also can't put you to sleep — a separate immunity, not tracked here.)"},
    {"race": "Astral Elf", "ability": "WIS", "source": "Fey Ancestry", "conditional": True,
     "note": "Advantage specifically against being charmed, not all WIS saves."},
    {"race": "Halfling", "ability": "WIS", "source": "Brave", "conditional": True,
     "note": "Advantage specifically against being frightened, not all WIS saves."},
    {"race": "Kor", "ability": "WIS", "source": "Brave", "conditional": True,
     "note": "Advantage specifically against being frightened, not all WIS saves."},
    {"race": "Githzerai", "ability": "WIS", "source": "Mental Discipline", "conditional": True,
     "note": "Advantage specifically against being charmed or frightened, not all WIS saves."},
    {"race": "Loxodon", "ability": "WIS", "source": "Loxodon Serenity", "conditional": True,
     "note": "Advantage specifically against being charmed or frightened, not all WIS saves."},
    {"race": "Warforged", "ability": "CON", "source": "Constructed Resilience", "conditional": True,
     "note": "Advantage specifically against being poisoned, not all CON saves."},
    {"race": "Autognome", "ability": "CON", "source": "Mechanical Nature", "conditional": True,
     "note": "Advantage specifically against being paralyzed or poisoned, not all CON saves."},
    {"race": "Plasmoid", "ability": "CON", "source": "Natural Resilience", "conditional": True,
     "note": "Advantage specifically against being poisoned, not all CON saves."},
    {"race": "Reborn", "ability": "CON", "source": "Deathless Nature", "conditional": True,
     "note": "Advantage specifically against disease and being poisoned, not all CON saves. "
             "(Also grants advantage on death saving throws, a separate mechanic not tracked here.)"},
    {"race": "Giff", "ability": "STR", "source": "Hippo Build",
     "note": "Advantage on Strength-based ability checks and Strength saving throws."},
]
for _ability in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
    SAVE_ADVANTAGE_SOURCES.append(
        {"race": "Satyr", "ability": _ability, "source": "Magic Resistance", "conditional": True,
         "note": "Advantage on saving throws against spells specifically, not all saves of this ability."})
    SAVE_ADVANTAGE_SOURCES.append(
        {"race": "Yuan-ti Pureblood", "ability": _ability, "source": "Magic Resistance", "conditional": True,
         "note": "Advantage on saving throws against spells and other magical effects, "
                 "not all saves of this ability."})


def get_save_advantage_status(char: dict, ability: str) -> dict:
    """Return {'has_advantage': bool, 'conditional': bool, 'sources': [...]}
    for a given saving throw ability. Mirrors get_skill_advantage_status's
    shape, but deliberately does NOT fold conditional advantage into the
    save's numeric bonus — see SAVE_ADVANTAGE_SOURCES' docstring for why."""
    sources = []
    for entry in SAVE_ADVANTAGE_SOURCES:
        if entry["ability"] != ability:
            continue
        if "class_key" in entry:
            lvl = class_levels(char).get(entry["class_key"], 0)
            if lvl < entry.get("min_level", 1):
                continue
            if entry.get("subclass_match") is not None:
                sub = subclasses(char).get(entry["class_key"], "").lower()
                if entry["subclass_match"] not in sub:
                    continue
        if "requires_invocation" in entry:
            invs = [i.lower() for i in char.get("eldritch_invocations", [])]
            if not any(entry["requires_invocation"] in i for i in invs):
                continue
        if "race" in entry:
            char_race = char.get("species") or char.get("race", "")
            if char_race != entry["race"]:
                continue
        sources.append(entry)
    # Magic items (Ring of Protection, Mindguard Crown, etc.) populate this
    # list via the advantage_save effect type in core/magic_items.py.
    for item_ability, item_name in char.get("advantage_saves_magic", []):
        if item_ability in ("all", ability):
            sources.append({"ability": ability, "source": item_name})
    return {
        "has_advantage": len(sources) > 0,
        "conditional": any(s.get("conditional") for s in sources),
        "sources": sources,
    }


def get_skill_advantage_status(char: dict, skill: str) -> dict:
    """
    Return {'advantage': bool, 'disadvantage': bool, 'net': 'advantage'|'disadvantage'|'normal',
            'adv_reasons': [...], 'disadv_reasons': [...]}
    for a given skill, based on currently active magic items and equipment
    (e.g. armor that imposes Stealth disadvantage). Advantage and disadvantage
    from different sources cancel out per RAW (PHB p.173).
    """
    has_adv = skill in char.get("skill_advantages", [])
    has_disadv = skill in char.get("skill_disadvantages", [])
    adv_reasons = list(char.get("_skill_advantage_sources", {}).get(skill, []))
    disadv_reasons = list(char.get("_skill_disadvantage_sources", {}).get(skill, []))
    if has_adv and has_disadv:
        net = "normal"   # they cancel — roll straight, per RAW
    elif has_adv:
        net = "advantage"
    elif has_disadv:
        net = "disadvantage"
    else:
        net = "normal"
    return {
        "advantage": has_adv, "disadvantage": has_disadv, "net": net,
        "adv_reasons": adv_reasons, "disadv_reasons": disadv_reasons,
    }


def _passive_skill_adjustment(char: dict, skill: str) -> int:
    """+5 if permanent (always-on) advantage on this skill, -5 if disadvantage, else 0."""
    status = get_skill_advantage_status(char, skill)
    if status["net"] == "advantage":
        return 5
    if status["net"] == "disadvantage":
        return -5
    return 0


def get_passive_perception(char: dict) -> int:
    observant_bonus = 5 if "Observant" in char.get("feats", []) else 0
    return 10 + get_skill_bonus(char, "Perception") + _passive_skill_adjustment(char, "Perception") + observant_bonus


def get_passive_investigation(char: dict) -> int:
    observant_bonus = 5 if "Observant" in char.get("feats", []) else 0
    return 10 + get_skill_bonus(char, "Investigation") + _passive_skill_adjustment(char, "Investigation") + observant_bonus


def get_passive_insight(char: dict) -> int:
    return 10 + get_skill_bonus(char, "Insight") + _passive_skill_adjustment(char, "Insight")


def get_passive_skill(char: dict, skill: str) -> int:
    """Generic passive score for any skill (10 + bonus, ±5 for permanent adv/disadv)."""
    return 10 + get_skill_bonus(char, skill) + _passive_skill_adjustment(char, skill)


def get_ac(char: dict) -> int:
    """Calculate AC based on armor worn and relevant abilities,
    plus any active spell effects (Haste, Shield of Faith, Barkskin…)."""
    # Wild Shape: AC is the beast's own listed AC directly, not computed
    # from armor/Unarmored Defense — you also can't wear armor while
    # transformed (it doesn't fit, and RAW gear either merges into the
    # new form or falls away), so no armor-based bonus applies on top of
    # it either. Using the beast's own AC number avoids relying on the
    # ability-score override to reproduce the right value through
    # Unarmored Defense's formula, which only happens to match for
    # Barbarian/Monk and omits the beast's own natural armor bonus for
    # every other class.
    active_beast = char.get("_wildshape_active")
    if active_beast:
        from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(active_beast)
        if beast:
            return beast["ac"]
    from .effects import effect_ac_bonus, effect_ac_floor
    base = _get_ac_base(char)
    ac = base + effect_ac_bonus(char)
    floor = effect_ac_floor(char)
    return max(ac, floor) if floor else ac


def _get_ac_base(char: dict) -> int:
    override = char.get("ac_override")
    if override is not None:
        return override

    armor_name = char.get("armor_worn", "No Armor")
    # Strip a magic " +1"/"+2"/"+3" suffix (e.g. "Studded Leather +2") for lookup,
    # adding the bonus on top of the base armor's AC.
    from .magic_items import parse_magic_suffix
    base_armor_name, armor_magic_bonus = parse_magic_suffix(armor_name)

    # Defense fighting style: +1 AC while wearing armor. Checked here
    # (not folded into magic_ac below) since it's conditional on actually
    # wearing a real armor item — a positive check against ARMOR_DICT
    # correctly excludes Unarmored Defense, Mage Armor, Natural Armor,
    # Dragon Hide, and Warforged Plating, none of which are actually worn
    # armor even though some of them produce an AC in the same range.
    _armor_entry = ARMOR_DICT.get(base_armor_name)
    has_defense_style = (_armor_entry is not None and _armor_entry.get("type") != "shield" and
                          any("defense" in fs.lower() for fs in char.get("fighting_styles", [])))
    defense_bonus = 1 if has_defense_style else 0

    # Integrated Protection (Warforged): flat +1 AC, always, regardless
    # of armor worn — the real rule has no armor-type condition at all,
    # unlike the fake "Warforged Plating" armor option this replaces.
    race_ac = char.get("species") or char.get("race", "")
    warforged_bonus = 1 if race_ac == "Warforged" else 0

    # Carapace (Simic Hybrid, 5th-level Animal Enhancement choice): +1 AC
    # while not wearing heavy armor.
    heavy_armors_ac = {"Plate", "Splint", "Ring Mail", "Chain Mail", "Half Plate"}
    has_carapace = "Carapace" in char.get("_choices", {}).get("simic_enhancement_5th", [])
    carapace_bonus = 1 if (has_carapace and base_armor_name not in heavy_armors_ac) else 0

    shield = char.get("shield", False)
    shield_bonus = (2 + char.get("shield_magic_bonus", 0)) if shield else 0
    dex_mod = ability_mod(char, "DEX")
    con_mod = ability_mod(char, "CON")
    wis_mod = ability_mod(char, "WIS")
    str_score = ability_score(char, "STR")

    # Check for Unarmored Defense
    cl = class_levels(char)
    barbarian_lvl = cl.get("Barbarian", 0)
    monk_lvl = cl.get("Monk", 0)

    magic_ac = char.get("magic_ac_bonus", 0)
    if base_armor_name == "No Armor":
        # Mage Armor (PHB p.256): base AC becomes 13 + DEX while unarmored.
        # It doesn't stack with Unarmored Defense — use whichever is higher,
        # same as a player would choose in play. Armor of Shadows
        # (Eldritch Invocation) grants this same benefit at will, without
        # needing to actually cast/concentrate on the spell.
        has_mage_armor = ("Mage Armor" in char.get("active_effects", [])
                           or char.get("_armor_of_shadows", False))
        candidates = []
        if barbarian_lvl > 0:
            candidates.append(10 + dex_mod + con_mod + shield_bonus + magic_ac)
        elif monk_lvl > 0:
            candidates.append(10 + dex_mod + wis_mod + magic_ac)
        else:
            candidates.append(10 + dex_mod + shield_bonus + magic_ac)
        if has_mage_armor:
            candidates.append(13 + dex_mod + shield_bonus + magic_ac)
        # Draconic Resilience (Sorcerer, Draconic Bloodline, 1st level):
        # AC 13 + DEX while unarmored, always-on.
        sorc_lvl_ac = cl.get("Sorcerer", 0)
        if sorc_lvl_ac > 0 and "draconic" in subclasses(char).get("Sorcerer", "").lower():
            candidates.append(13 + dex_mod + shield_bonus + magic_ac)
        # Racial Natural Armor / built-in AC formulas, always-on while
        # unarmored.
        species_ac = (char.get("species") or char.get("race", "")).strip().lower()
        if species_ac == "lizardfolk":
            candidates.append(13 + dex_mod + shield_bonus + magic_ac)
        if species_ac == "loxodon":
            candidates.append(12 + con_mod + shield_bonus + magic_ac)
        if species_ac == "autognome":
            candidates.append(13 + dex_mod + shield_bonus + magic_ac)
        if species_ac == "thri-kreen":
            candidates.append(13 + dex_mod + shield_bonus + magic_ac)
        return max(candidates) + warforged_bonus + carapace_bonus

    if base_armor_name in ("Unarmored (Barb)", "Unarmored Defense (Barb)"):
        return 10 + dex_mod + con_mod + shield_bonus + magic_ac + warforged_bonus + carapace_bonus
    if base_armor_name in ("Unarmored (Monk)", "Unarmored Defense (Monk)"):
        return 10 + dex_mod + wis_mod + magic_ac + warforged_bonus + carapace_bonus

    ac = None
    if base_armor_name == "Mage Armor (spell)":
        ac = 13 + dex_mod + shield_bonus
    if ac is None and base_armor_name == "Natural Armor":
        ac = 13 + con_mod + shield_bonus
    if ac is None and base_armor_name == "Dragon Hide (feat)":
        ac = 13 + dex_mod + shield_bonus

    if ac is None:
        armor = ARMOR_DICT.get(base_armor_name)
        if not armor:
            ac = 10 + dex_mod + shield_bonus
        elif armor["type"] == "shield":
            ac = 10 + dex_mod + armor["ac"]
        else:
            base_ac = armor["ac"] + armor_magic_bonus
            dex_cap = armor.get("dex_cap")
            # Medium Armor Master: with DEX 16+ (mod +3), medium armor's
            # Dexterity cap rises from +2 to +3.
            if (dex_cap == 2 and dex_mod >= 3
                    and "Medium Armor Master" in char.get("feats", [])):
                dex_cap = 3
            if dex_cap is None:
                ac = base_ac + dex_mod + shield_bonus
            elif dex_cap == 0:
                ac = base_ac + shield_bonus
            else:
                ac = base_ac + min(dex_mod, dex_cap) + shield_bonus

    return ac + magic_ac + defense_bonus + warforged_bonus + carapace_bonus


def get_speed_breakdown(char: dict) -> list[tuple[str, str]]:
    """Return [(label, display_str), ...] explaining the character's
    current walking speed, for a right-click breakdown popup. Mirrors
    get_ac_breakdown's shape but formats each line itself (rather than a
    bare int) since some contributions are multiplicative (Haste) rather
    than additive."""
    from .effects import EFFECT_TABLE
    parts: list[tuple[str, str]] = []
    base = char.get("speed", 30)
    parts.append(("Base speed", f"{base} ft"))
    monk_bonus = char.get("monk_speed_bonus", 0)
    if monk_bonus:
        parts.append(("Monk (Unarmored Movement)", f"+{monk_bonus} ft"))
    magic_bonus = char.get("magic_speed_bonus", 0)
    if magic_bonus:
        parts.append(("Magic item (flat bonus)", f"+{magic_bonus} ft"))
    for source, value in char.get("_speed_bonus_sources", []):
        if value:
            parts.append((source, f"+{value} ft"))
    bh_lvl_bd = class_levels(char).get("Blood Hunter", 0)
    if bh_lvl_bd >= 7 and "lycan" in subclasses(char).get("Blood Hunter", "").lower():
        parts.append(("Stalker's Prowess (Blood Hunter)", "+10 ft"))
    if bh_lvl_bd >= 10:
        parts.append(("Dark Augmentation (Blood Hunter)", "+5 ft"))
    for name in char.get("active_effects", []):
        e = EFFECT_TABLE.get(name, {})
        if "speed_mult" in e:
            parts.append((name, f"\u00d7{e['speed_mult']:g}"))
        if e.get("speed_add"):
            parts.append((name, f"+{e['speed_add']} ft"))
    exh = char.get("exhaustion", 0)
    if exh >= 5:
        parts.append(("Exhaustion (5+)", "speed = 0"))
    elif exh >= 2:
        parts.append(("Exhaustion (2+)", "\u00d70.5 (rounded down)"))
    active_conditions = set(char.get("conditions", []))
    lock_sources = active_conditions & {
        "Grappled", "Restrained", "Paralyzed", "Petrified", "Stunned", "Unconscious",
    }
    for cond in lock_sources:
        parts.append((cond, "speed = 0"))
    return parts


def get_save_dc_breakdown(char: dict, ability: str) -> list[tuple[str, int]]:
    """[(label, value), ...] for a spell save DC using a SPECIFIC class's
    spellcasting ability — used by the per-class Save DC table so each
    class's own breakdown is shown, not a pooled/auto-detected one."""
    parts = [("Base", 8), ("Proficiency bonus", get_prof_bonus(char)),
             (f"{ability} modifier", ability_mod(char, ability))]
    bonus = char.get("spell_dc_bonus", 0)
    if bonus:
        parts.append(("Magic item bonus", bonus))
    return parts


def get_spell_attack_breakdown(char: dict, ability: str) -> list[tuple[str, int]]:
    """[(label, value), ...] for a spell attack bonus using a SPECIFIC
    class's spellcasting ability (see get_save_dc_breakdown)."""
    parts = [("Proficiency bonus", get_prof_bonus(char)),
             (f"{ability} modifier", ability_mod(char, ability))]
    bonus = char.get("spell_attack_bonus", 0)
    if bonus:
        parts.append(("Magic item bonus", bonus))
    return parts


def get_condition_save_status(char: dict, ability: str) -> dict:
    """Whether a saving throw of the given ability currently auto-fails
    or has disadvantage from active conditions/exhaustion. Distinguishes
    auto-fail (Paralyzed/Stunned/Unconscious/Petrified force a failed
    STR/DEX save outright, not just disadvantage on it) from disadvantage (Restrained
    imposes disadvantage specifically on DEX saves; exhaustion 3+ affects
    all saves) since the real rule text for each is genuinely different,
    not just "some generic penalty."
    Returns {'auto_fail': bool, 'disadvantage': bool, 'sources': [str]}."""
    active = set(char.get("conditions", []))
    auto_fail_sources = []
    dis_sources = []
    if ability in ("STR", "DEX"):
        for cond in ("Paralyzed", "Stunned", "Unconscious", "Petrified"):
            if cond in active:
                auto_fail_sources.append(cond)
    if ability == "DEX" and "Restrained" in active:
        dis_sources.append("Restrained")
    if char.get("exhaustion", 0) >= 3:
        dis_sources.append("Exhaustion (3+)")
    return {"auto_fail": bool(auto_fail_sources), "disadvantage": bool(dis_sources),
            "sources": auto_fail_sources + dis_sources}


def get_condition_attack_status(char: dict) -> dict:
    """Whether the character's own attack rolls currently have
    advantage/disadvantage from active conditions and exhaustion. Real
    5e rule: if a roll would have both advantage and disadvantage from
    different sources, they cancel and neither applies — handled
    explicitly here rather than just returning whichever was checked
    first.
    Returns {'advantage': bool, 'disadvantage': bool, 'sources': [str]}."""
    active = set(char.get("conditions", []))
    adv_sources = []
    dis_sources = []
    # The creature's OWN attack rolls have disadvantage:
    for cond in ("Blinded", "Frightened", "Poisoned", "Prone", "Restrained"):
        if cond in active:
            dis_sources.append(cond)
    # The creature's OWN attack rolls have advantage:
    if "Invisible" in active:
        adv_sources.append("Invisible")
    if char.get("exhaustion", 0) >= 3:
        dis_sources.append("Exhaustion (3+)")
    has_adv = bool(adv_sources)
    has_dis = bool(dis_sources)
    if has_adv and has_dis:
        # Cancel per the real rule — neither applies, but still worth
        # surfacing why in the sources list for the tooltip.
        return {"advantage": False, "disadvantage": False,
                "sources": adv_sources + dis_sources,
                "note": "Advantage and disadvantage sources both present — they cancel out."}
    return {"advantage": has_adv, "disadvantage": has_dis,
            "sources": adv_sources + dis_sources, "note": ""}


def get_weapon_attack_breakdown(char: dict, ability: str, proficient: bool,
                                 magic_bonus: int = 0) -> list[tuple[str, int]]:
    """[(label, value), ...] for a specific weapon's attack bonus."""
    parts = [(f"{ability} modifier", ability_mod(char, ability))]
    if proficient:
        parts.append(("Proficiency bonus", get_prof_bonus(char)))
    if magic_bonus:
        parts.append(("Magic weapon bonus", magic_bonus))
    return parts


def get_ac_breakdown(char: dict) -> list[tuple[str, int]]:
    """
    Return a list of (label, value) pairs explaining how AC was computed,
    for use in a tooltip. Does not include the running total.
    """
    from .magic_items import parse_magic_suffix
    armor_name = char.get("armor_worn", "No Armor")
    base_armor_name, armor_magic_bonus = parse_magic_suffix(armor_name)
    dex_mod = ability_mod(char, "DEX")
    con_mod = ability_mod(char, "CON")
    wis_mod = ability_mod(char, "WIS")
    cl = class_levels(char)
    barbarian_lvl = cl.get("Barbarian", 0)
    monk_lvl = cl.get("Monk", 0)
    shield = char.get("shield", False)
    shield_magic = char.get("shield_magic_bonus", 0)

    parts: list[tuple[str, int]] = []

    if base_armor_name == "No Armor":
        if barbarian_lvl > 0:
            parts.append(("Base (Unarmored Defense)", 10))
            parts.append(("Dexterity modifier", dex_mod))
            parts.append(("Constitution modifier", con_mod))
        elif monk_lvl > 0:
            parts.append(("Base (Unarmored Defense)", 10))
            parts.append(("Dexterity modifier", dex_mod))
            parts.append(("Wisdom modifier", wis_mod))
        else:
            parts.append(("Base (unarmored)", 10))
            parts.append(("Dexterity modifier", dex_mod))
    else:
        armor = ARMOR_DICT.get(base_armor_name)
        if armor and armor["type"] != "shield":
            parts.append((base_armor_name, armor["ac"]))
            if armor_magic_bonus:
                parts.append((f"{base_armor_name} (+{armor_magic_bonus} enchantment)", armor_magic_bonus))
            dex_cap = armor.get("dex_cap")
            if dex_cap is None:
                parts.append(("Dexterity modifier", dex_mod))
            elif dex_cap == 0:
                pass
            else:
                parts.append((f"Dexterity modifier (max +{dex_cap})", min(dex_mod, dex_cap)))
        else:
            parts.append(("Base (unarmored)", 10))
            parts.append(("Dexterity modifier", dex_mod))

    if shield:
        label = "Shield" if not shield_magic else f"Shield (+{shield_magic} enchantment)"
        parts.append((label, 2 + shield_magic))

    for source, value in char.get("_ac_bonus_sources", []):
        if value:
            parts.append((source, value))

    from .effects import EFFECT_TABLE
    heavy_armors = {"Plate", "Splint", "Ring Mail", "Chain Mail", "Half Plate"}
    wearing_heavy = base_armor_name in heavy_armors
    for name in char.get("active_effects", []):
        e = EFFECT_TABLE.get(name, {})
        if e.get("ac"):
            parts.append((name, e["ac"]))
        if "ac_no_heavy_armor" in e and not wearing_heavy:
            parts.append((f"{name} (no heavy armor)", e["ac_no_heavy_armor"]))

    return parts

def get_save_bonus_breakdown(char: dict) -> list[tuple[str, int]]:
    """Return [(source, value), ...] of magic items contributing to saving throws."""
    return [(s, v) for s, v in char.get("_save_bonus_sources", []) if v]


def get_resistances_summary(char: dict) -> dict:
    """
    Return {'resistances': [(dmg_type, source), ...], 'immunities': [...]}
    sourced from currently active magic items.
    """
    return {
        "resistances": list(char.get("damage_resistances", [])),
        "immunities": list(char.get("damage_immunities", [])),
    }


def get_spell_save_dc(char: dict, ability: str = None) -> int:
    """Calculate spell save DC. If ability is None, auto-detect from first spellcasting class."""
    if ability is None:
        ability = _detect_spell_ability(char)
    if not ability:
        return 8 + get_prof_bonus(char)
    return 8 + get_prof_bonus(char) + ability_mod(char, ability) + char.get("spell_dc_bonus", 0)


def resolve_stat_placeholders(text: str, char: dict) -> str:
    """Replace '+STAT' placeholders in feature/action/item text with the
    actual resolved number, in the order the game expects: the dice or
    base value, then the resolved modifier, then the stat abbreviation in
    parens — e.g. '2d6 + CON' becomes '2d6 + 4 (CON)', '1d10+DEX' becomes
    '1d10 + 4 (DEX)', a negative modifier renders as '- 1 (STR)' rather
    than '+ -1 (STR)'.

    A genuine multi-ability CHOICE ('+CHA/INT/WIS' — e.g. Telekinetic's
    shove DC, which lets you use whichever ability you'd use for
    spellcasting) resolves to whichever of those abilities is actually
    highest for this character, with that one <u>underlined</u> so the
    player can see which applies without losing the other options from
    the rule text — e.g. '8+prof+CHA/INT/WIS' becomes
    '8 + 3 (prof) + 5 (<u>CHA</u>/INT/WIS)'. A single ability followed by
    a non-ability shorthand ('+CHA/LR' = "per long rest", not a choice)
    is unaffected by this and resolves as a normal single stat.

    Shared by the Features tab, Action-tab combat cards, and the level-up
    feature preview so all three read identically instead of only some of
    them resolving the placeholder.
    """
    import re
    if not text:
        return text
    _ABIL = "STR|DEX|CON|INT|WIS|CHA"

    # ── Multi-ability choice: '+ABC/DEF/GHI' (2 or more) ──────────────────────
    multi_pat = re.compile(rf'\s*\+\s*((?:{_ABIL})(?:/(?:{_ABIL}))+)\b')
    def _multi_sub(m):
        abilities = m.group(1).split('/')
        mods = {a: ability_mod(char, a) for a in abilities}
        best = max(mods, key=mods.get)
        best_mod = mods[best]
        labeled = '/'.join(f'<u>{a}</u>' if a == best else a for a in abilities)
        sign_val = f"+ {best_mod}" if best_mod >= 0 else f"- {abs(best_mod)}"
        return f" {sign_val} ({labeled})"
    text = multi_pat.sub(_multi_sub, text)

    # ── Single ability: '+STAT' (not immediately followed by another /STAT,
    # since that already got handled above as a multi-ability choice) ────────
    pat = re.compile(rf'\s*\+\s*({_ABIL})\b(?!/(?:{_ABIL})\b)')
    def _sub(m):
        abl = m.group(1)
        mod = ability_mod(char, abl)
        return f" + {mod} ({abl})" if mod >= 0 else f" - {abs(mod)} ({abl})"
    return pat.sub(_sub, text)


def get_spell_attack_bonus(char: dict, ability: str = None) -> int:
    if ability is None:
        ability = _detect_spell_ability(char)
    if not ability:
        return get_prof_bonus(char)
    return get_prof_bonus(char) + ability_mod(char, ability) + char.get("spell_attack_bonus", 0)


def _detect_spell_ability(char: dict) -> str:
    """Find the primary spellcasting ability from first spellcasting class."""
    from ..data.phb2014.classes import CLASS_DICT
    for c in char.get("classes", []):
        cls_name = c["class"]
        sub = c.get("subclass", "").lower()
        cls = CLASS_DICT.get(cls_name, {})
        # Eldritch Knight and Arcane Trickster use INT (PHB p.74, p.97)
        if cls_name == "Fighter" and "eldritch knight" in sub:
            return "INT"
        if cls_name == "Rogue" and "arcane trickster" in sub:
            return "INT"
        spell_ab = cls.get("spell_ability")
        if spell_ab:
            return spell_ab
    return ""



def get_carry_capacity_detail(char: dict) -> dict:
    str_score = ability_score(char, "STR")
    # Check Powerful Build
    has_powerful_build = _has_trait(char, "Powerful Build")
    multiplier = 2 if has_powerful_build else 1
    return {
        "carry": str_score * 15 * multiplier,
        "push_drag_lift": str_score * 30 * multiplier,
        "encumbered": str_score * 5 * multiplier,
        "heavily_encumbered": str_score * 10 * multiplier,
    }


def _has_trait(char: dict, trait_name: str) -> bool:
    traits = char.get("species_traits", [])
    return any(trait_name.lower() in t.lower() for t in traits)


def get_weapon_attack_bonus(char: dict, weapon_name: str,
                             finesse_dex: bool = False,
                             ranged: bool = False) -> int:
    pb = get_prof_bonus(char)
    if ranged or finesse_dex:
        stat_mod = ability_mod(char, "DEX")
    else:
        stat_mod = ability_mod(char, "STR")
    return pb + stat_mod


def get_sneak_attack(char: dict) -> str:
    from .multiclass import sneak_attack_dice
    rogue_lvl = class_levels(char).get("Rogue", 0)
    return sneak_attack_dice(rogue_lvl)


# Cantrips whose damage die count increases at 5th/11th/17th CHARACTER
# level (not caster class level — PHB p.201: "the two rules... refer to
# your character level, not your level in this class or any other").
# Value is (base_dice_count, die_size); the display becomes
# base_dice_count * tier, where tier = 1/2/3/4 for level 1-4/5-10/11-16/17+.
# Utility/buff cantrips that don't deal a scaling damage roll (Shillelagh,
# Magic Stone, Guidance, Prestidigitation, etc.) are intentionally absent.
CANTRIP_DAMAGE_SCALING = {
    "Acid Splash":       (1, 6),
    "Chill Touch":       (1, 8),
    "Create Bonfire":    (1, 8),
    "Fire Bolt":         (1, 10),
    "Frostbite":         (1, 6),
    "Infestation":       (1, 6),
    "Lightning Lure":    (1, 8),
    "Mind Sliver":       (1, 6),
    "Poison Spray":      (1, 12),
    "Primal Savagery":   (1, 10),
    "Produce Flame":     (1, 8),
    "Ray of Frost":      (1, 8),
    "Sacred Flame":      (1, 8),
    "Shocking Grasp":    (1, 8),
    "Sword Burst":       (1, 6),
    "Thunderclap":       (1, 6),
    "Vicious Mockery":   (1, 4),
    "Word of Radiance":  (1, 6),
    "Thorn Whip":        (1, 6),
    "Sapping Sting":     (1, 4),
    "Booming Blade":     (1, 8),   # extra damage die if the target moves
    # Toll the Dead has two base dice (higher one if target is missing HP);
    # both scale together, handled as a special case below.
    "Toll the Dead":     (1, 8),
}


def _cantrip_tier(char_level: int) -> int:
    """1x at 1-4, 2x at 5-10, 3x at 11-16, 4x at 17+ (PHB p.201)."""
    if char_level >= 17: return 4
    if char_level >= 11: return 3
    if char_level >= 5:  return 2
    return 1


def get_cantrip_damage_display(spell_name: str, char: dict) -> str | None:
    """Return the cantrip's CURRENT damage dice for this character's
    level, e.g. 'Fire Bolt' for a level-11 character returns '3d10'.
    Returns None for cantrips that don't have a scaling damage roll here
    (utility cantrips) or aren't in the table at all.

    Eldritch Blast is intentionally excluded — it scales by adding extra
    beams (each still 1d10) rather than a bigger die, a fundamentally
    different display (see get_eldritch_blast_beams below).
    """
    if spell_name not in CANTRIP_DAMAGE_SCALING:
        return None
    base_n, die = CANTRIP_DAMAGE_SCALING[spell_name]
    tier = _cantrip_tier(total_level(char))
    n = base_n * tier
    if spell_name == "Toll the Dead":
        return f"{n}d8 (or {n}d12 if the target is missing any HP)"
    return f"{n}d{die}"


def get_eldritch_blast_beams(char: dict) -> int:
    """Eldritch Blast: 1 beam at levels 1-4, 2 at 5-10, 3 at 11-16, 4 at 17+
    — each beam is a separate 1d10 force attack roll, not a bigger die."""
    return _cantrip_tier(total_level(char))


def get_green_flame_blade_damage(char: dict, ability_modifier: int) -> tuple[str, str]:
    """Green-Flame Blade has an asymmetric scaling shape unlike standard
    damage cantrips: the primary target gets a scaling BONUS die that
    doesn't exist at all below 5th level, and the secondary target's
    damage is the spellcasting ability modifier alone at low level, THEN
    that same scaling die on top of the modifier from 5th level up.
    Returns (primary_bonus_str, secondary_str) — primary_bonus_str is ''
    below 5th level (no bonus damage yet)."""
    tier = _cantrip_tier(total_level(char))
    extra_dice = tier - 1   # 0 at tier 1, then 1/2/3 dice at tiers 2/3/4
    primary = f"{extra_dice}d8 fire" if extra_dice > 0 else ""
    secondary = (f"{ability_modifier} fire" if extra_dice == 0
                 else f"{extra_dice}d8 + {ability_modifier} fire")
    return primary, secondary


def get_superiority_die(char: dict) -> str:
    """Battle Master's superiority die: d8 at 3rd-9th level, d10 at 10th-17th,
    d12 at 18th-20th (PHB p.73). Requires the Battle Master subclass
    specifically — not just any Fighter level, which this incorrectly
    granted a die to before. Superior Technique (TCE fighting style,
    available to Fighter/Paladin/Ranger) grants a flat, non-scaling d8
    independent of class level or subclass."""
    if any("superior technique" in fs.lower() for fs in char.get("fighting_styles", [])):
        return "d8"
    if "Martial Adept" in char.get("feats", []):
        return "d6"
    from .character import subclasses
    lvl = class_levels(char).get("Fighter", 0)
    if lvl == 0 or "battle master" not in subclasses(char).get("Fighter", "").lower():
        return "—"
    if lvl >= 18: return "d12"
    if lvl >= 10: return "d10"
    return "d8"


_COMPANION_SPELL_ABILITY = {
    "Artificer": "INT", "Druid": "WIS", "Ranger": "WIS", "Bard": "CHA",
}


def get_innate_resistance_grants(char: dict) -> list[dict]:
    """Resolve every RACIAL/SUBRACE/FEAT/subclass-passive/subclass-toggle
    resistance, immunity, and condition-immunity that currently applies
    to this character (races.py/feats.py resistances are always text-only
    there; this is the one place they become functional). Each returned
    dict has at least {"kind", "source"} plus either "target" (damage
    type or condition name) matching the schema in resistance_sources.py.
    Does NOT include magic items (magic_items.py handles those
    separately) or Hybrid Transformation (handled inline in update_all
    since it has its own bespoke multi-damage-type shape already)."""
    from dnd_app.data.phbCommon.resistance_sources import (
        RACIAL_RESISTANCES, SUBRACE_RESISTANCES, FEAT_RESISTANCES,
        DM_REWARD_RESISTANCES, SPELL_EFFECT_RESISTANCES,
        SUBCLASS_PASSIVE_RESISTANCES, SUBCLASS_TOGGLE_RESISTANCES)
    from .character import class_levels, subclasses

    out = []
    race = char.get("species") or char.get("race", "")
    subrace = char.get("subrace", "")

    out.extend(RACIAL_RESISTANCES.get(race, []))
    for (r, sub_substr), grants in SUBRACE_RESISTANCES.items():
        if r == race and sub_substr in subrace.lower():
            out.extend(grants)

    known_feats = set(char.get("feats", []))
    for feat_name in known_feats:
        out.extend(FEAT_RESISTANCES.get(feat_name, []))

    # DM-Granted Bonus Features: resistance/immunity grants from dm_rewards.py.
    for reward_name in char.get("dm_rewards", []):
        out.extend(DM_REWARD_RESISTANCES.get(reward_name, []))

    # Spells: resistance/immunity grants from active spell effects (spells.py).
    for effect_name in char.get("active_effects", []):
        out.extend(SPELL_EFFECT_RESISTANCES.get(effect_name, []))

    # Soul of the Storm Giant: resistance to lightning/thunder only while
    # its Maelstrom Aura (a bonus action, not always-on) is active — a real
    # benefit, but conditional, unlike the always-on FEAT_RESISTANCES table
    # above, so it's checked separately here against active_effects.
    if "Soul of the Storm Giant" in known_feats and "Maelstrom Aura" in char.get("active_effects", []):
        out.append({"kind": "resistance", "target": "lightning", "source": "Maelstrom Aura"})
        out.append({"kind": "resistance", "target": "thunder", "source": "Maelstrom Aura"})

    # Scion of the Outer Planes: resistance depends on the player's chosen plane type.
    if "Scion of the Outer Planes" in known_feats:
        plane_choice = char.get("_choices", {}).get("feat_scion_plane_type", [])
        plane = plane_choice[0] if plane_choice else None
        SCION_PLANE_RESISTANCE = {
            "Chaotic Outer Plane": "poison", "Evil Outer Plane": "necrotic",
            "Good Outer Plane": "radiant", "Lawful Outer Plane": "force",
            "The Outlands": "psychic",
        }
        if plane in SCION_PLANE_RESISTANCE:
            out.append({"kind": "resistance", "target": SCION_PLANE_RESISTANCE[plane],
                        "source": "Scion of the Outer Planes"})

    # Resistant Armor (Artificer infusion): applies only while the infusion
    # is actually active, not merely known — matching how every other
    # infusion effect in this app is gated.
    if any(inf.get("infusion") == "Resistant Armor" for inf in char.get("active_infusions", [])):
        ra_type = char.get("_choices", {}).get("resistant_armor_type", "")
        if ra_type:
            out.append({"kind": "resistance", "target": ra_type.lower(), "source": "Resistant Armor"})

    # Petrified (PHB p.291): resistance to all damage, immunity to poison
    # damage and the poisoned condition, and immunity to disease. Its
    # auto-fail STR/DEX saves are handled separately in
    # get_condition_save_status.
    if "Petrified" in char.get("conditions", []):
        out.append({"kind": "resistance", "target": "all", "source": "Petrified"})
        out.append({"kind": "immunity", "target": "poison", "source": "Petrified"})
        out.append({"kind": "condition", "condition": "poisoned", "source": "Petrified"})
        out.append({"kind": "condition", "condition": "disease", "source": "Petrified"})

    cl = class_levels(char)
    subs = subclasses(char)
    active_fx = char.get("active_effects", [])

    for rule in SUBCLASS_PASSIVE_RESISTANCES:
        lvl = cl.get(rule["class_key"], 0)
        sub = subs.get(rule["class_key"], "").lower()
        if rule.get("subclass_match") is not None and rule["subclass_match"] not in sub:
            continue
        # Passive features whose grant depends on an earlier player choice
        # (which totem/aura/essence they picked) rather than just level —
        # the choice_id to read is specified per-rule via "choice_source".
        if rule.get("override_check") in ("storm_herald_aura", "drake_essence", "fiendish_resilience", "elemental_affinity", "lunar_empowerment"):
            if lvl < rule["min_level"]:
                continue
            choice_id = rule.get("choice_source", rule["override_check"])
            picks = char.get("_choices", {}).get(choice_id, [])
            pick_text = " ".join(picks).lower()
            for name, grants in rule["override_grants"].items():
                if name in pick_text:
                    out.extend(grants)
                    break
            continue
        if "upgrade_level" in rule and lvl >= rule["upgrade_level"]:
            out.extend(rule["upgrade_grants"])
        elif lvl >= rule["min_level"]:
            out.extend(rule["grants"])

    for rule in SUBCLASS_TOGGLE_RESISTANCES:
        lvl = cl.get(rule["class_key"], 0)
        if lvl < rule["min_level"]:
            continue
        if rule["subclass_match"]:
            sub = subs.get(rule["class_key"], "").lower()
            if rule["subclass_match"] not in sub:
                continue
        if rule["toggle_key"] not in active_fx:
            continue
        # Bear Totem overrides Rage's base resistance while raging.
        if rule.get("override_check") == "bear_totem":
            picks = char.get("_choices", {}).get("totem_spirit_3", [])
            pick_text = " ".join(picks).lower()
            if "bear" in pick_text:
                out.extend(rule["override_grants"])
                continue
        # Genie's Elemental Gift resistance depends on which genie kind
        # (Dao/Djinni/Efreeti/Marid) was chosen at 1st level.
        if rule.get("override_check") == "genie_kind":
            picks = char.get("_choices", {}).get("genie_kind", [])
            pick_text = " ".join(picks).lower()
            for kind_name, grants in rule["override_grants"].items():
                if kind_name in pick_text:
                    out.extend(grants)
                    break
            continue
        if "upgrade_level" in rule and lvl >= rule["upgrade_level"]:
            out.extend(rule["upgrade_grants"])
        else:
            out.extend(rule["grants"])

    return out


def get_innate_movement_grants(char: dict) -> dict:
    """Resolve every RACIAL/SUBRACE/subclass-passive/subclass-toggle swim,
    climb, and fly speed that currently applies, returning {'swim': int,
    'climb': int, 'fly': int} — the highest value found per movement type
    (these don't stack additively; two fly-speed sources don't add
    together). Populates char['fly_speed']/['swim_speed']/['climb_speed'],
    which get_effective_speed() already reads. Magic items are handled
    separately in magic_items.py and are folded in by the caller."""
    from .character import class_levels, subclasses
    from dnd_app.data.phbCommon.movement_sources import (RACIAL_MOVEMENT, SUBRACE_MOVEMENT,
        SUBCLASS_PASSIVE_MOVEMENT, SUBCLASS_TOGGLE_MOVEMENT)

    best = {"swim": 0, "climb": 0, "fly": 0}
    base_walk = char.get("speed", 30) + char.get("monk_speed_bonus", 0)
    # Fast Movement (Barbarian, 5th level): +10 ft while not wearing heavy
    # armor. Duplicated from get_effective_speed() rather than shared,
    # since this function is called independently from update_all() to
    # populate char["fly_speed"]/etc, before get_effective_speed() ever
    # runs — any grant that resolves "walk" (Eagle Totemic Attunement's
    # fly speed, Bestial Soul's swim speed) needs this included here too,
    # or it silently resolves against a lower, stale value.
    barb_lvl = class_levels(char).get("Barbarian", 0)
    if barb_lvl >= 5:
        from dnd_app.data.phbCommon.items import ARMOR_DICT
        from .magic_items import parse_magic_suffix
        armor_name = char.get("armor_worn", "No Armor")
        base_armor_name, _ = parse_magic_suffix(armor_name)
        armor_entry = ARMOR_DICT.get(base_armor_name)
        is_heavy = armor_entry is not None and armor_entry.get("type") == "heavy"
        if not is_heavy:
            base_walk += 10

    # Powered Steps (Artificer Armorer, Infiltrator model, 3rd level): +5
    # ft. Kept in sync with get_effective_speed's identical check — see
    # that function's comment for why this can't just be shared directly.
    art_lvl = class_levels(char).get("Artificer", 0)
    if art_lvl >= 3 and "armorer" in subclasses(char).get("Artificer", "").lower():
        picks = char.get("_choices", {}).get("armorer_model_3", [])
        if any("infiltrator" in p.lower() for p in picks):
            base_walk += 5

    # Aura of Alacrity (Paladin, Oath of Glory, 7th level): always-on +10
    # ft walking speed, not toggle-dependent. Kept in sync with the
    # identical check in get_effective_speed.
    pal_lvl_aura = class_levels(char).get("Paladin", 0)
    if pal_lvl_aura >= 7 and "glory" in subclasses(char).get("Paladin", "").lower():
        base_walk += 10

    # Bladesong (Wizard, Bladesinging, 2nd level): +10 ft speed while
    # active. Kept in sync with the identical check in get_effective_speed.
    if "Bladesong" in char.get("active_effects", []):
        base_walk += 10

    def _consider(kind, speed):
        val = base_walk if speed == "walk" else speed
        if kind in best:
            best[kind] = max(best[kind], val)

    race = char.get("species") or char.get("race", "")
    subrace = char.get("subrace", "")
    total_level = sum(c.get("level", 0) for c in char.get("classes", []))

    heavy_armors = {"Plate", "Splint", "Ring Mail", "Chain Mail", "Half Plate"}
    medium_armors = {"Hide", "Chain Shirt", "Scale Mail", "Breastplate"}
    worn = char.get("armor_worn", "")

    for grant in RACIAL_MOVEMENT.get(race, []):
        if grant.get("no_medium_heavy_armor") and worn in (heavy_armors | medium_armors):
            continue
        if grant.get("no_heavy_armor") and worn in heavy_armors:
            continue
        _consider(grant["kind"], grant["speed"])

    # Simic Hybrid's 1st-level Animal Enhancement choice (Nimble Climber /
    # Underwater Adaptation grant a climb/swim speed equal to walking
    # speed; Manta Glide has no speed to grant). Conditional on the
    # player's actual choice, so checked directly rather than via the
    # fixed RACIAL_MOVEMENT table.
    if race == "Simic Hybrid":
        enh = char.get("simic_enhancement_1st", "")
        if enh == "Nimble Climber":
            _consider("climb", "walk")
        elif enh == "Underwater Adaptation":
            _consider("swim", "walk")

    for (r, sub_substr), grants in SUBRACE_MOVEMENT.items():
        if r == race and sub_substr in subrace.lower():
            for grant in grants:
                if grant.get("min_char_level", 0) <= total_level:
                    _consider(grant["kind"], grant["speed"])

    cl = class_levels(char)
    subs = subclasses(char)
    active_fx = char.get("active_effects", [])

    for rule in SUBCLASS_PASSIVE_MOVEMENT:
        lvl = cl.get(rule["class_key"], 0)
        sub = subs.get(rule["class_key"], "").lower()
        if rule.get("subclass_match") is not None and rule["subclass_match"] not in sub:
            continue
        if lvl < rule["min_level"]:
            continue
        if rule.get("override_check"):
            picks = char.get("_choices", {}).get(rule.get("choice_source", ""), [])
            pick_text = " ".join(picks).lower()
            matched_grants = None
            for key, grants in rule.get("override_grants", {}).items():
                if key in pick_text:
                    matched_grants = grants
                    break
            for grant in (matched_grants or []):
                _consider(grant["kind"], grant["speed"])
            continue
        for grant in rule["grants"]:
            _consider(grant["kind"], grant["speed"])

    total_lvl_toggle = sum(c.get("level", 0) for c in char.get("classes", []))
    char_race_toggle = char.get("species") or char.get("race", "")
    for rule in SUBCLASS_TOGGLE_MOVEMENT:
        if "race" in rule:
            if char_race_toggle != rule["race"]:
                continue
            if total_lvl_toggle < rule.get("min_char_level", 1):
                continue
            if rule.get("subrace_match"):
                char_subrace = (char.get("subrace") or "").lower()
                if rule["subrace_match"] not in char_subrace:
                    continue
        else:
            lvl = cl.get(rule["class_key"], 0)
            if lvl < rule["min_level"]:
                continue
            if rule["subclass_match"]:
                sub = subs.get(rule["class_key"], "").lower()
                if rule["subclass_match"] not in sub:
                    continue
        if rule["toggle_key"] not in active_fx:
            continue
        if rule.get("override_check") == "eagle_totem_attunement":
            pick = char.get("_choices", {}).get("totem_attune_14", [])
            if any("eagle" in p.lower() for p in pick):
                for grant in rule["override_grants"]:
                    _consider(grant["kind"], grant["speed"])
            continue
        for grant in rule["grants"]:
            _consider(grant["kind"], grant["speed"])

    # Investiture of Wind (spell): 60 ft. flying speed while active.
    if "Investiture of Wind" in active_fx:
        _consider("fly", 60)

    # Tasha's Otherworldly Guise (spell): real 40 ft. flying speed,
    # unconditional across both Lower/Upper Planes variants.
    if any(fx.startswith("Tasha's Otherworldly Guise") for fx in active_fx):
        _consider("fly", 40)

    # Draconic Transformation (spell): grants a 60 ft. flying speed ("Wings" clause).
    if "Draconic Transformation" in active_fx:
        _consider("fly", 60)

    return best


def companion_max_simultaneous(key: str, char: dict) -> int:
    """How many simultaneous active instances of this companion the
    character can have. 1 for every companion except Dancing Item once
    Creative Crescendo applies (Bard, College of Creation, 14th level):
    "you can have a number of animated objects from Animating
    Performance equal to your Charisma modifier active at once ...
    rather than just one." A negative/zero CHA modifier still gets at
    least the base 1 Animating Performance always allows."""
    if key == "dancing_item":
        from .character import class_levels, subclasses
        cl = class_levels(char)
        subs = subclasses(char)
        if cl.get("Bard", 0) >= 14 and "creation" in subs.get("Bard", "").lower():
            return max(1, ability_mod(char, "CHA"))
    return 1


def count_active_companion_instances(key: str, active_summons: list) -> int:
    """Count how many active_summoned_companions entries belong to this
    template key — either the bare key itself (single-instance
    companions) or an instance-suffixed "key#N" form (multi-instance
    companions like Dancing Item once Creative Crescendo applies)."""
    return sum(1 for a in active_summons if a == key or a.startswith(key + "#"))


def get_summonable_but_inactive_companions(char: dict) -> list[str]:
    """Companions the character is class/subclass/level-eligible for,
    tagged requires_summon_action, that still have room for another
    active instance — used by the UI to show a "Summon" prompt
    alongside (or instead of) the full stat block card. For ordinary
    single-instance companions this is "hasn't summoned it yet"; for a
    multi-instance-capable one (Dancing Item + Creative Crescendo)
    it's "hasn't hit the simultaneous-instance cap yet", so the prompt
    can still appear even with one already active."""
    from .character import class_levels, subclasses
    from dnd_app.data.phbCommon.statblocks import COMPANION_STATBLOCKS
    cl = class_levels(char)
    subs = subclasses(char)
    active_summons = char.get("active_summoned_companions", [])
    result = []
    for key, tmpl in COMPANION_STATBLOCKS.items():
        if not tmpl.get("requires_summon_action"):
            continue
        if count_active_companion_instances(key, active_summons) >= companion_max_simultaneous(key, char):
            continue
        cls_lvl = cl.get(tmpl["class_key"], 0)
        if cls_lvl < tmpl["min_level"]:
            continue
        sub = subs.get(tmpl["class_key"], "").lower()
        if tmpl["subclass_match"] not in sub:
            continue
        result.append(key)
    return result


def get_available_companions(char: dict) -> list[str]:
    """Return the companion_statblocks keys the character currently
    qualifies for, based on class/subclass/level. Doesn't second-guess
    whether they actually chose an optional feature (e.g. Beast Master's
    Primal Companion vs the default Ranger's Companion) — if the
    prerequisite subclass+level is met, it's offered.

    Three exceptions, all about respecting the real recreation timing
    rather than always showing a stat block the moment the class
    feature is unlocked:
    - Companions tagged requires_summon_action (Drake Companion,
      Dancing Item, Wildfire Spirit) are only included once actually
      summoned — tracked in char["active_summoned_companions"]. A
      multi-instance-capable companion (Dancing Item, once Creative
      Crescendo applies) contributes one list entry per currently
      active instance, using an instance-suffixed "key#N" id, so the
      UI builds one stat block card per instance instead of one total.
    - Companions tagged requires_active_infusion (Homunculus Servant)
      are only included while an active_infusions entry for that exact
      infusion exists — matching how it's really created (infusing a
      gem, via the app's existing infuse-item flow) rather than a
      separate summon action or rest-based resource.
    - ANY companion (including Steel Defender and the Primal Companion
      beasts, which have no per-use summon limit at all) is excluded
      while marked "pending replacement" in
      char["companion_pending_replacement"] — set when it dies, and
      cleared on the character's next long rest, matching the real
      rule that recreation happens "at the end of a long rest," not
      instantly the moment the old one is destroyed."""
    from .character import class_levels, subclasses
    from dnd_app.data.phbCommon.statblocks import COMPANION_STATBLOCKS, ELDRITCH_CANNON
    cl = class_levels(char)
    subs = subclasses(char)
    active_summons = char.get("active_summoned_companions", [])
    pending_replacement = set(char.get("companion_pending_replacement", []))
    active_infusion_names = {inf.get("infusion", "") for inf in char.get("active_infusions", [])}
    available = []
    for key, tmpl in {**COMPANION_STATBLOCKS, "eldritch_cannon": ELDRITCH_CANNON}.items():
        cls_lvl = cl.get(tmpl["class_key"], 0)
        if cls_lvl < tmpl["min_level"]:
            continue
        sub = subs.get(tmpl["class_key"], "").lower()
        if tmpl["subclass_match"] not in sub:
            continue
        if tmpl.get("requires_summon_action"):
            instances = [a for a in active_summons if a == key or a.startswith(key + "#")]
            if not instances:
                continue
            req_infusion = tmpl.get("requires_active_infusion")
            if req_infusion and req_infusion not in active_infusion_names:
                continue
            if key in pending_replacement:
                continue
            available.extend(instances)
            continue
        req_infusion = tmpl.get("requires_active_infusion")
        if req_infusion and req_infusion not in active_infusion_names:
            continue
        if key in pending_replacement:
            continue
        available.append(key)
    return available


def resolve_companion_statblock(key: str, char: dict) -> dict:
    """Compute the actual current numbers for one companion stat block,
    given this character's level/proficiency bonus/spellcasting stats.
    Returns a dict with the same shape as the template but with every
    {formula} string already filled in with real numbers.

    key may be an instance-suffixed "template_key#N" id (multi-instance
    companions like Dancing Item under Creative Crescendo) — the
    template is looked up by its base key, and the returned
    display_name gets a "#<n+1>" suffix so multiple active instances
    are distinguishable in the UI."""
    from dnd_app.data.phbCommon.statblocks import COMPANION_STATBLOCKS, ELDRITCH_CANNON
    from .character import class_levels

    base_key, sep, instance_n = key.partition("#")
    tmpl = COMPANION_STATBLOCKS.get(base_key) or (ELDRITCH_CANNON if base_key == "eldritch_cannon" else None)
    if not tmpl:
        return {}
    cls_name = tmpl["class_key"]
    level = class_levels(char).get(cls_name, 0)
    pb = get_prof_bonus(char)
    int_mod = ability_mod(char, "INT")
    ability = _COMPANION_SPELL_ABILITY.get(cls_name, "INT")
    dc = get_spell_save_dc(char, ability=ability)
    atk_bonus = get_spell_attack_bonus(char, ability=ability)
    atk = f"+{atk_bonus}" if atk_bonus >= 0 else str(atk_bonus)
    # Drake's Bite uses a flat "+3 + PB" not tied to spellcasting ability
    # (matches its STR modifier of +3 printed directly in the stat block).
    atk_flat_val = 3 + pb
    atk_flat = f"+{atk_flat_val}"

    fmt_kwargs = dict(level=level, pb=pb, int_mod=int_mod, atk=atk, dc=dc, atk_flat=atk_flat)

    def _fmt(s):
        return s.format(**fmt_kwargs) if isinstance(s, str) else s

    def _eval_bonus(s):
        """'+1 + 4' -> '+5', '+0 + 4×2' -> '+8'. Falls back to the raw
        formatted string if it's not simple +N arithmetic (e.g. contains
        prose)."""
        from dnd_app.core.safe_eval import safe_eval_arith
        txt = _fmt(s)
        try:
            val = safe_eval_arith(txt)
            return f"+{val}" if val >= 0 else str(val)
        except Exception:
            return txt

    out = dict(tmpl)
    out["level"] = level
    if sep and instance_n.isdigit():
        out["display_name"] = f"{tmpl.get('display_name', base_key)} #{int(instance_n) + 1}"
    out["ac"] = _eval_bonus(tmpl.get("ac_formula", "")).lstrip("+") if tmpl.get("ac_formula") else ""
    if tmpl.get("hp_formula"):
        # Evaluate the arithmetic (formulas use only +, ×, and the
        # already-substituted numbers) to show a real HP total, not just
        # the formula text.
        from dnd_app.core.safe_eval import safe_eval_arith
        hp_expr = _fmt(tmpl["hp_formula"])
        try:
            out["hp"] = safe_eval_arith(hp_expr)
        except Exception:
            out["hp"] = hp_expr
    if tmpl.get("hit_dice_formula"):
        out["hit_dice"] = _fmt(tmpl["hit_dice_formula"])
    out["saves"] = [(ab, _eval_bonus(f)) for ab, f in tmpl.get("saves", [])]
    out["skills"] = [(sk, _eval_bonus(f)) for sk, f in tmpl.get("skills", [])]
    out["senses"] = _fmt(tmpl.get("senses", ""))
    # Senses text has a "passive Perception 10 + (N×2)" style tail —
    # evaluate that trailing arithmetic too so it reads as a real number.
    import re as _re_sense
    from dnd_app.core.safe_eval import safe_eval_arith
    m = _re_sense.search(r"passive Perception (\d+ \+ \([^)]*\))", out["senses"])
    if m:
        try:
            val = safe_eval_arith(m.group(1))
            out["senses"] = out["senses"][:m.start(1)] + str(val) + out["senses"][m.end(1):]
        except Exception:
            pass
    out["traits"] = [(n, _fmt(d)) for n, d in tmpl.get("traits", [])]
    out["actions"] = [(n, _fmt(d)) for n, d in tmpl.get("actions", [])]
    out["reactions"] = [(n, _fmt(d)) for n, d in tmpl.get("reactions", [])]
    if "cannon_types" in tmpl:
        out["cannon_types"] = [(n, _fmt(d)) for n, d in tmpl["cannon_types"]]
    if "notes" in tmpl:
        out["notes"] = _fmt(tmpl["notes"])
    return out


def get_hemocraft_die(char: dict) -> str:
    """Blood Hunter's Hemocraft die: 1d4 at levels 1-4, 1d6 at 5-10,
    1d8 at 11-16, 1d10 at 17-20. Used for Crimson Rite activation cost
    and Blood Maledict amplification, among other class features."""
    lvl = class_levels(char).get("Blood Hunter", 0)
    if lvl == 0:
        return "—"
    if lvl >= 17: return "1d10"
    if lvl >= 11: return "1d8"
    if lvl >= 5:  return "1d6"
    return "1d4"


def get_wild_shape_info(char: dict) -> dict | None:
    """Return {'max_cr': str, 'restriction': str} for the character's
    CURRENT Wild Shape access. Returns None if not a Druid.

    Base progression (PHB p.68 Beast Shapes table):
      2nd level: max CR 1/4, no flying or swimming speed
      4th level: max CR 1/2, no flying speed
      8th level: max CR 1, no restriction

    Circle of the Moon (PHB p.68) IGNORES the Max CR column — max CR 1
    starting at 2nd level, then floor(druid level / 3) starting at 6th —
    but still must obey the OTHER limitations on that table (the
    flying/swimming restriction is separate from the CR cap and still
    applies by druid level exactly as the base table says).
    """
    from .character import class_levels, subclasses
    druid_lvl = class_levels(char).get("Druid", 0)
    if druid_lvl == 0:
        return None
    is_moon = "moon" in subclasses(char).get("Druid", "").lower()

    if druid_lvl < 4:
        restriction = "No flying or swimming speed"
    elif druid_lvl < 8:
        restriction = "No flying speed"
    else:
        restriction = "No restriction"

    if is_moon:
        max_cr = "1" if druid_lvl < 6 else str(druid_lvl // 3)
    else:
        if druid_lvl < 4:
            max_cr = "1/4"
        elif druid_lvl < 8:
            max_cr = "1/2"
        else:
            max_cr = "1"

    return {"max_cr": max_cr, "restriction": restriction}


def get_available_wildshape_beasts(char: dict) -> list[str]:
    """Return the WILDSHAPE_BEASTS keys this Druid can currently turn into,
    filtered by get_wild_shape_info()'s max_cr and restriction (no
    flying/swimming speed below certain levels). Returns [] if not a
    Druid or Wild Shape isn't available yet."""
    from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
    from .character import class_levels, subclasses
    info = get_wild_shape_info(char)
    if not info:
        return []
    druid_lvl = class_levels(char).get("Druid", 0)
    is_moon = "moon" in subclasses(char).get("Druid", "").lower()
    cr_map = {"1/8": 0.125, "1/4": 0.25, "1/2": 0.5}
    max_cr = cr_map.get(info["max_cr"], None)
    if max_cr is None:
        try:
            max_cr = float(info["max_cr"])
        except ValueError:
            max_cr = 0
    restriction = info["restriction"]

    out = []
    for name, beast in WILDSHAPE_BEASTS.items():
        if beast["cr"] > max_cr:
            continue
        if restriction == "No flying or swimming speed" and (beast["flies"] or beast["swims"]):
            continue
        if restriction == "No flying speed" and beast["flies"]:
            continue
        out.append(name)

    # Circle of the Moon's Elemental Wild Shape is a distinct 10th-level
    # feature, not reachable via the generic max-CR formula above (a
    # level-10 Moon Druid's generic max CR is only 3, not the 5 these
    # elementals require), so it needs its own explicit gate.
    if is_moon and druid_lvl >= 10:
        for elem in ("Air Elemental", "Water Elemental", "Earth Elemental", "Fire Elemental"):
            if elem in WILDSHAPE_BEASTS and elem not in out:
                out.append(elem)
    return out


def get_martial_arts_die(char: dict) -> str:
    monk_lvl = class_levels(char).get("Monk", 0)
    if monk_lvl == 0:
        return "—"
    edition = char.get("edition", "2014")
    if edition == "2024":
        if monk_lvl >= 17: return "1d12"
        if monk_lvl >= 11: return "1d10"
        if monk_lvl >= 5:  return "1d8"
        return "1d6"
    else:
        if monk_lvl >= 17: return "1d10"
        if monk_lvl >= 11: return "1d8"
        if monk_lvl >= 5:  return "1d6"
        return "1d4"


def get_ki_points(char: dict) -> int:
    return class_levels(char).get("Monk", 0)


def get_rage_damage(char: dict) -> str:
    barb_lvl = class_levels(char).get("Barbarian", 0)
    if barb_lvl == 0:
        return "—"
    if barb_lvl >= 16:
        return "+4"
    elif barb_lvl >= 9:
        return "+3"
    else:
        return "+2"


def get_carry_capacity(char: dict) -> int:
    """STR score × 15 lb, doubled by: Aspect of the Beast (Bear totem,
    Barbarian Path of the Totem Warrior, 6th level); Powerful Build
    (racial trait, e.g. Goliath/Firbolg — restored here after this
    function's name briefly collided with and shadowed the original,
    dict-returning version that had this check); or Peerless Athlete
    (Paladin, Oath of Glory, toggle). Multiple doubling sources don't
    stack multiplicatively — any one of them doubles the base once."""
    base = ability_score(char, "STR") * 15
    doubled = False

    barb_lvl = class_levels(char).get("Barbarian", 0)
    barb_sub = subclasses(char).get("Barbarian", "")
    if barb_lvl >= 6 and "totem warrior" in barb_sub.lower():
        picks = char.get("_choices", {}).get("totem_spirit_3", [])
        if any("bear" in p.lower() for p in picks):
            doubled = True

    if _has_trait(char, "Powerful Build"):
        doubled = True

    if "Peerless Athlete" in char.get("active_effects", []):
        doubled = True

    return base * 2 if doubled else base


def get_total_weight(char: dict) -> float:
    total = 0.0
    for item in char.get("equipment", []):
        total += item.get("weight", 0) * item.get("qty", 1)
    armor_name = char.get("armor_worn", "No Armor")
    armor = ARMOR_DICT.get(armor_name)
    if armor:
        total += armor.get("weight", 0)
    if char.get("shield"):
        total += 6  # standard shield weight
    for w in char.get("weapons", []):
        # look up weapon weight
        from ..data.phbCommon.items import WEAPON_DICT
        wd = WEAPON_DICT.get(w["name"])
        if wd:
            total += wd.get("weight", 0)
    return total


def restore_hit_dice_pool(char: dict) -> int:
    """
    Long-rest hit-dice recovery (PHB p.186): regain spent Hit Dice, up to a
    number of dice equal to HALF YOUR TOTAL HIT DICE (minimum 1), as a single
    shared pool across all die types — not independently per type.

    The previous implementation restored max(1, total//2) for EACH die type
    independently, which under-restored single-class characters at level 2-3
    (floor rounding gave "1" no matter how large the pool should be) and wildly
    over-restored multiclass characters (each small class bucket got its own
    minimum-1 top-up). This version pools correctly and prioritises the
    character's primary (first-listed) class die, matching how most tables
    play it. Returns the number of dice actually restored.
    """
    import math
    hd_dict = char.get("hit_dice", {})
    if not hd_dict:
        return 0
    total_dice = sum(d.get("total", 0) for d in hd_dict.values())
    pool = max(1, math.ceil(total_dice / 2))
    ordered_keys = []
    for cls_entry in char.get("classes", []):
        hd_key = f"d{cls_entry.get('hit_die', 8)}"
        if hd_key in hd_dict and hd_key not in ordered_keys:
            ordered_keys.append(hd_key)
    for k in hd_dict:
        if k not in ordered_keys:
            ordered_keys.append(k)
    restored = 0
    for hd_key in ordered_keys:
        if pool <= 0:
            break
        hd_data = hd_dict[hd_key]
        deficit = hd_data.get("total", 0) - hd_data.get("remaining", 0)
        give = min(deficit, pool)
        hd_data["remaining"] = hd_data.get("remaining", 0) + give
        pool -= give
        restored += give
    return restored


def has_weapon_proficiency(char: dict, weapon_name: str, category: str) -> bool:
    """
    Check whether the character is proficient with a given weapon, using the
    aggregated char["weapon_proficiencies"] strings (free-text, comma-joined
    grants from class/race/background/feat). Understands the "Simple weapons"
    / "Martial weapons" blanket grants plus specific named weapons.
    """
    profs = char.get("weapon_proficiencies", [])
    if not profs:
        return False
    blob = ", ".join(profs).lower()
    cat = (category or "").lower()
    if "simple weapon" in blob and "simple" in cat:
        return True
    if "martial weapon" in blob and "martial" in cat:
        return True
    # Named-weapon grants (e.g. "hand crossbows, longswords, rapiers").
    # Compare singular and a naive plural form against the blob.
    wname = (weapon_name or "").lower().strip()
    if not wname:
        return False
    if wname in blob:
        return True
    plural = wname + "s" if not wname.endswith("s") else wname
    if plural in blob:
        return True
    return False


def get_effective_speed(char: dict) -> dict:
    """
    Single source of truth for all movement speeds, folding in:
      - base walking speed + monk unarmored speed bonus + magic item bonus
      - Barbarian Fast Movement (+10 ft while not wearing heavy armor)
      - active spell effects (Haste doubles, Longstrider +10, etc.)
      - exhaustion (level 2+: half speed; level 5+: speed 0)  — PHB p.291
    Returns {'walk':int, 'fly':int, 'swim':int, 'climb':int}.
    """
    from .effects import effect_speed
    from dnd_app.data.phbCommon.items import ARMOR_DICT
    from .magic_items import parse_magic_suffix
    base = char.get("speed", 30) + char.get("monk_speed_bonus", 0) + char.get("magic_speed_bonus", 0)

    # Subrace walking speed bonuses: Wood Elf, Half-Elf Wood Descent, and
    # Shifter Swiftstride each grant +5 ft base walking speed.
    subrace_speed = (char.get("subrace") or "").lower()
    if "wood" in subrace_speed or "swiftstride" in subrace_speed:
        base += 5

    # Race-granted swim/climb speeds. Each race's specific value is used
    # rather than a generic guess — some are a flat number, others scale
    # to match walking speed.
    race_name_sp = (char.get("species") or char.get("race", "")).strip()
    race_swim_bonus = 0
    race_climb_bonus = 0
    if race_name_sp in ("Locathah", "Triton", "Merfolk"):
        race_swim_bonus = 30
    elif race_name_sp == "Tabaxi":
        race_climb_bonus = 20
    elif race_name_sp in ("Genasi", "Genasi (MPMM)") and "water" in subrace_speed and race_name_sp == "Genasi":
        race_swim_bonus = 30
    # "equal to your walking speed" races are computed from the final,
    # fully-bonused walk value further below, not this early base —
    # otherwise they'd miss later bonuses like Barbarian Fast Movement.
    race_swim_matches_walk = race_name_sp in ("Triton (MPMM)", "Giff") or (
        race_name_sp == "Genasi (MPMM)" and "water" in subrace_speed) or \
        "Alter Self: Aquatic Adaptation" in char.get("active_effects", []) or \
        any(inv.split(" (")[0].strip() == "Gift of the Depths" for inv in char.get("eldritch_invocations", []))
    race_climb_matches_walk = race_name_sp in ("Tabaxi (MPMM)", "Hadozee") or \
        "Spider Climb" in char.get("active_effects", [])
    # Roving (Ranger's Deft Explorer, TCE optional, 6th level): climb
    # and swim speed equal to walking speed, plus a flat +5 ft walking
    # speed bonus.
    ranger_lvl_rv = class_levels(char).get("Ranger", 0)
    roving_on = ranger_lvl_rv >= 6 and (
        char.get("_choices", {}).get("optional_features", {}).get("Deft Explorer", False)
        or char.get("optional_rules", {}).get("deft_explorer", False))
    if roving_on:
        race_swim_matches_walk = True
        race_climb_matches_walk = True
        char["_speed_bonus_sources"] = [("Roving (Deft Explorer)", 5)]
    else:
        char["_speed_bonus_sources"] = []

    # Storm Soul (Barbarian, Storm Herald, 6th level, Sea environment): 30 ft. swim speed.
    swim_bonus = 0
    barb_lvl_storm = class_levels(char).get("Barbarian", 0)
    if barb_lvl_storm >= 6 and "storm herald" in subclasses(char).get("Barbarian", "").lower():
        storm_picks = char.get("_choices", {}).get("storm_aura_3", [])
        if any("sea" in p.lower() for p in storm_picks):
            swim_bonus = 30

    # Fast Movement: +10 ft while not wearing heavy armor. Checked via a
    # positive lookup against ARMOR_DICT's weight category, same pattern
    # used elsewhere (e.g. Defense fighting style) to correctly exclude
    # Unarmored Defense and other non-armor AC sources from counting as
    # "wearing armor" in the first place.
    barb_lvl = class_levels(char).get("Barbarian", 0)
    if barb_lvl >= 5:
        armor_name = char.get("armor_worn", "No Armor")
        base_armor_name, _ = parse_magic_suffix(armor_name)
        armor_entry = ARMOR_DICT.get(base_armor_name)
        is_heavy = armor_entry is not None and armor_entry.get("type") == "heavy"
        if not is_heavy:
            base += 10

    # Elk Totem Spirit (Barbarian Path of the Totem Warrior, 3rd level):
    # +15 ft. while not wearing heavy armor. Computed independently of
    # Fast Movement's is_heavy above, since that's gated behind level 5
    # and wouldn't exist yet for an Elk Totem Warrior at 3rd-4th level.
    if barb_lvl >= 3 and "totem warrior" in subclasses(char).get("Barbarian", "").lower():
        elk_picks = char.get("_choices", {}).get("totem_spirit_3", [])
        if any("elk" in p.lower() for p in elk_picks):
            elk_armor_name = char.get("armor_worn", "No Armor")
            elk_base_armor, _ = parse_magic_suffix(elk_armor_name)
            elk_armor_entry = ARMOR_DICT.get(elk_base_armor)
            elk_is_heavy = elk_armor_entry is not None and elk_armor_entry.get("type") == "heavy"
            if not elk_is_heavy:
                base += 15

    # Powered Steps (Artificer Armorer, Infiltrator model, 3rd level): +5 ft.
    art_lvl = class_levels(char).get("Artificer", 0)
    if art_lvl >= 3 and "armorer" in subclasses(char).get("Artificer", "").lower():
        picks = char.get("_choices", {}).get("armorer_model_3", [])
        if any("infiltrator" in p.lower() for p in picks):
            base += 5

    # Aura of Alacrity (Paladin, Oath of Glory, 7th level): always-on +10 ft.
    pal_lvl_aura = class_levels(char).get("Paladin", 0)
    if pal_lvl_aura >= 7 and "glory" in subclasses(char).get("Paladin", "").lower():
        base += 10

    # Bladesong (Wizard, Bladesinging, 2nd level): +10 ft while active.
    if "Bladesong" in char.get("active_effects", []):
        base += 10

    # Stalker's Prowess (Blood Hunter, Order of the Lycan, 7th level):
    # always-on +10 ft, not tied to Hybrid Transformation being active.
    bh_lvl_speed = class_levels(char).get("Blood Hunter", 0)
    if bh_lvl_speed >= 7 and "lycan" in subclasses(char).get("Blood Hunter", "").lower():
        base += 10

    # Dark Augmentation (Blood Hunter Core, 10th level): always-on +5 ft,
    # regardless of Order.
    if bh_lvl_speed >= 10:
        base += 5

    # Mobile (feat): always-on +10 ft.
    if "Mobile" in char.get("feats", []):
        base += 10

    # Squat Nimbleness (feat, Dwarf/Small race): always-on +5 ft.
    if "Squat Nimbleness" in char.get("feats", []):
        base += 5

    walk = effect_speed(char, base)
    exh = char.get("exhaustion", 0)
    if exh >= 5:
        walk = 0
    elif exh >= 2:
        walk = walk // 2
    # Grappled/Restrained ("speed becomes 0") and Paralyzed/Petrified/
    # Stunned/Unconscious ("can't move") each zero every movement speed a
    # creature has, not just walking. Incapacitated alone does not stop
    # movement, and Prone only restricts movement to crawling, so neither
    # is included here.
    active_conditions = set(char.get("conditions", []))
    speed_locked = bool(active_conditions & {
        "Grappled", "Restrained", "Paralyzed", "Petrified", "Stunned", "Unconscious",
    })
    if speed_locked:
        walk = 0
    if race_swim_matches_walk:
        race_swim_bonus = walk
    if race_climb_matches_walk:
        race_climb_bonus = walk
    # Investiture of Wind (spell): flying speed 60 ft.
    race_fly_bonus = 60 if "Investiture of Wind" in char.get("active_effects", []) else 0
    return {
        "walk": max(0, walk),
        "fly": 0 if speed_locked else max(char.get("fly_speed", 0), race_fly_bonus),
        "swim": 0 if speed_locked else max(char.get("swim_speed", 0), swim_bonus, race_swim_bonus),
        "climb": 0 if speed_locked else max(char.get("climb_speed", 0), race_climb_bonus),
    }


def get_character_senses(char: dict) -> dict:
    """Returns the character's senses as a structured dict, e.g.
    {"darkvision": 60, "blindsight": 0, "tremorsense": 0, "truesight": 0}.
    Parsed from race trait text and subrace description text rather than
    a new explicit data field, since the existing traits are already
    consistently formatted and re-tagging every race would duplicate data
    that's already there. Standard 5e senses only (darkvision, blindsight,
    tremorsense, truesight) — the source material listed several
    non-standard terms (scent, tremorsense, lifesight, mindsight, etc.)
    that don't correspond to anything in this game's actual senses system
    for the races currently in this database.

    Wild Shape entirely REPLACES the character's own senses with the
    beast's — not a merge of both — matching the real rule ('you can't
    use any of your special senses... unless your new form also has that
    sense'): you're seeing through the beast's eyes, not your own.
    """
    import re
    senses = {"darkvision": 0, "blindsight": 0, "tremorsense": 0, "truesight": 0}

    active_beast = char.get("_wildshape_active")
    if active_beast:
        from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(active_beast, {})
        beast_senses_text = beast.get("senses", "")
        for sense_name in senses:
            m = re.search(rf"{sense_name} (\d+) ?ft", beast_senses_text, re.I)
            if m:
                senses[sense_name] = int(m.group(1))
        return senses

    from dnd_app.data.phb2014.races import get_race
    species = char.get("species") or char.get("race", "")
    subrace = char.get("subrace", "") or ""
    race = get_race(species)
    if race:
        # Base race traits first
        for t in race.get("traits", []):
            for sense_name in senses:
                m = re.search(rf"{sense_name} (\d+) ?ft", t, re.I)
                if m:
                    senses[sense_name] = max(senses[sense_name], int(m.group(1)))

        # Subrace text can upgrade a sense (e.g. Drow/Duergar's Superior
        # Darkvision to 120 ft) — take the higher value if both are present.
        for sub_text in race.get("subraces", []) or []:
            clean_name = sub_text.split("(")[0].strip()
            if clean_name.lower() not in subrace.lower() and subrace.lower() not in clean_name.lower():
                continue
            for sense_name in senses:
                m = re.search(rf"{sense_name} (\d+) ?ft", sub_text, re.I)
                if m:
                    senses[sense_name] = max(senses[sense_name], int(m.group(1)))

    # Blind Fighting fighting style: blindsight 10 ft, a genuinely
    # different sense source from race — checked separately here rather
    # than folded into the race-trait loop above, and deliberately outside
    # the "if race:" block since it doesn't depend on having valid race data.
    if any("blind fighting" in fs.lower() for fs in char.get("fighting_styles", [])):
        senses["blindsight"] = max(senses["blindsight"], 10)

    # Devil's Sight (Eldritch Invocation): darkvision 120 ft. This system
    # doesn't distinguish magical vs nonmagical darkness, so granting 120ft
    # unconditionally is the closest accurate approximation.
    if char.get("_devils_sight", False):
        senses["darkvision"] = max(senses["darkvision"], 120)

    # Keenness of the Stone Giant (feat): darkvision 60 ft., or +60 ft.
    # range if you already have darkvision from another source.
    if "Keenness of the Stone Giant" in char.get("feats", []):
        if senses["darkvision"] > 0:
            senses["darkvision"] += 60
        else:
            senses["darkvision"] = 60

    # Orb of the Veil (magic item): darkvision 60 ft., or +60 ft. range
    # if you already have darkvision from another source -- same
    # additive shape as Keenness of the Stone Giant above.
    from .magic_items import _active_item_names as _senses_active_item_names
    if "Orb of the Veil" in _senses_active_item_names(char):
        if senses["darkvision"] > 0:
            senses["darkvision"] += 60
        else:
            senses["darkvision"] = 60

    # Doppelganger (DM Reward): darkvision 60 ft.
    if "Doppelganger" in char.get("dm_rewards", []):
        senses["darkvision"] = max(senses["darkvision"], 60)

    # Darkvision (spell): darkvision 60 ft.
    if "Darkvision" in char.get("active_effects", []):
        senses["darkvision"] = max(senses["darkvision"], 60)

    # Draconic Transformation (spell): real blindsight 30 ft. grant.
    if "Draconic Transformation" in char.get("active_effects", []):
        senses["blindsight"] = max(senses["blindsight"], 30)

    # Magic items (Goggles of Night, Dragon Masks, etc.) — populated by
    # apply_all_magic_item_effects()'s "senses" effect type.
    for sense_name, val in char.get("magic_senses", {}).items():
        if sense_name in senses:
            senses[sense_name] = max(senses[sense_name], val)

    return senses


def compute_max_hp(char: dict) -> int:
    """
    Compute maximum HP from class levels + CON.
    PHB: only the very first character level uses max die value.
    All other levels (including multiclass level 1) use floor(hd/2)+1,
    unless the "max_hp_per_level" optional rule is on, in which case
    every level uses the hit die's maximum value instead — a common
    table variant, not an official rule.
    Class order is preserved from char['classes'] — first entry = primary class.
    """
    classes = char.get("classes", [])
    if not classes:
        return 0
    from dnd_app.data.phb2014.classes import CLASS_DICT
    con = ability_mod(char, "CON", ignore_wildshape=True)
    total = total_level(char)
    tough_bonus = 2 * total if "Tough" in char.get("feats", []) else 0
    max_per_level = char.get("optional_rules", {}).get("max_hp_per_level", False)

    hp = 0
    first_level_done = False
    for entry in classes:
        cname = entry.get("class", "")
        lvl   = entry.get("level", 1)
        hd    = entry.get("hit_die") or CLASS_DICT.get(cname, {}).get("hit_die", 8)
        avg   = hd if max_per_level else hd // 2 + 1  # PHB average formula, or max if the optional rule is on
        if not first_level_done:
            # Character level 1: max hit die
            hp += hd + con
            hp += (avg + con) * (lvl - 1)
            first_level_done = True
        else:
            # Multiclass entries: every level uses average (incl. their 'level 1')
            hp += (avg + con) * lvl

    # Draconic Resilience (Sorcerer, Draconic Bloodline, 1st level):
    # +1 HP per Sorcerer level.
    from dnd_app.core.character import subclasses as _subclasses_hp, class_levels as _class_levels_hp
    sorc_lvl = _class_levels_hp(char).get("Sorcerer", 0)
    if sorc_lvl > 0 and "draconic" in _subclasses_hp(char).get("Sorcerer", "").lower():
        hp += sorc_lvl

    return hp + tough_bonus


def preview_level_gain(char: dict, cls_name: str, is_new: bool) -> dict:
    """Pure preview of what gaining a level in `cls_name` would grant —
    HP and spell-slot deltas — without mutating `char`. Used by the
    Level Up / Multiclass dialog's "What You'll Get" panel so a player
    can see the numbers before committing, rather than only the class's
    static per-level feature list.

    `is_new` marks a brand-new multiclass entry (added at level 1)
    rather than an existing class going up one level. Only computes HP
    and spell slots — feature text is already handled separately by the
    dialog from CLASS_DICT's per-level feature list.

    Returns {"hp_gain", "hp_before", "hp_after", "slot_deltas",
    "pact_before", "pact_after"}. slot_deltas is a list of
    (spell_level, delta) for every spell level whose max slots change;
    pact_before/after are the Warlock pact slot dicts (count/level) or
    None, since those live outside the standard spell_slots array."""
    import copy
    from dnd_app.data.phb2014.classes import CLASS_DICT

    hp_before = compute_max_hp(char)
    cur_cl, cur_subs = class_levels(char), subclasses(char)
    cur_slot_info = compute_all_spell_slots(cur_cl, cur_subs)

    hyp = copy.deepcopy(char)
    if is_new:
        hd = CLASS_DICT.get(cls_name, {}).get("hit_die", 8)
        hyp.setdefault("classes", []).append(
            {"class": cls_name, "level": 1, "subclass": "", "hit_die": hd})
    else:
        for entry in hyp.get("classes", []):
            if entry.get("class") == cls_name:
                entry["level"] = min(20, entry.get("level", 1) + 1)
                break

    hp_after = compute_max_hp(hyp)
    new_cl, new_subs = class_levels(hyp), subclasses(hyp)
    new_slot_info = compute_all_spell_slots(new_cl, new_subs)

    cur_slots, new_slots = cur_slot_info["spell_slots"], new_slot_info["spell_slots"]
    slot_deltas = [(lvl + 1, new_slots[lvl] - cur_slots[lvl])
                   for lvl in range(9) if new_slots[lvl] != cur_slots[lvl]]

    return {
        "hp_gain": hp_after - hp_before, "hp_before": hp_before, "hp_after": hp_after,
        "slot_deltas": slot_deltas,
        "pact_before": cur_slot_info.get("warlock_slots"),
        "pact_after": new_slot_info.get("warlock_slots"),
    }


def update_all(char: dict) -> dict:
    """
    Recompute all derived stats and update the character dict.
    Returns the updated character dict.
    """
    cl = class_levels(char)
    subs = subclasses(char)
    # Effective ability scores (base + ability_bonuses from ASI/racial
    # ASI + magic_ability_bonuses from items + ability_overrides), not
    # just the raw base char["abilities"] — this feeds aggregate_
    # resources()'s ability-modifier formulas (Bardic Inspiration's
    # CHA_mod, Hexblade's Curse, War Priest, Momentary Stasis, and
    # every other ability-mod-driven resource in classes.py/
    # classes_2024.py/_add_subclass_resources()), so a raw-base-only
    # dict here meant an ASI, racial ASI, or item bonus to that ability
    # never actually raised the resource's max uses. ignore_wildshape
    # matches max-HP's own convention: a resource's max shouldn't
    # fluctuate just because the character is currently Wild Shaped.
    ability_scores = {ab: ability_score(char, ab, ignore_wildshape=True)
                       for ab in ("STR", "DEX", "CON", "INT", "WIS", "CHA")}
    total = total_level(char)

    if total == 0:
        return char

    # ── Proficiency Bonus ─────────────────────────────────────────────────────
    pb = prof_bonus(total)

    # ── Spell slots ───────────────────────────────────────────────────────────
    slot_info = compute_all_spell_slots(cl, subs)
    # Only update max slots (don't override used)
    char["spell_slots_max"] = slot_info["spell_slots"]
    if slot_info["warlock_slots"]:
        ws = slot_info["warlock_slots"]
        char["pact_slots_max"] = ws["count"]
        char["pact_slot_level"] = ws["level"]

    # Saving throws are set by rebuild(); do not overwrite here.

    # ── Magic items ───────────────────────────────────────────────────────────
    from .magic_items import apply_all_magic_item_effects, _active_item_names
    apply_all_magic_item_effects(char)

    # Armor of Vulnerability: speed -10 ft while worn, but only if the
    # wearer's STR is below 15 -- a per-character conditional the generic
    # data-driven magic-item-effect system has no way to express, so
    # checked directly here (same pattern as Heavy Armor Master below).
    # Its Stealth disadvantage is the ordinary, unconditional part of the
    # same item and is wired normally via MAGIC_ITEM_EFFECTS.
    if "Armor of Vulnerability" in _active_item_names(char) and ability_score(char, "STR") < 15:
        char["magic_speed_bonus"] = char.get("magic_speed_bonus", 0) - 10
        char.setdefault("_speed_bonus_sources", []).append(("Armor of Vulnerability", -10))

    # Exhaustion level 1+: disadvantage on ability checks (PHB p.291),
    # layered on top of whatever magic items already contributed to
    # skill_disadvantages via the same list/source-tracking mechanism.
    if char.get("exhaustion", 0) >= 1:
        from dnd_app.data.phb2014.classes import SKILLS as _ALL_SKILLS
        dis = char.setdefault("skill_disadvantages", [])
        src = char.setdefault("_skill_disadvantage_sources", {})
        for sk in _ALL_SKILLS:
            if sk not in dis:
                dis.append(sk)
            src.setdefault(sk, []).append("Exhaustion (level 1+)")

    # Frightened/Poisoned: disadvantage on ability checks (PHB p.290-291),
    # via the same list/source-tracking mechanism as exhaustion above.
    # Frightened's real text ties this to the fear source being in
    # sight, which this app has no way to know, so — matching the same
    # simplification used for its attack-roll disadvantage in
    # get_condition_attack_status — it applies unconditionally whenever
    # the condition is checked.
    _active_conds_for_checks = set(char.get("conditions", []))
    for _cond_name in ("Frightened", "Poisoned"):
        if _cond_name in _active_conds_for_checks:
            from dnd_app.data.phb2014.classes import SKILLS as _ALL_SKILLS
            dis = char.setdefault("skill_disadvantages", [])
            src = char.setdefault("_skill_disadvantage_sources", {})
            for sk in _ALL_SKILLS:
                if sk not in dis:
                    dis.append(sk)
                src.setdefault(sk, []).append(_cond_name)

    # Actor: advantage on Deception/Performance checks to pass as a different person.
    if "Actor" in char.get("feats", []):
        adv = char.setdefault("skill_advantages", [])
        src2 = char.setdefault("_skill_advantage_sources", {})
        for sk in ("Deception", "Performance"):
            if sk not in adv:
                adv.append(sk)
            src2.setdefault(sk, []).append("Actor (passing as a different person)")

    # Spirit Medium (DM Reward): advantage on Arcana/Religion checks related to spirits/the afterlife.
    if "Spirit Medium" in char.get("dm_rewards", []):
        adv2 = char.setdefault("skill_advantages", [])
        src3 = char.setdefault("_skill_advantage_sources", {})
        for sk in ("Arcana", "Religion"):
            if sk not in adv2:
                adv2.append(sk)
            src3.setdefault(sk, []).append("Spirit Medium (spirits/the afterlife)")

    # ── Active-effect / racial / feat / subclass-passive resistances ──────────
    # apply_all_magic_item_effects() just reset damage_resistances to only
    # what's sourced from equipped magic items — add back everything else
    # (Rage, Hybrid Transformation, racial traits, feats, subclass passives
    # like Storm Sorcery's Heart of the Storm, etc.) so toggling an effect
    # doesn't get silently wiped by the very next refresh.
    if "Hybrid Transformation" in char.get("active_effects", []):
        res = char.setdefault("damage_resistances", [])
        for dmg_type in ("bludgeoning (nonmagical, non-silvered)",
                        "piercing (nonmagical, non-silvered)",
                        "slashing (nonmagical, non-silvered)"):
            entry = (dmg_type, "Hybrid Transformation")
            if entry not in res:
                res.append(entry)

    # Generic active-effect resistance/ability-override hooks (mainly
    # consumable potions — Potion of Invulnerability, the resistance
    # potions, the Giant Strength potions). Reuses the exact same
    # add-back-after-magic-items-reset pattern as Hybrid Transformation
    # just above, driven by EFFECT_TABLE instead of a hardcoded name so
    # new active effects don't each need their own bespoke block here.
    from .effects import EFFECT_TABLE as _EFFECT_TABLE
    for _fx_name in char.get("active_effects", []):
        _fx_info = _EFFECT_TABLE.get(_fx_name, {})
        for _dmg_type in _fx_info.get("resistance", []):
            res = char.setdefault("damage_resistances", [])
            entry = (_dmg_type, _fx_name)
            if entry not in res:
                res.append(entry)
        for _ab, _val in _fx_info.get("ability_override", {}).items():
            overrides = char.setdefault("ability_overrides", {})
            overrides[_ab] = max(overrides.get(_ab, 0), _val)

    # Heavy Armor Master: -3 flat damage reduction (not true resistance)
    # against nonmagical bludgeoning/piercing/slashing, while wearing
    # heavy armor. Shown alongside resistances per design — labeled
    # clearly as a reduction, not folded into any resistance-halving
    # calculation, since the two are mechanically different things.
    heavy_armors_ham = {"Plate", "Splint", "Ring Mail", "Chain Mail", "Half Plate"}
    if ("Heavy Armor Master" in char.get("feats", [])
            and char.get("armor_worn") in heavy_armors_ham):
        res = char.setdefault("damage_resistances", [])
        entry = ("bludgeoning/piercing/slashing (nonmagical) \u22123 damage", "Heavy Armor Master")
        if entry not in res:
            res.append(entry)

    for grant in get_innate_resistance_grants(char):
        kind = grant["kind"]
        source = grant["source"]
        if kind == "resistance":
            label = grant["target"] + (" (nonmagical)" if grant.get("nonmagical") else "")
            res = char.setdefault("damage_resistances", [])
            entry = (label, source)
            if entry not in res: res.append(entry)
        elif kind == "immunity":
            imm = char.setdefault("damage_immunities", [])
            entry = (grant["target"], source)
            if entry not in imm: imm.append(entry)
        elif kind == "condition":
            imm = char.setdefault("damage_immunities", [])
            entry = (f"{grant['condition']} (condition)", source)
            if entry not in imm: imm.append(entry)

    # ── Swim/climb/fly speeds (racial traits, subclass features/toggles) ─────
    _moves = get_innate_movement_grants(char)
    char["swim_speed"] = _moves["swim"]
    char["climb_speed"] = _moves["climb"]
    char["fly_speed"] = _moves["fly"]

    # Magic items granting a swim/climb/fly speed (Ring of Swimming, Cloak
    # of the Manta Ray, Wings of Flying, etc.) are computed here, after
    # apply_all_magic_item_effects() already ran earlier in this
    # function, since that's the only point a magic item can reach them.
    # "walking" as a value means "equal to your walking speed", matching
    # how most of these items are actually worded.
    from .magic_items import _active_item_names as _active_magic_item_names
    from dnd_app.data.phbCommon.magic_items import get_item_effect as _get_item_effect
    walk_speed = char.get("speed", 30) + char.get("magic_speed_bonus", 0)
    for _fx_name in _active_magic_item_names(char):
        _fx_info = _get_item_effect(_fx_name)
        if not _fx_info:
            continue
        for _sub in (_fx_info if isinstance(_fx_info, list) else [_fx_info]):
            if _sub.get("type") not in ("swim_speed", "climb_speed", "fly_speed"):
                continue
            _val = _sub.get("value", 0)
            _val = walk_speed if _val == "walking" else _val
            char[_sub["type"]] = max(char.get(_sub["type"], 0), _val)

    # ── Max HP ────────────────────────────────────────────────────────────────
    # hp_max_override lets a player manually set Max HP (homebrew items, DM
    # rulings, features this app doesn't model) without it being silently
    # overwritten by the next recompute — the override IS the computed value.
    override = char.get("hp_max_override")
    base_max = override if override is not None else compute_max_hp(char)
    base_max += char.get("magic_hp_max_bonus", 0)
    # Exhaustion level 4+: hit point maximum is halved (PHB p.291). Applied as
    # a display-time adjustment (not baked into the stored/override value) so
    # recovering from exhaustion correctly restores full max HP.
    new_max = base_max // 2 if char.get("exhaustion", 0) >= 4 else base_max
    if new_max > 0:
        diff = new_max - char.get("max_hp", 0)
        char["max_hp"] = new_max
        # A level-up genuinely grants new hit points (PHB: you gain hit
        # points equal to the new hit die roll/average + CON), so current
        # HP should rise with it. Other sources of a higher max — a CON
        # score increase, attuning a magic item with an hp_max_bonus,
        # exhaustion 4+ clearing — only raise the ceiling, not your
        # current HP, per the real rule text for each (none of them say
        # "and you gain that many hit points"). Gated on whether total
        # character level actually went up since the last recompute,
        # since compute_max_hp() has no other way to tell why max grew.
        prev_level = char.get("_hp_level_snapshot")
        cur_level = total_level(char)
        char["_hp_level_snapshot"] = cur_level
        leveled_up = prev_level is None or cur_level > prev_level
        if diff > 0 and leveled_up:
            char["current_hp"] = min(char["current_hp"] + diff, new_max)
        else:
            # Max HP dropped, or rose from a non-level-up source: clamp
            # current HP down if it now exceeds the new max, otherwise
            # leave it exactly as it was.
            char["current_hp"] = min(char.get("current_hp", new_max), new_max)
    # Exhaustion level 6: death (PHB p.291).
    if char.get("exhaustion", 0) >= 6 and char.get("current_hp", 1) > 0:
        char["current_hp"] = 0
        char["_died_of_exhaustion"] = True

    # ── Hit Dice ──────────────────────────────────────────────────────────────
    hit_dice = {}
    for c in char.get("classes", []):
        if c.get("level", 0) > 0:
            # Self-heal: correct any stale hit_die against class data
            from dnd_app.core.character import _lookup_hit_die
            correct_hd = _lookup_hit_die(c.get("class",""), c.get("hit_die", 8))
            if c.get("hit_die") != correct_hd:
                c["hit_die"] = correct_hd
            hd_key = f"d{c['hit_die']}"
            existing = char.get("hit_dice", {}).get(hd_key, {})
            total_for_class = c["level"]
            remaining = existing.get("remaining", total_for_class)
            hit_dice[hd_key] = {
                "total": total_for_class,
                "remaining": min(remaining, total_for_class),
            }
    char["hit_dice"] = hit_dice

    # ── Resources from multiclass handler ────────────────────────────────────
    # Merge computed resources with existing ones (preserve current values)
    existing_resources = {r["key"]: r for r in char.get("resources", [])}
    new_resources = aggregate_resources(cl, ability_scores, subs, char.get("_choices", {}),
                                         char.get("optional_rules", {}),
                                         char.get("edition", "2014"))

    # Racial resources — not tied to any class, so added here where the
    # full char dict (race/subrace) is available rather than inside
    # aggregate_resources (which only receives class-related data).
    total_lvl_res = sum(v for v in cl.values())
    char_race_res = char.get("species") or char.get("race", "")
    char_subrace_res = (char.get("subrace") or "").lower()
    if char_race_res == "Aasimar" and total_lvl_res >= 3:
        if "protector" in char_subrace_res:
            new_resources.append({
                "name": "Radiant Soul (Aasimar)", "key": "radiant_soul",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Action, 1 min: fly speed 30 ft; once/turn extra radiant damage "
                        "equal to your level on a hit.",
                "source_class": "", "subclass": "",
            })
        elif "fallen" in char_subrace_res:
            new_resources.append({
                "name": "Necrotic Shroud", "key": "necrotic_shroud",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Action, 1 min: fly speed 30 ft; frightening 10-ft aura (CHA save); "
                        "once/turn extra necrotic damage equal to your level on a hit.",
                "source_class": "", "subclass": "",
            })
        elif "scourge" in char_subrace_res:
            new_resources.append({
                "name": "Radiant Consumption", "key": "radiant_consumption",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Action, 1 min: 10-ft radiant aura deals damage equal to half your "
                        "level to each creature in it (including you) at the end of your turn; "
                        "once/turn extra radiant damage equal to your level on a hit.",
                "source_class": "", "subclass": "",
            })
    # Aasimar (MPMM) Celestial Revelation scales by proficiency bonus,
    # not character level — a deliberate difference from the VGM
    # version's level-based scaling above.
    if char_race_res == "Aasimar (MPMM)" and total_lvl_res >= 3:
        revelation = char.get("_choices", {}).get("aasimar_revelation", [])
        rev_name = revelation[0] if revelation else ""
        pb_aasimar = get_prof_bonus(char)
        if rev_name == "Necrotic Shroud":
            new_resources.append({
                "name": "Necrotic Shroud (Aasimar)", "key": "necrotic_shroud_mpmm",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Bonus action, 1 min: frighten nearby non-allies (CHA save); once/turn "
                        f"extra necrotic damage = your proficiency bonus ({pb_aasimar}) on a hit.",
                "source_class": "", "subclass": "",
            })
        elif rev_name == "Radiant Consumption":
            new_resources.append({
                "name": "Radiant Consumption (Aasimar)", "key": "radiant_consumption_mpmm",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Bonus action, 1 min: shed light, deal proficiency-bonus radiant damage "
                        f"({pb_aasimar}) to nearby creatures each turn; once/turn extra radiant "
                        f"damage = your proficiency bonus on a hit.",
                "source_class": "", "subclass": "",
            })
        elif rev_name == "Radiant Soul":
            new_resources.append({
                "name": "Radiant Soul (Aasimar)", "key": "radiant_soul_mpmm",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Bonus action, 1 min: flying speed = walking speed; once/turn extra "
                        f"radiant damage = your proficiency bonus ({pb_aasimar}) on a hit.",
                "source_class": "", "subclass": "",
            })
    if char_race_res == "Dragonborn" and total_lvl_res >= 5 and "gem" in char_subrace_res:
        new_resources.append({
            "name": "Gem Flight", "key": "gem_flight",
            "reset": "LR", "current_max": 1, "track": "uses",
            "note": "1 minute: flying speed equal to your walking speed.",
            "source_class": "", "subclass": "",
        })
    if char_race_res == "Shifter":
        new_resources.append({
            "name": "Shifting", "key": "shifting",
            "reset": "SR/LR", "current_max": 1, "track": "uses",
            "note": "Bonus action, 1 min (or until you revert as a bonus action): gain temp HP "
                    "equal to your proficiency bonus + CON modifier (min 1), plus subrace-specific "
                    "benefits while shifted.",
            "source_class": "", "subclass": "",
        })

    # ── Feats whose limited-use ability scales as "proficiency bonus uses
    # per long rest" ─────────────────────────────────────────────────────
    known_feats_res = set(char.get("feats", []))
    pb_res = prof_bonus(total_lvl_res) if total_lvl_res > 0 else 1
    FEAT_PB_USES_RESOURCES = {
        "Ember of the Fire Giant": ("Searing Ignition", "Replace one Attack with a 15-ft.-radius fire "
            "burst: DEX save or 1d8 + proficiency bonus fire damage and blinded until your next turn "
            "(half damage on a save). Max once per turn."),
        "Fury of the Frost Giant": ("Frigid Retaliation", "Reaction after a creature within 30 ft. hits "
            "and damages you: CON save or it takes 1d8 + proficiency bonus cold damage and its speed "
            "drops to 0 until the end of its next turn."),
        "Guile of the Cloud Giant": ("Cloudy Escape", "Reaction when hit by an attack roll: gain "
            "resistance to that damage, then teleport to an unoccupied space you can see within 30 ft."),
        "Keenness of the Stone Giant": ("Stone Throw", "Bonus action: ranged spell attack with a rock, "
            "range 60 ft. — 1d10 force damage, STR save or prone."),
        "Soul of the Storm Giant": ("Maelstrom Aura", "Bonus action: 10-ft. aura of wind/lightning until "
            "the start of your next turn or incapacitated — resist lightning/thunder, attackers vs. you "
            "have disadvantage, creatures starting their turn in it make a STR save or speed is halved."),
        "Agent of Order": ("Stasis Strike", "Once per turn on damaging a creature within 60 ft.: extra "
            "1d8 force damage, WIS save or restrained until the start of your next turn."),
        "Baleful Scion": ("Grasp of Avarice", "Once per turn on damaging a creature within 60 ft.: extra "
            "1d6 + proficiency bonus necrotic damage, and regain that much HP."),
        "Righteous Heritor": ("Soothe Pain", "Reaction when you or a creature within 30 ft. takes "
            "damage: reduce it by 1d10 + proficiency bonus."),
        "Knight of the Crown": ("Commanding Rally", "Bonus action: command an ally within 30 ft. who "
            "can see/hear you to attack as a reaction; on a hit, they add 1d8 to the damage."),
        "Knight of the Rose": ("Bolstering Rally", "Bonus action: a creature you can see within 30 ft. "
            "(including yourself) who can see/hear you gains temp HP = 1d8 + proficiency bonus + the "
            "increased ability's modifier."),
        "Knight of the Sword": ("Demoralizing Strike", "Once per turn on a weapon attack hit, force a "
            "WIS save (DC 8 + proficiency bonus + the increased ability's modifier) or frighten the "
            "target until the end of your next turn."),
        "Squire of Solamnia": ("Precise Strike", "Once per turn on a weapon attack roll, give it "
            "advantage; if it hits, roll a d8 and add it to the damage (use expended only on a hit)."),
        "Gift of the Gem Dragon": ("Telekinetic Reprisal", "Reaction when a creature within 10 ft. "
            "damages you: it makes a STR save (DC 8 + proficiency bonus + the increased ability's "
            "modifier) or takes 2d8 force damage and is pushed 10 ft."),
        "Strike of the Giants": ("Strike of the Giants", "Once per turn on a melee or thrown-weapon "
            "hit, imbue it with your chosen benefit (extra damage + a save-based effect)."),
        "Cruel": ("Cruelty Dice (d6)", "Spend one: on damaging a creature, add the roll as extra "
            "damage; on a critical hit, gain that many temp HP instead; on a CHA (Intimidation) "
            "check, add the roll to it. One rollable per turn."),
    }
    for fname, (label, note) in FEAT_PB_USES_RESOURCES.items():
        if fname in known_feats_res:
            new_resources.append({
                "name": label, "key": fname.lower().replace(" ","_").replace("'",""),
                "reset": "LR", "current_max": max(1, pb_res), "track": "uses",
                "note": note, "source_class": "", "subclass": "",
            })

    # ── Feats with a fixed (not proficiency-bonus-scaled) number of uses ─────
    FEAT_FIXED_USES_RESOURCES = {
        "Fade Away": ("Fade Away", 1, "SR/LR",
            "Reaction immediately after taking damage: become invisible until the end of your next "
            "turn or until you attack, deal damage, or force a save."),
        "Second Chance": ("Second Chance", 1, "SR/LR",
            "Reaction when a creature hits you with an attack roll: force it to reroll."),
        "Svirfneblin Magic": ("Svirfneblin Magic", 3, "LR",
            "Cast blindness/deafness, blur, or disguise self (once each) without a spell slot. "
            "Nondetection on yourself is separately at-will, not tracked here."),
        "Cartomancer": ("Hidden Ace", 1, "LR",
            "Imbue a card with a spell you have a slot for (casting time 1 action); bonus action to "
            "flourish and cast it (lasts 8 hours if unused)."),
        "Rune Shaper": ("Rune Shaper (Invoke)", 1, "LR",
            "Invoke a rune you have inscribed to cast its spell without a spell slot or components."),
        "Divinely Favored": ("Divinely Favored", 2, "LR",
            "Cast your chosen 1st-level spell and augury, each once, without a spell slot."),
        "Aberrant Dragonmark": ("Aberrant Dragonmark", 1, "SR/LR",
            "Cast your chosen 1st-level spell through your mark without a spell slot."),
        "Lucky": ("Luck Points", 3, "LR",
            "Spend to roll an extra d20 for an attack roll, ability check, or save, or to make an "
            "attacker reroll against you."),
        "Martial Adept": ("Superiority Dice (Martial Adept)", 1, "SR/LR",
            "A d6 superiority die (stacks with any from another source) to fuel a learned maneuver."),
        "Metamagic Adept": ("Sorcery Points (Metamagic Adept)", 2, "LR",
            "Usable only on Metamagic options; stacks with any sorcery points from another source."),
        "Orcish Fury": ("Orcish Fury", 1, "SR/LR",
            "Reroll one damage die on a hit with a simple/martial weapon, adding it as extra damage."),
        "Outlands Envoy": ("Crossroads Emissary", 2, "LR",
            "Cast misty step and tongues, each once, without a spell slot."),
        "Planar Wanderer": ("Portal Sense (detect)", 1, "LR",
            "Action: detect any portals within 30 ft. not behind total cover. (Portal Cracker is "
            "per-portal, not a general use-limit, and isn't tracked here.)"),
        "Fey Teleportation": ("Fey Teleportation", 1, "SR/LR",
            "Cast misty step without a spell slot."),
        "Magic Initiate": ("Magic Initiate (1st-level spell)", 1, "LR",
            "Cast your chosen 1st-level spell at its lowest level without a spell slot."),
        "Strixhaven Initiate": ("Strixhaven Initiate (1st-level spell)", 1, "LR",
            "Cast your chosen 1st-level spell without a spell slot."),
        "Telepathic": ("Telepathic (Detect Thoughts)", 1, "LR",
            "Cast detect thoughts, using the ability increased by this feat, without a spell slot."),
        "Bandit Cunning": ("Bandit Cunning (Lucky Break)", 1, "LR",
            "Reaction: add your INT modifier to a saving throw you're making."),
        "Flamewoken": ("Empower Flames", 1, "SR/LR",
            "Bonus action: the next fire damage you deal to a creature before the end of your next "
            "turn adds +2d10 fire."),
        "Flash Recall": ("Flash Recall", 1, "SR/LR",
            "Bonus action: prepare a 1st-level+ spell of a level you have slots for, replacing an "
            "equal-or-higher-level prepared spell."),
        "Mystic Conflux": ("Mystic Conflux (Identify)", 1, "LR",
            "Cast identify without a spell slot or material components."),
    }
    for fname, (label, uses, reset, note) in FEAT_FIXED_USES_RESOURCES.items():
        if fname in known_feats_res:
            new_resources.append({
                "name": label, "key": fname.lower().replace(" ","_").replace("'",""),
                "reset": reset, "current_max": uses, "track": "uses",
                "note": note, "source_class": "", "subclass": "",
            })

    # Field Medic scales at half proficiency bonus (rounded down, min 1),
    # unlike the full-proficiency-bonus feats above.
    if "Field Medic" in known_feats_res:
        new_resources.append({
            "name": "Field Medic (Cure Wounds)", "key": "field_medic",
            "reset": "LR", "current_max": max(1, pb_res // 2), "track": "uses",
            "note": "Cast cure wounds without a spell slot, using WIS as your spellcasting ability.",
            "source_class": "", "subclass": "",
        })

    # Iconoclast (dm_rewards.py): level-gated tier system. Enlightened
    # Protection is unconditional; 3 more tiers unlock at levels 5/11/17.
    # Oracle's own Piety-gated tiers (Augur/Seer/Sibyl/Divine Oracle) are
    # not modeled — this app has no Piety-tracking mechanic to gate them on.
    if "Iconoclast" in char.get("dm_rewards", []):
        char_lvl_ic = total_level(char)
        new_resources.append({
            "name": "Enlightened Protection", "key": "dmreward_iconoclast_protection",
            "reset": "LR", "current_max": 1, "track": "uses",
            "note": "Cast protection from evil and good (self only, no material components) "
                    "without a spell slot, using WIS as your spellcasting ability.",
            "source_class": "", "subclass": "",
        })
        if char_lvl_ic >= 5:
            new_resources.append({
                "name": "Iconoclast Hero (Dispel Magic)", "key": "dmreward_iconoclast_hero",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": f"Cast dispel magic without a spell slot, using WIS as your spellcasting "
                        f"ability. Cast as a {'5th' if char_lvl_ic>=17 else '4th' if char_lvl_ic>=11 else '3rd'}-level spell.",
                "source_class": "", "subclass": "",
            })
        if char_lvl_ic >= 11:
            new_resources.append({
                "name": "Iconoclast Paragon (Dispel Evil/Good)", "key": "dmreward_iconoclast_paragon",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Cast dispel evil and good (no material components) without a spell "
                        "slot, using WIS as your spellcasting ability.",
                "source_class": "", "subclass": "",
            })
        if char_lvl_ic >= 17:
            new_resources.append({
                "name": "Iconoclast Archetype (Antimagic Field)", "key": "dmreward_iconoclast_archetype",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Cast antimagic field (no material components) without a spell slot, "
                        "using WIS as your spellcasting ability.",
                "source_class": "", "subclass": "",
            })

    # Yuan-ti Pureblood: Suggestion, once per long rest.
    race_sp = char.get("species") or char.get("race", "")
    if race_sp == "Yuan-ti Pureblood" and total_level(char) >= 3:
        new_resources.append({
            "name": "Suggestion (Yuan-ti)", "key": "yuanti_suggestion",
            "reset": "LR", "current_max": 1, "track": "uses",
            "note": "Cast suggestion without a spell slot, using your race's chosen spellcasting "
                    "ability.",
            "source_class": "", "subclass": "",
        })

    # Earth Genasi (MPMM) Merge with Stone: grants Blade Ward at level 1
    # and Pass Without Trace at level 5.
    if race_sp == "Genasi (MPMM)" and "earth" in (char.get("subrace") or "").lower():
        new_resources.append({
            "name": "Blade Ward (Bonus Action)", "key": "earth_genasi_blade_ward",
            "reset": "LR", "current_max": max(1, pb_res), "track": "uses",
            "note": "Cast Blade Ward as a bonus action (in addition to being able to cast it "
                    "normally, which doesn't use this resource).",
            "source_class": "", "subclass": "",
        })
        if total_level(char) >= 5:
            new_resources.append({
                "name": "Pass without Trace (Merge with Stone)", "key": "earth_genasi_pwt",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Cast pass without trace without a material component. Can also be cast "
                        "using a spell slot of 2nd level or higher instead of this resource.",
                "source_class": "", "subclass": "",
            })

    # Mind Sharpener and Spell-Refueling Ring (Artificer Infusions) are
    # gated on active_infusions, not just known, same as Resistant Armor
    # above. (Boots of the Winding Path has no limited uses, so it
    # belongs in the Actions tab, not here as a resource.)
    _active_inf_names = {inf.get("infusion") for inf in char.get("active_infusions", [])}
    if "Mind Sharpener" in _active_inf_names:
        new_resources.append({
            "name": "Mind Sharpener", "key": "mind_sharpener",
            "reset": "LR", "current_max": 4, "track": "uses",
            "note": "Reaction: expend 1 charge to automatically succeed a concentration save "
                    "you just failed. Regains 1d4 expended charges daily at dawn (not a full "
                    "reset — tracked as a flat max here for simplicity).",
            "source_class": "", "subclass": "",
        })
    if "Spell-Refueling Ring" in _active_inf_names:
        new_resources.append({
            "name": "Spell-Refueling Ring", "key": "spell_refueling_ring",
            "reset": "LR", "current_max": 1, "track": "uses",
            "note": "Action: recover one expended spell slot of 3rd level or lower.",
            "source_class": "", "subclass": "",
        })

    _known_inv = [inv.split(" (")[0].strip() for inv in char.get("eldritch_invocations", [])]
    _pb_res = get_prof_bonus(char)
    if "Cloak of Flies" in _known_inv:
        new_resources.append({
            "name": "Cloak of Flies", "key": "cloak_of_flies",
            "reset": "SR/LR", "current_max": 1, "track": "uses",
            "note": "Bonus action: 5-ft. aura of buzzing flies. Adv. Intimidation, disadv. other "
                    "CHA checks. Others starting their turn in it take CHA-mod poison damage "
                    "(min 0). Lasts until dismissed (bonus action) or you're incapacitated.",
            "source_class": "", "subclass": "",
        })
    if "Bond of the Talisman" in _known_inv:
        new_resources.append({
            "name": "Bond of the Talisman", "key": "bond_of_the_talisman",
            "reset": "LR", "current_max": max(1, _pb_res), "track": "uses",
            "note": "Action: teleport to the unoccupied space closest to your talisman's "
                    "wearer (same plane only). The wearer can do the same to reach you.",
            "source_class": "", "subclass": "",
        })
    if "Protection of the Talisman" in _known_inv:
        new_resources.append({
            "name": "Protection of the Talisman", "key": "protection_of_the_talisman",
            "reset": "LR", "current_max": max(1, _pb_res), "track": "uses",
            "note": "The talisman's wearer can add a d4 to a failed saving throw.",
            "source_class": "", "subclass": "",
        })
    if "Gift of the Protectors" in _known_inv:
        new_resources.append({
            "name": "Gift of the Protectors", "key": "gift_of_the_protectors",
            "reset": "LR", "current_max": 1, "track": "uses",
            "note": "A named creature reduced to 0 HP (but not killed outright) drops to 1 HP "
                    "instead. Book of Shadows page holds up to your proficiency bonus in names.",
            "source_class": "", "subclass": "",
        })

    # DM-Granted Bonus Features (dm_rewards.py): these 4 have a real,
    # directly-stated flat 1-use resource in their source text.
    known_rewards_res = set(char.get("dm_rewards", []))
    DM_REWARD_FIXED_USES_RESOURCES = {
        "Mist Walker": ("Misty Step (Mist Walker)", 1, "LR",
            "Cast misty step without a spell slot, using your chosen INT/WIS/CHA as your "
            "spellcasting ability."),
        "Second Skin": ("Transformation (Alter Self)", 1, "LR",
            "Cast alter self (Change Appearance option only) without a spell slot, appearing "
            "in your second form, using your chosen INT/WIS/CHA as your spellcasting ability."),
        "Symbiotic Being": ("Sustained Symbiosis", 1, "LR",
            "When you fail a saving throw, expend one of your Hit Dice, roll it, and add the "
            "result to the save (potentially turning it into a success). On a death save, you "
            "automatically succeed and regain 1 HP, regardless of the roll."),
        "Watchers": ("Borrowed Eyes", 1, "LR",
            "Action: for 1 hour, gain advantage on Intelligence (Investigation) and Wisdom "
            "(Perception) checks, and you can't be blinded."),
        "Lifelong Companion": ("Companion's Protection", 1, "LR",
            "Reaction: when a creature within 5 ft. is hit by an attack roll, cause the attack "
            "to hit you instead."),
        "Nyxborn": ("Cloak of Stars", 1, "LR",
            "Action: wrap yourself in a starry cloak for 1 minute — attack rolls against you "
            "have disadvantage."),
        "Oracle": ("Oracle's Insight", 1, "SR/LR",
            "After rolling an ability check (before the DM says success/failure): roll a d10 "
            "and add it to the check."),
        "Gathered Whispers": ("Sudden Cacophony", 1, "LR",
            "Reaction when hit by an attack roll (if the attacker isn't deafened): add your "
            "proficiency bonus to your AC against that attack, potentially causing it to miss."),
        "Heroic Destiny": ("Hard to Kill", 1, "LR",
            "When reduced to 0 HP but not killed outright, you can drop to 1 HP instead."),
        "Pious": ("Pious Protection", 1, "LR",
            "If you fail a saving throw, you can reroll it and must use the new roll."),
        "Unscarred": ("Unscarred Resilience", 1, "SR/LR",
            "Reaction on taking damage: roll a d12, add your CON modifier, reduce the damage by "
            "that total."),
        "Hollow One": ("Unsettling Presence", 1, "LR",
            "Action: a creature you can see within 15 ft. has disadvantage on the next saving "
            "throw it makes within the next minute. Constructs, undead, and creatures that can't "
            "be frightened are immune."),
    }
    for rname, (label, uses, reset, note) in DM_REWARD_FIXED_USES_RESOURCES.items():
        if rname in known_rewards_res:
            new_resources.append({
                "name": label, "key": f"dmreward_{rname.lower().replace(' ','_')}",
                "reset": reset, "current_max": uses, "track": "uses",
                "note": note, "source_class": "", "subclass": "",
            })

    known_invocations = set(inv.split(" (")[0].strip() for inv in char.get("eldritch_invocations", []))
    # Eldritch Invocations: some modify an existing cantrip/spell's own
    # description text rather than appearing as a separately-named entry.
    INVOCATION_FIXED_USES_RESOURCES = {
        "Bewitching Whispers": ("Compulsion (Bewitching Whispers)", 1, "LR",
            "Cast compulsion using a warlock spell slot."),
        "Chains of Carceri": ("Hold Monster (Chains of Carceri)", 1, "LR",
            "Cast hold monster at will, targeting a celestial, fiend, or elemental, without a "
            "spell slot or material components. Once per long rest against the same creature."),
        "Ghostly Gaze": ("Ghostly Gaze", 1, "SR/LR",
            "Action: see through solid objects to 30 ft. (with darkvision if you lack it) for 1 "
            "minute or until your concentration ends."),
        "Minions of Chaos": ("Conjure Elemental (Minions of Chaos)", 1, "LR",
            "Cast conjure elemental using a warlock spell slot."),
        "Mire the Mind": ("Slow (Mire the Mind)", 1, "LR",
            "Cast slow using a warlock spell slot."),
        "Sculptor of Flesh": ("Polymorph (Sculptor of Flesh)", 1, "LR",
            "Cast polymorph using a warlock spell slot."),
        "Sign of Ill Omen": ("Bestow Curse (Sign of Ill Omen)", 1, "LR",
            "Cast bestow curse using a warlock spell slot."),
        "Tomb of Levistus": ("Tomb of Levistus", 1, "SR/LR",
            "Reaction on taking damage: entomb yourself in ice, gaining 10 temp HP per warlock "
            "level (absorbing as much of the triggering damage as possible). You then gain "
            "vulnerability to fire, speed 0, and incapacitated until the ice melts at the end of "
            "your next turn."),
        "Trickster's Escape": ("Freedom of Movement (Trickster's Escape)", 1, "LR",
            "Cast freedom of movement on yourself without expending a spell slot."),
        "Dreadful Word": ("Confusion (Dreadful Word)", 1, "LR",
            "Cast confusion using a warlock spell slot."),
        "Undying Servitude": ("Animate Dead (Undying Servitude)", 1, "LR",
            "Cast animate dead without using a spell slot."),
    }
    for iname, (label, uses, reset, note) in INVOCATION_FIXED_USES_RESOURCES.items():
        if iname in known_invocations:
            new_resources.append({
                "name": label, "key": f"invocation_{iname.lower().replace(' ','_').replace(chr(39),'')}",
                "reset": reset, "current_max": uses, "track": "uses",
                "note": note, "source_class": "", "subclass": "",
            })

    # Empty Body (Monk, 18th level).
    monk_lvl_eb = class_levels(char).get("Monk", 0)
    if monk_lvl_eb >= 18:
        new_resources.append({
            "name": "Empty Body", "key": "empty_body",
            "reset": "LR", "current_max": 1, "track": "uses",
            "note": "Action, 4 ki: become invisible for 1 min, resisting all damage except "
                    "force during that time. (Separately: 8 ki to cast Astral Projection "
                    "without material components.)",
            "source_class": "", "subclass": "",
        })

    # Favored Foe and Nature's Veil (Ranger, TCE optional features) each
    # replace a base feature (Favored Enemy / Hide in Plain Sight
    # respectively), so they're gated on the optional-feature toggle
    # being on, matching the dual-mechanism check used elsewhere for
    # optional features.
    def _tce_opt_on(name):
        enabled = char.get("_choices", {}).get("optional_features", {})
        if enabled.get(name, False):
            return True
        rules_key = name.lower().replace(" ", "_").replace("'", "")
        return char.get("optional_rules", {}).get(rules_key, False)

    ranger_lvl_opt = class_levels(char).get("Ranger", 0)
    pb_opt = get_prof_bonus(char)
    if ranger_lvl_opt >= 1 and _tce_opt_on("Favored Foe"):
        new_resources.append({
            "name": "Favored Foe", "key": "favored_foe",
            "reset": "LR", "current_max": max(1, pb_opt), "track": "uses",
            "note": "When you hit a creature, mark it as your favored enemy for 1 min or until "
                    "your concentration ends. First hit each turn against it deals +1d4 damage "
                    "(1d6 at 6th level, 1d8 at 14th level).",
            "source_class": "", "subclass": "",
        })
    if ranger_lvl_opt >= 10 and _tce_opt_on("Nature's Veil"):
        new_resources.append({
            "name": "Nature's Veil", "key": "natures_veil",
            "reset": "LR", "current_max": max(1, pb_opt), "track": "uses",
            "note": "Bonus action: become invisible, along with your equipment, until the "
                    "start of your next turn.",
            "source_class": "", "subclass": "",
        })
    # Tireless is Deft Explorer's 10th-level addition, not a separate feature.
    if ranger_lvl_opt >= 10 and _tce_opt_on("Deft Explorer"):
        new_resources.append({
            "name": "Tireless", "key": "tireless",
            "reset": "LR", "current_max": max(1, pb_opt), "track": "uses",
            "note": "Action: gain 1d8 + your WIS modifier in temporary hit points.",
            "source_class": "", "subclass": "",
        })

    # Dedicated Weapon (Monk, TCE optional): this app has no deeper
    # weapon-eligibility system to hook a mechanical outcome into (same
    # situation as Ki-Empowered Strikes), so this just tracks the choice
    # visibly rather than fabricate a mechanical connection.
    monk_lvl_dw = class_levels(char).get("Monk", 0)
    if monk_lvl_dw >= 2 and _tce_opt_on("Dedicated Weapon"):
        new_resources.append({
            "name": "Dedicated Weapon", "key": "dedicated_weapon",
            "reset": "SR", "current_max": 1, "track": "uses",
            "note": "When you finish a short or long rest, choose one weapon — it counts as "
                    "a monk weapon for you until your next rest, even if it wouldn't "
                    "otherwise qualify.",
            "source_class": "", "subclass": "",
        })

    # Living Shadow's Shadow Strike: proficiency-bonus-scaled, doesn't
    # fit the flat-1-use dict above.
    if "Living Shadow" in known_rewards_res:
        new_resources.append({
            "name": "Shadow Strike", "key": "dmreward_living_shadow_strike",
            "reset": "LR", "current_max": max(1, pb_res), "track": "uses",
            "note": "Melee attack: increase your reach for it by 10 ft., your shadow delivering "
                    "the attack as if it were you.",
            "source_class": "", "subclass": "",
        })

    # ── Feats needing MORE THAN ONE distinct resource (two separate
    # abilities, each with its own use count) — a single feat_name-keyed
    # dict can't represent this, so each entry here includes its own key
    # suffix to keep the two resources distinct within the same feat.
    FEAT_MULTI_RESOURCES = {
        "Gift of the Chromatic Dragon": [
            ("infusion", "Chromatic Infusion", 1, "LR",
             "Bonus action: infuse a touched weapon with acid/cold/fire/lightning/poison for 1 "
             "minute, adding 1d4 of that type on a hit."),
            ("reactive_resistance", "Reactive Resistance", max(1, pb_res), "LR",
             "Reaction when you take acid/cold/fire/lightning/poison damage: gain resistance to "
             "that instance."),
        ],
        "Gift of the Metallic Dragon": [
            ("draconic_healing", "Draconic Healing", 1, "LR",
             "Cast cure wounds without a spell slot."),
            ("protective_wings", "Protective Wings", max(1, pb_res), "LR",
             "Reaction when you or a creature within 5 ft. is hit: manifest spectral wings, "
             "granting +proficiency bonus to the target's AC against that attack."),
        ],
        "Adept of the Red Robes": [
            ("insightful_magic", "Insightful Magic", 1, "LR",
             "Cast your chosen 2nd-level illusion or transmutation spell without a spell slot."),
            ("magical_balance", "Magical Balance", max(1, pb_res), "LR",
             "When you roll 9 or lower on an attack roll or ability check, treat it as a 10."),
        ],
        "Adept of the Black Robes": [
            ("ambitious_magic", "Ambitious Magic", 1, "LR",
             "Cast your chosen 2nd-level enchantment or necromancy spell without a spell slot."),
        ],
        "Adept of the White Robes": [
            ("protective_magic", "Protective Magic", 1, "LR",
             "Cast your chosen 2nd-level abjuration or divination spell without a spell slot."),
        ],
        "Strixhaven Mascot": [
            ("teleport_swap", "Teleport Swap", 1, "LR",
             "Action: if your mascot familiar is within 60 ft., teleport to swap places with it."),
        ],
        "Wood Elf Magic": [
            ("longstrider", "Longstrider (Wood Elf Magic)", 1, "LR",
             "Cast longstrider without a spell slot."),
            ("pass_without_trace", "Pass Without Trace (Wood Elf Magic)", 1, "LR",
             "Cast pass without trace without a spell slot."),
        ],
        "Drow High Magic": [
            ("levitate", "Levitate (Drow High Magic)", 1, "LR",
             "Cast levitate without a spell slot."),
            ("dispel_magic", "Dispel Magic (Drow High Magic)", 1, "LR",
             "Cast dispel magic without a spell slot."),
        ],
        "Initiate of High Sorcery": [
            ("spell_1", "1st-Level Spell #1 (Initiate of High Sorcery)", 1, "LR",
             "Cast the first of your two chosen 1st-level spells without a spell slot."),
            ("spell_2", "1st-Level Spell #2 (Initiate of High Sorcery)", 1, "LR",
             "Cast the second of your two chosen 1st-level spells without a spell slot."),
        ],
        "Plantmender": [
            ("vision", "Plant Vision", max(1, 2 * ability_mod(char, "WIS")), "LR",
             "Action: touch a plant/tree to see visions of what happened to it and its vicinity "
             "in the last 24 hours, and learn its current health/blights."),
            ("barkskin_spike_growth", "Barkskin/Spike Growth (Plantmender)", 1, "LR",
             "Cast barkskin or spike growth once, using WIS as your spellcasting ability."),
        ],
    }
    for fname, entries in FEAT_MULTI_RESOURCES.items():
        if fname not in known_feats_res:
            continue
        base_key = fname.lower().replace(" ","_").replace("'","")
        for key_suffix, label, uses, reset, note in entries:
            new_resources.append({
                "name": label, "key": f"{base_key}_{key_suffix}",
                "reset": reset, "current_max": uses, "track": "uses",
                "note": note, "source_class": "", "subclass": "",
            })

    # Pact of the Talisman (Warlock): uses = proficiency bonus, per the actual rule text.
    pact_choice = char.get("_choices", {}).get("warlock_pact_boon", [])
    if pact_choice and "talisman" in pact_choice[0].lower():
        new_resources.append({
            "name": "Pact of the Talisman", "key": "pact_of_the_talisman",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "When the wearer fails an ability check, add a d4 to the roll "
                    "(potentially turning it into a success).",
            "source_class": "Warlock", "subclass": "",
        })

    # Firbolg Magic and Relentless Endurance are both concrete "once per rest" racial features.
    race_res = (char.get("species") or char.get("race", "")).lower()
    if race_res == "firbolg":
        # Firbolg Magic resets on a short OR long rest per the real rule.
        new_resources.append({
            "name": "Detect Magic (Firbolg Magic)", "key": "firbolg_detect_magic",
            "reset": "SR/LR", "current_max": 1, "track": "uses",
            "note": "Cast Detect Magic, using WIS as your spellcasting ability.",
            "source_class": "", "subclass": "",
        })
        new_resources.append({
            "name": "Disguise Self (Firbolg Magic)", "key": "firbolg_disguise_self",
            "reset": "SR/LR", "current_max": 1, "track": "uses",
            "note": "Cast Disguise Self, using WIS as your spellcasting ability.",
            "source_class": "", "subclass": "",
        })
        # Hidden Step: a concrete "once per short or long rest" ability, same pattern as Firbolg Magic above.
        new_resources.append({
            "name": "Hidden Step", "key": "firbolg_hidden_step",
            "reset": "SR/LR", "current_max": 1, "track": "uses",
            "note": "Bonus action: turn invisible until the start of your next turn, or until "
                    "you attack, deal damage, or force a saving throw.",
            "source_class": "", "subclass": "",
        })
    # Orc's Adrenaline Rush: a proficiency-bonus-scaled "times per long rest" ability.
    if race_res == "orc":
        new_resources.append({
            "name": "Adrenaline Rush", "key": "orc_adrenaline_rush",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "Bonus action: Dash, gaining temp HP equal to your proficiency bonus.",
            "source_class": "", "subclass": "",
        })
    if race_res in ("half-orc", "orc"):
        new_resources.append({
            "name": "Relentless Endurance", "key": "relentless_endurance",
            "reset": "LR", "current_max": 1, "track": "uses",
            "note": "When reduced to 0 HP but not killed outright, you can drop to 1 HP instead.",
            "source_class": "", "subclass": "",
        })

    # Harengon's Rabbit Hop: a proficiency-bonus-scaled, long-rest-only ability.
    if race_res == "harengon":
        new_resources.append({
            "name": "Rabbit Hop", "key": "harengon_rabbit_hop",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "Bonus action: jump a number of feet equal to 5 × your proficiency bonus, "
                    "without provoking opportunity attacks. Requires speed > 0.",
            "source_class": "", "subclass": "",
        })

    # Dhampir's Vampiric Bite and Reborn's Knowledge from a Past Life are
    # both proficiency-bonus-scaled, long-rest-only abilities.
    if race_res == "dhampir":
        new_resources.append({
            "name": "Vampiric Bite (empower)", "key": "dhampir_vampiric_bite",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "After hitting a non-Construct, non-Undead creature with your bite, either "
                    "regain HP equal to the piercing damage dealt, or gain a bonus to your next "
                    "ability check or attack roll equal to that damage.",
            "source_class": "", "subclass": "",
        })
    if race_res == "reborn":
        new_resources.append({
            "name": "Knowledge from a Past Life", "key": "reborn_past_life",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "After seeing the d20 result on an ability check using a skill, roll a d6 "
                    "and add it to the check.",
            "source_class": "", "subclass": "",
        })
    if race_res == "astral elf":
        new_resources.append({
            "name": "Starlight Step", "key": "astral_elf_starlight_step",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "Bonus action: teleport up to 30 ft to an unoccupied space you can see.",
            "source_class": "", "subclass": "",
        })
    if race_res == "autognome":
        new_resources.append({
            "name": "Built for Success", "key": "autognome_built_for_success",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "Add a d4 to one attack roll, ability check, or saving throw, after seeing "
                    "the d20 roll but before the effects resolve.",
            "source_class": "", "subclass": "",
        })
    if race_res == "giff":
        new_resources.append({
            "name": "Astral Spark (uses)", "key": "giff_astral_spark",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "Track uses of Astral Spark's extra force damage — limited to once per turn, "
                    "and to your proficiency bonus in uses per long rest. (The bonus damage itself "
                    "is already applied automatically on weapon hits; this tracks the limited-use cap.)",
            "source_class": "", "subclass": "",
        })
    if race_res == "kender":
        new_resources.append({
            "name": "Taunt", "key": "kender_taunt",
            "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
            "note": "Bonus action: one creature within 60 ft that can hear/understand you makes "
                    "a WIS save (DC 8 + PB + your chosen INT/WIS/CHA mod) or has disadvantage on "
                    "attack rolls against targets other than you until the start of your next turn.",
            "source_class": "", "subclass": "",
        })

    # Lunar Sorcery (Sorcerer).
    if "lunar" in subclasses(char).get("Sorcerer", "").lower():
        sorc_lvl = class_levels(char).get("Sorcerer", 0)
        if sorc_lvl >= 6:
            # Waxing and Waning: one free 1st-level spell from EACH
            # phase, each usable only while in that phase — modeled as
            # 3 separate resources since they're independently tracked.
            for phase in ("Full Moon", "New Moon", "Crescent Moon"):
                new_resources.append({
                    "name": f"Lunar Spell ({phase})", "key": f"lunar_spell_{phase.lower().replace(' ','_')}",
                    "reset": "LR", "current_max": 1, "track": "uses",
                    "note": f"Cast the {phase} 1st-level spell from the Lunar Spells table without "
                            f"expending a slot, while in the {phase} phase.",
                    "source_class": "Sorcerer", "subclass": "Lunar Sorcery",
                })
            new_resources.append({
                "name": "Lunar Boons (Metamagic discount)", "key": "lunar_boons",
                "reset": "LR", "current_max": get_prof_bonus(char), "track": "uses",
                "note": "Reduce Metamagic's sorcery point cost by 1 (min 0) on a spell of the "
                        "school matching your current phase (Full: Abjuration/Divination, "
                        "New: Enchantment/Necromancy, Crescent: Illusion/Transmutation).",
                "source_class": "Sorcerer", "subclass": "Lunar Sorcery",
            })
        elif sorc_lvl >= 1:
            new_resources.append({
                "name": "Lunar Spell (current phase)", "key": "lunar_spell_current",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Cast the 1st-level spell from the Lunar Spells table matching your "
                        "current phase, without expending a slot.",
                "source_class": "Sorcerer", "subclass": "Lunar Sorcery",
            })
        if sorc_lvl >= 18:
            new_resources.append({
                "name": "Lunar Phenomenon", "key": "lunar_phenomenon",
                "reset": "LR", "current_max": 1, "track": "uses",
                "note": "Bonus action: tap into your current phase's special power "
                        "(or as part of changing phase via Waxing and Waning). "
                        "5 sorcery points to use again after the first time.",
                "source_class": "Sorcerer", "subclass": "Lunar Sorcery",
            })

    merged = []
    for res in new_resources:
        key = res.get("key", "")
        if key in existing_resources:
            # Preserve current tracking value, update max
            existing = existing_resources[key]
            res["current"] = existing.get("current", res.get("current_max", 0))
        else:
            res["current"] = res.get("current_max", 0)
        merged.append(res)
    char["resources"] = merged

    return char


def all_skill_bonuses(char: dict) -> dict:
    return {skill: get_skill_bonus(char, skill) for skill in SKILL_ABILITY}


def all_saving_throw_bonuses(char: dict) -> dict:
    return {ab: get_saving_throw_bonus(char, ab) for ab in ["STR","DEX","CON","INT","WIS","CHA"]}


def combat_stats(char: dict) -> dict:
    """Return all combat-relevant derived stats as a dict."""
    return {
        "ac": get_ac(char),
        "initiative": get_initiative(char),
        "speed": char.get("speed", 30),
        "max_hp": char.get("max_hp", 0),
        "current_hp": char.get("current_hp", 0),
        "temp_hp": char.get("temp_hp", 0),
        "proficiency_bonus": get_prof_bonus(char),
        "spell_save_dc": get_spell_save_dc(char),
        "spell_attack_bonus": get_spell_attack_bonus(char),
        "passive_perception": get_passive_perception(char),
        "passive_investigation": get_passive_investigation(char),
        "passive_insight": get_passive_insight(char),
        "sneak_attack": get_sneak_attack(char),
        "martial_arts_die": get_martial_arts_die(char),
        "rage_damage": get_rage_damage(char),
        "extra_attacks": get_extra_attacks(class_levels(char), subclasses(char), char),
        "carry_capacity": get_carry_capacity_detail(char),
        "total_weight": get_total_weight(char),
    }
