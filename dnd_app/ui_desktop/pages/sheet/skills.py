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


class SkillsMixin:
    def _lay_out_skills(self, cols: int):
        """The skill rows in one column, or two side by side (read down the
        first, then the second) when the window has room for both."""
        if cols == getattr(self, "_skill_cols", 0) or not getattr(self, "_skill_row_order", None):
            return
        self._skill_cols = cols
        grid, order = self._skill_grid, self._skill_row_order
        for f in order:
            grid.removeWidget(f)
        per = -(-len(order) // cols)
        for i, f in enumerate(order):
            grid.addWidget(f, i % per, i // per)
        for c in range(2):
            grid.setColumnStretch(c, 1 if c < cols else 0)
        for r in range(per):
            grid.setRowStretch(r, 1)   # the rows share the card's height

    def _build_skills_card(self):
        """The Overview's Skills card: the eighteen in two columns of nine,
        each with its proficiency mark (right-click to set it), bonus, and
        the dice that roll it."""
        sk_card = _card()
        skcl = QVBoxLayout(sk_card); skcl.setContentsMargins(16,14,16,16); skcl.setSpacing(6)
        skcl.addWidget(_lbl("SKILLS", GOLD, FS_SMALL, bold=True))

        # Legend
        leg = QHBoxLayout(); leg.setSpacing(12)
        for sym, label, color in [("—","None",TEXT3),("◆","Proficient",INDIGO),("◈","Expertise",PURP2),("½","Half",IND2)]:
            lrow = QHBoxLayout(); lrow.setSpacing(4)
            lrow.addWidget(_lbl(sym, color, FS_BODY, bold=True, wrap=False))
            lrow.addWidget(_lbl(label, color, FS_SMALL, wrap=False))
            leg.addLayout(lrow)
        leg.addStretch()
        # (on the legend's row: it had a row of its own under it)
        reset_skills_btn = QPushButton("↺ Reset")
        reset_skills_btn.setToolTip(
            "Reset manual changes: clears every skill proficiency and rebuilds them from scratch "
            "using only your actual grants (class, background, race, feat choices) — undoes any "
            "manual clicks that don't correspond to a real source.")
        reset_skills_btn.setAccessibleName("Reset manual skill changes")
        reset_skills_btn.setStyleSheet(
            _btn("", CRIMSON, variant="danger", bg_alpha=0x22, border_width=1,
                 text_color=CRIM2, hover_text="white", font_size=FS_SMALL,
                 padding="3px 12px").styleSheet())
        reset_skills_btn.clicked.connect(self._reset_manual_skill_changes)
        leg.addWidget(reset_skills_btn)
        skcl.addLayout(leg)
        if has_reliable_talent(self.char):
            skcl.addWidget(_lbl("✦ Reliable Talent: a roll of 9 or lower counts as 10 on a proficient check",
                                AMBE2, FS_SMALL, bold=True))
        skcl.addWidget(_sep())
        self._skill_grid = QGridLayout(); self._skill_grid.setHorizontalSpacing(8); self._skill_grid.setVerticalSpacing(5)
        self._skill_grid.setContentsMargins(0, 0, 0, 0)
        self._skill_row_order = []
        self._skill_cols = 0

        from dnd_app.core.calculator import has_jack_of_all_trades
        _jack = has_jack_of_all_trades(self.char)
        skills = all_skill_bonuses(self.char)
        self._skill_rows = {}
        for skill_name, bonus in sorted(skills.items()):
            from dnd_app.core.calculator import skill_prof_level
            prof_level = skill_prof_level(self.char, skill_name)
            ab = SKILL_AB.get(skill_name,"STR")
            # Show ½ symbol for JoAT on non-proficient skills
            _disp_level = prof_level if prof_level > 0 else (1 if _jack else 0)
            sym = {0:"—",1:"½",2:"◆",3:"◈"}.get(_disp_level,"—")
            sym_color = {0:TEXT3,1:IND2,2:INDIGO,3:PURP2}.get(_disp_level,TEXT3)
            val_color = TEAL2 if bonus>0 else (CRIM2 if bonus<0 else TEXT2)

            row_f = QFrame()
            row_f.setStyleSheet(f"QFrame{{background:{SURF2 if prof_level>0 else SURF};border:1px solid {BORDER if prof_level==0 else BORDER2};border-radius:7px;}}")
            rl = QHBoxLayout(row_f); rl.setContentsMargins(10,2,8,2); rl.setSpacing(8)

            sym_l = _lbl(sym, sym_color, FS_BODY, bold=True, wrap=False, align=Qt.AlignCenter)
            sym_l.setFixedWidth(20)
            val_l = _lbl(sign(bonus), val_color, FS_LABEL, bold=True, wrap=False, align=Qt.AlignRight)
            val_l.setFixedWidth(40)
            name_l = _lbl(skill_name, TEXT if prof_level>0 else TEXT2, FS_BODY, wrap=False)
            ab_l = _lbl(f"({ab})", TEXT3, FS_TINY, wrap=False)

            # Advantage/disadvantage badge — populated by _refresh_skills
            adv_badge = _lbl("", TEXT3, FS_TINY, bold=True, wrap=False, align=Qt.AlignCenter)
            adv_badge.setVisible(False)

            # Right-click for an explicit menu of proficiency levels —
            # deliberately not a blind cycle-on-every-click. Cycling with no
            # visible options meant overshooting past the level you wanted
            # was easy, and there was no visibility into what state you'd
            # land on next; a menu makes the change deliberate and visible.
            row_f.mousePressEvent = (lambda e, sk=skill_name, rf=row_f:
                self._show_skill_prof_menu(sk, e.globalPos()) if e.button() == Qt.RightButton else None)
            row_f.setCursor(Qt.PointingHandCursor)
            row_f.setToolTip(f"Right-click to set proficiency level  •  the dice button rolls the check")

            # Dice roll button — rolls d20 + skill bonus without touching proficiency
            roll_btn = _btn("", TEAL, variant="ghost", width=26, height=24, radius=5,
                             font_size=FS_SMALL, tooltip=f"Roll {skill_name} ({sign(bonus)})")
            _icons.set_button_icon(roll_btn, "dice", 14)
            roll_btn.clicked.connect(
                lambda checked=False, sk=skill_name, b=bonus:
                    self._quick_roll_toast(f"{sk} check", b, "check"))

            rl.addWidget(sym_l); rl.addWidget(val_l); rl.addWidget(name_l, 1)
            rl.addWidget(adv_badge); rl.addWidget(ab_l); rl.addWidget(roll_btn)
            self._skill_row_order.append(row_f)
            self._skill_rows[skill_name] = (row_f, sym_l, val_l, name_l, adv_badge)

        skcl.addLayout(self._skill_grid, 1)
        self._lay_out_skills(2)
        return sk_card

    def _build_proficiencies_card(self):
        """The Overview's Proficiencies card: languages, armour, weapons and
        tools a line each (as tall as they need), and the DM's own."""
        card = _card()
        cl = QVBoxLayout(card); cl.setContentsMargins(16, 14, 16, 14); cl.setSpacing(0)
        cl.addWidget(_lbl("PROFICIENCIES", GOLD, FS_SMALL, bold=True))
        cl.addSpacing(6)
        grid = QGridLayout(); grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12); grid.setVerticalSpacing(0)
        grid.setColumnStretch(1, 1)
        made = {}
        for i, (label, color) in enumerate((("Languages", TEAL2), ("Armor", GOLD2),
                                            ("Weapons", IND2), ("Tools", AMBE2))):
            line = QFrame(); line.setFixedHeight(1)
            line.setStyleSheet(f"background:{BORDER};border:none;")
            grid.addWidget(line, i * 2, 0, 1, 2)
            name = _lbl(label, color, FS_SMALL, bold=True, wrap=False)
            name.setFixedWidth(92)
            name.setContentsMargins(0, 6, 0, 6)
            val = _lbl("", TEXT, FS_SMALL, wrap=True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(name, i * 2 + 1, 0, Qt.AlignTop)
            grid.addWidget(val, i * 2 + 1, 1)
            grid.setRowMinimumHeight(i * 2 + 1, 28)
            made[label] = val
        for w in made.values():
            w.setContentsMargins(0, 6, 0, 6)
        cl.addLayout(grid)
        self._lang_lbl, self._armor_prof_lbl = made["Languages"], made["Armor"]
        self._wpn_prof_lbl, self._tool_prof_lbl = made["Weapons"], made["Tools"]
        cl.addSpacing(8)
        # anything the DM grants outside the rules (core/dm_proficiencies.py)
        dm_btn = _btn("DM-granted proficiencies…", GOLD, variant="neutral", height=32,
                      tooltip="Add or remove weapons, armour, tools and languages your DM gave you")
        dm_btn.setObjectName("dmProficienciesBtn")
        dm_btn.clicked.connect(self._open_dm_proficiencies)
        cl.addWidget(dm_btn)
        return card

    def _open_dm_proficiencies(self):
        from dnd_app.ui_desktop.dialogs.dm_proficiencies import DmProficienciesDialog
        def changed():
            # rebuild adds them to the lists; every tab redraws
            self.ctrl.refresh()
            self._mark_dirty()
        DmProficienciesDialog(self.char, changed, self).exec()

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
        # the player's own setting, kept as an override on top of what's
        # granted (core/builder.py), so a rebuild doesn't undo it
        from dnd_app.core.builder import set_skill_level
        set_skill_level(self.char, skill_name, level)
        self.ctrl.refresh()
        self._mark_dirty()

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
        from dnd_app.core.builder import reset_skill_levels
        reset_skill_levels(self.char)
        self.ctrl.refresh()
        self._mark_dirty()
        self._refresh_skills()
        self._toast("↺ Skill proficiencies reset to granted baseline")

    def _refresh_skills(self):
        from dnd_app.core.calculator import get_skill_advantage_status, has_jack_of_all_trades
        skills = all_skill_bonuses(self.char)
        _jack = has_jack_of_all_trades(self.char)
        for sk, (row_f, sym_l, val_l, name_l, adv_badge) in self._skill_rows.items():
            from dnd_app.core.calculator import skill_prof_level
            prof = skill_prof_level(self.char, sk)
            bonus = skills.get(sk,0)
            # Same display rule as the initial build: JoAT shows ½ on any
            # skill that isn't already proficient/expert.
            _disp = prof if prof > 0 else (1 if _jack else 0)
            sym = {0:"—",1:"½",2:"◆",3:"◈"}.get(_disp,"—")
            sym_color = {0:TEXT3,1:IND2,2:INDIGO,3:PURP2}.get(_disp,TEXT3)
            val_color = TEAL2 if bonus>0 else (CRIM2 if bonus<0 else TEXT2)
            sym_l.setText(sym); sym_l.setStyleSheet(f"color:{sym_color};font-size:{FS_BODY}px;font-weight:700;background:transparent;border:none;")
            val_l.setText(sign(bonus)); val_l.setStyleSheet(f"color:{val_color};font-size:{FS_LABEL}px;font-weight:700;background:transparent;border:none;")
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
        _order = {"light armor": 0, "medium armor": 1, "heavy armor": 2, "shields": 3}
        self._armor_prof_lbl.setText(", ".join(sorted(set(self.char.get("armor_proficiencies", [])) - {"None"},
                                                      key=lambda a: (_order.get(a.lower(), 4), a))) or "None")
        self._wpn_prof_lbl.setText(", ".join(sorted(set(self.char.get("weapon_proficiencies", [])) - {"None"})) or "None")
        from dnd_app.core.calculator import known_languages
        self._lang_lbl.setText(", ".join(known_languages(self.char) or ["Common"]))
        self._refresh_tool_prof_chips()

    def _refresh_tool_prof_chips(self):
        """The Tools line: every tool, and what each is for on hover (the
        XGE tool descriptions)."""
        lbl = getattr(self, "_tool_prof_lbl", None)
        if lbl is None:
            return
        import html
        tools = sorted(set(self.char.get("tool_proficiencies", [])))
        if not tools:
            lbl.setTextFormat(Qt.PlainText); lbl.setText("None")
            return
        # each tool its own hover target: a link, drawn as plain text, whose
        # hover shows that tool's details (_tool_hovered)
        lbl.setTextFormat(Qt.RichText)
        lbl.setText(", ".join(
            f'<a href="{html.escape(t, quote=True)}" style="color:{TEXT};text-decoration:none">{html.escape(t)}</a>'
            for t in tools))
        if not getattr(lbl, "_hover_wired", False):
            lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
            lbl.linkHovered.connect(self._tool_hovered)
            lbl._hover_wired = True

    def _tool_hovered(self, tool: str):
        """A tool's details on hover (the XGE tool descriptions)."""
        from PySide6.QtWidgets import QToolTip
        from PySide6.QtGui import QCursor
        if not tool:
            QToolTip.hideText()
            return
        from dnd_app.data.feature_tooltips import get_tool_tooltip
        QToolTip.showText(QCursor.pos(), f"<b>{tool}</b><br>{get_tool_tooltip(tool) or 'No details for this tool.'}",
                          self._tool_prof_lbl)
