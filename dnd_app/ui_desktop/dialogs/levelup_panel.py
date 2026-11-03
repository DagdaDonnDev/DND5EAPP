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
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QColor
from dnd_app.ui_desktop.style.theme import *
from ..shared import h as _h, _btn
from dnd_app.core.builder import (
    get_choices_needed, apply_choice, rebuild,
    get_background_skills, get_race_skills, get_race_asi,
)
from dnd_app.core.calculator import resolve_stat_placeholders
from dnd_app.ui_desktop import icons as _icons
from dnd_app.core.choices import (
    ALL_SKILLS, LANGUAGES, feat_prereq_met,
    _get_subclass_choices, _get_feat_choices, _get_optional_feature_choices,
    _get_race_choices, _get_class_tool_choices, _get_dm_reward_choices,
)

ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]


def _lbl(text, color=TEXT, bold=False, size=FS_BODY, align=Qt.AlignLeft, wrap=True):
    # Thin wrapper, not a straight alias: this file's own (bold, size)
    # positional order is swapped from shared.py's h() (size, bold) —
    # at least one call site here relies on that exact order — so a
    # direct `_lbl = h` would silently reinterpret an existing
    # positional call's arguments. Delegating still removes the
    # duplicate QLabel-building logic without touching any call site.
    return _h(text, color, size, bold, align, wrap)


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

        # Built fresh per widget, not a module-level dict: a dict literal
        # at module scope is evaluated exactly once, at this module's
        # first import, so it would freeze to whichever theme was active
        # at app startup and never pick up a later theme switch.
        source_colors = {"race": TEAL2, "background": GOLD, "class": IND2, "subclass": PURP2}
        bg = source_colors.get(choice_info.get("source", "class"), IND2)
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
        head.addWidget(_lbl(choice_info["label"], TEXT, bold=True, size=FS_LABEL), 1)
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
        elif ctype in ("skill_or_tool_prof", "weapon_or_tool_prof"):
            self._build_tool_chooser()  # generic checkbox-from-pool behavior works for a mixed pool too
        elif ctype == "language":
            self._build_language_chooser()
        elif ctype == "asi_or_feat":
            self._build_asi_chooser()
        elif ctype in ("asi", "feat"):
            # one half of an ASI-or-feat pick on its own: a Variant Human's
            # two +1s or its feat, a dragonmark's +1 (one point, not to the
            # ability its +2 went to)
            self._asi_points = choice_info.get("points", 2)
            self._build_asi_chooser()
            for ab in choice_info.get("exclude") or []:
                self._asi_ctrls[ab].setEnabled(False)
            self._asi_type.setCurrentText("+1 to two abilities" if ctype == "asi" else "Take a Feat")
            self._asi_type.hide()
            self._asi_total.setVisible(ctype == "asi")
            if choice_info.get("max_per"):        # Fizban's dragonborn: +2/+1 or three +1s
                for sp in self._asi_spins.values():
                    sp.setRange(0, choice_info["max_per"])
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
            base_ss = _btn("", bg, variant="cta", radius=8, bg_alpha=0x22,
                            hover_text="white", font_size=FS_BODY, padding="6px 14px").styleSheet()
            # The shared factory's normal hover rule fires even while
            # disabled; split it into ":hover:enabled" here to preserve
            # this button's own disabled-state styling, which _btn()
            # doesn't model.
            base_ss = base_ss.replace("QPushButton:hover{", "QPushButton:hover:enabled{")
            self._confirm_btn.setStyleSheet(
                base_ss + f"QPushButton:disabled{{background:{SURF};color:{TEXT3};border-color:{BORDER};}}")
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
            # a rogue's thieves' tools can take the place of one skill
            pool += list(self.choice_info.get("extra_pool") or [])
        else:
            raw_pool = explicit_pool or ALL_SKILLS
            # If pool is a placeholder like ['Any 3 skills'], use full skill list
            if len(raw_pool)==1 and 'any' in str(raw_pool[0]).lower():
                pool = ALL_SKILLS
            else:
                pool = raw_pool
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMinimumHeight(100)
        scroll.setStyleSheet(f"QScrollArea{{background:transparent;border:1px solid {BORDER};border-radius:4px;}}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;border:none;")
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
        # Also gray out weapons the character is already proficient with —
        # relevant when this pool is a mixed weapon-or-tool pool (see
        # weapon_or_tool_prof), harmless for tool-only pools since weapon
        # names never appear in them.
        current_tools = set(self.char.get("tool_proficiencies", [])) | set(self.char.get("weapon_proficiencies", []))

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMinimumHeight(140)
        scroll.setStyleSheet(f"QScrollArea{{background:transparent;border:1px solid {BORDER};border-radius:4px;}}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;border:none;")
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
        # Same rule as the generic checkbox handler (_on_check) below:
        # reaching the required count only ENABLES the Confirm button for
        # a multi-select chooser -- it doesn't submit on its own. Only a
        # genuinely single-item choice (_count == 1) has nothing left to
        # confirm, so that's the only case that auto-submits.
        if self._confirm_btn:
            self._confirm_btn.setEnabled(len(self._selected) >= self._count)
        if self._count == 1 and len(self._selected) == 1:
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
        # Same rule as _on_check/_on_tool_check: only a single-language
        # choice has nothing left to confirm and can auto-submit; a
        # multi-language choice just enables Confirm.
        if self._confirm_btn:
            self._confirm_btn.setEnabled(len(sel) >= self._count)
        if self._count == 1 and len(sel) == 1:
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

        self._asi_frame = QWidget(); self._asi_frame.setStyleSheet("background:transparent;border:none;")
        asf = QGridLayout(self._asi_frame)
        asf.setSpacing(4); asf.setContentsMargins(0,0,0,0)
        self._asi_spins = {}; self._asi_mod_lbls = {}; self._asi_ctrls = {}

        for col_i, ab in enumerate(ABILITIES):
            asf.addWidget(_lbl(ab, TEXT3, bold=True, size=FS_SMALL, align=Qt.AlignCenter), 0, col_i)

            # Live score + modifier preview (updates as user clicks +/-)
            cur_score = _as(self.char, ab) if self.char else 10
            cur_mod   = _am(self.char, ab) if self.char else 0
            sign = "+" if cur_mod >= 0 else ""
            mod_lbl = QLabel(f"{cur_score}\n({sign}{cur_mod})")
            mod_lbl.setAlignment(Qt.AlignCenter)
            mod_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:600;background:transparent;border:none;")
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

            ctrl_w = QWidget(); ctrl_w.setStyleSheet("background:transparent;border:none;")
            ctrl_lay = QHBoxLayout(ctrl_w)
            ctrl_lay.setContentsMargins(0,0,0,0); ctrl_lay.setSpacing(2)
            ctrl_lay.addWidget(minus); ctrl_lay.addWidget(val_lbl); ctrl_lay.addWidget(plus)
            asf.addWidget(ctrl_w, 2, col_i)
            self._asi_ctrls[ab] = ctrl_w

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
        self._feat_frame = QWidget(); self._feat_frame.setStyleSheet("background:transparent;border:none;")
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
        # a feat already picked (the choice reopened) shows selected, without
        # picking it again
        for item in self._selected:
            if item.startswith("feat:"):
                found = self._feat_list.findItems(item.split(":", 1)[1], Qt.MatchExactly)
                if found:
                    self._feat_list.blockSignals(True)
                    self._feat_list.setCurrentItem(found[0])
                    self._feat_list.blockSignals(False)
        ff.addStretch()
        self._feat_frame.setVisible(False)
        self._lay.addWidget(self._feat_frame)

        # Points remaining label
        self._asi_total = _lbl(f"Points: 0/{getattr(self, '_asi_points', 2)}", TEXT2, size=FS_SMALL, bold=True)
        self._asi_total.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:700;background:transparent;border:none;")
        self._lay.addWidget(self._asi_total)

        self._asi_type.currentTextChanged.connect(self._on_asi_type)

    def _on_feat_list_changed(self, feat_name: str):
        """
        Called when user selects a feat from the searchable list. What the
        choice keeps -- "feat:Name" and the feat's own ability increase
        ("asi:CON:1", which rebuild() reads from any _choices list) -- and
        what the pick decides (Resilient's save, Elemental Adept's type)
        come from core/builder.py feat_choice_picks, the same on Android;
        this only asks the questions it raises.
        """
        if not feat_name:
            return
        from dnd_app.core.builder import feat_choice_picks
        answers = {}
        while True:
            res = feat_choice_picks(self.char, feat_name, answers)
            ask = res.get("ask")
            if not ask:
                break
            pick = self._prompt_feat_ability_choice(feat_name, ask["options"], ask["title"])
            if not pick:
                return            # closed without picking: the feat isn't taken
            answers[ask["key"]] = pick
        self._selected = list(res["picks"])
        self._set_confirmed()

        # Notify parent via the same signal other choices use
        if hasattr(self, "choice_confirmed"):
            self.choice_confirmed.emit(self.choice_info["id"], self._selected)

    def _prompt_feat_ability_choice(self, feat_name: str, options: list, question: str = "") -> str | None:
        """Small dialog letting the player pick what a feat asks: which
        ability gets its +1, Elemental Adept's damage type."""
        dlg = QDialog(self)
        dlg.setWindowTitle(feat_name)
        dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg); lay.setSpacing(10)
        lay.addWidget(_lbl(
            question or f"{feat_name} grants +1 to one ability score. Which one?",
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
        self._asi_total.setText(f"Points: 0/{getattr(self, '_asi_points', 2)}")
        self._asi_total.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:700;background:transparent;border:none;")
        # Reset modifier labels to base scores
        from dnd_app.core.character import ability_score as _as, ability_mod as _am
        if hasattr(self, "_asi_mod_lbls") and self.char:
            for ab, mod_lbl in self._asi_mod_lbls.items():
                sc = _as(self.char, ab); md = _am(self.char, ab)
                sign = "+" if md >= 0 else ""
                mod_lbl.setText(f"{sc}\n({sign}{md})")
                mod_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;font-weight:600;background:transparent;border:none;")

    def _on_asi_spin(self):
        # Legacy signal from hidden QSpinBox — delegate to manual handler
        self._on_asi_spin_manual(None, None)

    def _on_asi_spin_manual(self, changed_ab=None, new_val=None):
        from dnd_app.core.character import ability_score as _as
        asi_text = self._asi_type.currentText() if hasattr(self, "_asi_type") else "+2 to one ability"
        is_plus2_one = "+2 to one" in asi_text
        max_pts = getattr(self, "_asi_points", 2)
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
        self._asi_total.setStyleSheet(f"color:{color};font-size:{FS_SMALL}px;font-weight:700;background:transparent;border:none;")
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
                mod_lbl.setStyleSheet(f"color:{fg};font-size:{FS_SMALL}px;font-weight:{fw};background:transparent;border:none;")
        # Store selection
        vals = {ab: sp.value() for ab, sp in self._asi_spins.items() if sp.value() > 0}
        self._selected = [f"asi:{ab}:{v}" for ab, v in vals.items()]
        # Auto-confirm when points filled
        if total == max_pts:
            self._set_confirmed()
            self.choice_confirmed.emit(self.choice_info["id"], list(self._selected))


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
        # search + list in one box; the level filter slides in over the
        # box's right side from the funnel button
        ms_box = QWidget(); ms_lay = QVBoxLayout(ms_box)
        ms_lay.setContentsMargins(0, 0, 0, 0); ms_lay.setSpacing(6)
        self._ms_search = QLineEdit(); self._ms_search.setPlaceholderText("Search spells…")
        self._ms_lvl_f = QComboBox()
        self._ms_lvl_f.addItem("All Levels")
        for i in range(10): self._ms_lvl_f.addItem("Cantrip" if i==0 else f"Level {i}")
        from ..widgets import FilterSidebar
        self._ms_filters = FilterSidebar(ms_box)
        self._ms_filters.add_combo("Level", self._ms_lvl_f)
        ms_lay.addLayout(self._ms_filters.search_row(self._ms_search))

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
        ms_lay.addWidget(self._ms_list)
        ms_lay.addStretch(1)   # any spare height goes under the list, not above it
        self._lay.addWidget(ms_box)
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
        # Same rule as _on_check/_on_tool_check/_on_lang_change: Magical
        # Secrets is a multi-select choice (2+ spells) so reaching the
        # count only enables Confirm, it doesn't submit on its own.
        if self._confirm_btn:
            self._confirm_btn.setEnabled(len(sel) >= self._count)
        if self._count == 1 and len(sel) == 1:
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
        race_skills = get_race_skills(race, char.get("subrace", "")) if race else []
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
            row_frame = QFrame(); row_frame.setStyleSheet("background:transparent;border:none;")
            rl = QHBoxLayout(row_frame); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
            badge = _lbl(source, "white", bold=True, size=FS_TINY, align=Qt.AlignCenter, wrap=False)
            badge.setFixedHeight(16)
            badge.setStyleSheet(f"color:white;font-size:{FS_TINY}px;font-weight:700;background:{color};"
                                f"border-radius:8px;padding:1px 6px;")
            rl.addWidget(badge)
            # the description takes the rest of the row (wrapping only when
            # it really runs out of room)
            rl.addWidget(_lbl(desc, TEXT2, size=FS_BODY), 1)
            self._outer.addWidget(row_frame)


# ═══════════════════════════════════════════════════════════════════
#  LEVEL-UP PANEL
# ═══════════════════════════════════════════════════════════════════
class LevelUpPanel(QWidget):
    choices_changed = Signal()
    # Unfinished-choice count after each refresh (the same number the
    # "PENDING CHOICES (N remaining)" header shows) -- drives the
    # character sheet's pulsing Choices tab.
    pending_count_changed = Signal(int)

    def __init__(self, char_ref, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self.char = char_ref
        self.pending_count = 0
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0,0,0,0)
        self._outer.setSpacing(8)

        self._grants = GrantsSummaryWidget(char_ref)
        self._outer.addWidget(self._grants)

        # ── Features timeline ─────────────────────────────────────────────
        self._features_hdr = _lbl("CLASS FEATURES BY LEVEL", IND2, bold=True, size=FS_LABEL)
        self._outer.addWidget(self._features_hdr)
        # as tall as the list, up to 340px -- past that it scrolls
        feat_scroll = QScrollArea(); feat_scroll.setWidgetResizable(True)
        feat_scroll.setMaximumHeight(340)
        self._feat_scroll = feat_scroll
        feat_scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:1px solid {BORDER};border-radius:6px;}}")
        feat_inner = QWidget(); feat_inner.setStyleSheet(f"background:{BG};")
        self._feat_inner = feat_inner
        self._features_lay = QVBoxLayout(feat_inner)
        self._features_lay.setSpacing(2); self._features_lay.setContentsMargins(6,4,6,4)
        feat_scroll.setWidget(feat_inner)
        self._outer.addWidget(feat_scroll)

        self._pending_hdr = _lbl("CHOICES FOR THIS CHARACTER", AMBER, bold=True, size=FS_HEAD)
        self._outer.addWidget(self._pending_hdr)

        # One card per choice, at full height (the Choices tab itself
        # scrolls); hidden when there are none.
        self._choices_inner = QFrame()
        self._choices_inner.setObjectName("choicesBox")
        self._choices_inner.setStyleSheet(
            f"QFrame#choicesBox{{background:{BG};border:1px solid {BORDER};border-radius:8px;}}")
        self._choices_vl = QVBoxLayout(self._choices_inner)
        self._choices_vl.setSpacing(8)
        self._choices_vl.setContentsMargins(8, 8, 8, 8)
        self._outer.addWidget(self._choices_inner)

        self._no_choices = _lbl("✓  No pending choices — character fully configured.", TEAL2, size=FS_BODY)
        self._outer.addWidget(self._no_choices)
        self._refreshing = False
        self._choice_widgets = []
        self.refresh()

    def _refresh_features(self):
        """Rebuild the class features timeline."""
        from dnd_app.data.classes import CLASS_DICT
        from dnd_app.data.phb2024.classes_2024 import CLASS_DICT_2024
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
                    badge.setStyleSheet(f"color:{qa(color,0x55)};font-size:{FS_TINY}px;font-weight:700;background:transparent;border:none;")
                    badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    lbl = QLabel(f"▸ {resolve_stat_placeholders(fname, self.char)}")
                    lbl.setWordWrap(True)
                    lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;background:transparent;border:none;")
                    row.addWidget(badge); row.addWidget(lbl, 1)
                    w = QWidget(); w.setStyleSheet("background:transparent;border:none;"); w.setLayout(row)
                    self._features_lay.addWidget(w)
                for ch in cl:
                    row = QHBoxLayout(); row.setSpacing(6); row.setContentsMargins(8,1,4,1)
                    badge = QLabel(f"L{lvl}"); badge.setFixedWidth(26)
                    badge.setStyleSheet(f"color:{qa(AMBE2,0x55)};font-size:{FS_TINY}px;font-weight:700;background:transparent;border:none;")
                    badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    lbl = QLabel(ch); lbl.setWordWrap(True)
                    lbl.setStyleSheet(f"color:{AMBE2};font-size:{FS_SMALL}px;background:transparent;border:none;")
                    row.addWidget(badge); row.addWidget(_icons.icon_label("choices", 12)); row.addWidget(lbl, 1)
                    w = QWidget(); w.setStyleSheet("background:transparent;border:none;"); w.setLayout(row)
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
        if len(unfinished) != self.pending_count:
            self.pending_count = len(unfinished)
            self.pending_count_changed.emit(self.pending_count)

        self._choices_inner.setVisible(bool(pending))
        # the features list: as tall as it needs, up to its 340px cap
        self._feat_inner.adjustSize()
        self._feat_scroll.setMinimumHeight(min(340, self._feat_inner.sizeHint().height() + 4))

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
            # rebuild() can re-derive it, same pattern used for skills.
            choices = self.char["_choices"]
            all_tool_profs = []
            for k, v in choices.items():
                if k.endswith("_tool_profs") and isinstance(v, list):
                    all_tool_profs.extend(v)
            choices["tool_profs"] = list(set(all_tool_profs))

        # ── Expertise ─────────────────────────────────────────────────────
        elif "expertise" in choice_id:
            for skill in selected:
                if skill in self.char.get("skills", {}):   # a tool (Thieves' tools) isn't a skill
                    self.char["skills"][skill] = 3
            self.char.setdefault("_choices",{})[choice_id] = selected
            # Same pattern as "_skill_profs" above: aggregate into a
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
            # the shared rule (core/builder.py apply_choice, as Android): the
            # pick, and every language pick gathered into "extra_languages"
            # -- which rebuild() reads -- so a language changed or no longer
            # chosen goes too
            apply_choice(self.char, choice_id, selected)

        # ── ASI: store in _choices['asi_bonuses'] only, rebuild() applies ──

        elif choice_id.endswith("_asi_") or "asi_" in choice_id or choice_id in ("variant_human_asi",
                                                                                 "variant_human_feat",
                                                                                 "dragonmark_asi",
                                                                                 "race_flex_asi"):
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

        # ── Death Domain: Reaper bonus necromancy cantrip ───────────────────
        elif choice_id == "death_domain_reaper_cantrip":
            # Just record the pick — get_bonus_spells() reads it back in on
            # the rebuild() below, adding it to spells_known/spells_prepared
            # as a proper bonus spell (doesn't count against cantrip cap),
            # the same path every other domain's bonus spells use.
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
        # The sheet (and this panel) are rebuilt once the pick's own signal
        # has finished -- the language combo's, a box's, a radio's -- not in
        # the middle of it, while the widget that sent it is being torn down.
        QTimer.singleShot(0, self, self.choices_changed.emit)   # not if this panel's gone by then
        # Sheet observer handles refresh via ctrl.refresh() -> _levelup_panel.refresh()


