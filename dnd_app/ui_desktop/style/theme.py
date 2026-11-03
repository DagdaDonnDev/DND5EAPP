"""
Accessible dark theme — WCAG AA compliant.
Min font: 13px body, 15px labels, 18px headings, 24px+ stat numbers.
Contrast ratios: text on dark bg ≥ 4.5:1

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0f1117"   # page background
SURF    = "#181c28"   # card/panel surface
SURF2   = "#1e2336"   # raised surface
SURF3   = "#252a40"   # hover/selected surface
BORDER  = "#505670"   # subtle border — 2.6:1 on BG (was 1.6:1, too faint to read as an edge)
BORDER2 = "#4a5480"   # active border

TEXT    = "#eeeaf8"   # primary text  — 14.8:1 on BG
TEXT2   = "#b0acc8"   # secondary text — 7.2:1 on BG
TEXT3   = "#908fa9"   # muted text — 6.0:1 on BG, 4.5:1 on SURF3 (was 4.6:1/3.4:1, failed against raised surfaces)

GOLD    = "#d4a820"   # gold accent — 6.8:1 on BG
GOLD2   = "#f5cc50"   # bright gold

INDIGO  = "#5b7af5"   # primary blue — 4.7:1 on SURF
IND2    = "#8fa8ff"   # lighter blue — 7.1:1

TEAL    = "#18b28a"   # success/heal — 5.2:1
TEAL2   = "#22d4a8"   # bright teal

CRIMSON = "#d44040"   # danger — 5.1:1
CRIM2   = "#f06060"   # bright red

PURPLE  = "#8e50d8"   # magic — 4.8:1
PURP2   = "#b87cff"   # bright purple

AMBER   = "#e09020"   # warning — 5.4:1
AMBE2   = "#f5b040"   # bright amber

GREEN   = "#2ea854"   # success
GREEN2  = "#48d470"

PANELDK = "#212949"   # dark accent chrome (tab-bar gap, etc.) -- see THEMES

def qa(color: str, alpha) -> str:
    """Qt-style alpha hex: Qt QSS parses 8-digit hex as #AARRGGBB (alpha FIRST),
    unlike CSS #RRGGBBAA. qa(TEAL, 0x33) -> "#3318b28a"."""
    a = alpha if isinstance(alpha, str) else f"{alpha:02x}"
    return f"#{a}{color.lstrip('#')}"


# ── Font sizes (px) — WCAG compliant ─────────────────────────────────────────
# Base (100%/"Medium") sizes. The module-level FS_* names below are the
# live, scale-adjusted values every other module reads (directly via
# `from .theme import *`, or refreshed via sync_globals()) — set_font_scale()
# recomputes them in place so "Small"/"Large" in Settings actually changes
# rendered text size, instead of only being saved and never applied.
_BASE_FS = {
    "FS_TINY": 11,    # badge labels only
    "FS_SMALL": 13,   # secondary labels, hints
    "FS_BODY": 15,    # primary body text
    "FS_LABEL": 16,   # form labels, skill names
    "FS_HEAD": 18,    # section headers
    "FS_TITLE": 22,   # card titles
    "FS_STAT": 28,    # ability score numbers
    "FS_BIG": 36,     # AC, HP, major stats
}
from dnd_app.data.themes import THEMES, FONT_SCALES
_font_scale = 1.0

FS_TINY, FS_SMALL, FS_BODY, FS_LABEL, FS_HEAD, FS_TITLE, FS_STAT, FS_BIG = (
    _BASE_FS["FS_TINY"], _BASE_FS["FS_SMALL"], _BASE_FS["FS_BODY"], _BASE_FS["FS_LABEL"],
    _BASE_FS["FS_HEAD"], _BASE_FS["FS_TITLE"], _BASE_FS["FS_STAT"], _BASE_FS["FS_BIG"],
)


def set_font_scale(scale_name: str) -> None:
    """Recompute the module-level FS_* globals for the given Settings
    scale name ("Small"/"Medium (default)"/"Large"). Callers must still
    re-apply the theme (apply_theme()) and call sync_globals() in every
    already-built widget module for the change to actually render —
    this function only updates theme.py's own copy of the values.

    FS_TINY is deliberately excluded from scaling: it's used exclusively
    for badge/pill labels (source badges, reset badges, level pills) set
    in fixed-pixel containers as short as 16px tall with almost no
    padding to spare. Scaling it up would clip that text; scaling it
    down would make already-small badge text harder to read for no
    benefit. Every other size (body text, labels, headings, stat
    numbers) lives in normal flow layouts that can absorb the change."""
    global FS_SMALL, FS_BODY, FS_LABEL, FS_HEAD, FS_TITLE, FS_STAT, FS_BIG, _font_scale
    _font_scale = FONT_SCALES.get(scale_name, 1.0)
    FS_SMALL = max(1, round(_BASE_FS["FS_SMALL"] * _font_scale))
    FS_BODY  = max(1, round(_BASE_FS["FS_BODY"] * _font_scale))
    FS_LABEL = max(1, round(_BASE_FS["FS_LABEL"] * _font_scale))
    FS_HEAD  = max(1, round(_BASE_FS["FS_HEAD"] * _font_scale))
    FS_TITLE = max(1, round(_BASE_FS["FS_TITLE"] * _font_scale))
    FS_STAT  = max(1, round(_BASE_FS["FS_STAT"] * _font_scale))
    FS_BIG   = max(1, round(_BASE_FS["FS_BIG"] * _font_scale))



_active = dict(THEMES["(Dark) Obsidian"])

def apply_theme(name: str):
    global _active
    global BG,SURF,SURF2,SURF3,BORDER,BORDER2,TEXT,TEXT2,TEXT3
    global GOLD,GOLD2,INDIGO,IND2,TEAL,TEAL2,CRIMSON,CRIM2,PURPLE,PURP2,AMBER,AMBE2
    global GREEN,GREEN2,PANELDK
    t = THEMES.get(name, THEMES["(Dark) Obsidian"])
    _active = dict(t)
    BG=t["BG"]; SURF=t["SURF"]; SURF2=t["SURF2"]; SURF3=t["SURF3"]
    BORDER=t["BORDER"]; BORDER2=t["BORDER2"]
    TEXT=t["TEXT"]; TEXT2=t["TEXT2"]; TEXT3=t["TEXT3"]
    GOLD=t["GOLD"]; GOLD2=t["GOLD2"]
    INDIGO=t["INDIGO"]; IND2=t["IND2"]
    TEAL=t["TEAL"]; TEAL2=t["TEAL2"]
    CRIMSON=t["CRIMSON"]; CRIM2=t["CRIM2"]
    PURPLE=t["PURPLE"]; PURP2=t["PURP2"]
    AMBER=t["AMBER"]; AMBE2=t["AMBE2"]
    # GREEN/GREEN2 are theme-driven like every other accent color (HP
    # bars, the initiative "Adv" badge, healing toasts) rather than a
    # single fixed value, since a bright-on-dark green fails contrast
    # against a light background.
    GREEN=t.get("GREEN", GREEN); GREEN2=t.get("GREEN2", GREEN2)
    PANELDK=t.get("PANELDK", PANELDK)
    # shared.py (button/card/pill/label factories used app-wide) is a
    # plain module of functions, not a widget with its own __init__ --
    # so unlike sheet.py/wizard.py/etc it never gets a per-construction
    # sync_globals(globals()) call of its own. Its `from .theme import *`
    # only ran once, at shared.py's first import, so every color it reads
    # directly rather than receiving as a caller-supplied argument (SURF/
    # SURF2/BORDER/BORDER2/TEXT2/TEXT3/BG inside card()/hline()/_btn()'s
    # "neutral"/"ghost" variants/_pill()/pill_btn()/badge()) needs an
    # explicit sync here, at the one place a theme switch actually
    # happens, to stay current for every caller.
    import dnd_app.ui_desktop.shared as _shared
    sync_globals(_shared.__dict__)
    # Line icons are drawn in the theme accent (IND2) -- repaint every live
    # one so screens that aren't rebuilt on a theme switch (Start Menu,
    # menu bar, wizard) pick up the new colour too.
    import dnd_app.ui_desktop.icons as _icons
    _icons.refresh_all()
    return build_qss(t)


def sync_globals(module_globals: dict) -> None:
    """Re-inject the active theme values into a module's globals.
    Call at the start of any widget __init__ that uses ``from .theme import *``.
    """
    import dnd_app.ui_desktop.style.theme as _t
    for name, val in _active.items():
        module_globals[name] = val
    for attr in ('FS_TINY','FS_SMALL','FS_BODY','FS_LABEL','FS_HEAD',
                 'FS_TITLE','FS_STAT','FS_BIG','GREEN','GREEN2','PANELDK'):
        if hasattr(_t, attr):
            module_globals[attr] = getattr(_t, attr)


def _spin_glyphs(colour: str) -> tuple[str, str]:
    """Paths to small "-" and "+" images in `colour` for the spin box
    buttons (QSS can only show an image there, not text), drawn once per
    colour into a cache folder. ("", "") before a Qt application exists."""
    import os, tempfile
    from PySide6.QtGui import QGuiApplication
    if QGuiApplication.instance() is None:
        return "", ""
    from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
    from PySide6.QtCore import Qt
    folder = os.path.join(tempfile.gettempdir(), "mimic_spin_glyphs")
    os.makedirs(folder, exist_ok=True)
    paths = []
    for kind in ("minus", "plus"):
        path = os.path.join(folder, f"{kind}_{colour.lstrip('#')}.png")
        if not os.path.exists(path):
            pm = QPixmap(24, 24)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(colour), 3)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(5, 12, 19, 12)
            if kind == "plus":
                p.drawLine(12, 5, 12, 19)
            p.end()
            pm.save(path)
        paths.append(path.replace("\\", "/"))
    return paths[0], paths[1]


def build_qss(t=None):  # noqa: C901
    if t is None: t = _active
    b=t["BG"]; s=t["SURF"]; s2=t["SURF2"]; s3=t["SURF3"]
    bo=t["BORDER"]; bo2=t["BORDER2"]
    tx=t["TEXT"]; tx2=t["TEXT2"]; tx3=t["TEXT3"]
    g=t["GOLD"]; g2=t["GOLD2"]
    ind=t["INDIGO"]; ind2=t["IND2"]
    cr=t["CRIMSON"]; cr2=t["CRIM2"]
    tl=t["TEAL"]; tl2=t["TEAL2"]
    pu=t["PURPLE"]; pu2=t["PURP2"]
    am=t["AMBER"]; am2=t["AMBE2"]
    pdk=t.get("PANELDK", PANELDK)
    # Determine if theme is light (Arcane Scroll) or dark
    is_light = int(b.lstrip('#')[:2], 16) > 180

    # ── Scrollbar colours adapt to accent ─────────────────────────────────────
    scroll_handle = bo2
    scroll_hover  = ind

    # Scales every hardcoded pixel size below by the active "UI text size"
    # Settings choice, the same factor applied to the FS_* constants (see
    # set_font_scale()) — without this, native Qt widgets styled directly
    # by this stylesheet (QComboBox, QPushButton, tabs, etc.) would ignore
    # the Settings toggle entirely, even though custom-built labels using
    # FS_* would still respond.
    def px(n):
        return max(1, round(n * _font_scale))

    # spin boxes read "-  value  +" like Android's: the down button on the
    # left, up on the right, each showing a glyph in the text colour
    minus_img, plus_img = _spin_glyphs(tx)
    spin_glyph_qss = (
        f"QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({minus_img}); width: 10px; height: 10px; }}\n"
        f"QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({plus_img}); width: 10px; height: 10px; }}\n"
    ) if minus_img else ""

    return f"""
/* ── Reset & Base ────────────────────────────────────────────────────────── */
* {{ font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif; font-size: {px(15)}px; }}
QMainWindow, QDialog {{ background: {b}; color: {tx}; }}
QWidget {{ background: transparent; color: {tx}; }}
QFrame {{ background: transparent; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QSplitter {{ background: {b}; }}

/* ── Tabs ──────────────────────────────────────────────────────────────────── */
/* QTabWidget's own base background (distinct from ::pane, the content
   area below the tabs, and from QTabBar, which only paints its own
   tabs) -- without this, the strip to the right of the last tab (the
   tab bar row doesn't stretch to fill the widget's full width) falls
   back to the OS's raw default widget background, which reads as a
   stray black bar regardless of the active theme.
   Painted with PANELDK (a deliberate dark accent, not the plain page
   background) rather than {b} -- on a light theme, a gap that merely
   matched the page background still read as a stray "hole"/wrong-color
   bar at a glance, and it left every theme's own visual identity out of
   an otherwise-blank strip. PANELDK gives that strip real presence, in
   the same "recessed dark chrome" language as other panel surfaces,
   with a hue unique to each theme (see THEMES/PANELDK's own comment). */
QTabWidget {{ background: {pdk}; }}
/* Corner radii are set one corner at a time: Qt's stylesheets don't take
   CSS's four-value "border-radius: a b c d" (it rounds every corner), so
   a tab written that way came out rounded at the bottom too.
   The selected tab is joined to its page, like a folder tab: it's the
   page's own colour, and the page is pulled up 1px (top: -1px) so its top
   border runs along the bottom of the tabs -- under the selected tab that
   line is painted over in the page colour, so tab and page read as one
   piece. The other tabs keep the line, so they sit "behind" it. */
QTabWidget::pane {{ border: 1px solid {bo2}; background: {b}; border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 8px; border-bottom-left-radius: 8px; top: -1px; }}
QTabBar {{ background: {pdk}; }}
QTabBar::tab {{
    background: {s}; color: {tx2}; padding: 12px 12px;
    border: 1px solid {bo}; border-bottom: 1px solid {bo2};
    border-top-left-radius: 8px; border-top-right-radius: 8px; border-bottom-right-radius: 0px; border-bottom-left-radius: 0px; font-weight: 700; font-size: {px(14)}px;
    margin-right: 2px; min-width: 60px;
}}
QTabBar::tab:selected {{ background: {b}; color: {g2}; border-color: {bo2}; border-bottom: 1px solid {b}; }}
QTabBar::tab:hover:!selected {{ background: {s2}; color: {tx}; }}

/* ── Group Boxes ───────────────────────────────────────────────────────────── */
QGroupBox {{
    background: {s}; border: 1px solid {bo}; border-radius: 10px;
    margin-top: 18px; padding: 12px 10px 10px 10px;
    font-weight: 700; font-size: {px(12)}px; color: {g};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 12px; top: 0px; background: {s};
    color: {g}; font-size: {px(12)}px; font-weight: 700; letter-spacing: 1px; padding: 0 6px;
}}

/* ── Input Fields ──────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QListWidget {{
    background: {b}; border: 2px solid {bo};
    border-radius: 6px; color: {tx}; padding: 6px 10px;
    font-size: {px(15)}px; selection-background-color: {ind};
    min-height: 32px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {ind}; background: {s};
}}
/* "-  value  +": down button on the left, up on the right, full height */
QSpinBox, QDoubleSpinBox {{ padding-left: 2px; padding-right: 2px; }}   /* Qt leaves room for both buttons itself */
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: center left;
    width: 24px; height: 200px; background: {bo}; border: none;
    border-top-left-radius: 5px; border-bottom-left-radius: 5px;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: center right;
    width: 24px; height: 200px; background: {bo}; border: none;
    border-top-right-radius: 5px; border-bottom-right-radius: 5px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{ background: {ind}; }}
QSpinBox::up-button:disabled, QSpinBox::down-button:disabled {{ background: {s2}; }}
{spin_glyph_qss}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ border: none; width: 26px; background: {bo2}; border-top-left-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px; border-bottom-left-radius: 0px; }}
QComboBox::down-arrow {{ image: none; }}
QComboBox QAbstractItemView {{
    background: {s2}; border: 2px solid {bo2};
    selection-background-color: {ind}; color: {tx};
    outline: none; font-size: {px(15)}px; padding: 4px;
}}

/* ── Buttons ───────────────────────────────────────────────────────────────── */
QPushButton {{
    background: {s2}; border: 2px solid {bo2};
    border-radius: 7px; color: {tx}; padding: 8px 18px;
    font-weight: 700; font-size: {px(15)}px; min-height: 36px;
}}
QPushButton:hover {{ background: {ind}44; border-color: {ind}; color: {tx}; }}
QPushButton:pressed {{ background: {ind}; color: white; border-color: {ind2}; }}
QPushButton:checked {{ background: {ind}; color: white; border-color: {ind2}; }}
QPushButton:disabled {{ background: {bo}; color: {tx3}; border-color: {bo}; }}

/* ── Checkboxes & Radios ───────────────────────────────────────────────────── */
QCheckBox {{ color: {tx}; spacing: 8px; font-size: {px(15)}px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 4px;
    border: 2px solid {bo2}; background: {b};
}}
QCheckBox::indicator:checked {{ background: {ind}; border-color: {ind2}; }}
QCheckBox::indicator:hover {{ border-color: {ind}; }}
QRadioButton {{ color: {tx}; spacing: 8px; font-size: {px(15)}px; }}
QRadioButton::indicator {{
    width: 18px; height: 18px; border-radius: 9px;
    border: 2px solid {bo2}; background: {b};
}}
QRadioButton::indicator:checked {{ background: {ind}; border-color: {ind2}; }}

/* ── Scrollbars ────────────────────────────────────────────────────────────── */
QScrollBar:vertical {{ background: {s}; width: 10px; border-radius: 5px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {scroll_handle}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {scroll_hover}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; background: none; }}
QScrollBar:horizontal {{ background: {s}; height: 10px; border-radius: 5px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {scroll_handle}; border-radius: 5px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {scroll_hover}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; background: none; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

/* ── Lists & Tables ────────────────────────────────────────────────────────── */
QListWidget {{ background: {b}; color: {tx}; border: 2px solid {bo}; border-radius: 6px; outline: none; font-size: {px(15)}px; }}
/* no colour on ::item -- it would override each item's own (setForeground) colour */
QListWidget::item {{ padding: 6px 10px; border-radius: 4px; }}
QListWidget::item:selected {{ background: {ind}; color: white; }}
QListWidget::item:hover:!selected {{ background: {s2}; }}
QTableWidget {{ background: {b}; color: {tx}; border: none; gridline-color: {bo}; font-size: {px(14)}px; }}
QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {bo}; color: {tx}; }}
QTableWidget::item:selected {{ background: {ind}; color: white; }}
QHeaderView::section {{ background: {s2}; color: {g}; font-weight: 700; padding: 8px; border: none; border-bottom: 2px solid {bo}; font-size: {px(13)}px; }}

/* ── Labels ────────────────────────────────────────────────────────────────── */
QLabel {{ color: {tx}; font-size: {px(15)}px; background: transparent; }}
QLabel[heading="true"] {{ font-size: {px(20)}px; font-weight: 700; color: {g2}; }}
QLabel[subheading="true"] {{ font-size: {px(16)}px; font-weight: 700; color: {tx}; }}

/* ── Tooltips ──────────────────────────────────────────────────────────────── */
QToolTip {{
    background: {s2}; color: {tx}; border: 1px solid {bo2};
    border-radius: 6px; padding: 6px 10px; font-size: {px(13)}px;
}}

/* ── Menus ─────────────────────────────────────────────────────────────────── */
QStatusBar {{ background: {s}; border-top: 2px solid {bo}; color: {tx2}; font-size: {px(14)}px; }}
QStatusBar::item {{ border: none; }}
QMenuBar {{ background: {s}; color: {tx}; border-bottom: 1px solid {bo}; font-size: {px(15)}px; }}
QMenuBar::item {{ background: transparent; padding: 6px 12px; }}
QMenuBar::item:selected {{ background: {ind}; color: white; border-radius: 4px; }}
QMenu {{ background: {s2}; border: 2px solid {bo2}; color: {tx}; padding: 4px; font-size: {px(15)}px; }}
QMenu::item {{ padding: 8px 28px 8px 14px; border-radius: 4px; color: {tx}; }}
QMenu::item:selected {{ background: {ind}; color: white; }}
QMenu::separator {{ height: 1px; background: {bo}; margin: 3px 0; }}

/* ── Progress & Sliders ────────────────────────────────────────────────────── */
QProgressBar {{
    background: {b}; border: 2px solid {bo}; border-radius: 8px;
    text-align: center; font-size: {px(13)}px; color: {tx}; min-height: 20px;
}}
QProgressBar::chunk {{ background: {ind}; border-radius: 6px; }}
QSlider::groove:horizontal {{ background: {bo}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {ind}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; border: 2px solid {ind2}; }}
QSlider::sub-page:horizontal {{ background: {ind}; border-radius: 3px; }}

/* ── Splitters ─────────────────────────────────────────────────────────────── */
QSplitter::handle {{ background: {bo}; }}
QSplitter::handle:horizontal {{ width: 3px; }}
QSplitter::handle:vertical {{ height: 3px; }}
QSplitter::handle:hover {{ background: {ind}; }}

/* ── Dialogs ───────────────────────────────────────────────────────────────── */
QDialogButtonBox QPushButton {{ min-width: 80px; }}
QInputDialog QLabel {{ color: {tx}; }}
"""


QSS = build_qss()
