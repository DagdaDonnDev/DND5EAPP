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


class RestOptionsDialog(QDialog):
    """Unified rest-configuration dialog — shown after finishing a short
    or long rest, surfaces every "you can change X when you finish a
    rest" choice the character actually has, found by searching the
    game's own feature text for short/long rest + change/swap language.
    Extensible: add more entries to _build_options() as more of these
    get confirmed and wired up.

    Currently covers: unpreparing all spells to choose new ones (any
    prepared caster, long rest), and the Artificer Armorer's Arcane
    Armor model swap (short or long rest, smith's tools in hand)."""

    def __init__(self, char, rest_type, parent=None):
        super().__init__(parent)
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
        self.char = char
        self.rest_type = rest_type  # "short" or "long"
        self.setWindowTitle(f"{'Long' if rest_type == 'long' else 'Short'} Rest Options")
        self.setMinimumSize(480, 300)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        self._options = RestOptionsDialog._build_options(char, rest_type)
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

    @staticmethod
    def _build_options(char, rest_type):
        """Static so RestPreviewDialog can reuse this exact list without
        needing a RestOptionsDialog instance — this class stays the
        documented name/reference for "what's reconfigurable on a rest"
        (see the many comments elsewhere pointing to it), it just no
        longer needs to be constructed to compute the list."""
        opts = []
        # Unprepare all spells — any prepared caster, long rest only (this
        # is the normal way of re-choosing prepared spells: 1 minute per
        # spell level during a long rest, PHB p.201-202).
        if rest_type == "long":
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
                "detail": "Requires smith's tools in hand.",
            })
        # Arcane Recovery (Wizard 1+): short rest only (the rule triggers
        # "when you finish a short rest"), once per day (checked via the
        # resource added in update_all), only if there's actually
        # something expended to recover.
        if rest_type == "short":
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
        if rest_type == "long" and "eladrin" in race.lower() and char.get("_choices", {}).get("eladrin_season"):
            opts.append({
                "kind": "eladrin_season",
                "label": "Change Eladrin season",
                "detail": "Changes which additional effect your Fey Step bonus action has.",
            })
        # Githyanki (MPMM)'s Astral Knowledge / Astral Elf's Astral Trance:
        # both grant "proficiency in one skill and with one weapon or tool
        # of your choice ... until the end of your next long rest" —
        # re-chosen every long rest, not a one-time pick.
        if rest_type == "long" and race in ("Githyanki (MPMM)", "Astral Elf") and \
                char.get("_choices", {}).get("astral_knowledge_skill"):
            trait_name = "Astral Knowledge" if race == "Githyanki (MPMM)" else "Astral Trance"
            opts.append({
                "kind": "astral_knowledge_swap",
                "label": f"Re-choose {trait_name}'s skill and weapon/tool proficiencies",
                "detail": "Changes which skill and which weapon or tool proficiency you currently "
                          "have from this trait.",
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
        if rest_type == "long" and char.get("_choices", {}).get("guidance_of_the_spirits_skill"):
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
        if rest_type == "long" and char.get("_choices", {}).get("lunar_phase"):
            opts.append({
                "kind": "lunar_phase_swap",
                "label": "Change your Lunar Embodiment phase",
                "detail": "Choose Full Moon, New Moon, or Crescent Moon.",
            })
        return opts

    def get_selected(self):
        return [kind for kind, cb in self._checks.items() if cb.isChecked()]




class RestPreviewDialog(QDialog):
    """Shows exactly what a Short/Long Rest is about to restore/reset —
    HP, hit dice, spell slots, resources — before it's applied, instead
    of the rest silently happening with only a toast confirming it
    afterward. Purely informational (Confirm/Cancel); the real apply
    logic in CharacterSheet._short_rest()/_long_rest() is unchanged and
    only runs once this dialog is confirmed. `preview` is built by
    CharacterSheet._preview_short_rest()/_preview_long_rest() — plain
    filters over current character state, not a simulation, so this
    can't drift from what those methods actually do next.

    `options` (from RestOptionsDialog._build_options()) folds the
    "anything you'd like to reconfigure on this rest" checklist into
    this same preview dialog rather than a separate confirm step, so
    the player gets one dialog and one Confirm for the whole rest.
    get_selected() below is read the same way RestOptionsDialog's is."""

    def __init__(self, rest_type: str, preview: dict, options: list, parent=None):
        super().__init__(parent)
        from dnd_app.ui.style.theme import sync_globals as _sg; _sg(globals())
        self.rest_type = rest_type
        self._options = options
        self._checks = {}
        label = "Short Rest" if rest_type == "short" else "Long Rest"
        icon = "⏸" if rest_type == "short" else "🌙"
        self.setWindowTitle(label)
        self.setMinimumWidth(440)
        self.setStyleSheet(f"QDialog{{background:{BG};}}")
        root = QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(12)
        root.addWidget(_lbl(f"{icon}  {label}", GOLD2, FS_HEAD, bold=True))

        card = _card(qa(TEAL,0x44)); cl = QVBoxLayout(card)
        cl.setContentsMargins(14,12,14,14); cl.setSpacing(4)
        cl.addWidget(_lbl("WHAT THIS WILL DO", TEAL2, FS_SMALL, bold=True))
        cl.addWidget(_lbl("\n".join(self._build_lines(rest_type, preview)), TEXT, FS_BODY, wrap=True))
        root.addWidget(card)

        if options:
            opt_card = _card(qa(INDIGO,0x44)); ol = QVBoxLayout(opt_card)
            ol.setContentsMargins(14,12,14,14); ol.setSpacing(6)
            ol.addWidget(_lbl("ALSO RECONFIGURE?", IND2, FS_SMALL, bold=True))
            ol.addWidget(_lbl("Check anything you'd like to change as part of this rest.",
                               TEXT3, FS_TINY, wrap=True))
            for opt in options:
                cb = QCheckBox(opt["label"])
                cb.setToolTip(opt.get("detail", ""))
                ol.addWidget(cb)
                self._checks[opt["kind"]] = cb
            root.addWidget(opt_card)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton(f"Confirm {label}"); confirm_btn.setFixedHeight(34)
        confirm_btn.setStyleSheet(_btn("", GOLD, variant="cta", text_color=GOLD2).styleSheet())
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)

    def get_selected(self):
        return [kind for kind, cb in self._checks.items() if cb.isChecked()]

    @staticmethod
    def _build_lines(rest_type: str, preview: dict) -> list:
        lines = []
        if rest_type == "short":
            if preview["hp"] >= preview["max_hp"]:
                lines.append(f"HP: already full ({preview['max_hp']})")
            elif preview["hit_dice_available"] > 0:
                lines.append(f"HP: {preview['hp']}/{preview['max_hp']}  —  "
                              f"{preview['hit_dice_available']} hit dice available, "
                              f"you'll choose how many to spend next")
            else:
                lines.append(f"HP: {preview['hp']}/{preview['max_hp']}  —  no hit dice remaining")
        else:
            heal = preview["max_hp"] - preview["hp"]
            if heal > 0:
                lines.append(f"HP: {preview['hp']} → {preview['max_hp']} (full heal, +{heal})")
            else:
                lines.append(f"HP: already full ({preview['max_hp']})")
            if preview["temp_hp"] > 0:
                lines.append(f"Temporary HP: {preview['temp_hp']} → 0 (lost)")
            if preview["hit_dice_restored"] > 0:
                lines.append(f"Hit Dice: +{preview['hit_dice_restored']} restored")
            if preview["exhaustion"] > 0:
                lines.append(f"Exhaustion: level {preview['exhaustion']} → {preview['exhaustion_after']}")
            if preview["death_reset"]:
                lines.append("Death saves: cleared")
            if preview["was_concentrating"]:
                lines.append(f"Concentration on {preview['was_concentrating']}: will end")

        if preview.get("slot_levels_reset"):
            levels = ", ".join(f"Lv{lvl}" for lvl in preview["slot_levels_reset"])
            lines.append(f"Spell slots restored: {levels}")
        if preview.get("pact_restore"):
            lines.append("Pact Magic slots: restored")
        if preview.get("resets"):
            lines.append("")
            lines.append("Resources restored:")
            lines.extend(f"  • {name}: {cur} → {tgt}" for name, cur, tgt in preview["resets"])
        if preview.get("fading"):
            lines.append("")
            lines.append("Will fade/end:")
            lines.extend(f"  • {n}" for n in preview["fading"])
        return lines




def _spell_progression_tables_static():
    """Standalone version of CharacterSheet._spell_progression_tables,
    usable without a CharacterSheet instance (RestOptionsDialog doesn't
    have one)."""
    from dnd_app.data.phb2014.classes import CLASS_DICT
    prep_ab = {cn for cn, cd in CLASS_DICT.items() if cd.get("spell_ability") and cd.get("has_spells")
               and cn in ("Cleric", "Druid", "Paladin", "Artificer", "Wizard")}
    return None, None, None, prep_ab




def _all_relevant_choice_ids(char_snapshot: dict) -> set:
    """Every pending-choice id structurally relevant to this exact
    character state, regardless of whether it's already been answered
    (computed against a scratch copy with _choices cleared, so an
    already-answered choice still shows up here). Union of every
    choice-generating function the Choices tab actually combines.
    Used to diff "before" vs "after" a race/background/class/subclass/
    level change and prune any choice from the real character's
    _choices that's no longer relevant — without this, changing away
    from something never lets you make its choice differently, and can
    leave an old choice's pool/value silently misapplied to whatever
    replaced it."""
    import copy
    from dnd_app.core.builder import get_choices_needed
    from dnd_app.ui.dialogs.levelup_panel import (
        _get_subclass_choices, _get_race_choices, _get_class_tool_choices,
        _get_feat_choices, _get_dm_reward_choices, _get_optional_feature_choices,
    )
    scratch = copy.deepcopy(char_snapshot)
    scratch["_choices"] = {}
    all_choices = (get_choices_needed(scratch) + _get_subclass_choices(scratch)
                   + _get_race_choices(scratch) + _get_class_tool_choices(scratch)
                   + _get_feat_choices(scratch) + _get_dm_reward_choices(scratch)
                   + _get_optional_feature_choices(scratch))
    return {c["id"] for c in all_choices if "id" in c}


# Choice ids from _get_race_choices()/get_choices_needed() that are keyed
# generically (by choice TYPE, e.g. "race_skill_profs") rather than by the
# specific race/background name — so _all_relevant_choice_ids()'s before/
# after diff can't tell "still relevant" from "relevant to a DIFFERENT
# race/background now, with a completely different pool, but the old
# answer looks superficially complete". Astral Elf and Githyanki (MPMM)
# happen to share the same two ids since they're mechanically identical.
RACE_SCOPED_CHOICE_IDS = {
    "race_skill_profs", "race_tool_profs", "race_skill_or_tool_profs",
    "aasimar_revelation", "astral_knowledge_skill",
    "astral_knowledge_weapon_or_tool", "eladrin_season", "human_extra_language",
}
BACKGROUND_SCOPED_CHOICE_IDS = {"bg_languages", "bg_skill_profs", "bg_tool_profs"}




def _prune_stale_choices(char: dict, stale_ids: set) -> set:
    """Remove the given choice ids from char["_choices"] if present.
    Returns the ids actually removed."""
    store = char.get("_choices", {})
    removed = {cid for cid in stale_ids if cid in store}
    for cid in removed:
        store.pop(cid, None)
    return removed




