import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui_desktop.style.theme import *
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
from dnd_app.ui_desktop.dialogs.levelup_panel import LevelUpPanel
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
            ed.setAcceptRichText(False)
            self._trait_edits[key] = ed; ll.addWidget(ed)

        ll.addWidget(_lbl("APPEARANCE", GOLD, FS_SMALL, bold=True))
        self._appearance_edit = QTextEdit()
        self._appearance_edit.setPlaceholderText("Age, height, build, eyes, notable features…")
        self._appearance_edit.setAcceptRichText(False)
        ll.addWidget(self._appearance_edit, 1)
        root.addWidget(left, 1)

        # The right column is entirely the Campaign Notes tab widget --
        # Backstory is its own always-present first tab (a first-class
        # character field, not removable/renamable like the rest), and
        # a long-running campaign's session logs/quest threads/loot
        # lists get their own pages too rather than fighting for space
        # in one box. Each page is its own QTextEdit (already scrollable
        # on its own) with a player-chosen title -- double-click a tab
        # to rename it, "+ Page" to add another (capped at
        # _MAX_NOTES_PAGES so the tab bar can't grow without bound),
        # "Remove Page" to drop the one currently open (at least one
        # non-Backstory page always stays).
        right = QWidget(); rl5 = QVBoxLayout(right); rl5.setSpacing(10)
        notes_header = QHBoxLayout(); notes_header.setSpacing(8)
        notes_header.addWidget(_lbl("CAMPAIGN NOTES", GOLD, FS_SMALL, bold=True))
        notes_header.addStretch()
        remove_page_btn = _btn("Remove Page", CRIMSON, variant="ghost", height=24,
                                font_size=FS_TINY, padding="2px 10px",
                                tooltip="Remove the notes page currently open")
        remove_page_btn.clicked.connect(lambda: self._remove_notes_page(self._notes_tabs.currentIndex()))
        notes_header.addWidget(remove_page_btn)
        add_page_btn = _btn("+ Page", TEAL, variant="ghost", height=24,
                             font_size=FS_TINY, padding="2px 10px",
                             tooltip="Add a new notes page (e.g. NPCs, Loot, a specific arc)")
        add_page_btn.clicked.connect(self._add_notes_page)
        notes_header.addWidget(add_page_btn)
        rl5.addLayout(notes_header)

        self._notes_tabs = QTabWidget()
        # A compact, locally-scoped style rather than the global
        # QTabBar::tab rule -- that one's sized for the sheet's own
        # full-width top-level tabs (Abilities/Combat/etc.), and its
        # 12px/22px padding overwhelms a small tab strip squeezed into
        # one column.
        self._notes_tabs.setStyleSheet(
            f"QTabWidget::pane{{border:1px solid {qa(TEAL,0x33)};border-radius:8px;"
            f"background:{SURF};margin-top:-1px;}}"
            f"QTabBar::tab{{background:{BG};color:{TEXT2};border:1px solid {qa(TEAL,0x22)};"
            f"border-bottom:none;padding:6px 14px;border-radius:6px 6px 0 0;"
            f"font-size:{FS_SMALL}px;font-weight:700;min-width:0px;margin-right:2px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD};border-color:{qa(TEAL,0x66)};}}"
            f"QTabBar::tab:hover:!selected{{background:{qa(TEAL,0x11)};color:{TEAL2};}}"
        )
        self._notes_tabs.tabBarDoubleClicked.connect(self._rename_notes_page)

        self._backstory_edit = QTextEdit()
        self._backstory_edit.setPlaceholderText("Character backstory, allies, enemies…")
        self._backstory_edit.setAcceptRichText(False)
        self._notes_tabs.addTab(self._backstory_edit, "Backstory")

        for page in self._notes_pages_for_char():
            self._add_notes_page_widget(page.get("title", "Notes"), page.get("text", ""))
        rl5.addWidget(self._notes_tabs, 1)

        root.addWidget(right, 2)

        # Live-sync the Traits/Backstory/Appearance fields into self.char
        # as the player types, the same way _name_edit does -- otherwise
        # nothing ever writes these into self.char, so a later
        # refresh/rebuild (which repopulates these widgets FROM
        # self.char) or a save to disk (which serializes self.char
        # as-is) silently discards whatever was typed. The flexible
        # Notes pages sync the same way, via _sync_notes_pages_to_char
        # (connected in _add_notes_page_widget).
        self._notes_field_edits = dict(self._trait_edits, backstory=self._backstory_edit,
                                        appearance_notes=self._appearance_edit)
        for key, ed in self._notes_field_edits.items():
            ed.textChanged.connect(lambda k=key, e=ed: self._on_notes_field_changed(k, e))

        return tab

    def _on_notes_field_changed(self, key: str, edit) -> None:
        self.char[key] = edit.toPlainText()
        self._mark_dirty()

    # ── Campaign Notes: multi-page tabs ────────────────────────────────────
    _MAX_NOTES_PAGES = 8   # excludes the always-present Backstory tab

    def _default_notes_pages(self) -> list:
        """Starter categories for a character with nothing written yet --
        broad enough that most sessions' worth of scribbles have an
        obvious home, while "+ Page" covers anything more specific."""
        return [{"title": t, "text": ""} for t in
                ("Session Log", "Quest Log", "Loot & Treasure")]

    def _notes_pages_for_char(self) -> list:
        pages = self.char.get("notes_pages")
        if pages:
            return pages
        legacy = self.char.get("notes", "")
        if legacy:
            # Pre-tabs characters (and the Wizard's starting-notes field)
            # only ever wrote a single flat string -- preserved as one
            # page rather than dropped.
            return [{"title": "General", "text": legacy}]
        return self._default_notes_pages()

    def _add_notes_page_widget(self, title: str, text: str = ""):
        ed = QTextEdit()
        ed.setPlaceholderText("Session notes, quest log, treasure…")
        ed.setAcceptRichText(False)
        ed.setPlainText(text)
        ed._page_title = title
        ed.textChanged.connect(self._sync_notes_pages_to_char)
        self._notes_tabs.addTab(ed, title)
        return ed

    def _sync_notes_pages_to_char(self) -> None:
        pages = []
        for i in range(self._notes_tabs.count()):
            ed = self._notes_tabs.widget(i)
            if ed is None or ed is self._backstory_edit:
                continue
            pages.append({"title": getattr(ed, "_page_title", f"Page {i + 1}"),
                          "text": ed.toPlainText()})
        self.char["notes_pages"] = pages
        self._mark_dirty()

    def _add_notes_page(self) -> None:
        if self._notes_tabs.count() - 1 >= self._MAX_NOTES_PAGES:
            self._toast(f"Notes pages are capped at {self._MAX_NOTES_PAGES}")
            return
        title, ok = QInputDialog.getText(self, "New Notes Page", "Page name:")
        title = (title or "").strip()
        if not ok or not title:
            return
        ed = self._add_notes_page_widget(title)
        self._notes_tabs.setCurrentWidget(ed)
        self._sync_notes_pages_to_char()

    def _remove_notes_page(self, index: int) -> None:
        ed = self._notes_tabs.widget(index)
        if ed is None:
            return
        if ed is self._backstory_edit:
            self._toast("Backstory can't be removed")
            return
        if self._notes_tabs.count() - 1 <= 1:
            self._toast("Keep at least one notes page")
            return
        title = getattr(ed, "_page_title", "this page")
        reply = QMessageBox.question(
            self, "Remove Notes Page",
            f'Remove "{title}" and everything written on it? This can\'t be undone.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self._notes_tabs.removeTab(index)
        self._sync_notes_pages_to_char()

    def _rename_notes_page(self, index: int) -> None:
        ed = self._notes_tabs.widget(index)
        if ed is None or ed is self._backstory_edit:
            return
        old_title = getattr(ed, "_page_title", "")
        title, ok = QInputDialog.getText(self, "Rename Notes Page", "Page name:", text=old_title)
        title = (title or "").strip()
        if not ok or not title or title == old_title:
            return
        ed._page_title = title
        self._notes_tabs.setTabText(index, title)
        self._sync_notes_pages_to_char()

    # ════════════════════════════════════════════════════════════
    #  LOAD / REFRESH
    # ════════════════════════════════════════════════════════════
