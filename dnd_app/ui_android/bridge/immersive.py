"""The Android side of Immersive Health and Immersive Exhaustion. The rules,
the settings and the frame's look are shared with the desktop app in
core/immersive.py; App.qml applies them.

ImmersiveFrameProvider hands App.qml the exhaustion frame as an image, drawn
by the same painter the desktop uses: "image://immersive/<level>/<setting>/
<width>x<height>/<scale>" -- a frame at that level and setting, for a page
area that size (logical pixels) at that pixel density.
"""
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from dnd_app.core.immersive import render_frame


class ImmersiveFrameProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, id_, size, requested_size):
        try:
            level, setting, wh, scale = id_.split("/")
            w, h = (int(float(v)) for v in wh.split("x"))
            # (capped at 2x: the frame is soft, and a phone at 3x would
            # mean a 9-megapixel image for no visible gain)
            img = render_frame(w, h, int(level), setting, phone=True, scale=min(2.0, float(scale)))
            img.setDevicePixelRatio(1.0)
            return img
        except (ValueError, ZeroDivisionError):
            return QImage(1, 1, QImage.Format_ARGB32_Premultiplied)
