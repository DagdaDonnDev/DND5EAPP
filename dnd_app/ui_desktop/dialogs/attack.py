"""After an attack roll (desktop): the result, what to roll if it hits, and
what you can add or do -- each with its cost, only what you can pay for
right now. The rules and every word live in core/attacks.py
(attack_report, take_attack_options); Android shows the same dialog from
App.qml.

Laid out top to bottom:
  1. the roll: a card with the total, big, how it was made, and what it
     hits ("Hits AC 18 or lower"); a bar down its left side says what it
     was (gold a critical, red a natural 1)
  2. ADD TO THE ROLL / IF IT MISSES: what you can add to the d20 roll
     (Precision Attack, Lucky, Favored by the Gods...). Each has an Add
     button: it's paid for and rolled there and then, and the card above
     shows the new total -- so you see what it hits before you say
  3. IF IT HITS, ROLL: the attack's damage and each extra that's on now
     (a smite your next hit carries, Hunter's Mark...) with its type and
     where it's from, and what else it does under it
  4. ADD TO THIS HIT: damage you can add (Sneak Attack, a Divine Smite
     slot...)
  5. WITH YOUR BONUS ACTION: the off-hand attack, Flurry of Blows...
  6. Missed / It hit: "It hit" pays for what's ticked and sets off what
     the hit carries; "Missed" only takes the bonus action ones
A check or save shows only 1 and 2 (ADD TO THIS CHECK, IF IT FAILS) and
Done. A choice to tick is a row you click anywhere on; a picked row's
border turns gold. Colour stays on the bars and borders, never the words."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)


class _OptionRow(QFrame):
    """One choice: a box to tick, its name, what it adds on the right and
    its cost under the name. Clicking anywhere on the row ticks it."""

    def __init__(self, opt, t, on_change):
        super().__init__()
        self.opt, self._t, self._on_change = opt, t, on_change
        self.setObjectName("attackRow")
        self.setCursor(Qt.PointingHandCursor)
        lay = QHBoxLayout(self); lay.setContentsMargins(12, 9, 12, 9); lay.setSpacing(10)
        self.box = QCheckBox(); self.box.setObjectName(f"attackOption_{opt['key']}")
        # the app's own box: gold when ticked, like Android's
        self.box.setStyleSheet(
            f"QCheckBox{{background:transparent;}}"
            f"QCheckBox::indicator{{width:18px;height:18px;border-radius:4px;"
            f"border:1px solid {t['BORDER2']};background:{t['SURF2']};}}"
            f"QCheckBox::indicator:checked{{background:{t['GOLD']};border:1px solid {t['GOLD']};}}"
            f"QCheckBox::indicator:disabled{{background:{t['SURF']};border:1px solid {t['BORDER']};}}")
        self.box.toggled.connect(self._toggled)
        lay.addWidget(self.box, 0, Qt.AlignTop)
        text = QVBoxLayout(); text.setSpacing(2)
        top = QHBoxLayout(); top.setSpacing(8)
        self.title = QLabel(opt["title"]); self.title.setWordWrap(True)
        top.addWidget(self.title, 1)
        self.dice = QLabel(opt.get("dice", "")); self.dice.setWordWrap(True)
        self.dice.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.dice.setVisible(bool(opt.get("dice")))
        top.addWidget(self.dice, 0)
        text.addLayout(top)
        self.cost = QLabel(opt.get("cost", "")); self.cost.setWordWrap(True)
        self.cost.setVisible(bool(opt.get("cost")))
        text.addWidget(self.cost)
        lay.addLayout(text, 1)
        self._paint()

    def mousePressEvent(self, e):
        if self.isEnabled():
            self.box.setChecked(not self.box.isChecked())
        super().mousePressEvent(e)

    def _toggled(self, _):
        self._paint()
        self._on_change(self)

    def _paint(self):
        t, on, live = self._t, self.box.isChecked(), self.isEnabled()
        border = t["GOLD"] if on else t["BORDER"]
        self.setStyleSheet(
            f"QFrame#attackRow{{background:{t['SURF2'] if on else t['SURF']};"
            f"border:{2 if on else 1}px solid {border};border-radius:8px;}}")
        fg = t["TEXT"] if live else t["TEXT3"]
        for lbl, size, bold in ((self.title, t["FS_BODY"], True), (self.dice, t["FS_BODY"], True),
                                (self.cost, t["FS_SMALL"], False)):
            lbl.setStyleSheet(f"color:{fg if lbl is not self.cost else (t['TEXT2'] if live else t['TEXT3'])};"
                              f"font-size:{size}px;{'font-weight:700;' if bold else ''}"
                              f"background:transparent;border:none;")

    def setEnabled(self, on):
        super().setEnabled(on)
        self._paint()


class _AddRow(QFrame):
    """One thing you can add to the roll now: its name, what it adds on
    the right and its cost under the name, and an Add button that pays for
    it and rolls it there and then."""

    def __init__(self, opt, t, on_add):
        super().__init__()
        self.opt = opt
        self.setObjectName("attackRow")
        self.setStyleSheet(f"QFrame#attackRow{{background:{t['SURF']};border:1px solid {t['BORDER']};"
                           f"border-radius:8px;}}")
        lay = QHBoxLayout(self); lay.setContentsMargins(12, 9, 12, 9); lay.setSpacing(10)
        text = QVBoxLayout(); text.setSpacing(2)
        top = QHBoxLayout(); top.setSpacing(8)
        style = "background:transparent;border:none;"
        title = QLabel(opt["title"]); title.setWordWrap(True)
        title.setStyleSheet(f"color:{t['TEXT']};font-size:{t['FS_BODY']}px;font-weight:700;{style}")
        top.addWidget(title, 1)
        dice = QLabel(opt.get("dice", "")); dice.setWordWrap(True)
        dice.setAlignment(Qt.AlignRight | Qt.AlignTop)
        dice.setStyleSheet(f"color:{t['TEXT']};font-size:{t['FS_BODY']}px;font-weight:700;{style}")
        dice.setVisible(bool(opt.get("dice")))
        top.addWidget(dice, 0)
        text.addLayout(top)
        cost = QLabel(opt.get("cost", "")); cost.setWordWrap(True)
        cost.setStyleSheet(f"color:{t['TEXT2']};font-size:{t['FS_SMALL']}px;{style}")
        cost.setVisible(bool(opt.get("cost")))
        text.addWidget(cost)
        lay.addLayout(text, 1)
        self.button = QPushButton("Add")
        self.button.setObjectName(f"attackAdd_{opt['key']}")
        self.button.setFixedHeight(30)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setStyleSheet(
            f"QPushButton{{background:{t['SURF2']};color:{t['TEXT']};border:1px solid {t['GOLD']};"
            f"border-radius:6px;padding:2px 14px;font-size:{t['FS_SMALL']}px;font-weight:700;}}"
            f"QPushButton:hover{{background:{t['SURF3']};}}")
        self.button.clicked.connect(lambda _=False: on_add(opt["key"]))
        lay.addWidget(self.button, 0, Qt.AlignVCenter)


class AttackDialog(QDialog):
    """exec() is Accepted when "It hit" or "Missed" was pressed -- `hit`
    says which -- and Rejected when it was closed (or Cancel on a crit).
    A check or save (core/checks.py) uses it too: the total is "total", not
    "to hit" (report["total_label"]), and its one button is Done.
    on_add(key) -> the new report: an Add button's choice, paid for and
    rolled by the page (core/attacks.py add_to_attack, core/checks.py
    add_to_check); the dialog then shows the roll as it stands, keeping
    what's ticked. None: nothing changed."""

    def __init__(self, report, parent=None, on_add=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals
        t = {}
        sync_globals(t)
        self._t = t
        self._on_add = on_add
        self.hit = None
        self.setMinimumWidth(500)
        self.setStyleSheet(f"QDialog{{background:{t['BG']};}}")
        outer = QVBoxLayout(self); outer.setContentsMargins(20, 18, 20, 16); outer.setSpacing(12)
        self._title = QLabel()
        self._title.setStyleSheet(f"color:{t['GOLD2']};font-size:{t['FS_HEAD']}px;font-weight:700;")
        outer.addWidget(self._title)
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        outer.addWidget(self._scroll, 1)
        self._btn_box = QWidget()
        self._btns = QHBoxLayout(self._btn_box); self._btns.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._btn_box)
        self._show(report)

    def _show(self, report, keep=()):
        """Lay the dialog out for this report (again, after an Add), with
        the rows in `keep` ticked."""
        t = self._t
        self.report = report
        self._crit = bool((report.get("roll") or {}).get("crit"))
        self._total_label = report.get("total_label") or "to hit"
        self.setWindowTitle(report.get("title") or "Attack")
        self._title.setText(report.get("title") or "Attack")

        body = QWidget(); body.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(body); lay.setContentsMargins(0, 0, 4, 0); lay.setSpacing(10)
        lay.addWidget(self._roll_card(report.get("roll") or {}))
        # the plain text, for anything reading the dialog (and screen readers)
        msg = QLabel(report.get("message", "")); msg.setObjectName("attackMessage"); msg.setVisible(False)
        lay.addWidget(msg)

        self._rows, self._add_rows = [], []
        opts = report.get("options") or []
        sections = report.get("sections") or []
        # what you can add to the roll itself, right under it: Add does it now
        for section in (x for x in sections if x.get("now")):
            lay.addWidget(self._section(section["title"]))
            for o in (o for o in opts if o["section"] == section["name"]):
                row = _AddRow(o, t, self._add)
                self._add_rows.append(row)
                lay.addWidget(row)
        if report.get("hit"):
            lay.addWidget(self._section(report.get("hit_title") or "IF IT HITS, ROLL"))
            lay.addWidget(self._hit_card(report))
        for section in (x for x in sections if not x.get("now")):
            lay.addWidget(self._section(section["title"]))
            for o in (o for o in opts if o["section"] == section["name"]):
                if o.get("head"):
                    lay.addLayout(self._block_head(o))
                row = _OptionRow(o, t, self._changed)
                if o["key"] in keep:
                    row.box.blockSignals(True); row.box.setChecked(True); row.box.blockSignals(False)
                    row._paint()
                self._rows.append(row)
                lay.addWidget(row)
        lay.addStretch()
        # the old layout goes once this click is done with it
        old = self._scroll.takeWidget()
        if old is not None:
            old.deleteLater()
        self._scroll.setWidget(body)
        # as tall as what's in it, up to most of the screen, then it scrolls
        screen = self.screen().availableGeometry().height() if self.screen() else 900
        self._scroll.setMinimumHeight(min(body.sizeHint().height() + 8, int(screen * 0.72)))

        # Missed (Cancel on a crit) and It hit
        while self._btns.count():
            item = self._btns.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._btns.addStretch()
        style = (f"QPushButton{{background:{t['SURF2']};color:{t['TEXT']};border:1px solid {{b}};"
                 f"border-radius:7px;padding:4px 22px;font-size:{t['FS_BODY']}px;font-weight:700;}}"
                 f"QPushButton:hover{{background:{t['SURF3']};}}")
        if report.get("miss_button", "Missed"):
            miss = QPushButton(report.get("miss_button") or "Missed")
            miss.setFixedHeight(36); miss.setObjectName("attackMissed")
            miss.setStyleSheet(style.replace("{b}", t["BORDER2"]))
            miss.clicked.connect(self._missed)
            self._btns.addWidget(miss)
        if report.get("hit_button"):
            hit = QPushButton(report["hit_button"])
            hit.setFixedHeight(36); hit.setObjectName("attackHit")
            hit.setStyleSheet(style.replace("{b}", t["GOLD"]))
            hit.clicked.connect(self._hit)
            hit.setDefault(True)
            self._btns.addWidget(hit)
        self._changed(None)

    def _add(self, key):
        """An Add button: the page pays for it and rolls it, and the
        dialog shows the roll as it now stands."""
        if self._on_add is None:
            return
        new = self._on_add(key)
        if new:
            self._show(new, keep=self.ticked())

    # ── the parts ─────────────────────────────────────────────────────────
    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{self._t['TEXT2']};font-size:{self._t['FS_SMALL']}px;font-weight:700;"
                          f"letter-spacing:1px;margin-top:4px;")
        return lbl

    def _card(self, bar=None):
        t = self._t
        card = QFrame(); card.setObjectName("attackCard")
        left = f"border-left:4px solid {bar};" if bar else ""
        card.setStyleSheet(f"QFrame#attackCard{{background:{t['SURF']};border:1px solid {t['BORDER']};"
                           f"{left}border-radius:8px;}}")
        return card

    def _label(self, text, size, color, bold=False):
        lbl = QLabel(text); lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color:{color};font-size:{size}px;{'font-weight:700;' if bold else ''}"
                          f"background:transparent;border:none;")
        return lbl

    def _roll_card(self, roll):
        t = self._t
        bar = t["GOLD"] if roll.get("crit") else t["CRIM2"] if roll.get("nat1") else t["TEAL2"]
        card = self._card(bar)
        # as tall as what's in it: the room left over in the dialog goes below
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        lay = QHBoxLayout(card); lay.setContentsMargins(16, 10, 16, 12); lay.setSpacing(16)
        big = QVBoxLayout(); big.setSpacing(0)
        total = self._label(str(roll.get("total", "")), t["FS_STAT"], t["TEXT"], True)
        total.setObjectName("attackTotal")
        total.setWordWrap(False)
        big.addWidget(total, 0, Qt.AlignHCenter)
        big.addWidget(self._label(self._total_label, t["FS_SMALL"], t["TEXT2"]), 0, Qt.AlignHCenter)
        lay.addLayout(big)
        info = QVBoxLayout(); info.setSpacing(3)
        info.addWidget(self._label(roll.get("line", ""), t["FS_BODY"], t["TEXT"], True))
        if roll.get("note"):
            info.addWidget(self._label(roll["note"], t["FS_SMALL"], t["TEXT2"]))
        verdict = self._label(roll.get("verdict", ""), t["FS_BODY"], t["TEXT"], bool(roll.get("crit") or roll.get("nat1")))
        verdict.setObjectName("attackVerdict")
        info.addWidget(verdict)
        info.addStretch()
        lay.addLayout(info, 1)
        return card

    def _hit_card(self, report):
        """The attack's damage, then each extra that's on: the dice and type
        on the left, where it's from on the right, what else it does under
        it."""
        t = self._t
        card = self._card()
        lay = QVBoxLayout(card); lay.setContentsMargins(14, 10, 14, 12); lay.setSpacing(8)
        for i, h in enumerate(report["hit"]):
            block = QVBoxLayout(); block.setSpacing(2)
            line = QHBoxLayout(); line.setSpacing(10)
            if h["dice"]:
                sign = "" if i == 0 else "− " if h["dice"].startswith("-") else "+ "
                left = f"{sign}{h['dice'].lstrip('-')} {h['type']}".strip()
                line.addWidget(self._label(left, t["FS_BODY"], t["TEXT"], True), 1)
                src = self._label(h["source"], t["FS_SMALL"], t["TEXT2"])
                src.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                line.addWidget(src, 0)
            else:
                line.addWidget(self._label(h["source"], t["FS_BODY"], t["TEXT"], True), 1)
            block.addLayout(line)
            if h.get("note"):
                block.addWidget(self._label(h["note"], t["FS_SMALL"], t["TEXT2"]))
            lay.addLayout(block)
        if report.get("attacks"):
            lay.addWidget(self._label(report["attacks"], t["FS_SMALL"], t["TEXT2"]))
        return card

    def _block_head(self, o):
        """The name over a block of choices (Divine Smite), and its note."""
        t = self._t
        head = QVBoxLayout(); head.setSpacing(1); head.setContentsMargins(2, 4, 0, 0)
        head.addWidget(self._label(o["head"], t["FS_BODY"], t["TEXT"], True))
        if o.get("head_note"):
            head.addWidget(self._label(o["head_note"], t["FS_SMALL"], t["TEXT2"]))
        return head

    # ── picking ───────────────────────────────────────────────────────────
    def _changed(self, row):
        # one choice per group (one Divine Smite slot); a "needs" row only
        # counts with its group picked (undead or fiend)
        if row is not None and row.box.isChecked() and row.opt.get("group"):
            for other in self._rows:
                if other is not row and other.opt.get("group") == row.opt["group"]:
                    other.box.blockSignals(True); other.box.setChecked(False); other.box.blockSignals(False)
                    other._paint()
        picked_groups = {r.opt.get("group") for r in self._rows if r.box.isChecked() and r.opt.get("group")}
        for r in self._rows:
            need = r.opt.get("needs")
            if need:
                ok = need in picked_groups
                if not ok and r.box.isChecked():
                    r.box.blockSignals(True); r.box.setChecked(False); r.box.blockSignals(False)
                r.setEnabled(ok)

    def ticked(self):
        return [r.opt["key"] for r in self._rows if r.box.isChecked() and r.isEnabled()]

    def _hit(self):
        self.hit = True
        self.accept()

    def _missed(self):
        # a critical hit can't miss: its left button is Cancel
        if self._crit:
            self.reject()
            return
        self.hit = False
        self.accept()
