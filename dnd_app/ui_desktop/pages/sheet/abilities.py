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


class AbilityCard(QFrame):
    """One ability on the Overview: its name, score and modifier (the
    modifier rolls the check), and under them its saving throw -- the
    proficiency box, the bonus, any advantage or condition badge, and the
    dice that roll it."""
    roll_requested = Signal(str)

    def __init__(self, ab, score, parent=None):
        super().__init__(parent)
        self.ab = ab
        self.setObjectName("abilityCard")
        self.setStyleSheet(f"QFrame#abilityCard{{background:{SURF2};border:1px solid {BORDER};border-radius:10px;}}"
                           f"QFrame#abilityCard QLabel{{background:transparent;border:none;}}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(self); lay.setContentsMargins(12, 8, 10, 8); lay.setSpacing(4)
        lay.addWidget(_lbl(AB_FULL[ab].upper(), TEXT2, FS_TINY, bold=True, wrap=False))
        top = QHBoxLayout(); top.setSpacing(8)
        self._score = _lbl("", TEXT, FS_STAT, bold=True, wrap=False)
        top.addWidget(self._score); top.addStretch()
        self._mod = QPushButton()
        self._mod.setObjectName(f"abilityMod_{ab}")
        self._mod.setCursor(Qt.PointingHandCursor)
        self._mod.setToolTip(f"Roll a {AB_FULL[ab]} check")
        self._mod.setAccessibleName(f"Roll a {AB_FULL[ab]} check")
        self._mod.clicked.connect(lambda: self.roll_requested.emit(self.ab))
        top.addWidget(self._mod, 0, Qt.AlignVCenter)
        lay.addLayout(top)
        lay.addStretch(1)
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background:{BORDER};border:none;")
        lay.addWidget(line)
        self.save_row = QHBoxLayout(); self.save_row.setSpacing(6); self.save_row.setContentsMargins(0, 2, 0, 0)
        lay.addLayout(self.save_row)
        self.set_score(score)

    def set_score(self, score):
        mod = (score - 10) // 2
        self._score.setText(str(score))
        col = TEAL2 if mod > 0 else (CRIM2 if mod < 0 else TEXT2)
        self._mod.setText(sign(mod))
        self._mod.setStyleSheet(
            f"QPushButton{{color:{col};font-size:{FS_TITLE}px;font-weight:700;background:{SURF};"
            f"border:1px solid {BORDER};border-radius:8px;padding:2px 12px;min-height:0px;}}"
            f"QPushButton:hover{{border-color:{TEAL};background:{qa(TEAL, 0x22)};}}")


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
        abcl.addWidget(_lbl("ABILITIES AND SAVING THROWS", GOLD, FS_SMALL, bold=True))
        grid = QGridLayout(); grid.setSpacing(10)
        self._ab_blocks = {}
        self._save_widgets = {}
        self._save_adv_badges, self._save_cond_badges = {}, {}
        saves = all_saving_throw_bonuses(self.char)
        profs = get_saving_throw_profs(class_levels(self.char))
        for i, ab in enumerate(ABILITIES):
            card = AbilityCard(ab, ability_score(self.char, ab))
            card.roll_requested.connect(
                lambda a: self._quick_roll_toast(f"{AB_FULL[a]} check", ability_check_bonus(self.char, a), "check", a))
            self._ab_blocks[ab] = card
            grid.addWidget(card, i // 3, i % 3)
            val = saves.get(ab, 0)
            is_class = ab in profs
            is_p = is_class or self.char.get("saving_throws", {}).get(ab, False)
            rl = card.save_row
            # the save's proficiency: a class's can't be taken off here; one
            # from elsewhere (a feat) can -- the box or a click on the row
            dot = QCheckBox(); dot.setChecked(is_p)
            dot.setEnabled(not is_class)
            dot.setStyleSheet(f"QCheckBox::indicator{{width:13px;height:13px;border-radius:4px;border:2px solid {BORDER2};background:{BG};}}"
                              f"QCheckBox::indicator:checked{{background:{TEAL};border-color:{TEAL2};}}")
            save_word = _lbl("Save", TEXT2, FS_SMALL, wrap=False)
            val_lbl = _lbl(sign(val), TEAL2 if val > 0 else (CRIM2 if val < 0 else TEXT2), FS_LABEL, bold=True, wrap=False)
            rl.addWidget(dot); rl.addWidget(save_word); rl.addWidget(val_lbl)
            # advantage (a race's, a class's) and a condition's auto-fail or
            # disadvantage: parented before they're shown (see the badge
            # functions below), so none flashes up as a window of its own
            adv_badge = _icons.icon_label("adv", 16, "GREEN2")
            rl.addWidget(adv_badge); self._save_adv_badges[ab] = adv_badge
            self._update_save_advantage_badge(ab)
            cond_badge = _lbl("", CRIM2, FS_TINY, bold=True, wrap=False)
            rl.addWidget(cond_badge); self._save_cond_badges[ab] = cond_badge
            self._update_save_condition_badge(ab)
            if self.char.get("_paladin_aura"):
                rl.addWidget(_lbl(f"+{max(1, ability_mod(self.char, 'CHA'))} Aura", PURP2, FS_TINY, wrap=False))
            rl.addStretch()
            roll_btn = _btn("", TEAL, variant="ghost", width=26, height=22, radius=5,
                            font_size=FS_SMALL, tooltip=f"Roll a {AB_FULL[ab]} save")
            _icons.set_button_icon(roll_btn, "dice", 14)
            roll_btn.clicked.connect(lambda checked=False, a=ab:
                                     self._quick_roll_toast(f"{AB_FULL[a]} save",
                                                            all_saving_throw_bonuses(self.char).get(a, 0), "save", a))
            rl.addWidget(roll_btn)
            if is_class:
                save_word.setToolTip(f"{AB_FULL[ab]} save proficiency comes from your class")
            else:
                for wdg in (save_word, val_lbl):
                    wdg.setCursor(Qt.PointingHandCursor)
                    wdg.setToolTip(f"Click to toggle {AB_FULL[ab]} save proficiency")
                    wdg.mousePressEvent = lambda e, a=ab: self._toggle_save_prof(a)
                dot.toggled.connect(lambda checked, a=ab: self._toggle_save_prof(a, checked))
            self._save_widgets[ab] = (dot, val_lbl)
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
    def _toggle_save_prof(self, ability, checked=None):
        """Toggle a manually-granted saving throw proficiency (e.g. from a
        feat). char['saving_throws'] itself is a fully DERIVED field —
        builder.rebuild() overwrites it from scratch every call based on
        class grants plus this list — so writing to saving_throws directly
        would just get stomped on the next rebuild. _choices.extra_save_profs
        is the actual persistent source or truth for a manual addition;
        class-granted proficiencies aren't stored here at all, so this can't
        accidentally remove a real class feature."""
        choices = self.char.setdefault("_choices", {})
        current = list(choices.get("extra_save_profs", []))
        is_extra = ability in current
        new_state = (not is_extra) if checked is None else checked
        if new_state and ability not in current:
            current.append(ability)
        elif not new_state and ability in current:
            current.remove(ability)
        self.ctrl.update("_choices.extra_save_profs", current)

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
        # Saves
        saves = all_saving_throw_bonuses(self.char)
        profs = get_saving_throw_profs(class_levels(self.char))
        for ab, (dot, val_lbl) in self._save_widgets.items():
            val = saves.get(ab,0)
            color = TEAL2 if val>0 else (CRIM2 if val<0 else TEXT2)
            val_lbl.setText(sign(val))
            self._update_save_advantage_badge(ab)
            self._update_save_condition_badge(ab)
            val_lbl.setStyleSheet(f"color:{color};font-size:{FS_LABEL}px;font-weight:700;background:transparent;border:none;")
            is_p = ab in profs or self.char.get("saving_throws",{}).get(ab,False)
            dot.setChecked(is_p)

        self._refresh_senses()
