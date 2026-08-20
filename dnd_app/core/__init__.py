"""
Core package.

Non-UI application logic: character data model, derived-stat
calculation, multiclass rules, build/rebuild pipeline, magic item and
spell/condition effects, and save/load. Re-exports the most commonly
used entry points below.

Author: Ethan O'Brien
Date: 2026-08-20
"""

from .character import new_character, total_level, class_levels, subclasses
from .calculator import update_all, combat_stats, get_prof_bonus, get_ac
from .multiclass import build_character_summary, compute_all_spell_slots
from .save_load import save_character, load_character, list_saved_characters
