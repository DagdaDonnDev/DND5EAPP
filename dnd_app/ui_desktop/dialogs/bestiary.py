"""The Bestiary window (Tools → Bestiary, Ctrl+B): every creature MIMIC
knows, to find by name or type and filter by type, size, challenge
rating and how it moves, with its stat block beside the list. The finding
and the stat block are core/bestiary.py's, the same as Android's Bestiary
screen. A character's own creatures (mounts, steeds, summons, companions,
Wild Shape) are on its sheet's Creatures tab (pages/sheet/companions.py).
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
        all_page = self
        root = QHBoxLayout(self); root.setContentsMargins(14, 14, 14, 14); root.setSpacing(12)

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

    def show_creature(self, name: str):
        """Open on one creature (a summon, a Wild Shape form)."""
        self._search.setText(name)
        self._refresh()
        rows = self._list.findItems(name, Qt.MatchExactly)
        if rows:
            self._list.setCurrentItem(rows[0])


def show_creature_details(parent, name: str):
    """A creature's magnifying glass: its stat block in a window of its
    own, as an item's or a spell's glass opens its details."""
    c = get_creature(name)
    if not c:
        return
    win = parent.window() if parent is not None else None
    dlg = QDialog(win)
    dlg.setWindowTitle(name)
    dlg.resize(640, 720)
    lay = QVBoxLayout(dlg)
    view = QTextBrowser(); view.setOpenLinks(False)
    view.setObjectName("creatureDetails")
    view.setHtml(_b.statblock_html(c, GOLD2))
    lay.addWidget(view)
    buttons = QDialogButtonBox(QDialogButtonBox.Close)
    buttons.rejected.connect(dlg.reject)
    lay.addWidget(buttons)
    dlg.setAttribute(Qt.WA_DeleteOnClose)
    dlg.show()
    return dlg


def pick_group(parent, name: str, groups) -> str:
    """Add's popup: the creature's name at the top, a button for each
    group to put it in, Cancel at the bottom. Returns the group, or ""."""
    win = parent.window() if parent is not None else None
    dlg = QDialog(win); dlg.setObjectName("pickGroupDialog")
    dlg.setWindowTitle(f"Add {name}")
    dlg.setStyleSheet(f"QDialog#pickGroupDialog{{background:{SURF};}}")
    lay = QVBoxLayout(dlg); lay.setContentsMargins(18, 16, 18, 14); lay.setSpacing(8)
    lay.addWidget(_h(name, GOLD2, FS_HEAD, True))
    lay.addWidget(_h("Add it to which group?", TEXT2, FS_SMALL))
    picked = {"g": ""}
    for g in groups:
        b = QPushButton(g); b.setObjectName(f"pickGroup_{g}")
        b.setMinimumHeight(36); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"QPushButton{{background:{SURF2};border:1px solid {BORDER2};border-radius:8px;color:{TEXT};"
                        f"font-size:{FS_BODY}px;font-weight:700;}}"
                        f"QPushButton:hover{{border-color:{TEAL};background:{qa(TEAL, 0x22)};}}")
        b.clicked.connect(lambda checked=False, gg=g: (picked.__setitem__("g", gg), dlg.accept()))
        lay.addWidget(b)
    lay.addSpacing(6)
    from dnd_app.ui_desktop.shared import _btn
    # backing out: red, as the other negative buttons
    cancel = _btn("Cancel", CRIMSON, variant="danger", height=36, border_width=1,
                  bg_alpha=0x22, border_alpha=0x88, text_color=CRIM2, hover_text="white",
                  font_size=FS_BODY, radius=8)
    cancel.setObjectName("pickGroupCancel")
    cancel.clicked.connect(dlg.reject)
    lay.addWidget(cancel)
    dlg.setMinimumWidth(280)
    dlg.exec()
    return picked["g"]


class CreatureBrowser(QWidget):
    """The Bestiary as a browser beside your own list, the way the Spell
    Browser sits beside My Spells and the item browsers beside your
    inventory: the search box with its magnifying glass, the filters
    behind the funnel, a row per creature (type and challenge rating) with
    the glass that opens its stat block and Add beside it.
    on_add(name) -- what Add (or a double-click) does with the creature;
    with `groups`, on_add(name, group), the group picked in a popup."""

    def __init__(self, on_add, add_text="Add Selected", parent=None, groups=(), group="Other"):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        from PySide6.QtGui import QIcon
        from dnd_app.ui_desktop import icons as _icons
        from dnd_app.ui_desktop.widgets import FilterSidebar, InspectButtonDelegate
        from dnd_app.ui_desktop.shared import pill_btn
        from dnd_app.ui_desktop.style.theme import on_fill
        self._on_add = on_add
        lay = QVBoxLayout(self); lay.setContentsMargins(8, 8, 8, 8); lay.setSpacing(6)
        self.search = QLineEdit()
        self.search.setObjectName("creatureBrowserSearch")
        self.search.setPlaceholderText("Search creatures…")
        self.search.setClearButtonEnabled(True)
        self.search.setAccessibleName("Search creatures by name or type")
        _icons.set_action_icon(self.search.addAction(QIcon(), QLineEdit.LeadingPosition), "search")
        self.search.setStyleSheet(f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};"
                                  f"border-radius:6px;padding:4px 8px;color:{TEXT};}}")
        self._kind = _combo(_b.kinds(), "Any type", "Creature type")
        self._size = _combo(SIZES, "Any size", "Size")
        self._cr_min = _combo(_b.CR_ORDER, "CR from", "Lowest challenge rating")
        self._cr_max = _combo(_b.CR_ORDER, "CR to", "Highest challenge rating")
        self._move = _combo([label for label, _ in _b.MOVES], "Any movement", "How it moves")
        self._filters = FilterSidebar(self)
        for label, box in (("Type", self._kind), ("Size", self._size), ("CR from", self._cr_min),
                           ("CR to", self._cr_max), ("Moves", self._move)):
            self._filters.add_combo(label, box)
        lay.addLayout(self._filters.search_row(self.search))
        self.count = _h("", TEXT3, FS_TINY)
        lay.addWidget(self.count)
        self.tree = QTreeWidget()
        self.tree.setObjectName("creatureBrowserList")
        self.tree.setHeaderLabels(["Name", "Type", "CR", "", ""])
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree.setStyleSheet(
            f"QTreeWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;"
            f"alternate-background-color:{SURF};}}"
            f"QTreeWidget::item{{padding:4px 2px;font-size:{FS_BODY}px;color:{TEXT};}}"
            f"QTreeWidget::item:selected{{background:{TEAL};color:#0a0d12;font-weight:700;}}"
            f"QTreeWidget::item:selected:!active{{background:{TEAL};color:#0a0d12;}}")
        hdr = self.tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive); self.tree.setColumnWidth(1, 120)
        hdr.setSectionResizeMode(2, QHeaderView.Fixed); self.tree.setColumnWidth(2, 48)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed); self.tree.setColumnWidth(3, 32)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed); self.tree.setColumnWidth(4, 48)
        hdr.setStyleSheet(f"QHeaderView::section{{background:{SURF2};color:{GOLD2};font-weight:700;"
                          f"font-size:{FS_SMALL}px;padding:6px;border:1px solid {BORDER};}}")
        self.tree.setItemDelegateForColumn(3, InspectButtonDelegate(
            self.tree, lambda n: show_creature_details(self, n), selected_icon="#0a0d12", column=3))
        # Add, to the right of the glass: which group, in a popup
        from dnd_app.ui_desktop.widgets import AddButtonDelegate
        self.tree.setItemDelegateForColumn(4, AddButtonDelegate(
            self.tree, self._add_name, selected_icon="#0a0d12", column=4))
        self.tree.itemDoubleClicked.connect(lambda it, _c: self._add(it))
        lay.addWidget(self.tree, 1)
        self._groups = tuple(groups)
        self._timer = QTimer(self); self._timer.setSingleShot(True); self._timer.setInterval(150)
        self._timer.timeout.connect(self.refresh)
        self.search.textChanged.connect(lambda _t: self._timer.start())
        for box in (self._kind, self._size, self._cr_min, self._cr_max, self._move):
            box.currentIndexChanged.connect(lambda _i: self.refresh())
        self.refresh()

    def refresh(self):
        names = _b.search(self.search.text(), self._kind.currentData(), self._size.currentData(),
                          self._cr_min.currentData(), self._cr_max.currentData(), self._move.currentData())
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        rows = []
        for n in names:
            c = get_creature(n) or {}
            it = QTreeWidgetItem([n, c.get("type", ""), c.get("cr", ""), "", ""])
            it.setData(0, Qt.UserRole, n)
            it.setToolTip(0, _b.summary_line(c) if c else n)
            rows.append(it)
        self.tree.addTopLevelItems(rows)
        self.tree.setUpdatesEnabled(True)
        self.count.setText(f"{len(names):,} creature{'s' if len(names) != 1 else ''}")

    def _add(self, item):
        if item is not None and item.data(0, Qt.UserRole):
            self._add_name(item.data(0, Qt.UserRole))

    def _add_name(self, name):
        """Add (the row's button, or a double-click): the group from the
        popup when there are groups to put it in."""
        if self._groups:
            group = pick_group(self, name, self._groups)
            if group:
                self._on_add(name, group)
        else:
            self._on_add(name)


def show_plain_details(parent, name: str, sb: dict):
    win = parent.window() if parent is not None else None
    dlg = QDialog(win); dlg.setWindowTitle(name); dlg.resize(560, 620)
    lay = QVBoxLayout(dlg)
    view = QTextBrowser(); view.setOpenLinks(False); view.setObjectName("plainDetails")
    view.setHtml(_b.plain_statblock_html(name, sb, GOLD2))
    lay.addWidget(view)
    buttons = QDialogButtonBox(QDialogButtonBox.Close); buttons.rejected.connect(dlg.reject)
    lay.addWidget(buttons)
    dlg.setAttribute(Qt.WA_DeleteOnClose); dlg.show()
    return dlg


class MountVehicleBrowser(QWidget):
    """Mounts and vehicles beside the Bestiary on the Creatures page: the
    mounts you can buy and every vehicle, grouped, each with the glass for
    its stat block and Add beside it -- a mount goes in Mounts, a vehicle
    in Vehicles. on_add(name, "mount" | "vehicle")."""

    def __init__(self, on_add, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        from PySide6.QtGui import QIcon
        from dnd_app.ui_desktop import icons as _icons
        from dnd_app.ui_desktop.widgets import InspectButtonDelegate
        from dnd_app.ui_desktop.shared import pill_btn
        from dnd_app.ui_desktop.style.theme import on_fill
        self._on_add = on_add
        lay = QVBoxLayout(self); lay.setContentsMargins(8, 8, 8, 8); lay.setSpacing(6)
        self.search = QLineEdit(); self.search.setObjectName("mountVehicleSearch")
        self.search.setPlaceholderText("Search mounts and vehicles…")
        self.search.setClearButtonEnabled(True)
        _icons.set_action_icon(self.search.addAction(QIcon(), QLineEdit.LeadingPosition), "search")
        self.search.setStyleSheet(f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};"
                                  f"border-radius:6px;padding:4px 8px;color:{TEXT};}}")
        self.search.textChanged.connect(lambda _t: self.refresh())
        lay.addWidget(self.search)
        self.tree = QTreeWidget(); self.tree.setObjectName("mountVehicleList")
        self.tree.setHeaderLabels(["Name", "Speed", "", ""])
        self.tree.setIndentation(14)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree.setStyleSheet(
            f"QTreeWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;alternate-background-color:{SURF};}}"
            f"QTreeWidget::item{{padding:4px 2px;font-size:{FS_BODY}px;color:{TEXT};}}"
            f"QTreeWidget::item:selected{{background:{TEAL};color:#0a0d12;font-weight:700;}}"
            f"QTreeWidget::item:selected:!active{{background:{TEAL};color:#0a0d12;}}")
        hdr = self.tree.header(); hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive); self.tree.setColumnWidth(1, 170)
        hdr.setSectionResizeMode(2, QHeaderView.Fixed); self.tree.setColumnWidth(2, 32)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed); self.tree.setColumnWidth(3, 48)
        hdr.setStyleSheet(f"QHeaderView::section{{background:{SURF2};color:{GOLD2};font-weight:700;"
                          f"font-size:{FS_SMALL}px;padding:6px;border:1px solid {BORDER};}}")
        self.tree.setItemDelegateForColumn(2, InspectButtonDelegate(
            self.tree, self._inspect, selected_icon="#0a0d12", column=2,
            has_details=lambda d: bool(d) and d != "__section__"))
        # Add, to the right of the glass: a mount into Mounts, a vehicle into Vehicles
        from dnd_app.ui_desktop.widgets import AddButtonDelegate
        self.tree.setItemDelegateForColumn(3, AddButtonDelegate(
            self.tree, lambda n: self._add(self._find(n)), selected_icon="#0a0d12", column=3,
            has_details=lambda d: bool(d) and d != "__section__"))
        self.tree.itemDoubleClicked.connect(lambda it, _c: self._add(it))
        lay.addWidget(self.tree, 1)
        self.refresh()

    @staticmethod
    def sections():
        from dnd_app.data import items as I
        return [("Mounts", "mount", [r[0] for r in I.MOUNTS]),
                ("Land vehicles", "vehicle", I.VEHICLES_LAND), ("Water vehicles", "vehicle", I.VEHICLES_WATER),
                ("Air vehicles", "vehicle", I.VEHICLES_AIR), ("Spelljamming vessels", "vehicle", I.VEHICLES_SPELLJAMMING),
                ("Astral vehicles", "vehicle", I.VEHICLES_ASTRAL), ("Combat vehicles", "vehicle", I.VEHICLES_BGDIA),
                ("Magic item vehicles", "vehicle", I.VEHICLES_MAGIC)]

    @staticmethod
    def statblock(name, kind):
        from dnd_app.data.statblocks import get_mount_statblock, get_vehicle_statblock
        return (get_mount_statblock(name) if kind == "mount" else get_vehicle_statblock(name)) or {}

    def refresh(self):
        q = self.search.text().strip().lower()
        self.tree.clear()
        bold = self.tree.font(); bold.setBold(True)
        for title, kind, names in self.sections():
            hits = [n for n in names if not q or q in n.lower()]
            if not hits:
                continue
            head = QTreeWidgetItem([title]); head.setFont(0, bold)
            head.setForeground(0, __import__("PySide6.QtGui", fromlist=["QColor"]).QColor(GOLD2))
            head.setData(0, Qt.UserRole, "__section__")
            for n in hits:
                sb = self.statblock(n, kind)
                it = QTreeWidgetItem([n, str(sb.get("speed", "") or "—"), "", ""])
                it.setData(0, Qt.UserRole, n); it.setData(0, Qt.UserRole + 1, kind)
                head.addChild(it)
            self.tree.addTopLevelItem(head)
            head.setFirstColumnSpanned(True); head.setExpanded(True)

    def _find(self, name):
        for i in range(self.tree.topLevelItemCount()):
            head = self.tree.topLevelItem(i)
            for j in range(head.childCount()):
                if head.child(j).data(0, Qt.UserRole) == name:
                    return head.child(j)
        return None

    def _inspect(self, name):
        it = self._find(name)
        if it is not None:
            show_plain_details(self, name, self.statblock(name, it.data(0, Qt.UserRole + 1)))

    def _add(self, item):
        if item is None or item.data(0, Qt.UserRole) in (None, "__section__"):
            return
        self._on_add(item.data(0, Qt.UserRole), item.data(0, Qt.UserRole + 1))
