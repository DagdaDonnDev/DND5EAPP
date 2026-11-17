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
    update_all, get_ac, get_prof_bonus, get_initiative, ability_check_bonus,
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


class RollRow(QPushButton):
    """One roll on an ability's card -- its check or its save -- as a whole
    row to click: what it is on the left, the bonus and a d20 on the
    right. The check and the save are the same row, so the card reads as
    two rolls of one ability."""

    def __init__(self, word: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip); self.setAccessibleName(tooltip)
        self.setFixedHeight(40)
        row = QHBoxLayout(self); row.setContentsMargins(10, 0, 8, 0); row.setSpacing(6)
        self.sym = _lbl("", TEXT3, FS_BODY, bold=True, wrap=False)
        self.sym.setVisible(False)
        row.addWidget(self.sym)
        self.word = _lbl(word, TEXT2, FS_BODY, wrap=False)
        row.addWidget(self.word)
        self.badges = QHBoxLayout(); self.badges.setSpacing(4)
        row.addLayout(self.badges)
        row.addStretch()
        self.value = _lbl("", TEXT2, FS_TITLE, bold=True, wrap=False)
        row.addWidget(self.value)
        self.die = QLabel(); self.die.setStyleSheet("background:transparent;border:none;")
        self.die.setPixmap(_icons.pixmap("dice", _icons.scaled(18), TEAL2))
        row.addWidget(self.die)
        self.set_marked(False)

    def set_marked(self, on: bool):
        """A proficient save: an indigo edge and tint, as a proficient skill."""
        edge, fill = (qa(INDIGO, 0xaa), qa(INDIGO, 0x1c)) if on else (BORDER, SURF)
        self.setStyleSheet(
            f"QPushButton{{background:{fill};border:1px solid {edge};border-radius:8px;"
            f"padding:0;min-height:40px;max-height:40px;text-align:left;}}"
            f"QPushButton:hover{{background:{qa(TEAL, 0x2a)};border-color:{TEAL};}}"
            f"QPushButton:pressed{{background:{qa(TEAL, 0x55)};}}"
            f"QLabel{{background:transparent;border:none;}}")

    def set_value(self, val: int):
        self.value.setText(sign(val))
        col = TEAL2 if val > 0 else (CRIM2 if val < 0 else TEXT2)
        self.value.setStyleSheet(f"color:{col};font-size:{FS_TITLE}px;font-weight:700;background:transparent;border:none;")


class AbilityCard(QFrame):
    """One ability on the Overview: its name and score, then its two rolls
    as matching rows -- the check, and the saving throw (◆ when proficient;
    right-click it to change that) with any advantage or condition badge.
    Click either row to roll it."""
    roll_requested = Signal(str)

    def __init__(self, ab, score, parent=None):
        super().__init__(parent)
        self.ab = ab
        self.setObjectName("abilityCard")
        self.setStyleSheet(f"QFrame#abilityCard{{background:{SURF2};border:1px solid {BORDER};border-radius:10px;}}"
                           f"QFrame#abilityCard QLabel{{background:transparent;border:none;}}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 6, 10, 10); lay.setSpacing(6)
        # the name, and the score with what it is beside it
        head = QHBoxLayout(); head.setSpacing(6)
        head.addWidget(_lbl(AB_FULL[ab].upper(), GOLD2, FS_SMALL, bold=True, wrap=False), 0, Qt.AlignVCenter)
        head.addStretch()
        head.addWidget(_lbl("score", TEXT3, FS_SMALL, wrap=False), 0, Qt.AlignVCenter)
        self._score = _lbl("", TEXT, FS_TITLE, bold=True, wrap=False)
        self._score.setToolTip(f"Your {AB_FULL[ab]} score")
        head.addWidget(self._score, 0, Qt.AlignVCenter)
        lay.addLayout(head)
        lay.addStretch(1)
        self.check_btn = RollRow("Check", f"Roll a {AB_FULL[ab]} check")
        self.check_btn.setObjectName(f"abilityCheck_{ab}")
        self.check_btn.clicked.connect(lambda: self.roll_requested.emit(self.ab))
        self._mod = self.check_btn.value
        lay.addWidget(self.check_btn)
        self.save_btn = RollRow("Save", f"Roll a {AB_FULL[ab]} save · right-click to change its proficiency")
        self.save_btn.setObjectName(f"saveRoll_{ab}")
        self.save_btn.sym.setVisible(True)
        self.save_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        self.save_frame = self.save_btn          # (right-clicked for the proficiency)
        lay.addWidget(self.save_btn)
        self.set_score(score)

    def set_score(self, score):
        self._score.setText(str(score))
        self.check_btn.set_value((score - 10) // 2)

    def set_save(self, val: int, proficient: bool):
        self.save_btn.set_value(val)
        self.save_btn.set_marked(proficient)
        self.save_btn.sym.setText("◆" if proficient else "—")
        self.save_btn.sym.setStyleSheet(f"color:{INDIGO if proficient else TEXT3};font-size:{FS_BODY}px;"
                                        f"font-weight:700;background:transparent;border:none;")


class AbilitiesMixin:
    def _build_tab_overview(self):
        """The Overview: your abilities and saves, proficiencies, skills and
        senses on one page -- what you look up during play rather than act
        on (that's Combat). It fills the window; a small one scrolls."""
        tab = QScrollArea(); tab.setWidgetResizable(True); tab.setFrameShape(QFrame.NoFrame)
        tab.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        w = QWidget(); tab.setWidget(w)
        root = QHBoxLayout(w); root.setContentsMargins(16, 16, 16, 16); root.setSpacing(16)
        left = QVBoxLayout(); left.setSpacing(12)
        right = QVBoxLayout(); right.setSpacing(12)
        left.addWidget(self._build_abilities_card(), 1)
        left.addWidget(self._build_proficiencies_card(), 0)
        right.addWidget(self._build_skills_card(), 1)
        right.addWidget(self._build_senses_card(), 0)
        root.addLayout(left, 100); root.addLayout(right, 108)
        return tab

    def _build_abilities_card(self):
        ab_card = _card(); abcl = QVBoxLayout(ab_card); abcl.setContentsMargins(16,14,16,16); abcl.setSpacing(8)
        head = QHBoxLayout(); head.setSpacing(8)
        head.addWidget(_lbl("ABILITIES AND SAVING THROWS", GOLD, FS_SMALL, bold=True, wrap=False))
        head.addStretch()
        # Reset, as the skills have (their legend says what ◆ and — are)
        reset_btn = _btn("↺ Reset", CRIMSON, variant="danger", bg_alpha=0x22, border_width=1,
                         text_color=CRIM2, hover_text="white", font_size=FS_SMALL, padding="2px 12px",
                         height=28, min_height0=True,
                         tooltip="Saving throws back to what your class, feats and features give you: "
                                 "undoes every change made by right-clicking")
        reset_btn.setObjectName("resetSaveProfs")
        reset_btn.setAccessibleName("Reset saving throw proficiencies")
        reset_btn.clicked.connect(self._reset_save_profs)
        head.addWidget(reset_btn)
        abcl.addLayout(head)
        grid = QGridLayout(); grid.setSpacing(10)
        self._ab_blocks = {}
        self._save_widgets = {}
        self._save_adv_badges, self._save_cond_badges = {}, {}
        saves = all_saving_throw_bonuses(self.char)
        for i, ab in enumerate(ABILITIES):
            card = AbilityCard(ab, ability_score(self.char, ab))
            card.roll_requested.connect(
                lambda a: self._quick_roll_toast(f"{AB_FULL[a]} check", ability_check_bonus(self.char, a), "check", a))
            self._ab_blocks[ab] = card
            card.check_btn.set_value(ability_check_bonus(self.char, ab))
            grid.addWidget(card, i // 3, i % 3)
            rl = card.save_btn.badges
            # advantage (a race's, a class's) and a condition's auto-fail or
            # disadvantage: parented before they're shown (see the badge
            # functions below), so none flashes up as a window of its own
            adv_badge = _icons.icon_label("adv", 16, "GREEN2")
            rl.addWidget(adv_badge); self._save_adv_badges[ab] = adv_badge
            self._update_save_advantage_badge(ab)
            cond_badge = _lbl("", CRIM2, FS_SMALL, bold=True, wrap=False)
            rl.addWidget(cond_badge); self._save_cond_badges[ab] = cond_badge
            self._update_save_condition_badge(ab)
            if self.char.get("_paladin_aura"):
                rl.addWidget(_lbl(f"+{max(1, ability_mod(self.char, 'CHA'))} Aura", PURP2, FS_SMALL, wrap=False))
            card.save_btn.clicked.connect(lambda checked=False, a=ab:
                                          self._quick_roll_toast(f"{AB_FULL[a]} save",
                                                                 all_saving_throw_bonuses(self.char).get(a, 0), "save", a))
            card.save_btn.customContextMenuRequested.connect(
                lambda pos, a=ab, f=card.save_btn: self._show_save_prof_menu(a, f.mapToGlobal(pos)))
            self._save_widgets[ab] = (card.save_btn.sym, card.save_btn.value)
            self._style_save(ab, saves.get(ab, 0))
        for r in range(2):
            grid.setRowStretch(r, 1)
        abcl.addLayout(grid, 1)
        return ab_card

    def _build_senses_card(self):
        """Senses: the three passive scores in a column, and beside them a
        chip for each sense -- its range, where it's from on hover; one
        another covers (darkvision beside Devil's Sight) greyed out."""
        card = _card(qa(TEAL, 0x55)); cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 12); cl.setSpacing(6)
        cl.addWidget(_lbl("SENSES", TEAL2, FS_SMALL, bold=True))
        row = QHBoxLayout(); row.setSpacing(12)
        col = QVBoxLayout(); col.setSpacing(6)
        self._passive_boxes = {}
        for key in ("Perception", "Investigation", "Insight"):
            f = QFrame(); f.setObjectName("passiveBox")
            f.setStyleSheet(f"QFrame#passiveBox{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;}}"
                            f"QFrame#passiveBox QLabel{{background:transparent;border:none;}}")
            fl = QHBoxLayout(f); fl.setContentsMargins(12, 4, 12, 4)
            fl.addWidget(_lbl(f"Passive {key}", TEXT2, FS_SMALL, bold=True, wrap=False))
            fl.addStretch()
            v = _lbl("", TEAL2, FS_TITLE, bold=True, wrap=False)
            fl.addWidget(v)
            f.setFixedWidth(210)
            col.addWidget(f)
            self._passive_boxes[key] = (f, v)
        col.addStretch()
        row.addLayout(col)
        self._sense_chips = QGridLayout(); self._sense_chips.setSpacing(6)
        self._sense_chips.setContentsMargins(0, 0, 0, 0)
        chips_w = QWidget(); chips_w.setLayout(self._sense_chips)
        chips_w.setStyleSheet("background:transparent;")
        row.addWidget(chips_w, 1, Qt.AlignTop)
        cl.addLayout(row)
        self._refresh_senses()
        return card

    def _refresh_senses(self):
        boxes = getattr(self, "_passive_boxes", None)
        if not boxes:
            return
        from dnd_app.core.calculator import (get_passive_investigation, get_passive_insight,
                                             get_skill_advantage_status, sense_list)
        vals = {"Perception": get_passive_perception(self.char),
                "Investigation": get_passive_investigation(self.char),
                "Insight": get_passive_insight(self.char)}
        for key, (f, v) in boxes.items():
            v.setText(str(vals[key]))
            status = get_skill_advantage_status(self.char, key)
            tip = f"10 + your {key} bonus"
            if status["net"] == "advantage":
                tip += "\n+5: advantage on " + key + " checks (" + ", ".join(status["adv_reasons"]) + ")"
            elif status["net"] == "disadvantage":
                tip += "\n\u22125: disadvantage on " + key + " checks (" + ", ".join(status["disadv_reasons"]) + ")"
            f.setToolTip(tip)
        lay = self._sense_chips
        while lay.count():
            it = lay.takeAt(0)
            wdg = it.widget()
            if wdg is not None:
                wdg.setParent(None); wdg.deleteLater()
        senses = sense_list(self.char)
        if not senses:
            lay.addWidget(_lbl("No special senses", TEXT3, FS_SMALL, wrap=False), 0, 0)
            return
        for i, sn in enumerate(senses):
            off = sn["covered"]
            text = f"<b>{sn['name']}</b>" + (f"&nbsp;&nbsp;{sn['range']} ft" if sn["range"] else "")
            if off:
                text = f"<s>{text}</s>"
            chip = QLabel(text); chip.setTextFormat(Qt.RichText)
            chip.setObjectName("senseChip")
            ink = TEXT3 if off else TEAL2
            chip.setStyleSheet(f"QLabel#senseChip{{color:{ink};font-size:{FS_SMALL}px;padding:4px 9px;border-radius:7px;"
                               f"background:{SURF2 if off else qa(TEAL, 0x1f)};border:1px solid {BORDER if off else qa(TEAL, 0x88)};}}")
            chip.setToolTip(sn["source"] + (f"\n{sn['what'][0].upper()}{sn['what'][1:]}" if sn["what"] else ""))
            lay.addWidget(chip, i // 2, i % 2, Qt.AlignLeft)
        lay.setColumnStretch(2, 1)

    # ══ TAB 2: SKILLS & PROFICIENCIES ══════════════════════════════════════════
    def _style_save(self, ab, val):
        """A save's ◆ or —, its bonus, and its row's edge."""
        self._ab_blocks[ab].set_save(val, bool(self.char.get("saving_throws", {}).get(ab)))

    def _show_save_prof_menu(self, ability, global_pos):
        """Right-click a save: Not Proficient or Proficient, the current
        one ticked -- as a skill's menu."""
        from PySide6.QtWidgets import QMenu
        on = bool(self.char.get("saving_throws", {}).get(ability))
        menu = QMenu(self)
        for state, label in ((False, "Not Proficient"), (True, "Proficient")):
            act = menu.addAction(("\u2713 " if state == on else "    ") + label)
            act.triggered.connect(lambda checked=False, st=state: self._set_save_prof(ability, st))
        menu.exec(global_pos)

    def _set_save_prof(self, ability, on):
        # kept as an override on top of what's granted (core/builder.py),
        # so a rebuild doesn't undo it
        from dnd_app.core.builder import set_save_prof
        set_save_prof(self.char, ability, on)
        self.ctrl.refresh()
        self._mark_dirty()

    def _reset_save_profs(self):
        from PySide6.QtWidgets import QMessageBox as _QMB
        if _QMB.question(self, "Reset Saving Throws",
                         "Your saving throw proficiencies go back to what your class, feats and features "
                         "give you, undoing every change made by right-clicking. Continue?",
                         _QMB.Yes | _QMB.No, _QMB.No) != _QMB.Yes:
            return
        from dnd_app.core.builder import reset_save_profs
        reset_save_profs(self.char)
        self.ctrl.refresh()
        self._mark_dirty()
        self._toast("↺ Saving throws reset to what you're given")

    def _quick_roll_toast(self, label: str, bonus: int, kind: str = "check", ability: str = ""):
        """Roll a check, a save or initiative (core/checks.py, the same on
        Android): one d20 with what always applies on it (Reliable
        Talent, Bless...), what you'd decide first asked first (cast
        Guidance, take advantage you have), and what you can add after it
        (a superiority die, Lucky...) in the roll dialog, with its cost.
        Advantage and disadvantage the sheet knows of are a reminder: the
        table decides."""
        from dnd_app.core.calculator import SKILL_ABILITY
        skill = label[:-len(" check")] if label.endswith(" check") and label[:-len(" check")] in SKILL_ABILITY else ""
        if label == "Initiative":
            kind, ability = "initiative", "DEX"
        self._roll_check({"kind": kind, "ability": ability or SKILL_ABILITY.get(skill, ""), "skill": skill,
                          "label": label, "bonus": bonus})

    def _roll_check(self, what):
        """The roll, asking first if there's something to decide; then the
        roll dialog when there's something to add -- each Add pays for it
        and rolls it now, and the dialog shows the new total -- and Done.
        Returns the last result (None if the question before the roll was
        cancelled)."""
        from dnd_app.core.checks import roll_check, add_to_check, finish_check
        from dnd_app.ui_desktop.dialogs.attack import AttackDialog

        def free():
            return [b for b in ("Action", "Bonus Action", "Reaction")
                    if self._turn_counts.get(b, 0) < self._turn_limit(b)]
        res = self._ask_through(what["label"], lambda a: roll_check(self.char, what, a, free()))
        if res is None:
            return None
        self._after_check(res)
        if not res.get("report"):
            return res
        now = {"report": res["report"]}

        def add(key):
            got = self._ask_through(what["label"], lambda a: add_to_check(self.char, now["report"], key, a, free()))
            if not got:
                return None
            if not got.get("ok"):
                if got.get("toast"):
                    self._toast(got["toast"])
                return None
            now["report"] = got["report"]
            for slot in got.get("slots", []):
                self._mark_turn_used(slot)
            self._mark_dirty()
            return got["report"]
        AttackDialog(now["report"], self, on_add=add).exec()
        # Done (or closed): a die that's spent only on a success asks
        res = (self._ask_through(what["label"], lambda a: finish_check(self.char, now["report"], a))
               or finish_check(self.char, now["report"], {"succeeded": "It still failed"}))
        self._after_check(res)
        return res

    def _after_check(self, res):
        """What the roll used: parts of the turn, a spell cast first, the
        toast, and the sheet when something was spent."""
        for slot in res.get("slots", []):
            self._mark_turn_used(slot)
        if res.get("cast"):
            from dnd_app.data.spells import get_spell
            spell = get_spell(res["cast"])
            if spell:
                self._mark_spell_cast_time(spell)
        if res.get("toast"):
            self._toast(res["toast"].replace(" -- ", " — "), 6000)
        if res.get("refresh"):
            self._mark_dirty()
            QTimer.singleShot(0, self.ctrl.refresh)

    def _update_save_advantage_badge(self, ab: str):
        """Sync one saving throw's advantage indicator badge to current
        state — icon, tooltip, and visibility. Called at initial build and
        again from _refresh_abilities_tab so it stays correct if the
        character's class/level changes after the sheet is already open."""
        badge = getattr(self, "_save_adv_badges", {}).get(ab)
        if not badge:
            return
        status = get_save_advantage_status(self.char, ab)
        badge.setVisible(status["has_advantage"])
        if status["has_advantage"]:
            notes = "\n".join(f"• {s['source']}: {s['note']}" for s in status["sources"])
            badge.setToolTip(
                ("Conditional advantage:\n" if status["conditional"] else "Advantage:\n") + notes)

    def _update_save_condition_badge(self, ab: str):
        """Sync one saving throw's condition-based auto-fail/disadvantage
        badge — separate from _update_save_advantage_badge since this
        reflects a genuinely different, transient mechanic (active
        conditions/exhaustion), not racial/class traits. Called at
        initial build and again from _refresh_abilities_tab so it
        updates immediately when a condition checkbox is toggled."""
        badge = getattr(self, "_save_cond_badges", {}).get(ab)
        if not badge:
            return
        from dnd_app.core.calculator import get_condition_save_status
        status = get_condition_save_status(self.char, ab)
        if status["auto_fail"]:
            badge.setVisible(True)
            badge.setText("AUTO-FAIL")
            badge.setToolTip(f"Auto-fails {AB_FULL[ab]} saves: {', '.join(status['sources'])}")
        elif status["disadvantage"]:
            badge.setVisible(True)
            badge.setPixmap(_icons.pixmap("disadv", _icons.scaled(18), "CRIM2"))
            badge.setToolTip(f"Disadvantage on {AB_FULL[ab]} saves: {', '.join(status['sources'])}")
        else:
            badge.setVisible(False)
            badge.setText("")

    def _refresh_abilities_tab(self):
        for ab in ABILITIES:
            score = ability_score(self.char, ab)
            if ab in self._ab_blocks:
                self._ab_blocks[ab].set_score(score)
                # (what the check rolls: the modifier and anything added to it)
                self._ab_blocks[ab].check_btn.set_value(ability_check_bonus(self.char, ab))
        # Saves
        saves = all_saving_throw_bonuses(self.char)
        for ab in self._save_widgets:
            self._style_save(ab, saves.get(ab, 0))
            self._update_save_advantage_badge(ab)
            self._update_save_condition_badge(ab)

        self._refresh_senses()
