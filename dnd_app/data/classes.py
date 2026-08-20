"""
Classes data module.

D&D 5e class data: all 14 classes with full feature tables,
subclasses, resource trackers (ki, lay on hands, rage, etc.), spell
slot tables, and level-up choice definitions. Consumed by
dnd_app.core.builder/calculator and the level-up UI.

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ── Shared constants ──────────────────────────────────────────────────────────
SKILLS = ['Acrobatics','Animal Handling','Arcana','Athletics','Deception',
          'History','Insight','Intimidation','Investigation','Medicine',
          'Nature','Perception','Performance','Persuasion','Religion',
          'Sleight of Hand','Stealth','Survival']

FIGHTING_STYLES = [
    'Archery – +2 bonus to ranged attack rolls',
    'Blind Fighting – Blindsight 10 ft',
    'Defense – +1 AC while wearing armor',
    'Dueling – +2 damage with one-handed weapon (no other melee)',
    'Great Weapon Fighting – reroll 1s and 2s on two-handed weapon damage',
    'Interception – reaction: reduce damage to nearby ally by 1d10+Prof',
    'Protection – reaction: impose disadvantage on attack vs. nearby ally',
    'Superior Technique – 1 Battle Master maneuver + 1 superiority die (d6)',
    'Thrown Weapon Fighting – +2 damage with thrown weapons; draw as part of throw',
    'Two-Weapon Fighting – add ability mod to off-hand damage',
    'Unarmed Fighting – unarmed 1d6+STR (1d8 if no weapon); grappled = 1d4/turn',
]

METAMAGIC = [
    'Careful Spell – up to CHA creatures auto-succeed saves',
    'Distant Spell – double range (touch = 30 ft)',
    'Empowered Spell – reroll up to CHA damage dice',
    'Extended Spell – double duration (max 24 hr)',
    'Heightened Spell – 1 creature disadv on first save',
    'Quickened Spell – cast as bonus action',
    'Seeking Spell – miss → treat as automatic hit',
    'Subtle Spell – no verbal/somatic components',
    'Transmuted Spell – swap damage type among acid/cold/fire/lightning/poison/thunder',
    'Twinned Spell – target 2 creatures instead of 1',
]

ELDRITCH_INVOCATIONS = [
    'Agonizing Blast (prereq: Eldritch Blast) – add CHA mod to Eldritch Blast damage',
    'Armor of Shadows – Mage Armor at will',
    'Ascendant Step (9th) – Levitate at will',
    'Aspect of the Moon (Pact of the Tome) – no longer need to sleep',
    'Beast Speech – Speak with Animals at will',
    'Beguiling Influence – Deception + Persuasion proficiency',
    'Bond of the Talisman (12th, Pact of the Talisman) – action: teleport to/from talisman wearer, PB times/LR',
    'Cloak of Flies (5th) – bonus action aura: adv. Intimidation, disadv. other CHA checks, poison damage to others in it (1/SR/LR)',
    'Gift of the Depths (5th) – swim speed = walk speed, breathe water; cast Water Breathing 1/LR',
    'Gift of the Protectors (9th, Pact of the Tome) – named creatures drop to 1 HP instead of 0, once per LR',
    'Maddening Hex (5th, hex/curse feature) – bonus action: CHA mod psychic to hexed target + nearby creatures',
    'Protection of the Talisman (7th, Pact of the Talisman) – talisman wearer adds d4 to failed saves, PB times/LR',
    'Rebuke of the Talisman (Pact of the Talisman) – reaction: PB psychic damage + push 10ft when talisman wearer is hit',
    'Shroud of Shadow (15th) – Invisibility at will',
    'Thief of Five Fates – cast Bane once using a warlock spell slot, 1/LR',
    'Bewitching Whispers (7th) – Compulsion 1/LR',
    'Book of Ancient Secrets (Pact of the Tome) – ritual casting',
    'Chains of Carceri (15th, Great Old One/Fiend) – Hold Monster 1/LR',
    'Devil\'s Sight – Darkvision 120 ft in magical darkness',
    'Dreadful Word (7th) – Confusion 1/LR',
    'Eldritch Mind – adv. on Concentration checks',
    'Eldritch Sight – Detect Magic at will',
    'Eldritch Smite (5th, Pact of the Blade) – expend slot: +1d8/slot level force, knock prone',
    'Eldritch Spear (prereq: Eldritch Blast) – EB range 300 ft',
    'Eyes of the Rune Keeper – read all writing',
    'Far Scribe (5th, Pact of the Tome) – send/receive messages via Sending',
    'Fiendish Vigor – False Life at will',
    'Gaze of Two Minds – see/hear through willing creature',
    'Ghostly Gaze (7th) – see 30 ft through solid objects 1 min/LR',
    'Gift of the Ever-Living Ones (Pact of the Chain) – max healing dice',
    'Grasp of Hadar (prereq: Eldritch Blast) – pull EB target 10 ft',
    'Improved Pact Weapon (Pact of the Blade) – +1 weapon, use as focus',
    'Investment of the Chain Master (Pact of the Chain) – improve familiar',
    'Lance of Lethargy (prereq: Eldritch Blast) – reduce EB target speed 10 ft',
    'Lifedrinker (12th, Pact of the Blade) – +CHA necrotic on pact weapon attacks',
    'Mask of Many Faces – Disguise Self at will',
    'Master of Myriad Forms (15th) – Alter Self at will',
    'Minions of Chaos (9th) – Conjure Elemental 1/LR',
    'Mire the Mind (5th) – Slow 1/LR',
    'Misty Visions – Silent Image at will',
    'One with Shadows (5th) – invisible in dim/dark when standing still',
    'Otherworldly Leap (9th) – Jump at will',
    'Pact of the Blade – summon pact weapon',
    'Pact of the Chain – Find Familiar (special forms)',
    'Pact of the Tome – Book of Shadows + 3 cantrips',
    'Pact of the Talisman – talisman; add d4 to checks 1/LR per short rest charges',
    'Relentless Hex (7th) – teleport to Hexed target',
    'Repelling Blast (prereq: Eldritch Blast) – push EB target 10 ft',
    'Sculptor of Flesh (7th) – Polymorph 1/LR',
    'Sign of Ill Omen (5th) – Bestow Curse 1/LR',
    'Thirsting Blade (5th, Pact of the Blade) – extra attack',
    'Tomb of Levistus (5th) – reaction: encase yourself in ice',
    'Trickster\'s Escape (7th) – Freedom of Movement 1/LR',
    'Undying Servitude (Undead patron) – animate dead 1/LR',
    'Visions of Distant Realms (15th) – Arcane Eye at will',
    'Voice of the Chain Master (Pact of the Chain) – see/speak through familiar',
    'Whispers of the Grave (9th) – Speak with Dead at will',
    'Witch Sight (15th) – see true form of shapechangers/illusions',
]

# Blood Hunter's Blood Curses. Base curses have no prerequisite; four are
# gated behind a specific Order at a specific level (Corrosion/Mutant,
# Exorcist/Ghostslayer, Howl/Lycan, Soul Eater/Profane Soul — all filtered
# by the chooser so they only appear once actually eligible).
BLOOD_CURSES = [
    "Blood Curse of the Anxious – bonus action: cursed creature within 30 ft "
    "gives CHA (Intimidation) checks against it advantage until end of your "
    "next turn. Amplify: its next WIS save before the curse ends has disadvantage.",

    "Blood Curse of Binding – bonus action: a Large or smaller creature within "
    "30 ft makes a STR save or has speed 0 and can't use reactions until end "
    "of your next turn. Amplify: lasts 1 minute, any size, repeats the save "
    "each turn to end early.",

    "Blood Curse of Bloated Agony – bonus action: cursed creature within 30 ft "
    "has disadvantage on STR and DEX checks until end of your next turn, and "
    "takes 1d8 necrotic damage if it makes more than one attack on its turn. "
    "Amplify: lasts 1 minute, CON save each turn to end early.",

    "Blood Curse of Corrosion (prereq: 15th level, Order of the Mutant) – "
    "bonus action: poison a creature within 30 ft; CON save each turn ends "
    "it. Amplify: 4d6 necrotic damage when cast, and again each failed save.",

    "Blood Curse of the Exorcist (prereq: 15th level, Order of the Ghostslayer) "
    "– bonus action: end charmed, frightened, or possession on a creature "
    "within 30 ft. Amplify: whatever charmed/frightened/possessed it takes "
    "3d6 psychic damage and must succeed a WIS save or be stunned until end "
    "of your next turn.",

    "Blood Curse of Exposure – reaction when a creature within 30 ft takes "
    "damage: it loses resistance to that damage type until end of its next "
    "turn. Amplify: removes invulnerability instead, replacing it with "
    "resistance until end of its next turn.",

    "Blood Curse of the Eyeless – reaction when a creature within 30 ft "
    "attacks: subtract one Hemocraft die from its attack roll (before hit/miss "
    "is determined). No effect on creatures immune to blinded. Amplify: "
    "applies to all of that creature's attacks until the end of its turn.",

    "Blood Curse of the Fallen Puppet – reaction when a creature within 30 ft "
    "drops to 0 HP: it makes one weapon attack against a target of your "
    "choice within its range. Amplify: it can first move up to half its "
    "speed, and gains your Hemocraft modifier (min +1) on the attack roll.",

    "Blood Curse of the Howl (prereq: 18th level, Order of the Lycan) – "
    "action: each creature within 30 ft that can hear you makes a WIS save "
    "or is frightened until end of your next turn (stunned too if failed by "
    "5+); success grants 24h immunity. You can exempt any creatures you "
    "choose. Amplify: range becomes 60 ft.",

    "Blood Curse of the Marked – bonus action: mark a creature within 30 ft; "
    "until end of your turn, hits against it with a weapon under an active "
    "Crimson Rite roll one extra Hemocraft die. Amplify: your next attack "
    "against it this turn has advantage.",

    "Blood Curse of the Muddled Mind – bonus action: a concentrating creature "
    "within 30 ft has disadvantage on its next Concentration save before end "
    "of your next turn. Amplify: disadvantage on ALL Concentration saves "
    "until end of your next turn.",

    "Blood Curse of the Soul Eater (prereq: 18th level, Order of the Profane "
    "Soul) – reaction when a non-construct, non-undead creature within 30 ft "
    "drops to 0 HP: until end of your next turn you attack with advantage "
    "and have resistance to all damage. Amplify: also regain one expended "
    "warlock spell slot; once per long rest.",
]

# Blood Hunter's Mutagens (Order of the Mutant). Format matches
# BLOOD_CURSES: each string embeds the full effect + downside so it
# renders with real content, not just a name. A few scale their bonus at
# 11th/15th level (noted inline) or require a minimum level to consume at
# all (Aether, Cruelty, Precision — 11th; Reconstruction — 7th).
MUTAGENS = [
    "Aether (prereq: 11th level) – flying speed 20 ft for 1 hour; disadvantage on STR and DEX checks during that time.",

    "Alluring – advantage on CHA checks; disadvantage on initiative rolls.",

    "Celerity – DEX score and maximum increase by 3 (4 at 11th level, 5 at "
    "18th); disadvantage on WIS saving throws.",

    "Conversant – advantage on INT checks; disadvantage on WIS checks.",

    "Cruelty (prereq: 11th level) – when you use the Attack action, make one "
    "additional weapon attack as a bonus action; disadvantage on INT, WIS, "
    "and CHA saving throws.",

    "Deftness – advantage on DEX checks; disadvantage on WIS checks.",

    "Embers – resistance to fire damage; vulnerability to cold damage.",

    "Gelid – resistance to cold damage; vulnerability to fire damage.",

    "Impermeable – resistance to piercing damage; vulnerability to slashing "
    "damage.",

    "Mobility – immunity to the grappled and restrained conditions (also "
    "immune to paralyzed at 11th level); disadvantage on STR checks.",

    "Nighteye – darkvision 60 ft (or +60 ft if you already have it); "
    "disadvantage on attack rolls and WIS (Perception) checks that rely on "
    "sight when you, your target, or what you're perceiving is in direct "
    "sunlight.",

    "Percipient – advantage on WIS checks; disadvantage on CHA checks.",

    "Potency – STR score and maximum increase by 3 (4 at 11th level, 5 at "
    "18th); disadvantage on DEX saving throws.",

    "Precision (prereq: 11th level) – your weapon attacks score a critical "
    "hit on a roll of 19 or 20; disadvantage on STR saving throws.",

    "Rapidity – speed increases by 10 ft (+5 more at 15th level); "
    "disadvantage on INT checks.",

    "Reconstruction (prereq: 7th level) – for 1 hour, regain HP equal to "
    "your proficiency bonus at the start of each turn while below half HP "
    "(and above 0); your speed is reduced by 10 ft during that time.",

    "Sagacity – INT score and maximum increase by 3 (4 at 11th level, 5 at "
    "18th); disadvantage on CHA saving throws.",

    "Shielded – resistance to slashing damage; vulnerability to bludgeoning "
    "damage.",

    "Unbreakable – resistance to bludgeoning damage; vulnerability to "
    "piercing damage.",

    "Vermillion – gain an additional use of Blood Maledict; disadvantage on "
    "death saving throws.",
]

BATTLE_MASTER_MANEUVERS = [
    'Ambush – add SD to Initiative or Stealth',
    'Bait and Switch – swap places, ally or self gets +SD AC until next turn',
    'Brace – when enemy enters reach: OA + add SD to damage',
    'Commander\'s Strike – direct ally to attack (uses their reaction)',
    'Commanding Presence – add SD to Persuasion/Performance/Intimidation',
    'Disarming Attack – add SD to damage; target drops item (STR save)',
    'Distracting Strike – add SD to damage; next attacker has adv.',
    'Evasive Footwork – add SD to AC when moving',
    'Feinting Attack – feint (bonus): adv. on next attack + add SD to damage',
    'Goading Attack – add SD to damage; target disadv. vs others (WIS save)',
    'Grappling Strike – attempt grapple as bonus action after hitting; add SD to the Strength (Athletics) check (not to damage)',
    'Lunging Attack – +5 ft reach; add SD to damage',
    'Maneuvering Attack – add SD to damage; ally can move half speed without OA',
    'Menacing Attack – add SD to damage; target frightened (WIS save)',
    'Parry – reaction: reduce damage taken by SD+DEX',
    'Precision Attack – add SD to attack roll',
    'Pushing Attack – add SD to damage; push 15 ft (STR save)',
    'Quick Toss – bonus action: ranged attack with any thrown weapon (draw it as part of the attack) + add SD to damage',
    'Rally – bonus action: ally gains SD+CHA temp HP',
    'Riposte – reaction when missed: attack + add SD to damage',
    'Sweeping Attack – on hit, a second creature within 5 ft of the target takes SD damage of the same type as the original attack',
    'Tactical Assessment – add SD to Investigation/History/Insight',
    'Trip Attack – add SD to damage; target falls prone (STR save)',
]

TOTEM_SPIRITS = ['Bear','Eagle','Elk','Tiger','Wolf']
DIVINE_DOMAINS = [
    'Arcana Domain (SCAG)','Death Domain','Forge Domain (XGE)','Grave Domain (XGE)',
    'Knowledge Domain','Life Domain','Light Domain','Nature Domain',
    'Order Domain (GGR/TCE)','Peace Domain (TCE)','Trickery Domain',
    'Twilight Domain (TCE)','War Domain',
    'Ambition Domain (Amonkhet)','Solidarity Domain (Amonkhet)',
    'Strength Domain (Amonkhet)','Zeal Domain (Amonkhet)',
]
CIRCLE_OF_LAND_TERRAINS = [
    'Arctic','Coast','Desert','Forest','Grassland','Mountain','Swamp','Underdark',
]
DRAGONBORN_ANCESTRIES = [
    'Black (acid)', 'Blue (lightning)', 'Brass (fire)', 'Bronze (lightning)',
    'Copper (acid)', 'Gold (fire)', 'Green (poison)', 'Red (fire)',
    'Silver (cold)', 'White (cold)',
]
WARLOCK_PACT_SLOTS = {1:1,2:2,3:2,4:2,5:3,6:3,7:4,8:4,9:5,10:5,
                      11:5,12:5,13:5,14:5,15:5,16:5,17:5,18:5,19:5,20:5}
WARLOCK_PACT_LEVEL = {1:1,2:1,3:2,4:2,5:3,6:3,7:4,8:4,9:5,10:5,
                      11:5,12:5,13:5,14:5,15:5,16:5,17:5,18:5,19:5,20:5}

# ── Spell slot tables (per class, per level) ──────────────────────────────────
def _ss(*slots):
    """Pad to 9 spell levels."""
    return list(slots) + [0] * (9 - len(slots))

FULL_CASTER_SLOTS = [
    _ss(2),_ss(3),_ss(4,2),_ss(4,3),_ss(4,3,2),_ss(4,3,3),
    _ss(4,3,3,1),_ss(4,3,3,2),_ss(4,3,3,3,1),_ss(4,3,3,3,2),
    _ss(4,3,3,3,2,1),_ss(4,3,3,3,2,1),_ss(4,3,3,3,2,1,1),
    _ss(4,3,3,3,2,1,1),_ss(4,3,3,3,2,1,1,1),_ss(4,3,3,3,2,1,1,1),
    _ss(4,3,3,3,2,1,1,1,1),_ss(4,3,3,3,3,1,1,1,1),
    _ss(4,3,3,3,3,2,1,1,1),_ss(4,3,3,3,3,2,2,1,1),
]

HALF_CASTER_SLOTS = [
    _ss(),_ss(2),_ss(3),_ss(3),_ss(4,2),_ss(4,2),
    _ss(4,3),_ss(4,3),_ss(4,3,2),_ss(4,3,2),
    _ss(4,3,3),_ss(4,3,3),_ss(4,3,3,1),_ss(4,3,3,1),
    _ss(4,3,3,2),_ss(4,3,3,2),_ss(4,3,3,3,1),_ss(4,3,3,3,1),
    _ss(4,3,3,3,2),_ss(4,3,3,3,2),
]

THIRD_CASTER_SLOTS = [
    _ss(),_ss(),_ss(2),_ss(3),_ss(3),_ss(3),
    _ss(4,2),_ss(4,2),_ss(4,2),_ss(4,3),
    _ss(4,3),_ss(4,3),_ss(4,3,2),_ss(4,3,2),
    _ss(4,3,2),_ss(4,3,3),_ss(4,3,3),_ss(4,3,3),
    _ss(4,3,3,1),_ss(4,3,3,1),
]

ARTIFICER_SLOTS = [
    _ss(2),_ss(2),_ss(3),_ss(3),_ss(4,2),_ss(4,2),
    _ss(4,3),_ss(4,3),_ss(4,3,2),_ss(4,3,2),
    _ss(4,3,3),_ss(4,3,3),_ss(4,3,3,1),_ss(4,3,3,1),
    _ss(4,3,3,2),_ss(4,3,3,2),_ss(4,3,3,3,1),_ss(4,3,3,3,1),
    _ss(4,3,3,3,2),_ss(4,3,3,3,2),
]

# ── Class definitions ─────────────────────────────────────────────────────────
def cls(name, hit_die, save_profs, armor, weapons, tools,
        skill_choices, skill_count, spell_ability, has_spells,
        spell_slots, subclass_level, features, subclasses,
        resources=None, level_choices=None, multiclass_reqs=None):
    return dict(
        name=name, hit_die=hit_die, save_profs=save_profs,
        armor=armor, weapons=weapons, tools=tools,
        skill_choices=skill_choices, skill_count=skill_count,
        spell_ability=spell_ability, has_spells=has_spells,
        spell_slots=spell_slots,
        subclass_level=subclass_level, features=features,
        subclasses=subclasses, resources=resources or [],
        level_choices=level_choices or {},
        multiclass_reqs=multiclass_reqs or {},
    )


ALL_CLASSES = [

    # ── Artificer ──────────────────────────────────────────────────────────────
    cls("Artificer", 8,
        save_profs=["CON","INT"],
        armor="Light, Medium, Shields",
        weapons="Simple weapons",
        tools="Thieves' tools, Tinker's tools, one Artisan's tool of choice",
        skill_choices=["Arcana","History","Investigation","Medicine","Nature","Perception","Sleight of Hand"],
        skill_count=2, spell_ability="INT", has_spells=True,
        spell_slots=ARTIFICER_SLOTS, subclass_level=3,
        features={
            1: ["Magical Tinkering","Spellcasting"],
            2: ["Infuse Item (4 infusions known, 2 infused items)"],
            3: ["The Right Tool for the Job","Subclass Feature","Subclass Feature"],
            4: ["ASI / Feat"],
            5: ["Arcane Armament (Extra Attack for armed Artificers)","Subclass Feature"],
            6: ["Tool Expertise (expertise in tool profs)","Subclass Feature","Infuse Item (6 known, 3 infused)"],
            7: ["Flash of Genius (reaction: add INT mod to save or check)"],
            8: ["ASI / Feat"],
            9: ["Subclass Feature"],
            10: ["Magic Item Adept (attune 4 items; craft uncommon in 1 week)","Infuse Item (8 known, 4 infused)"],
            11: ["Spell-Storing Item","Subclass Feature"],
            12: ["ASI / Feat"],
            14: ["Magic Item Savant (attune 5 items, ignore reqs)","Subclass Feature","Infuse Item (10 known, 5 infused)"],
            15: [],
            16: ["ASI / Feat"],
            18: ["Magic Item Master (attune 6 items)","Infuse Item (12 known, 6 infused)"],
            19: ["ASI / Feat"],
            20: ["Soul of Artifice (+1 to all saves per attuned item)"],
        },
        subclasses=["Alchemist","Armorer","Artillerist","Battle Smith"],
        resources=[
            dict(name="Infused Items", key="infused_items", formula="infuse_by_level",
                 reset="LR", track="current_max",
                 by_level={2:2,6:3,10:4,14:5,18:6}),
        ],
        level_choices={
            2: ["Choose Infusions (start with 4 known; +2 at 6th/10th/14th/18th level)"],
            3: ["Choose Subclass"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"INT": 13},
    ),

    # ── Barbarian ─────────────────────────────────────────────────────────────
    cls("Barbarian", 12,
        save_profs=["STR","CON"],
        armor="Light, Medium, Shields",
        weapons="Simple weapons, Martial weapons",
        tools="None",
        skill_choices=["Animal Handling","Athletics","Intimidation","Nature","Perception","Survival"],
        skill_count=2, spell_ability=None, has_spells=False,
        spell_slots=None, subclass_level=3,
        features={
            1: ["Rage (2/LR, +2 damage, resist B/P/S)","Unarmored Defense (10+DEX+CON)"],
            2: ["Reckless Attack","Danger Sense (adv. DEX saves vs. things you can see)"],
            3: ["Primal Path (Subclass)","Primal Knowledge (1 extra skill)","Path Feature"],
            4: ["ASI / Feat"],
            5: ["Extra Attack","Fast Movement (+10 ft, no heavy armor)"],
            6: ["Path Feature","Rage (3/LR)"],
            7: ["Feral Instinct (adv. Initiative; enter rage if surprised)","Instinctive Pounce"],
            8: ["ASI / Feat"],
            9: ["Brutal Critical (+1 die on melee crit)"],
            10: ["Path Feature","Primal Knowledge (1 more skill)"],
            11: ["Relentless Rage (DC 10+5/use CON to stay at 1 HP)"],
            12: ["ASI / Feat","Rage (4/LR)"],
            13: ["Brutal Critical (+2 dice)"],
            14: ["Path Feature"],
            15: ["Persistent Rage (rage doesn't end early)"],
            16: ["ASI / Feat","Rage (5/LR)"],
            17: ["Brutal Critical (+3 dice)"],
            18: ["Indomitable Might (STR check min = STR score)"],
            19: ["ASI / Feat"],
            20: ["Primal Champion (+4 STR, +4 CON)","Rage unlimited"],
        },
        subclasses=[
            "Path of the Ancestral Guardian (XGE) – rage summons ancestral spirits",
            "Path of the Battlerager (SCAG) – spiked armor fighter (Dwarf only)",
            "Path of the Beast (TCE) – natural weapons from bestial spirit",
            "Path of the Berserker – frenzied rage for extra attack",
            "Path of the Giant (BGG) – giant's strength and size",
            "Path of the Storm Herald (XGE) – rage creates elemental aura",
            "Path of the Totem Warrior – spirit animal powers",
            "Path of the Wild Magic (TCE) – chaotic magical surges on rage",
            "Path of the Zealot (XGE) – divine fury; can't be killed while raging",
        ],
        resources=[
            dict(name="Rage", key="rage", reset="LR", track="uses",
                 by_level={1:2,3:3,6:4,12:5,17:6,20:"Unlimited"}),
            dict(name="Rage Damage Bonus", key="rage_dmg", track="info",
                 by_level={1:"+2",9:"+3",16:"+4"}),
        ],
        level_choices={
            1: ["Choose starting skill proficiencies (2 from list)"],
            3: ["Choose Primal Path (Subclass)",
                "Choose 1 Primal Knowledge skill"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            10: ["Choose 1 more Primal Knowledge skill"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
            # Totem Warrior choices at 3/6/14
            "totem_3": ["Choose Totem Spirit (Bear/Eagle/Elk/Tiger/Wolf)"],
            "totem_6": ["Choose Totem Spirit (aspect)"],
            "totem_14": ["Choose Totem Spirit (attunement)"],
        },
        multiclass_reqs={"STR": 13},
    ),

    # ── Bard ──────────────────────────────────────────────────────────────────
    cls("Bard", 8,
        save_profs=["DEX","CHA"],
        armor="Light armor",
        weapons="Simple weapons, hand crossbows, longswords, rapiers, shortswords",
        tools="3 musical instruments of your choice",
        skill_choices=["Any 3 skills"],
        skill_count=3, spell_ability="CHA", has_spells=True,
        spell_slots=FULL_CASTER_SLOTS, subclass_level=3,
        features={
            1: ["Spellcasting (CHA)","Bardic Inspiration (d6, CHA mod uses/LR)"],
            2: ["Jack of All Trades (+half prof to non-proficient checks)","Song of Rest (d6 heal on SR)"],
            3: ["Bard College (Subclass)","Expertise (2 skills or tools double prof)","Bard College Feature"],
            4: ["ASI / Feat"],
            5: ["Bardic Inspiration (d8)","Font of Inspiration (regain BI on SR)"],
            6: ["Countercharm (action: allies adv. vs. charm/frighten 30 ft)","Bard College Feature"],
            7: [],
            8: ["ASI / Feat"],
            9: ["Song of Rest (d8)"],
            10: ["Bardic Inspiration (d10)","Expertise (2 more skills)","Magical Secrets (learn 2 spells from any list)","Bard College Feature"],
            11: [],
            12: ["ASI / Feat"],
            13: ["Song of Rest (d10)"],
            14: ["Magical Secrets (2 more)","Bard College Feature"],
            15: ["Bardic Inspiration (d12)"],
            16: ["ASI / Feat"],
            17: ["Song of Rest (d12)"],
            18: ["Magical Secrets (2 more)"],
            19: ["ASI / Feat"],
            20: ["Superior Inspiration (regain 1 BI on Initiative if none left)"],
        },
        subclasses=[
            "College of Creation (TCE) – Note of Potential, Mote of Potential",
            "College of Eloquence (MOT/TCE) – silver tongue; near-perfect Persuasion",
            "College of Glamour (XGE) – Fey enchantment, Mantle of Majesty",
            "College of Lore – Cutting Words, Bonus Magical Secrets at 6",
            "College of Spirits (VRGtR) – commune with spirits for random effects",
            "College of Swords (XGE) – Blade Flourish combat maneuvers",
            "College of Valor – Combat Inspiration, Extra Attack, Battle Magic",
            "College of Whispers (XGE) – Psychic Blades, Words of Terror",
        ],
        resources=[
            dict(name="Bardic Inspiration", key="bardic_insp", formula="CHA_mod", reset="LR",
                 track="uses", min_val=1,
                 die_by_level={1:"d6",5:"d8",10:"d10",15:"d12"}),
        ],
        level_choices={
            1: ["Choose 3 skill proficiencies","Choose known spells (2+CHA mod cantrips, spells known by level)"],
            3: ["Choose Bard College (Subclass)","Choose Expertise skills (2)"],
            4: ["ASI / Feat"],
            6: ["Choose Expertise (2 more if Lore)"],
            8: ["ASI / Feat"],
            10: ["Choose Magical Secrets spells (2, any class list)","Choose Expertise skills (2 more)"],
            12: ["ASI / Feat"],
            14: ["Choose Magical Secrets spells (2 more)"],
            16: ["ASI / Feat"],
            18: ["Choose Magical Secrets spells (2 more)"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"CHA": 13},
    ),

    # ── Cleric ────────────────────────────────────────────────────────────────
    cls("Cleric", 8,
        save_profs=["WIS","CHA"],
        armor="Light, Medium, Shields",
        weapons="Simple weapons",
        tools="None",
        skill_choices=["History","Insight","Medicine","Persuasion","Religion"],
        skill_count=2, spell_ability="WIS", has_spells=True,
        spell_slots=FULL_CASTER_SLOTS, subclass_level=1,
        features={
            1: ["Spellcasting (WIS)","Divine Domain (Subclass) – grants bonus spells + feature","Divine Domain Feature (some domains grant a second 1st-level feature)"],
            2: ["Channel Divinity (1/SR): Turn Undead + Domain Feature (some domains grant a Channel Divinity option here)"],
            3: [],
            4: ["ASI / Feat"],
            5: ["Destroy Undead (CR 1/2)"],
            6: ["Channel Divinity (2/SR)","Divine Domain Feature"],
            7: [],
            8: ["ASI / Feat","Destroy Undead (CR 1)","Divine Domain Feature (Potent Spellcasting or Divine Strike)"],
            9: [],
            10: ["Divine Intervention (appeal to deity, lvl% chance)"],
            11: ["Destroy Undead (CR 2)"],
            12: ["ASI / Feat"],
            13: [],
            14: ["Destroy Undead (CR 3)"],
            15: [],
            16: ["ASI / Feat"],
            17: ["Destroy Undead (CR 4)","Divine Domain Feature"],
            18: ["Channel Divinity (3/SR)"],
            19: ["ASI / Feat"],
            20: ["Divine Intervention always succeeds (1/LR)"],
        },
        subclasses=[
            "Arcana Domain (SCAG) – arcane magic; arcane initiate",
            "Death Domain – necrotic magic; forbidden domain",
            "Forge Domain (XGE) – artifice; Blessing of the Forge",
            "Grave Domain (XGE) – life/death balance; Path to the Grave",
            "Knowledge Domain – omniscience; Visions of the Past",
            "Life Domain – heavy armor; Disciple of Life healing bonus",
            "Light Domain – radiance; Warding Flare",
            "Nature Domain – nature magic; Dampen Elements",
            "Order Domain (GGR/TCE) – law; Voice of Authority",
            "Peace Domain (TCE) – Emboldening Bond",
            "Trickery Domain – deception; Invoke Duplicity",
            "Twilight Domain (TCE) – Twilight Sanctuary",
            "Tempest Domain – storms; Wrath of the Storm reaction, Thunderbolt Strike, Stormborn",
            "War Domain – martial prowess; War Priest bonus attacks",
            "Ambition Domain (Amonkhet) – illusory duplicates; Invoke Duplicity",
            "Solidarity Domain (Amonkhet) – heavy armor; unity in battle, Divine Strike",
            "Strength Domain (Amonkhet) – heavy armor; feats of might, Divine Strike",
            "Zeal Domain (Amonkhet) – martial fervor; bonus attacks, Divine Strike",
        ],
        resources=[
            dict(name="Channel Divinity", key="channel_divinity", reset="SR", track="uses",
                 by_level={2:1,6:2,18:3}),
            dict(name="Harness Divine Power", key="harness_divine_power", reset="LR", track="uses",
                 by_level={2:1,6:2,18:3}, optional=True),
            dict(name="Divine Intervention", key="divine_interv", formula="1", reset="LR", track="uses"),
        ],
        level_choices={
            1: ["Choose Divine Domain (Subclass) – grants bonus spells"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"WIS": 13},
    ),

    # ── Druid ─────────────────────────────────────────────────────────────────
    cls("Druid", 8,
        save_profs=["INT","WIS"],
        armor="Light, Medium (non-metal), Shields (non-metal)",
        weapons="Clubs, daggers, darts, javelins, maces, quarterstaffs, scimitars, sickles, slings, spears",
        tools="Herbalism kit",
        skill_choices=["Arcana","Animal Handling","Insight","Medicine","Nature","Perception","Religion","Survival"],
        skill_count=2, spell_ability="WIS", has_spells=True,
        spell_slots=FULL_CASTER_SLOTS, subclass_level=2,
        features={
            1: ["Druidic (secret language)","Spellcasting (WIS)"],
            2: ["Wild Shape (CR 1/4, no fly/swim)","Druid Circle (Subclass)","Druid Circle Feature"],
            4: ["ASI / Feat","Wild Shape (CR 1/2, no fly)"],
            6: ["Druid Circle Feature"],
            8: ["ASI / Feat","Wild Shape (CR 1)"],
            10: ["Druid Circle Feature"],
            12: ["ASI / Feat"],
            14: ["Druid Circle Feature"],
            16: ["ASI / Feat"],
            18: ["Timeless Body (age 10× slower)","Beast Spells (cast while in Wild Shape)","Druid Circle Feature"],
            19: ["ASI / Feat"],
            20: ["Archdruid (unlimited Wild Shape uses)"],
        },
        subclasses=[
            "Circle of Dreams (XGE) – Fey healing; Balm of the Summer Court",
            "Circle of the Land – bonus cantrip; extra Druid spells by terrain",
            "Circle of the Moon – combat Wild Shape; CR-scaled beasts",
            "Circle of the Shepherd (XGE) – Spirit Totem; enhanced summoning",
            "Circle of Spores (GGR/TCE) – symbiotic entity; halo of spores",
            "Circle of Stars (TCE) – Starry Form with archer/chalice/dragon",
            "Circle of Wildfire (TCE) – summon wildfire spirit; fiery healing",
        ],
        resources=[
            # PHB p.66: "You regain expended uses when you finish a short
            # or long rest" -- was plain "SR" (this app's long_rest() only
            # resets resources tagged "LR" or "SR/LR", so a plain "SR"
            # resource never recovered on a long rest at all), the exact
            # bug already found and fixed for 10 other resources elsewhere
            # in this file/multiclass.py, just missed for this one.
            dict(name="Wild Shape", key="wild_shape", reset="SR/LR", track="uses",
                 by_level={2:2, 20:"Unlimited"}),
        ],
        level_choices={
            2: ["Choose Druid Circle (Subclass)","Wild Shape unlocked – max CR 1/4"],
            4: ["ASI / Feat","Wild Shape CR 1/2"],
            6: [],
            8: ["ASI / Feat","Wild Shape CR 1"],
            # Circle of Land terrain at level 2
            "land_terrain": [f"Choose terrain: {t}" for t in CIRCLE_OF_LAND_TERRAINS],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"WIS": 13},
    ),

    # ── Fighter ───────────────────────────────────────────────────────────────
    cls("Fighter", 10,
        save_profs=["STR","CON"],
        armor="All armor, Shields",
        weapons="Simple weapons, Martial weapons",
        tools="None",
        skill_choices=["Acrobatics","Animal Handling","Athletics","History","Insight","Intimidation","Perception","Survival"],
        skill_count=2, spell_ability=None, has_spells=False,
        spell_slots=None, subclass_level=3,
        features={
            1: ["Fighting Style (choose 1)","Second Wind (1d10+Fighter level, bonus action, 1/SR)"],
            2: ["Action Surge (1 extra action, 1/SR)"],
            3: ["Martial Archetype (Subclass)","Archetype Feature"],
            4: ["ASI / Feat"],
            5: ["Extra Attack (1) – 2 attacks per Attack action"],
            6: ["ASI / Feat"],
            7: ["Archetype Feature"],
            8: ["ASI / Feat"],
            9: ["Indomitable (reroll failed save, 1/LR)"],
            10: ["Archetype Feature"],
            11: ["Extra Attack (2) – 3 attacks per Attack action"],
            12: ["ASI / Feat"],
            13: ["Indomitable (2/LR)"],
            14: ["ASI / Feat"],
            15: ["Archetype Feature"],
            16: ["ASI / Feat"],
            17: ["Action Surge (2/SR)","Indomitable (3/LR)"],
            18: ["Archetype Feature"],
            19: ["ASI / Feat"],
            20: ["Extra Attack (3) – 4 attacks per Attack action"],
        },
        subclasses=[
            "Arcane Archer (XGE) – magical arrow shots",
            "Banneret (Purple Dragon Knight) (SCAG) – leadership inspire",
            "Battle Master – superiority dice + maneuvers",
            "Cavalier (XGE) – mounted combat specialist",
            "Champion – improved critical (19-20), remarkable athlete",
            "Echo Knight (EGW) – duplicate echo self",
            "Eldritch Knight – limited wizard spellcasting (INT)",
            "Psi Warrior (TCE) – psychic power, psionic dice",
            "Rune Knight (TCE) – giant rune magic",
            "Samurai (XGE) – Fighting Spirit extra attacks",
        ],
        resources=[
            dict(name="Second Wind", key="second_wind", formula="1", reset="SR", track="uses"),
            dict(name="Action Surge", key="action_surge", reset="SR", track="uses",
                 by_level={2:1,17:2}),
            dict(name="Indomitable", key="indomitable", reset="LR", track="uses",
                 by_level={9:1,13:2,17:3}),
            # Battle Master only
            dict(name="Superiority Dice (BM)", key="sup_dice", reset="SR", track="current_max",
                 by_level={3:4,7:5,10:6,15:6},
                 die_by_level={3:"d8",10:"d10",18:"d12"}, subclass="Battle Master"),
        ],
        level_choices={
            1: ["Choose Fighting Style"],
            3: ["Choose Martial Archetype (Subclass)",
                "Battle Master only: Choose 3 Maneuvers from Battle Master list"],
            4: ["ASI / Feat"],
            6: ["ASI / Feat"],
            7: ["Battle Master only: Choose 2 more Maneuvers"],
            8: ["ASI / Feat"],
            10: ["Battle Master only: Choose 2 more Maneuvers"],
            12: ["ASI / Feat"],
            14: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"STR": 13, "DEX": 13},  # OR
    ),

    # ── Monk ──────────────────────────────────────────────────────────────────
    cls("Monk", 8,
        save_profs=["STR","DEX"],
        armor="None",
        weapons="Simple weapons, shortswords",
        tools="1 artisan's tool or 1 musical instrument of your choice",
        skill_choices=["Acrobatics","Athletics","History","Insight","Religion","Stealth"],
        skill_count=2, spell_ability="WIS", has_spells=False,
        spell_slots=None, subclass_level=3,
        features={
            1: ["Unarmored Defense (10+DEX+WIS)","Martial Arts (1d4 unarmed; DEX for unarmed/monk weapons; bonus unarmed)"],
            2: ["Ki (=level points; Flurry of Blows/Patient Defense/Step of the Wind)","Unarmored Movement (+10 ft)"],
            3: ["Deflect Missiles (reduce ranged dmg, throw back if reduced to 0)","Monastic Tradition (Subclass)","Monastic Tradition Feature"],
            4: ["ASI / Feat","Slow Fall (reduce fall dmg by 5×level)"],
            5: ["Extra Attack","Stunning Strike (spend 1 ki: CON save or stunned until next turn)","Martial Arts (1d6)"],
            6: ["Ki-Empowered Strikes (unarmed magical)","Monastic Tradition Feature","Unarmored Movement (+15 ft)"],
            7: ["Evasion","Stillness of Mind (action: end charm/frighten)"],
            8: ["ASI / Feat"],
            9: ["Unarmored Movement (run on walls/water end of turn)"],
            10: ["Purity of Body (immune disease/poison)"],
            11: ["Monastic Tradition Feature","Martial Arts (1d8)"],
            12: ["ASI / Feat"],
            13: ["Tongue of the Sun and Moon (speak all languages)"],
            14: ["Diamond Soul (proficiency all saves; spend 1 ki to reroll)","Unarmored Movement (+25 ft)","Monastic Tradition Feature"],
            15: ["Timeless Body (no magical aging)"],
            16: ["ASI / Feat"],
            17: ["Monastic Tradition Feature","Martial Arts (1d10)"],
            18: ["Empty Body (action: invisible + resist all but force for 1 min, 4 ki; Astral Projection 8 ki)","Unarmored Movement (+30 ft)"],
            19: ["ASI / Feat"],
            20: ["Perfect Self (regain 4 ki on Initiative if none left)"],
        },
        subclasses=[
            "Way of the Ascendant Dragon (FTD) – draconic breath and strikes",
            "Way of the Astral Self (TCE) – manifest astral arms/visage",
            "Way of the Drunken Master (XGE) – unpredictable drunken style",
            "Way of the Four Elements – spend ki for elemental spells",
            "Way of the Kensei (XGE) – dedicated weapon mastery",
            "Way of the Long Death (SCAG) – Hour of Reaping; undying",
            "Way of Mercy (TCE) – healing/hurting hands",
            "Way of the Open Hand – Open Hand Technique; Tranquility",
            "Way of the Shadow – shadow teleport; shadow arts",
            "Way of the Sun Soul (SCAG/XGE) – radiant bolts; burning fan",
        ],
        resources=[
            dict(name="Ki Points", key="ki", formula="level", reset="SR", track="current_max",
                 available_at=2),
            dict(name="Martial Arts Die", key="martial_arts_die", track="info",
                 by_level={1:"d4",5:"d6",11:"d8",17:"d10"}),
        ],
        level_choices={
            2: ["Ki unlocked – learn Flurry of Blows, Patient Defense, Step of the Wind"],
            3: ["Choose Monastic Tradition (Subclass)"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            12: ["ASI / Feat"],
            # Four Elements choices
            "4e_discipline": ["Choose Elemental Discipline (3 known at 3, +1 per 2 levels after)"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"DEX": 13, "WIS": 13},
    ),

    # ── Paladin ───────────────────────────────────────────────────────────────
    cls("Paladin", 10,
        save_profs=["WIS","CHA"],
        armor="All armor, Shields",
        weapons="Simple weapons, Martial weapons",
        tools="None",
        skill_choices=["Athletics","Insight","Intimidation","Medicine","Persuasion","Religion"],
        skill_count=2, spell_ability="CHA", has_spells=True,
        spell_slots=HALF_CASTER_SLOTS, subclass_level=3,
        features={
            1: ["Divine Sense (1+CHA/LR: detect celestials/fiends/undead within 60 ft)","Lay on Hands (HP pool = 5×Paladin level/LR)"],
            2: ["Fighting Style","Spellcasting (CHA)","Divine Smite (expend spell slot for +2d8/slot level radiant, +1d8 vs undead/fiends)"],
            3: ["Divine Health (immune disease)","Sacred Oath (Subclass) + Channel Divinity","Sacred Oath Feature"],
            4: ["ASI / Feat"],
            5: ["Extra Attack"],
            6: ["Aura of Protection (CHA mod to saves for you + allies within 10 ft)"],
            7: ["Sacred Oath Feature"],
            8: ["ASI / Feat"],
            9: [],
            10: ["Aura of Courage (immune frightened; allies within 10 ft immune too)","Sacred Oath Feature"],
            11: ["Improved Divine Smite (+1d8 radiant on all MELEE weapon hits)"],
            12: ["ASI / Feat"],
            13: [],
            14: ["Cleansing Touch (action: dismiss magic effect on willing creature, CHA mod/LR)"],
            15: ["Sacred Oath Feature"],
            16: ["ASI / Feat"],
            17: ["Auras expand to 30 ft"],
            18: [],
            19: ["ASI / Feat"],
            20: ["Sacred Oath Capstone (major ability)"],
        },
        subclasses=[
            "Oath of the Ancients – nature's champion; Aura of Warding",
            "Oath of Conquest (XGE) – crushing tyrant; Aura of Conquest",
            "Oath of the Crown (SCAG) – protector of civilization",
            "Oath of Devotion – classic paladin; Sacred Weapon, Holy Nimbus",
            "Oath of Glory (MOT/TCE) – legendary hero; Aura of Alacrity",
            "Oath of Redemption (XGE) – pacifist warrior; Rebuke the Violent",
            "Oath of Vengeance – relentless hunter; Vow of Enmity",
            "Oath of the Watchers (TCE) – guard against otherworldly threats",
            "Oathbreaker – fallen paladin; dark powers (DM-only typically)",
        ],
        resources=[
            dict(name="Lay on Hands", key="loh", formula="5*level", reset="LR",
                 track="pool", note="Spend any amount; 5 pts to cure disease/poison"),
            dict(name="Channel Divinity", key="channel_div", formula="1", reset="SR", track="uses",
                 available_at=3),
            dict(name="Harness Divine Power", key="harness_divine_power", reset="LR", track="uses",
                 by_level={3:1,7:2,15:3}, optional=True),
            dict(name="Divine Sense", key="divine_sense", formula="1+CHA_mod", reset="LR", track="uses"),
            dict(name="Cleansing Touch", key="clean_touch", formula="CHA_mod", reset="LR", track="uses",
                 available_at=14),
        ],
        level_choices={
            1: ["Choose 2 skill proficiencies"],
            2: ["Choose Fighting Style"],
            3: ["Choose Sacred Oath (Subclass) – grants Oath spells (always prepared)"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"STR": 13, "CHA": 13},
    ),

    # ── Ranger ────────────────────────────────────────────────────────────────
    cls("Ranger", 10,
        save_profs=["STR","DEX"],
        armor="Light, Medium, Shields",
        weapons="Simple weapons, Martial weapons",
        tools="None",
        skill_choices=["Animal Handling","Athletics","Insight","Investigation","Nature","Perception","Stealth","Survival"],
        skill_count=3, spell_ability="WIS", has_spells=True,
        spell_slots=HALF_CASTER_SLOTS, subclass_level=3,
        features={
            1: ["Favored Enemy (2 types, adv. tracking + recall, no damage bonus in 5e)","Natural Explorer (terrain type, ignore difficult terrain, adv. checks)"],
            2: ["Fighting Style","Spellcasting (WIS)"],
            3: ["Primeval Awareness (expend slot: sense creature types 1 mi/6 mi)","Ranger Archetype (Subclass)","Archetype Feature"],
            4: ["ASI / Feat"],
            5: ["Extra Attack"],
            6: ["Favored Enemy (1 more type)","Natural Explorer (1 more terrain)"],
            7: ["Archetype Feature"],
            8: ["ASI / Feat","Land's Stride (ignore non-magical difficult terrain; adv. vs plant restraints)"],
            9: [],
            10: ["Natural Explorer (1 more terrain)","Hide in Plain Sight (spend 1 min: +10 Stealth to hide against a surface)"],
            11: ["Archetype Feature"],
            12: ["ASI / Feat"],
            13: ["Vanish (Hide as bonus action; can't be tracked non-magically)"],
            14: ["Favored Enemy (1 more type)","Archetype Feature"],
            15: [],
            16: ["ASI / Feat"],
            17: ["Archetype Feature"],
            18: ["Feral Senses (detect invisible creatures 30 ft; no disadv on hidden)"],
            19: ["ASI / Feat"],
            20: ["Foe Slayer (add WIS to one attack or damage vs Favored Enemy/turn)"],
        },
        subclasses=[
            "Beast Master – bond with a beast companion",
            "Drakewarden (FTD) – bond with a drake companion",
            "Fey Wanderer (TCE) – otherworldly presence; Dreadful Strikes",
            "Gloom Stalker (XGE) – ambush predator; Umbral Sight",
            "Horizon Walker (XGE) – planar scout; ethereal sight",
            "Hunter – Colossus Slayer / Giant Killer / Horde Breaker",
            "Monster Slayer (XGE) – Hunter's Sense; Slayer's Counter",
            "Swarmkeeper (TCE) – swarm of spirits; Gathered Swarm",
        ],
        resources=[],
        level_choices={
            1: ["Choose 2 Favored Enemy types",
                "Choose 1 Natural Explorer terrain type"],
            2: ["Choose Fighting Style"],
            3: ["Choose Ranger Archetype (Subclass)"],
            4: ["ASI / Feat"],
            6: ["Choose 1 more Favored Enemy type","Choose 1 more Natural Explorer terrain"],
            8: ["ASI / Feat"],
            10: ["Choose 1 more Natural Explorer terrain"],
            12: ["ASI / Feat"],
            14: ["Choose 1 more Favored Enemy type"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"DEX": 13, "WIS": 13},
    ),

    # ── Rogue ─────────────────────────────────────────────────────────────────
    cls("Rogue", 8,
        save_profs=["DEX","INT"],
        armor="Light armor",
        weapons="Simple weapons, hand crossbows, longswords, rapiers, shortswords",
        tools="Thieves' tools",
        skill_choices=["Any 4 skills"],
        skill_count=4, spell_ability=None, has_spells=False,
        spell_slots=None, subclass_level=3,
        features={
            1: ["Expertise (2 skills or tools)","Sneak Attack (1d6)","Thieves' Cant"],
            2: ["Cunning Action (bonus: Dash/Disengage/Hide)"],
            3: ["Roguish Archetype (Subclass)","Sneak Attack (2d6)","Archetype Feature"],
            4: ["ASI / Feat"],
            5: ["Uncanny Dodge (reaction: halve damage from attack you can see)","Sneak Attack (3d6)"],
            6: ["Expertise (2 more)","Sneak Attack (3d6)"],
            7: ["Evasion (DEX save half → none, fail → half)","Sneak Attack (4d6)"],
            8: ["ASI / Feat","Sneak Attack (4d6)"],
            9: ["Archetype Feature","Sneak Attack (5d6)"],
            10: ["ASI / Feat","Sneak Attack (5d6)"],
            11: ["Reliable Talent (treat any prof check below 10 as 10)","Sneak Attack (6d6)"],
            12: ["ASI / Feat","Sneak Attack (6d6)"],
            13: ["Archetype Feature","Sneak Attack (7d6)"],
            14: ["Blindsense (if you can hear, know hidden creature's location 10 ft)","Sneak Attack (7d6)"],
            15: ["Slippery Mind (add WIS save proficiency)","Sneak Attack (8d6)","Archetype Feature"],
            16: ["ASI / Feat","Sneak Attack (8d6)"],
            17: ["Archetype Feature","Sneak Attack (9d6)"],
            18: ["Elusive (attackers never have advantage on attacks vs you)","Sneak Attack (9d6)"],
            19: ["ASI / Feat","Sneak Attack (10d6)"],
            20: ["Stroke of Luck (1/LR: turn miss into hit or failed check into 20)","Sneak Attack (10d6)"],
        },
        subclasses=[
            "Arcane Trickster – Mage Hand Legerdemain; Wizard spell list (INT)",
            "Assassin – Assassinate vs surprised; Infiltration Expertise",
            "Inquisitive (XGE) – Ear for Deceit; Eye for Detail",
            "Mastermind (SCAG/XGE) – Master of Intrigue; Help as bonus action",
            "Phantom (TCE) – whispers of the dead; Tokens of the Departed",
            "Scout (XGE) – Skirmisher; Ambush Master",
            "Soulknife (TCE) – psychic blades from thin air",
            "Swashbuckler (SCAG/XGE) – Fancy Footwork; Panache",
            "Thief – Fast Hands; Second-Story Work; Supreme Sneak",
        ],
        resources=[
            dict(name="Stroke of Luck", key="stroke_luck", formula="1", reset="LR", track="uses",
                 available_at=20),
        ],
        level_choices={
            1: ["Choose 4 skill proficiencies","Choose 2 Expertise skills"],
            3: ["Choose Roguish Archetype (Subclass)"],
            4: ["ASI / Feat"],
            6: ["Choose 2 more Expertise skills"],
            8: ["ASI / Feat"],
            10: ["ASI / Feat"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"DEX": 13},
    ),

    # ── Sorcerer ──────────────────────────────────────────────────────────────
    cls("Sorcerer", 6,
        save_profs=["CON","CHA"],
        armor="None",
        weapons="Daggers, darts, slings, quarterstaffs, light crossbows",
        tools="None",
        skill_choices=["Arcana","Deception","Insight","Intimidation","Persuasion","Religion"],
        skill_count=2, spell_ability="CHA", has_spells=True,
        spell_slots=FULL_CASTER_SLOTS, subclass_level=1,
        features={
            1: ["Spellcasting (CHA)","Sorcerous Origin (Subclass)"],
            2: ["Font of Magic (Sorcery Points = Sorcerer level; convert SP↔slots)"],
            3: ["Metamagic (choose 2 options)","Sorcerous Origin Feature"],
            4: ["ASI / Feat"],
            5: [],
            6: ["Sorcerous Origin Feature"],
            7: [],
            8: ["ASI / Feat"],
            9: [],
            10: ["Metamagic (1 more option)","Sorcerous Origin Feature"],
            11: [],
            12: ["ASI / Feat"],
            13: [],
            14: ["Sorcerous Origin Feature"],
            15: [],
            16: ["ASI / Feat"],
            17: ["Metamagic (1 more option)"],
            18: ["Sorcerous Origin Feature"],
            19: ["ASI / Feat"],
            20: ["Sorcerous Restoration (regain 4 Sorcery Points on SR)"],
        },
        subclasses=[
            "Aberrant Mind (TCE) – Far Realm tentacles; psionic spells",
            "Clockwork Soul (TCE) – Mechanus order; Restore Balance",
            "Divine Soul (XGE) – chosen of the gods; divine spell list",
            "Draconic Bloodline – draconic ancestor; +1 HP/level; scaled skin",
            "Lunar Sorcery (DSotDQ) – moon phases; moonfire",
            "Pyromancer (PSK) – unofficial Plane Shift: Kaladesh; fire magic incarnate",
            "Shadow Magic (XGE) – Hound of Ill Omen; Shadow Walk",
            "Storm Sorcery (SCAG/XGE) – wind speaker; Tempestuous Magic",
            "Wild Magic – Wild Magic Surge table; Tides of Chaos",
        ],
        resources=[
            dict(name="Sorcery Points", key="sorcery_points", formula="level", reset="LR", track="current_max"),
        ],
        level_choices={
            1: ["Choose Sorcerous Origin (Subclass)",
                "Draconic: Choose Dragon Ancestor (type + language)"],
            2: ["Font of Magic unlocked"],
            3: ["Choose 2 Metamagic options"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            10: ["Choose 1 more Metamagic option"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            17: ["Choose 1 more Metamagic option"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"CHA": 13},
    ),

    # ── Warlock ───────────────────────────────────────────────────────────────
    cls("Warlock", 8,
        save_profs=["WIS","CHA"],
        armor="Light armor",
        weapons="Simple weapons",
        tools="None",
        skill_choices=["Arcana","Deception","History","Intimidation","Investigation","Nature","Religion"],
        skill_count=2, spell_ability="CHA", has_spells=True,
        # Warlock uses Pact Magic slots (not standard table)
        spell_slots=None,  # handled separately via WARLOCK_PACT_SLOTS
        subclass_level=1,
        features={
            1: ["Otherworldly Patron (Subclass)","Pact Magic (Pact spell slots; CHA-based; recover on SR)"],
            2: ["Eldritch Invocations (choose 2)","Subclass Feature"],
            3: ["Pact Boon (Pact of the Blade/Chain/Tome/Talisman)","Subclass Feature"],
            4: ["ASI / Feat"],
            5: ["Eldritch Invocations (3 total)"],
            6: ["Subclass Feature"],
            7: ["Eldritch Invocations (4 total)"],
            8: ["ASI / Feat"],
            9: ["Eldritch Invocations (5 total)"],
            10: ["Subclass Feature"],
            11: ["Mystic Arcanum (cast one 6th-level spell 1/LR)"],
            12: ["ASI / Feat","Eldritch Invocations (6 total)"],
            13: ["Mystic Arcanum (7th level)"],
            14: ["Subclass Feature"],
            15: ["Mystic Arcanum (8th level)","Eldritch Invocations (7 total)"],
            16: ["ASI / Feat"],
            17: ["Mystic Arcanum (9th level)"],
            18: ["Eldritch Invocations (8 total)"],
            19: ["ASI / Feat"],
            20: ["Eldritch Master (1 min: regain all Pact Magic slots 1/LR)"],
        },
        subclasses=[
            "The Archfey – Fey Presence; Misty Escape; Beguiling Defenses",
            "The Celestial (XGE) – divine patron; Healing Light dice pool",
            "The Fathomless (TCE) – tentacle of the deep; oceanic patron",
            "The Fiend – Dark One's Blessing (temp HP on kills); hurl through hell",
            "The Genie (TCE) – elemental patron; genie vessel home",
            "The Great Old One – telepathy; entropic ward; thought shield",
            "The Hexblade (XGE) – Hexblade's Curse; fighting style",
            "The Undead (VRGtR) – Form of Dread; undead patron",
            "The Undying (SCAG) – immortality; undying nature",
        ],
        resources=[
            dict(name="Pact Magic Slots", key="pact_slots", reset="SR", track="current_max",
                 note="Slot level = see table",
                 pact_level_by_level=WARLOCK_PACT_LEVEL),
            dict(name="Mystic Arcanum (6th)", key="arcanum_6", formula="1", reset="LR",
                 track="uses", available_at=11),
            dict(name="Mystic Arcanum (7th)", key="arcanum_7", formula="1", reset="LR",
                 track="uses", available_at=13),
            dict(name="Mystic Arcanum (8th)", key="arcanum_8", formula="1", reset="LR",
                 track="uses", available_at=15),
            dict(name="Mystic Arcanum (9th)", key="arcanum_9", formula="1", reset="LR",
                 track="uses", available_at=17),
            # Celestial patron resource
            dict(name="Healing Light (Celestial)", key="healing_light", reset="LR",
                 formula="1+level", track="pool", subclass="The Celestial (XGE)"),
        ],
        level_choices={
            1: ["Choose Otherworldly Patron (Subclass)"],
            2: ["Choose 2 Eldritch Invocations"],
            3: ["Choose Pact Boon (Blade/Chain/Tome/Talisman)",
                "Choose 1 more Eldritch Invocation"],
            4: ["ASI / Feat"],
            5: ["Choose 1 more Eldritch Invocation (3 total)"],
            6: [],
            7: ["Choose 1 more Eldritch Invocation (4 total)"],
            8: ["ASI / Feat"],
            9: ["Choose 1 more Eldritch Invocation (5 total)"],
            10: [],
            11: ["Choose Mystic Arcanum 6th-level spell"],
            12: ["ASI / Feat","Choose 1 more Eldritch Invocation (6 total)"],
            13: ["Choose Mystic Arcanum 7th-level spell"],
            15: ["Choose Mystic Arcanum 8th-level spell","Choose 1 more Invocation (7 total)"],
            16: ["ASI / Feat"],
            17: ["Choose Mystic Arcanum 9th-level spell"],
            18: ["Choose 1 more Eldritch Invocation (8 total)"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"CHA": 13},
    ),

    # ── Wizard ────────────────────────────────────────────────────────────────
    cls("Wizard", 6,
        save_profs=["INT","WIS"],
        armor="None",
        weapons="Daggers, darts, slings, quarterstaffs, light crossbows",
        tools="None",
        skill_choices=["Arcana","History","Insight","Investigation","Medicine","Religion"],
        skill_count=2, spell_ability="INT", has_spells=True,
        spell_slots=FULL_CASTER_SLOTS, subclass_level=2,
        features={
            1: ["Spellcasting (INT; spellbook with 6 spells)","Arcane Recovery (recover slots up to ceil(level/2) total on SR, 1/LR)"],
            2: ["Arcane Tradition (Subclass)","Arcane Tradition Feature"],
            3: [],
            4: ["ASI / Feat"],
            5: [],
            6: ["Arcane Tradition Feature"],
            7: [],
            8: ["ASI / Feat"],
            9: [],
            10: ["Arcane Tradition Feature"],
            11: [],
            12: ["ASI / Feat"],
            13: [],
            14: ["Arcane Tradition Feature"],
            15: [],
            16: ["ASI / Feat"],
            17: [],
            18: ["Spell Mastery (cast 1st + 2nd level spell at will without slot)"],
            19: ["ASI / Feat"],
            20: ["Signature Spells (always-prepared 3rd-level spells; cast without slot 1/each/SR)"],
        },
        subclasses=[
            "Abjuration – Ward Ward; Projected Ward; Improved Abjuration",
            "Bladesinging (SCAG/TCE) – Bladesong combat + spellcasting",
            "Chronurgy Magic (EGW) – time manipulation; Temporal Awareness",
            "Conjuration – Minor Conjuration; Focused Conjuration",
            "Divination – Portent (2 dice pre-roll per LR)",
            "Enchantment – Hypnotic Gaze; Instinctive Charm",
            "Evocation – Sculpt Spells; Overchannel",
            "Graviturgy Magic (EGW) – gravity manipulation; Event Horizon",
            "Illusion – Improved Minor Illusion; Malleable Illusions",
            "Necromancy – Grim Harvest; Undead Thralls",
            "Order of Scribes (TCE) – Awakened Spellbook; Manifest Mind",
            "Transmutation – Minor Alchemy; Transmuter's Stone; Shapechanger",
            "War Magic (XGE) – Arcane Deflection; Tactical Wit",
        ],
        resources=[
            dict(name="Arcane Recovery", key="arcane_recovery", formula="1", reset="LR", track="uses"),
        ],
        level_choices={
            1: ["Choose 2 skill proficiencies",
                "Add 6 spells to Spellbook (any 1st-level Wizard spells)"],
            2: ["Choose Arcane Tradition (Subclass)"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            18: ["Choose 2 spells for Spell Mastery (1 of 1st level, 1 of 2nd level)"],
            19: ["ASI / Feat"],
            20: ["Choose 2 spells for Signature Spells (must be 3rd level)"],
        },
        multiclass_reqs={"INT": 13},
    ),

    # ── Blood Hunter (Critical Role – unofficial) ─────────────────────────────
    cls("Blood Hunter", 10,
        save_profs=["DEX","INT"],
        armor="Light armor, Medium armor, Shields",
        weapons="Simple weapons, Martial weapons",
        tools="None",
        skill_choices=["Arcana","Athletics","History","Insight","Investigation","Perception","Survival"],
        skill_count=3, spell_ability="INT", has_spells=False,
        spell_slots=None, subclass_level=3,
        features={
            1: ["Hunter's Bane (adv. Survival to track fey/fiends/undead; INT checks to recall info about them)",
                "Blood Maledict (1 use/SR: Hex-like cursing rituals)"],
            2: ["Fighting Style","Crimson Rite (spend Hemocraft die HP to add elemental damage to weapon)"],
            3: ["Blood Hunter Order (Subclass)","Order Feature"],
            4: ["ASI / Feat"],
            5: ["Extra Attack"],
            6: ["Brand of Castigation","Blood Maledict (2 uses/SR)"],
            7: ["Order Feature","Crimson Rite Improvement (2nd rite known)"],
            8: ["ASI / Feat"],
            9: ["Grim Psychometry (INT check to read history of object/location)"],
            10: ["Dark Augmentation (+5 ft speed; +Hemocraft mod to Str/Dex/Con saves)"],
            11: ["Order Feature"],
            12: ["ASI / Feat"],
            13: ["Blood Maledict (3 uses/SR)","Brand of Tethering"],
            14: ["Hardened Soul (adv. vs Frightened and Charmed)","Crimson Rite Improvement (3rd rite known)"],
            15: ["Order Feature"],
            16: ["ASI / Feat"],
            17: ["Blood Maledict (4 uses/SR)"],
            18: ["Order Feature"],
            19: ["ASI / Feat"],
            20: ["Sanguine Mastery"],
        },
        subclasses=[
            "Order of the Ghostslayer – fight undead; Rite of the Dawn",
            "Order of the Lycan – werewolf transformation; Hybrid Transformation",
            "Order of the Mutant – mutagens for stat swaps",
            "Order of the Profane Soul – warlock-like patron pact",
        ],
        resources=[
            dict(name="Blood Maledict", key="blood_maledict", reset="SR", track="uses",
                 by_level={1:1,6:2,13:3,17:4}),
            dict(name="Crimson Rite", key="crimson_rite", reset="SR", track="info",
                 note="Bonus action: take necrotic damage equal to one Hemocraft die roll (1d4 at low levels, scaling to 1d10) to activate a known elemental rite on a weapon you hold. Lasts until your next rest; hits with that weapon deal extra damage of the rite's type equal to your Hemocraft die."),
        ],
        level_choices={
            2: ["Choose Fighting Style"],
            3: ["Choose Blood Hunter Order (Subclass)"],
            4: ["ASI / Feat"],
            8: ["ASI / Feat"],
            12: ["ASI / Feat"],
            16: ["ASI / Feat"],
            19: ["ASI / Feat"],
        },
        multiclass_reqs={"STR": 13, "INT": 13},
    ),
]

CLASS_DICT = {c["name"]: c for c in ALL_CLASSES}
CLASS_NAMES = [c["name"] for c in ALL_CLASSES]

WILD_MAGIC_SURGE_TABLE = [
    (1,2, 'Roll on the table again at the start of each turn. A Dispel Magic spell ends this effect.'),
    (3,4, 'For 1 minute, you can see any invisible creature within 30 ft.'),
    (5,6, 'A modron appears in an unoccupied space within 5 ft, then disappears 1 minute later.'),
    (7,8, 'You cast Fireball centred on yourself (DC 13, 5th-level slot).'),
    (9,10, 'You cast Magic Missile as a 5th-level spell.'),
    (11,12, 'Roll d10. Your height changes by that many inches (odd = shrink, even = grow).'),
    (13,14, 'You cast Confusion centred on yourself.'),
    (15,16, 'You regain 2d10 hit points for the next minute at the start of each turn.'),
    (17,18, 'You grow a long beard made of feathers that lasts until you sneeze.'),
    (19,20, 'You cast Grease centred on yourself.'),
    (21,22, 'Creatures within 30 ft are immune to the frightened condition for 1 minute.'),
    (23,24, 'Your skin turns a vibrant shade of blue. A Remove Curse ends this effect.'),
    (25,26, 'An eye appears on your forehead (Truesight 60 ft) for 1 minute.'),
    (27,28, 'All spells you cast for 1 minute have their range doubled.'),
    (29,30, 'You teleport up to 60 ft to an unoccupied space of your choice.'),
    (31,32, 'You are transported to the Astral Plane until the end of your next turn.'),
    (33,34, 'Maximize the damage of the next damaging spell you cast within 1 minute.'),
    (35,36, 'Roll d10. Your age changes by that many years (odd = older, even = younger; min 1).'),
    (37,38, 'You summon 1d6 flumphs in unoccupied spaces within 60 ft. They disappear after 1 minute.'),
    (39,40, 'You regain 2d10 sorcery points.'),
    (41,42, 'You turn into a potted plant until the start of your next turn.'),
    (43,44, 'For 1 minute, you can teleport up to 20 ft as a bonus action on each of your turns.'),
    (45,46, 'You cast Levitate on yourself.'),
    (47,48, 'A unicorn appears in a space within 5 ft of you, then disappears 1 minute later.'),
    (49,50, 'You cannot speak for 1 minute. Whenever you try, pink bubbles float out.'),
    (51,52, 'A spectral shield hovers near you (+2 AC, immune to Magic Missile) for 1 minute.'),
    (53,54, 'You are immune to being intoxicated for 5d6 days.'),
    (55,56, 'Your hair falls out but regrows within 24 hours.'),
    (57,58, 'For 1 minute, any flammable object you touch that is not worn or carried ignites.'),
    (59,60, 'You regain your lowest-level expended spell slot.'),
    (61,62, 'For 1 minute, you must shout when you speak.'),
    (63,64, 'You cast Fog Cloud centred on yourself.'),
    (65,66, 'Up to 3 creatures within 30 ft take 4d10 lightning damage (DEX save DC 13 for half).'),
    (67,68, 'You are frightened by the nearest creature until the end of your next turn.'),
    (69,70, 'Each creature within 30 ft takes 1d10 necrotic damage. You regain hit points equal to the sum.'),
    (71,72, 'You teleport up to 60 ft to an unoccupied space you can see.'),
    (73,74, 'The color of your eyes changes permanently.'),
    (75,76, 'You cast Blur on yourself.'),
    (77,78, 'A random creature within 60 ft becomes poisoned for 1d4 hours.'),
    (79,80, 'You glow with bright light in a 30 ft radius for 1 minute. Any creature that ends its turn within 5 ft is blinded until end of its next turn.'),
    (81,82, 'Illusory butterflies and flower petals flutter in the air within 10 ft of you for 1 minute.'),
    (83,84, 'You can take one additional action immediately.'),
    (85,86, 'Each creature within 30 ft takes 1d10 necrotic damage. You regain HP equal to total.'),
    (87,88, 'You cast Mirror Image.'),
    (89,90, 'You cast Fly on a random creature within 60 ft of you.'),
    (91,92, 'You become invisible for 1 minute or until you attack or cast a spell.'),
    (93,94, 'If you die in the next minute you return to life with 1 HP.'),
    (95,96, 'Each creature within 30 ft is poisoned for 1d4 hours (CON save DC 15 negates).'),
    (97,98, 'You are surrounded by faint ethereal music for 1 minute.'),
    (99,100, 'You regain all expended sorcery points.'),
]
# Wild Magic Surge table for Path of the Wild Magic Barbarian (TCE p.8)
# Roll d8 at the start of each turn while raging (when DM calls for it)
WILD_MAGIC_BARBARIAN_TABLE = [
    (1, "Each creature within 30 ft must succeed on a CON save (DC=8+PB+CON mod) "
        "or take 1d6 necrotic damage. You also gain 1d6 temporary HP."),
    (2, "You teleport up to 30 ft to an unoccupied space you can see. "
        "Until your rage ends, you can use this effect again on each of your turns as a bonus action."),
    (3, "Until your rage ends, you are surrounded by multicoloured, protective lights; "
        "you gain a +1 bonus to AC, and while within 10 ft of you, your allies gain the same bonus."),
    (4, "Spectral intangible bears appear. Each creature within 5 ft of you must succeed on "
        "a STR save or be knocked prone. You can push it up to 15 ft away from you."),
    (5, "Until your rage ends, any creature that hits you with an attack takes 1d6 force damage."),
    (6, "Until your rage ends, you gain advantage on attack rolls against creatures that are "
        "frightened of you."),
    (7, "Immediately after a creature hits you with an attack roll, "
        "you can use your reaction to teleport to a space within 5 ft of the attacker and "
        "make one weapon attack against them."),
    (8, "Until your rage ends, you are surrounded by a magical field. "
        "You and allies within 10 ft of you can't be surprised, and have advantage "
        "on initiative rolls."),
]


ARTIFICER_INFUSIONS = [
    "Arcane Propulsion Armor – armor boosts speed, flight, and force fist attacks (min level 14)",
    "Armor of Magical Strength – armor lets you use INT for Athletics; catch self with reaction",
    "Boots of the Winding Path – teleport back to space you left this turn as a bonus action (min level 6)",
    "Enhanced Arcane Focus – +1 (+2 at 10th level) to spell attack rolls; ignore half cover",
    "Enhanced Defense – +1 (+2 at 10th level) AC (armor or shield)",
    "Enhanced Weapon – +1 (+2 at 10th level) attack and damage rolls",
    "Helm of Awareness – advantage on initiative, can't be surprised (min level 10)",
    "Homunculus Servant – construct familiar with INT mod HP and attacks",
    "Mind Sharpener – reaction to succeed on concentration save you failed",
    "Radiant Weapon (+1) – +1 atk/dmg, bonus light, reaction to blind attacker (charges) (min level 6)",
    "Repeating Shot – ignore loading; no ammo needed; +1 attack rolls",
    "Repulsion Shield (+1) – +1 AC; reaction to push attacker 15 ft on hit (charges) (min level 6)",
    "Resistant Armor – resistance to one damage type of choice (min level 6)",
    "Returning Weapon (+1) – +1 atk/dmg; thrown weapon returns to hand",
    "Spell-Refueling Ring – once per day, regain one expended spell slot (3rd level or lower) (min level 6)",
    # Replicable Items (2nd-Level Artificer).
    "Alchemy Jug – produce vinegar, honey, oil, water, wine, or acid (min level 2)",
    "Bag of Holding – 500 lb / 64 cu ft of extradimensional storage (min level 2)",
    "Cap of Water Breathing – breathe underwater (min level 2)",
    "Goggles of Night – darkvision 60 ft (+30 if you already have it) (min level 2)",
    "Rope of Climbing – 60 ft animated rope, climbs/knots/unknots on command (min level 2)",
    "Sending Stones – pair of stones, cast Sending to its twin once/day (min level 2)",
    "Wand of Magic Detection – cast Detect Magic (charges) (min level 2)",
    "Wand of Secrets – senses secret doors/passages within 30 ft (charges) (min level 2)",
    # Replicable Items (6th-Level Artificer)
    "Boots of Elvenkind – advantage on Stealth checks relying on moving quietly (min level 6)",
    "Cloak of Elvenkind – advantage on Stealth; disadvantage on checks to see you (min level 6)",
    "Cloak of the Manta Ray – breathe underwater, swim speed 60 ft (min level 6)",
    "Eyes of Charming – cast Charm Person (charges) (min level 6)",
    "Gloves of Thievery – +5 Sleight of Hand, +5 to lock DCs against you (min level 6)",
    "Lantern of Revealing – invisible creatures in its light are visible (min level 6)",
    "Pipes of Haunting – frighten listeners on a failed WIS save (charges) (min level 6)",
    "Ring of Water Walking – walk on any liquid surface as if solid ground (min level 6)",
    # Replicable Items (10th-Level Artificer).
    "Boots of Striding and Springing – speed 30 ft even if heavier, triple jump distance (min level 10)",
    "Boots of the Winterlands – cold resistance, unaffected by extreme cold, no snow penalty (min level 10)",
    "Bracers of Archery – proficiency with longbow/shortbow, +2 damage with them (min level 10)",
    "Brooch of Shielding – immune to Magic Missile, resistance to force damage (min level 10)",
    "Cloak of Protection – +1 AC and saving throws (min level 10)",
    "Eyes of the Eagle – advantage on sight-based Perception, see clearly up to 1 mile (min level 10)",
    "Gauntlets of Ogre Power – STR score becomes 19 (if not already higher) (min level 10)",
    "Gloves of Missile Snaring – reaction: reduce ranged weapon damage by 1d10+DEX (min level 10)",
    "Gloves of Swimming and Climbing – climb/swim speed = walking speed, advantage on related checks (min level 10)",
    "Hat of Disguise – cast Disguise Self at will (min level 10)",
    "Headband of Intellect – INT score becomes 19 (if not already higher) (min level 10)",
    "Helm of Telepathy – read surface thoughts within 30 ft; cast Suggestion via telepathic bond (charges) (min level 10)",
    "Medallion of Thoughts – cast Detect Thoughts (charges) (min level 10)",
    "Necklace of Adaptation – immune to harmful gas, breathe any atmosphere (min level 10)",
    "Periapt of Wound Closure – stabilize automatically at 0 HP, double HP regained from healing (min level 10)",
    "Pipes of the Sewers – cast Speak with Animals (rats only) at will; can charm rat swarms (charges) (min level 10)",
    "Quiver of Ehlonna – extradimensional space holding arrows/bolts/javelins (min level 10)",
    "Ring of Jumping – cast Jump on yourself at will, no components (min level 10)",
    "Ring of Mind Shielding – immune to magic that detects/reads emotions/thoughts; soul preserved on death (min level 10)",
    "Slippers of Spider Climbing – climb difficult surfaces/ceilings like a spider (min level 10)",
    "Ventilating Lungs – breathe underwater, swim speed 30 ft (min level 10)",
    "Winged Boots – flying speed = walking speed for a limited duration (charges) (min level 10)",
    # Replicable Items (14th-Level Artificer).
    "Amulet of Health – CON score becomes 19 (if not already higher) (min level 14)",
    "Arcane Propulsion Arm – replacement arm, magic melee weapon, INT for attack/damage (min level 14)",
    "Belt of Hill Giant Strength – STR score becomes 21 (if not already higher) (min level 14)",
    "Boots of Levitation – cast Levitate on yourself at will (min level 14)",
    "Boots of Speed – bonus action: double speed, extra dodge-like benefit (charges) (min level 14)",
    "Bracers of Defense – +2 AC and saving throws while wearing no armor/shield (min level 14)",
    "Cloak of the Bat – advantage on Stealth in darkness, cast Polymorph (bat form only, charges) (min level 14)",
    "Dimensional Shackles – restrain a creature, blocks extradimensional/planar escape (min level 14)",
    "Gem of Seeing – cast True Seeing on yourself (charges) (min level 14)",
    "Horn of Blasting – action: 5d6 thunder damage in a cone (charges) (min level 14)",
    "Ring of Free Action – can't be paralyzed/restrained; difficult terrain costs no extra movement while unencumbered (min level 14)",
    "Ring of Protection – +1 AC and saving throws (min level 14)",
    "Ring of the Ram – ranged force attack that can push the target (charges) (min level 14)",
]

# Classifies each infusion by what kind of item it applies to, based on
# the actual "Item:" requirement in each infusion's real rule text.
# "weapon"/"armor"/"shield" infusions enchant an EXISTING item the
# character already owns (offered via the right-click "Infuse this
# item" menu on matching equipment); "standalone" infusions create
# their own item when activated, with no existing item needed.
ARTIFICER_INFUSION_TARGETS = {
    "Enhanced Weapon": "weapon",
    "Radiant Weapon (+1)": "weapon",
    "Repeating Shot": "weapon",
    "Returning Weapon (+1)": "weapon",
    "Enhanced Defense": "armor_or_shield",
    "Resistant Armor": "armor",
    "Armor of Magical Strength": "armor",
    "Arcane Propulsion Armor": "armor",
    "Mind Sharpener": "armor",  # "a suit of armor or robes"
    "Repulsion Shield (+1)": "shield",
    "Boots of the Winding Path": "standalone",  # boots — no "boots" equipment slot tracked
    "Enhanced Arcane Focus": "standalone", # wand/rod/staff — not tracked as separate gear
    "Helm of Awareness": "standalone",          # helmet — no separate slot tracked
    "Homunculus Servant": "standalone",         # a creature, not an item
    "Spell-Refueling Ring": "standalone",       # ring — no separate slot tracked
}

# These four infusions grant a genuine charge pool — a different data
# path from the existing charge system, which only covers magic_items
# catalog entries with a grant_spell effect, since these enchant an
# existing equipment item rather than creating a standalone
# magic_items entry.
# {infusion_name: (max_charges, recharge_dice, recharge_timing)}
ARTIFICER_INFUSION_CHARGES = {
    "Armor of Magical Strength": (6, "1d6", "dawn"),
    "Mind Sharpener": (4, "1d4", "dawn"),
    "Radiant Weapon (+1)": (4, "1d4", "dawn"),
    "Repulsion Shield (+1)": (4, "1d4", "dawn"),
}

# Artificer's Replicable Magic Items feature — NOT a "choose N of M" pick
# like Infusions/Metamagic/Invocations. Per the class table, you simply
# KNOW how to replicate every item on the list for your current tier (2nd/
# 6th/10th/14th level), no selection needed. (attunement: bool)
ARTIFICER_REPLICABLE_ITEMS = {
    2: [
        ("Alchemy Jug", False), ("Bag of Holding", False),
        ("Cap of Water Breathing", False), ("Goggles of Night", False),
        ("Rope of Climbing", False), ("Sending Stones", False),
        ("Wand of Magic Detection", False), ("Wand of Secrets", False),
    ],
    6: [
        ("Boots of Elvenkind", False), ("Cloak of Elvenkind", True),
        ("Cloak of the Manta Ray", False), ("Eyes of Charming", True),
        ("Gloves of Thievery", False), ("Lantern of Revealing", False),
        ("Pipes of Haunting", False), ("Ring of Water Walking", False),
    ],
    10: [
        ("Boots of Striding and Springing", True), ("Boots of the Winterlands", True),
        ("Bracers of Archery", True), ("Brooch of Shielding", True),
        ("Cloak of Protection", True), ("Eyes of the Eagle", True),
        ("Gauntlets of Ogre Power", True), ("Gloves of Missile Snaring", True),
        ("Gloves of Swimming and Climbing", True), ("Hat of Disguise", True),
        ("Headband of Intellect", True), ("Helm of Telepathy", True),
        ("Medallion of Thoughts", True), ("Necklace of Adaptation", True),
        ("Periapt of Wound Closure", True), ("Pipes of the Sewers", True),
        ("Quiver of Ehlonna", False), ("Ring of Jumping", True),
        ("Ring of Mind Shielding", True), ("Slippers of Spider Climbing", True),
        ("Ventilating Lungs (Eberron: Rising from the Last War)", True),
        ("Winged Boots", True),
    ],
    14: [
        ("Amulet of Health", True),
        ("Arcane Propulsion Arm (Eberron: Rising from the Last War)", True),
        ("Belt of Hill Giant Strength", True), ("Boots of Levitation", True),
        ("Boots of Speed", True), ("Bracers of Defense", True),
        ("Cloak of the Bat", True), ("Dimensional Shackles", False),
        ("Gem of Seeing", True), ("Horn of Blasting", False),
        ("Ring of Free Action", True), ("Ring of Protection", True),
        ("Ring of the Ram", True),
    ],
}


def get_class(name: str) -> dict:
    return CLASS_DICT.get(name)

def prof_bonus(total_level: int) -> int:
    return max(2, (total_level - 1) // 4 + 2)

def sneak_attack_dice(rogue_levels: int) -> int:
    return (rogue_levels + 1) // 2
