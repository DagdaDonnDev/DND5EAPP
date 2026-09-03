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
from dnd_app.ui.dialogs.rest import (_all_relevant_choice_ids, _prune_stale_choices,
    RACE_SCOPED_CHOICE_IDS, BACKGROUND_SCOPED_CHOICE_IDS)
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


class ChoicesMixin:
    def _on_add_xp(self):
        """Add the entered amount to the running XP total — the normal
        end-of-session workflow (add whatever the DM awarded), as opposed
        to _on_set_total_xp which overwrites the total outright for
        corrections/imports."""
        amount = self._xp_add_spin.value()
        if amount <= 0:
            return
        new_total = self.char.get("experience", 0) + amount
        self.ctrl.update("experience", new_total, rebuild_char=False)
        self._xp_add_spin.setValue(0)
        self._mark_dirty()
        from dnd_app.core.character import xp_progress
        prog = xp_progress(self.char)
        if prog["eligible"]:
            due = prog["levels_due"]
            suffix = "ready to level up!" if due <= 1 else f"ready to level up ×{due}!"
            self._toast(f"🌟 +{amount:,} XP — {suffix}")
        else:
            self._toast(f"+{amount:,} XP")

    def _on_set_total_xp(self):
        current = self.char.get("experience", 0)
        new_val, ok = QInputDialog.getInt(
            self, "Set Total XP", "Total experience points:", current, 0, 999999999, 1)
        if ok:
            self.ctrl.update("experience", new_val, rebuild_char=False)
            self._mark_dirty()

    def _edit_identity(self, slot: str):
        """Edit a character identity field (race/subrace/ancestry/background)."""
        from dnd_app.core.builder import rebuild
        from dnd_app.core.calculator import update_all
        if slot == "race":
            from dnd_app.data.phb2014.races import RACE_NAMES
            name, ok = QInputDialog.getItem(self, "Edit Race", "Species / Race:", RACE_NAMES, 0, False)
            if ok and name:
                old_race = self.char.get("race", "")
                if name != old_race:
                    # Race-scoped choice ids are keyed generically by
                    # choice TYPE ("race_skill_profs" etc.), not by which
                    # race — cleared before the rebuild below so a picked
                    # skill/tool/language from the OLD race doesn't get
                    # silently misapplied to whatever the NEW race's own
                    # (possibly completely different) choice pool is, and
                    # the new race's own pending choice actually re-prompts
                    # instead of looking "already answered".
                    _prune_stale_choices(self.char, RACE_SCOPED_CHOICE_IDS)
                self.ctrl.update_many({"race": name, "species": name, "subrace": ""})
                self._refresh_stat_bar()
                self._edit_identity("subrace")

        elif slot == "subrace":
            from dnd_app.data.phb2014.races import RACE_DICT
            import re as _re
            race = self.char.get("race", "")
            rdata = RACE_DICT.get(race, {})
            subraces_raw = rdata.get("subraces", [])
            if not subraces_raw:
                QMessageBox.information(self, "No Subraces", f"{race} has no subraces."); return
            _ASI_PAT = r"[+]([A-Z]{3})[ ](\d+)"
            _STRIP_PAT = r"[+][A-Z]{3}[ ]\d+,?[ ]*"
            options = []
            for sub_str in subraces_raw:
                name_part = sub_str.split("(")[0].strip()
                inner = sub_str[sub_str.find("(")+1:sub_str.rfind(")")]
                asis = ", ".join(f"{ab}+{n}" for ab, n in _re.findall(_ASI_PAT, inner))
                extra = _re.sub(_STRIP_PAT, "", inner).strip().strip(",").strip()
                desc = asis + (f"  ·  {extra[:50]}" if extra else "")
                options.append(f"{name_part}  ({desc})")
            current = self.char.get("subrace", "")
            cur_idx = next((i for i, o in enumerate(options) if o.startswith(current)), 0)
            choice, ok = QInputDialog.getItem(self, f"Choose Subrace — {race}", "Subrace:", options, cur_idx, False)
            if ok and choice:
                subrace_name = choice.split("(")[0].strip()
                self.char["subrace"] = subrace_name
                rebuild(self.char); update_all(self.char)
                self.ctrl.refresh()
                self._refresh_stat_bar()
                self._rebuild_features()
                self._mark_dirty()

        elif slot == "ancestry":
            if self.char.get("race", "") != "Dragonborn": return
            from dnd_app.data.phb2014.races import DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE
            subrace = self.char.get("subrace", "Standard") or "Standard"
            avail = ANCESTRY_BY_SUBRACE.get(subrace, ANCESTRY_BY_SUBRACE.get("Standard", []))
            options = [f"{a}  –  {DRACONIC_ANCESTRY[a][0]}, {DRACONIC_ANCESTRY[a][1]}" for a in avail]
            cur = self.char.get("draconic_ancestry", "")
            cur_idx = next((i for i, o in enumerate(options) if o.startswith(cur)), 0)
            choice, ok = QInputDialog.getItem(self, "Draconic Ancestry", "Dragon type:", options, cur_idx, False)
            if ok and choice:
                self.char["draconic_ancestry"] = choice.split("–")[0].strip().split("  ")[0].strip()
                self._rebuild_features()
                self._refresh_stat_bar()
                self._mark_dirty()

        elif slot == "background":
            from dnd_app.data.phbCommon.backgrounds import BACKGROUND_NAMES, get_background
            name, ok = QInputDialog.getItem(self, "Edit Background", "Background:", BACKGROUND_NAMES, 0, False)
            if ok and name:
                old_bg = self.char.get("background", "")
                if name != old_bg:
                    # Same reasoning as the race-scoped clear above: bg_skill_profs/
                    # bg_tool_profs/bg_languages are shared, generic ids used by
                    # whichever background currently needs a choice, not
                    # namespaced per background name.
                    _prune_stale_choices(self.char, BACKGROUND_SCOPED_CHOICE_IDS)
                self.ctrl.update("background", name)
                # Changing background here needs the same follow-up
                # prompts the creation wizard already runs for backgrounds
                # that grant a choice of feat (Rewarded/Ruined and others).
                bg = get_background(name)
                feat_choices = (bg or {}).get("feat_choices") or []
                if feat_choices:
                    feat_name, ok2 = QInputDialog.getItem(
                        self, name, f"{name} grants a choice of feat — which one?",
                        feat_choices, 0, False)
                    if ok2 and feat_name:
                        feats = self.char.setdefault("feats", [])
                        if feat_name not in feats:
                            feats.append(feat_name)
                self._mark_dirty()

    def _populate_subclass_combo(self):
        """Rebuild subclass combo boxes in the choices tab class card."""
        from dnd_app.data.phb2014.classes import CLASS_DICT
        from dnd_app.core.character import set_subclass

        # Target the class card layout in choices tab
        target = getattr(self, '_subclass_area_card', self._subclass_area)
        # Clear existing — blockSignals on all old combos before deletion
        for combo in list(self._subclass_combos.values()):
            combo.blockSignals(True)
        while target.count():
            item = target.takeAt(0)
            if item.widget():
                item.widget().blockSignals(True)
                item.widget().deleteLater()
        self._subclass_combos.clear()

        classes = self.char.get("classes", [])
        for cls_entry in classes:
            cname     = cls_entry.get("class", "")
            clvl      = cls_entry.get("level", 1)
            current   = cls_entry.get("subclass", "")
            cdata     = CLASS_DICT.get(cname, {})
            subs      = cdata.get("subclasses", [])
            sub_level = cdata.get("subclass_level", 3)

            col = QWidget()
            cl  = QVBoxLayout(col); cl.setContentsMargins(0,0,0,0); cl.setSpacing(2)
            cl.addWidget(_lbl(f"{cname} subclass:", TEXT3, FS_TINY, bold=True))

            from dnd_app.core.character import clean_subclass_name
            combo = QComboBox()
            combo.addItem("— (none chosen) —", "")
            for sub_str in subs:
                display = clean_subclass_name(sub_str)
                combo.addItem(display, display)

            # Set current — compare canonicalized on both sides so a value
            # stored with (or without) a source tag / dash summary still matches.
            current_clean = clean_subclass_name(current)
            cur_idx = next((i for i in range(combo.count())
                            if combo.itemData(i) == current_clean), 0)
            combo.setCurrentIndex(cur_idx)
            combo.setEnabled(clvl >= sub_level)
            combo.setToolTip(f"Unlocked at level {sub_level}" if clvl < sub_level
                             else f"{cname} subclass — choose your path")
            combo.setStyleSheet(
                f"QComboBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
                f"color:{TEXT};font-size:{FS_SMALL}px;padding:3px 6px;}}"
                f"QComboBox:focus{{border-color:{INDIGO};}}")

            def _on_change(idx, cn=cname, cb=combo):
                val = cb.itemData(idx) or ""
                # Diff relevant choice ids before/after the subclass swap
                # and clear anything no longer relevant — subclass-scoped
                # choice ids (rune_knight_runes, kensei_weapons, lunar_phase,
                # guidance_of_the_spirits_skill, ...) are each named for
                # their specific subclass, so switching away from Rune
                # Knight to Battle Master, say, would otherwise leave the
                # old chosen runes permanently stuck with no way to ever
                # pick differently, and no re-prompt for the new subclass's
                # own choices.
                from dnd_app.core.builder import rebuild as _rebuild
                from dnd_app.core.calculator import update_all as _update_all
                old_ids = _all_relevant_choice_ids(self.char)
                set_subclass(self.char, cn, val)
                new_ids = _all_relevant_choice_ids(self.char)
                _prune_stale_choices(self.char, old_ids - new_ids)
                _rebuild(self.char); _update_all(self.char)
                self.ctrl.refresh()
                self._rebuild_features()
                self._refresh_stat_bar()
                self._mark_dirty()

            combo.currentIndexChanged.connect(_on_change)
            self._subclass_combos[cname] = combo
            cl.addWidget(combo)
            target.addWidget(col)

    def _build_tab_choices(self):
        """Choices tab: Class Manager + Identity cards in a top pane, the
        LevelUpPanel (choices) and Optional Class Features in a bottom pane —
        split by a draggable handle, same pattern as the Combat tab, so a
        character with few pending choices doesn't leave a large empty
        gap with no way to reclaim that space."""
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(f"QSplitter::handle{{background:{qa(AMBER,0x33)};height:4px;"
                              f"border-radius:2px;margin:2px 40%;}}"
                              f"QSplitter::handle:hover{{background:{AMBER};}}")

        top_half = QWidget()
        layout = QVBoxLayout(top_half)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Class Manager card ────────────────────────────────────────────────
        cls_card = QFrame()
        cls_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {qa(INDIGO,0x44)};border-radius:10px;}}")
        cls_cl = QVBoxLayout(cls_card)
        cls_cl.setContentsMargins(12, 8, 12, 8); cls_cl.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        title_row.addWidget(_lbl("⚔  CLASS & LEVEL", INDIGO, FS_SMALL, bold=True))
        title_row.addStretch()
        # Class action buttons
        for label, fn, color, tip in [
            ("⬆ Level Up / Multiclass", self._open_level_up_or_multiclass, GOLD,
             "Gain a level in an existing class, or add a new one"),
            ("⬇ Level Down",      self._open_level_down,      CRIMSON,"Remove one level"),
            ("✕ Remove Class",    self._open_remove_class,    CRIMSON,"Remove an entire class (multiclass only)"),
        ]:
            b = _btn(label, color, variant="chip", height=28, font_size=FS_TINY, tooltip=tip)
            b.clicked.connect(fn)
            title_row.addWidget(b)
        cls_cl.addLayout(title_row)

        # Subclass selectors — one per active class
        self._subclass_area_card = QHBoxLayout(); self._subclass_area_card.setSpacing(8)
        cls_cl.addLayout(self._subclass_area_card)
        self._subclass_combos = {}

        layout.addWidget(cls_card)

        # ── Experience Points card — only visible in XP leveling mode
        # (Settings → Advancement); populated/hidden by _refresh_xp_tracker,
        # which also drives the header's XP pill from the same data. ──────
        self._xp_card = QFrame()
        self._xp_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(GOLD,0x44)};border-radius:10px;}}")
        xp_cl = QVBoxLayout(self._xp_card); xp_cl.setContentsMargins(12, 8, 12, 8); xp_cl.setSpacing(6)

        xp_title_row = QHBoxLayout()
        xp_title_row.addWidget(_lbl("🌟  EXPERIENCE", GOLD2, FS_SMALL, bold=True))
        xp_title_row.addStretch()
        self._xp_total_lbl = _lbl("0 XP", GOLD2, FS_SMALL, bold=True)
        xp_title_row.addWidget(self._xp_total_lbl)
        xp_cl.addLayout(xp_title_row)

        self._xp_bar = QProgressBar(); self._xp_bar.setRange(0, 100); self._xp_bar.setValue(0)
        self._xp_bar.setTextVisible(False); self._xp_bar.setFixedHeight(8)
        self._xp_bar.setStyleSheet(
            f"QProgressBar{{background:{SURF2};border:none;border-radius:4px;}}"
            f"QProgressBar::chunk{{border-radius:4px;background:{GOLD};}}")
        xp_cl.addWidget(self._xp_bar)

        self._xp_status_lbl = _lbl("", TEXT3, FS_SMALL, bold=True)
        xp_cl.addWidget(self._xp_status_lbl)

        xp_add_row = QHBoxLayout(); xp_add_row.setSpacing(6)
        xp_add_row.addWidget(_lbl("Add XP:", TEXT2, FS_SMALL))
        self._xp_add_spin = QSpinBox()
        self._xp_add_spin.setRange(0, 999999); self._xp_add_spin.setSingleStep(50)
        self._xp_add_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._xp_add_spin.setStyleSheet(
            f"QSpinBox{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;"
            f"color:{TEXT};padding:2px 6px;min-width:70px;}}")
        xp_add_row.addWidget(self._xp_add_spin)
        xp_add_btn = _btn("+ Add", GOLD, variant="chip", text_color=GOLD2,
                           hover_bg_alpha=0x44, padding="3px 12px")
        xp_add_btn.clicked.connect(self._on_add_xp)
        xp_add_row.addWidget(xp_add_btn)
        xp_add_row.addStretch()
        xp_set_btn = _btn("✎ Set Total", variant="neutral", padding="3px 12px",
                           tooltip="Directly correct the total, rather than adding an award")
        xp_set_btn.clicked.connect(self._on_set_total_xp)
        xp_add_row.addWidget(xp_set_btn)
        xp_cl.addLayout(xp_add_row)

        layout.addWidget(self._xp_card)

        # ── Identity / Character Config card ─────────────────────────────────
        # Title-row-then-content matches the Class Manager/Experience cards
        # above it — consistent card anatomy across the whole top pane, and
        # gives the buttons room to show their current value (see
        # _refresh_identity_buttons) without crowding.
        id_card = QFrame()
        id_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(TEAL,0x33)};border-radius:10px;}}")
        id_cl = QVBoxLayout(id_card); id_cl.setContentsMargins(12,8,12,8); id_cl.setSpacing(6)
        id_cl.addWidget(_lbl("🧬  IDENTITY", TEAL2, FS_SMALL, bold=True))
        id_btn_row = QHBoxLayout(); id_btn_row.setSpacing(8)
        self._identity_btns = {}
        self._identity_btn_labels = {}
        for label, slot, color in [
            ("Race",       "race",       TEAL),
            ("Subrace",    "subrace",    TEAL),
            ("Ancestry",   "ancestry",   GOLD),
            ("Background", "background", AMBER),
        ]:
            b = _btn(f"✎  {label}", color, variant="chip", height=28, font_size=FS_TINY)
            b.clicked.connect(lambda checked=False, s=slot: self._edit_identity(s))
            id_btn_row.addWidget(b)
            self._identity_btns[slot] = b
            self._identity_btn_labels[slot] = label
        id_btn_row.addStretch()
        id_cl.addLayout(id_btn_row)
        layout.addWidget(id_card)
        self._refresh_identity_buttons()
        layout.addStretch()

        # ── Bottom pane: LevelUpPanel + Optional Class Features ───────────────
        bottom_half = QWidget()
        blay = QVBoxLayout(bottom_half)
        blay.setContentsMargins(0, 0, 0, 0)
        blay.setSpacing(8)

        try:
            self._levelup_panel = LevelUpPanel(self.char)
            self._levelup_panel.choices_changed.connect(self._on_choices_changed)
            blay.addWidget(self._levelup_panel, 1)
        except Exception as e:
            import traceback; traceback.print_exc()
            blay.addWidget(_lbl(f"Error: {e}", CRIM2, FS_BODY))

        # ── Optional Class Features (TCoE) ────────────────────────────────
        opt_card = _card()
        opt_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(AMBER,0x55)};border-radius:10px;}}")
        opt_lay = QVBoxLayout(opt_card); opt_lay.setContentsMargins(14,12,14,14); opt_lay.setSpacing(6)
        opt_lay.addWidget(_lbl("✦  OPTIONAL CLASS FEATURES  —  Tasha's Cauldron of Everything",
                               AMBER, FS_SMALL, bold=True))
        opt_lay.addWidget(_lbl("Toggle alternate features for your classes. Discuss with your DM first.",
                               TEXT3, FS_SMALL))
        self._opt_feat_checks = {}
        self._opt_inner = QWidget(); self._opt_inner.setStyleSheet("background:transparent;")
        self._opt_inner_lay = QVBoxLayout(self._opt_inner)
        self._opt_inner_lay.setSpacing(3); self._opt_inner_lay.setContentsMargins(0,4,0,0)
        opt_lay.addWidget(self._opt_inner)
        blay.addWidget(opt_card)

        splitter.addWidget(top_half)
        splitter.addWidget(bottom_half)
        self._choices_top_half = top_half
        # Enough for all 3 top cards (Class Manager, Experience, Identity)
        # without initial clipping when XP leveling mode is on — a hidden
        # Experience card (milestone mode) doesn't consume this space, it
        # just leaves more room for the addStretch() below it, so this
        # default doesn't cost milestone characters anything. The splitter
        # handle can still be dragged to any ratio, same as the Combat tab.
        splitter.setSizes([280, 460])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

        return tab

    def _on_choices_changed(self):
        """Called when choices are made in the LevelUpPanel."""
        self.ctrl.refresh()
        self._mark_dirty()

    # ══ TAB 4: SPELLS ══════════════════════════════════════════════════════════
    def _has_infuse_item_access(self):
        from dnd_app.core.calculator import class_levels
        return class_levels(self.char).get("Artificer", 0) >= 2 and bool(
            self.char.get("artificer_infusions"))

    def _refresh_xp_tracker(self):
        """Updates both the header XP pill and the Choices-tab XP tracker
        card (if built) from char["experience"]/leveling_mode. Called from
        _refresh_stat_bar, so it stays in sync with every other
        controller-driven refresh — including the Settings dialog's
        leveling-mode toggle, which goes through sheet.ctrl.refresh()."""
        from dnd_app.core.character import xp_progress
        xp_mode = self.char.get("leveling_mode", "milestone") == "xp"
        prog = xp_progress(self.char)
        eligible = prog["eligible"]
        levels_due = prog["levels_due"]
        # A big enough XP award can cover more than one level at once —
        # that's supposed to carry over (same as it does at the table),
        # so say how many are actually owed rather than just "ready".
        ready_phrase = "Ready to level up!" if levels_due <= 1 else f"Ready to level up ×{levels_due}!"

        # Once more than one level is owed, "current / next-single-level
        # threshold" reads as broken (the total is already miles past
        # that number) — show the plain total instead of a fraction.
        xp_line = f"{prog['xp']:,} XP" if levels_due > 1 else f"{prog['xp']:,} / {prog['next']:,}"

        if hasattr(self, "_sb_xp"):
            self._sb_xp.setVisible(xp_mode)
            if xp_mode:
                self._sb_xp._val.setText(xp_line)
                self._sb_xp._bar.setValue(prog["pct"])
                border = GOLD if eligible else qa(GOLD,0x55)
                self._sb_xp.setStyleSheet(f"QFrame{{background:{SURF};border:2px solid {border};border-radius:10px;}}")
                if eligible:
                    self._sb_xp.setCursor(Qt.PointingHandCursor)
                    self._sb_xp.mousePressEvent = lambda e: self._open_level_up_or_multiclass()
                    self._sb_xp.setToolTip(f"{prog['xp']:,} XP — {ready_phrase} Click to level up.")
                else:
                    self._sb_xp.setCursor(Qt.ArrowCursor)
                    self._sb_xp.mousePressEvent = lambda e: None
                    remaining = prog["next"] - prog["xp"]
                    self._sb_xp.setToolTip(f"{prog['xp']:,} / {prog['next']:,} XP — {remaining:,} XP to next level")

        if hasattr(self, "_xp_card"):
            self._xp_card.setVisible(xp_mode)
            if xp_mode:
                self._xp_total_lbl.setText(f"{prog['xp']:,} XP")
                self._xp_bar.setValue(prog["pct"])
                if prog["level"] >= 20:
                    self._xp_status_lbl.setText("Max level")
                    self._xp_status_lbl.setStyleSheet(f"color:{TEXT3};font-size:{FS_SMALL}px;font-weight:700;")
                elif eligible:
                    self._xp_status_lbl.setText(f"🌟 {ready_phrase} ({xp_line} XP)" if levels_due <= 1
                                                 else f"🌟 {ready_phrase} ({xp_line})")
                    self._xp_status_lbl.setStyleSheet(f"color:{GOLD2};font-size:{FS_SMALL}px;font-weight:700;")
                else:
                    remaining = prog["next"] - prog["xp"]
                    self._xp_status_lbl.setText(f"{prog['xp']:,} / {prog['next']:,} XP  ·  {remaining:,} to next level")
                    self._xp_status_lbl.setStyleSheet(f"color:{TEXT3};font-size:{FS_SMALL}px;font-weight:700;")

    def _refresh_identity_buttons(self):
        """Shows the CURRENTLY set value on each Choices-tab Identity
        button (e.g. "✎  Race: Human") instead of a bare generic label,
        so the player can see what's already set without clicking
        through each one. Also drives Ancestry's visibility (Dragonborn
        only) from this same single check. Called from
        _refresh_stat_bar, so it stays in sync with every
        controller-driven refresh."""
        if not hasattr(self, "_identity_btns"):
            return
        values = {
            "race": self.char.get("race", ""),
            "subrace": self.char.get("subrace", ""),
            "ancestry": self.char.get("draconic_ancestry", ""),
            "background": self.char.get("background", ""),
        }
        for slot, label in getattr(self, "_identity_btn_labels", {}).items():
            btn = self._identity_btns.get(slot)
            if not btn:
                continue
            val = values.get(slot, "")
            btn.setText(f"✎  {label}: {val}" if val else f"✎  {label}")
        if "ancestry" in self._identity_btns:
            self._identity_btns["ancestry"].setVisible(self.char.get("race", "") == "Dragonborn")

