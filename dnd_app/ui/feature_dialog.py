"""
Feature Detail & Configuration Dialog.
Opens when a user clicks a feature card.
Shows full description + any interactive choices (ASI, expertise, spell selection, etc.)

Author: Ethan O'Brien
Date: 2026-08-20
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from .theme import *
from dnd_app.data.feature_ui_interactions import get_feature_config, SKILLS, TOOLS, LANGUAGES, ABILITIES

def _lbl(text, color=None, bold=False, size=11):
    w = QLabel(text)
    c = color or TEXT
    s = f"color:{c};font-size:{size}px;"
    if bold: s += "font-weight:700;"
    w.setWordWrap(True); w.setStyleSheet(s); return w


class FeatureDialog(QDialog):
    """Dialog shown when user clicks a feature card. Handles all choice types."""

    choices_saved = Signal(str, dict)  # (feature_key, choices_dict)

    def __init__(self, feature_name: str, char: dict, parent=None):
        super().__init__(parent)
        self.feature_name = feature_name
        self.char = char
        self.cfg = get_feature_config(feature_name)
        self._choice_widgets = {}

        self.setWindowTitle(feature_name)
        self.setMinimumSize(520, 400)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        lay = QVBoxLayout(self)
        lay.setSpacing(10); lay.setContentsMargins(16,16,16,16)

        # Title
        title = QLabel(feature_name)
        f = QFont(); f.setBold(True); f.setPointSize(14)
        title.setFont(f); title.setStyleSheet(f"color:{GOLD2};")
        lay.addWidget(title)

        # Description
        if self.cfg:
            desc = self.cfg.get("desc","")
        else:
            desc = f"Feature: {feature_name}\n\nNo additional configuration available for this feature."
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color:{TEXT2};font-size:11px;background:{SURF2};"
                                f"border-radius:6px;padding:8px;border:1px solid {BORDER};")
        lay.addWidget(desc_lbl)

        # Choice UI
        if self.cfg:
            ct = self.cfg.get("choice_type","info")
            if ct == "asi":
                self._build_asi_ui(lay)
            elif ct == "expertise":
                self._build_multi_choice_ui(lay, "Expertise", self.cfg.get("pool", SKILLS), self.cfg.get("count",2))
            elif ct == "proficiency":
                self._build_multi_choice_ui(lay, "Proficiency", self.cfg.get("pool", SKILLS), self.cfg.get("count",1))
            elif ct == "language":
                self._build_multi_choice_ui(lay, "Language", LANGUAGES, self.cfg.get("count",1))
            elif ct == "damage_type":
                self._build_single_choice_ui(lay, "Damage Type", self.cfg.get("options",[]))
            elif ct in ("spell_grant", "spell_grant_choose"):
                self._build_spell_grant_ui(lay)
            elif ct == "spell_choose":
                self._build_spell_choose_ui(lay)

        # Load existing choices
        key = self.cfg.get("key","") if self.cfg else ""
        existing = char.get("feature_choices",{}).get(key, {})
        self._load_existing(existing)

        # Buttons
        btn_box = QDialogButtonBox()
        save_btn = btn_box.addButton("Save Choices", QDialogButtonBox.AcceptRole)
        close_btn = btn_box.addButton("Close", QDialogButtonBox.RejectRole)
        save_btn.setStyleSheet(f"QPushButton{{background:{INDIGO};border:none;border-radius:5px;color:white;font-weight:700;padding:6px 16px;}}QPushButton:hover{{background:{IND2};}}")
        close_btn.setStyleSheet(f"QPushButton{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;color:{TEXT};padding:6px 16px;}}QPushButton:hover{{background:{SURF3};}}")
        btn_box.accepted.connect(self._save_and_close)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def _build_asi_ui(self, lay):
        grp = QGroupBox("Ability Score Improvement")
        gl = QGridLayout(grp); gl.setSpacing(8)
        self._asi_spins = {}
        points = self.cfg.get("points", 2)
        gl.addWidget(_lbl(f"Distribute {points} point(s) across abilities (max +2 per ability):", GOLD, bold=True), 0, 0, 1, 6)
        for i, ab in enumerate(ABILITIES):
            gl.addWidget(_lbl(ab, TEXT2, bold=True, size=10), 1, i)
            sp = QSpinBox(); sp.setRange(-2, 2); sp.setValue(0); sp.setFixedWidth(52)
            sp.setStyleSheet(f"color:{TEAL2};font-weight:700;font-size:13px;")
            sp.valueChanged.connect(self._update_asi_total)
            gl.addWidget(sp, 2, i)
            self._asi_spins[ab] = sp
        self._asi_total_lbl = _lbl(f"Points used: 0 / {points}", TEXT2)
        gl.addWidget(self._asi_total_lbl, 3, 0, 1, 6)
        lay.addWidget(grp)
        self._choice_widgets["asi"] = self._asi_spins

    def _update_asi_total(self):
        points = self.cfg.get("points", 2)
        total = sum(sp.value() for sp in self._asi_spins.values())
        color = TEAL2 if total <= points else CRIM2
        self._asi_total_lbl.setText(f"Points used: {total} / {points}")
        self._asi_total_lbl.setStyleSheet(f"color:{color};font-size:11px;")

    def _build_multi_choice_ui(self, lay, label, pool, count):
        grp = QGroupBox(f"Choose {count}")
        gl = QVBoxLayout(grp)
        gl.addWidget(_lbl(f"Select {count} option(s):", GOLD, bold=True))
        self._check_pool = {}
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMaximumHeight(200)
        inner = QWidget(); inner_lay = QGridLayout(inner); inner_lay.setSpacing(3)
        for i, item in enumerate(pool):
            cb = QCheckBox(item)
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:10px;}}")
            cb.stateChanged.connect(lambda s, n=count: self._enforce_limit(n))
            inner_lay.addWidget(cb, i//2, i%2)
            self._check_pool[item] = cb
        scroll.setWidget(inner); gl.addWidget(scroll)
        self._multi_count = count
        lay.addWidget(grp)
        self._choice_widgets["multi"] = self._check_pool

    def _enforce_limit(self, max_count):
        checked = [k for k,cb in self._check_pool.items() if cb.isChecked()]
        if len(checked) > max_count:
            # Uncheck the last one that was just checked (find it and uncheck)
            for k, cb in self._check_pool.items():
                if cb.isChecked() and k not in checked[:max_count]:
                    cb.blockSignals(True); cb.setChecked(False); cb.blockSignals(False)
                    break

    def _build_single_choice_ui(self, lay, label, options):
        grp = QGroupBox(label)
        gl = QVBoxLayout(grp)
        self._radio_group = QButtonGroup(self)
        for opt in options:
            rb = QRadioButton(opt)
            rb.setStyleSheet(f"color:{TEXT};font-size:11px;")
            gl.addWidget(rb); self._radio_group.addButton(rb)
        lay.addWidget(grp)
        self._choice_widgets["single"] = self._radio_group

    def _build_spell_grant_ui(self, lay):
        """Show spells that will be automatically granted."""
        ct = self.cfg.get("choice_type","")
        granted = self.cfg.get("granted",[]) or self.cfg.get("spells",[])
        choose_count = self.cfg.get("choose_count", 0)

        if granted:
            grp = QGroupBox("Spells Granted Automatically")
            gl = QVBoxLayout(grp)
            for sp_name in granted:
                row = QHBoxLayout()
                row.addWidget(_lbl(f"✓  {sp_name}", TEAL2, bold=True))
                gl.addLayout(row)
            apply_btn = QPushButton("Add these spells to my spell list →")
            apply_btn.setStyleSheet(f"QPushButton{{background:{TEAL};border:none;border-radius:5px;color:white;font-weight:700;padding:5px 12px;}}QPushButton:hover{{background:{TEAL2};}}")
            apply_btn.clicked.connect(lambda: self._apply_granted_spells(granted))
            gl.addWidget(apply_btn)
            lay.addWidget(grp)

        if choose_count > 0:
            self._build_spell_choose_ui(lay)

    def _apply_granted_spells(self, spell_names):
        from dnd_app.data.spells import get_spell
        added = []
        for name in spell_names:
            if name not in self.char.get("spells_known",[]):
                sp = get_spell(name)
                if sp:
                    self.char.setdefault("spells_known",[]).append(name)
                    added.append(name)
        if added:
            QMessageBox.information(self, "Spells Added",
                f"Added to your spell list:\n" + "\n".join(f"• {n}" for n in added) +
                "\n\nThey will appear in the Spells tab after saving.")
        else:
            QMessageBox.information(self, "Already Added", "These spells are already on your spell list.")

    def _build_spell_choose_ui(self, lay):
        from dnd_app.data.spells import ALL_SPELLS
        grp = QGroupBox(f"Choose Spells ({self.cfg.get('choose_count', self.cfg.get('count',1))} spell(s))")
        gl = QVBoxLayout(grp)
        # Filter controls
        frow = QHBoxLayout()
        self._sp_search = QLineEdit(); self._sp_search.setPlaceholderText("Search…")
        self._sp_cls_f  = QComboBox(); self._sp_cls_f.addItem("All Classes")
        for cn in ["Wizard","Cleric","Druid","Bard","Sorcerer","Warlock","Paladin","Ranger","Artificer"]:
            self._sp_cls_f.addItem(cn)
        frow.addWidget(self._sp_search,2); frow.addWidget(self._sp_cls_f)
        gl.addLayout(frow)

        self._spell_choose_list = QListWidget(); self._spell_choose_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self._spell_choose_list.setMaximumHeight(220)
        cls_f   = self.cfg.get("class_filter")
        lvl_f   = self.cfg.get("level_filter")
        sch_f   = self.cfg.get("school_filter")
        for s in ALL_SPELLS:
            if lvl_f and s["level"] not in lvl_f: continue
            if cls_f and not any(c.startswith(cls_f[:3]) for c in s.get("classes",[])): continue
            if sch_f and s.get("school") not in sch_f: continue
            lvl_txt = "C" if s["level"]==0 else str(s["level"])
            item = QListWidgetItem(f"  {lvl_txt}  {s['name']}  [{s['school'][:3]}]")
            item.setData(Qt.UserRole, s["name"])
            self._spell_choose_list.addItem(item)

        # Filter live
        def _filter():
            q = self._sp_search.text().lower(); cls = self._sp_cls_f.currentText()
            for i in range(self._spell_choose_list.count()):
                item = self._spell_choose_list.item(i); name = item.data(Qt.UserRole) or ""
                ok = (not q or q in name.lower())
                if cls != "All Classes":
                    from dnd_app.data.spells import get_spell
                    sp = get_spell(name)
                    ok = ok and sp and any(c.startswith(cls[:3]) for c in sp.get("classes",[]))
                item.setHidden(not ok)
        self._sp_search.textChanged.connect(_filter)
        self._sp_cls_f.currentTextChanged.connect(_filter)

        gl.addWidget(self._spell_choose_list)
        add_btn = QPushButton("Add selected spells to character")
        add_btn.setStyleSheet(f"QPushButton{{background:{INDIGO};border:none;border-radius:5px;color:white;font-weight:700;padding:5px 12px;}}QPushButton:hover{{background:{IND2};}}")
        add_btn.clicked.connect(self._add_chosen_spells)
        gl.addWidget(add_btn)
        lay.addWidget(grp)
        self._choice_widgets["spell_list"] = self._spell_choose_list

    def _add_chosen_spells(self):
        added = []
        for item in self._spell_choose_list.selectedItems():
            name = item.data(Qt.UserRole)
            if name and name not in self.char.get("spells_known",[]):
                self.char.setdefault("spells_known",[]).append(name)
                added.append(name)
        if added:
            QMessageBox.information(self,"Spells Added",
                "Added to your spell list:\n" + "\n".join(f"• {n}" for n in added) +
                "\n\nThey will appear in the Spells tab (reload character or restart).")

    def _load_existing(self, existing: dict):
        if not existing: return
        # ASI
        if "asi" in self._choice_widgets and "asi" in existing:
            for ab, val in existing["asi"].items():
                if ab in self._choice_widgets["asi"]:
                    self._choice_widgets["asi"][ab].blockSignals(True)
                    self._choice_widgets["asi"][ab].setValue(val)
                    self._choice_widgets["asi"][ab].blockSignals(False)
        # Multi-choice
        if "multi" in self._choice_widgets and "selected" in existing:
            for item in existing["selected"]:
                if item in self._choice_widgets["multi"]:
                    self._choice_widgets["multi"][item].setChecked(True)
        # Single / radio
        if "single" in self._choice_widgets and "selected" in existing:
            sel = existing["selected"]
            for btn in self._choice_widgets["single"].buttons():
                if btn.text() == sel:
                    btn.setChecked(True); break

    def _save_and_close(self):
        key = self.cfg.get("key","") if self.cfg else ""
        choices = {}
        ct = self.cfg.get("choice_type","info") if self.cfg else "info"

        if ct == "asi" and "asi" in self._choice_widgets:
            choices["asi"] = {ab: sp.value() for ab, sp in self._choice_widgets["asi"].items()}
            # Apply ASI to character ability_bonuses
            for ab, val in choices["asi"].items():
                self.char.setdefault("ability_bonuses",{ab:0 for ab in ABILITIES})[ab] += val
            QMessageBox.information(self,"ASI Applied",
                "Ability score improvements applied!\nNote: Bonuses stack — don't save twice for the same ASI.")

        elif ct in ("expertise","proficiency","language") and "multi" in self._choice_widgets:
            choices["selected"] = [k for k,cb in self._choice_widgets["multi"].items() if cb.isChecked()]
            # Apply expertise to skills
            if ct == "expertise":
                for skill_name in choices["selected"]:
                    if skill_name in self.char.get("skills",{}):
                        self.char["skills"][skill_name] = 3  # expertise level

        elif ct == "damage_type" and "single" in self._choice_widgets:
            for btn in self._choice_widgets["single"].buttons():
                if btn.isChecked():
                    choices["selected"] = btn.text(); break

        if key:
            self.char.setdefault("feature_choices",{})[key] = choices

        self.choices_saved.emit(key, choices)
        self.accept()
