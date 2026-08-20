"""
Feature configuration registry.
Maps feature names → what choices/configuration they expose when clicked.

choice_type:
  "asi"         → pick ability scores (e.g. +1 to any two, or +2/+1)
  "expertise"   → pick N skills/tools for expertise
  "proficiency" → pick N skill/tool/language proficiencies
  "language"    → pick N languages
  "spell_grant" → automatically grants listed spells (shown in dialog, added to sheet)
  "spell_choose"→ pick N spells from a filtered list
  "damage_type" → pick an elemental/damage type
  "info"        → read-only expanded description only

Author: Ethan O'Brien
Date: 2026-08-20
"""

SKILLS = [
    "Acrobatics","Animal Handling","Arcana","Athletics","Deception","History",
    "Insight","Intimidation","Investigation","Medicine","Nature","Perception",
    "Performance","Persuasion","Religion","Sleight of Hand","Stealth","Survival",
]
TOOLS = ["Thieves' Tools","Disguise Kit","Forgery Kit","Herbalism Kit","Poisoner's Kit",
         "Alchemist's Supplies","Brewer's Supplies","Calligrapher's Supplies",
         "Carpenter's Tools","Cobbler's Tools","Cook's Utensils","Glassblower's Tools",
         "Jeweler's Tools","Leatherworker's Tools","Mason's Tools","Painter's Supplies",
         "Potter's Tools","Smith's Tools","Tinker's Tools","Weaver's Tools","Woodcarver's Tools",
         "Navigator's Tools","Vehicles (Land)","Vehicles (Water)","Gaming Set","Musical Instrument"]
LANGUAGES = [
    "Aarakocra", "Abanasinian", "Abyssal", "Alzhedo", "Blink Dog", "Bothii", "Bullywug",
    "Celestial", "Chessentan", "Chondathan", "Common", "Daelkyr", "Damaran", "Dambrathan",
    "Deep Crow", "Deep Speech", "Draconic", "Druidic", "Dwarvish", "Elvish", "Ergot",
    "Giant", "Giant Eagle", "Giant Elk", "Giant Owl", "Gith", "Gnoll", "Gnomish", "Goblin",
    "Grell", "Grung", "Guran", "Halfling", "Halruaan", "Hook Horror", "Ice Toad", "Illuskan",
    "Infernal", "Istarian", "Ixitxachitl", "Kenderspeak", "Kharolian", "Khur", "Kothian",
    "Kraul", "Kruthik", "Leonin", "Loross", "Loxodon", "Marquesian", "Merfolk", "Midani",
    "Minotaur", "Modron", "Mulhorandi", "Naush", "Nerakese", "Netherese", "Nordmaarian",
    "Ogre", "Olman", "Orc", "Otyugh", "Primordial", "Qualith", "Quori", "Rashemi", "Riedran",
    "Roushoum", "Sahuagin", "Shaaran", "Shou", "Slaad", "Solamnic", "Sphinx", "Sylvan",
    "Thayan", "Thieves' Cant", "Thri-kreen", "Tlincalli", "Troglodyte", "Tuigan", "Turmic",
    "Uluik", "Umber Hulk", "Undercommon", "Untheric", "Vedalken", "Vegepygmy", "Waelan",
    "Winter Wolf", "Worg", "Yeti", "Yikaria", "Zemnian"
]
ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]

FEATURE_CONFIG = {
    # ── Race / Species ───────────────────────────────────────────────────────
    "+1 to all six ability scores": {
        "choice_type": "info",
        "desc": "Human Variant: You gain +1 to each of your six ability scores (already applied via race ASI).",
    },
    "Ability Score Increase": {
        "choice_type": "asi",
        "desc": "Choose how to distribute your racial Ability Score Increases.",
        "points": 3,  # total points to distribute across any abilities
    },
    "Extra Language": {
        "choice_type": "language",
        "count": 1,
        "desc": "You can speak, read, and write one additional language of your choice.",
    },
    "Skill Versatility": {
        "choice_type": "proficiency",
        "count": 2,
        "pool": SKILLS,
        "desc": "You gain proficiency in two skills of your choice.",
    },
    "Feat": {
        "choice_type": "info",
        "desc": "You gain one feat of your choice. Add it in the Feats tab.",
    },
    "Natural Weapons": {
        "choice_type": "info",
        "desc": "Your unarmed strikes deal 1d6 bludgeoning/slashing damage and count as magical.",
    },
    "Draconic Ancestry – choose dragon type (acid/cold/fire/lightning/poison)": {
        "choice_type": "damage_type",
        "desc": "Choose your draconic ancestry. This determines your Breath Weapon damage type and the damage type you resist.",
        "options": ["Acid","Cold","Fire","Lightning","Poison"],
        "key": "draconic_ancestry",
    },
    "Breath Weapon – 2d6 damage, scales at 6th (3d6), 11th (4d6), 16th (5d6)": {
        "choice_type": "info",
        "desc": "As an action, exhale destructive energy (your draconic ancestry type). DEX save (DC = 8 + CON mod + proficiency). On a failed save, creatures take 2d6 damage (3d6 at 6th, 4d6 at 11th, 5d6 at 16th); half on success.",
    },
    "Darkvision 60 ft": {
        "choice_type": "info",
        "desc": "You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
    },
    "Darkvision 120 ft": {
        "choice_type": "info",
        "desc": "You can see in dim light within 120 feet of you as if it were bright light, and in darkness as if it were dim light.",
    },
    "Subrace": {
        "choice_type": "info",
        "desc": "Select your subrace in the Identity tab for additional traits.",
    },
    "Gnome Cunning – adv. on INT/WIS/CHA saving throws vs. magic": {
        "choice_type": "info",
        "desc": "You have advantage on all Intelligence, Wisdom, and Charisma saving throws against magic.",
    },
    "Fey Ancestry": {
        "choice_type": "info",
        "desc": "You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
    },
    "Lucky – reroll attack/ability/save 1s": {
        "choice_type": "info",
        "desc": "When you roll a 1 on a d20 for an attack roll, ability check, or saving throw, you can reroll and must use the new roll.",
    },

    # ── Class: Rogue ─────────────────────────────────────────────────────────
    "Expertise (2 skills or tools)": {
        "choice_type": "expertise",
        "count": 2,
        "pool": SKILLS + ["Thieves' Tools"],
        "desc": "Choose 2 skills or Thieves' Tools you are proficient with. Your proficiency bonus is doubled for those checks.",
        "key": "expertise_1",
    },
    "Expertise (2 more)": {
        "choice_type": "expertise",
        "count": 2,
        "pool": SKILLS + ["Thieves' Tools"],
        "desc": "Choose 2 more skills or Thieves' Tools to gain Expertise in.",
        "key": "expertise_2",
    },
    "Thieves' Cant": {
        "choice_type": "info",
        "desc": "You know Thieves' Cant, a secret mix of dialect, jargon, and code. You can convey and understand secret messages. It takes four times longer to convey a message this way.",
    },
    "Cunning Action (bonus: Dash/Disengage/Hide)": {
        "choice_type": "info",
        "desc": "On each of your turns, you can use a bonus action to take the Dash, Disengage, or Hide action.",
    },
    "Uncanny Dodge": {
        "choice_type": "info",
        "desc": "When an attacker you can see hits you with an attack, you can use your reaction to halve the attack's damage against you.",
    },
    "Evasion": {
        "choice_type": "info",
        "desc": "When you are subjected to an effect that allows you to make a Dexterity saving throw to take only half damage, you instead take no damage if you succeed on the saving throw, and only half damage if you fail.",
    },

    # ── Class: Fighter ───────────────────────────────────────────────────────
    "Fighting Style": {
        "choice_type": "proficiency",
        "count": 1,
        "pool": ["Archery (+2 ranged attack rolls)","Defense (+1 AC while armored)","Dueling (+2 melee damage one-handed)",
                 "Great Weapon Fighting (reroll 1s/2s on damage)","Protection (impose disadv on adjacent attack)",
                 "Two-Weapon Fighting (add ability mod to off-hand)","Blind Fighting (blindsight 10 ft)",
                 "Interception (reduce damage to ally by 1d10+prof)","Superior Technique (one Battle Master maneuver)",
                 "Thrown Weapon Fighting (+2 thrown damage)","Unarmed Fighting (1d6+STR unarmed or 1d8 grappling)"],
        "desc": "Choose a Fighting Style. You can't take the same Fighting Style option more than once, even if you later get to choose again.",
        "key": "fighting_style",
    },
    "Second Wind (1/SR)": {
        "choice_type": "info",
        "desc": "On your turn, you can use a bonus action to regain hit points equal to 1d10 + your fighter level. You must finish a short or long rest before you can use this feature again.",
    },
    "Action Surge (1/SR)": {
        "choice_type": "info",
        "desc": "On your turn, you can push yourself beyond your normal limits for a moment. This turn, you can take one additional action. Once you use this feature, you must finish a short or long rest before you can use it again (2/SR at level 17).",
    },
    "Extra Attack (2 attacks)": {
        "choice_type": "info",
        "desc": "When you take the Attack action on your turn, you can attack twice, instead of once.",
    },
    "Indomitable (1/LR)": {
        "choice_type": "info",
        "desc": "You can reroll a saving throw that you fail. You must use the new roll.",
    },

    # ── Class: Wizard ────────────────────────────────────────────────────────
    "Spellcasting (INT; spellbook with 6 spells)": {
        "choice_type": "spell_choose",
        "count": 6,
        "class_filter": "Wizard",
        "level_filter": [1],
        "desc": "You start with a spellbook containing 6 1st-level wizard spells of your choice. Add them in the Spells tab.",
        "key": "wizard_starting_spells",
    },
    "Arcane Recovery (1/LR; recover slots ≤ half level)": {
        "choice_type": "info",
        "desc": "Once per day when you finish a short rest, you can choose expended spell slots to recover. The spell slots can have a combined level equal to or less than half your wizard level (round up), and none of the slots can be 6th level or higher.",
    },

    # ── Class: Cleric ────────────────────────────────────────────────────────
    "Spellcasting (WIS)": {
        "choice_type": "info",
        "desc": "Spellcasting ability is Wisdom. You prepare spells from the full Cleric list each long rest (WIS mod + Cleric level spells). You can also cast your domain spells without preparation.",
    },
    "Channel Divinity (1/SR)": {
        "choice_type": "info",
        "desc": "You can channel divine energy to fuel magical effects. You start knowing Turn Undead plus the Channel Divinity option of your domain.",
    },
    "Divine Domain (Subclass) – grants bonus spells + feature": {
        "choice_type": "info",
        "desc": "Your cleric subclass (Divine Domain) grants you additional spells that are always prepared and don't count against your prepared spells total. Select your subclass in the Identity tab.",
    },
    "Destroy Undead (CR 1/2)": {
        "choice_type": "info",
        "desc": "When an undead fails its saving throw against your Turn Undead feature, the creature is instantly destroyed if its CR is at or below 1/2.",
    },
    "Divine Intervention": {
        "choice_type": "info",
        "desc": "You can call on your deity to intervene on your behalf. Roll percentile dice — if you roll a number equal to or lower than your cleric level, your deity intervenes.",
    },

    # ── Class: Druid ─────────────────────────────────────────────────────────
    "Wild Shape (CR 1/4, no fly/swim)": {
        "choice_type": "info",
        "desc": "As an action, you can magically assume the shape of a beast with CR 1/4 or lower (no flying or swimming speed). You can use this feature twice, regaining uses on a short or long rest. Maximum time equals half druid level in hours.",
    },
    "Timeless Body": {
        "choice_type": "info",
        "desc": "The primal magic that you wield causes you to age more slowly. For every 10 years that pass, your body ages only 1 year.",
    },
    "Beast Spells (cast while in Wild Shape)": {
        "choice_type": "info",
        "desc": "You can cast many of your druid spells in any shape you assume using Wild Shape. You can perform the somatic and verbal components of a druid spell while in a beast shape, but you aren't able to provide material components.",
    },

    # ── Class: Paladin ───────────────────────────────────────────────────────
    "Divine Sense": {
        "choice_type": "info",
        "desc": "As an action, you can open your awareness to detect such forces. Until the end of your next turn, you know the location of any celestial, fiend, or undead within 60 feet of you that is not behind total cover. You can use this feature (1 + CHA mod) times per long rest.",
    },
    "Lay on Hands (pool = paladin level × 5)": {
        "choice_type": "info",
        "desc": "You have a pool of healing power that replenishes each long rest. With a touch, you can heal a number of hit points up to your pool maximum (paladin level × 5). You can also expend 5 HP from the pool to cure one disease or neutralize one poison.",
    },
    "Spellcasting (CHA)": {
        "choice_type": "info",
        "desc": "Spellcasting ability is Charisma. You prepare spells from the Paladin spell list each long rest (CHA mod + half paladin level spells).",
    },
    "Divine Smite (expend spell slot for +2d8/slot level radiant, +1d8 vs undead/fiends)": {
        "choice_type": "info",
        "desc": "When you hit a creature with a melee weapon attack, you can expend one paladin spell slot to deal radiant damage to the target, in addition to the weapon's damage. The extra damage is 2d8 for a 1st-level spell slot, plus 1d8 for each spell level higher than 1st (maximum 5d8). The damage increases by 1d8 if the target is an undead or a fiend.",
    },
    "Aura of Protection (CHA mod to saves, 10 ft)": {
        "choice_type": "info",
        "desc": "When you or a friendly creature within 10 feet of you must make a saving throw, the creature gains a bonus to the saving throw equal to your Charisma modifier (min +1). You must be conscious to grant this bonus. At 18th level the range increases to 30 ft.",
    },

    # ── Class: Barbarian ─────────────────────────────────────────────────────
    "Rage (2/LR; +2 dmg; resist B/P/S)": {
        "choice_type": "info",
        "desc": "As a bonus action, you can enter a rage. While raging: advantage on STR checks/saves; +2 to damage with STR weapons; resistance to bludgeoning, piercing, and slashing. Rage ends early if unconscious or if you end your turn without attacking/taking damage. Uses: 2/LR (increases at higher levels).",
    },
    "Unarmored Defense (Barb)": {
        "choice_type": "info",
        "desc": "While not wearing armor, your Armor Class equals 10 + your Dexterity modifier + your Constitution modifier. You can use a shield and still gain this benefit.",
    },
    "Reckless Attack": {
        "choice_type": "info",
        "desc": "When you make your first attack on your turn, you can decide to attack recklessly. You have advantage on melee weapon attack rolls using STR during that turn, but attack rolls against you have advantage until your next turn.",
    },
    "Danger Sense": {
        "choice_type": "info",
        "desc": "You have advantage on DEX saving throws against effects you can see, unless you are blinded, deafened, or incapacitated.",
    },
    "Primal Path (Subclass)": {
        "choice_type": "info",
        "desc": "Choose your Primal Path subclass in the Identity tab. This grants you features at levels 3, 6, 10, and 14.",
    },
    "Extra Attack (2)": {
        "choice_type": "info",
        "desc": "You can attack twice when you take the Attack action.",
    },
    "Fast Movement (+10 ft)": {
        "choice_type": "info",
        "desc": "Your speed increases by 10 feet while you aren't wearing heavy armor.",
    },
    "Feral Instinct (adv initiative + act while surprised)": {
        "choice_type": "info",
        "desc": "You have advantage on initiative rolls. Additionally, if you are surprised at the beginning of combat and aren't incapacitated, you can act normally on your first turn, but only if you enter your rage before doing anything else.",
    },

    # ── Class: Bard ──────────────────────────────────────────────────────────
    "Bardic Inspiration (d6; CHA mod/LR)": {
        "choice_type": "info",
        "desc": "As a bonus action, choose one creature other than yourself within 60 feet who can hear you. That creature gains one Bardic Inspiration die (d6, scales to d8/d10/d12). It can add the die to one ability check, attack roll, or saving throw within 10 minutes.",
    },
    "Jack of All Trades (½ prof to non-proficient checks)": {
        "choice_type": "info",
        "desc": "You can add half your proficiency bonus, rounded down, to any ability check you make that doesn't already include your proficiency bonus.",
    },
    "Song of Rest (d6 HP during short rest)": {
        "choice_type": "info",
        "desc": "If you or any friendly creatures who can hear your performance regain hit points at the end of a short rest, each of those creatures regains an extra 1d6 HP (scales with bard level).",
    },
    "Expertise (2 skills)": {
        "choice_type": "expertise",
        "count": 2,
        "pool": SKILLS,
        "desc": "Choose 2 skills you are proficient with. Your proficiency bonus is doubled for those ability checks.",
        "key": "bard_expertise_1",
    },

    # ── Class: Monk ──────────────────────────────────────────────────────────
    "Martial Arts (d4 unarmed; DEX for monk weapons)": {
        "choice_type": "info",
        "desc": "You gain the following benefits with unarmed strikes and monk weapons: use DEX instead of STR; damage die is 1d4 (scales up); when you use the Attack action you can make one unarmed strike as a bonus action.",
    },
    "Unarmored Defense (Monk)": {
        "choice_type": "info",
        "desc": "While not wearing armor or a shield, your AC equals 10 + your DEX modifier + your WIS modifier.",
    },
    "Ki (ki points = monk level; DC = 8+prof+WIS)": {
        "choice_type": "info",
        "desc": "You have a pool of ki points equal to your monk level. You regain all ki on a short or long rest. Ki save DC = 8 + proficiency + WIS modifier. Spend ki for: Flurry of Blows (2 unarmed strikes; 2 ki), Patient Defense (Dodge; 1 ki), Step of the Wind (Disengage/Dash + long jump; 1 ki).",
    },
    "Unarmored Movement (+10 ft, +15 ft at 9)": {
        "choice_type": "info",
        "desc": "Your speed increases by 10 feet while you aren't wearing armor or wielding a shield. This bonus increases at higher levels.",
    },
    "Deflect Missiles (reduce by 1d10+DEX+monk level)": {
        "choice_type": "info",
        "desc": "You can use your reaction to deflect or catch the missile when you are hit by a ranged weapon attack. The damage is reduced by 1d10 + DEX mod + monk level. If reduced to 0, you can catch and throw it back as a ranged weapon attack.",
    },
    "Slow Fall (reduce by monk level × 5)": {
        "choice_type": "info",
        "desc": "You can use your reaction to reduce any falling damage you take by an amount equal to five times your monk level.",
    },
    "Extra Attack (2 attacks)": {
        "choice_type": "info",
        "desc": "You can attack twice when you take the Attack action on your turn.",
    },
    "Stunning Strike (1 ki; CON save or stunned)": {
        "choice_type": "info",
        "desc": "When you hit another creature with a melee weapon attack, you can spend 1 ki point to attempt a stunning strike. The target must succeed on a CON saving throw or be stunned until the end of your next turn.",
    },

    # ── Class: Warlock ───────────────────────────────────────────────────────
    "Eldritch Invocations (2 invocations)": {
        "choice_type": "info",
        "desc": "You gain 2 Eldritch Invocations from the list. Add your choices to your character notes. Invocations grant special abilities — consult your subclass and the PHB invocation list. You gain more at levels 5, 7, 9, 12, 15, 18.",
    },
    "Pact Boon": {
        "choice_type": "proficiency",
        "count": 1,
        "pool": ["Pact of the Blade (conjure melee weapon; proficient; use as spellcasting focus)",
                 "Pact of the Chain (find familiar; includes imps/pseudodragons/quasits/sprites)",
                 "Pact of the Tome (Book of Shadows: 3 cantrips from any class list)",
                 "Pact of the Talisman (amulet: +1d4 to a failed ability check, uses = proficiency bonus per long rest)"],
        "desc": "Choose your Pact Boon at 3rd level. This shapes how your patron's power manifests.",
        "key": "pact_boon",
    },
    "Mystic Arcanum (6th-level spell; 1/LR)": {
        "choice_type": "spell_choose",
        "count": 1,
        "class_filter": "Warlock",
        "level_filter": [6],
        "desc": "Choose one 6th-level warlock spell as your Mystic Arcanum. You can cast it once without expending a spell slot. Regained on long rest.",
        "key": "mystic_arcanum_6",
    },
    "Mystic Arcanum (7th-level spell; 1/LR)": {
        "choice_type": "spell_choose",
        "count": 1,
        "class_filter": "Warlock",
        "level_filter": [7],
        "desc": "Choose one 7th-level warlock spell as your Mystic Arcanum.",
        "key": "mystic_arcanum_7",
    },
    "Mystic Arcanum (8th-level spell; 1/LR)": {
        "choice_type": "spell_choose",
        "count": 1,
        "class_filter": "Warlock",
        "level_filter": [8],
        "desc": "Choose one 8th-level warlock spell as your Mystic Arcanum.",
        "key": "mystic_arcanum_8",
    },
    "Mystic Arcanum (9th-level spell; 1/LR)": {
        "choice_type": "spell_choose",
        "count": 1,
        "class_filter": "Warlock",
        "level_filter": [9],
        "desc": "Choose one 9th-level warlock spell as your Mystic Arcanum.",
        "key": "mystic_arcanum_9",
    },

    # ── Class: Sorcerer ──────────────────────────────────────────────────────
    "Sorcerous Origin (Subclass)": {
        "choice_type": "info",
        "desc": "Choose your Sorcerous Origin in the Identity tab. This grants you a feature at 1st level and again at levels 6, 14, and 18.",
    },
    "Font of Magic (sorcery points = sorcerer level)": {
        "choice_type": "info",
        "desc": "You have a pool of sorcery points equal to your sorcerer level. Flexible Casting: spend sorcery points to create spell slots (1 pt = 1st level, 2 = 2nd, 3 = 3rd, 4 = 4th, 5 = 5th) or convert slots to sorcery points. Regain on long rest.",
    },
    "Metamagic (choose 2)": {
        "choice_type": "proficiency",
        "count": 2,
        "pool": ["Careful Spell (up to CHA mod creatures auto-succeed save)",
                 "Distant Spell (double range, or touch→30 ft)",
                 "Empowered Spell (reroll up to CHA mod damage dice; 1 pt)",
                 "Extended Spell (double duration up to 24 hr; 1 pt)",
                 "Heightened Spell (one target disadv on save; 3 pts)",
                 "Quickened Spell (cast 1 action spell as bonus action; 2 pts)",
                 "Subtle Spell (no verbal or somatic components; 1 pt)",
                 "Twinned Spell (target single-target spell at second target; 1+spell level pts)",
                 "Seeking Spell (reroll missed attack; 2 pts)",
                 "Transmuted Spell (change damage type; 1 pt)"],
        "desc": "Choose 2 Metamagic options. You choose 2 more at levels 10 and 17.",
        "key": "metamagic",
    },

    # ── ASI / Feat ────────────────────────────────────────────────────────────
    "ASI / Feat": {
        "choice_type": "asi",
        "desc": "Increase one ability score by 2, or two ability scores by 1 each (max 20). Alternatively, take a feat from the Feats tab.",
        "options": ["Two scores +1 each", "+2 to one score", "Take a Feat instead"],
        "points": 2,
    },
    "ASI": {
        "choice_type": "asi",
        "desc": "Increase one ability score by 2, or two ability scores by 1 each (max 20).",
        "points": 2,
    },

    # ── Feats ─────────────────────────────────────────────────────────────────
    "Magic Initiate": {
        "choice_type": "spell_choose",
        "count": 3,
        "desc": "Choose a class. Learn 2 cantrips from it and 1 1st-level spell (cast 1/LR). The 2 cantrips should be level 0 and the spell level 1.",
        "class_filter": None,
        "level_filter": [0, 1],
        "key": "magic_initiate_spells",
    },
    "Spell Sniper": {
        "choice_type": "spell_choose",
        "count": 1,
        "desc": "Learn one cantrip that requires an attack roll from any class.",
        "class_filter": None,
        "level_filter": [0],
        "key": "spell_sniper_cantrip",
    },
    "Wood Elf Magic": {
        "choice_type": "spell_grant",
        "spells": ["Druidcraft", "Longstrider", "Pass without Trace"],
        "desc": "You learn Druidcraft (cantrip), Longstrider, and Pass without Trace. Longstrider and Pass Without Trace are each cast 1/LR (WIS-based).",
        "key": "wood_elf_magic_spells",
    },
    "Fey Touched": {
        "choice_type": "spell_grant_choose",
        "granted": ["Misty Step"],
        "choose_count": 1,
        "class_filter": None,
        "level_filter": [1],
        "school_filter": ["Divination", "Enchantment"],
        "desc": "You learn Misty Step plus one 1st-level Divination or Enchantment spell of your choice. Both can be cast 1/LR for free (or using a spell slot).",
        "key": "fey_touched_spells",
    },
    "Shadow Touched": {
        "choice_type": "spell_grant_choose",
        "granted": ["Invisibility"],
        "choose_count": 1,
        "class_filter": None,
        "level_filter": [1],
        "school_filter": ["Illusion", "Necromancy"],
        "desc": "You learn Invisibility plus one 1st-level Illusion or Necromancy spell. Both can be cast 1/LR for free (or using a spell slot).",
        "key": "shadow_touched_spells",
    },
    "Artificer Initiate": {
        "choice_type": "spell_grant_choose",
        "granted": [],
        "choose_count": 2,
        "class_filter": "Artificer",
        "level_filter": [0, 1],
        "desc": "Learn one Artificer cantrip (INT-based) and one 1st-level Artificer spell (cast 1/LR, INT-based).",
        "key": "artificer_initiate_spells",
    },
    "Elemental Adept": {
        "choice_type": "damage_type",
        "options": ["Acid","Cold","Fire","Lightning","Thunder"],
        "desc": "Choose one damage type: Acid, Cold, Fire, Lightning, or Thunder. Your spells ignore resistance to that type and treat 1s as 2s on damage dice.",
        "key": "elemental_adept_type",
    },
    "Resilient": {
        "choice_type": "proficiency",
        "count": 1,
        "pool": ["STR saves","DEX saves","CON saves","INT saves","WIS saves","CHA saves"],
        "desc": "Choose one ability score. You gain proficiency in saving throws using that ability.",
        "key": "resilient_save",
    },
    "Skilled": {
        "choice_type": "proficiency",
        "count": 3,
        "pool": SKILLS + TOOLS,
        "desc": "You gain proficiency in any combination of 3 skills or tools of your choice.",
        "key": "skilled_profs",
    },
    "Linguist": {
        "choice_type": "language",
        "count": 3,
        "desc": "You learn 3 languages of your choice.",
        "key": "linguist_languages",
    },
    "Prodigy": {
        "choice_type": "expertise",
        "count": 1,
        "pool": SKILLS + TOOLS,
        "desc": "You gain one skill proficiency, one tool proficiency, and one language. You also gain expertise in one skill you are proficient with.",
        "key": "prodigy_expertise",
    },
}

def get_feature_config(feature_name: str) -> dict | None:
    """Look up feature config by exact name or partial match."""
    if feature_name in FEATURE_CONFIG:
        return FEATURE_CONFIG[feature_name]
    # Try partial match for features that include parenthetical details
    for key, cfg in FEATURE_CONFIG.items():
        if key.lower() in feature_name.lower() or feature_name.lower() in key.lower():
            return cfg
    return None

SPELLS_GRANTED_BY_FEAT = {
    "Wood Elf Magic": ["Druidcraft","Longstrider","Pass without Trace"],
    "Fey Touched": ["Misty Step"],
    "Shadow Touched": ["Invisibility"],
}

FEATURE_CONFIG.update({
    "Animal Enhancement at 1st level": {
        "choice_type": "proficiency",
        "count": 1,
        "pool": ["Manta Glide (slow falls: subtract 100 ft from fall damage calc, glide 2 ft horizontal per 1 ft descended)",
                 "Nimble Climber (climbing speed = walking speed)",
                 "Underwater Adaptation (breathe air and water, swim speed = walking speed)"],
        "desc": "Choose one Animal Enhancement at character creation.",
        "key": "simic_enhancement_1st",
    },
    "Additional Animal Enhancement at 5th level": {
        "choice_type": "proficiency",
        "count": 1,
        "pool": ["Grappling Appendages (2 appendages, each a natural weapon: 1d6+STR bludgeoning on an unarmed strike, then try to grapple as a bonus action)",
                 "Carapace (+1 AC when not wearing heavy armor)",
                 "Acid Spit (action: one target within 30 ft, DEX save vs DC 8+PB+CON mod, 2d10 acid damage on a fail — 3d10 at 11th, 4d10 at 17th; uses = CON mod per long rest)"],
        "desc": "Choose another Animal Enhancement at 5th level (or repeat a 1st-level option, DM permitting).",
        "key": "simic_enhancement_5th",
    },
})
