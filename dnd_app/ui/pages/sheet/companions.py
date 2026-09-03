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


class CompanionsMixin:
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
        from dnd_app.data.phbCommon.items import MOUNTS
        from dnd_app.data.phbCommon.statblocks import get_mount_statblock

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
        # animal.
        from dnd_app.data.phbCommon.statblocks import FIND_GREATER_STEED_OPTIONS
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
            remove_btn = _btn("\u2715 Remove", CRIMSON, variant="danger", radius=5,
                               border_width=1, text_color=CRIM2, hover_text="white",
                               font_size=FS_SMALL, padding="4px 10px")
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
        from dnd_app.data.phbCommon.items import (VEHICLES, VEHICLES_WATER, VEHICLES_AIR, VEHICLES_LAND,
                                         VEHICLES_BGDIA, VEHICLES_MAGIC, ADVENTURING_GEAR)
        from dnd_app.data.phbCommon.statblocks import get_vehicle_statblock

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
                remove_btn = _btn("\u2715 Remove", CRIMSON, variant="danger", radius=5,
                                   border_width=1, text_color=CRIM2, hover_text="white",
                                   font_size=FS_SMALL, padding="4px 10px")
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
                rm2 = _btn("\u2715 Remove", CRIMSON, variant="danger", radius=5,
                            border_width=1, text_color=CRIM2, hover_text="white",
                            font_size=FS_SMALL, padding="4px 10px")
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
        button (Drake Companion, Dancing Item, Wildfire Spirit). Spends
        the linked resource charge (or a Wild Shape use, for Wildfire
        Spirit, which shares that pool rather than having its own
        dedicated resource), marks the companion active so its stat
        block card appears, and resets its tracked HP to full —
        matching a fresh summon rather than picking up mid-fight with
        whatever HP was left from a previous card render."""
        from dnd_app.data.phbCommon.statblocks import COMPANION_STATBLOCKS
        tmpl = COMPANION_STATBLOCKS.get(key)
        if not tmpl:
            return
        from dnd_app.core.calculator import companion_max_simultaneous, count_active_companion_instances
        active_now = self.char.get("active_summoned_companions", [])
        if count_active_companion_instances(key, active_now) >= companion_max_simultaneous(key, self.char):
            # Defensive cap check — the Summon button is only shown while
            # under the cap (get_summonable_but_inactive_companions), but
            # guard here too rather than trusting the UI alone, matching
            # the resource-charge check just below.
            self._toast(f"Already at the maximum number of active {tmpl['display_name']}s.")
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
        from dnd_app.core.calculator import resolve_companion_statblock, companion_max_simultaneous
        active = self.char.setdefault("active_summoned_companions", [])
        if companion_max_simultaneous(key, self.char) > 1:
            # Multi-instance-capable (Dancing Item + Creative Crescendo):
            # find the lowest unused instance index rather than always
            # appending a new one, so a dismissed slot gets reused
            # instead of instance numbers climbing indefinitely.
            used = {int(a.split("#", 1)[1]) for a in active if a.startswith(key + "#")}
            idx = 0
            while idx in used:
                idx += 1
            instance_key = f"{key}#{idx}"
            active.append(instance_key)
        else:
            instance_key = key
            if key not in active:
                active.append(key)
        sb = resolve_companion_statblock(instance_key, self.char)
        self.char.setdefault("summon_hp_tracking", {})[f"companion_{instance_key}"] = sb.get("hp", 1)
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
        the Tasha's/Fizban's/Book of Many Things summon-a-spirit spells.
        Each entry stores (spell, cast level, form) so the stat block
        can be recomputed correctly if you look at it again (e.g. after
        leveling up your spell save DC)."""
        from dnd_app.data.phbCommon.statblocks import SCALING_SUMMONS, resolve_scaling_summon

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
            remove_btn = _btn("✕ Remove", CRIMSON, variant="danger", radius=5,
                               border_width=1, text_color=CRIM2, hover_text="white",
                               font_size=FS_SMALL, padding="4px 10px")
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
                from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
                return WILDSHAPE_BEASTS[n]["cr"]
            for name in sorted(beast_names, key=_sort_key):
                from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
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
        from dnd_app.data.phbCommon.statblocks import COMPANION_STATBLOCKS
        from dnd_app.core.calculator import companion_max_simultaneous, count_active_companion_instances
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
            # Multi-instance-capable companion with at least one already
            # active (Dancing Item + Creative Crescendo) — the prompt
            # still applies (there's room for another simultaneous
            # instance), but "Not currently summoned" would be wrong.
            active_n = count_active_companion_instances(key, self.char.get("active_summoned_companions", []))
            cap = companion_max_simultaneous(key, self.char)
            if active_n > 0:
                status_txt = f"{active_n}/{cap} active.{uses_txt}"
            else:
                status_txt = f"Not currently summoned.{uses_txt}"
            scl2.addWidget(_lbl(status_txt, TEXT3, FS_SMALL))
            btn_label = f"Summon another {tmpl.get('display_name', key)}" if active_n > 0 \
                else f"Summon {tmpl.get('display_name', key)}"
            summon_btn = QPushButton(btn_label)
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

        from dnd_app.data.phbCommon.statblocks import WILDSHAPE_BEASTS
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
                    from dnd_app.data.phbCommon.statblocks import COMPANION_STATBLOCKS
                    # companion_key may be an instance-suffixed "key#N" id
                    # (Dancing Item + Creative Crescendo) — look the
                    # template up by its base key, same as
                    # resolve_companion_statblock() does.
                    tmpl = COMPANION_STATBLOCKS.get(companion_key.split("#", 1)[0], {})
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
