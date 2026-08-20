"""
Creature stat blocks — mounts, companions, summoned creatures, and Wild
Shape beast forms. Merged from four formerly-separate files
(mount_statblocks.py, companions.py, summon_spells.py, wildshape_beasts.py)
into one, since they were small, related, and frequently needed together.

Sections below, each preserving its original file's docstring content
inline as comments:
  - MOUNT_STATBLOCKS / MOUNT_NAME_ALIASES / get_mount_statblock()
  - COMPANION_STATBLOCKS / ELDRITCH_CANNON
  - FIND_GREATER_STEED_OPTIONS / SCALING_SUMMONS / resolve_scaling_summon()
  - WILDSHAPE_BEASTS

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ═════════════════════════════════════════════════════════════════════════════
# Mounts
# ═════════════════════════════════════════════════════════════════════════════

MOUNT_STATBLOCKS = {
    "Camel": {
        "cr": 0.125, "cr_label": "1/8", "size": "Large",
        "ac": 9, "ac_note": "", "hp": 15, "hit_dice": "2d10+4",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 16, "DEX": 8, "CON": 14, "INT": 2, "WIS": 8, "CHA": 5},
        "skills": [], "senses": "passive Perception 9", "traits": [],
        "actions": [("Bite", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d4+3 bludgeoning damage.")],
    },
    "Donkey/Mule": {
        "cr": 0.125, "cr_label": "1/8", "size": "Medium",
        "ac": 10, "ac_note": "", "hp": 4, "hit_dice": "1d8",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 11, "DEX": 10, "CON": 11, "INT": 2, "WIS": 10, "CHA": 5},
        "skills": [], "senses": "passive Perception 10",
        "traits": [("Beast of Burden", "The mule is considered to be carrying a load of 1.5x the weight it can normally push, drag, or lift when determining its carrying capacity."),
                   ("Sure-Footed", "Advantage on STR and DEX saves made against being knocked prone.")],
        "actions": [("Hooves", "Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 1d2+1 bludgeoning damage.")],
    },
    "Elephant": {
        "cr": 4, "cr_label": "4", "size": "Huge",
        "ac": 12, "ac_note": "natural armor", "hp": 76, "hit_dice": "8d12+24",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 22, "DEX": 9, "CON": 17, "INT": 3, "WIS": 11, "CHA": 6},
        "skills": [], "senses": "passive Perception 10",
        "traits": [("Trampling Charge", "If the elephant moves at least 20 ft straight toward a creature and hits it with a gore attack, the target must succeed a DC 12 STR save or be knocked prone; if prone, the elephant can make one stomp attack against it as a bonus action.")],
        "actions": [
            ("Gore", "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 3d8+6 piercing damage."),
            ("Stomp", "Melee Weapon Attack: +8 to hit, reach 5 ft., one prone creature. Hit: 3d10+6 bludgeoning damage."),
        ],
    },
    "Draft Horse": {
        "cr": 0.25, "cr_label": "1/4", "size": "Large",
        "ac": 10, "ac_note": "", "hp": 19, "hit_dice": "3d10+3",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 18, "DEX": 10, "CON": 12, "INT": 2, "WIS": 11, "CHA": 7},
        "skills": [], "senses": "passive Perception 10", "traits": [],
        "actions": [("Hooves", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 2d4+4 bludgeoning damage.")],
    },
    "Riding Horse": {
        "cr": 0.25, "cr_label": "1/4", "size": "Large",
        "ac": 10, "ac_note": "", "hp": 13, "hit_dice": "2d10+2",
        "speed": "60 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 16, "DEX": 10, "CON": 12, "INT": 2, "WIS": 11, "CHA": 7},
        "skills": [], "senses": "passive Perception 10", "traits": [],
        "actions": [("Hooves", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 2d4+3 bludgeoning damage.")],
    },
    "Mastiff": {
        "cr": 0.125, "cr_label": "1/8", "size": "Medium",
        "ac": 12, "ac_note": "", "hp": 5, "hit_dice": "1d8+1",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 13, "DEX": 14, "CON": 12, "INT": 3, "WIS": 12, "CHA": 7},
        "skills": [("Perception", "+3")], "senses": "passive Perception 13",
        "traits": [("Keen Hearing and Smell", "Advantage on WIS (Perception) checks that rely on hearing or smell.")],
        "actions": [("Bite", "Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 1d4+1 piercing damage; if target is a creature, DC 11 STR save or be knocked prone.")],
    },
    "Pony": {
        "cr": 0.125, "cr_label": "1/8", "size": "Medium",
        "ac": 10, "ac_note": "", "hp": 11, "hit_dice": "2d8+2",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 15, "DEX": 13, "CON": 12, "INT": 2, "WIS": 11, "CHA": 7},
        "skills": [], "senses": "passive Perception 10", "traits": [],
        "actions": [("Hooves", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d4+2 bludgeoning damage.")],
    },
    "Warhorse": {
        "cr": 0.5, "cr_label": "1/2", "size": "Large",
        "ac": 11, "ac_note": "", "hp": 19, "hit_dice": "3d10+3",
        "speed": "60 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 18, "DEX": 12, "CON": 13, "INT": 2, "WIS": 12, "CHA": 7},
        "skills": [], "senses": "passive Perception 11", "traits": [],
        "actions": [
            ("Hooves", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 2d6+4 bludgeoning damage."),
        ],
    },
    "Elk": {
        "cr": 0.25, "cr_label": "1/4", "size": "Large",
        "ac": 10, "ac_note": "", "hp": 13, "hit_dice": "2d10+2",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 16, "DEX": 10, "CON": 12, "INT": 2, "WIS": 10, "CHA": 6},
        "skills": [], "senses": "passive Perception 10",
        "traits": [("Charge", "If the elk moves at least 20 ft straight toward a target and hits it with a ram attack on the same turn, the target takes an extra 2d6 damage. If the target is a creature, it must succeed on a DC 13 STR save or be knocked prone.")],
        "actions": [
            ("Ram", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d6+3 bludgeoning damage."),
            ("Hooves", "Melee Weapon Attack: +5 to hit, reach 5 ft., one prone creature. Hit: 2d4+3 bludgeoning damage."),
        ],
    },
}

# Maps the equipment-list mount names (which include Donkey/Mule as one
# entry in some catalogs) onto the stat block keys above.
MOUNT_NAME_ALIASES = {
    "Donkey": "Donkey/Mule",
    "Mule": "Donkey/Mule",
    "Horse, Draft": "Draft Horse",
    "Horse, Riding": "Riding Horse",
}

# ── Vehicle stat blocks (water + land) ───────────────────────────────────────
# Water vehicles: full Ghosts of Saltmarsh stat blocks (Hull AC/HP as the
# primary combat stat, ability scores, immunities, and the complete
# Helm/Oars/Sails/Weapons/Naval-Ram component breakdown as traits).
# Land vehicles (Cart, Carriage, Chariot, Sled, Wagon): no core PHB/DMG/
# Ghosts of Saltmarsh source gives these any AC/HP at all — the combat
# stats here come from a supplementary alternate vehicle-rules table
# (distinct from, and not fully consistent with, core 5e content) rather
# than an official WotC sourcebook. Cost/weight for these still live in
# ADVENTURING_GEAR (items.py) using the official PHB figures, since this
# alternate table's weight values conflict with those and PHB takes
# priority for that specific data.
VEHICLE_STATBLOCKS = {
    "Galley": {
        "size": "Gargantuan", "ac": 15, "hp": 500, "speed": "4 mph (96 miles/day)",
        "cargo": "150 tons", "crew": "80", "passengers": "40",
        "abilities": {"STR": 24, "DEX": 4, "CON": 20, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 20 or less."),
            ("Helm", "AC 16, HP 50. Move up to the speed of one movement component, one 90\u00b0 turn. "
                      "If destroyed, the galley can't turn."),
            ("Oars", "AC 12, HP 100. Speed (water) 30 ft. (requires at least 40 crew)."),
            ("Sails", "AC 12, HP 100. Speed (water) 35 ft.; 15 ft. into the wind; 50 ft. with the wind."),
            ("Weapon: Ballista (4)", "AC 15, HP 50 each. +6 to hit, range 120/480 ft. Hit: 16 (3d10) piercing."),
            ("Weapon: Mangonel (2)", "AC 15, HP 100 each. +5 to hit, range 200/800 ft. (can't hit within "
                                      "60 ft.). Hit: 27 (5d10) bludgeoning."),
            ("Naval Ram", "AC 20, HP 100 (threshold 10). Advantage on saves related to crashing when it "
                           "rams; crash damage applies to the ram instead of the hull (unless another "
                           "vessel rams the galley)."),
        ],
        "actions": [
            ("Actions (crew-scaled)", "3 actions/turn with 40+ crew, 2 with 20-39, 1 with 3-19; none below 3."),
            ("Fire Ballistas / Fire Mangonels", "Fire the mounted siege weapons."),
            ("Move", "Use its helm to move with oars or sails; can use its naval ram as part of this."),
        ],
    },
    "Keelboat": {
        "size": "Gargantuan", "ac": 15, "hp": 100, "speed": "3 mph (72 miles/day)",
        "cargo": "0.5 tons", "crew": "3", "passengers": "4",
        "abilities": {"STR": 16, "DEX": 7, "CON": 13, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 10 or less."),
            ("Helm", "AC 12, HP 50. Move up to the speed of one movement component, one 90\u00b0 turn. "
                      "If destroyed, the keelboat can't turn."),
            ("Oars", "AC 12, HP 100; -5 ft. speed per 20 damage taken. Speed (water) 20 ft."),
            ("Sails", "AC 12, HP 50; -5 ft. speed per 20 damage taken. Speed (water) 25 ft.; 15 ft. into "
                       "the wind; 35 ft. with the wind."),
            ("Weapon: Ballista", "AC 15, HP 50 (only if equipped for combat). +6 to hit, range 120/480 ft. "
                                  "Hit: 16 (3d10) piercing."),
        ],
        "actions": [
            ("Actions (crew-scaled)", "2 actions/turn with crew, 1 with only 1 crew; none with no crew."),
            ("Fire Ballistas", "Fire the mounted ballista, if equipped."),
            ("Move", "Use its helm to move with oars or sails."),
        ],
    },
    "Longship": {
        "size": "Gargantuan", "ac": 15, "hp": 300, "speed": "5 mph (120 miles/day)",
        "cargo": "10 tons", "crew": "40", "passengers": "100",
        "abilities": {"STR": 20, "DEX": 6, "CON": 17, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
            ("Helm", "AC 16, HP 50. Move up to the speed of one movement component, one 90\u00b0 turn. "
                      "If destroyed, the longship can't turn."),
            ("Oars", "AC 12, HP 100; -5 ft. speed per 25 damage taken. Speed (water) 20 ft. "
                      "(requires at least 20 crew)."),
            ("Sails", "AC 12, HP 100; -10 ft. speed per 25 damage taken. Speed (water) 45 ft.; 15 ft. "
                       "into the wind; 60 ft. with the wind."),
        ],
        "actions": [
            ("Move", "Use its helm to move with oars or sails (only action available; requires crew)."),
        ],
    },
    "Rowboat": {
        "size": "Large", "ac": 11, "hp": 50, "speed": "3 mph (72 miles/day)",
        "cargo": "0.2 tons", "crew": "2", "passengers": "2",
        "abilities": {"STR": 11, "DEX": 8, "CON": 11, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Oars", "AC 12, HP 25. Speed (water) 15 ft. Move up to the boat's speed, one 90\u00b0 turn. "
                      "Without oars, speed is 0."),
        ],
        "actions": [
            ("Move", "Use its oars to move (only action available; requires crew)."),
        ],
    },
    "Sailing Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 300, "speed": "5 mph (120 miles/day)",
        "cargo": "100 tons", "crew": "30", "passengers": "20",
        "abilities": {"STR": 20, "DEX": 7, "CON": 17, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
            ("Helm", "AC 18, HP 50. Move up to the speed of the ship's sails, one 90\u00b0 turn. "
                      "If destroyed, the ship can't turn."),
            ("Sails", "AC 12, HP 100; -5 ft. speed per 25 damage taken. Speed (water) 45 ft.; 15 ft. "
                       "into the wind; 60 ft. with the wind."),
            ("Weapon: Ballista", "AC 15, HP 50. +6 to hit, range 120/480 ft. Hit: 16 (3d10) piercing."),
            ("Weapon: Mangonel", "AC 15, HP 100. +5 to hit, range 200/800 ft. (can't hit within 60 ft.). "
                                   "Hit: 27 (5d10) bludgeoning."),
        ],
        "actions": [
            ("Actions (crew-scaled)", "3 actions/turn with 20+ crew, 2 with 10-19, 1 with 3-9; none below 3."),
            ("Fire Ballistas / Fire Mangonel", "Fire the mounted siege weapons."),
            ("Move", "Use its helm to move with its sails."),
        ],
    },
    "Warship": {
        "size": "Gargantuan", "ac": 15, "hp": 500, "speed": "4 mph (96 miles/day)",
        "cargo": "200 tons", "crew": "40", "passengers": "60",
        "abilities": {"STR": 20, "DEX": 4, "CON": 20, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 20 or less."),
            ("Helm", "AC 18, HP 50. Move up to the speed of one movement component, one 90\u00b0 turn. "
                      "If destroyed, the warship can't turn."),
            ("Oars", "AC 12, HP 100; -5 ft. speed per 25 damage taken. Speed (water) 20 ft. "
                      "(requires at least 20 crew)."),
            ("Sails", "AC 12, HP 100; -10 ft. speed per 25 damage taken. Speed (water) 35 ft.; 15 ft. "
                       "into the wind; 50 ft. with the wind."),
            ("Weapon: Ballista (2)", "AC 15, HP 50 each. +6 to hit, range 120/480 ft. Hit: 16 (3d10) piercing."),
            ("Weapon: Mangonel (2)", "AC 15, HP 100 each. +5 to hit, range 200/800 ft. (can't hit within "
                                      "60 ft.). Hit: 27 (5d10) bludgeoning."),
            ("Naval Ram", "AC 20, HP 100 (threshold 10). Advantage on saves related to crashing when it "
                           "rams; crash damage applies to the ram instead of the hull (unless another "
                           "vessel rams the warship)."),
        ],
        "actions": [
            ("Actions (crew-scaled)", "3 actions/turn with 20+ crew, 2 with 10-19, 1 with 3-9; none below 3."),
            ("Fire Ballistas / Fire Mangonels", "Fire the mounted siege weapons."),
            ("Move", "Use its helm to move with oars or sails; can use its naval ram as part of this."),
        ],
    },
    "Canoe": {
        "size": "Large", "ac": 12, "hp": 30, "speed": "3 mph (30 ft./round)",
        "crew": "1", "passengers": "-",
        "traits": [("Special", "Personal vehicle.")],
        "actions": [],
    },
    "Cart": {
        "size": "Large", "ac": 11, "hp": 30, "speed": "drawn (set by the animal(s) pulling it)",
        "crew": "1", "supply": "40",
        "traits": [("Special", "Drawn — speed and travel pace are determined by the animal(s) pulling it.")],
        "actions": [],
    },
    "Carriage": {
        "size": "Large", "ac": 15, "hp": 120, "speed": "drawn (set by the animal(s) pulling it)",
        "crew": "1", "supply": "40",
        "traits": [("Special", "Drawn — speed and travel pace are determined by the animal(s) pulling it.")],
        "actions": [],
    },
    "Chariot": {
        "size": "Large", "ac": 16, "hp": 50, "speed": "drawn (set by the animal(s) pulling it)",
        "crew": "1", "supply": "40",
        "traits": [("Special", "Drawn, personal — speed and travel pace are determined by the animal(s) "
                                "pulling it; carries at most one occupant.")],
        "actions": [],
    },
    "Sled": {
        "size": "Large", "ac": 12, "hp": 40, "speed": "drawn (set by the animal(s) pulling it)",
        "crew": "1", "supply": "40",
        "traits": [("Special", "Drawn, personal — speed and travel pace are determined by the animal(s) "
                                "pulling it; carries at most one occupant.")],
        "actions": [],
    },
    "Wagon": {
        "size": "Huge", "ac": 12, "hp": 80, "speed": "drawn (set by the animal(s) pulling it)",
        "crew": "1", "supply": "80",
        "traits": [("Special", "Drawn — speed and travel pace are determined by the animal(s) pulling it.")],
        "actions": [],
    },
}


# ── Air vehicles (alternate/supplementary vehicle rules) ────────────────────
# A distinct category — cloud galleon, hot-air balloon, sky skiff, and wind
# raider aren't in any core PHB/DMG/Ghosts of Saltmarsh table; they come from
# the same alternate vehicle-rules table that supplied the land vehicle
# combat stats above.
VEHICLE_STATBLOCKS_AIR = {
    "Cloud Galleon": {
        "size": "Gargantuan", "ac": 14, "hp": 300, "speed": "4 mph (40 ft./round)",
        "crew": "15", "supply": "800",
        "traits": [("Special", "Transport (double the normal cargo/passenger capacity for its size), "
                                "Three-Dimensional (can also turn up or down when maneuvering).")],
        "actions": [],
    },
    "Hot-air Balloon": {
        "size": "Large", "ac": 10, "hp": 40, "speed": "2 mph (20 ft./round)",
        "crew": "1", "supply": "40",
        "traits": [("Special", "Three-Dimensional (can also turn up or down when maneuvering).")],
        "actions": [],
    },
    "Sky Skiff": {
        "size": "Huge", "ac": 12, "hp": 60, "speed": "5 mph (50 ft./round)",
        "crew": "2", "supply": "80",
        "traits": [("Special", "Three-Dimensional (can also turn up or down when maneuvering).")],
        "actions": [],
    },
    "Wind Raider": {
        "size": "Gargantuan", "ac": 15, "hp": 180, "speed": "5 mph (50 ft./round)",
        "crew": "5", "supply": "800",
        "traits": [("Special", "Three-Dimensional (can also turn up or down when maneuvering).")],
        "actions": [("Weapons: Ballista (2)", "Armed with two ballistae (DMG, ch. 8).")],
    },
}


# ── Spelljamming vehicle stat blocks (Astral Adventurer's Guide) ────────────
# From the official "Spelljamming Vehicles Overview" table, plus each ship's
# descriptive flavor text (kept as a "Description" trait entry). These are
# built by various factions (giff, neogi, mind flayers, beholders, astral
# elves, etc.) for travel through the Astral Sea/Wildspace rather than
# ordinary sea travel — a different category from the mundane Basic Rules
# waterborne vehicles above, hence the separate dict.
VEHICLE_STATBLOCKS_SPELLJAMMING = {
    "Bombard": {
        "size": "Gargantuan", "ac": 15, "hp": 300, "speed": "fly 35 ft. (4 mph)",
        "cargo": "150 tons", "crew": "12", "keel_beam": "140 ft./30 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 20 or less."),
                   ("Description", "Built by giff. The major feature of each ship is an enormous cannon "
                    "that fires massive cannon balls capable of blowing other ships to smithereens (the "
                    "cannon is included in the cost of the ship). A bombard can carry up to fourteen giant "
                    "cannon balls, each weighing 10 tons; a winch on the aft deck loads them. Can float and "
                    "sail on water, but can't land safely on the ground (its keel would cause it to roll).")],
        "actions": [("Weapons", "2 Ballistae, Giant Cannon")],
    },
    "Damselfly Ship": {
        "size": "Gargantuan", "ac": 19, "hp": 200, "speed": "fly 70 ft. (8 mph)",
        "cargo": "5 tons", "crew": "9", "keel_beam": "100 ft./20 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Often used as courier vessels and armored transports; fast and sturdy, "
                    "also favored as command ships. Owners are fond of colorful paint jobs and customization, "
                    "and often gather to race one another through asteroid belts and other obstacle courses.")],
        "actions": [("Weapons", "Ballista, Mangonel+")],
    },
    "Flying Fish Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 250, "speed": "fly 40 ft. (4.5 mph)",
        "cargo": "13 tons", "crew": "10", "keel_beam": "120 ft./30 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Aside from space galleons, the most common vessels in Wildspace, "
                    "favored by merchants and adventurers alike. Can float and sail on water, but isn't "
                    "built to land on the ground (the ventral fins would snap, and the keel would cause "
                    "it to roll to one side). Typically mounts a forward mangonel and an aft ballista.")],
        "actions": [("Weapons", "Ballista, Mangonel")],
    },
    "Hammerhead Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 400, "speed": "fly 35 ft. (4 mph)",
        "cargo": "30 tons", "crew": "15", "keel_beam": "250 ft./25 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Popular among pirates and merchants carrying heavy cargo. Can float on "
                    "water and sail across it, but isn't built to land on the ground (its keel would cause "
                    "it to tip to one side). Standard weapons: fore and aft mangonels, a ballista, and a "
                    "reinforced bow for ramming.")],
        "actions": [("Weapons", "Ballista, Blunt Ram, 2 Mangonels")],
    },
    "Lamprey Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 250, "speed": "fly 35 ft. (4 mph)",
        "cargo": "6 tons", "crew": "15", "keel_beam": "115 ft./25 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Among the oldest spelljamming ship designs still in use, particularly "
                    "favored by psurlons. Metal grappling jaws on the bow let it latch onto another ship "
                    "during boarding actions. Can float on water but can't land safely on the ground — "
                    "lamprey ships that try have the distressing habit of rolling over.")],
        "actions": [("Weapons", "4 Ballistae, Grappling Jaws")],
    },
    "Living Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 250, "speed": "fly 40 ft. (4.5 mph)",
        "cargo": "10 tons", "crew": "5 (+ treant)", "keel_beam": "80 ft./20 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Bonded Treant", "A fully-grown treant is bonded to the aft deck, roots woven into it "
                    "(speed 0, inseparable from the ship). If the ship drops to 0 HP, the treant dies of "
                    "shock; the ship can still function if the treant dies, but it can never be replaced. "
                    "When the treant finishes a long rest, the ship regains 4d12 HP and its air envelope "
                    "refreshes (deadly air \u2192 foul air, or foul air \u2192 fresh air)."),
                   ("Description", "Favored by druids, rangers, nature clerics, and explorers who don't want "
                    "to worry about a fouled air envelope on a long voyage. Can float and sail on water, but "
                    "can't land safely on the ground (its keel would cause it to roll on its side).")],
        "actions": [("Weapons", "Ballista")],
    },
    "Nautiloid": {
        "size": "Gargantuan", "ac": 15, "hp": 400, "speed": "fly 40 ft. (4.5 mph)",
        "cargo": "17 tons", "crew": "20", "keel_beam": "180 ft./30 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Plane Shift", "As an action, a creature attuned to the ship's spelljamming helm and in "
                    "physical contact with it can transport the nautiloid and everyone/everything aboard to "
                    "a different plane, near an envisioned destination (or a random spot on the plane with "
                    "none envisioned). Roll a d6 each use: on a 5-6 it recharges after 1 minute, otherwise "
                    "it can't be used again for 24 hours."),
                   ("Description", "Built and used exclusively by mind flayers for space travel. Can't float "
                    "on water, nor land safely on the ground.")],
        "actions": [("Weapons", "4 Ballistae, Mangonel, Tentacles")],
    },
    "Nightspider": {
        "size": "Gargantuan", "ac": 19, "hp": 300, "speed": "fly 40 ft. (4.5 mph)",
        "cargo": "50 tons", "crew": "25", "keel_beam": "175 ft./50 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Built by neogi to terrorize Wildspace, often lying in ambush before "
                    "trying to steal a target ship's spelljamming helm and capture its crew (typically 19 "
                    "neogi plus up to a half-dozen umber hulk shock troops). Designed for space travel "
                    "alone — can't float on water or land safely on the ground (the weight would snap its "
                    "spindly legs and destroy its weblike rigging).")],
        "actions": [("Weapons", "4 Ballistae, Mangonel")],
    },
    "Scorpion Ship": {
        "size": "Gargantuan", "ac": 19, "hp": 250, "speed": "30 ft. (3.5 mph), fly 30 ft. (3.5 mph)",
        "cargo": "12 tons", "crew": "12", "keel_beam": "75 ft./25 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "An archaic but perennially popular metal warship prized for its "
                    "versatility. Articulated legs let it land safely on the ground and walk at 30 ft., "
                    "though it can't float on water. Its claws are relatively weak in combat but can quickly "
                    "take a grabbed creature out of the fight.")],
        "actions": [("Weapons", "Ballista, 2 Claws, Mangonel")],
    },
    "Shrike Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 250, "speed": "fly 70 ft. (8 mph)",
        "cargo": "20 tons", "crew": "11", "keel_beam": "100 ft./20 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "A relatively recent, swift design popular with merchants and pirates. "
                    "Its legs let it land safely on the ground; it can float but isn't built for water "
                    "travel and sinks quickly in rough seas. Its reinforced bow can be used as a piercing "
                    "ram in a pinch.")],
        "actions": [("Weapons", "3 Ballistae, Piercing Ram")],
    },
    "Space Galleon": {
        "size": "Gargantuan", "ac": 15, "hp": 400, "speed": "fly 35 ft. (4 mph)",
        "cargo": "20 tons", "crew": "20", "keel_beam": "130 ft./30 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "A mainstay of Wildspace and the Astral Sea, easily mistaken for an "
                    "ordinary seafaring galleon; can land on water and move across it like one, letting it "
                    "sail into terrestrial ports without attracting attention. Not built to land on solid "
                    "ground (its keel would cause it to roll on its side).")],
        "actions": [("Weapons", "2 Ballistae, Mangonel")],
    },
    "Squid Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 300, "speed": "fly 30 ft. (3.5 mph)",
        "cargo": "20 tons", "crew": "13", "keel_beam": "250 ft./25 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Among the oldest spelljamming vessel types, popular with privateers and "
                    "as patrol ships. Its bow tentacles account for nearly half the ship's keel length. Can "
                    "float and sail on water, and can land on the ground.")],
        "actions": [("Weapons", "3 Ballistae, Mangonel, Piercing Ram")],
    },
    "Star Moth": {
        "size": "Gargantuan", "ac": 13, "hp": 400, "speed": "fly 50 ft. (5.5 mph)",
        "cargo": "30 tons", "crew": "13", "keel_beam": "200 ft./20 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Constructed and flown by astral elves, who don't take kindly to these "
                    "ships ending up in others' hands. Hull is a grown, sculpted organic substance; its "
                    "decorative wings are shimmering crystal. Built for space travel, but can also float on "
                    "water or land safely on the ground.")],
        "actions": [("Weapons", "2 Ballistae, Mangonel")],
    },
    "Turtle Ship": {
        "size": "Gargantuan", "ac": 19, "hp": 300, "speed": "25 ft. (3 mph), fly 25 ft. (3 mph)",
        "cargo": "30 tons", "crew": "16", "keel_beam": "95 ft./70 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "Encased in a protective metal shell and bristling with weapons; roomy "
                    "and cargo-capable, making it popular with traders. Can land on the ground and floats on "
                    "water; sliding panels seal the hull airtight for safe underwater travel to great depths "
                    "(sealed interior hatches keep it from flooding if damaged on/under the water). Weapons "
                    "can't be used while submerged.")],
        "actions": [("Weapons", "3 Ballistae, Mangonel")],
    },
    "Tyrant Ship": {
        "size": "Gargantuan", "ac": 17, "hp": 300, "speed": "fly 40 ft. (4.5 mph)",
        "cargo": "20 tons", "crew": "10 (beholders)", "keel_beam": "100 ft./100 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 20 or less."),
                   ("Beholder Helm", "A spherical chamber on the command deck is a spelljamming helm only "
                    "beholders can attune to. Reducing the ship to 0 HP destroys it along with the helm and "
                    "its eyestalk cannons."),
                   ("Description", "Carved by beholders from stone using their disintegration rays, then "
                    "flown across the Astral Plane hunting for worlds to conquer and rival beholders to "
                    "destroy. No two look alike, but each bears features reminiscent of its beholder "
                    "creator. Can't float on water, but can safely land on the ground.")],
        "actions": [("Weapons", "3 Eyestalk Cannons")],
    },
    "Wasp Ship": {
        "size": "Gargantuan", "ac": 15, "hp": 250, "speed": "fly 50 ft. (5.5 mph)",
        "cargo": "10 tons", "crew": "5", "keel_beam": "80 ft./20 ft.",
        "traits": [("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
                   ("Description", "A lightweight wooden vessel that can land safely on the ground but not "
                    "on water. Affordable and low-crew, appealing to adventurers; swift enough for pirates; "
                    "and popular with aristocrats as flying yachts, since its cargo hold converts easily "
                    "into posh living quarters. Its raised back provides high ground for a weapon "
                    "emplacement, typically a ballista.")],
        "actions": [("Weapons", "Ballista")],
    },
}


# ── Astral Plane vehicles (Mordenkainen's Tome of Foes / Astral Adventurer's
# Guide) ──────────────────────────────────────────────────────────────────
# A distinct category from the Spelljamming ships above — these don't have
# Spelljamming helms or keel/beam dimensions. Astral Brig, Astral Skiff, and
# Planar Raider (MTF) are simpler entries with no AC/HP/ability scores given
# in their source at all (marked "no_combat_stats" rather than inventing
# numbers); Battle Balloon and Mechanical Beholder (Astral Adventurer's
# Guide) have full stat blocks matching the detail level of the water
# vehicles above.
VEHICLE_STATBLOCKS_ASTRAL = {
    "Astral Brig": {
        "size": "Gargantuan", "no_combat_stats": True, "speed": "12 mph (288 miles/day)",
        "crew": "5", "passengers": "60",
        "traits": [("Dimensions", "90 ft. by 30 ft.")],
        "actions": [("Weapons: Ballistas (2)", "+6 to hit, range 120/480 ft., one target. "
                                                 "Hit: 16 (3d10) piercing damage.")],
    },
    "Astral Skiff": {
        "size": "Huge", "no_combat_stats": True, "speed": "15 mph (360 miles/day)",
        "crew": "3", "passengers": "12",
        "traits": [("Dimensions", "30 ft. by 10 ft.")],
        "actions": [],
    },
    "Battle Balloon": {
        "size": "Gargantuan", "ac": 15, "hp": 500, "speed": "9 mph (216 miles/day)",
        "cargo": "1 ton", "crew": "20", "passengers": "10",
        "abilities": {"STR": 18, "DEX": 17, "CON": 20, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Dimensions", "80 ft. by 20 ft."),
            ("Damage Threshold", "Immune to damage from any single hit that deals 15 or less."),
            ("Control: Helm", "AC 18, HP 50. Move up to the speed of the propeller, one 90\u00b0 turn. "
                               "If destroyed, the ship can't turn."),
            ("Control: Balloon", "AC 12, HP 75. If destroyed, the battle balloon can't maintain altitude."),
            ("Movement: Propeller", "AC 12, HP 100; -5 ft. speed per 25 damage taken. Speed (air) 80 ft.; "
                                     "50 ft. into the wind; 100 ft. with the wind."),
            ("Weapons: Green Flame Arbalester", "AC 15, HP 75. +8 to hit, range 200/800 ft. (can't hit "
             "within 60 ft.). Hit: 16 (3d10) piercing + 22 (4d10) fire. On a miss, the bolt shatters near "
             "its impact point; each creature within 10 ft. makes a DC 15 DEX save, taking 5 (1d10) "
             "piercing + 5 (1d10) fire on a failure."),
            ("Weapons: Harpoon Gun (3)", "AC 15, HP 50 each. +8 to hit, range 120/480 ft. Hit: 11 (2d10) "
             "piercing, target grappled (escape DC 16); its speed is halved and it can't move farther "
             "from the balloon until the grapple ends. While it has a target grappled this way, the "
             "battle balloon's own speed isn't halved."),
        ],
        "actions": [
            ("Actions (crew-scaled)", "3 actions/turn with 20+ crew, 2 with 10-19, 1 with <10; none with no crew."),
            ("Fire Ballista / Fire Green Flame Arbalester", "Fire the mounted weapons."),
            ("Move", "Use its helm to move via its propeller. If it enters a Large or smaller creature's "
                      "space, that creature is pushed to the space's edge and makes a DC 15 DEX save, "
                      "taking 5 (1d10) bludgeoning on a failure."),
            ("Harpoon Haul", "Pull each creature grappled by its harpoon guns up to 30 ft. toward it."),
        ],
    },
    "Mechanical Beholder": {
        "size": "Huge", "ac": 18, "hp": 200, "speed": "3 mph (72 miles/day)",
        "cargo": "crew and passengers' normal gear", "crew": "1", "passengers": "5",
        "abilities": {"STR": 18, "DEX": 12, "CON": 18, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, exhaustion, frightened, incapacitated, "
                                 "paralyzed, petrified, poisoned, prone, stunned, unconscious",
        "traits": [
            ("Dimensions", "15 ft. by 15 ft."),
            ("Damage Threshold", "Immune to damage from any single hit that deals 10 or less."),
            ("Control: Helm", "AC 16, HP 25. Move up to the speed of the propulsion unit, one 90\u00b0 turn. "
                               "Can only be attacked once the hull has taken 100+ damage. If destroyed, "
                               "the mechanical beholder can't move."),
            ("Movement: Magical Propulsion Unit", "AC 16, HP 100; -5 ft. speed per 25 damage taken. "
             "Speed (magical): burrow 30 ft., fly 30 ft. (hover), swim 30 ft."),
            ("Weapons: Eye Ray Tentacles (6)", "AC 14, HP 50 each. Fires eye rays at up to three targets "
             "within 120 ft. that would be visible to the crew: Disintegration Ray (DC 15 DEX save or 18 "
             "(4d8) force damage; a creature reduced to 0 HP this way is turned to dust; Large or smaller "
             "nonmagical objects/magical force effects are disintegrated outright, Huge+ ones lose a "
             "10-ft. cube), Enervation Ray (DC 15 CON save, 18 (4d8) necrotic, half on success), or "
             "Paralyzing Ray (DC 15 CON save or paralyzed 1 minute, repeating the save each turn)."),
        ],
        "actions": [
            ("Actions", "1 action/turn if it has crew; none with no crew."),
            ("Eye Rays", "Use its eye ray tentacles."),
            ("Move", "Use its helm to move via its magical propulsion unit."),
        ],
    },
    "Planar Raider": {
        "size": "Huge", "no_combat_stats": True, "speed": "12 mph (288 miles/day)",
        "crew": "10", "passengers": "100",
        "traits": [("Dimensions", "120 ft. by 40 ft.")],
        "actions": [
            ("Weapons: Ballistas (2)", "+6 to hit, range 120/480 ft., one target. Hit: 16 (3d10) piercing."),
            ("Weapons: Catapult", "+5 to hit, range 200/800 ft. (can't hit within 60 ft.), one target. "
                                    "Hit: 27 (5d10) bludgeoning."),
        ],
    },
}


# ── Bigby Presents: Glory of the Giants combat vehicles ──────────────────────
# Purpose-built for chase scenes and vehicular combat, distinct from the
# travel-focused vehicles above. "Action Station" crew/cover requirements are
# folded into each action's description text.
VEHICLE_STATBLOCKS_BGDIA = {
    "Demon Grinder": {
        "size": "Gargantuan", "ac": 19, "hp": 200, "speed": "100 ft. (10 mph, 240 miles/day)",
        "crew": "capacity 8 Medium creatures", "cargo": "1 ton",
        "abilities": {"STR": 18, "DEX": 10, "CON": 18, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "fire, poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, frightened, paralyzed, petrified, "
                                 "poisoned, stunned, unconscious",
        "traits": [
            ("Damage/Mishap Threshold", "Threshold 10; rolls on the Mishap table at threshold 20."),
            ("Crushing Wheels", "Can move through the space of any Large or smaller creature; that "
             "creature makes a DC 11 DEX save or takes 22 (4d10) bludgeoning and is knocked prone "
             "(extra 22 (4d10) if already prone). Can't affect the same creature more than once/turn."),
            ("Magic Weapons", "The Demon Grinder's weapon attacks are magical."),
            ("Prone Deficiency", "If it rolls over and falls prone, it can't right itself and is "
                                  "incapacitated until flipped upright."),
        ],
        "actions": [
            ("Helm (1 crew, three-quarters cover)", "Drive and steer the Demon Grinder."),
            ("Chomper (1 crew, half cover)", "Melee: +9 to hit, reach 5 ft. Hit: 25 (6d6+4) piercing. "
             "A target reduced to 0 HP this way is ground to bits and ejected through side pipes; its "
             "nonmagical gear is destroyed too."),
            ("Wrecking Ball (1 crew, half cover)", "Melee: +9 to hit, reach 15 ft. Hit: 40 (8d8+4) "
             "bludgeoning (double against an object or structure)."),
            ("2 Harpoon Flingers (1 crew each, half cover)", "Ranged: +5 to hit, range 120 ft. "
             "Hit: 9 (2d8) piercing."),
        ],
    },
    "Devil's Ride": {
        "size": "Large", "ac": "23 (19 while motionless)", "hp": 30,
        "speed": "120 ft. (12 mph, 288 miles/day)",
        "crew": "capacity 1 Medium creature", "cargo": "100 lb.",
        "abilities": {"STR": 14, "DEX": 18, "CON": 12, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "fire, poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, frightened, paralyzed, petrified, "
                                 "poisoned, stunned, unconscious",
        "traits": [
            ("Damage/Mishap Threshold", "Threshold 5; rolls on the Mishap table at threshold 10."),
            ("Jump", "If it moves 30+ ft. in a straight line, it can clear up to 60 ft. jumping a gap; "
                      "each foot cleared costs a foot of movement."),
            ("Prone Deficiency", "If it falls prone, it can't right itself and is incapacitated until "
                                  "pulled upright."),
            ("Stunt", "The driver can spend 10 ft. of movement (after moving 10+ ft. straight) to "
             "attempt a free stunt: DC 10 DEX check using the bike's DEX. Success performs the stunt; "
             "on a failure the driver can't try again until the start of its next turn; failing by 5+ "
             "wipes out — the bike and all riders fall prone and it stops dead."),
        ],
        "actions": [
            ("Helm (1 crew, half cover)", "Drive and steer the Devil's Ride."),
        ],
        "reactions": [
            ("Juke", "If able to move, the driver can use its reaction to grant the Devil's Ride "
                      "advantage on a Dexterity saving throw."),
        ],
    },
    "Scavenger": {
        "size": "Huge", "ac": "20 (19 while motionless)", "hp": 150,
        "speed": "100 ft. (10 mph, 240 miles/day)",
        "crew": "capacity 8 Medium creatures", "cargo": "2 tons",
        "abilities": {"STR": 20, "DEX": 12, "CON": 20, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "fire, poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, frightened, paralyzed, petrified, "
                                 "poisoned, stunned, unconscious",
        "traits": [
            ("Damage/Mishap Threshold", "Threshold 10; rolls on the Mishap table at threshold 20."),
            ("Crushing Wheels", "Can move through the space of any Large or smaller creature; that "
             "creature makes a DC 12 DEX save or takes 16 (3d10) bludgeoning and is knocked prone "
             "(extra 16 (3d10) if already prone). Can't affect the same creature more than once/turn."),
            ("Magic Weapons", "The Scavenger's weapon attacks are magical."),
            ("Prone Deficiency", "If it rolls over and falls prone, it can't right itself and is "
                                  "incapacitated until flipped upright."),
        ],
        "actions": [
            ("Helm (1 crew, three-quarters cover)", "Drive and steer the Scavenger."),
            ("Grappling Claw (1 crew, half cover)", "Melee: +10 to hit, reach 15 ft. Hit: the target is "
             "grappled (escape DC 12); a creature target is also restrained until the grapple ends. Only "
             "one target grappled at a time; the operator can release it with a bonus action."),
            ("2 Harpoon Flingers (1 crew each, half cover)", "Ranged: +6 to hit, range 120 ft. "
             "Hit: 10 (2d8+1) piercing."),
        ],
    },
    "Tormentor": {
        "size": "Huge", "ac": "21 (19 while motionless)", "hp": 60,
        "speed": "100 ft. (10 mph, 240 miles/day)",
        "crew": "capacity 4 Medium creatures", "cargo": "500 lb.",
        "abilities": {"STR": 16, "DEX": 14, "CON": 14, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "fire, poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, frightened, paralyzed, petrified, "
                                 "poisoned, stunned, unconscious",
        "traits": [
            ("Damage/Mishap Threshold", "Threshold 10; rolls on the Mishap table at threshold 20."),
            ("Crushing Wheels", "Can move through the space of any Medium or smaller creature; that "
             "creature makes a DC 13 DEX save or takes 11 (2d10) bludgeoning and is knocked prone "
             "(extra 11 (2d10) if already prone). Can't affect the same creature more than once/turn."),
            ("Magic Weapons", "The Tormentor's weapon attacks are magical."),
            ("Prone Deficiency", "If it rolls over and falls prone, it can't right itself and is "
                                  "incapacitated until flipped upright."),
            ("Raking Scythes", "The first time it moves within 5 ft. of a non-prone creature or vehicle "
             "on a turn, it can rake for 13 (2d10+2) slashing; a DC 13 DEX save (the driver's save for "
             "a vehicle) avoids the damage entirely."),
        ],
        "actions": [
            ("Helm (1 crew, three-quarters cover)", "Drive and steer the Tormentor."),
            ("Harpoon Flinger (1 crew, half cover)", "Ranged: +7 to hit, range 120 ft. "
             "Hit: 11 (2d8+2) piercing."),
        ],
        "reactions": [
            ("Juke", "If able to move, the driver can use its reaction to grant the Tormentor "
                      "advantage on a Dexterity saving throw."),
        ],
    },
    "Venatrix": {
        "size": "Gargantuan", "ac": 19, "hp": 200, "speed": "100 ft. (10 mph, 240 miles/day)",
        "crew": "capacity 8 Medium creatures", "cargo": "1 ton",
        "abilities": {"STR": 18, "DEX": 18, "CON": 10, "INT": 0, "WIS": 0, "CHA": 0},
        "damage_immunities": "fire, poison, psychic",
        "condition_immunities": "blinded, charmed, deafened, frightened, paralyzed, petrified, "
                                 "poisoned, stunned, unconscious",
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 10 or less."),
        ],
        "actions": [
            ("Helm (1 crew)", "Drive and steer the Venatrix."),
            ("2 Harpoon Guns (1 crew each)", "Ranged: +6 to hit, range 120 ft. Hit: 10 (2d8+1) piercing."),
            ("Infernal Screamer (1 crew)", "One target within 120 ft. makes a DC 15 WIS save, taking "
             "26 (4d12) psychic damage on a failure or half as much on a success."),
        ],
    },
}


# ── Magic item vehicles ───────────────────────────────────────────────────────
# Unlike the vehicles above, these are magic items rather than ordinary
# purchasable equipment — included here so they get the same stat-block-card
# treatment, but flagged with is_magic_item for the UI to note that distinction.
VEHICLE_STATBLOCKS_MAGIC = {
    "Apparatus of Kwalish": {
        "size": "Large", "ac": 20, "hp": 200, "speed": "30 ft., swim 30 ft. (0 ft. for both if legs "
                                                          "aren't extended)",
        "is_magic_item": True,
        "damage_immunities": "poison, psychic",
        "traits": [
            ("Description", "A sealed iron barrel (500 lb.) with a hidden catch (DC 20 INT "
             "(Investigation) to find). Releasing it opens a hatch for two Medium or smaller creatures "
             "to crawl inside, where ten levers control the apparatus — which can transform to resemble "
             "a giant lobster."),
            ("Airtight Compartment", "While the hatch is closed, the compartment is airtight and "
             "watertight, holding 10 hours of air divided by the number of breathing creatures inside."),
            ("Underwater", "Floats on water; can dive to 900 ft. Below that depth it takes 2d6 "
             "bludgeoning damage each minute from pressure."),
            ("Levers", "A creature inside can use a Utilize action to move up to two levers (each "
             "returns to neutral after use): legs extend/retract (speed 0 when retracted, no speed "
             "bonuses apply); forward/side window shutters open/close; claws extend/retract; extended "
             "claws attack (+8 to hit, reach 5 ft., 7 (2d6) bludgeoning) or grapple (escape DC 15); walk/"
             "swim forward/backward; turn 90\u00b0 CCW/CW; eye lights on (30 ft. bright + 30 ft. dim) or "
             "off; sink/rise 20 ft. in liquid; rear hatch open/close."),
        ],
        "actions": [],
    },
    "Tasha's Creeping Keelboat": {
        "size": "Gargantuan", "ac": "\u2014", "hp": "\u2014",
        "speed": "20 ft., swim 20 ft. (can't travel underwater)",
        "cargo": "0.5 tons", "is_magic_item": True, "no_combat_stats": True,
        "traits": [
            ("Description", "A four-legged magic boat that walks across land and water alike, moving "
             "according to your spoken directions while you ride it."),
            ("Protective Aura", "Creatures of your choice gain a +1 bonus to AC while on the boat."),
            ("Cargo", "Carries up to 1,000 lb. without hindrance; can carry up to twice that, but "
             "moves at half speed while overloaded."),
        ],
        "actions": [],
    },
    "Lyrandar Air Cruiser": {
        "size": "Gargantuan", "ac": 16, "hp": 600, "speed": "10 mph (fly 100 ft., hover)",
        "crew": "10", "passengers": "40", "cargo": "2 tons", "is_magic_item": True,
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 20 or less."),
            ("Lightning Turret (6)", "Medium object, AC 17, HP 50, three-quarters cover for the "
             "occupant. Requires an Elemental Core to fire."),
            ("Helm", "Small object, AC 15, HP 20. Pilot must have the Mark of Storm. Tilt and Roll: "
             "spend half the ship's fly speed to invert it; unanchored creatures/objects fall unless "
             "a DC 15 DEX save is made to grab something fixed."),
            ("Shield Station", "Large object, AC 15, HP 25, up to 2 Medium creatures. Requires an "
             "Elemental Core; Calibrate then Activate Shields grants +5 AC to the ship and its crew "
             "stations plus half cover on deck for 1 minute (or until the station is destroyed or "
             "concentration ends). A crew member with the Mark of Warding can Activate Shields as a "
             "bonus action."),
        ],
        "actions": [
            ("Lightning Blast (requires Elemental Core)", "Ranged: +9 to hit, range 80/320 ft. "
             "Hit: 22 (4d10) lightning."),
            ("Drive (requires Mark of Storm)", "The ship moves up to its fly speed in any direction."),
            ("Shift Engine (requires Mark of Storm)", "Suppress or reengage the ship's elemental core."),
        ],
    },
    "Lyrandar Skyskiff": {
        "size": "Large", "ac": 18, "hp": 150, "speed": "7 mph (fly 70 ft., hover)",
        "crew": "2", "passengers": "2", "cargo": "0.5 tons", "is_magic_item": True,
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 5 or less."),
            ("Tow Cable", "Small object, AC 10, HP 40. Harpoon: +6 to hit, range 50/100 ft., 5 (2d4) "
             "piercing and the target is harpooned (grappled if Medium or smaller; can't move more than "
             "100 ft. from the ship while harpooned; released with no action required). Reel (requires "
             "Elemental Core): pull a harpooned target up to 50 ft. in a straight line toward the ship."),
            ("Helm", "Small object, AC 15, HP 20. Pilot must have the Mark of Storm. Tilt and Roll: "
             "spend half the ship's fly speed to invert it; unanchored creatures/objects fall unless "
             "a DC 15 DEX save is made to grab something fixed."),
        ],
        "actions": [
            ("Drive (requires Mark of Storm)", "The ship moves up to its fly speed in any direction."),
            ("Shift Engine (requires Mark of Storm)", "Suppress or reengage the ship's elemental core."),
        ],
    },
    "Flying Chariot": {
        "size": "Large", "ac": 16, "hp": 50, "speed": "drawn (set by the animal(s) pulling it); "
                                                        "can fly if pulled by one or more flying creatures",
        "crew": "1", "supply": "40", "is_magic_item": True,
        "traits": [
            ("Magic Bonus", "The chariot's riders and creatures pulling it gain a +1 bonus to AC."),
            ("Flight", "If the chariot is pulled by one or more flying creatures, it too can fly."),
        ],
        "actions": [],
    },
    "Ornithopter of Flying": {
        "size": "Large", "ac": "—", "hp": "—", "speed": "fly 30 ft. (can't hover)",
        "cargo": "300 lb", "is_magic_item": True, "no_combat_stats": True,
        "traits": [
            ("Description", "An 8-foot-long contraption with a 14-foot wingspan, weighing 25 pounds. "
             "Carries a rider (plus worn/carried gear) up to 300 pounds total, moving according to the "
             "rider's spoken directions."),
            ("Falling", "If the ornithopter loses its rider while airborne, it falls and can't fly "
             "again for 1d6 + 4 days."),
        ],
        "actions": [],
    },
    "Bobbing Lily Pad": {
        "size": "Large", "ac": "—", "hp": "—",
        "speed": "20 ft., fly 20 ft. (hover), swim 20 ft. (can't go underwater)",
        "cargo": "300 lb (600 lb overloaded, half speed)", "is_magic_item": True, "no_combat_stats": True,
        "traits": [
            ("Description", "A 10-foot-diameter floating leaf with tendrils that propel it across "
             "land, water, and air, moving according to the rider's spoken directions."),
        ],
        "actions": [],
    },
    "Carpet of Flying, 3 ft. × 5 ft.": {
        "size": "Large", "ac": "—", "hp": "—", "speed": "fly 80 ft. (hover)",
        "cargo": "200 lb (400 lb overloaded, half speed)", "is_magic_item": True, "no_combat_stats": True,
        "traits": [("Description", "Speak the command word (action) to make the carpet hover and fly; "
                     "moves according to your spoken directions as long as you're within 30 feet of it.")],
        "actions": [],
    },
    "Carpet of Flying, 4 ft. × 6 ft.": {
        "size": "Large", "ac": "—", "hp": "—", "speed": "fly 60 ft. (hover)",
        "cargo": "400 lb (800 lb overloaded, half speed)", "is_magic_item": True, "no_combat_stats": True,
        "traits": [("Description", "Speak the command word (action) to make the carpet hover and fly; "
                     "moves according to your spoken directions as long as you're within 30 feet of it.")],
        "actions": [],
    },
    "Carpet of Flying, 5 ft. × 7 ft.": {
        "size": "Huge", "ac": "—", "hp": "—", "speed": "fly 40 ft. (hover)",
        "cargo": "600 lb (1,200 lb overloaded, half speed)", "is_magic_item": True, "no_combat_stats": True,
        "traits": [("Description", "Speak the command word (action) to make the carpet hover and fly; "
                     "moves according to your spoken directions as long as you're within 30 feet of it.")],
        "actions": [],
    },
    "Carpet of Flying, 6 ft. × 9 ft.": {
        "size": "Huge", "ac": "—", "hp": "—", "speed": "fly 30 ft. (hover)",
        "cargo": "800 lb (1,600 lb overloaded, half speed)", "is_magic_item": True, "no_combat_stats": True,
        "traits": [("Description", "Speak the command word (action) to make the carpet hover and fly; "
                     "moves according to your spoken directions as long as you're within 30 feet of it.")],
        "actions": [],
    },
    "Quaal's Feather Token, Swan Boat": {
        "size": "Huge", "ac": "—", "hp": "—", "speed": "6 mph (self-propelled on water)",
        "is_magic_item": True, "no_combat_stats": True,
        "traits": [
            ("Description", "Touch the token to a body of water at least 60 feet in diameter to create "
             "a 50-foot-long, 20-foot-wide boat shaped like a swan. Single use; the token disappears "
             "when the boat is created."),
        ],
        "actions": [],
    },
    "Strider Airship": {
        "size": "Gargantuan", "ac": 16, "hp": 350, "speed": "8 mph (fly 80 ft., hover)",
        "crew": "6", "passengers": "20", "cargo": "1 ton", "is_magic_item": True,
        "traits": [
            ("Damage Threshold", "Immune to damage from any single hit that deals 10 or less."),
            ("Arcane Launcher (4)", "Medium object, AC 17, HP 30."),
            ("Helm", "Small object, AC 15, HP 20. Pilot must have the Mark of Storm. Tilt and Roll: "
             "spend half the ship's fly speed to invert it; unanchored creatures/objects fall unless "
             "a DC 15 DEX save is made to grab something fixed."),
        ],
        "actions": [
            ("Energy Blast", "Ranged: +7 to hit, range 100/500 ft. Hit: 14 (4d6) force damage."),
            ("Drive (requires Mark of Storm)", "The ship moves up to its fly speed in any direction."),
            ("Shift Engine (requires Mark of Storm)", "Suppress or reengage the ship's elemental core."),
        ],
    },
}


def get_vehicle_statblock(name: str) -> dict | None:
    """Resolve a vehicle name (water, land, Spelljamming, Astral Plane, air,
    Bigby's combat vehicle, or magic item vehicle) to its stat block,
    checking each category dict in turn. Returns None only for a name that
    isn't in any of them."""
    return (VEHICLE_STATBLOCKS.get(name) or VEHICLE_STATBLOCKS_SPELLJAMMING.get(name)
            or VEHICLE_STATBLOCKS_ASTRAL.get(name) or VEHICLE_STATBLOCKS_AIR.get(name)
            or VEHICLE_STATBLOCKS_BGDIA.get(name) or VEHICLE_STATBLOCKS_MAGIC.get(name))


def get_mount_statblock(name: str) -> dict | None:
    """Resolve a mount name (as it appears in the equipment list, or one of
    Find Greater Steed's summon options) to its stat block."""
    if name in MOUNT_STATBLOCKS:
        return MOUNT_STATBLOCKS[name]
    alias = MOUNT_NAME_ALIASES.get(name)
    if alias:
        return MOUNT_STATBLOCKS.get(alias)
    return FIND_GREATER_STEED_OPTIONS.get(name)

# ═════════════════════════════════════════════════════════════════════════════
# Companions (class-granted: Steel Defender, Ranger's Companion, etc.)
# ═════════════════════════════════════════════════════════════════════════════

COMPANION_STATBLOCKS = {
    "steel_defender": {
        "display_name": "Steel Defender",
        "source": "Artificer (Battle Smith), 3rd level",
        "size": "Medium", "creature_type": "construct",
        "ac_formula": "15",  # flat, natural armor — does NOT scale with PB
        "hp_formula": "2 + {int_mod} + 5 \u00d7 {level}",
        "hit_dice_formula": "{level}d8",
        "speed": "40 ft.",
        "abilities": {"STR": 14, "DEX": 12, "CON": 14, "INT": 4, "WIS": 10, "CHA": 6},
        "saves": [("DEX", "+1 + {pb}"), ("CON", "+2 + {pb}")],
        "skills": [("Athletics", "+2 + {pb}"), ("Perception", "+0 + {pb}\u00d72")],
        "damage_immunities": "poison",
        "condition_immunities": "charmed, exhaustion, poisoned",
        "senses": "darkvision 60 ft., passive Perception 10 + ({pb}\u00d72)",
        "languages": "understands the languages you speak",
        "traits": [
            ("Vigilant", "The defender can't be surprised."),
        ],
        "actions": [
            ("Force-Empowered Rend",
             "Melee Weapon Attack: {atk} to hit, reach 5 ft., one target you can see. "
             "Hit: 1d8 + {pb} force damage."),
            ("Repair (3/Day)",
             "The magical mechanisms inside the defender restore 2d8 + {pb} hit points "
             "to itself or to one construct or object within 5 feet of it."),
        ],
        "reactions": [
            ("Deflect Attack",
             "The defender imposes disadvantage on the attack roll of one creature it "
             "can see within 5 feet of it, provided the attack roll is against a "
             "creature other than the defender."),
        ],
        "class_key": "Artificer", "subclass_match": "battle smith", "min_level": 3,
        "level_source": "class",
    },

    "wildfire_spirit": {
        "display_name": "Wildfire Spirit",
        "source": "Druid (Circle of Wildfire), 2nd level",
        "requires_summon_action": True,
        "summon_uses_wild_shape": True,  # shares the existing Wild Shape
        # charge pool rather than having its own dedicated resource —
        # this expends a normal Wild Shape use, unlike Drake Companion/
        # Dancing Item which have their own separate "once per long rest" resource.
        "size": "Small", "creature_type": "elemental",
        "ac_formula": "13",
        "hp_formula": "5 + 5 \u00d7 {level}",
        "hit_dice_formula": None,
        "speed": "30 ft., fly 30 ft. (hover)",
        "abilities": {"STR": 10, "DEX": 14, "CON": 14, "INT": 13, "WIS": 15, "CHA": 11},
        "saves": [],
        "skills": [],
        "damage_immunities": "fire",
        "condition_immunities": "charmed, frightened, grappled, prone, restrained",
        "senses": "darkvision 60 ft., passive Perception 12",
        "languages": "understands the languages you speak",
        "traits": [],
        "actions": [
            ("Flame Seed",
             "Ranged Weapon Attack: {atk} to hit, range 60 ft., one target you can see. "
             "Hit: 1d6 + {pb} fire damage."),
            ("Fiery Teleportation",
             "The spirit and each willing creature of your choice within 5 feet of it "
             "teleport up to 15 feet to unoccupied spaces you can see. Then each "
             "creature within 5 feet of the space the spirit left must succeed on a "
             "DEX save against your spell save DC ({dc}) or take 1d6 + {pb} fire damage."),
        ],
        "reactions": [],
        "class_key": "Druid", "subclass_match": "wildfire", "min_level": 2,
        "level_source": "class",
    },

    "drake_companion": {
        "display_name": "Drake Companion",
        "source": "Ranger (Drakewarden), 3rd level",
        "requires_summon_action": True,  # only shown in the Companions tab
        # after being explicitly summoned (1/long rest resource), unlike
        # Steel Defender/Ranger's Companion/Homunculus Servant which
        # persist once created with no per-use summon action at all.
        "summon_resource_key": "drake_companion_summon",
        "size": "Small \u2192 Medium (7th) \u2192 Large (15th)", "creature_type": "dragon",
        "ac_formula": "14 + {pb}",
        "hp_formula": "5 + 5 \u00d7 {level}",
        "hit_dice_formula": "{level}d10",
        "speed": "40 ft. (+ fly = walk speed at 7th level)",
        "abilities": {"STR": 16, "DEX": 12, "CON": 15, "INT": 8, "WIS": 14, "CHA": 8},
        "saves": [("DEX", "+1 + {pb}"), ("WIS", "+2 + {pb}")],
        "skills": [],
        "damage_immunities": "determined by Draconic Essence (your choice: acid/cold/fire/lightning/poison)",
        "condition_immunities": "",
        "senses": "darkvision 60 ft., passive Perception 12",
        "languages": "Draconic",
        "traits": [
            ("Draconic Essence", "When you summon the drake, choose acid/cold/fire/lightning/poison \u2014 "
             "this sets its damage immunity and its Infused Strikes damage type."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: {atk_flat} to hit, reach 5 ft., one target. "
             "Hit: 1d6 + {pb} piercing damage (Bond of Fang and Scale adds +1d6 Draconic "
             "Essence damage at 7th level, increasing to +2d6 total at 15th)."),
        ],
        "reactions": [
            ("Infused Strikes",
             "When another creature within 30 ft of the drake that it can see hits a "
             "target with a weapon attack, the drake infuses the strike: the target "
             "takes an extra 1d6 damage of the Draconic Essence type."),
        ],
        "class_key": "Ranger", "subclass_match": "drakewarden", "min_level": 3,
        "level_source": "class",
    },

    "dancing_item": {
        "display_name": "Dancing Item",
        "source": "Bard (College of Creation), 6th level \u2014 via Animating Performance",
        "requires_summon_action": True,
        "summon_resource_key": "dancing_item_summon",
        # NOTE: Creative Crescendo (14th level) lets the character have
        # multiple Dancing Items active at once (CHA mod count) — this
        # single-instance-per-key tracking model doesn't yet represent
        # that; a 14th+ level College of Creation Bard is limited to
        # tracking one Dancing Item's HP/active-state through this UI
        # even though the real rule allows more. Known limitation, not
        # silently wrong — the single-item case (the common one for
        # most of the class's career) is handled correctly.
        "size": "Large or smaller", "creature_type": "construct",
        "ac_formula": "16",
        "hp_formula": "10 + 5 \u00d7 {level}",
        "hit_dice_formula": None,
        "speed": "30 ft., fly 30 ft. (hover)",
        "abilities": {"STR": 18, "DEX": 14, "CON": 16, "INT": 4, "WIS": 10, "CHA": 6},
        "saves": [],
        "skills": [],
        "damage_immunities": "poison, psychic",
        "condition_immunities": "charmed, exhaustion, poisoned, frightened",
        "senses": "darkvision 60 ft., passive Perception 10",
        "languages": "understands the languages you speak",
        "traits": [
            ("Immutable Form", "The item is immune to any spell or effect that would alter its form."),
            ("Irrepressible Dance", "When any creature starts its turn within 10 ft of the item, "
             "the item can increase or decrease (your choice) that creature's walking speed by 10 "
             "ft until the end of the turn, provided the item isn't incapacitated."),
        ],
        "actions": [
            ("Force-Empowered Slam",
             "Melee Weapon Attack: {atk} to hit, reach 5 ft., one target you can see. "
             "Hit: 1d10 + {pb} force damage."),
        ],
        "reactions": [],
        "class_key": "Bard", "subclass_match": "creation", "min_level": 6,
        "level_source": "class",
    },

    "beast_of_the_land": {
        "display_name": "Beast of the Land",
        "source": "Ranger (Beast Master \u2014 Primal Companion option), 3rd level",
        "size": "Medium", "creature_type": "beast",
        "ac_formula": "13 + {pb}",
        "hp_formula": "5 + 5 \u00d7 {level}",
        "hit_dice_formula": "{level}d8",
        "speed": "40 ft., climb 40 ft.",
        "abilities": {"STR": 14, "DEX": 14, "CON": 15, "INT": 8, "WIS": 14, "CHA": 11},
        "saves": [],
        "skills": [],
        "damage_immunities": "",
        "condition_immunities": "",
        "senses": "darkvision 60 ft., passive Perception 12",
        "languages": "understands the languages you speak",
        "traits": [
            ("Charge", "If the beast moves at least 20 ft straight toward a target and hits it "
             "with a maul attack on the same turn, the target takes an extra 1d6 slashing damage "
             "and (if a creature) must succeed on a STR save against your spell save DC ({dc}) or be knocked prone."),
            ("Primal Bond", "Add your proficiency bonus ({pb}) to any ability check or saving throw the beast makes."),
        ],
        "actions": [
            ("Maul", "Melee Weapon Attack: {atk} to hit, reach 5 ft., one target. "
             "Hit: 1d8 + 2 + {pb} slashing damage."),
        ],
        "reactions": [],
        "class_key": "Ranger", "subclass_match": "beast master", "min_level": 3,
        "level_source": "class", "requires_choice": True,
    },

    "beast_of_the_sea": {
        "display_name": "Beast of the Sea",
        "source": "Ranger (Beast Master \u2014 Primal Companion option), 3rd level",
        "size": "Medium", "creature_type": "beast",
        "ac_formula": "13 + {pb}",
        "hp_formula": "5 + 5 \u00d7 {level}",
        "hit_dice_formula": "{level}d8",
        "speed": "5 ft., swim 60 ft.",
        "abilities": {"STR": 14, "DEX": 14, "CON": 15, "INT": 8, "WIS": 14, "CHA": 11},
        "saves": [],
        "skills": [],
        "damage_immunities": "",
        "condition_immunities": "",
        "senses": "darkvision 60 ft., passive Perception 12",
        "languages": "understands the languages you speak",
        "traits": [
            ("Amphibious", "The beast can breathe both air and water."),
            ("Primal Bond", "Add your proficiency bonus ({pb}) to any ability check or saving throw the beast makes."),
        ],
        "actions": [
            ("Binding Strike", "Melee Weapon Attack: {atk} to hit, reach 5 ft., one target. "
             "Hit: 1d6 + 2 + {pb} piercing or bludgeoning damage (your choice), and the target is "
             "grappled (escape DC {dc}). The beast can't use this attack on another target until the grapple ends."),
        ],
        "reactions": [],
        "class_key": "Ranger", "subclass_match": "beast master", "min_level": 3,
        "level_source": "class", "requires_choice": True,
    },

    "beast_of_the_sky": {
        "display_name": "Beast of the Sky",
        "source": "Ranger (Beast Master \u2014 Primal Companion option), 3rd level",
        "size": "Small", "creature_type": "beast",
        "ac_formula": "13 + {pb}",
        "hp_formula": "4 + 4 \u00d7 {level}",
        "hit_dice_formula": "{level}d6",
        "speed": "10 ft., fly 60 ft.",
        "abilities": {"STR": 6, "DEX": 16, "CON": 13, "INT": 8, "WIS": 14, "CHA": 11},
        "saves": [],
        "skills": [],
        "damage_immunities": "",
        "condition_immunities": "",
        "senses": "darkvision 60 ft., passive Perception 12",
        "languages": "understands the languages you speak",
        "traits": [
            ("Flyby", "The beast doesn't provoke opportunity attacks when it flies out of a creature's reach."),
            ("Primal Bond", "Add your proficiency bonus ({pb}) to any ability check or saving throw the beast makes."),
        ],
        "actions": [
            ("Shred", "Melee Weapon Attack: {atk} to hit, reach 5 ft., one target. "
             "Hit: 1d4 + 3 + {pb} slashing damage."),
        ],
        "reactions": [],
        "class_key": "Ranger", "subclass_match": "beast master", "min_level": 3,
        "level_source": "class", "requires_choice": True,
    },
    "homunculus_servant": {
        "display_name": "Homunculus Servant",
        "source": "Artificer, via the Homunculus Servant infusion",
        "requires_active_infusion": "Homunculus Servant",  # gated on an
        # active_infusions entry for this specific infusion, not a
        # separate summon action or resource — matches how it's
        # actually created in the real rules (infusing a 100+ gp gem
        # or crystal), and how the app's existing infuse-item flow
        # already works for every other infusion.
        "size": "Tiny", "creature_type": "construct",
        "ac_formula": "13",  # flat, natural armor — does NOT scale with PB
        "hp_formula": "1 + {int_mod} + {level}",
        "hit_dice_formula": "{level}d4",
        "speed": "20 ft., fly 30 ft.",
        "abilities": {"STR": 4, "DEX": 15, "CON": 12, "INT": 10, "WIS": 10, "CHA": 7},
        "saves": [("DEX", "+2 + {pb}")],
        "skills": [("Perception", "+0 + {pb}\u00d72"), ("Stealth", "+2 + {pb}")],
        "damage_immunities": "poison",
        "condition_immunities": "exhaustion, poisoned",
        "senses": "darkvision 60 ft., passive Perception 10 + ({pb}\u00d72)",
        "languages": "understands the languages you speak",
        "traits": [
            ("Evasion", "If subjected to an effect that allows it to make a DEX save for "
             "half damage, it instead takes no damage on a success and half on a failure. "
             "Can't use this trait if incapacitated."),
        ],
        "actions": [
            ("Force Strike (Bonus Action to command)",
             "Ranged Weapon Attack: {atk} to hit, range 30 ft., one target you can see. "
             "Hit: 1d4 + {pb} force damage."),
        ],
        "reactions": [
            ("Channel Magic", "Delivers a spell you cast that has a range of touch, provided "
             "the homunculus is within 120 feet of you."),
        ],
        "class_key": "Artificer", "subclass_match": "", "min_level": 2,
        "level_source": "class",
    },
}

# Eldritch Cannon isn't a creature (no ability scores/saves as a normal
# statblock — treats all scores as 10 if forced to roll one) so it gets
# its own simpler template rather than forcing it into the shape above.
ELDRITCH_CANNON = {
    "display_name": "Eldritch Cannon",
    "source": "Artificer (Artillerist), 3rd level",
    "size": "Small or Tiny", "creature_type": "object",
    "ac_formula": "18",
    "hp_formula": "5 \u00d7 {level}",
    "notes": "Immune to poison and psychic damage. All ability scores treated as 10 (+0) "
             "for checks/saves it's forced to make. Regains 2d6 HP if Mending is cast on it. "
             "Disappears at 0 HP or after 1 hour (or dismiss it early as an action).",
    "class_key": "Artificer", "subclass_match": "artillerist", "min_level": 3,
    "level_source": "class",
    "cannon_types": [
        ("Flamethrower", "The cannon exhales fire in an adjacent 15-ft cone: DEX save against "
         "your spell save DC ({dc}), 2d8 fire damage on a fail (half on success). Ignites "
         "flammable objects in the area not worn/carried."),
        ("Force Ballista", "Ranged spell attack ({atk}) from the cannon at one creature/object "
         "within 120 ft: 2d8 force damage on a hit, and a creature is pushed up to 5 ft away."),
        ("Protector", "The cannon grants itself and each creature of your choice within 10 ft "
         "temporary HP equal to 1d8 + {int_mod} (minimum +1)."),
    ],
}

# ═════════════════════════════════════════════════════════════════════════════
# Summon spells (Find Greater Steed, scaling Summon X spells)
# ═════════════════════════════════════════════════════════════════════════════

FIND_GREATER_STEED_OPTIONS = {
    "Griffon": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 12, "ac_note": "", "hp": 59, "hit_dice": "7d10+21",
        "speed": "30 ft., fly 80 ft.", "flies": True, "swims": False,
        "abilities": {"STR": 18, "DEX": 15, "CON": 16, "INT": 2, "WIS": 13, "CHA": 8},
        "skills": [("Perception", "+5")], "senses": "darkvision 60 ft., passive Perception 15",
        "traits": [("Keen Sight", "Advantage on Wisdom (Perception) checks that rely on sight.")],
        "actions": [
            ("Multiattack", "The griffon makes two attacks: one with its beak and one with its claws."),
            ("Beak", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 1d8+4 piercing damage."),
            ("Claws", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 2d6+4 slashing damage."),
        ],
    },
    "Pegasus": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 12, "ac_note": "", "hp": 59, "hit_dice": "7d10+21",
        "speed": "60 ft., fly 90 ft.", "flies": True, "swims": False,
        "abilities": {"STR": 18, "DEX": 15, "CON": 16, "INT": 10, "WIS": 15, "CHA": 13},
        "skills": [("Perception", "+6")], "senses": "passive Perception 16",
        "traits": [],
        "actions": [("Hooves", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 2d6+4 bludgeoning damage.")],
    },
    "Peryton": {
        "cr": 2, "cr_label": "2", "size": "Medium",
        "ac": 13, "ac_note": "natural armor", "hp": 33, "hit_dice": "6d8+6",
        "speed": "20 ft., fly 60 ft.", "flies": True, "swims": False,
        "abilities": {"STR": 16, "DEX": 12, "CON": 13, "INT": 9, "WIS": 12, "CHA": 10},
        "skills": [("Perception", "+5")], "senses": "passive Perception 15",
        "traits": [
            ("Dive Attack", "If the peryton is flying and dives at least 30 ft straight toward a target and hits it with a melee attack, that attack deals an extra 2d8 damage."),
            ("Flyby", "The peryton doesn't provoke an opportunity attack when it flies out of an enemy's reach."),
            ("Keen Sight and Smell", "Advantage on Wisdom (Perception) checks that rely on sight or smell."),
        ],
        "actions": [
            ("Multiattack", "The peryton makes one gore attack and one talon attack."),
            ("Gore", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d8+3 piercing damage."),
            ("Talons", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 2d4+3 piercing damage."),
        ],
    },
    "Dire Wolf": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 14, "ac_note": "natural armor", "hp": 37, "hit_dice": "5d10+10",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 17, "DEX": 15, "CON": 15, "INT": 3, "WIS": 12, "CHA": 7},
        "skills": [("Perception", "+3"), ("Stealth", "+4")], "senses": "passive Perception 13",
        "traits": [
            ("Keen Hearing and Smell", "Advantage on Wisdom (Perception) checks that rely on hearing or smell."),
            ("Pack Tactics", "Advantage on an attack roll against a creature if at least one of the wolf's allies is within 5 ft of the creature and the ally isn't incapacitated."),
        ],
        "actions": [("Bite", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 2d6+3 piercing damage. Target must succeed a DC 13 STR save or be knocked prone.")],
    },
    "Rhinoceros": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 11, "ac_note": "natural armor", "hp": 45, "hit_dice": "6d10+12",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 21, "DEX": 8, "CON": 15, "INT": 2, "WIS": 12, "CHA": 6},
        "skills": [], "senses": "passive Perception 11",
        "traits": [("Charge", "If the rhinoceros moves at least 20 ft straight toward a target and hits it with a gore attack on the same turn, the target takes an extra 2d8 bludgeoning damage. If the target is a creature, it must succeed on a DC 15 STR save or be knocked prone.")],
        "actions": [("Gore", "Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 2d8+5 bludgeoning damage.")],
    },
    "Saber-Toothed Tiger": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 12, "ac_note": "", "hp": 52, "hit_dice": "7d10+14",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 18, "DEX": 14, "CON": 15, "INT": 3, "WIS": 12, "CHA": 8},
        "skills": [("Perception", "+3"), ("Stealth", "+6")], "senses": "passive Perception 13",
        "traits": [
            ("Keen Smell", "Advantage on Wisdom (Perception) checks that rely on smell."),
            ("Pounce", "If the tiger moves at least 20 ft straight toward a creature and hits it with a claw attack on the same turn, the target must succeed a DC 14 STR save or be knocked prone; if prone, the tiger can make one bite attack against it as a bonus action."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 1d10+5 piercing damage."),
            ("Claw", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 2d6+5 slashing damage."),
        ],
    },
}

# Each scaling summon: base_level (the spell's minimum casting level),
# hp_base, hp_per_level (added per slot level above base_level),
# ac_base (+ level, sometimes + a form-specific bonus), attacks_formula
# ("half_level" = floor(level/2)), and per-form flavor differences.
SCALING_SUMMONS = {
    "Summon Celestial": {
        "base_level": 5, "size": "Large", "creature_type": "celestial",
        "ac_base": 11, "hp_base": 40, "hp_per_level": 10,
        "speed": "30 ft., fly 40 ft.",
        "abilities": {"STR": 16, "DEX": 14, "CON": 16, "INT": 10, "WIS": 14, "CHA": 16},
        "damage_resistances": "radiant", "condition_immunities": "charmed, frightened",
        "senses": "darkvision 60 ft.", "languages": "Celestial, understands the languages you speak",
        "attacks_formula": "half_level",
        "forms": {
            "Avenger": {"ac_bonus": 0,
                        "action": "Radiant Bow — Ranged Weapon Attack: spell attack mod to hit, range 150/600 ft. Hit: 2d6+2+spell level radiant damage."},
            "Defender": {"ac_bonus": 2,
                         "action": "Radiant Mace — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d10+3+spell level radiant damage; you or another creature within 10 ft of the target gains 1d10 temp HP."},
        },
        "extra_note": "Healing Touch (1/Day): touch a creature to heal 2d8+spell level HP.",
    },
    "Summon Undead": {
        "base_level": 3, "size": "Medium", "creature_type": "undead",
        "ac_base": 11, "hp_per_level": 10,
        "abilities": {"STR": 12, "DEX": 16, "CON": 15, "INT": 4, "WIS": 10, "CHA": 9},
        "damage_immunities": "necrotic, poison",
        "condition_immunities": "exhaustion, frightened, paralyzed, poisoned",
        "senses": "darkvision 60 ft.", "languages": "understands the languages you speak",
        "attacks_formula": "half_level",
        "forms": {
            "Ghostly": {"hp_base": 30, "speed": "30 ft., fly 40 ft. (hover)",
                        "trait": "Incorporeal Passage — can move through creatures/objects as difficult terrain; 1d10 force damage per 5 ft if it ends turn inside an object.",
                        "action": "Deathly Touch — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d8+3+spell level necrotic damage; WIS save or frightened until end of target's next turn."},
            "Putrid": {"hp_base": 30, "speed": "30 ft.",
                       "trait": "Festering Aura — creatures (other than you) starting their turn within 5 ft must succeed a CON save vs your spell save DC or be poisoned until the start of their next turn.",
                       "action": "Rotting Claw — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d6+3+spell level slashing damage; if target is poisoned, CON save or paralyzed until end of its next turn."},
            "Skeletal": {"hp_base": 20, "speed": "30 ft.",
                         "action": "Grave Bolt — Ranged Spell Attack: spell attack mod to hit, range 150 ft. Hit: 2d4+3+spell level necrotic damage."},
        },
    },
    "Summon Fiend": {
        "base_level": 6, "size": "Large", "creature_type": "fiend",
        "ac_base": 12, "hp_per_level": 15,
        "abilities": {"STR": 13, "DEX": 16, "CON": 15, "INT": 10, "WIS": 10, "CHA": 16},
        "damage_resistances": "fire", "damage_immunities": "poison",
        "condition_immunities": "poisoned",
        "senses": "darkvision 60 ft.", "languages": "Abyssal, Infernal, telepathy 60 ft.",
        "attacks_formula": "half_level",
        "extra_note": "Magic Resistance: advantage on saves against spells and other magical effects.",
        "forms": {
            "Demon": {"hp_base": 50, "speed": "40 ft., climb 40 ft.",
                      "trait": "Death Throes — on 0 HP or spell end, explodes: each creature within 10 ft makes a DEX save vs your spell save DC, taking 2d10+spell level fire damage on a fail (half on success).",
                      "action": "Bite — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d12+3+spell level necrotic damage."},
            "Devil": {"hp_base": 40, "speed": "fly 60 ft.",
                      "trait": "Devil's Sight — magical darkness doesn't impede its darkvision.",
                      "action": "Hurl Flame — Ranged Spell Attack: spell attack mod to hit, range 150 ft. Hit: 2d6+3+spell level fire damage; flammable unattended objects hit also catch fire."},
            "Yugoloth": {"hp_base": 60, "speed": "40 ft.",
                         "action": "Claws — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d8+3+spell level slashing damage; can then teleport up to 30 ft to an unoccupied space it can see."},
        },
    },
    "Summon Draconic Spirit": {
        "base_level": 5, "size": "Large", "creature_type": "dragon",
        "ac_base": 14, "hp_base": 50, "hp_per_level": 10,
        "speed": "30 ft., fly 60 ft., swim 30 ft.",
        "abilities": {"STR": 19, "DEX": 14, "CON": 17, "INT": 10, "WIS": 14, "CHA": 14},
        "condition_immunities": "charmed, frightened, poisoned",
        "senses": "blindsight 30 ft., darkvision 60 ft.", "languages": "Draconic, understands the languages you speak",
        "attacks_formula": "half_level",
        "extra_note": "Shared Resistances: choose one of the dragon's damage resistances when summoned — you also gain resistance to that type until the spell ends.",
        "forms": {
            "Chromatic": {"damage_resistances": "acid, cold, fire, lightning, poison (choose one to also share with yourself)"},
            "Gem": {"damage_resistances": "force, necrotic, psychic, radiant, thunder (choose one to also share with yourself)"},
            "Metallic": {"damage_resistances": "acid, cold, fire, lightning, poison (choose one to also share with yourself)"},
        },
        "action_shared": "Rend — Melee Weapon Attack: spell attack mod to hit, reach 10 ft. Hit: 1d6+4+spell level piercing damage. | Breath Weapon (also used each Multiattack) — 30-ft cone, DEX save vs your spell save DC, 2d6 damage of a resisted type (your choice) on a fail, half on success.",
    },
    "Summon Shadowspawn": {
        "base_level": 3, "size": "Medium", "creature_type": "monstrosity",
        "ac_base": 11, "hp_base": 35, "hp_per_level": 15,
        "speed": "40 ft.",
        "abilities": {"STR": 13, "DEX": 16, "CON": 15, "INT": 4, "WIS": 10, "CHA": 16},
        "damage_resistances": "necrotic", "condition_immunities": "frightened",
        "senses": "darkvision 120 ft.", "languages": "understands the languages you speak",
        "attacks_formula": "half_level",
        "extra_note": "Dreadful Scream (1/Day): each creature within 30 ft makes a WIS save vs your spell save DC or is frightened of the spirit for 1 minute (repeatable save each turn).",
        "forms": {
            "Fury": {"trait": "Terror Frenzy — advantage on attack rolls against frightened creatures."},
            "Despair": {"trait": "Weight of Sorrow — creatures (other than you) starting their turn within 5 ft have their speed reduced by 20 ft until the start of their next turn."},
            "Fear": {"trait": "Shadow Stealth — while in dim light or darkness, can take the Hide action as a bonus action."},
        },
        "action_shared": "Chilling Hand — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d12+3+spell level cold damage.",
    },
    "Summon Fey": {
        "base_level": 3, "size": "Small", "creature_type": "fey",
        "ac_base": 12, "hp_base": 30, "hp_per_level": 10,
        "speed": "40 ft.",
        "abilities": {"STR": 13, "DEX": 16, "CON": 14, "INT": 14, "WIS": 11, "CHA": 16},
        "condition_immunities": "charmed",
        "senses": "darkvision 60 ft.", "languages": "Sylvan, understands the languages you speak",
        "attacks_formula": "half_level",
        "forms": {
            "Fuming": {"bonus_action": "Fey Step (teleport 30 ft), then gains advantage on its next attack roll this turn."},
            "Mirthful": {"bonus_action": "Fey Step (teleport 30 ft), then can force a creature within 10 ft to WIS save vs your spell save DC or be charmed for 1 minute or until damaged."},
            "Tricksy": {"bonus_action": "Fey Step (teleport 30 ft), then fills a 5-ft cube within 5 ft with magical darkness until the end of its next turn."},
        },
        "action_shared": "Shortsword — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d6+3+spell level piercing damage plus 1d6 force damage.",
    },
    "Summon Beast": {
        "base_level": 2, "size": "Small", "creature_type": "beast",
        "ac_base": 11, "hp_per_level": 5,
        "abilities": {"STR": 18, "DEX": 11, "CON": 16, "INT": 4, "WIS": 14, "CHA": 5},
        "senses": "darkvision 60 ft.", "languages": "understands the languages you speak",
        "attacks_formula": "half_level",
        "forms": {
            "Air": {"hp_base": 20, "speed": "30 ft., fly 60 ft.",
                    "trait": "Flyby — doesn't provoke opportunity attacks when it flies out of an enemy's reach."},
            "Land": {"hp_base": 30, "speed": "30 ft., climb 30 ft.",
                     "trait": "Pack Tactics — advantage on an attack roll against a creature if an ally is within 5 ft of it and isn't incapacitated."},
            "Water": {"hp_base": 30, "speed": "30 ft., swim 30 ft.",
                      "trait": "Water Breathing — can breathe only underwater."},
        },
        "action_shared": "Maul — Melee Weapon Attack: spell attack mod to hit, reach 5 ft. Hit: 1d8+4+spell level piercing damage.",
    },
    "Spirit of Death": {
        "base_level": 4, "size": "Medium", "creature_type": "undead",
        "ac_base": 11, "hp_base": 40, "hp_per_level": 10,
        "speed": "30 ft., fly 30 ft. (hover)",
        "abilities": {"STR": 16, "DEX": 16, "CON": 16, "INT": 16, "WIS": 16, "CHA": 16},
        "damage_immunities": "necrotic, poison",
        "condition_immunities": "charmed, exhaustion, frightened, paralyzed, poisoned",
        "senses": "darkvision 60 ft.", "languages": "understands the languages you speak",
        "attacks_formula": "half_level",
        "forms": {"Reaper": {}},
        "trait": "Incorporeal Movement — can move through creatures/objects as difficult terrain; 1d10 force damage per 5 ft if it ends its turn inside an object.",
        "action_shared": "Reaping Scythe — Melee Weapon Attack: spell attack mod to hit (with advantage), reach 5 ft. Hit: 1d8+3+spell level necrotic damage.",
        "bonus_action": "Haunt Creature — targets a creature within 10 ft; while haunted, you sense its direction/distance on the same plane, and if it starts its turn within 10 ft of the spirit, WIS save vs your spell save DC or frightened until the start of its next turn.",
    },
}


def resolve_scaling_summon(spell_name: str, cast_level: int, form: str, spell_attack_mod: int = 0) -> dict | None:
    """Compute the actual stat block for one of the SCALING_SUMMONS at the
    specific level it was cast, in the same shape mount/wildshape card
    rendering expects. cast_level must be >= the spell's base_level (the
    caller is responsible for enforcing that, same as any other spell)."""
    spell = SCALING_SUMMONS.get(spell_name)
    if not spell or form not in spell.get("forms", {}):
        return None
    base_level = spell["base_level"]
    lvl = max(cast_level, base_level)
    form_data = spell["forms"][form]

    hp_base = form_data.get("hp_base", spell.get("hp_base", 0))
    hp_per_level = spell.get("hp_per_level", 0)
    hp = hp_base + hp_per_level * (lvl - base_level)

    ac = spell["ac_base"] + lvl + form_data.get("ac_bonus", 0)

    num_attacks = lvl // 2  # "half this spell's level, rounded down"

    actions = [("Multiattack", f"Makes {num_attacks} attack(s) as described below.")]
    if spell.get("action_shared"):
        for part in spell["action_shared"].split(" | "):
            name, _, desc = part.partition(" — ")
            actions.append((name.strip(), desc.strip().replace("spell level", str(lvl))))
    if form_data.get("action"):
        name, _, desc = form_data["action"].partition(" — ")
        actions.append((name.strip(), desc.strip().replace("spell level", str(lvl))))

    traits = []
    if spell.get("trait"):
        traits.append(("Trait", spell["trait"]))
    if form_data.get("trait"):
        traits.append((f"{form} Trait", form_data["trait"]))
    if spell.get("extra_note"):
        traits.append(("Note", spell["extra_note"]))
    if form_data.get("bonus_action") or spell.get("bonus_action"):
        traits.append(("Bonus Action", form_data.get("bonus_action") or spell.get("bonus_action")))

    return {
        "display_name": f"{form} {spell_name.replace('Summon ', '').replace('Spirit of Death', 'Reaper Spirit')}",
        "source": f"{spell_name} (cast at level {lvl})",
        "size": spell["size"], "creature_type": spell["creature_type"],
        "ac": str(ac), "hp": hp, "hit_dice": f"(computed, not rolled — {hp} HP at this level)",
        "speed": form_data.get("speed", spell.get("speed", "30 ft.")),
        "abilities": spell["abilities"], "saves": [], "skills": [],
        "damage_resistances": form_data.get("damage_resistances", spell.get("damage_resistances", "")),
        "damage_immunities": spell.get("damage_immunities", ""),
        "condition_immunities": spell.get("condition_immunities", ""),
        "senses": spell.get("senses", ""), "languages": spell.get("languages", ""),
        "traits": traits, "actions": actions,
    }

# ═════════════════════════════════════════════════════════════════════════════
# Wild Shape beast forms
# ═════════════════════════════════════════════════════════════════════════════

# cr as a float for numeric comparison (1/4 -> 0.25, 1/2 -> 0.5, etc.)
WILDSHAPE_BEASTS = {
    'Almiraj': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 13, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 16, 'CON': 10, 'INT': 2, 'WIS': 14, 'CHA': 10},
        "skills": [('Perception', '+4'), ('Stealth', '+5')],
        "senses": 'darkvision 30 ft., passive Perception 14',
        "traits": [('Familiar', "With the DM's permission, the find familiar spell can summon an almiraj."), ('Keen Senses', 'The almiraj has advantage on Wisdom (Perception) checks that rely on hearing or sight.')],
        "actions": [('Horn', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 5 (1d4 + 3) piercing damage.')],
    },
    'Amphisbaena': {
        "cr": 3.0, "cr_label": '3', "size": 'Huge',
        "ac": 12, "ac_note": '', "hp": 60, "hit_dice": '8d12 + 8',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 19, 'DEX': 14, 'CON': 12, 'INT': 1, 'WIS': 10, 'CHA': 3},
        "skills": [('Perception', '+2')],
        "senses": 'blindsight 10 ft., passive Perception 12',
        "traits": [],
        "actions": [('Multiattack', 'The amphisbaena makes two attacks, only one of which can be a constrict attack.'), ('Bite', 'Melee Weapon Attack: +6 to hit, reach 10 ft., one creature. Hit: 11 (2d6 + 4) piercing damage.'), ('Constrict', "Melee Weapon Attack: +6 to hit, reach 5 ft., one creature. Hit: 13 (2d8 + 4) bludgeoning damage, and the target is grappled (escape DC 16). Until this grapple ends, the creature is restrained, and the snake can't constrict another target.")],
    },
    'Armored Saber-Toothed Tiger': {
        "cr": 3.0, "cr_label": '3', "size": 'Large',
        "ac": 17, "ac_note": '*half plate armor*', "hp": 84, "hit_dice": '7d10 + 14',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 14, 'CON': 15, 'INT': 3, 'WIS': 12, 'CHA': 8},
        "skills": [('Perception', '+3'), ('Stealth', '+6')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Smell', 'The tiger has advantage on Wisdom (Perception) checks that rely on smell.'), ('Pounce', 'If the tiger moves at least 20 feet straight toward a creature and then hits it with a claw attack on the same turn, that target must succeed on a DC 14 Strength saving throw or be knocked prone. If the target is prone, the tiger can make one bite attack against it as a bonus action.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 10 (1d10 + 5) piercing damage.'), ('Claw', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 12 (2d6 + 5) slashing damage.')],
    },
    'Aurochs': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 11, "ac_note": 'natural armor', "hp": 38, "hit_dice": '4d10 + 16',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 20, 'DEX': 10, 'CON': 19, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Charge', 'If the aurochs moves at least 20 feet straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 9 (2d8) piercing damage. If the target is a creature, it must succeed on a DC 15 Strength saving throw or be knocked prone.')],
        "actions": [('Gore', 'Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 14 (2d8 + 5) piercing damage.')],
    },
    'Baboon': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 8, 'DEX': 14, 'CON': 11, 'INT': 4, 'WIS': 12, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Pack Tactics', "The baboon has advantage on an attack roll against a creature if at least one of the baboon's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +1 to hit, reach 5 ft., one target. Hit: 1 (1d4 - 1) piercing damage.')],
    },
    'Badger': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 10, "ac_note": '', "hp": 3, "hit_dice": '1d4 + 1',
        "speed": '20 ft., burrow 5 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 4, 'DEX': 11, 'CON': 12, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 11',
        "traits": [('Keen Smell', 'The badger has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Bat': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 12, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '5 ft., fly 30 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 2, 'DEX': 15, 'CON': 8, 'INT': 2, 'WIS': 12, 'CHA': 4},
        "skills": [],
        "senses": 'blindsight 60 ft., passive Perception 11',
        "traits": [('Echolocation', "The bat can't use its blindsight while deafened."), ('Keen Hearing', 'The bat has advantage on Wisdom (Perception) checks that rely on hearing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +0 to hit, reach 5 ft., one creature. Hit: 1 piercing damage.')],
    },
    'Blood Hawk': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 7, "hit_dice": '2d6',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 6, 'DEX': 14, 'CON': 10, 'INT': 3, 'WIS': 14, 'CHA': 5},
        "skills": [('Perception', '+4')],
        "senses": 'passive Perception 14',
        "traits": [('Keen Sight', 'The hawk has advantage on Wisdom (Perception) checks that rely on sight.'), ('Pack Tactics', "The hawk has advantage on an attack roll against a creature if at least one of the hawk's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Beak', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) piercing damage.')],
    },
    'Boar': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 11, "ac_note": 'natural armor', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 13, 'DEX': 11, 'CON': 12, 'INT': 2, 'WIS': 9, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 9',
        "traits": [('Charge', 'If the boar moves at least 20 feet straight toward a target and then hits it with a tusk attack on the same turn, the target takes an extra 3 (1d6) slashing damage. If the target is a creature, it must succeed on a DC 11 Strength saving throw or be knocked prone.'), ('Relentless (Recharges after a Short or Long Rest)', 'If the boar takes 7 damage or less that would reduce it to 0 hit points, it is reduced to 1 hit point instead.')],
        "actions": [('Tusk', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) slashing damage.')],
    },
    'Bristled Moorbounder': {
        "cr": 3.0, "cr_label": '3', "size": 'Large',
        "ac": 15, "ac_note": 'natural armor', "hp": 52, "hit_dice": '7d10 + 14',
        "speed": '70 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 14, 'CON': 14, 'INT': 2, 'WIS': 13, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 11',
        "traits": [('Bladed Hide', 'At the start of each of its turns, the moorbounder deals 5 (2d4) piercing damage to any creature grappling it.'), ('Standing Leap', "The moorbounder's long jump is up to 40 feet and its high jump is up to 20 feet, with or without a running start.")],
        "actions": [('Multiattack', 'The moorbounder makes two attacks: one with its blades and one with its claws.'), ('Blades', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 11 (2d6 + 4) slashing damage.'), ('Claws', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 14 (4d4 + 4) slashing damage.')],
    },
    'Brontosaurus': {
        "cr": 5.0, "cr_label": '5', "size": 'Gargantuan',
        "ac": 15, "ac_note": 'natural armor', "hp": 121, "hit_dice": '9d20 + 27',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 21, 'DEX': 9, 'CON': 17, 'INT': 2, 'WIS': 10, 'CHA': 7},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Stomp', 'Melee Weapon Attack: +8 to hit, reach 20 ft., one target. Hit: 27 (5d8 + 5) bludgeoning damage, and the target must succeed on a DC 14 Strength saving throw or be knocked prone.'), ('Tail', 'Melee Weapon Attack: +8 to hit, reach 20 ft., one target. Hit: 32 (6d8 + 5) bludgeoning damage.')],
    },
    'Camel': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Large',
        "ac": 9, "ac_note": '', "hp": 15, "hit_dice": '2d10 + 4',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 8, 'CON': 14, 'INT': 2, 'WIS': 8, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 9',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 2 (1d4) bludgeoning damage.')],
    },
    'Cat': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 12, "ac_note": '', "hp": 2, "hit_dice": '1d4',
        "speed": '40 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 3, 'DEX': 15, 'CON': 10, 'INT': 3, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3'), ('Stealth', '+4')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Smell', 'The cat has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Claws', 'Melee Weapon Attack: +0 to hit, reach 5 ft., one target. Hit: 1 slashing damage.')],
    },
    'Cave Badger': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 12, "ac_note": 'natural armor', "hp": 13, "hit_dice": '2d8 + 4',
        "speed": '30 ft., burrow 15 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 13, 'DEX': 10, 'CON': 15, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 30 ft., tremorsense 60 ft., passive Perception 11',
        "traits": [('Keen Smell', 'The badger has advantage on Wisdom (Perception) checks that rely on smell.'), ('Tunneler', 'When the badger burrows, it leaves tunnels behind.')],
        "actions": [('Multiattack', 'The badger makes two attacks: one with its bite and one with its claws.'), ('Bite', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) piercing damage.'), ('Claws', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 6 (2d4 + 1) slashing damage.')],
    },
    'Cave Bear': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 12, "ac_note": 'natural armor', "hp": 42, "hit_dice": '5d10 + 15',
        "speed": '40 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 20, 'DEX': 10, 'CON': 16, 'INT': 2, 'WIS': 13, 'CHA': 7},
        "skills": [('Perception', '+3')],
        "senses": 'darkvision 60 ft., passive Perception 13',
        "traits": [('Keen Smell', 'The bear has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Multiattack', 'The bear makes two attacks: one with its bite and one with its claws.'), ('Bite', 'Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 9 (1d8 + 5) piercing damage.'), ('Claws', 'Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 12 (2d6 + 5) slashing damage.')],
    },
    'Chimeric Baboon': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 8, 'DEX': 14, 'CON': 11, 'INT': 4, 'WIS': 12, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Pack Tactics', "The baboon has advantage on an attack roll against a creature if at least one of the baboon's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +1 to hit, reach 5 ft., one target. Hit: 1 (1d4 - 1) piercing damage, plus an extra 3 (1d6) poison damage.')],
    },
    'Chimeric Cat': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 12, "ac_note": '', "hp": 2, "hit_dice": '1d4',
        "speed": '40 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 3, 'DEX': 15, 'CON': 10, 'INT': 3, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3'), ('Stealth', '+4')],
        "senses": 'blindsight 60 ft., tremorsense 60 ft., passive Perception 13',
        "traits": [('Keen Smell', 'The cat has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Claws', 'Melee Weapon Attack: +0 to hit, reach 5 ft., one target. Hit: 1 slashing damage.')],
    },
    'Chimeric Fox': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 2, "hit_dice": '1d4',
        "speed": '30 ft., burrow 5 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 16, 'CON': 11, 'INT': 3, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3'), ('Stealth', '+5')],
        "senses": 'darkvision 60 ft., passive Perception 13',
        "traits": [('Chimeric Creation', 'The fox has fur that changes color to match its surroundings, giving it advantage on Dexterity (Stealth) checks.'), ('Keen Hearing', 'The fox has advantage on Wisdom (Perception) checks that rely on hearing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 1 piercing damage.')],
    },
    'Chimeric Hare': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '20 ft., burrow 5 ft., fly 30 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 1, 'DEX': 17, 'CON': 9, 'INT': 2, 'WIS': 11, 'CHA': 4},
        "skills": [('Perception', '+2'), ('Stealth', '+5')],
        "senses": 'passive Perception 12',
        "traits": [('Escape', 'The hare can take the Dash, Disengage, or Hide action as a bonus action on each of its turns.')],
        "actions": [],
    },
    'Chimeric Rat': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 10, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '20 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 11, 'CON': 9, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [('Chimeric Creation', 'The rat has gills, iridescent scales, and the ability to breathe air and water.'), ('Keen Smell', 'The rat has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +0 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Chimeric Weasel': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 3, 'DEX': 16, 'CON': 8, 'INT': 2, 'WIS': 12, 'CHA': 3},
        "skills": [('Perception', '+3'), ('Stealth', '+5')],
        "senses": 'passive Perception 13',
        "traits": [('Chimeric Creation', 'The weasel has glowing eyes that emit bright light out in a 20-foot radius and dim light for an additional 20 feet.'), ('Keen Hearing and Smell', 'The weasel has advantage on Wisdom (Perception) checks that rely on hearing or smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Clawfoot': {
        "cr": 1.0, "cr_label": '1', "size": 'Medium',
        "ac": 13, "ac_note": '', "hp": 19, "hit_dice": '3d8 + 6',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 12, 'DEX': 16, 'CON': 14, 'INT': 4, 'WIS': 12, 'CHA': 10},
        "skills": [('Perception', '+3'), ('Stealth', '+5')],
        "senses": 'passive Perception 13',
        "traits": [('Pack Tactics', "The clawfoot has advantage on an attack roll against a creature if at least one of the clawfoot's allies is within 5 feet of the creature and the ally isn't incapacitated."), ('Pounce', 'If the clawfoot moves at least 20 feet straight toward a creature and then hits it with a claw attack on the same turn, that target must succeed on a DC 11 Strength saving throw or be knocked prone. If the target is prone, the clawfoot can make one bite attack against it as a bonus action.')],
        "actions": [('Multiattack', 'The clawfoot makes two attacks: one with its bite and one with its claws.'), ('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 7 (1d8 + 3) piercing damage.'), ('Claws', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 7 (1d8 + 3) slashing damage.')],
    },
    'Constrictor Snake': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 12, "ac_note": '', "hp": 13, "hit_dice": '2d10 + 2',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 15, 'DEX': 14, 'CON': 12, 'INT': 1, 'WIS': 10, 'CHA': 3},
        "skills": [],
        "senses": 'blindsight 10 ft., passive Perception 10',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 5 (1d6 + 2) piercing damage.'), ('Constrict', "Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 6 (1d8 + 2) bludgeoning damage, and the target is grappled (escape DC 14). Until this grapple ends, the creature is restrained, and the snake can't constrict another target.")],
    },
    'Cow': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 15, "hit_dice": '2d10 + 4',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 10, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Charge', 'If the cow moves at least 20 feet straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 7 (2d6) piercing damage.')],
        "actions": [('Gore', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 7 (1d6 + 4) piercing damage.')],
    },
    'Crab': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 11, "ac_note": 'natural armor', "hp": 2, "hit_dice": '1d4',
        "speed": '20 ft., swim 20 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 2, 'DEX': 11, 'CON': 10, 'INT': 1, 'WIS': 8, 'CHA': 2},
        "skills": [('Stealth', '+2')],
        "senses": 'blindsight 30 ft., passive Perception 9',
        "traits": [('Amphibious', 'The crab can breathe air and water.')],
        "actions": [('Claw', 'Melee Weapon Attack: +0 to hit, reach 5 ft., one target. Hit: 1 bludgeoning damage.')],
    },
    'Cranium Rat': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 12, "ac_note": '', "hp": 2, "hit_dice": '1d4',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 14, 'CON': 10, 'INT': 4, 'WIS': 11, 'CHA': 8},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [('Illumination', 'As a bonus action, the cranium rat can shed dim light from its brain in a 5-foot radius or extinguish the light.'), ('Telepathic Shroud', 'The cranium rat is immune to any effect that would sense its emotions or read its thoughts, as well as to all divination spells.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Crow': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 12, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '10 ft., fly 50 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 2, 'DEX': 14, 'CON': 8, 'INT': 2, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Mimicry', 'The crow can mimic simple sounds it has heard, such as a person whispering, a baby crying, or an animal chittering. A creature that hears the sounds can tell they are imitations with a successful DC 10 Wisdom (Insight) check.')],
        "actions": [('Beak', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Deep Rothé': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d8 + 4',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 10, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Charge', 'If the rothé moves at least 20 feet straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 7 (2d6) piercing damage.'), ('Innate Spellcasting', "The deep rothé's spellcasting ability is Charisma. It can innately cast dancing lights at will, requiring no components.")],
        "actions": [('Gore', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 7 (1d6 + 4) piercing damage.')],
    },
    'Deer': {
        "cr": 0.0, "cr_label": '0', "size": 'Medium',
        "ac": 13, "ac_note": '', "hp": 4, "hit_dice": '1d8',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 11, 'DEX': 16, 'CON': 11, 'INT': 2, 'WIS': 14, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 12',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 2 (1d4) piercing damage.')],
    },
    'Deinonychus': {
        "cr": 1.0, "cr_label": '1', "size": 'Medium',
        "ac": 13, "ac_note": 'natural armor', "hp": 26, "hit_dice": '4d8 + 8',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 15, 'CON': 14, 'INT': 4, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Pounce', 'If the deinonychus moves at least 20 feet straight toward a creature and then hits it with a claw attack on the same turn, that target must succeed on a DC 12 Strength saving throw or be knocked prone. If the target is prone, the deinonychus can make one bite attack against it as a bonus action.')],
        "actions": [('Multiattack', 'The deinonychus makes three attacks: one with its bite and two with its claws.'), ('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 6 (1d8 + 2) piercing damage.'), ('Claw', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 6 (1d8 + 2) slashing damage.')],
    },
    'Diatryma': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 11, "ac_note": '', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 14, 'DEX': 12, 'CON': 12, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Beak', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 6 (1d8 + 2) piercing damage.')],
    },
    'Dimetrodon': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 12, "ac_note": 'natural armor', "hp": 19, "hit_dice": '3d8 + 6',
        "speed": '30 ft., swim 20 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 14, 'DEX': 10, 'CON': 15, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [('Perception', '+2')],
        "senses": 'passive Perception 12',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 9 (2d6 + 2) piercing damage.')],
    },
    'Dolphin': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Medium',
        "ac": 12, "ac_note": 'natural armor', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '0 ft., swim 60 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 14, 'DEX': 13, 'CON': 13, 'INT': 6, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3')],
        "senses": 'blindsight 60 ft., passive Perception 13',
        "traits": [('Charge', 'If the dolphin moves at least 30 feet straight toward a target and then hits it with a slam attack on the same turn, the target takes an extra 3 (1d6) bludgeoning damage.'), ('Hold Breath', 'The dolphin can hold its breath for 20 minutes.')],
        "actions": [('Slam', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) bludgeoning damage.')],
    },
    'Draft Horse': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 10, 'CON': 12, 'INT': 2, 'WIS': 11, 'CHA': 7},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Hooves', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 9 (2d4 + 4) bludgeoning damage.')],
    },
    'Eagle': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 6, 'DEX': 15, 'CON': 10, 'INT': 2, 'WIS': 14, 'CHA': 7},
        "skills": [('Perception', '+4')],
        "senses": 'passive Perception 14',
        "traits": [('Keen Sight', 'The eagle has advantage on Wisdom (Perception) checks that rely on sight.')],
        "actions": [('Talons', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) slashing damage.')],
    },
    'Elder Giant Lizard': {
        "cr": 5.0, "cr_label": '5', "size": 'Huge',
        "ac": 14, "ac_note": 'natural armor', "hp": 85, "hit_dice": '9d12 + 27',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 21, 'DEX': 9, 'CON': 17, 'INT': 2, 'WIS': 10, 'CHA': 7},
        "skills": [('Stealth', '+5')],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Hold Breath', 'The lizard can hold its breath for 30 minutes.')],
        "actions": [('Multiattack', 'The lizard makes two attacks: one with its bite and one with its tail.'), ('Bite', "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 21 (3d10 + 5) piercing damage, and the target is grappled (escape DC 16). Until this grapple ends, the target is restrained, and the lizard can't bite another target."), ('Tail', 'Melee Weapon Attack: +8 to hit, reach 10 ft., one target not grappled by the lizard. Hit: 14 (2d8 + 5) bludgeoning damage. If the target is a creature, it must succeed on a DC 16 Strength saving throw or be knocked prone.')],
    },
    'Elk': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d10 + 2',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 10, 'CON': 12, 'INT': 2, 'WIS': 10, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Charge', 'If the elk moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 7 (2d6) damage. If the target is a creature, it must succeed on a DC 13 Strength saving throw or be knocked prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 6 (1d6 + 3) bludgeoning damage.'), ('Hooves', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one prone creature. Hit: 8 (2d4 + 3) bludgeoning damage.')],
    },
    'Enormous Tentacle': {
        "cr": 2.0, "cr_label": '2', "size": 'Huge',
        "ac": 12, "ac_note": '', "hp": 60, "hit_dice": '8d12 + 8',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 19, 'DEX': 14, 'CON': 12, 'INT': 1, 'WIS': 10, 'CHA': 3},
        "skills": [('Perception', '+2')],
        "senses": 'blindsight 10 ft., passive Perception 12',
        "traits": [('Reach', 'The tentacle can reach anywhere in the room.')],
        "actions": [('Constrict', "Melee Weapon Attack: +6 to hit, reach 35 ft., one creature. Hit: 13 (2d8 + 4) bludgeoning damage, and the target is grappled (escape DC 16). Until this grapple ends, the creature is restrained, and the tentacle can't constrict another target.")],
    },
    'Falcon': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 5, 'DEX': 16, 'CON': 8, 'INT': 2, 'WIS': 14, 'CHA': 6},
        "skills": [('Perception', '+4')],
        "senses": 'passive Perception 14',
        "traits": [('Keen Sight', 'The falcon has advantage on Wisdom (Perception) checks that rely on sight.')],
        "actions": [('Talons', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1 slashing damage.')],
    },
    'Fastieth': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 14, "ac_note": '', "hp": 9, "hit_dice": '2d8',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 12, 'DEX': 18, 'CON': 10, 'INT': 4, 'WIS': 11, 'CHA': 4},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Quickness (Recharge 5–6)', 'The fastieth can take the Dodge action as a bonus action.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 8 (1d8 + 4) piercing damage.')],
    },
    'Female Steeder': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 14, "ac_note": 'natural armor', "hp": 30, "hit_dice": '4d10 + 8',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 16, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 3},
        "skills": [('Stealth', '+7')],
        "senses": 'darkvision 120 ft., passive Perception 10',
        "traits": [('Leap', 'The steeder can expend all its movement on its turn to jump up to 90 feet vertically or horizontally, provided that its speed is at least 30 feet.'), ('Spider Climb', 'The steeder can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 7 (1d8 + 3) piercing damage, and the target must make a DC 12 Constitution saving throw, taking 9 (2d8) acid damage on a failed save, or half as much damage on a successful one.'), ('Sticky Leg (Recharges when the Steeder Has No Creatures Grappled)', "Melee Weapon Attack: +5 to hit, reach 5 ft., one Medium or smaller creature. Hit: The target is stuck to the steeder's leg and grappled until it escapes (escape DC 12).")],
    },
    'Fiendish Giant Spider': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Medium',
        "ac": 13, "ac_note": '', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '40 ft., climb 40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 12, 'DEX': 16, 'CON': 13, 'INT': 3, 'WIS': 12, 'CHA': 4},
        "skills": [('Perception', '+3'), ('Stealth', '+7')],
        "senses": 'blindsight 10 ft., darkvision 60 ft., passive Perception 13',
        "traits": [('Spider Climb', 'The spider can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.'), ('Web Sense', 'While in contact with a web, the spider knows the exact location of any other creature in contact with the same web.'), ('Web Walker', 'The spider ignores movement restrictions caused by webbing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one creature. Hit: 4 (1d6 + 1) piercing damage, and the target must make a DC 11 Constitution saving throw, taking 7 (2d6) poison damage on a failed save, or half as much damage on a successful one. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.')],
    },
    'Fish': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 2, 'DEX': 16, 'CON': 9, 'INT': 1, 'WIS': 7, 'CHA': 2},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 8',
        "traits": [('Water Breathing', 'The fish can breathe only underwater.')],
        "actions": [],
    },
    'Flying Monkey': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '30 ft., climb 20 ft., fly 30 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 8, 'DEX': 14, 'CON': 11, 'INT': 5, 'WIS': 12, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Familiar', "With the DM's permission, the find familiar spell can summon a flying monkey."), ('Pack Tactics', "The flying monkey has advantage on an attack roll against a creature if at least one of the monkey's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +1 to hit, reach 5 ft., one target Hit: 1 (1d4 - 1) piercing damage.')],
    },
    'Flying Snake': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Tiny',
        "ac": 14, "ac_note": '', "hp": 5, "hit_dice": '2d4',
        "speed": '30 ft., fly 60 ft., swim 30 ft.', "flies": True, "swims": True,
        "abilities": {'STR': 4, 'DEX': 18, 'CON': 11, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'blindsight 10 ft., passive Perception 11',
        "traits": [('Flyby', "The snake doesn't provoke opportunity attacks when it flies out of an enemy's reach.")],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 1 piercing damage plus 7 (3d4) poison damage.')],
    },
    'Fox': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 2, "hit_dice": '1d4',
        "speed": '30 ft., burrow 5 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 16, 'CON': 11, 'INT': 3, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3'), ('Stealth', '+5')],
        "senses": 'darkvision 60 ft., passive Perception 13',
        "traits": [('Keen Hearing', 'The fox has advantage on Wisdom (Perception) checks that rely on hearing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 1 piercing damage.')],
    },
    'Frog': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 11, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '20 ft., swim 20 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 1, 'DEX': 13, 'CON': 8, 'INT': 1, 'WIS': 8, 'CHA': 3},
        "skills": [('Perception', '+1'), ('Stealth', '+3')],
        "senses": 'darkvision 30 ft., passive Perception 11',
        "traits": [('Amphibious', 'The frog can breathe air and water.'), ('Standing Leap', "The frog's long jump is up to 10 feet and its high jump is up to 5 feet, with or without a running start.")],
        "actions": [],
    },
    'Giant Badger': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d8 + 4',
        "speed": '30 ft., burrow 10 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 13, 'DEX': 10, 'CON': 15, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 11',
        "traits": [('Keen Smell', 'The badger has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Multiattack', 'The badger makes two attacks: one with its bite and one with its claws.'), ('Bite', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) piercing damage.'), ('Claws', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 6 (2d4 + 1) slashing damage.')],
    },
    'Giant Bat': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 13, "ac_note": '', "hp": 22, "hit_dice": '4d10',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 15, 'DEX': 16, 'CON': 11, 'INT': 2, 'WIS': 12, 'CHA': 6},
        "skills": [],
        "senses": 'blindsight 60 ft., passive Perception 11',
        "traits": [('Echolocation', "The bat can't use its blindsight while deafened."), ('Keen Hearing', 'The bat has advantage on Wisdom (Perception) checks that rely on hearing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 5 (1d6 + 2) piercing damage.')],
    },
    'Giant Canary': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 12, "ac_note": '', "hp": 26, "hit_dice": '4d10 + 4',
        "speed": '30 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 10, 'DEX': 14, 'CON': 12, 'INT': 2, 'WIS': 10, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Peck', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (1d10 + 2) piercing damage.')],
    },
    'Giant Centipede': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Small',
        "ac": 13, "ac_note": 'natural armor', "hp": 4, "hit_dice": '1d6 + 1',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 5, 'DEX': 14, 'CON': 12, 'INT': 1, 'WIS': 7, 'CHA': 3},
        "skills": [],
        "senses": 'blindsight 30 ft., passive Perception 8',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 4 (1d4 + 2) piercing damage, and the target must succeed on a DC 11 Constitution saving throw or take 10 (3d6) poison damage. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.')],
    },
    'Giant Coral Snake': {
        "cr": 4.0, "cr_label": '4', "size": 'Large',
        "ac": 13, "ac_note": '', "hp": 90, "hit_dice": '12d10 + 24',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 12, 'DEX': 16, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 3},
        "skills": [('Perception', '+2')],
        "senses": 'blindsight 10 ft., passive Perception 12',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 8 (2d4 + 3) piercing damage, and the target must succeed on a DC 12 Constitution saving throw or be stunned until the end of its next turn. On a failed save, the target begins to hallucinate and is afflicted with a short-term madness effect (determined randomly or by the DM; see "Madness" in chapter 8 of the Dungeon Master\'s Guide). The effect lasts 10 minutes.')],
    },
    'Giant Crab': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Medium',
        "ac": 15, "ac_note": 'natural armor', "hp": 13, "hit_dice": '3d8',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 13, 'DEX': 15, 'CON': 11, 'INT': 1, 'WIS': 9, 'CHA': 3},
        "skills": [('Stealth', '+4')],
        "senses": 'blindsight 30 ft., passive Perception 9',
        "traits": [('Amphibious', 'The crab can breathe air and water.')],
        "actions": [('Claw', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) bludgeoning damage, and the target is grappled (escape DC 11). The crab has two claws, each of which can grapple only one target.')],
    },
    'Giant Crayfish': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 15, "ac_note": 'natural armor', "hp": 45, "hit_dice": '7d10 + 7',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 15, 'DEX': 13, 'CON': 13, 'INT': 1, 'WIS': 9, 'CHA': 3},
        "skills": [('Stealth', '+3')],
        "senses": 'blindsight 30 ft., passive Perception 9',
        "traits": [('Amphibious', 'The giant crayfish can breathe air and water.')],
        "actions": [('Multiattack', 'The giant crayfish makes two claw attacks.'), ('Claw', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (1d10 + 2) bludgeoning damage, and the target is grappled (escape DC 12). The crayfish has two claws, each of which can grapple only one target.')],
    },
    'Giant Dragonfly': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 16, "ac_note": 'natural armor', "hp": 22, "hit_dice": '4d10',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 15, 'DEX': 18, 'CON': 11, 'INT': 3, 'WIS': 10, 'CHA': 3},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Drone', 'When it beats its wings, the dragonfly emits a loud droning sound that can be heard out to a range of 120 feet.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 6 (1d4 + 4) piercing damage.'), ('Uncanny Dodge', 'The dragonfly halves the damage it takes from an attack made against it, provided it can see the attacker.')],
    },
    'Giant Elk': {
        "cr": 2.0, "cr_label": '2', "size": 'Huge',
        "ac": 14, "ac_note": 'natural armor', "hp": 42, "hit_dice": '5d12 + 10',
        "speed": '60 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 19, 'DEX': 16, 'CON': 14, 'INT': 7, 'WIS': 14, 'CHA': 10},
        "skills": [('Perception', '+4')],
        "senses": 'passive Perception 14',
        "traits": [('Charge', 'If the elk moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 7 (2d6) damage. If the target is a creature, it must succeed on a DC 14 Strength saving throw or be knocked prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +6 to hit, reach 10 ft., one target. Hit: 11 (2d6 + 4) bludgeoning damage.'), ('Hooves', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one prone creature. Hit: 22 (4d8 + 4) bludgeoning damage.')],
    },
    'Giant Fire Beetle': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 13, "ac_note": 'natural armor', "hp": 4, "hit_dice": '1d6 + 1',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 8, 'DEX': 10, 'CON': 12, 'INT': 1, 'WIS': 7, 'CHA': 3},
        "skills": [],
        "senses": 'blindsight 30 ft., passive Perception 8',
        "traits": [('Illumination', 'The beetle sheds bright light in a 10-foot radius and dim light for an additional 10 ft..')],
        "actions": [('Bite', 'Melee Weapon Attack: +1 to hit, reach 5 ft., one target. Hit: 2 (1d6 - 1) slashing damage.')],
    },
    'Giant Flying Spider': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 14, "ac_note": 'natural armor', "hp": 26, "hit_dice": '4d10 + 4',
        "speed": '30 ft., climb 30 ft., fly 40 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 14, 'DEX': 16, 'CON': 12, 'INT': 2, 'WIS': 11, 'CHA': 4},
        "skills": [('Stealth', '+7')],
        "senses": 'blindsight 10 ft., darkvision 60 ft., passive Perception 10',
        "traits": [('Spider Climb', 'The spider can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.'), ('Web Sense', 'While in contact with a web, the spider knows the exact location of any other creature in contact with the same web.'), ('Web Walker', 'The spider ignores movement restrictions caused by webbing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 7 (1d8 + 3) piercing damage, and the target must make a DC 11 Constitution saving throw, taking 9 (2d8) poison damage on a failed save, or half as much damage on a successful one. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.'), ('Web (Recharge 5–6)', 'Ranged Weapon Attack: +5 to hit, range 30/60 ft., one creature. Hit: The target is restrained by webbing. As an action, the restrained target can make a DC 12 Strength check, bursting the webbing on a success. The webbing can also be attacked and destroyed (AC 10; hp 5; vulnerability to fire damage; immunity to bludgeoning, poison, and psychic damage).')],
    },
    'Giant Frog': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 11, "ac_note": '', "hp": 18, "hit_dice": '4d8',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 12, 'DEX': 13, 'CON': 11, 'INT': 2, 'WIS': 10, 'CHA': 3},
        "skills": [('Perception', '+2'), ('Stealth', '+3')],
        "senses": 'darkvision 30 ft., passive Perception 12',
        "traits": [('Amphibious', 'The frog can breathe air and water.'), ('Standing Leap', "The frog's long jump is up to 20 feet and its high jump is up to 10 feet, with or without a running start.")],
        "actions": [('Bite', "Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) piercing damage, and the target is grappled (escape DC 11). Until this grapple ends, the target is restrained, and the frog can't bite another target."), ('Swallow', "The frog makes one bite attack against a Small or smaller target it is grappling. If the attack hits, the target is swallowed, and the grapple ends. The swallowed target is blinded and restrained, it has total cover against attacks and other effects outside the frog, and it takes 5 (2d4) acid damage at the start of each of the frog's turns. The frog can have only one target swallowed at a time. If the frog dies, a swallowed creature is no longer restrained by it and can escape from the corpse using 5 feet of movement, exiting prone.")],
    },
    'Giant Goat': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 11, "ac_note": 'natural armor', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 17, 'DEX': 11, 'CON': 12, 'INT': 3, 'WIS': 12, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Charge', 'If the goat moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 5 (2d4) bludgeoning damage. If the target is a creature, it must succeed on a DC 13 Strength saving throw or be knocked prone.'), ('Sure-Footed', 'The goat has advantage on Strength and Dexterity saving throws made against effects that would knock it prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 8 (2d4 + 3) bludgeoning damage.')],
    },
    'Giant Hyena': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 12, "ac_note": '', "hp": 45, "hit_dice": '6d10 + 12',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 2, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Rampage', 'When the hyena reduces a creature to 0 hit points with a melee attack on its turn, the hyena can take a bonus action to move up to half its speed and make a bite attack.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 10 (2d6 + 3) piercing damage.')],
    },
    'Giant Lightning Eel': {
        "cr": 3.0, "cr_label": '3', "size": 'Large',
        "ac": 13, "ac_note": '', "hp": 42, "hit_dice": '5d10 + 15',
        "speed": '5 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 11, 'DEX': 17, 'CON': 16, 'INT': 2, 'WIS': 12, 'CHA': 3},
        "skills": [],
        "senses": 'blindsight 60 ft., passive Perception 11',
        "traits": [('Water Breathing', 'The eel can breathe only underwater.')],
        "actions": [('Multiattack', 'The eel makes two bite attacks.'), ('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 10 (2d6 + 3) piercing damage plus 4 (1d8) lightning damage.'), ('Lightning Jolt (Recharge 5–6)', "One creature the eel touches within 5 feet of it outside water, or each creature within 15 feet of it in a body of water, must make a DC 12 Constitution saving throw. On failed save, a target takes 13 (3d8) lightning damage. If the target takes any of this damage, the target is stunned until the end of the eel's next turn. On a successful save, a target takes half as much damage and isn't stunned.")],
    },
    'Giant Lizard': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 12, "ac_note": 'natural armor', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 12, 'CON': 13, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 6 (1d8 + 2) piercing damage.'), ('Hold Breath', 'The lizard can hold its breath for 15 minutes. (A lizard that has this trait also has a swimming speed of 30 feet.)'), ('Spider Climb', 'The lizard can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.')],
    },
    'Giant Octopus': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 11, "ac_note": '', "hp": 52, "hit_dice": '8d10 + 8',
        "speed": '10 ft., swim 60 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 17, 'DEX': 13, 'CON': 13, 'INT': 4, 'WIS': 10, 'CHA': 4},
        "skills": [('Perception', '+4'), ('Stealth', '+5')],
        "senses": 'darkvision 60 ft., passive Perception 14',
        "traits": [('Hold Breath', 'While out of water, the octopus can hold its breath for 1 hour.'), ('Underwater Camouflage', 'The octopus has advantage on Dexterity (Stealth) checks made while underwater.'), ('Water Breathing', 'The octopus can breathe only underwater.')],
        "actions": [('Tentacles', "Melee Weapon Attack: +5 to hit, reach 15 ft., one target. Hit: 10 (2d6 + 3) bludgeoning damage. If the target is a creature, it is grappled (escape DC 16). Until this grapple ends, the target is restrained, and the octopus can't use its tentacles on another target."), ('Ink Cloud (Recharges after a Short or Long Rest)', 'A 20-foot-radius cloud of ink extends all around the octopus if it is underwater. The area is heavily obscured for 1 minute, although a significant current can disperse the ink. After releasing the ink, the octopus can use the Dash action as a bonus action.')],
    },
    'Giant Poisonous Snake': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 14, "ac_note": '', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 10, 'DEX': 18, 'CON': 13, 'INT': 2, 'WIS': 10, 'CHA': 3},
        "skills": [('Perception', '+2')],
        "senses": 'blindsight 10 ft., passive Perception 12',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 10 ft., one target. Hit: 6 (1d4 + 4) piercing damage, and the target must make a DC 11 Constitution saving throw, taking 10 (3d6) poison damage on a failed save, or half as much damage on a successful one.')],
    },
    'Giant Rat': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 7, "hit_dice": '2d6',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 7, 'DEX': 15, 'CON': 11, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Keen Smell', 'The rat has advantage on Wisdom (Perception) checks that rely on smell.'), ('Pack Tactics', "The rat has advantage on an attack roll against a creature if at least one of the rat's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) piercing damage.'), ('Bite', "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) piercing damage. If the target is a creature, it must succeed on a DC 10 Constitution saving throw or contract a disease. Until the disease is cured, the target can't regain hit points except by magical means, and the target's hit point maximum decreases by 3 (1d6) every 24 hours. If the target's hit point maximum drops to 0 as a result of this disease, the target dies.")],
    },
    'Giant Raven': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 22, "hit_dice": '3d10 + 6',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 15, 'DEX': 10, 'CON': 15, 'INT': 6, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Sight and Smell', 'The raven has advantage on Wisdom (Perception) checks that rely on sight or smell.'), ('Pack Tactics', "The raven has advantage on an attack roll against a creature if at least one of the raven's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Multiattack', 'The raven makes two attacks: one with its beak and one with its talons.'), ('Beak', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (2d4 + 2) piercing damage.'), ('Talons', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 9 (2d6 + 2) slashing damage.')],
    },
    'Giant Riding Lizard': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 12, "ac_note": 'natural armor', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 12, 'CON': 13, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [('Spider Climb', 'The lizard can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 6 (1d8 + 2) piercing damage.')],
    },
    'Giant Rocktopus': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 11, "ac_note": '', "hp": 52, "hit_dice": '8d10 + 8',
        "speed": '20 ft., climb 10 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 17, 'DEX': 13, 'CON': 13, 'INT': 4, 'WIS': 10, 'CHA': 4},
        "skills": [('Perception', '+4'), ('Stealth', '+5')],
        "senses": 'darkvision 60 ft., passive Perception 14',
        "traits": [('Camouflage', 'The octopus has advantage on Dexterity (Stealth) checks.')],
        "actions": [('Tentacles', "Melee Weapon Attack: +5 to hit, reach 15 ft., one target. Hit: 10 (2d6 + 3) bludgeoning damage. If the target is a creature, it is grappled (escape DC 16). Until this grapple ends, the target is restrained, and the octopus can't use its tentacles on another target."), ('Ink Cloud (Recharges after a Short or Long Rest)', 'A 20-foot-radius cloud of ink extends all around the octopus if it is underwater. The area is heavily obscured for 1 minute, although a significant current can disperse the ink. After releasing the ink, the octopus can use the Dash action as a bonus action.')],
    },
    'Giant Sea Eel': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 14, "ac_note": 'natural armor', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 11, 'DEX': 14, 'CON': 12, 'INT': 7, 'WIS': 10, 'CHA': 7},
        "skills": [('Perception', '+2'), ('Stealth', '+4')],
        "senses": 'darkvision 60 ft., passive Perception 12',
        "traits": [('Water Breathing', 'The eel can breathe only underwater.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 13 (2d10 + 2) piercing damage.')],
    },
    'Giant Sea Horse': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 13, "ac_note": 'natural armor', "hp": 16, "hit_dice": '3d10',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 12, 'DEX': 15, 'CON': 11, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Charge', 'If the sea horse moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 7 (2d6) bludgeoning damage. If the target is a creature, it must succeed on a DC 11 Strength saving throw or be knocked prone.'), ('Water Breathing', 'The sea horse can breathe only underwater.')],
        "actions": [('Ram', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) bludgeoning damage.')],
    },
    'Giant Snail': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 11, "ac_note": 'natural armor', "hp": 22, "hit_dice": '4d10',
        "speed": '10 ft., climb 10 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 3, 'CON': 11, 'INT': 3, 'WIS': 10, 'CHA': 3},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Salt Osmosis', 'Whenever the snail starts its turn in contact with a pound or more of salt, it takes 1d4 necrotic damage. Using an action to sprinkle a pound of salt on the snail deals 1d4 necrotic damage to it immediately and another 1d4 necrotic damage to it at the start of its next turn (after which the salt rubs off), provided the snail has not withdrawn into its shell.')],
        "actions": [('Slam', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) bludgeoning damage.'), ('Shell Defense', 'The snail withdraws into its shell, gaining a +4 bonus to its AC until it emerges. It can emerge from its shell as a bonus action on its turn.')],
    },
    'Giant Snapping Turtle': {
        "cr": 3.0, "cr_label": '3', "size": 'Large',
        "ac": 17, "ac_note": 'natural armor', "hp": 75, "hit_dice": '10d10 + 20',
        "speed": '30 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 19, 'DEX': 10, 'CON': 14, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 11',
        "traits": [('Amphibious', 'The turtle can breathe air and water.'), ('Stable', 'Whenever an effect knocks the turtle prone, it can make a DC 10 Constitution saving throw to avoid being knocked prone. A prone turtle is upside down. To stand up, it must succeed on a DC 10 Dexterity check on its turn and then use all its movement for that turn.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 18 (4d6 + 4) slashing damage.')],
    },
    'Giant Space Hamster': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 11, "ac_note": '', "hp": 22, "hit_dice": '4d10',
        "speed": '30 ft., burrow 10 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 14, 'DEX': 12, 'CON': 10, 'INT': 2, 'WIS': 12, 'CHA': 4},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (2d4 + 2) piercing damage.')],
    },
    'Giant Subterranean Lizard': {
        "cr": 4.0, "cr_label": '4', "size": 'Huge',
        "ac": 14, "ac_note": 'natural armor', "hp": 66, "hit_dice": '7d12 + 21',
        "speed": '30 ft., swim 50 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 21, 'DEX': 9, 'CON': 17, 'INT': 2, 'WIS': 10, 'CHA': 7},
        "skills": [('Stealth', '+3')],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Multiattack', 'The lizard makes two attacks: one with its bite and one with its tail. One attack can be replaced by Swallow.'), ('Bite', "Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 16 (2d10 + 5) piercing damage and the target is grappled (escape DC 15). Until this grapple ends, the target is restrained, and the lizard can't bite another target."), ('Tail', 'Melee Weapon Attack: +7 to hit, reach 10 ft., one target not grappled by the lizard. Hit: 12 (2d6 + 5) bludgeoning damage. If the target is a creature, it must succeed on a DC 15 Strength saving throw or be knocked prone.'), ('Swallow', "Melee Weapon Attack: +7 to hit, reach 5 ft., one Medium or smaller creature the lizard is grappling. Hit: 16 (2d10 + 5) piercing damage. The target is swallowed, and the grapple ends. The swallowed target is blinded and restrained, it has total cover against attacks and other effects outside the lizard, and it takes 10 (3d6) acid damage at the start of each of the lizard's turns. The lizard can have only one target swallowed at a time. >If the lizard dies, a swallowed creature is no longer restrained by it and can escape from the corpse using 10 feet of movement, exiting prone.")],
    },
    'Giant Swan': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 13, "ac_note": '', "hp": 26, "hit_dice": '4d10 + 4',
        "speed": '10 ft., fly 80 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 16, 'DEX': 17, 'CON': 13, 'INT': 8, 'WIS': 14, 'CHA': 10},
        "skills": [('Perception', '+4')],
        "senses": 'passive Perception 14',
        "traits": [('Keen Sight', 'The swan has advantage on Wisdom (Perception) checks that rely on sight.')],
        "actions": [('Multiattack', 'The swan makes two attacks with its beak.'), ('Beak', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 6 (1d6 + 3) piercing damage.')],
    },
    'Giant Vulture': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 22, "hit_dice": '3d10 + 6',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 15, 'DEX': 10, 'CON': 15, 'INT': 6, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Sight and Smell', 'The vulture has advantage on Wisdom (Perception) checks that rely on sight or smell.'), ('Pack Tactics', "The vulture has advantage on an attack roll against a creature if at least one of the vulture's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Multiattack', 'The vulture makes two attacks: one with its beak and one with its talons.'), ('Beak', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (2d4 + 2) piercing damage.'), ('Talons', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 9 (2d6 + 2) slashing damage.')],
    },
    'Giant Walrus': {
        "cr": 4.0, "cr_label": '4', "size": 'Huge',
        "ac": 9, "ac_note": '', "hp": 85, "hit_dice": '9d12 + 27',
        "speed": '20 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 22, 'DEX': 9, 'CON': 16, 'INT': 3, 'WIS': 11, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Hold Breath', 'The walrus can hold its breath for 30 minutes.')],
        "actions": [('Multiattack', 'The walrus makes two attacks: one with its body flop and one with its tusks.'), ('Body Flop', 'Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 15 (2d8 + 6) bludgeoning damage.'), ('Tusks', 'Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 16 (3d6 + 6) piercing damage.')],
    },
    'Giant Wasp': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Medium',
        "ac": 12, "ac_note": '', "hp": 13, "hit_dice": '3d8',
        "speed": '10 ft., fly 50 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 10, 'DEX': 14, 'CON': 10, 'INT': 1, 'WIS': 10, 'CHA': 3},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Sting', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 5 (1d6 + 2) piercing damage, and the target must make a DC 11 Constitution saving throw, taking 10 (3d6) poison damage on a failed save, or half as much damage on a successful one. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.')],
    },
    'Giant Weasel': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Medium',
        "ac": 13, "ac_note": '', "hp": 9, "hit_dice": '2d8',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 11, 'DEX': 16, 'CON': 10, 'INT': 4, 'WIS': 12, 'CHA': 5},
        "skills": [('Perception', '+3'), ('Stealth', '+5')],
        "senses": 'darkvision 60 ft., passive Perception 13',
        "traits": [('Keen Hearing and Smell', 'The weasel has advantage on Wisdom (Perception) checks that rely on hearing or smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 5 (1d4 + 3) piercing damage.')],
    },
    'Giant White Moray Eel': {
        "cr": 2.0, "cr_label": '2', "size": 'Huge',
        "ac": 12, "ac_note": '', "hp": 60, "hit_dice": '8d12 + 8',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 19, 'DEX': 14, 'CON': 12, 'INT': 1, 'WIS': 10, 'CHA': 3},
        "skills": [('Perception', '+2'), ('Stealth', '+4')],
        "senses": 'blindsight 10 ft., passive Perception 12',
        "traits": [('Water Breathing', 'The eel can breathe only underwater.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 10 ft., one creature. Hit: 11 (2d6 + 4) piercing damage.')],
    },
    'Giant Wolf Spider': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 13, "ac_note": '', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '40 ft., climb 40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 12, 'DEX': 16, 'CON': 13, 'INT': 3, 'WIS': 12, 'CHA': 4},
        "skills": [('Perception', '+3'), ('Stealth', '+7')],
        "senses": 'blindsight 10 ft., darkvision 60 ft., passive Perception 13',
        "traits": [('Spider Climb', 'The spider can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.'), ('Web Sense', 'While in contact with a web, the spider knows the exact location of any other creature in contact with the same web.'), ('Web Walker', 'The spider ignores movement restrictions caused by webbing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one creature. Hit: 4 (1d6 + 1) piercing damage, and the target must make a DC 11 Constitution saving throw, taking 7 (2d6) poison damage on a failed save, or half as much damage on a successful one. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.')],
    },
    'Goat': {
        "cr": 0.0, "cr_label": '0', "size": 'Medium',
        "ac": 10, "ac_note": '', "hp": 4, "hit_dice": '1d8',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 12, 'DEX': 10, 'CON': 11, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Charge', 'If the goat moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 2 (1d4) bludgeoning damage. If the target is a creature, it must succeed on a DC 10 Strength saving throw or be knocked prone.'), ('Sure-Footed', 'The goat has advantage on Strength and Dexterity saving throws made against effects that would knock it prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 3 (1d4 + 1) bludgeoning damage.')],
    },
    'Golden Stag': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d10 + 2',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 10, 'CON': 12, 'INT': 2, 'WIS': 10, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Charge', 'If the elk moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 7 (2d6) damage. If the target is a creature, it must succeed on a DC 13 Strength saving throw or be knocked prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 6 (1d6 + 3) bludgeoning damage.'), ('Hooves', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one prone creature. Hit: 8 (2d4 + 3) bludgeoning damage.')],
    },
    'Hadrosaurus': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 11, "ac_note": 'natural armor', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 10, 'CON': 13, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [('Perception', '+2')],
        "senses": 'passive Perception 12',
        "traits": [],
        "actions": [('Tail', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (1d10 + 2) bludgeoning damage.')],
    },
    'Hare': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '20 ft., burrow 5 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 1, 'DEX': 17, 'CON': 9, 'INT': 2, 'WIS': 11, 'CHA': 4},
        "skills": [('Perception', '+2'), ('Stealth', '+5')],
        "senses": 'passive Perception 12',
        "traits": [('Escape', 'The hare can take the Dash, Disengage, or Hide action as a bonus action on each of its turns.')],
        "actions": [],
    },
    'Hawk': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 5, 'DEX': 16, 'CON': 8, 'INT': 2, 'WIS': 14, 'CHA': 6},
        "skills": [('Perception', '+4')],
        "senses": 'passive Perception 14',
        "traits": [('Keen Sight', 'The hawk has advantage on Wisdom (Perception) checks that rely on sight.')],
        "actions": [('Talons', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1 slashing damage.')],
    },
    'Hellwasp Grub': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Small',
        "ac": 13, "ac_note": 'natural armor', "hp": 4, "hit_dice": '1d6 + 1',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 5, 'DEX': 14, 'CON': 12, 'INT': 1, 'WIS': 7, 'CHA': 3},
        "skills": [],
        "senses": 'blindsight 30 ft., passive Perception 8',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 4 (1d4 + 2) piercing damage, and the target must succeed on a DC 11 Constitution saving throw or take 10 (3d6) poison damage. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.')],
    },
    'Huge Polar Bear': {
        "cr": 2.0, "cr_label": '2', "size": 'Huge',
        "ac": 12, "ac_note": 'natural armor', "hp": 65, "hit_dice": '5d12 + 15',
        "speed": '40 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 20, 'DEX': 10, 'CON': 16, 'INT': 2, 'WIS': 13, 'CHA': 7},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Smell', 'The bear has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Multiattack', 'The bear makes two attacks: one with its bite and one with its claws.'), ('Bite', 'Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 9 (1d8 + 5) piercing damage.'), ('Claws', 'Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 12 (2d6 + 5) slashing damage.')],
    },
    'Hulking Crab': {
        "cr": 5.0, "cr_label": '5', "size": 'Huge',
        "ac": 17, "ac_note": 'natural armor', "hp": 76, "hit_dice": '8d12 + 24',
        "speed": '20 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 19, 'DEX': 8, 'CON': 16, 'INT': 3, 'WIS': 11, 'CHA': 3},
        "skills": [('Stealth', '+2')],
        "senses": 'blindsight 30 ft., passive Perception 10',
        "traits": [('Amphibious', 'The crab can breathe air and water.'), ('Shell Camouflage', 'While the crab remains motionless with its eyestalks and pincers tucked close to its body, it resembles a natural formation or a pile of detritus. A creature within 30 feet of it can discern its true nature with a successful DC 15 Intelligence (Nature) check.')],
        "actions": [('Multiattack', 'The crab makes two attacks with its claws.'), ('Claw', 'Melee Weapon Attack: +7 to hit, reach 10 ft., one target. Hit: 20 (3d10 + 4) bludgeoning damage, and the target is grappled (escape DC 15). The crab has two claws, each of which can grapple only one target')],
    },
    'Hunter Shark': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 12, "ac_note": 'natural armor', "hp": 45, "hit_dice": '6d10 + 12',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 18, 'DEX': 13, 'CON': 15, 'INT': 1, 'WIS': 10, 'CHA': 4},
        "skills": [('Perception', '+2')],
        "senses": 'blindsight 30 ft., passive Perception 12',
        "traits": [('Blood Frenzy', "The shark has advantage on melee attack rolls against any creature that doesn't have all its hit points."), ('Water Breathing', 'The shark can breathe only underwater.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 13 (2d8 + 4) piercing damage.')],
    },
    'Hyena': {
        "cr": 0.0, "cr_label": '0', "size": 'Medium',
        "ac": 11, "ac_note": '', "hp": 5, "hit_dice": '1d8 + 1',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 11, 'DEX': 13, 'CON': 12, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Pack Tactics', "The hyena has advantage on an attack roll against a creature if at least one of the hyena's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 3 (1d6) piercing damage.')],
    },
    'Ice Spider': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 14, "ac_note": 'natural armor', "hp": 26, "hit_dice": '4d10 + 4',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 14, 'DEX': 16, 'CON': 12, 'INT': 2, 'WIS': 11, 'CHA': 4},
        "skills": [('Stealth', '+7')],
        "senses": 'blindsight 10 ft., darkvision 60 ft., passive Perception 10',
        "traits": [('Spider Climb', 'The spider can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.'), ('Web Sense', 'While in contact with a web, the spider knows the exact location of any other creature in contact with the same web.'), ('Web Walker', 'The spider ignores movement restrictions caused by webbing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 7 (1d8 + 3) piercing damage, and the target must make a DC 11 Constitution saving throw, taking 9 (2d8) poison damage on a failed save, or half as much damage on a successful one. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.'), ('Icy Web (Recharge 5–6)', 'Ranged Weapon Attack: +5 to hit, range 30/60 ft., one creature. Hit: The target is restrained by webbing, and takes 1 cold damage at the start of each of its turns. As an action, the restrained target can make a DC 12 Strength check, bursting the webbing on a success. The webbing can also be attacked and destroyed (AC 10; hp 5; vulnerability to fire damage; immunity to poison, and psychic damage).')],
    },
    'Ice Spider Queen': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 14, "ac_note": 'natural armor', "hp": 44, "hit_dice": '4d10 + 4',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 14, 'DEX': 16, 'CON': 12, 'INT': 2, 'WIS': 11, 'CHA': 4},
        "skills": [('Stealth', '+7')],
        "senses": 'blindsight 10 ft., darkvision 60 ft., passive Perception 10',
        "traits": [('Cold Aura', 'Any creature that starts its turn within 5 feet of the spider takes 5 (2d4) cold damage.'), ('Spider Climb', 'The spider can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.'), ('Web Sense', 'While in contact with a web, the spider knows the exact location of any other creature in contact with the same web.'), ('Web Walker', 'The spider ignores movement restrictions caused by webbing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 7 (1d8 + 3) piercing damage, and the target must make a DC 11 Constitution saving throw, taking 9 (2d8) poison damage on a failed save, or half as much damage on a successful one. If the poison damage reduces the target to 0 hit points, the target is stable but poisoned for 1 hour, even after regaining hit points, and is paralyzed while poisoned in this way.'), ('Icy Web (Recharge 5–6)', 'Ranged Weapon Attack: +5 to hit, range 30/60 ft., one creature. Hit: The target is restrained by webbing, and takes 2 (1d4) cold damage at the start of each of its turns. As an action, the restrained target can make a DC 12 Strength check, bursting the webbing on a success. The webbing can also be attacked and destroyed (AC 10; hp 5; vulnerability to fire damage; immunity to poison, and psychic damage).')],
    },
    'Jackal': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 8, 'DEX': 15, 'CON': 11, 'INT': 3, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Hearing and Smell', 'The jackal has advantage on Wisdom (Perception) checks that rely on hearing or smell.'), ('Pack Tactics', "The jackal has advantage on an attack roll against a creature if at least one of the jackal's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +1 to hit, reach 5 ft., one target. Hit: 1 (1d4 - 1) piercing damage.')],
    },
    'Jaculi': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 14, "ac_note": 'natural armor', "hp": 16, "hit_dice": '3d10',
        "speed": '30 ft., climb 20 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 14, 'CON': 11, 'INT': 2, 'WIS': 8, 'CHA': 3},
        "skills": [('Athletics', '+4'), ('Perception', '+1'), ('Stealth', '+4')],
        "senses": 'blindsight 30 ft., passive Perception 11',
        "traits": [('Camouflage', 'The jaculi has advantage on Dexterity (Stealth) checks made to hide.'), ('Keen Smell', 'The jaculi has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 9 (2d6 + 2) piercing damage.'), ('Spring', 'The jaculi springs up to 30 feet in a straight line and makes a bite attack against a target within its reach. This attack has advantage if the jaculi springs at least 10 feet. If the attack hits, the bite deals an extra 7 (2d6) piercing damage.')],
    },
    'Knucklehead Trout': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 7, "hit_dice": '2d6',
        "speed": '0 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 14, 'DEX': 14, 'CON': 11, 'INT': 1, 'WIS': 6, 'CHA': 1},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 8',
        "traits": [('Water Breathing', 'The trout can breathe only underwater.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) piercing damage.'), ('Tail', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) bludgeoning damage.')],
    },
    'Koi Prawn': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 13, "ac_note": 'natural armor', "hp": 16, "hit_dice": '3d10',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 12, 'DEX': 15, 'CON': 11, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Charge', 'If the prawn moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 7 (2d6) bludgeoning damage. If the target is a creature, it must succeed on a DC 11 Strength saving throw or be knocked prone.'), ('Water Breathing', 'The prawn can breathe only underwater.')],
        "actions": [('Ram', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) bludgeoning damage.')],
    },
    'Lizard': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 10, "ac_note": '', "hp": 2, "hit_dice": '1d4',
        "speed": '20 ft., climb 20 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 11, 'CON': 10, 'INT': 1, 'WIS': 8, 'CHA': 3},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 9',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +0 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Male Steeder': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 12, "ac_note": 'natural armor', "hp": 13, "hit_dice": '2d8 + 4',
        "speed": '30 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 12, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 3},
        "skills": [('Stealth', '+5')],
        "senses": 'darkvision 120 ft., passive Perception 10',
        "traits": [('Leap', 'The steeder can expend all its movement on its turn to jump up to 60 feet vertically or horizontally, provided that its speed is at least 30 feet.'), ('Spider Climb', 'The steeder can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 7 (1d8 + 2) piercing damage, and the target must make a DC 12 Constitution saving throw, taking 4 (1d8) acid damage on a failed save, or half as much damage on a successful one.'), ('Sticky Leg (Recharges when the Steeder Has No Creatures Grappled)', "Melee Weapon Attack: +4 to hit, reach 5 ft., one Small or Tiny creature. Hit: The target is stuck to the steeder's leg and grappled until it escapes (escape DC 12).")],
    },
    'Mastiff': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Medium',
        "ac": 12, "ac_note": '', "hp": 5, "hit_dice": '1d8 + 1',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 13, 'DEX': 14, 'CON': 12, 'INT': 3, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Hearing and Smell', 'The mastiff has advantage on Wisdom (Perception) checks that rely on hearing or smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) piercing damage. If the target is a creature, it must succeed on a DC 11 Strength saving throw or be knocked prone.')],
    },
    'Moonshark': {
        "cr": 5.0, "cr_label": '5', "size": 'Huge',
        "ac": 13, "ac_note": 'natural armor', "hp": 126, "hit_dice": '11d12 + 55',
        "speed": '0 ft., swim 50 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 23, 'DEX': 11, 'CON': 21, 'INT': 1, 'WIS': 10, 'CHA': 5},
        "skills": [('Perception', '+3')],
        "senses": 'blindsight 60 ft., passive Perception 13',
        "traits": [('Blood Frenzy', "The shark has advantage on melee attack rolls against any creature that doesn't have all its hit points."), ('Silver Spear', 'A character within 5 feet of the shark can use an action to try to dislodge the spear, doing so with a successful DC 13 Strength (Athletics) check. While the spear is lodged in the shark, the shark glows with silvery illumination, shedding bright light in a 10-foot radius and dim light for an additional 10 feet.'), ('Water Breathing', 'The shark can breathe only underwater.')],
        "actions": [('Bite', "Melee Weapon Attack: +9 to hit, reach 5 ft., one target. Hit: 22 (3d10 + 6) piercing damage. If the shark misses, it can use a bonus action to swim up to 25 feet. This movement doesn't provoke opportunity attacks.")],
    },
    'Moorbounder': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 13, "ac_note": 'natural armor', "hp": 30, "hit_dice": '4d10 + 8',
        "speed": '70 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 14, 'CON': 14, 'INT': 2, 'WIS': 13, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 11',
        "traits": [('Standing Leap', "The moorbounder's long jump is up to 40 feet and its high jump is up to 20 feet, with or without a running start.")],
        "actions": [('Claws', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 14 (4d4 + 4) slashing damage.')],
    },
    'Mountain Goat': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Medium',
        "ac": 11, "ac_note": '', "hp": 13, "hit_dice": '2d8 + 4',
        "speed": '40 ft., climb 30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 14, 'DEX': 12, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Charge', 'If the goat moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 3 (1d6) bludgeoning damage. If the target is a creature, it must succeed on a DC 12 Strength saving throw or be knocked prone.'), ('Sure-Footed', 'The goat has advantage on Strength and Dexterity saving throws made against effects that would knock it prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) bludgeoning damage.')],
    },
    'Mule': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Medium',
        "ac": 10, "ac_note": '', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 14, 'DEX': 10, 'CON': 13, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Beast of Burden', 'The mule is considered to be a Large animal for the purpose of determining its carrying capacity.'), ('Sure-Footed', 'The mule has advantage on Strength and Dexterity saving throws made against effects that would knock it prone.')],
        "actions": [('Hooves', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) bludgeoning damage.')],
    },
    'Octopus': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '5 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 4, 'DEX': 15, 'CON': 11, 'INT': 3, 'WIS': 10, 'CHA': 4},
        "skills": [('Perception', '+2'), ('Stealth', '+4')],
        "senses": 'darkvision 30 ft., passive Perception 12',
        "traits": [('Hold Breath', 'While out of water, the octopus can hold its breath for 30 minutes.'), ('Underwater Camouflage', 'The octopus has advantage on Dexterity (Stealth) checks made while underwater.'), ('Water Breathing', 'The octopus can breathe only underwater.')],
        "actions": [('Tentacles', "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1 bludgeoning damage, and the target is grappled (escape DC 10). Until this grapple ends, the octopus can't use its tentacles on another target."), ('Ink Cloud (Recharges after a Short or Long Rest)', 'A 5-foot-radius cloud of ink extends all around the octopus if it is underwater. The area is heavily obscured for 1 minute, although a significant current can disperse the ink. After releasing the ink, the octopus can use the Dash action as a bonus action.')],
    },
    'Owl': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 11, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '5 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 3, 'DEX': 13, 'CON': 8, 'INT': 2, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3'), ('Stealth', '+3')],
        "senses": 'darkvision 120 ft., passive Perception 13',
        "traits": [('Flyby', "The owl doesn't provoke opportunity attacks when it flies out of an enemy's reach."), ('Keen Hearing and Sight', 'The owl has advantage on Wisdom (Perception) checks that rely on hearing or sight.')],
        "actions": [('Talons', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 1 slashing damage.')],
    },
    'Ox': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 15, "hit_dice": '2d10 + 4',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 10, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Beast of Burden', 'The oxen is considered to be a Huge animal for the purposes of determining its carrying capacity.'), ('Charge', 'If the ox moves at least 20 feet straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 7 (2d6) piercing damage.')],
        "actions": [('Gore', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 7 (1d6 + 4) piercing damage.')],
    },
    'Peacock': {
        "cr": 0.0, "cr_label": '0', "size": 'Medium',
        "ac": 10, "ac_note": '', "hp": 5, "hit_dice": '1d8 + 1',
        "speed": '10 ft., fly 50 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 7, 'DEX': 10, 'CON': 13, 'INT': 2, 'WIS': 12, 'CHA': 4},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Sight and Smell', 'The peacock has advantage on Wisdom (Perception) checks that rely on sight or smell.'), ('Pack Tactics', "The peacock has advantage on an attack roll against a creature if at least one of the peacock's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Beak', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 2 (1d4) piercing damage.')],
    },
    'Pig': {
        "cr": 0.0, "cr_label": '0', "size": 'Medium',
        "ac": 11, "ac_note": 'natural armor', "hp": 5, "hit_dice": '1d8 + 1',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 13, 'DEX': 11, 'CON': 12, 'INT': 2, 'WIS': 9, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 9',
        "traits": [],
        "actions": [],
    },
    'Plesiosaurus': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 13, "ac_note": 'natural armor', "hp": 68, "hit_dice": '8d10 + 24',
        "speed": '20 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 18, 'DEX': 15, 'CON': 16, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [('Perception', '+3'), ('Stealth', '+4')],
        "senses": 'passive Perception 13',
        "traits": [('Hold Breath', 'The plesiosaurus can hold its breath for 1 hour.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 10 ft., one target. Hit: 14 (3d6 + 4) piercing damage.')],
    },
    'Poisonous Snake': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 2, "hit_dice": '1d4',
        "speed": '30 ft., swim 30 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 2, 'DEX': 16, 'CON': 11, 'INT': 1, 'WIS': 10, 'CHA': 3},
        "skills": [],
        "senses": 'blindsight 10 ft., passive Perception 10',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1 piercing damage, and the target must make a DC 10 Constitution saving throw, taking 5 (2d4) poison damage on a failed save, or half as much damage on a successful one.')],
    },
    'Pony': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Medium',
        "ac": 10, "ac_note": '', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 15, 'DEX': 10, 'CON': 13, 'INT': 2, 'WIS': 11, 'CHA': 7},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Hooves', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (2d4 + 2) bludgeoning damage.')],
    },
    'Pteranodon': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 13, "ac_note": 'natural armor', "hp": 13, "hit_dice": '3d8',
        "speed": '10 ft., fly 60 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 12, 'DEX': 15, 'CON': 10, 'INT': 2, 'WIS': 9, 'CHA': 5},
        "skills": [('Perception', '+1')],
        "senses": 'passive Perception 11',
        "traits": [('Flyby', "The pteranodon doesn't provoke opportunity attacks when it flies out of an enemy's reach.")],
        "actions": [('Bite', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 6 (2d4 + 1) piercing damage.')],
    },
    'Quetzalcoatlus': {
        "cr": 2.0, "cr_label": '2', "size": 'Huge',
        "ac": 13, "ac_note": 'natural armor', "hp": 30, "hit_dice": '4d12 + 4',
        "speed": '10 ft., fly 80 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 15, 'DEX': 13, 'CON': 13, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [('Perception', '+2')],
        "senses": 'passive Perception 12',
        "traits": [('Dive Attack', 'If the quetzalcoatlus is flying and dives at least 30 feet toward a target and then hits with a bite attack, the attack deals an extra 10 (3d6) damage to the target.'), ('Flyby', "The quetzalcoatlus doesn't provoke an opportunity attack when it flies out of an enemy's reach.")],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 10 ft., one creature. Hit: 12 (3d6 + 2) piercing damage.')],
    },
    'Quipper': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 2, 'DEX': 16, 'CON': 9, 'INT': 1, 'WIS': 7, 'CHA': 2},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 8',
        "traits": [('Blood Frenzy', "The quipper has advantage on melee attack rolls against any creature that doesn't have all its hit points."), ('Water Breathing', 'The quipper can breathe only underwater.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Rat': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 10, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '20 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 11, 'CON': 9, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [('Keen Smell', 'The rat has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +0 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Raven': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 12, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '10 ft., fly 50 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 2, 'DEX': 14, 'CON': 8, 'INT': 2, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Mimicry', 'The raven can mimic simple sounds it has heard, such as a person whispering, a baby crying, or an animal chittering. A creature that hears the sounds can tell they are imitations with a successful DC 10 Wisdom (Insight) check.')],
        "actions": [('Beak', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Reef Shark': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Medium',
        "ac": 12, "ac_note": 'natural armor', "hp": 22, "hit_dice": '4d8 + 4',
        "speed": '0 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 14, 'DEX': 13, 'CON': 13, 'INT': 1, 'WIS': 10, 'CHA': 4},
        "skills": [('Perception', '+2')],
        "senses": 'blindsight 30 ft., passive Perception 12',
        "traits": [('Pack Tactics', "The shark has advantage on an attack roll against a creature if at least one of the shark's allies is within 5 feet of the creature and the ally isn't incapacitated."), ('Water Breathing', 'The shark can breathe only underwater.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 6 (1d8 + 2) piercing damage.')],
    },
    'Reindeer': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d10 + 2',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 10, 'CON': 12, 'INT': 2, 'WIS': 10, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Charge', 'If the reindeer moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 7 (2d6) damage. If the target is a creature, it must succeed on a DC 13 Strength saving throw or be knocked prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 6 (1d6 + 3) bludgeoning damage.'), ('Hooves', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one prone creature. Hit: 8 (2d4 + 3) bludgeoning damage.')],
    },
    'Relic Sloth': {
        "cr": 2.0, "cr_label": '2', "size": 'Huge',
        "ac": 13, "ac_note": 'natural armor', "hp": 76, "hit_dice": '8d12 + 24',
        "speed": '20 ft., climb 20 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 20, 'DEX': 9, 'CON': 17, 'INT': 2, 'WIS': 12, 'CHA': 8},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [],
        "actions": [('Claws', 'Melee Weapon Attack: +7 to hit, reach 10 ft., one target. Hit: 14 (2d8 + 5) slashing damage, and the target is grappled (escape DC 15). The relic sloth can grapple no more than two targets at a time.'), ('Slow but Sturdy', 'When the relic sloth is subjected to an effect that would move it out of its current space or knock it prone, it is neither moved nor knocked prone.')],
    },
    'Riding Horse': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d10 + 2',
        "speed": '60 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 10, 'CON': 12, 'INT': 2, 'WIS': 11, 'CHA': 7},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Hooves', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 8 (2d4 + 3) bludgeoning damage.')],
    },
    'Rooster': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '10 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 5, 'DEX': 16, 'CON': 8, 'INT': 2, 'WIS': 14, 'CHA': 6},
        "skills": [('Perception', '+4')],
        "senses": 'passive Perception 14',
        "traits": [('Keen Sight', 'The rooster has advantage on Wisdom (Perception) checks that rely on sight.')],
        "actions": [('Talons', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1 slashing damage.')],
    },
    'Rothé': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 15, "hit_dice": '2d10 + 4',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 10, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [('Charge', 'If the rothé moves at least 20 feet straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 7 (2d6) piercing damage.')],
        "actions": [('Gore', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 7 (1d6 + 4) piercing damage.')],
    },
    'Saber-Toothed Tiger': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 12, "ac_note": '', "hp": 52, "hit_dice": '7d10 + 14',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 14, 'CON': 15, 'INT': 3, 'WIS': 12, 'CHA': 8},
        "skills": [('Perception', '+3'), ('Stealth', '+6')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Smell', 'The tiger has advantage on Wisdom (Perception) checks that rely on smell.'), ('Pounce', 'If the tiger moves at least 20 feet straight toward a creature and then hits it with a claw attack on the same turn, that target must succeed on a DC 14 Strength saving throw or be knocked prone. If the target is prone, the tiger can make one bite attack against it as a bonus action.')],
        "actions": [('Bite', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 10 (1d10 + 5) piercing damage.'), ('Claw', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 12 (2d6 + 5) slashing damage.')],
    },
    'Scorpion': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 11, "ac_note": 'natural armor', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '10 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 11, 'CON': 8, 'INT': 1, 'WIS': 8, 'CHA': 2},
        "skills": [],
        "senses": 'blindsight 10 ft., passive Perception 9',
        "traits": [],
        "actions": [('Sting', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one creature. Hit: 1 piercing damage, and the target must make a DC 9 Constitution saving throw, taking 4 (1d8) poison damage on a failed save, or half as much damage on a successful one.')],
    },
    'Sea Horse': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 11, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '0 ft., swim 20 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 1, 'DEX': 12, 'CON': 8, 'INT': 1, 'WIS': 10, 'CHA': 2},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Water Breathing', 'The sea horse can breathe only underwater.')],
        "actions": [],
    },
    'Seal': {
        "cr": 0.0, "cr_label": '0', "size": 'Medium',
        "ac": 11, "ac_note": '', "hp": 9, "hit_dice": '2d8',
        "speed": '20 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 10, 'DEX': 12, 'CON': 11, 'INT': 3, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 11',
        "traits": [('Hold Breath', 'The seal can hold its breath for 15 minutes.'), ('Keen Smell', 'The seal has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 1 piercing damage.')],
    },
    'Sheep': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 10, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 12, 'DEX': 10, 'CON': 11, 'INT': 2, 'WIS': 10, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Sure-Footed', 'The sheep has advantage on Strength and Dexterity saving throws made against effects that would knock it prone.')],
        "actions": [],
    },
    'Sled Dog': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 13, "ac_note": 'natural armor', "hp": 11, "hit_dice": '2d8 + 2',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 12, 'DEX': 15, 'CON': 12, 'INT': 3, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3'), ('Stealth', '+4')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Hearing and Smell', 'The dog has advantage on Wisdom (Perception) checks that rely on hearing or smell.'), ('Pack Tactics', "The dog has advantage on an attack roll against a creature if at least one of the dog's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (2d4 + 2) piercing damage. If the target is a creature, it must succeed on a DC 11 Strength saving throw or be knocked prone.')],
    },
    'Snow Leopard': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 12, "ac_note": '', "hp": 37, "hit_dice": '5d10 + 10',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 17, 'DEX': 15, 'CON': 14, 'INT': 3, 'WIS': 12, 'CHA': 8},
        "skills": [('Perception', '+3'), ('Stealth', '+6')],
        "senses": 'darkvision 60 ft., passive Perception 13',
        "traits": [('Keen Smell', 'The leopard has advantage on Wisdom (Perception) checks that rely on smell.'), ('Pounce', 'If the leopard moves at least 20 feet straight toward a creature and then hits it with a claw attack on the same turn, that target must succeed on a DC 13 Strength saving throw or be knocked prone. If the target is prone, the leopard can make one bite attack against it as a bonus action.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 8 (1d10 + 3) piercing damage.'), ('Claw', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 7 (1d8 + 3) slashing damage.')],
    },
    'Space Eel': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Small',
        "ac": 14, "ac_note": '', "hp": 7, "hit_dice": '2d6',
        "speed": '10 ft., fly 30 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 12, 'DEX': 18, 'CON': 11, 'INT': 1, 'WIS': 10, 'CHA': 1},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Unusual Nature', "The eel doesn't require air.")],
        "actions": [('Multiattack', "If it isn't attached to a creature, the eel makes one Bite attack and one Tail Spine attack."), ('Bite', "Melee Weapon Attack: +3 to hit, reach 5 ft., one creature. Hit: 4 (1d6 + 1) piercing damage, and the eel attaches to the target. While attached, the eel can't make Bite attacks. Instead, the target takes 4 (1d6 + 1) piercing damage at the start of each of the eel's turns. The eel can detach itself as a bonus action. A creature, including the target, can use its action to detach the eel."), ('Tail Spine', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one creature. Hit: 3 (1d4 + 1) piercing damage, and the target must succeed on a DC 10 Constitution saving throw or be poisoned for 1 minute. Until this poison ends, the target is paralyzed. The target can repeat the saving throw at the end of each of its turns, ending the effect on itself on a success.')],
    },
    'Space Guppy': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 13, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '0 ft., fly 30 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 3, 'DEX': 16, 'CON': 10, 'INT': 1, 'WIS': 10, 'CHA': 1},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Air Envelope', 'If it has at least 1 hit point, the guppy can generate an air envelope around itself when in a vacuum. This air envelope can sustain the guppy and one other Tiny creature in its space indefinitely.'), ('Flyby', "The guppy doesn't provoke opportunity attacks when it flies out of an enemy's reach.")],
        "actions": [('Tail Slap', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1 bludgeoning damage.')],
    },
    'Space Hamster': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 10, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '20 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 11, 'CON': 9, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [('Keen Smell', 'the hamster has advantage on Wisdom (Perception) checks that rely on smell.')],
        "actions": [],
    },
    'Space Mollymawk': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '10 ft., fly 50 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 6, 'DEX': 14, 'CON': 11, 'INT': 3, 'WIS': 12, 'CHA': 3},
        "skills": [('Perception', '+5')],
        "senses": 'passive Perception 15',
        "traits": [('Flyby', "The mollymawk doesn't provoke opportunity attacks when it flies out of an enemy's reach."), ('Hold Breath', 'The mollymawk can hold its breath for 15 minutes.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) piercing damage.')],
    },
    'Space Swine': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Medium',
        "ac": 11, "ac_note": '', "hp": 22, "hit_dice": '4d8 + 4',
        "speed": '40 ft., fly 40 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 12, 'DEX': 12, 'CON': 12, 'INT': 4, 'WIS': 10, 'CHA': 3},
        "skills": [('Perception', '+4'), ('Survival', '+4')],
        "senses": 'passive Perception 14',
        "traits": [],
        "actions": [('Bite', 'Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 4 (1d6 + 1) piercing damage.')],
    },
    'Spider': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 12, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '20 ft., climb 20 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 2, 'DEX': 14, 'CON': 8, 'INT': 1, 'WIS': 10, 'CHA': 2},
        "skills": [('Stealth', '+4')],
        "senses": 'darkvision 30 ft., passive Perception 10',
        "traits": [('Spider Climb', 'The spider can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.'), ('Web Sense', 'While in contact with a web, the spider knows the exact location of any other creature in contact with the same web.'), ('Web Walker', 'The spider ignores movement restrictions caused by webbing.')],
        "actions": [('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 1 piercing damage, and the target must succeed on a DC 9 Constitution saving throw or take 2 (1d4) poison damage.')],
    },
    'Spotted Lion': {
        "cr": 3.0, "cr_label": '3', "size": 'Huge',
        "ac": 15, "ac_note": 'natural armor', "hp": 66, "hit_dice": '7d12 + 21',
        "speed": '60 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 23, 'DEX': 14, 'CON': 17, 'INT': 5, 'WIS': 13, 'CHA': 10},
        "skills": [('Perception', '+5'), ('Stealth', '+6')],
        "senses": 'darkvision 60 ft., passive Perception 15',
        "traits": [('Pack Tactics', "The lion has advantage on an attack roll against a creature if at least one of the lion's allies is within 5 feet of the target and the ally doesn't have the incapacitated condition.")],
        "actions": [('Rend', 'Melee Weapon Attack: +8 to hit, reach 10 ft., one target. Hit: 15 (2d8 + 6) piercing damage. If the lion moved at least 20 feet straight toward the target immediately before the hit, the target must succeed on a DC 16 Strength saving throw or have the prone condition. If the target has the prone condition, the lion can make another Rend attack against it as a bonus action.')],
    },
    'Stench Kow': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 15, "hit_dice": '2d10 + 4',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 10, 'CON': 14, 'INT': 2, 'WIS': 10, 'CHA': 4},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 10',
        "traits": [('Charge', 'If the kow moves at least 20 feet straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 7 (2d6) piercing damage.'), ('Stench', "Any creature other than a stench kow that starts its turn within 5 feet of the stench kow must succeed on a DC 12 Constitution saving throw or be poisoned until the start of the creature's next turn. On a successful saving throw, the creature is immune to the stench of all stench kows for 1 hour.")],
        "actions": [('Gore', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 7 (1d6 + 4) piercing damage.')],
    },
    'Stirge': {
        "cr": 0.125, "cr_label": '1/8', "size": 'Tiny',
        "ac": 14, "ac_note": 'natural armor', "hp": 2, "hit_dice": '1d4',
        "speed": '10 ft., fly 40 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 4, 'DEX': 16, 'CON': 11, 'INT': 2, 'WIS': 8, 'CHA': 6},
        "skills": [],
        "senses": 'darkvision 60 ft., passive Perception 9',
        "traits": [],
        "actions": [('Blood Drain', "Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 5 (1d4 + 3) piercing damage, and the stirge attaches to the target. While attached, the stirge doesn't attack. Instead, at the start of each of the stirge's turns, the target loses 5 (1d4 + 3) hit points due to blood loss. >The stirge can detach itself by spending 5 feet of its movement. It does so after it drains 10 hit points of blood from the target or the target dies. A creature, including the target, can use its action to detach the stirge.")],
    },
    'Titanothere': {
        "cr": 5.0, "cr_label": '5', "size": 'Huge',
        "ac": 16, "ac_note": 'natural armor', "hp": 136, "hit_dice": '13d12 + 52',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 25, 'DEX': 10, 'CON': 19, 'INT': 2, 'WIS': 12, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Beast of Burden', 'The titanothere is considered to be one size larger for the purpose of determining its carrying capacity.')],
        "actions": [('Stomp', 'Melee Weapon Attack: +10 to hit, reach 10 ft., one target. Hit: 20 (3d8 + 7) bludgeoning damage. If the titanothere moved at least 20 feet straight toward the target immediately before the hit, the target takes an extra 13 (3d8) bludgeoning damage, and the target must succeed on a DC 18 Strength saving throw or have the prone condition if it is a creature.')],
    },
    'Velociraptor': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Tiny',
        "ac": 13, "ac_note": 'natural armor', "hp": 10, "hit_dice": '3d4 + 3',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 6, 'DEX': 14, 'CON': 13, 'INT': 4, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Pack Tactics', "The velociraptor has advantage on an attack roll against a creature if at least one of the velociraptor's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Multiattack', 'The velociraptor makes two attacks: one with its bite and one with its claws.'), ('Bite', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 5 (1d6 + 2) piercing damage.'), ('Claws', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) slashing damage.')],
    },
    'Vulture': {
        "cr": 0.0, "cr_label": '0', "size": 'Medium',
        "ac": 10, "ac_note": '', "hp": 5, "hit_dice": '1d8 + 1',
        "speed": '10 ft., fly 50 ft.', "flies": True, "swims": False,
        "abilities": {'STR': 7, 'DEX': 10, 'CON': 13, 'INT': 2, 'WIS': 12, 'CHA': 4},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Sight and Smell', 'The vulture has advantage on Wisdom (Perception) checks that rely on sight or smell.'), ('Pack Tactics', "The vulture has advantage on an attack roll against a creature if at least one of the vulture's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Beak', 'Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 2 (1d4) piercing damage.')],
    },
    'Walrus': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 9, "ac_note": '', "hp": 22, "hit_dice": '3d10 + 6',
        "speed": '20 ft., swim 40 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 15, 'DEX': 9, 'CON': 14, 'INT': 3, 'WIS': 11, 'CHA': 4},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Hold Breath', 'The walrus can hold its breath for 10 minutes.')],
        "actions": [('Tusks', 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 7 (2d4 + 2) piercing damage.')],
    },
    'Warhorse': {
        "cr": 0.5, "cr_label": '1/2', "size": 'Large',
        "ac": 11, "ac_note": '', "hp": 19, "hit_dice": '3d10 + 3',
        "speed": '60 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 18, 'DEX': 12, 'CON': 13, 'INT': 2, 'WIS': 12, 'CHA': 7},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Trampling Charge', 'If the horse moves at least 20 feet straight toward a creature and then hits it with a hooves attack on the same turn, that target must succeed on a DC 14 Strength saving throw or be knocked prone. If the target is prone, the horse can make another attack with its hooves against it as a bonus action.')],
        "actions": [('Hooves', 'Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 11 (2d6 + 4) bludgeoning damage.')],
    },
    'Weasel': {
        "cr": 0.0, "cr_label": '0', "size": 'Tiny',
        "ac": 13, "ac_note": '', "hp": 1, "hit_dice": '1d4 - 1',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 3, 'DEX': 16, 'CON': 8, 'INT': 2, 'WIS': 12, 'CHA': 3},
        "skills": [('Perception', '+3'), ('Stealth', '+5')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Hearing and Smell', 'The weasel has advantage on Wisdom (Perception) checks that rely on hearing or smell.')],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 1 piercing damage.')],
    },
    'Whirlwyrm': {
        "cr": 5.0, "cr_label": '5', "size": 'Huge',
        "ac": 14, "ac_note": 'natural armor', "hp": 85, "hit_dice": '9d12 + 27',
        "speed": '30 ft., swim 50 ft.', "flies": False, "swims": True,
        "abilities": {'STR': 21, 'DEX': 9, 'CON': 17, 'INT': 2, 'WIS': 10, 'CHA': 7},
        "skills": [('Stealth', '+5')],
        "senses": 'passive Perception 10',
        "traits": [('Hold Breath', 'The whirlwyrm can hold its breath for 30 minutes.')],
        "actions": [('Multiattack', 'The whirlwyrm makes two attacks: one with its bite and one with its tail.'), ('Bite', "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 21 (3d10 + 5) piercing damage, and the target is grappled (escape DC 16). Until this grapple ends, the target is restrained, and the whirlwyrm can't bite another target."), ('Tail', 'Melee Weapon Attack: +8 to hit, reach 10 ft., one target not grappled by the whirlwyrm. Hit: 14 (2d8 + 5) bludgeoning damage. If the target is a creature, it must succeed on a DC 16 Strength saving throw or be knocked prone.')],
    },
    'Wild Dog': {
        "cr": 0.0, "cr_label": '0', "size": 'Small',
        "ac": 12, "ac_note": '', "hp": 3, "hit_dice": '1d6',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 8, 'DEX': 15, 'CON': 11, 'INT': 3, 'WIS': 12, 'CHA': 6},
        "skills": [('Perception', '+3')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Hearing and Smell', 'The dog has advantage on Wisdom (Perception) checks that rely on hearing or smell.'), ('Pack Tactics', "The dog has advantage on an attack roll against a creature if at least one of the dog's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +1 to hit, reach 5 ft., one target. Hit: 1 (1d4 - 1) piercing damage.')],
    },
    'Yak': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d10 + 2',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 10, 'CON': 12, 'INT': 2, 'WIS': 10, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [('Charge', 'If the yak moves at least 20 feet straight toward a target and then hits it with a ram attack on the same turn, the target takes an extra 7 (2d6) damage. If the target is a creature, it must succeed on a DC 13 Strength saving throw or be knocked prone.')],
        "actions": [('Ram', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 6 (1d6 + 3) bludgeoning damage.'), ('Hooves', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one prone creature. Hit: 8 (2d4 + 3) bludgeoning damage.')],
    },
    'Young Bulette': {
        "cr": 2.0, "cr_label": '2', "size": 'Large',
        "ac": 11, "ac_note": 'natural armor', "hp": 45, "hit_dice": '6d10 + 12',
        "speed": '40 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 21, 'DEX': 8, 'CON': 15, 'INT': 2, 'WIS': 12, 'CHA': 6},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Charge', 'If the bulette moves at least 20 feet straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 9 (2d8) bludgeoning damage. If the target is a creature, it must succeed on a DC 15 Strength saving throw or be knocked prone.')],
        "actions": [('Bite', 'Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 14 (2d8 + 5) piercing damage.')],
    },
    'Young Horizonback Tortoise': {
        "cr": 3.0, "cr_label": '3', "size": 'Huge',
        "ac": 15, "ac_note": 'natural armor', "hp": 68, "hit_dice": '8d12 + 16',
        "speed": '30 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 19, 'DEX': 11, 'CON': 15, 'INT': 2, 'WIS': 12, 'CHA': 5},
        "skills": [],
        "senses": 'passive Perception 11',
        "traits": [('Amphibious', 'The young horizonback tortoise can breathe air and water.')],
        "actions": [('Bite', 'Melee Weapon Attack: +7 to hit, reach 10 ft., one target. Hit: 18 (4d6 + 4) piercing damage. If the target is a creature, it must succeed on a DC 14 Strength saving throw or be knocked prone.')],
    },
    'Young Winter Wolf': {
        "cr": 1.0, "cr_label": '1', "size": 'Large',
        "ac": 14, "ac_note": 'natural armor', "hp": 37, "hit_dice": '5d10 + 10',
        "speed": '50 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 17, 'DEX': 15, 'CON': 15, 'INT': 3, 'WIS': 12, 'CHA': 7},
        "skills": [('Perception', '+3'), ('Stealth', '+4')],
        "senses": 'passive Perception 13',
        "traits": [('Keen Hearing and Smell', 'The wolf has advantage on Wisdom (Perception) checks that rely on hearing or smell.'), ('Pack Tactics', "The wolf has advantage on an attack roll against a creature if at least one of the wolf's allies is within 5 feet of the creature and the ally isn't incapacitated.")],
        "actions": [('Bite', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 10 (2d6 + 3) piercing damage. If the target is a creature, it must succeed on a DC 13 Strength saving throw or be knocked prone.')],
    },
    'Zebra': {
        "cr": 0.25, "cr_label": '1/4', "size": 'Large',
        "ac": 10, "ac_note": '', "hp": 13, "hit_dice": '2d10 + 2',
        "speed": '60 ft.', "flies": False, "swims": False,
        "abilities": {'STR': 16, 'DEX': 10, 'CON': 12, 'INT': 2, 'WIS': 11, 'CHA': 7},
        "skills": [],
        "senses": 'passive Perception 10',
        "traits": [],
        "actions": [('Hooves', 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 8 (2d4 + 3) bludgeoning damage.')],
    },
    "Wolf": {
        "cr": 0.25, "cr_label": "1/4", "size": "Medium",
        "ac": 13, "ac_note": "natural armor", "hp": 11, "hit_dice": "2d8+2",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 12, "DEX": 15, "CON": 12, "INT": 3, "WIS": 12, "CHA": 6},
        "skills": [("Perception", "+3"), ("Stealth", "+4")],
        "senses": "passive Perception 13",
        "traits": [
            ("Keen Hearing and Smell", "Advantage on WIS (Perception) checks that rely on hearing or smell."),
            ("Pack Tactics", "Advantage on an attack roll against a creature if at least one of the wolf's allies is within 5 ft of the creature and not incapacitated."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 2d4+2 piercing damage. If the target is a creature, it must succeed on a DC 11 STR save or be knocked prone."),
        ],
    },
    "Giant Spider": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 14, "ac_note": "natural armor", "hp": 26, "hit_dice": "4d10+4",
        "speed": "30 ft., climb 30 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 14, "DEX": 16, "CON": 12, "INT": 2, "WIS": 11, "CHA": 4},
        "skills": [("Stealth", "+7")],
        "senses": "blindsight 10 ft., darkvision 60 ft., passive Perception 10",
        "traits": [
            ("Spider Climb", "The spider can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check."),
            ("Web Sense", "While in contact with a web, the spider knows the exact location of any other creature in contact with the same web."),
            ("Web Walker", "The spider ignores movement restrictions caused by webbing."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +5 to hit, reach 5 ft., one creature. Hit: 1d8+3 piercing damage, and the target must make a DC 11 CON save, taking 2d8 poison damage on a fail (half on success). If the poison damage reduces the target to 0 HP, it's stable but poisoned for 1 hour and paralyzed while poisoned this way."),
            ("Web (Recharge 5\u20136)", "Ranged Weapon Attack: +5 to hit, range 30/60 ft., one creature. Hit: the target is restrained by webbing; DC 11 STR check to break free (destroying the web instead takes 5 slashing/bludgeoning/fire damage, AC 10)."),
        ],
    },
    "Brown Bear": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 11, "ac_note": "natural armor", "hp": 34, "hit_dice": "4d10+12",
        "speed": "40 ft., climb 30 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 19, "DEX": 10, "CON": 16, "INT": 2, "WIS": 13, "CHA": 7},
        "skills": [("Perception", "+3")],
        "senses": "passive Perception 13",
        "traits": [("Keen Smell", "Advantage on WIS (Perception) checks that rely on smell.")],
        "actions": [
            ("Multiattack", "The bear makes two attacks: one bite and one claw."),
            ("Bite", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 1d8+4 piercing damage."),
            ("Claws", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 2d6+4 slashing damage."),
        ],
    },
    "Dire Wolf": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 14, "ac_note": "natural armor", "hp": 37, "hit_dice": "5d10+10",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 17, "DEX": 15, "CON": 15, "INT": 3, "WIS": 12, "CHA": 7},
        "skills": [("Perception", "+3"), ("Stealth", "+4")],
        "senses": "passive Perception 13",
        "traits": [
            ("Keen Hearing and Smell", "Advantage on WIS (Perception) checks that rely on hearing or smell."),
            ("Pack Tactics", "Advantage on an attack roll against a creature if at least one of the wolf's allies is within 5 ft of the creature and not incapacitated."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 2d6+3 piercing damage. If the target is a creature, it must succeed on a DC 13 STR save or be knocked prone."),
        ],
    },
    "Giant Eagle": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 13, "ac_note": "natural armor", "hp": 26, "hit_dice": "4d10+4",
        "speed": "10 ft., fly 80 ft.", "flies": True, "swims": False,
        "abilities": {"STR": 16, "DEX": 17, "CON": 13, "INT": 8, "WIS": 14, "CHA": 10},
        "skills": [("Perception", "+4")],
        "senses": "passive Perception 14",
        "traits": [("Keen Sight", "Advantage on WIS (Perception) checks that rely on sight.")],
        "actions": [
            ("Multiattack", "The eagle makes two attacks: one with its beak and one with its talons."),
            ("Beak", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d6+3 piercing damage."),
            ("Talons", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 2d6+3 slashing damage."),
        ],
    },
    "Crocodile": {
        "cr": 0.5, "cr_label": "1/2", "size": "Large",
        "ac": 12, "ac_note": "natural armor", "hp": 19, "hit_dice": "3d10+3",
        "speed": "20 ft., swim 30 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 15, "DEX": 10, "CON": 13, "INT": 2, "WIS": 10, "CHA": 5},
        "skills": [("Stealth", "+2")],
        "senses": "passive Perception 10",
        "traits": [("Hold Breath", "The crocodile can hold its breath for 15 minutes.")],
        "actions": [
            ("Bite", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d10+2 piercing damage, and the target is grappled (escape DC 12). Until the grapple ends, the crocodile can't bite another target."),
        ],
    },
    "Ape": {
        "cr": 0.5, "cr_label": "1/2", "size": "Medium",
        "ac": 12, "ac_note": "natural armor", "hp": 19, "hit_dice": "3d8+6",
        "speed": "30 ft., climb 30 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 16, "DEX": 14, "CON": 14, "INT": 6, "WIS": 12, "CHA": 7},
        "skills": [("Athletics", "+5"), ("Perception", "+3")],
        "senses": "passive Perception 13",
        "traits": [],
        "actions": [
            ("Multiattack", "The ape makes two fist attacks."),
            ("Fist", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d6+3 bludgeoning damage."),
            ("Rock", "Ranged Weapon Attack: +5 to hit, range 25/50 ft., one target. Hit: 1d6+3 bludgeoning damage."),
        ],
    },
    "Giant Boar": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 12, "ac_note": "natural armor", "hp": 42, "hit_dice": "5d10+15",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 17, "DEX": 10, "CON": 16, "INT": 2, "WIS": 7, "CHA": 5},
        "skills": [],
        "senses": "passive Perception 8",
        "traits": [
            ("Charge", "If the boar moves at least 20 ft. straight toward a target and then hits it with a tusk attack on the same turn, the target takes an extra 7 (2d6) slashing damage. If the target is a creature, it must succeed on a DC 13 STR save or be knocked prone."),
            ("Relentless (Recharges after a Short or Long Rest)", "If the boar takes 10 damage or less that would reduce it to 0 HP, it is reduced to 1 HP instead."),
        ],
        "actions": [
            ("Tusk", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 10 (2d6+3) slashing damage."),
        ],
    },
    "Polar Bear": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 12, "ac_note": "natural armor", "hp": 42, "hit_dice": "5d10+15",
        "speed": "40 ft., swim 30 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 20, "DEX": 10, "CON": 16, "INT": 2, "WIS": 13, "CHA": 7},
        "skills": [("Perception", "+3")],
        "senses": "passive Perception 13",
        "traits": [("Keen Smell", "Advantage on WIS (Perception) checks that rely on smell.")],
        "actions": [
            ("Multiattack", "The bear makes two attacks: one bite and one claw."),
            ("Bite", "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 1d8+5 piercing damage."),
            ("Claws", "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 2d6+5 slashing damage."),
        ],
    },
    "Giant Constrictor Snake": {
        "cr": 2, "cr_label": "2", "size": "Huge",
        "ac": 12, "ac_note": "", "hp": 60, "hit_dice": "8d12+8",
        "speed": "30 ft., swim 30 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 19, "DEX": 14, "CON": 12, "INT": 1, "WIS": 10, "CHA": 3},
        "skills": [("Perception", "+2")],
        "senses": "blindsight 10 ft., passive Perception 12",
        "traits": [],
        "actions": [
            ("Bite", "Melee Weapon Attack: +6 to hit, reach 10 ft., one target. Hit: 2d6+4 piercing damage."),
            ("Constrict", "Melee Weapon Attack: +6 to hit, reach 5 ft., one creature. Hit: 2d8+4 bludgeoning damage, and the target is grappled (escape DC 16), restrained until the grapple ends."),
        ],
    },
    "Rhinoceros": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 11, "ac_note": "natural armor", "hp": 45, "hit_dice": "6d10+12",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 21, "DEX": 8, "CON": 15, "INT": 2, "WIS": 12, "CHA": 6},
        "skills": [],
        "senses": "passive Perception 11",
        "traits": [
            ("Charge", "If the rhinoceros moves at least 20 ft. straight toward a target and then hits it with a gore attack on the same turn, the target takes an extra 9 (2d8) bludgeoning damage. If the target is a creature, it must succeed on a DC 15 STR save or be knocked prone."),
        ],
        "actions": [
            ("Gore", "Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 14 (2d8+5) bludgeoning damage."),
        ],
    },
    "Elephant": {
        "cr": 4, "cr_label": "4", "size": "Huge",
        "ac": 12, "ac_note": "natural armor", "hp": 76, "hit_dice": "8d12+24",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 22, "DEX": 9, "CON": 17, "INT": 3, "WIS": 11, "CHA": 6},
        "skills": [],
        "senses": "passive Perception 10",
        "traits": [("Trampling Charge", "If the elephant moves at least 20 ft straight toward a creature and hits with a gore, that target must succeed a DC 12 STR save or be knocked prone; if prone, the elephant can make one stomp attack against it as a bonus action.")],
        "actions": [
            ("Gore", "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 3d8+6 piercing damage."),
            ("Stomp", "Melee Weapon Attack: +8 to hit, reach 5 ft., one prone creature. Hit: 3d10+6 bludgeoning damage."),
        ],
    },
    "Giant Shark": {
        "cr": 5, "cr_label": "5", "size": "Huge",
        "ac": 13, "ac_note": "natural armor", "hp": 126, "hit_dice": "11d12+55",
        "speed": "0 ft., swim 50 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 23, "DEX": 11, "CON": 21, "INT": 1, "WIS": 10, "CHA": 5},
        "skills": [("Perception", "+4")],
        "senses": "blindsight 60 ft., passive Perception 14",
        "traits": [
            ("Blood Frenzy", "The shark has advantage on melee attack rolls against any creature that doesn't have all its HP."),
            ("Water Breathing", "The shark can breathe only underwater."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +9 to hit, reach 5 ft., one target. Hit: 3d10+6 piercing damage."),
        ],
    },
    "Mammoth": {
        "cr": 6, "cr_label": "6", "size": "Huge",
        "ac": 13, "ac_note": "natural armor", "hp": 126, "hit_dice": "11d12+55",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 24, "DEX": 9, "CON": 21, "INT": 3, "WIS": 11, "CHA": 6},
        "skills": [],
        "senses": "passive Perception 10",
        "traits": [("Trampling Charge", "If the mammoth moves at least 20 ft straight toward a creature and hits with a gore, that target must succeed a DC 14 STR save or be knocked prone; if prone, the mammoth can make one stomp attack against it as a bonus action.")],
        "actions": [
            ("Gore", "Melee Weapon Attack: +10 to hit, reach 5 ft., one target. Hit: 4d8+7 piercing damage."),
            ("Stomp", "Melee Weapon Attack: +10 to hit, reach 5 ft., one prone creature. Hit: 4d10+7 bludgeoning damage."),
        ],
    },
    # ── Added from a user-supplied, source-verified stat list (not built
    # from memory like the entries above) — see conversation history.
    "Panther": {
        "cr": 0.25, "cr_label": "1/4", "size": "Medium",
        "ac": 12, "ac_note": "", "hp": 13, "hit_dice": "3d8",
        "speed": "50 ft., climb 40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 14, "DEX": 15, "CON": 10, "INT": 3, "WIS": 14, "CHA": 7},
        "skills": [("Perception", "+4"), ("Stealth", "+6")],
        "senses": "passive Perception 14",
        "traits": [
            ("Keen Smell", "Advantage on WIS (Perception) checks that rely on smell."),
            ("Pounce", "If the panther moves at least 20 ft straight toward a creature and hits with a claw, that target must succeed a DC 12 STR save or be knocked prone; if prone, the panther can make one bite attack against it as a bonus action."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d6+2 piercing damage."),
            ("Claw", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d4+2 slashing damage."),
        ],
    },
    "Giant Owl": {
        "cr": 0.25, "cr_label": "1/4", "size": "Large",
        "ac": 12, "ac_note": "", "hp": 19, "hit_dice": "3d10+3",
        "speed": "5 ft., fly 60 ft.", "flies": True, "swims": False,
        "abilities": {"STR": 13, "DEX": 15, "CON": 12, "INT": 8, "WIS": 13, "CHA": 10},
        "skills": [("Perception", "+5"), ("Stealth", "+4")],
        "senses": "darkvision 120 ft., passive Perception 15",
        "traits": [
            ("Flyby", "The owl doesn't provoke opportunity attacks when it flies out of a creature's reach."),
            ("Keen Hearing and Sight", "Advantage on WIS (Perception) checks that rely on hearing or sight."),
        ],
        "actions": [
            ("Talons", "Melee Weapon Attack: +3 to hit, reach 5 ft., one target. Hit: 2d6+1 slashing damage."),
        ],
    },
    "Axe Beak": {
        "cr": 0.25, "cr_label": "1/4", "size": "Large",
        "ac": 11, "ac_note": "", "hp": 19, "hit_dice": "3d10+3",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 14, "DEX": 12, "CON": 12, "INT": 2, "WIS": 10, "CHA": 5},
        "skills": [],
        "senses": "passive Perception 10",
        "traits": [],
        "actions": [
            ("Beak", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d8+2 slashing damage."),
        ],
    },
    "Black Bear": {
        "cr": 0.5, "cr_label": "1/2", "size": "Medium",
        "ac": 11, "ac_note": "", "hp": 19, "hit_dice": "3d8+6",
        "speed": "40 ft., climb 30 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 15, "DEX": 10, "CON": 14, "INT": 2, "WIS": 12, "CHA": 7},
        "skills": [("Perception", "+3")],
        "senses": "passive Perception 13",
        "traits": [("Keen Smell", "Advantage on WIS (Perception) checks that rely on smell.")],
        "actions": [
            ("Multiattack", "The bear makes two attacks: one bite and one claw."),
            ("Bite", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d6+2 piercing damage."),
            ("Claws", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 2d4+2 slashing damage."),
        ],
    },
    "Lion": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 12, "ac_note": "", "hp": 26, "hit_dice": "4d10+4",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 17, "DEX": 15, "CON": 13, "INT": 3, "WIS": 12, "CHA": 8},
        "skills": [("Perception", "+3"), ("Stealth", "+6")],
        "senses": "passive Perception 13",
        "traits": [
            ("Keen Smell", "Advantage on WIS (Perception) checks that rely on smell."),
            ("Pack Tactics", "Advantage on an attack roll against a creature if at least one of the lion's allies is within 5 ft of the creature and not incapacitated."),
            ("Pounce", "If the lion moves at least 20 ft straight toward a creature and hits with a claw, that target must succeed a DC 13 STR save or be knocked prone; if prone, the lion can make one bite attack against it as a bonus action."),
            ("Running Leap", "With a 10 ft running start, the lion can long jump up to 25 ft."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d8+3 piercing damage."),
            ("Claw", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d6+3 slashing damage."),
        ],
    },
    "Tiger": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 12, "ac_note": "", "hp": 37, "hit_dice": "5d10+10",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 17, "DEX": 15, "CON": 14, "INT": 3, "WIS": 12, "CHA": 8},
        "skills": [("Perception", "+3"), ("Stealth", "+6")],
        "senses": "darkvision 60 ft., passive Perception 13",
        "traits": [
            ("Keen Smell", "Advantage on WIS (Perception) checks that rely on smell."),
            ("Pounce", "If the tiger moves at least 20 ft straight toward a creature and hits with a claw, that target must succeed a DC 13 STR save or be knocked prone; if prone, the tiger can make one bite attack against it as a bonus action."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d10+3 piercing damage."),
            ("Claw", "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d8+3 slashing damage."),
        ],
    },
    "Giant Toad": {
        "cr": 1, "cr_label": "1", "size": "Large",
        "ac": 11, "ac_note": "", "hp": 39, "hit_dice": "6d10+6",
        "speed": "20 ft., swim 40 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 15, "DEX": 13, "CON": 13, "INT": 2, "WIS": 10, "CHA": 3},
        "skills": [],
        "senses": "darkvision 30 ft., passive Perception 10",
        "traits": [
            ("Amphibious", "The toad can breathe air and water."),
            ("Standing Leap", "The toad's long jump is up to 20 ft and its high jump is up to 10 ft, with or without a running start."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d10+2 piercing damage plus 1d10 poison damage, and the target is grappled (escape DC 13) and restrained until the grapple ends; the toad can't bite another target while grappling one."),
            ("Swallow", "The toad makes a bite attack against a Medium or smaller target it's grappling. On a hit, the target is swallowed instead — blinded, restrained, has total cover against outside attacks, and takes 3d6 acid damage at the start of each of the toad's turns. Only one creature can be swallowed at a time; if the toad dies, a swallowed creature can escape (exiting prone) using 5 ft of movement."),
        ],
    },
    "Allosaurus": {
        "cr": 2, "cr_label": "2", "size": "Large",
        "ac": 13, "ac_note": "natural armor", "hp": 51, "hit_dice": "6d10+18",
        "speed": "60 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 19, "DEX": 13, "CON": 17, "INT": 2, "WIS": 12, "CHA": 5},
        "skills": [("Perception", "+5")],
        "senses": "passive Perception 15",
        "traits": [("Pounce", "If the allosaurus moves at least 30 ft straight toward a creature and hits with a claw, that target must succeed a DC 13 STR save or be knocked prone; if prone, the allosaurus can make one bite attack against it as a bonus action.")],
        "actions": [
            ("Bite", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 2d10+4 piercing damage."),
            ("Claw", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 1d8+4 slashing damage."),
        ],
    },
    "Killer Whale": {
        "cr": 3, "cr_label": "3", "size": "Huge",
        "ac": 12, "ac_note": "natural armor", "hp": 90, "hit_dice": "12d12+12",
        "speed": "0 ft., swim 60 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 19, "DEX": 10, "CON": 13, "INT": 3, "WIS": 12, "CHA": 7},
        "skills": [("Perception", "+3")],
        "senses": "blindsight 120 ft., passive Perception 13",
        "traits": [
            ("Echolocation", "The whale can't use its blindsight while deafened."),
            ("Hold Breath", "The whale can hold its breath for 30 minutes."),
            ("Keen Hearing", "Advantage on WIS (Perception) checks that rely on hearing."),
        ],
        "actions": [
            ("Bite", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 5d6+4 piercing damage."),
        ],
    },
    "Ankylosaurus": {
        "cr": 3, "cr_label": "3", "size": "Huge",
        "ac": 15, "ac_note": "natural armor", "hp": 68, "hit_dice": "8d12+16",
        "speed": "30 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 19, "DEX": 11, "CON": 15, "INT": 2, "WIS": 12, "CHA": 5},
        "skills": [],
        "senses": "passive Perception 11",
        "traits": [],
        "actions": [
            ("Tail", "Melee Weapon Attack: +7 to hit, reach 10 ft., one target. Hit: 4d6+4 bludgeoning damage; if the target is a creature, it must succeed a DC 14 STR save or be knocked prone."),
        ],
    },
    "Giant Scorpion": {
        "cr": 3, "cr_label": "3", "size": "Large",
        "ac": 15, "ac_note": "natural armor", "hp": 52, "hit_dice": "7d10+14",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 15, "DEX": 13, "CON": 15, "INT": 1, "WIS": 9, "CHA": 3},
        "skills": [],
        "senses": "blindsight 60 ft., passive Perception 9",
        "traits": [],
        "actions": [
            ("Multiattack", "The scorpion makes three attacks: two with its claws and one with its sting."),
            ("Claw", "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 1d8+2 bludgeoning damage, and the target is grappled (escape DC 12). The scorpion has two claws, each able to grapple only one target."),
            ("Sting", "Melee Weapon Attack: +4 to hit, reach 5 ft., one creature. Hit: 1d10+2 piercing damage, and the target must make a DC 12 CON save, taking 4d10 poison damage on a fail (half on success)."),
        ],
    },
    "Stegosaurus": {
        "cr": 4, "cr_label": "4", "size": "Huge",
        "ac": 13, "ac_note": "natural armor", "hp": 76, "hit_dice": "8d12+24",
        "speed": "40 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 20, "DEX": 9, "CON": 17, "INT": 2, "WIS": 11, "CHA": 5},
        "skills": [],
        "senses": "passive Perception 10",
        "traits": [],
        "actions": [
            ("Tail", "Melee Weapon Attack: +7 to hit, reach 10 ft., one target. Hit: 6d6+5 piercing damage."),
        ],
    },
    "Triceratops": {
        "cr": 5, "cr_label": "5", "size": "Huge",
        "ac": 13, "ac_note": "natural armor", "hp": 95, "hit_dice": "10d12+30",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 22, "DEX": 9, "CON": 17, "INT": 2, "WIS": 11, "CHA": 5},
        "skills": [],
        "senses": "passive Perception 10",
        "traits": [("Trampling Charge", "If the triceratops moves at least 20 ft straight toward a creature and hits with a gore, that target must succeed a DC 13 STR save or be knocked prone; if prone, the triceratops can make one stomp attack against it as a bonus action.")],
        "actions": [
            ("Gore", "Melee Weapon Attack: +9 to hit, reach 5 ft., one target. Hit: 4d8+6 piercing damage."),
            ("Stomp", "Melee Weapon Attack: +9 to hit, reach 5 ft., one prone creature. Hit: 3d10+6 bludgeoning damage."),
        ],
    },
    "Giant Crocodile": {
        "cr": 5, "cr_label": "5", "size": "Huge",
        "ac": 14, "ac_note": "natural armor", "hp": 85, "hit_dice": "9d12+27",
        "speed": "30 ft., swim 50 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 21, "DEX": 9, "CON": 17, "INT": 2, "WIS": 10, "CHA": 7},
        "skills": [("Stealth", "+5")],
        "senses": "passive Perception 10",
        "traits": [("Hold Breath", "The crocodile can hold its breath for 30 minutes.")],
        "actions": [
            ("Multiattack", "The crocodile makes two attacks: one bite and one tail."),
            ("Bite", "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 3d10+5 piercing damage, and the target is grappled (escape DC 16) and restrained until the grapple ends; the crocodile can't bite another target while grappling one."),
            ("Tail", "Melee Weapon Attack: +8 to hit, reach 10 ft., one target not grappled by the crocodile. Hit: 2d8+5 bludgeoning damage; if the target is a creature, it must succeed a DC 16 STR save or be knocked prone."),
        ],
    },
    "Air Elemental": {
        "cr": 5, "cr_label": "5", "size": "Large",
        "ac": 15, "ac_note": "", "hp": 90, "hit_dice": "12d10+24",
        "speed": "0 ft., fly 90 ft. (hover)", "flies": True, "swims": False,
        "abilities": {"STR": 14, "DEX": 20, "CON": 14, "INT": 6, "WIS": 10, "CHA": 6},
        "skills": [],
        "senses": "darkvision 60 ft., passive Perception 10",
        "damage_resistances": "lightning, thunder; bludgeoning, piercing, and slashing from nonmagical attacks",
        "damage_immunities": "poison",
        "condition_immunities": "exhaustion, grappled, paralyzed, petrified, poisoned, prone, restrained, unconscious",
        "traits": [("Air Form", "The elemental can enter a hostile creature's space and stop there. It can move through a space as narrow as 1 inch wide without squeezing.")],
        "actions": [
            ("Multiattack", "The elemental makes two slam attacks."),
            ("Slam", "Melee Weapon Attack: +8 to hit, reach 5 ft., one target. Hit: 14 (2d8+5) bludgeoning damage."),
            ("Whirlwind (Recharge 4-6)", "Each creature in the elemental's space must make a DC 13 Strength saving throw. On a failure, a target takes 15 (3d8+2) bludgeoning damage and is flung up to 20 ft away in a random direction and knocked prone; if it strikes an object it takes 3 (1d6) bludgeoning damage per 10 ft thrown, and if thrown at another creature that creature must succeed on a DC 13 Dexterity save or take the same damage and be knocked prone. On a success, the target takes half damage and isn't flung or knocked prone."),
        ],
    },
    "Water Elemental": {
        "cr": 5, "cr_label": "5", "size": "Large",
        "ac": 14, "ac_note": "natural armor", "hp": 114, "hit_dice": "12d10+48",
        "speed": "30 ft., swim 90 ft.", "flies": False, "swims": True,
        "abilities": {"STR": 18, "DEX": 14, "CON": 18, "INT": 5, "WIS": 10, "CHA": 8},
        "skills": [],
        "senses": "darkvision 60 ft., passive Perception 10",
        "damage_resistances": "acid; bludgeoning, piercing, and slashing from nonmagical attacks",
        "damage_immunities": "poison",
        "condition_immunities": "exhaustion, grappled, paralyzed, petrified, poisoned, prone, restrained, unconscious",
        "traits": [
            ("Freeze", "If the elemental takes cold damage, its speed is reduced by 20 ft until the end of its next turn."),
            ("Water Form", "The elemental can enter a hostile creature's space and stop there. It can move through a space as narrow as 1 inch wide without squeezing."),
        ],
        "actions": [
            ("Multiattack", "The elemental makes two slam attacks."),
            ("Slam", "Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 13 (2d8+4) bludgeoning damage."),
            ("Whelm (Recharge 4-6)", "Each creature in the elemental's space must make a DC 15 Strength saving throw. On a failure, a target takes 13 (2d8+4) bludgeoning damage; if Large or smaller, it's also grappled (escape DC 14) and restrained and unable to breathe unless it can breathe water, taking 13 (2d8+4) bludgeoning damage again at the start of each of the elemental's turns until the grapple ends. On a success, the target is pushed out of the elemental's space. The elemental can grapple one Large or up to two Medium/smaller creatures at once."),
        ],
    },
    "Earth Elemental": {
        "cr": 5, "cr_label": "5", "size": "Large",
        "ac": 17, "ac_note": "natural armor", "hp": 126, "hit_dice": "12d10+60",
        "speed": "30 ft., burrow 30 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 20, "DEX": 8, "CON": 20, "INT": 5, "WIS": 10, "CHA": 5},
        "skills": [],
        "senses": "darkvision 60 ft., tremorsense 60 ft., passive Perception 10",
        "damage_resistances": "bludgeoning, piercing, and slashing from nonmagical attacks",
        "damage_immunities": "poison",
        "condition_immunities": "exhaustion, paralyzed, petrified, poisoned, unconscious",
        "traits": [
            ("Vulnerable to Thunder", "The elemental has vulnerability to thunder damage."),
            ("Earth Glide", "The elemental can burrow through nonmagical, unworked earth and stone without disturbing the material it moves through."),
            ("Siege Monster", "The elemental deals double damage to objects and structures."),
        ],
        "actions": [
            ("Multiattack", "The elemental makes two slam attacks."),
            ("Slam", "Melee Weapon Attack: +8 to hit, reach 10 ft., one target. Hit: 14 (2d8+5) bludgeoning damage."),
        ],
    },
    "Fire Elemental": {
        "cr": 5, "cr_label": "5", "size": "Large",
        "ac": 13, "ac_note": "", "hp": 102, "hit_dice": "12d10+36",
        "speed": "50 ft.", "flies": False, "swims": False,
        "abilities": {"STR": 10, "DEX": 17, "CON": 16, "INT": 6, "WIS": 10, "CHA": 7},
        "skills": [],
        "senses": "darkvision 60 ft., passive Perception 10",
        "damage_resistances": "bludgeoning, piercing, and slashing from nonmagical attacks",
        "damage_immunities": "fire, poison",
        "condition_immunities": "exhaustion, grappled, paralyzed, petrified, poisoned, prone, restrained, unconscious",
        "traits": [
            ("Fire Form", "The elemental can move through a space as narrow as 1 inch wide without squeezing. A creature that touches it or hits it with a melee attack within 5 ft takes 5 (1d10) fire damage. The first time it enters a creature's space on a turn, that creature takes 5 (1d10) fire damage and catches fire, taking 5 (1d10) fire damage at the start of each of its turns until someone douses it."),
            ("Illumination", "The elemental sheds bright light in a 30-foot radius and dim light for an additional 30 feet."),
            ("Water Susceptibility", "For every 5 ft the elemental moves in water, or for every gallon of water splashed on it, it takes 1 cold damage."),
        ],
        "actions": [
            ("Multiattack", "The elemental makes two touch attacks."),
            ("Touch", "Melee Weapon Attack: +6 to hit, reach 5 ft., one target. Hit: 10 (2d6+3) fire damage; a creature or flammable object hit ignites, taking 5 (1d10) fire damage at the start of each of its turns until someone douses it."),
        ],
    },
}


