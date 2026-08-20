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
# name -> scale factor. "Medium (default)" is the reference 1.0 in _BASE_FS.
# Large is deliberately modest (not e.g. 1.3+): a lot of small UI chrome
# (level pills, source badges, reset badges) lives in setFixedHeight/
# setFixedSize containers as tight as 16-18px tall with only 1-2px of
# padding around FS_TINY text -- a bigger jump risks clipped/truncated
# text in exactly those spots. 1.15 keeps body/heading text meaningfully
# larger while staying inside that headroom.
FONT_SCALES = {"Small": 0.85, "Medium (default)": 1.0, "Large": 1.15}
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


THEMES = {
    # ── 1. Obsidian — sharp indigo/blue on near-black. Clean modern default ─
    "(Dark) Obsidian": {
        "BG":"#0d0f18","SURF":"#161922","SURF2":"#1c2030","SURF3":"#242840",
        "BORDER":"#50556d","BORDER2":"#4a5890",
        "TEXT":"#eae8f5","TEXT2":"#a8a4c8","TEXT3":"#8f8da8",
        "GOLD":"#e0b030","GOLD2":"#f8d060",
        "INDIGO":"#5878f8","IND2":"#90a8ff",
        "TEAL":"#18c090","TEAL2":"#28e8b0",
        "CRIMSON":"#e04050","CRIM2":"#f87080",
        "PURPLE":"#9858e8","PURP2":"#c090ff",
        "AMBER":"#e89828","AMBE2":"#f8c048",
    },
    # ── 2. Dragon's Hoard — deep emerald + molten gold. Wealth and danger ──
    "(Dark) Dragon's Hoard": {
        "BG":"#060d0a","SURF":"#0c1a12","SURF2":"#12241a","SURF3":"#182e22",
        "BORDER":"#3b5c47","BORDER2":"#286040",
        "TEXT":"#e8f5e0","TEXT2":"#90c898","TEXT3":"#739979",
        "GOLD":"#e8a820","GOLD2":"#ffd050",
        "INDIGO":"#20b860","IND2":"#40e880",
        "TEAL":"#18b8a0","TEAL2":"#30e0c0",
        "CRIMSON":"#e84828","CRIM2":"#f87858",
        "PURPLE":"#8840d0","PURP2":"#b878ff",
        "AMBER":"#e8a820","AMBE2":"#ffd050",
    },
    # ── 3. Shadowfell — cold purple/grey on true black. Gothic and moody ───
    "(Dark) Shadowfell": {
        "BG":"#080610","SURF":"#100e1c","SURF2":"#181528","SURF3":"#201c34",
        "BORDER":"#53506a","BORDER2":"#4a4470",
        "TEXT":"#d8d0f0","TEXT2":"#9888c8","TEXT3":"#8882a0",
        "GOLD":"#c8a838","GOLD2":"#e8c858",
        "INDIGO":"#7a6cdb","IND2":"#a090f8",
        "TEAL":"#4898c8","TEAL2":"#70c0f0",
        "CRIMSON":"#c03870","CRIM2":"#e86898",
        "PURPLE":"#9068e0","PURP2":"#c098ff",
        "AMBER":"#c89838","AMBE2":"#e8c050",
    },
    # ── 4. Arcane Scroll — warm parchment. Wizard's library, readable ─────
    "(Light) Arcane Scroll": {
        "BG":"#f2edd8","SURF":"#e8e0c4","SURF2":"#ddd5b0","SURF3":"#cfc79a",
        "BORDER":"#a69161","BORDER2":"#9a7840",
        "TEXT":"#18100a","TEXT2":"#3a2808","TEXT3":"#6a4820",
        "GOLD":"#7a4c08","GOLD2":"#9a6820",
        "INDIGO":"#1e3ea0","IND2":"#2856d0",
        "TEAL":"#0c6040","TEAL2":"#18804e",
        "CRIMSON":"#8c1818","CRIM2":"#c02828",
        "PURPLE":"#5a1878","PURP2":"#7828a0",
        "AMBER":"#8e5708","AMBE2":"#c07820",
    },
    # ── Moonlit Vellum — cool silvery-blue-grey parchment. Scholarly, crisp ─
    "(Light) Moonlit Vellum": {
        "BG":"#eef1f6","SURF":"#e2e7f0","SURF2":"#d5dcea","SURF3":"#c7d0e2",
        "BORDER":"#8f96a7","BORDER2":"#77829b",
        "TEXT":"#282e3b","TEXT2":"#495162","TEXT3":"#535967",
        "GOLD":"#82630f","GOLD2":"#7f6420",
        "INDIGO":"#2c4ba8","IND2":"#4563bb",
        "TEAL":"#0d765b","TEAL2":"#1b755e",
        "CRIMSON":"#a3273a","CRIM2":"#b33f4f",
        "PURPLE":"#6a3a9e","PURP2":"#8052b0",
        "AMBER":"#965908","AMBE2":"#8f5d18",
    },
    # ── Sunlit Meadow — warm cream and sage green. Bright, welcoming ──────
    "(Light) Sunlit Meadow": {
        "BG":"#f3f0e2","SURF":"#e9e4cd","SURF2":"#ded6b3","SURF3":"#cfc596",
        "BORDER":"#9f966e","BORDER2":"#8e814b",
        "TEXT":"#312d1b","TEXT2":"#565135","TEXT3":"#585239",
        "GOLD":"#83600b","GOLD2":"#7e6120",
        "INDIGO":"#39548a","IND2":"#4c6598",
        "TEAL":"#166b40","TEAL2":"#28734c",
        "CRIMSON":"#9e3428","CRIM2":"#a9473a",
        "PURPLE":"#6f3f7e","PURP2":"#825590",
        "AMBER":"#8b5c0f","AMBE2":"#855f1e",
    },
    # ── 5. Feywild — vibrant teal/pink on rich midnight blue. Magical ─────
    "(Dark) Feywild": {
        "BG":"#080820","SURF":"#0e1030","SURF2":"#141640","SURF3":"#1a1c52",
        "BORDER":"#4c5086","BORDER2":"#303898",
        "TEXT":"#f0ecff","TEXT2":"#b0a8e8","TEXT3":"#8b84ac",
        "GOLD":"#e8c840","GOLD2":"#ffe870",
        "INDIGO":"#28c8d8","IND2":"#60e8f8",
        "TEAL":"#18c898","TEAL2":"#28f0c0",
        "CRIMSON":"#e83888","CRIM2":"#f870b8",
        "PURPLE":"#a850e8","PURP2":"#d890ff",
        "AMBER":"#e8a830","AMBE2":"#ffd060",
    },
    # ── 6. Blood Moon — gothic vampire crimson/black. Ravenloft horror ────
    "(Dark) Blood Moon": {
        "BG":"#100609","SURF":"#1c0c10","SURF2":"#241016","SURF3":"#30161e",
        "BORDER":"#6e4952","BORDER2":"#8a3048",
        "TEXT":"#f5e0e4","TEXT2":"#c890a0","TEXT3":"#9b7d89",
        "GOLD":"#c89040","GOLD2":"#e8b060",
        "INDIGO":"#d24d68","IND2":"#f85878",
        "TEAL":"#209888","TEAL2":"#40c8b0",
        "CRIMSON":"#f01838","CRIM2":"#ff5068",
        "PURPLE":"#863eb1","PURP2":"#a858d8",
        "AMBER":"#d87828","AMBE2":"#f89848",
    },
    # ── 7. Frostspire — icy blue/white winter. Frost giant peaks ──────────
    "(Dark) Frostspire": {
        "BG":"#060a12","SURF":"#0c1420","SURF2":"#121c2c","SURF3":"#182438",
        "BORDER":"#40566b","BORDER2":"#406890",
        "TEXT":"#e8f0f8","TEXT2":"#98b8d0","TEXT3":"#798d9f",
        "GOLD":"#c8b060","GOLD2":"#e8d080",
        "INDIGO":"#3888e0","IND2":"#68b0f8",
        "TEAL":"#20b8c8","TEAL2":"#48e0f0",
        "CRIMSON":"#e04848","CRIM2":"#f87878",
        "PURPLE":"#7868c8","PURP2":"#a898f0",
        "AMBER":"#d89840","AMBE2":"#f8b860",
    },
    # ── 8. Cinderveil — volcanic orange/black. Molten, infernal ───────────
    "(Dark) Cinderveil": {
        "BG":"#100804","SURF":"#1c1008","SURF2":"#241608","SURF3":"#301c0a",
        "BORDER":"#724b33","BORDER2":"#985018",
        "TEXT":"#f8ecd8","TEXT2":"#d0a878","TEXT3":"#a0825d",
        "GOLD":"#e89818","GOLD2":"#ffc040",
        "INDIGO":"#e85818","IND2":"#ff8848",
        "TEAL":"#189888","TEAL2":"#38c8a8",
        "CRIMSON":"#c81818","CRIM2":"#f04838",
        "PURPLE":"#795579","PURP2":"#986898",
        "AMBER":"#f8a828","AMBE2":"#ffc858",
    },
    # ── 9. Tavern Hearth — warm aged wood + firelight. Cozy, welcoming ────
    "(Dark) Tavern Hearth": {
        "BG":"#140d08","SURF":"#1e140c","SURF2":"#281c12","SURF3":"#322418",
        "BORDER":"#655241","BORDER2":"#785030",
        "TEXT":"#f5e8d0","TEXT2":"#c8a878","TEXT3":"#a3886f",
        "GOLD":"#e8a838","GOLD2":"#ffc858",
        "INDIGO":"#c87830","IND2":"#e89850",
        "TEAL":"#5f895f","TEAL2":"#68a068",
        "CRIMSON":"#b83828","CRIM2":"#e05848",
        "PURPLE":"#765a76","PURP2":"#987898",
        "AMBER":"#f0a828","AMBE2":"#ffc858",
    },
    # ── 10. Mossgrove — lighter, earthy olive-green forest ────────────────
    "(Dark) Mossgrove": {
        "BG":"#0e120a","SURF":"#161c10","SURF2":"#1e2616","SURF3":"#26301c",
        "BORDER":"#4e5b3e","BORDER2":"#5c7038",
        "TEXT":"#e8f0d8","TEXT2":"#a8c088","TEXT3":"#8b996f",
        "GOLD":"#b8a038","GOLD2":"#d8c058",
        "INDIGO":"#798939","IND2":"#a0b858",
        "TEAL":"#489878","TEAL2":"#68c098",
        "CRIMSON":"#b84838","CRIM2":"#e07058",
        "PURPLE":"#786898","PURP2":"#a898c8",
        "AMBER":"#c88838","AMBE2":"#e8a858",
    },
    # ── 11. Gearworks — artificer's workshop. Brass, copper, gunmetal ─────
    "(Dark) Gearworks": {
        "BG":"#0e1012","SURF":"#161a1e","SURF2":"#1e242a","SURF3":"#262e36",
        "BORDER":"#51575e","BORDER2":"#605038",
        "TEXT":"#f0ece0","TEXT2":"#b8a888","TEXT3":"#9d9286",
        "GOLD":"#c88838","GOLD2":"#e8a858",
        "INDIGO":"#5a86aa","IND2":"#70a0c8",
        "TEAL":"#389888","TEAL2":"#58c0a8",
        "CRIMSON":"#c83828","CRIM2":"#e86848",
        "PURPLE":"#6d5e8c","PURP2":"#9888b8",
        "AMBER":"#d89838","AMBE2":"#f8b858",
    },
    # ── 12. Hallowed Stone — church slate grey + gold. Temple and vestry ──
    "(Dark) Hallowed Stone": {
        "BG":"#0e1014","SURF":"#161a20","SURF2":"#1e242c","SURF3":"#262e38",
        "BORDER":"#4f5763","BORDER2":"#586478",
        "TEXT":"#e8e8f0","TEXT2":"#a8b0c0","TEXT3":"#8e94a0",
        "GOLD":"#d8b840","GOLD2":"#f8d868",
        "INDIGO":"#7281a7","IND2":"#8898c0",
        "TEAL":"#389880","TEAL2":"#58c0a0",
        "CRIMSON":"#af4040","CRIM2":"#d85858",
        "PURPLE":"#786098","PURP2":"#a890c8",
        "AMBER":"#c89840","AMBE2":"#e8b860",
    },
}

_active = dict(THEMES["(Dark) Obsidian"])

def apply_theme(name: str):
    global _active
    global BG,SURF,SURF2,SURF3,BORDER,BORDER2,TEXT,TEXT2,TEXT3
    global GOLD,GOLD2,INDIGO,IND2,TEAL,TEAL2,CRIMSON,CRIM2,PURPLE,PURP2,AMBER,AMBE2
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
    return build_qss(t)


def sync_globals(module_globals: dict) -> None:
    """Re-inject the active theme values into a module's globals.
    Call at the start of any widget __init__ that uses ``from .theme import *``.
    """
    import dnd_app.ui.theme as _t
    for name, val in _active.items():
        module_globals[name] = val
    for attr in ('FS_TINY','FS_SMALL','FS_BODY','FS_LABEL','FS_HEAD',
                 'FS_TITLE','FS_STAT','FS_BIG','GREEN','GREEN2'):
        if hasattr(_t, attr):
            module_globals[attr] = getattr(_t, attr)


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

    return f"""
/* ── Reset & Base ────────────────────────────────────────────────────────── */
* {{ font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif; font-size: {px(15)}px; }}
QMainWindow, QDialog {{ background: {b}; color: {tx}; }}
QWidget {{ background: transparent; color: {tx}; }}
QFrame {{ background: transparent; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QSplitter {{ background: {b}; }}

/* ── Tabs ──────────────────────────────────────────────────────────────────── */
QTabWidget::pane {{ border: 1px solid {bo}; background: {b}; border-radius: 0 8px 8px 8px; }}
QTabBar {{ background: {b}; border-bottom: 2px solid {bo}; }}
QTabBar::tab {{
    background: {s}; color: {tx2}; padding: 12px 22px;
    border: 1px solid {bo}; border-bottom: none;
    border-radius: 8px 8px 0 0; font-weight: 700; font-size: {px(14)}px;
    margin-right: 2px; min-width: 80px;
}}
QTabBar::tab:selected {{ background: {s2}; color: {g2}; border-color: {bo2}; border-bottom: 2px solid {s2}; }}
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
QSpinBox::up-button, QSpinBox::down-button {{
    background: {bo}; border: none; width: 20px; border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {ind}; }}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ border: none; width: 26px; background: {bo2}; border-radius: 0 5px 5px 0; }}
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
QListWidget {{ background: {b}; border: 2px solid {bo}; border-radius: 6px; outline: none; font-size: {px(15)}px; }}
QListWidget::item {{ padding: 6px 10px; border-radius: 4px; color: {tx}; }}
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
