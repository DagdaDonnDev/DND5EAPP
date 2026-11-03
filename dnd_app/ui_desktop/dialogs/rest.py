import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui_desktop.style.theme import *
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
from dnd_app.core.spellcasting import spell_component_block_reason
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters, character_filename, validate_character,
)
from dnd_app.core.character import set_subclass, get_class_entry
from dnd_app.core.character import rest_options, rest_preview_lines
from dnd_app.data.magic_items import ALL_MAGIC_ITEMS, has_item_effect
from dnd_app.ui_desktop.dialogs.levelup_panel import LevelUpPanel
from dnd_app.data.classes import CLASS_DICT, CLASS_NAMES, BATTLE_MASTER_MANEUVERS, WILD_MAGIC_SURGE_TABLE
from dnd_app.data.races import get_race
from dnd_app.data.backgrounds import get_background
from dnd_app.data.feats import get_feat
from dnd_app.data.spells import get_spell, spells_for_class, ALL_SPELLS
from dnd_app.data.items import (ARMOR, ARMOR_DICT, ALL_WEAPONS, WEAPON_DICT,
    ADVENTURING_GEAR, GEAR_NAMES, MOUNTS, ALL_TOOLS, SIMPLE_MELEE, SIMPLE_RANGED,
    MARTIAL_MELEE, MARTIAL_RANGED, ARTISAN_TOOLS, SPECIAL_ARMOR)
from dnd_app.data.conditions import CONDITIONS
from dnd_app.ui_desktop import icons as _icons


class RestOptionsDialog(QDialog):
    """Unified rest-configuration dialog — shown after finishing a short
    or long rest, surfaces every "you can change X when you finish a
    rest" choice the character actually has, found by searching the
    game's own feature text for short/long rest + change/swap language.
    Extensible: add more entries to core/character.py's rest_options() as more of these
    get confirmed and wired up.

    Currently covers: unpreparing all spells to choose new ones (any
    prepared caster, long rest), and the Artificer Armorer's Arcane
    Armor model swap (short or long rest, smith's tools in hand)."""

    def __init__(self, char, rest_type, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        self.rest_type = rest_type  # "short" or "long"
        self.setWindowTitle(f"{'Long' if rest_type == 'long' else 'Short'} Rest Options")
        self.setMinimumSize(480, 300)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        self._options = rest_options(char, rest_type)
        self._checks = {}

        root = QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(10)
        root.addWidget(_lbl("Rest Options", GOLD2, FS_HEAD, bold=True))
        root.addWidget(_lbl(
            "Your character has features that can be reconfigured on this rest. "
            "Check anything you'd like to change now.",
            TEXT2, FS_SMALL, wrap=True))

        card = _card(qa(INDIGO,0x44)); card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(10,10,10,10); card_lay.setSpacing(6)
        for opt in self._options:
            cb = QCheckBox(opt["label"])
            cb.setToolTip(opt.get("detail", ""))
            card_lay.addWidget(cb)
            self._checks[opt["kind"]] = cb
        if not self._options:
            card_lay.addWidget(_lbl("Nothing reconfigurable on this character right now.", TEXT3, FS_SMALL))
        root.addWidget(card)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        skip_btn = QPushButton("Skip"); skip_btn.setFixedHeight(34)
        skip_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton("Apply Selected"); confirm_btn.setFixedHeight(34)
        confirm_btn.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2).styleSheet())
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(skip_btn); btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)


    def get_selected(self):
        return [kind for kind, cb in self._checks.items() if cb.isChecked()]


class RestPreviewDialog(QDialog):
    """Shows exactly what a Short/Long Rest is about to restore/reset —
    HP, hit dice, spell slots, resources — before it's applied, instead
    of the rest silently happening with only a toast confirming it
    afterward. Purely informational (Confirm/Cancel); the real apply
    logic in CharacterSheet._short_rest()/_long_rest() is unchanged and
    only runs once this dialog is confirmed. `preview` is built by
    CharacterSheet._preview_short_rest()/_preview_long_rest() — plain
    filters over current character state, not a simulation, so this
    can't drift from what those methods actually do next.

    `options` (from core/character.py's rest_options()) folds the
    "anything you'd like to reconfigure on this rest" checklist into
    this same preview dialog rather than a separate confirm step, so
    the player gets one dialog and one Confirm for the whole rest.
    get_selected() below is read the same way RestOptionsDialog's is."""

    def __init__(self, rest_type: str, preview: dict, options: list, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self.rest_type = rest_type
        self._options = options
        self._checks = {}
        label = "Short Rest" if rest_type == "short" else "Long Rest"
        icon = "short_rest" if rest_type == "short" else "long_rest"
        self.setWindowTitle(label)
        self.setMinimumWidth(440)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        root = QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(12)
        root.addWidget(_icons.icon_header(icon, _lbl(label, GOLD2, FS_HEAD, bold=True), size=20, spacing=8))

        card = _card(qa(TEAL,0x44)); cl = QVBoxLayout(card)
        cl.setContentsMargins(14,12,14,14); cl.setSpacing(4)
        cl.addWidget(_lbl("WHAT THIS WILL DO", TEAL2, FS_SMALL, bold=True))
        cl.addWidget(_lbl("\n".join(rest_preview_lines(rest_type, preview)), TEXT, FS_BODY, wrap=True))
        root.addWidget(card)

        if options:
            opt_card = _card(qa(INDIGO,0x44)); ol = QVBoxLayout(opt_card)
            ol.setContentsMargins(14,12,14,14); ol.setSpacing(6)
            ol.addWidget(_lbl("ALSO RECONFIGURE?", IND2, FS_SMALL, bold=True))
            ol.addWidget(_lbl("Check anything you'd like to change as part of this rest.",
                               TEXT3, FS_TINY, wrap=True))
            for opt in options:
                cb = QCheckBox(opt["label"])
                cb.setToolTip(opt.get("detail", ""))
                ol.addWidget(cb)
                self._checks[opt["kind"]] = cb
            root.addWidget(opt_card)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton(f"Confirm {label}"); confirm_btn.setFixedHeight(34)
        confirm_btn.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2).styleSheet())
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)

    def get_selected(self):
        return [kind for kind, cb in self._checks.items() if cb.isChecked()]


