"""
Central catalog of every source (outside of magic items, which are handled
in magic_items.py) that can grant a character a damage resistance,
damage immunity, or condition immunity: racial traits, feats, and
subclass features — both passive (always on) and toggle-driven (only
while an active_effects entry, like Rage or Form of Dread, is active).

Each entry is a flat dict so the resolver in calculator.py can iterate
them uniformly. Fields:
  kind        "resistance" | "immunity"
  target      damage type string (e.g. "fire"), or "all"
  condition   (for condition immunities instead of damage) e.g. "frightened"
  nonmagical  True if the resistance only applies to nonmagical weapon damage
  source      display label used in the resistance-strip tooltip

RACIAL_RESISTANCES: keyed by exact race name, applies regardless of subrace.
SUBRACE_RESISTANCES: keyed by (race name, subrace name substring), only
  applies for that specific subrace.
FEAT_RESISTANCES: keyed by exact feat name.
SUBCLASS_PASSIVE_RESISTANCES: list of dicts, always active once the
  character's (class, subclass, level) matches — no toggle needed.
SUBCLASS_TOGGLE_RESISTANCES: list of dicts, only active while a specific
  active_effects entry is present. Some have a level-gated upgrade (e.g.
  Form of Dread's necrotic resistance becomes immunity at 10th level).

Known gaps (need a dedicated sub-choice picker that doesn't exist yet, so
these can't be auto-resolved): Monk Ascendant Dragon's separate
resistance-vs-frightful-presence choice at higher levels (distinct from
Draconic Strike's per-attack damage type, which the "ascendant_dragon_ack"
info acknowledgment already covers), and Sorcerer/Fighter feats with a
DM's-choice or chosen-plane component (Scion of the Outer Planes,
Elemental Adept). These are intentionally left out rather than guessed.

Author: Ethan O'Brien
Date: 2026-08-20
"""

RACIAL_RESISTANCES = {
    "Dwarf":             [{"kind": "resistance", "target": "poison", "source": "Dwarven Resilience"}],
    "Tiefling":          [{"kind": "resistance", "target": "fire", "source": "Hellish Resistance"}],
    "Aasimar":           [{"kind": "resistance", "target": "necrotic", "source": "Celestial Resistance"},
                           {"kind": "resistance", "target": "radiant", "source": "Celestial Resistance"}],
    "Githzerai":         [{"kind": "resistance", "target": "psychic", "source": "Psychic Resilience"}],
    "Triton":            [{"kind": "resistance", "target": "cold", "source": "Guardians of the Depths"}],
    "Kalashtar":         [{"kind": "resistance", "target": "psychic", "source": "Mental Discipline"}],
    "Autognome":         [{"kind": "resistance", "target": "poison", "source": "Mechanical Nature"},
                           {"kind": "condition", "condition": "disease", "source": "Mechanical Nature"}],
    # Deathless Nature grants resistance to poison damage (plus advantage
    # on saves against disease/poison, which isn't a resistance/immunity
    # in the sense this table tracks).
    "Reborn":            [{"kind": "resistance", "target": "poison", "source": "Deathless Nature"}],
    "Plasmoid":          [{"kind": "resistance", "target": "acid", "source": "Natural Resilience"},
                           {"kind": "resistance", "target": "poison", "source": "Natural Resilience"}],
    "Warforged":         [{"kind": "resistance", "target": "poison", "source": "Constructed Resilience"}],
    "Aetherborn":        [{"kind": "resistance", "target": "necrotic", "source": "Born of Aether"}],
}

SUBRACE_RESISTANCES = {
    ("Halfling", "stout"):  [{"kind": "resistance", "target": "poison", "source": "Stout Resilience"}],
    ("Elf", "shadar-kai"):  [{"kind": "resistance", "target": "necrotic", "source": "Shadar-kai"}],
    ("Genasi", "fire"):     [{"kind": "resistance", "target": "fire", "source": "Fire Genasi"}],
    ("Genasi", "water"):    [{"kind": "resistance", "target": "acid", "source": "Water Genasi"}],
    ("Yuan-ti Pureblood", "mpmm"): [{"kind": "resistance", "target": "poison", "source": "Poison Resilience"}],
    ("Yuan-ti Pureblood", "vgm"):  [{"kind": "immunity", "target": "poison", "source": "Poison Immunity"},
                                     {"kind": "condition", "condition": "poisoned", "source": "Poison Immunity"}],
}

FEAT_RESISTANCES = {
    "Infernal Constitution":       [{"kind": "resistance", "target": "cold", "source": "Infernal Constitution"},
                                     {"kind": "resistance", "target": "poison", "source": "Infernal Constitution"}],
    "Ember of the Fire Giant":     [{"kind": "resistance", "target": "fire", "source": "Ember of the Fire Giant"}],
    "Fury of the Frost Giant":     [{"kind": "resistance", "target": "cold", "source": "Fury of the Frost Giant"}],
}

# DM-Granted Bonus Features (dm_rewards.py) with a passive resistance
# or immunity. Keyed by exact DM reward name, same shape as
# FEAT_RESISTANCES above.
DM_REWARD_RESISTANCES = {
    "Anvilwrought":  [{"kind": "resistance", "target": "poison", "source": "Constructed Resilience"},
                       {"kind": "condition", "condition": "disease", "source": "Constructed Resilience"}],
    "Midwinter Child": [{"kind": "resistance", "target": "cold", "source": "Midwinter Child"}],
    "Inscrutable":   [{"kind": "resistance", "target": "psychic", "source": "Psychic Shield"}],
    "Nyxborn":       [{"kind": "resistance", "target": "necrotic", "source": "Nyxborn Resistance"},
                       {"kind": "resistance", "target": "radiant", "source": "Nyxborn Resistance"}],
}

# Spells (spells.py) with a real resistance grant — keyed by active_effects name, not feat/DM-reward name.
SPELL_EFFECT_RESISTANCES = {
    "Protection from Poison": [{"kind": "resistance", "target": "poison", "source": "Protection from Poison"}],
    "Gaseous Form": [{"kind": "resistance", "target": "nonmagical", "source": "Gaseous Form"}],
    "Invulnerability": [{"kind": "immunity", "target": "all", "source": "Invulnerability"}],
    "Aura of Life": [{"kind": "resistance", "target": "necrotic", "source": "Aura of Life"}],
    "Aura of Purity": [{"kind": "resistance", "target": "poison", "source": "Aura of Purity"},
                        {"kind": "condition", "condition": "disease", "source": "Aura of Purity"}],
    "Mind Blank": [{"kind": "immunity", "target": "psychic", "source": "Mind Blank"},
                   {"kind": "condition", "condition": "charmed", "source": "Mind Blank"}],
    "Investiture of Flame": [{"kind": "immunity", "target": "fire", "source": "Investiture of Flame"},
                              {"kind": "resistance", "target": "cold", "source": "Investiture of Flame"}],
    "Investiture of Ice": [{"kind": "immunity", "target": "cold", "source": "Investiture of Ice"},
                            {"kind": "resistance", "target": "fire", "source": "Investiture of Ice"}],
    "Investiture of Stone": [{"kind": "resistance", "target": "nonmagical", "source": "Investiture of Stone"}],
    "Fire Shield: Warm Shield": [{"kind": "resistance", "target": "cold", "source": "Fire Shield"}],
    "Fire Shield: Chill Shield": [{"kind": "resistance", "target": "fire", "source": "Fire Shield"}],
    "Shadow of Moil": [{"kind": "resistance", "target": "radiant", "source": "Shadow of Moil"}],
    "Primordial Ward": [
        {"kind": "resistance", "target": "acid", "source": "Primordial Ward"},
        {"kind": "resistance", "target": "cold", "source": "Primordial Ward"},
        {"kind": "resistance", "target": "fire", "source": "Primordial Ward"},
        {"kind": "resistance", "target": "lightning", "source": "Primordial Ward"},
        {"kind": "resistance", "target": "thunder", "source": "Primordial Ward"},
    ],
    "Tasha's Otherworldly Guise: Lower Planes": [
        {"kind": "immunity", "target": "fire", "source": "Tasha's Otherworldly Guise"},
        {"kind": "immunity", "target": "poison", "source": "Tasha's Otherworldly Guise"},
        {"kind": "condition", "condition": "poisoned", "source": "Tasha's Otherworldly Guise"},
    ],
    "Tasha's Otherworldly Guise: Upper Planes": [
        {"kind": "immunity", "target": "radiant", "source": "Tasha's Otherworldly Guise"},
        {"kind": "immunity", "target": "necrotic", "source": "Tasha's Otherworldly Guise"},
        {"kind": "condition", "condition": "charmed", "source": "Tasha's Otherworldly Guise"},
    ],
}

# Each: class_key, subclass_substring (lowercase, matched as substring),
# min_level, grants (list of resistance dicts), plus an optional
# (upgrade_level, upgrade_grants) that REPLACES `grants` once reached.
SUBCLASS_PASSIVE_RESISTANCES = [
    {"class_key": "Monk", "subclass_match": None, "min_level": 10,
     "grants": [{"kind": "immunity", "target": "poison", "source": "Purity of Body"},
                {"kind": "condition", "condition": "poisoned", "source": "Purity of Body"},
                {"kind": "condition", "condition": "disease", "source": "Purity of Body"}]},
    {"class_key": "Paladin", "subclass_match": None, "min_level": 3,
     "grants": [{"kind": "condition", "condition": "disease", "source": "Divine Health"}]},
    {"class_key": "Paladin", "subclass_match": None, "min_level": 10,
     "grants": [{"kind": "condition", "condition": "frightened", "source": "Aura of Courage"}]},
    {"class_key": "Paladin", "subclass_match": "devotion", "min_level": 7,
     "grants": [{"kind": "condition", "condition": "charmed", "source": "Aura of Devotion"}]},
    {"class_key": "Cleric", "subclass_match": "forge domain", "min_level": 6,
     "grants": [{"kind": "resistance", "target": "fire", "source": "Soul of the Forge"}],
     "upgrade_level": 17,
     "upgrade_grants": [{"kind": "immunity", "target": "fire", "source": "Saint of Forge and Fire"},
                        {"kind": "resistance", "target": "bludgeoning", "nonmagical": True, "source": "Saint of Forge and Fire"},
                        {"kind": "resistance", "target": "piercing", "nonmagical": True, "source": "Saint of Forge and Fire"},
                        {"kind": "resistance", "target": "slashing", "nonmagical": True, "source": "Saint of Forge and Fire"}]},
    {"class_key": "Sorcerer", "subclass_match": "pyromancer", "min_level": 6,
     "grants": [{"kind": "resistance", "target": "fire", "source": "Fire in the Veins"}],
     "upgrade_level": 18,
     "upgrade_grants": [{"kind": "immunity", "target": "fire", "source": "Fiery Soul"}]},
    {"class_key": "Cleric", "subclass_match": "war domain", "min_level": 17,
     "grants": [{"kind": "resistance", "target": "bludgeoning", "nonmagical": True, "source": "Avatar of Battle"},
                {"kind": "resistance", "target": "piercing", "nonmagical": True, "source": "Avatar of Battle"},
                {"kind": "resistance", "target": "slashing", "nonmagical": True, "source": "Avatar of Battle"}]},
    {"class_key": "Paladin", "subclass_match": "ancients", "min_level": 7,
     "grants": [{"kind": "resistance", "target": "spell damage", "source": "Aura of Warding"}]},
    {"class_key": "Paladin", "subclass_match": "redemption", "min_level": 20,
     "grants": [{"kind": "resistance", "target": "all", "source": "Emissary of Redemption"}]},
    {"class_key": "Sorcerer", "subclass_match": "draconic", "min_level": 6,
     "override_check": "elemental_affinity", "choice_source": "sorcerer_dragon_ancestor",
     "override_grants": {
         "acid": [{"kind": "resistance", "target": "acid", "source": "Elemental Affinity"}],
         "lightning": [{"kind": "resistance", "target": "lightning", "source": "Elemental Affinity"}],
         "fire": [{"kind": "resistance", "target": "fire", "source": "Elemental Affinity"}],
         "poison": [{"kind": "resistance", "target": "poison", "source": "Elemental Affinity"}],
         "cold": [{"kind": "resistance", "target": "cold", "source": "Elemental Affinity"}],
     }},
    {"class_key": "Sorcerer", "subclass_match": "lunar", "min_level": 14,
     "override_check": "lunar_empowerment", "choice_source": "lunar_phase",
     "override_grants": {
         "crescent moon": [{"kind": "resistance", "target": "necrotic", "source": "Lunar Empowerment"},
                           {"kind": "resistance", "target": "radiant", "source": "Lunar Empowerment"}],
         "full moon": [],
         "new moon": [],
     }},
    {"class_key": "Paladin", "subclass_match": "oathbreaker", "min_level": 15,
     "grants": [{"kind": "resistance", "target": "bludgeoning", "nonmagical": True, "source": "Supernatural Resistance"},
                {"kind": "resistance", "target": "piercing", "nonmagical": True, "source": "Supernatural Resistance"},
                {"kind": "resistance", "target": "slashing", "nonmagical": True, "source": "Supernatural Resistance"}]},
    {"class_key": "Warlock", "subclass_match": "celestial", "min_level": 6,
     "grants": [{"kind": "resistance", "target": "radiant", "source": "Radiant Soul"}]},
    {"class_key": "Warlock", "subclass_match": "undead", "min_level": 10,
     "grants": [{"kind": "resistance", "target": "necrotic", "source": "Necrotic Husk"}]},
    {"class_key": "Warlock", "subclass_match": "great old one", "min_level": 10,
     "grants": [{"kind": "resistance", "target": "psychic", "source": "Thought Shield"}]},
    {"class_key": "Warlock", "subclass_match": "fathomless", "min_level": 6,
     "grants": [{"kind": "resistance", "target": "cold", "source": "Oceanic Soul"}]},
    {"class_key": "Warlock", "subclass_match": "archfey", "min_level": 10,
     "grants": [{"kind": "condition", "condition": "charmed", "source": "Beguiling Defenses"}]},
    {"class_key": "Fighter", "subclass_match": "psi warrior", "min_level": 10,
     "grants": [{"kind": "resistance", "target": "psychic", "source": "Guarded Mind"}]},
    {"class_key": "Wizard", "subclass_match": "necromancy", "min_level": 10,
     "grants": [{"kind": "resistance", "target": "necrotic", "source": "Inured to Undeath"}]},
    {"class_key": "Sorcerer", "subclass_match": "aberrant mind", "min_level": 6,
     "grants": [{"kind": "resistance", "target": "psychic", "source": "Psychic Defenses"}]},
    {"class_key": "Sorcerer", "subclass_match": "storm sorcery", "min_level": 6,
     "grants": [{"kind": "resistance", "target": "lightning", "source": "Heart of the Storm"},
                {"kind": "resistance", "target": "thunder", "source": "Heart of the Storm"}],
     "upgrade_level": 18,
     "upgrade_grants": [{"kind": "immunity", "target": "lightning", "source": "Wind Soul"},
                        {"kind": "immunity", "target": "thunder", "source": "Wind Soul"}]},
    {"class_key": "Artificer", "subclass_match": "alchemist", "min_level": 15,
     "grants": [{"kind": "resistance", "target": "acid", "source": "Chemical Mastery"},
                {"kind": "resistance", "target": "poison", "source": "Chemical Mastery"},
                {"kind": "condition", "condition": "poisoned", "source": "Chemical Mastery"}]},
    {"class_key": "Paladin", "subclass_match": "oathbreaker", "min_level": 15,
     "grants": [{"kind": "resistance", "target": "bludgeoning", "nonmagical": True, "source": "Supernatural Resistance"},
                {"kind": "resistance", "target": "piercing", "nonmagical": True, "source": "Supernatural Resistance"},
                {"kind": "resistance", "target": "slashing", "nonmagical": True, "source": "Supernatural Resistance"}]},
    {"class_key": "Blood Hunter", "subclass_match": "mutant", "min_level": 7,
     "grants": [{"kind": "condition", "condition": "poisoned", "source": "Strange Metabolism"}]},
    # Storm Herald's Storm Soul (6th level) depends on which aura was picked
    # at 3rd level (storm_aura_3 chooser) — Desert grants fire resistance,
    # Sea grants lightning resistance, Tundra grants cold resistance.
    {"class_key": "Barbarian", "subclass_match": "storm herald", "min_level": 6,
     "override_check": "storm_herald_aura", "choice_source": "storm_aura_3",
     "override_grants": {
         "desert": [{"kind": "resistance", "target": "fire", "source": "Storm Soul (Desert)"}],
         "sea": [{"kind": "resistance", "target": "lightning", "source": "Storm Soul (Sea)"}],
         "tundra": [{"kind": "resistance", "target": "cold", "source": "Storm Soul (Tundra)"}],
     }},
    # Drakewarden's Bond of Fang and Scale (7th level) grants resistance to
    # the damage type chosen for the drake's Draconic Essence (drake_essence
    # chooser). Real text gates this on the drake actually being summoned;
    # simplified here to level + choice only,
    # matching the same simplification already used for Storm Soul above.
    {"class_key": "Ranger", "subclass_match": "drakewarden", "min_level": 7,
     "override_check": "drake_essence",
     "override_grants": {
         "acid": [{"kind": "resistance", "target": "acid", "source": "Bond of Fang and Scale"}],
         "cold": [{"kind": "resistance", "target": "cold", "source": "Bond of Fang and Scale"}],
         "fire": [{"kind": "resistance", "target": "fire", "source": "Bond of Fang and Scale"}],
         "lightning": [{"kind": "resistance", "target": "lightning", "source": "Bond of Fang and Scale"}],
         "poison": [{"kind": "resistance", "target": "poison", "source": "Bond of Fang and Scale"}],
     }},
    # Fiendish Resilience (Warlock, The Fiend, 10th level) — resistance to
    # whichever damage type was chosen (fiendish_resilience chooser). Real
    # text lets you re-choose each rest; simplified to a persistent,
    # re-pickable-via-Choices-tab selection like the others above.
    # Fiendish Resilience (Warlock, The Fiend, 10th level) — resistance to
    # whichever damage type was chosen (fiendish_resilience chooser).
    # Corrected per the real rule text: no type is excluded (including
    # B/P/S), and damage from magical or silver weapons bypasses this
    # resistance regardless of the chosen type — the "nonmagical" flag
    # marks that bypass, matching how Rage's resistance already works.
    {"class_key": "Warlock", "subclass_match": "fiend", "min_level": 10,
     "override_check": "fiendish_resilience", "choice_source": "fiendish_resilience",
     "override_grants": {
         "acid": [{"kind": "resistance", "target": "acid", "source": "Fiendish Resilience"}],
         "bludgeoning": [{"kind": "resistance", "target": "bludgeoning", "nonmagical": True, "source": "Fiendish Resilience"}],
         "cold": [{"kind": "resistance", "target": "cold", "source": "Fiendish Resilience"}],
         "fire": [{"kind": "resistance", "target": "fire", "source": "Fiendish Resilience"}],
         "force": [{"kind": "resistance", "target": "force", "source": "Fiendish Resilience"}],
         "lightning": [{"kind": "resistance", "target": "lightning", "source": "Fiendish Resilience"}],
         "necrotic": [{"kind": "resistance", "target": "necrotic", "source": "Fiendish Resilience"}],
         "piercing": [{"kind": "resistance", "target": "piercing", "nonmagical": True, "source": "Fiendish Resilience"}],
         "poison": [{"kind": "resistance", "target": "poison", "source": "Fiendish Resilience"}],
         "psychic": [{"kind": "resistance", "target": "psychic", "source": "Fiendish Resilience"}],
         "radiant": [{"kind": "resistance", "target": "radiant", "source": "Fiendish Resilience"}],
         "slashing": [{"kind": "resistance", "target": "slashing", "nonmagical": True, "source": "Fiendish Resilience"}],
         "thunder": [{"kind": "resistance", "target": "thunder", "source": "Fiendish Resilience"}],
     }},
]

# Each: activates only while `toggle_key` is present in char["active_effects"].
# min_level gates whether the toggle is available at all; upgrade_level/
# upgrade_grants let the SAME toggle grant more once a higher class level
# is reached (Necrotic Husk upgrading Form of Dread's resistance to
# immunity, for instance).
SUBCLASS_TOGGLE_RESISTANCES = [
    {"class_key": "Barbarian", "subclass_match": None, "min_level": 1,
     "toggle_key": "Rage",
     "grants": [{"kind": "resistance", "target": "bludgeoning", "nonmagical": True, "source": "Rage"},
                {"kind": "resistance", "target": "piercing", "nonmagical": True, "source": "Rage"},
                {"kind": "resistance", "target": "slashing", "nonmagical": True, "source": "Rage"}],
     # Totem Warrior's Bear totem replaces the above with resistance to
     # ALL damage except psychic, while raging. Checked via a stored pick
     # (char["_choices"]["totem_spirit"] containing "bear"), not a level gate.
     "override_check": "bear_totem",
     "override_grants": [{"kind": "resistance", "target": "all except psychic", "source": "Totem Spirit (Bear)"}]},
    {"class_key": "Barbarian", "subclass_match": "berserker", "min_level": 6,
     "toggle_key": "Rage",
     "grants": [{"kind": "condition", "condition": "charmed", "source": "Mindless Rage"},
                {"kind": "condition", "condition": "frightened", "source": "Mindless Rage"}]},
    {"class_key": "Warlock", "subclass_match": "undead", "min_level": 1,
     "toggle_key": "Form of Dread",
     "grants": [{"kind": "condition", "condition": "frightened", "source": "Form of Dread"}],
     "upgrade_level": 10,
     "upgrade_grants": [{"kind": "condition", "condition": "frightened", "source": "Form of Dread"},
                        {"kind": "immunity", "target": "necrotic", "source": "Necrotic Husk (while transformed)"}]},
    {"class_key": "Sorcerer", "subclass_match": "shadow magic", "min_level": 18,
     "toggle_key": "Umbral Form",
     "grants": [{"kind": "resistance", "target": "all except force/radiant", "source": "Umbral Form"}]},
    {"class_key": "Warlock", "subclass_match": "undead", "min_level": 14,
     "toggle_key": "Spirit Projection",
     "grants": [{"kind": "resistance", "target": "bludgeoning", "source": "Spirit Projection"},
                {"kind": "resistance", "target": "piercing", "source": "Spirit Projection"},
                {"kind": "resistance", "target": "slashing", "source": "Spirit Projection"}]},
    {"class_key": "Paladin", "subclass_match": "conquest", "min_level": 20,
     "toggle_key": "Invincible Conqueror",
     "grants": [{"kind": "resistance", "target": "all", "source": "Invincible Conqueror"}]},
    {"class_key": "Druid", "subclass_match": "circle of stars", "min_level": 10,
     "toggle_key": "Starry Form",
     "grants": [{"kind": "resistance", "target": "bludgeoning", "source": "Full of Stars"},
                {"kind": "resistance", "target": "piercing", "source": "Full of Stars"},
                {"kind": "resistance", "target": "slashing", "source": "Full of Stars"}]},
    # Not a class feature — Warding Bond is a 2nd-level spell any character
    # could have active (Cleric/Paladin base list, multiclass, or a magic
    # item), so this isn't gated by class/subclass/level at all.
    {"class_key": None, "subclass_match": None, "min_level": 0,
     "toggle_key": "Warding Bond",
     "grants": [{"kind": "resistance", "target": "all", "source": "Warding Bond"}]},
    # Genie's Elemental Gift resistance depends on which genie kind was
    # chosen at 1st level (genie_kind chooser). Real damage types per the
    # feature text: bludgeoning (dao), thunder (djinni), fire (efreeti),
    # cold (marid) — these follow the SAME mapping as Genie's Wrath, not
    # the classical element (earth/air/fire/water) the kind names suggest.
    {"class_key": "Warlock", "subclass_match": "genie", "min_level": 6,
     "toggle_key": "Elemental Gift",
     "grants": [],
     "override_check": "genie_kind",
     "override_grants": {
         "dao": [{"kind": "resistance", "target": "bludgeoning", "source": "Elemental Gift (Dao)"}],
         "djinni": [{"kind": "resistance", "target": "thunder", "source": "Elemental Gift (Djinni)"}],
         "efreeti": [{"kind": "resistance", "target": "fire", "source": "Elemental Gift (Efreeti)"}],
         "marid": [{"kind": "resistance", "target": "cold", "source": "Elemental Gift (Marid)"}],
     }},
]
