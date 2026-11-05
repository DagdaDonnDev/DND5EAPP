import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui_desktop.style.theme import *
from ..shared import *
# `import *` silently skips underscore-prefixed names when a module has no
# __all__ (shared.py doesn't) — _btn/_pill need an explicit import for that
# reason. _lbl/_card/_sep don't (they're defined a few lines down as local
# aliases to h/card/hline, which ARE plain names the wildcard import above
# already brought in).
from ..shared import _btn, _pill
# Local aliases matching the short names used throughout this file.
_lbl = h
_sep = hline
_card = card
from ..widgets import FlowLayout, FlowContainer
from dnd_app.core.character import (
    ability_score, ability_mod, total_level, class_levels, subclasses,
    long_rest, short_rest, add_class
)
from dnd_app.core.calculator import (
    update_all, get_ac, get_prof_bonus, get_initiative,
    all_skill_bonuses, all_saving_throw_bonuses, get_save_advantage_status,
    get_initiative_advantage_status, get_carry_capacity,
    get_spell_save_dc, get_spell_attack_bonus,
    get_passive_perception, get_sneak_attack, get_martial_arts_die,
    get_rage_damage, _detect_spell_ability, get_ac, has_reliable_talent,
    get_ac_breakdown, get_speed_breakdown, get_effective_speed,
    get_save_dc_breakdown, get_spell_attack_breakdown, get_weapon_attack_breakdown,
    get_onhit_damage_bonuses,
)
from dnd_app.core.multiclass import (
    compute_all_spell_slots, get_extra_attacks, aggregate_resources,
    compute_hit_points, get_saving_throw_profs
)
from dnd_app.core.builder import rebuild
from dnd_app.core.controller import CharacterController
from dnd_app.core.magic_items import concentration_save, start_concentration, drop_concentration
from dnd_app.core.spellcasting import spell_component_block_reason
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters, character_filename, validate_character,
)
from dnd_app.core.character import set_subclass, get_class_entry
from dnd_app.core.character import rest_options, rest_preview_lines, rest_activities, rest_extras
from dnd_app.data.magic_items import ALL_MAGIC_ITEMS, has_item_effect
from dnd_app.ui_desktop.dialogs.levelup_panel import LevelUpPanel
from dnd_app.data.classes import CLASS_DICT, CLASS_NAMES, BATTLE_MASTER_MANEUVERS, WILD_MAGIC_SURGE_TABLE
from dnd_app.data.races import get_race
from dnd_app.data.backgrounds import get_background
from dnd_app.data.feats import get_feat
from dnd_app.data.spells import get_spell, spells_for_class, ALL_SPELLS
from dnd_app.data.items import (ARMOR, ARMOR_DICT, ALL_WEAPONS, WEAPON_DICT,
    ADVENTURING_GEAR, GEAR_NAMES, MOUNTS, ALL_TOOLS, SIMPLE_MELEE, SIMPLE_RANGED,
    MARTIAL_MELEE, MARTIAL_RANGED, ARTISAN_TOOLS, SPECIAL_ARMOR)
from dnd_app.data.conditions import CONDITIONS
from dnd_app.ui_desktop import icons as _icons


class RestOptionsDialog(QDialog):
    """Unified rest-configuration dialog — shown after finishing a short
    or long rest, surfaces every "you can change X when you finish a
    rest" choice the character actually has, found by searching the
    game's own feature text for short/long rest + change/swap language.
    Extensible: add more entries to core/character.py's rest_options() as more of these
    get confirmed and wired up.

    Currently covers: unpreparing all spells to choose new ones (any
    prepared caster, long rest), and the Artificer Armorer's Arcane
    Armor model swap (short or long rest, smith's tools in hand)."""

    def __init__(self, char, rest_type, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        self.rest_type = rest_type  # "short" or "long"
        self.setWindowTitle(f"{'Long' if rest_type == 'long' else 'Short'} Rest Options")
        self.setMinimumSize(480, 300)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        self._options = rest_options(char, rest_type)
        self._checks = {}

        root = QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(10)
        root.addWidget(_lbl("Rest Options", GOLD2, FS_HEAD, bold=True))
        root.addWidget(_lbl(
            "Your character has features that can be reconfigured on this rest. "
            "Check anything you'd like to change now.",
            TEXT2, FS_SMALL, wrap=True))

        card = _card(qa(INDIGO,0x44)); card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(10,10,10,10); card_lay.setSpacing(6)
        for opt in self._options:
            cb = QCheckBox(opt["label"])
            cb.setToolTip(opt.get("detail", ""))
            card_lay.addWidget(cb)
            self._checks[opt["kind"]] = cb
        if not self._options:
            card_lay.addWidget(_lbl("Nothing reconfigurable on this character right now.", TEXT3, FS_SMALL))
        root.addWidget(card)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        skip_btn = QPushButton("Skip"); skip_btn.setFixedHeight(34)
        skip_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton("Apply Selected"); confirm_btn.setFixedHeight(34)
        confirm_btn.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2).styleSheet())
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(skip_btn); btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)


    def get_selected(self):
        return [kind for kind, cb in self._checks.items() if cb.isChecked()]


class RestDialog(QDialog):
    """One dialog for a rest, from the sheet's Rest button: Short or Long
    (a switch at the top), what it will restore, the hit dice to spend on
    a short rest, and anything this character can change on that rest
    (core/character.py's rest_options(): re-preparing spells, a pact
    weapon, an Armorer's model...). One Confirm does the lot; the sheet
    then applies it (_do_short_rest / _do_long_rest).

    `previews` is {"short": dict, "long": dict}, from the sheet's
    _preview_short_rest()/_preview_long_rest() -- plain filters over the
    character as it is, so they can't drift from what the rest does.
    `long_block` is why a long rest can't be taken now ("" if it can)."""

    def __init__(self, char: dict, previews: dict, rest_type: str = "short",
                 long_block: str = "", parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        self._previews = previews
        self._long_block = long_block
        self._checks = {}
        self._extras = {}          # key -> (its extra, its tick, its number box or None)
        self.setWindowTitle("Rest")
        self.setMinimumWidth(480)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        root = QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(12)
        root.addWidget(_icons.icon_header("long_rest", _lbl("Rest", GOLD2, FS_HEAD, bold=True),
                                          size=20, spacing=8))

        # Short or long: a two-way switch
        sw = QHBoxLayout(); sw.setSpacing(0)
        self._type_btns = {}
        for i, (kind, text, tip) in enumerate((
                ("short", "Short Rest  ·  1 hour", "At least an hour: spend hit dice, and "
                                                    "what comes back on a short rest does"),
                ("long", "Long Rest  ·  8 hours", "8 hours: all your HP and spell slots, up to "
                                                   "half your hit dice back, a level of exhaustion off"))):
            b = QPushButton(text); b.setCheckable(True)
            b.setToolTip(tip)
            _icons.set_button_icon(b, "short_rest" if kind == "short" else "long_rest", 15)
            left, right = (8, 0) if i == 0 else (0, 8)
            b.setStyleSheet(
                f"QPushButton{{background:{SURF};color:{TEXT2};border:2px solid {BORDER2};"
                f"border-top-left-radius:{left}px;border-bottom-left-radius:{left}px;"
                f"border-top-right-radius:{right}px;border-bottom-right-radius:{right}px;"
                f"font-size:{FS_SMALL}px;font-weight:700;padding:0px 14px;"
                f"min-height:32px;max-height:32px;}}"   # (36px with the border)
                f"QPushButton:checked{{background:{qa(GOLD,0x33)};color:{GOLD2};border-color:{GOLD};}}"
                f"QPushButton:disabled{{color:{TEXT3};}}")
            b.clicked.connect(lambda checked=False, k=kind: self._set_type(k))
            sw.addWidget(b, 1)
            self._type_btns[kind] = b
        if long_block:
            self._type_btns["long"].setEnabled(False)
            self._type_btns["long"].setToolTip(f"Can't take a long rest: {long_block}")
        root.addLayout(sw)
        self._block_lbl = _lbl(f"Can't take a long rest: {long_block}." if long_block else "",
                               CRIM2, FS_SMALL, wrap=True)
        self._block_lbl.setVisible(bool(long_block))
        root.addWidget(self._block_lbl)

        # The cards scroll, if there's more than the screen has room for (a
        # character with a lot to do on a long rest)
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self._body = QWidget(); self._body.setStyleSheet("background:transparent;")
        body = QVBoxLayout(self._body); body.setContentsMargins(0, 0, 6, 0); body.setSpacing(12)
        self._scroll.setWidget(self._body)
        root.addWidget(self._scroll, 1)

        # What it will do
        prev = _card(qa(TEAL,0x44)); pl = QVBoxLayout(prev)
        pl.setContentsMargins(14,12,14,14); pl.setSpacing(4)
        pl.addWidget(_lbl("WHAT THIS WILL DO", TEAL2, FS_SMALL, bold=True))
        self._preview_lbl = _lbl("", TEXT, FS_BODY, wrap=True)
        pl.addWidget(self._preview_lbl)
        body.addWidget(prev)

        # Hit dice to spend (a short rest)
        self._dice_card = _card(qa(GREEN,0x44)); dl = QVBoxLayout(self._dice_card)
        dl.setContentsMargins(14,12,14,14); dl.setSpacing(6)
        dl.addWidget(_lbl("SPEND HIT DICE", GREEN2, FS_SMALL, bold=True))
        from dnd_app.core.character import rest_dice_note
        note = rest_dice_note(char)      # (the same words as Android's)
        drow = QHBoxLayout(); drow.setSpacing(10)
        self._dice = QSpinBox(); self._dice.setRange(0, note["left"]); self._dice.setValue(0)
        self._dice.setAlignment(Qt.AlignCenter)
        self._dice.setAccessibleName("How many hit dice to spend")
        self._dice.setStyleSheet(stepper_qss())
        self._dice.setFixedWidth(120)
        self._dice.setEnabled(note["can_spend"])
        drow.addWidget(self._dice)
        drow.addWidget(_lbl(note["text"], TEXT2, FS_SMALL, wrap=True), 1)
        dl.addLayout(drow)
        # ...and what adds to the dice (Song of Rest, a Chef's food: yours,
        # or your party's), once there are dice to spend
        self._dice_extra_box = QWidget(); self._dice_extra_box.setStyleSheet("background:transparent;")
        self._dice_extra_lay = QVBoxLayout(self._dice_extra_box)
        self._dice_extra_lay.setContentsMargins(0, 4, 0, 0); self._dice_extra_lay.setSpacing(6)
        dl.addWidget(self._dice_extra_box)
        self._dice.valueChanged.connect(self._update_dice_extras)
        body.addWidget(self._dice_card)

        # Anything this character can change on the rest
        self._opt_card = _card(qa(INDIGO,0x44)); self._opt_lay = QVBoxLayout(self._opt_card)
        self._opt_lay.setContentsMargins(14,12,14,14); self._opt_lay.setSpacing(6)
        body.addWidget(self._opt_card)

        # Everything else the character can do on this rest: their own
        # features', feats', race's and items' (core's rest_activities), and
        # the rules everyone has (attuning to an item...)
        self._act_card = _card(qa(GOLD,0x33)); self._act_lay = QVBoxLayout(self._act_card)
        self._act_lay.setContentsMargins(14,12,14,14); self._act_lay.setSpacing(6)
        body.addWidget(self._act_card)
        body.addStretch(1)
        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        self._confirm = QPushButton(); self._confirm.setFixedHeight(34)
        self._confirm.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2).styleSheet())
        self._confirm.clicked.connect(self.accept)
        self._confirm.setDefault(True)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(self._confirm)
        root.addLayout(btn_row)

        self._set_type("long" if rest_type == "long" and not long_block else "short")

    def _set_type(self, kind: str):
        self.rest_type = kind
        for k, b in self._type_btns.items():
            b.setChecked(k == kind)
        self._preview_lbl.setText("\n".join(
            rest_preview_lines(kind, self._previews[kind], dice_below=True)))
        self._dice_card.setVisible(kind == "short")
        # the options for this rest (rebuilt: some are long-rest only)
        while self._opt_lay.count():
            w = self._opt_lay.takeAt(0).widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        self._checks = {}
        self._extras = {}
        options = rest_options(self.char, kind)
        extras = rest_extras(self.char, kind)
        rest_own = [e for e in extras if e["group"] == "rest" and not e["party"]]
        rest_party = [e for e in extras if e["group"] == "rest" and e["party"]]
        if options or rest_own or rest_party:
            self._opt_lay.addWidget(_lbl("ALSO ON THIS REST", IND2, FS_SMALL, bold=True))
            self._opt_lay.addWidget(_lbl("Tick anything you'd like as part of it.",
                                         TEXT3, FS_TINY, wrap=True))
            for opt in options:
                cb = QCheckBox(opt["label"])
                cb.setToolTip(opt.get("detail", ""))
                self._opt_lay.addWidget(cb)
                self._checks[opt["kind"]] = cb
            for e in rest_own:
                self._add_extra(e, self._opt_lay)
            if rest_party:
                party = _lbl("FROM YOUR PARTY", TEXT3, FS_TINY, bold=True)
                party.setContentsMargins(0, 6, 0, 0)
                self._opt_lay.addWidget(party)
                for e in rest_party:
                    self._add_extra(e, self._opt_lay)
        self._opt_card.setVisible(bool(options or rest_own or rest_party))
        # what adds to the hit dice (a short rest's)
        while self._dice_extra_lay.count():
            w = self._dice_extra_lay.takeAt(0).widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        for e in extras:
            if e["group"] == "dice":
                self._add_extra(e, self._dice_extra_lay)
        self._dice_extra_box.setVisible(self._dice.isEnabled() and any(e["group"] == "dice" for e in extras))
        self._update_dice_extras()
        # ...and everything else they can do on it
        while self._act_lay.count():
            w = self._act_lay.takeAt(0).widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        import html
        acts = rest_activities(self.char, kind)
        if acts:
            self._act_lay.addWidget(_lbl("YOU CAN ALSO", GOLD2, FS_SMALL, bold=True))
            for a in acts:
                line = _lbl(f"<b>{html.escape(a['source'])}</b> — {html.escape(a['text'])}",
                            TEXT, FS_SMALL, wrap=True)
                line.setTextFormat(Qt.RichText)
                self._act_lay.addWidget(line)
        self._act_card.setVisible(bool(acts))
        self._confirm.setText("Take a Short Rest" if kind == "short" else "Take a Long Rest")
        # all of it in view when the screen has room; a scroll when it hasn't
        self._body.adjustSize()
        screen = self.screen().availableGeometry().height() if self.screen() else 800
        self._scroll.setMinimumHeight(min(self._body.sizeHint().height(), max(240, screen - 260)))
        self.adjustSize()

    def _add_extra(self, e: dict, lay):
        """One extra (core's rest_extras) as a tick; one that needs a number
        (a die they rolled, an ally's temporary hit points) opens a box for
        it once ticked."""
        box = QWidget(); box.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(box); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(4)
        cb = QCheckBox(e["label"]); cb.setToolTip(e.get("detail", ""))
        cb.setChecked(bool(e.get("checked")))
        bl.addWidget(cb)
        spin = None
        if e.get("ask"):
            row = QWidget(); row.setStyleSheet("background:transparent;")
            rl = QHBoxLayout(row); rl.setContentsMargins(26, 0, 0, 0); rl.setSpacing(8)
            rl.addWidget(_lbl("You rolled" if e["ask"] == "rolled" else "How many?", TEXT2, FS_SMALL))
            spin = QSpinBox()
            spin.setRange(1 if e["ask"] == "rolled" else 0, e.get("max") or 99)
            spin.setValue(1 if e["ask"] == "rolled" else 0)
            spin.setAlignment(Qt.AlignCenter); spin.setFixedWidth(110)
            spin.setStyleSheet(stepper_qss())
            spin.setAccessibleName(e["label"] + (": what you rolled" if e["ask"] == "rolled" else ": how many"))
            rl.addWidget(spin)
            if e["ask"] == "rolled":
                rl.addWidget(_lbl("(d6 to d12, by their level)" if e["key"] == "ally_song_of_rest"
                                  else f"(1\u2013{e.get('max')})", TEXT3, FS_TINY))
            rl.addStretch(1)
            row.setVisible(cb.isChecked())
            cb.toggled.connect(row.setVisible)
            cb.toggled.connect(lambda *_: QTimer.singleShot(0, self._refit))
            bl.addWidget(row)
        lay.addWidget(box)
        self._extras[e["key"]] = (e, cb, spin)

    def _update_dice_extras(self, *_):
        """What adds to the hit dice only counts when some are spent."""
        on = self._dice.value() > 0
        for e, cb, spin in self._extras.values():
            if e["group"] == "dice":
                cb.setEnabled(on)
                cb.setToolTip(e.get("detail", "") if on else "Spend at least one Hit Die for this.")

    def _refit(self):
        self._body.adjustSize()
        screen = self.screen().availableGeometry().height() if self.screen() else 800
        self._scroll.setMinimumHeight(min(self._body.sizeHint().height(), max(240, screen - 260)))
        self.adjustSize()

    def get_selected(self):
        return [kind for kind, cb in self._checks.items() if cb.isChecked()]

    def get_extras(self) -> dict:
        """{key: the number in its box, or True} for every extra ticked --
        those that add to the hit dice only when some are spent."""
        out = {}
        for key, (e, cb, spin) in self._extras.items():
            if not cb.isChecked() or (e["group"] == "dice" and not self.dice_to_spend()):
                continue
            out[key] = spin.value() if spin is not None else True
        return out

    def dice_to_spend(self) -> int:
        return self._dice.value() if self.rest_type == "short" and self._dice.isEnabled() else 0
