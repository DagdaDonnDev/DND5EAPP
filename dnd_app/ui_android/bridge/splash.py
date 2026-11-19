"""The Android side of the startup animation: the mimic chest in the app
theme's colours, the same frames the desktop splash plays (core/splash_art.py).

SplashFrameProvider: "image://splash/<frame>" is that frame, in the app's
remembered theme. App.qml plays them over the Start Menu as the app opens,
timed by appSettingsBridge.splashDelays.
"""
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class SplashFrameProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, id_, size, requested_size):
        try:
            from dnd_app.core import splash_art
            from dnd_app.core.app_settings import get_app_theme
            return splash_art.frame(get_app_theme(), int(id_.split("/")[0]))
        except Exception:
            return QImage(1, 1, QImage.Format_ARGB32_Premultiplied)
