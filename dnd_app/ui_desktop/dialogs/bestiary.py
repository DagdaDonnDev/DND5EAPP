"""The Bestiary window (Tools → Bestiary, Ctrl+B): every creature MIMIC
knows, to find by name or type and filter by type, size and challenge
rating, with its stat block beside the list. The finding and the stat
block are core/bestiary.py's, the same as Android's Bestiary screen.
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from dnd_app.ui_desktop.style.theme import *
from ..shared import h as _h
from dnd_app.core import bestiary as _b
from dnd_app.data.bestiary import SIZES, get_creature


def _combo(items, first, name):
    box = QComboBox()
    box.setAccessibleName(name)
    box.addItem(first, "")
    for it in items:
        box.addItem(it, it)
    return box


class BestiaryWindow(QWidget):
    """Search and filters on the left with the list under them; the
    chosen creature's stat block on the right."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self.setWindowTitle("Bestiary")
        self.setObjectName("bestiaryWindow")
        self.resize(1000, 720)
        self.setStyleSheet(
            f"QWidget#bestiaryWindow{{background:{BG};}}"
            f"QListWidget{{background:{SURF};border:1px solid {BORDER};border-radius:8px;color:{TEXT};"
            f"font-size:{FS_SMALL}px;outline:none;}}"
            f"QListWidget::item{{padding:6px 8px;border-bottom:1px solid {BORDER};}}"
            f"QListWidget::item:selected{{background:{qa(GOLD, 0x33)};color:{TEXT};}}"
            f"QTextBrowser{{background:{SURF};border:1px solid {BORDER};border-radius:8px;color:{TEXT};"
            f"font-size:{FS_BODY}px;padding:10px;}}")
        root = QHBoxLayout(self); root.setContentsMargins(14, 14, 14, 14); root.setSpacing(12)

        left = QVBoxLayout(); left.setSpacing(8)
        self._search = QLineEdit()
        self._search.setObjectName("bestiarySearch")
        self._search.setPlaceholderText("Find a creature by name or type…")
        self._search.setClearButtonEnabled(True)
        self._search.setAccessibleName("Find a creature")
        left.addWidget(self._search)
        filters = QGridLayout(); filters.setHorizontalSpacing(6); filters.setVerticalSpacing(6)
        self._kind = _combo(_b.kinds(), "Any type", "Creature type")
        self._size = _combo(SIZES, "Any size", "Size")
        self._cr_min = _combo(_b.CR_ORDER, "CR from", "Lowest challenge rating")
        self._cr_max = _combo(_b.CR_ORDER, "CR to", "Highest challenge rating")
        for box, nm in ((self._kind, "bestiaryType"), (self._size, "bestiarySize"),
                        (self._cr_min, "bestiaryCrMin"), (self._cr_max, "bestiaryCrMax")):
            box.setObjectName(nm)
        filters.addWidget(self._kind, 0, 0); filters.addWidget(self._size, 0, 1)
        filters.addWidget(self._cr_min, 1, 0); filters.addWidget(self._cr_max, 1, 1)
        left.addLayout(filters)
        self._count = _h("", TEXT3, FS_TINY)
        left.addWidget(self._count)
        self._list = QListWidget()
        self._list.setObjectName("bestiaryList")
        self._list.setUniformItemSizes(True)
        left.addWidget(self._list, 1)
        lw = QWidget(); lw.setLayout(left); lw.setFixedWidth(340)
        root.addWidget(lw)

        right = QVBoxLayout(); right.setSpacing(6)
        self._title = _h("", GOLD2, FS_HEAD, True)
        self._title.setObjectName("bestiaryTitle")
        right.addWidget(self._title)
        self._block = QTextBrowser()
        self._block.setObjectName("bestiaryStatblock")
        self._block.setOpenLinks(False)
        right.addWidget(self._block, 1)
        root.addLayout(right, 1)

        # typing waits a moment, so the list isn't rebuilt on every key
        self._timer = QTimer(self); self._timer.setSingleShot(True); self._timer.setInterval(150)
        self._timer.timeout.connect(self._refresh)
        self._search.textChanged.connect(lambda _t: self._timer.start())
        for box in (self._kind, self._size, self._cr_min, self._cr_max):
            box.currentIndexChanged.connect(lambda _i: self._refresh())
        self._list.currentItemChanged.connect(lambda cur, _prev: self._show(cur.text() if cur else ""))
        self._refresh()

    def _refresh(self):
        names = _b.search(self._search.text(), self._kind.currentData(), self._size.currentData(),
                          self._cr_min.currentData(), self._cr_max.currentData())
        keep = self._list.currentItem().text() if self._list.currentItem() else ""
        self._list.blockSignals(True)
        self._list.clear()
        for n in names:
            it = QListWidgetItem(n)
            c = get_creature(n)
            it.setToolTip(_b.summary_line(c))
            self._list.addItem(it)
        self._list.blockSignals(False)
        self._count.setText(f"{len(names):,} creature{'s' if len(names) != 1 else ''}")
        if not names:
            self._show("")
            return
        rows = self._list.findItems(keep, Qt.MatchExactly) if keep else []
        self._list.setCurrentItem(rows[0] if rows else self._list.item(0))

    def _show(self, name: str):
        c = get_creature(name) if name else None
        self._title.setText(name if c else "")
        self._block.setHtml(_b.statblock_html(c, GOLD2) if c else
                            f'<span style="color:{TEXT3}">No creature matches. Try fewer words or another filter.</span>')

    def show_creature(self, name: str):
        """Open on one creature (a summon, a Wild Shape form)."""
        self._search.setText(name)
        self._refresh()
        rows = self._list.findItems(name, Qt.MatchExactly)
        if rows:
            self._list.setCurrentItem(rows[0])
