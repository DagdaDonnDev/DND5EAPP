"""
Character Sheet module.

Main PySide6 widget shown after character creation or when loading a
saved character. Builds and refreshes every tab of the live sheet:
  1. Ability Scores & Saves
  2. Skills, Languages & Proficiencies
  3. Combat  (stats, HP, weapons, class abilities by recharge, favourited spells)
  4. Spells  (slots per class, DCs, spell list with modifiers)
  5. Features (by class + feats)
  6. Traits & Notes
Reads/writes the character dict directly and calls into
dnd_app.core.calculator/builder to recompute derived values whenever
the underlying data changes.

Author: Ethan O'Brien
Date: 2026-08-20
"""
import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from .theme import *
from .shared import *
from .widgets import FlowLayout, FlowContainer
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
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters, character_filename, validate_character,
)
from dnd_app.core.character import set_subclass, get_class_entry
from dnd_app.data.magic_items import ALL_MAGIC_ITEMS, has_item_effect
from dnd_app.ui.levelup_panel import LevelUpPanel
from dnd_app.data.classes import CLASS_DICT, CLASS_NAMES, BATTLE_MASTER_MANEUVERS, WILD_MAGIC_SURGE_TABLE
from dnd_app.data.races import get_race
from dnd_app.data.backgrounds import get_background
from dnd_app.data.feats import get_feat
from dnd_app.data.spells import get_spell, spells_for_class, ALL_SPELLS
from dnd_app.data.items import (ARMOR, ARMOR_DICT, ALL_WEAPONS, WEAPON_DICT,
    ADVENTURING_GEAR, GEAR_NAMES, MOUNTS, ALL_TOOLS, SIMPLE_MELEE, SIMPLE_RANGED,
    MARTIAL_MELEE, MARTIAL_RANGED, ARTISAN_TOOLS, SPECIAL_ARMOR)
from dnd_app.data.conditions import CONDITIONS

# Features that clearly require holding a holy symbol/spellcasting focus
# and/or speaking — the same standard the real Wild Shape rule applies to
# spellcasting itself ("you retain the benefit of any features... if the
# new form is physically capable of doing so"). This is deliberately a
# short, conservative list of clear-cut cases rather than an attempt to
# categorize every class feature in the game; anything not in this list
# is allowed by default, matching the rule's own default-allow framing.
# Matched as a substring against the feature's display name, lowercased.
WILDSHAPE_BLOCKED_FEATURES = {
    # Requires touching a creature/object with your hands. Not explicitly
    # addressed in the later, more detailed reference, so kept blocked on
    # the original reasoning (a beast's mouth/paws aren't hands) rather
    # than assumed to work without confirmation either way.
    "lay on hands",
    # Monk features requiring an unarmed strike specifically — natural
    # weapons are weapons, but they aren't unarmed strikes, so these
    # don't apply even though other Monk features (Unarmored Defense,
    # Slow Fall, Stillness of Mind, Evasion, etc.) work fine.
    "martial arts", "flurry of blows", "stunning strike",
    "ki-empowered strikes", "hands of harm", "open hand technique",
    "quivering palm", "touch of the long death", "drunken technique",
    "intoxicated frenzy", "radiant sun bolt", "searing arc strike",
    "searing sunburst", "sun shield",
    # Require actual arms to manifest
    "arms of the astral self", "visage of the astral self",
    "body of the astral self", "awakened astral self",
    # Require casting a spell or cantrip (or are themselves spellcasting).
    # NOTE: "disciple of life", "sacred weapon", "pact magic", and
    # "moon fire" were deliberately removed from this list — the app's
    # real subclass feature strings bundle these with a component that
    # explicitly works ("Sacred Weapon + Turn the Unholy",
    # "Lunar Embodiment + Moon Fire", "Otherworldly Patron + Pact Magic +
    # Rite Focus", "Bonus Proficiency (Heavy Armor) + Disciple of Life"),
    # and substring-blocking the whole bundle would incorrectly block the
    # working half too. The spellcasting half of each is already covered
    # by the separate _cast_spell gate regardless.
    "war magic", "eldritch strike", "spell thief", "magical ambush",
    "versatile trickster", "share spells", "misty wanderer",
    "fey reinforcements", "mystic frenzy", "revealed arcana",
    "unsealed arcana", "alchemical savant", "arcane firearm",
    "destructive wrath", "blessed healer", "reaper", "supreme healing",
    "grim harvest", "spell breaker",
    "circle of mortality", "voice of authority", "expert divination",
    "spell mastery", "signature spells", "arcane ward",
    "projected ward", "improved abjuration", "focused conjuration",
    "split enchantment", "alter memories", "sculpt spells",
    "potent cantrip", "empowered evocation", "overchannel",
    "power surge", "durable magic", "arcane abeyance", "gravity well",
    "awakened spellbook", "font of magic", "metamagic",
    "controlled chaos", "divine magic", "tempestuous magic",
    "clockwork magic", "psionic spells", "psionic sorcery",
    "eldritch master", "bonus cantrips",
    "grasping tentacles", "magical secrets", "additional magical secrets",
    "battle magic", "mantle of majesty", "mystic chronicle",
    "awakened spirit", "light bearer", "ritual caster",
    # Requires manifesting a weapon out of psychic energy
    "soul blades", "psychic blades",
    # Require a finesse or ranged weapon specifically (Sneak Attack) —
    # these all key off having Sneak Attack damage to add to/trigger from,
    # which natural weapons can never provide.
    "insightful fighting", "eye for weakness", "sudden strike",
    "wails from the grave", "death's friend",
    # Require a bow specifically
    "arcane shot", "magic arrow", "curving shot", "ever-ready shot",
    "kensei's shot",
}

ABILITIES = ["STR","DEX","CON","INT","WIS","CHA"]
AB_FULL   = {"STR":"Strength","DEX":"Dexterity","CON":"Constitution",
              "INT":"Intelligence","WIS":"Wisdom","CHA":"Charisma"}
SKILL_AB  = {"Acrobatics":"DEX","Animal Handling":"WIS","Arcana":"INT","Athletics":"STR",
             "Deception":"CHA","History":"INT","Insight":"WIS","Intimidation":"CHA",
             "Investigation":"INT","Medicine":"WIS","Nature":"INT","Perception":"WIS",
             "Performance":"CHA","Persuasion":"CHA","Religion":"INT",
             "Sleight of Hand":"DEX","Stealth":"DEX","Survival":"WIS"}
ALIGNMENTS = ["Lawful Good","Neutral Good","Chaotic Good","Lawful Neutral","True Neutral",
              "Chaotic Neutral","Lawful Evil","Neutral Evil","Chaotic Evil"]

def _lbl(text, color=TEXT, size=FS_BODY, bold=False, wrap=True, align=Qt.AlignLeft):
    w = QLabel(text); w.setWordWrap(wrap); w.setAlignment(align)
    w.setStyleSheet(f"color:{color};font-size:{size}px;background:transparent;{'font-weight:700;' if bold else ''}")
    return w

def _sep():
    f = QFrame(); f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background:{BORDER};max-height:1px;border:none;"); return f

def _card(accent=BORDER):
    f = QFrame(); f.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {accent};border-radius:10px;}}"); return f


# ═══════════════════════════════════════════════════════════════════
#  SLOT BAR — bubble checkboxes for spell slots
# ═══════════════════════════════════════════════════════════════════
class SlotBar(QWidget):
    """One row of spell-slot squares for a given level.

    Squares are uniformly blue (INDIGO/IND2) — filled = slot available,
    hollow (outline only) = slot spent. Click a square to toggle it (handy
    for manually correcting state); casting a spell fills them in from the
    left automatically via set_used().
    """
    changed = Signal()

    def __init__(self, level, parent=None, color=None):
        super().__init__(parent)
        self.level = level; self._max = 0
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        lname = "Cantrip" if level==0 else ("Pact" if level==-1 else f"Level {level}")
        self._lbl_w = _lbl(lname, TEXT2, FS_SMALL, bold=True, wrap=False)
        self._lbl_w.setFixedWidth(68); lay.addWidget(self._lbl_w)
        self._bubble_lay = QHBoxLayout(); self._bubble_lay.setSpacing(5)
        lay.addLayout(self._bubble_lay); lay.addStretch()
        self._count_lbl = _lbl("0/0", TEXT3, FS_SMALL, wrap=False); lay.addWidget(self._count_lbl)
        self.bubbles = []
        self._color = color or INDIGO   # blue by default; pact magic uses purple

    def _style_square(self, cb: "QCheckBox"):
        accent = IND2 if self._color == INDIGO else (PURP2 if self._color == PURPLE else self._color)
        cb.setStyleSheet(
            f"QCheckBox::indicator{{width:18px;height:18px;border-radius:3px;"
            f"border:2px solid {self._color};background:{self._color};}}"
            f"QCheckBox::indicator:checked{{background:transparent;border:2px solid {accent};}}"
            f"QCheckBox::indicator:hover{{border-color:{accent};}}"
        )

    def set_max(self, n):
        self._max = n
        while len(self.bubbles) < n:
            cb = QCheckBox()
            cb.setFixedSize(20,20)
            cb.setToolTip(f"{self._lbl_w.text()} slot — click to toggle spent/available")
            self._style_square(cb)
            cb.stateChanged.connect(self.changed)
            self._bubble_lay.addWidget(cb); self.bubbles.append(cb)
        while len(self.bubbles) > n:
            cb = self.bubbles.pop()
            self._bubble_lay.removeWidget(cb); cb.setParent(None); cb.deleteLater()
        self.setVisible(n > 0)
        self._update_count()

    # NOTE: checkbox "checked" = SPENT (hollow square); unchecked = available (filled).
    def get_used(self): return sum(1 for b in self.bubbles if b.isChecked())
    def set_used(self, n):
        for i,b in enumerate(self.bubbles):
            b.blockSignals(True); b.setChecked(i < n); b.blockSignals(False)
        self._update_count()

    def reset(self):
        for b in self.bubbles: b.blockSignals(True); b.setChecked(False); b.blockSignals(False)
        self._update_count()

    def _update_count(self):
        used = self.get_used(); rem = self._max - used
        self._count_lbl.setText(f"{rem}/{self._max}")
        self._count_lbl.setStyleSheet(f"color:{TEAL2 if rem>0 else TEXT3};font-size:{FS_SMALL}px;background:transparent;")


# ═══════════════════════════════════════════════════════════════════
#  RESOURCE WIDGET — use/restore buttons
# ═══════════════════════════════════════════════════════════════════
class ResourceWidget(QFrame):
    """
    Universal resource counter. Renders differently based on resource type:
      - 'info'         : label only (e.g. Martial Arts die = d6)
      - 'uses', max≤8  : pip bubbles (click to spend/restore)
      - 'uses', max>8  : +/- numeric counter
      - 'pool'  max≤12 : pip bubbles
      - 'pool'  max>12 : spinbox (e.g. Lay on Hands HP pool)
    Die type (if present) shown as a coloured badge next to the name.
    """
    def __init__(self, resource: dict, parent=None):
        super().__init__(parent)
        self.resource = resource

        reset = resource.get("reset", "LR")
        track = resource.get("track", "uses")
        # Normalise 'current_max' to 'pool' for display purposes
        if track == "current_max":
            track = "pool" 

        # Colour by reset type
        RESET_COLORS = {"SR": TEAL2, "LR": GOLD2, "SR/LR": IND2,
                        "Wild Shape use": PURP2, "uses_per_turn": AMBE2}
        color = RESET_COLORS.get(reset, GOLD2)

        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border:1px solid {qa(color,0x44)};"
            f"border-left:4px solid {color};border-radius:8px;}}"
        )
        outer = QVBoxLayout(self); outer.setContentsMargins(10,8,10,8); outer.setSpacing(6)

        # ── Header row: reset badge + name + die badge ─────────────────────
        header = QHBoxLayout(); header.setSpacing(8)

        reset_badge = _lbl(reset[:4], "white", FS_TINY, bold=True,
                           wrap=False, align=Qt.AlignCenter)
        reset_badge.setFixedSize(34, 20)
        reset_badge.setStyleSheet(
            f"background:{color};color:white;border-radius:10px;"
            f"font-size:{FS_TINY}px;font-weight:700;padding:0 4px;")
        header.addWidget(reset_badge)

        name_lbl = _lbl(resource["name"], TEXT, FS_BODY, bold=True, wrap=False)
        header.addWidget(name_lbl, 1)

        # Die badge (d6/d8/d10/d12)
        die = resource.get("die")
        if die:
            die_badge = _lbl(die, "white", FS_SMALL, bold=True,
                             wrap=False, align=Qt.AlignCenter)
            die_badge.setStyleSheet(
                f"background:{PURPLE};color:white;border-radius:4px;"
                f"font-size:{FS_SMALL}px;font-weight:700;padding:2px 6px;")
            header.addWidget(die_badge)

        # Source class badge
        src_cls = resource.get("source_class", "")
        if src_cls:
            src_badge = _lbl(src_cls[:5], TEXT3, FS_TINY, wrap=False)
            header.addWidget(src_badge)

        outer.addLayout(header)

        # ── Note ───────────────────────────────────────────────────────────
        note = resource.get("note", "")
        if note:
            outer.addWidget(_lbl(note, TEXT3, FS_SMALL, wrap=True))

        # ── Determine max ──────────────────────────────────────────────────
        raw_max = resource.get("current_max", resource.get("max", 1))
        self._unlimited = False
        self._info_value = None
        if isinstance(raw_max, str):
            low = raw_max.lower().strip()
            if low in ("unlimited", "∞", "—", "-"):
                self._unlimited = True; self._max = 999; track = "info"
            elif low and (low[0] in ('+', 'd') or not low.lstrip('-').isdigit()):
                # Info string like '+4', 'd6', '+2' — display-only
                self._info_value = raw_max; self._max = 0; track = "info"
            else:
                try: self._max = int(raw_max)
                except ValueError: self._max = 0
        else:
            self._max = int(raw_max) if raw_max is not None else 1

        raw_cur = resource.get("current", self._max)
        if isinstance(raw_cur, str):
            low_c = raw_cur.lower().strip()
            if low_c in ("unlimited", "∞"):
                raw_cur = 999
            else:
                try: raw_cur = int(raw_cur)
                except ValueError: raw_cur = self._max
        self._used = max(0, self._max - int(raw_cur)) if self._max > 0 else 0

        # ── Counter UI ─────────────────────────────────────────────────────
        self._bubbles = []
        self._counter_lbl = None
        self._spinbox = None

        if track == "info":
            if self._unlimited:
                outer.addWidget(_lbl("∞  Unlimited", TEAL2, FS_BODY, bold=True, wrap=False))
            elif self._info_value:
                val_lbl = _lbl(self._info_value, GOLD2, FS_STAT, bold=True,
                               align=Qt.AlignCenter, wrap=False)
                outer.addWidget(val_lbl)

        elif self._max > 0 and (track in ("uses", "pool")) and self._max <= 12:
            # Bubble pips
            bubble_row = QHBoxLayout(); bubble_row.setSpacing(4)
            for i in range(self._max):
                cb = QCheckBox()
                cb.setFixedSize(24, 24)
                cb.setChecked(i < self._used)
                cb.setStyleSheet(
                    f"QCheckBox::indicator{{width:22px;height:22px;border-radius:11px;"
                    f"border:2px solid {color};background:{BG};}}"
                    f"QCheckBox::indicator:checked{{background:{color};border-color:{color};}}"
                )
                cb.stateChanged.connect(self._on_bubble_change)
                bubble_row.addWidget(cb)
                self._bubbles.append(cb)
            self._counter_lbl = _lbl("", TEXT2, FS_SMALL, wrap=False)
            bubble_row.addSpacing(8); bubble_row.addWidget(self._counter_lbl)
            bubble_row.addStretch()
            outer.addLayout(bubble_row)

        elif self._max > 12 or track == "pool":
            # Spinbox for large pools (Lay on Hands HP, etc.)
            sp_row = QHBoxLayout(); sp_row.setSpacing(8)
            minus_btn = QPushButton("−"); minus_btn.setFixedSize(34, 34)
            minus_btn.setStyleSheet(
                f"QPushButton{{background:{qa(CRIMSON,0x44)};border:2px solid {CRIMSON};"
                f"border-radius:6px;color:{CRIM2};font-size:20px;font-weight:700;}}"
                f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
            self._spinbox = QSpinBox()
            self._spinbox.setRange(0, self._max)
            self._spinbox.setValue(max(0, self._max - self._used))
            self._spinbox.setAlignment(Qt.AlignCenter)
            self._spinbox.setFixedWidth(70)
            self._spinbox.setStyleSheet(
                f"QSpinBox{{font-size:{FS_TITLE}px;font-weight:700;color:{color};"
                f"border:2px solid {qa(color,0x55)};border-radius:6px;background:{SURF};padding:2px;}}")
            self._spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self._spinbox.valueChanged.connect(self._on_spinbox_change)
            plus_btn = QPushButton("+"); plus_btn.setFixedSize(34, 34)
            plus_btn.setStyleSheet(
                f"QPushButton{{background:{qa(TEAL,0x44)};border:2px solid {TEAL};"
                f"border-radius:6px;color:{TEAL2};font-size:20px;font-weight:700;}}"
                f"QPushButton:hover{{background:{TEAL};color:white;}}")
            max_lbl = _lbl(f"/ {self._max}", TEXT3, FS_BODY, wrap=False)
            minus_btn.clicked.connect(lambda: self._spinbox.setValue(max(0, self._spinbox.value()-1)))
            plus_btn.clicked.connect(lambda: self._spinbox.setValue(min(self._max, self._spinbox.value()+1)))
            sp_row.addWidget(minus_btn); sp_row.addWidget(self._spinbox)
            sp_row.addWidget(max_lbl); sp_row.addWidget(plus_btn); sp_row.addStretch()
            outer.addLayout(sp_row)

        else:
            # Numeric: Use / Restore buttons with counter display
            ctrl_row = QHBoxLayout(); ctrl_row.setSpacing(8)
            use_btn = QPushButton("Use"); use_btn.setFixedHeight(34)
            use_btn.setStyleSheet(
                f"QPushButton{{background:{qa(CRIMSON,0x44)};border:2px solid {CRIMSON};"
                f"border-radius:6px;color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:4px 14px;}}"
                f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
            use_btn.clicked.connect(self._use)
            self._counter_lbl = _lbl("", TEXT, FS_BODY, bold=True, wrap=False)
            rest_btn = QPushButton("↺"); rest_btn.setFixedSize(34, 34)
            rest_btn.setStyleSheet(
                f"QPushButton{{background:{qa(TEAL,0x44)};border:2px solid {TEAL};"
                f"border-radius:6px;color:{TEAL2};font-size:18px;}}"
                f"QPushButton:hover{{background:{TEAL};color:white;}}")
            rest_btn.clicked.connect(self._restore)
            ctrl_row.addWidget(use_btn); ctrl_row.addWidget(self._counter_lbl)
            ctrl_row.addStretch(); ctrl_row.addWidget(rest_btn)
            outer.addLayout(ctrl_row)

        self._sync()

    # ── State ─────────────────────────────────────────────────────────────
    def _on_bubble_change(self, _state):
        # Count checked bubbles = used count
        self._used = sum(1 for b in self._bubbles if b.isChecked())
        self._sync()

    def _on_spinbox_change(self, value):
        self._used = max(0, self._max - value)
        self._sync(update_spinbox=False)

    def _use(self):
        if self._used < self._max:
            self._used += 1; self._sync()

    def _restore(self):
        if self._used > 0:
            self._used -= 1; self._sync()

    def _sync(self, update_spinbox=True):
        rem = self._max - self._used
        self.resource["current"] = rem

        if self._bubbles:
            for i, b in enumerate(self._bubbles):
                b.blockSignals(True); b.setChecked(i < self._used); b.blockSignals(False)
            if self._counter_lbl:
                self._counter_lbl.setText(f"{rem}/{self._max}")
                c = TEAL2 if rem > 0 else TEXT3
                self._counter_lbl.setStyleSheet(
                    f"color:{c};font-size:{FS_SMALL}px;background:transparent;")

        elif self._spinbox and update_spinbox:
            self._spinbox.blockSignals(True)
            self._spinbox.setValue(rem)
            self._spinbox.blockSignals(False)

        elif self._counter_lbl:
            self._counter_lbl.setText(f"{rem} / {self._max}")
            c = TEAL2 if rem > 0 else TEXT3
            self._counter_lbl.setStyleSheet(
                f"color:{c};font-size:{FS_BODY}px;font-weight:700;background:transparent;")

    def restore_all(self):
        if not getattr(self, '_unlimited', False):
            self._used = 0; self._sync()


# ═══════════════════════════════════════════════════════════════════
#  CHARACTER SHEET
# ═══════════════════════════════════════════════════════════════════


# Action economy helpers live in ui/action_abilities.py
from dnd_app.ui.action_abilities import (
    build_action_abilities,
    _classify_action,
    _breath_weapon_desc,
    _resolve_dynamic_combat_text,
    _append_cantrip_scaling_note,
    _feature_matches_char_subclass,
)

class ArcaneRecoveryDialog(QDialog):
    """Lets a Wizard choose which expended spell slots to recover via
    Arcane Recovery — one spinbox per slot level (1-5, since level 6+
    slots can't be recovered this way), live-validating the total level
    spent against the budget (half Wizard level, rounded up)."""

    def __init__(self, char, budget, parent=None):
        super().__init__(parent)
        self.char = char
        self.budget = budget
        self.setWindowTitle("Arcane Recovery")
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        root = QVBoxLayout(self); root.setContentsMargins(18,16,18,16); root.setSpacing(8)
        root.addWidget(_lbl("Arcane Recovery", GOLD2, FS_HEAD, bold=True))
        self._budget_lbl = _lbl("", TEXT2, FS_SMALL, wrap=True)
        root.addWidget(self._budget_lbl)

        self._spins = {}
        used = char.get("spell_slots_used", [0]*9)
        for lvl in range(1, 6):  # slot levels 1-5 only
            expended = used[lvl - 1] if lvl - 1 < len(used) else 0
            if expended <= 0:
                continue
            row = QHBoxLayout()
            row.addWidget(_lbl(f"Level {lvl} slot ({expended} expended):", TEXT, FS_SMALL))
            sp = QSpinBox(); sp.setRange(0, expended)
            sp.valueChanged.connect(self._update_budget_label)
            row.addWidget(sp)
            root.addLayout(row)
            self._spins[lvl] = sp
        self._update_budget_label()

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(self.reject)
        self._confirm_btn = QPushButton("Recover"); self._confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(self._confirm_btn)
        root.addLayout(btn_row)

    def _update_budget_label(self, *_):
        spent = sum(lvl * sp.value() for lvl, sp in self._spins.items())
        remaining = self.budget - spent
        self._budget_lbl.setText(
            f"Budget: {self.budget} total slot levels. Spent so far: {spent}. Remaining: {remaining}.")
        over_budget = spent > self.budget
        self._budget_lbl.setStyleSheet(
            f"color:{CRIM2 if over_budget else TEXT2};font-size:{FS_SMALL}px;")
        if hasattr(self, "_confirm_btn"):
            self._confirm_btn.setEnabled(not over_budget)

    def get_recovered_levels(self):
        """Returns a flat list of slot levels to recover, e.g. [1,1,3]
        for two 1st-level slots and one 3rd-level slot."""
        levels = []
        for lvl, sp in self._spins.items():
            levels.extend([lvl] * sp.value())
        return levels


class RestOptionsDialog(QDialog):
    """Unified rest-configuration dialog — shown after finishing a short
    or long rest, surfaces every "you can change X when you finish a
    rest" choice the character actually has, found by searching the
    game's own feature text for short/long rest + change/swap language.
    Extensible: add more entries to _build_options() as more of these
    get confirmed and wired up.

    Currently covers: unpreparing all spells to choose new ones (any
    prepared caster, long rest), and the Artificer Armorer's Arcane
    Armor model swap (confirmed via the actual rule text — short or
    long rest, smith's tools in hand)."""

    def __init__(self, char, rest_type, parent=None):
        super().__init__(parent)
        self.char = char
        self.rest_type = rest_type  # "short" or "long"
        self.setWindowTitle(f"{'Long' if rest_type == 'long' else 'Short'} Rest Options")
        self.setMinimumSize(480, 300)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        self._options = self._build_options()
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
        confirm_btn.setStyleSheet(
            f"QPushButton{{background:{qa(GOLD,0x33)};border:2px solid {GOLD};border-radius:6px;"
            f"color:{GOLD2};font-weight:700;padding:4px 20px;}}"
            f"QPushButton:hover{{background:{GOLD};color:{BG};}}")
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(skip_btn); btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)

    def _build_options(self):
        char = self.char
        opts = []
        # Unprepare all spells — any prepared caster, long rest only (this
        # is the normal way of re-choosing prepared spells: 1 minute per
        # spell level during a long rest, PHB p.201-202).
        if self.rest_type == "long":
            _, _, _, prep_ab = _spell_progression_tables_static()
            if any(cn in prep_ab for cn in {c["class"] for c in char.get("classes", [])}):
                if char.get("spells_prepared"):
                    opts.append({
                        "kind": "unprepare_all",
                        "label": "Unprepare all spells (choose new ones afterward)",
                        "detail": "Clears every non-bonus prepared spell so you can pick a "
                                  "different set from the Spells tab.",
                    })
        # Armorer's Arcane Armor model is changeable on either rest type with smith's tools in hand.
        is_armorer = any(
            c.get("class") == "Artificer" and "armorer" in c.get("subclass", "").lower()
            for c in char.get("classes", [])
        )
        if is_armorer and char.get("_choices", {}).get("armorer_model_3"):
            opts.append({
                "kind": "armorer_model",
                "label": "Change Arcane Armor model (Guardian ↔ Infiltrator)",
                "detail": "Requires smith's tools in hand — confirmed via the actual rule text.",
            })
        # Arcane Recovery (Wizard 1+): short rest only (the rule triggers
        # "when you finish a short rest"), once per day (checked via the
        # resource added in update_all), only if there's actually
        # something expended to recover.
        if self.rest_type == "short":
            arcane_recovery_res = next(
                (r for r in char.get("resources", []) if r.get("key") == "arcane_recovery"), None)
            if arcane_recovery_res and arcane_recovery_res.get("current", 0) > 0:
                if any(char.get("spell_slots_used", [])):
                    opts.append({
                        "kind": "arcane_recovery",
                        "label": "Arcane Recovery — recover expended spell slots",
                        "detail": "Once per day: recover slots totaling \u2264 half your Wizard "
                                  "level (rounded up), max slot level 5.",
                    })
        # Eladrin season changes only on a long rest ("you can change your chosen season after a long rest").
        race = char.get("species") or char.get("race", "")
        if self.rest_type == "long" and "eladrin" in race.lower() and char.get("_choices", {}).get("eladrin_season"):
            opts.append({
                "kind": "eladrin_season",
                "label": "Change Eladrin season",
                "detail": "Changes which additional effect your Fey Step bonus action has.",
            })
        # Pact Boon 1-hour rituals are available on short rest (and long rest), since a short rest is defined as being at least an hour.
        pact_choice = char.get("_choices", {}).get("warlock_pact_boon", [])
        pact_name = pact_choice[0].lower() if pact_choice else ""
        if "blade" in pact_name:
            opts.append({
                "kind": "pact_blade_bond",
                "label": "Bond a magic weapon to become your pact weapon",
                "detail": "1-hour ritual, performable during a short rest. The weapon becomes "
                          "your pact weapon until you die, bond a different weapon, or break "
                          "the bond (also a 1-hour ritual).",
            })
        if "tome" in pact_name:
            opts.append({
                "kind": "pact_tome_replace",
                "label": "Replace a lost Book of Shadows",
                "detail": "1-hour ceremony, performable during a short or long rest. Destroys "
                          "the previous book.",
            })
        if "talisman" in pact_name:
            opts.append({
                "kind": "pact_talisman_replace",
                "label": "Replace a lost Talisman",
                "detail": "1-hour ceremony, performable during a short or long rest. Destroys "
                          "the previous amulet.",
            })
        # Guidance of the Spirits (Bard, College of Spirits) resets on a long rest only. Whispers of the Dead (Rogue, Phantom) resets on either rest type.
        if self.rest_type == "long" and char.get("_choices", {}).get("guidance_of_the_spirits_skill"):
            opts.append({
                "kind": "guidance_spirits_swap",
                "label": "Swap Guidance of the Spirits' skill",
                "detail": "Changes which skill you gained proficiency in.",
            })
        if char.get("_choices", {}).get("whispers_of_the_dead_prof"):
            opts.append({
                "kind": "whispers_dead_swap",
                "label": "Channel a different Whispers of the Dead proficiency",
                "detail": "Changes which skill or tool proficiency you currently have from this feature.",
            })
        if self.rest_type == "long" and char.get("_choices", {}).get("lunar_phase"):
            opts.append({
                "kind": "lunar_phase_swap",
                "label": "Change your Lunar Embodiment phase",
                "detail": "Choose Full Moon, New Moon, or Crescent Moon.",
            })
        return opts

    def get_selected(self):
        return [kind for kind, cb in self._checks.items() if cb.isChecked()]


def _spell_progression_tables_static():
    """Standalone version of CharacterSheet._spell_progression_tables,
    usable without a CharacterSheet instance (RestOptionsDialog doesn't
    have one)."""
    from dnd_app.data.classes import CLASS_DICT
    prep_ab = {cn for cn, cd in CLASS_DICT.items() if cd.get("spell_ability") and cd.get("has_spells")
               and cn in ("Cleric", "Druid", "Paladin", "Artificer", "Wizard")}
    return None, None, None, prep_ab


class LevelUpMulticlassDialog(QDialog):
    """Unified Level Up / Multiclass panel (BG3-style) — always shows every
    class as a radio button: classes the character already has (labeled
    with their current level) and every class they could multiclass into
    (labeled "New", grayed out entirely if the ability score prerequisite
    isn't met). Defaults to whichever class was leveled last, so a plain
    level-up is a single click, while multiclassing is equally visible
    right there instead of a separate, easy-to-miss action. Shows what
    the selected choice actually grants before confirming."""

    def __init__(self, char, parent=None):
        super().__init__(parent)
        self.char = char
        self.setWindowTitle("Level Up / Multiclass")
        self.setMinimumSize(560, 480)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        root = QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(12)
        # setChecked(True) in the radio loop below fires the toggled signal
        # synchronously (Qt behavior), which would call _on_pick() before
        # several attributes it needs (_details_lbl, _SWAP_CLASSES, etc.)
        # are constructed, crashing for any character with an existing
        # class. __init__ already calls _on_pick(default_choice)
        # explicitly at the end regardless, so this guard just prevents
        # the redundant, unsafe early trigger.
        self._init_in_progress = True

        root.addWidget(_lbl("Level Up / Multiclass", GOLD2, FS_HEAD, bold=True))
        root.addWidget(_lbl(
            "Choose a class to gain a level in. Classes you don't have yet are shown "
            "as multiclass options — grayed out if you don't meet their ability score requirement.",
            TEXT2, FS_SMALL, wrap=True))

        body = QHBoxLayout(); body.setSpacing(16)

        # This widget must be created before the left-side radio loop:
        # rb.setChecked(True) below fires the toggled signal synchronously
        # (Qt behavior), calling _on_pick(), which needs this label to
        # already exist.
        self._details_lbl = _lbl("", TEXT, FS_BODY, wrap=True)

        # ── Left: radio list of every class ──────────────────────────────
        from dnd_app.data.classes import CLASS_NAMES, CLASS_DICT
        left_card = _card(qa(INDIGO,0x44)); left_lay = QVBoxLayout(left_card)
        left_lay.setContentsMargins(10,10,10,10); left_lay.setSpacing(4)
        self._btn_group = QButtonGroup(self)
        self._radios = {}
        existing = {c["class"]: c["level"] for c in char.get("classes", [])}
        default_choice = char.get("_last_leveled_class")
        if default_choice not in existing:
            default_choice = max(existing, key=lambda k: existing[k]) if existing else None
        for cls_name in CLASS_NAMES:
            in_use = cls_name in existing
            if in_use:
                label = f"{cls_name}  (Lv {existing[cls_name]})"
            else:
                label = f"{cls_name}  (New)"
            rb = QRadioButton(label)
            if not in_use:
                ok_req, msg = self._meets_multiclass_reqs(cls_name, existing)
                if not ok_req:
                    rb.setEnabled(False)
                    rb.setToolTip(f"Doesn't meet multiclass prerequisites: {msg}")
            rb.toggled.connect(lambda checked, n=cls_name: self._on_pick(n) if checked else None)
            self._btn_group.addButton(rb)
            self._radios[cls_name] = rb
            left_lay.addWidget(rb)
            if cls_name == default_choice and rb.isEnabled():
                rb.setChecked(True)
        left_lay.addStretch()
        body.addWidget(left_card, 1)

        # ── Right: details of what the selected class/level grants ──────
        right_card = _card(qa(TEAL,0x44)); right_lay = QVBoxLayout(right_card)
        right_lay.setContentsMargins(12,12,12,12)
        right_lay.addWidget(_lbl("WHAT YOU'LL GET", TEAL2, FS_SMALL, bold=True))
        right_lay.addWidget(self._details_lbl)
        right_lay.addStretch()
        body.addWidget(right_card, 1)

        root.addLayout(body)

        # ── Known-spell swap — Bard/Sorcerer/Warlock only ────────────────
        # Per the real rule ("whenever you gain a level in this class, you
        # can replace one spell you know with another from the class
        # list"), shown/hidden based on which class is currently selected.
        self._SWAP_CLASSES = {"Bard", "Sorcerer", "Warlock", "Ranger"}
        self._swap_card = _card(qa(PURPLE, 0x44))
        swap_lay = QVBoxLayout(self._swap_card)
        swap_lay.setContentsMargins(10, 10, 10, 10)
        swap_lay.addWidget(_lbl("SWAP A KNOWN SPELL (OPTIONAL)", PURPLE, FS_SMALL, bold=True))
        swap_row = QHBoxLayout()
        self._swap_out_combo = QComboBox()
        self._swap_in_combo = QComboBox()
        swap_row.addWidget(_lbl("Remove:", TEXT2, FS_SMALL))
        swap_row.addWidget(self._swap_out_combo, 1)
        swap_row.addWidget(_lbl("Learn:", TEXT2, FS_SMALL))
        swap_row.addWidget(self._swap_in_combo, 1)
        swap_lay.addLayout(swap_row)
        self._swap_card.setVisible(False)
        root.addWidget(self._swap_card)

        # ── Eldritch Versatility (Warlock, TCoE, optional) ────────────────
        # Gated behind the Settings toggle since it's titled "(Optional)"
        # in the rule text.
        self._ev_card = _card(qa(PURPLE, 0x44))
        ev_lay = QVBoxLayout(self._ev_card)
        ev_lay.setContentsMargins(10, 10, 10, 10)
        ev_lay.addWidget(_lbl("ELDRITCH VERSATILITY (OPTIONAL)", PURPLE, FS_SMALL, bold=True))
        self._ev_what_combo = QComboBox()
        self._ev_what_combo.addItem("— don't use Eldritch Versatility —", None)
        self._ev_what_combo.addItem("Replace a Pact Magic cantrip", "cantrip")
        self._ev_what_combo.addItem("Replace my Pact Boon", "pact_boon")
        self._ev_what_combo.addItem("Replace a Mystic Arcanum spell (12th level+)", "arcanum")
        ev_lay.addWidget(self._ev_what_combo)
        ev_sub_row = QHBoxLayout()
        self._ev_out_combo = QComboBox()
        self._ev_in_combo = QComboBox()
        ev_sub_row.addWidget(_lbl("Remove:", TEXT2, FS_SMALL))
        ev_sub_row.addWidget(self._ev_out_combo, 1)
        ev_sub_row.addWidget(_lbl("Add:", TEXT2, FS_SMALL))
        ev_sub_row.addWidget(self._ev_in_combo, 1)
        ev_lay.addLayout(ev_sub_row)
        self._ev_what_combo.currentIndexChanged.connect(self._on_ev_what_changed)
        self._ev_card.setVisible(False)
        root.addWidget(self._ev_card)

        # Martial Versatility (Fighter/Paladin/Ranger, TCE, optional) is
        # also ASI-level-gated, matching Eldritch Versatility's
        # architecture — simpler here since there's only one swap type
        # (fighting style for fighting style), not three.
        self._mv_card = _card(qa(TEAL, 0x44))
        mv_lay = QVBoxLayout(self._mv_card)
        mv_lay.setContentsMargins(10, 10, 10, 10)
        mv_lay.addWidget(_lbl("MARTIAL VERSATILITY (OPTIONAL)", TEAL2, FS_SMALL, bold=True))
        # Fighter can also swap a known Battle Master maneuver, not just a fighting style.
        self._mv_what_combo = QComboBox()
        self._mv_what_combo.addItem("Replace a Fighting Style", "style")
        mv_lay.addWidget(self._mv_what_combo)
        mv_sub_row = QHBoxLayout()
        self._mv_out_combo = QComboBox()
        self._mv_in_combo = QComboBox()
        mv_sub_row.addWidget(_lbl("Replace:", TEXT2, FS_SMALL))
        mv_sub_row.addWidget(self._mv_out_combo, 1)
        mv_sub_row.addWidget(_lbl("With:", TEXT2, FS_SMALL))
        mv_sub_row.addWidget(self._mv_in_combo, 1)
        mv_lay.addLayout(mv_sub_row)
        self._mv_what_combo.currentIndexChanged.connect(self._on_mv_what_changed)
        self._mv_card.setVisible(False)
        root.addWidget(self._mv_card)

        # Cantrip Versatility (Cleric/Druid, TCE, optional): both classes
        # share the same single-swap-type rule, so one card covers both.
        self._cv_card = _card(qa(GOLD, 0x44))
        cv_lay = QVBoxLayout(self._cv_card)
        cv_lay.setContentsMargins(10, 10, 10, 10)
        cv_lay.addWidget(_lbl("CANTRIP VERSATILITY (OPTIONAL)", GOLD2, FS_SMALL, bold=True))
        cv_sub_row = QHBoxLayout()
        self._cv_out_combo = QComboBox()
        self._cv_in_combo = QComboBox()
        cv_sub_row.addWidget(_lbl("Replace:", TEXT2, FS_SMALL))
        cv_sub_row.addWidget(self._cv_out_combo, 1)
        cv_sub_row.addWidget(_lbl("With:", TEXT2, FS_SMALL))
        cv_sub_row.addWidget(self._cv_in_combo, 1)
        cv_lay.addLayout(cv_sub_row)
        self._cv_card.setVisible(False)
        root.addWidget(self._cv_card)

        # Bardic Versatility (TCE, optional): two swap types, matching the
        # Eldritch Versatility "what kind" pattern.
        self._bv_card = _card(qa(CRIMSON, 0x44))
        bv_lay = QVBoxLayout(self._bv_card)
        bv_lay.setContentsMargins(10, 10, 10, 10)
        bv_lay.addWidget(_lbl("BARDIC VERSATILITY (OPTIONAL)", CRIM2, FS_SMALL, bold=True))
        self._bv_what_combo = QComboBox()
        self._bv_what_combo.addItem("Replace an Expertise skill", "expertise")
        self._bv_what_combo.addItem("Replace a cantrip", "cantrip")
        bv_lay.addWidget(self._bv_what_combo)
        bv_sub_row = QHBoxLayout()
        self._bv_out_combo = QComboBox()
        self._bv_in_combo = QComboBox()
        bv_sub_row.addWidget(_lbl("Replace:", TEXT2, FS_SMALL))
        bv_sub_row.addWidget(self._bv_out_combo, 1)
        bv_sub_row.addWidget(_lbl("With:", TEXT2, FS_SMALL))
        bv_sub_row.addWidget(self._bv_in_combo, 1)
        bv_lay.addLayout(bv_sub_row)
        self._bv_what_combo.currentIndexChanged.connect(self._on_bv_what_changed)
        self._bv_card.setVisible(False)
        root.addWidget(self._bv_card)

        # Sorcerous Versatility (TCE, optional): two swap types, matching the same pattern.
        self._sv_card = _card(qa(PURPLE, 0x44))
        sv_lay = QVBoxLayout(self._sv_card)
        sv_lay.setContentsMargins(10, 10, 10, 10)
        sv_lay.addWidget(_lbl("SORCEROUS VERSATILITY (OPTIONAL)", PURP2, FS_SMALL, bold=True))
        self._sv_what_combo = QComboBox()
        self._sv_what_combo.addItem("Replace a Metamagic option", "metamagic")
        self._sv_what_combo.addItem("Replace a cantrip", "cantrip")
        sv_lay.addWidget(self._sv_what_combo)
        sv_sub_row = QHBoxLayout()
        self._sv_out_combo = QComboBox()
        self._sv_in_combo = QComboBox()
        sv_sub_row.addWidget(_lbl("Replace:", TEXT2, FS_SMALL))
        sv_sub_row.addWidget(self._sv_out_combo, 1)
        sv_sub_row.addWidget(_lbl("With:", TEXT2, FS_SMALL))
        sv_sub_row.addWidget(self._sv_in_combo, 1)
        sv_lay.addLayout(sv_sub_row)
        self._sv_what_combo.currentIndexChanged.connect(self._on_sv_what_changed)
        self._sv_card.setVisible(False)
        root.addWidget(self._sv_card)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        self._confirm_btn = QPushButton("Confirm"); self._confirm_btn.setFixedHeight(34)
        self._confirm_btn.setStyleSheet(
            f"QPushButton{{background:{qa(GOLD,0x33)};border:2px solid {GOLD};border-radius:6px;"
            f"color:{GOLD2};font-weight:700;padding:4px 20px;}}"
            f"QPushButton:hover{{background:{GOLD};color:{BG};}}")
        self._confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(self._confirm_btn)
        root.addLayout(btn_row)

        self.selected_class = default_choice
        self._init_in_progress = False
        if default_choice:
            self._on_pick(default_choice)

    def _meets_multiclass_reqs(self, class_name, existing_classes):
        """Delegates to the single canonical check_multiclass_prereq()
        function rather than re-implementing this logic separately.
        Confirmed a real bug from doing so previously: this dialog had
        its own copy of the ability-score-requirement data (via
        CLASS_DICT's multiclass_reqs field), completely separate from
        multiclass.py's MULTICLASS_PREREQS_2024 — so the Blood Hunter
        fix made earlier this session (the real rule is INT 13 AND
        (STR or DEX) 13, not STR AND INT both required) only ever
        reached one of the two copies, leaving a Dexterity-based Blood
        Hunter wrongly grayed out here even after that fix landed."""
        from dnd_app.core.multiclass import check_multiclass_prereq
        if not self.char.get("optional_rules", {}).get("multiclass_ability_reqs", True):
            return True, ""
        base_scores = self.char.get("abilities", {})
        bonuses = self.char.get("ability_bonuses", {})
        scores = {ab: base_scores.get(ab, 10) + bonuses.get(ab, 0) for ab in
                  ("STR", "DEX", "CON", "INT", "WIS", "CHA")}
        return check_multiclass_prereq(class_name, scores)

    def _on_pick(self, cls_name):
        if getattr(self, "_init_in_progress", False):
            return
        self.selected_class = cls_name
        from dnd_app.data.classes import CLASS_DICT
        existing = {c["class"]: c["level"] for c in self.char.get("classes", [])}
        cdata = CLASS_DICT.get(cls_name, {})
        lines = []
        if cls_name in existing:
            cur_lvl = existing[cls_name]
            if cur_lvl >= 20:
                lines.append(f"{cls_name} is already at the maximum level (20).")
                lines.append("")
                lines.append("Pick a different class to gain a level, or multiclass into a new one.")
                self._details_lbl.setText("\n".join(lines))
                if hasattr(self, "_confirm_btn"):
                    self._confirm_btn.setEnabled(False)
                return
            if hasattr(self, "_confirm_btn"):
                self._confirm_btn.setEnabled(True)
            next_lvl = cur_lvl + 1
            lines.append(f"{cls_name}, level {cur_lvl} → {next_lvl}")
            feats = cdata.get("features", {}).get(next_lvl, [])
            if feats:
                lines.append("")
                lines.append("New at this level:")
                lines.extend(f"  • {f}" for f in feats)
            else:
                lines.append("")
                lines.append("No new features at this level (ASI/subclass features may "
                              "still appear at specific levels — check the Features tab).")
        else:
            if hasattr(self, "_confirm_btn"):
                self._confirm_btn.setEnabled(True)
            lines.append(f"{cls_name} (new, starts at level 1)")
            lines.append("")
            feats = cdata.get("features", {}).get(1, [])
            if feats:
                lines.append("Gains at level 1:")
                lines.extend(f"  • {f}" for f in feats)
            lines.append("")
            lines.append(f"Hit Die: d{cdata.get('hit_die', 8)}")
            lines.append(
                "Multiclassing grants only partial proficiencies (per the 2014 PHB "
                "multiclassing table) — not the full starting proficiency list a "
                "level 1 character of this class would normally get.")
        self._details_lbl.setText("\n".join(lines))

        # Known-spell swap — standard casters (Bard/Sorcerer/Warlock/
        # Ranger) swap from their own list; Eldritch Knight (Fighter) and
        # Arcane Trickster (Rogue) instead swap a WIZARD spell (they have
        # no spell list of their own), restricted to specific schools per
        # the exact rule text: abjuration/evocation for Eldritch Knight,
        # enchantment/illusion for Arcane Trickster. Only for an EXISTING
        # character leveling up — a brand new multiclass addition starts
        # fresh with its own spell choices, so there's nothing yet to
        # swap out.
        my_subclass = existing.get(cls_name) and next(
            (c.get("subclass", "") for c in self.char.get("classes", []) if c["class"] == cls_name), "")
        is_eldritch_knight = cls_name == "Fighter" and "eldritch knight" in (my_subclass or "").lower()
        is_arcane_trickster = cls_name == "Rogue" and "arcane trickster" in (my_subclass or "").lower()
        show_swap = (cls_name in self._SWAP_CLASSES and cls_name in existing) \
            or is_eldritch_knight or is_arcane_trickster
        self._swap_card.setVisible(show_swap)
        if show_swap:
            from dnd_app.data.spells import ALL_SPELLS
            known = [s for s in self.char.get("spells_known", [])]
            if is_eldritch_knight or is_arcane_trickster:
                swap_list_class = "Wizard"
                allowed_schools = {"Abjuration", "Evocation"} if is_eldritch_knight else {"Enchantment", "Illusion"}
            else:
                swap_list_class = cls_name
                allowed_schools = None  # no school restriction for standard known-spell casters
            class_spell_names = {s["name"] for s in ALL_SPELLS
                                  if swap_list_class in s.get("classes", []) and s.get("level", 0) > 0}
            known_of_class = [n for n in known if n in class_spell_names]
            self._swap_out_combo.clear()
            self._swap_out_combo.addItem("— don't swap —", None)
            for n in sorted(known_of_class):
                self._swap_out_combo.addItem(n, n)
            self._swap_in_combo.clear()
            self._swap_in_combo.addItem("— choose a spell —", None)
            for s in sorted(ALL_SPELLS, key=lambda s: (s.get("level", 0), s["name"])):
                if swap_list_class not in s.get("classes", []) or s["name"] in known:
                    continue
                if s.get("level", 0) == 0:
                    continue
                if allowed_schools is not None and s.get("school") not in allowed_schools:
                    continue
                self._swap_in_combo.addItem(f"{s['name']} (Lv{s.get('level',0)})", s["name"])

        # Eldritch Versatility (Warlock, TCoE, optional) — only shown
        # when the Settings toggle is on and the character is an
        # existing Warlock leveling to an ASI-granting level.
        ASI_LEVELS = {4, 8, 12, 16, 19}
        current_warlock_lvl = existing.get(cls_name, 0) if cls_name == "Warlock" else 0
        is_asi_level = (current_warlock_lvl + 1) in ASI_LEVELS
        show_ev = (self.char.get("optional_rules", {}).get("eldritch_versatility", False)
                   and cls_name == "Warlock" and cls_name in existing and is_asi_level)
        self._ev_card.setVisible(show_ev)
        if show_ev:
            self._ev_what_combo.setCurrentIndex(0)
            self._on_ev_what_changed(0)

        # Martial Versatility: Fighter has a different ASI level set than
        # Paladin/Ranger (extra levels at 6 and 14), so this can't reuse a
        # single shared ASI_LEVELS set the way Eldritch Versatility does
        # for Warlock alone.
        MV_ASI_LEVELS = {"Fighter": {4,6,8,12,14,16,19}, "Paladin": {4,8,12,16,19}, "Ranger": {4,8,12,16,19}}
        current_mv_lvl = existing.get(cls_name, 0)
        is_mv_asi_level = (current_mv_lvl + 1) in MV_ASI_LEVELS.get(cls_name, set())
        has_a_style = bool(self.char.get("fighting_styles"))
        show_mv = (self.char.get("optional_rules", {}).get("martial_versatility", False)
                   and cls_name in MV_ASI_LEVELS and cls_name in existing
                   and is_mv_asi_level and has_a_style)
        self._mv_card.setVisible(show_mv)
        if show_mv:
            # Fighter can also swap a known Battle Master maneuver ("if you
            # know any maneuvers from the Battle Master archetype"), gated
            # on actually knowing any. Paladin and Ranger never get
            # maneuvers, so they only see the fighting-style option.
            self._mv_what_combo.blockSignals(True)
            self._mv_what_combo.clear()
            self._mv_what_combo.addItem("Replace a Fighting Style", "style")
            known_maneuvers = self.char.get("battle_master_maneuvers", [])
            if cls_name == "Fighter" and known_maneuvers:
                self._mv_what_combo.addItem("Replace a Maneuver", "maneuver")
            self._mv_what_combo.blockSignals(False)
            self._mv_what_combo.setCurrentIndex(0)
            self._on_mv_what_changed(0)

        # Cantrip Versatility (Cleric/Druid): both share the same single-swap-type rule.
        CV_CLASSES = {"Cleric", "Druid"}
        current_cv_lvl = existing.get(cls_name, 0)
        is_cv_asi_level = (current_cv_lvl + 1) in ASI_LEVELS
        show_cv_versatility = (self.char.get("optional_rules", {}).get("cantrip_versatility", False)
                   and cls_name in CV_CLASSES and cls_name in existing and is_cv_asi_level)
        # Cantrip Formulas (Wizard, TCE optional, genuinely missing
        # entirely): same swap mechanism, but correctly NOT ASI-gated —
        # the real rule is "whenever you finish a long rest," so kept
        # as a separate, always-available condition rather than
        # incorrectly folded into the ASI-level check above.
        show_cv_formulas = (self.char.get("optional_rules", {}).get("cantrip_formulas", False)
                   and cls_name == "Wizard" and existing.get("Wizard", 0) >= 3)
        show_cv = show_cv_versatility or show_cv_formulas
        self._cv_card.setVisible(show_cv)
        if show_cv:
            from dnd_app.data.spells import ALL_SPELLS
            known_cantrips = [n for n in self.char.get("spells_known", [])
                              if any(s["name"] == n and s.get("level", 0) == 0
                                     and cls_name in s.get("classes", []) for s in ALL_SPELLS)]
            self._cv_out_combo.clear()
            for n in sorted(known_cantrips):
                self._cv_out_combo.addItem(n, n)
            self._cv_in_combo.clear()
            for s in sorted(ALL_SPELLS, key=lambda s: s["name"]):
                if (s.get("level", 0) == 0 and cls_name in s.get("classes", [])
                        and s["name"] not in known_cantrips):
                    self._cv_in_combo.addItem(s["name"], s["name"])

        # Bardic Versatility swap.
        show_bv = (self.char.get("optional_rules", {}).get("bardic_versatility", False)
                   and cls_name == "Bard" and cls_name in existing and is_cv_asi_level)
        self._bv_card.setVisible(show_bv)
        if show_bv:
            self._bv_what_combo.setCurrentIndex(0)
            self._on_bv_what_changed(0)

        # Sorcerous Versatility swap.
        show_sv = (self.char.get("optional_rules", {}).get("sorcerous_versatility", False)
                   and cls_name == "Sorcerer" and cls_name in existing and is_cv_asi_level)
        self._sv_card.setVisible(show_sv)
        if show_sv:
            self._sv_what_combo.setCurrentIndex(0)
            self._on_sv_what_changed(0)

    def _on_ev_what_changed(self, _idx):
        kind = self._ev_what_combo.currentData()
        self._ev_out_combo.clear()
        self._ev_in_combo.clear()
        if kind is None:
            return
        from dnd_app.data.spells import ALL_SPELLS, spells_for_class_at_level
        if kind == "cantrip":
            known_cantrips = [n for n in self.char.get("spells_known", [])
                              if any(s["name"] == n and s.get("level", 0) == 0
                                     and "Warlock" in s.get("classes", []) for s in ALL_SPELLS)]
            for n in sorted(known_cantrips):
                self._ev_out_combo.addItem(n, n)
            for s in sorted(ALL_SPELLS, key=lambda s: s["name"]):
                if (s.get("level", 0) == 0 and "Warlock" in s.get("classes", [])
                        and s["name"] not in known_cantrips):
                    self._ev_in_combo.addItem(s["name"], s["name"])
        elif kind == "pact_boon":
            pool = ["Pact of the Blade (summon a pact weapon)",
                    "Pact of the Chain (imp/quasit/pseudodragon/sprite familiar)",
                    "Pact of the Tome (Book of Shadows: 3 extra cantrips from any class, cast as rituals if the spell allows)",
                    "Pact of the Talisman (amulet: +1d4 to a failed ability check, uses = proficiency bonus per long rest)"]
            current = self.char.get("_choices", {}).get("warlock_pact_boon", [])
            self._ev_out_combo.addItem(current[0] if current else "(none chosen yet)", current[0] if current else None)
            self._ev_out_combo.setEnabled(False)
            for p in pool:
                if not current or p != current[0]:
                    self._ev_in_combo.addItem(p, p)
        elif kind == "arcanum":
            ARCANUM_LEVELS = {11: 6, 13: 7, 15: 8, 17: 9}
            warlock_lvl = next((c["level"] for c in self.char.get("classes", []) if c["class"] == "Warlock"), 0)
            for char_lvl, spell_lvl in sorted(ARCANUM_LEVELS.items()):
                if warlock_lvl >= char_lvl:
                    chosen = self.char.get("_choices", {}).get(f"mystic_arcanum_{spell_lvl}", [])
                    if chosen:
                        self._ev_out_combo.addItem(f"{chosen[0]} (Lv{spell_lvl} Arcanum)", (spell_lvl, chosen[0]))
            if self._ev_out_combo.count():
                spell_lvl = self._ev_out_combo.currentData()[0] if self._ev_out_combo.currentData() else 6
                for s in spells_for_class_at_level("Warlock", spell_lvl):
                    self._ev_in_combo.addItem(s["name"], s["name"])

    def _on_mv_what_changed(self, _idx):
        kind = self._mv_what_combo.currentData()
        self._mv_out_combo.clear()
        self._mv_in_combo.clear()
        if kind is None:
            return
        if kind == "style":
            from dnd_app.ui.levelup_panel import FIGHTING_STYLES as MV_FIGHTING_STYLES
            known_styles = self.char.get("fighting_styles", [])
            for s in known_styles:
                self._mv_out_combo.addItem(s.split(" (")[0].strip(), s)
            pool = MV_FIGHTING_STYLES.get(self.selected_class, [])
            for s in pool:
                base_name = s.split(" (")[0].strip()
                if not any(base_name.lower() == ks.split(" (")[0].strip().lower() for ks in known_styles):
                    self._mv_in_combo.addItem(base_name, s)
        elif kind == "maneuver":
            from dnd_app.data.classes import BATTLE_MASTER_MANEUVERS
            known_maneuvers = self.char.get("battle_master_maneuvers", [])
            for m in known_maneuvers:
                self._mv_out_combo.addItem(m.split(" – ")[0].strip(), m)
            for m in BATTLE_MASTER_MANEUVERS:
                base_name = m.split(" – ")[0].strip()
                if not any(base_name.lower() == km.split(" – ")[0].strip().lower() for km in known_maneuvers):
                    self._mv_in_combo.addItem(base_name, m)

    def _on_bv_what_changed(self, _idx):
        kind = self._bv_what_combo.currentData()
        self._bv_out_combo.clear()
        self._bv_in_combo.clear()
        if kind is None:
            return
        if kind == "expertise":
            expert_skills = [s for s, lvl in self.char.get("skills", {}).items() if lvl == 3]
            proficient_only = [s for s, lvl in self.char.get("skills", {}).items() if lvl == 2]
            for s in expert_skills:
                self._bv_out_combo.addItem(s, s)
            for s in proficient_only:
                self._bv_in_combo.addItem(s, s)
        elif kind == "cantrip":
            from dnd_app.data.spells import ALL_SPELLS
            known_cantrips = [n for n in self.char.get("spells_known", [])
                              if any(s["name"] == n and s.get("level", 0) == 0
                                     and "Bard" in s.get("classes", []) for s in ALL_SPELLS)]
            for n in sorted(known_cantrips):
                self._bv_out_combo.addItem(n, n)
            for s in sorted(ALL_SPELLS, key=lambda s: s["name"]):
                if (s.get("level", 0) == 0 and "Bard" in s.get("classes", [])
                        and s["name"] not in known_cantrips):
                    self._bv_in_combo.addItem(s["name"], s["name"])

    def _on_sv_what_changed(self, _idx):
        kind = self._sv_what_combo.currentData()
        self._sv_out_combo.clear()
        self._sv_in_combo.clear()
        if kind is None:
            return
        if kind == "metamagic":
            from dnd_app.data.classes import METAMAGIC
            known_mm = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
            for m in known_mm:
                self._sv_out_combo.addItem(m.split(" – ")[0].strip(), m)
            for m in METAMAGIC:
                base_name = m.split(" – ")[0].strip()
                if not any(base_name.lower() == km.split(" – ")[0].strip().lower() for km in known_mm):
                    self._sv_in_combo.addItem(base_name, m)
        elif kind == "cantrip":
            from dnd_app.data.spells import ALL_SPELLS
            known_cantrips = [n for n in self.char.get("spells_known", [])
                              if any(s["name"] == n and s.get("level", 0) == 0
                                     and "Sorcerer" in s.get("classes", []) for s in ALL_SPELLS)]
            for n in sorted(known_cantrips):
                self._sv_out_combo.addItem(n, n)
            for s in sorted(ALL_SPELLS, key=lambda s: s["name"]):
                if (s.get("level", 0) == 0 and "Sorcerer" in s.get("classes", [])
                        and s["name"] not in known_cantrips):
                    self._sv_in_combo.addItem(s["name"], s["name"])

    def get_spell_swap(self):
        """Returns (old_spell_name, new_spell_name) or (None, None) if no
        swap was requested."""
        if not self._swap_card.isVisible():
            return None, None
        old = self._swap_out_combo.currentData()
        new = self._swap_in_combo.currentData()
        if old and new:
            return old, new
        return None, None

    def get_eldritch_versatility(self):
        """Returns a dict {'kind': 'cantrip'|'pact_boon'|'arcanum', 'old':
        ..., 'new': ...} describing the requested Eldritch Versatility
        swap, or None if not used/not applicable."""
        if not self._ev_card.isVisible():
            return None
        kind = self._ev_what_combo.currentData()
        if kind is None:
            return None
        old = self._ev_out_combo.currentData()
        new = self._ev_in_combo.currentData()
        if new is None:
            return None
        if kind == "pact_boon" and old is None:
            return None  # nothing to replace yet
        return {"kind": kind, "old": old, "new": new}

    def get_martial_versatility(self):
        """Returns (kind, old, new) or (None, None, None) if not used."""
        if not self._mv_card.isVisible():
            return None, None, None
        kind = self._mv_what_combo.currentData()
        old = self._mv_out_combo.currentData()
        new = self._mv_in_combo.currentData()
        if kind and old and new:
            return kind, old, new
        return None, None, None

    def get_cantrip_versatility(self):
        """Returns (old_cantrip, new_cantrip) or (None, None) if not used."""
        if not self._cv_card.isVisible():
            return None, None
        old = self._cv_out_combo.currentData()
        new = self._cv_in_combo.currentData()
        if old and new:
            return old, new
        return None, None

    def get_bardic_versatility(self):
        """Returns (kind, old, new) or (None, None, None) if not used."""
        if not self._bv_card.isVisible():
            return None, None, None
        kind = self._bv_what_combo.currentData()
        old = self._bv_out_combo.currentData()
        new = self._bv_in_combo.currentData()
        if kind and old and new:
            return kind, old, new
        return None, None, None

    def get_sorcerous_versatility(self):
        """Returns (kind, old, new) or (None, None, None) if not used."""
        if not self._sv_card.isVisible():
            return None, None, None
        kind = self._sv_what_combo.currentData()
        old = self._sv_out_combo.currentData()
        new = self._sv_in_combo.currentData()
        if kind and old and new:
            return kind, old, new
        return None, None, None

    def get_result(self):
        """Returns (class_name, is_new_class)."""
        existing = {c["class"] for c in self.char.get("classes", [])}
        return self.selected_class, self.selected_class not in existing


class CharacterSheet(QWidget):
    back_to_menu = Signal()

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        from dnd_app.ui.theme import sync_globals as _sg; _sg(globals())
        self.ctrl = CharacterController(char)
        self.char = self.ctrl.char
        self._spell_rows = []
        self._level_headers = {}
        self._slot_bars = {}
        self._resource_widgets = []
        self._weapon_row_widgets = []
        self._magic_item_rows = []
        self._resource_widgets: list = []   # populated by _build_resource_rows
        self._blocking_refresh = False
        self._dirty = False
        self._save_path = None
        self.ctrl.subscribe(self._on_char_updated)
        self._build_ui()
        self.ctrl.refresh()
        self._load()
        self.ctrl.mark_ui_ready()
        # ── Accessibility: keyboard-focus rings + unambiguous disabled state ──
        self.setStyleSheet(self.styleSheet() + f"""
            QPushButton:focus, QComboBox:focus, QLineEdit:focus,
            QSpinBox:focus, QCheckBox:focus, QListWidget:focus,
            QTabBar::tab:focus {{
                outline: none;
                border: 2px solid {TEAL2};
            }}
            QPushButton:disabled {{
                background: {SURF2};
                color: {TEXT3};
                border: 2px dashed {BORDER2};
            }}
            QToolTip {{
                background: {SURF2}; color: {TEXT};
                border: 1px solid {AMBER}; padding: 6px;
                font-size: {FS_SMALL}px;
            }}
        """)

        self._dirty = False
        # Auto-save backup every 60 seconds if the sheet has unsaved changes
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(60_000)
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start()

        # ── Keyboard shortcuts ────────────────────────────────────────────────
        from PySide6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Ctrl+S"), self, self._save)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, self._long_rest)
        QShortcut(QKeySequence("Ctrl+R"), self, self._short_rest)
        for i in range(1, 9):   # Ctrl+1..8 → jump to tab
            QShortcut(QKeySequence(f"Ctrl+{i}"), self,
                      lambda idx=i-1: self._tabs.setCurrentIndex(idx)
                      if idx < self._tabs.count() else None)

        # A character saved while dead (3 failed death saves, massive
        # damage, or exhaustion 6) and never revived should still show
        # the death screen on reopen -- deferred to the next event loop
        # tick since the overlay sizes itself from self.rect(), which
        # isn't finalized yet mid-construction.
        if self.char.get("is_dead", False):
            QTimer.singleShot(0, self._show_death_screen)

    def _autosave(self):
        """Silently write a .autosave backup when there are unsaved changes."""
        if not getattr(self, "_is_dirty", False):
            return
        try:
            from dnd_app.core.save_load import save_character, character_filename
            base = character_filename(self.char)
            save_character(self.char, base.replace(".json", ".autosave.json"))
        except Exception:
            pass  # never let auto-save crash the app

    def _force_full_refresh(self):
        """Manual refresh: fully rebuild the character sheet from scratch —
        the same path used when loading or switching characters — rather
        than replaying a hand-maintained list of _refresh_XXX() calls.
        That list has drifted out of sync before (the Companions tab, for
        instance, wasn't added to it until this was refactored) and will
        again as new tabs get added; a full rebuild can't miss anything.
        Cheap enough to do unconditionally now that _show_sheet() no
        longer double-builds the sheet on every call."""
        from dnd_app.core.builder import rebuild
        from dnd_app.core.calculator import update_all
        rebuild(self.char); update_all(self.char)

        win = self.window()
        if hasattr(win, "_show_sheet"):
            char = self.char
            cur_tab_idx = self._tabs.currentIndex()
            win._show_sheet(char)
            if win._sheet:
                win._sheet._tabs.setCurrentIndex(cur_tab_idx)
                win._sheet._toast("🔄 Refreshed")
        else:
            # Defensive fallback if this widget is ever used without a
            # CharacterCreatorApp parent (e.g. an isolated test harness).
            self._blocking_refresh = False
            self._on_char_updated(self.char)
            self._toast("🔄 Refreshed")

    def _on_char_updated(self, _char: dict) -> None:
        if self._blocking_refresh:
            return
        self._blocking_refresh = True
        try:
            self._refresh_stat_bar()
            self._refresh_abilities_tab()
            self._refresh_skills()
            # Call _do_refresh_combat directly: _refresh_combat() checks the
            # _blocking_refresh flag we just set and would return immediately,
            # leaving the combat tab (weapons, action tabs, effects, turn bar)
            # permanently stale on controller-driven updates.
            self._do_refresh_combat()
            self._refresh_spells()
            self._refresh_spell_row_titles()
            self._refresh_concentration()
            self._refresh_magic_items()
            if hasattr(self, "_levelup_panel"):
                self._levelup_panel.refresh()
            self._refresh_gear_equipment()
            # The Features tab (class/race/subrace/subclass/feat features)
            # and the subclass dropdown combos are repainted here so
            # level-ups, feat grants, and subclass picks made via the
            # Level Up panel are reflected immediately, not only after a
            # full character load or manual dropdown edit.
            if hasattr(self, "_rebuild_features"):
                self._rebuild_features()
            if hasattr(self, "_populate_subclass_combo"):
                self._populate_subclass_combo()
            self._sync_infusions_tab()
        finally:
            self._blocking_refresh = False

    def _refresh_spell_row_titles(self):
        """Immersive Spells (optional rule): re-derive each spell row's
        title text on every controller-driven refresh, so it stays in
        sync with whatever triggered the change (transforming/reverting
        Wild Shape, Rage turning on/off via any of its several toggle
        paths, a level-up granting a Paladin Oath, or the setting itself
        being flipped on/off) without needing a hook at every one of
        those individual call sites."""
        if not self._spell_rows:
            return
        from dnd_app.ui.immersive_spells import compute_display_spell_title
        for row in self._spell_rows:
            row.set_display_name(compute_display_spell_title(self.char, row.spell["name"]))

    def _sync_infusions_tab(self):
        """Add/remove the Infusions tab as eligibility changes, and refresh
        its content while present. Confirmed this tab previously could
        never appear after initial sheet construction — __init__ builds
        the tab list once, before a freshly-created or just-leveled-up
        character has any infusions known yet, and nothing ever
        re-checked eligibility afterward."""
        eligible = self._has_infuse_item_access()
        current_index = None
        for i in range(self._tabs.count()):
            if "Infusions" in self._tabs.tabText(i):
                current_index = i
                break
        if eligible and current_index is None:
            # Insert right after the Spells tab, before Choices — matches
            # the original fixed ordering from __init__.
            insert_at = None
            for i in range(self._tabs.count()):
                if "Spells" in self._tabs.tabText(i):
                    insert_at = i + 1
                    break
            if insert_at is None:
                insert_at = self._tabs.count()
            self._tabs.insertTab(insert_at, self._build_tab_infusions(), "\U0001f527  Infusions")
        elif not eligible and current_index is not None:
            self._tabs.removeTab(current_index)
        elif eligible and current_index is not None:
            self._refresh_infusions_tab()

    def _mark_dirty(self):
        self._dirty = True

    def _short_rest(self):
        """Short rest: optionally spend hit dice to heal, reset SR resources."""
        from dnd_app.core.calculator import update_all
        import random
        char = self.char
        # Offer hit-dice spending if any remain and HP is below max
        hd_model = char.get("hit_dice", {})
        total_remaining = sum(d.get("remaining", 0) for d in hd_model.values())
        cur, mx = char.get("current_hp", 0), char.get("max_hp", 0)
        healed = 0; dice_spent = 0
        if total_remaining > 0 and cur < mx:
            n, ok = QInputDialog.getInt(
                self, "Short Rest — Spend Hit Dice",
                f"HP: {cur}/{mx}   |   Hit dice remaining: {total_remaining}\n"
                f"How many hit dice do you want to spend?\n"
                f"(each heals 1 die + {ability_mod(char,'CON'):+d} CON)",
                0, 0, total_remaining)
            if ok and n > 0:
                con = ability_mod(char, "CON")
                rolls = []
                for _ in range(n):
                    # Spend from the largest die first
                    for die_key in sorted(hd_model, key=lambda k: -int(k[1:])):
                        d = hd_model[die_key]
                        if d.get("remaining", 0) > 0:
                            sides = int(die_key[1:])
                            r = random.randint(1, sides)
                            rolls.append(f"{die_key}:{r}")
                            healed += max(0, r + con)
                            d["remaining"] -= 1
                            dice_spent += 1
                            break
                char["current_hp"] = min(mx, cur + healed)
        # Reset SR resources
        for r in char.get("resources", []):
            if r.get("reset") in ("SR", "sr"):
                r["current"] = r.get("current_max") or r.get("max", 0)
        # Font of Inspiration (Bard 5+): Bardic Inspiration also recovers on
        # a short rest, even though its base resource is flagged LR-only.
        from dnd_app.core.character import class_levels as _cls_lvls_sr
        if _cls_lvls_sr(char).get("Bard", 0) >= 5:
            for r in char.get("resources", []):
                if "bardic inspiration" in str(r.get("name","")).lower():
                    r["current"] = r.get("current_max") or r.get("max", 0)
        # Warlock: restore pact slots on SR
        char["pact_slots_used"] = 0
        # Relentless Rage's DC resets to 10 after a short or long rest
        char["_relentless_rage_uses"] = 0
        expired = self._clear_expired_active_effects(("short",))
        update_all(char)
        self.ctrl.refresh()
        self._mark_dirty()
        self._offer_rest_options("short")
        if dice_spent:
            self._toast(f"⏸ Short rest: spent {dice_spent} hit dice, healed {healed} HP")
        else:
            self._toast("⏸ Short rest complete — SR resources restored")
        if expired:
            self._toast(f"⏸ Faded: {', '.join(expired)}")

    def _long_rest(self):
        """Long rest: full HP, all resources reset, reduce exhaustion by 1."""
        from dnd_app.core.calculator import update_all
        from dnd_app.core.builder import rebuild
        char = self.char
        # Restore HP
        char["current_hp"] = char.get("max_hp", 0)
        char["temp_hp"] = 0
        # Restore hit dice as a shared pool across all die types (PHB p.186) —
        # NOT independently per type, which either under- or over-restored
        # depending on class layout.
        from dnd_app.core.calculator import restore_hit_dice_pool
        restore_hit_dice_pool(char)
        # Reset all LR resources
        for r in char.get("resources", []):
            if r.get("reset") in ("LR", "lr", "SR", "sr"):
                r["current"] = r.get("current_max") or r.get("max", 0)
        # Reset death saves
        char["death_saves"] = {"successes": 0, "failures": 0}
        # Reset spell slots (canonical shape: 9-element list, see character.py)
        char["spell_slots_used"] = [0] * 9
        char["pact_slots_used"] = 0
        char["_relentless_rage_uses"] = 0
        # Reduce exhaustion
        char["exhaustion"] = max(0, char.get("exhaustion", 0) - 1)
        expired = self._clear_expired_active_effects(("short", "long"))
        rebuild(char); update_all(char)
        self.ctrl.refresh()
        self._mark_dirty()
        self._offer_rest_options("long")
        from dnd_app.ui.flavor_text import random_long_rest_dream
        if expired:
            self._toast(f"🌙 Faded: {', '.join(expired)}")
        else:
            self._toast(f"🌙 Long rest complete — HP, slots & resources restored\n"
                        f"{random_long_rest_dream()}")

    def _clear_expired_active_effects(self, categories: tuple[str, ...]) -> list[str]:
        """Remove active_effects (mainly consumable potions) whose
        EFFECT_TABLE entry's duration_category is in categories — 'short'
        for effects lasting about an hour or less (a short rest takes at
        least that long per RAW), 'long' for effects that outlast a short
        rest but not a full night. Effects with no duration_category are
        untouched — same as they were before this existed, manual removal
        only. Returns the names actually removed, for the rest toast."""
        from dnd_app.core.effects import EFFECT_TABLE
        fx = self.char.get("active_effects", [])
        removed = [n for n in fx if EFFECT_TABLE.get(n, {}).get("duration_category") in categories]
        for n in removed:
            fx.remove(n)
        return removed

    def _offer_rest_options(self, rest_type: str):
        """Opens RestOptionsDialog after finishing a rest, and applies
        whichever rest-changeable options the player actually selected.
        Replaces the earlier Armorer-only prompt — that's now one option
        among however many the dialog finds applicable."""
        dlg = RestOptionsDialog(self.char, rest_type, self)
        if not dlg._options:
            return  # nothing to offer, don't bother showing an empty dialog
        if dlg.exec() != QDialog.Accepted:
            return
        selected = dlg.get_selected()
        if not selected:
            return
        char = self.char
        from dnd_app.core.builder import rebuild as _rebuild
        from dnd_app.core.calculator import update_all as _update_all
        changed_anything = False

        if "unprepare_all" in selected:
            bonus = set(char.get("bonus_spells", []))
            before = len(char.get("spells_prepared", []))
            char["spells_prepared"] = [n for n in char.get("spells_prepared", []) if n in bonus]
            removed = before - len(char["spells_prepared"])
            if removed:
                self._toast(f"📖 Unprepared {removed} spell(s) — pick new ones from the Spells tab")
                changed_anything = True
                # _refresh_spells() -> _sync_new_spell_rows() deliberately
                # never touches existing rows' checkbox state, to avoid
                # clobbering in-progress edits elsewhere — so after this
                # bulk clear, every spell row would stay visually checked
                # despite the underlying prepared list now being empty.
                # Every existing row is re-synced here directly to cover
                # this exception.
                if hasattr(self, "_spell_rows"):
                    for row in self._spell_rows:
                        if row.spell.get("name") not in bonus and row.spell.get("level", 0) > 0:
                            row.set_prepared(False)

        if "armorer_model" in selected:
            current = char.get("_choices", {}).get("armorer_model_3", [])
            pool = ["Guardian – Thunder Gauntlets (1d8 thunder, target has disadvantage attacking others); "
                    "bonus action: temp HP = artificer level, PB times/long rest",
                    "Infiltrator – Lightning Launcher (ranged 90/300ft, 1d6 lightning + extra 1d6 once/turn); "
                    "+5ft speed; advantage on Stealth checks"]
            current_idx = pool.index(current[0]) if current and current[0] in pool else 0
            choice, ok = QInputDialog.getItem(
                self, "Arcane Armor Model", "New model:", pool, 1 - current_idx, False)
            if ok and choice:
                char.setdefault("_choices", {})["armorer_model_3"] = [choice]
                self._toast(f"🛡️ Arcane Armor model changed to {choice.split(' – ')[0]}")
                changed_anything = True

        if "arcane_recovery" in selected:
            from math import ceil
            from dnd_app.core.calculator import class_levels
            from dnd_app.core.character import restore_spell_slot
            wiz_lvl = class_levels(char).get("Wizard", 0)
            budget = ceil(wiz_lvl / 2)
            dlg2 = ArcaneRecoveryDialog(char, budget, self)
            if dlg2.exec() == QDialog.Accepted:
                to_recover = dlg2.get_recovered_levels()  # list of slot-level ints
                for lvl in to_recover:
                    restore_spell_slot(char, lvl)
                if to_recover:
                    res = next((r for r in char.get("resources", []) if r.get("key") == "arcane_recovery"), None)
                    if res:
                        res["current"] = 0
                    self._toast(f"📗 Arcane Recovery: recovered {len(to_recover)} slot(s) "
                                f"(levels {', '.join(map(str, sorted(to_recover)))})")
                    changed_anything = True

        if "eladrin_season" in selected:
            pool = ["Autumn – Fey Step charms one creature within 5 ft. of your destination",
                    "Winter – Fey Step frightens one creature within 5 ft. of your destination",
                    "Spring – a willing creature within 5 ft. can teleport with you",
                    "Summer – Fey Step deals 2d6 fire damage to creatures within 5 ft. of your origin"]
            current = char.get("_choices", {}).get("eladrin_season", [])
            current_idx = pool.index(current[0]) if current and current[0] in pool else 0
            choice, ok = QInputDialog.getItem(
                self, "Eladrin Season", "New season:", pool, current_idx, False)
            if ok and choice:
                char.setdefault("_choices", {})["eladrin_season"] = [choice]
                self._toast(f"🍂 Eladrin season changed to {choice.split(' – ')[0]}")
                changed_anything = True

        if "pact_blade_bond" in selected:
            weapon_names = [i.get("name") if isinstance(i, dict) else i
                            for i in char.get("magic_items", [])]
            weapon_names = [n for n in weapon_names if n]
            if not weapon_names:
                QMessageBox.information(self, "Pact of the Blade",
                                        "You don't own a magic weapon to bond yet.")
            else:
                choice, ok = QInputDialog.getItem(
                    self, "Pact of the Blade", "Bond which magic weapon?", weapon_names, 0, False)
                if ok and choice:
                    char.setdefault("_choices", {})["pact_weapon_bond"] = [choice]
                    self._toast(f"\U0001f5e1\ufe0f {choice} bonded as your pact weapon")
                    changed_anything = True

        if "pact_tome_replace" in selected:
            self._toast("\U0001f4d5 Received a replacement Book of Shadows from your patron")
            changed_anything = True

        if "pact_talisman_replace" in selected:
            self._toast("\U0001f4ff Received a replacement Talisman from your patron")
            changed_anything = True

        if "guidance_spirits_swap" in selected:
            from dnd_app.ui.levelup_panel import ALL_SKILLS
            current = char.get("_choices", {}).get("guidance_of_the_spirits_skill", [])
            choice, ok = QInputDialog.getItem(
                self, "Guidance of the Spirits", "New skill:", ALL_SKILLS,
                ALL_SKILLS.index(current[0]) if current and current[0] in ALL_SKILLS else 0, False)
            if ok and choice:
                char.setdefault("_choices", {})["guidance_of_the_spirits_skill"] = [choice]
                self._toast(f"👻 Guidance of the Spirits now grants {choice}")
                changed_anything = True

        if "whispers_dead_swap" in selected:
            from dnd_app.ui.levelup_panel import ALL_SKILLS
            from dnd_app.data.feature_ui_interactions import TOOLS as ALL_TOOLS
            pool = ALL_SKILLS + ALL_TOOLS
            current = char.get("_choices", {}).get("whispers_of_the_dead_prof", [])
            choice, ok = QInputDialog.getItem(
                self, "Whispers of the Dead", "New proficiency:", pool,
                pool.index(current[0]) if current and current[0] in pool else 0, False)
            if ok and choice:
                char.setdefault("_choices", {})["whispers_of_the_dead_prof"] = [choice]
                self._toast(f"👻 Whispers of the Dead now grants {choice}")
                changed_anything = True

        if "lunar_phase_swap" in selected:
            pool = ["Full Moon", "New Moon", "Crescent Moon"]
            current = char.get("_choices", {}).get("lunar_phase", [])
            choice, ok = QInputDialog.getItem(
                self, "Lunar Embodiment", "New phase:", pool,
                pool.index(current[0]) if current and current[0] in pool else 0, False)
            if ok and choice:
                char.setdefault("_choices", {})["lunar_phase"] = [choice]
                self._toast(f"🌙 Lunar phase changed to {choice}")
                changed_anything = True

        if changed_anything:
            _rebuild(char); _update_all(char)
            self.ctrl.refresh()
            self._mark_dirty()

    def _save(self):
        """Save current character to disk."""
        from dnd_app.core.save_load import save_character
        import os
        name = self.char.get("name","Unknown").strip() or "Unknown"
        save_dir = os.path.expanduser("~/.dnd_characters")
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, f"{name}.json")
        save_character(self.char, path)
        self._dirty = False
        self._update_title()
        self._toast(f"💾 Saved to {os.path.basename(path)}")

    def _load_dialog(self):
        """Open a saved character via file dialog."""
        from PySide6.QtWidgets import QFileDialog
        from dnd_app.core.save_load import load_character
        import os
        save_dir = os.path.expanduser("~/.dnd_characters")
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Character", save_dir, "Character Files (*.json)")
        if path:
            char = load_character(path)
            if char:
                self.char.clear()
                self.char.update(char)
                self._save_path = path
                from dnd_app.core.builder import rebuild
                from dnd_app.core.calculator import update_all
                rebuild(self.char); update_all(self.char)
                self.ctrl.refresh()


    def confirm_leave(self) -> bool:
        """Prompt to save before leaving sheet. Returns True if safe to leave."""
        if getattr(self, "_confirm_leave_active", False):
            # Already showing (or just resolved) this exact prompt — a
            # second, near-simultaneous call means a signal fired twice
            # (e.g. connected more than once), not a genuine repeat request.
            return False
        self._confirm_leave_active = True
        try:
            self._collect()
            if not self._dirty:
                return True
            ans = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Save changes before returning to the menu?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if ans == QMessageBox.Cancel:
                return False
            if ans == QMessageBox.Save:
                self._save()
                return not self._dirty
            return True
        finally:
            self._confirm_leave_active = False

    def _on_back_clicked(self):
        # confirm_leave() is called by main_window.py's _sheet_back_to_menu,
        # which is what back_to_menu's connected slot actually runs — not
        # here too. Checking it in both places meant a single Back click
        # ran the unsaved-changes prompt twice in a row.
        self.back_to_menu.emit()

    def _build_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        # ── Slim top bar: name · identity chips · inspiration · save/load ─────
        header = QFrame(); header.setStyleSheet(f"QFrame{{background:{SURF};border-bottom:2px solid {BORDER};}}")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header); hl.setContentsMargins(16,0,16,0); hl.setSpacing(10)

        # ← Menu
        back_btn = QPushButton("← Menu")
        back_btn.setFixedWidth(90)
        back_btn.setStyleSheet(f"QPushButton{{background:{SURF2};border:1px solid {BORDER2};border-radius:7px;color:{TEXT2};font-size:{FS_SMALL}px;font-weight:700;padding:5px 10px;}}QPushButton:hover{{background:{SURF3};color:{TEXT};}}")
        back_btn.clicked.connect(self._on_back_clicked)
        hl.addWidget(back_btn)

        # Character name
        self._name_edit = QLineEdit(self.char.get("name",""))
        self._name_edit.setStyleSheet(f"QLineEdit{{font-size:{FS_HEAD}px;font-weight:700;color:{GOLD2};border:none;background:transparent;padding:0;}}")
        self._name_edit.setMinimumWidth(180)
        self._name_edit.setMaximumWidth(320)
        self._name_edit.textChanged.connect(self._on_name_changed)
        hl.addWidget(self._name_edit)

        # (Race/Subrace/Ancestry/Background edit buttons live in the Choices tab)

        # Subclass area (invisible placeholder — only used in the choices tab now via _refresh_subclass_area)
        self._subclass_area = QHBoxLayout(); self._subclass_area.setSpacing(0)
        self._subclass_combos = {}
        # (hidden — class controls live in Level Up tab)

        # Class summary chip — read-only, just shows e.g. "Fighter 5"
        self._class_summary = _lbl("", TEXT2, FS_SMALL, wrap=False)
        self._class_summary.setStyleSheet(f"color:{IND2};font-size:{FS_SMALL}px;font-weight:700;padding:2px 8px;"
                                           f"border:1px solid {qa(INDIGO,0x44)};border-radius:5px;background:{qa(INDIGO,0x11)};")
        hl.addWidget(self._class_summary)

        hl.addStretch()

        # Manual refresh — fail-safe in case a future edit reintroduces a
        # stale-tab bug. Forces every tab to repaint from current char data.
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh — repaint every tab from current character data")
        refresh_btn.setAccessibleName("Refresh all tabs")
        refresh_btn.setFixedSize(32,32)
        refresh_btn.setStyleSheet(
            f"QPushButton{{background:{SURF2};border:1px solid {BORDER};border-radius:7px;"
            f"color:{TEXT2};font-size:15px;padding:0;}}"
            f"QPushButton:hover{{background:{qa(TEAL,0x33)};border-color:{TEAL};color:{TEAL2};}}")
        refresh_btn.clicked.connect(self._force_full_refresh)
        hl.addWidget(refresh_btn)

        # Inspiration toggle
        self._insp_btn = QPushButton("☀")
        self._insp_btn.setToolTip("Inspiration")
        self._insp_btn.setCheckable(True)
        self._insp_btn.setChecked(self.char.get("inspiration", False))
        self._insp_btn.toggled.connect(self._on_inspiration_toggled)
        self._insp_btn.setFixedSize(32,32)
        self._insp_btn.setStyleSheet(
            f"QPushButton{{background:{SURF2};border:1px solid {BORDER};border-radius:7px;"
            f"color:{TEXT3};font-size:14px;padding:0;}}"
            f"QPushButton:checked{{background:{qa(GOLD,0x44)};border-color:{GOLD};color:{GOLD2};}}"
            f"QPushButton:hover{{border-color:{GOLD};color:{GOLD2};}}")
        hl.addWidget(self._insp_btn)

        # Save / Load
        for label, fn, color in [("💾","self._save",TEAL),("📂","self._load_dialog",INDIGO)]:
            fn_ref = self._save if label=="💾" else self._load_dialog
            b=QPushButton(label); b.setFixedSize(32,32)
            b.setToolTip("Save" if label=="💾" else "Load")
            b.setStyleSheet(f"QPushButton{{background:{qa(color,0x22)};border:1px solid {qa(color,0x55)};border-radius:7px;font-size:15px;padding:0;}}QPushButton:hover{{background:{qa(color,0x44)};border-color:{color};}}")
            b.clicked.connect(fn_ref); hl.addWidget(b)

        root.addWidget(header)

        # ── Status bar (AC, HP, Prof, Speed always visible) ───────────────────
        stat_bar = QFrame(); stat_bar.setStyleSheet(f"QFrame{{background:{SURF2};border-bottom:1px solid {BORDER};}}")
        stat_bar.setFixedHeight(64)
        sl = QHBoxLayout(stat_bar); sl.setContentsMargins(20,0,20,0); sl.setSpacing(24)

        self._sb_ac   = self._make_stat_pill("AC", "—", GOLD2)
        self._sb_hp   = self._make_stat_pill("HP", "—", GREEN2)
        self._sb_init = self._make_stat_pill("Initiative", "—", TEAL2)
        self._sb_prof = self._make_stat_pill("Prof Bonus", "—", IND2)
        self._sb_spd  = self._make_stat_pill("Speed", "—", TEXT)
        for pill in [self._sb_ac, self._sb_hp, self._sb_init, self._sb_prof, self._sb_spd]:
            sl.addWidget(pill)
        # Right-click AC / Speed for a breakdown of what contributes to them
        self._sb_ac.contextMenuEvent = lambda e: self._show_breakdown_popup(
            "Armor Class", get_ac_breakdown(self.char), str(get_ac(self.char)), e.globalPos())
        self._sb_spd.contextMenuEvent = lambda e: self._show_breakdown_popup(
            "Speed",
            [(lbl, val) for lbl, val in get_speed_breakdown(self.char)],
            f"{get_effective_speed(self.char)['walk']} ft", e.globalPos())
        # Initiative pill: click to roll
        self._sb_init.setToolTip("Click to roll initiative (d20 + Initiative bonus)")
        self._sb_init.setCursor(Qt.PointingHandCursor)
        self._sb_init.mousePressEvent = lambda e: self._roll_initiative()
        sl.addStretch()

        # Rest buttons in stat bar
        sr_btn = QPushButton("⏸ Short Rest")
        lr_btn = QPushButton("🌙 Long Rest")
        for btn, fn, c in [(sr_btn, self._short_rest, TEAL),(lr_btn, self._long_rest, INDIGO)]:
            btn.setFixedHeight(40)
            btn.setStyleSheet(f"QPushButton{{background:{qa(c,0x33)};border:2px solid {qa(c,0x88)};border-radius:8px;color:{TEXT};font-size:{FS_SMALL}px;font-weight:700;padding:6px 14px;}}QPushButton:hover{{background:{c};color:white;}}")
            btn.clicked.connect(fn); sl.addWidget(btn)

        root.addWidget(stat_bar)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.addTab(self._build_tab_abilities(),    "📊  Abilities & Saves")
        self._tabs.addTab(self._build_tab_skills(),       "🎲  Skills & Proficiencies")
        self._tabs.addTab(self._build_tab_combat(),       "⚔   Combat")
        self._tabs.addTab(self._build_tab_gear(),         "🎒  Gear & Items")
        self._tabs.addTab(self._build_tab_spells(),       "✨  Spells")
        if self._has_infuse_item_access():
            self._tabs.addTab(self._build_tab_infusions(), "\U0001f527  Infusions")
        self._tabs.addTab(self._build_tab_choices(),      "⚙   Choices")
        self._tabs.addTab(self._build_tab_features(),     "📖  Features")
        self._tabs.addTab(self._build_tab_traits_notes(), "📜  Traits & Notes")
        root.addWidget(self._tabs, 1)

    def _show_breakdown_popup(self, title: str, parts, total_str: str, global_pos):
        """Small dismissible popup listing each contribution to a stat,
        plus the running total — used for right-click breakdowns on AC,
        Speed, Save DC, and Attack Bonus.

        `parts` is either a list of (label, int) — shown with an explicit
        sign — or (label, str) — shown exactly as given (for non-additive
        notes like Haste's "×2")."""
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{SURF2};border:1px solid {BORDER2};color:{TEXT};padding:6px;}}"
            f"QMenu::item{{padding:4px 16px;}}"
            f"QMenu::item:disabled{{color:{TEXT2};}}"
            f"QMenu::separator{{height:1px;background:{BORDER};margin:4px 2px;}}")
        head = menu.addAction(f"  {title}")
        head.setEnabled(False)
        f = head.font(); f.setBold(True); head.setFont(f)
        menu.addSeparator()
        for label, val in parts:
            if isinstance(val, str):
                line = f"  {label}: {val}"
            else:
                line = f"  {label}: {'+' if val >= 0 else ''}{val}"
            act = menu.addAction(line)
            act.setEnabled(False)
        menu.addSeparator()
        total_act = menu.addAction(f"  Total: {total_str}")
        total_act.setEnabled(False)
        tf = total_act.font(); tf.setBold(True); total_act.setFont(tf)
        menu.exec(global_pos)

    def _make_stat_pill(self, label, value, color):
        f = QFrame(); f.setStyleSheet(f"QFrame{{background:{SURF};border:2px solid {qa(color,0x55)};border-radius:10px;}}")
        f.setFixedHeight(52); f.setMinimumWidth(96)
        l = QVBoxLayout(f); l.setContentsMargins(10,4,10,4); l.setSpacing(0)
        val = _lbl(str(value), color, FS_TITLE, bold=True, align=Qt.AlignCenter, wrap=False)
        ttl = _lbl(label, TEXT3, FS_TINY, align=Qt.AlignCenter, wrap=False)
        l.addWidget(val); l.addWidget(ttl)
        f._val = val; return f

    # ══ TAB 1: ABILITY SCORES & SAVES ══════════════════════════════════════════
    def _build_tab_abilities(self):
        tab = QScrollArea(); tab.setWidgetResizable(True)
        w = QWidget(); tab.setWidget(w); lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(16)

        # Ability score blocks
        ab_card = _card(); abcl = QVBoxLayout(ab_card); abcl.setContentsMargins(16,14,16,16)
        abcl.addWidget(_lbl("ABILITY SCORES", GOLD, FS_SMALL, bold=True))
        ab_row = QHBoxLayout(); ab_row.setSpacing(10)
        self._ab_blocks = {}
        for ab in ABILITIES:
            blk = AbilityBlock(ab, ability_score(self.char, ab), editable=False)
            ab_row.addWidget(blk); self._ab_blocks[ab] = blk
        ab_row.addStretch()
        abcl.addLayout(ab_row)

        # ASI note
        bonuses = self.char.get("ability_bonuses",{})
        parts = [f"{ab} +{v}" for ab,v in bonuses.items() if v>0]
        if parts:
            note = _lbl(f"Includes racial/ASI bonuses: {', '.join(parts)}", TEAL2, FS_SMALL)
            abcl.addWidget(note)
        lay.addWidget(ab_card)

        # Saving throws
        save_card = _card(); svcl = QVBoxLayout(save_card); svcl.setContentsMargins(16,14,16,16)
        svcl.addWidget(_lbl("SAVING THROWS", GOLD, FS_SMALL, bold=True))
        saves = all_saving_throw_bonuses(self.char)
        profs = get_saving_throw_profs(class_levels(self.char))
        save_grid = QGridLayout(); save_grid.setSpacing(8)
        self._save_widgets = {}
        for i, ab in enumerate(ABILITIES):
            val      = saves.get(ab, 0)
            is_class = ab in profs
            is_p     = is_class or self.char.get("saving_throws",{}).get(ab, False)
            color = TEAL2 if val > 0 else (CRIM2 if val < 0 else TEXT2)

            row_f = QFrame()
            row_f.setStyleSheet(f"QFrame{{background:{SURF3 if is_p else SURF2};border:1px solid {BORDER2 if is_p else BORDER};border-radius:8px;}}")
            rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)

            # Same interactive-dot pattern as Skills' proficiency symbol —
            # clicking the row toggles it, rather than a disabled read-only
            # indicator with no way to correct or override the auto-detected
            # class value (e.g. for a feat granting an extra save proficiency).
            dot = QCheckBox(); dot.setChecked(is_p)
            dot.setEnabled(not is_class)  # class-granted saves aren't user-revocable
            dot.setStyleSheet(f"QCheckBox::indicator{{width:16px;height:16px;border-radius:8px;border:2px solid {BORDER2};background:{BG};}}QCheckBox::indicator:checked{{background:{TEAL};border-color:{TEAL2};}}")

            val_lbl = _lbl(sign(val), color, FS_TITLE, bold=True, wrap=False, align=Qt.AlignRight)
            val_lbl.setFixedWidth(52)
            ab_lbl = _lbl(f"{AB_FULL[ab]}", TEXT, FS_BODY, bold=is_p, wrap=False)

            # 🎲 roll button — same role as Skills' roll button: rolls the
            # save without touching proficiency, which is now a separate
            # click target (the row itself, like Skills' cycle-on-click).
            roll_btn = QPushButton("🎲")
            roll_btn.setFixedSize(26, 24)
            roll_btn.setToolTip(f"Roll {AB_FULL[ab]} save ({sign(val)})")
            roll_btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:1px solid {BORDER};"
                f"border-radius:5px;font-size:{FS_SMALL}px;padding:0px;min-height:0px;}}"
                f"QPushButton:hover{{background:{qa(TEAL,0x33)};border-color:{TEAL};}}")
            roll_btn.clicked.connect(
                lambda checked=False, a=ab, v=val:
                    self._quick_roll_toast(f"{AB_FULL[a]} save", v))

            rl.addWidget(dot); rl.addWidget(val_lbl); rl.addWidget(ab_lbl)

            # Save advantage/disadvantage indicator — see
            # get_save_advantage_status() docstring for why this is shown
            # as an icon+tooltip rather than folded into val_lbl's number.
            # Always created (even if initially hidden) so _refresh_abilities_tab
            # can keep it in sync if class/level changes after the sheet
            # is already open, rather than only reflecting state from
            # whenever the tab was first built.
            adv_badge = _lbl("🎯", GOLD2, FS_BODY, bold=True, wrap=False)
            if not hasattr(self, "_save_adv_badges"):
                self._save_adv_badges = {}
            self._save_adv_badges[ab] = adv_badge
            self._update_save_advantage_badge(ab)
            rl.addWidget(adv_badge)

            # Condition-based auto-fail/disadvantage badge — separate from
            # the racial/class advantage badge above since it's a
            # different, transient mechanic (Paralyzed/Stunned/
            # Unconscious auto-fail STR/DEX saves outright; Restrained
            # imposes disadvantage on DEX specifically).
            cond_save_badge = _lbl("", CRIM2, FS_BODY, bold=True, wrap=False)
            if not hasattr(self, "_save_cond_badges"):
                self._save_cond_badges = {}
            self._save_cond_badges[ab] = cond_save_badge
            self._update_save_condition_badge(ab)
            rl.addWidget(cond_save_badge)

            rl.addWidget(roll_btn); rl.addStretch()

            # Click the row (or the dot) to toggle proficiency — mirrors
            # Skills' click-to-cycle exactly, just a 2-state toggle instead
            # of a 4-state cycle since saves don't have Expertise/Half.
            if is_class:
                row_f.setToolTip(f"{AB_FULL[ab]} save proficiency comes from your "
                                  f"class and can't be toggled off here — 🎲 rolls it")
            else:
                row_f.setCursor(Qt.PointingHandCursor)
                row_f.setToolTip(f"Click to toggle {AB_FULL[ab]} save proficiency  •  🎲 rolls it")
                row_f.mousePressEvent = lambda e, a=ab: self._toggle_save_prof(a)
                dot.toggled.connect(lambda checked, a=ab: self._toggle_save_prof(a, checked))

            # Special bonuses note
            if self.char.get("_paladin_aura"):
                cha = ability_mod(self.char, "CHA")
                note = _lbl(f"(+{max(1,cha)} Aura)", PURP2, FS_TINY, wrap=False)
                rl.addWidget(note)

            save_grid.addWidget(row_f, i//3, i%3)
            self._save_widgets[ab] = (dot, val_lbl)

        svcl.addLayout(save_grid)

        # Reliable talent note
        if has_reliable_talent(self.char):
            svcl.addWidget(_lbl("✦ Reliable Talent: minimum roll of 10 on proficient checks", AMBE2, FS_SMALL, bold=True))
        if self.char.get("_jack_of_all_trades"):
            svcl.addWidget(_lbl("✦ Jack of All Trades: +½ proficiency to non-proficient checks", IND2, FS_SMALL, bold=True))

        lay.addWidget(save_card)

        # Derived stats grid
        der_card = _card(); dcl = QVBoxLayout(der_card); dcl.setContentsMargins(16,14,16,16)
        dcl.addWidget(_lbl("DERIVED STATS", GOLD, FS_SMALL, bold=True))
        d_grid = QGridLayout(); d_grid.setSpacing(8)
        self._stat_boxes = {}
        pb = get_prof_bonus(self.char)
        ea = get_extra_attacks(class_levels(self.char), subclasses(self.char), self.char)
        from dnd_app.core.calculator import get_effective_speed, get_character_senses
        spd = get_effective_speed(self.char)["walk"]
        senses = get_character_senses(self.char)
        senses_str = ", ".join(f"{k.title()} {v} ft" for k, v in senses.items() if v > 0) or "—"
        if self.char.get("_devils_sight", False):
            senses_str += " (Devil's Sight: darkvision works through magical darkness too)"

        stats = [
            ("Prof Bonus", sign(pb), INDIGO),
            ("Initiative", sign(get_initiative(self.char)), TEAL2),
            ("Speed", f"{spd} ft", TEXT),
            ("Senses", senses_str, TEAL2),
            ("Passive Perc.", str(get_passive_perception(self.char)), TEAL),
            ("Extra Attacks", str(ea), GOLD),
            ("Carry Capacity", f"{get_carry_capacity(self.char)} lb", AMBER),
        ]
        mad = get_martial_arts_die(self.char)
        if mad != "—": stats.append(("Martial Arts", mad, IND2))
        rage = get_rage_damage(self.char)
        if rage != "—": stats.append(("Rage Damage", rage, CRIM2))

        for i, (label, val, color) in enumerate(stats):
            box = BigStatBox(label, val, color)
            box.setFixedWidth(140)
            d_grid.addWidget(box, i//4, i%4)
            self._stat_boxes[label] = box
        dcl.addLayout(d_grid); lay.addWidget(der_card)
        lay.addStretch()
        return tab

    # ══ TAB 2: SKILLS & PROFICIENCIES ══════════════════════════════════════════
    def _build_tab_skills(self):
        tab = QScrollArea(); tab.setWidgetResizable(True)
        w = QWidget(); tab.setWidget(w)
        root = QHBoxLayout(w); root.setContentsMargins(20,20,20,20); root.setSpacing(16)

        # Left: skills
        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(8)
        sk_card = _card()
        skcl = QVBoxLayout(sk_card); skcl.setContentsMargins(16,14,16,16); skcl.setSpacing(6)
        skcl.addWidget(_lbl("SKILLS", GOLD, FS_SMALL, bold=True))

        # Legend
        leg = QHBoxLayout(); leg.setSpacing(12)
        for sym, label, color in [("—","None",TEXT3),("◆","Proficient",INDIGO),("◈","Expertise",PURP2),("½","Half (Jack of All Trades)",IND2)]:
            lrow = QHBoxLayout(); lrow.setSpacing(4)
            lrow.addWidget(_lbl(sym, color, FS_BODY, bold=True, wrap=False))
            lrow.addWidget(_lbl(label, color, FS_SMALL, wrap=False))
            leg.addLayout(lrow)
        leg.addStretch(); skcl.addLayout(leg)

        reset_row = QHBoxLayout()
        reset_row.addStretch()
        reset_skills_btn = QPushButton("↺ Reset Manual Changes")
        reset_skills_btn.setToolTip(
            "Clears every skill proficiency and rebuilds them from scratch using only your "
            "actual grants (class, background, race, feat choices) — undoes any manual clicks "
            "that don't correspond to a real source.")
        reset_skills_btn.setStyleSheet(
            f"QPushButton{{background:{qa(CRIMSON,0x22)};border:1px solid {CRIMSON};"
            f"border-radius:6px;color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:5px 12px;}}"
            f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
        reset_skills_btn.clicked.connect(self._reset_manual_skill_changes)
        reset_row.addWidget(reset_skills_btn)
        skcl.addLayout(reset_row)
        skcl.addWidget(_sep())

        from dnd_app.core.calculator import has_jack_of_all_trades
        _jack = has_jack_of_all_trades(self.char)
        skills = all_skill_bonuses(self.char)
        self._skill_rows = {}
        for skill_name, bonus in sorted(skills.items()):
            prof_level = self.char.get("skills",{}).get(skill_name, 0)
            ab = SKILL_AB.get(skill_name,"STR")
            # Show ½ symbol for JoAT on non-proficient skills
            _disp_level = prof_level if prof_level > 0 else (1 if _jack else 0)
            sym = {0:"—",1:"½",2:"◆",3:"◈"}.get(_disp_level,"—")
            sym_color = {0:TEXT3,1:IND2,2:INDIGO,3:PURP2}.get(_disp_level,TEXT3)
            val_color = TEAL2 if bonus>0 else (CRIM2 if bonus<0 else TEXT2)

            row_f = QFrame()
            row_f.setStyleSheet(f"QFrame{{background:{SURF2 if prof_level>0 else SURF};border:1px solid {BORDER if prof_level==0 else BORDER2};border-radius:7px;}}")
            rl = QHBoxLayout(row_f); rl.setContentsMargins(10,7,10,7); rl.setSpacing(8)

            sym_l = _lbl(sym, sym_color, FS_BODY, bold=True, wrap=False, align=Qt.AlignCenter)
            sym_l.setFixedWidth(20)
            val_l = _lbl(sign(bonus), val_color, FS_LABEL, bold=True, wrap=False, align=Qt.AlignRight)
            val_l.setFixedWidth(44)
            name_l = _lbl(skill_name, TEXT if prof_level>0 else TEXT2, FS_BODY, wrap=False)
            name_l.setFixedWidth(148)  # fits "Animal Handling"/"Sleight of Hand" (longest names) so the (ABILITY) tags that follow always line up in a column
            ab_l = _lbl(f"({ab})", TEXT3, FS_SMALL, wrap=False)
            ab_l.setFixedWidth(46)  # all ability tags are "(XXX)" — fixed width keeps the roll button/stretch after it aligned consistently row to row

            # Advantage/disadvantage badge — populated by _refresh_skills
            adv_badge = _lbl("", TEXT3, FS_TINY, bold=True, wrap=False, align=Qt.AlignCenter)
            adv_badge.setFixedWidth(64)
            adv_badge.setVisible(False)

            # Right-click for an explicit menu of proficiency levels —
            # deliberately not a blind cycle-on-every-click. Cycling with no
            # visible options meant overshooting past the level you wanted
            # was easy, and there was no visibility into what state you'd
            # land on next; a menu makes the change deliberate and visible.
            row_f.mousePressEvent = (lambda e, sk=skill_name, rf=row_f:
                self._show_skill_prof_menu(sk, e.globalPos()) if e.button() == Qt.RightButton else None)
            row_f.setCursor(Qt.PointingHandCursor)
            row_f.setToolTip(f"Right-click to set proficiency level  •  🎲 button rolls the check")

            # 🎲 roll button — rolls d20 + skill bonus without touching proficiency
            roll_btn = QPushButton("🎲")
            roll_btn.setFixedSize(26, 24)
            roll_btn.setToolTip(f"Roll {skill_name} ({sign(bonus)})")
            roll_btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:1px solid {BORDER};"
                f"border-radius:5px;font-size:{FS_SMALL}px;padding:0px;min-height:0px;}}"
                f"QPushButton:hover{{background:{qa(TEAL,0x33)};border-color:{TEAL};}}")
            roll_btn.clicked.connect(
                lambda checked=False, sk=skill_name, b=bonus:
                    self._quick_roll_toast(f"{sk} check", b))

            rl.addWidget(sym_l); rl.addWidget(val_l); rl.addWidget(name_l); rl.addWidget(ab_l)
            rl.addWidget(roll_btn)
            rl.addStretch(); rl.addWidget(adv_badge)
            skcl.addWidget(row_f)
            self._skill_rows[skill_name] = (row_f, sym_l, val_l, name_l, adv_badge)

        ll.addWidget(sk_card); root.addWidget(left, 3)

        # Right: languages + proficiencies
        right = QWidget(); rl2 = QVBoxLayout(right); rl2.setSpacing(10)

        lang_card = _card(TEAL+"55"); lcl = QVBoxLayout(lang_card); lcl.setContentsMargins(14,12,14,14)
        lcl.addWidget(_lbl("LANGUAGES", TEAL2, FS_SMALL, bold=True))
        self._lang_lbl = _lbl("", TEXT2, FS_BODY, wrap=True)
        lcl.addWidget(self._lang_lbl); rl2.addWidget(lang_card)

        armor_card = _card(GOLD+"55"); acl = QVBoxLayout(armor_card); acl.setContentsMargins(14,12,14,14)
        acl.addWidget(_lbl("ARMOR PROFICIENCIES", GOLD, FS_SMALL, bold=True))
        self._armor_prof_lbl = _lbl("", TEXT2, FS_BODY); acl.addWidget(self._armor_prof_lbl)
        rl2.addWidget(armor_card)

        wpn_card = _card(IND2+"55"); wcl = QVBoxLayout(wpn_card); wcl.setContentsMargins(14,12,14,14)
        wcl.addWidget(_lbl("WEAPON PROFICIENCIES", IND2, FS_SMALL, bold=True))
        self._wpn_prof_lbl = _lbl("", TEXT2, FS_BODY); wcl.addWidget(self._wpn_prof_lbl)
        rl2.addWidget(wpn_card)

        tool_card = _card(AMBE2+"55"); tcl = QVBoxLayout(tool_card); tcl.setContentsMargins(14,12,14,14)
        tcl.addWidget(_lbl("TOOL PROFICIENCIES", AMBE2, FS_SMALL, bold=True))
        # Plain QWidget + QGridLayout, not FlowContainer/FlowLayout —
        # avoids FlowContainer.resizeEvent()'s setMinimumHeight()-inside-
        # a-resize-handler pattern, which can cause an infinite resize
        # loop in Qt with a custom QLayout subclass. A grid wraps at a
        # fixed column count instead of dynamically by pixel width, an
        # acceptable trade-off since tool names are short and this list
        # rarely exceeds a handful of entries.
        self._tool_prof_frame = QWidget(); self._tool_prof_frame.setStyleSheet("QWidget{background:transparent;}")
        self._tool_prof_lay = QGridLayout(self._tool_prof_frame)
        self._tool_prof_lay.setSpacing(4); self._tool_prof_lay.setContentsMargins(0,0,0,0)
        tcl.addWidget(self._tool_prof_frame)
        self._refresh_tool_prof_chips()
        rl2.addWidget(tool_card)
        rl2.addStretch(); root.addWidget(right, 2)
        return tab

    # Armor/shield are now equipped exclusively from the Gear tab
    # (see _toggle_armor_worn / _toggle_shield); Combat tab just displays them.

    def _on_inspiration_toggled(self, on: bool):
        self.ctrl.update("inspiration", on, rebuild_char=False)
        self._mark_dirty()

    def _show_skill_prof_menu(self, skill_name, global_pos):
        from PySide6.QtWidgets import QMenu
        curr = self.char.get("skills", {}).get(skill_name, 0)
        menu = QMenu(self)
        LEVELS = [
            (0, "Not Proficient"),
            (1, "Half Proficient (Jack of All Trades–style)"),
            (2, "Proficient"),
            (3, "Expertise (double proficiency)"),
        ]
        for level, label in LEVELS:
            marker = "\u2713 " if level == curr else "    "
            act = menu.addAction(f"{marker}{label}")
            act.triggered.connect(lambda checked=False, lv=level: self._set_skill_prof(skill_name, lv))
        menu.exec(global_pos)

    def _set_skill_prof(self, skill_name, level):
        self.ctrl.update(f"skills.{skill_name}", level)

    def _reset_manual_skill_changes(self):
        """Clear every skill proficiency and rebuild from scratch, keeping
        only what's actually granted (class/background/race/feat choices).
        char['skills'] is a pure accumulator that rebuild() only ever adds
        to, never clears — so any manual click that isn't backed by a real
        grant has no other way to be undone short of this."""
        from PySide6.QtWidgets import QMessageBox as _QMB
        confirm = _QMB.question(
            self, "Reset Skill Proficiencies",
            "This clears every skill proficiency and rebuilds them from scratch using only your "
            "actual grants (class, background, race, feat choices). Any manual click that isn't "
            "backed by a real grant will be undone. Continue?",
            _QMB.Yes | _QMB.No, _QMB.No)
        if confirm != _QMB.Yes:
            return
        from dnd_app.core.builder import rebuild
        self.char["skills"] = {}
        rebuild(self.char)
        self._mark_dirty()
        self._refresh_skills()
        self._toast("↺ Skill proficiencies reset to granted baseline")

    def _toggle_save_prof(self, ability, checked=None):
        """Toggle a manually-granted saving throw proficiency (e.g. from a
        feat). char['saving_throws'] itself is a fully DERIVED field —
        builder.rebuild() overwrites it from scratch every call based on
        class grants plus this list — so writing to saving_throws directly
        would just get stomped on the next rebuild. _choices.extra_save_profs
        is the actual persistent source or truth for a manual addition;
        class-granted proficiencies aren't stored here at all, so this can't
        accidentally remove a real class feature."""
        choices = self.char.setdefault("_choices", {})
        current = list(choices.get("extra_save_profs", []))
        is_extra = ability in current
        new_state = (not is_extra) if checked is None else checked
        if new_state and ability not in current:
            current.append(ability)
        elif not new_state and ability in current:
            current.remove(ability)
        self.ctrl.update("_choices.extra_save_profs", current)

    def _bind_death_and_conditions(self):
        if getattr(self, "_death_cond_bound", False):
            return
        ds = self.char.get("death_saves", {"successes": 0, "failures": 0})
        for i, cb in enumerate(self._death_success):
            cb.setChecked(i < ds.get("successes", 0))
            cb.stateChanged.connect(self._on_death_save_changed)
        for i, cb in enumerate(self._death_fail):
            cb.setChecked(i < ds.get("failures", 0))
            cb.stateChanged.connect(self._on_death_save_changed)
        active = set(self.char.get("conditions", []))
        for cond, cb in self._cond_checks.items():
            cb.blockSignals(True)
            cb.setChecked(cond in active)
            cb.blockSignals(False)
            cb.stateChanged.connect(lambda s, c=cond: self._on_condition_changed(c, bool(s)))
        self._death_cond_bound = True

    def _on_death_save_changed(self):
        succ = sum(1 for cb in self._death_success if cb.isChecked())
        fail = sum(1 for cb in self._death_fail if cb.isChecked())
        self.char["death_saves"] = {"successes": min(3, succ), "failures": min(3, fail)}
        if fail >= 3:
            self._show_death_screen()
        elif succ >= 3:
            # Stable at 1 HP
            self.char["current_hp"] = 1
            self._hp_current_hp.setValue(1)
            self.char["death_saves"] = {"successes": 0, "failures": 0}
            # Only update model — don't trigger full combat rebuild
            QMessageBox.information(self, "Stable", "You are stable! You regain consciousness with 1 HP.")
        self._mark_dirty()

    def _show_death_screen(self):
        # Persisted (not just a transient UI event) so that loading a
        # character who died and was saved before being revived shows
        # the death screen again on reopen, instead of silently landing
        # back on a live-looking sheet with no indication anything
        # happened. Only mark dirty on an actual new death, not when
        # __init__ re-shows this for an already-dead loaded character
        # (that shouldn't flag an untouched file as having unsaved edits).
        if not self.char.get("is_dead", False):
            self.char["is_dead"] = True
            self._mark_dirty()
        overlay = QFrame(self)
        overlay.setObjectName("death_overlay")
        overlay.setStyleSheet(
            "QFrame#death_overlay{background:rgba(0,0,0,210);}"
        )
        overlay.setGeometry(self.rect())
        overlay.raise_()
        vl = QVBoxLayout(overlay); vl.setAlignment(Qt.AlignCenter); vl.setSpacing(24)
        vl.addStretch(2)
        you_died = _lbl("YOU DIED", "#c00000", 72, bold=True, align=Qt.AlignCenter)
        you_died.setStyleSheet(
            "color:#c00000;font-size:72px;font-weight:900;letter-spacing:12px;"
            "text-shadow:0 0 40px #88ff0000;"
            "font-family:'Georgia','Times New Roman',serif;"
        )
        vl.addWidget(you_died)
        # Massive damage rule note
        note = _lbl("Instant death: damage ≥ 2× max HP in one hit", "#aa3333", FS_BODY,
                    align=Qt.AlignCenter, wrap=False)
        vl.addWidget(note)
        vl.addSpacing(32)
        revive_btn = QPushButton("  Revive  ")
        revive_btn.setFixedSize(200, 56)
        revive_btn.setStyleSheet(
            f"QPushButton{{background:#2a0000;border:2px solid #c00000;border-radius:10px;"
            f"color:#c00000;font-size:{FS_TITLE}px;font-weight:700;letter-spacing:4px;}}"
            f"QPushButton:hover{{background:#c00000;color:white;}}"
        )
        def _revive():
            overlay.deleteLater()
            if hasattr(self, "_toast_lbl"):
                self._toast_lbl.hide()
            self.char["is_dead"] = False
            self.char["current_hp"] = 1
            self.char["death_saves"] = {"successes": 0, "failures": 0}
            self.char["exhaustion"] = 0          # reviving clears exhaustion
            self._hp_current_hp.setValue(1)
            if hasattr(self, "_exh_combo"):
                self._exh_combo.blockSignals(True)
                self._exh_combo.setCurrentIndex(0)
                self._exh_combo.blockSignals(False)
            self._refresh_death_and_conditions()
            self.ctrl.update("current_hp", 1, rebuild_char=False)
            self._mark_dirty()
        revive_btn.clicked.connect(_revive)
        vl.addWidget(revive_btn, alignment=Qt.AlignCenter)
        vl.addStretch(3)
        overlay.show()

        # Critical Flavor (DM Secrets, optional rule, default off): a
        # random quip at the bottom of the screen -- the death overlay
        # above is centered and mechanical, this is a separate, smaller
        # aside underneath it.
        if self.char.get("optional_rules", {}).get("critical_flavor", False):
            from dnd_app.ui.flavor_text import random_death_message
            self._toast(random_death_message(), duration_ms=0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep death overlay covering the whole sheet
        for child in self.children():
            if isinstance(child, QFrame) and child.objectName() == "death_overlay":
                child.setGeometry(self.rect())

    def _on_condition_changed(self, cond: str, on: bool):
        active = set(self.char.get("conditions", []))
        if on:
            active.add(cond)
        else:
            active.discard(cond)
        self.char["conditions"] = sorted(active)
        self._refresh_active_conditions()
        self._mark_dirty()
            # Without this, condition-based mechanical indicators (saving
            # throw badges, weapon row advantage/disadvantage, speed)
            # would not update when a condition is toggled — only the
            # underlying data and the "Active Conditions" badge list
            # would change.
        self.ctrl.refresh()

    # ══ TAB 3: COMBAT ══════════════════════════════════════════════════════════

    def _edit_identity(self, slot: str):
        """Edit a character identity field (race/subrace/ancestry/background)."""
        from dnd_app.core.builder import rebuild
        from dnd_app.core.calculator import update_all
        if slot == "race":
            from dnd_app.data.races import RACE_NAMES
            name, ok = QInputDialog.getItem(self, "Edit Race", "Species / Race:", RACE_NAMES, 0, False)
            if ok and name:
                self.ctrl.update_many({"race": name, "species": name, "subrace": ""})
                self._refresh_stat_bar()
                self._edit_identity("subrace")

        elif slot == "subrace":
            from dnd_app.data.races import RACE_DICT
            import re as _re
            race = self.char.get("race", "")
            rdata = RACE_DICT.get(race, {})
            subraces_raw = rdata.get("subraces", [])
            if not subraces_raw:
                QMessageBox.information(self, "No Subraces", f"{race} has no subraces."); return
            _ASI_PAT = r"[+]([A-Z]{3})[ ](\d+)"
            _STRIP_PAT = r"[+][A-Z]{3}[ ]\d+,?[ ]*"
            options = []
            for sub_str in subraces_raw:
                name_part = sub_str.split("(")[0].strip()
                inner = sub_str[sub_str.find("(")+1:sub_str.rfind(")")]
                asis = ", ".join(f"{ab}+{n}" for ab, n in _re.findall(_ASI_PAT, inner))
                extra = _re.sub(_STRIP_PAT, "", inner).strip().strip(",").strip()
                desc = asis + (f"  ·  {extra[:50]}" if extra else "")
                options.append(f"{name_part}  ({desc})")
            current = self.char.get("subrace", "")
            cur_idx = next((i for i, o in enumerate(options) if o.startswith(current)), 0)
            choice, ok = QInputDialog.getItem(self, f"Choose Subrace — {race}", "Subrace:", options, cur_idx, False)
            if ok and choice:
                subrace_name = choice.split("(")[0].strip()
                self.char["subrace"] = subrace_name
                rebuild(self.char); update_all(self.char)
                self.ctrl.refresh()
                self._refresh_stat_bar()
                self._rebuild_features()
                self._mark_dirty()

        elif slot == "ancestry":
            if self.char.get("race", "") != "Dragonborn": return
            from dnd_app.data.races import DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE
            subrace = self.char.get("subrace", "Standard") or "Standard"
            avail = ANCESTRY_BY_SUBRACE.get(subrace, ANCESTRY_BY_SUBRACE.get("Standard", []))
            options = [f"{a}  –  {DRACONIC_ANCESTRY[a][0]}, {DRACONIC_ANCESTRY[a][1]}" for a in avail]
            cur = self.char.get("draconic_ancestry", "")
            cur_idx = next((i for i, o in enumerate(options) if o.startswith(cur)), 0)
            choice, ok = QInputDialog.getItem(self, "Draconic Ancestry", "Dragon type:", options, cur_idx, False)
            if ok and choice:
                self.char["draconic_ancestry"] = choice.split("–")[0].strip().split("  ")[0].strip()
                self._rebuild_features()
                self._refresh_stat_bar()
                self._mark_dirty()

        elif slot == "background":
            from dnd_app.data.backgrounds import BACKGROUND_NAMES, get_background
            name, ok = QInputDialog.getItem(self, "Edit Background", "Background:", BACKGROUND_NAMES, 0, False)
            if ok and name:
                self.ctrl.update("background", name)
                # Changing background here needs the same follow-up
                # prompts the creation wizard already runs for backgrounds
                # that grant a choice of feat (Rewarded/Ruined and others).
                bg = get_background(name)
                feat_choices = (bg or {}).get("feat_choices") or []
                if feat_choices:
                    feat_name, ok2 = QInputDialog.getItem(
                        self, name, f"{name} grants a choice of feat — which one?",
                        feat_choices, 0, False)
                    if ok2 and feat_name:
                        feats = self.char.setdefault("feats", [])
                        if feat_name not in feats:
                            feats.append(feat_name)
                self._mark_dirty()

    def _on_name_changed(self, text: str):
        self.char["name"] = text.strip() or "Unnamed"
        self._update_title()
        self._mark_dirty()

    # ════════════════════════════════════════════════════════════════════════
    # Character state helpers (refresh, collect, title, rest, level ops)
    # ════════════════════════════════════════════════════════════════════════

    def _update_title(self):
        """Sync window title with character name + dirty indicator."""
        name = self.char.get("name","Unnamed")
        dirty = " •" if self._dirty else ""
        if self.window():
            self.window().setWindowTitle(f"D&D 5e — {name}{dirty}")

    def _collect(self):
        """Flush current UI state into char dict (name etc.)."""
        if hasattr(self, "_name_edit"):
            self.char["name"] = self._name_edit.text().strip() or "Unnamed"

    # ── Refresh helpers ───────────────────────────────────────────────────────

    def _sync_slot_bars_from_char(self):
        """Sync slot-bar widgets from char's spell_slots_used data."""
        if not hasattr(self, "_slot_bars"):
            return
        from dnd_app.core.multiclass import compute_all_spell_slots
        from dnd_app.core.calculator import class_levels, subclasses
        slot_data = compute_all_spell_slots(class_levels(self.char), subclasses(self.char))
        slot_list = slot_data.get("spell_slots") or [0]*9   # index 0 = level 1
        # spell_slots_used is canonically a 9-element list (index 0 = level 1),
        # matching character.py's use_spell_slot()/recover_spell_slot()/long_rest().
        # Read defensively in case an older save has the legacy dict shape.
        used_raw = self.char.get("spell_slots_used", [0]*9)
        if isinstance(used_raw, dict):
            used_list = [used_raw.get(str(i), 0) for i in range(1, 10)]
            self.char["spell_slots_used"] = used_list   # self-heal on read
            used_raw = used_list
        for lvl, bar in self._slot_bars.items():
            idx = lvl - 1
            total = slot_list[idx] if 0 <= idx < len(slot_list) else 0
            used = used_raw[idx] if 0 <= idx < len(used_raw) else 0
            bar.set_max(total)
            bar.set_used(min(used, total))
        if hasattr(self, "_pact_bar"):
            from dnd_app.core.multiclass import get_warlock_slots
            from dnd_app.core.calculator import class_levels
            _wlvl = class_levels(self.char).get("Warlock", 0)
            _ps = get_warlock_slots(_wlvl) if _wlvl else {}
            _pact_max = _ps.get("count", 0)
            self._pact_bar.set_max(_pact_max)
            self._pact_bar.set_used(self.char.get("pact_slots_used", 0))
            if hasattr(self, "_pact_card"):
                self._pact_card.setVisible(_pact_max > 0)

    def _refresh_spells(self):
        """Update spell-tab slot bars, count labels and concentration state."""
        if not hasattr(self, "_slot_bars"):
            return
        try:
            self._sync_new_spell_rows()
        except Exception:
            pass
        try:
            self._remove_stale_spell_rows()
        except Exception:
            pass
        try:
            self._sync_slot_bars_from_char()
        except Exception:
            pass
        try:
            self._refresh_spell_count_labels()
        except Exception:
            pass
        try:
            self._refresh_concentration()
        except Exception:
            pass
        try:
            # Re-apply the browser's castable-level/class-list filter,
            # since the character's max castable spell level (and class
            # list) can change on level-up while the sheet is already open.
            self._filter_spell_browser()
        except Exception:
            pass

    def _remove_stale_spell_rows(self):
        """Remove any spell row whose spell is no longer in
        char['spells_known'] at all — the symmetric counterpart to
        _sync_new_spell_rows(), which only ever adds rows. Confirmed via
        direct reproduction that a spell becoming stale (e.g. a Circle
        of the Land Druid switching terrain, dropping their old
        bonus spells from spells_known) previously left its row
        lingering on the tab forever, still checked as prepared, since
        nothing but the manual ✕ button ever removed a row. This is a
        genuinely different case from what _sync_new_spell_rows()
        deliberately protects (in-progress edits on spells that are
        still validly known) — a spell that's not known at all anymore
        has nothing to preserve."""
        if not hasattr(self, "_spell_rows"):
            return
        known = set(self.char.get("spells_known", []))
        stale_rows = [r for r in self._spell_rows if r.spell.get("name") not in known]
        for row in stale_rows:
            self._remove_spell_row(row)

    def _sync_new_spell_rows(self):
        """Add a row for any spell in char['spells_known'] that isn't
        displayed yet — e.g. a full-list prepared caster (Cleric/Druid/
        Paladin/Artificer) gaining access to a new spell level on level-up,
        or a bonus spell (domain/oath/circle) becoming available. Never
        removes or rebuilds existing rows, so in-progress prepared/pin
        toggles the player has already set are left alone; a spell that's
        no longer eligible (e.g. switching Circle of the Land terrain) is
        cleaned up separately by the bonus-spell staleness check in
        builder.py, which also prunes it from spells_known itself."""
        if not hasattr(self, "_spell_rows"):
            return
        from dnd_app.data.spells import get_spell as _gs
        shown = {r.spell.get("name") for r in self._spell_rows}
        prepared_set = set(self.char.get("spells_prepared", []))
        for name in self.char.get("spells_known", []):
            if name in shown:
                continue
            sp = _gs(name)
            if sp:
                self._add_spell_row(sp, prepared=(name in prepared_set))
                shown.add(name)

    def _refresh_death_and_conditions(self):
        """Update death-save checkboxes and condition toggles (non-destructive).
        Never rebuilds widgets — only calls setChecked. Never touches HP spinboxes."""
        if not hasattr(self, "_death_success"):
            return
        # Show/hide the death-saves container based on HP
        at_zero = self.char.get("current_hp", 1) <= 0
        if hasattr(self, "_death_saves_container"):
            self._death_saves_container.setVisible(at_zero)
        ds = self.char.get("death_saves", {"successes": 0, "failures": 0})
        for i, cb in enumerate(self._death_success):
            cb.blockSignals(True)
            cb.setChecked(i < ds.get("successes", 0))
            cb.blockSignals(False)
        for i, cb in enumerate(self._death_fail):
            cb.blockSignals(True)
            cb.setChecked(i < ds.get("failures", 0))
            cb.blockSignals(False)
        if hasattr(self, "_cond_checks"):
            active = set(self.char.get("conditions", []))
            for cond, cb in self._cond_checks.items():
                cb.blockSignals(True)
                cb.setChecked(cond in active)
                cb.blockSignals(False)

    def _refresh_optional_features(self):
        """Rebuild the Optional Class Features card in the Features tab."""
        # No-op if not yet built; features tab handles this via _rebuild_features.
        pass

    # ── Hit dice / currency event handlers ───────────────────────────────────

    def _on_hd_changed(self, hd_key: str, value: int, total: int):
        """User changed a hit-dice spinbox."""
        hd = self.char.setdefault("hit_dice", {})
        hd.setdefault(hd_key, {"total": total, "remaining": total})["remaining"] = value
        self._mark_dirty()

    def _on_currency_change(self, coin: str, value: int):
        """User changed a currency spinbox (gp, sp, cp, ep, pp)."""
        self.char.setdefault("currency", {})[coin] = value
        self._mark_dirty()

    # ── Level-up / class management ───────────────────────────────────────────

    def _open_level_up_or_multiclass(self):
        """Unified Level Up / Multiclass panel — replaces the separate
        Level Up and Add Multiclass buttons. See LevelUpMulticlassDialog
        for the full behavior."""
        from dnd_app.data.classes import CLASS_DICT
        from dnd_app.core.character import add_class
        dlg = LevelUpMulticlassDialog(self.char, self)
        if dlg.exec() != QDialog.Accepted:
            return
        cls_name, is_new = dlg.get_result()
        if not cls_name:
            return
        swap_old, swap_new = dlg.get_spell_swap()
        eldritch_versatility = dlg.get_eldritch_versatility()

        if is_new:
            # Same ability score prerequisite check as before — kept as a
            # safety net even though the dialog already grays out
            # ineligible classes entirely, in case of any edge case (e.g.
            # abilities changing between opening the dialog and confirming).
            existing = {c["class"] for c in self.char.get("classes", [])}

            def _meets_reqs(class_name):
                reqs = CLASS_DICT.get(class_name, {}).get("multiclass_reqs", {})
                if not reqs:
                    return True, ""
                if not self.char.get("optional_rules", {}).get("multiclass_ability_reqs", True):
                    return True, ""
                base_scores = self.char.get("abilities", {})
                bonuses = self.char.get("ability_bonuses", {})
                scores = {ab: base_scores.get(ab, 10) + bonuses.get(ab, 0) for ab in
                          ("STR", "DEX", "CON", "INT", "WIS", "CHA")}
                if class_name == "Fighter":
                    if any(scores.get(ab, 0) >= val for ab, val in reqs.items()):
                        return True, ""
                    req_text = " or ".join(f"{ab} {val}" for ab, val in reqs.items())
                    return False, f"{class_name} requires {req_text}"
                missing = [f"{ab} {val}" for ab, val in reqs.items() if scores.get(ab, 0) < val]
                if missing:
                    return False, f"{class_name} requires " + " and ".join(missing)
                return True, ""

            fails = []
            for existing_cls in existing:
                ok_req, msg = _meets_reqs(existing_cls)
                if not ok_req: fails.append(msg)
            ok_req, msg = _meets_reqs(cls_name)
            if not ok_req: fails.append(msg)
            if fails:
                QMessageBox.warning(
                    self, "Multiclass Requirements Not Met",
                    "This character doesn't meet the ability score prerequisites to multiclass:\n\n"
                    + "\n".join(f"• {f}" for f in fails))
                return
            hd = CLASS_DICT.get(cls_name, {}).get("hit_die", 8)
            add_class(self.char, cls_name, 1, "", hd)
        else:
            entry = next(c for c in self.char.get("classes", []) if c["class"] == cls_name)
            entry["level"] = min(20, entry["level"] + 1)

        if swap_old and swap_new:
            known = self.char.setdefault("spells_known", [])
            if swap_old in known:
                known.remove(swap_old)
            if swap_new not in known:
                known.append(swap_new)
            for field in ("spells_prepared", "quick_spells"):
                lst = self.char.get(field, [])
                if swap_old in lst:
                    lst.remove(swap_old)
            self._toast(f"📖 Swapped {swap_old} for {swap_new}")

        if eldritch_versatility:
            kind = eldritch_versatility["kind"]
            old, new = eldritch_versatility["old"], eldritch_versatility["new"]
            if kind == "cantrip":
                known = self.char.setdefault("spells_known", [])
                if old in known: known.remove(old)
                if new not in known: known.append(new)
                self._toast(f"📖 Eldritch Versatility: swapped cantrip {old} for {new}")
            elif kind == "pact_boon":
                self.char.setdefault("_choices", {})["warlock_pact_boon"] = [new]
                # Cascading Eldritch Invocation re-check, per the actual
                # rule text: if this change makes an invocation
                # ineligible, remove it so the player must re-choose via
                # the existing invocation chooser (which already only
                # offers eligible options).
                new_boon_name = next((b for b in ("blade", "chain", "tome", "talisman")
                                     if b in new.lower()), "")
                new_pact_tag = f"(pact of the {new_boon_name})" if new_boon_name else ""
                invocations = self.char.get("eldritch_invocations", [])
                kept = []
                removed = []
                for inv in invocations:
                    inv_lower = inv.lower()
                    if "pact of the" in inv_lower and new_pact_tag and new_pact_tag not in inv_lower:
                        removed.append(inv)
                    else:
                        kept.append(inv)
                self.char["eldritch_invocations"] = kept
                if removed:
                    self._toast(f"🔮 Pact Boon changed to {new.split(' – ')[0] if ' – ' in new else new.split('(')[0].strip()} "
                                f"— {len(removed)} invocation(s) no longer eligible, re-choose them in the Choices tab")
                else:
                    self._toast(f"🔮 Pact Boon changed to {new.split('(')[0].strip()}")
            elif kind == "arcanum":
                spell_lvl, old_name = old
                self.char.setdefault("_choices", {})[f"mystic_arcanum_{spell_lvl}"] = [new]
                self._toast(f"📖 Eldritch Versatility: swapped Mystic Arcanum {old_name} for {new}")

        mv_kind, mv_old, mv_new = dlg.get_martial_versatility()
        if mv_kind and mv_old and mv_new:
            if mv_kind == "style":
                styles = self.char.setdefault("fighting_styles", [])
                if mv_old in styles:
                    styles.remove(mv_old)
                styles.append(mv_new)
                self._toast(f"⚔ Martial Versatility: swapped {mv_old.split(' (')[0].strip()} "
                            f"for {mv_new.split(' (')[0].strip()}")
            elif mv_kind == "maneuver":
                maneuvers = self.char.setdefault("battle_master_maneuvers", [])
                if mv_old in maneuvers:
                    maneuvers.remove(mv_old)
                maneuvers.append(mv_new)
                self._toast(f"⚔ Martial Versatility: swapped maneuver {mv_old.split(' – ')[0].strip()} "
                            f"for {mv_new.split(' – ')[0].strip()}")

        cv_old, cv_new = dlg.get_cantrip_versatility()
        if cv_old and cv_new:
            known = self.char.setdefault("spells_known", [])
            if cv_old in known: known.remove(cv_old)
            if cv_new not in known: known.append(cv_new)
            self._toast(f"📖 Cantrip Versatility: swapped {cv_old} for {cv_new}")

        bv_kind, bv_old, bv_new = dlg.get_bardic_versatility()
        if bv_kind and bv_old and bv_new:
            if bv_kind == "expertise":
                skills = self.char.setdefault("skills", {})
                skills[bv_old] = 2
                skills[bv_new] = 3
                self._toast(f"🎵 Bardic Versatility: moved Expertise from {bv_old} to {bv_new}")
            elif bv_kind == "cantrip":
                known = self.char.setdefault("spells_known", [])
                if bv_old in known: known.remove(bv_old)
                if bv_new not in known: known.append(bv_new)
                self._toast(f"🎵 Bardic Versatility: swapped {bv_old} for {bv_new}")

        sv_kind, sv_old, sv_new = dlg.get_sorcerous_versatility()
        if sv_kind and sv_old and sv_new:
            if sv_kind == "metamagic":
                mm = self.char.setdefault("_choices", {}).setdefault("sorcerer_metamagic", [])
                if sv_old in mm: mm.remove(sv_old)
                mm.append(sv_new)
                self._toast(f"✨ Sorcerous Versatility: swapped metamagic {sv_old.split(' – ')[0].strip()} "
                            f"for {sv_new.split(' – ')[0].strip()}")
            elif sv_kind == "cantrip":
                known = self.char.setdefault("spells_known", [])
                if sv_old in known: known.remove(sv_old)
                if sv_new not in known: known.append(sv_new)
                self._toast(f"✨ Sorcerous Versatility: swapped {sv_old} for {sv_new}")

        self.char["_last_leveled_class"] = cls_name
        self.ctrl.refresh()
        self._mark_dirty()

    def _open_level_up(self):
        """Add one level to an existing class (prompt if multi-class)."""
        from PySide6.QtWidgets import QInputDialog
        from dnd_app.core.character import add_class
        from dnd_app.core.builder import rebuild
        from dnd_app.core.calculator import update_all
        classes = self.char.get("classes", [])
        if not classes:
            QMessageBox.warning(self, "No Class", "Add a class first."); return
        if len(classes) == 1:
            cls_name = classes[0]["class"]
        else:
            names = [f"{c['class']} (Lv{c['level']})" for c in classes]
            choice, ok = QInputDialog.getItem(self, "Level Up", "Choose class:", names, 0, False)
            if not ok: return
            cls_name = choice.split(" (")[0]
        entry = next(c for c in classes if c["class"] == cls_name)
        entry["level"] = min(20, entry["level"] + 1)
        self.ctrl.refresh()                         # rebuild + update_all + notify
        # _on_char_updated() (subscribed above) already calls both
        # _populate_subclass_combo() and self._levelup_panel.refresh() —
        # calling them again here duplicated the entire pending-choices
        # rebuild in immediate succession, which is the likely cause of
        # the "windows popping up and immediately deleting themselves"
        # symptom reported specifically during level-up (a manual refresh,
        # which doesn't go through this doubled path, doesn't show it).
        self._mark_dirty()

    def _open_level_down(self):
        """Remove one level from an existing class."""
        from PySide6.QtWidgets import QInputDialog
        from dnd_app.core.builder import rebuild, get_choices_needed
        from dnd_app.core.calculator import update_all
        from dnd_app.ui.levelup_panel import _get_subclass_choices, _get_race_choices, _get_class_tool_choices, _get_dm_reward_choices
        import copy
        classes = self.char.get("classes", [])
        if not classes:
            return
        if len(classes) == 1:
            cls_name = classes[0]["class"]
        else:
            names = [f"{c['class']} (Lv{c['level']})" for c in classes]
            choice, ok = QInputDialog.getItem(self, "Level Down", "Choose class:", names, 0, False)
            if not ok: return
            cls_name = choice.split(" (")[0]
        entry = next(c for c in classes if c["class"] == cls_name)
        if entry["level"] <= 1:
            QMessageBox.information(self, "Minimum", f"{cls_name} is already level 1."); return

        # Diff the full set of structurally-relevant choice IDs (not just
        # pending ones — a scratch copy with _choices cleared makes every
        # relevant choice show up as "pending" regardless of whether it
        # was already answered) before and after the level decrement, and
        # clear any choice from the real character that's no longer valid
        # at the new, lower level. Without this, delevelling silently kept
        # every prior choice (Fighting Style, ASI, subclass picks, etc.)
        # locked in forever, with no way to ever pick differently.
        def _relevant_ids(char_snapshot):
            scratch = copy.deepcopy(char_snapshot)
            scratch["_choices"] = {}
            all_choices = (get_choices_needed(scratch) + _get_subclass_choices(scratch)
                           + _get_race_choices(scratch) + _get_class_tool_choices(scratch)
                           + _get_dm_reward_choices(scratch))
            return {c["id"] for c in all_choices if "id" in c}

        old_ids = _relevant_ids(self.char)
        entry["level"] -= 1
        new_ids = _relevant_ids(self.char)
        removed_ids = old_ids - new_ids
        choices_store = self.char.get("_choices", {})
        for cid in removed_ids:
            choices_store.pop(cid, None)

        self.ctrl.refresh()
        # self.ctrl.refresh() already triggers _populate_subclass_combo()
        # and _levelup_panel.refresh() via the observer chain (see
        # _open_level_up for the full explanation) — no need to call
        # them again here.
        self._mark_dirty()

    def _open_add_multiclass(self):
        """Add a new class for multiclassing."""
        from PySide6.QtWidgets import QInputDialog
        from dnd_app.data.classes import CLASS_NAMES, CLASS_DICT
        from dnd_app.core.character import add_class
        from dnd_app.core.builder import rebuild
        from dnd_app.core.calculator import update_all
        existing = {c["class"] for c in self.char.get("classes", [])}
        available = [n for n in CLASS_NAMES if n not in existing]
        if not available:
            QMessageBox.information(self, "All Classes", "All classes are already added."); return
        cls_name, ok = QInputDialog.getItem(self, "Add Multiclass", "New class:", available, 0, False)
        if not ok: return

        # Ability score prerequisites — per the 2014 PHB multiclassing
        # rule, a character must meet the requirements for BOTH their
        # current class(es) and the new one.
        def _meets_reqs(class_name):
            reqs = CLASS_DICT.get(class_name, {}).get("multiclass_reqs", {})
            if not reqs:
                return True, ""
            if not self.char.get("optional_rules", {}).get("multiclass_ability_reqs", True):
                return True, ""
            base_scores = self.char.get("abilities", {})
            bonuses = self.char.get("ability_bonuses", {})
            scores = {ab: base_scores.get(ab, 10) + bonuses.get(ab, 0) for ab in
                      ("STR", "DEX", "CON", "INT", "WIS", "CHA")}
            if class_name == "Fighter":
                # The one special "OR" case: STR 13 or DEX 13, either
                # sufficing — every other multi-ability requirement below
                # is a strict AND.
                if any(scores.get(ab, 0) >= val for ab, val in reqs.items()):
                    return True, ""
                req_text = " or ".join(f"{ab} {val}" for ab, val in reqs.items())
                return False, f"{class_name} requires {req_text}"
            missing = [f"{ab} {val}" for ab, val in reqs.items() if scores.get(ab, 0) < val]
            if missing:
                return False, f"{class_name} requires " + " and ".join(missing)
            return True, ""

        fails = []
        for existing_cls in existing:
            ok_req, msg = _meets_reqs(existing_cls)
            if not ok_req: fails.append(msg)
        ok_req, msg = _meets_reqs(cls_name)
        if not ok_req: fails.append(msg)
        if fails:
            QMessageBox.warning(
                self, "Multiclass Requirements Not Met",
                "This character doesn't meet the ability score prerequisites to multiclass:\n\n"
                + "\n".join(f"• {f}" for f in fails)
                + "\n\nPer the 2014 PHB rule, you need at least a 13 in the relevant "
                  "ability score(s) for both your current class(es) and the new one.")
            return

        hd = CLASS_DICT.get(cls_name, {}).get("hit_die", 8)
        add_class(self.char, cls_name, 1, "", hd)
        self.ctrl.refresh()
        # See _open_level_up — self.ctrl.refresh() already triggers both
        # calls via the observer chain.
        self._mark_dirty()

    def _open_remove_class(self):
        """Remove an entire class (multiclass only — keeps at least one)."""
        from PySide6.QtWidgets import QInputDialog
        from dnd_app.core.builder import rebuild
        from dnd_app.core.calculator import update_all
        classes = self.char.get("classes", [])
        if len(classes) <= 1:
            QMessageBox.information(self, "Can't Remove", "Cannot remove the only class."); return
        names = [f"{c['class']} (Lv{c['level']})" for c in classes]
        choice, ok = QInputDialog.getItem(self, "Remove Class", "Remove which class?", names, 0, False)
        if not ok: return
        cls_name = choice.split(" (")[0]
        self.char["classes"] = [c for c in classes if c["class"] != cls_name]
        self.ctrl.refresh()
        # See _open_level_up — self.ctrl.refresh() already triggers both
        # calls via the observer chain.
        self._mark_dirty()

    def _wildshape_resource(self):
        """The formal char['resources'] entry for Wild Shape (key
        'wild_shape') -- the SAME entry the Passive/Other tab's generic
        resource tracker (_build_resource_rows) reads and writes. This
        card previously tracked uses via a separate, disconnected
        char['_wildshape_uses_spent'] counter: transforming here never
        moved that tab's pips, and editing that tab's spinbox never
        blocked/allowed a transform here. Returns None if Wild Shape
        isn't available yet (not a Druid, or below 2nd level)."""
        return next((r for r in self.char.get("resources", [])
                     if r.get("key") == "wild_shape"), None)

    def _wildshape_uses_left(self):
        """(uses_remaining, uses_max), both ints -- or (None, None) for
        unlimited (Archdruid, 20th level: current_max is the string
        "Unlimited" at that point, not a number)."""
        res = self._wildshape_resource()
        if res is None:
            return (0, 0)
        mx = res.get("current_max", 0)
        if not isinstance(mx, int):
            return (None, None)
        return (res.get("current", 0), mx)

    def _spend_wildshape_use(self) -> bool:
        """Spend one Wild Shape use against the shared resource. Returns
        False (and spends nothing) if none remain; always True for
        unlimited (Archdruid)."""
        res = self._wildshape_resource()
        if res is None:
            return False
        mx = res.get("current_max", 0)
        if not isinstance(mx, int):
            return True
        cur = res.get("current", 0)
        if cur <= 0:
            return False
        res["current"] = cur - 1
        return True

    def _build_wildshape_control_card(self) -> QFrame:
        """Wild Shape transformation control — prime (pick a beast), fire
        (transform, consuming one use), reload (the use is spent
        automatically as part of firing, not a separate step the player
        has to remember). While transformed, shows the beast's own HP pool
        (tracked separately from the character's own HP, matching the real
        rule that you don't lose your own HP while shapeshifted) with a
        Revert control.

        Known limitation: this does not yet cascade the beast's ability
        scores into every downstream calculation (skills, saves, etc.) —
        it tracks the transformation state, uses, and a separate HP pool
        correctly, and shows the beast's stat block, but a full sheet-wide
        override of STR/DEX/CON-driven calculations is a larger follow-up."""
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        from dnd_app.core.calculator import get_available_wildshape_beasts

        card = _card(PURPLE+"55")
        cl = QVBoxLayout(card); cl.setContentsMargins(12,10,12,10); cl.setSpacing(6)
        cl.addWidget(_lbl("WILD SHAPE", GOLD, FS_SMALL, bold=True))

        active = self.char.get("_wildshape_active")
        if active and active in WILDSHAPE_BEASTS:
            beast = WILDSHAPE_BEASTS[active]
            cl.addWidget(_lbl(f"Currently: {active}", PURP2, FS_BODY, bold=True, wrap=False))
            cur_hp = self.char.get("_wildshape_hp", beast["hp"])
            cl.addWidget(_lbl(f"HP {cur_hp}/{beast['hp']}   AC {beast['ac']}   "
                              f"(edit HP in the card above — same pool)", TEXT2, FS_SMALL))
            # Circle of the Moon's Combat Wild Shape: while transformed,
            # spend a spell slot as a bonus action to regain 1d8 HP per
            # level of the slot expended.
            from dnd_app.core.calculator import subclasses as _subclasses_wsc, class_levels as _cl_wsc
            is_moon_wsc = "moon" in _subclasses_wsc(self.char).get("Druid", "").lower()
            if is_moon_wsc:
                slots_used = self.char.get("spell_slots_used", [0]*9)
                from dnd_app.core.multiclass import compute_all_spell_slots
                slot_data = compute_all_spell_slots(_cl_wsc(self.char), _subclasses_wsc(self.char))
                slots_max = slot_data.get("spell_slots") or [0]*9
                has_slot = any(slots_max[i] - (slots_used[i] if i < len(slots_used) else 0) > 0 for i in range(9))
                heal_btn = QPushButton("\U0001f52e Combat Wild Shape: Spend Slot to Heal")
                heal_btn.setEnabled(has_slot and cur_hp < beast["hp"])
                heal_btn.setToolTip("Bonus action: expend a spell slot to regain 1d8 HP per level of the slot.")
                heal_btn.setStyleSheet(pill_btn("", GOLD).styleSheet())
                heal_btn.clicked.connect(self._wildshape_moon_heal)
                cl.addWidget(heal_btn)
            revert_btn = QPushButton("Revert to Normal Form")
            revert_btn.setStyleSheet(pill_btn("", CRIMSON).styleSheet())
            revert_btn.clicked.connect(self._wildshape_revert)
            cl.addWidget(revert_btn)
        else:
            available = get_available_wildshape_beasts(self.char)
            picker_row = QHBoxLayout(); picker_row.setSpacing(8)
            combo = QComboBox(); combo.setAccessibleName("Choose a beast to Wild Shape into")
            for name in available:
                b = WILDSHAPE_BEASTS.get(name, {})
                combo.addItem(f"{name} (CR {b.get('cr_label','?')})", name)
            picker_row.addWidget(combo, 1)
            cl.addLayout(picker_row)

            uses_left, uses_max = self._wildshape_uses_left()
            if uses_left is None:
                cl.addWidget(_lbl("Unlimited uses (Archdruid)", TEXT2, FS_SMALL))
            else:
                cl.addWidget(_lbl(f"{uses_left}/{uses_max} uses remaining (short/long rest)", TEXT2, FS_SMALL))
            from dnd_app.core.calculator import subclasses as _sc_wsp
            if "moon" in _sc_wsp(self.char).get("Druid", "").lower():
                cl.addWidget(_lbl("Combat Wild Shape: use as a bonus action instead of an action.",
                                   GOLD2, FS_TINY, wrap=True))

            fire_btn = QPushButton("\U0001f43e Transform" if uses_left is None
                                    else f"\U0001f43e Transform ({uses_left} left)")
            fire_btn.setEnabled((uses_left is None or uses_left > 0) and combo.count() > 0)
            fire_btn.setStyleSheet(pill_btn("", PURPLE).styleSheet())
            fire_btn.clicked.connect(lambda checked=False, cb=combo: self._wildshape_transform(cb.currentData()))
            cl.addWidget(fire_btn)
        return card

    def _rebuild_wildshape_card(self):
        """_refresh_combat() only updates values on existing widgets, it
        doesn't rebuild the tab structure — but the Wild Shape card needs
        to switch its entire content (picker vs. transformed-state view)
        after transforming or reverting, not just update a number. This
        removes the old card and puts a freshly-built one in its place."""
        container = getattr(self, "_wildshape_card_container", None)
        old_card = getattr(self, "_wildshape_card_widget", None)
        if container is None:
            return
        if old_card is not None:
            container.removeWidget(old_card)
            old_card.hide()
            old_card.setParent(None)
            old_card.deleteLater()
        new_card = self._build_wildshape_control_card()
        self._wildshape_card_widget = new_card
        container.addWidget(new_card, 4)

    def _wildshape_transform(self, beast_name: str):
        if not beast_name: return
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(beast_name)
        if not beast: return
        if not self._spend_wildshape_use():
            self._toast("No Wild Shape uses remaining — available again after a short or long rest.")
            return
        self.char["_wildshape_active"] = beast_name
        self.char["_wildshape_hp"] = beast["hp"]
        if "Wild Shape" not in self.char.get("active_effects", []):
            self.char.setdefault("active_effects", []).append("Wild Shape")
        self._mark_dirty()
        self.ctrl.refresh()
        self._refresh_combat()
        self._rebuild_wildshape_card()
        self._toast(f"\U0001f43e Transformed into {beast_name}")

    def _wildshape_moon_heal(self):
        """Circle of the Moon's Combat Wild Shape: spend a spell slot as
        a bonus action to regain 1d8 HP per level of the slot, while
        transformed. Confirmed a real feature with zero prior mechanical
        presence anywhere in the app."""
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        from dnd_app.core.calculator import subclasses as _sc, class_levels as _clv
        from dnd_app.core.multiclass import compute_all_spell_slots
        active = self.char.get("_wildshape_active")
        beast = WILDSHAPE_BEASTS.get(active)
        if not beast: return
        slots_used = self.char.get("spell_slots_used", [0]*9)
        slot_data = compute_all_spell_slots(_clv(self.char), _sc(self.char))
        slots_max = slot_data.get("spell_slots") or [0]*9
        available_levels = [i+1 for i in range(9) if slots_max[i] - (slots_used[i] if i < len(slots_used) else 0) > 0]
        if not available_levels:
            return
        level, ok = QInputDialog.getItem(
            self, "Combat Wild Shape",
            "Expend which spell slot level? (heals 1d8 per level)",
            [str(l) for l in available_levels], 0, False)
        if not ok:
            return
        level = int(level)
        import random
        roll = sum(random.randint(1, 8) for _ in range(level))
        cur_hp = self.char.get("_wildshape_hp", beast["hp"])
        new_hp = min(beast["hp"], cur_hp + roll)
        self.char["_wildshape_hp"] = new_hp
        used_list = list(slots_used) + [0]*(9-len(slots_used))
        used_list[level-1] += 1
        self.char["spell_slots_used"] = used_list
        self._mark_dirty()
        self.ctrl.refresh()
        self._refresh_combat()
        self._rebuild_wildshape_card()
        self._toast(f"\U0001f52e Expended a level {level} slot: healed {roll} HP ({new_hp}/{beast['hp']})")

    def _wildshape_revert(self):
        # Reverting early doesn't refund the use — matches the real rule
        # that the use is spent the moment you transform, not metered by
        # how long you stay shapeshifted.
        self.char["_wildshape_active"] = None
        self.char.pop("_wildshape_hp", None)
        fx = self.char.get("active_effects", [])
        if "Wild Shape" in fx:
            fx.remove("Wild Shape")
        self._mark_dirty()
        self.ctrl.refresh()
        self._refresh_combat()
        self._rebuild_wildshape_card()
        self._toast("Reverted to normal form")

    def _set_wildshape_hp(self, value: int):
        self.char["_wildshape_hp"] = value
        self._mark_dirty()

    def _build_tab_combat(self):
        """
        Combat tab — redesigned layout:
          TOP STRIP  (~20%): HP | Armor & Shield | Conditions  (always visible)
          BOTTOM     (~80%): Action economy tabs (full height, scrollable)
                              + Class resources / quick spells inside the Other tab
        The old left/right split is gone; everything lives in a single QSplitter
        so the user can drag the divider if they want.
        """
        tab = QWidget()
        root_lay = QVBoxLayout(tab); root_lay.setContentsMargins(10,10,10,10); root_lay.setSpacing(8)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(f"QSplitter::handle{{background:{qa(AMBER,0x33)};height:4px;"
                              f"border-radius:2px;margin:2px 40%;}}"
                              f"QSplitter::handle:hover{{background:{AMBER};}}")

        top_half = QWidget()
        top_half_lay = QVBoxLayout(top_half); top_half_lay.setContentsMargins(0,0,0,0); top_half_lay.setSpacing(8)

        # ── TOP STRIP: HP | Armor | Conditions ───────────────────────────────
        top_strip = QWidget()
        top_strip.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        top_lay = QHBoxLayout(top_strip); top_lay.setContentsMargins(0,0,0,0); top_lay.setSpacing(8)

        # ── HP card ───────────────────────────────────────────────────────────
        hp_card = _card(GREEN+"55"); hp_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hpcl = QVBoxLayout(hp_card); hpcl.setContentsMargins(12,10,12,10)
        hpcl.addWidget(_lbl("HIT POINTS", GOLD, FS_SMALL, bold=True))
        hp_row = QHBoxLayout(); hp_row.setSpacing(8)
        for label, key, color in [("Max","max_hp",IND2),("Current","current_hp",GREEN2),("Temp","temp_hp",TEAL2)]:
            col = QVBoxLayout(); col.setSpacing(2)
            if key == "max_hp":
                label_row = QHBoxLayout(); label_row.setSpacing(2); label_row.setContentsMargins(0,0,0,0)
                label_row.addWidget(_lbl(label, TEXT2, FS_TINY, bold=True, align=Qt.AlignCenter), 1)
                reset_max = QPushButton("↺")
                reset_max.setFixedSize(14, 14)
                reset_max.setToolTip("Reset Max HP to the auto-calculated value "
                                     "(class Hit Dice + CON)")
                reset_max.setStyleSheet(
                    f"QPushButton{{background:transparent;border:none;"
                    f"color:{TEXT3};font-size:11px;padding:0;}}"
                    f"QPushButton:hover{{color:{TEAL2};}}")
                reset_max.clicked.connect(self._reset_max_hp_override)
                label_row.addWidget(reset_max)
                col.addLayout(label_row)
            else:
                col.addWidget(_lbl(label, TEXT2, FS_TINY, bold=True, align=Qt.AlignCenter))
            sp = QSpinBox(); sp.setRange(0,999); sp.setAlignment(Qt.AlignCenter)
            sp.setButtonSymbols(QAbstractSpinBox.NoButtons)
            sp.setStyleSheet(f"QSpinBox{{font-size:{FS_TITLE}px;font-weight:700;color:{color};"
                             f"border:2px solid {qa(color,0x55)};border-radius:8px;"
                             f"background:{SURF2};padding:2px;min-width:64px;}}")
            col.addWidget(sp); hp_row.addLayout(col, 1)
            setattr(self, f"_hp_{key}", sp)
        hpcl.addLayout(hp_row)
        self._hp_bar = QProgressBar(); self._hp_bar.setRange(0,100); self._hp_bar.setValue(100)
        self._hp_bar.setTextVisible(False); self._hp_bar.setFixedHeight(6)
        self._hp_bar.setStyleSheet(
            f"QProgressBar{{background:{SURF2};border:none;border-radius:3px;}}"
            f"QProgressBar::chunk{{border-radius:3px;background:{GREEN2};}}")
        hpcl.addWidget(self._hp_bar)
        # Resistances strip: holds an arbitrary number of badges (multiple
        # resistance/immunity sources, or a "resistance to everything but
        # psychic"-style toggle expanded into 12 individual damage types)
        # without overflowing or squeezing off-screen. Uses plain QWidget
        # + QGridLayout rather than FlowContainer/FlowLayout — same as
        # the tool proficiency chips in _build_tab_skills, since
        # FlowContainer.resizeEvent()'s setMinimumHeight() can trigger
        # another resize event in Qt, looping forever; these strips are
        # an even more direct trigger, since their own refresh functions
        # also call heightForWidth()+setMinimumHeight() explicitly. A
        # grid wraps at a fixed column count instead of dynamically by
        # pixel width, an acceptable trade-off since these badges are
        # short and few. A caption above each strip distinguishes it from
        # adjacent badge groups sharing the same visual style.
        self._resist_caption = _lbl("RESISTANCES", TEXT3, FS_TINY, bold=True, wrap=False)
        self._resist_caption.setVisible(False)
        hpcl.addWidget(self._resist_caption)
        self._resist_frame = QWidget(); self._resist_frame.setStyleSheet("QWidget{background:transparent;}")
        self._resist_lay = QGridLayout(self._resist_frame)
        self._resist_lay.setSpacing(4); self._resist_lay.setContentsMargins(0,0,0,0)
        self._resist_frame.setVisible(False)
        hpcl.addWidget(self._resist_frame, 1)
        # NOTE: climb/swim/fly used to get their own badge strip here too,
        # separate from the resistances strip above. Removed — the top
        # stat-bar speed pill already shows climb/swim/fly (✈/🌊/↑ next to
        # the walk speed) whenever any are non-zero, so this strip was
        # pure duplication of information already on screen, not just a
        # resistance-lookalike problem (which the caption/color fix above
        # already solved on its own).
        # Small, read-only concentration indicator — the full tracker (with
        # Drop/Save buttons) lives in the Spells tab, which isn't very
        # visible during active combat where damage tracking happens. This
        # just gives at-a-glance visibility here too; the automatic
        # concentration-save prompt on taking damage already fires from
        # this tab regardless (see _do_damage), so no duplicate controls
        # are needed.
        self._combat_conc_lbl = _lbl("", AMBER, FS_SMALL, wrap=False)
        self._combat_conc_lbl.setVisible(False)
        hpcl.addWidget(self._combat_conc_lbl)
        # Damage / Heal
        ctrl_row = QHBoxLayout(); ctrl_row.setSpacing(6)
        self._hp_amt = QSpinBox(); self._hp_amt.setRange(1,9999); self._hp_amt.setValue(1)
        self._hp_amt.setMinimumWidth(64); self._hp_amt.setMaximumWidth(80)
        dmg_btn = QPushButton("Damage"); dmg_btn.setFixedHeight(32)
        dmg_btn.setStyleSheet(f"QPushButton{{background:{qa(CRIMSON,0x44)};border:2px solid {CRIMSON};"
                              f"border-radius:6px;color:{CRIM2};font-weight:700;font-size:{FS_SMALL}px;}}"
                              f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
        dmg_btn.setAccessibleName("Apply damage to hit points")
        dmg_btn.clicked.connect(self._do_damage)
        heal_btn = QPushButton("Heal"); heal_btn.setFixedHeight(32)
        heal_btn.setStyleSheet(f"QPushButton{{background:{qa(GREEN,0x44)};border:2px solid {GREEN};"
                               f"border-radius:6px;color:{GREEN2};font-weight:700;font-size:{FS_SMALL}px;}}"
                               f"QPushButton:hover{{background:{GREEN};color:white;}}")
        heal_btn.setAccessibleName("Heal hit points")
        heal_btn.clicked.connect(self._do_heal)
        ctrl_row.addWidget(self._hp_amt); ctrl_row.addWidget(dmg_btn); ctrl_row.addWidget(heal_btn)
        ctrl_row.addStretch()
        hpcl.addLayout(ctrl_row)
        # Death saves
        self._death_saves_container = QWidget(); self._death_saves_container.setStyleSheet("background:transparent;")
        self._death_saves_container.setVisible(False)
        death_row = QHBoxLayout(self._death_saves_container)
        death_row.setContentsMargins(0,2,0,0); death_row.setSpacing(6)
        death_row.addWidget(_lbl("Death Saves:", TEXT2, FS_SMALL, bold=True, wrap=False))
        self._death_success = [QCheckBox() for _ in range(3)]
        self._death_fail    = [QCheckBox() for _ in range(3)]
        death_row.addWidget(_lbl("✓", GREEN2, FS_SMALL, wrap=False))
        for cb in self._death_success:
            cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:7px;"
                             f"border:2px solid {GREEN};background:{BG};}}"
                             f"QCheckBox::indicator:checked{{background:{GREEN2};}}")
            death_row.addWidget(cb)
        death_row.addSpacing(6)
        death_row.addWidget(_lbl("✗", CRIM2, FS_SMALL, wrap=False))
        for cb in self._death_fail:
            cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:7px;"
                             f"border:2px solid {CRIMSON};background:{BG};}}"
                             f"QCheckBox::indicator:checked{{background:{CRIM2};}}")
            death_row.addWidget(cb)
        death_row.addStretch()
        hpcl.addWidget(self._death_saves_container)
        top_lay.addWidget(hp_card, 4)

        # ── Armor & Shield card (READ-ONLY display — equip via Gear tab) ──────
        armor_card = _card(); armor_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        acl2 = QVBoxLayout(armor_card); acl2.setContentsMargins(12,10,12,10)
        acl2.addWidget(_lbl("ARMOR & SHIELD", GOLD, FS_SMALL, bold=True))
        self._armor_card_ac_lbl = _lbl("AC —", TEAL2, FS_BODY, bold=True)
        self._armor_card_ac_lbl.setStyleSheet(
            f"QLabel{{background:{qa(TEAL,0x22)};border:1px solid {TEAL};border-radius:6px;"
            f"padding:4px 10px;color:{TEAL2};font-weight:700;font-size:{FS_BODY}px;}}")
        acl2.addWidget(self._armor_card_ac_lbl)
        self._armor_display = QLabel("No Armor")
        self._armor_display.setStyleSheet(
            f"QLabel{{background:{SURF2};border:1px solid {BORDER2};border-radius:6px;"
            f"padding:6px 10px;color:{TEXT};font-weight:700;}}")
        self._armor_display.setToolTip("Equip armor from the Gear tab")
        self._shield_display = QLabel("No Shield")
        self._shield_display.setStyleSheet(
            f"QLabel{{background:{SURF2};border:1px solid {BORDER};border-radius:6px;"
            f"padding:4px 10px;color:{TEXT3};font-size:{FS_SMALL}px;}}")
        acl2.addWidget(self._armor_display); acl2.addWidget(self._shield_display)
        armor_jump = QPushButton("⚙ Equip armor & shield in Gear ▸")
        armor_jump.setFixedHeight(24)
        armor_jump.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{TEAL2};"
            f"font-size:{FS_TINY}px;text-align:left;}}"
            f"QPushButton:hover{{color:{TEAL};text-decoration:underline;}}")
        armor_jump.clicked.connect(lambda: self._tabs.setCurrentIndex(3))
        acl2.addWidget(armor_jump)
        # Weapons section embedded in armor card. The Gear tab (for
        # equipping weapons/armor) is one click away on the tab bar itself.
        acl2.addWidget(_lbl("WEAPONS", GOLD, FS_SMALL, bold=True))
        wpn_host = QWidget(); wpn_host.setStyleSheet("background:transparent;")
        self._weapon_rows = QVBoxLayout(wpn_host)
        self._weapon_rows.setSpacing(4); self._weapon_rows.setContentsMargins(0,0,0,0)
        wpn_scroll = QScrollArea(); wpn_scroll.setWidgetResizable(True)
        wpn_scroll.setFrameShape(QFrame.NoFrame)
        wpn_scroll.setMinimumHeight(80)
        wpn_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        wpn_scroll.setWidget(wpn_host)
        acl2.addWidget(wpn_scroll, 1)
        top_lay.addWidget(armor_card, 5)

        # ── Conditions card ───────────────────────────────────────────────────
        cond_card = _card(); cond_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ccl = QVBoxLayout(cond_card); ccl.setContentsMargins(12,10,12,10)
        ccl.addWidget(_lbl("CONDITIONS", GOLD, FS_SMALL, bold=True))
        exh_row = QWidget(); exhl = QHBoxLayout(exh_row)
        exhl.setContentsMargins(0,0,0,0); exhl.setSpacing(6)
        exhl.addWidget(_lbl("Exhaustion:", TEXT2, FS_SMALL, wrap=False))
        self._exhaustion_spin = QSpinBox(); self._exhaustion_spin.setRange(0,6)
        self._exhaustion_spin.setFixedWidth(52)
        self._exhaustion_spin.setStyleSheet(
            f"QSpinBox{{background:{SURF2};border:1px solid {BORDER2};"
            f"border-radius:4px;color:{TEXT};font-size:{FS_SMALL}px;padding:2px;}}")
        self._exhaustion_spin.setToolTip(
            "PHB exhaustion (cumulative):\n"
            "1 — Disadvantage on ability checks\n"
            "2 — Speed halved\n"
            "3 — Disadvantage on attack rolls and saving throws\n"
            "4 — Hit point maximum halved\n"
            "5 — Speed reduced to 0\n"
            "6 — Death")
        self._exhaustion_spin.setAccessibleName(
            "Exhaustion level, 0 to 6. Level 6 is death.")
        self._exhaustion_spin.valueChanged.connect(self._on_exhaustion_changed)
        exhl.addWidget(self._exhaustion_spin)
        exhl.addStretch()
        ccl.addWidget(exh_row)
        self._cond_checks = {}
        COND_NAMES = ["Blinded","Charmed","Deafened","Frightened",
                      "Grappled","Incapacitated","Invisible","Paralyzed",
                      "Petrified","Poisoned","Prone","Restrained","Stunned","Unconscious"]
        cond_grid = QGridLayout(); cond_grid.setSpacing(3)
        for ci, cname in enumerate(COND_NAMES):
            cb = QCheckBox(cname); cb.setStyleSheet(
                f"QCheckBox{{color:{TEXT2};font-size:{FS_SMALL}px;}}"
                f"QCheckBox::indicator{{width:12px;height:12px;border:1px solid {BORDER2};"
                f"border-radius:3px;background:{SURF2};}}"
                f"QCheckBox::indicator:checked{{background:{CRIM2};border-color:{CRIM2};}}")
            cb.stateChanged.connect(lambda s,n=cname: self._on_condition_changed(n, bool(s)))
            cdata = CONDITIONS.get(cname, {})
            tip_lines = list(cdata.get("effects", []))
            if cdata.get("levels"):
                tip_lines = tip_lines + [""] + cdata["levels"]
            if cdata.get("source"):
                tip_lines.append(f"({cdata['source']})")
            if tip_lines:
                cb.setToolTip("\n".join(tip_lines))
            self._cond_checks[cname] = cb
            cond_grid.addWidget(cb, ci//3, ci%3)
        ccl.addLayout(cond_grid)

        # "Active Conditions" section — uses the space that used to just
        # be addStretch()'d away. Shows each currently-active condition
        # (plus exhaustion, if its level is above 0) as a readable badge
        # with the full effect text (including exhaustion's disadvantage
        # note, which was always present in the data but too cramped in
        # the old inline label to actually read) available on hover.
        ccl.addWidget(_sep())
        ccl.addWidget(_lbl("ACTIVE CONDITIONS", GOLD, FS_TINY, bold=True))
        self._active_cond_frame = QWidget(); self._active_cond_frame.setStyleSheet("background:transparent;")
        self._active_cond_lay = QGridLayout(self._active_cond_frame)
        self._active_cond_lay.setSpacing(4); self._active_cond_lay.setContentsMargins(0,4,0,0)
        ccl.addWidget(self._active_cond_frame)
        self._active_cond_none_lbl = _lbl("None", TEXT3, FS_SMALL)
        ccl.addWidget(self._active_cond_none_lbl)
        top_lay.addWidget(cond_card, 3)

        from dnd_app.core.calculator import get_wild_shape_info
        if get_wild_shape_info(self.char) is not None:
            self._wildshape_card_container = top_lay
            self._wildshape_card_widget = self._build_wildshape_control_card()
            top_lay.addWidget(self._wildshape_card_widget, 4)

        top_half_lay.addWidget(top_strip)
        # No addStretch() here: dragging the splitter handle below should
        # grow top_strip (and its cards, set to Expanding) rather than
        # have the extra space absorbed as invisible blank space. With
        # top_strip's size policy set to Preferred rather than a hard
        # Maximum, and nothing else competing for space in this layout,
        # it claims whatever height the layout gives it.

        # Per-bucket category filters are built inside the tab-
        # construction loop below so each tab gets its own independent
        # filter row, rather than one shared row across all 4.

        # ── BOTTOM: Action Economy tabs (full remaining height) ───────────────
        self._action_tabs = QTabWidget()
        self._action_tabs.setDocumentMode(True)
        self._action_tabs.setTabPosition(QTabWidget.North)
        self._action_tabs.setStyleSheet(
            f"QTabWidget::pane{{border:1px solid {qa(AMBER,0x33)};border-radius:8px;"
            f"background:{SURF};margin-top:-1px;}}"
            f"QTabBar::tab{{background:{BG};color:{TEXT2};border:1px solid {qa(AMBER,0x22)};"
            f"border-bottom:none;padding:6px 14px;border-radius:6px 6px 0 0;"
            f"font-size:{FS_SMALL}px;font-weight:700;min-width:80px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD};border-color:{qa(AMBER,0x66)};}}"
            f"QTabBar::tab:hover{{background:{qa(AMBER,0x11)};color:{AMBE2};}}"
        )
        self._action_bucket_widgets = {}
        self._action_cat_filters = {}
        self._action_cat_btns_by_bucket = {}
        self._action_filter_rows = {}
        self._action_spell_level_filters = {}
        self._action_lvl_btns_by_bucket = {}
        self._action_level_filter_rows = {}
        _TAB_DISPLAY_LABEL = {"Action":"Action","Bonus Action":"Bonus Action",
                               "Reaction":"Reaction","Passive":"Other"}
        CAT_ICONS = {"All": "◆", "Common": "⚔", "Magic Item": "✨", "Race": "🧬", "Spell": "📖"}
        for bucket_name, icon in [("Action","⚔"),("Bonus Action","✦"),
                                   ("Reaction","⚡"),("Passive","◎")]:
            bw = QWidget(); bw.setStyleSheet("background:transparent;")
            bl = QVBoxLayout(bw); bl.setContentsMargins(8,8,8,8); bl.setSpacing(5)

            # Per-bucket category filter row: independent state so each
            # tab (including Passive) filters independently rather than
            # sharing one row.
            self._action_cat_filters[bucket_name] = "All"
            self._action_cat_btns_by_bucket[bucket_name] = {}
            filter_row_w = QWidget()
            filter_row = QHBoxLayout(filter_row_w)
            filter_row.setContentsMargins(0,0,0,0); filter_row.setSpacing(6)
            def _make_cat_click(cat, _bucket=bucket_name):
                def _click():
                    self._action_cat_filters[_bucket] = cat
                    for c, b in self._action_cat_btns_by_bucket[_bucket].items():
                        b.setStyleSheet(self._action_cat_btn_style(c == cat))
                    self._action_level_filter_rows[_bucket].setVisible(cat == "Spell")
                    self._refresh_action_tabs()
                return _click
            for cat in ["All", "Common", "Magic Item", "Race", "Spell"]:
                btn = QPushButton(f"{CAT_ICONS[cat]} {cat}")
                btn.setMinimumHeight(24)
                btn.setStyleSheet(self._action_cat_btn_style(cat == "All"))
                btn.clicked.connect(_make_cat_click(cat))
                if cat == "Magic Item":
                    btn.setToolTip("Placeholder — magic items aren't mechanically wired into "
                                    "Known Actions yet.")
                self._action_cat_btns_by_bucket[bucket_name][cat] = btn
                filter_row.addWidget(btn)
            filter_row.addStretch()
            self._action_filter_rows[bucket_name] = filter_row_w
            bl.addWidget(filter_row_w)

            # Secondary spell-level filter — hidden until "Spell" is
            # selected in THIS bucket's own filter row.
            self._action_spell_level_filters[bucket_name] = "All"
            self._action_lvl_btns_by_bucket[bucket_name] = {}
            lvl_row_w = QWidget()
            lvl_row = QHBoxLayout(lvl_row_w)
            lvl_row.setContentsMargins(0,0,0,0); lvl_row.setSpacing(4)
            def _make_lvl_click(lvl, _bucket=bucket_name):
                def _click():
                    self._action_spell_level_filters[_bucket] = lvl
                    for l, b in self._action_lvl_btns_by_bucket[_bucket].items():
                        b.setStyleSheet(self._action_cat_btn_style(l == lvl, small=True))
                    self._refresh_action_tabs()
                return _click
            for lvl_label in ["All", "Cantrip"] + [f"L{n}" for n in range(1, 10)]:
                btn = QPushButton(lvl_label)
                btn.setMinimumHeight(20); btn.setMaximumWidth(48)
                btn.setStyleSheet(self._action_cat_btn_style(lvl_label == "All", small=True))
                btn.clicked.connect(_make_lvl_click(lvl_label))
                self._action_lvl_btns_by_bucket[bucket_name][lvl_label] = btn
                lvl_row.addWidget(btn)
            lvl_row.addStretch()
            lvl_row_w.setVisible(False)
            self._action_level_filter_rows[bucket_name] = lvl_row_w
            bl.addWidget(lvl_row_w)

            bl.addStretch()
            self._action_bucket_widgets[bucket_name] = (bw, bl)
            scroll = QScrollArea(); scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(bw)
            scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
            label = _TAB_DISPLAY_LABEL.get(bucket_name, bucket_name)
            self._action_tabs.addTab(scroll, f"{icon} {label}")

        # ── 5th tab: Active spell effects (Shield of Faith, Haste, …) ────────
        fx_tab = QWidget(); fx_tab.setStyleSheet("background:transparent;")
        fxl = QVBoxLayout(fx_tab); fxl.setContentsMargins(10,10,10,10); fxl.setSpacing(8)
        add_row = QHBoxLayout(); add_row.setSpacing(8)
        self._fx_combo = QComboBox(); self._fx_combo.setEditable(True)
        self._fx_combo.setAccessibleName("Choose or type a spell effect to apply")
        from dnd_app.core.effects import EFFECT_TABLE
        self._fx_combo.addItems(sorted(EFFECT_TABLE.keys()))
        self._fx_combo.setMinimumHeight(30)
        fx_add = QPushButton("＋ Apply Effect"); fx_add.setMinimumHeight(30)
        fx_add.setAccessibleName("Apply the selected spell effect")
        fx_add.setStyleSheet(
            f"QPushButton{{background:{qa(TEAL,0x33)};border:2px solid {TEAL};border-radius:6px;"
            f"color:{TEAL2};font-weight:700;padding:2px 14px;}}"
            f"QPushButton:hover{{background:{TEAL};color:white;}}")
        fx_add.clicked.connect(self._add_active_effect)
        add_row.addWidget(self._fx_combo, 1); add_row.addWidget(fx_add)
        fxl.addLayout(add_row)
        fx_scroll = QScrollArea(); fx_scroll.setWidgetResizable(True)
        fx_scroll.setFrameShape(QFrame.NoFrame)
        fx_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        fx_host = QWidget(); fx_host.setStyleSheet("background:transparent;")
        self._fx_lay = QVBoxLayout(fx_host); self._fx_lay.setSpacing(6)
        self._fx_lay.addStretch()
        fx_scroll.setWidget(fx_host)
        fxl.addWidget(fx_scroll, 1)
        self._action_tabs.addTab(fx_tab, "☄ Effects")

        # ── Turn tracker bar (Action / Bonus / Reaction economy per turn) ────
        # Deliberately NOT part of the resizable splitter below — it's a
        # single fixed-height row of buttons with no variable-length
        # content, so giving it a share of the splitter just took space
        # away from the Attacks/action-tabs area (which holds actual
        # variable-length content players need to read clearly) for zero
        # benefit, since there's nothing useful gained by resizing this bar
        # bigger or smaller.
        self._turn_counts = {"Action":0, "Bonus Action":0, "Reaction":0}
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        turn_bar = QFrame()
        turn_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        turn_bar.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(AMBER,0x33)};"
                               f"border-radius:8px;}}")
        tb = QHBoxLayout(turn_bar); tb.setContentsMargins(10,6,10,6); tb.setSpacing(8)
        tb.addWidget(_lbl("TURN:", GOLD, FS_SMALL, bold=True, wrap=False))
        self._turn_chips = {}
        for bname, icon in [("Action","⚔"),("Bonus Action","✦"),("Reaction","⚡")]:
            chip = QPushButton(f"{icon} {bname}  ●")
            chip.setCheckable(False); chip.setMinimumHeight(28)
            chip.setAccessibleName(f"{bname} availability — click to toggle used")
            chip.setToolTip(f"Click to manually toggle your {bname} as used/available")
            chip.clicked.connect(lambda checked=False, b=bname: self._toggle_turn_slot(b))
            tb.addWidget(chip)
            self._turn_chips[bname] = chip
        self._haste_chip = _lbl("⚡ HASTE: +1 action", "#FFD34D", FS_SMALL, bold=True, wrap=False)
        self._haste_chip.setStyleSheet(
            f"background:#22FFD34D;border:1px solid #FFD34D;border-radius:6px;"
            f"padding:4px 8px;color:#FFD34D;font-weight:700;")
        self._haste_chip.setVisible(False)
        tb.addWidget(self._haste_chip)
        self._sneak_chip = QPushButton("🗡 Sneak Attack ●")
        self._sneak_chip.setMinimumHeight(28)
        self._sneak_chip.setToolTip("Rogue: once per turn. Click to toggle used.")
        self._sneak_chip.setAccessibleName("Sneak Attack availability — click to toggle")
        self._sneak_chip.clicked.connect(self._toggle_sneak)
        self._sneak_chip.setVisible(False)
        tb.addWidget(self._sneak_chip)
        tb.addStretch()
        new_turn = QPushButton("🔄 New Turn")
        new_turn.setMinimumHeight(30)
        new_turn.setAccessibleName("Start a new turn — resets action, bonus action, reaction and sneak attack")
        new_turn.setStyleSheet(
            f"QPushButton{{background:{qa(GREEN,0x33)};border:2px solid {GREEN};border-radius:6px;"
            f"color:{GREEN2};font-weight:800;padding:2px 16px;}}"
            f"QPushButton:hover{{background:{GREEN};color:white;}}")
        new_turn.clicked.connect(self._new_turn)
        tb.addWidget(new_turn)
        root_lay.addWidget(turn_bar)

        splitter.addWidget(top_half)
        splitter.addWidget(self._action_tabs)
        self._combat_top_half = top_half
        # The Attacks/action-tabs area holds the variable-length content
        # (attacks, spells, abilities) a player needs to read during
        # play, so it gets the majority share of the default split, with
        # a minimum height so dragging the handle can't squeeze it down
        # to near-nothing. top_half (HP, conditions, resistance/movement
        # badges, etc.) can still be dragged larger if it has many
        # badges wrapping across rows.
        self._action_tabs.setMinimumHeight(320)
        splitter.setSizes([280, 460])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Other tab also hosts class resources, hit dice, and quick spells
        # They are injected via _build_resource_rows() during _refresh_action_tabs()
        root_lay.addWidget(splitter, 1)
        return tab


    def _do_damage(self):
        amt = self._hp_amt.value()
        cur = self._hp_current_hp.value()
        wild = self.char.get("_wildshape_active")
        max_hp = self.char.get("max_hp", 1)
        if wild:
            from dnd_app.data.statblocks import WILDSHAPE_BEASTS
            beast = WILDSHAPE_BEASTS.get(wild, {})
            max_hp = beast.get("hp", 1)
        # Instant death: damage ≥ 2× max HP (PHB p.197) — while Wild Shaped,
        # this checks against the BEAST's max HP (the creature actually
        # taking the hit), and simply reverts you to your normal form at
        # full awareness rather than killing you outright, per the Wild
        # Shape reversion rule; it only threatens actual death once
        # applied to your own HP after reverting.
        if amt >= max_hp * 2 and not wild:
            self.char["current_hp"] = 0
            self._hp_current_hp.setValue(0)
            self.ctrl.update("current_hp", 0, rebuild_char=False)
            self._show_death_screen()
            return
        # Temporary HP absorbs damage first (PHB p.198) — beast forms
        # don't have their own temp HP pool, only your own does, so this
        # only applies when not Wild Shaped.
        temp = self._hp_temp_hp.value()
        absorbed = 0
        if temp > 0 and not wild:
            absorbed = min(temp, amt)
            new_temp = temp - absorbed
            self._hp_temp_hp.setValue(new_temp)
            self.char["temp_hp"] = new_temp
            amt -= absorbed

        if wild:
            # Wild Shape (PHB p.66): if this damage would reduce the beast
            # to 0 HP or below, you revert to your normal form immediately,
            # and any EXCESS damage (beyond what the beast's remaining HP
            # could absorb) carries over to your own HP. You aren't
            # knocked unconscious unless that excess itself drops your own
            # HP to 0.
            if amt >= cur:
                excess = amt - cur
                self._wildshape_revert()
                own_max = self.char.get("max_hp", 1)
                own_cur = self.char.get("current_hp", own_max)
                own_new = max(0, own_cur - excess)
                self._hp_current_hp.setValue(own_new)
                self.ctrl.update("current_hp", own_new, rebuild_char=False)
                self._toast(f"🐾 Beast form dropped to 0 HP — reverted to normal form, "
                            f"{excess} excess damage carried over")
                if excess >= own_max * 2:
                    self._show_death_screen()
                    return
            else:
                new_hp = cur - amt
                self._hp_current_hp.setValue(new_hp)
                self.char["_wildshape_hp"] = new_hp
                self._mark_dirty()
            self._toast(f"Beast form took {amt} damage" if amt else "No damage")
            return

        # Rage Beyond Death (Zealot Barbarian, 14th level): while raging,
        # damage that would drop you to 0 instead leaves you at 1 — unless
        # the overkill portion of the damage (what's left after your
        # current HP is exhausted) itself exceeds your max HP, in which
        # case you're killed outright even through this protection.
        # Doesn't apply if Rage isn't currently active (toggled off = the
        # protection ends with it).
        from dnd_app.core.character import class_levels
        barb_lvl = class_levels(self.char).get("Barbarian", 0)
        is_zealot_14 = (barb_lvl >= 14
                         and any("zealot" in sub.lower()
                                 for cl in self.char.get("classes", [])
                                 for sub in [cl.get("subclass", "")]))
        is_raging = "Rage" in self.char.get("active_effects", [])
        overkill = amt - cur
        would_drop_to_0 = cur - amt <= 0

        if is_zealot_14 and is_raging and would_drop_to_0 and overkill < max_hp:
            new_hp = 1
            self._toast("🛡 Rage Beyond Death: damage would drop you to 0, but your rage "
                        "keeps you standing at 1 HP")
        elif (barb_lvl >= 11 and is_raging and would_drop_to_0 and overkill < max_hp):
            # Relentless Rage: a CON save (not a guarantee like Rage Beyond
            # Death) to drop to 1 HP instead of 0. DC starts at 10 and
            # rises by 5 each use since the last short/long rest.
            import random
            uses = self.char.get("_relentless_rage_uses", 0)
            dc = 10 + 5 * uses
            con_mod = ability_mod(self.char, "CON")
            roll = random.randint(1, 20)
            total = roll + con_mod
            self.char["_relentless_rage_uses"] = uses + 1
            self._mark_dirty()
            if total >= dc:
                new_hp = 1
                self._toast(f"🎲 Relentless Rage: DC {dc} CON save — rolled {roll}{sign(con_mod)}"
                            f" = {total}, SUCCESS — you drop to 1 HP instead of 0")
            else:
                new_hp = 0
                self._toast(f"🎲 Relentless Rage: DC {dc} CON save — rolled {roll}{sign(con_mod)}"
                            f" = {total}, FAILED — you drop to 0 HP")
        else:
            new_hp = max(0, cur - amt)
        self._hp_current_hp.setValue(new_hp)
        self.ctrl.update("current_hp", new_hp, rebuild_char=False)
        if absorbed and amt == 0:
            self._toast(f"🛡 Temp HP absorbed all {absorbed} damage")
        elif absorbed:
            self._toast(f"🛡 Temp HP absorbed {absorbed}, took {amt} damage")

        conc_spell = self.char.get("concentration", {}).get("spell")
        if conc_spell:
            roll, ok = QInputDialog.getInt(
                self, "Concentration Save",
                f"Concentrating on {conc_spell}. Enter your d20 roll (modifier applied automatically):",
                10, 1, 30,
            )
            if ok:
                from dnd_app.core.calculator import get_saving_throw_bonus
                import random
                if roll <= 0:
                    roll = random.randint(1, 20)
                dc = max(10, amt // 2)
                total = roll + get_saving_throw_bonus(self.char, "CON")
                if total >= dc:
                    QMessageBox.information(
                        self, "Concentration",
                        f"Maintained on {conc_spell}.\n{roll} + modifier = {total} vs DC {dc}",
                    )
                else:
                    drop_concentration(self.char)
                    self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
                    QMessageBox.warning(
                        self, "Concentration Broken",
                        f"Failed ({total} vs DC {dc}). Dropped {conc_spell}.",
                    )
                    self._refresh_concentration()
                    self._toast("Your focus shatters like cheap glass.")
        self._mark_dirty()

    def _roll_initiative(self):
        """Roll d20 + initiative bonus — shown as a non-blocking toast."""
        self._quick_roll_toast("Initiative", get_initiative(self.char))

    def _do_heal(self):
        amt = self._hp_amt.value()
        cur = self._hp_current_hp.value()
        wild = self.char.get("_wildshape_active")
        if wild:
            from dnd_app.data.statblocks import WILDSHAPE_BEASTS
            beast_max = WILDSHAPE_BEASTS.get(wild, {}).get("hp", cur)
            new_hp = min(beast_max, cur + amt)
            self._hp_current_hp.setValue(new_hp)
            self.char["_wildshape_hp"] = new_hp
            self._mark_dirty()
            return
        mx = self._hp_max_hp.value()
        new_hp = min(mx, cur + amt)
        # Healing from 0 HP: regain consciousness, death saves reset (PHB p.197)
        if cur == 0 and new_hp > 0:
            self.char["death_saves"] = {"successes": 0, "failures": 0}
            for cb in self._death_success + self._death_fail:
                cb.setChecked(False)
            self._toast(f"💚 Back on your feet! Death saves reset")
        self._hp_current_hp.setValue(new_hp)
        self.ctrl.update("current_hp", new_hp, rebuild_char=False)

    # ═══ Turn tracker ══════════════════════════════════════════════════════
    def _turn_limit(self, bucket: str) -> int:
        from dnd_app.core.effects import has_extra_action
        if bucket == "Action" and has_extra_action(self.char):
            return 2
        return 1

    def _mark_turn_used(self, bucket: str):
        """Consume one use of an action-economy slot; grey the bucket when spent."""
        if bucket not in self._turn_counts:
            return
        limit = self._turn_limit(bucket)
        if self._turn_counts[bucket] >= limit:
            return
        self._turn_counts[bucket] += 1
        if bucket == "Action" and limit == 2 and self._turn_counts[bucket] == 1:
            self._toast("⚡ Haste: first action used — one more available")
        self._apply_turn_state()

    def _toggle_turn_slot(self, bucket: str):
        limit = self._turn_limit(bucket)
        self._turn_counts[bucket] = 0 if self._turn_counts[bucket] >= limit else limit
        self._apply_turn_state()

    def _toggle_sneak(self):
        self._sneak_used = not getattr(self, "_sneak_used", False)
        self._apply_turn_state()

    def _new_turn(self):
        for k in self._turn_counts: self._turn_counts[k] = 0
        self._sneak_used = False
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        self.char["_action_surge_used_this_turn"] = False
        # Reckless Attack lasts only the turn it was activated on
        fx = self.char.get("active_effects", [])
        if "Reckless Attack" in fx:
            fx.remove("Reckless Attack")
            self._refresh_combat_weapons()
        self._apply_turn_state()
        self._toast("🔄 New turn — action, bonus & reaction ready")

    def _apply_turn_state(self):
        """Grey out Use/Cast buttons in spent buckets; refresh chips."""
        if not hasattr(self, "_turn_chips"):
            return
        from dnd_app.core.character import class_levels
        ICONS = {"Action":"⚔","Bonus Action":"✦","Reaction":"⚡"}
        for bname, chip in self._turn_chips.items():
            limit = self._turn_limit(bname)
            used  = self._turn_counts.get(bname, 0)
            free  = used < limit
            marker = "●" * max(0, limit-used) + "○" * used
            chip.setText(f"{ICONS[bname]} {bname}  {marker}")
            col = GREEN2 if free else TEXT2
            chip.setStyleSheet(
                f"QPushButton{{background:{qa(col,0x1e)};border:2px solid {col};"
                f"border-radius:6px;color:{col};font-weight:700;padding:2px 10px;}}"
                f"QPushButton:hover{{border-color:{TEAL2};}}"
                f"QPushButton:focus{{border:2px solid {TEAL2};}}")
            # Grey the bucket's buttons + dim cards
            for btn in getattr(self, "_bucket_use_btns", {}).get(bname, []):
                try:
                    btn.setEnabled(free)
                    if not free and btn.text() not in ("✓",):
                        btn.setProperty("_orig_text", btn.text()); btn.setText("✓")
                    elif free and btn.property("_orig_text"):
                        btn.setText(btn.property("_orig_text"))
                except RuntimeError:
                    pass
        # Haste chip
        from dnd_app.core.effects import has_extra_action
        self._haste_chip.setVisible(has_extra_action(self.char))
        # Sneak chip (rogues only): hidden while Wild Shaped, since Sneak
        # Attack requires a finesse or ranged weapon and natural weapons
        # never qualify. Also hidden if nothing currently equipped qualifies.
        rogue_lvl = class_levels(self.char).get("Rogue", 0)
        has_qualifying_weapon = False
        if rogue_lvl > 0:
            from dnd_app.data.items import WEAPON_DICT
            from dnd_app.core.magic_items import parse_magic_suffix
            for wpn_name in self.char.get("equipped_weapons", []):
                base_name, _ = parse_magic_suffix(wpn_name)
                wpn = WEAPON_DICT.get(base_name)
                if not wpn:
                    continue
                props = wpn.get("properties", [])
                is_finesse = any("finesse" in str(p).lower() for p in props)
                if base_name == "Double-Bladed Scimitar" and "Revenant Blade" in self.char.get("feats", []):
                    is_finesse = True
                is_ranged = "ranged" in str(wpn.get("category", "")).lower()
                if is_finesse or is_ranged:
                    has_qualifying_weapon = True
                    break
        if rogue_lvl > 0 and not self.char.get("_wildshape_active") and has_qualifying_weapon:
            dice = (rogue_lvl + 1) // 2
            used = getattr(self, "_sneak_used", False)
            self._sneak_chip.setVisible(True)
            self._sneak_chip.setText(f"🗡 Sneak {dice}d6  {'○ used' if used else '● ready'}")
            col = TEXT3 if used else PURP2
            self._sneak_chip.setStyleSheet(
                f"QPushButton{{background:{qa(col,0x1e)};border:2px solid {col};"
                f"border-radius:6px;color:{col};font-weight:700;padding:2px 10px;}}"
                f"QPushButton:focus{{border:2px solid {TEAL2};}}")
        else:
            self._sneak_chip.setVisible(False)

    # ═══ Active spell effects ═══════════════════════════════════════════════
    def _add_active_effect(self):
        from dnd_app.core.effects import EFFECT_TABLE
        typed = self._fx_combo.currentText().strip()
        if not typed: return
        # Editable QComboBox.currentText() returns whatever was typed, with
        # no guarantee it matches a real entry — a mistyped or misremembered
        # name must not silently create a bogus "active effect" that
        # doesn't correspond to anything real. Resolve it properly instead:
        # exact match first, then a forgiving case-insensitive match, and
        # only fall through to a warning toast (no effect added) if neither
        # finds anything real. The valid set isn't just EFFECT_TABLE — a few
        # toggles (Rage, Form of Dread, Starry Form, Hybrid Transformation)
        # are driven by resource-pool checkboxes elsewhere and have no
        # EFFECT_TABLE entry of their own, but typing "Rage" here should
        # still work rather than being rejected.
        RESOURCE_POOL_TOGGLES = {"Hybrid Transformation", "Rage", "Form of Dread", "Starry Form", "Reckless Attack", "Frenzy", "Sacred Weapon", "Invincible Conqueror", "Exalted Champion", "Peerless Athlete", "Hexblade's Curse", "Bladesong", "Radiant Soul (Aasimar)", "Necrotic Shroud", "Gem Flight", "Shifting", "Vow of Enmity", "Living Legend", "Mortal Bulwark", "Elder Champion", "Elemental Gift", "Writhing Tide", "Otherworldly Wings", "Trance of Order", "Umbral Form", "Ghost Walk", "Steps of Night", "Arms of the Astral Self", "Awakened Astral Self", "Giant's Might", "Aspect of the Wyrm", "Spirit Totem", "Radiant Consumption", "Maelstrom Aura"}
        valid_names = set(EFFECT_TABLE.keys()) | RESOURCE_POOL_TOGGLES
        name = None
        if typed in valid_names:
            name = typed
        else:
            for key in valid_names:
                if key.lower() == typed.lower():
                    name = key
                    break
        if name is None:
            self._toast(f"⚠ \"{typed}\" isn't a recognized effect — pick one from the list")
            return
        self.char.setdefault("active_effects", []).append(name)
        self.ctrl.refresh()          # AC pill etc. recompute
        self._refresh_effects_list()
        self._apply_turn_state()     # haste chip
        self._mark_dirty()
        self._toast(f"☄ {name} applied")

    def _remove_active_effect(self, name: str):
        fx = self.char.get("active_effects", [])
        if name in fx:
            fx.remove(name)
            # Berserker's Frenzy: if Rage ends while frenzied, gain 1
            # level of exhaustion and Frenzy itself ends (it can't outlast
            # the rage it was part of).
            frenzy_ended = False
            if name == "Rage" and "Frenzy" in fx:
                fx.remove("Frenzy")
                self.char["exhaustion"] = min(6, self.char.get("exhaustion", 0) + 1)
                frenzy_ended = True
            self.ctrl.refresh()
            self._refresh_effects_list()
            self._apply_turn_state()
            self._mark_dirty()
            if frenzy_ended:
                self._toast("😵 Rage removed — Frenzy ends with it, gain 1 level of exhaustion")
            else:
                self._toast(f"✖ {name} removed")

    def _refresh_effects_list(self):
        if not hasattr(self, "_fx_lay"): return
        from dnd_app.core.effects import EFFECT_TABLE
        while self._fx_lay.count() > 1:
            it = self._fx_lay.takeAt(0)
            w = it.widget()
            if w:
                w.hide(); w.setParent(None); w.deleteLater()
        fx = self.char.get("active_effects", [])
        if not fx:
            self._fx_lay.insertWidget(0, _lbl(
                "No active effects. Pick a spell above (Haste, Shield of Faith, "
                "Enlarge…) — AC, speed and the turn tracker update automatically.",
                TEXT3, FS_SMALL, wrap=True))
            return
        for i, name in enumerate(fx):
            info = EFFECT_TABLE.get(name, {})
            row = QFrame()
            col = TEAL2 if info else AMBE2
            row.setStyleSheet(f"QFrame{{background:{qa(col,0x11)};border:1px solid {qa(col,0x44)};"
                              f"border-radius:8px;}}")
            rl = QHBoxLayout(row); rl.setContentsMargins(10,7,8,7); rl.setSpacing(8)
            head = name + ("  ©" if info.get("conc") else "")
            tcol = QVBoxLayout(); tcol.setSpacing(1)
            tcol.addWidget(_lbl(head, GOLD, FS_BODY, bold=True, wrap=False))
            note = info.get("note", "Custom effect — tracked, no automatic numbers.")
            tcol.addWidget(_lbl(note, TEXT2, FS_TINY, wrap=True))
            rm = QPushButton("✕ End"); rm.setMinimumHeight(28); rm.setMinimumWidth(58)
            rm.setAccessibleName(f"End the {name} effect")
            rm.setStyleSheet(
                f"QPushButton{{background:{qa(CRIMSON,0x22)};border:2px solid {CRIMSON};"
                f"border-radius:6px;color:{CRIM2};font-weight:700;}}"
                f"QPushButton:hover{{background:{CRIMSON};color:white;}}"
                f"QPushButton:focus{{border:2px solid {TEAL2};}}")
            rm.clicked.connect(lambda checked=False, n=name: self._remove_active_effect(n))
            rl.addLayout(tcol, 1); rl.addWidget(rm, 0, Qt.AlignTop)
            self._fx_lay.insertWidget(i, row)

    _EXHAUSTION_EFFECTS = {
        0: "",
        1: "Disadvantage on ability checks.",
        2: "Disadvantage on ability checks. Speed halved.",
        3: "Disadvantage on ability checks, attack rolls, and saving throws. Speed halved.",
        4: "Disadvantage on ability checks, attack rolls, and saving throws. "
           "Speed halved. Hit point maximum halved.",
        5: "Disadvantage on ability checks, attack rolls, and saving throws. "
           "Speed 0. Hit point maximum halved.",
        6: "💀 Death.",
    }

    def _on_exhaustion_changed(self, v: int):
        self.char["exhaustion"] = v
        self._refresh_exhaustion_label()
        self._refresh_active_conditions()
        self.ctrl.refresh()   # recompute max HP / speed / apply death check
        self._mark_dirty()
        if v >= 6:
            self._toast("💀 Exhaustion level 6 — the character has died")
            self._show_death_screen()
        elif v >= 4:
            self._toast(f"⚠ Exhaustion {v}: hit point maximum halved")

    def _refresh_exhaustion_label(self):
        if not hasattr(self, "_exh_effect_lbl"):
            return
        lvl = self.char.get("exhaustion", 0)
        self._exh_effect_lbl.setText(self._EXHAUSTION_EFFECTS.get(lvl, ""))

    def _refresh_active_conditions(self):
        """Populate the readable "Active Conditions" badge section — one
        badge per checked condition checkbox, plus exhaustion (if its
        level is above 0), each with the condition's full effect text
        (from the same data wired into the checkboxes' own tooltips)
        shown on hover."""
        if not hasattr(self, "_active_cond_lay"):
            return
        while self._active_cond_lay.count():
            item = self._active_cond_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)

        def _badge(text, tooltip):
            b = _lbl(text, CRIM2, FS_SMALL, bold=True, wrap=False)
            b.setStyleSheet(
                f"background:{qa(CRIMSON,0x33)};border:1.5px solid {qa(CRIMSON,0x99)};"
                f"border-radius:5px;padding:3px 8px;color:{CRIM2};"
                f"font-size:{FS_SMALL}px;font-weight:700;")
            b.setToolTip(tooltip)
            return b

        active = []
        for cname, cb in self._cond_checks.items():
            if cb.isChecked():
                active.append((cname, cb.toolTip()))
        lvl = self.char.get("exhaustion", 0)
        if lvl > 0:
            active.append((f"Exhaustion ({lvl})", self._EXHAUSTION_EFFECTS.get(lvl, "")))

        self._active_cond_none_lbl.setVisible(not active)
        self._active_cond_frame.setVisible(bool(active))
        for i, (name, tip) in enumerate(sorted(active)):
            self._active_cond_lay.addWidget(_badge(name, tip), i // 2, i % 2)

    def _reset_max_hp_override(self):
        """Clear the manual Max HP override and let it auto-calculate again."""
        self.char.pop("hp_max_override", None)
        from dnd_app.core.calculator import update_all
        update_all(self.char)
        if hasattr(self, "_hp_max_hp"):
            self._hp_max_hp.blockSignals(True)
            self._hp_max_hp.setValue(self.char.get("max_hp", 0))
            self._hp_max_hp.blockSignals(False)
        if hasattr(self, "_hp_current_hp"):
            self._hp_current_hp.blockSignals(True)
            self._hp_current_hp.setValue(self.char.get("current_hp", 0))
            self._hp_current_hp.blockSignals(False)
        self._update_hp_bar()
        self._mark_dirty()
        self._toast("↺ Max HP reset to auto-calculated value")

    def _on_max_hp_changed(self, v: int):
        """Manual Max HP edits set hp_max_override, which update_all() respects
        and will not silently overwrite on the next refresh (see calculator.py)."""
        char = self.char
        old_max = char.get("max_hp", v)
        char["hp_max_override"] = v
        char["max_hp"] = v
        # Keep current HP sane relative to the new max (mirror the auto-calc rule)
        diff = v - old_max
        if diff > 0:
            char["current_hp"] = min(char.get("current_hp", v) + diff, v)
        else:
            char["current_hp"] = min(char.get("current_hp", v), v)
        if hasattr(self, "_hp_current_hp"):
            self._hp_current_hp.blockSignals(True)
            self._hp_current_hp.setValue(char["current_hp"])
            self._hp_current_hp.blockSignals(False)
        self._update_hp_bar()
        self._mark_dirty()

    def _update_hp_bar(self):
        """Live green→amber→red HP bar; safe to call from any HP change."""
        if not hasattr(self, "_hp_bar"): return
        mx  = self._hp_max_hp.value()
        cur = self._hp_current_hp.value()
        pct = max(0, min(100, round(cur * 100 / mx))) if mx > 0 else 0
        self._hp_bar.setValue(pct)
        bar_col = GREEN2 if pct > 50 else (AMBER if pct > 25 else CRIM2)
        self._hp_bar.setStyleSheet(
            f"QProgressBar{{background:{SURF2};border:none;border-radius:4px;}}"
            f"QProgressBar::chunk{{border-radius:4px;background:{bar_col};}}")

    # ── Toast notifications (non-blocking) ────────────────────────────────────
    def _toast(self, text: str, duration_ms: int = 3200):
        """Show a transient notification banner at the bottom of the sheet.
        Pass duration_ms=0 for a persistent toast that stays up until the
        caller explicitly hides self._toast_lbl (used for the death
        screen's quip, which should last until the character is revived
        rather than fade out from under a modal overlay)."""
        if not hasattr(self, "_toast_lbl"):
            self._toast_lbl = QLabel(self)
            self._toast_lbl.setAlignment(Qt.AlignCenter)
            self._toast_lbl.setWordWrap(False)
            self._toast_lbl.hide()
            self._toast_timer = QTimer(self)
            self._toast_timer.setSingleShot(True)
            self._toast_timer.timeout.connect(self._toast_lbl.hide)
        self._toast_lbl.setText(f"  {text}  ")
        self._toast_lbl.setStyleSheet(
            f"QLabel{{background:{SURF2};color:{GOLD};border:1px solid {qa(AMBER,0x88)};"
            f"border-radius:10px;padding:10px 18px;font-size:{FS_BODY}px;font-weight:700;}}")
        self._toast_lbl.adjustSize()
        x = (self.width() - self._toast_lbl.width()) // 2
        y = self.height() - self._toast_lbl.height() - 28
        self._toast_lbl.move(max(8, x), max(8, y))
        self._toast_lbl.raise_()
        self._toast_lbl.show()
        self._toast_timer.stop()
        if duration_ms > 0:
            self._toast_timer.start(duration_ms)

    # ── Hit dice: spend one to heal (short-rest style) ────────────────────────
    def _spend_hit_die(self, die_key: str):
        import random
        hd = self.char.get("hit_dice", {}).get(die_key)
        if not hd or hd.get("remaining", 0) <= 0:
            return
        sides = int(die_key[1:])
        roll = random.randint(1, sides)
        con = ability_mod(self.char, "CON")
        # Durable: the die roll itself (before CON is added) has a floor of 2x CON modifier (min 2).
        if "Durable" in self.char.get("feats", []):
            roll = max(roll, 2 * con, 2)
        heal = max(0, roll + con)
        # Dwarven Fortitude: guarantees at least 1 HP healed (the standard
        # hit-die-spend formula allows 0). This app doesn't track "when"
        # a hit die is spent, so the Dodge-triggered part of this feat
        # works through this same button; only this floor differs from the norm.
        if "Dwarven Fortitude" in self.char.get("feats", []):
            heal = max(1, roll + con)
        # Vigor of the Hill Giant: extra HP = CON modifier + proficiency
        # bonus when spending a Hit Die during a short rest ("Iron Stomach").
        if "Vigor of the Hill Giant" in self.char.get("feats", []):
            from dnd_app.core.calculator import get_prof_bonus
            heal += con + get_prof_bonus(self.char)
        hd["remaining"] -= 1
        cur, mx = self.char.get("current_hp", 0), self.char.get("max_hp", 0)
        self.char["current_hp"] = min(mx, cur + heal)
        if hasattr(self, "_hp_current_hp"):
            self._hp_current_hp.setValue(self.char["current_hp"])
        self._toast(f"🎲 Spent {die_key}: rolled {roll} {con:+d} CON → healed {heal} HP "
                    f"({hd['remaining']} dice left)")
        self._mark_dirty()
        self._refresh_action_tabs()
        if hasattr(self, "_hd_layout"):
            self._refresh_hit_dice()

    # ── Quick d20 roll with toast (skills / saves / abilities / initiative) ───
    def _quick_roll_toast(self, label: str, bonus: int):
        import random
        d = random.randint(1, 20)
        total = d + bonus
        flair = ""
        if d == 20: flair = "  🌟 NAT 20!"
        elif d == 1: flair = "  💀 Nat 1…"
        self._toast(f"🎲 {label}: [{d}] {bonus:+d} = {total}{flair}", 4200)

    def _add_weapon_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("Add Weapon"); dlg.setMinimumWidth(400)
        dlg.setStyleSheet(self.styleSheet())
        l = QVBoxLayout(dlg)
        l.addWidget(_lbl("Choose a weapon to equip:", TEXT, FS_BODY))
        combo = QComboBox()
        for (name,cat,dmg,dmg_type,cost,wt,props) in ALL_WEAPONS:
            combo.addItem(f"{name} — {dmg} {dmg_type}", name)
        l.addWidget(combo)
        # Material modifier costs: Adamantine +500gp, Silvered +100gp.
        l.addWidget(_lbl("Material (optional):", TEXT, FS_BODY))
        material_combo = QComboBox()
        material_combo.addItem("None (+0 gp)", "")
        material_combo.addItem("Adamantine (+500 gp)", "Adamantine")
        material_combo.addItem("Silvered (+100 gp)", "Silvered")
        l.addWidget(material_combo)
        cost_lbl = _lbl("", TEXT2, FS_SMALL)
        l.addWidget(cost_lbl)
        def _update_cost(*_):
            base_cost = next((c for (n,cat,dmg,dmg_type,wt,c,props) in ALL_WEAPONS if n == combo.currentData()), 0)
            extra = {"": 0, "Adamantine": 500, "Silvered": 100}[material_combo.currentData()]
            cost_lbl.setText(f"Cost: {base_cost + extra} gp" if (base_cost or extra) else "")
        combo.currentIndexChanged.connect(_update_cost)
        material_combo.currentIndexChanged.connect(_update_cost)
        _update_cost()
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        l.addWidget(btns)
        if dlg.exec():
            base_name = combo.currentData()
            material = material_combo.currentData()
            wpn_name = f"{material} {base_name}" if material else base_name
            equipped = self.char.setdefault("equipped_weapons", [])
            if wpn_name in equipped:
                QMessageBox.information(self, "Weapon", f"{wpn_name} is already equipped.")
                return
            equipped.append(wpn_name)
            self._add_weapon_row(wpn_name)
            self._mark_dirty()

    def _add_onhit_damage_badges(self, rl):
        """Append a separate badge for each passive on-hit damage bonus
        (Divine Strike, Genie's Wrath, Dreadful Strikes) to a weapon row's
        layout. Deliberately separate from the base weapon damage label —
        these are often a different damage type, which matters for
        resistance/immunity, so combining them into one number would hide
        that. Shared by every weapon-row-building method in this class."""
        for bonus in get_onhit_damage_bonuses(self.char):
            badge = _lbl(f"+{bonus['die']} {bonus['damage_type']}", TEAL2, FS_SMALL, wrap=False)
            badge.setToolTip(f"{bonus['name']} (once per turn on a hit)")
            rl.addWidget(badge)

    def _add_weapon_row(self, wpn_name, is_offhand=False):
        from dnd_app.core.magic_items import parse_magic_suffix, parse_material_prefix
        base_wpn_name, magic_bonus = parse_magic_suffix(wpn_name)
        # "Silvered X"/"Adamantine X" aren't recognized by the weapon
        # lookup on their own (only the "+1"/"+2"/"+3" suffix is), so the
        # material prefix is stripped here (after the magic suffix, so
        # "Silvered Longsword +1" parses correctly) to find the real base weapon.
        base_wpn_name, weapon_material = parse_material_prefix(base_wpn_name)
        # Check for an active infusion targeting this weapon (Enhanced
        # Weapon, Radiant Weapon, Repeating Shot, Returning Weapon) and
        # apply its real "+N" attack/damage bonus, using the higher of
        # the two if both are present.
        from dnd_app.core.calculator import get_infusion_bonus, class_levels
        art_lvl_wr = class_levels(self.char).get("Artificer", 0)
        for inf in self.char.get("active_infusions", []):
            if inf.get("target_item") == wpn_name:
                inf_bonus = get_infusion_bonus(inf.get("infusion", ""), art_lvl_wr)
                magic_bonus = max(magic_bonus, inf_bonus)
        wpn = next((w for w in ALL_WEAPONS if w[0]==base_wpn_name), None)
        is_named_magic_fallback = wpn is None
        if not wpn:
            # Named magic weapon (e.g. "Sun Blade", "Armblade") — render a generic
            # magic-blade profile instead of silently dropping it. These items'
            # own flavor text typically grants proficiency regardless of class
            # (e.g. Armblade: "counts as a simple weapon you are proficient
            # with"), so we treat named-fallback weapons as always-proficient.
            nb = self.char.get("_named_weapon_bonuses", {}).get(wpn_name, 0)
            wpn = (wpn_name, "Melee (magic)", "1d8", "radiant" if "sun" in wpn_name.lower() else "slashing",
                   0, 0, ["Finesse"] if nb else [])
        name,cat,dmg,dmg_type,_,_,props = wpn
        props = list(props or [])
        # Thrown Arms Master: simple/martial melee weapons without the
        # Thrown property gain it; weapons that already have it get an
        # extended range instead.
        if "Thrown Arms Master" in self.char.get("feats", []) and "Melee" in cat:
            has_thrown_already = any("Thrown" in str(p) for p in props)
            is_two_handed_tam = "Two-Handed" in props
            if not has_thrown_already:
                props.append(f"Thrown ({'15/30' if is_two_handed_tam else '20/60'} ft, Thrown Arms Master)")
            else:
                for i, p in enumerate(props):
                    if "Thrown" in str(p):
                        import re as _re_tam
                        m = _re_tam.search(r'\((\d+)/(\d+)', str(p))
                        if m:
                            near, far = int(m.group(1)), int(m.group(2))
                            props[i] = _re_tam.sub(r'\(\d+/\d+', f'({near+20}/{far+40}', str(p))
        from dnd_app.core.calculator import has_weapon_proficiency
        pb_full = get_prof_bonus(self.char)
        proficient = is_named_magic_fallback or has_weapon_proficiency(self.char, base_wpn_name, cat)
        pb = pb_full if proficient else 0
        is_finesse = "Finesse" in (props or [])
        # Revenant Blade: grants Finesse to the Double-Bladed Scimitar specifically (it doesn't have Finesse by default).
        if base_wpn_name == "Double-Bladed Scimitar" and "Revenant Blade" in self.char.get("feats", []):
            is_finesse = True
        is_ranged  = "Ranged" in cat
        is_thrown  = any("Thrown" in str(p) for p in (props or []))
        is_two_handed_hw = "Two-Handed" in (props or [])
        # Hex Warrior (Warlock, The Hexblade, 1st level): use CHA instead
        # of STR/DEX for a non-two-handed weapon's attack/damage rolls.
        warlock_lvl_hw = class_levels(self.char).get("Warlock", 0)
        is_hexblade = "hexblade" in subclasses(self.char).get("Warlock", "").lower()
        # Battle Ready (Artificer, Battle Smith, 3rd level): use INT
        # instead of STR/DEX for attack/damage rolls with a magic
        # weapon. Checks every path this app tracks magic weapons
        # through: a "+N" suffix, a named-fallback item (not in the
        # mundane weapon list at all), presence in magic_items, or an
        # infusion-marked equipment entry.
        art_lvl_br = class_levels(self.char).get("Artificer", 0)
        is_battlesmith = "battle smith" in subclasses(self.char).get("Artificer", "").lower()
        is_magic_weapon = bool(magic_bonus) or is_named_magic_fallback
        if not is_magic_weapon:
            mi_names = {(i.get("name") if isinstance(i, dict) else i) for i in self.char.get("magic_items", [])}
            if wpn_name in mi_names or base_wpn_name in mi_names:
                is_magic_weapon = True
            for eq in self.char.get("equipment", []):
                if eq.get("name") in (wpn_name, base_wpn_name) and eq.get("magic"):
                    is_magic_weapon = True
                    break
        if warlock_lvl_hw >= 1 and is_hexblade and not is_two_handed_hw:
            stat = "CHA"
        elif art_lvl_br >= 3 and is_battlesmith and is_magic_weapon:
            stat = "INT"
        else:
            stat = "DEX" if (is_finesse and ability_mod(self.char,"DEX")>ability_mod(self.char,"STR")) or is_ranged else "STR"
        mod = ability_mod(self.char, stat)

        # Check if this weapon is a named magic item with an effect-based bonus
        # (e.g. "Sun Blade" gives +2 independent of the "+N" suffix system)
        named_bonuses = self.char.get("_named_weapon_bonuses", {})
        named_bonus = named_bonuses.get(wpn_name, 0) or named_bonuses.get(base_wpn_name, 0)
        total_bonus = magic_bonus + named_bonus

        # Archery fighting style: +2 to ranged weapon attack rolls.
        fighting_styles = self.char.get("fighting_styles", [])
        has_archery = is_ranged and any("archery" in fs.lower() for fs in fighting_styles)
        atk_style_bonus = 2 if has_archery else 0

        # Sacred Weapon (Paladin, Oath of Devotion): Channel Divinity —
        # while active, add CHA mod to attack rolls with the touched
        # weapon. Previously had no mechanical effect at all.
        sacred_weapon_bonus = 0
        if "Sacred Weapon" in self.char.get("active_effects", []):
            sacred_weapon_bonus = ability_mod(self.char, "CHA")

        # Great Weapon Master / Sharpshooter: -5 to attack, +10 to
        # damage, toggleable per weapon (the real rule is decided per
        # attack, not a character-wide stance). GWM requires a heavy
        # melee weapon; Sharpshooter requires a ranged weapon; both
        # require proficiency.
        is_heavy = "Heavy" in (props or [])
        char_feats = self.char.get("feats", [])
        can_power_attack = proficient and (
            ("Great Weapon Master" in char_feats and not is_ranged and is_heavy) or
            ("Sharpshooter" in char_feats and is_ranged))
        power_attack_active = can_power_attack and wpn_name in self.char.get("power_attack_weapons", [])
        power_attack_atk = -5 if power_attack_active else 0
        power_attack_dmg = 10 if power_attack_active else 0

        atk = sign(pb + mod + total_bonus + atk_style_bonus + sacred_weapon_bonus + power_attack_atk)
        prof_note = "" if proficient else "  (not proficient — no prof. bonus)"
        # Display the weapon under its full enchanted name (e.g. "Longsword +1")
        name = wpn_name

        # ── Ammo type for this weapon ─────────────────────────────────────────
        _AMMO_KEY = {
            "Shortbow":        "arrows",  "Longbow":         "arrows",
            "Light Crossbow":  "bolts",   "Hand Crossbow":   "bolts",
            "Heavy Crossbow":  "bolts",   "Sling":           "bullets",
            "Blowgun":         "needles", "Pistol":          "bullets_modern",
            "Musket":          "bullets_modern", "Revolver": "bullets_modern",
            "Hunting Rifle":   "bullets_modern", "Automatic Rifle": "bullets_modern",
            "Laser Pistol":    "energy_cells",   "Laser Rifle":     "energy_cells",
            "Antimatter Rifle":"energy_cells",
        }
        _AMMO_LABEL = {
            "arrows":         "Arrows",       "bolts":          "Bolts",
            "bullets":        "Sling Bullets","needles":        "Needles",
            "bullets_modern": "Bullets",      "energy_cells":   "Energy Cells",
        }
        _AMMO_EQUIP_NAMES = {
            "arrows":         ["Arrows","Arrow","Arrows (20)","Ammunition, Arrows (20)"],
            "bolts":          ["Bolts","Bolt","Bolts (20)","Crossbow Bolts (20)","Ammunition, Bolts (20)"],
            "bullets":        ["Sling Bullets","Sling Bullets (20)","Bullets"],
            "needles":        ["Needles","Blowgun Needles (50)"],
            "bullets_modern": ["Bullets (Modern)","Bullets"],
            "energy_cells":   ["Energy Cell","Energy Cells"],
        }
        ammo_key = _AMMO_KEY.get(base_wpn_name, "") if is_ranged and not is_thrown else ""

        # Seed ammo tracker from equipment list if currently at 0
        if ammo_key and self.char.get("ammo", {}).get(ammo_key, 0) == 0:
            for eq in self.char.get("equipment", []):
                if not isinstance(eq, dict): continue
                eq_name = eq.get("name","")
                if any(eq_name.lower() == n.lower() for n in _AMMO_EQUIP_NAMES.get(ammo_key,[])):
                    self.char.setdefault("ammo", {})[ammo_key] = eq.get("qty", 0)
                    break

        row_f = QFrame()
        row_f.setStyleSheet(f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(name, TEXT, FS_BODY, bold=True, wrap=False))
        from dnd_app.core.calculator import get_condition_attack_status
        cond_status = get_condition_attack_status(self.char)
        atk_text = f"{atk} to hit"
        if cond_status["advantage"]:
            atk_text += "  (ADV)"
        elif cond_status["disadvantage"]:
            atk_text += "  (DISADV)"
        atk_lbl = _lbl(atk_text, TEAL2 if proficient else AMBER, FS_BODY, wrap=False)
        if not proficient:
            atk_lbl.setToolTip(
                f"Not proficient with {name} — proficiency bonus (+{pb_full}) "
                f"is not added to this attack roll.")
        elif cond_status["sources"]:
            reason = cond_status["note"] or f"Source: {', '.join(cond_status['sources'])}"
            atk_lbl.setToolTip(reason)
        else:
            atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _prof=proficient, _bonus=total_bonus, _atk=atk:
            self._show_breakdown_popup(f"{name} — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, _prof, _bonus), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        if "Reckless Attack" in self.char.get("active_effects", []) and not is_ranged and stat == "STR":
            reckless_badge = _lbl("⚔ Reckless (adv)", GOLD2, FS_TINY, bold=True, wrap=False)
            reckless_badge.setToolTip("Reckless Attack is active: advantage on this attack, "
                                       "but attack rolls against you also have advantage until your next turn.")
            rl.addWidget(reckless_badge)
        # Dueling fighting style: +2 damage when wielding a one-handed
        # melee weapon (not Two-Handed) and no other weapon equipped.
        is_two_handed = "Two-Handed" in (props or [])
        only_weapon = len(self.char.get("equipped_weapons", [])) == 1
        has_dueling = (not is_ranged and not is_two_handed and only_weapon and
                       any("dueling" in fs.lower() for fs in fighting_styles))
        dueling_bonus = 2 if has_dueling else 0

        # Rage: melee weapon attacks using Strength get a damage bonus
        # while raging. Previously get_rage_damage() was computed and
        # displayed as a reference stat but never actually added to any
        # weapon's damage roll — this wires it into the real calculation.
        rage_active = "Rage" in self.char.get("active_effects", [])
        rage_bonus = 0
        if rage_active and not is_ranged and stat == "STR":
            from dnd_app.core.calculator import get_rage_damage
            rage_str = get_rage_damage(self.char)
            if rage_str != "—":
                rage_bonus = int(rage_str.replace("+", ""))

        # Off-hand (second+ equipped weapon) damage: a positive ability
        # modifier is only added if Two-Weapon Fighting is selected — the
        # real rule is that you DON'T add it for the bonus-action off-hand
        # attack unless you have this style, though a negative modifier
        # still applies regardless (it's a penalty, not a bonus you can
        # opt out of).
        has_twf = any("two-weapon fighting" in fs.lower() for fs in fighting_styles)
        offhand_mod = mod if (not is_offhand or mod < 0 or has_twf) else 0
        dmg_total_mod = offhand_mod + total_bonus + dueling_bonus + rage_bonus + power_attack_dmg
        dmg_display = f"{dmg}+{dmg_total_mod}" if dmg_total_mod >= 0 else f"{dmg}{dmg_total_mod}"
        rl.addWidget(_lbl(f"{dmg_display} {dmg_type}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        # Weapon-type-specific item bonuses (e.g. Bracers of Archery's +2
        # damage on bow attacks), shown only on weapon rows matching the
        # item's restriction rather than as a general character-wide badge.
        for wb in self.char.get("_weapon_damage_bonuses", []):
            wtype = wb.get("weapon_type", "").lower()
            if wtype and wtype in name.lower():
                wb_badge = _lbl(f"+{wb['value']} ({wb['source']})", TEAL2, FS_SMALL, wrap=False)
                wb_badge.setToolTip(f"{wb['source']}: +{wb['value']} damage with {wtype} weapons")
                rl.addWidget(wb_badge)
        if total_bonus:
            tip_src = wpn_name if named_bonus else f"+{total_bonus} enchantment"
            magic_badge = _lbl(f"✦ +{total_bonus}", AMBE2, FS_TINY, bold=True, wrap=False)
            magic_badge.setToolTip(f"Magical weapon: +{total_bonus} to attack and damage rolls\nSource: {tip_src}")
            rl.addWidget(magic_badge)
        if weapon_material:
            material_badge = _lbl(f"\u26cf {weapon_material}", TEAL2, FS_TINY, bold=True, wrap=False)
            if weapon_material == "Silvered":
                material_badge.setToolTip(
                    "Silvered weapon: this weapon's damage counts as silvered for the purpose "
                    "of overcoming a creature's resistance or immunity to nonmagical attacks "
                    "(e.g. many lycanthropes and certain other creatures).")
            else:
                material_badge.setToolTip(
                    "Adamantine weapon: whenever this weapon hits an object, the hit is a "
                    "critical hit.")
            rl.addWidget(material_badge)
        if can_power_attack:
            pa_cb = QCheckBox("Power Attack (-5/+10)")
            pa_cb.setChecked(power_attack_active)
            pa_cb.setStyleSheet(f"QCheckBox{{color:{CRIM2 if power_attack_active else TEXT3};font-size:{FS_TINY}px;font-weight:700;}}")
            pa_cb.setToolTip(
                f"{'Great Weapon Master' if not is_ranged else 'Sharpshooter'}: "
                "trade -5 to hit for +10 damage on this weapon's attacks.")
            def _on_power_attack_toggle(state, _wname=wpn_name):
                pa_list = self.char.setdefault("power_attack_weapons", [])
                if state and _wname not in pa_list:
                    pa_list.append(_wname)
                elif not state and _wname in pa_list:
                    pa_list.remove(_wname)
                self._mark_dirty()
                self._refresh_combat()
            pa_cb.stateChanged.connect(_on_power_attack_toggle)
            rl.addWidget(pa_cb)
        prop_str = ", ".join(str(p) for p in (props[:2] if props else []))
        if prop_str: rl.addWidget(_lbl(prop_str, TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        # ── Ammo counter (ranged non-thrown weapons) ──────────────────────────
        ammo_lbl = None
        if ammo_key:
            ammo_count = self.char.setdefault("ammo", {}).get(ammo_key, 0)
            ammo_lbl = QPushButton(f"\U0001f3f9 {_AMMO_LABEL.get(ammo_key,'Ammo')}: {ammo_count}")
            ammo_lbl.setStyleSheet(
                f"QPushButton{{background:{qa(AMBE2,0x22)};border:1px solid {qa(AMBER,0x55)};"
                f"border-radius:5px;color:{AMBE2};font-size:{FS_TINY}px;"
                f"font-weight:700;padding:2px 6px;}}"
                f"QPushButton:hover{{background:{qa(AMBER,0x33)};}}")
            ammo_lbl.setFixedHeight(26)
            def _add_ammo(checked=False, _key=ammo_key, _lbl=ammo_lbl,
                          _label=_AMMO_LABEL.get(ammo_key,"Ammo"),
                          _equip_names=_AMMO_EQUIP_NAMES.get(ammo_key,[])):
                n, ok = QInputDialog.getInt(
                    None, f"Restock {_label}",
                    f"Add how many {_label}?", 20, 0, 9999)
                if ok:
                    self.char.setdefault("ammo",{})[_key] = (
                        self.char["ammo"].get(_key, 0) + n)
                    # Sync to equipment list
                    total = self.char["ammo"][_key]
                    for _eq in self.char.get("equipment",[]):
                        if not isinstance(_eq,dict): continue
                        if any(_eq.get("name","").lower()==en.lower() for en in _equip_names):
                            _eq["qty"] = total; break
                    else:
                        # Add to equipment if not present
                        from dnd_app.data.items import ADVENTURING_GEAR as _AG
                        _ammo_cost = next((float(g[2] or 0) for g in _AG if g[0] == _label), 0.0)
                        self.char.setdefault("equipment",[]).append(
                            {"name":_label,"qty":total,"weight":0.02,"cost":_ammo_cost,"notes":""})
                    _lbl.setText(f"\U0001f3f9 {_label}: {total}")
                    self._mark_dirty()
            ammo_lbl.clicked.connect(_add_ammo)
            rl.addWidget(ammo_lbl)

        # ── Attack roll button ────────────────────────────────────────────────
        def _roll_hit(checked=False, _atk=atk, _name=name,
                      _ak=ammo_key, _al=ammo_lbl,
                      _ammo_lbl_ref=_AMMO_LABEL,
                      _equip_names=_AMMO_EQUIP_NAMES.get(ammo_key,[])):
            import random
            if _ak:
                cur = self.char.setdefault("ammo", {}).get(_ak, 0)
                if cur <= 0:
                    QMessageBox.warning(
                        None, "No Ammo",
                        "No " + _ammo_lbl_ref.get(_ak,"ammo") + " remaining!\n"
                        "Click the ammo counter to restock.")
                    return
                self.char["ammo"][_ak] = cur - 1
                new_qty = self.char["ammo"][_ak]
                # Sync to equipment
                for _eq in self.char.get("equipment",[]):
                    if not isinstance(_eq,dict): continue
                    if any(_eq.get("name","").lower()==en.lower() for en in _equip_names):
                        _eq["qty"] = max(0, new_qty); break
                if _al:
                    _al.setText(
                        f"\U0001f3f9 {_ammo_lbl_ref.get(_ak,'Ammo')}: {new_qty}")
                self._mark_dirty()
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name}\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(TEAL,0x33)};border:1px solid {TEAL};"
            f"border-radius:5px;color:{TEAL2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{TEAL};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        # Attach the completed row to the combat tab (this line was lost in a
        # past refactor — without it every weapon row was built then dropped).
        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_martial_arts_row(self):
        """Monks always have an unarmed-strike attack available via Martial
        Arts, scaling in damage die by level and usable with STR or DEX
        (whichever is better) — but it never showed up as an actual attack,
        only as a passive 'die size' stat. Render it exactly like a real
        weapon row so it can be rolled the same way equipped weapons are."""
        from dnd_app.core.calculator import get_martial_arts_die, get_prof_bonus
        die = get_martial_arts_die(self.char)
        if die == "—":
            return
        pb = get_prof_bonus(self.char)   # monks are always proficient unarmed
        str_mod = ability_mod(self.char, "STR")
        dex_mod = ability_mod(self.char, "DEX")
        stat = "DEX" if dex_mod > str_mod else "STR"
        mod = max(str_mod, dex_mod)
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(TEAL,0x14)};border:1px solid {qa(TEAL,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Unarmed Strike", TEXT, FS_BODY, bold=True, wrap=False))
        ma_badge = _lbl("Martial Arts", TEAL2, FS_TINY, bold=True, wrap=False)
        ma_badge.setToolTip(f"Monk unarmed strikes use {stat} and scale with level "
                            f"— always proficient, never needs to be equipped.")
        rl.addWidget(ma_badge)
        ma_atk_lbl = _lbl(f"{atk} to hit", TEAL2, FS_BODY, wrap=False)
        ma_atk_lbl.setToolTip("Right-click for a breakdown")
        ma_atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _atk=atk:
            self._show_breakdown_popup("Unarmed Strike — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, True, 0), _atk, e.globalPos()))
        rl.addWidget(ma_atk_lbl)
        dmg_display = f"{die}+{mod}" if mod >= 0 else f"{die}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} bludgeoning", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl(f"({stat})", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Unarmed Strike\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(TEAL,0x33)};border:1px solid {TEAL};"
            f"border-radius:5px;color:{TEAL2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{TEAL};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _build_tab_gear(self):
        tab = QWidget(); root = QVBoxLayout(tab)
        root.setContentsMargins(16,16,16,16); root.setSpacing(8)

        # ── Currency tracker ─────────────────────────────────────────────────
        money_card = _card(GOLD+"55")
        mcl = QHBoxLayout(money_card); mcl.setContentsMargins(14,10,14,10); mcl.setSpacing(16)
        mcl.addWidget(_lbl("💰 CURRENCY", GOLD2, FS_SMALL, bold=True, wrap=False))
        self._currency_spins = {}
        for coin, color in [("PP","#b0a0e0"),("GP","#f5c518"),("EP","#a0c8a0"),
                             ("SP","#d0d0d0"),("CP","#c87941")]:
            col = QVBoxLayout(); col.setSpacing(2)
            col.addWidget(_lbl(coin, color, FS_TINY, bold=True, align=Qt.AlignCenter))
            sp = QSpinBox(); sp.setRange(0,999999); sp.setMinimumWidth(72)
            sp.setValue(self.char.get("currency",{}).get(coin.lower(),0))
            sp.setAlignment(Qt.AlignCenter)
            sp.setStyleSheet(f"QSpinBox{{font-size:{FS_BODY}px;font-weight:700;color:{color};"
                             f"border:2px solid {qa(color,0x66)};border-radius:6px;background:{SURF2};}}")
            sp.setButtonSymbols(QAbstractSpinBox.NoButtons)
            sp.valueChanged.connect(lambda v,k=coin.lower(): self._on_currency_change(k,v))
            col.addWidget(sp); mcl.addLayout(col)
            self._currency_spins[coin.lower()] = sp
        mcl.addStretch()
        root.addWidget(money_card)

        # ── Two-panel browser: left = owned, right = browser tabs ────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)

        # ── LEFT: owned equipment + magic items ───────────────────────────────
        left_w = QWidget(); left_l = QVBoxLayout(left_w)
        # Weight / carrying capacity
        self._weight_lbl = _lbl("", TEXT3, FS_SMALL, wrap=False)
        self._update_weight()
        left_l.addWidget(self._weight_lbl)
        left_l.setContentsMargins(0,0,4,0); left_l.setSpacing(8)

        # Vertical splitter between Carried Equipment and Magic Items —
        # replaces a fixed 1:1 stretch split, which resized awkwardly
        # (both panes always exactly half the space regardless of how
        # many items were actually in each). The user can now drag to
        # resize either pane, with a default favoring the equipment list
        # since it's typically the larger of the two.
        left_split = QSplitter(Qt.Vertical)
        left_split.setChildrenCollapsible(False)
        left_split.setHandleWidth(6)

        # ── Carried Equipment: QTreeWidget list, matching the browser's style ──
        equip_w = QWidget(); egl = QVBoxLayout(equip_w)
        egl.setContentsMargins(0,0,0,0); egl.setSpacing(6)
        egl.addWidget(_lbl("⚔  CARRIED EQUIPMENT", TEAL2, FS_SMALL, bold=True, wrap=False))
        self._gear_equip_tree = QTreeWidget()
        self._gear_equip_tree.setHeaderLabels(["Item", "Eq", "Qty", "Wt", "Value", ""])
        self._gear_equip_tree.setAlternatingRowColors(True)
        self._gear_equip_tree.setRootIsDecorated(False)
        self._gear_equip_tree.setStyleSheet(
            f"QTreeWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;"
            f"alternate-background-color:{SURF};}}"
            f"QTreeWidget::item{{padding:3px 2px;font-size:{FS_SMALL}px;color:{TEXT};}}"
            f"QTreeWidget::item:selected{{background:{TEAL};color:#0a0d12;}}")
        self._gear_equip_tree.header().setStyleSheet(
            f"QHeaderView::section{{background:{SURF2};color:{GOLD2};font-weight:700;"
            f"font-size:{FS_TINY}px;padding:4px;border:1px solid {BORDER};}}")
        hdr = self._gear_equip_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in [(1,32),(2,52),(3,48),(4,55),(5,28)]:
            hdr.setSectionResizeMode(col, QHeaderView.Fixed)
            self._gear_equip_tree.setColumnWidth(col, w)
        egl.addWidget(self._gear_equip_tree, 1)
        add_eq = pill_btn("+ Custom Item", TEAL)
        add_eq.clicked.connect(self._add_equipment_dialog)
        egl.addWidget(add_eq)
        left_split.addWidget(equip_w)

        # ── Magic Items / Attunement: same QTreeWidget list style ──────────────
        art_lvl_for_max = class_levels(self.char).get("Artificer", 0)
        att_max_display = 6 if art_lvl_for_max >= 18 else 5 if art_lvl_for_max >= 14 else 4 if art_lvl_for_max >= 10 else 3
        if "Mystic Conflux" in self.char.get("feats", []):
            att_max_display = max(att_max_display, 4)
        mi_w = QWidget(); mgl = QVBoxLayout(mi_w)
        mgl.setContentsMargins(0,0,0,0); mgl.setSpacing(6)
        self._mi_title_lbl = _lbl(f"✨  MAGIC ITEMS  (max {att_max_display} attuned)",
                                   PURP2, FS_SMALL, bold=True, wrap=False)
        mgl.addWidget(self._mi_title_lbl)
        self._magic_items_tree = QTreeWidget()
        self._magic_items_tree.setHeaderLabels(["Item", "Rarity", "Attuned", "Eq'd", ""])
        self._magic_items_tree.setAlternatingRowColors(True)
        self._magic_items_tree.setRootIsDecorated(False)
        self._magic_items_tree.setStyleSheet(
            f"QTreeWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;"
            f"alternate-background-color:{SURF};}}"
            f"QTreeWidget::item{{padding:3px 2px;font-size:{FS_SMALL}px;color:{TEXT};}}"
            f"QTreeWidget::item:selected{{background:{PURP2};color:#0a0d12;}}")
        self._magic_items_tree.header().setStyleSheet(
            f"QHeaderView::section{{background:{SURF2};color:{GOLD2};font-weight:700;"
            f"font-size:{FS_TINY}px;padding:4px;border:1px solid {BORDER};}}")
        mhdr = self._magic_items_tree.header()
        mhdr.setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in [(1,80),(2,64),(3,52),(4,28)]:
            mhdr.setSectionResizeMode(col, QHeaderView.Fixed)
            self._magic_items_tree.setColumnWidth(col, w)
        mgl.addWidget(self._magic_items_tree, 1)
        self._magic_item_rows = []
        left_split.addWidget(mi_w)
        left_split.setSizes([340, 220])
        left_l.addWidget(left_split, 1)
        splitter.addWidget(left_w)

        # ── RIGHT: browser tabs (Mundane | Magic) ─────────────────────────────
        right_tabs = QTabWidget()
        right_tabs.setStyleSheet(
            f"QTabWidget::pane{{background:{SURF};border:1px solid {BORDER};border-radius:8px;}}"
            f"QTabBar::tab{{background:{SURF2};color:{TEXT2};padding:8px 16px;"
            f"font-size:{FS_SMALL}px;border:1px solid {BORDER};border-bottom:none;"
            f"border-radius:6px 6px 0 0;margin-right:2px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD2};font-weight:700;}}")

        # ── MUNDANE BROWSER ───────────────────────────────────────────────────
        mundane_tab = QWidget(); mdt = QVBoxLayout(mundane_tab)
        mdt.setContentsMargins(8,8,8,8); mdt.setSpacing(6)

        # Search + category filter
        mdt_top = QHBoxLayout()
        self._md_search = QLineEdit(); self._md_search.setPlaceholderText("Search equipment…")
        self._md_search.setStyleSheet(f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};"
                                       f"border-radius:6px;padding:4px 8px;color:{TEXT};}}")
        self._md_cat = QComboBox()
        for cat in ["All","Weapons — Simple","Weapons — Martial","Materials (Silvered/Adamantine)","Armor",
                     "Adventuring Gear","Tools","Mounts & Vehicles"]:
            self._md_cat.addItem(cat)
        mdt_top.addWidget(self._md_search,2); mdt_top.addWidget(self._md_cat)
        mdt.addLayout(mdt_top)

        self._md_list = QTreeWidget()
        self._md_list.setHeaderLabels(["Name","Category","Damage / AC","Weight","Cost"])
        self._md_list.setAlternatingRowColors(True)
        self._md_list.setRootIsDecorated(True)
        self._md_list.setStyleSheet(
            f"QTreeWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;"
            f"alternate-background-color:{SURF};}}"
            f"QTreeWidget::item{{padding:4px 2px;font-size:{FS_BODY}px;color:{TEXT};}}"
            f"QTreeWidget::item:selected{{background:{TEAL};color:#0a0d12;font-weight:700;}}"
            f"QTreeWidget::item:selected:!active{{background:{TEAL};color:#0a0d12;}}")
        for col,w in enumerate([200,140,100,70,80]):
            self._md_list.setColumnWidth(col,w)
        self._md_list.header().setStyleSheet(
            f"QHeaderView::section{{background:{SURF2};color:{GOLD2};font-weight:700;"
            f"font-size:{FS_SMALL}px;padding:6px;border:1px solid {BORDER};}}")
        self._md_list.itemDoubleClicked.connect(self._add_mundane_from_browser)
        mdt.addWidget(self._md_list,1)
        add_selected = pill_btn("⬅  Add Selected to Inventory", TEAL)
        add_selected.clicked.connect(lambda: self._add_mundane_from_browser(self._md_list.currentItem(),0))
        mdt.addWidget(add_selected)
        right_tabs.addTab(mundane_tab, "⚔  Mundane Equipment")

        # ── MAGIC ITEM BROWSER ────────────────────────────────────────────────
        magic_tab = QWidget(); mgt = QVBoxLayout(magic_tab)
        mgt.setContentsMargins(8,8,8,8); mgt.setSpacing(6)

        mgt_top = QHBoxLayout()
        self._mi_search = QLineEdit(); self._mi_search.setPlaceholderText("Search magic items…")
        self._mi_search.setStyleSheet(f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};"
                                        f"border-radius:6px;padding:4px 8px;color:{TEXT};}}")
        self._mi_type_f = QComboBox()
        self._mi_type_f.addItems(["All Slots","Weapon","Armor","Ring","Cloak / Robe",
                                    "Hat / Helm","Boots / Slippers","Bracers / Gauntlets",
                                    "Belt","Potion","Scroll / Wand / Rod / Staff","Other"])
        self._mi_rarity_f = QComboBox()
        self._mi_rarity_f.addItems(["All Rarities","Common","Uncommon","Rare","Very Rare","Legendary","Artifact"])
        self._mi_attune_f = QComboBox()
        self._mi_attune_f.addItems(["All","Requires Attunement","No Attunement"])
        mgt_top.addWidget(self._mi_search,2)
        mgt_top.addWidget(self._mi_type_f)
        mgt_top.addWidget(self._mi_rarity_f)
        mgt_top.addWidget(self._mi_attune_f)
        mgt.addLayout(mgt_top)

        self._mi_browser = QListWidget()
        self._mi_browser.setStyleSheet(
            f"QListWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;}}"
            f"QListWidget::item{{padding:6px 10px;font-size:{FS_BODY}px;color:{TEXT};}}"
            f"QListWidget::item:selected{{background:{PURP2};color:#15071f;font-weight:700;}}"
            f"QListWidget::item:selected:!active{{background:{PURP2};color:#15071f;}}"
            f"QListWidget::item:alternate{{background:{SURF};}}")
        self._mi_browser.setAlternatingRowColors(True)
        self._mi_browser.itemDoubleClicked.connect(lambda item: self._add_magic_item_by_name(item.data(Qt.UserRole)))
        mgt.addWidget(self._mi_browser,1)

        mi_add_btn = pill_btn("✨  Add Selected to Inventory", INDIGO)
        mi_add_btn.clicked.connect(self._add_magic_from_browser)
        mgt.addWidget(mi_add_btn)
        right_tabs.addTab(magic_tab, "✨  Magic Items")

        companions_tab = self._build_companions_tab()
        right_tabs.addTab(companions_tab, "🐉  Companions")

        splitter.addWidget(right_tabs)
        splitter.setSizes([380,500])
        root.addWidget(splitter,1)

        # Connect filters
        self._mi_search.textChanged.connect(self._populate_magic_browser)
        self._mi_type_f.currentTextChanged.connect(self._populate_magic_browser)
        self._mi_rarity_f.currentTextChanged.connect(self._populate_magic_browser)
        self._mi_attune_f.currentTextChanged.connect(self._populate_magic_browser)
        self._md_search.textChanged.connect(self._populate_mundane_browser)
        self._md_cat.currentTextChanged.connect(self._populate_mundane_browser)

        # Populate browsers
        self._populate_mundane_browser()
        self._populate_magic_browser()
        return tab

    def _build_companions_tab(self):
        """Shows live stat blocks (real numbers, not formulas) for
        whichever companion/summon features the character currently
        qualifies for — Steel Defender, Wildfire Spirit, Drake Companion,
        Dancing Item, Eldritch Cannon, or the Beast Master's three Primal
        Companion options. Rebuilt on every refresh since most of these
        scale with class level."""
        tab = QWidget()
        outer = QVBoxLayout(tab); outer.setContentsMargins(8,8,8,8)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        self._companions_lay = QVBoxLayout(inner); self._companions_lay.setSpacing(10)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        self._refresh_companions_tab()
        return tab

    def _build_mounts_section(self):
        """Mounts get a real stat block card here instead of being treated
        as generic carried equipment — a Warhorse has an AC, HP, and attacks
        that matter in play, not just a weight and a price."""
        from dnd_app.data.items import MOUNTS
        from dnd_app.data.statblocks import get_mount_statblock

        mc = _card(GOLD+"55")
        mcl = QVBoxLayout(mc); mcl.setContentsMargins(14,12,14,12); mcl.setSpacing(6)
        mcl.addWidget(_lbl("Mounts", GOLD2, FS_TITLE, bold=True))

        picker_row = QHBoxLayout(); picker_row.setSpacing(8)
        picker_row.addWidget(_lbl("Add a mount:", TEXT2, FS_SMALL, bold=True, wrap=False))
        add_combo = QComboBox()
        add_combo.setAccessibleName("Choose a mount to add")
        for row in MOUNTS:
            add_combo.addItem(row[0], row[0])
        picker_row.addWidget(add_combo, 1)
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(lambda checked=False, cb=add_combo: self._add_mount(cb.currentData()))
        picker_row.addWidget(add_btn)
        mcl.addLayout(picker_row)

        # Find Steed / Find Greater Steed — same underlying mount system,
        # since casting either spell is summoning a mount, just one that
        # happens to be a celestial/fey/fiend spirit rather than a mundane
        # animal. Previously casting these spells did nothing beyond the
        # normal spell-casting flow — no way to actually add the steed.
        from dnd_app.data.statblocks import FIND_GREATER_STEED_OPTIONS
        steed_row = QHBoxLayout(); steed_row.setSpacing(8)
        steed_row.addWidget(_lbl("Find Steed / Find Greater Steed:", TEAL2, FS_SMALL, bold=True, wrap=False))
        steed_combo = QComboBox()
        steed_combo.setAccessibleName("Choose a steed form to summon")
        for name in ["Warhorse", "Pony", "Camel", "Elk", "Mastiff"]:
            steed_combo.addItem(f"{name} (Find Steed)", name)
        for name in FIND_GREATER_STEED_OPTIONS:
            steed_combo.addItem(f"{name} (Find Greater Steed)", name)
        steed_row.addWidget(steed_combo, 1)
        steed_btn = QPushButton("+ Summon")
        steed_btn.clicked.connect(lambda checked=False, cb=steed_combo: self._add_mount(cb.currentData()))
        steed_row.addWidget(steed_btn)
        mcl.addLayout(steed_row)
        self._companions_lay.addWidget(mc)

        owned = self.char.get("owned_mounts", [])
        for i, mount_name in enumerate(owned):
            sb_data = get_mount_statblock(mount_name)
            if not sb_data:
                continue
            sb = {
                "display_name": mount_name, "source": "Mount",
                "size": sb_data["size"], "creature_type": "beast",
                "ac": str(sb_data["ac"]) + (f" ({sb_data['ac_note']})" if sb_data.get("ac_note") else ""),
                "hp": sb_data["hp"], "hit_dice": sb_data["hit_dice"], "speed": sb_data["speed"],
                "abilities": sb_data["abilities"], "saves": [], "skills": sb_data["skills"],
                "damage_immunities": "", "condition_immunities": "",
                "senses": sb_data["senses"], "languages": "\u2014",
                "traits": sb_data["traits"], "actions": sb_data["actions"], "reactions": [],
            }
            card = self._build_statblock_card(sb, hp_key=f"mount_{mount_name}")
            # than a separate row, so it's clearly tied to that one mount.
            remove_btn = QPushButton("\u2715 Remove")
            remove_btn.setStyleSheet(
                f"QPushButton{{background:{qa(CRIMSON,0x33)};border:1px solid {CRIMSON};"
                f"border-radius:5px;color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:4px 10px;min-height:0px;}}"
                f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
            remove_btn.clicked.connect(lambda checked=False, idx=i: self._remove_mount(idx))
            card.layout().insertWidget(0, remove_btn, 0, Qt.AlignRight)
            self._companions_lay.addWidget(card)

    def _build_vehicles_section(self):
        """Vehicles get the same treatment as mounts: water vehicles (which
        have real, official AC/HP/speed stats) get a full stat block card
        with HP tracking, same as a mount. Land vehicles (Cart, Wagon,
        Chariot, etc.) have no official 5e combat stats in any published
        source, so they get a simpler info row instead of a fabricated
        stat block."""
        from dnd_app.data.items import (VEHICLES, VEHICLES_WATER, VEHICLES_AIR, VEHICLES_LAND,
                                         VEHICLES_BGDIA, VEHICLES_MAGIC, ADVENTURING_GEAR)
        from dnd_app.data.statblocks import get_vehicle_statblock

        vc = _card(TEAL+"55")
        vcl = QVBoxLayout(vc); vcl.setContentsMargins(14,12,14,12); vcl.setSpacing(6)
        vcl.addWidget(_lbl("Vehicles", TEAL2, FS_TITLE, bold=True))

        picker_row = QHBoxLayout(); picker_row.setSpacing(8)
        picker_row.addWidget(_lbl("Add a vehicle:", TEXT2, FS_SMALL, bold=True, wrap=False))
        add_combo = QComboBox()
        add_combo.setAccessibleName("Choose a vehicle to add")
        for vname in VEHICLES:
            add_combo.addItem(vname, vname)
        picker_row.addWidget(add_combo, 1)
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(lambda checked=False, cb=add_combo: self._add_vehicle(cb.currentData()))
        picker_row.addWidget(add_btn)
        vcl.addLayout(picker_row)
        self._companions_lay.addWidget(vc)

        owned = self.char.get("owned_vehicles", [])
        gear_lookup = {g[0]: g for g in ADVENTURING_GEAR}
        for i, vname in enumerate(owned):
            vdata = get_vehicle_statblock(vname)
            if vdata:
                extra_traits = [
                    ("Cargo", vdata.get("cargo", "\u2014")),
                    ("Crew", vdata.get("crew", "\u2014")),
                ]
                if vdata.get("passengers"):
                    extra_traits.append(("Passengers", vdata["passengers"]))
                if vdata.get("keel_beam"):
                    extra_traits.append(("Keel/Beam", vdata["keel_beam"]))
                no_stats = vdata.get("no_combat_stats", False)
                is_magic_item = vdata.get("is_magic_item", False)
                if vdata.get("keel_beam"):
                    source_label = "Spelljamming Vessel"
                elif vname in VEHICLES_BGDIA:
                    source_label = "Combat Vehicle (Bigby Presents: Glory of the Giants)"
                elif is_magic_item and no_stats:
                    source_label = "Magic Item Vehicle (no official combat stats)"
                elif is_magic_item:
                    source_label = "Magic Item Vehicle"
                elif no_stats:
                    source_label = "Astral Vehicle (no official combat stats)"
                elif vname in VEHICLES_AIR:
                    source_label = "Air Vehicle"
                elif vname in VEHICLES_LAND:
                    source_label = "Land Vehicle"
                else:
                    source_label = "Vehicle"
                sb = {
                    "display_name": vname, "source": source_label,
                    "size": vdata["size"], "creature_type": "vehicle (object)",
                    "ac": "\u2014" if no_stats else str(vdata["ac"]),
                    "hp": "\u2014" if no_stats else vdata["hp"], "hit_dice": "",
                    "speed": vdata["speed"], "abilities": vdata.get("abilities", {}), "saves": [], "skills": [],
                    "damage_immunities": vdata.get("damage_immunities", ""),
                    "condition_immunities": vdata.get("condition_immunities", ""),
                    "senses": "\u2014", "languages": "\u2014",
                    "traits": vdata.get("traits", []) + extra_traits,
                    "actions": vdata.get("actions", []), "reactions": vdata.get("reactions", []),
                }
                # No HP tracking (hp_key) for vehicles with no real HP value —
                # nothing to track, and passing one would create a phantom
                # persistent-storage entry for a stat that doesn't exist.
                card_hp_key = None if no_stats else f"vehicle_{vname}"
                card = self._build_statblock_card(sb, hp_key=card_hp_key)
                remove_btn = QPushButton("\u2715 Remove")
                remove_btn.setStyleSheet(
                    f"QPushButton{{background:{qa(CRIMSON,0x33)};border:1px solid {CRIMSON};"
                    f"border-radius:5px;color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:4px 10px;min-height:0px;}}"
                    f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
                remove_btn.clicked.connect(lambda checked=False, idx=i: self._remove_vehicle(idx))
                card.layout().insertWidget(0, remove_btn, 0, Qt.AlignRight)
                self._companions_lay.addWidget(card)
            else:
                # Land vehicle: no official combat stats — simple info row
                # pulled from the general gear catalog (cost/weight/desc).
                g = gear_lookup.get(vname)
                desc = g[3] if g else ""
                row = _card(GOLD+"33")
                rl = QHBoxLayout(row); rl.setContentsMargins(12,8,12,8); rl.setSpacing(10)
                rl.addWidget(_lbl("🛒", GOLD2, FS_BODY, wrap=False))
                name_col = QVBoxLayout(); name_col.setSpacing(0)
                name_col.addWidget(_lbl(vname, TEXT, FS_BODY, bold=True, wrap=False))
                name_col.addWidget(_lbl(desc, TEXT3, FS_TINY))
                rl.addLayout(name_col, 1)
                rm2 = QPushButton("\u2715 Remove")
                rm2.setStyleSheet(
                    f"QPushButton{{background:{qa(CRIMSON,0x33)};border:1px solid {CRIMSON};"
                    f"border-radius:5px;color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:4px 10px;}}"
                    f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
                rm2.clicked.connect(lambda checked=False, idx=i: self._remove_vehicle(idx))
                rl.addWidget(rm2)
                self._companions_lay.addWidget(row)

    def _add_vehicle(self, name: str):
        if not name: return
        self.char.setdefault("owned_vehicles", []).append(name)
        self._mark_dirty()
        self._refresh_companions_tab()

    def _remove_vehicle(self, index: int):
        owned = self.char.get("owned_vehicles", [])
        if 0 <= index < len(owned):
            owned.pop(index)
            self._mark_dirty()
            self._refresh_companions_tab()

    def _summon_companion(self, key: str):
        """Handler for a requires_summon_action companion's Summon
        button (Drake Companion, Dancing Item, Wildfire Spirit).
        Confirmed via the user's own request: spends the linked
        resource charge (or a Wild Shape use, for Wildfire Spirit,
        which shares that pool rather than having its own dedicated
        resource), marks the companion active so its stat block card
        appears, and resets its tracked HP to full — matching a fresh
        summon rather than picking up mid-fight with whatever HP was
        left from a previous card render."""
        from dnd_app.data.statblocks import COMPANION_STATBLOCKS
        tmpl = COMPANION_STATBLOCKS.get(key)
        if not tmpl:
            return
        if tmpl.get("summon_uses_wild_shape"):
            if not self._spend_wildshape_use():
                self._toast("No Wild Shape uses remaining — available again after a short or long rest.")
                return
        else:
            res_key = tmpl.get("summon_resource_key")
            if res_key:
                res = next((r for r in self.char.get("resources", []) if r.get("key") == res_key), None)
                if res is not None and res.get("current", 0) <= 0:
                    self._toast(f"No uses of {res['name']} remaining — available again after a long rest.")
                    return
                if res is not None:
                    res["current"] = res.get("current", 1) - 1
        active = self.char.setdefault("active_summoned_companions", [])
        if key not in active:
            active.append(key)
        from dnd_app.core.calculator import resolve_companion_statblock
        sb = resolve_companion_statblock(key, self.char)
        self.char.setdefault("summon_hp_tracking", {})[f"companion_{key}"] = sb.get("hp", 1)
        self._mark_dirty()
        self._refresh_companions_tab()
        self._toast(f"\U0001f409 {tmpl['display_name']} summoned!")

    def _dismiss_companion(self, key: str):
        """Remove a requires_summon_action companion from the active
        set — called both by an explicit dismiss and, from within
        _build_statblock_card's HP handler, automatically once its
        tracked HP reaches 0 (matching the real rule: the companion
        remains until reduced to 0 HP, re-summoned, or you die)."""
        active = self.char.get("active_summoned_companions", [])
        if key in active:
            active.remove(key)
            self._mark_dirty()
            self._refresh_companions_tab()

    def _add_mount(self, name: str):
        if not name: return
        self.char.setdefault("owned_mounts", []).append(name)
        self._mark_dirty()
        self._refresh_companions_tab()

    def _remove_mount(self, index: int):
        owned = self.char.get("owned_mounts", [])
        if 0 <= index < len(owned):
            owned.pop(index)
            self._mark_dirty()
            self._refresh_companions_tab()

    def _build_summoned_creatures_section(self):
        """Summon Celestial, Summon Undead, Summon Fiend, and the rest of
        the Tasha's/Fizban's/Book of Many Things summon-a-spirit spells —
        previously casting any of these did nothing beyond the normal
        spell-casting flow; there was no way to actually add the summoned
        creature anywhere. Each entry stores (spell, cast level, form) so
        the stat block can be recomputed correctly if you look at it again
        (e.g. after leveling up your spell save DC)."""
        from dnd_app.data.statblocks import SCALING_SUMMONS, resolve_scaling_summon

        sc = _card(TEAL+"55")
        scl = QVBoxLayout(sc); scl.setContentsMargins(14,12,14,12); scl.setSpacing(6)
        scl.addWidget(_lbl("Summoned Creatures", TEAL2, FS_TITLE, bold=True))
        scl.addWidget(_lbl("For Summon Celestial, Summon Undead, Summon Fiend, Summon Beast, and similar "
                           "spells — pick the spell, the level you're casting it at, and its form.",
                           TEXT3, FS_SMALL))

        picker_row = QHBoxLayout(); picker_row.setSpacing(8)
        spell_combo = QComboBox(); spell_combo.setAccessibleName("Choose a summon spell")
        for name in SCALING_SUMMONS:
            spell_combo.addItem(name, name)
        picker_row.addWidget(spell_combo, 1)

        level_combo = QComboBox(); level_combo.setAccessibleName("Choose the spell slot level")
        form_combo = QComboBox(); form_combo.setAccessibleName("Choose the summon's form")

        def _refresh_level_and_form():
            spell_name = spell_combo.currentData()
            spell = SCALING_SUMMONS.get(spell_name, {})
            level_combo.clear()
            for lvl in range(spell.get("base_level", 1), 10):
                level_combo.addItem(f"Level {lvl}", lvl)
            form_combo.clear()
            for form in spell.get("forms", {}):
                form_combo.addItem(form, form)
        spell_combo.currentIndexChanged.connect(lambda i: _refresh_level_and_form())
        _refresh_level_and_form()

        picker_row.addWidget(level_combo)
        picker_row.addWidget(form_combo)
        add_btn = QPushButton("+ Summon")
        add_btn.clicked.connect(lambda checked=False: self._add_summoned_creature(
            spell_combo.currentData(), level_combo.currentData(), form_combo.currentData()))
        picker_row.addWidget(add_btn)
        scl.addLayout(picker_row)
        self._companions_lay.addWidget(sc)

        owned = self.char.get("owned_summons", [])
        for i, entry in enumerate(owned):
            spell_name, lvl, form = entry.get("spell"), entry.get("level"), entry.get("form")
            sb = resolve_scaling_summon(spell_name, lvl, form)
            if not sb:
                continue
            card = self._build_statblock_card(sb, hp_key=f"summon_{i}")
            remove_btn.setStyleSheet(
                f"QPushButton{{background:{qa(CRIMSON,0x33)};border:1px solid {CRIMSON};"
                f"border-radius:5px;color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:4px 10px;min-height:0px;}}"
                f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
            remove_btn.clicked.connect(lambda checked=False, idx=i: self._remove_summoned_creature(idx))
            card.layout().insertWidget(0, remove_btn, 0, Qt.AlignRight)
            self._companions_lay.addWidget(card)

    def _add_summoned_creature(self, spell_name: str, level: int, form: str):
        if not (spell_name and level and form): return
        self.char.setdefault("owned_summons", []).append(
            {"spell": spell_name, "level": level, "form": form})
        self._mark_dirty()
        self._refresh_companions_tab()

    def _remove_summoned_creature(self, index: int):
        owned = self.char.get("owned_summons", [])
        if 0 <= index < len(owned):
            owned.pop(index)
            self._mark_dirty()
            self._refresh_companions_tab()

    def _refresh_companions_tab(self):
        if not hasattr(self, "_companions_lay"):
            return
        while self._companions_lay.count():
            item = self._companions_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Mounts are available to any character regardless of class — shown
        # first, always, unlike the class-gated companions/Wild Shape below.
        self._build_mounts_section()
        self._build_vehicles_section()
        self._build_summoned_creatures_section()

        from dnd_app.core.calculator import (get_available_companions, resolve_companion_statblock,
            get_available_wildshape_beasts, get_wild_shape_info, get_summonable_but_inactive_companions)
        keys = get_available_companions(self.char)
        beast_names = get_available_wildshape_beasts(self.char)
        summonable = get_summonable_but_inactive_companions(self.char)

        if not keys and not beast_names and not summonable:
            self._companions_lay.addWidget(_lbl(
                "No class-granted companion, summon, or Wild Shape stat blocks apply to "
                "your current class/subclass/level. This section fills in automatically "
                "for Battle Smith Artificers, Circle of Wildfire Druids, Drakewarden "
                "Rangers, Beast Master Rangers, College of Creation Bards (once you "
                "animate an item), Artillerist Artificers, and any Druid once Wild Shape "
                "is available.", TEXT3, FS_SMALL))
            self._companions_lay.addStretch()
            return

        if beast_names:
            info = get_wild_shape_info(self.char)
            wc = _card(GREEN+"55")
            wcl = QVBoxLayout(wc); wcl.setContentsMargins(14,12,14,12); wcl.setSpacing(6)
            wcl.addWidget(_lbl("Wild Shape", TEAL2, FS_TITLE, bold=True))
            wcl.addWidget(_lbl(f"Max CR {info['max_cr']} \u2014 {info['restriction']}", TEXT3, FS_TINY))
            picker_row = QHBoxLayout(); picker_row.setSpacing(8)
            picker_row.addWidget(_lbl("Turn into:", TEXT2, FS_SMALL, bold=True, wrap=False))
            self._wildshape_combo = QComboBox()
            self._wildshape_combo.setAccessibleName("Choose a beast to view its Wild Shape stat block")
            def _sort_key(n):
                from dnd_app.data.statblocks import WILDSHAPE_BEASTS
                return WILDSHAPE_BEASTS[n]["cr"]
            for name in sorted(beast_names, key=_sort_key):
                from dnd_app.data.statblocks import WILDSHAPE_BEASTS
                cr = WILDSHAPE_BEASTS[name]["cr_label"]
                self._wildshape_combo.addItem(f"{name}  (CR {cr})", name)
            picker_row.addWidget(self._wildshape_combo, 1)
            wcl.addLayout(picker_row)
            self._wildshape_card_host = QVBoxLayout(); self._wildshape_card_host.setSpacing(0)
            wcl.addLayout(self._wildshape_card_host)
            self._wildshape_combo.currentIndexChanged.connect(self._refresh_wildshape_beast_card)
            self._companions_lay.addWidget(wc)
            self._refresh_wildshape_beast_card()

        for key in keys:
            if key == "eldritch_cannon":
                card = self._build_eldritch_cannon_card()
            else:
                sb = resolve_companion_statblock(key, self.char)
                # Hardened against a real, plausible scenario: a stale
                # companion key from an earlier session/version that no
                # longer matches anything in COMPANION_STATBLOCKS returns
                # an empty dict here, which would otherwise crash with a
                # KeyError reading sb["hp"] below.
                if not sb:
                    continue
                card = self._build_statblock_card(sb, hp_key=f"companion_{key}", companion_key=key)
            self._companions_lay.addWidget(card)

        # Summon-gated companions the character qualifies for but hasn't
        # summoned yet (currently just Drake Companion) — shown as a
        # prompt card instead of the full stat block, since there's
        # nothing to show HP/AC for until it's actually been summoned.
        from dnd_app.data.statblocks import COMPANION_STATBLOCKS
        for key in summonable:
            tmpl = COMPANION_STATBLOCKS.get(key, {})
            sc = _card(TEAL+"33")
            scl2 = QVBoxLayout(sc); scl2.setContentsMargins(14,12,14,12); scl2.setSpacing(6)
            scl2.addWidget(_lbl(tmpl.get("display_name", key), TEAL2, FS_TITLE, bold=True))
            if tmpl.get("summon_uses_wild_shape"):
                ws_left, ws_max = self._wildshape_uses_left()
                uses_txt = (" (Unlimited Wild Shape uses)" if ws_left is None
                            else f" ({ws_left}/{ws_max} Wild Shape uses left)")
            else:
                res_key = tmpl.get("summon_resource_key")
                res = next((r for r in self.char.get("resources", []) if r.get("key") == res_key), None)
                uses_txt = f" ({res['current']}/{res['current_max']} uses left)" if res else ""
            scl2.addWidget(_lbl(f"Not currently summoned.{uses_txt}", TEXT3, FS_SMALL))
            summon_btn = QPushButton(f"Summon {tmpl.get('display_name', key)}")
            summon_btn.clicked.connect(lambda checked=False, k=key: self._summon_companion(k))
            scl2.addWidget(summon_btn)
            self._companions_lay.addWidget(sc)
        self._companions_lay.addStretch()

    def _refresh_wildshape_beast_card(self):
        if not hasattr(self, "_wildshape_card_host"):
            return
        while self._wildshape_card_host.count():
            item = self._wildshape_card_host.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        name = self._wildshape_combo.currentData()
        if not name or name not in WILDSHAPE_BEASTS:
            return
        beast = WILDSHAPE_BEASTS[name]
        sb = {
            "display_name": name, "source": f"Wild Shape (CR {beast['cr_label']})",
            "size": beast["size"], "creature_type": "beast",
            "ac": str(beast["ac"]) + (f" ({beast['ac_note']})" if beast.get("ac_note") else ""),
            "hp": beast["hp"], "hit_dice": beast["hit_dice"], "speed": beast["speed"],
            "abilities": beast["abilities"], "saves": [], "skills": beast["skills"],
            "damage_resistances": beast.get("damage_resistances", ""),
            "damage_immunities": beast.get("damage_immunities", ""),
            "condition_immunities": beast.get("condition_immunities", ""),
            "senses": beast["senses"], "languages": "\u2014",
            "traits": beast["traits"], "actions": beast["actions"], "reactions": [],
        }
        card = self._build_statblock_card(sb)
        self._wildshape_card_host.addWidget(card)

    def _build_statblock_card(self, sb: dict, start_expanded: bool = False, hp_key: str = None,
                               companion_key: str = None) -> QFrame:
        """An expandable tile: collapsed by default, showing just name, HP,
        and AC so a Companions tab with several mounts/summons/wild shape
        options stays scannable instead of every card being fully expanded
        (and taking up a full screen of space) all the time. Click the
        header to expand the full stat block.

        hp_key: if given, HP is shown as an editable spinbox backed by
        persistent per-creature tracking (char['summon_hp_tracking'][hp_key])
        instead of a static label showing only the max value forever with
        no way to record damage actually taken. Pass a stable, unique key
        per owned creature (e.g. f"summon_{i}", f"mount_{steed_name}",
        f"companion_{key}"). Left as None for purely informational/preview
        cards (e.g. the Wild Shape form preview, whose real active HP is
        tracked separately via the Combat tab once actually transformed)."""
        card = _card(TEAL+"55")
        cl = QVBoxLayout(card); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)

        tracking = self.char.setdefault("summon_hp_tracking", {}) if hp_key else {}
        # Some statblocks (e.g. "Tasha's Creeping Keelboat") store hp as
        # a non-numeric placeholder like '—' rather than a real number,
        # since the creature/vehicle has no standard numeric HP in its
        # own source text. QSpinBox.setRange requires an int, so this
        # falls back to 1 (still shown, but not a broken/negative
        # range) rather than trusting the raw value to always be a real int.
        raw_hp = sb["hp"]
        max_hp = raw_hp if isinstance(raw_hp, int) else 1
        if hp_key:
            cur_hp = tracking.get(hp_key, max_hp)
        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame{background:transparent;border:none;}")
        hl = QHBoxLayout(header); hl.setContentsMargins(14,12,14,12); hl.setSpacing(14)
        chevron = _lbl("\u25b6", TEAL2, FS_BODY, bold=True, wrap=False)
        hl.addWidget(chevron)
        name_col = QVBoxLayout(); name_col.setSpacing(0)
        name_col.addWidget(_lbl(sb["display_name"], TEAL2, FS_BODY, bold=True, wrap=False))
        name_col.addWidget(_lbl(sb["source"], TEXT3, FS_TINY, wrap=False))
        hl.addLayout(name_col)
        hl.addStretch()
        hl.addWidget(_lbl(f"AC {sb['ac']}", GOLD2, FS_BODY, bold=True, wrap=False))

        hp_spin_header = None
        if hp_key:
            hp_row_hdr = QHBoxLayout(); hp_row_hdr.setSpacing(3)
            hp_row_hdr.addWidget(_lbl("HP", GREEN2, FS_BODY, bold=True, wrap=False))
            hp_spin_header = QSpinBox()
            hp_spin_header.setRange(0, max_hp)
            hp_spin_header.setValue(cur_hp)
            hp_spin_header.setFixedWidth(56)
            hp_spin_header.setAccessibleName(f"{sb['display_name']} current HP")
            hp_spin_header.setToolTip("Current HP for this creature — edits are saved.")
            hp_row_hdr.addWidget(hp_spin_header)
            hp_row_hdr.addWidget(_lbl(f"/ {max_hp}", TEXT3, FS_SMALL, wrap=False))
            # Stop clicks on the spinbox itself from also toggling the
            # header's expand/collapse (the header's mousePressEvent is
            # attached further down and would otherwise fire too).
            hp_spin_hdr_host = QWidget(); hp_spin_hdr_host.setLayout(hp_row_hdr)
            hl.addWidget(hp_spin_hdr_host)
        else:
            hl.addWidget(_lbl(f"HP {sb['hp']}", GREEN2, FS_BODY, bold=True, wrap=False))
        cl.addWidget(header)

        details = QFrame()
        details.setStyleSheet("QFrame{background:transparent;border:none;}")
        details.setVisible(start_expanded)
        dl = QVBoxLayout(details); dl.setContentsMargins(14,0,14,12); dl.setSpacing(6)

        dl.addWidget(_lbl(f"{sb['size']} {sb['creature_type']}", TEXT2, FS_SMALL, bold=True))
        stat_row = QHBoxLayout(); stat_row.setSpacing(18)
        if hp_key:
            hp_lbl_detail = _lbl(f"HP {cur_hp}/{max_hp}" + (f"  ({sb['hit_dice']})" if sb.get("hit_dice") else ""),
                                  GREEN2, FS_BODY, bold=True, wrap=False)
            stat_row.addWidget(hp_lbl_detail)

            def _on_hp_spin_changed(v):
                tracking[hp_key] = v
                self._mark_dirty()
                hp_lbl_detail.setText(f"HP {v}/{max_hp}" + (f"  ({sb['hit_dice']})" if sb.get("hit_dice") else ""))
                if v <= 0 and companion_key:
                    from dnd_app.data.statblocks import COMPANION_STATBLOCKS
                    tmpl = COMPANION_STATBLOCKS.get(companion_key, {})
                    if tmpl.get("requires_summon_action"):
                        self._toast(f"\U0001f480 {sb['display_name']} has fallen — re-summon it after a long rest.")
                        self._dismiss_companion(companion_key)
                    elif tmpl.get("requires_active_infusion"):
                        # The real rule: "if you or the homunculus dies,
                        # it vanishes, leaving its heart in its space."
                        # Remove the active_infusions entry entirely —
                        # re-creating it needs a fresh infuse action (the
                        # infusion itself is still known, just not
                        # currently applied), not a rest-based recovery.
                        req_name = tmpl["requires_active_infusion"]
                        self.char["active_infusions"] = [
                            a for a in self.char.get("active_infusions", [])
                            if a.get("infusion") != req_name]
                        self._mark_dirty()
                        self._toast(f"\U0001f480 {sb['display_name']} has vanished, leaving its heart behind — "
                                    f"re-infuse a gem to create a new one.")
                        self._refresh_companions_tab()
                    else:
                        # Unlimited-recreation companions (Steel Defender,
                        # Beast of the Land/Sea/Sky) have no summon
                        # resource to gate re-creation, but the real rule
                        # still ties recreation to "the end of a long
                        # rest," not instant reappearance — so mark it
                        # pending instead of leaving it available.
                        pending = self.char.setdefault("companion_pending_replacement", [])
                        if companion_key not in pending:
                            pending.append(companion_key)
                        self._mark_dirty()
                        self._toast(f"\U0001f480 {sb['display_name']} has perished — a new one can be made at your next long rest.")
                        self._refresh_companions_tab()
            hp_spin_header.valueChanged.connect(_on_hp_spin_changed)
        else:
            hp_txt = f"HP {sb['hp']}"
            if sb.get("hit_dice"):
                hp_txt += f"  ({sb['hit_dice']})"
            stat_row.addWidget(_lbl(hp_txt, GREEN2, FS_BODY, bold=True, wrap=False))
        stat_row.addWidget(_lbl(f"Speed {sb['speed']}", TEAL2, FS_BODY, bold=True, wrap=False))
        stat_row.addStretch()
        dl.addLayout(stat_row)

        ab_row = QHBoxLayout(); ab_row.setSpacing(10)
        for ab, score in sb["abilities"].items():
            mod = (score - 10) // 2
            mod_str = f"+{mod}" if mod >= 0 else str(mod)
            col = QVBoxLayout(); col.setSpacing(0)
            col.addWidget(_lbl(ab, TEXT3, FS_TINY, bold=True, align=Qt.AlignCenter))
            col.addWidget(_lbl(f"{score} ({mod_str})", TEXT, FS_SMALL, bold=True, align=Qt.AlignCenter, wrap=False))
            ab_row.addLayout(col)
        ab_row.addStretch()
        dl.addLayout(ab_row)

        if sb.get("saves"):
            dl.addWidget(_lbl("Saving Throws: " + ", ".join(f"{a} {v}" for a,v in sb["saves"]), TEXT2, FS_SMALL))
        if sb.get("skills"):
            dl.addWidget(_lbl("Skills: " + ", ".join(f"{s} {v}" for s,v in sb["skills"]), TEXT2, FS_SMALL))
        if sb.get("damage_resistances"):
            dl.addWidget(_lbl("Damage Resistances: " + sb["damage_resistances"], TEXT2, FS_SMALL))
        if sb.get("damage_immunities"):
            dl.addWidget(_lbl("Damage Immunities: " + sb["damage_immunities"], TEXT2, FS_SMALL))
        if sb.get("condition_immunities"):
            dl.addWidget(_lbl("Condition Immunities: " + sb["condition_immunities"], TEXT2, FS_SMALL))
        dl.addWidget(_lbl("Senses: " + sb["senses"], TEXT2, FS_SMALL))
        dl.addWidget(_lbl("Languages: " + sb["languages"], TEXT2, FS_SMALL))

        for section_name, entries in [("Traits", sb.get("traits")),
                                        ("Actions", sb.get("actions")),
                                        ("Reactions", sb.get("reactions"))]:
            if not entries:
                continue
            dl.addWidget(_lbl(section_name.upper(), GOLD2, FS_SMALL, bold=True))
            for name, desc in entries:
                line = _lbl(f"{name}. {desc}", TEXT, FS_SMALL, wrap=True)
                dl.addWidget(line)
        cl.addWidget(details)

        def _toggle(event, d=details, chev=chevron):
            d.setVisible(not d.isVisible())
            chev.setText("\u25bc" if d.isVisible() else "\u25b6")
        header.mousePressEvent = _toggle

        return card

    def _build_eldritch_cannon_card(self) -> QFrame:
        from dnd_app.core.calculator import resolve_companion_statblock
        sb = resolve_companion_statblock("eldritch_cannon", self.char)
        card = _card(TEAL+"55")
        cl = QVBoxLayout(card); cl.setContentsMargins(14,12,14,12); cl.setSpacing(6)
        cl.addWidget(_lbl(sb["display_name"], TEAL2, FS_TITLE, bold=True))
        cl.addWidget(_lbl(sb["source"], TEXT3, FS_TINY))
        cl.addWidget(_lbl(f"{sb['size']} {sb['creature_type']}", TEXT2, FS_SMALL, bold=True))
        stat_row = QHBoxLayout(); stat_row.setSpacing(18)
        stat_row.addWidget(_lbl(f"AC {sb['ac']}", GOLD2, FS_BODY, bold=True, wrap=False))
        stat_row.addWidget(_lbl(f"HP {sb['hp']}", GREEN2, FS_BODY, bold=True, wrap=False))
        stat_row.addStretch()
        cl.addLayout(stat_row)
        cl.addWidget(_lbl(sb["notes"], TEXT2, FS_SMALL))
        cl.addWidget(_lbl("ACTIVATION (bonus action, choose one type each time you create it)", GOLD2, FS_SMALL, bold=True))
        for name, desc in sb["cannon_types"]:
            cl.addWidget(_lbl(f"{name}. {desc}", TEXT, FS_SMALL))
        return card

    # ── Mundane browser ───────────────────────────────────────────────────────
    def _populate_mundane_browser(self):
        self._md_list.clear()
        cat = self._md_cat.currentText()
        search = self._md_search.text().lower()

        sections = []
        if cat in ("All","Weapons — Simple"):
            sections.append(("Simple Melee",   SIMPLE_MELEE,   "wep"))
            sections.append(("Simple Ranged",  SIMPLE_RANGED,  "wep"))
        if cat in ("All","Weapons — Martial"):
            sections.append(("Martial Melee",  MARTIAL_MELEE,  "wep"))
            sections.append(("Martial Ranged", MARTIAL_RANGED, "wep"))
        if cat in ("All","Materials (Silvered/Adamantine)"):
            # Silvering applies to any weapon ("weapons aren't limited
            # in choice"), while adamantine specifically applies only
            # to melee weapons or ammunition (XGE: "a melee weapon or
            # of ten pieces of ammunition") — a ranged weapon itself
            # can't be adamantine, only its ammunition can, so ranged
            # weapons only get a Silvered variant here, not an
            # Adamantine one.
            SILVER_TIP = ("this weapon's damage counts as silvered for the purpose of "
                          "overcoming a creature's resistance or immunity to nonmagical "
                          "attacks (e.g. many lycanthropes and certain undead)")
            ADAMANTINE_TIP = "whenever this weapon hits an object, the hit is a critical hit"
            melee_weapons = SIMPLE_MELEE + MARTIAL_MELEE
            ranged_weapons = SIMPLE_RANGED + MARTIAL_RANGED
            material_data = []
            for name, wcat, dmg, dtype, wt, cost, props in melee_weapons + ranged_weapons:
                new_props = list(props) + [f"Silvered: {SILVER_TIP}"]
                material_data.append((f"Silvered {name}", wcat, dmg, dtype, wt, cost + 100, new_props))
            for name, wcat, dmg, dtype, wt, cost, props in melee_weapons:
                new_props = list(props) + [f"Adamantine: {ADAMANTINE_TIP}"]
                material_data.append((f"Adamantine {name}", wcat, dmg, dtype, wt, cost + 500, new_props))
            sections.append(("Materials (Silvered/Adamantine — unmagical)", material_data, "wep"))
        if cat in ("All","Armor"):
            sections.append(("Armor",          ARMOR,           "arm"))
        if cat in ("All","Adventuring Gear"):
            sections.append(("Adventuring Gear", ADVENTURING_GEAR, "gear"))
        if cat in ("All","Tools"):
            tool_data = [(t,"Tool","—","—","varies") for t in ALL_TOOLS]
            sections.append(("Tools",          tool_data,       "tool"))
        if cat in ("All","Mounts & Vehicles"):
            sections.append(("Mounts",         MOUNTS,          "mount"))

        for section_name, items, kind in sections:
            parent = QTreeWidgetItem([section_name])
            parent.setForeground(0, __import__('PySide6.QtGui',fromlist=['QColor']).QColor(GOLD2))
            parent.setFont(0, __import__('PySide6.QtGui',fromlist=['QFont']).QFont("", -1, 700))
            parent.setData(0, Qt.UserRole, "__section__")
            added = 0
            for row in items:
                if kind == "wep":
                    name,wcat,dmg,dtype,wt,cost,props = row[0],row[1],row[2],row[3],row[4] if len(row)>4 else 0,row[5] if len(row)>5 else "—",row[6] if len(row)>6 else []
                    display_dmg = f"{dmg} {dtype}"
                    display_cat = wcat
                    display_wt  = f"{wt} lb"
                    display_cost= f"{cost} gp"
                elif kind == "arm":
                    name,akind,base_ac,dex_cap = row[0],row[1],row[2],row[3]
                    if name in ("No Armor","Mage Armor (spell)"): continue
                    display_dmg = f"AC {base_ac}" + (f" +DEX(max {dex_cap})" if dex_cap else " +DEX" if akind in ("light","medium") and dex_cap is None else "")
                    display_cat = akind.title()
                    display_wt  = f"{row[6] if len(row)>6 else '—'} lb" if len(row)>6 else "—"
                    display_cost= f"{row[7] if len(row)>7 else '—'} gp" if len(row)>7 else "—"
                elif kind == "gear":
                    name,wt,cost,notes = row[0],row[1],row[2],row[3] if len(row)>3 else ""
                    display_dmg = notes[:30] if notes else "—"
                    display_cat = "Gear"
                    display_wt  = f"{wt} lb"
                    display_cost= f"{cost} gp"
                elif kind == "tool":
                    name = row[0]; display_dmg="—"; display_cat="Tool"; display_wt="—"; display_cost="varies"
                elif kind == "mount":
                    name = row[0]
                    display_dmg = f"Speed {row[2]}'" if len(row)>2 else "—"
                    display_cat = "Mount"
                    display_wt  = str(row[1]) if len(row)>1 else "—"
                    display_cost= f"{row[4] if len(row)>4 else '—'} gp"
                else:
                    continue

                if search and search not in name.lower(): continue
                child = QTreeWidgetItem([name, display_cat, display_dmg, display_wt, display_cost])
                child.setData(0, Qt.UserRole, name)
                # Kind-appropriate tooltip built from the item's own
                # descriptive text (e.g. weapon property mechanics).
                tip_lines = [f"<b>{name}</b>"]
                if kind == "wep":
                    tip_lines.append(f"{display_cat} \u2014 {dmg} {dtype} \u2014 {display_wt} \u2014 {display_cost}")
                    if props:
                        tip_lines.append("<br>".join(str(p) for p in props))
                elif kind == "arm":
                    tip_lines.append(f"{display_cat} \u2014 {display_dmg} \u2014 {display_wt} \u2014 {display_cost}")
                elif kind == "gear":
                    tip_lines.append(f"{display_wt} \u2014 {display_cost}")
                    if notes:
                        tip_lines.append(notes)
                elif kind == "tool":
                    tip_lines.append("Tool proficiency")
                elif kind == "mount":
                    tip_lines.append(f"{display_dmg} \u2014 {display_cost}")
                child.setToolTip(0, "<br>".join(tip_lines))
                parent.addChild(child)
                added += 1

            if added > 0:
                self._md_list.addTopLevelItem(parent)
                parent.setExpanded(True)

    def _add_mundane_from_browser(self, item, col=None):
        if not item: return
        name = item.data(0, Qt.UserRole) if hasattr(item,'data') else item
        if not name or name == "__section__": return
        # Mounts get a real stat block in the Companions tab instead of a
        # generic equipment line — a Warhorse's AC/HP/attacks matter in
        # play, unlike a bedroll's weight and price.
        from dnd_app.data.items import MOUNTS
        if any(row[0] == name for row in MOUNTS):
            self._add_mount(name)
            self._toast(f"\U0001f40e {name} added — see its stat block in the Companions tab")
            return
        # Get weight and cost from item data
        from dnd_app.data.items import WEAPON_DICT, ARMOR_DICT, ADVENTURING_GEAR, ALL_WEAPONS
        weight = 0.0
        cost = 0.0
        wd = WEAPON_DICT.get(name)
        if wd:
            weight = float(wd.get("weight",0) or 0)
            cost = float(wd.get("cost",0) or 0)
        else:
            for g in ADVENTURING_GEAR:
                if g[0] == name: weight = float(g[1] or 0); cost = float(g[2] or 0); break
        # Ask quantity via a small dialog
        qty, ok = QInputDialog.getInt(self, f"Add {name}", f"How many {name}?", 1, 1, 9999, 1)
        if not ok: return
        eq = self.char.setdefault("equipment", [])
        existing = next((e for e in eq if isinstance(e,dict) and e.get("name")==name), None)
        if existing:
            existing["qty"] = existing.get("qty",1) + qty
        else:
            eq.append({"name": name, "qty": qty, "weight": weight, "cost": cost, "notes": ""})
        self._refresh_gear_equipment()
        if hasattr(self,"_update_weight"): self._update_weight()
        self._mark_dirty()

    # ── Magic item browser ────────────────────────────────────────────────────
    _SLOT_KEYWORDS = {
        "Weapon":        ["sword","axe","bow","mace","hammer","blade","lance","dagger","arrow",
                          "whip","spear","trident","quarterstaff","club","flail","handaxe",
                          "longsword","shortsword","scimitar","rapier","greatsword","greataxe"],
        "Armor":         ["armor","shield","chain","plate","leather","scale","breastplate",
                          "bracers of defense","elven chain"],
        "Ring":          ["ring"],
        "Cloak / Robe":  ["cloak","mantle","robe"],
        "Hat / Helm":    ["helm","hat","crown","tiara","circlet","cap","headband"],
        "Boots / Slippers":["boots","slippers","sandal","shoes"],
        "Bracers / Gauntlets":["bracers","gauntlets","gloves"],
        "Belt":          ["belt","girdle"],
        "Potion":        ["potion"],
        "Scroll / Wand / Rod / Staff": ["scroll","wand","rod","staff"],
    }

    def _mi_slot(self, item_name: str, itype: str) -> str:
        n = item_name.lower()
        for slot, kws in self._SLOT_KEYWORDS.items():
            if any(kw in n for kw in kws):
                return slot
        if itype in ("Wand","Rod","Staff","Scroll"): return "Scroll / Wand / Rod / Staff"
        if itype == "Potion": return "Potion"
        if itype == "Armor":  return "Armor"
        if itype == "Ring":   return "Ring"
        if itype == "Weapon": return "Weapon"
        return "Other"

    _RARITY_ORDER = ["Common","Uncommon","Rare","Very Rare","Legendary","Artifact"]
    _RARITY_COLORS = {
        "Common":    "#aaaaaa",
        "Uncommon":  "#1eff00",
        "Rare":      "#0070dd",
        "Very Rare": "#a335ee",
        "Legendary": "#ff8000",
        "Artifact":  "#e6cc80",
    }

    def _populate_magic_browser(self):
        self._mi_browser.clear()
        search  = self._mi_search.text().lower()
        slot_f  = self._mi_type_f.currentText()
        rarity_f= self._mi_rarity_f.currentText()
        attune_f= self._mi_attune_f.currentText()

        # Filter items
        filtered = []
        for item in ALL_MAGIC_ITEMS:
            n       = item["name"]
            rarity  = item.get("rarity","?")
            itype   = item.get("type","?")
            attune  = item.get("attunement", False)
            slot    = self._mi_slot(n, itype)

            if search and search not in n.lower(): continue
            if slot_f != "All Slots" and slot != slot_f: continue
            if rarity_f != "All Rarities" and rarity != rarity_f: continue
            if attune_f == "Requires Attunement" and not attune: continue
            if attune_f == "No Attunement" and attune: continue
            filtered.append(item)

        # Group by rarity with divider headers
        by_rarity = {}
        for item in filtered:
            r = item.get("rarity","?")
            by_rarity.setdefault(r,[]).append(item)

        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtGui import QColor, QFont
        for rarity in self._RARITY_ORDER:
            items_in_rarity = by_rarity.get(rarity,[])
            if not items_in_rarity: continue
            # Rarity divider header
            hdr = QListWidgetItem(f"── {rarity} ({len(items_in_rarity)}) ──")
            hdr.setForeground(QColor(self._RARITY_COLORS[rarity]))
            f = QFont(); f.setBold(True); f.setPointSize(9)
            hdr.setFont(f)
            hdr.setFlags(Qt.NoItemFlags)  # not selectable
            hdr.setData(Qt.UserRole, None)
            self._mi_browser.addItem(hdr)
            # Items in this rarity
            for item in sorted(items_in_rarity, key=lambda i: i["name"]):
                attune_tag = " ◆" if item.get("attunement") else ""
                desc = item.get("desc","")
                label = f"  {item['name']}{attune_tag}"
                li = QListWidgetItem(label)
                li.setForeground(QColor(self._RARITY_COLORS[rarity]))
                li.setData(Qt.UserRole, item["name"])
                if desc:
                    li.setToolTip(f"<b>{item['name']}</b> [{rarity}]<br><br>{desc[:300]}{'…' if len(desc)>300 else ''}")
                self._mi_browser.addItem(li)

    def _add_magic_from_browser(self):
        current = self._mi_browser.currentItem()
        if not current: return
        name = current.data(Qt.UserRole)
        if not name: return
        self._add_magic_item_by_name(name)

    def _open_enchant_dialog(self, kind: str, bonus: int):
        """
        Show a dialog letting the player choose which of their OWN nonmagical
        weapons/armor to enchant with a +bonus magic property, or — for
        shields — simply confirm adding the bonus to their shield.
        Updates equipped_weapons / armor_worn / shield_magic_bonus directly,
        and adds a tracking entry to the magic items list.
        """
        from dnd_app.core.magic_items import parse_magic_suffix

        if kind == "Shield":
            # No item to choose — shields are a single binary slot.
            has_shield = bool(self.char.get("shield", False))
            msg = (f"Add a +{bonus} enchantment to your equipped shield?"
                   if has_shield else
                   f"You don't currently have a shield equipped.\n"
                   f"Equip a +{bonus} magic shield now?")
            reply = QMessageBox.question(
                self, f"+{bonus} Shield", msg,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply != QMessageBox.Yes:
                return
            self.char["shield"] = True
            self.char["shield_magic_bonus"] = max(bonus, self.char.get("shield_magic_bonus", 0))
            item_name = f"Shield +{bonus}"
            items = self.char.setdefault("magic_items", [])
            if not any((i.get("name") if isinstance(i,dict) else i) == item_name for i in items):
                items.append({"name": item_name, "attunement": False,
                              "equipped": True, "notes": ""})
            self.ctrl.refresh(); self._refresh_combat(); self._refresh_magic_items()
            self._mark_dirty()
            return

        # ── Weapon / Armor: build a pool of the character's OWN candidate items ─
        if kind == "Weapon":
            equipped_list = self.char.get("equipped_weapons", [])
            owned_names = {e.get("name","") for e in self.char.get("equipment", [])
                            if isinstance(e, dict)}
            from dnd_app.data.items import ALL_WEAPONS
            valid_names = {w[0] for w in ALL_WEAPONS}
        else:  # Armor
            cur_armor = self.char.get("armor_worn", "No Armor")
            equipped_list = [cur_armor] if cur_armor not in ("No Armor",) else []
            owned_names = {e.get("name","") for e in self.char.get("equipment", [])
                            if isinstance(e, dict)}
            from dnd_app.data.items import ARMOR
            valid_names = {a[0] for a in ARMOR if a[0] not in ("No Armor","Mage Armor (spell)")}

        # Candidates: currently equipped (not already magical) first, then
        # owned-but-unequipped items of the right type, deduplicated.
        candidates = []
        seen = set()
        for n in equipped_list:
            base, existing_bonus = parse_magic_suffix(n)
            if base in valid_names and base not in seen:
                candidates.append((base, True, existing_bonus)); seen.add(base)
        for n in owned_names:
            base, existing_bonus = parse_magic_suffix(n)
            if base in valid_names and base not in seen:
                candidates.append((base, False, existing_bonus)); seen.add(base)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Enchant {kind} (+{bonus})")
        dlg.setMinimumWidth(380)
        lay = QVBoxLayout(dlg); lay.setSpacing(10)

        if candidates:
            lay.addWidget(_lbl(
                f"Choose which {kind.lower()} receives the +{bonus} enchantment:",
                TEXT2, FS_SMALL))
            list_w = QListWidget()
            list_w.setStyleSheet(
                f"QListWidget{{background:{SURF2};border:1px solid {BORDER};"
                f"border-radius:6px;color:{TEXT};}}"
                f"QListWidget::item{{padding:6px;}}"
                f"QListWidget::item:selected{{background:{qa(AMBER,0x44)};}}"
            )
            for base, is_equipped, existing_bonus in sorted(candidates, key=lambda x: (-x[1], x[0])):
                tag = "  (equipped)" if is_equipped else "  (owned)"
                if existing_bonus:
                    tag += f"  — currently +{existing_bonus}"
                li = QListWidgetItem(f"{base}{tag}")
                li.setData(Qt.UserRole, base)
                list_w.addItem(li)
            list_w.setCurrentRow(0)
            lay.addWidget(list_w)
        else:
            list_w = None
            lay.addWidget(_lbl(
                f"You don't currently have any nonmagical {kind.lower()} equipped "
                f"or in your inventory. Type the {kind.lower()} name to enchant:",
                TEXT2, FS_SMALL, wrap=True))
            name_edit = QLineEdit()
            name_edit.setPlaceholderText(f"e.g. {'Longsword' if kind=='Weapon' else 'Studded Leather'}")
            lay.addWidget(name_edit)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        if dlg.exec() != QDialog.Accepted:
            return

        if list_w is not None:
            cur = list_w.currentItem()
            if not cur: return
            base_name = cur.data(Qt.UserRole)
        else:
            base_name = name_edit.text().strip()
            if not base_name or base_name not in valid_names:
                QMessageBox.warning(self, "Unknown Item",
                    f"'{base_name}' isn't a recognized {kind.lower()} name.")
                return

        enchanted_name = f"{base_name} +{bonus}"

        if kind == "Weapon":
            equipped = self.char.setdefault("equipped_weapons", [])
            # Replace a matching unenchanted (or differently-enchanted) entry
            for i, n in enumerate(equipped):
                if parse_magic_suffix(n)[0] == base_name:
                    equipped[i] = enchanted_name
                    break
            else:
                equipped.append(enchanted_name)
            self._refresh_combat_weapons()
        else:  # Armor
            self.char["armor_worn"] = enchanted_name

        # Track in the magic items list for visibility/removal (no attunement
        # needed — +1/+2/+3 weapons and armor work automatically while worn).
        items = self.char.setdefault("magic_items", [])
        if not any((i.get("name") if isinstance(i,dict) else i) == enchanted_name for i in items):
            items.append({"name": enchanted_name, "attunement": False,
                          "equipped": True, "notes": ""})

        self.ctrl.refresh(); self._refresh_combat(); self._refresh_magic_items()
        if hasattr(self, "_refresh_gear_equipment"): self._refresh_gear_equipment()
        self._mark_dirty()

    def _add_magic_item_by_name(self, name: str):
        if not name: return
        # Generic "+N Weapon/Armor/Shield" — open the enchant dialog instead of
        # adding a generic catalog entry. This lets the player apply the bonus
        # directly to a weapon/armor/shield they already own.
        import re as _re
        plus_m = _re.match(r'^([+][123]) (Weapon|Armor|Shield)$', name)
        if plus_m:
            bonus_str, kind = plus_m.groups()
            bonus = int(bonus_str[1])
            self._open_enchant_dialog(kind, bonus)
            return
        from dnd_app.data.magic_items import get_magic_item
        catalog = get_magic_item(name) or {}
        needs_attune = bool(catalog.get("attunement"))
        itype = catalog.get("type","")
        # True consumables (Potions/Scrolls) → gear/equipment list
        is_consumable = itype in ("Potion","Scroll") or "potion" in name.lower() or "scroll" in name.lower()
        if is_consumable:
            eq = self.char.setdefault("equipment", [])
            # A generic "Spell Scroll (Nth level)" catalog entry doesn't say
            # which spell is actually written on this copy -- prompt for one
            # so the scroll becomes a concrete item (e.g. "Spell Scroll (3rd
            # level) — Fireball") instead of a vague inert placeholder.
            import re as _re
            m = _re.match(r'^Spell Scroll \((Cantrip|\d+(?:st|nd|rd|th) level)\)$', name)
            if m:
                from dnd_app.data.spells import SPELLS_BY_LEVEL
                lvl = 0 if m.group(1) == "Cantrip" else int(_re.match(r'\d+', m.group(1)).group())
                choices = sorted(s["name"] for s in SPELLS_BY_LEVEL.get(lvl, []))
                if choices:
                    spell_choice, ok = QInputDialog.getItem(
                        self, "Spell Scroll", f"Which spell is inscribed on this {name}?",
                        choices, 0, False)
                    if ok and spell_choice:
                        name = f"{name} — {spell_choice}"
            existing = next((e for e in eq if isinstance(e,dict) and e.get("name")==name), None)
            if existing:
                existing["qty"] = existing.get("qty", 1) + 1   # stack
            else:
                eq.append({"name": name, "qty": 1, "weight": 0.5, "notes": "",
                           "magic": True, "rarity": catalog.get("rarity",""),
                           "desc": catalog.get("desc","")})
            self._refresh_gear_equipment(); self._mark_dirty(); return
        # All other magic items (attunable or not) → magic items section
        items = self.char.setdefault("magic_items", [])
        # Deduplicate: don't add if already present
        existing_names = {(i.get("name") if isinstance(i,dict) else i) for i in items}
        if name not in existing_names:
            items.append({"name": name, "attunement": needs_attune,
                          "equipped": True, "notes": ""})
        self.ctrl.refresh()
        self._refresh_magic_items()
        self._mark_dirty()

    def _filter_magic_item_combo(self, text: str):
        pass  # legacy — replaced by _populate_magic_browser

    def _add_magic_item(self):
        pass  # legacy — replaced by _add_magic_from_browser

    def _refresh_magic_items(self):
        from PySide6.QtGui import QColor
        art_lvl_for_max = class_levels(self.char).get("Artificer", 0)
        att_max_display = 6 if art_lvl_for_max >= 18 else 5 if art_lvl_for_max >= 14 else 4 if art_lvl_for_max >= 10 else 3
        if "Mystic Conflux" in self.char.get("feats", []):
            att_max_display = max(att_max_display, 4)
        if hasattr(self, "_mi_title_lbl"):
            self._mi_title_lbl.setText(f"✨  MAGIC ITEMS  (max {att_max_display} attuned)")
        self._magic_items_tree.clear()
        self._magic_item_rows = []
        attuned = set(self.char.get("attuned_items", []))
        owned = self.char.get("magic_items", [])
        if not owned:
            placeholder = QTreeWidgetItem(["No magic items. Browse & add →", "", "", "", ""])
            placeholder.setForeground(0, QColor(TEXT3))
            self._magic_items_tree.addTopLevelItem(placeholder)
            return

        from dnd_app.data.magic_items import get_magic_item, get_item_effect as _gie
        for entry in owned:
            if isinstance(entry, str):
                entry = {"name": entry, "attunement": False, "equipped": True, "notes": ""}
            name = entry.get("name","?")
            catalog = get_magic_item(name) or {}
            rarity  = catalog.get("rarity","")
            rarity_color = self._RARITY_COLORS.get(rarity, TEXT2)
            needs_attune = bool(catalog.get("attunement"))
            itype_local = catalog.get("type","Wondrous")
            desc = catalog.get("desc","")

            name_txt = name
            if has_item_effect(name):
                name_txt = f"⚡ {name}"
            item = QTreeWidgetItem([name_txt, rarity, "", "", ""])
            item.setForeground(0, QColor(TEXT))
            item.setForeground(1, QColor(rarity_color))

            tip_parts = [f"<b>{name}</b>"]
            if rarity: tip_parts.append(f"<i>{rarity} {itype_local}</i>")
            if needs_attune: tip_parts.append("<b>Requires Attunement</b>")
            if desc: tip_parts.append(desc[:600] + ("…" if len(desc)>600 else ""))
            tip = "<br>".join(tip_parts)
            item.setToolTip(0, tip)
            item.setData(0, Qt.UserRole, (name, entry, tip))

            self._magic_items_tree.addTopLevelItem(item)

            # Items that grant resistance to a damage type fixed at creation
            # (Ring/Armor of Resistance, Absorbing Tattoo, Orb of Shielding)
            # need the player to pick which type their copy is. Shown as an
            # extra combo row directly beneath the item when applicable.
            _eff = _gie(name)
            if isinstance(_eff, dict) and _eff.get("type") == "resistance_choice":
                dmg_combo = QComboBox()
                dmg_combo.addItem("— choose damage type —", None)
                for dt in _eff.get("pool", []):
                    dmg_combo.addItem(dt, dt)
                current = self.char.get("_choices", {}).get(f"item_dmgtype_{name}", [])
                if current:
                    idx = dmg_combo.findData(current[0])
                    if idx >= 0: dmg_combo.setCurrentIndex(idx)
                dmg_combo.setStyleSheet(f"QComboBox{{background:{SURF3};color:{TEXT};font-size:{FS_TINY}px;"
                                          f"border:1px solid {BORDER};border-radius:4px;padding:1px 4px;}}")
                dmg_combo.currentIndexChanged.connect(
                    lambda idx, n=name, cb=dmg_combo: self._set_item_damage_type(n, cb.currentData()))
                self._magic_items_tree.setItemWidget(item, 0, dmg_combo)

            # Attuned checkbox (col 2) — only shown for items that
            # actually need attunement, rather than shown-but-disabled
            # for every item regardless of whether attunement applies.
            if needs_attune:
                att_cb = QCheckBox()
                att_cb.setToolTip("Requires Attunement")
                att_cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                                      f"border:1px solid {PURP2};background:{SURF2};}}"
                                      f"QCheckBox::indicator:checked{{background:{PURP2};}}")
                att_cb.blockSignals(True); att_cb.setChecked(name in attuned); att_cb.blockSignals(False)
                att_cb.stateChanged.connect(lambda s,n=name: self._toggle_attunement(n, bool(s)))
                self._magic_items_tree.setItemWidget(item, 2, att_cb)

            # Equipped checkbox (col 3)
            eq_cb = QCheckBox()
            eq_cb.setToolTip("Equipped/worn/carried")
            eq_cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                                 f"border:1px solid {TEAL};background:{SURF2};}}"
                                 f"QCheckBox::indicator:checked{{background:{TEAL};}}")
            eq_cb.blockSignals(True); eq_cb.setChecked(entry.get("equipped",True)); eq_cb.blockSignals(False)
            eq_cb.stateChanged.connect(lambda s,n=name: self._toggle_equipped(n, bool(s)))
            self._magic_items_tree.setItemWidget(item, 3, eq_cb)

            # Remove button (col 4)
            rm = QPushButton("✕"); rm.setFixedSize(20,20)
            rm.setStyleSheet(f"QPushButton{{background:{qa(CRIMSON,0x44)};border:1px solid {CRIMSON};"
                              f"border-radius:4px;color:{CRIM2};font-size:11px;}}"
                              f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
            rm.clicked.connect(lambda checked=False, n=name: self._remove_magic_item(n))
            self._magic_items_tree.setItemWidget(item, 4, rm)
            self._magic_item_rows.append(item)

        self._magic_items_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        try:
            self._magic_items_tree.customContextMenuRequested.disconnect()
        except Exception:
            pass
        def _mi_ctx_menu(pos):
            it = self._magic_items_tree.itemAt(pos)
            if not it: return
            data = it.data(0, Qt.UserRole)
            if not data: return
            _name, _entry, _tip = data
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self._magic_items_tree)
            act = menu.addAction(f"📖  Details: {_name[:36]}")
            act.triggered.connect(lambda: QMessageBox.information(self, _name, _tip))
            from dnd_app.core.magic_items import ABILITY_SCORE_MANUALS
            if _name in ABILITY_SCORE_MANUALS:
                study_act = menu.addAction(f"✨  Study {_name[:36]} (48 hrs over 6 days)")
                study_act.triggered.connect(lambda checked=False, n=_name: self._study_manual(n))
            rm_act = menu.addAction(f"✕  Remove {_name[:36]}")
            rm_act.triggered.connect(lambda: self._remove_magic_item(_name))
            menu.exec(self._magic_items_tree.viewport().mapToGlobal(pos))
        self._magic_items_tree.customContextMenuRequested.connect(_mi_ctx_menu)

    def _set_item_damage_type(self, item_name: str, dmg_type):
        """Store which damage type a resistance-choice item (Ring/Armor of
        Resistance, Absorbing Tattoo, Orb of Shielding) grants for THIS
        character, then recompute so the resistance actually applies."""
        choices = self.char.setdefault("_choices", {})
        key = f"item_dmgtype_{item_name}"
        if dmg_type:
            choices[key] = [dmg_type]
        else:
            choices.pop(key, None)
        self.ctrl.refresh()
        self._refresh_combat()

    def _toggle_attunement(self, name: str, on: bool):
        att = self.char.setdefault("attuned_items", [])
        if on:
            if name not in att:
                from dnd_app.core.magic_items import attunement_prereq_met
                met, reason = attunement_prereq_met(self.char, name)
                if not met:
                    QMessageBox.warning(self, "Attunement",
                        f"{name} requires attunement by {reason} — this character doesn't qualify.\n\n"
                        "(Disable this check under Optional Rules if your table allows it anyway.)")
                    self._refresh_magic_items(); return
                # Artificer attunement scaling: 4 at 10th (Magic Item
                # Adept), 5 at 14th (Magic Item Savant), 6 at 18th (Magic
                # Item Master). Previously only Adept's 4 was handled.
                from dnd_app.core.calculator import class_levels as _cl
                art_lvl = _cl(self.char).get("Artificer", 0)
                att_max = 6 if art_lvl >= 18 else 5 if art_lvl >= 14 else 4 if art_lvl >= 10 else 3
                if "Mystic Conflux" in self.char.get("feats", []):
                    att_max = max(att_max, 4)
                if len(att) >= att_max:
                    QMessageBox.warning(self, "Attunement",
                        f"Maximum {att_max} attuned items (PHB p.138).")
                    self._refresh_magic_items(); return
                att.append(name)
        else:
            if name in att: att.remove(name)
        for entry in self.char.get("magic_items",[]):
            if isinstance(entry,dict) and entry.get("name")==name:
                entry["attunement"] = on
        # Deferred: self.ctrl.refresh() -> _on_char_updated() ->
        # _refresh_magic_items() clears and rebuilds the whole tree,
        # including this very checkbox — destroying it while its own
        # stateChanged signal is still on the call stack is a Qt
        # anti-pattern. Running it on the next event loop tick instead
        # lets this signal handler finish cleanly first.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.ctrl.refresh)

    def _toggle_equipped(self, name: str, on: bool):
        for entry in self.char.get("magic_items",[]):
            if isinstance(entry,dict) and entry.get("name")==name:
                entry["equipped"] = on
        # Syncs equipped_weapons/armor_worn/shield in addition to the
        # item's own bookkeeping flag, so a magic weapon like Armblade
        # or Sun Blade shows up as an attackable weapon in the Combat
        # tab as soon as it's checked "Equipped".
        from dnd_app.data.magic_items import get_magic_item
        catalog = get_magic_item(name) or {}
        itype = catalog.get("type", "")
        if itype == "Weapon":
            equipped_wpns = self.char.setdefault("equipped_weapons", [])
            if on:
                if name not in equipped_wpns:
                    equipped_wpns.append(name)
            else:
                if name in equipped_wpns:
                    equipped_wpns.remove(name)
        elif itype == "Armor":
            if on:
                self.char["armor_worn"] = name
            elif self.char.get("armor_worn") == name:
                self.char["armor_worn"] = "No Armor"
        elif itype == "Shield":
            self.char["shield"] = on
        # Same deferred-refresh fix as _toggle_attunement above, and for
        # the same reason — this checkbox also lives in the tree that
        # _refresh_magic_items() clears and rebuilds.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.ctrl.refresh)
        self._mark_dirty()

    def _remove_magic_item(self, name: str):
        from dnd_app.core.magic_items import parse_magic_suffix
        self.char["magic_items"] = [i for i in self.char.get("magic_items",[])
            if (i.get("name") if isinstance(i,dict) else i) != name]
        att = self.char.get("attuned_items",[])
        if name in att: att.remove(name)

        # If this was a "+N" enchantment applied to one of the player's own
        # weapon/armor/shield, revert that item back to its mundane form.
        base_name, bonus = parse_magic_suffix(name)
        if bonus:
            if name == f"Shield +{bonus}" or name.startswith("Shield +"):
                self.char["shield_magic_bonus"] = 0
            else:
                equipped = self.char.get("equipped_weapons", [])
                for i, n in enumerate(equipped):
                    if n == name:
                        equipped[i] = base_name
                        break
                if self.char.get("armor_worn", "") == name:
                    self.char["armor_worn"] = base_name
            self._refresh_combat_weapons()

        self.ctrl.refresh(); self._refresh_combat(); self._refresh_magic_items()
        if hasattr(self, "_refresh_gear_equipment"): self._refresh_gear_equipment()

    def _study_manual(self, name: str):
        """Study one of the 6 classic ability-score manuals/tomes: permanently
        raises the named ability score by 2 (real 5e rule -- no hard cap on
        this kind of magical increase) and consumes the book. Confirmed
        there was no consumption path for these at all before this --
        equip-based MAGIC_ITEM_EFFECTS can't represent a one-time permanent
        change, so this writes directly to char["abilities"]."""
        from dnd_app.core.magic_items import ABILITY_SCORE_MANUALS
        ability = ABILITY_SCORE_MANUALS.get(name)
        if not ability:
            return
        abilities = self.char.setdefault("abilities", {})
        abilities[ability] = abilities.get(ability, 10) + 2
        self._remove_magic_item(name)
        self._toast(f"✨ {name} — your {ability} score permanently increases by 2 (now {abilities[ability]})")
        self.ctrl.refresh()
        self._mark_dirty()

    def _add_equipment_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("Add Custom Item")
        lay = QVBoxLayout(dlg); lay.setSpacing(8)
        lay.addWidget(_lbl("Or browse and double-click/Add from the Equipment Browser →", TEXT3, FS_SMALL))
        name_edit = QLineEdit(); name_edit.setPlaceholderText("Item name")
        qty_spin  = QSpinBox(); qty_spin.setRange(1,99); qty_spin.setValue(1)
        row = QHBoxLayout(); row.addWidget(_lbl("Qty:",TEXT2,FS_SMALL,wrap=False)); row.addWidget(qty_spin)
        lay.addWidget(name_edit); lay.addLayout(row)
        btns = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec() and name_edit.text().strip():
            eq = self.char.setdefault("equipment",[])
            eq.append({"name":name_edit.text().strip(),"qty":qty_spin.value(),"weight":0.0,"notes":""})
            self._refresh_gear_equipment()

    def _update_weight(self):
        """Show total carried weight vs capacity."""
        if not hasattr(self,"_weight_lbl"): return
        total = sum(eq.get("weight",0)*eq.get("qty",1) for eq in self.char.get("equipment",[]))
        total += sum(eq.get("weight",0) for eq in self.char.get("magic_items",[]))
        from dnd_app.core.calculator import ability_score as _as
        str_score = _as(self.char,"STR")
        cap = str_score * 15
        push = cap * 2
        col = TEAL2 if total <= cap else (AMBER if total <= push else CRIM2)
        self._weight_lbl.setText(f"⚖  Carry: {total:.1f} / {cap} lb  (push {push} lb)")
        self._weight_lbl.setStyleSheet(f"color:{col};font-size:{FS_SMALL}px;")

    def _refresh_gear_equipment(self):
        from PySide6.QtGui import QColor
        self._gear_equip_tree.clear()

        # Build a combined list: mundane equipment PLUS owned magic items
        # (magic items appear here as read-only reference rows)
        from dnd_app.data.magic_items import get_magic_item
        items = list(self.char.get("equipment", []))
        mi_names_in_eq = {e.get("name") for e in items if e.get("magic")}
        for mi in self.char.get("magic_items", []):
            if isinstance(mi, dict):
                mname = mi.get("name","")
            else:
                mname = str(mi)
            if mname in mi_names_in_eq:
                continue   # already shown from equipment list
            cat = get_magic_item(mname)
            rarity = cat.get("rarity","") if cat else ""
            itype  = cat.get("type","Wondrous") if cat else "Wondrous"
            desc   = cat.get("desc","") if cat else ""
            items.append({
                "name": mname, "qty": 1, "weight": 0,
                "magic": True, "rarity": rarity, "type": itype, "desc": desc,
                "_mi_only": True,   # flag: shown in equipment for reference only
            })

        if not items:
            placeholder = QTreeWidgetItem(["No items — double-click from the Equipment Browser →", "", "", "", "", ""])
            placeholder.setForeground(0, QColor(TEXT3))
            self._gear_equip_tree.addTopLevelItem(placeholder)
            return

        from dnd_app.data.items import ADVENTURING_GEAR as _AG_notes
        GEAR_NOTES = {row[0]: (row[3] if len(row) > 3 else "") for row in _AG_notes}

        from dnd_app.data.items import WEAPON_DICT, ARMOR_DICT
        for eq in items:
            name = eq.get("name","?")
            is_magic  = bool(eq.get("magic"))
            _mi_type  = str(eq.get("type","")) if is_magic else ""
            is_weapon = (name in WEAPON_DICT or any(w[0]==name for w in ALL_WEAPONS)
                         or _mi_type == "Weapon")
            is_armor  = ((name in ARMOR_DICT and name not in ("No Armor","Mage Armor (spell)"))
                         or _mi_type == "Armor")
            rarity_color = self._RARITY_COLORS.get(eq.get("rarity",""), TEXT2) if is_magic else None
            accent = rarity_color if rarity_color else (
                TEAL2 if is_weapon else (GOLD2 if is_armor else TEXT2))
            icon = ("⚔" if is_weapon else ("🛡" if is_armor else ("✨" if is_magic else "📦")))

            wt = eq.get("weight",0)
            total_wt = wt * eq.get("qty",1)
            wt_str = f"{total_wt:.1f}" if total_wt else "—"
            cost = eq.get("cost",0)
            total_cost = cost * eq.get("qty",1)
            cost_str = f"{total_cost:g} gp" if total_cost else ("—" if not is_magic else "")

            item = QTreeWidgetItem([f"{icon}  {name}", "", "", wt_str, cost_str, ""])
            is_shield = name in ARMOR_DICT and ARMOR_DICT[name].get("type") == "shield"
            item.setForeground(0, QColor(accent))
            item.setForeground(3, QColor(TEXT3))
            item.setForeground(4, QColor(TEXT3))

            # Tooltip with full item description
            if is_magic and eq.get("desc"):
                tip = f"<b>{name}</b><br><i>{eq.get('rarity','')} {eq.get('type','')}</i><br><br>{self._format_multi_para(eq.get('desc',''))}"
                item.setToolTip(0, tip)
            elif is_weapon and name in WEAPON_DICT:
                w = WEAPON_DICT[name]
                wprops = ", ".join(str(p) for p in w.get("properties",[]))
                item.setToolTip(0, f"<b>{name}</b>  {w.get('category','')}<br>"
                                    f"Damage: {w.get('damage','?')} {w.get('dmg_type','')}<br>{wprops}")
            elif is_armor and name in ARMOR_DICT:
                a = ARMOR_DICT[name]
                dex_note = "no DEX limit" if a.get("dex_cap") is None else f"max +{a['dex_cap']} DEX"
                item.setToolTip(0, f"<b>{name}</b>  {a.get('type','').title()} armor<br>"
                                    f"AC {a.get('ac','?')} ({dex_note})"
                                    + (", stealth disadvantage" if a.get("stealth") else "")
                                    + (f", requires {a['str_req']} STR" if a.get("str_req") else ""))
            else:
                # General adventuring gear (rope, torches, rations,
                # tools, and the majority of a real inventory) always
                # shows at least weight/cost, matching the standard
                # already used for the reference browser, even for
                # plain flavor items with no special mechanic text
                # (Abacus, Bedroll, Rope).
                notes = GEAR_NOTES.get(name, "")
                base = f"<b>{name}</b>"
                if notes:
                    base += f"<br>{notes}"
                if wt_str != "—" or cost_str not in ("", "—"):
                    base += f"<br>{wt_str} lb \u2014 {cost_str}" if wt_str != "—" else f"<br>{cost_str}"
                item.setToolTip(0, base)

            self._gear_equip_tree.addTopLevelItem(item)

            # Equip toggle (col 1) — only for weapons/armor
            if is_weapon:
                eq_cb = QCheckBox(); eq_cb.setToolTip("Equip to combat")
                equipped = self.char.get("equipped_weapons",[])
                eq_cb.setChecked(name in equipped)
                eq_cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                                     f"border:1px solid {TEAL};background:{SURF2};}}"
                                     f"QCheckBox::indicator:checked{{background:{TEAL};border-color:{TEAL2};}}")
                eq_cb.stateChanged.connect(lambda s,n=name: self._toggle_weapon_equipped(n, bool(s)))
                self._gear_equip_tree.setItemWidget(item, 1, eq_cb)
            elif is_armor:
                eq_cb = QCheckBox(); eq_cb.setToolTip("Wear this armor")
                eq_cb.setChecked(self.char.get("armor_worn","") == name)
                eq_cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                                     f"border:1px solid {GOLD};background:{SURF2};}}"
                                     f"QCheckBox::indicator:checked{{background:{GOLD};border-color:{GOLD2};}}")
                eq_cb.stateChanged.connect(lambda s,n=name: self._toggle_armor_worn(n, bool(s)))
                self._gear_equip_tree.setItemWidget(item, 1, eq_cb)

            # Quantity spin (col 2)
            qty_spin = QSpinBox()
            qty_spin.setRange(0, 9999); qty_spin.setValue(eq.get("qty",1))
            qty_spin.setAlignment(Qt.AlignCenter)
            qty_spin.setStyleSheet(
                f"QSpinBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:4px;"
                f"color:{GOLD2 if eq.get('qty',1)>1 else TEXT};font-size:{FS_TINY}px;font-weight:700;padding:0 2px;}}"
                f"QSpinBox::up-button,QSpinBox::down-button{{width:12px;background:{BORDER};}}")
            def _qty_changed(v, eq_ref=eq, n=name):
                eq_ref["qty"] = v
                if v == 0:
                    self._remove_equipment(n)
                    return
                self._update_weight(); self._mark_dirty()
            qty_spin.valueChanged.connect(_qty_changed)
            self._gear_equip_tree.setItemWidget(item, 2, qty_spin)

            # Remove / Info button (col 4)
            if eq.get("_mi_only"):
                info_btn = QPushButton("ℹ"); info_btn.setFixedSize(20,20)
                info_btn.setStyleSheet(
                    f"QPushButton{{background:transparent;border:none;color:{AMBE2};"
                    f"font-size:11px;border-radius:3px;}}"
                    f"QPushButton:hover{{background:{qa(AMBER,0x44)};}}")
                tip_html = (f"<b>{name}</b><br><i>{eq.get('rarity','')} "
                            f"{eq.get('type','')}</i><br><br>{self._format_multi_para(eq.get('desc',''))}")
                info_btn.clicked.connect(lambda checked=False, t=tip_html, n=name:
                    QMessageBox.information(self, n, t))
                self._gear_equip_tree.setItemWidget(item, 5, info_btn)
            else:
                rm = QPushButton("✕"); rm.setFixedSize(20,20)
                rm.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT3};"
                                 f"font-size:10px;border-radius:3px;}}"
                                 f"QPushButton:hover{{background:{CRIMSON};color:white;}}")
                rm.clicked.connect(lambda checked=False,n=name: self._remove_equipment(n))
                self._gear_equip_tree.setItemWidget(item, 5, rm)

            # Right-click context menu for full details (magic items) / removal
            # is handled at the tree level below (customContextMenuRequested),
            # since a per-item mousePressEvent wouldn't fire reliably when a
            # cell widget (checkbox/spinbox/button) is under the cursor.
            item.setData(0, Qt.UserRole, (name, eq, is_magic, is_weapon, is_armor, is_shield))

        self._gear_equip_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        try:
            self._gear_equip_tree.customContextMenuRequested.disconnect()
        except Exception:
            pass
        def _tree_ctx_menu(pos):
            item = self._gear_equip_tree.itemAt(pos)
            if not item: return
            data = item.data(0, Qt.UserRole)
            if not data: return
            _name, _eq, _is_magic, _is_weapon, _is_armor, _is_shield = data
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self._gear_equip_tree)
            if _is_magic:
                tip = (f"<b>{_name}</b><br><i>{_eq.get('rarity','')} "
                       f"{_eq.get('type','')}</i><br><br>{self._format_multi_para(_eq.get('desc',''))}")
                act = menu.addAction(f"📖  Details: {_name[:36]}")
                act.triggered.connect(lambda: QMessageBox.information(self, _name, tip))
            # "Infuse this item" — only for weapons/armor/shields, only
            # if the character actually knows an applicable Artificer
            # infusion and hasn't hit the active-infusion cap. Most
            # infusions apply to an existing mundane item the character
            # already owns, not a standalone creation.
            if not _is_magic and (_is_weapon or _is_armor or _is_shield):
                applicable = self._get_applicable_infusions(_is_weapon, _is_armor, _is_shield)
                if applicable:
                    infuse_menu = menu.addMenu(f"\u2728  Infuse {_name[:30]} with...")
                    from dnd_app.core.calculator import get_max_active_infusions
                    max_active = get_max_active_infusions(self.char)
                    active_count = len(self.char.get("active_infusions", []))
                    for inf_name in applicable:
                        act2 = infuse_menu.addAction(inf_name)
                        act2.setEnabled(active_count < max_active)
                        act2.triggered.connect(
                            lambda checked=False, n=_name, i=inf_name: self._infuse_item(n, i))
                    if active_count >= max_active:
                        full_act = infuse_menu.addAction(
                            f"(At max active infusions: {active_count}/{max_active})")
                        full_act.setEnabled(False)
            if _eq.get("type") == "Potion" or "potion" in _name.lower():
                drink_act = menu.addAction(f"🧪  Drink {_name[:36]}")
                drink_act.triggered.connect(lambda checked=False, n=_name: self._use_potion(n))
            if "scroll" in _name.lower():
                read_act = menu.addAction(f"📜  Read {_name[:36]}")
                read_act.triggered.connect(lambda checked=False, n=_name: self._use_scroll(n))
            rm_act = menu.addAction(f"✕  Remove {_name[:36]}")
            rm_act.triggered.connect(lambda: self._remove_equipment(_name))
            if _eq.get("_mi_only"):
                rm_act.setEnabled(False)
                rm_act.setText("(Manage in Magic Items list below)")
            menu.exec(self._gear_equip_tree.viewport().mapToGlobal(pos))
        self._gear_equip_tree.customContextMenuRequested.connect(_tree_ctx_menu)

    def _get_applicable_infusions(self, is_weapon, is_armor, is_shield):
        """Returns the names of infusions this character knows that apply
        to an item of this type (weapon/armor/shield), per
        ARTIFICER_INFUSION_TARGETS, and aren't already active on some
        other item."""
        from dnd_app.data.classes import ARTIFICER_INFUSION_TARGETS
        known = self.char.get("artificer_infusions", [])
        active_infusions = {a["infusion"] for a in self.char.get("active_infusions", [])}
        result = []
        for inf in known:
            base_name = inf.split(" – ")[0].strip()
            target = ARTIFICER_INFUSION_TARGETS.get(base_name)
            if target is None:
                continue
            matches = (
                (target == "weapon" and is_weapon) or
                (target == "armor" and is_armor) or
                (target == "shield" and is_shield) or
                (target == "armor_or_shield" and (is_armor or is_shield))
            )
            if matches and base_name not in active_infusions:
                result.append(base_name)
        return result

    def _infuse_item(self, item_name: str, infusion_name: str, give_away: bool = False):
        """Apply a known infusion to a specific mundane item, turning it
        magical and counting it against the active-infusion cap. Confirmed
        via research this is a genuinely separate step from learning the
        infusion — most infusions apply to an existing item the character
        owns, not a standalone creation. If give_away is True, the
        infusion still counts against the cap but the item isn't added to
        (or is removed from) this character's own inventory, matching the
        real rule that lets an Artificer forgo attunement so someone else
        can use the infused item."""
        active = self.char.setdefault("active_infusions", [])
        from dnd_app.core.calculator import get_max_active_infusions
        max_active = get_max_active_infusions(self.char)
        if len(active) >= max_active:
            QMessageBox.warning(self, "Infusion Limit Reached",
                                 f"You can only have {max_active} infusions active at once.")
            return
        active.append({"infusion": infusion_name, "target_item": item_name if not give_away else None,
                       "given_away": give_away})
        if not give_away:
            # Two cases: (1) enchanting an existing mundane item already
            # in equipment — mark it magical in place; (2) a standalone
            # creation (Replicate Magic Item's chosen item, Homunculus
            # Servant, etc.) with no existing equipment entry — add it
            # as a proper magic_items entry instead.
            found = False
            for eq in self.char.get("equipment", []):
                if eq.get("name") == item_name:
                    eq["magic"] = True
                    eq["infused_with"] = infusion_name
                    found = True
                    break
            # Homunculus Servant creates a companion CREATURE, already
            # correctly detected purely from this active_infusions entry
            # (see get_available_companions) — filing it as a magic_items
            # entry too would show it twice: once correctly as a
            # companion, once incorrectly as a piece of gear.
            if not found and infusion_name != "Homunculus Servant":
                items = self.char.setdefault("magic_items", [])
                if not any((i.get("name") if isinstance(i, dict) else i) == item_name for i in items):
                    items.append({"name": item_name, "attunement": False,
                                  "equipped": True, "notes": f"Artificer infusion: {infusion_name}"})
            self._toast(f"\u2728 {item_name} infused with {infusion_name}")
        else:
            self._toast(f"\u2728 {infusion_name} infused and given to another character "
                        f"(counts against your active infusions, not in your own inventory)")
        self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._mark_dirty()

    def _remove_equipment(self, name: str):
        # Don't try to remove _mi_only (magic-item-only) entries — they aren't
        # in the real equipment list; they're injected for display only.
        real_eq = self.char.get("equipment", [])
        if not any(e.get("name") == name for e in real_eq):
            return   # nothing to remove (was a display-only magic item row)
        self.char["equipment"] = [e for e in real_eq if e.get("name") != name]
        # Also un-equip from combat if equipped
        if name in self.char.get("equipped_weapons",[]):
            self.char["equipped_weapons"].remove(name)
        if self.char.get("armor_worn","") == name:
            self.char["armor_worn"] = "No Armor"
        self._refresh_gear_equipment()
        self._refresh_combat(); self._mark_dirty()

    def _use_potion(self, name: str):
        """Drink one dose of a potion: consumes it from inventory and, if
        it has a lasting effect (EFFECT_TABLE entry), adds it to
        active_effects so it's visible on the combat page immediately —
        the same list Rage/Haste/etc. already use — and can be removed by
        hand or fades automatically on a short/long rest per its
        duration_category. Confirmed there was previously no consumption
        path for potions at all: they only ever sat in the equipment list
        as an inert line item with a quantity."""
        eq = self.char.get("equipment", [])
        entry = next((e for e in eq if e.get("name") == name), None)
        if not entry:
            return
        entry["qty"] = entry.get("qty", 1) - 1
        if entry["qty"] <= 0:
            self.char["equipment"] = [e for e in eq if e.get("name") != name]

        from dnd_app.core.effects import EFFECT_TABLE, INSTANT_POTION_EFFECTS
        instant = INSTANT_POTION_EFFECTS.get(name)
        if instant:
            msgs = []
            if "heal_dice" in instant:
                count, sides, bonus = instant["heal_dice"]
                rolled = sum(random.randint(1, sides) for _ in range(count)) + bonus
                mx = self.char.get("max_hp", 0)
                cur = self.char.get("current_hp", 0)
                self.char["current_hp"] = min(mx, cur + rolled)
                msgs.append(f"healed {rolled} HP")
            if "damage_dice" in instant:
                count, sides, bonus = instant["damage_dice"]
                rolled = sum(random.randint(1, sides) for _ in range(count)) + bonus
                self.char["current_hp"] = max(0, self.char.get("current_hp", 0) - rolled)
                dtype = instant.get("damage_type", "")
                msgs.append(f"took {rolled} {dtype} damage".replace("  ", " "))
            if "add_condition" in instant:
                conds = self.char.setdefault("conditions", [])
                if instant["add_condition"] not in conds:
                    conds.append(instant["add_condition"])
                msgs.append(f"gained {instant['add_condition']}")
            if "cure_conditions" in instant:
                conds = self.char.get("conditions", [])
                removed = [c for c in instant["cure_conditions"] if c in conds]
                self.char["conditions"] = [c for c in conds if c not in instant["cure_conditions"]]
                if removed:
                    msgs.append(f"cured {', '.join(removed)}")
            summary = "; ".join(msgs) if msgs else instant.get("cure_note", "used")
            self._toast(f"🧪 {name} — {summary}")
        else:
            info = EFFECT_TABLE.get(name, {})
            if info:
                fx = self.char.setdefault("active_effects", [])
                if name not in fx:
                    fx.append(name)
                    self._toast(f"🧪 {name} — active (see Effects tab)")
                else:
                    self._toast(f"🧪 {name} — already active")
            else:
                self._toast(f"🧪 Drank {name}")

        self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._refresh_effects_list()
        self._apply_turn_state()
        self._mark_dirty()

    def _use_scroll(self, name: str):
        """Read one scroll: consumes it from inventory and, if it has a
        lasting effect (EFFECT_TABLE entry, e.g. the Scroll of Protection
        family), adds it to active_effects the same way potions do.
        Generic "Spell Scroll (Nth level)" entries don't record which
        specific spell is written on this copy, so reading one just
        confirms the scroll was used rather than auto-applying a spell
        effect — casting any known spell already works the same way
        everywhere else in this app (no spell has automatic mechanical
        application from a spellbook either)."""
        eq = self.char.get("equipment", [])
        entry = next((e for e in eq if e.get("name") == name), None)
        if not entry:
            return
        entry["qty"] = entry.get("qty", 1) - 1
        if entry["qty"] <= 0:
            self.char["equipment"] = [e for e in eq if e.get("name") != name]

        from dnd_app.core.effects import EFFECT_TABLE
        info = EFFECT_TABLE.get(name, {})
        if info:
            fx = self.char.setdefault("active_effects", [])
            if name not in fx:
                fx.append(name)
                self._toast(f"📜 {name} — active (see Effects tab)")
            else:
                self._toast(f"📜 {name} — already active")
        else:
            self._toast(f"📜 Read {name}")

        self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._refresh_effects_list()
        self._apply_turn_state()
        self._mark_dirty()

    def _toggle_weapon_equipped(self, name: str, equip: bool):
        from dnd_app.data.items import WEAPON_DICT
        from dnd_app.core.magic_items import parse_magic_suffix
        equipped = self.char.setdefault("equipped_weapons", [])
        if not equip:
            if name in equipped: equipped.remove(name)
            self._refresh_combat_weapons(); self._mark_dirty(); return
        # Already equipped? Still enforce shield/conflict rules
        already_equipped = name in equipped

        # Check for conflicts (use the base name for property lookups —
        # a magic weapon like "Longsword +1" shares the base weapon's properties)
        _base_name, _ = parse_magic_suffix(name)
        w = WEAPON_DICT.get(_base_name)
        props = w.get('properties', []) if isinstance(w, dict) else [str(p) for p in (w[6] if w and len(w)>6 else [])]
        is_two_handed  = "Two-handed" in props
        is_light       = "Light" in props
        has_dual_wielder = "Dual Wielder" in self.char.get("feats",[])

        # Resolve conflicts
        conflicts = []
        shield_on  = bool(self.char.get("shield", False))
        current_wpns = list(equipped)  # copy

        if is_two_handed:
            # Two-handed clears everything else + shield
            conflicts = current_wpns[:]
            if shield_on:
                self.char["shield"] = False  # Can't hold 2H + shield (PHB p.147)
        elif shield_on:
            # Sword + shield: can hold one one-handed weapon. Remove any existing if already one there
            if len([w2 for w2 in current_wpns if w2 != name]) >= 1:
                # Already holding a weapon with shield — replace it
                conflicts = current_wpns[:]
        else:
            # No shield: can hold 2 light weapons, or 1 non-light, or 2 with Dual Wielder
            if is_light or has_dual_wielder:
                max_wep = 2
            else:
                max_wep = 1
            # Also check if current weapons are two-handed
            for cw in current_wpns:
                cw_base, _ = parse_magic_suffix(cw)
                cw_data = WEAPON_DICT.get(cw_base)
                cw_props = cw_data.get("properties",[]) if isinstance(cw_data,dict) else []
                if "Two-handed" in cw_props:
                    conflicts.append(cw)  # can't add anything to a two-handed grip
            if not conflicts and len([w2 for w2 in current_wpns if w2!=name]) >= max_wep:
                # Too many — unequip oldest
                while len([w2 for w2 in equipped if w2!=name]) >= max_wep:
                    equipped.remove(equipped[0])

        for c in conflicts:
            if c in equipped: equipped.remove(c)

        if name not in equipped:
            equipped.append(name)
        self._refresh_combat_weapons()
        update_all(self.char); self.ctrl.refresh()
        if hasattr(self,"_update_weight"): self._update_weight()
        self._mark_dirty()

    def _toggle_armor_worn(self, name: str, wear: bool):
        if wear:
            self.char["armor_worn"] = name
        else:
            if self.char.get("armor_worn","") == name:
                self.char["armor_worn"] = "No Armor"
        update_all(self.char); self.ctrl.refresh()
        self._refresh_combat(); self._mark_dirty()

    def _populate_subclass_combo(self):
        """Rebuild subclass combo boxes in the choices tab class card."""
        from dnd_app.data.classes import CLASS_DICT
        from dnd_app.core.character import set_subclass

        # Target the class card layout in choices tab
        target = getattr(self, '_subclass_area_card', self._subclass_area)
        # Clear existing — blockSignals on all old combos before deletion
        for combo in list(self._subclass_combos.values()):
            combo.blockSignals(True)
        while target.count():
            item = target.takeAt(0)
            if item.widget():
                item.widget().blockSignals(True)
                item.widget().deleteLater()
        self._subclass_combos.clear()

        classes = self.char.get("classes", [])
        for cls_entry in classes:
            cname     = cls_entry.get("class", "")
            clvl      = cls_entry.get("level", 1)
            current   = cls_entry.get("subclass", "")
            cdata     = CLASS_DICT.get(cname, {})
            subs      = cdata.get("subclasses", [])
            sub_level = cdata.get("subclass_level", 3)

            col = QWidget()
            cl  = QVBoxLayout(col); cl.setContentsMargins(0,0,0,0); cl.setSpacing(2)
            cl.addWidget(_lbl(f"{cname} subclass:", TEXT3, FS_TINY, bold=True))

            from dnd_app.core.character import clean_subclass_name
            combo = QComboBox()
            combo.addItem("— (none chosen) —", "")
            for sub_str in subs:
                display = clean_subclass_name(sub_str)
                combo.addItem(display, display)

            # Set current — compare canonicalized on both sides so a value
            # stored with (or without) a source tag / dash summary still matches.
            current_clean = clean_subclass_name(current)
            cur_idx = next((i for i in range(combo.count())
                            if combo.itemData(i) == current_clean), 0)
            combo.setCurrentIndex(cur_idx)
            combo.setEnabled(clvl >= sub_level)
            combo.setToolTip(f"Unlocked at level {sub_level}" if clvl < sub_level
                             else f"{cname} subclass — choose your path")
            combo.setStyleSheet(
                f"QComboBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
                f"color:{TEXT};font-size:{FS_SMALL}px;padding:3px 6px;}}"
                f"QComboBox:focus{{border-color:{INDIGO};}}")

            def _on_change(idx, cn=cname, cb=combo):
                val = cb.itemData(idx) or ""
                set_subclass(self.char, cn, val)
                self._rebuild_features()
                self._refresh_stat_bar()
                self._mark_dirty()

            combo.currentIndexChanged.connect(_on_change)
            self._subclass_combos[cname] = combo
            cl.addWidget(combo)
            target.addWidget(col)

    def _refresh_hit_dice(self):
        """Rebuild hit dice spinboxes. Called only from _do_refresh_combat."""
        char = self.char
        while self._hd_layout.count():
            item = self._hd_layout.takeAt(0)
            if item.widget():  item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    si = item.layout().takeAt(0)
                    if si.widget(): si.widget().deleteLater()

        for c in char.get("classes", []):
            hd  = c.get("hit_die", 8)
            lvl = c.get("level", 1)
            hd_key  = f"d{hd}"
            hd_data = char.get("hit_dice", {}).get(hd_key, {"total": lvl, "remaining": lvl})
            col = QVBoxLayout()
            col.setSpacing(3)
            col.addWidget(_lbl(c["class"][:6], TEXT3, FS_TINY, bold=True, align=Qt.AlignCenter))
            sp = QSpinBox()
            sp.setRange(0, hd_data.get("total", lvl))
            sp.setValue(hd_data.get("remaining", lvl))
            sp.setFixedWidth(54); sp.setFixedHeight(32)
            sp.setAlignment(Qt.AlignCenter)
            sp.setStyleSheet(
                f"QSpinBox{{background:{SURF2};border:2px solid {qa(TEAL,0x66)};border-radius:6px;"
                f"font-weight:700;font-size:{FS_SMALL}px;color:{TEAL2};}}"
                f"QSpinBox::up-button,QSpinBox::down-button{{width:14px;background:{BORDER};}}")
            col.addWidget(_lbl(f"d{hd}", TEXT3, FS_TINY, align=Qt.AlignCenter))
            sp.valueChanged.connect(
                lambda v, k=hd_key, tot=hd_data.get("total", lvl):
                    self._on_hd_changed(k, v, tot))
            self._hd_layout.addLayout(col)

    def _add_hybrid_transformation_row(self):
        """Order of the Lycan's Hybrid Transformation grants a real unarmed
        attack (Predatory Strikes) that scales with level — shown as a real
        weapon row, same treatment as Monk's Martial Arts, only while the
        transformation is actually toggled active."""
        from dnd_app.core.calculator import get_prof_bonus, class_levels
        bh_lvl = class_levels(self.char).get("Blood Hunter", 0)
        if bh_lvl == 0:
            return
        die = "1d8" if bh_lvl >= 11 else "1d6"
        pb = get_prof_bonus(self.char)
        str_mod = ability_mod(self.char, "STR")
        dex_mod = ability_mod(self.char, "DEX")
        stat = "DEX" if dex_mod > str_mod else "STR"
        mod = max(str_mod, dex_mod)
        # Stalker's Prowess (7th): Improved Predatory Strikes, +1/+2/+3 to
        # attack rolls at 7th/11th/18th.
        atk_bonus = 3 if bh_lvl >= 18 else 2 if bh_lvl >= 11 else 1 if bh_lvl >= 7 else 0
        atk = sign(pb + mod + atk_bonus)
        # Feral Might: +1/+2/+3 melee damage at 3rd/11th/18th.
        dmg_bonus = 3 if bh_lvl >= 18 else 2 if bh_lvl >= 11 else 1
        dmg_mod = mod + dmg_bonus

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Unarmed Strike", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Hybrid Form", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip(f"Predatory Strikes: uses {stat}, always proficient. "
                         f"An active Crimson Rite can apply to this attack. "
                         f"You can also make one extra unarmed strike as a "
                         f"bonus action when you take the Attack action.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _atk=atk:
            self._show_breakdown_popup("Unarmed Strike (Hybrid Form) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, True, atk_bonus), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"{die}+{dmg_mod}" if dmg_mod >= 0 else f"{die}{dmg_mod}"
        rl.addWidget(_lbl(f"{dmg_display} bludgeoning or slashing", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl(f"({stat})", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Unarmed Strike (Hybrid Form)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(CRIM2,0x33)};border:1px solid {CRIM2};"
            f"border-radius:5px;color:{CRIM2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{CRIM2};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_racial_natural_weapon_row(self):
        """Racial natural weapon traits (Aarakocra Talons, Tabaxi Claws,
        Lizardfolk Bite, Naga Bite+Constrict, etc.) as real weapon rows —
        computed attack bonus, rollable damage, same treatment as Martial
        Arts / Hybrid Transformation. Always shown when applicable; these
        aren't rage- or toggle-gated, they're just part of the character.
        Some races have more than one distinct natural attack, so this
        renders one row per entry rather than assuming exactly one."""
        from dnd_app.data.items import RACIAL_NATURAL_WEAPONS
        species = self.char.get("species") or self.char.get("race", "")
        weapons = list(RACIAL_NATURAL_WEAPONS.get(species, []))
        if species == "Simic Hybrid" and "Grappling Appendages" in self.char.get("_choices", {}).get("simic_enhancement_5th", []):
            weapons.append({"name": "Grappling Appendages", "die": "1d6", "damage_type": "bludgeoning", "stat": "STR",
                             "note": "Immediately after hitting, try to grapple as a bonus action. Can't wield weapons/cast with these appendages."})
        # Dragon Hide (XGE): retractable claws, usable as natural weapons.
        if "Dragon Hide" in self.char.get("feats", []):
            weapons.append({"name": "Dragon Hide Claws", "die": "1d4", "damage_type": "slashing", "stat": "STR",
                             "note": "Retractable claws (no action to extend/retract); replaces an unarmed strike's bludgeoning damage with slashing."})
        # Touch of Death (DM reward, Dark Gift): a level-scaling necrotic bonus on an unarmed strike.
        if "Touch of Death" in self.char.get("dm_rewards", []):
            from dnd_app.core.calculator import total_level as _tl_td
            _td_lvl = _tl_td(self.char)
            _td_dice = "4d10" if _td_lvl >= 17 else "3d10" if _td_lvl >= 11 else "2d10" if _td_lvl >= 5 else "1d10"
            weapons.append({"name": "Death Touch", "die": _td_dice, "damage_type": "necrotic (flat, not STR-modified)", "stat": "STR", "no_mod": True,
                             "note": f"Action: unarmed strike — on a hit, also deals {_td_dice} necrotic (in "
                                     f"addition to the normal unarmed strike damage). Ignores resistance to "
                                     f"necrotic damage."})
        for info in weapons:
            self._add_one_natural_weapon_row(info)

    def _unarmed_strike_blocked(self) -> bool:
        """Shared guard: Wild Shape and Hybrid Transformation (Blood
        Hunter, Order of the Lycan) both replace your entire body, so no
        ordinary Unarmed Strike variant applies while either is active."""
        if self.char.get("_wildshape_active"):
            return True
        if "Hybrid Transformation" in self.char.get("active_effects", []):
            return True
        return False

    def _is_dual_wielding(self) -> bool:
        """True if 2+ distinct weapons are currently equipped (both hands
        occupied by separate weapons) — per design, Unarmed Strike isn't
        offered while dual-wielding, since neither hand is free to throw
        a punch."""
        equipped = set(self.char.get("equipped_weapons", []))
        return len(equipped) >= 2

    def _add_unarmed_fighting_row(self):
        """Unarmed Fighting style: your unarmed strike becomes a real
        attack option dealing 1d6+STR (1d8+STR with both hands
        completely free — no weapon and no shield). Replaces the base
        Unarmed Strike rather than adding to it."""
        if self._unarmed_strike_blocked() or self._is_dual_wielding():
            return
        if not any("unarmed fighting" in fs.lower() for fs in self.char.get("fighting_styles", [])):
            return
        both_hands_free = (len(self.char.get("equipped_weapons", [])) == 0
                            and not self.char.get("shield", False))
        die = "1d8" if both_hands_free else "1d6"
        self._add_one_natural_weapon_row({
            "name": "Unarmed Strike", "die": die, "damage_type": "bludgeoning", "stat": "STR",
            "note": "Unarmed Fighting fighting style. 1d8 requires both hands completely free "
                    "(no weapon, no shield)."
        })

    def _add_tavern_brawler_row(self):
        """Tavern Brawler: your unarmed strike deals 1d4 instead of the
        normal flat damage. Replaces the base Unarmed Strike, same as
        Unarmed Fighting — if a character somehow has both, Unarmed
        Fighting wins, since its die is never worse (1d6/1d8 vs 1d4)."""
        if self._unarmed_strike_blocked() or self._is_dual_wielding():
            return
        if "Tavern Brawler" not in self.char.get("feats", []):
            return
        if any("unarmed fighting" in fs.lower() for fs in self.char.get("fighting_styles", [])):
            return  # Unarmed Fighting already covers this, and is strictly better
        from dnd_app.core.calculator import get_martial_arts_die
        if get_martial_arts_die(self.char) != "\u2014":
            return  # Monk Martial Arts already covers this
        self._add_one_natural_weapon_row({
            "name": "Unarmed Strike", "die": "1d4", "damage_type": "bludgeoning", "stat": "STR",
            "note": "Tavern Brawler feat. Hitting with this (or an improvised weapon) lets you "
                    "bonus-action attempt to grapple the target."
        })

    def _add_generic_unarmed_strike_row(self):
        """Every character always has a basic Unarmed Strike available —
        per the 2024 rules: attack bonus STR mod + proficiency bonus, 1 +
        STR mod bludgeoning damage on a hit. Was previously missing
        entirely for anyone without a better option; this is only a
        fallback shown when nothing else (Monk Martial Arts, Unarmed
        Fighting, Tavern Brawler) already covers it, and is blocked under
        the same conditions as those (Wild Shape/Hybrid Transformation,
        dual-wielding two weapons)."""
        if self._unarmed_strike_blocked() or self._is_dual_wielding():
            return
        from dnd_app.core.calculator import get_martial_arts_die
        if get_martial_arts_die(self.char) != "\u2014":
            return
        if any("unarmed fighting" in fs.lower() for fs in self.char.get("fighting_styles", [])):
            return
        if "Tavern Brawler" in self.char.get("feats", []):
            return
        self._add_one_natural_weapon_row({
            "name": "Unarmed Strike", "die": "1", "damage_type": "bludgeoning", "stat": "STR",
            "note": "Basic Unarmed Strike (2024 rules): a punch, kick, headbutt, or similar blow. "
                    "Instead of damage, you can Grapple or Shove with it instead — see the Actions tab."
        })

    def _add_one_natural_weapon_row(self, info):
        pb = get_prof_bonus(self.char)
        stat = info["stat"]
        mod = ability_mod(self.char, stat)
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(TEAL2,0x14)};border:1px solid {qa(TEAL2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(info["name"], TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Natural Weapon", TEAL2, FS_TINY, bold=True, wrap=False)
        if info.get("note"):
            badge.setToolTip(info["note"])
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", TEAL2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _stat=stat, _atk=atk:
            self._show_breakdown_popup(f"{info['name']} — Attack Bonus",
                get_weapon_attack_breakdown(self.char, _stat, True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        if info.get("no_mod"):
            dmg_display = info['die']
        else:
            dmg_display = f"{info['die']}+{mod}" if mod >= 0 else f"{info['die']}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} {info['damage_type']}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl(f"({stat})", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk, _name=info["name"]):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name}\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(TEAL2,0x33)};border:1px solid {TEAL2};"
            f"border-radius:5px;color:{TEAL2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{TEAL2};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_beast_form_row(self):
        """Path of the Beast's Form of the Beast grants a real natural
        weapon (Bite/Claws/Tail) while raging, with a computed attack bonus
        and damage. Only shown while the character is actually raging AND
        actually has Path of the Beast — checking only the Rage toggle and
        the stored choice isn't enough, since choice data can persist
        after a subclass swap and shouldn't grant the weapon on its own."""
        if "Rage" not in self.char.get("active_effects", []):
            return
        from dnd_app.core.character import subclasses
        barb_sub = subclasses(self.char).get("Barbarian", "")
        if "beast" not in barb_sub.lower():
            return
        pick = self.char.get("_choices", {}).get("beast_form_3", [])
        if not pick:
            return
        pick_text = pick[0]
        animal = pick_text.split("\u2013")[0].split("-")[0].strip()
        FORMS = {
            "Bite": {"die": "1d8", "damage_type": "piercing",
                     "note": "Once/turn when you hit a target below half HP, heal PB."},
            "Claws": {"die": "1d6", "damage_type": "slashing",
                      "note": "Once/turn, make one extra claw attack as part of the same Attack action."},
            "Tail": {"die": "1d8", "damage_type": "piercing",
                     "note": "Reach 10 ft. Reaction: roll a d8 and add it to your AC against one attack."},
        }
        info = FORMS.get(animal)
        if not info:
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(animal, TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Form of the Beast", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip(info["note"])
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup(f"{animal} (Form of the Beast) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"{info['die']}+{mod}" if mod >= 0 else f"{info['die']}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} {info['damage_type']}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk, _name=animal):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name} (Form of the Beast)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(CRIM2,0x33)};border:1px solid {CRIM2};"
            f"border-radius:5px;color:{CRIM2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{CRIM2};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_battlerager_spikes_row(self):
        """Path of the Battlerager's armor spikes — a bonus-action attack
        while raging. Requires wearing spiked barbarian armor specifically,
        which doesn't exist as a tracked item in this app's magic item
        database, so this can't verify actual possession — shown whenever
        raging + this subclass, with the requirement noted in the tooltip
        rather than silently assumed."""
        if "Rage" not in self.char.get("active_effects", []):
            return
        from dnd_app.core.character import subclasses
        barb_sub = subclasses(self.char).get("Barbarian", "")
        if "battlerager" not in barb_sub.lower():
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Armor Spikes", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Battlerager Armor (Bonus Action)", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip("Requires wearing spiked barbarian armor while raging. "
                          "Also: when you grapple a creature with the Attack action "
                          "and succeed, the spikes deal it 3 piercing damage.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup("Armor Spikes (Battlerager Armor) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"1d4+{mod}" if mod >= 0 else f"1d4{mod}"
        rl.addWidget(_lbl(f"{dmg_display} piercing", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Armor Spikes (Battlerager Armor)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(CRIM2,0x33)};border:1px solid {CRIM2};"
            f"border-radius:5px;color:{CRIM2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{CRIM2};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_armorer_model_row(self):
        """Artificer Armorer's Arcane Armor grants a built-in weapon
        depending on which model was chosen at 3rd level — Guardian's
        Thunder Gauntlets (1d8 thunder unarmed strike) or Infiltrator's
        Lightning Launcher (ranged 1d6 lightning). Always available once
        chosen, unlike Rage-gated natural weapons elsewhere."""
        from dnd_app.core.character import subclasses
        art_sub = subclasses(self.char).get("Artificer", "")
        if "armorer" not in art_sub.lower():
            return
        pick = self.char.get("_choices", {}).get("armorer_model_3", [])
        if not pick:
            return
        pick_text = pick[0].lower()
        is_guardian = "guardian" in pick_text
        is_infiltrator = "infiltrator" in pick_text
        if not (is_guardian or is_infiltrator):
            return

        pb = get_prof_bonus(self.char)
        # Both models use INT as the spellcasting-focus-driven attack
        # stat for these weapons per their real text (artificer's casting
        # ability), not STR/DEX.
        mod = ability_mod(self.char, "INT")
        atk = sign(pb + mod)
        name = "Thunder Gauntlets" if is_guardian else "Lightning Launcher"
        die = "1d8" if is_guardian else "1d6"
        dmg_type = "thunder" if is_guardian else "lightning"
        note = ("Target has disadvantage on attacks against creatures other than you until your next turn."
                if is_guardian else
                "Ranged 90/300 ft. Once per turn on a hit, deal an extra 1d6 lightning.")

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(PURPLE,0x14)};border:1px solid {qa(PURPLE,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl(name, TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Armor Model", PURP2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip(note)
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", PURP2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup(f"{name} (Armor Model) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "INT", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"{die}+{mod}" if mod >= 0 else f"{die}{mod}"
        rl.addWidget(_lbl(f"{dmg_display} {dmg_type}", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(INT)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk, _name=name):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 {_name} (Armor Model)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(PURPLE,0x33)};border:1px solid {PURPLE};"
            f"border-radius:5px;color:{PURP2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{PURPLE};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_longtooth_shifter_row(self):
        """Longtooth Shifter's fangs — a real natural weapon only while
        Shifting (a bonus action, temporary transformation), matching the
        real trait text exactly."""
        if "Shifting" not in self.char.get("active_effects", []):
            return
        species = self.char.get("species") or self.char.get("race", "")
        subrace = self.char.get("subrace", "") or ""
        # The fangs themselves are mechanically identical between both
        # versions (same 1d6 STR piercing), matched explicitly rather
        # than via a blanket normalization, since other Shifter
        # mechanics (Shifting's own temp-HP formula) do genuinely
        # differ between versions and must never be conflated the same way.
        if species.strip().lower() not in ("shifter", "shifter (mpmm)") or "longtooth" not in subrace.lower():
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Fangs", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Longtooth Shifter", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip("Bonus action attack while Shifting.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup("Fangs (Longtooth Shifter) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        dmg_display = f"1d6+{mod}" if mod >= 0 else f"1d6{mod}"
        rl.addWidget(_lbl(f"{dmg_display} piercing", GOLD2, FS_BODY, wrap=False))
        self._add_onhit_damage_badges(rl)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Fangs (Longtooth Shifter)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(CRIM2,0x33)};border:1px solid {CRIM2};"
            f"border-radius:5px;color:{CRIM2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{CRIM2};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _add_vampire_bite_row(self):
        """Vampire's Bloodthirst — always available, not conditional on
        any toggle (unlike Longtooth Shifter's fangs)."""
        species = self.char.get("species") or self.char.get("race", "")
        if species.strip().lower() != "vampire":
            return
        pb = get_prof_bonus(self.char)
        mod = ability_mod(self.char, "STR")
        atk = sign(pb + mod)

        row_f = QFrame()
        row_f.setStyleSheet(
            f"QFrame{{background:{qa(CRIM2,0x14)};border:1px solid {qa(CRIM2,0x55)};border-radius:8px;}}")
        rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
        rl.addWidget(_lbl("Bloodthirst", TEXT, FS_BODY, bold=True, wrap=False))
        badge = _lbl("Vampire", CRIM2, FS_TINY, bold=True, wrap=False)
        badge.setToolTip("Only against a willing, grappled, incapacitated, or restrained creature. "
                          "Reduces the target's HP max by the necrotic damage dealt (until it long "
                          "rests) and you regain that much HP.")
        rl.addWidget(badge)
        atk_lbl = _lbl(f"{atk} to hit", CRIM2, FS_BODY, wrap=False)
        atk_lbl.setToolTip("Right-click for a breakdown")
        atk_lbl.contextMenuEvent = (lambda e, _atk=atk:
            self._show_breakdown_popup("Bloodthirst (Vampire) — Attack Bonus",
                get_weapon_attack_breakdown(self.char, "STR", True, 0), _atk, e.globalPos()))
        rl.addWidget(atk_lbl)
        rl.addWidget(_lbl("1 piercing", GOLD2, FS_BODY, wrap=False))
        necro_badge = _lbl("+1d6 necrotic", TEAL2, FS_SMALL, wrap=False)
        necro_badge.setToolTip("Bloodthirst (restricted target; drains HP max, heals you)")
        rl.addWidget(necro_badge)
        rl.addWidget(_lbl("(STR)", TEXT3, FS_SMALL, wrap=False))
        rl.addStretch()

        def _roll_hit(checked=False, _atk=atk):
            import random
            d20 = random.randint(1, 20)
            bonus = int(_atk.replace("+","").replace("\u2212","-")) if _atk else 0
            total = d20 + bonus
            crit = (" \u2014 CRIT \u26a1" if d20==20
                    else (" \u2014 Miss \U0001f480" if d20==1 else ""))
            QMessageBox.information(
                None, "Roll To Hit",
                f"\U0001f3b2 Bloodthirst (Vampire)\n\nd20={d20}  {_atk}\nTotal: {total}{crit}")

        hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
        hit_btn.setStyleSheet(
            f"QPushButton{{background:{qa(CRIM2,0x33)};border:1px solid {CRIM2};"
            f"border-radius:5px;color:{CRIM2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{CRIM2};color:white;}}")
        hit_btn.clicked.connect(_roll_hit)
        rl.addWidget(hit_btn)

        self._weapon_rows.addWidget(row_f)
        self._weapon_row_widgets.append(row_f)

    def _refresh_combat_weapons(self):
        """Rebuild the weapon rows in the combat tab from char[equipped_weapons]."""
        while self._weapon_rows.count():
            item = self._weapon_rows.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().setParent(None)
                item.widget().deleteLater()
        self._weapon_row_widgets.clear()
        from dnd_app.core.calculator import class_levels
        if class_levels(self.char).get("Monk", 0) > 0:
            self._add_martial_arts_row()
        if "Hybrid Transformation" in self.char.get("active_effects", []):
            self._add_hybrid_transformation_row()
        self._add_racial_natural_weapon_row()
        self._add_unarmed_fighting_row()
        self._add_tavern_brawler_row()
        self._add_generic_unarmed_strike_row()
        self._add_beast_form_row()
        self._add_battlerager_spikes_row()
        self._add_armorer_model_row()
        self._add_longtooth_shifter_row()
        self._add_vampire_bite_row()
        self._add_wildshape_beast_attack_rows()
        for idx, wpn in enumerate(self.char.get("equipped_weapons",[])):
            self._add_weapon_row(wpn, is_offhand=(idx > 0))

    def _add_wildshape_beast_attack_rows(self):
        """While Wild Shaped, the beast's own actions (Bite, Claws, etc.)
        become real, rollable weapon rows instead of just reference text —
        matching the real rule that your available actions are the
        beast's while transformed. Uses the beast's own pre-computed
        attack bonus and damage from its stat block text rather than
        recomputing from ability scores, since 'Multiattack' and
        condition-on-hit riders (like the wolf's prone-on-hit) don't
        reduce to a single die+modifier the way a simple weapon does."""
        active = self.char.get("_wildshape_active")
        if not active:
            return
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(active)
        if not beast:
            return
        import re
        for name, desc in beast.get("actions", []):
            if name.lower() == "multiattack":
                continue  # descriptive only ("makes two attacks..."), not itself a rollable attack
            m = re.search(r"([+\u2212-]\d+) to hit", desc)
            atk = m.group(1).replace("\u2212", "-") if m else None
            dmg_m = re.search(r"Hit: ([\dd+\u2212-]+) (\w+) damage", desc)
            # Traits like Pounce/Trampling Charge/Dive Attack are bonus-
            # action follow-ups keyed to a specific attack (e.g. Pounce
            # triggers off a claw hit) but live as separate trait entries
            # in the stat block, not part of the action's own text — so
            # without this they'd only be visible by opening the full
            # reference card in the Companions tab.
            linked_trait = next((tname for tname, tdesc in beast.get("traits", [])
                                  if name.lower() in tdesc.lower()
                                  and any(k in tname.lower() for k in
                                          ("pounce", "charge", "dive", "trampl"))), None)

            row_f = QFrame()
            row_f.setStyleSheet(
                f"QFrame{{background:{qa(PURPLE,0x14)};border:1px solid {qa(PURPLE,0x55)};border-radius:8px;}}")
            rl = QHBoxLayout(row_f); rl.setContentsMargins(10,8,10,8); rl.setSpacing(10)
            rl.addWidget(_lbl(name, TEXT, FS_BODY, bold=True, wrap=False))
            badge = _lbl(active, PURP2, FS_TINY, bold=True, wrap=False)
            badge.setToolTip(desc)
            rl.addWidget(badge)
            if linked_trait:
                trait_desc = next(td for tn, td in beast["traits"] if tn == linked_trait)
                trait_badge = _lbl(f"\u26a1 {linked_trait}", GOLD2, FS_TINY, bold=True, wrap=False)
                trait_badge.setToolTip(trait_desc)
                rl.addWidget(trait_badge)
            if atk:
                rl.addWidget(_lbl(f"{atk} to hit", PURP2, FS_BODY, wrap=False))
            if dmg_m:
                rl.addWidget(_lbl(f"{dmg_m.group(1)} {dmg_m.group(2)}", GOLD2, FS_BODY, wrap=False))
            rl.addStretch()

            if atk:
                def _roll_hit(checked=False, _atk=atk, _name=name):
                    import random
                    d20 = random.randint(1, 20)
                    bonus = int(_atk)
                    total = d20 + bonus
                    crit = (" \u2014 CRIT \u26a1" if d20==20
                            else (" \u2014 Miss \U0001f480" if d20==1 else ""))
                    QMessageBox.information(
                        None, "Roll To Hit",
                        f"\U0001f3b2 {_name}\n\nd20={d20}  {'+' if bonus>=0 else ''}{bonus}\nTotal: {total}{crit}")
                hit_btn = QPushButton("\U0001f3b2 Hit"); hit_btn.setFixedSize(60,26)
                hit_btn.setStyleSheet(
                    f"QPushButton{{background:{qa(PURPLE,0x33)};border:1px solid {PURPLE};"
                    f"border-radius:5px;color:{PURP2};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
                    f"QPushButton:hover{{background:{PURPLE};color:white;}}")
                hit_btn.clicked.connect(_roll_hit)
                rl.addWidget(hit_btn)

            self._weapon_rows.addWidget(row_f)
            self._weapon_row_widgets.append(row_f)

        # ══ TAB: CHOICES (level-up panel) ═════════════════════════════════════════
    def _build_tab_choices(self):
        """Choices tab: Class Manager + Identity cards in a top pane, the
        LevelUpPanel (choices) and Optional Class Features in a bottom pane —
        split by a draggable handle, same pattern as the Combat tab. This
        used to be a single QVBoxLayout with the LevelUpPanel forced to
        stretch and fill all remaining space regardless of how much content
        it actually had, which meant a character with few pending choices
        showed a large empty gap with no way to reclaim that space."""
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(f"QSplitter::handle{{background:{qa(AMBER,0x33)};height:4px;"
                              f"border-radius:2px;margin:2px 40%;}}"
                              f"QSplitter::handle:hover{{background:{AMBER};}}")

        top_half = QWidget()
        layout = QVBoxLayout(top_half)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Class Manager card ────────────────────────────────────────────────
        cls_card = QFrame()
        cls_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {qa(INDIGO,0x44)};border-radius:10px;}}")
        cls_cl = QVBoxLayout(cls_card)
        cls_cl.setContentsMargins(12, 8, 12, 8); cls_cl.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        title_row.addWidget(_lbl("⚔  CLASS & LEVEL", INDIGO, FS_SMALL, bold=True))
        title_row.addStretch()
        # Class action buttons
        for label, fn, color, tip in [
            ("⬆ Level Up / Multiclass", self._open_level_up_or_multiclass, GOLD,
             "Gain a level in an existing class, or add a new one"),
            ("⬇ Level Down",      self._open_level_down,      CRIMSON,"Remove one level"),
            ("✕ Remove Class",    self._open_remove_class,    CRIMSON,"Remove an entire class (multiclass only)"),
        ]:
            b = QPushButton(label)
            b.setToolTip(tip)
            b.setFixedHeight(28)
            b.setStyleSheet(
                f"QPushButton{{background:{qa(color,0x22)};border:1px solid {qa(color,0x66)};border-radius:6px;"
                f"color:{color};font-size:{FS_TINY}px;font-weight:700;padding:2px 10px;}}"
                f"QPushButton:hover{{background:{qa(color,0x55)};border-color:{color};}}")
            b.clicked.connect(fn)
            title_row.addWidget(b)
        cls_cl.addLayout(title_row)

        # Subclass selectors — one per active class
        self._subclass_area_card = QHBoxLayout(); self._subclass_area_card.setSpacing(8)
        cls_cl.addLayout(self._subclass_area_card)
        self._subclass_combos = {}

        layout.addWidget(cls_card)

        # ── Identity / Character Config card ─────────────────────────────────
        id_card = QFrame()
        id_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid {qa(TEAL,0x33)};border-radius:10px;}}")
        id_cl = QHBoxLayout(id_card); id_cl.setContentsMargins(12,8,12,8); id_cl.setSpacing(8)
        id_cl.addWidget(_lbl("🧬  IDENTITY", TEAL2, FS_SMALL, bold=True))
        id_cl.addSpacing(4)
        self._identity_btns = {}
        for label, slot, color in [
            ("Race",       "race",       TEAL),
            ("Subrace",    "subrace",    TEAL),
            ("Ancestry",   "ancestry",   GOLD),
            ("Background", "background", AMBER),
        ]:
            b = QPushButton(f"✎  {label}")
            b.setFixedHeight(28)
            b.setStyleSheet(
                f"QPushButton{{background:{qa(color,0x22)};border:1px solid {qa(color,0x66)};border-radius:6px;"
                f"color:{color};font-size:{FS_TINY}px;font-weight:700;padding:2px 10px;}}"
                f"QPushButton:hover{{background:{qa(color,0x44)};border-color:{color};}}")
            b.clicked.connect(lambda checked=False, s=slot: self._edit_identity(s))
            id_cl.addWidget(b)
            self._identity_btns[slot] = b
        id_cl.addStretch()
        layout.addWidget(id_card)
        # Hide Ancestry unless Dragonborn
        if "ancestry" in self._identity_btns:
            self._identity_btns["ancestry"].setVisible(
                self.char.get("race","") == "Dragonborn")
        layout.addStretch()

        # ── Bottom pane: LevelUpPanel + Optional Class Features ───────────────
        bottom_half = QWidget()
        blay = QVBoxLayout(bottom_half)
        blay.setContentsMargins(0, 0, 0, 0)
        blay.setSpacing(8)

        try:
            self._levelup_panel = LevelUpPanel(self.char)
            self._levelup_panel.choices_changed.connect(self._on_choices_changed)
            blay.addWidget(self._levelup_panel, 1)
        except Exception as e:
            import traceback; traceback.print_exc()
            blay.addWidget(_lbl(f"Error: {e}", CRIM2, FS_BODY))

        # ── Optional Class Features (TCoE) ────────────────────────────────
        opt_card = _card()
        opt_card.setStyleSheet(f"QFrame{{background:{SURF};border:1px solid #55E8A020;border-radius:10px;}}")
        opt_lay = QVBoxLayout(opt_card); opt_lay.setContentsMargins(14,12,14,14); opt_lay.setSpacing(6)
        opt_lay.addWidget(_lbl("✦  OPTIONAL CLASS FEATURES  —  Tasha's Cauldron of Everything",
                               "#E8A020", FS_SMALL, bold=True))
        opt_lay.addWidget(_lbl("Toggle alternate features for your classes. Discuss with your DM first.",
                               TEXT3, FS_SMALL))
        self._opt_feat_checks = {}
        self._opt_inner = QWidget(); self._opt_inner.setStyleSheet("background:transparent;")
        self._opt_inner_lay = QVBoxLayout(self._opt_inner)
        self._opt_inner_lay.setSpacing(3); self._opt_inner_lay.setContentsMargins(0,4,0,0)
        opt_lay.addWidget(self._opt_inner)
        blay.addWidget(opt_card)

        splitter.addWidget(top_half)
        splitter.addWidget(bottom_half)
        self._choices_top_half = top_half
        # Roughly a third for the class/identity cards, two-thirds for
        # the scrollable choices list — the splitter handle can be
        # dragged to any ratio, same as the Combat tab.
        splitter.setSizes([220, 460])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

        return tab

    def _on_choices_changed(self):
        """Called when choices are made in the LevelUpPanel."""
        self.ctrl.refresh()
        self._mark_dirty()

    # ══ TAB 4: SPELLS ══════════════════════════════════════════════════════════
    def _has_infuse_item_access(self):
        from dnd_app.core.calculator import class_levels
        return class_levels(self.char).get("Artificer", 0) >= 2 and bool(
            self.char.get("artificer_infusions"))

    def _build_tab_infusions(self):
        tab = QWidget(); lay = QVBoxLayout(tab); lay.setContentsMargins(16,14,16,14); lay.setSpacing(10)
        lay.addWidget(_lbl("ARTIFICER INFUSIONS", GOLD2, FS_HEAD, bold=True))
        self._infusions_summary_lbl = _lbl("", TEXT2, FS_SMALL, wrap=True)
        lay.addWidget(self._infusions_summary_lbl)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:transparent;border:none;}}")
        inner = QWidget(); self._infusions_list_lay = QVBoxLayout(inner)
        self._infusions_list_lay.setSpacing(6)
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)
        self._refresh_infusions_tab()
        return tab

    def _refresh_infusions_tab(self):
        if not hasattr(self, "_infusions_list_lay"):
            return
        from dnd_app.core.calculator import get_max_active_infusions
        known = self.char.get("artificer_infusions", [])
        active = self.char.get("active_infusions", [])
        max_active = get_max_active_infusions(self.char)
        self._infusions_summary_lbl.setText(
            f"Known: {len(known)}  \u2022  Active: {len(active)} / {max_active}")

        while self._infusions_list_lay.count():
            item = self._infusions_list_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)

        active_by_name = {a["infusion"]: a for a in active}
        for inf in known:
            base_name = inf.split(" \u2013 ")[0].strip()
            row = _card(qa(INDIGO, 0x33)); row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(10, 8, 10, 8)
            info = active_by_name.get(base_name)
            status = ""
            if info:
                status = " \u2014 given to another character" if info.get("given_away") else \
                    f" \u2014 active on {info.get('target_item', '?')}"
            name_lbl = _lbl(f"{base_name}{status}", TEXT, FS_BODY, wrap=True)
            row_lay.addWidget(name_lbl, 1)
            if info:
                deactivate_btn = QPushButton("Deactivate")
                deactivate_btn.clicked.connect(lambda checked=False, n=base_name: self._deactivate_infusion(n))
                row_lay.addWidget(deactivate_btn)
            else:
                activate_btn = QPushButton("Activate...")
                activate_btn.setEnabled(len(active) < max_active)
                activate_btn.clicked.connect(lambda checked=False, n=base_name: self._activate_infusion_dialog(n))
                row_lay.addWidget(activate_btn)
            self._infusions_list_lay.addWidget(row)
        self._infusions_list_lay.addStretch()

    def _use_soul_of_artifice(self):
        """Soul of Artifice (Artificer, 20th level) — confirmed this had
        no real implementation beyond the +1-save-per-attuned-item half
        (already correctly handled in calculator.py). The "end an
        infusion to drop to 1 HP instead of 0" half is now buildable
        since active_infusions tracking exists — reuses the exact same
        deactivation logic as the Infusions tab."""
        active = self.char.get("active_infusions", [])
        if not active:
            QMessageBox.information(self, "Soul of Artifice",
                                    "You have no active infusions to end.")
            return
        names = [a["infusion"] for a in active]
        choice, ok = QInputDialog.getItem(
            self, "Soul of Artifice", "End which infusion to drop to 1 HP instead of 0?",
            names, 0, False)
        if ok and choice:
            self._deactivate_infusion(choice)
            self.char["current_hp"] = 1
            self._toast(f"💫 Soul of Artifice: ended {choice}, dropped to 1 HP instead of 0")
            self.ctrl.refresh()
            self._mark_dirty()

    def _deactivate_infusion(self, infusion_name):
        active = self.char.get("active_infusions", [])
        entry = next((a for a in active if a["infusion"] == infusion_name), None)
        if not entry:
            return
        target = entry.get("target_item")
        if target:
            for eq in self.char.get("equipment", []):
                if eq.get("name") == target and eq.get("infused_with") == infusion_name:
                    eq["magic"] = False
                    eq.pop("infused_with", None)
                    break
        self.char["active_infusions"] = [a for a in active if a["infusion"] != infusion_name]
        self._toast(f"Deactivated {infusion_name}")
        self.ctrl.refresh()
        self._refresh_infusions_tab()
        if hasattr(self, "_refresh_gear_equipment"):
            self._refresh_gear_equipment()
        self._mark_dirty()

    def _activate_infusion_dialog(self, infusion_name):
        from dnd_app.data.classes import ARTIFICER_INFUSION_TARGETS
        from dnd_app.core.calculator import get_max_active_infusions
        if len(self.char.get("active_infusions", [])) >= get_max_active_infusions(self.char):
            QMessageBox.warning(self, "Infusion Limit Reached",
                                 "You're already at your maximum number of active infusions.")
            return
        target_type = ARTIFICER_INFUSION_TARGETS.get(infusion_name, "standalone")
        if target_type == "standalone":
            # Homunculus Servant creates a companion CREATURE, not a
            # giftable item, so it gets its own, simpler confirmation
            # rather than the generic "give it to yourself, or to
            # another character?" prompt (you can't hand off your own
            # bonded companion).
            if infusion_name == "Homunculus Servant":
                reply = QMessageBox.question(
                    self, infusion_name,
                    "Activate Homunculus Servant? This infuses a gem to summon your "
                    "homunculus companion.",
                    QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                self._infuse_item(infusion_name, infusion_name, give_away=False)
                self._refresh_infusions_tab()
                self._refresh_companions_tab()
                return
            # No existing item needed — this infusion creates its own
            # item/effect once activated.
            reply = QMessageBox.question(
                self, infusion_name,
                f"Activate {infusion_name}? This creates its own item — give it to yourself, "
                f"or to another character?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
            self._infuse_item(infusion_name if reply == QMessageBox.Yes else "",
                               infusion_name, give_away=(reply != QMessageBox.Yes))
            self._refresh_infusions_tab()
            return
        # "weapon"/"armor"/"shield"/"armor_or_shield" — needs an existing
        # owned mundane item of the matching type to enchant.
        from dnd_app.data.items import WEAPON_DICT, ARMOR_DICT
        candidates = []
        for eq in self.char.get("equipment", []):
            if eq.get("magic"):
                continue
            name = eq.get("name", "")
            is_weapon = name in WEAPON_DICT
            is_armor = name in ARMOR_DICT and ARMOR_DICT[name].get("type") != "shield" and name != "No Armor"
            is_shield = name in ARMOR_DICT and ARMOR_DICT[name].get("type") == "shield"
            if (target_type == "weapon" and is_weapon) or \
               (target_type == "shield" and is_shield) or \
               (target_type == "armor" and is_armor) or \
               (target_type == "armor_or_shield" and (is_armor or is_shield)):
                candidates.append(name)
        if not candidates:
            QMessageBox.information(
                self, infusion_name,
                f"You don't own a mundane item {infusion_name} can apply to yet. Add one from the "
                f"Equipment Browser first, or right-click it directly once you own it.")
            return
        choice, ok = QInputDialog.getItem(
            self, infusion_name, "Apply to which item?", candidates, 0, False)
        if ok and choice:
            self._infuse_item(choice, infusion_name)
            # Resistant Armor: the real rule requires picking one damage
            # type when the armor is infused.
            if infusion_name == "Resistant Armor":
                dmg_type, ok2 = QInputDialog.getItem(
                    self, infusion_name, "Choose a damage type to resist:",
                    ["Acid", "Cold", "Fire", "Force", "Lightning", "Necrotic",
                     "Poison", "Psychic", "Radiant", "Thunder", "Bludgeoning",
                     "Piercing", "Slashing"], 0, False)
                if ok2 and dmg_type:
                    self.char.setdefault("_choices", {})["resistant_armor_type"] = dmg_type
            self._refresh_infusions_tab()

    def _build_tab_spells(self):
        tab = QWidget(); root = QHBoxLayout(tab); root.setContentsMargins(16,16,16,16); root.setSpacing(16)

        # Left: slot tracker + spellcasting info
        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(8)

        # Per-class DC table
        dc_card = _card(PURPLE+"55"); dccl = QVBoxLayout(dc_card); dccl.setContentsMargins(14,12,14,14)
        dccl.addWidget(_lbl("SPELLCASTING", PURP2, FS_SMALL, bold=True))
        self._dc_table_lay = QGridLayout(); self._dc_table_lay.setSpacing(6)
        self._dc_table_lay.addWidget(_lbl("Class", TEXT3, FS_SMALL, bold=True), 0, 0)
        self._dc_table_lay.addWidget(_lbl("Ability", TEXT3, FS_SMALL, bold=True), 0, 1)
        self._dc_table_lay.addWidget(_lbl("Save DC", TEXT3, FS_SMALL, bold=True), 0, 2)
        self._dc_table_lay.addWidget(_lbl("Atk Bonus", TEXT3, FS_SMALL, bold=True), 0, 3)
        dccl.addLayout(self._dc_table_lay); ll.addWidget(dc_card)

        # Spell count summary card
        count_card = _card(PURPLE+"22"); cccl = QVBoxLayout(count_card)
        cccl.setContentsMargins(12,8,12,8); cccl.setSpacing(4)
        cccl.addWidget(_lbl("SPELLS KNOWN / PREPARED", PURP2, FS_SMALL, bold=True))
        self._spell_count_lbl = _lbl("", TEXT2, FS_SMALL, wrap=True)
        self._spell_count_lbl.setTextFormat(Qt.RichText)
        cccl.addWidget(self._spell_count_lbl)
        ll.addWidget(count_card)

        # Spell slots
        slots_card = _card(); sccl = QVBoxLayout(slots_card); sccl.setContentsMargins(14,12,14,14)
        sccl.addWidget(_lbl("SPELL SLOTS", GOLD, FS_SMALL, bold=True))
        self._slot_bars = {}
        for lvl in range(1,10):
            bar = SlotBar(lvl); bar.changed.connect(self._on_slot_change)
            sccl.addWidget(bar); self._slot_bars[lvl] = bar
        ll.addWidget(slots_card)

        # Pact Magic — mechanically distinct from normal spell slots (all
        # slots are the same level, recharge on a SHORT rest not long rest),
        # so it gets its own purple-accented card rather than blending into
        # the blue "SPELL SLOTS" list above.
        self._pact_card = _card(PURPLE+"55")
        pccl = QVBoxLayout(self._pact_card); pccl.setContentsMargins(14,12,14,14)
        pccl.addWidget(_lbl("PACT MAGIC  (recharges on a short rest)", PURP2, FS_SMALL, bold=True))
        self._pact_bar = SlotBar(-1, color=PURPLE); self._pact_bar.changed.connect(self._on_slot_change)
        pccl.addWidget(self._pact_bar)
        ll.addWidget(self._pact_card)
        self._pact_card.setVisible(False)   # hidden until refresh confirms Warlock levels

        # Metamagic quick-apply — lets a Sorcerer pick which known option(s)
        # to apply to their NEXT spell cast and spend the right Sorcery
        # Points, rather than only ever seeing Metamagic listed passively
        # in the Features tab with no way to actually use it.
        self._metamagic_card = _card(PURPLE+"55")
        mmcl = QVBoxLayout(self._metamagic_card); mmcl.setContentsMargins(14,12,14,14)
        mmcl.addWidget(_lbl("METAMAGIC — apply to next cast", PURP2, FS_SMALL, bold=True))
        self._metamagic_cbs = {}
        self._metamagic_box = QVBoxLayout(); self._metamagic_box.setSpacing(4)
        mmcl.addLayout(self._metamagic_box)
        mm_btn_row = QHBoxLayout()
        self._mm_apply_btn = QPushButton("Spend SP & Mark Active")
        self._mm_apply_btn.setStyleSheet(
            f"QPushButton{{background:{qa(PURPLE,0x33)};border:1px solid {PURPLE};"
            f"border-radius:5px;color:{PURP2};font-size:{FS_SMALL}px;font-weight:700;padding:4px 10px;}}"
            f"QPushButton:hover{{background:{PURPLE};color:white;}}")
        self._mm_apply_btn.clicked.connect(self._apply_metamagic_selection)
        mm_btn_row.addWidget(self._mm_apply_btn)
        self._mm_active_lbl = _lbl("", TEAL2, FS_SMALL, bold=True, wrap=True)
        mm_btn_row.addWidget(self._mm_active_lbl, 1)
        mmcl.addLayout(mm_btn_row)
        ll.addWidget(self._metamagic_card)
        self._metamagic_card.setVisible(False)   # shown only if character knows any Metamagic

        # Concentration tracker
        conc_frame = QFrame()
        conc_frame.setStyleSheet(
            f"QFrame{{background:{SURF2};border:1px solid {qa(AMBER,0x55)};border-radius:8px;}}"
        )
        cf = QHBoxLayout(conc_frame)
        cf.setContentsMargins(12, 8, 12, 8)
        cf.setSpacing(10)
        cf.addWidget(_lbl("Concentrating:", AMBER, FS_BODY, bold=True, wrap=False))
        self._conc_lbl = _lbl("—", TEXT2, FS_BODY, wrap=True)
        self._conc_lbl.setMinimumWidth(120)
        self._conc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cf.addWidget(self._conc_lbl, 2)
        drop_btn = QPushButton("Drop")
        drop_btn.setFixedSize(64,30)
        drop_btn.setStyleSheet(f"QPushButton{{background:{qa(CRIMSON,0x44)};border:1px solid {CRIMSON};border-radius:6px;color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:0px;min-height:0px;}}QPushButton:hover{{background:{CRIMSON};color:white;}}")
        drop_btn.clicked.connect(self._drop_concentration)
        cf.addWidget(drop_btn)
        self._conc_save_btn = QPushButton("Conc. Save")
        self._conc_save_btn.setFixedSize(90, 30)
        self._conc_save_btn.setStyleSheet(
            f"QPushButton{{background:{qa(AMBER,0x44)};border:1px solid {AMBER};border-radius:6px;"
            f"color:{AMBER};font-size:{FS_SMALL}px;font-weight:700;padding:0px;min-height:0px;}}"
            f"QPushButton:hover{{background:{AMBER};color:white;}}"
        )
        self._conc_save_btn.clicked.connect(self._prompt_concentration_save)
        cf.addWidget(self._conc_save_btn)
        ll.addWidget(conc_frame)

        # Soul of Artifice (Artificer, 20th level): the "end an infusion
        # to drop to 1 HP instead of 0" half, alongside the +1-save
        # bonus. Buildable since active_infusions tracking exists.
        self._soul_artifice_btn = QPushButton("💫 Soul of Artifice: End an Infusion (drop to 1 HP)")
        self._soul_artifice_btn.setStyleSheet(
            f"QPushButton{{background:{qa(PURPLE,0x33)};border:1px solid {PURPLE};"
            f"border-radius:6px;color:{PURP2};font-size:{FS_SMALL}px;font-weight:700;padding:6px;}}"
            f"QPushButton:hover{{background:{PURPLE};color:white;}}")
        self._soul_artifice_btn.clicked.connect(self._use_soul_of_artifice)
        self._soul_artifice_btn.setVisible(False)  # shown only for 20th-level Artificers
        ll.addWidget(self._soul_artifice_btn)
        ll.addStretch(); root.addWidget(left, 2)

        # Right: two tabs — My Spells | Spell Browser
        right = QTabWidget()
        right.setStyleSheet(
            f"QTabWidget::pane{{background:{SURF};border:1px solid {BORDER};border-radius:8px;}}"
            f"QTabBar::tab{{background:{SURF2};color:{TEXT2};padding:8px 18px;"
            f"font-size:{FS_SMALL}px;border:1px solid {BORDER};border-bottom:none;"
            f"border-radius:6px 6px 0 0;margin-right:2px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD2};font-weight:700;}}"
        )

        # ── My Spells tab ─────────────────────────────────────────────────────
        my_spells_w = QWidget(); mst_lay = QVBoxLayout(my_spells_w)
        mst_lay.setContentsMargins(8,8,8,8); mst_lay.setSpacing(6)
        mst_lay.addWidget(_lbl("MY SPELLS  [ ✓ = Prepared  |  ★ = Quick  |  right-click = Cast ]",
                               GOLD, FS_SMALL, bold=True))
        # Filter box: live-search your known/prepared spells by name
        self._my_sp_filter = QLineEdit()
        self._my_sp_filter.setPlaceholderText("🔍 Filter my spells…")
        self._my_sp_filter.setClearButtonEnabled(True)
        self._my_sp_filter.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:7px;"
            f"padding:6px 10px;color:{TEXT};font-size:{FS_BODY}px;}}")
        self._my_sp_filter.textChanged.connect(self._filter_my_spells)
        mst_lay.addWidget(self._my_sp_filter)

        self._my_sp_prepared_only = QCheckBox("Show only prepared spells")
        self._my_sp_prepared_only.setStyleSheet(
            f"QCheckBox{{color:{TEAL2};font-size:{FS_SMALL}px;font-weight:700;padding:2px;}}")
        self._my_sp_prepared_only.stateChanged.connect(lambda _s: self._filter_my_spells())
        mst_lay.addWidget(self._my_sp_prepared_only)

        self._my_spells_scroll = QScrollArea(); self._my_spells_scroll.setWidgetResizable(True)
        self._my_spells_inner = QWidget(); self._my_spells_inner.setStyleSheet(f"background:{BG};")
        self._my_spells_lay = QVBoxLayout(self._my_spells_inner)
        self._my_spells_lay.setSpacing(4); self._my_spells_lay.setContentsMargins(2,2,2,2)
        self._my_spells_lay.addStretch()
        self._my_spells_scroll.setWidget(self._my_spells_inner)
        self._spell_rows = []; self._level_headers = {}
        mst_lay.addWidget(self._my_spells_scroll, 1)
        right.addTab(my_spells_w, "📖  My Spells")

        # ── Spell Browser tab ─────────────────────────────────────────────────
        browser_w = QWidget(); brl = QVBoxLayout(browser_w); brl.setContentsMargins(8,8,8,8); brl.setSpacing(6)
        browser_card = _card(); brcl = QVBoxLayout(browser_card); brcl.setContentsMargins(14,12,14,14)
        brcl.addWidget(_lbl("SPELL BROWSER", GOLD, FS_SMALL, bold=True))
        bt_row = QHBoxLayout(); bt_row.setSpacing(8)
        self._sp_search = QLineEdit(); self._sp_search.setPlaceholderText("Search 435 spells…")
        self._sp_cls_f  = QComboBox(); self._sp_cls_f.addItem("All Classes")
        for cn in ["Wizard","Cleric","Druid","Bard","Sorcerer","Warlock","Paladin","Ranger","Artificer"]:
            self._sp_cls_f.addItem(cn)
        self._sp_lvl_f = QComboBox(); self._sp_lvl_f.addItem("All Levels")
        for i in range(10): self._sp_lvl_f.addItem("Cantrip" if i==0 else f"Lv {i}")
        bt_row.addWidget(self._sp_search, 2); bt_row.addWidget(self._sp_cls_f); bt_row.addWidget(self._sp_lvl_f)
        brcl.addLayout(bt_row)
        # ── Homebrew toggle: OFF = class-list only + known-spell limits enforced
        self._sp_homebrew = QCheckBox("🔓 Homebrew mode — learn any spell, ignore spell limits")
        self._sp_homebrew.setAccessibleName("Homebrew mode: allow learning any spell and ignore spell limits")
        self._sp_homebrew.setToolTip(
            "Unchecked (default): the browser shows only spells on your classes' lists,\n"
            "and adding is blocked once you reach your spells-known / cantrip limits.\n"
            "Checked: every spell is visible and learnable with no cap.")
        self._sp_homebrew.setStyleSheet(
            f"QCheckBox{{color:{AMBE2};font-size:{FS_SMALL}px;font-weight:700;padding:2px;}}"
            f"QCheckBox::indicator{{width:16px;height:16px;border:2px solid {AMBER};"
            f"border-radius:4px;background:{SURF2};}}"
            f"QCheckBox::indicator:checked{{background:{AMBER};}}"
            f"QCheckBox:focus{{border:2px solid {TEAL2};border-radius:4px;}}")
        self._sp_homebrew.stateChanged.connect(lambda s: (
            self._filter_spell_browser(),
            self._toast("🔓 Homebrew learning ON — any spell, no limits" if s
                        else "🔒 Class lists & spell limits enforced")))
        brcl.addWidget(self._sp_homebrew)
        self._sp_browser = QListWidget()  # no height limit — tab gives full space
        self._sp_browser.setStyleSheet(f"QListWidget{{background:{BG};border:1px solid {BORDER};}}QListWidget::item{{padding:6px 10px;border-bottom:1px solid {BORDER};font-size:{FS_BODY}px;}}QListWidget::item:selected{{background:{INDIGO};color:white;}}")
        self._populate_spell_browser(); brcl.addWidget(self._sp_browser)
        add_btn = pill_btn("+ Add to My Spells", INDIGO); add_btn.clicked.connect(self._add_spell_from_browser)
        brcl.addWidget(add_btn); brl.addWidget(browser_card, 1)
        # Right-click context menu on browser
        self._sp_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self._sp_browser.customContextMenuRequested.connect(self._on_spell_browser_ctx)
        right.addTab(browser_w, "🔍  Spell Browser")

        self._sp_search.textChanged.connect(self._filter_spell_browser)
        self._sp_cls_f.currentTextChanged.connect(self._filter_spell_browser)
        self._sp_lvl_f.currentTextChanged.connect(self._filter_spell_browser)
        self._filter_spell_browser()   # apply class restriction on first view
        root.addWidget(right, 3)
        # My Spells is populated once by _load() right after all tabs finish
        # building (see CharacterSheet.__init__) — NOT here too. This used
        # to also call _populate_my_spells_from_char() at the end of tab
        # construction, which meant it ran twice on every single sheet
        # build; the first pass's widgets got removeWidget()'d but were
        # still scheduled (not yet actually deleted) when the second pass
        # repopulated, leaving stale orphaned spell-row/level-header labels
        # sitting at Qt's default un-laid-out geometry, visible on top of
        # the real content.
        return tab

    def _populate_my_spells_from_char(self):
        """(Re)build the My Spells list widgets from char['spells_known'].
        Called once at sheet construction and once whenever a different
        character is loaded into this sheet — NOT on every generic refresh,
        so in-progress prepared/pin toggles aren't clobbered mid-session."""
        if not hasattr(self, "_my_spells_lay"):
            return
        for row in list(self._spell_rows):
            self._my_spells_lay.removeWidget(row); row.setParent(None); row.deleteLater()
        for hdr in list(self._level_headers.values()):
            self._my_spells_lay.removeWidget(hdr); hdr.setParent(None); hdr.deleteLater()
        for hdr in list(getattr(self, "_class_level_headers", {}).values()):
            self._my_spells_lay.removeWidget(hdr); hdr.setParent(None); hdr.deleteLater()
        self._spell_rows = []
        self._level_headers = {}
        self._class_level_headers = {}
        from dnd_app.data.spells import get_spell as _gs
        prepared_set = set(self.char.get("spells_prepared", []))
        # Sort by class then level. _attribute_known_spells() is
        # intentionally scoped to only track "known spells" caps for
        # Sorcerer/Warlock/Bard/Ranger, so it can't be reused here — a
        # Wizard's (a prepared caster) leveled spells would never be
        # attributed to any class at all. This builds a dedicated
        # attribution instead, covering every known spell for every
        # caster type via _all_caster_classes() (which correctly
        # includes prepared casters).
        all_classes = self._all_caster_classes()
        class_order = [c.get("class","") for c in self.char.get("classes", [])
                       if c.get("class","") in all_classes]
        spell_to_class = {}
        for name in self.char.get("spells_known", []):
            sp = _gs(name)
            sp_classes = set(sp.get("classes", [])) if sp else set()
            for cn in class_order:
                cn_bare = cn.split(" (")[0]  # "Fighter (EK)" -> "Fighter" for list matching
                if cn in sp_classes or cn_bare in sp_classes:
                    spell_to_class[name] = cn
                    break
            else:
                spell_to_class[name] = class_order[0] if class_order else ""
        def _sort_key(name):
            sp = _gs(name)
            lvl = sp.get("level", 0) if sp else 0
            cn = spell_to_class.get(name, "")
            cls_idx = class_order.index(cn) if cn in class_order else len(class_order)
            return (cls_idx, lvl, name)
        for name in sorted(self.char.get("spells_known", []), key=_sort_key):
            sp = _gs(name)
            if sp:
                self._add_spell_row(sp, prepared=(name in prepared_set))
        self._refresh_spell_count_labels()
        self._relayout_my_spells_by_class(spell_to_class, class_order)

    def _relayout_my_spells_by_class(self, spell_to_class, class_order):
        """Re-order the My Spells list into class-then-level groups with
        class-aware headers. A separate, additive pass after the normal
        row-adding process (rather than rewriting _add_spell_row's
        level-only header system) — that system is also used by the
        separate incremental sync path and is carefully written to avoid
        clobbering in-progress prepared/pin edits, so it's kept untouched;
        this only reorders widgets already built."""
        if not class_order:
            return
        for hdr in list(self._level_headers.values()):
            self._my_spells_lay.removeWidget(hdr); hdr.setParent(None); hdr.deleteLater()
        self._level_headers = {}
        self._class_level_headers = {}
        self._spell_row_class = {}
        rows_by_class_level = {}
        for row in self._spell_rows:
            self._my_spells_lay.removeWidget(row)
            cn = spell_to_class.get(row.spell.get("name",""), "")
            self._spell_row_class[row] = cn
            lvl = row.spell.get("level", 0)
            rows_by_class_level.setdefault((cn, lvl), []).append(row)
        lvl_names = ["Cantrips","1st Level","2nd Level","3rd Level","4th Level",
                     "5th Level","6th Level","7th Level","8th Level","9th Level"]
        insert_at = self._my_spells_lay.count() - 1  # before the trailing stretch
        for cn in class_order:
            cls_lvls = sorted({lvl for (c, lvl) in rows_by_class_level if c == cn})
            if not cls_lvls:
                continue
            cls_hdr = _lbl(cn, GOLD2, FS_BODY, bold=True)
            cls_hdr.setStyleSheet(cls_hdr.styleSheet() +
                f"border-bottom:2px solid {qa(GOLD2,0x66)};padding-bottom:4px;margin-top:12px;")
            self._my_spells_lay.insertWidget(insert_at, cls_hdr); insert_at += 1
            self._class_level_headers[(cn, "class")] = cls_hdr
            for lvl in cls_lvls:
                lvl_hdr = _lbl(lvl_names[min(lvl,9)], IND2, FS_SMALL, bold=True)
                lvl_hdr.setStyleSheet(lvl_hdr.styleSheet() +
                    f"border-bottom:1px solid {qa(IND2,0x33)};padding-bottom:2px;margin-top:4px;")
                self._my_spells_lay.insertWidget(insert_at, lvl_hdr); insert_at += 1
                self._class_level_headers[(cn, lvl)] = lvl_hdr
                for row in rows_by_class_level[(cn, lvl)]:
                    self._my_spells_lay.insertWidget(insert_at, row); insert_at += 1

    def _populate_spell_browser(self):
        self._sp_browser.clear()
        for s in ALL_SPELLS:
            lvl_txt = "Ctrp" if s["level"]==0 else f"L{s['level']}"
            conc = " ©" if s.get("concentration") else ""
            rit  = " ®" if s.get("ritual") else ""
            text = f"{lvl_txt:4s}  {s['name']}{conc}{rit}  [{s['school'][:3]}]"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, s)
            item.setToolTip(self._spell_tooltip_text(s))
            self._sp_browser.addItem(item)

    @staticmethod
    def _spell_progression_tables():
        """Single source of truth for spells-known / cantrips-known
        progression tables, shared by the summary display, the learn-gate,
        and the multiclass attribution logic below. (Previously duplicated
        3x across the file, which is exactly how the Metamagic count
        formula drifted into a bug — keeping one copy avoids that class
        of error here.)"""
        SPELLS_KNOWN = {
            "Bard":     {1:4,2:5,3:6,4:7,5:8,6:9,7:10,8:11,9:12,10:14,11:15,12:15,
                         13:16,14:18,15:19,16:19,17:20,18:22,19:22,20:22},
            "Sorcerer": {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,12:12,
                         13:13,14:13,15:14,16:14,17:15,18:15,19:15,20:15},
            "Warlock":  {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:10,11:11,12:11,
                         13:12,14:12,15:13,16:13,17:14,18:14,19:15,20:15},
            "Ranger":   {1:0,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6,10:6,11:7,12:7,
                         13:8,14:8,15:9,16:9,17:10,18:10,19:11,20:11},
        }
        CANTRIPS = {
            "Wizard":   {1:3,4:4,10:5},
            "Cleric":   {1:3},
            "Druid":    {1:2,6:3,11:4},
            "Bard":     {1:2,4:3,10:4},
            "Sorcerer": {1:4,4:5,10:6},
            "Warlock":  {1:2,4:3,10:4},
            "Artificer":{1:2},
        }
        EK_AT = {3:3,4:4,7:5,8:6,10:7,11:8,13:9,14:10,16:11,19:12,20:13}
        PREPARE_AB = {"Wizard":"INT","Cleric":"WIS","Druid":"WIS","Paladin":"CHA","Artificer":"INT"}
        return SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB

    def _all_caster_classes(self):
        """{class_name: (cantrip_max, leveled_max_or_None)} for EVERY class
        that grants cantrips and/or known spells. leveled_max is None for
        prepared casters (Wizard/Cleric/Druid/Paladin/Artificer) — they
        don't have a 'known' leveled-spell cap, they prepare a subset of
        their full list daily (tracked separately via spells_prepared).
        Cantrips work the same way for every class though, so they're
        covered here regardless of prepared vs. known."""
        SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB = self._spell_progression_tables()
        out = {}
        for c in self.char.get("classes", []):
            cname, lvl = c.get("class",""), c.get("level",0)
            sub = c.get("subclass","").lower()
            cant_max = max((v for k,v in CANTRIPS.get(cname,{}).items() if k<=lvl), default=0)
            if cname in SPELLS_KNOWN:
                lvl_max = max((v for k,v in SPELLS_KNOWN[cname].items() if k<=lvl), default=0)
                out[cname] = (cant_max, lvl_max)
            elif cname == "Fighter" and "eldritch knight" in sub:
                lvl_max = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                out["Fighter (EK)"] = (2 + (1 if lvl>=10 else 0), lvl_max)
            elif cname == "Rogue" and "arcane trickster" in sub:
                lvl_max = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                out["Rogue (AT)"] = (2 + (1 if lvl>=10 else 0), lvl_max)
            elif cname in PREPARE_AB:
                out[cname] = (cant_max, None)
        return out

    def _known_spell_classes(self):
        """{class_name: (cantrip_max, leveled_max)} for classes that track
        their OWN known-LEVELED-spells list (Bard, Sorcerer, Warlock,
        Ranger, EK Fighter, AT Rogue) — i.e. _all_caster_classes() minus
        the prepared casters, who don't have a known-spells cap at all."""
        return {cn: (c, l) for cn, (c, l) in self._all_caster_classes().items()
                if l is not None}

    def _attribute_known_spells(self):
        """Partition char['spells_known'] into per-class buckets.

        5e multiclass spellcasting (PHB p.164): each class's spells-known
        is a COMPLETELY SEPARATE pool — a Sorcerer/Warlock doesn't share
        one combined list, and spell slots being shared (multiclass slot
        table) doesn't change that. This was previously computed as ONE
        pooled total shown redundantly against EACH class's own cap, which
        both mis-split multiclass casters and let one class's spells count
        against another's limit. Cantrips are attributed across EVERY
        casting class (prepared casters included, since cantrips are
        always "known" regardless of prepared/known spellcasting style);
        leveled spells are only attributed across classes with a genuine
        known-spells pool.

        When a known spell is on more than one of the character's own
        eligible class lists (a genuine overlap), it's assigned to
        whichever eligible class currently has the most room left
        relative to its own cap, keeping the split balanced rather than
        one class eating the other's allowance by list order alone.

        Returns: {class_name: {'cantrips': [...], 'leveled': [...]}}
        """
        from dnd_app.data.spells import get_spell as _gs
        all_classes = self._all_caster_classes()
        known_classes = self._known_spell_classes()
        buckets = {cn: {"cantrips": [], "leveled": []} for cn in all_classes}
        if not all_classes:
            return buckets

        def _real_name(cn):
            return "Wizard" if cn in ("Fighter (EK)", "Rogue (AT)") else cn

        # Racial/subclass bonus spells (Fairy's Druidcraft, a Cleric
        # domain spell, etc.) are merged into spells_known so they're
        # castable, but they're always-known freebies, not a pick that
        # should eat into a class's own known-spells/cantrip cap — so
        # this loop excludes anything in char["bonus_spells"] before
        # counting entries against a class's cap.
        bonus = set(self.char.get("bonus_spells", []))
        for name in self.char.get("spells_known", []):
            if name in bonus:
                continue
            sp = _gs(name)
            if not sp: continue
            is_cantrip = sp.get("level", 1) == 0
            sp_classes = set(sp.get("classes", []))
            pool = all_classes if is_cantrip else known_classes
            eligible = [cn for cn in pool if _real_name(cn) in sp_classes]
            eligible = list(dict.fromkeys(eligible)) or list(pool.keys())
            if not eligible:
                continue
            if len(eligible) == 1:
                target = eligible[0]
            else:
                def _room(cn):
                    cant_max, lvl_max = all_classes[cn]
                    bucket = buckets[cn]["cantrips"] if is_cantrip else buckets[cn]["leveled"]
                    cap = cant_max if is_cantrip else (lvl_max if lvl_max is not None else 999)
                    return cap - len(bucket)
                target = max(eligible, key=_room)
            buckets[target]["cantrips" if is_cantrip else "leveled"].append(name)
        return buckets

    def _refresh_spellcasting_table(self):
        """Populate the 'Class | Ability | Save DC | Atk Bonus' table.

        This table's HEADER existed but nothing ever populated a data row —
        spell save DC and attack bonus were completely invisible in the UI
        for every character, single-class or multiclass.

        5e multiclass spellcasting (PHB p.164): a spell's save DC and attack
        bonus use the spellcasting ability of the class it was learned
        from — a Sorcerer/Wizard doesn't have one shared DC, it has a
        separate DC for its Sorcerer spells (CHA) and its Wizard spells
        (INT). So this is genuinely one row per casting class, not one
        pooled row for the whole character.
        """
        if not hasattr(self, "_dc_table_lay"): return
        from dnd_app.core.calculator import get_prof_bonus, ability_mod as _am
        from dnd_app.data.classes import CLASS_DICT

        # Clear any existing data rows. QGridLayout has no removeRow(), so
        # track our own row widgets instead — rebuilt fresh on every refresh.
        # setParent(None) (not just deleteLater()) matters here: this table
        # gets refreshed more than once in a single _load() pass (once via
        # _refresh_spells(), again via _populate_my_spells_from_char()), and
        # deleteLater() alone only *schedules* eventual destruction — it
        # doesn't stop the widget from still being part of the tree (and
        # visible) in between. setParent(None) detaches it immediately.
        lay = self._dc_table_lay
        for w in getattr(self, "_dc_row_widgets", []):
            lay.removeWidget(w); w.setParent(None); w.deleteLater()
        self._dc_row_widgets = []

        pb = get_prof_bonus(self.char)
        row_i = 1
        for c in self.char.get("classes", []):
            cname, lvl = c.get("class",""), c.get("level",0)
            sub = c.get("subclass","").lower()
            ability = CLASS_DICT.get(cname, {}).get("spell_ability")
            display_name = cname
            if cname == "Fighter" and "eldritch knight" in sub:
                ability, display_name = "INT", "Fighter (EK)"
            elif cname == "Rogue" and "arcane trickster" in sub:
                ability, display_name = "INT", "Rogue (AT)"
            if not ability:
                continue   # non-casting class (or subclass without spells yet)
            mod = _am(self.char, ability)
            dc = 8 + pb + mod
            atk = pb + mod
            atk_str = f"+{atk}" if atk >= 0 else str(atk)
            dc_lbl  = _lbl(str(dc), GOLD2, FS_SMALL, bold=True, wrap=False)
            atk_lbl = _lbl(atk_str, TEAL2, FS_SMALL, bold=True, wrap=False)
            dc_lbl.setToolTip("Right-click for a breakdown")
            atk_lbl.setToolTip("Right-click for a breakdown")
            dc_lbl.contextMenuEvent = (lambda e, _a=ability, _dc=dc:
                self._show_breakdown_popup(f"{_a} Save DC",
                    get_save_dc_breakdown(self.char, _a), str(_dc), e.globalPos()))
            atk_lbl.contextMenuEvent = (lambda e, _a=ability, _atk=atk_str:
                self._show_breakdown_popup(f"{_a} Spell Attack Bonus",
                    get_spell_attack_breakdown(self.char, _a), _atk, e.globalPos()))
            cells = [
                _lbl(display_name, TEXT, FS_SMALL, bold=True, wrap=False),
                _lbl(ability, TEXT2, FS_SMALL, wrap=False),
                dc_lbl,
                atk_lbl,
            ]
            for col, w in enumerate(cells):
                lay.addWidget(w, row_i, col)
                self._dc_row_widgets.append(w)
            row_i += 1

        if row_i == 1:
            hint = _lbl("No spellcasting classes.", TEXT3, FS_SMALL, wrap=False)
            lay.addWidget(hint, row_i, 0, 1, 4)
            self._dc_row_widgets.append(hint)

    def _refresh_spell_count_labels(self):
        """Show how many spells and cantrips each class can currently know/prepare.
        Multiclass known-spell casters (Sorcerer/Warlock, Bard/Warlock, etc.)
        are tracked SEPARATELY per class and summed additively for the total —
        never pooled into one shared count checked against every class's cap."""
        if not hasattr(self, "_spell_count_lbl"): return
        from dnd_app.core.character import ability_mod as _am
        char = self.char
        SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB = self._spell_progression_tables()
        attributed = self._attribute_known_spells()
        prepared_attributed = self._attribute_prepared_spells()
        lines = []
        for c in char.get("classes",[]):
            cname = c["class"]; lvl = c["level"]
            sub = c.get("subclass","").lower()
            ctbl = CANTRIPS.get(cname,{})
            cmax = max((v for k,v in ctbl.items() if k<=lvl), default=0)
            is_ek = cname=="Fighter" and "eldritch knight" in sub
            is_at = cname=="Rogue" and "arcane trickster" in sub
            if is_ek or is_at:
                # EK/AT aren't in the CANTRIPS table (it's keyed by full
                # caster class names) — they get 2 cantrips at 3rd level,
                # 3 at 10th, same formula used in _known_spell_classes().
                cmax = 2 + (1 if lvl >= 10 else 0)
            # This class's OWN attributed spells only — not the whole
            # character's flat spells_known list.
            bucket_key = ("Fighter (EK)" if cname=="Fighter" and "eldritch knight" in sub
                         else "Rogue (AT)" if cname=="Rogue" and "arcane trickster" in sub
                         else cname)
            my_bucket = attributed.get(bucket_key, {"cantrips":[], "leveled":[]})
            cur_cantrips = len(my_bucket["cantrips"])
            cur_noncant  = len(my_bucket["leveled"])
            cantrip_line = (f"  <span style='color:{TEXT3};'>Cantrips: {cur_cantrips}/{cmax}</span>" if cmax else "")
            if cname in SPELLS_KNOWN:
                tbl = SPELLS_KNOWN[cname]
                best = max((v for k,v in tbl.items() if k<=lvl), default=0)
                lines.append(f"<b>{cname} Lv{lvl}</b>: {cur_noncant}/{best} spells known{cantrip_line}")
            elif cname == "Fighter" and "eldritch knight" in sub:
                best = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                lines.append(f"<b>EK Fighter Lv{lvl}</b>: {cur_noncant}/{best} spells{cantrip_line}")
            elif cname == "Rogue" and "arcane trickster" in sub:
                best = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
                lines.append(f"<b>AT Rogue Lv{lvl}</b>: {cur_noncant}/{best} spells{cantrip_line}")
            elif cname in PREPARE_AB:
                ab = PREPARE_AB[cname]
                mod = _am(char, ab)
                eff = lvl if cname not in ("Paladin","Artificer") else max(1, lvl//2)
                max_prep = max(1, mod + eff)
                cur_prep = len(prepared_attributed.get(cname, []))
                lines.append(f"<b>{cname} Lv{lvl}</b>: {cur_prep}/{max_prep} prepared"
                              f"<span style='color:{TEXT3};'> ({ab}+lvl)</span>{cantrip_line}")
        self._spell_count_lbl.setText("<br>".join(lines) if lines else "No spellcasting classes.")
        self._refresh_spell_class_badges()
        self._refresh_spellcasting_table()
        self._refresh_metamagic_card()

    @staticmethod
    def _parse_sp_cost(option_text: str) -> tuple[int | None, bool]:
        """Parse a Metamagic option's SP cost. Returns (fixed_cost_or_None,
        is_per_spell_level) — e.g. 'spend 2 SP' -> (2, False), 'spend SP
        equal to spell level' -> (None, True)."""
        import re
        if "equal to spell level" in option_text.lower():
            return None, True
        m = re.search(r'spend (\d+) SP', option_text)
        return (int(m.group(1)) if m else 1), False

    def _refresh_metamagic_card(self):
        """Rebuild the Metamagic quick-apply checkboxes from the character's
        actually-known options (never the full pool), and show/hide the
        whole card based on whether they know any at all."""
        if not hasattr(self, "_metamagic_card"):
            return
        known = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
        self._metamagic_card.setVisible(bool(known))
        if hasattr(self, "_soul_artifice_btn"):
            from dnd_app.core.calculator import class_levels
            self._soul_artifice_btn.setVisible(class_levels(self.char).get("Artificer", 0) >= 20)
        while self._metamagic_box.count():
            item = self._metamagic_box.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._metamagic_cbs = {}
        for opt in known:
            name = opt.split("–")[0].strip()
            cost, per_level = self._parse_sp_cost(opt)
            cost_str = "SP = spell level" if per_level else f"{cost} SP"
            cb = QCheckBox(f"{name}  ({cost_str})")
            cb.setStyleSheet(f"QCheckBox{{color:{TEXT};font-size:{FS_SMALL}px;}}")
            cb.setToolTip(opt)
            self._metamagic_box.addWidget(cb)
            self._metamagic_cbs[opt] = cb
        self._mm_active_lbl.setText("")

    def _apply_metamagic_selection(self):
        """Spend Sorcery Points for whichever Metamagic checkboxes are
        selected and mark them active for the next cast. Doesn't simulate
        each option's mechanical effect (that varies per spell/target) —
        it handles the concrete, common part: paying the SP cost and
        tracking what's active so the player (and the cast confirmation)
        can see it."""
        selected = [opt for opt, cb in self._metamagic_cbs.items() if cb.isChecked()]
        if not selected:
            self._toast("Select at least one Metamagic option first")
            return
        sp_res = next((r for r in self.char.get("resources", [])
                       if r.get("key") == "sorcery_points"), None)
        if not sp_res:
            self._toast("No Sorcery Points resource found")
            return
        total_cost = 0
        per_level_opts = []
        for opt in selected:
            cost, per_level = self._parse_sp_cost(opt)
            if per_level:
                per_level_opts.append(opt.split("–")[0].strip())
            else:
                total_cost += cost
        available = sp_res.get("current", 0)
        if total_cost > available:
            self._toast(f"🔒 Not enough Sorcery Points ({available} available, "
                        f"{total_cost} needed for fixed-cost options)")
            return
        sp_res["current"] = available - total_cost
        active_names = [opt.split("–")[0].strip() for opt in selected]
        self.char["_active_metamagic"] = active_names
        note = f"Active for next cast: {', '.join(active_names)}"
        if per_level_opts:
            note += f"  ({', '.join(per_level_opts)} costs SP = the slot level you cast at)"
        self._mm_active_lbl.setText(note)
        self._toast(f"✓ Spent {total_cost} SP — {', '.join(active_names)} active for your next cast")
        if hasattr(self, "_refresh_action_tabs"): self._refresh_action_tabs()
        self._mark_dirty()

    def _refresh_spell_class_badges(self):
        """Show a small class-source badge (SORC/LOCK/etc.) on each spell
        row when the character has 2+ known-spell classes, so a multiclass
        caster can see at a glance which pool each spell counts against.
        Single-class casters never see this — nothing to disambiguate."""
        if not hasattr(self, "_spell_rows"):
            return
        known_classes = self._known_spell_classes()
        if len(known_classes) < 2:
            for row in self._spell_rows:
                row.set_class_tag(None)
            return
        attributed = self._attribute_known_spells()
        owner = {}
        for cn, buckets in attributed.items():
            for name in buckets["cantrips"] + buckets["leveled"]:
                owner[name] = cn
        for row in self._spell_rows:
            row.set_class_tag(owner.get(row.spell.get("name")))

    def _refresh_quick_spells(self):
        """Quick spells now live in the Action tab via _refresh_action_tabs.
        This method is kept so callers don't crash; it delegates to the full refresh."""
        if hasattr(self, '_action_tabs'):
            self._refresh_action_tabs()

    def _on_spell_browser_ctx(self, pos):
        """Right-click on spell browser — show full details."""
        item = self._sp_browser.itemAt(pos)
        if not item: return
        spell_name = item.text().strip()
        from dnd_app.data.spells import get_spell
        spell = get_spell(spell_name)
        if not spell: return
        from PySide6.QtWidgets import QMenu, QDialog, QVBoxLayout, QScrollArea, QWidget, QLabel, QDialogButtonBox
        menu = QMenu(self)
        detail_act = menu.addAction(f"📖  Details: {spell_name}")
        add_act    = menu.addAction(f"+ Add to My Spells")
        action = menu.exec(self._sp_browser.viewport().mapToGlobal(pos))
        if action == detail_act:
            s = spell
            lvl_txt = "Cantrip" if s.get("level",0)==0 else f"Level {s['level']}"
            desc = s.get("desc") or s.get("description","")
            higher = s.get("higher_levels","") or s.get("higher","")
            detail = (f"<b>{s['name']}</b> [{lvl_txt} {s.get('school','').title()}]<br>"
                      f"<i>Cast:</i> {s.get('casting_time',s.get('cast_time','—'))} &nbsp;"
                      f"<i>Range:</i> {s.get('range','—')} &nbsp;"
                      f"<i>Duration:</i> {s.get('duration','—')}<br>"
                      f"<i>Components:</i> {s.get('components','—')}<br><br>"
                      f"{desc}" + (f"<br><br><i>At Higher Levels:</i> {higher}" if higher else ""))
            dlg = QDialog(self); dlg.setWindowTitle(s['name']); dlg.setMinimumWidth(520)
            lay = QVBoxLayout(dlg)
            lbl = QLabel(detail); lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size:13px;padding:8px;")
            sa = QScrollArea(); sa.setWidgetResizable(True)
            inner = QWidget(); il = QVBoxLayout(inner); il.addWidget(lbl)
            sa.setWidget(inner); lay.addWidget(sa)
            bb = QDialogButtonBox(QDialogButtonBox.Close)
            bb.rejected.connect(dlg.reject); lay.addWidget(bb); dlg.exec()
        elif action == add_act:
            self._add_spell_from_browser()

    def _filter_spell_browser(self):
        q  = self._sp_search.text().lower()
        cl = self._sp_cls_f.currentText()
        lv = self._sp_lvl_f.currentText()
        homebrew = self._sp_homebrew.isChecked()
        max_castable = None if homebrew else self._max_castable_spell_level()
        for i in range(self._sp_browser.count()):
            item = self._sp_browser.item(i); sp = item.data(Qt.UserRole)
            if not sp: continue
            ok = not q or q in sp["name"].lower()
            if cl != "All Classes": ok = ok and cl in sp.get("classes",[])
            if not homebrew:
                mine = self._char_spell_classes()
                if mine: ok = ok and bool(set(sp.get("classes",[])) & mine)
                # Hide leveled spells above what the character can currently
                # cast — unless Homebrew mode is on, matching the "+ Add"
                # button's own castable-level gate so the browser doesn't
                # show spells it would then refuse to add.
                if max_castable is not None and sp.get("level", 0) > max_castable:
                    ok = False
            if lv != "All Levels":
                ok = ok and ((lv=="Cantrip" and sp["level"]==0) or
                             (lv.startswith("Lv") and sp["level"]==int(lv[3:])))
            item.setHidden(not ok)

    def _char_spell_classes(self) -> set:
        """Class spell-lists this character can learn from (EK/AT → Wizard)."""
        out = set()
        for c in self.char.get("classes", []):
            cn = c.get("class",""); sub = c.get("subclass","").lower()
            if cn in ("Wizard","Cleric","Druid","Bard","Sorcerer","Warlock",
                      "Paladin","Ranger","Artificer"):
                out.add(cn)
            if cn == "Fighter" and "eldritch knight" in sub: out.add("Wizard")
            if cn == "Rogue"   and "arcane trickster" in sub: out.add("Wizard")
        return out

    def _spell_caps(self):
        """(cantrip_max, leveled_max_or_None) POOLED across all casting
        classes — kept only as a coarse "could this possibly fit anywhere"
        check for UI hints. Actual per-spell gating in
        _add_spell_from_browser uses _all_caster_classes()/
        _attribute_known_spells() for genuine per-class caps instead of
        this pooled total, since 5e multiclass spellcasting never actually
        shares one combined known-spells pool."""
        all_classes = self._all_caster_classes()
        cant_max = sum(c for c, l in all_classes.values())
        leveled_vals = [l for c, l in all_classes.values() if l is not None]
        lvl_max = sum(leveled_vals) if leveled_vals else 0
        prepared_only = bool(all_classes) and not leveled_vals
        return cant_max, (None if prepared_only else lvl_max)

    def _max_castable_spell_level(self) -> int:
        """Highest spell level the character can currently cast, combining
        ordinary spell slots and Warlock Pact Magic — the two are tracked
        completely separately in the character data, so checking only one
        would wrongly block (or wrongly allow) a pure-Warlock or
        multiclass Warlock character."""
        max_lvl = 0
        for i, count in enumerate(self.char.get("spell_slots_max", [])):
            if count > 0:
                max_lvl = i + 1
        if self.char.get("pact_slots_max", 0) > 0:
            max_lvl = max(max_lvl, self.char.get("pact_slot_level", 0))
        return max_lvl

    def _add_spell_from_browser(self):
        homebrew = self._sp_homebrew.isChecked()
        my_classes = self._char_spell_classes()
        from dnd_app.data.spells import get_spell as _gs

        def _real_name(cn):
            return "Wizard" if cn in ("Fighter (EK)", "Rogue (AT)") else cn

        for item in self._sp_browser.selectedItems():
            sp = item.data(Qt.UserRole)
            if not sp or any(r.spell["name"]==sp["name"] for r in self._spell_rows):
                continue
            name = sp["name"]
            if not homebrew:
                # Gate 1: must be on one of your classes' lists — OR added
                # to that list by a racial Mark (Mark of Shadow/Detection/
                # Storm expand the spell list itself, per their real text,
                # rather than granting a spell directly).
                from dnd_app.data.spells import get_mark_expanded_spells
                mark_spells = get_mark_expanded_spells(self.char)
                if my_classes and name not in mark_spells and not (set(sp.get("classes",[])) & my_classes):
                    self._toast(f"🔒 {name} isn't on your class spell lists "
                                f"— enable Homebrew mode to learn it")
                    continue
                # Gate 2: spell level can't exceed what you can actually
                # cast yet — a 1st-level Wizard has no business learning a
                # 3rd-level spell just because it's on the Wizard list.
                # Cantrips (level 0) are always castable, so this only
                # applies to leveled spells.
                sp_level = sp.get("level", 0)
                if sp_level > 0:
                    max_lvl = self._max_castable_spell_level()
                    if sp_level > max_lvl:
                        self._toast(f"🔒 {name} is a level {sp_level} spell — you can only "
                                    f"cast up to level {max_lvl} right now "
                                    f"— enable Homebrew mode to exceed it")
                        continue
                # Gate 3: per-class spells-known / cantrip caps. Recomputed
                # fresh each spell (not hoisted out of the loop) so adding
                # spell N correctly affects the room-check for spell N+1 —
                # multiclass casters have SEPARATE pools per class, so a
                # Sorcerer/Warlock can't "borrow" the other's headroom.
                all_classes = self._all_caster_classes()
                is_cantrip = sp.get("level", 0) == 0
                sp_classes = set(sp.get("classes", []))
                pool = all_classes if is_cantrip else self._known_spell_classes()
                eligible = [cn for cn in pool if _real_name(cn) in sp_classes]
                if pool and not eligible:
                    # On your class list overall (Gate 1 passed) but none of
                    # your KNOWN-spell classes can take it — e.g. a spell
                    # that's only on a prepared caster's list for this
                    # character. No "known" cap applies to that; let it through.
                    eligible = []
                if eligible:
                    attributed = self._attribute_known_spells()
                    def _room(cn):
                        cant_max, lvl_max = all_classes[cn]
                        bucket = attributed.get(cn, {"cantrips":[], "leveled":[]})
                        used = len(bucket["cantrips"]) if is_cantrip else len(bucket["leveled"])
                        cap = cant_max if is_cantrip else lvl_max
                        return (cap if cap is not None else 999) - used
                    best_cn = max(eligible, key=_room)
                    if _room(best_cn) <= 0:
                        cap_shown = all_classes[best_cn][0 if is_cantrip else 1]
                        used_shown = cap_shown - _room(best_cn) if cap_shown is not None else "?"
                        kind = "Cantrip" if is_cantrip else "Spells-known"
                        self._toast(f"🔒 {kind} limit reached for {_real_name(best_cn)} "
                                    f"({used_shown}/{cap_shown}) — enable Homebrew mode to exceed it")
                        continue
            if name not in self.char.get("spells_known", []):
                self.char.setdefault("spells_known",[]).append(name)
            row = self._add_spell_row(sp)
            # Full-list prepared casters (Cleric/Druid/Paladin/Artificer)
            # don't have a separate "learn a spell" step at all in the real
            # rules — their entire class list is always available, and
            # preparing IS the only choice. Auto-prepare here rather than
            # making the player click Add and then separately check
            # Prepared for the same spell. Wizard is deliberately excluded:
            # it's also a prepared caster, but real Wizards are limited to
            # whatever's in their spellbook, so the "add" step here still
            # means something distinct from "prepare" for them.
            _, _, _, PREPARE_AB = self._spell_progression_tables()
            full_list_classes = {c for c in PREPARE_AB if c != "Wizard"}
            if sp.get("level", 0) > 0 and full_list_classes & set(sp.get("classes", [])) & my_classes:
                self._on_prep_toggled(row, True)
        self._refresh_spell_count_labels()
        self._mark_dirty()

    def _filter_my_spells(self, text: str = None):
        """Live-filter the My Spells list; hides non-matching rows and
        empty headers. Also applies the "show only prepared" toggle —
        directly requested, alongside class-then-level sorting."""
        q = (text if text is not None else self._my_sp_filter.text()).strip().lower()
        prepared_only = getattr(self, "_my_sp_prepared_only", None)
        prepared_only = prepared_only.isChecked() if prepared_only else False
        visible = {}  # (class, level) -> True if any matching row is visible there
        for row in self._spell_rows:
            name = row.spell.get("name", "").lower()
            text_match = (q in name) if q else True
            prep_match = (not prepared_only) or row.is_prepared()
            match = text_match and prep_match
            row.setVisible(match)
            if match:
                cn = self._spell_row_class.get(row, "") if hasattr(self, "_spell_row_class") else ""
                visible[(cn, row.spell.get("level", 0))] = True
                visible[(cn, "class")] = True
        for lvl, hdr in self._level_headers.items():
            hdr.setVisible(True if not (q or prepared_only) else any(
                k[1] == lvl for k in visible))
        for key, hdr in getattr(self, "_class_level_headers", {}).items():
            hdr.setVisible(True if not (q or prepared_only) else visible.get(key, False))

    def _prepared_caster_caps(self) -> dict:
        """{class_name: cap} for each prepared-casting class the character
        has (Wizard/Cleric/Druid: ability mod + class level; Paladin/
        Artificer: ability mod + half class level, rounded down), each with
        a minimum of 1. Per-class, NOT pooled — 5e multiclass spellcasting
        gives each prepared-caster class its own separate prepared-spell
        allotment (PHB p.164, same principle as spells-known being
        per-class for Sorcerer/Bard/Warlock/Ranger). Preparing a Cleric
        spell should never eat into a Druid's separate allotment on the
        same character, or vice versa."""
        from dnd_app.core.character import ability_mod
        _, _, _, PREPARE_AB = self._spell_progression_tables()
        caps = {}
        for c in self.char.get("classes", []):
            cname, lvl = c.get("class",""), c.get("level",0)
            if cname not in PREPARE_AB or lvl <= 0:
                continue
            mod = ability_mod(self.char, PREPARE_AB[cname])
            level_term = (lvl // 2) if cname in ("Paladin", "Artificer") else lvl
            caps[cname] = max(1, mod + level_term)
        return caps

    def _attribute_prepared_spells(self) -> dict:
        """Partition char['spells_prepared'] into per-class buckets, the
        same way _attribute_known_spells() does for spells_known. Only
        ordinary leveled spells count (cantrips and bonus/domain/circle
        spells are always-available and don't draw from any class's
        prepared allotment). When a prepared spell is on more than one of
        the character's own prepared-caster class lists, it's assigned to
        whichever eligible class currently has the most room left, keeping
        the split balanced rather than one class's list winning by order.

        Returns: {class_name: [spell_name, ...]}
        """
        from dnd_app.data.spells import get_spell as _gs
        caps = self._prepared_caster_caps()
        buckets = {cn: [] for cn in caps}
        if not caps:
            return buckets
        bonus = set(self.char.get("bonus_spells", []))
        for name in self.char.get("spells_prepared", []):
            if name in bonus:
                continue
            sp = _gs(name)
            if not sp or sp.get("level", 0) == 0:
                continue
            sp_classes = set(sp.get("classes", []))
            eligible = [cn for cn in caps if cn in sp_classes]
            if not eligible:
                continue
            if len(eligible) == 1:
                target = eligible[0]
            else:
                target = max(eligible, key=lambda cn: caps[cn] - len(buckets[cn]))
            buckets[target].append(name)
        return buckets

    def _on_prep_toggled(self, row, checked: bool):
        """Sync a spell row's prepared checkbox to char['spells_prepared'],
        enforcing each prepared-caster class's OWN cap on the way in —
        not a single total pooled across every prepared-caster class the
        character has. 5e multiclass spellcasting gives each prepared-
        caster class its own separate prepared-spell allotment; a Cleric/
        Druid character preparing 5 Cleric spells shouldn't have any less
        room left for Druid spells as a result, and vice versa."""
        name = row.spell.get("name", "")
        prepared = self.char.setdefault("spells_prepared", [])
        if not checked:
            if name in prepared:
                prepared.remove(name)
            self._refresh_spell_count_labels()
            self._mark_dirty()
            return
        if name in prepared:
            return
        # Cantrips and class-granted bonus spells (domain/oath/circle
        # spells) don't count against any prepared cap — only ordinary
        # leveled spells the player is actively choosing to prepare do.
        if row.spell.get("level", 0) > 0 and name not in self.char.get("bonus_spells", []):
            caps = self._prepared_caster_caps()
            sp_classes = set(row.spell.get("classes", []))
            eligible = [cn for cn in caps if cn in sp_classes]
            if eligible:
                attributed = self._attribute_prepared_spells()
                target = max(eligible, key=lambda cn: caps[cn] - len(attributed.get(cn, [])))
                current = len(attributed.get(target, []))
                cap = caps[target]
                if current >= cap:
                    row.set_prepared(False)
                    self._toast(f"🔒 {target}'s prepared spell limit reached ({current}/{cap}) "
                                f"— unprepare another {target} spell first")
                    return
        prepared.append(name)
        self._refresh_spell_count_labels()
        self._mark_dirty()

    def _add_spell_row(self, spell, prepared=False):
        lvl = spell["level"]
        is_bonus = spell["name"] in self.char.get("bonus_spells", [])
        if lvl == 0:
            prepared = True   # Cantrips are always available — no prep needed (PHB p.201)
            # Show the actual current damage for a scaling cantrip rather
            # than making the player do the 5/11/17 math themselves — on a
            # COPY, since `spell` is the shared global spell-database dict.
            resolved_desc = _append_cantrip_scaling_note(spell["name"], spell.get("desc",""), self.char)
            if resolved_desc != spell.get("desc",""):
                spell = {**spell, "desc": resolved_desc}
        elif is_bonus:
            prepared = True   # Feat/racial/class bonus spells are always available too
        if lvl not in self._level_headers:
            names = ["Cantrips","1st Level","2nd Level","3rd Level","4th Level",
                     "5th Level","6th Level","7th Level","8th Level","9th Level"]
            hdr = _lbl(names[min(lvl,9)], IND2, FS_SMALL, bold=True)
            hdr.setStyleSheet(hdr.styleSheet() + f"border-bottom:2px solid {qa(IND2,0x44)};padding-bottom:4px;margin-top:8px;")
            self._level_headers[lvl] = hdr
            ins = self._find_hdr_pos(lvl)
            self._my_spells_lay.insertWidget(ins, hdr)
        from dnd_app.ui.immersive_spells import compute_display_spell_title
        row = SpellRow(spell, prepared, locked=is_bonus,
                        display_name=compute_display_spell_title(self.char, spell["name"]))
        from dnd_app.core.calculator import can_ritual_cast
        row.set_can_ritual(can_ritual_cast(self.char, spell))
        row.remove.connect(self._remove_spell_row)
        row.cast.connect(self._cast_spell)
        row.cast_ritual.connect(self._cast_spell_as_ritual)
        row.toggle_quick.connect(self._on_spell_quick_toggle)
        row.prepared_toggled.connect(self._on_prep_toggled)
        # Restore pinned state
        if spell["name"] in self.char.get("quick_spells",[]):
            row.set_pinned(True)
        ins = self._find_spell_pos(lvl)
        self._my_spells_lay.insertWidget(ins, row)
        self._spell_rows.append(row)
        return row

    def _on_spell_quick_toggle(self, spell_name: str, pinned: bool):
        qs = self.char.setdefault("quick_spells",[])
        if pinned and spell_name not in qs: qs.append(spell_name)
        elif not pinned and spell_name in qs: qs.remove(spell_name)
        # Sync star state on all matching spell rows
        for row in self._spell_rows:
            if row.spell.get("name") == spell_name:
                row.set_pinned(pinned)
        # (_refresh_action_tabs runs once at the end of this method)
        self._mark_dirty()

    def _find_hdr_pos(self, level):
        for i in range(self._my_spells_lay.count()):
            w = self._my_spells_lay.itemAt(i).widget()
            if w in self._level_headers.values():
                lv = next(k for k,v in self._level_headers.items() if v==w)
                if lv > level: return i
        return self._my_spells_lay.count()-1

    def _find_spell_pos(self, level):
        for i in range(self._my_spells_lay.count()-1,-1,-1):
            w = self._my_spells_lay.itemAt(i).widget()
            if isinstance(w,SpellRow) and w.spell["level"]<=level: return i+1
            if w in self._level_headers.values():
                lv = next(k for k,v in self._level_headers.items() if v==w)
                if lv==level: return i+1
        return self._my_spells_lay.count()-1

    def _remove_spell_row(self, row):
        lvl = row.spell["level"]
        name = row.spell["name"]
        self._spell_rows.remove(row)
        self._my_spells_lay.removeWidget(row); row.setParent(None); row.deleteLater()
        if name in self.char.get("spells_known",[]): self.char["spells_known"].remove(name)
        if name in self.char.get("spells_prepared",[]): self.char["spells_prepared"].remove(name)
        if name in self.char.get("quick_spells",[]): self.char["quick_spells"].remove(name)
        if not any(r.spell["level"]==lvl for r in self._spell_rows):
            if lvl in self._level_headers:
                h = self._level_headers.pop(lvl)
                self._my_spells_lay.removeWidget(h); h.setParent(None); h.deleteLater()
        # Was missing: the known/prepared count label never updated on removal,
        # so it looked like the spell was still "counted" even after deletion.
        self._refresh_spell_count_labels()
        self._mark_dirty()

    def _spell_tooltip_text(self, spell: dict) -> str:
        from dnd_app.ui.shared import _spell_tooltip
        text = _spell_tooltip(spell)
        # Agonizing Blast (Eldritch Invocation): the shared tooltip builder
        # has no character context to know about this, so append it here.
        if spell.get("name") == "Eldritch Blast":
            has_agonizing = any("agonizing blast" in i.lower()
                                 for i in self.char.get("eldritch_invocations", []))
            if has_agonizing:
                mod = ability_mod(self.char, _detect_spell_ability(self.char) or "CHA")
                text += f"\n\nAgonizing Blast: each beam deals 1d10{sign(mod)} force."
        return text

    def _has_beast_spells(self) -> bool:
        """Beast Spells (Druid, 18th level): confirmed via research this
        is specifically a Druid class-level threshold, not total
        character level — checks the character's actual Druid class
        level, correctly handling a multiclass Druid who hasn't reached
        18 Druid levels even if their total character level is higher."""
        for c in self.char.get("classes", []):
            if c.get("class") == "Druid" and c.get("level", 0) >= 18:
                return True
        return False

    def _cast_spell_as_ritual(self, spell):
        """Cast a spell as a ritual — no spell slot expended, but it takes
        10 minutes longer than the spell's normal casting time (PHB
        p.201-202). Confirmed this option never existed anywhere before;
        _cast_spell() always expended a slot with no alternative."""
        if self.char.get("_wildshape_active") and not self._has_beast_spells():
            self._toast(f"\U0001f43e Can't cast {spell['name']} while Wild Shaped — "
                        f"revert to your normal form first")
            return
        base_time = spell.get("casting_time", spell.get("cast_time", "1 action"))
        self._toast(f"📜 Cast {spell['name']} as a ritual — no spell slot used, "
                    f"but casting time is {base_time} + 10 minutes.")
        self._mark_dirty()

    def _cast_spell(self, spell):
        if self.char.get("_wildshape_active") and not self._has_beast_spells():
            self._toast(f"\U0001f43e Can't cast {spell['name']} while Wild Shaped — "
                        f"revert to your normal form first")
            return
        lvl = spell["level"]
        is_cantrip = (lvl == 0)
        ct = (spell.get("cast_time") or "1 action").strip().lower()
        bucket = {"1 action": "Action", "bonus action": "Bonus Action",
                  "reaction": "Reaction"}.get(ct)
        # Gate checked up front, before any slot is expended — including
        # for cantrips, since a cantrip cast via bonus action (Shillelagh,
        # or a bonus-action-granting feature like Earth Genasi's Blade
        # Ward) can still be blocked if a leveled spell was already cast
        # via the regular Action that turn.
        if bucket in ("Action", "Bonus Action") and not self._check_bonus_action_spell_rule(is_cantrip, bucket):
            self._toast(f"✖ Can't cast {spell['name']} via {bucket} — casting a spell with a "
                        f"bonus action means the only other spell you can cast this turn is a "
                        f"cantrip")
            return
        if is_cantrip:
            # Cantrips don't expend a slot, but still cost the same
            # action-economy resource as any other spell (most have a
            # 1-action cast time), so this can't return early before
            # that's consumed.
            self._mark_spell_cast_time(spell)
            self._toast(f"✨ Cast {spell['name']} (cantrip — at will)")
            return
        for l in range(lvl, 10):
            bar = self._slot_bars.get(l)
            if bar and bar._max > 0 and bar.get_used() < bar._max:
                bar.set_used(bar.get_used() + 1)
                bar._update_count()
                self._on_slot_change()
                if spell.get("concentration"):
                    start_concentration(self.char, spell["name"])
                    self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
                    self._refresh_concentration()
                self._apply_spell_active_effect(spell)
                self._mark_spell_cast_time(spell)
                self._toast(f"✨ Cast {spell['name']} — slot expended")
                return
        if self._pact_bar._max > 0 and self._pact_bar.get_used() < self._pact_bar._max:
            self._pact_bar.set_used(self._pact_bar.get_used() + 1)
            self._pact_bar._update_count()
            self._on_slot_change()
            if spell.get("concentration"):
                start_concentration(self.char, spell["name"])
                self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
                self._refresh_concentration()
            self._apply_spell_active_effect(spell)
            self._mark_spell_cast_time(spell)
            # A little flavor for Warlocks specifically -- Pact Magic is
            # power borrowed from your patron, unlike an ordinary prepared
            # or known spell slot, so spending one gets its own tiny nod.
            self._toast(f"✨ Cast {spell['name']} — pact slot expended\nYour patron approves.")
            self._mark_dirty()
            return
        self._toast(f"🔒 Can't cast {spell['name']} — no level-{lvl}+ spell slots available")

    def _check_bonus_action_spell_rule(self, is_cantrip: bool, bucket: str) -> bool:
        """The real rule: casting a spell with a bonus action means the
        only other spell castable that turn is a cantrip with a 1-action
        cast time — and this is symmetric regardless of cast order.
        Correctly covers the Earth Genasi Blade Ward case: even though
        Blade Ward is itself a cantrip, casting it via a bonus-action-
        granting feature still counts as "casting a spell with a bonus
        action," which requires whatever was cast via the regular Action
        that turn to also be a cantrip — a leveled spell like Fireball
        violates that regardless of which slot came first."""
        from dnd_app.core.effects import has_extra_action
        if has_extra_action(self.char):
            return True
        if bucket == "Bonus Action":
            if self._action_spell_is_cantrip is False:
                return False
        elif bucket == "Action" and not is_cantrip:
            if self._bonus_action_spell_is_cantrip is not None:
                return False
        return True

    def _mark_spell_cast_time(self, spell):
        """Confirmed a real, reported gap: casting a spell never
        consumed anything from the existing turn-economy tracker (which
        already correctly handles other abilities, including the Haste
        extra-action case). Maps the spell's real cast_time to the
        correct bucket, and correctly skips the tracker entirely for
        longer, out-of-combat casting times that don't fit the per-turn
        economy at all."""
        ct = (spell.get("cast_time") or "1 action").strip().lower()
        is_cantrip = spell.get("level", 1) == 0
        if ct == "1 action":
            self._mark_turn_used("Action")
            self._action_spell_is_cantrip = is_cantrip
        elif ct == "bonus action":
            self._mark_turn_used("Bonus Action")
            self._bonus_action_spell_is_cantrip = is_cantrip
        elif ct == "reaction":
            self._mark_turn_used("Reaction")

    def _action_cat_btn_style(self, active: bool, small: bool = False) -> str:
        fs = FS_TINY if small else FS_SMALL
        pad = "2px 8px" if small else "3px 12px"
        if active:
            return (f"QPushButton{{background:{GOLD};color:{BG};border:1px solid {GOLD};"
                    f"border-radius:5px;font-size:{fs}px;font-weight:700;padding:{pad};}}")
        return (f"QPushButton{{background:{SURF2};color:{TEXT2};border:1px solid {qa(AMBER,0x33)};"
                f"border-radius:5px;font-size:{fs}px;font-weight:600;padding:{pad};}}"
                f"QPushButton:hover{{background:{qa(AMBER,0x22)};color:{AMBE2};}}")

    def _classify_action_entry(self, entry):
        """Confirmed via direct testing: racial trait entries reliably
        use the character's own base race name as their source, so
        matching against that is accurate. Magic Item is a deliberate
        placeholder until that system is properly wired — it currently
        classifies nothing rather than guess inaccurately from
        arbitrary source-name text, per explicit direction."""
        source = entry[2] if len(entry) > 2 else ""
        is_spell = len(entry) > 3 and entry[3] is not None
        if is_spell:
            return "Spell"
        if source and source == self.char.get("race", ""):
            return "Race"
        return "Common"

    def _apply_spell_active_effect(self, spell):
        """Confirmed a real, reported gap: the active_effects system
        already existed (Haste, Bless, Shield of Faith, dozens more with
        real mechanical hooks), but nothing connected actually casting a
        spell to it — the player had to separately, manually re-add the
        same effect through a dropdown after casting it. Self-only
        spells auto-apply with no ambiguity. Spells with a real range
        prompt for self-vs-another, since these buff spells can target
        either, and only adding it to the caster's own sheet is correct
        when they're the actual target."""
        from dnd_app.core.effects import EFFECT_TABLE
        name = spell["name"]
        if name not in EFFECT_TABLE:
            return
        rng = (spell.get("range") or "").strip().lower()
        is_self_only = rng == "self" or rng.startswith("self (") or rng.startswith("self(")
        if is_self_only:
            target_self = True
        else:
            reply = QMessageBox.question(
                self, name, f"Cast {name} on yourself, or on another creature?\n\n"
                f"(Choose \"No\" if targeting someone else — it won't be added to your own "
                f"Active Effects.)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            target_self = (reply == QMessageBox.Yes)
        if target_self:
            fx = self.char.setdefault("active_effects", [])
            if name not in fx:
                fx.append(name)
                self.ctrl.refresh()
                self._refresh_effects_list()
                self._apply_turn_state()
                self._toast(f"☄ {name} added to Active Effects")

    def _drop_concentration(self):
        drop_concentration(self.char)
        self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
        self._refresh_concentration()

    def _prompt_concentration_save(self):
        if not self.char.get("concentration", {}).get("spell"):
            QMessageBox.information(self, "Concentration", "Not concentrating on a spell.")
            return
        dmg, ok = QInputDialog.getInt(self, "Concentration Save", "Damage taken this turn:", 10, 0, 999)
        if not ok:
            return
        roll, ok_roll = QInputDialog.getInt(
            self, "Concentration Save",
            "Enter your d20 roll (CON modifier applied automatically):",
            10, 1, 30,
        )
        if not ok_roll:
            return
        from dnd_app.core.calculator import get_saving_throw_bonus
        dc = max(10, dmg // 2)
        total = roll + get_saving_throw_bonus(self.char, "CON")
        if total >= dc:
            QMessageBox.information(self, "Concentration", f"Maintained ({total} vs DC {dc})")
        else:
            drop_concentration(self.char)
            self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
            QMessageBox.warning(self, "Concentration", f"Failed ({total} vs DC {dc}) — concentration dropped.")
            self._toast("Your focus shatters like cheap glass.")
        self._refresh_concentration()
        self._mark_dirty()

    def _refresh_concentration(self):
        spell = self.char.get("concentration", {}).get("spell")
        if spell:
            self._conc_lbl.setText(spell)
            self._conc_lbl.setToolTip(spell)
            self._conc_lbl.setStyleSheet(
                f"color:{AMBER};font-size:{FS_BODY}px;font-weight:700;background:transparent;"
            )
        else:
            self._conc_lbl.setText("—")
            self._conc_lbl.setToolTip("")
            self._conc_lbl.setStyleSheet(f"color:{TEXT2};font-size:{FS_BODY}px;background:transparent;")
        if hasattr(self, "_combat_conc_lbl"):
            if spell:
                self._combat_conc_lbl.setText(f"🎯 Concentrating: {spell}")
                self._combat_conc_lbl.setToolTip(f"{spell} — manage/drop concentration from the Spells tab.")
                self._combat_conc_lbl.setVisible(True)
            else:
                self._combat_conc_lbl.setVisible(False)

    def _on_slot_change(self):
        self.char["spell_slots_used"] = [self._slot_bars[i].get_used() for i in range(1, 10)]
        self.char["pact_slots_used"] = self._pact_bar.get_used()
        self._mark_dirty()

    # ══ TAB 5: FEATURES ════════════════════════════════════════════════════════
    def _build_tab_features(self):
        tab = QScrollArea(); tab.setWidgetResizable(True)
        w = QWidget(); tab.setWidget(w)
        self._feat_tab_lay = QVBoxLayout(w); self._feat_tab_lay.setContentsMargins(16,16,16,16); self._feat_tab_lay.setSpacing(12)
        self._feat_sections = []   # (groupbox, content_lay)
        self._feat_tab_lay.addStretch()
        return tab

    @staticmethod
    def _get_subclass_feature_names(cname, subclass_display, D):
        """Parse actual feature names from the subclass data string.
        
        Subclass strings look like:
          'The Archfey – Fey Presence; Misty Escape; Beguiling Defenses'
        Features after '–' are mapped in order to subclass feature slots.
        """
        if not subclass_display:
            return []
        cdata = D.get(cname, {})
        # Find matching subclass entry (display name match)
        sub_display_norm = subclass_display.lower().strip()
        for sub_full in cdata.get("subclasses", []):
            disp = sub_full.split("–")[0].split("—")[0].strip().lower()
            if disp == sub_display_norm or sub_display_norm in disp or disp in sub_display_norm:
                # Found it — parse features after the dash
                if "–" in sub_full:
                    feat_str = sub_full.split("–", 1)[1]
                elif "—" in sub_full:
                    feat_str = sub_full.split("—", 1)[1]
                else:
                    return []
                return [f.strip() for f in feat_str.split(";") if f.strip()]
        return []

    def _rebuild_features(self):
        lay = self._feat_tab_lay
        while lay.count():
            item = lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        # _add_feature_section() inserts each new section at count()-1, i.e.
        # "just before the last item" — which only produces the intended
        # top-to-bottom order (Race, then Ancestry, then Subrace, then each
        # class...) if a stable trailing placeholder already exists before
        # the FIRST section is added. Without one, count()-1 on an empty
        # layout is -1 (Qt appends at the end — fine for the first section),
        # but then count()-1 on a 1-item layout is 0, which inserts BEFORE
        # that first section instead of after it. Re-adding this stretch
        # here (not just once at initial tab construction) is what keeps
        # every rebuild — not only the first one — in the right order.
        lay.addStretch()

        cls_colors = [IND2, PURP2, AMBE2, TEAL2, CRIM2, GOLD2]
        D = CLASS_DICT

        # Race features
        race = self.char.get("species") or self.char.get("race","")
        if race:
            rdata = get_race(race)
            if rdata and rdata.get("traits"):
                display_traits = rdata["traits"]
                # If the active subrace carries its OWN ability score bonus
                # (Dragonmarks, etc.), it fully REPLACES the base race's ASI
                # per builder.py's actual math — so don't show a contradictory
                # "+1 to all six ability scores"-style line alongside it.
                subrace_now = self.char.get("subrace", "")
                if subrace_now:
                    from dnd_app.core.builder import _get_subrace_asi
                    if _get_subrace_asi(race, subrace_now):
                        _asi_line = re.compile(
                            r'^\s*\+\d.*\b(ability scores?|STR|DEX|CON|INT|WIS|CHA)\b',
                            re.IGNORECASE)
                        display_traits = [t for t in display_traits if not _asi_line.match(t)]
                # Only add the section if there's still something left to
                # show — the check above (rdata.get("traits")) only looked
                # at the UNFILTERED list, so a race whose traits happened to
                # be entirely ASI-only would pass that check but then call
                # _add_feature_section with an empty list here, producing a
                # section with nothing in it (or none at all, depending on
                # how that function handles empty items) sitting above
                # Subrace — which is what "subrace displaying before race"
                # would actually look like, even though the add order was
                # correct the whole time.
                if display_traits:
                    self._add_feature_section(f"Race: {race}", TEAL2, display_traits,
                                              badge_color=TEAL2)
            # Draconic ancestry trait (Dragonborn)
            if race == "Dragonborn":
                anc = self.char.get("draconic_ancestry","")
                if anc:
                    try:
                        from dnd_app.data.races import DRACONIC_ANCESTRY
                        anc_data = DRACONIC_ANCESTRY.get(anc)
                        if anc_data:
                            dmg, shape, desc = anc_data
                            self._add_feature_section(
                                f"Draconic Ancestry: {anc}", GOLD2,
                                [f"Damage type: {dmg}  ·  Breath shape: {shape}",
                                 f"Breath Weapon: 2d6 (3d6 Lv6, 4d6 Lv11, 5d6 Lv16)  ·  {desc}",
                                 f"Resistance: {dmg} damage"],
                                badge_color=GOLD2)
                    except ImportError: pass
            # Subrace traits
            subrace = self.char.get("subrace","")
            if subrace and rdata:
                import re as _re_sub
                for sub_str in rdata.get("subraces",[]):
                    sub_name=sub_str.split("(")[0].strip()
                    if sub_name==subrace:
                        inner=sub_str[sub_str.find("(")+1:sub_str.rfind(")")]
                        # Strip leading "+ABC N" ASI clauses (shown elsewhere),
                        # one at a time, from the front of the string.
                        asi_pat = _re_sub.compile(r"^\s*[+][A-Z]{3}\s+\d+\s*,?\s*")
                        remainder = inner
                        while True:
                            m = asi_pat.match(remainder)
                            if not m: break
                            remainder = remainder[m.end():]
                        # Some traits (Eladrin's seasonal Fey Step, Shadar-kai's
                        # Blessing, etc.) contain commas WITHIN a single trait's
                        # description. A blind comma-split shreds those into
                        # meaningless fragments. If the remainder contains a
                        # semicolon, treat semicolons as the trait boundary
                        # instead (preserving internal commas); otherwise fall
                        # back to the original comma-split for simple lists.
                        #
                        # Also strip a trailing sourcebook tag (", ERLW)",
                        # ", SCAG)", etc.) — without this it survives the
                        # comma-split and renders as its own meaningless row
                        # (e.g. a feature row that just says "ERLW").
                        _SOURCE_TAGS = {"PHB","XGE","TCE","SCAG","MTOF","FTD","EGW",
                                        "ERLW","VRGTR","BGG","MOT","DSOTDQ","WBTW","GGR"}
                        remainder = remainder.strip().rstrip(",").strip()
                        _last_comma = remainder.rfind(",")
                        if _last_comma >= 0:
                            _tail = remainder[_last_comma+1:].strip()
                            if _tail.upper().replace("/", "") in _SOURCE_TAGS:
                                remainder = remainder[:_last_comma].strip()
                        if ";" in remainder:
                            parts = [p.strip() for p in remainder.split(";") if p.strip()]
                        else:
                            parts = [p.strip() for p in remainder.split(",") if p.strip()]
                        if parts:
                            self._add_feature_section(
                                f"Subrace: {subrace}", TEAL, parts, badge_color=TEAL)
                        break

        # Background feature
        bg = get_background(self.char.get("background",""))
        if bg and bg.get("feature"):
            self._add_feature_section(f"Background: {self.char.get('background','')}", GOLD,
                                      [f"{bg['feature']}: {bg.get('feature_desc','')}"],
                                      badge_color=GOLD)

        # Per-class features
        for ci, c in enumerate(self.char.get("classes",[])):
            cname = c["class"]; clvl = c["level"]; sub = c.get("subclass","")
            color = cls_colors[ci % len(cls_colors)]
            title = f"{cname}" + (f" — {sub}" if sub else "") + f"  (Level {clvl})"
            feats = []
            cdata = D.get(cname, {}); features = cdata.get("features",{})

            # Load proper subclass feature names from SUBCLASS_FEATURES
            try:
                from dnd_app.data.class_features import SUBCLASS_FEATURES, CLASS_FEATURE_INDEX
                proper_names = SUBCLASS_FEATURES.get((cname, sub), [])
            except ImportError:
                proper_names = []
                CLASS_FEATURE_INDEX = {}
            # Fall back to parsed summary names from CLASS_DICT
            if not proper_names:
                proper_names = self._get_subclass_feature_names(cname, sub, D)
            sub_feat_idx = 0  # pointer into proper names

            # VERIFIED, LEVEL-KEYED override: if this (class, subclass) has
            # been properly indexed in CLASS_FEATURE_INDEX with real,
            # sourced levels (not just a flat unordered list), use that
            # directly instead of the fragile placeholder-position-counting
            # below — the positional system silently misassigns levels any
            # time the number of generic "Archetype Feature"-style
            # placeholders in classes.py's per-level table doesn't exactly
            # match the length of SUBCLASS_FEATURES' flat list (see class_feature_index.py).
            _sub_index = CLASS_FEATURE_INDEX.get(cname, {}).get(sub)
            _has_verified_levels = isinstance(_sub_index, dict)
            if _has_verified_levels:
                for lvl in sorted(_sub_index):
                    if lvl > clvl:
                        break
                    for real_name in _sub_index[lvl]:
                        feats.append(f"[Lv {lvl}]  {sub}: {real_name}")

            if not _has_verified_levels:
                for lvl in range(1, clvl+1):
                    for fname in features.get(lvl, []):
                        is_sub_slot = any(kw in fname.lower() for kw in [
                            'subclass feature', 'archetype feature', 'domain feature',
                            'circle feature', 'sacred oath feature', 'primal path feature',
                            'order feature', 'college feature', 'ranger archetype feature',
                            'ranger archetype', '(subclass)', 'martial archetype',
                            'roguish archetype', 'sorcerous origin', 'otherworldly patron',
                            'divine domain', 'druid circle', 'monastic tradition',
                            'primal path', 'bardic college', 'arcane tradition',
                            'sacred oath', 'ranger conclave', 'alchemical homunculus',
                            'path feature',       # Barbarian Path Feature at Lv6/10/14
                            'sacred oath feature', # Paladin oath feature at Lv7/15/20
                            'bard college feature', # Bard college feature at Lv6/14
                            'ki feature',          # Monk ki features
                        ])
                        if is_sub_slot:
                            # Some slot markers are explicitly optional ("some
                            # domains grant a second 1st-level feature") — only
                            # treat them as real if this subclass's feature list
                            # is actually long enough to have that extra entry.
                            # Baseline is 5 (the normal single-1st-level-feature
                            # count for Cleric domains); domains with a genuine
                            # second 1st-level feature provide 6+ and so do
                            # consume this slot. Without this check, domains
                            # with only 5 features had every feature after 1st
                            # level shift one slot early, ending in a blank
                            # placeholder at the final level.
                            is_optional_slot = "second 1st-level feature" in fname.lower()
                            if is_optional_slot and len(proper_names) <= 5:
                                continue  # phantom slot — this domain doesn't have one
                            if sub and sub_feat_idx < len(proper_names):
                                real_name = proper_names[sub_feat_idx]
                                sub_feat_idx += 1
                                feats.append(f"[Lv {lvl}]  {sub}: {real_name}")
                            elif sub:
                                sub_feat_idx += 1
                                feats.append(f"[Lv {lvl}]  {sub} — Subclass Feature")
                            else:
                                feats.append(f"[Lv {lvl}]  {fname}")
                        else:
                            feats.append(f"[Lv {lvl}]  {fname}")

            # Add invocations
            invocs = self.char.get("eldritch_invocations", [])
            if cname == "Warlock" and invocs:
                feats.append(f"[Invocations]  " + ", ".join(
                    i.split("–")[0].strip() for i in invocs))

            # Totem Warrior: once the 3rd-level Totem Spirit choice has
            # actually been made, replace the generic "Totem Spirit" line
            # (which otherwise always lists all three options — Bear/Eagle/
            # Wolf — with no indication of which one this character has)
            # with the specific animal and its real effect text.
            if cname == "Barbarian" and "totem" in sub.lower():
                totem_pick = self.char.get("_choices", {}).get("totem_spirit_3", [])
                if totem_pick:
                    pick_text = totem_pick[0]
                    animal = pick_text.split("–")[0].split("-")[0].strip()
                    for _i, _f in enumerate(feats):
                        if _f.rstrip().endswith("Totem Spirit"):
                            feats[_i] = f"{_f} ({animal}) – {pick_text.split('–',1)[-1].strip() if '–' in pick_text else pick_text}"
                            break

            # Add metamagic
            metamagic = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
            if cname == "Sorcerer" and metamagic:
                feats.append(f"[Metamagic]  " + ", ".join(
                    m.split("–")[0].strip() for m in metamagic))

            # Add infusions
            infusions = self.char.get("artificer_infusions", [])
            if cname == "Artificer" and infusions:
                feats.append(f"[Infusions]  " + ", ".join(
                    i.split("–")[0].strip() for i in infusions))

            # Add battle master maneuvers
            maneuvers = self.char.get("battle_master_maneuvers", [])
            if cname == "Fighter" and "battle master" in sub.lower() and maneuvers:
                feats.append(f"[Maneuvers]  " + ", ".join(
                    m.split("–")[0].strip() for m in maneuvers))

            # Fix Indomitable display - show uses count clearly
            if cname == "Fighter":
                uses = 1 if clvl >= 9 else 0
                if clvl >= 13: uses = 2
                if clvl >= 17: uses = 3
                # Replace the plain feature text with a clearer version
                feats = [f if "Indomitable" not in f
                         else f"[Lv {([lvl for lvl in [9,13,17] if lvl<=clvl] or [0])[-1]}]  Indomitable — Reroll failed save ({uses}/Long Rest)"
                         for f in feats]

            if feats:
                self._add_feature_section(title, color, feats, badge_color=color)

        # Chosen feats
        feat_items = []
        for fname in self.char.get("feats",[]):
            fd = get_feat(fname)
            if fd:
                chosen_ab = self.char.get("_choices", {}).get(f"feat_ability_{fname.lower().replace(' ','_')}")
                prefix = f"{chosen_ab}-based — " if chosen_ab else ""
                summary = self._summarize_feature_text(fd.get('special', ''))
                feat_items.append(f"{fname}: {prefix}{summary}")
        if feat_items:
            self._add_feature_section("Feats", PURP2, feat_items, badge_color=PURP2)

        # Fighting Style is fully stored and mechanically wired (drives
        # real attack/damage bonuses), but is displayed here for visibility in the Features tab.
        fs_items = self.char.get("fighting_styles", [])
        if fs_items:
            self._add_feature_section("Fighting Style", TEAL2, list(fs_items), badge_color=TEAL2)

        # Battle Master maneuvers
        maneuvers = self.char.get("battle_master_maneuvers",[])
        if maneuvers:
            from dnd_app.core.calculator import get_superiority_die
            import re as _re_sd
            sd = get_superiority_die(self.char)
            maneuvers = [_re_sd.sub(r'\bSD\b', sd, m) for m in maneuvers]
            self._add_feature_section("Battle Master Maneuvers", AMBE2, maneuvers, badge_color=AMBE2)

        # Wild Magic surge table
        # Wild Magic: check if any Sorcerer has Wild Magic subclass stored
        # Both Wild Magic tables if multiclassing both
        wm_sorc = any(c.get("class")=="Sorcerer" and "wild magic" in c.get("subclass","").lower()
                      for c in self.char.get("classes",[]))
        wm_barb = any(c.get("class")=="Barbarian" and "wild magic" in c.get("subclass","").lower()
                      for c in self.char.get("classes",[]))
        # Also from _choices
        for cn,v in self.char.get("_choices",{}).items():
            if "subclass" in cn.lower() and isinstance(v,list) and v:
                val=str(v[0]).lower()
                if "wild magic" in val:
                    if "sorcerer" in cn.lower(): wm_sorc=True
                    if "barbarian" in cn.lower(): wm_barb=True
        if wm_sorc: self._add_wild_magic_section(barb=False)
        if wm_barb: self._add_wild_magic_section(barb=True)

        # Eldritch Invocations
        invocs = self.char.get("eldritch_invocations",[])
        if invocs:
            self._add_feature_section("Eldritch Invocations", PURP2, invocs, badge_color=PURP2)

        # Metamagic (only the options actually chosen — never the full pool)
        metamagic = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
        if metamagic:
            self._add_feature_section("Metamagic", PURP2, metamagic, badge_color=PURP2)

        # Blood Curses Known (Blood Hunter) — only the ones actually chosen
        blood_curses = self.char.get("_choices", {}).get("blood_hunter_curses", [])
        if blood_curses:
            self._add_feature_section("Blood Curses Known", CRIM2, blood_curses, badge_color=CRIM2)

        # Mutagen Formulas Known (Blood Hunter, Order of the Mutant)
        mutagens = self.char.get("_choices", {}).get("blood_hunter_mutagens", [])
        if mutagens:
            self._add_feature_section("Mutagen Formulas Known", CRIM2, mutagens, badge_color=CRIM2)

        # Elemental Disciplines (Way of the Four Elements)
        disciplines = self.char.get("_choices", {}).get("four_elements_disciplines", [])
        if disciplines:
            self._add_feature_section("Elemental Disciplines", PURP2, disciplines, badge_color=PURP2)

        # Replicated Magic Items (Artificer): the real rule requires
        # explicitly learning each one as its own "Replicate Magic
        # Item" infusion pick, consuming an infusions-known slot — not
        # every item across every tier the character's level qualifies
        # for. Shows only the specific items the character has actually learned.
        from dnd_app.core.character import class_levels as _cls_lvls_repl
        art_lvl = _cls_lvls_repl(self.char).get("Artificer", 0)
        if art_lvl >= 2:
            from dnd_app.data.classes import ARTIFICER_REPLICABLE_ITEMS
            all_replicable_names = {name for tier_items in ARTIFICER_REPLICABLE_ITEMS.values()
                                     for name, _ in tier_items}
            known_infusions = self.char.get("artificer_infusions", [])
            learned_replicated = [inf.split(" \u2013 ")[0].strip() for inf in known_infusions
                                   if inf.split(" \u2013 ")[0].strip() in all_replicable_names]
            if learned_replicated:
                attunement_lookup = {name: att for tier_items in ARTIFICER_REPLICABLE_ITEMS.values()
                                      for name, att in tier_items}
                display_items = [f"{name} (requires attunement)" if attunement_lookup.get(name) else name
                                 for name in learned_replicated]
                self._add_feature_section("Replicated Magic Items (learned)", TEAL2, display_items, badge_color=TEAL2)

                # ── Optional / Alternate Class Features (TCoE) ──────────────────────
        try:
            from dnd_app.data.class_features import OPTIONAL_CLASS_FEATURES as _OPT
        except ImportError:
            _OPT = {}
        _enabled = self.char.get("_choices",{}).get("optional_features",{})
        _rules = self.char.get("optional_rules", {})
        for _ce in self.char.get("classes",[]):
            _cn=_ce.get("class",""); _cl=_ce.get("level",1)
            _cls_opts=_OPT.get(_cn,{}); _items=[]
            for _ul,_fl in sorted(_cls_opts.items()):
                if _ul>_cl: continue
                for _f in _fl:
                    # Some optional features (Harness Divine Power) have
                    # a Settings-popup toggle; others (Martial
                    # Versatility, Deft Explorer, etc.) only have this
                    # per-feature one. Checks both, so a feature enabled
                    # through either mechanism is recognized consistently.
                    _rules_key = _f["name"].lower().replace(" ", "_")
                    if _enabled.get(_f["name"],False) or _rules.get(_rules_key, False):
                        _rep=_f.get("replaces")
                        _tag=f"(replaces {_rep})" if _rep else "(TCoE optional)"
                        _items.append(f"[Lv{_ul}]  {_f['name']} {_tag}")
            if _items:
                self._add_feature_section(f"✦ Optional — {_cn}","#E8A020",_items,badge_color="#E8A020")

        # ── DM-Granted Feats Browser ─────────────────────────────────────────
        from dnd_app.data.feats import ALL_FEATS, get_feat as _get_feat
        # Show any already-granted feats
        granted = self.char.get("dm_feats", [])
        if granted:
            feat_items = []
            for fname in granted:
                ft = _get_feat(fname)
                if ft:
                    src_tag = ft.get("source","")
                    pre = ft.get("prereq","")
                    desc = self._summarize_feature_text(ft.get("special",""), max_len=180)
                    feat_items.append(
                        f"<b>{fname}</b>  [{src_tag}]"
                        + (f"  <i>Req: {pre}</i>" if pre else "")
                        + (f"<br>{desc}" if desc else "")
                    )
                else:
                    feat_items.append(fname)
            self._add_feature_section("✦  DM-Granted Feats", AMBER, feat_items, badge_color=AMBER)

        # Show any already-granted DM rewards (Character Secrets / narrative
        # bonus features) — same pattern as DM-Granted Feats above, so a
        # granted reward actually appears on the sheet, not just as a
        # checkmark in the browser below.
        from dnd_app.data.dm_rewards import get_dm_reward as _get_dm_reward
        granted_rewards = self.char.get("dm_rewards", [])
        if granted_rewards:
            reward_items = []
            for rname in granted_rewards:
                rw = _get_dm_reward(rname)
                if rw:
                    pre = rw.get("prereq","")
                    # NOT _summarize_feature_text() here, unlike DM-Granted
                    # Feats above -- DM Rewards (Supernatural Gifts, Dark
                    # Gifts, Iconoclast's tiers, etc.) routinely run several
                    # paragraphs, and a max_len=180 summary truncated mid-
                    # sentence with no way to see the rest: the row label
                    # has no height cap (it just grows), and the right-click
                    # "Show Details" fallback reuses this same string when
                    # there's no separate FEATURE_DESCS lookup for a DM
                    # reward's custom name -- so a truncated summary here
                    # was truncated everywhere, with no path to the full
                    # text at all. _format_multi_para() renders the real
                    # paragraph breaks and bolds each trait's name, same as
                    # the feat browser's detail panel does for these.
                    desc = self._format_multi_para(rw.get("desc",""))
                    cat = rw.get("category",""); src = rw.get("source","")
                    tag = f"{cat} \u2014 {src}" if cat else ""
                    reward_items.append(
                        f"<b>{rname}</b>"
                        + (f"  <i>[{tag}]</i>" if tag else "")
                        + (f"  <i>Req: {pre}</i>" if pre else "")
                        + (f"<br>{desc}" if desc else "")
                    )
                else:
                    reward_items.append(rname)
            self._add_feature_section("✦  DM-Granted Bonus Features", AMBER, reward_items, badge_color=AMBER)

        # Feat browser card — always visible at bottom
        fb_card = QFrame()
        fb_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {qa(AMBER,0x44)};border-radius:10px;}}")
        fb_cl = QVBoxLayout(fb_card)
        fb_cl.setContentsMargins(12, 10, 12, 10); fb_cl.setSpacing(6)

        # Header row
        fb_hdr = QHBoxLayout()
        fb_hdr.addWidget(_lbl("✦  BONUS FEATURE BROWSER  —  DM Rewards", AMBER, FS_SMALL, bold=True))
        fb_hdr.addStretch()
        fb_hdr.addWidget(_lbl("Double-click or click Add to grant a feat outside class progression",
                               TEXT3, FS_TINY, wrap=False))
        fb_cl.addLayout(fb_hdr)

        # Search + list row
        fb_body = QHBoxLayout(); fb_body.setSpacing(8)

        # Left: search + category filter + list
        fb_left = QVBoxLayout(); fb_left.setSpacing(4)
        fb_search_row = QHBoxLayout(); fb_search_row.setSpacing(6)
        fb_search = QLineEdit(); fb_search.setPlaceholderText("Search feats…")
        fb_search.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;font-size:{FS_SMALL}px;}}"
            f"QLineEdit:focus{{border-color:{AMBER};}}")
        fb_search_row.addWidget(fb_search, 2)
        from dnd_app.data.dm_rewards import DM_REWARD_CATEGORIES
        fb_type_filter = QComboBox()
        fb_type_filter.addItems(DM_REWARD_CATEGORIES)
        fb_type_filter.setStyleSheet(
            f"QComboBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;font-size:{FS_SMALL}px;}}")
        fb_type_filter.setToolTip("Filter by feature type")
        fb_search_row.addWidget(fb_type_filter, 1)
        fb_left.addLayout(fb_search_row)

        fb_list = QListWidget()
        fb_list.setMaximumHeight(200)
        fb_list.setStyleSheet(
            f"QListWidget{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;"
            f"color:{TEXT};font-size:{FS_SMALL}px;}}"
            f"QListWidget::item{{padding:3px 8px;}}"
            f"QListWidget::item:selected{{background:{qa(AMBER,0x88)};color:white;}}"
            f"QListWidget::item:hover:!selected{{background:{SURF3};}}")
        from dnd_app.data.feature_tooltips import FEATURE_DESCS as _FEAT_DESCS
        for ft in ALL_FEATS:
            already = ft["name"] in self.char.get("dm_feats", [])
            item = QListWidgetItem(("✓ " if already else "") + ft["name"])
            item.setData(Qt.UserRole, ft["name"])
            item.setData(Qt.UserRole + 1, "feat")
            item.setData(Qt.UserRole + 2, "Feat")
            prereq = ft.get("prereq","")
            source = ft.get("source","")
            # Full detail from FEATURE_DESCS for the tooltip, falling back to
            # the feature-bar's short special[:250] snippet only if a feat
            # somehow has no dedicated tooltip entry.
            desc = _FEAT_DESCS.get(ft["name"]) or ft.get("special","")[:250]
            item.setToolTip(
                f"<b>{ft['name']}</b>  [{source}]"
                + (f"<br><i>Requires: {prereq}</i>" if prereq else "")
                + (f"<br>{desc}" if desc else ""))
            if already:
                item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(AMBER))
            fb_list.addItem(item)

        # DM Rewards ("Character Secrets" / narrative bonus features) — same
        # list, distinguished by a 🔮 marker and the second data role, since
        # these are a genuinely different kind of content (mostly narrative
        # hooks with occasional mechanical traits) than standard feats.
        from dnd_app.data.dm_rewards import ALL_DM_REWARDS
        for rw in ALL_DM_REWARDS:
            already_rw = rw["name"] in self.char.get("dm_rewards", [])
            item = QListWidgetItem(("✓ " if already_rw else "") + "🔮 " + rw["name"])
            item.setData(Qt.UserRole, rw["name"])
            item.setData(Qt.UserRole + 1, "dm_reward")
            item.setData(Qt.UserRole + 2, rw.get("category", ""))
            prereq = rw.get("prereq","")
            desc = self._summarize_feature_text(rw.get("desc",""), max_len=250).replace("\n\n", "<br><br>").replace("\n", "<br>")
            cat = rw.get("category",""); src = rw.get("source","")
            tag = f"{cat} \u2014 {src}" if cat else ""
            item.setToolTip(
                f"<b>{rw['name']}</b>" + (f"  <i>[{tag}]</i>" if tag else "")
                + (f"<br><i>Requires: {prereq}</i>" if prereq else "")
                + (f"<br>{desc}" if desc else ""))
            if already_rw:
                item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(AMBER))
            fb_list.addItem(item)

        def _filter_feats(_arg=None, lst=fb_list, search=fb_search, type_filter=fb_type_filter):
            text = search.text()
            selected_cat = type_filter.currentText()
            for i in range(lst.count()):
                it = lst.item(i)
                raw = it.data(Qt.UserRole) or it.text()
                cat = it.data(Qt.UserRole + 2) or ""
                text_ok = text.lower() in raw.lower()
                cat_ok = selected_cat == "All Types" or cat == selected_cat
                it.setHidden(not (text_ok and cat_ok))
        fb_search.textChanged.connect(_filter_feats)
        fb_type_filter.currentTextChanged.connect(_filter_feats)
        fb_left.addWidget(fb_list)
        fb_body.addLayout(fb_left, 3)

        # Right: info + add/remove buttons
        fb_right = QVBoxLayout(); fb_right.setSpacing(6)
        # Wrapped in a QScrollArea with a taller viewport rather than a
        # fixed-height QLabel, so a long entry (any DM Reward with more
        # than a couple sentences — Supernatural Gifts, Dark Gifts, and
        # Iconoclast's tiers routinely run several paragraphs) scrolls
        # rather than getting clipped with no way to reach the rest.
        fb_info = QLabel("Select a feat to see details.")
        fb_info.setWordWrap(True)
        fb_info.setStyleSheet(
            f"QLabel{{color:{TEXT2};font-size:{FS_SMALL}px;background:{SURF2};padding:8px;}}")
        fb_info.setMinimumWidth(220)
        fb_info_scroll = QScrollArea()
        fb_info_scroll.setWidget(fb_info)
        fb_info_scroll.setWidgetResizable(True)
        fb_info_scroll.setStyleSheet(
            f"QScrollArea{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;}}")
        fb_info_scroll.setMinimumHeight(120); fb_info_scroll.setMaximumHeight(280)
        fb_right.addWidget(fb_info_scroll)

        def _on_feat_select(item, info=fb_info):
            if not item: return
            fname = item.data(Qt.UserRole) or item.text().lstrip("✓ ")
            item_type = item.data(Qt.UserRole + 1) or "feat"
            if item_type == "dm_reward":
                from dnd_app.data.dm_rewards import get_dm_reward as _gdr2
                rw = _gdr2(fname)
                if rw:
                    pre = rw.get("prereq","")
                    cat = rw.get("category",""); src = rw.get("source","")
                    tag = f"{cat} \u2014 {src}" if cat else ""
                    info.setText(
                        f"<b>{fname}</b>" + (f"  <i>[{tag}]</i>" if tag else "")
                        + (f"<br><span style='color:{AMBER};'>Requires: {pre}</span>" if pre else "")
                        + f"<br><br>{self._format_multi_para(rw.get('desc',''))}")
                return
            from dnd_app.data.feats import get_feat as _gf2
            from dnd_app.data.feature_tooltips import FEATURE_DESCS as _FEAT_DESCS2
            ft = _gf2(fname)
            if ft:
                pre = ft.get("prereq",""); src_tag=ft.get("source","")
                full_desc = _FEAT_DESCS2.get(fname) or ft.get('special','')
                info.setText(
                    f"<b>{fname}</b>  <i>[{src_tag}]</i>"
                    + (f"<br><span style='color:{AMBER};'>Requires: {pre}</span>" if pre else "")
                    + f"<br><br>{self._format_multi_para(full_desc)}")
        fb_list.currentItemChanged.connect(lambda cur,prev: _on_feat_select(cur))

        btn_add = QPushButton("＋  Grant Feat")
        btn_add.setStyleSheet(
            f"QPushButton{{background:{qa(AMBER,0x33)};border:1px solid {AMBER};border-radius:6px;"
            f"color:{AMBER};font-size:{FS_SMALL}px;font-weight:700;padding:6px 12px;}}"
            f"QPushButton:hover{{background:{AMBER};color:{BG};}}")
        btn_rem = QPushButton("✕  Remove")
        btn_rem.setStyleSheet(
            f"QPushButton{{background:{qa(CRIMSON,0x22)};border:1px solid {qa(CRIMSON,0x55)};border-radius:6px;"
            f"color:{CRIM2};font-size:{FS_SMALL}px;font-weight:700;padding:6px 12px;}}"
            f"QPushButton:hover{{background:{CRIMSON};color:white;}}")

        def _grant_feat(lst=fb_list):
            item = lst.currentItem()
            if not item: return
            fname = item.data(Qt.UserRole) or item.text().lstrip("✓ ")
            item_type = item.data(Qt.UserRole + 1) or "feat"
            field = "dm_rewards" if item_type == "dm_reward" else "dm_feats"
            granted_list = self.char.setdefault(field, [])
            if fname not in granted_list:
                granted_list.append(fname)
                self._rebuild_features()
                self._mark_dirty()

        def _remove_feat(lst=fb_list):
            item = lst.currentItem()
            if not item: return
            fname = item.data(Qt.UserRole) or item.text().lstrip("✓ ")
            item_type = item.data(Qt.UserRole + 1) or "feat"
            field = "dm_rewards" if item_type == "dm_reward" else "dm_feats"
            granted_list = self.char.get(field, [])
            if fname in granted_list:
                granted_list.remove(fname)
                self._rebuild_features()
                self._mark_dirty()

        btn_add.clicked.connect(lambda _: _grant_feat())
        btn_rem.clicked.connect(lambda _: _remove_feat())
        fb_list.itemDoubleClicked.connect(lambda item: _grant_feat())

        fb_right.addWidget(btn_add)
        fb_right.addWidget(btn_rem)
        fb_right.addStretch()
        fb_body.addLayout(fb_right, 1)
        fb_cl.addLayout(fb_body)
        lay.addWidget(fb_card)

        lay.addStretch()

    @staticmethod
    def _inject_ability_modifier(item_str: str, char: dict) -> str:
        """Resolve '+STAT' placeholders — see calculator.resolve_stat_placeholders
        for the exact rules (shared with the level-up preview panel so
        every surface reads the same way)."""
        from dnd_app.core.calculator import resolve_stat_placeholders
        return resolve_stat_placeholders(item_str, char)

    @staticmethod
    def _summarize_feature_text(text: str, max_len: int = 110) -> str:
        """Short summary for a Features tab row label — the full text
        stays available via the existing tooltip/right-click detail
        view, so this is purely about not dumping an entire paragraph
        of rules text inline. Strips a leading boilerplate ASI clause
        (e.g. "+1 INT/WIS/CHA (max 20)." — present in most 2024-style
        feats and not itself the feature's actual unique mechanic),
        then truncates the remainder at a clean word boundary."""
        import re
        t = text.strip()
        # Strip a leading "+N ABILITY[/ABILITY...] (max 20)." clause.
        t = re.sub(r'^\+\d+\s+[A-Z]{3}(?:/[A-Z]{3})*\s*\(max\s*20\)\.\s*', '', t)
        if len(t) <= max_len:
            return t
        cut = t[:max_len]
        last_space = cut.rfind(' ')
        if last_space > max_len * 0.6:
            cut = cut[:last_space]
        return cut.rstrip('.,;: ') + '…'

    @staticmethod
    def _format_multi_para(text: str) -> str:
        """Format a long, multi-ability description (DM rewards like
        Supernatural Gifts, Dark Gifts, Iconoclast's tiers, etc.) for
        an HTML-rendered popup. Confirmed a real, guaranteed crash —
        this was called but never defined. Two real problems fixed:
        (1) the source text has real '\\n\\n' paragraph breaks, but
        plain newlines are silently collapsed by Qt's HTML rendering,
        producing one unreadable wall of text; (2) each distinct
        ability starts with "Trait Name. description..." (originally
        markdown bold, flattened to plain text during parsing) — these
        are re-bolded so each ability reads as its own clearly
        separated block instead of blending into running prose."""
        import re
        if not text:
            return ""
        paras = [p.strip() for p in text.split('\n\n') if p.strip()]
        out_paras = []
        for p in paras:
            # "Trait Name. rest of description" at the start of a
            # paragraph — re-bold just the name, not the whole
            # paragraph. Matches a short (1-6 word), capitalized
            # phrase followed by a period and a space.
            m = re.match(r'^([A-Z][A-Za-z\'\u2019 ]{1,50}?)\.\s+(.*)$', p, re.DOTALL)
            if m and len(m.group(1).split()) <= 6:
                p = f"<b>{m.group(1)}.</b> {m.group(2)}"
            # Some entries embed markdown tables (pipe-delimited rows)
            # as raw text with single \n between rows; each row would
            # otherwise collapse into one unreadable run in the
            # rendered HTML. Converts any remaining single newlines to
            # real line breaks too, after the paragraph-level bolding above already ran.
            p = p.replace('\n', '<br>')
            out_paras.append(p)
        return '<br><br>'.join(out_paras)

    @staticmethod
    def _break_long_tooltip(text: str, chunk_chars: int = 220) -> str:
        """For genuinely run-on text with no \\n\\n breaks at all in the
        source (unlike _format_multi_para's DM Reward entries) — some
        feat descriptions run over 1300 characters as a single,
        unbroken block. Even though Qt's HTML tooltip wrapping handles
        the width correctly, a very long, unstructured block could
        still be clipped by a tooltip's maximum render height. Breaks
        into readable chunks at real sentence boundaries (never mid-
        sentence), each chunk close to but not exceeding chunk_chars."""
        import re
        if not text or len(text) <= chunk_chars:
            return text
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks, current = [], ""
        for s in sentences:
            if current and len(current) + len(s) + 1 > chunk_chars:
                chunks.append(current)
                current = s
            else:
                current = f"{current} {s}".strip()
        if current:
            chunks.append(current)
        return '<br><br>'.join(chunks)

    def _add_feature_section(self, title, color, items, badge_color=None):
        from dnd_app.data.feature_ui_interactions import FEATURE_CONFIG
        try:
            from dnd_app.data.feature_tooltips import FEATURE_DESCS
        except ImportError:
            FEATURE_DESCS = {}
        # Resolve '+STAT' placeholders into real numbers for every item —
        # resolve_stat_placeholders() is a no-op on text with no such
        # placeholder, so it's safe to call unconditionally. (The old
        # pre-filter here only matched "CHA modifier"-style phrasing or a
        # bare "CHA/" pattern, missing plenty of real cases like
        # "1+CHA/LR" shorthand, which never got resolved as a result.)
        items = list(dict.fromkeys(items))   # dedupe (race vs ancestry overlap)
        items = [self._inject_ability_modifier(it, self.char) for it in items]
        grp = QGroupBox(title)
        grp.setStyleSheet(
            f"QGroupBox{{background:{SURF};border:1px solid {qa(color,0x55)};border-radius:10px;"
            f"margin-top:16px;padding:10px 10px 10px 10px;}}"
            f"QGroupBox::title{{left:12px;top:0;background:{SURF};color:{color};"
            f"font-size:{FS_SMALL}px;font-weight:700;letter-spacing:1px;padding:0 6px;}}"
        )
        gl = QVBoxLayout(grp); gl.setSpacing(6)
        for item in items:
            row = QFrame()
            row.setStyleSheet(
                f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:7px;}}"
                f"QFrame:hover{{background:{SURF3};border-color:{BORDER2};}}")
            row.setCursor(Qt.WhatsThisCursor)
            rl = QHBoxLayout(row); rl.setContentsMargins(10,8,10,8); rl.setSpacing(8)
            feat_lbl = _lbl(item, TEXT, FS_BODY, wrap=True)
            feat_lbl.setMinimumHeight(32)
            rl.addWidget(feat_lbl)

            # ── Tooltip lookup (multiple strategies) ──────────────────────────
            _bracket = item.strip()
            if _bracket.startswith("[") and "]" in _bracket:
                raw = _bracket[_bracket.index("]")+1:].strip()
            else:
                raw = _bracket
            raw_no_paren = raw.split("(")[0].strip()
            raw_no_dash = raw.split("\u2014")[0].strip() if "\u2014" in raw else raw
            raw_no_dash_paren = raw_no_dash.split("(")[0].strip()
            after_colon = raw.split(":", 1)[1].strip() if ":" in raw else ""
            after_colon_no_paren = after_colon.split("(")[0].strip() if after_colon else ""
            # "Chosen Feats" format is "FeatName: special text…" — the name
            # comes BEFORE the colon here, the opposite of after_colon above
            # (which is for a different, "Label: Name" style of item).
            before_colon = raw.split(":", 1)[0].strip() if ":" in raw else ""
            # DM-Granted Feats (and similar) format as "<b>Name</b>  [source]
            # <i>Req: ...</i><br>desc…" — the name is wrapped in bold tags
            # rather than prefixed with a leading bracket, so none of the
            # candidates above would ever match it without this.
            bold_name = ""
            if "<b>" in item and "</b>" in item:
                bold_name = item.split("<b>",1)[1].split("</b>",1)[0].strip()
            def _lu(c):
                if not c: return ""
                return (FEATURE_DESCS.get(c) or
                        (FEATURE_CONFIG.get(c) or {}).get("desc","") or
                        (FEATURE_CONFIG.get(c) or {}).get("note","") or "")
            tip = ""
            # Unarmored Defense needs special handling: the generic
            # FEATURE_DESCS entry describes BOTH the Barbarian and Monk
            # versions in one sentence (confusing when you only have one
            # of them), and a bare formula ("10 + DEX + CON") isn't as
            # useful as showing the character's actual current AC total
            # first, with the breakdown of what it's made of underneath.
            if raw_no_paren == "Unarmored Defense":
                from dnd_app.core.calculator import get_ac, get_ac_breakdown
                total = get_ac(self.char)
                parts = [(lbl, val) for lbl, val in get_ac_breakdown(self.char)
                         if "Unarmored Defense" in lbl or "modifier" in lbl.lower()]
                if parts:
                    breakdown_str = " + ".join(f"{v:+d} ({lbl})" if i else f"{v} ({lbl})"
                                                for i, (lbl, v) in enumerate(parts))
                    tip = f"Total: AC {total}<br>{breakdown_str}"
            if not tip:
                for _cand in [bold_name, raw, raw_no_paren, raw_no_dash, raw_no_dash_paren, before_colon, after_colon, after_colon_no_paren]:
                    _d = _lu(_cand)
                    if _d: tip = _d; break
            if not tip and " + " in (after_colon or raw_no_paren):
                _src = after_colon if after_colon else raw_no_paren
                _parts = [p.strip().split("(")[0].strip() for p in _src.split(" + ")]
                _pds = [f"<b>{p}</b><br>{_lu(p)}" for p in _parts if _lu(p)]
                if _pds: tip = "<br><br>".join(_pds)
            # NOTE: intentionally no "len(item) > 80 → tip = raw" fallback here.
            # Background/race/subrace items already show their FULL description
            # inline in the row label; repeating it verbatim in the tooltip is
            # just noise (the "doubled text" bug). Only show a tooltip when we
            # found a genuinely different, shorter lookup via FEATURE_DESCS.
            if tip:
                display_name = after_colon_no_paren or raw_no_paren
                tip_formatted = self._break_long_tooltip(tip)
                row.setToolTip(f"<b>{display_name}</b><br><br>{tip_formatted}")
                row.setToolTipDuration(15000)
                feat_lbl.setToolTip(f"<b>{display_name}</b><br><br>{tip_formatted}")
                feat_lbl.setToolTipDuration(15000)

            # ── Right-click context menu ──────────────────────────────────────
            # _tip is deliberately empty for race/subrace/background items
            # (their full text is already inline, so a hover tooltip would
            # just repeat it) — but that meant right-click found nothing to
            # show either, since the menu action was only ever added "if
            # _tip". Fall back to the item's own text so right-click always
            # has something to display, for every feature row without
            # exception, while leaving the hover-tooltip behavior alone.
            def _show_detail_menu(ev, _item=item, _tip=(tip or item), _raw=raw_no_paren, _row=row):
                from PySide6.QtWidgets import QMenu
                menu = QMenu(_row)
                act = menu.addAction(f"📖  Show Details: {_raw[:40]}")
                act.triggered.connect(lambda: QMessageBox.information(
                    _row, _raw,
                    f"<b>{_raw}</b><br><br>{_tip}",
                ))
                menu.exec(ev.globalPos())
            row.mousePressEvent = lambda ev, f=_show_detail_menu: (
                f(ev) if ev.button() == Qt.RightButton else None
            )

            gl.addWidget(row)
        self._feat_tab_lay.insertWidget(self._feat_tab_lay.count()-1, grp)

    def _add_wild_magic_section(self, barb: bool = False):
        from dnd_app.data.classes import WILD_MAGIC_SURGE_TABLE, WILD_MAGIC_BARBARIAN_TABLE
        # Determine which table to use: Barbarian=d8, Sorcerer=d100
        is_barb_wm = barb
        if is_barb_wm:
            table_data = [(i+1, i+1, eff) for i, (_, eff) in enumerate(WILD_MAGIC_BARBARIAN_TABLE)]
            title = "Wild Magic Surge Table  (Barbarian — roll d8 when you enter your rage)"
            die_label = "🎲  Roll Wild Magic Surge (d8)"
            die_max = 8
        else:
            table_data = WILD_MAGIC_SURGE_TABLE
            title = "Wild Magic Surge Table  (Sorcerer — roll d100 after casting a spell)"
            die_label = "🎲  Roll Wild Magic Surge (d100)"
            die_max = 100

        grp = QGroupBox(title)
        grp.setStyleSheet(f"QGroupBox{{background:{SURF};border:1px solid {qa(PURP2,0x55)};border-radius:10px;margin-top:16px;padding:10px;}}QGroupBox::title{{left:12px;top:0;background:{SURF};color:{PURP2};font-size:{FS_SMALL}px;font-weight:700;padding:0 6px;}}")
        gl = QVBoxLayout(grp)
        roll_row = QHBoxLayout()
        roll_btn = QPushButton(die_label)
        roll_btn.setStyleSheet(f"QPushButton{{background:{PURPLE};border:none;border-radius:8px;color:white;font-weight:700;font-size:{FS_BODY}px;padding:8px 16px;}}QPushButton:hover{{background:{PURP2};}}")
        self._wm_result_lbl = _lbl("—", PURP2, FS_BODY, bold=True, wrap=True)
        roll_row.addWidget(roll_btn); roll_row.addWidget(self._wm_result_lbl, 1); roll_row.addStretch()
        gl.addLayout(roll_row)
        table = QTableWidget(len(table_data), 2)
        table.setHorizontalHeaderLabels(["Roll","Effect"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setMaximumHeight(220)
        for i,(lo,hi,eff) in enumerate(table_data):
            table.setItem(i,0,QTableWidgetItem(str(lo) if lo==hi else f"{lo:02d}–{hi:02d}"))
            item = QTableWidgetItem(eff); item.setToolTip(eff)
            table.setItem(i,1,item)
        def _roll(_=None, _max=die_max, _tbl=table_data, _lbl=self._wm_result_lbl):
            r = random.randint(1, _max)
            for i,(lo,hi,eff) in enumerate(_tbl):
                if lo<=r<=hi:
                    table.selectRow(i); table.scrollToItem(table.item(i,0))
                    _lbl.setText(f"Roll {r}: {eff[:120]}{'…' if len(eff)>120 else ''}")
                    break
        roll_btn.clicked.connect(_roll)
        gl.addWidget(table)
        self._feat_tab_lay.insertWidget(self._feat_tab_lay.count()-1, grp)

    # ══ TAB 6: TRAITS & NOTES ══════════════════════════════════════════════════
    def _build_tab_traits_notes(self):
        tab = QScrollArea(); tab.setWidgetResizable(True)
        w = QWidget(); tab.setWidget(w)
        root = QHBoxLayout(w); root.setContentsMargins(20,20,20,20); root.setSpacing(16)

        left = QWidget(); ll = QVBoxLayout(left); ll.setSpacing(10)
        self._trait_edits = {}
        for label, key in [("Personality Traits","personality_traits"),("Ideals","ideals"),
                           ("Bonds","bonds"),("Flaws","flaws")]:
            ll.addWidget(_lbl(label.upper(), GOLD, FS_SMALL, bold=True))
            ed = QTextEdit(); ed.setMaximumHeight(90)
            ed.setPlaceholderText(f"Enter {label.lower()}…")
            self._trait_edits[key] = ed; ll.addWidget(ed)
        ll.addStretch(); root.addWidget(left, 1)

        right = QWidget(); rl5 = QVBoxLayout(right); rl5.setSpacing(10)
        rl5.addWidget(_lbl("BACKSTORY & APPEARANCE", GOLD, FS_SMALL, bold=True))
        self._backstory_edit = QTextEdit(); self._backstory_edit.setPlaceholderText("Character backstory, appearance, allies, enemies…")
        rl5.addWidget(self._backstory_edit, 1)
        rl5.addWidget(_lbl("CAMPAIGN NOTES", GOLD, FS_SMALL, bold=True))
        self._notes_edit = QTextEdit(); self._notes_edit.setPlaceholderText("Session notes, quest log, treasure…")
        rl5.addWidget(self._notes_edit, 1)
        root.addWidget(right, 2)
        return tab

    # ════════════════════════════════════════════════════════════
    #  LOAD / REFRESH
    # ════════════════════════════════════════════════════════════
    def _load(self):
        char = self.char
        self.ctrl.refresh()

        # Sync the condition checkboxes and exhaustion spinbox from the
        # actual character data, so both reflect what a saved character
        # actually has active rather than their default (unchecked/0) state.
        if hasattr(self, "_cond_checks"):
            active_conds = set(char.get("conditions", []))
            for cname, cb in self._cond_checks.items():
                cb.blockSignals(True)
                cb.setChecked(cname in active_conds)
                cb.blockSignals(False)
        if hasattr(self, "_exhaustion_spin"):
            self._exhaustion_spin.blockSignals(True)
            self._exhaustion_spin.setValue(char.get("exhaustion", 0))
            self._exhaustion_spin.blockSignals(False)
        self._refresh_exhaustion_label()
        self._refresh_active_conditions()

        self._name_edit.blockSignals(True)
        self._name_edit.setText(char.get("name", ""))
        self._name_edit.blockSignals(False)
        self._populate_subclass_combo()
        if total_level(char) == 0:
            QMessageBox.warning(
                self,
                "Incomplete Character",
                "This character has no class levels. Use Edit Class or reload after completing creation.",
            )
        classes = char.get("classes", [])
        cls_parts = []
        for c in classes:
            sub = c.get("subclass","")
            cls_parts.append(f"{c['class']} {c['level']}" + (f" ({sub})" if sub else ""))
        self._class_summary.setText("  ·  ".join(cls_parts))

        self._refresh_stat_bar()
        self._refresh_abilities_tab()
        self._refresh_skills()
        self._refresh_combat()
        self._refresh_spells()
        self._populate_my_spells_from_char()
        self._rebuild_features()
        if hasattr(self,"_refresh_optional_features"): self._refresh_optional_features()
        self._refresh_concentration()
        self._refresh_magic_items()
        self._refresh_gear_equipment()
        if hasattr(self, "_levelup_panel"):
            self._levelup_panel.refresh()

        # Traits
        for key, ed in self._trait_edits.items():
            ed.setPlainText(char.get(key,""))
        self._backstory_edit.setPlainText(char.get("backstory",""))
        self._notes_edit.setPlainText(char.get("notes",""))

    def _refresh_stat_bar(self):
        update_all(self.char)
        ac = get_ac(self.char)
        cur_hp = self.char.get("current_hp", self.char.get("max_hp",0))
        max_hp = self.char.get("max_hp",0)
        pb = get_prof_bonus(self.char)
        ini = get_initiative(self.char)
        from dnd_app.core.calculator import get_effective_speed
        _spds = get_effective_speed(self.char)
        spd  = _spds["walk"]
        fly  = _spds["fly"]
        swim = _spds["swim"]
        clmb = _spds["climb"]
        self._sb_ac._val.setText(str(ac))
        self._sb_hp._val.setText(f"{cur_hp}/{max_hp}")
        init_adv = get_initiative_advantage_status(self.char)
        self._sb_init._val.setText(sign(ini) + (" 🎯" if init_adv["has_advantage"] else ""))
        if init_adv["has_advantage"]:
            notes = "\n".join(f"• {s['source']}: {s['note']}" for s in init_adv["sources"])
            self._sb_init.setToolTip(f"Click to roll initiative (d20 + {sign(ini)})\n\nAdvantage:\n{notes}")
        else:
            self._sb_init.setToolTip("Click to roll initiative (d20 + Initiative bonus)")

        # ── AC tooltip: full breakdown showing where each point comes from ────
        from dnd_app.core.calculator import get_ac_breakdown
        ac_parts = get_ac_breakdown(self.char)
        ac_lines = "\n".join(f"  {label}: {'+' if val>=0 else ''}{val}" for label, val in ac_parts)
        self._sb_ac.setToolTip(f"AC {ac} breakdown:\n{ac_lines}")
        if hasattr(self, "_armor_card_ac_lbl"):
            self._armor_card_ac_lbl.setText(f"AC {ac}")
            self._armor_card_ac_lbl.setToolTip(f"AC {ac} breakdown:\n{ac_lines}")

        # ── Speed tooltip: note any magic source ───────────────────────────────
        spd_sources = self.char.get("_speed_bonus_sources", [])
        if spd_sources:
            src_lines = "\n".join(f"  +{v} ft — {s}" for s, v in spd_sources)
            self._sb_spd.setToolTip(f"Base speed {self.char.get('speed',30)} ft, plus:\n{src_lines}")
        else:
            self._sb_spd.setToolTip("")
        if hasattr(self,"_exh_combo"):
            self._exh_combo.blockSignals(True)
            self._exh_combo.setCurrentIndex(self.char.get("exhaustion",0))
            self._exh_combo.blockSignals(False)
        # Show/hide Ancestry button based on race
        for btn in self.findChildren(QPushButton):
            if "Ancestry" in btn.text():
                btn.setVisible(self.char.get("race","") == "Dragonborn")
        # Sync identity buttons in choices tab if present
        if hasattr(self, "_identity_btns") and "ancestry" in self._identity_btns:
            self._identity_btns["ancestry"].setVisible(
                self.char.get("race","") == "Dragonborn")
        self._sb_prof._val.setText(sign(pb))
        _spd_parts = [f"{spd} ft"]
        if fly:  _spd_parts.append(f"✈ {fly}")
        if swim: _spd_parts.append(f"🌊 {swim}")
        if clmb: _spd_parts.append(f"↑ {clmb}")
        self._sb_spd._val.setText(" / ".join(_spd_parts))
        cls_parts = []
        for c in self.char.get("classes",[]):
            sub = c.get("subclass","")
            cls_parts.append(f"{c['class']} {c['level']}" + (f" ({sub})" if sub else ""))
        self._class_summary.setText("  ·  ".join(cls_parts))

    def _update_save_advantage_badge(self, ab: str):
        """Sync one saving throw's advantage indicator badge to current
        state — icon, tooltip, and visibility. Called at initial build and
        again from _refresh_abilities_tab so it stays correct if the
        character's class/level changes after the sheet is already open."""
        badge = getattr(self, "_save_adv_badges", {}).get(ab)
        if not badge:
            return
        status = get_save_advantage_status(self.char, ab)
        badge.setVisible(status["has_advantage"])
        if status["has_advantage"]:
            icon = "🎯" if status["conditional"] else "✓"
            notes = "\n".join(f"• {s['source']}: {s['note']}" for s in status["sources"])
            badge.setText(icon)
            badge.setToolTip(
                ("Conditional advantage:\n" if status["conditional"] else "Advantage:\n") + notes)

    def _update_save_condition_badge(self, ab: str):
        """Sync one saving throw's condition-based auto-fail/disadvantage
        badge — separate from _update_save_advantage_badge since this
        reflects a genuinely different, transient mechanic (active
        conditions/exhaustion), not racial/class traits. Called at
        initial build and again from _refresh_abilities_tab so it
        updates immediately when a condition checkbox is toggled."""
        badge = getattr(self, "_save_cond_badges", {}).get(ab)
        if not badge:
            return
        from dnd_app.core.calculator import get_condition_save_status
        status = get_condition_save_status(self.char, ab)
        if status["auto_fail"]:
            badge.setVisible(True)
            badge.setText("AUTO-FAIL")
            badge.setToolTip(f"Auto-fails {AB_FULL[ab]} saves: {', '.join(status['sources'])}")
        elif status["disadvantage"]:
            badge.setVisible(True)
            badge.setText("DISADV")
            badge.setToolTip(f"Disadvantage on {AB_FULL[ab]} saves: {', '.join(status['sources'])}")
        else:
            badge.setVisible(False)
            badge.setText("")

    def _refresh_abilities_tab(self):
        for ab in ABILITIES:
            score = ability_score(self.char, ab)
            if ab in self._ab_blocks:
                self._ab_blocks[ab].set_score(score)
        # Saves
        saves = all_saving_throw_bonuses(self.char)
        profs = get_saving_throw_profs(class_levels(self.char))
        for ab, (dot, val_lbl) in self._save_widgets.items():
            val = saves.get(ab,0)
            color = TEAL2 if val>0 else (CRIM2 if val<0 else TEXT2)
            val_lbl.setText(sign(val))
            self._update_save_advantage_badge(ab)
            self._update_save_condition_badge(ab)
            val_lbl.setStyleSheet(f"color:{color};font-size:{FS_TITLE}px;font-weight:700;background:transparent;")
            is_p = ab in profs or self.char.get("saving_throws",{}).get(ab,False)
            dot.setChecked(is_p)

        # Derived stat boxes are refreshed here (not just set once at
        # build time) so Passive Perception correctly reflects live
        # advantage/disadvantage adjustments, e.g. from armor or items.
        if hasattr(self, "_stat_boxes"):
            from dnd_app.core.calculator import (
                get_skill_advantage_status, get_extra_attacks, get_sneak_attack,
                get_martial_arts_die, get_rage_damage,
            )
            pb = get_prof_bonus(self.char)
            from dnd_app.core.calculator import get_effective_speed, get_character_senses
            spd = get_effective_speed(self.char)["walk"]
            senses = get_character_senses(self.char)
            senses_str = ", ".join(f"{k.title()} {v} ft" for k, v in senses.items() if v > 0) or "—"
            # Devil's Sight: the defining feature is seeing through
            # *magical* darkness specifically (which normal darkvision
            # cannot do), not just a flat darkvision number.
            if self.char.get("_devils_sight", False):
                senses_str += " (Devil's Sight: darkvision works through magical darkness too)"

            martial_arts_val = get_martial_arts_die(self.char)
            rage_val = get_rage_damage(self.char)
            updates = {
                "Prof Bonus": sign(pb),
                "Initiative": sign(get_initiative(self.char)),
                "Speed": f"{spd} ft",
                "Passive Perc.": str(get_passive_perception(self.char)),
                "Senses": senses_str,
                "Extra Attacks": str(get_extra_attacks(class_levels(self.char), subclasses(self.char), self.char)),
                "Carry Capacity": f"{get_carry_capacity(self.char)} lb",
                "Sneak Attack": get_sneak_attack(self.char),
                "Martial Arts": martial_arts_val,
                "Rage Damage": rage_val,
            }
            # These two are class-conditional (only meaningful for Monk
            # / Barbarian respectively) — both their text AND visibility
            # are updated on a class change, so a character that had
            # ever been a Barbarian in this sheet session doesn't keep
            # showing a "Rage Damage: —" box after respeccing away from
            # it; the box disappears entirely, the same as for a
            # character that was never a Barbarian.
            CONDITIONAL_BOXES = {"Martial Arts": martial_arts_val, "Rage Damage": rage_val}
            for label, val in updates.items():
                box = self._stat_boxes.get(label)
                if not box:
                    continue
                if label in CONDITIONAL_BOXES:
                    box.setVisible(val != "—")
                box.set_val(val)

            # Passive Perception tooltip: explain any +5/-5 adjustment
            pp_box = self._stat_boxes.get("Passive Perc.")
            if pp_box:
                status = get_skill_advantage_status(self.char, "Perception")
                if status["net"] == "advantage":
                    pp_box.setToolTip(
                        "+5 from permanent advantage on Perception checks\n"
                        "From: " + ", ".join(status["adv_reasons"]))
                elif status["net"] == "disadvantage":
                    pp_box.setToolTip(
                        "\u22125 from permanent disadvantage on Perception checks\n"
                        "From: " + ", ".join(status["disadv_reasons"]))
                else:
                    pp_box.setToolTip("10 + Perception skill bonus")

    def _refresh_skills(self):
        from dnd_app.core.calculator import get_skill_advantage_status, has_jack_of_all_trades
        skills = all_skill_bonuses(self.char)
        _jack = has_jack_of_all_trades(self.char)
        for sk, (row_f, sym_l, val_l, name_l, adv_badge) in self._skill_rows.items():
            prof = self.char.get("skills",{}).get(sk,0)
            bonus = skills.get(sk,0)
            # Same display rule as the initial build: JoAT shows ½ on any
            # skill that isn't already proficient/expert.
            _disp = prof if prof > 0 else (1 if _jack else 0)
            sym = {0:"—",1:"½",2:"◆",3:"◈"}.get(_disp,"—")
            sym_color = {0:TEXT3,1:IND2,2:INDIGO,3:PURP2}.get(_disp,TEXT3)
            val_color = TEAL2 if bonus>0 else (CRIM2 if bonus<0 else TEXT2)
            sym_l.setText(sym); sym_l.setStyleSheet(f"color:{sym_color};font-size:{FS_BODY}px;font-weight:700;background:transparent;")
            val_l.setText(sign(bonus)); val_l.setStyleSheet(f"color:{val_color};font-size:{FS_LABEL}px;font-weight:700;background:transparent;")
            row_f.setStyleSheet(f"QFrame{{background:{SURF2 if prof>0 else SURF};border:1px solid {BORDER2 if prof>0 else BORDER};border-radius:7px;}}")

            # Advantage / disadvantage badge, with a tooltip explaining why
            status = get_skill_advantage_status(self.char, sk)
            if status["net"] == "advantage":
                adv_badge.setText("▲ ADV"); badge_color = TEAL2
                reasons = status["adv_reasons"]
                tip = "Advantage on " + sk + " checks (passive score +5)\nFrom: " + ", ".join(reasons)
            elif status["net"] == "disadvantage":
                adv_badge.setText("▼ DISADV"); badge_color = CRIM2
                reasons = status["disadv_reasons"]
                tip = "Disadvantage on " + sk + " checks (passive score \u22125)\nFrom: " + ", ".join(reasons)
            elif status["advantage"] and status["disadvantage"]:
                adv_badge.setText("⇅ NORMAL"); badge_color = TEXT3
                tip = ("Advantage and disadvantage cancel out — roll normally.\n"
                       "Advantage from: " + ", ".join(status["adv_reasons"]) + "\n"
                       "Disadvantage from: " + ", ".join(status["disadv_reasons"]))
            else:
                adv_badge.setText(""); adv_badge.setVisible(False)
                continue

            adv_badge.setVisible(True)
            adv_badge.setStyleSheet(
                f"color:{badge_color};font-size:{FS_TINY}px;font-weight:700;"
                f"background:{qa(badge_color,0x1f)};border:1px solid {qa(badge_color,0x55)};"
                f"border-radius:4px;padding:1px 4px;"
            )
            adv_badge.setToolTip(tip)
            row_f.setToolTip(tip)

        # Proficiency lists — use the actual, already-correct derived
        # fields (which include class, subclass, race, background, and
        # feat grants) rather than rebuilding a partial, class-only
        # version here that silently ignored every other source.
        self._armor_prof_lbl.setText("; ".join(sorted(set(self.char.get("armor_proficiencies", [])) - {"None"})) or "None")
        self._wpn_prof_lbl.setText("; ".join(sorted(set(self.char.get("weapon_proficiencies", [])) - {"None"})) or "None")
        self._lang_lbl.setText(", ".join(sorted(set(self.char.get("languages", ["Common"])))) or "None")
        self._refresh_tool_prof_chips()

    def _refresh_tool_prof_chips(self):
        """Individual tool-proficiency chips, each with a full hover
        tooltip from the XGE tool descriptions — replaces the old plain
        comma-separated text blob, which couldn't show per-tool detail.
        Uses a plain QGridLayout (not FlowLayout) — see the setup comment
        in _build_tab_skills for why."""
        while self._tool_prof_lay.count():
            item = self._tool_prof_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)
        from dnd_app.data.feature_tooltips import get_tool_tooltip
        def _tool_badge(text, color, tooltip):
            b = _lbl(text, color, FS_SMALL, bold=True, wrap=False)
            b.setStyleSheet(
                f"background:{qa(color,0x33)};border:1.5px solid {qa(color,0x99)};"
                f"border-radius:5px;padding:3px 8px;color:{color};"
                f"font-size:{FS_SMALL}px;font-weight:700;"
            )
            b.setToolTip(tooltip)
            return b
        tools = self.char.get("tool_proficiencies", [])
        if not tools:
            self._tool_prof_lay.addWidget(_tool_badge("None", TEXT3, ""), 0, 0)
            return
        cols = 4
        for i, tool in enumerate(sorted(set(tools))):
            tip = get_tool_tooltip(tool)
            self._tool_prof_lay.addWidget(_tool_badge(tool, AMBE2, tip), i // cols, i % cols)

    def _refresh_combat(self):
        if getattr(self, "_blocking_refresh", False):
            return
        self._blocking_refresh = True
        try:
            self._do_refresh_combat()
        finally:
            self._blocking_refresh = False

    def _do_refresh_combat(self):
        char = self.char
        update_all(char)
        if hasattr(self,"_refresh_quick_spells"): self._refresh_quick_spells()
        # HP spinboxes — while Wild Shaped, show and edit the beast's own
        # separate HP pool instead of the character's own current_hp. Your
        # own hit points are untouched by damage taken in beast form
        # (except overflow past 0), so the two pools stay genuinely
        # separate rather than one masking the other.
        self._hp_max_hp.blockSignals(True)
        self._hp_current_hp.blockSignals(True)
        self._hp_temp_hp.blockSignals(True)
        active_beast = char.get("_wildshape_active")
        if active_beast:
            from dnd_app.data.statblocks import WILDSHAPE_BEASTS
            beast = WILDSHAPE_BEASTS.get(active_beast, {})
            mx = beast.get("hp", 0)
            cur = char.get("_wildshape_hp", mx)
            tmp = 0
        else:
            mx   = char.get("max_hp", 0)
            cur  = char.get("current_hp", mx)
            tmp  = char.get("temp_hp", 0)
        self._hp_max_hp.setValue(mx)
        self._hp_current_hp.setValue(cur)
        self._hp_temp_hp.setValue(tmp)
        self._hp_max_hp.setReadOnly(bool(active_beast))  # beast's max HP is fixed, not player-editable
        self._hp_max_hp.blockSignals(False)
        self._hp_current_hp.blockSignals(False)
        self._hp_temp_hp.blockSignals(False)
        self._update_hp_bar()
        if not getattr(self, "_hp_signals_connected", False):
            def _on_current_hp_changed(v):
                if self.char.get("_wildshape_active"):
                    if v <= 0:
                        self._wildshape_revert()
                        self._toast("🐾 Beast form dropped to 0 HP — reverted to normal form")
                    else:
                        self.char["_wildshape_hp"] = v
                        self._mark_dirty()
                else:
                    self.ctrl.update("current_hp", v, rebuild_char=False)
                self._update_hp_bar()
                self._refresh_death_and_conditions()
            self._hp_current_hp.valueChanged.connect(_on_current_hp_changed)
            self._hp_max_hp.valueChanged.connect(self._on_max_hp_changed)
            self._hp_temp_hp.valueChanged.connect(
                lambda v: self.ctrl.update("temp_hp", v, rebuild_char=False)
            )
            self._hp_signals_connected = True

        # Armor combo
        _armor_name = char.get("armor_worn", "No Armor")
        if _armor_name and _armor_name != "No Armor":
            _abase = next((a for a in ARMOR if a[0] == _armor_name), None)
            self._armor_display.setText(f"{_armor_name} (AC {_abase[2]})" if _abase else _armor_name)
        else:
            self._armor_display.setText("No Armor")
        self._shield_display.setText("Shield equipped (+2 AC)" if char.get("shield") else "No Shield")
        self._shield_display.setStyleSheet(
            f"QLabel{{background:{SURF2};border:1px solid {GOLD if char.get('shield') else BORDER};"
            f"border-radius:6px;padding:4px 10px;color:{GOLD2 if char.get('shield') else TEXT3};"
            f"font-size:{FS_SMALL}px;font-weight:{700 if char.get('shield') else 400};}}")

        self._bind_death_and_conditions()
        self._refresh_death_and_conditions()

        # Delegates to _refresh_combat_weapons rather than duplicating
        # the clear-and-rebuild loop here, so synthetic attack rows
        # (Martial Arts, etc.) stay in sync with equipment changes
        # rather than only appearing until the next tab switch.
        self._refresh_combat_weapons()
        self._refresh_companions_tab()

        # Resources and hit dice are now rendered inside the Other action tab
        # via _build_resource_rows(), called from _refresh_action_tabs().
        self._resource_widgets = []   # reset list; rebuilt in _refresh_action_tabs

        self._refresh_action_tabs()
        self._refresh_resistances_strip()
        # No maximumHeight cap on _combat_top_half: a hard cap would
        # stop dead space from appearing when the splitter shrinks the
        # action list, but would also stop the user from ever dragging
        # the handle to give the top area MORE room, which matters when
        # there are many resistance/movement badges wrapped into
        # several rows. Manual drag control in both directions wins here.

    def _refresh_resistances_strip(self):
        """Rebuild the Resistances/Immunities badge row. Expands 'all' and
        'all except X' shorthand into every individual damage type (so the
        strip always shows concrete types, never a vague summary), and
        applies D&D's actual rule that resistance and immunity to the same
        type don't stack — if a type has immunity from any source, its
        resistance badge (from any source) is dropped, not shown alongside."""
        if not hasattr(self, '_resist_frame'):
            return
        while self._resist_lay.count():
            item = self._resist_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)

        resistances = self.char.get("damage_resistances", [])
        immunities  = self.char.get("damage_immunities", []) + [
            (f"{cond} (condition)", source)
            for cond, source in self.char.get("condition_immunities_magic", [])
        ]

        if not resistances and not immunities:
            self._resist_frame.setVisible(False)
            self._resist_caption.setVisible(False)
            return
        self._resist_frame.setVisible(True)
        self._resist_caption.setVisible(True)
        idx = 0
        cols = 5

        def _badge(text, color, tooltip):
            b = _lbl(text, color, FS_SMALL, bold=True, wrap=False)
            b.setStyleSheet(
                f"background:{qa(color,0x33)};border:1.5px solid {qa(color,0x99)};"
                f"border-radius:5px;padding:3px 8px;color:{color};"
                f"font-size:{FS_SMALL}px;font-weight:700;"
            )
            b.setToolTip(tooltip)
            return b

        ALL_DAMAGE_TYPES = ["acid","bludgeoning","cold","fire","force","lightning",
                            "necrotic","piercing","poison","psychic","radiant",
                            "slashing","thunder"]

        def _expand(dmg_type, source):
            """'all' / 'all except X[/Y]' -> one (type, source) pair per
            real damage type; anything else passes through unchanged."""
            low = dmg_type.lower()
            if low == "all":
                return [(t, source) for t in ALL_DAMAGE_TYPES]
            if low.startswith("all except"):
                excluded = {e.strip() for e in low.replace("all except","").split("/")}
                return [(t, source) for t in ALL_DAMAGE_TYPES if t not in excluded]
            return [(dmg_type, source)]

        from collections import defaultdict
        res_by_type = defaultdict(list)
        for dmg_type, source in resistances:
            base = dmg_type.split(" (")[0]           # "bludgeoning (nonmagical)" -> "bludgeoning"
            qualifier = dmg_type[len(base):].strip() # "" or "(nonmagical)"
            for t, src in _expand(base, source):
                label = t + (f" {qualifier}" if qualifier else "")
                res_by_type[t].append((label, src))
        imm_by_type = defaultdict(list)
        for dmg_type, source in immunities:
            if "(condition)" in dmg_type:
                # Condition immunities (frightened, poisoned, etc.) aren't a
                # damage type and can't be superseded by damage resistance —
                # keep them in their own bucket, never expand/dedupe them
                # against the damage-type table.
                imm_by_type[dmg_type].append((dmg_type, source))
                continue
            base = dmg_type.split(" (")[0]
            for t, src in _expand(base, source):
                imm_by_type[t].append((t, src))

        # Immunity supersedes resistance to the same type — D&D doesn't
        # stack them, so don't display both for one damage type.
        for t in list(res_by_type):
            if t in imm_by_type:
                del res_by_type[t]

        for dmg_type, entries in sorted(res_by_type.items()):
            # Prefer an unqualified entry (e.g. Totem Barbarian's broad,
            # magical "all damage" resistance) over a qualified one (e.g.
            # Lycanthropy's narrower "bludgeoning (nonmagical, non-
            # silvered)") when both exist for the same base damage type —
            # an unqualified resistance always covers at least as much as
            # any qualified one, so it should win the display, not
            # whichever entry happened to be appended to the list first.
            unqualified = next((e for e in entries if " (" not in e[0]), None)
            display_label = unqualified[0] if unqualified else entries[0][0]
            sources = [s for _, s in entries]
            tip = f"Resistance to {display_label} damage\nFrom: " + ", ".join(sources)
            r, c = divmod(idx, cols)
            self._resist_lay.addWidget(_badge(f"½ {display_label}", TEAL2, tip), r, c)
            idx += 1
        for dmg_type, entries in sorted(imm_by_type.items()):
            display_label = entries[0][0]
            sources = [s for _, s in entries]
            is_condition = "(condition)" in display_label
            label_txt = display_label if is_condition else f"{display_label} damage"
            tip = f"Immunity to {label_txt}\nFrom: " + ", ".join(sources)
            r, c = divmod(idx, cols)
            self._resist_lay.addWidget(_badge(f"⊘ {display_label}", GOLD2, tip), r, c)
            idx += 1

    def _build_resource_rows(self, bl):
        """
        Populate the top of the 'Other' tab with live resource pools: class
        features tracked in char['resources'] (Ki, Lay on Hands, Channel
        Divinity, Sorcery Points, Healing Light, etc.), magic item charges,
        and a few feat-granted pools that aren't otherwise tracked.
        """
        def _pool_row(name, current, maximum, reset_label, tooltip_extra="",
                      res_key=None, is_item=False, item_name=None, toggle_effect=None):
            """Interactive resource row with a spinbox to track uses.
            If toggle_effect is given (an EFFECT_TABLE key), also render an
            on/off toggle next to the counter that adds/removes that effect
            from char['active_effects'] and applies its real mechanical
            changes (AC, resistances, combat-tab attack row) immediately —
            rather than just being a passive usage tracker."""
            row = QWidget()
            pct = (current / maximum) if maximum else 0
            if pct > 0.5: bar_color = TEAL2
            elif pct > 0: bar_color = AMBER
            else: bar_color = CRIM2
            row.setStyleSheet(
                f"QWidget{{background:{qa(bar_color,0x14)};border:1px solid {qa(bar_color,0x44)};"
                f"border-radius:6px;margin:1px;}}")
            rl = QHBoxLayout(row); rl.setContentsMargins(8,5,8,5); rl.setSpacing(6)

            name_l = _lbl(name, TEXT, FS_TINY, bold=True, wrap=False)
            reset_l = _lbl(reset_label, TEXT3, FS_TINY-1, wrap=False)
            reset_l.setFixedWidth(70)  # fits "Short Rest"/"Long Rest" (the longest values) without clipping
            tip = f"{name}: {current}/{maximum}\nRecharges: {reset_label}"
            if tooltip_extra: tip += f"\n{tooltip_extra}"

            # Spinbox for current value — editable in-place
            sp = QSpinBox(); sp.setRange(0, maximum); sp.setValue(current)
            sp.setFixedWidth(48); sp.setAlignment(Qt.AlignCenter)
            sp.setToolTip(f"Current uses of {name}")
            sp.setStyleSheet(
                f"QSpinBox{{background:{SURF2};border:1px solid {qa(bar_color,0x66)};"
                f"border-radius:4px;color:{bar_color};font-size:{FS_TINY}px;"
                f"font-weight:700;padding:1px;}}")
            max_l = _lbl(f"/{maximum}", TEXT3, FS_TINY, wrap=False)

            def _save_res(val, _key=res_key, _iname=item_name, _is_item=is_item):
                if _is_item and _iname:
                    ic = self.char.setdefault("item_charges",{})
                    ic.setdefault(_iname,{})["current"] = val
                elif _key:
                    for res in self.char.get("resources",[]):
                        if res.get("key") == _key or res.get("name") == _key:
                            res["current"] = val; break
                self._mark_dirty()
            sp.valueChanged.connect(_save_res)
            self._resource_widgets.append(row)

            # −/+ buttons for quick spend/restore
            minus = QPushButton("−"); minus.setFixedSize(30,30)
            plus  = QPushButton("+"); plus.setFixedSize(30,30)
            btn_ss = (f"QPushButton{{background:{qa(bar_color,0x22)};border:1px solid {qa(bar_color,0x55)};"
                      f"border-radius:5px;color:{bar_color};font-size:16px;"
                      f"font-weight:700;line-height:1;padding:0;}}"
                      f"QPushButton:hover{{background:{bar_color};color:white;}}")
            minus.setStyleSheet(btn_ss); plus.setStyleSheet(btn_ss)
            def _on_minus_click(checked=False, _key=res_key):
                # Earth Genasi Blade Ward needs the same gate as real
                # spell-casting — even though Blade Ward is a cantrip,
                # spending this use is "casting a spell with a bonus
                # action," which can be blocked if a leveled spell was
                # already cast via the regular Action that turn.
                if _key == "earth_genasi_blade_ward":
                    if not self._check_bonus_action_spell_rule(True, "Bonus Action"):
                        self._toast("✖ Can't cast Blade Ward via Bonus Action — you've already "
                                    "cast a non-cantrip spell via your Action this turn")
                        return
                    self._bonus_action_spell_is_cantrip = True
                sp.setValue(max(0, sp.value()-1))
                # Harness Divine Power (Cleric/Paladin, TCE optional
                # feature): this feature both has its own limited uses
                # AND separately consumes a normal Channel Divinity
                # charge each time it's used — not two independent
                # pools. Only this one resource needs the linked decrement.
                if _key == "harness_divine_power":
                    for cd_key in ("channel_divinity", "channel_div"):
                        for res in self.char.get("resources", []):
                            if res.get("key") == cd_key:
                                res["current"] = max(0, res.get("current", 0) - 1)
                                self._mark_dirty()
                                QTimer.singleShot(0, self.ctrl.refresh)
                # Action Surge grants an extra action for the current
                # turn per the real rule, tied into the turn-economy
                # system here rather than existing only as a spendable resource.
                if _key == "action_surge":
                    self.char["_action_surge_used_this_turn"] = True
                    self._toast("⚡ Action Surge: gained an extra action this turn")
                    self._apply_turn_state()
            minus.clicked.connect(_on_minus_click)
            plus.clicked.connect(lambda: sp.setValue(min(maximum, sp.value()+1)))

            for w in (row, name_l): w.setToolTip(tip)
            rl.addWidget(name_l, 1)
            if toggle_effect:
                is_active = toggle_effect in self.char.get("active_effects", [])
                tgl = QCheckBox("Active")
                tgl.setChecked(is_active)
                tgl.setStyleSheet(
                    f"QCheckBox{{color:{CRIM2 if is_active else TEXT3};font-size:{FS_TINY}px;font-weight:700;}}"
                    f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                    f"border:2px solid {CRIM2};background:{CRIM2 if is_active else 'transparent'};}}")
                tgl.setToolTip(f"Toggle {name} on/off — applies its AC bonus, "
                               f"damage resistance/immunity, and any other real "
                               f"mechanical effects (like Hybrid Transformation's "
                               f"unarmed-strike row) immediately.")
                def _on_toggle(state, _name=toggle_effect):
                    active = self.char.setdefault("active_effects", [])
                    on = bool(state)
                    if on and _name not in active:
                        active.append(_name)
                    elif not on and _name in active:
                        active.remove(_name)
                    self._mark_dirty()
                    # Deferred: rebuilding the Other tab (which recreates
                    # this very checkbox) must NOT happen synchronously
                    # inside its own stateChanged handler — doing so while
                    # the signal is still being emitted crashes Qt. Let this
                    # callback fully return first, then refresh. The actual
                    # resistance add/remove is handled centrally inside
                    # update_all() (called by ctrl.refresh()), keyed off
                    # active_effects — not done here — so it survives every
                    # future refresh instead of being wiped by the magic
                    # item recompute that resets damage_resistances.
                    QTimer.singleShot(0, self.ctrl.refresh)
                tgl.stateChanged.connect(_on_toggle)
                rl.addWidget(tgl)
            rl.addWidget(minus); rl.addWidget(sp); rl.addWidget(max_l); rl.addWidget(plus)
            rl.addWidget(reset_l)
            bl.insertWidget(bl.count()-1, row)

        has_any = False

        # ── Class/subclass resource pools (Ki, Lay on Hands, Sorcery Points...) ─
        RESET_LABEL = {'SR':'Short Rest','LR':'Long Rest','SR/LR':'SR or LR',
                       'sr':'Short Rest','lr':'Long Rest'}
        seen_keys = set()
        for r in self.char.get('resources', []):
            if r.get('track') not in ('current_max','uses','pool'):
                continue
            key = r.get('key','') + r.get('name','')
            if key in seen_keys:
                continue
            seen_keys.add(key)
            current = r.get('current', 0)
            maximum = r.get('current_max', 0)
            if not isinstance(maximum, int) or maximum <= 0:
                continue
            reset_label = RESET_LABEL.get(r.get('reset',''), r.get('reset','—'))
            TOGGLE_KEY_MAP = {
                "hybrid_form": "Hybrid Transformation",
                "rage": "Rage",
                "form_of_dread": "Form of Dread",
                "starry_form": "Starry Form",
                "bladesong": "Bladesong",
                "invincible_conqueror": "Invincible Conqueror",
                "exalted_champion": "Exalted Champion",
                "hexblade_curse": "Hexblade's Curse",
                "radiant_soul": "Radiant Soul (Aasimar)",
                "necrotic_shroud": "Necrotic Shroud",
                "gem_flight": "Gem Flight",
                "shifting": "Shifting",
                "vow_of_enmity": "Vow of Enmity",
                "living_legend": "Living Legend",
                "mortal_bulwark": "Mortal Bulwark",
                "elder_champion": "Elder Champion",
                "elemental_gift": "Elemental Gift",
                "writhing_tide": "Writhing Tide",
                "otherworldly_wings": "Otherworldly Wings",
                "trance_of_order": "Trance of Order",
                "umbral_form": "Umbral Form",
                "ghost_walk": "Ghost Walk",
                "steps_of_night": "Steps of Night",
                "arms_of_the_astral_self": "Arms of the Astral Self",
                "awakened_astral_self": "Awakened Astral Self",
                "giants_might": "Giant's Might",
                "giants_might_barb": "Giant's Might",
                "aspect_of_the_wyrm": "Aspect of the Wyrm",
                "spirit_totem": "Spirit Totem",
                "radiant_consumption": "Radiant Consumption",
                "soul_of_the_storm_giant": "Maelstrom Aura",
            }
            _pool_row(r['name'], current, maximum, reset_label,
                      f"From: {r.get('source_class','')}",
                      res_key=r.get('key') or r.get('name'),
                      toggle_effect=TOGGLE_KEY_MAP.get(r.get('key')))
            has_any = True

        # Lucky, Martial Adept, and Metamagic Adept are now properly wired
        # through the standard feat-resource system in calculator.py
        # (FEAT_FIXED_USES_RESOURCES) — the FEAT_RESOURCES dict that used
        # to live here has been removed: it hardcoded current=maximum on
        # every refresh, so editing its spinbox never actually persisted
        # anywhere, since these 3 feats had no real char["resources"] entry
        # for _save_res() to find and update.

        # ── Magic item charges ──────────────────────────────────────────────────
        for iname, charge_data in self.char.get('item_charges', {}).items():
            current = charge_data.get('current', 0)
            maximum = charge_data.get('max', 0)
            if maximum <= 0:
                continue
            recharge = charge_data.get('recharge', 'dawn')
            reset_label = {'dawn':'Dawn','dusk':'Dusk'}.get(recharge, recharge.title())
            _pool_row(f"✦ {iname}", current, maximum, reset_label,
                      f"Magic item charges, from: {iname}",
                      is_item=True, item_name=iname)
            has_any = True

        # ── Hit Dice tracker (uses char["hit_dice"] — the canonical model) ─────
        hd_model = self.char.get("hit_dice", {})
        if hd_model:
            hd_hdr = _lbl("HIT DICE  (spend to heal: roll + CON)", GOLD, FS_TINY, bold=True, wrap=False)
            bl.insertWidget(bl.count()-1, hd_hdr)
            con_mod = ability_mod(self.char, "CON")
            for die_key, hd_data in sorted(hd_model.items()):
                total = hd_data.get("total", 0)
                remaining = hd_data.get("remaining", 0)
                if total <= 0: continue
                pct = remaining/total if total else 0
                bar_color = GREEN2 if pct > 0.5 else (AMBER if pct > 0 else CRIM2)
                hd_row = QWidget()
                hd_row.setStyleSheet(f"QWidget{{background:{qa(bar_color,0x14)};border:1px solid "
                                     f"{qa(bar_color,0x44)};border-radius:6px;margin:1px;}}")
                hr = QHBoxLayout(hd_row); hr.setContentsMargins(8,4,8,4); hr.setSpacing(8)
                hr.addWidget(_lbl(f"Hit Dice ({die_key})", TEXT, FS_TINY, bold=True, wrap=False), 1)
                hr.addWidget(_lbl(f"{remaining}/{total}", bar_color, FS_TINY, bold=True, wrap=False))
                spend = QPushButton(f"🎲 Spend")
                spend.setFixedSize(64, 24)
                spend.setEnabled(remaining > 0)
                spend.setToolTip(f"Roll 1{die_key} + {con_mod} CON and heal that much")
                spend.setStyleSheet(
                    f"QPushButton{{background:{qa(bar_color,0x22)};border:1px solid {qa(bar_color,0x66)};"
                    f"border-radius:4px;color:{bar_color};font-size:{FS_TINY}px;font-weight:700;padding:0px;min-height:0px;}}"
                    f"QPushButton:hover{{background:{bar_color};color:white;}}"
                    f"QPushButton:disabled{{color:{TEXT3};border-color:{BORDER};}}")
                spend.clicked.connect(lambda checked=False, k=die_key: self._spend_hit_die(k))
                hr.addWidget(spend)
                bl.insertWidget(bl.count()-1, hd_row)
            has_any = True

        if has_any:
            sep = _lbl("— Passive Features —", TEXT3, FS_TINY, bold=True, wrap=False, align=Qt.AlignCenter)
            bl.insertWidget(bl.count()-1, sep)

    def _refresh_action_tabs(self):
        """Rebuild the action economy tabs from current character state."""
        if not hasattr(self, '_action_bucket_widgets'):
            return
        buckets = build_action_abilities(self.char)

        for bucket_name, (bw, bl) in self._action_bucket_widgets.items():
            # Clear existing rows — items 0 and 1 are the permanent
            # filter row and level-filter row and must be preserved,
            # along with the stretch at the end.
            while bl.count() > 3:
                item = bl.takeAt(2)
                if item.widget():
                    item.widget().setParent(None)

            # ── "Other" tab gets a Resources & Charges section up top ────────
            if bucket_name == 'Passive':
                self._build_resource_rows(bl)

            CLASS_COLORS = {
                'Universal': TEXT3, 'Fighter': TEAL2, 'Barbarian': CRIM2,
                'Rogue': IND2, 'Monk': TEAL2, 'Paladin': GOLD, 'Ranger': GREEN2,
                'Druid': GREEN2, 'Bard': PURP2, 'Wizard': PURP2, 'Cleric': GOLD,
                'Sorcerer': CRIM2, 'Warlock': IND2, 'Artificer': TEAL2,
                'Blood Hunter': CRIM2,
            }
            rows = buckets.get(bucket_name, [])

            # Conditional filter visibility: only show the chooser for
            # THIS bucket if more than one distinct category is
            # actually present.
            present_cats = {self._classify_action_entry(e) for e in rows}
            self._action_filter_rows[bucket_name].setVisible(len(present_cats) > 1)

            cat_filter = self._action_cat_filters.get(bucket_name, "All")
            if cat_filter != "All":
                rows = [e for e in rows if self._classify_action_entry(e) == cat_filter]
                if cat_filter == "Spell":
                    lvl_filter = self._action_spell_level_filters.get(bucket_name, "All")
                    if lvl_filter != "All":
                        def _entry_level_tag(e):
                            src = e[2] if len(e) > 2 else ""
                            return src  # spell entries already tag source as "Cantrip"/"Spell L1" etc.
                        target = "Cantrip" if lvl_filter == "Cantrip" else f"Spell {lvl_filter}"
                        rows = [e for e in rows if _entry_level_tag(e) == target]
            self._bucket_use_btns = getattr(self, '_bucket_use_btns', {})
            self._bucket_use_btns[bucket_name] = []

            # ── Laptop-friendly 2-column card grid ───────────────────────────
            grid_host = QWidget(); grid_host.setStyleSheet("background:transparent;")
            grid = QGridLayout(grid_host)
            grid.setContentsMargins(0,0,0,0)
            grid.setHorizontalSpacing(8); grid.setVerticalSpacing(6)
            grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)

            for idx, entry in enumerate(rows):
                display, desc, source = entry[0], entry[1], entry[2]
                spell = entry[3] if len(entry) > 3 else None
                is_spell = spell is not None
                if not is_spell:
                    # Spell descriptions come straight from spell data and
                    # don't use these "+STAT" shorthands; class/race/item
                    # feature text does, and was never resolved anywhere
                    # outside the Features tab — combat cards showed the
                    # raw placeholder the whole time.
                    desc = self._inject_ability_modifier(desc, self.char)
                src_color = (IND2 if is_spell
                             else CLASS_COLORS.get(source, AMBE2))
                is_class = source in CLASS_COLORS
                tip_head = (f"<b>{display}</b>" if is_class or is_spell
                            else f"<b>{display}</b><br>Magic item: {source}")
                tooltip_text = f"{tip_head}<br><br>{desc}".replace('\n','<br>')

                card = QFrame()
                card.setCursor(Qt.PointingHandCursor)
                card.setStyleSheet(
                    f"QFrame{{background:{qa(src_color,0x11)};border:1px solid {qa(src_color,0x33)};"
                    f"border-radius:8px;}}"
                    f"QFrame:hover{{background:{qa(src_color,0x1e)};border-color:{qa(src_color,0x77)};}}")
                cl = QHBoxLayout(card); cl.setContentsMargins(10,7,8,7); cl.setSpacing(8)

                src_badge = _lbl(source[:9], src_color, FS_TINY, bold=True, wrap=False)
                src_badge.setFixedWidth(60); src_badge.setAlignment(Qt.AlignCenter)
                src_badge.setStyleSheet(
                    f"background:{qa(src_color,0x22)};border:1px solid {qa(src_color,0x55)};"
                    f"border-radius:4px;color:{src_color};font-size:{FS_TINY}px;"
                    f"font-weight:700;padding:2px 3px;")

                text_col = QVBoxLayout(); text_col.setSpacing(1)
                lbl_name = _lbl(display, GOLD, FS_SMALL, bold=True, wrap=False)
                lbl_desc = _lbl(desc[:170] + ("…" if len(desc)>170 else ""),
                                TEXT2, FS_TINY, wrap=True)
                text_col.addWidget(lbl_name); text_col.addWidget(lbl_desc)

                # ── Cast / Use button ─────────────────────────────────────────
                btn_txt = "Cast" if is_spell else "Use"
                use_btn = QPushButton(btn_txt)
                use_btn.setFixedSize(46, 26)
                use_btn.setStyleSheet(
                    f"QPushButton{{background:{qa(src_color,0x33)};border:1px solid {qa(src_color,0x66)};"
                    f"border-radius:5px;color:{src_color};font-size:{FS_TINY}px;"
                    f"font-weight:700;padding:0px;min-height:0px;}}"
                    f"QPushButton:hover{{background:{src_color};color:white;}}")
                use_btn.setToolTip(tooltip_text)

                if is_spell:
                    def _cast_from_card(checked=False, _sp=spell):
                        self._cast_spell(_sp)
                    use_btn.clicked.connect(_cast_from_card)
                else:
                    def _use_ability(checked=False, _display=display,
                                     _desc=desc, _src=source, _b=bucket_name):
                        # Local copy — the RESOURCE_POOL_TOGGLES set used
                        # elsewhere in this class lives in a different,
                        # unrelated method's scope and isn't visible here.
                        # Must be kept in sync with that other definition.
                        RESOURCE_POOL_TOGGLES = {"Hybrid Transformation", "Rage", "Form of Dread", "Starry Form", "Reckless Attack", "Frenzy", "Sacred Weapon", "Invincible Conqueror", "Exalted Champion", "Peerless Athlete", "Hexblade's Curse", "Bladesong", "Radiant Soul (Aasimar)", "Necrotic Shroud", "Gem Flight", "Shifting", "Vow of Enmity", "Living Legend", "Mortal Bulwark", "Elder Champion", "Elemental Gift", "Writhing Tide", "Otherworldly Wings", "Trance of Order", "Umbral Form", "Ghost Walk", "Steps of Night", "Arms of the Astral Self", "Awakened Astral Self", "Giant's Might", "Aspect of the Wyrm", "Spirit Totem", "Radiant Consumption", "Maelstrom Aura"}
                        key = _display.split('(')[0].strip().lower()
                        # Wild Shape blocks features that need a holy
                        # symbol/spellcasting focus in hand and/or speech —
                        # the same standard as spellcasting itself, since
                        # neither is physically possible in most beast
                        # forms. Everything else is allowed by default,
                        # per the real rule ("retain the benefit of any
                        # features... if the new form is physically
                        # capable of doing so") — Rage, Unarmored Defense,
                        # Danger Sense, Second Wind, etc. all work fine in
                        # beast form and are deliberately NOT in this list.
                        if self.char.get("_wildshape_active") and any(
                                b in key for b in WILDSHAPE_BLOCKED_FEATURES):
                            self._toast(f"\U0001f43e Can't use {_display} while Wild Shaped — "
                                        f"your beast form can't perform what it requires "
                                        f"(a held item, speech, an unarmed strike, or casting)")
                            return
                        # Reckless Attack: a real toggle rather than a
                        # one-off reminder. Doesn't consume a turn slot —
                        # it modifies an attack you're already making, not
                        # a separate action — and stays on until manually
                        # toggled off or cleared by the New Turn button.
                        if key == "reckless attack":
                            fx = self.char.setdefault("active_effects", [])
                            if "Reckless Attack" in fx:
                                fx.remove("Reckless Attack")
                                self._toast("⚔ Reckless Attack: OFF")
                            else:
                                fx.append("Reckless Attack")
                                msg = ("⚔ Reckless Attack: ON — advantage on your melee "
                                       "attacks, but attacks against you also have advantage")
                                # Reckless Abandon (Battlerager, 2nd level):
                                # gain temp HP equal to CON mod (min 1) when
                                # you use Reckless Attack while wearing
                                # battlerager armor. Can't verify the armor
                                # specifically (not a tracked item), gated
                                # on the subclass alone like Armor Spikes.
                                from dnd_app.core.character import subclasses, class_levels
                                barb_sub = subclasses(self.char).get("Barbarian", "")
                                if (class_levels(self.char).get("Barbarian", 0) >= 2
                                        and "battlerager" in barb_sub.lower()):
                                    con_mod = max(1, ability_mod(self.char, "CON"))
                                    cur_temp = self.char.get("temp_hp", 0)
                                    if con_mod > cur_temp:
                                        self.char["temp_hp"] = con_mod
                                    msg += f"\n🛡 Reckless Abandon: {con_mod} temporary HP"
                                self._toast(msg)
                            self._mark_dirty()
                            self._refresh_combat_weapons()
                            self._refresh_effects_list()
                            self._refresh_combat()
                            return
                        # Berserker's Frenzy: same disconnection bug as Rage
                        # had — clicking Use never actually turned it on.
                        # Requires Rage to already be active (you can only
                        # frenzy while raging); doesn't consume a turn slot
                        # itself since it's a decision made alongside
                        # raging, not a separate action.
                        # Sacred Weapon (Paladin, Oath of Devotion): draws
                        # from the shared Channel Divinity pool rather than
                        # having its own resource, so the generic
                        # fuzzy-match loop below wouldn't find a match for
                        # "sacred weapon" against a resource named "Channel
                        # Divinity" — needs its own handling.
                        # Second Wind (Fighter, 1st level): the generic
                        # fallback below only decrements the use counter,
                        # it never actually applies HP — meaning every
                        # Fighter's most basic, most-used feature required
                        # manually rolling and updating HP themselves.
                        # Rolls and applies the heal directly, matching
                        # the pattern used for hit-dice spending.
                        if key == "second wind":
                            sw_res = next((r for r in self.char.get("resources", [])
                                           if "second wind" in str(r.get("name","")).lower()), None)
                            if sw_res is None or sw_res.get("current", 0) <= 0:
                                self._toast("✖ Second Wind: no uses left (recharges on short/long rest)")
                                return
                            import random
                            from dnd_app.core.character import class_levels as _class_levels_sw
                            fighter_lvl = _class_levels_sw(self.char).get("Fighter", 0)
                            roll = random.randint(1, 10)
                            heal = roll + fighter_lvl
                            sw_res["current"] = sw_res.get("current", 1) - 1
                            cur, mx = self.char.get("current_hp", 0), self.char.get("max_hp", 0)
                            self.char["current_hp"] = min(mx, cur + heal)
                            if hasattr(self, "_hp_current_hp"):
                                self._hp_current_hp.setValue(self.char["current_hp"])
                            self._toast(f"\U0001f4aa Second Wind: rolled {roll} + {fighter_lvl} "
                                        f"(Fighter level) = {heal} HP healed "
                                        f"({sw_res['current']}/{sw_res.get('current_max')} left)")
                            self._mark_dirty()
                            self._refresh_combat()
                            return
                        if key == "divine smite":
                            avail_levels = [l for l in range(1, 6)
                                           if (bar := self._slot_bars.get(l)) and bar._max > 0
                                           and bar.get_used() < bar._max]
                            if not avail_levels:
                                self._toast("✖ Divine Smite: no available spell slots to expend")
                                return
                            level, ok = QInputDialog.getItem(
                                self, "Divine Smite", "Expend which spell slot level?",
                                [f"{l}{'st' if l==1 else 'nd' if l==2 else 'rd' if l==3 else 'th'}-level"
                                 for l in avail_levels], 0, False)
                            if not ok:
                                return
                            slot_lvl = avail_levels[[f"{l}{'st' if l==1 else 'nd' if l==2 else 'rd' if l==3 else 'th'}-level"
                                                      for l in avail_levels].index(level)]
                            # The undead/fiend bonus is asked about and
                            # added to the computed total here, not just
                            # shown as a static reminder in the toast text.
                            is_undead_fiend = QMessageBox.question(
                                self, "Divine Smite", "Is the target undead or a fiend?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
                            bar = self._slot_bars[slot_lvl]
                            bar.set_used(bar.get_used() + 1)
                            bar._update_count()
                            self._on_slot_change()
                            # 1d8 base + 1d8 per slot level (equivalent to the
                            # standard "2d8 + 1d8 per level above 1st"
                            # phrasing, capped at 5d8 before the undead/fiend
                            # bonus), +1d8 more if the target is undead/fiend.
                            dice = min(5, 1 + slot_lvl)
                            if is_undead_fiend:
                                dice += 1
                            self._toast(f"⚔ Divine Smite: expended a level-{slot_lvl} slot — "
                                        f"{dice}d8 radiant damage"
                                        + (" (includes +1d8 vs. undead/fiend)" if is_undead_fiend else ""))
                            self._mark_dirty()
                            return
                        if key == "sacred weapon":
                            fx = self.char.setdefault("active_effects", [])
                            if "Sacred Weapon" in fx:
                                fx.remove("Sacred Weapon")
                                self._toast("⚔ Sacred Weapon: OFF")
                            else:
                                cd_res = next((r for r in self.char.get("resources", [])
                                               if "channel divinity" in str(r.get("name","")).lower()), None)
                                if cd_res and cd_res.get("current", 0) <= 0:
                                    self._toast("✖ Sacred Weapon: no Channel Divinity uses left "
                                                "(recharges on short/long rest)")
                                    return
                                if cd_res:
                                    cd_res["current"] = cd_res.get("current", 0) - 1
                                fx.append("Sacred Weapon")
                                self._toast("⚔ Sacred Weapon: ON — add CHA mod to attacks with "
                                            "your weapon for 1 minute")
                            self._mark_dirty()
                            self._refresh_combat_weapons()
                            self._refresh_effects_list()
                            return
                        if key == "peerless athlete":
                            # Peerless Athlete is a Channel Divinity
                            # option (Oath of Glory, 3rd level), not its own resource.
                            fx = self.char.setdefault("active_effects", [])
                            if "Peerless Athlete" in fx:
                                fx.remove("Peerless Athlete")
                                self._toast("🏃 Peerless Athlete: OFF")
                            else:
                                cd_res = next((r for r in self.char.get("resources", [])
                                               if "channel divinity" in str(r.get("name","")).lower()), None)
                                if cd_res and cd_res.get("current", 0) <= 0:
                                    self._toast("✖ Peerless Athlete: no Channel Divinity uses left "
                                                "(recharges on short/long rest)")
                                    return
                                if cd_res:
                                    cd_res["current"] = cd_res.get("current", 0) - 1
                                fx.append("Peerless Athlete")
                                self._toast("🏃 Peerless Athlete: ON — doubled carry capacity, "
                                            "advantage on Athletics/Acrobatics, for 10 minutes")
                            self._mark_dirty()
                            self._refresh_combat_weapons()
                            self._refresh_effects_list()
                            return
                        if "frenzi" in key:
                            if "Rage" not in self.char.get("active_effects", []):
                                self._toast("⚠ Frenzy requires an active Rage first")
                                return
                            fx = self.char.setdefault("active_effects", [])
                            if "Frenzy" in fx:
                                fx.remove("Frenzy")
                                self._toast("😤 Frenzy: OFF")
                            else:
                                fx.append("Frenzy")
                                self._toast("😤 Frenzy: ON — bonus action melee attack each turn "
                                            "for the rest of your rage; 1 exhaustion when it ends")
                            self._mark_dirty()
                            self._refresh_effects_list()
                            return
                        # Try to spend a matching tracked resource first
                        for res in self.char.get("resources", []):
                            rname = str(res.get("name","")).lower()
                            if (key and (key in rname or rname in key)
                                    and res.get("current_max", 0) > 0):
                                # Simple toggles (Rage, Bladesong, Invincible
                                # Conqueror, etc. — anything in
                                # RESOURCE_POOL_TOGGLES): don't spend a second
                                # use if already active — the real toggle for
                                # on/off is the "Active" checkbox on this
                                # resource's own row in the Other tab, which
                                # already correctly manages active_effects.
                                # This button is for STARTING the effect, not
                                # re-affirming one already in progress.
                                # Previously this check (and the matching
                                # activation below) only ever fired for the
                                # literal string "rage" — every other simple
                                # toggle sharing this fallback had a Use
                                # button that correctly spent its resource
                                # but never actually turned the effect on.
                                if _display in RESOURCE_POOL_TOGGLES and _display in self.char.get("active_effects", []):
                                    self._toast(f"⚡ {_display} already active — use the \"Active\" "
                                                f"checkbox on its resource row (Other tab) to end it")
                                    return
                                cur = res.get("current", 0)
                                if cur <= 0:
                                    self._toast(f"✖ {_display}: no uses left "
                                                f"(recharges on {res.get('reset','rest')})")
                                else:
                                    res["current"] = cur - 1
                                    self._toast(f"⚡ Used {_display} "
                                                f"({res['current']}/{res.get('current_max')} left)")
                                    # The resource spend alone wouldn't
                                    # otherwise turn the effect on — every
                                    # mechanical effect of these toggles reads
                                    # active_effects, and this keeps the two
                                    # in sync with what the Other tab's
                                    # checkbox already does, so starting the
                                    # effect from either place works the same.
                                    if _display in RESOURCE_POOL_TOGGLES:
                                        fx = self.char.setdefault("active_effects", [])
                                        if _display not in fx:
                                            fx.append(_display)
                                        self._refresh_combat_weapons()
                                        self._refresh_effects_list()
                                    self._mark_dirty()
                                    self._mark_turn_used(_b)
                                    self._refresh_action_tabs()
                                return
                        # No tracked resource → consume the turn slot + summary
                        self._mark_turn_used(_b)
                        self._toast(f"⚔ {_display}: {_desc[:90]}")
                    use_btn.clicked.connect(_use_ability)
                    # Row click → full rules text (button = do it)
                    card.mousePressEvent = (lambda e, _d=display, _s=source, _x=desc:
                        QMessageBox.information(self, _d,
                            f"<b>{_d}</b><br><i>Source: {_s}</i><br><br>{_x}"))

                for w in (card, lbl_name, lbl_desc, src_badge):
                    w.setToolTip(tooltip_text)

                cl.addWidget(src_badge, 0, Qt.AlignTop)
                cl.addLayout(text_col, 1)
                cl.addWidget(use_btn, 0, Qt.AlignTop)
                if bucket_name in ('Action','Bonus Action','Reaction'):
                    self._bucket_use_btns[bucket_name].append(use_btn)
                grid.addWidget(card, idx // 2, idx % 2)

            if rows:
                # Balance odd counts so the last card doesn't stretch full width
                if len(rows) % 2 == 1:
                    filler = QWidget(); filler.setStyleSheet("background:transparent;")
                    grid.addWidget(filler, (len(rows)-1)//2, 1)
                bl.insertWidget(bl.count()-1, grid_host)
            else:
                hint = {"Action": "Universal actions apply — see any missing? "
                                   "Attack, Dash, Dodge and friends live here.",
                        "Bonus Action": "No bonus actions available — class features, "
                                        "feats, and ★-pinned spells appear here.",
                        "Reaction": "Opportunity Attack is always available. Reaction "
                                    "spells like Shield or Counterspell appear here when known.",
                        "Passive": "Passive features, resources and item charges appear here."}
                empty = _lbl(hint.get(bucket_name, "None for this character"),
                             TEXT3, FS_TINY, wrap=True)
                bl.insertWidget(bl.count()-1, empty)

        # ── Update tab labels with live counts ───────────────────────────────
        _ICONS = {"Action":"⚔","Bonus Action":"✦","Reaction":"⚡","Passive":"◎"}
        _LABELS = {"Action":"Action","Bonus Action":"Bonus Action",
                   "Reaction":"Reaction","Passive":"Other"}
        for ti, bname in enumerate(["Action","Bonus Action","Reaction","Passive"]):
            n = len(buckets.get(bname, []))
            self._action_tabs.setTabText(
                ti, f"{_ICONS[bname]} {_LABELS[bname]}" + (f"  ({n})" if n else ""))
        self._refresh_effects_list()
        self._apply_turn_state()

