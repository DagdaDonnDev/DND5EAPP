"""Floating dice roller panel.

Author: Ethan O'Brien
Date: 2026-08-20
"""
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from dnd_app.ui.style.theme import *
from ..shared import h as _h, card as _card


def sign(n): return f"+{n}" if n >= 0 else str(n)

def lbl(text, color=None, bold=False, size=None, align=Qt.AlignLeft):
    # Not a direct alias to shared.py's h(): h() defaults wrap=True and
    # calls setWordWrap(True), but this file's labels never had word-
    # wrap enabled (no such param existed here) — a straight alias would
    # silently start wrapping "Pick a die below to get started." inside
    # a panel never laid out to expect that. Delegates with wrap=False
    # to keep the original (never-wraps) behavior exactly.
    return _h(text, color or TEXT, size or FS_TINY, bold, align, wrap=False)

# card() is shared.py's promoted version of this exact shape (background
# SURF, 1px BORDER, radius 10) — this file's own _card() took no accent
# param and always used BORDER, matching card()'s own default exactly.

def _section_header(text: str) -> QLabel:
    return lbl(text, TEAL2, bold=True, size=FS_TINY)


class DiceRollerPanel(QWidget):
    """Floating dice roller. Roll dice with optional modifier and bonus."""

    def __init__(self, char_ref: dict, parent=None):
        super().__init__(parent, Qt.Window | Qt.Tool | Qt.WindowStaysOnTopHint)
        # `from .theme import *` above only captured whatever the theme
        # was when this module was first imported -- a persistent
        # floating window like this one is exactly the case where that
        # staleness is most visible, since it can outlive several later
        # theme switches. main_window.py's _set_theme() destroys and
        # recreates this panel (preserving position/visibility) on every
        # theme change specifically so this line picks up fresh colors
        # each time, rather than trying to re-style already-built child
        # widgets in place.
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
        self.char = char_ref
        self.setWindowTitle("Dice Roller")
        self.setFixedWidth(380)
        self.setStyleSheet(f"""
            QWidget {{ background: {BG}; color: {TEXT}; font-size: {FS_TINY}px; font-family: 'Segoe UI', sans-serif; }}
            QPushButton {{ background: {SURF3}; border: 1px solid {BORDER2}; border-radius: 6px; color: {TEXT}; padding: 4px 8px; font-weight: 700; }}
            QPushButton:hover {{ background: {INDIGO}; border-color: {IND2}; color: white; }}
            QPushButton:pressed {{ background: {qa(INDIGO,0xaa)}; }}
            QSpinBox {{ background: {SURF2}; border: 1px solid {BORDER}; border-radius: 5px; color: {TEXT}; padding: 3px 6px; }}
            QComboBox {{ background: {SURF2}; border: 1px solid {BORDER}; border-radius: 5px; color: {TEXT}; padding: 3px 6px; }}
            QComboBox::drop-down {{ border: none; width: 18px; background: {BORDER}; border-radius: 0 5px 5px 0; }}
            QComboBox QAbstractItemView {{ background: {SURF2}; border: 1px solid {BORDER2}; color: {TEXT}; selection-background-color: {INDIGO}; }}
        """)
        self._history = []   # [{"text": str, "crit": "nat20"|"nat1"|None}]
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(12,12,12,12); outer.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.addWidget(lbl("\U0001f3b2  DICE ROLLER", GOLD2, bold=True, size=FS_LABEL))
        title_row.addStretch()
        outer.addLayout(title_row)

        # ── Result display ────────────────────────────────────────────────────
        # Placed above the roll controls since the result is the whole
        # point of this panel.
        self.result_frame = QFrame()
        self.result_frame.setMinimumHeight(96)
        self.result_frame.setStyleSheet(
            f"QFrame{{background:{SURF};border:2px solid {BORDER2};border-radius:10px;}}")
        rf_lay = QVBoxLayout(self.result_frame); rf_lay.setContentsMargins(10,10,10,8); rf_lay.setSpacing(2)

        self.crit_badge = lbl("", "white", bold=True, size=FS_TINY, align=Qt.AlignCenter)
        self.crit_badge.setFixedHeight(20)
        self.crit_badge.hide()
        rf_lay.addWidget(self.crit_badge)

        self.result_main = QLabel("—")
        f = QFont(); f.setBold(True); f.setPointSize(36)
        self.result_main.setFont(f)
        self.result_main.setAlignment(Qt.AlignCenter)
        self.result_main.setStyleSheet(f"color:{GOLD2};")
        rf_lay.addWidget(self.result_main)

        self.result_detail = lbl("Pick a die below to get started.", TEXT2, size=FS_TINY, align=Qt.AlignCenter)
        self.result_detail.setWordWrap(True)
        rf_lay.addWidget(self.result_detail)
        outer.addWidget(self.result_frame)

        # ── Quick dice buttons ────────────────────────────────────────────────
        quick_card = _card()
        qg = QVBoxLayout(quick_card); qg.setContentsMargins(12,10,12,12); qg.setSpacing(8)
        qg.addWidget(_section_header("QUICK ROLL"))
        row1 = QHBoxLayout(); row1.setSpacing(6)
        row2 = QHBoxLayout(); row2.setSpacing(6)
        for die, row in [("d4",row1),("d6",row1),("d8",row1),("d10",row1),("d12",row2),("d20",row2),("d100",row2)]:
            btn = QPushButton(die)
            btn.setFixedHeight(38)
            if die == "d20":
                btn.setStyleSheet(
                    f"QPushButton{{background:{INDIGO};border:1px solid {IND2};border-radius:6px;"
                    f"color:white;font-weight:700;font-size:{FS_SMALL}px;}}"
                    f"QPushButton:hover{{background:{IND2};}}")
            btn.clicked.connect(lambda _, d=die: self._quick_roll(d))
            row.addWidget(btn)
        qg.addLayout(row1); qg.addLayout(row2)
        outer.addWidget(quick_card)

        # ── Custom roll ───────────────────────────────────────────────────────
        custom_card = _card()
        cvl = QVBoxLayout(custom_card); cvl.setContentsMargins(12,10,12,12); cvl.setSpacing(8)
        cvl.addWidget(_section_header("CUSTOM ROLL"))
        cg = QHBoxLayout(); cg.setSpacing(6)
        self.num_dice = QSpinBox(); self.num_dice.setRange(1,20); self.num_dice.setValue(1); self.num_dice.setFixedWidth(52)
        self.die_combo = QComboBox()
        for d in ["d4","d6","d8","d10","d12","d20","d100"]: self.die_combo.addItem(d)
        self.die_combo.setCurrentIndex(5)  # d20 default
        self.mod_spin = QSpinBox(); self.mod_spin.setRange(-20,20); self.mod_spin.setValue(0); self.mod_spin.setPrefix("+"); self.mod_spin.setFixedWidth(62)
        roll_btn = QPushButton("Roll!")
        roll_btn.setFixedHeight(32)
        roll_btn.setStyleSheet(
            f"QPushButton{{background:{INDIGO};border:1px solid {IND2};border-radius:6px;"
            f"color:white;font-weight:700;padding:4px 14px;}}QPushButton:hover{{background:{IND2};}}")
        roll_btn.clicked.connect(self._custom_roll)
        cg.addWidget(self.num_dice); cg.addWidget(lbl("×")); cg.addWidget(self.die_combo)
        cg.addWidget(lbl("+")); cg.addWidget(self.mod_spin); cg.addStretch(); cg.addWidget(roll_btn)
        cvl.addLayout(cg)
        outer.addWidget(custom_card)

        # ── Skill / Save roll ─────────────────────────────────────────────────
        skill_card = _card()
        svl = QVBoxLayout(skill_card); svl.setContentsMargins(12,10,12,12); svl.setSpacing(8)
        svl.addWidget(_section_header("ROLL WITH BONUS"))
        sg_top = QHBoxLayout(); sg_top.setSpacing(6)
        self.bonus_combo = QComboBox(); self.bonus_combo.setMinimumWidth(180)
        self._populate_bonus_combo()
        self.adv_combo = QComboBox()
        self.adv_combo.addItems(["Normal","Advantage","Disadvantage"])
        sg_top.addWidget(self.bonus_combo, 2); sg_top.addWidget(self.adv_combo)
        svl.addLayout(sg_top)
        skill_roll_btn = QPushButton("Roll d20 + Bonus")
        skill_roll_btn.setFixedHeight(32)
        skill_roll_btn.clicked.connect(self._skill_roll)
        svl.addWidget(skill_roll_btn)
        outer.addWidget(skill_card)

        # ── History ───────────────────────────────────────────────────────────
        hist_card = _card()
        hl = QVBoxLayout(hist_card); hl.setContentsMargins(12,10,12,12); hl.setSpacing(6)
        h_top = QHBoxLayout()
        h_top.addWidget(_section_header("HISTORY (LAST 8)"))
        h_top.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(56, 24)
        clear_btn.clicked.connect(self._clear_history)
        h_top.addWidget(clear_btn)
        hl.addLayout(h_top)
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(130)
        self.history_list.setStyleSheet(
            f"QListWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;"
            f"font-size:{FS_TINY}px;color:{TEXT2};}}"
            f"QListWidget::item{{padding:3px 6px;border-radius:3px;}}"
            f"QListWidget::item:selected{{background:{INDIGO};color:white;}}")
        hl.addWidget(self.history_list)
        outer.addWidget(hist_card)

    def _populate_bonus_combo(self):
        self.bonus_combo.clear()
        # Ability checks
        from dnd_app.core.calculator import all_skill_bonuses, all_saving_throw_bonuses
        from dnd_app.core.character import class_levels
        skills = all_skill_bonuses(self.char)
        saves = all_saving_throw_bonuses(self.char)
        self.bonus_combo.addItem("No bonus (raw d20)", 0)
        self.bonus_combo.addItem(f"─── Skills ───", None)
        for skill, bonus in sorted(skills.items()):
            self.bonus_combo.addItem(f"  {skill}: {sign(bonus)}", bonus)
        self.bonus_combo.addItem(f"─── Saving Throws ───", None)
        for ab, bonus in saves.items():
            self.bonus_combo.addItem(f"  {ab} Save: {sign(bonus)}", bonus)
        self.bonus_combo.addItem(f"─── Ability Checks ───", None)
        from dnd_app.core.character import ability_mod
        for ab in ["STR","DEX","CON","INT","WIS","CHA"]:
            mod = ability_mod(self.char, ab)
            self.bonus_combo.addItem(f"  {ab} Check: {sign(mod)}", mod)

    def refresh_bonuses(self):
        idx = self.bonus_combo.currentIndex()
        self._populate_bonus_combo()
        if idx < self.bonus_combo.count():
            self.bonus_combo.setCurrentIndex(idx)

    def _quick_roll(self, die_str: str):
        sides = int(die_str[1:])
        result = random.randint(1, sides)
        # A single quick d20 is exactly a "natural" roll -- give it the
        # same crit treatment as the "Roll with Bonus" button.
        is_d20 = (sides == 20)
        self._show_result(result, f"1{die_str}", [result],
                           nat20=(is_d20 and result == 20), nat1=(is_d20 and result == 1))

    def _custom_roll(self):
        n = self.num_dice.value()
        die_str = self.die_combo.currentText()
        sides = int(die_str[1:])
        mod = self.mod_spin.value()
        rolls = [random.randint(1, sides) for _ in range(n)]
        total = sum(rolls) + mod
        detail = f"{n}{die_str}: [{', '.join(str(r) for r in rolls)}]" + (f" {sign(mod)}" if mod else "")
        # Crit styling only makes sense for a single natural d20 -- with
        # multiple dice "natural 20" isn't a meaningful concept.
        single_d20 = (n == 1 and sides == 20)
        self._show_result(total, detail, rolls, modifier=mod,
                           nat20=(single_d20 and rolls[0] == 20),
                           nat1=(single_d20 and rolls[0] == 1))

    def _skill_roll(self):
        bonus = self.bonus_combo.currentData()
        if bonus is None: return  # separator selected
        label = self.bonus_combo.currentText().strip()
        mode = self.adv_combo.currentText()

        if mode == "Normal":
            roll = random.randint(1,20)
            rolls = [roll]
        elif mode == "Advantage":
            rolls = [random.randint(1,20), random.randint(1,20)]
            roll = max(rolls)
        else:
            rolls = [random.randint(1,20), random.randint(1,20)]
            roll = min(rolls)

        total = roll + bonus
        adv_str = f" (Adv: {rolls})" if len(rolls)>1 else ""
        detail = f"{label}: d20={roll}{adv_str} {sign(bonus)} = {total}"
        self._show_result(total, detail, rolls, modifier=bonus, nat20=(roll==20), nat1=(roll==1))

    def _show_result(self, total, detail, rolls, modifier=0, nat20=False, nat1=False):
        self.result_main.setText(str(total))
        self.result_detail.setText(detail)

        if nat20:
            color, border_color = TEAL2, TEAL2
            self.crit_badge.setText("✨  NATURAL 20")
            self.crit_badge.setStyleSheet(
                f"background:{TEAL};color:white;font-size:{FS_TINY}px;font-weight:700;"
                f"border-radius:4px;padding:2px 8px;")
            self.crit_badge.show()
        elif nat1:
            color, border_color = CRIM2, CRIM2
            self.crit_badge.setText("\U0001f480  NATURAL 1")
            self.crit_badge.setStyleSheet(
                f"background:{CRIMSON};color:white;font-size:{FS_TINY}px;font-weight:700;"
                f"border-radius:4px;padding:2px 8px;")
            self.crit_badge.show()
        else:
            border_color = BORDER2
            self.crit_badge.hide()
            if total >= 20:
                color = GOLD2
            elif total <= 5:
                color = TEXT2
            else:
                color = TEXT

        self.result_main.setStyleSheet(f"color:{color};")

        # Flash animation, settling to a crit-colored border afterward
        # (rather than always reverting to the plain default) so a nat
        # 20/1 stays visually obvious at a glance even after the flash
        # fades.
        self.result_frame.setStyleSheet(
            f"QFrame{{background:{qa(INDIGO,0x44)};border:2px solid {INDIGO};border-radius:10px;}}")
        QTimer.singleShot(200, lambda bc=border_color: self.result_frame.setStyleSheet(
            f"QFrame{{background:{SURF};border:2px solid {bc};border-radius:10px;}}"
        ))

        # Add to history
        crit = "nat20" if nat20 else ("nat1" if nat1 else None)
        self._history.insert(0, {"text": f"{total:>3d}  {detail[:55]}", "crit": crit})
        self._history = self._history[:8]
        self.history_list.clear()
        for entry in self._history:
            item = QListWidgetItem(entry["text"])
            if entry["crit"] == "nat20":
                item.setForeground(QColor(TEAL2))
            elif entry["crit"] == "nat1":
                item.setForeground(QColor(CRIM2))
            self.history_list.addItem(item)

    def _clear_history(self):
        self._history.clear()
        self.history_list.clear()
        self.result_main.setText("—")
        self.result_detail.setText("Pick a die below to get started.")
        self.crit_badge.hide()
        self.result_frame.setStyleSheet(
            f"QFrame{{background:{SURF};border:2px solid {BORDER2};border-radius:10px;}}")
