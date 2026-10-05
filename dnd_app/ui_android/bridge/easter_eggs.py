"""App-wide "cheese" easter egg -- same as ui_desktop's main_window.py
MainWindow.eventFilter(): typing "cheese" anywhere pops a tiny cheese
icon in the corner for a few seconds, purely for fun, no gameplay
effect. Installed as a QGuiApplication-level event filter (mirroring
desktop's QApplication.installEventFilter(self) exactly) so it fires
regardless of which control currently has focus -- a text field, a
spell search box, or nothing at all.
"""
from PySide6.QtCore import QObject, Signal, QEvent
from PySide6.QtGui import QGuiApplication, QWindow
from shiboken6 import getCppPointer


class EasterEggBridge(QObject):
    cheeseTyped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buffer = ""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # An unhandled key event delivered to a Qt Quick window
            # gets forwarded on to the scene's focused Item, and BOTH
            # hops individually pass through QGuiApplication::notify()
            # -- an app-installed filter (unlike widgets' keyPressEvent,
            # which only fires once per actual receiver) sees the same
            # physical keypress twice unless restricted to just the
            # window-level dispatch here.
            if not isinstance(obj, QWindow):
                return False
            text = event.text()
            if text:
                self._feed(text, "")
        elif event.type() == QEvent.InputMethod:
            # Phone keyboards (Gboard, SwiftKey, ...) don't send key
            # presses for letters at all: text arrives as input-method
            # events, the word-in-progress as "preedit" text and finished
            # text as a "commit". Without this the easter egg only ever
            # fired with a hardware keyboard. Input-method events go
            # straight to the focused item, so count each one once -- for
            # the app's focus object only.
            focus = QGuiApplication.focusObject()
            if focus is None or getCppPointer(obj)[0] != getCppPointer(focus)[0]:
                return False
            self._feed(event.commitString(), event.preeditString())
        return False

    def _feed(self, committed, preedit):
        if committed:
            self._buffer = (self._buffer + committed.lower())[-12:]
        if (self._buffer + preedit.lower()).endswith("cheese"):
            self.cheeseTyped.emit()
            self._buffer = ""
