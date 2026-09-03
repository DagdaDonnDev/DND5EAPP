import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui.style.theme import *
from ...shared import *
# `import *` silently skips underscore-prefixed names when a module has no
# __all__ (shared.py doesn't) — _btn/_pill need an explicit import for that
# reason. _lbl/_card/_sep don't (they're defined a few lines down as local
# aliases to h/card/hline, which ARE plain names the wildcard import above
# already brought in).
from ...shared import _btn, _pill
from ...widgets import FlowLayout, FlowContainer
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
from .base import *
from .base import _lbl, _sep, _card


class AbilitiesMixin:
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
            blk.roll_requested.connect(
                lambda a: self._quick_roll_toast(f"{AB_FULL[a]} check", ability_mod(self.char, a)))
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
            roll_btn = _btn("🎲", TEAL, variant="ghost", width=26, height=24, radius=5,
                             font_size=FS_SMALL, tooltip=f"Roll {AB_FULL[ab]} save ({sign(val)})")
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
            adv_badge = _lbl("Adv", GREEN2, FS_SMALL, bold=True, wrap=False)
            if not hasattr(self, "_save_adv_badges"):
                self._save_adv_badges = {}
            self._save_adv_badges[ab] = adv_badge
            # Must be parented (addWidget) BEFORE the first setVisible()
            # call below -- a QLabel with no parent yet is a genuine
            # top-level window as far as Qt/the OS window manager is
            # concerned, so calling setVisible(True) on it here (when a
            # class/race grants save advantage) briefly flashed a real,
            # full-chrome window on screen during initial sheet build.
            rl.addWidget(adv_badge)
            self._update_save_advantage_badge(ab)

            # Condition-based auto-fail/disadvantage badge — separate from
            # the racial/class advantage badge above since it's a
            # different, transient mechanic (Paralyzed/Stunned/
            # Unconscious auto-fail STR/DEX saves outright; Restrained
            # imposes disadvantage on DEX specifically).
            cond_save_badge = _lbl("", CRIM2, FS_BODY, bold=True, wrap=False)
            if not hasattr(self, "_save_cond_badges"):
                self._save_cond_badges = {}
            self._save_cond_badges[ab] = cond_save_badge
            # Same parent-before-setVisible ordering as adv_badge above.
            rl.addWidget(cond_save_badge)
            self._update_save_condition_badge(ab)

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

    def _quick_roll_toast(self, label: str, bonus: int):
        import random
        d = random.randint(1, 20)
        total = d + bonus
        flair = ""
        if d == 20: flair = "  🌟 NAT 20!"
        elif d == 1: flair = "  💀 Nat 1…"
        self._toast(f"🎲 {label}: [{d}] {bonus:+d} = {total}{flair}", 4200)

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
            notes = "\n".join(f"• {s['source']}: {s['note']}" for s in status["sources"])
            badge.setText("Adv")
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

