"""
Action Abilities module.

Builds the Combat tab's Action/Bonus Action/Reaction/Passive cards for
a character: the KNOWN_ACTIONS reference catalog of class/subclass/
feat/race/magic-item abilities, plus build_action_abilities(), which
filters that catalog against a character's actual class levels,
subclass, known feats, race, and equipped/attuned items and returns
only the entries that genuinely apply. Extracted from ui/sheet.py so
combat action cards stay maintainable outside the CharacterSheet
monolith.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from __future__ import annotations

from collections import defaultdict

def sign(n): return f"+{n}" if n >= 0 else str(n)

def _classify_action(feature_text):
    """Return action economy bucket for a feature description string."""
    t = feature_text.lower()
    # Reaction
    if 'reaction' in t:
        return 'Reaction'
    # Free / object interaction
    if ('free action' in t or 'no action' in t or 'passively' in t
            or t.startswith('passive') or 'always on' in t
            or ('automatically' in t and 'no action' in t)):
        return 'Passive'
    # Bonus action keywords
    if ('bonus action' in t or '(ba)' in t or 'offhand' in t
            or 'as a bonus' in t):
        return 'Bonus Action'
    # Action keywords  
    if ('as an action' in t or '(action)' in t or 'use an action' in t
            or 'action to' in t or 'action:' in t):
        return 'Action'
    # Default: passive / always-on
    return 'Passive'


def _breath_weapon_desc(char: dict) -> str:
    """Concrete Breath Weapon text for THIS character: real damage dice for
    their level, real damage type/shape/save from their draconic ancestry,
    and the actual computed save DC — not the full level-progression table."""
    from dnd_app.core.calculator import get_prof_bonus, ability_mod, total_level
    anc = char.get("draconic_ancestry", "")
    dmg_type, shape, save_desc = "", "", ""
    try:
        from dnd_app.data.phb2014.races import DRACONIC_ANCESTRY
        data = DRACONIC_ANCESTRY.get(anc)
        if data:
            dmg_type, shape, save_desc = data
    except ImportError:
        pass
    save_ab = "DEX"
    for ab in ("STR","DEX","CON","INT","WIS","CHA"):
        if f"{ab} save" in save_desc:
            save_ab = ab
            break
    lvl = total_level(char)
    dice = "2d6" if lvl < 6 else "3d6" if lvl < 11 else "4d6" if lvl < 16 else "5d6"
    con_mod = ability_mod(char, "CON")
    pb = get_prof_bonus(char)
    dc = 8 + con_mod + pb
    dmg_type = dmg_type or "elemental"
    shape = shape or "15 ft cone"
    return (f"{shape}, {dice} {dmg_type.lower()} damage. "
            f"Targets must beat DC {dc} {save_ab} save or take full damage "
            f"(half on a successful save). Once per short or long rest.")


def _resolve_dynamic_combat_text(char: dict, text: str) -> str:
    """
    Replace generic rules-formula placeholders with the character's actual
    computed numbers, so combat-tab cards show what a player needs at the
    table ("DC 15 CON save", "+4 (STR)") instead of a formula they'd have
    to do math on mid-combat.
    """
    from dnd_app.core.calculator import get_prof_bonus, ability_mod, resolve_stat_placeholders
    import re
    pb = get_prof_bonus(char)
    ab_mods = {ab: ability_mod(char, ab) for ab in ("STR","DEX","CON","INT","WIS","CHA")}
    def _dc_sub(m):
        ab = m.group(1).upper()
        return f"DC {8 + ab_mods.get(ab,0) + pb}"
    text = re.sub(r"DC\s*8\s*\+\s*([A-Z]{3})\s*\+\s*prof(?:iciency)?",
                  _dc_sub, text, flags=re.IGNORECASE)
    # +STAT resolution is shared with the Features tab / level-up preview
    # so every surface formats it identically: "+ 4 (STR)" / "- 1 (STR)".
    text = resolve_stat_placeholders(text, char)
    text = re.sub(r"\bprof\b(?!iciency)", str(pb), text)
    return text


def _append_cantrip_scaling_note(sp_name: str, desc: str, char: dict) -> str:
    """Append a concrete 'Currently: ...' note showing the cantrip's ACTUAL
    damage for this character's level, rather than leaving the player to
    do the 5/11/17 math themselves mid-combat. Appends rather than
    rewrites the base description text — safer than regex-replacing a die
    notation inside free text, and the original rule text stays intact
    for reference."""
    from dnd_app.core.calculator import (
        get_cantrip_damage_display, get_eldritch_blast_beams,
        get_green_flame_blade_damage, CANTRIP_DAMAGE_SCALING, ability_mod,
        _detect_spell_ability,
    )
    if sp_name in CANTRIP_DAMAGE_SCALING:
        current = get_cantrip_damage_display(sp_name, char)
        return f"{desc}  Currently: {current}."
    if sp_name == "Eldritch Blast":
        beams = get_eldritch_blast_beams(char)
        word = "beam" if beams == 1 else "beams"
        has_agonizing = any("agonizing blast" in i.lower() for i in char.get("eldritch_invocations", []))
        # Repelling Blast: shown only when the character actually has
        # it, same pattern as Agonizing Blast above.
        has_repelling = any("repelling blast" in i.lower() for i in char.get("eldritch_invocations", []))
        repel_note = " Each beam that hits can push the target 10 ft. away (Repelling Blast)." if has_repelling else ""
        if has_agonizing:
            ability = _detect_spell_ability(char) or "CHA"
            mod = ability_mod(char, ability)
            dmg_str = f"1d10{sign(mod)} force each" if mod != 0 else "1d10 force each"
            return f"{desc}  Currently: {beams} {word} of {dmg_str} (Agonizing Blast).{repel_note}"
        return f"{desc}  Currently: {beams} {word} of 1d10 force each.{repel_note}"
    if sp_name == "Green-Flame Blade":
        ability = _detect_spell_ability(char) or "CHA"
        mod = ability_mod(char, ability)
        primary, secondary = get_green_flame_blade_damage(char, mod)
        bonus_note = f" +{primary} to the target hit," if primary else ""
        return f"{desc}  Currently:{bonus_note} {secondary} to the second creature."
    return desc


def _feature_matches_char_subclass(cls_name: str, feat_fragment: str, char_subclass: str) -> bool:
    """
    True if feat_fragment should be shown for this character.

    KNOWN_ACTIONS entries are keyed only by (class, feature name) — with
    no subclass in the key at all — so without this check, every
    subclass's reminders leak to every character of that class
    regardless of their actual subclass (confirmed directly: a Life
    Domain Cleric was seeing Solidarity Domain's "Solidarity's Action"
    and Ambition Domain's "Warding Flare").

    Cross-references CLASS_FEATURE_INDEX, which IS subclass-specific,
    to find which subclass(es) actually grant this feature name. If the
    name doesn't appear under any subclass for this class at all, it's
    presumably a Core (class-wide) feature or one not yet catalogued
    there, so it's allowed through unfiltered rather than being hidden
    by a false negative.
    """
    from dnd_app.data.phbCommon.class_features import CLASS_FEATURE_INDEX
    def _norm(s):
        return s.replace("'", "").replace("’", "")
    feat_norm = _norm(feat_fragment)
    class_subs = CLASS_FEATURE_INDEX.get(cls_name, {})
    granting_subclasses = []
    for sub_name, level_map in class_subs.items():
        if sub_name == "Core":
            continue
        all_names = []
        if isinstance(level_map, dict):
            for names in level_map.values():
                all_names.extend(names)
        else:
            all_names = level_map
        if any(_norm(n) == feat_norm for n in all_names):
            granting_subclasses.append(sub_name)
    if not granting_subclasses:
        # Not catalogued as any subclass's feature — treat as Core/universal.
        return True
    return char_subclass in granting_subclasses


def _get_artificer_infusion_base_names():
    """Base names (stripped of the " \xe2\x80\x93 description" suffix) of
    every real Artificer infusion. Used to gate Combat-page infusion
    reminders on the character actually knowing that specific infusion,
    not just being an Artificer of a high enough level."""
    from dnd_app.data.phb2014.classes import ARTIFICER_INFUSIONS
    return {inf.split(" \u2013 ")[0].strip() for inf in ARTIFICER_INFUSIONS}


_ARTIFICER_INFUSION_BASE_NAMES = _get_artificer_infusion_base_names()


def _optional_feature_enabled(char, feature_name):
    """Checks both real enable mechanisms this app uses for an optional
    feature (a per-feature toggle, or the broader optional_rules
    toggle), matching the same dual-check already used for display in
    sheet.py."""
    enabled = char.get("_choices", {}).get("optional_features", {})
    if enabled.get(feature_name, False):
        return True
    rules_key = feature_name.lower().replace(" ", "_").replace("'", "")
    return char.get("optional_rules", {}).get(rules_key, False)


def build_action_abilities(char):
    """
    Return {bucket: [(name, desc, source), ...]} for the action economy display.
    Buckets: 'Action', 'Bonus Action', 'Reaction', 'Passive'
    """
    from collections import defaultdict
    buckets = defaultdict(list)

    # Hard-coded well-known class abilities per action type
    KNOWN_ACTIONS = {
        # (class, feature_name_fragment): (bucket, display_name, short_desc)
        ('Fighter','Second Wind'):     ('Bonus Action','Second Wind','Heal 1d10 + Fighter level HP. 1/SR.'),
        ('Fighter','Fighting Style'): ('Passive', 'Fighting Style (passive)',
            "Your chosen fighting style's benefit (Archery, Defense, Dueling, Great Weapon Fighting, "
            "Protection, Two-Weapon Fighting, etc. — see your specific choice)."),
        ('Fighter','Extra Attack'): ('Passive', 'Extra Attack (passive)',
            "Attack twice, instead of once, whenever you take the Attack action on your turn "
            "(three times at 11th level, four at 20th)."),
        ('Fighter','Survivor (Champion)'): ('Passive', 'Survivor (passive)',
            "Regain HP equal to 5 + CON modifier at the start of each of your turns, if you have no "
            "more than half your HP left (and aren't at 0)."),
        ('Fighter','Combat Superiority'): ('Passive', 'Combat Superiority (passive)',
            "4 Superiority Dice (d8s), regained on a short or long rest. Know 3 maneuvers (2 more "
            "at 7th/10th/15th), each expending one die when used. Maneuver save DC = 8 + STR or "
            "DEX modifier (your choice) + proficiency bonus. See your chosen maneuvers for their "
            "individual effects."),
        ('Fighter','Student of War'): ('Passive', 'Student of War (passive)',
            "Proficiency with one type of artisan's tools of your choice."),
        ('Fighter','Know Your Enemy'): ('Action', 'Know Your Enemy',
            "Spend 1 minute observing or interacting with a creature outside combat to learn how it "
            "compares to you in two chosen categories (Strong/Weak, Fast/Slow, etc.)."),
        ('Fighter','Improved Combat Superiority'): ('Passive', 'Improved Combat Superiority (passive)',
            "Your Superiority Dice upgrade to d10s."),
        ('Fighter','Improved Combat Superiority (18th)'): ('Passive', 'Improved Combat Superiority (18th) (passive)',
            "Your Superiority Dice upgrade further, to d12s."),
        ('Fighter','Relentless'): ('Passive', 'Relentless (passive)',
            "If you have no Superiority Dice remaining when you roll initiative, you regain one."),
        ('Fighter','Weapon Bond'): ('Action', 'Weapon Bond',
            "Perform a 1-hour ritual to magically bond with a weapon — you can't be disarmed of it "
            "unless incapacitated, and can summon it to your hand as a bonus action if it's on the "
            "same plane. Bond with up to two weapons at a time."),
        ('Fighter','War Magic'): ('Bonus Action', 'War Magic',
            "When you take the Attack action, you can replace one of its attacks with casting a "
            "cantrip."),
        ('Fighter','Eldritch Strike'): ('Passive', 'Eldritch Strike (passive)',
            "When you hit a creature with a weapon attack, it has disadvantage on its next save "
            "against a spell you cast before the end of your next turn."),
        ('Fighter','Arcane Charge'): ('Passive', 'Arcane Charge (passive)',
            "When you use Action Surge, you can teleport up to 30 ft. to an unoccupied space you can "
            "see, before or after the extra action."),
        ('Fighter','Improved War Magic'): ('Passive', 'Improved War Magic (passive)',
            "Replace one of your Attack action's attacks with any spell you cast with a casting time "
            "of 1 action, not just a cantrip."),
        ('Fighter','Arcane Archer Lore'): ('Passive', 'Arcane Archer Lore (passive)',
            "Proficiency in Arcana or Nature (your choice), and learn the Prestidigitation or "
            "Druidcraft cantrip (your choice)."),
        ('Fighter','Arcane Shot'): ('Action', 'Arcane Shot',
            "Once per turn, when you fire an arrow from a shortbow or longbow as part of the Attack "
            "action, apply one of your known Arcane Shot options to it. 2 uses, regained on a short "
            "or long rest."),
        ('Fighter','Magic Arrow'): ('Passive', 'Magic Arrow (passive)',
            "Whenever you fire a nonmagical arrow from a shortbow or longbow, you can make it "
            "magical for the purpose of overcoming resistance/immunity — the magic fades immediately "
            "after it hits or misses."),
        ('Fighter','Curving Shot'): ('Bonus Action', 'Curving Shot',
            "When you make an attack roll with a magic arrow and miss, reroll the attack roll "
            "against a different target within 60 ft. of the original target."),
        ('Fighter','Arcane Shot (10th)'): ('Passive', 'Arcane Shot (10th) (passive)',
            "Gain 1 additional Arcane Shot option of your choice."),
        ('Fighter','Ever-Ready Shot'): ('Passive', 'Ever-Ready Shot (passive)',
            "If you have no uses of Arcane Shot left when you roll initiative, you regain one use."),
        ('Fighter','Arcane Shot (18th)'): ('Passive', 'Arcane Shot (18th) (passive)',
            "Gain 1 additional Arcane Shot option of your choice."),
        ('Fighter','Rallying Cry'): ('Passive', 'Rallying Cry (passive)',
            "When you use Second Wind, up to 3 allies within 60 ft. who can see or hear you each "
            "regain HP equal to your Fighter level."),
        ('Fighter','Unwavering Mark'): ('Action', 'Unwavering Mark',
            "When you hit with a melee weapon attack, mark the creature until the end of your next "
            "turn — while within 5 ft. of you, it has disadvantage on attacks that don't target you. "
            "If it damages someone else, bonus action on your next turn: special attack against it "
            "with advantage, +half your Fighter level damage on a hit. Uses = STR mod (min 1) per "
            "long rest."),
        ('Fighter','Bonus Proficiency (Cavalier)'): ('Passive', 'Bonus Proficiency (passive)',
            "Proficiency in one of Animal Handling, History, Insight, Performance, or Persuasion."),
        ('Fighter','Born to the Saddle'): ('Passive', 'Born to the Saddle (passive)',
            "Advantage on saves against being dismounted; if you fall off your mount and descend no "
            "more than 10 ft., you take no falling damage and land on your feet; mounting/dismounting "
            "costs only 5 ft. of movement instead of half your speed."),
        ('Fighter','Warding Maneuver'): ('Reaction', 'Warding Maneuver',
            "When you or a creature within 5 ft. is hit by an attack (while you wield a melee weapon "
            "or shield): roll 1d8, add it to the target's AC against that attack; if it still hits, "
            "the target has resistance to the damage. Uses = CON modifier (min 1) per long rest."),
        ('Fighter','Hold the Line'): ('Passive', 'Hold the Line (passive)',
            "Creatures provoke an opportunity attack from you when they move 5 ft. or more while "
            "within your reach. If you hit with that opportunity attack, the target's speed is "
            "reduced to 0 until the end of the current turn."),
        ('Fighter','Ferocious Charger'): ('Passive', 'Ferocious Charger (passive)',
            "Once per turn: if you move at least 10 ft. in a straight line right before hitting a "
            "creature with an attack, it must succeed on a STR save (DC 8 + prof + STR) or be "
            "knocked prone."),
        ('Fighter','Vigilant Defender'): ('Passive', 'Vigilant Defender (passive)',
            "You get a special reaction usable once on every creature's turn except your own, only "
            "to make an opportunity attack — separate from your normal reaction."),
        ('Fighter','Psionic Power'): ('Passive', 'Psionic Power (passive)',
            "Psionic Energy dice (d6s, scaling to d8/d10/d12 at 5th/11th/17th) — you have twice your "
            "proficiency bonus of them, regained on a long rest (or regain one as a bonus action, "
            "1/short or long rest). Protective Field "
            "(reaction: reduce damage to you or a creature within 30 ft. by the die roll + INT mod), "
            "Psionic Strike (once per turn: extra force damage on a weapon hit equal to the die roll "
            "+ INT mod), and Telekinetic Movement (move an object or willing creature with your mind) "
            "all expend one die."),
        ('Fighter','Telekinetic Adept'): ('Bonus Action', 'Telekinetic Adept',
            "Psi-Powered Leap: gain a flying speed equal to double your walking speed until the end "
            "of the turn (1/short or long rest, or expend a Psionic Energy die). Telekinetic Thrust: "
            "when you deal Psionic Strike damage, force a STR save (DC 8 + prof + INT); on a fail, "
            "push the target 10 ft. or knock it prone."),
        ('Fighter','Guarded Mind'): ('Passive', 'Guarded Mind (passive)',
            "Resistance to psychic damage. If you start your turn charmed or frightened, you can "
            "expend a Psionic Energy die to end those effects on yourself."),
        ('Fighter','Bulwark of Force'): ('Bonus Action', 'Bulwark of Force',
            "Grant half cover to yourself and chosen creatures within 30 ft. (up to your INT "
            "modifier, min 1) for 1 minute. 1/long rest, or expend a Psionic Energy die to use again."),
        ('Fighter','Telekinetic Master'): ('Action', 'Telekinetic Master',
            "Cast Telekinesis without a spell slot, and make one weapon attack as a bonus action when "
            "you do. 1/long rest, or expend a Psionic Energy die to use again."),
        ('Fighter','Bonus Proficiency (Rune Knight)'): ('Passive', 'Bonus Proficiency (passive)',
            "Proficiency with smith's tools. Learn to speak, read, and write Giant."),
        ('Fighter','Rune Carver'): ('Passive', 'Rune Carver (passive)',
            "Learn 2 Giant runes to carve into your armor/weapon/shield (more at higher levels). See "
            "your specific chosen runes for their individual effects."),
        ('Fighter','Runic Shield'): ('Reaction', 'Runic Shield',
            "When another creature you can see within 60 ft. is hit by an attack roll, force the "
            "attacker to reroll and use the new result. Uses = proficiency bonus per long rest."),
        ('Fighter','Great Stature'): ('Passive', 'Great Stature (passive)',
            "Grow permanently taller (roll 3d4 inches). Giant's Might's extra damage increases to 1d8."),
        ('Fighter','Runic Juggernaut'): ('Passive', 'Runic Juggernaut (passive)',
            "Giant's Might's extra damage increases to 1d10. While using Giant's Might, you can grow "
            "to Huge size instead of Large, and your reach increases by 5 ft. while that size."),
        ('Fighter','Bonus Proficiency (Samurai)'): ('Passive', 'Bonus Proficiency (passive)',
            "Proficiency in one of History, Insight, Performance, or Persuasion. Alternatively, "
            "learn one language of your choice."),
        ('Fighter','Fighting Spirit'): ('Bonus Action', 'Fighting Spirit',
            "Gain advantage on weapon attack rolls until the end of the turn, and gain temp HP "
            "(5 at 3rd level, 10 at 10th, 15 at 15th). 3 uses per long rest."),
        ('Fighter','Tireless Spirit'): ('Passive', 'Tireless Spirit (passive)',
            "If you have no uses of Fighting Spirit left when you roll initiative, you regain one use."),
        ('Fighter','Rapid Strike'): ('Passive', 'Rapid Strike (passive)',
            "Once per turn: if you take the Attack action and have advantage on an attack roll "
            "against a target, you can forgo the advantage to make an additional weapon attack "
            "against that target as part of the same action."),
        ('Fighter','Strength before Death'): ('Reaction', 'Strength before Death',
            "If damage reduces you to 0 HP without killing you outright, delay falling unconscious "
            "and immediately take an extra turn (interrupting the current one). Death saves still "
            "apply as normal if you take damage during it; you fall unconscious at its end if still "
            "at 0 HP."),
        ('Fighter','Action Surge'):    ('Action',      'Action Surge','Take one additional action this turn. 1/SR (2/SR at 17).'),
        ('Fighter','Indomitable'):     ('Reaction',    'Indomitable','Reroll a failed saving throw. Keep new result. 1/LR.'),
        ('Barbarian','Rage'):          ('Bonus Action','Rage','Enter rage: resist bludg/slash/pierce, +damage, adv STR checks. 1/LR (more at higher levels).'),
        ('Barbarian','Unarmored Defense'): ('Passive', 'Unarmored Defense (passive)',
            "AC = 10 + DEX mod + CON mod when wearing no armor (a shield is still fine)."),
        ('Barbarian','Danger Sense'): ('Passive', 'Danger Sense (passive)',
            "Advantage on DEX saves against effects you can see (traps, spells), unless blinded, "
            "deafened, or incapacitated."),
        ('Barbarian','Extra Attack'): ('Passive', 'Extra Attack (passive)',
            "Attack twice, instead of once, whenever you take the Attack action on your turn."),
        ('Barbarian','Fast Movement'): ('Passive', 'Fast Movement (passive)',
            "+10 ft. walking speed while not wearing heavy armor."),
        ('Barbarian','Feral Instinct'): ('Passive', 'Feral Instinct (passive)',
            "Advantage on initiative rolls. If surprised but able to act (because you enter your rage "
            "before acting), you're no longer considered surprised."),
        ('Barbarian','Instinctive Pounce'): ('Passive', 'Instinctive Pounce (passive)',
            "As part of the bonus action you take to enter your rage, you can move up to half your speed."),
        ('Barbarian','Brutal Critical'): ('Passive', 'Brutal Critical (passive)',
            "Roll one additional weapon damage die (2 extra at 13th, 3 at 17th) when determining the "
            "extra damage for a critical hit with a melee attack."),
        ('Barbarian','Persistent Rage'): ('Passive', 'Persistent Rage (passive)',
            "Your rage only ends early if you fall unconscious or choose to end it yourself — it no "
            "longer ends just because you go a turn without attacking or taking damage."),
        ('Barbarian','Indomitable Might'): ('Passive', 'Indomitable Might (passive)',
            "If your total for a Strength check is less than your Strength score, use that score in "
            "place of the total."),
        ('Barbarian','Primal Champion'): ('Passive', 'Primal Champion (passive)',
            "STR and CON scores each increase by 4 (to a maximum of 24)."),
        ('Barbarian','Retaliation'):   ('Reaction',     'Retaliation','When a creature within 5 ft damages you, make a melee weapon attack against it.'),
        ('Barbarian','Relentless Rage'): ('Passive', 'Relentless Rage (passive)',
            "If you drop to 0 HP while raging and aren't killed outright, DC 10 CON save to drop to 1 HP "
            "instead. DC increases by 5 each time you use this again before your next short or long rest, "
            "then resets."),
        ('Barbarian','Ancestral Protectors'): ('Passive', 'Ancestral Protectors (passive)',
            "While raging: the first creature you hit with an attack on your turn is marked by spectral "
            "warriors until the start of your next turn — it has disadvantage on any attack roll that "
            "isn't against you, and if it hits a creature other than you, that creature has resistance "
            "to the damage dealt by the attack."),
        ('Barbarian','Consult the Spirits'): ('Passive', 'Consult the Spirits (1/SR or LR)',
            "Cast Augury or Clairvoyance (using WIS, no slot or components) — Clairvoyance's sensor is "
            "invisibly one of your ancestral spirits instead of a floating orb. Once per short or long rest."),
        ('Barbarian','Spirit Shield'): ('Reaction',     'Spirit Shield','While raging, reduce damage taken by an ally within 30 ft by 2d6 (scales at 10th/14th).'),
        ('Barbarian','Battlerager Charge'): ('Bonus Action', 'Battlerager Charge', 'While raging, Dash as a bonus action.'),
        ('Barbarian','Spiked Retribution'): ('Passive', 'Spiked Retribution (passive)', "While raging in battlerager armor, a creature within 5 ft that hits you with a melee attack takes 3 piercing damage from the spikes."),
        ('Barbarian','Intimidating Presence'): ('Action', 'Intimidating Presence', 'Frighten a creature within 30 ft (WIS save DC 8+prof+CHA, repeats each round it can see you).'),
        ('Barbarian','Reckless Attack'):('Action',     'Reckless Attack','On first attack each turn: adv on attack, enemies have adv against you until next turn.'),
        ('Barbarian','Frenzy'):        ('Passive',     'Frenzied Attack (Frenzy)','Make one extra melee attack as bonus action while frenzied. Gain exhaustion after rage.'),
        ('Barbarian','Infectious Fury'): ('Passive', 'Infectious Fury (passive)', "When you damage a creature with Form of the Beast, force a WIS save (DC 8+prof+CON) or deal 2d12 psychic damage, or force it to attack a creature of your choice. Uses = proficiency bonus per long rest."),
        ('Barbarian','Call the Hunt'): ('Bonus Action', 'Call the Hunt', "When you enter your rage, choose willing creatures within 30 ft equal to your CON modifier (min 1) — you gain 5 temp HP for each that accepts. Until your rage ends, each of them can once per turn add a d6 to their damage on a hit. Uses = proficiency bonus per long rest."),
        ('Barbarian',"Giant's Power"): ('Passive', "Giant's Power (passive)", "Learn Giant (or another language if you already know Giant), plus Druidcraft or Thaumaturgy (WIS-based)."),
        ('Barbarian',"Giant's Havoc"): ('Passive', "Giant's Havoc (passive)", "While raging, both benefits apply: add Rage Damage to a thrown STR weapon attack (Crushing Throw), and gain +5 ft reach and become Large if smaller (Giant Stature)."),
        ('Barbarian','Mindless Rage'): ('Passive', 'Mindless Rage (passive)', "While raging, you can't be charmed or frightened. If already charmed/frightened when you rage, the effect is suspended for the rage's duration."),
        ('Barbarian','Demiurgic Colossus'): ('Passive', 'Demiurgic Colossus (passive)', "While raging: reach +10 ft, grow to Large or Huge (your choice), Mighty Impel can target Large or smaller creatures, and Elemental Cleaver's bonus damage becomes 2d6."),
        ('Barbarian','Elemental Cleaver'): ('Bonus Action', 'Elemental Cleaver', "While raging, infuse a held weapon with an element: changes its damage type, adds +1d6 (2d6 at 14th) of that type, gains thrown 20/60 ft and returns to your hand."),
        ('Barbarian','Mighty Impel'): ('Bonus Action', 'Mighty Impel', "While raging, move a Medium or smaller creature within reach to an unoccupied space within 30 ft (STR save if unwilling)."),
        ('Barbarian','Storm Aura'): ('Bonus Action', 'Storm Aura', "10-ft aura while raging, activates on entering rage and again each turn as a bonus action — Desert: all other creatures in the aura take fire damage; Sea: one chosen creature makes a DEX save or takes lightning damage (half on success); Tundra: creatures of your choice in the aura gain temp HP. Damage/HP amount scales with level (2 at 3rd, 3 at 5th, 4 at 10th, 5 at 15th, 6 at 20th for Desert/Tundra; 1d6→4d6 for Sea)."),
        ('Barbarian','Shielding Storm'): ('Passive', 'Shielding Storm (passive)', "While raging, allies within your Storm Aura also gain your Storm Soul's benefits."),
        ('Barbarian','Raging Storm'): ('Reaction', 'Raging Storm', "Desert: after a creature in your aura hits you, force a DEX save or it takes fire damage = half your Barbarian level. Sea: after you hit a creature in your aura, force a STR save or knock it prone. Tundra: whenever Storm Aura activates, choose a creature in the aura — STR save or its speed is 0 until the start of your next turn."),
        ('Barbarian','Magic Awareness'): ('Action', 'Magic Awareness', "Sense the location of spells and magic items within 60 ft (through walls) for 1 minute."),
        ('Barbarian','Wild Surge'): ('Passive', 'Wild Surge (passive)', "When you enter your rage, roll on the Wild Magic table to determine the magical effect produced."),
        ('Barbarian','Bolstering Magic'): ('Bonus Action', 'Bolstering Magic', "Roll a d3: give a creature that many extra dice for its next attack/save/check, or grant a spellcaster a spell slot of that level."),
        ('Barbarian','Unstable Backlash'): ('Reaction', 'Unstable Backlash', "Immediately after you take damage or fail a saving throw while raging, roll on the Wild Magic table and immediately produce that effect, replacing your current Wild Magic effect."),
        ('Barbarian','Controlled Surge'): ('Passive', 'Controlled Surge (passive)', "When you roll on the Wild Magic table, roll twice and choose either result."),
        ('Barbarian','Battlerager Armor'): ('Bonus Action', 'Battlerager Armor',
            "While raging and wearing spiked barbarian armor you're proficient with: deal 1d4 piercing "
            "damage to a creature that grapples you, or that you grapple, hit, or pin."),
        ('Barbarian','Reckless Abandon'): ('Passive', 'Reckless Abandon (passive)',
            "When you make a Reckless Attack while raging, gain temp HP equal to your CON modifier "
            "(minimum 1)."),
        ('Barbarian','Form of the Beast'): ('Passive', 'Form of the Beast (passive)',
            "While raging: grow a natural weapon of your choice — Bite (1d8 piercing; regain HP = "
            "proficiency bonus once per turn on a hit, if below half HP), Claws (1d6 slashing; one "
            "additional claw attack as part of the same Attack action), or Tail (1d8 piercing, has "
            "the reach property; reaction when hit by an attack roll from within 10 ft.: roll a d8 "
            "and add it to your AC against that attack)."),
        ('Barbarian','Bestial Soul'): ('Passive', 'Bestial Soul (passive)',
            "Your Form of the Beast natural weapons count as magical for overcoming resistance/"
            "immunity to nonmagical attacks. When you finish a short or long rest, choose one until "
            "your next rest: swimming speed = walking speed + breathe underwater; climbing speed = "
            "walking speed + no check needed to climb difficult surfaces (even upside down); or "
            "extend your jump distance by the total of a STR (Athletics) check, once per turn."),
        ('Barbarian','Spirit Seeker'): ('Action', 'Spirit Seeker (ritual)',
            "Cast Beast Sense or Speak with Animals as a ritual, communing with nature to understand "
            "the land around you."),
        ('Barbarian','Totem Spirit'): ('Passive', 'Totem Spirit (passive)',
            "Chosen totem animal's benefit while raging (Bear/Eagle/Elk/Wolf, etc. — see your specific "
            "choice for the exact effect)."),
        ('Barbarian','Aspect of the Beast'): ('Passive', 'Aspect of the Beast (passive)',
            "A second, always-on totem animal benefit (not limited to while raging) — see your "
            "specific choice for the exact effect."),
        ('Barbarian','Spirit Walker'): ('Action', 'Spirit Walker (ritual)',
            "Cast Commune with Nature as a ritual, using a totemic incarnation of the spirit of nature "
            "instead of your own consciousness to explore the environment."),
        ('Barbarian','Totemic Attunement'): ('Passive', 'Totemic Attunement (passive)',
            "A third, more powerful totem animal benefit while raging — see your specific choice for "
            "the exact effect."),
        ('Barbarian','Storm Soul'): ('Passive', 'Storm Soul (passive)',
            "Benefits even when your Storm Aura isn't active, based on your chosen environment — "
            "Desert: fire resistance, no extreme heat effects, action to ignite a flammable object; "
            "Sea: lightning resistance, breathe underwater, 30 ft. swim speed; Tundra: cold "
            "resistance, no extreme cold effects, action to freeze a 5-ft. cube of water."),
        ('Barbarian','Divine Fury'): ('Passive', 'Divine Fury (passive)',
            "While raging: the first creature you hit on each of your turns takes extra damage equal "
            "to 1d6 + half your Barbarian level (your choice of necrotic or radiant, fixed once chosen)."),
        ('Barbarian','Warrior of the Gods'): ('Passive', 'Warrior of the Gods (passive)',
            "Any spell that would restore you to life (but not undeath) requires no material "
            "components when cast on you."),
        ('Barbarian','Rage Beyond Death'): ('Passive', 'Rage Beyond Death (passive)',
            "While raging, having 0 HP doesn't knock you unconscious — you keep fighting, still make "
            "death saving throws normally, and suffer the normal effects of being at 0 HP. If you'd "
            "die from failing death saves, death is delayed until your rage ends, and only happens "
            "then if you still have 0 HP."),
        ('Artificer','The Right Tool for the Job'): ('Action', 'The Right Tool for the Job',
            "With thieves' or artisan's tools in hand: spend 1 hour of uninterrupted work (can "
            "overlap a short/long rest) to magically create one set of artisan's tools in an "
            "unoccupied space within 5 ft. Nonmagical; vanishes when you use this again."),
        ('Artificer','Tool Expertise'): ('Passive', 'Tool Expertise (passive)',
            "Your proficiency bonus is doubled for any ability check using a tool you're proficient with."),
        ('Artificer','Alchemical Savant'): ('Passive', 'Alchemical Savant (passive)',
            "When you cast a spell using your alchemist's supplies as a focus: add your INT "
            "modifier (min +1) to one roll of the spell that restores HP or deals acid, fire, "
            "necrotic, or poison damage."),
        ('Artificer','Extra Attack'): ('Passive', 'Extra Attack (passive)',
            "Attack twice, instead of once, whenever you take the Attack action on your turn."),
        ('Artificer','Steel Defender'): ('Bonus Action', 'Steel Defender',
            "Command your steel defender to take an action of your choice (otherwise it just "
            "Dodges on its turn, right after yours). Mending restores 2d6 HP to it; if it died "
            "within the last hour, revive it (smith's tools, action, within 5 ft, spend a spell "
            "slot) — returns after 1 minute at full HP. Create a new one at the end of a long "
            "rest (the old one perishes if you already have one)."),
        ('Artificer','Arcane Firearm'): ('Passive', 'Arcane Firearm (passive)', "Spells cast through your wand/staff/rod focus add 1d8 to one damage roll."),
        ('Artificer','Fortified Position'): ('Passive', 'Fortified Position (passive)', "You and allies within 10 ft of your cannon have half cover. You can maintain two cannons at once."),
        ('Artificer','Improved Defender'): ('Passive', 'Improved Defender (passive)',
            "Arcane Jolt's extra damage/healing increases to 4d6. Your Steel Defender gains +2 AC."),
        ('Artificer','Explosive Cannon'): ('Action', 'Explosive Cannon', "Your Eldritch Cannon deals +1d8 damage and can explode on destruction: 3d8 force in a 20-ft sphere, DEX save for half."),
        ('Artificer','Flash of Genius'): ('Reaction', 'Flash of Genius',
            "When you or a creature within 30 ft makes an ability check or saving throw, add your "
            "INT modifier to the roll."),
        ('Artificer','Arcane Jolt'): ('Passive', 'Arcane Jolt (passive)',
            "When you hit with a magic weapon attack, or your Steel Defender hits: extra 2d6 "
            "(4d6 at 15th) force damage, or restore that much HP to a creature/object within 30 "
            "ft. Max once per turn."),
        ('Artificer','Restorative Reagents'): ('Passive', 'Restorative Reagents (passive)',
            "Creatures who drink your Experimental Elixirs also gain 2d6+INT mod (min 1) temp HP. "
            "Cast Lesser Restoration at will (using alchemist's supplies, no slot/preparation). "
            "Uses = INT mod (min 1) per long rest."),
        ('Artificer','Armor Modifications'): ('Passive', 'Armor Modifications (passive)',
            "Your Arcane Armor's chest piece, boots, helmet, and special weapon each count as "
            "separate items for Infuse Item, transferring if you switch Armor Model. Max infused "
            "items increases by 2, restricted to Arcane Armor parts."),
        ('Artificer','Magic Item Adept'): ('Passive', 'Magic Item Adept (passive)',
            "Attune to up to 4 magic items at once. Crafting a common/uncommon magic item costs "
            "a quarter the time and half the gold."),
        ('Artificer','Spell-Storing Item'): ('Action', 'Spell-Storing Item',
            "At the end of a long rest, store a 1st or 2nd level artificer spell (1 action to "
            "cast, no need to have it prepared) into a weapon or spellcasting focus you touch. "
            "Anyone holding it can use it that many times (2× your INT mod, min 2) using your "
            "spellcasting ability."),
        ('Artificer','Magic Item Savant'): ('Passive', 'Magic Item Savant (passive)',
            "Attune to up to 5 magic items at once. Ignore all class, race, spell, and level "
            "requirements on attuning to or using a magic item."),
        ('Artificer','Magic Item Master'): ('Passive', 'Magic Item Master (passive)',
            "Attune to up to 6 magic items at once."),
        ('Artificer','Chemical Mastery'): ('Passive', 'Chemical Mastery (passive)',
            "Resistance to acid and poison damage; immune to the poisoned condition. Cast Greater "
            "Restoration and Heal at will (using alchemist's supplies, no slot/preparation/"
            "material components) — once each until you finish a long rest."),
        ('Artificer','Battle Ready'): ('Passive', 'Battle Ready (passive)', "Proficiency with martial weapons. Use INT instead of STR/DEX for attack and damage rolls with magic weapons."),
        ('Artificer','Homunculus Servant'): ('Bonus Action', 'Homunculus Servant',
            "Infuse a gem/crystal (100+ gp) into a Tiny construct companion. HP = 1 + INT mod "
            "+ Artificer level (d4 hit dice); Evasion (no damage on a successful DEX save "
            "instead of half). Force Strike: ranged attack, your spell attack modifier to "
            "hit, 30 ft, 1d4+PB force damage on a hit. Shares your initiative, acts right "
            "after you. Bonus action to command it to act; otherwise it just Dodges. If "
            "incapacitated, it can act freely. Regains 2d6 HP from Mending."),
        ('Artificer',"Boots of the Winding Path"): ('Bonus Action', "Boots of the Winding Path",
            "Teleport up to 15 ft to an unoccupied space you occupied earlier this turn."),
        ('Artificer','Resistant Armor'): ('Passive', 'Resistant Armor (passive)',
            "While worn: resistance to one damage type of your choice (acid, cold, fire, force, "
            "lightning, necrotic, poison, psychic, radiant, or thunder), chosen when infused."),
        ('Artificer','Spell-Refueling Ring'): ('Action', 'Spell-Refueling Ring',
            "While worn: recover one expended spell slot of 3rd level or lower. Once per dawn."),
        ('Artificer','Arcane Armor'): ('Action', 'Arcane Armor',
            "With smith's tools in hand, turn armor you're wearing into Arcane Armor: ignores any "
            "STR requirement, usable as a spellcasting focus, attaches and can't be removed "
            "against your will (retract/deploy the helmet as a bonus action), and replaces "
            "missing limbs. Doff/don as an action; stays Arcane Armor until you wear other armor "
            "or die."),
        ('Artificer','Armor Model'): ('Passive', 'Armor Model (passive)',
            "Choose Guardian or Infiltrator for your Arcane Armor's special benefits and weapon "
            "(INT for its attack/damage rolls). Change model on a short or long rest with smith's "
            "tools in hand."),
        ('Artificer','Thunder Gauntlets'): ('Passive', 'Thunder Gauntlets (passive)',
            "Guardian: each gauntlet is a free simple melee weapon, 1d8 thunder. A creature you "
            "hit has disadvantage on attacks against anyone but you until the start of your next turn."),
        ('Artificer','Defensive Field'): ('Bonus Action', 'Defensive Field',
            "Guardian: gain temp HP equal to your Artificer level, replacing any you have. Lost "
            "if you doff the armor. Uses = proficiency bonus per long rest."),
        ('Artificer','Lightning Launcher'): ('Passive', 'Lightning Launcher (passive)',
            "Infiltrator: a free simple ranged weapon (90/300 ft), 1d6 lightning. Once per turn "
            "on a hit, deal an extra 1d6 lightning damage."),
        ('Artificer','Powered Steps'): ('Passive', 'Powered Steps (passive)', "Infiltrator: +5 ft walking speed."),
        ('Artificer','Dampening Field'): ('Passive', 'Dampening Field (passive)',
            "Infiltrator: advantage on DEX (Stealth) checks (cancels out any disadvantage the armor itself imposes)."),
        ('Artificer','Perfected Armor'): ('Reaction', 'Perfected Armor',
            "Guardian: force a Huge-or-smaller creature within 30 ft that ends its turn there to "
            "make a STR save or get pulled up to 25 ft to you (melee attack if pulled adjacent). "
            "Uses = proficiency bonus per long rest. Infiltrator: a creature hit by Lightning "
            "Launcher glimmers until your next turn — dim light, disadvantage attacking you, and "
            "the next attack against it has advantage plus 1d6 extra lightning on a hit."),
        ('Artificer','Experimental Elixir'): ('Action', 'Experimental Elixir',
            "Produce an elixir in an empty flask (needs alchemist's supplies); roll d6 for its "
            "effect: 1 Healing (2d4+INT mod HP), 2 Swiftness (+10 ft speed, 1 hr), 3 Resilience "
            "(+1 AC, 10 min), 4 Boldness (+1d4 to all attacks/saves, 1 min), 5 Flight (10 ft fly "
            "speed, 10 min), 6 Transformation (Alter Self, 10 min). Drink or administer as an "
            "action. Lasts until drunk or your next long rest ends. Extra elixirs cost a spell slot each.",
        ),
        ('Artificer','Eldritch Cannon'): ('Action', 'Eldritch Cannon',
            "Create a Small/Tiny cannon within 5 ft (needs woodcarver's or smith's tools; AC 18, "
            "HP = 5×artificer level; only one at a time). Choose its type: Flamethrower "
            "(bonus action, 15-ft cone, DEX save or 2d8 fire, half on success), Force Ballista "
            "(bonus action, ranged spell attack within 120 ft, 2d8 force + push 5 ft), or "
            "Protector (bonus action, itself + chosen creatures within 10 ft gain 1d8+INT mod "
            "temp HP). Lasts 1 hour or until destroyed/dismissed.",
        ),
        ('Artificer','Soul of Artifice'): ('Reaction', 'Soul of Artifice',
            "+1 to all saving throws per attuned magic item. If reduced to 0 HP but not killed "
            "outright: end one of your infusions to drop to 1 HP instead of 0 — use the button on "
            "the HP card to actually do this."),
        ('Barbarian','Fanatical Focus'): ('Reaction', 'Fanatical Focus', "Once per rage, if you fail a saving throw, reroll it and take the new result."),
        ('Barbarian','Zealous Presence'): ('Bonus Action', 'Zealous Presence', "Up to 10 chosen creatures within 60 ft gain advantage on attack rolls and saves until the start of your next turn. 1/LR."),
        ('Rogue','Cunning Action'):    ('Bonus Action','Cunning Action','Dash, Disengage, or Hide as a bonus action.'),
        ('Rogue','Uncanny Dodge'):     ('Reaction',    'Uncanny Dodge','Halve damage from one attack you can see. Requires no incapacitation.'),
        ('Rogue','Evasion'):           ('Passive',     'Evasion (passive)','On DEX save for half damage: no damage on success, half on fail.'),
        ('Rogue','Reliable Talent'):  ('Passive', 'Reliable Talent (passive)', "Whenever you make an ability check with a skill or tool you're proficient in, treat any roll of 9 or lower on the d20 as a 10."),
        ('Rogue','Blindsense'):       ('Passive', 'Blindsense (passive)', "If you can hear, you're aware of the location of any hidden or invisible creature within 10 ft of you."),
        ('Rogue','Elusive'):          ('Passive', 'Elusive (passive)', "No attack roll has advantage against you while you aren't incapacitated."),
        ('Rogue','Stroke of Luck'):  ('Bonus Action', 'Stroke of Luck', "Turn a missed attack into a hit, or a failed ability check into a success (treat the roll as 20). 1/LR."),
        ('Rogue','Fast Hands'):      ('Bonus Action', 'Fast Hands', "Use your Cunning Action bonus action for a Sleight of Hand check, using thieves' tools to disarm a trap or open a lock, or the Use an Object action."),
        ('Rogue','Second-Story Work'): ('Passive', 'Second-Story Work (passive)', "Climbing no longer costs extra movement. Running jump distance increases by your DEX modifier."),
        ('Rogue','Supreme Sneak'):   ('Passive', 'Supreme Sneak (passive)', "Advantage on Stealth checks if you move no more than half your speed on the same turn."),
        ('Rogue','Use Magic Device'): ('Passive', 'Use Magic Device (passive)', "Ignore all class, race, and level requirements on the use of magic items."),
        ('Rogue',"Thief's Reflexes"): ('Passive', "Thief's Reflexes (passive)", "In the first round of any combat, take two turns: one at your normal initiative, one at initiative -10. Can't use this feature when you're surprised."),
        ('Rogue','Mage Hand Legerdemain'): ('Action', 'Mage Hand Legerdemain', "Your Mage Hand is invisible, and you can use it to stow/retrieve objects in a container worn/carried by another, or to pick locks/disarm traps at range."),
        ('Rogue','Magical Ambush'):  ('Passive', 'Magical Ambush (passive)', "If you're hidden from a creature when you cast a spell on it, the creature has disadvantage on any saving throw against the spell this turn."),
        ('Rogue','Versatile Trickster'): ('Bonus Action', 'Versatile Trickster', "Use your Mage Hand to distract a creature within 5 ft of it, gaining advantage on attack rolls against that creature until the end of your turn."),
        ('Rogue','Spell Thief'):     ('Reaction', 'Spell Thief', "When a creature casts a spell targeting you, force a save; on a failure, negate the spell and steal it for 8 hours. 1/LR."),
        ('Rogue','Assassinate'):     ('Passive', 'Assassinate (passive)', "You have advantage on attack rolls against any creature that hasn't taken a turn yet. Any hit you score against a surprised creature is a critical hit."),
        ('Rogue','Bonus Proficiencies (Assassin)'): ('Passive', 'Bonus Proficiencies (passive)',
            "Proficiency with the disguise kit and the poisoner's kit."),
        ('Rogue','Master of Intrigue'): ('Passive', 'Master of Intrigue (passive)',
            "Proficiency with the disguise kit, the forgery kit, and one gaming set of your choice. "
            "Learn 2 languages of your choice. Unerringly mimic the speech patterns and accent of a "
            "creature you've heard speak for at least 1 minute (if you know the language)."),
        ('Rogue','Infiltration Expertise'): ('Passive', 'Infiltration Expertise (passive)', "Spend 7 days and 25 gp to establish a false identity, complete with documentation, contacts, and disguises."),
        ('Rogue','Impostor'):        ('Action', 'Impostor', "Perfectly mimic another person's speech, writing, and behavior after spending at least 3 hours studying them."),
        ('Rogue','Death Strike'):    ('Passive', 'Death Strike (passive)', "When you hit a surprised creature, it must succeed on a CON save (DC 8 + your DEX modifier + proficiency bonus) or take double damage from the hit."),
        ('Rogue','Ear for Deceit'):  ('Passive', 'Ear for Deceit (passive)', "When you make a WIS (Insight) check to determine whether a creature is lying, treat a roll of 7 or lower on the die as an 8."),
        ('Rogue','Unerring Eye'):    ('Action', 'Unerring Eye', "Sense that an illusion, shapechanger not in its true form, or other magical deception is present within 30 ft (you don't learn what it is or its true nature). Uses = WIS modifier (min 1) per long rest. Can't use while blinded or deafened."),
        ('Rogue','Eye for Detail'):  ('Bonus Action', 'Eye for Detail', "Make a Wisdom (Perception) or Intelligence (Investigation) check to spot a hidden object/creature, or find clues, as a bonus action."),
        ('Rogue','Insightful Fighting'): ('Bonus Action', 'Insightful Fighting', "Contest Insight against a creature's Deception to read its combat style; on success, Sneak Attack against it doesn't require advantage for 1 minute (but you still can't use it if you have disadvantage on the attack roll)."),
        ('Rogue','Steady Eye'):      ('Passive', 'Steady Eye (passive)', "Advantage on a Wisdom (Perception) or Intelligence (Investigation) check if you move no more than half your speed on the same turn."),
        ("Rogue","Unerring Eye"):    ('Passive', "Unerring Eye (passive)", "Sense the presence of illusions, shapechangers in a different form, and other deceptive magic within 30 ft, unless it's from a source with a higher spell save DC."),
        ('Rogue','Eye for Weakness'): ('Passive', 'Eye for Weakness (passive)', "While Insightful Fighting is active, your Sneak Attack against that target deals an extra 3d6 damage."),
        ('Rogue','Master of Tactics'): ('Bonus Action', 'Master of Tactics', "Use the Help action as a bonus action, targeting an ally within 30 ft (not just 5 ft) who can see or hear you."),
        ('Rogue','Insightful Manipulator'): ('Action', 'Insightful Manipulator', "Study a creature for 1 minute to learn whether its CHA/INT/WIS scores are higher, lower, or equal to your own."),
        ('Rogue','Misdirection'):    ('Reaction', 'Misdirection', "When a creature hits you with an attack, redirect it to a different creature within 5 ft that granted you cover against the original attack."),
        ('Rogue','Soul of Deceit'):  ('Passive', 'Soul of Deceit (passive)', "Your thoughts can't be read by telepathy or similar means unless you allow it. You can present false thoughts with a CHA (Deception) check contested by the reader's WIS (Insight). Magic that would reveal you're lying instead shows you as truthful if you choose, and you can't be magically compelled to tell the truth."),
        ('Rogue','Whispers of the Dead'): ('Passive', 'Whispers of the Dead (passive)', "When you finish a short or long rest, choose one skill or tool proficiency you lack and gain it; you lose it if you use this again to choose a different one."),
        ('Rogue','Wails from the Grave'): ('Action', 'Wails from the Grave', "Immediately after dealing Sneak Attack damage, target a second creature within 30 ft of the first: roll half your Sneak Attack dice for your level (rounded up) as necrotic damage to it. Uses = proficiency bonus per long rest."),
        ('Rogue','Tokens of the Departed'): ('Reaction', 'Tokens of the Departed', "As a reaction when a creature dies within 30 ft, collect a Soul Trinket (hold up to proficiency bonus at once). Spend one to ask its spirit a question, or for other benefits like advantage on a death save or protection from being frightened."),
        ('Rogue','Ghost Walk'):      ('Bonus Action', 'Ghost Walk', "Become spectral for 10 minutes: fly speed 10 ft (can hover), attack rolls against you have disadvantage, and you can move through creatures/objects (1d10 force damage if you end your turn inside one). Requires a long rest to use again, or destroy a Soul Trinket to use it early."),
        ('Rogue',"Death's Friend"):   ('Passive', "Death's Friend (passive)", "Wails from the Grave now also deals its necrotic damage to your original Sneak Attack target. Also, gain a Soul Trinket at the end of a long rest if you have none."),
        ('Rogue','Skirmisher'):      ('Reaction', 'Skirmisher', "When a creature within 5 ft ends its turn there, move up to half your speed without provoking opportunity attacks from it."),
        ('Rogue','Survivalist'):     ('Passive', 'Survivalist (passive)', "Gain proficiency and expertise in the Nature and Survival skills."),
        ('Rogue','Superior Mobility'): ('Passive', 'Superior Mobility (passive)', "Your walking speed increases by 10 ft (climbing and swimming speed too, if you have them)."),
        ('Rogue','Ambush Master'):   ('Passive', 'Ambush Master (passive)', "Advantage on initiative rolls. Attack rolls made by anyone against the first creature you hit in the first round of combat have advantage until the start of your next turn."),
        ('Rogue','Sudden Strike'):   ('Bonus Action', 'Sudden Strike', "When you take the Attack action, make one additional attack as a bonus action. Can be a Sneak Attack (even if you already used it this turn), but not against the same creature twice in one turn."),
        ("Rogue","Sudden Strike"):   ('Passive', 'Sudden Strike (passive)', "Once per turn, make an extra weapon attack as a bonus action; you can apply Sneak Attack to a different attack than the first, without needing advantage."),
        ('Rogue','Psionic Power'):   ('Passive', 'Psionic Power (passive)', "Gain a pool of Psionic Energy dice, used to fuel your Psychic Blades and Psi-Powered Leap."),
        ('Rogue','Psychic Blades'):  ('Action', 'Psychic Blades', "When you take the Attack action, manifest a psychic blade from your free hand and attack with it (finesse, thrown, range 60 ft, 1d6 + attack ability mod psychic damage); it vanishes after. Bonus action: a second blade attack for 1d4 + ability mod."),
        ('Rogue','Soul Blades'):     ('Bonus Action', 'Soul Blades', "Homing Strikes: when you miss with a psychic blade attack, spend a Psionic Energy die and reroll the attack, adding the die to the new roll. Psychic Teleportation: as a bonus action, spend a Psionic Energy die and teleport a distance in feet equal to 10x the roll."),
        ('Rogue','Psychic Veil'):    ('Action', 'Psychic Veil', "Become invisible (with your worn/carried gear) for 1 hour or until you dismiss it, deal damage, or force a save. Once per long rest free; spend a Psionic Energy die to use it again."),
        ('Rogue','Rend Mind'):       ('Passive', 'Rend Mind (passive)', "When you deal Sneak Attack damage with a psychic blade, force a WIS save (DC 8 + PB + DEX mod) or the target is stunned for 1 minute (repeating the save at the end of each of its turns). Once per long rest free; spend 3 Psionic Energy dice to use it again."),
        ('Rogue','Fancy Footwork'):  ('Passive', 'Fancy Footwork (passive)', "During your turn, a creature you attack in melee can't make opportunity attacks against you for the rest of the turn."),
        ('Rogue','Rakish Audacity'): ('Passive', 'Rakish Audacity (passive)', "Add your CHA modifier to your initiative rolls. You can use Sneak Attack without advantage if you're within 5 ft of the target, no other creature is within 5 ft of you, and you don't have disadvantage on the attack roll."),
        ('Rogue','Panache'):         ('Action', 'Panache', "Attempt to charm a creature with a CHA (Persuasion) check contested by its WIS (Insight); on success, it's distracted or has disadvantage attacking others."),
        ('Rogue','Elegant Maneuver'): ('Bonus Action', 'Elegant Maneuver', "Gain advantage on the next Acrobatics or Athletics check you make before the end of your turn."),
        ('Rogue','Master Duelist'):  ('Reaction', 'Master Duelist', "When you miss with an attack roll, reroll it with advantage. 1/SR."),
        ('Monk','Elemental Attunement'): ('Action', 'Elemental Attunement', "Free, automatic discipline (doesn't count against known disciplines): briefly control elemental forces within 30 ft for a minor sensory or utility effect (create/reshape a small amount of an element, light/snuff a small flame, etc.), no ki cost."),
        ('Monk','Ki-Empowered Strikes'): ('Passive', 'Ki-Empowered Strikes (passive)', "Your unarmed strikes count as magical for the purpose of overcoming resistance and immunity to nonmagical attacks and damage."),
        ('Monk','Open Hand Technique'): ('Passive', 'Open Hand Technique (passive)', "When you hit with Flurry of Blows, choose one: the target DEX saves or is knocked prone; the target STR saves or is pushed 15 ft; or the target can't take reactions until the end of your next turn."),
        ('Monk','Wholeness of Body'): ('Action', 'Wholeness of Body', "Regain HP equal to 3x your Monk level. 1/LR."),
        ('Monk','Tranquility'):      ('Passive', 'Tranquility (passive)', "At the end of a long rest, gain the effect of Sanctuary until the start of your next long rest (ends early if you attack/cast a spell)."),
        ('Monk','Quivering Palm'):   ('Bonus Action', 'Quivering Palm', "Spend 3 ki when you hit with an unarmed strike to set up vibrations (lasts days = your Monk level, only 1 creature at a time); later, as an action on the same plane, end them: the target makes a CON save or is reduced to 0 HP, or takes 10d10 necrotic damage on a success."),
        ('Monk','Shadow Arts'):      ('Bonus Action', 'Shadow Arts', "Spend 2 ki to cast Darkness, Darkvision, Pass without Trace, or Silence, without components. Learn Minor Illusion if you don't know it."),
        ('Monk','Shadow Step'):      ('Bonus Action', 'Shadow Step', "In dim light or darkness, teleport up to 60 ft to an unoccupied space you can see that's also in dim light or darkness; gain advantage on your next melee attack this turn."),
        ('Monk','Cloak of Shadows'): ('Action', 'Cloak of Shadows', "In dim light or darkness, become invisible until you attack, cast a spell, or enter bright light."),
        ('Monk','Opportunist'):      ('Reaction', 'Opportunist', "When a creature within 5 ft is hit by an attack from someone else, use your reaction to make a melee attack against that creature."),
        ('Monk','Path of the Kensei'): ('Passive', 'Path of the Kensei (passive)', "Choose 2 kensei weapons (1 more at 6th/11th/17th). Agile Parry: if you make an unarmed strike as part of the Attack action while holding a melee kensei weapon, +2 AC until your next turn. Kensei's Shot: bonus action to add 1d4 damage to your ranged kensei weapon attacks until end of turn."),
        ('Monk','One with the Blade'): ('Passive', 'One with the Blade (passive)', "Your kensei weapon attacks count as magical. Once per turn, spend 1 ki when you hit with a kensei weapon to deal extra damage equal to your Martial Arts die (Deft Strike)."),
        ('Monk','Sharpen the Blade'): ('Bonus Action', 'Sharpen the Blade', "Spend up to 3 ki to grant a kensei weapon you're holding a bonus to attack/damage rolls for 1 minute."),
        ('Monk','Unerring Accuracy'): ('Passive', 'Unerring Accuracy (passive)', "Once per turn on a miss with a kensei weapon attack, reroll it. 1/turn."),
        ('Monk','Arms of the Astral Self'): ('Bonus Action', 'Arms of the Astral Self', "Spend 1 ki to summon spectral arms for 10 min: each creature you choose within 10 ft makes a DEX save or takes force damage (2 Martial Arts die rolls). While manifest: use WIS instead of STR for STR checks/saves; unarmed strikes with the arms (+5 ft reach) use WIS instead of STR/DEX for attack/damage, dealing force damage."),
        ('Monk','Visage of the Astral Self'): ('Bonus Action', 'Visage of the Astral Self', "Spend 1 ki (or as part of manifesting Arms) to summon a spectral visage for 10 min: Astral Sight (see in magical/nonmagical darkness out to 120 ft), and advantage on WIS (Insight) and CHA (Intimidation) checks."),
        ('Monk','Body of the Astral Self'): ('Reaction', 'Body of the Astral Self', "Prerequisite: 11th level, both Arms and Visage manifest (the body appears automatically, no action needed). Deflect Energy: reaction to reduce acid/cold/fire/force/lightning/thunder damage taken by 1d10 + WIS modifier. Empowered Arms: once per turn on a hit with the astral arms, add extra damage equal to your Martial Arts die."),
        ('Monk','Awakened Astral Self'): ('Bonus Action', 'Awakened Astral Self', "Spend 5 ki to summon arms, visage, and body together for 10 minutes: Armor of the Spirit (+2 AC), and Astral Barrage (if using Extra Attack and attacking only with your astral arms, make one additional attack)."),
        ('Monk','Drunken Technique'): ('Passive', 'Drunken Technique (passive)', "When you use Flurry of Blows, gain the benefit of the Disengage action and +10 ft speed until the end of the turn."),
        ('Monk','Bonus Proficiencies (Drunken Master)'): ('Passive', 'Bonus Proficiencies (passive)',
            "Proficiency with brewer's supplies and one type of musical instrument."),
        ('Monk','Ascendant Aspect'): ('Passive', 'Ascendant Aspect (passive)',
            "Blindsight out to 30 ft. Spending a ki point on Breath of the Dragon increases its area "
            "and damage die count. Activating Aspect of the Wyrm also deals damage to creatures in "
            "the aura on a failed DEX save."),
        ('Monk','Tipsy Sway'):       ('Reaction', 'Tipsy Sway', "Spend 2 ki to stagger away 5 ft as a reaction when you're hit, or force a creature that missed you to move 5 ft."),
        ("Monk","Drunkards Luck"):   ('Reaction', "Drunkard's Luck", "Spend 1 ki to gain advantage on an ability check, attack roll, or saving throw you're about to make."),
        ('Monk','Intoxicated Frenzy'): ('Passive', 'Intoxicated Frenzy (passive)', "When you use Flurry of Blows, make up to 3 additional attacks against different creatures within 5 ft, instead of the usual 2 against the same target."),
        ('Monk','Touch of Death (Long Death)'):   ('Passive', 'Touch of Death (Long Death, passive)', "When you reduce a creature within 5 ft of you to 0 HP, gain temporary HP equal to your WIS modifier + your Monk level (min 1)."),
        ('Monk','Hour of Reaping'):  ('Action', 'Hour of Reaping', "Spend 1 ki: each creature within 30 ft that can see you must WIS save or be frightened of you for 1 minute."),
        ('Monk','Mastery of Death'): ('Reaction', 'Mastery of Death', "Spend 1 ki when you'd drop to 0 HP to instead drop to 1 HP."),
        ('Monk','Touch of the Long Death'): ('Action', 'Touch of the Long Death', "Spend 1-10 ki: touch one creature within 5 ft, dealing 2d10 necrotic damage per ki point spent (CON save halves)."),
        ('Monk','Implements of Mercy'): ('Passive', 'Implements of Mercy (passive)', "Gain proficiency in the Insight and Medicine skills, and with the disguise kit and the herbalism kit."),
        ('Monk','Hand of Harm'):     ('Bonus Action', 'Hand of Harm', "Spend 1 ki when you hit with an unarmed strike: deal extra necrotic damage equal to your Martial Arts die + WIS modifier. The target also can't regain HP until the start of your next turn."),
        ('Monk','Hand of Healing'):  ('Action', 'Hand of Healing', "Spend 1 ki: touch a creature to restore HP equal to your Martial Arts die + WIS modifier. Can be used in place of an unarmed strike in Flurry of Blows."),
        ("Monk","Physician's Touch"): ('Passive', "Physician's Touch (passive)", "Hand of Healing can also cure one of: blinded, deafened, paralyzed, poisoned, or stunned. Hand of Harm can also impose the poisoned condition until the end of your next turn."),
        ('Monk','Flurry of Healing and Harm'): ('Passive', 'Flurry of Healing and Harm (passive)', "When you use Flurry of Blows, you can replace both unarmed strikes with Hand of Healing, and Hand of Harm no longer requires a ki point when used as part of Flurry of Blows (still once per turn)."),
        ('Monk','Hand of Ultimate Mercy'): ('Action', 'Hand of Ultimate Mercy', "Spend 5 ki and touch a creature dead for no more than 24 hours to return it to life with 4d10 + WIS modifier HP. 1/LR."),
        ('Monk','Radiant Sun Bolt'): ('Action', 'Radiant Sun Bolt', "Hurl a bolt of radiant energy at a target within 30 ft as a ranged spell attack, dealing radiant damage equal to your martial arts die + DEX modifier; can spend 1 ki for a second bolt."),
        ('Monk','Searing Arc Strike'): ('Bonus Action', 'Searing Arc Strike', "Spend 2+ ki (max total = half your Monk level) to cast Burning Hands as a bonus action immediately after taking the Attack action, scaling with extra ki spent."),
        ('Monk','Searing Sunburst'): ('Action', 'Searing Sunburst', "Create a 20-ft-radius sphere within 150 ft, free of charge: each creature there makes a CON save or takes 2d6 radiant damage (no damage on success). Optionally spend up to 3 ki to add 2d6 more damage per ki spent."),
        ('Monk','Sun Shield'):       ('Reaction', 'Sun Shield', "You shed bright light in a 30 ft radius and dim light for an additional 30 ft (extinguish/restore as a bonus action). If a creature hits you with a melee attack while it shines, you can use your reaction to deal radiant damage to it equal to 5 + your WIS modifier."),
        ('Monk','Draconic Disciple'): ('Passive', 'Draconic Disciple (passive)', "Learn a cantrip from the Draconic Sorcery-adjacent list and gain a small bonus tied to your chosen dragon ancestor's damage type."),
        ('Monk','Breath of the Dragon'): ('Action', 'Breath of the Dragon', "Spend 2 ki to exhale a breath weapon (line or cone) matching your dragon ancestor's damage type, dealing martial-arts-die-based damage (DEX or CON save for half)."),
        ('Monk','Wings Unfurled'):  ('Bonus Action', 'Wings Unfurled', "When you use Step of the Wind, spectral wings unfurl (vanishing at end of turn), granting a flying speed equal to your walking speed while they last. Uses = proficiency bonus per long rest."),
        ('Monk','Aspect of the Wyrm'): ('Bonus Action', 'Aspect of the Wyrm', "Spend 2 ki to frighten creatures in a cone matching your dragon ancestor's energy, or gain a protective aspect (resistance to your ancestor's damage type and one other minor benefit) for 1 minute."),
        ('Monk','Draconic Presence (Monk)'): ('Action', 'Draconic Presence (Monk)', "Spend 3 ki to emanate draconic awe or dread for 1 minute: each creature of your choice within 60 ft must WIS save or be charmed/frightened by you."),
        ('Monk','Flurry of Blows'):    ('Bonus Action','Flurry of Blows','Spend 1 Ki: make 2 extra unarmed strikes as bonus action after Attack action.'),
        ('Monk','Patient Defense'):    ('Bonus Action','Patient Defense','Spend 1 Ki: take Dodge action as bonus action.'),
        ('Monk','Step of the Wind'):   ('Bonus Action','Step of the Wind','Spend 1 Ki: take Dash or Disengage as bonus action; jump distance doubled this turn.'),
        ('Monk','Deflect Missiles'):   ('Reaction',    'Deflect Missiles','Reduce ranged weapon damage by 1d10+DEX+Monk level. If reduced to 0, catch and throw it.'),
        ('Monk','Slow Fall'):          ('Reaction',    'Slow Fall','Reduce falling damage by 5 × Monk level.'),
        ('Monk','Stunning Strike'):    ('Passive',     'Stunning Strike','After hitting: spend 1 Ki. Target DC CON save or stunned until end of your next turn.'),
        ('Paladin','Divine Smite'):    ('Action',     'Divine Smite','On hit: expend a spell slot for 2d8+1d8/slot level radiant (+1d8 vs undead/fiends, max 5d8).'),
        ('Paladin','Cleansing Touch'): ('Action', 'Cleansing Touch', "End one spell on yourself or a willing creature you touch. Uses = CHA mod per long rest."),
        ('Paladin','Sacred Weapon'):   ('Bonus Action', 'Sacred Weapon', 'Channel Divinity: touch a weapon for 1 minute — add CHA mod to attack rolls with it, and it sheds bright light 20 ft.'),
        ('Paladin','Aura of Devotion'): ('Passive', 'Aura of Devotion (passive)', "You and friendly creatures within 10 ft of you (30 ft at 18th level) can't be charmed while you are conscious."),
        ('Paladin','Turn the Unholy'): ('Action', 'Turn the Unholy', "Channel Divinity: undead and fiends within 30 ft must succeed on a WIS save or be turned for 1 minute."),
        ('Paladin','Purity of Spirit'): ('Passive', 'Purity of Spirit (passive)', "You are always under the effect of Protection from Evil and Good."),
        ('Paladin','Holy Nimbus'):     ('Bonus Action', 'Holy Nimbus', "30-ft aura of sunlight for 1 minute. Enemies that start their turn in it take 10 radiant damage. 1/LR."),
        ('Paladin','Abjure Enemy'):    ('Action', 'Abjure Enemy', "Channel Divinity: frighten one creature within 60 ft (WIS save, disadvantage for fiends/undead). Frightened this way has speed 0."),
        ('Paladin','Vow of Enmity'):   ('Bonus Action', 'Vow of Enmity', "Channel Divinity: gain advantage on attack rolls against one creature within 10 ft for 1 minute."),
        ('Paladin','Relentless Avenger'): ('Passive', 'Relentless Avenger (passive)', "When you hit with an opportunity attack, you can move up to half your speed toward the creature you hit, without provoking opportunity attacks."),
        ('Paladin','Soul of Vengeance'): ('Reaction', 'Soul of Vengeance', "When a creature under your Vow of Enmity makes an attack, use your reaction to make a melee weapon attack against it."),
        ('Paladin','Avenging Angel'):  ('Action', 'Avenging Angel', "Transform for 1 hour: fly speed 60 ft, 30-ft aura where enemies entering must WIS save or become frightened. 1/LR."),
        ('Paladin','Conquering Presence'): ('Action', 'Conquering Presence', "Channel Divinity: each creature of your choice within 30 ft you can see must WIS save or be frightened of you for 1 minute (repeats each turn)."),
        ('Paladin','Guided Strike'):   ('Bonus Action', 'Guided Strike', "Channel Divinity: gain +10 to one attack roll."),
        ('Paladin','Aura of Conquest'): ('Passive', 'Aura of Conquest (passive)', "Frightened creatures within 10 ft (30 ft at 18th) have speed 0 and take psychic damage equal to half your Paladin level at the start of each of their turns."),
        ('Paladin','Scornful Rebuke'): ('Passive', 'Scornful Rebuke (passive)', "When a creature hits you with an attack, it takes psychic damage equal to your CHA modifier."),
        ('Paladin','Invincible Conqueror'): ('Action', 'Invincible Conqueror', "Become an avatar of conquest for 1 minute: resistance to all damage, one additional attack when you take the Attack action, melee crits on 19-20. 1/LR."),
        ('Paladin','Emissary of Peace'): ('Bonus Action', 'Emissary of Peace', "Channel Divinity: +5 to CHA (Persuasion) checks for the next 10 minutes."),
        ('Paladin','Rebuke the Violent'): ('Reaction', 'Rebuke the Violent', "Channel Divinity: when an attacker within 30 ft damages someone other than you, it WIS saves or takes radiant damage equal to the damage it just dealt (half on success)."),
        ('Paladin','Aura of the Guardian'): ('Reaction', 'Aura of the Guardian', "Transfer damage from an ally within 10 ft (30 ft at 18th) to yourself instead."),
        ('Paladin','Protective Spirit'): ('Passive', 'Protective Spirit (passive)', "If you're below half HP at the start of your turn and not unconscious, regain 1d6 + half your Paladin level in HP."),
        ('Paladin','Emissary of Redemption'): ('Passive', 'Emissary of Redemption (passive)', "Always active from 20th level: resistance to all damage from others' attacks/spells/effects (implemented). Whenever a creature hits you, it takes radiant damage equal to half the damage you took (reminder only). Both stop working against a specific creature if you attack/damage/force a save on it, until your next long rest."),
        ('Paladin','Champion Challenge'): ('Action', 'Champion Challenge', "Channel Divinity: challenge creatures within 30 ft (WIS save) — they can't willingly move away from you."),
        ('Paladin','Turn the Tide'): ('Bonus Action', 'Turn the Tide', "Channel Divinity: each creature of your choice within 30 ft who can hear you and has no more than half its HP regains 1d6 + CHA mod HP (min 1)."),
        ('Paladin','Divine Allegiance'): ('Reaction', 'Divine Allegiance', "Redirect damage from an adjacent ally to yourself instead."),
        ('Paladin','Unyielding Saint'): ('Passive', 'Unyielding Saint (passive)', "You have advantage on saving throws to avoid becoming paralyzed or stunned."),
        ('Paladin','Exalted Champion'): ('Action', 'Exalted Champion', "Resistance to bludgeoning/piercing/slashing for 1 hour; allies within 30 ft get advantage on death saves and WIS saves. 1/LR."),
        ('Paladin','Peerless Athlete'): ('Bonus Action', 'Peerless Athlete', "For 10 minutes: advantage on STR (Athletics)/DEX (Acrobatics) checks, double carry/push/drag/lift capacity, +10 ft jump distance."),
        ('Paladin','Inspiring Smite'): ('Bonus Action', 'Inspiring Smite', "Immediately after Divine Smite damage, Channel Divinity: distribute 2d8 + Paladin level in temp HP among creatures within 30 ft (including yourself)."),
        ('Paladin','Aura of Alacrity'): ('Passive', 'Aura of Alacrity (passive)', "Your walking speed increases by 10 ft (implemented). Allies who start their turn within 5 ft (10 ft at 18th) of you gain the same bonus until they move away — this ally-extension isn't tracked."),
        ('Paladin','Glorious Defense'): ('Reaction', 'Glorious Defense', "When a creature hits an ally within 10 ft, give that ally +CHA mod to AC against that attack and make a melee attack against the attacker."),
        ('Paladin','Living Legend'):   ('Bonus Action', 'Living Legend', "For 1 minute: advantage on all CHA checks; once per turn, turn a missed weapon attack into a hit instead; and if you fail a save, use your reaction to reroll it (must use the new result). Once per long rest, or expend a 5th-level spell slot to use it again."),
        ('Paladin','Abjure the Extraplanar'): ('Action', 'Abjure the Extraplanar', "Channel Divinity: each aberration/celestial/elemental/fey/fiend within 30 ft that can hear you WIS saves or is turned for 1 minute or until it takes damage."),
        ('Paladin','Aura of the Sentinel'): ('Passive', 'Aura of the Sentinel (passive)', "You and allies within 10 ft of you (30 ft at 18th level) gain a bonus to initiative rolls equal to your proficiency bonus."),
        ('Paladin',"Watcher's Will"):  ('Action', "Watcher's Will", "Channel Divinity: up to CHA modifier (min 1) creatures within 30 ft (including you) gain advantage on INT/WIS/CHA saves for 1 minute."),
        ('Paladin','Vigilant Rebuke'): ('Reaction', 'Vigilant Rebuke', "Whenever you or a creature within 30 ft succeeds on an INT/WIS/CHA save, use your reaction to deal 2d8 + CHA mod force damage to whatever forced that save."),
        ('Paladin','Mortal Bulwark'):  ('Bonus Action', 'Mortal Bulwark', "For 1 minute: truesight 120 ft, advantage vs aberrations/celestials/elementals/fey/fiends, on hit force a CHA save or banish to native plane. 1/LR or 5th-level slot."),
        ("Paladin","Nature's Wrath"):  ('Action', "Nature's Wrath", "Channel Divinity: spectral vines restrain a creature within 15 ft (STR save, repeatable at end of turn)."),
        ('Paladin','Aura of Warding'): ('Passive', 'Aura of Warding (passive)', "You and friendly creatures within 10 ft of you (30 ft at 18th level) have resistance to damage from spells."),
        ('Paladin','Turn the Faithless'): ('Action', 'Turn the Faithless', "Channel Divinity: each fey or fiend within 30 ft that can hear you WIS saves or is turned for 1 minute or until it takes damage."),
        ('Paladin','Undying Sentinel'): ('Passive', 'Undying Sentinel (passive)', "When reduced to 0 HP and not killed outright, drop to 1 HP instead. 1/LR."),
        ('Paladin','Elder Champion'):  ('Action', 'Elder Champion', "Transform for 1 minute: regain 10 HP each turn, cast Paladin spells as a bonus action, enemies within 10 ft have disadvantage on saves vs your spells/Channel Divinity. 1/LR."),
        ('Paladin','Control Undead'):  ('Action', 'Control Undead', "Channel Divinity: one undead within 30 ft WIS saves or obeys your commands for 24 hours."),
        ('Paladin','Aura of Hate'):    ('Passive', 'Aura of Hate (passive)', "You and fiend/undead allies within 10 ft of you (30 ft at 18th level) add your CHA modifier (min +1) to melee weapon damage rolls. A creature benefits from only one Paladin's aura at a time."),
        ('Paladin','Supernatural Resistance'): ('Passive', 'Supernatural Resistance (passive)', "You have resistance to bludgeoning, piercing, and slashing damage from nonmagical attacks."),
        ('Paladin','Dreadful Aspect'): ('Action', 'Dreadful Aspect', "Channel Divinity: each creature of your choice within 30 ft that can see you WIS saves or is frightened for 1 minute. If it ends its turn more than 30 ft away from you, it can repeat the save to end the effect on itself."),
        ('Paladin','Dread Lord'):      ('Action', 'Dread Lord', "30-ft aura of gloom for 1 minute: dims light, deeper shadow on chosen creatures, frightened enemies starting their turn in it take 4d10 psychic. 1/LR."),
        ('Paladin','Lay on Hands'):   ('Action',       'Lay on Hands','Heal HP from pool (5 x Paladin level), or spend 5 HP to cure disease/poison.'),
        ('Paladin','Divine Sense'):    ('Action',      'Divine Sense','Know location of celestial/fiend/undead within 60 ft for 1 turn. 1+CHA mod/LR.'),
        ('Paladin','Aura of Protection'):('Passive',   'Aura of Protection (passive)','Allies within 10 ft add CHA mod to saving throws while you are conscious.'),
        ('Ranger','Hunters Mark'):    ('Bonus Action', "Hunter's Mark",'Cast as bonus action: +1d6 damage to target, adv Perception/Survival to find it.'),
        ('Ranger','Favored Enemy'):    ('Passive',     'Favored Enemy (passive)','Adv on Survival to track chosen enemy types; adv on INT checks about them.'),
        ('Ranger','Natural Explorer'): ('Passive', 'Natural Explorer (passive)', "In your favored terrain: double proficiency bonus on INT/WIS checks related to it, difficult terrain doesn't slow your group, you can't become lost except by magic, and you can forage for double food."),
        ('Ranger','Primeval Awareness'): ('Action', 'Primeval Awareness', "Expend a spell slot to sense the presence of aberrations, celestials, dragons, elementals, fey, fiends, and undead within 1 mile (6 miles in favored terrain)."),
        ('Ranger',"Ranger's Companion"): ('Bonus Action', "Ranger's Companion",
            "Add your proficiency bonus to the beast's AC, attack rolls, damage rolls, and any "
            "saving throws/skills it's proficient in. Its HP = its own stat block or 4x your "
            "Ranger level, whichever is higher. Command it to take the Attack, Dash, "
            "Disengage, Dodge, or Help action; otherwise it takes the Dodge action on its own."),
        ('Ranger','Drake Companion'): ('Bonus Action', 'Drake Companion',
            "AC = 14 + your proficiency bonus (natural armor). HP = 5 + 5x your Ranger level "
            "(d10 hit dice). Can't summon more than once per long rest if it isn't already out. "
            "Command it to take the Attack, Dash, Disengage, Dodge, or Help action; otherwise "
            "it acts on its own."),
        ('Ranger','Bond of Fang and Scale'): ('Passive', 'Bond of Fang and Scale (passive)',
            "Resistance to the drake's breath weapon damage type. When you or your drake hits a "
            "creature, the other can add extra damage of that type equal to your proficiency bonus, "
            "once per turn."),
        ('Ranger','Perfected Bond'): ('Passive', 'Perfected Bond (passive)',
            "Your drake grows to Large size (if it wasn't already) and its stats improve further."),
        ("Ranger","Land's Stride"):   ('Passive', "Land's Stride (passive)", "Moving through nonmagical difficult terrain costs no extra movement. Advantage on saves against magical plants that impede movement."),
        ('Ranger','Hide in Plain Sight'): ('Action', 'Hide in Plain Sight', "Spend 1 minute creating camouflage. While motionless, +10 to Stealth checks as long as you don't move or take actions."),
        ('Ranger','Vanish'):          ('Bonus Action', 'Vanish', "Take the Hide action as a bonus action. Can't be tracked by nonmagical means unless you choose to leave a trail."),
        ('Ranger','Feral Senses'):    ('Passive', 'Feral Senses (passive)', "While not blinded or deafened, you know the location of invisible creatures within 30 ft. No disadvantage attacking a hidden creature."),
        ('Ranger','Foe Slayer'):      ('Passive', 'Foe Slayer (passive)', "Once per turn, add your WIS modifier to an attack roll or damage roll against a favored enemy."),
        ("Ranger","Hunter's Prey"):   ('Passive', "Hunter's Prey (passive)", "Colossus Slayer (once/turn, extra 1d8 damage to a target below max HP), Giant Killer (reaction attack a Large+ creature that hits or misses you within 5 ft), or Horde Breaker (once/turn, attack a second creature within 5 ft of your first target) — whichever you chose at 3rd level."),
        ('Ranger','Defensive Tactics'): ('Passive', 'Defensive Tactics (passive)', "Escape the Horde (opportunity attacks against you have disadvantage), Multiattack Defense (+4 AC against further attacks from a creature that just hit you), or Steel Will (advantage on saves against fear) — whichever you chose at 7th level."),
        ('Ranger','Multiattack'):     ('Action', 'Multiattack', "Volley (ranged attack against any number of creatures within 10 ft of a point in range) or Whirlwind Attack (melee attack against any number of creatures within 5 ft) — whichever you chose at 11th level."),
        ("Ranger","Superior Hunter's Defense"): ('Passive', "Superior Hunter's Defense (passive)", "Evasion, Stand Against the Tide (a hostile creature that misses you with a melee attack must repeat it against another creature), or Uncanny Dodge — whichever you chose at 15th level."),
        ('Ranger','Exceptional Training'): ('Bonus Action', 'Exceptional Training', "Your companion doesn't attack on its turn; instead command it to Dash/Disengage/Help, or have it take the Attack action if it doesn't already have that option."),
        ('Ranger','Bestial Fury'):    ('Passive', 'Bestial Fury (passive)', "Your companion can make two attacks when you command it to attack."),
        ('Ranger','Share Spells'):    ('Passive', 'Share Spells (passive)', "When you cast a spell targeting only yourself, you can also affect your companion if it's within 30 ft."),
        ('Ranger','Dread Ambusher'):  ('Passive', 'Dread Ambusher (passive)', "At the start of your first turn of combat, your speed increases by 10 ft until the end of that turn. If you attack that turn, make one additional weapon attack; on a hit, it deals an extra 1d8 damage."),
        ('Ranger','Umbral Sight'):    ('Passive', 'Umbral Sight (passive)', "You gain darkvision, or +30 ft if you already have it. You're invisible to creatures relying on darkvision to see you in darkness."),
        ('Ranger','Iron Mind'):       ('Passive', 'Iron Mind (passive)', "Gain proficiency in WIS saving throws. If already proficient, instead gain proficiency in CHA or INT saving throws (your choice)."),
        ('Ranger',"Stalker's Flurry"): ('Passive', "Stalker's Flurry (passive)", "Once per turn, when you miss with a weapon attack, immediately make another weapon attack as part of the same action."),
        ('Ranger','Shadowy Dodge'):   ('Reaction', 'Shadowy Dodge', "When a creature makes an attack roll against you, impose disadvantage on it."),
        ('Ranger','Detect Portal'):   ('Action', 'Detect Portal', "Sense the presence and general direction of the nearest planar portal within 1 mile (1/SR or LR)."),
        ('Ranger','Planar Warrior'):  ('Bonus Action', 'Planar Warrior', "Force weapon damage against one creature you can see within 30 ft, dealing an extra 1d8 force damage on the next hit before the end of your next turn."),
        ('Ranger','Ethereal Step'):   ('Bonus Action', 'Ethereal Step', "Cast Etherealness on yourself without a spell slot; the spell ends at the end of the current turn. 1/SR or LR."),
        ('Ranger','Distant Strike'):  ('Passive', 'Distant Strike (passive)', "When you take the Attack action, teleport up to 10 ft before each attack. If you attack at least two different creatures, make one additional attack against a third."),
        ('Ranger','Spectral Defense'): ('Reaction', 'Spectral Defense', "When you take damage, give yourself resistance to all of that attack's damage this turn."),
        ("Ranger","Hunter's Sense"):  ('Action', "Hunter's Sense", "Study a creature within 60 ft to learn if it has damage resistances/immunities and, if so, which."),
        ("Ranger","Slayer's Prey"):   ('Bonus Action', "Slayer's Prey", "Mark one creature you can see. Once per turn, deal an extra 1d6 damage to it."),
        ('Ranger',"Hunter's Sense"): ('Action', "Hunter's Sense", "Study a creature within 60 ft to learn its damage immunities, resistances, or vulnerabilities. Uses = WIS modifier per long rest."),
        ('Ranger',"Slayer's Prey"): ('Bonus Action', "Slayer's Prey", "Mark a creature you can see as your quarry. Once per turn, deal an extra 1d6 damage to it. Ends if it drops to 0 HP or you choose a new target."),
        ('Ranger','Supernatural Defense'): ('Passive', 'Supernatural Defense (passive)', "Add 1d6 whenever your Slayer's Prey target forces you to make a saving throw, or when you make an ability check to escape that target's grapple."),
        ('Ranger',"Magic-User's Nemesis"): ('Reaction', "Magic-User's Nemesis", "When you see a creature within 60 ft casting a spell or teleporting, force a WIS save (vs your spell save DC) or the spell/teleport fails and is wasted. Uses = 1/short or long rest."),
        ('Ranger',"Slayer's Counter"): ('Reaction', "Slayer's Counter", "If your Slayer's Prey target forces a saving throw from you, make a weapon attack against it first — if it hits, your saving throw automatically succeeds."),
        ("Ranger","Slayer's Counter"): ('Reaction', "Slayer's Counter", "When your Slayer's Prey target forces a save from you, make an attack against it instead — on a hit, the save auto-succeeds."),
        ('Ranger','Dreadful Strikes'): ('Passive', 'Dreadful Strikes (passive)', "Once per turn, deal an extra 1d4 psychic damage on a weapon hit."),
        ('Ranger','Otherworldly Glamour'): ('Passive', 'Otherworldly Glamour (passive)', "Gain proficiency in one of Deception/Performance/Persuasion, and add WIS mod to that skill's checks."),
        ('Ranger','Beguiling Twist'): ('Reaction', 'Beguiling Twist', "Gain advantage on saves against being charmed/frightened; when an ally near you succeeds a charm/fright save, redirect it as your reaction."),
        ('Ranger','Fey Reinforcements'): ('Action', 'Fey Reinforcements', "Cast Conjure Woodland Beings once without a slot, summoning a single Fey Spirit instead of the usual list. 1/LR."),
        ('Ranger','Misty Wanderer'):  ('Bonus Action', 'Misty Wanderer', "Cast Misty Step without a spell slot (can bring one willing creature along). 1/SR or LR."),
        ('Ranger','Gathered Swarm'):  ('Passive', 'Gathered Swarm (passive)', "Once per turn, immediately after you hit with an attack, choose one: the target takes 1d6 piercing damage from your swarm; or it makes a STR save or is moved up to 15 ft horizontally; or you are moved 5 ft horizontally."),
        ('Ranger','Swarmkeeper Magic'): ('Passive', 'Swarmkeeper Magic (passive)', "Learn the Mage Hand cantrip if you don't already know it — the hand takes the form of your swarming spirits."),
        ('Ranger','Writhing Tide'):   ('Bonus Action', 'Writhing Tide', "Gain a flying speed of 10 ft and the ability to hover, for 1 minute or until incapacitated. Uses = proficiency bonus per long rest."),
        ('Ranger','Mighty Swarm'):    ('Passive', 'Mighty Swarm (passive)', "Gathered Swarm's damage increases to 1d8; a creature that fails its save against being moved can also be knocked prone; when the swarm moves you, you have half cover until the start of your next turn."),
        ('Ranger','Swarming Dispersal'): ('Reaction', 'Swarming Dispersal', "When you take damage, gain resistance to it and teleport to an unoccupied space you can see within 30 ft."),
        ('Ranger','Draconic Gift'):   ('Passive', 'Draconic Gift (passive)', "Gain resistance to one damage type shared with your drake, and other minor draconic benefits, when your drake is nearby."),
        ("Ranger","Drakes Breath"):   ('Action', "Drake's Breath", "Your drake companion can use a breath weapon matching its damage type. Uses = proficiency bonus per long rest."),
        ('Ranger','Symbiotic Link'):  ('Passive', 'Symbiotic Link (passive)', "When your drake takes damage, you can take some of it instead; you also gain resistance while your drake is within 5 ft."),
        ("Ranger","Dragons Purpose"): ('Passive', "Dragon's Purpose (passive)", "Your drake grows to Large size and gains additional combat benefits."),
        ('Fighter','Improved Critical'): ('Passive', 'Improved Critical (passive)', "Your weapon attacks score a critical hit on a roll of 19 or 20."),
        ('Fighter','Remarkable Athlete'): ('Passive', 'Remarkable Athlete (passive)', "Add half your proficiency bonus (round up) to STR/DEX/CON checks that don't already use your proficiency bonus, and to initiative rolls. Running jump distance increases by your STR modifier."),
        ('Fighter','Additional Fighting Style'): ('Passive', 'Additional Fighting Style (passive)', "Choose a second Fighting Style from the list."),
        ('Fighter','Superior Critical'): ('Passive', 'Superior Critical (passive)', "Your weapon attacks score a critical hit on a roll of 18-20."),
        ('Fighter','Survivor (Champion)'):      ('Passive', 'Survivor (Champion, passive)', "At the start of each of your turns, if you have no more than half your max HP (but not 0 HP), you regain 5 + CON modifier HP."),
        ('Fighter','Rallying Cry'):  ('Bonus Action', 'Rallying Cry', "When you use Second Wind, up to 3 allies within 60 ft who can see or hear you each regain HP equal to your Fighter level."),
        ('Fighter','Royal Envoy'):   ('Passive', 'Royal Envoy (passive)', "Gain proficiency in Persuasion (or Animal Handling/Insight/Intimidation/Performance if already proficient in Persuasion), plus expertise in that skill."),
        ('Fighter','Inspiring Surge'): ('Passive', 'Inspiring Surge (passive)', "When you use Action Surge, one ally within 60 ft who can see or hear you can use their reaction to make one weapon attack."),
        ('Fighter','Bulwark'):       ('Passive', 'Bulwark (passive)', "When you use Indomitable, you can extend its benefit to one ally within 60 ft who can see or hear you and also failed a save, letting them reroll too."),
        ('Fighter','Unwavering Mark'): ('Bonus Action', 'Unwavering Mark', "When you hit a creature with a melee weapon attack, mark it (up to 3 marks at once) until the end of your next turn: it has disadvantage on attack rolls against anyone but you. If a marked creature attacks someone else, you can use a bonus action to make a melee weapon attack against it with advantage, dealing bonus damage equal to your Fighter level if it hits."),
        ('Fighter','Warding Maneuver'): ('Reaction', 'Warding Maneuver', "While wielding a melee weapon or shield: when you or a creature within 5 ft of you is hit by an attack, roll 1d8 and add it to the target's AC against that attack. If it still hits, the target has resistance to that attack's damage. Uses = CON modifier (min 1) per long rest."),
        ('Fighter','Hold the Line'): ('Passive', 'Hold the Line (passive)', "Creatures provoke an opportunity attack from you when they move 5+ feet while within your reach, even if that wouldn't normally provoke. If you hit with that opportunity attack, the target's speed is reduced to 0 until the end of the current turn."),
        ('Fighter','Ferocious Charger'): ('Passive', 'Ferocious Charger (passive)', "After moving 10+ ft in a straight line right before hitting a creature with an attack, it makes a STR save (DC 8 + PB + STR mod) or is knocked prone. Once per turn."),
        ('Fighter','Vigilant Defender'): ('Passive', 'Vigilant Defender (passive)', "You get a special reaction usable once on every creature's turn but your own, only to make an opportunity attack. Can't be used the same turn you take your normal reaction."),
        ('Fighter',"Giant's Might"): ('Bonus Action', "Giant's Might", "Magically grow one size larger for 1 minute (if space allows): unarmed strikes/weapon attacks deal an extra 1d6 damage (1d8 at 10th, 1d10 at 18th if Huge), and you have advantage on STR checks. Uses = proficiency bonus per long rest."),
        ('Fighter','Runic Shield'): ('Reaction', 'Runic Shield', "When another creature you can see within 60 ft is hit by an attack roll, force the attacker to reroll and accept the new result. Uses = proficiency bonus per long rest."),
        ('Fighter','Great Stature'): ('Passive', 'Great Stature (passive)', "You permanently grow 3d4 inches taller. Giant's Might's damage die increases from 1d6 to 1d8."),
        ('Fighter','Master of Runes'): ('Passive', 'Master of Runes (passive)', "Each of your runes can be invoked twice per long rest instead of once."),
        ('Fighter','Runic Juggernaut'): ('Passive', 'Runic Juggernaut (passive)', "While Giant's Might is active, you can grow to Huge size instead (+5 ft reach), and its damage die becomes 1d10."),
        ('Fighter','Fighting Spirit'): ('Bonus Action', 'Fighting Spirit', "Gain advantage on all weapon attack rolls until the end of the current turn, and 5 temporary HP. Uses = 3 per long rest."),
        ('Fighter','Elegant Courtier'): ('Passive', 'Elegant Courtier (passive)', "Add your WIS modifier to CHA (Persuasion) checks. Also gain proficiency in WIS saving throws."),
        ('Fighter','Tireless Spirit'): ('Passive', 'Tireless Spirit (passive)', "When you roll initiative with no uses of Fighting Spirit remaining, you regain one use."),
        ('Fighter','Rapid Strike'): ('Passive', 'Rapid Strike (passive)', "Once per turn, when you have advantage on a weapon attack roll during your Attack action, you can forgo the advantage to make one additional attack with that weapon."),
        ('Fighter','Strength before Death'): ('Reaction', 'Strength before Death', "When you drop to 0 HP, use your reaction to gain temporary HP equal to 1d10 + your Fighter level, remaining conscious and able to act until the end of your next turn (then fall unconscious as normal if not healed)."),
        ('Fighter','Manifest Echo'): ('Bonus Action', 'Manifest Echo', "Summon a spectral echo of yourself within 15 ft. As a free action, move it up to 30 ft, or swap places with it for up to 15 ft of your movement. You can attack from either your space or the echo's. Make an opportunity attack through it as a reaction. Dismiss/resummon as a bonus action."),
        ('Fighter','Unleash Incarnation'): ('Passive', 'Unleash Incarnation (passive)', "While your echo is manifested, when you take the Attack action, make one additional attack from your echo's position. Uses = CON modifier per long rest."),
        ('Fighter','Echo Avatar'): ('Passive', 'Echo Avatar (passive)', "See and hear through your echo (blinded/deafened to your own surroundings meanwhile); its max distance from you increases from 30 to 1,000 ft while doing so."),
        ('Fighter','Shadow Martyr'): ('Reaction', 'Shadow Martyr', "Teleport your echo to intercept an attack meant for a creature you can see, taking the hit in that creature's place. Once per short or long rest."),
        ('Fighter','Reclaim Potential'): ('Passive', 'Reclaim Potential (passive)', "When your echo is destroyed, gain temporary HP; both the amount and your uses of this feature scale with your Constitution modifier."),
        ('Fighter','Legion of One'): ('Passive', 'Legion of One (passive)', "You can manifest 2 echoes at once. When you roll initiative, regain one expended use of Unleash Incarnation."),
        ('Druid','Wild Shape'):        ('Action',      'Wild Shape','Transform into beast (CR limit by level, no fly/swim restrictions lift by 8th). Action to transform back. 2/SR (unlimited at 20th, Archdruid).'),
        ('Druid','Druidic'):          ('Passive', 'Druidic (passive)', "You know Druidic, the secret language of druids. You can also leave hidden messages in it that only other druids can find and read."),
        ('Druid','Beast Spells'):     ('Passive', 'Beast Spells (passive)', "You can cast Druid spells (that don't require material components you don't have) while in Wild Shape."),
        ('Druid','Timeless Body'):    ('Passive', 'Timeless Body (passive)', "You age at a rate of 1 year for every 10 years that pass, and can't be aged magically."),
        ('Druid','Archdruid'):        ('Passive', 'Archdruid (passive)', "Wild Shape uses are unlimited (implemented). You can also ignore verbal/somatic components and most material component costs when casting Druid spells."),
        ('Druid','Combat Wild Shape'): ('Bonus Action', 'Combat Wild Shape', "Use Wild Shape as a bonus action instead of an action. While Wild Shaped, expend a spell slot as a bonus action to heal 1d8 HP per level of the slot."),
        ('Druid','Circle Forms'):    ('Passive', 'Circle Forms (passive)', "Ignore the normal Wild Shape CR limit — max CR 1 starting at 2nd level, rising to Druid level ÷ 3 (rounded down) starting at 6th. Still bound by the same fly/swim movement restrictions as other druids."),
        ('Druid','Primal Strike'):   ('Passive', 'Primal Strike (passive)', "Your attacks in Wild Shape count as magical for overcoming resistance and immunity to nonmagical attacks."),
        ('Druid','Elemental Wild Shape'): ('Bonus Action', 'Elemental Wild Shape', "Expend 2 Wild Shape uses to transform into an air, earth, fire, or water elemental."),
        ('Druid','Thousand Forms'):  ('Action', 'Thousand Forms', "Cast Alter Self at will, without expending a spell slot."),
        ('Druid','Bonus Cantrip (Circle of the Land)'):   ('Passive', 'Bonus Cantrip (passive)', "Learn one extra Druid cantrip of your choice."),
        ('Druid','Natural Recovery'): ('Action', 'Natural Recovery', "During a short rest, recover spell slots totaling up to half your Druid level (rounded up), max 5th level. 1/LR."),
        ('Druid','Circle Spells'):   ('Passive', 'Circle Spells (passive)', "Gain access to extra Druid spells based on your chosen terrain/circle, always prepared, not counting against your number of spells prepared."),
        ("Druid","Lands Stride"):    ('Passive', "Land's Stride (passive)", "Moving through nonmagical difficult terrain costs no extra movement. Advantage on saves against magical plants that impede movement."),
        ("Druid","Natures Sanctuary"): ('Passive', "Nature's Sanctuary (passive)", "Beasts and plant creatures must WIS save to attack you, unless you've damaged them recently. On a success, they can still attack, but have disadvantage."),
        ('Druid','Balm of the Summer Court'): ('Bonus Action', 'Balm of the Summer Court', "Spend up to half your Druid level (rounded down) worth of d6s from your pool (Druid level total) on an ally within 120 ft: roll them, restore that much HP, and grant 1 temp HP per die spent. Regain all dice on a long rest."),
        ('Druid','Hearth of Moonlight and Shadow'): ('Passive', 'Hearth of Moonlight and Shadow (passive)', "During a short or long rest, conjure an invisible 30-ft-radius warded sphere (blocked by total cover): +5 to DEX (Stealth) and WIS (Perception) checks inside, and open flame light isn't visible from outside it. Vanishes at the rest's end or if you leave."),
        ('Druid','Hidden Paths'):    ('Bonus Action', 'Hidden Paths', "Teleport yourself up to 60 ft to an unoccupied space you can see — or use your action to teleport a willing creature you touch up to 30 ft. Uses = WIS modifier per long rest."),
        ('Druid','Walker in Dreams'): ('Action', 'Walker in Dreams', "When you finish a short rest, cast Dream, Scrying, or Teleportation Circle (opening a portal to wherever you last finished a long rest) without a spell slot or components. Once per long rest."),
        ('Druid','Speech of the Woods'): ('Passive', 'Speech of the Woods (passive)', "Learn Sylvan and can communicate with beasts in a limited way."),
        ('Druid','Spirit Totem'): ('Bonus Action', 'Spirit Totem',
            "Summon a spirit totem (30-ft aura, movable 60 ft as a bonus action) for 1 minute — "
            "Bear: chosen creatures gain 5+druid level temp HP on summon, plus advantage on STR "
            "checks/saves while in the aura. Hawk: reaction to grant advantage on an attack roll "
            "against a target in the aura, plus advantage on WIS (Perception) checks while in it. "
            "Unicorn: advantage on checks to detect creatures in the aura; when you heal with a "
            "spell slot, chosen creatures in the aura also heal = your druid level. 1/short or "
            "long rest."),
        ('Druid','Fungal Body'): ('Passive', 'Fungal Body (passive)',
            "Immune to being blinded, deafened, frightened, and poisoned. Critical hits against you "
            "count as normal hits instead."),
        ('Druid','Mighty Summoner'): ('Passive', 'Mighty Summoner (passive)', "Beasts and fey you summon with a conjuration spell gain +2 HP per Hit Die and their natural weapons count as magical."),
        ('Druid','Guardian Spirit'): ('Passive', 'Guardian Spirit (passive)', "Beasts and fey you summon with a conjuration spell regain HP equal to half their max HP when they end their turn with 1+ HP near you."),
        ('Druid','Faithful Summons'): ('Passive', 'Faithful Summons (passive)', "If you're reduced to 0 HP or incapacitated, automatically and instantly cast Conjure Animals to summon protective spirits. 1/LR."),
        ('Druid','Halo of Spores'):  ('Reaction', 'Halo of Spores', "When a creature you can see moves into or starts its turn within 10 ft of you, deal necrotic damage to it (CON save negates) — 1d4 (1d6 at 6th, 1d8 at 10th, 1d10 at 14th)."),
        ('Druid','Symbiotic Entity'): ('Bonus Action', 'Symbiotic Entity', "Expend a Wild Shape use to gain temp HP (4x Druid level) and boost your Halo of Spores' damage die and unarmed strike damage for 10 minutes."),
        ('Druid','Fungal Infestation'): ('Reaction', 'Fungal Infestation', "When a Small or Medium beast or humanoid dies within 10 ft, animate it as a zombie with 1 HP under your control (only the Attack action, acts right after you) for 1 hour. Uses = WIS modifier (min 1) per long rest."),
        ('Druid','Spreading Spores'): ('Bonus Action', 'Spreading Spores', "While Symbiotic Entity is active: hurl spores up to 30 ft into a 10-ft cube for 1 minute. Creatures that move into it or start their turn there take your Halo of Spores damage (CON save negates, once per turn each). You can't use your Halo of Spores reaction while the cube persists."),
        ('Druid','Spreading Spores (Improved)'): ('Passive', 'Spreading Spores (Improved) (passive)', "Halo of Spores' damage die increases further, and Spreading Spores' range extends."),
        ('Druid','Star Map'):        ('Passive', 'Star Map (passive)', "Gain a star chart focus usable as a spellcasting focus, granting +5 ft to Guidance/Guiding Bolt-style range and letting you cast Guidance at will."),
        ('Druid','Starry Form'):     ('Bonus Action', 'Starry Form', "Expend a Wild Shape use: assume a starry form for 10 minutes, choosing Archer (bonus action ranged spell attack, 1d8+WIS radiant), Chalice (when you cast a healing spell with a slot, you or an ally within 30 ft also heals 1d8+WIS), or Dragon (treat a 9 or lower as a 10 on INT/WIS checks or CON concentration saves)."),
        ('Druid','Cosmic Omen'):     ('Reaction', 'Cosmic Omen', "Roll a die after a long rest (Weal or Woe); use your reaction to add or subtract it from a creature's roll near you, once per short/long rest."),
        ('Druid','Twinkling Constellations'): ('Passive', 'Twinkling Constellations (passive)', "Starry Form's benefits improve: Archer's and Chalice's dice become 2d8, and Dragon grants a 20 ft flying speed with hover. You can freely change which constellation is active at the start of each of your turns."),
        ('Druid',"Nature's Ward"): ('Passive', "Nature's Ward (passive)", "Can't be charmed or frightened by elementals or fey. Immune to poison damage and the poisoned condition, and to disease."),
        ('Druid','Full of Stars'):   ('Passive', 'Full of Stars (passive)', "While in Starry Form, gain resistance to bludgeoning, piercing, and slashing damage."),
        ('Druid','Summon Wildfire Spirit'): ('Action', 'Summon Wildfire Spirit', "Expend one Wild Shape use to summon a wildfire spirit in an unoccupied space within 30 ft: each other creature within 10 ft of it makes a DEX save or takes 2d6 fire damage. Lasts 1 hour; acts right after you in initiative; command it with a bonus action."),
        ('Druid','Enhanced Bond'):   ('Passive', 'Enhanced Bond (passive)', "While your wildfire spirit is summoned: casting a spell that deals fire damage or restores HP adds 1d8 to one roll of it. Also, spells with a range other than self can instead originate from your spirit's location."),
        ('Druid','Cauterizing Flames'): ('Reaction', 'Cauterizing Flames', "When a Small+ creature dies within 30 ft of you or your spirit, a flame lingers in its space for 1 min. When a creature enters that space, use your reaction to extinguish it and heal or damage that creature for 2d10 + WIS modifier."),
        ('Druid','Blazing Revival'): ('Passive', 'Blazing Revival (passive)', "If you're reduced to 0 HP while your wildfire spirit is present, it can sacrifice itself to heal you instead. 1/LR."),
        ('Bard','Bardic Inspiration'):('Bonus Action','Bardic Inspiration','Give ally within 60 ft a Bardic Inspiration die (d6→d12 by level). 1/SR or CHA mod/LR.'),
        ('Bard','Song of Rest'):       ('Passive',     'Song of Rest (passive)','Allies who hear your performance during SR regain extra HP (d6→d12 by level).'),
        ('Bard','Countercharm'):       ('Action',      'Countercharm','Performance: allies within 30 ft have adv on fear/charm saves while you perform.'),
        ('Bard','Jack of All Trades'): ('Passive', 'Jack of All Trades (passive)',
            "Add half your proficiency bonus (rounded down) to any ability check that doesn't "
            "already include your proficiency bonus."),
        ('Bard','Expertise'): ('Passive', 'Expertise (passive)',
            "Double proficiency bonus for 2 chosen skill proficiencies (4 more at 10th level)."),
        ('Bard','Font of Inspiration'): ('Passive', 'Font of Inspiration (passive)',
            "Bardic Inspiration now recharges on a short OR long rest, instead of long rest only."),
        ('Bard','Magical Secrets'): ('Passive', 'Magical Secrets (passive)',
            "Learn 2 spells from any class's spell list (2 more each at 14th and 18th level); "
            "they count as Bard spells for you."),
        ('Bard','Bonus Proficiencies (Lore Bard)'): ('Passive', 'Bonus Proficiencies (passive)',
            "Proficiency in 3 skills of your choice."),
        ('Bard','Additional Magical Secrets'): ('Passive', 'Additional Magical Secrets (passive)',
            "Learn 2 more spells from any class's spell list."),
        ('Bard','Guidance of the Spirits'): ('Passive', 'Guidance of the Spirits (passive)',
            "Proficiency in a chosen skill; cast Guidance at will using that skill's ability. "
            "Swappable on a long rest."),
        ('Bard','Spirit Session'): ('Action', 'Spirit Session',
            "Commune with spirits for a d6 Spirit Tale Die (heal/damage/status, story-dependent). "
            "Uses = proficiency bonus per long rest."),
        ('Bard','Bonus Proficiencies (Swords)'): ('Passive', 'Bonus Proficiencies (passive)',
            "Proficiency with medium armor, shields, and scimitars."),
        ('Bard','Fighting Style (Swords)'): ('Passive', 'Fighting Style (passive)',
            "Choose Dueling or Two-Weapon Fighting."),
        ('Bard','Bonus Proficiencies (Valor Bard)'): ('Passive', 'Bonus Proficiencies (passive)',
            "Proficiency with medium armor, shields, and martial weapons."),
        ('Bard','Extra Attack'): ('Passive', 'Extra Attack (passive)',
            "Attack twice, instead of once, whenever you take the Attack action on your turn."),
        ('Bard','Superior Inspiration'): ('Passive', 'Superior Inspiration (passive)', "When you roll initiative and have no Bardic Inspiration uses left, regain 1 use."),
        ('Bard','Cutting Words'): ('Reaction', 'Cutting Words', "When a creature you can see within 60 ft makes an attack roll, ability check, or damage roll, expend a Bardic Inspiration die and subtract it from that roll."),
        ('Bard','Peerless Skill'): ('Reaction', 'Peerless Skill', "When you make an ability check, expend a Bardic Inspiration die and add it to the roll."),
        ('Bard','Combat Inspiration'): ('Passive', 'Combat Inspiration (passive)', "A creature with your Bardic Inspiration die can add it to a weapon damage roll, or use its reaction to add it to AC against an attack."),
        ('Bard','Battle Magic'): ('Passive', 'Battle Magic (passive)', "When you cast a spell as an action, you can make a weapon attack as a bonus action."),
        ('Bard','Blade Flourish'): ('Passive', 'Blade Flourish (passive)', "When you take the Attack action, your walking speed increases by 10 ft. On a hit, expend a Bardic Inspiration die for a Flourish: Defensive, Slashing, or Mobile."),
        ('Bard',"Master's Flourish"): ('Passive', "Master's Flourish (passive)", "Use a rolled d6 for Blade Flourishes instead of expending a Bardic Inspiration die."),
        ('Bard','Mote of Potential'): ('Passive', 'Mote of Potential (passive)', "Bardic Inspiration dice you give out become Motes of Potential — the recipient rolls twice and takes the better result, or you can spend them for other creation effects."),
        ('Bard','Performance of Creation'): ('Action', 'Performance of Creation', "Expend Bardic Inspiration and perform for 1 minute to conjure a nonmagical object worth no more than 20 gp x your Bard level (can't be Large until 6th, Huge until 14th). Lasts hours = proficiency bonus. Once per long rest free; reuse with a 2nd-level+ spell slot."),
        ('Bard','Animating Performance'): ('Action', 'Animating Performance', "Target a Large or smaller nonmagical object within 30 ft and animate it as a temporary ally for 1 hour. Command it with a bonus action alongside Bardic Inspiration. Only one at a time; reuse by spending a 3rd-level+ spell slot."),
        ('Bard','Creative Crescendo'): ('Passive', 'Creative Crescendo (passive)', "You can have a number of animated objects from Animating Performance equal to your CHA modifier at once (only one can be Large, the rest Small or smaller)."),
        ('Bard','Silver Tongue'): ('Passive', 'Silver Tongue (passive)', "On a CHA (Persuasion) or CHA (Deception) check, treat a d20 roll of 9 or lower as a 10, before adding modifiers."),
        ('Bard','Unsettling Words'): ('Bonus Action', 'Unsettling Words', "Expend a Bardic Inspiration die: a creature you can see within 60 ft subtracts the die roll from its next saving throw before the start of your next turn."),
        ('Bard','Unfailing Inspiration'): ('Passive', 'Unfailing Inspiration (passive)', "When a creature adds your Bardic Inspiration die to a failed roll, it keeps the die instead of losing it."),
        ('Bard','Universal Speech'): ('Action', 'Universal Speech', "Up to CHA modifier (min 1) creatures within 60 ft magically understand you for 1 hour, regardless of language. 1/LR, or again by spending a spell slot."),
        ('Bard','Infectious Inspiration'): ('Reaction', 'Infectious Inspiration', "When a creature within 60 ft succeeds using your Bardic Inspiration die, use your reaction to give a Bardic Inspiration die (no use expended) to a different creature within 60 ft."),
        ('Bard','Mantle of Inspiration'): ('Bonus Action', 'Mantle of Inspiration', "Instead of a normal Bardic Inspiration, grant proficiency-bonus allies up to 5 temp HP each (scales higher by level) and let each move up to their speed without provoking opportunity attacks."),
        ('Bard','Enthralling Performance'): ('Action', 'Enthralling Performance', "Perform for 1 minute: up to CHA mod humanoids who watched become charmed by you for 1 hour (WIS save)."),
        ('Bard','Mantle of Majesty'): ('Bonus Action', 'Mantle of Majesty', "Cast Command without a spell slot, then again as a bonus action each turn for 1 minute. 1/LR."),
        ('Bard','Unbreakable Majesty'): ('Bonus Action', 'Unbreakable Majesty', "For 1 minute, a creature that attacks you must succeed on a CHA save or choose a new target. 1/SR."),
        ('Bard','Mystic Chronicle'): ('Action', 'Mystic Chronicle', "Spend 1 minute weaving a longer tale to duplicate a spell of 5th level or lower without a spell slot. 1/LR."),
        ('Bard','Awakened Spirit'): ('Passive', 'Awakened Spirit (passive)', "Your Spirit Tale Die becomes a d12. Once per turn when you deal damage with a spell, you can also apply a Spirit Tale Die effect."),
        ('Bard','Psychic Blades (Whispers)'): ('Passive', 'Psychic Blades (passive)', "When you hit with a weapon attack, expend a Bardic Inspiration die to deal extra 2d6 psychic damage (scales higher by level), if you can perceive the target's mind."),
        ('Bard','Words of Terror'): ('Action', 'Words of Terror', "Spend 1 minute talking with a humanoid: WIS save or it becomes frightened of you (or a creature of your choice) for 1 hour or until it takes damage."),
        ('Bard','Mantle of Whispers'): ('Passive', 'Mantle of Whispers (passive)', "When a humanoid dies within 30 ft, capture its shadow and later assume its appearance and mannerisms (not memories or voice) for as long as you wish."),
        ('Bard','Shadow Lore'): ('Action', 'Shadow Lore', "Whisper to a creature for 1 minute: WIS save or it's charmed for 8 hours, believes a lie you tell it, and forgets the conversation. 1/LR."),
        ('Wizard','Bladesong'):       ('Bonus Action', 'Bladesong', "While lightly armored/unarmored and wielding a one-handed weapon with a free hand: +INT mod AC (implemented), +10 ft speed (implemented), advantage on Acrobatics checks, and an extra bonus to concentration saves, for 1 minute. Uses = INT mod per long rest."),
        ('Wizard','Extra Attack'): ('Passive', 'Extra Attack (passive)',
            "Attack twice, instead of once, whenever you take the Attack action on your turn. You "
            "can cast one of your cantrips in place of one of those attacks."),
        ('Wizard','Abjuration Savant'): ('Passive', 'Abjuration Savant (passive)', "The gold and time you must spend to copy an Abjuration spell into your spellbook is halved."),
        ('Wizard','Conjuration Savant'): ('Passive', 'Conjuration Savant (passive)', "The gold and time you must spend to copy a Conjuration spell into your spellbook is halved."),
        ('Wizard','Divination Savant'): ('Passive', 'Divination Savant (passive)', "The gold and time you must spend to copy a Divination spell into your spellbook is halved."),
        ('Wizard','Enchantment Savant'): ('Passive', 'Enchantment Savant (passive)', "The gold and time you must spend to copy an Enchantment spell into your spellbook is halved."),
        ('Wizard','Evocation Savant'): ('Passive', 'Evocation Savant (passive)', "The gold and time you must spend to copy an Evocation spell into your spellbook is halved."),
        ('Wizard','Sculpt Spells'): ('Passive', 'Sculpt Spells (passive)',
            "When you cast an Evocation spell that affects other creatures you can see, you can "
            "choose a number of them equal to 1 + the spell's level — they automatically succeed on "
            "their save and take no damage if they'd normally take half on a success."),
        ('Wizard','Illusion Savant'): ('Passive', 'Illusion Savant (passive)', "The gold and time you must spend to copy an Illusion spell into your spellbook is halved."),
        ('Wizard','Necromancy Savant'): ('Passive', 'Necromancy Savant (passive)', "The gold and time you must spend to copy a Necromancy spell into your spellbook is halved."),
        ('Wizard','Transmutation Savant'): ('Passive', 'Transmutation Savant (passive)', "The gold and time you must spend to copy a Transmutation spell into your spellbook is halved."),
        ('Wizard','Training in War and Song'): ('Passive', 'Training in War and Song (passive)',
            "Proficiency with light armor and one type of one-handed melee weapon. Proficiency in "
            "the Performance skill."),
        ('Wizard','Song of Defense'): ('Reaction', 'Song of Defense',
            "While Bladesong is active, expend a spell slot to reduce damage you'd take by 5 × the "
            "slot's level."),
        ('Wizard','Song of Victory'): ('Passive', 'Song of Victory (passive)',
            "While Bladesong is active, add your INT modifier to weapon damage rolls."),
        ('Wizard','Extra Attack (Bladesinging)'): ('Action', 'Extra Attack (Bladesinging)', "Attack twice instead of once when you take the Attack action. You can cast one of your cantrips in place of one of those attacks."),
        ('Wizard','Arcane Ward'):     ('Passive', 'Arcane Ward (passive)', "Absorbs damage before it reaches your HP (implemented as a pool). Recharges when you cast an Abjuration spell of 1st level or higher, by twice that spell's level — not on a rest, so adjust the pool manually when that happens."),
        ('Wizard','Projected Ward'):  ('Reaction', 'Projected Ward', "Use your reaction to protect a creature within 30 ft with your Arcane Ward, absorbing the damage instead."),
        ('Wizard','Improved Abjuration'): ('Passive', 'Improved Abjuration (passive)', "Add your proficiency bonus to the effectiveness of certain Abjuration spells (Alarm, Arcane Lock, Banishment, etc.) that don't already use it."),
        ('Wizard','Spell Resistance'): ('Passive', 'Spell Resistance (passive)', "Advantage on saving throws against spells, and resistance to damage from spells."),
        ('Wizard','Minor Conjuration'): ('Action', 'Minor Conjuration', "Conjure a nonmagical object (up to 3 ft on a side, 10 lbs) in your hand or on the ground within 10 ft. Lasts 1 hour or until dismissed."),
        ('Wizard','Benign Transposition'): ('Action', 'Benign Transposition', "Teleport up to 30 ft to an unoccupied space you can see, or swap places with a willing Small/Medium creature summoned by one of your conjuration spells. 1/LR, or again by expending a spell slot."),
        ('Wizard','Focused Conjuration'): ('Passive', 'Focused Conjuration (passive)', "Your concentration on a conjuration spell can't be broken by taking damage."),
        ('Wizard','Durable Summons'): ('Passive', 'Durable Summons (passive)', "Any creature you summon or create with a conjuration spell gains 30 temporary HP."),
        ('Wizard','Portent'):        ('Reaction', 'Portent', "Roll 2 (3 at 14th) d20s after a long rest; replace any attack roll, saving throw, or ability check with one of these dice instead of rolling."),
        ('Wizard','Expert Divination'): ('Passive', 'Expert Divination (passive)', "When you cast a divination spell of 2nd level or higher using a spell slot, regain one expended spell slot of a lower level (max 5th)."),
        ('Wizard','The Third Eye'):  ('Action', 'The Third Eye', "Gain one at will: darkvision 60 ft, read any language, see invisible creatures/objects within 10 ft, or see the true form of a shapechanged/polymorphed/transmuted creature within 10 ft."),
        ('Wizard','Greater Portent'): ('Passive', 'Greater Portent (passive)', "Your Portent dice pool increases to 3 (implemented)."),
        ('Wizard','Hypnotic Gaze'):  ('Action', 'Hypnotic Gaze', "Fix a creature within 5 ft with your gaze: if it can see/hear you, WIS save or it's charmed until the end of your next turn (speed 0, incapacitated). Ends early if you move away, it can't see/hear you, or it takes damage. Once resolved, can't reuse on that creature until a long rest."),
        ('Wizard','Instinctive Charm'): ('Reaction', 'Instinctive Charm', "When a creature you can see within 30 ft targets you with an attack, redirect it (WIS save) to the nearest other creature."),
        ('Wizard','Split Enchantment'): ('Passive', 'Split Enchantment (passive)', "When you cast an enchantment spell targeting only one creature, you can target a second creature with it."),
        ('Wizard','Alter Memories'): ('Action', 'Alter Memories', "When you charm a creature, make it unaware it was charmed, and can erase up to 24 hours of its memories."),
        ('Wizard','Potent Cantrip'): ('Passive', 'Potent Cantrip (passive)', "When a creature succeeds on a save against your cantrip, it still takes half damage (if the cantrip deals damage), instead of none."),
        ('Wizard','Empowered Evocation'): ('Passive', 'Empowered Evocation (passive)', "Add your INT modifier to the damage of one Evocation spell you cast."),
        ('Wizard','Overchannel'):    ('Passive', 'Overchannel (passive)', "Deal maximum damage with a 1st-5th level damage spell instead of rolling. Repeated use before a long rest deals necrotic damage to you, increasing each time."),
        ('Wizard','Improved Minor Illusion'): ('Passive', 'Improved Minor Illusion (passive)', "Your Minor Illusion cantrip can create both a sound and an image with the same casting. Learn Minor Illusion if you don't know it."),
        ('Wizard','Malleable Illusions'): ('Passive', 'Malleable Illusions (passive)', "Change the nature of an illusion you've cast (that has a duration of 1 minute or longer) as an action."),
        ('Wizard','Illusory Self'):  ('Reaction', 'Illusory Self', "When a creature hits you with an attack, interpose an illusory duplicate to cause the attack to miss automatically. 1/SR or LR."),
        ('Wizard','Illusory Reality'): ('Bonus Action', 'Illusory Reality', "Make one inanimate, illusory object created by an illusion spell you cast briefly real and physically interactive for 1 minute."),
        ('Wizard','Grim Harvest'):   ('Passive', 'Grim Harvest (passive)', "Once per turn when you kill a creature with a spell, regain HP equal to twice the spell's level (thrice if Necromancy)."),
        ('Wizard','Undead Thralls'): ('Passive', 'Undead Thralls (passive)', "Animate Dead is added to your spellbook for free if you don't have it, and targets one extra corpse/pile of bones. Any undead you create with a necromancy spell gets +Wizard level HP max and +proficiency bonus to its weapon damage rolls."),
        ('Wizard','Inured to Undeath'): ('Passive', 'Inured to Undeath (passive)', "Resistance to necrotic damage, and your hit point maximum can't be reduced."),
        ('Wizard','Command Undead'): ('Action', 'Command Undead', "Prerequisite: 14th level. Choose one undead you can see within 60 ft; it makes a CHA save against your Wizard spell save DC. On a failure, it becomes friendly to you and obeys your commands until you use this again (on it or another target). On a success, you can't use this on it again. Undead with INT 8+ have advantage on the save; if INT 12+ and it fails, it can repeat the save every hour until it succeeds and breaks free."),
        ('Wizard','Minor Alchemy'):  ('Action', 'Minor Alchemy', "Transform one nonmagical object of one material into another material for up to 1 hour."),
        ("Wizard","Transmuters Stone"): ('Bonus Action', "Transmuter's Stone", "Create a stone granting darkvision, +10 ft speed, proficiency in CON saves, or resistance to one damage type, to whoever holds it. Can change the benefit when you cast a Transmutation spell."),
        ('Wizard','Shapechanger'):   ('Action', 'Shapechanger', "Cast Polymorph on yourself without a spell slot, gaining the option to transform into a CR-1 beast. 1/SR or LR."),
        ('Wizard','Master Transmuter'): ('Action', 'Master Transmuter', "Destroy your Transmuter's Stone for one of several powerful effects: remove a curse/disease/poison, restore youth, or reduce a creature's age."),
        ('Wizard','Chronal Shift'):  ('Reaction', 'Chronal Shift', "Force a creature to reroll an attack roll, ability check, or saving throw. Uses = 2 per long rest."),
        ('Wizard','Temporal Awareness'): ('Passive', 'Temporal Awareness (passive)', "Add your INT modifier to your initiative rolls."),
        ('Wizard','Momentary Stasis'): ('Action', 'Momentary Stasis', "Force a Large or smaller creature within 60 ft to make a CON save or be encased (incapacitated, speed 0) until the end of your next turn or until it takes damage. Uses = INT mod (min 1) per long rest."),
        ('Wizard','Arcane Abeyance'): ('Passive', 'Arcane Abeyance (passive)', "Store a spell of 3rd level or lower in an object, to be released later when triggered."),
        ('Wizard','Convergent Future'): ('Reaction', 'Convergent Future', "Declare the outcome of a roll you can see before it's made, then spend a Chronal Shift use to force that outcome to happen. 1/LR."),
        ('Wizard','Adjust Density'): ('Action', 'Adjust Density', "Halve or double the weight of a Large or smaller (Huge+ at 10th) object/creature within 30 ft for 1 min or until you lose concentration. Halved: +10 ft speed, jumps twice as far, disadvantage on STR checks/saves. Doubled: -10 ft speed, advantage on STR checks/saves."),
        ('Wizard','Gravity Well'):   ('Passive', 'Gravity Well (passive)', "Whenever you cast a spell on a creature and it's willing to move, is hit by the spell's attack roll, or fails its save against the spell — move that target 5 ft to an unoccupied space of your choice."),
        ('Wizard','Violent Attraction'): ('Passive', 'Violent Attraction (passive)', "Increase the damage of a spell that deals bludgeoning, force, piercing, or slashing damage."),
        ('Wizard','Event Horizon'):  ('Action', 'Event Horizon', "Create a localized gravitational field for 1 minute: creatures within 15 ft are pulled toward its center at the start of each of their turns."),
        ('Wizard','Gravity Fissure'): ('Action', 'Gravity Fissure', "Create a line of intense gravity: creatures in it take force damage and are pulled toward its center. 1/LR or via a spell slot."),
        ('Wizard','Wizardly Quill'): ('Passive', 'Wizardly Quill (passive)', "Gain a magic quill (bonus action to create): needs no ink (any color you choose), copies spells into your spellbook in just 2 min/spell level if used, and can erase its own writing within 5 ft as a bonus action."),
        ('Wizard','Awakened Spellbook'): ('Passive', 'Awakened Spellbook (passive)', "While holding your spellbook: use it as a spellcasting focus; when you cast a spell with a spell slot, temporarily change its damage type to one from another spell in the book of the same level; and cast a ritual spell at its normal casting time instead of +10 minutes, once per long rest."),
        ('Wizard','Manifest Mind'):  ('Bonus Action', 'Manifest Mind', "Manifest an invisible, sensor-like mind within 60 ft that you can perceive and cast spells through for 1 hour. Uses = INT mod per long rest."),
        ('Wizard','Master Scrivener'): ('Action', 'Master Scrivener', "Inscribe a temporary spell scroll of a spell in your spellbook, usable by anyone who can cast spells, lasting until your next long rest."),
        ('Wizard','One with the Word'): ('Reaction', 'One with the Word', "Reduce the damage of a spell you or an ally within 60 ft is targeted by, at the cost of a spell slot from your own spellbook-linked pool."),
        ('Wizard','Arcane Deflection'): ('Reaction', 'Arcane Deflection', "Gain +2 AC against one attack, or +4 to one saving throw, but can't cast a spell (other than cantrips) on your next turn."),
        ('Wizard','Tactical Wit'):   ('Passive', 'Tactical Wit (passive)', "Add your INT modifier to your initiative rolls."),
        ('Wizard','Power Surge'):    ('Passive', 'Power Surge (passive)', "Store excess magical energy when you don't cast a leveled spell on your turn, up to a max, then release it to add damage to a later spell."),
        ('Wizard','Durable Magic'):  ('Passive', 'Durable Magic (passive)', "While concentrating on a spell, gain +2 AC and +2 to all saving throws."),
        ('Wizard','Deflecting Shroud'): ('Reaction', 'Deflecting Shroud', "When you take damage, deal force damage equal to your INT modifier to up to 3 creatures within 60 ft that you can see."),
        ('Cleric','Channel Divinity'): ('Action',      'Channel Divinity','Use one Channel Divinity option. 1/SR (2/SR at 6, 3/SR at 18).'),
        ('Cleric','Disciple of Life'): ('Passive', 'Disciple of Life (passive)', "Healing spells you cast of 1st level or higher restore additional HP equal to 2 + the spell's level."),
        ('Cleric','Preserve Life'):    ('Action',      'Preserve Life (Channel Divinity)','Distribute healing equal to 5 × Cleric level among creatures in 30 ft (≤ half their max HP).'),
        ('Cleric','Blessed Healer'): ('Passive', 'Blessed Healer (passive)', "When you cast a healing spell of 1st level or higher on another creature, you also regain HP equal to 2 + the spell's level."),
        ('Cleric','Divine Strike'): ('Passive', 'Divine Strike (passive)', "Once per turn, deal an extra 1d8 damage of your domain's associated type on a weapon hit (2d8 at 14th level)."),
        ('Cleric','Reaper'): ('Passive', 'Reaper (passive)', "Learn one necromancy cantrip of your choice. Necromancy cantrips that normally target only one creature can instead target two creatures within range and within 5 ft of each other."),
        ('Cleric','Touch of Death'):   ('Passive', 'Touch of Death (Channel Divinity, passive)', "When you hit a creature with a melee attack, use Channel Divinity to deal extra necrotic damage equal to 5 + twice your Cleric level."),
        ('Cleric','Inescapable Destruction'): ('Passive', 'Inescapable Destruction (passive)', "Necrotic damage from your Channel Divinity or spells ignores resistance to necrotic damage."),
        ('Cleric','Improved Reaper'): ('Passive', 'Improved Reaper (passive)', "Reaper now also applies to necromancy spells that target only one creature — they can target two creatures within range instead."),
        ('Cleric','Turn Undead'):      ('Action',      'Turn Undead (Channel Divinity)','Undead within 30 ft must make WIS save or be turned for 1 minute. Destroys low-CR undead.'),
        ('Sorcerer','Metamagic'):      ('Passive',     'Metamagic (passive)','Spend Sorcery Points to apply metamagic options to spells as you cast them.'),
        ('Sorcerer','Flexible Casting'):('Bonus Action','Flexible Casting','Convert spell slots ↔ Sorcery Points (1 SP per slot level to convert a slot to points; 2/3/5/6/7 SP to create a 1st/2nd/3rd/4th/5th-level slot).'),
        ('Sorcerer','Dragon Ancestor'): ('Passive', 'Dragon Ancestor (passive)',
            "Choose a draconic ancestry (color), setting your damage type for later features. Learn "
            "Draconic. Your proficiency bonus is doubled on CHA checks interacting with dragons."),
        ('Sorcerer','Draconic Resilience'): ('Passive', 'Draconic Resilience (passive)',
            "+1 HP per Sorcerer level. AC = 13 + DEX modifier when you aren't wearing armor."),
        ('Sorcerer','Dragon Wings'): ('Bonus Action', 'Dragon Wings',
            "Grow draconic wings, gaining a flying speed equal to your current speed, until you "
            "dismiss them as a bonus action. Can't manifest while wearing armor not made to "
            "accommodate them; unaccommodating clothing may be destroyed."),
        ('Sorcerer','Wild Magic Surge'): ('Passive', 'Wild Magic Surge (passive)',
            "After you cast a Sorcerer spell of 1st level or higher, the DM can have you roll a d20; "
            "on a 1, roll on the Wild Magic Surge table for a random magical effect."),
        ('Sorcerer','Tides of Chaos'): ('Bonus Action', 'Tides of Chaos',
            "Gain advantage on one attack roll, ability check, or saving throw. Once used, the DM can "
            "have you roll on the Wild Magic Surge table the next time you cast a Sorcerer spell "
            "before you finish a long rest."),
        ('Sorcerer','Bend Luck'): ('Reaction', 'Bend Luck',
            "When another creature you can see makes an attack roll, ability check, or save: spend "
            "2 sorcery points to roll 1d4 and apply it as a bonus or penalty (your choice) to their "
            "roll, after it's rolled but before the outcome is known."),
        ('Sorcerer','Controlled Chaos'): ('Passive', 'Controlled Chaos (passive)',
            "Whenever you roll on the Wild Magic Surge table, roll twice and use either result."),
        ('Sorcerer','Psionic Spells'): ('Passive', 'Psionic Spells (passive)',
            "Cast your Sorcerer spells with no verbal or somatic components."),
        ('Sorcerer','Psychic Defenses'): ('Passive', 'Psychic Defenses (passive)',
            "Resistance to psychic damage. Advantage on saves against being charmed or frightened."),
        ('Sorcerer','Otherworldly Wings'): ('Bonus Action', 'Otherworldly Wings',
            "Manifest spectral wings for 10 minutes, gaining a flying speed equal to your current "
            "speed. Uses = proficiency bonus per long rest."),
        ('Sorcerer','Wind Speaker'): ('Passive', 'Wind Speaker (passive)',
            "Speak, read, and write Primordial and its dialects (Auran, Aquan, Ignan, Terran)."),
        ('Sorcerer','Storm Guide'): ('Action', 'Storm Guide',
            "If it's raining: stop rain in a 20-ft. radius around you (bonus action to end early). "
            "If it's windy: bonus action each round to choose the wind's direction in a 100-ft. "
            "radius (doesn't change its speed)."),
        ('Sorcerer','Heart of the Storm'): ('Passive', 'Heart of the Storm (passive)',
            "Resistance to lightning and thunder damage. Whenever you start casting a spell of 1st "
            "level or higher that deals lightning or thunder damage, creatures of your choice "
            "within 10 ft. of you (not you) take lightning or thunder damage equal to half your "
            "Sorcerer level."),
        ('Sorcerer',"Storm's Fury"): ('Reaction', "Storm's Fury",
            "When hit by a melee attack: deal lightning damage to the attacker equal to your "
            "Sorcerer level. STR save (your spell save DC) or they're pushed up to 20 ft. away."),
        ('Sorcerer','Wind Soul'): ('Action', 'Wind Soul',
            "Resistance to lightning and thunder damage (permanent). Flying speed of 60 ft. As an "
            "action, grant a flying speed of 30 ft. for 1 hour to a number of other creatures equal "
            "to your CHA modifier (min 1). 1/long rest."),
        ('Sorcerer','Elemental Affinity'): ('Passive', 'Elemental Affinity (passive)', "Resistance to your Dragon Ancestor's damage type is implemented. Additionally: when you cast a spell dealing damage of that type, add your CHA modifier to one damage roll of that spell."),
        ('Sorcerer','Draconic Presence'): ('Action', 'Draconic Presence',
            "Spend 5 sorcery points: exude an aura of awe or fear (your choice) to 60 ft. for 1 "
            "minute or until you lose concentration. Each hostile creature that starts its turn in "
            "it must succeed on a WIS save or be charmed (awe) or frightened (fear) until the aura "
            "ends; a success grants 24-hour immunity to this aura."),
        ('Sorcerer','Draconic Presence'): ('Action', 'Draconic Presence', "Spend 5 sorcery points to emanate awe or fear for 1 minute: each creature of your choice within 60 ft must WIS save or be charmed/frightened by you."),
        ('Sorcerer','Bend Luck'):    ('Reaction', 'Bend Luck', "Spend 2 sorcery points to roll 1d4 and apply it as a bonus or penalty to another creature's attack roll, ability check, or saving throw."),
        ('Sorcerer','Controlled Chaos'): ('Passive', 'Controlled Chaos (passive)', "When you roll on the Wild Magic Surge table, roll twice and choose either result."),
        ('Sorcerer','Spell Bombardment'): ('Passive', 'Spell Bombardment (passive)', "When you roll damage for a spell and roll the highest number on any die, roll that die again and add it as extra damage of the same type. Once per turn."),
        ('Sorcerer','Tempestuous Magic'): ('Bonus Action', 'Tempestuous Magic', "Before or after casting a spell of 1st level or higher, fly up to 10 ft without provoking opportunity attacks."),
        ('Sorcerer','Divine Magic'): ('Passive', 'Divine Magic (passive)', "Choose an alignment-appropriate Cleric spell list; you can pick your Sorcerer spells known from either the Sorcerer list or that Cleric list."),
        ('Sorcerer','Favored by the Gods'): ('Reaction', 'Favored by the Gods', "Add 2d4 to a failed saving throw or missed attack roll, possibly turning it into a success. 1/SR or LR."),
        ('Sorcerer','Empowered Healing'): ('Passive', 'Empowered Healing (passive)', "Once per turn, when you or an ally within range would roll dice to restore HP, spend 1 sorcery point to reroll any number of those dice."),
        ('Sorcerer','Unearthly Recovery'): ('Bonus Action', 'Unearthly Recovery', "When below half HP, regain HP equal to half your HP maximum. 1/LR."),
        ('Sorcerer','Telepathic Speech'): ('Passive', 'Telepathic Speech (passive)', "Form a telepathic connection with a creature you can see within 30 ft, letting you speak mind-to-mind for the rest of the encounter or 1 hour."),
        ('Sorcerer','Psionic Sorcery'): ('Passive', 'Psionic Sorcery (passive)', "Cast certain spells (Psionic Spells list) using sorcery points instead of a spell slot, without verbal or somatic components."),
        ('Sorcerer','Revelation in Flesh'): ('Bonus Action', 'Revelation in Flesh', "Manifest your psionic potential: gain a swim/climb/fly speed equal to your walking speed, or become invisible, for 10 minutes. Uses = proficiency bonus per long rest."),
        ('Sorcerer','Warping Implosion'): ('Action', 'Warping Implosion', "Spend 3 sorcery points to create a localized spatial rift: teleport up to 60 ft, then creatures near your departure point take force damage and are pulled toward it. 1/LR or 3 sorcery points."),
        ('Sorcerer','Clockwork Magic'): ('Passive', 'Clockwork Magic (passive)', "Learn Aid, Alarm, Detect Magic, Protection from Evil and Good, Sanctuary, or Summon Construct at certain levels without spending them as spells known."),
        ('Sorcerer','Restore Balance'): ('Reaction', 'Restore Balance', "When a creature within 60 ft would gain advantage or disadvantage on a roll, negate that advantage/disadvantage. Uses = proficiency bonus per long rest."),
        ('Sorcerer','Bastion of Law'): ('Action', 'Bastion of Law', "Spend 5+ sorcery points to grant allies within 30 ft temp HP and other defensive benefits for 1 minute, scaling with points spent."),
        ('Sorcerer','Trance of Order'): ('Passive', 'Trance of Order (passive)', "While concentrating on a spell, you have advantage on ability checks and can't be surprised, plus one attack roll per turn against you can be treated as a 10 if lower."),
        ('Sorcerer','Clockwork Cavalcade'): ('Action', 'Clockwork Cavalcade', "Spend 7 sorcery points to restore HP, remove conditions, and repair objects in a 30-ft cube. 1/LR or 7 sorcery points."),
        ('Sorcerer','Lunar Embodiment'): ('Passive', 'Lunar Embodiment (passive)', "Your spells are empowered by moon phases, granting a Moulting die you spend for various minor bonus effects."),
        ('Sorcerer','Moon Fire'): ('Action', 'Moon Fire', "A ranged spell attack dealing radiant damage, scaling with your moon phase and Sorcerer level."),
        ('Sorcerer','Lunar Boons + Waxing and Waning'): ('Passive', 'Lunar Boons (passive)', "Gain an additional benefit tied to your current moon phase, changing over time."),
        ('Sorcerer','Lunar Empowerment'): ('Passive', 'Lunar Empowerment (passive)', "Your Moon Fire and lunar boons grow more powerful."),
        ('Sorcerer','Lunar Phenomenon'): ('Action', 'Lunar Phenomenon', "A powerful capstone effect tied to your moon phase, usable once per long rest."),
        ('Sorcerer','Eyes of the Dark'): ('Passive', 'Eyes of the Dark (passive)', "Gain darkvision to 120 ft. Starting at 3rd level, cast Darkness without a slot, and can see through it yourself as if it were dim light."),
        ('Sorcerer','Strength of the Grave'): ('Reaction', 'Strength of the Grave (passive)', "When damage would reduce you to 0 HP but not kill you outright, CHA save (DC 5 + damage taken) to drop to 1 HP instead. Once per short/long rest."),
        ('Sorcerer','Hound of Ill Omen'): ('Bonus Action', 'Hound of Ill Omen', "Spend 3 sorcery points to summon a spectral hound that hunts a creature you can see within 60 ft, attacking it and hampering its speed."),
        ('Sorcerer','Shadow Walk'): ('Bonus Action', 'Shadow Walk', "In dim light or darkness, teleport up to 120 ft to an unoccupied space you can see in dim light or darkness."),
        ('Sorcerer','Umbral Form'): ('Action', 'Umbral Form', "Spend 6 sorcery points to become a shadow for 1 minute: resistance to all damage except force/radiant (implemented), move through creatures/objects, no disadvantage in dim light/darkness."),
        # Eldritch Blast intentionally has NO KNOWN_ACTIONS entry — it's
        # handled by the spell-routing path below instead, which resolves
        # the actual current beam count (2/3/4 at levels 5/11/17) rather
        # than showing static, unresolved rule text. A KNOWN_ACTIONS entry
        # here used to create a confusing duplicate card.
        ('Warlock','Eldritch Master'): ('Action', 'Eldritch Master', "Spend 1 minute entreating your patron for aid to regain all expended Pact Magic slots. 1/LR."),
        ('Warlock','Mystic Arcanum (6th)'): ('Action', 'Mystic Arcanum (6th)', "Cast your chosen 6th-level spell once, without expending a spell slot. 1/LR."),
        ('Warlock','Mystic Arcanum (7th)'): ('Action', 'Mystic Arcanum (7th)', "Cast your chosen 7th-level spell once, without expending a spell slot. 1/LR."),
        ('Warlock','Mystic Arcanum (8th)'): ('Action', 'Mystic Arcanum (8th)', "Cast your chosen 8th-level spell once, without expending a spell slot. 1/LR."),
        ('Warlock','Mystic Arcanum (9th)'): ('Action', 'Mystic Arcanum (9th)', "Cast your chosen 9th-level spell once, without expending a spell slot. 1/LR."),
        ('Warlock','Fey Presence'): ('Action', 'Fey Presence', "Each creature in a 10-ft cube of you must WIS save or be charmed or frightened by you until the end of your next turn. 1/SR."),
        ('Warlock','Misty Escape'): ('Reaction', 'Misty Escape', "When you take damage, turn invisible and teleport up to 60 ft to an unoccupied space you can see. Invisibility ends if you attack, cast a spell, or the start of your next turn. 1/SR."),
        ('Warlock','Beguiling Defenses'): ('Reaction', 'Beguiling Defenses (passive/reaction)', "You're immune to being charmed. When a creature tries to charm you, you can use your reaction to turn the attempt back on it (WIS save) instead."),
        ('Warlock','Dark Delirium'): ('Action', 'Dark Delirium', "One creature within 60 ft: WIS save or be charmed or frightened by you for 1 minute, perceiving confused visions of another place. 1/SR."),
        ('Warlock','Gift of the Sea'): ('Passive', 'Gift of the Sea (passive)', "You have a swimming speed of 40 ft and can breathe underwater."),
        ('Warlock','Tentacle of the Deep'): ('Bonus Action', 'Tentacle of the Deep', "Summon a single 10-ft spectral tentacle within 60 ft for 1 minute (replaces any existing one). Melee spell attack against a creature within 10 ft of it: 1d8 cold damage (2d8 at 10th) and its speed is reduced by 10 ft. As a bonus action, move it 30 ft and attack again. Uses = proficiency bonus per long rest."),
        ('Warlock','Oceanic Soul'):   ('Passive', 'Oceanic Soul (passive)', "Resistance to cold damage. While you are fully submerged, any other fully-submerged creature can understand your speech, and you can understand theirs."),
        ('Warlock','Guardian Coil'): ('Reaction', 'Guardian Coil', "When a creature grappled by your Tentacle of the Deep is hit, use your reaction to have the tentacle absorb some of the damage."),
        ('Warlock','Grasping Tentacles'): ('Action', 'Grasping Tentacles', "Cast Evard's Black Tentacles once per long rest without a slot; casting it grants temp HP equal to your Warlock level and damage can't break your concentration on it."),
        ('Warlock','Fathomless Plunge'): ('Bonus Action', 'Fathomless Plunge', "Teleport yourself (and willing creatures within 10 ft) to an unoccupied space you can see within 60 ft, surrounded by a burst of water that damages nearby enemies."),
        ("Warlock","Dark One's Blessing"): ('Passive', "Dark One's Blessing (passive)", "When you reduce a hostile creature to 0 HP, gain temporary HP equal to your CHA modifier + your Warlock level (min 1)."),
        ('Warlock',"Dark One's Own Luck"): ('Bonus Action', "Dark One's Own Luck", "Add 1d10 to one ability check or saving throw you make. Can decide after seeing the roll but before the outcome. 1/SR."),
        ('Warlock',"Dark One's Own Luck"): ('Bonus Action', "Dark One's Own Luck", "Add 1d10 to one ability check or saving throw you make. Can decide after seeing the roll but before the outcome. 1/SR."),
        ('Warlock','Fiendish Resilience'): ('Passive', 'Fiendish Resilience (passive)', "Choose a damage type after a short or long rest: you have resistance to it until you choose a different type again (unless the source is magical or silvered weapons)."),
        ('Warlock','Hurl Through Hell'): ('Passive', 'Hurl Through Hell (passive)', "When you hit a creature with an attack, you can hurl it through the lower planes. It disappears and takes 10d10 psychic damage when it returns at the end of your next turn. 1/LR."),
        ("Warlock","Genie's Vessel"): ('Action', "Genie's Vessel", "Bottled Respite: as an action, you and up to 5 willing creatures can enter its extradimensional interior for up to 2x your proficiency bonus in hours. 1/LR."),
        ("Warlock","Genie's Wrath"):  ('Passive', "Genie's Wrath (passive)", "Once per turn when you hit with an attack, deal extra damage (type depends on your genie kind: bludgeoning/thunder/fire/cold) equal to your proficiency bonus."),
        ('Warlock',"Genie's Vessel"): ('Passive', "Genie's Vessel (passive)", "A magical vessel usable as a spellcasting focus. Bottled Respite: as an action, you and up to 5 willing creatures can enter its extradimensional interior (20-ft cylinder) for up to 2x your proficiency bonus in hours, once per long rest."),
        ('Warlock',"Genie's Wrath"): ('Passive', "Genie's Wrath (passive)", "Once per turn when you hit with an attack, deal extra damage (type depending on your genie kind: bludgeoning, thunder, fire, or cold) equal to your proficiency bonus."),
        ('Warlock','Elemental Gift'): ('Bonus Action', 'Elemental Gift', "Gain resistance to your genie kind's damage type (always on). As a bonus action, gain a flying speed of 30 ft for 10 minutes (can hover). Uses = proficiency bonus per long rest."),
        ('Warlock','Sanctuary Vessel'): ('Passive', 'Sanctuary Vessel (passive)', "While inside your Genie's Vessel, you and creatures you bring with you regain HP as if finishing a short rest. 1/LR."),
        ('Warlock','Limited Wish'):    ('Action', 'Limited Wish', "Request the effect of any 6th-level-or-lower spell with a 1-action casting time (any class's list, no restrictions) — it just happens. 1/1d4 long rests."),
        ('Warlock','Awakened Mind'):   ('Passive', 'Awakened Mind (passive)', "Telepathically communicate with a creature within 30 ft that you can see, in any language."),
        ('Warlock','Entropic Ward'):   ('Reaction', 'Entropic Ward', "When a creature attacks you, impose disadvantage on the roll. If it misses, gain advantage on your next attack against it. 1/SR."),
        ('Warlock','Thought Shield'):  ('Passive', 'Thought Shield (passive)', "Resistance to psychic damage. Your thoughts can't be read by telepathy unless you allow it. When you take psychic damage, the attacker takes the same amount."),
        ('Warlock','Create Thrall'):   ('Action', 'Create Thrall', "Charm an incapacitated humanoid — it remains charmed by you indefinitely, until a remove curse is cast on it."),
        ('Warlock','Hexblades Curse'): ('Bonus Action', "Hexblade's Curse", "Curse a creature within 30 ft for 1 minute: damage rolls against it get +proficiency bonus, attack rolls against it crit on 19-20, and if it dies while cursed you regain HP equal to your Warlock level + CHA mod (min 1). Can't use again until a short or long rest."),
        ('Warlock','Hex Warrior'):    ('Passive', 'Hex Warrior (passive)', "Proficiency with medium armor, shields, martial weapons (implemented). Use CHA instead of STR/DEX for a non-two-handed weapon's attacks (implemented)."),
        ('Warlock','Accursed Specter'): ('Passive', 'Accursed Specter (passive)', "When you slay a humanoid, you can bind its spirit into a spectral warrior that fights for you until your next long rest."),
        ('Warlock','Armor of Hexes'): ('Passive', 'Armor of Hexes (passive)', "While a creature is cursed by Hexblade's Curse, any attack it makes against you has a 50% chance to simply miss, regardless of its roll."),
        ('Warlock','Master of Hexes'): ('Bonus Action', 'Master of Hexes', "When the creature cursed by Hexblade's Curse dies, apply the curse to a new creature within 30 ft."),
        ('Warlock','Bonus Cantrips'): ('Passive', 'Bonus Cantrips (passive)', "Learn the Light and Sacred Flame cantrips; they don't count against your number of cantrips known."),
        ('Warlock','Healing Light'):  ('Bonus Action', 'Healing Light', "Spend up to your CHA modifier (min 1) dice from your healing pool (1d6 per die, pool = Warlock level + 1) to heal a creature within 60 ft. Regain the whole pool on a long rest."),
        ('Warlock','Radiant Soul'):   ('Passive', 'Radiant Soul (passive)', "Resistance to radiant damage. Once per turn when you deal damage with a spell, you can add your CHA modifier as extra radiant damage."),
        ('Warlock','Celestial Resilience'): ('Passive', 'Celestial Resilience (passive)', "At the start of each short or long rest, you and up to 5 allies of your choice within 30 ft gain temporary HP equal to your Warlock level + your CHA modifier."),
        ('Warlock','Searing Vengeance'): ('Reaction', 'Searing Vengeance', "When you fail a death saving throw, burst with radiant energy instead of dying: regain HP equal to half your max, stand up, and each creature within 30 ft takes radiant damage equal to half your Warlock level and is blinded until the end of your next turn (CON save negates). Once per long rest."),
        ('Warlock','Form of Dread'): ('Bonus Action', 'Form of Dread', "Transform for 1 minute: gain temp HP equal to 1d10 + Warlock level. Once per turn on a hit, force a WIS save or frighten the target until the end of your next turn. You're immune to frightened while transformed. Uses = proficiency bonus per long rest."),
        ('Warlock','Grave Touched'): ('Passive', 'Grave Touched (passive)', "You don't need to eat, drink, or breathe. Additionally, once during each of your turns when you hit with an attack and roll damage, you can replace the damage type with necrotic. While your Form of Dread is active, roll one additional damage die for that necrotic damage."),
        ('Warlock','Necrotic Husk'): ('Reaction', 'Necrotic Husk', "Resistance to necrotic damage (implemented) — becomes immunity while your Form of Dread is active (implemented). Additionally: when reduced to 0 HP, use your reaction to drop to 1 HP instead and deal 2d10 + Warlock level necrotic damage to each creature of your choice within 30 ft, then gain 1 level of exhaustion. Once per 1d4 long rests."),
        ('Warlock','Spirit Projection'): ('Action', 'Spirit Projection', "Project your spirit from your body for up to 1 hour (body left unconscious). Resistance to bludgeoning/piercing/slashing (implemented) and flying speed equal to walking speed (implemented). Conjuration/Necromancy spells don't need V/S components or non-gold-cost material components. While your Form of Dread is active, regain HP equal to half the necrotic damage you deal once per turn. 1/LR."),
        ('Warlock','Among the Dead'): ('Passive', 'Among the Dead (passive)', "Learn the Spare the Dying cantrip; advantage on saves against disease. Undead that target you directly must succeed on a WIS save or choose a new target (or waste the attack), becoming immune to this effect from you for 24 hours on a success — and if you target such a creature, it becomes immune to this effect from you for 24 hours too."),
        ('Warlock','Defy Death'):     ('Passive', 'Defy Death (passive)', "Regain HP equal to 1d8 + your CON modifier (min 1) when you succeed on a death saving throw, or when you stabilize a creature with Spare the Dying. Uses = 1/long rest."),
        ('Warlock','Undying Nature'):  ('Passive', 'Undying Nature (passive)', "You no longer age, and can go without food, water, or air for weeks at a time."),
        ('Warlock','Indestructible Life'): ('Bonus Action', 'Indestructible Life', "Regain HP equal to 1d8 + your Warlock level, or reattach a severed body part or regrow a missing one (if you have at least 1 HP). Once per short or long rest."),
        ('Cleric','Blessings of Knowledge'): ('Passive', 'Blessings of Knowledge (passive)', "Learn two languages of your choice. Gain proficiency in two of Arcana/History/Nature/Religion, doubling your proficiency bonus for those skills."),
        ('Cleric','Knowledge of the Ages'): ('Bonus Action', 'Knowledge of the Ages', "Channel Divinity: gain proficiency with one skill or tool of your choice for 10 minutes."),
        ('Cleric','Read Thoughts'):    ('Action', 'Read Thoughts', "Channel Divinity: read a creature's surface thoughts within 60 ft (WIS save). While reading, cast Suggestion on it without a slot."),
        ('Cleric','Potent Spellcasting'): ('Passive', 'Potent Spellcasting (passive)', "Add your WIS modifier to the damage you deal with Cleric cantrips."),
        ('Cleric','Warding Flare'):   ('Reaction', 'Warding Flare', "When attacked by a creature within 30 ft you can see, impose disadvantage on the attack roll. Uses = WIS modifier (min 1) per long rest. An attacker immune to being blinded is immune."),
        ('Cleric','Radiance of the Dawn'): ('Action', 'Radiance of the Dawn (Channel Divinity)', "Dispel magical darkness in 30 ft; each hostile creature there takes 2d10 + Cleric level radiant damage (CON save halves)."),
        ('Cleric','Improved Flare'): ('Passive', 'Improved Flare (passive)', "Warding Flare now also protects allies within 30 ft, not just yourself."),
        ('Cleric','Corona of Light'): ('Bonus Action', 'Corona of Light', "60-ft aura of bright light (dim for another 30 ft) for 1 minute: creatures in it have disadvantage on saves against fire and radiant damage."),
        ('Cleric','Wrath of the Storm'): ('Reaction', 'Wrath of the Storm', "When a creature within 5 ft hits you with an attack, deal it 2d8 lightning or thunder damage (DEX save halves). Uses = WIS modifier (min 1) per long rest."),
        ('Cleric','Destructive Wrath'): ('Bonus Action', 'Destructive Wrath (Channel Divinity)', "When you roll lightning or thunder damage from a spell or Wrath of the Storm, deal maximum damage instead of rolling."),
        ('Cleric','Thunderbolt Strike'): ('Passive', 'Thunderbolt Strike (passive)', "When you deal lightning damage to a Large or smaller creature, you can push it up to 10 ft away from you."),
        ('Cleric','Stormborn'): ('Passive', 'Stormborn (passive)', "You have a flying speed equal to your walking speed whenever you are not underground or indoors."),
        ('Cleric','Arcane Initiate'): ('Passive', 'Arcane Initiate (passive)', "Gain proficiency in Arcana, and learn 2 cantrips from the Wizard spell list (they count as Cleric cantrips for you)."),
        ('Cleric','Arcane Abjuration'): ('Action', 'Arcane Abjuration (Channel Divinity)', "Present your holy symbol and target one celestial, elemental, fey, or fiend within 30 ft: WIS save or it's turned (forced to flee), or banished to its home plane if summoned/conjured."),
        ('Cleric','Spell Breaker'): ('Passive', 'Spell Breaker (passive)', "When you restore HP to a creature with a spell of 1st level or higher, you can also end one spell of equal or lower level affecting it."),
        ('Cleric','Arcane Mastery'): ('Passive', 'Arcane Mastery (passive)', "Choose 4 Wizard spells (one each of 6th/7th/8th/9th level); add them to your domain spells, always prepared."),
        ('Cleric','Blessing of the Forge'): ('Action', 'Blessing of the Forge', "Also grants proficiency with heavy armor. Touch a nonmagical weapon or suit of armor: it becomes magical, granting +1 to its attack/damage rolls (weapon) or AC (armor), until your next long rest. Once per long rest."),
        ('Cleric',"Artisan's Blessing"): ('Action', "Artisan's Blessing", "Spend 1 hour and any needed materials at smith's tools to conjure a nonmagical metal item worth up to 100 gp."),
        ('Cleric','Soul of the Forge'): ('Passive', 'Soul of the Forge (passive)', "Resistance to fire damage. While wearing heavy armor, gain +1 AC."),
        ('Cleric','Saint of Forge and Fire'): ('Passive', 'Saint of Forge and Fire (passive)', "Immunity to fire damage. While wearing heavy armor, also gain resistance to nonmagical bludgeoning/piercing/slashing damage."),
        ('Cleric','Circle of Mortality'): ('Passive', 'Circle of Mortality (passive)', "Healing spells cast on a creature at 0 HP treat any die as rolling maximum. Also cast Spare the Dying at 30 ft as a bonus action, using WIS."),
        ('Cleric','Eyes of the Grave'): ('Action', 'Eyes of the Grave', "Sense the presence of undead within 60 ft (through walls, not total cover) until the end of your next turn. Uses = WIS modifier (min 1) per long rest."),
        ('Cleric','Path to the Grave'): ('Action', 'Path to the Grave (Channel Divinity)', "Curse a creature within 30 ft until the end of your next turn: the next attack from you or an ally to hit it deals with vulnerability, then the curse ends."),
        ('Cleric',"Sentinel at Death's Door"): ('Reaction', "Sentinel at Death's Door", "When a creature within 30 ft would suffer a critical hit, turn it into a normal hit instead. Uses = WIS modifier per long rest."),
        ('Cleric','Keeper of Souls'): ('Passive', 'Keeper of Souls (passive)', "Once per turn, when an enemy you can see dies within 30 ft, you or an ally within 30 ft regains HP equal to the enemy's Hit Dice (not while incapacitated)."),
        ('Cleric','Voice of Authority'): ('Passive', 'Voice of Authority (passive)', "When you target an ally with a spell using a 1st-level+ slot, that ally can immediately use its reaction to make one weapon attack against a creature you can see."),
        ('Cleric',"Order's Demand"): ('Action', "Order's Demand (Channel Divinity)", "Each creature of your choice within 30 ft that can see/hear you: WIS save or be charmed until the end of your next turn or until it takes damage; charmed creatures also drop what they're holding if you choose."),
        ('Cleric','Embodiment of the Law'): ('Passive', 'Embodiment of the Law (passive)', "Casting an enchantment spell with a 1st-level+ slot that normally takes an action can instead be cast as a bonus action. Uses = WIS modifier (min 1) per long rest."),
        ('Cleric',"Order's Wrath"): ('Passive', "Order's Wrath (passive)", "When Voice of Authority triggers an ally's attack and it hits, the target also takes 2d8 extra psychic damage."),
        ('Cleric','Emboldening Bond'): ('Bonus Action', 'Emboldening Bond', "Create an empathic bond between up to 5 willing creatures within 30 ft (including yourself) for 10 minutes. Bonded creatures near another bonded creature can add 1d4 to attack rolls, ability checks, and saves. Uses = WIS modifier (min 1) per long rest."),
        ('Cleric','Balm of Peace'): ('Action', 'Balm of Peace', "Move up to your speed without provoking opportunity attacks; heal each creature you touch along the way for 2d6 + WIS modifier (once per creature)."),
        ('Cleric','Protective Bond'): ('Reaction', 'Protective Bond', "A creature bonded to you (Emboldening Bond) can teleport to intercept an attack meant for another bonded creature within 30 ft, taking the damage instead."),
        ('Cleric','Expansive Bond'): ('Passive', 'Expansive Bond (passive)', "Emboldening Bond and Protective Bond now work at 60 ft instead of 30 ft. A creature that uses Protective Bond to take someone else's damage also gains resistance to it."),
        ('Cleric','Eyes of Night'): ('Passive', 'Eyes of Night (passive)', "You have darkvision out to 300 ft, and can share it with willing creatures you touch for 1 hour. Uses = proficiency bonus per long rest."),
        ('Cleric','Vigilant Blessing'): ('Action', 'Vigilant Blessing', "Touch a creature (possibly yourself) to grant advantage on its next initiative roll. Ends after that roll, or if you use this again."),
        ('Cleric','Twilight Sanctuary'): ('Action', 'Twilight Sanctuary (Channel Divinity)', "Create a 30-ft-radius sphere of dim light for 1 minute. Each creature that ends its turn there gains temp HP (1d6 + Cleric level) or a save vs. one frightened/charmed effect on it (your choice)."),
        ('Cleric','Steps of Night'): ('Bonus Action', 'Steps of Night', "While in dim light or darkness, gain a flying speed equal to your walking speed for 1 minute. Uses = proficiency bonus per long rest."),
        ('Cleric','Twilight Shroud'): ('Passive', 'Twilight Shroud (passive)', "Creatures of your choice within your Twilight Sanctuary have half cover."),
        ('Cleric',"Solidarity's Action"): ('Bonus Action', "Solidarity's Action", "When you take the Help action to aid an ally's attack, make one weapon attack as a bonus action. Uses = WIS modifier (min 1) per long rest."),
        ('Cleric',"Oketra's Blessing"): ('Reaction', "Oketra's Blessing", "Channel Divinity: when a creature within 30 ft makes an attack roll, grant it +10 to that roll, chosen after seeing the roll but before the outcome."),
        ('Cleric','Blessing of the Trickster'): ('Action', 'Blessing of the Trickster', "Touch a willing creature other than yourself to grant it advantage on DEX (Stealth) checks for 1 hour, or until you use this again."),
        ('Cleric','Invoke Duplicity'): ('Action', 'Invoke Duplicity', "Channel Divinity: create an illusory duplicate of yourself for 1 minute. Bonus action to move it up to 30 ft (within 120 ft of you). Cast spells as though from its space; advantage on attacks against a creature within 5 ft of both you and the illusion."),
        ('Cleric','Cloak of Shadows'): ('Action', 'Cloak of Shadows', "Channel Divinity: as an action while in dim light or darkness, become invisible until you make an attack, cast a spell, or are in an area of bright light."),
        ('Cleric','Divine Strike (Trickery)'): ('Passive', 'Divine Strike (Trickery) (passive)', "Once per turn, deal an extra 1d8 psychic damage on a weapon hit (2d8 at 14th level)."),
        ('Cleric','Improved Duplicity'): ('Passive', 'Improved Duplicity (passive)', "Invoke Duplicity creates up to 4 duplicates instead of 1; move any number of them up to 30 ft each (still within 120 ft of you) as a bonus action."),
        ('Cleric','Oketra\'s Blessing'): ('Reaction', "Oketra's Blessing", "Channel Divinity: when a creature within 30 ft makes an attack roll, grant it a +10 bonus, chosen after seeing the roll but before the outcome is known."),
        ('Cleric','Supreme Healing'): ('Passive', 'Supreme Healing (passive)', "When you roll dice to restore HP with a spell, use the highest possible number for each die instead of rolling."),
        ('Cleric','Acolyte of Strength'): ('Passive', 'Acolyte of Strength (passive)', "Learn one Druid cantrip of your choice. Gain proficiency in one of Animal Handling, Athletics, Nature, or Survival."),
        ('Cleric','Feat of Strength'): ('Bonus Action', 'Feat of Strength', "Channel Divinity: when you make an attack roll, ability check, or saving throw using Strength, gain a +10 bonus, chosen after seeing the roll but before the outcome is known."),
        ('Cleric',"Rhonas' Blessing"): ('Reaction', "Rhonas' Blessing", "Channel Divinity: when a creature within 30 ft makes an attack roll, ability check, or saving throw using Strength, grant it +10 to that roll, chosen after seeing the roll but before the outcome."),
        ('Cleric','Priest of Zeal'): ('Bonus Action', 'Priest of Zeal', "When you take the Attack action, make one weapon attack as a bonus action. Uses = WIS modifier (min 1) per long rest."),
        ('Cleric','Consuming Fervor'): ('Passive', 'Consuming Fervor (passive)', "Channel Divinity: when you roll fire or thunder damage, deal maximum damage instead of rolling."),
        ('Cleric','Resounding Strike'): ('Passive', 'Resounding Strike (passive)', "When you deal thunder damage to a Large or smaller creature, you can also push it up to 10 ft away from you."),
        ('Cleric','Blaze of Glory'): ('Reaction', 'Blaze of Glory', "When reduced to 0 HP by an attacker you can see (even lethally), move up to your speed toward it and make one melee attack with advantage. On a hit: extra 5d10 fire + 5d10 weapon-type damage. Then fall unconscious and make death saves as normal. 1/LR."),
        ('Cleric','Visions of the Past'): ('Action', 'Visions of the Past', "Meditate for at least 1 minute to receive visions of relevant past events related to an object you hold or your surroundings. 1/SR or LR."),
        ('Cleric','Acolyte of Nature'): ('Passive', 'Acolyte of Nature (passive)', "Learn one druid cantrip and gain proficiency in one of Animal Handling, Nature, or Survival."),
        ('Cleric','Charm Animals and Plants'): ('Action', 'Charm Animals and Plants', "Channel Divinity: each beast or plant creature within 30 ft must succeed on a WIS save or be charmed by you for 1 minute."),
        ('Cleric','Bonus Proficiency (Heavy Armor)'): ('Passive', 'Bonus Proficiency (passive)', "Proficiency with heavy armor."),
        ('Cleric','Bonus Proficiencies (Martial Weapons, Heavy Armor)'): ('Passive', 'Bonus Proficiencies (passive)', "Proficiency with martial weapons and heavy armor."),
        ('Cleric','Bonus Proficiencies (War Domain)'): ('Passive', 'Bonus Proficiencies (passive)', "Proficiency with martial weapons and heavy armor."),
        ('Cleric','Bonus Cantrip (Light Domain)'): ('Passive', 'Bonus Cantrip (passive)', "You learn the Light cantrip if you don't already know it. It doesn't count against your cantrips known."),
        ('Cleric','Bonus Proficiencies (Tempest)'): ('Passive', 'Bonus Proficiencies (passive)', "Proficiency with martial weapons and heavy armor."),
        ('Cleric','Bonus Proficiencies (Order)'): ('Passive', 'Bonus Proficiencies (passive)', "Proficiency with heavy armor and martial weapons."),
        ('Cleric','Implement of Peace'): ('Passive', 'Implement of Peace (passive)', "Proficiency in the Insight, Performance, or Persuasion skill."),
        ('Cleric','Bonus Proficiencies (Twilight)'): ('Passive', 'Bonus Proficiencies (passive)', "Proficiency with martial weapons and heavy armor."),
        ('Cleric','Destructive Wrath'): ('Reaction', 'Destructive Wrath', "Channel Divinity: when you roll lightning or thunder damage, deal maximum damage instead of rolling."),
        ("Cleric","War God's Blessing"): ('Reaction', "War God's Blessing", "Channel Divinity: when a creature within 30 ft makes an attack roll, grant it +10 to the roll (chosen after seeing the roll, before the DM says hit or miss)."),
        ('Cleric','Dampen Elements'):  ('Reaction', 'Dampen Elements', "When you or a creature within 30 ft takes acid, cold, fire, lightning, or thunder damage, grant resistance to that instance of the damage."),
        ('Cleric','Master of Nature'): ('Bonus Action', 'Master of Nature', "While a creature is charmed by your Charm Animals and Plants, command what it does on its next turn."),
        ('Cleric','War Priest'):      ('Bonus Action', 'War Priest', "When you take the Attack action, you can make one weapon attack as a bonus action. Uses = WIS mod per long rest."),
        ('Cleric','Guided Strike'):   ('Reaction', 'Guided Strike', "Channel Divinity: gain +10 to one attack roll."),
        ('Cleric',"War God's Blessing"): ('Reaction', "War God's Blessing", "Channel Divinity: when an ally within 30 ft makes an attack roll, grant it +10 to that roll."),
        ('Cleric','Avatar of Battle'): ('Passive', 'Avatar of Battle (passive)', "Resistance to bludgeoning, piercing, and slashing damage from nonmagical attacks."),
        ('Artificer','Magical Tinkering'):('Action',   'Magical Tinkering','Imbue a tiny object with one of 4 minor magical properties. INT mod active at once.'),
        ('Artificer','Infuse Item'):   ('Action',      'Infuse Item','During LR: infuse nonmagical items with magic. Known infusions / 2 active at once.'),
        ('Blood Hunter','Blood Maledict'):('Bonus Action','Blood Maledict','Curse a creature within 30 ft with a known blood curse. Free to invoke; you may optionally Amplify it by taking necrotic damage equal to your Hemocraft die for an added effect. Uses per short/long rest scale by level.'),
        ('Blood Hunter','Crimson Rite'):('Bonus Action','Crimson Rite','Activate a rite on a weapon you hold: take necrotic damage equal to your Hemocraft die, then your hits with it deal extra elemental damage equal to that same die until your next rest.'),
        ('Blood Hunter','Fighting Style'): ('Passive', 'Fighting Style (passive)',
            "Your chosen fighting style's benefit (Archery, Dueling, Great Weapon Fighting, or "
            "Two-Weapon Fighting — see your specific choice for the exact effect)."),
        ('Blood Hunter','Extra Attack'): ('Passive', 'Extra Attack (passive)',
            "Attack twice, instead of once, whenever you take the Attack action on your turn."),
        ('Blood Hunter','Rite of the Dawn'): ('Passive', 'Rite of the Dawn (passive)',
            "This Crimson Rite deals radiant damage. While active: your weapon sheds bright light "
            "in a 20-ft radius, you have resistance to necrotic damage, and hitting an undead "
            "creature with it rolls an extra hemocraft die for the rite's damage."),
        ('Blood Hunter','Blood Curse of the Exorcist'): ('Bonus Action', 'Blood Curse of the Exorcist',
            "Bonus blood curse (doesn't count against curses known): choose a charmed, frightened, "
            "or possessed creature within 30 ft — it's freed of that condition. Amplify: whatever "
            "charmed/frightened/possessed it takes 3d6 psychic damage and must succeed on a WIS "
            "save or be stunned until the end of your next turn."),
        ('Blood Hunter','Blood Curse of Corrosion'): ('Bonus Action', 'Blood Curse of Corrosion',
            "Bonus blood curse (doesn't count against curses known): poison a creature within 30 "
            "ft — CON save at the end of each of its turns ends it. Amplify: it takes 4d6 necrotic "
            "damage now, and again each time it fails that save."),
        ('Blood Hunter','Blood Curse of the Souleater'): ('Reaction', 'Blood Curse of the Souleater',
            "Bonus blood curse (doesn't count against curses known): when a non-construct, "
            "non-undead creature within 30 ft drops to 0 HP, offer its life energy to your patron "
            "— until the end of your next turn you attack with advantage and have resistance to "
            "all damage. Amplify: also regain an expended warlock spell slot; can't amplify again "
            "until a long rest."),
        ('Blood Hunter','Blood Curse of the Howl'): ('Action', 'Blood Curse of the Howl',
            "Bonus blood curse (doesn't count against curses known): unleash a howl — each "
            "creature within 30 ft that can hear you (any you exclude are unaffected) makes a WIS "
            "save or is frightened until the end of your next turn (failing by 5+ also stuns while "
            "frightened); a success grants 24-hour immunity to this curse. Amplify: range becomes 60 ft."),
        ("Blood Hunter","Hunters Bane"): ('Passive', "Hunter's Bane (passive)", "Advantage on WIS (Survival) checks to track fey, fiends, or undead, and on INT checks to recall information about them."),
        ('Blood Hunter','Brand of Castigation'): ('Passive', 'Brand of Castigation (passive)', "No action needed when you damage a creature with an active-crimson-rite weapon: brand it, always know its direction, and it takes psychic damage (= Hemocraft mod, min 1) whenever it damages you or an ally within 5 ft. 1/SR or LR."),
        ('Blood Hunter','Grim Psychometry'): ('Passive', 'Grim Psychometry (passive)', "Advantage on INT (History) checks about the sinister or tragic history of an object you're touching or your location."),
        ('Blood Hunter','Dark Augmentation'): ('Passive', 'Dark Augmentation (passive)', "+5 ft speed. Gain a bonus to STR/DEX/CON saving throws equal to your Hemocraft modifier (min +1)."),
        ('Blood Hunter','Brand of Tethering'): ('Passive', 'Brand of Tethering (passive)', "Brand of Castigation's psychic damage becomes 2x your Hemocraft modifier. A branded creature can't Dash, and teleporting or leaving its plane deals it 4d6 psychic damage plus a WIS save or the attempt fails."),
        ('Blood Hunter','Hardened Soul'): ('Passive', 'Hardened Soul (passive)', "Advantage on saving throws against being charmed and frightened."),
        ('Blood Hunter','Sanguine Mastery'): ('Passive', 'Sanguine Mastery (passive)', "Once per turn, reroll any Hemocraft die for a Blood Hunter feature and use either result. A critical hit with an active-crimson-rite weapon regains one use of Blood Maledict."),
        ('Blood Hunter','Curse Specialist'): ('Passive', 'Curse Specialist (passive)', "Gain an additional use of Blood Maledict. Your blood curses can target any creature, whether it has blood or not."),
        ('Blood Hunter','Aether Walk'): ('Action', 'Aether Walk', "At the start of your turn (if not incapacitated): step into the veil between planes for a number of rounds = Hemocraft modifier. Move through creatures/objects as difficult terrain; see/affect Ethereal creatures. 1d10 force damage if you end your turn inside an object. 1/SR or LR (2/rest at 15th)."),
        ('Blood Hunter','Brand of Sundering'): ('Passive', 'Brand of Sundering (passive)', "Hits against a branded creature with an active-crimson-rite weapon roll an extra Hemocraft die. A branded creature with Incorporeal Movement can't use it to move through creatures/objects."),
        ('Blood Hunter','Rite Revival'): ('Reaction', 'Rite Revival', "If you have an active crimson rite and drop to 0 HP without dying outright, end all active rites to drop to 1 HP instead."),
        ('Blood Hunter','Heightened Senses'): ('Passive', 'Heightened Senses (passive)', "Advantage on WIS (Perception) checks relying on hearing or smell."),
        ('Blood Hunter','Hybrid Transformation'): ('Bonus Action', 'Hybrid Transformation', "Transform into a hybrid form for up to 1 hour: Feral Might (adv. STR checks/saves, +melee damage), Resilient Hide (resistance to nonmagical B/P/S, +1 AC unarmored/light), Predatory Strikes (Crimson Rite on unarmed strikes using DEX, extra unarmed strike as bonus action), Bloodlust (below half HP: WIS save or attack nearest creature). 1/SR or LR (2 at 11th, unlimited at 18th)."),
        ("Blood Hunter","Stalkers Prowess"): ('Passive', "Stalker's Prowess (passive)", "+10 ft speed, +10 ft long jump, +3 ft high jump. Hybrid form also gains +1 (scaling) to unarmed strike attack rolls."),
        ('Blood Hunter','Advanced Transformation'): ('Passive', 'Advanced Transformation (passive)', "Hybrid Transformation usable twice per short/long rest. Hybrid form also regains 1 + CON mod HP at the start of each turn while between 1 HP and half max."),
        ('Blood Hunter','Brand of the Voracious'): ('Passive', 'Brand of the Voracious (passive)', "Advantage on your Bloodlust save while in hybrid form. Advantage on attack rolls against a creature branded by your Brand of Castigation while in hybrid form."),
        ('Blood Hunter','Hybrid Transformation Mastery'): ('Passive', 'Hybrid Transformation Mastery (passive)', "Unlimited Hybrid Transformation uses (implemented); hybrid form lasts until you revert, fall unconscious, or die. Also grants the Blood Curse of the Howl for free."),
        ('Blood Hunter','Mutagencraft'): ('Bonus Action', 'Mutagencraft', "Consume a known mutagen formula (uses/formulas known scale by level, both implemented). Action to flush all active mutagens early."),
        ('Blood Hunter','Strange Metabolism'): ('Passive', 'Strange Metabolism (passive)', "Immunity to poison damage and the poisoned condition. Bonus action: ignore one mutagen's negative side effect for 1 minute, 1/LR."),
        ('Blood Hunter','Brand of Axiom'): ('Passive', 'Brand of Axiom (passive)', "Branding a creature ends illusion/invisibility on it and blocks either while branded. Alternate-form creatures WIS save or revert and are stunned; attempts to change form while branded need the same save or fail and stun."),
        ('Blood Hunter','Exalted Mutation'): ('Bonus Action', 'Exalted Mutation', "End one active mutagen and immediately gain a different known mutagen's effects instead. Uses = Hemocraft modifier (min 1) per long rest."),
        ('Blood Hunter','Otherworldly Patron'): ('Passive', 'Otherworldly Patron (passive)', "Choose a Warlock-style patron at 3rd level; it flavors several of your Profane Soul features."),
        ('Blood Hunter','Pact Magic'): ('Passive', 'Pact Magic (passive)', "Cast Warlock spells with slots that scale by Blood Hunter level and recharge on a short rest, using your Hemocraft ability."),
        ('Blood Hunter','Rite Focus'): ('Passive', 'Rite Focus (passive)', "While a crimson rite is active, your weapon is a spellcasting focus for your Warlock spells, plus a patron-specific bonus (e.g. Archfey lights up a struck foe, negating its cover/invisibility)."),
        ('Blood Hunter','Mystic Frenzy'): ('Bonus Action', 'Mystic Frenzy', "When you cast a cantrip with Pact Magic, make one weapon attack as a bonus action."),
        ('Blood Hunter','Revealed Arcana'): ('Action', 'Revealed Arcana', "Cast a patron-specific spell using a Pact Magic slot; can't repeat until a long rest."),
        ("Blood Hunter","Brand of the Sapping Scar"): ('Passive', 'Brand of the Sapping Scar (passive)', "A creature branded by your Brand of Castigation has disadvantage on saves against your Warlock spells."),
        ('Blood Hunter','Unsealed Arcana'): ('Action', 'Unsealed Arcana', "Cast a second, more powerful patron-specific spell without a spell slot; can't repeat until a long rest."),
    }

    # Collect classes the character has
    char_classes = {c['class']: c.get('level',0) for c in char.get('classes',[])}
    char_subclasses_map = {c['class']: c.get('subclass','') for c in char.get('classes',[])}
    
    for (cls_name, feat_fragment), (bucket, display, desc) in KNOWN_ACTIONS.items():
        if cls_name not in char_classes:
            continue
        char_lvl = char_classes[cls_name]
        # Level gating for some features
        min_level = {
            'Evasion': 7, 'Uncanny Dodge': 5, 'Countercharm': 6,
            'Cunning Action': 2, 'Wild Shape': 2, 'Divine Smite': 2,
            'Cleansing Touch': 14, 'Primeval Awareness': 3, 'Flash of Genius': 7,
            'Reliable Talent': 11, 'Blindsense': 14, 'Elusive': 18, 'Stroke of Luck': 20,
            'Magical Ambush': 9, 'Versatile Trickster': 13, 'Spell Thief': 17,
            'Infiltration Expertise': 9, 'Impostor': 13, 'Death Strike': 17,
            'Steady Eye': 9, 'Unerring Eye': 13, 'Eye for Weakness': 17,
            'Superior Mobility': 9, 'Ambush Master': 13, 'Sudden Strike': 17,
            'Tokens of the Departed': 9, 'Ghost Walk': 13, "Death's Friend": 17,
            'Insightful Manipulator': 9, 'Misdirection': 13, 'Soul of Deceit': 17,
            'Superior Mobility': 9, 'Ambush Master': 13, "Sudden Strike": 17,
            'Soul Blades': 9, 'Psychic Veil': 13, 'Rend Mind': 17,
            'Panache': 9, 'Elegant Maneuver': 13, 'Master Duelist': 17,
            'Projected Ward': 6, 'Improved Abjuration': 10, 'Spell Resistance': 14,
            'Benign Transposition': 6, 'Focused Conjuration': 10, 'Durable Summons': 14,
            'Expert Divination': 6, 'The Third Eye': 10, 'Greater Portent': 14,
            'Instinctive Charm': 6, 'Split Enchantment': 10, 'Alter Memories': 14,
            'Potent Cantrip': 6, 'Empowered Evocation': 10, 'Overchannel': 14,
            'Malleable Illusions': 6, 'Illusory Self': 10, 'Illusory Reality': 14,
            'Undead Thralls': 6, 'Inured to Undeath': 10, 'Command Undead': 14,
            "Transmuters Stone": 6, 'Shapechanger': 10, 'Master Transmuter': 14,
            'Momentary Stasis': 6, 'Arcane Abeyance': 10, 'Convergent Future': 14,
            'Violent Attraction': 6, 'Event Horizon': 10, 'Gravity Fissure': 14,
            'Manifest Mind': 6, 'Master Scrivener': 10, 'One with the Word': 14,
            'Power Surge': 6, 'Durable Magic': 10, 'Deflecting Shroud': 14,
            'Brand of Castigation': 6, 'Grim Psychometry': 9, 'Dark Augmentation': 10,
            'Brand of Tethering': 13, 'Hardened Soul': 14, 'Sanguine Mastery': 20,
            'Curse Specialist': 3, 'Aether Walk': 7, 'Brand of Sundering': 11, 'Rite Revival': 18,
            'Advanced Transformation': 11, 'Brand of the Voracious': 15, 'Hybrid Transformation Mastery': 18,
            'Strange Metabolism': 7, 'Brand of Axiom': 11, 'Exalted Mutation': 18,
            'Mystic Frenzy': 7, 'Revealed Arcana': 7, "Brand of the Sapping Scar": 11, 'Unsealed Arcana': 15,
            'Beast Spells': 18, 'Timeless Body': 18, 'Archdruid': 20,
            'Primal Strike': 6, 'Elemental Wild Shape': 10, 'Thousand Forms': 14,
            "Lands Stride": 6, "Natures Sanctuary": 14,
            'Hearth of Moonlight and Shadow': 6, 'Hidden Paths': 10, 'Walker in Dreams': 14,
            'Mighty Summoner': 6, 'Guardian Spirit': 10, 'Faithful Summons': 14,
            'Fungal Infestation': 6, 'Spreading Spores': 10, 'Spreading Spores (Improved)': 14,
            'Cosmic Omen': 6, 'Twinkling Constellations': 10, 'Full of Stars': 14,
            'Enhanced Bond': 6, 'Cauterizing Flames': 10, 'Blazing Revival': 14,
            'Elemental Attunement': 3,
            'Wholeness of Body': 6, 'Tranquility': 11, 'Quivering Palm': 17,
            'Shadow Step': 6, 'Cloak of Shadows': 11, 'Opportunist': 17,
            'One with the Blade': 6, 'Sharpen the Blade': 11, 'Unerring Accuracy': 17,
            'Visage of the Astral Self': 6, 'Body of the Astral Self': 11, 'Awakened Astral Self': 17,
            'Tipsy Sway': 6, "Drunkards Luck": 11, 'Intoxicated Frenzy': 17,
            'Hour of Reaping': 6, 'Mastery of Death': 11, 'Touch of the Long Death': 17,
            "Physician's Touch": 6, 'Flurry of Healing and Harm': 11, 'Hand of Ultimate Mercy': 17,
            'Searing Arc Strike': 6, 'Searing Sunburst': 11, 'Sun Shield': 17,
            'Wings Unfurled': 6, 'Aspect of the Wyrm': 11, 'Draconic Presence (Monk)': 17,
            'Indomitable': 9, 'Aura of Protection': 6, 'Song of Rest': 2,
            'Slow Fall': 4, 'Patient Defense': 2, 'Step of the Wind': 2,
            'Deflect Missiles': 3, 'Flurry of Blows': 2, 'Stunning Strike': 5,
            'Favored Enemy': 1, 'Flexible Casting': 2, 'Metamagic': 3,
            'Preserve Life': 2, 'Turn Undead': 2, 'Channel Divinity': 2,
            'Crimson Rite': 2, 'Spirit Shield': 6, 'Battlerager Charge': 10,
            'Spiked Retribution': 14, 'Infectious Fury': 10, 'Call the Hunt': 14,
            'Elemental Cleaver': 6, 'Mighty Impel': 10, 'Demiurgic Colossus': 14,
            'Mindless Rage': 6, 'Intimidating Presence': 10, 'Retaliation': 14,
            'Shielding Storm': 10, 'Raging Storm': 14, 'Bolstering Magic': 6,
            'Unstable Backlash': 10, 'Fanatical Focus': 6, 'Zealous Presence': 10,
            'Controlled Surge': 14,
            'Arcane Firearm': 5, 'Fortified Position': 9, 'Explosive Cannon': 15,
            'Superior Inspiration': 20, 'Peerless Skill': 14, 'Battle Magic': 14,
            "Master's Flourish": 14, 'Animating Performance': 6, 'Creative Crescendo': 14,
            'Universal Speech': 6, 'Infectious Inspiration': 14, 'Unfailing Inspiration': 6,
            'Divine Strike': 8, 'Improved Flare': 8, 'Corona of Light': 17,
            'Wrath of the Storm': 2, 'Arcane Abjuration': 2, "Artisan's Blessing": 2,
            'Path to the Grave': 2, "Order's Demand": 2, 'Balm of Peace': 2, 'Twilight Sanctuary': 2,
            'Blessed Healer': 6, 'Radiance of the Dawn': 2,
            'Mantle of Majesty': 6, 'Unbreakable Majesty': 14,
            'Mystic Chronicle': 6, 'Awakened Spirit': 14,
            'Mantle of Whispers': 6, 'Shadow Lore': 14,
            'Purity of Spirit': 15, 'Holy Nimbus': 20,
            'Relentless Avenger': 7, 'Soul of Vengeance': 15, 'Avenging Angel': 20,
            'Aura of Conquest': 7, 'Scornful Rebuke': 15, 'Invincible Conqueror': 20,
            'Aura of the Guardian': 7, 'Protective Spirit': 15,
            'Glorious Defense': 15, 'Living Legend': 20,
            'Vigilant Rebuke': 15, 'Mortal Bulwark': 20,
            'Undying Sentinel': 15, 'Elder Champion': 20, 'Dread Lord': 20,
            'Eldritch Master': 20, 'Dark Delirium': 14,
            'Guardian Coil': 6, 'Grasping Tentacles': 10, 'Hurl Through Hell': 14,
            'Fiendish Resilience': 10, 'Thought Shield': 10,
            'Radiant Soul': 6, 'Celestial Resilience': 10, 'Searing Vengeance': 14,
            'Elemental Gift': 6,
            'Sanctuary Vessel': 10, 'Limited Wish': 14, 'Create Thrall': 14,
            'Accursed Specter': 6, 'Armor of Hexes': 10, 'Master of Hexes': 14,
            'Grave Touched': 6, 'Necrotic Husk': 10, 'Spirit Projection': 14, 'Undying Nature': 10,
            'Defy Death': 6, 'Indestructible Life': 14,
            'Read Thoughts': 6, 'Potent Spellcasting': 8, 'Visions of the Past': 17,
            'Dampen Elements': 6, 'Master of Nature': 17,
            "Land's Stride": 8, 'Hide in Plain Sight': 10, 'Vanish': 13,
            'Feral Senses': 18, 'Foe Slayer': 20,
            'Defensive Tactics': 7, 'Multiattack': 11, "Superior Hunter's Defense": 15,
            'Exceptional Training': 7, 'Bestial Fury': 11, 'Share Spells': 15,
            'Iron Mind': 7, "Stalker's Flurry": 11, 'Shadowy Dodge': 15,
            'Ethereal Step': 7, 'Distant Strike': 11, 'Spectral Defense': 15,
            'Supernatural Defense': 7, "Magic-User's Nemesis": 11, "Slayer's Counter": 15,
            'Divine Allegiance': 7, 'Unyielding Saint': 15, 'Exalted Champion': 20,
            'Aura of Devotion': 7, 'Emissary of Redemption': 20, 'Aura of Alacrity': 7,
            'Aura of the Sentinel': 7, 'Aura of Warding': 7, 'Aura of Hate': 7, 'Supernatural Resistance': 15,
            'Misty Escape': 6, 'Beguiling Defenses': 10, 'Oceanic Soul': 6, 'Fathomless Plunge': 14,
            # Cross-class gate fixes found by the systematic leak scan (levels taken
            # directly from the already-verified CLASS_FEATURE_INDEX, not re-derived):
            'Infuse Item': 2, 'Reckless Attack': 2, 'Action Surge': 2,
            'Invoke Duplicity': 2, 'Improved Duplicity': 17, 'Divine Strike (Trickery)': 8,
            "Oketra's Blessing": 6, 'Supreme Healing': 17,
            'Feat of Strength': 2, "Rhonas' Blessing": 6,
            'Consuming Fervor': 2, 'Resounding Strike': 6, 'Blaze of Glory': 17,
            "War God's Blessing": 6, 'Touch of Death': 2, 'Avatar of Battle': 17,
            'Inescapable Destruction': 6, 'Improved Reaper': 17,
            'Destructive Wrath': 6, 'Thunderbolt Strike': 8, 'Stormborn': 17,
            'Spell Breaker': 6, 'Arcane Mastery': 17,
            'Soul of the Forge': 6, 'Saint of Forge and Fire': 17,
            "Sentinel at Death's Door": 6, 'Keeper of Souls': 17,
            'Embodiment of the Law': 6, "Order's Wrath": 17,
            'Protective Bond': 6, 'Expansive Bond': 17,
            'Steps of Night': 6, 'Twilight Shroud': 17,
            'Charm Animals and Plants': 2, 'Knowledge of the Ages': 2,
            'Bend Luck': 6, 'Storm Guide': 6,
            "Dark One's Own Luck": 6, 'Entropic Ward': 6,
            'Gravity Well': 6,
            "Stalkers Prowess": 7, 'Guided Strike': 2,
            'Beguiling Twist': 7, 'Fey Reinforcements': 11, 'Misty Wanderer': 15,
            'Writhing Tide': 7, 'Mighty Swarm': 11, 'Swarming Dispersal': 15,
            "Drakes Breath": 7, 'Symbiotic Link': 11, "Dragons Purpose": 15,
            'Remarkable Athlete': 7, 'Additional Fighting Style': 10,
            'Superior Critical': 15, 'Survivor (Champion)': 18,
            'Extra Attack (Bladesinging)': 6,
            'Unwavering Mark': 3, 'Warding Maneuver': 7, 'Hold the Line': 10,
            'Ferocious Charger': 15, 'Vigilant Defender': 18,
            'Runic Shield': 7, 'Great Stature': 10, 'Master of Runes': 15, 'Runic Juggernaut': 18,
            'Elegant Courtier': 7, 'Tireless Spirit': 10, 'Rapid Strike': 15, 'Strength before Death': 18,
            'Supreme Sneak': 9, 'Use Magic Device': 13, "Thief's Reflexes": 17,
            'Echo Avatar': 7, 'Shadow Martyr': 10, 'Reclaim Potential': 15, 'Legion of One': 18,
            'Royal Envoy': 7, 'Inspiring Surge': 10,
            'Elemental Affinity': 6, 'Draconic Presence': 18,
            'Controlled Chaos': 14, 'Spell Bombardment': 18,
            'Empowered Healing': 6, 'Unearthly Recovery': 18,
            'Psionic Sorcery': 6, 'Revelation in Flesh': 14, 'Warping Implosion': 18,
            'Restore Balance': 1, 'Bastion of Law': 6, 'Trance of Order': 14, 'Clockwork Cavalcade': 18,
            'Moon Fire': 1, 'Lunar Boons + Waxing and Waning': 6, 'Lunar Empowerment': 14, 'Lunar Phenomenon': 18,
            'Strength of the Grave': 1, 'Hound of Ill Omen': 6, 'Shadow Walk': 14, 'Umbral Form': 18,
            'Mystic Arcanum (6th)': 11, 'Mystic Arcanum (7th)': 13,
            'Mystic Arcanum (8th)': 15, 'Mystic Arcanum (9th)': 17,
            'Relentless Rage': 11, 'Consult the Spirits': 10,
            'Danger Sense': 2, 'Extra Attack': 5, 'Fast Movement': 5,
            'Feral Instinct': 7, 'Instinctive Pounce': 7, 'Brutal Critical': 9,
            'Persistent Rage': 15, 'Indomitable Might': 18, 'Primal Champion': 20,
            'Reckless Abandon': 6, 'Bestial Soul': 6, 'Aspect of the Beast': 6,
            'Spirit Walker': 10, 'Totemic Attunement': 14, 'Storm Soul': 6,
            'Rage Beyond Death': 14,
            'Soul of Artifice': 20,
            'Jack of All Trades': 2, 'Expertise': 3, 'Font of Inspiration': 5,
            'Bond of Fang and Scale': 7, 'Perfected Bond': 15,
            'Survivor (Champion)': 18, 'Know Your Enemy': 7, 'Improved Combat Superiority': 10,
            'Improved Combat Superiority (18th)': 18,
            'Relentless': 15, 'War Magic': 7, 'Eldritch Strike': 10, 'Arcane Charge': 15,
            'Improved War Magic': 18, 'Magic Arrow': 7, 'Curving Shot': 7, 'Arcane Shot (10th)': 10,
            'Ever-Ready Shot': 15, 'Arcane Shot (18th)': 18, 'Bulwark': 15, 'Inspiring Surge (18th)': 18,
            'Telekinetic Adept': 7, 'Guarded Mind': 10, 'Bulwark of Force': 15, 'Telekinetic Master': 18,
            'Dragon Wings': 14, 'Psychic Defenses': 6, 'Otherworldly Wings': 14,
            'Bend Luck': 6, 'Controlled Chaos': 14, 'Storm Guide': 6, "Storm's Fury": 14,
            'Draconic Presence': 18,
            'Heart of the Storm': 6, 'Wind Soul': 18,
            'Song of Defense': 10, 'Song of Victory': 14,
            "Nature's Ward": 10,
            'The Right Tool for the Job': 3, 'Tool Expertise': 6, 'Alchemical Savant': 5,
            'Restorative Reagents': 9, 'Armor Modifications': 9,
            'Magic Item Adept': 10, 'Spell-Storing Item': 11, 'Magic Item Savant': 14,
            'Magic Item Master': 18, 'Chemical Mastery': 15,
            'Perfected Armor': 15, 'Improved Defender': 15,
            'Blood Curse of the Exorcist': 15, 'Blood Curse of Corrosion': 15,
            'Blood Curse of the Souleater': 18, 'Blood Curse of the Howl': 18,
            'Runic Shield': 7, 'Great Stature': 10, 'Runic Juggernaut': 18,
            'Warding Maneuver': 7, 'Hold the Line': 10, 'Ferocious Charger': 15, 'Vigilant Defender': 18,
            'Tireless Spirit': 10, 'Rapid Strike': 15, 'Strength before Death': 18,
            'Magical Secrets': 10, 'Additional Magical Secrets': 6,
        }
        # A small number of feature names are shared across classes with
        # genuinely different level requirements (e.g. "Cloak of Shadows"
        # is Monk Way of the Shadow's 11th-level feature AND Cleric
        # Trickery Domain's 6th-level one) — a single by-name gate can only
        # be correct for one of them. These class-specific overrides win
        # over the shared by-name entry above.
        CLASS_SPECIFIC_GATE_OVERRIDES = {
            ('Cleric', 'Cloak of Shadows'): 6,
            ('Bard', 'Extra Attack'): 6,
            ('Wizard', 'Extra Attack'): 6,
            ('Blood Hunter', 'Fighting Style'): 2,
            ('Monk', 'Ki-Empowered Strikes'): 6,
            # Paladin's Channel Divinity (and every subclass option that
            # uses it) doesn't unlock until 3rd level. Guided Strike uses
            # its own level-3 gate rather than Cleric's level-2 gate.
            ('Paladin', 'Sacred Weapon'): 3, ('Paladin', 'Turn the Unholy'): 3,
            ('Paladin', 'Abjure Enemy'): 3, ('Paladin', 'Vow of Enmity'): 3,
            ('Paladin', 'Conquering Presence'): 3, ('Paladin', 'Guided Strike'): 3,
            ('Paladin', 'Emissary of Peace'): 3, ('Paladin', 'Rebuke the Violent'): 3,
            ('Paladin', 'Champion Challenge'): 3, ('Paladin', 'Turn the Tide'): 3,
            ('Paladin', 'Inspiring Smite'): 3, ('Paladin', 'Abjure the Extraplanar'): 3,
            ('Paladin', "Watcher's Will"): 3, ('Paladin', 'Turn the Faithless'): 3,
            ('Paladin', 'Control Undead'): 3, ('Paladin', 'Dreadful Aspect'): 3,
        }
        gate = CLASS_SPECIFIC_GATE_OVERRIDES.get((cls_name, feat_fragment))
        min_level = gate if gate is not None else min_level.get(feat_fragment, 1)
        # Only applies to genuine infusion choices (checked against the
        # real ARTIFICER_INFUSIONS list), not just class/level/subclass
        # — an Artificer who hasn't learned a given infusion (Boots of
        # the Winding Path, Resistant Armor, Spell-Refueling Ring,
        # Enhanced Weapon, etc.) shouldn't see its Combat page entry.
        # Automatic class features like Infuse Item itself or Flash of
        # Genius aren't in that list and are unaffected.
        if cls_name == 'Artificer' and feat_fragment in _ARTIFICER_INFUSION_BASE_NAMES:
            known_infusion_bases = {inf.split(" \u2013 ")[0].strip()
                                     for inf in char.get('artificer_infusions', [])}
            if feat_fragment not in known_infusion_bases:
                continue
        
        char_sub = char_subclasses_map.get(cls_name, '')
        if (char_lvl >= min_level
                and _feature_matches_char_subclass(cls_name, feat_fragment, char_sub)):
            # Bardic Inspiration's die size scales with Bard level — show the
            # ACTUAL current die instead of a vague "d6→d12" range.
            if feat_fragment == 'Bardic Inspiration' and cls_name == 'Bard':
                die = 6 if char_lvl < 5 else 8 if char_lvl < 10 else 10 if char_lvl < 15 else 12
                recovers = "short or long rest" if char_lvl >= 5 else "long rest"
                display = f"Bardic Inspiration (d{die})"
                desc = (f"Bonus action: give one ally within 60 ft a d{die} "
                        f"Bardic Inspiration die. They can add it to one "
                        f"attack roll, ability check, or saving throw within "
                        f"10 minutes. Uses = CHA modifier per {recovers}.")
            elif feat_fragment == 'Song of Rest' and cls_name == 'Bard':
                # PHB p.54: d6 at 2nd, d8 at 9th, d10 at 13th, d12 at 17th.
                die = 6 if char_lvl < 9 else 8 if char_lvl < 13 else 10 if char_lvl < 17 else 12
                desc = (f"Allies who hear your performance during a short "
                        f"rest and spend at least one Hit Die to heal regain "
                        f"an extra d{die} HP.")
                display = f"Song of Rest (d{die})"
            elif feat_fragment == 'Spirit Shield' and cls_name == 'Barbarian':
                # Ancestral Guardian: 2d6 at 6th, 3d6 at 10th, 4d6 at 14th.
                dice = 2 if char_lvl < 10 else 3 if char_lvl < 14 else 4
                desc = (f"While raging, use your reaction to reduce damage "
                        f"taken by an ally within 30 ft by {dice}d6.")
                # Vengeful Ancestors (14th level) upgrades this same feature
                # rather than being its own separate ability — added as an
                # addendum to Spirit Shield's own description, per the
                # user's specific request for how feature upgrades should
                # be shown, instead of a duplicate standalone entry.
                if char_lvl >= 14:
                    desc += (" Vengeful Ancestors: the attacker also takes force damage equal to "
                             "the amount this reduces.")
                display = f"Spirit Shield ({dice}d6)"
            elif feat_fragment == 'Inspiring Surge' and cls_name == 'Fighter':
                # SCAG p.128: 1 ally at 10th level, 2 allies at 18th.
                allies = 1 if char_lvl < 18 else 2
                ally_word = "one ally" if allies == 1 else "up to two allies"
                desc = (f"When you use Action Surge, {ally_word} within 60 ft. who can see or hear "
                        f"you can each use their reaction to make one weapon attack.")
            elif feat_fragment == 'Hybrid Transformation' and cls_name == 'Blood Hunter':
                # Melee damage bonus scales +1/+2/+3 at 3rd/11th/18th,
                # the resistance has a silvered-weapon exception, the AC
                # bonus applies while not wearing HEAVY armor (not just
                # "unarmored/light", which would wrongly exclude
                # medium), unarmed strike damage scales 1d6->1d8 at
                # 11th, and Bloodlust's save DC is a fixed 8.
                dmg_bonus = "+3" if char_lvl >= 18 else "+2" if char_lvl >= 11 else "+1"
                unarmed_die = "1d8" if char_lvl >= 11 else "1d6"
                desc = (f"Transform into a hybrid form for up to 1 hour: Feral Might (advantage on "
                        f"STR checks/saves, {dmg_bonus} melee damage rolls), Resilient Hide "
                        f"(resistance to nonmagical bludgeoning/piercing/slashing not made with "
                        f"silvered weapons, +1 AC while not wearing heavy armor), Predatory "
                        f"Strikes (Crimson Rite works on unarmed strikes, DEX for their "
                        f"attack/damage, {unarmed_die} bludgeoning or slashing, extra unarmed "
                        f"strike as a bonus action), Bloodlust (below half HP: DC 8 WIS save or "
                        f"move to and Attack the nearest creature).")
            elif feat_fragment == "Stalkers Prowess" and cls_name == 'Blood Hunter':
                # Same +1/+2/+3 scaling pattern as Hybrid Transformation's
                # damage bonus; the unarmed strikes also count as magical.
                atk_bonus = "+3" if char_lvl >= 18 else "+2" if char_lvl >= 11 else "+1"
                desc = (f"+10 ft speed, +10 ft long jump, +3 ft high jump. Hybrid form also "
                        f"gains {atk_bonus} to unarmed strike attack rolls, and with an active "
                        f"Crimson Rite on it, your unarmed strikes count as magical for "
                        f"overcoming resistance/immunity to nonmagical attacks.")
            elif feat_fragment == 'Channel Divinity' and cls_name == 'Cleric':
                # PHB p.59: 1 use at 2nd level, 2 at 6th, 3 at 18th.
                uses = 1 if char_lvl < 6 else 2 if char_lvl < 18 else 3
                display = f"Channel Divinity ({uses}/SR)"
                # Scan KNOWN_ACTIONS for every real Channel Divinity
                # entry and filter to just this character's subclass,
                # the same way the rest of this file avoids leaking
                # other subclasses' features, so the listed options
                # match what the character actually has rather than a
                # generic "use one option" placeholder.
                from dnd_app.core.character import subclasses as _subclasses_cd
                char_sub = _subclasses_cd(char).get('Cleric', '')
                cd_options = ['Turn Undead']
                # Exceptions: real Channel Divinity options whose
                # KNOWN_ACTIONS text mentions "Channel Divinity" in
                # neither the display name nor the description, so no
                # text-match can find them — named directly rather than
                # chasing a fully generic pattern for this
                # inconsistently-labeled data.
                CD_TEXT_EXCEPTIONS = {'Blessing of the Forge', 'Balm of Peace'}
                for (k_cls, k_frag), (k_bucket, k_disp, k_desc) in KNOWN_ACTIONS.items():
                    if k_cls != 'Cleric' or k_frag == 'Channel Divinity':
                        continue
                    if (k_frag not in CD_TEXT_EXCEPTIONS
                            and 'channel divinity' not in k_disp.lower()
                            and 'channel divinity' not in k_desc.lower()):
                        continue
                    if _feature_matches_char_subclass('Cleric', k_frag, char_sub):
                        cd_options.append(k_frag)
                opts_str = ', '.join(dict.fromkeys(cd_options))  # de-dupe, preserve order
                desc = (f"Use one Channel Divinity option: {opts_str}. {uses} use"
                        f"{'s' if uses != 1 else ''} per short or long rest.")
            elif feat_fragment == 'Wild Shape' and cls_name == 'Druid':
                from dnd_app.core.calculator import get_wild_shape_info
                info = get_wild_shape_info(char)
                if info:
                    display = f"Wild Shape (CR {info['max_cr']})"
                    desc = (f"Transform into a beast of challenge rating "
                            f"{info['max_cr']} or lower ({info['restriction']}). "
                            f"Action to transform back early. 2 uses per short or long rest.")
            elif feat_fragment == 'Blood Maledict' and cls_name == 'Blood Hunter':
                from dnd_app.core.calculator import get_hemocraft_die
                # PHB (BH) uses-per-rest: 1 at 1st, 2 at 6th, 3 at 13th, 4 at 17th.
                uses = 1 if char_lvl < 6 else 2 if char_lvl < 13 else 3 if char_lvl < 17 else 4
                die = get_hemocraft_die(char)
                known_curses = [c.split("–")[0].strip() for c in
                                char.get("_choices", {}).get("blood_hunter_curses", [])]
                curse_note = (f" Known: {', '.join(known_curses)}." if known_curses
                             else " (choose your known curses at level-up)")
                display = f"Blood Maledict ({uses}/rest)"
                desc = (f"Curse a creature within 30 ft with a known blood "
                        f"curse — free to invoke. You may optionally Amplify "
                        f"it by taking {die} necrotic damage (can't be "
                        f"reduced) for an added effect. {uses} use"
                        f"{'s' if uses != 1 else ''} per short or long rest."
                        f"{curse_note}")
            elif feat_fragment == 'Crimson Rite' and cls_name == 'Blood Hunter':
                from dnd_app.core.calculator import get_hemocraft_die
                die = get_hemocraft_die(char)
                # 1 rite known at 2nd level, 2nd rite at 7th, 3rd at 14th.
                rites_known = 1 if char_lvl < 7 else 2 if char_lvl < 14 else 3
                display = f"Crimson Rite ({die})"
                desc = (f"Activate one of your {rites_known} known rites on "
                        f"a weapon you hold: take {die} necrotic damage "
                        f"(can't be reduced), then your hits with it deal "
                        f"extra {die} damage of that rite's element until "
                        f"your next short or long rest.")
            buckets[bucket].append((display, desc, cls_name))

    # TCE optional class features: these 5 use existing resources (ki,
    # sorcery points, wild shape uses) rather than needing a new
    # resource pool, so they get real Actions tab entries here.
    if _optional_feature_enabled(char, "Steady Aim") and char_classes.get("Rogue", 0) >= 3:
        buckets["Bonus Action"].append((
            "Steady Aim", "Give yourself advantage on your next attack roll this turn. You "
            "must not have moved this turn; your speed is then 0 until the end of the turn.",
            "Rogue"))
    if _optional_feature_enabled(char, "Ki-Fueled Attack") and char_classes.get("Monk", 0) >= 3:
        buckets["Bonus Action"].append((
            "Ki-Fueled Attack", "If you spend 1+ ki points as part of your action this turn, "
            "make one attack with a monk weapon as a bonus action.", "Monk"))
    if _optional_feature_enabled(char, "Focused Aim") and char_classes.get("Monk", 0) >= 5:
        buckets["Reaction"].append((
            "Focused Aim", "When you miss with an attack roll, spend 1-3 ki points to increase "
            "that roll by 2 per ki point spent — potentially turning the miss into a hit.",
            "Monk"))
    if _optional_feature_enabled(char, "Quickened Healing") and char_classes.get("Monk", 0) >= 4:
        from dnd_app.core.calculator import get_martial_arts_die
        buckets["Action"].append((
            "Quickened Healing", f"Spend 2 ki points: roll your Martial Arts die "
            f"({get_martial_arts_die(char)}) and regain that many HP, plus your proficiency "
            f"bonus.", "Monk"))
    if _optional_feature_enabled(char, "Magical Guidance") and char_classes.get("Sorcerer", 0) >= 5:
        buckets["Reaction"].append((
            "Magical Guidance", "When you fail an ability check, spend 1 sorcery point to "
            "reroll the d20 — you must use the new roll.", "Sorcerer"))
    if _optional_feature_enabled(char, "Wild Companion") and char_classes.get("Druid", 0) >= 2:
        buckets["Action"].append((
            "Wild Companion", "Expend a use of Wild Shape to cast Find Familiar without "
            "material components; the familiar is a fey and disappears after hours equal to "
            "half your Druid level.", "Druid"))
    if _optional_feature_enabled(char, "Magical Inspiration") and char_classes.get("Bard", 0) >= 2:
        buckets["Passive"].append((
            "Magical Inspiration (passive)", "If a creature holding one of your Bardic "
            "Inspiration dice casts a spell that heals or deals damage, it can roll that die "
            "and add the result to the healing or damage — the die is then lost.", "Bard"))
    if _optional_feature_enabled(char, "Spellcasting Focus") and char_classes.get("Ranger", 0) >= 2:
        buckets["Passive"].append((
            "Spellcasting Focus (passive)", "You can use a druidic focus (sprig of mistletoe "
            "or holly, a wand/rod of special wood, a staff drawn from a living tree, etc.) as "
            "a spellcasting focus for your ranger spells.", "Ranger"))

    # Add active magic item abilities from equipped + attuned items.
    # ITEM_ACTIONS matches by substring of the item's catalog name (fragment
    # keys avoid apostrophes to dodge string-escaping pitfalls; display names
    # use the full proper name including apostrophes where needed).
    ITEM_ACTIONS = {
        # ── Wands / charged casters ──────────────────────────────────────────
        'Wand of Magic Missiles': ('Action','Wand of Magic Missiles (7 ch)','Cast Magic Missile using 1-7 charges. Regains 1d6+1 charges at dawn.'),
        'Wand of Fireballs':   ('Action','Wand of Fireballs (7 ch)','Cast Fireball (DC 15 DEX) using 1-7 charges.'),
        'Wand of Lightning':   ('Action','Wand of Lightning Bolts (7 ch)','Cast Lightning Bolt (DC 15 DEX) using 1-7 charges.'),
        'Wand of Fear':        ('Action','Wand of Fear (7 ch)','Frighten 60-ft cone (DC 15 WIS) or Command (1 ch).'),
        'Wand of Binding':     ('Action','Wand of Binding (7 ch)','Hold Monster (5 ch, DC 17) or Hold Person (2 ch).'),
        'Wand of Magic Detection': ('Action','Wand of Magic Detection (3 ch)','Cast Detect Magic. Regains 1d3 charges at dawn.'),
        'Wand of Secrets':     ('Action','Wand of Secrets (3 ch)','Detect nearest secret door/trap within 30 ft.'),
        'Wand of Web':         ('Action','Wand of Web (7 ch)','Cast Web (DC 15). Regains 1d6+1 charges at dawn.'),
        'Wand of Conducting':  ('Action','Wand of Conducting (3 ch)','Produce orchestral music for 1 minute.'),
        'Wand of Pyrotechnics':('Action','Wand of Pyrotechnics (7 ch)','Create a harmless firework display visible 60 ft away.'),
        'Wand of Scowls':      ('Action','Wand of Scowls (3 ch)','Force target to scowl (DC 10 CHA save) for 1 min.'),
        'Wand of Smiles':      ('Action','Wand of Smiles (3 ch)','Force target to smile (DC 10 CHA save) for 1 min.'),

        # ── Cosmetic / utility actions ───────────────────────────────────────
        'Circlet of Blasting': ('Action','Circlet of Blasting (1/day)','Cast Scorching Ray (+5 to hit, 3 rays, 2d6 fire each).'),
        'Cape of the Mountebank': ('Action','Cape of the Mountebank (1/day)','Cast Dimension Door. Leave a cloud of smoke.'),
        'Boots of Speed':      ('Bonus Action','Boots of Speed (10 min/LR)','Double walking speed, opportunity attacks against you have disadvantage.'),
        'Cloak of the Bat':    ('Bonus Action','Cloak of the Bat','In darkness: transform into a bat (fly 30 ft). Bonus action to revert.'),
        'Winged Boots':        ('Bonus Action','Winged Boots (4 hr/day)','Grow wings, gain fly speed equal to walk speed.'),
        'Masquerade Tattoo':   ('Action','Masquerade Tattoo','Cast Disguise Self at will (unlimited uses).'),
        'Hat of Disguise':     ('Action','Hat of Disguise','Cast Disguise Self at will.'),
        'Horn of Silent Alarm':('Action','Horn of Silent Alarm (4 ch)','Blow: one creature within 600 ft hears the alarm. Silent to all others.'),
        'Clockwork Amulet':    ('Action','Clockwork Amulet (1/day)','Replace attack roll d20 with a flat 10 result (modifiers still apply).'),
        'Cast-Off Armor':      ('Bonus Action','Cast-Off Armor','Doff this armor instantly as a bonus action.'),
        'Ring of Jumping':     ('Bonus Action','Ring of Jumping','Cast Jump on yourself at will (triple jump distance, 1 min).'),
        'Cloak of Billowing':  ('Bonus Action','Cloak of Billowing','Make the cloak billow dramatically (cosmetic).'),
        'Staff of Adornment':  ('Action','Staff of Adornment','Cause the floating object atop the staff to glow (1 charge).'),
        'Staff of Birdcalls':  ('Action','Staff of Birdcalls','Produce a bird call audible 60 ft away (1 charge).'),
        'Staff of Flowers':    ('Action','Staff of Flowers','Cause a flower to instantly bloom from earth (1 charge).'),
        'Medal of Muscle':     ('Bonus Action','Medal of Muscle (1/day)','Gain advantage on Strength checks and saves for 1 hour.'),
        'Medal of the Conch':  ('Bonus Action','Medal of the Conch (1/day)','Gain swim speed = walk speed for 1 hour.'),
        'Medal of the Horizonback': ('Reaction','Medal of the Horizonback (1/day)','+4 AC against one attack as a reaction.'),
        'Medal of the Maze':   ('Action','Medal of the Maze (1/day)','Advantage on Survival and know which way is north for 1 hour.'),
        'Medal of Wit':        ('Bonus Action','Medal of Wit (1/day)','Advantage on Intelligence checks and saves for 1 hour.'),

        # ── Detection / divination items ─────────────────────────────────────
        'Helm of Comprehending Languages': ('Action',"Helm of Comprehending Languages",'Cast Comprehend Languages at will.'),
        'Helm of Telepathy':   ('Action','Helm of Telepathy','Cast Detect Thoughts (DC 13). While focused, telepathy and Suggestion (1/day) available.'),
        'Eyes of Charming':    ('Action','Eyes of Charming (3 ch)','Cast Charm Person (DC 13) on a humanoid you can see.'),
        'Goggles of Object Reading': ('Action','Goggles of Object Reading (1/day)','Cast Identify as a 1-minute ritual by touching the object.'),
        "Inquisitive's Goggles": ('Action',"Inquisitive's Goggles (1/day)",'10 min: see invisible creatures.'),
        "Danoth's Visor":      ('Action',"Danoth's Visor (1/day)",'Cast True Seeing on yourself (1 hour, truesight extends to 120 ft).'),
        'Medallion of Thoughts': ('Action','Medallion of Thoughts (3 ch)','Cast Detect Thoughts (DC 13).'),
        'Psi Crystal':         ('Action','Psi Crystal (1/day)','Cast Detect Thoughts (DC 13) by holding and concentrating.'),
        'Lantern of Tracking': ('Bonus Action','Lantern of Tracking','Name a creature type: lantern flickers when one is within 300 ft.'),
        'Orb of Direction':    ('Action','Orb of Direction','Determine which way is north.'),
        'Orb of Time':         ('Action','Orb of Time','Determine the rough time of day.'),
        'Orb of Gonging':      ('Action','Orb of Gonging','Cause the orb to ring loudly for 10 minutes (or stop early).'),

        # ── Crowd control / combat items ─────────────────────────────────────
        'Gem of Brightness':   ('Action','Gem of Brightness','1 ch: bright light. 5 ch: blind cone (DC 15 CON). 10 ch: blind beam (DC 15 CON).'),
        'Pipes of Haunting':   ('Action','Pipes of Haunting (3 ch)','Frighten creatures within 30 ft (DC 13 WIS).'),
        'Pipes of the Sewers': ('Action','Pipes of the Sewers (3 ch)','Summon 1-3 rat swarms within 30 ft.'),
        'Skyblinder Staff':    ('Action','Skyblinder Staff (3 ch)','Cast Faerie Fire (DC 13).'),
        'Cube of Force':       ('Action','Cube of Force','Press a face (1-5 ch) to erect/alter a selective barrier; 0 ch deactivates.'),
        'Iron Flask':          ('Action','Iron Flask','Trap a CR 6 or lower elemental/fey/fiend/celestial within 30 ft (DC 17 CHA).'),
        'Helm of Disjunction':  ('Action','Helm of Disjunction (5 ch)',"Suppress a creature's magic items, a single item, or dispel a spell effect (DC 17)."),
        'Dried Leech':         ('Action','Dried Leech','Attach to weapon: on next hit, leech drains 1d4 CON/turn (DC 12 CON) until removed.'),
        'Dust of Disappearance': ('Action','Dust of Disappearance','Scatter: you and creatures within 10 ft turn invisible for 2d4 minutes.'),
        'Dust of Dryness':     ('Action','Dust of Dryness','Sprinkle a pinch over water: absorb up to 15 gallons into a pellet.'),
        'Coiling Grasp Tattoo': ('Action','Coiling Grasp Tattoo','Attempt to grapple a creature within 30 ft (contested Athletics check).'),

        # ── Summons / mounts ──────────────────────────────────────────────────
        'Robe of Serpents':    ('Bonus Action','Robe of Serpents (1/day)','Pull a snake free: becomes a giant poisonous snake ally for 1 hour.'),
        'Staff of the Python': ('Action','Staff of the Python','Throw the staff: becomes a giant constrictor snake ally.'),

        # ── Social / charm items ──────────────────────────────────────────────
        'Ring of the Orator':  ('Action','Ring of the Orator (1/day)','Cast Charm Person (DC 14).'),
        'Ring of Truth Telling': ('Action','Ring of Truth Telling (1/day)','Cast Zone of Truth (DC 14).'),
        "Card Sharp's Deck":   ('Bonus Action',"Card Sharp's Deck",'Throw a card (your attack bonus): 1d4 + DEX slashing damage. Once/turn.'),
        'Boomerang Shield':    ('Action','Boomerang Shield','Throw shield (your attack bonus): 1d4 + STR bludgeoning. Returns to hand.'),

        # ── Earth / nature themed actions ────────────────────────────────────
        'Ironfang':            ('Action','Ironfang (1/day)','Cast Earthquake (DC 17) by striking the ground.'),
        "Stonebreaker's Breastplate": ('Action',"Stonebreaker's Breastplate (1/day)",'Cast Earthquake (DC 17) centered on yourself.'),
        'Mask of the Beast':   ('Action','Mask of the Beast (1/day)','Cast Speak with Animals as a ritual.'),
        'Propeller Helm':      ('Bonus Action','Propeller Helm','Activate: fly speed 10 ft for 1 minute.'),
        'Pixie Dust':          ('Action','Pixie Dust','Sprinkle on a creature: flying speed 30 ft for 1 minute.'),

        # ── Defensive reactions ────────────────────────────────────────────────
        'Gloves of Missile Snaring': ('Reaction','Gloves of Missile Snaring','Reduce ranged weapon damage by 1d10 + DEX. Catch the missile if reduced to 0.'),

        # ── Big-ticket Legendary / Artifact actions ──────────────────────────
        'Holy Symbol of Ravenkind': ('Action','Holy Symbol of Ravenkind (1/day)','30-ft sunlight burst for 1 minute, or 20 radiant burst vs. one vampire.'),
        'Eye and Hand of Vecna': ('Action','Eye/Hand of Vecna (1/day each)','Eye: Disintegrate (DC 18). Hand: Finger of Death (DC 18).'),
        'Wand of Orcus':       ('Action','Wand of Orcus','Animate Dead at will. 1 ch: Create Undead. 3 ch: Circle of Death (DC 18). 7 ch: Power Word Kill.'),
        'Spell Bottle':        ('Action','Spell Bottle (1/day)','Release the spell stored within, cast at your stored save DC/attack bonus.'),
        'Crown of Lies':       ('Action','Crown of Lies (1/day)','Dominate a creature that can hear you speak (DC 20 WIS).'),
        'Wreath of the Prism': ('Action','Wreath of the Prism (1/day)','Cast Prismatic Wall (DC 18) centered on a point within 60 ft.'),
        'Verminshroud':        ('Action','Verminshroud (3/day)','Transform into a swarm of rats for up to 1 hour.'),
        'Sword of the Planes': ('Action','Sword of the Planes (1/day)','Cast Plane Shift (DC 15) on yourself and up to 8 willing creatures.'),
        'Tome of the Stilled Tongue': ('Action','Tome of the Stilled Tongue (1/day)','Cast a prepared spell of 5th level or lower without expending a slot.'),
        'Spindle of Fate':     ('Action','Spindle of Fate (7 ch)','Cut one strand of fate: end a curse or fate-bound effect on a creature within 30 ft.'),
        'Wyrmskull Throne':    ('Action','Wyrmskull Throne (1/day)','Cast Clairvoyance at will while seated; dragons within 1 mile must save vs. charm.'),
    }
    covered_sources = set()
    for _ia in char.get('item_actions', []):
        covered_sources.add(_ia.get('source',''))
    for _d in char.get('item_granted_spell_details', []):
        covered_sources.add(_d.get('source',''))

    # Use the same equip+attune gating as the rest of the magic item system,
    # so an item requiring attunement only shows here while actually attuned.
    from dnd_app.core.magic_items import _active_item_names
    for iname in _active_item_names(char):
        if iname in covered_sources:
            continue  # already added via a structured effect below
        for fragment, action_data in ITEM_ACTIONS.items():
            if action_data and fragment.lower() in iname.lower():
                bucket, display, desc = action_data
                buckets[bucket].append((display, desc, iname))
                break

    # ── Structured effects: items with a grant_spell or grant_action entry ────
    # (Spells granted this way are intentionally NOT added to the character's
    # spell list — they appear only here, since they're cast via the item.)
    for _d in char.get('item_granted_spell_details', []):
        spell = _d['spell']; source = _d['source']
        uses = _d.get('uses', 0)
        recharge = _d.get('recharge', 'dawn')
        action_type = _d.get('action_type', 'Action')
        uses_str = f" ({uses} ch, recharges {recharge})" if uses else " (at will)"
        desc = f"Cast {spell}{uses_str}, using the item's own save DC/attack bonus."
        buckets[action_type].append((f"{spell} ({source})", desc, source))

    for _ia in char.get('item_actions', []):
        action_type = _ia.get('action_type', 'Passive')
        buckets[action_type].append((_ia.get('name','Special'), _ia.get('description',''), _ia.get('source','')))

    # ── Passive numeric/stat effects (AC, saves, spell DC/attack, resistance,
    # ability score bonuses, initiative/skill advantage, etc.) ────────────────
    # get_item_effect() results for these types are fully applied to
    # char state (AC, spell DC, resistances...) but aren't otherwise
    # summarized anywhere in the Known Actions / Passive tab, so a
    # player attuning to, say, a +2 AC/spell-attack staff can see which
    # item is responsible. This block doesn't duplicate the
    # grant_action/grant_spell entries above; it only describes the
    # effect types nothing else already narrates.
    from dnd_app.data.phbCommon.magic_items import get_item_effect as _get_item_effect

    def _describe_passive_effect(sub, char, item_name):
        t = sub.get('type')
        if t == 'ac_bonus':
            v = sub.get('value', 0)
            parts = [f"+{v} bonus to AC"] if v else []
            sb = sub.get('save_bonus', 0)
            if sb:
                parts.append(f"+{sb} bonus to saving throws")
            return " and ".join(parts) if parts else None
        if t == 'save_bonus':
            v = sub.get('value', 0)
            return f"+{v} bonus to saving throws" if v else None
        if t == 'spell_dc_bonus':
            v = sub.get('value', 0)
            atk = sub.get('atk_bonus', 0)
            if atk:
                return f"+{v} bonus to spell attack rolls and spell save DC"
            return f"+{v} bonus to spell save DC" if v else None
        if t == 'spell_attack_bonus':
            v = sub.get('value', 0)
            return f"+{v} bonus to spell attack rolls" if v else None
        if t == 'weapon_attack_bonus':
            v = sub.get('value', 0)
            return f"+{v} bonus to attack and damage rolls" if v else None
        if t == 'weapon_damage_bonus':
            v = sub.get('value', 0)
            wt = sub.get('weapon_type', 'weapon')
            return f"+{v} bonus to damage rolls with {wt} weapons" if v else None
        if t == 'set_ability':
            return f"Your {sub.get('ability','?')} score is {sub.get('value','?')} (unless already higher)"
        if t == 'ability_bonus':
            cap = sub.get('cap')
            cap_str = f", to a maximum of {cap}" if cap else ""
            return f"+{sub.get('value',0)} bonus to your {sub.get('ability','?')} score{cap_str}"
        if t == 'prof_bonus':
            return f"+{sub.get('value',0)} bonus to your proficiency bonus"
        if t == 'speed_bonus':
            v = sub.get('value', 0)
            return f"+{v} ft. to your speed" if v else None
        if t == 'min_speed':
            return f"Your speed is at least {sub.get('value',0)} ft."
        if t in ('swim_speed', 'climb_speed', 'fly_speed'):
            kind = {'swim_speed': 'swimming', 'climb_speed': 'climbing', 'fly_speed': 'flying'}[t]
            v = sub.get('value')
            v_str = "equal to your walking speed" if v == 'walking' else f"of {v} ft"
            return f"You have a {kind} speed {v_str}"
        if t == 'resistance':
            return f"Resistance to {sub.get('damage_type','?')} damage"
        if t == 'immunity':
            return f"Immunity to {sub.get('damage_type','?')} damage"
        if t == 'condition_immunity':
            return f"Immunity to the {sub.get('condition','?')} condition"
        if t == 'advantage_save':
            ab = sub.get('ability', 'all')
            return "Advantage on all saving throws" if ab == 'all' else f"Advantage on {ab} saving throws"
        if t == 'initiative_advantage':
            return "Advantage on initiative rolls"
        if t == 'skill_advantage':
            return f"Advantage on {sub.get('skill','?')} checks"
        if t == 'skill_disadvantage':
            return f"Disadvantage on {sub.get('skill','?')} checks"
        if t == 'resistance_choice':
            picks = char.get('_choices', {}).get(f'item_dmgtype_{item_name}', [])
            dtype = picks[0] if picks else "a damage type (choose one on the Gear tab)"
            return f"Resistance to {dtype} damage"
        if t == 'senses':
            return f"You have {sub.get('sense','?')} out to {sub.get('value',0)} ft. (or +{sub.get('value',0)} ft. if you already have it)"
        if t == 'hp_max_bonus':
            if sub.get('formula') == '10_plus_level':
                return "Your hit point maximum increases by 10 + your level"
            return f"+{sub.get('value',0)} bonus to your hit point maximum"
        return None

    for _iname in _active_item_names(char):
        _effect = _get_item_effect(_iname)
        if not _effect:
            continue
        _sub_list = _effect if isinstance(_effect, list) else [_effect]
        _lines = []
        for _sub in _sub_list:
            _text = _describe_passive_effect(_sub, char, _iname)
            if _text:
                _lines.append(_text)
        if _lines:
            buckets['Passive'].append((_iname, "; ".join(_lines) + ".", _iname))

    # ── Feat-granted abilities ─────────────────────────────────────────────────
    # Feats have no equip/attune gating — once taken, they're always active.
    FEAT_ACTIONS = {
        # ── Bonus Action feats ───────────────────────────────────────────────
        'Charger':           ('Bonus Action','Charger','After Dashing: melee attack +5 damage, or shove 10 ft.'),
        'Great Weapon Master': ('Bonus Action','Great Weapon Master','On a crit or kill with a heavy weapon: one bonus action melee attack.'),
        'Polearm Master':     ('Bonus Action','Polearm Master','Butt-end attack: 1d4 + STR bludgeoning (spear/glaive/halberd/pike/quarterstaff).'),
        'Shield Master':      ('Bonus Action','Shield Master','Shove a creature with your shield after taking the Attack action.'),
        'Tavern Brawler':     ('Bonus Action','Tavern Brawler (Grapple)','Attempt to grapple a creature as a bonus action after an unarmed strike hit.'),
        'Telekinetic':        ('Bonus Action','Telekinetic Shove','Shove a creature up to 5 ft (STR save vs. 8+prof+CHA/INT/WIS) within 30 ft.'),
        'Gift of the Chromatic Dragon': ('Bonus Action','Chromatic Infusion (1/LR)','Add 1d4 of your chosen damage type to a weapon for 1 minute.'),
        'Strike of the Giants': ('Bonus Action','Giant Strike (1/SR)','On hit: infuse the attack with chosen Giant power (push, slow, etc.).'),
        'Ember of the Fire Giant': ('Bonus Action','Fire Giant Strike (1/SR)','On hit: ignite the area, creatures take fire damage.'),
        'Fury of the Frost Giant': ('Bonus Action','Frost Giant Strike (1/SR)','On hit: reduce target speed to 0 until your next turn.'),
        'Guile of the Cloud Giant': ('Bonus Action','Cloud Giant Strike (1/SR)','On hit: teleport up to 30 ft with the target.'),
        'Keenness of the Stone Giant': ('Bonus Action','Stone Giant Strike (1/SR)','On hit: push the target and knock it prone.'),
        'Soul of the Storm Giant': ('Bonus Action','Storm Giant Strike (1/SR)','On hit: deal extra lightning damage and teleport the target.'),
        'Vigor of the Hill Giant': ('Bonus Action','Hill Giant Strike (1/SR)','On hit: push the target up to 10 ft away.'),
        'Knight of the Crown': ('Bonus Action','Knight of the Crown','On hit with Attack action: one additional weapon attack.'),
        # These 5 feats have accurate descriptions but no other mechanical presence in the app.
        'Vital Sacrifice': ('Bonus Action','Vital Sacrifice',
            "Take 1d6 necrotic damage (can't be reduced) for a blood boon lasting 1 hour or until "
            "spent. Spend it: +1d6 on an attack roll; +2d6 necrotic damage on a hit with an attack "
            "or spell; or reduce a creature's STR/DEX/CON saving throw by 1d4."),
        'Opportunistic Thief': ('Reaction','Opportunistic Thief',
            "When a creature misses you with a melee attack: DEX (Sleight of Hand) check (DC 10 + "
            "its DEX modifier) to steal an item it's not holding or wearing."),
        'Scourge Master': ('Bonus Action','Scourge Master',
            "Hitting with a whip or tetherhooks: bonus action, STR or DEX check vs. the target's "
            "STR check to disarm a shield or held item, dropping it between you. You can also use "
            "your whip/tetherhooks to pull a sub-1-lb item within reach back to yourself."),

        # ── Passive-style feats (trigger conditions, not activated actions) ──
        'Remarkable Recovery': ('Passive','Remarkable Recovery (passive)',
            "Stabilizing while dying also regains HP equal to your CON modifier (min 1). Regaining "
            "HP from a spell, potion, or class feature (not this feat) regains that much extra HP "
            "again."),
        'Speech of the Ancient Beasts': ('Passive','Speech of the Ancient Beasts (passive)',
            "Large-or-larger beasts are friendly to you unless attacked, and you have advantage on "
            "CHA checks against them. You can speak and understand Giant Eagle, Giant Elk, and "
            "Giant Owl; any Large-or-larger beast can otherwise understand you."),
        'Spelldriver': ('Passive','Spelldriver (passive)',
            "When you cast a 1st-level+ spell as a bonus action, you can also cast another "
            "1st-level+ spell with your action that turn. If casting two or more spells in one "
            "turn this way, at most one can be 3rd level or higher."),

        # ── Passive combat-modifier feats ─────────────────────────────
        'Crossbow Expert':    ('Passive','Crossbow Expert',
            "Ignore the loading property of crossbows you're proficient with. Being within 5 ft. "
            "of a hostile creature doesn't impose disadvantage on your ranged attack rolls. When "
            "you attack with a one-handed weapon, bonus action: attack with a hand crossbow you're holding."),
        'Dual Wielder':       ('Passive','Dual Wielder',
            "+1 AC while wielding two melee weapons. Can use two-weapon fighting even if the "
            "weapons aren't light. Can draw/stow two one-handed weapons when you'd normally draw/stow one."),
        'Sharpshooter':       ('Passive','Sharpshooter',
            "Attacking at long range doesn't impose disadvantage. Ranged weapon attacks ignore "
            "half and three-quarters cover. Before a ranged weapon attack you're proficient with: "
            "can take -5 to the attack roll for +10 damage if it hits."),
        'Gunner':             ('Passive','Gunner',
            "Proficient with all firearms. Ignore the loading property of firearms. Being within "
            "5 ft. of a hostile creature doesn't impose disadvantage on your ranged attack rolls "
            "with firearms."),
        'Spell Sniper':       ('Passive','Spell Sniper',
            "Attack-roll spells you cast have their range doubled. Spell attacks ignore half and "
            "three-quarters cover. You learn one attack-roll cantrip from the Wizard/Cleric/Druid/"
            "Sorcerer/Warlock list."),
        'Savage Attacker':    ('Passive','Savage Attacker',
            "Once per turn when you roll damage for a melee weapon attack, you can reroll the "
            "weapon's damage dice and use either total."),
        'Piercer':            ('Passive','Piercer',
            "Once per turn on a hit with a piercing-damage weapon: reroll one damage die (or two "
            "on a crit), use either. +1 STR or DEX."),
        'Crusher':            ('Passive','Crusher',
            "Once per turn on a hit with bludgeoning damage: move the target 5 ft. (if Large or "
            "smaller). On a crit with bludgeoning: attacks against that creature have advantage "
            "until your next turn. +1 STR or CON."),
        'Slasher':            ('Passive','Slasher',
            "Once per turn on a hit with slashing damage: reduce the target's speed by 10 ft. "
            "until your next turn. On a crit with slashing: target has disadvantage on attack "
            "rolls until your next turn. +1 STR or DEX."),
        'Mounted Combatant':  ('Passive','Mounted Combatant',
            "Advantage on melee attack rolls against an unmounted creature smaller than your "
            "mount. Can force an attack targeting your mount to target you instead. If your mount "
            "is subjected to an effect allowing a DEX save for half damage, it takes none on a "
            "success and half on a failure."),
        'Inspiring Leader':   ('Action','Inspiring Leader',
            "Spend 10 minutes inspiring up to 6 companions within 30 ft. who can see/hear you — "
            "each gains temp HP equal to your level + CHA mod. Can't use on the same creature "
            "twice until it finishes a short or long rest."),
        'War Caster':         ('Passive','War Caster',
            "Advantage on CON saves to maintain concentration. Perform spells' somatic components "
            "even with weapons/a shield in your hands. Can cast a spell (instead of a melee "
            "attack) as your opportunity attack."),
        'Skulker':            ('Passive','Skulker',
            "Can hide when only lightly obscured. Missing with a ranged attack doesn't reveal "
            "your position. Dim light doesn't impose disadvantage on sight-based Perception checks."),
        'Dungeon Delver':     ('Passive','Dungeon Delver',
            "Advantage on checks to detect secret doors/traps, and on saves to avoid/resist them. "
            "Resistance to trap damage. Can search for traps at a normal pace, not just searching pace."),

        # ── Reaction feats ───────────────────────────────────────────────────
        'Defensive Duelist':  ('Reaction','Defensive Duelist','When hit by a melee attack (finesse weapon equipped): add proficiency bonus to AC.'),
        'Mage Slayer':        ('Reaction','Mage Slayer','Melee attack against a caster within 5 ft who casts a spell.'),
        'Bountiful Luck':     ('Reaction','Bountiful Luck','Ally within 30 ft rolls a 1: they reroll instead.'),
        'Fade Away':          ('Reaction','Fade Away','When you take damage: become invisible until the start of your next turn.'),
        'Flames of Phlegethos': ('Reaction','Flame Shield','When hit by a melee attack: attacker takes fire damage.'),
        'Second Chance':      ('Reaction','Second Chance','When hit by an attack: force the attacker to reroll.'),
        'Gift of the Gem Dragon': ('Reaction','Telekinetic Reprisal (1/LR)','When you take damage: 20-ft burst, STR save or be pushed and take force damage.'),
        'Sentinel':           ('Reaction','Sentinel (enhanced OA)','Opportunity attacks reduce speed to 0; trigger even on Disengage.'),

        # ── Action feats ──────────────────────────────────────────────────────
        'Grappler':           ('Action','Grappler (Pin)','While grappling a creature: attempt to pin it (both restrained).'),
        'Healer':              ('Action','Healer (Kit)',"Use a healer's kit to restore HP to a creature (1d6 + their max HD spent + your bonus)."),

        # ── Spell-granting feats (cast via the feat, not added to spell list) ──
        'Magic Initiate':     ('Action','Magic Initiate (1/LR)','Cast your chosen 1st-level spell from the feat once per long rest, or at-will as a cantrip.'),
        'Drow High Magic':    ('Action','Drow High Magic','Detect Magic at will. Levitate and Dispel Magic each once per long rest.'),
        'Fey Teleportation':  ('Action','Fey Teleportation (1/SR)','Cast Misty Step once per short rest.'),
        'Wood Elf Magic':     ('Action','Wood Elf Magic (1/LR each)','Cast Longstrider and Pass Without Trace, each once per long rest.'),
        'Telepathic':         ('Action','Telepathic (1/LR)','Cast Detect Thoughts once per long rest. Telepathic communication within 60 ft at will.'),
        'Tracker':            ('Bonus Action','Tracker (1/LR)',"Cast Hunter's Mark once per long rest without using a spell slot."),
        'Fey Touched':        ('Action','Fey Touched (1/LR each)','Cast Misty Step and your chosen Divination/Enchantment spell, each once per long rest.'),
        'Shadow Touched':     ('Action','Shadow Touched (1/LR each)','Cast Invisibility and your chosen Illusion/Necromancy spell, each once per long rest.'),
        'Artificer Initiate': ('Action','Artificer Initiate (1/LR)','Cast your chosen 1st-level Artificer spell once per long rest, or at-will as a cantrip.'),
        'Aberrant Dragonmark': ('Action','Aberrant Dragonmark (1/LR)','Cast your chosen cantrip at will and 1st-level spell once per long rest (CON-based).'),
        'Strixhaven Initiate': ('Action','Strixhaven Initiate (1/LR)','Cast your chosen 1st-level college spell once per long rest, or the cantrips at-will.'),
        'Divinely Favored':   ('Action','Divinely Favored (1/LR)','Cast your chosen 1st-level cleric spell once per long rest, or the cantrip at-will.'),
        'Gift of the Metallic Dragon': ('Action','Draconic Healing','Cast Cure Wounds a number of times per long rest equal to half your proficiency bonus.'),
        'Squire of Solamnia': ('Action','Lay On Hands (SR)','Heal HP from a 5-HP pool that refills on a short rest.'),
        'Initiate of High Sorcery': ('Action','Wizard Cantrip','Cast your chosen wizard cantrip at will.'),
    }
    covered_feat_sources = set()  # avoid double-listing if a feat ever gets a structured effect
    for fname in char.get('feats', []):
        if fname in covered_feat_sources:
            continue
        for fragment, action_data in FEAT_ACTIONS.items():
            if action_data and fragment.lower() in fname.lower():
                bucket, display, desc = action_data
                desc = _resolve_dynamic_combat_text(char, desc)
                buckets[bucket].append((display, desc, fname))
                break

    # Add universal abilities
    from dnd_app.core.calculator import get_extra_attacks
    from dnd_app.core.character import class_levels, subclasses
    _n_attacks = get_extra_attacks(class_levels(char), subclasses(char), char)
    if _n_attacks <= 1:
        _atk_desc = "Make one weapon or unarmed attack."
    else:
        _atk_desc = f"Make {_n_attacks} attacks (Extra Attack) as part of this one action."
    _wiz_sub = next((c.get("subclass","") for c in char.get("classes",[])
                     if c.get("class")=="Wizard"), "")
    _wiz_lvl = class_levels(char).get("Wizard", 0)
    if "bladesing" in _wiz_sub.lower() and _wiz_lvl >= 6:
        _atk_desc += " Bladesong: you can replace one of these attacks with a cantrip."
    buckets['Action'].insert(0, ('Attack', _atk_desc, 'Universal'))
    # "Cast a Spell" and "End Concentration" are only added for
    # characters with actual known/prepared spells, not unconditionally
    # for every character — this correctly covers multiclass and
    # partial-caster edge cases without needing a hardcoded class list.
    from dnd_app.data.phbCommon.spells import get_spell as _gs_action
    _known_spell_names = set(char.get("spells_known", [])) | set(char.get("spells_prepared", []))
    _has_any_spell = bool(_known_spell_names)
    _has_concentration_spell = any(
        (_sp := _gs_action(_n)) and _sp.get("concentration") for _n in _known_spell_names
    )
    if _has_any_spell:
        buckets['Action'].append(('Cast a Spell','Cast a spell with a casting time of 1 action.', 'Universal'))
    buckets['Action'].append(('Dash','Double your movement speed this turn.', 'Universal'))
    buckets['Action'].append(('Disengage','Your movement does not provoke opportunity attacks this turn.', 'Universal'))
    buckets['Action'].append(('Dodge','Until next turn: attackers have disadv, you have adv on DEX saves.', 'Universal'))
    buckets['Action'].append(('Help','Give ally adv on ability check or attack roll.', 'Universal'))
    buckets['Action'].append(('Hide','Make Stealth check to become hidden.', 'Universal'))
    buckets['Action'].append(('Ready','Prepare a reaction to a specified trigger.', 'Universal'))
    buckets['Action'].append(('Search','Make Perception/Investigation check.', 'Universal'))
    buckets['Action'].append(('Use Object','Interact with an object that requires an action.', 'Universal'))
    buckets['Action'].append(('Escape a Grapple',
        'STR (Athletics) or DEX (Acrobatics) check (your choice) contested by the grappler\'s '
        'STR (Athletics) check.', 'Universal'))
    buckets['Action'].append(('Stabilize a Creature',
        'DC 10 WIS (Medicine) check to stabilize an unconscious, dying creature (0 HP, failing '
        'death saves).', 'Universal'))
    buckets['Action'].append(('Don or Doff a Shield',
        'Put on or remove a shield.', 'Universal'))
    if _has_concentration_spell or char.get("concentration", {}).get("spell"):
        buckets['Passive'].append(('End Concentration',
            'Free action, any time: voluntarily end your concentration on a spell.', 'Universal'))
    buckets['Action'].append(('Activate an Item',
        'Some magic items require an action to activate (command word, drinking a potion, reading '
        'a scroll, etc.) — check the item\'s own description for specifics.', 'Universal'))
    if char.get("optional_rules", {}).get("dmg_xge_optional_actions", True):
        buckets['Action'].append(('Disarm (optional rule, DMG)',
            'Weapon attack roll contested by the target\'s STR (Athletics) or DEX (Acrobatics) check — '
            'no damage on a win, but the target drops the item. Disadvantage on your roll if they hold '
            'it with two hands; they have advantage/disadvantage on their check if larger/smaller than you.',
            'Universal'))
        buckets['Action'].append(('Overrun (optional rule, DMG)',
            'Action or bonus action: STR (Athletics) check contested by a blocking creature\'s STR '
            '(Athletics) check to force your way through its space this turn. Advantage/disadvantage '
            'if you\'re larger/smaller than it.', 'Universal'))
        buckets['Action'].append(('Tumble (optional rule, DMG)',
            'Action or bonus action: DEX (Acrobatics) check contested by a blocking creature\'s DEX '
            '(Acrobatics) check to move through its space this turn.', 'Universal'))
        buckets['Action'].append(('Shove Aside (optional rule, DMG)',
            'Shove variant: STR (Athletics) check (with disadvantage) contested by the target\'s STR '
            '(Athletics) or DEX (Acrobatics) check — on a win, move it 5 ft. sideways into a different '
            'space within your reach, rather than away from you.', 'Universal'))
        buckets['Action'].append(('Climb onto a Bigger Creature (optional rule, DMG)',
            'STR (Athletics) or DEX (Acrobatics) check contested by a larger creature\'s DEX '
            '(Acrobatics) check to move into and cling to its space; you have advantage on attacks '
            'against it while there.', 'Universal'))
        buckets['Action'].append(('Identify a Spell (optional rule, XGE)',
            'Reaction (as it\'s cast) or action (after, by its effect): INT (Arcana) check, DC 15 + the '
            'spell\'s level. Advantage if it was cast by a member of your own class.', 'Universal'))
        buckets['Reaction'].append(('Mark (optional rule, DMG)',
            'On a melee hit: mark the target — your opportunity attacks against it have advantage '
            'until the end of your next turn (doesn\'t cost your reaction to make).', 'Universal'))
        buckets['Passive'].append(('Waking Someone (optional rule, XGE)',
            'Action to shake/slap a naturally sleeping creature awake, or any damage/sudden loud noise '
            'wakes it automatically.', 'Universal'))
        buckets['Action'].append(('Healing Surge (optional rule, DMG)',
            'Spend up to half your Hit Dice at once (roll each + CON mod, heal the total) — once per '
            'short or long rest. An alternate way to spend the same Hit Dice pool tracked elsewhere on '
            'this sheet, not an extra pool of its own.', 'Universal'))


    # ── Tool special uses ────────────────────────────────────────────────────
    # Only shown when the character has BOTH the tool proficiency AND the
    # matching physical tool item in their equipment — per user instruction,
    # since the source text doesn't otherwise specify a further condition.
    TOOL_SPECIAL_USES = {
        "Alchemist's supplies": [("Alchemical Crafting", "As part of a long rest, make one dose of "
            "acid, alchemist's fire, antitoxin, oil, perfume, or soap (spend gp on raw materials).")],
        "Brewer's supplies": [("Potable Water", "Purify up to 6 gallons of water on a long rest, "
            "or 1 gallon on a short rest.")],
        "Calligrapher's supplies": [("Decipher Treasure Map", "INT check to determine a map's age, "
            "hidden messages, or similar facts.")],
        "Carpenter's tools": [
            ("Fortify", "1 minute + materials: increase a door/window's DC to force open by 5."),
            ("Temporary Shelter", "As part of a long rest, build a lean-to (collapses 1d3 days later)."),
        ],
        "Cartographer's tools": [("Craft a Map", "Draw a map while traveling, without using up "
            "other activity.")],
        "Cobbler's tools": [
            ("Maintain Shoes", "As part of a long rest, repair up to 6 creatures' shoes — for the "
             "next 24 hours they can travel 10 hrs/day without exhaustion saves."),
            ("Craft Hidden Compartment", "8 hours of work adds a hidden compartment to a shoe."),
        ],
        "Cook's utensils": [("Prepare Meals", "As part of a short rest, you and up to 5 creatures "
            "regain 1 extra HP per Hit Die spent that rest.")],
        "Disguise kit": [("Create Disguise", "As part of a long rest, create a disguise (1 minute "
            "to don once made).")],
        "Forgery kit": [("Quick Fake", "As part of a short rest, forge a 1-page document; as part "
            "of a long rest, up to 4 pages.")],
        "Glassblower's tools": [("Identify Weakness", "1 minute of study finds a glass object's "
            "weak point — damage striking it is doubled.")],
        "Herbalism kit": [("Identify Plants", "Quickly identify most plants by appearance/smell.")],
        "Jeweler's tools": [("Identify Gems", "Identify gems and their value at a glance.")],
        "Vehicles (land)": [("Vehicle Handling", "While piloting, add your proficiency bonus to "
            "the vehicle's AC and saving throws.")],
        "Vehicles (water)": [("Vehicle Handling", "While piloting, add your proficiency bonus to "
            "the vehicle's AC and saving throws.")],
        "Vehicles (air)": [("Vehicle Handling", "While piloting, add your proficiency bonus to "
            "the vehicle's AC and saving throws.")],
        "Leatherworker's tools": [("Identify Hides", "Determine a hide/leather item's source and "
            "any treatment techniques used.")],
        "Mason's tools": [("Demolition", "Spot weak points in brick walls, dealing double weapon "
            "damage to such structures.")],
        "Navigator's tools": [("Sighting", "Careful measurements determine your position on a "
            "nautical chart and the time of day.")],
        "Painter's supplies": [("Painting and Drawing", "As part of a short or long rest, produce "
            "a simple work of art.")],
        "Poisoner's kit": [("Handle Poison", "Handle and apply a poison without risk of exposing "
            "yourself.")],
        "Potter's tools": [("Reconstruction", "Examine pottery shards to determine an object's "
            "original form and purpose.")],
        "Smith's tools": [("Repair", "With an open flame, restore 10 HP to a damaged metal object "
            "per hour of work.")],
        "Thieves' tools": [("Set a Trap", "As part of a short rest, craft a trap from items on "
            "hand; your check total becomes the DC to discover/disable it.")],
        "Tinker's tools": [("Repair", "Restore 10 HP to a damaged object per hour of work (metal "
            "objects need an open flame).")],
        "Weaver's tools": [
            ("Repair (Cloth)", "As part of a short rest, repair one damaged cloth object."),
            ("Craft Clothing", "Given cloth/thread, create an outfit as part of a long rest."),
        ],
        "Woodcarver's tools": [
            ("Repair (Wood)", "As part of a short rest, repair one damaged wooden object."),
            ("Craft Arrows", "As part of a short rest craft up to 5 arrows, or up to 20 on a long rest."),
        ],
    }
    owned_item_names = {e.get("name","") for e in char.get("equipment", [])}
    for tool_name, uses in TOOL_SPECIAL_USES.items():
        if tool_name in char.get("tool_proficiencies", []) and tool_name in owned_item_names:
            for use_name, use_desc in uses:
                buckets['Passive'].append((f"{use_name} ({tool_name})", use_desc, 'Tool'))

    # ── Musical instrument / gaming set special uses (name-matched against
    # owned equipment individually, since these are specific instruments/
    # games rather than one fixed tool name) ─────────────────────────────────
    from dnd_app.data.phbCommon.items import INSTRUMENT_TOOLS, GAMING_SETS
    for inst in INSTRUMENT_TOOLS:
        if inst in char.get("tool_proficiencies", []) and inst in owned_item_names:
            buckets['Passive'].append((f"Compose a Tune ({inst})",
                "As part of a long rest, compose a new tune and lyrics.", 'Tool'))
    from dnd_app.core.calculator import get_prof_bonus, ability_mod
    _grapple_shove_dc = 8 + get_prof_bonus(char) + ability_mod(char, "STR")
    buckets['Action'].append(('Grapple',
        f"Unarmed Strike option: target (no more than one size larger) makes a STR or DEX save "
        f"(its choice) vs. DC {_grapple_shove_dc}, or is grappled. Requires a free hand.", 'Universal'))
    buckets['Action'].append(('Shove',
        f"Unarmed Strike option: target (no more than one size larger) makes a STR or DEX save "
        f"(its choice) vs. DC {_grapple_shove_dc}, or is pushed 5 ft. or knocked prone (your choice).", 'Universal'))
    # Telekinetic: bonus-action telekinetic shove — only shown if the
    # character actually has the feat. DC uses the highest of INT/WIS/CHA
    # as a stand-in for "the ability increased by this feat," since the
    # app doesn't track which specific ability an ASI came from.
    if "Telekinetic" in char.get("feats", []):
        _tk_mod = max(ability_mod(char, a) for a in ("INT", "WIS", "CHA"))
        _tk_dc = 8 + get_prof_bonus(char) + _tk_mod
        buckets['Bonus Action'].append(('Telekinetic Shove',
            f"Telekinetically shove a creature within 30 ft.: STR save vs. DC {_tk_dc} or move "
            f"5 ft. toward or away from you (it can willingly fail).", 'Telekinetic'))

    # Polearm Master: gated on actually wielding a qualifying polearm, not just knowing the feat.
    if "Polearm Master" in char.get("feats", []):
        _pm_weapons = {"Glaive", "Halberd", "Quarterstaff", "Pike", "Spear"}
        _pm_equipped = _pm_weapons & set(w.split(" +")[0].strip() for w in char.get("equipped_weapons", []))
        if _pm_equipped:
            _pm_mod = ability_mod(char, "STR" if ability_mod(char, "STR") >= ability_mod(char, "DEX") else "DEX")
            buckets['Bonus Action'].append(('Butt End Strike',
                f"Attack with the other end of your {next(iter(_pm_equipped)).lower()}: "
                f"1d4{f'+{_pm_mod}' if _pm_mod>=0 else _pm_mod} bludgeoning.", 'Polearm Master'))
        buckets['Passive'].append(('Polearm Reach',
            "While wielding a glaive/halberd/pike/quarterstaff/spear, other creatures provoke "
            "an opportunity attack from you on entering your reach (not just leaving it).",
            'Polearm Master'))

    # Sentinel.
    if "Sentinel" in char.get("feats", []):
        buckets['Passive'].append(('Sentinel',
            "Hitting with an opportunity attack reduces the target's speed to 0 for the rest "
            "of the turn. Creatures provoke your opportunity attacks even after Disengaging.",
            'Sentinel'))
        buckets['Reaction'].append(('Sentinel Retaliation',
            "When a creature within 5 ft. attacks a target other than you (who doesn't have "
            "this feat), melee attack the attacker.", 'Sentinel'))

    # Crossbow Expert: the bonus-action attack is gated on actually wielding a hand crossbow.
    if "Crossbow Expert" in char.get("feats", []):
        buckets['Passive'].append(('Crossbow Expert',
            "Ignore the Loading property on crossbows you're proficient with. Being within "
            "5 ft. of a hostile creature doesn't impose disadvantage on your ranged attacks.",
            'Crossbow Expert'))
        if "Hand Crossbow" in set(w.split(" +")[0].strip() for w in char.get("equipped_weapons", [])):
            _ce_mod = ability_mod(char, "DEX")
            buckets['Bonus Action'].append(('Hand Crossbow Attack',
                f"After attacking with a one-handed weapon, bonus-action attack with your hand "
                f"crossbow: 1d6{f'+{_ce_mod}' if _ce_mod>=0 else _ce_mod} piercing.",
                'Crossbow Expert'))

    # War Caster.
    if "War Caster" in char.get("feats", []):
        buckets['Passive'].append(('War Caster',
            "Advantage on CON saves to maintain concentration when damaged. Perform somatic "
            "components of spells even with weapons/a shield in hand.", 'War Caster'))
        buckets['Reaction'].append(('War Caster Spellstrike',
            "Cast a spell (1-action casting time, targeting only the provoking creature) "
            "instead of making an opportunity attack.", 'War Caster'))

    # Shield Master: all three benefits are gated on actually wielding a shield.
    if "Shield Master" in char.get("feats", []) and char.get("shield", False):
        _sm_bonus = 2 + char.get("shield_magic_bonus", 0)
        buckets['Bonus Action'].append(('Shield Shove',
            "After taking the Attack action: shove a creature within 5 ft. (STR/DEX save, "
            "its choice, vs. your grapple/shove DC), pushing it 5 ft. or knocking it prone.",
            'Shield Master'))
        buckets['Passive'].append(('Shield Master (DEX Saves)',
            f"If not incapacitated, add your shield's AC bonus (+{_sm_bonus}) to a DEX save "
            f"against an effect that targets only you.", 'Shield Master'))
        buckets['Reaction'].append(('Shield Master (No Damage)',
            "On a successful DEX save against an effect that would normally deal half damage "
            "on a success, take no damage instead, interposing your shield.", 'Shield Master'))

    # Mage Slayer.
    if "Mage Slayer" in char.get("feats", []):
        buckets['Reaction'].append(('Mage Slayer',
            "Melee attack a creature within 5 ft. that casts a spell.", 'Mage Slayer'))
        buckets['Passive'].append(('Mage Slayer (Saves)',
            "Damaging a concentrating creature gives it disadvantage on that concentration "
            "save. Advantage on your saves against spells cast by creatures within 5 ft. of you.",
            'Mage Slayer'))

    # Harness Divine Power (TCE optional class feature, Cleric and
    # Paladin): fully defined in class_features.py with a real
    # resource. This is an OPTIONAL feature (DM-approved opt-in, not
    # automatic) — gated by the Settings-popup "Optional Rules" toggle,
    # the same mechanism used for Eldritch Versatility.
    if char.get("optional_rules", {}).get("harness_divine_power", False):
        if class_levels(char).get("Cleric", 0) >= 2 or class_levels(char).get("Paladin", 0) >= 3:
            buckets['Bonus Action'].append(('Harness Divine Power (Channel Divinity)',
                "Touch your holy symbol, utter a prayer, and regain one expended spell slot whose "
                "level is no higher than half your proficiency bonus (rounded up).",
                'Harness Divine Power'))

    # Actor.
    if "Actor" in char.get("feats", []):
        buckets['Passive'].append(('Actor',
            "Advantage on CHA (Deception) and CHA (Performance) checks when trying to pass "
            "yourself off as a different person. Can mimic another person's speech or a "
            "creature's sounds you've heard for 1+ minute.", 'Actor'))

    # Elven Accuracy: this app doesn't roll dice for attacks (it shows
    # modifiers, not rolls), so the reroll itself has no numeric hook
    # to attach to — shown as a passive reminder instead.
    if "Elven Accuracy" in char.get("feats", []):
        buckets['Passive'].append(('Elven Accuracy',
            "Whenever you have advantage on an attack roll using DEX, INT, WIS, or CHA, "
            "reroll one of the two dice once.", 'Elven Accuracy'))

    # Elemental Adept: shown once the player has made their damage-type
    # choice via the feat-selection dialog; falls back to a generic
    # note if not yet chosen.
    if "Elemental Adept" in char.get("feats", []):
        _ea_type = char.get("_choices", {}).get("elemental_adept_type", "your chosen")
        buckets['Passive'].append(('Elemental Adept',
            f"Your {_ea_type} spells ignore resistance to {_ea_type} damage, and you can treat "
            f"any 1 rolled on a {_ea_type} damage die as a 2.", 'Elemental Adept'))

    # Dragon Fear: used "in place of your Breath Weapon" (same
    # resource, an alternative choice each time), so shown as an
    # additional action alongside it rather than replacing that entry outright.
    if "Dragon Fear" in char.get("feats", []):
        from dnd_app.core.calculator import get_prof_bonus, ability_mod
        _df_dc = 8 + get_prof_bonus(char) + ability_mod(char, "CHA")
        buckets['Action'].append(('Dragon Fear',
            f"In place of your Breath Weapon, roar: each creature you choose within 30 ft. "
            f"makes a WIS save (DC {_df_dc}) or is frightened of you for 1 minute (repeatable "
            f"save on taking damage; automatic success if it can't see/hear you).",
            'Dragon Fear'))

    # Littlest Yeti (DM reward): situational advantage, no numeric
    # hook beyond the language grant (already wired in builder.py).
    if "Littlest Yeti" in char.get("dm_rewards", []):
        buckets['Passive'].append(('Littlest Yeti',
            "Advantage on CHA checks made to influence yeti or improve their attitude toward "
            "you.", 'Littlest Yeti'))

    # Owlbear Whisperer (DM reward): a real, specific DC, but purely
    # situational (NPC-attitude-dependent) with no numeric character
    # stat to modify.
    if "Owlbear Whisperer" in char.get("dm_rewards", []):
        buckets['Action'].append(('Owlbear Whisperer',
            "Within 10 ft. of an owlbear: DC 10 CHA (Animal Handling) check to improve its "
            "attitude toward you one step (hostile\u2192indifferent or indifferent\u2192friendly).",
            'Owlbear Whisperer'))

    # Spirit Medium (DM reward): situational advantage; its proficiency
    # grant is already wired in builder.py.
    if "Spirit Medium" in char.get("dm_rewards", []):
        buckets['Passive'].append(('Spirit Medium',
            "Advantage on Arcana or Religion checks to remember or research information about "
            "spirits and the afterlife.", 'Spirit Medium'))

    # Lifelong Companion (DM reward): passive aura for nearby allies;
    # its reaction (Companion's Protection) is already wired as a
    # real resource in calculator.py.
    if "Lifelong Companion" in char.get("dm_rewards", []):
        buckets['Passive'].append(('Boon Aura',
            "Allies within 5 ft. of you have advantage on saving throws against being "
            "frightened or charmed, provided you aren't incapacitated.", 'Lifelong Companion'))
    # Doppelganger (DM Reward): darkvision is wired separately in calculator.py's get_character_senses().
    if "Doppelganger" in char.get("dm_rewards", []):
        from dnd_app.core.calculator import get_prof_bonus, ability_mod
        _dg_dc = 8 + get_prof_bonus(char) + ability_mod(char, "INT")
        buckets['Action'].append(('Detect Thoughts (at will)',
            f"Innately cast detect thoughts, no components. Spellcasting ability: INT. "
            f"Save DC {_dg_dc}.", 'Doppelganger'))
        buckets['Action'].append(('Polymorph (Doppelganger)',
            "Polymorph into any humanoid you have seen or back into your true form. Your "
            "statistics (other than size) don't change; equipment isn't transformed. You "
            "revert to your true form when you die.", 'Doppelganger'))

    # Owlbear Whisperer (DM Reward): a fixed, stated DC — not player-scaled.
    if "Owlbear Whisperer" in char.get("dm_rewards", []):
        buckets['Action'].append(('Owlbear Whisperer',
            "If within 10 ft. of an owlbear: DC 10 CHA (Animal Handling) check. On a success, "
            "shift its attitude toward you (hostile→indifferent, or indifferent→friendly).",
            'Owlbear Whisperer'))

    # Littlest Yeti (DM Reward).
    if "Littlest Yeti" in char.get("dm_rewards", []):
        buckets['Passive'].append(('Littlest Yeti',
            "Speak Yeti. Advantage on CHA checks made to influence yeti or improve their "
            "attitudes.", 'Littlest Yeti'))


    # for this Pact Boon option — creating the pact weapon is an action
    # per the actual rule text provided.
    _pact_choice = char.get("_choices", {}).get("warlock_pact_boon", [])
    if _pact_choice and "blade" in _pact_choice[0].lower():
        buckets['Action'].append(('Create Pact Weapon',
            "Create a melee weapon of your choice in your empty hand (proficient with it, "
            "counts as magical). Disappears if more than 5 ft. away for 1 min.+, if you create "
            "it again, if dismissed (no action), or if you die.", 'Warlock'))
    # Pact of the Chain (Warlock): the find familiar grant itself is handled separately, via bonus_spells.
    if _pact_choice and "chain" in _pact_choice[0].lower():
        buckets['Action'].append(('Forgo Attack for Familiar',
            "When you take the Attack action, forgo one of your own attacks to let your "
            "familiar make one attack with its reaction.", 'Warlock'))
    # Waxing and Waning (Lunar Sorcery, 6th level).
    if class_levels(char).get("Sorcerer", 0) >= 6 and "lunar" in subclasses(char).get("Sorcerer", "").lower():
        buckets['Bonus Action'].append(('Waxing and Waning',
            "Spend 1 sorcery point to change your current Lunar Embodiment phase for a "
            "different one.", 'Sorcerer'))
    # Pyromancer's Fury (Pyromancer, PSK, 14th level): unofficial
    # (Plane Shift: Kaladesh), noted in the description itself.
    sorc_lvl_pf = class_levels(char).get("Sorcerer", 0)
    if sorc_lvl_pf >= 14 and "pyromancer" in subclasses(char).get("Sorcerer", "").lower():
        buckets['Reaction'].append(("Pyromancer's Fury",
            f"Unofficial (Plane Shift: Kaladesh). When hit by a melee attack, deal fire "
            f"damage equal to your sorcerer level ({sorc_lvl_pf}) to the attacker, ignoring "
            f"resistance to fire damage.", 'Sorcerer'))
    # Heart of Fire (Pyromancer, PSK, 1st level): this app has no
    # "which spells deal fire damage" flag to hook a mechanical trigger
    # into — a visible Passive note instead.
    if sorc_lvl_pf >= 1 and "pyromancer" in subclasses(char).get("Sorcerer", "").lower():
        buckets['Passive'].append(("Heart of Fire (passive)",
            f"Unofficial (Plane Shift: Kaladesh). Whenever you start casting a spell of 1st "
            f"level or higher that deals fire damage, creatures of your choice within 10 ft "
            f"that you can see take fire damage equal to half your sorcerer level "
            f"({max(1, sorc_lvl_pf // 2)}).", 'Sorcerer'))
    buckets['Bonus Action'].append(('Offhand Attack','When you take the Attack action with a light weapon, attack with your off-hand light weapon (no ability mod to damage unless negative).', 'Universal'))
    buckets['Reaction'].append(('Opportunity Attack','When enemy leaves your melee reach: make one melee attack against them.', 'Universal'))
    buckets['Passive'].append(('Spellcasting (passive)','Cast spells using your prepared/known spells and available spell slots.', 'Universal'))

    # ── Race / species actions ────────────────────────────────────────────────
    race_name = char.get("species") or char.get("race", "")
    RACE_ACTIONS = {   # trait fragment → (bucket, display, desc)
        "Breath Weapon":     ("Action", "Breath Weapon",
            "Exhale destructive energy (shape/type by ancestry). "
            "DC 8+CON+prof, half on save. 2d6→5d6 by level. 1/SR."),
        "Healing Hands":     ("Action", "Healing Hands",
            "Touch a creature: it regains HP equal to your level. 1/LR."),
        "Hidden Step":       ("Bonus Action", "Hidden Step",
            "Turn invisible until your next turn starts or you attack/deal damage. PB/LR."),
        "Fury of the Small": ("Passive", "Fury of the Small",
            "When you damage a larger creature: +your level damage. 1/SR."),
        "Stone's Endurance": ("Reaction", "Stone's Endurance",
            "When you take damage: reduce it by 1d12 + CON. 1/SR."),
        "Daunting Roar":     ("Bonus Action", "Daunting Roar",
            "Creatures within 10 ft: CON save or frightened until your next turn. 1/SR."),
        "Mimicry":           ("Passive", "Mimicry (passive)", "MIMICRY_DYNAMIC"),
        "Goring Rush":       ("Bonus Action", "Goring Rush",
            "After you Dash: one melee attack with your horns."),
        "Hammering Horns":   ("Bonus Action", "Hammering Horns",
            "After you hit with melee: shove that target with your horns."),
        "Rabbit Hop":        ("Bonus Action", "Rabbit Hop",
            "Jump Prof×5 ft without provoking opportunity attacks. PB/LR."),
        "Adrenaline Rush":   ("Bonus Action", "Adrenaline Rush",
            "Dash as a bonus action + temp HP equal to prof. 1/LR."),
        "Nimble Escape":     ("Bonus Action", "Nimble Escape",
            "Disengage or Hide as a bonus action."),
        "Grovel, Cower":     ("Action", "Grovel, Cower, and Beg",
            "Allies gain advantage vs enemies within 10 ft of you until your next turn. 1/SR."),
        "Hungry Jaws":       ("Bonus Action", "Hungry Jaws",
            "Special bite: on hit, gain CON mod temp HP. 1/SR."),
        "Flurry of":         (None, "", ""),  # guard: never match monk via race
        "Second Chance":     ("Reaction", "Second Chance",
            "When hit by an attack: force a reroll. 1/LR."),
        "Fey Step":          ("Bonus Action", "Fey Step",
            "Teleport 30 ft (seasonal rider effect). 1/SR."),
        "Shifting":          ("Bonus Action", "Shifting",
            "Bestial form 1 min: temp HP = prof + CON, subrace perks. 1/SR."),
        "Vampiric Bite":     ("Passive", "Vampiric Bite",
            "Natural weapon bite, 1d4+CON piercing (CON instead of STR). Advantage on attack rolls with it while you have half or fewer HP. On a hit against a non-Construct/non-Undead, empower yourself: regain HP equal to the damage dealt, or gain a bonus to your next check/attack equal to it. Uses = PB per long rest."),
        "Ram":               ("Passive", "Ram (Satyr)",
            "1d6+STR bludgeon; after 10 ft straight move, STR save or pushed 5 ft."),
    }
    if race_name:
        try:
            from dnd_app.data.phb2014.races import get_race
            rdata = get_race(race_name) or {}
            traits_blob = " || ".join(rdata.get("traits", []))
            # subrace strings can also carry actions (Eladrin Fey Step etc.)
            sub = char.get("subrace", "") or ""
            traits_blob += " || " + sub
            for frag, spec in RACE_ACTIONS.items():
                bucket = spec[0]
                if not bucket or frag.lower() not in traits_blob.lower():
                    continue
                if frag == "Breath Weapon":
                    # Fully dynamic: real damage type/shape/save from the
                    # character's chosen ancestry, real dice for their level,
                    # real DC — not the generic level-progression text.
                    desc = _breath_weapon_desc(char)
                elif frag == "Mimicry":
                    # The base and MPMM Kenku versions have genuinely
                    # different mechanics (opposed Deception check vs.
                    # flat DC), resolved separately rather than shown as
                    # one, potentially-wrong generic description.
                    if race_name == "Kenku (MPMM)":
                        from dnd_app.core.calculator import get_prof_bonus
                        from dnd_app.core.character import ability_mod
                        pb_mim = get_prof_bonus(char)
                        cha_mim = ability_mod(char, "CHA")
                        desc = ("You can accurately mimic sounds you've heard, including "
                                f"voices. A listener can tell it's an imitation only with a "
                                f"successful Wisdom (Insight) check (DC {8+pb_mim+cha_mim}).")
                    else:
                        desc = ("You can mimic sounds you've heard, including voices. A "
                                "listener can tell it's an imitation with a successful Wisdom "
                                "(Insight) check opposed by your Charisma (Deception) check.")
                else:
                    desc = _resolve_dynamic_combat_text(char, spec[2])
                buckets[bucket].append((spec[1], desc, race_name))
        except Exception:
            pass

    # ── Spells routed by casting time ─────────────────────────────────────────
    # Cantrips + pinned spells + all bonus-action/reaction spells appear as
    # castable cards. Leveled 1-action spells appear only when pinned (★) so a
    # 15-spell wizard list doesn't flood the Action tab.
    try:
        from dnd_app.data.phbCommon.spells import ALL_SPELLS
        spell_cat = {s['name']: s for s in ALL_SPELLS}
        known  = list(char.get('spells_known', []))
        prepared = set(char.get('spells_prepared', []))
        char_classes = {c.get('class','') for c in char.get('classes', [])}
        PREPARE_CLASSES = {"Wizard", "Cleric", "Druid", "Paladin", "Artificer"}
        my_prepare_classes = char_classes & PREPARE_CLASSES
        pinned = set(char.get('quick_spells', []))
        seen = set()
        for sp_name in known + [p for p in pinned if p not in known]:
            if sp_name in seen: continue
            seen.add(sp_name)
            sp = spell_cat.get(sp_name)
            if not sp: continue
            # A leveled spell belonging to one of this character's own
            # prepared-caster classes must actually be prepared to be
            # castable — being in the spellbook (spells_known) alone isn't
            # enough for these classes, unlike Sorcerer/Bard/Warlock/Ranger
            # where "known" is the only relevant list. Cantrips are exempt:
            # they're never prepared, for any class.
            if (sp.get('level', 0) > 0 and my_prepare_classes & set(sp.get('classes', []))
                    and sp_name not in prepared):
                continue
            ct  = str(sp.get('cast_time') or '1 action')
            lvl = sp.get('level', 0)
            if 'bonus' in ct.lower():   bucket = 'Bonus Action'
            elif 'reaction' in ct.lower(): bucket = 'Reaction'
            elif ct == '1 action':
                bucket = 'Action'
            else:
                continue                # 1-min+ casts aren't combat actions
            tag = 'Cantrip' if lvl == 0 else f'Spell L{lvl}'
            star = '★ ' if sp_name in pinned else ''
            extra = ' (C)' if sp.get('concentration') else ''
            sp_desc = sp.get('desc','')
            if lvl == 0:
                sp_desc = _append_cantrip_scaling_note(sp_name, sp_desc, char)
            buckets[bucket].append(
                (f"{star}{sp_name}{extra}", sp_desc, tag, sp))
    except Exception:
        pass

    # Way of the Four Elements: chosen Elemental Disciplines are
    # player-chosen (not fixed by CLASS_FEATURE_INDEX like most
    # subclass features), so a static KNOWN_ACTIONS entry can't cover
    # them — only the free, unconditional Elemental Attunement would
    # otherwise appear on the Combat page.
    try:
        chosen_disciplines = char.get("_choices", {}).get("four_elements_disciplines", [])
        for disc in chosen_disciplines:
            disc_name = disc.split(" – ")[0].strip()
            disc_desc = disc.split(" – ", 1)[1].strip() if " – " in disc else disc
            buckets['Action'].append((disc_name, disc_desc, 'Monk'))
    except Exception:
        pass

    # Arcane Archer: chosen Arcane Shot options are player-chosen, so no
    # static KNOWN_ACTIONS entry can cover them. Arcane Shot replaces
    # one of the Extra Attacks with a special shot, so it's a
    # Reaction-free Action use.
    try:
        chosen_shots = char.get("_choices", {}).get("arcane_shot_options", [])
        for shot in chosen_shots:
            shot_name = shot.split(" – ")[0].strip()
            shot_desc = shot.split(" – ", 1)[1].strip() if " – " in shot else shot
            buckets['Action'].append((shot_name, shot_desc, 'Fighter'))
    except Exception:
        pass

    # Rune Knight: chosen Runes. Each rune grants both a passive skill
    # benefit and an active, limited-use effect (bonus action or
    # reaction depending on the rune) — shown together here as one
    # entry per rune rather than splitting the passive/active halves
    # apart, since the reference text describes them as a single package per rune.
    try:
        chosen_runes = char.get("_choices", {}).get("rune_knight_runes", [])
        for rune in chosen_runes:
            rune_name = rune.split(" – ")[0].strip()
            rune_desc = rune.split(" – ", 1)[1].strip() if " – " in rune else rune
            buckets['Passive'].append((rune_name, rune_desc, 'Fighter'))
    except Exception:
        pass

    # Battle Master: chosen Maneuvers are shown here as real, usable
    # Actions tab entries with their actual effect text, not just in
    # the Features tab's passive list. Maneuvers are triggered on a
    # weapon hit as part of an attack, so they land in Action alongside
    # the attack itself rather than as a separate bonus action.
    try:
        chosen_maneuvers = char.get("battle_master_maneuvers", [])
        for man in chosen_maneuvers:
            man_name = man.split(" – ")[0].strip()
            man_desc = man.split(" – ", 1)[1].strip() if " – " in man else man
            buckets['Action'].append((man_name, man_desc, 'Fighter'))
    except Exception:
        pass

    # One with Shadows and Relentless Hex are unlimited-use but
    # conditional (light level, or an active cursed target), so they
    # don't fit the resource-cap pattern used for the other Eldritch
    # Invocations. Far Scribe's spell-storing book mechanic is complex
    # enough that a full simulation isn't practical here, so it gets an
    # accurate note-only entry.
    _known_inv3 = [inv.split(" (")[0].strip() for inv in char.get("eldritch_invocations", [])]
    if "One with Shadows" in _known_inv3:
        buckets['Action'].append(('One with Shadows',
            "While in an area of dim light or darkness, become invisible until you move, take "
            "an action, or take a reaction.",
            'One with Shadows'))
    if "Relentless Hex" in _known_inv3:
        buckets['Bonus Action'].append(('Relentless Hex',
            "Teleport up to 30 ft. to an unoccupied space within 5 ft. of a creature cursed by "
            "your hex spell (or a cursing warlock feature like Hexblade's Curse or Sign of Ill "
            "Omen). You must be able to see the cursed target.",
            'Relentless Hex'))
    if "Far Scribe" in _known_inv3:
        buckets['Passive'].append(('Far Scribe',
            "A page in your Book of Shadows can hold a number of names (proficiency bonus) that "
            "creatures write there themselves. Cast sending to a named creature without a spell "
            "slot or material components by writing the message on the page.",
            'Far Scribe'))

    # 10 "at-will" spell-like Eldritch Invocations go into Known
    # Actions rather than being left as passive notes, since each is a
    # real, repeatable action a player takes in play.
    AT_WILL_INVOCATIONS = {
        "Ascendant Step": "Cast levitate on yourself at will, without a spell slot or material components.",
        "Beast Speech": "Cast speak with animals at will, without expending a spell slot.",
        "Eldritch Sight": "Cast detect magic at will, without expending a spell slot.",
        "Fiendish Vigor": "Cast false life on yourself at will as a 1st-level spell, without a spell slot or material components.",
        "Mask of Many Faces": "Cast disguise self at will, without expending a spell slot.",
        "Master of Myriad Forms": "Cast alter self at will, without expending a spell slot.",
        "Misty Visions": "Cast silent image at will, without a spell slot or material components.",
        "Otherworldly Leap": "Cast jump on yourself at will, without a spell slot or material components.",
        "Visions of Distant Realms": "Cast arcane eye at will, without expending a spell slot.",
        "Whispers of the Grave": "Cast speak with dead at will, without expending a spell slot.",
    }
    for iname, note in AT_WILL_INVOCATIONS.items():
        if iname in _known_inv3:
            buckets['Action'].append((iname, note, iname))

    # Eldritch Blast on-hit modifiers — each triggers when the cantrip
    # hits, so they land in Passive as a standing modifier rather than
    # their own separate action, matching how Agonizing Blast's own
    # bonus is already shown as an annotation on the cantrip itself
    # rather than a separate entry.
    ELDRITCH_BLAST_MODS = {
        "Eldritch Spear": "Your eldritch blast's range is 300 ft. instead of 120 ft.",
        "Grasp of Hadar": "Once each turn when you hit with eldritch blast, pull that creature 10 ft. closer to you.",
        "Lance of Lethargy": "Once each turn when you hit with eldritch blast, reduce that creature's speed by 10 ft. until the end of your next turn.",
        "Repelling Blast": "When you hit with eldritch blast, you can push the creature up to 10 ft. away from you in a straight line.",
    }
    for iname, note in ELDRITCH_BLAST_MODS.items():
        if iname in _known_inv3:
            buckets['Passive'].append((iname, note, iname))

    # Pact of the Blade-specific invocations: gated on the actual pact
    # boon choice, not just being known, since these are meaningless
    # without that specific pact.
    _pact_lower = char.get("_choices", {}).get("warlock_pact_boon", [""])[0].lower() if char.get("_choices", {}).get("warlock_pact_boon") else ""
    if "blade" in _pact_lower:
        if "Eldritch Smite" in _known_inv3:
            buckets['Passive'].append(('Eldritch Smite',
                "Once per turn when you hit with your pact weapon, expend a spell slot to deal an "
                "extra 1d8 force damage (+1d8 per slot level), and knock the target prone if it's "
                "Huge or smaller.", 'Eldritch Smite'))
        if "Improved Pact Weapon" in _known_inv3:
            buckets['Passive'].append(('Improved Pact Weapon',
                "Your pact weapon can serve as a spellcasting focus, gains a +1 bonus to attack and "
                "damage rolls (unless it's already a magic weapon with a bonus), and can take the "
                "form of a shortbow, longbow, light crossbow, or heavy crossbow.",
                'Improved Pact Weapon'))
        if "Lifedrinker" in _known_inv3:
            buckets['Passive'].append(('Lifedrinker',
                "When you hit with your pact weapon, the creature takes extra necrotic damage equal "
                "to your Charisma modifier (minimum 1).", 'Lifedrinker'))
        if "Thirsting Blade" in _known_inv3:
            buckets['Passive'].append(('Thirsting Blade',
                "You can attack with your pact weapon twice, instead of once, whenever you take the "
                "Attack action.", 'Thirsting Blade'))

    # Pact of the Chain-specific invocations: same gating logic.
    if "chain" in _pact_lower:
        if "Gift of the Ever-Living Ones" in _known_inv3:
            buckets['Passive'].append(('Gift of the Ever-Living Ones',
                "Whenever you regain hit points while your familiar is within 100 ft. of you, treat "
                "any dice rolled to determine the hit points as having rolled their maximum value.",
                'Gift of the Ever-Living Ones'))
        if "Investment of the Chain Master" in _known_inv3:
            buckets['Passive'].append(('Investment of the Chain Master',
                "Your familiar gains a flying or swimming speed of 40 ft.; as a bonus action you can "
                "command it to Attack; its weapon attacks count as magical; it uses your spell save "
                "DC; and you can use your reaction to grant it resistance to damage it takes.",
                'Investment of the Chain Master'))
        if "Voice of the Chain Master" in _known_inv3:
            buckets['Passive'].append(('Voice of the Chain Master',
                "Communicate telepathically with your familiar and perceive through its senses "
                "while on the same plane, and speak through it in your own voice.",
                'Voice of the Chain Master'))

    # Passive skill/utility grants with no activation needed.
    if "Beguiling Influence" in _known_inv3:
        buckets['Passive'].append(('Beguiling Influence',
            "You gain proficiency in the Deception and Persuasion skills.", 'Beguiling Influence'))
    if "Eyes of the Rune Keeper" in _known_inv3:
        buckets['Passive'].append(('Eyes of the Rune Keeper',
            "You can read all writing.", 'Eyes of the Rune Keeper'))
    if "Witch Sight" in _known_inv3:
        buckets['Passive'].append(('Witch Sight',
            "You can see the true form of any shapechanger or creature concealed by illusion or "
            "transmutation magic within 30 ft. and within line of sight.", 'Witch Sight'))
    if "Gaze of Two Minds" in _known_inv3:
        buckets['Action'].append(('Gaze of Two Minds',
            "Touch a willing humanoid and perceive through its senses until the end of your next "
            "turn; on later turns, use your action again to extend the connection. You're blinded "
            "and deafened to your own surroundings while doing so.", 'Gaze of Two Minds'))

    # Boots of the Winding Path (Artificer Infusion): unlimited uses (no
    # resource cap needed), so this is a plain Bonus Action entry.
    if any(inf.get("infusion") == "Boots of the Winding Path" for inf in char.get("active_infusions", [])):
        buckets['Bonus Action'].append(('Boots of the Winding Path',
            "Teleport up to 15 ft. to an unoccupied space you can see that you occupied at "
            "some point this turn.",
            'Boots of the Winding Path'))

    # 3 more newly-built Eldritch Invocations.
    _known_inv2 = [inv.split(" (")[0].strip() for inv in char.get("eldritch_invocations", [])]
    if "Maddening Hex" in _known_inv2:
        buckets['Bonus Action'].append(('Maddening Hex',
            "Deal CHA-mod psychic damage (min 1) to the target of your hex spell/cursing "
            "feature and each creature you choose within 5 ft. of it. Requires seeing the "
            "cursed target, within 30 ft.",
            'Maddening Hex'))
    if "Rebuke of the Talisman" in _known_inv2:
        buckets['Reaction'].append(('Rebuke of the Talisman',
            "When your talisman's wearer is hit by an attacker you can see within 30 ft., deal "
            "proficiency-bonus psychic damage to the attacker and push it up to 10 ft. away.",
            'Rebuke of the Talisman'))
    if "Aspect of the Moon" in _known_inv2:
        buckets['Passive'].append(('Aspect of the Moon',
            "No longer need to sleep, and can't be forced to sleep by any means. To gain the "
            "benefits of a long rest, spend all 8 hours doing light activity instead.",
            'Aspect of the Moon'))

    # Rage "addon" summary: features that add onto an existing base
    # mechanic (subclass/level bonuses "while raging") are visible
    # together rather than scattered as separate entries a player has
    # to notice individually. Scans every other entry already computed
    # above for a "while raging" mention and appends a short list of
    # names to Rage's own description, so looking at Rage shows
    # everything it currently does.
    try:
        rage_addons = []
        for bucket_items in buckets.values():
            for item in bucket_items:
                item_name, item_desc = item[0], item[1]
                if item_name != 'Rage' and 'while raging' in item_desc.lower():
                    rage_addons.append(item_name)
        if rage_addons:
            for bucket_items in buckets.values():
                for i, item in enumerate(bucket_items):
                    if item[0] == 'Rage':
                        new_desc = (item[1] + " Also active while raging: "
                                   + ", ".join(sorted(set(rage_addons))) + ".")
                        bucket_items[i] = (item[0], new_desc) + item[2:]
    except Exception:
        pass

    # Throwable/usable consumable items (Alchemist's Fire, Acid, Holy
    # Water, etc.) use their correct, detailed mechanical text from the
    # items data. Only surfaced for items the character actually owns,
    # not shown unconditionally.
    CONSUMABLE_ITEM_ACTIONS = {
        "Acid (vial)": ("Action", "Acid (vial)"),
        "Alchemist's Fire (flask)": ("Action", "Alchemist's Fire (flask)"),
        "Holy Water (flask)": ("Action", "Holy Water (flask)"),
        "Oil (flask)": ("Action", "Oil (flask)"),
        "Alchemist's Doom (flask)": ("Action", "Alchemist's Doom (flask)"),
        "Catapult Munition": ("Action", "Catapult Munition"),
        "Tinderbox": ("Action", "Tinderbox"),
        "Backpack Parachute": ("Reaction", "Backpack Parachute"),
        "Barking Box": ("Action", "Barking Box"),
        "Murgaxor's Elixir of Life": ("Action", "Murgaxor's Elixir of Life"),
        "Vial of Stardust": ("Action", "Vial of Stardust"),
    }
    from dnd_app.data.phbCommon.items import ADVENTURING_GEAR as _AG
    _gear_notes = {row[0]: (row[3] if len(row) > 3 else "") for row in _AG}
    owned_names = {eq.get("name", "") for eq in char.get("equipment", [])}
    for item_name, (bucket_name, gear_key) in CONSUMABLE_ITEM_ACTIONS.items():
        if item_name in owned_names:
            note = _gear_notes.get(gear_key, "")
            if note:
                buckets[bucket_name].append((item_name, note, item_name))

    # Interception / Protection fighting styles are reaction-based
    # (unlike the other 9 fighting styles, which are passive combat-math
    # modifiers already handled elsewhere), so they get their own
    # Actions tab entries alongside the Features tab display.
    _fighting_styles = char.get("fighting_styles", [])
    if any("interception" in fs.lower() for fs in _fighting_styles):
        buckets['Reaction'].append(('Interception (Fighting Style)',
            "When a creature within 5 ft. that you can see is hit by an attack, reduce the "
            "damage by 1d10 + your proficiency bonus (using a weapon you're wielding).",
            'Interception'))
    if any("protection" in fs.lower() and "aura" not in fs.lower() for fs in _fighting_styles):
        buckets['Reaction'].append(('Protection (Fighting Style)',
            "When a creature you can see attacks a target other than you that's within 5 ft. "
            "of you, impose disadvantage on the attack roll (requires a shield).",
            'Protection'))

    # Pact Boon (Warlock): Blade and Talisman each get an Actions tab
    # entry describing when/how to use them (Talisman's own resource is
    # wired elsewhere), and Chain's forgo-attack mechanic and special
    # familiar forms are noted here alongside the spell grant.
    _pact = char.get("_choices", {}).get("warlock_pact_boon", [])
    _pact_name = _pact[0].lower() if _pact else ""
    if "blade" in _pact_name:
        blade_desc = ("Create a pact weapon in your empty hand (choose its melee weapon form each time). "
                      "You're proficient with it, and it counts as magical for overcoming resistance/"
                      "immunity to nonmagical attacks. Disappears if more than 5 ft. away for 1 min., or "
                      "if you use this again.")
        # Lifedrinker: computes the real, live CHA-mod bonus here,
        # following the same pattern used for Agonizing Blast's
        # Eldritch Blast damage, rather than just noting the rule exists.
        if any("lifedrinker" in i.lower() for i in char.get("eldritch_invocations", [])):
            from dnd_app.core.calculator import ability_mod
            cha_mod = ability_mod(char, "CHA")
            bonus_str = f"+{cha_mod}" if cha_mod > 0 else str(cha_mod)
            blade_desc += (f" Lifedrinker: on a hit with this weapon, deal an extra "
                          f"{bonus_str} necrotic damage (minimum 1).")
        buckets['Bonus Action'].append(('Pact of the Blade', blade_desc, 'Pact of the Blade'))
    elif "chain" in _pact_name:
        buckets['Passive'].append(('Pact of the Chain',
            "Familiar can take imp, pseudodragon, quasit, or sprite form in addition to the "
            "normal options. When you take the Attack action, you can forgo one of your own "
            "attacks to let your familiar use its reaction to make one attack.",
            'Pact of the Chain'))
    elif "talisman" in _pact_name:
        buckets['Passive'].append(('Pact of the Talisman',
            "When the wearer of your talisman fails an ability check, they can add a d4 to the "
            "roll (potentially turning it into a success). Uses = proficiency bonus per long "
            "rest.",
            'Pact of the Talisman'))

    return dict(buckets)

