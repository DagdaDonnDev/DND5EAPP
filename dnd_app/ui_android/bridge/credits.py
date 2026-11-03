"""Credits bridge -- the Android side of desktop's CreditsDialog
(ui_desktop/pages/main_window.py). Both show the project's README.md,
cleaned up for Qt's Markdown viewer by core/readme.py, rather than a
separate credits blurb that would drift out of sync with it.
"""
from PySide6.QtCore import QObject, Property

from dnd_app.core.readme import readme_text


class CreditsBridge(QObject):
    """Stateless -- the README doesn't change while the app is running,
    so this is read once and exposed as a constant property."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = readme_text()

    @Property(str, constant=True)
    def readmeText(self):
        return self._text
