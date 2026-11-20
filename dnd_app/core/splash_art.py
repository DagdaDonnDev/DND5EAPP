"""The startup animation (both apps): the mimic chest of splash.gif, in the
colours of a theme.

The art itself is never changed. Behind it goes the theme's background and a
glow in its accent colour (brightest while the mimic bites); the platform's
stones take the theme's border colour, keeping their shading; and the last
frame, where it has settled back into a chest, carries the name, and
stays a moment (HOLD). It plays at the GIF's own speed, inside a border
in the theme's colours.

frame(theme, i) -> QImage, made when first asked for and kept; delays() ->
each frame's time on screen in ms. Each frame takes a few ms to make, so a
player asks for the next one as it goes rather than all of them up front.
"""
import os

from PySide6.QtGui import QImageReader, QImage, QPainter, QColor, QFont, QRadialGradient, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF

# (here in core, not with the desktop code, so the Android build has it too)
GIF = os.path.join(os.path.dirname(__file__), "splash.gif")
SPEED = 1.0
# how long the last frame (the name) stays before the app shows, in ms
HOLD = 1200
SIZE = 720

# the platform's stones, and how much lighter or darker than the theme's
# border colour each becomes
_STONE = {"#3f515b": 0.0, "#445b67": 0.10, "#192024": -0.55, "#566065": 0.18}
# the frames where its mouth is open, and around them
_BITE = range(25, 35)
_AWAKE = range(18, 41)

_raw = None
_cache = {}


def _frames():
    global _raw
    if _raw is None:
        _raw = []
        r = QImageReader(GIF)
        while True:
            im = r.read()
            if im.isNull():
                break
            _raw.append((im.convertToFormat(QImage.Format_ARGB32), max(20, r.nextImageDelay())))
    return _raw


def _palette(theme: str) -> dict:
    from dnd_app.data.themes import THEMES
    return THEMES.get(theme) or THEMES["(Dark) Obsidian"]


def _stone(t: dict, shade: float) -> QColor:
    h, s, l, _ = QColor(t["BORDER"]).getHsl()
    return QColor.fromHsl(max(h, 0), s, max(0, min(255, int(l * (1 + shade)))))


def _recolour(img: QImage, t: dict) -> QImage:
    """The art with its stones in the theme's colour: an exact swap of the
    few stone colours, pixel for pixel (4-byte BGRA words)."""
    out = img.copy()
    bits = out.bits()
    buf = bytes(bits)
    for name, shade in _STONE.items():
        a, b = QColor(name), _stone(t, shade)
        buf = buf.replace(bytes([a.blue(), a.green(), a.red(), 255]),
                          bytes([b.blue(), b.green(), b.red(), 255]))
    bits[:] = buf
    return out


def _compose(i: int, art: QImage, t: dict, last: bool) -> QImage:
    out = QImage(SIZE, SIZE, QImage.Format_ARGB32)
    out.fill(QColor(t["BG"]))
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    strength = 150 if i in _BITE else (95 if i in _AWAKE else 55)
    g = QRadialGradient(QPointF(SIZE / 2, SIZE * 0.46), SIZE * 0.32)
    c = QColor(t["INDIGO"]); c.setAlpha(strength)
    g.setColorAt(0, c); c2 = QColor(c); c2.setAlpha(0); g.setColorAt(1, c2)
    p.fillRect(out.rect(), QBrush(g))
    p.drawImage(0, -30, art)
    # the border: the theme's accent edge round a rounded frame
    from PySide6.QtGui import QPen
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(t["BORDER2"]), 10))
    p.drawRoundedRect(QRectF(9, 9, SIZE - 18, SIZE - 18), 40, 40)
    p.setPen(QPen(QColor(t["INDIGO"]), 2))
    p.drawRoundedRect(QRectF(20, 20, SIZE - 40, SIZE - 40), 32, 32)
    if last:
        light = QColor(t["BG"]).lightness() > 128
        f = QFont(); f.setPixelSize(84); f.setBold(True); f.setLetterSpacing(QFont.AbsoluteSpacing, 10)
        p.setFont(f); p.setPen(QColor(t["GOLD"] if light else t["GOLD2"]))
        p.drawText(QRectF(0, 520, SIZE, 100), Qt.AlignCenter, "MIMIC")
        f2 = QFont(); f2.setPixelSize(24)
        p.setFont(f2); p.setPen(QColor(t["TEXT2"]))
        p.drawText(QRectF(0, 612, SIZE, 40), Qt.AlignCenter, "Loading…")
    p.end()
    return out


def frame(theme: str, i: int) -> QImage:
    key = (theme, i)
    if key not in _cache:
        t = _palette(theme)
        raw = _frames()
        _cache[key] = _compose(i, _recolour(raw[i][0], t), t, i == len(raw) - 1)
    return _cache[key]


def frame_count() -> int:
    return len(_frames())


def delays() -> list:
    """Each frame's time on screen, in ms, at the animation's speed."""
    return [max(15, int(d / SPEED)) for _, d in _frames()]
