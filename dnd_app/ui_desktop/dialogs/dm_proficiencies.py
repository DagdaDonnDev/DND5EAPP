"""DM-granted proficiencies (desktop): weapons, armour, tools and
languages your DM gives you outside the usual rules. The rules live in
core/dm_proficiencies.py; Android has the same editor on its
Proficiencies screen."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QCompleter, QDialog, QFrame, QHBoxLayout,
                               QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from dnd_app.core import dm_proficiencies as rules
from dnd_app.ui_desktop import icons as _icons

TITLE = "DM-granted proficiencies"
ABOUT = ("Proficiencies your DM gives you outside the usual rules. They count like "
         "any other: attack rolls, Dedicated Weapon, feat prerequisites, tools and "
         "the exported sheet.")
_ADD_HINT = {"weapons": "Add a weapon, or Simple weapons, Martial weapons, Firearms…",
             "armor": "Add an armour type or Shields…",
             "tools": "Add a tool or kit…",
             "languages": "Add a language…"}


class DmProficienciesDialog(QDialog):
    """One section per kind: what's granted (each with a remove button),
    then a box to add another -- pick from the list or type any name."""

    def __init__(self, char: dict, on_change=None, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals
        self.t = {}
        sync_globals(self.t)
        self.char = char
        self._on_change = on_change or (lambda: None)
        t = self.t
        self.setWindowTitle(TITLE)
        self.setMinimumWidth(520)
        self.resize(560, 720)
        self.setStyleSheet(f"QDialog{{background:{t['BG']};}}")

        root = QVBoxLayout(self); root.setContentsMargins(20, 18, 20, 18); root.setSpacing(12)
        title = QLabel(TITLE)
        title.setStyleSheet(f"color:{t['GOLD2']};font-size:{t['FS_HEAD']}px;font-weight:700;")
        root.addWidget(title)
        about = QLabel(ABOUT); about.setWordWrap(True)
        about.setStyleSheet(f"color:{t['TEXT2']};font-size:{t['FS_SMALL']}px;")
        root.addWidget(about)

        # the four sections scroll together if the lists get long
        body = QWidget(); body.setStyleSheet("background:transparent;")
        self._body = QVBoxLayout(body); self._body.setContentsMargins(0, 0, 4, 0); self._body.setSpacing(14)
        self._lists = {}
        for kind, heading, _ in rules.KINDS:
            self._body.addWidget(self._section(kind, heading))
        self._body.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(body)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        root.addWidget(scroll, 1)

        btns = QHBoxLayout(); btns.addStretch()
        done = QPushButton("Done"); done.setFixedHeight(34); done.clicked.connect(self.accept)
        done.setStyleSheet(f"QPushButton{{background:{t['SURF2']};color:{t['TEXT']};border:1px solid {t['GOLD']};"
                           f"border-radius:7px;padding:4px 24px;font-size:{t['FS_BODY']}px;font-weight:700;}}"
                           f"QPushButton:hover{{background:{t['SURF3']};}}")
        btns.addWidget(done)
        root.addLayout(btns)
        for kind, _, _ in rules.KINDS:
            self._show(kind)

    # ── One kind: heading, what's granted, the add box ───────────────────
    def _section(self, kind, heading):
        t = self.t
        box = QFrame()
        # a gold bar down the left marks each section (colour stays off the text)
        box.setStyleSheet(f"QFrame#dmSection{{background:{t['SURF']};border:1px solid {t['BORDER']};"
                          f"border-left:3px solid {t['GOLD']};border-radius:8px;}}")
        box.setObjectName("dmSection")
        lay = QVBoxLayout(box); lay.setContentsMargins(12, 10, 12, 12); lay.setSpacing(8)
        head = QLabel(heading.upper())
        head.setStyleSheet(f"color:{t['TEXT']};font-size:{t['FS_SMALL']}px;font-weight:700;"
                           f"background:transparent;border:none;")
        lay.addWidget(head)
        rows = QVBoxLayout(); rows.setSpacing(4)
        lay.addLayout(rows)
        self._lists[kind] = rows

        add_row = QHBoxLayout(); add_row.setSpacing(8)
        combo = QComboBox(); combo.setEditable(True); combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setObjectName(f"dmAdd_{kind}")
        combo.addItems(rules.suggestions(kind))
        combo.setCurrentIndex(-1)
        combo.lineEdit().setPlaceholderText(_ADD_HINT[kind])
        # typing finds a match anywhere in the name ("bow" -> Longbow, Shortbow)
        completer = QCompleter(rules.suggestions(kind), combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        combo.setCompleter(completer)
        add = QPushButton("Add"); add.setObjectName(f"dmAddBtn_{kind}")
        add.setFixedHeight(combo.sizeHint().height())      # same height as the box beside it
        add.setStyleSheet(f"QPushButton{{background:{t['SURF2']};color:{t['TEXT']};border:1px solid {t['BORDER2']};"
                          f"border-radius:6px;padding:0 18px;min-height:0;font-size:{t['FS_BODY']}px;font-weight:700;}}"
                          f"QPushButton:hover{{background:{t['SURF3']};border-color:{t['GOLD']};}}")
        add.clicked.connect(lambda checked=False, k=kind, c=combo: self._add(k, c))
        combo.lineEdit().returnPressed.connect(lambda k=kind, c=combo: self._add(k, c))
        add_row.addWidget(combo, 1); add_row.addWidget(add)
        lay.addLayout(add_row)
        return box

    def _show(self, kind):
        """Redraw one section's granted list."""
        t = self.t
        rows = self._lists[kind]
        while rows.count():
            item = rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        names = rules.granted(self.char, kind)
        if not names:
            none = QLabel("None yet")
            none.setStyleSheet(f"color:{t['TEXT3']};font-size:{t['FS_SMALL']}px;background:transparent;border:none;")
            rows.addWidget(none)
            return
        for name in names:
            row = QFrame(); row.setObjectName("dmRow")
            row.setStyleSheet(f"QFrame#dmRow{{background:{t['SURF2']};border:1px solid {t['BORDER']};border-radius:6px;}}")
            rl = QHBoxLayout(row); rl.setContentsMargins(10, 4, 4, 4); rl.setSpacing(6)
            lbl = QLabel(name)
            lbl.setStyleSheet(f"color:{t['TEXT']};font-size:{t['FS_BODY']}px;background:transparent;border:none;")
            rm = QPushButton(); rm.setFixedSize(30, 28); rm.setToolTip(f"Remove {name}")
            rm.setIcon(_icons.icon("trash", 16)); rm.setObjectName(f"dmRemove_{kind}_{name}")
            rm.setStyleSheet(f"QPushButton{{background:transparent;border:1px solid {t['BORDER']};border-radius:5px;"
                             f"padding:0;min-height:0;}}"
                             f"QPushButton:hover{{border-color:{t['CRIM2']};}}")
            rm.clicked.connect(lambda checked=False, k=kind, n=name: self._remove(k, n))
            rl.addWidget(lbl, 1); rl.addWidget(rm)
            rows.addWidget(row)

    def _add(self, kind, combo):
        if rules.add(self.char, kind, combo.currentText()):
            self._on_change()
            self._show(kind)
        combo.setCurrentIndex(-1)
        combo.setEditText("")

    def _remove(self, kind, name):
        rules.remove(self.char, kind, name)
        self._on_change()
        self._show(kind)
