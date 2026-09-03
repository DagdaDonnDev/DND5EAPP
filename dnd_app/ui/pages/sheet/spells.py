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
from dnd_app.ui.action_abilities import _append_cantrip_scaling_note
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


class SlotBar(QWidget):
    """One row of spell-slot squares for a given level.

    Squares are uniformly blue (INDIGO/IND2) — filled = slot available,
    hollow (outline only) = slot spent. Click a square to toggle it (handy
    for manually correcting state); casting a spell fills them in from the
    left automatically via set_used().
    """
    changed = Signal()

    def __init__(self, level, parent=None, color=None):
        super().__init__(parent)
        self.level = level; self._max = 0
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        lname = "Cantrip" if level==0 else ("Pact" if level==-1 else f"Level {level}")
        self._lbl_w = _lbl(lname, TEXT2, FS_SMALL, bold=True, wrap=False)
        self._lbl_w.setFixedWidth(68); lay.addWidget(self._lbl_w)
        self._bubble_lay = QHBoxLayout(); self._bubble_lay.setSpacing(5)
        lay.addLayout(self._bubble_lay); lay.addStretch()
        self._count_lbl = _lbl("0/0", TEXT3, FS_SMALL, wrap=False); lay.addWidget(self._count_lbl)
        self.bubbles = []
        self._color = color or INDIGO   # blue by default; pact magic uses purple

    def _style_square(self, cb: "QCheckBox"):
        accent = IND2 if self._color == INDIGO else (PURP2 if self._color == PURPLE else self._color)
        cb.setStyleSheet(
            f"QCheckBox::indicator{{width:18px;height:18px;border-radius:3px;"
            f"border:2px solid {self._color};background:{self._color};}}"
            f"QCheckBox::indicator:checked{{background:transparent;border:2px solid {accent};}}"
            f"QCheckBox::indicator:hover{{border-color:{accent};}}"
        )

    def set_max(self, n):
        self._max = n
        while len(self.bubbles) < n:
            cb = QCheckBox()
            cb.setFixedSize(20,20)
            cb.setToolTip(f"{self._lbl_w.text()} slot — click to toggle spent/available")
            self._style_square(cb)
            cb.stateChanged.connect(self.changed)
            self._bubble_lay.addWidget(cb); self.bubbles.append(cb)
        while len(self.bubbles) > n:
            cb = self.bubbles.pop()
            self._bubble_lay.removeWidget(cb); cb.setParent(None); cb.deleteLater()
        self.setVisible(n > 0)
        self._update_count()

    # NOTE: checkbox "checked" = SPENT (hollow square); unchecked = available (filled).
    def get_used(self): return sum(1 for b in self.bubbles if b.isChecked())
    def set_used(self, n):
        for i,b in enumerate(self.bubbles):
            b.blockSignals(True); b.setChecked(i < n); b.blockSignals(False)
        self._update_count()

    def reset(self):
        for b in self.bubbles: b.blockSignals(True); b.setChecked(False); b.blockSignals(False)
        self._update_count()

    def _update_count(self):
        used = self.get_used(); rem = self._max - used
        self._count_lbl.setText(f"{rem}/{self._max}")
        self._count_lbl.setStyleSheet(f"color:{TEAL2 if rem>0 else TEXT3};font-size:{FS_SMALL}px;background:transparent;")


# ═══════════════════════════════════════════════════════════════════
#  RESOURCE WIDGET — use/restore buttons
# ═══════════════════════════════════════════════════════════════════


class SpellsMixin:
    def _refresh_spell_row_titles(self):
        """Immersive Spells (optional rule): re-derive each spell row's
        title text on every controller-driven refresh, so it stays in
        sync with whatever triggered the change (transforming/reverting
        Wild Shape, Rage turning on/off via any of its several toggle
        paths, a level-up granting a Paladin Oath, or the setting itself
        being flipped on/off) without needing a hook at every one of
        those individual call sites."""
        if not self._spell_rows:
            return
        from dnd_app.ui.style.immersive_spells import compute_display_spell_title
        for row in self._spell_rows:
            row.set_display_name(compute_display_spell_title(self.char, row.spell))

    def _sync_slot_bars_from_char(self):
        """Sync slot-bar widgets from char's spell_slots_used data."""
        if not hasattr(self, "_slot_bars"):
            return
        from dnd_app.core.multiclass import compute_all_spell_slots
        from dnd_app.core.calculator import class_levels, subclasses
        slot_data = compute_all_spell_slots(class_levels(self.char), subclasses(self.char))
        slot_list = slot_data.get("spell_slots") or [0]*9   # index 0 = level 1
        # spell_slots_used is canonically a 9-element list (index 0 = level 1),
        # matching character.py's use_spell_slot()/recover_spell_slot()/long_rest().
        # Read defensively in case an older save has the legacy dict shape.
        used_raw = self.char.get("spell_slots_used", [0]*9)
        if isinstance(used_raw, dict):
            used_list = [used_raw.get(str(i), 0) for i in range(1, 10)]
            self.char["spell_slots_used"] = used_list   # self-heal on read
            used_raw = used_list
        for lvl, bar in self._slot_bars.items():
            idx = lvl - 1
            total = slot_list[idx] if 0 <= idx < len(slot_list) else 0
            used = used_raw[idx] if 0 <= idx < len(used_raw) else 0
            bar.set_max(total)
            bar.set_used(min(used, total))
        if hasattr(self, "_pact_bar"):
            from dnd_app.core.multiclass import get_warlock_slots
            from dnd_app.core.calculator import class_levels
            _wlvl = class_levels(self.char).get("Warlock", 0)
            _ps = get_warlock_slots(_wlvl) if _wlvl else {}
            _pact_max = _ps.get("count", 0)
            self._pact_bar.set_max(_pact_max)
            self._pact_bar.set_used(self.char.get("pact_slots_used", 0))
            if hasattr(self, "_pact_card"):
                self._pact_card.setVisible(_pact_max > 0)

    def _refresh_spells(self):
        """Update spell-tab slot bars, count labels and concentration state."""
        if not hasattr(self, "_slot_bars"):
            return
        try:
            self._sync_new_spell_rows()
        except Exception:
            pass
        try:
            self._remove_stale_spell_rows()
        except Exception:
            pass
        try:
            self._sync_slot_bars_from_char()
        except Exception:
            pass
        try:
            self._refresh_spell_count_labels()
        except Exception:
            pass
        try:
            self._refresh_concentration()
        except Exception:
            pass
        try:
            # Re-apply the browser's castable-level/class-list filter,
            # since the character's max castable spell level (and class
            # list) can change on level-up while the sheet is already open.
            self._filter_spell_browser()
        except Exception:
            pass

    def _remove_stale_spell_rows(self):
        """Remove any spell row whose spell is no longer in
        char['spells_known'] at all — the symmetric counterpart to
        _sync_new_spell_rows(), which only ever adds rows. Needed since
        a spell can become stale on its own (e.g. a Circle of the Land
        Druid switching terrain drops their old bonus spells from
        spells_known) with nothing but the manual ✕ button otherwise
        removing its row. This is a genuinely different case from what
        _sync_new_spell_rows() deliberately protects (in-progress edits
        on spells that are still validly known) — a spell that's not
        known at all anymore has nothing to preserve."""
        if not hasattr(self, "_spell_rows"):
            return
        known = set(self.char.get("spells_known", []))
        stale_rows = [r for r in self._spell_rows if r.spell.get("name") not in known]
        for row in stale_rows:
            self._remove_spell_row(row)

    def _sync_new_spell_rows(self):
        """Add a row for any spell in char['spells_known'] that isn't
        displayed yet — e.g. a full-list prepared caster (Cleric/Druid/
        Paladin/Artificer) gaining access to a new spell level on level-up,
        or a bonus spell (domain/oath/circle) becoming available. Never
        removes or rebuilds existing rows, so in-progress prepared/pin
        toggles the player has already set are left alone; a spell that's
        no longer eligible (e.g. switching Circle of the Land terrain) is
        cleaned up separately by the bonus-spell staleness check in
        builder.py, which also prunes it from spells_known itself."""
        if not hasattr(self, "_spell_rows"):
            return
        from dnd_app.data.phbCommon.spells import get_spell as _gs
        shown = {r.spell.get("name") for r in self._spell_rows}
        prepared_set = set(self.char.get("spells_prepared", []))
        for name in self.char.get("spells_known", []):
            if name in shown:
                continue
            sp = _gs(name)
            if sp:
                self._add_spell_row(sp, prepared=(name in prepared_set))
                shown.add(name)

    def _build_tab_spells(self):
        tab = QWidget(); root = QHBoxLayout(tab); root.setContentsMargins(16,16,16,16); root.setSpacing(16)

        # Left: slot tracker + spellcasting info
        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(8)

        # Per-class DC table
        dc_card = _card(PURPLE+"55"); dccl = QVBoxLayout(dc_card); dccl.setContentsMargins(14,12,14,14)
        dccl.addWidget(_lbl("SPELLCASTING", PURP2, FS_SMALL, bold=True))
        self._dc_table_lay = QGridLayout(); self._dc_table_lay.setSpacing(6)
        self._dc_table_lay.addWidget(_lbl("Class", TEXT3, FS_SMALL, bold=True), 0, 0)
        self._dc_table_lay.addWidget(_lbl("Ability", TEXT3, FS_SMALL, bold=True), 0, 1)
        self._dc_table_lay.addWidget(_lbl("Save DC", TEXT3, FS_SMALL, bold=True), 0, 2)
        self._dc_table_lay.addWidget(_lbl("Atk Bonus", TEXT3, FS_SMALL, bold=True), 0, 3)
        dccl.addLayout(self._dc_table_lay); ll.addWidget(dc_card)

        # Spell count summary card
        count_card = _card(PURPLE+"22"); cccl = QVBoxLayout(count_card)
        cccl.setContentsMargins(12,8,12,8); cccl.setSpacing(4)
        cccl.addWidget(_lbl("SPELLS KNOWN / PREPARED", PURP2, FS_SMALL, bold=True))
        self._spell_count_lbl = _lbl("", TEXT2, FS_SMALL, wrap=True)
        self._spell_count_lbl.setTextFormat(Qt.RichText)
        cccl.addWidget(self._spell_count_lbl)
        ll.addWidget(count_card)

        # Spell slots
        slots_card = _card(); sccl = QVBoxLayout(slots_card); sccl.setContentsMargins(14,12,14,14)
        sccl.addWidget(_lbl("SPELL SLOTS", GOLD, FS_SMALL, bold=True))
        self._slot_bars = {}
        for lvl in range(1,10):
            bar = SlotBar(lvl); bar.changed.connect(self._on_slot_change)
            sccl.addWidget(bar); self._slot_bars[lvl] = bar
        ll.addWidget(slots_card)

        # Pact Magic — mechanically distinct from normal spell slots (all
        # slots are the same level, recharge on a SHORT rest not long rest),
        # so it gets its own purple-accented card rather than blending into
        # the blue "SPELL SLOTS" list above.
        self._pact_card = _card(PURPLE+"55")
        pccl = QVBoxLayout(self._pact_card); pccl.setContentsMargins(14,12,14,14)
        pccl.addWidget(_lbl("PACT MAGIC  (recharges on a short rest)", PURP2, FS_SMALL, bold=True))
        self._pact_bar = SlotBar(-1, color=PURPLE); self._pact_bar.changed.connect(self._on_slot_change)
        pccl.addWidget(self._pact_bar)
        ll.addWidget(self._pact_card)
        self._pact_card.setVisible(False)   # hidden until refresh confirms Warlock levels

        # Metamagic quick-apply — lets a Sorcerer pick which known option(s)
        # to apply to their NEXT spell cast and spend the right Sorcery
        # Points, rather than only ever seeing Metamagic listed passively
        # in the Features tab with no way to actually use it.
        self._metamagic_card = _card(PURPLE+"55")
        mmcl = QVBoxLayout(self._metamagic_card); mmcl.setContentsMargins(14,12,14,14)
        mmcl.addWidget(_lbl("METAMAGIC — apply to next cast", PURP2, FS_SMALL, bold=True))
        self._metamagic_cbs = {}
        self._metamagic_box = QVBoxLayout(); self._metamagic_box.setSpacing(4)
        mmcl.addLayout(self._metamagic_box)
        mm_btn_row = QHBoxLayout()
        self._mm_apply_btn = QPushButton("Spend SP & Mark Active")
        self._mm_apply_btn.setStyleSheet(
            _btn("", PURPLE, variant="danger", radius=5, border_width=1,
                 text_color=PURP2, hover_text="white", font_size=FS_SMALL,
                 padding="4px 10px").styleSheet())
        self._mm_apply_btn.clicked.connect(self._apply_metamagic_selection)
        mm_btn_row.addWidget(self._mm_apply_btn)
        self._mm_active_lbl = _lbl("", TEAL2, FS_SMALL, bold=True, wrap=True)
        mm_btn_row.addWidget(self._mm_active_lbl, 1)
        mmcl.addLayout(mm_btn_row)
        ll.addWidget(self._metamagic_card)
        self._metamagic_card.setVisible(False)   # shown only if character knows any Metamagic

        # Concentration tracker
        conc_frame = QFrame()
        conc_frame.setStyleSheet(
            f"QFrame{{background:{SURF2};border:1px solid {qa(AMBER,0x55)};border-radius:8px;}}"
        )
        cf = QHBoxLayout(conc_frame)
        cf.setContentsMargins(12, 8, 12, 8)
        cf.setSpacing(10)
        cf.addWidget(_lbl("Concentrating:", AMBER, FS_BODY, bold=True, wrap=False))
        self._conc_lbl = _lbl("—", TEXT2, FS_BODY, wrap=True)
        self._conc_lbl.setMinimumWidth(120)
        self._conc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cf.addWidget(self._conc_lbl, 2)
        drop_btn = QPushButton("Drop")
        drop_btn.setFixedSize(64,30)
        drop_btn.setStyleSheet(
            _btn("", CRIMSON, variant="danger", border_width=1, bg_alpha=0x44,
                 text_color=CRIM2, hover_text="white", font_size=FS_SMALL,
                 padding="0px").styleSheet())
        drop_btn.clicked.connect(self._drop_concentration)
        cf.addWidget(drop_btn)
        self._conc_save_btn = QPushButton("Conc. Save")
        self._conc_save_btn.setFixedSize(90, 30)
        self._conc_save_btn.setStyleSheet(
            _btn("", AMBER, variant="danger", border_width=1, bg_alpha=0x44,
                 hover_text="white", font_size=FS_SMALL, padding="0px").styleSheet())
        self._conc_save_btn.clicked.connect(self._prompt_concentration_save)
        cf.addWidget(self._conc_save_btn)
        ll.addWidget(conc_frame)

        # Soul of Artifice (Artificer, 20th level): the "end an infusion
        # to drop to 1 HP instead of 0" half, alongside the +1-save
        # bonus. Buildable since active_infusions tracking exists.
        self._soul_artifice_btn = QPushButton("💫 Soul of Artifice: End an Infusion (drop to 1 HP)")
        self._soul_artifice_btn.setStyleSheet(
            _btn("", PURPLE, variant="danger", border_width=1, text_color=PURP2,
                 hover_text="white", font_size=FS_SMALL, padding="6px").styleSheet())
        self._soul_artifice_btn.clicked.connect(self._use_soul_of_artifice)
        self._soul_artifice_btn.setVisible(False)  # shown only for 20th-level Artificers
        ll.addWidget(self._soul_artifice_btn)
        ll.addStretch(); root.addWidget(left, 2)

        # Right: two tabs — My Spells | Spell Browser
        right = QTabWidget()
        # See base.py's _tabs for why this is needed -- QTabWidget ignores
        # a plain QSS "background" rule without it, leaving the strip
        # past the last tab showing the OS default background.
        right.setAttribute(Qt.WA_StyledBackground, True)
        right.setStyleSheet(
            f"QTabWidget::pane{{background:{SURF};border:1px solid {BORDER};border-radius:8px;}}"
            f"QTabBar::tab{{background:{SURF2};color:{TEXT2};padding:8px 18px;"
            f"font-size:{FS_SMALL}px;border:1px solid {BORDER};border-bottom:none;"
            f"border-radius:6px 6px 0 0;margin-right:2px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD2};font-weight:700;}}"
        )

        # ── My Spells tab ─────────────────────────────────────────────────────
        my_spells_w = QWidget(); mst_lay = QVBoxLayout(my_spells_w)
        mst_lay.setContentsMargins(8,8,8,8); mst_lay.setSpacing(6)
        mst_lay.addWidget(_lbl("MY SPELLS  [ ✓ = Prepared  |  ★ = Quick  |  right-click = Cast ]",
                               GOLD, FS_SMALL, bold=True))
        # Filter box: live-search your known/prepared spells by name
        self._my_sp_filter = QLineEdit()
        self._my_sp_filter.setPlaceholderText("🔍 Filter my spells…")
        self._my_sp_filter.setClearButtonEnabled(True)
        self._my_sp_filter.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:7px;"
            f"padding:6px 10px;color:{TEXT};font-size:{FS_BODY}px;}}")
        self._my_sp_filter.textChanged.connect(self._filter_my_spells)
        mst_lay.addWidget(self._my_sp_filter)

        my_sp_row2 = QHBoxLayout()
        self._my_sp_prepared_only = QCheckBox("Show only prepared spells")
        self._my_sp_prepared_only.setStyleSheet(
            f"QCheckBox{{color:{TEAL2};font-size:{FS_SMALL}px;font-weight:700;padding:2px;}}")
        self._my_sp_prepared_only.stateChanged.connect(lambda _s: self._filter_my_spells())
        my_sp_row2.addWidget(self._my_sp_prepared_only)
        my_sp_row2.addStretch()
        # Class filter — only meaningful (and only shown) for a multiclass
        # caster; a single-casting-class character has nothing to sort by.
        self._my_sp_class_f = QComboBox()
        self._my_sp_class_f.setStyleSheet(
            f"QComboBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:6px;"
            f"padding:4px 8px;color:{TEXT};font-size:{FS_SMALL}px;}}")
        self._my_sp_class_f.currentTextChanged.connect(lambda _t: self._filter_my_spells())
        self._my_sp_class_f.setVisible(False)  # shown once _refresh_my_spells_class_filter() finds 2+ classes
        my_sp_row2.addWidget(self._my_sp_class_f)
        mst_lay.addLayout(my_sp_row2)

        self._my_spells_scroll = QScrollArea(); self._my_spells_scroll.setWidgetResizable(True)
        self._my_spells_inner = QWidget(); self._my_spells_inner.setStyleSheet(f"background:{BG};")
        self._my_spells_lay = QVBoxLayout(self._my_spells_inner)
        self._my_spells_lay.setSpacing(4); self._my_spells_lay.setContentsMargins(2,2,2,2)
        self._my_spells_lay.addStretch()
        self._my_spells_scroll.setWidget(self._my_spells_inner)
        self._spell_rows = []; self._level_headers = {}
        mst_lay.addWidget(self._my_spells_scroll, 1)
        right.addTab(my_spells_w, "📖  My Spells")

        # ── Spell Browser tab ─────────────────────────────────────────────────
        browser_w = QWidget(); brl = QVBoxLayout(browser_w); brl.setContentsMargins(8,8,8,8); brl.setSpacing(6)
        browser_card = _card(); brcl = QVBoxLayout(browser_card); brcl.setContentsMargins(14,12,14,14)
        brcl.addWidget(_lbl("SPELL BROWSER", GOLD, FS_SMALL, bold=True))
        bt_row = QHBoxLayout(); bt_row.setSpacing(8)
        self._sp_search = QLineEdit(); self._sp_search.setPlaceholderText("Search 435 spells…")
        self._sp_cls_f  = QComboBox(); self._sp_cls_f.addItem("All Classes")
        for cn in ["Wizard","Cleric","Druid","Bard","Sorcerer","Warlock","Paladin","Ranger","Artificer"]:
            self._sp_cls_f.addItem(cn)
        self._sp_lvl_f = QComboBox(); self._sp_lvl_f.addItem("All Levels")
        for i in range(10): self._sp_lvl_f.addItem("Cantrip" if i==0 else f"Lv {i}")
        bt_row.addWidget(self._sp_search, 2); bt_row.addWidget(self._sp_cls_f); bt_row.addWidget(self._sp_lvl_f)
        brcl.addLayout(bt_row)
        # ── Homebrew toggle: OFF = class-list only + known-spell limits enforced
        self._sp_homebrew = QCheckBox("🔓 Homebrew mode — learn any spell, ignore spell limits")
        self._sp_homebrew.setAccessibleName("Homebrew mode: allow learning any spell and ignore spell limits")
        self._sp_homebrew.setToolTip(
            "Unchecked (default): the browser shows only spells on your classes' lists,\n"
            "and adding is blocked once you reach your spells-known / cantrip limits.\n"
            "Checked: every spell is visible and learnable with no cap.")
        self._sp_homebrew.setStyleSheet(
            f"QCheckBox{{color:{AMBE2};font-size:{FS_SMALL}px;font-weight:700;padding:2px;}}"
            f"QCheckBox::indicator{{width:16px;height:16px;border:2px solid {AMBER};"
            f"border-radius:4px;background:{SURF2};}}"
            f"QCheckBox::indicator:checked{{background:{AMBER};}}"
            f"QCheckBox:focus{{border:2px solid {TEAL2};border-radius:4px;}}")
        self._sp_homebrew.stateChanged.connect(lambda s: (
            self._filter_spell_browser(),
            self._toast("🔓 Homebrew learning ON — any spell, no limits" if s
                        else "🔒 Class lists & spell limits enforced")))
        brcl.addWidget(self._sp_homebrew)
        self._sp_browser = QListWidget()  # no height limit — tab gives full space
        self._sp_browser.setStyleSheet(f"QListWidget{{background:{BG};border:1px solid {BORDER};}}QListWidget::item{{padding:6px 10px;border-bottom:1px solid {BORDER};font-size:{FS_BODY}px;}}QListWidget::item:selected{{background:{INDIGO};color:white;}}")
        self._populate_spell_browser(); brcl.addWidget(self._sp_browser)
        add_btn = pill_btn("+ Add to My Spells", INDIGO); add_btn.clicked.connect(self._add_spell_from_browser)
        brcl.addWidget(add_btn); brl.addWidget(browser_card, 1)
        # Right-click context menu on browser
        self._sp_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self._sp_browser.customContextMenuRequested.connect(self._on_spell_browser_ctx)
        right.addTab(browser_w, "🔍  Spell Browser")

        self._sp_search.textChanged.connect(self._filter_spell_browser)
        self._sp_cls_f.currentTextChanged.connect(self._filter_spell_browser)
        self._sp_lvl_f.currentTextChanged.connect(self._filter_spell_browser)
        self._filter_spell_browser()   # apply class restriction on first view
        root.addWidget(right, 3)
        # My Spells is populated once by _load() right after all tabs finish
        # building (see CharacterSheet.__init__) — NOT here too. This used
        # to also call _populate_my_spells_from_char() at the end of tab
        # construction, which meant it ran twice on every single sheet
        # build; the first pass's widgets got removeWidget()'d but were
        # still scheduled (not yet actually deleted) when the second pass
        # repopulated, leaving stale orphaned spell-row/level-header labels
        # sitting at Qt's default un-laid-out geometry, visible on top of
        # the real content.
        return tab

    def _populate_my_spells_from_char(self):
        """(Re)build the My Spells list widgets from char['spells_known'].
        Called once at sheet construction and once whenever a different
        character is loaded into this sheet — NOT on every generic refresh,
        so in-progress prepared/pin toggles aren't clobbered mid-session."""
        if not hasattr(self, "_my_spells_lay"):
            return
        for row in list(self._spell_rows):
            self._my_spells_lay.removeWidget(row); row.setParent(None); row.deleteLater()
        for hdr in list(self._level_headers.values()):
            self._my_spells_lay.removeWidget(hdr); hdr.setParent(None); hdr.deleteLater()
        for hdr in list(getattr(self, "_class_level_headers", {}).values()):
            self._my_spells_lay.removeWidget(hdr); hdr.setParent(None); hdr.deleteLater()
        self._spell_rows = []
        self._level_headers = {}
        self._class_level_headers = {}
        from dnd_app.data.phbCommon.spells import get_spell as _gs
        prepared_set = set(self.char.get("spells_prepared", []))
        # Sort by class then level. _attribute_known_spells() is
        # intentionally scoped to only track "known spells" caps for
        # Sorcerer/Warlock/Bard/Ranger, so it can't be reused here — a
        # Wizard's (a prepared caster) leveled spells would never be
        # attributed to any class at all. This builds a dedicated
        # attribution instead, covering every known spell for every
        # caster type via _all_caster_classes() (which correctly
        # includes prepared casters).
        spell_to_class, class_order = self._compute_spell_class_attribution()
        def _sort_key(name):
            sp = _gs(name)
            lvl = sp.get("level", 0) if sp else 0
            cn = spell_to_class.get(name, "")
            cls_idx = class_order.index(cn) if cn in class_order else len(class_order)
            return (cls_idx, lvl, name)
        for name in sorted(self.char.get("spells_known", []), key=_sort_key):
            sp = _gs(name)
            if sp:
                self._add_spell_row(sp, prepared=(name in prepared_set))
        self._refresh_spell_count_labels()
        self._relayout_my_spells_by_class(spell_to_class, class_order)
        self._refresh_my_spells_class_filter(class_order)

    def _compute_spell_class_attribution(self):
        """{spell_name: class_name} for every entry in spells_known, plus
        the character's caster classes in creation order — the same
        attribution _populate_my_spells_from_char() uses for its class-
        then-level sort/headers and the My Spells class filter. Extracted
        so _add_spell_from_browser() can recompute it after adding a
        single new spell too, without a full list rebuild (which would
        clobber in-progress prepared/pin toggles elsewhere on the tab)."""
        from dnd_app.data.phbCommon.spells import get_spell as _gs
        all_classes = self._all_caster_classes()
        class_order = [c.get("class","") for c in self.char.get("classes", [])
                       if c.get("class","") in all_classes]
        spell_to_class = {}
        for name in self.char.get("spells_known", []):
            sp = _gs(name)
            sp_classes = set(sp.get("classes", [])) if sp else set()
            for cn in class_order:
                cn_bare = cn.split(" (")[0]  # "Fighter (EK)" -> "Fighter" for list matching
                if cn in sp_classes or cn_bare in sp_classes:
                    spell_to_class[name] = cn
                    break
            else:
                spell_to_class[name] = class_order[0] if class_order else ""
        return spell_to_class, class_order

    def _refresh_my_spells_class_filter(self, class_order):
        """(Re)populate the My Spells class-filter dropdown from the
        character's current caster classes, preserving the current
        selection across a refresh when it's still valid. Only shown for
        an actual multiclass caster — a single casting class has nothing
        to filter by."""
        combo = getattr(self, "_my_sp_class_f", None)
        if not combo:
            return
        combo.setVisible(len(class_order) > 1)
        if len(class_order) <= 1:
            return
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("All Classes")
        combo.addItems(class_order)
        idx = combo.findText(current)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _relayout_my_spells_by_class(self, spell_to_class, class_order):
        """Re-order the My Spells list into class-then-level groups with
        class-aware headers. A separate, additive pass after the normal
        row-adding process (rather than rewriting _add_spell_row's
        level-only header system) — that system is also used by the
        separate incremental sync path and is carefully written to avoid
        clobbering in-progress prepared/pin edits, so it's kept untouched;
        this only reorders widgets already built."""
        if not class_order:
            return
        for hdr in list(self._level_headers.values()):
            self._my_spells_lay.removeWidget(hdr); hdr.setParent(None); hdr.deleteLater()
        self._level_headers = {}
        self._class_level_headers = {}
        self._spell_row_class = {}
        rows_by_class_level = {}
        for row in self._spell_rows:
            self._my_spells_lay.removeWidget(row)
            cn = spell_to_class.get(row.spell.get("name",""), "")
            self._spell_row_class[row] = cn
            lvl = row.spell.get("level", 0)
            rows_by_class_level.setdefault((cn, lvl), []).append(row)
        lvl_names = ["Cantrips","1st Level","2nd Level","3rd Level","4th Level",
                     "5th Level","6th Level","7th Level","8th Level","9th Level"]
        insert_at = self._my_spells_lay.count() - 1  # before the trailing stretch
        for cn in class_order:
            cls_lvls = sorted({lvl for (c, lvl) in rows_by_class_level if c == cn})
            if not cls_lvls:
                continue
            cls_hdr = _lbl(cn, GOLD2, FS_BODY, bold=True)
            cls_hdr.setStyleSheet(cls_hdr.styleSheet() +
                f"border-bottom:2px solid {qa(GOLD2,0x66)};padding-bottom:4px;margin-top:12px;")
            self._my_spells_lay.insertWidget(insert_at, cls_hdr); insert_at += 1
            self._class_level_headers[(cn, "class")] = cls_hdr
            for lvl in cls_lvls:
                lvl_hdr = _lbl(lvl_names[min(lvl,9)], IND2, FS_SMALL, bold=True)
                lvl_hdr.setStyleSheet(lvl_hdr.styleSheet() +
                    f"border-bottom:1px solid {qa(IND2,0x33)};padding-bottom:2px;margin-top:4px;")
                self._my_spells_lay.insertWidget(insert_at, lvl_hdr); insert_at += 1
                self._class_level_headers[(cn, lvl)] = lvl_hdr
                for row in rows_by_class_level[(cn, lvl)]:
                    self._my_spells_lay.insertWidget(insert_at, row); insert_at += 1

    def _populate_spell_browser(self):
        self._sp_browser.clear()
        for s in ALL_SPELLS:
            lvl_txt = "Ctrp" if s["level"]==0 else f"L{s['level']}"
            conc = " ©" if s.get("concentration") else ""
            rit  = " ®" if s.get("ritual") else ""
            text = f"{lvl_txt:4s}  {s['name']}{conc}{rit}  [{s['school'][:3]}]"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, s)
            item.setToolTip(self._spell_tooltip_text(s))
            self._sp_browser.addItem(item)

    @staticmethod
    def _spell_progression_tables():
        """Single source of truth for spells-known / cantrips-known
        progression tables, shared by the summary display, the learn-gate,
        and the multiclass attribution logic below — kept as one copy so
        the three call sites can never drift out of sync with each
        other."""
        SPELLS_KNOWN = {
            "Bard":     {1:4,2:5,3:6,4:7,5:8,6:9,7:10,8:11,9:12,10:14,11:15,12:15,
                         13:16,14:18,15:19,16:19,17:20,18:22,19:22,20:22},
            "Sorcerer": {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,12:12,
                         13:13,14:13,15:14,16:14,17:15,18:15,19:15,20:15},
            "Warlock":  {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:10,11:11,12:11,
                         13:12,14:12,15:13,16:13,17:14,18:14,19:15,20:15},
            "Ranger":   {1:0,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6,10:6,11:7,12:7,
                         13:8,14:8,15:9,16:9,17:10,18:10,19:11,20:11},
        }
        CANTRIPS = {
            "Wizard":   {1:3,4:4,10:5},
            "Cleric":   {1:3},
            "Druid":    {1:2,6:3,11:4},
            "Bard":     {1:2,4:3,10:4},
            "Sorcerer": {1:4,4:5,10:6},
            "Warlock":  {1:2,4:3,10:4},
            "Artificer":{1:2},
        }
        EK_AT = {3:3,4:4,7:5,8:6,10:7,11:8,13:9,14:10,16:11,19:12,20:13}
        PREPARE_AB = {"Wizard":"INT","Cleric":"WIS","Druid":"WIS","Paladin":"CHA","Artificer":"INT"}
        return SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB

    def _all_caster_classes(self):
        """{class_name: (cantrip_max, leveled_max_or_None)} for EVERY class
        that grants cantrips and/or known spells. leveled_max is None for
        prepared casters (Wizard/Cleric/Druid/Paladin/Artificer) — they
        don't have a 'known' leveled-spell cap, they prepare a subset of
        their full list daily (tracked separately via spells_prepared).
        Cantrips work the same way for every class though, so they're
        covered here regardless of prepared vs. known."""
        SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB = self._spell_progression_tables()
        out = {}
        for c in self.char.get("classes", []):
            cname, lvl = c.get("class",""), c.get("level",0)
            sub = c.get("subclass","").lower()
            cant_max = max((v for k,v in CANTRIPS.get(cname,{}).items() if k<=lvl), default=0)
            if cname in SPELLS_KNOWN:
                lvl_max = max((v for k,v in SPELLS_KNOWN[cname].items() if k<=lvl), default=0)
                out[cname] = (cant_max, lvl_max)
            elif cname == "Fighter" and "eldritch knight" in sub:
                lvl_max = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                out["Fighter (EK)"] = (2 + (1 if lvl>=10 else 0), lvl_max)
            elif cname == "Rogue" and "arcane trickster" in sub:
                lvl_max = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                out["Rogue (AT)"] = (2 + (1 if lvl>=10 else 0), lvl_max)
            elif cname in PREPARE_AB:
                out[cname] = (cant_max, None)
        return out

    def _known_spell_classes(self):
        """{class_name: (cantrip_max, leveled_max)} for classes that track
        their OWN known-LEVELED-spells list (Bard, Sorcerer, Warlock,
        Ranger, EK Fighter, AT Rogue) — i.e. _all_caster_classes() minus
        the prepared casters, who don't have a known-spells cap at all."""
        return {cn: (c, l) for cn, (c, l) in self._all_caster_classes().items()
                if l is not None}

    def _attribute_known_spells(self):
        """Partition char['spells_known'] into per-class buckets.

        5e multiclass spellcasting (PHB p.164): each class's spells-known
        is a COMPLETELY SEPARATE pool — a Sorcerer/Warlock doesn't share
        one combined list, and spell slots being shared (multiclass slot
        table) doesn't change that, so a pooled total shown against EACH
        class's own cap would both mis-split multiclass casters and let
        one class's spells count against another's limit. Cantrips are
        attributed across EVERY casting class (prepared casters included,
        since cantrips are
        always "known" regardless of prepared/known spellcasting style);
        leveled spells are only attributed across classes with a genuine
        known-spells pool.

        When a known spell is on more than one of the character's own
        eligible class lists (a genuine overlap), it's assigned to
        whichever eligible class currently has the most room left
        relative to its own cap, keeping the split balanced rather than
        one class eating the other's allowance by list order alone.

        Returns: {class_name: {'cantrips': [...], 'leveled': [...]}}
        """
        from dnd_app.data.phbCommon.spells import get_spell as _gs
        all_classes = self._all_caster_classes()
        known_classes = self._known_spell_classes()
        buckets = {cn: {"cantrips": [], "leveled": []} for cn in all_classes}
        if not all_classes:
            return buckets

        def _real_name(cn):
            return "Wizard" if cn in ("Fighter (EK)", "Rogue (AT)") else cn

        # Racial/subclass bonus spells (Fairy's Druidcraft, a Cleric
        # domain spell, etc.) are merged into spells_known so they're
        # castable, but they're always-known freebies, not a pick that
        # should eat into a class's own known-spells/cantrip cap — so
        # this loop excludes anything in char["bonus_spells"] before
        # counting entries against a class's cap.
        bonus = set(self.char.get("bonus_spells", []))
        # A prepared caster's (Cleric/Druid/Paladin/Artificer) own
        # full-list access dumps its entire available spell list into the
        # same flat spells_known — a leveled spell there belongs to that
        # class, not to a known-caster class's own pick, even when the
        # name also happens to be on that known-caster's spell list (e.g.
        # "Silence" is both Cleric and Bard). Without this exclusion a
        # Cleric's own domain access got silently counted as "Bard
        # learned it", inflating the Bard's known-spell count/cap.
        from dnd_app.core.builder import full_list_dumped_spell_names
        full_dumped = set()
        for names in full_list_dumped_spell_names(self.char).values():
            full_dumped.update(names)
        for name in self.char.get("spells_known", []):
            if name in bonus:
                continue
            sp = _gs(name)
            if not sp: continue
            is_cantrip = sp.get("level", 1) == 0
            if not is_cantrip and name in full_dumped:
                continue
            sp_classes = set(sp.get("classes", []))
            pool = all_classes if is_cantrip else known_classes
            eligible = [cn for cn in pool if _real_name(cn) in sp_classes]
            eligible = list(dict.fromkeys(eligible)) or list(pool.keys())
            if not eligible:
                continue
            if len(eligible) == 1:
                target = eligible[0]
            else:
                def _room(cn):
                    cant_max, lvl_max = all_classes[cn]
                    bucket = buckets[cn]["cantrips"] if is_cantrip else buckets[cn]["leveled"]
                    cap = cant_max if is_cantrip else (lvl_max if lvl_max is not None else 999)
                    return cap - len(bucket)
                target = max(eligible, key=_room)
            buckets[target]["cantrips" if is_cantrip else "leveled"].append(name)
        return buckets

    def _refresh_spellcasting_table(self):
        """Populate the 'Class | Ability | Save DC | Atk Bonus' table.

        This table's HEADER existed but nothing ever populated a data row —
        spell save DC and attack bonus were completely invisible in the UI
        for every character, single-class or multiclass.

        5e multiclass spellcasting (PHB p.164): a spell's save DC and attack
        bonus use the spellcasting ability of the class it was learned
        from — a Sorcerer/Wizard doesn't have one shared DC, it has a
        separate DC for its Sorcerer spells (CHA) and its Wizard spells
        (INT). So this is genuinely one row per casting class, not one
        pooled row for the whole character.
        """
        if not hasattr(self, "_dc_table_lay"): return
        from dnd_app.core.calculator import get_prof_bonus, ability_mod as _am
        from dnd_app.data.phb2014.classes import CLASS_DICT

        # Clear any existing data rows. QGridLayout has no removeRow(), so
        # track our own row widgets instead — rebuilt fresh on every refresh.
        # setParent(None) (not just deleteLater()) matters here: this table
        # gets refreshed more than once in a single _load() pass (once via
        # _refresh_spells(), again via _populate_my_spells_from_char()), and
        # deleteLater() alone only *schedules* eventual destruction — it
        # doesn't stop the widget from still being part of the tree (and
        # visible) in between. setParent(None) detaches it immediately.
        lay = self._dc_table_lay
        for w in getattr(self, "_dc_row_widgets", []):
            lay.removeWidget(w); w.setParent(None); w.deleteLater()
        self._dc_row_widgets = []

        pb = get_prof_bonus(self.char)
        row_i = 1
        for c in self.char.get("classes", []):
            cname, lvl = c.get("class",""), c.get("level",0)
            sub = c.get("subclass","").lower()
            ability = CLASS_DICT.get(cname, {}).get("spell_ability")
            display_name = cname
            if cname == "Fighter" and "eldritch knight" in sub:
                ability, display_name = "INT", "Fighter (EK)"
            elif cname == "Rogue" and "arcane trickster" in sub:
                ability, display_name = "INT", "Rogue (AT)"
            if not ability:
                continue   # non-casting class (or subclass without spells yet)
            mod = _am(self.char, ability)
            dc = 8 + pb + mod
            atk = pb + mod
            atk_str = f"+{atk}" if atk >= 0 else str(atk)
            dc_lbl  = _lbl(str(dc), GOLD2, FS_SMALL, bold=True, wrap=False)
            atk_lbl = _lbl(atk_str, TEAL2, FS_SMALL, bold=True, wrap=False)
            dc_lbl.setToolTip("Right-click for a breakdown")
            atk_lbl.setToolTip("Right-click for a breakdown")
            dc_lbl.contextMenuEvent = (lambda e, _a=ability, _dc=dc:
                self._show_breakdown_popup(f"{_a} Save DC",
                    get_save_dc_breakdown(self.char, _a), str(_dc), e.globalPos()))
            atk_lbl.contextMenuEvent = (lambda e, _a=ability, _atk=atk_str:
                self._show_breakdown_popup(f"{_a} Spell Attack Bonus",
                    get_spell_attack_breakdown(self.char, _a), _atk, e.globalPos()))
            cells = [
                _lbl(display_name, TEXT, FS_SMALL, bold=True, wrap=False),
                _lbl(ability, TEXT2, FS_SMALL, wrap=False),
                dc_lbl,
                atk_lbl,
            ]
            for col, w in enumerate(cells):
                lay.addWidget(w, row_i, col)
                self._dc_row_widgets.append(w)
            row_i += 1

        if row_i == 1:
            hint = _lbl("No spellcasting classes.", TEXT3, FS_SMALL, wrap=False)
            lay.addWidget(hint, row_i, 0, 1, 4)
            self._dc_row_widgets.append(hint)

    def _refresh_spell_count_labels(self):
        """Show how many spells and cantrips each class can currently know/prepare.
        Multiclass known-spell casters (Sorcerer/Warlock, Bard/Warlock, etc.)
        are tracked SEPARATELY per class and summed additively for the total —
        never pooled into one shared count checked against every class's cap."""
        if not hasattr(self, "_spell_count_lbl"): return
        from dnd_app.core.character import ability_mod as _am
        char = self.char
        SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB = self._spell_progression_tables()
        attributed = self._attribute_known_spells()
        prepared_attributed = self._attribute_prepared_spells()
        lines = []
        for c in char.get("classes",[]):
            cname = c["class"]; lvl = c["level"]
            sub = c.get("subclass","").lower()
            ctbl = CANTRIPS.get(cname,{})
            cmax = max((v for k,v in ctbl.items() if k<=lvl), default=0)
            is_ek = cname=="Fighter" and "eldritch knight" in sub
            is_at = cname=="Rogue" and "arcane trickster" in sub
            if is_ek or is_at:
                # EK/AT aren't in the CANTRIPS table (it's keyed by full
                # caster class names) — they get 2 cantrips at 3rd level,
                # 3 at 10th, same formula used in _known_spell_classes().
                cmax = 2 + (1 if lvl >= 10 else 0)
            # This class's OWN attributed spells only — not the whole
            # character's flat spells_known list.
            bucket_key = ("Fighter (EK)" if cname=="Fighter" and "eldritch knight" in sub
                         else "Rogue (AT)" if cname=="Rogue" and "arcane trickster" in sub
                         else cname)
            my_bucket = attributed.get(bucket_key, {"cantrips":[], "leveled":[]})
            cur_cantrips = len(my_bucket["cantrips"])
            cur_noncant  = len(my_bucket["leveled"])
            cantrip_line = (f"  <span style='color:{TEXT3};'>Cantrips: {cur_cantrips}/{cmax}</span>" if cmax else "")
            if cname in SPELLS_KNOWN:
                tbl = SPELLS_KNOWN[cname]
                best = max((v for k,v in tbl.items() if k<=lvl), default=0)
                lines.append(f"<b>{cname} Lv{lvl}</b>: {cur_noncant}/{best} spells known{cantrip_line}")
            elif cname == "Fighter" and "eldritch knight" in sub:
                best = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                lines.append(f"<b>EK Fighter Lv{lvl}</b>: {cur_noncant}/{best} spells{cantrip_line}")
            elif cname == "Rogue" and "arcane trickster" in sub:
                best = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                lines.append(f"<b>AT Rogue Lv{lvl}</b>: {cur_noncant}/{best} spells{cantrip_line}")
            elif cname in PREPARE_AB:
                ab = PREPARE_AB[cname]
                mod = _am(char, ab)
                eff = lvl if cname not in ("Paladin","Artificer") else max(1, lvl//2)
                max_prep = max(1, mod + eff)
                cur_prep = len(prepared_attributed.get(cname, []))
                lines.append(f"<b>{cname} Lv{lvl}</b>: {cur_prep}/{max_prep} prepared"
                              f"<span style='color:{TEXT3};'> ({ab}+lvl)</span>{cantrip_line}")
        self._spell_count_lbl.setText("<br>".join(lines) if lines else "No spellcasting classes.")
        self._refresh_spell_class_badges()
        self._refresh_spellcasting_table()
        self._refresh_metamagic_card()

    @staticmethod
    def _parse_sp_cost(option_text: str) -> tuple[int | None, bool]:
        """Parse a Metamagic option's SP cost. Returns (fixed_cost_or_None,
        is_per_spell_level) — e.g. 'spend 2 SP' -> (2, False), 'spend SP
        equal to spell level' -> (None, True)."""
        import re
        if "equal to spell level" in option_text.lower():
            return None, True
        m = re.search(r'spend (\d+) SP', option_text)
        return (int(m.group(1)) if m else 1), False

    def _refresh_metamagic_card(self):
        """Rebuild the Metamagic quick-apply checkboxes from the character's
        actually-known options (never the full pool), and show/hide the
        whole card based on whether they know any at all."""
        if not hasattr(self, "_metamagic_card"):
            return
        known = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
        self._metamagic_card.setVisible(bool(known))
        if hasattr(self, "_soul_artifice_btn"):
            from dnd_app.core.calculator import class_levels
            self._soul_artifice_btn.setVisible(class_levels(self.char).get("Artificer", 0) >= 20)
        while self._metamagic_box.count():
            item = self._metamagic_box.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._metamagic_cbs = {}
        for opt in known:
            name = opt.split("–")[0].strip()
            cost, per_level = self._parse_sp_cost(opt)
            cost_str = "SP = spell level" if per_level else f"{cost} SP"
            cb = QCheckBox(f"{name}  ({cost_str})")
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_SMALL}px;}}")
            cb.setToolTip(opt)
            self._metamagic_box.addWidget(cb)
            self._metamagic_cbs[opt] = cb
        self._mm_active_lbl.setText("")

    def _apply_metamagic_selection(self):
        """Spend Sorcery Points for whichever Metamagic checkboxes are
        selected and mark them active for the next cast. Doesn't simulate
        each option's mechanical effect (that varies per spell/target) —
        it handles the concrete, common part: paying the SP cost and
        tracking what's active so the player (and the cast confirmation)
        can see it."""
        selected = [opt for opt, cb in self._metamagic_cbs.items() if cb.isChecked()]
        if not selected:
            self._toast("Select at least one Metamagic option first")
            return
        sp_res = next((r for r in self.char.get("resources", [])
                       if r.get("key") == "sorcery_points"), None)
        if not sp_res:
            self._toast("No Sorcery Points resource found")
            return
        total_cost = 0
        per_level_opts = []
        for opt in selected:
            cost, per_level = self._parse_sp_cost(opt)
            if per_level:
                per_level_opts.append(opt.split("–")[0].strip())
            else:
                total_cost += cost
        available = sp_res.get("current", 0)
        if total_cost > available:
            self._toast(f"🔒 Not enough Sorcery Points ({available} available, "
                        f"{total_cost} needed for fixed-cost options)")
            return
        sp_res["current"] = available - total_cost
        active_names = [opt.split("–")[0].strip() for opt in selected]
        self.char["_active_metamagic"] = active_names
        note = f"Active for next cast: {', '.join(active_names)}"
        if per_level_opts:
            note += f"  ({', '.join(per_level_opts)} costs SP = the slot level you cast at)"
        self._mm_active_lbl.setText(note)
        self._toast(f"✓ Spent {total_cost} SP — {', '.join(active_names)} active for your next cast")
        if hasattr(self, "_refresh_action_tabs"): self._refresh_action_tabs()
        self._mark_dirty()

    def _refresh_spell_class_badges(self):
        """Show a small class-source badge (SORC/LOCK/etc.) on each spell
        row when the character has 2+ known-spell classes, so a multiclass
        caster can see at a glance which pool each spell counts against.
        Single-class casters never see this — nothing to disambiguate."""
        if not hasattr(self, "_spell_rows"):
            return
        known_classes = self._known_spell_classes()
        if len(known_classes) < 2:
            for row in self._spell_rows:
                row.set_class_tag(None)
            return
        attributed = self._attribute_known_spells()
        owner = {}
        for cn, buckets in attributed.items():
            for name in buckets["cantrips"] + buckets["leveled"]:
                owner[name] = cn
        for row in self._spell_rows:
            row.set_class_tag(owner.get(row.spell.get("name")))

    def _refresh_quick_spells(self):
        """Quick spells now live in the Action tab via _refresh_action_tabs.
        This method is kept so callers don't crash; it delegates to the full refresh."""
        if hasattr(self, '_action_tabs'):
            self._refresh_action_tabs()

    def _on_spell_browser_ctx(self, pos):
        """Right-click on spell browser — show full details."""
        item = self._sp_browser.itemAt(pos)
        if not item: return
        spell_name = item.text().strip()
        from dnd_app.data.phbCommon.spells import get_spell
        spell = get_spell(spell_name)
        if not spell: return
        from PySide6.QtWidgets import QMenu, QDialog, QVBoxLayout, QScrollArea, QWidget, QLabel, QDialogButtonBox
        menu = QMenu(self)
        detail_act = menu.addAction(f"📖  Details: {spell_name}")
        add_act    = menu.addAction(f"+ Add to My Spells")
        action = menu.exec(self._sp_browser.viewport().mapToGlobal(pos))
        if action == detail_act:
            s = spell
            lvl_txt = "Cantrip" if s.get("level",0)==0 else f"Level {s['level']}"
            desc = s.get("desc") or s.get("description","")
            higher = s.get("higher_levels","") or s.get("higher","")
            detail = (f"<b>{s['name']}</b> [{lvl_txt} {s.get('school','').title()}]<br>"
                      f"<i>Cast:</i> {s.get('casting_time',s.get('cast_time','—'))} &nbsp;"
                      f"<i>Range:</i> {s.get('range','—')} &nbsp;"
                      f"<i>Duration:</i> {s.get('duration','—')}<br>"
                      f"<i>Components:</i> {s.get('components','—')}<br><br>"
                      f"{desc}" + (f"<br><br><i>At Higher Levels:</i> {higher}" if higher else ""))
            dlg = QDialog(self); dlg.setWindowTitle(s['name']); dlg.setMinimumWidth(520)
            lay = QVBoxLayout(dlg)
            lbl = QLabel(detail); lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size:13px;padding:8px;")
            sa = QScrollArea(); sa.setWidgetResizable(True)
            inner = QWidget(); il = QVBoxLayout(inner); il.addWidget(lbl)
            sa.setWidget(inner); lay.addWidget(sa)
            bb = QDialogButtonBox(QDialogButtonBox.Close)
            bb.rejected.connect(dlg.reject); lay.addWidget(bb); dlg.exec()
        elif action == add_act:
            self._add_spell_from_browser()

    def _filter_spell_browser(self):
        q  = self._sp_search.text().lower()
        cl = self._sp_cls_f.currentText()
        lv = self._sp_lvl_f.currentText()
        homebrew = self._sp_homebrew.isChecked()
        max_castable = None if homebrew else self._max_castable_spell_level()
        for i in range(self._sp_browser.count()):
            item = self._sp_browser.item(i); sp = item.data(Qt.UserRole)
            if not sp: continue
            ok = not q or q in sp["name"].lower()
            if cl != "All Classes": ok = ok and cl in sp.get("classes",[])
            if not homebrew:
                mine = self._char_spell_classes()
                if mine: ok = ok and bool(set(sp.get("classes",[])) & mine)
                # Hide leveled spells above what the character can currently
                # cast — unless Homebrew mode is on, matching the "+ Add"
                # button's own castable-level gate so the browser doesn't
                # show spells it would then refuse to add.
                if max_castable is not None and sp.get("level", 0) > max_castable:
                    ok = False
            if lv != "All Levels":
                ok = ok and ((lv=="Cantrip" and sp["level"]==0) or
                             (lv.startswith("Lv") and sp["level"]==int(lv[3:])))
            item.setHidden(not ok)

    def _char_spell_classes(self) -> set:
        """Class spell-lists this character can learn from (EK/AT → Wizard)."""
        out = set()
        for c in self.char.get("classes", []):
            cn = c.get("class",""); sub = c.get("subclass","").lower()
            if cn in ("Wizard","Cleric","Druid","Bard","Sorcerer","Warlock",
                      "Paladin","Ranger","Artificer"):
                out.add(cn)
            if cn == "Fighter" and "eldritch knight" in sub: out.add("Wizard")
            if cn == "Rogue"   and "arcane trickster" in sub: out.add("Wizard")
        return out

    def _spell_caps(self):
        """(cantrip_max, leveled_max_or_None) POOLED across all casting
        classes — kept only as a coarse "could this possibly fit anywhere"
        check for UI hints. Actual per-spell gating in
        _add_spell_from_browser uses _all_caster_classes()/
        _attribute_known_spells() for genuine per-class caps instead of
        this pooled total, since 5e multiclass spellcasting never actually
        shares one combined known-spells pool."""
        all_classes = self._all_caster_classes()
        cant_max = sum(c for c, l in all_classes.values())
        leveled_vals = [l for c, l in all_classes.values() if l is not None]
        lvl_max = sum(leveled_vals) if leveled_vals else 0
        prepared_only = bool(all_classes) and not leveled_vals
        return cant_max, (None if prepared_only else lvl_max)

    def _max_castable_spell_level(self) -> int:
        """Highest spell level the character can currently cast, combining
        ordinary spell slots and Warlock Pact Magic — the two are tracked
        completely separately in the character data, so checking only one
        would wrongly block (or wrongly allow) a pure-Warlock or
        multiclass Warlock character."""
        max_lvl = 0
        for i, count in enumerate(self.char.get("spell_slots_max", [])):
            if count > 0:
                max_lvl = i + 1
        if self.char.get("pact_slots_max", 0) > 0:
            max_lvl = max(max_lvl, self.char.get("pact_slot_level", 0))
        return max_lvl

    def _add_spell_from_browser(self):
        homebrew = self._sp_homebrew.isChecked()
        my_classes = self._char_spell_classes()
        from dnd_app.data.phbCommon.spells import get_spell as _gs

        def _real_name(cn):
            return "Wizard" if cn in ("Fighter (EK)", "Rogue (AT)") else cn

        for item in self._sp_browser.selectedItems():
            sp = item.data(Qt.UserRole)
            if not sp or any(r.spell["name"]==sp["name"] for r in self._spell_rows):
                continue
            name = sp["name"]
            if not homebrew:
                # Gate 1: must be on one of your classes' lists — OR added
                # to that list by a racial Mark (Mark of Shadow/Detection/
                # Storm expand the spell list itself, per their real text,
                # rather than granting a spell directly).
                from dnd_app.data.phbCommon.spells import get_mark_expanded_spells
                mark_spells = get_mark_expanded_spells(self.char)
                if my_classes and name not in mark_spells and not (set(sp.get("classes",[])) & my_classes):
                    self._toast(f"🔒 {name} isn't on your class spell lists "
                                f"— enable Homebrew mode to learn it")
                    continue
                # Gate 2: spell level can't exceed what you can actually
                # cast yet — a 1st-level Wizard has no business learning a
                # 3rd-level spell just because it's on the Wizard list.
                # Cantrips (level 0) are always castable, so this only
                # applies to leveled spells.
                sp_level = sp.get("level", 0)
                if sp_level > 0:
                    max_lvl = self._max_castable_spell_level()
                    if sp_level > max_lvl:
                        self._toast(f"🔒 {name} is a level {sp_level} spell — you can only "
                                    f"cast up to level {max_lvl} right now "
                                    f"— enable Homebrew mode to exceed it")
                        continue
                # Gate 3: per-class spells-known / cantrip caps. Recomputed
                # fresh each spell (not hoisted out of the loop) so adding
                # spell N correctly affects the room-check for spell N+1 —
                # multiclass casters have SEPARATE pools per class, so a
                # Sorcerer/Warlock can't "borrow" the other's headroom.
                all_classes = self._all_caster_classes()
                is_cantrip = sp.get("level", 0) == 0
                sp_classes = set(sp.get("classes", []))
                pool = all_classes if is_cantrip else self._known_spell_classes()
                eligible = [cn for cn in pool if _real_name(cn) in sp_classes]
                if pool and not eligible:
                    # On your class list overall (Gate 1 passed) but none of
                    # your KNOWN-spell classes can take it — e.g. a spell
                    # that's only on a prepared caster's list for this
                    # character. No "known" cap applies to that; let it through.
                    eligible = []
                if eligible:
                    attributed = self._attribute_known_spells()
                    def _room(cn):
                        cant_max, lvl_max = all_classes[cn]
                        bucket = attributed.get(cn, {"cantrips":[], "leveled":[]})
                        used = len(bucket["cantrips"]) if is_cantrip else len(bucket["leveled"])
                        cap = cant_max if is_cantrip else lvl_max
                        return (cap if cap is not None else 999) - used
                    best_cn = max(eligible, key=_room)
                    if _room(best_cn) <= 0:
                        cap_shown = all_classes[best_cn][0 if is_cantrip else 1]
                        used_shown = cap_shown - _room(best_cn) if cap_shown is not None else "?"
                        kind = "Cantrip" if is_cantrip else "Spells-known"
                        self._toast(f"🔒 {kind} limit reached for {_real_name(best_cn)} "
                                    f"({used_shown}/{cap_shown}) — enable Homebrew mode to exceed it")
                        continue
            if name not in self.char.get("spells_known", []):
                self.char.setdefault("spells_known",[]).append(name)
            row = self._add_spell_row(sp)
            # Full-list prepared casters (Cleric/Druid/Paladin/Artificer)
            # don't have a separate "learn a spell" step at all in the real
            # rules — their entire class list is always available, and
            # preparing IS the only choice. Auto-prepare here rather than
            # making the player click Add and then separately check
            # Prepared for the same spell. Wizard is deliberately excluded:
            # it's also a prepared caster, but real Wizards are limited to
            # whatever's in their spellbook, so the "add" step here still
            # means something distinct from "prepare" for them.
            _, _, _, PREPARE_AB = self._spell_progression_tables()
            full_list_classes = {c for c in PREPARE_AB if c != "Wizard"}
            if sp.get("level", 0) > 0 and full_list_classes & set(sp.get("classes", [])) & my_classes:
                self._on_prep_toggled(row, True)
        self._refresh_spell_count_labels()
        # Newly added rows have no _spell_row_class entry yet (that's only
        # set by the class-then-level relayout below) — without this, the
        # My Spells class filter would incorrectly hide a spell just
        # added, since its attributed class reads as "" until the next
        # full character reload. Recomputing + relaying out is safe here
        # (unlike _populate_my_spells_from_char, it only repositions
        # widgets and doesn't touch prepared/pin state).
        spell_to_class, class_order = self._compute_spell_class_attribution()
        self._relayout_my_spells_by_class(spell_to_class, class_order)
        self._refresh_my_spells_class_filter(class_order)
        self._mark_dirty()

    def _filter_my_spells(self, text: str = None):
        """Live-filter the My Spells list; hides non-matching rows and
        empty headers. Also applies the "show only prepared" toggle and
        the caster-class filter, alongside class-then-level sorting."""
        q = (text if text is not None else self._my_sp_filter.text()).strip().lower()
        prepared_only = getattr(self, "_my_sp_prepared_only", None)
        prepared_only = prepared_only.isChecked() if prepared_only else False
        class_f = getattr(self, "_my_sp_class_f", None)
        class_f = class_f.currentText() if class_f and class_f.isVisible() else "All Classes"
        any_filter = bool(q) or prepared_only or class_f != "All Classes"
        visible = {}  # (class, level) -> True if any matching row is visible there
        for row in self._spell_rows:
            name = row.spell.get("name", "").lower()
            cn = self._spell_row_class.get(row, "") if hasattr(self, "_spell_row_class") else ""
            text_match = (q in name) if q else True
            prep_match = (not prepared_only) or row.is_prepared()
            class_match = (class_f == "All Classes") or (cn == class_f)
            match = text_match and prep_match and class_match
            row.setVisible(match)
            if match:
                visible[(cn, row.spell.get("level", 0))] = True
                visible[(cn, "class")] = True
        for lvl, hdr in self._level_headers.items():
            hdr.setVisible(True if not any_filter else any(
                k[1] == lvl for k in visible))
        for key, hdr in getattr(self, "_class_level_headers", {}).items():
            hdr.setVisible(True if not any_filter else visible.get(key, False))

    def _prepared_caster_caps(self) -> dict:
        """{class_name: cap} for each prepared-casting class the character
        has (Wizard/Cleric/Druid: ability mod + class level; Paladin/
        Artificer: ability mod + half class level, rounded down), each with
        a minimum of 1. Per-class, NOT pooled — 5e multiclass spellcasting
        gives each prepared-caster class its own separate prepared-spell
        allotment (PHB p.164, same principle as spells-known being
        per-class for Sorcerer/Bard/Warlock/Ranger). Preparing a Cleric
        spell should never eat into a Druid's separate allotment on the
        same character, or vice versa."""
        from dnd_app.core.character import ability_mod
        _, _, _, PREPARE_AB = self._spell_progression_tables()
        caps = {}
        for c in self.char.get("classes", []):
            cname, lvl = c.get("class",""), c.get("level",0)
            if cname not in PREPARE_AB or lvl <= 0:
                continue
            mod = ability_mod(self.char, PREPARE_AB[cname])
            level_term = (lvl // 2) if cname in ("Paladin", "Artificer") else lvl
            caps[cname] = max(1, mod + level_term)
        return caps

    def _attribute_prepared_spells(self) -> dict:
        """Partition char['spells_prepared'] into per-class buckets, the
        same way _attribute_known_spells() does for spells_known. Only
        ordinary leveled spells count (cantrips and bonus/domain/circle
        spells are always-available and don't draw from any class's
        prepared allotment). When a prepared spell is on more than one of
        the character's own prepared-caster class lists, it's assigned to
        whichever eligible class currently has the most room left, keeping
        the split balanced rather than one class's list winning by order.

        Returns: {class_name: [spell_name, ...]}
        """
        from dnd_app.data.phbCommon.spells import get_spell as _gs
        caps = self._prepared_caster_caps()
        buckets = {cn: [] for cn in caps}
        if not caps:
            return buckets
        bonus = set(self.char.get("bonus_spells", []))
        for name in self.char.get("spells_prepared", []):
            if name in bonus:
                continue
            sp = _gs(name)
            if not sp or sp.get("level", 0) == 0:
                continue
            sp_classes = set(sp.get("classes", []))
            eligible = [cn for cn in caps if cn in sp_classes]
            if not eligible:
                continue
            if len(eligible) == 1:
                target = eligible[0]
            else:
                target = max(eligible, key=lambda cn: caps[cn] - len(buckets[cn]))
            buckets[target].append(name)
        return buckets

    def _on_prep_toggled(self, row, checked: bool):
        """Sync a spell row's prepared checkbox to char['spells_prepared'],
        enforcing each prepared-caster class's OWN cap on the way in —
        not a single total pooled across every prepared-caster class the
        character has. 5e multiclass spellcasting gives each prepared-
        caster class its own separate prepared-spell allotment; a Cleric/
        Druid character preparing 5 Cleric spells shouldn't have any less
        room left for Druid spells as a result, and vice versa."""
        name = row.spell.get("name", "")
        prepared = self.char.setdefault("spells_prepared", [])
        if not checked:
            if name in prepared:
                prepared.remove(name)
            self._refresh_spell_count_labels()
            self._mark_dirty()
            return
        if name in prepared:
            return
        # Cantrips and class-granted bonus spells (domain/oath/circle
        # spells) don't count against any prepared cap — only ordinary
        # leveled spells the player is actively choosing to prepare do.
        if row.spell.get("level", 0) > 0 and name not in self.char.get("bonus_spells", []):
            caps = self._prepared_caster_caps()
            sp_classes = set(row.spell.get("classes", []))
            eligible = [cn for cn in caps if cn in sp_classes]
            if eligible:
                attributed = self._attribute_prepared_spells()
                target = max(eligible, key=lambda cn: caps[cn] - len(attributed.get(cn, [])))
                current = len(attributed.get(target, []))
                cap = caps[target]
                if current >= cap:
                    row.set_prepared(False)
                    self._toast(f"🔒 {target}'s prepared spell limit reached ({current}/{cap}) "
                                f"— unprepare another {target} spell first")
                    return
        prepared.append(name)
        self._refresh_spell_count_labels()
        self._mark_dirty()

    def _add_spell_row(self, spell, prepared=False):
        lvl = spell["level"]
        is_bonus = spell["name"] in self.char.get("bonus_spells", [])
        if lvl == 0:
            prepared = True   # Cantrips are always available — no prep needed (PHB p.201)
            # Show the actual current damage for a scaling cantrip rather
            # than making the player do the 5/11/17 math themselves — on a
            # COPY, since `spell` is the shared global spell-database dict.
            resolved_desc = _append_cantrip_scaling_note(spell["name"], spell.get("desc",""), self.char)
            if resolved_desc != spell.get("desc",""):
                spell = {**spell, "desc": resolved_desc}
        elif is_bonus:
            prepared = True   # Feat/racial/class bonus spells are always available too
        if lvl not in self._level_headers:
            names = ["Cantrips","1st Level","2nd Level","3rd Level","4th Level",
                     "5th Level","6th Level","7th Level","8th Level","9th Level"]
            hdr = _lbl(names[min(lvl,9)], IND2, FS_SMALL, bold=True)
            hdr.setStyleSheet(hdr.styleSheet() + f"border-bottom:2px solid {qa(IND2,0x44)};padding-bottom:4px;margin-top:8px;")
            self._level_headers[lvl] = hdr
            ins = self._find_hdr_pos(lvl)
            self._my_spells_lay.insertWidget(ins, hdr)
        from dnd_app.ui.style.immersive_spells import compute_display_spell_title
        row = SpellRow(spell, prepared, locked=is_bonus,
                        display_name=compute_display_spell_title(self.char, spell))
        from dnd_app.core.calculator import can_ritual_cast
        row.set_can_ritual(can_ritual_cast(self.char, spell))
        row.remove.connect(self._remove_spell_row)
        row.cast.connect(self._cast_spell)
        row.cast_ritual.connect(self._cast_spell_as_ritual)
        row.toggle_quick.connect(self._on_spell_quick_toggle)
        row.prepared_toggled.connect(self._on_prep_toggled)
        # Restore pinned state
        if spell["name"] in self.char.get("quick_spells",[]):
            row.set_pinned(True)
        ins = self._find_spell_pos(lvl)
        self._my_spells_lay.insertWidget(ins, row)
        self._spell_rows.append(row)
        return row

    def _on_spell_quick_toggle(self, spell_name: str, pinned: bool):
        qs = self.char.setdefault("quick_spells",[])
        if pinned and spell_name not in qs: qs.append(spell_name)
        elif not pinned and spell_name in qs: qs.remove(spell_name)
        # Sync star state on all matching spell rows
        for row in self._spell_rows:
            if row.spell.get("name") == spell_name:
                row.set_pinned(pinned)
        # (_refresh_action_tabs runs once at the end of this method)
        self._mark_dirty()

    def _find_hdr_pos(self, level):
        for i in range(self._my_spells_lay.count()):
            w = self._my_spells_lay.itemAt(i).widget()
            if w in self._level_headers.values():
                lv = next(k for k,v in self._level_headers.items() if v==w)
                if lv > level: return i
        return self._my_spells_lay.count()-1

    def _find_spell_pos(self, level):
        for i in range(self._my_spells_lay.count()-1,-1,-1):
            w = self._my_spells_lay.itemAt(i).widget()
            if isinstance(w,SpellRow) and w.spell["level"]<=level: return i+1
            if w in self._level_headers.values():
                lv = next(k for k,v in self._level_headers.items() if v==w)
                if lv==level: return i+1
        return self._my_spells_lay.count()-1

    def _remove_spell_row(self, row):
        lvl = row.spell["level"]
        name = row.spell["name"]
        self._spell_rows.remove(row)
        self._my_spells_lay.removeWidget(row); row.setParent(None); row.deleteLater()
        if name in self.char.get("spells_known",[]): self.char["spells_known"].remove(name)
        if name in self.char.get("spells_prepared",[]): self.char["spells_prepared"].remove(name)
        if name in self.char.get("quick_spells",[]): self.char["quick_spells"].remove(name)
        if not any(r.spell["level"]==lvl for r in self._spell_rows):
            if lvl in self._level_headers:
                h = self._level_headers.pop(lvl)
                self._my_spells_lay.removeWidget(h); h.setParent(None); h.deleteLater()
        # Was missing: the known/prepared count label never updated on removal,
        # so it looked like the spell was still "counted" even after deletion.
        self._refresh_spell_count_labels()
        self._mark_dirty()

    def _spell_tooltip_text(self, spell: dict) -> str:
        from dnd_app.ui.shared import _spell_tooltip
        text = _spell_tooltip(spell)
        # Agonizing Blast (Eldritch Invocation): the shared tooltip builder
        # has no character context to know about this, so append it here.
        if spell.get("name") == "Eldritch Blast":
            has_agonizing = any("agonizing blast" in i.lower()
                                 for i in self.char.get("eldritch_invocations", []))
            if has_agonizing:
                mod = ability_mod(self.char, _detect_spell_ability(self.char) or "CHA")
                text += f"\n\nAgonizing Blast: each beam deals 1d10{sign(mod)} force."
        return text

    def _has_beast_spells(self) -> bool:
        """Beast Spells (Druid, 18th level) is a Druid class-level
        threshold, not total character level — checks the character's
        actual Druid class level, correctly handling a multiclass Druid
        who hasn't reached 18 Druid levels even if their total
        character level is higher."""
        for c in self.char.get("classes", []):
            if c.get("class") == "Druid" and c.get("level", 0) >= 18:
                return True
        return False

    def _cast_spell_as_ritual(self, spell):
        """Cast a spell as a ritual — no spell slot expended, but it takes
        10 minutes longer than the spell's normal casting time (PHB
        p.201-202)."""
        if self.char.get("_wildshape_active") and not self._has_beast_spells():
            self._toast(f"\U0001f43e Can't cast {spell['name']} while Wild Shaped — "
                        f"revert to your normal form first")
            return
        block_reason = spell_component_block_reason(self.char, spell)
        if block_reason:
            self._toast(f"🔇 Can't cast {spell['name']} — {block_reason}")
            return
        base_time = spell.get("casting_time", spell.get("cast_time", "1 action"))
        self._toast(f"📜 Cast {spell['name']} as a ritual — no spell slot used, "
                    f"but casting time is {base_time} + 10 minutes.")
        self._mark_dirty()

    def _cast_spell(self, spell):
        if self.char.get("_wildshape_active") and not self._has_beast_spells():
            self._toast(f"\U0001f43e Can't cast {spell['name']} while Wild Shaped — "
                        f"revert to your normal form first")
            return
        block_reason = spell_component_block_reason(self.char, spell)
        if block_reason:
            self._toast(f"🔇 Can't cast {spell['name']} — {block_reason}")
            return
        lvl = spell["level"]
        is_cantrip = (lvl == 0)
        ct = (spell.get("cast_time") or "1 action").strip().lower()
        bucket = {"1 action": "Action", "bonus action": "Bonus Action",
                  "reaction": "Reaction"}.get(ct)
        # Gate checked up front, before any slot is expended — including
        # for cantrips, since a cantrip cast via bonus action (Shillelagh,
        # or a bonus-action-granting feature like Earth Genasi's Blade
        # Ward) can still be blocked if a leveled spell was already cast
        # via the regular Action that turn.
        if bucket in ("Action", "Bonus Action") and not self._check_bonus_action_spell_rule(is_cantrip, bucket):
            self._toast(f"✖ Can't cast {spell['name']} via {bucket} — casting a spell with a "
                        f"bonus action means the only other spell you can cast this turn is a "
                        f"cantrip")
            return
        if is_cantrip:
            # Cantrips don't expend a slot, but still cost the same
            # action-economy resource as any other spell (most have a
            # 1-action cast time), so this can't return early before
            # that's consumed.
            self._mark_spell_cast_time(spell)
            self._toast(f"✨ Cast {spell['name']} (cantrip — at will)")
            return
        for l in range(lvl, 10):
            bar = self._slot_bars.get(l)
            if bar and bar._max > 0 and bar.get_used() < bar._max:
                bar.set_used(bar.get_used() + 1)
                bar._update_count()
                self._on_slot_change()
                if spell.get("concentration"):
                    start_concentration(self.char, spell["name"])
                    self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
                    self._refresh_concentration()
                self._apply_spell_active_effect(spell)
                self._mark_spell_cast_time(spell)
                self._toast(f"✨ Cast {spell['name']} — slot expended")
                return
        if self._pact_bar._max > 0 and self._pact_bar.get_used() < self._pact_bar._max:
            self._pact_bar.set_used(self._pact_bar.get_used() + 1)
            self._pact_bar._update_count()
            self._on_slot_change()
            if spell.get("concentration"):
                start_concentration(self.char, spell["name"])
                self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
                self._refresh_concentration()
            self._apply_spell_active_effect(spell)
            self._mark_spell_cast_time(spell)
            # A little flavor for Warlocks specifically -- Pact Magic is
            # power borrowed from your patron, unlike an ordinary prepared
            # or known spell slot, so spending one gets its own tiny nod.
            self._toast(f"✨ Cast {spell['name']} — pact slot expended\nYour patron approves.")
            self._mark_dirty()
            return
        self._toast(f"🔒 Can't cast {spell['name']} — no level-{lvl}+ spell slots available")

    def _check_bonus_action_spell_rule(self, is_cantrip: bool, bucket: str) -> bool:
        """The real rule: casting a spell with a bonus action means the
        only other spell castable that turn is a cantrip with a 1-action
        cast time — and this is symmetric regardless of cast order.
        Correctly covers the Earth Genasi Blade Ward case: even though
        Blade Ward is itself a cantrip, casting it via a bonus-action-
        granting feature still counts as "casting a spell with a bonus
        action," which requires whatever was cast via the regular Action
        that turn to also be a cantrip — a leveled spell like Fireball
        violates that regardless of which slot came first."""
        from dnd_app.core.effects import has_extra_action
        if has_extra_action(self.char):
            return True
        if bucket == "Bonus Action":
            if self._action_spell_is_cantrip is False:
                return False
        elif bucket == "Action" and not is_cantrip:
            if self._bonus_action_spell_is_cantrip is not None:
                return False
        return True

    def _mark_spell_cast_time(self, spell):
        """Feeds casting a spell into the same turn-economy tracker used
        by other abilities (including the Haste extra-action case).
        Maps the spell's real cast_time to the correct bucket, and
        skips the tracker entirely for longer, out-of-combat casting
        times that don't fit the per-turn economy at all."""
        ct = (spell.get("cast_time") or "1 action").strip().lower()
        is_cantrip = spell.get("level", 1) == 0
        if ct == "1 action":
            self._mark_turn_used("Action")
            self._action_spell_is_cantrip = is_cantrip
        elif ct == "bonus action":
            self._mark_turn_used("Bonus Action")
            self._bonus_action_spell_is_cantrip = is_cantrip
        elif ct == "reaction":
            self._mark_turn_used("Reaction")

    def _action_cat_btn_style(self, active: bool, small: bool = False) -> str:
        fs = FS_TINY if small else FS_SMALL
        pad = "2px 8px" if small else "3px 12px"
        if active:
            return (f"QPushButton{{background:{GOLD};color:{BG};border:1px solid {GOLD};"
                    f"border-radius:5px;font-size:{fs}px;font-weight:700;padding:{pad};}}")
        return (f"QPushButton{{background:{SURF2};color:{TEXT2};border:1px solid {qa(AMBER,0x33)};"
                f"border-radius:5px;font-size:{fs}px;font-weight:600;padding:{pad};}}"
                f"QPushButton:hover{{background:{qa(AMBER,0x22)};color:{AMBE2};}}")

    def _classify_action_entry(self, entry):
        """Racial trait entries reliably use the character's own base
        race name as their source, so matching against that is
        accurate. Magic Item is a deliberate placeholder until that
        system is properly wired — it currently classifies nothing
        rather than guess inaccurately from arbitrary source-name
        text."""
        source = entry[2] if len(entry) > 2 else ""
        is_spell = len(entry) > 3 and entry[3] is not None
        if is_spell:
            return "Spell"
        if source and source == self.char.get("race", ""):
            return "Race"
        return "Common"

    def _apply_spell_active_effect(self, spell):
        """Connects casting a spell to the active_effects system (Haste,
        Bless, Shield of Faith, dozens more with real mechanical hooks)
        so the player doesn't have to separately, manually re-add the
        same effect through a dropdown after casting it. Self-only
        spells auto-apply with no ambiguity. Spells with a real range
        prompt for self-vs-another, since these buff spells can target
        either, and only adding it to the caster's own sheet is correct
        when they're the actual target."""
        from dnd_app.core.effects import EFFECT_TABLE
        name = spell["name"]
        if name not in EFFECT_TABLE:
            return
        rng = (spell.get("range") or "").strip().lower()
        is_self_only = rng == "self" or rng.startswith("self (") or rng.startswith("self(")
        if is_self_only:
            target_self = True
        else:
            reply = QMessageBox.question(
                self, name, f"Cast {name} on yourself, or on another creature?\n\n"
                f"(Choose \"No\" if targeting someone else — it won't be added to your own "
                f"Active Effects.)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            target_self = (reply == QMessageBox.Yes)
        if target_self:
            fx = self.char.setdefault("active_effects", [])
            if name not in fx:
                fx.append(name)
                self.ctrl.refresh()
                self._refresh_effects_list()
                self._apply_turn_state()
                self._toast(f"☄ {name} added to Active Effects")

    def _drop_concentration(self):
        drop_concentration(self.char)
        self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
        self._refresh_concentration()

    def _prompt_concentration_save(self):
        if not self.char.get("concentration", {}).get("spell"):
            QMessageBox.information(self, "Concentration", "Not concentrating on a spell.")
            return
        dmg, ok = QInputDialog.getInt(self, "Concentration Save", "Damage taken this turn:", 10, 0, 999)
        if not ok:
            return
        roll, ok_roll = QInputDialog.getInt(
            self, "Concentration Save",
            "Enter your d20 roll (CON modifier applied automatically):",
            10, 1, 30,
        )
        if not ok_roll:
            return
        from dnd_app.core.calculator import get_saving_throw_bonus
        dc = max(10, dmg // 2)
        total = roll + get_saving_throw_bonus(self.char, "CON")
        if total >= dc:
            QMessageBox.information(self, "Concentration", f"Maintained ({total} vs DC {dc})")
        else:
            drop_concentration(self.char)
            self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
            QMessageBox.warning(self, "Concentration", f"Failed ({total} vs DC {dc}) — concentration dropped.")
            self._toast("Your focus shatters like cheap glass.")
        self._refresh_concentration()
        self._mark_dirty()

    def _refresh_concentration(self):
        spell = self.char.get("concentration", {}).get("spell")
        if spell:
            self._conc_lbl.setText(spell)
            self._conc_lbl.setToolTip(spell)
            self._conc_lbl.setStyleSheet(
                f"color:{AMBER};font-size:{FS_BODY}px;font-weight:700;background:transparent;"
            )
        else:
            self._conc_lbl.setText("—")
            self._conc_lbl.setToolTip("")
            self._conc_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_BODY}px;background:transparent;")
        if hasattr(self, "_combat_conc_lbl"):
            if spell:
                self._combat_conc_lbl.setText(f"🎯 Concentrating: {spell}")
                self._combat_conc_lbl.setToolTip(f"{spell} — manage/drop concentration from the Spells tab.")
                self._combat_conc_lbl.setVisible(True)
            else:
                self._combat_conc_lbl.setVisible(False)

    def _on_slot_change(self):
        self.char["spell_slots_used"] = [self._slot_bars[i].get_used() for i in range(1, 10)]
        self.char["pact_slots_used"] = self._pact_bar.get_used()
        self._mark_dirty()

    # ══ TAB 5: FEATURES ════════════════════════════════════════════════════════
