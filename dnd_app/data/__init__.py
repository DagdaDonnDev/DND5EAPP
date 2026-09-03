"""
Data package.

Static game-rules data: races/species, classes, backgrounds, feats,
mundane and magic items, spells, conditions, movement/resistance
sources, and feature tooltips. Re-exports the most commonly used
lookups below.

Author: Ethan O'Brien
Date: 2026-08-20
"""

from .phb2014.races import ALL_RACES, RACE_NAMES, RACE_DICT, get_race
from .phb2014.classes import ALL_CLASSES, CLASS_NAMES, CLASS_DICT, get_class, prof_bonus, sneak_attack_dice
from .phb2024.classes_2024 import (ALL_CLASSES_2024, CLASS_NAMES_2024, CLASS_DICT_2024,
                            EPIC_BOONS_2024, FIGHTING_STYLE_FEATS_2024, METAMAGIC_2024)
from .phb2024.species_2024 import (ALL_SPECIES_2024, SPECIES_NAMES_2024,
                            ORIGIN_FEATS_2024, GENERAL_FEATS_2024,
                            get_species_2024)
from .phbCommon.backgrounds import ALL_BACKGROUNDS, BACKGROUND_NAMES, get_background
from .phbCommon.feats import ALL_FEATS, FEAT_NAMES, get_feat, feats_by_source
from .phbCommon.items import (ARMOR, ARMOR_DICT, ARMOR_NAMES, ARMOR_NAMES_FULL,
                    ALL_WEAPONS, WEAPON_DICT, WEAPON_NAMES, ADVENTURING_GEAR, ALL_TOOLS)
from .phbCommon.magic_items import (
    ALL_MAGIC_ITEMS, MAGIC_ITEM_NAMES, MAGIC_ITEM_EFFECTS,
    get_magic_item, get_item_effect, has_item_effect, items_by_rarity,
)
