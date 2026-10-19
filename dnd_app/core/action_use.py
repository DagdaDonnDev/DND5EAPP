"""What pressing Use on an action does — the one set of rules both apps
follow (desktop: pages/sheet/action_tabs.py, Android: bridge
character_sheet.py useAbility).

    use_action(char, bucket, name, desc, answers) -> dict
        ok       False when it can't be used (no ki left, needs Rage...)
        toast    what happened, said plainly: what it does, what was
                 spent and what's left, any roll
        slot     the part of the turn it takes ("Action", "Bonus Action",
                 "Reaction"), or None for a rider (Reckless Attack)
        refresh  something changed that the sheet must recompute
        ask      a question to put to the player first — {"key", "title",
                 "options"}: show the options, put the answer in
                 answers[key] and call again (how many ki, which slot, a
                 Wild Shape check...)

How an action is decided, in order:
  1. Wild Shape: spellcasting is refused; anything that needs hands, a
     held weapon or an unarmed strike asks first (the DM decides whether
     the beast form can do it).
  2. A few hand-written actions (Divine Smite, Second Wind, Reckless
     Attack...).
  3. The RULES table: what it costs (ki, Channel Divinity, a spell
     slot...), its own uses per rest, and what it does (an effect, a
     heal, temporary hit points, a roll).
  4. Its own tracked resource (Action Surge, Rage...), switching the
     effect on for the Rage-style toggles.
  5. Otherwise: just the part of the turn, and a summary of the rules.

Per-rest uses that no other resource tracks (Wholeness of Body 1/LR,
Warding Flare per WIS modifier...) become resources of their own
(feature_use_resources, called by calculator.update_all), so they show
under Resources & Charges and reset with every rest like the rest.
"""
import random
import re

# ── Pools an action can spend: code -> (resource keys, one, many) ────────
POOLS = {
    "ki":       (("ki",), "ki point", "ki points"),
    "cd":       (("channel_divinity", "channel_div"), "Channel Divinity use", "Channel Divinity uses"),
    "bi":       (("bardic_insp",), "Bardic Inspiration use", "Bardic Inspiration uses"),
    "sd":       (("sup_dice",), "superiority die", "superiority dice"),
    "sp":       (("sorcery_points",), "sorcery point", "sorcery points"),
    "psi":      (("psionic_dice", "psionic_dice_rogue"), "Psionic Energy die", "Psionic Energy dice"),
    "ws":       (("wild_shape",), "Wild Shape use", "Wild Shape uses"),
    "loh":      (("loh", "lay_on_hands"), "Lay on Hands point", "Lay on Hands points"),
    "maledict": (("blood_maledict",), "Blood Maledict use", "Blood Maledict uses"),
    "mut":      (("mutagens",), "mutagen", "mutagens"),
}

# Effects that last until the start of your next turn (or to the end of
# this one): New Turn takes them off (new_turn below).
TURN_EFFECTS = ("Reckless Attack", "Dodge", "Agile Parry", "Kensei's Shot", "Fighting Spirit")

_CLASSES = ("artificer", "barbarian", "bard", "blood hunter", "cleric", "druid", "fighter",
            "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard")


def normalize(name: str) -> str:
    """"Turn Undead (Channel Divinity)" -> "turn undead"."""
    return " ".join(re.sub(r"\([^)]*\)", " ", name or "").lower().split())


# ── The rules ─────────────────────────────────────────────────────────────
# cost   (pool, n) or a list of them; n can be (lo, hi): ask how many.
#        pool "slot" spends a spell slot of at least level n ("pact": a
#        Pact Magic slot)
# uses   its own uses: "1/LR", "2/SR", "PB/LR", "WIS/LR" (modifier, min 1)
# alt    what it costs once those uses are gone (asks first)
# fx     an effect switched on (data in core/effects.py EFFECT_TABLE)
# heal / temp / roll   amounts: "1d10+DEX+monk", "3*monk", "2*MA", "KI*2d10"
#        (MA = Martial Arts die, BI = Bardic Inspiration die, KI/SP = the
#        number chosen, maxhp = hit point maximum)
# target "ask": yourself or someone else (heals)
# hp1    drops you to 1 hit point instead of 0
# needs  "rage" / "kensei melee" — refused without it
# once   only once per turn
# slot   False: takes no part of the turn (a rider)
# damage True: {roll} says what to roll ("1d10 + 8") instead of rolling it
#        -- damage, dealt or taken off, is the player's roll
# self_damage  damage you take for using it: asks what you rolled
# rite   Crimson Rite: asks which rite and which weapon
# again  can be used again while its effect is on
# pick_weapon / pick_type  asks which weapon / which damage type
# say    what it does, for the toast ({roll} = the roll, worked out)
RULES = {}


def R(*names, exact=False, **spec):
    """Register a rule under each name — normalized ("Turn Undead
    (Channel Divinity)" finds "Turn Undead"), or the exact full name when
    two actions share one (the Monk's and the Sorcerer's Draconic
    Presence)."""
    for n in names:
        RULES[n.lower() if exact else normalize(n)] = spec


def rule_for(display):
    """The RULES entry for an action's name, or None."""
    return RULES.get((display or "").strip().lower()) or RULES.get(normalize(display))


# Universal
R("Dodge", fx="Dodge")
R("Dash", say="your speed is doubled this turn")
R("Disengage", say="your movement doesn't provoke opportunity attacks this turn")
# Artificer
R("Defensive Field", uses="PB/LR", temp="artificer", replace_temp=True,
  say="temporary hit points equal to your Artificer level")
R("Perfected Armor", uses="PB/LR", say="Guardian: pull the creature up to 25 ft toward you (STR save)")
# Barbarian
R("Magic Awareness", uses="PB/LR")
R("Bolstering Magic", uses="PB/LR", roll="1d3", say="rolled {roll}: that many extra d3s, or a spell slot of that level")
R("Call the Hunt", uses="PB/LR", needs="rage")
R("Zealous Presence", uses="1/LR")
R("Elemental Cleaver", needs="rage", fx="Elemental Cleaver", pick_weapon=True,
  pick_type=("Acid", "Cold", "Fire", "Lightning", "Thunder"))
R("Mighty Impel", needs="rage")
R("Storm Aura", needs="rage")
R("Raging Storm", needs="rage")
R("Fanatical Focus", needs="rage", say="reroll the failed saving throw (once per rage)")
R("Spirit Shield", needs="rage", roll="NAMEDICE", damage=True, say="roll {roll} and take that much off the damage")
R("Unstable Backlash", needs="rage", roll="1d8", say="Wild Magic table: rolled {roll}")
R("Battlerager Charge", needs="rage", say="Dash as a bonus action")
R("Battlerager Armor", needs="rage", say="attack with your armor spikes: 1d4 piercing")
# Bard
R("Enthralling Performance", uses="1/SR")
R("Mystic Chronicle", uses="1/LR")
R("Performance of Creation", uses="1/LR", alt=("slot", 2))
R("Shadow Lore", uses="1/LR")
R("Universal Speech", uses="1/LR", alt=("slot", 1))
R("Words of Terror", uses="1/SR")
R("Mantle of Inspiration", cost=("bi", 1))
R("Mantle of Majesty", uses="1/LR")
R("Unbreakable Majesty", uses="1/SR")
R("Unsettling Words", cost=("bi", 1), roll="BI", say="the creature subtracts {roll} from its next saving throw")
R("Cutting Words", cost=("bi", 1), roll="BI", say="subtract {roll} from the roll")
R("Peerless Skill", cost=("bi", 1), roll="BI", say="add {roll} to the check")
R("Infectious Inspiration", uses="CHA/LR")
# Blood Hunter
R("Blood Curse of the Howl", "Blood Curse of Corrosion", "Blood Curse of the Exorcist",
  "Blood Curse of the Souleater", cost=("maledict", 1))
R("Revealed Arcana", uses="1/LR", cost=("slot", "pact"))
R("Unsealed Arcana", uses="1/LR")
R("Crimson Rite", self_damage="HEMODIE", fx="Crimson Rite", rite=True, again=True)
R("Mutagencraft", cost=("mut", 1))
R("Rite Revival", hp1=True, say="end your active rites: you drop to 1 hit point instead")
# Cleric
for _n in ("Arcane Abjuration", "Artisan's Blessing", "Charm Animals and Plants", "Cloak of Shadows",
           "Invoke Duplicity", "Order's Demand", "Path to the Grave", "Read Thoughts", "Turn Undead",
           "Twilight Sanctuary", "Feat of Strength", "Knowledge of the Ages", "Destructive Wrath",
           "Oketra's Blessing", "Rhonas' Blessing", "War God's Blessing"):
    R(_n, cost=("cd", 1))
R("Guided Strike", cost=("cd", 1), say="+10 to the attack roll")
R("Balm of Peace", cost=("cd", 1), roll="2d6+WIS", say="each creature you touch regains {roll} HP")
R("Preserve Life", cost=("cd", 1), roll="5*cleric", say="share {roll} HP among creatures within 30 ft (up to half their maximum)")
R("Radiance of the Dawn", cost=("cd", 1), roll="2d10+cleric", damage=True,
  say="the darkness is dispelled; roll {roll} radiant damage for each hostile creature within 30 ft (CON save halves)")
R("Blessing of the Forge", uses="1/LR")
R("Eyes of the Grave", uses="WIS/LR")
R("Visions of the Past", uses="1/SR")
R("Priest of Zeal", "Solidarity's Action", uses="WIS/LR")
R("Blaze of Glory", uses="1/LR", roll="5d10", damage=True, say="on a hit, add {roll} fire damage, and as much again of the weapon's type")
R("Sentinel at Death's Door", uses="WIS/LR", say="the critical hit becomes a normal hit")
R("Warding Flare", uses="WIS/LR", say="the attack roll has disadvantage")
R("Wrath of the Storm", uses="WIS/LR", roll="2d8", damage=True, say="roll {roll} lightning or thunder damage for the attacker (DEX save halves)")
R("Dampen Elements", say="resistance to that damage")
# Druid
R("Summon Wildfire Spirit", cost=("ws", 1), roll="2d6", damage=True, say="roll {roll} fire damage for each creature within 10 ft of it (DEX save negates)")
R("Walker in Dreams", uses="1/LR")
R("Hidden Paths", uses="WIS/LR")
R("Cauterizing Flames", uses="PB/LR", roll="2d10+WIS", damage=True, say="roll {roll}: that much healing, or that much fire damage")
R("Cosmic Omen", uses="PB/LR", roll="1d6", say="add or subtract {roll}")
R("Fungal Infestation", uses="WIS/LR")
R("Halo of Spores", roll="HALO", damage=True, say="roll {roll} necrotic damage (CON save negates)")
R("Symbiotic Entity", cost=("ws", 1), temp="4*druid", fx="Symbiotic Entity")
# Fighter
R("Arcane Shot", uses="2/SR", once=True)
R("Telekinetic Master", uses="1/LR", alt=("psi", 1))
R("Bulwark of Force", uses="1/LR", alt=("psi", 1))
R("Telekinetic Adept", uses="1/SR", alt=("psi", 1), say="Psi-Powered Leap: fly at double your walking speed until the end of the turn")
R("Runic Shield", uses="PB/LR", say="the attacker rerolls and must use the new roll")
R("Shadow Martyr", uses="1/SR")
R("Strength before Death", uses="1/LR")
R("Warding Maneuver", uses="CON/LR", roll="1d8", say="+{roll} AC against that attack; if it still hits, resistance to its damage")
R("Fighting Spirit", uses="3/LR", fx="Fighting Spirit", temp="FIGHTINGSPIRIT")
R("Action Surge", uses="1/SR", surge=True, slot=False, say="take one more action this turn")
R("Fire Rune", uses="1/SR", slot=False,
  say="add 2d6 fire damage to the hit; STR save or it's restrained, taking 2d6 fire each turn")
R("Cloud Rune", "Stone Rune", uses="1/SR")
R("Frost Rune", uses="1/SR", say="+2 to STR and CON checks and saves for 10 minutes")
R("Hill Rune", uses="1/SR", say="resistance to bludgeoning, piercing and slashing damage for 1 minute")
R("Storm Rune", uses="1/SR", say="for 1 minute, your reaction can give advantage or disadvantage to a roll within 60 ft")
# Feats and races
R("Stone's Endurance", uses="1/SR", roll="1d12+CON", damage=True, say="roll {roll} and take that much off the damage")
R("Breath Weapon", uses="1/SR", roll="BW", damage=True, say="roll {roll} {ANCESTRY} damage (DC {BWDC} {BWSAVE} save halves)")
R("Dragon Fear", share="Breath Weapon")
R("Grovel, Cower, and Beg", "Daunting Roar", uses="1/SR")
R("Hungry Jaws", uses="1/SR", temp="CON")
R("Fire Giant Strike", "Frost Giant Strike", "Cloud Giant Strike", "Stone Giant Strike",
  "Hill Giant Strike", "Storm Giant Strike", "Giant Strike", uses="PB/LR")
R("Defensive Duelist", say="+{PB} AC against that attack")
R("Healer", roll="1d6+4", target="ask", heal_self="1d6+4+level",
  say="the creature regains {roll} HP plus its number of Hit Dice")
R("Inspiring Leader", temp="level+CHA", say="up to six creatures, you included, gain temporary hit points")
R("Adrenaline Rush", uses="PB/LR", temp="PB", say="Dash as a bonus action")
R("Healing Hands", uses="1/LR", roll="level", target="ask", say="the creature regains {roll} HP")
R("Vital Sacrifice", self_damage="1d6", say="you take {roll} necrotic damage for a blood boon that lasts 1 hour")
R("Favored Foe", uses="PB/LR", fx="Favored Foe")
R("Cunning Action", say="Dash, Disengage or Hide")
R("Chromatic Infusion", uses="1/LR", fx="Chromatic Infusion", pick_weapon=True,
  pick_type=("Acid", "Cold", "Fire", "Lightning", "Poison"))
# Monk
R("Flurry of Blows", cost=("ki", 1), say="make two unarmed strikes")
R("Patient Defense", cost=("ki", 1), fx="Dodge")
R("Step of the Wind", cost=("ki", 1), say="Dash or Disengage; your jump distance doubles this turn")
R("Breath of the Dragon", uses="PB/LR", alt=("ki", 2), roll="2*MA", damage=True,
  say="roll {roll} acid, cold, fire, lightning or poison damage, your pick (DEX or CON save halves)")
R("Draconic Presence (Monk)", exact=True, cost=("ki", 3))
R("Hand of Healing", cost=("ki", 1), roll="MA+WIS", target="ask", say="the creature regains {roll} HP")
R("Hand of Ultimate Mercy", cost=("ki", 5), uses="1/LR", roll="4d10+WIS", say="the creature returns to life with {roll} HP")
R("Hour of Reaping", cost=("ki", 1))
R("Radiant Sun Bolt", roll="MA+DEX", damage=True, say="on a hit, roll {roll} radiant damage")
R("Searing Sunburst", cost=("ki", (0, 3)), roll="2d6+KI*2d6", damage=True, say="roll {roll} radiant damage for each creature in the 20-ft sphere (CON save negates)")
R("Touch of the Long Death", cost=("ki", (1, 10)), roll="KI*2d10", damage=True, say="roll {roll} necrotic damage (CON save halves)")
R("Wholeness of Body", uses="1/LR", heal="3*monk")
R("Hand of Harm", cost=("ki", 1), once=True, roll="MA+WIS", damage=True, say="add {roll} necrotic damage to the hit")
R("Quivering Palm", cost=("ki", 3))
R("Searing Arc Strike", cost=("ki", (2, "HALFMONK")), say="cast Burning Hands at level KI-1")
R("Shadow Arts", cost=("ki", 2))
R("Sharpen the Blade", cost=("ki", (1, 3)), fx="Sharpen the Blade", sharpen=True,
  say="+KI to attack and damage rolls with your WEAPON for 1 minute")
R("Visage of the Astral Self", cost=("ki", 1))
R("Wings Unfurled", uses="PB/LR")
R("Body of the Astral Self", roll="1d10+WIS", damage=True, say="roll {roll} and take that much off the damage")
R("Deflect Missiles", roll="1d10+DEX+monk", damage=True,
  say="roll {roll} and take that much off the damage; at 0 you catch the missile, and can throw it back for 1 ki")
R("Drunkard's Luck", cost=("ki", 2), say="cancel the disadvantage on that roll")
R("Mastery of Death", cost=("ki", 1), hp1=True, say="you drop to 1 hit point instead")
R("Slow Fall", roll="5*monk", say="reduce the falling damage by {roll}")
R("Sun Shield", roll="5+WIS", say="{roll} radiant damage to the attacker")
R("Tipsy Sway", cost=("ki", 1), say="the missed attack hits a creature of your choice within 5 ft instead")
# Kensei (Way of the Kensei)
R("Kensei's Shot", fx="Kensei's Shot")
R("Agile Parry", fx="Agile Parry", slot=False, needs="kensei melee")
R("Deft Strike", cost=("ki", 1), once=True, slot=False, roll="MA", damage=True, say="add {roll} damage of the weapon's type to the hit")
R("Unerring Accuracy", once=True, slot=False, say="reroll the missed attack")
# Paladin
for _n in ("Abjure Enemy", "Abjure the Extraplanar", "Champion Challenge", "Conquering Presence",
           "Dreadful Aspect", "Nature's Wrath", "Turn the Faithless", "Turn the Unholy",
           "Watcher's Will", "Emissary of Peace", "Rebuke the Violent"):
    R(_n, cost=("cd", 1))
R("Inspiring Smite", cost=("cd", 1), roll="2d8+paladin", say="share {roll} temporary hit points among creatures within 30 ft")
R("Turn the Tide", cost=("cd", 1), roll="1d6+CHA", say="each creature at half HP or less regains {roll} HP")
R("Avenging Angel", "Dread Lord", "Holy Nimbus", uses="1/LR")
R("Glorious Defense", uses="CHA/LR", say="the ally gets +{CHA} AC against the attack, then you can attack the attacker")
R("Vigilant Rebuke", roll="2d8+CHA", damage=True, say="roll {roll} force damage for the creature")
# Ranger
R("Detect Portal", uses="1/SR")
R("Drake's Breath", uses="1/LR", alt=("slot", 3))
R("Fey Reinforcements", uses="1/LR")
R("Hunter's Sense", uses="WIS/LR")
R("Primeval Awareness", cost=("slot", 1), say="sense the creature types for 1 minute per slot level")
R("Ethereal Step", uses="1/SR")
R("Misty Wanderer", uses="WIS/LR")
R("Magic-User's Nemesis", uses="1/SR")
R("Swarming Dispersal", uses="PB/LR", say="resistance to the damage, then teleport up to 30 ft")
R("Slayer's Prey", fx="Slayer's Prey")
R("Planar Warrior", fx="Planar Warrior")
# Rogue
R("Psychic Veil", uses="1/LR", alt=("psi", 1))
R("Wails from the Grave", uses="PB/LR")
R("Soul Blades", cost=("psi", 1))
R("Master Duelist", uses="1/SR", say="reroll the attack with advantage")
R("Spell Thief", uses="1/LR")
R("Uncanny Dodge", say="halve the attack's damage")
# Sorcerer
R("Bastion of Law", cost=("sp", (1, 5)), say="a ward of KI d8s absorbs damage until your next long rest")
R("Clockwork Cavalcade", uses="1/LR", alt=("sp", 7))
R("Draconic Presence", cost=("sp", 5))
R("Warping Implosion", uses="1/LR", alt=("sp", 5))
R("Wind Soul", uses="1/LR")
R("Hound of Ill Omen", cost=("sp", 3))
R("Revelation in Flesh", cost=("sp", (1, 4)), say="one benefit per sorcery point for 10 minutes")
R("Unearthly Recovery", uses="1/LR", heal="maxhp/2", needs="below half")
R("Waxing and Waning", cost=("sp", 1))
R("Bend Luck", cost=("sp", 2), roll="1d4", say="add or subtract {roll}")
R("Restore Balance", uses="PB/LR")
R("Storm's Fury", roll="sorcerer", say="{roll} lightning damage to the attacker (STR save or pushed 20 ft)")
R("Strength of the Grave", uses="1/LR", say="CHA save (DC 5 + the damage): on a success you drop to 1 HP instead")
# Warlock
R("Dark Delirium", "Fey Presence", "Fathomless Plunge", "Entropic Ward", uses="1/SR")
R("Eldritch Master", uses="1/LR", pact_back=True, say="your Pact Magic slots come back")
R("Grasping Tentacles", uses="1/LR", temp="warlock", say="cast Evard's Black Tentacles without a slot")
R("Limited Wish", uses="1/LR", say="can't be used again for 1d4 long rests")
R("Spirit Projection", uses="1/LR")
R("Dark One's Own Luck", uses="1/SR", roll="1d10", say="add {roll} to the roll")
R("Guardian Coil", roll="1d8", damage=True, say="roll {roll} and take that much off the damage")
R("Necrotic Husk", uses="1/LR", hp1=True, roll="2d10+warlock", damage=True,
  say="you drop to 1 HP instead; roll {roll} necrotic damage for each creature within 30 ft")
R("Searing Vengeance", uses="1/LR", heal="maxhp/2", say="you stand up and creatures within 30 ft take radiant damage and are blinded")
# Wizard
R("Benign Transposition", uses="1/LR")
R("Event Horizon", uses="1/LR", alt=("slot", 3))
R("Gravity Fissure", uses="1/LR", alt=("slot", 1))
R("Shapechanger", "The Third Eye", "Illusory Self", uses="1/SR")
R("Arcane Deflection", say="+2 AC against the attack or +4 to the save; only cantrips on your next turn")
R("Deflecting Shroud", say="{INT} force damage to up to three creatures within 60 ft")
R("Song of Defense", cost=("slot", 1), needs="bladesong", say="reduce the damage by 5 per slot level")


# ── Small helpers ─────────────────────────────────────────────────────────
def _lvl(char, cls):
    from dnd_app.core.character import class_levels
    return class_levels(char).get(cls.title() if cls != "blood hunter" else "Blood Hunter", 0)


def _numeric(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _find_pool(char, pool):
    """The resource behind a pool — numeric, or "Unlimited" (a 20th-level
    Archdruid's Wild Shape), which is never spent."""
    keys = POOLS[pool][0]
    for r in char.get("resources", []):
        if r.get("key") in keys and (_numeric(r.get("current_max")) or _unlimited(r)):
            return r
    return None


def _noun(pool, n):
    return POOLS[pool][1] if n == 1 else POOLS[pool][2]


def _slots_free(char):
    """[(label, kind, level)] for every spell slot level with one left."""
    out = []
    maxes = char.get("spell_slots_max", [0] * 9)
    used = char.get("spell_slots_used", [0] * 9)
    for lvl in range(1, 10):
        if maxes[lvl - 1] - used[lvl - 1] > 0:
            out.append((f"{_ordinal(lvl)}-level slot ({maxes[lvl - 1] - used[lvl - 1]} left)", "slot", lvl))
    pmax, pused, plvl = char.get("pact_slots_max", 0), char.get("pact_slots_used", 0), char.get("pact_slot_level", 0)
    if pmax and pmax - pused > 0:
        out.append((f"Pact Magic slot, {_ordinal(plvl)} level ({pmax - pused} left)", "pact", plvl))
    return out


def _ordinal(n):
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"


def _mods(char):
    from dnd_app.core.character import ability_mod
    return {ab: ability_mod(char, ab) for ab in ("STR", "DEX", "CON", "INT", "WIS", "CHA")}


def _pb(char):
    from dnd_app.core.calculator import get_prof_bonus
    return get_prof_bonus(char)


def _uses_max(char, uses):
    """"WIS/LR" -> (max, reset) — reset as the resources store it."""
    count, per = uses.split("/")
    reset = "LR" if per == "LR" else "SR/LR"
    if count == "PB":
        n = _pb(char)
    elif count in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
        n = max(1, _mods(char)[count])
    else:
        n = int(count)
    return max(1, n), reset


def _special_die(char, tok, name=""):
    """The dice behind a named die: MA, BI, BW, HEMODIE, NAMEDICE."""
    from dnd_app.core.character import total_level
    if tok == "MA":
        from dnd_app.core.calculator import get_martial_arts_die
        d = get_martial_arts_die(char)
        return d if d.startswith(tuple("123456789")) else "1" + d
    if tok == "BI":
        b = _lvl(char, "bard")
        return "1d12" if b >= 15 else "1d10" if b >= 10 else "1d8" if b >= 5 else "1d6"
    if tok == "BW":
        lv = total_level(char)
        return f"{2 + (lv >= 6) + (lv >= 11) + (lv >= 16)}d6"
    if tok == "HEMODIE":
        from dnd_app.core.calculator import get_hemocraft_die
        d = get_hemocraft_die(char)
        return d if d[0].isdigit() else "1" + d
    if tok == "HALO":
        d = _lvl(char, "druid")
        return "1d10" if d >= 14 else "1d8" if d >= 10 else "1d6" if d >= 6 else "1d4"
    if tok == "NAMEDICE":
        m = re.search(r"(\d+d\d+)", name)
        return m.group(1) if m else "1d6"
    return tok


def _terms(char, expr, chosen=0, name=""):
    """An amount like "1d10+DEX+monk", term by term: [(dice or None,
    multiplier, label)] -- ("1d10", 1, None), (None, 3, "DEX 3")..."""
    from dnd_app.core.character import total_level
    mods = _mods(char)
    out = []
    for term in expr.split("+"):
        term = term.strip()
        if not term:
            continue
        mult, dice, label = 1, None, None
        for f in term.split("*"):
            f = f.strip()
            if f in ("MA", "BI", "BW", "HEMODIE", "NAMEDICE", "HALO"):
                dice = _special_die(char, f, name)
            elif re.fullmatch(r"\d+d\d+", f):
                dice = f
            elif f in ("KI", "SP"):
                mult *= chosen
            elif f.isdigit():
                mult *= int(f)
            elif f in mods:
                mult *= mods[f]; label = f"{f} {mods[f]}"
            elif f == "PB":
                mult *= _pb(char); label = f"PB {_pb(char)}"
            elif f == "level":
                mult *= total_level(char); label = f"level {total_level(char)}"
            elif f.startswith("maxhp"):
                hp = char.get("max_hp", 0)
                mult *= hp // 2 if f == "maxhp/2" else hp; label = "half your maximum" if f == "maxhp/2" else "max HP"
            elif f == "FIGHTINGSPIRIT":
                fl = _lvl(char, "fighter")
                mult *= 15 if fl >= 15 else 10 if fl >= 10 else 5
            elif f.lower() in _CLASSES:
                lv = _lvl(char, f.lower()); mult *= lv; label = f"{f.title()} {lv}"
        out.append((dice, mult, label if "*" not in term else None))
    return out


def evaluate(char, expr, chosen=0, name="", rng=random):
    """Roll an amount like "1d10+DEX+monk" -> (total, "7 + DEX 3 + Monk 5")."""
    total, parts = 0, []
    for dice, mult, label in _terms(char, expr, chosen, name):
        if dice:
            n, s = map(int, dice.split("d"))
            count = n * max(0, mult)
            value = sum(rng.randint(1, s) for _ in range(count))
            parts.append((f"{count}d{s}", value, True))
        else:
            value = mult
            if label:
                ab, _, v = label.rpartition(" ")
                parts.append((f"{'+' if value >= 0 else ''}{value} {ab}", value, False))
            else:
                parts.append((f"{'+' if value >= 0 else ''}{value}", value, False))
        total += value
    # "4 (1d8)" for a lone die; "15 (8 on the 1d10, +4 DEX, +3 Monk)" otherwise
    if len(parts) == 1 and parts[0][2]:
        return total, parts[0][0]
    if len(parts) == 1:
        return total, ""
    how = ", ".join(f"{v} on the {d}" if is_die else d for d, v, is_die in parts)
    return total, how


def formula(char, expr, chosen=0, name=""):
    """What to roll, not rolled -- damage is the player's to roll:
    "1d10+DEX+monk" -> "1d10 + 8", "2d6+KI*2d6" with 2 ki -> "6d6"."""
    dice, flat = {}, 0
    for d, mult, _ in _terms(char, expr, chosen, name):
        if d:
            n, sides = map(int, d.split("d"))
            dice[sides] = dice.get(sides, 0) + n * max(0, mult)
        else:
            flat += mult
    parts = [f"{n}d{sides}" for sides, n in sorted(dice.items(), reverse=True) if n]
    if not parts:
        return str(flat)
    if flat:
        parts.append(f"{'+' if flat > 0 else '−'} {abs(flat)}")
    return " ".join([parts[0]] + [f"+ {p}" if not p[0] in "+−" else p for p in parts[1:]])


def _breath_tokens(char, say):
    """{ANCESTRY} {BWDC} {BWSAVE}: a dragonborn's Breath Weapon type and save."""
    if "{ANCESTRY}" not in say:
        return say
    from dnd_app.data.races import DRACONIC_ANCESTRY
    dtype, _, save = DRACONIC_ANCESTRY.get(char.get("draconic_ancestry", ""), ("", "", ""))
    ab = next((a for a in ("STR", "DEX", "CON", "INT", "WIS", "CHA") if f"{a} save" in save), "DEX")
    dc = 8 + _mods(char)["CON"] + _pb(char)
    return (say.replace("{ANCESTRY}", (dtype or "your ancestry's").lower())
               .replace("{BWDC}", str(dc)).replace("{BWSAVE}", ab))


def _cleaver_dice(char):
    return "2d6" if _lvl(char, "barbarian") >= 14 else "1d6"


def _summary(desc, limit=150):
    """The rules text, cut down for a toast: no "Uses = ..." sentences."""
    text = re.sub(r"\s+", " ", desc or "").strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    keep = []
    for s in sentences:
        if re.fullmatch(r"(uses?\s*=.*|\(?\d+/(lr|sr)\)?\.?|1/(short|long) rest.*"
                        r"|once per (short or long|short|long) rest\.?)", s, re.I):
            continue
        if keep and len(" ".join(keep + [s])) > limit:
            break
        keep.append(s)
    out = " ".join(keep) or text[:limit]
    return out[:limit].rstrip(" .") + ("…" if len(out) > limit else "")


def _own_resource(char, display):
    """The tracked resource that IS this action: same name (Action Surge),
    or a name that starts with it ("Experimental Elixir" -> "Experimental
    Elixirs"). Information-only entries (the Martial Arts die) never are."""
    key = normalize(display)
    full = (display or "").strip().lower()
    best = None
    for r in char.get("resources", []):
        if r.get("track") == "info":
            continue
        mx = r.get("current_max")
        if not (_numeric(mx) or str(mx).lower() == "unlimited"):
            continue
        rname = str(r.get("name", "")).lower()
        if rname == full:
            return r
        rn = normalize(rname)
        if key and (rn == key or rn.startswith(key + " ") or rn.startswith(key + "s") or rn == key + "s"):
            best = best or r
    return best


def _unlimited(r):
    return str(r.get("current_max")).lower() == "unlimited"


def _left(r):
    return "unlimited" if _unlimited(r) else f"{r.get('current', 0)}/{r.get('current_max')} left"


def _kensei_in_hand(char):
    """The kensei weapons in hand, by name ("Longsword"), each once."""
    from dnd_app.core.weapons import kensei_weapons, weapon_base
    ks = kensei_weapons(char)
    out = []
    for w in char.get("equipped_weapons", []):
        b = weapon_base(w)
        if b in ks and b not in out:
            out.append(b)
    return out


def _has_kensei_melee(char):
    from dnd_app.core.weapons import kensei_weapons, weapon_base
    from dnd_app.data.items import WEAPON_DICT
    ks = kensei_weapons(char)
    for w in char.get("equipped_weapons", []):
        b = weapon_base(w)
        if b in ks and "Melee" in WEAPON_DICT.get(b, {}).get("category", ""):
            return True
    return False


def _need_problem(char, need):
    fx = char.get("active_effects", [])
    if need == "rage" and "Rage" not in fx:
        return "only while raging"
    if need == "bladesong" and "Bladesong" not in fx:
        return "only while your Bladesong is active"
    if need == "kensei melee" and not _has_kensei_melee(char):
        return "needs a melee kensei weapon in hand"
    if need == "below half" and char.get("current_hp", 0) >= char.get("max_hp", 0) / 2:
        return "only when you're below half your hit points"
    return ""


def _lower_first(text):
    """"Attacks against you..." -> "attacks against you..." (not "DEX")."""
    if len(text) > 1 and text[0].isupper() and text[1].islower():
        return text[0].lower() + text[1:]
    return text


def _result(ok=True, toast="", slot=None, refresh=False, **kw):
    out = {"ok": ok, "toast": toast, "slot": slot, "refresh": refresh, "ask": None}
    out.update(kw)
    return out


# ── Wild Shape ────────────────────────────────────────────────────────────
def _wild_shape_check(char, display, answers):
    """None to go ahead, or the result that stops (or asks) first."""
    if not char.get("_wildshape_active"):
        return None
    from dnd_app.core.effects import WILDSHAPE_NO_CAST, WILDSHAPE_ASK
    key = display.split("(")[0].strip().lower()
    if any(b in key for b in WILDSHAPE_NO_CAST):
        return _result(False, f"Can't use {display} while Wild Shaped — you can't cast spells in beast form")
    if any(b in key for b in WILDSHAPE_ASK):
        if answers.get("wildshape") == "Use it":
            return None
        if answers.get("wildshape"):
            return _result(False, "")
        return _result(False, ask={
            "key": "wildshape",
            "title": "This needs hands, a held weapon or an unarmed strike. "
                     "Your DM decides whether your beast form can do it.",
            "options": ["Use it", "Cancel"]})
    return None


# ── The hand-written actions ──────────────────────────────────────────────
def _special(char, key, display, bucket, answers, rng):
    fx = char.setdefault("active_effects", [])
    if key == "wild shape":
        return _result(False, "Use the Wild Shape card to pick a beast and transform")
    if key == "reckless attack":
        if "Reckless Attack" in fx:
            fx.remove("Reckless Attack")
            return _result(True, "Reckless Attack off", refresh=True)
        fx.append("Reckless Attack")
        msg = ("Reckless Attack on: advantage on your Strength melee attacks this turn, "
               "and attacks against you have advantage until your next turn")
        from dnd_app.core.character import subclasses
        if _lvl(char, "barbarian") >= 2 and "battlerager" in subclasses(char).get("Barbarian", "").lower():
            con = max(1, _mods(char)["CON"])
            if con > char.get("temp_hp", 0):
                char["temp_hp"] = con
            msg += f". Reckless Abandon: {con} temporary hit points"
        return _result(True, msg, refresh=True)
    if key == "second wind":
        res = _own_resource(char, "Second Wind")
        if res is None or res.get("current", 0) <= 0:
            return _result(False, "Second Wind: no uses left (back on a short or long rest)")
        if char.get("current_hp", 0) >= char.get("max_hp", 0):
            return _result(False, "Second Wind: you're already at full hit points")
        total, how = evaluate(char, "1d10+fighter", rng=rng)
        res["current"] -= 1
        from dnd_app.core.dying import heal
        before = char.get("current_hp", 0)
        note = heal(char, total)
        return _result(True, f"Second Wind: regained {char.get('current_hp', 0) - before} HP ({how}), "
                             f"now {char.get('current_hp', 0)}/{char.get('max_hp', 0)}"
                             + (f". {note}" if note else "") + f" ({_left(res)})",
                       slot=bucket, refresh=True)
    if key == "divine smite":
        free = [s for s in _slots_free(char) if s[1] == "slot" and s[2] <= 5]
        if not free:
            return _result(False, "Divine Smite: no spell slots left to expend")
        if "slot" not in answers:
            return _result(False, ask={"key": "slot", "title": "Expend which spell slot?",
                                       "options": [s[0] for s in free]})
        if "fiend" not in answers:
            return _result(False, ask={"key": "fiend", "title": "Is the target undead or a fiend?",
                                       "options": ["No", "Yes"]})
        lvl = next(s[2] for s in free if s[0] == answers["slot"])
        char["spell_slots_used"][lvl - 1] += 1
        dice = min(5, 1 + lvl) + (answers["fiend"] == "Yes")
        return _result(True, f"Divine Smite: add {dice}d8 radiant damage to the hit (spent a "
                             f"{_ordinal(lvl)}-level slot)", slots_changed=True, refresh=True)
    if key in ("sacred weapon", "peerless athlete"):
        name = "Sacred Weapon" if key == "sacred weapon" else "Peerless Athlete"
        if name in fx:
            fx.remove(name)
            return _result(True, f"{name} off", refresh=True)
        cd = _find_pool(char, "cd")
        if cd and cd.get("current", 0) <= 0:
            return _result(False, f"{name}: no Channel Divinity uses left (back on a short or long rest)")
        if cd:
            cd["current"] -= 1
        fx.append(name)
        what = (f"+{max(1, _mods(char)['CHA'])} to attack rolls with your weapon for 1 minute"
                if name == "Sacred Weapon" else
                "advantage on Athletics and Acrobatics, double carrying capacity and jump, for 10 minutes")
        return _result(True, f"{name} on: {what}" + (f" ({_left(cd)})" if cd else ""),
                       slot=bucket, refresh=True)
    if "frenzi" in key:
        if "Rage" not in fx:
            return _result(False, "Frenzy: only while raging")
        if "Frenzy" in fx:
            fx.remove("Frenzy")
            return _result(True, "Frenzy off", refresh=True)
        fx.append("Frenzy")
        return _result(True, "Frenzy on: a melee attack as a bonus action on each turn of this rage; "
                             "one level of exhaustion when it ends", refresh=True)
    if key == "lay on hands":
        pool = _find_pool(char, "loh") or _own_resource(char, display)
        if not pool:
            return None
        if pool.get("current", 0) <= 0:
            return _result(False, "Lay on Hands: the pool is empty (refills on a long rest)")
        if "target" not in answers:
            return _result(False, ask={"key": "target", "title": "Who is it for?",
                                       "options": ["Yourself", "Someone else"]})
        cap = pool["current"]
        if answers["target"] == "Yourself":
            cap = min(cap, max(0, char.get("max_hp", 0) - max(0, char.get("current_hp", 0))))
            if cap <= 0:
                return _result(False, "Lay on Hands: you're already at full hit points")
        if "amount" not in answers:
            steps = sorted({n for n in (1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100) if n <= cap} | {cap})
            return _result(False, ask={"key": "amount", "title": f"How many hit points? ({pool['current']} in the pool)",
                                       "options": [str(n) for n in steps]})
        amount = min(cap, int(answers["amount"]))
        pool["current"] -= amount
        if answers["target"] == "Yourself":
            from dnd_app.core.dying import heal
            note = heal(char, amount)
            return _result(True, f"Lay on Hands: regained {amount} HP, now {char.get('current_hp')}/{char.get('max_hp')}"
                                 + (f". {note}" if note else "") + f" ({pool['current']} left in the pool)",
                           slot=bucket, refresh=True)
        return _result(True, f"Lay on Hands: the creature regains {amount} HP ({pool['current']} left in the pool)",
                       slot=bucket, refresh=True)
    return None


# ── Costs ─────────────────────────────────────────────────────────────────
def _costs(spec):
    c = spec.get("cost")
    if not c:
        return []
    return c if isinstance(c, list) else [c]


def _pay(char, display, costs, answers, check_only=False):
    """Check (and with check_only False, spend) every cost. Returns
    (problem or "", ask or None, spent text list, chosen number)."""
    spent, chosen = [], 0
    for pool, n in costs:
        if pool == "slot":
            free = [s for s in _slots_free(char)
                    if (s[1] == "pact" if n == "pact" else s[2] >= (n if isinstance(n, int) else 1))]
            if not free:
                what = ("Pact Magic slots" if n == "pact" else
                        f"{_ordinal(n)}-level or higher slots" if n > 1 else "spell slots")
                return (f"no {what} left", None, [], 0)
            if len(free) > 1 and "slot" not in answers:
                return ("", {"key": "slot", "title": "Expend which spell slot?",
                             "options": [s[0] for s in free]}, [], 0)
            pick = next((s for s in free if s[0] == answers.get("slot")), free[0])
            if not check_only:
                if pick[1] == "pact":
                    char["pact_slots_used"] = char.get("pact_slots_used", 0) + 1
                else:
                    char["spell_slots_used"][pick[2] - 1] += 1
            spent.append(f"spent a {_ordinal(pick[2])}-level {'Pact Magic ' if pick[1] == 'pact' else ''}slot")
            chosen = pick[2]
            continue
        res = _find_pool(char, pool)
        if res is None:
            return (f"you have no {POOLS[pool][2]}", None, [], 0)
        if _unlimited(res):
            spent.append(f"{POOLS[pool][2]} unlimited")
            continue
        have = res.get("current", 0)
        if isinstance(n, tuple):
            lo, hi = n
            if hi == "HALFMONK":
                hi = max(lo, _lvl(char, "monk") // 2)
            hi = min(hi, have)
            if hi < lo:
                return (f"needs at least {lo} {_noun(pool, lo)} ({have} left)", None, [], 0)
            if f"n_{pool}" not in answers:
                return ("", {"key": f"n_{pool}", "title": f"How many {POOLS[pool][2]}? ({have} left)",
                             "options": [str(i) for i in range(lo, hi + 1)]}, [], 0)
            n = int(answers[f"n_{pool}"])
            chosen = n
        if have < n:
            return (f"needs {n} {_noun(pool, n)} ({have} left)", None, [], 0)
        if not check_only and n:
            res["current"] = have - n
        if n:
            spent.append(f"{n} {_noun(pool, n)} spent, {res['current'] if not check_only else have - n} left")
    return ("", None, spent, chosen)


# ── Per-rest uses with no other tracker ───────────────────────────────────
def _use_key(name):
    return "use_" + re.sub(r"[^a-z0-9]+", "_", normalize(name)).strip("_")


_FEATURE_USE_CACHE = {}


def feature_use_resources(char, existing):
    """Resources for the per-rest uses in RULES that the character's
    actions have and nothing else tracks yet. Called by update_all."""
    from dnd_app.core.character import class_levels
    sig = (tuple(sorted((c.get("class"), c.get("level"), c.get("subclass", "")) for c in char.get("classes", []))),
           char.get("race"), char.get("subrace"), tuple(sorted(char.get("feats", []))),
           tuple(sorted(_mods(char).items())), _pb(char),
           tuple(sorted((char.get("_choices", {}).get("optional_features") or {}).items())))
    cached = _FEATURE_USE_CACHE.get(sig)
    if cached is None:
        from dnd_app.core.actions import build_action_abilities
        probe = dict(char)
        probe["resources"] = list(existing)
        try:
            buckets = build_action_abilities(probe)
        except Exception:
            buckets = {}
        cached, seen = [], set()
        for bucket, entries in buckets.items():
            for e in entries:
                if len(e) > 3 and e[3] is not None:
                    continue
                display, desc = e[0], e[1]
                spec = RULES.get(normalize(display))
                if not spec or not spec.get("uses"):
                    continue
                name = display.split("(")[0].strip()
                key = _use_key(spec.get("share") or name)
                if key in seen:
                    continue
                if _own_resource({"resources": existing}, name):
                    continue
                seen.add(key)
                mx, reset = _uses_max(char, spec["uses"])
                cached.append({"name": spec.get("share") or name, "key": key, "reset": reset,
                               "current_max": mx, "track": "uses", "note": _summary(desc, 200),
                               "source_class": "", "subclass": ""})
        # shared counters (Dragon Fear uses the Breath Weapon's)
        if len(_FEATURE_USE_CACHE) > 64:
            _FEATURE_USE_CACHE.clear()
        _FEATURE_USE_CACHE[sig] = cached
    return [dict(r) for r in cached]


def _uses_resource(char, display, spec):
    name = spec.get("share") or display.split("(")[0].strip()
    for r in char.get("resources", []):
        if r.get("key") == _use_key(name):
            return r
    return _own_resource(char, name)


# ── Use ───────────────────────────────────────────────────────────────────
def use_action(char, bucket, display, desc="", answers=None, rng=random):
    answers = dict(answers or {})
    slot = bucket if bucket in ("Action", "Bonus Action", "Reaction") else None
    key = normalize(display)
    fx = char.setdefault("active_effects", [])

    # 1. Wild Shape
    stop = _wild_shape_check(char, display, answers)
    if stop:
        return stop

    # 2. hand-written
    out = _special(char, key, display, slot, answers, rng)
    if out is not None:
        return out

    spec = rule_for(display)
    if spec is not None:
        return _use_rule(char, display, desc, spec, slot, answers, rng)

    # 3b. a magic item's action: its charges, its once-a-day use
    item = _item_for(char, display)
    if item:
        return _use_item(char, item, display, desc, slot, answers)

    # 4. its own tracked resource
    res = _own_resource(char, display)
    if res is not None:
        return _use_resource(char, display, desc, res, slot)

    # 5. just the turn
    return _result(True, f"{display}: {_lower_first(_summary(desc)) or 'used'}", slot=slot)


# ── Magic items ───────────────────────────────────────────────────────────
# Item effects switched on and off from the item's action card
ITEM_TOGGLES = {"Flame Tongue": "Flame Tongue"}
_DAILY_RE = re.compile(r"1/day|once (?:per|a) (?:day|dawn)|until the next dawn|\(1/day", re.I)
_CHARGE_RE = re.compile(r"(\d+)\s*(?:ch\b|charges?\b)", re.I)


def _item_for(char, display):
    """The magic item an action card comes from ("" if none): a granted
    action (Flame Tongue), a spell cast from one ("Fireball (Wand of
    Fireballs)") or a card named after it ("Holy Symbol of Ravenkind (1/day)")."""
    from dnd_app.core.magic_items import _active_item_names
    names = _active_item_names(char)
    if not names:
        return ""
    for ia in char.get("item_actions", []):
        if ia.get("name") == display and ia.get("source") in names:
            return ia["source"]
    m = re.search(r"\(([^()]+)\)\s*$", display or "")
    if m and m.group(1) in names:
        return m.group(1)
    base = (display or "").split("(")[0].strip().lower()
    for n in names:
        if base and base == n.lower():
            return n
    return ""


def _use_item(char, item, display, desc, slot, answers):
    """Step by step:
      1. an effect the item switches on or off (Flame Tongue's flames)
      2. its charges: as many as the card says (asks when it lists several,
         "1 ch: Create Undead. 3 ch: Circle of Death"), refused when they've
         run out
      3. a once-a-day action with no charges: its own use, back at dawn"""
    fx = char.setdefault("active_effects", [])
    name = display.split("(")[0].strip()
    toggle = ITEM_TOGGLES.get(item) if name == item else None
    if toggle:
        from dnd_app.core.effects import EFFECT_TABLE
        if toggle in fx:
            fx.remove(toggle)
            return _result(True, f"{item} off: the flames go out", slot=slot, refresh=True)
        fx.append(toggle)
        note = EFFECT_TABLE.get(toggle, {}).get("note", "").rstrip(".")
        return _result(True, f"{item} on: {_lower_first(note)}", slot=slot, refresh=True)
    text = f"{display} {desc}"
    charges = char.get("item_charges", {}).get(item)
    tail = ""
    if charges and charges.get("max", 0) > 0:
        from dnd_app.data.magic_items import get_magic_item
        have = charges.get("current", 0)
        rules = (get_magic_item(item) or {}).get("desc", "") or ""
        spell_card = any(f"{d.get('spell')} ({item})" == display for d in char.get("item_granted_spell_details", []))
        if spell_card:
            # a spell cast from the item: 1 charge, or more for a stronger
            # casting when the item allows it (Wand of Fireballs)
            costs = list(range(1, charges["max"] + 1)) if re.search(r"\b1 or more\b", rules, re.I) else [1]
        else:
            costs = sorted({int(n) for n in _CHARGE_RE.findall(desc or "") if int(n) > 0}) or [1]
        free = "at will" in (desc or "").lower()
        if len(costs) > 1 or free:
            opts = (["No charge"] if free else []) + [f"{n} charge{'s' if n != 1 else ''}" for n in costs if n <= have]
            if not opts:
                return _result(False, f"{item}: not enough charges left ({have}/{charges['max']}, back at dawn)")
            if answers.get("charges") not in opts:
                return _result(False, ask={"key": "charges", "title": f"How many charges? ({have} left)",
                                           "options": opts})
            n = 0 if answers["charges"] == "No charge" else int(answers["charges"].split()[0])
        else:
            n = costs[0]
        if have < n:
            return _result(False, f"{item}: {'no' if have == 0 else 'not enough'} charges left "
                                  f"({have}/{charges['max']}, back at dawn)")
        charges["current"] = have - n
        if n:
            tail = f" ({n} charge{'s' if n != 1 else ''} spent, {charges['current']}/{charges['max']} left)"
    elif _DAILY_RE.search(text):
        uses = char.setdefault("item_uses", {}).setdefault(display, {"current": 1, "max": 1, "recharge": "dawn"})
        if uses.get("current", 0) <= 0:
            return _result(False, f"{display}: already used today (back at dawn)")
        uses["current"] -= 1
        tail = " (used for today, back at dawn)"
    card = next((d for d in char.get("item_granted_spell_details", [])
                 if f"{d.get('spell')} ({item})" == display), None)
    if card:
        # "Cast Fireball from the Wand of Fireballs at 4th level, save DC 15"
        from dnd_app.data.spells import get_spell
        base = (get_spell(card["spell"]) or {}).get("level", 0) or 0
        n = int(str(answers.get("charges", "1 charge")).split()[0]) if str(answers.get("charges", "1")).split()[0].isdigit() else 1
        lvl = base + max(0, n - 1)
        text = (f"Cast {card['spell']} from the {item}"
                + (f" at {_ordinal(lvl)} level" if lvl > base and base else "")
                + (f", save DC {card['dc']}" if card.get("dc") else ""))
        note_spell_cast(char, card["spell"])
        return _result(True, text + tail, slot=slot, refresh=bool(tail))
    return _result(True, f"{display}: {_lower_first(_summary(desc)) or 'used'}{tail}", slot=slot,
                   refresh=bool(tail))


def _use_resource(char, display, desc, res, slot):
    from dnd_app.core.effects import RESOURCE_POOL_TOGGLES
    from dnd_app.core.calculator import effect_start_problem, on_effect_started
    fx = char.setdefault("active_effects", [])
    toggle = display in RESOURCE_POOL_TOGGLES
    if toggle and display in fx:
        return _result(False, f"{display} is already on — end it from its row under Resources & Charges")
    if toggle:
        why = effect_start_problem(char, display)
        if why:
            return _result(False, f"{display}: {why}")
    if not _unlimited(res):
        if res.get("current", 0) <= 0:
            reset = {"LR": "a long rest", "SR": "a short rest", "SR/LR": "a short or long rest"}.get(res.get("reset"), "a rest")
            return _result(False, f"{display}: no uses left (back on {reset})")
        res["current"] = res.get("current", 0) - 1
    note = ""
    if toggle:
        fx.append(display)
        note = on_effect_started(char, display) or ""
    what = _lower_first(_toggle_say(char, display) if toggle else (_summary(desc) or "used"))
    msg = f"{display}{' on' if toggle else ''}: {what} ({_left(res)})" + (f". {note}" if note else "")
    if res.get("key") == "action_surge" or display.startswith("Action Surge"):
        char["_action_surge_used_this_turn"] = True
        slot = None
    return _result(True, msg, slot=slot, refresh=True)


def _toggle_say(char, name):
    if name == "Rage":
        from dnd_app.core.calculator import get_rage_damage
        return (f"resistance to bludgeoning, piercing and slashing damage, {get_rage_damage(char)} damage "
                f"on Strength melee attacks, advantage on Strength checks and saves")
    if name == "Bladesong":
        return (f"+{max(1, _mods(char)['INT'])} AC, +10 ft speed, advantage on Acrobatics, "
                f"+{max(1, _mods(char)['INT'])} to Constitution saves to keep concentrating")
    from dnd_app.core.effects import EFFECT_TABLE
    if EFFECT_TABLE.get(name, {}).get("note"):
        return EFFECT_TABLE[name]["note"].rstrip(".")
    from dnd_app.data.feature_tooltips import FEATURE_DESCS
    return _summary(FEATURE_DESCS.get(name, ""), 160) or "on"


def _use_rule(char, display, desc, spec, slot, answers, rng):
    from dnd_app.core.effects import EFFECT_TABLE
    fx = char.setdefault("active_effects", [])
    name = display.split("(")[0].strip()
    if spec.get("slot") is False:
        slot = None
    # requirements
    if spec.get("needs"):
        why = _need_problem(char, spec["needs"])
        if why:
            return _result(False, f"{name}: {why}")
    turn = char.setdefault("_turn_uses", [])
    if spec.get("once") and name in turn:
        return _result(False, f"{name}: already used this turn")
    # an effect that's on goes off again (Agile Parry, Kensei's Shot...);
    # one that cost something stays until it ends (Sharpen the Blade can
    # be used again to change its bonus)
    effect = spec.get("fx")
    if effect and effect in fx and not (spec.get("sharpen") or spec.get("again")):
        if _costs(spec) or spec.get("uses"):
            return _result(False, f"{name}: already on")
        fx.remove(effect)
        return _result(True, f"{name} off", refresh=True)

    # own uses, or the alternate cost once they're gone
    spent = []
    uses = _uses_resource(char, display, spec) if spec.get("uses") or spec.get("share") else None
    costs = _costs(spec)
    if uses is not None and not _unlimited(uses):
        if uses.get("current", 0) > 0:
            uses_ok = True
        elif spec.get("alt"):
            alt = spec["alt"]
            if answers.get("alt") != "Yes":
                if answers.get("alt"):
                    return _result(False, "")
                what = (f"a {_ordinal(alt[1])}-level or higher spell slot" if alt[0] == "slot" and alt[1] > 1
                        else "a spell slot" if alt[0] == "slot" else f"{alt[1]} {_noun(alt[0], alt[1])}")
                return _result(False, ask={"key": "alt", "title": f"No free uses left. Use it by spending {what}?",
                                           "options": ["Yes", "No"]})
            costs = costs + [alt]
            uses_ok = False
        else:
            reset = {"LR": "a long rest", "SR/LR": "a short or long rest"}.get(uses.get("reset"), "a rest")
            return _result(False, f"{name}: no uses left (back on {reset})")
    else:
        uses_ok = False

    # Sharpen the Blade: the one kensei weapon you touch -- in your hand
    sharpened = ""
    if spec.get("sharpen"):
        held = _kensei_in_hand(char)
        if not held:
            return _result(False, f"{name}: needs a kensei weapon in hand")
        if len(held) > 1 and "weapon" not in answers:
            return _result(False, ask={"key": "weapon", "title": "Which kensei weapon?", "options": held})
        sharpened = answers.get("weapon") if answers.get("weapon") in held else held[0]

    # Crimson Rite: which rite, on which weapon (Blood Hunter)
    rite = rite_on = ""
    if spec.get("rite"):
        from dnd_app.core.riders import crimson_rite_options
        held = list(dict.fromkeys(char.get("equipped_weapons", [])))
        if "Hybrid Transformation" in fx:
            held.append("Unarmed strikes")
        if not held:
            return _result(False, f"{name}: needs a weapon in hand")
        rites = crimson_rite_options(char)
        if answers.get("rite") not in rites:
            return _result(False, ask={"key": "rite", "title": "Which rite?", "options": rites})
        if len(held) > 1 and answers.get("weapon") not in held:
            return _result(False, ask={"key": "weapon", "title": "On which weapon?", "options": held})
        rite = answers["rite"]
        rite_on = answers.get("weapon") if answers.get("weapon") in held else held[0]
    # Elemental Cleaver: which weapon, which element
    picked = {}
    if spec.get("pick_weapon"):
        held = list(dict.fromkeys(char.get("equipped_weapons", [])))
        if not held:
            return _result(False, f"{name}: needs a weapon in hand")
        if len(held) > 1 and answers.get("weapon") not in held:
            return _result(False, ask={"key": "weapon", "title": "Which weapon?", "options": held})
        picked["weapon"] = answers.get("weapon") if answers.get("weapon") in held else held[0]
    if spec.get("pick_type"):
        if answers.get("type") not in spec["pick_type"]:
            return _result(False, ask={"key": "type", "title": "Which damage type?",
                                       "options": list(spec["pick_type"])})
        picked["type"] = answers["type"].lower()

    problem, ask, _, _ = _pay(char, name, costs, answers, check_only=True)
    if ask:
        return _result(False, ask=ask)
    if problem:
        return _result(False, f"{name}: {problem}")

    # damage you take for it (Crimson Rite, Vital Sacrifice): you roll it
    self_hurt = 0
    if spec.get("self_damage"):
        die = formula(char, spec["self_damage"], name=display)
        m = re.fullmatch(r"1d(\d+)", die)
        if m:
            if not str(answers.get("self_roll", "")).isdigit():
                return _result(False, ask={"key": "self_roll", "title": f"Roll {die} for the necrotic damage you take. What did you roll?",
                                           "options": [str(i) for i in range(1, int(m.group(1)) + 1)]})
            self_hurt = int(answers["self_roll"])
        else:
            self_hurt = evaluate(char, spec["self_damage"], name=display, rng=rng)[0]

    # heal targets
    if spec.get("target") == "ask" and "target" not in answers:
        return _result(False, ask={"key": "target", "title": "Who is it for?", "options": ["Yourself", "Someone else"]})
    healing_you = spec.get("heal") or (spec.get("target") == "ask" and answers.get("target") == "Yourself")
    if healing_you and char.get("current_hp", 0) >= char.get("max_hp", 0):
        return _result(False, f"{name}: you're already at full hit points")

    # pay for real
    _, _, spent, chosen = _pay(char, name, costs, answers)
    if uses_ok:
        uses["current"] -= 1
        left = uses["current"]
        spent.append(f"{left} of {uses['current_max']} use{'s' if uses['current_max'] != 1 else ''} left")
    if spec.get("once"):
        turn.append(name)

    lines, refresh = [], bool(spent)
    say = spec.get("say", "")
    say = say.replace("KI-1", str(max(1, chosen - 1))).replace("+KI", f"+{chosen}").replace("KI d8s", f"{chosen}d8s")
    say = say.replace("WEAPON", sharpened.lower())
    say = say.replace("{PB}", str(_pb(char))).replace("{CHA}", str(max(1, _mods(char)["CHA"]))).replace("{INT}", str(max(1, _mods(char)["INT"])))
    # rolls
    say = _breath_tokens(char, say)
    if spec.get("roll") and spec.get("damage"):
        lines.append(say.replace("{roll}", formula(char, spec["roll"], chosen=chosen, name=display)))
        say = ""
    elif spec.get("roll"):
        total, how = evaluate(char, spec["roll"], chosen=chosen, name=display, rng=rng)
        rolled = f"{total} ({how})" if how else str(total)
        if spec.get("target") == "ask" and answers.get("target") == "Yourself":
            from dnd_app.core.dying import heal
            if spec.get("heal_self"):
                total, how = evaluate(char, spec["heal_self"], chosen=chosen, rng=rng)
            before = char.get("current_hp", 0)
            note = heal(char, total)
            lines.append(f"regained {char.get('current_hp', 0) - before} HP" + (f" ({how})" if how else "")
                         + f", now {char.get('current_hp')}/{char.get('max_hp')}" + (f". {note}" if note else ""))
            refresh = True
        else:
            lines.append(say.replace("{roll}", rolled) if "{roll}" in say else f"{say} {rolled}".strip())
        say = ""
    if spec.get("self_damage"):
        from dnd_app.core.dying import take_damage
        take_damage(char, self_hurt)
        hurt = f"you take {self_hurt} necrotic damage, now {char.get('current_hp', 0)}/{char.get('max_hp', 0)} HP"
        lines.append(say.replace("you take {roll} necrotic damage", hurt) if say else hurt)
        say, refresh = "", True
    if rite:
        from dnd_app.core.riders import CRIMSON_RITES
        from dnd_app.core.calculator import get_hemocraft_die
        details = char.setdefault("effect_details", {})
        if effect not in fx:
            details["Crimson Rite"] = {"rites": {}}
        details.setdefault("Crimson Rite", {}).setdefault("rites", {})[rite_on] = rite
        what = "your unarmed strikes" if rite_on == "Unarmed strikes" else f"your {rite_on}"
        lines.append(f"{rite} on {what}: +{get_hemocraft_die(char)} {CRIMSON_RITES.get(rite, '')} "
                     f"damage on every hit until your next rest")
    if picked:
        char.setdefault("effect_details", {})[effect] = dict(picked)
    if spec.get("heal"):
        total, how = evaluate(char, spec["heal"], chosen=chosen, rng=rng)
        from dnd_app.core.dying import heal
        before = char.get("current_hp", 0)
        note = heal(char, total)
        lines.append(f"regained {char.get('current_hp', 0) - before} HP" + (f" ({how})" if how else "")
                     + f", now {char.get('current_hp')}/{char.get('max_hp')}" + (f". {note}" if note else ""))
        refresh = True
    if spec.get("temp"):
        total, how = evaluate(char, spec["temp"], chosen=chosen, rng=rng)
        cur = char.get("temp_hp", 0)
        if spec.get("replace_temp") or total > cur:
            char["temp_hp"] = total
            lines.append(f"{total} temporary hit points" + (f" ({how})" if how else ""))
        else:
            lines.append(f"you keep your {cur} temporary hit points (more than {total})")
        refresh = True
    if spec.get("hp1"):
        if char.get("current_hp", 0) <= 0 and not char.get("is_dead"):
            char["current_hp"] = 1
            char["death_saves"] = {"successes": 0, "failures": 0}
        refresh = True
    if spec.get("pact_back"):
        char["pact_slots_used"] = 0
        refresh = True
    if spec.get("surge"):
        char["_action_surge_used_this_turn"] = True
    if effect:
        if spec.get("sharpen"):
            char["sharpen_the_blade"] = {"bonus": chosen, "weapon": sharpened}
        if effect not in fx:
            fx.append(effect)
        note = EFFECT_TABLE.get(effect, {}).get("note", "")
        if spec.get("sharpen"):
            note = say or note
            say = ""
        if rite:
            note = ""
        if picked:
            where = f" on your {picked['weapon']}" if picked.get("weapon") else ""
            if effect == "Elemental Cleaver":
                note = f"+{_cleaver_dice(char)} {picked.get('type', '')} damage{where} while you rage"
            else:
                note = f"+1d4 {picked.get('type', '')} damage{where} for 1 minute"
        lines.insert(0, _lower_first(note.rstrip(".")) if note else "")
        name = f"{name} on"
        refresh = True
    if say:
        lines.append(say)
    if not any(lines):
        lines.append(_lower_first(_summary(desc)) or "used")
    text = f"{name}: " + "; ".join(l for l in lines if l)
    tail = ", ".join(s for s in spent if s)
    if tail:
        text += f" ({tail})"
    return _result(True, text, slot=slot, refresh=refresh or bool(effect),
                   slots_changed=any("slot" in s for s in spent))


# ── Reopening a character ─────────────────────────────────────────────────
def leftover_effects(char) -> list:
    """Effects still on that a short rest would end -- Rage, Bladesong,
    Sharpen the Blade, a potion's hour... -- for the "have these ended?"
    question when a saved character is opened again (the set both apps'
    short rests clear). Not the turn-long ones (Dodge, Agile Parry...):
    those end with the next New Turn anyway."""
    from dnd_app.core.effects import EFFECT_TABLE, RESOURCE_POOL_TOGGLES
    return [n for n in char.get("active_effects", [])
            if n not in TURN_EFFECTS
            and (EFFECT_TABLE.get(n, {}).get("duration_category") == "short"
                 or n in RESOURCE_POOL_TOGGLES)]


def take_leftover_effects(char) -> list:
    """leftover_effects, once, right after the character was opened from
    a save (core/save_load.py marks it) -- [] any other time."""
    if not char.pop("_reopened", False):
        return []
    return leftover_effects(char)


def end_effects(char, names) -> list:
    """End these effects (the player says they're over). Returns the ones
    that were on."""
    fx = char.get("active_effects", [])
    ended = [n for n in names if n in fx]
    char["active_effects"] = [n for n in fx if n not in ended]
    if "Sharpen the Blade" in ended:
        char.pop("sharpen_the_blade", None)
    # what each was cast on goes with it (a smite that landed, a weapon pick)
    for n in ended:
        (char.get("effect_details") or {}).pop(n, None)
    return ended


# ── New turn ──────────────────────────────────────────────────────────────
def new_turn(char) -> list:
    """Start of your turn: the effects that last until now end, and the
    once-per-turn uses come back. Returns what ended."""
    fx = char.get("active_effects", [])
    ended = [n for n in fx if n in TURN_EFFECTS]
    if ended:
        char["active_effects"] = [n for n in fx if n not in TURN_EFFECTS]
    char["_turn_uses"] = []
    char["_turn_spells"] = []
    return ended


def note_spell_cast(char, name) -> None:
    """A spell was cast this turn: the attack dialog then offers no other
    spell (the 2024 Divine Smite) until New Turn."""
    char.setdefault("_turn_spells", []).append(name)
