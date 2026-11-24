"""The app's own pop-ups: a name, a pick from a list, a how-many, a
"are you sure?" and a plain message, in the theme's colours instead of
the system's grey boxes.

Each opens beside the pointer (where you right-clicked or clicked), or
over the middle of the window when the pointer is elsewhere (a keyboard
shortcut), and is always kept wholly on the screen: it flips to the other
side of the pointer when there's no room, and a long message scrolls
inside it rather than growing past the screen's edge.

`Ask` stands in for QInputDialog's getText / getInt / getItem and `Tell`
for QMessageBox's information / warning / question: the same arguments
and the same answers, so a call site only changes its class name.
QMessageBox's button constants (QMessageBox.Yes, .Cancel, ...) are still
what `Tell.question` takes and returns.
"""
import re

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QCursor, QGuiApplication, QColor, QIntValidator
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QComboBox, QPushButton, QScrollArea, QWidget,
    QGraphicsDropShadowEffect, QMessageBox,
)

import dnd_app.ui_desktop.style.theme as T

_SHADOW = 16          # room around the card for its shadow
_GAP = 10             # from the pointer to the card's corner
_EDGE = 8             # kept from the screen's edge
_DANGER_WORDS = ("delete", "remove", "discard", "can't be undone", "cannot be undone",
                 "permanently", "clear ")

_LABELS = {
    QMessageBox.Ok: "OK", QMessageBox.Yes: "Yes", QMessageBox.No: "No",
    QMessageBox.Save: "Save", QMessageBox.Discard: "Don't Save",
    QMessageBox.Cancel: "Cancel", QMessageBox.Close: "Close",
    QMessageBox.Apply: "Apply", QMessageBox.Retry: "Try Again",
    QMessageBox.Ignore: "Ignore", QMessageBox.Abort: "Stop",
    QMessageBox.YesToAll: "Yes to All", QMessageBox.NoToAll: "No to All",
}
_ORDER = (QMessageBox.Discard, QMessageBox.No, QMessageBox.NoToAll, QMessageBox.Abort,
          QMessageBox.Ignore, QMessageBox.Cancel, QMessageBox.Close, QMessageBox.Retry,
          QMessageBox.Apply, QMessageBox.YesToAll, QMessageBox.Save, QMessageBox.Yes,
          QMessageBox.Ok)
_BACKING = (QMessageBox.No, QMessageBox.Cancel, QMessageBox.Close, QMessageBox.Abort,
            QMessageBox.NoToAll, QMessageBox.Ignore, QMessageBox.Discard)


def _danger(*texts) -> bool:
    t = " ".join(x for x in texts if x).casefold()
    return any(w in t for w in _DANGER_WORDS)


def _button(text: str, kind: str) -> QPushButton:
    """kind: "ok" (teal), "danger" (crimson), "warn" (amber) or "back"."""
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setMinimumWidth(84)
    h = "min-height:30px;max-height:30px;"
    fs = T.FS_BODY
    if kind == "back":
        b.setStyleSheet(
            f"QPushButton{{background:{T.SURF2};border:1px solid {T.BORDER2};border-radius:7px;"
            f"color:{T.TEXT2};font-weight:700;font-size:{fs}px;padding:0 14px;{h}}}"
            f"QPushButton:hover{{background:{T.SURF3};color:{T.TEXT};}}"
            f"QPushButton:focus{{border-color:{T.IND2};}}")
        return b
    col = {"ok": T.TEAL, "danger": T.CRIMSON, "warn": T.AMBER}[kind]
    txt = T.on_fill(col)
    b.setStyleSheet(
        f"QPushButton{{background:{col};border:1px solid {col};border-radius:7px;"
        f"color:{txt};font-weight:800;font-size:{fs}px;padding:0 16px;{h}}}"
        f"QPushButton:hover{{background:{T.tint(col, '#ffffff', 0x30)};}}"
        f"QPushButton:focus{{border:1px solid {T.TEXT};}}"
        f"QPushButton:disabled{{background:{T.SURF3};border-color:{T.BORDER};color:{T.TEXT3};}}")
    return b


class Popup(QDialog):
    """One themed pop-up: a title, the question or message, what you fill
    in (if anything), then its buttons on the right."""

    def __init__(self, parent, title: str, text: str = "", accent: str = None):
        win = parent.window() if isinstance(parent, QWidget) else QApplication.activeWindow()
        super().__init__(win)
        self._anchor_win = win
        self.setObjectName("themedPopup")
        self.setWindowTitle(title or "MIMIC")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self._drag = None
        self._result_value = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(_SHADOW, _SHADOW, _SHADOW, _SHADOW)
        self.card = QFrame()
        self.card.setObjectName("popupCard")
        self.card.setStyleSheet(
            f"QFrame#popupCard{{background:{T.SURF};border:1px solid {T.BORDER2};border-radius:12px;}}"
            f"QFrame#popupCard QLabel{{background:transparent;border:none;}}")
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(28); shadow.setOffset(0, 8); shadow.setColor(QColor(0, 0, 0, 150))
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card)

        self.body = QVBoxLayout(self.card)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(11)

        self.title = QLabel(title)
        self.title.setWordWrap(True)
        self.title.setStyleSheet(f"color:{accent or T.GOLD2};font-size:{T.FS_HEAD}px;font-weight:800;")
        self.title.installEventFilter(self)          # drag it by its title
        self.title.setCursor(Qt.SizeAllCursor)
        self.body.addWidget(self.title)

        self.text = None
        if text:
            self.text = QLabel(text)
            self.text.setWordWrap(True)
            self.text.setTextFormat(Qt.RichText if re.search(r"<(b|i|br|p|ul|li|table|span|div|h\d)\b", text, re.I) else Qt.PlainText)
            self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.text.setStyleSheet(f"color:{T.TEXT};font-size:{T.FS_BODY}px;")
            # a long message scrolls inside the card (see place())
            self._scroll = QScrollArea()
            self._scroll.setWidgetResizable(True)
            self._scroll.setFrameShape(QFrame.NoFrame)
            self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self._scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                                       "QScrollArea > QWidget > QWidget{background:transparent;}")
            self._scroll.setWidget(self.text)
            self.body.addWidget(self._scroll)

        self.extra = QVBoxLayout(); self.extra.setSpacing(8)
        self.body.addLayout(self.extra)
        self.buttons = QHBoxLayout(); self.buttons.setSpacing(8)
        self.buttons.addStretch(1)
        self.body.addLayout(self.buttons)

    # what you fill in, and the buttons
    def field_style(self) -> str:
        return (f"background:{T.SURF2};border:1px solid {T.BORDER2};border-radius:8px;"
                f"color:{T.TEXT};font-size:{T.FS_BODY}px;padding:6px 10px;"
                f"selection-background-color:{T.INDIGO};selection-color:{T.on_fill(T.INDIGO)};")

    def add_button(self, text, kind, on_click):
        b = _button(text, kind)
        b.clicked.connect(on_click)
        self.buttons.addWidget(b)
        return b

    # where it opens: beside the pointer, wholly on the screen
    def place(self):
        self.setMaximumWidth(10_000)
        self.card.setMinimumWidth(340)
        self.card.setMaximumWidth(500)
        cursor = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor)
        win = self._anchor_win
        in_win = win is not None and win.isVisible() and win.frameGeometry().contains(cursor)
        if not in_win and win is not None and win.isVisible():
            screen = win.screen()
        screen = screen or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        # a long message scrolls, so the card is never taller than the screen
        if self.text is not None:
            fm = self.text.fontMetrics()
            plain = self.text.text() if self.text.textFormat() == Qt.PlainText else ""
            natural = max((fm.horizontalAdvance(l) for l in plain.splitlines()), default=0) + 8
            tw = max(304, min(natural or 464, 464))
            self.text.setFixedWidth(tw)
            self._scroll.setFixedWidth(tw)
            need = self.text.heightForWidth(tw) + 4
            # everything else in the pop-up, measured with the text left out
            self._scroll.setFixedHeight(0)
            self.body.invalidate(); self.layout().invalidate()
            self.body.activate(); self.layout().activate()
            others = self.layout().totalSizeHint().height()
            room = max(120, avail.height() - 2 * _EDGE - others + 2 * _SHADOW)
            self._scroll.setFixedHeight(max(20, need))
            if need > room:
                # too long for the screen: it scrolls, the bar beside the text
                self.text.setFixedWidth(tw - 14)
                self._scroll.setFixedHeight(room)
        self.body.invalidate(); self.layout().invalidate()
        self.body.activate(); self.layout().activate()
        hint = self.layout().totalSizeHint()
        w, h = hint.width(), hint.height()
        w = min(w, avail.width() + 2 * _SHADOW - 2 * _EDGE)
        h = min(h, avail.height() + 2 * _SHADOW - 2 * _EDGE)
        self.resize(w, h)
        if in_win:
            # down and right of the pointer, or flipped where there's no room
            x = cursor.x() + _GAP - _SHADOW
            y = cursor.y() + _GAP - _SHADOW
            if x + w - _SHADOW > avail.right() - _EDGE:
                x = cursor.x() - _GAP - w + _SHADOW
            if y + h - _SHADOW > avail.bottom() - _EDGE:
                y = cursor.y() - _GAP - h + _SHADOW
        else:
            c = (win.frameGeometry().center() if win is not None and win.isVisible()
                 else avail.center())
            x, y = c.x() - w // 2, c.y() - h // 2
        # and never past an edge, whatever happened above
        x = max(avail.left() + _EDGE - _SHADOW, min(x, avail.right() - _EDGE - w + _SHADOW + 1))
        y = max(avail.top() + _EDGE - _SHADOW, min(y, avail.bottom() - _EDGE - h + _SHADOW + 1))
        self.move(x, y)

    def run(self):
        self.place()
        return self.exec()

    # dragging it by the title, kept on the screen
    def eventFilter(self, obj, ev):
        if obj is self.title:
            if ev.type() == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
                self._drag = ev.globalPosition().toPoint() - self.pos()
                return True
            if ev.type() == QEvent.MouseMove and self._drag is not None:
                p = ev.globalPosition().toPoint() - self._drag
                scr = (QGuiApplication.screenAt(ev.globalPosition().toPoint())
                       or self.screen()).availableGeometry()
                p.setX(max(scr.left() - _SHADOW, min(p.x(), scr.right() - self.width() + _SHADOW)))
                p.setY(max(scr.top() - _SHADOW, min(p.y(), scr.bottom() - self.height() + _SHADOW)))
                self.move(p)
                return True
            if ev.type() == QEvent.MouseButtonRelease:
                self._drag = None
                return True
        return super().eventFilter(obj, ev)


class Ask:
    """QInputDialog's questions, themed (same arguments, same answers)."""

    @staticmethod
    def getText(parent, title, label, echo=QLineEdit.Normal, text="", *a, **k):
        if "echo" in k:
            echo = k.pop("echo")
        d = Popup(parent, title, label)
        edit = QLineEdit(text or "")
        edit.setEchoMode(echo)
        edit.setStyleSheet(f"QLineEdit{{{d.field_style()}min-height:24px;}}"
                           f"QLineEdit:focus{{border-color:{T.IND2};}}")
        edit.selectAll()
        d.extra.addWidget(edit)
        danger = _danger(title, label)
        d.add_button("Cancel", "back", d.reject)
        ok = d.add_button("Delete" if "type delete" in (label or "").casefold() else "OK",
                          "danger" if danger else "ok", d.accept)
        ok.setDefault(True)
        edit.returnPressed.connect(d.accept)
        edit.setFocus()
        accepted = d.run() == QDialog.Accepted
        return (edit.text() if accepted else ""), accepted

    @staticmethod
    def getInt(parent, title, label, value=0, minValue=-2147483647, maxValue=2147483647,
               step=1, *a, **k):
        value = k.pop("value", value); minValue = k.pop("minValue", k.pop("min", minValue))
        maxValue = k.pop("maxValue", k.pop("max", maxValue)); step = k.pop("step", step)
        d = Popup(parent, title, label)
        row = QHBoxLayout(); row.setSpacing(8)
        # the number, typed or stepped, kept within its range
        edit = QLineEdit(str(value))
        edit.setValidator(QIntValidator(minValue, maxValue, edit))
        edit.setAlignment(Qt.AlignCenter)
        edit.setStyleSheet(f"QLineEdit{{{d.field_style()}font-size:{T.FS_HEAD + 2}px;font-weight:800;"
                           f"min-height:26px;max-height:26px;}}"
                           f"QLineEdit:focus{{border-color:{T.IND2};}}")

        def current():
            try:
                return max(minValue, min(maxValue, int(edit.text())))
            except ValueError:
                return value

        def stepper(glyph, delta):
            b = QPushButton(glyph)
            b.setFixedWidth(40)
            b.setCursor(Qt.PointingHandCursor)
            b.setAutoRepeat(True)
            b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet(
                f"QPushButton{{background:{T.SURF2};border:1px solid {T.BORDER2};border-radius:8px;"
                f"color:{T.TEXT};font-size:{T.FS_HEAD + 2}px;font-weight:800;padding:0;"
                f"min-height:38px;max-height:38px;}}"
                f"QPushButton:hover{{background:{T.SURF3};border-color:{T.IND2};}}")
            b.clicked.connect(lambda: edit.setText(str(max(minValue, min(maxValue, current() + delta * step)))))
            return b
        row.addWidget(stepper("−", -1)); row.addWidget(edit, 1); row.addWidget(stepper("+", 1))
        d.extra.addLayout(row)
        d.add_button("Cancel", "back", d.reject)
        ok = d.add_button("OK", "ok", d.accept)
        ok.setDefault(True)
        if (title or "").startswith("Add "):
            ok.setText(f"Add {current()}")
            edit.textChanged.connect(lambda _t: ok.setText(f"Add {current()}"))
        edit.returnPressed.connect(d.accept)
        edit.setFocus(); edit.selectAll()
        accepted = d.run() == QDialog.Accepted
        return (current() if accepted else value), accepted

    @staticmethod
    def getItem(parent, title, label, items, current=0, editable=True, *a, **k):
        current = k.pop("current", current); editable = k.pop("editable", editable)
        items = list(items)
        d = Popup(parent, title, label)
        if editable:
            # a pick or something new typed in (a new folder's name)
            box = QComboBox()
            box.setEditable(True)
            box.addItems(items)
            if 0 <= current < len(items):
                box.setCurrentIndex(current)
            box.setStyleSheet(f"QComboBox{{{d.field_style()}min-height:24px;}}QComboBox:focus{{border-color:{T.IND2};}}")
            d.extra.addWidget(box)
            get = box.currentText
            box.lineEdit().returnPressed.connect(d.accept)
            box.setFocus()
        else:
            # the choices as rows: click one and OK, or double-click it
            lst = QListWidget()
            lst.setObjectName("popupList")
            lst.addItems(items)
            lst.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            lst.setStyleSheet(
                f"QListWidget{{background:{T.SURF2};border:1px solid {T.BORDER2};border-radius:8px;"
                f"color:{T.TEXT};font-size:{T.FS_BODY}px;padding:4px;outline:0;}}"
                f"QListWidget::item{{padding:6px 8px;border-radius:5px;}}"
                f"QListWidget::item:hover{{background:{T.SURF3};}}"
                f"QListWidget::item:selected{{background:{T.qa(T.TEAL, 0x40)};color:{T.TEXT};"
                f"border:1px solid {T.TEAL};}}")
            if items:
                lst.setCurrentRow(current if 0 <= current < len(items) else 0)
            row_h = max(lst.sizeHintForRow(0), 24) + 2 if items else 28
            scr = (QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen())
            most = max(4, int(scr.availableGeometry().height() * 0.5) // max(row_h, 1))
            lst.setFixedHeight(min(len(items), min(most, 10)) * row_h + 12)
            lst.itemDoubleClicked.connect(lambda _it: d.accept())
            if len(items) > 10:
                # a long list: a search box over it, as the browsers have
                search = QLineEdit()
                search.setObjectName("popupSearch")
                search.setPlaceholderText("Search…")
                search.setClearButtonEnabled(True)
                search.setStyleSheet(f"QLineEdit{{{d.field_style()}min-height:22px;}}"
                                     f"QLineEdit:focus{{border-color:{T.IND2};}}")

                def _filter(text):
                    words = text.casefold().split()
                    first = None
                    for i in range(lst.count()):
                        it = lst.item(i)
                        hide = bool(words) and not all(w in it.text().casefold() for w in words)
                        it.setHidden(hide)
                        if not hide and first is None:
                            first = it
                    cur = lst.currentItem()
                    if first is not None and (cur is None or cur.isHidden()):
                        lst.setCurrentItem(first)
                search.textChanged.connect(_filter)
                search.returnPressed.connect(d.accept)
                d.extra.addWidget(search)
            d.extra.addWidget(lst)
            get = lambda: (lst.currentItem().text()
                           if lst.currentItem() is not None and not lst.currentItem().isHidden() else "")
            (search if len(items) > 10 else lst).setFocus()
        d.add_button("Cancel", "back", d.reject)
        ok = d.add_button("OK", "ok", d.accept)
        ok.setDefault(True)
        accepted = d.run() == QDialog.Accepted and (editable or bool(get()))
        return (get() if accepted else ""), accepted


class Tell:
    """QMessageBox's messages and questions, themed (same arguments, same
    answers: a QMessageBox.StandardButton)."""

    @staticmethod
    def _show(parent, title, text, buttons, default, accent, plain_kind="ok"):
        d = Popup(parent, title, text, accent=accent)
        chosen = {"b": QMessageBox.NoButton}
        if not isinstance(buttons, QMessageBox.StandardButton):
            buttons = QMessageBox.StandardButton(buttons)
        present = [b for b in _ORDER if buttons & b]
        if not present:
            present = [QMessageBox.Ok]
        danger = _danger(title, text)
        escape = next((b for b in present if b in (QMessageBox.Cancel, QMessageBox.No, QMessageBox.Close)),
                      present[0] if len(present) == 1 else None)
        default_b = default if default in present else next(
            (b for b in reversed(present) if b not in _BACKING), present[-1])
        for b in present:
            if b in _BACKING:
                kind = "back"
            elif len(present) == 1:
                kind = plain_kind
            else:
                kind = "danger" if danger else "ok"

            def pick(_=False, b=b):
                chosen["b"] = b
                d.done(1)
            btn = d.add_button(_LABELS.get(b, "OK"), kind, pick)
            if b == default_b:
                btn.setDefault(True); btn.setFocus()
        d.run()
        if chosen["b"] == QMessageBox.NoButton:       # Esc
            return escape if escape is not None else QMessageBox.NoButton
        return chosen["b"]

    @staticmethod
    def information(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return Tell._show(parent, title, text, buttons, defaultButton, None)

    @staticmethod
    def warning(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return Tell._show(parent, title, text, buttons, defaultButton, T.AMBE2 if hasattr(T, "AMBE2") else T.AMBER)

    @staticmethod
    def critical(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return Tell._show(parent, title, text, buttons, defaultButton, T.CRIM2)

    @staticmethod
    def question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No,
                 defaultButton=QMessageBox.NoButton):
        return Tell._show(parent, title, text, buttons, defaultButton, None)

    @staticmethod
    def choose(parent, title, text, ok_text, cancel_text="Cancel") -> bool:
        """A message with its own wording on the go-ahead button (e.g.
        "Choose PDF…"): True when it was pressed."""
        d = Popup(parent, title, text)
        d.add_button(cancel_text, "back", d.reject)
        ok = d.add_button(ok_text, "ok", d.accept)
        ok.setDefault(True); ok.setFocus()
        return d.run() == QDialog.Accepted
