"""The app's icon -- the d20 -- in each theme's colours (both apps).

The default theme, (Dark) Obsidian, keeps the icon as drawn. For the
others the die takes the theme's die colour (die_colour: a dark theme's
accent, Blood Moon's a classic bright red; a light theme its dark
partner's, so the d20 is the same in either mode): every die pixel keeps its own
shading, moved to the accent's hue, with the two face tones kept apart.
The ink outline keeps its darkness, tinted the same way, and the dark
backdrop of the Android icon becomes the theme's background, lighter in
the middle as before.

    recolour(img, theme) -> QImage      (img: the icon as drawn)
    slug(theme) -> "dragons_hoard"      (file and resource names)
    window_icon(theme) -> QIcon         (desktop: the window and taskbar)
    remember_launcher_icon(theme)       (Android: the launcher icon to
                                         switch to as the app closes)

packaging/make_theme_icons.py writes the files from these.
"""
import os
import re

from PySide6.QtGui import QImage, QColor

DEFAULT = "(Dark) Obsidian"
HERE = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(HERE, "theme_icons")
# the die's own colours, as drawn: its light face, and its backdrop
_FACE = QColor("#f0a02c")          # (between the two face tones)
_BACK = QColor("#0d0f18")
# a dark theme whose die is a set colour rather than its accent: the
# classic bright red d20
_DIE = {"(Dark) Blood Moon": "#e8202a"}


def die_colour(theme: str):
    """The die's colour for this theme: a dark theme's accent (its INDIGO,
    or a set colour above), and a light theme its dark partner's
    (data/themes.py DARK_PARTNER) -- the same d20 in either mode. None:
    the die as drawn (Obsidian's, and so Arcane Scroll's)."""
    from dnd_app.data.themes import DARK_PARTNER
    dark = DARK_PARTNER.get(theme, theme)
    if dark == DEFAULT:
        return None
    return _DIE.get(dark) or _palette(dark)["INDIGO"]


def slug(theme: str) -> str:
    name = re.sub(r"^\((Dark|Light)\)\s*", "", theme)
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def _palette(theme: str) -> dict:
    from dnd_app.data.themes import THEMES
    return THEMES.get(theme) or THEMES[DEFAULT]


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def _map(theme: str):
    """A function from an (r, g, b) of the drawn icon to its new colour."""
    t = _palette(theme)
    light = QColor(t["BG"]).lightnessF() > 0.5
    die = die_colour(theme)
    acc = QColor(die or "#000000")
    ah, as_, al, _ = acc.getHslF()
    fh, fs, fl, _ = _FACE.getHslF()
    bg, edge = QColor(t["BG"]), QColor(t["SURF2"] if not light else t["SURF"])
    back_l = _BACK.lightnessF()
    cache = {}

    def f(r, g, b):
        key = (r, g, b)
        if key in cache:
            return cache[key]
        c = QColor(r, g, b)
        h, s, l, _ = c.getHslF()
        if h < 0:
            h = 0
        warm = 0.0 <= h <= 0.15 and s > 0.25          # the die: faces and its ink
        if warm and die is None:
            out = c                                    # the die as drawn
        elif warm and l > 0.22:
            # a face: the accent's hue; its shading kept, moved to the
            # accent's lightness (a dark theme's accent lifted a little so
            # it reads as a die, not a shadow)
            target = _clamp(al, 0.30, 0.66)
            nl = _clamp(l - fl + target, 0.08, 0.92)
            ns = _clamp(s * (as_ / max(fs, 0.01)) if as_ > 0.05 else s * 0.15)
            out = QColor.fromHslF(ah if ah >= 0 else 0, ns, nl)
        elif warm:
            # the ink: as dark as before, in a deep shade of the accent
            out = QColor.fromHslF(ah if ah >= 0 else 0, _clamp(as_ * 0.6), _clamp(l * 0.9))
        else:
            # the backdrop: the theme's background, lighter (or, on a light
            # theme, a little deeper) towards the middle as drawn
            k = _clamp((l - back_l) / 0.10)
            a, b2 = (bg, edge)
            out = QColor.fromRgbF(a.redF() + (b2.redF() - a.redF()) * k,
                                  a.greenF() + (b2.greenF() - a.greenF()) * k,
                                  a.blueF() + (b2.blueF() - a.blueF()) * k)
        cache[key] = (out.red(), out.green(), out.blue())
        return cache[key]
    return f


def recolour(img: QImage, theme: str) -> QImage:
    """The icon in this theme's colours (the default theme's: as drawn).
    Transparency is kept as it is."""
    src = img.convertToFormat(QImage.Format_ARGB32)
    if theme == DEFAULT:
        return src
    out = src.copy()
    f = _map(theme)
    bits = out.bits()
    buf = bytearray(bytes(bits))
    for i in range(0, len(buf), 4):
        if buf[i + 3] == 0:
            continue
        b, g, r = buf[i], buf[i + 1], buf[i + 2]
        a = buf[i + 3]
        if a < 255:                       # (premultiplied-free ARGB32: plain values)
            pass
        nr, ng, nb = f(r, g, b)
        buf[i], buf[i + 1], buf[i + 2] = nb, ng, nr
    bits[:] = bytes(buf)
    return out


def icon_file(theme: str) -> str:
    """The desktop window icon for this theme ("" for the default: icon.ico)."""
    if theme == DEFAULT:
        return ""
    p = os.path.join(ICON_DIR, slug(theme) + ".png")
    return p if os.path.exists(p) else ""


def window_icon(theme: str):
    from PySide6.QtGui import QIcon
    p = icon_file(theme)
    if p:
        return QIcon(p)
    return QIcon(os.path.join(os.path.dirname(HERE), "ui_desktop", "icon.ico"))


def remember_launcher_icon(theme: str) -> None:
    """Android: the launcher icon to switch to, read by the app (as it goes
    to the background) from launcher_icon.txt in its private files. Off
    Android this does nothing."""
    root = os.environ.get("ANDROID_PRIVATE")
    if not root:
        return
    try:
        with open(os.path.join(root, "launcher_icon.txt"), "w") as fh:
            fh.write("default" if theme == DEFAULT else slug(theme))
    except OSError:
        pass
