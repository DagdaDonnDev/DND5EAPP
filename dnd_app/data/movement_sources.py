"""
Central catalog of sources that grant a character a swim, climb, or fly
speed beyond plain walking — racial traits (passive) and class features
(passive or toggle-driven, same active_effects mechanism as
resistance_sources.py). Multiple sources of the SAME movement type don't
add together (a character with two "swim 30" sources doesn't swim 60) —
the resolver in calculator.py takes the highest value per type.

Author: Ethan O'Brien
Date: 2026-08-20
"""

# Fixed per race, no sub-choice, always active (some level-gated).
RACIAL_MOVEMENT = {
    "Aarakocra": [{"kind": "fly", "speed": 50, "source": "Flight",
                   "no_medium_heavy_armor": True}],
    "Dhampir":   [{"kind": "climb", "speed": "walk", "source": "Spider Climb"}],
    "Locathah":  [{"kind": "swim", "speed": 30, "source": "Locathah"}],
    "Tabaxi":    [{"kind": "climb", "speed": 20, "source": "Cat's Claws"}],
    "Triton":    [{"kind": "swim", "speed": 30, "source": "Triton"}],
    "Fairy":     [{"kind": "fly", "speed": 30, "source": "Flight",
                   "no_medium_heavy_armor": True}],
    "Owlin":     [{"kind": "fly", "speed": 30, "source": "Flight",
                   "no_medium_heavy_armor": True}],
    "Merfolk":   [{"kind": "swim", "speed": 30, "source": "Amphibious"}],
    "Kor":       [{"kind": "climb", "speed": 30, "source": "Kor Climbing",
                   "no_heavy_armor": True}],
}

SUBRACE_MOVEMENT = {
    ("Elf", "sea"):        [{"kind": "swim", "speed": 30, "source": "Sea Elf"}],
    ("Half-Elf", "aquatic"): [{"kind": "swim", "speed": 30, "source": "Aquatic Half-Elf"}],
    ("Genasi", "water"):  [{"kind": "swim", "speed": 30, "source": "Water Genasi"}],
    ("Tiefling", "winged"): [{"kind": "fly", "speed": 30, "source": "Winged Tiefling", "min_char_level": 3}],
}

# Always active once the (class, subclass, level) matches — no toggle.
SUBCLASS_PASSIVE_MOVEMENT = [
    {"class_key": "Sorcerer", "subclass_match": "storm sorcery", "min_level": 18,
     "grants": [{"kind": "fly", "speed": 60, "source": "Wind Soul"}]},
    # Storm Herald's Storm Soul (6th level): Sea grants a swim speed of 30
    # ft alongside its already-implemented lightning resistance (see
    # resistance_sources.py). Desert/Tundra grant no movement benefit.
    {"class_key": "Barbarian", "subclass_match": "storm herald", "min_level": 6,
     "override_check": "storm_herald_aura", "choice_source": "storm_aura_3",
     "override_grants": {
         "sea": [{"kind": "swim", "speed": 30, "source": "Storm Soul (Sea)"}],
     }},
    {"class_key": "Warlock", "subclass_match": "fathomless", "min_level": 1,
     "grants": [{"kind": "swim", "speed": 40, "source": "Gift of the Sea"}]},
    {"class_key": "Rogue", "subclass_match": "thief", "min_level": 3,
     "grants": [{"kind": "climb", "speed": "walk", "source": "Second-Story Work"}]},
]

# Only active while `toggle_key` is present in char["active_effects"].
# speed == "walk" means "equal to your current walking speed" (resolved
# against the character's own base+effect walk speed at read time).
SUBCLASS_TOGGLE_MOVEMENT = [
    {"race": "Aasimar", "subrace_match": "protector", "min_char_level": 3,
     "toggle_key": "Radiant Soul (Aasimar)",
     "grants": [{"kind": "fly", "speed": 30, "source": "Radiant Soul"}]},
    {"race": "Aasimar", "subrace_match": "fallen", "min_char_level": 3,
     "toggle_key": "Necrotic Shroud",
     "grants": [{"kind": "fly", "speed": 30, "source": "Necrotic Shroud"}]},
    {"race": "Dragonborn", "subrace_match": "gem", "min_char_level": 5,
     "toggle_key": "Gem Flight",
     "grants": [{"kind": "fly", "speed": "walk", "source": "Gem Flight"}]},
    {"class_key": "Warlock", "subclass_match": "undead", "min_level": 10,
     "toggle_key": "Spirit Projection",
     "grants": [{"kind": "fly", "speed": "walk", "source": "Spirit Projection"}]},
    {"class_key": "Sorcerer", "subclass_match": "draconic", "min_level": 14,
     "toggle_key": "Dragon Wings",
     "grants": [{"kind": "fly", "speed": "walk", "source": "Dragon Wings"}]},
    {"class_key": "Sorcerer", "subclass_match": "divine soul", "min_level": 14,
     "toggle_key": "Otherworldly Wings",
     "grants": [{"kind": "fly", "speed": 30, "source": "Otherworldly Wings"}]},
    {"class_key": "Warlock", "subclass_match": "genie", "min_level": 6,
     "toggle_key": "Elemental Gift",
     "grants": [{"kind": "fly", "speed": 30, "source": "Elemental Gift"}]},
    {"class_key": "Barbarian", "subclass_match": None, "min_level": 1,
     "toggle_key": "Rage",
     # Totem Warrior's Eagle Totemic Attunement (14th level) grants a
     # flying speed equal to walking speed while raging. totem_attune_14
     # is collected during level-up (levelup_panel.py) and read here via
     # this override_check.
     "grants": [],
     "override_check": "eagle_totem_attunement",
     "override_grants": [{"kind": "fly", "speed": "walk", "source": "Totemic Attunement (Eagle)"}]},
    {"class_key": "Barbarian", "subclass_match": "beast", "min_level": 6,
     "toggle_key": "Rage",
     # Bestial Soul grants swim OR climb speed (player's choice, tied to
     # which animal their Form of the Beast resembles) — this app doesn't
     # separately track which animal beyond the Bite/Claws/Tail weapon
     # choice, so this grants swim as a reasonable default rather than
     # blocking the feature entirely for lack of a finer-grained pick.
     "grants": [{"kind": "swim", "speed": "walk", "source": "Bestial Soul"}]},
]
