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


class InfusionsMixin:
    def _sync_infusions_tab(self):
        """Add/remove the Infusions tab as eligibility changes, and refresh
        its content while present. Needed since __init__ builds the tab
        list once, before a freshly-created or just-leveled-up character
        has any infusions known yet, so eligibility must be re-checked
        on every refresh rather than only at construction."""
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
        """Soul of Artifice (Artificer, 20th level) — the
        +1-save-per-attuned-item half is handled in calculator.py; this
        is the "end an infusion to drop to 1 HP instead of 0" half,
        reusing the exact same deactivation logic as the Infusions
        tab."""
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
        from dnd_app.data.phb2014.classes import ARTIFICER_INFUSION_TARGETS
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
        from dnd_app.data.phbCommon.items import WEAPON_DICT, ARMOR_DICT
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

