"""Reusable custom widgets for the character creator.

- FlowLayout / FlowContainer: wrap chips onto new rows (badge strips).
- RarityBarDelegate: a magic item's rarity as a coloured bar beside it.
- InspectButtonDelegate / RarityInspectDelegate: a magnifying glass on
  each row of a browser list that opens the row's details.
- FilterSidebar: a browser's filters in a panel that slides in from the
  right, opened by a funnel button at the end of the search row.
(SkillRow, StatBox, HPTracker and the like are built directly into
the sheet pages / shared.py instead.)

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QFont
from dnd_app.ui_desktop.style.theme import *


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


# Item data role holding a row's rarity colour (a "#rrggbb" string) for
# RarityBarDelegate.
RARITY_ROLE = Qt.UserRole + 42
RARITY_BAR_WIDTH = 8


class RarityBarDelegate(QStyledItemDelegate):
    """Paints a solid bar in the item's rarity colour down the left edge of
    the cell, and moves the text over to make room. Colour marks rarity
    without colouring the text itself -- coloured text (navy on a dark
    background...) is hard to read. Rows with no RARITY_ROLE colour are
    drawn as normal, with the same indent so names line up."""

    def paint(self, painter, option, index):
        super().paint(painter, self.indented(option), index)
        self.paint_bar(painter, option, index)

    @staticmethod
    def indented(option):
        """The row's option moved right, past the bar."""
        shifted = QStyleOptionViewItem(option)
        shifted.rect = option.rect.adjusted(RARITY_BAR_WIDTH + 6, 0, 0, 0)
        return shifted

    @staticmethod
    def paint_bar(painter, option, index):
        from PySide6.QtGui import QColor
        colour = index.data(RARITY_ROLE)
        if not colour:
            return
        bar = QRect(option.rect.left() + 2, option.rect.top() + 3,
                    RARITY_BAR_WIDTH, max(4, option.rect.height() - 6))
        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(colour))
        painter.drawRoundedRect(bar, 2, 2)
        painter.restore()

    def sizeHint(self, option, index):
        s = super().sizeHint(option, index)
        return QSize(s.width() + RARITY_BAR_WIDTH + 6, s.height())


_inspect_pixmaps = {}   # (colour, size, device pixel ratio) -> QPixmap


class InspectButtonDelegate(QStyledItemDelegate):
    """A magnifying glass at the right end of each row of a browser list:
    the same 28x24 Details button an owned item has in the inventory.
    Pressing it calls on_inspect with the row's Qt.UserRole data (the
    spell, the item's name); the rest of the row still selects,
    double-clicks and right-clicks as before. The button is painted rather
    than a QPushButton per row, so a list of a thousand magic items still
    filters quickly.

    column -- in a tree, the narrow column the button goes in (give the
      delegate to that column alone); the row's data is still read from
      column 0. A list has just the one.
    has_details(data) -- whether a row gets a button; by default any row
      with data, so headings (no data) have none.
    selected_icon -- the icon's colour on a selected row: the view's own
      selected-text colour, since the accent can vanish on the highlight."""

    BTN_W, BTN_H, ICON = 28, 24, 18
    RARITY_BAR = False   # RarityInspectDelegate: RarityBarDelegate's bar on the left too

    def __init__(self, view, on_inspect, selected_icon="white", column=0, has_details=None):
        from PySide6.QtCore import QPersistentModelIndex
        super().__init__(view)
        self._view = view
        self._on_inspect = on_inspect
        self._selected_icon = selected_icon
        self._column = column
        self._has_details = has_details or (lambda data: data is not None)
        self._hot = QPersistentModelIndex()       # the button the mouse is over
        self._pressed = QPersistentModelIndex()   # the button pressed
        view.setMouseTracking(True)
        view.viewport().installEventFilter(self)

    def _has_button(self, index) -> bool:
        return (index.isValid() and index.column() == self._column
                and self._has_details(index.siblingAtColumn(0).data(Qt.UserRole)))

    def _button_rect(self, rect) -> QRect:
        # the row's right edge as seen: a row can run past the viewport
        right = min(rect.right(), self._view.viewport().rect().right())
        return QRect(right - self.BTN_W - 3, rect.top() + (rect.height() - self.BTN_H) // 2,
                     self.BTN_W, self.BTN_H)

    def sizeHint(self, option, index):
        s = super().sizeHint(option, index)
        return QSize(s.width() + RARITY_BAR_WIDTH + 6, s.height()) if self.RARITY_BAR else s

    def _paint_row(self, painter, option, index, text_end=None):
        """The row as QStyledItemDelegate.paint draws it (past the rarity
        bar, and the bar, for RarityInspectDelegate), with its text cut
        short to end at x = text_end. Done here rather than by overriding
        initStyleOption, which Qt also calls for every row's size: under
        PySide6 6.12.0 on Python 3.11 or older (see requirements.txt) each
        of those calls loses a reference to None, and a thousand-row list
        used them up within seconds."""
        opt = RarityBarDelegate.indented(option) if self.RARITY_BAR else QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        if text_end is not None:
            room = text_end - opt.rect.left() - 10   # 10px: the rows' padding before the text
            opt.text = opt.fontMetrics.elidedText(opt.text, Qt.ElideRight, room) if room > 0 else ""
        widget = option.widget
        (widget.style() if widget else QApplication.style()).drawControl(
            QStyle.CE_ItemViewItem, opt, painter, widget)
        if self.RARITY_BAR:
            RarityBarDelegate.paint_bar(painter, option, index)

    def paint(self, painter, option, index):
        if not self._has_button(index):
            self._paint_row(painter, option, index)
            return
        from PySide6.QtGui import QColor, QPainter
        from PySide6.QtCore import QRectF
        from dnd_app.ui_desktop import icons as _icons
        from dnd_app.ui_desktop.style import theme as _theme
        btn = self._button_rect(option.rect)
        split = btn.left() - 4
        r = option.rect
        # The row is drawn whole twice -- the same rounded background,
        # selection and lines both times, so it stays one piece -- once
        # left of the button with its text (shortened to end before it),
        # once under the button with no text.
        for clip, text_end in ((QRect(r.left(), r.top(), split - r.left(), r.height()), split - 4),
                               (QRect(split, r.top(), r.right() - split + 1, r.height()), 0)):
            painter.save()
            painter.setClipRect(clip, Qt.IntersectClip)
            self._paint_row(painter, option, index, text_end)
            painter.restore()

        selected = bool(option.state & QStyle.State_Selected)
        if self._hot.isValid() and self._hot == index:
            edge = self._selected_icon if selected else _theme.INDIGO
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor(edge))
            painter.setBrush(QColor(qa(QColor(edge).name(), 0x33)))
            painter.drawRoundedRect(QRectF(btn).adjusted(0.5, 0.5, -0.5, -0.5), 5, 5)
            painter.restore()
        size = _icons.scaled(self.ICON)
        colour = self._selected_icon if selected else _icons.accent()
        key = (colour, size, _icons._dpr())
        pm = _inspect_pixmaps.get(key)
        if pm is None:
            pm = _inspect_pixmaps[key] = _icons.pixmap("search", size, colour)
        painter.drawPixmap(btn.left() + (btn.width() - size) // 2,
                           btn.top() + (btn.height() - size) // 2, pm)

    def helpEvent(self, event, view, option, index):
        from PySide6.QtCore import QEvent
        if (event.type() == QEvent.ToolTip and self._has_button(index)
                and self._button_rect(option.rect).contains(event.pos())):
            QToolTip.showText(event.globalPos(), "Details", view)
            return True
        return super().helpEvent(event, view, option, index)

    def _button_at(self, pos):
        """The button cell under pos, or an invalid index."""
        from PySide6.QtCore import QModelIndex
        index = self._view.indexAt(pos)
        cell = index.siblingAtColumn(self._column) if index.isValid() else QModelIndex()
        if self._has_button(cell) and self._button_rect(self._view.visualRect(cell)).contains(pos):
            return cell
        return QModelIndex()

    def _set_hot(self, cell):
        from PySide6.QtCore import QPersistentModelIndex
        if self._hot == cell:
            return
        for old_or_new in (self._hot, cell):
            if old_or_new.isValid():
                self._view.viewport().update(self._view.visualRect(old_or_new))
        self._hot = QPersistentModelIndex(cell)
        if cell.isValid():
            self._view.viewport().setCursor(Qt.PointingHandCursor)
        else:
            self._view.viewport().unsetCursor()

    def _refresh_hot(self):
        from PySide6.QtGui import QCursor
        from PySide6.QtCore import QModelIndex
        vp = self._view.viewport()
        pos = vp.mapFromGlobal(QCursor.pos())
        self._set_hot(self._button_at(pos) if vp.rect().contains(pos) else QModelIndex())

    def eventFilter(self, obj, ev):
        from PySide6.QtCore import QEvent, QTimer, QModelIndex, QPersistentModelIndex
        t = ev.type()
        if t == QEvent.MouseMove:
            self._set_hot(self._button_at(ev.position().toPoint()))
        elif t == QEvent.Leave:
            self._set_hot(QModelIndex())
        elif t == QEvent.Wheel:
            # the rows move under a mouse that stays put
            QTimer.singleShot(0, self, self._refresh_hot)
        elif (t in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.MouseButtonRelease)
                and ev.button() == Qt.LeftButton):
            # presses on the button are its own: the row isn't selected, or
            # added by a double-click
            cell = self._button_at(ev.position().toPoint())
            if t == QEvent.MouseButtonRelease:
                pressed, self._pressed = self._pressed, QPersistentModelIndex()
                if pressed.isValid() and pressed == cell:
                    data = cell.siblingAtColumn(0).data(Qt.UserRole)
                    # once the click is over, not from inside the view's mouse handling
                    QTimer.singleShot(0, self, lambda: self._on_inspect(data))
                return pressed.isValid() or cell.isValid()
            if cell.isValid():
                # a double-click's second press only swallowed: one window
                first = t == QEvent.MouseButtonPress and not self._pressed.isValid()
                self._pressed = QPersistentModelIndex(cell) if first else QPersistentModelIndex()
                return True
        return False


class RarityInspectDelegate(InspectButtonDelegate):
    """The magic item browser's rows: the rarity bar on the left and the
    magnifying glass on the right."""
    RARITY_BAR = True


class FilterSidebar(QFrame):
    """A panel of filters that slides in over the right-hand side of a
    browser, so the browser's top row can be just a search box.

    Using it:
      1. Build the search box and the filter drop-downs as usual.
      2. sidebar = FilterSidebar(host) -- host is the widget the panel
         covers (the browser's page/tab).
      3. sidebar.add_combo("Rarity", combo) for each drop-down filter,
         sidebar.add_check(checkbox) for each on/off filter.
      4. Put sidebar.search_row(search_box) where the search box used to
         go: the search box takes the whole row except for a small funnel
         button at the end.

    The funnel button opens and closes the panel and, while any filter is
    set, shows how many. "Clear filters" puts every drop-down back on its
    first entry ("All ...") and every checkbox back how it started. The
    filters themselves are unchanged widgets -- the browser still reads
    combo.currentText() / checkbox.isChecked() and listens to their
    signals exactly as before.
    """

    WIDTH = 236

    def __init__(self, host: QWidget, title: str = "Filters"):
        super().__init__(host)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        self._host = host
        self._combos = []      # (row widget, combo)
        self._checks = []      # (checkbox, its starting state)
        self._anim = None
        self.setObjectName("filterSidebar")
        self.setStyleSheet(
            f"QFrame#filterSidebar{{background:{SURF2};border:1px solid {BORDER2};"
            f"border-radius:8px;}}"
            # (a host styled with a bare QFrame{...} rule would otherwise
            # draw its border round every label in here too)
            f"QLabel{{background:transparent;border:none;}}")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24); shadow.setOffset(-4, 0); shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self); lay.setContentsMargins(14, 10, 10, 12); lay.setSpacing(8)
        # header: "FILTERS" and a close button
        head = QHBoxLayout(); head.setSpacing(4)
        cap = QLabel(title.upper())
        cap.setStyleSheet(f"color:{GOLD};font-size:{FS_SMALL}px;font-weight:700;")
        head.addWidget(cap); head.addStretch()
        # close: a chevron pointing the way the panel slides away
        close = QToolButton(); close.setToolTip("Close filters")
        from dnd_app.ui_desktop import icons as _icons
        _icons.set_button_icon(close, "chevron_right", 16)
        close.setAccessibleName("Close filters")
        close.setStyleSheet(
            f"QToolButton{{background:transparent;border:none;color:{TEXT2};"
            f"font-size:{FS_BODY}px;min-height:0;padding:2px 6px;}}"
            f"QToolButton:hover{{color:{TEXT};}}")
        close.clicked.connect(self.close_panel)
        head.addWidget(close)
        lay.addLayout(head)
        # the filters go in here, one under the other
        self._body = QVBoxLayout(); self._body.setSpacing(10)
        lay.addLayout(self._body)
        lay.addStretch()
        self._clear = QPushButton("Clear filters")
        self._clear.setAccessibleName("Clear all filters")
        self._clear.setStyleSheet(
            f"QPushButton{{background:{SURF3};border:1px solid {BORDER2};border-radius:6px;"
            f"color:{TEXT};padding:6px 10px;font-size:{FS_SMALL}px;font-weight:700;}}"
            f"QPushButton:hover{{border-color:{INDIGO};}}"
            f"QPushButton:disabled{{color:{TEXT3};}}")
        self._clear.clicked.connect(self.clear)
        lay.addWidget(self._clear)

        # the funnel button that sits at the end of the search row
        self.button = QToolButton()
        self.button.setCheckable(True)
        self.button.setToolTip("Filters")
        self.button.setAccessibleName("Show filters")
        self.button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        _icons.set_button_icon(self.button, "filter", 18)
        self.button.toggled.connect(self._toggle)

        self.hide()
        host.installEventFilter(self)
        self._update_badge()

    # ── Building ──────────────────────────────────────────────────────────
    def add_combo(self, label: str, combo: QComboBox) -> QWidget:
        """Move a filter drop-down into the panel under a small label.
        Returns the row, so a filter that only sometimes applies can be
        hidden with set_filter_visible()."""
        row = QWidget(); rl = QVBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(3)
        cap = QLabel(label)
        cap.setStyleSheet(f"color:{TEXT2};font-size:{FS_TINY}px;font-weight:700;")
        rl.addWidget(cap)
        # the panel is narrow: let the box be narrower than its longest
        # entry (the list itself still opens wide enough to read)
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(8)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo.view().setMinimumWidth(combo.view().sizeHintForColumn(0) + 24)
        rl.addWidget(combo)
        self._body.addWidget(row)
        # only once it's in the panel: shown while it had no parent, it
        # would flash up on screen as a little window of its own
        combo.setVisible(True)
        self._combos.append((row, combo))
        combo.currentIndexChanged.connect(lambda _i: self._update_badge())
        self._update_badge()
        return row

    def add_check(self, check: QCheckBox):
        """Move an on/off filter (e.g. "Show only prepared") into the panel."""
        self._body.addWidget(check)
        self._checks.append((check, check.isChecked()))
        check.toggled.connect(lambda _c: self._update_badge())
        self._update_badge()

    def set_filter_visible(self, combo: QComboBox, visible: bool):
        """Show or hide one drop-down's row (label included)."""
        for row, c in self._combos:
            if c is combo:
                row.setVisible(visible)
        self._update_badge()

    def search_row(self, search: QLineEdit) -> QHBoxLayout:
        """The browser's top row: the search box, then the funnel button."""
        row = QHBoxLayout(); row.setSpacing(6)
        row.addWidget(search, 1)
        h = max(34, search.sizeHint().height())
        self.button.setFixedHeight(h)
        self.button.setMinimumWidth(h + 4)
        row.addWidget(self.button)
        return row

    # ── State ─────────────────────────────────────────────────────────────
    def active_count(self) -> int:
        """How many filters are set to something other than their default."""
        n = sum(1 for row, c in self._combos if not row.isHidden() and c.currentIndex() > 0)
        return n + sum(1 for c, start in self._checks if c.isChecked() != start)

    def clear(self):
        for _row, c in self._combos:
            c.setCurrentIndex(0)
        for c, start in self._checks:
            c.setChecked(start)

    def _update_badge(self):
        """Funnel button: plain when nothing is filtered, accent-bordered
        with the number of filters set when something is."""
        n = self.active_count()
        self.button.setText(str(n) if n else "")
        self.button.setAccessibleDescription(f"{n} filters set" if n else "No filters set")
        edge = INDIGO if (n or self.button.isChecked()) else BORDER2
        self.button.setStyleSheet(
            f"QToolButton{{background:{SURF2};border:1px solid {edge};border-radius:6px;"
            f"color:{IND2};font-weight:700;font-size:{FS_SMALL}px;min-height:0;padding:0 6px;}}"
            f"QToolButton:hover{{border-color:{INDIGO};}}"
            f"QToolButton:checked{{background:{SURF3};}}")
        self._clear.setEnabled(n > 0)

    # ── Opening / closing ─────────────────────────────────────────────────
    def _target_rect(self) -> QRect:
        """Down the right-hand edge of the host, from just under the search
        row (so the funnel button and its count stay in view) to the
        bottom."""
        w = min(self.WIDTH, max(160, self._host.width() - 24))
        top = 4
        if self._host.isAncestorOf(self.button):
            top = self.button.mapTo(self._host, QPoint(0, self.button.height())).y() + 6
        return QRect(self._host.width() - w - 4, top, w, max(120, self._host.height() - top - 4))

    def _toggle(self, on: bool):
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        self._update_badge()
        end = self._target_rect()
        start = QRect(end); start.moveLeft(self._host.width())
        if self._anim:
            self._anim.stop()
        if on:
            self.setGeometry(start); self.show(); self.raise_()
            a, b = start, end
        else:
            a, b = self.geometry(), start
        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(160); anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(a); anim.setEndValue(b)
        if not on:
            anim.finished.connect(self.hide)
        anim.start()
        self._anim = anim
        if on and self._combos:
            self._combos[0][1].setFocus()

    def open_panel(self):
        self.button.setChecked(True)

    def close_panel(self):
        self.button.setChecked(False)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape:
            self.close_panel(); self.button.setFocus(); return
        super().keyPressEvent(ev)

    def eventFilter(self, obj, ev):
        # keep the panel pinned to the host's right edge as it resizes
        from PySide6.QtCore import QEvent
        if obj is self._host and ev.type() == QEvent.Resize and self.isVisible():
            if not (self._anim and self._anim.state() == self._anim.State.Running):
                self.setGeometry(self._target_rect())
        return False
