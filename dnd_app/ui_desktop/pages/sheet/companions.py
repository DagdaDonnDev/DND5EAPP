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
from .base import *
from .base import _lbl, _sep, _card
from dnd_app.ui_desktop import icons as _icons
from dnd_app.ui_desktop.popups import Ask, Tell


class CreatureGroup(QFrame):
    """One group on the Creatures page: a header to open or close it (▾/▸,
    its name and how many), and the cards under it."""

    def __init__(self, name, open_, on_toggle, parent=None):
        super().__init__(parent)
        self.setObjectName("creatureGroup")
        self.setStyleSheet("QFrame#creatureGroup{background:transparent;border:none;}")
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 4); lay.setSpacing(6)
        self._name, self._open, self._on_toggle = name, open_, on_toggle
        self.header = QPushButton(); self.header.setObjectName(f"creatureGroupHeader_{name}")
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setStyleSheet(
            f"QPushButton{{text-align:left;background:{SURF2};border:1px solid {BORDER};border-radius:8px;"
            f"padding:7px 12px;color:{GOLD2};font-size:{FS_BODY}px;font-weight:700;min-height:0px;}}"
            f"QPushButton:hover{{border-color:{BORDER2};}}")
        self.header.clicked.connect(self._toggle)
        lay.addWidget(self.header)
        self._holder = QWidget(); self._holder.setStyleSheet("background:transparent;")
        self.body = QVBoxLayout(self._holder); self.body.setContentsMargins(6, 0, 0, 0); self.body.setSpacing(8)
        lay.addWidget(self._holder)
        self._count = 0
        self._show()

    def set_count(self, n):
        self._count = n
        self._show()

    def _show(self):
        self.header.setText(f"{'▾' if self._open else '▸'}  {self._name}" + (f"   ({self._count})" if self._count else ""))
        self._holder.setVisible(self._open)

    def _toggle(self):
        self._open = not self._open
        self._show()
        self._on_toggle(self._name, self._open)


class CompanionsMixin:
    def _build_companions_tab(self):
        """Shows live stat blocks (real numbers, not formulas) for
        whichever companion/summon features the character currently
        qualifies for — Steel Defender, Wildfire Spirit, Drake Companion,
        Dancing Item, Eldritch Cannon, or the Beast Master's three Primal
        Companion options. Rebuilt on every refresh since most of these
        scale with class level."""
        tab = QWidget()
        outer = QVBoxLayout(tab); outer.setContentsMargins(16,16,16,16)
        # yours on the left, the Bestiary to add from on the right -- the
        # way Spells and Inventory have their browsers
        splitter = QSplitter(Qt.Horizontal); splitter.setChildrenCollapsible(False)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget(); inner.setObjectName("creaturesDrop"); inner.setStyleSheet(f"QWidget#creaturesDrop{{background:{BG};}}")
        self._companions_lay = QVBoxLayout(inner); self._companions_lay.setSpacing(10)
        # a creature dragged over from the Bestiary: onto a group, into it
        # (see _fill_companions_tab); anywhere else, the group is asked
        from dnd_app.ui_desktop.widgets import accept_drop
        accept_drop(inner, "creature", self._drop_creature)
        accept_drop(inner, "mount-vehicle", self._drop_mount_vehicle)
        scroll.setWidget(inner)
        splitter.addWidget(scroll)
        from dnd_app.ui_desktop.dialogs.bestiary import CreatureBrowser
        side = QTabWidget()
        side.setAttribute(Qt.WA_StyledBackground, True)
        side.setStyleSheet(
            f"QTabWidget::pane{{background:{SURF};border:1px solid {BORDER};border-top-left-radius:0px;"
            f"border-top-right-radius:8px;border-bottom-right-radius:8px;border-bottom-left-radius:8px;top:-1px;}}"
            f"QTabBar::tab{{background:{SURF2};color:{TEXT2};padding:8px 8px;font-size:{FS_SMALL}px;"
            f"border:1px solid {BORDER};border-top-left-radius:6px;border-top-right-radius:6px;"
            f"border-bottom-right-radius:0px;border-bottom-left-radius:0px;margin-right:1px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD2};font-weight:700;border-bottom-color:{SURF};}}")
        from dnd_app.core.summons import GROUPS
        self._creature_browser = CreatureBrowser(self._add_creature_from_browser, "Add",
                                                 groups=GROUPS, group="Other")
        side.addTab(self._creature_browser, "Bestiary")
        from dnd_app.ui_desktop import icons as _icons
        _icons.set_tab_icon(side, self._creature_browser, "paw", 15)
        # the mounts you can buy and every vehicle: into Mounts and Vehicles
        from dnd_app.ui_desktop.dialogs.bestiary import MountVehicleBrowser
        self._mount_vehicle_browser = MountVehicleBrowser(self._add_mount_or_vehicle)
        side.addTab(self._mount_vehicle_browser, "Mounts && Vehicles")
        _icons.set_tab_icon(side, self._mount_vehicle_browser, "wagon", 15)
        splitter.addWidget(side)
        # your creatures and the Bestiary half and half (still draggable)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 1)
        splitter.setSizes([600, 600])
        outer.addWidget(splitter)
        self._refresh_companions_tab()
        return tab

    def _add_mount_or_vehicle(self, name: str, kind: str):
        if kind == "mount":
            self._add_mount(name)
        else:
            self._add_vehicle(name)
        self._toast(f"{name} added to your creatures ({'Mounts' if kind == 'mount' else 'Vehicles'})")

    def _drop_creature(self, name: str):
        """A creature dropped on the page but not on a group: which group?"""
        from dnd_app.core.summons import GROUPS
        from dnd_app.ui_desktop.dialogs.bestiary import pick_group
        g = pick_group(self, name, GROUPS)
        if g:
            self._add_creature_from_browser(name, g)

    def _drop_mount_vehicle(self, text: str):
        name, _, kind = text.partition("|")
        if name and kind in ("mount", "vehicle"):
            self._add_mount_or_vehicle(name, kind)

    def _add_creature_from_browser(self, name: str, group: str = "Other"):
        """Add Selected to Creatures: a Bestiary creature on your page with
        its own hit points, in the group picked beside the button -- a pet,
        a hireling, a mount, one your DM gave."""
        from dnd_app.core.summons import add_summons
        real = add_summons(self.char, name, 1, "From the Bestiary", group=group)
        self._mark_dirty()
        self._refresh_companions_tab()
        self._toast(f"{real} added to your creatures ({group})")

    def _build_mounts_section(self):
        """The mounts you've bought (Inventory's Mounts & Vehicles): a real
        stat block each -- a Warhorse's AC, HP and attacks matter in play,
        not just a weight and a price."""
        from dnd_app.data.statblocks import get_mount_statblock

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
            card = self._build_statblock_card(
                sb, hp_key=f"mount_{mount_name}",
                context_menu=lambda m, idx=i: self._remove_action(m, lambda: self._remove_mount(idx)))
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
                card = self._build_statblock_card(
                    sb, hp_key=card_hp_key,
                    context_menu=lambda m, idx=i: self._remove_action(m, lambda: self._remove_vehicle(idx)))
                self._companions_lay.addWidget(card)
            else:
                # Land vehicle: no official combat stats — simple info row
                # pulled from the general gear catalog (cost/weight/desc).
                g = gear_lookup.get(vname)
                desc = g[3] if g else ""
                row = QFrame(); row.setObjectName("creatureCard")
                row.setStyleSheet(f"QFrame#creatureCard{{background:{SURF};border:1px solid {BORDER};"
                                  f"border-left:3px solid {GOLD};border-radius:9px;}}"
                                  f"QFrame#creatureCard QLabel{{background:transparent;border:none;}}")
                rl = QHBoxLayout(row); rl.setContentsMargins(12,8,12,8); rl.setSpacing(10)
                rl.addWidget(_icons.icon_label("wagon", 20))
                name_col = QVBoxLayout(); name_col.setSpacing(0)
                name_col.addWidget(_lbl(vname, TEXT, FS_BODY, bold=True, wrap=False))
                name_col.addWidget(_lbl(desc, TEXT3, FS_TINY))
                rl.addLayout(name_col, 1)
                row.setContextMenuPolicy(Qt.CustomContextMenu)
                row.setToolTip("Right-click to remove")

                def _row_menu(pos, r=row, idx=i):
                    from PySide6.QtWidgets import QMenu
                    m = QMenu(self)
                    self._remove_action(m, lambda: self._remove_vehicle(idx))
                    m.exec(r.mapToGlobal(pos))
                row.customContextMenuRequested.connect(_row_menu)
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
        from dnd_app.data.statblocks import COMPANION_STATBLOCKS
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
        self._toast(f"{tmpl['display_name']} summoned!")

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

    def _build_owned_creature_cards(self, group: str):
        """The creatures you've summoned or added in `group` (core/summons.py
        group_of): each a stat block card with its hit points; right-click
        to move it to another group, or remove it."""
        from dnd_app.core.summons import summon_statblock, group_of, GROUPS
        for i, entry in enumerate(self.char.get("owned_summons", [])):
            if group_of(entry) != group:
                continue
            sb = summon_statblock(entry, self.char)      # a Bestiary creature, or a Tasha's spirit
            if not sb:
                continue
            card = self._build_statblock_card(sb, hp_key=f"summon_{i}",
                                              context_menu=lambda m, idx=i, g=group: self._creature_menu(m, idx, g))
            self._companions_lay.addWidget(card)

    def _max_hp_actions(self, menu, sb: dict, hp_key: str):
        """Set max HP… (its hit dice and their average to go by) and, once
        set, Back to its own max -- on every creature card with hit points."""
        from dnd_app.core.summons import max_hp_of, set_max_hp, dice_average
        base = sb["hp"]
        own = (self.char.get("summon_hp_max") or {}).get(hp_key)

        def _set():
            cur = max_hp_of(self.char, hp_key, base)
            dice = sb.get("hit_dice") or ""
            hint = (f"Its hit dice: {dice} (average {dice_average(dice)}). Roll them, or set any number."
                    if dice else "Set any number.")
            v, ok = Ask.getInt(self, f"{sb['display_name']}: max HP", hint, cur, 1, 9999, 1)
            if ok:
                set_max_hp(self.char, hp_key, v)
                self._mark_dirty()
                self._refresh_companions_tab()
        act = menu.addAction("Set max HP…")
        act.triggered.connect(lambda checked=False: _set())
        if own:
            back = menu.addAction(f"Back to its own max ({base})")
            back.triggered.connect(lambda checked=False: (set_max_hp(self.char, hp_key, None), self._mark_dirty(),
                                                          self._refresh_companions_tab()))

    def _creature_menu(self, menu, index: int, current: str):
        """A summoned or added creature's right-click: Move to (another
        group), and Remove."""
        from dnd_app.core.summons import GROUPS
        sub = menu.addMenu(_icons.icon("paw"), "Move to")
        for g in GROUPS:
            act = sub.addAction(("✓ " if g == current else "   ") + g)
            act.setEnabled(g != current)
            act.triggered.connect(lambda checked=False, gg=g: self._move_creature(index, gg))
        self._remove_action(menu, lambda: self._remove_summoned_creature(index))

    def _remove_action(self, menu, do):
        menu.addSeparator()
        act = menu.addAction(_icons.icon("trash"), "Remove")
        act.triggered.connect(lambda checked=False: do())

    def _move_creature(self, index: int, group: str):
        from dnd_app.core.summons import set_group
        if set_group(self.char, index, group):
            self._mark_dirty()
            QTimer.singleShot(0, self, self._refresh_companions_tab)   # (not while its own box is still busy)

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
        self._fill_companions_tab()
        # the pickers narrow with the page (the Bestiary beside it), rather
        # than pushing the cards off its right edge
        host = self._companions_lay.parentWidget()
        if host is not None:
            for box in host.findChildren(QComboBox):
                box.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
                # (a group's box: "Companions" in full)
                box.setMinimumContentsLength(6)

    def _fill_companions_tab(self):
        """The Creatures page, in groups you can open and close: Mounts
        (bought, and a Find Steed's), Companions (a class's, and any you
        move there), Familiars, Summons, Wild Shape, Vehicles (only once
        you have one) and Other (added from the Bestiary). A group with
        nothing in it isn't shown."""
        while self._companions_lay.count():
            item = self._companions_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        page = self._companions_lay
        closed = set(self.char.get("_closed_creature_groups", []))
        made = []

        from dnd_app.core.summons import GROUPS
        from dnd_app.ui_desktop.widgets import accept_drop

        def group(name, build):
            box = CreatureGroup(name, name not in closed, self._toggle_creature_group)
            box.setObjectName(f"creatureGroup_{name.replace(' ', '')}")
            box.setStyleSheet(f"QFrame#{box.objectName()}{{background:transparent;border:none;}}")
            if name in GROUPS:
                accept_drop(box, "creature", lambda n, g=name: self._add_creature_from_browser(n, g), TEAL)
            else:
                accept_drop(box, "creature", self._drop_creature)
            accept_drop(box, "mount-vehicle", self._drop_mount_vehicle)
            self._companions_lay = box.body
            try:
                build()
            finally:
                self._companions_lay = page
            if box.body.count():
                box.set_count(box.body.count())
                page.addWidget(box)
                made.append(name)
            else:
                box.deleteLater()

        group("Mounts", lambda: (self._build_mounts_section(), self._build_owned_creature_cards("Mounts")))
        group("Companions", lambda: (self._build_class_companions(), self._build_owned_creature_cards("Companions")))
        group("Familiars", lambda: self._build_owned_creature_cards("Familiars"))
        group("Summons", lambda: self._build_owned_creature_cards("Summons"))
        group("Wild Shape", self._build_wildshape_section)
        group("Vehicles", self._build_vehicles_section)
        group("Other", lambda: self._build_owned_creature_cards("Other"))
        if not made:
            page.addWidget(_lbl("No creatures yet. Add one from the Bestiary, buy a mount or vehicle in "
                                "your Inventory, or cast a spell that summons one.", TEXT3, FS_SMALL))
        page.addStretch()

    def _toggle_creature_group(self, name: str, open_: bool):
        closed = [g for g in self.char.get("_closed_creature_groups", []) if g != name]
        if not open_:
            closed.append(name)
        self.char["_closed_creature_groups"] = closed

    def _build_wildshape_section(self):
        from dnd_app.core.calculator import get_available_wildshape_beasts, get_wild_shape_info
        beast_names = get_available_wildshape_beasts(self.char)
        if beast_names:
            info = get_wild_shape_info(self.char)
            wc = _card(qa(GREEN, 0x55))
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


    def _build_class_companions(self):
        from dnd_app.core.calculator import (get_available_companions, resolve_companion_statblock,
                                             get_summonable_but_inactive_companions)
        keys = get_available_companions(self.char)
        summonable = get_summonable_but_inactive_companions(self.char)
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
        from dnd_app.core.calculator import companion_max_simultaneous, count_active_companion_instances
        for key in summonable:
            tmpl = COMPANION_STATBLOCKS.get(key, {})
            sc = _card(qa(TEAL, 0x33))
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
                               companion_key: str = None, context_menu=None) -> QFrame:
        """A creature's card: one slim line when closed -- a coloured stripe,
        its name with its size, type and where it's from, and AC, HP and
        speed as chips -- and the whole stat block when opened (click the
        line): the six abilities as small boxes, the rest a line each, and
        its traits, actions and reactions under headings.

        hp_key: HP is a box you can change, kept per creature in
        char['summon_hp_tracking'][hp_key] (a stable key per creature:
        f"summon_{i}", f"mount_{name}", f"companion_{key}"); None for a
        preview card (the Wild Shape form's).
        context_menu(menu): fills its right-click menu (Move to group,
        Remove...)."""
        card = QFrame(); card.setObjectName("creatureCard")
        card.setStyleSheet(
            f"QFrame#creatureCard{{background:{SURF};border:1px solid {BORDER};border-left:3px solid {TEAL};"
            f"border-radius:9px;}}"
            f"QFrame#creatureCard:hover{{border-color:{BORDER2};border-left-color:{TEAL2};}}"
            f"QFrame#creatureCard QLabel{{background:transparent;border:none;}}")
        cl = QVBoxLayout(card); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(0)
        if context_menu is not None or hp_key:
            card.setContextMenuPolicy(Qt.CustomContextMenu)

            def _menu(pos, c=card):
                from PySide6.QtWidgets import QMenu
                m = QMenu(self)
                if hp_key:
                    self._max_hp_actions(m, sb, hp_key)
                if context_menu is not None:
                    context_menu(m)
                if not m.isEmpty():
                    m.exec(c.mapToGlobal(pos))
            card.customContextMenuRequested.connect(_menu)
            card.setToolTip("Click to open or close · right-click for more")

        tracking = self.char.setdefault("summon_hp_tracking", {}) if hp_key else {}
        # a stat block's hp can be a placeholder ('—', a vehicle with none):
        # the box then runs to 1, never a broken range
        from dnd_app.core.summons import max_hp_of
        raw_hp = sb["hp"]
        max_hp = max_hp_of(self.char, hp_key, raw_hp) if hp_key else \
            (raw_hp if isinstance(raw_hp, int) else (int(raw_hp) if str(raw_hp).isdigit() else 1))
        cur_hp = min(tracking.get(hp_key, max_hp), max_hp) if hp_key else max_hp

        def chip(text, color):
            c = _lbl(text, color, FS_SMALL, bold=True, wrap=False)
            c.setStyleSheet(f"QLabel{{color:{color};font-size:{FS_SMALL}px;font-weight:700;"
                            f"background:{qa(color, 0x1c)};border:1px solid {qa(color, 0x66)};"
                            f"border-radius:6px;padding:3px 8px;}}")
            return c

        header = QFrame(); header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame{background:transparent;border:none;}")
        hl = QHBoxLayout(header); hl.setContentsMargins(12, 8, 12, 8); hl.setSpacing(10)
        chevron = _lbl("▾" if start_expanded else "▸", TEAL2, FS_BODY, bold=True, wrap=False)
        chevron.setFixedWidth(12)
        hl.addWidget(chevron)
        name_col = QVBoxLayout(); name_col.setSpacing(0)
        name_col.addWidget(_lbl(sb["display_name"], TEXT, FS_BODY, bold=True, wrap=False))
        kind = " ".join(x for x in (sb.get("size", ""), sb.get("creature_type", "")) if x)
        sub = " · ".join(x for x in (kind, sb.get("source", "")) if x)
        name_col.addWidget(_lbl(sub, TEXT3, FS_TINY, wrap=False))
        hl.addLayout(name_col, 1)
        hl.addWidget(chip(f"AC {sb['ac']}", GOLD2))
        hp_spin_header = None
        if hp_key:
            hp_box = QFrame(); hp_box.setObjectName("hpChip")
            hp_box.setStyleSheet(f"QFrame#hpChip{{background:{qa(GREEN2, 0x1c)};border:1px solid {qa(GREEN2, 0x66)};"
                                 f"border-radius:6px;}}")
            hb = QHBoxLayout(hp_box); hb.setContentsMargins(8, 2, 8, 2); hb.setSpacing(2)
            hb.addWidget(_lbl("HP", GREEN2, FS_SMALL, bold=True, wrap=False))
            hb.addSpacing(4)
            # the chip's own − and +, flat, with the number between them
            # (still typed into): the stock arrows were grey blocks in it
            # the value lives in a spin box (its range and the saving hang
            # off it), shown as a plain number field: the theme's spin box
            # padding hid the number in a box this narrow
            hp_spin_header = QSpinBox(hp_box)
            hp_spin_header.setRange(0, max_hp); hp_spin_header.setValue(cur_hp)
            hp_spin_header.setAccessibleName(f"{sb['display_name']} current HP")
            hp_spin_header.hide()
            hp_edit = QLineEdit(str(cur_hp)); hp_edit.setObjectName("hpField")
            hp_edit.setAlignment(Qt.AlignCenter); hp_edit.setFixedWidth(38)
            from PySide6.QtGui import QIntValidator
            hp_edit.setValidator(QIntValidator(0, max_hp, hp_edit))
            hp_edit.setAccessibleName(f"{sb['display_name']} current HP, typed")
            hp_edit.setToolTip("Current HP for this creature — edits are saved.")
            hp_edit.setStyleSheet(
                f"QLineEdit{{background:transparent;border:none;color:{TEXT};font-size:{FS_BODY}px;"
                f"font-weight:700;padding:0px;min-height:0px;}}"
                f"QLineEdit:focus{{background:{qa(GREEN2, 0x22)};border-radius:4px;}}")
            hp_edit.editingFinished.connect(
                lambda: hp_spin_header.setValue(int(hp_edit.text() or 0)))
            hp_spin_header.valueChanged.connect(lambda v: hp_edit.setText(str(v)))
            def _step_btn(text, step, tip):
                b = QToolButton(); b.setText(text); b.setAutoRaise(True)
                b.setCursor(Qt.PointingHandCursor); b.setToolTip(tip); b.setAccessibleName(tip)
                b.setFixedSize(22, 22)
                b.setStyleSheet(
                    f"QToolButton{{color:{GREEN2};font-size:{FS_BODY}px;font-weight:700;background:transparent;"
                    f"border:none;border-radius:5px;padding:0px;}}"
                    f"QToolButton:hover{{background:{qa(GREEN2, 0x33)};}}")
                b.clicked.connect(lambda: hp_spin_header.stepBy(step))
                return b
            hb.addWidget(_step_btn("−", -1, "1 less HP"))
            hb.addWidget(hp_edit)
            hb.addWidget(_step_btn("+", 1, "1 more HP"))
            hb.addWidget(_lbl(f"/ {max_hp}", TEXT3, FS_SMALL, wrap=False))
            hl.addWidget(hp_box)
        else:
            hl.addWidget(chip(f"HP {sb['hp']}", GREEN2))
        speed = str(sb.get("speed", "") or "")
        if speed:
            sp = _lbl(speed, TEAL2, FS_SMALL, bold=True, wrap=False)
            sp.setMaximumWidth(150)
            sp.setToolTip(f"Speed {speed}")
            hl.addWidget(sp)
        cl.addWidget(header)

        details = QFrame(); details.setObjectName("creatureDetails")
        details.setStyleSheet(f"QFrame#creatureDetails{{background:transparent;border:none;border-top:1px solid {BORDER};}}")
        details.setVisible(start_expanded)
        dl = QVBoxLayout(details); dl.setContentsMargins(16, 10, 14, 12); dl.setSpacing(8)

        # the six abilities: a small box each
        ab_row = QHBoxLayout(); ab_row.setSpacing(6)
        for ab, score in (sb.get("abilities") or {}).items():
            try:
                score = int(score)
            except (TypeError, ValueError):
                continue
            mod = (score - 10) // 2
            box = QFrame(); box.setObjectName("abBox")
            box.setStyleSheet(f"QFrame#abBox{{background:{SURF2};border:1px solid {BORDER};border-radius:7px;}}")
            bl = QVBoxLayout(box); bl.setContentsMargins(4, 4, 4, 4); bl.setSpacing(0)
            bl.addWidget(_lbl(ab, TEXT3, FS_TINY, bold=True, align=Qt.AlignCenter, wrap=False))
            bl.addWidget(_lbl(str(score), TEXT, FS_BODY, bold=True, align=Qt.AlignCenter, wrap=False))
            bl.addWidget(_lbl(sign(mod), TEAL2 if mod > 0 else (CRIM2 if mod < 0 else TEXT2), FS_TINY,
                              bold=True, align=Qt.AlignCenter, wrap=False))
            ab_row.addWidget(box, 1)
        if ab_row.count():
            dl.addLayout(ab_row)

        # the rest a line each: what it is in bold, then its value
        facts = []
        if sb.get("hit_dice"):
            facts.append(("Hit Dice", sb["hit_dice"]))
        if sb.get("saves"):
            facts.append(("Saving Throws", ", ".join(f"{a} {v}" for a, v in sb["saves"])))
        if sb.get("skills"):
            facts.append(("Skills", ", ".join(f"{k} {v}" for k, v in sb["skills"])))
        for key, label in (("damage_resistances", "Resistances"), ("damage_immunities", "Immunities"),
                           ("condition_immunities", "Condition Immunities")):
            if sb.get(key):
                facts.append((label, sb[key]))
        for key, label in (("senses", "Senses"), ("languages", "Languages")):
            if sb.get(key) and sb[key] != "—":
                facts.append((label, sb[key]))
        if facts:
            grid = QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(3)
            grid.setColumnStretch(1, 1)
            for r, (k, v) in enumerate(facts):
                grid.addWidget(_lbl(k, TEXT2, FS_SMALL, bold=True, wrap=False), r, 0, Qt.AlignTop)
                grid.addWidget(_lbl(str(v), TEXT, FS_SMALL, wrap=True), r, 1)
            dl.addLayout(grid)

        import html as _html
        for section_name, entries in [("Traits", sb.get("traits")),
                                      ("Actions", sb.get("actions")),
                                      ("Reactions", sb.get("reactions"))]:
            if not entries:
                continue
            head = QHBoxLayout(); head.setSpacing(8)
            head.addWidget(_lbl(section_name.upper(), GOLD2, FS_TINY, bold=True, wrap=False))
            line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background:{qa(GOLD, 0x55)};border:none;")
            head.addWidget(line, 1, Qt.AlignVCenter)
            dl.addLayout(head)
            for name, desc in entries:
                lab = QLabel(f"<b><i>{_html.escape(str(name))}.</i></b> {_html.escape(str(desc))}")
                lab.setTextFormat(Qt.RichText); lab.setWordWrap(True)
                lab.setStyleSheet(f"color:{TEXT};font-size:{FS_SMALL}px;background:transparent;border:none;")
                dl.addWidget(lab)
        cl.addWidget(details)

        if hp_key:
            def _on_hp_spin_changed(v):
                tracking[hp_key] = v
                self._mark_dirty()
                if v <= 0 and companion_key:
                    from dnd_app.data.statblocks import COMPANION_STATBLOCKS
                    # companion_key may be an instance-suffixed "key#N" id
                    # (Dancing Item + Creative Crescendo) — look the
                    # template up by its base key, same as
                    # resolve_companion_statblock() does.
                    tmpl = COMPANION_STATBLOCKS.get(companion_key.split("#", 1)[0], {})
                    if tmpl.get("requires_summon_action"):
                        self._toast(f"{sb['display_name']} has fallen — re-summon it after a long rest.")
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
                        self._toast(f"{sb['display_name']} has vanished, leaving its heart behind — "
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
                        self._toast(f"{sb['display_name']} has perished — a new one can be made at your next long rest.")
                        self._refresh_companions_tab()
            hp_spin_header.valueChanged.connect(_on_hp_spin_changed)

        def _toggle(event, d=details, chev=chevron):
            if event.button() != Qt.LeftButton:
                return
            d.setVisible(not d.isVisible())
            chev.setText("▾" if d.isVisible() else "▸")
        header.mousePressEvent = _toggle
        return card

    def _build_eldritch_cannon_card(self) -> QFrame:
        from dnd_app.core.calculator import resolve_companion_statblock
        sb = resolve_companion_statblock("eldritch_cannon", self.char)
        card = _card(qa(TEAL, 0x55))
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
