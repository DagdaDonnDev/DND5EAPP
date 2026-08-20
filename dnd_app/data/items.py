"""
D&D 5e Mundane Items — weapons, armor, adventuring gear, tools, mounts.

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ── Armor ─────────────────────────────────────────────────────────────────────
ARMOR = [
    # name, type, ac_base, dex_cap, stealth_disadv, str_req, weight_lb, cost_gp
    ("No Armor",          "none",   10, None,  False,  0,  0,    0),
    ("Padded",            "light",  11, None,  True,   0,  8,    5),
    ("Leather",           "light",  11, None,  False,  0,  10,   10),
    ("Studded Leather",   "light",  12, None,  False,  0,  13,   45),
    ("Hide",              "medium", 12, 2,     False,  0,  12,   10),
    ("Chain Shirt",       "medium", 13, 2,     False,  0,  20,   50),
    ("Scale Mail",        "medium", 14, 2,     True,   0,  45,   50),
    ("Breastplate",       "medium", 14, 2,     False,  0,  20,   400),
    ("Half Plate",        "medium", 15, 2,     True,   0,  40,   750),
    ("Ring Mail",         "heavy",  14, 0,     True,   0,  40,   30),
    ("Chain Mail",        "heavy",  16, 0,     True,   13, 55,   75),
    ("Splint",            "heavy",  17, 0,     True,   15, 60,   200),
    ("Plate",             "heavy",  18, 0,     True,   15, 65,   1500),
    ("Shield",            "shield", 2,  None,  False,  0,  6,    10),
    # ── Adventure-specific armor ────────────────────────────────────────────
    ("Spiked Armor",      "medium", 14, 2,     True,   0,  45,   75),
    # Survival Mantle's special properties (breathe in any environment
    # including vacuum, advantage on saves vs. harmful gases, can't be
    # worn with other armor) aren't captured by this plain tuple format
    # — only its AC/weight/cost mechanics are represented here.
    ("Survival Mantle",   "medium", 15, 2,     True,   0,  40,   0),
]

# Special/magic-adjacent armors
SPECIAL_ARMOR = [
    ("Mage Armor (spell)", "none",  13, None,  False, 0, 0, 0,
     "13 + DEX mod. Requires no armor worn."),
    ("Natural Armor",      "none",  13, None,  False, 0, 0, 0,
     "13 + CON mod. Tortle, Loxodon, etc."),
    ("Unarmored Defense (Barb)", "none", 10, None, False, 0, 0, 0,
     "10 + DEX + CON mod. Barbarian class feature."),
    ("Unarmored Defense (Monk)", "none", 10, None, False, 0, 0, 0,
     "10 + DEX + WIS mod. Monk class feature."),
    ("Dragon Hide (feat)", "none",  13, None,  False, 0, 0, 0,
     "13 + DEX mod. From the Dragon Hide feat."),
]

def armor_dict():
    return {name: dict(type=t, ac=ac, dex_cap=dc, stealth=st,
                       str_req=sr, weight=w, cost=c)
            for name, t, ac, dc, st, sr, w, c in ARMOR}

ARMOR_DICT = armor_dict()
ARMOR_NAMES = [a[0] for a in ARMOR]
ARMOR_NAMES_FULL = ARMOR_NAMES + [a[0] for a in SPECIAL_ARMOR]

# ── Weapons ───────────────────────────────────────────────────────────────────
# name, category, damage, damage_type, weight, cost_gp, properties
SIMPLE_MELEE = [
    ("Club",          "Simple Melee",  "1d4",  "bludgeoning", 2,   0.1,  ["Light"]),
    ("Dagger",        "Simple Melee",  "1d4",  "piercing",    1,   2,    ["Finesse","Light","Thrown (20/60)"]),
    ("Greatclub",     "Simple Melee",  "1d8",  "bludgeoning", 10,  0.2,  ["Two-handed"]),
    ("Handaxe",       "Simple Melee",  "1d6",  "slashing",    2,   5,    ["Light","Thrown (20/60)"]),
    ("Javelin",       "Simple Melee",  "1d6",  "piercing",    2,   0.5,  ["Thrown (30/120)"]),
    ("Light Hammer",  "Simple Melee",  "1d4",  "bludgeoning", 2,   2,    ["Light","Thrown (20/60)"]),
    ("Mace",          "Simple Melee",  "1d6",  "bludgeoning", 4,   5,    []),
    ("Quarterstaff",  "Simple Melee",  "1d6",  "bludgeoning", 4,   0.2,  ["Versatile (1d8)"]),
    ("Sickle",        "Simple Melee",  "1d4",  "slashing",    2,   1,    ["Light"]),
    ("Spear",         "Simple Melee",  "1d6",  "piercing",    3,   1,    ["Thrown (20/60)","Versatile (1d8)"]),
    ("Unarmed Strike","Simple Melee",  "1+STR","bludgeoning", 0,   0,    []),
]

SIMPLE_RANGED = [
    ("Light Crossbow","Simple Ranged","1d8",  "piercing",    5,   25,   ["Ammunition (80/320)","Loading","Two-handed"]),
    ("Dart",           "Simple Ranged","1d4",  "piercing",    0.25,0.05, ["Finesse","Thrown (20/60)"]),
    ("Shortbow",       "Simple Ranged","1d6",  "piercing",    2,   25,   ["Ammunition (80/320)","Two-handed"]),
    ("Sling",          "Simple Ranged","1d4",  "bludgeoning", 0,   0.1,  ["Ammunition (30/120)"]),
    ("Iron Ball",      "Simple Ranged","1d4",  "bludgeoning", 0,   0,    ["Finesse", "Thrown (120)"]),
    ("Light Repeating Crossbow","Simple Ranged","1d8","piercing", 5, 0,  ["Ammunition (40/160)", "Two-handed", "Holds 6 bolts, no Loading property (reloading the cartridge takes an action)"]),
]

MARTIAL_MELEE = [
    ("Battleaxe",      "Martial Melee","1d8",  "slashing",    4,   10,   ["Versatile (1d10)"]),
    ("Flail",          "Martial Melee","1d8",  "bludgeoning", 2,   10,   []),
    ("Glaive",         "Martial Melee","1d10", "slashing",    6,   20,   ["Heavy","Reach","Two-handed"]),
    ("Greataxe",       "Martial Melee","1d12", "slashing",    7,   30,   ["Heavy","Two-handed"]),
    ("Greatsword",     "Martial Melee","2d6",  "slashing",    6,   50,   ["Heavy","Two-handed"]),
    ("Halberd",        "Martial Melee","1d10", "slashing",    6,   20,   ["Heavy","Reach","Two-handed"]),
    ("Lance",          "Martial Melee","1d12", "piercing",    6,   10,   ["Reach","Special"]),
    ("Longsword",      "Martial Melee","1d8",  "slashing",    3,   15,   ["Versatile (1d10)"]),
    ("Maul",           "Martial Melee","2d6",  "bludgeoning", 10,  10,   ["Heavy","Two-handed"]),
    ("Morningstar",    "Martial Melee","1d8",  "piercing",    4,   15,   []),
    ("Pike",           "Martial Melee","1d10", "piercing",    18,  5,    ["Heavy","Reach","Two-handed"]),
    ("Rapier",         "Martial Melee","1d8",  "piercing",    2,   25,   ["Finesse"]),
    ("Scimitar",       "Martial Melee","1d6",  "slashing",    3,   25,   ["Finesse","Light"]),
    ("Shortsword",     "Martial Melee","1d6",  "piercing",    2,   10,   ["Finesse","Light"]),
    ("Trident",        "Martial Melee","1d6",  "piercing",    4,   5,    ["Thrown (20/60)","Versatile (1d8)"]),
    ("War Pick",       "Martial Melee","1d8",  "piercing",    2,   5,    []),
    ("Warhammer",      "Martial Melee","1d8",  "bludgeoning", 2,   15,   ["Versatile (1d10)"]),
    ("Whip",           "Martial Melee","1d4",  "slashing",    3,   2,    ["Finesse","Reach"]),
    # ── Sourcebook Weapons ──────────────────────────────────────────────────
    ("Double-Bladed Scimitar","Martial Melee","2d4","slashing",  6, 100, ["Special","Two-Handed"]),
    ("Hoopak",               "Martial Melee","1d6","bludgeoning",2,   5, ["Versatile(sling 1d4)","Two-Handed"]),
    ("Yklwa",                "Simple Melee", "1d6","piercing",   3,   1, ["Thrown (10/30)"]),
    ("Hooked Shortspear",    "Martial Melee","1d4","piercing",   2,   0, ["Light", "On a hit, can forgo damage to trip: target makes a STR save (DC 8 + wielder's STR mod + PB) or falls prone"]),
    # Flensing Claws: a special, creature-specific Illithid-thrall
    # augmentation (surgically implanted, can't be removed or used by
    # anyone else) — always uses the wielder's own proficiency bonus
    # and STR modifier, not standard weapon proficiency rules. Tiny
    # and Gargantuan creatures can't be fitted with these.
    ("Flensing Claws (Small)","Martial Melee","1d8","slashing",  0,   0, ["Special: surgically implanted, creature-specific, always proficient"]),
    ("Flensing Claws (Medium)","Martial Melee","1d10","slashing",0,   0, ["Special: surgically implanted, creature-specific, always proficient"]),
    ("Flensing Claws (Large)","Martial Melee","1d12","slashing", 0,   0, ["Special: surgically implanted, creature-specific, always proficient"]),
    ("Flensing Claws (Huge)","Martial Melee","2d8","slashing",   0,   0, ["Special: surgically implanted, creature-specific, always proficient"]),
]

MARTIAL_RANGED = [
    ("Blowgun",        "Martial Ranged","1",   "piercing",    1,   10,   ["Ammunition (25/100)","Loading"]),
    ("Hand Crossbow", "Martial Ranged","1d6", "piercing",    3,   75,   ["Ammunition (30/120)","Light","Loading"]),
    ("Heavy Crossbow","Martial Ranged","1d10","piercing",    18,  50,   ["Ammunition (100/400)","Heavy","Loading","Two-handed"]),
    ("Longbow",        "Martial Ranged","1d8", "piercing",    2,   50,   ["Ammunition (150/600)","Heavy","Two-handed"]),
    ("Oversized Longbow","Martial Ranged","2d6","piercing",   2,   0,    ["Ammunition (150/600)","Heavy","Two-handed","Requires STR 18+, Medium or larger"]),
    ("Net",            "Martial Ranged","—",   "—",           3,   1,    ["Special","Thrown (5/15)"]),
]

ALL_WEAPONS = SIMPLE_MELEE + SIMPLE_RANGED + MARTIAL_MELEE + MARTIAL_RANGED

FIREARMS = [
    # ── Firearms (DMG optional rules, DMG pp.267-268) ─────────────────────

    # Renaissance
    ("Pistol",          "Martial Ranged","1d10","piercing", 3,  250, ["Ammunition (30/90)","Loading","Reload (4 shots)"]),
    ("Musket",          "Martial Ranged","1d12","piercing", 10, 500, ["Ammunition (40/120)","Loading","Two-Handed","Reload (1 shot)"]),
    # Modern
    ("Revolver",        "Martial Ranged","2d8", "piercing", 3,  500, ["Ammunition (40/120)","Reload (6 shots)"]),
    ("Hunting Rifle",   "Martial Ranged","2d10","piercing", 8,  750, ["Ammunition (80/240)","Two-Handed","Reload (5 shots)"]),
    ("Automatic Rifle", "Martial Ranged","2d8", "piercing", 8,  1500,["Ammunition (100/300)","Burst Fire (10)","Two-Handed","Reload (30 shots)"]),
    # Futuristic
    ("Laser Pistol",    "Martial Ranged","3d6", "radiant",  2,  250, ["Ammunition – Energy Cell (40/120)","Reload (50 shots)"]),
    ("Laser Rifle",     "Martial Ranged","3d8", "radiant",  7,  750, ["Ammunition – Energy Cell (100/300)","Two-Handed","Reload (30 shots)"]),
    ("Antimatter Rifle","Martial Ranged","6d8", "necrotic", 10, 1000,["Ammunition – Energy Cell (120/360)","Two-Handed","Reload (2 shots)"]),
]

ALL_WEAPONS = ALL_WEAPONS + FIREARMS

WEAPON_NAMES = [w[0] for w in ALL_WEAPONS]

def weapon_dict():
    return {name: dict(category=cat, damage=dmg, dmg_type=dt,
                       weight=w, cost=c, properties=props)
            for name, cat, dmg, dt, w, c, props in ALL_WEAPONS}

WEAPON_DICT = weapon_dict()

# ── Equipment Packs ────────────────────────────────────────────────────────────
# Each entry: (item_name, qty). Referenced by name in
# starting_equipment.py's choice options; a chosen pack adds its real component items.
EQUIPMENT_PACKS = {
    "Burglar's Pack": [
        ("Backpack", 1), ("Ball bearings (bag of 1,000)", 1), ("String (10 feet)", 1),
        ("Bell", 1), ("Candle", 5), ("Crowbar", 1), ("Hammer", 1), ("Piton", 10),
        ("Hooded lantern", 1), ("Oil (flask)", 2), ("Rations (1 day)", 5),
        ("Tinderbox", 1), ("Waterskin", 1), ("Hempen rope (50 feet)", 1),
    ],
    "Diplomat's Pack": [
        ("Chest", 1), ("Case, map or scroll", 2), ("Fine clothes", 1), ("Ink (1 oz bottle)", 1),
        ("Ink pen", 1), ("Lamp", 1), ("Oil (flask)", 2), ("Paper (one sheet)", 5),
        ("Perfume (vial)", 1), ("Sealing wax", 1), ("Soap", 1),
    ],
    "Dungeoneer's Pack": [
        ("Backpack", 1), ("Crowbar", 1), ("Hammer", 1), ("Piton", 10), ("Torch", 10),
        ("Tinderbox", 1), ("Rations (1 day)", 10), ("Waterskin", 1), ("Hempen rope (50 feet)", 1),
    ],
    "Entertainer's Pack": [
        ("Backpack", 1), ("Bedroll", 1), ("Costume", 2), ("Candle", 5),
        ("Rations (1 day)", 5), ("Waterskin", 1), ("Disguise kit", 1),
    ],
    "Explorer's Pack": [
        ("Backpack", 1), ("Bedroll", 1), ("Mess kit", 1), ("Tinderbox", 1), ("Torch", 10),
        ("Rations (1 day)", 10), ("Waterskin", 1), ("Hempen rope (50 feet)", 1),
    ],
    "Priest's Pack": [
        ("Backpack", 1), ("Blanket", 1), ("Candle", 10), ("Tinderbox", 1), ("Alms box", 1),
        ("Block of incense", 2), ("Censer", 1), ("Vestments", 1), ("Rations (1 day)", 2),
        ("Waterskin", 1),
    ],
    "Scholar's Pack": [
        ("Backpack", 1), ("Book of lore", 1), ("Ink (1 oz bottle)", 1), ("Ink pen", 1),
        ("Parchment (one sheet)", 10), ("Little bag of sand", 1), ("Small knife", 1),
    ],
}

# ── Adventuring Gear ──────────────────────────────────────────────────────────
# name, weight_lb, cost_gp, notes
ADVENTURING_GEAR = [
    ("Abacus",                  2,   2,    ""),
    ("Acid (vial)",             1,   25,   "Action throw: 2d6 acid on hit (DEX save DC 10)."),
    ("Alchemist's Fire (flask)",1,   50,   "Ranged attack, 1d4 fire/turn until action DC 10 DEX."),
    ("Ammunition, Arrows (20)", 1,   1,    ""),
    ("Ammunition, Bolts (20)",  1.5, 1,    ""),
    ("Ammunition, Bullets (20)",1.5, 0.04, "Sling bullets."),
    ("Ammunition, Needles (50)",0.5, 1,    "Blowgun needles."),
    ("Antitoxin",               0,   50,   "Adv. on saves vs poison for 1 hour."),
    ("Arcane Focus",            0, 0, "Crystal/Orb/Rod/Staff/Wand. Used by Sorcerer/Warlock/Wizard."),
    ("Backpack",                5,   2,    "Holds 30 lb (1 cu ft)."),
    ("Ball Bearings (1000)",    2,   1,    "Scatter: DEX DC 10 or fall prone."),
    ("Barrel",                  70,  2,    "Holds 40 gallons liquid or 4 cu ft solid."),
    ("Basket",                  2,   0.4,  "Holds 2 cu ft / 40 lb."),
    ("Bedroll",                 7,   1,    ""),
    ("Bell",                    0,   1,    ""),
    ("Blanket",                 3,   0.5,  ""),
    ("Block and Tackle",        5,   1,    "Rig for hoisting: limit = str score × 30 lb."),
    ("Book",                    5,   25,   ""),
    ("Bottle, Glass",           2,   2,    ""),
    ("Bucket",                  2,   0.05, ""),
    ("Caltrops (bag of 20)",    2,   1,    "Cover 5 sq ft: DEX DC 15 or 1 piercing + speed halved."),
    ("Candle",                  0,   0.01, "1 hr: bright 5 ft, dim 5 ft."),
    ("Case, Crossbow Bolt",     1,   1,    "Holds 20 bolts."),
    ("Case, Map or Scroll",     1,   1,    "Cylindrical leather, holds up to 10 sheets."),
    ("Chain (10 ft)",           10,  5,    ""),
    ("Chalk (1 piece)",         0,   0.01, ""),
    ("Chest",                   25,  5,    "Holds 12 cu ft / 300 lb."),
    ("Climber's Kit",           12,  25,   "Pitons, boot tips, gloves, harness."),
    ("Clothes, Common",         3,   0.5,  ""),
    ("Clothes, Costume",        4,   5,    ""),
    ("Clothes, Fine",           6,   15,   ""),
    ("Clothes, Traveler's",     4,   2,    ""),
    ("Component Pouch",         2,   25,   "Material spell components (non-costly)."),
    ("Crowbar",                 5,   2,    "Adv. STR checks where leverage applies."),
    ("Druidic Focus",           0, 0, "Sprig of mistletoe/totem/staff/wand. For Druids."),
    ("Fishing Tackle",          4,   1,    ""),
    ("Flask or Tankard",        1,   0.02, ""),
    ("Grappling Hook",          4,   2,    ""),
    ("Hammer",                  3,   1,    ""),
    ("Hammer, Sledge",          10,  2,    ""),
    ("Healer's Kit",            3,   5,    "10 uses: stabilize creature without Medicine check."),
    ("Holy Symbol",             1,   5,    "Amulet/emblem/reliquary. For Clerics/Paladins."),
    ("Holy Water (flask)",      1,   25,   "Action throw: 2d6 radiant vs undead/fiends (DEX DC 10)."),
    ("Hourglass",               1,   25,   ""),
    ("Hunting Trap",            25,  5,    "DC 13 DEX or restrained (escaped by STR DC 13 + 1 dmg attempt)."),
    ("Ink (1 oz bottle)",       0,   10,   ""),
    ("Ink Pen",                 0,   0.02, ""),
    ("Jug or Pitcher",          4,   0.02, ""),
    ("Ladder (10 ft)",          25,  0.1,  ""),
    ("Lamp",                    1,   0.5,  "6 hrs on 1 pint oil: bright 15 ft, dim 30 ft."),
    ("Lantern, Bullseye",       2,   10,   "6 hrs on 1 pint oil: bright 60 ft cone, dim 120 ft."),
    ("Lantern, Hooded",         2,   5,    "6 hrs on 1 pint oil: bright 30 ft, dim 60 ft. Can shutter."),
    ("Lock",                    1,   10,   "DC 15 Thieves' Tools to pick."),
    ("Magnifying Glass",        0,   100,  "Advantage on appraisal checks. Start fires in sunlight."),
    ("Manacles",                6,   2,    "DC 20 STR to break, DC 15 Thieves' Tools."),
    ("Mess Kit",                1,   0.2,  ""),
    ("Mirror, Steel",           0.5, 5,    ""),
    ("Net",                     3,   1,    "Large or smaller: restrained. DC 10 STR to break, 5 slashing to cut."),
    ("Oil (flask)",             1,   0.1,  "Action douse: ignite — 5 fire damage/round for 2 rounds."),
    ("Paper (one sheet)",       0,   0.2,  ""),
    ("Parchment (one sheet)",   0,   0.1,  ""),
    ("Perfume (vial)",          0,   5,    ""),
    ("Pick, Miner's",           10,  2,    ""),
    ("Piton",                   0.25,0.05, ""),
    ("Poison, Basic (vial)",    0,   100,  "Coat weapon (1 min): DC 10 CON or 1d4 poison, 1 hr."),
    ("Pole (10-foot)",          7,   0.05, ""),
    ("Pot, Iron",               10,  2,    ""),
    ("Potion of Healing",       0.5, 50,   "Heal 2d4+2 HP."),
    ("Pouch",                   1,   0.5,  "Holds 6 lb / 1/5 cu ft."),
    ("Quiver",                  1,   1,    "Holds 20 arrows."),
    ("Ram, Portable",           35,  4,    "2+ people: adv STR checks to break doors."),
    ("Rations (1 day)",         2,   0.5,  ""),
    ("Robes",                   4,   1,    ""),
    ("Rope, Hempen (50 ft)",    10,  1,    ""),
    ("Rope, Silk (50 ft)",      5,   10,   ""),
    ("Sack",                    0.5, 0.01, "Holds 30 lb / 1 cu ft."),
    ("Scale, Merchant's",       3,   5,    ""),
    ("Sealing Wax",             0,   0.5,  ""),
    ("Shovel",                  5,   2,    ""),
    ("Signal Whistle",          0,   0.05, ""),
    ("Signet Ring",             0,   5,    ""),
    ("Soap",                    0,   0.02, ""),
    ("Spellbook",               3,   50,   "100 pages. Records Wizard spells. Required for prep."),
    ("Spike, Iron",             0.5, 0.1,  ""),
    ("Spyglass",                1,   1000, "Objects 2× closer."),
    ("Tent, Two-Person",        20,  2,    ""),
    ("Tinderbox",               1,   0.5,  "Strike spark to light fire (action or 1 min)."),
    ("Torch",                   1,   0.01, "1 hr: bright 20 ft, dim 20 ft. 1 fire damage."),
    ("Vial",                    0,   1,    ""),
    ("Waterskin",               5,   0.2,  "Holds 4 pints of liquid."),
    ("Whetstone",               1,   0.01, ""),
]


# ── Tack, Vehicles, Trade Goods & Misc ────────────────────────────────────────
# These are added to ADVENTURING_GEAR so they show up in the gear browser
ADVENTURING_GEAR += [
    # ── Tack & Harness ────────────────────────────────────────────────────
    ("Bit and Bridle",          1,    2,    "Required to ride a beast."),
    ("Feed (per day)",          10,   0.05, "Feed for one animal."),
    ("Riding Saddle",           25,   10,   "+2 to checks to stay mounted."),
    ("Exotic Saddle",           40,   60,   "Required for exotic or monster mounts."),
    ("Saddlebags",              8,    4,    "Carry capacity: 2×20 lb pouches."),
    ("Portable Ram",            35,   4,    "Break down doors: +4 to Strength check, advantage with 2 people."),
    # ── Vehicles (land) ───────────────────────────────────────────────────
    ("Cart",                    200,  15,   "Two-wheeled vehicle. Carry: 1,000 lb."),
    ("Carriage",                600,  100,  "Four-wheeled enclosed vehicle."),
    ("Chariot",                 100,  250,  "Combat vehicle. +AC if moving."),
    ("Sled",                    300,  20,   "Runners for snow/ice travel."),
    ("Wagon",                   400,  35,   "Four-wheeled heavy vehicle. Carry: 4,000 lb."),
    # ── Vehicles (water) ──────────────────────────────────────────────────
    ("Galley",                  0,    30000,"Oared warship. 4 mph. Crew: 80."),
    ("Keelboat",                0,    3000, "River/coastal vessel. 1 mph sail. Crew: 1."),
    ("Longship",                0,    10000,"Fast raiding vessel. 3 mph. Crew: 40."),
    ("Rowboat",                 100,  50,   "Small boat. 1.5 mph. Crew: 1."),
    ("Sailing Ship",            0,    10000,"Ocean vessel. 2 mph. Crew: 20."),
    ("Warship",                 0,    25000,"Heavy armed vessel. 2.5 mph. Crew: 60."),
    ("Canoe",                   25,   0,    "Small personal watercraft. 3 mph. Crew: 1."),
    # ── Vehicles (air) ────────────────────────────────────────────────────
    ("Cloud Galleon",           0,    40000,"Gargantuan airship. 4 mph. Crew: 15."),
    ("Hot-air Balloon",         0,    7500, "Three-dimensional airborne vehicle. 2 mph. Crew: 1."),
    ("Sky Skiff",               0,    12000,"Small airship. 5 mph. Crew: 2."),
    ("Wind Raider",             0,    20000,"Armed airship (2 ballistae). 5 mph. Crew: 5."),
    # ── Trade Goods ──────────────────────────────────────────────────────
    ("Wheat Flour (1 lb)",      1,    0.01, "Foodstuff. Trade good."),
    ("Salt (1 lb)",             1,    0.05, "Spice/preservative. Trade good."),
    ("Cinnamon (1 lb)",         0.5,  2,    "Spice. Trade good."),
    ("Pepper (1 lb)",           0.5,  2,    "Spice. Trade good."),
    ("Clove (1 lb)",            0.5,  5,    "Spice. Trade good."),
    ("Ginger (1 lb)",           0.5,  1,    "Spice. Trade good."),
    ("Saffron (1 lb)",          0.5,  15,   "Rare spice. Trade good."),
    ("Linen (1 sq yd)",         0.5,  0.5,  "Fabric. Trade good."),
    ("Cotton (1 sq yd)",        0.5,  0.05, "Fabric. Trade good."),
    ("Silk (1 sq yd)",          0.5,  10,   "Luxury fabric. Trade good."),
    ("Velvet (1 sq yd)",        0.5,  5,    "Luxury fabric. Trade good."),
    ("Copper (1 lb)",           1,    0.05, "Metal. Trade good."),
    ("Silver (1 lb)",           1,    5,    "Metal. Trade good."),
    ("Iron (1 lb)",             1,    0.01, "Metal. Trade good."),
    ("Tin (1 lb)",              1,    0.1,  "Metal. Trade good."),
    ("Mithral (1 lb)",          1,    500,  "Rare metal. Trade good."),
    ("Adamantine (1 lb)",       1,    750,  "Legendary metal. Trade good."),
    # ── Spellcasting Components ──────────────────────────────────────────
    ("Pearl",                   0,    100,  "Material component for Identify."),
    ("Diamond (small)",         0,    50,   "Material component for Chromatic Orb."),
    ("Diamond (500 gp+)",       0,    500,  "Material component for Revivify and similar."),
    ("Ruby dust (50 gp)",       0,    50,   "Material component for Continual Flame."),
    ("Mercury, phosphorus, powdered silver & iron",0,500,"Material component for Magic Circle."),
    ("Energy Cell",             0,    50,   "Ammunition for futuristic firearms. 10 shots."),
    ("Bullets (10)",            2,    3,    "Ammunition for Renaissance/Modern firearms."),
    # ── Adventure-specific / unique items ──────────────────────────────────
    ("Adjustable Stilts",       8,    0,    "1 min to don/doff. Increases wearer's height by 2-5 ft."),
    ("Alchemist's Doom (flask)",1,    0,    "Ranged attack (improvised weapon) to throw 20 ft, shattering on impact: hit deals 2d6 fire/turn until DC 10 DEX (action) to extinguish."),
    ("Backpack Parachute",      0,    0,    "Reaction while falling, or action otherwise (needs a 10-ft cube of space): deploy to land with no falling damage if fall is 60+ ft. 10 min to repack."),
    ("Barking Box",             0,    0,    "Action to wind (8 hrs): barks when it detects vibration within 15 ft. Set for small or large dog bark."),
    ("Catapult Munition",       0,    0,    "Thrown 30 ft, explodes: 15-ft radius, 10d6 fire (DEX DC 14 half); unattended objects in the area take 10d6 fire too."),
    ("Ivana's Whisper (poison, inhaled)",0,0,"CON DC 18 or suffer a dream spell (cast by Ivana Boritsi) next time you sleep."),
    ("Matchless Pipe",          0,    0,    "A smoking pipe with a built-in flint switch that lights itself."),
    ("Menga leaves (1 oz)",     0,    2,    "Ingested: regain 1 HP. More than 5 oz/24 hrs: CON DC 11 or unconscious 1 hr (wakes if it takes 5+ damage)."),
    ("Murgaxor's Elixir of Life",0,   0,    "Drink: advantage on death saving throws for 24 hours."),
    ("Nimblewright Detector",   0,    0,    "Hold trigger down: spins/whirs/clicks faster as a nimblewright (other than Nim) within 500 ft gets closer, max at 30 ft."),
    ("Ryath Root",              0,    50,   "Ingested: gain 2d4 temp HP. More than 1/24 hrs: CON DC 13 or poisoned 1 hour."),
    ("Shatterstick",            4,    0,    "Pounded into earth/rock: 1 min seismic vibration in 20-ft radius, then breaks, dealing 10d6 bludgeoning to structures within 20 ft."),
    ("Sinda berries (10)",      0,    5,    "Eating 10+ fresh berries: advantage on saves vs. disease and poison for 24 hours."),
    ("The Incantations of Iriolarthas",3, 0,"Netherese lich Iriolarthas's spellbook — 60 pages containing spells from 1st through 9th level."),
    ("Vial of Stardust",        0,    0,    "Sprinkle over yourself: cast Dream once as an action (DC 15), no components."),
    ("Wildroot",                0,    25,   "Rub the juice on a poisoned creature: cures the poisoned condition. Single use."),
    ("Wukka Nut",               0,    1,    "Shake: shell sheds bright light 10 ft / dim 10 ft more for 1 min. Cracking the shell destroys the magic."),
]

GEAR_NAMES = [g[0] for g in ADVENTURING_GEAR]

VEHICLES_LAND = ["Cart", "Carriage", "Chariot", "Sled", "Wagon"]
VEHICLES_WATER = ["Galley", "Keelboat", "Longship", "Rowboat", "Sailing Ship", "Warship", "Canoe"]
VEHICLES_SPELLJAMMING = ["Bombard", "Damselfly Ship", "Flying Fish Ship", "Hammerhead Ship",
    "Lamprey Ship", "Living Ship", "Nautiloid", "Nightspider", "Scorpion Ship", "Shrike Ship",
    "Space Galleon", "Squid Ship", "Star Moth", "Turtle Ship", "Tyrant Ship", "Wasp Ship"]
VEHICLES_ASTRAL = ["Astral Brig", "Astral Skiff", "Battle Balloon", "Mechanical Beholder", "Planar Raider"]
VEHICLES_AIR = ["Cloud Galleon", "Hot-air Balloon", "Sky Skiff", "Wind Raider"]
VEHICLES_BGDIA = ["Demon Grinder", "Devil's Ride", "Scavenger", "Tormentor", "Venatrix"]
VEHICLES_MAGIC = ["Apparatus of Kwalish", "Tasha's Creeping Keelboat", "Lyrandar Air Cruiser",
    "Lyrandar Skyskiff", "Strider Airship", "Flying Chariot", "Ornithopter of Flying",
    "Bobbing Lily Pad", "Quaal's Feather Token, Swan Boat",
    "Carpet of Flying, 3 ft. × 5 ft.", "Carpet of Flying, 4 ft. × 6 ft.",
    "Carpet of Flying, 5 ft. × 7 ft.", "Carpet of Flying, 6 ft. × 9 ft."]
VEHICLES = (VEHICLES_LAND + VEHICLES_WATER + VEHICLES_SPELLJAMMING + VEHICLES_ASTRAL
            + VEHICLES_AIR + VEHICLES_BGDIA + VEHICLES_MAGIC)



# ── Tools ─────────────────────────────────────────────────────────────────────
ARTISAN_TOOLS = [
    "Alchemist's supplies", "Brewer's supplies", "Calligrapher's supplies",
    "Carpenter's tools", "Cartographer's tools", "Cobbler's tools",
    "Cook's utensils", "Glassblower's tools", "Jeweler's tools",
    "Leatherworker's tools", "Mason's tools", "Painter's supplies",
    "Potter's tools", "Smith's tools", "Tinker's tools",
    "Weaver's tools", "Woodcarver's tools",
]

GAMING_SETS = [
    "Dice set", "Dragonchess set", "Playing card set", "Three-Dragon Ante set",
]

INSTRUMENT_TOOLS = [
    "Bagpipes", "Drum", "Dulcimer", "Flute", "Lute", "Lyre",
    "Horn", "Pan flute", "Shawm", "Viol",
]

OTHER_TOOLS = [
    "Disguise kit", "Forgery kit", "Herbalism kit", "Navigator's tools",
    "Poisoner's kit", "Thieves' tools",
]

VEHICLE_PROFS = ["Vehicles (land)", "Vehicles (water)", "Vehicles (air)"]

ALL_TOOLS = (ARTISAN_TOOLS + GAMING_SETS + INSTRUMENT_TOOLS +
             OTHER_TOOLS + VEHICLE_PROFS)

# ── Mounts & Vehicles ─────────────────────────────────────────────────────────
MOUNTS = [
    ("Camel",      "480 lb",  50,  "—",  50),
    ("Donkey",     "420 lb",  40,  "—",  8),
    ("Elephant",   "1,320 lb",40,  "—",  200),
    ("Horse, Draft","540 lb", 40,  "—",  50),
    ("Horse, Riding","480 lb",60,  "—",  75),
    ("Mastiff",    "195 lb",  40,  "—",  25),
    ("Mule",       "420 lb",  40,  "—",  8),
    ("Pony",       "225 lb",  40,  "—",  30),
    ("Warhorse",   "540 lb",  60,  "—",  400),
]

# ── Racial natural weapons ───────────────────────────────────────────────────
# Merged in from the former natural_weapons.py — traits that let a
# character make an unarmed strike dealing real weapon-style damage (a
# die plus an ability modifier) instead of the standard 1 bludgeoning.
# Drives a real weapon row in the Combat tab for each one, with a
# computed attack bonus and rollable damage, the same treatment given to
# Monk's Martial Arts and Blood Hunter's Hybrid Transformation.
#
# Each race maps to a LIST of weapon dicts (some races, like Naga, have
# more than one distinct natural attack). Each entry: display name,
# damage die, damage type, and the ability score used for the
# attack/damage roll. An optional note documents a rider effect that
# isn't itself a separate attack (shown as a tooltip rather than
# computed, since it's usually a resource-limited bonus action or an
# on-hit condition).
RACIAL_NATURAL_WEAPONS = {
    "Aarakocra": [{"name": "Talons", "die": "1d4", "damage_type": "slashing", "stat": "STR"}],
    "Centaur": [{"name": "Hooves", "die": "1d4", "damage_type": "bludgeoning", "stat": "STR"}],
    "Dhampir": [{"name": "Vampiric Bite", "die": "1d4", "damage_type": "piercing", "stat": "CON",
                 "note": "While at half HP or fewer, advantage on attack rolls with this bite. On a hit against a non-Construct/non-Undead, empower yourself: regain HP equal to the damage dealt, or gain a bonus to your next check/attack equal to it. Uses = proficiency bonus per long rest."}],
    "Leonin": [{"name": "Claws", "die": "1d4", "damage_type": "slashing", "stat": "STR"}],
    "Lizardfolk": [{"name": "Bite", "die": "1d6", "damage_type": "piercing", "stat": "STR",
                     "note": "Hungry Jaws (1/short or long rest): bonus action bite attack; on a hit, gain temporary HP equal to your CON modifier (min 1)."}],
    "Minotaur": [{"name": "Horns", "die": "1d6", "damage_type": "piercing", "stat": "STR"}],
    "Minotaur (MPMM)": [{"name": "Horns", "die": "1d6", "damage_type": "piercing", "stat": "STR"}],
    "Aarakocra (MPMM)": [{"name": "Talons", "die": "1d6", "damage_type": "slashing", "stat": "STR"}],
    "Centaur (MPMM)": [{"name": "Hooves", "die": "1d6", "damage_type": "bludgeoning", "stat": "STR"}],
    "Lizardfolk (MPMM)": [{"name": "Bite", "die": "1d6", "damage_type": "slashing", "stat": "STR",
                     "note": "Hungry Jaws (1/short or long rest): bonus action bite attack; on a hit, gain temporary HP equal to your proficiency bonus."}],
    "Satyr (MPMM)": [{"name": "Ram", "die": "1d6", "damage_type": "bludgeoning", "stat": "STR"}],
    "Tabaxi (MPMM)": [{"name": "Cat's Claws", "die": "1d6", "damage_type": "slashing", "stat": "STR"}],
    "Tortle (MPMM)": [{"name": "Claws", "die": "1d6", "damage_type": "slashing", "stat": "STR"}],
    "Tabaxi": [{"name": "Cat's Claws", "die": "1d4", "damage_type": "slashing", "stat": "STR"}],
    "Tortle": [{"name": "Claws", "die": "1d4", "damage_type": "slashing", "stat": "STR"}],
    "Naga": [
        {"name": "Bite", "die": "1d4", "damage_type": "piercing", "stat": "STR",
         "note": "Target makes a CON save (DC 8+PB+CON mod) or takes an extra 1d4 poison damage."},
        {"name": "Constrict", "die": "1d6", "damage_type": "bludgeoning", "stat": "STR",
         "note": "Target is grappled (escape DC 8+PB+STR mod) and restrained until the grapple ends; you can't constrict a second target at the same time."},
    ],
}
