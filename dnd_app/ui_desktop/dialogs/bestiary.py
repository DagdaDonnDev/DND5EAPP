"""The Bestiary window (Tools → Bestiary, Ctrl+B): every creature MIMIC
knows, to find by name or type and filter by type, size, challenge
rating and how it moves, with its stat block beside the list -- and, in
its Yours tab (Tools → Your Creatures, Ctrl+Shift+B), the open
character's own creatures: mounts, steeds, summons, companions and Wild
Shape. The finding and the stat block are core/bestiary.py's, the same as
Android's Bestiary screen; the Yours tab is the sheet's own creatures page
(pages/sheet/companions.py), so it changes with the sheet.
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

    def __init__(self, parent=None, sheet_of=None):
        super().__init__(parent, Qt.Window)
        self._sheet_of = sheet_of          # () -> the open CharacterSheet, or None
        self._yours_sheet = None
        self._yours_page = None
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
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8)
        self._tabs = QTabWidget(); self._tabs.setObjectName("bestiaryTabs")
        outer.addWidget(self._tabs)
        all_page = QWidget()
        root = QHBoxLayout(all_page); root.setContentsMargins(6, 10, 6, 6); root.setSpacing(12)
        self._tabs.addTab(all_page, "All creatures")
        self._yours_box = QWidget()
        self._yours_lay = QVBoxLayout(self._yours_box); self._yours_lay.setContentsMargins(0, 0, 0, 0)
        self._tabs.addTab(self._yours_box, "Yours")
        self._tabs.currentChanged.connect(lambda i: self.follow_sheet() if i == 1 else None)

        left = QVBoxLayout(); left.setSpacing(8)
        # the search box as the other browsers have it (a magnifying glass at
        # its start), and the filters behind the funnel button beside it
        from PySide6.QtGui import QIcon
        from dnd_app.ui_desktop import icons as _icons
        from dnd_app.ui_desktop.widgets import FilterSidebar, InspectButtonDelegate
        self._search = QLineEdit()
        self._search.setObjectName("bestiarySearch")
        self._search.setPlaceholderText("Search creatures…")
        self._search.setClearButtonEnabled(True)
        self._search.setAccessibleName("Search creatures by name or type")
        _icons.set_action_icon(self._search.addAction(QIcon(), QLineEdit.LeadingPosition), "search")
        self._search.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:7px;"
            f"padding:6px 10px;color:{TEXT};font-size:{FS_BODY}px;}}")
        self._kind = _combo(_b.kinds(), "Any type", "Creature type")
        self._size = _combo(SIZES, "Any size", "Size")
        self._cr_min = _combo(_b.CR_ORDER, "CR from", "Lowest challenge rating")
        self._cr_max = _combo(_b.CR_ORDER, "CR to", "Highest challenge rating")
        self._move = _combo([label for label, _ in _b.MOVES], "Any movement", "How it moves")
        for box, nm in ((self._kind, "bestiaryType"), (self._size, "bestiarySize"),
                        (self._cr_min, "bestiaryCrMin"), (self._cr_max, "bestiaryCrMax"),
                        (self._move, "bestiaryMove")):
            box.setObjectName(nm)
        self._filters = FilterSidebar(all_page)
        self._filters.add_combo("Type", self._kind)
        self._filters.add_combo("Size", self._size)
        self._filters.add_combo("CR from", self._cr_min)
        self._filters.add_combo("CR to", self._cr_max)
        self._filters.add_combo("Moves", self._move)
        left.addLayout(self._filters.search_row(self._search))
        self._count = _h("", TEXT3, FS_TINY)
        left.addWidget(self._count)
        self._list = QListWidget()
        self._list.setObjectName("bestiaryList")
        self._list.setUniformItemSizes(True)
        # a magnifying glass on each row, as the spell and magic item browsers
        # have: its stat block
        self._list.setItemDelegate(InspectButtonDelegate(self._list, self._inspect))
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
        for box in (self._kind, self._size, self._cr_min, self._cr_max, self._move):
            box.currentIndexChanged.connect(lambda _i: self._refresh())
        self._list.currentItemChanged.connect(lambda cur, _prev: self._show(cur.text() if cur else ""))
        self._refresh()

    def _refresh(self):
        names = _b.search(self._search.text(), self._kind.currentData(), self._size.currentData(),
                          self._cr_min.currentData(), self._cr_max.currentData(), self._move.currentData())
        keep = self._list.currentItem().text() if self._list.currentItem() else ""
        self._list.blockSignals(True)
        self._list.clear()
        for n in names:
            it = QListWidgetItem(n)
            it.setData(Qt.UserRole, n)
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

    def _inspect(self, name):
        rows = self._list.findItems(name, Qt.MatchExactly)
        if rows:
            self._list.setCurrentItem(rows[0])
        self._show(name)

    def _show(self, name: str):
        c = get_creature(name) if name else None
        self._title.setText(name if c else "")
        self._block.setHtml(_b.statblock_html(c, GOLD2) if c else
                            f'<span style="color:{TEXT3}">No creature matches. Try fewer words or another filter.</span>')

    def show_yours(self):
        """Open on the Yours tab."""
        self._tabs.setCurrentIndex(1)
        self.follow_sheet()

    def follow_sheet(self):
        """The Yours tab shows the open character's creatures page (made
        afresh for a new character; "open a character" without one)."""
        sheet = self._sheet_of() if self._sheet_of else None
        if sheet is self._yours_sheet and (self._yours_page is not None or sheet is None):
            return
        self._drop_yours()
        self._yours_sheet = sheet
        if sheet is None:
            self._yours_page = _h("Open a character to see its creatures here: its mounts and steeds, "
                                  "what it's summoned, its companions and its Wild Shape forms.", TEXT3, FS_SMALL)
            self._yours_page.setWordWrap(True)
        else:
            self._yours_page = sheet._build_companions_tab()
            # (a closed sheet's page goes with it)
            sheet.destroyed.connect(self._sheet_gone)
        self._yours_lay.addWidget(self._yours_page)

    def _sheet_gone(self, *_):
        self._yours_page = None             # (deleted with the sheet)
        self._yours_sheet = None
        self.follow_sheet()

    def _drop_yours(self):
        if self._yours_page is not None:
            self._yours_lay.removeWidget(self._yours_page)
            self._yours_page.setParent(None)
            self._yours_page.deleteLater()
            self._yours_page = None

    def show_creature(self, name: str):
        """Open on one creature (a summon, a Wild Shape form)."""
        self._tabs.setCurrentIndex(0)
        self._search.setText(name)
        self._refresh()
        rows = self._list.findItems(name, Qt.MatchExactly)
        if rows:
            self._list.setCurrentItem(rows[0])
