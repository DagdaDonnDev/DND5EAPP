import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui.style.theme import *
from ..shared import *
# `import *` silently skips underscore-prefixed names when a module has no
# __all__ (shared.py doesn't) — _btn/_pill need an explicit import for that
# reason. _lbl/_card/_sep don't (they're defined a few lines down as local
# aliases to h/card/hline, which ARE plain names the wildcard import above
# already brought in).
from ..shared import _btn, _pill
# Local aliases matching the short names used throughout this file.
_lbl = h
_sep = hline
_card = card
from ..widgets import FlowLayout, FlowContainer
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


class ArcaneRecoveryDialog(QDialog):
    """Lets a Wizard choose which expended spell slots to recover via
    Arcane Recovery — one spinbox per slot level (1-5, since level 6+
    slots can't be recovered this way), live-validating the total level
    spent against the budget (half Wizard level, rounded up)."""

    def __init__(self, char, budget, parent=None):
        super().__init__(parent)
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        self.budget = budget
        self.setWindowTitle("Arcane Recovery")
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        root = QVBoxLayout(self); root.setContentsMargins(18,16,18,16); root.setSpacing(8)
        root.addWidget(_lbl("Arcane Recovery", GOLD2, FS_HEAD, bold=True))
        self._budget_lbl = _lbl("", TEXT2, FS_SMALL, wrap=True)
        root.addWidget(self._budget_lbl)

        self._spins = {}
        used = char.get("spell_slots_used", [0]*9)
        for lvl in range(1, 6):  # slot levels 1-5 only
            expended = used[lvl - 1] if lvl - 1 < len(used) else 0
            if expended <= 0:
                continue
            row = QHBoxLayout()
            row.addWidget(_lbl(f"Level {lvl} slot ({expended} expended):", TEXT, FS_SMALL))
            sp = QSpinBox(); sp.setRange(0, expended)
            sp.valueChanged.connect(self._update_budget_label)
            row.addWidget(sp)
            root.addLayout(row)
            self._spins[lvl] = sp
        self._update_budget_label()

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(self.reject)
        self._confirm_btn = QPushButton("Recover"); self._confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(self._confirm_btn)
        root.addLayout(btn_row)

    def _update_budget_label(self, *_):
        spent = sum(lvl * sp.value() for lvl, sp in self._spins.items())
        remaining = self.budget - spent
        self._budget_lbl.setText(
            f"Budget: {self.budget} total slot levels. Spent so far: {spent}. Remaining: {remaining}.")
        over_budget = spent > self.budget
        self._budget_lbl.setStyleSheet(
            f"color:{CRIM2 if over_budget else TEXT2};font-size:{FS_SMALL}px;")
        if hasattr(self, "_confirm_btn"):
            self._confirm_btn.setEnabled(not over_budget)

    def get_recovered_levels(self):
        """Returns a flat list of slot levels to recover, e.g. [1,1,3]
        for two 1st-level slots and one 3rd-level slot."""
        levels = []
        for lvl, sp in self._spins.items():
            levels.extend([lvl] * sp.value())
        return levels




