from PySide6.QtCore import QObject, Property, Signal, Slot

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

    # ── Immersive Health / Immersive Exhaustion (core/immersive.py) ──
    immersiveChanged = Signal()

    @Property("QVariantList", constant=True)
    def immersiveModes(self):
        from dnd_app.core.immersive import MODES
        return list(MODES)

    @Property(str, notify=immersiveChanged)
    def immersiveHealth(self):
        from dnd_app.core.immersive import mode
        return mode("health")

    @Property(str, notify=immersiveChanged)
    def immersiveExhaustion(self):
        from dnd_app.core.immersive import mode
        return mode("exhaustion")

    @Slot(str, str)
    def setImmersive(self, kind: str, value: str):
        """kind: "health" or "exhaustion"; value: Full, Reduced or Off."""
        from dnd_app.core.immersive import set_mode
        set_mode(kind, value)
        self.immersiveChanged.emit()

    @Slot(str, result="QVariant")
    def immersiveInfo(self, kind: str):
        """{name, what, reduced} for a setting ("prompt" for the one-time
        note) -- the same words the desktop uses."""
        from dnd_app.core.immersive import SETTINGS, MODE_HELP, PROMPT_TITLE, PROMPT_TEXT
        name, what = (PROMPT_TITLE, PROMPT_TEXT) if kind == "prompt" else SETTINGS.get(kind, ("", ""))
        return {"name": name, "what": what, "reduced": MODE_HELP["Reduced"]}
