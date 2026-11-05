"""Floating dice roller panel: a dice tray (pick dice, add your bonus,
advantage or disadvantage on a d20, roll) and the roll history -- every
roll the sheet makes (checks, saves, attacks, hit dice, what actions
roll) and the tray's own, kept with the character (core/roll_log.py).
The rolling is core/dice.py's, the same as Android's Dice Roller.

Author: Ethan O'Brien
Date: 2026-08-20
"""
import html
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui_desktop.style.theme import *
from ..shared import h as _h, card as _card
from dnd_app.ui_desktop import icons as _icons
from dnd_app.core import dice as _dice
from dnd_app.core import roll_log as _log

DICE = (4, 6, 8, 10, 12, 20, 100)
MODES = (("normal", "Normal"), ("advantage", "Advantage"), ("disadvantage", "Disadvantage"))
SHOWN = 60          # history rows shown (the character keeps more)


def sign(n): return f"+{n}" if n >= 0 else str(n)


def lbl(text, color=None, bold=False, size=None, align=Qt.AlignLeft, wrap=False):
    return _h(text, color or TEXT, size or FS_TINY, bold, align, wrap=wrap)


def _big(color) -> str:
    # (its own font size: the panel's QWidget rule would make it the small one)
    return f"color:{color};border:none;background:transparent;font-size:44px;font-weight:700;"


def _small_btn() -> str:
    return (f"QPushButton{{background:transparent;border:1px solid {BORDER2};border-radius:6px;color:{TEXT2};"
            f"padding:2px 10px;min-height:0px;font-weight:700;}}"
            f"QPushButton:hover{{background:{SURF3};color:{TEXT};}}"
            f"QPushButton:disabled{{color:{TEXT3};border-color:{BORDER};}}")


def _section_header(text: str) -> QLabel:
    return lbl(text, TEAL2, bold=True, size=FS_TINY)


class DiceRollerPanel(QWidget):
    """Floating dice roller: the tray and the history."""

    def __init__(self, char_ref: dict, parent=None):
        super().__init__(parent, Qt.Window | Qt.Tool | Qt.WindowStaysOnTopHint)
        # `from .theme import *` above only captured whatever the theme
        # was when this module was first imported -- main_window.py's
        # _set_theme() destroys and recreates this panel on every theme
        # change, so this line picks up fresh colours each time.
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self._char = char_ref
        self._mode = "normal"
        self._fresh = False          # the next die starts a new roll (after a roll)
        self.setWindowTitle("Dice Roller")
        self.setFixedWidth(400)
        self.setStyleSheet(f"""
            QWidget {{ background: {BG}; color: {TEXT}; font-size: {FS_TINY}px; font-family: 'Segoe UI', sans-serif; }}
            QPushButton {{ background: {SURF3}; border: 1px solid {BORDER2}; border-radius: 6px; color: {TEXT}; padding: 4px 8px; font-weight: 700; }}
            QPushButton:hover {{ background: {INDIGO}; border-color: {IND2}; color: {on_fill(INDIGO)}; }}
            QPushButton:pressed {{ background: {qa(INDIGO,0xaa)}; }}
            QLineEdit {{ background: {SURF2}; border: 2px solid {BORDER2}; border-radius: 8px; color: {TEXT};
                         padding: 4px 8px; font-size: {FS_BODY}px; font-weight: 700; }}
            QLineEdit:focus {{ border-color: {INDIGO}; }}
            QComboBox {{ background: {SURF2}; border: 1px solid {BORDER}; border-radius: 5px; color: {TEXT}; padding: 3px 6px; }}
            QComboBox::drop-down {{ border: none; width: 18px; background: {BORDER}; border-top-left-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px; border-bottom-left-radius: 0px; }}
            QComboBox QAbstractItemView {{ background: {SURF2}; border: 1px solid {BORDER2}; color: {TEXT}; selection-background-color: {INDIGO}; }}
        """)
        self._build_ui()
        # the sheet's rolls land in the history as they're made
        self._stop_listening = _log.on_roll(self._on_logged)
        self.destroyed.connect(lambda *_: self._stop_listening())
        self._refresh_history()

    # the character whose rolls these are (main_window sets it as sheets open)
    @property
    def char(self):
        return self._char

    @char.setter
    def char(self, value):
        self._char = value
        if hasattr(self, "history_box"):
            self.refresh_bonuses()
            self._refresh_history()

    def set_char(self, value):
        self.char = value

    def _build_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(12, 12, 12, 12); outer.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.addWidget(_icons.icon_header("dice", lbl("DICE ROLLER", GOLD2, bold=True, size=FS_LABEL), size=18))
        title_row.addStretch()
        outer.addLayout(title_row)

        # ── The result ────────────────────────────────────────────────
        self.result_frame = QFrame()
        self.result_frame.setMinimumHeight(96)
        self.result_frame.setStyleSheet(
            f"QFrame{{background:{SURF};border:2px solid {BORDER2};border-radius:10px;}}")
        rf_lay = QVBoxLayout(self.result_frame); rf_lay.setContentsMargins(10, 10, 10, 8); rf_lay.setSpacing(2)
        self.crit_badge = lbl("", on_fill(TEAL), bold=True, size=FS_TINY, align=Qt.AlignCenter)
        self.crit_badge.setFixedHeight(20)
        self.crit_badge.hide()
        rf_lay.addWidget(self.crit_badge)
        self.result_main = QLabel("—")
        f = QFont(); f.setBold(True); f.setPointSize(36)
        self.result_main.setFont(f)
        self.result_main.setAlignment(Qt.AlignCenter)
        self.result_main.setStyleSheet(_big(GOLD2))
        rf_lay.addWidget(self.result_main)
        self.result_detail = lbl("Pick dice below, then Roll.", TEXT2, size=FS_TINY, align=Qt.AlignCenter, wrap=True)
        rf_lay.addWidget(self.result_detail)
        outer.addWidget(self.result_frame)

        # ── The tray ──────────────────────────────────────────────────
        tray = _card()
        tl = QVBoxLayout(tray); tl.setContentsMargins(12, 10, 12, 12); tl.setSpacing(8)
        tl.addWidget(_section_header("ROLL"))
        dice_row = QHBoxLayout(); dice_row.setSpacing(5)
        self._die_btns = {}
        for sides in DICE:
            b = QPushButton(f"d{sides}"); b.setFixedHeight(36)
            b.setToolTip(f"Add a d{sides}")
            if sides == 20:
                b.setStyleSheet(
                    f"QPushButton{{background:{INDIGO};border:1px solid {IND2};border-radius:6px;"
                    f"color:{on_fill(INDIGO)};font-weight:700;font-size:{FS_SMALL}px;}}"
                    f"QPushButton:hover{{background:{IND2};color:{on_fill(IND2)};}}")
            b.clicked.connect(lambda _=False, s=sides: self._add_die(s))
            dice_row.addWidget(b)
            self._die_btns[sides] = b
        tl.addLayout(dice_row)
        er = QHBoxLayout(); er.setSpacing(6)
        self.expr_edit = QLineEdit()
        self.expr_edit.setPlaceholderText("e.g. 2d6 + 3")
        self.expr_edit.setAccessibleName("Dice to roll")
        self.expr_edit.setToolTip("The dice to roll: pick them above, or type them (2d6 + 1d4 + 3, 4d6kh3...)")
        self.expr_edit.textEdited.connect(lambda *_: setattr(self, "_fresh", False))
        self.expr_edit.returnPressed.connect(self._roll)
        er.addWidget(self.expr_edit, 1)
        clear_btn = QPushButton("Clear"); clear_btn.setFixedHeight(34)
        clear_btn.clicked.connect(self._clear_tray)
        er.addWidget(clear_btn)
        tl.addLayout(er)
        br = QHBoxLayout(); br.setSpacing(6)
        br.addWidget(lbl("Your bonus", TEXT2, size=FS_TINY))
        self.bonus_combo = QComboBox(); self.bonus_combo.setMinimumWidth(200)
        self.bonus_combo.setToolTip("Adds one of your bonuses to the roll (a d20 if there are no dice yet)")
        self.refresh_bonuses()
        self.bonus_combo.activated.connect(self._bonus_picked)
        br.addWidget(self.bonus_combo, 1)
        tl.addLayout(br)
        mr = QHBoxLayout(); mr.setSpacing(0)
        self._mode_btns = {}
        for i, (key, text) in enumerate(MODES):
            b = QPushButton(text); b.setCheckable(True); b.setFixedHeight(30)
            left, right = (6, 0) if i == 0 else (0, 6) if i == len(MODES) - 1 else (0, 0)
            b.setStyleSheet(
                f"QPushButton{{background:{SURF};color:{TEXT2};border:1px solid {BORDER2};"
                f"border-top-left-radius:{left}px;border-bottom-left-radius:{left}px;"
                f"border-top-right-radius:{right}px;border-bottom-right-radius:{right}px;font-weight:700;}}"
                f"QPushButton:checked{{background:{qa(GOLD,0x33)};color:{GOLD2};border-color:{GOLD};}}"
                f"QPushButton:hover:!checked{{background:{SURF3};color:{TEXT};}}")
            b.setToolTip("Two d20s, the higher one" if key == "advantage" else
                         "Two d20s, the lower one" if key == "disadvantage" else "One d20")
            b.clicked.connect(lambda _=False, k=key: self._set_mode(k))
            mr.addWidget(b, 1)
            self._mode_btns[key] = b
        self._set_mode("normal")
        tl.addLayout(mr)
        self._mode_note = lbl("Advantage and disadvantage are for a single d20.", TEXT3, size=FS_TINY, wrap=True)
        tl.addWidget(self._mode_note)
        self.roll_btn = QPushButton("Roll")
        self.roll_btn.setFixedHeight(36)
        self.roll_btn.setStyleSheet(
            f"QPushButton{{background:{GOLD};border:1px solid {GOLD2};border-radius:8px;"
            f"color:{on_fill(GOLD)};font-weight:700;font-size:{FS_SMALL}px;}}"
            f"QPushButton:hover{{background:{GOLD2};color:{on_fill(GOLD2)};}}")
        self.roll_btn.clicked.connect(self._roll)
        tl.addWidget(self.roll_btn)
        outer.addWidget(tray)

        # ── The history ───────────────────────────────────────────────
        hist = _card()
        hl = QVBoxLayout(hist); hl.setContentsMargins(12, 10, 12, 12); hl.setSpacing(6)
        h_top = QHBoxLayout()
        self.history_title = _section_header("HISTORY")
        h_top.addWidget(self.history_title)
        h_top.addStretch()
        self.clear_hist_btn = QPushButton("Clear")
        self.clear_hist_btn.setStyleSheet(_small_btn())
        self.clear_hist_btn.setFixedHeight(24)
        self.clear_hist_btn.setToolTip("Clear this character's roll history")
        self.clear_hist_btn.clicked.connect(self._clear_history)
        h_top.addWidget(self.clear_hist_btn)
        hl.addLayout(h_top)
        self.history_scroll = QScrollArea(); self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.NoFrame)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_scroll.setFixedHeight(250)
        self.history_scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:6px;}}")
        self.history_box = QWidget(); self.history_box.setStyleSheet(f"background:{BG};")
        self.history_lay = QVBoxLayout(self.history_box)
        self.history_lay.setContentsMargins(6, 6, 6, 6); self.history_lay.setSpacing(4)
        self.history_scroll.setWidget(self.history_box)
        hl.addWidget(self.history_scroll)
        outer.addWidget(hist)

    # ── Your bonus ────────────────────────────────────────────────────
    def refresh_bonuses(self):
        """The skills, saves and ability checks to add, as they are now."""
        keep = self.bonus_combo.currentIndex() if self.bonus_combo.count() else 0
        self.bonus_combo.clear()
        self.bonus_combo.addItem("No bonus", None)
        char = self._char or {}
        if char.get("abilities"):
            from dnd_app.core.calculator import all_skill_bonuses, all_saving_throw_bonuses
            from dnd_app.core.character import ability_mod
            try:
                skills = all_skill_bonuses(char)
                saves = all_saving_throw_bonuses(char)
            except Exception:
                skills, saves = {}, {}
            for skill, bonus in sorted(skills.items()):
                self.bonus_combo.addItem(f"{skill} {sign(bonus)}", (skill, bonus))
            for ab, bonus in saves.items():
                self.bonus_combo.addItem(f"{ab} save {sign(bonus)}", (f"{ab} save", bonus))
            for ab in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
                mod = ability_mod(char, ab)
                self.bonus_combo.addItem(f"{ab} check {sign(mod)}", (f"{ab} check", mod))
        self.bonus_combo.setCurrentIndex(min(keep, self.bonus_combo.count() - 1))

    def _bonus_picked(self, *_):
        data = self.bonus_combo.currentData()
        expr = self.expr_edit.text()
        if self._fresh or not _dice.parse(expr) or isinstance(_dice.parse(expr), str):
            expr = "1d20"            # a bonus on its own: a d20 with it
        self.expr_edit.setText(_dice.set_modifier(expr, data[1] if data else 0) or expr)
        self._fresh = False

    # ── The tray ──────────────────────────────────────────────────────
    def _add_die(self, sides: int):
        expr = "" if self._fresh else self.expr_edit.text()
        if self._fresh:
            self.bonus_combo.setCurrentIndex(0)
        self.expr_edit.setText(_dice.add_die(expr, sides))
        self._fresh = False

    def _set_mode(self, key: str):
        self._mode = key
        for k, b in self._mode_btns.items():
            b.setChecked(k == key)

    def _clear_tray(self):
        self.expr_edit.clear()
        self.bonus_combo.setCurrentIndex(0)
        self._set_mode("normal")
        self._fresh = False

    def _roll(self):
        res = _dice.roll(self.expr_edit.text(), self._mode)
        if res["error"]:
            self.result_detail.setText(res["error"])
            self.result_main.setText("—")
            self.crit_badge.hide()
            return
        self.expr_edit.setText(res["expr"])
        bonus = self.bonus_combo.currentData()
        detail = res["text"] + (f"  ({bonus[0]})" if bonus else "")
        self._show_result(res["total"], detail, nat=res["nat"])
        _log.log_roll(self._char, "dice", res["expr"], res["total"], detail, nat=res["nat"],
                      result=res["mode"] if res["mode"] != "normal" else "")
        self._fresh = True

    def _show_result(self, total, detail, nat=0):
        self.result_main.setText(str(total))
        self.result_detail.setText(detail)
        if nat == 20:
            color, border = TEAL2, TEAL2
            self.crit_badge.setText("NATURAL 20")
            self.crit_badge.setStyleSheet(f"background:{TEAL};color:{on_fill(TEAL)};font-size:{FS_TINY}px;"
                                          f"font-weight:700;border-radius:4px;padding:2px 8px;")
            self.crit_badge.show()
        elif nat == 1:
            color, border = CRIM2, CRIM2
            self.crit_badge.setText("NATURAL 1")
            self.crit_badge.setStyleSheet(f"background:{CRIMSON};color:{on_fill(CRIMSON)};font-size:{FS_TINY}px;"
                                          f"font-weight:700;border-radius:4px;padding:2px 8px;")
            self.crit_badge.show()
        else:
            color, border = GOLD2, BORDER2
            self.crit_badge.hide()
        self.result_main.setStyleSheet(_big(color))
        self.result_frame.setStyleSheet(
            f"QFrame{{background:{qa(INDIGO,0x44)};border:2px solid {INDIGO};border-radius:10px;}}")
        QTimer.singleShot(200, lambda bc=border: self.result_frame.setStyleSheet(
            f"QFrame{{background:{SURF};border:2px solid {bc};border-radius:10px;}}"))

    # ── The history ───────────────────────────────────────────────────
    def _on_logged(self, char, entry):
        if char is self._char:
            QTimer.singleShot(0, self._refresh_history)

    def _refresh_history(self):
        while self.history_lay.count():
            w = self.history_lay.takeAt(0).widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        entries = _log.roll_history(self._char)
        name = (self._char or {}).get("name") or ""
        self.history_title.setText(f"HISTORY · {name.upper()}" if name else "HISTORY")
        self.clear_hist_btn.setEnabled(bool(entries))
        if not entries:
            self.history_lay.addWidget(lbl("No rolls yet. Your sheet's rolls show here too: checks, saves, "
                                           "attacks, hit dice.", TEXT3, size=FS_TINY, wrap=True))
        for e in entries[:SHOWN]:
            self.history_lay.addWidget(self._history_row(e))
        self.history_lay.addStretch(1)

    def _history_row(self, e: dict) -> QWidget:
        row = QFrame(); row.setObjectName("rollRow")
        row.setStyleSheet(f"QFrame#rollRow{{background:{SURF};border-radius:6px;}}"
                          f"QFrame#rollRow:hover{{background:{SURF2};}}")
        rl = QHBoxLayout(row); rl.setContentsMargins(8, 5, 8, 5); rl.setSpacing(8)
        col = QVBoxLayout(); col.setSpacing(1)
        result = f" · {e['result']}" if e.get("result") else ""
        head = lbl(f"<span style='color:{TEXT3}'>{_log.when(e)}</span>&nbsp;&nbsp;"
                   f"<b>{html.escape(e.get('label') or '')}</b>{html.escape(result)}", TEXT, size=FS_TINY, wrap=True)
        head.setTextFormat(Qt.RichText)
        col.addWidget(head)
        if e.get("detail"):
            col.addWidget(lbl(e["detail"], TEXT2, size=FS_TINY, wrap=True))
        rl.addLayout(col, 1)
        if e.get("total") is not None:
            tint = TEAL2 if e.get("nat") == 20 else CRIM2 if e.get("nat") == 1 else GOLD2
            tot = lbl(str(e["total"]), tint, bold=True, size=FS_HEAD, align=Qt.AlignRight | Qt.AlignVCenter)
            tot.setToolTip("A natural 20" if e.get("nat") == 20 else "A natural 1" if e.get("nat") == 1 else "")
            rl.addWidget(tot)
        if e.get("kind") == "dice":
            row.setCursor(Qt.PointingHandCursor)
            row.setToolTip("Click to roll these dice again")
            row.mousePressEvent = lambda ev, ex=e: self._reuse(ex)
        return row

    def _reuse(self, e: dict):
        """A tray roll from the history, back in the tray."""
        self.expr_edit.setText(e.get("label") or "")
        self._set_mode(e.get("result") if e.get("result") in ("advantage", "disadvantage") else "normal")
        self._fresh = False

    def _clear_history(self):
        if QMessageBox.question(self, "Clear history", "Clear this character's roll history?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        _log.clear_roll_history(self._char)
        self._refresh_history()
        self.result_main.setText("—")
        self.result_detail.setText("Pick dice below, then Roll.")
        self.crit_badge.hide()
        self.result_frame.setStyleSheet(
            f"QFrame{{background:{SURF};border:2px solid {BORDER2};border-radius:10px;}}")
