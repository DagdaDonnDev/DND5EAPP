"""
Main application window.
Shows:  StartMenu → CharacterWizard → CharacterSheet
        StartMenu → Load → CharacterSheet

Author: Ethan O'Brien
Date: 2026-08-20
"""
import os, sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QFont, QAction
from dnd_app.ui.style.theme import *
from ..shared import *
# `import *` skips underscore-prefixed names when a module has no
# __all__ (shared.py doesn't) — _btn needs an explicit import for that
# reason, same as sheet.py.
from ..shared import _btn
from .wizard import CharacterWizard
from .sheet import CharacterSheet
from dnd_app.core.character import new_character
from dnd_app.core.save_load import list_saved_characters, load_character, delete_character

# ── Recent files helpers ──────────────────────────────────────────────────────
import json as _json_mod
_RECENT_FILE = os.path.join(os.path.expanduser("~"), ".dnd5e_recent.json")

def _load_recent() -> list:
    try:
        with open(_RECENT_FILE) as _f: paths = _json_mod.load(_f)
        return [p for p in paths if os.path.exists(p)][:8]
    except Exception: return []

def _save_recent(path: str):
    recent = _load_recent(); path = os.path.abspath(path)
    if path in recent: recent.remove(path)
    recent.insert(0, path)
    try:
        with open(_RECENT_FILE, "w") as _f: _json_mod.dump(recent[:8], _f)
    except Exception: pass



# Same shape/param order as shared.py's h() — safe direct alias.
_lbl = h


class StartMenu(QWidget):
    new_char  = Signal()
    load_char = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0)

        hero = QFrame(); hero.setStyleSheet(f"QFrame{{background:{SURF};}}")
        hl = QVBoxLayout(hero); hl.setContentsMargins(60,60,60,40); hl.setSpacing(16)
        hl.setAlignment(Qt.AlignCenter)

        title = QLabel("⚔  MIMIC")
        tf = QFont(); tf.setBold(True); tf.setPointSize(28)
        title.setFont(tf); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{GOLD2};background:transparent;")
        hl.addWidget(title)
        hl.addWidget(_lbl("A D&D 5e Character Creator", GOLD, FS_BODY, bold=True, align=Qt.AlignCenter))
        hl.addWidget(_lbl("Build, track, and play your character from creation to legend.", TEXT2, FS_BODY+2, align=Qt.AlignCenter))

        btn_row = QHBoxLayout(); btn_row.setSpacing(20); btn_row.setAlignment(Qt.AlignCenter)
        new_btn = pill_btn("⚔  Create New Character", INDIGO)
        new_btn.setFixedSize(280, 54)
        new_btn.clicked.connect(self.new_char)
        btn_row.addWidget(new_btn)
        hl.addLayout(btn_row)
        root.addWidget(hero, 1)

        saved_frame = QFrame(); saved_frame.setStyleSheet(f"QFrame{{background:{BG};}}")
        sl = QVBoxLayout(saved_frame); sl.setContentsMargins(40,24,40,24); sl.setSpacing(12)
        sl.addWidget(_lbl("Saved Characters", GOLD, FS_HEAD, bold=True))

        saved = list_saved_characters()
        if not saved:
            sl.addWidget(_lbl("No saved characters yet. Create one to get started!", TEXT2, FS_BODY))
        else:
            scroll = QScrollArea(); scroll.setWidgetResizable(True)
            inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
            il = QVBoxLayout(inner); il.setSpacing(8)
            for entry in saved:
                path = entry.get("filepath", "")
                if not path or not os.path.exists(path):
                    continue
                try:
                    c = load_character(path)
                except Exception:
                    continue
                row = QFrame()
                row.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}QFrame:hover{{border-color:{BORDER2};background:{SURF2};}}")
                rl = QHBoxLayout(row); rl.setContentsMargins(16,12,16,12); rl.setSpacing(12)
                col = QVBoxLayout(); col.setSpacing(3)
                col.addWidget(_lbl(c.get("name","Unknown"), TEXT, FS_BODY+2, bold=True, wrap=False))
                classes = c.get("classes",[])
                cls_str = "  ·  ".join(f"{x['class']} {x['level']}" + (f" ({x['subclass']})" if x.get('subclass') else "") for x in classes)
                race = c.get("species") or c.get("race","")
                col.addWidget(_lbl(f"{race}  |  {cls_str}" if race else cls_str, TEXT2, FS_SMALL, wrap=False))
                rl.addLayout(col, 1)
                load_btn = _btn("Load →", INDIGO, variant="cta", width=100, height=38,
                                 radius=8, text_color=IND2, hover_text="white", font_size=FS_SMALL)
                load_btn.clicked.connect(lambda checked, p=path: self.load_char.emit(p))
                rl.addWidget(load_btn)
                del_btn = _btn("✕", CRIMSON, variant="ghost", width=38, height=38, radius=8,
                                border_alpha=0x55, text_color=TEXT3, font_size=16)
                del_btn.setStyleSheet(del_btn.styleSheet() + f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
                del_btn.clicked.connect(lambda checked, p=path, r=row: self._delete_saved_row(p, r))
                rl.addWidget(del_btn)
                il.addWidget(row)
            il.addStretch(); scroll.setWidget(inner); sl.addWidget(scroll, 1)

        root.addWidget(saved_frame, 2)

    def _delete_saved_row(self, path: str, row: QFrame):
        if QMessageBox.question(
            self, "Delete?", "Delete this character permanently?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            delete_character(path)
            row.deleteLater()


class SettingsDialog(QDialog):
    """Consolidates the theme chooser, a font-size scale option, and
    optional-rules toggles. Only wires toggles for rules that already
    have real, meaningful enforcement built — feat prerequisites and
    multiclass ability score requirements — rather than adding
    switches for things with no actual mechanic behind them."""

    def __init__(self, app_window, parent=None):
        super().__init__(parent)
        # main_window.py's `from .theme import *` only ever captured
        # whatever the theme was at the moment this module was first
        # imported (Python's `import *` is a one-time snapshot, not a
        # live binding) -- every dialog/window built here was frozen at
        # startup's theme regardless of later switches, unlike sheet.py/
        # wizard.py/levelup_panel.py, which already call this at the top
        # of their own __init__.
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
        self.app_window = app_window
        self.setWindowTitle("Settings")
        self.setMinimumSize(420, 420)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        root = QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(14)
        root.addWidget(_lbl("Settings", GOLD2, size=22, bold=True))

        # ── Appearance ────────────────────────────────────────────────────
        app_card = QFrame(); app_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
        acl = QVBoxLayout(app_card); acl.setContentsMargins(14,12,14,14); acl.setSpacing(8)
        acl.addWidget(_lbl("APPEARANCE", TEAL2, FS_SMALL, bold=True))

        theme_row = QHBoxLayout()
        theme_row.addWidget(_lbl("Theme:", TEXT2, FS_BODY))
        self._theme_combo = QComboBox()
        for name in THEMES:
            self._theme_combo.addItem(name)
        current = getattr(app_window, "_current_theme_name", "(Dark) Obsidian")
        idx = self._theme_combo.findText(current)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self._theme_combo, 1)
        acl.addLayout(theme_row)

        font_row = QHBoxLayout()
        font_row.addWidget(_lbl("UI text size:", TEXT2, FS_BODY))
        self._font_combo = QComboBox()
        self._font_combo.addItems(["Small", "Medium (default)", "Large"])
        char = getattr(app_window, "_sheet", None)
        saved_scale = "Medium (default)"
        if char and char.char.get("ui_font_scale"):
            saved_scale = char.char["ui_font_scale"]
        idxf = self._font_combo.findText(saved_scale)
        if idxf >= 0:
            self._font_combo.setCurrentIndex(idxf)
        self._font_combo.currentTextChanged.connect(self._on_font_scale_changed)
        font_row.addWidget(self._font_combo, 1)
        acl.addLayout(font_row)
        root.addWidget(app_card)

        # ── Advancement: milestone vs. tracked XP ──────────────────────────
        adv_card = QFrame(); adv_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {qa(GOLD,0x33)};border-radius:10px;}}")
        advl = QVBoxLayout(adv_card); advl.setContentsMargins(14,12,14,14); advl.setSpacing(8)
        advl.addWidget(_lbl("ADVANCEMENT", GOLD2, FS_SMALL, bold=True))

        adv_row = QHBoxLayout()
        adv_row.addWidget(_lbl("Leveling:", TEXT2, FS_BODY))
        self._leveling_combo = QComboBox()
        self._leveling_combo.addItem("Milestone (DM decides when you level up)", "milestone")
        self._leveling_combo.addItem("Experience Points (XP)", "xp")
        cur_mode = char.char.get("leveling_mode", "milestone") if char else "milestone"
        idxl = self._leveling_combo.findData(cur_mode)
        if idxl >= 0:
            self._leveling_combo.setCurrentIndex(idxl)
        adv_row.addWidget(self._leveling_combo, 1)
        advl.addLayout(adv_row)
        advl.addWidget(_lbl(
            "XP mode adds an experience tracker to the header and the "
            "Choices tab, and flags your character as ready to level up "
            "once you cross the next threshold — leveling up itself is "
            "still a manual click, same as milestone.", TEXT3, FS_TINY))
        root.addWidget(adv_card)

        # ── Character Rules, Tasha's Cauldron Options, and DM Secrets are
        # three separate cards, split by what kind of toggle each one is:
        # core enforcement rules, Tasha's Cauldron of Everything's "swap
        # something at an ASI level" class options, and purely cosmetic
        # flavor toggles.
        rules_card = QFrame(); rules_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
        rcl = QVBoxLayout(rules_card); rcl.setContentsMargins(14,12,14,14); rcl.setSpacing(8)
        rcl.addWidget(_lbl("CHARACTER RULES", TEAL2, FS_SMALL, bold=True))

        opt_rules = {}
        if char:
            opt_rules = char.char.setdefault("optional_rules", {
                "feat_prereqs": True, "multiclass_ability_reqs": True,
                "dmg_xge_optional_actions": True,
                "eldritch_versatility": False, "harness_divine_power": False,
                "martial_versatility": False,
                "cantrip_versatility": False, "bardic_versatility": False,
                "sorcerous_versatility": False, "max_hp_per_level": False,
                "immersive_spells": False, "critical_flavor": False,
                "component_restrictions": False,
            })

        self._feat_prereq_cb = QCheckBox("Enforce feat prerequisites (race, ability scores, etc.)")
        self._feat_prereq_cb.setChecked(opt_rules.get("feat_prereqs", True))
        self._feat_prereq_cb.setToolTip(
            "When off, any feat can be picked at level-up regardless of its "
            "listed prerequisite — useful for tables that allow feat flexibility.")
        rcl.addWidget(self._feat_prereq_cb)

        self._multiclass_cb = QCheckBox("Enforce multiclass ability score requirements (13+)")
        self._multiclass_cb.setChecked(opt_rules.get("multiclass_ability_reqs", True))
        self._multiclass_cb.setToolTip(
            "When off, any class can be multiclassed into regardless of ability "
            "scores — useful for tables that don't use this restriction.")
        rcl.addWidget(self._multiclass_cb)

        self._dmg_xge_cb = QCheckBox("Show DMG/XGE optional combat actions (Disarm, Overrun, "
                                      "Tumble, Mark, Healing Surge, etc.)")
        self._dmg_xge_cb.setChecked(opt_rules.get("dmg_xge_optional_actions", True))
        self._dmg_xge_cb.setToolTip(
            "When off, hides these variant rules from the Actions tab entirely — "
            "useful for tables that stick to core PHB rules only.")
        rcl.addWidget(self._dmg_xge_cb)

        self._max_hp_per_level_cb = QCheckBox(
            "Maximum hit points per level — use each class's maximum hit die "
            "value instead of the average/rolled result")
        self._max_hp_per_level_cb.setChecked(opt_rules.get("max_hp_per_level", False))
        self._max_hp_per_level_cb.setToolTip(
            "When on, every level (not just 1st) uses the hit die's maximum "
            "value + CON modifier instead of the PHB average formula "
            "(floor(hd/2)+1 + CON) — e.g. a Barbarian gains 12 + CON at "
            "every level instead of 12 + CON at 1st and 7 + CON afterward. "
            "A common table variant, not an official rule.")
        rcl.addWidget(self._max_hp_per_level_cb)

        self._component_restrictions_cb = QCheckBox(
            "Component Restrictions — Blinded/Gagged/Restrained block casting "
            "spells needing sight/verbal/somatic components")
        self._component_restrictions_cb.setChecked(opt_rules.get("component_restrictions", False))
        self._component_restrictions_cb.setToolTip(
            "When on, a spell can't be cast if an active condition blocks "
            "something it specifically needs: Blinded blocks any non-self-only "
            "spell (can't see a target), Gagged (a homebrew condition, not an "
            "official one) blocks spells with a verbal component, Restrained "
            "blocks spells with a somatic component. Only checked per-spell — "
            "e.g. a self-only spell with no verbal component still works while "
            "Blinded and Gagged. A table-variant interpretation, not RAW.")
        rcl.addWidget(self._component_restrictions_cb)
        root.addWidget(rules_card)

        # ── Tasha's Cauldron of Everything: "swap something at an ASI
        # level" class options, all the same shape, grouped together ──────
        tasha_card = QFrame(); tasha_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
        tcl = QVBoxLayout(tasha_card); tcl.setContentsMargins(14,12,14,14); tcl.setSpacing(8)
        tcl.addWidget(_lbl("TASHA'S CAULDRON OPTIONS", TEAL2, FS_SMALL, bold=True))

        self._eldritch_versatility_cb = QCheckBox(
            "Eldritch Versatility (Warlock, TCoE) — swap a cantrip/Pact Boon/"
            "Mystic Arcanum at each ASI level")
        self._eldritch_versatility_cb.setChecked(opt_rules.get("eldritch_versatility", False))
        self._eldritch_versatility_cb.setToolTip(
            "When on, adds the option to change your Pact Magic cantrips, Pact "
            "Boon, or Mystic Arcanum spells whenever you'd gain an Ability Score "
            "Improvement — an optional Tasha's Cauldron of Everything rule.")
        tcl.addWidget(self._eldritch_versatility_cb)

        self._harness_divine_power_cb = QCheckBox(
            "Harness Divine Power (TCE) — Cleric/Paladin: bonus action, expend Channel "
            "Divinity to regain a spell slot")
        self._harness_divine_power_cb.setChecked(opt_rules.get("harness_divine_power", False))
        self._harness_divine_power_cb.setToolTip(
            "When on, Cleric (2nd level+) and Paladin (3rd level+) gain this optional "
            "Tasha's Cauldron of Everything class feature: touch your holy symbol as a "
            "bonus action to regain one expended spell slot of level ≤ half your "
            "proficiency bonus (rounded up), a limited number of times per long rest.")
        tcl.addWidget(self._harness_divine_power_cb)

        self._martial_versatility_cb = QCheckBox(
            "Martial Versatility (TCE) — Fighter/Paladin/Ranger: swap a Fighting Style at any "
            "level that grants an Ability Score Improvement")
        self._martial_versatility_cb.setChecked(opt_rules.get("martial_versatility", False))
        self._martial_versatility_cb.setToolTip(
            "When on, Fighter, Paladin, and Ranger characters can replace one Fighting Style "
            "they know with another available to their class, at each level that grants an "
            "Ability Score Improvement — a Tasha's Cauldron of Everything optional rule.")
        tcl.addWidget(self._martial_versatility_cb)

        self._cantrip_versatility_cb = QCheckBox(
            "Cantrip Versatility (TCE) — Cleric/Druid: swap a cantrip at any level that grants "
            "an Ability Score Improvement")
        self._cantrip_versatility_cb.setChecked(opt_rules.get("cantrip_versatility", False))
        self._cantrip_versatility_cb.setToolTip(
            "When on, Cleric and Druid characters can replace one cantrip they know with "
            "another from their class's spell list, at each level that grants an Ability "
            "Score Improvement — a Tasha's Cauldron of Everything optional rule.")
        tcl.addWidget(self._cantrip_versatility_cb)

        self._bardic_versatility_cb = QCheckBox(
            "Bardic Versatility (TCE) — Bard: swap an Expertise skill or a cantrip at any level "
            "that grants an Ability Score Improvement")
        self._bardic_versatility_cb.setChecked(opt_rules.get("bardic_versatility", False))
        self._bardic_versatility_cb.setToolTip(
            "When on, Bard characters can replace one Expertise skill or one cantrip they know, "
            "at each level that grants an Ability Score Improvement — a Tasha's Cauldron of "
            "Everything optional rule.")
        tcl.addWidget(self._bardic_versatility_cb)

        self._sorcerous_versatility_cb = QCheckBox(
            "Sorcerous Versatility (TCE) — Sorcerer: swap a Metamagic option or a cantrip at "
            "any level that grants an Ability Score Improvement")
        self._sorcerous_versatility_cb.setChecked(opt_rules.get("sorcerous_versatility", False))
        self._sorcerous_versatility_cb.setToolTip(
            "When on, Sorcerer characters can replace one Metamagic option or one cantrip they "
            "know, at each level that grants an Ability Score Improvement — a Tasha's Cauldron "
            "of Everything optional rule.")
        tcl.addWidget(self._sorcerous_versatility_cb)
        root.addWidget(tasha_card)

        # ── DM Secrets: purely cosmetic flavor toggles, grouped separately
        # at the bottom since they have no effect on actual gameplay ──────
        secrets_card = QFrame(); secrets_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
        scl = QVBoxLayout(secrets_card); scl.setContentsMargins(14,12,14,14); scl.setSpacing(8)
        scl.addWidget(_lbl("DM SECRETS", GOLD2, FS_SMALL, bold=True))

        self._immersive_spells_cb = QCheckBox(
            "Immersive Spells — spell names in the list change to reflect what "
            "your character can actually say")
        self._immersive_spells_cb.setChecked(opt_rules.get("immersive_spells", False))
        self._immersive_spells_cb.setToolTip(
            "Purely cosmetic — only the spell list's title text changes, never "
            "the underlying spell, tooltip, or casting. Wild Shaped without "
            "Beast Spells: titles become your beast form's noise, stretched to "
            "roughly the original word's length. Raging: titles collapse to a "
            "shout (\"SMASH!\" for most, a few iconic spells get their own "
            "line). A Paladin with an Oath: titles are prefixed with a short "
            "phrase themed to that Oath.")
        scl.addWidget(self._immersive_spells_cb)

        self._critical_flavor_cb = QCheckBox(
            "Critical Flavor — a random quip at the bottom of the screen when your character dies")
        self._critical_flavor_cb.setChecked(opt_rules.get("critical_flavor", False))
        self._critical_flavor_cb.setToolTip(
            "Purely cosmetic — a small toast under the death screen, picked at random "
            "from a pool of gallows-humor one-liners. No gameplay effect.")
        scl.addWidget(self._critical_flavor_cb)
        root.addWidget(secrets_card)

        root.addStretch()
        btn_row = QHBoxLayout(); btn_row.addStretch()
        close_btn = QPushButton("Done"); close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2, padding="4px 24px").styleSheet())
        close_btn.clicked.connect(self._on_done)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _on_theme_changed(self, name):
        # _set_theme() below is synchronous and, with a character sheet
        # open, rebuilds the whole CharacterSheet (12 mixins, hundreds of
        # widgets) -- on a big character that's a noticeable freeze with
        # zero visual feedback otherwise, since Qt can't repaint anything
        # (including this combo going disabled) until it's back in the
        # event loop. Disable the combo, switch to a wait cursor, and
        # force a repaint via processEvents() *before* starting the heavy
        # work so the user actually sees something happened.
        self._theme_combo.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            self.app_window._set_theme(name)
        finally:
            QApplication.restoreOverrideCursor()
        # This dialog's own background/labels were built once, from
        # whatever theme was active when it opened -- _set_theme()'s
        # rebuild-in-place only covers the sheet/wizard/start menu, none
        # of which is this dialog. Close and let _open_settings()'s loop
        # reopen a fresh one, which picks up the new colors the same way
        # every other themed window already does at its own __init__.
        self._reopen_for_theme = True
        self.close()

    def _on_font_scale_changed(self, scale_text):
        from dnd_app.ui.style import theme
        theme.set_font_scale(scale_text)
        sheet = getattr(self.app_window, "_sheet", None)
        if sheet:
            sheet.char["ui_font_scale"] = scale_text
            sheet._mark_dirty()
        # Re-run the same rebuild path theme switching uses: it re-applies
        # build_qss() (now reading the new _font_scale) and reconstructs
        # CharacterSheet, whose __init__ calls sync_globals() to pick up
        # the freshly recomputed FS_* values -- without this, the saved
        # scale had nowhere to actually take effect. Same wait-cursor
        # treatment as _on_theme_changed -- this is the same expensive
        # synchronous rebuild.
        self._font_combo.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            self.app_window._set_theme(self.app_window._current_theme_name)
        finally:
            QApplication.restoreOverrideCursor()
        # Same reasoning as _on_theme_changed: this dialog's own text
        # sizes were also fixed at __init__ and won't reflect the new
        # scale without reopening.
        self._reopen_for_theme = True
        self.close()

    def _on_done(self):
        sheet = getattr(self.app_window, "_sheet", None)
        if sheet:
            sheet.char["leveling_mode"] = self._leveling_combo.currentData()
            sheet.char.setdefault("optional_rules", {})
            sheet.char["optional_rules"]["feat_prereqs"] = self._feat_prereq_cb.isChecked()
            sheet.char["optional_rules"]["multiclass_ability_reqs"] = self._multiclass_cb.isChecked()
            sheet.char["optional_rules"]["dmg_xge_optional_actions"] = self._dmg_xge_cb.isChecked()
            sheet.char["optional_rules"]["eldritch_versatility"] = self._eldritch_versatility_cb.isChecked()
            sheet.char["optional_rules"]["harness_divine_power"] = self._harness_divine_power_cb.isChecked()
            sheet.char["optional_rules"]["martial_versatility"] = self._martial_versatility_cb.isChecked()
            sheet.char["optional_rules"]["cantrip_versatility"] = self._cantrip_versatility_cb.isChecked()
            sheet.char["optional_rules"]["bardic_versatility"] = self._bardic_versatility_cb.isChecked()
            sheet.char["optional_rules"]["sorcerous_versatility"] = self._sorcerous_versatility_cb.isChecked()
            sheet.char["optional_rules"]["max_hp_per_level"] = self._max_hp_per_level_cb.isChecked()
            sheet.char["optional_rules"]["component_restrictions"] = self._component_restrictions_cb.isChecked()
            sheet.char["optional_rules"]["immersive_spells"] = self._immersive_spells_cb.isChecked()
            sheet.char["optional_rules"]["critical_flavor"] = self._critical_flavor_cb.isChecked()
            # Saving here alone doesn't recompute char["resources"]
            # (only a full rebuild does), so a newly-toggled optional
            # feature's resource needs this explicit refresh rather
            # than waiting for some unrelated character change to
            # trigger a rebuild later.
            if hasattr(sheet, "ctrl"):
                sheet.ctrl.refresh()
            if hasattr(sheet, "_refresh_action_tabs"):
                sheet._refresh_action_tabs()
            sheet._mark_dirty()
        self.accept()


def _find_readme_text() -> str:
    """Locate and read README.md, whether running from source (repo
    root, two levels up from this file) or from a frozen PyInstaller
    build (bundled next to the executable via sys._MEIPASS)."""
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(getattr(sys, "_MEIPASS", ""), "README.md"))
        candidates.append(os.path.join(os.path.dirname(sys.executable), "README.md"))
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "README.md"))
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                continue
    return ("# MIMIC\n\nA Complete D&D 5e Character Creator & Management Tool.\n\n"
            "Created by Ethan O'Brien.\n\nThank you for downloading MIMIC, and for "
            "supporting the project.\n\n(The full README.md could not be found "
            "alongside this build.)")


class CreditsDialog(QDialog):
    """Shows the project README — what the app is, what it covers, and
    its credits — in a scrollable, read-only view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
        self.setWindowTitle("Credits")
        self.setMinimumSize(640, 560)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16); lay.setSpacing(12)

        viewer = QTextBrowser()
        viewer.setOpenExternalLinks(True)
        viewer.setStyleSheet(
            f"QTextBrowser{{background:{SURF};border:1px solid {BORDER};"
            f"border-radius:8px;padding:10px;color:{TEXT};font-size:{FS_BODY}px;}}")
        viewer.setMarkdown(_find_readme_text())
        lay.addWidget(viewer, 1)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        close_btn = QPushButton("Close"); close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2, padding="4px 24px").styleSheet())
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        lay.addLayout(btn_row)


class CharacterCreatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        import os
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("MIMIC")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        from dnd_app.ui.style.theme import build_qss
        _initial_qss = build_qss()
        self.setStyleSheet(_initial_qss)
        # Also set at the QApplication level -- see _set_theme()'s comment
        # for why a single widget's setStyleSheet() isn't enough to theme
        # QToolTip everywhere (this is the initial app-launch styling,
        # before any theme switch has happened, so it needs the same fix).
        _app = QApplication.instance()
        if _app is not None:
            _app.setStyleSheet(_initial_qss)
        # Must match a real THEMES key ("(Dark) Obsidian", not bare
        # "Obsidian") -- theme.py's own default palette used until
        # apply_theme() is ever called happens to look like this theme,
        # but the bookkeeping name has to be a real key or every
        # `saved_theme in THEMES`/`findText(current)` check downstream
        # silently fails to match it.
        self._current_theme_name = "(Dark) Obsidian"

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        self._wizard = None
        self._sheet  = None
        self._dice_roller = None

        self._start = StartMenu(self)
        self._start.new_char.connect(self._go_wizard)
        self._start.load_char.connect(self._go_sheet_from_path)
        self._stack.addWidget(self._start)

        self._build_menu()

        # Easter egg: typing "cheese" anywhere in the app pops a tiny
        # cheese icon in the corner for a few seconds -- no purpose,
        # just for fun. An application-wide event filter is the only
        # way to catch it regardless of which widget currently has
        # focus (a text field, a spell search box, the sheet itself).
        self._cheese_buffer = ""
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            text = event.text()
            if text:
                self._cheese_buffer = (self._cheese_buffer + text.lower())[-6:]
                if self._cheese_buffer == "cheese":
                    self._show_cheese_easter_egg()
                    self._cheese_buffer = ""
        # Opt-in trace, off by default -- see dnd_app/ui/diagnostics.py.
        if event.type() == QEvent.Show:
            from dnd_app.ui.diagnostics import log_window_show
            log_window_show(obj, event)
        return super().eventFilter(obj, event)

    def _show_cheese_easter_egg(self):
        if not hasattr(self, "_cheese_lbl"):
            self._cheese_lbl = QLabel("\U0001f9c0", self)
            self._cheese_lbl.setStyleSheet("font-size:32px;background:transparent;")
            self._cheese_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            self._cheese_timer = QTimer(self)
            self._cheese_timer.setSingleShot(True)
            self._cheese_timer.timeout.connect(self._cheese_lbl.hide)
        self._cheese_lbl.adjustSize()
        self._cheese_lbl.move(self.width() - self._cheese_lbl.width() - 18, 46)
        self._cheese_lbl.raise_()
        self._cheese_lbl.show()
        self._cheese_timer.start(5000)

    _GOLDEN_MENU_QSS = (
        "QMenuBar{background:#3a2e05;color:#f5cc50;}"
        "QMenuBar::item{background:transparent;color:#f5cc50;padding:4px 10px;}"
        "QMenuBar::item:selected{background:#f5cc50;color:#3a2e05;}"
        "QMenu{background:#3a2e05;color:#f5cc50;border:2px solid #f5cc50;}"
        "QMenu::item{padding:6px 20px;}"
        "QMenu::item:selected{background:#f5cc50;color:#3a2e05;}"
    )

    def _apply_name_easter_egg(self, char):
        """If the loaded character is named after this app's creator,
        the menu bar goes gold -- regardless of the active theme. A
        widget's own setStyleSheet() takes precedence over the window's,
        so this override survives later theme switches without needing
        to be re-applied from _set_theme()."""
        name = (char.get("name") or "").strip().lower()
        self.menuBar().setStyleSheet(
            self._GOLDEN_MENU_QSS if name == "ethan o'brien" else "")

    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("&File")
        a = QAction("New Character", self); a.setShortcut("Ctrl+N"); a.triggered.connect(self._go_wizard); fm.addAction(a)
        a = QAction("Open…", self);         a.setShortcut("Ctrl+O"); a.triggered.connect(self._load_dialog); fm.addAction(a)
        self._recent_menu = fm.addMenu("Open Recent"); self._rebuild_recent_menu()
        a = QAction("Save", self);           a.setShortcut("Ctrl+S"); a.triggered.connect(self._save); fm.addAction(a)
        a = QAction("Export…", self);        a.setShortcut("Ctrl+E"); a.triggered.connect(self._export_dialog); fm.addAction(a)
        a = QAction("Duplicate Character", self); a.setShortcut("Ctrl+Shift+D"); a.triggered.connect(self._duplicate_character); fm.addAction(a)
        fm.addSeparator()
        a = QAction("Quit", self);           a.setShortcut("Ctrl+Q"); a.triggered.connect(self.close); fm.addAction(a)

        tm = mb.addMenu("&Tools")
        a = QAction("🎲  Dice Roller", self); a.setShortcut("Ctrl+D"); a.triggered.connect(self._open_dice_roller); tm.addAction(a)
        a = QAction("⏸  Short Rest",  self); a.setShortcut("Ctrl+R"); a.triggered.connect(self._short_rest);       tm.addAction(a)
        a = QAction("🌙  Long Rest",   self); a.setShortcut("Ctrl+Shift+R"); a.triggered.connect(self._long_rest); tm.addAction(a)

        # Settings/Credits are single actions, not menus with one item
        # inside them -- addAction() straight onto the menu bar makes
        # each a direct single-click, no dropdown to open first.
        a = QAction("⚙  Settings…", self); a.setShortcut("Ctrl+,"); a.triggered.connect(self._open_settings); mb.addAction(a)
        a = QAction("Credits", self); a.triggered.connect(self._open_credits); mb.addAction(a)

    def _open_settings(self):
        # SettingsDialog's own background/labels are built once, at
        # __init__, from whatever theme was active at that moment --
        # _set_theme() (fired live as soon as the Theme combo inside this
        # very dialog changes) rebuilds the sheet/wizard/start menu in
        # place, but has no way to restyle a dialog it doesn't own the
        # reference to. Rather than hand-restyle every already-built
        # child widget in place, SettingsDialog closes itself and sets
        # _reopen_for_theme when its own theme combo changes -- this
        # loop just builds a fresh one (picking up the new colors from
        # scratch, same as every other rebuild-on-theme-switch spot)
        # until the user actually dismisses it normally.
        from dnd_app.ui.pages.main_window import SettingsDialog
        while True:
            dlg = SettingsDialog(self, self)
            dlg.exec()
            if not getattr(dlg, "_reopen_for_theme", False):
                break

    def _open_credits(self):
        from dnd_app.ui.pages.main_window import CreditsDialog
        dlg = CreditsDialog(self)
        dlg.exec()

    def _set_theme(self, name):
        from dnd_app.ui.style.theme import apply_theme
        self._switching_theme = True
        try:
            qss = apply_theme(name)
            self.setStyleSheet(qss)
            # QToolTip (and a few other selectors) don't reliably cascade
            # from a single widget's setStyleSheet() down to tooltips
            # shown by unrelated descendants -- Qt only guarantees that
            # for a stylesheet set at the QApplication level. Without
            # this, a tooltip triggered anywhere outside whichever widget
            # actually got setStyleSheet() falls back to the OS's native
            # tooltip look regardless of the app's active theme.
            app = QApplication.instance()
            if app is not None:
                app.setStyleSheet(qss)
            self._current_theme_name = name
            if self._sheet:
                char = self._sheet.char
                char["theme"] = name
                cur_tab = self._sheet._tabs.currentIndex()
                self._show_sheet(char)
                if self._sheet:
                    self._sheet._tabs.setCurrentIndex(cur_tab)

            # CharacterWizard has the exact same never-rebuilt-on-theme-
            # switch gap StartMenu/CharacterSheet had -- Settings is
            # reachable mid-wizard too, and its own sync_globals() call
            # only ever runs once, at construction. Rebuilt in place,
            # preserving in-progress selections (self.char) and which
            # step the player was on, same pattern as the sheet above.
            if self._wizard:
                was_current_wizard = (self._stack.currentWidget() is self._wizard)
                old_char, old_step = self._wizard.char, self._wizard._step
                self._stack.removeWidget(self._wizard); self._wizard.deleteLater()
                self._wizard = CharacterWizard(self)
                self._wizard.char = old_char
                self._wizard.done.connect(self._show_sheet)
                self._stack.addWidget(self._wizard)
                self._wizard._step = old_step
                steps = [self._wizard._step1, self._wizard._step2, self._wizard._step3,
                         self._wizard._step4, self._wizard._step5]
                steps[old_step].populate(self._wizard.char)
                self._wizard._stack.setCurrentIndex(old_step)
                self._wizard._update_pills()
                if was_current_wizard:
                    self._stack.setCurrentWidget(self._wizard)

            # StartMenu is built once at app startup, so a theme switch
            # (Settings is reachable from the menu bar regardless of
            # which screen is showing) needs it explicitly rebuilt in
            # place, restoring which stack widget was current if
            # StartMenu itself was showing.
            was_current_start = (self._stack.currentWidget() is self._start)
            self._stack.removeWidget(self._start); self._start.deleteLater()
            self._start = StartMenu(self)
            self._start.new_char.connect(self._go_wizard)
            self._start.load_char.connect(self._go_sheet_from_path)
            self._stack.insertWidget(0, self._start)
            if was_current_start:
                self._stack.setCurrentWidget(self._start)

            # The Dice Roller is the one persistent, non-modal window
            # that can genuinely outlive a theme switch (it isn't inside
            # self._stack, and isn't rebuilt/closed by anything else
            # here) -- rebuilt in place, preserving its screen position
            # and only re-shown if it was actually visible.
            if self._dice_roller:
                from dnd_app.ui.dialogs.dice_roller import DiceRollerPanel
                was_visible = self._dice_roller.isVisible()
                pos = self._dice_roller.pos()
                dice_char = self._dice_roller.char
                self._dice_roller.deleteLater()
                self._dice_roller = DiceRollerPanel(dice_char, parent=self)
                self._dice_roller.move(pos)
                if was_visible:
                    self._dice_roller.show()
        finally:
            self._switching_theme = False

    def _go_wizard(self):
        if self._wizard:
            self._stack.removeWidget(self._wizard); self._wizard.deleteLater()
        self._wizard = CharacterWizard(self)
        self._wizard.done.connect(self._show_sheet)
        self._stack.addWidget(self._wizard)
        self._stack.setCurrentWidget(self._wizard)

    def _go_sheet_from_path(self, path: str):
        try:
            char = load_character(path); self._show_sheet(char)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", str(e))

    def _show_sheet(self, char: dict):
        from dnd_app.ui.style import theme
        theme.set_font_scale(char.get("ui_font_scale", "Medium (default)"))
        self._apply_name_easter_egg(char)
        # Apply this character's own theme (if it has a valid one and it
        # differs from what's currently active) BEFORE building its
        # sheet, not after. Building it after meant constructing a full
        # CharacterSheet with the wrong colors active, immediately
        # discarding it, and building a second one correctly once the
        # right theme was applied -- besides being wasteful, that first,
        # thrown-away construction still runs every bit of _load()'s own
        # logic (LevelUpPanel/ChoiceWidget construction, death-screen
        # state check, etc), which is a very plausible source of a
        # stray dialog flashing and immediately closing again when that
        # first sheet gets torn down moments later.
        saved_theme = char.get("theme")
        if saved_theme in THEMES:
            if (saved_theme != self._current_theme_name
                    and not getattr(self, "_switching_theme", False)):
                qss = theme.apply_theme(saved_theme)
                self.setStyleSheet(qss)
                # Same QApplication-level QToolTip fix as _set_theme() --
                # a per-widget setStyleSheet() doesn't reliably theme
                # tooltips shown by unrelated descendants.
                app = QApplication.instance()
                if app is not None:
                    app.setStyleSheet(qss)
                self._current_theme_name = saved_theme
        else:
            # New characters (and old saves from before "theme" existed)
            # have no theme of their own recorded yet -- stamp the
            # currently-active one so this character remembers it from
            # here on, not only after an explicit Settings change.
            char["theme"] = self._current_theme_name
        self._stack.setUpdatesEnabled(False)
        try:
            if self._sheet:
                self._stack.removeWidget(self._sheet); self._sheet.deleteLater()
            # Explicit parent (self, not the default None) matters here:
            # CharacterSheet.__init__ runs a lot of work -- every tab's
            # _build_tab_* -- before this line's addWidget() reparents it
            # into self._stack a moment later. A parentless QWidget is a
            # genuine independent top-level window as far as Qt/the OS
            # window manager is concerned for that whole window, full
            # min/max/close chrome included, even though nothing here
            # ever calls .show() on it -- an unparented sheet would flash
            # open and shut as a real window during construction.
            # StartMenu()/CharacterWizard() construction sites need the
            # same explicit parent, for the same reason.
            self._sheet = CharacterSheet(char, self)
            self._sheet.back_to_menu.connect(self._sheet_back_to_menu)
            self._stack.addWidget(self._sheet)
            self._stack.setCurrentWidget(self._sheet)
        except Exception:
            # Safety net: surface the real failure to the player and log
            # it, instead of letting sheet construction fail silently.
            import traceback
            from dnd_app.ui.shared import write_diagnostic_log
            tb = traceback.format_exc()
            log_path = write_diagnostic_log("mimic_crash_log.txt", tb)
            dlg = QMessageBox(self)
            dlg.setIcon(QMessageBox.Critical)
            dlg.setWindowTitle("Character Sheet Failed to Build")
            dlg.setText("Something went wrong building the character sheet. The details below "
                        + (f"(also saved to {log_path}) " if log_path else "")
                        + "will help fix this.")
            dlg.setDetailedText(tb)
            dlg.exec()
            return
        finally:
            self._stack.setUpdatesEnabled(True)

    def _sheet_back_to_menu(self):
        if self._sheet and not self._sheet.confirm_leave():
            return
        self._go_menu()

    def _go_menu(self):
        self._stack.removeWidget(self._start); self._start.deleteLater()
        self._start = StartMenu(self)
        self._start.new_char.connect(self._go_wizard)
        self._start.load_char.connect(self._go_sheet_from_path)
        self._stack.insertWidget(0, self._start)
        self._stack.setCurrentIndex(0)

    def _load_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Character",
                      os.path.expanduser("~/.dnd_characters"), "JSON files (*.json)")
        if path: self._go_sheet_from_path(path)

    def _save(self):
        if self._sheet:
            self._sheet._collect()
            self._sheet._save()

    def _export_dialog(self):
        if self._sheet: self._sheet._export_dialog()

    def _short_rest(self):
        if self._sheet: self._sheet._short_rest()

    def _long_rest(self):
        if self._sheet: self._sheet._long_rest()

    def _rebuild_recent_menu(self):
        self._recent_menu.clear()
        from dnd_app.ui.pages.main_window import _load_recent
        recent = _load_recent()
        if not recent:
            a = self._recent_menu.addAction("(no recent characters)"); a.setEnabled(False)
        else:
            for path in recent:
                name = os.path.splitext(os.path.basename(path))[0].replace("_"," ").title()
                act = self._recent_menu.addAction(f"\U0001f4c4  {name}")
                act.triggered.connect(lambda checked=False, p=path: self._go_sheet_from_path(p))
            self._recent_menu.addSeparator()
            self._recent_menu.addAction("Clear Recent").triggered.connect(self._clear_recent)

    def _clear_recent(self):
        try:
            import json
            open(_RECENT_FILE,"w").write("[]")
        except Exception: pass
        self._rebuild_recent_menu()

    def _duplicate_character(self):
        if not self._sheet: return
        import copy, time
        from dnd_app.core.save_load import save_character, character_filename
        from dnd_app.ui.pages.main_window import _save_recent
        dup = copy.deepcopy(self._sheet.char)
        dup["name"] = dup.get("name","Character") + " (Copy)"
        dup["_id"] = f"char_{int(time.time())}"
        self._show_sheet(dup)
        path = character_filename(dup)
        save_character(dup, path)
        _save_recent(path)
        if hasattr(self,"_recent_menu"): self._rebuild_recent_menu()
        self.statusBar().showMessage(f"Duplicated → {dup['name']}", 3000)

    def _open_dice_roller(self):
        from dnd_app.ui.dialogs.dice_roller import DiceRollerPanel
        char = self._sheet.char if self._sheet else new_character()
        if self._dice_roller:
            self._dice_roller.char = char
            # "Roll with Bonus" caches skill/save/ability bonuses at
            # construction time and never refreshed them again -- a
            # level-up or ability score change while the roller sat open
            # (or just in the background) left it showing stale numbers
            # until the whole panel was recreated. Re-deriving them here,
            # every time the roller is (re)opened or brought to front,
            # covers that without needing a live subscription that would
            # also have to survive the sheet being rebuilt from scratch.
            self._dice_roller.refresh_bonuses()
        if not self._dice_roller:
            self._dice_roller = DiceRollerPanel(char, parent=self)
        if self._dice_roller.isHidden():
            geo = self.geometry()
            self._dice_roller.move(geo.right()-400, geo.top()+80)
            self._dice_roller.show()
        else:
            self._dice_roller.raise_(); self._dice_roller.activateWindow()


def main(app=None, splash=None):
    """If app/splash aren't provided (e.g. main_window is imported and run
    directly rather than through run_dnd_creator.py's fast-splash launch
    sequence), fall back to creating them here — just later than ideal,
    since importing this module has already pulled in every heavy
    transitive dependency (wizard, sheet, all game data) by this point."""
    owns_app = app is None
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("MIMIC")

    if splash is None:
        # Show a splash immediately — building the sheet (magic items, spells,
        # every tab widget) takes a couple of seconds on some machines, and an
        # empty frame during that time reads as a frozen/crashed app. Drop
        # dnd_app/ui/splash/splash.gif (or splash.png) in to use a custom splash.
        from dnd_app.ui.splash import AnimatedSplash
        splash = AnimatedSplash()
        splash.show()
        app.processEvents()

    win = CharacterCreatorApp()   # build eagerly; window itself stays hidden

    def _reveal():
        win.show()
        splash.finish_and_close(win)

    if splash.loop_complete:
        # Either there's no gif to wait on, or building the window already
        # took at least one full animation cycle — show immediately.
        _reveal()
    else:
        # The window was ready before the splash finished its first loop;
        # hold it back so the animation is never cut off mid-cycle.
        splash.loop_finished.connect(_reveal)

    sys.exit(app.exec())
