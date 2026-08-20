"""Shared helper widgets used across wizard and sheet.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from .theme import *
ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]
AB_FULL = {"STR":"Strength","DEX":"Dexterity","CON":"Constitution",
           "INT":"Intelligence","WIS":"Wisdom","CHA":"Charisma"}

def sign(n): return f"+{n}" if n >= 0 else str(n)

def h(text, color=None, size=FS_BODY, bold=False, align=Qt.AlignLeft, wrap=True):
    """Quick label factory."""
    w = QLabel(text)
    c = color or TEXT
    s = f"color:{c};font-size:{size}px;background:transparent;"
    if bold: s += "font-weight:700;"
    w.setStyleSheet(s)
    w.setAlignment(align)
    if wrap: w.setWordWrap(True)
    return w

def section_header(text, color=None):
    lbl = h(text.upper(), color or GOLD, FS_SMALL, bold=True)
    lbl.setStyleSheet(lbl.styleSheet() + f"letter-spacing:2px;padding-bottom:2px;")
    return lbl

def hline():
    f = QFrame(); f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"color:{BORDER};background:{BORDER};max-height:1px;border:none;")
    return f

def card(parent=None, color=BORDER):
    """Styled card frame."""
    f = QFrame(parent)
    f.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {color};border-radius:10px;}}")
    return f

def pill_btn(text, bg=INDIGO, fg="white", hover=None):
    """Styled button."""
    btn = QPushButton(text)
    h_color = hover or IND2
    btn.setStyleSheet(
        f"QPushButton{{background:{bg};border:none;border-radius:8px;color:{fg};"
        f"font-weight:700;font-size:{FS_BODY}px;padding:9px 20px;}}"
        f"QPushButton:hover{{background:{h_color};}}"
        f"QPushButton:pressed{{background:{BG};}}"
        f"QPushButton:disabled{{background:{SURF3};color:{TEXT3};}}"
    )
    return btn

def badge(text, bg=INDIGO, size=FS_SMALL):
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background:{bg};color:white;font-size:{size}px;font-weight:700;"
        f"border-radius:{size}px;padding:2px 8px;"
    )
    lbl.setFixedHeight(size + 8)
    return lbl

class BigStatBox(QFrame):
    """Large stat display box: big number + label below."""
    def __init__(self, label, value="—", color=None, parent=None):
        super().__init__(parent)
        self._color = color or IND2
        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border:2px solid {BORDER};border-radius:10px;}}"
        )
        lay = QVBoxLayout(self); lay.setContentsMargins(10,10,10,8); lay.setSpacing(2)
        self._val_lbl = QLabel(str(value))
        self._val_lbl.setAlignment(Qt.AlignCenter)
        f = QFont(); f.setBold(True); f.setPointSize(20)
        self._val_lbl.setFont(f)
        self._val_lbl.setStyleSheet(f"color:{self._color};background:transparent;")
        self._ttl_lbl = QLabel(label)
        self._ttl_lbl.setAlignment(Qt.AlignCenter)
        self._ttl_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:700;background:transparent;letter-spacing:1px;")
        lay.addWidget(self._val_lbl); lay.addWidget(self._ttl_lbl)

    def set_val(self, v): self._val_lbl.setText(str(v))
    def set_color(self, c):
        self._color = c
        self._val_lbl.setStyleSheet(f"color:{c};background:transparent;")

class AbilityBlock(QFrame):
    """One ability score block: name / score / modifier."""
    changed = Signal(str, int)   # (ability, new_score)

    def __init__(self, ab, score=10, editable=True, parent=None):
        super().__init__(parent)
        self.ab = ab
        self._editable = editable
        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border:2px solid {BORDER};border-radius:12px;}}"
            f"QFrame:hover{{border-color:{BORDER2};}}"
        )
        self.setFixedWidth(120)
        lay = QVBoxLayout(self); lay.setContentsMargins(8,8,8,10); lay.setSpacing(4)

        # Ability name
        name_lbl = h(ab, TEXT2, FS_SMALL, bold=True, align=Qt.AlignCenter, wrap=False)
        lay.addWidget(name_lbl)

        # Score spinbox or label
        if editable:
            self._score_spin = QSpinBox()
            self._score_spin.setRange(1, 20)
            self._score_spin.setValue(score)
            self._score_spin.setAlignment(Qt.AlignCenter)
            self._score_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self._score_spin.setStyleSheet(
                f"QSpinBox{{font-size:{FS_STAT}px;font-weight:700;color:{TEXT};"
                f"border:none;background:transparent;text-align:center;}}"
            )
            def _on_spin_change(v, self=self):
                mod = (v - 10) // 2
                self._mod_lbl.setText(sign(mod))
                self._mod_lbl.setStyleSheet(
                    f"color:{TEAL2 if mod >= 0 else CRIM2};font-size:{FS_TITLE}px;"
                    f"font-weight:700;background:transparent;")
                self.changed.emit(self.ab, v)
            self._score_spin.valueChanged.connect(_on_spin_change)
            lay.addWidget(self._score_spin)
        else:
            self._score_lbl = h(str(score), TEXT, FS_STAT, bold=True, align=Qt.AlignCenter)
            lay.addWidget(self._score_lbl)

        # Modifier
        mod = (score - 10) // 2
        self._mod_lbl = h(sign(mod), TEAL2 if mod >= 0 else CRIM2, FS_TITLE, bold=True, align=Qt.AlignCenter)
        lay.addWidget(self._mod_lbl)

    def set_score(self, v):
        if self._editable:
            self._score_spin.blockSignals(True)
            self._score_spin.setValue(v)
            self._score_spin.blockSignals(False)
        else:
            self._score_lbl.setText(str(v))
        mod = (v - 10) // 2
        self._mod_lbl.setText(sign(mod))
        self._mod_lbl.setStyleSheet(
            f"color:{TEAL2 if mod >= 0 else CRIM2};font-size:{FS_TITLE}px;font-weight:700;background:transparent;"
        )

    def value(self):
        return self._score_spin.value() if self._editable else int(self._score_lbl.text())


def _spell_tooltip(spell: dict) -> str:
    """Full spell description for hover tooltips."""
    name = spell.get("name", "Spell")
    lvl = spell.get("level", 0)
    lvl_s = "Cantrip" if lvl == 0 else f"Level {lvl}"
    parts = [
        f"{name} ({lvl_s})",
        f"School: {spell.get('school', '?')}",
        f"Casting Time: {spell.get('casting_time', spell.get('cast_time', '?'))}",
        f"Range: {spell.get('range', '?')}",
        f"Components: {spell.get('components', '?')}",
        f"Duration: {spell.get('duration', '?')}",
    ]
    if spell.get("concentration"):
        parts.append("Concentration: Yes")
    if spell.get("ritual"):
        parts.append("Ritual: Yes")
    desc = spell.get("desc", "")
    if desc:
        parts.append("")
        parts.append(desc)
    higher = spell.get("higher_levels", "")
    if higher:
        parts.append("")
        parts.append(f"At Higher Levels: {higher}")
    return "\n".join(parts)


class SpellRow(QFrame):
    """One row in the spell list."""
    remove           = Signal(object)
    cast             = Signal(dict)
    cast_ritual      = Signal(dict)
    toggle_quick     = Signal(str, bool)   # (spell_name, pinned)
    prepared_toggled = Signal(object, bool)  # (row, checked)

    LEVEL_COLORS = [SURF3,TEAL,IND2,PURPLE,AMBER,GOLD,CRIMSON,"#8b0000","#6b0000","#4b0000"]

    def __init__(self, spell, prepared=False, parent=None, locked=False, display_name=None):
        super().__init__(parent)
        self.spell = spell
        lvl = spell["level"]
        lc  = self.LEVEL_COLORS[min(lvl, 9)]
        self.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:7px;}}"
            f"QFrame:hover{{background:{SURF2};border-color:{BORDER2};}}"
        )
        lay = QHBoxLayout(self); lay.setContentsMargins(8,6,8,6); lay.setSpacing(8)

        # Level pill
        lvl_txt = "C" if lvl==0 else str(lvl)
        lvl_pill = h(lvl_txt, "white", FS_SMALL, bold=True, align=Qt.AlignCenter, wrap=False)
        lvl_pill.setFixedSize(28,28)
        lvl_pill.setStyleSheet(f"background:{lc};color:white;border-radius:14px;font-size:{FS_SMALL}px;font-weight:700;")
        lay.addWidget(lvl_pill)

        # Prepared checkbox — cantrips are always available (PHB p.201), and
        # bonus spells granted outside the normal preparation system (a feat
        # like Magic Initiate, a racial trait, etc.) work the same way: the
        # character just knows/can cast them, with no daily prep choice and
        # no competing for room against ordinary prepared spells. Both get
        # locked checked+disabled rather than a meaningful toggle.
        self._prep_cb = QCheckBox()
        self._prep_cb.setChecked(prepared)
        if lvl == 0:
            self._prep_cb.setChecked(True)
            self._prep_cb.setEnabled(False)
            self._prep_cb.setToolTip("Cantrips are always available — no preparation needed")
        elif locked:
            self._prep_cb.setChecked(True)
            self._prep_cb.setEnabled(False)
            self._prep_cb.setToolTip(
                "Granted outside normal preparation (feat/racial/class bonus spell) — "
                "always available and doesn't count against your prepared spell limit.")
        else:
            self._prep_cb.setToolTip("Prepared")
            self._prep_cb.toggled.connect(lambda checked: self.prepared_toggled.emit(self, checked))
        lay.addWidget(self._prep_cb)

        # Spell info
        info_col = QVBoxLayout(); info_col.setSpacing(1)
        name_row = QHBoxLayout(); name_row.setSpacing(6)
        self._name_lbl = h(display_name or spell["name"], TEXT, FS_BODY, bold=True, wrap=False)
        name_row.addWidget(self._name_lbl)
        if spell.get("concentration"):
            name_row.addWidget(badge("Conc", PURPLE, FS_TINY))
        if spell.get("ritual"):
            name_row.addWidget(badge("Rit", TEAL, FS_TINY))
        # Class-source badge — only shown for multiclass known-spell casters
        # (Sorcerer/Warlock etc.), set via set_class_tag() since attribution
        # can shift as spells are added/removed. Hidden by default.
        self._class_tag_lbl = badge("", TEXT3, FS_TINY)
        self._class_tag_lbl.setVisible(False)
        name_row.addWidget(self._class_tag_lbl)
        name_row.addStretch()
        info_col.addLayout(name_row)
        details = f"{spell.get('school','?')} · {spell.get('casting_time', spell.get('cast_time','?'))} · {spell.get('range','?')}"
        detail_lbl = h(details, TEXT2, FS_SMALL, wrap=True)
        detail_lbl.setMinimumHeight(36)
        info_col.addWidget(detail_lbl)
        lay.addLayout(info_col, 1)

        tip = _spell_tooltip(spell)
        self.setToolTip(tip)
        for w in (lvl_pill, self._prep_cb, detail_lbl):
            w.setToolTip(tip)

        # Star: pin to Quick Spells on Combat tab
        self._pinned = False
        self._star_btn = QPushButton("☆"); self._star_btn.setFixedSize(26,26)
        self._star_btn.setToolTip("Pin to Quick Spells (Combat tab)")
        self._star_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT3};font-size:15px;}}QPushButton:hover{{color:#ffd700;}}")
        self._star_btn.clicked.connect(self._on_star)
        lay.addWidget(self._star_btn)

        # Remove button
        rm = QPushButton("✕"); rm.setFixedSize(28,28)
        rm.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT3};font-size:16px;border-radius:14px;}}QPushButton:hover{{background:{CRIMSON};color:white;}}")
        rm.clicked.connect(lambda: self.remove.emit(self))
        lay.addWidget(rm)

    def set_display_name(self, text: str):
        """Update just the title label's text (Immersive Spells optional
        rule) -- leaves self.spell["name"] and everything else about the
        row (tooltip, context menu, cast/prep logic) untouched."""
        self._name_lbl.setText(text)

    def set_pinned(self, pinned: bool):
        self._pinned = pinned
        self._star_btn.setText("★" if pinned else "☆")
        color = "#ffd700" if pinned else TEXT3
        self._star_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{color};font-size:15px;}}QPushButton:hover{{color:#ffd700;}}")

    _TAG_COLORS = {
        "Sorcerer": INDIGO, "Warlock": PURPLE, "Bard": TEAL,
        "Ranger": "#4a8c3f", "Fighter (EK)": AMBER, "Rogue (AT)": AMBER,
    }

    def set_class_tag(self, class_name):
        """Show/hide the small class-source badge (e.g. 'SORC', 'LOCK').
        Pass None to hide it (single-class casters don't need this)."""
        if not class_name:
            self._class_tag_lbl.setVisible(False)
            return
        abbrev = {"Sorcerer":"SORC", "Warlock":"LOCK", "Bard":"BARD",
                  "Ranger":"RNGR", "Fighter (EK)":"EK", "Rogue (AT)":"AT"}.get(
                      class_name, class_name[:4].upper())
        color = self._TAG_COLORS.get(class_name, TEXT3)
        self._class_tag_lbl.setText(abbrev)
        self._class_tag_lbl.setStyleSheet(
            f"background:{color};color:white;font-size:{FS_TINY}px;font-weight:700;"
            f"border-radius:{FS_TINY}px;padding:2px 8px;")
        self._class_tag_lbl.setToolTip(f"Counts against your {class_name} known-spells pool")
        self._class_tag_lbl.setVisible(True)

    def _on_star(self):
        self._pinned = not self._pinned
        self.set_pinned(self._pinned)
        self.toggle_quick.emit(self.spell["name"], self._pinned)

    def is_prepared(self): return self._prep_cb.isChecked()
    def set_prepared(self, v): self._prep_cb.setChecked(v)
    def is_prepared(self): return self._prep_cb.isChecked()
    def set_can_ritual(self, v): self._can_ritual = bool(v)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu{{background:{SURF2};border:2px solid {BORDER2};color:{TEXT};font-size:{FS_BODY}px;padding:4px;}}"
                           f"QMenu::item{{padding:8px 20px;border-radius:4px;}}"
                           f"QMenu::item:selected{{background:{INDIGO};color:white;}}")
        detail_act = menu.addAction(f"📖  Show Details: {self.spell['name']}")
        menu.addSeparator()
        cast_act  = menu.addAction(f"🎲  Cast {self.spell['name']}")
        ritual_act = None
        if self.spell.get("ritual") and getattr(self, "_can_ritual", False):
            ritual_act = menu.addAction(
                f"📜  Cast {self.spell['name']} as Ritual (no slot, +10 min cast time)")
        prep_act  = menu.addAction("✓  Toggle Prepared")
        star_act  = menu.addAction("★  Pin to Quick Spells" if not self._pinned else "☆  Unpin from Quick Spells")
        menu.addSeparator()
        rm_act    = menu.addAction("✕  Remove from list")
        action = menu.exec(event.globalPos())
        if action == detail_act:
            from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget
            s = self.spell
            lvl_txt = "Cantrip" if s.get("level",0)==0 else f"Level {s.get('level','?')}"
            desc = s.get("desc") or s.get("description","")
            higher = s.get("higher_levels","") or s.get("higher","")
            detail = (f"<b>{s['name']}</b>  [{lvl_txt} {s.get('school','').title()}]<br>"
                      f"<i>Casting Time:</i> {s.get('casting_time',s.get('cast_time','—'))}<br>"
                      f"<i>Range:</i> {s.get('range','—')}  &nbsp; <i>Duration:</i> {s.get('duration','—')}<br>"
                      f"<i>Components:</i> {s.get('components','—')}<br><br>"
                      f"{desc}<br><br>" + (f"<i>At Higher Levels:</i> {higher}" if higher else ""))
            dlg = QDialog(); dlg.setWindowTitle(s['name']); dlg.setMinimumWidth(500)
            lay = QVBoxLayout(dlg)
            lbl = QLabel(detail); lbl.setWordWrap(True); lbl.setOpenExternalLinks(False)
            lbl.setStyleSheet("font-size:13px;padding:8px;")
            sa = QScrollArea(); sa.setWidgetResizable(True)
            inner = QWidget(); il = QVBoxLayout(inner); il.addWidget(lbl)
            sa.setWidget(inner); lay.addWidget(sa)
            from PySide6.QtWidgets import QDialogButtonBox
            bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(dlg.reject)
            lay.addWidget(bb); dlg.exec()
        elif action == cast_act:  self.cast.emit(self.spell)
        elif ritual_act is not None and action == ritual_act: self.cast_ritual.emit(self.spell)
        elif action == prep_act: self._prep_cb.setChecked(not self._prep_cb.isChecked())
        elif action == star_act: self._on_star()
        elif action == rm_act:  self.remove.emit(self)
