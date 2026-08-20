"""
Level-Up Panel module.

PySide6 widget for both initial character creation and later level-
ups. Presents every pending choice a level grants (ASI/feat, subclass
picks, spells known/prepared, fighting styles, infusions, invocations,
racial/subclass sub-choices such as Eladrin season or Lunar Sorcery
phase) with enforce-count validation and confirm-on-done, then calls
into dnd_app.core.builder to apply the results to the character dict.

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor
from .theme import *
from dnd_app.core.builder import (
    get_choices_needed, apply_choice, rebuild,
    get_background_skills, get_race_skills, get_race_asi,
)
from dnd_app.core.calculator import resolve_stat_placeholders

ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]
ALL_SKILLS = [
    "Acrobatics","Animal Handling","Arcana","Athletics","Deception","History",
    "Insight","Intimidation","Investigation","Medicine","Nature","Perception",
    "Performance","Persuasion","Religion","Sleight of Hand","Stealth","Survival",
]
LANGUAGES = [
    "Aarakocra", "Abanasinian", "Abyssal", "Alzhedo", "Blink Dog", "Bothii", "Bullywug",
    "Celestial", "Chessentan", "Chondathan", "Common", "Daelkyr", "Damaran", "Dambrathan",
    "Deep Crow", "Deep Speech", "Draconic", "Druidic", "Dwarvish", "Elvish", "Ergot",
    "Giant", "Giant Eagle", "Giant Elk", "Giant Owl", "Gith", "Gnoll", "Gnomish", "Goblin",
    "Grell", "Grung", "Guran", "Halfling", "Halruaan", "Hook Horror", "Ice Toad", "Illuskan",
    "Infernal", "Istarian", "Ixitxachitl", "Kenderspeak", "Kharolian", "Khur", "Kothian",
    "Kraul", "Kruthik", "Leonin", "Loross", "Loxodon", "Marquesian", "Merfolk", "Midani",
    "Minotaur", "Modron", "Mulhorandi", "Naush", "Nerakese", "Netherese", "Nordmaarian",
    "Ogre", "Olman", "Orc", "Otyugh", "Primordial", "Qualith", "Quori", "Rashemi", "Riedran",
    "Roushoum", "Sahuagin", "Shaaran", "Shou", "Slaad", "Solamnic", "Sphinx", "Sylvan",
    "Thayan", "Thieves' Cant", "Thri-kreen", "Tlincalli", "Troglodyte", "Tuigan", "Turmic",
    "Uluik", "Umber Hulk", "Undercommon", "Untheric", "Vedalken", "Vegepygmy", "Waelan",
    "Winter Wolf", "Worg", "Yeti", "Yikaria", "Zemnian"
]

FIGHTING_STYLES = {
    "Fighter": ["Archery (+2 to ranged attack rolls)",
                "Blind Fighting (blindsight 10 ft, see through blindness/darkness in range)",
                "Defense (+1 AC while wearing armor)",
                "Dueling (+2 damage on one-handed melee weapon, no other weapon)",
                "Great Weapon Fighting (reroll 1s and 2s on damage dice, two-handed/versatile)",
                "Interception (reaction: reduce damage to a nearby ally by 1d10+PB)",
                "Protection (impose disadvantage on attack vs adjacent ally, requires shield)",
                "Superior Technique (learn 1 Battle Master maneuver + 1 superiority die)",
                "Thrown Weapon Fighting (draw as part of the attack; +2 damage on thrown hits)",
                "Two-Weapon Fighting (add ability modifier to off-hand attack)",
                "Unarmed Fighting (unarmed strikes deal 1d6+STR, or 1d8 with two free hands)"],
    "Paladin": ["Blessed Warrior (learn 2 cleric cantrips, CHA-based)",
                "Defense (+1 AC while wearing armor)",
                "Dueling (+2 damage on one-handed melee weapon, no other weapon)",
                "Great Weapon Fighting (reroll 1s and 2s on damage dice, two-handed/versatile)",
                "Interception (reaction: reduce damage to a nearby ally by 1d10+PB)",
                "Protection (impose disadvantage on attack vs adjacent ally, requires shield)"],
    "Ranger":  ["Archery (+2 to ranged attack rolls)",
                "Blind Fighting (blindsight 10 ft, see through blindness/darkness in range)",
                "Defense (+1 AC while wearing armor)",
                "Druidic Warrior (learn 2 druid cantrips, WIS-based)",
                "Dueling (+2 damage on one-handed melee weapon, no other weapon)",
                "Thrown Weapon Fighting (draw as part of the attack; +2 damage on thrown hits)",
                "Two-Weapon Fighting (add ability modifier to off-hand attack)"],
}

RACE_SKILL_CHOICES = {
    "Half-Elf":  {"count": 2, "pool": ALL_SKILLS, "label": "Skill Versatility (Half-Elf): choose 2 skills"},
    "Kenku":     {"count": 2, "pool": ["Acrobatics","Deception","Stealth","Sleight of Hand"],
                  "label": "Kenku Training: choose 2 of Acrobatics, Deception, Stealth, Sleight of Hand"},
    "Kenku (MPMM)": {"count": 2, "pool": ALL_SKILLS,
                      "label": "Kenku Recall (MPMM): choose 2 skills"},
    "Human (Variant)": {"count": 1, "pool": ALL_SKILLS, "label": "Human Variant: choose 1 skill proficiency"},
    "Centaur":   {"count": 1, "pool": ["Animal Handling","Medicine","Nature","Survival"],
                  "label": "Survivor (Centaur): choose 1 of Animal Handling, Medicine, Nature, Survival"},
    "Leonin":    {"count": 1, "pool": ["Intimidation","Athletics","Perception","Survival"],
                  "label": "Hunter's Instincts (Leonin): choose 1 of Intimidation, Athletics, Perception, Survival"},
    "Minotaur":  {"count": 1, "pool": ["Intimidation","Persuasion"],
                  "label": "Imposing Presence (Minotaur): choose 1 of Intimidation or Persuasion"},
    "Dhampir":   {"count": 2, "pool": ALL_SKILLS,
                  "label": "Ancestral Legacy (Dhampir): choose 2 skill proficiencies"},
    "Hexblood":  {"count": 2, "pool": ALL_SKILLS,
                  "label": "Ancestral Legacy (Hexblood): choose 2 skill proficiencies"},
    "Reborn":    {"count": 2, "pool": ALL_SKILLS,
                  "label": "Ancestral Legacy (Reborn): choose 2 skill proficiencies"},
}

SOURCE_COLORS = {"race": TEAL2, "background": GOLD, "class": IND2, "subclass": PURP2}


def _lbl(text, color=TEXT, bold=False, size=FS_BODY, align=Qt.AlignLeft, wrap=True):
    w = QLabel(text)
    w.setStyleSheet(f"color:{color};font-size:{size}px;{'font-weight:700;' if bold else ''}")
    w.setAlignment(align)
    if wrap: w.setWordWrap(True)
    return w


# ═══════════════════════════════════════════════════════════════════
#  CHOICE WIDGET — one card per pending choice
# ═══════════════════════════════════════════════════════════════════
class ChoiceWidget(QFrame):
    choice_confirmed = Signal(str, list)   # (choice_id, final_selected)

    def __init__(self, choice_info: dict, char: dict, parent=None):
        super().__init__(parent)
        self.choice_info = choice_info
        self.char = char
        self._selected = list(choice_info.get("already_chosen", []))
        self._confirmed = len(self._selected) >= choice_info.get("count", 1)
        self._count = choice_info.get("count", 1)

        bg = SOURCE_COLORS.get(choice_info.get("source", "class"), IND2)
        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border:1px solid {qa(bg,0x44)};"
            f"border-left:3px solid {bg};border-radius:6px;}}"
        )
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(10, 8, 10, 10)
        self._lay.setSpacing(6)

        # Header row
        head = QHBoxLayout(); head.setSpacing(8)
        src_badge = _lbl(choice_info.get("source","").upper(), "white", bold=True, size=FS_TINY, wrap=False)
        src_badge.setFixedHeight(18)
        src_badge.setStyleSheet(f"color:white;font-size:{FS_TINY}px;font-weight:700;background:{bg};"
                                 f"border-radius:8px;padding:2px 7px;")
        head.addWidget(src_badge)
        src_name = choice_info.get("source_name","")
        if src_name:
            head.addWidget(_lbl(src_name, bg, bold=True, size=FS_BODY, wrap=False))
        head.addWidget(_lbl(choice_info["label"], TEXT, bold=True, size=FS_LABEL))
        head.addStretch()
        self._done_lbl = _lbl("✓ Done", TEAL2, bold=True, size=FS_BODY, wrap=False)
        self._done_lbl.setVisible(self._confirmed)
        head.addWidget(self._done_lbl)
        self._lay.addLayout(head)

        # Build chooser based on type
        ctype = choice_info.get("type", "skill_prof")
        if ctype in ("skill_prof", "expertise"):
            self._build_skill_chooser(ctype)
        elif ctype == "tool_prof":
            self._build_tool_chooser()
        elif ctype == "skill_or_tool_prof":
            self._build_tool_chooser()  # generic checkbox-from-pool behavior works for a mixed pool too
        elif ctype == "language":
            self._build_language_chooser()
        elif ctype == "asi_or_feat":
            self._build_asi_chooser()
        elif ctype == "fighting_style":
            self._build_radio_chooser(choice_info.get("pool", []))
        elif ctype == "subclass":
            self._build_subclass_chooser()
        elif ctype == "invocation":
            self._build_invocation_chooser()
        elif ctype in ("metamagic", "discipline"):
            self._build_metamagic_chooser()
        elif ctype == "maneuver":
            self._build_maneuver_chooser()
        elif ctype == "infusion":
            self._build_infusion_chooser()
        elif ctype == "magical_secrets":
            self._build_spell_chooser_generic()
        elif ctype == "info":
            pass   # label only

        # Confirm button for multi-select choices
        if self._count > 1 and not self._confirmed:
            self._confirm_btn = QPushButton(f"✓  Confirm  ({len(self._selected)}/{self._count} selected)")
            self._confirm_btn.setFixedHeight(40)
            self._confirm_btn.setStyleSheet(
                f"QPushButton{{background:{qa(bg,0x22)};border:2px solid {bg};"
                f"border-radius:8px;color:{bg};font-weight:700;font-size:{FS_BODY}px;padding:6px 14px;}}"
                f"QPushButton:hover:enabled{{background:{bg};color:white;}}"
                f"QPushButton:disabled{{background:{SURF};color:{TEXT3};border-color:{BORDER};}}") 
            self._confirm_btn.setEnabled(len(self._selected) >= self._count)
            self._confirm_btn.clicked.connect(self._on_confirm)
            self._lay.addWidget(self._confirm_btn)
        else:
            self._confirm_btn = None

    # ── Skill chooser ─────────────────────────────────────────────
    def _build_skill_chooser(self, mode):
        explicit_pool = self.choice_info.get("pool")
        if mode == "expertise" and not explicit_pool:
            # Standard case (Rogue/Bard/feats): "choose from any skill
            # you're already proficient in" — expertise requires
            # existing proficiency. Does NOT apply when a caller already
            # provides an explicit, restricted pool (e.g. Knowledge
            # Domain's 4-skill list, which grants proficiency AND
            # expertise together regardless of prior proficiency — a
            # genuinely different mechanic).
            pool = [s for s, lvl in self.char.get("skills", {}).items() if lvl >= 2]
        else:
            raw_pool = explicit_pool or ALL_SKILLS
            # If pool is a placeholder like ['Any 3 skills'], use full skill list
            if len(raw_pool)==1 and 'any' in str(raw_pool[0]).lower():
                pool = ALL_SKILLS
            else:
                pool = raw_pool
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMinimumHeight(100)
        scroll.setStyleSheet(f"QScrollArea{{background:transparent;border:1px solid {BORDER};border-radius:4px;}}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        grid = QGridLayout(inner); grid.setSpacing(2); grid.setContentsMargins(4,4,4,4)
        self._skill_cbs = {}

        for i, skill in enumerate(pool):
            current = self.char.get("skills",{}).get(skill, 0)
            cb = QCheckBox(skill)
            cb.setChecked(skill in self._selected)
            if mode == "expertise":
                if current == 3 and skill not in self._selected:
                    cb.setStyleSheet(f"QCheckBox{{color:{TEXT3};text-decoration:line-through;font-size:{FS_BODY}px;}}")
                    cb.setToolTip("Already has Expertise")
                else:
                    cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;}}")
            elif current == 3 and skill not in self._selected:
                cb.setStyleSheet(f"QCheckBox{{color:{TEXT3};text-decoration:line-through;font-size:{FS_BODY}px;}}")
                cb.setToolTip("Already has Expertise")
            elif current >= 2 and skill not in self._selected:
                cb.setStyleSheet(f"QCheckBox{{color:{TEXT3};font-size:{FS_BODY}px;}}")
                cb.setToolTip("Already proficient (choosing again is wasted)")
            else:
                cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;}}")
            cb.stateChanged.connect(lambda s, sk=skill: self._on_check(sk, s))
            grid.addWidget(cb, i // 3, i % 3)
            self._skill_cbs[skill] = cb

        scroll.setWidget(inner)
        self._lay.addWidget(scroll)
        self._status = _lbl(self._status_text(), TEXT2, size=FS_SMALL)
        self._lay.addWidget(self._status)

    # ── Tool proficiency chooser ──────────────────────────────────
    def _build_tool_chooser(self):
        from dnd_app.data.items import ALL_TOOLS
        pool = self.choice_info.get("pool") or ALL_TOOLS
        current_tools = set(self.char.get("tool_proficiencies", []))

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMinimumHeight(140)
        scroll.setStyleSheet(f"QScrollArea{{background:transparent;border:1px solid {BORDER};border-radius:4px;}}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        grid = QGridLayout(inner); grid.setSpacing(2); grid.setContentsMargins(4,4,4,4)
        self._tool_cbs = {}

        for i, tool in enumerate(pool):
            cb = QCheckBox(tool)
            cb.setChecked(tool in self._selected)
            if tool in current_tools and tool not in self._selected:
                cb.setStyleSheet(f"QCheckBox{{color:{TEXT3};font-size:{FS_BODY}px;}}")
                cb.setToolTip("Already proficient (choosing again is wasted)")
            else:
                cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;}}")
            cb.stateChanged.connect(lambda s, t=tool: self._on_tool_check(t, s))
            grid.addWidget(cb, i // 3, i % 3)
            self._tool_cbs[tool] = cb

        scroll.setWidget(inner)
        self._lay.addWidget(scroll)
        self._status = _lbl(self._status_text(), TEXT2, size=FS_SMALL)
        self._lay.addWidget(self._status)

    def _on_tool_check(self, value, state):
        checked = bool(state)
        if checked:
            if value not in self._selected and len(self._selected) < self._count:
                self._selected.append(value)
            elif value not in self._selected:
                # Over the limit — revert the checkbox rather than silently exceeding count.
                self._tool_cbs[value].blockSignals(True)
                self._tool_cbs[value].setChecked(False)
                self._tool_cbs[value].blockSignals(False)
                return
        else:
            if value in self._selected:
                self._selected.remove(value)
        if hasattr(self, "_status"):
            self._status.setText(self._status_text())
        if len(self._selected) == self._count:
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], list(self._selected))

    # ── Language chooser ──────────────────────────────────────────
    def _build_language_chooser(self):
        n = self._count
        pool = self.choice_info.get("pool", LANGUAGES)
        self._lang_combos = []
        row = QHBoxLayout(); row.setSpacing(6)
        for i in range(n):
            combo = QComboBox(); combo.addItem("— Choose —")
            for lang in pool: combo.addItem(lang)
            if i < len(self._selected):
                idx = combo.findText(self._selected[i])
                if idx >= 0: combo.setCurrentIndex(idx)
            combo.currentTextChanged.connect(self._on_lang_change)
            row.addWidget(combo)
            self._lang_combos.append(combo)
        row.addStretch()
        self._lay.addLayout(row)

    def _on_lang_change(self):
        sel = [c.currentText() for c in self._lang_combos if c.currentText() != "— Choose —"]
        self._selected = sel
        if len(sel) == self._count:
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], sel)

    # ── Radio chooser (Fighting Style, etc.) ─────────────────────
    def _build_radio_chooser(self, pool):
        self._radio_group = QButtonGroup(self)
        for item in pool:
            rb = QRadioButton(item)
            rb.setStyleSheet(f"QRadioButton{{color:{TEXT};font-size:{FS_BODY}px;}}") 
            rb.setChecked(item in self._selected)
            rb.toggled.connect(lambda checked, v=item: self._on_radio(v, checked))
            self._lay.addWidget(rb)
            self._radio_group.addButton(rb)

    def _on_radio(self, value, checked):
        if checked:
            self._selected = [value]
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], [value])

    # ── ASI / Feat chooser ────────────────────────────────────────
    def _build_asi_chooser(self):
        from dnd_app.core.character import ability_score as _as, ability_mod as _am
        self._asi_type = QComboBox()
        self._asi_type.addItems(["+2 to one ability", "+1 to two abilities", "Take a Feat"])
        self._lay.addWidget(self._asi_type)

        self._asi_frame = QWidget(); self._asi_frame.setStyleSheet("background:transparent;")
        asf = QGridLayout(self._asi_frame)
        asf.setSpacing(4); asf.setContentsMargins(0,0,0,0)
        self._asi_spins = {}; self._asi_mod_lbls = {}

        for col_i, ab in enumerate(ABILITIES):
            asf.addWidget(_lbl(ab, TEXT3, bold=True, size=FS_SMALL, align=Qt.AlignCenter), 0, col_i)

            # Live score + modifier preview (updates as user clicks +/-)
            cur_score = _as(self.char, ab) if self.char else 10
            cur_mod   = _am(self.char, ab) if self.char else 0
            sign = "+" if cur_mod >= 0 else ""
            mod_lbl = QLabel(f"{cur_score}\n({sign}{cur_mod})")
            mod_lbl.setAlignment(Qt.AlignCenter)
            mod_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:600;background:transparent;")
            self._asi_mod_lbls[ab] = mod_lbl
            asf.addWidget(mod_lbl, 1, col_i)

            # Restore saved value
            saved = 0
            for item in self._selected:
                if item.startswith(f"asi:{ab}:"):
                    saved = int(item.split(":")[2])

            # Hidden QSpinBox for state tracking
            sp = QSpinBox(); sp.setRange(0, 2); sp.setValue(saved); sp.hide()
            self._asi_spins[ab] = sp

            # − [val] + control row
            val_lbl = QLabel(str(saved)); val_lbl.setFixedWidth(38)
            val_lbl.setAlignment(Qt.AlignCenter)
            bc = TEAL2 if saved > 0 else BORDER2
            val_lbl.setStyleSheet(f"color:{TEAL2};font-size:{FS_BODY}px;font-weight:700;"
                                  f"background:{SURF2};border:2px solid {bc};border-radius:4px;")

            minus = QPushButton("−"); minus.setFixedSize(26, 28)
            minus.setStyleSheet(
                f"QPushButton{{background:{SURF2};border:1px solid {BORDER2};"
                f"border-radius:4px;color:{TEXT2};font-size:15px;font-weight:700;padding:0;}}"
                f"QPushButton:hover{{background:{qa(CRIMSON,0x55)};color:{CRIM2};}}"
                f"QPushButton:pressed{{background:{CRIMSON};color:white;}}")
            plus = QPushButton("+"); plus.setFixedSize(26, 28)
            plus.setStyleSheet(
                f"QPushButton{{background:{SURF2};border:1px solid {BORDER2};"
                f"border-radius:4px;color:{TEXT2};font-size:15px;font-weight:700;padding:0;}}"
                f"QPushButton:hover{{background:{qa(TEAL,0x55)};color:{TEAL2};}}"
                f"QPushButton:pressed{{background:{TEAL};color:white;}}")

            ctrl_w = QWidget(); ctrl_w.setStyleSheet("background:transparent;")
            ctrl_lay = QHBoxLayout(ctrl_w)
            ctrl_lay.setContentsMargins(0,0,0,0); ctrl_lay.setSpacing(2)
            ctrl_lay.addWidget(minus); ctrl_lay.addWidget(val_lbl); ctrl_lay.addWidget(plus)
            asf.addWidget(ctrl_w, 2, col_i)

            def _wire(ability, vl, sp_ref):
                def _minus():
                    if sp_ref.value() > 0:
                        sp_ref.setValue(sp_ref.value() - 1)
                        vl.setText(str(sp_ref.value()))
                        bc2 = TEAL2 if sp_ref.value() > 0 else BORDER2
                        vl.setStyleSheet(f"color:{TEAL2};font-size:{FS_BODY}px;font-weight:700;"
                                         f"background:{SURF2};border:2px solid {bc2};border-radius:4px;")
                        self._on_asi_spin_manual(ability, sp_ref.value())
                def _plus():
                    if sp_ref.value() < sp_ref.maximum():
                        sp_ref.setValue(sp_ref.value() + 1)
                        vl.setText(str(sp_ref.value()))
                        vl.setStyleSheet(f"color:{TEAL2};font-size:{FS_BODY}px;font-weight:700;"
                                         f"background:{SURF2};border:2px solid {TEAL2};border-radius:4px;")
                        self._on_asi_spin_manual(ability, sp_ref.value())
                return _minus, _plus

            h_minus, h_plus = _wire(ab, val_lbl, sp)
            minus.clicked.connect(h_minus)
            plus.clicked.connect(h_plus)

        self._lay.addWidget(self._asi_frame)

        # Feat chooser frame — searchable list
        self._feat_frame = QWidget(); self._feat_frame.setStyleSheet("background:transparent;")
        ff = QVBoxLayout(self._feat_frame); ff.setSpacing(4); ff.setContentsMargins(0,0,0,0)
        feat_hdr = QHBoxLayout()
        feat_hdr.addWidget(_lbl("Choose Feat:", TEXT2, size=FS_BODY, bold=True, wrap=False))
        from dnd_app.data.feats import ALL_FEATS
        self._feat_search = QLineEdit(); self._feat_search.setPlaceholderText("Search feats…")
        self._feat_search.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;font-size:{FS_SMALL}px;}}"
            f"QLineEdit:focus{{border-color:{INDIGO};}}")
        feat_hdr.addWidget(self._feat_search, 1)
        ff.addLayout(feat_hdr)
        self._feat_list = QListWidget()
        self._feat_list.setMaximumHeight(150)
        self._feat_list.setStyleSheet(
            f"QListWidget{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;"
            f"color:{TEXT};font-size:{FS_SMALL}px;}}"
            f"QListWidget::item{{padding:3px 8px;}}"
            f"QListWidget::item:selected{{background:{INDIGO};color:white;}}"
            f"QListWidget::item:hover:!selected{{background:{SURF3};}}")
        for ft in ALL_FEATS:
            item = QListWidgetItem(ft["name"])
            prereq = ft.get("prereq","")
            met, reason = feat_prereq_met(self.char, ft) if self.char else (True, "")
            if not met:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                item.setForeground(QColor(TEXT3))
            item.setToolTip(f"<b>{ft['name']}</b>  [{ft.get('source','')}]"
                           + (f"<br><i>Requires: {prereq}</i>" if prereq else "")
                           + (f"<br><b>Prerequisite not met</b>" if not met else "")
                           + f"<br>{ft.get('special','')[:200]}")
            self._feat_list.addItem(item)
        def _filter_feats(text):
            for i in range(self._feat_list.count()):
                it = self._feat_list.item(i)
                it.setHidden(text.lower() not in it.text().lower())
        self._feat_search.textChanged.connect(_filter_feats)
        self._feat_list.currentItemChanged.connect(lambda cur,prev: self._on_feat_list_changed(cur.text() if cur else ""))
        ff.addWidget(self._feat_list)
        # Keep _feat_combo alias for backward compatibility
        self._feat_combo = self._feat_list
        for item in self._selected:
            if item.startswith("feat:"):
                idx = self._feat_combo.findText(item.split(":",1)[1])
                if idx >= 0: self._feat_combo.setCurrentIndex(idx)
        ff.addWidget(self._feat_combo); ff.addStretch()
        self._feat_frame.setVisible(False)
        self._lay.addWidget(self._feat_frame)

        # Points remaining label
        self._asi_total = _lbl("Points: 0/2", TEXT2, size=FS_SMALL, bold=True)
        self._asi_total.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:700;background:transparent;")
        self._lay.addWidget(self._asi_total)

        self._asi_type.currentTextChanged.connect(self._on_asi_type)
        self._feat_combo.currentTextChanged.connect(self._on_feat_pick)

    def _on_feat_list_changed(self, feat_name: str):
        """
        Called when user selects a feat from the searchable list. If the feat
        grants an ability score increase (fixed asi={} or a player-chosen
        asi_flex=[...]), bake an "asi:ABILITY:VALUE" entry into the same
        selection list — rebuild() already scans every _choices list for
        these regardless of which key they live under, so this is enough
        for the bonus to actually apply with no further engine changes.
        """
        if not feat_name:
            return
        # Reset fully — only one feat can be active in "Take a Feat" mode,
        # so any stale asi:/feat: entries from a previous pick must go too.
        self._selected = []
        self._selected.append(f"feat:{feat_name}")

        from dnd_app.data.feats import get_feat
        fdata = get_feat(feat_name) or {}
        fixed_asi = fdata.get("asi") or {}
        flex_asi = fdata.get("asi_flex") or []
        chosen_ability = None

        if fixed_asi:
            for ab, val in fixed_asi.items():
                self._selected.append(f"asi:{ab}:{val}")
                chosen_ability = ab  # only relevant for single-key fixed dicts
        elif len(flex_asi) == 1:
            chosen_ability = flex_asi[0]
            self._selected.append(f"asi:{chosen_ability}:1")
        elif len(flex_asi) > 1:
            chosen_ability = self._prompt_feat_ability_choice(feat_name, flex_asi)
            if chosen_ability:
                self._selected.append(f"asi:{chosen_ability}:1")

        # Resilient also grants saving throw proficiency in the SAME ability
        # chosen for its +1 — write directly into the dedicated extra_save_profs
        # slot that builder.py's rebuild() already reads.
        if feat_name == "Resilient" and chosen_ability:
            extra_saves = self.char.setdefault("_choices", {}).setdefault("extra_save_profs", [])
            if chosen_ability not in extra_saves:
                extra_saves.append(chosen_ability)

        # Forest Sage: the same +1-ability choice also determines which
        # ability substitutes for Animal Handling/Arcana/Nature/Survival
        # checks — store it for get_skill_bonus() to read.
        if feat_name == "Forest Sage" and chosen_ability:
            self.char.setdefault("_choices", {})["forest_sage_ability"] = chosen_ability

        # Generic fallback: ANY feat with a multi-option asi_flex (e.g.
        # Telekinetic's INT/WIS/CHA choice) gets its chosen ability
        # stored too, keyed by feat name — not just the two feats above
        # that already had dedicated storage for their own specific
        # mechanical use of the choice. This is what lets the Features
        # tab show which ability a feat like Telekinetic actually keyed off.
        if chosen_ability and len(flex_asi) > 1:
            self.char.setdefault("_choices", {})[f"feat_ability_{feat_name.lower().replace(' ','_')}"] = chosen_ability

        # Elemental Adept: reuses the same generic choice dialog (it only
        # needs a list of options, not specifically abilities). This was
        # a documented, deliberate gap — no choice-tracking mechanism
        # existed for it before, so the resistance table couldn't
        # represent a feat needing a chosen damage type.
        if feat_name == "Elemental Adept":
            chosen_element = self._prompt_feat_ability_choice(
                feat_name, ["Acid", "Cold", "Fire", "Lightning", "Thunder"])
            if chosen_element:
                self.char.setdefault("_choices", {})["elemental_adept_type"] = chosen_element

        # Notify parent via the same signal other choices use
        if hasattr(self, "choice_confirmed"):
            self.choice_confirmed.emit(self.choice_info["id"], self._selected)

    def _prompt_feat_ability_choice(self, feat_name: str, options: list) -> str | None:
        """Small dialog letting the player pick which ability gets +1 from a feat."""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"{feat_name} — Choose Ability")
        dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg); lay.setSpacing(10)
        lay.addWidget(_lbl(
            f"{feat_name} grants +1 to one ability score. Which one?",
            TEXT2, size=FS_BODY, wrap=True))
        btn_row = QHBoxLayout(); btn_row.setSpacing(6)
        chosen = {"value": None}
        for ab in options:
            b = QPushButton(ab)
            b.setFixedSize(72, 38)
            b.setStyleSheet(
                f"QPushButton{{background:{SURF2};border:1px solid {BORDER2};"
                f"border-radius:6px;color:{TEXT};font-size:{FS_BODY}px;font-weight:700;padding:0;}}"
                f"QPushButton:hover{{background:{INDIGO};color:white;}}")
            def _pick(checked=False, a=ab):
                chosen["value"] = a
                dlg.accept()
            b.clicked.connect(_pick)
            btn_row.addWidget(b)
        lay.addLayout(btn_row)
        dlg.exec()
        return chosen["value"]


    def _on_asi_type(self, text):
        is_feat = text == "Take a Feat"
        self._asi_frame.setVisible(not is_feat)
        self._feat_frame.setVisible(is_feat)
        is_plus2_one = "+2 to one" in text
        # Reset all spins and update ranges
        for ab, sp in self._asi_spins.items():
            sp.blockSignals(True)
            sp.setRange(0, 2 if is_plus2_one else 1)
            sp.setValue(0)
            sp.blockSignals(False)
        # Reset val labels in the grid
        for vl in self._asi_frame.findChildren(QLabel):
            text_v = vl.text()
            if text_v in ("0", "1", "2"):
                vl.setText("0")
                vl.setStyleSheet(f"color:{TEAL2};font-size:{FS_BODY}px;font-weight:700;"
                                 f"background:{SURF2};border:2px solid {BORDER2};border-radius:4px;")
        self._selected = []
        self._asi_total.setText("Points: 0/2")
        self._asi_total.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:700;background:transparent;")
        # Reset modifier labels to base scores
        from dnd_app.core.character import ability_score as _as, ability_mod as _am
        if hasattr(self, "_asi_mod_lbls") and self.char:
            for ab, mod_lbl in self._asi_mod_lbls.items():
                sc = _as(self.char, ab); md = _am(self.char, ab)
                sign = "+" if md >= 0 else ""
                mod_lbl.setText(f"{sc}\n({sign}{md})")
                mod_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:600;background:transparent;")

    def _on_asi_spin(self):
        # Legacy signal from hidden QSpinBox — delegate to manual handler
        self._on_asi_spin_manual(None, None)

    def _on_asi_spin_manual(self, changed_ab=None, new_val=None):
        from dnd_app.core.character import ability_score as _as
        asi_text = self._asi_type.currentText() if hasattr(self, "_asi_type") else "+2 to one ability"
        is_plus2_one = "+2 to one" in asi_text
        max_pts = 2
        total = sum(sp.value() for sp in self._asi_spins.values())
        # For +2 to one: clear other spinboxes
        if is_plus2_one and changed_ab:
            for ab, sp in self._asi_spins.items():
                if ab != changed_ab and sp.value() > 0:
                    sp.blockSignals(True); sp.setValue(0); sp.blockSignals(False)
            total = sum(sp.value() for sp in self._asi_spins.values())
        # Clamp total
        if total > max_pts:
            for ab, sp in self._asi_spins.items():
                if ab != changed_ab and sp.value() > 0 and total > max_pts:
                    excess = total - max_pts
                    sp.blockSignals(True); sp.setValue(max(0, sp.value()-excess)); sp.blockSignals(False); break
            total = sum(sp.value() for sp in self._asi_spins.values())
        # Update total label
        color = TEAL2 if total <= max_pts else CRIM2
        self._asi_total.setText(f"Points: {total}/{max_pts}")
        self._asi_total.setStyleSheet(f"color:{color};font-size:{FS_SMALL}px;font-weight:700;background:transparent;")
        # Update EVERY ability modifier preview label LIVE
        if hasattr(self, "_asi_mod_lbls") and self.char:
            for ab, mod_lbl in self._asi_mod_lbls.items():
                base = _as(self.char, ab)
                bonus = self._asi_spins[ab].value()
                new_score = base + bonus
                new_mod = (new_score - 10) // 2
                sign = "+" if new_mod >= 0 else ""
                mod_lbl.setText(f"{new_score}\n({sign}{new_mod})")
                fg = TEAL2 if bonus > 0 else (TEXT2 if new_mod >= 0 else CRIM2)
                fw = 700 if bonus > 0 else 600
                mod_lbl.setStyleSheet(f"color:{fg};font-size:{FS_SMALL}px;font-weight:{fw};background:transparent;")
        # Store selection
        vals = {ab: sp.value() for ab, sp in self._asi_spins.items() if sp.value() > 0}
        self._selected = [f"asi:{ab}:{v}" for ab, v in vals.items()]
        # Auto-confirm when points filled
        if total == max_pts:
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], list(self._selected))

    def _on_feat_pick(self, name):
        if name != "— Choose Feat —":
            self._selected = [f"feat:{name}"]
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], [f"feat:{name}"])


    # ── Subclass chooser ──────────────────────────────────────────────
    def _build_subclass_chooser(self):
        pool = self.choice_info.get("pool", [])
        if not pool:
            self._lay.addWidget(_lbl("No subclasses available.", TEXT3, size=FS_BODY))
            return
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMaximumHeight(240)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:6px;}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(inner); vl.setSpacing(3); vl.setContentsMargins(8,6,8,6)
        self._sub_btn_group = QButtonGroup(self)
        for i, sub in enumerate(pool):
            rb = QRadioButton(sub)
            rb.setStyleSheet(f"QRadioButton{{color:{TEXT};font-size:{FS_BODY}px;padding:3px 0;}}")
            if sub in self._selected: rb.setChecked(True)
            rb.toggled.connect(lambda checked, s=sub: self._on_sub_radio(s, checked))
            self._sub_btn_group.addButton(rb, i)
            vl.addWidget(rb)
        scroll.setWidget(inner)
        self._lay.addWidget(scroll)

    def _on_sub_radio(self, sub_name, checked):
        if checked:
            self._selected = [sub_name]
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], [sub_name])

    # ── Invocation chooser ────────────────────────────────────────
    def _build_metamagic_chooser(self):
        """Larger-text chooser for Metamagic, Elemental Disciplines, etc."""
        pool = self.choice_info.get("pool") or []
        if not pool:
            # Generate from invocation list if no pool (shouldn't happen but safe)
            from dnd_app.data.classes import ELDRITCH_INVOCATIONS
            pool = ELDRITCH_INVOCATIONS
        self._skill_cbs = {}
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:6px;}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(inner); vl.setSpacing(6); vl.setContentsMargins(8,8,8,8)
        for opt in pool:
            # Split on – or — to get name + description
            if "–" in opt:
                name,desc = opt.split("–",1)
            elif "—" in opt:
                name,desc = opt.split("—",1)
            else:
                name,desc = opt, ""
            name=name.strip(); desc=desc.strip()
            cb = QCheckBox(name)
            cb.setStyleSheet(
                f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;font-weight:600;padding:4px;}}"
                f"QCheckBox::indicator{{width:18px;height:18px;border-radius:4px;"
                f"border:2px solid {BORDER2};background:{SURF2};}}"
                f"QCheckBox::indicator:checked{{background:{TEAL};border-color:{TEAL2};}}"
            )
            if opt in self._selected or name in self._selected:
                cb.setChecked(True)
            if desc:
                cb.setToolTip(f"<b>{name}</b><br>{desc}")
            cb.stateChanged.connect(lambda s, v=opt: self._on_check(v, s))
            self._skill_cbs[opt] = cb
            vl.addWidget(cb)
            if desc:
                dl = _lbl(f"  {desc[:80]}{'…' if len(desc)>80 else ''}", TEXT3, FS_SMALL, wrap=True)
                vl.addWidget(dl)
        vl.addStretch()
        scroll.setWidget(inner)
        self._lay.addWidget(scroll, 1)

    def _build_invocation_chooser(self):
        from dnd_app.data.classes import ELDRITCH_INVOCATIONS
        search = QLineEdit(); search.setPlaceholderText(f"Search invocations… ({self._count} required)")
        search.setStyleSheet(f"border:1px solid {BORDER};border-radius:4px;padding:3px 6px;background:{BG};color:{TEXT};")
        self._lay.addWidget(search)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMaximumHeight(180)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:4px;}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(inner); vl.setSpacing(2); vl.setContentsMargins(4,4,4,4)
        self._inv_cbs = {}

        for inv in ELDRITCH_INVOCATIONS:
            cb = QCheckBox(inv)
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;}}QCheckBox::indicator{{width:18px;height:18px;}}")
            cb.setChecked(inv in self._selected)
            cb.stateChanged.connect(lambda s, v=inv: self._on_check(v, s))
            vl.addWidget(cb)
            self._inv_cbs[inv] = cb

        def _filter(text):
            for v, cb in self._inv_cbs.items():
                cb.setVisible(not text or text.lower() in v.lower())
        search.textChanged.connect(_filter)
        scroll.setWidget(inner)
        self._lay.addWidget(scroll)
        self._status = _lbl(self._status_text(), TEXT2, size=FS_SMALL)
        self._lay.addWidget(self._status)
        # Alias skill_cbs so _on_check works
        self._skill_cbs = self._inv_cbs

    # ── Battle Master maneuver chooser ────────────────────────────
    def _build_maneuver_chooser(self):
        from dnd_app.data.classes import BATTLE_MASTER_MANEUVERS
        from dnd_app.core.calculator import get_superiority_die
        import re as _re_sd
        sd = get_superiority_die(self.char)
        search = QLineEdit(); search.setPlaceholderText(f"Search maneuvers… ({self._count} required)")
        search.setStyleSheet(f"border:1px solid {BORDER};border-radius:4px;padding:3px 6px;background:{BG};color:{TEXT};")
        self._lay.addWidget(search)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMaximumHeight(180)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:4px;}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(inner); vl.setSpacing(2); vl.setContentsMargins(4,4,4,4)
        self._maneuver_cbs = {}

        for m in BATTLE_MASTER_MANEUVERS:
            m = _re_sd.sub(r'\bSD\b', sd, m)
            cb = QCheckBox(m)
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_BODY}px;}}QCheckBox::indicator{{width:18px;height:18px;}}")
            cb.setChecked(m in self._selected)
            cb.stateChanged.connect(lambda s, v=m: self._on_check(v, s))
            vl.addWidget(cb)
            self._maneuver_cbs[m] = cb

        def _filter(text):
            for v, cb in self._maneuver_cbs.items():
                cb.setVisible(not text or text.lower() in v.lower())
        search.textChanged.connect(_filter)
        scroll.setWidget(inner)
        self._lay.addWidget(scroll)
        self._status = _lbl(self._status_text(), TEXT2, size=FS_SMALL)
        self._lay.addWidget(self._status)
        self._skill_cbs = self._maneuver_cbs

    # ── Artificer Infusion chooser ────────────────────────────────
    def _build_infusion_chooser(self):
        from dnd_app.data.classes import ARTIFICER_INFUSIONS
        from dnd_app.core.calculator import get_infusion_min_level, class_levels
        art_lvl = class_levels(self.char).get("Artificer", 0)
        # Only shows infusions the character actually qualifies for by
        # level — e.g. Arcane Propulsion Armor requires 14th level and
        # shouldn't be selectable at 1st.
        eligible_infusions = [inf for inf in ARTIFICER_INFUSIONS
                              if get_infusion_min_level(inf) <= art_lvl]
        search = QLineEdit()
        search.setPlaceholderText(f"Search infusions… (choose {self._count})")
        search.setStyleSheet(f"border:1px solid {BORDER};border-radius:4px;padding:3px 6px;background:{BG};color:{TEXT};")
        self._lay.addWidget(search)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMaximumHeight(200)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:4px;}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(inner); vl.setSpacing(2); vl.setContentsMargins(4,4,4,4)
        from dnd_app.data.magic_items import get_magic_item
        self._inf_cbs = {}
        for inf in eligible_infusions:
            cb = QCheckBox(inf)
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_SMALL}px;}}QCheckBox::indicator{{width:14px;height:14px;}}")
            cb.setChecked(inf in self._selected)
            # Full official description from the magic item catalog —
            # the checkbox label itself is only this data file's own
            # short summary, not the complete item text already
            # available in the magic item browser.
            base_name = inf.split(" – ")[0].strip()
            lookup_name = base_name.split(" (+")[0].strip()
            catalog_entry = get_magic_item(lookup_name) or get_magic_item(base_name)
            if catalog_entry and catalog_entry.get("desc"):
                cb.setToolTip(catalog_entry["desc"])
            cb.stateChanged.connect(lambda s, v=inf: self._on_check(v, s))
            vl.addWidget(cb)
            self._inf_cbs[inf] = cb
        def _filt(text):
            for v, cb in self._inf_cbs.items():
                cb.setVisible(not text or text.lower() in v.lower())
        search.textChanged.connect(_filt)
        scroll.setWidget(inner); self._lay.addWidget(scroll)
        self._status = _lbl(self._status_text(), TEXT2, size=FS_SMALL)
        self._lay.addWidget(self._status)
        self._skill_cbs = self._inf_cbs

    # ── Magical Secrets spell chooser ─────────────────────────────
    def _build_spell_chooser_generic(self):
        from dnd_app.data.spells import ALL_SPELLS
        # Restrict to choice_info["pool"] when provided (e.g. Blessed
        # Warrior/Druidic Warrior's specific cantrip list) — falls back to
        # every spell in the game when no pool is given, preserving the
        # original behavior for Magical Secrets, which legitimately wants
        # spells from any class.
        pool_names = self.choice_info.get("pool")
        spell_list = ([s for s in ALL_SPELLS if s["name"] in pool_names]
                      if pool_names else ALL_SPELLS)
        top = QHBoxLayout()
        self._ms_search = QLineEdit(); self._ms_search.setPlaceholderText("Search spells…")
        self._ms_lvl_f = QComboBox()
        self._ms_lvl_f.addItem("All Levels")
        for i in range(10): self._ms_lvl_f.addItem("Cantrip" if i==0 else f"Level {i}")
        top.addWidget(self._ms_search, 2); top.addWidget(self._ms_lvl_f)
        self._lay.addLayout(top)

        self._ms_list = QListWidget()
        self._ms_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self._ms_list.setMaximumHeight(180)
        self._ms_list.setStyleSheet(
            f"QListWidget{{background:{BG};border:1px solid {BORDER};}}"
            f"QListWidget::item{{padding:4px 8px;border-bottom:1px solid {BORDER};color:{TEXT};}}"
            f"QListWidget::item:selected{{background:{INDIGO};color:white;}}")

        for s in spell_list:
            lvl_txt = "Ctrp" if s["level"]==0 else f"L{s['level']}"
            item = QListWidgetItem(f"{lvl_txt:4s}  {s['name']}  [{s['school'][:3]}]")
            item.setData(Qt.UserRole, s["name"])
            self._ms_list.addItem(item)
            if s["name"] in self._selected:
                item.setSelected(True)

        def _filter():
            q = self._ms_search.text().lower()
            lvl = self._ms_lvl_f.currentText()
            for i in range(self._ms_list.count()):
                it = self._ms_list.item(i)
                name = it.data(Qt.UserRole) or ""
                ok = not q or q in name.lower()
                if lvl != "All Levels":
                    from dnd_app.data.spells import get_spell
                    sp = get_spell(name)
                    ok = ok and sp and ((lvl=="Cantrip" and sp["level"]==0) or
                                        (lvl.startswith("Level") and sp["level"]==int(lvl[-1])))
                it.setHidden(not ok)
        self._ms_search.textChanged.connect(_filter)
        self._ms_lvl_f.currentTextChanged.connect(_filter)
        self._ms_list.itemSelectionChanged.connect(self._on_ms_change)
        self._lay.addWidget(self._ms_list)
        self._status = _lbl(self._status_text(), TEXT2, size=FS_SMALL)
        self._lay.addWidget(self._status)

    def _on_ms_change(self):
        sel = [self._ms_list.item(i).data(Qt.UserRole)
               for i in range(self._ms_list.count())
               if self._ms_list.item(i).isSelected()]
        if len(sel) > self._count:
            # Deselect the last-added one
            for i in range(self._ms_list.count()-1,-1,-1):
                it = self._ms_list.item(i)
                if it.isSelected() and it.data(Qt.UserRole) not in self._selected:
                    it.setSelected(False); break
            return
        self._selected = sel
        self._update_status()
        if len(sel) == self._count:
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], sel)

    # ── Generic check handler (skills, invocations, maneuvers) ────
    def _on_check(self, value, state):
        cbs = getattr(self, '_skill_cbs', getattr(self, '_inv_cbs', getattr(self, '_maneuver_cbs', {})))
        if bool(state):  # stateChanged emits int 2=checked; Qt.Checked enum != int in PySide6
            if value not in self._selected:
                if len(self._selected) >= self._count:
                    # Remove the oldest, uncheck its checkbox
                    oldest = self._selected.pop(0)
                    if oldest in cbs and cbs[oldest] is not None:
                        cbs[oldest].blockSignals(True)
                        cbs[oldest].setChecked(False)
                        cbs[oldest].blockSignals(False)
                self._selected.append(value)
        else:
            if value in self._selected:
                self._selected.remove(value)
        
        self._update_status()
        # Update confirm button
        if self._confirm_btn:
            ready = len(self._selected) >= self._count
            self._confirm_btn.setEnabled(ready)
            txt = (f"✓  Confirm Selection  ({len(self._selected)}/{self._count})"
                   if ready else f"Confirm  ({len(self._selected)}/{self._count} selected)")
            self._confirm_btn.setText(txt)
        # Auto-confirm single-count choices
        if self._count == 1 and len(self._selected) == 1:
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], list(self._selected))

    def _on_confirm(self):
        if len(self._selected) >= self._count:
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], list(self._selected))

    def _set_confirmed(self):
        self._confirmed = True
        self._done_lbl.setVisible(True)
        if self._confirm_btn:
            self._confirm_btn.setVisible(False)

    def _update_status(self):
        text = self._status_text()
        color = TEAL2 if len(self._selected) >= self._count else TEXT2
        if hasattr(self, '_status'):
            self._status.setText(text)
            self._status.setStyleSheet(f"color:{color};font-size:{FS_SMALL}px;")

    def _status_text(self):
        n = len(self._selected)
        if n >= self._count: return f"✓  {n}/{self._count} — ready, click Confirm!"
        return f"Need {self._count - n} more  ({n}/{self._count})"


# ═══════════════════════════════════════════════════════════════════
#  GRANTS SUMMARY
# ═══════════════════════════════════════════════════════════════════
class GrantsSummaryWidget(QFrame):
    def __init__(self, char, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {BORDER};border-radius:6px;}}")
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(10, 8, 10, 8)
        self._outer.setSpacing(3)
        self._build_content(char)

    def _build_content(self, char):
        """Rebuild the auto-applied and pending choices sections."""
        while self._outer.count():
            item = self._outer.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        grants = char.get("_grants", {})
        race = char.get("species") or char.get("race","")
        bg = char.get("background","")
        classes = char.get("classes",[])

        self._outer.addWidget(_lbl("AUTO-APPLIED", GOLD, bold=True, size=FS_SMALL))

        rows = []
        asi = grants.get("asi",{})
        asi_parts = [f"{ab} +{v}" for ab,v in asi.items() if v != 0]
        if race: rows.append((race[:12], ", ".join(asi_parts) if asi_parts else "No ASI", TEAL2))
        if bg:
            bg_skills = get_background_skills(bg)
            if bg_skills: rows.append((bg[:12], f"Skills: {', '.join(bg_skills)}", GOLD))
        race_skills = get_race_skills(race) if race else []
        if race_skills: rows.append((race[:12], f"Auto-skill: {', '.join(race_skills)}", TEAL2))
        save_profs = sorted(grants.get("save_profs",set()))
        if classes and save_profs:
            rows.append((classes[0].get("class","")[:8], f"Saves: {', '.join(save_profs)}", IND2))
        if char.get("_paladin_aura"):
            cha_mod = (char["abilities"].get("CHA",10)-10)//2
            rows.append(("Paladin", f"Aura: +{max(1,cha_mod)} to ALL saves", PURP2))
        if char.get("_jack_of_all_trades"):
            rows.append(("Bard", "Jack of All Trades: +½ prof to non-prof skills", IND2))
        if char.get("_reliable_talent"):
            rows.append(("Rogue", "Reliable Talent: prof. check min roll = 10", CRIM2))
        if char.get("monk_speed_bonus",0) > 0:
            rows.append(("Monk", f"Unarmored Movement: +{char['monk_speed_bonus']} ft speed", TEAL2))

        if not rows:
            self._outer.addWidget(_lbl("Pick race, background, and class to see grants.", TEXT3, size=FS_SMALL))
            return

        for source, desc, color in rows:
            row_frame = QFrame(); row_frame.setStyleSheet("background:transparent;")
            rl = QHBoxLayout(row_frame); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
            badge = _lbl(source, "white", bold=True, size=FS_TINY, align=Qt.AlignCenter, wrap=False)
            badge.setFixedHeight(16)
            badge.setStyleSheet(f"color:white;font-size:{FS_TINY}px;font-weight:700;background:{color};"
                                f"border-radius:8px;padding:1px 6px;")
            rl.addWidget(badge)
            rl.addWidget(_lbl(desc, TEXT2, size=FS_BODY))
            rl.addStretch()
            self._outer.addWidget(row_frame)


# ═══════════════════════════════════════════════════════════════════
#  LEVEL-UP PANEL
# ═══════════════════════════════════════════════════════════════════
def feat_prereq_met(char: dict, feat: dict) -> tuple[bool, str]:
    """Checks a feat's actual prerequisite against the character's real
    data. Confirmed this had zero enforcement anywhere before — every
    feat was shown regardless of prereq, with the prereq text only ever
    appearing in a tooltip. Returns (met, reason_if_not_met).
    Campaign-specific prereqs (Planescape/Dragonlance) are left
    unenforced — the app has no way to know which campaign a table is
    using, so those stay informational only."""
    prereq = feat.get("prereq", "")
    if not prereq:
        return True, ""
    if not char.get("optional_rules", {}).get("feat_prereqs", True):
        return True, ""
    from dnd_app.core.calculator import total_level, ability_score

    # Ability score minimums, e.g. "DEX 13+", "INT or WIS 13+"
    import re
    m = re.match(r"^((?:STR|DEX|CON|INT|WIS|CHA)(?:\s+or\s+(?:STR|DEX|CON|INT|WIS|CHA))*)\s+(\d+)\+$", prereq)
    if m:
        abs_needed = re.findall(r"STR|DEX|CON|INT|WIS|CHA", m.group(1))
        threshold = int(m.group(2))
        if any(ability_score(char, ab) >= threshold for ab in abs_needed):
            return True, ""
        return False, prereq

    # Armor/weapon proficiency
    if "Prof. medium armor" in prereq:
        return ("Medium" in char.get("armor_proficiencies", []), prereq)
    if "Prof. heavy armor" in prereq:
        return ("Heavy" in char.get("armor_proficiencies", []), prereq)
    if "Prof. light armor" in prereq:
        return ("Light" in char.get("armor_proficiencies", []), prereq)
    if "Prof. martial weapon" in prereq:
        return (bool(char.get("weapon_proficiencies")) and
                any("Martial" in w for w in char.get("weapon_proficiencies", [])), prereq)

    # Spellcasting / Pact Magic
    if prereq in ("Spellcasting", "Spellcasting or Pact Magic"):
        has_spells = any(c.get("class") in
            ("Bard", "Cleric", "Druid", "Paladin", "Ranger", "Sorcerer", "Warlock", "Wizard", "Artificer")
            for c in char.get("classes", []))
        return (has_spells, prereq)

    # Level minimums (e.g. "4th level, X") — check the level part; the
    # named prior-feat part (if any) is checked separately below.
    lvl_m = re.match(r"^(\d+)(?:st|nd|rd|th) level", prereq)
    if lvl_m and total_level(char) < int(lvl_m.group(1)):
        return False, prereq

    # Previous-feat chains, e.g. "4th level, Scion of the Outer Planes
    # (lawful plane)" — check the base feat name is already known
    # (ignoring the specific sub-choice in parens, since the app doesn't
    # track that level of detail for these chain feats).
    for known_feat in ("Scion of the Outer Planes", "Strike of the Giants", "Squire of Solamnia",
                        "Initiate of High Sorcery", "Strixhaven Initiate"):
        if known_feat in prereq and known_feat != feat.get("name"):
            if known_feat not in char.get("feats", []):
                return False, prereq

    # Race-specific — includes subrace parenthetical matching, e.g.
    # "Elf (drow)", "Elf (high)", "Elf (wood)", "Gnome (deep)".
    race = (char.get("species") or char.get("race", "")).lower()
    subrace = char.get("subrace", "").lower()
    RACE_PREREQS = {
        "Halfling": ["halfling"],
        "Dragonborn": ["dragonborn"],
        "Elf (drow)": ["drow"],
        "Dwarf": ["dwarf"],
        "Elf or Half-Elf": ["elf", "half-elf"],
        "Gnome": ["gnome"],
        "Elf (high)": ["high elf", "elf"],  # "elf" alone with subrace check below
        "Tiefling": ["tiefling"],
        "Half-Orc": ["half-orc"],
        "Prodigy": None,  # handled specially below (multi-race OR)
        "Dwarf or a Small race": ["dwarf", "gnome", "halfling"],
        "Gnome (deep)": ["deep gnome", "gnome"],
        "Elf (wood)": ["wood elf", "elf"],
        "Elf": ["elf"],
    }
    if prereq == "Half-Elf, Half-Orc, or Human":
        ok = any(r in race for r in ("half-elf", "half-orc", "human"))
        return (ok, prereq)
    if prereq in RACE_PREREQS and RACE_PREREQS[prereq] is not None:
        needles = RACE_PREREQS[prereq]
        # Parenthetical subrace variants need the subrace to match too,
        # not just the base race (e.g. Drow specifically, not any elf).
        if "(" in prereq:
            sub_needle = prereq.split("(")[1].rstrip(")").lower()
            ok = sub_needle in subrace or sub_needle in race
        else:
            ok = any(n in race for n in needles)
        return (ok, prereq)

    # Anything else (campaign-specific, "No other dragonmark", etc.) —
    # left unenforced, same as before.
    return True, ""


class LevelUpPanel(QWidget):
    choices_changed = Signal()

    def __init__(self, char_ref, parent=None):
        super().__init__(parent)
        from dnd_app.ui.theme import sync_globals as _sg; _sg(globals())
        self.char = char_ref
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0,0,0,0)
        self._outer.setSpacing(8)

        self._grants = GrantsSummaryWidget(char_ref)
        self._outer.addWidget(self._grants)

        # ── Features timeline ─────────────────────────────────────────────
        self._features_hdr = _lbl("CLASS FEATURES BY LEVEL", IND2, bold=True, size=FS_LABEL)
        self._outer.addWidget(self._features_hdr)
        feat_scroll = QScrollArea(); feat_scroll.setWidgetResizable(True)
        feat_scroll.setMaximumHeight(340)
        feat_scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:6px;}}")
        feat_inner = QWidget(); feat_inner.setStyleSheet(f"background:{BG};")
        self._features_lay = QVBoxLayout(feat_inner)
        self._features_lay.setSpacing(2); self._features_lay.setContentsMargins(6,4,6,4)
        feat_scroll.setWidget(feat_inner)
        self._outer.addWidget(feat_scroll)

        self._pending_hdr = _lbl("CHOICES FOR THIS CHARACTER", AMBER, bold=True, size=FS_HEAD)
        self._outer.addWidget(self._pending_hdr)

        self._choices_scroll = QScrollArea()
        self._choices_scroll.setWidgetResizable(True)
        self._choices_scroll.setMinimumHeight(200)
        self._choices_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._choices_scroll.setStyleSheet(
            f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:8px;}}"
        )
        self._choices_inner = QWidget()
        self._choices_inner.setStyleSheet(f"background:{BG};")
        self._choices_vl = QVBoxLayout(self._choices_inner)
        self._choices_vl.setSpacing(8)
        self._choices_vl.setContentsMargins(8, 8, 8, 8)
        self._choices_scroll.setWidget(self._choices_inner)
        self._outer.addWidget(self._choices_scroll, 1)

        self._no_choices = _lbl("✓  No pending choices — character fully configured.", TEAL2, size=FS_BODY)
        self._outer.addWidget(self._no_choices)
        self._refreshing = False
        self._choice_widgets = []
        self.refresh()

    def _refresh_features(self):
        """Rebuild the class features timeline."""
        from dnd_app.data.classes import CLASS_DICT
        from dnd_app.data.classes_2024 import CLASS_DICT_2024
        while self._features_lay.count():
            item = self._features_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        edition = self.char.get("edition", "2014")
        D = CLASS_DICT_2024 if edition == "2024" else CLASS_DICT
        classes = self.char.get("classes", [])
        CLS_COLORS = [IND2, PURP2, AMBE2, TEAL2, CRIM2, GOLD2]
        total_lvl = sum(c.get("level", 0) for c in classes)
        for ci, c in enumerate(classes):
            cname = c.get("class", ""); clvl = c.get("level", 1); sub = c.get("subclass", "")
            color = CLS_COLORS[ci % len(CLS_COLORS)]
            cdata = D.get(cname, {})
            feats_map = cdata.get("features", {}); choices_map = cdata.get("level_choices", {})
            hdr = QLabel(f"{cname}" + (f" — {sub}" if sub else "") + f"  (Lv {clvl})  [Total Lv {total_lvl}]")
            hdr.setStyleSheet(f"color:{color};font-size:{FS_BODY}px;font-weight:700;background:{SURF2};"                              f"border-left:3px solid {color};padding:4px 8px;border-radius:3px;")
            hdr.setWordWrap(True)
            self._features_lay.addWidget(hdr)
            for lvl in range(1, clvl + 1):
                fl = feats_map.get(lvl, []); cl = choices_map.get(lvl, [])
                if not fl and not cl: continue
                for fname in fl:
                    row = QHBoxLayout(); row.setSpacing(6); row.setContentsMargins(8,1,4,1)
                    badge = QLabel(f"L{lvl}"); badge.setFixedWidth(26)
                    badge.setStyleSheet(f"color:{qa(color,0x55)};font-size:{FS_TINY}px;font-weight:700;background:transparent;")
                    badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    lbl = QLabel(f"▸ {resolve_stat_placeholders(fname, self.char)}")
                    lbl.setWordWrap(True)
                    lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;background:transparent;")
                    row.addWidget(badge); row.addWidget(lbl, 1)
                    w = QWidget(); w.setStyleSheet("background:transparent;"); w.setLayout(row)
                    self._features_lay.addWidget(w)
                for ch in cl:
                    row = QHBoxLayout(); row.setSpacing(6); row.setContentsMargins(8,1,4,1)
                    badge = QLabel(f"L{lvl}"); badge.setFixedWidth(26)
                    badge.setStyleSheet(f"color:{qa(AMBE2,0x55)};font-size:{FS_TINY}px;font-weight:700;background:transparent;")
                    badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    lbl = QLabel(f"⚙ {ch}"); lbl.setWordWrap(True)
                    lbl.setStyleSheet(f"color:{AMBE2};font-size:{FS_SMALL}px;background:transparent;")
                    row.addWidget(badge); row.addWidget(lbl, 1)
                    w = QWidget(); w.setStyleSheet("background:transparent;"); w.setLayout(row)
                    self._features_lay.addWidget(w)

    def refresh(self, char=None):
        """Refresh the level-up panel from the current character state."""
        if char is not None:
            self.char = char          # accept a new char ref when explicitly passed
        if getattr(self, '_refreshing', False):
            return
        self._refreshing = True
        try:
            self._do_refresh()        # handles grants + features + pending choices
        finally:
            self._refreshing = False

    def _do_refresh(self):
        while self._choices_vl.count():
            item = self._choices_vl.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)   # detach immediately so findChildren won't see it
                w.deleteLater()
        self._choice_widgets = []   # authoritative list of current widgets

        self._grants._build_content(self.char)
        self._refresh_features()

        pending = get_choices_needed(self.char)
        # Add subclass-conditional choices
        pending += _get_subclass_choices(self.char)
        # Add race proficiency choices
        pending += _get_race_choices(self.char)
        pending += _get_class_tool_choices(self.char)
        pending += _get_feat_choices(self.char)
        pending += _get_dm_reward_choices(self.char)
        pending += _get_optional_feature_choices(self.char)

        unfinished = [p for p in pending if len(p.get("already_chosen",[])) < p.get("count",1)]

        self._no_choices.setVisible(not unfinished)
        self._pending_hdr.setVisible(bool(unfinished))
        if unfinished:
            self._pending_hdr.setText(f"PENDING CHOICES  ({len(unfinished)} remaining)")

        min_h = max(120, min(480, 72 * len(pending) + 40))
        self._choices_scroll.setMinimumHeight(min_h)

        for choice_info in pending:
            w = ChoiceWidget(choice_info, self.char)
            w.setMinimumHeight(80)
            w.choice_confirmed.connect(self._on_confirmed)
            self._choices_vl.addWidget(w)
            self._choice_widgets.append(w)
        self._choices_vl.addStretch()

    def _on_confirmed(self, choice_id, selected):
        """Apply the choice to char dict and refresh."""
        # ── Skill proficiencies ────────────────────────────────────────────
        if choice_id.endswith("_skill_profs") or choice_id == "race_skill_profs":
            for skill in selected:
                if skill in self.char.get("skills",{}):
                    if self.char["skills"][skill] < 2:
                        self.char["skills"][skill] = 2
            self.char.setdefault("_choices",{})[choice_id] = selected
            # Aggregate into "class_skill_profs", the same way apply_choice()
            # does — this is what actually makes the choice re-derivable by
            # rebuild() later (e.g. after the Skills tab's "Reset Manual
            # Changes" button, or a delevel/relevel). Without this, a skill
            # choice made through this normal UI path had no persistent
            # record rebuild() could read back, even though it LOOKED
            # applied — it only worked because the raw skills dict was
            # never independently cleared anywhere.
            choices = self.char["_choices"]
            all_skill_profs = []
            for k, v in choices.items():
                if k.endswith("_skill_profs") and isinstance(v, list):
                    all_skill_profs.extend(v)
            choices["class_skill_profs"] = list(set(all_skill_profs))

        # ── Mixed skill-or-tool proficiencies (e.g. Skilled) ────────────────
        elif choice_id.endswith("_skill_or_tool_profs"):
            from dnd_app.data.items import ALL_TOOLS as _all_tools
            skill_names = set(ALL_SKILLS)
            skill_part = [s for s in selected if s in skill_names]
            for skill in skill_part:
                if skill in self.char.get("skills",{}) and self.char["skills"][skill] < 2:
                    self.char["skills"][skill] = 2
            self.char.setdefault("_choices",{})[choice_id] = selected
            choices = self.char["_choices"]
            all_skill_profs = []
            for k, v in choices.items():
                if (k.endswith("_skill_profs") or k.endswith("_skill_or_tool_profs")) and isinstance(v, list):
                    all_skill_profs.extend([x for x in v if x in skill_names])
            choices["class_skill_profs"] = list(set(all_skill_profs))
            all_tool_profs = []
            for k, v in choices.items():
                if (k.endswith("_tool_profs") or k.endswith("_skill_or_tool_profs")) and isinstance(v, list):
                    all_tool_profs.extend([x for x in v if x in _all_tools])
            choices["tool_profs"] = list(set(all_tool_profs))

        # ── Tool proficiencies ──────────────────────────────────────────────
        elif choice_id.endswith("_tool_profs"):
            self.char.setdefault("_choices",{})[choice_id] = selected
            # Aggregate into "tool_profs" — the exact key builder.py's
            # rebuild() reads from (char["tool_proficiencies"] =
            # grants["tool_profs"] + choices.get("tool_profs", [])) — so
            # this is re-derivable, same fix already applied to skills.
            choices = self.char["_choices"]
            all_tool_profs = []
            for k, v in choices.items():
                if k.endswith("_tool_profs") and isinstance(v, list):
                    all_tool_profs.extend(v)
            choices["tool_profs"] = list(set(all_tool_profs))

        # ── Expertise ─────────────────────────────────────────────────────
        elif "expertise" in choice_id:
            for skill in selected:
                self.char["skills"][skill] = 3
            self.char.setdefault("_choices",{})[choice_id] = selected
            # Same root-cause fix as "_skill_profs" above: aggregate into a
            # dedicated key so rebuild() can re-derive expertise choices
            # too, rather than relying entirely on the raw skills dict
            # never being independently cleared.
            choices = self.char["_choices"]
            all_expertise = []
            for k, v in choices.items():
                if "expertise" in k and isinstance(v, list):
                    all_expertise.extend(v)
            choices["class_skill_expertise"] = list(set(all_expertise))

        # ── Languages ─────────────────────────────────────────────────────
        elif "language" in choice_id or "bg_languages" in choice_id:
            langs = self.char.get("languages",["Common"])
            for lang in selected:
                if lang not in langs: langs.append(lang)
            self.char["languages"] = langs
            self.char.setdefault("_choices",{})[choice_id] = selected
            # Aggregate into "extra_languages" — the exact key builder.py's
            # rebuild() reads from (char["languages"] = grants["languages"]
            # + choices.get("extra_languages", [...])) — without this, any
            # language chosen here would be lost on the next rebuild.
            choices = self.char["_choices"]
            all_extra_langs = []
            for k, v in choices.items():
                if ("language" in k or k.endswith("_bg_languages")) and isinstance(v, list):
                    all_extra_langs.extend(v)
            choices["extra_languages"] = list(set(all_extra_langs))

        # ── ASI: store in _choices['asi_bonuses'] only, rebuild() applies ──

        elif choice_id.endswith("_asi_") or "asi_" in choice_id:
            # Store choice by its ID — rebuild() accumulates all ASI keys fresh
            self.char.setdefault("_choices", {})[choice_id] = selected
            # Handle feat selection
            for item in selected:
                if item.startswith("feat:"):
                    fname = item.split(":", 1)[1]
                    if fname not in self.char.get("feats", []):
                        self.char.setdefault("feats", []).append(fname)


        # ── Subclass ──────────────────────────────────────────────────────
        elif choice_id.endswith("_subclass"):
            cls_name = choice_id.replace("_subclass", "")
            sub_display = selected[0] if selected else ""
            if sub_display:
                from dnd_app.core.character import set_subclass
                set_subclass(self.char, cls_name, sub_display)
                self.char.setdefault("_choices", {})[choice_id] = selected
                # Also refresh subclass combos in sheet if possible
                if hasattr(self, '_sheet_ref'):
                    try: self._sheet_ref._populate_subclass_combo()
                    except: pass

        # ── Fighting Style ────────────────────────────────────────────────
        elif choice_id.endswith("_fighting_style"):
            fs = self.char.get("fighting_styles",[])
            for item in selected:
                if item not in fs: fs.append(item)
            self.char["fighting_styles"] = fs
            self.char.setdefault("_choices",{})[choice_id] = selected

        # ── Eldritch Invocations ──────────────────────────────────────────
        elif choice_id == "eldritch_invocations":
            self.char["eldritch_invocations"] = selected
            self.char.setdefault("_choices",{})[choice_id] = selected

        # ── Battle Master Maneuvers ───────────────────────────────────────
        elif choice_id.endswith("_maneuvers"):
            existing = self.char.get("battle_master_maneuvers",[])
            for m in selected:
                if m not in existing: existing.append(m)
            self.char["battle_master_maneuvers"] = existing
            self.char.setdefault("_choices",{})[choice_id] = selected

        # ── Magical Secrets ───────────────────────────────────────────────
        elif choice_id == "magical_secrets_spells":
            self.char["magical_secrets_spells"] = selected
            for sp in selected:
                if sp not in self.char.get("spells_known",[]):
                    self.char.setdefault("spells_known",[]).append(sp)
            self.char.setdefault("_choices",{})[choice_id] = selected

        elif choice_id == "artificer_infusions":
            new_selected = set(selected)
            prev_selected = set(self.char.get("artificer_infusions", []))
            self.char["artificer_infusions"] = selected
            self.char.setdefault("_choices", {})[choice_id] = selected
            # Learning an infusion just adds it to your known
            # repertoire — "known" and "active" are different: you can
            # know far more infusions than you can have active at once
            # (active cap = half of known). Actually creating/enchanting
            # an item happens separately, via the Infusions tab or
            # right-clicking a weapon/armor/shield in the Equipment tab
            # — not automatically here. If an infusion is un-learned
            # (replaced at level-up) while still active on an item,
            # that active assignment is removed too, since you can no
            # longer maintain it.
            removed_names = {inf.split(" – ")[0].strip() for inf in (prev_selected - new_selected)}
            if removed_names:
                self.char["active_infusions"] = [
                    a for a in self.char.get("active_infusions", [])
                    if a.get("infusion") not in removed_names]

        elif choice_id.startswith("totem_") or choice_id == "land_terrain":
            # Totem/terrain single-pick stored in _choices
            self.char.setdefault("_choices", {})[choice_id] = selected

        elif choice_id == "sorcerer_metamagic":
            self.char.setdefault("_choices", {})[choice_id] = selected

        elif choice_id == "four_elements_disciplines":
            self.char.setdefault("_choices", {})[choice_id] = selected

        elif choice_id == "blood_hunter_curses":
            self.char.setdefault("_choices", {})[choice_id] = selected

        elif choice_id == "blood_hunter_mutagens":
            self.char.setdefault("_choices", {})[choice_id] = selected

        elif choice_id.startswith("bard_magical_secrets") or choice_id.startswith("bard_lore_secrets") or choice_id.startswith("mystic_arcanum_"):
            # Add chosen spells to spells_known
            for sp_name in selected:
                if sp_name not in self.char.get("spells_known", []):
                    self.char.setdefault("spells_known", []).append(sp_name)
            self.char.setdefault("_choices", {})[choice_id] = selected

        else:
            apply_choice(self.char, choice_id, selected)

        rebuild(self.char)
        self.choices_changed.emit()
        # Sheet observer handles refresh via ctrl.refresh() -> _levelup_panel.refresh()


# ── Subclass-conditional choices ─────────────────────────────────────────────
def _get_subclass_choices(char):
    """Extra choices that only appear for specific subclasses."""
    choices = []
    made = char.get("_choices",{})

    for c in char.get("classes",[]):
        cname = c.get("class","")
        clvl  = c.get("level",0)
        sub   = c.get("subclass","").lower()

        # Blood Hunter: Fighting Style (2nd level, core). Uses the
        # exact class-specific wording (e.g. Great Weapon Fighting
        # explicitly excludes rite damage dice, unlike other classes' version).
        if cname == "Blood Hunter" and clvl >= 2:
            key = "blood_hunter_fighting_style_2"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "class", "source_name": "Blood Hunter",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Archery – +2 to attack rolls with ranged weapons",
                             "Dueling – +2 damage with a one-handed melee weapon, wielding no other weapon",
                             "Great Weapon Fighting – reroll 1s and 2s on non-rite damage dice with a "
                             "two-handed/versatile melee weapon",
                             "Two-Weapon Fighting – add your ability modifier to the second attack's damage"],
                    "label": "Choose a Fighting Style (Blood Hunter Lv2)",
                    "already_chosen": already,
                })

        # Lunar Sorcery: Lunar Embodiment phase choice (1st level).
        # Re-chosen every long rest (handled via RestOptionsDialog) and,
        # from 6th level, via a bonus action for 1 sorcery point (Waxing
        # and Waning, handled as a combat action).
        if cname == "Sorcerer" and clvl >= 1 and "lunar" in sub:
            key = "lunar_phase"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "subclass", "source_name": "Lunar Embodiment",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Full Moon", "New Moon", "Crescent Moon"],
                    "label": "Choose your Lunar Embodiment phase (changeable on a long rest, "
                             "or as a bonus action for 1 sorcery point from 6th level)",
                    "already_chosen": already,
                })

        # Guidance of the Spirits (Bard, College of Spirits, 3rd level):
        # skill choice, swappable on long rest via RestOptionsDialog.
        if cname == "Bard" and clvl >= 3 and "spirits" in sub:
            key = "guidance_of_the_spirits_skill"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "subclass", "source_name": "Guidance of the Spirits",
                    "type": "skill_prof", "count": 1, "pool": ALL_SKILLS,
                    "label": "Choose a skill for Guidance of the Spirits (swappable on long rest)",
                    "already_chosen": already,
                })

        # Whispers of the Dead (Rogue, Phantom, 3rd level): skill-or-tool
        # choice, swappable on either rest type via RestOptionsDialog.
        if cname == "Rogue" and clvl >= 3 and "phantom" in sub:
            key = "whispers_of_the_dead_prof"
            already = made.get(key, [])
            if not already:
                from dnd_app.data.feature_ui_interactions import TOOLS as ALL_TOOLS
                choices.append({
                    "id": key, "source": "subclass", "source_name": "Whispers of the Dead",
                    "type": "skill_or_tool_prof", "count": 1, "pool": ALL_SKILLS + ALL_TOOLS,
                    "label": "Choose a skill or tool proficiency for Whispers of the Dead "
                             "(swappable on any rest)",
                    "already_chosen": already,
                })

        # Mystic Arcanum (Warlock, 11th/13th/15th/17th): choose one spell
        # of the corresponding level once each. Same kind of gap as
        # Eldritch Invocations and Pact Boon — genuinely missing.
        if cname == "Warlock":
            from dnd_app.data.spells import spells_for_class_at_level
            ARCANUM_LEVELS = {11: 6, 13: 7, 15: 8, 17: 9}
            for char_lvl, spell_lvl in ARCANUM_LEVELS.items():
                if clvl >= char_lvl:
                    key = f"mystic_arcanum_{spell_lvl}"
                    already = made.get(key, [])
                    if not already:
                        pool = [s["name"] for s in spells_for_class_at_level("Warlock", spell_lvl)]
                        choices.append({
                            "id": key,
                            "source": "class", "source_name": "Warlock",
                            "type": "magical_secrets", "count": 1,
                            "pool": pool,
                            "label": f"Mystic Arcanum: choose one {spell_lvl}th-level spell (Lv{char_lvl})",
                            "already_chosen": already,
                        })

        # Pact Boon (Warlock, 3rd level): single choice, same gap in kind
        # as Eldritch Invocations — no offering code existed at all.
        if cname == "Warlock" and clvl >= 3:
            key = "warlock_pact_boon"
            if key not in made:
                choices.append({
                    "id": key,
                    "source": "class", "source_name": "Warlock",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Pact of the Blade (summon a pact weapon)",
                             "Pact of the Chain (imp/quasit/pseudodragon/sprite familiar)",
                             "Pact of the Tome (Book of Shadows: 3 extra cantrips from any class, cast as rituals if the spell allows)",
                             "Pact of the Talisman (amulet: +1d4 to a failed ability check, uses = proficiency bonus per long rest)"],
                    "label": "Choose a Pact Boon",
                    "already_chosen": made.get(key, []),
                })

        # Pact of the Tome's 3 cantrips, from ANY class's spell list per the actual rule text.
        pact_choice = made.get("warlock_pact_boon", [])
        if cname == "Warlock" and clvl >= 3 and pact_choice and "tome" in pact_choice[0].lower():
            key = "pact_of_the_tome_cantrips"
            already = made.get(key, [])
            if len(already) < 3:
                from dnd_app.data.spells import ALL_SPELLS
                pool = sorted({s["name"] for s in ALL_SPELLS if s.get("level", 0) == 0})
                choices.append({
                    "id": key, "source": "class", "source_name": "Pact of the Tome",
                    "type": "magical_secrets", "count": 3,
                    "pool": pool,
                    "label": "Choose 3 cantrips from any class's spell list (Book of Shadows)",
                    "already_chosen": already,
                })

        # Book of Ancient Secrets (Eldritch Invocation, requires Pact of
        # the Tome): a separate invocation from Pact of the Tome itself,
        # granting 2 additional 1st-level ritual spells from any class's
        # list. Gated on the invocation actually being chosen, not just
        # the pact, since a Pact of the Tome warlock who hasn't taken
        # this specific invocation shouldn't get the ritual spells.
        known_invs_for_secrets = [i.split(" (")[0].strip() for i in char.get("eldritch_invocations", [])]
        if "Book of Ancient Secrets" in known_invs_for_secrets:
            key = "book_of_ancient_secrets_rituals"
            already = made.get(key, [])
            if len(already) < 2:
                from dnd_app.data.spells import ALL_SPELLS
                pool = sorted({s["name"] for s in ALL_SPELLS if s.get("level") == 1 and s.get("ritual")})
                choices.append({
                    "id": key, "source": "class", "source_name": "Book of Ancient Secrets",
                    "type": "magical_secrets", "count": 2,
                    "pool": pool,
                    "label": "Choose 2 1st-level ritual spells from any class's spell list (Book of Ancient Secrets)",
                    "already_chosen": already,
                })

        # Eldritch Invocations (Warlock, Core): a working chooser widget
        # and processing path already existed, but nothing ever offered
        # this choice — meaning no Warlock character could ever actually
        # select an invocation. Count scales 2/5/6/7/8/9/10 at Warlock
        # levels 2/5/7/10/12/15/18 (classes.py's own feature table).
        if cname == "Warlock" and clvl >= 2:
            inv_levels = [(2,2),(5,3),(7,4),(9,5),(12,6),(15,7),(18,8)]
            total_needed = max((n for lvl, n in inv_levels if clvl >= lvl), default=0)
            already = char.get("eldritch_invocations", [])
            remaining = max(0, total_needed - len(already))
            if remaining > 0:
                from dnd_app.data.classes import ELDRITCH_INVOCATIONS
                import re
                known_cantrips = char.get("cantrips_known", []) + char.get("spells_known", [])
                has_eldritch_blast = any("eldritch blast" in c.lower() for c in known_cantrips)
                pact_choice2 = made.get("warlock_pact_boon", [])
                pact_lower = pact_choice2[0].lower() if pact_choice2 else ""
                # This pool is filtered by the character's actual level
                # and pact boon, and excludes the 4 entries that are
                # Pact Boons, not invocations. "hex/curse feature" means
                # knowing the Hex spell, OR having a cursing Warlock
                # feature — Hexblade's Curse (an automatic level-1
                # feature of the Hexblade patron, so checking the
                # subclass name is reliable) or the Sign of Ill Omen
                # invocation.
                has_hex_curse = (any("hex" == s.lower() for s in known_cantrips + char.get("spells_known", []))
                                  or "hexblade" in sub.lower()
                                  or "Sign of Ill Omen" in [i.split(" (")[0].strip() for i in already])
                filtered_pool = []
                for inv in ELDRITCH_INVOCATIONS:
                    name_part = inv.split("–")[0].strip()
                    if name_part.startswith("Pact of the"):
                        continue
                    m = re.search(r'\(([^)]*)\)\s*$', name_part)
                    ok = True
                    if m:
                        req = m.group(1).lower()
                        lvl_m = re.match(r'(\d+)(st|nd|rd|th)', req)
                        if lvl_m and clvl < int(lvl_m.group(1)):
                            ok = False
                        if "pact of the blade" in req and "blade" not in pact_lower:
                            ok = False
                        if "pact of the chain" in req and "chain" not in pact_lower:
                            ok = False
                        if "pact of the tome" in req and "tome" not in pact_lower:
                            ok = False
                        if "pact of the talisman" in req and "talisman" not in pact_lower:
                            ok = False
                        if "eldritch blast" in req and not has_eldritch_blast:
                            ok = False
                        if "hex/curse" in req and not has_hex_curse:
                            ok = False
                    if ok:
                        filtered_pool.append(inv)
                choices.append({
                    "id": "eldritch_invocations",
                    "source": "class", "source_name": "Warlock",
                    "type": "invocation", "count": remaining,
                    "pool": filtered_pool,
                    "label": f"Choose {remaining} Eldritch Invocation(s)",
                    "already_chosen": already,
                })

        # Battle Master maneuvers
        if cname == "Fighter" and "battle master" in sub:
            maneuver_levels = [(3,3),(7,2),(10,2),(15,2),(18,2)]
            total_needed = sum(n for lvl, n in maneuver_levels if clvl >= lvl)
            already = char.get("battle_master_maneuvers", [])
            remaining = max(0, total_needed - len(already))
            if remaining > 0:
                choices.append({
                    "id": "fighter_maneuvers",
                    "source": "subclass", "source_name": "Battle Master",
                    "type": "maneuver", "count": remaining,
                    "pool": None,
                    "label": f"Choose {remaining} Battle Master maneuver(s)",
                    "already_chosen": already,
                })

        # Superior Technique fighting style (TCE): grants exactly 1
        # maneuver + 1 superiority die, independent of Battle Master
        # subclass — shares the same battle_master_maneuvers storage so a
        # Battle Master who also somehow had this wouldn't double-track,
        # though realistically this only ever fires for a non-Battle-
        # Master Fighter/Paladin/Ranger who picked this fighting style.
        if any("superior technique" in fs.lower() for fs in char.get("fighting_styles", [])):
            already_st = char.get("battle_master_maneuvers", [])
            # Superior Technique's own 1-maneuver allotment is tracked
            # against a fixed count of 1 rather than the Battle Master
            # progression table above, so it doesn't ask for more just
            # because a Battle Master Fighter later multiclassed in.
            if len(already_st) < 1 and "battle master" not in sub:
                choices.append({
                    "id": "fighter_maneuvers",
                    "source": "fighting_style", "source_name": "Superior Technique",
                    "type": "maneuver", "count": 1,
                    "pool": None,
                    "label": "Superior Technique: choose 1 maneuver",
                    "already_chosen": already_st,
                })

        # College of Lore Bard: 3rd-level Bonus Proficiencies — three skills
        # of your choice. Tracked as its own chooser since the subclass
        # feature list combines this with Cutting Words into one flavor
        # string that has no mechanism of its own to grant proficiencies.
        if cname == "Bard" and "lore" in sub and clvl >= 3:
            already = made.get("bard_lore_skill_profs", [])
            if len(already) < 3:
                choices.append({
                    "id": "bard_lore_skill_profs",
                    "source": "subclass", "source_name": "College of Lore",
                    "type": "skill_prof", "count": 3,
                    "pool": ALL_SKILLS,
                    "label": "Bonus Proficiencies (College of Lore): choose 3 skills",
                    "already_chosen": already,
                })

        # College of Swords: Fighting Style choice (Dueling or Two-Weapon
        # Fighting) — was never collected, so it never applied to the
        # actual weapon damage calculation despite that already
        # supporting these styles for Fighters/Rangers/Paladins.
        if cname == "Bard" and "swords" in sub and clvl >= 3:
            key = "bard_swords_fighting_style"
            if key not in made:
                choices.append({
                    "id": key,
                    "source": "subclass", "source_name": "College of Swords",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Dueling", "Two-Weapon Fighting"],
                    "label": "College of Swords: Choose a Fighting Style",
                    "already_chosen": made.get(key, []),
                })

        # Wild Magic Sorcerer / Barbarian: show surge table reference
        is_wild_magic = (
            (cname == "Sorcerer" or cname == "Barbarian") and
            "wild magic" in sub
        )
        if is_wild_magic and clvl >= 1:
            if "wild_magic_ack" not in made:
                choices.append({
                    "id": "wild_magic_ack",
                    "source": "subclass", "source_name": "Wild Magic",
                    "type": "info",
                    "count": 1,
                    "pool": None,
                    "label": "Wild Magic Surge: see the Features tab for the full d100 table",
                    "already_chosen": ["ack"],
                })

        # ── Ranger subclass choices ──────────────────────────────────────
        if cname == "Ranger":
            # Hunter: Colossus Slayer/Giant Killer/Horde Breaker at Lv3
            if "hunter" in sub and clvl >= 3:
                key = "hunter_prey_3"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",  # radio buttons work for single choice
                        "count": 1,
                        "pool": ["Colossus Slayer – once per turn, extra d8 damage to a damaged target",
                                 "Giant Killer – reaction attack on a Large+ creature within 5ft that hits OR misses you",
                                 "Horde Breaker – once per turn, attack a second creature within 5ft of your original target with the same weapon"],
                        "label": "Hunter: Choose Hunter's Prey (Lv3)",
                        "already_chosen": made.get(key, [])})
            # Hunter: Escape the Horde/Multiattack Defence/Steel Will at Lv7
            if "hunter" in sub and clvl >= 7:
                key = "hunter_defensive_7"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",
                        "count": 1,
                        "pool": ["Escape the Horde – opportunity attacks against you have disadvantage",
                                 "Multiattack Defense – +4 AC against further attacks from a creature that just hit you, rest of the turn",
                                 "Steel Will – advantage on saves against being frightened"],
                        "label": "Hunter: Choose Defensive Tactic (Lv7)",
                        "already_chosen": made.get(key, [])})
            # Hunter: Volley/Whirlwind Attack at Lv11
            if "hunter" in sub and clvl >= 11:
                key = "hunter_multiattack_11"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",
                        "count": 1,
                        "pool": ["Volley – ranged attack against any number of creatures within 10 ft of a point in range (ammo + separate roll per target)",
                                 "Whirlwind Attack – melee attack against any number of creatures within 5 ft (separate roll per target)"],
                        "label": "Hunter: Choose Multiattack (Lv11)",
                        "already_chosen": made.get(key, [])})
            # Hunter: Evasion/Stand Against the Tide/Uncanny Dodge at Lv15.
            if "hunter" in sub and clvl >= 15:
                key = "hunter_defense_15"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",
                        "count": 1,
                        "pool": ["Evasion – successful DEX save vs an area effect takes no damage instead of half; failed save takes half instead of full",
                                 "Stand Against the Tide – reaction: a hostile creature that misses you with a melee attack must repeat the attack against another creature of your choice",
                                 "Uncanny Dodge – reaction: halve the damage of an attack that hits you"],
                        "label": "Hunter: Choose Superior Hunter's Defense (Lv15)",
                        "already_chosen": made.get(key, [])})
            # Gloom Stalker: Umbral Sight, Dread Ambusher etc. — info only
            if "gloom" in sub and clvl >= 3:
                key = "gloom_stalker_ack"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Gloom Stalker",
                        "type": "info", "count": 1, "pool": None,
                        "label": "Gloom Stalker features active: Dread Ambusher, Umbral Sight, Iron Mind",
                        "already_chosen": ["ack"]})
            # Gloom Stalker Iron Mind (7th level): only a real choice if the
            # character is already proficient in WIS saves from elsewhere
            # (an unusual multiclass edge case) — otherwise Iron Mind just
            # grants WIS automatically (handled in builder.py, not here).
            if "gloom" in sub and clvl >= 7 and char.get("saving_throws", {}).get("WIS"):
                key = "gloom_stalker_iron_mind"
                if key not in made:
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Iron Mind", "type": "fighting_style",
                        "count": 1, "pool": ["INT", "CHA"],
                        "label": "Already proficient in WIS saves — choose INT or CHA instead (Iron Mind)",
                        "already_chosen": made.get(key, [])})
            # Beastmaster: companion pick
            if ("beast" in sub or "beastmaster" in sub.replace(" ","")) and clvl >= 3:
                key = "beastmaster_companion"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Beast Master",
                        "type": "info", "count": 1, "pool": None,
                        "label": "Choose a Medium or smaller beast as your companion (CR ≤ ¼)",
                        "already_chosen": ["ack"]})

        # Fighting Style
        if cname in ("Fighter","Paladin","Ranger"):
            min_lvl = 1 if cname == "Fighter" else 2
            if clvl >= min_lvl:
                key = f"{cname}_fighting_style"
                already = made.get(key,[])
                if not already:
                    pool = FIGHTING_STYLES.get(cname,[])
                    choices.append({
                        "id": key,
                        "source": "class", "source_name": cname,
                        "type": "fighting_style", "count": 1,
                        "pool": pool,
                        "label": f"Choose Fighting Style ({cname})",
                        "already_chosen": already,
                    })
                # Blessed Warrior (Paladin) and Druidic Warrior (Ranger)
                # each grant 2 cantrips from another class's list — a real
                # choice, not something with a sensible default, so it
                # only appears once that specific fighting style has
                # actually been picked.
                fs_pick = " ".join(already).lower()
                if "blessed warrior" in fs_pick or "druidic warrior" in fs_pick:
                    other_class = "Cleric" if "blessed warrior" in fs_pick else "Druid"
                    cantrip_key = f"{cname}_{other_class.lower()}_cantrips"
                    cantrip_already = made.get(cantrip_key, [])
                    if len(cantrip_already) < 2:
                        from dnd_app.data.spells import ALL_SPELLS
                        cantrips = sorted({s["name"] for s in ALL_SPELLS
                                           if s.get("level") == 0 and other_class in s.get("classes", [])})
                        choices.append({"id": cantrip_key, "source": "class",
                            "source_name": f"Blessed Warrior" if other_class=="Cleric" else "Druidic Warrior",
                            "type": "magical_secrets", "count": 2,
                            "pool": cantrips,
                            "label": f"Choose 2 {other_class} cantrips",
                            "already_chosen": cantrip_already})

        # ── Totem Warrior choices ─────────────────────────────────────────
        # Each tier (Totem Spirit at 3rd, Aspect of the Beast at 6th,
        # Totemic Attunement at 14th) has its own pool, since the same
        # animal grants a different, tier-specific benefit at each level —
        # Bear's Totem Spirit is a damage resistance, while Bear's Aspect
        # of the Beast is a carrying-capacity benefit, for example.
        if cname == "Barbarian" and "totem" in sub:
            TOTEM_SPIRIT_3 = [
                "Bear – while raging, resistance to all damage except psychic",
                "Eagle – while raging (and not wearing heavy armor), others have disadvantage on opportunity attacks against you, and you can Dash as a bonus action",
                "Elk – while raging (and not wearing heavy armor), your walking speed increases by 15 ft",
                "Tiger – while raging, add 10 ft to your long jump and 3 ft to your high jump",
                "Wolf – while raging, friends have advantage on melee attack rolls against any creature within 5 ft of you that's hostile to you",
            ]
            TOTEM_ASPECT_6 = [
                "Bear – carrying capacity (and max load/lift) doubled; advantage on STR checks to push/pull/lift/break objects",
                "Eagle – see up to 1 mile away with no difficulty; dim light doesn't impose disadvantage on Perception checks",
                "Elk – your travel pace (and up to 10 companions' within 60 ft) is doubled",
                "Tiger – proficiency in two of: Athletics, Acrobatics, Stealth, Survival",
                "Wolf – track creatures at a fast pace, and move stealthily at a normal pace",
            ]
            TOTEM_ATTUNEMENT_14 = [
                "Bear – while raging, hostile creatures within 5 ft have disadvantage on attacks against anyone but you (or another with this feature), unless immune to being frightened",
                "Eagle – while raging, flying speed equal to your walking speed (you fall if still aloft at end of turn with nothing else holding you up)",
                "Elk – while raging, bonus action during your move to barrel through a Large or smaller creature's space (STR save DC 8+STR+PB or be knocked prone + 1d12+STR bludgeoning)",
                "Tiger – while raging, after moving 20+ ft straight toward a Large or smaller target, bonus action for one extra melee attack against it",
                "Wolf – while raging, bonus action to knock a Large or smaller creature prone when you hit it with a melee weapon attack",
            ]
            totem_levels = [(3,"Choose Totem Spirit","totem_spirit_3", TOTEM_SPIRIT_3),
                           (6,"Choose Aspect of the Beast","totem_aspect_6", TOTEM_ASPECT_6),
                           (14,"Choose Totemic Attunement","totem_attune_14", TOTEM_ATTUNEMENT_14)]
            for lvl, label, key, pool in totem_levels:
                if clvl >= lvl and key not in made:
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Totem Warrior", "type": "fighting_style",
                        "count": 1, "pool": pool,
                        "label": f"{label} (Totem Warrior Lv{lvl})",
                        "already_chosen": made.get(key, [])})
            # Aspect of the Beast's Tiger option is itself a "choose 2 of 4
            # skills" pick (Athletics/Acrobatics/Stealth/Survival) — the
            # animal choice above just picks Tiger as flavor/mechanics
            # bundle, it doesn't grant any skill by itself. This nested
            # chooser only appears once Tiger has actually been selected,
            # and its id ends in "_skill_profs" so the existing generic
            # skill-proficiency-granting logic picks it up automatically.
            aspect_pick = made.get("totem_aspect_6", [])
            if clvl >= 6 and aspect_pick and "tiger" in " ".join(aspect_pick).lower():
                already_tiger_skills = made.get("totem_tiger_skill_profs", [])
                if len(already_tiger_skills) < 2:
                    choices.append({"id": "totem_tiger_skill_profs", "source": "subclass",
                        "source_name": "Aspect of the Beast (Tiger)", "type": "skill_prof",
                        "count": 2, "pool": ["Athletics","Acrobatics","Stealth","Survival"],
                        "label": "Choose 2 skills (Aspect of the Beast: Tiger)",
                        "already_chosen": already_tiger_skills})

        # ── Circle of the Land terrain choice (Druid) ─────────────────────────
        if cname == "Druid" and "land" in sub:
            if "land_terrain" not in made:
                terrains = ["Arctic","Coast","Desert","Forest","Grassland",
                            "Mountain","Swamp","Underdark"]
                choices.append({"id": "land_terrain", "source": "subclass",
                    "source_name": "Circle of the Land", "type": "fighting_style",
                    "count": 1, "pool": terrains,
                    "label": "Choose your Favored Terrain (Circle of the Land)",
                    "already_chosen": made.get("land_terrain", [])})

        # ── Way of the Four Elements: Elemental Disciplines (Monk) ────────────
        if cname == "Monk" and "four elements" in sub:
            # Elemental Attunement is automatic ("You know the Elemental
            # Attunement discipline AND one other...") so it isn't in this
            # pickable pool at all — only the "one other" (and later
            # additional) discipline choices count against the known total.
            DISCIPLINES = [
                "Breath of Winter (17th+) – spend 6 ki to cast Cone of Cold",
                "Clench of the North Wind (6th+) – spend 3 ki to cast Hold Person",
                "Eternal Mountain Defense (17th+) – spend 5 ki to cast Stoneskin on yourself",
                "Fangs of the Fire Snake – spend 1 ki: unarmed reach +10ft this turn, hits deal fire not bludgeoning; spend 1 more ki on a hit for +1d10 fire",
                "Fist of Four Thunders – spend 2 ki to cast Thunderwave",
                "Fist of Unbroken Air – spend 2 ki (+1d10 dmg per extra ki): target STR save or 3d10+ bludgeoning, pushed 20ft & prone (half dmg, no push/prone on save)",
                "Flames of the Phoenix (11th+) – spend 4 ki to cast Fireball",
                "Gong of the Summit (6th+) – spend 3 ki to cast Shatter",
                "Mist Stance (11th+) – spend 4 ki to cast Gaseous Form on yourself",
                "Ride the Wind (11th+) – spend 4 ki to cast Fly on yourself",
                "River of Hungry Flame (17th+) – spend 5 ki to cast Wall of Fire",
                "Rush of the Gale Spirits – spend 2 ki to cast Gust of Wind",
                "Shape the Flowing River – spend 1 ki: reshape/move up to a 30ft-cube area of ice or water within 120ft",
                "Sweeping Cinder Strike – spend 2 ki to cast Burning Hands",
                "Water Whip – spend 2 ki (+1d10 dmg per extra ki): target DEX save or 3d10+ bludgeoning, knocked prone or pulled 25ft (half dmg, no prone/pull on save)",
                "Wave of Rolling Earth (17th+) – spend 6 ki to cast Wall of Stone",
            ]
            # Real progression: "one other" at 3rd, "one additional" at 6th/
            # 11th/17th — i.e. 1/2/3/4 CHOSEN disciplines at those levels
            # (Elemental Attunement itself doesn't count toward this, since
            # it's free).
            KNOWN_BY_LEVEL = {3: 1, 6: 2, 11: 3, 17: 4}
            known = max((v for lvl, v in KNOWN_BY_LEVEL.items() if clvl >= lvl), default=0)
            already = char.get("_choices", {}).get("four_elements_disciplines", [])
            if clvl >= 3 and len(already) < known:
                choices.append({"id": "four_elements_disciplines", "source": "subclass",
                    "source_name": "Four Elements", "type": "metamagic",
                    "count": known, "pool": DISCIPLINES,
                    "label": f"Choose {known} Elemental Disciplines",
                    "already_chosen": already})

        # ── Bard: Magical Secrets ──────────────────────────────────────────────
        if cname == "Bard":
            MS_LEVELS = {10: 2, 14: 4, 18: 6}
            for ms_lvl, total_count in sorted(MS_LEVELS.items()):
                if clvl >= ms_lvl:
                    key = f"bard_magical_secrets_{ms_lvl}"
                    already = char.get("_choices", {}).get(key, [])
                    batch_count = 2  # each threshold grants 2 more
                    if len(already) < batch_count:
                        choices.append({"id": key, "source": "class",
                            "source_name": "Bard", "type": "magical_secrets",
                            "count": batch_count, "pool": None,
                            "label": f"Magical Secrets: choose {batch_count} spells from any class (Lv{ms_lvl})",
                            "already_chosen": already})

        # ── College of Lore: Bonus Magical Secrets (Lv6) ──────────────────────
        if cname == "Bard" and "lore" in sub and clvl >= 6:
            key = "bard_lore_secrets_6"
            already = made.get(key, [])
            if not already:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "College of Lore", "type": "magical_secrets",
                    "count": 2, "pool": None,
                    "label": "Bonus Magical Secrets: choose 2 spells from any class (Lore Bard Lv6)",
                    "already_chosen": already})

        # ── Eldritch Knight: spells known (uses get_choices_needed for spell slots) ──
        # (handled by existing spell chooser logic)

        # ── Cleric Knowledge Domain: Blessings of Knowledge (Lv1) ───────────────
        # Real text grants proficiency AND doubled proficiency bonus (i.e.
        # expertise) in 2 of 4 listed skills — using the "expertise" chooser
        # type rather than plain "skill_prof" so it grants the doubled
        # bonus, not just ordinary proficiency.
        if cname == "Cleric" and "knowledge" in sub and clvl >= 1:
            already = made.get("knowledge_domain_expertise", [])
            if len(already) < 2:
                choices.append({"id": "knowledge_domain_expertise", "source": "subclass",
                    "source_name": "Knowledge Domain", "type": "expertise",
                    "count": 2, "pool": ["Arcana","History","Nature","Religion"],
                    "label": "Blessings of Knowledge: choose 2 skills (expertise)",
                    "already_chosen": already})
            already_lang = made.get("knowledge_domain_languages", [])
            if len(already_lang) < 2:
                choices.append({"id": "knowledge_domain_languages", "source": "subclass",
                    "source_name": "Knowledge Domain", "type": "skill_prof",
                    "count": 2, "pool": LANGUAGES,
                    "label": "Blessings of Knowledge: choose 2 languages",
                    "already_chosen": already_lang})

        # ── Cleric Strength Domain (Amonkhet): Acolyte of Strength (Lv1) ────────
        if cname == "Cleric" and "strength domain" in sub.lower() and clvl >= 1:
            already = made.get("acolyte_of_strength_skill_profs", [])
            if not already:
                choices.append({"id": "acolyte_of_strength_skill_profs", "source": "subclass",
                    "source_name": "Acolyte of Strength", "type": "skill_prof",
                    "count": 1, "pool": ["Animal Handling","Athletics","Nature","Survival"],
                    "label": "Acolyte of Strength: choose 1 skill",
                    "already_chosen": already})

        # ── Sorcerer: Metamagic choices ────────────────────────────────────────
        if cname == "Sorcerer" and clvl >= 3:
            METAMAGIC_OPTIONS = [
                "Careful Spell – spend 1 SP: chosen creatures auto-succeed your spell saves",
                "Distant Spell – spend 1 SP: double range, or touch becomes 30 ft",
                "Empowered Spell – spend 1 SP: reroll up to CHA mod damage dice (once per spell)",
                "Extended Spell – spend 1 SP: double duration (max 24h)",
                "Heightened Spell – spend 3 SP: one target has disadv on first save",
                "Quickened Spell – spend 2 SP: change cast time from 1 action to bonus action",
                "Seeking Spell – spend 2 SP: if a spell attack roll misses, reroll it (must use new roll)",
                "Subtle Spell – spend 1 SP: cast without V or S components",
                "Transmuted Spell – spend 1 SP: change damage type to acid/cold/fire/lightning/poison/thunder",
                "Twinned Spell – spend SP = spell level (1 SP if a cantrip): target a second creature",
            ]
            # PHB 2014 progression: 2 at 3rd level, 3 at 10th, 4 at 17th.
            # (The old "+1 every 4 levels" formula was mathematically wrong —
            # it gave 5 options at 15th level and 6 by 19th, both too many.)
            count = 4 if clvl >= 17 else 3 if clvl >= 10 else 2
            already = char.get("_choices", {}).get("sorcerer_metamagic", [])
            if len(already) < count:
                choices.append({"id": "sorcerer_metamagic", "source": "class",
                    "source_name": "Sorcerer", "type": "metamagic",
                    "count": count, "pool": METAMAGIC_OPTIONS,
                    "label": f"Choose {count} Metamagic Options",
                    "already_chosen": already})

        # ── Artificer Armorer: Arcane Armor model (Lv3) ─────────────────────────
        if cname == "Artificer" and "armorer" in sub and clvl >= 3:
            key = "armorer_model_3"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Armorer", "type": "fighting_style", "count": 1,
                    "pool": ["Guardian – Thunder Gauntlets (1d8 thunder, target has disadvantage attacking others); bonus action: temp HP = artificer level, PB times/long rest",
                             "Infiltrator – Lightning Launcher (ranged 90/300ft, 1d6 lightning + extra 1d6 once/turn); +5ft speed; advantage on Stealth checks"],
                    "label": "Choose Arcane Armor Model (Armorer Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Barbarian Path of the Beast: Form of the Beast (Lv3) ────────────────
        if cname == "Barbarian" and "beast" in sub and clvl >= 3:
            key = "beast_form_3"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Path of the Beast", "type": "fighting_style", "count": 1,
                    "pool": ["Bite – reach 5ft, 1d8+STR piercing; once/turn when you hit below half HP, heal PB",
                             "Claws – reach 5ft, 1d6+STR slashing; once/turn, make one extra claw attack as part of the same Attack action",
                             "Tail – reach 10ft, 1d8+STR piercing; reaction: roll a d8 and add it to your AC against one attack"],
                    "label": "Choose Form of the Beast (Path of the Beast Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Barbarian Storm Herald: Storm Aura (Lv3) ────────────────────────────
        if cname == "Barbarian" and "storm herald" in sub and clvl >= 3:
            key = "storm_aura_3"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Storm Herald", "type": "fighting_style", "count": 1,
                    "pool": ["Desert – on activation, all other creatures in your aura take 2 fire damage (scales with level)",
                             "Sea – choose one creature in your aura: DEX save or take 1d6 lightning damage, half on success (scales with level)",
                             "Tundra – choose one creature in your aura to gain 2 temporary HP (scales with level)"],
                    "label": "Choose Storm Aura (Storm Herald Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Fighter Arcane Archer: Arcane Shot options (Lv3, 2 initially) ───────
        if cname == "Fighter" and "arcane archer" in sub and clvl >= 3:
            ARCANE_SHOT_OPTIONS = [
                "Banishing Arrow – CHA save or banished (speed 0, incapacitated) until end of its next turn; +2d6 force at 18th level",
                "Beguiling Arrow – +2d6 psychic; WIS save or charmed by an ally you choose until start of your next turn",
                "Bursting Arrow – +2d6 force to the target AND every creature within 10ft of it",
                "Enfeebling Arrow – +2d6 necrotic; CON save or its weapon damage is halved until start of your next turn",
                "Grasping Arrow – +2d6 poison; speed reduced 10ft, +2d6 slashing the first time it moves each turn (STR check vs your save DC to clear)",
                "Piercing Arrow – no attack roll: 30ft line, 1ft wide, ignores cover; DEX save or full damage +1d6 piercing (half on save)",
                "Seeking Arrow – no attack roll: curving shot ignores 3/4 and half cover; DEX save or full damage +1d6 force and you learn its location (half, no location on save)",
                "Shadow Arrow – +2d6 psychic; WIS save or blinded beyond 5ft until start of your next turn",
            ]
            shots_known = {3:2, 7:3, 10:4, 15:5, 18:6}
            total = max(v for lvl2,v in shots_known.items() if clvl >= lvl2)
            already = made.get("arcane_shot_options", [])
            if len(already) < total:
                choices.append({"id": "arcane_shot_options", "source": "subclass",
                    "source_name": "Arcane Archer", "type": "metamagic",
                    "count": total, "pool": ARCANE_SHOT_OPTIONS,
                    "label": f"Choose {total} Arcane Shot option(s)",
                    "already_chosen": already})

        # ── Fighter Rune Knight: Runes (Lv3, 2 initially) ───────────────────────
        if cname == "Fighter" and "rune knight" in sub and clvl >= 3:
            RUNE_OPTIONS = [
                "Cloud Rune – advantage on Sleight of Hand & Deception; reaction: redirect an attack that hit someone within 30ft to a different creature",
                "Fire Rune – double proficiency bonus on tool checks; on a hit, +2d6 fire and STR save or restrained + 2d6 fire/turn until it saves",
                "Frost Rune – advantage on Animal Handling & Intimidation; bonus action: +2 to STR checks/saves for 10 min",
                "Hill Rune – advantage on saves vs poison + resistance to poison damage; bonus action: resistance to bludgeoning/piercing/slashing for 1 min",
                "Stone Rune – advantage on Insight, darkvision 120ft; reaction: WIS save or charmed (speed 0, incapacitated) for 1 min",
                "Storm Rune (7th+) – advantage on Arcana, can't be surprised; bonus action 1 min: reaction to impose advantage or disadvantage on a roll within 60ft",
            ]
            runes_known = {3:2, 7:3, 10:4, 15:5}
            total = max(v for lvl2,v in runes_known.items() if clvl >= lvl2)
            already = made.get("rune_knight_runes", [])
            if len(already) < total:
                choices.append({"id": "rune_knight_runes", "source": "subclass",
                    "source_name": "Rune Knight", "type": "metamagic",
                    "count": total, "pool": RUNE_OPTIONS,
                    "label": f"Choose {total} Rune(s)",
                    "already_chosen": already})

        # ── Monk Way of the Ascendant Dragon: Draconic Strike is per-attack ─────
        # Not a permanent pick — Draconic Strike lets you change your unarmed
        # strike's damage type to acid/cold/fire/lightning/poison freely each
        # time you hit, so this is an acknowledgment rather than a chooser
        # (a previous version incorrectly forced a one-time permanent choice).
        if cname == "Monk" and "ascendant dragon" in sub and clvl >= 3:
            key = "ascendant_dragon_ack"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Way of the Ascendant Dragon", "type": "info",
                    "count": 1, "pool": None,
                    "label": "Draconic Strike: freely choose acid/cold/fire/lightning/poison each time you hit with an unarmed strike",
                    "already_chosen": ["ack"]})

        # ── Monk Way of the Kensei: Kensei weapons (Lv3, 2 initially) ───────────
        if cname == "Monk" and "kensei" in sub and clvl >= 3:
            KENSEI_WEAPON_OPTIONS = [
                "Club", "Dagger", "Greatclub", "Handaxe", "Javelin", "Light Hammer",
                "Mace", "Quarterstaff", "Sickle", "Spear", "Light Crossbow", "Dart",
                "Shortbow", "Sling", "Battleaxe", "Longsword", "Morningstar", "Rapier",
                "Scimitar", "Shortsword", "Trident", "War Pick", "Warhammer", "Whip",
                "Longbow",
            ]
            weapons_known = {3:2, 6:3, 11:4, 17:5}
            total = max(v for lvl2,v in weapons_known.items() if clvl >= lvl2)
            already = made.get("kensei_weapons", [])
            if len(already) < total:
                choices.append({"id": "kensei_weapons", "source": "subclass",
                    "source_name": "Way of the Kensei", "type": "metamagic",
                    "count": total, "pool": KENSEI_WEAPON_OPTIONS,
                    "label": f"Choose {total} Kensei weapon(s)",
                    "already_chosen": already})

        # ── Sorcerer Divine Soul: Affinity (Lv1) ────────────────────────────────
        # Divine Magic itself (choosing sorcerer cantrips/spells from the
        # Cleric list too) is an ongoing privilege applied whenever spells
        # are picked, not a one-time chooser. The actual permanent 1st-level
        # pick is an affinity, each granting one specific fixed bonus spell.
        if cname == "Sorcerer" and "divine soul" in sub and clvl >= 1:
            key = "divine_soul_affinity"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Divine Soul", "type": "fighting_style", "count": 1,
                    "pool": ["Good – bonus spell: Cure Wounds", "Evil – bonus spell: Inflict Wounds",
                             "Law – bonus spell: Bless", "Chaos – bonus spell: Bane",
                             "Neutrality – bonus spell: Protection from Evil and Good"],
                    "label": "Choose Divine Magic Affinity (Divine Soul Lv1)",
                    "already_chosen": made.get(key, [])})

        # ── Wizard: Spell Mastery (18th) and Signature Spells (20th) ────────────
        # Both had the same shape of gap as Warlock's Mystic Arcanum — never
        # actually offered despite being real, high-level Wizard features.
        # Filtered to the Wizard's own known spells (spells_known) at the
        # correct level, since the real rule specifies spells "from your
        # spellbook," not any spell of that level from the full class list.
        if cname == "Wizard" and clvl >= 18:
            from dnd_app.data.spells import SPELL_DICT
            known_names = char.get("spells_known", [])
            for spell_lvl, key in ((1, "wizard_spell_mastery_1"), (2, "wizard_spell_mastery_2")):
                already = made.get(key, [])
                if already:
                    continue
                pool = [n for n in known_names
                        if SPELL_DICT.get(n, {}).get("level") == spell_lvl]
                if pool:
                    choices.append({
                        "id": key,
                        "source": "class", "source_name": "Wizard",
                        "type": "magical_secrets", "count": 1,
                        "pool": pool,
                        "label": f"Spell Mastery: choose 1 known {spell_lvl}st-level spell to cast at will"
                                 if spell_lvl == 1 else
                                 f"Spell Mastery: choose 1 known {spell_lvl}nd-level spell to cast at will",
                        "already_chosen": already,
                    })
        if cname == "Wizard" and clvl >= 20:
            from dnd_app.data.spells import SPELL_DICT
            known_names = char.get("spells_known", [])
            key = "wizard_signature_spells"
            already = made.get(key, [])
            pool = [n for n in known_names if SPELL_DICT.get(n, {}).get("level") == 3]
            if len(already) < 2 and pool:
                choices.append({
                    "id": key,
                    "source": "class", "source_name": "Wizard",
                    "type": "magical_secrets", "count": 2 - len(already),
                    "pool": pool,
                    "label": f"Signature Spells: choose {2 - len(already)} known 3rd-level spell(s)",
                    "already_chosen": already,
                })

        # ── Sorcerer Draconic Bloodline: Dragon Ancestor (Lv1) ──────────────────
        if cname == "Sorcerer" and "draconic" in sub and clvl >= 1:
            key = "sorcerer_dragon_ancestor"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Draconic Bloodline", "type": "fighting_style", "count": 1,
                    "pool": ["Black – acid", "Blue – lightning", "Brass – fire", "Bronze – lightning",
                             "Copper – acid", "Gold – fire", "Green – poison", "Red – fire",
                             "Silver – cold", "White – cold"],
                    "label": "Choose Dragon Ancestor (Draconic Bloodline Lv1)",
                    "already_chosen": made.get(key, [])})

        # ── Warlock The Genie: Genie's Vessel kind (Lv1) ────────────────────────
        if cname == "Warlock" and "genie" in sub and clvl >= 1:
            key = "genie_kind"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "The Genie", "type": "fighting_style", "count": 1,
                    "pool": ["Dao – bonus attack damage and resistance are bludgeoning",
                             "Djinni – bonus attack damage and resistance are thunder",
                             "Efreeti – bonus attack damage and resistance are fire",
                             "Marid – bonus attack damage and resistance are cold"],
                    "label": "Choose Genie kind (The Genie Lv1)",
                    "already_chosen": made.get(key, [])})

        # ── Ranger Drakewarden: Draconic Essence (Lv3) ──────────────────────────
        # Chosen each time the drake is summoned per the real rules, but
        # tracked as a single persistent choice here for simplicity — it
        # determines both the drake's Infused Strikes damage type and (at
        # 7th level, Bond of Fang and Scale) the character's own resistance.
        if cname == "Ranger" and "drakewarden" in sub and clvl >= 3:
            key = "drake_essence"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Drakewarden", "type": "fighting_style", "count": 1,
                    "pool": ["Acid", "Cold", "Fire", "Lightning", "Poison"],
                    "label": "Choose Draconic Essence (Drake Companion Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Warlock The Fiend: Fiendish Resilience (Lv10) ───────────────────────
        # Real text: choose any damage type each time you finish a short or
        # long rest, gain resistance to it (magic/silver weapons bypass).
        # Simplified to a persistent choice, re-pickable via the Choices tab.
        if cname == "Warlock" and "fiend" in sub and clvl >= 10:
            key = "fiendish_resilience"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "The Fiend", "type": "fighting_style", "count": 1,
                    "pool": ["Acid","Bludgeoning","Cold","Fire","Force","Lightning",
                             "Necrotic","Piercing","Poison","Psychic","Radiant","Slashing","Thunder"],
                    "label": "Choose Fiendish Resilience damage type (re-choosable each rest)",
                    "already_chosen": made.get(key, [])})

    return choices


def _get_feat_choices(char):
    """Player-chosen proficiency grants from feats — confirmed these had
    zero UI selection support at all despite being an explicit, real part
    of the feat's benefit (a player taking Skilled had no way to actually
    pick their 3 skills/tools anywhere in the app). Detects a feat was
    taken by scanning every _choices value for a "feat:Name" entry, the
    same way it's stored when picked via the ASI-or-feat chooser.
    Weapon Master, Skill Expert, and Prodigy need the same kind of
    treatment but are more complex (weapon pools, an additional
    expertise-in-an-existing-skill sub-choice) and aren't covered yet —
    flagged rather than rushed."""
    choices = []
    made = char.get("_choices", {})
    all_feats = set(char.get("feats", []))

    if "Skilled" in all_feats:
        key = "feat_skilled_skill_or_tool_profs"
        already = made.get(key, [])
        if len(already) < 3:
            from dnd_app.data.items import ALL_TOOLS
            choices.append({
                "id": key, "source": "feat", "source_name": "Skilled",
                "type": "skill_or_tool_prof", "count": 3,
                "pool": ALL_SKILLS + ALL_TOOLS,
                "label": "Choose any combination of 3 skills or tools",
                "already_chosen": already,
            })
    if "Woodwise" in all_feats:
        key = "feat_woodwise_skill_prof"
        already = made.get(key, [])
        if len(already) < 1:
            choices.append({
                "id": key, "source": "feat", "source_name": "Woodwise",
                "type": "skill_prof", "count": 1,
                "pool": ["Survival", "Nature"],
                "label": "Choose 1 of Survival or Nature",
                "already_chosen": already,
            })
    if "Forest Sage" in all_feats:
        key = "feat_forest_sage_spells"
        already = made.get(key, [])
        if len(already) < 2:
            # Same max-castable-level formula used in sheet.py/wizard.py's
            # _max_castable_spell_level(), replicated here since this is a
            # standalone function operating on the char parameter directly.
            max_lvl = 0
            for i, count in enumerate(char.get("spell_slots_max", [])):
                if count > 0:
                    max_lvl = i + 1
            if char.get("pact_slots_max", 0) > 0:
                max_lvl = max(max_lvl, char.get("pact_slot_level", 0))
            from dnd_app.data.spells import ALL_SPELLS
            pool = sorted({s["name"] for s in ALL_SPELLS
                           if 1 <= s.get("level", 0) <= max_lvl
                           and ("Druid" in s.get("classes", []) or "Wizard" in s.get("classes", []))})
            choices.append({
                "id": key, "source": "feat", "source_name": "Forest Sage",
                "type": "magical_secrets", "count": 2,
                "pool": pool,
                "label": f"Choose 2 spells (level 1-{max_lvl}) from the Druid or Wizard list",
                "already_chosen": already,
            })
    if "Weapon Master" in all_feats:
        key = "feat_weapon_master_weapons"
        already = made.get(key, [])
        if len(already) < 4:
            from dnd_app.data.items import SIMPLE_MELEE, SIMPLE_RANGED, MARTIAL_MELEE, MARTIAL_RANGED
            weapon_pool = [w[0] for w in (SIMPLE_MELEE + SIMPLE_RANGED + MARTIAL_MELEE + MARTIAL_RANGED)]
            choices.append({
                "id": key, "source": "feat", "source_name": "Weapon Master",
                "type": "magical_secrets", "count": 4,
                "pool": weapon_pool,
                "label": "Choose 4 weapons (simple or martial) to gain proficiency with",
                "already_chosen": already,
            })
    if "Artificer Initiate" in all_feats:
        key = "feat_artificer_initiate_tool_profs"
        already = made.get(key, [])
        if len(already) < 1:
            from dnd_app.data.items import ARTISAN_TOOLS
            choices.append({
                "id": key, "source": "feat", "source_name": "Artificer Initiate",
                "type": "tool_prof", "count": 1,
                "pool": ARTISAN_TOOLS,
                "label": "Choose 1 type of artisan's tools",
                "already_chosen": already,
            })

    if "Scion of the Outer Planes" in all_feats:
        key = "feat_scion_plane_type"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "feat", "source_name": "Scion of the Outer Planes",
                "type": "fighting_style", "count": 1,
                "pool": ["Chaotic Outer Plane", "Evil Outer Plane", "Good Outer Plane",
                         "Lawful Outer Plane", "The Outlands"],
                "label": "Choose your plane type (determines your resistance and cantrip)",
                "already_chosen": already,
            })

    if "Fighting Initiate" in all_feats:
        key = "feat_initiate_fighting_style"
        already = made.get(key, [])
        if not already:
            known_styles_lower = {fs.split(" (")[0].strip().lower()
                                   for fs in char.get("fighting_styles", [])}
            pool = [fs for fs in FIGHTING_STYLES["Fighter"]
                    if fs.split(" (")[0].strip().lower() not in known_styles_lower]
            if pool:
                choices.append({
                    "id": key, "source": "feat", "source_name": "Fighting Initiate",
                    "type": "fighting_style", "count": 1,
                    "pool": pool,
                    "label": "Choose 1 Fighting Style (must differ from any you already know)",
                    "already_chosen": already,
                })

    if "Ritual Caster" in all_feats:
        key = "feat_ritual_caster_spells"
        already = made.get(key, [])
        if len(already) < 2:
            from dnd_app.data.spells import ALL_SPELLS
            pool = sorted({s["name"] for s in ALL_SPELLS if s.get("level") == 1 and s.get("ritual")
                          and any(cn in s.get("classes", []) for cn in ("Cleric", "Druid", "Wizard"))})
            choices.append({
                "id": key, "source": "feat", "source_name": "Ritual Caster",
                "type": "magical_secrets", "count": 2,
                "pool": pool,
                "label": "Choose 2 1st-level ritual spells (Cleric/Druid/Wizard list) — always prepared",
                "already_chosen": already,
            })

    if "Linguist" in all_feats:
        key = "feat_linguist_languages"
        already = made.get(key, [])
        if len(already) < 3:
            choices.append({
                "id": key, "source": "feat", "source_name": "Linguist",
                "type": "language", "count": 3,
                "label": "Choose 3 languages",
                "already_chosen": already,
            })

    if "Prodigy" in all_feats:
        from dnd_app.data.items import ALL_TOOLS
        key_skill = "feat_prodigy_skill_profs"
        already_skill = made.get(key_skill, [])
        if len(already_skill) < 1:
            choices.append({
                "id": key_skill, "source": "feat", "source_name": "Prodigy",
                "type": "skill_prof", "count": 1,
                "pool": ALL_SKILLS,
                "label": "Choose 1 skill to gain proficiency in",
                "already_chosen": already_skill,
            })
        key_tool = "feat_prodigy_tool_profs"
        already_tool = made.get(key_tool, [])
        if len(already_tool) < 1:
            choices.append({
                "id": key_tool, "source": "feat", "source_name": "Prodigy",
                "type": "tool_prof", "count": 1,
                "pool": ALL_TOOLS,
                "label": "Choose 1 tool to gain proficiency in",
                "already_chosen": already_tool,
            })
        key_lang = "feat_prodigy_language"
        already_lang = made.get(key_lang, [])
        if len(already_lang) < 1:
            choices.append({
                "id": key_lang, "source": "feat", "source_name": "Prodigy",
                "type": "language", "count": 1,
                "label": "Choose 1 language",
                "already_chosen": already_lang,
            })
        key_exp = "feat_prodigy_expertise"
        already_exp = made.get(key_exp, [])
        if len(already_exp) < 1:
            proficient_skills = [s for s, lvl in char.get("skills", {}).items() if lvl >= 2]
            if proficient_skills:
                choices.append({
                    "id": key_exp, "source": "feat", "source_name": "Prodigy",
                    "type": "expertise", "count": 1,
                    "pool": sorted(proficient_skills),
                    "label": "Choose 1 already-proficient skill to gain expertise in",
                    "already_chosen": already_exp,
                })

    if "Skill Expert" in all_feats:
        key_new = "feat_skill_expert_skill_profs"
        already_new = made.get(key_new, [])
        if len(already_new) < 1:
            choices.append({
                "id": key_new, "source": "feat", "source_name": "Skill Expert",
                "type": "skill_prof", "count": 1,
                "pool": ALL_SKILLS,
                "label": "Choose 1 skill to gain proficiency in",
                "already_chosen": already_new,
            })
        key_exp = "feat_skill_expert_expertise"
        already_exp = made.get(key_exp, [])
        if len(already_exp) < 1:
            proficient_skills = [s for s, lvl in char.get("skills", {}).items() if lvl >= 2]
            if proficient_skills:
                choices.append({
                    "id": key_exp, "source": "feat", "source_name": "Skill Expert",
                    "type": "expertise", "count": 1,
                    "pool": sorted(proficient_skills),
                    "label": "Choose 1 already-proficient skill to gain expertise in",
                    "already_chosen": already_exp,
                })

    if "Martial Adept" in all_feats:
        key = "feat_martial_adept_maneuvers"
        already = made.get(key, [])
        if len(already) < 2:
            from dnd_app.data.classes import BATTLE_MASTER_MANEUVERS
            choices.append({
                "id": key, "source": "feat", "source_name": "Martial Adept",
                "type": "maneuver", "count": 2 - len(already),
                "pool": BATTLE_MASTER_MANEUVERS,
                "label": f"Choose {2 - len(already)} Battle Master maneuver(s)",
                "already_chosen": already,
            })
    if "Metamagic Adept" in all_feats:
        key = "feat_metamagic_adept_options"
        already = made.get(key, [])
        if len(already) < 2:
            from dnd_app.data.classes import METAMAGIC
            choices.append({
                "id": key, "source": "feat", "source_name": "Metamagic Adept",
                "type": "metamagic", "count": 2 - len(already),
                "pool": METAMAGIC,
                "label": f"Choose {2 - len(already)} Metamagic option(s)",
                "already_chosen": already,
            })
    if "Eldritch Adept" in all_feats:
        key = "feat_eldritch_adept_invocation"
        already = made.get(key, [])
        if len(already) < 1:
            from dnd_app.data.classes import ELDRITCH_INVOCATIONS
            import re
            is_warlock = char.get("class") == "Warlock" or any(
                c.get("class") == "Warlock" for c in char.get("classes", []))
            warlock_lvl = char.get("level", 0) if char.get("class") == "Warlock" else next(
                (c.get("level", 0) for c in char.get("classes", []) if c.get("class") == "Warlock"), 0)
            # Real rule: "If the invocation has a prerequisite of any
            # kind, you can choose that invocation only if you're a
            # warlock who meets the prerequisite" — reuses the same
            # prerequisite filter already built for real Warlocks
            # rather than duplicating that logic.
            pool = []
            for inv in ELDRITCH_INVOCATIONS:
                name_part = inv.split("–")[0].strip()
                if name_part.startswith("Pact of the"):
                    continue
                m = re.search(r'\(([^)]*)\)\s*$', name_part)
                if not m:
                    pool.append(inv)
                elif is_warlock:
                    req = m.group(1).lower()
                    lvl_m = re.match(r'(\d+)(st|nd|rd|th)', req)
                    if not lvl_m or warlock_lvl >= int(lvl_m.group(1)):
                        pool.append(inv)
            choices.append({
                "id": key, "source": "feat", "source_name": "Eldritch Adept",
                "type": "invocation", "count": 1,
                "pool": pool,
                "label": "Choose 1 Eldritch Invocation",
                "already_chosen": already,
            })
    return choices


def _get_optional_feature_choices(char):
    """TCE optional-feature choices — extensible for future ones.
    Canny (Deft Explorer's foundational 1st-level component) confirmed
    genuinely missing a real choice card, even though its other two
    parts (Roving, Tireless) were already correctly built elsewhere."""
    choices = []
    made = char.get("_choices", {})
    ranger_lvl = sum(c.get("level", 0) for c in char.get("classes", []) if c.get("class") == "Ranger")
    deft_on = (made.get("optional_features", {}).get("Deft Explorer", False)
               or char.get("optional_rules", {}).get("deft_explorer", False))
    if ranger_lvl >= 1 and deft_on:
        already_canny = made.get("deft_explorer_canny", [])
        if not already_canny:
            proficient_only = [s for s, lvl in char.get("skills", {}).items() if lvl == 2]
            if proficient_only:
                choices.append({
                    "id": "deft_explorer_canny", "source": "class", "source_name": "Ranger",
                    "type": "expertise", "count": 1,
                    "pool": sorted(proficient_only),
                    "label": "Canny (Deft Explorer): choose 1 proficient skill for doubled "
                             "proficiency bonus",
                    "already_chosen": already_canny,
                })
        already_canny_lang = made.get("deft_explorer_canny_languages", [])
        if len(already_canny_lang) < 2:
            choices.append({
                "id": "deft_explorer_canny_languages", "source": "class", "source_name": "Ranger",
                "type": "language", "count": 2,
                "label": "Canny (Deft Explorer): choose 2 additional languages",
                "already_chosen": already_canny_lang,
            })

    # Primal Knowledge (Barbarian, TCE optional, genuinely missing
    # entirely): 2 separate choice instances since 3rd and 10th level
    # are independent grants, not one combined choice. Uses Barbarian's
    # real 1st-level skill pool rather than a hardcoded guess.
    from dnd_app.data.classes import CLASS_DICT
    barb_lvl = sum(c.get("level", 0) for c in char.get("classes", []) if c.get("class") == "Barbarian")
    primal_on = (made.get("optional_features", {}).get("Primal Knowledge", False)
                 or char.get("optional_rules", {}).get("primal_knowledge", False))
    if primal_on:
        barb_skill_pool = CLASS_DICT.get("Barbarian", {}).get("skill_choices", [])
        for req_lvl, choice_id in ((3, "primal_knowledge_3_skill_profs"), (10, "primal_knowledge_10_skill_profs")):
            if barb_lvl >= req_lvl:
                already_pk = made.get(choice_id, [])
                if not already_pk:
                    choices.append({
                        "id": choice_id, "source": "class", "source_name": "Barbarian",
                        "type": "skill_prof", "count": 1,
                        "pool": barb_skill_pool,
                        "label": f"Primal Knowledge ({req_lvl}th level): choose 1 skill "
                                 f"proficiency",
                        "already_chosen": already_pk,
                    })
    return choices


def _get_race_choices(char):
    """Race-specific choices not covered by the main builder."""
    choices = []
    made = char.get("_choices",{})
    race = char.get("species") or char.get("race","")

    if race in RACE_SKILL_CHOICES:
        cfg = RACE_SKILL_CHOICES[race]
        already = made.get("race_skill_profs",[])
        if len(already) < cfg["count"]:
            choices.append({
                "id": "race_skill_profs",
                "source": "race", "source_name": race,
                "type": "skill_prof",
                "count": cfg["count"],
                "pool": cfg["pool"],
                "label": cfg["label"],
                "already_chosen": already,
            })

    # Aasimar (MPMM) Celestial Revelation: lets the player select which
    # revelation they get, from the race data's 3 options. Gated to
    # level 3+, and locked in once chosen per the real rule (never re-offered after).
    if race == "Aasimar (MPMM)":
        clvl = sum(c.get("level", 0) for c in char.get("classes", []))
        already_rev = made.get("aasimar_revelation", [])
        if clvl >= 3 and not already_rev:
            choices.append({
                "id": "aasimar_revelation", "source": "race", "source_name": race,
                "type": "skill_prof", "count": 1,
                "pool": ["Necrotic Shroud", "Radiant Consumption", "Radiant Soul"],
                "label": "Celestial Revelation: choose 1 (locked in once chosen)",
                "already_chosen": already_rev,
            })

    # Vedalken's Tireless Precision: a restricted-pool skill choice PLUS
    # a separate tool choice — both required, neither optional, so
    # modeled as two distinct choice cards rather than one combined
    # skill-or-tool pick.
    if race == "Vedalken":
        already_sk = made.get("race_skill_profs", [])
        if len(already_sk) < 1:
            choices.append({
                "id": "race_skill_profs", "source": "race", "source_name": race,
                "type": "skill_prof", "count": 1,
                "pool": ["Arcana","History","Investigation","Medicine","Performance","Sleight of Hand"],
                "label": "Tireless Precision (Vedalken): choose 1 of Arcana, History, Investigation, Medicine, Performance, Sleight of Hand",
                "already_chosen": already_sk,
            })
        already_tl = made.get("race_tool_profs", [])
        if len(already_tl) < 1:
            choices.append({
                "id": "race_tool_profs", "source": "race", "source_name": race,
                "type": "tool_prof", "count": 1, "pool": None,
                "label": "Tireless Precision (Vedalken): choose 1 tool proficiency",
                "already_chosen": already_tl,
            })

    # Warforged's Specialized Design: one skill (any) AND one tool
    # (any) — both required, modeled the same way as Vedalken above.
    if race == "Warforged":
        already_sk = made.get("race_skill_profs", [])
        if len(already_sk) < 1:
            choices.append({
                "id": "race_skill_profs", "source": "race", "source_name": race,
                "type": "skill_prof", "count": 1, "pool": ALL_SKILLS,
                "label": "Specialized Design (Warforged): choose 1 skill proficiency",
                "already_chosen": already_sk,
            })
        already_tl = made.get("race_tool_profs", [])
        if len(already_tl) < 1:
            choices.append({
                "id": "race_tool_profs", "source": "race", "source_name": race,
                "type": "tool_prof", "count": 1, "pool": None,
                "label": "Specialized Design (Warforged): choose 1 tool proficiency",
                "already_chosen": already_tl,
            })

    # Githyanki's Decadent Mastery: one skill OR tool of choice — a
    # single combined pick, using the existing skill_or_tool_prof type
    # the picker UI and apply_choice's aggregation already support.
    if race == "Githyanki":
        already = made.get("race_skill_or_tool_profs", [])
        if len(already) < 1:
            choices.append({
                "id": "race_skill_or_tool_profs", "source": "race", "source_name": race,
                "type": "skill_or_tool_prof", "count": 1, "pool": None,
                "label": "Decadent Mastery (Githyanki): choose 1 skill or tool proficiency",
                "already_chosen": already,
            })

    # Eladrin: seasonal Fey Step effect. Player picks one season;
    # RestOptionsDialog offers to re-pick after a long rest per the
    # actual rule ("you can change your chosen season after a long rest").
    if "eladrin" in race.lower():
        already_season = made.get("eladrin_season", [])
        if not already_season:
            choices.append({
                "id": "eladrin_season", "source": "race", "source_name": "Eladrin",
                "type": "fighting_style", "count": 1,
                "pool": ["Autumn – Fey Step charms one creature within 5 ft. of your destination",
                         "Winter – Fey Step frightens one creature within 5 ft. of your destination",
                         "Spring – a willing creature within 5 ft. can teleport with you",
                         "Summer – Fey Step deals 2d6 fire damage to creatures within 5 ft. of your origin"],
                "label": "Choose your Eladrin season (changeable after a long rest)",
                "already_chosen": already_season,
            })

    # Human extra language
    if race == "Human":
        already = made.get("human_extra_language",[])
        if not already:
            choices.append({
                "id": "human_extra_language",
                "source": "race", "source_name": "Human",
                "type": "language", "count": 1,
                "pool": LANGUAGES,
                "label": "Human Extra Language: choose 1",
                "already_chosen": already,
            })

    # High Elf / Half-Elf (High Descent): choose any cantrip from the
    # Wizard spell list. A genuine open choice, not a fixed grant — no
    # default can be guessed here any more than a Genie's kind could.
    subrace = char.get("subrace", "") or ""
    is_high_elf = race == "Elf" and "high" in subrace.lower()
    is_high_half_elf = race == "Half-Elf" and "high" in subrace.lower()
    if is_high_elf or is_high_half_elf:
        from dnd_app.data.spells import ALL_SPELLS
        wiz_cantrips = sorted({s["name"] for s in ALL_SPELLS
                                if s.get("level") == 0 and "Wizard" in s.get("classes", [])})
        key = "race_wizard_cantrip"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "race",
                "source_name": "High Elf" if is_high_elf else "Half-Elf (High Descent)",
                "type": "fighting_style", "count": 1,
                "pool": wiz_cantrips,
                "label": "Choose a Wizard cantrip",
                "already_chosen": already,
            })

    # Merfolk: each subrace grants an open cantrip choice from a specific
    # class's list — same open-list pattern as High Elf, just keyed to a
    # different class per subrace rather than always Wizard.
    if race == "Merfolk":
        MERFOLK_CANTRIP_CLASS = {
            "green": "Druid", "blue": "Wizard", "emeria": "Druid",
            "ula": "Wizard", "cosi": "Bard",
        }
        matched_class = next((cls for key, cls in MERFOLK_CANTRIP_CLASS.items()
                               if key in subrace.lower()), None)
        if matched_class:
            from dnd_app.data.spells import ALL_SPELLS
            cantrips = sorted({s["name"] for s in ALL_SPELLS
                                if s.get("level") == 0 and matched_class in s.get("classes", [])})
            key = "race_merfolk_cantrip"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "race", "source_name": f"Merfolk ({matched_class} cantrip)",
                    "type": "fighting_style", "count": 1,
                    "pool": cantrips,
                    "label": f"Choose a {matched_class} cantrip",
                    "already_chosen": already,
                })

    # Astral Elf: choose one of exactly three cantrips (not an open Wizard
    # list like High Elf).
    if race == "Astral Elf":
        key = "astral_elf_cantrip"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "race", "source_name": "Astral Elf",
                "type": "fighting_style", "count": 1,
                "pool": ["Dancing Lights", "Light", "Sacred Flame"],
                "label": "Astral Fire: choose a cantrip",
                "already_chosen": already,
            })

    # Racial spellcasting ability — several races with innate spellcasting
    # let the player choose which of INT/WIS/CHA powers it, rather than
    # fixing one. A real choice, not something with a sensible default, so
    # it's asked for explicitly rather than silently assumed.
    RACES_WITH_ABILITY_CHOICE = {
        "Firbolg": "Firbolg Magic", "Fairy": "Fairy Magic",
        "Astral Elf": "Astral Fire", "Hexblood": "Hex Magic",
    }
    ability_source = RACES_WITH_ABILITY_CHOICE.get(race)
    if not ability_source and race == "Yuan-ti Pureblood" and "mpmm" in subrace.lower():
        ability_source = "Innate Spellcasting"
    if ability_source:
        key = "racial_spell_ability"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "race", "source_name": ability_source,
                "type": "fighting_style", "count": 1,
                "pool": ["Intelligence", "Wisdom", "Charisma"],
                "label": f"Choose spellcasting ability for {ability_source}",
                "already_chosen": already,
            })

    # Simic Hybrid: Additional Animal Enhancement at 5th (total) level.
    # The 1st-level pick is made in the character-creation wizard
    # (stored as simic_enhancement_1st); this is the second, later pick
    # the real rules grant, deliberately left for this level-up system.
    if race == "Simic Hybrid":
        total_lvl = sum(c.get("level", 0) for c in char.get("classes", []))
        if total_lvl >= 5:
            key = "simic_enhancement_5th"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "race", "source_name": "Simic Hybrid",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Grappling Appendages", "Carapace", "Acid Spit"],
                    "label": "Additional Animal Enhancement (5th level): choose one",
                    "already_chosen": already,
                })

    return choices


def _get_class_tool_choices(char):
    """Flexible ('of your choice') portions of class-granted tool
    proficiencies — Bard's 3 musical instruments, Monk's 1 artisan's-
    tool-or-instrument, and Artificer's 1 remaining artisan's tool
    pick. The fixed portions (Rogue's Thieves' tools, Druid's
    Herbalism kit, Artificer's Thieves'/Tinker's tools) are granted
    automatically via get_class_tool_profs() in builder.py and don't
    need a choice card at all."""
    from dnd_app.data.items import ALL_TOOLS, ARTISAN_TOOLS, INSTRUMENT_TOOLS
    choices = []
    made = char.get("_choices", {})
    class_names = [c.get("class", "") for c in char.get("classes", [])]

    if "Bard" in class_names:
        already = made.get("class_bard_tool_profs", [])
        if len(already) < 3:
            choices.append({
                "id": "class_bard_tool_profs", "source": "class", "source_name": "Bard",
                "type": "tool_prof", "count": 3, "pool": INSTRUMENT_TOOLS,
                "label": "Bard: choose 3 musical instruments",
                "already_chosen": already,
            })

    if "Monk" in class_names:
        already = made.get("class_monk_tool_profs", [])
        if len(already) < 1:
            choices.append({
                "id": "class_monk_tool_profs", "source": "class", "source_name": "Monk",
                "type": "tool_prof", "count": 1, "pool": ARTISAN_TOOLS + INSTRUMENT_TOOLS,
                "label": "Monk: choose 1 artisan's tool or musical instrument",
                "already_chosen": already,
            })

    if "Artificer" in class_names:
        already = made.get("class_artificer_tool_profs", [])
        if len(already) < 1:
            choices.append({
                "id": "class_artificer_tool_profs", "source": "class", "source_name": "Artificer",
                "type": "tool_prof", "count": 1, "pool": ARTISAN_TOOLS,
                "label": "Artificer: choose 1 additional artisan's tool",
                "already_chosen": already,
            })

    return choices


def _get_dm_reward_choices(char):
    """Player-chosen proficiency grants from DM-Granted Bonus Features
    (dm_rewards.py) — confirmed these had zero mechanical wiring of any
    kind before this pass, including no way to actually make the
    choices their own text describes."""
    choices = []
    made = char.get("_choices", {})
    rewards = set(char.get("dm_rewards", []))

    if "Echoing Soul" in rewards:
        key_sk = "dmreward_echoing_soul_skills"
        already_sk = made.get(key_sk, [])
        if len(already_sk) < 2:
            choices.append({
                "id": key_sk, "source": "dm_reward", "source_name": "Echoing Soul",
                "type": "skill_prof", "count": 2, "pool": ALL_SKILLS,
                "label": "Channeled Prowess: choose 2 skill proficiencies",
                "already_chosen": already_sk,
            })
        key_lang = "dmreward_echoing_soul_language"
        already_lang = made.get(key_lang, [])
        if len(already_lang) < 1:
            choices.append({
                "id": key_lang, "source": "dm_reward", "source_name": "Echoing Soul",
                "type": "language", "count": 1,
                "label": "Inherent Tongue: choose 1 additional language",
                "already_chosen": already_lang,
            })

    if "Symbiotic Being" in rewards:
        key_sk2 = "dmreward_symbiotic_being_skill"
        already_sk2 = made.get(key_sk2, [])
        if len(already_sk2) < 1:
            choices.append({
                "id": key_sk2, "source": "dm_reward", "source_name": "Symbiotic Being",
                "type": "skill_prof", "count": 1,
                "pool": ["Arcana", "Deception", "History", "Intimidation", "Insight",
                         "Investigation", "Nature", "Religion", "Perception", "Persuasion"],
                "label": "Entwined Existence: choose 1 skill proficiency",
                "already_chosen": already_sk2,
            })

    return choices
