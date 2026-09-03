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


class CombatMixin:
    def _bind_death_and_conditions(self):
        if getattr(self, "_death_cond_bound", False):
            return
        ds = self.char.get("death_saves", {"successes": 0, "failures": 0})
        for i, cb in enumerate(self._death_success):
            cb.setChecked(i < ds.get("successes", 0))
            cb.stateChanged.connect(self._on_death_save_changed)
        for i, cb in enumerate(self._death_fail):
            cb.setChecked(i < ds.get("failures", 0))
            cb.stateChanged.connect(self._on_death_save_changed)
        if hasattr(self, "_death_status_lbl"):
            self._death_status_lbl.setText(
                self._death_status_text(ds.get("successes", 0), ds.get("failures", 0)))
        active = set(self.char.get("conditions", []))
        for cond, cb in self._cond_checks.items():
            cb.blockSignals(True)
            cb.setChecked(cond in active)
            cb.blockSignals(False)
            cb.stateChanged.connect(lambda s, c=cond: self._on_condition_changed(c, bool(s)))
        self._death_cond_bound = True

    @staticmethod
    def _death_status_text(succ: int, fail: int) -> str:
        if fail >= 3:
            return "DEAD"
        if succ >= 3:
            return "STABLE"
        if fail == 2:
            return "1 more failure = death"
        if succ >= 1 or fail >= 1:
            return f"{succ} success, {fail} failure" + ("s" if fail != 1 else "")
        return "Rolling to live or die"

    def _on_death_save_changed(self):
        succ = sum(1 for cb in self._death_success if cb.isChecked())
        fail = sum(1 for cb in self._death_fail if cb.isChecked())
        self.char["death_saves"] = {"successes": min(3, succ), "failures": min(3, fail)}
        if hasattr(self, "_death_status_lbl"):
            self._death_status_lbl.setText(self._death_status_text(succ, fail))
        if fail >= 3:
            self._show_death_screen()
        elif succ >= 3:
            # Stable at 1 HP
            self.char["current_hp"] = 1
            self._hp_current_hp.setValue(1)
            self.char["death_saves"] = {"successes": 0, "failures": 0}
            # Only update model — don't trigger full combat rebuild
            QMessageBox.information(self, "Stable", "You are stable! You regain consciousness with 1 HP.")
        self._mark_dirty()

    def _show_death_screen(self):
        # Persisted (not just a transient UI event) so that loading a
        # character who died and was saved before being revived shows
        # the death screen again on reopen, instead of silently landing
        # back on a live-looking sheet with no indication anything
        # happened. Only mark dirty on an actual new death, not when
        # __init__ re-shows this for an already-dead loaded character
        # (that shouldn't flag an untouched file as having unsaved edits).
        if not self.char.get("is_dead", False):
            self.char["is_dead"] = True
            self._mark_dirty()
        overlay = QFrame(self)
        overlay.setObjectName("death_overlay")
        overlay.setStyleSheet(
            "QFrame#death_overlay{background:rgba(0,0,0,210);}"
        )
        overlay.setGeometry(self.rect())
        overlay.raise_()
        vl = QVBoxLayout(overlay); vl.setAlignment(Qt.AlignCenter); vl.setSpacing(24)
        vl.addStretch(2)
        you_died = _lbl("YOU DIED", "#c00000", 72, bold=True, align=Qt.AlignCenter)
        you_died.setStyleSheet(
            "color:#c00000;font-size:72px;font-weight:900;letter-spacing:12px;"
            "text-shadow:0 0 40px #88ff0000;"
            "font-family:'Georgia','Times New Roman',serif;"
        )
        vl.addWidget(you_died)
        # Massive damage rule note
        note = _lbl("Instant death: damage ≥ 2× max HP in one hit", "#aa3333", FS_BODY,
                    align=Qt.AlignCenter, wrap=False)
        vl.addWidget(note)
        vl.addSpacing(32)
        revive_btn = QPushButton("  Revive  ")
        revive_btn.setFixedSize(200, 56)
        revive_btn.setStyleSheet(
            f"QPushButton{{background:#2a0000;border:2px solid #c00000;border-radius:10px;"
            f"color:#c00000;font-size:{FS_TITLE}px;font-weight:700;letter-spacing:4px;}}"
            f"QPushButton:hover{{background:#c00000;color:white;}}"
        )
        def _revive():
            overlay.deleteLater()
            if hasattr(self, "_toast_lbl"):
                self._toast_lbl.hide()
            self.char["is_dead"] = False
            self.char["current_hp"] = 1
            self.char["death_saves"] = {"successes": 0, "failures": 0}
            self.char["exhaustion"] = 0          # reviving clears exhaustion
            self._hp_current_hp.setValue(1)
            if hasattr(self, "_exh_combo"):
                self._exh_combo.blockSignals(True)
                self._exh_combo.setCurrentIndex(0)
                self._exh_combo.blockSignals(False)
            self._refresh_death_and_conditions()
            self.ctrl.update("current_hp", 1, rebuild_char=False)
            self._mark_dirty()
        revive_btn.clicked.connect(_revive)
        vl.addWidget(revive_btn, alignment=Qt.AlignCenter)
        vl.addStretch(3)
        overlay.show()

        # Critical Flavor (DM Secrets, optional rule, default off): a
        # random quip at the bottom of the screen -- the death overlay
        # above is centered and mechanical, this is a separate, smaller
        # aside underneath it.
        if self.char.get("optional_rules", {}).get("critical_flavor", False):
            from dnd_app.ui.style.flavor_text import random_death_message
            self._toast(random_death_message(), duration_ms=0)

    def _on_condition_changed(self, cond: str, on: bool):
        active = set(self.char.get("conditions", []))
        if on:
            active.add(cond)
        else:
            active.discard(cond)
        self.char["conditions"] = sorted(active)
        self._refresh_active_conditions()
        self._mark_dirty()
            # Without this, condition-based mechanical indicators (saving
            # throw badges, weapon row advantage/disadvantage, speed)
            # would not update when a condition is toggled — only the
            # underlying data and the "Active Conditions" badge list
            # would change.
        self.ctrl.refresh()

    # ══ TAB 3: COMBAT ══════════════════════════════════════════════════════════

    def _refresh_death_and_conditions(self):
        """Update death-save checkboxes and condition toggles (non-destructive).
        Never rebuilds widgets — only calls setChecked. Never touches HP spinboxes."""
        if not hasattr(self, "_death_success"):
            return
        # Show/hide the death-saves container based on HP
        at_zero = self.char.get("current_hp", 1) <= 0
        if hasattr(self, "_death_saves_container"):
            self._death_saves_container.setVisible(at_zero)
        ds = self.char.get("death_saves", {"successes": 0, "failures": 0})
        for i, cb in enumerate(self._death_success):
            cb.blockSignals(True)
            cb.setChecked(i < ds.get("successes", 0))
            cb.blockSignals(False)
        for i, cb in enumerate(self._death_fail):
            cb.blockSignals(True)
            cb.setChecked(i < ds.get("failures", 0))
            cb.blockSignals(False)
        if hasattr(self, "_death_status_lbl"):
            self._death_status_lbl.setText(
                self._death_status_text(ds.get("successes", 0), ds.get("failures", 0)))
        if hasattr(self, "_cond_checks"):
            active = set(self.char.get("conditions", []))
            for cond, cb in self._cond_checks.items():
                cb.blockSignals(True)
                cb.setChecked(cond in active)
                cb.blockSignals(False)

    def _on_hd_changed(self, hd_key: str, value: int, total: int):
        """User changed a hit-dice spinbox."""
        hd = self.char.setdefault("hit_dice", {})
        hd.setdefault(hd_key, {"total": total, "remaining": total})["remaining"] = value
        self._mark_dirty()

    def _wildshape_resource(self):
        """The formal char['resources'] entry for Wild Shape (key
        'wild_shape') -- the SAME entry the Passive/Other tab's generic
        resource tracker (_build_resource_rows) reads and writes, so
        transforming here and editing that tab's spinbox stay in sync.
        Returns None if Wild Shape isn't available yet (not a Druid, or
        below 2nd level)."""
        return next((r for r in self.char.get("resources", [])
                     if r.get("key") == "wild_shape"), None)

    def _wildshape_uses_left(self):
        """(uses_remaining, uses_max), both ints -- or (None, None) for
        unlimited (Archdruid, 20th level: current_max is the string
        "Unlimited" at that point, not a number)."""
        res = self._wildshape_resource()
        if res is None:
            return (0, 0)
        mx = res.get("current_max", 0)
        if not isinstance(mx, int):
            return (None, None)
        return (res.get("current", 0), mx)

    def _spend_wildshape_use(self) -> bool:
        """Spend one Wild Shape use against the shared resource. Returns
        False (and spends nothing) if none remain; always True for
        unlimited (Archdruid)."""
        res = self._wildshape_resource()
        if res is None:
            return False
        mx = res.get("current_max", 0)
        if not isinstance(mx, int):
            return True
        cur = res.get("current", 0)
        if cur <= 0:
            return False
        res["current"] = cur - 1
        return True

    def _build_wildshape_control_card(self) -> QFrame:
        """Wild Shape transformation control — prime (pick a beast), fire
        (transform, consuming one use), reload (the use is spent
        automatically as part of firing, not a separate step the player
        has to remember). While transformed, shows the beast's own HP pool
        (tracked separately from the character's own HP, matching the real
        rule that you don't lose your own HP while shapeshifted) with a
        Revert control.

        Known limitation: this does not yet cascade the beast's ability
        scores into every downstream calculation (skills, saves, etc.) —
        it tracks the transformation state, uses, and a separate HP pool
        correctly, and shows the beast's stat block, but a full sheet-wide
        override of STR/DEX/CON-driven calculations is a larger follow-up."""
        from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
        from dnd_app.core.calculator import get_available_wildshape_beasts

        card = _card(PURPLE+"55")
        cl = QVBoxLayout(card); cl.setContentsMargins(12,10,12,10); cl.setSpacing(6)
        cl.addWidget(_lbl("WILD SHAPE", GOLD, FS_SMALL, bold=True))

        active = self.char.get("_wildshape_active")
        if active and active in WILDSHAPE_BEASTS:
            beast = WILDSHAPE_BEASTS[active]
            cl.addWidget(_lbl(f"Currently: {active}", PURP2, FS_BODY, bold=True, wrap=False))
            cur_hp = self.char.get("_wildshape_hp", beast["hp"])
            cl.addWidget(_lbl(f"HP {cur_hp}/{beast['hp']}   AC {beast['ac']}   "
                              f"(edit HP in the card above — same pool)", TEXT2, FS_SMALL))
            # Circle of the Moon's Combat Wild Shape: while transformed,
            # spend a spell slot as a bonus action to regain 1d8 HP per
            # level of the slot expended.
            from dnd_app.core.calculator import subclasses as _subclasses_wsc, class_levels as _cl_wsc
            is_moon_wsc = "moon" in _subclasses_wsc(self.char).get("Druid", "").lower()
            if is_moon_wsc:
                slots_used = self.char.get("spell_slots_used", [0]*9)
                from dnd_app.core.multiclass import compute_all_spell_slots
                slot_data = compute_all_spell_slots(_cl_wsc(self.char), _subclasses_wsc(self.char))
                slots_max = slot_data.get("spell_slots") or [0]*9
                has_slot = any(slots_max[i] - (slots_used[i] if i < len(slots_used) else 0) > 0 for i in range(9))
                heal_btn = QPushButton("\U0001f52e Combat Wild Shape: Spend Slot to Heal")
                heal_btn.setEnabled(has_slot and cur_hp < beast["hp"])
                heal_btn.setToolTip("Bonus action: expend a spell slot to regain 1d8 HP per level of the slot.")
                heal_btn.setStyleSheet(pill_btn("", GOLD).styleSheet())
                heal_btn.clicked.connect(self._wildshape_moon_heal)
                cl.addWidget(heal_btn)
            revert_btn = QPushButton("Revert to Normal Form")
            revert_btn.setStyleSheet(pill_btn("", CRIMSON).styleSheet())
            revert_btn.clicked.connect(self._wildshape_revert)
            cl.addWidget(revert_btn)
        else:
            available = get_available_wildshape_beasts(self.char)
            picker_row = QHBoxLayout(); picker_row.setSpacing(8)
            combo = QComboBox(); combo.setAccessibleName("Choose a beast to Wild Shape into")
            for name in available:
                b = WILDSHAPE_BEASTS.get(name, {})
                combo.addItem(f"{name} (CR {b.get('cr_label','?')})", name)
            picker_row.addWidget(combo, 1)
            cl.addLayout(picker_row)

            uses_left, uses_max = self._wildshape_uses_left()
            if uses_left is None:
                cl.addWidget(_lbl("Unlimited uses (Archdruid)", TEXT2, FS_SMALL))
            else:
                cl.addWidget(_lbl(f"{uses_left}/{uses_max} uses remaining (short/long rest)", TEXT2, FS_SMALL))
            from dnd_app.core.calculator import subclasses as _sc_wsp
            if "moon" in _sc_wsp(self.char).get("Druid", "").lower():
                cl.addWidget(_lbl("Combat Wild Shape: use as a bonus action instead of an action.",
                                   GOLD2, FS_TINY, wrap=True))

            fire_btn = QPushButton("\U0001f43e Transform" if uses_left is None
                                    else f"\U0001f43e Transform ({uses_left} left)")
            fire_btn.setEnabled((uses_left is None or uses_left > 0) and combo.count() > 0)
            fire_btn.setStyleSheet(pill_btn("", PURPLE).styleSheet())
            fire_btn.clicked.connect(lambda checked=False, cb=combo: self._wildshape_transform(cb.currentData()))
            cl.addWidget(fire_btn)
        return card

    def _rebuild_wildshape_card(self):
        """_refresh_combat() only updates values on existing widgets, it
        doesn't rebuild the tab structure — but the Wild Shape card needs
        to switch its entire content (picker vs. transformed-state view)
        after transforming or reverting, not just update a number. This
        removes the old card and puts a freshly-built one in its place."""
        container = getattr(self, "_wildshape_card_container", None)
        old_card = getattr(self, "_wildshape_card_widget", None)
        if container is None:
            return
        if old_card is not None:
            container.removeWidget(old_card)
            old_card.hide()
            old_card.setParent(None)
            old_card.deleteLater()
        new_card = self._build_wildshape_control_card()
        self._wildshape_card_widget = new_card
        container.addWidget(new_card, 4)

    def _wildshape_transform(self, beast_name: str):
        if not beast_name: return
        from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(beast_name)
        if not beast: return
        if not self._spend_wildshape_use():
            self._toast("No Wild Shape uses remaining — available again after a short or long rest.")
            return
        self.char["_wildshape_active"] = beast_name
        self.char["_wildshape_hp"] = beast["hp"]
        if "Wild Shape" not in self.char.get("active_effects", []):
            self.char.setdefault("active_effects", []).append("Wild Shape")
        self._mark_dirty()
        self.ctrl.refresh()
        self._refresh_combat()
        self._rebuild_wildshape_card()
        self._toast(f"\U0001f43e Transformed into {beast_name}")

    def _wildshape_moon_heal(self):
        """Circle of the Moon's Combat Wild Shape: spend a spell slot as
        a bonus action to regain 1d8 HP per level of the slot, while
        transformed."""
        from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
        from dnd_app.core.calculator import subclasses as _sc, class_levels as _clv
        from dnd_app.core.multiclass import compute_all_spell_slots
        active = self.char.get("_wildshape_active")
        beast = WILDSHAPE_BEASTS.get(active)
        if not beast: return
        slots_used = self.char.get("spell_slots_used", [0]*9)
        slot_data = compute_all_spell_slots(_clv(self.char), _sc(self.char))
        slots_max = slot_data.get("spell_slots") or [0]*9
        available_levels = [i+1 for i in range(9) if slots_max[i] - (slots_used[i] if i < len(slots_used) else 0) > 0]
        if not available_levels:
            return
        level, ok = QInputDialog.getItem(
            self, "Combat Wild Shape",
            "Expend which spell slot level? (heals 1d8 per level)",
            [str(l) for l in available_levels], 0, False)
        if not ok:
            return
        level = int(level)
        import random
        roll = sum(random.randint(1, 8) for _ in range(level))
        cur_hp = self.char.get("_wildshape_hp", beast["hp"])
        new_hp = min(beast["hp"], cur_hp + roll)
        self.char["_wildshape_hp"] = new_hp
        used_list = list(slots_used) + [0]*(9-len(slots_used))
        used_list[level-1] += 1
        self.char["spell_slots_used"] = used_list
        self._mark_dirty()
        self.ctrl.refresh()
        self._refresh_combat()
        self._rebuild_wildshape_card()
        self._toast(f"\U0001f52e Expended a level {level} slot: healed {roll} HP ({new_hp}/{beast['hp']})")

    def _wildshape_revert(self):
        # Reverting early doesn't refund the use — matches the real rule
        # that the use is spent the moment you transform, not metered by
        # how long you stay shapeshifted.
        self.char["_wildshape_active"] = None
        self.char.pop("_wildshape_hp", None)
        fx = self.char.get("active_effects", [])
        if "Wild Shape" in fx:
            fx.remove("Wild Shape")
        self._mark_dirty()
        self.ctrl.refresh()
        self._refresh_combat()
        self._rebuild_wildshape_card()
        self._toast("Reverted to normal form")

    def _set_wildshape_hp(self, value: int):
        self.char["_wildshape_hp"] = value
        self._mark_dirty()

    def _build_tab_combat(self):
        """
        Combat tab — redesigned layout:
          TOP STRIP  (~20%): HP | Armor & Shield | Conditions  (always visible)
          BOTTOM     (~80%): Action economy tabs (full height, scrollable)
                              + Class resources / quick spells inside the Other tab
        The old left/right split is gone; everything lives in a single QSplitter
        so the user can drag the divider if they want.
        """
        tab = QWidget()
        root_lay = QVBoxLayout(tab); root_lay.setContentsMargins(10,10,10,10); root_lay.setSpacing(8)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(f"QSplitter::handle{{background:{qa(AMBER,0x33)};height:4px;"
                              f"border-radius:2px;margin:2px 40%;}}"
                              f"QSplitter::handle:hover{{background:{AMBER};}}")

        top_half = QWidget()
        top_half_lay = QVBoxLayout(top_half); top_half_lay.setContentsMargins(0,0,0,0); top_half_lay.setSpacing(8)

        # ── TOP STRIP: HP | Armor | Conditions ───────────────────────────────
        top_strip = QWidget()
        top_strip.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        top_lay = QHBoxLayout(top_strip); top_lay.setContentsMargins(0,0,0,0); top_lay.setSpacing(8)

        # ── HP card ───────────────────────────────────────────────────────────
        hp_card = _card(GREEN+"55"); hp_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hpcl = QVBoxLayout(hp_card); hpcl.setContentsMargins(12,10,12,10)
        hpcl.addWidget(_lbl("HIT POINTS", GOLD, FS_SMALL, bold=True))
        hp_row = QHBoxLayout(); hp_row.setSpacing(8)
        for label, key, color in [("Max","max_hp",IND2),("Current","current_hp",GREEN2),("Temp","temp_hp",TEAL2)]:
            col = QVBoxLayout(); col.setSpacing(2)
            if key == "max_hp":
                label_row = QHBoxLayout(); label_row.setSpacing(2); label_row.setContentsMargins(0,0,0,0)
                label_row.addWidget(_lbl(label, TEXT2, FS_TINY, bold=True, align=Qt.AlignCenter), 1)
                reset_max = QPushButton("↺")
                reset_max.setFixedSize(14, 14)
                reset_max.setToolTip("Reset Max HP to the auto-calculated value "
                                     "(class Hit Dice + CON)")
                reset_max.setStyleSheet(
                    f"QPushButton{{background:transparent;border:none;"
                    f"color:{TEXT3};font-size:11px;padding:0;}}"
                    f"QPushButton:hover{{color:{TEAL2};}}")
                reset_max.clicked.connect(self._reset_max_hp_override)
                label_row.addWidget(reset_max)
                col.addLayout(label_row)
            else:
                col.addWidget(_lbl(label, TEXT2, FS_TINY, bold=True, align=Qt.AlignCenter))
            sp = QSpinBox(); sp.setRange(0,999); sp.setAlignment(Qt.AlignCenter)
            sp.setButtonSymbols(QAbstractSpinBox.NoButtons)
            sp.setStyleSheet(f"QSpinBox{{font-size:{FS_TITLE}px;font-weight:700;color:{color};"
                             f"border:2px solid {qa(color,0x55)};border-radius:8px;"
                             f"background:{SURF2};padding:2px;min-width:64px;}}")
            col.addWidget(sp); hp_row.addLayout(col, 1)
            setattr(self, f"_hp_{key}", sp)
        hpcl.addLayout(hp_row)
        self._hp_bar = QProgressBar(); self._hp_bar.setRange(0,100); self._hp_bar.setValue(100)
        self._hp_bar.setTextVisible(False); self._hp_bar.setFixedHeight(6)
        self._hp_bar.setStyleSheet(
            f"QProgressBar{{background:{SURF2};border:none;border-radius:3px;}}"
            f"QProgressBar::chunk{{border-radius:3px;background:{GREEN2};}}")
        hpcl.addWidget(self._hp_bar)
        # Resistances strip: holds an arbitrary number of badges (multiple
        # resistance/immunity sources, or a "resistance to everything but
        # psychic"-style toggle expanded into 12 individual damage types)
        # without overflowing or squeezing off-screen. Uses plain QWidget
        # + QGridLayout rather than FlowContainer/FlowLayout — same as
        # the tool proficiency chips in _build_tab_skills, since
        # FlowContainer.resizeEvent()'s setMinimumHeight() can trigger
        # another resize event in Qt, looping forever; these strips are
        # an even more direct trigger, since their own refresh functions
        # also call heightForWidth()+setMinimumHeight() explicitly. A
        # grid wraps at a fixed column count instead of dynamically by
        # pixel width, an acceptable trade-off since these badges are
        # short and few. A caption above each strip distinguishes it from
        # adjacent badge groups sharing the same visual style.
        self._resist_caption = _lbl("RESISTANCES", TEXT3, FS_TINY, bold=True, wrap=False)
        self._resist_caption.setVisible(False)
        hpcl.addWidget(self._resist_caption)
        self._resist_frame = QWidget(); self._resist_frame.setStyleSheet("QWidget{background:transparent;}")
        self._resist_lay = QGridLayout(self._resist_frame)
        self._resist_lay.setSpacing(4); self._resist_lay.setContentsMargins(0,0,0,0)
        self._resist_frame.setVisible(False)
        hpcl.addWidget(self._resist_frame, 1)
        # NOTE: climb/swim/fly used to get their own badge strip here too,
        # separate from the resistances strip above. Removed — the top
        # stat-bar speed pill already shows climb/swim/fly (✈/🌊/↑ next to
        # the walk speed) whenever any are non-zero, so this strip was
        # pure duplication of information already on screen, not just a
        # resistance-lookalike problem (which the caption/color fix above
        # already solved on its own).
        # Small, read-only concentration indicator — the full tracker (with
        # Drop/Save buttons) lives in the Spells tab, which isn't very
        # visible during active combat where damage tracking happens. This
        # just gives at-a-glance visibility here too; the automatic
        # concentration-save prompt on taking damage already fires from
        # this tab regardless (see _do_damage), so no duplicate controls
        # are needed.
        self._combat_conc_lbl = _lbl("", AMBER, FS_SMALL, wrap=False)
        self._combat_conc_lbl.setVisible(False)
        hpcl.addWidget(self._combat_conc_lbl)
        # Damage / Heal
        ctrl_row = QHBoxLayout(); ctrl_row.setSpacing(6)
        self._hp_amt = QSpinBox(); self._hp_amt.setRange(1,9999); self._hp_amt.setValue(1)
        self._hp_amt.setMinimumWidth(64); self._hp_amt.setMaximumWidth(80)
        dmg_btn = _btn("Damage", CRIMSON, variant="danger", height=32, bg_alpha=0x44,
                        text_color=CRIM2, hover_text="white", font_size=FS_SMALL, padding="0px")
        dmg_btn.setAccessibleName("Apply damage to hit points")
        dmg_btn.clicked.connect(self._do_damage)
        heal_btn = _btn("Heal", GREEN, variant="cta", height=32, bg_alpha=0x44,
                         text_color=GREEN2, hover_text="white", font_size=FS_SMALL, padding="0px")
        heal_btn.setAccessibleName("Heal hit points")
        heal_btn.clicked.connect(self._do_heal)
        ctrl_row.addWidget(self._hp_amt); ctrl_row.addWidget(dmg_btn); ctrl_row.addWidget(heal_btn)
        ctrl_row.addStretch()
        hpcl.addLayout(ctrl_row)
        # Death saves — a genuinely tense moment (0 HP, rolling to live or
        # die) gets its own alert-styled card (only shown at 0 HP to
        # begin with, so it earns the attention) with bigger pips, a
        # live status line, and per-pip tooltips explaining the actual
        # rule.
        self._death_saves_container = QFrame()
        self._death_saves_container.setStyleSheet(
            f"QFrame{{background:{qa(CRIMSON,0x14)};border:2px solid {qa(CRIMSON,0x66)};"
            f"border-radius:8px;}}")
        self._death_saves_container.setVisible(False)
        dsl = QVBoxLayout(self._death_saves_container)
        dsl.setContentsMargins(12,10,12,10); dsl.setSpacing(6)

        ds_hdr = QHBoxLayout(); ds_hdr.setSpacing(8)
        ds_hdr.addWidget(_lbl("\U0001f480  DEATH SAVING THROWS", CRIM2, FS_SMALL, bold=True, wrap=False))
        ds_hdr.addStretch()
        self._death_status_lbl = _lbl("", TEXT2, FS_TINY, bold=True, wrap=False)
        ds_hdr.addWidget(self._death_status_lbl)
        dsl.addLayout(ds_hdr)

        pip_tip = ("Roll a d20 at the start of each of your turns while at 0 HP and "
                   "taking no other action. 10 or higher: success. Below 10: failure. "
                   "A natural 20 regains 1 HP instead; a natural 1 counts as two failures. "
                   "3 successes: stable at 0 HP. 3 failures: dead.")
        pips_row = QHBoxLayout(); pips_row.setSpacing(18)

        succ_block = QVBoxLayout(); succ_block.setSpacing(4)
        succ_block.addWidget(_lbl("SUCCESSES", GREEN2, FS_TINY, bold=True, wrap=False))
        succ_pips = QHBoxLayout(); succ_pips.setSpacing(5)
        self._death_success = [QCheckBox() for _ in range(3)]
        for cb in self._death_success:
            cb.setFixedSize(24,24)
            cb.setToolTip(pip_tip)
            cb.setStyleSheet(
                f"QCheckBox::indicator{{width:22px;height:22px;border-radius:11px;"
                f"border:2px solid {GREEN};background:{BG};}}"
                f"QCheckBox::indicator:hover{{border-color:{GREEN2};background:{qa(GREEN,0x22)};}}"
                f"QCheckBox::indicator:checked{{background:{GREEN2};border-color:{GREEN2};}}")
            succ_pips.addWidget(cb)
        succ_block.addLayout(succ_pips)
        pips_row.addLayout(succ_block)

        fail_block = QVBoxLayout(); fail_block.setSpacing(4)
        fail_block.addWidget(_lbl("FAILURES", CRIM2, FS_TINY, bold=True, wrap=False))
        fail_pips = QHBoxLayout(); fail_pips.setSpacing(5)
        self._death_fail = [QCheckBox() for _ in range(3)]
        for cb in self._death_fail:
            cb.setFixedSize(24,24)
            cb.setToolTip(pip_tip)
            cb.setStyleSheet(
                f"QCheckBox::indicator{{width:22px;height:22px;border-radius:11px;"
                f"border:2px solid {CRIMSON};background:{BG};}}"
                f"QCheckBox::indicator:hover{{border-color:{CRIM2};background:{qa(CRIMSON,0x22)};}}"
                f"QCheckBox::indicator:checked{{background:{CRIM2};border-color:{CRIM2};}}")
            fail_pips.addWidget(cb)
        fail_block.addLayout(fail_pips)
        pips_row.addLayout(fail_block)
        pips_row.addStretch()
        dsl.addLayout(pips_row)
        hpcl.addWidget(self._death_saves_container)
        top_lay.addWidget(hp_card, 4)

        # ── Armor & Shield card (READ-ONLY display — equip via Gear tab) ──────
        armor_card = _card(); armor_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        acl2 = QVBoxLayout(armor_card); acl2.setContentsMargins(12,10,12,10)
        acl2.addWidget(_lbl("ARMOR & SHIELD", GOLD, FS_SMALL, bold=True))
        self._armor_card_ac_lbl = _lbl("AC —", TEAL2, FS_BODY, bold=True)
        self._armor_card_ac_lbl.setStyleSheet(
            f"QLabel{{background:{qa(TEAL,0x22)};border:1px solid {TEAL};border-radius:6px;"
            f"padding:4px 10px;color:{TEAL2};font-weight:700;font-size:{FS_BODY}px;}}")
        acl2.addWidget(self._armor_card_ac_lbl)
        self._armor_display = QLabel("No Armor")
        self._armor_display.setStyleSheet(
            f"QLabel{{background:{SURF2};border:1px solid {BORDER2};border-radius:6px;"
            f"padding:6px 10px;color:{TEXT};font-weight:700;}}")
        self._armor_display.setToolTip("Equip armor from the Gear tab")
        self._shield_display = QLabel("No Shield")
        self._shield_display.setStyleSheet(
            f"QLabel{{background:{SURF2};border:1px solid {BORDER};border-radius:6px;"
            f"padding:4px 10px;color:{TEXT3};font-size:{FS_SMALL}px;}}")
        acl2.addWidget(self._armor_display); acl2.addWidget(self._shield_display)
        armor_jump = QPushButton("⚙ Equip armor & shield in Gear ▸")
        armor_jump.setFixedHeight(24)
        armor_jump.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{TEAL2};"
            f"font-size:{FS_TINY}px;text-align:left;}}"
            f"QPushButton:hover{{color:{TEAL};text-decoration:underline;}}")
        armor_jump.clicked.connect(lambda: self._tabs.setCurrentIndex(3))
        acl2.addWidget(armor_jump)
        # Weapons section embedded in armor card. The Gear tab (for
        # equipping weapons/armor) is one click away on the tab bar itself.
        acl2.addWidget(_lbl("WEAPONS", GOLD, FS_SMALL, bold=True))
        wpn_host = QWidget(); wpn_host.setStyleSheet("background:transparent;")
        self._weapon_rows = QVBoxLayout(wpn_host)
        self._weapon_rows.setSpacing(4); self._weapon_rows.setContentsMargins(0,0,0,0)
        wpn_scroll = QScrollArea(); wpn_scroll.setWidgetResizable(True)
        wpn_scroll.setFrameShape(QFrame.NoFrame)
        wpn_scroll.setMinimumHeight(80)
        wpn_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        wpn_scroll.setWidget(wpn_host)
        acl2.addWidget(wpn_scroll, 1)
        top_lay.addWidget(armor_card, 5)

        # ── Conditions card ───────────────────────────────────────────────────
        cond_card = _card(); cond_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ccl = QVBoxLayout(cond_card); ccl.setContentsMargins(12,10,12,10)
        ccl.addWidget(_lbl("CONDITIONS", GOLD, FS_SMALL, bold=True))
        exh_row = QWidget(); exhl = QHBoxLayout(exh_row)
        exhl.setContentsMargins(0,0,0,0); exhl.setSpacing(6)
        exhl.addWidget(_lbl("Exhaustion:", TEXT2, FS_SMALL, wrap=False))
        self._exhaustion_spin = QSpinBox(); self._exhaustion_spin.setRange(0,6)
        self._exhaustion_spin.setFixedWidth(52)
        self._exhaustion_spin.setStyleSheet(
            f"QSpinBox{{background:{SURF2};border:1px solid {BORDER2};"
            f"border-radius:4px;color:{TEXT};font-size:{FS_SMALL}px;padding:2px;}}")
        self._exhaustion_spin.setToolTip(
            "PHB exhaustion (cumulative):\n"
            "1 — Disadvantage on ability checks\n"
            "2 — Speed halved\n"
            "3 — Disadvantage on attack rolls and saving throws\n"
            "4 — Hit point maximum halved\n"
            "5 — Speed reduced to 0\n"
            "6 — Death")
        self._exhaustion_spin.setAccessibleName(
            "Exhaustion level, 0 to 6. Level 6 is death.")
        self._exhaustion_spin.valueChanged.connect(self._on_exhaustion_changed)
        exhl.addWidget(self._exhaustion_spin)
        exhl.addStretch()
        ccl.addWidget(exh_row)
        self._cond_checks = {}
        COND_NAMES = ["Blinded","Charmed","Deafened","Frightened","Gagged",
                      "Grappled","Incapacitated","Invisible","Paralyzed",
                      "Petrified","Poisoned","Prone","Restrained","Stunned","Unconscious"]
        cond_grid = QGridLayout(); cond_grid.setSpacing(3)
        for ci, cname in enumerate(COND_NAMES):
            cb = QCheckBox(cname); cb.setStyleSheet(
                f"QCheckBox{{color:{TEXT2};font-size:{FS_SMALL}px;}}"
                f"QCheckBox::indicator{{width:12px;height:12px;border:1px solid {BORDER2};"
                f"border-radius:3px;background:{SURF2};}}"
                f"QCheckBox::indicator:checked{{background:{CRIM2};border-color:{CRIM2};}}")
            cb.stateChanged.connect(lambda s,n=cname: self._on_condition_changed(n, bool(s)))
            cdata = CONDITIONS.get(cname, {})
            tip_lines = list(cdata.get("effects", []))
            if cdata.get("levels"):
                tip_lines = tip_lines + [""] + cdata["levels"]
            if cdata.get("source"):
                tip_lines.append(f"({cdata['source']})")
            if tip_lines:
                cb.setToolTip("\n".join(tip_lines))
            self._cond_checks[cname] = cb
            cond_grid.addWidget(cb, ci//3, ci%3)
        ccl.addLayout(cond_grid)

        # "Active Conditions" section — uses the space that used to just
        # be addStretch()'d away. Shows each currently-active condition
        # (plus exhaustion, if its level is above 0) as a readable badge
        # with the full effect text (including exhaustion's disadvantage
        # note, which was always present in the data but too cramped in
        # the old inline label to actually read) available on hover.
        ccl.addWidget(_sep())
        ccl.addWidget(_lbl("ACTIVE CONDITIONS", GOLD, FS_TINY, bold=True))
        self._active_cond_frame = QWidget(); self._active_cond_frame.setStyleSheet("background:transparent;")
        self._active_cond_lay = QGridLayout(self._active_cond_frame)
        self._active_cond_lay.setSpacing(4); self._active_cond_lay.setContentsMargins(0,4,0,0)
        ccl.addWidget(self._active_cond_frame)
        self._active_cond_none_lbl = _lbl("None", TEXT3, FS_SMALL)
        ccl.addWidget(self._active_cond_none_lbl)
        top_lay.addWidget(cond_card, 3)

        from dnd_app.core.calculator import get_wild_shape_info
        if get_wild_shape_info(self.char) is not None:
            self._wildshape_card_container = top_lay
            self._wildshape_card_widget = self._build_wildshape_control_card()
            top_lay.addWidget(self._wildshape_card_widget, 4)

        top_half_lay.addWidget(top_strip)
        # No addStretch() here: dragging the splitter handle below should
        # grow top_strip (and its cards, set to Expanding) rather than
        # have the extra space absorbed as invisible blank space. With
        # top_strip's size policy set to Preferred rather than a hard
        # Maximum, and nothing else competing for space in this layout,
        # it claims whatever height the layout gives it.

        # Per-bucket category filters are built inside the tab-
        # construction loop below so each tab gets its own independent
        # filter row, rather than one shared row across all 4.

        # ── BOTTOM: Action Economy tabs (full remaining height) ───────────────
        self._action_tabs = QTabWidget()
        # See base.py's _tabs for why this is needed -- QTabWidget ignores
        # a plain QSS "background" rule without it, leaving the strip
        # past the last tab showing the OS default background.
        self._action_tabs.setAttribute(Qt.WA_StyledBackground, True)
        # NOT setDocumentMode(True): document mode suppresses the style
        # engine's own ::pane frame/background painting in most Qt styles,
        # making the "::pane{border:...;background:{SURF};...}" rule below
        # a no-op -- with WA_StyledBackground set above, that would let the
        # widget's own dark PANELDK gap-strip color wash across the entire
        # content area behind every action row, instead of just the strip
        # past the last tab. Leaving document mode off matches the other 3
        # QTabWidgets in the app (none of which set it), letting ::pane's
        # own light background actually render.
        self._action_tabs.setTabPosition(QTabWidget.North)
        self._action_tabs.setStyleSheet(
            f"QTabWidget::pane{{border:1px solid {qa(AMBER,0x33)};border-radius:8px;"
            f"background:{SURF};margin-top:-1px;}}"
            f"QTabBar::tab{{background:{BG};color:{TEXT2};border:1px solid {qa(AMBER,0x22)};"
            f"border-bottom:none;padding:6px 14px;border-radius:6px 6px 0 0;"
            f"font-size:{FS_SMALL}px;font-weight:700;min-width:80px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD};border-color:{qa(AMBER,0x66)};}}"
            f"QTabBar::tab:hover{{background:{qa(AMBER,0x11)};color:{AMBE2};}}"
        )
        self._action_bucket_widgets = {}
        self._action_cat_filters = {}
        self._action_cat_btns_by_bucket = {}
        self._action_filter_rows = {}
        self._action_spell_level_filters = {}
        self._action_lvl_btns_by_bucket = {}
        self._action_level_filter_rows = {}
        _TAB_DISPLAY_LABEL = {"Action":"Action","Bonus Action":"Bonus Action",
                               "Reaction":"Reaction","Passive":"Other"}
        CAT_ICONS = {"All": "◆", "Common": "⚔", "Magic Item": "✨", "Race": "🧬", "Spell": "📖"}
        for bucket_name, icon in [("Action","⚔"),("Bonus Action","✦"),
                                   ("Reaction","⚡"),("Passive","◎")]:
            bw = QWidget(); bw.setStyleSheet("background:transparent;")
            bl = QVBoxLayout(bw); bl.setContentsMargins(8,8,8,8); bl.setSpacing(5)

            # Per-bucket category filter row: independent state so each
            # tab (including Passive) filters independently rather than
            # sharing one row.
            self._action_cat_filters[bucket_name] = "All"
            self._action_cat_btns_by_bucket[bucket_name] = {}
            filter_row_w = QWidget()
            filter_row = QHBoxLayout(filter_row_w)
            filter_row.setContentsMargins(0,0,0,0); filter_row.setSpacing(6)
            def _make_cat_click(cat, _bucket=bucket_name):
                def _click():
                    self._action_cat_filters[_bucket] = cat
                    for c, b in self._action_cat_btns_by_bucket[_bucket].items():
                        b.setStyleSheet(self._action_cat_btn_style(c == cat))
                    self._action_level_filter_rows[_bucket].setVisible(cat == "Spell")
                    self._refresh_action_tabs()
                return _click
            for cat in ["All", "Common", "Magic Item", "Race", "Spell"]:
                btn = QPushButton(f"{CAT_ICONS[cat]} {cat}")
                btn.setMinimumHeight(24)
                btn.setStyleSheet(self._action_cat_btn_style(cat == "All"))
                btn.clicked.connect(_make_cat_click(cat))
                if cat == "Magic Item":
                    btn.setToolTip("Placeholder — magic items aren't mechanically wired into "
                                    "Known Actions yet.")
                self._action_cat_btns_by_bucket[bucket_name][cat] = btn
                filter_row.addWidget(btn)
            filter_row.addStretch()
            self._action_filter_rows[bucket_name] = filter_row_w
            bl.addWidget(filter_row_w)

            # Secondary spell-level filter — hidden until "Spell" is
            # selected in THIS bucket's own filter row.
            self._action_spell_level_filters[bucket_name] = "All"
            self._action_lvl_btns_by_bucket[bucket_name] = {}
            lvl_row_w = QWidget()
            lvl_row = QHBoxLayout(lvl_row_w)
            lvl_row.setContentsMargins(0,0,0,0); lvl_row.setSpacing(4)
            def _make_lvl_click(lvl, _bucket=bucket_name):
                def _click():
                    self._action_spell_level_filters[_bucket] = lvl
                    for l, b in self._action_lvl_btns_by_bucket[_bucket].items():
                        b.setStyleSheet(self._action_cat_btn_style(l == lvl, small=True))
                    self._refresh_action_tabs()
                return _click
            for lvl_label in ["All", "Cantrip"] + [f"L{n}" for n in range(1, 10)]:
                btn = QPushButton(lvl_label)
                btn.setMinimumHeight(20); btn.setMaximumWidth(48)
                btn.setStyleSheet(self._action_cat_btn_style(lvl_label == "All", small=True))
                btn.clicked.connect(_make_lvl_click(lvl_label))
                self._action_lvl_btns_by_bucket[bucket_name][lvl_label] = btn
                lvl_row.addWidget(btn)
            lvl_row.addStretch()
            lvl_row_w.setVisible(False)
            self._action_level_filter_rows[bucket_name] = lvl_row_w
            bl.addWidget(lvl_row_w)

            bl.addStretch()
            self._action_bucket_widgets[bucket_name] = (bw, bl)
            scroll = QScrollArea(); scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(bw)
            scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
            label = _TAB_DISPLAY_LABEL.get(bucket_name, bucket_name)
            self._action_tabs.addTab(scroll, f"{icon} {label}")

        # ── 5th tab: Active spell effects (Shield of Faith, Haste, …) ────────
        fx_tab = QWidget(); fx_tab.setStyleSheet("background:transparent;")
        fxl = QVBoxLayout(fx_tab); fxl.setContentsMargins(10,10,10,10); fxl.setSpacing(8)
        add_row = QHBoxLayout(); add_row.setSpacing(8)
        self._fx_combo = QComboBox(); self._fx_combo.setEditable(True)
        self._fx_combo.setAccessibleName("Choose or type a spell effect to apply")
        from dnd_app.core.effects import EFFECT_TABLE
        self._fx_combo.addItems(sorted(EFFECT_TABLE.keys()))
        self._fx_combo.setMinimumHeight(30)
        fx_add = QPushButton("＋ Apply Effect"); fx_add.setMinimumHeight(30)
        fx_add.setAccessibleName("Apply the selected spell effect")
        fx_add.setStyleSheet(_btn("", TEAL, variant="cta", text_color=TEAL2,
                                   hover_text="white", padding="2px 14px").styleSheet())
        fx_add.clicked.connect(self._add_active_effect)
        add_row.addWidget(self._fx_combo, 1); add_row.addWidget(fx_add)
        fxl.addLayout(add_row)
        fx_scroll = QScrollArea(); fx_scroll.setWidgetResizable(True)
        fx_scroll.setFrameShape(QFrame.NoFrame)
        fx_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        fx_host = QWidget(); fx_host.setStyleSheet("background:transparent;")
        self._fx_lay = QVBoxLayout(fx_host); self._fx_lay.setSpacing(6)
        self._fx_lay.addStretch()
        fx_scroll.setWidget(fx_host)
        fxl.addWidget(fx_scroll, 1)
        self._action_tabs.addTab(fx_tab, "☄ Effects")

        # ── Turn tracker bar (Action / Bonus / Reaction economy per turn) ────
        # Deliberately NOT part of the resizable splitter below — it's a
        # single fixed-height row of buttons with no variable-length
        # content, so giving it a share of the splitter just took space
        # away from the Attacks/action-tabs area (which holds actual
        # variable-length content players need to read clearly) for zero
        # benefit, since there's nothing useful gained by resizing this bar
        # bigger or smaller.
        self._turn_counts = {"Action":0, "Bonus Action":0, "Reaction":0}
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        turn_bar = QFrame()
        turn_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        turn_bar.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(AMBER,0x33)};"
                               f"border-radius:8px;}}")
        tb = QHBoxLayout(turn_bar); tb.setContentsMargins(10,6,10,6); tb.setSpacing(8)
        tb.addWidget(_lbl("TURN:", GOLD, FS_SMALL, bold=True, wrap=False))
        self._turn_chips = {}
        for bname, icon in [("Action","⚔"),("Bonus Action","✦"),("Reaction","⚡")]:
            chip = QPushButton(f"{icon} {bname}  ●")
            chip.setCheckable(False); chip.setMinimumHeight(28)
            chip.setAccessibleName(f"{bname} availability — click to toggle used")
            chip.setToolTip(f"Click to manually toggle your {bname} as used/available")
            chip.clicked.connect(lambda checked=False, b=bname: self._toggle_turn_slot(b))
            tb.addWidget(chip)
            self._turn_chips[bname] = chip
        self._haste_chip = _lbl("⚡ HASTE: +1 action", "#FFD34D", FS_SMALL, bold=True, wrap=False)
        self._haste_chip.setStyleSheet(
            f"background:#22FFD34D;border:1px solid #FFD34D;border-radius:6px;"
            f"padding:4px 8px;color:#FFD34D;font-weight:700;")
        self._haste_chip.setVisible(False)
        tb.addWidget(self._haste_chip)
        self._sneak_chip = QPushButton("🗡 Sneak Attack ●")
        self._sneak_chip.setMinimumHeight(28)
        self._sneak_chip.setToolTip("Rogue: once per turn. Click to toggle used.")
        self._sneak_chip.setAccessibleName("Sneak Attack availability — click to toggle")
        self._sneak_chip.clicked.connect(self._toggle_sneak)
        self._sneak_chip.setVisible(False)
        tb.addWidget(self._sneak_chip)
        tb.addStretch()
        new_turn = QPushButton("🔄 New Turn")
        new_turn.setMinimumHeight(30)
        new_turn.setAccessibleName("Start a new turn — resets action, bonus action, reaction and sneak attack")
        new_turn.setStyleSheet(_btn("", GREEN, variant="cta", text_color=GREEN2,
                                     hover_text="white", padding="2px 16px").styleSheet())
        new_turn.clicked.connect(self._new_turn)
        tb.addWidget(new_turn)
        root_lay.addWidget(turn_bar)

        splitter.addWidget(top_half)
        splitter.addWidget(self._action_tabs)
        self._combat_top_half = top_half
        # The Attacks/action-tabs area holds the variable-length content
        # (attacks, spells, abilities) a player needs to read during
        # play, so it gets the majority share of the default split, with
        # a minimum height so dragging the handle can't squeeze it down
        # to near-nothing. top_half (HP, conditions, resistance/movement
        # badges, etc.) can still be dragged larger if it has many
        # badges wrapping across rows.
        self._action_tabs.setMinimumHeight(320)
        splitter.setSizes([280, 460])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Other tab also hosts class resources, hit dice, and quick spells
        # They are injected via _build_resource_rows() during _refresh_action_tabs()
        root_lay.addWidget(splitter, 1)
        return tab


    def _do_damage(self):
        amt = self._hp_amt.value()
        cur = self._hp_current_hp.value()
        wild = self.char.get("_wildshape_active")
        max_hp = self.char.get("max_hp", 1)
        if wild:
            from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
            beast = WILDSHAPE_BEASTS.get(wild, {})
            max_hp = beast.get("hp", 1)
        # Instant death: damage ≥ 2× max HP (PHB p.197) — while Wild Shaped,
        # this checks against the BEAST's max HP (the creature actually
        # taking the hit), and simply reverts you to your normal form at
        # full awareness rather than killing you outright, per the Wild
        # Shape reversion rule; it only threatens actual death once
        # applied to your own HP after reverting.
        if amt >= max_hp * 2 and not wild:
            self.char["current_hp"] = 0
            self._hp_current_hp.setValue(0)
            self.ctrl.update("current_hp", 0, rebuild_char=False)
            self._show_death_screen()
            return
        # Temporary HP absorbs damage first (PHB p.198) — beast forms
        # don't have their own temp HP pool, only your own does, so this
        # only applies when not Wild Shaped.
        temp = self._hp_temp_hp.value()
        absorbed = 0
        if temp > 0 and not wild:
            absorbed = min(temp, amt)
            new_temp = temp - absorbed
            self._hp_temp_hp.setValue(new_temp)
            self.char["temp_hp"] = new_temp
            amt -= absorbed

        if wild:
            # Wild Shape (PHB p.66): if this damage would reduce the beast
            # to 0 HP or below, you revert to your normal form immediately,
            # and any EXCESS damage (beyond what the beast's remaining HP
            # could absorb) carries over to your own HP. You aren't
            # knocked unconscious unless that excess itself drops your own
            # HP to 0.
            if amt >= cur:
                excess = amt - cur
                self._wildshape_revert()
                own_max = self.char.get("max_hp", 1)
                own_cur = self.char.get("current_hp", own_max)
                own_new = max(0, own_cur - excess)
                self._hp_current_hp.setValue(own_new)
                self.ctrl.update("current_hp", own_new, rebuild_char=False)
                self._toast(f"🐾 Beast form dropped to 0 HP — reverted to normal form, "
                            f"{excess} excess damage carried over")
                if excess >= own_max * 2:
                    self._show_death_screen()
                    return
            else:
                new_hp = cur - amt
                self._hp_current_hp.setValue(new_hp)
                self.char["_wildshape_hp"] = new_hp
                self._mark_dirty()
            self._toast(f"Beast form took {amt} damage" if amt else "No damage")
            return

        # Rage Beyond Death (Zealot Barbarian, 14th level): while raging,
        # damage that would drop you to 0 instead leaves you at 1 — unless
        # the overkill portion of the damage (what's left after your
        # current HP is exhausted) itself exceeds your max HP, in which
        # case you're killed outright even through this protection.
        # Doesn't apply if Rage isn't currently active (toggled off = the
        # protection ends with it).
        from dnd_app.core.character import class_levels
        barb_lvl = class_levels(self.char).get("Barbarian", 0)
        is_zealot_14 = (barb_lvl >= 14
                         and any("zealot" in sub.lower()
                                 for cl in self.char.get("classes", [])
                                 for sub in [cl.get("subclass", "")]))
        is_raging = "Rage" in self.char.get("active_effects", [])
        overkill = amt - cur
        would_drop_to_0 = cur - amt <= 0

        if is_zealot_14 and is_raging and would_drop_to_0 and overkill < max_hp:
            new_hp = 1
            self._toast("🛡 Rage Beyond Death: damage would drop you to 0, but your rage "
                        "keeps you standing at 1 HP")
        elif (barb_lvl >= 11 and is_raging and would_drop_to_0 and overkill < max_hp):
            # Relentless Rage: a CON save (not a guarantee like Rage Beyond
            # Death) to drop to 1 HP instead of 0. DC starts at 10 and
            # rises by 5 each use since the last short/long rest.
            import random
            uses = self.char.get("_relentless_rage_uses", 0)
            dc = 10 + 5 * uses
            con_mod = ability_mod(self.char, "CON")
            roll = random.randint(1, 20)
            total = roll + con_mod
            self.char["_relentless_rage_uses"] = uses + 1
            self._mark_dirty()
            if total >= dc:
                new_hp = 1
                self._toast(f"🎲 Relentless Rage: DC {dc} CON save — rolled {roll}{sign(con_mod)}"
                            f" = {total}, SUCCESS — you drop to 1 HP instead of 0")
            else:
                new_hp = 0
                self._toast(f"🎲 Relentless Rage: DC {dc} CON save — rolled {roll}{sign(con_mod)}"
                            f" = {total}, FAILED — you drop to 0 HP")
        else:
            new_hp = max(0, cur - amt)
        self._hp_current_hp.setValue(new_hp)
        self.ctrl.update("current_hp", new_hp, rebuild_char=False)
        if absorbed and amt == 0:
            self._toast(f"🛡 Temp HP absorbed all {absorbed} damage")
        elif absorbed:
            self._toast(f"🛡 Temp HP absorbed {absorbed}, took {amt} damage")

        conc_spell = self.char.get("concentration", {}).get("spell")
        if conc_spell:
            roll, ok = QInputDialog.getInt(
                self, "Concentration Save",
                f"Concentrating on {conc_spell}. Enter your d20 roll (modifier applied automatically):",
                10, 1, 30,
            )
            if ok:
                from dnd_app.core.calculator import get_saving_throw_bonus
                import random
                if roll <= 0:
                    roll = random.randint(1, 20)
                dc = max(10, amt // 2)
                total = roll + get_saving_throw_bonus(self.char, "CON")
                if total >= dc:
                    QMessageBox.information(
                        self, "Concentration",
                        f"Maintained on {conc_spell}.\n{roll} + modifier = {total} vs DC {dc}",
                    )
                else:
                    drop_concentration(self.char)
                    self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
                    QMessageBox.warning(
                        self, "Concentration Broken",
                        f"Failed ({total} vs DC {dc}). Dropped {conc_spell}.",
                    )
                    self._refresh_concentration()
                    self._toast("Your focus shatters like cheap glass.")
        self._mark_dirty()

    def _roll_initiative(self):
        """Roll d20 + initiative bonus — shown as a non-blocking toast."""
        self._quick_roll_toast("Initiative", get_initiative(self.char))

    def _do_heal(self):
        amt = self._hp_amt.value()
        cur = self._hp_current_hp.value()
        wild = self.char.get("_wildshape_active")
        if wild:
            from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
            beast_max = WILDSHAPE_BEASTS.get(wild, {}).get("hp", cur)
            new_hp = min(beast_max, cur + amt)
            self._hp_current_hp.setValue(new_hp)
            self.char["_wildshape_hp"] = new_hp
            self._mark_dirty()
            return
        mx = self._hp_max_hp.value()
        new_hp = min(mx, cur + amt)
        # Healing from 0 HP: regain consciousness, death saves reset (PHB p.197)
        if cur == 0 and new_hp > 0:
            self.char["death_saves"] = {"successes": 0, "failures": 0}
            for cb in self._death_success + self._death_fail:
                cb.setChecked(False)
            self._toast(f"💚 Back on your feet! Death saves reset")
        self._hp_current_hp.setValue(new_hp)
        self.ctrl.update("current_hp", new_hp, rebuild_char=False)

    # ═══ Turn tracker ══════════════════════════════════════════════════════
    def _turn_limit(self, bucket: str) -> int:
        from dnd_app.core.effects import has_extra_action
        if bucket == "Action" and has_extra_action(self.char):
            return 2
        return 1

    def _mark_turn_used(self, bucket: str):
        """Consume one use of an action-economy slot; grey the bucket when spent."""
        if bucket not in self._turn_counts:
            return
        limit = self._turn_limit(bucket)
        if self._turn_counts[bucket] >= limit:
            return
        self._turn_counts[bucket] += 1
        if bucket == "Action" and limit == 2 and self._turn_counts[bucket] == 1:
            self._toast("⚡ Haste: first action used — one more available")
        self._apply_turn_state()

    def _toggle_turn_slot(self, bucket: str):
        limit = self._turn_limit(bucket)
        self._turn_counts[bucket] = 0 if self._turn_counts[bucket] >= limit else limit
        self._apply_turn_state()

    def _toggle_sneak(self):
        self._sneak_used = not getattr(self, "_sneak_used", False)
        self._apply_turn_state()

    def _new_turn(self):
        for k in self._turn_counts: self._turn_counts[k] = 0
        self._sneak_used = False
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        self.char["_action_surge_used_this_turn"] = False
        # Reckless Attack lasts only the turn it was activated on
        fx = self.char.get("active_effects", [])
        if "Reckless Attack" in fx:
            fx.remove("Reckless Attack")
            self._refresh_combat_weapons()
        self._apply_turn_state()
        self._toast("🔄 New turn — action, bonus & reaction ready")

    def _apply_turn_state(self):
        """Grey out Use/Cast buttons in spent buckets; refresh chips."""
        if not hasattr(self, "_turn_chips"):
            return
        from dnd_app.core.character import class_levels
        ICONS = {"Action":"⚔","Bonus Action":"✦","Reaction":"⚡"}
        for bname, chip in self._turn_chips.items():
            limit = self._turn_limit(bname)
            used  = self._turn_counts.get(bname, 0)
            free  = used < limit
            marker = "●" * max(0, limit-used) + "○" * used
            chip.setText(f"{ICONS[bname]} {bname}  {marker}")
            col = GREEN2 if free else TEXT2
            chip.setStyleSheet(
                f"QPushButton{{background:{qa(col,0x1e)};border:2px solid {col};"
                f"border-radius:6px;color:{col};font-weight:700;padding:2px 10px;}}"
                f"QPushButton:hover{{border-color:{TEAL2};}}"
                f"QPushButton:focus{{border:2px solid {TEAL2};}}")
            # Grey the bucket's buttons + dim cards
            for btn in getattr(self, "_bucket_use_btns", {}).get(bname, []):
                try:
                    btn.setEnabled(free)
                    if not free and btn.text() not in ("✓",):
                        btn.setProperty("_orig_text", btn.text()); btn.setText("✓")
                    elif free and btn.property("_orig_text"):
                        btn.setText(btn.property("_orig_text"))
                except RuntimeError:
                    pass
        # Haste chip
        from dnd_app.core.effects import has_extra_action
        self._haste_chip.setVisible(has_extra_action(self.char))
        # Sneak chip (rogues only): hidden while Wild Shaped, since Sneak
        # Attack requires a finesse or ranged weapon and natural weapons
        # never qualify. Also hidden if nothing currently equipped qualifies.
        rogue_lvl = class_levels(self.char).get("Rogue", 0)
        has_qualifying_weapon = False
        if rogue_lvl > 0:
            from dnd_app.data.phbCommon.items import WEAPON_DICT
            from dnd_app.core.magic_items import parse_magic_suffix
            for wpn_name in self.char.get("equipped_weapons", []):
                base_name, _ = parse_magic_suffix(wpn_name)
                wpn = WEAPON_DICT.get(base_name)
                if not wpn:
                    continue
                props = wpn.get("properties", [])
                is_finesse = any("finesse" in str(p).lower() for p in props)
                if base_name == "Double-Bladed Scimitar" and "Revenant Blade" in self.char.get("feats", []):
                    is_finesse = True
                is_ranged = "ranged" in str(wpn.get("category", "")).lower()
                if is_finesse or is_ranged:
                    has_qualifying_weapon = True
                    break
        if rogue_lvl > 0 and not self.char.get("_wildshape_active") and has_qualifying_weapon:
            dice = (rogue_lvl + 1) // 2
            used = getattr(self, "_sneak_used", False)
            self._sneak_chip.setVisible(True)
            self._sneak_chip.setText(f"🗡 Sneak {dice}d6  {'○ used' if used else '● ready'}")
            col = TEXT3 if used else PURP2
            self._sneak_chip.setStyleSheet(
                f"QPushButton{{background:{qa(col,0x1e)};border:2px solid {col};"
                f"border-radius:6px;color:{col};font-weight:700;padding:2px 10px;}}"
                f"QPushButton:focus{{border:2px solid {TEAL2};}}")
        else:
            self._sneak_chip.setVisible(False)

    # ═══ Active spell effects ═══════════════════════════════════════════════
    def _add_active_effect(self):
        from dnd_app.core.effects import EFFECT_TABLE
        typed = self._fx_combo.currentText().strip()
        if not typed: return
        # Editable QComboBox.currentText() returns whatever was typed, with
        # no guarantee it matches a real entry — a mistyped or misremembered
        # name must not silently create a bogus "active effect" that
        # doesn't correspond to anything real. Resolve it properly instead:
        # exact match first, then a forgiving case-insensitive match, and
        # only fall through to a warning toast (no effect added) if neither
        # finds anything real. The valid set isn't just EFFECT_TABLE — a few
        # toggles (Rage, Form of Dread, Starry Form, Hybrid Transformation)
        # are driven by resource-pool checkboxes elsewhere and have no
        # EFFECT_TABLE entry of their own, but typing "Rage" here should
        # still work rather than being rejected.
        valid_names = set(EFFECT_TABLE.keys()) | RESOURCE_POOL_TOGGLES
        name = None
        if typed in valid_names:
            name = typed
        else:
            for key in valid_names:
                if key.lower() == typed.lower():
                    name = key
                    break
        if name is None:
            self._toast(f"⚠ \"{typed}\" isn't a recognized effect — pick one from the list")
            return
        self.char.setdefault("active_effects", []).append(name)
        self.ctrl.refresh()          # AC pill etc. recompute
        self._refresh_effects_list()
        self._apply_turn_state()     # haste chip
        self._mark_dirty()
        self._toast(f"☄ {name} applied")

    def _remove_active_effect(self, name: str):
        fx = self.char.get("active_effects", [])
        if name in fx:
            fx.remove(name)
            # Berserker's Frenzy: if Rage ends while frenzied, gain 1
            # level of exhaustion and Frenzy itself ends (it can't outlast
            # the rage it was part of).
            frenzy_ended = False
            if name == "Rage" and "Frenzy" in fx:
                fx.remove("Frenzy")
                self.char["exhaustion"] = min(6, self.char.get("exhaustion", 0) + 1)
                frenzy_ended = True
            self.ctrl.refresh()
            self._refresh_effects_list()
            self._apply_turn_state()
            self._mark_dirty()
            if frenzy_ended:
                self._toast("😵 Rage removed — Frenzy ends with it, gain 1 level of exhaustion")
            else:
                self._toast(f"✖ {name} removed")

    def _refresh_effects_list(self):
        if not hasattr(self, "_fx_lay"): return
        from dnd_app.core.effects import EFFECT_TABLE
        while self._fx_lay.count() > 1:
            it = self._fx_lay.takeAt(0)
            w = it.widget()
            if w:
                w.hide(); w.setParent(None); w.deleteLater()
        fx = self.char.get("active_effects", [])
        if not fx:
            self._fx_lay.insertWidget(0, _lbl(
                "No active effects. Pick a spell above (Haste, Shield of Faith, "
                "Enlarge…) — AC, speed and the turn tracker update automatically.",
                TEXT3, FS_SMALL, wrap=True))
            return
        for i, name in enumerate(fx):
            info = EFFECT_TABLE.get(name, {})
            row = QFrame()
            col = TEAL2 if info else AMBE2
            row.setStyleSheet(f"QFrame{{background:{qa(col,0x11)};border:1px solid {qa(col,0x44)};"
                              f"border-radius:8px;}}")
            rl = QHBoxLayout(row); rl.setContentsMargins(10,7,8,7); rl.setSpacing(8)
            head = name + ("  ©" if info.get("conc") else "")
            tcol = QVBoxLayout(); tcol.setSpacing(1)
            tcol.addWidget(_lbl(head, GOLD, FS_BODY, bold=True, wrap=False))
            note = info.get("note", "Custom effect — tracked, no automatic numbers.")
            tcol.addWidget(_lbl(note, TEXT2, FS_TINY, wrap=True))
            rm = QPushButton("✕ End"); rm.setMinimumHeight(28); rm.setMinimumWidth(58)
            rm.setAccessibleName(f"End the {name} effect")
            rm.setStyleSheet(
                _btn("", CRIMSON, variant="danger", bg_alpha=0x22, text_color=CRIM2,
                     hover_text="white", padding="0px").styleSheet()
                + f"QPushButton:focus{{border:2px solid {TEAL2};}}")
            rm.clicked.connect(lambda checked=False, n=name: self._remove_active_effect(n))
            rl.addLayout(tcol, 1); rl.addWidget(rm, 0, Qt.AlignTop)
            self._fx_lay.insertWidget(i, row)

    _EXHAUSTION_EFFECTS = {
        0: "",
        1: "Disadvantage on ability checks.",
        2: "Disadvantage on ability checks. Speed halved.",
        3: "Disadvantage on ability checks, attack rolls, and saving throws. Speed halved.",
        4: "Disadvantage on ability checks, attack rolls, and saving throws. "
           "Speed halved. Hit point maximum halved.",
        5: "Disadvantage on ability checks, attack rolls, and saving throws. "
           "Speed 0. Hit point maximum halved.",
        6: "💀 Death.",
    }

    def _on_exhaustion_changed(self, v: int):
        self.char["exhaustion"] = v
        self._refresh_exhaustion_label()
        self._refresh_active_conditions()
        self.ctrl.refresh()   # recompute max HP / speed / apply death check
        self._mark_dirty()
        if v >= 6:
            self._toast("💀 Exhaustion level 6 — the character has died")
            self._show_death_screen()
        elif v >= 4:
            self._toast(f"⚠ Exhaustion {v}: hit point maximum halved")

    def _refresh_exhaustion_label(self):
        if not hasattr(self, "_exh_effect_lbl"):
            return
        lvl = self.char.get("exhaustion", 0)
        self._exh_effect_lbl.setText(self._EXHAUSTION_EFFECTS.get(lvl, ""))

    def _refresh_active_conditions(self):
        """Populate the readable "Active Conditions" badge section — one
        badge per checked condition checkbox, plus exhaustion (if its
        level is above 0), each with the condition's full effect text
        (from the same data wired into the checkboxes' own tooltips)
        shown on hover."""
        if not hasattr(self, "_active_cond_lay"):
            return
        while self._active_cond_lay.count():
            item = self._active_cond_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)

        def _badge(text, tooltip):
            b = _lbl(text, CRIM2, FS_SMALL, bold=True, wrap=False)
            b.setStyleSheet(
                f"background:{qa(CRIMSON,0x33)};border:1.5px solid {qa(CRIMSON,0x99)};"
                f"border-radius:5px;padding:3px 8px;color:{CRIM2};"
                f"font-size:{FS_SMALL}px;font-weight:700;")
            b.setToolTip(tooltip)
            return b

        active = []
        for cname, cb in self._cond_checks.items():
            if cb.isChecked():
                active.append((cname, cb.toolTip()))
        lvl = self.char.get("exhaustion", 0)
        if lvl > 0:
            active.append((f"Exhaustion ({lvl})", self._EXHAUSTION_EFFECTS.get(lvl, "")))

        self._active_cond_none_lbl.setVisible(not active)
        self._active_cond_frame.setVisible(bool(active))
        for i, (name, tip) in enumerate(sorted(active)):
            self._active_cond_lay.addWidget(_badge(name, tip), i // 2, i % 2)

    def _reset_max_hp_override(self):
        """Clear the manual Max HP override and let it auto-calculate again."""
        self.char.pop("hp_max_override", None)
        from dnd_app.core.calculator import update_all
        update_all(self.char)
        if hasattr(self, "_hp_max_hp"):
            self._hp_max_hp.blockSignals(True)
            self._hp_max_hp.setValue(self.char.get("max_hp", 0))
            self._hp_max_hp.blockSignals(False)
        if hasattr(self, "_hp_current_hp"):
            self._hp_current_hp.blockSignals(True)
            self._hp_current_hp.setValue(self.char.get("current_hp", 0))
            self._hp_current_hp.blockSignals(False)
        self._update_hp_bar()
        self._mark_dirty()
        self._toast("↺ Max HP reset to auto-calculated value")

    def _on_max_hp_changed(self, v: int):
        """Manual Max HP edits set hp_max_override, which update_all() respects
        and will not silently overwrite on the next refresh (see calculator.py)."""
        char = self.char
        old_max = char.get("max_hp", v)
        char["hp_max_override"] = v
        char["max_hp"] = v
        # Keep current HP sane relative to the new max (mirror the auto-calc rule)
        diff = v - old_max
        if diff > 0:
            char["current_hp"] = min(char.get("current_hp", v) + diff, v)
        else:
            char["current_hp"] = min(char.get("current_hp", v), v)
        if hasattr(self, "_hp_current_hp"):
            self._hp_current_hp.blockSignals(True)
            self._hp_current_hp.setValue(char["current_hp"])
            self._hp_current_hp.blockSignals(False)
        self._update_hp_bar()
        self._mark_dirty()

    def _update_hp_bar(self):
        """Live green→amber→red HP bar; safe to call from any HP change."""
        if not hasattr(self, "_hp_bar"): return
        mx  = self._hp_max_hp.value()
        cur = self._hp_current_hp.value()
        pct = max(0, min(100, round(cur * 100 / mx))) if mx > 0 else 0
        self._hp_bar.setValue(pct)
        bar_col = GREEN2 if pct > 50 else (AMBER if pct > 25 else CRIM2)
        self._hp_bar.setStyleSheet(
            f"QProgressBar{{background:{SURF2};border:none;border-radius:4px;}}"
            f"QProgressBar::chunk{{border-radius:4px;background:{bar_col};}}")

    # ── Toast notifications (non-blocking) ────────────────────────────────────
    def _spend_hit_die(self, die_key: str):
        import random
        hd = self.char.get("hit_dice", {}).get(die_key)
        if not hd or hd.get("remaining", 0) <= 0:
            return
        sides = int(die_key[1:])
        roll = random.randint(1, sides)
        con = ability_mod(self.char, "CON")
        # Durable: the die roll itself (before CON is added) has a floor of 2x CON modifier (min 2).
        if "Durable" in self.char.get("feats", []):
            roll = max(roll, 2 * con, 2)
        heal = max(0, roll + con)
        # Dwarven Fortitude: guarantees at least 1 HP healed (the standard
        # hit-die-spend formula allows 0). This app doesn't track "when"
        # a hit die is spent, so the Dodge-triggered part of this feat
        # works through this same button; only this floor differs from the norm.
        if "Dwarven Fortitude" in self.char.get("feats", []):
            heal = max(1, roll + con)
        # Vigor of the Hill Giant: extra HP = CON modifier + proficiency
        # bonus when spending a Hit Die during a short rest ("Iron Stomach").
        if "Vigor of the Hill Giant" in self.char.get("feats", []):
            from dnd_app.core.calculator import get_prof_bonus
            heal += con + get_prof_bonus(self.char)
        hd["remaining"] -= 1
        cur, mx = self.char.get("current_hp", 0), self.char.get("max_hp", 0)
        self.char["current_hp"] = min(mx, cur + heal)
        if hasattr(self, "_hp_current_hp"):
            self._hp_current_hp.setValue(self.char["current_hp"])
        self._toast(f"🎲 Spent {die_key}: rolled {roll} {con:+d} CON → healed {heal} HP "
                    f"({hd['remaining']} dice left)")
        self._mark_dirty()
        self._refresh_action_tabs()
        if hasattr(self, "_hd_layout"):
            self._refresh_hit_dice()

    # ── Quick d20 roll with toast (skills / saves / abilities / initiative) ───
    def _add_weapon_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("Add Weapon"); dlg.setMinimumWidth(400)
        dlg.setStyleSheet(self.styleSheet())
        l = QVBoxLayout(dlg)
        l.addWidget(_lbl("Choose a weapon to equip:", TEXT, FS_BODY))
        combo = QComboBox()
        for (name,cat,dmg,dmg_type,cost,wt,props) in ALL_WEAPONS:
            combo.addItem(f"{name} — {dmg} {dmg_type}", name)
        l.addWidget(combo)
        # Material modifier costs: Adamantine +500gp, Silvered +100gp.
        l.addWidget(_lbl("Material (optional):", TEXT, FS_BODY))
        material_combo = QComboBox()
        material_combo.addItem("None (+0 gp)", "")
        material_combo.addItem("Adamantine (+500 gp)", "Adamantine")
        material_combo.addItem("Silvered (+100 gp)", "Silvered")
        l.addWidget(material_combo)
        cost_lbl = _lbl("", TEXT2, FS_SMALL)
        l.addWidget(cost_lbl)
        def _update_cost(*_):
            base_cost = next((c for (n,cat,dmg,dmg_type,wt,c,props) in ALL_WEAPONS if n == combo.currentData()), 0)
            extra = {"": 0, "Adamantine": 500, "Silvered": 100}[material_combo.currentData()]
            cost_lbl.setText(f"Cost: {base_cost + extra} gp" if (base_cost or extra) else "")
        combo.currentIndexChanged.connect(_update_cost)
        material_combo.currentIndexChanged.connect(_update_cost)
        _update_cost()
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        l.addWidget(btns)
        if dlg.exec():
            base_name = combo.currentData()
            material = material_combo.currentData()
            wpn_name = f"{material} {base_name}" if material else base_name
            equipped = self.char.setdefault("equipped_weapons", [])
            if wpn_name in equipped:
                QMessageBox.information(self, "Weapon", f"{wpn_name} is already equipped.")
                return
            equipped.append(wpn_name)
            self._add_weapon_row(wpn_name)
            self._mark_dirty()

    def _add_onhit_damage_badges(self, rl):
        """Append a separate badge for each passive on-hit damage bonus
        (Divine Strike, Genie's Wrath, Dreadful Strikes) to a weapon row's
        layout. Deliberately separate from the base weapon damage label —
        these are often a different damage type, which matters for
        resistance/immunity, so combining them into one number would hide
        that. Shared by every weapon-row-building method in this class."""
        for bonus in get_onhit_damage_bonuses(self.char):
            badge = _lbl(f"+{bonus['die']} {bonus['damage_type']}", TEAL2, FS_SMALL, wrap=False)
            badge.setToolTip(f"{bonus['name']} (once per turn on a hit)")
            rl.addWidget(badge)

    def _add_weapon_row(self, wpn_name, is_offhand=False):
        from dnd_app.core.magic_items import parse_magic_suffix, parse_material_prefix
        base_wpn_name, magic_bonus = parse_magic_suffix(wpn_name)
        # "Silvered X"/"Adamantine X" aren't recognized by the weapon
        # lookup on their own (only the "+1"/"+2"/"+3" suffix is), so the
        # material prefix is stripped here (after the magic suffix, so
        # "Silvered Longsword +1" parses correctly) to find the real base weapon.
        base_wpn_name, weapon_material = parse_material_prefix(base_wpn_name)
        # Check for an active infusion targeting this weapon (Enhanced
        # Weapon, Radiant Weapon, Repeating Shot, Returning Weapon) and
        # apply its real "+N" attack/damage bonus, using the higher of
        # the two if both are present.
        from dnd_app.core.calculator import get_infusion_bonus, class_levels
        art_lvl_wr = class_levels(self.char).get("Artificer", 0)
        for inf in self.char.get("active_infusions", []):
            if inf.get("target_item") == wpn_name:
                inf_bonus = get_infusion_bonus(inf.get("infusion", ""), art_lvl_wr)
                magic_bonus = max(magic_bonus, inf_bonus)
        wpn = next((w for w in ALL_WEAPONS if w[0]==base_wpn_name), None)
        is_named_magic_fallback = wpn is None
        if not wpn:
            # Named magic weapon (e.g. "Sun Blade", "Armblade") — render a generic
            # magic-blade profile instead of silently dropping it. These items'
            # own flavor text typically grants proficiency regardless of class
            # (e.g. Armblade: "counts as a simple weapon you are proficient
            # with"), so we treat named-fallback weapons as always-proficient.
            nb = self.char.get("_named_weapon_bonuses", {}).get(wpn_name, 0)
            wpn = (wpn_name, "Melee (magic)", "1d8", "radiant" if "sun" in wpn_name.lower() else "slashing",
                   0, 0, ["Finesse"] if nb else [])
        name,cat,dmg,dmg_type,_,_,props = wpn
        props = list(props or [])
        # Thrown Arms Master: simple/martial melee weapons without the
        # Thrown property gain it; weapons that already have it get an
        # extended range instead.
        if "Thrown Arms Master" in self.char.get("feats", []) and "Melee" in cat:
            has_thrown_already = any("Thrown" in str(p) for p in props)
            is_two_handed_tam = "Two-Handed" in props
            if not has_thrown_already:
                props.append(f"Thrown ({'15/30' if is_two_handed_tam else '20/60'} ft, Thrown Arms Master)")
            else:
                for i, p in enumerate(props):
                    if "Thrown" in str(p):
                        import re as _re_tam
                        m = _re_tam.search(r'\((\d+)/(\d+)', str(p))
                        if m:
                            near, far = int(m.group(1)), int(m.group(2))
                            props[i] = _re_tam.sub(r'\(\d+/\d+', f'({near+20}/{far+40}', str(p))
        from dnd_app.core.calculator import has_weapon_proficiency
        pb_full = get_prof_bonus(self.char)
        proficient = is_named_magic_fallback or has_weapon_proficiency(self.char, base_wpn_name, cat)
        pb = pb_full if proficient else 0
        is_finesse = "Finesse" in (props or [])
        # Revenant Blade: grants Finesse to the Double-Bladed Scimitar specifically (it doesn't have Finesse by default).
        if base_wpn_name == "Double-Bladed Scimitar" and "Revenant Blade" in self.char.get("feats", []):
            is_finesse = True
        is_ranged  = "Ranged" in cat
        is_thrown  = any("Thrown" in str(p) for p in (props or []))
        is_two_handed_hw = "Two-Handed" in (props or [])
        # Hex Warrior (Warlock, The Hexblade, 1st level): use CHA instead
        # of STR/DEX for a non-two-handed weapon's attack/damage rolls.
        warlock_lvl_hw = class_levels(self.char).get("Warlock", 0)
        is_hexblade = "hexblade" in subclasses(self.char).get("Warlock", "").lower()
        # Battle Ready (Artificer, Battle Smith, 3rd level): use INT
        # instead of STR/DEX for attack/damage rolls with a magic
        # weapon. Checks every path this app tracks magic weapons
        # through: a "+N" suffix, a named-fallback item (not in the
        # mundane weapon list at all), presence in magic_items, or an
        # infusion-marked equipment entry.
        art_lvl_br = class_levels(self.char).get("Artificer", 0)
        is_battlesmith = "battle smith" in subclasses(self.char).get("Artificer", "").lower()
        is_magic_weapon = bool(magic_bonus) or is_named_magic_fallback
        if not is_magic_weapon:
            mi_names = {(i.get("name") if isinstance(i, dict) else i) for i in self.char.get("magic_items", [])}
            if wpn_name in mi_names or base_wpn_name in mi_names:
                is_magic_weapon = True
            for eq in self.char.get("equipment", []):
                if eq.get("name") in (wpn_name, base_wpn_name) and eq.get("magic"):
                    is_magic_weapon = True
                    break
        if warlock_lvl_hw >= 1 and is_hexblade and not is_two_handed_hw:
            stat = "CHA"
        elif art_lvl_br >= 3 and is_battlesmith and is_magic_weapon:
            stat = "INT"
        else:
            stat = "DEX" if (is_finesse and ability_mod(self.char,"DEX")>ability_mod(self.char,"STR")) or is_ranged else "STR"
        mod = ability_mod(self.char, stat)

        # Check if this weapon is a named magic item with an effect-based bonus
        # (e.g. "Sun Blade" gives +2 independent of the "+N" suffix system)
        named_bonuses = self.char.get("_named_weapon_bonuses", {})
        named_bonus = named_bonuses.get(wpn_name, 0) or named_bonuses.get(base_wpn_name, 0)
        total_bonus = magic_bonus + named_bonus

        # Archery fighting style: +2 to ranged weapon attack rolls.
        fighting_styles = self.char.get("fighting_styles", [])
        has_archery = is_ranged and any("archery" in fs.lower() for fs in fighting_styles)
        atk_style_bonus = 2 if has_archery else 0

        # Sacred Weapon (Paladin, Oath of Devotion): Channel Divinity —
        # while active, add CHA mod to attack rolls with the touched
        # weapon.
        sacred_weapon_bonus = 0
        if "Sacred Weapon" in self.char.get("active_effects", []):
            sacred_weapon_bonus = ability_mod(self.char, "CHA")

        # Great Weapon Master / Sharpshooter: -5 to attack, +10 to
        # damage, toggleable per weapon (the real rule is decided per
        # attack, not a character-wide stance). GWM requires a heavy
        # melee weapon; Sharpshooter requires a ranged weapon; both
        # require proficiency.
        is_heavy = "Heavy" in (props or [])
        char_feats = self.char.get("feats", [])
        can_power_attack = proficient and (
            ("Great Weapon Master" in char_feats and not is_ranged and is_heavy) or
            ("Sharpshooter" in char_feats and is_ranged))
        power_attack_active = can_power_attack and wpn_name in self.char.get("power_attack_weapons", [])
        power_attack_atk = -5 if power_attack_active else 0
        power_attack_dmg = 10 if power_attack_active else 0

        atk = sign(pb + mod + total_bonus + atk_style_bonus + sacred_weapon_bonus + power_attack_atk)
        prof_note = "" if proficient else "  (not proficient — no prof. bonus)"
        # Display the weapon under its full enchanted name (e.g. "Longsword +1")
        name = wpn_name

        # ── Ammo type for this weapon ─────────────────────────────────────────
        _AMMO_KEY = {
            "Shortbow":        "arrows",  "Longbow":         "arrows",
            "Light Crossbow":  "bolts",   "Hand Crossbow":   "bolts",
            "Heavy Crossbow":  "bolts",   "Sling":           "bullets",
            "Blowgun":         "needles", "Pistol":          "bullets_modern",
            "Musket":          "bullets_modern", "Revolver": "bullets_modern",
            "Hunting Rifle":   "bullets_modern", "Automatic Rifle": "bullets_modern",
            "Laser Pistol":    "energy_cells",   "Laser Rifle":     "energy_cells",
            "Antimatter Rifle":"energy_cells",
        }
        _AMMO_LABEL = {
            "arrows":         "Arrows",       "bolts":          "Bolts",
            "bullets":        "Sling Bullets","needles":        "Needles",
            "bullets_modern": "Bullets",      "energy_cells":   "Energy Cells",
        }
        _AMMO_EQUIP_NAMES = {
            "arrows":         ["Arrows","Arrow","Arrows (20)","Ammunition, Arrows (20)"],
            "bolts":          ["Bolts","Bolt","Bolts (20)","Crossbow Bolts (20)","Ammunition, Bolts (20)"],
            "bullets":        ["Sling Bullets","Sling Bullets (20)","Bullets"],
            "needles":        ["Needles","Blowgun Needles (50)"],
            "bullets_modern": ["Bullets (Modern)","Bullets"],
            "energy_cells":   ["Energy Cell","Energy Cells"],
        }
        ammo_key = _AMMO_KEY.get(base_wpn_name, "") if is_ranged and not is_thrown else ""

        # Seed ammo tracker from equipment list if currently at 0
        if ammo_key and self.char.get("ammo", {}).get(ammo_key, 0) == 0:
            for eq in self.char.get("equipment", []):
                if not isinstance(eq, dict): continue
                eq_name = eq.get("name","")
                if any(eq_name.lower() == n.lower() for n in _AMMO_EQUIP_NAMES.get(ammo_key,[])):
                    self.char.setdefault("ammo", {})[ammo_key] = eq.get("qty", 0)
                    break

        row_f = QFrame()
        row_f.setStyleSheet(f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(name, TEXT, FS_BODY, bold=True, wrap=False))
        from dnd_app.core.calculator import get_condition_attack_status
        cond_status = get_condition_attack_status(self.char)
        atk_text = f"{atk} to hit"
        if cond_status["advantage"]:
            atk_text += "  (ADV)"
        elif cond_status["disadvantage"]:
            atk_text += "  (DISADV)"
        atk_lbl = _lbl(atk_text, TEAL2 if proficient else AMBER, FS_BODY, wrap=False)
        if not proficient:
            atk_lbl.setToolTip(
                f"Not proficient with {name} — proficiency bonus (+{pb_full}) "
                f"is not added to this attack roll.")
        elif cond_status["sources"]:
            reason = cond_status["note"] or f"Source: {', '.join(cond_status['sources'])}"
            atk_lbl.setToolTip(reason)
        else:
            atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _prof=proficient, _bonus=total_bonus, _atk=atk:
            self._show_breakdown_popup(f"{name} — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, _prof, _bonus), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        if "Reckless Attack" in self.char.get("active_effects", []) and not is_ranged and stat == "STR":
            reckless_badge = _lbl("⚔ Reckless (adv)", GOLD2, FS_TINY, bold=True, wrap=False)
            reckless_badge.setToolTip("Reckless Attack is active: advantage on this attack, "
                                       "but attack rolls against you also have advantage until your next turn.")
            rl.addWidget(reckless_badge)
        # Dueling fighting style: +2 damage when wielding a one-handed
        # melee weapon (not Two-Handed) and no other weapon equipped.
        is_two_handed = "Two-Handed" in (props or [])
        only_weapon = len(self.char.get("equipped_weapons", [])) == 1
        has_dueling = (not is_ranged and not is_two_handed and only_weapon and
                       any("dueling" in fs.lower() for fs in fighting_styles))
        dueling_bonus = 2 if has_dueling else 0

        # Rage: melee weapon attacks using Strength get a damage bonus
        # while raging, from get_rage_damage().
        rage_active = "Rage" in self.char.get("active_effects", [])
        rage_bonus = 0
        if rage_active and not is_ranged and stat == "STR":
            from dnd_app.core.calculator import get_rage_damage
            rage_str = get_rage_damage(self.char)
            if rage_str != "—":
                rage_bonus = int(rage_str.replace("+", ""))

        # Off-hand (second+ equipped weapon) damage: a positive ability
        # modifier is only added if Two-Weapon Fighting is selected — the
        # real rule is that you DON'T add it for the bonus-action off-hand
        # attack unless you have this style, though a negative modifier
        # still applies regardless (it's a penalty, not a bonus you can
        # opt out of).
        has_twf = any("two-weapon fighting" in fs.lower() for fs in fighting_styles)
        offhand_mod = mod if (not is_offhand or mod < 0 or has_twf) else 0
        dmg_total_mod = offhand_mod + total_bonus + dueling_bonus + rage_bonus + power_attack_dmg
        dmg_display = f"{dmg}+{dmg_total_mod}" if dmg_total_mod >= 0 else f"{dmg}{dmg_total_mod}"
        rl.addWidget(_lbl(f"{dmg_display} {dmg_type}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        # Weapon-type-specific item bonuses (e.g. Bracers of Archery's +2
        # damage on bow attacks), shown only on weapon rows matching the
        # item's restriction rather than as a general character-wide badge.
        for wb in self.char.get("_weapon_damage_bonuses", []):
            wtype = wb.get("weapon_type", "").lower()
            if wtype and wtype in name.lower():
                wb_badge = _lbl(f"+{wb['value']} ({wb['source']})", TEAL2, FS_SMALL, wrap=False)
                wb_badge.setToolTip(f"{wb['source']}: +{wb['value']} damage with {wtype} weapons")
                rl.addWidget(wb_badge)
        if total_bonus:
            tip_src = wpn_name if named_bonus else f"+{total_bonus} enchantment"
            magic_badge = _lbl(f"✦ +{total_bonus}", AMBE2, FS_TINY, bold=True, wrap=False)
            magic_badge.setToolTip(f"Magical weapon: +{total_bonus} to attack and damage rolls\nSource: {tip_src}")
            rl.addWidget(magic_badge)
        if weapon_material:
            material_badge = _lbl(f"\u26cf {weapon_material}", TEAL2, FS_TINY, bold=True, wrap=False)
            if weapon_material == "Silvered":
                material_badge.setToolTip(
                    "Silvered weapon: this weapon's damage counts as silvered for the purpose "
                    "of overcoming a creature's resistance or immunity to nonmagical attacks "
                    "(e.g. many lycanthropes and certain other creatures).")
            else:
                material_badge.setToolTip(
                    "Adamantine weapon: whenever this weapon hits an object, the hit is a "
                    "critical hit.")
            rl.addWidget(material_badge)
        if can_power_attack:
            pa_cb = QCheckBox("Power Attack (-5/+10)")
            pa_cb.setChecked(power_attack_active)
            pa_cb.setStyleSheet(f"QCheckBox{{color:{CRIM2 if power_attack_active else TEXT3};font-size:{FS_TINY}px;font-weight:700;}}")
            pa_cb.setToolTip(
                f"{'Great Weapon Master' if not is_ranged else 'Sharpshooter'}: "
                "trade -5 to hit for +10 damage on this weapon's attacks.")
            def _on_power_attack_toggle(state, _wname=wpn_name):
                pa_list = self.char.setdefault("power_attack_weapons", [])
                if state and _wname not in pa_list:
                    pa_list.append(_wname)
                elif not state and _wname in pa_list:
                    pa_list.remove(_wname)
                self._mark_dirty()
                self._refresh_combat()
            pa_cb.stateChanged.connect(_on_power_attack_toggle)
            rl.addWidget(pa_cb)
        prop_str = ", ".join(str(p) for p in (props[:2] if props else []))
        if prop_str: rl.addWidget(_lbl(prop_str, TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        # ── Ammo counter (ranged non-thrown weapons) ──────────────────────────
        ammo_lbl = None
        if ammo_key:
            ammo_count = self.char.setdefault("ammo", {}).get(ammo_key, 0)
            ammo_lbl = QPushButton(f"\U0001f3f9 {_AMMO_LABEL.get(ammo_key,'Ammo')}: {ammo_count}")
            ammo_lbl.setStyleSheet(
                _btn("", AMBER, variant="chip", radius=5, text_color=AMBE2,
                     border_alpha=0x55, hover_bg_alpha=0x33, font_size=FS_TINY,
                     padding="2px 6px").styleSheet())
            ammo_lbl.setFixedHeight(26)
            def _add_ammo(checked=False, _key=ammo_key, _lbl=ammo_lbl,
                          _label=_AMMO_LABEL.get(ammo_key,"Ammo"),
                          _equip_names=_AMMO_EQUIP_NAMES.get(ammo_key,[])):
                n, ok = QInputDialog.getInt(
                    None, f"Restock {_label}",
                    f"Add how many {_label}?", 20, 0, 9999)
                if ok:
                    self.char.setdefault("ammo",{})[_key] = (
                        self.char["ammo"].get(_key, 0) + n)
                    # Sync to equipment list
                    total = self.char["ammo"][_key]
                    for _eq in self.char.get("equipment",[]):
                        if not isinstance(_eq,dict): continue
                        if any(_eq.get("name","").lower()==en.lower() for en in _equip_names):
                            _eq["qty"] = total; break
                    else:
                        # Add to equipment if not present
                        from dnd_app.data.phbCommon.items import ADVENTURING_GEAR as _AG
                        _ammo_cost = next((float(g[2] or 0) for g in _AG if g[0] == _label), 0.0)
                        self.char.setdefault("equipment",[]).append(
                            {"name":_label,"qty":total,"weight":0.02,"cost":_ammo_cost,"notes":""})
                    _lbl.setText(f"\U0001f3f9 {_label}: {total}")
                    self._mark_dirty()
            ammo_lbl.clicked.connect(_add_ammo)
            rl.addWidget(ammo_lbl)

        # ── Attack roll button ────────────────────────────────────────────────
        def _roll_hit(checked=False, _atk=atk, _name=name,
                      _ak=ammo_key, _al=ammo_lbl,
                      _ammo_lbl_ref=_AMMO_LABEL,
                      _equip_names=_AMMO_EQUIP_NAMES.get(ammo_key,[])):
            import random
            if _ak:
                cur = self.char.setdefault("ammo", {}).get(_ak, 0)
                if cur <= 0:
                    QMessageBox.warning(
                        None, "No Ammo",
                        "No " + _ammo_lbl_ref.get(_ak,"ammo") + " remaining!\n"
                        "Click the ammo counter to restock.")
                    return
                self.char["ammo"][_ak] = cur - 1
                new_qty = self.char["ammo"][_ak]
                # Sync to equipment
                for _eq in self.char.get("equipment",[]):
                    if not isinstance(_eq,dict): continue
                    if any(_eq.get("name","").lower()==en.lower() for en in _equip_names):
                        _eq["qty"] = max(0, new_qty); break
                if _al:
                    _al.setText(
                        f"\U0001f3f9 {_ammo_lbl_ref.get(_ak,'Ammo')}: {new_qty}")
                self._mark_dirty()
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name}\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", TEAL, variant="danger", height=26, width=60,
                        radius=5, border_width=1, text_color=TEAL2, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        # Attach the completed row to the combat tab (this line was lost in a
        # past refactor — without it every weapon row was built then dropped).
        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_martial_arts_row(self):
        """Monks always have an unarmed-strike attack available via Martial
        Arts, scaling in damage die by level and usable with STR or DEX
        (whichever is better) — but it never showed up as an actual attack,
        only as a passive 'die size' stat. Render it exactly like a real
        weapon row so it can be rolled the same way equipped weapons are."""
        from dnd_app.core.calculator import get_martial_arts_die, get_prof_bonus
        die = get_martial_arts_die(self.char)
        if die == "—":
            return
        pb = get_prof_bonus(self.char)   # monks are always proficient unarmed
        str_mod = ability_mod(self.char, "STR")
        dex_mod = ability_mod(self.char, "DEX")
        stat = "DEX" if dex_mod > str_mod else "STR"
        mod = max(str_mod, dex_mod)
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(TEAL,0x14)};border:1px solid {qa(TEAL,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Unarmed Strike", TEXT, FS_BODY, bold=True, wrap=False))
        ma_badge = _lbl("Martial Arts", TEAL2, FS_TINY, bold=True, wrap=False)
        ma_badge.setToolTip(f"Monk unarmed strikes use {stat} and scale with level "
                            f"— always proficient, never needs to be equipped.")
        rl.addWidget(ma_badge)
        ma_atk_lbl = _lbl(f"{atk} to hit", TEAL2, FS_BODY, wrap=False)
        ma_atk_lbl.setToolTip("Right-click for a breakdown")
        ma_atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _atk=atk:
            self._show_breakdown_popup("Unarmed Strike — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, True, 0), _atk, e.globalPos()))
        rl.addWidget(ma_atk_lbl)
        dmg_display = f"{die}+{mod}" if mod >= 0 else f"{die}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} bludgeoning", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl(f"({stat})", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Unarmed Strike\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", TEAL, variant="danger", height=26, width=60,
                        radius=5, border_width=1, text_color=TEAL2, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _refresh_hit_dice(self):
        """Rebuild hit dice spinboxes. Called only from _do_refresh_combat."""
        char = self.char
        while self._hd_layout.count():
            item = self._hd_layout.takeAt(0)
            if item.widget():  item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    si = item.layout().takeAt(0)
                    if si.widget(): si.widget().deleteLater()

        for c in char.get("classes", []):
            hd  = c.get("hit_die", 8)
            lvl = c.get("level", 1)
            hd_key  = f"d{hd}"
            hd_data = char.get("hit_dice", {}).get(hd_key, {"total": lvl, "remaining": lvl})
            col = QVBoxLayout()
            col.setSpacing(3)
            col.addWidget(_lbl(c["class"][:6], TEXT3, FS_TINY, bold=True, align=Qt.AlignCenter))
            sp = QSpinBox()
            sp.setRange(0, hd_data.get("total", lvl))
            sp.setValue(hd_data.get("remaining", lvl))
            sp.setFixedWidth(54); sp.setFixedHeight(32)
            sp.setAlignment(Qt.AlignCenter)
            sp.setStyleSheet(
                f"QSpinBox{{background:{SURF2};border:2px solid {qa(TEAL,0x66)};border-radius:6px;"
                f"font-weight:700;font-size:{FS_SMALL}px;color:{TEAL2};}}"
                f"QSpinBox::up-button,QSpinBox::down-button{{width:14px;background:{BORDER};}}")
            col.addWidget(_lbl(f"d{hd}", TEXT3, FS_TINY, align=Qt.AlignCenter))
            sp.valueChanged.connect(
                lambda v, k=hd_key, tot=hd_data.get("total", lvl):
                    self._on_hd_changed(k, v, tot))
            self._hd_layout.addLayout(col)

    def _add_hybrid_transformation_row(self):
        """Order of the Lycan's Hybrid Transformation grants a real unarmed
        attack (Predatory Strikes) that scales with level — shown as a real
        weapon row, same treatment as Monk's Martial Arts, only while the
        transformation is actually toggled active."""
        from dnd_app.core.calculator import get_prof_bonus, class_levels
        bh_lvl = class_levels(self.char).get("Blood Hunter", 0)
        if bh_lvl == 0:
            return
        die = "1d8" if bh_lvl >= 11 else "1d6"
        pb = get_prof_bonus(self.char)
        str_mod = ability_mod(self.char, "STR")
        dex_mod = ability_mod(self.char, "DEX")
        stat = "DEX" if dex_mod > str_mod else "STR"
        mod = max(str_mod, dex_mod)
        # Stalker's Prowess (7th): Improved Predatory Strikes, +1/+2/+3 to
        # attack rolls at 7th/11th/18th.
        atk_bonus = 3 if bh_lvl >= 18 else 2 if bh_lvl >= 11 else 1 if bh_lvl >= 7 else 0
        atk = sign(pb + mod + atk_bonus)
        # Feral Might: +1/+2/+3 melee damage at 3rd/11th/18th.
        dmg_bonus = 3 if bh_lvl >= 18 else 2 if bh_lvl >= 11 else 1
        dmg_mod = mod + dmg_bonus

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Unarmed Strike", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Hybrid Form", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip(f"Predatory Strikes: uses {stat}, always proficient. "
                         f"An active Crimson Rite can apply to this attack. "
                         f"You can also make one extra unarmed strike as a "
                         f"bonus action when you take the Attack action.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _atk=atk:
            self._show_breakdown_popup("Unarmed Strike (Hybrid Form) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, True, atk_bonus), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"{die}+{dmg_mod}" if dmg_mod >= 0 else f"{die}{dmg_mod}"
        rl.addWidget(_lbl(f"{dmg_display} bludgeoning or slashing", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl(f"({stat})", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Unarmed Strike (Hybrid Form)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", CRIM2, variant="danger", height=26, width=60,
                        radius=5, border_width=1, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_racial_natural_weapon_row(self):
        """Racial natural weapon traits (Aarakocra Talons, Tabaxi Claws,
        Lizardfolk Bite, Naga Bite+Constrict, etc.) as real weapon rows —
        computed attack bonus, rollable damage, same treatment as Martial
        Arts / Hybrid Transformation. Always shown when applicable; these
        aren't rage- or toggle-gated, they're just part of the character.
        Some races have more than one distinct natural attack, so this
        renders one row per entry rather than assuming exactly one."""
        from dnd_app.data.phbCommon.items import RACIAL_NATURAL_WEAPONS
        species = self.char.get("species") or self.char.get("race", "")
        weapons = list(RACIAL_NATURAL_WEAPONS.get(species, []))
        if species == "Simic Hybrid" and "Grappling Appendages" in self.char.get("_choices", {}).get("simic_enhancement_5th", []):
            weapons.append({"name": "Grappling Appendages", "die": "1d6", "damage_type": "bludgeoning", "stat": "STR",
                             "note": "Immediately after hitting, try to grapple as a bonus action. Can't wield weapons/cast with these appendages."})
        # Dragon Hide (XGE): retractable claws, usable as natural weapons.
        if "Dragon Hide" in self.char.get("feats", []):
            weapons.append({"name": "Dragon Hide Claws", "die": "1d4", "damage_type": "slashing", "stat": "STR",
                             "note": "Retractable claws (no action to extend/retract); replaces an unarmed strike's bludgeoning damage with slashing."})
        # Touch of Death (DM reward, Dark Gift): a level-scaling necrotic bonus on an unarmed strike.
        if "Touch of Death" in self.char.get("dm_rewards", []):
            from dnd_app.core.calculator import total_level as _tl_td
            _td_lvl = _tl_td(self.char)
            _td_dice = "4d10" if _td_lvl >= 17 else "3d10" if _td_lvl >= 11 else "2d10" if _td_lvl >= 5 else "1d10"
            weapons.append({"name": "Death Touch", "die": _td_dice, "damage_type": "necrotic (flat, not STR-modified)", "stat": "STR", "no_mod": True,
                             "note": f"Action: unarmed strike — on a hit, also deals {_td_dice} necrotic (in "
                                     f"addition to the normal unarmed strike damage). Ignores resistance to "
                                     f"necrotic damage."})
        for info in weapons:
            self._add_one_natural_weapon_row(info)

    def _unarmed_strike_blocked(self) -> bool:
        """Shared guard: Wild Shape and Hybrid Transformation (Blood
        Hunter, Order of the Lycan) both replace your entire body, so no
        ordinary Unarmed Strike variant applies while either is active."""
        if self.char.get("_wildshape_active"):
            return True
        if "Hybrid Transformation" in self.char.get("active_effects", []):
            return True
        return False

    def _is_dual_wielding(self) -> bool:
        """True if 2+ distinct weapons are currently equipped (both hands
        occupied by separate weapons) — per design, Unarmed Strike isn't
        offered while dual-wielding, since neither hand is free to throw
        a punch."""
        equipped = set(self.char.get("equipped_weapons", []))
        return len(equipped) >= 2

    def _add_unarmed_fighting_row(self):
        """Unarmed Fighting style: your unarmed strike becomes a real
        attack option dealing 1d6+STR (1d8+STR with both hands
        completely free — no weapon and no shield). Replaces the base
        Unarmed Strike rather than adding to it."""
        if self._unarmed_strike_blocked() or self._is_dual_wielding():
            return
        if not any("unarmed fighting" in fs.lower() for fs in self.char.get("fighting_styles", [])):
            return
        both_hands_free = (len(self.char.get("equipped_weapons", [])) == 0
                            and not self.char.get("shield", False))
        die = "1d8" if both_hands_free else "1d6"
        self._add_one_natural_weapon_row({
            "name": "Unarmed Strike", "die": die, "damage_type": "bludgeoning", "stat": "STR",
            "note": "Unarmed Fighting fighting style. 1d8 requires both hands completely free "
                    "(no weapon, no shield)."
        })

    def _add_tavern_brawler_row(self):
        """Tavern Brawler: your unarmed strike deals 1d4 instead of the
        normal flat damage. Replaces the base Unarmed Strike, same as
        Unarmed Fighting — if a character somehow has both, Unarmed
        Fighting wins, since its die is never worse (1d6/1d8 vs 1d4)."""
        if self._unarmed_strike_blocked() or self._is_dual_wielding():
            return
        if "Tavern Brawler" not in self.char.get("feats", []):
            return
        if any("unarmed fighting" in fs.lower() for fs in self.char.get("fighting_styles", [])):
            return  # Unarmed Fighting already covers this, and is strictly better
        from dnd_app.core.calculator import get_martial_arts_die
        if get_martial_arts_die(self.char) != "\u2014":
            return  # Monk Martial Arts already covers this
        self._add_one_natural_weapon_row({
            "name": "Unarmed Strike", "die": "1d4", "damage_type": "bludgeoning", "stat": "STR",
            "note": "Tavern Brawler feat. Hitting with this (or an improvised weapon) lets you "
                    "bonus-action attempt to grapple the target."
        })

    def _add_generic_unarmed_strike_row(self):
        """Every character always has a basic Unarmed Strike available —
        per the 2024 rules: attack bonus STR mod + proficiency bonus, 1 +
        STR mod bludgeoning damage on a hit. Only a fallback shown when
        nothing else (Monk Martial Arts, Unarmed Fighting, Tavern
        Brawler) already covers it, and is blocked under the same
        conditions as those (Wild Shape/Hybrid Transformation,
        dual-wielding two weapons)."""
        if self._unarmed_strike_blocked() or self._is_dual_wielding():
            return
        from dnd_app.core.calculator import get_martial_arts_die
        if get_martial_arts_die(self.char) != "\u2014":
            return
        if any("unarmed fighting" in fs.lower() for fs in self.char.get("fighting_styles", [])):
            return
        if "Tavern Brawler" in self.char.get("feats", []):
            return
        self._add_one_natural_weapon_row({
            "name": "Unarmed Strike", "die": "1", "damage_type": "bludgeoning", "stat": "STR",
            "note": "Basic Unarmed Strike (2024 rules): a punch, kick, headbutt, or similar blow. "
                    "Instead of damage, you can Grapple or Shove with it instead — see the Actions tab."
        })

    def _add_one_natural_weapon_row(self, info):
        pb = get_prof_bonus(self.char)
        stat = info["stat"]
        mod = ability_mod(self.char, stat)
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(TEAL2,0x14)};border:1px solid {qa(TEAL2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(info["name"], TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Natural Weapon", TEAL2, FS_TINY, bold=True, wrap=False)
        if info.get("note"):
            badge.setToolTip(info["note"])
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", TEAL2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _atk=atk:
            self._show_breakdown_popup(f"{info['name']} — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        if info.get("no_mod"):
            dmg_display = info['die']
        else:
            dmg_display = f"{info['die']}+{mod}" if mod >= 0 else f"{info['die']}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} {info['damage_type']}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl(f"({stat})", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk, _name=info["name"]):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name}\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", TEAL2, variant="danger", height=26, width=60,
                        radius=5, border_width=1, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_beast_form_row(self):
        """Path of the Beast's Form of the Beast grants a real natural
        weapon (Bite/Claws/Tail) while raging, with a computed attack bonus
        and damage. Only shown while the character is actually raging AND
        actually has Path of the Beast — checking only the Rage toggle and
        the stored choice isn't enough, since choice data can persist
        after a subclass swap and shouldn't grant the weapon on its own."""
        if "Rage" not in self.char.get("active_effects", []):
            return
        from dnd_app.core.character import subclasses
        barb_sub = subclasses(self.char).get("Barbarian", "")
        if "beast" not in barb_sub.lower():
            return
        pick = self.char.get("_choices", {}).get("beast_form_3", [])
        if not pick:
            return
        pick_text = pick[0]
        animal = pick_text.split("\u2013")[0].split("-")[0].strip()
        FORMS = {
            "Bite": {"die": "1d8", "damage_type": "piercing",
                     "note": "Once/turn when you hit a target below half HP, heal PB."},
            "Claws": {"die": "1d6", "damage_type": "slashing",
                      "note": "Once/turn, make one extra claw attack as part of the same Attack action."},
            "Tail": {"die": "1d8", "damage_type": "piercing",
                     "note": "Reach 10 ft. Reaction: roll a d8 and add it to your AC against one attack."},
        }
        info = FORMS.get(animal)
        if not info:
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(animal, TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Form of the Beast", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip(info["note"])
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup(f"{animal} (Form of the Beast) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"{info['die']}+{mod}" if mod >= 0 else f"{info['die']}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} {info['damage_type']}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk, _name=animal):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name} (Form of the Beast)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", CRIM2, variant="danger", height=26, width=60,
                        radius=5, border_width=1, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_battlerager_spikes_row(self):
        """Path of the Battlerager's armor spikes — a bonus-action attack
        while raging. Requires wearing spiked barbarian armor specifically,
        which doesn't exist as a tracked item in this app's magic item
        database, so this can't verify actual possession — shown whenever
        raging + this subclass, with the requirement noted in the tooltip
        rather than silently assumed."""
        if "Rage" not in self.char.get("active_effects", []):
            return
        from dnd_app.core.character import subclasses
        barb_sub = subclasses(self.char).get("Barbarian", "")
        if "battlerager" not in barb_sub.lower():
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Armor Spikes", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Battlerager Armor (Bonus Action)", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip("Requires wearing spiked barbarian armor while raging. "
                          "Also: when you grapple a creature with the Attack action "
                          "and succeed, the spikes deal it 3 piercing damage.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup("Armor Spikes (Battlerager Armor) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"1d4+{mod}" if mod >= 0 else f"1d4{mod}"
        rl.addWidget(_lbl(f"{dmg_display} piercing", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Armor Spikes (Battlerager Armor)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", CRIM2, variant="danger", height=26, width=60,
                        radius=5, border_width=1, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_armorer_model_row(self):
        """Artificer Armorer's Arcane Armor grants a built-in weapon
        depending on which model was chosen at 3rd level — Guardian's
        Thunder Gauntlets (1d8 thunder unarmed strike) or Infiltrator's
        Lightning Launcher (ranged 1d6 lightning). Always available once
        chosen, unlike Rage-gated natural weapons elsewhere."""
        from dnd_app.core.character import subclasses
        art_sub = subclasses(self.char).get("Artificer", "")
        if "armorer" not in art_sub.lower():
            return
        pick = self.char.get("_choices", {}).get("armorer_model_3", [])
        if not pick:
            return
        pick_text = pick[0].lower()
        is_guardian = "guardian" in pick_text
        is_infiltrator = "infiltrator" in pick_text
        if not (is_guardian or is_infiltrator):
            return

        pb = get_prof_bonus(self.char)
        # Both models use INT as the spellcasting-focus-driven attack
        # stat for these weapons per their real text (artificer's casting
        # ability), not STR/DEX.
        mod = ability_mod(self.char, "INT")
        atk = sign(pb + mod)
        name = "Thunder Gauntlets" if is_guardian else "Lightning Launcher"
        die = "1d8" if is_guardian else "1d6"
        dmg_type = "thunder" if is_guardian else "lightning"
        note = ("Target has disadvantage on attacks against creatures other than you until your next turn."
                if is_guardian else
                "Ranged 90/300 ft. Once per turn on a hit, deal an extra 1d6 lightning.")

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(PURPLE,0x14)};border:1px solid {qa(PURPLE,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(name, TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Armor Model", PURP2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip(note)
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", PURP2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup(f"{name} (Armor Model) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "INT", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"{die}+{mod}" if mod >= 0 else f"{die}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} {dmg_type}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(INT)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk, _name=name):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name} (Armor Model)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", PURPLE, variant="danger", height=26, width=60,
                        radius=5, border_width=1, text_color=PURP2, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_longtooth_shifter_row(self):
        """Longtooth Shifter's fangs — a real natural weapon only while
        Shifting (a bonus action, temporary transformation), matching the
        real trait text exactly."""
        if "Shifting" not in self.char.get("active_effects", []):
            return
        species = self.char.get("species") or self.char.get("race", "")
        subrace = self.char.get("subrace", "") or ""
        # The fangs themselves are mechanically identical between both
        # versions (same 1d6 STR piercing), matched explicitly rather
        # than via a blanket normalization, since other Shifter
        # mechanics (Shifting's own temp-HP formula) do genuinely
        # differ between versions and must never be conflated the same way.
        if species.strip().lower() not in ("shifter", "shifter (mpmm)") or "longtooth" not in subrace.lower():
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Fangs", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Longtooth Shifter", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip("Bonus action attack while Shifting.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup("Fangs (Longtooth Shifter) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"1d6+{mod}" if mod >= 0 else f"1d6{mod}"
        rl.addWidget(_lbl(f"{dmg_display} piercing", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Fangs (Longtooth Shifter)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", CRIM2, variant="danger", height=26, width=60,
                        radius=5, border_width=1, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_vampire_bite_row(self):
        """Vampire's Bloodthirst — always available, not conditional on
        any toggle (unlike Longtooth Shifter's fangs)."""
        species = self.char.get("species") or self.char.get("race", "")
        if species.strip().lower() != "vampire":
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Bloodthirst", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Vampire", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip("Only against a willing, grappled, incapacitated, or restrained creature. "
                          "Reduces the target's HP max by the necrotic damage dealt (until it long "
                          "rests) and you regain that much HP.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup("Bloodthirst (Vampire) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        rl.addWidget(_lbl("1 piercing", GOLD2, FS_BODY, wrap=False))
        necro_badge = _lbl("+1d6 necrotic", TEAL2, FS_SMALL, wrap=False)
        necro_badge.setToolTip("Bloodthirst (restricted target; drains HP max, heals you)")
        rl.addWidget(necro_badge)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Bloodthirst (Vampire)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = _btn("\U0001f3b2 Hit", CRIM2, variant="danger", height=26, width=60,
                        radius=5, border_width=1, hover_text="white",
                        font_size=FS_TINY, padding="0px")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _refresh_combat_weapons(self):
        """Rebuild the weapon rows in the combat tab from char[equipped_weapons]."""
        while self._weapon_rows.count():
            item = self._weapon_rows.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().setParent(None)
                item.widget().deleteLater()
        self._weapon_row_widgets.clear()
        from dnd_app.core.calculator import class_levels
        if class_levels(self.char).get("Monk", 0) > 0:
            self._add_martial_arts_row()
        if "Hybrid Transformation" in self.char.get("active_effects", []):
            self._add_hybrid_transformation_row()
        self._add_racial_natural_weapon_row()
        self._add_unarmed_fighting_row()
        self._add_tavern_brawler_row()
        self._add_generic_unarmed_strike_row()
        self._add_beast_form_row()
        self._add_battlerager_spikes_row()
        self._add_armorer_model_row()
        self._add_longtooth_shifter_row()
        self._add_vampire_bite_row()
        self._add_wildshape_beast_attack_rows()
        for idx, wpn in enumerate(self.char.get("equipped_weapons",[])):
            self._add_weapon_row(wpn, is_offhand=(idx > 0))

    def _add_wildshape_beast_attack_rows(self):
        """While Wild Shaped, the beast's own actions (Bite, Claws, etc.)
        become real, rollable weapon rows instead of just reference text —
        matching the real rule that your available actions are the
        beast's while transformed. Uses the beast's own pre-computed
        attack bonus and damage from its stat block text rather than
        recomputing from ability scores, since 'Multiattack' and
        condition-on-hit riders (like the wolf's prone-on-hit) don't
        reduce to a single die+modifier the way a simple weapon does."""
        active = self.char.get("_wildshape_active")
        if not active:
            return
        from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(active)
        if not beast:
            return
        import re
        for name, desc in beast.get("actions", []):
            if name.lower() == "multiattack":
                continue  # descriptive only ("makes two attacks..."), not itself a rollable attack
            m = re.search(r"([+\u2212-]\d+) to hit", desc)
            atk = m.group(1).replace("\u2212", "-") if m else None
            dmg_m = re.search(r"Hit: ([\dd+\u2212-]+) (\w+) damage", desc)
            # Traits like Pounce/Trampling Charge/Dive Attack are bonus-
            # action follow-ups keyed to a specific attack (e.g. Pounce
            # triggers off a claw hit) but live as separate trait entries
            # in the stat block, not part of the action's own text — so
            # without this they'd only be visible by opening the full
            # reference card in the Companions tab.
            linked_trait = next((tname for tname, tdesc in beast.get("traits", [])
                                  if name.lower() in tdesc.lower()
                                  and any(k in tname.lower() for k in
                                          ("pounce", "charge", "dive", "trampl"))), None)

            row_f = QFrame()
            row_f.setStyleSheet(
                f"QFrame{{background:{qa(PURPLE,0x14)};border:1px solid {qa(PURPLE,0x55)};border-radius:8px;}}")
            rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
            rl.addWidget(_lbl(name, TEXT, FS_BODY, bold=True, wrap=False))
            badge = _lbl(active, PURP2, FS_TINY, bold=True, wrap=False)
            badge.setToolTip(desc)
            rl.addWidget(badge)
            if linked_trait:
                trait_desc = next(td for tn, td in beast["traits"] if tn == linked_trait)
                trait_badge = _lbl(f"\u26a1 {linked_trait}", GOLD2, FS_TINY, bold=True, wrap=False)
                trait_badge.setToolTip(trait_desc)
                rl.addWidget(trait_badge)
            if atk:
                rl.addWidget(_lbl(f"{atk} to hit", PURP2, FS_BODY, wrap=False))
            if dmg_m:
                rl.addWidget(_lbl(f"{dmg_m.group(1)} {dmg_m.group(2)}", GOLD2, FS_BODY, wrap=False))
            rl.addStretch()

            if atk:
                def _roll_hit(checked=False, _atk=atk, _name=name):
                    import random
                    d20 = random.randint(1, 20)
                    bonus = int(_atk)
                    total = d20 + bonus
                    crit = (" \u2014 CRIT \u26a1" if d20==20
                            else (" \u2014 Miss \U0001f480" if d20==1 else ""))
                    QMessageBox.information(
                        None, "Roll To Hit",
                        f"\U0001f3b2 {_name}\n\nd20={d20}  {'+' if bonus>=0 else ''}{bonus}\nTotal: {total}{crit}")
                hit_btn = _btn("\U0001f3b2 Hit", PURPLE, variant="danger", height=26, width=60,
                                radius=5, border_width=1, text_color=PURP2, hover_text="white",
                                font_size=FS_TINY, padding="0px")
                hit_btn.clicked.connect(_roll_hit)
                rl.addWidget(hit_btn)

            self._weapon_rows.addWidget(row_f)
            self._weapon_row_widgets.append(row_f)

        # ══ TAB: CHOICES (level-up panel) ═════════════════════════════════════════
    def _refresh_combat(self):
        if getattr(self, "_blocking_refresh", False):
            return
        self._blocking_refresh = True
        try:
            self._do_refresh_combat()
        finally:
            self._blocking_refresh = False

    def _do_refresh_combat(self):
        char = self.char
        update_all(char)
        if hasattr(self,"_refresh_quick_spells"): self._refresh_quick_spells()
        # HP spinboxes — while Wild Shaped, show and edit the beast's own
        # separate HP pool instead of the character's own current_hp. Your
        # own hit points are untouched by damage taken in beast form
        # (except overflow past 0), so the two pools stay genuinely
        # separate rather than one masking the other.
        self._hp_max_hp.blockSignals(True)
        self._hp_current_hp.blockSignals(True)
        self._hp_temp_hp.blockSignals(True)
        active_beast = char.get("_wildshape_active")
        if active_beast:
            from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
            beast = WILDSHAPE_BEASTS.get(active_beast, {})
            mx = beast.get("hp", 0)
            cur = char.get("_wildshape_hp", mx)
            tmp = 0
        else:
            mx   = char.get("max_hp", 0)
            cur  = char.get("current_hp", mx)
            tmp  = char.get("temp_hp", 0)
        self._hp_max_hp.setValue(mx)
        self._hp_current_hp.setValue(cur)
        self._hp_temp_hp.setValue(tmp)
        self._hp_max_hp.setReadOnly(bool(active_beast))  # beast's max HP is fixed, not player-editable
        self._hp_max_hp.blockSignals(False)
        self._hp_current_hp.blockSignals(False)
        self._hp_temp_hp.blockSignals(False)
        self._update_hp_bar()
        if not getattr(self, "_hp_signals_connected", False):
            def _on_current_hp_changed(v):
                if self.char.get("_wildshape_active"):
                    if v <= 0:
                        self._wildshape_revert()
                        self._toast("🐾 Beast form dropped to 0 HP — reverted to normal form")
                    else:
                        self.char["_wildshape_hp"] = v
                        self._mark_dirty()
                else:
                    self.ctrl.update("current_hp", v, rebuild_char=False)
                self._update_hp_bar()
                self._refresh_death_and_conditions()
            self._hp_current_hp.valueChanged.connect(_on_current_hp_changed)
            self._hp_max_hp.valueChanged.connect(self._on_max_hp_changed)
            self._hp_temp_hp.valueChanged.connect(
                lambda v: self.ctrl.update("temp_hp", v, rebuild_char=False)
            )
            self._hp_signals_connected = True

        # Armor combo
        _armor_name = char.get("armor_worn", "No Armor")
        if _armor_name and _armor_name != "No Armor":
            _abase = next((a for a in ARMOR if a[0] == _armor_name), None)
            self._armor_display.setText(f"{_armor_name} (AC {_abase[2]})" if _abase else _armor_name)
        else:
            self._armor_display.setText("No Armor")
        self._shield_display.setText("Shield equipped (+2 AC)" if char.get("shield") else "No Shield")
        self._shield_display.setStyleSheet(
            f"QLabel{{background:{SURF2};border:1px solid {GOLD if char.get('shield') else BORDER};"
            f"border-radius:6px;padding:4px 10px;color:{GOLD2 if char.get('shield') else TEXT3};"
            f"font-size:{FS_SMALL}px;font-weight:{700 if char.get('shield') else 400};}}")

        self._bind_death_and_conditions()
        self._refresh_death_and_conditions()

        # Delegates to _refresh_combat_weapons rather than duplicating
        # the clear-and-rebuild loop here, so synthetic attack rows
        # (Martial Arts, etc.) stay in sync with equipment changes
        # rather than only appearing until the next tab switch.
        self._refresh_combat_weapons()
        self._refresh_companions_tab()

        # Resources and hit dice are now rendered inside the Other action tab
        # via _build_resource_rows(), called from _refresh_action_tabs().
        self._resource_widgets = []   # reset list; rebuilt in _refresh_action_tabs

        self._refresh_action_tabs()
        self._refresh_resistances_strip()
        # No maximumHeight cap on _combat_top_half: a hard cap would
        # stop dead space from appearing when the splitter shrinks the
        # action list, but would also stop the user from ever dragging
        # the handle to give the top area MORE room, which matters when
        # there are many resistance/movement badges wrapped into
        # several rows. Manual drag control in both directions wins here.

    def _refresh_resistances_strip(self):
        """Rebuild the Resistances/Immunities badge row. Expands 'all' and
        'all except X' shorthand into every individual damage type (so the
        strip always shows concrete types, never a vague summary), and
        applies D&D's actual rule that resistance and immunity to the same
        type don't stack — if a type has immunity from any source, its
        resistance badge (from any source) is dropped, not shown alongside."""
        if not hasattr(self, '_resist_frame'):
            return
        while self._resist_lay.count():
            item = self._resist_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)

        resistances = self.char.get("damage_resistances", [])
        immunities  = self.char.get("damage_immunities", []) + [
            (f"{cond} (condition)", source)
            for cond, source in self.char.get("condition_immunities_magic", [])
        ]

        if not resistances and not immunities:
            self._resist_frame.setVisible(False)
            self._resist_caption.setVisible(False)
            return
        self._resist_frame.setVisible(True)
        self._resist_caption.setVisible(True)
        idx = 0
        cols = 5

        def _badge(text, color, tooltip):
            b = _lbl(text, color, FS_SMALL, bold=True, wrap=False)
            b.setStyleSheet(
                f"background:{qa(color,0x33)};border:1.5px solid {qa(color,0x99)};"
                f"border-radius:5px;padding:3px 8px;color:{color};"
                f"font-size:{FS_SMALL}px;font-weight:700;"
            )
            b.setToolTip(tooltip)
            return b

        ALL_DAMAGE_TYPES = ["acid","bludgeoning","cold","fire","force","lightning",
                            "necrotic","piercing","poison","psychic","radiant",
                            "slashing","thunder"]

        def _expand(dmg_type, source):
            """'all' / 'all except X[/Y]' -> one (type, source) pair per
            real damage type; anything else passes through unchanged."""
            low = dmg_type.lower()
            if low == "all":
                return [(t, source) for t in ALL_DAMAGE_TYPES]
            if low.startswith("all except"):
                excluded = {e.strip() for e in low.replace("all except","").split("/")}
                return [(t, source) for t in ALL_DAMAGE_TYPES if t not in excluded]
            return [(dmg_type, source)]

        from collections import defaultdict
        res_by_type = defaultdict(list)
        for dmg_type, source in resistances:
            base = dmg_type.split(" (")[0]           # "bludgeoning (nonmagical)" -> "bludgeoning"
            qualifier = dmg_type[len(base):].strip() # "" or "(nonmagical)"
            for t, src in _expand(base, source):
                label = t + (f" {qualifier}" if qualifier else "")
                res_by_type[t].append((label, src))
        imm_by_type = defaultdict(list)
        for dmg_type, source in immunities:
            if "(condition)" in dmg_type:
                # Condition immunities (frightened, poisoned, etc.) aren't a
                # damage type and can't be superseded by damage resistance —
                # keep them in their own bucket, never expand/dedupe them
                # against the damage-type table.
                imm_by_type[dmg_type].append((dmg_type, source))
                continue
            base = dmg_type.split(" (")[0]
            for t, src in _expand(base, source):
                imm_by_type[t].append((t, src))

        # Immunity supersedes resistance to the same type — D&D doesn't
        # stack them, so don't display both for one damage type.
        for t in list(res_by_type):
            if t in imm_by_type:
                del res_by_type[t]

        for dmg_type, entries in sorted(res_by_type.items()):
            # Prefer an unqualified entry (e.g. Totem Barbarian's broad,
            # magical "all damage" resistance) over a qualified one (e.g.
            # Lycanthropy's narrower "bludgeoning (nonmagical, non-
            # silvered)") when both exist for the same base damage type —
            # an unqualified resistance always covers at least as much as
            # any qualified one, so it should win the display, not
            # whichever entry happened to be appended to the list first.
            unqualified = next((e for e in entries if " (" not in e[0]), None)
            display_label = unqualified[0] if unqualified else entries[0][0]
            sources = [s for _, s in entries]
            tip = f"Resistance to {display_label} damage\nFrom: " + ", ".join(sources)
            r, c = divmod(idx, cols)
            self._resist_lay.addWidget(_badge(f"½ {display_label}", TEAL2, tip), r, c)
            idx += 1
        for dmg_type, entries in sorted(imm_by_type.items()):
            display_label = entries[0][0]
            sources = [s for _, s in entries]
            is_condition = "(condition)" in display_label
            label_txt = display_label if is_condition else f"{display_label} damage"
            tip = f"Immunity to {label_txt}\nFrom: " + ", ".join(sources)
            r, c = divmod(idx, cols)
            self._resist_lay.addWidget(_badge(f"⊘ {display_label}", GOLD2, tip), r, c)
            idx += 1

