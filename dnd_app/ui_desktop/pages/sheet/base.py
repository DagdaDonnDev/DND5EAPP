import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui_desktop.style.theme import *
from ...shared import *
# `import *` silently skips underscore-prefixed names when a module has no
# __all__ (shared.py doesn't) — _btn/_pill need an explicit import for that
# reason. _lbl/_card/_sep don't (they're defined a few lines down as local
# aliases to h/card/hline, which ARE plain names the wildcard import above
# already brought in).
from ...shared import _btn, _pill
from ...widgets import FlowLayout, FlowContainer
from dnd_app.ui_desktop.dialogs.arcane_recovery import ArcaneRecoveryDialog
from dnd_app.ui_desktop.dialogs.rest import RestOptionsDialog, RestPreviewDialog
from dnd_app.core.choices import _all_relevant_choice_ids, _prune_stale_choices
from dnd_app.ui_desktop.dialogs.levelup_multiclass import LevelUpMulticlassDialog
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
from dnd_app.core.effects import WILDSHAPE_BLOCKED_FEATURES, RESOURCE_POOL_TOGGLES
from dnd_app.core.character import rest_options


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

# Local aliases matching the short names used throughout this file.
_lbl = h
_sep = hline
_card = card



class BaseSheetMixin:
    def __init__(self, char: dict, parent=None, save_path: str = None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals as _sg
        _sg(globals())
        # CharacterSheet is composed of 12 mixin files (see
        # dnd_app/ui_desktop/pages/sheet/__init__.py); every one of them does its
        # own `from dnd_app.ui_desktop.style.theme import *` at module level, same
        # as this file. That import only ever runs ONCE per process --
        # Python caches modules -- so it captures whatever theme was
        # active the very first time each mixin module was imported and
        # never updates again. sync_globals(globals()) above only patches
        # THIS module's (base.py's) namespace; every other mixin
        # (abilities/skills/combat/gear/companions/choices/infusions/
        # spells/features/traits/action_tabs) kept rendering with
        # whatever colors were active at first launch regardless of any
        # later theme switch -- the HP boxes, weapon damage badges, the
        # Combat tab's turn bar, and the Action/Bonus/Reaction sub-tabs
        # all live in combat.py/action_tabs.py, never resynced until now.
        import dnd_app.ui_desktop.pages.sheet.abilities as _m_abilities
        import dnd_app.ui_desktop.pages.sheet.skills as _m_skills
        import dnd_app.ui_desktop.pages.sheet.combat as _m_combat
        import dnd_app.ui_desktop.pages.sheet.gear as _m_gear
        import dnd_app.ui_desktop.pages.sheet.companions as _m_companions
        import dnd_app.ui_desktop.pages.sheet.choices as _m_choices
        import dnd_app.ui_desktop.pages.sheet.infusions as _m_infusions
        import dnd_app.ui_desktop.pages.sheet.spells as _m_spells
        import dnd_app.ui_desktop.pages.sheet.features as _m_features
        import dnd_app.ui_desktop.pages.sheet.traits as _m_traits
        import dnd_app.ui_desktop.pages.sheet.action_tabs as _m_action_tabs
        for _m in (_m_abilities, _m_skills, _m_combat, _m_gear, _m_companions,
                   _m_choices, _m_infusions, _m_spells, _m_features, _m_traits,
                   _m_action_tabs):
            _sg(_m.__dict__)
        self.ctrl = CharacterController(char)
        self.char = self.ctrl.char
        self._spell_rows = []
        self._level_headers = {}
        self._slot_bars = {}
        self._resource_widgets = []
        self._weapon_row_widgets = []
        self._ammo_counters = []     # (ammo kind, counter button) per weapon row
        self._magic_item_rows = []
        self._resource_widgets: list = []   # populated by _build_resource_rows
        self._blocking_refresh = False
        self._dirty = False
        # The exact file this character was loaded from (None for a
        # brand-new character) -- _save() reuses this instead of always
        # re-deriving a path from the current name, or renaming the
        # character (editing the header name field, then Save) would
        # silently create a second file under the new name and leave
        # the original one behind as an orphan.
        self._save_path = save_path
        self.ctrl.subscribe(self._on_char_updated)
        self._build_ui()
        self.ctrl.refresh()
        self._load()
        self.ctrl.mark_ui_ready()
        # opened from a save with Rage, Bladesong... still on: have they ended?
        QTimer.singleShot(350, self._ask_leftover_effects)
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

        # Immersive Health / Immersive Exhaustion: colour drains as HP
        # drops, and a dark frame closes in with exhaustion (see
        # ui_desktop/immersive.py)
        from dnd_app.ui_desktop.immersive import SheetImmersion
        self._immersion = SheetImmersion(self)

    def _autosave(self):
        """Silently write a .autosave backup when there are unsaved changes."""
        if not getattr(self, "_dirty", False):
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
                win._sheet._toast("Refreshed")
        else:
            # Defensive fallback if this widget is ever used without a
            # CharacterCreatorApp parent (e.g. an isolated test harness).
            self._blocking_refresh = False
            self._on_char_updated(self.char)
            self._toast("Refreshed")

    def _ask_leftover_effects(self):
        """A character just opened from a save, with effects a short rest
        would end still on (core/action_use.py leftover_effects): ask
        whether they've ended, and end the ticked ones."""
        from dnd_app.core.action_use import take_leftover_effects, end_effects
        names = take_leftover_effects(self.char)
        if not names:
            return
        from dnd_app.ui_desktop.dialogs.leftover_effects import LeftoverEffectsDialog
        dlg = LeftoverEffectsDialog(names, self)
        if dlg.exec() == QDialog.Accepted and end_effects(self.char, dlg.ticked()):
            self._mark_dirty()
            self.ctrl.refresh()

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

    def _mark_dirty(self):
        self._dirty = True

    def _preview_short_rest(self) -> dict:
        """Non-mutating preview of what _short_rest() is about to do,
        for the confirm dialog shown before it runs. These are plain
        filters over current state -- the exact same conditions
        _short_rest() itself checks right after -- not a simulation, so
        there's no separate logic to drift out of sync."""
        char = self.char
        hd_model = char.get("hit_dice", {})
        hit_dice_available = sum(d.get("remaining", 0) for d in hd_model.values())
        cur, mx = char.get("current_hp", 0), char.get("max_hp", 0)

        resets = []
        for r in char.get("resources", []):
            if r.get("reset") in ("SR", "sr", "SR/LR"):
                target = r.get("current_max") or r.get("max", 0)
                if r.get("current", 0) != target:
                    resets.append((r.get("name", "?"), r.get("current", 0), target))
        from dnd_app.core.character import class_levels as _cls_lvls_sr
        if _cls_lvls_sr(char).get("Bard", 0) >= 5:
            for r in char.get("resources", []):
                if "bardic inspiration" in str(r.get("name", "")).lower():
                    target = r.get("current_max") or r.get("max", 0)
                    if r.get("current", 0) != target:
                        resets.append((r.get("name", "?"), r.get("current", 0), target))

        pact_restore = char.get("pact_slots_used", 0) > 0
        from dnd_app.core.effects import EFFECT_TABLE
        fading = [n for n in char.get("active_effects", [])
                  if EFFECT_TABLE.get(n, {}).get("duration_category") == "short"
                  or n in RESOURCE_POOL_TOGGLES]
        return {
            "hp": cur, "max_hp": mx, "hit_dice_available": hit_dice_available,
            "resets": resets, "pact_restore": pact_restore, "fading": fading,
        }

    def _preview_long_rest(self) -> dict:
        """Non-mutating preview of what _long_rest() is about to do —
        same reasoning as _preview_short_rest(), except hit-dice
        recovery isn't a simple filter (restore_hit_dice_pool()
        distributes across die types), so that one piece runs the real
        pool math on a throwaway copy of just the hit-dice/classes data
        rather than re-deriving the distribution logic here."""
        char = self.char
        cur, mx = char.get("current_hp", 0), char.get("max_hp", 0)
        temp_hp = char.get("temp_hp", 0)

        import copy
        from dnd_app.core.calculator import restore_hit_dice_pool
        hd_before = char.get("hit_dice", {})
        scratch = {"hit_dice": copy.deepcopy(hd_before), "classes": char.get("classes", [])}
        hit_dice_restored = restore_hit_dice_pool(scratch)

        resets = []
        for r in char.get("resources", []):
            if r.get("reset") in ("LR", "lr", "SR", "sr", "SR/LR"):
                target = r.get("current_max") or r.get("max", 0)
                if r.get("current", 0) != target:
                    resets.append((r.get("name", "?"), r.get("current", 0), target))

        slots_used = char.get("spell_slots_used", [0] * 9)
        slot_levels_reset = [i + 1 for i, v in enumerate(slots_used) if v > 0]
        pact_restore = char.get("pact_slots_used", 0) > 0

        death_saves = char.get("death_saves", {})
        death_reset = death_saves.get("successes", 0) > 0 or death_saves.get("failures", 0) > 0

        exhaustion = char.get("exhaustion", 0)
        was_concentrating = char.get("concentration", {}).get("spell")

        from dnd_app.core.effects import EFFECT_TABLE
        fading = [n for n in char.get("active_effects", [])
                  if EFFECT_TABLE.get(n, {}).get("duration_category") in ("short", "long")
                  or n in RESOURCE_POOL_TOGGLES]

        return {
            "hp": cur, "max_hp": mx, "temp_hp": temp_hp,
            "hit_dice_restored": hit_dice_restored,
            "resets": resets, "slot_levels_reset": slot_levels_reset,
            "pact_restore": pact_restore, "death_reset": death_reset,
            "exhaustion": exhaustion, "exhaustion_after": max(0, exhaustion - 1),
            "was_concentrating": was_concentrating, "fading": fading,
        }

    def _short_rest(self):
        """Short rest: preview what it'll restore/reset, then optionally
        spend hit dice to heal, reset SR resources."""
        from dnd_app.core.calculator import update_all
        import random
        char = self.char

        preview = self._preview_short_rest()
        options = rest_options(char, "short")
        dlg = RestPreviewDialog("short", preview, options, self)
        if dlg.exec() != QDialog.Accepted:
            return
        selected_options = dlg.get_selected()

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
        # Reset SR resources. Was ("SR","sr") only -- silently excluded
        # every resource tagged the compound "SR/LR" (Hexblade's Curse,
        # Misty Escape, Indestructible Life, Mutagens, Control Undead,
        # Vow of Enmity, Favored by the Gods, Firbolg Magic, and now
        # Wild Shape), which is a real, distinct value used elsewhere in
        # this very file (RESET_COLORS above) and is the whole point of
        # a prior "SR vs SR/LR" audit that retagged those 8 resources to
        # it -- but that audit only fixed the TAG, not this loop, so
        # none of them were actually resetting via the real Rest button.
        for r in char.get("resources", []):
            if r.get("reset") in ("SR", "sr", "SR/LR"):
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
        expired += self._clear_active_toggles()
        update_all(char)
        self.ctrl.refresh()
        self._mark_dirty()
        self._apply_rest_options(selected_options)
        if dice_spent:
            self._toast(f"Short rest: spent {dice_spent} hit dice, healed {healed} HP")
        else:
            self._toast("Short rest complete — SR resources restored")
        if expired:
            self._toast(f"Faded: {', '.join(expired)}")

    def _long_rest(self):
        """Long rest: preview what it'll restore/reset, then full HP,
        all resources reset, reduce exhaustion by 1."""
        from dnd_app.core.calculator import update_all
        from dnd_app.core.builder import rebuild
        from dnd_app.core.character import long_rest_block_reason
        char = self.char
        why = long_rest_block_reason(char)   # e.g. at 0 HP
        if why:
            QMessageBox.information(self, "Long Rest", f"Can't take a long rest — {why}.")
            return

        preview = self._preview_long_rest()
        options = rest_options(char, "long")
        dlg = RestPreviewDialog("long", preview, options, self)
        if dlg.exec() != QDialog.Accepted:
            return
        selected_options = dlg.get_selected()

        # Restore HP
        char["current_hp"] = char.get("max_hp", 0)
        char["temp_hp"] = 0
        # Restore hit dice as a shared pool across all die types (PHB p.186) —
        # NOT independently per type, which either under- or over-restored
        # depending on class layout.
        from dnd_app.core.calculator import restore_hit_dice_pool
        restore_hit_dice_pool(char)
        # Reset all LR (and SR, and SR/LR) resources -- see the matching
        # note in _short_rest() above; this loop was already broad
        # enough to catch plain "SR" but still missed "SR/LR" the same
        # way.
        for r in char.get("resources", []):
            if r.get("reset") in ("LR", "lr", "SR", "sr", "SR/LR"):
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
        expired += self._clear_active_toggles()
        # A long rest is 8 hours -- well beyond any spell's concentration
        # duration -- so whatever was being concentrated on has long since
        # ended by the time the rest completes. Wasn't cleared here
        # before, so a stale "concentrating on X" indicator could persist
        # indefinitely across rests with nothing left to justify it.
        was_concentrating = self.char.get("concentration", {}).get("spell")
        if was_concentrating:
            drop_concentration(char)
            expired.append(f"concentration on {was_concentrating}")
        # dawn comes: magic items get their charges back (core/magic_items.py)
        from dnd_app.core.magic_items import charges_at_dawn
        dawn = charges_at_dawn(char)
        rebuild(char); update_all(char)
        self.ctrl.refresh()
        self._mark_dirty()
        self._apply_rest_options(selected_options)
        from dnd_app.data.flavor_text import random_long_rest_dream
        items = ("\nAt dawn: " + "; ".join(dawn)) if dawn else ""
        if expired:
            self._toast(f"Faded: {', '.join(expired)}{items}")
        else:
            self._toast(f"Long rest complete — HP, slots & resources restored{items}\n"
                        f"{random_long_rest_dream()}")

    def _clear_active_toggles(self) -> list[str]:
        """Clear any RESOURCE_POOL_TOGGLES member (Rage, Reckless Attack,
        Bladesong, Hexblade's Curse, etc.) still marked active in
        active_effects when a rest completes. These are all
        combat-duration on/off states -- by the time a short rest (at
        least an hour, RAW) or long rest (8 hours) has actually
        completed, every one of them would already have naturally ended
        long before the rest even started, whether or not the player
        remembered to manually toggle it off. A rest must clear the
        on/off state itself, not just each toggle's own RESOURCE reset
        (uses remaining) — otherwise the state stays stuck active
        indefinitely (a level-up next session could still show "Rage:
        ON" from days ago)."""
        fx = self.char.get("active_effects", [])
        cleared = [name for name in fx if name in RESOURCE_POOL_TOGGLES]
        for name in cleared:
            fx.remove(name)
        return cleared

    def _clear_expired_active_effects(self, categories: tuple[str, ...]) -> list[str]:
        """Remove active_effects (mainly consumable potions) whose
        EFFECT_TABLE entry's duration_category is in categories — 'short'
        for effects lasting about an hour or less (a short rest takes at
        least that long per RAW), 'long' for effects that outlast a short
        rest but not a full night. Effects with no duration_category are
        untouched -- manual removal only. Returns the names actually
        removed, for the rest toast."""
        from dnd_app.core.effects import EFFECT_TABLE
        fx = self.char.get("active_effects", [])
        removed = [n for n in fx if EFFECT_TABLE.get(n, {}).get("duration_category") in categories]
        for n in removed:
            fx.remove(n)
        return removed

    def _apply_rest_options(self, selected: list):
        """Applies whichever rest-changeable options the player checked
        in RestPreviewDialog's "ALSO RECONFIGURE?" section (built from
        core/character.py's rest_options()). Folded into the single
        preview-and-confirm dialog shown BEFORE the rest applies, so
        confirming a rest is only ever one dialog, not two back to back.
        A checked option that needs a specific new value (which model,
        which skill, etc.) still asks via its own QInputDialog below —
        an unavoidable, expected follow-up for picking a value."""
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
                self._toast(f"Unprepared {removed} spell(s) — pick new ones from the Spells tab")
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
                self._toast(f"Arcane Armor model changed to {choice.split(' – ')[0]}")
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
                    self._toast(f"Arcane Recovery: recovered {len(to_recover)} slot(s) "
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
                self._toast(f"Eladrin season changed to {choice.split(' – ')[0]}")
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
                    self._toast(f"{choice} bonded as your pact weapon")
                    changed_anything = True

        if "pact_tome_replace" in selected:
            self._toast("Received a replacement Book of Shadows from your patron")
            changed_anything = True

        if "pact_talisman_replace" in selected:
            self._toast("Received a replacement Talisman from your patron")
            changed_anything = True

        if "guidance_spirits_swap" in selected:
            from dnd_app.core.choices import ALL_SKILLS
            current = char.get("_choices", {}).get("guidance_of_the_spirits_skill", [])
            choice, ok = QInputDialog.getItem(
                self, "Guidance of the Spirits", "New skill:", ALL_SKILLS,
                ALL_SKILLS.index(current[0]) if current and current[0] in ALL_SKILLS else 0, False)
            if ok and choice:
                char.setdefault("_choices", {})["guidance_of_the_spirits_skill"] = [choice]
                self._toast(f"Guidance of the Spirits now grants {choice}")
                changed_anything = True

        if "whispers_dead_swap" in selected:
            from dnd_app.core.choices import ALL_SKILLS
            from dnd_app.data.feature_ui_interactions import TOOLS as ALL_TOOLS
            pool = ALL_SKILLS + ALL_TOOLS
            current = char.get("_choices", {}).get("whispers_of_the_dead_prof", [])
            choice, ok = QInputDialog.getItem(
                self, "Whispers of the Dead", "New proficiency:", pool,
                pool.index(current[0]) if current and current[0] in pool else 0, False)
            if ok and choice:
                char.setdefault("_choices", {})["whispers_of_the_dead_prof"] = [choice]
                self._toast(f"Whispers of the Dead now grants {choice}")
                changed_anything = True

        if "lunar_phase_swap" in selected:
            pool = ["Full Moon", "New Moon", "Crescent Moon"]
            current = char.get("_choices", {}).get("lunar_phase", [])
            choice, ok = QInputDialog.getItem(
                self, "Lunar Embodiment", "New phase:", pool,
                pool.index(current[0]) if current and current[0] in pool else 0, False)
            if ok and choice:
                char.setdefault("_choices", {})["lunar_phase"] = [choice]
                self._toast(f"Lunar phase changed to {choice}")
                changed_anything = True

        if "astral_knowledge_swap" in selected:
            from dnd_app.core.choices import ALL_SKILLS
            from dnd_app.data.items import WEAPON_NAMES, ALL_TOOLS
            race = char.get("species") or char.get("race", "")
            trait_name = "Astral Knowledge" if race == "Githyanki (MPMM)" else "Astral Trance"
            current_sk = char.get("_choices", {}).get("astral_knowledge_skill", [])
            sk_choice, ok = QInputDialog.getItem(
                self, trait_name, "New skill proficiency:", ALL_SKILLS,
                ALL_SKILLS.index(current_sk[0]) if current_sk and current_sk[0] in ALL_SKILLS else 0, False)
            if ok and sk_choice:
                char.setdefault("_choices", {})["astral_knowledge_skill"] = [sk_choice]
                wt_pool = WEAPON_NAMES + ALL_TOOLS
                current_wt = char.get("_choices", {}).get("astral_knowledge_weapon_or_tool", [])
                wt_choice, ok2 = QInputDialog.getItem(
                    self, trait_name, "New weapon or tool proficiency:", wt_pool,
                    wt_pool.index(current_wt[0]) if current_wt and current_wt[0] in wt_pool else 0, False)
                if ok2 and wt_choice:
                    char.setdefault("_choices", {})["astral_knowledge_weapon_or_tool"] = [wt_choice]
                    self._toast(f"{trait_name}: {sk_choice}, {wt_choice}")
                    changed_anything = True

        if changed_anything:
            _rebuild(char); _update_all(char)
            self.ctrl.refresh()
            self._mark_dirty()

    def _save(self):
        """Save current character to disk."""
        from dnd_app.core.save_load import save_character, character_filename
        import os
        # Overwrite the exact file this character was loaded from, when
        # known -- otherwise (a brand-new character) derive one from its
        # name via character_filename(), which must match how every
        # other writer (initial wizard save, autosave, Duplicate
        # Character) names files, or Save would create a different file
        # than the one already on disk. Without _save_path, renaming a
        # character (editing the header field) and then hitting Save --
        # e.g. via File > Save, which flushes that field into self.char
        # first -- would silently create a second file under the new
        # name and leave the original behind as an orphan, since the
        # path was always re-derived from whatever the current name is.
        path = self._save_path or character_filename(self.char)
        if not self._save_path:
            # a new file -- never on top of another character's
            from dnd_app.core.save_load import name_in_use, NAME_IN_USE_MESSAGE
            if os.path.exists(path) or name_in_use(self.char.get("name", "")):
                QMessageBox.warning(self, "Name Already Used", NAME_IN_USE_MESSAGE)
                return
        save_character(self.char, path)
        self._save_path = path
        self._dirty = False
        self._update_title()
        self._toast(f"Saved to {os.path.basename(path)}")

    def _auto_save(self):
        """Save quietly after character creation, level up/down and
        confirmed choices -- the same file Save writes, no toast. Skipped
        (no error) if the character can't be saved yet."""
        from dnd_app.core.save_load import save_character, character_filename
        if hasattr(self, "_collect"):
            self._collect()
        if not validate_character(self.char)[0]:
            return
        path = self._save_path or character_filename(self.char)
        if not self._save_path:
            import os
            from dnd_app.core.save_load import name_in_use
            if os.path.exists(path) or name_in_use(self.char.get("name", "")):
                return      # would replace another character's file
        try:
            save_character(self.char, path)
        except (OSError, ValueError):
            return
        self._save_path = path
        self._dirty = False
        self._update_title()

    def _load_dialog(self):
        """Open a saved character via file dialog."""
        from PySide6.QtWidgets import QFileDialog
        from dnd_app.core.save_load import load_character
        import os
        from dnd_app.core.save_load import get_save_dir
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Character", get_save_dir(), "Character Files (*.json)")
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
                QTimer.singleShot(350, self._ask_leftover_effects)

    def _export_dialog(self):
        """Export the character for a DM to review or as a personal
        quick-reference cheat sheet — separate from the JSON save format,
        which round-trips back into the app but isn't meant for a human
        to read directly. Two formats: a plain-text summary (stats,
        skills, proficiencies, senses, weapons, resources, spells, magic
        items, full action/bonus-action/reaction/passive list), or the
        official WotC fillable PDF sheet filled in with this character's
        real data."""
        options = [
            "Official character sheet (PDF)",
            "Plain text summary (.txt)",
        ]
        choice, ok = QInputDialog.getItem(
            self, "Export Character", "Format:", options, 0, False)
        if not ok:
            return
        if choice.startswith("Official"):
            self._export_pdf_dialog()
        else:
            self._export_text_dialog()

    def _export_text_dialog(self):
        from PySide6.QtWidgets import QFileDialog
        from dnd_app.core.save_load import export_character_text
        import os
        from dnd_app.core.save_load import character_export_dir, character_folder_name
        # the character's own folder in the save location (same as Android)
        name = character_folder_name(self.char)
        default_path = os.path.join(character_export_dir(self.char), f"{name} - Character Sheet.txt")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Character Sheet", default_path, "Text Files (*.txt)")
        if not path:
            return
        text = export_character_text(self.char)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._toast(f"Exported to {os.path.basename(path)}")
        except OSError as e:
            QMessageBox.warning(self, "Export Failed", f"Could not write file:\n{e}")

    def _export_pdf_dialog(self):
        from PySide6.QtWidgets import QFileDialog
        from dnd_app.core.pdf_sheet import export_official_pdf, TEMPLATE_PATH
        import os
        if not os.path.exists(TEMPLATE_PATH):
            QMessageBox.warning(
                self, "Export Failed",
                f"The official character sheet template is missing:\n{TEMPLATE_PATH}")
            return
        from dnd_app.core.save_load import character_export_dir, character_folder_name
        # the character's own folder in the save location (same as Android)
        name = character_folder_name(self.char)
        default_path = os.path.join(character_export_dir(self.char), f"{name} - Character Sheet.pdf")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Character Sheet (PDF)", default_path, "PDF Files (*.pdf)")
        if not path:
            return
        try:
            export_official_pdf(self.char, path)
            self._toast(f"Exported to {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not write PDF:\n{e}")


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
        # (#id selector: a bare QFrame{...} rule would also hit every QLabel
        # inside -- QLabel is a QFrame -- giving each one a bottom border)
        header = QFrame(); header.setObjectName("sheetHeader")
        self._sheet_header = header   # its width decides how the class cards fit
        header.setStyleSheet(f"QFrame#sheetHeader{{background:{SURF};border-bottom:2px solid {BORDER};}}")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header); hl.setContentsMargins(16,0,16,0); hl.setSpacing(10)

        # ← Menu
        back_btn = _btn("← Menu", variant="neutral", width=90, radius=7, font_size=FS_SMALL)
        back_btn.clicked.connect(self._on_back_clicked)
        hl.addWidget(back_btn, 0, Qt.AlignVCenter)

        # Character name
        self._name_edit = QLineEdit(self.char.get("name",""))
        self._name_edit.setStyleSheet(f"QLineEdit{{font-size:{FS_HEAD}px;font-weight:700;color:{GOLD2};border:none;background:transparent;padding:0;}}")
        self._name_edit.setMinimumWidth(180)
        self._name_edit.setMaximumWidth(320)
        self._name_edit.textChanged.connect(self._on_name_changed)
        # A rename that clashes with another saved character is refused
        self._accepted_name = self.char.get("name", "")
        self._name_edit.editingFinished.connect(self._check_name_unique)
        hl.addWidget(self._name_edit)

        # (Race/Subrace/Ancestry/Background edit buttons live in the Choices tab)

        # Subclass area (invisible placeholder — only used in the choices tab now via _refresh_subclass_area)
        self._subclass_area = QHBoxLayout(); self._subclass_area.setSpacing(0)
        self._subclass_combos = {}
        # (hidden — class controls live in Level Up tab)

        # Class summary chip — read-only, just shows e.g. "Fighter 5"
        # Class cards -- read-only, one per class so a multiclass slots each
        # one in beside the last: "Wizard 5" large, its subclass under it.
        # Filled by _refresh_class_cards().
        self._class_summary = QWidget()
        self._class_summary.setStyleSheet("background:transparent;")
        self._class_cards_lay = QHBoxLayout(self._class_summary)
        self._class_cards_lay.setContentsMargins(0, 0, 0, 0)
        self._class_cards_lay.setSpacing(8)
        hl.addWidget(self._class_summary, 0, Qt.AlignVCenter)

        hl.addStretch()

        # Manual refresh — fail-safe in case a future edit reintroduces a
        # stale-tab bug. Forces every tab to repaint from current char data.
        refresh_btn = QPushButton()
        _icons.set_button_icon(refresh_btn, "refresh", 17)
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
        self._insp_btn = QPushButton()
        _icons.set_button_icon(self._insp_btn, "inspiration", 19)
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

        # Save/Load/Export live only in the File menu; no duplicate icon
        # buttons here.

        root.addWidget(header)

        # ── Status bar (AC, HP, Prof, Speed always visible) ───────────────────
        stat_bar = QFrame(); stat_bar.setStyleSheet(f"QFrame{{background:{SURF2};border-bottom:1px solid {BORDER};}}")
        stat_bar.setFixedHeight(64)
        sl = QHBoxLayout(stat_bar); sl.setContentsMargins(20,0,20,0); sl.setSpacing(24)

        self._sb_ac   = self._make_stat_pill("AC", "—", GOLD2)
        self._sb_hp   = self._make_stat_pill("HP", "—", GREEN2)
        self._sb_init = self._make_stat_pill("Initiative", "—", TEAL2)
        # advantage / disadvantage die beside the initiative number
        _init_lay = self._sb_init.layout()
        _init_val = self._sb_init._val
        _idx = _init_lay.indexOf(_init_val)
        _init_lay.removeWidget(_init_val)
        _init_row = QWidget(); _init_row.setStyleSheet("background:transparent;border:none;")
        _irl = QHBoxLayout(_init_row); _irl.setContentsMargins(0, 0, 0, 0); _irl.setSpacing(4)
        self._sb_init_adv = QLabel(); self._sb_init_adv.setStyleSheet("background:transparent;border:none;")
        self._sb_init_adv.hide()
        _irl.addStretch(); _irl.addWidget(_init_val); _irl.addWidget(self._sb_init_adv); _irl.addStretch()
        _init_lay.insertWidget(_idx, _init_row)
        self._sb_prof = self._make_stat_pill("Prof Bonus", "—", IND2)
        self._sb_spd  = self._make_stat_pill("Speed", "—", TEXT)
        for pill in [self._sb_ac, self._sb_hp, self._sb_init, self._sb_prof, self._sb_spd]:
            sl.addWidget(pill)
        # XP pill — only shown when Settings → Advancement is set to
        # "Experience Points"; hidden (not removed) for milestone
        # characters so toggling the setting doesn't need a UI rebuild.
        # Clickable to jump straight to Level Up once eligible (see
        # _refresh_xp_tracker, which wires/unwires the click handler).
        self._sb_xp = self._make_xp_pill()
        sl.addWidget(self._sb_xp)
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
        sr_btn = QPushButton("Short Rest")
        lr_btn = QPushButton("Long Rest")
        _icons.set_button_icon(sr_btn, "short_rest", 16)
        _icons.set_button_icon(lr_btn, "long_rest", 16)
        for btn, fn, c in [(sr_btn, self._short_rest, TEAL),(lr_btn, self._long_rest, INDIGO)]:
            btn.setFixedHeight(40)
            btn.setStyleSheet(_btn("", c, variant="cta", radius=8, border_alpha=0x88,
                                    text_color=TEXT, hover_text="white",
                                    font_size=FS_SMALL, padding="6px 14px").styleSheet())
            btn.clicked.connect(fn); sl.addWidget(btn)

        root.addWidget(stat_bar)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        # QTabWidget paints its own custom background by default and
        # ignores a plain QSS "background" rule on it unless this
        # attribute is set -- true for compound/complex widgets
        # generally, unlike QWidget/QFrame/QLabel. Without it, the strip
        # to the right of the last tab (the tab bar row doesn't stretch
        # to the widget's full width) fell through to the OS's raw
        # default widget background regardless of theme.py's own
        # QTabWidget{background:...} rule.
        self._tabs.setAttribute(Qt.WA_StyledBackground, True)
        self._tabs.setTabPosition(QTabWidget.North)
        # The tabs always fit the window: they share its full width, and
        # when that's not enough the longer names shorten with "…" (hover
        # for the full name) instead of the row spilling off the right
        # behind scroll arrows.
        _bar = self._tabs.tabBar()
        _bar.setUsesScrollButtons(False)
        _bar.setElideMode(Qt.ElideRight)
        _bar.setExpanding(True)
        # "&&" is a literal ampersand -- a single "&" in tab text is a
        # keyboard-mnemonic marker and would vanish.
        # Each tab has a full name and a short one; _fit_tab_names() shows
        # the short ones only when the full ones don't fit the window.
        self._tab_names = []   # (full, short) per tab, in order
        _SHORT = {"Abilities && Saves": "Abilities", "Skills && Proficiencies": "Skills",
                  "Gear && Items": "Gear", "Traits && Notes": "Notes"}

        def _add_tab(page, label, icon):
            idx = self._tabs.addTab(page, label)
            self._tab_names.append((label, _SHORT.get(label, label)))
            self._tabs.setTabToolTip(idx, label.replace("&&", "&"))   # the full name, if it's shortened
            _icons.set_tab_icon(self._tabs, page, icon)
            return page
        _add_tab(self._build_tab_abilities(),    "Abilities && Saves",      "abilities")
        _add_tab(self._build_tab_skills(),       "Skills && Proficiencies", "skills")
        _add_tab(self._build_tab_combat(),       "Combat",                  "combat")
        _add_tab(self._build_tab_gear(),         "Gear && Items",           "gear")
        _add_tab(self._build_tab_spells(),       "Spells",                  "spells")
        if self._has_infuse_item_access():
            _add_tab(self._build_tab_infusions(), "Infusions",              "infusions")
        self._choices_tab_page = _add_tab(self._build_tab_choices(), "Choices", "choices")
        _add_tab(self._build_tab_features(),     "Features",                "features")
        _add_tab(self._build_tab_traits_notes(), "Traits && Notes",         "notes")
        root.addWidget(self._tabs, 1)
        self._install_choices_pulse()
        self._tabs.installEventFilter(self)   # re-fit the tab names on resize
        self._sheet_header.installEventFilter(self)   # ...and the class cards
        self._fit_tab_names()

    def _refresh_class_cards(self):
        """(Re)build the header's class cards: one per class, each in its
        class's colour (data/class_colors.py) as the card's border,
        left stripe and tint -- the text stays the normal text colour, so
        darker class colours stay readable. A multiclass slots each class
        in beside the last. They always fit the
        header -- trying, widest first:
          1. full cards: "Wizard 5" with its subclass underneath
          2. compact cards: just "Wizard 5"
          3. as many compact cards as fit, then a "+N more" card listing
             the rest on hover (a 13-class character is legal, if unwise)"""
        lay = self._class_cards_lay
        classes = self.char.get("classes", [])
        from dnd_app.data.class_colors import class_color, needs_outline
        avail = self._class_cards_room()

        def _card(title, sub, col, tip, compact):
            card = QFrame(); card.setObjectName("classCard")
            # a colour that would vanish into the header (Rogue's black on a
            # dark theme, Cleric's white on a light one) gets a neutral
            # outline, and a stronger tint so the card still reads as it
            faint = needs_outline(col, SURF)
            edge = qa(TEXT3, 0xaa) if faint else qa(col, 0xaa)
            card.setStyleSheet(
                f"QFrame#classCard{{background:{qa(col, 0x66 if faint else 0x26)};"
                f"border:1px solid {edge};border-left:4px solid {col};border-radius:8px;}}")
            card.setMinimumHeight(50)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10 if compact else 16, 4, 10 if compact else 16, 4); cl.setSpacing(0)
            cl.addWidget(_lbl(title, TEXT, FS_LABEL + 1, bold=True, align=Qt.AlignCenter, wrap=False))
            if sub:
                cl.addWidget(_lbl(sub, TEXT2, FS_SMALL, align=Qt.AlignCenter, wrap=False))
            card.setToolTip(tip)
            return card

        def _tip(c):
            sub = c.get("subclass", "")
            return (f"{c['class']} {c['level']}" + (f" — {sub}" if sub else "")
                    + "\nLevel up, level down or change subclass on the Choices tab")

        def _build(compact, limit=None):
            cards = []
            shown = classes if limit is None else classes[:limit]
            for i, c in enumerate(shown):
                cards.append(_card(f"{c['class']} {c['level']}",
                                   "" if compact else c.get("subclass", ""),
                                   class_color(c["class"]), _tip(c), compact))
            rest = classes[len(shown):]
            if rest:
                cards.append(_card(f"+{len(rest)} more", "", TEXT2,
                                   "\n".join(_tip(c).split("\n")[0] for c in rest), True))
            return cards

        def _width(cards):
            return sum(cd.sizeHint().width() for cd in cards) + lay.spacing() * max(0, len(cards) - 1)

        cards = _build(compact=False)
        if avail and _width(cards) > avail:
            cards = _build(compact=True)
            limit = len(classes)
            while avail and _width(cards) > avail and limit > 1:
                limit -= 1
                cards = _build(compact=True, limit=limit)

        while lay.count():
            w = lay.takeAt(0).widget()
            if w is not None:
                w.deleteLater()
        for cd in cards:
            lay.addWidget(cd)
        if hasattr(self, "_refresh_class_buttons"):
            self._refresh_class_buttons()   # level/class buttons follow the same change

    def _class_cards_room(self) -> int:
        """Width the header has for the class cards: its own width minus
        everything else in it (0 before the header has been laid out)."""
        hdr = getattr(self, "_sheet_header", None)
        if hdr is None or hdr.width() < 100:
            return 0
        hl = hdr.layout()
        m = hl.contentsMargins()
        room = hdr.width() - m.left() - m.right()
        for i in range(hl.count()):
            item = hl.itemAt(i)
            w = item.widget()
            if w is self._class_summary:
                continue
            if w is not None and not w.isHidden():
                room -= w.sizeHint().width() + hl.spacing()
        return max(0, room - 24)   # a little air either side

    def _fit_tab_names(self):
        """Full tab names when they all fit across the window, the short
        ones (Abilities, Skills, Gear, Notes) when they don't -- the tab bar
        never spills off the edge, and only shortens further (with "…")
        in a very narrow window."""
        tabs = getattr(self, "_tabs", None)
        if tabs is None or len(self._tab_names) != tabs.count():
            return
        bar = tabs.tabBar()
        for i, (full, _short) in enumerate(self._tab_names):
            if tabs.tabText(i) != full:
                tabs.setTabText(i, full)
        need = sum(bar.tabSizeHint(i).width() for i in range(bar.count()))
        if need > tabs.width():
            for i, (_full, short) in enumerate(self._tab_names):
                tabs.setTabText(i, short)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is getattr(self, "_tabs", None) and event.type() == QEvent.Resize:
            self._fit_tab_names()
        elif obj is getattr(self, "_sheet_header", None) and event.type() == QEvent.Resize:
            self._refresh_class_cards()
        return super().eventFilter(obj, event)

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
        return _pill(label, value, color)

    def _make_xp_pill(self):
        """Wider gold pill for the header: "XP" title, a "2,450 / 6,500"
        value line, and a slim progress bar underneath tracking distance
        to the next level. Built once in _build_ui; _refresh_xp_tracker
        fills it in and toggles visibility/eligibility styling."""
        f = QFrame(); f.setStyleSheet(f"QFrame{{background:{SURF};border:2px solid {qa(GOLD,0x55)};border-radius:10px;}}")
        f.setFixedHeight(52); f.setMinimumWidth(150)
        l = QVBoxLayout(f); l.setContentsMargins(10,4,10,4); l.setSpacing(2)
        top = QHBoxLayout(); top.setSpacing(6)
        val = _lbl("—", GOLD2, FS_BODY, bold=True, align=Qt.AlignCenter, wrap=False)
        top.addWidget(val, 1)
        l.addLayout(top)
        bar = QProgressBar(); bar.setRange(0,100); bar.setValue(0)
        bar.setTextVisible(False); bar.setFixedHeight(6)
        bar.setStyleSheet(
            f"QProgressBar{{background:{SURF2};border:none;border-radius:3px;}}"
            f"QProgressBar::chunk{{border-radius:3px;background:{GOLD};}}")
        l.addWidget(bar)
        ttl = _lbl("XP", TEXT3, FS_TINY, align=Qt.AlignCenter, wrap=False)
        l.addWidget(ttl)
        f._val = val; f._bar = bar; return f

    # ══ TAB 1: ABILITY SCORES & SAVES ══════════════════════════════════════════
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep death overlay covering the whole sheet
        for child in self.children():
            if isinstance(child, QFrame) and child.objectName() == "death_overlay":
                child.setGeometry(self.rect())
        # ...and the exhaustion frame (redrawn once the resize settles)
        if getattr(self, "_immersion", None) is not None:
            self._immersion.resized()

    def _on_name_changed(self, text: str):
        self.char["name"] = text.strip() or "Unnamed"
        self._update_title()
        self._mark_dirty()

    def _check_name_unique(self):
        from dnd_app.core.save_load import name_in_use, NAME_IN_USE_MESSAGE
        name = self._name_edit.text().strip()
        if name == getattr(self, "_accepted_name", None):
            return
        if name and name_in_use(name, exclude_path=self._save_path):
            QMessageBox.warning(self, "Name Already Used", NAME_IN_USE_MESSAGE)
            self._name_edit.setText(self._accepted_name)   # textChanged puts it back in char
            return
        self._accepted_name = name

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

    def _open_level_up_or_multiclass(self):
        """Unified Level Up / Multiclass panel — replaces the separate
        Level Up and Add Multiclass buttons. See LevelUpMulticlassDialog
        for the full behavior."""
        from dnd_app.data.classes import CLASS_DICT
        from dnd_app.core.character import add_class, level_up_block_reason
        why = level_up_block_reason(self.char)   # character level 20
        if why:
            QMessageBox.information(self, "Level Up", f"Can't gain a level — {why}.")
            return
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
            self._toast(f"Swapped {swap_old} for {swap_new}")

        if eldritch_versatility:
            kind = eldritch_versatility["kind"]
            old, new = eldritch_versatility["old"], eldritch_versatility["new"]
            if kind == "cantrip":
                known = self.char.setdefault("spells_known", [])
                if old in known: known.remove(old)
                if new not in known: known.append(new)
                self._toast(f"Eldritch Versatility: swapped cantrip {old} for {new}")
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
                # ...and out of the pick itself, so the chooser asks again
                held = self.char.setdefault("_choices", {}).get("eldritch_invocations")
                if isinstance(held, list):
                    self.char["_choices"]["eldritch_invocations"] = [i for i in held if i not in removed]
                if removed:
                    self._toast(f"Pact Boon changed to {new.split(' – ')[0] if ' – ' in new else new.split('(')[0].strip()} "
                                f"— {len(removed)} invocation(s) no longer eligible, re-choose them in the Choices tab")
                else:
                    self._toast(f"Pact Boon changed to {new.split('(')[0].strip()}")
            elif kind == "arcanum":
                spell_lvl, old_name = old
                self.char.setdefault("_choices", {})[f"mystic_arcanum_{spell_lvl}"] = [new]
                self._toast(f"Eldritch Versatility: swapped Mystic Arcanum {old_name} for {new}")

        mv_kind, mv_old, mv_new = dlg.get_martial_versatility()
        if mv_kind and mv_old and mv_new:
            from dnd_app.core.builder import swap_choice_pick
            if mv_kind == "style":
                styles = self.char.setdefault("fighting_styles", [])
                if mv_old in styles:
                    styles.remove(mv_old)
                styles.append(mv_new)
                swap_choice_pick(self.char, lambda k: "fighting_style" in k, mv_old, mv_new)
                self._toast(f"Martial Versatility: swapped {mv_old.split(' (')[0].strip()} "
                            f"for {mv_new.split(' (')[0].strip()}")
            elif mv_kind == "maneuver":
                maneuvers = self.char.setdefault("battle_master_maneuvers", [])
                if mv_old in maneuvers:
                    maneuvers.remove(mv_old)
                maneuvers.append(mv_new)
                swap_choice_pick(self.char, lambda k: "maneuvers" in k, mv_old, mv_new)
                self._toast(f"Martial Versatility: swapped maneuver {mv_old.split(' – ')[0].strip()} "
                            f"for {mv_new.split(' – ')[0].strip()}")

        cv_old, cv_new = dlg.get_cantrip_versatility()
        if cv_old and cv_new:
            known = self.char.setdefault("spells_known", [])
            if cv_old in known: known.remove(cv_old)
            if cv_new not in known: known.append(cv_new)
            self._toast(f"Cantrip Versatility: swapped {cv_old} for {cv_new}")

        bv_kind, bv_old, bv_new = dlg.get_bardic_versatility()
        if bv_kind and bv_old and bv_new:
            if bv_kind == "expertise":
                from dnd_app.core.builder import move_expertise
                move_expertise(self.char, bv_old, bv_new)     # in the pick, so it stays
                self._toast(f"Bardic Versatility: moved Expertise from {bv_old} to {bv_new}")
            elif bv_kind == "cantrip":
                known = self.char.setdefault("spells_known", [])
                if bv_old in known: known.remove(bv_old)
                if bv_new not in known: known.append(bv_new)
                self._toast(f"Bardic Versatility: swapped {bv_old} for {bv_new}")

        sv_kind, sv_old, sv_new = dlg.get_sorcerous_versatility()
        if sv_kind and sv_old and sv_new:
            if sv_kind == "metamagic":
                mm = self.char.setdefault("_choices", {}).setdefault("sorcerer_metamagic", [])
                if sv_old in mm: mm.remove(sv_old)
                mm.append(sv_new)
                self._toast(f"Sorcerous Versatility: swapped metamagic {sv_old.split(' – ')[0].strip()} "
                            f"for {sv_new.split(' – ')[0].strip()}")
            elif sv_kind == "cantrip":
                known = self.char.setdefault("spells_known", [])
                if sv_old in known: known.remove(sv_old)
                if sv_new not in known: known.append(sv_new)
                self._toast(f"Sorcerous Versatility: swapped {sv_old} for {sv_new}")

        self.char["_last_leveled_class"] = cls_name
        self.ctrl.refresh()
        self._mark_dirty()
        self._auto_save()

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
        had_sub = entry.get("subclass", "")
        self.ctrl.refresh()                         # rebuild + update_all + notify
        if entry.get("subclass") and not had_sub:   # set aside by a level down
            self._toast(f"{cls_name} {entry['level']}: {entry['subclass']} is back")
        # _on_char_updated() (subscribed above) already calls both
        # _populate_subclass_combo() and self._levelup_panel.refresh() —
        # calling them again here would run the entire pending-choices
        # rebuild twice in immediate succession, momentarily constructing
        # and tearing down duplicate chooser widgets.
        self._mark_dirty()
        self._auto_save()

    def _open_level_down(self):
        """Remove one level from an existing class."""
        from PySide6.QtWidgets import QInputDialog
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

        # Diff the full set of structurally-relevant choice IDs before and
        # after the level decrement, and clear any choice from the real
        # character that's no longer valid at the new, lower level.
        # Without this, delevelling silently kept every prior choice
        # (Fighting Style, ASI, subclass picks, etc.) locked in forever,
        # with no way to ever pick differently.
        old_ids = _all_relevant_choice_ids(self.char)
        entry["level"] -= 1
        # below its subclass level, a class can't keep a subclass
        from dnd_app.core.character import drop_subclasses_below_level
        dropped = drop_subclasses_below_level(self.char)
        new_ids = _all_relevant_choice_ids(self.char)
        _prune_stale_choices(self.char, old_ids - new_ids)

        self.ctrl.refresh()
        for cn, sub, need in dropped:
            self._toast(f"{sub} set aside until {cn} level {need}")
        # self.ctrl.refresh() already triggers _populate_subclass_combo()
        # and _levelup_panel.refresh() via the observer chain (see
        # _open_level_up for the full explanation) — no need to call
        # them again here.
        self._mark_dirty()
        self._auto_save()

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
        self._auto_save()

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
        # Same diff-and-prune as _open_level_down above, for the same
        # reason -- removing a class entirely is a bigger change than
        # levelling it down by one, so it needs this at least as much:
        # without it, a removed class's Fighting Style/ASI/subclass picks
        # stayed stuck in char["_choices"] forever, and re-adding the
        # same class later saw them as "already chosen" instead of
        # prompting fresh.
        old_ids = _all_relevant_choice_ids(self.char)
        removed = next(c for c in classes if c["class"] == cls_name)
        self.char["classes"] = [c for c in classes if c["class"] != cls_name]
        # Its spells go with it -- only the ones no remaining class could
        # have (core/character.py). Before the prune, which would hide its
        # Magical Secrets picks.
        from dnd_app.core.character import drop_spells_of_removed_class, name_list
        lost = drop_spells_of_removed_class(self.char, removed)
        self.char.get("_choices", {}).pop(f"{cls_name}_subclass", None)   # re-adding asks again
        new_ids = _all_relevant_choice_ids(self.char)
        _prune_stale_choices(self.char, old_ids - new_ids)
        self.ctrl.refresh()
        # See _open_level_up — self.ctrl.refresh() already triggers both
        # calls via the observer chain. My Spells only rebuilds on load,
        # so it's redone here when spells left.
        if lost:
            self._populate_my_spells_from_char()
            self._toast(f"{cls_name} removed, along with its spells: {name_list(lost)}")
        else:
            self._toast(f"{cls_name} removed")
        self._mark_dirty()
        self._auto_save()

    def _toast(self, text: str, duration_ms: int = None):
        """Show a transient notification banner at the top of the sheet.
        Pass duration_ms=0 for a persistent toast that stays up until the
        caller explicitly hides self._toast_lbl (used for the death
        screen's quip, which should last until the character is revived
        rather than fade out from under a modal overlay)."""
        # Opt-in trace, off by default -- see dnd_app/ui_desktop/diagnostics.py.
        from dnd_app.ui_desktop.diagnostics import log_toast
        log_toast(text)
        if not hasattr(self, "_toast_lbl"):
            self._toast_lbl = QLabel(self)
            self._toast_lbl.setAlignment(Qt.AlignCenter)
            self._toast_lbl.setWordWrap(False)
            self._toast_lbl.hide()
            self._toast_timer = QTimer(self)
            self._toast_timer.setSingleShot(True)
            self._toast_timer.timeout.connect(self._toast_lbl.hide)
        self._toast_lbl.setText(text)
        self._toast_lbl.setStyleSheet(
            f"QLabel{{background:{SURF2};color:{TEXT};border:1px solid {GOLD};"
            f"border-radius:10px;padding:10px 18px;font-size:{FS_BODY}px;font-weight:700;}}")
        # long ones wrap inside the window instead of running off its edges
        self._toast_lbl.setWordWrap(True)
        self._toast_lbl.setMaximumWidth(max(260, min(self.width() - 48, 760)))
        self._toast_lbl.adjustSize()
        x = (self.width() - self._toast_lbl.width()) // 2
        y = 28
        self._toast_lbl.move(max(8, x), max(8, y))
        self._toast_lbl.raise_()
        self._toast_lbl.show()
        self._toast_timer.stop()
        if duration_ms is None:
            # long enough to read: longer messages stay up longer
            duration_ms = min(9000, max(3200, 55 * len(text)))
        if duration_ms > 0:
            self._toast_timer.start(duration_ms)

    # ── Hit dice: spend one to heal (short-rest style) ────────────────────────
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
        self._refresh_class_cards()

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
        for key, ed in self._notes_field_edits.items():
            ed.blockSignals(True)
            ed.setPlainText(char.get(key,""))
            ed.blockSignals(False)

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
        # QLabel auto-detects HTML in setText() -- rich text so "Adv"/
        # "Disadv" can be colored independently of the plain-text
        # initiative number sharing the same label. net already handles
        # the RAW cancellation (advantage + disadvantage from different
        # sources -> neither applies), so only one badge (or none) shows.
        self._sb_init._val.setText(sign(ini))
        if init_adv["net"] in ("advantage", "disadvantage"):
            adv = init_adv["net"] == "advantage"
            self._sb_init_adv.setPixmap(_icons.pixmap("adv" if adv else "disadv", _icons.scaled(18),
                                                      "GREEN2" if adv else "CRIM2"))
            self._sb_init_adv.show()
        else:
            self._sb_init_adv.hide()
        if init_adv["net"] == "advantage":
            notes = "\n".join(f"• {s['source']}: {s['note']}" for s in init_adv["sources"])
            self._sb_init.setToolTip(f"Click to roll initiative (d20 + {sign(ini)})\n\nAdvantage:\n{notes}")
        elif init_adv["net"] == "disadvantage":
            notes = "\n".join(f"• {s}" for s in init_adv["disadvantage_sources"])
            self._sb_init.setToolTip(f"Click to roll initiative (d20 + {sign(ini)})\n\nDisadvantage:\n{notes}")
        elif init_adv["has_advantage"] and init_adv["has_disadvantage"]:
            self._sb_init.setToolTip(
                f"Click to roll initiative (d20 + {sign(ini)})\n\n"
                "Advantage and disadvantage sources both present — they cancel out.")
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
        self._refresh_identity_buttons()
        self._sb_prof._val.setText(sign(pb))
        _spd_parts = [f"{spd} ft"]
        if fly:  _spd_parts.append(f"fly {fly}")
        if swim: _spd_parts.append(f"swim {swim}")
        if clmb: _spd_parts.append(f"climb {clmb}")
        self._sb_spd._val.setText(" / ".join(_spd_parts))
        self._refresh_class_cards()
        self._refresh_xp_tracker()

