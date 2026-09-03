"""Shared helper widgets used across wizard and sheet.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from dnd_app.ui.style.theme import *
ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]
AB_FULL = {"STR":"Strength","DEX":"Dexterity","CON":"Constitution",
           "INT":"Intelligence","WIS":"Wisdom","CHA":"Charisma"}

def sign(n): return f"+{n}" if n >= 0 else str(n)


def diagnostic_log_dir() -> str:
    """Where to write crash/diagnostic log files (mimic_crash_log.txt,
    mimic_toast_log.txt) -- the folder the running executable actually
    lives in, not sys._MEIPASS (PyInstaller onefile's temp extraction
    dir, wiped after the process exits, so a log written there would
    vanish before anyone could read it) and not the user's home folder
    (harder to find than just looking next to MIMIC.exe). Falls back to
    the current working directory when running from source, unfrozen."""
    import sys, os
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.getcwd()


def write_diagnostic_log(filename: str, text: str, mode: str = "w") -> str | None:
    """Write (or append) a diagnostic log file, trying diagnostic_log_dir()
    first and falling back to the user's home folder if that write fails
    (e.g. the exe's own folder isn't writable -- Program Files, a
    read-only network share). Returns the path actually written, or None
    if both attempts failed, so a caller can tell the user exactly where
    to look rather than assuming the primary location worked."""
    import os
    for candidate_dir in (diagnostic_log_dir(), os.path.expanduser("~")):
        path = os.path.join(candidate_dir, filename)
        try:
            with open(path, mode, encoding="utf-8") as f:
                f.write(text)
            return path
        except Exception:
            continue
    return None

def h(text, color=None, size=FS_BODY, bold=False, align=Qt.AlignLeft, wrap=True):
    """Quick label factory."""
    w = QLabel(text)
    c = color or TEXT
    s = f"color:{c};font-size:{size}px;background:transparent;"
    if bold: s += "font-weight:700;"
    w.setStyleSheet(s)
    w.setAlignment(align)
    if wrap: w.setWordWrap(True)
    return w

# Every UI file used to define its own near-identical copy of this exact
# label factory under the name "_lbl" (sheet.py, wizard.py, main_window.py,
# levelup_panel.py, feature_dialog.py all had one). h() is the original of
# the bunch; this alias lets every file just `from .shared import _lbl` and
# delete its local copy, with zero call-site changes anywhere.
_lbl = h

def section_header(text, color=None):
    lbl = h(text.upper(), color or GOLD, FS_SMALL, bold=True)
    lbl.setStyleSheet(lbl.styleSheet() + f"letter-spacing:2px;padding-bottom:2px;")
    return lbl

def hline():
    f = QFrame(); f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"color:{BORDER};background:{BORDER};max-height:1px;border:none;")
    return f

def card(accent=BORDER):
    """Styled card frame — a bordered QFrame with the standard SURF
    background. Was already defined here with a different (parent, color)
    signature, but never actually called anywhere; sheet.py had grown its
    own separate, differently-named `_card(accent=BORDER)` used 61 times
    instead. This adopts THAT signature (the one actually in use) as the
    canonical one, so sheet.py's existing `_card(...)` call sites need no
    changes — just `_card = card` after importing this."""
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {accent};border-radius:10px;}}")
    return f

# Same reasoning as _lbl above: sheet.py's own `_card` and this module's
# `card` were the same shape, just never unified. Alias, not a rename, so
# every existing `_card(...)` call site across the app keeps working.
_card = card


def _btn(label, color=None, *, variant="cta", height=28, width=None,
         radius=6, padding=None, bold=True, font_size=None, tooltip="",
         enabled=True, bg_alpha=None, border_alpha=None, text_color=None,
         hover_text=None, hover_bg_alpha=None, min_height0=False,
         border_width=None):
    """Shared QPushButton factory covering the ~4 button "shapes" used
    at call sites app-wide, each a variation on one of these with only
    the accent color (and occasionally the alpha/text-color specifics
    below) actually differing. NOT a replacement for pill_btn() above
    (a distinct, already-shared solid/no-border/rounded-pill shape used
    for the most prominent CTAs like "Create New Character").

    variant="cta"     (default) — tinted background, thick 2px border
                       in the same color, hover FILLS to solid color.
                       The "Confirm"/"Level Up"/rest-button look.
                       `color` required.
    variant="chip"     — lighter tint, thin 1px border, hover tints
                       further (never fills solid). Small in-a-row
                       action buttons (Identity/Class-Manager buttons,
                       toolbar icons with a color). `color` required.
    variant="neutral"  — SURF2 background, BORDER2 border, TEXT2 text,
                       SURF3/TEXT on hover. Cancel/Back/Skip buttons.
                       `color` is ignored.
    variant="ghost"    — transparent background, thin BORDER border,
                       tints toward `color` on hover. Small icon
                       buttons (🎲 roll buttons). `color` required
                       (used only for the hover tint).
    variant="danger"   — same shape as "cta", defaults `color` to
                       CRIMSON when not given (destructive actions).

    Every hand-rolled call site this replaces used the same handful of
    shapes above, but not always the exact same alpha/text-color pick
    (e.g. some "cta" buttons use a brighter "2"-suffixed text color
    like CRIM2/TEAL2 instead of the base color, some hover to white
    text instead of the page background). Rather than one rigid look,
    the shape is fixed per variant and these are the parts that vary:
    bg_alpha/border_alpha/hover_bg_alpha (ints, e.g. 0x33) and
    text_color/hover_text (full color strings) override the variant's
    defaults when the original call site used something else.
    """
    if variant == "danger" and color is None:
        color = CRIMSON
    if variant != "neutral" and color is None:
        raise ValueError(f"_btn(variant={variant!r}) requires a color")

    btn = QPushButton(label)
    if height: btn.setFixedHeight(height)
    if width: btn.setFixedWidth(width)
    if tooltip: btn.setToolTip(tooltip)
    if not enabled: btn.setEnabled(False)

    weight = "font-weight:700;" if bold else ""
    fs = f"font-size:{font_size}px;" if font_size else ""
    mh = "min-height:0px;" if min_height0 else ""

    if variant in ("cta", "danger"):
        pad = padding or "4px 20px"
        bw = border_width if border_width is not None else 2
        bg_a = bg_alpha if bg_alpha is not None else 0x33
        border = qa(color, border_alpha) if border_alpha is not None else color
        txt = text_color or color
        hov_txt = hover_text if hover_text is not None else BG
        btn.setStyleSheet(
            f"QPushButton{{background:{qa(color,bg_a)};border:{bw}px solid {border};"
            f"border-radius:{radius}px;color:{txt};{weight}{fs}{mh}padding:{pad};}}"
            f"QPushButton:hover{{background:{color};color:{hov_txt};}}")
    elif variant == "chip":
        pad = padding or "2px 10px"
        bw = border_width if border_width is not None else 1
        bg_a = bg_alpha if bg_alpha is not None else 0x22
        bor_a = border_alpha if border_alpha is not None else 0x66
        hov_a = hover_bg_alpha if hover_bg_alpha is not None else 0x55
        txt = text_color or color
        btn.setStyleSheet(
            f"QPushButton{{background:{qa(color,bg_a)};border:{bw}px solid {qa(color,bor_a)};"
            f"border-radius:{radius}px;color:{txt};{weight}{fs}{mh}padding:{pad};}}"
            f"QPushButton:hover{{background:{qa(color,hov_a)};border-color:{color};}}")
    elif variant == "neutral":
        pad = padding or "5px 10px"
        btn.setStyleSheet(
            f"QPushButton{{background:{SURF2};border:1px solid {BORDER2};"
            f"border-radius:{radius}px;color:{TEXT2};{weight}{fs}{mh}padding:{pad};}}"
            f"QPushButton:hover{{background:{SURF3};color:{TEXT};}}")
    elif variant == "ghost":
        pad = padding or "0px"
        bor_a = border_alpha  # None -> plain BORDER, matching the original ghost shape
        border = qa(BORDER, bor_a) if bor_a is not None else BORDER
        hov_a = hover_bg_alpha if hover_bg_alpha is not None else 0x33
        btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {border};"
            f"border-radius:{radius}px;{fs or f'font-size:{FS_SMALL}px;'}padding:{pad};min-height:0px;}}"
            f"QPushButton:hover{{background:{qa(color,hov_a)};border-color:{color};}}")
    else:
        raise ValueError(f"_btn: unknown variant {variant!r}")
    return btn


def _pill(label, value, color, width=96):
    """Small bordered stat block: big value + title below. Generalizes
    what CharacterSheet._make_stat_pill()/_make_xp_pill() were building
    ad hoc — those become thin wrappers around this. Returns the QFrame
    with a `._val` QLabel attribute for later `.setText()` updates,
    matching the contract every existing stat-pill call site already
    depends on (AC/HP/Initiative/Prof Bonus/Speed/XP)."""
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:{SURF};border:2px solid {qa(color,0x55)};border-radius:10px;}}")
    f.setFixedHeight(52); f.setMinimumWidth(width)
    lay = QVBoxLayout(f); lay.setContentsMargins(10,4,10,4); lay.setSpacing(0)
    val = h(str(value), color, FS_TITLE, bold=True, align=Qt.AlignCenter, wrap=False)
    ttl = h(label, TEXT3, FS_TINY, align=Qt.AlignCenter, wrap=False)
    lay.addWidget(val); lay.addWidget(ttl)
    f._val = val
    return f


def pill_btn(text, bg=INDIGO, fg="white", hover=None):
    """Styled button."""
    btn = QPushButton(text)
    h_color = hover or IND2
    btn.setStyleSheet(
        f"QPushButton{{background:{bg};border:none;border-radius:8px;color:{fg};"
        f"font-weight:700;font-size:{FS_BODY}px;padding:9px 20px;}}"
        f"QPushButton:hover{{background:{h_color};}}"
        f"QPushButton:pressed{{background:{BG};}}"
        f"QPushButton:disabled{{background:{SURF3};color:{TEXT3};}}"
    )
    return btn

def badge(text, bg=INDIGO, size=FS_SMALL):
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background:{bg};color:white;font-size:{size}px;font-weight:700;"
        f"border-radius:{size}px;padding:2px 8px;"
    )
    lbl.setFixedHeight(size + 8)
    return lbl

class BigStatBox(QFrame):
    """Large stat display box: big number + label below."""
    def __init__(self, label, value="—", color=None, parent=None):
        super().__init__(parent)
        self._color = color or IND2
        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border:2px solid {BORDER};border-radius:10px;}}"
        )
        lay = QVBoxLayout(self); lay.setContentsMargins(10,10,10,8); lay.setSpacing(2)
        self._val_lbl = QLabel(str(value))
        self._val_lbl.setAlignment(Qt.AlignCenter)
        # Most values here are short (a number, "+2", "30 ft"), but Senses
        # can be a real sentence ("Darkvision 60 ft, Blindsight 10 ft") --
        # at the fixed 20pt size that just got clipped by the box's fixed
        # width instead of wrapping. Word-wrap plus a smaller font for
        # longer text keeps every value fully visible instead of cut off.
        f = QFont(); f.setBold(True)
        f.setPointSize(20 if len(str(value)) <= 8 else 12)
        self._val_lbl.setFont(f)
        self._val_lbl.setWordWrap(True)
        self._val_lbl.setStyleSheet(f"color:{self._color};background:transparent;")
        self._ttl_lbl = QLabel(label)
        self._ttl_lbl.setAlignment(Qt.AlignCenter)
        self._ttl_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:700;background:transparent;letter-spacing:1px;")
        lay.addWidget(self._val_lbl); lay.addWidget(self._ttl_lbl)

    def set_val(self, v):
        v = str(v)
        self._val_lbl.setText(v)
        f = self._val_lbl.font(); f.setPointSize(20 if len(v) <= 8 else 12)
        self._val_lbl.setFont(f)
    def set_color(self, c):
        self._color = c
        self._val_lbl.setStyleSheet(f"color:{c};background:transparent;")

class AbilityBlock(QFrame):
    """One ability score block: name / score / modifier."""
    changed = Signal(str, int)   # (ability, new_score)
    roll_requested = Signal(str)  # (ability) -- raw ability check, d20 + mod

    def __init__(self, ab, score=10, editable=True, parent=None):
        super().__init__(parent)
        self.ab = ab
        self._editable = editable
        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border:2px solid {BORDER};border-radius:12px;}}"
            f"QFrame:hover{{border-color:{BORDER2};}}"
        )
        self.setFixedWidth(120)
        lay = QVBoxLayout(self); lay.setContentsMargins(8,8,8,10); lay.setSpacing(4)

        # Ability name
        name_lbl = h(ab, TEXT2, FS_SMALL, bold=True, align=Qt.AlignCenter, wrap=False)
        lay.addWidget(name_lbl)

        # Score spinbox or label
        if editable:
            self._score_spin = QSpinBox()
            self._score_spin.setRange(1, 20)
            self._score_spin.setValue(score)
            self._score_spin.setAlignment(Qt.AlignCenter)
            self._score_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self._score_spin.setStyleSheet(
                f"QSpinBox{{font-size:{FS_STAT}px;font-weight:700;color:{TEXT};"
                f"border:none;background:transparent;text-align:center;}}"
            )
            def _on_spin_change(v, self=self):
                mod = (v - 10) // 2
                self._mod_lbl.setText(sign(mod))
                self._mod_lbl.setStyleSheet(
                    f"color:{TEAL2 if mod >= 0 else CRIM2};font-size:{FS_TITLE}px;"
                    f"font-weight:700;background:transparent;")
                self.changed.emit(self.ab, v)
            self._score_spin.valueChanged.connect(_on_spin_change)
            lay.addWidget(self._score_spin)
        else:
            self._score_lbl = h(str(score), TEXT, FS_STAT, bold=True, align=Qt.AlignCenter)
            lay.addWidget(self._score_lbl)

        # Modifier
        mod = (score - 10) // 2
        self._mod_lbl = h(sign(mod), TEAL2 if mod >= 0 else CRIM2, FS_TITLE, bold=True, align=Qt.AlignCenter)
        lay.addWidget(self._mod_lbl)

        # 🎲 roll button — raw ability check (d20 + mod, no proficiency).
        # Only on the sheet's read-only blocks (editable=False): the
        # wizard's blocks (editable=True) are mid-creation, still being
        # assigned, so there's nothing real yet to roll. Same button
        # style/role as the Skills/Saves rows' roll buttons.
        self._roll_btn = None
        if not editable:
            self._roll_btn = QPushButton("🎲")
            self._roll_btn.setFixedHeight(22)
            self._roll_btn.setToolTip(f"Roll {ab} check ({sign(mod)})")
            self._roll_btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:1px solid {BORDER};"
                f"border-radius:5px;font-size:{FS_SMALL}px;padding:0px;min-height:0px;}}"
                f"QPushButton:hover{{background:{qa(TEAL,0x33)};border-color:{TEAL};}}")
            self._roll_btn.clicked.connect(lambda checked=False: self.roll_requested.emit(self.ab))
            lay.addWidget(self._roll_btn)

    def set_score(self, v):
        if self._editable:
            self._score_spin.blockSignals(True)
            self._score_spin.setValue(v)
            self._score_spin.blockSignals(False)
        else:
            self._score_lbl.setText(str(v))
        mod = (v - 10) // 2
        self._mod_lbl.setText(sign(mod))
        self._mod_lbl.setStyleSheet(
            f"color:{TEAL2 if mod >= 0 else CRIM2};font-size:{FS_TITLE}px;font-weight:700;background:transparent;"
        )
        if self._roll_btn:
            self._roll_btn.setToolTip(f"Roll {self.ab} check ({sign(mod)})")

    def value(self):
        return self._score_spin.value() if self._editable else int(self._score_lbl.text())


def _spell_tooltip(spell: dict) -> str:
    """Full spell description for hover tooltips."""
    name = spell.get("name", "Spell")
    lvl = spell.get("level", 0)
    lvl_s = "Cantrip" if lvl == 0 else f"Level {lvl}"
    parts = [
        f"{name} ({lvl_s})",
        f"School: {spell.get('school', '?')}",
        f"Casting Time: {spell.get('casting_time', spell.get('cast_time', '?'))}",
        f"Range: {spell.get('range', '?')}",
        f"Components: {spell.get('components', '?')}",
        f"Duration: {spell.get('duration', '?')}",
    ]
    if spell.get("concentration"):
        parts.append("Concentration: Yes")
    if spell.get("ritual"):
        parts.append("Ritual: Yes")
    desc = spell.get("desc", "")
    if desc:
        parts.append("")
        parts.append(desc)
    higher = spell.get("higher_levels", "")
    if higher:
        parts.append("")
        parts.append(f"At Higher Levels: {higher}")
    return "\n".join(parts)


class SpellRow(QFrame):
    """One row in the spell list."""
    remove           = Signal(object)
    cast             = Signal(dict)
    cast_ritual      = Signal(dict)
    toggle_quick     = Signal(str, bool)   # (spell_name, pinned)
    prepared_toggled = Signal(object, bool)  # (row, checked)

    def __init__(self, spell, prepared=False, parent=None, locked=False, display_name=None):
        super().__init__(parent)
        self.spell = spell
        lvl = spell["level"]
        # Built fresh on every row, not a class attribute: a class-level
        # list literal is evaluated exactly once, at class-definition time
        # (this module's first import), so it would freeze to whatever
        # theme was active at app startup and never track a later switch.
        level_colors = [SURF3,TEAL,IND2,PURPLE,AMBER,GOLD,CRIMSON,"#8b0000","#6b0000","#4b0000"]
        lc = level_colors[min(lvl, 9)]
        self.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:7px;}}"
            f"QFrame:hover{{background:{SURF2};border-color:{BORDER2};}}"
        )
        lay = QHBoxLayout(self); lay.setContentsMargins(8,6,8,6); lay.setSpacing(8)

        # Level pill
        lvl_txt = "C" if lvl==0 else str(lvl)
        lvl_pill = h(lvl_txt, "white", FS_SMALL, bold=True, align=Qt.AlignCenter, wrap=False)
        lvl_pill.setFixedSize(28,28)
        lvl_pill.setStyleSheet(f"background:{lc};color:white;border-radius:14px;font-size:{FS_SMALL}px;font-weight:700;")
        lay.addWidget(lvl_pill)

        # Prepared checkbox — cantrips are always available (PHB p.201), and
        # bonus spells granted outside the normal preparation system (a feat
        # like Magic Initiate, a racial trait, etc.) work the same way: the
        # character just knows/can cast them, with no daily prep choice and
        # no competing for room against ordinary prepared spells. Both get
        # locked checked+disabled rather than a meaningful toggle.
        self._prep_cb = QCheckBox()
        self._prep_cb.setChecked(prepared)
        if lvl == 0:
            self._prep_cb.setChecked(True)
            self._prep_cb.setEnabled(False)
            self._prep_cb.setToolTip("Cantrips are always available — no preparation needed")
        elif locked:
            self._prep_cb.setChecked(True)
            self._prep_cb.setEnabled(False)
            self._prep_cb.setToolTip(
                "Granted outside normal preparation (feat/racial/class bonus spell) — "
                "always available and doesn't count against your prepared spell limit.")
        else:
            self._prep_cb.setToolTip("Prepared")
            self._prep_cb.toggled.connect(lambda checked: self.prepared_toggled.emit(self, checked))
        lay.addWidget(self._prep_cb)

        # Spell info
        info_col = QVBoxLayout(); info_col.setSpacing(1)
        name_row = QHBoxLayout(); name_row.setSpacing(6)
        self._name_lbl = h(display_name or spell["name"], TEXT, FS_BODY, bold=True, wrap=False)
        name_row.addWidget(self._name_lbl)
        if spell.get("concentration"):
            name_row.addWidget(badge("Conc", PURPLE, FS_TINY))
        if spell.get("ritual"):
            name_row.addWidget(badge("Rit", TEAL, FS_TINY))
        # Class-source badge — only shown for multiclass known-spell casters
        # (Sorcerer/Warlock etc.), set via set_class_tag() since attribution
        # can shift as spells are added/removed. Hidden by default.
        self._class_tag_lbl = badge("", TEXT3, FS_TINY)
        self._class_tag_lbl.setVisible(False)
        name_row.addWidget(self._class_tag_lbl)
        name_row.addStretch()
        info_col.addLayout(name_row)
        details = f"{spell.get('school','?')} · {spell.get('casting_time', spell.get('cast_time','?'))} · {spell.get('range','?')}"
        detail_lbl = h(details, TEXT2, FS_SMALL, wrap=True)
        detail_lbl.setMinimumHeight(36)
        info_col.addWidget(detail_lbl)
        lay.addLayout(info_col, 1)

        tip = _spell_tooltip(spell)
        self.setToolTip(tip)
        for w in (lvl_pill, self._prep_cb, detail_lbl):
            w.setToolTip(tip)

        # Star: pin to Quick Spells on Combat tab
        self._pinned = False
        self._star_btn = QPushButton("☆"); self._star_btn.setFixedSize(26,26)
        self._star_btn.setToolTip("Pin to Quick Spells (Combat tab)")
        self._star_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT3};font-size:15px;}}QPushButton:hover{{color:#ffd700;}}")
        self._star_btn.clicked.connect(self._on_star)
        lay.addWidget(self._star_btn)

        # Remove button
        rm = QPushButton("✕"); rm.setFixedSize(28,28)
        rm.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT3};font-size:16px;border-radius:14px;}}QPushButton:hover{{background:{CRIMSON};color:white;}}")
        rm.clicked.connect(lambda: self.remove.emit(self))
        lay.addWidget(rm)

    def set_display_name(self, text: str):
        """Update just the title label's text (Immersive Spells optional
        rule) -- leaves self.spell["name"] and everything else about the
        row (tooltip, context menu, cast/prep logic) untouched."""
        self._name_lbl.setText(text)

    def set_pinned(self, pinned: bool):
        self._pinned = pinned
        self._star_btn.setText("★" if pinned else "☆")
        color = "#ffd700" if pinned else TEXT3
        self._star_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{color};font-size:15px;}}QPushButton:hover{{color:#ffd700;}}")

    _TAG_COLORS = {
        "Sorcerer": INDIGO, "Warlock": PURPLE, "Bard": TEAL,
        "Ranger": "#4a8c3f", "Fighter (EK)": AMBER, "Rogue (AT)": AMBER,
    }

    def set_class_tag(self, class_name):
        """Show/hide the small class-source badge (e.g. 'SORC', 'LOCK').
        Pass None to hide it (single-class casters don't need this)."""
        if not class_name:
            self._class_tag_lbl.setVisible(False)
            return
        abbrev = {"Sorcerer":"SORC", "Warlock":"LOCK", "Bard":"BARD",
                  "Ranger":"RNGR", "Fighter (EK)":"EK", "Rogue (AT)":"AT"}.get(
                      class_name, class_name[:4].upper())
        color = self._TAG_COLORS.get(class_name, TEXT3)
        self._class_tag_lbl.setText(abbrev)
        self._class_tag_lbl.setStyleSheet(
            f"background:{color};color:white;font-size:{FS_TINY}px;font-weight:700;"
            f"border-radius:{FS_TINY}px;padding:2px 8px;")
        self._class_tag_lbl.setToolTip(f"Counts against your {class_name} known-spells pool")
        self._class_tag_lbl.setVisible(True)

    def _on_star(self):
        self._pinned = not self._pinned
        self.set_pinned(self._pinned)
        self.toggle_quick.emit(self.spell["name"], self._pinned)

    def is_prepared(self): return self._prep_cb.isChecked()
    def set_prepared(self, v): self._prep_cb.setChecked(v)
    def is_prepared(self): return self._prep_cb.isChecked()
    def set_can_ritual(self, v): self._can_ritual = bool(v)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu{{background:{SURF2};border:2px solid {BORDER2};color:{TEXT};font-size:{FS_BODY}px;padding:4px;}}"
                           f"QMenu::item{{padding:8px 20px;border-radius:4px;}}"
                           f"QMenu::item:selected{{background:{INDIGO};color:white;}}")
        detail_act = menu.addAction(f"📖  Show Details: {self.spell['name']}")
        menu.addSeparator()
        cast_act  = menu.addAction(f"🎲  Cast {self.spell['name']}")
        ritual_act = None
        if self.spell.get("ritual") and getattr(self, "_can_ritual", False):
            ritual_act = menu.addAction(
                f"📜  Cast {self.spell['name']} as Ritual (no slot, +10 min cast time)")
        prep_act  = menu.addAction("✓  Toggle Prepared")
        star_act  = menu.addAction("★  Pin to Quick Spells" if not self._pinned else "☆  Unpin from Quick Spells")
        menu.addSeparator()
        rm_act    = menu.addAction("✕  Remove from list")
        action = menu.exec(event.globalPos())
        if action == detail_act:
            from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget
            s = self.spell
            lvl_txt = "Cantrip" if s.get("level",0)==0 else f"Level {s.get('level','?')}"
            desc = s.get("desc") or s.get("description","")
            higher = s.get("higher_levels","") or s.get("higher","")
            detail = (f"<b>{s['name']}</b>  [{lvl_txt} {s.get('school','').title()}]<br>"
                      f"<i>Casting Time:</i> {s.get('casting_time',s.get('cast_time','—'))}<br>"
                      f"<i>Range:</i> {s.get('range','—')}  &nbsp; <i>Duration:</i> {s.get('duration','—')}<br>"
                      f"<i>Components:</i> {s.get('components','—')}<br><br>"
                      f"{desc}<br><br>" + (f"<i>At Higher Levels:</i> {higher}" if higher else ""))
            dlg = QDialog(); dlg.setWindowTitle(s['name']); dlg.setMinimumWidth(500)
            lay = QVBoxLayout(dlg)
            lbl = QLabel(detail); lbl.setWordWrap(True); lbl.setOpenExternalLinks(False)
            lbl.setStyleSheet("font-size:13px;padding:8px;")
            sa = QScrollArea(); sa.setWidgetResizable(True)
            inner = QWidget(); il = QVBoxLayout(inner); il.addWidget(lbl)
            sa.setWidget(inner); lay.addWidget(sa)
            from PySide6.QtWidgets import QDialogButtonBox
            bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(dlg.reject)
            lay.addWidget(bb); dlg.exec()
        elif action == cast_act:  self.cast.emit(self.spell)
        elif ritual_act is not None and action == ritual_act: self.cast_ritual.emit(self.spell)
        elif action == prep_act: self._prep_cb.setChecked(not self._prep_cb.isChecked())
        elif action == star_act: self._on_star()
        elif action == rm_act:  self.remove.emit(self)
