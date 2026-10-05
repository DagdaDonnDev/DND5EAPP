from PySide6.QtCore import QObject, Property, Slot

from dnd_app.core.app_settings import get_app_theme, set_app_theme


class AppSettingsBridge(QObject):
    """App-level settings persisted outside any character file -- just
    the Start Menu / mid-wizard theme default today. See
    core/app_settings.py's module docstring for why this needs to be
    separate from CharacterSheetBridge.theme/setTheme, which read/write
    a specific character's own char["theme"]."""

    @Property(str)
    def theme(self):
        return get_app_theme()

    @Slot(str)
    def setTheme(self, name: str):
        set_app_theme(name)
