import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
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
from dnd_app.core.dying import (
    take_damage, heal, heal_block_reason, set_death_saves,
    revive, death_cause, death_status_text, STABLE_MESSAGE,
)
from dnd_app.core.spellcasting import spell_component_block_reason
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters, character_filename, validate_character,
)
from dnd_app.core.character import set_subclass, get_class_entry
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
from .base import *
from .base import _lbl, _sep, _card
from dnd_app.ui_desktop import icons as _icons


class PickerPopup(QFrame):
    """A small list to pick one name from, with a search box over it, that
    drops down under a button and closes once something's picked (or on
    a click elsewhere). Typing narrows the list; Enter picks the first
    one shown."""
    picked = Signal(str)

    def __init__(self, names, placeholder="Search…", parent=None):
        super().__init__(parent, Qt.Popup)
        self.setObjectName("pickerPopup")
        self.setStyleSheet(f"QFrame#pickerPopup{{background:{SURF2};border:2px solid {BORDER2};"
                           f"border-radius:8px;}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(8,8,8,8); lay.setSpacing(6)
        self._search = QLineEdit(); self._search.setPlaceholderText(placeholder)
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._filter)
        self._search.returnPressed.connect(self._pick_first)
        self._list = QListWidget()
        self._list.addItems(list(names))
        self._list.itemClicked.connect(lambda it: self._pick(it.text()))
        self._list.itemActivated.connect(lambda it: self._pick(it.text()))
        lay.addWidget(self._search); lay.addWidget(self._list, 1)
        self.resize(300, 340)

    def show_at(self, pos):
        self.move(pos)
        self.show()
        self._search.setFocus()

    def _filter(self, text):
        low = text.strip().lower()
        for i in range(self._list.count()):
            it = self._list.item(i)
            it.setHidden(bool(low) and low not in it.text().lower())

    def _pick_first(self):
        for i in range(self._list.count()):
            it = self._list.item(i)
            if not it.isHidden():
                self._pick(it.text())
                return

    def _pick(self, name):
        self.close()
        self.picked.emit(name)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Down and self._search.hasFocus():
            self._list.setFocus()
            for i in range(self._list.count()):
                if not self._list.item(i).isHidden():
                    self._list.setCurrentRow(i)
                    break
            return
        super().keyPressEvent(e)


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
        # (the conditions' menu actions are connected where they're built)
        active = set(self.char.get("conditions", []))
        for cond, act in self._cond_checks.items():
            act.blockSignals(True)
            act.setChecked(cond in active)
            act.blockSignals(False)
        self._death_cond_bound = True

    @staticmethod
    def _death_status_text(succ: int, fail: int) -> str:
        # core/dying.py, shared with Android (desktop text uses an em dash)
        return death_status_text(succ, fail).replace(" -- ", " — ")

    def _on_death_save_changed(self):
        """A death save pip was ticked: store it (core/dying.py) and show
        what it means -- third failure, dead; third success, stable (still
        at 0 HP and unconscious, so the pips stay up until healed)."""
        succ = sum(1 for cb in self._death_success if cb.isChecked())
        fail = sum(1 for cb in self._death_fail if cb.isChecked())
        verdict = set_death_saves(self.char, succ, fail)
        self._refresh_death_and_conditions()
        if verdict == "dead":
            self._show_death_screen()
        elif verdict == "stable":
            QMessageBox.information(self, "Stable", STABLE_MESSAGE.replace(" -- ", " — "))
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
        # What killed them: failed saves, exhaustion 6 or massive damage.
        # Plain light text under the title (dark red vanished into the
        # black overlay). Fixed colour: the overlay is black on every theme.
        note = QLabel(death_cause(self.char))
        note.setAlignment(Qt.AlignCenter); note.setWordWrap(True)
        # a fixed width, so the wrapped height is measured at the width it gets
        note.setFixedWidth(min(720, max(260, self.width() - 80)))
        note.setStyleSheet(
            f"QLabel{{color:#e6d3d3;font-size:{FS_BODY + 2}px;font-weight:600;"
            f"background:transparent;border:none;"
            f"font-family:'Georgia','Times New Roman',serif;}}")
        vl.addWidget(note, alignment=Qt.AlignCenter)
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
            revive(self.char)                    # 1 HP, saves and exhaustion cleared
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
            from dnd_app.data.flavor_text import random_death_message
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
        if hasattr(self, "_apply_turn_state"):
            self._apply_turn_state()     # Incapacitated/Surprised block the turn
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
        # Show/hide the death-saves container based on HP -- and when it
        # comes or goes, make room for it (or give the room back)
        at_zero = self.char.get("current_hp", 1) <= 0
        if hasattr(self, "_death_saves_container"):
            if self._death_saves_container.isHidden() == at_zero:
                self._death_saves_container.setVisible(at_zero)
                QTimer.singleShot(0, lambda down=at_zero: self._make_room_for_death_saves(down))
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
            changed = False
            for cond, act in self._cond_checks.items():
                if act.isChecked() != (cond in active):
                    act.blockSignals(True)
                    act.setChecked(cond in active)
                    act.blockSignals(False)
                    changed = True
            if changed:   # (put on or taken off by something else: a rest, a beast form...)
                self._refresh_active_conditions()

    def _make_room_for_death_saves(self, down: bool):
        """At 0 HP the death saves card appears under the HP boxes, and on a
        laptop-height window the combat tab's top half is too short for it.
          1. Going down: if the top half is shorter than it now needs, take
             the height from the action list (no actions while unconscious
             anyway) and remember the old split.
          2. Back up: put the old split back."""
        th = getattr(self, "_combat_top_half", None)
        sp = th.parentWidget() if th is not None else None
        if not isinstance(sp, QSplitter):
            return
        if down:
            sizes = sp.sizes()
            need = th.minimumSizeHint().height()
            if not sum(sizes) or sizes[0] >= need:
                return
            self._split_before_down = sizes
            self._action_tabs.setMinimumHeight(120)
            sp.setSizes([need, max(120, sum(sizes) - need)])
        elif getattr(self, "_split_before_down", None):
            sp.setSizes(self._split_before_down)
            self._split_before_down = None
            self._action_tabs.setMinimumHeight(320)

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
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        from dnd_app.core.calculator import get_available_wildshape_beasts

        card = _card(qa(PURPLE, 0x55))
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
                heal_btn = QPushButton("Combat Wild Shape: Spend Slot to Heal")
                _icons.set_button_icon(heal_btn, "magic", 16, color=on_fill(GOLD))
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

            fire_btn = QPushButton("Transform" if uses_left is None
                                    else f"Transform ({uses_left} left)")
            _icons.set_button_icon(fire_btn, "paw", 16, color=on_fill(PURPLE))
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
        """Transform (core/action_use.py wild_shape_into: the use or two
        it costs, the beast's hit points), then show the beast."""
        if not beast_name: return
        from dnd_app.core.action_use import wild_shape_into
        ok, msg = wild_shape_into(self.char, beast_name)
        self._toast(msg)
        if not ok:
            return
        self._wildshape_shown()

    def _wildshape_shown(self):
        """After a transform (here or from the Wild Shape action card): the
        sheet, the combat page and the Wild Shape card show the beast."""
        self._mark_dirty()
        self.ctrl.refresh()
        self._refresh_combat()
        self._rebuild_wildshape_card()

    def _wildshape_moon_heal(self):
        """Circle of the Moon's Combat Wild Shape: spend a spell slot as
        a bonus action to regain 1d8 HP per level of the slot, while
        transformed."""
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
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
        self._toast(f"Expended a level {level} slot: healed {roll} HP ({new_hp}/{beast['hp']})")

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

        # ── Vitals: the HP card (AC with it), and Initiative & Speed under it ─
        vitals = QWidget(); vitals.setStyleSheet("background:transparent;border:none;")
        vitl = QVBoxLayout(vitals); vitl.setContentsMargins(0,0,0,0); vitl.setSpacing(8)
        # The HP card: two columns (the header's health bar and the menu
        # bar show HP too) -- AC beside Temp, which sits over Current (it's
        # lost first), with Max beside Current; then how much, across
        # both, and Damage / Heal under it.
        hp_card = _card(qa(GREEN, 0x55)); hp_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hpcl = QVBoxLayout(hp_card); hpcl.setContentsMargins(12,10,12,10); hpcl.setSpacing(6)
        title_row = QHBoxLayout(); title_row.setSpacing(4); title_row.setContentsMargins(0,0,0,0)
        title_row.addWidget(_lbl("HIT POINTS", GOLD, FS_SMALL, bold=True, wrap=False))
        reset_max = QPushButton("↺")
        reset_max.setFixedSize(18, 18)
        reset_max.setToolTip("Reset Max HP to the auto-calculated value "
                             "(class Hit Dice + CON)")
        reset_max.setAccessibleName("Reset Max HP to the auto-calculated value")
        reset_max.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"color:{TEXT3};font-size:11px;padding:0;min-height:0px;}}"
            f"QPushButton:hover{{color:{TEAL2};}}")
        reset_max.clicked.connect(self._reset_max_hp_override)
        title_row.addWidget(reset_max)
        title_row.addStretch()
        hpcl.addLayout(title_row)

        hp_grid = QGridLayout(); hp_grid.setHorizontalSpacing(8); hp_grid.setVerticalSpacing(3)
        hp_grid.setColumnStretch(0, 1); hp_grid.setColumnStretch(1, 1)

        def _hp_box(key, color):
            sp = QSpinBox(); sp.setRange(0,999); sp.setAlignment(Qt.AlignCenter)
            sp.setStyleSheet(f"QSpinBox{{font-size:{FS_TITLE}px;font-weight:700;color:{color};"
                             f"border:2px solid {qa(color,0x55)};border-radius:8px;"
                             f"background:{SURF2};padding:0px 2px;min-width:56px;}}" + SPIN_NO_BUTTONS)
            setattr(self, f"_hp_{key}", sp)   # (36px: the theme's 32 + its border)
            return sp

        def _cap(text, gap=False):
            lbl = _lbl(text, TEXT2, FS_TINY, bold=True, align=Qt.AlignCenter, wrap=False)
            if gap:
                lbl.setContentsMargins(0, 4, 0, 0)   # (a little air between the pairs)
            return lbl
        hp_grid.addWidget(_cap("AC"), 0, 0)
        hp_grid.addWidget(_cap("Temp"), 0, 1)
        hp_grid.addWidget(self._build_ac_box(), 1, 0)
        hp_grid.addWidget(_hp_box("temp_hp", TEAL2), 1, 1)
        hp_grid.addWidget(_cap("Max", True), 2, 0)
        hp_grid.addWidget(_cap("Current", True), 2, 1)
        hp_grid.addWidget(_hp_box("max_hp", IND2), 3, 0)
        hp_grid.addWidget(_hp_box("current_hp", GREEN2), 3, 1)
        hpcl.addLayout(hp_grid)
        # (the health bar is the window's menu bar: _update_hp_bar)

        # how much, then Damage | Heal
        ctrl = QGridLayout(); ctrl.setHorizontalSpacing(8); ctrl.setVerticalSpacing(6)
        ctrl.setColumnStretch(0, 1); ctrl.setColumnStretch(1, 1)
        self._hp_amt = QSpinBox(); self._hp_amt.setRange(1,9999); self._hp_amt.setValue(1)
        self._hp_amt.setAlignment(Qt.AlignCenter)
        self._hp_amt.setAccessibleName("How much damage or healing")
        # 36px, the same as Damage / Heal (shared.py's stepper look)
        self._hp_amt.setStyleSheet(stepper_qss())
        dmg_btn = _btn("Damage", CRIMSON, variant="danger", height=36, bg_alpha=0x44,
                        text_color=CRIM2, hover_text="white", font_size=FS_SMALL, padding="0px")
        dmg_btn.setAccessibleName("Apply damage to hit points")
        dmg_btn.clicked.connect(self._do_damage)
        heal_btn = _btn("Heal", GREEN, variant="cta", height=36, bg_alpha=0x44,
                         text_color=GREEN2, hover_text="white", font_size=FS_SMALL, padding="0px")
        heal_btn.setAccessibleName("Heal hit points")
        heal_btn.clicked.connect(self._do_heal)
        # padding:0 above sizes these to their bare text -- give them room
        dmg_btn.setMinimumWidth(72); heal_btn.setMinimumWidth(56)
        ctrl.addWidget(self._hp_amt, 0, 0, 1, 2)
        ctrl.addWidget(dmg_btn, 1, 0); ctrl.addWidget(heal_btn, 1, 1)
        hpcl.addLayout(ctrl)
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
        self._resist_frame = QWidget(); self._resist_frame.setStyleSheet("QWidget{background:transparent;border:none;}")
        self._resist_lay = QGridLayout(self._resist_frame)
        self._resist_lay.setSpacing(4); self._resist_lay.setContentsMargins(0,0,0,0)
        self._resist_frame.setVisible(False)
        hpcl.addWidget(self._resist_frame, 1)
        # NOTE: climb/swim/fly used to get their own badge strip here too,
        # separate from the resistances strip above. Removed — the top
        # stat-bar speed pill already shows climb/swim/fly (fly/swim/climb next to
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
        self._combat_conc_lbl = _lbl("", AMBER, FS_SMALL, wrap=True)
        self._combat_conc_lbl.setVisible(False)
        hpcl.addWidget(self._combat_conc_lbl)
        # Death saves — a genuinely tense moment (0 HP, rolling to live or
        # die) gets its own alert-styled card (only shown at 0 HP to
        # begin with, so it earns the attention) with bigger pips, a
        # live status line, and per-pip tooltips explaining the actual
        # rule.
        self._death_saves_container = QFrame()
        self._death_saves_container.setObjectName("deathSaves")
        self._death_saves_container.setStyleSheet(
            f"QFrame#deathSaves{{background:{qa(CRIMSON,0x14)};border:2px solid {qa(CRIMSON,0x66)};"
            f"border-radius:8px;}}")
        self._death_saves_container.setVisible(False)
        dsl = QVBoxLayout(self._death_saves_container)
        dsl.setContentsMargins(12,8,12,8); dsl.setSpacing(4)

        ds_hdr = QHBoxLayout(); ds_hdr.setSpacing(8)
        ds_hdr.addWidget(_icons.icon_header("skull", _lbl("DEATH SAVES", CRIM2, FS_SMALL, bold=True, wrap=False)))
        ds_hdr.addStretch()
        dsl.addLayout(ds_hdr)
        # (its own line: the card is narrow)
        self._death_status_lbl = _lbl("", TEXT2, FS_TINY, bold=True, wrap=True)
        dsl.addWidget(self._death_status_lbl)

        pip_tip = ("Roll a d20 at the start of each of your turns while at 0 HP and "
                   "taking no other action. 10 or higher: success. Below 10: failure. "
                   "A natural 20 regains 1 HP instead; a natural 1 counts as two failures. "
                   "3 successes: stable at 0 HP. 3 failures: dead.")
        # Successes ooo over Failures ooo, to fit the HP card's two columns
        pips_grid = QGridLayout(); pips_grid.setHorizontalSpacing(6); pips_grid.setVerticalSpacing(4)

        def _pips(row, title, color, color2, attr):
            pips_grid.addWidget(_lbl(title, color2, FS_TINY, bold=True, wrap=False), row, 0)
            boxes = [QCheckBox() for _ in range(3)]
            for i, cb in enumerate(boxes):
                # 20px circles and their 2px edge: 24px, in a 26px box (a
                # 22px circle there was cut off)
                cb.setFixedSize(26,26)
                cb.setToolTip(pip_tip)
                cb.setStyleSheet(
                    f"QCheckBox{{spacing:0px;padding:1px;}}"
                    f"QCheckBox::indicator{{width:20px;height:20px;border-radius:12px;"
                    f"border:2px solid {color};background:{BG};}}"
                    f"QCheckBox::indicator:hover{{border-color:{color2};background:{qa(color,0x22)};}}"
                    f"QCheckBox::indicator:checked{{background:{color2};border-color:{color2};}}")
                pips_grid.addWidget(cb, row, 1 + i)
            setattr(self, attr, boxes)

        _pips(0, "SUCCESSES", GREEN, GREEN2, "_death_success")
        _pips(1, "FAILURES", CRIMSON, CRIM2, "_death_fail")
        pips_grid.setColumnStretch(4, 1)
        dsl.addLayout(pips_grid)
        hpcl.addWidget(self._death_saves_container)
        # spare height goes under the controls, not between the title and
        # the numbers
        hpcl.addStretch(1)
        vitl.addWidget(hp_card, 1)
        vitl.addWidget(self._build_init_speed_card())
        top_lay.addWidget(vitals, 3)

        # ── Weapons card, with what's worn on one line at the top ────────────
        # (read-only: armour and shield are put on in the Gear tab -- the
        # line takes you there -- so the weapons get the card's height)
        armor_card = _card(); armor_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        acl2 = QVBoxLayout(armor_card); acl2.setContentsMargins(12,10,12,10); acl2.setSpacing(6)
        wpn_head = QHBoxLayout(); wpn_head.setSpacing(6)
        wpn_head.addWidget(_lbl("WEAPONS", GOLD, FS_SMALL, bold=True, wrap=False))
        # a rogue's once-a-turn Sneak Attack (● ready, ○ used), by the
        # attacks it goes on; New Turn makes it ready again
        self._sneak_chip = QPushButton("Sneak Attack ●")
        _icons.set_button_icon(self._sneak_chip, "dagger", 13)
        self._sneak_chip.setFixedHeight(24)
        self._sneak_chip.setToolTip("Sneak Attack: once a turn. Click to mark it used or ready.")
        self._sneak_chip.setAccessibleName("Sneak Attack this turn — click to mark it used or ready")
        self._sneak_chip.clicked.connect(self._toggle_sneak)
        self._sneak_chip.setVisible(False)
        wpn_head.addWidget(self._sneak_chip)
        wpn_head.addStretch()
        worn = QFrame(); worn.setObjectName("wornLine")
        worn.setCursor(Qt.PointingHandCursor)
        worn.setToolTip("Your armour and shield. Put them on or take them off in the Gear tab.")
        worn.setStyleSheet("QFrame#wornLine{background:transparent;border:none;}")
        wl = QHBoxLayout(worn); wl.setContentsMargins(0,0,0,0); wl.setSpacing(6)
        # (the AC they make is in the HP card, beside this one)
        self._armor_display = _lbl("No armor", TEXT2, FS_SMALL, wrap=False)
        self._shield_display = _lbl("No shield", TEXT3, FS_SMALL, wrap=False)
        wl.addWidget(self._armor_display)
        wl.addWidget(_lbl("·", TEXT3, FS_SMALL, wrap=False))
        wl.addWidget(self._shield_display)
        wl.addWidget(_lbl("Gear ▸", TEAL2, FS_TINY, bold=True, wrap=False))
        worn.mousePressEvent = lambda e: self._tabs.setCurrentIndex(3)
        wpn_head.addWidget(worn)
        acl2.addLayout(wpn_head)
        # The Gear tab (for equipping weapons/armor) is one click away on
        # the tab bar itself.
        wpn_host = QWidget(); wpn_host.setStyleSheet("background:transparent;border:none;")
        self._weapon_rows = QVBoxLayout(wpn_host)
        self._weapon_rows.setSpacing(4); self._weapon_rows.setContentsMargins(0,0,0,0)
        self._weapon_rows.setAlignment(Qt.AlignTop)   # rows keep their own height, stacked from the top
        wpn_scroll = QScrollArea(); wpn_scroll.setWidgetResizable(True)
        wpn_scroll.setFrameShape(QFrame.NoFrame)
        wpn_scroll.setMinimumHeight(80)
        # never scrolled sideways: the card is kept as wide as its widest
        # row (_refresh_combat_weapons), so every weapon's to-hit, damage
        # and Hit button are always in view
        wpn_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._weapons_card, self._weapons_scroll = armor_card, wpn_scroll
        wpn_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        wpn_scroll.setWidget(wpn_host)
        acl2.addWidget(wpn_scroll, 1)
        top_lay.addWidget(armor_card, 5)

        # ── Conditions & Effects card ─────────────────────────────────────────
        # Two pages under tabs (a stacked widget): the conditions on you,
        # and the effects on you (Bless, Haste, Shield of Faith...). Each
        # tab says how many it holds, so neither goes unseen; ＋ Add puts
        # one on, for whichever page is showing.
        cond_card = _card(); cond_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ccl = QVBoxLayout(cond_card); ccl.setContentsMargins(10,6,10,10); ccl.setSpacing(8)
        head = QHBoxLayout(); head.setSpacing(6); head.setContentsMargins(0,0,0,0)
        self._ce_bar = QTabBar()
        self._ce_bar.setDrawBase(False); self._ce_bar.setExpanding(False)
        self._ce_bar.setUsesScrollButtons(False)
        self._ce_bar.addTab("Conditions"); self._ce_bar.addTab("Effects")
        self._ce_bar.setTabToolTip(0, "The conditions on you: what each does, and how to take it off")
        self._ce_bar.setTabToolTip(1, "The effects on you: your own spells, and ones an ally put on you")
        self._ce_bar.setStyleSheet(
            f"QTabBar{{background:transparent;border:none;}}"
            f"QTabBar::tab{{background:transparent;color:{TEXT2};border:none;"
            f"border-bottom:2px solid transparent;border-radius:0px;padding:4px 2px;"
            f"margin-right:14px;min-width:0px;font-size:{FS_SMALL}px;font-weight:700;}}"
            f"QTabBar::tab:selected{{color:{GOLD};border-bottom:2px solid {GOLD};}}"
            f"QTabBar::tab:hover:!selected{{color:{TEXT};}}")
        head.addWidget(self._ce_bar, 0, Qt.AlignBottom)
        head.addStretch()
        self._ce_add = QPushButton("＋ Add")
        self._ce_add.setStyleSheet(_btn("", variant="neutral", radius=6, font_size=FS_SMALL,
                                        padding="0px 10px", min_height0=True).styleSheet())
        self._ce_add.setFixedHeight(26)
        self._ce_add.clicked.connect(self._ce_add_clicked)
        head.addWidget(self._ce_add, 0, Qt.AlignVCenter)
        ccl.addLayout(head)
        self._ce_stack = QStackedWidget()
        self._ce_stack.setStyleSheet("QStackedWidget{background:transparent;border:none;}")
        self._ce_bar.currentChanged.connect(self._ce_stack.setCurrentIndex)
        self._ce_bar.currentChanged.connect(lambda i: self._ce_add.setToolTip(
            "Put a condition on you, or take one off" if i == 0 else
            "Put an effect on you: one an ally cast on you, a potion..."))
        ccl.addWidget(self._ce_stack, 1)

        def _list_page():
            """A page: a list that scrolls (never sideways), and its layout."""
            sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sc.setStyleSheet("QScrollArea{background:transparent;border:none;}")
            host = QWidget(); host.setStyleSheet("background:transparent;border:none;")
            lay = QVBoxLayout(host); lay.setContentsMargins(0,0,4,0); lay.setSpacing(5)
            sc.setWidget(host)
            return sc, lay

        def _empty(text):
            lbl = _lbl(text, TEXT3, FS_SMALL, align=Qt.AlignCenter, wrap=True)
            lbl.setContentsMargins(6, 14, 6, 14)
            return lbl

        # ── page 1: conditions, and exhaustion's level under them ──
        cpage = QWidget(); cpage.setStyleSheet("background:transparent;border:none;")
        cpl = QVBoxLayout(cpage); cpl.setContentsMargins(0,0,0,0); cpl.setSpacing(8)
        cond_scroll, self._active_cond_lay = _list_page()
        # the rows go in above these two: the "none" line, and a stretch
        self._active_cond_none_lbl = _empty("No conditions on you.")
        self._active_cond_lay.addWidget(self._active_cond_none_lbl)
        self._active_cond_lay.addStretch(1)
        COND_NAMES = ["Blinded","Charmed","Deafened","Frightened","Gagged",
                      "Grappled","Incapacitated","Invisible","Paralyzed",
                      "Petrified","Poisoned","Prone","Restrained","Stunned","Surprised",
                      "Unconscious"]
        self._cond_menu = QMenu(cond_card)
        self._cond_menu.setToolTipsVisible(True)
        self._cond_checks = {}   # name -> its checkable menu action
        for cname in COND_NAMES:
            act = self._cond_menu.addAction(cname)
            act.setCheckable(True)
            cdata = CONDITIONS.get(cname, {})
            tip_lines = list(cdata.get("effects", []))
            if cdata.get("source"):
                tip_lines.append(f"({cdata['source']})")
            if tip_lines:
                act.setToolTip("\n".join(tip_lines))
            act.toggled.connect(lambda on, n=cname: self._on_condition_changed(n, on))
            self._cond_checks[cname] = act
        self._cond_menu.addSeparator()
        self._cond_clear_act = self._cond_menu.addAction("Clear all")
        self._cond_clear_act.setToolTip("Take every condition off (exhaustion stays: a long rest takes a level off)")
        self._cond_clear_act.triggered.connect(self._clear_conditions)
        cpl.addWidget(cond_scroll, 1)

        # Exhaustion: six pips, the level filled in -- click one to set it
        # (click the top one again to take a level off). The spin box under
        # them is the level itself, kept hidden: loading, rests and the
        # rules all set it, and the pips follow.
        exh = QFrame(); exh.setObjectName("exhRow")
        exh.setStyleSheet(f"QFrame#exhRow{{background:{SURF2};border:1px solid {BORDER};border-radius:6px;}}")
        exl = QHBoxLayout(exh); exl.setContentsMargins(10,6,10,6); exl.setSpacing(5)
        exl.addWidget(_lbl("Exhaustion", TEXT2, FS_SMALL, bold=True, wrap=False))
        exl.addSpacing(4)
        self._exh_pips = []
        for n in range(1, 7):
            pip = QPushButton(); pip.setFixedSize(16, 16)
            pip.setCursor(Qt.PointingHandCursor)
            pip.setAccessibleName(f"Exhaustion level {n}")
            pip.clicked.connect(lambda checked=False, lv=n: self._exh_pip_clicked(lv))
            exl.addWidget(pip)
            self._exh_pips.append(pip)
        exl.addStretch(1)
        self._exh_level_lbl = _lbl("", TEXT3, FS_TINY, bold=True, wrap=False)
        exl.addWidget(self._exh_level_lbl)
        cpl.addWidget(exh)
        self._exhaustion_spin = QSpinBox(cpage); self._exhaustion_spin.setRange(0,6)
        self._exhaustion_spin.hide()
        self._exhaustion_spin.valueChanged.connect(self._on_exhaustion_changed)
        # what the exhaustion level does, while there is one
        self._exh_effect_lbl = _lbl("", CRIM2, FS_TINY, wrap=True)
        self._exh_effect_lbl.setVisible(False)
        cpl.addWidget(self._exh_effect_lbl)
        self._ce_stack.addWidget(cpage)

        # ── page 2: effects (Haste, Shield of Faith, an ally's Bless...) ──
        epage = QWidget(); epage.setStyleSheet("background:transparent;border:none;")
        epl = QVBoxLayout(epage); epl.setContentsMargins(0,0,0,0); epl.setSpacing(6)
        fx_scroll, self._fx_lay = _list_page()
        self._fx_lay.addStretch()   # (the rows go in above it: _refresh_effects_list)
        epl.addWidget(fx_scroll, 1)
        self._ce_stack.addWidget(epage)

        self._cond_card = cond_card
        top_lay.addWidget(cond_card, 3)

        from dnd_app.core.calculator import get_wild_shape_info
        if get_wild_shape_info(self.char) is not None:
            self._wildshape_card_container = top_lay
            self._wildshape_card_widget = self._build_wildshape_control_card()
            top_lay.addWidget(self._wildshape_card_widget, 2)

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
            # selected tab joined to its page (see theme.py's QTabWidget::pane)
            f"QTabWidget::pane{{border:1px solid {qa(AMBER,0x33)};border-top-left-radius:0px;border-top-right-radius:8px;border-bottom-right-radius:8px;border-bottom-left-radius:8px;"
            f"background:{SURF};top:-1px;}}"
            f"QTabBar::tab{{background:{BG};color:{TEXT2};border:1px solid {qa(AMBER,0x22)};"
            f"border-bottom:1px solid {qa(AMBER,0x33)};padding:6px 14px;border-top-left-radius:6px;border-top-right-radius:6px;border-bottom-right-radius:0px;border-bottom-left-radius:0px;"
            f"font-size:{FS_SMALL}px;font-weight:700;min-width:80px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD};border-color:{qa(AMBER,0x66)};"
            f"border-bottom:1px solid {SURF};}}"
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
        CAT_ICONS = {"Common": "combat", "Item": "gear", "Race": "identity", "Spell": "spells"}
        for bucket_name, icon in [("Action","combat"),("Bonus Action","bonus"),
                                   ("Reaction","bolt"),("Passive","passive")]:
            bw = QWidget(); bw.setStyleSheet("background:transparent;border:none;")
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
            # (a category shows only while the tab has something in it:
            # _refresh_action_tabs)
            for cat in ["All", "Common", "Item", "Race", "Spell"]:
                btn = QPushButton(cat)
                if cat in CAT_ICONS:
                    _icons.set_button_icon(btn, CAT_ICONS[cat], 13)
                btn.setFixedHeight(26)
                btn.setStyleSheet(self._action_cat_btn_style(cat == "All"))
                btn.clicked.connect(_make_cat_click(cat))
                btn.setToolTip({"All": "Everything in this tab",
                                "Common": "Class features, feats and the basic actions",
                                "Item": "What your items and tools let you do",
                                "Race": "Your race's traits",
                                "Spell": "Your spells"}[cat])
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
                btn.setFixedHeight(22); btn.setMaximumWidth(48)
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
            self._action_tabs.addTab(scroll, label)
            _icons.set_tab_icon(self._action_tabs, scroll, icon, 15)

        # ── Turn tracker (Action / Bonus / Reaction economy per turn) ────────
        # Beside the action tabs, in the corner of their tab row, so it
        # doesn't take a row of its own: a chip each for this turn's
        # action, bonus action and reaction (● ready, ○ used -- click to
        # change it) and New Turn. (A rogue's Sneak Attack is on the
        # Weapons card, by the attacks it goes on.)
        self._turn_counts = {"Action":0, "Bonus Action":0, "Reaction":0}
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        turn_bar = QWidget()
        turn_bar.setStyleSheet("background:transparent;border:none;")
        tb = QHBoxLayout(turn_bar); tb.setContentsMargins(8,0,2,3); tb.setSpacing(6)
        self._turn_chips = {}
        for bname, short, icon in [("Action","Action","combat"),("Bonus Action","Bonus","bonus"),
                                   ("Reaction","Reaction","bolt")]:
            chip = QPushButton(f"{short}  ●")
            _icons.set_button_icon(chip, icon, 14)
            chip.setProperty("_short", short)
            chip.setCheckable(False); chip.setFixedHeight(26)
            chip.setAccessibleName(f"{bname} this turn — click to mark it used or ready")
            chip.clicked.connect(lambda checked=False, b=bname: self._toggle_turn_slot(b))
            tb.addWidget(chip)
            self._turn_chips[bname] = chip
        new_turn = QPushButton("New Turn")
        _icons.set_button_icon(new_turn, "refresh", 14)
        new_turn.setFixedHeight(26)
        new_turn.setAccessibleName("Start a new turn — resets action, bonus action, reaction and sneak attack")
        new_turn.setToolTip("Start your next turn: your action, bonus action and reaction are ready again")
        # (the turn chips' look: on the action tabs' darker strip, its text
        # kept readable on its tint there -- in a light theme too)
        _nt_ink = readable(GREEN2, tint(PANELDK, GREEN2, 0x1e))
        new_turn.setStyleSheet(
            f"QPushButton{{background:{qa(GREEN2,0x1e)};border:2px solid {GREEN2};font-size:{FS_SMALL}px;"
            f"border-radius:6px;color:{_nt_ink};font-weight:700;padding:0px 12px;min-height:0px;}}"
            f"QPushButton:hover{{background:{GREEN2};color:{on_fill(GREEN2)};}}"
            f"QPushButton:focus{{border:2px solid {TEAL2};}}")
        new_turn.clicked.connect(self._new_turn)
        tb.addWidget(new_turn)
        self._action_tabs.setCornerWidget(turn_bar, Qt.TopRightCorner)

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
        """Damage button. A Wild Shape beast form takes it from its own
        pool first; everything about your own hit points (temp HP, massive
        damage, death saves, rage, concentration) is core/dying.py's
        take_damage(), the same rules as the Android sheet."""
        amt = self._hp_amt.value()
        if amt <= 0:
            return
        if self.char.get("_wildshape_active"):
            # Wild Shape (PHB p.66): the beast's hit points take the hit.
            # Reaching 0 reverts you to your normal form, and the damage
            # left over carries on to your own hit points.
            cur = self._hp_current_hp.value()          # the beast's HP
            if amt >= cur:
                excess = amt - cur
                self._wildshape_revert()
                lead = (f"Beast form dropped to 0 HP — reverted to normal form, "
                        f"{excess} excess damage carried over")
                self._after_damage(take_damage(self.char, excess), lead)
                return
            self._hp_current_hp.setValue(cur - amt)
            self.char["_wildshape_hp"] = cur - amt
            self._mark_dirty()
            self._toast(f"Beast form took {amt} damage")
            if self.char.get("concentration", {}).get("spell"):
                self._concentration_save_prompt(max(10, amt // 2))
            return
        self._after_damage(take_damage(self.char, amt))

    def _after_damage(self, res: dict, lead: str = ""):
        """Show what take_damage() did: the HP boxes, one toast, the death
        screen, and the concentration save it asks for."""
        # 1. Every HP widget follows the character (one controller refresh).
        self.ctrl.update("current_hp", self.char.get("current_hp", 0), rebuild_char=False)
        self._refresh_concentration()
        self._mark_dirty()
        # 2. Dead: the YOU DIED screen says why.
        if res["died"]:
            self._show_death_screen()
            return
        # 3. One toast with everything that happened, in order.
        notes = ([lead] if lead else []) + [n.replace(" -- ", " — ") for n in res["notes"]]
        if notes:
            self._toast("\n".join(notes))
        # 4. Still concentrating: roll to keep it.
        if res["concentration_dc"]:
            self._concentration_save_prompt(res["concentration_dc"])

    def _concentration_save_prompt(self, dc: int):
        """Took damage while concentrating: the CON save against the DC
        (core/checks.py, the same on Android) -- with what always applies
        on it (Bless, War Caster's reminder, Bladesong...), and when it's
        under the DC, what you can add (Lucky, Flash of Genius...) in the
        roll dialog. Under the DC after that, the spell drops."""
        conc_spell = self.char.get("concentration", {}).get("spell")
        if not conc_spell:
            return
        from dnd_app.core.calculator import get_saving_throw_bonus
        self._roll_check({"kind": "concentration", "ability": "CON", "skill": "",
                          "label": f"Concentration ({conc_spell})", "bonus": get_saving_throw_bonus(self.char, "CON"),
                          "dc": dc, "spell": conc_spell})
        if not self.char.get("concentration", {}).get("spell"):
            self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
        self._refresh_concentration()
        self._mark_dirty()

    def _roll_initiative(self):
        """Roll d20 + initiative bonus — shown as a non-blocking toast."""
        self._quick_roll_toast("Initiative", get_initiative(self.char))

    def _do_heal(self):
        amt = self._hp_amt.value()
        cur = self._hp_current_hp.value()
        wild = self.char.get("_wildshape_active")
        if wild:
            from dnd_app.data.statblocks import WILDSHAPE_BEASTS
            beast_max = WILDSHAPE_BEASTS.get(wild, {}).get("hp", cur)
            new_hp = min(beast_max, cur + amt)
            self._hp_current_hp.setValue(new_hp)
            self.char["_wildshape_hp"] = new_hp
            self._mark_dirty()
            return
        # The dead need Revive, not a potion. Otherwise core/dying.py's
        # heal(): up to max HP, and back up from 0 resets the death saves.
        why = heal_block_reason(self.char)
        if why:
            self._toast(why.replace(" -- ", " — "))
            return
        note = heal(self.char, amt)
        self.ctrl.update("current_hp", self.char["current_hp"], rebuild_char=False)
        self._mark_dirty()
        if note:
            self._toast(note)

    # ═══ Turn tracker ══════════════════════════════════════════════════════
    def _turn_limit(self, bucket: str) -> int:
        from dnd_app.core.effects import has_extra_action
        from dnd_app.core.calculator import get_turn_blocks
        if bucket in get_turn_blocks(self.char):
            return 0          # Incapacitated / Surprised: this part of the turn is gone
        if bucket == "Action" and has_extra_action(self.char):
            return 2
        return 1

    def _mark_turn_used(self, bucket: str):
        """Consume one use of an action-economy slot; grey the bucket when spent."""
        if bucket not in self._turn_counts:
            return
        limit = self._turn_limit(bucket)
        if limit == 0:
            self._toast_turn_block(bucket)
            return
        if self._turn_counts[bucket] >= limit:
            return
        self._turn_counts[bucket] += 1
        if bucket == "Action" and limit == 2 and self._turn_counts[bucket] == 1:
            self._toast("Haste: first action used — one more available")
        self._apply_turn_state()

    def _toast_turn_block(self, bucket: str):
        from dnd_app.core.calculator import get_turn_blocks
        why = get_turn_blocks(self.char).get(bucket)
        if why:
            self._toast(f"Can't use your {bucket.lower()}: {why}")

    def _toggle_turn_slot(self, bucket: str):
        limit = self._turn_limit(bucket)
        if limit == 0:
            self._toast_turn_block(bucket)
            return
        self._turn_counts[bucket] = 0 if self._turn_counts[bucket] >= limit else limit
        self._apply_turn_state()

    def _toggle_sneak(self):
        # the once-a-turn tracker the attack dialog uses too (core/attacks.py)
        turn = self.char.setdefault("_turn_uses", [])
        if "Sneak Attack" in turn:
            turn.remove("Sneak Attack")
        else:
            turn.append("Sneak Attack")
        self._apply_turn_state()

    def _new_turn(self):
        for k in self._turn_counts: self._turn_counts[k] = 0
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        self.char["_action_surge_used_this_turn"] = False
        # what lasted until now ends: Reckless Attack, Dodge, Agile Parry,
        # Kensei's Shot... and once-per-turn uses come back (core/action_use.py)
        from dnd_app.core.action_use import new_turn
        if new_turn(self.char):
            self._mark_dirty()
            QTimer.singleShot(0, self.ctrl.refresh)
        # Surprise lasts until the end of your first turn -- a new turn
        # means it's over.
        if "Surprised" in self.char.get("conditions", []):
            self.char["conditions"] = [c for c in self.char["conditions"] if c != "Surprised"]
            cb = getattr(self, "_cond_checks", {}).get("Surprised")
            if cb is not None:
                cb.blockSignals(True); cb.setChecked(False); cb.blockSignals(False)
            self._refresh_active_conditions()
            self._mark_dirty()
            self.ctrl.refresh()
            self._apply_turn_state()
            self._toast("New turn — no longer surprised; action, bonus & reaction ready")
            return
        self._apply_turn_state()
        from dnd_app.core.calculator import get_turn_blocks
        if get_turn_blocks(self.char):
            self._toast("New turn — still incapacitated, no actions or reactions")
        else:
            self._toast("New turn — action, bonus & reaction ready")

    def _apply_turn_state(self):
        """Grey out Use/Cast buttons in spent buckets; refresh chips."""
        if not hasattr(self, "_turn_chips"):
            return
        from dnd_app.core.character import class_levels
        from dnd_app.core.calculator import get_turn_blocks
        blocks = get_turn_blocks(self.char)
        # Greying out the Use button just pressed (it has the focus) makes Qt
        # pass the focus to the next one down -- greyed out too -- card by
        # card to the bottom, the list scrolling after it. So take the focus
        # off it first.
        from PySide6.QtWidgets import QApplication
        fw = QApplication.focusWidget()
        if fw is not None and any(fw in btns for btns in getattr(self, "_bucket_use_btns", {}).values()):
            fw.clearFocus()
        from dnd_app.core.effects import has_extra_action
        extra = has_extra_action(self.char)
        for bname, chip in self._turn_chips.items():
            limit = self._turn_limit(bname)
            used  = self._turn_counts.get(bname, 0)
            free  = used < limit
            marker = "●" * max(0, limit-used) + "○" * used if limit else "—"
            chip.setText(f"{chip.property('_short') or bname}  {marker}")
            if bname in blocks:
                tip = f"No {bname.lower()} this turn: {blocks[bname]}"
            else:
                tip = (f"Your {bname.lower()} this turn: "
                       + ("ready" if free else "used") + ". Click to mark it "
                       + ("used." if free else "ready again."))
                if bname == "Action" and extra and limit == 2:
                    tip += ("\nAction Surge: one more action this turn."
                            if self.char.get("_action_surge_used_this_turn") else
                            "\nHasted: one more action this turn (Attack with one weapon "
                            "attack only, Dash, Disengage, Hide or Use an Object).")
            chip.setToolTip(tip)
            col = GREEN2 if free else (CRIM2 if bname in blocks else TEXT2)
            # (on the action tabs' darker strip: kept readable on its tint)
            ink = readable(col, tint(PANELDK, col, 0x1e))
            chip.setStyleSheet(
                f"QPushButton{{background:{qa(col,0x1e)};border:2px solid {col};font-size:{FS_SMALL}px;"
                f"border-radius:6px;color:{ink};font-weight:700;padding:0px 10px;min-height:0px;}}"
                f"QPushButton:hover{{border-color:{TEAL2};}}"
                f"QPushButton:focus{{border:2px solid {TEAL2};}}")
            # Grey the bucket's buttons + dim cards
            for btn in getattr(self, "_bucket_use_btns", {}).get(bname, []):
                try:
                    btn.setEnabled(free)
                    mark = "—" if bname in blocks else "✓"
                    if not free and btn.text() != mark:
                        if btn.text() not in ("✓", "—"):
                            btn.setProperty("_orig_text", btn.text())
                        btn.setText(mark)
                    elif free and btn.property("_orig_text"):
                        btn.setText(btn.property("_orig_text"))
                except RuntimeError:
                    pass
        # Sneak chip (rogues only): hidden while Wild Shaped, since Sneak
        # Attack requires a finesse or ranged weapon and natural weapons
        # never qualify. Also hidden if nothing currently equipped qualifies.
        rogue_lvl = class_levels(self.char).get("Rogue", 0)
        has_qualifying_weapon = False
        if rogue_lvl > 0:
            from dnd_app.data.items import WEAPON_DICT
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
            used = "Sneak Attack" in self.char.get("_turn_uses", [])
            self._sneak_chip.setVisible(True)
            self._sneak_chip.setText(f"Sneak {dice}d6  {'○' if used else '●'}")
            self._sneak_chip.setToolTip(
                f"Sneak Attack ({dice}d6): once a turn, "
                + ("used this turn. Click to mark it ready again." if used
                   else "ready. Click to mark it used."))
            col = TEXT2 if used else PURP2
            ink = readable(col, tint(SURF, col, 0x1e))
            self._sneak_chip.setStyleSheet(
                f"QPushButton{{background:{qa(col,0x1e)};border:2px solid {col};font-size:{FS_SMALL}px;"
                f"border-radius:6px;color:{ink};font-weight:700;padding:0px 10px;min-height:0px;}}"
                f"QPushButton:hover{{border-color:{TEAL2};}}"
                f"QPushButton:focus{{border:2px solid {TEAL2};}}")
        else:
            self._sneak_chip.setVisible(False)

    def _ce_add_clicked(self):
        """＋ Add on the Conditions & Effects card: for conditions, the menu
        of them (ticked: on you; click to put one on or take it off); for
        effects, a list to pick from, with a search box."""
        b = self._ce_add
        at = b.mapToGlobal(QPoint(b.width(), b.height() + 2))
        if self._ce_stack.currentIndex() == 0:
            self._cond_menu.exec(QPoint(at.x() - self._cond_menu.sizeHint().width(), at.y()))
            return
        from dnd_app.core.effects import EFFECT_TABLE
        on = set(self.char.get("active_effects", []))
        names = [n for n in sorted(set(EFFECT_TABLE) | RESOURCE_POOL_TOGGLES) if n not in on]
        pop = PickerPopup(names, "Search effects…", self)
        pop.picked.connect(self._add_active_effect)
        pop.show_at(QPoint(at.x() - pop.width(), at.y()))

    def _exh_pip_clicked(self, level: int):
        """An exhaustion pip: that level (the top one again: a level off).
        Level 6 is death, so that one asks first."""
        cur = self._exhaustion_spin.value()
        new = level - 1 if cur == level else level
        if new >= 6 > cur:
            ans = QMessageBox.question(self, "Exhaustion 6",
                                       "Exhaustion level 6 is death. Set it?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ans != QMessageBox.Yes:
                return
        self._exhaustion_spin.setValue(new)

    # ═══ Active spell effects ═══════════════════════════════════════════════
    def _add_active_effect(self, typed: str = ""):
        from dnd_app.core.effects import EFFECT_TABLE
        typed = (typed or "").strip()
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
            self._toast(f"\"{typed}\" isn't a recognized effect — pick one from the list")
            return
        from dnd_app.core.calculator import effect_start_problem, on_effect_started
        why = effect_start_problem(self.char, name)   # Rage in heavy armor
        if why:
            self._toast(f"{name}: {why}".replace(" -- ", " — "))
            return
        if name in self.char.get("active_effects", []):
            self._toast(f"{name} is already on you")
            return
        self.char.setdefault("active_effects", []).append(name)
        note = on_effect_started(self.char, name)       # Rage ends concentration
        self.ctrl.refresh()          # AC pill etc. recompute
        self._refresh_effects_list()
        self._apply_turn_state()     # haste chip
        self._mark_dirty()
        self._toast(f"{name} applied" + (f" — {note}" if note else ""))

    def _remove_active_effect(self, name: str):
        fx = self.char.get("active_effects", [])
        if name in fx:
            fx.remove(name)
            (self.char.get("effect_details") or {}).pop(name, None)
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
                self._toast("Rage removed — Frenzy ends with it, gain 1 level of exhaustion")
            else:
                self._toast(f"{name} removed")

    def _refresh_effects_list(self):
        """The Effects page: a row for each effect on you -- its name, what
        it does, and ✕ to end it. The tab says how many there are."""
        if not hasattr(self, "_fx_lay"): return
        from dnd_app.core.effects import EFFECT_TABLE
        from dnd_app.core.riders import effect_note
        while self._fx_lay.count() > 1:
            it = self._fx_lay.takeAt(0)
            w = it.widget()
            if w:
                w.hide(); w.setParent(None); w.deleteLater()
        fx = self.char.get("active_effects", [])
        if hasattr(self, "_ce_bar"):
            self._ce_bar.setTabText(1, "Effects" + (f" ({len(fx)})" if fx else ""))
        if not fx:
            empty = _lbl("No effects on you. A spell you cast on yourself shows here; "
                         "＋ Add puts on one an ally cast on you.",
                         TEXT3, FS_SMALL, align=Qt.AlignCenter, wrap=True)
            empty.setContentsMargins(6, 14, 6, 14)
            self._fx_lay.insertWidget(0, empty)
            return
        for i, name in enumerate(fx):
            info = EFFECT_TABLE.get(name, {})
            col = TEAL if info else AMBER
            under = tint(SURF, col, 0x1a)
            ink = readable(GOLD, under)
            row = QFrame(); row.setObjectName("fxRow")
            row.setStyleSheet(f"QFrame#fxRow{{background:{qa(col,0x1a)};border:1px solid {qa(col,0x66)};"
                              f"border-radius:6px;}}")
            rl = QHBoxLayout(row); rl.setContentsMargins(8,5,8,5); rl.setSpacing(7)
            rl.addWidget(_icons.icon_label("effects", 16, ink))
            rl.addWidget(_lbl(name + ("  ©" if info.get("conc") else ""), ink, FS_SMALL,
                              bold=True, wrap=False), 1)
            # a smite's dice at the level it was cast, or what's left of it on
            # the target once it has landed (core/riders.py)
            note = effect_note(self.char, name) or info.get("note", "Custom effect — tracked, no automatic numbers.")
            row.setToolTip(f"<b>{name}</b>" + (" (concentration)" if info.get("conc") else "")
                           + f"<br>{note}<br><br><i>Right-click: end it, or read it all</i>")
            row.setAccessibleName(f"{name}: {note}")

            def _menu(pos, r=row, n=name, nt=note):
                m = QMenu(r)
                m.addAction(f"End {n}", lambda: QTimer.singleShot(0, self, lambda: self._remove_active_effect(n)))
                m.addAction("Details…", lambda: show_details(self, n, details_markdown(nt)))
                m.exec(r.mapToGlobal(pos))
            row.setContextMenuPolicy(Qt.CustomContextMenu)
            row.customContextMenuRequested.connect(_menu)
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
        6: "Death.",
    }

    def _on_exhaustion_changed(self, v: int):
        self.char["exhaustion"] = v
        self._refresh_exhaustion_label()
        self._refresh_active_conditions()
        self.ctrl.refresh()   # recompute max HP / speed / apply death check
        self._mark_dirty()
        if v >= 6:
            self._toast("Exhaustion level 6 — the character has died")
            self._show_death_screen()
        elif v >= 4:
            self._toast(f"Exhaustion {v}: hit point maximum halved")

    def _refresh_exhaustion_label(self):
        if not hasattr(self, "_exh_effect_lbl"):
            return
        lvl = self.char.get("exhaustion", 0)
        text = self._EXHAUSTION_EFFECTS.get(lvl, "")
        self._exh_effect_lbl.setText(text)
        self._exh_effect_lbl.setVisible(bool(text))
        _LEVEL = {1: "Disadvantage on ability checks", 2: "Speed halved",
                  3: "Disadvantage on attack rolls and saving throws",
                  4: "Hit point maximum halved", 5: "Speed reduced to 0", 6: "Death"}
        for n, pip in enumerate(getattr(self, "_exh_pips", []), start=1):
            on = n <= lvl
            pip.setStyleSheet(
                f"QPushButton{{background:{CRIM2 if on else 'transparent'};"
                f"border:2px solid {CRIM2 if on else BORDER2};border-radius:8px;"
                f"padding:0px;min-height:0px;}}"
                f"QPushButton:hover{{border-color:{CRIM2};}}")
            pip.setToolTip(f"Level {n}: {_LEVEL[n]} (and everything below it)"
                           + ("\nClick to take this level off" if n == lvl else ""))
        if hasattr(self, "_exh_level_lbl"):
            self._exh_level_lbl.setText(f"Level {lvl}" if lvl else "None")
            self._exh_level_lbl.setStyleSheet(
                f"color:{CRIM2 if lvl else TEXT3};font-size:{FS_TINY}px;font-weight:700;"
                f"background:transparent;border:none;")

    def _refresh_active_conditions(self):
        """The Conditions page: a row for each condition on you -- its icon
        and name; what it does on hover, and a right-click to take it off or
        read the full rules. One another condition brings with it (Stunned
        -> Incapacitated, Unconscious -> Prone) says what it's from, and goes
        when that one does. The tab says how many there are."""
        if not hasattr(self, "_active_cond_lay"):
            return
        lay = self._active_cond_lay
        # the rows sit above the permanent tail: the "none" line, and a stretch
        while lay.count() > 2:
            w = lay.takeAt(0).widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        def _menu(pos, row, cond, removable, cause):
            m = QMenu(row)
            if removable:
                m.addAction(f"Take {cond} off",
                            lambda c=cond: QTimer.singleShot(0, self, lambda: self._cond_checks[c].setChecked(False)))
            else:
                a = m.addAction(f"Goes when {cause} does"); a.setEnabled(False)
            m.addAction("Details…", lambda c=cond: self._show_condition_details(c))
            m.exec(row.mapToGlobal(pos))

        def _row(cond, title, removable, cause=""):
            alpha = 0x22 if removable else 0x10
            under = tint(SURF, CRIMSON, alpha)
            ink = readable(CRIM2 if removable else TEXT2, under)
            row = QFrame(); row.setObjectName("condRow")
            row.setStyleSheet(
                f"QFrame#condRow{{background:{qa(CRIMSON, alpha)};"
                f"border:1px solid {qa(CRIMSON, 0x88 if removable else 0x44)};border-radius:6px;}}")
            rl = QHBoxLayout(row); rl.setContentsMargins(8,5,8,5); rl.setSpacing(7)
            icon = CONDITIONS.get(cond, {}).get("icon")
            if icon:
                rl.addWidget(_icons.icon_label(icon, 16, ink))
            rl.addWidget(_lbl(title, ink, FS_SMALL, bold=True, wrap=False), 1)
            summary = CONDITIONS.get(cond, {}).get("summary", "")
            row.setToolTip(f"<b>{cond}</b>" + (f" (from {cause})" if cause else "")
                           + (f"<br>{summary}" if summary else "")
                           + "<br><br><i>Right-click: "
                           + ("take it off, or " if removable else "") + "the full rules</i>")
            row.setContextMenuPolicy(Qt.CustomContextMenu)
            row.customContextMenuRequested.connect(
                lambda pos, r=row, c=cond, rm=removable, cs=cause: _menu(pos, r, c, rm, cs))
            return row

        on = set(self.char.get("conditions", []))
        rows = [_row(c, c, True) for c in self._cond_checks if c in on]
        from dnd_app.core.calculator import implied_conditions
        implied = implied_conditions(self.char)
        rows += [_row(c, f"{c} · from {', '.join(causes)}", False, ", ".join(causes))
                 for c, causes in implied.items()]
        for i, row in enumerate(rows):
            lay.insertWidget(i, row)
        self._active_cond_none_lbl.setVisible(not rows)
        if hasattr(self, "_cond_clear_act"):
            self._cond_clear_act.setEnabled(bool(on))
        if hasattr(self, "_ce_bar"):
            n = len(on) + len(implied) + (1 if self.char.get("exhaustion", 0) else 0)
            self._ce_bar.setTabText(0, "Conditions" + (f" ({n})" if n else ""))

    def _show_condition_details(self, cond: str):
        """A condition's full rules, from its row's right-click menu."""
        data = CONDITIONS.get(cond, {})
        text = "\n".join(f"• {e}" for e in data.get("effects", []))
        if data.get("source"):
            text += f"\n\n*{data['source']}*"
        show_details(self, cond, details_markdown(text))

    def _clear_conditions(self):
        """Clear all, from the Add condition menu: every condition off.
        (Exhaustion stays -- it's a level a long rest takes down.)"""
        if not self.char.get("conditions"):
            return
        self.char["conditions"] = []
        for act in self._cond_checks.values():
            act.blockSignals(True); act.setChecked(False); act.blockSignals(False)
        self._refresh_active_conditions()
        self._mark_dirty()
        self._apply_turn_state()     # Incapacitated/Surprised no longer block the turn
        self.ctrl.refresh()

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
        """The health bar -- the window's menu bar (main_window.py) -- shows
        the HP in the boxes here: current and temp of max, a beast form's
        own while Wild Shaped. Safe to call from any HP change."""
        if not hasattr(self, "_hp_max_hp"): return
        self.health_changed.emit(self._hp_current_hp.value(), self._hp_max_hp.value(),
                                 self._hp_temp_hp.value(), bool(self.char.get("_wildshape_active")))

    # ── Toast notifications (non-blocking) ────────────────────────────────────
    def _spend_hit_die(self, die_key: str):
        import random
        hd = self.char.get("hit_dice", {}).get(die_key)
        if not hd or hd.get("remaining", 0) <= 0:
            return
        sides = int(die_key[1:])
        con = ability_mod(self.char, "CON")
        # what changes a Hit Die's healing (Durable, Dwarven Fortitude, Vigor
        # of the Hill Giant, a Periapt of Wound Closure) -- core, shared with
        # the Rest dialog's dice and Android
        from dnd_app.core.character import roll_hit_die
        roll, heal = roll_hit_die(self.char, sides)
        hd["remaining"] -= 1
        cur, mx = self.char.get("current_hp", 0), self.char.get("max_hp", 0)
        self.char["current_hp"] = min(mx, cur + heal)
        if hasattr(self, "_hp_current_hp"):
            self._hp_current_hp.setValue(self.char["current_hp"])
        self._toast(f"Spent {die_key}: rolled {roll} {con:+d} CON → healed {heal} HP "
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

    def _attack_row_layout(self, row_f):
        """An attack row's layout: one line (name, to-hit, damage, the Hit
        button...) and room under it for the extra damage its hits carry
        (_add_damage_riders). Returns the line."""
        outer = QVBoxLayout(row_f); outer.setContentsMargins(10, 8, 10, 8); outer.setSpacing(4)
        line = QHBoxLayout(); line.setSpacing(10)
        outer.addLayout(line)
        row_f._line, row_f._outer = line, outer
        return line

    def _add_damage_riders(self, row_f, weapon, riders=None):
        """Under an attack row, the extra damage its hits carry -- spells,
        class features, race traits, magic items (core/riders.py) -- each
        with its damage type, as plain wrapped text (what to add is the
        player's roll). Hover for what each one is."""
        from dnd_app.core.riders import weapon_riders, rider_text, rider_tip
        riders = weapon_riders(self.char, weapon) if riders is None else riders
        text = rider_text(riders)
        if not text:
            return
        lbl = _lbl(text, TEXT2, FS_SMALL, wrap=True)
        lbl.setObjectName("weaponRiders")
        lbl.setToolTip(rider_tip(riders))
        row_f._outer.addWidget(lbl)

    def _add_weapon_row(self, wpn_name, is_offhand=False):
        """One weapon in hand. Its numbers come from core/attacks.py
        weapon_attack -- the same as Android's Combat screen -- and this
        lays them out: name, to-hit, damage and type, what's on now under
        it (and the off-hand attack, holding two), then Hit."""
        from dnd_app.core.attacks import weapon_attack
        from dnd_app.core.riders import rider_text
        from dnd_app.core.ammo import ammo_label, ammo_count, set_ammo
        from dnd_app.core.calculator import get_condition_attack_status
        w = weapon_attack(self.char, wpn_name)
        name = wpn_name
        atk = sign(w["atk"])

        row_f = QFrame()
        row_f.setStyleSheet(f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;}}")
        rl = self._attack_row_layout(row_f)
        rl.addWidget(_lbl(name, TEXT, FS_BODY, bold=True, wrap=False))
        # a reminder of what the sheet knows gives advantage or disadvantage
        # (the roll is one d20 either way -- the table decides)
        cond_status = get_condition_attack_status(self.char)
        atk_text = f"{atk} to hit"
        if cond_status["advantage"] or cond_status["disadvantage"]:
            atk_text += "  (" + "/".join(t for t, on in (("ADV", cond_status["advantage"]),
                                                         ("DISADV", cond_status["disadvantage"])) if on) + ")"
        atk_lbl = _lbl(atk_text, TEAL2 if w["proficient"] else AMBER, FS_BODY, wrap=False)
        if not w["proficient"]:
            atk_lbl.setToolTip(
                f"Not proficient with {name} — proficiency bonus (+{w['pb']}) "
                f"is not added to this attack roll.")
        elif cond_status["sources"]:
            atk_lbl.setToolTip(cond_status["note"] or f"Source: {', '.join(cond_status['sources'])}")
        else:
            atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _w=w, _atk=atk:
            self._show_breakdown_popup(f"{name} — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _w["stat"], _w["proficient"], _w["magic_bonus"]),
                _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        if w["reckless"]:
            reckless_badge = _lbl("Reckless (adv)", GOLD2, FS_TINY, bold=True, wrap=False)
            reckless_badge.setToolTip("Reckless Attack is active: advantage on this attack, "
                                       "but attack rolls against you also have advantage until your next turn.")
            rl.addWidget(reckless_badge)
        dmg_lbl = _lbl(f"{w['damage']} {w['damage_type']}", GOLD2, FS_BODY, wrap=False)
        if w["flat_sources"]:
            dmg_lbl.setToolTip("Includes " + ", ".join(w["flat_sources"]))
        rl.addWidget(dmg_lbl)
        # what Green-Flame Blade and Booming Blade swing (spells.py)
        if not hasattr(self, "_weapon_row_stats"):
            self._weapon_row_stats = {}
        self._weapon_row_stats[wpn_name] = {"name": wpn_name, "atk": atk, "type": w["damage_type"],
                                            "damage": w["damage"], "melee": w["melee"],
                                            "riders": rider_text(w["riders"])}
        self._add_damage_riders(row_f, wpn_name, w["riders"])
        if w["offhand"]:
            off = _lbl(f"Off-hand attack (a bonus action): {w['offhand']} {w['damage_type']}",
                       TEXT2, FS_SMALL, wrap=True)
            off.setToolTip("Holding two weapons, the bonus action attack with a light one adds "
                           "no ability modifier to its damage, unless you have Two-Weapon Fighting.")
            row_f._outer.addWidget(off)
        if w["magic_bonus"]:
            tip_src = wpn_name if w["named_bonus"] else f"+{w['magic_bonus']} enchantment"
            magic_badge = _lbl(f"✦ +{w['magic_bonus']}", AMBE2, FS_TINY, bold=True, wrap=False)
            magic_badge.setToolTip(f"Magical weapon: +{w['magic_bonus']} to attack and damage rolls\nSource: {tip_src}")
            rl.addWidget(magic_badge)
        if w["material"]:
            material_badge = _lbl(f"{w['material']}", TEAL2, FS_TINY, bold=True, wrap=False)
            if w["material"] == "Silvered":
                material_badge.setToolTip(
                    "Silvered weapon: this weapon's damage counts as silvered for the purpose "
                    "of overcoming a creature's resistance or immunity to nonmagical attacks "
                    "(e.g. many lycanthropes and certain other creatures).")
            else:
                material_badge.setToolTip(
                    "Adamantine weapon: whenever this weapon hits an object, the hit is a "
                    "critical hit.")
            rl.addWidget(material_badge)
        if w["can_power_attack"]:
            pa_cb = QCheckBox("Power Attack (-5/+10)")
            pa_cb.setChecked(w["power_attack"])
            pa_cb.setStyleSheet(f"QCheckBox{{color:{CRIM2 if w['power_attack'] else TEXT3};font-size:{FS_TINY}px;font-weight:700;}}")
            pa_cb.setToolTip(
                f"{'Great Weapon Master' if not w['ranged'] else 'Sharpshooter'}: "
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
        # properties (Versatile, Heavy, range...) on hover rather than inline:
        # the row stays one line with its Hit button in view
        if w["props"]:
            row_f.setToolTip(f"Properties: {', '.join(str(p) for p in w['props'])}")
        rl.addStretch()

        # ── Ammo counter (ranged non-thrown weapons) ──────────────────────────
        # Shows what the inventory holds (bundles count every piece in them);
        # click to change how many you have -- the Gear tab follows, and an
        # edit there (or another weapon's shot) updates every counter
        # (_refresh_ammo_counters).
        ammo_key = w["ammo"]
        if ammo_key:
            ammo_lbl = QPushButton(f"{ammo_label(ammo_key)}: {ammo_count(self.char, ammo_key)}")
            _icons.set_button_icon(ammo_lbl, "ammo", 13)
            ammo_lbl.setToolTip(f"{ammo_label(ammo_key)} in your inventory — click to change")
            ammo_lbl.setStyleSheet(
                _btn("", AMBER, variant="chip", radius=5, text_color=AMBE2,
                     border_alpha=0x55, hover_bg_alpha=0x33, font_size=FS_TINY,
                     padding="2px 6px").styleSheet())
            ammo_lbl.setFixedHeight(26)
            def _set_ammo(checked=False, _key=ammo_key):
                label = ammo_label(_key)
                n, ok = QInputDialog.getInt(
                    None, label, f"How many {label.lower()} do you have?",
                    ammo_count(self.char, _key), 0, 9999)
                if ok:
                    set_ammo(self.char, _key, n)
                    self._refresh_gear_equipment()
                    self._mark_dirty()
            ammo_lbl.clicked.connect(_set_ammo)
            self._ammo_counters.append((ammo_key, ammo_lbl))
            rl.addWidget(ammo_lbl)

        # ── Attack roll button: the roll, then what you can add ──────────────
        hit_btn = _icons.with_icon(_btn("Hit", TEAL, variant="danger", height=26, width=66,
                        radius=5, border_width=1, text_color=TEAL2, hover_text="white",
                        font_size=FS_TINY, padding="0px"), "dice", 12)
        hit_btn.setObjectName(f"hit_{wpn_name}")
        hit_btn.clicked.connect(lambda checked=False, _w=w: self._attack(_w))
        rl.addWidget(hit_btn)

        # Attach the completed row to the combat tab (this line was lost in a
        # past refactor — without it every weapon row was built then dropped).
        self._place_weapon_row(row_f)
        self._weapon_row_widgets.append(row_f)

    def _attack(self, row):
        """Hit on any attack row: what you'd decide before the d20 asked
        first (Inspiration, Tides of Chaos, a Portent roll), a shot uses
        one piece of its ammunition, then the roll, what you can add to it
        (an Add pays for it and rolls it now: Precision Attack, Lucky...),
        what to roll if it hits and what you can add to the hit, with each
        one's cost (core/attacks.py) -- only what you can pay for right
        now. "It hit" pays for the ticked ones (a slot, ki, a die, once a
        turn...) and sets off what the hit carries (a smite); "Missed" only
        takes the bonus action ones. The toast says what to roll. True once
        the attack is made."""
        from dnd_app.core.attacks import (attack_before, roll_attack, attack_report, add_to_attack,
                                          take_attack_options)
        from dnd_app.core.ammo import ammo_label, spend_ammo
        from dnd_app.ui_desktop.dialogs.attack import AttackDialog

        def free():
            return [b for b in ("Action", "Bonus Action", "Reaction")
                    if self._turn_counts.get(b, 0) < self._turn_limit(b)]
        pre = self._ask_through(row["name"], lambda a: attack_before(self.char, row, a, free()))
        if pre is None:
            return False
        if row.get("ammo"):
            label = ammo_label(row["ammo"])
            if not spend_ammo(self.char, row["ammo"]):
                QMessageBox.warning(None, "No Ammo",
                                    f"Out of {label.lower()}!\nClick the {label} counter to add more.")
                return False
            self._refresh_gear_equipment()
            self._mark_dirty()
        now = {"roll": roll_attack(self.char, row, before=pre.get("before", ""), free=free())}
        now["added"] = bool(now["roll"]["state"]["spent"])     # Inspiration spent before the roll
        for slot in now["roll"]["state"]["slots"]:            # Cosmic Omen's reaction
            self._mark_turn_used(slot)
        if now["added"]:
            self._mark_dirty()

        def add(key):
            # an Add on the roll: paid for and rolled now, the dialog shows it
            res = self._ask_through(row["name"], lambda a: add_to_attack(self.char, row, now["roll"], key, a,
                                                                        free()))
            if not res:
                return None
            if not res.get("ok"):
                if res.get("toast"):
                    self._toast(res["toast"])
                return None
            now["roll"], now["added"] = res["roll"], True
            for slot in res.get("slots", []):
                self._mark_turn_used(slot)
            self._mark_dirty()
            return attack_report(self.char, row, now["roll"], free())
        dlg = AttackDialog(attack_report(self.char, row, now["roll"], free()), self, on_add=add)
        if dlg.exec() != QDialog.Accepted:
            if now["added"]:
                QTimer.singleShot(0, self.ctrl.refresh)
            return False
        picked, hit = dlg.ticked(), bool(dlg.hit)
        res = self._ask_through(row["name"], lambda a: take_attack_options(
            self.char, row, picked, a, hit=hit, roll=now["roll"]))
        if not res:
            return False
        for slot in res.get("slots", []):
            self._mark_turn_used(slot)
        self._apply_turn_state()          # the Sneak Attack chip follows
        if res.get("toast"):
            self._toast(res["toast"])
        if res.get("refresh") or now["added"]:
            self._mark_dirty()
            QTimer.singleShot(0, self.ctrl.refresh)
        return True

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
            sp.setFixedWidth(78); sp.setFixedHeight(32)   # "-  n  +" needs the room
            sp.setAlignment(Qt.AlignCenter)
            sp.setStyleSheet(
                f"QSpinBox{{background:{SURF2};border:2px solid {qa(TEAL,0x66)};border-radius:6px;"
                f"font-weight:700;font-size:{FS_SMALL}px;color:{TEAL2};padding:0 2px;}}"
                f"QSpinBox::up-button,QSpinBox::down-button{{width:18px;background:{BORDER};}}")
            col.addWidget(_lbl(f"d{hd}", TEXT3, FS_TINY, align=Qt.AlignCenter))
            sp.valueChanged.connect(
                lambda v, k=hd_key, tot=hd_data.get("total", lvl):
                    self._on_hd_changed(k, v, tot))
            self._hd_layout.addLayout(col)

    def _add_attack_row(self, a):
        """One attack that isn't a weapon in your hand (core/attacks.py: a
        Monk's unarmed strike, a bite, armor spikes, a beast's claws): its
        name and what it is, to-hit, damage and type, the extra damage its
        hits carry under it, and Hit. The row's tint says what kind it is;
        the words stay plain."""
        tone = {"monk": TEAL, "rage": CRIM2, "natural": TEAL2,
                "armor": PURPLE, "beast": PURPLE}.get(a["tone"], TEAL2)
        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(tone,0x14)};border:1px solid {qa(tone,0x55)};border-radius:8px;}}")
        rl = self._attack_row_layout(row_f)
        rl.addWidget(_lbl(a["name"], TEXT, FS_BODY, bold=True, wrap=False))
        if a["badge"]:
            badge = _lbl(a["badge"], TEXT2, FS_TINY, bold=True, wrap=False)
            badge.setToolTip(a["note"])
            rl.addWidget(badge)
        atk = sign(a["atk"]) if a["atk"] is not None else ""
        if atk:
            atk_lbl = _lbl(f"{atk} to hit", TEAL2, FS_BODY, wrap=False)
            if a["stat"]:
                atk_lbl.setToolTip("Right-click for a breakdown")
                atk_lbl.contextMenuEvent = (lambda e, _a=a, _atk=atk:
                    self._show_breakdown_popup(f"{_a['name']} — Attack Bonus",
                        get_weapon_attack_breakdown(self.char, _a["stat"], True, _a["atk_extra"]),
                        _atk, e.globalPos()))
            rl.addWidget(atk_lbl)
        if a["damage"]:
            rl.addWidget(_lbl(f"{a['damage']} {a['damage_type']}", GOLD2, FS_BODY, wrap=False))
        self._add_damage_riders(row_f, None, a["riders"])
        # what it is and which ability it uses are on hover -- keeps the
        # row narrow enough that its Hit button stays in view
        row_f.setToolTip(a["note"] + (f"\nAttack and damage use {a['stat']}" if a["stat"] else ""))
        rl.addStretch()
        if atk:
            hit_btn = _icons.with_icon(_btn("Hit", tone, variant="danger", height=26, width=66,
                            radius=5, border_width=1, hover_text="white",
                            font_size=FS_TINY, padding="0px"), "dice", 12)
            hit_btn.setObjectName(f"hit_{a['name']}")
            hit_btn.clicked.connect(lambda checked=False, _a=a: self._attack(_a))
            rl.addWidget(hit_btn)
        self._place_weapon_row(row_f)
        self._weapon_row_widgets.append(row_f)

    def _place_weapon_row(self, row_f):
        """Add a finished attack row to the Weapons list, with everything in
        it (name, to-hit, damage, the Hit button...) centred on one line --
        otherwise the taller buttons sit lower than the text beside them."""
        lay = getattr(row_f, "_line", None) or row_f.layout()
        for i in range(lay.count() if lay else 0):
            w = lay.itemAt(i).widget()
            if w is not None:
                lay.setAlignment(w, Qt.AlignVCenter)
        self._weapon_rows.addWidget(row_f)

    def _refresh_combat_weapons(self):
        """Rebuild the weapon rows in the combat tab from char[equipped_weapons]."""
        while self._weapon_rows.count():
            item = self._weapon_rows.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().setParent(None)
                item.widget().deleteLater()
        self._weapon_row_widgets.clear()
        self._ammo_counters.clear()
        self._weapon_row_stats = {}
        # attacks that aren't a weapon in hand -- Martial Arts, natural
        # weapons, the unarmed strike, Wild Shape... (core/attacks.py, the
        # same rows Android's Combat screen shows)
        from dnd_app.core.attacks import other_attacks
        for a in other_attacks(self.char):
            self._add_attack_row(a)
        for idx, wpn in enumerate(self.char.get("equipped_weapons",[])):
            self._add_weapon_row(wpn, is_offhand=(idx > 0))
        self._fit_weapons_card()

    def _fit_weapons_card(self):
        """The weapons card is at least as wide as its widest row, so no
        row is cut off: the other cards give it the room."""
        card = getattr(self, "_weapons_card", None)
        if card is None:
            return
        rows = [w for w in self._weapon_row_widgets if w is not None]
        widest = max((w.sizeHint().width() for w in rows), default=0)
        scroll_bar = self._weapons_scroll.verticalScrollBar().sizeHint().width()
        m = card.layout().contentsMargins()
        card.setMinimumWidth(min(620, widest + scroll_bar + m.left() + m.right() + 6) if widest else 0)

    def _refresh_ammo_counters(self):
        """Every weapon's ammo counter shows the inventory as it is now --
        after a shot, a Gear tab edit, or an item added or removed."""
        from dnd_app.core.ammo import ammo_label, ammo_count
        for kind, btn in self._ammo_counters:
            try:
                btn.setText(f"{ammo_label(kind)}: {ammo_count(self.char, kind)}")
            except RuntimeError:   # its row was rebuilt meanwhile
                pass

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
            from dnd_app.data.statblocks import WILDSHAPE_BEASTS
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
                        self._toast("Beast form dropped to 0 HP — reverted to normal form")
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
            self._hp_temp_hp.valueChanged.connect(lambda v: self._update_hp_bar())
            self._hp_signals_connected = True

        # What's worn, on the weapons card's top line
        _armor_name = char.get("armor_worn", "No Armor")
        if _armor_name and _armor_name != "No Armor":
            _abase = next((a for a in ARMOR if a[0] == _armor_name), None)
            self._armor_display.setText(_armor_name)
            self._armor_display.setToolTip(f"{_armor_name}: base AC {_abase[2]}" if _abase else _armor_name)
            self._armor_display.setStyleSheet(
                f"color:{TEXT};font-size:{FS_SMALL}px;font-weight:700;background:transparent;border:none;")
        else:
            self._armor_display.setText("No armor")
            self._armor_display.setToolTip("")
            self._armor_display.setStyleSheet(
                f"color:{TEXT3};font-size:{FS_SMALL}px;background:transparent;border:none;")
        has_shield = bool(char.get("shield"))
        self._shield_display.setText("Shield +2" if has_shield else "No shield")
        self._shield_display.setStyleSheet(
            f"color:{GOLD2 if has_shield else TEXT3};font-size:{FS_SMALL}px;"
            f"font-weight:{700 if has_shield else 400};background:transparent;border:none;")

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
        cols = 2   # (the HP card is two columns wide)

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

