import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui.style.theme import *
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
from dnd_app.core.spell_components import spell_component_block_reason
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters, character_filename, validate_character,
)
from dnd_app.core.character import set_subclass, get_class_entry
from dnd_app.data.phbCommon.magic_items import ALL_MAGIC_ITEMS, has_item_effect
from dnd_app.ui.dialogs.levelup_panel import LevelUpPanel
from dnd_app.data.phb2014.classes import CLASS_DICT, CLASS_NAMES, BATTLE_MASTER_MANEUVERS, WILD_MAGIC_SURGE_TABLE
from dnd_app.data.phb2014.races import get_race
from dnd_app.data.phbCommon.backgrounds import get_background
from dnd_app.data.phbCommon.feats import get_feat
from dnd_app.data.phbCommon.spells import get_spell, spells_for_class, ALL_SPELLS
from dnd_app.data.phbCommon.items import (ARMOR, ARMOR_DICT, ALL_WEAPONS, WEAPON_DICT,
    ADVENTURING_GEAR, GEAR_NAMES, MOUNTS, ALL_TOOLS, SIMPLE_MELEE, SIMPLE_RANGED,
    MARTIAL_MELEE, MARTIAL_RANGED, ARTISAN_TOOLS, SPECIAL_ARMOR)
from dnd_app.data.phbCommon.conditions import CONDITIONS


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
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
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
        from dnd_app.data.phb2014.classes import CLASS_NAMES, CLASS_DICT
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
        self._confirm_btn.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2).styleSheet())
        self._confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(self._confirm_btn)
        root.addLayout(btn_row)

        self.selected_class = default_choice
        self._init_in_progress = False
        if default_choice:
            self._on_pick(default_choice)

    def _meets_multiclass_reqs(self, class_name, existing_classes):
        """Delegates to the single canonical check_multiclass_prereq()
        function rather than keeping a second copy of the ability-score
        requirements here, so this dialog's eligibility check and
        multiclass.py's MULTICLASS_PREREQS_2024 can never drift apart
        (e.g. Blood Hunter's real requirement is INT 13 AND (STR or DEX)
        13, not STR AND INT both)."""
        from dnd_app.core.multiclass import check_multiclass_prereq
        if not self.char.get("optional_rules", {}).get("multiclass_ability_reqs", True):
            return True, ""
        base_scores = self.char.get("abilities", {})
        bonuses = self.char.get("ability_bonuses", {})
        scores = {ab: base_scores.get(ab, 10) + bonuses.get(ab, 0) for ab in
                  ("STR", "DEX", "CON", "INT", "WIS", "CHA")}
        return check_multiclass_prereq(class_name, scores)

    def _append_level_preview(self, lines, cls_name, is_new):
        """Appends the HP/spell-slot numbers this pick would actually
        grant — the class's static feature-name list above already says
        WHAT you get, this says how much, so a player can weigh the
        choice (e.g. multiclassing for a feature vs. staying single-class
        for the bigger HP/slot jump) before committing."""
        from dnd_app.core.calculator import preview_level_gain
        try:
            preview = preview_level_gain(self.char, cls_name, is_new)
        except Exception:
            return  # cosmetic preview only — never block leveling on it
        lines.append("")
        con_mod = ability_mod(self.char, "CON")
        lines.append(f"HP: +{preview['hp_gain']} (max {preview['hp_before']} → {preview['hp_after']}, "
                     f"includes CON {sign(con_mod)})")
        if preview["slot_deltas"]:
            slot_bits = ", ".join(
                f"{'+' if d > 0 else ''}{d} Lv{lvl}" for lvl, d in preview["slot_deltas"])
            lines.append(f"Spell slots: {slot_bits}")
        pact_before, pact_after = preview["pact_before"], preview["pact_after"]
        if pact_after and pact_after != pact_before:
            lines.append(f"Pact Magic: {pact_after['count']} slot(s) at level {pact_after['level']}")

    def _append_xp_surplus_note(self, lines):
        """If the character is in XP leveling mode and already has enough
        XP for more than one level, says so — this dialog only ever
        applies one level at a time (same as milestone), so the note
        makes clear the surplus isn't lost, just not auto-applied."""
        if self.char.get("leveling_mode", "milestone") != "xp":
            return
        from dnd_app.core.character import xp_progress
        due = xp_progress(self.char)["levels_due"]
        if due > 1:
            lines.append("")
            lines.append(f"🌟 You have enough XP for {due} levels right now — "
                          f"this uses 1, leaving {due - 1} more to take right after.")

    def _on_pick(self, cls_name):
        if getattr(self, "_init_in_progress", False):
            return
        self.selected_class = cls_name
        from dnd_app.data.phb2014.classes import CLASS_DICT
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
            self._append_level_preview(lines, cls_name, is_new=False)
        else:
            if hasattr(self, "_confirm_btn"):
                self._confirm_btn.setEnabled(True)
            lines.append(f"{cls_name} (new, starts at level 1)")
            lines.append("")
            feats = cdata.get("features", {}).get(1, [])
            if feats:
                lines.append("Gains at level 1:")
                lines.extend(f"  • {f}" for f in feats)
            self._append_level_preview(lines, cls_name, is_new=True)
            lines.append("")
            lines.append(f"Hit Die: d{cdata.get('hit_die', 8)}")
            lines.append(
                "Multiclassing grants only partial proficiencies (per the 2014 PHB "
                "multiclassing table) — not the full starting proficiency list a "
                "level 1 character of this class would normally get.")
        self._append_xp_surplus_note(lines)
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
            from dnd_app.data.phbCommon.spells import ALL_SPELLS
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
            from dnd_app.data.phbCommon.spells import ALL_SPELLS
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
        from dnd_app.data.phbCommon.spells import ALL_SPELLS, spells_for_class_at_level
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
            from dnd_app.ui.dialogs.levelup_panel import FIGHTING_STYLES as MV_FIGHTING_STYLES
            known_styles = self.char.get("fighting_styles", [])
            for s in known_styles:
                self._mv_out_combo.addItem(s.split(" (")[0].strip(), s)
            pool = MV_FIGHTING_STYLES.get(self.selected_class, [])
            for s in pool:
                base_name = s.split(" (")[0].strip()
                if not any(base_name.lower() == ks.split(" (")[0].strip().lower() for ks in known_styles):
                    self._mv_in_combo.addItem(base_name, s)
        elif kind == "maneuver":
            from dnd_app.data.phb2014.classes import BATTLE_MASTER_MANEUVERS
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
            from dnd_app.data.phbCommon.spells import ALL_SPELLS
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
            from dnd_app.data.phb2014.classes import METAMAGIC
            known_mm = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
            for m in known_mm:
                self._sv_out_combo.addItem(m.split(" – ")[0].strip(), m)
            for m in METAMAGIC:
                base_name = m.split(" – ")[0].strip()
                if not any(base_name.lower() == km.split(" – ")[0].strip().lower() for km in known_mm):
                    self._sv_in_combo.addItem(base_name, m)
        elif kind == "cantrip":
            from dnd_app.data.phbCommon.spells import ALL_SPELLS
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




