"""
Character Creation Wizard module.

PySide6 multi-step wizard that builds a new character from scratch:
  1. Race
  2. Ability Scores
  3. Background + Class (with scrollable level timeline + subclass + choices)
  4. Spells  (only if caster)
  5. Equipment
Each step collects its choices into the character dict and calls
dnd_app.core.builder.rebuild() before advancing, so later steps (e.g.
starting spells, which depend on class) always see up-to-date state.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QFont
from .theme import *
from .shared import *
from dnd_app.core.character import new_character, add_class, ability_score, ability_mod, get_class_entry, set_subclass
from dnd_app.core.builder import rebuild, get_choices_needed, apply_choice
from dnd_app.core.multiclass import check_multiclass_prereq
from dnd_app.data.races import ALL_RACES, RACE_NAMES, RACE_DICT, get_race
from dnd_app.data.classes import CLASS_DICT, CLASS_NAMES, BATTLE_MASTER_MANEUVERS, WILD_MAGIC_SURGE_TABLE
from dnd_app.data.backgrounds import ALL_BACKGROUNDS, BACKGROUND_NAMES, get_background
from dnd_app.data.feats import ALL_FEATS
from dnd_app.data.spells import ALL_SPELLS, spells_for_class, get_spell
from dnd_app.data.items import ARMOR, ALL_WEAPONS, ADVENTURING_GEAR, SIMPLE_MELEE, SIMPLE_RANGED, MARTIAL_MELEE, MARTIAL_RANGED

ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]
AB_FULL = {"STR":"Strength","DEX":"Dexterity","CON":"Constitution",
           "INT":"Intelligence","WIS":"Wisdom","CHA":"Charisma"}

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
POINT_BUY_COSTS = {8:0,9:1,10:2,11:3,12:4,13:5,14:7,15:9}

# Spell-granting races
def _lbl(text, color=TEXT, size=FS_BODY, bold=False, wrap=True, align=Qt.AlignLeft):
    w = QLabel(text); w.setWordWrap(wrap); w.setAlignment(align)
    s = f"color:{color};font-size:{size}px;background:transparent;"
    if bold: s += "font-weight:700;"
    w.setStyleSheet(s); return w


# ═══════════════════════════════════════════════════════════════════
#  WIZARD MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════
class CharacterWizard(QWidget):
    """Drives the creation flow; emits 'done' with finished char dict."""
    done = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        from dnd_app.ui.theme import sync_globals as _sg; _sg(globals())
        self.char = new_character()
        self._step = 0
        self._steps = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # ── Top header bar ────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{SURF};border-bottom:2px solid {BORDER};}}")
        header.setFixedHeight(64)
        hl = QHBoxLayout(header); hl.setContentsMargins(24,0,24,0)
        hl.addWidget(_lbl("⚔", GOLD2, 28, bold=True, wrap=False))
        hl.addWidget(_lbl("New Character", TEXT, FS_TITLE, bold=True, wrap=False))
        hl.addStretch()
        # Step indicator pills
        self._step_pills = []
        step_names = ["Race","Abilities","Class","Equipment"]
        for i, name in enumerate(step_names):
            pill = _lbl(f" {i+1}. {name} ", TEXT3, FS_SMALL, wrap=False, align=Qt.AlignCenter)
            pill.setFixedHeight(30)
            pill.setStyleSheet(f"background:{SURF3};color:{TEXT3};border-radius:15px;font-size:{FS_SMALL}px;padding:0 12px;")
            hl.addWidget(pill); hl.addSpacing(4)
            self._step_pills.append(pill)
        root.addWidget(header)

        # ── Page stack ────────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{BG};")
        self._step1 = Step1Race(self.char)
        self._step2 = Step2Abilities(self.char)
        self._step3 = Step3Class(self.char)
        self._step4 = Step4Spells(self.char)
        self._step5 = Step5Equipment(self.char)
        for s in [self._step1, self._step2, self._step3, self._step4, self._step5]:
            self._stack.addWidget(s)
        root.addWidget(self._stack, 1)

        # ── Bottom nav bar ─────────────────────────────────────────────────────
        nav = QFrame()
        nav.setStyleSheet(f"QFrame{{background:{SURF};border-top:2px solid {BORDER};}}")
        nav.setFixedHeight(72)
        nl = QHBoxLayout(nav); nl.setContentsMargins(24,0,24,0)
        self._back_btn = pill_btn("← Back", SURF2, TEXT)
        self._back_btn.setFixedWidth(130)
        self._back_btn.setVisible(False)
        self._back_btn.clicked.connect(self._prev_step)
        self._next_btn = pill_btn("Next →", INDIGO)
        self._next_btn.setMinimumWidth(160)   # min not fixed — "Create Character ✓" needs more
        self._next_btn.clicked.connect(self._next_step)
        nl.addWidget(self._back_btn); nl.addStretch(); nl.addWidget(self._next_btn)
        root.addWidget(nav)

        self._update_pills()

    def _update_pills(self):
        for i, pill in enumerate(self._step_pills):
            if i == self._step:
                pill.setStyleSheet(f"background:{INDIGO};color:white;border-radius:15px;font-size:{FS_SMALL}px;font-weight:700;padding:0 12px;")
            elif i < self._step:
                pill.setStyleSheet(f"background:{qa(TEAL,0x55)};color:{TEAL2};border-radius:15px;font-size:{FS_SMALL}px;padding:0 12px;")
            else:
                pill.setStyleSheet(f"background:{SURF3};color:{TEXT3};border-radius:15px;font-size:{FS_SMALL}px;padding:0 12px;")
        self._back_btn.setVisible(self._step > 0)
        # Last step label changes to "Create Character" — the stylesheet
        # is built fresh each time rather than string-replacing whatever
        # was already set, so :hover and other states stay consistent
        # regardless of which stylesheet was previously applied.
        if self._step == 4:  # Equipment (step 3 skipped, so 4 is last)
            self._next_btn.setText("Create Character ✓")
            self._next_btn.setStyleSheet(pill_btn("", TEAL, hover=TEAL2).styleSheet())
        else:
            self._next_btn.setText("Next →")
            self._next_btn.setStyleSheet(pill_btn("", INDIGO).styleSheet())

    def _next_step(self):
        steps = [self._step1, self._step2, self._step3, self._step4, self._step5]
        if not steps[self._step].collect(self.char):
            return
        try:
            rebuild(self.char)
            if self._step == 4:          # Equipment = last real step
                self.done.emit(self.char)
                return
        except Exception:
            # Diagnostic safety net: surface the real failure instead of
            # letting it fail silently — needed to actually diagnose the
            # reported "button does nothing" issue without a live PySide6
            # install to test against.
            import traceback, os
            tb = traceback.format_exc()
            try:
                with open(os.path.join(os.path.expanduser("~"), "mimic_crash_log.txt"), "w") as f:
                    f.write(tb)
            except Exception:
                pass
            dlg = QMessageBox(self)
            dlg.setIcon(QMessageBox.Critical)
            dlg.setWindowTitle("Character Build Failed")
            dlg.setText("Something went wrong finalizing your character. The details below "
                        "(also saved to mimic_crash_log.txt in your home folder) will help fix this.")
            dlg.setDetailedText(tb)
            dlg.exec()
            return
        self._step += 1
        if self._step == 3:          # ALWAYS skip Spells step
            self._step += 1
        steps[self._step].populate(self.char)
        self._stack.setCurrentIndex(self._step)
        self._update_pills()

    def _prev_step(self):
        self._step -= 1
        if self._step == 3:          # ALWAYS skip Spells going back too
            self._step -= 1
        steps = [self._step1, self._step2, self._step3, self._step4, self._step5]
        steps[self._step].populate(self.char)
        self._stack.setCurrentIndex(self._step)
        self._update_pills()


# ═══════════════════════════════════════════════════════════════════
#  STEP 1: RACE
# ═══════════════════════════════════════════════════════════════════
class Step1Race(QWidget):
    def __init__(self, char, parent=None):
        super().__init__(parent)
        from dnd_app.ui.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        root = QHBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(20)

        # Left: race grid
        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(12)
        ll.addWidget(_lbl("Choose Your Race", GOLD2, FS_HEAD, bold=True))
        ll.addWidget(_lbl("Your race grants ability score bonuses, traits, and proficiencies.", TEXT2, FS_BODY))

        search = QLineEdit(); search.setPlaceholderText("Search races…")
        ll.addWidget(search)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        self._grid = QGridLayout(inner); self._grid.setSpacing(8)
        scroll.setWidget(inner); ll.addWidget(scroll, 1)
        root.addWidget(left, 3)

        # Right: detail panel
        right = QWidget(); rl = QVBoxLayout(right); rl.setSpacing(10)
        rl.addWidget(_lbl("Race Details", GOLD2, FS_HEAD, bold=True))
        self._detail_card = QFrame()
        self._detail_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
        dcl = QVBoxLayout(self._detail_card); dcl.setContentsMargins(16,14,16,14)
        self._detail_name  = _lbl("Select a race to see details", TEXT2, FS_BODY)
        self._detail_asi   = _lbl("", TEAL2, FS_BODY, bold=True)
        self._detail_speed = _lbl("", TEXT2, FS_SMALL)
        self._detail_size  = _lbl("", TEXT2, FS_SMALL)
        self._detail_traits = QTextEdit(); self._detail_traits.setReadOnly(True)
        self._detail_traits.setMaximumHeight(200)
        self._detail_traits.setStyleSheet(f"background:{SURF2};border:1px solid {BORDER};border-radius:6px;font-size:{FS_BODY}px;color:{TEXT};")
        dcl.addWidget(self._detail_name); dcl.addWidget(self._detail_asi)
        dcl.addWidget(self._detail_speed); dcl.addWidget(self._detail_size)
        dcl.addWidget(self._detail_traits)

        # Subrace
        sub_row = QHBoxLayout()
        sub_row.addWidget(_lbl("Subrace:", TEXT2, FS_BODY, bold=True))
        self._subrace_combo = QComboBox(); self._subrace_combo.addItem("(None)")
        self._subrace_combo.setMinimumWidth(240)
        sub_row.addWidget(self._subrace_combo, 1)
        dcl.addLayout(sub_row)

        # Draconic Ancestry — shown only for Dragonborn
        self._anc_row = QHBoxLayout()
        self._anc_row.addWidget(_lbl("Draconic Ancestry:", TEXT2, FS_BODY, bold=True))
        self._ancestry_combo = QComboBox()
        self._ancestry_combo.setMinimumWidth(240)
        self._anc_row.addWidget(self._ancestry_combo, 1)
        self._anc_widget = QWidget(); self._anc_widget.setLayout(self._anc_row)
        self._anc_widget.setVisible(False)
        dcl.addWidget(self._anc_widget)

        # Eladrin Season — shown only for the Eladrin (Elf) subrace. Each
        # season changes what Fey Step does when you teleport (Autumn
        # charms, Winter frightens, Spring lets a willing creature come
        # with you, Summer burns everyone at your origin point).
        self._season_row = QHBoxLayout()
        self._season_row.addWidget(_lbl("Eladrin Season:", TEXT2, FS_BODY, bold=True))
        self._season_combo = QComboBox()
        self._season_combo.setMinimumWidth(340)
        for season, effect in [
            ("Autumn", "charm one creature within 5 ft of your destination"),
            ("Winter", "frighten one creature within 5 ft of your destination"),
            ("Spring", "a willing creature within 5 ft can teleport with you"),
            ("Summer", "2d6 fire damage to each creature within 5 ft of your origin"),
        ]:
            self._season_combo.addItem(f"{season}  –  {effect}", season)
        self._season_row.addWidget(self._season_combo, 1)
        self._season_widget = QWidget(); self._season_widget.setLayout(self._season_row)
        self._season_widget.setVisible(False)
        dcl.addWidget(self._season_widget)

        # Simic Hybrid's 1st-level Animal Enhancement — shown only for
        # that race. The 5th-level "Additional Animal Enhancement" choice
        # is granted later, not at character creation, so it isn't picked
        # here (same reasoning as feats/ASIs gained on level-up).
        self._simic_row = QHBoxLayout()
        self._simic_row.addWidget(_lbl("Animal Enhancement:", TEXT2, FS_BODY, bold=True))
        self._simic_combo = QComboBox()
        self._simic_combo.setMinimumWidth(340)
        for opt, desc in [
            ("Manta Glide", "slow falls: subtract 100 ft from fall damage, glide 2 ft horizontal per 1 ft descended"),
            ("Nimble Climber", "climbing speed = walking speed"),
            ("Underwater Adaptation", "breathe air and water, swim speed = walking speed"),
        ]:
            self._simic_combo.addItem(f"{opt}  –  {desc}", opt)
        self._simic_row.addWidget(self._simic_combo, 1)
        self._simic_widget = QWidget(); self._simic_widget.setLayout(self._simic_row)
        self._simic_widget.setVisible(False)
        dcl.addWidget(self._simic_widget)

        rl.addWidget(self._detail_card, 1); rl.addStretch()
        root.addWidget(right, 2)

        self._selected_race = None
        self._race_btns = {}

        # Populate grid
        for i, name in enumerate(RACE_NAMES):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setMinimumHeight(44)
            btn.setStyleSheet(
                f"QPushButton{{background:{SURF2};border:2px solid {BORDER};border-radius:8px;"
                f"color:{TEXT};font-size:{FS_BODY}px;text-align:left;padding:6px 12px;}}"
                f"QPushButton:checked{{background:{qa(INDIGO,0x22)};border-color:{INDIGO};color:{IND2};}}"
                f"QPushButton:hover{{background:{SURF3};border-color:{BORDER2};}}"
            )
            btn.clicked.connect(lambda checked, n=name: self._select_race(n))
            self._grid.addWidget(btn, i//2, i%2)
            self._race_btns[name] = btn

        def _filter(text):
            for name, btn in self._race_btns.items():
                btn.setVisible(not text or text.lower() in name.lower())
        search.textChanged.connect(_filter)

    @staticmethod
    def _flex_asi_desc(flex: int, style: str) -> str:
        """Correctly describe a race's flexible ASI grant by its real
        mechanic, replacing the old universally-wrong '+1 to N abilities'
        wording that misrepresented the 2024/MPMM distribute-style rule."""
        if style == "each" or flex == 1:
            noun = "ability" if flex == 1 else "abilities"
            return f"+1 to {flex} {noun} of your choice"
        return "+2 to one ability and +1 to a different ability, OR +1 to three different abilities (your choice)"

    def _select_race(self, name):
        self._selected_race = name
        for n, btn in self._race_btns.items():
            btn.setChecked(n == name)

        rdata = RACE_DICT.get(name, {})
        self._detail_name.setText(name)
        self._detail_name.setStyleSheet(f"color:{GOLD2};font-size:{FS_TITLE}px;font-weight:700;background:transparent;")

        # ASI display
        asi = rdata.get("asi", {})
        flex = rdata.get("asi_flex", 0)
        style = rdata.get("asi_flex_style", "distribute")
        asi_parts = [f"{ab} +{v}" for ab, v in asi.items()]
        if flex:
            asi_parts.append(self._flex_asi_desc(flex, style))
            self._detail_asi.setText("ASI: " + (", ".join(asi_parts) if asi_parts else "None"))

        self._detail_speed.setText(f"Speed: {rdata.get('speed',30)} ft   Size: {rdata.get('size','Medium')}")
        self._detail_size.setText(f"Source: {rdata.get('source','PHB')}")

        traits = rdata.get("traits", [])
        self._base_race_traits = traits  # cached so _update_subrace_detail can rebuild without re-fetching rdata
        self._detail_traits.setPlainText("\n\n".join(f"• {t}" for t in traits))

        # Subraces
        self._subrace_combo.clear()
        self._subrace_combo.addItem("(None)")
        for sub in rdata.get("subraces", []):
            display_name = sub.split("(")[0].strip()
            full_desc = sub[sub.find("("):]  # the parenthetical bit
            self._subrace_combo.addItem(f"{display_name}  {full_desc}", display_name)

        # Draconic ancestry for Dragonborn
        is_dragonborn = (name == "Dragonborn")
        if hasattr(self, "_anc_widget"):
            self._anc_widget.setVisible(is_dragonborn)
            if is_dragonborn:
                from dnd_app.data.races import DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE
                self._ancestry_combo.clear()
                # Default to Standard types (all 10)
                for anc in ANCESTRY_BY_SUBRACE.get("Standard", []):
                    dmg = DRACONIC_ANCESTRY[anc][0]
                    shape = DRACONIC_ANCESTRY[anc][1]
                    self._ancestry_combo.addItem(f"{anc}  –  {dmg}, {shape}", anc)

        # Simic Hybrid's 1st-level Animal Enhancement picker
        if hasattr(self, "_simic_widget"):
            self._simic_widget.setVisible(name == "Simic Hybrid")

        # Single handler for subrace changes — updates the Dragonborn
        # ancestry list AND refreshes the ASI/traits detail panel to show
        # the chosen subrace's own bonuses, not just the base race's.
        def _on_subrace_changed(idx):
            if is_dragonborn and hasattr(self, "_anc_widget"):
                from dnd_app.data.races import DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE
                sub_name = self._subrace_combo.currentData() or "Standard"
                types = ANCESTRY_BY_SUBRACE.get(sub_name, ANCESTRY_BY_SUBRACE["Standard"])
                self._ancestry_combo.clear()
                for anc in types:
                    dmg = DRACONIC_ANCESTRY[anc][0]
                    shape = DRACONIC_ANCESTRY[anc][1]
                    self._ancestry_combo.addItem(f"{anc}  –  {dmg}, {shape}", anc)
            self._update_subrace_detail()
        try:
            self._subrace_combo.currentIndexChanged.disconnect()
        except (TypeError, RuntimeError):
            pass
        self._subrace_combo.currentIndexChanged.connect(_on_subrace_changed)

        # Also show ASI summary for the race in Step1 panel
        if rdata.get("subraces") and not asi_parts:
            self._detail_asi.setText("ASI: from subrace — see below")
        self._update_subrace_detail()  # reflect "(None)" state right away

    def _update_subrace_detail(self):
        """Refresh the ASI/traits detail panel for whichever subrace is
        currently selected. Without this, the panel only ever showed the
        base race's own info — picking "Hill" vs "Mountain" Dwarf, for
        example, never changed what was displayed, even though each
        subrace has its own ASI and adds its own traits (Dwarven
        Toughness, Duergar Magic, etc.) on top of the base race's."""
        if not hasattr(self, "_detail_traits"):
            return
        rdata = RACE_DICT.get(self._selected_race, {})
        base_traits = getattr(self, "_base_race_traits", rdata.get("traits", []))
        sub_data = self._subrace_combo.currentData()

        # Eladrin Season picker — only relevant when the Eladrin subrace of
        # Elf is actually selected. This visibility toggle was the missing
        # piece keeping the whole widget permanently hidden/dead: it was
        # fully built (all 4 seasons with their Fey Step effects) but
        # nothing ever showed it or read a choice out of it.
        if hasattr(self, "_season_widget"):
            self._season_widget.setVisible(sub_data == "Eladrin")

        if not sub_data:
            self._detail_traits.setPlainText("\n\n".join(f"• {t}" for t in base_traits))
            asi = rdata.get("asi", {})
            flex = rdata.get("asi_flex", 0)
            style = rdata.get("asi_flex_style", "distribute")
            asi_parts = [f"{ab} +{v}" for ab, v in asi.items()]
            if flex:
                asi_parts.append(self._flex_asi_desc(flex, style))
            if asi_parts:
                self._detail_asi.setText("ASI: " + ", ".join(asi_parts))
            elif rdata.get("subraces"):
                self._detail_asi.setText("ASI: from subrace — see below")
            else:
                self._detail_asi.setText("ASI: None")
            return

        sub_full = next((s for s in rdata.get("subraces", [])
                          if s.split("(")[0].strip() == sub_data), None)
        if not sub_full:
            return
        paren = sub_full[sub_full.find("(")+1 : sub_full.rfind(")")]
        segments = [s.strip() for s in paren.split(";") if s.strip()]
        asi_desc = segments[0].lstrip("–").strip() if segments else ""
        sub_traits = segments[1:]

        if asi_desc:
            self._detail_asi.setText(f"ASI: {asi_desc}  (from {sub_data})")
        combined = list(base_traits) + [f"[{sub_data}] {t}" for t in sub_traits]
        self._detail_traits.setPlainText("\n\n".join(f"• {t}" for t in combined))

    def populate(self, char):
        race = char.get("race","")
        if race and race in self._race_btns:
            self._select_race(race)

    def collect(self, char) -> bool:
        if not self._selected_race:
            QMessageBox.warning(self, "Race Required", "Please choose a race before continuing.")
            return False
        char["race"] = self._selected_race
        char["species"] = self._selected_race
        sub_data = self._subrace_combo.currentData()  # stored as name only
        sub_text = self._subrace_combo.currentText()
        if sub_data:
            char["subrace"] = sub_data  # clean name like "Hill"
        elif sub_text and sub_text != "(None)":
            char["subrace"] = sub_text.split("(")[0].strip().rstrip()
        else:
            char["subrace"] = ""
        # Save draconic ancestry for Dragonborn
        if hasattr(self, "_ancestry_combo") and self._anc_widget.isVisible():
            anc = self._ancestry_combo.currentData() or self._ancestry_combo.currentText().split("–")[0].strip()
            char["draconic_ancestry"] = anc
        elif "draconic_ancestry" not in char:
            char["draconic_ancestry"] = ""
        # Save Eladrin season — this widget existed and was fully built out
        # (all 4 seasons with their Fey Step rider effects) but was never
        # actually wired to anything: it never became visible, and nothing
        # ever read a choice out of it, so the season was silently lost.
        if hasattr(self, "_season_widget") and self._season_widget.isVisible():
            season = self._season_combo.currentData() or self._season_combo.currentText().split("–")[0].strip()
            char["eladrin_season"] = season
        elif "eladrin_season" not in char:
            char["eladrin_season"] = ""
        # Save Simic Hybrid's 1st-level Animal Enhancement choice
        if hasattr(self, "_simic_widget") and self._simic_widget.isVisible():
            enh = self._simic_combo.currentData() or self._simic_combo.currentText().split("–")[0].strip()
            char["simic_enhancement_1st"] = enh
        elif "simic_enhancement_1st" not in char:
            char["simic_enhancement_1st"] = ""
        # Apply race traits
        rdata = RACE_DICT.get(self._selected_race, {})
        char["species_traits"] = rdata.get("traits", [])
        char.setdefault("languages", ["Common"])
        for lang in rdata.get("languages", []):
            if lang not in char["languages"] and "your choice" not in lang.lower():
                char["languages"].append(lang)
        return True


# ═══════════════════════════════════════════════════════════════════
#  STEP 2: ABILITY SCORES
# ═══════════════════════════════════════════════════════════════════
class Step2Abilities(QWidget):
    def __init__(self, char, parent=None):
        super().__init__(parent)
        from dnd_app.ui.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        root = QVBoxLayout(self); root.setContentsMargins(40,24,40,24); root.setSpacing(16)
        root.addWidget(_lbl("Ability Scores", GOLD2, FS_HEAD, bold=True))
        root.addWidget(_lbl("Set your base ability scores, then apply racial and ASI bonuses below.", TEXT2, FS_BODY))

        # Method selector
        method_row = QHBoxLayout(); method_row.setSpacing(12)
        method_row.addWidget(_lbl("Method:", TEXT, FS_BODY, bold=True))
        self._method = QComboBox()
        self._method.addItems([
            "Manual Entry",
            "Standard Array (15,14,13,12,10,8)",
            "Point Buy (27 points)",
            "Tasha's: Reassign Racial ASIs (keeps all racial traits)",
        ])
        self._method.setFixedWidth(380)
        self._method.currentTextChanged.connect(self._on_method_change)
        method_row.addWidget(self._method); method_row.addStretch()
        root.addLayout(method_row)

        # Ability blocks
        ab_frame = QFrame(); ab_frame.setStyleSheet(f"background:{SURF};border:1px solid {BORDER};border-radius:10px;")
        ab_lay = QHBoxLayout(ab_frame); ab_lay.setContentsMargins(20,16,20,16); ab_lay.setSpacing(10)
        self._ab_blocks = {}
        for ab in ABILITIES:
            blk = AbilityBlock(ab, 10, editable=True)
            blk.changed.connect(self._on_score_change)
            ab_lay.addWidget(blk)
            self._ab_blocks[ab] = blk
        root.addWidget(ab_frame)

        # Point buy tracker
        self._pb_lbl = _lbl("Points remaining: 27 / 27", GOLD2, FS_BODY, bold=True)
        self._pb_lbl.setVisible(False)
        root.addWidget(self._pb_lbl)

        # Racial bonus preview
        self._race_bonus_card = QFrame()
        self._race_bonus_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(TEAL,0x55)};border-radius:10px;}}")
        rbl = QVBoxLayout(self._race_bonus_card); rbl.setContentsMargins(16,12,16,12)
        rbl.addWidget(_lbl("Racial Ability Score Increases", TEAL2, FS_BODY, bold=True))
        self._race_bonus_lbl = _lbl("", TEXT2, FS_BODY)
        rbl.addWidget(self._race_bonus_lbl)
        root.addWidget(self._race_bonus_card)

        # Totals row
        totals_card = QFrame(); totals_card.setStyleSheet(f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:10px;}}")
        tl = QHBoxLayout(totals_card); tl.setContentsMargins(20,12,20,12); tl.setSpacing(8)
        tl.addWidget(_lbl("TOTAL SCORES WITH RACIAL BONUSES:", TEXT2, FS_SMALL, bold=True)); tl.addStretch()
        self._total_lbls = {}
        for ab in ABILITIES:
            col = QVBoxLayout(); col.setSpacing(2)
            col.addWidget(_lbl(ab, TEXT3, FS_SMALL, bold=True, align=Qt.AlignCenter))
            lbl = _lbl("10", TEXT, FS_TITLE, bold=True, align=Qt.AlignCenter)
            col.addWidget(lbl); tl.addLayout(col)
            self._total_lbls[ab] = lbl
        root.addWidget(totals_card)

        # ── Flex ASI picker (Half-Elf, Human Variant etc.) ────────────────────
        self._flex_card = QFrame()
        self._flex_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(PURP2,0x55)};border-radius:10px;}}")
        fcl = QVBoxLayout(self._flex_card); fcl.setContentsMargins(16,12,16,12); fcl.setSpacing(8)
        self._flex_lbl = _lbl("Choose 2 abilities to receive +1:", PURP2, FS_BODY, bold=True)
        fcl.addWidget(self._flex_lbl)
        flex_row = QHBoxLayout(); flex_row.setSpacing(10)
        self._flex_cbs = {}
        for ab in ABILITIES:
            cb = QCheckBox(ab)
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;}}")
            cb.stateChanged.connect(self._on_flex_changed)
            flex_row.addWidget(cb)
            self._flex_cbs[ab] = cb
        flex_row.addStretch()
        fcl.addLayout(flex_row)
        self._flex_count = 0
        self._flex_card.setVisible(False)
        root.addWidget(self._flex_card)

        # ── Distribute ASI picker (2024/MPMM style: +2/+1 split OR three +1s) ──
        # The checkbox-only picker above can only represent "choose N
        # different abilities, each gets a flat +1" (the older,
        # Half-Elf-style rule). For 2024/MPMM-style races — asi_flex=2,
        # the majority of races in this app — the player needs to pick
        # between a "+2/+1 split" or "three different +1s" distribution,
        # which this picker provides.
        self._dist_card = QFrame()
        self._dist_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(PURP2,0x55)};border-radius:10px;}}")
        self._dist_card.setMinimumHeight(190)
        self._dist_card.setMinimumWidth(420)
        dcl = QVBoxLayout(self._dist_card); dcl.setContentsMargins(16,12,16,12); dcl.setSpacing(8)
        dcl.addWidget(_lbl("Ability Score Increase — choose one option:", PURP2, FS_BODY, bold=True))

        self._dist_group = QButtonGroup(self._dist_card)
        self._dist_radio_a = QRadioButton("(a) +2 to one ability, +1 to a different ability")
        self._dist_radio_b = QRadioButton("(b) +1 to three different abilities")
        for rb in (self._dist_radio_a, self._dist_radio_b):
            rb.setStyleSheet(f"QRadioButton{{color:{TEXT};font-size:{FS_BODY}px;}}")
            self._dist_group.addButton(rb)
        self._dist_radio_a.setChecked(True)
        dcl.addWidget(self._dist_radio_a)

        # Option (a) sub-picker: two dropdowns, must be different abilities
        dist_a_row = QHBoxLayout(); dist_a_row.setSpacing(10)
        dist_a_row.addWidget(_lbl("+2:", TEXT2, FS_SMALL))
        self._dist_plus2_combo = QComboBox()
        self._dist_plus2_combo.addItems(ABILITIES)
        self._dist_plus2_combo.setMinimumWidth(90)
        dist_a_row.addWidget(self._dist_plus2_combo)
        dist_a_row.addWidget(_lbl("+1:", TEXT2, FS_SMALL))
        self._dist_plus1_combo = QComboBox()
        self._dist_plus1_combo.addItems(ABILITIES)
        self._dist_plus1_combo.setMinimumWidth(90)
        self._dist_plus1_combo.setCurrentIndex(1)
        dist_a_row.addWidget(self._dist_plus1_combo)
        dist_a_row.addStretch()
        self._dist_a_widget = QWidget(); self._dist_a_widget.setLayout(dist_a_row)
        dcl.addWidget(self._dist_a_widget)

        dcl.addWidget(self._dist_radio_b)

        # Option (b) sub-picker: exactly 3 checkboxes, each a flat +1
        dist_b_row = QHBoxLayout(); dist_b_row.setSpacing(10)
        self._dist_triple_cbs = {}
        for ab in ABILITIES:
            cb = QCheckBox(ab)
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;}}")
            cb.stateChanged.connect(self._on_dist_triple_changed)
            dist_b_row.addWidget(cb)
            self._dist_triple_cbs[ab] = cb
        dist_b_row.addStretch()
        self._dist_b_widget = QWidget(); self._dist_b_widget.setLayout(dist_b_row)
        dcl.addWidget(self._dist_b_widget)

        self._dist_radio_a.toggled.connect(self._on_dist_option_changed)
        self._dist_plus2_combo.currentTextChanged.connect(self._update_totals)
        self._dist_plus1_combo.currentTextChanged.connect(self._update_totals)
        self._on_dist_option_changed()
        self._dist_card.setVisible(False)
        root.addWidget(self._dist_card)

        # ── Tasha's: Reassign Racial ASIs ────────────────────────────────
        self._tashas_card = QFrame()
        self._tashas_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(GOLD,0x55)};border-radius:10px;}}")
        tcl = QVBoxLayout(self._tashas_card); tcl.setContentsMargins(16,12,16,12); tcl.setSpacing(8)
        tcl.addWidget(_lbl("Tasha's Reassignment: redistribute your racial ASI points to any abilities.",
                           GOLD2, FS_BODY, bold=True))
        tcl.addWidget(_lbl(
            "All racial traits, features, languages, speed, darkvision and proficiencies are kept. "
            "Only where the ability score increases land is changed.",
            TEAL2, FS_SMALL))
        self._tashas_summary = _lbl("", TEXT2, FS_SMALL); tcl.addWidget(self._tashas_summary)
        self._tashas_spins_frame = QWidget(); self._tashas_spins_frame.setStyleSheet("background:transparent;")
        tsf = QHBoxLayout(self._tashas_spins_frame); tsf.setSpacing(10)
        self._tashas_spins = {}; self._tashas_mod_lbls = {}
        for ab in ABILITIES:
            col = QVBoxLayout(); col.setSpacing(3)
            col.addWidget(_lbl(ab, TEXT3, FS_SMALL, bold=True, align=Qt.AlignCenter))
            sp = QSpinBox(); sp.setRange(0, 4); sp.setValue(0); sp.setFixedWidth(52)
            sp.setButtonSymbols(QAbstractSpinBox.NoButtons)
            sp.setStyleSheet(f"QSpinBox{{color:{GOLD2};font-weight:700;font-size:{FS_BODY}px;"
                             f"border:2px solid {qa(GOLD,0x55)};border-radius:6px;background:{SURF2};}}")
            sp.valueChanged.connect(self._on_tashas_spin)
            mod_lbl = QLabel("0"); mod_lbl.setAlignment(Qt.AlignCenter)
            mod_lbl.setStyleSheet(f"color:{TEXT3};font-size:{FS_SMALL}px;background:transparent;")
            col.addWidget(sp); col.addWidget(mod_lbl); tsf.addLayout(col)
            self._tashas_spins[ab] = sp; self._tashas_mod_lbls[ab] = mod_lbl
        tsf.addStretch(); tcl.addWidget(self._tashas_spins_frame)
        self._tashas_pts_lbl = _lbl("Points: 0 / 0", TEXT2, FS_SMALL, bold=True)
        tcl.addWidget(self._tashas_pts_lbl)
        self._tashas_card.setVisible(False)
        root.addWidget(self._tashas_card)

        # Standard array assign (hidden unless method = standard)
        self._sa_frame = QFrame(); self._sa_frame.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(GOLD,0x55)};border-radius:10px;}}")
        sal = QVBoxLayout(self._sa_frame); sal.setContentsMargins(16,12,16,12)
        sal.addWidget(_lbl("Assign each value to one ability:", GOLD, FS_BODY, bold=True))
        self._sa_combos = {}
        sa_grid = QGridLayout(); sa_grid.setSpacing(8)
        for i, ab in enumerate(ABILITIES):
            sa_grid.addWidget(_lbl(f"{AB_FULL[ab]}:", TEXT, FS_BODY, bold=True), i, 0)
            combo = QComboBox()
            combo.setMinimumWidth(80)
            for v in STANDARD_ARRAY: combo.addItem(str(v))
            combo.setCurrentIndex(i)
            combo.currentTextChanged.connect(self._update_totals)
            sa_grid.addWidget(combo, i, 1)
            self._sa_combos[ab] = combo
        sal.addLayout(sa_grid)
        self._sa_frame.setVisible(False)
        root.addWidget(self._sa_frame)

        root.addStretch()

    def populate(self, char):
        from dnd_app.core.character import ability_score
        for ab in ABILITIES:
            base = char["abilities"].get(ab, 10)
            self._ab_blocks[ab].set_score(base)
        self._update_race_bonuses(char)
        self._update_flex_asi(char)
        self._update_totals()

    def _get_combined_racial_asi(self, char) -> dict:
        """Return the effective racial ASI dict.
        Subrace strings encode the TOTAL bonus (not an addend), so when a subrace
        is chosen its parsed values replace the base race ASI entirely."""
        import re as _re
        from dnd_app.data.races import RACE_DICT
        race   = char.get("race", "")
        rdata  = RACE_DICT.get(race, {})
        base   = dict(rdata.get("asi", {}))
        subrace = char.get("subrace", "")
        if subrace:
            for sub_str in rdata.get("subraces", []):
                if sub_str.split("(")[0].strip() == subrace:
                    inner = sub_str[sub_str.find("(")+1:sub_str.rfind(")")]
                    sub_asi = {}
                    for ab, n in _re.findall(r"[+]([A-Z]{3})\s+(\d+)", inner):
                        sub_asi[ab] = int(n)
                    if sub_asi:
                        return sub_asi   # subrace encodes the total — replace, not add
                    break
        return base

    def _update_flex_asi(self, char):
        """Show/hide the correct flex ASI picker. Two genuinely different
        mechanics share the asi_flex field: the legacy "each" style
        (Half-Elf: choose N abilities, each flat +1) and the 2024/MPMM
        "distribute" style (choose either a +2/+1 split or three
        different +1s) — confirmed via user report that every
        distribute-style race was previously being shown the each-style
        checkbox picker, which can represent neither valid distribute
        option correctly."""
        from dnd_app.data.races import RACE_DICT
        race = char.get("race", "")
        rdata = RACE_DICT.get(race, {})
        flex = rdata.get("asi_flex", 0)
        style = rdata.get("asi_flex_style", "distribute")
        use_dist = flex == 2 and style == "distribute"
        if hasattr(self, '_flex_card'):
            self._flex_card.setVisible(flex > 0 and not use_dist)
            if flex > 0 and not use_dist:
                self._flex_lbl.setText(f"Choose {flex} abilities to receive +1 (from {race}):")
        if hasattr(self, '_dist_card'):
            self._dist_card.setVisible(use_dist)
            if use_dist:
                self._dist_radio_a.setChecked(True)
                self._on_dist_option_changed()
                for cb in self._dist_triple_cbs.values():
                    cb.blockSignals(True); cb.setChecked(False); cb.blockSignals(False)
        self._flex_count = 0 if use_dist else flex
        # Prime Tasha's card with the correct pool size (race + subrace combined)
        self._current_race_for_tashas = char.get("race", "")
        self._current_subrace_for_tashas = char.get("subrace", "")
        combined_asi = self._get_combined_racial_asi(char)
        pool2 = sum(combined_asi.values())
        if hasattr(self, '_tashas_summary') and self._current_race_for_tashas:
            subrace = char.get("subrace", "")
            orig = ", ".join(f"{ab} +{v}" for ab, v in combined_asi.items()) if combined_asi else "None"
            flex_note = f" + {flex}\u00d7+1 flex (stays free)" if flex > 0 else ""
            self._tashas_summary.setText(
                f"Original fixed ASI: {orig}{flex_note}\n"
                f"Redistribute the {pool2} fixed point{'s' if pool2!=1 else ''} "
                f"below. All other racial traits are unchanged.")
            for sp in self._tashas_spins.values():
                sp.setRange(0, max(1, pool2))
        if hasattr(self, '_on_tashas_spin'):
            self._on_tashas_spin()

    def _on_tashas_spin(self):
        race    = getattr(self, '_current_race_for_tashas', '')
        subrace = getattr(self, '_current_subrace_for_tashas', '')
        combined = self._get_combined_racial_asi({"race": race, "subrace": subrace})
        pool = sum(combined.values()) or 2
        used = sum(sp.value() for sp in self._tashas_spins.values())
        if used > pool:
            for sp in self._tashas_spins.values():
                if sp.value() > 0 and used > pool:
                    excess = used - pool
                    sp.blockSignals(True); sp.setValue(max(0, sp.value()-excess)); sp.blockSignals(False)
                    used = sum(s.value() for s in self._tashas_spins.values()); break
        color = TEAL2 if used == pool else (GOLD2 if used < pool else CRIM2)
        if hasattr(self, '_tashas_pts_lbl'):
            self._tashas_pts_lbl.setText(f"Points used: {used} / {pool}")
            self._tashas_pts_lbl.setStyleSheet(f"color:{color};font-size:{FS_SMALL}px;font-weight:700;background:transparent;")
        for ab, sp in self._tashas_spins.items():
            base = self._ab_blocks[ab].value() if ab in self._ab_blocks else 10
            total = base + sp.value()
            mod = (total - 10) // 2
            sign = '+' if mod >= 0 else ''
            ml = self._tashas_mod_lbls.get(ab)
            if ml:
                ml.setText(f"{total}\n({sign}{mod})")
                ml.setStyleSheet(f"color:{TEAL2 if sp.value()>0 else TEXT3};font-size:{FS_SMALL}px;background:transparent;")

    def _on_flex_changed(self, _state):
        """Enforce max selection for flex ASI checkboxes."""
        max_flex = getattr(self, '_flex_count', 0)
        if max_flex <= 0:
            return
        checked = [ab for ab, cb in self._flex_cbs.items() if cb.isChecked()]
        if len(checked) > max_flex:
            for ab, cb in self._flex_cbs.items():
                if cb.isChecked() and ab not in checked[:max_flex]:
                    cb.blockSignals(True); cb.setChecked(False); cb.blockSignals(False); break
            checked = [ab for ab, cb in self._flex_cbs.items() if cb.isChecked()]
        self._update_totals()

    def _on_dist_option_changed(self):
        """Toggle which sub-picker is active for the distribute-style ASI
        card: option (a)'s two dropdowns, or option (b)'s three
        checkboxes — only one option's picks should count at a time."""
        is_a = self._dist_radio_a.isChecked()
        self._dist_a_widget.setEnabled(is_a)
        self._dist_b_widget.setEnabled(not is_a)
        self._update_totals()

    def _on_dist_triple_changed(self, _state):
        """Enforce exactly 3 selections for option (b) — not 'up to 3'
        like the each-style picker, since the real rule requires three
        different abilities, no fewer."""
        checked = [ab for ab, cb in self._dist_triple_cbs.items() if cb.isChecked()]
        if len(checked) > 3:
            for ab, cb in self._dist_triple_cbs.items():
                if cb.isChecked() and ab not in checked[:3]:
                    cb.blockSignals(True); cb.setChecked(False); cb.blockSignals(False); break
        self._update_totals()

    def _on_method_change(self, text):
        is_sa = "Standard Array" in text
        is_pb = "Point Buy" in text
        is_ta = "Tasha" in text
        self._sa_frame.setVisible(is_sa)
        self._pb_lbl.setVisible(is_pb)
        self._tashas_card.setVisible(is_ta)
        # Hide manual blocks for standard array
        for ab, blk in self._ab_blocks.items():
            blk.setVisible(not is_sa and not is_ta)
        if is_sa:
            for ab, combo in self._sa_combos.items():
                self._ab_blocks[ab].set_score(int(combo.currentText()))
        if is_ta:
            for sp in self._tashas_spins.values():
                sp.blockSignals(True); sp.setValue(0); sp.blockSignals(False)
            self._on_tashas_spin()
        self._update_totals()

    def _on_score_change(self, ab, val):
        self._update_totals()
        if "Point Buy" in self._method.currentText():
            used = sum(POINT_BUY_COSTS.get(self._ab_blocks[a].value(), 0) for a in ABILITIES)
            rem = 27 - used
            self._pb_lbl.setText(f"Points remaining: {rem} / 27")
            color = TEAL2 if rem >= 0 else CRIM2
            self._pb_lbl.setStyleSheet(f"color:{color};font-size:{FS_BODY}px;font-weight:700;background:transparent;")

    def _update_race_bonuses(self, char):
        """Update the racial ASI preview label. Uses _get_combined_racial_asi
        so it never double-counts the base race bonus."""
        race  = char.get("race","")
        rdata = RACE_DICT.get(race, {})
        flex  = rdata.get("asi_flex", 0)
        asi   = self._get_combined_racial_asi(char)
        parts = [f"{ab} +{v}" for ab, v in sorted(asi.items())]
        sub_name = char.get("subrace","")
        if flex:
            parts.append(f"+1 to {flex} abilities of your choice")
        if hasattr(self, "_race_bonus_card"):
            self._race_bonus_card.setVisible(bool(parts) or bool(sub_name))
        if parts:
            self._race_bonus_lbl.setText(", ".join(parts))
        elif sub_name:
            self._race_bonus_lbl.setText(f"Subrace: {sub_name}")
    def _update_totals(self):
        from dnd_app.data.races import RACE_DICT as RD
        if "Standard Array" in self._method.currentText():
            for ab, combo in self._sa_combos.items():
                self._ab_blocks[ab].set_score(int(combo.currentText()))
        bases = {ab: self._ab_blocks[ab].value() for ab in ABILITIES}
        # Racial ASI — use the canonical helper so base+subrace never double-count
        racial_asi = self._get_combined_racial_asi(self.char)
        flex_picks = {ab for ab, cb in self._flex_cbs.items() if cb.isChecked()} if hasattr(self,'_flex_cbs') and self._flex_card.isVisible() else set()
        dist_bonus = {}
        if hasattr(self, '_dist_card') and self._dist_card.isVisible():
            if self._dist_radio_a.isChecked():
                ab2, ab1 = self._dist_plus2_combo.currentText(), self._dist_plus1_combo.currentText()
                if ab2 != ab1:
                    dist_bonus[ab2] = dist_bonus.get(ab2, 0) + 2
                    dist_bonus[ab1] = dist_bonus.get(ab1, 0) + 1
            else:
                for ab, cb in self._dist_triple_cbs.items():
                    if cb.isChecked():
                        dist_bonus[ab] = dist_bonus.get(ab, 0) + 1
        for ab, lbl in self._total_lbls.items():
            racial = racial_asi.get(ab, 0)
            flex_bonus = 1 if ab in flex_picks else 0
            total = bases[ab] + racial + flex_bonus + dist_bonus.get(ab, 0)
            mod = (total - 10) // 2
            sign_mod = f"+{mod}" if mod >= 0 else str(mod)
            lbl.setText(f"{total}  ({sign_mod})")
            changed = (racial + flex_bonus + dist_bonus.get(ab, 0)) > 0
            lbl.setStyleSheet(
                f"color:{TEAL2 if changed else TEXT};"
                f"font-size:{FS_BODY}px;font-weight:700;background:transparent;")

    def collect(self, char) -> bool:
        if "Standard Array" in self._method.currentText():
            vals = [int(c.currentText()) for c in self._sa_combos.values()]
            if sorted(vals) != sorted(STANDARD_ARRAY):
                QMessageBox.warning(self, "Duplicate Values", "Each standard array value must be used exactly once.")
                return False
            for ab, combo in self._sa_combos.items():
                char["abilities"][ab] = int(combo.currentText())
        elif "Point Buy" in self._method.currentText():
            used = sum(POINT_BUY_COSTS.get(self._ab_blocks[ab].value(), 99) for ab in ABILITIES)
            if used > 27:
                QMessageBox.warning(self, "Over Budget", f"You've spent {used} points but only have 27.")
                return False
            for ab in ABILITIES:
                char["abilities"][ab] = self._ab_blocks[ab].value()
        elif "Tasha" in self._method.currentText():
            # Tasha's Reassignment: keep ALL racial traits, only redirect ASI points
            for ab in ABILITIES:
                char["abilities"][ab] = self._ab_blocks[ab].value()
            combined_asi = self._get_combined_racial_asi(char)
            pool = sum(combined_asi.values())
            used = sum(sp.value() for sp in self._tashas_spins.values())
            if pool > 0 and used != pool:
                subrace = char.get("subrace","")
                sub_note = f" ({subrace})" if subrace else ""
                QMessageBox.warning(self, "Tasha's Reassignment",
                    f"You must distribute all {pool} racial ASI point(s) "
                    f"from {char.get('race','')}{sub_note}.\nCurrently placed: {used}")
                return False
            # Store redistribution — builder reads this instead of fixed racial ASI
            char.setdefault("_choices", {})["tashas_asi_reassign"] = {
                ab: sp.value() for ab, sp in self._tashas_spins.items() if sp.value() > 0
            }
        else:
            for ab in ABILITIES:
                char["abilities"][ab] = self._ab_blocks[ab].value()
        # Apply flex ASI choices — two genuinely different mechanics,
        # only one of which is active per race (see _update_flex_asi).
        if hasattr(self, '_flex_card') and self._flex_card.isVisible():
            flex_picks = [ab for ab, cb in self._flex_cbs.items() if cb.isChecked()]
            flex_needed = getattr(self, '_flex_count', 0)
            if flex_needed > 0 and len(flex_picks) < flex_needed:
                QMessageBox.warning(self, "Racial ASI",
                    f"Please choose {flex_needed} abilities to receive +1 (your race grants this).")
                return False
            for ab in flex_picks:
                char["abilities"][ab] = char["abilities"].get(ab, 10) + 1
        if hasattr(self, '_dist_card') and self._dist_card.isVisible():
            if self._dist_radio_a.isChecked():
                ab_plus2 = self._dist_plus2_combo.currentText()
                ab_plus1 = self._dist_plus1_combo.currentText()
                if ab_plus2 == ab_plus1:
                    QMessageBox.warning(self, "Racial ASI",
                        "The +2 and +1 must go to two different abilities.")
                    return False
                char["abilities"][ab_plus2] = char["abilities"].get(ab_plus2, 10) + 2
                char["abilities"][ab_plus1] = char["abilities"].get(ab_plus1, 10) + 1
            else:
                triple_picks = [ab for ab, cb in self._dist_triple_cbs.items() if cb.isChecked()]
                if len(triple_picks) != 3:
                    QMessageBox.warning(self, "Racial ASI",
                        f"Please choose exactly 3 different abilities to receive +1 "
                        f"(currently {len(triple_picks)} chosen).")
                    return False
                for ab in triple_picks:
                    char["abilities"][ab] = char["abilities"].get(ab, 10) + 1
        return True


# ═══════════════════════════════════════════════════════════════════
#  STEP 3: BACKGROUND + CLASS
# ═══════════════════════════════════════════════════════════════════
class Step3Class(QWidget):
    """Step 3 — Character identity: name, alignment, edition, background, starting class."""

    def __init__(self, char, parent=None):
        super().__init__(parent)
        from dnd_app.ui.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24); root.setSpacing(16)
        root.addWidget(_lbl("Character Identity", GOLD2, FS_HEAD, bold=True))
        root.addWidget(_lbl(
            "Choose your name, background, and starting class. "
            "You'll level up and choose subclasses in the main app.",
            TEXT2, FS_BODY))

        form = QFrame()
        form.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:12px;}}")
        fl = QGridLayout(form); fl.setContentsMargins(20,16,20,16); fl.setSpacing(12)

        def row_lbl(text):
            l = _lbl(text, TEXT, FS_BODY, bold=True, wrap=False)
            return l

        # Name
        fl.addWidget(row_lbl("Character Name:"), 0, 0)
        self._name_edit = QLineEdit(); self._name_edit.setPlaceholderText("Enter name…")
        self._name_edit.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:6px;"
            f"padding:6px 10px;font-size:{FS_BODY}px;color:{TEXT};}}")
        fl.addWidget(self._name_edit, 0, 1)

        # Alignment
        fl.addWidget(row_lbl("Alignment:"), 1, 0)
        self._align_combo = QComboBox()
        self._align_combo.setMinimumWidth(220)
        for a in ["Lawful Good","Neutral Good","Chaotic Good","Lawful Neutral","True Neutral",
                  "Chaotic Neutral","Lawful Evil","Neutral Evil","Chaotic Evil"]:
            self._align_combo.addItem(a)
        fl.addWidget(self._align_combo, 1, 1)

        # Edition: 2024 ruleset is incomplete / unverified — hidden from UI.
        # Characters always use 2014 for creation; saves with edition=="2024"
        # are coerced to 2014 on load (see save_load._migrate).
        char.setdefault("edition", "2014")
        fl.addWidget(row_lbl("Edition:"), 2, 0)
        ed_lbl = QLabel("2014 (PHB Classic)")
        ed_lbl.setStyleSheet(f"color:{TEXT2};font-size:12px;")
        fl.addWidget(ed_lbl, 2, 1)
        self._edition_combo = None  # removed; kept attribute absent intentionally

        # Background — searchable list
        fl.addWidget(row_lbl("Background:"), 3, 0)
        bg_container = QWidget()
        bg_vl = QVBoxLayout(bg_container); bg_vl.setContentsMargins(0,0,0,0); bg_vl.setSpacing(3)
        self._bg_search = QLineEdit(); self._bg_search.setPlaceholderText("Search backgrounds…")
        self._bg_search.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:5px 8px;font-size:{FS_SMALL}px;}}"
            f"QLineEdit:focus{{border-color:{INDIGO};}}")
        bg_vl.addWidget(self._bg_search)
        self._bg_list = QListWidget()
        self._bg_list.setMaximumHeight(160)
        self._bg_list.setStyleSheet(
            f"QListWidget{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;"
            f"color:{TEXT};font-size:{FS_SMALL}px;}}"
            f"QListWidget::item{{padding:4px 8px;}}"
            f"QListWidget::item:selected{{background:{INDIGO};color:white;}}"
            f"QListWidget::item:hover:!selected{{background:{SURF3};}}")
        self._all_bg_names = list(BACKGROUND_NAMES)
        for b in self._all_bg_names: self._bg_list.addItem(b)
        def _filter_bg(text):
            for i in range(self._bg_list.count()):
                item = self._bg_list.item(i)
                item.setHidden(text.lower() not in item.text().lower())
        self._bg_search.textChanged.connect(_filter_bg)
        self._bg_list.currentTextChanged.connect(self._on_bg_change)
        bg_vl.addWidget(self._bg_list)
        fl.addWidget(bg_container, 3, 1)
        self._bg_combo = self._bg_list   # alias so collect() still works

        # Background skill info
        self._bg_skills_lbl = _lbl("", TEAL2, FS_SMALL, wrap=True)
        fl.addWidget(self._bg_skills_lbl, 4, 1)
        # Full background detail (feature description, equipment, languages,
        # origin feat) — was a single QLabel capped at 60px with the feature
        # description and equipment text hard-truncated to 120/80 characters
        # respectively, which cut off nearly all of the actual text for any
        # background with a description longer than a sentence or two, and
        # never showed languages or origin feat at all. Same fix pattern as
        # the race detail panel: a read-only, scrollable, untruncated box.
        self._bg_desc_lbl = QTextEdit(); self._bg_desc_lbl.setReadOnly(True)
        self._bg_desc_lbl.setMinimumHeight(140)
        self._bg_desc_lbl.setMaximumHeight(220)
        self._bg_desc_lbl.setStyleSheet(
            f"background:{SURF2};border:1px solid {BORDER};border-radius:6px;"
            f"font-size:{FS_SMALL}px;color:{TEXT};padding:6px;")
        fl.addWidget(self._bg_desc_lbl, 5, 0, 1, 2)

        # Optional background feat choice (Rewarded / Ruined BOMT, etc.)
        self._bg_feat_lbl = row_lbl("Background Feat:")
        self._bg_feat_lbl.setVisible(False)
        fl.addWidget(self._bg_feat_lbl, 6, 0)
        self._bg_feat_combo = QComboBox()
        self._bg_feat_combo.setVisible(False)
        self._bg_feat_combo.setMinimumWidth(220)
        self._bg_feat_combo.setStyleSheet(
            f"QComboBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;}}")
        fl.addWidget(self._bg_feat_combo, 6, 1)

        # Starting Class
        fl.addWidget(row_lbl("Starting Class:"), 7, 0)
        self._cls_combo = QComboBox()
        self._cls_combo.setMinimumWidth(220)
        self._cls_combo.addItem("— Choose Class —")
        for n in CLASS_NAMES: self._cls_combo.addItem(n)
        self._cls_combo.currentTextChanged.connect(self._on_cls_change)
        fl.addWidget(self._cls_combo, 7, 1)

        # Class info label
        self._cls_info_lbl = _lbl("", TEXT3, FS_SMALL, wrap=True)
        fl.addWidget(self._cls_info_lbl, 8, 1)

        root.addWidget(form)
        root.addStretch()

        # Hidden: always level 1
        self._lvl_spin = QSpinBox(); self._lvl_spin.setRange(1,1); self._lvl_spin.setValue(1); self._lvl_spin.hide()

    def _on_bg_change(self, text):
        if text.startswith("—"):
            self._bg_skills_lbl.setText("")
            if hasattr(self, "_bg_desc_lbl"):
                self._bg_desc_lbl.setPlainText("")
            if hasattr(self, "_bg_feat_combo"):
                self._bg_feat_combo.clear()
                self._bg_feat_combo.setVisible(False)
                self._bg_feat_lbl.setVisible(False)
            return
        from dnd_app.data.backgrounds import get_background
        bg = get_background(text) or {}
        feat_choices = bg.get("feat_choices") or []
        # Skills row
        skills = bg.get("skill_proficiencies") or bg.get("skills") or []
        tools  = bg.get("tools") or bg.get("tool_proficiencies") or []
        parts  = []
        if skills: parts.append(f"Skills: {', '.join(skills)}")
        if tools:  parts.append(f"Tools: {', '.join(tools)}")
        self._bg_skills_lbl.setText("  ·  ".join(parts))
        # Full detail box: feature description, equipment, languages, origin
        # feat, and source — all untruncated, since this is meant to be the
        # actual reference a player reads before committing to a choice.
        if hasattr(self, "_bg_desc_lbl"):
            feat = bg.get("feature","")
            feat_desc = bg.get("feature_desc","")
            equipment = bg.get("equipment","")
            languages = bg.get("languages", 0)
            origin_feat = bg.get("origin_feat")
            notes = bg.get("notes","")
            source = bg.get("source","")
            desc_parts = []
            if feat:
                desc_parts.append(f"◆ Feature: {feat}\n{feat_desc}" if feat_desc else f"◆ Feature: {feat}")
            if origin_feat:
                desc_parts.append(f"◆ Origin Feat: {origin_feat}")
            if feat_choices:
                desc_parts.append(f"◆ Feat (choose one): {', '.join(feat_choices)}")
            if languages:
                lang_word = "language" if languages == 1 else "languages"
                desc_parts.append(f"◆ Languages: {languages} {lang_word} of your choice")
            if equipment:
                desc_parts.append(f"◆ Equipment: {equipment}")
            if notes:
                desc_parts.append(f"◆ Notes: {notes}")
            if source:
                desc_parts.append(f"Source: {source}")
            self._bg_desc_lbl.setPlainText("\n\n".join(desc_parts))

        # Show/hide feat picker for backgrounds that grant a choice of feat
        if hasattr(self, "_bg_feat_combo"):
            self._bg_feat_combo.blockSignals(True)
            self._bg_feat_combo.clear()
            if feat_choices:
                self._bg_feat_combo.addItem("— Choose feat —")
                for f in feat_choices:
                    self._bg_feat_combo.addItem(f)
                self._bg_feat_combo.setVisible(True)
                self._bg_feat_lbl.setVisible(True)
            else:
                self._bg_feat_combo.setVisible(False)
                self._bg_feat_lbl.setVisible(False)
            self._bg_feat_combo.blockSignals(False)

    def _on_cls_change(self, text):
        if text.startswith("—"): self._cls_info_lbl.setText(""); return
        from dnd_app.data.classes import CLASS_DICT
        cdata = CLASS_DICT.get(text, {})
        hd = cdata.get("hit_die", 8)
        saves = ", ".join(cdata.get("save_profs", []))
        self._cls_info_lbl.setText(
            f"Hit Die: d{hd}  ·  Saving Throws: {saves}")

    def populate(self, char):
        self._name_edit.setText(char.get("name", ""))
        align = char.get("alignment", "True Neutral")
        idx = self._align_combo.findText(align)
        if idx >= 0: self._align_combo.setCurrentIndex(idx)
        ed = char.get("edition", "2014")
        # 2024 UI is hidden; always display/force 2014 for new edits
        if ed != "2014":
            char["edition"] = "2014"
        bg = char.get("background", "")
        if bg:
            if hasattr(self._bg_combo, 'findItems'):
                items = self._bg_combo.findItems(bg, Qt.MatchExactly)
                if items: self._bg_combo.setCurrentItem(items[0])
            elif hasattr(self._bg_combo, 'findText'):
                bi = self._bg_combo.findText(bg)
                if bi >= 0: self._bg_combo.setCurrentIndex(bi)
            self._on_bg_change(bg)
            chosen = (char.get("_choices") or {}).get("background_feat", "")
            if chosen and hasattr(self, "_bg_feat_combo"):
                fi = self._bg_feat_combo.findText(chosen)
                if fi >= 0:
                    self._bg_feat_combo.setCurrentIndex(fi)
        classes = char.get("classes", [])
        if classes:
            ci = self._cls_combo.findText(classes[0]["class"])
            if ci >= 0: self._cls_combo.setCurrentIndex(ci)

    def _rebuild_choices(self): pass  # no-op, choices handled in main app

    def collect(self, char) -> bool:
        name = self._name_edit.text().strip()
        if not name:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Name Required", "Please enter a character name."); return False
        _cur_bg = self._bg_combo.currentItem() if hasattr(self._bg_combo,'currentItem') else None
        bg_name = _cur_bg.text() if _cur_bg else (self._bg_combo.currentText() if hasattr(self._bg_combo,'currentText') else "")
        if not bg_name or bg_name.startswith("—"):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Background Required", "Please choose a background."); return False
        cls_name = self._cls_combo.currentText()
        if cls_name.startswith("—"):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Class Required", "Please choose a starting class."); return False

        char["name"] = name
        char["alignment"] = self._align_combo.currentText()
        char["edition"] = "2014"
        char["background"] = bg_name

        from dnd_app.data.backgrounds import get_background
        bg_data = get_background(bg_name) or {}
        feat_choices = bg_data.get("feat_choices") or []
        if feat_choices:
            chosen = self._bg_feat_combo.currentText() if hasattr(self, "_bg_feat_combo") else ""
            if not chosen or chosen.startswith("—"):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "Background Feat Required",
                    f"{bg_name} grants a feat — please choose one of: "
                    + ", ".join(feat_choices))
                return False
            if chosen not in feat_choices:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Invalid Feat",
                                    f"Choose one of: {', '.join(feat_choices)}")
                return False
            char["_choices"] = char.get("_choices") or {}
            char["_choices"]["background_feat"] = chosen
        else:
            # Clear prior BOMT-style feat choice when switching away
            if isinstance(char.get("_choices"), dict):
                char["_choices"].pop("background_feat", None)

        from dnd_app.data.classes import CLASS_DICT
        from dnd_app.core.character import add_class
        cdata = CLASS_DICT.get(cls_name, {})
        hd = cdata.get("hit_die", 8)
        char.setdefault("classes", [])
        # Only set if no classes yet, or replace first class
        if not char["classes"] or char["classes"][0]["class"] != cls_name:
            char["classes"] = [{"class": cls_name, "level": 1, "subclass": "", "hit_die": hd}]
        return True


class Step4Spells(QWidget):
    def __init__(self, char, parent=None):
        super().__init__(parent)
        self.char = char
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(12)
        root.addWidget(_lbl("Spells", GOLD2, FS_HEAD, bold=True))
        self._hint = _lbl("", TEXT2, FS_BODY); root.addWidget(self._hint)

        splitter = QSplitter(Qt.Horizontal)

        # Left: browser
        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(8)
        ll.addWidget(_lbl("Available Spells", GOLD, FS_BODY, bold=True))
        top = QHBoxLayout(); top.setSpacing(8)
        self._sp_search = QLineEdit(); self._sp_search.setPlaceholderText("Search spells…")
        self._sp_lvl = QComboBox(); self._sp_lvl.addItem("All Levels")
        self._sp_lvl.setMinimumWidth(130)
        for i in range(10): self._sp_lvl.addItem("Cantrip" if i==0 else f"Level {i}")
        top.addWidget(self._sp_search, 2); top.addWidget(self._sp_lvl)
        ll.addLayout(top)
        self._browser = QListWidget(); self._browser.setMinimumWidth(300)
        ll.addWidget(self._browser, 1)
        add_btn = pill_btn("Add Selected →", INDIGO)
        add_btn.clicked.connect(self._add_selected)
        ll.addWidget(add_btn)
        splitter.addWidget(left)

        # Right: character spells by level
        right = QWidget(); rl = QVBoxLayout(right); rl.setSpacing(6)
        rl.addWidget(_lbl("My Spells", GOLD, FS_BODY, bold=True))
        self._spell_scroll = QScrollArea(); self._spell_scroll.setWidgetResizable(True)
        self._spell_inner = QWidget(); self._spell_lay = QVBoxLayout(self._spell_inner)
        self._spell_lay.setSpacing(4); self._spell_lay.setContentsMargins(4,4,4,4)
        self._spell_lay.addStretch()
        self._spell_scroll.setWidget(self._spell_inner)
        self._spell_rows = []
        self._level_headers = {}
        rl.addWidget(self._spell_scroll, 1)
        splitter.addWidget(right)
        splitter.setSizes([420, 480])
        root.addWidget(splitter, 1)

        self._sp_search.textChanged.connect(self._filter)
        self._sp_lvl.currentTextChanged.connect(self._filter)

    def populate(self, char):
        classes = char.get("classes", [])
        has_spells = any(CLASS_DICT.get(c["class"],{}).get("has_spells",False) for c in classes)
        race = char.get("race","")
        # bonus_spells is computed fresh by rebuild() (called after every
        # wizard step, including the one just before this) and correctly
        # level-gates racial spells — Tiefling doesn't get Hellish
        # Rebuke until 3rd character level, for instance.
        bonus_spells = char.get("bonus_spells", [])

        if has_spells:
            cls_names = [c["class"] for c in classes if CLASS_DICT.get(c["class"],{}).get("has_spells",False)]
            self._hint.setText(f"You are a spellcaster ({', '.join(cls_names)}). Add your known/prepared spells.")
        elif bonus_spells:
            self._hint.setText(f"Your race ({race}) grants innate spells: {', '.join(bonus_spells)}. They've been added automatically.")
        else:
            self._hint.setText("You have no spellcasting classes. Click Next to continue to equipment.")

        # Populate browser
        self._browser.clear()
        for s in ALL_SPELLS:
            lvl_txt = "Ctrp" if s["level"]==0 else f"L{s['level']}"
            conc = " ©" if s.get("concentration") else ""
            rit  = " ®" if s.get("ritual") else ""
            item = QListWidgetItem(f"  {lvl_txt:4s}  {s['name']}{conc}{rit}  [{s['school'][:3]}]")
            item.setData(Qt.UserRole, s)
            self._browser.addItem(item)

        # Clear old spells and add race bonus spells automatically
        for row in self._spell_rows[:]:
            self._spell_lay.removeWidget(row); row.deleteLater()
        self._spell_rows.clear()
        for h in self._level_headers.values():
            self._spell_lay.removeWidget(h); h.deleteLater()
        self._level_headers.clear()

        # Pre-load bonus spells (racial and, if applicable, class/subclass)
        for sp_name in bonus_spells:
            sp = get_spell(sp_name)
            if sp: self._add_spell_row(sp, prepared=True)

        # Pre-load already chosen spells
        for sp_name in char.get("spells_known", []):
            if sp_name not in bonus_spells:
                sp = get_spell(sp_name)
                if sp: self._add_spell_row(sp, prepared=sp_name in char.get("spells_prepared",[]))

    def _filter(self):
        q = self._sp_search.text().lower()
        lvl_txt = self._sp_lvl.currentText()
        for i in range(self._browser.count()):
            item = self._browser.item(i)
            sp = item.data(Qt.UserRole)
            if not sp: continue
            ok = not q or q in sp["name"].lower()
            if lvl_txt != "All Levels":
                ok = ok and ((lvl_txt=="Cantrip" and sp["level"]==0) or
                             (lvl_txt.startswith("Level") and sp["level"]==int(lvl_txt[-1])))
            item.setHidden(not ok)

    def _max_castable_spell_level(self) -> int:
        """Highest spell level the character can currently cast. Computes
        spell_slots_max/pact_slot_level fresh via rebuild()+update_all() on
        the actual char dict, since the wizard's char may not have had
        these derived fields populated yet at this point in creation."""
        from dnd_app.core.calculator import update_all
        rebuild(self.char)
        update_all(self.char)
        max_lvl = 0
        for i, count in enumerate(self.char.get("spell_slots_max", [])):
            if count > 0:
                max_lvl = i + 1
        if self.char.get("pact_slots_max", 0) > 0:
            max_lvl = max(max_lvl, self.char.get("pact_slot_level", 0))
        return max_lvl

    def _add_selected(self):
        max_lvl = self._max_castable_spell_level()
        blocked = []
        for item in self._browser.selectedItems():
            sp = item.data(Qt.UserRole)
            if not sp or any(r.spell["name"]==sp["name"] for r in self._spell_rows):
                continue
            if sp.get("level", 0) > 0 and sp["level"] > max_lvl:
                blocked.append(sp["name"])
                continue
            self._add_spell_row(sp)
        if blocked:
            self._hint.setText(f"⚠ Not added (above your current max castable level {max_lvl}): "
                                f"{', '.join(blocked)}")

    def _add_spell_row(self, spell, prepared=False):
        lvl = spell["level"]
        # Level header
        if lvl not in self._level_headers:
            names = ["Cantrips","1st Level","2nd Level","3rd Level","4th Level",
                     "5th Level","6th Level","7th Level","8th Level","9th Level"]
            hdr = _lbl(names[min(lvl,9)], IND2, FS_SMALL, bold=True)
            hdr.setStyleSheet(hdr.styleSheet() + f"border-bottom:2px solid {qa(IND2,0x44)};padding-bottom:4px;margin-top:6px;")
            self._level_headers[lvl] = hdr
            # Insert at correct position
            insert_idx = self._find_header_pos(lvl)
            self._spell_lay.insertWidget(insert_idx, hdr)

        row = SpellRow(spell, prepared)
        row.remove.connect(self._remove_spell_row)
        insert_idx = self._find_spell_pos(lvl)
        self._spell_lay.insertWidget(insert_idx, row)
        self._spell_rows.append(row)

    def _find_header_pos(self, level):
        for i in range(self._spell_lay.count()):
            w = self._spell_lay.itemAt(i).widget()
            if isinstance(w, QLabel) and w in self._level_headers.values():
                lv = next(k for k,v in self._level_headers.items() if v==w)
                if lv > level: return i
        return self._spell_lay.count() - 1

    def _find_spell_pos(self, level):
        for i in range(self._spell_lay.count()-1, -1, -1):
            w = self._spell_lay.itemAt(i).widget()
            if isinstance(w, SpellRow) and w.spell["level"] <= level: return i+1
            if isinstance(w, QLabel) and w in self._level_headers.values():
                lv = next(k for k,v in self._level_headers.items() if v==w)
                if lv == level: return i+1
        return self._spell_lay.count() - 1

    def _remove_spell_row(self, row):
        lvl = row.spell["level"]
        self._spell_rows.remove(row)
        self._spell_lay.removeWidget(row); row.deleteLater()
        if not any(r.spell["level"]==lvl for r in self._spell_rows):
            if lvl in self._level_headers:
                h = self._level_headers.pop(lvl)
                self._spell_lay.removeWidget(h); h.deleteLater()

    def collect(self, char) -> bool:
        char["spells_known"] = [r.spell["name"] for r in self._spell_rows]
        char["spells_prepared"] = [r.spell["name"] for r in self._spell_rows if r.is_prepared()]
        return True


# ═══════════════════════════════════════════════════════════════════
#  STEP 5: EQUIPMENT
# ═══════════════════════════════════════════════════════════════════
def _weapon_category_pool(category_text: str) -> list:
    """Resolve a starting-equipment placeholder like 'Any simple weapon'
    or 'Any martial melee weapon' to the real, concrete weapon list it
    refers to. Confirmed a real, reported bug: this always fell through
    to a weapon pool for ANY "Any X" text, even non-weapon categories
    like "Any other musical instrument" — which incorrectly resolved to
    simple weapons, since "martial" isn't in that text either. Now
    checks for real non-weapon categories first."""
    from dnd_app.data.items import INSTRUMENT_TOOLS, ARTISAN_TOOLS, GAMING_SETS
    t = category_text.lower()
    if "instrument" in t:
        return list(INSTRUMENT_TOOLS)
    if "artisan" in t:
        return list(ARTISAN_TOOLS)
    if "gaming set" in t:
        return list(GAMING_SETS)
    is_martial = "martial" in t
    is_melee = "melee" in t
    is_ranged = "ranged" in t
    pools = []
    if is_melee:
        pools.append(MARTIAL_MELEE if is_martial else SIMPLE_MELEE)
    elif is_ranged:
        pools.append(MARTIAL_RANGED if is_martial else SIMPLE_RANGED)
    else:
        pools.append(MARTIAL_MELEE if is_martial else SIMPLE_MELEE)
        pools.append(MARTIAL_RANGED if is_martial else SIMPLE_RANGED)
    names = []
    for p in pools:
        names.extend(w[0] for w in p)
    return names


class Step5Equipment(QWidget):
    def __init__(self, char, parent=None):
        super().__init__(parent)
        self.char = char
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(12)
        root.addWidget(_lbl("Starting Equipment", GOLD2, FS_HEAD, bold=True))

        # This whole widget is constructed once, upfront, before the
        # player has picked a class in Step 3, so it starts with an
        # empty class name and zero equipment groups. populate() (called
        # on every navigation into this step) only refreshes the
        # background-gear note below by default, so this section lives
        # in its own container: _rebuild_equipment_groups() can clear
        # and rebuild just this part on every populate() call, without
        # touching the background-gear card or notes field that follow.
        self._equip_container = QWidget()
        self._equip_container_lay = QVBoxLayout(self._equip_container)
        self._equip_container_lay.setContentsMargins(0,0,0,0); self._equip_container_lay.setSpacing(12)
        root.addWidget(self._equip_container, 1)
        self._group_widgets = []
        self._rebuild_equipment_groups(char)

        # Background gear note
        self._bg_gear_card = QFrame()
        self._bg_gear_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(TEAL,0x55)};border-radius:10px;}}")
        bgcl = QVBoxLayout(self._bg_gear_card); bgcl.setContentsMargins(14,12,14,14)
        bgcl.addWidget(_lbl("Starting Gear from Background", TEAL2, FS_BODY, bold=True))
        self._bg_gear_lbl = _lbl("", TEXT2, FS_BODY)
        self._bg_gear_lbl.setWordWrap(True)
        bgcl.addWidget(self._bg_gear_lbl)
        root.addWidget(self._bg_gear_card)

        # Free notes
        root.addWidget(_lbl("Additional Notes / Starting Items:", TEXT, FS_BODY, bold=True))
        self._notes = QTextEdit(); self._notes.setPlaceholderText("List any other starting equipment, currency, notes…")
        self._notes.setMaximumHeight(80)
        root.addWidget(self._notes)

    def _rebuild_equipment_groups(self, char):
        """Build (or rebuild) the class-specific equipment choice groups
        for the character's CURRENT class. Called once at construction
        (when the class may not be picked yet) and again from populate()
        every time the player navigates into this step (when the class
        selection may have changed, or been made for the first time)."""
        for i in reversed(range(self._equip_container_lay.count())):
            w = self._equip_container_lay.itemAt(i).widget()
            if w is not None:
                self._equip_container_lay.removeWidget(w); w.setParent(None); w.deleteLater()
        self._group_widgets = []

        cls_name = char.get("classes", [{}])[0].get("class", "") if char.get("classes") else ""
        self._equip_container_lay.addWidget(_lbl(
            f"Choose your starting equipment ({cls_name}):" if cls_name
            else "Choose your starting equipment:", TEXT2, FS_BODY))

        from dnd_app.data.starting_equipment import get_starting_equipment
        self._groups = get_starting_equipment(cls_name)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        gl = QVBoxLayout(inner); gl.setSpacing(10)

        for gi, group in enumerate(self._groups):
            card = QFrame()
            card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
            cl = QVBoxLayout(card); cl.setContentsMargins(14,12,14,12); cl.setSpacing(6)
            options = group["options"]
            if len(options) == 1:
                opt = options[0]
                any_items = [it for it in opt if it.lower().startswith("any ")]
                if not any_items:
                    # Genuinely fixed, no choice at all — just display it.
                    items_text = ", ".join(opt)
                    cl.addWidget(_lbl(items_text, TEXT, FS_BODY, bold=True))
                    self._group_widgets.append((None, options, [[]]))
                else:
                    # Fixed grant that still needs a concrete weapon
                    # picked for one or more "Any X" slots (e.g.
                    # Warlock's "Any simple weapon") gets a dropdown
                    # here, rather than adding the raw placeholder text
                    # as a fake equipment item.
                    fixed_parts = [it for it in opt if not it.lower().startswith("any ")]
                    if fixed_parts:
                        cl.addWidget(_lbl(", ".join(fixed_parts), TEXT, FS_BODY, bold=True))
                    option_combos = []
                    for item in any_items:
                        row = QHBoxLayout(); row.setSpacing(8)
                        row.addWidget(_lbl(f"{item}:", TEXT2, FS_BODY))
                        combo = QComboBox()
                        combo.setMinimumWidth(220)
                        combo.addItems(_weapon_category_pool(item))
                        row.addWidget(combo)
                        row.addStretch()
                        row_w = QWidget(); row_w.setLayout(row)
                        cl.addWidget(row_w)
                        option_combos.append(combo)
                    self._group_widgets.append((None, options, [option_combos]))
            else:
                btn_group = QButtonGroup(card)
                sub_combos = []
                letters = "abcdefg"
                for oi, opt in enumerate(options):
                    row = QHBoxLayout(); row.setSpacing(8)
                    label_parts = list(opt)
                    rb = QRadioButton(f"({letters[oi]}) " + ", ".join(label_parts))
                    rb.setStyleSheet(f"QRadioButton{{color:{TEXT};font-size:{FS_BODY}px;}}")
                    btn_group.addButton(rb)
                    if oi == 0:
                        rb.setChecked(True)
                    row.addWidget(rb)
                    # One independent combo per "Any X" placeholder in
                    # this option, so an option with two such
                    # placeholders (e.g. Fighter's "two martial weapons")
                    # can pick two different weapons rather than sharing
                    # a single dropdown.
                    option_combos = []
                    for item in opt:
                        if item.lower().startswith("any "):
                            combo = QComboBox()
                            combo.setMinimumWidth(220)
                            combo.addItems(_weapon_category_pool(item))
                            # Combos are enabled only for the currently
                            # selected radio option, so it's clear which
                            # ones actually matter for the result.
                            combo.setEnabled(oi == 0)
                            rb.toggled.connect(lambda checked, c=combo: c.setEnabled(checked))
                            row.addWidget(combo)
                            option_combos.append(combo)
                    sub_combos.append(option_combos)
                    row.addStretch()
                    row_w = QWidget(); row_w.setLayout(row)
                    cl.addWidget(row_w)
                self._group_widgets.append((btn_group, options, sub_combos))
            gl.addWidget(card)

        scroll.setWidget(inner)
        self._equip_container_lay.addWidget(scroll, 1)

    def populate(self, char):
        # Rebuild the class-specific equipment groups every time the
        # player navigates into this step, since the class selection may
        # have just been made for the first time, or changed since the last visit.
        self._rebuild_equipment_groups(char)
        bg = get_background(char.get("background",""))
        if bg:
            gear = bg.get("equipment","")
            self._bg_gear_lbl.setText(str(gear)[:300] if gear else "Standard adventuring gear")

    def collect(self, char) -> bool:
        # Resolve each choice group's selected option into concrete items,
        # then sort those into armor/weapons/general gear.
        chosen_items = []
        for btn_group, options, sub_combos in self._group_widgets:
            if btn_group is None:
                opt = options[0]
                combos = sub_combos[0]
                combo_iter = iter(combos)
                for item in opt:
                    if item.lower().startswith("any "):
                        chosen_items.append(next(combo_iter).currentText())
                    else:
                        chosen_items.append(item)
                continue
            selected_idx = 0
            for i, btn in enumerate(btn_group.buttons()):
                if btn.isChecked():
                    selected_idx = i
                    break
            opt = options[selected_idx]
            combos = sub_combos[selected_idx]
            combo_iter = iter(combos)
            for item in opt:
                if item.lower().startswith("any "):
                    chosen_items.append(next(combo_iter).currentText())
                else:
                    chosen_items.append(item)

        armor_names = {a[0] for a in ARMOR}
        weapon_names = {w[0] for w in ALL_WEAPONS}
        armor_dict = {a[0]: a for a in ARMOR}
        char["armor_worn"] = "No Armor"
        char["shield"] = False
        # setdefault only initializes an empty list, it never clears one
        # that's already there — so navigating back and changing class
        # (re-triggering populate() -> collect()) would otherwise
        # accumulate the previous class's starting equipment on top of
        # the new class's, rather than replacing it. Safe to reset here
        # since this method only runs during the wizard flow, before any
        # real gameplay additions could exist.
        char["equipped_weapons"] = []
        char["equipment"] = []
        from dnd_app.data.items import WEAPON_DICT, EQUIPMENT_PACKS
        for item in chosen_items:
            base = item.split(" (")[0].strip()
            if base == "Shield":
                char["shield"] = True
                a = armor_dict.get("Shield")
                # Adds a corresponding entry to the actual inventory
                # list, not just the mechanical flag used for AC math, so
                # the Gear tab shows starting armor/weapons as owned items.
                char["equipment"].append({"name": "Shield", "qty": 1,
                                          "weight": a[6] if a else 6, "cost": a[7] if a else 10})
            elif base in armor_names:
                char["armor_worn"] = base
                a = armor_dict.get(base)
                char["equipment"].append({"name": base, "qty": 1,
                                          "weight": a[6] if a else 0, "cost": a[7] if a else 0})
            elif base in weapon_names:
                # Each weapon copy is added as its own row rather than
                # skipped when a name is already present, so real
                # multi-weapon starting equipment (e.g. a Rogue's two
                # daggers, "two Handaxes") is fully represented.
                char["equipped_weapons"].append(base)
                w = WEAPON_DICT.get(base, {})
                char["equipment"].append({"name": base, "qty": 1,
                                          "weight": w.get("weight", 0), "cost": w.get("cost", 0)})
            elif base in EQUIPMENT_PACKS:
                # A chosen pack adds its real, individual contents rather than a single, opaque item.
                for pack_item, qty in EQUIPMENT_PACKS[base]:
                    char["equipment"].append({"name": pack_item, "qty": qty, "weight": 0, "cost": 0})
            else:
                char["equipment"].append({"name": item, "qty": 1, "weight": 0, "cost": 0})

        # Background equipment is parsed and added to the character's
        # real inventory/currency, not just shown as display text.
        bg = get_background(char.get("background", ""))
        bg_eq_text = (bg or {}).get("equipment", "")
        if bg_eq_text and char.get("background") != "Custom Background":
            import re
            parts, depth, current = [], 0, ""
            for ch in bg_eq_text:
                if ch == '(':
                    depth += 1; current += ch
                elif ch == ')':
                    depth -= 1; current += ch
                elif ch == ',' and depth == 0:
                    parts.append(current.strip()); current = ""
                else:
                    current += ch
            if current.strip():
                parts.append(current.strip())
            for p in parts:
                m = re.match(r'^(\d+)\s*(gp|sp|cp|ep|pp)$', p, re.IGNORECASE)
                if m:
                    cur = char.setdefault("currency", {})
                    denom = m.group(2).upper()
                    cur[denom] = cur.get(denom, 0) + int(m.group(1))
                elif p:
                    char["equipment"].append({"name": p, "qty": 1, "weight": 0, "cost": 0})

        notes = self._notes.toPlainText()
        if notes: char["notes"] = notes
        return True
