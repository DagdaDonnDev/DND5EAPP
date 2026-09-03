"""
Starting Equipment data module.

Class starting equipment — the real "(a) or (b)" choice tables from
the PHB (plus Artificer/TCE and Blood Hunter), not just a flat gear
list. Feeds the equipment step of the character creation wizard.

Each class maps to a list of "choice groups". Each group is a dict:
  {"options": [...], "gold_alt": int or None}
Each option in "options" is itself a list of item name strings
(a group of items granted together as one lettered choice, e.g.
"(a) leather armor, two daggers" is one option with two items).
"gold_alt", if present, means the group can alternatively be
satisfied by taking that many gold pieces instead (used sparingly —
most PHB classes don't offer this per-group, it's usually an
overall alternative; see NOTES below for classes where the "or take
starting wealth instead" alternative applies at the whole-class
level rather than per-group).

Author: Ethan O'Brien
Date: 2026-08-20
"""

STARTING_EQUIPMENT = {
    "Barbarian": [
        {"options": [["Greataxe"], ["Any martial melee weapon"]]},
        {"options": [["Handaxe", "Handaxe"], ["Any simple weapon"]]},
        {"options": [["Explorer's Pack", "Javelin", "Javelin", "Javelin", "Javelin"]]},
    ],
    "Bard": [
        {"options": [["Rapier"], ["Longsword"], ["Any simple weapon"]]},
        {"options": [["Diplomat's Pack"], ["Entertainer's Pack"]]},
        {"options": [["Lute"], ["Any other musical instrument"]]},
        {"options": [["Leather", "Dagger"]]},
    ],
    "Cleric": [
        {"options": [["Mace"], ["Warhammer (if proficient)"]]},
        {"options": [["Scale Mail"], ["Leather"], ["Chain Mail (if proficient)"]]},
        {"options": [["Light Crossbow", "Crossbow Bolts (20)"], ["Any simple weapon"]]},
        {"options": [["Priest's Pack"], ["Explorer's Pack"]]},
        {"options": [["Shield", "Holy Symbol"]]},
    ],
    "Druid": [
        {"options": [["Wooden Shield"], ["Any simple weapon"]]},
        {"options": [["Scimitar"], ["Any simple melee weapon"]]},
        {"options": [["Leather", "Explorer's Pack", "Druidic Focus"]]},
    ],
    "Fighter": [
        {"options": [["Chain Mail"], ["Leather", "Longbow", "Arrows (20)"]]},
        {"options": [["Any martial weapon", "Shield"], ["Any martial weapon", "Any martial weapon"]]},
        {"options": [["Light Crossbow", "Crossbow Bolts (20)"], ["Handaxe", "Handaxe"]]},
        {"options": [["Dungeoneer's Pack"], ["Explorer's Pack"]]},
    ],
    "Monk": [
        {"options": [["Shortsword"], ["Any simple weapon"]]},
        {"options": [["Dungeoneer's Pack"], ["Explorer's Pack"]]},
        {"options": [["Dart", "Dart", "Dart", "Dart", "Dart",
                       "Dart", "Dart", "Dart", "Dart", "Dart"]]},
    ],
    "Paladin": [
        {"options": [["Any martial weapon", "Shield"], ["Any martial weapon", "Any martial weapon"]]},
        {"options": [["Javelin", "Javelin", "Javelin", "Javelin", "Javelin"],
                     ["Any simple melee weapon"]]},
        {"options": [["Priest's Pack"], ["Explorer's Pack"]]},
        {"options": [["Chain Mail", "Holy Symbol"]]},
    ],
    "Ranger": [
        {"options": [["Scale Mail"], ["Leather"]]},
        {"options": [["Shortsword", "Shortsword"], ["Any simple melee weapon", "Any simple melee weapon"]]},
        {"options": [["Dungeoneer's Pack"], ["Explorer's Pack"]]},
        {"options": [["Longbow", "Quiver", "Arrows (20)"]]},
    ],
    "Rogue": [
        {"options": [["Rapier"], ["Shortsword"]]},
        {"options": [["Shortbow", "Quiver", "Arrows (20)"], ["Shortsword"]]},
        {"options": [["Burglar's Pack"], ["Dungeoneer's Pack"], ["Explorer's Pack"]]},
        {"options": [["Leather", "Dagger", "Dagger", "Thieves' Tools"]]},
    ],
    "Sorcerer": [
        {"options": [["Light Crossbow", "Crossbow Bolts (20)"], ["Any simple weapon"]]},
        {"options": [["Component Pouch"], ["Arcane Focus"]]},
        {"options": [["Dungeoneer's Pack"], ["Explorer's Pack"]]},
        {"options": [["Dagger", "Dagger"]]},
    ],
    "Warlock": [
        {"options": [["Light Crossbow", "Crossbow Bolts (20)"], ["Any simple weapon"]]},
        {"options": [["Component Pouch"], ["Arcane Focus"]]},
        {"options": [["Scholar's Pack"], ["Dungeoneer's Pack"]]},
        {"options": [["Leather", "Any simple weapon", "Dagger", "Dagger"]]},
    ],
    "Wizard": [
        {"options": [["Quarterstaff"], ["Dagger"]]},
        {"options": [["Component Pouch"], ["Arcane Focus"]]},
        {"options": [["Scholar's Pack"], ["Explorer's Pack"]]},
        {"options": [["Spellbook"]]},
    ],
    "Artificer": [
        {"options": [["Any simple weapon", "Any simple weapon"]]},
        {"options": [["Light Crossbow", "Crossbow Bolts (20)"]]},
        {"options": [["Studded Leather"], ["Scale Mail"]]},
        {"options": [["Thieves' Tools", "Dungeoneer's Pack"]]},
    ],
    "Blood Hunter": [
        {"options": [["Any martial weapon", "Shield"], ["Any simple weapon", "Any simple weapon"],
                     ["Any martial weapon", "Any martial weapon"]]},
        {"options": [["Light Crossbow", "Crossbow Bolts (20)"], ["Hand Crossbow", "Crossbow Bolts (20)"]]},
        {"options": [["Studded Leather"], ["Scale Mail"], ["Chain Mail"]]},
        {"options": [["Explorer's Pack", "Alchemist's Supplies"]]},
    ],
}


def get_starting_equipment(class_name: str) -> list:
    return STARTING_EQUIPMENT.get(class_name, [])
