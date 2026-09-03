"""Reusable custom widgets for the character creator.

Only FlowLayout/FlowContainer are actually used anywhere in the app
(imported by sheet.py) — the equivalents these components need
(SkillRow, StatBox, HPTracker, etc.) are built directly into
sheet.py/shared.py instead.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QFont
from dnd_app.ui.style.theme import *


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
