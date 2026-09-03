import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui.style.theme import *
from ...shared import *
# `import *` silently skips underscore-prefixed names when a module has no
# __all__ (shared.py doesn't) — _btn/_pill need an explicit import for that
# reason. _lbl/_card/_sep don't (they're defined a few lines down as local
# aliases to h/card/hline, which ARE plain names the wildcard import above
# already brought in).
from ...shared import _btn, _pill
from ...widgets import FlowLayout, FlowContainer
from dnd_app.core.character import (
    ability_score, ability_mod, total_level, class_levels, subclasses,
    long_rest, short_rest, add_class
)
from dnd_app.core.calculator import (
    update_all, get_ac, get_prof_bonus, get_initiative,
    all_skill_bonuses, all_saving_throw_bonuses, get_save_advantage_status,
    get_initiative_advantage_status, get_carry_capacity,
    get_spell_save_dc, get_spell_attack_bonus,
    get_passive_perception, get_sneak_attack, get_martial_arts_die,
    get_rage_damage, _detect_spell_ability, get_ac, has_reliable_talent,
    get_ac_breakdown, get_speed_breakdown, get_effective_speed,
    get_save_dc_breakdown, get_spell_attack_breakdown, get_weapon_attack_breakdown,
    get_onhit_damage_bonuses,
)
from dnd_app.core.multiclass import (
    compute_all_spell_slots, get_extra_attacks, aggregate_resources,
    compute_hit_points, get_saving_throw_profs
)
from dnd_app.core.builder import rebuild
from dnd_app.core.controller import CharacterController
from dnd_app.core.magic_items import concentration_save, start_concentration, drop_concentration
from dnd_app.core.spell_components import spell_component_block_reason
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters, character_filename, validate_character,
)
from dnd_app.core.character import set_subclass, get_class_entry
from dnd_app.data.phbCommon.magic_items import ALL_MAGIC_ITEMS, has_item_effect
from dnd_app.ui.dialogs.levelup_panel import LevelUpPanel
from dnd_app.data.phb2014.classes import CLASS_DICT, CLASS_NAMES, BATTLE_MASTER_MANEUVERS, WILD_MAGIC_SURGE_TABLE
from dnd_app.data.phb2014.races import get_race
from dnd_app.data.phbCommon.backgrounds import get_background
from dnd_app.data.phbCommon.feats import get_feat
from dnd_app.data.phbCommon.spells import get_spell, spells_for_class, ALL_SPELLS
from dnd_app.data.phbCommon.items import (ARMOR, ARMOR_DICT, ALL_WEAPONS, WEAPON_DICT,
    ADVENTURING_GEAR, GEAR_NAMES, MOUNTS, ALL_TOOLS, SIMPLE_MELEE, SIMPLE_RANGED,
    MARTIAL_MELEE, MARTIAL_RANGED, ARTISAN_TOOLS, SPECIAL_ARMOR)
from dnd_app.data.phbCommon.conditions import CONDITIONS
from .base import *
from .base import _lbl, _sep, _card


class TraitsNotesMixin:
    def _build_tab_traits_notes(self):
        tab = QScrollArea(); tab.setWidgetResizable(True)
        w = QWidget(); tab.setWidget(w)
        root = QHBoxLayout(w); root.setContentsMargins(20,20,20,20); root.setSpacing(16)

        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(10)
        self._trait_edits = {}
        for label, key in [("Personality Traits","personality_traits"),("Ideals","ideals"),
                           ("Bonds","bonds"),("Flaws","flaws")]:
            ll.addWidget(_lbl(label.upper(), GOLD, FS_SMALL, bold=True))
            ed = QTextEdit(); ed.setMaximumHeight(90)
            ed.setPlaceholderText(f"Enter {label.lower()}…")
            self._trait_edits[key] = ed; ll.addWidget(ed)
        ll.addStretch(); root.addWidget(left, 1)

        right = QWidget(); rl5 = QVBoxLayout(right); rl5.setSpacing(10)
        rl5.addWidget(_lbl("BACKSTORY & APPEARANCE", GOLD, FS_SMALL, bold=True))
        self._backstory_edit = QTextEdit(); self._backstory_edit.setPlaceholderText("Character backstory, appearance, allies, enemies…")
        rl5.addWidget(self._backstory_edit, 1)
        rl5.addWidget(_lbl("CAMPAIGN NOTES", GOLD, FS_SMALL, bold=True))
        self._notes_edit = QTextEdit(); self._notes_edit.setPlaceholderText("Session notes, quest log, treasure…")
        rl5.addWidget(self._notes_edit, 1)
        root.addWidget(right, 2)
        return tab

    # ════════════════════════════════════════════════════════════
    #  LOAD / REFRESH
    # ════════════════════════════════════════════════════════════
