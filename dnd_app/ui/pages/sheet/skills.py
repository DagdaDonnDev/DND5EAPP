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


class SkillsMixin:
    def _build_tab_skills(self):
        tab = QScrollArea(); tab.setWidgetResizable(True)
        w = QWidget(); tab.setWidget(w)
        root = QHBoxLayout(w); root.setContentsMargins(20,20,20,20); root.setSpacing(16)

        # Left: skills
        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(8)
        sk_card = _card()
        skcl = QVBoxLayout(sk_card); skcl.setContentsMargins(16,14,16,16); skcl.setSpacing(6)
        skcl.addWidget(_lbl("SKILLS", GOLD, FS_SMALL, bold=True))

        # Legend
        leg = QHBoxLayout(); leg.setSpacing(12)
        for sym, label, color in [("—","None",TEXT3),("◆","Proficient",INDIGO),("◈","Expertise",PURP2),("½","Half (Jack of All Trades)",IND2)]:
            lrow = QHBoxLayout(); lrow.setSpacing(4)
            lrow.addWidget(_lbl(sym, color, FS_BODY, bold=True, wrap=False))
            lrow.addWidget(_lbl(label, color, FS_SMALL, wrap=False))
            leg.addLayout(lrow)
        leg.addStretch(); skcl.addLayout(leg)

        reset_row = QHBoxLayout()
        reset_row.addStretch()
        reset_skills_btn = QPushButton("↺ Reset Manual Changes")
        reset_skills_btn.setToolTip(
            "Clears every skill proficiency and rebuilds them from scratch using only your "
            "actual grants (class, background, race, feat choices) — undoes any manual clicks "
            "that don't correspond to a real source.")
        reset_skills_btn.setStyleSheet(
            _btn("", CRIMSON, variant="danger", bg_alpha=0x22, border_width=1,
                 text_color=CRIM2, hover_text="white", font_size=FS_SMALL,
                 padding="5px 12px").styleSheet())
        reset_skills_btn.clicked.connect(self._reset_manual_skill_changes)
        reset_row.addWidget(reset_skills_btn)
        skcl.addLayout(reset_row)
        skcl.addWidget(_sep())

        from dnd_app.core.calculator import has_jack_of_all_trades
        _jack = has_jack_of_all_trades(self.char)
        skills = all_skill_bonuses(self.char)
        self._skill_rows = {}
        for skill_name, bonus in sorted(skills.items()):
            prof_level = self.char.get("skills",{}).get(skill_name, 0)
            ab = SKILL_AB.get(skill_name,"STR")
            # Show ½ symbol for JoAT on non-proficient skills
            _disp_level = prof_level if prof_level > 0 else (1 if _jack else 0)
            sym = {0:"—",1:"½",2:"◆",3:"◈"}.get(_disp_level,"—")
            sym_color = {0:TEXT3,1:IND2,2:INDIGO,3:PURP2}.get(_disp_level,TEXT3)
            val_color = TEAL2 if bonus>0 else (CRIM2 if bonus<0 else TEXT2)

            row_f = QFrame()
            row_f.setStyleSheet(f"QFrame{{background:{SURF2 if prof_level>0 else SURF};border:1px solid {BORDER if prof_level==0 else BORDER2};border-radius:7px;}}")
            rl = QHBoxLayout(row_f); rl.setContentsMargins(10,7,10,7); rl.setSpacing(8)

            sym_l = _lbl(sym, sym_color, FS_BODY, bold=True, wrap=False, align=Qt.AlignCenter)
            sym_l.setFixedWidth(20)
            val_l = _lbl(sign(bonus), val_color, FS_LABEL, bold=True, wrap=False, align=Qt.AlignRight)
            val_l.setFixedWidth(44)
            name_l = _lbl(skill_name, TEXT if prof_level>0 else TEXT2, FS_BODY, wrap=False)
            name_l.setFixedWidth(148)  # fits "Animal Handling"/"Sleight of Hand" (longest names) so the (ABILITY) tags that follow always line up in a column
            ab_l = _lbl(f"({ab})", TEXT3, FS_SMALL, wrap=False)
            ab_l.setFixedWidth(46)  # all ability tags are "(XXX)" — fixed width keeps the roll button/stretch after it aligned consistently row to row

            # Advantage/disadvantage badge — populated by _refresh_skills
            adv_badge = _lbl("", TEXT3, FS_TINY, bold=True, wrap=False, align=Qt.AlignCenter)
            adv_badge.setFixedWidth(64)
            adv_badge.setVisible(False)

            # Right-click for an explicit menu of proficiency levels —
            # deliberately not a blind cycle-on-every-click. Cycling with no
            # visible options meant overshooting past the level you wanted
            # was easy, and there was no visibility into what state you'd
            # land on next; a menu makes the change deliberate and visible.
            row_f.mousePressEvent = (lambda e, sk=skill_name, rf=row_f:
                self._show_skill_prof_menu(sk, e.globalPos()) if e.button() == Qt.RightButton else None)
            row_f.setCursor(Qt.PointingHandCursor)
            row_f.setToolTip(f"Right-click to set proficiency level  •  🎲 button rolls the check")

            # 🎲 roll button — rolls d20 + skill bonus without touching proficiency
            roll_btn = _btn("🎲", TEAL, variant="ghost", width=26, height=24, radius=5,
                             font_size=FS_SMALL, tooltip=f"Roll {skill_name} ({sign(bonus)})")
            roll_btn.clicked.connect(
                lambda checked=False, sk=skill_name, b=bonus:
                    self._quick_roll_toast(f"{sk} check", b))

            rl.addWidget(sym_l); rl.addWidget(val_l); rl.addWidget(name_l); rl.addWidget(ab_l)
            rl.addWidget(roll_btn)
            rl.addStretch(); rl.addWidget(adv_badge)
            skcl.addWidget(row_f)
            self._skill_rows[skill_name] = (row_f, sym_l, val_l, name_l, adv_badge)

        ll.addWidget(sk_card); root.addWidget(left, 3)

        # Right: languages + proficiencies
        right = QWidget(); rl2 = QVBoxLayout(right); rl2.setSpacing(10)

        lang_card = _card(TEAL+"55"); lcl = QVBoxLayout(lang_card); lcl.setContentsMargins(14,12,14,14)
        lcl.addWidget(_lbl("LANGUAGES", TEAL2, FS_SMALL, bold=True))
        self._lang_lbl = _lbl("", TEXT2, FS_BODY, wrap=True)
        lcl.addWidget(self._lang_lbl); rl2.addWidget(lang_card)

        armor_card = _card(GOLD+"55"); acl = QVBoxLayout(armor_card); acl.setContentsMargins(14,12,14,14)
        acl.addWidget(_lbl("ARMOR PROFICIENCIES", GOLD, FS_SMALL, bold=True))
        self._armor_prof_lbl = _lbl("", TEXT2, FS_BODY); acl.addWidget(self._armor_prof_lbl)
        rl2.addWidget(armor_card)

        wpn_card = _card(IND2+"55"); wcl = QVBoxLayout(wpn_card); wcl.setContentsMargins(14,12,14,14)
        wcl.addWidget(_lbl("WEAPON PROFICIENCIES", IND2, FS_SMALL, bold=True))
        self._wpn_prof_lbl = _lbl("", TEXT2, FS_BODY); wcl.addWidget(self._wpn_prof_lbl)
        rl2.addWidget(wpn_card)

        tool_card = _card(AMBE2+"55"); tcl = QVBoxLayout(tool_card); tcl.setContentsMargins(14,12,14,14)
        tcl.addWidget(_lbl("TOOL PROFICIENCIES", AMBE2, FS_SMALL, bold=True))
        # Plain QWidget + QGridLayout, not FlowContainer/FlowLayout —
        # avoids FlowContainer.resizeEvent()'s setMinimumHeight()-inside-
        # a-resize-handler pattern, which can cause an infinite resize
        # loop in Qt with a custom QLayout subclass. A grid wraps at a
        # fixed column count instead of dynamically by pixel width, an
        # acceptable trade-off since tool names are short and this list
        # rarely exceeds a handful of entries.
        self._tool_prof_frame = QWidget(); self._tool_prof_frame.setStyleSheet("QWidget{background:transparent;}")
        self._tool_prof_lay = QGridLayout(self._tool_prof_frame)
        self._tool_prof_lay.setSpacing(4); self._tool_prof_lay.setContentsMargins(0,0,0,0)
        tcl.addWidget(self._tool_prof_frame)
        self._refresh_tool_prof_chips()
        rl2.addWidget(tool_card)
        rl2.addStretch(); root.addWidget(right, 2)
        return tab

    # Armor/shield are now equipped exclusively from the Gear tab
    # (see _toggle_armor_worn / _toggle_shield); Combat tab just displays them.

    def _on_inspiration_toggled(self, on: bool):
        self.ctrl.update("inspiration", on, rebuild_char=False)
        self._mark_dirty()

    def _show_skill_prof_menu(self, skill_name, global_pos):
        from PySide6.QtWidgets import QMenu
        curr = self.char.get("skills", {}).get(skill_name, 0)
        menu = QMenu(self)
        LEVELS = [
            (0, "Not Proficient"),
            (1, "Half Proficient (Jack of All Trades–style)"),
            (2, "Proficient"),
            (3, "Expertise (double proficiency)"),
        ]
        for level, label in LEVELS:
            marker = "\u2713 " if level == curr else "    "
            act = menu.addAction(f"{marker}{label}")
            act.triggered.connect(lambda checked=False, lv=level: self._set_skill_prof(skill_name, lv))
        menu.exec(global_pos)

    def _set_skill_prof(self, skill_name, level):
        self.ctrl.update(f"skills.{skill_name}", level)

    def _reset_manual_skill_changes(self):
        """Clear every skill proficiency and rebuild from scratch, keeping
        only what's actually granted (class/background/race/feat choices).
        char['skills'] is a pure accumulator that rebuild() only ever adds
        to, never clears — so any manual click that isn't backed by a real
        grant has no other way to be undone short of this."""
        from PySide6.QtWidgets import QMessageBox as _QMB
        confirm = _QMB.question(
            self, "Reset Skill Proficiencies",
            "This clears every skill proficiency and rebuilds them from scratch using only your "
            "actual grants (class, background, race, feat choices). Any manual click that isn't "
            "backed by a real grant will be undone. Continue?",
            _QMB.Yes | _QMB.No, _QMB.No)
        if confirm != _QMB.Yes:
            return
        from dnd_app.core.builder import rebuild
        self.char["skills"] = {}
        rebuild(self.char)
        self._mark_dirty()
        self._refresh_skills()
        self._toast("↺ Skill proficiencies reset to granted baseline")

    def _refresh_skills(self):
        from dnd_app.core.calculator import get_skill_advantage_status, has_jack_of_all_trades
        skills = all_skill_bonuses(self.char)
        _jack = has_jack_of_all_trades(self.char)
        for sk, (row_f, sym_l, val_l, name_l, adv_badge) in self._skill_rows.items():
            prof = self.char.get("skills",{}).get(sk,0)
            bonus = skills.get(sk,0)
            # Same display rule as the initial build: JoAT shows ½ on any
            # skill that isn't already proficient/expert.
            _disp = prof if prof > 0 else (1 if _jack else 0)
            sym = {0:"—",1:"½",2:"◆",3:"◈"}.get(_disp,"—")
            sym_color = {0:TEXT3,1:IND2,2:INDIGO,3:PURP2}.get(_disp,TEXT3)
            val_color = TEAL2 if bonus>0 else (CRIM2 if bonus<0 else TEXT2)
            sym_l.setText(sym); sym_l.setStyleSheet(f"color:{sym_color};font-size:{FS_BODY}px;font-weight:700;background:transparent;")
            val_l.setText(sign(bonus)); val_l.setStyleSheet(f"color:{val_color};font-size:{FS_LABEL}px;font-weight:700;background:transparent;")
            row_f.setStyleSheet(f"QFrame{{background:{SURF2 if prof>0 else SURF};border:1px solid {BORDER2 if prof>0 else BORDER};border-radius:7px;}}")

            # Advantage / disadvantage badge, with a tooltip explaining why
            status = get_skill_advantage_status(self.char, sk)
            if status["net"] == "advantage":
                adv_badge.setText("▲ ADV"); badge_color = TEAL2
                reasons = status["adv_reasons"]
                tip = "Advantage on " + sk + " checks (passive score +5)\nFrom: " + ", ".join(reasons)
            elif status["net"] == "disadvantage":
                adv_badge.setText("▼ DISADV"); badge_color = CRIM2
                reasons = status["disadv_reasons"]
                tip = "Disadvantage on " + sk + " checks (passive score \u22125)\nFrom: " + ", ".join(reasons)
            elif status["advantage"] and status["disadvantage"]:
                adv_badge.setText("⇅ NORMAL"); badge_color = TEXT3
                tip = ("Advantage and disadvantage cancel out — roll normally.\n"
                       "Advantage from: " + ", ".join(status["adv_reasons"]) + "\n"
                       "Disadvantage from: " + ", ".join(status["disadv_reasons"]))
            else:
                adv_badge.setText(""); adv_badge.setVisible(False)
                continue

            adv_badge.setVisible(True)
            adv_badge.setStyleSheet(
                f"color:{badge_color};font-size:{FS_TINY}px;font-weight:700;"
                f"background:{qa(badge_color,0x1f)};border:1px solid {qa(badge_color,0x55)};"
                f"border-radius:4px;padding:1px 4px;"
            )
            adv_badge.setToolTip(tip)
            row_f.setToolTip(tip)

        # Proficiency lists — use the actual, already-correct derived
        # fields (which include class, subclass, race, background, and
        # feat grants) rather than rebuilding a partial, class-only
        # version here that silently ignored every other source.
        self._armor_prof_lbl.setText("; ".join(sorted(set(self.char.get("armor_proficiencies", [])) - {"None"})) or "None")
        self._wpn_prof_lbl.setText("; ".join(sorted(set(self.char.get("weapon_proficiencies", [])) - {"None"})) or "None")
        self._lang_lbl.setText(", ".join(sorted(set(self.char.get("languages", ["Common"])))) or "None")
        self._refresh_tool_prof_chips()

    def _refresh_tool_prof_chips(self):
        """Individual tool-proficiency chips, each with a full hover
        tooltip from the XGE tool descriptions — replaces the old plain
        comma-separated text blob, which couldn't show per-tool detail.
        Uses a plain QGridLayout (not FlowLayout) — see the setup comment
        in _build_tab_skills for why."""
        while self._tool_prof_lay.count():
            item = self._tool_prof_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)
        from dnd_app.data.phbCommon.feature_tooltips import get_tool_tooltip
        def _tool_badge(text, color, tooltip):
            b = _lbl(text, color, FS_SMALL, bold=True, wrap=False)
            b.setStyleSheet(
                f"background:{qa(color,0x33)};border:1.5px solid {qa(color,0x99)};"
                f"border-radius:5px;padding:3px 8px;color:{color};"
                f"font-size:{FS_SMALL}px;font-weight:700;"
            )
            b.setToolTip(tooltip)
            return b
        tools = self.char.get("tool_proficiencies", [])
        if not tools:
            self._tool_prof_lay.addWidget(_tool_badge("None", TEXT3, ""), 0, 0)
            return
        cols = 4
        for i, tool in enumerate(sorted(set(tools))):
            tip = get_tool_tooltip(tool)
            self._tool_prof_lay.addWidget(_tool_badge(tool, AMBE2, tip), i // cols, i % cols)

