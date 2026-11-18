"""
The new-character wizard (desktop).

Six steps, each laid out from core/wizard_flow.py (Android's wizard reads
the same module):
  1. Race                 the race browser, its details on the right half
  2. Abilities            the method as tabs, one card of six abilities
  3. Class & Background   name and alignment, the classes as tiles, the
                          background browser on the right half
  4. Spells & Choices     what level 1 asks you to pick, and your starting
                          spells ("Choices" for a class with none; skipped
                          when there's nothing to pick)
  5. Equipment            each A or B pick, and what you'll start with
  6. Summary              the whole character, an edit button on each card

What you pick lives in self.state; the character is rebuilt from it on the
way into each step (_built), so going back and changing something never
leaves an earlier pick behind.

Author: Ethan O'Brien
Date: 2026-08-20
"""
import copy

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from dnd_app.ui_desktop.style.theme import *
from ..shared import *
from dnd_app.core.character import new_character
from dnd_app.core import wizard_flow as W
from dnd_app.core.builder import ABILITIES
from dnd_app.ui_desktop import icons as _icons

ALIGNMENTS = W.ALIGNMENTS

_lbl = h


def _fresh_state() -> dict:
    return {
        "race": "", "sub": "", "rpicks": {}, "race_search": "", "race_group": "All",
        "method": "Standard Array", "base": W.start_scores("Standard Array"), "picks": {}, "moved": None,
        "name": "", "alignment": "True Neutral", "cls": "", "bg": "", "bg_feat": "", "bg_search": "",
        "l1_picks": {}, "spells": {}, "spell_tab": "cantrips", "spell_search": "", "spell_school": "",
        "equip": None, "equip_cls": "", "extra": "",
    }


# ═══════════════════════════════════════════════════════════════════
#  Small pieces
# ═══════════════════════════════════════════════════════════════════
def _t(text, color=None, size=None, bold=False, wrap=False, align=Qt.AlignLeft, spacing=False):
    l = QLabel(text)
    l.setWordWrap(wrap)
    if not (align & Qt.AlignVertical_Mask):
        align = align | Qt.AlignVCenter
    l.setAlignment(align)
    l.setAttribute(Qt.WA_TransparentForMouseEvents)
    l.setStyleSheet(f"QLabel{{color:{color or TEXT};font-size:{size or FS_BODY}px;"
                    f"font-weight:{800 if bold == 'x' else (700 if bold else 400)};"
                    f"{'letter-spacing:0.5px;' if spacing else ''}background:transparent;border:none;}}")
    return l


def _head(title, sub="", right=None):
    """A card's heading: GOLD CAPS, a quieter line beside it, and whatever
    sits on its right (a count, an edit button)."""
    w = QWidget(); w.setObjectName("wizHead"); w.setStyleSheet("#wizHead{background:transparent;}")
    l = QHBoxLayout(w); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(8)
    l.addWidget(_t(title.upper(), GOLD, FS_SMALL, bold="x", spacing=True))
    if sub:
        s = _t(sub, TEXT3, FS_SMALL)
        s.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        l.addWidget(s, 1)
    else:
        l.addStretch(1)
    if right is not None:
        l.addWidget(right)
    return w


def _count(text, ok):
    c = TEAL2 if ok else GOLD2
    l = QLabel(text)
    l.setObjectName("wizCount")
    l.setStyleSheet(f"#wizCount{{color:{c};background:{qa(c, 0x24)};border:none;border-radius:9px;"
                    f"padding:1px 9px;font-size:{FS_SMALL - 1}px;font-weight:800;}}")
    return l


def _card(name="wizCard", pad=(14, 11, 14, 12)):
    f = QFrame(); f.setObjectName(name)
    f.setStyleSheet(f"#{name}{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
    lay = QVBoxLayout(f); lay.setContentsMargins(*pad); lay.setSpacing(8)
    return f, lay


def _chip(text, kind="", height=26):
    col = {"teal": TEAL2, "gold": GOLD2, "off": TEXT3}.get(kind, IND2)
    l = QLabel(text); l.setObjectName("wizChip")
    l.setAlignment(Qt.AlignCenter)
    l.setFixedHeight(height)
    l.setStyleSheet(f"#wizChip{{color:{col};background:{qa(col, 0x1c)};border:1px solid {qa(col, 0x90)};"
                    f"border-radius:6px;padding:0 10px;font-size:{FS_SMALL - 1}px;font-weight:700;}}")
    return l


def _red_chip(text, height=24):
    l = _chip(text, "", height)
    l.setStyleSheet(f"#wizChip{{color:{CRIM2};background:{qa(CRIMSON, 0x1c)};border:1px solid {qa(CRIMSON, 0x90)};"
                    f"border-radius:6px;padding:0 10px;font-size:{FS_SMALL - 1}px;font-weight:700;}}")
    return l


def _chip_grid(chips, cols, height=28):
    """Chips in even columns, filling the width."""
    w = QWidget(); w.setObjectName("wizChipGrid"); w.setStyleSheet("#wizChipGrid{background:transparent;}")
    g = QGridLayout(w); g.setContentsMargins(0, 0, 0, 0); g.setSpacing(6)
    for i, (text, kind) in enumerate(chips):
        g.addWidget(_chip(text, kind, height), i // cols, i % cols)
    for c in range(cols):
        g.setColumnStretch(c, 1)
    return w


def _field_qss(name):
    return (f"#{name}{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;color:{TEXT};"
            f"padding:0 12px;font-size:{FS_BODY}px;min-height:36px;max-height:36px;}}"
            f"#{name}:focus{{border-color:{INDIGO};}}")


def _search(placeholder, text, on_change, name="wizSearch"):
    e = QLineEdit(); e.setObjectName(name)
    e.setPlaceholderText("⌕  " + placeholder)
    e.setText(text)
    e.setStyleSheet(_field_qss(name))
    e.textChanged.connect(on_change)
    return e


class Tile(QPushButton):
    """A pick: its name and a short second line; on (teal, ✓), off, or
    one you already have (dashed, its reason on hover)."""

    def __init__(self, label, sub="", state="", tip="", height=34, parent=None):
        super().__init__(parent)
        self.setObjectName("wizTile")
        self.setCursor(Qt.PointingHandCursor if state != "have" else Qt.ArrowCursor)
        self.setProperty("tileLabel", label)
        self.setProperty("tileState", state)
        lay = QVBoxLayout(self); lay.setContentsMargins(6, 2, 6, 2); lay.setSpacing(0)
        on = state == "on"
        col = TEAL2 if on else (TEXT3 if state == "have" else TEXT2)
        lay.addWidget(_t(("✓ " if on else "") + label, col, FS_SMALL, bold=True, align=Qt.AlignCenter))
        if sub:
            lay.addWidget(_t(sub, TEAL2 if on else TEXT3, FS_SMALL - 2, align=Qt.AlignCenter))
            height = max(height, 42)
        self._h = height
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if on:
            qss = f"#wizTile{{background:{qa(TEAL, 0x24)};border:1px solid {TEAL};border-radius:7px;}}"
        elif state == "have":
            qss = f"#wizTile{{background:transparent;border:1px dashed {BORDER2};border-radius:7px;}}"
        else:
            qss = (f"#wizTile{{background:{SURF2};border:1px solid {BORDER};border-radius:7px;}}"
                   f"#wizTile:hover{{border-color:{BORDER2};background:{SURF3};}}")
        self.setStyleSheet(qss + f"#wizTile{{min-height:{height}px;padding:0px;}}")
        if tip:
            self.setToolTip(tip)


def _tile_grid(tiles, cols, fill=False):
    w = QWidget(); w.setObjectName("wizTiles"); w.setStyleSheet("#wizTiles{background:transparent;}")
    g = QGridLayout(w); g.setContentsMargins(0, 0, 0, 0); g.setSpacing(6)
    cols = max(1, cols)
    for i, t in enumerate(tiles):
        g.addWidget(t, i // cols, i % cols)
    for c in range(cols):
        g.setColumnStretch(c, 1)
    if fill:
        for r in range((len(tiles) + cols - 1) // cols):
            g.setRowStretch(r, 1)
    return w


class Row(QFrame):
    """A browser row: its name, quieter details and a source tag."""
    clicked = Signal()

    def __init__(self, name, metas=(), tag="", selected=False, height=38, parent=None):
        super().__init__(parent)
        self.setObjectName("wizRow")
        self.setProperty("rowName", name)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(height)
        lay = QHBoxLayout(self); lay.setContentsMargins(12, 0, 10, 0); lay.setSpacing(10)
        lay.addWidget(_t(name, TEAL2 if selected else TEXT, FS_BODY - 1, bold=True), 1)
        for m in metas:
            if m:
                lay.addWidget(_t(m, TEXT2, FS_SMALL - 1))
        if tag:
            tg = QLabel(tag); tg.setObjectName("wizTag"); tg.setFixedHeight(20); tg.setAlignment(Qt.AlignCenter)
            tg.setStyleSheet(f"#wizTag{{color:{GOLD2};background:{qa(GOLD, 0x1c)};border:1px solid {qa(GOLD, 0x80)};"
                             f"border-radius:5px;padding:0 7px;font-size:{FS_TINY}px;font-weight:800;}}")
            lay.addWidget(tg)
        if selected:
            self.setStyleSheet(f"#wizRow{{background:{qa(TEAL, 0x1f)};border:1px solid {TEAL};border-radius:8px;}}")
        else:
            self.setStyleSheet(f"#wizRow{{background:{SURF};border:1px solid {BORDER};border-radius:8px;}}"
                               f"#wizRow:hover{{border-color:{BORDER2};}}")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


def _seg(options, current, on_pick, name="wizSeg", counts=None):
    """Tabs in a row (a method, Cantrips / 1st level)."""
    w = QWidget(); w.setObjectName(name); w.setStyleSheet(f"#{name}{{background:transparent;}}")
    l = QHBoxLayout(w); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(6)
    for opt in options:
        b = QPushButton(); b.setObjectName("wizSegBtn"); b.setCursor(Qt.PointingHandCursor)
        b.setProperty("segName", opt)
        bl = QHBoxLayout(b); bl.setContentsMargins(10, 0, 10, 0); bl.setSpacing(8)
        bl.addStretch(1)
        on = opt == current
        bl.addWidget(_t(opt, GOLD2 if on else TEXT2, FS_SMALL + 1, bold=True))
        if counts and opt in counts:
            txt, ok = counts[opt]
            bl.addWidget(_count(txt, ok))
        bl.addStretch(1)
        b.setStyleSheet(
            (f"#wizSegBtn{{background:{qa(GOLD, 0x1c)};border:1px solid {GOLD};border-radius:8px;"
             if on else
             f"#wizSegBtn{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;")
            + "min-height:38px;max-height:38px;padding:0px;}"
            + (f"#wizSegBtn:hover{{border-color:{BORDER2};}}" if not on else ""))
        b.clicked.connect(lambda _=False, o=opt: on_pick(o))
        l.addWidget(b, 1)
    return w


def _clear(lay):
    while lay.count():
        it = lay.takeAt(0)
        w = it.widget()
        if w is not None:
            w.setParent(None); w.deleteLater()
        elif it.layout() is not None:
            _clear(it.layout())


def _scroll(inner, name="wizScroll"):
    s = QScrollArea(); s.setObjectName(name); s.setWidgetResizable(True)
    s.setFrameShape(QFrame.NoFrame)
    s.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    s.setStyleSheet(f"#{name}{{background:transparent;border:none;}}")
    inner.setObjectName(name + "In"); inner.setStyleSheet(f"#{name}In{{background:transparent;}}")
    s.setWidget(inner)
    return s


def _small_btn(text, name="wizSmallBtn", color=None):
    b = QPushButton(text); b.setObjectName(name); b.setCursor(Qt.PointingHandCursor)
    c = color or IND2
    b.setStyleSheet(f"#{name}{{color:{c};background:transparent;border:1px solid {BORDER2};border-radius:6px;"
                    f"font-size:{FS_SMALL - 1}px;font-weight:700;padding:0 9px;min-height:24px;max-height:24px;}}"
                    f"#{name}:hover{{background:{qa(c, 0x22)};}}")
    return b


def _box(name, bg=None, border=None, radius=8, dashed=False):
    f = QFrame(); f.setObjectName(name)
    f.setStyleSheet(f"#{name}{{background:{bg or SURF2};border:1px {'dashed' if dashed else 'solid'} {border or BORDER};"
                    f"border-radius:{radius}px;}}")
    return f


# ═══════════════════════════════════════════════════════════════════
#  The steps bar
# ═══════════════════════════════════════════════════════════════════
class StepsBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("wizSteps"); self.setStyleSheet("#wizSteps{background:transparent;}")
        self._lay = QHBoxLayout(self); self._lay.setContentsMargins(0, 0, 0, 0); self._lay.setSpacing(0)

    def show_steps(self, names, current, values):
        _clear(self._lay)
        for i, name in enumerate(names):
            if i:
                ln = QFrame(); ln.setFixedSize(12, 2)
                ln.setStyleSheet(f"background:{TEAL if i <= current else BORDER};border:none;")
                self._lay.addWidget(ln, 0, Qt.AlignVCenter)
            done, on = i < current, i == current
            pill = QFrame(); pill.setObjectName("wizStep")
            pill.setProperty("stepName", name)
            bc = TEAL if done else (GOLD if on else BORDER)
            bg = qa(GOLD, 0x14) if on else SURF
            pill.setStyleSheet(f"#wizStep{{background:{bg};border:1px solid {qa(bc, 0xa0) if done else bc};border-radius:10px;}}")
            pill.setFixedHeight(46)
            pl = QHBoxLayout(pill); pl.setContentsMargins(6, 0, 10, 0); pl.setSpacing(7)
            dot = QLabel("✓" if done else str(i + 1)); dot.setObjectName("wizStepDot")
            dot.setAlignment(Qt.AlignCenter); dot.setFixedSize(28, 28)
            dc, dfg = ((qa(TEAL, 0x33), TEAL2) if done else ((GOLD, "#1a1405") if on else (SURF3, TEXT2)))
            dot.setStyleSheet(f"#wizStepDot{{background:{dc};color:{dfg};border-radius:14px;font-weight:800;"
                              f"font-size:{FS_SMALL}px;border:none;}}")
            pl.addWidget(dot)
            col = QVBoxLayout(); col.setSpacing(0); col.setContentsMargins(0, 0, 0, 0)
            col.addWidget(_t(name, GOLD2 if on else (TEXT2 if not done else TEXT), FS_SMALL, bold=True))
            v = values[i] if i < len(values) else ""
            if done and v:
                col.addWidget(_t(v, TEAL2, FS_SMALL - 2))
            elif on:
                col.addWidget(_t("choosing…", TEXT3, FS_SMALL - 2))
            pl.addLayout(col)
            self._lay.addWidget(pill)


# ═══════════════════════════════════════════════════════════════════
#  WIZARD
# ═══════════════════════════════════════════════════════════════════
class CharacterWizard(QWidget):
    """Drives the creation flow; emits 'done' with the finished character."""
    done = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self.char = new_character()
        self.state = _fresh_state()
        self._step = 0
        self._build_ui()
        self._show()

    # ── frame ────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        header = QFrame(); header.setObjectName("wizHeader")
        header.setStyleSheet(f"#wizHeader{{background:{BG};border-bottom:1px solid {BORDER2};}}")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header); hl.setContentsMargins(22, 0, 16, 0); hl.setSpacing(12)
        hl.addWidget(_icons.icon_label("combat", 26))
        hl.addWidget(_t("New Character", TEXT, FS_TITLE - 1, bold="x"))
        hl.addStretch(1)
        self._bar = StepsBar(); hl.addWidget(self._bar)
        root.addWidget(header)

        self._page_host = QWidget(); self._page_host.setObjectName("wizPage")
        self._page_host.setStyleSheet(f"#wizPage{{background:{BG};}}")
        self._page = QVBoxLayout(self._page_host); self._page.setContentsMargins(16, 14, 16, 14); self._page.setSpacing(0)
        root.addWidget(self._page_host, 1)

        nav = QFrame(); nav.setObjectName("wizNav")
        nav.setStyleSheet(f"#wizNav{{background:{SURF};border-top:1px solid {BORDER2};}}")
        nav.setFixedHeight(72)
        nl = QHBoxLayout(nav); nl.setContentsMargins(22, 0, 22, 0); nl.setSpacing(14)
        self._back_btn = QPushButton("← Back"); self._back_btn.setObjectName("wizBack")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setStyleSheet(f"#wizBack{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;color:{TEXT};"
                                     f"font-weight:700;font-size:{FS_BODY}px;padding:0 22px;min-height:46px;max-height:46px;}}"
                                     f"#wizBack:hover{{border-color:{BORDER2};}}")
        self._back_btn.clicked.connect(self._prev_step)
        nl.addWidget(self._back_btn)
        self._status = QLabel(""); self._status.setObjectName("wizStatus")
        self._status.setTextFormat(Qt.RichText)
        self._status.setStyleSheet(f"#wizStatus{{color:{TEXT2};font-size:{FS_SMALL + 1}px;background:transparent;}}")
        nl.addWidget(self._status, 1)
        self._next_btn = QPushButton("Next →"); self._next_btn.setObjectName("wizNext")
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.clicked.connect(self._next_step)
        nl.addWidget(self._next_btn)
        root.addWidget(nav)

    # kept for older callers
    def _update_pills(self):
        self._show()

    def restore(self, state: dict, step: int):
        """Back where it was (a theme change rebuilds the wizard)."""
        self.state = state
        self._step = step
        self._show()

    # ── the character, rebuilt from the picks ─────────────────────────
    def _built(self, upto: int) -> dict:
        """The character with steps 1..upto applied (0: a fresh one)."""
        s = self.state
        c = new_character()
        if upto >= 1:
            W.commit_race(c, s["race"], s["sub"], s["rpicks"])
        if upto >= 2:
            W.commit_abilities(c, W.bonus_plan(c), s["base"], s["picks"], s["moved"])
        if upto >= 3:
            W.commit_identity(c, s["name"], s["alignment"], s["cls"], s["bg"], s["bg_feat"])
        if upto >= 4:
            base = copy.deepcopy(c)
            W.commit_level1(c, base, s["l1_picks"], W.spell_plan(base), s["spells"])
        return c

    def _has_level1(self) -> bool:
        if not (self.state["cls"] and self.state["bg"]):
            return True
        return W.has_level1_step(self._built(3))

    def _step_names(self):
        names = list(W.STEPS)
        if self.state["cls"] and self.state["bg"] and self._step >= 3:
            if not W.spell_plan(self._built(3)):
                names[3] = "Choices"
        if self._step != 2:
            names[2] = "Class & Bg"
        return names

    def _step_values(self):
        s = self.state
        return [s["race"], "Ready", " · ".join(x for x in (s["cls"], s["bg"]) if x), "Chosen", "Ready", ""]

    # ── navigation ───────────────────────────────────────────────────
    def _block(self) -> str:
        s = self.state
        try:
            if self._step == 0:
                return W.race_block_reason(s["race"], s["sub"], s["rpicks"])
            if self._step == 1:
                return W.abilities_block_reason(s["method"], W.bonus_plan(self._built(1)),
                                                s["base"], s["picks"], s["moved"])
            if self._step == 2:
                return W.identity_block_reason(s["name"], s["cls"], s["bg"], s["bg_feat"])
            if self._step == 3:
                left = self._level1_left()
                return ("Still to pick: " + " · ".join(left)) if left else ""
        except Exception:
            import traceback; traceback.print_exc()
            return ""
        return ""

    def _next_step(self):
        if self._block():
            self._show_status()
            return
        if self._step == 5:
            try:
                c = self._built(4)
                W.finish(c, self._equip_items(), self.state["extra"])
            except Exception:
                self._crash()
                return
            self.char = c
            self.done.emit(c)
            return
        self._step += 1
        if self._step == 3 and not self._has_level1():
            self._step += 1
        self._show()

    def _prev_step(self):
        if self._step == 0:
            return
        self._step -= 1
        if self._step == 3 and not self._has_level1():
            self._step -= 1
        self._show()

    def go_to(self, step: int):
        self._step = step
        self._show()

    def _crash(self):
        import traceback
        from dnd_app.ui_desktop.shared import write_diagnostic_log
        tb = traceback.format_exc()
        log_path = write_diagnostic_log("mimic_crash_log.txt", tb)
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Character Build Failed")
        dlg.setText("Something went wrong finishing your character. The details below "
                    + (f"(also saved to {log_path}) " if log_path else "") + "will help fix this.")
        dlg.setDetailedText(tb)
        dlg.exec()

    # ── drawing ──────────────────────────────────────────────────────
    def _show(self):
        _clear(self._page)
        builders = [self._race_page, self._abilities_page, self._identity_page,
                    self._level1_page, self._equipment_page, self._summary_page]
        try:
            self._page.addWidget(builders[self._step](), 1)
        except Exception:
            import traceback; traceback.print_exc()
        self._bar.show_steps(self._step_names(), self._step, self._step_values())
        self._back_btn.setVisible(self._step > 0)
        self._next_btn.setText("Create Character ✓" if self._step == 5 else "Next →")
        self._show_status()

    def _refresh(self):
        """Redraw the current step, keeping where its lists are scrolled and
        which box has the keyboard."""
        keep = {s.objectName(): s.verticalScrollBar().value()
                for s in self._page_host.findChildren(QScrollArea) if s.objectName()}
        focus = QApplication.focusWidget()
        fname = focus.objectName() if isinstance(focus, QLineEdit) else ""
        fpos = focus.cursorPosition() if isinstance(focus, QLineEdit) else 0
        self._show()
        for s in self._page_host.findChildren(QScrollArea):
            if s.objectName() in keep:
                v = keep[s.objectName()]
                s.verticalScrollBar().setValue(v)
                QTimer.singleShot(0, lambda s=s, v=v: s.verticalScrollBar().setValue(v))
        if fname:
            e = self._page_host.findChild(QLineEdit, fname)
            if e:
                e.setFocus(); e.setCursorPosition(min(fpos, len(e.text())))

    def _show_status(self):
        block = self._block()
        last = self._step == 5
        fill = TEAL if last else GOLD
        if not block:
            self._next_btn.setStyleSheet(
                f"#wizNext{{background:{fill};border:none;border-radius:8px;color:{on_fill(fill)};font-weight:800;"
                f"font-size:{FS_BODY}px;padding:0 24px;min-height:46px;max-height:46px;}}"
                f"#wizNext:hover{{background:{TEAL2 if last else GOLD2};}}")
        else:
            self._next_btn.setStyleSheet(
                f"#wizNext{{background:{qa(GOLD, 0x66)};border:none;border-radius:8px;color:{on_fill(GOLD)};font-weight:800;"
                f"font-size:{FS_BODY}px;padding:0 24px;min-height:46px;max-height:46px;}}")
        self._status.setText(self._status_text(block))

    def _status_text(self, block):
        s = self.state
        if block:
            if self._step == 3:
                return "Still to pick: " + " · ".join(f"<b style='color:{TEXT}'>{x}</b>" for x in self._level1_left())
            return f"<span style='color:{GOLD2}'>{block}</span>"
        if self._step == 0:
            return f"<b style='color:{TEXT}'>{s['race']}</b> selected"
        if self._step == 1:
            picks = [ab for ab in ABILITIES if s["picks"].get(ab)]
            if picks:
                return "Your picks: " + ", ".join(f"<b style='color:{TEXT}'>{ab} +{s['picks'][ab]}</b>" for ab in picks)
            return "Scores set"
        if self._step == 2:
            return f"<b style='color:{TEXT}'>{s['cls']}</b> · <b style='color:{TEXT}'>{s['bg']}</b>"
        if self._step == 3:
            return "All picked"
        if self._step == 4:
            return "Ready to go"
        return "Everything picked"

    def _set(self, key, value):
        self.state[key] = value
        self._refresh()

    # ═══════════════════════════════════════════════════════════════
    #  1. Race
    # ═══════════════════════════════════════════════════════════════
    def _race_page(self):
        s = self.state
        page = QWidget(); page.setObjectName("wizRacePage"); page.setStyleSheet("#wizRacePage{background:transparent;}")
        row = QHBoxLayout(page); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(14)

        left = QVBoxLayout(); left.setSpacing(8)
        left.addWidget(_search("Search races…", s["race_search"], self._race_search, "wizRaceSearch"))
        chips = QHBoxLayout(); chips.setSpacing(6)
        for name, _ in W.SOURCE_GROUPS:
            b = QPushButton(name); b.setObjectName("wizGroup"); b.setCursor(Qt.PointingHandCursor)
            on = s["race_group"] == name
            c = GOLD2 if on else TEXT3
            b.setStyleSheet(f"#wizGroup{{color:{c};background:{qa(GOLD, 0x1c) if on else SURF2};"
                            f"border:1px solid {GOLD if on else BORDER};border-radius:6px;font-size:{FS_SMALL - 1}px;"
                            f"font-weight:700;padding:0 10px;min-height:26px;max-height:26px;}}")
            b.clicked.connect(lambda _=False, n=name: self._set("race_group", n))
            chips.addWidget(b)
        chips.addStretch(1)
        left.addLayout(chips)
        inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 4, 0); il.setSpacing(5)
        for r in W.race_rows(s["race_search"], s["race_group"]):
            rw = Row(r["name"], (r["asi"], r["speed"]), r["source"], r["name"] == s["race"])
            rw.clicked.connect(lambda n=r["name"]: self._pick_race(n))
            il.addWidget(rw)
        il.addStretch(1)
        left.addWidget(_scroll(inner, "wizRaceList"), 1)
        lw = QWidget(); lw.setLayout(left); lw.setObjectName("wizRaceLeft"); lw.setStyleSheet("#wizRaceLeft{background:transparent;}")
        row.addWidget(lw, 1)
        row.addWidget(self._race_details(), 1)
        return page

    def _race_details(self):
        s = self.state
        card, lay = _card("wizRaceCard", (16, 14, 16, 14))
        if not s["race"]:
            lay.addWidget(_t("Pick a race on the left to see what it gives you.", TEXT3, FS_BODY, wrap=True))
            lay.addStretch(1)
            return card
        rc = W.race_card(s["race"], s["sub"])
        top = QHBoxLayout(); top.setSpacing(10)
        top.addWidget(_t(rc["name"], GOLD2, FS_TITLE, bold="x"))
        top.addWidget(_chip(rc["source"], "gold", 22)); top.addStretch(1)
        lay.addLayout(top)
        lay.addWidget(_chip_grid([(c["text"], c["kind"]) for c in rc["chips"]], 3))
        content = QWidget(); cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 4, 0); cl.setSpacing(8)
        if rc["subraces"]:
            cl.addWidget(_head("Subrace", "pick one" if rc["subrace_required"] else "optional"))
            tiles = []
            if rc["subrace_required"] or "Standard" in rc["subraces"]:
                opts = [(n, n) for n in rc["subraces"]]
            else:
                opts = [("Standard", "")] + [(n, n) for n in rc["subraces"]]
            for label, val in opts:
                on = s["sub"] == val
                t = Tile(label, state="on" if on else "", height=36)
                t.clicked.connect(lambda _=False, v=val: self._pick_sub(v))
                tiles.append(t)
            cl.addWidget(_tile_grid(tiles, 4 if len(tiles) > 5 else len(tiles)))
        for key, title, field in (("ancestry", "Draconic ancestry", "ancestry"), ("seasons", "Eladrin season", "season"),
                                  ("simic", "Animal enhancement", "simic")):
            opts = rc.get(key) or []
            if not opts:
                continue
            cl.addWidget(_head(title, "pick one"))
            tiles = []
            for o in opts:
                on = s["rpicks"].get(field) == o["value"]
                short = len(o["sub"]) <= 16
                t = Tile(o["name"], o["sub"] if short else "", "on" if on else "", tip="" if short else o["sub"])
                t.clicked.connect(lambda _=False, f=field, v=o["value"]: self._pick_rextra(f, v))
                tiles.append(t)
            cl.addWidget(_tile_grid(tiles, 5 if len(tiles) >= 5 else len(tiles)))
        cl.addWidget(_head("Traits"))
        for tr in rc["traits"]:
            f = _box("wizTrait")
            fl = QVBoxLayout(f); fl.setContentsMargins(12, 8, 12, 8); fl.setSpacing(2)
            fl.addWidget(_t(tr["name"], TEXT, FS_BODY - 1, bold=True, wrap=True))
            if tr["text"]:
                fl.addWidget(_t(tr["text"], TEXT2, FS_SMALL, wrap=True))
            cl.addWidget(f)
        cl.addStretch(1)
        lay.addWidget(_scroll(content, "wizRaceDetail"), 1)
        return card

    def _race_search(self, text):
        self.state["race_search"] = text
        self._refresh()

    def _pick_race(self, name):
        s = self.state
        if s["race"] != name:
            s.update(race=name, sub="", rpicks={}, picks={}, moved=None, l1_picks={})
        self._refresh()

    def _pick_sub(self, sub):
        s = self.state
        if s["sub"] != sub:
            s.update(sub=sub, picks={}, moved=None, l1_picks={})
            s["rpicks"].pop("ancestry", None); s["rpicks"].pop("season", None)
        self._refresh()

    def _pick_rextra(self, field, value):
        self.state["rpicks"][field] = value
        self._refresh()

    # ═══════════════════════════════════════════════════════════════
    #  2. Abilities
    # ═══════════════════════════════════════════════════════════════
    def _abilities_page(self):
        s = self.state
        plan = W.bonus_plan(self._built(1))
        s["picks"] = {ab: n for ab, n in s["picks"].items() if n and ab not in plan["exclude"]}
        page = QWidget(); page.setObjectName("wizAbPage"); page.setStyleSheet("#wizAbPage{background:transparent;}")
        v = QVBoxLayout(page); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(12)

        mcard, ml = _card("wizMethodCard")
        right = None
        if s["method"] == "Point Buy":
            left = W.point_buy_left(s["base"])
            right = QLabel(f"Point Buy: <b style='color:{TEAL2 if left >= 0 else CRIM2}'>{left}</b> of 27 left")
            right.setObjectName("wizPbLeft")
            right.setStyleSheet(f"#wizPbLeft{{color:{TEXT2};font-size:{FS_SMALL}px;background:transparent;}}")
        elif s["method"] == "Roll":
            right = _small_btn("🎲  Roll all", "wizRollAll", TEAL2)
            right.clicked.connect(self._roll_all)
        ml.addWidget(_head("Method", "", right))
        ml.addWidget(_seg(W.METHODS, s["method"], self._set_method, "wizMethods"))
        v.addWidget(mcard)

        acard, al = _card("wizAbCard", (14, 11, 14, 14))
        mv = None
        if plan["fixed"]:
            mv = _small_btn("Move my race bonus" if s["moved"] is None else "Put my race bonus back",
                            "wizMoveBonus", GOLD2)
            mv.setToolTip("Tasha's: put your race's bonus on different abilities")
            mv.clicked.connect(self._toggle_moved)
        al.addWidget(_head("Ability scores", plan["text"], mv))
        tots = W.totals(plan, s["base"], s["picks"], s["moved"])
        cols = QHBoxLayout(); cols.setSpacing(10)
        for ab in ABILITIES:
            cols.addWidget(self._ability_column(ab, tots[ab], plan), 1)
        al.addLayout(cols)
        v.addWidget(acard)
        v.addStretch(1)
        return page

    def _ability_column(self, ab, t, plan):
        s = self.state
        f = _box("wizAbCol", SURF2, BORDER, 10); f.setProperty("ability", ab)
        l = QVBoxLayout(f); l.setContentsMargins(8, 10, 8, 10); l.setSpacing(6)
        l.addWidget(_t(ab, TEXT2, FS_SMALL - 1, bold="x", align=Qt.AlignCenter, spacing=True))
        row = QHBoxLayout(); row.setSpacing(6); row.addStretch(1)
        num = _t(str(t["base"]), TEXT, FS_HEAD + 2, bold="x", align=Qt.AlignCenter)
        num.setObjectName(f"wizBase_{ab}"); num.setMinimumWidth(30)
        if s["method"] == "Roll":
            row.addWidget(num)
            d = _small_btn("🎲", f"wizRoll_{ab}", TEAL2)
            d.setToolTip(f"Roll {ab} again (4d6, the lowest dropped)")
            d.clicked.connect(lambda _=False, a=ab: self._roll_one(a))
            row.addWidget(d)
        else:
            for up in (False, None, True):
                if up is None:
                    row.addWidget(num)
                    continue
                nm = f"wizStep_{ab}_{'up' if up else 'down'}"
                b = QPushButton("+" if up else "−"); b.setObjectName(nm)
                b.setCursor(Qt.PointingHandCursor); b.setFixedSize(30, 30)
                b.setStyleSheet(f"#{nm}{{background:{SURF};border:1px solid {BORDER};border-radius:7px;"
                                f"color:{TEXT};font-weight:800;font-size:{FS_BODY}px;padding:0;min-height:0px;}}"
                                f"#{nm}:hover{{border-color:{BORDER2};background:{SURF3};}}")
                b.clicked.connect(lambda _=False, a=ab, u=up: self._step_score(a, u))
                row.addWidget(b)
        row.addStretch(1)
        l.addLayout(row)
        l.addWidget(_t("base", TEXT3, FS_SMALL - 2, align=Qt.AlignCenter))
        # the race's bonus here, or the +1 you place here
        br = QHBoxLayout(); br.setSpacing(4); br.addStretch(1)
        n0 = 0
        if s["moved"] is not None and plan["fixed"]:
            m = s["moved"].get(ab, 0)
            for d in (-1, 0, 1):
                if d == 0:
                    br.addWidget(_chip(f"+{m} race" if m else "race", "teal" if m else "off", 24))
                    continue
                nm = f"wizMove_{ab}_{'up' if d > 0 else 'down'}"
                b = QPushButton("+" if d > 0 else "−"); b.setObjectName(nm)
                b.setFixedSize(24, 24); b.setCursor(Qt.PointingHandCursor)
                b.setStyleSheet(f"#{nm}{{background:transparent;border:1px solid {BORDER};border-radius:6px;"
                                f"color:{TEXT2};font-weight:800;padding:0;min-height:0px;}}")
                b.clicked.connect(lambda _=False, a=ab, dd=d: self._move_bonus(a, dd))
                br.addWidget(b)
            n0 = 1
        elif t["fixed"]:
            br.addWidget(_chip(f"+{t['fixed']} race", "teal", 24)); n0 = 1
        if plan["points"] and ab not in plan["exclude"]:
            p = t["pick"]
            nm = f"wizPick_{ab}"
            tb = QPushButton(f"✓ +{p}" if p else "+1"); tb.setObjectName(nm)
            tb.setCursor(Qt.PointingHandCursor); tb.setFixedHeight(24)
            c = TEAL2 if p else TEXT3
            tb.setStyleSheet(f"#{nm}{{color:{c};background:{qa(TEAL, 0x24) if p else 'transparent'};"
                             f"border:1px solid {TEAL if p else BORDER2};border-radius:6px;font-size:{FS_SMALL - 1}px;"
                             f"font-weight:800;padding:0 9px;min-height:0px;}}")
            tb.setToolTip("Tap to place your race's +1 here")
            tb.clicked.connect(lambda _=False, a=ab: self._tap_pick(a))
            br.addWidget(tb); n0 = 1
        if not n0:
            sp = QWidget(); sp.setFixedHeight(24); br.addWidget(sp)
        br.addStretch(1)
        l.addLayout(br)
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background:{BORDER};border:none;")
        l.addWidget(line)
        tot = _t(str(t["total"]), TEAL2 if t["bonus"] else TEXT, FS_STAT + 4, bold="x", align=Qt.AlignCenter)
        tot.setObjectName(f"wizTotal_{ab}")
        l.addWidget(tot)
        mc = QHBoxLayout(); mc.addStretch(1)
        mc.addWidget(_red_chip(t["mod"]) if t["mod"].startswith("-") else _chip(t["mod"], "teal", 24))
        mc.addStretch(1)
        l.addLayout(mc)
        return f

    def _set_method(self, m):
        s = self.state
        if s["method"] != m:
            s["method"] = m
            s["base"] = W.start_scores(m)
        self._refresh()

    def _step_score(self, ab, up):
        s = self.state
        s["base"] = W.step_score(s["method"], s["base"], ab, up)
        self._refresh()

    def _roll_all(self):
        self.state["base"] = W.start_scores("Roll")
        self._refresh()

    def _roll_one(self, ab):
        self.state["base"] = dict(self.state["base"], **{ab: W.roll_score()})
        self._refresh()

    def _tap_pick(self, ab):
        plan = W.bonus_plan(self._built(1))
        self.state["picks"] = W.next_pick(plan, self.state["picks"], ab)
        self._refresh()

    def _toggle_moved(self):
        s = self.state
        s["moved"] = dict(W.bonus_plan(self._built(1))["fixed"]) if s["moved"] is None else None
        self._refresh()

    def _move_bonus(self, ab, d):
        s = self.state
        need = sum(W.bonus_plan(self._built(1))["fixed"].values())
        cur = dict(s["moved"] or {})
        nv = cur.get(ab, 0) + d
        if nv < 0 or nv > 2 or (d > 0 and sum(cur.values()) >= need):
            return
        cur[ab] = nv
        s["moved"] = {k: v for k, v in cur.items() if v}
        self._refresh()

    # ═══════════════════════════════════════════════════════════════
    #  3. Class & Background
    # ═══════════════════════════════════════════════════════════════
    def _identity_page(self):
        s = self.state
        page = QWidget(); page.setObjectName("wizIdPage"); page.setStyleSheet("#wizIdPage{background:transparent;}")
        row = QHBoxLayout(page); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(14)
        left = QVBoxLayout(); left.setSpacing(12)

        who, wl = _card("wizWhoCard")
        wl.addWidget(_head("Who"))
        r = QHBoxLayout(); r.setSpacing(10)
        name = QLineEdit(s["name"]); name.setObjectName("wizName"); name.setPlaceholderText("Character name")
        name.setStyleSheet(_field_qss("wizName"))
        name.textChanged.connect(self._set_name)
        r.addWidget(name, 3)
        al = QComboBox(); al.setObjectName("wizAlign"); al.addItems(ALIGNMENTS)
        al.setCurrentText(s["alignment"])
        al.currentTextChanged.connect(lambda t: self.state.__setitem__("alignment", t))
        r.addWidget(al, 2)
        wl.addLayout(r)
        left.addWidget(who)

        ccard, cl = _card("wizClassCard")
        cl.addWidget(_head("Class", "you start at level 1"))
        tiles = []
        for ct in W.class_tiles():
            on = ct["name"] == s["cls"]
            t = Tile(ct["name"], f"{ct['hit_die']} · {ct['main']}", "on" if on else "", height=46)
            t.clicked.connect(lambda _=False, n=ct["name"]: self._pick_class(n))
            tiles.append(t)
        cl.addWidget(_tile_grid(tiles, 4))
        if s["cls"]:
            cl.addWidget(_chip_grid([(c, "") for c in W.class_chips(s["cls"])], 4))
        cl.addStretch(1)
        left.addWidget(ccard, 1)
        lw = QWidget(); lw.setObjectName("wizIdLeft"); lw.setStyleSheet("#wizIdLeft{background:transparent;}"); lw.setLayout(left)
        row.addWidget(lw, 1)

        right = QVBoxLayout(); right.setSpacing(8)
        right.addWidget(_search("Search backgrounds…", s["bg_search"], self._bg_search, "wizBgSearch"))
        inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 4, 0); il.setSpacing(5)
        for b in W.background_rows(s["bg_search"]):
            rw = Row(b["name"], (b["skills"],), b["source"], b["name"] == s["bg"], height=36)
            rw.clicked.connect(lambda n=b["name"]: self._pick_bg(n))
            il.addWidget(rw)
        il.addStretch(1)
        right.addWidget(_scroll(inner, "wizBgList"), 1)
        if s["bg"]:
            right.addWidget(self._bg_card())
        rw_ = QWidget(); rw_.setObjectName("wizIdRight"); rw_.setStyleSheet("#wizIdRight{background:transparent;}"); rw_.setLayout(right)
        row.addWidget(rw_, 1)
        return page

    def _bg_card(self):
        s = self.state
        bc = W.background_card(s["bg"])
        card, lay = _card("wizBgCard", (16, 12, 16, 12))
        top = QHBoxLayout(); top.setSpacing(8)
        top.addWidget(_t(bc["name"], GOLD2, FS_HEAD, bold="x"))
        if bc["source"]:
            top.addWidget(_chip(bc["source"], "gold", 22))
        top.addStretch(1)
        for c in bc["chips"][:4]:
            top.addWidget(_chip(c["text"], c["kind"], 24))
        lay.addLayout(top)
        if bc["feature"]:
            f = _box("wizTrait")
            fl = QVBoxLayout(f); fl.setContentsMargins(12, 8, 12, 8); fl.setSpacing(2)
            fl.addWidget(_t(bc["feature"], TEXT, FS_BODY - 1, bold=True, wrap=True))
            if bc["text"]:
                fl.addWidget(_t(bc["text"], TEXT2, FS_SMALL, wrap=True))
            lay.addWidget(f)
        if bc["feats"]:
            lay.addWidget(_head("Feat", f"{bc['name']} gives you one"))
            tiles = []
            for n in bc["feats"]:
                t = Tile(n, state="on" if s["bg_feat"] == n else "")
                t.clicked.connect(lambda _=False, v=n: self._set("bg_feat", v))
                tiles.append(t)
            lay.addWidget(_tile_grid(tiles, min(4, len(tiles))))
        if bc["gear"]:
            lay.addWidget(_t(bc["gear"], TEXT3, FS_SMALL, wrap=True))
        return card

    def _set_name(self, t):
        self.state["name"] = t
        self._show_status()

    def _pick_class(self, n):
        s = self.state
        if s["cls"] != n:
            s.update(cls=n, l1_picks={}, spells={}, equip=None)
        self._refresh()

    def _bg_search(self, t):
        self.state["bg_search"] = t
        self._refresh()

    def _pick_bg(self, n):
        s = self.state
        if s["bg"] != n:
            s.update(bg=n, bg_feat="")
        self._refresh()

    # ═══════════════════════════════════════════════════════════════
    #  4. Spells & Choices
    # ═══════════════════════════════════════════════════════════════
    def _level1_data(self):
        s = self.state
        base = self._built(3)
        cards = W.level1_cards(base, s["l1_picks"])
        tidy = W.tidy_picks(cards, s["l1_picks"])
        if tidy != s["l1_picks"]:
            s["l1_picks"] = tidy
            cards = W.level1_cards(base, tidy)
        plan = W.spell_plan(base)
        keep = {}
        for t in plan.get("tabs", []):
            ok = {r["name"] for r in W.spell_rows(t)}
            keep[t["key"]] = [n for n in s["spells"].get(t["key"], []) if n in ok][:t["count"]]
        s["spells"] = keep
        return base, cards, plan

    def _level1_left(self):
        try:
            _, cards, plan = self._level1_data()
        except Exception:
            import traceback; traceback.print_exc()
            return []
        return W.level1_left(cards, plan, self.state["spells"])

    def _level1_page(self):
        base, cards, plan = self._level1_data()
        page = QWidget(); page.setObjectName("wizL1Page"); page.setStyleSheet("#wizL1Page{background:transparent;}")
        row = QHBoxLayout(page); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(14)
        mains = [c for c in cards if not c["parent"]]
        if plan:
            inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 4, 0); il.setSpacing(8)
            for c in mains:
                il.addWidget(self._choice_card(c, cards))
            il.addStretch(1)
            row.addWidget(_scroll(inner, "wizChoices"), 1)
            row.addWidget(self._spells_card(plan), 1)
        else:
            # no spells: the cards at their usual width, centred, filling the
            # height -- each as tall as its rows, so every tile is the same.
            # More than fits scrolls instead, at the tiles' own height.
            def rows_of(c):
                return 1 if c["big"] else (len(c["tiles"]) + c["cols"] - 1) // c["cols"]
            need = sum(46 + rows_of(c) * 48 for c in mains) + 8 * len(mains)
            room = max(400, self._page_host.height() - 28) if self._page_host.height() > 100 else 600
            fill = need <= room
            col = QVBoxLayout(); col.setSpacing(8); col.setContentsMargins(0, 0, 4 if not fill else 0, 0)
            for c in mains:
                col.addWidget(self._choice_card(c, cards, fill=fill), rows_of(c) * 4 + 1 if fill else 0)
            if not fill:
                col.addStretch(1)
            holder = QWidget(); holder.setObjectName("wizL1Col"); holder.setStyleSheet("#wizL1Col{background:transparent;}")
            holder.setLayout(col)
            width = max(560, (self.width() - 46) // 2) if self.width() > 600 else 617
            row.addStretch(1)
            if fill:
                holder.setFixedWidth(width)
                row.addWidget(holder, 0)
            else:
                sc = _scroll(holder, "wizChoices")
                sc.setFixedWidth(width + 10)
                row.addWidget(sc, 0)
            row.addStretch(1)
        return page

    def _choice_card(self, c, cards, fill=False, inner=False):
        name = "wizChoiceInner" if inner else "wizChoice"
        f = _box(name, SURF2 if inner else SURF, BORDER, 8 if inner else 10)
        f.setProperty("choiceId", c["id"])
        lay = QVBoxLayout(f); lay.setContentsMargins(12, 9, 12, 11); lay.setSpacing(7)
        done = not c["left"]
        if inner:
            hw = QWidget(); hw.setObjectName("wizHead"); hw.setStyleSheet("#wizHead{background:transparent;}")
            hl = QHBoxLayout(hw); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(8)
            hl.addWidget(_t(c["title"], TEXT, FS_BODY - 1, bold=True))
            hl.addWidget(_count("picked" if done else "pick one" if c["count"] == 1 else f"pick {c['count']}", done))
            hl.addStretch(1)
            lay.addWidget(hw)
        else:
            lay.addWidget(_head(c["title"], c["sub"], _count(f"{len(c['picked'])} of {c['count']}", done)))
        tiles = []
        if c["big"]:
            for v in c["picked"]:
                t = next((x for x in c["tiles"] if x["value"] == v), {"label": v})
                tt = Tile(t["label"], "", "on")
                tt.clicked.connect(lambda _=False, i=c["id"], val=v: self._toggle_choice(i, val))
                tiles.append(tt)
            if c["left"]:
                add = Tile("＋ pick" + (" another" if c["picked"] else ""), height=34)
                add.setProperty("pickMore", c["id"])
                add.clicked.connect(lambda _=False, cc=c: self._pick_from_list(cc))
                tiles.append(add)
            cols = 3
        else:
            for t in c["tiles"]:
                state = "have" if t["have"] else ("on" if t["value"] in c["picked"] else "")
                tip = ""
                if t["have"]:
                    tip = (f"<b style='color:{GOLD2}'>You already have {t['label']}</b><br>"
                           f"from {t['have']}")
                elif t.get("tip"):
                    tip = t["tip"]
                tt = Tile(t["label"], t["sub"], state, tip)
                if not t["have"]:
                    tt.clicked.connect(lambda _=False, i=c["id"], val=t["value"]: self._toggle_choice(i, val))
                tiles.append(tt)
            cols = c["cols"]
        lay.addWidget(_tile_grid(tiles, cols, fill), 1 if fill else 0)
        for kid in cards:
            if kid["parent"] == c["id"]:
                lay.addWidget(self._choice_card(kid, cards, inner=True))
        return f

    def _toggle_choice(self, cid, value):
        _, cards, _ = self._level1_data()
        self.state["l1_picks"] = W.toggle_pick(cards, self.state["l1_picks"], cid, value)
        self._refresh()

    def _pick_from_list(self, card):
        dlg = QDialog(self); dlg.setWindowTitle(card["title"])
        dlg.setObjectName("wizPicker")
        dlg.setStyleSheet(f"#wizPicker{{background:{SURF};}}")
        dlg.resize(380, 460)
        v = QVBoxLayout(dlg); v.setContentsMargins(14, 14, 14, 14); v.setSpacing(8)
        v.addWidget(_t(f"{card['title']}: {card['sub']}", GOLD2, FS_BODY, bold=True, wrap=True))
        search = QLineEdit(); search.setObjectName("wizPickSearch"); search.setPlaceholderText("⌕  Search…")
        search.setStyleSheet(_field_qss("wizPickSearch"))
        v.addWidget(search)
        lst = QListWidget(); lst.setObjectName("wizPickList")
        lst.setStyleSheet(f"#wizPickList{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;color:{TEXT};"
                          f"font-size:{FS_BODY - 1}px;}}#wizPickList::item{{padding:6px 10px;}}"
                          f"#wizPickList::item:selected{{background:{qa(TEAL, 0x33)};color:{TEAL2};}}")
        for t in card["tiles"]:
            if t["value"] in card["picked"]:
                continue
            it = QListWidgetItem(t["label"] + (f"  (you have it: {t['have']})" if t["have"] else ""))
            it.setData(Qt.UserRole, t["value"])
            if t["have"]:
                it.setFlags(Qt.NoItemFlags)
            lst.addItem(it)
        v.addWidget(lst, 1)
        search.textChanged.connect(lambda q: [lst.item(i).setHidden(q.lower() not in lst.item(i).text().lower())
                                              for i in range(lst.count())])
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lst.itemDoubleClicked.connect(lambda _it: dlg.accept())
        v.addWidget(btns)
        if dlg.exec() == QDialog.Accepted and lst.currentItem() is not None:
            self._toggle_choice(card["id"], lst.currentItem().data(Qt.UserRole))

    def _spells_card(self, plan):
        s = self.state
        card, lay = _card("wizSpellCard")
        lay.addWidget(_head("Starting spells",
                            f"casts with {plan['ability']} · save DC {plan.get('dc')} · {plan.get('attack', 0):+d} to hit"))
        tabs = plan["tabs"]
        if s["spell_tab"] not in [t["key"] for t in tabs]:
            s["spell_tab"] = tabs[0]["key"]
        cur = next(t for t in tabs if t["key"] == s["spell_tab"])
        counts = {t["title"]: (f"{len(s['spells'].get(t['key'], []))} of {t['count']}",
                               len(s["spells"].get(t["key"], [])) >= t["count"]) for t in tabs}
        lay.addWidget(_seg([t["title"] for t in tabs], cur["title"],
                           lambda title: self._set("spell_tab", next(t["key"] for t in tabs if t["title"] == title)),
                           "wizSpellTabs", counts))
        fr = QHBoxLayout(); fr.setSpacing(6)
        what = "cantrips" if cur["key"] == "cantrips" else "spells"
        fr.addWidget(_search(f"Search {plan.get('label', '').lower()} {what}…", s["spell_search"],
                             lambda t: self._set("spell_search", t), "wizSpellSearch"), 1)
        school = QComboBox(); school.setObjectName("wizSchool")
        rows_all = W.spell_rows(cur)
        school.addItem("Any school")
        for sc in sorted({r["school"] for r in rows_all if r["school"]}):
            school.addItem(sc)
        school.setCurrentText(s["spell_school"] or "Any school")
        school.currentTextChanged.connect(lambda t: self._set("spell_school", "" if t == "Any school" else t))
        fr.addWidget(school)
        lay.addLayout(fr)
        inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 4, 0); il.setSpacing(4)
        picked = s["spells"].get(cur["key"], [])
        for r in W.spell_rows(cur, s["spell_search"]):
            if s["spell_school"] and r["school"] != s["spell_school"]:
                continue
            il.addWidget(self._spell_row(r, r["name"] in picked, cur["key"]))
        il.addStretch(1)
        lay.addWidget(_scroll(inner, "wizSpellList"), 1)
        return card

    def _spell_row(self, r, on, key):
        f = Row(r["name"], (), "", on, height=36)
        lay = f.layout()
        box = QLabel("✓" if on else ""); box.setObjectName("wizCheck"); box.setFixedSize(18, 18)
        box.setAlignment(Qt.AlignCenter)
        box.setStyleSheet(f"#wizCheck{{background:{TEAL if on else 'transparent'};border:1px solid {TEAL if on else BORDER2};"
                          f"border-radius:4px;color:{on_fill(TEAL)};font-weight:900;font-size:{FS_SMALL - 1}px;}}")
        lay.insertWidget(0, box)
        if r["conc"]:
            lay.addWidget(_chip("Conc", "off", 20))
        if r["ritual"]:
            lay.addWidget(_chip("Ritual", "off", 20))
        lay.addWidget(_t(r["school"], TEXT3, FS_SMALL - 1))
        tr = _t(f"{r['time']} · {r['range']}", TEXT3, FS_SMALL - 1); tr.setMinimumWidth(130)
        tr.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(tr)
        f.setToolTip(r["desc"])
        f.clicked.connect(lambda k=key, n=r["name"]: self._toggle_spell(k, n))
        return f

    def _toggle_spell(self, key, name):
        plan = W.spell_plan(self._built(3))
        self.state["spells"] = W.toggle_spell(plan, self.state["spells"], key, name)
        self._refresh()

    # ═══════════════════════════════════════════════════════════════
    #  5. Equipment
    # ═══════════════════════════════════════════════════════════════
    def _equip_state(self, groups):
        s = self.state
        if s["equip"] is None or s["equip_cls"] != s["cls"] or len(s["equip"]) != len(groups):
            s["equip"] = W.default_choice(groups)
            s["equip_cls"] = s["cls"]
        return s["equip"]

    def _equip_items(self):
        groups = W.equipment_groups(self.state["cls"])
        return W.resolve_equipment(groups, self._equip_state(groups))

    def _equipment_page(self):
        s = self.state
        c = self._built(4)
        groups = W.equipment_groups(s["cls"])
        choice = self._equip_state(groups)
        page = QWidget(); page.setObjectName("wizEqPage"); page.setStyleSheet("#wizEqPage{background:transparent;}")
        row = QHBoxLayout(page); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(14)
        inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 4, 0); il.setSpacing(8)
        always = []
        for gi, g in enumerate(groups):
            if g["fixed"] and not g["options"][0]["anys"]:
                always += W._count_items(g["options"][0]["items"])
                continue
            il.addWidget(self._equip_group(gi, g, choice[gi]))
        if always:
            card, cl = _card("wizAlways", (12, 9, 12, 11))
            cl.addWidget(_head("Always"))
            cl.addWidget(_chip_grid([(x, "") for x in always], 3, 30))
            il.addWidget(card)
        bgear = W.background_gear(c)
        if bgear:
            card, cl = _card("wizBgGear", (12, 9, 12, 11))
            cl.addWidget(_head(f"From {s['bg']}"))
            cl.addWidget(_chip_grid([(x, "gold") for x in bgear], 4, 30))
            il.addWidget(card)
        il.addStretch(1)
        row.addWidget(_scroll(inner, "wizEquip"), 1)
        row.addWidget(self._kit_card(c), 1)
        return page

    def _equip_group(self, gi, g, sel):
        card, lay = _card("wizEqGroup", (12, 9, 12, 11))
        lay.addWidget(_head(g["title"]))
        grid = QGridLayout(); grid.setSpacing(8)
        letters = "ABCDEFG"
        n = len(g["options"])
        for oi, o in enumerate(g["options"]):
            on = g["fixed"] or sel.get("option", 0) == oi
            f = QPushButton(); f.setObjectName("wizOpt"); f.setCursor(Qt.PointingHandCursor)
            f.setProperty("option", f"{gi}:{oi}")
            outer = QVBoxLayout(f); outer.setContentsMargins(10, 7, 10, 7); outer.setSpacing(5)
            fl = QHBoxLayout(); fl.setSpacing(8)
            outer.addLayout(fl)
            if not g["fixed"]:
                fl.addWidget(_t(letters[oi], TEXT3, FS_SMALL, bold=True))
            fixed = [x for x in o["items"] if not x.lower().startswith("any ")]
            text = ", ".join(W._count_items(fixed + [a_["name"] for a_ in o["anys"]]))
            lbl = _t(text, TEAL2 if on else TEXT, FS_SMALL + 1, bold=True, wrap=True)
            fl.addWidget(lbl, 1)
            for ai, a in enumerate(o["anys"]):
                cb = QComboBox(); cb.setObjectName(f"wizAny_{gi}_{oi}_{ai}")
                cb.addItems(a["pool"])
                anys = sel.get("anys") or []
                if on and ai < len(anys) and anys[ai]:
                    cb.setCurrentText(anys[ai])
                cb.setEnabled(on)
                cb.setFixedHeight(32)
                cb.currentTextChanged.connect(lambda t, gi_=gi, ai_=ai: self._set_any(gi_, ai_, t))
                outer.addWidget(cb)
            tall = 46 + 37 * len(o["anys"]) + (18 if len(text) > 34 else 0)
            f.setStyleSheet((f"#wizOpt{{background:{qa(TEAL, 0x1f)};border:1px solid {TEAL};border-radius:8px;"
                             if on else
                             f"#wizOpt{{background:{SURF};border:1px solid {BORDER};border-radius:8px;")
                            + f"text-align:left;padding:0px;min-height:{tall}px;}}" + f"#wizOpt:hover{{border-color:{TEAL if on else BORDER2};}}")
            if not g["fixed"]:
                f.clicked.connect(lambda _=False, gi_=gi, oi_=oi: self._pick_option(gi_, oi_))
            per = 3 if n == 3 else 2
            grid.addWidget(f, oi // per, oi % per)
        for c in range(3 if n == 3 else 2):
            grid.setColumnStretch(c, 1)
        lay.addLayout(grid)
        return card

    def _pick_option(self, gi, oi):
        groups = W.equipment_groups(self.state["cls"])
        ch = self._equip_state(groups)
        if ch[gi].get("option") != oi:
            ch[gi] = {"option": oi, "anys": [a["pool"][0] if a["pool"] else "" for a in groups[gi]["options"][oi]["anys"]]}
        self._refresh()

    def _set_any(self, gi, ai, text):
        groups = W.equipment_groups(self.state["cls"])
        ch = self._equip_state(groups)
        anys = list(ch[gi].get("anys") or [])
        while len(anys) <= ai:
            anys.append("")
        if anys[ai] == text:
            return
        anys[ai] = text
        ch[gi]["anys"] = anys
        QTimer.singleShot(0, self._refresh)

    def _kit_card(self, c):
        s = self.state
        pv = W.kit_preview(c, self._equip_items(), s["extra"])
        card, lay = _card("wizKit")
        lay.addWidget(_head("You'll start with", "as your Loadout will show it"))
        grid = QGridLayout(); grid.setSpacing(8)
        for i, sl in enumerate(pv["slots"]):
            f = _box("wizSlot", dashed=sl["empty"])
            fl = QVBoxLayout(f); fl.setContentsMargins(10, 7, 10, 7); fl.setSpacing(1)
            fl.addWidget(_t(sl["label"], TEXT3, FS_SMALL - 2, bold="x"))
            fl.addWidget(_t(sl["name"], TEXT3 if sl["empty"] else TEXT, FS_BODY - 1, bold=True))
            if sl["sub"]:
                fl.addWidget(_t(sl["sub"], TEXT2, FS_SMALL - 2))
            grid.addWidget(f, i // 2, i % 2)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        lay.addLayout(grid)
        lay.addWidget(_head("Inventory"))
        inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 4, 0); il.setSpacing(4)
        for r in pv["rows"]:
            rw = Row(r["name"], (f"×{r['qty']}" if r["qty"] > 1 else "",), "", False, height=32)
            rw.setCursor(Qt.ArrowCursor)
            il.addWidget(rw)
        il.addStretch(1)
        lay.addWidget(_scroll(inner, "wizKitList"), 1)
        foot = QHBoxLayout(); foot.setSpacing(8)
        if pv["gold"]:
            foot.addWidget(_chip(pv["gold"], "gold", 28))
        if pv["weight"]:
            foot.addWidget(_t(f"Weight {pv['weight']}", TEXT3, FS_SMALL))
        foot.addStretch(1)
        extra = QLineEdit(s["extra"]); extra.setObjectName("wizExtra")
        extra.setPlaceholderText("+ Anything else to add…")
        extra.setToolTip("Items to add as well, with commas between")
        extra.setStyleSheet(_field_qss("wizExtra"))
        extra.setMinimumWidth(240)
        extra.editingFinished.connect(lambda e=extra: self._set_extra(e.text()))
        foot.addWidget(extra)
        lay.addLayout(foot)
        return card

    def _set_extra(self, text):
        if text != self.state["extra"]:
            self.state["extra"] = text
            QTimer.singleShot(0, self._refresh)

    # ═══════════════════════════════════════════════════════════════
    #  6. Summary
    # ═══════════════════════════════════════════════════════════════
    def _summary_page(self):
        c = W.kit_char(self._built(4), self._equip_items(), self.state["extra"])
        sm = W.summary(c)
        page = QWidget(); page.setObjectName("wizSumPage"); page.setStyleSheet("#wizSumPage{background:transparent;}")
        g = QGridLayout(page); g.setContentsMargins(0, 0, 0, 0); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)
        choices_step = 3 if self._has_level1() else 2

        def edit(text, step):
            b = _small_btn(f"✎ {text}", "wizEdit")
            b.setProperty("editStep", step)
            b.clicked.connect(lambda _=False, st=step: self.go_to(st))
            return b

        def kv_rows(cl, rows):
            for lab, txt in rows:
                r = QHBoxLayout(); r.setSpacing(8)
                lb = _t(lab, TEXT3, FS_SMALL, bold=True); lb.setFixedWidth(84); r.addWidget(lb, 0, Qt.AlignTop)
                r.addWidget(_t(txt, TEXT, FS_SMALL, wrap=True), 1)
                cl.addLayout(r)

        # name, and the six numbers
        idw = QWidget(); idw.setObjectName("wizSumId"); idw.setStyleSheet("#wizSumId{background:transparent;}")
        iv = QVBoxLayout(idw); iv.setContentsMargins(0, 0, 0, 0); iv.setSpacing(8)
        card, cl = _card("wizSumName", (14, 12, 14, 12))
        top = QHBoxLayout(); top.addWidget(_t(sm["name"], GOLD2, FS_TITLE + 2, bold="x")); top.addStretch(1)
        top.addWidget(edit("Name", 2)); cl.addLayout(top)
        cl.addWidget(_t(sm["line"], TEXT, FS_BODY - 1, bold=True))
        for x in (sm["sub"], sm["sub2"]):
            if x:
                cl.addWidget(_t(x, TEXT2, FS_SMALL))
        iv.addWidget(card)
        sg = QGridLayout(); sg.setSpacing(6)
        for i, (val, lab) in enumerate(sm["stats"]):
            pb = lab == "PROF BONUS"
            f = _box("wizStat", SURF2, BORDER2 if pb else BORDER, 9)
            f.setProperty("statName", lab)
            fl = QVBoxLayout(f); fl.setContentsMargins(4, 8, 4, 8); fl.setSpacing(0)
            fl.addWidget(_t(val, IND2 if pb else TEXT, FS_TITLE, bold="x", align=Qt.AlignCenter))
            fl.addWidget(_t(lab, TEXT3, FS_SMALL - 3, bold="x", align=Qt.AlignCenter, spacing=True))
            sg.addWidget(f, i // 3, i % 3)
        iv.addLayout(sg)
        g.addWidget(idw, 0, 0)

        card, cl = _card("wizSumAb")
        cl.addWidget(_head("Abilities", "", edit("Abilities", 1)))
        ag = QGridLayout(); ag.setSpacing(6)
        for i, a in enumerate(sm["abilities"]):
            f = _box("wizSumAbBox", SURF2, BORDER, 9)
            fl = QVBoxLayout(f); fl.setContentsMargins(4, 6, 4, 8); fl.setSpacing(1)
            hr = QHBoxLayout(); hr.addSpacing(8); hr.addStretch(1)
            hr.addWidget(_t(a["ab"], TEXT2, FS_SMALL - 1, bold="x", align=Qt.AlignCenter, spacing=True))
            hr.addStretch(1)
            d = QLabel(); d.setObjectName("wizSaveDot"); d.setFixedSize(8, 8)
            d.setStyleSheet(f"#wizSaveDot{{background:{TEAL if a['save'] else 'transparent'};border-radius:4px;}}")
            if a["save"]:
                d.setToolTip("Save proficiency")
            hr.addWidget(d, 0, Qt.AlignTop)
            fl.addLayout(hr)
            fl.addWidget(_t(str(a["score"]), TEXT, FS_TITLE, bold="x", align=Qt.AlignCenter))
            mr = QHBoxLayout(); mr.addStretch(1)
            mr.addWidget(_red_chip(a["mod"], 22) if a["mod"].startswith("-") else _chip(a["mod"], "teal", 22))
            mr.addStretch(1); fl.addLayout(mr)
            ag.addWidget(f, i // 3, i % 3)
        cl.addLayout(ag)
        if sm["saves_text"]:
            sv = QHBoxLayout(); sv.setSpacing(5)
            d = QLabel(); d.setObjectName("wizSaveDot2"); d.setFixedSize(8, 8)
            d.setStyleSheet(f"#wizSaveDot2{{background:{TEAL};border-radius:4px;}}")
            sv.addWidget(d); sv.addWidget(_t(f"save proficiency: {sm['saves_text']}", TEXT3, FS_SMALL - 1)); sv.addStretch(1)
            cl.addLayout(sv)
        g.addWidget(card, 0, 1)

        card, cl = _card("wizSumSkills")
        cl.addWidget(_head("Skills", "", edit("Choices", choices_step)))
        for n, b in sm["skills"]:
            r = QFrame(); r.setObjectName("wizSkRow")
            r.setStyleSheet(f"#wizSkRow{{background:transparent;border:none;border-bottom:1px solid {SURF3};}}")
            r.setFixedHeight(30)
            rl = QHBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0)
            rl.addWidget(_t(n, TEXT, FS_SMALL + 1)); rl.addStretch(1); rl.addWidget(_t(b, TEAL2, FS_SMALL + 1, bold="x"))
            cl.addWidget(r)
        cl.addWidget(_t(sm["senses"], TEXT3, FS_SMALL - 1, wrap=True))
        cl.addStretch(1)
        g.addWidget(card, 0, 2)

        card, cl = _card("wizSumSpells")
        sp = sm["spells"]
        cl.addWidget(_head("Spells", "", edit("Spells", 3) if sp and self._has_level1() else None))
        if sp:
            if sp["head"]:
                cl.addWidget(_t(sp["head"], TEXT2, FS_SMALL))
            if sp["cantrips"]:
                cl.addWidget(_t("CANTRIPS", TEXT3, FS_SMALL - 2, bold="x"))
                cl.addWidget(_chip_grid([(x, "") for x in sp["cantrips"]], 2, 30))
            if sp["spells"]:
                cl.addWidget(_t(sp["title"], TEXT3, FS_SMALL - 2, bold="x"))
                cl.addWidget(_chip_grid([(x, "teal") for x in sp["spells"]], 2, 30))
            if sp.get("note"):
                cl.addWidget(_t(sp["note"], TEXT3, FS_SMALL - 1))
        else:
            cl.addWidget(_t("No spells at level 1.", TEXT3, FS_SMALL))
        cl.addStretch(1)
        g.addWidget(card, 1, 0)

        card, cl = _card("wizSumProfs")
        cl.addWidget(_head("Proficiencies", "", edit("Choices", choices_step)))
        kv_rows(cl, sm["profs"])
        cl.addStretch(1)
        g.addWidget(card, 1, 1)

        card, cl = _card("wizSumEquip")
        cl.addWidget(_head("Equipment", "", edit("Equipment", 4)))
        kv_rows(cl, sm["equipment"])
        fr = QHBoxLayout(); fr.setSpacing(8)
        if sm["gold"]:
            fr.addWidget(_chip(sm["gold"], "gold", 26))
        if sm["weight"]:
            fr.addWidget(_t(sm["weight"], TEXT3, FS_SMALL - 1))
        fr.addStretch(1)
        cl.addLayout(fr)
        cl.addStretch(1)
        g.addWidget(card, 1, 2)

        card, cl = _card("wizSumFeatures")
        cl.addWidget(_head("Features"))
        feats = sm["features"]
        n = min(7, max(1, len(feats)))
        cl.addWidget(_chip_grid([(x, "off") for x in feats], n, 32))
        g.addWidget(card, 2, 0, 1, 3)
        for col in range(3):
            g.setColumnStretch(col, 1)
        g.setRowStretch(3, 1)
        return page
