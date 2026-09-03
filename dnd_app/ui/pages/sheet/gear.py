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


class GearMixin:
    def _on_currency_change(self, coin: str, value: int):
        """User changed a currency spinbox (gp, sp, cp, ep, pp)."""
        self.char.setdefault("currency", {})[coin] = value
        self._mark_dirty()

    # ── Level-up / class management ───────────────────────────────────────────

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
        # See base.py's _tabs for why this is needed -- QTabWidget ignores
        # a plain QSS "background" rule without it, leaving the strip
        # past the last tab showing the OS default background.
        right_tabs.setAttribute(Qt.WA_StyledBackground, True)
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
        from dnd_app.data.phbCommon.items import MOUNTS
        if any(row[0] == name for row in MOUNTS):
            self._add_mount(name)
            self._toast(f"\U0001f40e {name} added — see its stat block in the Companions tab")
            return
        # Get weight and cost from item data
        from dnd_app.data.phbCommon.items import WEAPON_DICT, ARMOR_DICT, ADVENTURING_GEAR, ALL_WEAPONS
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
            from dnd_app.data.phbCommon.items import ALL_WEAPONS
            valid_names = {w[0] for w in ALL_WEAPONS}
        else:  # Armor
            cur_armor = self.char.get("armor_worn", "No Armor")
            equipped_list = [cur_armor] if cur_armor not in ("No Armor",) else []
            owned_names = {e.get("name","") for e in self.char.get("equipment", [])
                            if isinstance(e, dict)}
            from dnd_app.data.phbCommon.items import ARMOR
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
        from dnd_app.data.phbCommon.magic_items import get_magic_item
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
                from dnd_app.data.phbCommon.spells import SPELLS_BY_LEVEL
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

        from dnd_app.data.phbCommon.magic_items import get_magic_item, get_item_effect as _gie
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
            rm = _btn("✕", CRIMSON, variant="danger", width=20, height=20, radius=4,
                       border_width=1, bg_alpha=0x44, text_color=CRIM2,
                       hover_text="white", font_size=11, padding="0px")
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
                # Item Master).
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
        from dnd_app.data.phbCommon.magic_items import get_magic_item
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
        this kind of magical increase) and consumes the book. Equip-based
        MAGIC_ITEM_EFFECTS can't represent a one-time permanent change, so
        this writes directly to char["abilities"]."""
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
        from dnd_app.data.phbCommon.magic_items import get_magic_item
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

        from dnd_app.data.phbCommon.items import ADVENTURING_GEAR as _AG_notes
        GEAR_NOTES = {row[0]: (row[3] if len(row) > 3 else "") for row in _AG_notes}

        from dnd_app.data.phbCommon.items import WEAPON_DICT, ARMOR_DICT
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
        from dnd_app.data.phb2014.classes import ARTIFICER_INFUSION_TARGETS
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
        duration_category."""
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
        from dnd_app.data.phbCommon.items import WEAPON_DICT
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

