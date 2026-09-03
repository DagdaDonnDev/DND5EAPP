"""
Active spell-effect engine.

char["active_effects"] is a list of effect-name strings. EFFECT_TABLE maps
each known effect to its mechanical hooks; anything not in the table is
tracked as a note-only effect (still listed, no auto numbers).

Hooks:
  ac         flat AC bonus (may be negative)
  ac_floor   AC becomes at least this value (Barkskin)
  speed_mult multiply walking speed
  speed_add  flat speed bonus
  extra_action  True → grants one extra Action per turn (Haste)
  conc       effect requires the *caster's* concentration (display hint)
  note       one-line mechanical summary shown in the Effects tab

Author: Ethan O'Brien
Date: 2026-08-20
"""

EFFECT_TABLE: dict[str, dict] = {
    "Haste": {
        "ac": 2, "speed_mult": 2, "extra_action": True, "conc": True,
        "note": "+2 AC, double speed, adv. DEX saves, +1 action "
                "(Attack ×1 / Dash / Disengage / Hide / Use Object). "
                "Lethargy when it ends.",
    },
    "Slow": {
        "ac": -2, "speed_mult": 0.5, "conc": True,
        "note": "−2 AC & DEX saves, half speed, no reactions, "
                "action OR bonus action (not both).",
    },
    "Shield (spell)": {
        "ac": 5,
        "note": "+5 AC until the start of your next turn; "
                "immune to Magic Missile.",
    },
    "Shield of Faith": {
        "ac": 2, "conc": True,
        "note": "+2 AC for the duration (10 min).",
    },
    "Barkskin": {
        "ac_floor": 16, "conc": True,
        "note": "Your AC can't be lower than 16.",
    },
    "Bless": {
        "conc": True,
        "note": "+1d4 to attack rolls and saving throws.",
    },
    "Bane": {
        "conc": True,
        "note": "−1d4 to attack rolls and saving throws.",
    },
    "Enlarge": {
        "conc": True,
        "note": "Size up one category, +1d4 weapon damage, "
                "advantage on STR checks & saves.",
    },
    "Reduce": {
        "conc": True,
        "note": "Size down one category, −1d4 weapon damage, "
                "disadvantage on STR checks & saves.",
    },
    "Blur": {
        "conc": True,
        "note": "Attackers have disadvantage unless they don't rely on sight.",
    },
    "Hybrid Transformation": {
        "ac_no_heavy_armor": 1,
        "note": "Advantage on STR checks/saves; +1 melee damage (+2 at 11th, "
                "+3 at 18th); resistance to nonmagical/non-silvered B/P/S "
                "damage; +1 AC if not wearing heavy armor. Bloodlust: below "
                "half HP, DC 8 WIS save at the start of your turn or attack "
                "the nearest creature.",
    },
    "Invisibility": {
        "conc": True,
        "note": "Attacks against you have disadvantage; yours have advantage. "
                "Ends if you attack or cast.",
    },
    "Greater Invisibility": {
        "conc": True,
        "note": "As Invisibility but does not end when you attack or cast.",
    },
    "Faerie Fire": {
        "note": "Attacks against you have advantage; you can't benefit "
                "from being invisible.",
    },
    "Mirror Image": {
        "note": "3 duplicates; attacks may hit an image (AC 10+DEX) instead.",
    },
    "Longstrider": {
        "speed_add": 10,
        "note": "+10 ft walking speed (1 hour).",
    },
    "Kinetic Jaunt": {
        "speed_add": 10,
        "conc": True,
        "note": "+10 ft walking speed. Doesn't provoke opportunity attacks from movement. Can "
                "move through another creature's space (not difficult terrain); if you end your "
                "turn there, you're shunted to the last unoccupied space and take 1d8 force "
                "damage. 1 minute.",
    },
    "Darkvision": {
        "note": "Darkvision 60 ft. (8 hours). Mechanical hook applied automatically.",
    },
    "Spider Climb": {
        "note": "Climbing speed equal to walking speed; can climb difficult surfaces/ceilings "
                "hands-free. Mechanical hook applied automatically.",
    },
    "Protection from Poison": {
        "conc": False,
        "note": "Advantage on saves vs. poisoned; resistance to poison damage (1 hour). "
                "Also neutralizes one poison currently affecting you, if any.",
    },
    "Gaseous Form": {
        "conc": True,
        "note": "Fly speed 10 ft. (only movement method); can occupy another creature's "
                "space; resistance to nonmagical damage (hook applied automatically); "
                "advantage on STR/DEX/CON saves. Ends if reduced to 0 HP.",
    },
    "Invulnerability": {
        "conc": True,
        "note": "Immune to all damage (hook applied automatically).",
    },
    "Aura of Life": {
        "conc": True,
        "note": "30-ft aura (moves with you): nonhostile creatures inside (including you) "
                "have resistance to necrotic damage (hook applied automatically) and their HP "
                "max can't be reduced; a nonhostile living creature at 0 HP regains 1 HP at "
                "the start of its turn in the aura.",
    },
    "Enhance Ability": {
        "conc": True,
        "note": "Choose one: Bear's Endurance (adv. CON checks, +2d6 temp HP), Bull's Strength "
                "(adv. STR checks, double carry capacity), Cat's Grace (adv. DEX checks, no fall "
                "damage from a controlled fall), Eagle's Splendor (adv. CHA checks), Fox's "
                "Cunning (adv. INT checks), or Owl's Wisdom (adv. WIS checks). 1 hour.",
    },
    "Zephyr Strike": {
        "conc": False,
        "note": "Your movement doesn't provoke opportunity attacks. Once before the spell "
                "ends: advantage on one weapon attack (+1d8 force on a hit), and your walking "
                "speed +30 ft. until the end of that turn either way. 1 minute.",
    },
    "Protection from Energy": {
        "conc": True,
        "note": "Resistance to one damage type of your choice: acid, cold, fire, lightning, "
                "or thunder. 1 hour.",
    },
    "Aura of Purity": {
        "conc": True,
        "note": "30-ft aura (moves with you): nonhostile creatures inside (including you) "
                "can't become diseased, have resistance to poison damage (hooks applied "
                "automatically), and advantage on saves vs. blinded/charmed/deafened/"
                "frightened/paralyzed/poisoned/stunned.",
    },
    "Holy Aura": {
        "conc": True,
        "note": "30-ft radius: chosen creatures (including you) shed dim light and have "
                "advantage on all saves; other creatures have disadvantage on attacks against "
                "them. A fiend/undead that melee-hits an affected creature must make a CON "
                "save or be blinded. 1 minute.",
    },
    "Circle of Power": {
        "conc": True,
        "note": "30-ft sphere (moves with you): friendly creatures inside (including you) "
                "have advantage on saves vs. spells/magical effects, and a successful "
                "half-damage-on-success save instead takes no damage. 10 minutes.",
    },
    "Mind Blank": {
        "conc": False,
        "note": "Immune to psychic damage, mind-reading/emotion-sensing, divination spells, "
                "and the charmed condition (hooks applied automatically). Foils wish and "
                "similar effects targeting the mind. 24 hours.",
    },
    "Alter Self: Aquatic Adaptation": {
        "conc": True,
        "note": "Breathe underwater; swimming speed equal to walking speed (hook applied "
                "automatically). Can switch to a different Alter Self option as an action.",
    },
    "Alter Self: Change Appearance": {
        "conc": True,
        "note": "Change your appearance (height/weight/features/voice/etc., including looking "
                "like another race — no stats change, same size/basic shape). Can switch to a "
                "different Alter Self option as an action.",
    },
    "Alter Self: Natural Weapons": {
        "conc": True,
        "note": "Grow claws/fangs/spines/horns: unarmed strikes deal 1d6 (your choice of "
                "bludgeoning/piercing/slashing), you're proficient with them, and they count as "
                "magic with a +1 attack/damage bonus. Can switch to a different Alter Self "
                "option as an action.",
    },
    "Foresight": {
        "conc": False,
        "note": "Can't be surprised; advantage on attack rolls, ability checks, and saving "
                "throws; other creatures have disadvantage on attacks against you. Ends "
                "immediately if cast again before its duration ends. 8 hours.",
    },
    "Feign Death": {
        "conc": False,
        "note": "Appears dead to all inspection (including detection spells); blinded, "
                "incapacitated, speed 0; resistance to all damage except psychic. Any disease/"
                "poison affecting you is suspended until the spell ends. 1 hour.",
    },
    "Absorb Elements": {
        "conc": False,
        "note": "Resistance to the triggering damage type (acid/cold/fire/lightning/thunder) "
                "until the start of your next turn. First melee hit before then adds +1d6 of "
                "that type (+1d6 per slot level above 1st) and ends the spell.",
    },
    "Investiture of Flame": {
        "conc": True,
        "note": "Immune to fire damage, resistance to cold damage (hooks applied "
                "automatically). Sheds light 30/30 ft. Creatures that start their turn or "
                "move within 5 ft. of you take 1d10 fire. Action: 15x5 ft. line, DEX save or "
                "4d8 fire (half on success).",
    },
    "Investiture of Ice": {
        "conc": True,
        "note": "Immune to cold damage, resistance to fire damage (hooks applied "
                "automatically). No extra movement cost on ice/snow terrain; a 10-ft. icy "
                "difficult-terrain radius follows you. Action: 15-ft. cone, CON save or 4d6 "
                "cold (half on success), fails also reduce speed to 0 until start of next turn.",
    },
    "Investiture of Stone": {
        "conc": True,
        "note": "Resistance to nonmagical bludgeoning/piercing/slashing (hook applied "
                "automatically). No extra movement cost through earth/stone terrain (can't end "
                "movement inside it). Action: 15-ft. radius earthquake, DEX save or knocked "
                "prone.",
    },
    "Fire Shield: Warm Shield": {
        "conc": False,
        "note": "Resistance to cold damage (hook applied automatically). A creature that hits "
                "you with a melee attack within 5 ft. takes 2d8 fire damage.",
    },
    "Fire Shield: Chill Shield": {
        "conc": False,
        "note": "Resistance to fire damage (hook applied automatically). A creature that hits "
                "you with a melee attack within 5 ft. takes 2d8 cold damage.",
    },
    "Beast Bond": {
        "conc": True,
        "note": "Telepathic link with a touched, friendly/charmed beast (INT 3 or lower) while "
                "in line of sight; it can send simple emotions/concepts back. The beast has "
                "advantage on attack rolls against any creature within 5 ft. of you.",
    },
    "Ensnaring Strike": {
        "conc": True,
        "note": "Your next weapon hit before this ends: target makes a STR save (advantage if "
                "Large+) or is restrained by vines until the spell ends, taking 1d6 piercing at "
                "the start of each of its turns. 1 minute.",
    },
    "Bestow Curse": {
        "conc": True,
        "note": "Touch a creature: WIS save or cursed with one chosen effect (disadvantage on "
                "checks/saves with one ability score; disadvantage on attacks against you; WIS "
                "save each turn near you or waste its action; your attacks deal +1d8 necrotic "
                "to it). 1 minute (longer/permanent at higher levels).",
    },
    "Dispel Evil and Good": {
        "conc": True,
        "note": "Celestials/elementals/fey/fiends/undead have disadvantage on attack rolls "
                "against you. Action: Break Enchantment (end a charm/fear/possession from one "
                "of those creature types) or Dismissal (banish one, WIS save negates). 1 minute.",
    },
    "Eyebite": {
        "conc": True,
        "note": "Action each turn: target 1 new creature within 60 ft. (WIS save) with "
                "Asleep/Sickened/Panicked (your choice each time). 1 minute.",
    },
    "Friends": {
        "conc": True,
        "note": "Advantage on all CHA checks toward one chosen, non-hostile creature. It "
                "becomes hostile toward you when the spell ends (Enchantment cantrip; some "
                "classes are barred from casting it on themselves). 1 minute.",
    },
    "Druid Grove": {
        "conc": False,
        "note": "Wards a 30-90 ft. cube outdoor/underground area for 24 hours (or until "
                "dispelled, if recast in the same spot daily for a year) with a chosen "
                "combination of effects: difficult terrain, false trails, animated trees, "
                "hidden entrances, or a summoned spirit guardian.",
    },
    "Guards and Wards": {
        "conc": False,
        "note": "Wards up to 2,500 sq. ft. of floor space (24 hours) with a combination of "
                "fog, locked/webbed passages, a summoned spirit guardian, magically stuck "
                "doors, and a suggestion-based password effect.",
    },
    "Hallow": {
        "conc": False,
        "note": "Touch a point, infuse a 5-120 ft. radius (your choice): celestials/elementals/"
                "fey/fiends/undead can't enter or charm/frighten/possess creatures there, plus "
                "one chosen additional effect (e.g. courage, daylight, energy resistance, "
                "fear, silence, or tongues). Permanent until dispelled.",
    },
    "Mislead": {
        "conc": True,
        "note": "You're invisible (as Invisibility — ends if you attack or cast) while an "
                "illusory double appears in your place; you can move/speak/act through it and "
                "see/hear through it. 1 hour.",
    },
    "Resurrection": {
        "conc": False,
        "note": "Touch a creature dead ≤100 years (not old age, not undead): returns to life "
                "at full HP if its soul is free and willing. Cures normal disease/poison. "
                "Costs the caster to age by 1 year each time they cast it (this specific spell).",
    },
    "Sunbeam": {
        "conc": True,
        "note": "Action: 5x60-ft. line of radiant light. CON save or 6d8 radiant + blinded "
                "until your next turn (half damage, no blind on a success; undead/oozes have "
                "disadvantage). Can repeat as an action each turn until the spell ends. Also "
                "sheds sunlight in a 30-ft. radius. 1 minute.",
    },
    "Symbol": {
        "conc": False,
        "note": "Inscribes a hidden, triggered glyph (10-ft. surface or a concealable object) "
                "with a chosen effect (Death/Discord/Fear/Insanity/Pain/Sleep/Stunning, etc.) "
                "on creatures that trigger it. Permanent until triggered or dispelled.",
    },
    "Wish": {
        "conc": False,
        "note": "Duplicates any spell of 8th level or lower with no requirements, or one of a "
                "listed set of greater effects (7d8+ healing to up to 10 creatures, +1 weapon/"
                "armor item, restore a lost body part/life, negate one effect, undo a recent "
                "event, or create a truly novel effect at DM's discretion). 1d10 STR damage and "
                "unable to cast Wish again for 2d12 days if using it for anything beyond spell "
                "duplication.",
    },
    "Investiture of Wind": {
        "conc": True,
        "note": "Flying speed 60 ft. (hook applied automatically; you fall if still flying "
                "when the spell ends). Ranged attacks against you have disadvantage. Action: "
                "15-ft. cube within 60 ft., CON save or 2d10 bludgeoning + pushed 10 ft. "
                "(half damage, no push on success).",
    },
    "Shapechange": {
        "conc": True,
        "note": "Your game statistics are replaced by an average example of a creature you've "
                "seen (CR \u2264 your level, not a construct/undead) \u2014 keeping your alignment, "
                "INT/WIS/CHA, and languages. Retains full mechanical detail beyond this app's "
                "scope; consult the new form's own stat block.",
    },
    "Draconic Transformation": {
        "conc": False,
        "note": "Blindsight 30 ft., sees invisible creatures within range unless they "
                "successfully hide; flying speed 60 ft. (hooks applied automatically). "
                "Breath weapon on cast and as a bonus action on later turns: 60-ft. cone, "
                "DEX save or 6d8 force (half on success).",
    },
    "Shadow of Moil": {
        "conc": True,
        "note": "Heavily obscured to others; dim light within 10 ft. becomes darkness, bright "
                "light becomes dim. Resistance to radiant damage (hook applied automatically). "
                "A creature within 10 ft. that hits you with an attack takes 2d8 necrotic.",
    },
    "Primordial Ward": {
        "conc": False,
        "note": "Resistance to acid/cold/fire/lightning/thunder (hooks applied automatically). "
                "Reaction on taking one of those types: trade the resistances for immunity to "
                "that type (incl. the triggering hit) until the end of your next turn, then "
                "the spell ends.",
    },
    "Tasha's Otherworldly Guise: Lower Planes": {
        "conc": False, "ac": 2,
        "note": "Immune to fire/poison damage and the poisoned condition (hooks applied "
                "automatically). Flying speed 40 ft., +2 AC (hooks applied automatically). "
                "Weapon attacks count as magic and deal +2d6 damage of your choice (fire, "
                "poison, necrotic, or force) once per turn on a hit.",
    },
    "Tasha's Otherworldly Guise: Upper Planes": {
        "conc": False, "ac": 2,
        "note": "Immune to radiant/necrotic damage and the charmed condition (hooks applied "
                "automatically). Flying speed 40 ft., +2 AC (hooks applied automatically). "
                "Weapon attacks count as magic and deal +2d6 damage of your choice (radiant, "
                "necrotic, or force) once per turn on a hit.",
    },
    "Aid": {
        "note": "+5 current and maximum HP (8 hours). Apply manually to Max HP.",
    },
    "Guidance": {
        "conc": True,
        "note": "+1d4 to one ability check, then the effect ends.",
    },
    "Resistance": {
        "conc": True,
        "note": "+1d4 to one saving throw, then the effect ends.",
    },
    "Heroism": {
        "conc": True,
        "note": "Immune to frightened; gain caster's ability mod temp HP "
                "each turn start.",
    },
    "Protection from Evil and Good": {
        "conc": True,
        "note": "Aberrations/celestials/elementals/fey/fiends/undead have "
                "disadvantage to hit you; you can't be charmed/frightened/"
                "possessed by them.",
    },
    "Stoneskin": {
        "conc": True,
        "note": "Resistance to nonmagical bludgeoning, piercing, slashing.",
    },
    "Fly": {
        "conc": True,
        "note": "Flying speed 60 ft for the duration.",
    },
    "Mage Armor": {
        "note": "AC becomes 13 + DEX while unarmored. Applied automatically "
                "to your AC — doesn't stack with Unarmored Defense.",
    },
    "Hex": {
        "conc": True,
        "note": "Cursed target takes +1d6 necrotic from your attacks; "
                "disadvantage on chosen ability checks.",
    },
    "Hunter's Mark": {
        "conc": True,
        "note": "Marked target takes +1d6 from your weapon attacks.",
    },
    # Resistance-granting class-feature toggles. These have no AC/speed
    # hook of their own — get_innate_resistance_grants() in calculator.py
    # is what actually applies their damage resistance/immunity once the
    # matching class/subclass/level requirement is also met, so picking
    # one of these for a character who doesn't qualify is harmless (no
    # resistance gets added, it just sits in active_effects unused).
    "Umbral Form": {
        "note": "Sorcerer (Shadow Magic, 18th): resistance to all damage except force and radiant.",
    },
    "Spirit Projection": {
        "note": "Warlock (Undead, 10th): resistance to all damage except force and radiant.",
    },
    "Invincible Conqueror": {
        "note": "Paladin (Oath of Conquest, 20th): resistance to all damage.",
    },
    "Emissary of Redemption": {
        "note": "Paladin (Oath of Redemption, 20th): resistance to all damage from others' attacks/spells.",
    },
    "Starry Form": {
        "note": "Druid (Circle of Stars, 10th+): resistance to bludgeoning/piercing/slashing while in Starry Form.",
    },
    "Dragon Wings": {
        "note": "Sorcerer (Draconic Bloodline, 14th): bonus action, flying speed equal to your walking speed.",
    },
    "Elemental Gift": {
        "note": "Warlock (Genie, 6th): bonus action, flying speed of 30 ft for 10 minutes, plus resistance to your genie kind's damage type.",
    },
    "Warding Bond": {
        "note": "2nd-level spell (Cleric/Paladin, 1 hour, no concentration): while within 60 ft of the bonded creature, you both gain +1 AC and +1 to saving throws, and resistance to all damage. Whenever the target takes damage, you take the same amount.",
    },

    # ── Consumable potions ──────────────────────────────────────────────────
    # duration_category drives auto-clearing on rest (see _short_rest /
    # _long_rest in sheet.py): "short" = fades by/during a short rest
    # (roughly potions lasting an hour or less — a short rest is at least
    # that long per RAW), "long" = lasts longer than that but still fades
    # by the next long rest. Potions with no duration_category here are
    # either instantaneous (no lingering state to track) or have a duration
    # long/vague enough (Longevity, multi-day effects) that guessing a rest
    # boundary would be less honest than just not auto-clearing them.
    "Potion of Hill Giant Strength": {
        "ability_override": {"STR": 21}, "duration_category": "short",
        "note": "Your Strength score becomes 21 for 1 hour (no effect if already higher).",
    },
    "Potion of Fire Giant Strength": {
        "ability_override": {"STR": 25}, "duration_category": "short",
        "note": "Your Strength score becomes 25 for 1 hour (no effect if already higher).",
    },
    "Potion of Frost Giant Strength": {
        "ability_override": {"STR": 23}, "duration_category": "short",
        "note": "Your Strength score becomes 23 for 1 hour (no effect if already higher).",
    },
    "Potion of Stone Giant Strength": {
        "ability_override": {"STR": 23}, "duration_category": "short",
        "note": "Your Strength score becomes 23 for 1 hour (no effect if already higher).",
    },
    "Potion of Giant Strength (Cloud)": {
        "ability_override": {"STR": 27}, "duration_category": "short",
        "note": "Your Strength score becomes 27 for 1 hour (no effect if already higher).",
    },
    "Potion of Storm Giant Strength": {
        "ability_override": {"STR": 29}, "duration_category": "short",
        "note": "Your Strength score becomes 29 for 1 hour (no effect if already higher).",
    },
    "Potion of Acid Resistance": {"resistance": ["acid"], "duration_category": "short",
        "note": "Resistance to acid damage for 1 hour."},
    "Potion of Cold Resistance": {"resistance": ["cold"], "duration_category": "short",
        "note": "Resistance to cold damage for 1 hour."},
    "Potion of Fire Resistance": {"resistance": ["fire"], "duration_category": "short",
        "note": "Resistance to fire damage for 1 hour."},
    "Potion of Force Resistance": {"resistance": ["force"], "duration_category": "short",
        "note": "Resistance to force damage for 1 hour."},
    "Potion of Lightning Resistance": {"resistance": ["lightning"], "duration_category": "short",
        "note": "Resistance to lightning damage for 1 hour."},
    "Potion of Necrotic Resistance": {"resistance": ["necrotic"], "duration_category": "short",
        "note": "Resistance to necrotic damage for 1 hour."},
    "Potion of Poison Resistance": {"resistance": ["poison"], "duration_category": "short",
        "note": "Resistance to poison damage for 1 hour."},
    "Potion of Psychic Resistance": {"resistance": ["psychic"], "duration_category": "short",
        "note": "Resistance to psychic damage for 1 hour."},
    "Potion of Radiant Resistance": {"resistance": ["radiant"], "duration_category": "short",
        "note": "Resistance to radiant damage for 1 hour."},
    "Potion of Thunder Resistance": {"resistance": ["thunder"], "duration_category": "short",
        "note": "Resistance to thunder damage for 1 hour."},
    "Potion of Invulnerability": {
        "resistance": ["acid","bludgeoning","cold","fire","force","lightning","necrotic",
                       "piercing","poison","psychic","radiant","slashing","thunder"],
        "duration_category": "short",
        "note": "Resistance to all damage for 1 minute.",
    },
    "Potion of Speed": {
        "extra_action": True, "duration_category": "short",
        "note": "Effect of the haste spell for 1 minute (no concentration): +2 AC, double speed, "
                "advantage on DEX saves, +1 action (Attack ×1/Dash/Disengage/Hide/Use Object). "
                "Lethargy (no actions/movement) for 1 round when it ends.",
    },
    "Potion of Heroism": {
        "duration_category": "short",
        "note": "10 temporary hit points, plus the effect of bless (+1d4 to attack rolls and "
                "saving throws, no concentration) for 1 hour.",
    },
    "Potion of Invisibility": {
        "duration_category": "short",
        "note": "You (and anything you wear/carry) are invisible for 1 hour, or until you attack "
                "or cast a spell.",
    },
    "Potion of Advantage": {
        "duration_category": "short",
        "note": "Advantage on one ability check, attack roll, or saving throw of your choice, "
                "usable within the next hour.",
    },
    "Potion of Psionic Fortitude": {
        "duration_category": "short",
        "note": "Advantage on saving throws to avoid or end the charmed or stunned condition on "
                "yourself, for 1 hour.",
    },
    "Potion of Fire Breath": {
        "duration_category": "short",
        "note": "As a bonus action, exhale fire at a target within 30 ft: DC 13 DEX save, 4d6 fire "
                "damage (half on a success). Usable once; the effect ends 1 hour after drinking "
                "or once used.",
    },
    "Potion of Growth": {
        "duration_category": "short",
        "note": "Effect of enlarge (from enlarge/reduce) for 1d4 hours, no concentration: size up "
                "one category, +1d4 damage on Strength-based weapon hits, advantage on Strength "
                "checks/saves.",
    },
    "Potion of Diminution": {
        "duration_category": "short",
        "note": "Effect of reduce (from enlarge/reduce) for 1d4 hours, no concentration: size down "
                "one category, -1d4 damage on Strength-based weapon hits, disadvantage on "
                "Strength checks/saves.",
    },
    "Potion of Flying": {
        "duration_category": "short",
        "note": "Flying speed equal to your walking speed for 1 hour, and you can hover. Falling "
                "if airborne when it ends, unless you have another way to stay aloft.",
    },
    "Potion of Climbing": {
        "duration_category": "short",
        "note": "Climbing speed equal to your walking speed for 1 hour, plus advantage on "
                "Strength (Athletics) checks to climb.",
    },
    "Potion of Water Breathing": {
        "duration_category": "short",
        "note": "You can breathe underwater for 1 hour.",
    },
    "Potion of Gaseous Form": {
        "duration_category": "short",
        "note": "Effect of gaseous form for 1 hour, no concentration, or until ended early as a "
                "bonus action.",
    },
    "Potion of Mind Reading": {
        "duration_category": "short",
        "note": "Effect of detect thoughts (save DC 13).",
    },
    "Potion of Clairvoyance": {
        "duration_category": "short",
        "note": "Effect of clairvoyance.",
    },
    "Potion of Animal Friendship": {
        "duration_category": "short",
        "note": "Can cast animal friendship (save DC 13) at will for 1 hour.",
    },
    "Potion of Watchful Rest": {
        "duration_category": "long",
        "note": "For 8 hours: magic can't put you to sleep, and you can remain awake through a "
                "long rest and still gain its benefits.",
    },
    "Potion of Vitality": {
        "duration_category": "long",
        "note": "Removes exhaustion and cures disease/poison affecting you. For the next 24 "
                "hours, Hit Dice you spend restore the maximum possible instead of a roll.",
    },
    "Oil of Slipperiness": {
        "duration_category": "long",
        "note": "Applied over 10 minutes: effect of freedom of movement for 8 hours (or, poured "
                "on the ground, creates a 10-ft.-square patch of grease for 8 hours).",
    },
    "Oil of Etherealness": {
        "duration_category": "short",
        "note": "Applied over 10 minutes: effect of the etherealness spell for 1 hour.",
    },
    "Oil of Sharpness": {
        "duration_category": "short",
        "note": "Applied to a slashing/piercing weapon or up to 5 pieces of ammunition (1 minute): "
                "for 1 hour, the coated item is magical and has a +3 bonus to attack and damage rolls.",
    },
    "Philter of Love": {
        "duration_category": "short",
        "note": "The next creature you see within 10 minutes charms you for 1 hour.",
    },
    "Bottled Breath": {
        "duration_category": "short",
        "note": "Exhale for the effect of gust of wind, or hold your breath to not need to "
                "breathe for 1 hour (ends early if you speak or choose to end it).",
    },
    "Potion of Comprehension": {
        "duration_category": "short",
        "note": "Effect of the comprehend languages spell for 1 hour.",
    },
    "Potion of Polychromy": {
        "duration_category": "short",
        "note": "You and your gear take on a rainbow-hued appearance for 1 hour; bonus action to "
                "change colors, with advantage on Stealth checks while matching your surroundings.",
    },
    "Potion of Aqueous Form": {
        "duration_category": "short",
        "note": "Transform into a pool of water for 10 minutes (ends early if incapacitated or "
                "killed): swimming speed 30 ft., can move through liquids and occupy a creature's "
                "space, resistance to bludgeoning/piercing/slashing, can't attack or manipulate objects normally.",
    },
    "Potion of Maximum Power": {
        "duration_category": "short",
        "note": "The first damage-dealing spell of 4th level or lower you cast within 1 minute "
                "deals maximum damage on each die instead of rolling.",
    },
    "Potion of Mind Control": {
        "duration_category": "short",
        "note": "Cast Dominate Monster (no save) on a beast, humanoid, giant, or DM-chosen monster "
                "within 30 feet (type set randomly when the potion was found). Lasts 1 hour, no concentration required.",
    },
    "Potion of Mind Control (Beast)": {
        "duration_category": "short",
        "note": "Cast Dominate Monster (no save) on a beast within 30 feet. Lasts 1 hour, no concentration required.",
    },
    "Potion of Mind Control (Humanoid)": {
        "duration_category": "short",
        "note": "Cast Dominate Monster (no save) on a humanoid within 30 feet. Lasts 1 hour, no concentration required.",
    },
    "Potion of Mind Control (Monster)": {
        "duration_category": "short",
        "note": "Cast Dominate Monster (no save) on a monster within 30 feet. Lasts 1 hour, no concentration required.",
    },
    "Potion of Possibility": {
        "duration_category": "long",
        "note": "Grants two Fragments of Possibility (8 hours or until used): expend one when you "
                "make an attack roll, ability check, or saving throw to roll an extra d20 and use either result.",
    },
    "Potion of Dragon's Majesty": {
        "duration_category": "short",
        "note": "Transform into an adult dragon matching the potion's scale for 1 hour, using the "
                "dragon's statistics (your gear melds into the new form or falls, your choice).",
    },
    "Potion of Giant Size": {
        "ability_override": {"STR": 25},
        "duration_category": "long",
        "note": "If Medium or smaller, become Huge for 24 hours: Strength becomes 25 (if not "
                "already higher), hit point maximum and current hit points double, and melee reach increases by 5 feet.",
    },
}


EFFECT_TABLE["Scroll of the Comet"] = {
    "duration_category": "short",
    "note": "Reading the scroll (outdoors only, or it's wasted) calls down a comet at a point you can "
            "see up to 1 mile away: a 50-ft.-deep, 500-ft.-radius crater forms on impact. Every creature "
            "in that radius fails a DC 20 Dexterity save (30d10 force damage) or succeeds (half damage); "
            "all structures and unworn/unheld nonmagical objects in the crater are destroyed. One-shot "
            "effect -- clear it from the Effects tab once resolved.",
}


for _prot_type in ("Aberrations", "Beasts", "Celestials", "Elementals", "Fey", "Fiends", "Plants", "Undead"):
    EFFECT_TABLE[f"Scroll of Protection from {_prot_type}"] = {
        "duration_category": "short",
        "note": f"Reading the scroll (action) encloses you in an invisible 5-ft.-radius, 10-ft.-high "
                f"barrier for 5 minutes that prevents {_prot_type.lower()} from entering or affecting "
                f"anything within it. Moves with you; ends if you'd move it to enclose one of them. A "
                f"creature can overcome it with a successful DC 15 Charisma check (action).",
    }


EFFECT_TABLE["Scroll of Protection"] = {
    "duration_category": "short",
    "note": "Generic placeholder -- the real item is always one of the 8 creature-type-specific "
            "variants above (Aberrations/Beasts/Celestials/Elementals/Fey/Fiends/Plants/Undead), "
            "each with its own full barrier effect.",
}

EFFECT_TABLE["Nether Scroll of Azumar"] = {
    "duration_category": "long",
    "note": "Not consumable. Takes 30 days of 8-hr/day study, then a DC 25 Intelligence (Arcana) "
            "check (16d10 psychic damage and another 30 days to study on a failure). On success: "
            "Intelligence +2 (once, max 22) and permanent advantage on saving throws vs. spells and "
            "magical effects, plus a stone golem ally appears (turns to dust if you die). Its one-time "
            "ability-score boost parallels the DMG ability-score Manuals, but the summoned-ally "
            "component isn't tracked anywhere in this app -- clear this from the Effects tab once "
            "resolved, and apply the INT increase by hand via the Abilities tab.",
}

EFFECT_TABLE["Scroll of Tarrasque Summoning"] = {
    "duration_category": "short",
    "note": "Reading the scroll (action) summons the tarrasque in an unoccupied space you can see "
            "within 1 mile, hostile to all creatures but itself; it disappears at 0 hit points. This "
            "app has no monster/summon-tracking engine, so the tarrasque itself isn't modeled -- "
            "clear this from the Effects tab once resolved.",
}

for _lvl, _dc in ((1, 11), (2, 12), (3, 13), (4, 14), (5, 15), (6, 16), (7, 17), (8, 18), (9, 19)):
    _ord = {1: "1st", 2: "2nd", 3: "3rd"}.get(_lvl, f"{_lvl}th")
    EFFECT_TABLE[f"Spell Scroll ({_ord} level)"] = {
        "duration_category": "short",
        "note": f"Reading the scroll (action) casts the {_ord}-level spell it bears for free if it's "
                f"on your class's spell list; otherwise make an Intelligence (Arcana) check, DC {_dc} "
                f"-- a failure loses the spell with no other effect. Either way the scroll is destroyed "
                f"after use, and a spell cast this way uses the scroll's own save DC/attack bonus, not "
                f"yours. The specific spell is chosen per physical copy, which this app doesn't track "
                f"separately -- cast the actual spell from your own known/prepared list to model it, "
                f"then clear this from the Effects tab.",
    }
EFFECT_TABLE["Spell Scroll (Cantrip)"] = {
    "duration_category": "short",
    "note": "Reading the scroll (its own casting time) casts the cantrip it bears for free if it's on "
            "your class's spell list; otherwise the scroll is unintelligible. The scroll crumbles to "
            "dust once cast. The specific cantrip is chosen per physical copy, which this app doesn't "
            "track separately -- cast the actual cantrip from your own known list to model it, then "
            "clear this from the Effects tab.",
}


# Potions/oils with an instant, one-shot effect rather than a lingering
# active_effect -- healing, curing, or (for Potion of Poison) harming the
# drinker immediately. Applied directly to current_hp/conditions by
# sheet.py's _use_potion() instead of being added to active_effects, since
# there's no ongoing state to track or fade on a rest.
INSTANT_POTION_EFFECTS: dict[str, dict] = {
    "Potion of Healing": {"heal_dice": (2, 4, 2)},
    "Potion of Greater Healing": {"heal_dice": (4, 4, 4)},
    "Potion of Superior Healing": {"heal_dice": (8, 4, 8)},
    "Potion of Supreme Healing": {"heal_dice": (10, 4, 20)},
    "Elixir of Health": {
        "cure_conditions": ["Blinded", "Deafened", "Paralyzed", "Poisoned"],
        "cure_note": "Also cures any disease afflicting you.",
    },
    "Potion of Poison": {
        "damage_dice": (3, 6, 0), "damage_type": "poison", "add_condition": "Poisoned",
        "cure_note": "Looks/smells/tastes like a beneficial potion. DC 13 Constitution save or "
                      "remain poisoned, taking 3d6 poison damage at the start of each of your turns "
                      "until the condition ends (repeat the save at the end of each of your turns).",
    },
    "Blood of the Lycanthrope Antidote": {
        "cure_note": "Ends a lycanthropy curse, if drunk before your first full moon as a lycanthrope.",
    },
    "Mummy Rot Antidote": {
        "cure_note": "Neutralizes the Mummy Rot curse and restores your hit point maximum, if "
                      "administered within 24 hours of contracting it.",
    },
    "Thessaltoxin Antidote": {
        "cure_conditions": ["Poisoned"],
        "cure_note": "Neutralizes thessaltoxin poison.",
    },
    "Potion of Longevity": {
        "cure_note": "Physical age reduced by 1d6+6 years (minimum age 13). Each subsequent drink "
                      "has a cumulative 10% chance of instead aging you by 1d6+6 years. A roleplay/"
                      "narrative effect this app doesn't track a character age field for -- adjust by hand.",
    },
}


def effect_ac_bonus(char: dict) -> int:
    """Sum of flat AC modifiers from active effects."""
    total = 0
    heavy_armors = {"Plate", "Splint", "Ring Mail", "Chain Mail", "Half Plate"}
    medium_armors = {"Hide", "Chain Shirt", "Scale Mail", "Breastplate"}
    wearing_heavy = char.get("armor_worn") in heavy_armors
    for name in char.get("active_effects", []):
        e = EFFECT_TABLE.get(name, {})
        total += e.get("ac", 0)
        if "ac_no_heavy_armor" in e and not wearing_heavy:
            total += e["ac_no_heavy_armor"]
    # Bladesong (Wizard, Bladesinging, 2nd level): +INT modifier to AC
    # while lightly armored or unarmored. Variable per-character bonus,
    # so it can't live as a static EFFECT_TABLE value like most entries.
    if "Bladesong" in char.get("active_effects", []):
        wearing_medium_or_heavy = char.get("armor_worn") in (heavy_armors | medium_armors)
        if not wearing_medium_or_heavy:
            from dnd_app.core.calculator import ability_mod
            total += max(0, ability_mod(char, "INT"))
    # Dual Wielder: +1 AC while wielding a separate melee weapon in each
    # hand. Checks the character's actual equipped weapons (not just
    # "has the feat") for 2+ distinct melee weapons, neither Two-handed,
    # since a Two-handed weapon can't be one of a pair held one in each hand.
    if "Dual Wielder" in char.get("feats", []):
        from dnd_app.data.phbCommon.items import WEAPON_DICT
        melee_one_handed = []
        for wname in char.get("equipped_weapons", []):
            base_name = wname.split(" +")[0].strip()  # strip a magic "+1"/"+2" suffix
            w = WEAPON_DICT.get(base_name, {})
            if w.get("category","").endswith("Melee") and "Two-handed" not in w.get("properties", []):
                melee_one_handed.append(wname)
        if len(set(melee_one_handed)) >= 2:
            total += 1
    # Revenant Blade: +1 AC while holding a double-bladed scimitar with two hands.
    if "Revenant Blade" in char.get("feats", []):
        equipped = {w.split(" +")[0].strip() for w in char.get("equipped_weapons", [])}
        if "Double-Bladed Scimitar" in equipped:
            total += 1
    return total


def effect_ac_floor(char: dict) -> int:
    """Highest AC floor among active effects (0 = none)."""
    floor = 0
    for name in char.get("active_effects", []):
        floor = max(floor, EFFECT_TABLE.get(name, {}).get("ac_floor", 0))
    return floor


def effect_speed(char: dict, base: int) -> int:
    """Apply speed multipliers and flat bonuses from active effects."""
    speed = base
    for name in char.get("active_effects", []):
        e = EFFECT_TABLE.get(name, {})
        if "speed_mult" in e:
            speed = int(speed * e["speed_mult"])
        speed += e.get("speed_add", 0)
    return speed


def has_extra_action(char: dict) -> bool:
    """True if any active effect grants an additional action (Haste),
    or Action Surge was spent this turn. Action Surge is tracked as a
    separate, turn-scoped flag rather than an active_effect, since it's
    a one-time spend, not a duration effect."""
    return (char.get("_action_surge_used_this_turn", False)
            or any(EFFECT_TABLE.get(n, {}).get("extra_action")
                   for n in char.get("active_effects", [])))
