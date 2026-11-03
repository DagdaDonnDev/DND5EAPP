"""Desktop rendering of the shared line icons (icon_data.ICON_PATHS).

Icons replace the emoji the UI used to show. Every icon is a single colour:
the active theme's accent, IND2 (blue in Obsidian, emerald in Dragon's
Hoard, navy in Arcane Scroll, ...). Drawn with QPainter rather than loaded
as .svg because the Windows build deliberately excludes QtSvg (see
packaging/windows/MIMIC.spec).

Widgets that show an icon register through set_button_icon()/
set_tab_icon()/set_label_icon()/set_action_icon(), and theme.apply_theme()
calls refresh_all() so they repaint in the new accent the moment the theme
changes -- including screens that aren't rebuilt on a theme switch (Start
Menu, menu bar, wizard).
"""
import re
import weakref

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap

import dnd_app.ui_desktop.style.theme as _theme
from dnd_app.data.icon_data import (CHEESE_PALETTE, CHEESE_PIXELS, CUT_WIDTH, CUT_WIDTHS, ICON_CUTS, ICON_FILLS,
                                          ICON_PATHS, STROKE)

_TOKEN = re.compile(r"[MLQCZ]|-?\d*\.?\d+")


def _parse(d: str) -> QPainterPath:
    path = QPainterPath()
    toks = _TOKEN.findall(d)
    i = 0
    nums = lambda n: [float(t) for t in toks[i + 1:i + 1 + n]]
    while i < len(toks):
        op = toks[i]
        if op == "M":
            path.moveTo(*nums(2)); i += 3
        elif op == "L":
            path.lineTo(*nums(2)); i += 3
        elif op == "Q":
            a = nums(4); path.quadTo(QPointF(a[0], a[1]), QPointF(a[2], a[3])); i += 5
        elif op == "C":
            a = nums(6); path.cubicTo(QPointF(a[0], a[1]), QPointF(a[2], a[3]), QPointF(a[4], a[5])); i += 7
        elif op == "Z":
            path.closeSubpath(); i += 1
        else:
            raise ValueError(f"unexpected token {op!r} in icon path")
    return path


_PATHS = {name: _parse(d) for name, d in ICON_PATHS.items()}
_FILLS = {name: _parse(d) for name, d in ICON_FILLS.items()}
for _fp in _FILLS.values():
    # non-zero, as Qt Quick's Canvas fills on Android: overlapping solid
    # parts (a cross, a bird's head on its body) stay solid
    _fp.setFillRule(Qt.WindingFill)
_CUTS = {name: _parse(d) for name, d in ICON_CUTS.items()}


def accent() -> str:
    return _theme.IND2


def _resolve(color):
    """A colour may be given as a theme key ("GREEN2", "CRIM2") so it's
    re-read from the active theme on every repaint, or as a fixed colour."""
    if color is None:
        return accent()
    return getattr(_theme, color, color) if color.isupper() else color


def _dpr() -> float:
    app = QGuiApplication.instance()
    return app.devicePixelRatio() if app is not None else 1.0


def pixmap(name: str, size: int, color: str = None) -> QPixmap:
    dpr = _dpr()
    pm = QPixmap(round(size * dpr), round(size * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 24.0, size / 24.0)
    color = _resolve(color)
    pen = QPen(QColor(color), STROKE)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPath(_PATHS[name])
    if name in _FILLS:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
        p.drawPath(_FILLS[name])
    if name in _CUTS:
        # carve the detail lines out of the solid shape
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        cut = QPen(Qt.black, CUT_WIDTHS.get(name, CUT_WIDTH))
        cut.setCapStyle(Qt.RoundCap)
        cut.setJoinStyle(Qt.RoundJoin)
        p.setPen(cut)
        p.setBrush(Qt.NoBrush)
        p.drawPath(_CUTS[name])
    p.end()
    return pm


def icon(name: str, size: int = 24, color: str = None) -> QIcon:
    return QIcon(pixmap(name, size, color))


def scaled(n: int) -> int:
    """An icon size that follows the Settings "UI text size" scale."""
    return max(10, round(n * _theme._font_scale))


# ── Live theme updates ──────────────────────────────────────────────────
_registry = []   # (weakref to owner, callable(owner) that re-applies the icon)


def _register(owner, apply):
    apply(owner)
    try:
        _registry.append((weakref.ref(owner), apply))
    except TypeError:
        pass


def refresh_all():
    """Re-apply every registered icon in the current theme's accent.
    Called by theme.apply_theme()."""
    alive = []
    for ref, apply in _registry:
        owner = ref()
        if owner is None:
            continue
        try:
            apply(owner)
        except RuntimeError:      # underlying C++ object already deleted
            continue
        alive.append((ref, apply))
    _registry[:] = alive


def set_button_icon(button, name: str, size: int = 16, color: str = None):
    """QAbstractButton (QPushButton, QToolButton, QCheckBox, ...). `color`
    overrides the accent -- for a button whose own background IS the
    accent (pill_btn), where an accent icon would vanish; pass its text
    colour instead."""
    n = scaled(size)

    def apply(b):
        b.setIcon(icon(name, n, color))
        b.setIconSize(QSize(n, n))
    _register(button, apply)


def with_icon(button, name: str, size: int = 16, color: str = None):
    """set_button_icon(), returning the button -- for inline use."""
    set_button_icon(button, name, size, color)
    return button


def set_action_icon(action, name: str):
    """QAction (menus, menu bar, QLineEdit leading actions)."""
    _register(action, lambda a: a.setIcon(icon(name, 24)))


def set_label_icon(label, name: str, size: int = 16, color: str = None):
    """QLabel showing only an icon."""
    n = scaled(size)

    def apply(lbl):
        lbl.setPixmap(pixmap(name, n, color))
        lbl.setFixedSize(n, n)
    _register(label, apply)


def set_tab_icon(tabs, page, name: str, size: int = 17):
    """Icon for the tab holding `page` in QTabWidget `tabs` -- found by page
    rather than index, since tabs can be inserted later (Infusions)."""
    n = scaled(size)

    def apply(t):
        idx = t.indexOf(page)
        if idx >= 0:
            t.setTabIcon(idx, icon(name, n))
            t.setIconSize(QSize(n, n))
    _register(tabs, apply)


def icon_label(name: str, size: int = 16, color: str = None):
    """A new QLabel showing just `name`, kept in the theme's accent (or
    `color`, e.g. "GREEN2" for the advantage die)."""
    from PySide6.QtWidgets import QLabel
    lbl = QLabel()
    # border:none too -- a QLabel is a QFrame, so a parent card's
    # "QFrame{border:...}" rule would otherwise box the icon
    lbl.setStyleSheet("background:transparent;border:none;")
    set_label_icon(lbl, name, size, color)
    return lbl


def icon_header(name: str, text_label, size: int = 15, spacing: int = 6, center: bool = False):
    """[icon] [text_label] row, for headings that used to start with an
    emoji. Left-aligned unless `center`. Returns a QWidget."""
    from PySide6.QtWidgets import QHBoxLayout, QWidget
    w = QWidget()
    w.setStyleSheet("background:transparent;border:none;")
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(spacing)
    if center:
        row.addStretch()
    row.addWidget(icon_label(name, size), 0, Qt.AlignVCenter)
    # QLabel is a QFrame: without this, a parent card's "QFrame{border:..}"
    # rule draws a box around the heading text
    text_label.setStyleSheet(text_label.styleSheet() + "border:none;")
    row.addWidget(text_label, 0, Qt.AlignVCenter)
    row.addStretch()
    return w


def cheese_pixmap(scale: int = 3) -> QPixmap:
    """The pixel-art cheese for the "type cheese" easter egg, each art pixel
    drawn as a crisp scale x scale square."""
    h, w = len(CHEESE_PIXELS), len(CHEESE_PIXELS[0])
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    for y, row in enumerate(CHEESE_PIXELS):
        for x, ch in enumerate(row):
            if ch in CHEESE_PALETTE:
                img.setPixelColor(x, y, QColor(CHEESE_PALETTE[ch]))
    return QPixmap.fromImage(img.scaled(w * scale, h * scale, Qt.IgnoreAspectRatio, Qt.FastTransformation))
