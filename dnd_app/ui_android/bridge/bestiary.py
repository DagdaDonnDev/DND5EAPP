"""Bestiary bridge -- the Android side of desktop's Bestiary window
(ui_desktop/dialogs/bestiary.py). Finding a creature and its stat block
are core/bestiary.py's, so both apps show the same.
"""
from PySide6.QtCore import QObject, Property, Signal, Slot

from dnd_app.core import bestiary as _b
from dnd_app.data.bestiary import SIZES, get_creature


class BestiaryBridge(QObject):
    resultsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []

    @Property(list, constant=True)
    def kinds(self):
        return _b.kinds()

    @Property(list, constant=True)
    def sizes(self):
        return list(SIZES)

    @Property(list, constant=True)
    def crs(self):
        return list(_b.CR_ORDER)

    @Property(list, constant=True)
    def bookCodes(self):
        """[{code, book}] for the Reference popup (data/books.py)."""
        from dnd_app.data.books import book_rows
        return [{"code": c, "book": b} for c, b in book_rows()]

    @Property(list, constant=True)
    def moves(self):
        """"Flies", "Swims"... for the movement filter."""
        return [label for label, _ in _b.MOVES]

    @Property(list, notify=resultsChanged)
    def results(self):
        """[{name, line}] for the list: 'Medium Beast · CR 1/4'."""
        return self._results

    @Slot(str, str, str, str, str)
    def search(self, text, kind, size, cr_min, cr_max):
        self.searchMoving(text, kind, size, cr_min, cr_max, "")

    @Slot(str, str, str, str, str, str)
    def searchMoving(self, text, kind, size, cr_min, cr_max, move):
        names = _b.search(text, kind, size, cr_min, cr_max, move)
        self._results = [{"name": n, "line": _b.summary_line(get_creature(n))} for n in names]
        self.resultsChanged.emit()

    @Slot(str, str, str, str, str, str, result=list)
    def find(self, text, kind, size, cr_min, cr_max, move):
        """The same search, handed back rather than kept: the Creatures
        page's own browser, which mustn't change the Bestiary screen's list."""
        return [{"name": n, "line": _b.summary_line(get_creature(n))}
                for n in _b.search(text, kind, size, cr_min, cr_max, move)]

    @Slot(str, str, result=str)
    def statblock(self, name, heading):
        """A creature's stat block as rich text (Text.StyledText)."""
        return _b.creature_html(name, heading)
