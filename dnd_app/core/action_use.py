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
TURN_EFFECTS = ("Reckless Attack", "Dodge", "Agile Parry", "Kensei's Shot", "Fighting Spirit", "Steady Aim",
                "Precise Strike", "Maelstrom Aura")

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


def _mpmm(char):
    """A Monsters of the Multiverse race (its traits count by proficiency bonus)."""
    return "MPMM" in (char.get("species") or char.get("race", "") or "")


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
R("Zealous Presence", uses="1/LR")
R("Elemental Cleaver", needs="rage", fx="Elemental Cleaver", pick_weapon=True,
  pick_type=("Acid", "Cold", "Fire", "Lightning", "Thunder"))
R("Fanatical Focus", needs="rage", once_per="Rage", say="reroll the failed saving throw and use the new roll")
R("Battlerager Charge", needs="rage", say="Dash as a bonus action")
R("Battlerager Armor", needs="rage", say="attack with your armor spikes: 1d4 piercing")
# Bard
R("Enthralling Performance", uses="1/SR")
R("Performance of Creation", uses="1/LR", alt=("slot", 2))
R("Shadow Lore", uses="1/LR")
R("Universal Speech", uses="1/LR", alt=("slot", 1))
R("Words of Terror", uses="1/SR")
R("Mantle of Majesty", uses="1/LR")
R("Unbreakable Majesty", uses="1/SR")
R("Unsettling Words", cost=("bi", 1), roll="BI", say="the creature subtracts {roll} from its next saving throw")
R("Cutting Words", cost=("bi", 1), roll="BI", say="subtract {roll} from the roll")
R("Peerless Skill", cost=("bi", 1), roll="BI", say="add {roll} to the check")
R("Infectious Inspiration", uses="CHA/LR")
# Blood Hunter
R("Blood Curse of the Howl", "Blood Curse of Corrosion", "Blood Curse of the Exorcist",
  "Blood Curse of the Souleater", "Blood Curse of the Anxious", "Blood Curse of Binding",
  "Blood Curse of Bloated Agony", "Blood Curse of the Eyeless", "Blood Curse of the Fallen Puppet",
  "Blood Curse of the Marked", "Blood Curse of the Muddled Mind", "Blood Curse of Spell Sunder",
  "Blood Curse of the Exposed", cost=("maledict", 1), ask="Amplify the curse?", choose=[
      {"label": "Invoke it", "say": ""},
      {"label": "Amplify it (take your hemocraft die in necrotic damage)", "self_damage": "HEMODIE",
       "say": "amplified"}])
R("Revealed Arcana", uses="1/LR", cost=("slot", "pact"), spell=True,
  say="cast your patron's Revealed Arcana spell with the Pact Magic slot")
R("Unsealed Arcana", uses="1/LR", spell=True, say="cast your patron's Unsealed Arcana spell without a spell slot")
R("Crimson Rite", self_damage="HEMODIE", fx="Crimson Rite", rite=True, again=True)
R("Mutagencraft", cost=("mut", 1))
R("Rite Revival", hp1=True, say="end your active rites: you drop to 1 hit point instead")
# Cleric
for _n in ("Arcane Abjuration", "Artisan's Blessing", "Charm Animals and Plants", "Cloak of Shadows",
           "Invoke Duplicity", "Order's Demand", "Path to the Grave", "Read Thoughts", "Turn Undead",
           "Twilight Sanctuary", "Feat of Strength", "Knowledge of the Ages", "Destructive Wrath",
           "Oketra's Blessing", "Rhonas' Blessing", "War God's Blessing"):
    R(_n, cost=("cd", 1))
R("Balm of Peace", cost=("cd", 1), roll="2d6+WIS", say="each creature you touch regains {roll} HP")
R("Preserve Life", cost=("cd", 1), roll="5*cleric", say="share {roll} HP among creatures within 30 ft (up to half their maximum)")
R("Radiance of the Dawn", cost=("cd", 1), roll="2d10+cleric", damage=True,
  say="the darkness is dispelled; roll {roll} radiant damage for each hostile creature within 30 ft (CON save halves)")
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
R("Telekinetic Master", uses="1/LR", alt=("psi", 1))
R("Bulwark of Force", uses="1/LR", alt=("psi", 1))
R("Telekinetic Adept", uses="1/SR", alt=("psi", 1), say="Psi-Powered Leap: fly at double your walking speed until the end of the turn")
R("Runic Shield", uses="PB/LR", say="the attacker rerolls and must use the new roll")
R("Shadow Martyr", uses="1/SR")
R("Strength before Death", uses="1/LR")
R("Warding Maneuver", uses="CON/LR", roll="1d8", say="+{roll} AC against that attack; if it still hits, resistance to its damage")
R("Fighting Spirit", uses="3/LR", fx="Fighting Spirit", temp="FIGHTINGSPIRIT")
# Feats and races
R("Stone's Endurance", uses=lambda c: "PB/LR" if _mpmm(c) else "1/SR", roll="1d12+CON", damage=True,
  say="roll {roll} and take that much off the damage")
R("Breath Weapon", uses=lambda c: "PB/LR" if _ftd_breath(c) else "1/SR", roll="BW", damage=True,
  say="roll {roll} {ANCESTRY} damage (DC {BWDC} {BWSAVE} save halves)")
R("Dragon Fear", share="Breath Weapon")
R("Grovel, Cower, and Beg", "Daunting Roar", uses="1/SR")
R("Hungry Jaws", uses=lambda c: "PB/LR" if _mpmm(c) else "1/SR",
  choose=lambda c: [{"label": "go", "temp": "PB" if _mpmm(c) else "CON"}])
R("Defensive Duelist", say="+{PB} AC against that attack")
R("Healer", roll="1d6+4", target="ask", heal_self="1d6+4+level",
  say="the creature regains {roll} HP plus its number of Hit Dice")
R("Inspiring Leader", temp="level+CHA", say="up to six creatures, you included, gain temporary hit points")
R("Adrenaline Rush", uses="PB/LR", temp="PB", say="Dash as a bonus action")
R("Healing Hands", uses="1/LR", target="ask", say="the creature regains {roll} HP",
  choose=lambda c: [{"label": "go", "roll": "PB*1d4" if _mpmm(c) else "level"}])
R("Hidden Step", uses=lambda c: "PB/LR" if _mpmm(c) else "1/SR",
  say="you turn invisible until the start of your next turn, or until you attack, make a damage roll or force a "
      "saving throw")
R("Fury of the Small", uses=lambda c: "PB/LR" if _mpmm(c) else "1/SR", slot=False, choose=lambda c: [
    {"label": "go", "say": f"add {_pb(c) if _mpmm(c) else _level(c)} to the damage against the larger creature"}])
R("Vital Sacrifice", self_damage="1d6", say="you take {roll} necrotic damage for a blood boon that lasts 1 hour")
R("Favored Foe", uses="PB/LR", fx="Favored Foe")
R("Cunning Action", say="Dash, Disengage or Hide")
R("Chromatic Infusion", uses="1/LR", fx="Chromatic Infusion", pick_weapon=True,
  pick_type=("Acid", "Cold", "Fire", "Lightning", "Poison"))
# Monk
R("Flurry of Blows", cost=("ki", 1), say="make two unarmed strikes")
R("Patient Defense", cost=("ki", 1), fx="Dodge")
R("Step of the Wind", cost=("ki", 1), say="Dash or Disengage; your jump distance doubles this turn")
R("Hand of Healing", cost=("ki", 1), roll="MA+WIS", target="ask", say="the creature regains {roll} HP")
R("Hand of Ultimate Mercy", cost=("ki", 5), uses="1/LR", roll="4d10+WIS", say="the creature returns to life with {roll} HP")
R("Radiant Sun Bolt", roll="MA+DEX", damage=True, say="on a hit, roll {roll} radiant damage")
R("Searing Sunburst", cost=("ki", (0, 3)), roll="2d6+KI*2d6", damage=True, say="roll {roll} radiant damage for each creature in the 20-ft sphere (CON save negates)")
R("Touch of the Long Death", cost=("ki", (1, 10)), roll="KI*2d10", damage=True, say="roll {roll} necrotic damage (CON save halves)")
R("Wholeness of Body", uses="1/LR", heal="3*monk")
R("Hand of Harm", cost=("ki", 1), once=True, roll="MA+WIS", damage=True, say="add {roll} necrotic damage to the hit")
R("Searing Arc Strike", cost=("ki", (2, "HALFMONK")), say="cast Burning Hands at level KI-1")
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
R("Necrotic Husk", uses="1/LR", hp1=True, roll="2d10+warlock", damage=True,
  say="you drop to 1 HP instead; roll {roll} necrotic damage for each creature within 30 ft")
# Wizard
R("Benign Transposition", uses="1/LR")
R("Event Horizon", uses="1/LR", alt=("slot", 3))
R("Shapechanger", "The Third Eye", "Illusory Self", uses="1/SR")
R("Dragon Wings", fx="Dragon Wings")
# Feats (actions.py _feat_cards)
R("Lucky", share="Luck Points", uses="3/LR", slot=False, roll="1d20",
  say="your extra d20: {roll}. Choose which d20 counts")
R("Chef's Treat", share="Chef's Treats", uses="PB/LR", temp="PB", say="you eat one of your treats")


def _giant_strikes(char):
    """Strike of the Giants: the strike you chose -- known from the giant
    feat you took after it, or asked."""
    strikes = {
        "Cloud Strike": {"say": "add 1d4 thunder damage to the hit; the target makes a DC {GIANT_DC} WIS save or "
                                "you're invisible to it until the start of your next turn (or until you attack "
                                "or cast a spell)"},
        "Fire Strike": {"say": "add 1d10 fire damage to the hit"},
        "Frost Strike": {"say": "add 1d6 cold damage to the hit; the target makes a DC {GIANT_DC} CON save or its "
                                "speed is 0 until the start of your next turn"},
        "Hill Strike": {"say": "add 1d6 to the damage; the target makes a DC {GIANT_DC} STR save or is knocked "
                               "prone"},
        "Stone Strike": {"say": "add 1d6 force damage to the hit; the target makes a DC {GIANT_DC} STR save or is "
                                "pushed 10 ft away"},
        "Storm Strike": {"say": "add 1d6 lightning damage to the hit; the target makes a DC {GIANT_DC} CON save "
                                "or has disadvantage on attack rolls until the start of your next turn"},
    }
    later = {"Guile of the Cloud Giant": "Cloud Strike", "Ember of the Fire Giant": "Fire Strike",
             "Fury of the Frost Giant": "Frost Strike", "Vigor of the Hill Giant": "Hill Strike",
             "Keenness of the Stone Giant": "Stone Strike", "Soul of the Storm Giant": "Storm Strike"}
    known = [v for k, v in later.items() if k in (char.get("feats") or [])]
    picked = [p.split(" –")[0].strip() for p in ((char.get("_choices") or {}).get("feat_strike_of_the_giants") or [])]
    known = known or [p for p in picked if p in strikes]
    dc = str(8 + _pb(char) + max(_mods(char)["STR"], _mods(char)["CON"]))
    return [{"label": n, "say": strikes[n]["say"].replace("{GIANT_DC}", dc)}
            for n in (known or list(strikes))]


R("Giant Strike", share="Strike of the Giants", uses="PB/LR", once=True, slot=False, choose=_giant_strikes,
  ask="Which strike?")
R("Searing Ignition", uses="PB/LR")
R("Frigid Retaliation", uses="PB/LR")
R("Cloudy Escape", uses="PB/LR", say="resistance to that attack's damage; now teleport up to 30 ft to a space you "
  "can see")
R("Stone Throw", uses="PB/LR")
R("Hill Giant Bulwark", say="you aren't moved and aren't knocked prone")
R("Precise Strike", once=True, slot=False, needs="precise", fx="Precise Strike")
R("Commanding Rally", uses="PB/LR", say="an ally within 30 ft makes one weapon attack with its reaction; on a hit "
  "it adds 1d8 to the damage")
R("Bolstering Rally", uses="PB/LR", choose=lambda c: [
    {"label": "Yourself", "temp": f"1d8+{_pb(c) + max(_mods(c)[a] for a in ('STR', 'CON', 'CHA'))}"},
    {"label": "Someone else", "roll": f"1d8+{_pb(c) + max(_mods(c)[a] for a in ('STR', 'CON', 'CHA'))}",
     "say": "the creature gains {roll} temporary hit points"}], ask="Bolstering Rally: for whom?")
R("Demoralizing Strike", uses="PB/LR", once=True, slot=False, choose=lambda c: [
    {"label": "go", "say": f"the target makes a DC {8 + _pb(c) + max(_mods(c)[a] for a in ('STR', 'DEX', 'CON'))} "
                           f"WIS save or is frightened of you until the end of your next turn (on a success it "
                           f"has disadvantage on its next attack roll)"}])
R("Protective Wings", uses="PB/LR", say="+{PB} AC against that attack")
R("Reactive Resistance", uses="PB/LR", say="resistance to that acid, cold, fire, lightning or poison damage")
R("Stasis Strike", uses="PB/LR", once=True, slot=False, say="add 1d8 force damage to the hit; the target makes a "
  "WIS save or is restrained until the start of your next turn")
R("Grasp of Avarice", uses="PB/LR", once=True, slot=False, say="add 1d6+{PB} necrotic damage to the hit, and you "
  "regain hit points equal to that necrotic damage")
R("Soothe Pain", uses="PB/LR", roll="1d10+PB", damage=True, say="roll {roll} and take that much off the damage")
R("Portal Sense", uses="1/LR", say="you sense any portals within 30 ft that aren't behind total cover")
R("Protective Ward", cost=("slot", 1), say="roll a d6 per level of the slot, add your spellcasting modifier, and "
  "take that much off the damage")
R("Hidden Ace", uses="1/LR", spell=True, say="you flourish the card and cast its spell")
R("Flash Recall", uses="1/SR", say="prepare the spell in place of one of equal or higher level")
R("Spare the Dying (Field Medic)", exact=True, spell=True, say="cast Spare the Dying")
R("Empower Flames", uses="1/SR", say="the next time you deal fire damage before the end of your next turn, one of "
  "the creatures takes 2d10 more fire damage")
R("Metamagic Adept", share="Sorcery Points (Metamagic Adept)", uses="2/LR", slot=False,
  say="1 sorcery point on Metamagic (an option that costs more: Use again)")
R("Cruel", share="Cruelty Dice (d6)", uses="PB/LR", once=True, slot=False, ask="Cruel:", choose=[
    {"label": "Extra damage", "roll": "1d6", "damage": True, "say": "add {roll} to the damage"},
    {"label": "Hit points on a critical hit", "heal": "1d6", "say": ""},
    {"label": "An Intimidation check", "roll": "1d6", "say": "add {roll} to the Intimidation check"}])
R("Orcish Fury: Attack", exact=True, say="one weapon attack, right after Relentless Endurance")
R("Lucky Break", share="Bandit Cunning (Lucky Break)", uses="1/LR", say="add {INT} to the saving throw")
R("Plant Vision", uses="1/LR", say="visions of what happened around the plant in the last 24 hours, and its "
  "health")
R("Mascot Swap", uses="1/LR", alt=("slot", 2), say="you and your mascot familiar swap places")
# Fighting styles with a reaction (Fighter, Paladin, Ranger, Fighting Initiate)
R("Interception", roll="1d10+PB", damage=True, say="roll {roll} and take that much off the damage the creature "
  "takes (to a minimum of 0)")
R("Protection", needs="shield", say="the attack roll against the creature next to you has disadvantage")
R("Thousand Forms", spell=True, say="cast Alter Self at will, without a spell slot")
R("Arcane Deflection", say="+2 AC against the attack or +4 to the save; only cantrips on your next turn")
R("Song of Defense", cost=("slot", 1), needs="bladesong", say="reduce the damage by 5 per slot level")


# ── Checked against the rules books (docs/reference) ──────────────────────
# Later entries replace earlier ones of the same name.
from dnd_app.data.classes import WILD_MAGIC_BARBARIAN_TABLE, WILD_MAGIC_SURGE_TABLE


def _by_level(lvl, steps):
    """steps [(level, value)] ascending -> the value for this level."""
    out = steps[0][1]
    for at, v in steps:
        if lvl >= at:
            out = v
    return out


def _sub(char, cls):
    from dnd_app.core.character import subclasses
    return (subclasses(char).get(cls, "") or "").lower()


def _one(say, **kw):
    """A rule whose words depend on the character: one option, worked out."""
    return lambda char: [dict(label="go", say=say(char), **kw)]


# Race traits (actions.py _race_cards)
R("Starlight Step", uses="PB/LR", say="teleport up to 30 ft to an unoccupied space you can see")
R("Built for Success", uses="PB/LR", slot=False, roll="1d4", say="add {roll} to the attack roll, check or save")
R("Chromatic Warding", uses="1/LR", fx="Chromatic Warding")
R("Metallic Breath Weapon", uses="1/LR", ask="Metallic Breath Weapon:", choose=[
    {"label": "Enervating Breath", "say": "each creature in the 15-ft cone makes a DC {BWDC} CON save or is "
                                          "incapacitated until the start of your next turn"},
    {"label": "Repulsion Breath", "say": "each creature in the 15-ft cone makes a DC {BWDC} STR save or is "
                                         "pushed 20 ft away from you and knocked prone"}])
R("Forceful Presence", uses="1/SR", slot=False, say="make the Intimidation or Persuasion check with advantage")
R("Vengeful Assault", uses="1/SR", say="one attack with your weapon against the creature that damaged you")
R("Blessing of the Raven Queen", uses="1/LR", choose=_one(
    lambda c: "teleport up to 30 ft to an unoccupied space you can see"
              + ("; resistance to all damage until the start of your next turn" if _level(c) >= 3 else "")))
R("Merge with Stone", uses="PB/LR", spell=True, say="cast Blade Ward as a bonus action")
R("Dexterous Feet", say="use your feet to manipulate an object, open or close a door or container, or pick up or "
  "set down a Tiny object")
R("Glide", say="glide up to your walking speed horizontally, taking no damage from the fall")
R("Hadozee Dodge", uses="PB/LR", roll="1d6+PB", damage=True, say="roll {roll} and take that much off the damage")
R("Relentless Endurance", uses="1/LR", slot=False, needs="down", hp1=True, say="you drop to 1 hit point instead")
R("Lucky Footwork", roll="1d4", say="add {roll} to the failed DEX save")
R("Emboldening Bond", uses="PB/LR", fx="Emboldening Bond", say="for 10 minutes the bonded creatures (you can be "
  "one) can each add a d4 to an attack roll, check or save once a turn, while within 30 ft of another")
R("Kenku Recall", uses="PB/LR", slot=False, say="advantage on the check (a skill you're proficient in), taken "
  "before you roll")
R("Eerie Token", uses="1/LR", say="your token is imbued until your next long rest: within 10 miles of it, your "
  "action can send a 25-word telepathic message to whoever holds it, or let you see and hear through it for up "
  "to 1 minute (then it's destroyed)")
R("Saving Face", uses="1/SR", slot=False, say="+1 to the roll for each ally you can see within 30 ft (up to +5)")
R("Fey Gift", uses="PB/LR", choose=lambda c: [{"label": "Help", "say": "take the Help action"}] if _level(c) < 3 else [
    {"label": "Hospitality", "temp": "1d6+PB", "say": "take the Help action; the creature you help also gains "
                                                    "1d6 + {PB} temporary hit points"},
    {"label": "Passage", "say": "take the Help action; you and the creature you help each get +10 ft walking "
                                "speed until the start of your next turn"},
    {"label": "Spite", "say": "take the Help action; until the start of your next turn, the first target the "
                              "creature you help hits has disadvantage on its next attack roll within a minute"}],
  ask="Fey Gift:")
R("Fortune from the Many", uses="PB/LR", slot=False, say="+1 to the roll for each ally you can see within 30 ft "
  "(up to +3)")
R("Vigilant Guardian", uses="1/LR", say="swap places with the creature that was hit; the attack hits you instead")
R("Taunt", uses="PB/LR", choose=_one(
    lambda c: f"the creature makes a DC {8 + _pb(c) + max(_mods(c)[a] for a in ('INT', 'WIS', 'CHA'))} WIS save or "
              f"has disadvantage on attacks against anyone but you until the start of your next turn"))
R("Fearless", uses="1/LR", slot=False, say="the failed save against being frightened succeeds instead")
R("Draconic Cry", uses="PB/LR", say="until the start of your next turn, you and your allies have advantage on attack "
  "rolls against the enemies within 10 ft that heard you")
R("Aggressive", say="move up to your speed toward a hostile creature you can see or hear, ending closer to it")
R("Shape Self", say="reshape your body: a head, one or two arms and legs, and makeshift hands and feet, or back to "
  "a limbless blob")
R("Knowledge from a Past Life", uses="PB/LR", slot=False, roll="1d6", say="add {roll} to the skill check")
R("Swiftstride Step", needs="shifting", say="move up to 10 ft without provoking opportunity attacks")
R("Feline Agility", slot=False, say="double your speed until the end of the turn; it comes back once you spend a "
  "turn without moving")
R("Shell Defense", fx="Shell Defense")
R("Leave Your Shell", end_fx="Shell Defense", say="you come out of your shell")

# Barbarian
R("Bolstering Magic", uses="PB/LR", choose=[
    {"label": "A d3 on attack rolls and checks",
     "say": "for 10 minutes the creature you touch adds a d3 to its attack rolls and ability checks"},
    {"label": "Regain a spell slot", "roll": "1d3",
     "say": "rolled {roll}: the creature you touch regains one expended spell slot of that level or lower "
            "(each creature once per long rest)"}])
R("Call the Hunt", uses="PB/LR", needs="rage", ask="Call the Hunt: how many creatures accept?",
  choose=lambda char: [{"label": f"{n} creature{'s' if n > 1 else ''}", "temp": str(5 * n),
                        "say": "until your rage ends, each of them can add 1d6 to the damage of one hit on each "
                               "of its turns"} for n in range(1, max(1, _mods(char)["CON"]) + 1)])
R("Intimidating Presence", say="a creature within 30 ft that can see or hear you makes a DC {DC_CHA} WIS save "
  "or is frightened of you until the end of your next turn (use your action each turn to extend it; "
  "if it succeeds, not again on it for 24 hours)")
R("Mighty Impel", needs="rage", say="move a Medium or smaller creature within your reach to a space within "
  "30 ft; an unwilling one makes a DC {DC_STR} STR save to resist")


def _storm_options(char, which):
    from dnd_app.core.character import class_levels
    bb = class_levels(char).get("Barbarian", 0)
    env = " ".join((char.get("_choices", {}) or {}).get("storm_aura_3", []) or []).lower()
    n = _by_level(bb, [(0, 2), (5, 3), (10, 4), (15, 5), (20, 6)])
    sea = _by_level(bb, [(0, "1d6"), (10, "2d6"), (15, "3d6"), (20, "4d6")])
    if which == "aura":
        opts = [{"label": "Desert", "say": f"each other creature in your 10-ft aura takes {n} fire damage"},
                {"label": "Sea", "roll": sea, "damage": True,
                 "say": "one creature in your aura makes a DC {DC_CON} DEX save: {roll} lightning damage, "
                        "half on a success"},
                {"label": "Tundra", "say": f"each creature of your choice in your aura gains {n} temporary "
                                           f"hit points"}]
    else:
        opts = [{"label": "Desert", "say": f"after a creature in your aura hits you: it makes a DC {{DC_CON}} "
                                           f"DEX save or takes {bb // 2} fire damage"},
                {"label": "Sea", "say": "when you hit a creature in your aura: it makes a DC {DC_CON} STR save "
                                        "or is knocked prone"},
                {"label": "Tundra", "say": "when your Storm Aura activates: one creature in it makes a DC "
                                           "{DC_CON} STR save or its speed is 0 until the start of your next "
                                           "turn"}]
    mine = [o for o in opts if o["label"].lower() in env]
    return mine or opts


R("Storm Aura", needs="rage", ask="Storm Aura: which environment?", choose=lambda c: _storm_options(c, "aura"))
R("Raging Storm", needs="rage", ask="Raging Storm: which environment?", choose=lambda c: _storm_options(c, "raging"))
R("Unstable Backlash", needs="rage", table=("1d8", WILD_MAGIC_BARBARIAN_TABLE), say="")
R("Magic Awareness", uses="PB/LR", say="until the end of your next turn, you know where every spell and magic "
  "item within 60 ft is (not behind total cover), and the school of any spell")
R("Spirit Shield", needs="rage", choose=_one(
    lambda c: "roll {roll} and take that much off the damage"
              + ("; the attacker takes that much force damage (Vengeful Ancestors)" if _lvl(c, "barbarian") >= 14 else ""),
    roll="NAMEDICE", damage=True))
R("Infectious Fury", uses="PB/LR", needs="rage", slot=False, choose=[
    {"label": "2d12 psychic damage", "roll": "2d12", "damage": True,
     "say": "the target makes a DC {DC_CON} WIS save or takes {roll} psychic damage"},
    {"label": "It attacks another creature",
     "say": "the target makes a DC {DC_CON} WIS save or uses its reaction to make a melee attack against "
            "another creature of your choice"}])
R("Consult the Spirits", uses="1/SR", spell=True, say="cast Augury or Clairvoyance without a spell slot or "
  "material components")
R("Eagle Spirit: Dash", exact=True, needs="rage", say="Dash as a bonus action")
R("Elk Attunement: Trample", exact=True, needs="rage", roll="1d12+STR", damage=True,
  say="the creature makes a DC {DC_STR} STR save or is knocked prone and takes {roll} bludgeoning damage")
R("Tiger Attunement: Pounce", exact=True, needs="rage", say="one more melee weapon attack against the target")
R("Wolf Attunement: Knock Prone", exact=True, needs="rage", say="the Large or smaller creature you hit is "
  "knocked prone")
R("Tail Swipe", roll="1d8", say="add {roll} to your AC against that attack")
# Bard
SPIRIT_TALES = [
    (1, "Tale of the Clever Animal: for 10 minutes, the target adds a roll of your Bardic Inspiration die to "
        "its INT, WIS and CHA checks"),
    (2, "Tale of the Renowned Duelist: make a melee spell attack against the target; on a hit it takes two "
        "rolls of your Bardic Inspiration die + {CHA} force damage"),
    (3, "Tale of the Beloved Friends: the target and another creature within 5 ft of it gain a roll of your "
        "Bardic Inspiration die + {CHA} temporary hit points"),
    (4, "Tale of the Runaway: the target can use its reaction to teleport up to 30 ft, and up to {CHA} "
        "creatures within 30 ft of it can do the same"),
    (5, "Tale of the Avenger: for 1 minute, a creature that hits the target with a melee attack takes a roll "
        "of your Bardic Inspiration die in force damage"),
    (6, "Tale of the Traveler: the target gains a roll of your Bardic Inspiration die + {LVL:Bard} temporary "
        "hit points, and while it has them, +10 ft speed and +1 AC"),
    (7, "Tale of the Beguiler: the target makes a WIS save or takes two rolls of your Bardic Inspiration die "
        "in psychic damage and is incapacitated until the end of its next turn"),
    (8, "Tale of the Phantom: the target is invisible until the end of its next turn or until it hits with an "
        "attack; the creature it hits takes a roll of your die in necrotic damage and is frightened"),
    (9, "Tale of the Brute: each creature of the target's choice within 30 ft makes a STR save: three rolls of "
        "your Bardic Inspiration die in thunder damage and knocked prone, or half and not prone on a success"),
    (10, "Tale of the Dragon: the target breathes a 30-ft cone of fire: DEX save, four rolls of your Bardic "
         "Inspiration die in fire damage, half on a success"),
    (11, "Tale of the Angel: the target regains two rolls of your Bardic Inspiration die + {CHA} hit points, "
         "and you end one of: blinded, deafened, paralyzed, petrified or poisoned on it"),
    (12, "Tale of the Mind-Bender: the target makes an INT save or takes three rolls of your Bardic Inspiration "
         "die in psychic damage and is stunned until the end of its next turn"),
]
R("Tales from Beyond", cost=("bi", 1), table=("BI", SPIRIT_TALES), choose=_one(
    lambda c: "bestow it with an action on a creature within 30 ft (you included)"
              + ("; Mystical Connection: roll again and use either tale" if _lvl(c, "bard") >= 14 else "")))
R("Mantle of Inspiration", cost=("bi", 1), choose=_one(
    lambda c: f"up to {{CHA}} creatures within 60 ft gain "
              f"{_by_level(_lvl(c, 'bard'), [(0, 5), (5, 8), (10, 11), (15, 14)])} temporary hit points, and each "
              f"can use its reaction to move up to its speed without provoking opportunity attacks"))
R("Battle Magic", say="one weapon attack, after casting a bard spell with your action")
R("Mantle of Whispers", say="capture the humanoid's shadow (kept until you use it or finish a long rest); use it "
  "as an action to take on its appearance for 1 hour")
# Cleric
R("Turn Undead", cost=("cd", 1), choose=_one(
    lambda c: "each undead within 30 ft that can see or hear you makes a DC {SPELL_DC} WIS save or is turned "
              "for 1 minute"
              + (f"; undead of CR {_by_level(_lvl(c, 'cleric'), [(5, '1/2'), (8, '1'), (11, '2'), (14, '3'), (17, '4')])} "
                 f"or lower are destroyed instead" if _lvl(c, "cleric") >= 5 else "")))
R("Arcane Abjuration", cost=("cd", 1), choose=_one(
    lambda c: "one celestial, elemental, fey or fiend within 30 ft makes a DC {SPELL_DC} WIS save or is turned "
              "for 1 minute"
              + (f"; if its CR is {_by_level(_lvl(c, 'cleric'), [(5, '1/2'), (8, '1'), (11, '2'), (14, '3'), (17, '4')])} "
                 f"or lower it's banished for 1 minute instead" if _lvl(c, "cleric") >= 5 else "")))
R("Harness Divine Power", cost=("cd", 1), uses="HDP/LR", ask="Regain which spell slot?",
  choose=lambda c: [{"label": f"A {_ordinal(n)}-level slot", "regain_slot": n}
                    for n in range(1, -(-_pb(c) // 2) + 1)
                    if c.get("spell_slots_used", [0] * 9)[n - 1] > 0])
R("Blessing of the Forge", uses="1/LR", say="the nonmagical weapon or armor you touch becomes a +1 weapon or +1 "
  "armor until the end of your next long rest")
R("Guided Strike", cost=("cd", 1), slot=False, say="+10 to the attack roll")
R("Destructive Wrath", cost=("cd", 1), slot=False, say="deal the maximum lightning or thunder damage instead of "
  "rolling")
R("Consuming Fervor", cost=("cd", 1), slot=False, say="deal the maximum fire or thunder damage instead of rolling")
R("Feat of Strength", cost=("cd", 1), slot=False, say="+10 to that Strength roll")
R("Divine Intervention", uses="1/LR")
R("Cloak of Shadows (Channel Divinity)", exact=True, cost=("cd", 1),
  say="you become invisible until the end of your next turn, or until you attack or cast a spell")
# Druid
R("Wild Companion", cost=("ws", 1), spell=True, say="cast Find Familiar without material components; it's a fey "
  "and lasts {HALF:Druid} hours")
R("Spirit Totem", uses="1/SR", fx="Spirit Totem", remember=True, ask="Spirit Totem: which spirit?", choose=lambda c: [
    {"label": "Bear", "say": f"each creature of your choice in the 30-ft aura gains {5 + _lvl(c, 'druid')} temporary "
                             f"hit points, and advantage on STR checks and saves while in it"},
    {"label": "Hawk", "say": "your reaction can give advantage on an attack roll against a target in the aura; "
                             "creatures in it have advantage on Perception checks"},
    {"label": "Unicorn", "say": f"advantage on checks to detect creatures in the aura; when you cast a healing "
                                f"spell with a slot, each creature of your choice in it regains {_lvl(c, 'druid')} HP"}])
def _starry_forms(c):
    """Starry Form's constellations, each with what it gives at this level
    (Twinkling Constellations at 10th, Full of Stars at 14th)."""
    die = _by_level(_lvl(c, 'druid'), [(0, '1d8'), (10, '2d8')])
    full = "; resistance to bludgeoning, piercing and slashing damage" if _lvl(c, "druid") >= 14 else ""
    return [
        {"label": "Archer", "say": f"bright light 10 ft; when you take the form and with your bonus action on later "
                                   f"turns, a ranged spell attack within 60 ft: {die} + {{WIS}} radiant damage on a "
                                   f"hit (Luminous Arrow on the Combat page){full}"},
        {"label": "Chalice", "say": f"bright light 10 ft; when you cast a healing spell with a slot, you or a creature "
                                    f"within 30 ft regains {die} + {{WIS}} hit points{full}"},
        {"label": "Dragon", "say": "bright light 10 ft; INT and WIS checks and CON saves to concentrate: a roll of 9 "
                                   "or lower counts as 10" + ("; a 20-ft flying speed (you can hover)"
                                                              if _lvl(c, "druid") >= 10 else "") + full}]


R("Starry Form", cost=("ws", 1), fx="Starry Form", remember=True, ask="Starry Form: which constellation?",
  choose=_starry_forms)
R("Natural Recovery", uses="1/LR", slot=False, say="during a short rest, recover spell slots with a combined level "
  "up to half your druid level (rounded up), none of 6th level or higher")
# Fighter
R("Action Surge", uses="1/SR", surge=True, slot=False, choose=_one(
    lambda c: "take one more action this turn"
              + ("; Inspiring Surge: {N} creature{S} within 60 ft can use its reaction to make one weapon attack"
                 .replace("{N}", "two" if _lvl(c, "fighter") >= 18 else "one").replace("{S}", "s" if _lvl(c, "fighter") >= 18 else "")
                 if _lvl(c, "fighter") >= 10 and ("banneret" in _sub(c, "Fighter") or "purple dragon" in _sub(c, "Fighter")) else "")
              + ("; Arcane Charge: teleport up to 30 ft before or after the action"
                 if _lvl(c, "fighter") >= 15 and "eldritch knight" in _sub(c, "Fighter") else "")))
R("Unwavering Mark", uses="STR/LR", say="a special melee weapon attack against the marked creature, with advantage "
  "and +{HALF:Fighter} damage on a hit")
R("Unleash Incarnation", uses="CON/LR", slot=False, say="one more melee attack, from your echo's position")
R("Reclaim Potential", uses="CON/LR", slot=False, temp="2d6+CON")
R("Echo Avatar", say="see and hear through your echo for up to 10 minutes (deafened and blinded yourself); it can "
  "be up to 1,000 ft away")
R("Weapon Bond", say="summon a bonded weapon to your hand, if it's on the same plane")
R("Protective Field", cost=("psi", 1), roll="PSI+INT", damage=True, say="roll {roll} and take that much off the damage")
R("Telekinetic Movement", cost=("psi", 1), say="move a Large or smaller loose object or a willing creature within "
  "30 ft up to 30 ft")
R("Psionic Power: Recover", exact=True, uses="1/SR", regain_pool=("psi", 1))
R("Cloud Rune", uses="RUNE/SR", say="the attack hits a different creature of your choice within 30 ft of you "
  "instead, with the same roll")
R("Stone Rune", uses="RUNE/SR", say="the creature makes a DC {DC_CON} WIS save or is charmed for 1 minute: speed 0 "
  "and incapacitated (it saves again at the end of each of its turns)")
R("Frost Rune", uses="RUNE/SR", fx="Frost Rune", say="+2 to STR and CON checks and saves for 10 minutes")
R("Hill Rune", uses="RUNE/SR", say="resistance to bludgeoning, piercing and slashing damage for 1 minute")
R("Storm Rune", uses="RUNE/SR", say="for 1 minute, your reaction can give advantage or disadvantage to a roll "
  "within 60 ft")
R("Fire Rune", uses="RUNE/SR", slot=False,
  say="add 2d6 fire damage to the hit; the target makes a DC {DC_CON} STR save or is restrained for 1 minute, "
      "taking 2d6 fire at the start of each of its turns (it saves again at the end of each)")
# Arcane Shot: which of your shots (Arcane Archer)
_SHOTS = {
    "Banishing Arrow": ("", "the target makes a DC {DC_INT} CHA save or is banished until the end of its next turn"
                        " (speed 0, incapacitated){X}"),
    "Beguiling Arrow": ("2d6", "+{roll} psychic; the target makes a DC {DC_INT} WIS save or is charmed by an ally "
                        "of your choice within 30 ft until the start of your next turn"),
    "Bursting Arrow": ("2d6", "the target and each creature within 10 ft of it take {roll} force damage"),
    "Enfeebling Arrow": ("2d6", "+{roll} necrotic; the target makes a DC {DC_INT} CON save or its weapon damage is "
                         "halved until the start of your next turn"),
    "Grasping Arrow": ("2d6", "+{roll} poison; for 1 minute its speed drops by 10 ft and it takes {roll} slashing "
                       "the first time each turn it moves (a STR (Athletics) check against DC {DC_INT} frees it)"),
    "Piercing Arrow": ("1d6", "no attack roll: each creature in a 30-ft line makes a DC {DC_INT} DEX save: the "
                       "arrow's damage + {roll} piercing, half on a success"),
    "Seeking Arrow": ("1d6", "no attack roll at a creature you've seen in the last minute: it makes a DC {DC_INT} "
                      "DEX save: the arrow's damage + {roll} force, half on a success, and you learn where it is"),
    "Shadow Arrow": ("2d6", "+{roll} psychic; the target makes a DC {DC_INT} WIS save or can't see farther than "
                     "5 ft until the start of your next turn"),
}


def _shot_options(char):
    high = _lvl(char, "fighter") >= 18
    out = []
    for raw in (char.get("_choices", {}) or {}).get("arcane_shot_options", []) or []:
        shot = raw.split(" –")[0].split(" (")[0].strip()
        if shot not in _SHOTS:
            continue
        dice, say = _SHOTS[shot]
        if dice and high:
            dice = f"{2 * int(dice[0])}d6"
        say = say.replace("{X}", "; it also takes 2d6 force damage" if high else "")
        out.append({"label": shot, "say": say, **({"roll": dice, "damage": True} if dice else {})})
    return out


R("Arcane Shot", uses="2/SR", once=True, slot=False, ask="Arcane Shot: which shot?", choose=_shot_options)
# Battle Master maneuvers: a superiority die each, with the save DC
_MANEUVERS = {
    "Commander's Strike": ("forgo one of your attacks: a companion uses its reaction to make one weapon attack, "
                           "adding {roll} to its damage", True),
    "Disarming Attack": ("add {roll} to the damage; the target makes a DC {DC_MAN} STR save or drops one item you "
                         "choose", True),
    "Distracting Strike": ("add {roll} to the damage; the next attack roll against the target by someone else "
                           "before your next turn has advantage", True),
    "Evasive Footwork": ("add {roll} to your AC until you stop moving", True),
    "Feinting Attack": ("advantage on your next attack against a creature within 5 ft this turn; add {roll} to "
                        "its damage if it hits", True),
    "Goading Attack": ("add {roll} to the damage; the target makes a DC {DC_MAN} WIS save or has disadvantage on "
                       "attacks against anyone but you until the end of your next turn", True),
    "Lunging Attack": ("+5 ft reach for this attack; add {roll} to the damage if it hits", True),
    "Maneuvering Attack": ("add {roll} to the damage; an ally can use its reaction to move up to half its speed "
                           "without provoking opportunity attacks from the target", True),
    "Menacing Attack": ("add {roll} to the damage; the target makes a DC {DC_MAN} WIS save or is frightened of you "
                        "until the end of your next turn", True),
    "Parry": ("roll {roll} + {DEX} and take that much off the damage", True),
    "Precision Attack": ("add {roll} to the attack roll", True),
    "Pushing Attack": ("add {roll} to the damage; a Large or smaller target makes a DC {DC_MAN} STR save or is "
                       "pushed up to 15 ft away", True),
    "Rally": ("a friendly creature that can see or hear you gains {roll} + {CHA} temporary hit points", True),
    "Riposte": ("make a melee weapon attack against the creature that missed you; add {roll} to the damage if it "
                "hits", True),
    "Sweeping Attack": ("another creature within 5 ft of the target, in your reach, takes {roll} damage of the "
                        "attack's type if your attack roll would hit it", True),
    "Trip Attack": ("add {roll} to the damage; a Large or smaller target makes a DC {DC_MAN} STR save or is "
                    "knocked prone", True),
    "Ambush": ("add {roll} to the Stealth check or initiative roll", True),
    "Bait and Switch": ("swap places with an ally within 5 ft (5 ft of movement); you or the ally gets +{roll} AC "
                        "until the start of your next turn", True),
    "Brace": ("when a creature moves into your reach: one weapon attack against it, adding {roll} to the damage", True),
    "Commanding Presence": ("add {roll} to the Intimidation, Performance or Persuasion check", True),
    "Grappling Strike": ("after a melee hit: try to grapple the target, adding {roll} to the Athletics check", True),
    "Quick Toss": ("a ranged attack with a thrown weapon (drawn as part of it); add {roll} to the damage if it "
                   "hits", True),
    "Tactical Assessment": ("add {roll} to the Investigation, History or Insight check", True),
}
for _m, (_say, _dmg) in _MANEUVERS.items():
    R(_m, cost=("sd", 1), roll="SD", damage=_dmg, say=_say, maneuver=True)
# Monk
R("Hour of Reaping", say="each creature within 30 ft that can see you makes a DC {DC_WIS} WIS save or is "
  "frightened of you until the end of your next turn")
R("Breath of the Dragon", uses="PB/LR", alt=("ki", 2), roll="BREATHMONK", damage=True,
  say="in place of one attack: each creature in a 20-ft cone or 30-ft line makes a DC {DC_WIS} DEX save: {roll} "
      "acid, cold, fire, lightning or poison damage (your pick), half on a success")
R("Arms of the Astral Self", cost=("ki", 1), fx="Arms of the Astral Self", roll="2*MA", damage=True,
  say="each creature of your choice within 10 ft makes a DC {DC_WIS} DEX save or takes {roll} force damage; for "
      "10 minutes your arms attack with WIS and deal force damage, with 5 ft more reach")
R("Awakened Astral Self", cost=("ki", 5), fx="Awakened Astral Self",
  say="for 10 minutes: +2 AC, and the Attack action makes three attacks with your astral arms")
R("Stunning Strike", cost=("ki", 1), slot=False,
  say="the target makes a DC {DC_WIS} CON save or is stunned until the end of your next turn")
R("Stillness of Mind", end_condition=("Charmed", "Frightened"),
  say="end one effect on yourself that's charming or frightening you")
R("Diamond Soul", cost=("ki", 1), slot=False, say="reroll the failed saving throw and take the second result")
R("Empty Body", ask="Empty Body: which?", choose=[
    {"label": "Invisible (4 ki)", "cost": ("ki", 4), "fx": "Empty Body",
     "say": "invisible for 1 minute, with resistance to all damage but force"},
    {"label": "Astral Projection (8 ki)", "cost": ("ki", 8), "spell": True,
     "say": "cast Astral Projection without material components, taking no one with you"}])
R("Draconic Disciple: Reroll", exact=True, uses="1/LR", slot="Reaction",
  say="reroll the failed CHA check (the use is spent only if it succeeds)")
R("Quickened Healing", cost=("ki", 2), heal="MA+PB")
R("Focused Aim", cost=("ki", (1, 3)), slot=False, say="+{KI2} to the attack roll")
R("Ki-Fueled Attack", say="one attack with an unarmed strike or a monk weapon")
R("Quivering Palm", ask="Quivering Palm:", choose=[
    {"label": "Start the vibrations (3 ki)", "cost": ("ki", 3), "slot": False,
     "say": "after your unarmed strike hits: the vibrations last {LVL:Monk} days"},
    {"label": "End them (your action)", "slot": "Action", "roll": "10d10", "damage": True,
     "say": "the creature makes a DC {DC_WIS} CON save: on a fail it drops to 0 hit points, on a success it takes "
            "{roll} necrotic damage"}])
R("Cloak of Shadows", say="in dim light or darkness, you become invisible until you attack, cast a spell, or are "
  "in bright light")
R("Shadow Arts", cost=("ki", 2), spell=True, say="cast Darkness, Darkvision, Pass without Trace or Silence, without "
  "material components")
# Paladin
R("Vow of Enmity", cost=("cd", 1), fx="Vow of Enmity", say="advantage on attack rolls against one creature within "
  "10 ft for 1 minute")
R("Control Undead", cost=("cd", 1), say="one undead within 30 ft (CR lower than {LVL:Paladin}) makes a DC {SPELL_DC} "
  "WIS save or obeys your commands for 24 hours")
R("Champion Challenge", cost=("cd", 1), say="each creature of your choice within 30 ft makes a DC {SPELL_DC} WIS "
  "save or can't willingly move more than 30 ft away from you")
# Ranger
R("Tireless", uses="PB/LR", temp="1d8+WIS")
R("Nature's Veil", uses="PB/LR", say="you're invisible until the start of your next turn")
R("Giant Killer", say="attack the Large or larger creature")
R("Stand Against the Tide", say="the attacker repeats the attack against another creature of your choice")
R("Ranger's Companion", say="command your companion to take the Attack, Dash, Disengage, Dodge or Help action")
# Rogue
R("Wails from the Grave", uses="PB/LR", slot=False, roll="WAILS", damage=True,
  say="a second creature within 30 ft of the first takes {roll} necrotic damage")
R("Steady Aim", fx="Steady Aim", say="advantage on your next attack roll this turn; your speed is 0 until the end "
  "of the turn")
R("Soul Blades", ask="Soul Blades:", choose=[
    {"label": "Homing Strikes (a missed blade attack)", "cost": ("psi", 1), "slot": False, "roll": "PSI",
     "say": "add {roll} to the missed attack roll (the die is spent only if it then hits)"},
    {"label": "Psychic Teleportation", "slot": "Bonus Action", "cost": ("psi", 1), "roll": "PSI",
     "say": "rolled {roll}: throw a blade and teleport up to ten times that many feet"}])
R("Psi-Bolstered Knack", cost=("psi", 1), slot=False, roll="PSI",
  say="add {roll} to the check (the die is spent only if the check then succeeds)")
R("Psychic Whispers", cost=("psi", 1), roll="PSI", say="telepathy with up to {PB} creatures for {roll} hours")
R("Rend Mind", uses="1/LR", alt=("psi", 3), slot=False,
  say="the target makes a DC {DC_DEX} WIS save or is stunned for 1 minute (it saves again at the end of each of "
      "its turns)")
R("Death Strike", slot=False, say="the surprised target makes a DC {DC_DEX} CON save or the attack's damage is "
  "doubled")
R("Unerring Eye", uses="WIS/LR", say="for 1 minute, you sense illusions, shapechangers and other magical "
  "deception within 30 ft")
# Sorcerer
R("Favored by the Gods", uses="1/SR", slot=False, roll="2d4", say="add {roll} to the failed save or missed attack")
R("Umbral Form", cost=("sp", 6), fx="Umbral Form", say="for 1 minute: resistance to all damage except force and "
  "radiant, and you can move through creatures and objects as difficult terrain")
R("Lunar Phenomenon", ask="Lunar Phenomenon: which phase?", each=("Full Moon", "New Moon", "Crescent Moon"),
  uses="1/LR", alt=("sp", 5), choose=[
    {"label": "Full Moon", "share": "Lunar Phenomenon (Full Moon)",
     "say": "each creature of your choice within 30 ft makes a DC {SPELL_DC} CON save or is blinded until the end "
            "of its next turn; one creature of your choice there regains 3d8 hit points"},
    {"label": "New Moon", "share": "Lunar Phenomenon (New Moon)",
     "say": "each creature of your choice within 30 ft makes a DC {SPELL_DC} DEX save or takes 3d10 necrotic "
            "damage and its speed is 0 until the end of its next turn; you're invisible until the end of your next "
            "turn or until you attack or cast"},
    {"label": "Crescent Moon", "share": "Lunar Phenomenon (Crescent Moon)",
     "say": "teleport up to 60 ft, with a willing creature within 5 ft; you both have resistance to all damage "
            "until the start of your next turn"}])
R("Pyromancer's Fury", say="{LVL:Sorcerer} fire damage to the attacker, ignoring resistance to fire")
R("Telepathic Speech", say="a telepathic link with a creature you can see within 30 ft, for {LVL:Sorcerer} minutes")
R("Trance of Order", uses="1/LR", alt=("sp", 5), fx="Trance of Order",
  say="for 1 minute: attack rolls against you can't have advantage, and your attack rolls, checks and saves treat "
      "a d20 roll of 9 or lower as a 10")
R("Wild Magic Surge", slot=False, table=("1d100", WILD_MAGIC_SURGE_TABLE), say="")
# Warlock
R("Guardian Coil", roll="COIL", damage=True, say="roll {roll} and take that much off the damage")
R("Form of Dread", uses="PB/LR", fx="Form of Dread", temp="1d10+warlock",
  say="for 1 minute: immune to frightened; once per turn when you hit with an attack, the target makes a DC "
      "{SPELL_DC} WIS save or is frightened of you until the end of your next turn")
R("Indestructible Life", uses="1/SR", heal="1d8+warlock", say="and you can reattach a severed body part")
R("Searing Vengeance", uses="1/LR", heal="maxhp/2", roll="2d8+CHA", damage=True,
  say="you stand up; each creature of your choice within 30 ft takes {roll} radiant damage and is blinded until "
      "the end of the current turn")
R("Dark One's Blessing", slot=False, temp="CHA+warlock")
R("Hurl Through Hell", uses="1/LR", slot=False, roll="10d10", damage=True,
  say="the creature vanishes until the end of your next turn; when it returns, if it isn't a fiend it takes "
      "{roll} psychic damage")
R("Defy Death", uses="1/LR", slot=False, heal="1d8+CON")
R("Armor of Hexes", roll="1d6", say="rolled {roll}: on a 4 or higher the cursed creature's attack misses you")
R("Rebuke of the Talisman", say="{PB} psychic damage to the attacker, and you can push it up to 10 ft away")
R("Maddening Hex", say="{CHA} psychic damage to the cursed target and each creature of your choice within 5 ft "
  "of it")
R("Bottled Respite", uses="1/LR", say="you're inside your vessel for up to {PB}×2 hours; leave with a bonus action")
R("Tentacle of the Deeps", "Tentacle of the Deep", uses="PB/LR", fx="Tentacle of the Deeps")
for _inv, _sp in (("Ascendant Step", "Levitate"), ("Master of Myriad Forms", "Alter Self"),
                  ("Otherworldly Leap", "Jump"), ("Visions of Distant Realms", "Arcane Eye"),
                  ("Whispers of the Grave", "Speak with Dead")):
    R(_inv, spell=True, say=f"cast {_sp} at will, without a spell slot")
# Wizard
R("Deflecting Shroud", say="{HALF:Wizard} force damage to up to three creatures within 60 ft")
R("Convergent Future", exhaust=1, say="the roll becomes exactly the number it needs to succeed, or one less "
  "(your choice)")
R("Violent Attraction", uses="INT/LR", choose=[
    {"label": "A weapon attack", "roll": "1d10", "damage": True, "say": "the weapon attack deals {roll} more damage"},
    {"label": "A fall", "roll": "2d10", "damage": True, "say": "the falling creature takes {roll} more damage"}])
R("Malleable Illusions", say="change the nature of an illusion of yours that lasts 1 minute or longer")
R("One with the Word", uses="1/LR", roll="3d6",
  say="dismiss your spellbook's mind and take none of the damage; rolled {roll}: your spellbook loses spells "
      "totaling that many levels or more until you finish 1d6 long rests")
R("Overchannel", uses="1/LR", slot=False, say="the 1st-5th-level wizard spell deals maximum damage")
# Artificer
R("Soul of Artifice", hp1=True, say="end one of your artificer infusions: you drop to 1 hit point instead of 0")
R("Experimental Elixir", uses="1/LR", alt=("slot", 1), table=("1d6", [
    (1, "Healing: the drinker regains 2d4 + {INT} hit points"),
    (2, "Swiftness: the drinker's walking speed increases by 10 ft for 1 hour"),
    (3, "Resilience: the drinker gains a +1 bonus to AC for 10 minutes"),
    (4, "Boldness: for 1 minute the drinker adds a d4 to its attack rolls and saving throws"),
    (5, "Flight: the drinker gains a 10-ft flying speed for 10 minutes"),
    (6, "Transformation: the drinker's body is transformed as if by Alter Self for 10 minutes")]),
  say="the elixir lasts until drunk or your next long rest")
R("Command Eldritch Cannon", ask="Your cannon:", choose=lambda c: [
    {"label": "Flamethrower", "roll": "3d8" if _lvl(c, "artificer") >= 9 else "2d8", "damage": True,
     "say": "each creature in a 15-ft cone makes a DC {SPELL_DC} DEX save: {roll} fire damage, half on a success"},
    {"label": "Force Ballista", "roll": "3d8" if _lvl(c, "artificer") >= 9 else "2d8", "damage": True,
     "say": "a ranged spell attack ({SPELL_ATK}) at a creature within 120 ft: {roll} force damage on a hit, and "
            "it's pushed 5 ft away"},
    {"label": "Protector", "roll": "1d8+INT",
     "say": "you and each creature of your choice within 10 ft of the cannon gain {roll} temporary hit points"}])


# ── Small helpers ─────────────────────────────────────────────────────────
def _lvl(char, cls):
    from dnd_app.core.character import class_levels
    return class_levels(char).get(cls.title() if cls != "blood hunter" else "Blood Hunter", 0)


def _level(char):
    """The character's total level (race traits that grow at 3rd level)."""
    from dnd_app.core.character import total_level
    return total_level(char)


def _numeric(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# The maneuvers used on the hit itself (the attack dialog's Maneuver): a
# reaction or bonus action one (Riposte, Feinting Attack...) is its own
# card, and Precision Attack goes on the roll (core/checks.py)
_ON_HIT_MANEUVERS = ("Disarming Attack", "Distracting Strike", "Goading Attack", "Lunging Attack",
                     "Maneuvering Attack", "Menacing Attack", "Pushing Attack", "Sweeping Attack", "Trip Attack")


def on_hit_maneuvers(char) -> list:
    known = [m.split(" –")[0].split(" (")[0].strip() for m in char.get("battle_master_maneuvers", []) or []]
    return [m for m in known if m in _ON_HIT_MANEUVERS]


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
    """"WIS/LR" -> (max, reset) — reset as the resources store it. `uses`
    can also be worked out for the character (a race's two versions)."""
    if callable(uses):
        uses = uses(char)
    count, per = uses.split("/")
    reset = "LR" if per == "LR" else "SR/LR"
    if count == "PB":
        n = _pb(char)
    elif count == "RUNE":
        n = 2 if _lvl(char, "fighter") >= 15 else 1          # Master of Runes
    elif count == "HDP":
        c, p = _lvl(char, "cleric"), _lvl(char, "paladin")
        n = max(3 if c >= 18 else 2 if c >= 6 else 1 if c >= 2 else 0,
                3 if p >= 15 else 2 if p >= 7 else 1 if p >= 3 else 0)
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
        if _ftd_breath(char):
            return f"{1 + (lv >= 5) + (lv >= 11) + (lv >= 17)}d10"
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
    if tok == "SD":
        # a superiority die: d8, d10 at 10th, d12 at 18th (Battle Master);
        # a d6 from Martial Adept or Superior Technique
        from dnd_app.core.character import subclasses
        f = _lvl(char, "fighter")
        if f >= 3 and "battle master" in subclasses(char).get("Fighter", "").lower():
            return "1d12" if f >= 18 else "1d10" if f >= 10 else "1d8"
        return "1d6"
    if tok == "BREATHMONK":
        # Breath of the Dragon: two Martial Arts dice, three from 11th level
        ma = _special_die(char, "MA")
        return f"{3 if _lvl(char, 'monk') >= 11 else 2}d{ma.split('d')[1]}"
    if tok == "COIL":
        return "2d8" if _lvl(char, "warlock") >= 10 else "1d8"
    if tok == "PSI":
        # a Psionic Energy die: d6, d8 at 5th, d10 at 11th, d12 at 17th
        lv = max(_lvl(char, "fighter"), _lvl(char, "rogue"))
        return "1d12" if lv >= 17 else "1d10" if lv >= 11 else "1d8" if lv >= 5 else "1d6"
    if tok == "WAILS":
        # Wails from the Grave: half your Sneak Attack dice, rounded up
        from dnd_app.core.calculator import get_sneak_attack
        m = re.match(r"(\d+)d(\d+)", get_sneak_attack(char) or "")
        return f"{-(-int(m.group(1)) // 2)}d{m.group(2)}" if m else "1d6"
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
            if f in ("MA", "BI", "BW", "HEMODIE", "NAMEDICE", "HALO", "SD", "BREATHMONK", "COIL", "PSI", "WAILS"):
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


def _ftd_breath(char):
    """A Fizban's dragonborn (chromatic, metallic or gem): its Breath Weapon
    replaces an attack, uses a d10 and a DEX save, PB times a long rest."""
    race = (char.get("species") or char.get("race", "") or "").strip()
    sub = (char.get("subrace") or "").lower()
    return race == "Dragonborn" and any(w in sub for w in ("chromatic", "metallic", "gem"))


def _breath_tokens(char, say):
    """{ANCESTRY} {BWDC} {BWSAVE}: a dragonborn's Breath Weapon type and save."""
    if not any(t in say for t in ("{ANCESTRY}", "{BWDC}", "{BWSAVE}")):
        return say
    from dnd_app.data.races import DRACONIC_ANCESTRY
    dtype, _, save = DRACONIC_ANCESTRY.get(char.get("draconic_ancestry", ""), ("", "", ""))
    ab = next((a for a in ("STR", "DEX", "CON", "INT", "WIS", "CHA") if f"{a} save" in save), "DEX")
    if _ftd_breath(char):
        ab = "DEX"
    dc = 8 + _mods(char)["CON"] + _pb(char)
    return (say.replace("{ANCESTRY}", (dtype or "your ancestry's").lower())
               .replace("{BWDC}", str(dc)).replace("{BWSAVE}", ab))


def _cleaver_dice(char):
    return "2d6" if _lvl(char, "barbarian") >= 14 else "1d6"


def _summary(desc, limit=150):
    """The rules text, cut down for a toast: no "Uses = ..." or
    "Prerequisite: ..." sentences."""
    text = re.sub(r"\s+", " ", desc or "").strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    keep = []
    for s in sentences:
        if re.fullmatch(r"(uses?\s*=.*|\(?\d+/(lr|sr)\)?\.?|1/(short|long) rest.*|\(?prerequisites?:.*"
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
    if need == "shield" and not char.get("shield"):
        return "needs a shield"
    if need == "down" and char.get("current_hp", 0) > 0:
        return "only when you drop to 0 hit points"
    if need == "shifting" and "Shifting" not in fx:
        return "only while you're shifted"
    if need == "precise":
        res = _own_resource(char, "Precise Strike")
        if res is not None and not _unlimited(res) and res.get("current", 0) <= 0:
            return "no uses left (back on a long rest)"
    return ""


def _lower_first(text):
    """"Attacks against you..." -> "attacks against you..." (not "DEX")."""
    if len(text) > 1 and text[0].isupper() and text[1].islower():
        return text[0].lower() + text[1:]
    return text


def tool_check_card(char, display, answers):
    """A card that's a check with a tool you carry -- "Thieves' tools check"
    (one for each tool: core/actions.py), Decipher Treasure Map, Set a Trap
    -- and Fast Hands, which asks what your bonus action does first. None
    for any other card. {"ok", "check": what, for the apps to roll with
    core/checks.py roll_check (it asks the ability: your DM's call), and
    "check_slot": the part of the turn it takes once rolled}."""
    from dnd_app.core.calculator import carried_tools, get_skill_bonus
    carried = {t.lower(): t for t in carried_tools(char)}
    name = display.strip()

    def tool_check(tool, ability="", note="", check_slot=None):
        return _result(True, "", check={"kind": "check", "tool": tool, "ability": ability, "skill": "",
                                        "label": f"{tool} check", "note": note}, check_slot=check_slot)
    if name.lower().endswith(" check") and name[:-len(" check")].lower() in carried:
        return tool_check(carried[name[:-len(" check")].lower()])
    m = re.fullmatch(r"(Decipher Treasure Map|Set a Trap) \((.+)\)", name)
    if m and m.group(2).lower() in carried:
        if m.group(1) == "Decipher Treasure Map":
            return tool_check(carried[m.group(2).lower()], "INT")
        return tool_check(carried[m.group(2).lower()], note="your total is the trap's DC to find or disable it")
    if name == "Fast Hands":
        opts = ["A Sleight of Hand check"]
        if "thieves' tools" in carried:
            opts.append("Thieves' tools: pick a lock or disarm a trap")
        opts.append("Use an Object")
        if answers.get("fast_hands") not in opts:
            return _result(False, ask={"key": "fast_hands", "title": "Fast Hands: what does your bonus action do?",
                                       "options": opts})
        pick = answers["fast_hands"]
        if pick == "Use an Object":
            return _result(True, "Fast Hands: Use an Object, with your bonus action", slot="Bonus Action")
        if pick.startswith("Thieves' tools"):
            return tool_check(carried["thieves' tools"], check_slot="Bonus Action")
        return _result(True, "", check={"kind": "check", "skill": "Sleight of Hand", "ability": "DEX",
                                        "label": "Sleight of Hand check",
                                        "bonus": get_skill_bonus(char, "Sleight of Hand")},
                       check_slot="Bonus Action")
    return None


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


# ── Wild Shape ────────────────────────────────────────────────────────────
ELEMENTALS = ("Air Elemental", "Earth Elemental", "Fire Elemental", "Water Elemental")


def wild_shape_into(char, beast_name):
    """Turn into a beast: spend a Wild Shape use (two for an elemental,
    Elemental Wild Shape; none for an Archdruid) and take the beast's hit
    points. Both apps' Wild Shape cards and the Use button call this.
    Returns (ok, message)."""
    from dnd_app.data.statblocks import WILDSHAPE_BEASTS
    beast = WILDSHAPE_BEASTS.get(beast_name)
    if not beast:
        return False, f"{beast_name} isn't a form you can take"
    n = 2 if beast_name in ELEMENTALS else 1
    res = _find_pool(char, "ws")
    if res is None:
        return False, "No Wild Shape uses (it comes with 2nd-level druid)"
    left = ""
    if not _unlimited(res):
        if res.get("current", 0) < n:
            return False, ("An elemental takes two Wild Shape uses" if n == 2 and res.get("current", 0)
                           else "No Wild Shape uses left -- they come back on a short or long rest")
        res["current"] -= n
        left = f" ({res['current']} of {res['current_max']} Wild Shape uses left)"
    char["_wildshape_active"] = beast_name
    char["_wildshape_hp"] = beast["hp"]
    fx = char.setdefault("active_effects", [])
    if "Wild Shape" not in fx:
        fx.append("Wild Shape")
    return True, f"Transformed into {beast_name}: {beast['hp']} hit points, AC {beast['ac']}{left}"


def _wild_shape_use(char, key, bucket, answers):
    """The Wild Shape cards: which form, then into it."""
    from dnd_app.core.calculator import get_available_wildshape_beasts
    if char.get("_wildshape_active"):
        return _result(False, f"You're already in Wild Shape ({char['_wildshape_active']}) -- revert first")
    from dnd_app.data.statblocks import WILDSHAPE_BEASTS
    # the strongest forms first
    forms = sorted(get_available_wildshape_beasts(char), key=lambda n: (-WILDSHAPE_BEASTS[n]["cr"], n))
    if key == "elemental wild shape":
        forms = [f for f in forms if f in ELEMENTALS]
    if not forms:
        return _result(False, "No Wild Shape forms available yet")
    if answers.get("beast") not in forms:
        return _result(False, ask={"key": "beast", "title": "Wild Shape into which form?", "options": forms})
    ok, msg = wild_shape_into(char, answers["beast"])
    return _result(ok, msg, slot=bucket if ok else None, refresh=ok, wild_shape=answers["beast"] if ok else None)


# ── The hand-written actions ──────────────────────────────────────────────
def _attack_action(char, answers):
    """The Attack action: which weapon (or other attack) it's made with.
    The apps then roll it the way that attack's Hit button does, and the
    action is spent once the attack is made ("attack_slot")."""
    from dnd_app.core.attacks import attack_rows
    names = list(dict.fromkeys(r["name"] for r in attack_rows(char)))
    if not names:
        return _result(False, "Attack: nothing to attack with")
    pick = answers.get("attack")
    if pick not in names:
        if len(names) > 1:
            return _result(False, ask={"key": "attack", "title": "Attack with which?", "options": names})
        pick = names[0]
    return _result(True, "", attack=pick, attack_slot="Action")


def _special(char, key, display, bucket, answers, rng, desc=""):
    fx = char.setdefault("active_effects", [])
    if key in ("wild shape", "elemental wild shape"):
        return _wild_shape_use(char, key, bucket, answers)
    if key == "attack" and bucket == "Action":
        return _attack_action(char, answers)
    more = _more_specials(char, key, display, bucket, answers, rng, desc)
    if more is not None:
        return more
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
        from dnd_app.core.character import subclasses
        sub = subclasses(char).get("Fighter", "").lower()
        rally = (f". Rallying Cry: up to three creatures within 60 ft regain {_lvl(char, 'fighter')} HP"
                 if _lvl(char, "fighter") >= 3 and ("banneret" in sub or "purple dragon" in sub) else "")
        return _result(True, f"Second Wind: regained {char.get('current_hp', 0) - before} HP ({how}), "
                             f"now {char.get('current_hp', 0)}/{char.get('max_hp', 0)}"
                             + (f". {note}" if note else "") + rally + f" ({_left(res)})",
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
            opts = ["Yourself", "Someone else"] + (["Cure a disease or poison (5 points)"] if pool["current"] >= 5 else [])
            return _result(False, ask={"key": "target", "title": "Who is it for?", "options": opts})
        if answers["target"].startswith("Cure"):
            pool["current"] -= 5
            return _result(True, f"Lay on Hands: cure one disease or neutralize one poison on the creature you touch "
                                 f"(5 points spent, {pool['current']} left in the pool)", slot=bucket, refresh=True)
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


# ── More hand-written actions ─────────────────────────────────────────────
METAMAGIC = {   # option: (sorcery points or "level", what it does)
    "Careful Spell": (1, "up to your CHA modifier creatures automatically succeed on the spell's save"),
    "Distant Spell": (1, "the spell's range doubles (touch becomes 30 ft)"),
    "Empowered Spell": (1, "reroll up to your CHA modifier of the damage dice, using the new rolls"),
    "Extended Spell": (1, "the spell's duration doubles (up to 24 hours)"),
    "Heightened Spell": (3, "one target has disadvantage on its first save against the spell"),
    "Quickened Spell": (2, "a 1-action spell is cast as a bonus action"),
    "Subtle Spell": (1, "no verbal or somatic components"),
    "Twinned Spell": ("level", "the single-target spell targets a second creature in range"),
    "Seeking Spell": (2, "reroll a missed spell attack roll, using the new roll"),
    "Transmuted Spell": (1, "change the spell's acid, cold, fire, lightning, poison or thunder damage to another of them"),
}
SLOT_COSTS = {1: 2, 2: 3, 3: 5, 4: 6, 5: 7}     # Flexible Casting: sorcery points for a slot


def _free_cast_spells(char, source):
    """The spells a feat or trait lets you cast for free ("Misty Step"
    for Fey Touched): the ones it casts at will (Drow High Magic's Detect
    Magic), its own free-cast counters (core/spellcasting.py), or the
    counter of the same name that casts them (Draconic Healing's Cure
    Wounds)."""
    from dnd_app.core.spellcasting import free_spells_of, at_will_feat_spells
    out = at_will_feat_spells(char, source)
    for r in char.get("resources", []):
        name = str(r.get("name", ""))
        m = re.match(r"^(.+) \((.+)\)$", name)
        if m and m.group(2).lower() == source.lower():
            # "Pass Without Trace (Wood Elf Magic)": the spell, as the spell
            # list names it ("Pass without Trace")
            from dnd_app.data.spells import SPELL_NAMES
            spell = ({n.lower(): n for n in SPELL_NAMES}.get(m.group(1).lower())
                     or next(iter(free_spells_of(char, r)), None))
            if spell and spell not in out:
                out.append(spell)
        elif normalize(name) == normalize(source) and r.get("track") != "info":
            out.extend(sp for sp in free_spells_of(char, r) if sp not in out)
    return out


def _more_specials(char, key, display, bucket, answers, rng, desc):
    """Actions that need more than the RULES table: delegating to another
    card, slots and points traded, a pool spent by the die."""
    # a feat's or trait's spell, cast from its card: the app's own cast
    # (which spends the free use) does the rest
    spells = _free_cast_spells(char, display.split(" (")[0])
    if spells:
        if len(spells) > 1 and answers.get("spell") not in spells:
            return _result(False, ask={"key": "spell", "title": f"{display.split(' (')[0]}: cast which spell?",
                                       "options": spells})
        return _result(True, "", cast=answers.get("spell") if answers.get("spell") in spells else spells[0])
    # the Cleric's Channel Divinity card: which option, then that option's card
    if key == "channel divinity" and display.lower().startswith("channel divinity ("):
        m = re.search(r"option: ([^.]+)\.", desc or "")
        opts = [o.strip() for o in m.group(1).split(",")] if m else ["Turn Undead"]
        if answers.get("cd_option") not in opts:
            return _result(False, ask={"key": "cd_option", "title": "Which Channel Divinity?", "options": opts})
        pick = answers["cd_option"]
        pick = "Cloak of Shadows (Channel Divinity)" if pick == "Cloak of Shadows" else pick
        rest = {k: v for k, v in answers.items() if k != "cd_option"}
        return use_action(char, bucket, pick, "", rest, rng)
    # a Battle Master maneuver on a hit (the attack dialog's option): which one
    if key == "maneuver":
        on_hit = on_hit_maneuvers(char)
        if not on_hit:
            return None
        if answers.get("maneuver") not in on_hit:
            return _result(False, ask={"key": "maneuver", "title": "Which maneuver?", "options": on_hit})
        rest = {k: v for k, v in answers.items() if k != "maneuver"}
        return use_action(char, "Passive", answers["maneuver"], "", rest, rng)
    # Flexible Casting: a slot into sorcery points, or points into a slot
    if key == "flexible casting":
        sp = _find_pool(char, "sp")
        if sp is None:
            return None
        ways = ["Turn a spell slot into sorcery points", "Turn sorcery points into a spell slot"]
        if answers.get("way") not in ways:
            return _result(False, ask={"key": "way", "title": "Flexible Casting:", "options": ways})
        maxes = char.get("spell_slots_max", [0] * 9)
        used = char.setdefault("spell_slots_used", [0] * 9)
        if answers["way"] == ways[0]:
            have = [l for l in range(1, 10) if maxes[l - 1] - used[l - 1] > 0]
            if not have:
                return _result(False, "Flexible Casting: no spell slots left to convert")
            opts = [f"{_ordinal(l)}-level slot (+{l} points)" for l in have]
            if answers.get("slot") not in opts:
                return _result(False, ask={"key": "slot", "title": f"Which slot? ({sp.get('current', 0)}/{sp.get('current_max')} points)",
                                           "options": opts})
            lvl = have[opts.index(answers["slot"])]
            used[lvl - 1] += 1
            sp["current"] = min(sp.get("current_max", 0), sp.get("current", 0) + lvl)
            return _result(True, f"Flexible Casting: a {_ordinal(lvl)}-level slot became {lvl} sorcery points "
                                 f"({sp['current']}/{sp['current_max']})", slot=bucket, refresh=True, slots_changed=True)
        can = [l for l in SLOT_COSTS if used[l - 1] > 0 and maxes[l - 1] > 0 and sp.get("current", 0) >= SLOT_COSTS[l]]
        if not can:
            return _result(False, "Flexible Casting: no spent slot of 5th level or lower you have the points for")
        opts = [f"{_ordinal(l)}-level slot ({SLOT_COSTS[l]} points)" for l in can]
        if answers.get("slot") not in opts:
            return _result(False, ask={"key": "slot", "title": f"Which slot? ({sp.get('current', 0)} points)",
                                       "options": opts})
        lvl = can[opts.index(answers["slot"])]
        sp["current"] -= SLOT_COSTS[lvl]
        used[lvl - 1] -= 1
        return _result(True, f"Flexible Casting: {SLOT_COSTS[lvl]} sorcery points became a {_ordinal(lvl)}-level slot "
                             f"({sp['current']} points left)", slot=bucket, refresh=True, slots_changed=True)
    # Metamagic: one of your options, its sorcery points spent as you cast
    if key == "metamagic":
        sp = _find_pool(char, "sp")
        known = [m.split(" –")[0].split(" (")[0].strip()
                 for m in (char.get("_choices", {}) or {}).get("sorcerer_metamagic", []) or []]
        known = [m for m in known if m in METAMAGIC]
        if sp is None or not known:
            return None
        if answers.get("metamagic") not in known:
            return _result(False, ask={"key": "metamagic", "title": f"Which Metamagic? ({sp.get('current', 0)} points)",
                                       "options": known})
        pick = answers["metamagic"]
        cost, what = METAMAGIC[pick]
        if cost == "level":
            lv_opts = ["A cantrip (1 point)"] + [f"{_ordinal(l)}-level spell ({l} points)" for l in range(1, 10)]
            if answers.get("level") not in lv_opts:
                return _result(False, ask={"key": "level", "title": "Twinned Spell: the spell's level?", "options": lv_opts})
            cost = max(1, lv_opts.index(answers["level"]))
        if sp.get("current", 0) < cost:
            return _result(False, f"{pick}: needs {cost} sorcery point{'s' if cost != 1 else ''} "
                                  f"({sp.get('current', 0)} left)")
        sp["current"] -= cost
        return _result(True, f"{pick}: {what} ({cost} sorcery point{'s' if cost != 1 else ''} spent, "
                             f"{sp['current']} left)", refresh=True)
    # Healing Light (Celestial): d6s from the pool, up to your CHA modifier
    if key == "healing light":
        pool = _own_resource(char, "Healing Light")
        if pool is None:
            return None
        have = pool.get("current", 0)
        if have <= 0:
            return _result(False, "Healing Light: no dice left in the pool (back on a long rest)")
        most = min(have, max(1, _mods(char)["CHA"]))
        opts = [f"{n}d6" for n in range(1, most + 1)]
        if answers.get("dice") not in opts:
            return _result(False, ask={"key": "dice", "title": f"Healing Light: how many dice? ({have} in the pool)",
                                       "options": opts})
        if "target" not in answers:
            return _result(False, ask={"key": "target", "title": "Who is it for?", "options": ["Yourself", "Someone else"]})
        n = int(answers["dice"].split("d")[0])
        pool["current"] = have - n
        if answers["target"] == "Yourself":
            from dnd_app.core.dying import heal
            total = sum(rng.randint(1, 6) for _ in range(n))
            before = char.get("current_hp", 0)
            note = heal(char, total)
            return _result(True, f"Healing Light: regained {char.get('current_hp', 0) - before} HP ({total} on "
                                 f"{n}d6), now {char.get('current_hp')}/{char.get('max_hp')}" + (f". {note}" if note else "")
                                 + f" ({pool['current']} dice left)", slot=bucket, refresh=True)
        return _result(True, f"Healing Light: the creature regains {n}d6 hit points ({pool['current']} dice left)",
                       slot=bucket, refresh=True)
    # Grim Harvest (Necromancy): hit points back when a spell kills
    if key == "grim harvest":
        opts = [f"{_ordinal(l)}-level spell" for l in range(1, 10)]
        if answers.get("level") not in opts:
            return _result(False, ask={"key": "level", "title": "Grim Harvest: the spell's level?", "options": opts})
        if answers.get("necro") not in ("Yes", "No"):
            return _result(False, ask={"key": "necro", "title": "Was it a necromancy spell?", "options": ["No", "Yes"]})
        lvl = opts.index(answers["level"]) + 1
        amount = lvl * (3 if answers["necro"] == "Yes" else 2)
        from dnd_app.core.dying import heal
        before = char.get("current_hp", 0)
        heal(char, amount)
        return _result(True, f"Grim Harvest: regained {char.get('current_hp', 0) - before} HP, now "
                             f"{char.get('current_hp')}/{char.get('max_hp')}", refresh=True)
    # Combat Wild Shape: a spell slot for 1d8 hit points a level, in beast form
    if key == "combat wild shape":
        if not char.get("_wildshape_active"):
            # Combat Wild Shape: Wild Shape with your bonus action
            return _wild_shape_use(char, "wild shape", bucket, answers)
        free = [s for s in _slots_free(char) if s[1] == "slot"]
        if not free:
            return _result(False, "Combat Wild Shape: no spell slots left")
        if answers.get("slot") not in [s[0] for s in free]:
            return _result(False, ask={"key": "slot", "title": "Expend which spell slot?", "options": [s[0] for s in free]})
        lvl = next(s[2] for s in free if s[0] == answers["slot"])
        char["spell_slots_used"][lvl - 1] += 1
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(char["_wildshape_active"], {})
        total = sum(rng.randint(1, 8) for _ in range(lvl))
        cur = char.get("_wildshape_hp", beast.get("hp", 0))
        char["_wildshape_hp"] = min(beast.get("hp", cur + total), cur + total)
        return _result(True, f"Combat Wild Shape: the beast regains {char['_wildshape_hp'] - cur} HP ({total} on "
                             f"{lvl}d8), now {char['_wildshape_hp']}/{beast.get('hp', '?')} (spent a "
                             f"{_ordinal(lvl)}-level slot)", slot=bucket, refresh=True, slots_changed=True)
    # Blood Maledict: one of your known curses, invoked or amplified with
    # your own blood (Blood Hunter)
    if key == "blood maledict":
        pool = _find_pool(char, "maledict")
        known = []
        for c in (char.get("_choices", {}) or {}).get("blood_hunter_curses", []) or []:
            name = c.split(" –")[0].split(" (")[0].strip()
            text = c.split(" – ", 1)[1] if " – " in c else ""
            known.append((name, text))
        if pool is None or not known:
            return None
        if not _unlimited(pool) and pool.get("current", 0) <= 0:
            return _result(False, "Blood Maledict: no uses left (back on a short or long rest)")
        names = [n for n, _ in known]
        if answers.get("curse") not in names:
            return _result(False, ask={"key": "curse", "title": "Which blood curse?", "options": names})
        ways = ["Invoke it", "Amplify it (take your hemocraft die in necrotic damage)"]
        if answers.get("amplify") not in ways:
            return _result(False, ask={"key": "amplify", "title": f"{answers['curse']}:", "options": ways})
        text = dict(known)[answers["curse"]]
        base, _, amp = text.partition(" Amplify: ")
        when = re.match(r"(bonus action|reaction|action)\b[^:]*:\s*", base, re.I)
        slot = {"bonus action": "Bonus Action", "reaction": "Reaction", "action": "Action"}.get(
            when.group(1).lower() if when else "", bucket)
        base = base[when.end():] if when else base
        hurt = ""
        if answers["amplify"] == ways[1]:
            die = formula(char, "HEMODIE")
            sides = int(die.split("d")[1])
            if not str(answers.get("self_roll", "")).isdigit():
                return _result(False, ask={"key": "self_roll", "title": f"Roll {die} for the necrotic damage you take. "
                                                                       f"What did you roll?",
                                           "options": [str(i) for i in range(1, sides + 1)]})
            from dnd_app.core.dying import take_damage
            take_damage(char, int(answers["self_roll"]))
            hurt = (f"; amplified: {_lower_first(amp.rstrip('.'))} (you take {answers['self_roll']} necrotic damage, "
                    f"now {char.get('current_hp', 0)}/{char.get('max_hp', 0)} HP)")
        if not _unlimited(pool):
            pool["current"] -= 1
        return _result(True, f"{answers['curse']}: {_lower_first(_tokens(char, base).rstrip('.'))}{hurt} "
                             f"({_left(pool)})", slot=slot, refresh=True)
    # Divine Intervention: percentile dice against your cleric level
    if key == "divine intervention":
        uses = _uses_resource(char, display, {"uses": "1/LR"})
        if uses is not None and uses.get("current", 0) <= 0:
            return _result(False, "Divine Intervention: not again until after a long rest (7 days after a success)")
        lvl = _lvl(char, "cleric")
        roll = rng.randint(1, 100)
        ok = lvl >= 20 or roll <= lvl
        if uses is not None:
            uses["current"] = 0
        how = "automatic at 20th level" if lvl >= 20 else f"rolled {roll} against your cleric level {lvl}"
        return _result(True, f"Divine Intervention: {how} -- "
                             + ("your deity intervenes (describe the help; the DM picks the miracle). Not again for "
                                "7 days" if ok else "no answer this time. You can try again after a long rest"),
                       slot=bucket, refresh=True)
    # Portent: one of the foretelling rolls takes the place of a d20
    if key == "portent" and _portent_res(char) is not None:
        rolls = portent_rolls(char, rng)
        if not rolls:
            return _result(False, "Portent: no foretelling rolls left (you roll new ones after a long rest)")
        options = [str(r) for r in sorted(set(rolls), reverse=True)]
        if len(options) > 1 and answers.get("portent") not in options:
            return _result(False, ask={"key": "portent", "title": "Portent: use which roll?", "options": options})
        pick = int(answers.get("portent") if answers.get("portent") in options else options[0])
        return _result(True, spend_portent(char, pick), refresh=True)
    return None


# ── Portent ───────────────────────────────────────────────────────────────
# A Diviner rolls two d20s (three from 14th level) after each long rest and
# can use one in place of any attack roll, saving throw or ability check
# made by them or a creature they can see. The rolls are kept on the
# character ("portent_rolls"); the Portent counter says how many are left.
def _portent_res(char):
    return next((r for r in char.get("resources", []) if r.get("key") == "portent"), None)


def portent_rolls(char, rng=random) -> list:
    """The foretelling rolls still unused, kept in step with the Portent
    counter: a roll is made for each use the counter has and the list
    doesn't (a new character, or a use put back by hand), and the last
    ones go when the counter has fewer (a roll spent at the table)."""
    res = _portent_res(char)
    if res is None:
        return []
    n = max(0, int(res.get("current", 0) or 0))
    rolls = [int(r) for r in char.get("portent_rolls") or []][:n]
    rolls += [rng.randint(1, 20) for _ in range(n - len(rolls))]
    char["portent_rolls"] = rolls
    return rolls


def spend_portent(char, roll) -> str:
    """Use the foretelling roll showing this number: it's gone, and the
    Portent counter goes down one. Returns the message."""
    rolls = portent_rolls(char)
    if roll not in rolls:
        return f"Portent: no {roll} left among your rolls"
    rolls.remove(roll)
    res = _portent_res(char)
    res["current"] = max(0, res.get("current", 0) - 1)
    left = f"rolls left: {', '.join(map(str, rolls))}" if rolls else "no rolls left until your next long rest"
    return f"Portent: the d20 roll is a {roll} ({left})"


def roll_portent(char, rng=random) -> str:
    """After a long rest: any unused rolls are lost and new ones are rolled
    (call it once the counters are back to full). Returns the line for the
    rest message, "" without Portent."""
    if _portent_res(char) is None:
        return ""
    char["portent_rolls"] = []
    return "Portent rolls: " + ", ".join(map(str, portent_rolls(char, rng)))


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
    import json
    # everything that changes which cards there are: classes, race, feats,
    # and every pick (runes, maneuvers, invocations, optional features...)
    sig = (tuple(sorted((c.get("class"), c.get("level"), c.get("subclass", "")) for c in char.get("classes", []))),
           char.get("race"), char.get("subrace"), tuple(sorted(char.get("feats", []))),
           tuple(sorted(_mods(char).items())), _pb(char),
           json.dumps(char.get("_choices", {}), sort_keys=True, default=str),
           tuple(char.get("eldritch_invocations", []) or []), tuple(char.get("battle_master_maneuvers", []) or []),
           tuple(sorted((char.get("optional_rules") or {}).items())))
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
                spec = rule_for(display)
                if not spec or not spec.get("uses"):
                    continue
                name = display.split("(")[0].strip()
                if spec.get("each"):
                    # one counter per option (Lunar Phenomenon's phases)
                    for opt in spec["each"]:
                        oname = f"{name} ({opt})"
                        okey = _use_key(oname)
                        if okey in seen or _own_resource({"resources": existing}, oname):
                            continue
                        seen.add(okey)
                        mx, reset = _uses_max(char, spec["uses"])
                        cached.append({"name": oname, "key": okey, "reset": reset, "current_max": mx,
                                       "track": "uses", "note": _summary(desc, 200),
                                       "source_class": "", "subclass": ""})
                    continue
                key = _use_key(spec.get("share") or name)
                if key in seen:
                    continue
                if _own_resource({"resources": existing}, name) or \
                        (spec.get("share") and _own_resource({"resources": existing}, spec["share"])):
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

    # 1b. a check with a tool you carry, rolled by the apps (core/checks.py)
    out = tool_check_card(char, display, answers)
    if out is not None:
        return out

    # 1c. a potion or a scroll you carry (core/actions.py potion_scroll_cards):
    #     the apps drink or read it, and mark the part of the turn it took
    #     ("spends" -- a spell scroll's spell marks its own casting time)
    from dnd_app.core.actions import carried_use_item
    carried = carried_use_item(char, display)
    if carried is not None:
        from dnd_app.core.spellcasting import parse_spell_scroll
        spell_scroll = carried["kind"] == "scroll" and parse_spell_scroll(carried["name"])
        return _result(True, "", use_item=carried, spends=None if spell_scroll else slot)

    # 2. hand-written
    out = _special(char, key, display, slot, answers, rng, desc)
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

    # 5. a cost its own text names ("Spend 2 ki to cast..." -- the Four
    #    Elements disciplines), then the turn
    m = re.search(r"\bspend (\d+) (ki|sorcery points?)\b", desc or "", re.I)
    if m:
        pool = "ki" if m.group(2).lower() == "ki" else "sp"
        return _use_rule(char, display, desc, {"cost": (pool, int(m.group(1)))}, slot, answers, rng)
    return _result(True, f"{display}: {_lower_first(_summary(desc)) or 'used'}", slot=slot)


# ── Magic items ───────────────────────────────────────────────────────────
# Item effects switched on and off from the item's action card
ITEM_TOGGLES = {"Flame Tongue": "Flame Tongue"}
_DAILY_RE = re.compile(r"(\d+)/day|once (?:per|a) (?:day|dawn)|until the next dawn", re.I)
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
    # "Invisibility (Jewel of Three Prayers (Awakened))": the item's own
    # name can have brackets in it, so it's matched whole at the end
    for n in sorted(names, key=len, reverse=True):
        if (display or "").endswith(f"({n})"):
            return n
    base = (display or "").split("(")[0].strip().lower()
    for n in names:
        if base and base == n.lower():
            return n
    # a card named for the item without its state ("Verminshroud (3/day)"
    # for the Verminshroud (Dormant))
    for n in names:
        if base and n.lower().startswith(base + " ("):
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
        # once a day, or N times a day ("Verminshroud (3/day)")
        m = _DAILY_RE.search(text)
        per_day = int(m.group(1)) if m.group(1) else 1
        uses = char.setdefault("item_uses", {}).setdefault(display, {"current": per_day, "max": per_day,
                                                                     "recharge": "dawn"})
        uses["max"] = per_day
        if uses.get("current", 0) <= 0:
            return _result(False, f"{display}: already used today (back at dawn)")
        uses["current"] -= 1
        tail = (" (used for today, back at dawn)" if per_day == 1 else
                f" ({uses['current']} of {per_day} left today, back at dawn)")
        if display == "Cursed Luckstone":
            # its curse, the same as when a check uses it (core/checks.py)
            char["_luckstone_curse"] = 2
            tail += ". Your next two ability checks have disadvantage"
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
    if display == "Rage":
        from dnd_app.core.character import subclasses
        if "wild magic" in subclasses(char).get("Barbarian", "").lower():
            # Wild Surge: entering the rage rolls on the Wild Magic table
            _, rolled = _table_roll(char, ("1d8", WILD_MAGIC_BARBARIAN_TABLE), random)
            msg += f". Wild Surge: {rolled}"
    if res.get("key") == "action_surge" or display.startswith("Action Surge"):
        char["_action_surge_used_this_turn"] = True
        slot = None
    return _result(True, msg, slot=slot, refresh=True)


def _aasimar_say(char, name):
    """An aasimar's transformation, with this character's numbers: the extra
    damage is your level (VGM) or your proficiency bonus (MPMM)."""
    import math
    mpmm, pb, cha = _mpmm(char), _pb(char), _mods(char)["CHA"]
    n = pb if mpmm else _level(char)
    hit = f"once on each of your turns, +{n} {'necrotic' if name == 'Necrotic Shroud' else 'radiant'} damage to " \
          f"one target of your attack or spell"
    if name == "Necrotic Shroud":
        return (f"for 1 minute: creatures other than your allies within 10 ft that can see you make a DC "
                f"{8 + pb + cha} CHA save or are frightened of you until the end of your next turn; {hit}")
    if name == "Radiant Consumption":
        aura = (f"each creature within 10 ft takes {pb} radiant damage" if mpmm else
                f"you and each creature within 10 ft take {math.ceil(_level(char) / 2)} radiant damage")
        return f"for 1 minute: bright light 10 ft; at the end of each of your turns {aura}; {hit}"
    fly = "a flying speed equal to your walking speed" if mpmm else "a flying speed of 30 ft"
    return f"for 1 minute: {fly}; {hit}"


def _shifting_say(char):
    """What shifting gives this shifter, by kind (the temporary hit points
    are in on_effect_started's note)."""
    sub = (char.get("subrace") or "").lower()
    kinds = {"beasthide": "+1 AC while shifted",
             "longtooth": "your fangs: a bonus action attack (its row is on the Combat page)",
             "swiftstride": "+10 ft walking speed, and your reaction can move you 10 ft when a creature ends its "
                            "turn within 5 ft (the Swiftstride Step card)",
             "wildhunt": "advantage on WIS checks, and no creature within 30 ft can make an attack roll with "
                         "advantage against you unless you're incapacitated"}
    what = next((v for k, v in kinds.items() if k in sub), "your shifter kind's benefit")
    return f"for 1 minute (end it with a bonus action): {what}"


def _toggle_say(char, name):
    if name == "Shifting":
        return _shifting_say(char)
    if name in ("Radiant Soul (Aasimar)", "Necrotic Shroud", "Radiant Consumption") \
            and "aasimar" in (char.get("species") or char.get("race", "") or "").lower():
        return _aasimar_say(char, name)
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


def _tokens(char, text):
    """The numbers a card's text needs, worked out for this character:
    {PB}; {STR}..{CHA} (the modifier, at least 1); {DC_STR}..{DC_CHA}
    (8 + PB + that modifier); {SPELL_DC}; {LEVEL}; {LVL:Monk} (a class's
    level); {HALF:Wizard} (half of it, rounded down)."""
    if "{" not in (text or ""):
        return text or ""
    mods, pb = _mods(char), _pb(char)
    for ab, m in mods.items():
        text = text.replace("{" + ab + "}", str(max(1, m))).replace("{DC_" + ab + "}", str(8 + pb + m))
    text = text.replace("{PB}", str(pb))
    # a Battle Master's maneuver save DC: 8 + PB + STR or DEX, the higher
    text = text.replace("{DC_MAN}", str(8 + pb + max(mods["STR"], mods["DEX"])))
    if "{SPELL_DC}" in text:
        from dnd_app.core.calculator import get_spell_save_dc
        text = text.replace("{SPELL_DC}", str(get_spell_save_dc(char)))
    if "{SPELL_ATK}" in text:
        from dnd_app.core.calculator import get_spell_attack_bonus
        b = get_spell_attack_bonus(char)
        text = text.replace("{SPELL_ATK}", f"+{b}" if b >= 0 else str(b))
    if "{LEVEL}" in text:
        from dnd_app.core.character import total_level
        text = text.replace("{LEVEL}", str(total_level(char)))
    text = re.sub(r"\{LVL:([A-Za-z ]+)\}", lambda m: str(_lvl(char, m.group(1).lower())), text)
    text = re.sub(r"\{HALF:([A-Za-z ]+)\}", lambda m: str(max(1, _lvl(char, m.group(1).lower()) // 2)), text)
    return text


def _table_roll(char, table, rng, name=""):
    """Roll on a table: (die, entries) with entries [(low, high, text)] or
    [(n, text)] -> "rolled 6: ..."."""
    die, entries = table
    die = _special_die(char, die, name) if not re.fullmatch(r"\d+d\d+", die) else die
    n, s = map(int, die.split("d"))
    roll = sum(rng.randint(1, s) for _ in range(n))
    for e in entries:
        lo, hi, text = (e[0], e[0], e[1]) if len(e) == 2 else e
        if lo <= roll <= hi:
            return roll, f"rolled {roll}: {_lower_first(_tokens(char, text)).rstrip('.')}"
    return roll, f"rolled {roll}"


def _use_rule(char, display, desc, spec, slot, answers, rng):
    from dnd_app.core.effects import EFFECT_TABLE
    fx = char.setdefault("active_effects", [])
    name = display.split("(")[0].strip()
    # a card with options (Bolstering Magic, Spirit Totem, Storm Aura...):
    # which one, then that option's own rules on top
    if spec.get("choose"):
        opts = spec["choose"](char) if callable(spec["choose"]) else spec["choose"]
        opts = [o for o in opts if o]
        labels = [o["label"] for o in opts]
        if len(labels) == 1:
            answers.setdefault("choice", labels[0])
        if answers.get("choice") not in labels:
            if not labels:
                return _result(False, f"{name}: nothing to choose from yet")
            return _result(False, ask={"key": "choice", "title": spec.get("ask", f"{name}: which one?"),
                                       "options": labels})
        opt = next(o for o in opts if o["label"] == answers["choice"])
        spec = {**{k: v for k, v in spec.items() if k not in ("choose", "ask")},
                **{k: v for k, v in opt.items() if k != "label"}}
        if spec.get("as"):
            name = spec["as"]
    if spec.get("slot") is False:
        slot = None
    elif spec.get("slot") in ("Action", "Bonus Action", "Reaction"):
        slot = spec["slot"]
    # requirements
    if spec.get("needs"):
        why = _need_problem(char, spec["needs"])
        if why:
            return _result(False, f"{name}: {why}")
    turn = char.setdefault("_turn_uses", [])
    if spec.get("once") and name in turn:
        return _result(False, f"{name}: already used this turn")
    # once per rage (Fanatical Focus): back when a new rage starts
    per = None
    if spec.get("once_per"):
        per = char.setdefault("_once_per", {}).setdefault(spec["once_per"], [])
        if name in per:
            return _result(False, f"{name}: already used this {spec['once_per'].lower()}")
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
    if spec.get("remember") and answers.get("choice"):
        picked["choice"] = answers["choice"]

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
    if per is not None:
        per.append(name)

    lines, refresh = [], bool(spent)
    say = spec.get("say", "")
    say = say.replace("KI-1", str(max(1, chosen - 1))).replace("+KI", f"+{chosen}").replace("KI d8s", f"{chosen}d8s")
    say = say.replace("{KI2}", str(2 * chosen))
    say = say.replace("WEAPON", sharpened.lower())
    say = _tokens(char, say)
    # rolls
    say = _breath_tokens(char, say)
    if spec.get("table"):
        # a roll on its table (Wild Magic, Spirit Tales, an elixir...)
        _, rolled = _table_roll(char, spec["table"], rng, name=display)
        lines.append(rolled)
    if spec.get("exhaust"):
        # it costs a level of exhaustion (Convergent Future)
        char["exhaustion"] = min(6, char.get("exhaustion", 0) + spec["exhaust"])
        lines.append(f"you gain a level of exhaustion (now {char['exhaustion']})")
        refresh = True
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
    if spec.get("spell"):
        # a spell cast through the feature: no other spell from the attack
        # dialog this turn
        note_spell_cast(char, name)
    if spec.get("regain_pool"):
        pool_code, n = spec["regain_pool"]
        res = _find_pool(char, pool_code)
        if res is not None and not _unlimited(res):
            res["current"] = min(res.get("current_max", 0), res.get("current", 0) + n)
            lines.append(f"regained {n} {_noun(pool_code, n)} ({res['current']}/{res['current_max']})")
            refresh = True
    if spec.get("regain_slot"):
        lvl = spec["regain_slot"]
        used = char.setdefault("spell_slots_used", [0] * 9)
        if used[lvl - 1] > 0:
            used[lvl - 1] -= 1
            lines.append(f"regained a {_ordinal(lvl)}-level spell slot")
            refresh = True
    if spec.get("end_fx") and spec["end_fx"] in fx:
        end_effects(char, [spec["end_fx"]])
        refresh = True
    if spec.get("end_condition"):
        conds = char.get("conditions", [])
        gone = next((c for c in spec["end_condition"] if c in conds), None)
        if gone:
            conds.remove(gone)
            lines.append(f"you're no longer {gone.lower()}")
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
        if picked.get("weapon") or picked.get("type"):
            where = f" on your {picked['weapon']}" if picked.get("weapon") else ""
            if effect == "Elemental Cleaver":
                note = f"+{_cleaver_dice(char)} {picked.get('type', '')} damage{where} while you rage"
            else:
                note = f"+1d4 {picked.get('type', '')} damage{where} for 1 minute"
        elif picked.get("choice") and say:
            note = ""              # the option picked says what it does (a Starry Form constellation)
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
