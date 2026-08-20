"""Reusable custom widgets for the character creator.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QFont
from .theme import *


class FlowLayout(QLayout):
    """A layout that arranges child widgets left-to-right, wrapping onto a
    new row when the current row runs out of horizontal space — used for
    badge/chip strips (like the resistances/immunities row) that need to
    hold an unpredictable, potentially large number of items without
    overflowing off-screen or getting squeezed into unreadable widths."""
    def __init__(self, parent=None, margin=0, h_spacing=6, v_spacing=6):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x, y = effective_rect.x(), effective_rect.y()
        line_height = 0
        for item in self._items:
            widget = item.widget()
            # isVisible() depends on the whole ancestor chain already being
            # shown, which isn't reliably true yet for a widget added to
            # the layout moments ago (even though it WILL become visible
            # once the event loop catches up) — that timing gap caused
            # freshly-added items to get silently skipped here, leaving
            # them at Qt's default (0,0,640,480) placeholder geometry,
            # stacked on top of everything else. isHidden() only reflects
            # an explicit hide()/setVisible(False) on this widget, which is
            # the only case we actually want to skip.
            if widget is not None and widget.isHidden():
                continue
            next_x = x + item.sizeHint().width() + self._h_spacing
            if next_x - self._h_spacing > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + self._v_spacing
                next_x = x + item.sizeHint().width() + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y() + bottom


class FlowContainer(QWidget):
    """A QWidget meant to hold a FlowLayout. Plain QWidget/QFrame containers
    don't automatically grow to fit a wrapping FlowLayout's real height —
    QVBoxLayout doesn't query a child's heightForWidth() the way it would
    need to for that to work — so without this, badges on the second and
    later wrapped rows silently overlap whatever comes next below the
    container instead of pushing it down. This keeps the widget's own
    minimum height in sync with the layout's computed wrapped height
    every time it's resized (i.e. every time the flow re-wraps)."""
    def resizeEvent(self, event):
        super().resizeEvent(event)
        lay = self.layout()
        if lay is not None:
            needed = lay.heightForWidth(self.width())
            if needed > 0 and self.minimumHeight() != needed:
                self.setMinimumHeight(needed)



ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]
AB_NAMES  = {"STR":"Strength","DEX":"Dexterity","CON":"Constitution",
             "INT":"Intelligence","WIS":"Wisdom","CHA":"Charisma"}
PROF_CYCLE = {0:2, 2:3, 3:0}
PROF_LABEL = {0:"—", 1:"½", 2:"◆", 3:"◈"}
PROF_COLOR = {0:SURF3, 1:AMBER, 2:INDIGO, 3:PURP2}

def sign(n): return f"+{n}" if n >= 0 else str(n)

def lbl(text, color=TEXT, bold=False, size=11, align=Qt.AlignLeft):
    w = QLabel(text)
    s = f"color:{color}; font-size:{size}px;"
    if bold: s += "font-weight:700;"
    w.setStyleSheet(s); w.setAlignment(align); return w

def hline():
    f = QFrame(); f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background:{BORDER}; max-height:1px;"); return f

def colored_btn(text, bg=INDIGO, fg="white"):
    b = QPushButton(text)
    b.setStyleSheet(f"QPushButton{{background:{bg};border:1px solid {bg};border-radius:5px;"
                    f"color:{fg};padding:5px 12px;font-weight:700;}}"
                    f"QPushButton:hover{{opacity:0.85;background:{qa(bg,0xcc)};}}")
    return b


class AbilityWidget(QWidget):
    changed = Signal()
    def __init__(self, ab, parent=None):
        super().__init__(parent)
        self.ab = ab
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(3)
        lay.addWidget(lbl(AB_NAMES[ab][:3].upper(), TEXT3, bold=True, size=8, align=Qt.AlignCenter))

        frame = QFrame()
        frame.setFixedSize(74, 74)
        frame.setStyleSheet(f"QFrame{{background:{SURF2};border:2px solid {BORDER2};border-radius:8px;}}")
        fl = QVBoxLayout(frame); fl.setContentsMargins(2,2,2,2); fl.setSpacing(0)

        self.spin = QSpinBox(); self.spin.setRange(1,30); self.spin.setValue(10)
        self.spin.setAlignment(Qt.AlignCenter); self.spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin.setStyleSheet(f"QSpinBox{{font-size:22px;font-weight:700;color:{TEXT};"
                                 f"border:none;background:transparent;padding:0;}}")
        self.mod_lbl = lbl("+0", IND2, bold=True, size=14, align=Qt.AlignCenter)
        fl.addWidget(self.spin); fl.addWidget(self.mod_lbl)
        lay.addWidget(frame, alignment=Qt.AlignCenter)

        btn_lay = QHBoxLayout(); btn_lay.setSpacing(2)
        self.minus = QPushButton("−"); self.plus = QPushButton("+")
        for b in (self.minus, self.plus):
            b.setFixedSize(30,20)
            b.setStyleSheet(f"QPushButton{{background:{SURF3};border:1px solid {BORDER};border-radius:3px;"
                            f"color:{TEXT};font-size:14px;font-weight:700;padding:0;}}"
                            f"QPushButton:hover{{background:{INDIGO};color:white;}}")
        btn_lay.addWidget(self.minus); btn_lay.addWidget(self.plus)
        lay.addLayout(btn_lay)

        self.spin.valueChanged.connect(self._update)
        self.minus.clicked.connect(lambda: self.spin.setValue(max(1, self.spin.value()-1)))
        self.plus.clicked.connect(lambda: self.spin.setValue(min(30, self.spin.value()+1)))

    def _update(self, v):
        mod = (v-10)//2
        c = TEAL2 if mod > 0 else (CRIM2 if mod < 0 else TEXT2)
        self.mod_lbl.setText(sign(mod))
        self.mod_lbl.setStyleSheet(f"color:{c};font-size:14px;font-weight:700;")
        self.changed.emit()

    def value(self): return self.spin.value()
    def set_value(self, v):
        self.spin.blockSignals(True); self.spin.setValue(v); self.spin.blockSignals(False); self._update(v)


class SkillRow(QWidget):
    changed = Signal()
    def __init__(self, skill, ab, parent=None):
        super().__init__(parent)
        self.skill = skill; self.ab = ab; self._prof = 0
        lay = QHBoxLayout(self); lay.setContentsMargins(1,1,1,1); lay.setSpacing(5)
        self.pip = QPushButton(PROF_LABEL[0])
        self.pip.setFixedSize(26,26)
        self.pip.setStyleSheet(self._pip_style(0))
        self.pip.setToolTip("Click to cycle: None → Proficient → Expertise")
        self.pip.clicked.connect(self._cycle)
        self.bonus_lbl = lbl("+0", IND2, bold=True, size=12)
        self.bonus_lbl.setFixedWidth(34); self.bonus_lbl.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        skill_lbl = QLabel(skill)
        skill_lbl.setStyleSheet(f"color:{TEXT};font-size:11px;")
        ab_lbl = lbl(f"  {ab}", TEXT3, size=9)
        ab_lbl.setFixedWidth(32)
        lay.addWidget(self.pip); lay.addWidget(self.bonus_lbl)
        lay.addWidget(skill_lbl); lay.addWidget(ab_lbl); lay.addStretch()

    def _pip_style(self, lv):
        c = PROF_COLOR[lv]
        return (f"QPushButton{{background:{c};border:1px solid {BORDER2};border-radius:12px;"
                f"color:{'white' if lv>0 else TEXT3};font-size:10px;font-weight:700;padding:0;}}"
                f"QPushButton:hover{{background:{INDIGO};color:white;}}")

    def _cycle(self):
        self._prof = PROF_CYCLE.get(self._prof, 0)
        self.pip.setText(PROF_LABEL[self._prof]); self.pip.setStyleSheet(self._pip_style(self._prof))
        self.changed.emit()

    def set_prof(self, v):
        self._prof = v; self.pip.setText(PROF_LABEL[v]); self.pip.setStyleSheet(self._pip_style(v))

    def set_bonus(self, v):
        c = TEAL2 if v>0 else (CRIM2 if v<0 else TEXT2)
        self.bonus_lbl.setText(sign(v)); self.bonus_lbl.setStyleSheet(f"color:{c};font-weight:700;font-size:11px;")

    def get_prof(self): return self._prof


class StatBox(QFrame):
    def __init__(self, title, value="—", color=INDIGO, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(6,6,6,6); lay.setSpacing(2)
        self.val = QLabel(value); self.val.setAlignment(Qt.AlignCenter)
        f = QFont(); f.setBold(True); f.setPointSize(18)
        self.val.setFont(f); self.val.setStyleSheet(f"color:{color};")
        self.ttl = QLabel(title); self.ttl.setAlignment(Qt.AlignCenter)
        self.ttl.setStyleSheet(f"color:{TEXT2};font-size:9px;font-weight:700;letter-spacing:0.5px;")
        lay.addWidget(self.val); lay.addWidget(self.ttl)
    def set_val(self, v): self.val.setText(str(v))


class HPTracker(QFrame):
    changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:8px;}}")
        outer = QVBoxLayout(self); outer.setSpacing(6); outer.setContentsMargins(10,10,10,10)
        outer.addWidget(lbl("HIT POINTS", GOLD, bold=True, size=9))
        outer.addWidget(hline())

        grid = QGridLayout(); grid.setSpacing(6)
        def spin_col(label, color):
            vl = QVBoxLayout(); vl.setSpacing(2)
            vl.addWidget(lbl(label, TEXT3, size=8, align=Qt.AlignCenter))
            sp = QSpinBox(); sp.setRange(-999,9999); sp.setValue(0); sp.setAlignment(Qt.AlignCenter)
            sp.setStyleSheet(f"QSpinBox{{font-size:22px;font-weight:700;color:{color};"
                             f"border:2px solid {BORDER};border-radius:6px;background:{SURF2};"
                             f"padding:4px;text-align:center;}}"
                             f"QSpinBox::up-button,QSpinBox::down-button{{width:0;height:0;}}")
            sp.setButtonSymbols(QAbstractSpinBox.NoButtons)
            vl.addWidget(sp); return sp, vl

        self.max_hp, c1 = spin_col("MAX", TEXT)
        self.cur_hp, c2 = spin_col("CURRENT", TEAL2)
        self.tmp_hp, c3 = spin_col("TEMP", AMBER)
        grid.addLayout(c1,0,0); grid.addLayout(c2,0,1); grid.addLayout(c3,0,2)
        outer.addLayout(grid)

        br = QHBoxLayout(); br.setSpacing(6)
        self.amt = QSpinBox(); self.amt.setRange(1,999); self.amt.setValue(1); self.amt.setFixedWidth(60)
        self.dmg_btn = QPushButton("Damage")
        self.heal_btn = QPushButton("Heal")
        self.dmg_btn.setStyleSheet(f"QPushButton{{background:{CRIMSON};border:none;border-radius:5px;color:white;font-weight:700;padding:5px 10px;}}QPushButton:hover{{background:{CRIM2};}}")
        self.heal_btn.setStyleSheet(f"QPushButton{{background:{GREEN};border:none;border-radius:5px;color:white;font-weight:700;padding:5px 10px;}}QPushButton:hover{{background:{GREEN2};}}")
        br.addWidget(self.amt); br.addWidget(self.dmg_btn); br.addWidget(self.heal_btn)
        outer.addLayout(br)

        ds = QHBoxLayout(); ds.setSpacing(10)
        ds.addWidget(lbl("Death Saves:", TEXT3, size=9))
        self.succ = [QCheckBox() for _ in range(3)]
        self.fail = [QCheckBox() for _ in range(3)]
        sl = QHBoxLayout(); sl.addWidget(lbl("✓", TEAL2, bold=True, size=12))
        fl = QHBoxLayout(); fl.addWidget(lbl("✗", CRIM2, bold=True, size=12))
        for s in self.succ: s.setStyleSheet(f"QCheckBox::indicator:checked{{background:{TEAL};}}"); sl.addWidget(s)
        for f in self.fail: f.setStyleSheet(f"QCheckBox::indicator:checked{{background:{CRIMSON};}}"); fl.addWidget(f)
        ds.addLayout(sl); ds.addLayout(fl); ds.addStretch()
        outer.addLayout(ds)

        self.max_hp.valueChanged.connect(self.changed); self.cur_hp.valueChanged.connect(self.changed)
        self.tmp_hp.valueChanged.connect(self.changed)
        self.dmg_btn.clicked.connect(self._dmg); self.heal_btn.clicked.connect(self._heal)

    def _dmg(self):
        a = self.amt.value(); t = self.tmp_hp.value()
        if t >= a: self.tmp_hp.setValue(t-a)
        else: self.tmp_hp.setValue(0); self.cur_hp.setValue(max(-999, self.cur_hp.value()-(a-t)))
        self.changed.emit()

    def _heal(self):
        self.cur_hp.setValue(min(self.max_hp.value(), self.cur_hp.value()+self.amt.value()))
        self.changed.emit()


class ClassEntryRow(QWidget):
    changed = Signal(); remove_me = Signal(object)
    def __init__(self, edition="2014", parent=None):
        super().__init__(parent)
        self.edition = edition
        lay = QHBoxLayout(self); lay.setContentsMargins(0,2,0,2); lay.setSpacing(6)
        self.cls_combo = QComboBox(); self.cls_combo.setFixedWidth(145)
        lv_lbl = QLabel("Lv"); lv_lbl.setStyleSheet(f"color:{TEXT3};font-size:10px;font-weight:700;")
        self.lvl_spin = QSpinBox(); self.lvl_spin.setRange(1,20); self.lvl_spin.setFixedWidth(44)
        self.sub_combo = QComboBox(); self.sub_combo.setMinimumWidth(160); self.sub_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.del_btn = QPushButton("✕"); self.del_btn.setFixedSize(22,22)
        self.del_btn.setStyleSheet(f"QPushButton{{background:{CRIMSON};border:none;border-radius:11px;"
                                   f"color:white;font-weight:700;font-size:12px;padding:0;}}"
                                   f"QPushButton:hover{{background:{CRIM2};}}")
        lay.addWidget(self.cls_combo); lay.addWidget(lv_lbl); lay.addWidget(self.lvl_spin)
        lay.addWidget(self.sub_combo); lay.addWidget(self.del_btn)
        self._populate()
        self.cls_combo.currentTextChanged.connect(self._on_cls)
        self.cls_combo.currentTextChanged.connect(lambda _: self.changed.emit())
        self.lvl_spin.valueChanged.connect(lambda _: self.changed.emit())
        self.sub_combo.currentTextChanged.connect(lambda _: self.changed.emit())
        self.del_btn.clicked.connect(lambda: self.remove.emit(self))

    def _populate(self):
        from dnd_app.data.classes import CLASS_NAMES
        from dnd_app.data.classes_2024 import CLASS_NAMES_2024
        names = CLASS_NAMES_2024 if self.edition=="2024" else CLASS_NAMES
        self.cls_combo.blockSignals(True); self.cls_combo.clear()
        for n in names: self.cls_combo.addItem(n)
        self.cls_combo.blockSignals(False)
        self._on_cls(self.cls_combo.currentText())

    def _on_cls(self, name):
        from dnd_app.data.classes import CLASS_DICT
        from dnd_app.data.classes_2024 import CLASS_DICT_2024
        d = CLASS_DICT_2024 if self.edition=="2024" else CLASS_DICT
        self.sub_combo.blockSignals(True); self.sub_combo.clear()
        self.sub_combo.addItem("— Choose Subclass —")
        for sub in d.get(name,{}).get("subclasses",[]):
            from dnd_app.core.character import clean_subclass_name
            self.sub_combo.addItem(clean_subclass_name(sub), sub)
        self.sub_combo.blockSignals(False)

    def get_cls(self): return self.cls_combo.currentText()
    def get_lvl(self): return self.lvl_spin.value()
    def get_sub(self): return self.sub_combo.currentText() if self.sub_combo.currentIndex()>0 else ""
    def set_data(self, cls, lvl, sub=""):
        i = self.cls_combo.findText(cls)
        if i>=0: self.cls_combo.setCurrentIndex(i)
        self.lvl_spin.setValue(lvl)
        if sub:
            i2 = self.sub_combo.findText(sub)
            if i2>=0: self.sub_combo.setCurrentIndex(i2)


class SpellSlotBar(QWidget):
    changed = Signal()
    def __init__(self, level, parent=None):
        super().__init__(parent)
        self.level = level; self._max = 0
        lay = QHBoxLayout(self); lay.setContentsMargins(2,2,2,2); lay.setSpacing(4)
        label = "Cantrip" if level==0 else f"Level {level}"
        self.lvl_lbl = lbl(label, TEXT2, size=10); self.lvl_lbl.setFixedWidth(60)
        lay.addWidget(self.lvl_lbl)
        self.bubbles = []; self._blay = QHBoxLayout(); self._blay.setSpacing(4)
        lay.addLayout(self._blay); lay.addStretch()
        self.max_lbl = lbl("0", TEXT3, size=9); lay.addWidget(self.max_lbl)

    def update_max(self, mx):
        self._max = mx; self.max_lbl.setText(f"/{mx}")
        for b in self.bubbles: self._blay.removeWidget(b); b.deleteLater()
        self.bubbles = []
        self.setVisible(mx > 0)
        for _ in range(mx):
            b = QCheckBox()
            b.setStyleSheet(
                f"QCheckBox::indicator{{width:18px;height:18px;border-radius:9px;"
                f"border:2px solid {BORDER2};background:{SURF3};}}"
                f"QCheckBox::indicator:checked{{background:{INDIGO};border-color:{IND2};}}")
            b.stateChanged.connect(self.changed)
            self._blay.addWidget(b); self.bubbles.append(b)

    def get_used(self): return sum(1 for b in self.bubbles if b.isChecked())
    def set_used(self, n):
        for i,b in enumerate(self.bubbles):
            b.blockSignals(True); b.setChecked(i<n); b.blockSignals(False)
    def reset(self):
        for b in self.bubbles: b.blockSignals(True); b.setChecked(False); b.blockSignals(False)


SCHOOL_COLORS = {
    "Abjuration": INDIGO, "Conjuration": TEAL, "Divination": GOLD,
    "Enchantment": PURP2, "Evocation": CRIM2, "Illusion": AMBER,
    "Necromancy": GREEN2, "Transmutation": TEXT2,
}
LEVEL_COLORS = [BORDER2, TEAL, IND2, INDIGO, PURP2, AMBER, GOLD, CRIM2, CRIMSON, CRIMSON]


class SpellRow(QWidget):
    """One row in the character's spell list — checkbox for prepared, tags for C/R/school."""
    remove     = Signal(object)
    cast        = Signal(dict)
    toggle_quick = Signal(dict)

    def __init__(self, spell_data, parent=None):
        super().__init__(parent)
        self.spell = spell_data
        self.setStyleSheet(f"QWidget{{background:{SURF2};border-radius:5px;}}QWidget:hover{{background:{SURF3};}}")

        lay = QHBoxLayout(self); lay.setContentsMargins(6,4,6,4); lay.setSpacing(6)

        # Prepared checkbox — star-shaped teal tick
        self.prepared_cb = QCheckBox()
        self.prepared_cb.setToolTip("Mark as prepared")
        self.prepared_cb.setStyleSheet(
            f"QCheckBox::indicator{{width:16px;height:16px;border-radius:3px;"
            f"border:1px solid {BORDER2};background:{SURF3};}}"
            f"QCheckBox::indicator:checked{{background:{TEAL};border-color:{TEAL2};"
            f"image:none;}}")
        lay.addWidget(self.prepared_cb)

        # Concentration marker
        has_c = spell_data.get("concentration", False)
        c_lbl = lbl("C", AMBER if has_c else TEXT3, bold=True, size=9)
        c_lbl.setFixedWidth(11); c_lbl.setToolTip("Concentration" if has_c else "")
        lay.addWidget(c_lbl)

        # Ritual marker
        has_r = spell_data.get("ritual", False)
        r_lbl = lbl("R", PURP2 if has_r else TEXT3, bold=True, size=9)
        r_lbl.setFixedWidth(11); r_lbl.setToolTip("Ritual" if has_r else "")
        lay.addWidget(r_lbl)

        # School colour tag
        sc = spell_data.get("school","")
        sc_c = SCHOOL_COLORS.get(sc, TEXT2)
        sc_lbl = lbl(sc[:3].upper(), sc_c, bold=True, size=8); sc_lbl.setFixedWidth(28)
        lay.addWidget(sc_lbl)

        # Name + short description
        name_col = QVBoxLayout(); name_col.setSpacing(0)
        name_col.addWidget(lbl(spell_data["name"], TEXT, bold=True, size=11))
        desc = spell_data.get("desc","")
        name_col.addWidget(lbl((desc[:80]+"…") if len(desc)>80 else desc, TEXT3, size=9))
        lay.addLayout(name_col); lay.addStretch()

        # Class-source badge — only meaningful (and only shown) for
        # multiclass known-spell casters, so a Sorcerer/Warlock can see at
        # a glance which pool each spell counts against. Set/cleared via
        # set_class_tag() since attribution can shift as spells are added.
        self._tag_lbl = lbl("", TEXT3, bold=True, size=8)
        self._tag_lbl.setFixedWidth(34)
        self._tag_lbl.setAlignment(Qt.AlignCenter)
        self._tag_lbl.setVisible(False)
        lay.addWidget(self._tag_lbl)

        # Level pill
        lvl = spell_data["level"]
        lvl_c = LEVEL_COLORS[min(lvl, 9)]
        lvl_text = "0" if lvl==0 else str(lvl)
        lvl_lbl = lbl(lvl_text, "white", bold=True, size=9, align=Qt.AlignCenter)
        lvl_lbl.setFixedSize(20,20)
        lvl_lbl.setStyleSheet(f"background:{lvl_c};color:white;border-radius:10px;font-size:9px;font-weight:700;padding:2px;")
        lay.addWidget(lvl_lbl)

        # Pin/quick-access button
        self._pin_btn = QPushButton("☆"); self._pin_btn.setFixedSize(20,20)
        self._pin_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT3};font-size:14px;}}QPushButton:hover{{color:#FFD700;}}")
        self._pin_btn.setToolTip("Pin to Quick Spells in Combat tab")
        self._pin_btn.clicked.connect(lambda: (
            self.set_pinned(not self.is_pinned()),
            self.toggle_quick.emit(self.spell)
        ))
        lay.addWidget(self._pin_btn)

        rm = QPushButton("✕"); rm.setFixedSize(20,20)
        rm.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT3};font-size:11px;}}QPushButton:hover{{color:{CRIM2};}}")
        rm.clicked.connect(lambda: self.remove.emit(self))
        lay.addWidget(rm)


    def is_prepared(self): return self.prepared_cb.isChecked()
    def set_prepared(self, v): self.prepared_cb.setChecked(v)

    def is_pinned(self): return getattr(self, '_pinned', False)
    def set_pinned(self, v: bool):
        self._pinned = v
        if hasattr(self, '_pin_btn'):
            self._pin_btn.setText("★" if v else "☆")
            self._pin_btn.setStyleSheet(
                (f"QPushButton{{background:transparent;border:none;"
                 f"color:{'#FFD700' if v else TEXT3};font-size:14px;}}"
                 f"QPushButton:hover{{color:#FFD700;}}"))

    _TAG_COLORS = {
        "Sorcerer": INDIGO, "Warlock": PURPLE, "Bard": TEAL,
        "Ranger": "#4a8c3f", "Fighter (EK)": AMBER, "Rogue (AT)": AMBER,
    }

    def set_class_tag(self, class_name: str | None):
        """Show/hide the small class-source badge (e.g. 'SORC', 'LOCK').
        Pass None to hide it (single-class casters don't need this)."""
        if not class_name:
            self._tag_lbl.setVisible(False)
            return
        abbrev = {"Sorcerer":"SORC", "Warlock":"LOCK", "Bard":"BARD",
                  "Ranger":"RNGR", "Fighter (EK)":"EK", "Rogue (AT)":"AT"}.get(
                      class_name, class_name[:4].upper())
        color = self._TAG_COLORS.get(class_name, TEXT3)
        self._tag_lbl.setText(abbrev)
        self._tag_lbl.setStyleSheet(
            f"background:{color}22;border:1px solid {color}66;border-radius:3px;"
            f"color:{color};font-size:8px;font-weight:700;padding:1px;")
        self._tag_lbl.setToolTip(f"Counts against your {class_name} known-spells pool")
        self._tag_lbl.setVisible(True)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu{{background:{SURF2};border:1px solid {BORDER2};color:{TEXT};padding:4px;}}"
                           f"QMenu::item{{padding:5px 20px;border-radius:3px;}}"
                           f"QMenu::item:selected{{background:{INDIGO};color:white;}}")
        cast_act   = menu.addAction(f"🎲 Cast {self.spell['name']}")
        prep_act   = menu.addAction("✓ Mark as Prepared" if not self.is_prepared() else "✗ Mark as Unprepared")
        detail_act = menu.addAction(f"📖 Show Details")
        menu.addSeparator()
        remove_act = menu.addAction("✕ Remove from list")
        action = menu.exec(event.globalPos())
        if action == cast_act:
            self.cast.emit(self.spell)
        elif action == prep_act:
            self.set_prepared(not self.is_prepared())
        elif action == detail_act:
            name   = self.spell.get("name", "?")
            school = self.spell.get("school", "")
            cast_t = self.spell.get("casting_time", "")
            rng    = self.spell.get("range", "")
            dur    = self.spell.get("duration", "")
            comp   = self.spell.get("components", "")
            desc   = self.spell.get("desc", "No description available.")
            detail = f"<b>{name}</b>"
            if school: detail += f"  <i>({school})</i>"
            detail += "<br>"
            if cast_t: detail += f"Casting Time: {cast_t}<br>"
            if rng:    detail += f"Range: {rng}<br>"
            if dur:    detail += f"Duration: {dur}<br>"
            if comp:   detail += f"Components: {comp}<br>"
            detail += f"<br>{desc[:1500]}"
            QMessageBox.information(self, name, detail)
        elif action == remove_act:
            self.remove.emit(self)



class FeatureCard(QFrame):
    """A single feature shown as a dark card with name + description."""
    def __init__(self, name, desc="", badge_text=None, badge_color=INDIGO, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{SURF3};border:1px solid {BORDER};border-radius:6px;}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(10,6,10,6); lay.setSpacing(3)

        top = QHBoxLayout(); top.setSpacing(6)
        top.addWidget(lbl(name, TEXT, bold=True, size=11))
        if badge_text:
            b = lbl(badge_text, "white", bold=True, size=8, align=Qt.AlignCenter)
            b.setFixedHeight(18)
            b.setStyleSheet(f"color:white;font-size:8px;font-weight:700;background:{badge_color};"
                            f"border-radius:9px;padding:1px 7px;")
            top.addWidget(b)
        top.addStretch()
        lay.addLayout(top)
        if desc:
            d = lbl(desc, TEXT2, size:=10)
            d.setWordWrap(True)
            lay.addWidget(d)


class FeatureSection(QGroupBox):
    """A groupbox containing feature cards, categorised by source."""
    def __init__(self, title, accent_color=GOLD, parent=None):
        super().__init__(parent)
        self._accent = accent_color
        self.setTitle("")
        outer = QVBoxLayout(self); outer.setContentsMargins(8,4,8,8); outer.setSpacing(6)

        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{BG};border-radius:5px;border-left:3px solid {accent_color};}}")
        hl = QHBoxLayout(header); hl.setContentsMargins(10,5,10,5)
        hl.addWidget(lbl(title.upper(), accent_color, bold=True, size=10))
        hl.addStretch()
        outer.addWidget(header)

        self._cards_layout = QVBoxLayout(); self._cards_layout.setSpacing(5)
        outer.addLayout(self._cards_layout)

    def clear(self):
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def add_feature(self, name, desc="", badge_text=None):
        card = FeatureCard(name, desc, badge_text, self._accent)
        self._cards_layout.addWidget(card)

    def is_empty(self): return self._cards_layout.count() == 0


class ResourceWidget(QFrame):
    def __init__(self, name, max_val, reset_type, track="uses", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:6px;}}")
        lay = QHBoxLayout(self); lay.setContentsMargins(8,6,8,6); lay.setSpacing(8)

        rc = CRIM2 if reset_type=="LR" else IND2
        r = lbl(reset_type, rc, bold=True, size=8)
        r.setStyleSheet(f"color:{rc};font-size:8px;font-weight:700;background:{BG};"
                        f"border-radius:8px;padding:2px 5px;border:1px solid {qa(rc,0x44)};")
        lay.addWidget(r)
        lay.addWidget(lbl(name, TEXT, bold=True, size=11)); lay.addStretch()
        lay.addWidget(lbl("Max:", TEXT3, size=9))
        self.max_lbl = lbl(str(max_val), GOLD, bold=True, size=11); lay.addWidget(self.max_lbl)
        lay.addWidget(lbl("Used:", TEXT3, size=9))
        self.current = QSpinBox()
        self.current.setRange(0, max(max_val, 9999) if track=="pool" else max_val)
        self.current.setValue(0); self.current.setFixedWidth(60)
        lay.addWidget(self.current)

        use_btn = QPushButton("Use"); use_btn.setFixedWidth(40)
        use_btn.setStyleSheet(f"QPushButton{{background:{qa(CRIMSON,0x44)};border:1px solid {CRIMSON};border-radius:3px;"
                               f"color:{CRIM2};font-size:9px;font-weight:700;padding:2px;}}"
                               f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
        rst_btn = QPushButton("↺"); rst_btn.setFixedWidth(26)
        rst_btn.setStyleSheet(f"QPushButton{{background:{qa(TEAL,0x44)};border:1px solid {TEAL};border-radius:3px;"
                               f"color:{TEAL2};font-size:12px;padding:1px;}}"
                               f"QPushButton:hover{{background:{TEAL};color:white;}}")
        use_btn.clicked.connect(lambda: self.current.setValue(min(int(self.max_lbl.text()), self.current.value()+1)))
        rst_btn.clicked.connect(lambda: self.current.setValue(0))
        lay.addWidget(use_btn); lay.addWidget(rst_btn)

    def set_max(self, v): self.max_lbl.setText(str(v)); self.current.setMaximum(v)
    def get_used(self): return self.current.value()
    def set_used(self, v): self.current.setValue(v)


# ── Clickable Feature Card ─────────────────────────────────────────────────────
class FeatureCard(QFrame):
    """Dark card for a feature. Clickable — opens FeatureDialog."""
    clicked = Signal(str)   # emits feature_name

    def __init__(self, name, desc="", badge_text=None, badge_color=None, parent=None):
        super().__init__(parent)
        self.feature_name = name
        self._badge_color = badge_color or INDIGO
        self.setStyleSheet(
            f"QFrame{{background:{SURF3};border:1px solid {BORDER};border-radius:6px;}}"
            f"QFrame:hover{{background:{SURF2};border-color:{BORDER2};}}"
        )
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self); lay.setContentsMargins(10,6,10,6); lay.setSpacing(3)

        top = QHBoxLayout(); top.setSpacing(6)
        top.addWidget(lbl(name, TEXT, bold=True, size=11))
        if badge_text:
            b = lbl(badge_text, "white", bold=True, size=8, align=Qt.AlignCenter)
            b.setFixedHeight(18)
            b.setStyleSheet(f"color:white;font-size:8px;font-weight:700;background:{self._badge_color};"
                            f"border-radius:9px;padding:1px 7px;")
            top.addWidget(b)
        # Config indicator
        from dnd_app.data.feature_ui_interactions import get_feature_config
        cfg = get_feature_config(name)
        if cfg and cfg.get("choice_type","info") != "info":
            cfg_dot = lbl("⚙", AMBER, size=12)
            cfg_dot.setToolTip("Click to configure this feature")
            top.addWidget(cfg_dot)
        top.addStretch()
        lay.addLayout(top)

        if desc:
            max_desc = 160
            d_text = (desc[:max_desc] + "…") if len(desc) > max_desc else desc
            lay.addWidget(lbl(d_text, TEXT2, size=10))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.feature_name)
        super().mousePressEvent(event)


# ── Level Group Header (for spell list) ───────────────────────────────────────
class LevelHeader(QFrame):
    LEVEL_COLORS = ["#3d4890","#16a085","#4a6cf0","#7d3c98","#d68910","#c9921a","#c0392b","#8b0000","#8b0000","#4a0000"]
    LEVEL_NAMES  = ["Cantrips","1st Level","2nd Level","3rd Level","4th Level",
                    "5th Level","6th Level","7th Level","8th Level","9th Level"]
    def __init__(self, level: int, parent=None):
        super().__init__(parent)
        self.level = level   # ← store level for lookup
        color = self.LEVEL_COLORS[min(level, 9)]
        name  = self.LEVEL_NAMES[min(level, 9)]
        self.setStyleSheet(f"QFrame{{background:transparent;border-bottom:1px solid {qa(color,0x44)};"
                           f"margin-bottom:2px;margin-top:6px;}}")
        lay = QHBoxLayout(self); lay.setContentsMargins(4,2,4,4); lay.setSpacing(6)
        pill = lbl(name, "white", bold=True, size=9, align=Qt.AlignCenter)
        pill.setFixedHeight(20)
        pill.setStyleSheet(f"background:{color};color:white;border-radius:10px;"
                           f"font-size:9px;font-weight:700;padding:1px 10px;")
        lay.addWidget(pill); lay.addStretch()
