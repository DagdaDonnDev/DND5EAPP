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

    @Property(list, notify=resultsChanged)
    def results(self):
        """[{name, line}] for the list: 'Medium Beast · CR 1/4'."""
        return self._results

    @Slot(str, str, str, str, str)
    def search(self, text, kind, size, cr_min, cr_max):
        names = _b.search(text, kind, size, cr_min, cr_max)
        self._results = [{"name": n, "line": _b.summary_line(get_creature(n))} for n in names]
        self.resultsChanged.emit()

    @Slot(str, str, result=str)
    def statblock(self, name, heading):
        """A creature's stat block as rich text (Text.StyledText)."""
        return _b.creature_html(name, heading)
