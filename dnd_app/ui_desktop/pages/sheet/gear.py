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
from ...widgets import (FlowLayout, FlowContainer, RarityBarDelegate, InspectButtonDelegate,
                        RarityInspectDelegate, RARITY_ROLE, FilterSidebar)
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
    MARTIAL_MELEE, MARTIAL_RANGED, FIREARMS, ARTISAN_TOOLS, SPECIAL_ARMOR,
    gear_icon, is_scroll_name, is_thrown_consumable)
from dnd_app.data.conditions import CONDITIONS
from .base import *
from .base import _lbl, _sep, _card
from dnd_app.ui_desktop import icons as _icons
from dnd_app.ui_desktop.popups import Ask, Tell


class GearMixin:
    def _on_currency_change(self, coin: str, value: int):
        """User changed a currency spinbox ("GP", "SP"... -- the spelling
        every other part of both apps uses)."""
        self.char.setdefault("currency", {})[coin] = value
        self._mark_dirty()

    # ── Level-up / class management ───────────────────────────────────────────

    def _gear_tabs_style(self, tabs):
        # See base.py's _tabs for why this is needed -- QTabWidget ignores
        # a plain QSS "background" rule without it
        tabs.setAttribute(Qt.WA_StyledBackground, True)
        tabs.tabBar().setUsesScrollButtons(False)
        tabs.tabBar().setElideMode(Qt.ElideRight)
        tabs.setStyleSheet(
            # selected tab joined to its page (see theme.py's QTabWidget::pane)
            f"QTabWidget::pane{{background:{SURF};border:1px solid {BORDER};border-top-left-radius:0px;border-top-right-radius:8px;border-bottom-right-radius:8px;border-bottom-left-radius:8px;top:-1px;}}"
            f"QTabBar::tab{{background:{SURF2};color:{TEXT2};padding:8px 12px;"
            f"font-size:{FS_SMALL}px;border:1px solid {BORDER};"
            f"border-top-left-radius:6px;border-top-right-radius:6px;border-bottom-right-radius:0px;border-bottom-left-radius:0px;margin-right:1px;}}"
            f"QTabBar::tab:selected{{background:{SURF};color:{GOLD2};font-weight:700;border-bottom-color:{SURF};}}")

    def _build_tab_gear(self):
        tab = QWidget(); root = QVBoxLayout(tab)
        root.setContentsMargins(16,16,16,16); root.setSpacing(8)

        # ── Two panels: left = yours (Loadout / Inventory / Infusions), right = the browsers
        from ...widgets import GripSplitter
        splitter = GripSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_w = QWidget(); left_l = QVBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 4, 0); left_l.setSpacing(8)
        left_tabs = QTabWidget()
        left_tabs.setObjectName("gearLeftTabs")
        self._gear_tabs_style(left_tabs)
        self._gear_left_tabs = left_tabs

        # ── Loadout: in hand, worn, tattoos (core/loadout.py, as Android's)
        lo_scroll = QScrollArea(); lo_scroll.setWidgetResizable(True)
        lo_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        lo_inner = QWidget(); lo_inner.setObjectName("loadoutPage")
        lo_inner.setStyleSheet(f"QWidget#loadoutPage{{background:{SURF};}}")
        self._loadout_lay = QVBoxLayout(lo_inner)
        self._loadout_lay.setContentsMargins(12, 10, 12, 12); self._loadout_lay.setSpacing(8)
        lo_scroll.setWidget(lo_inner)
        left_tabs.addTab(lo_scroll, "Loadout")
        _icons.set_tab_icon(left_tabs, lo_scroll, "shield", 15)

        # ── Inventory: everything else you carry
        inv_page = QWidget(); egl = QVBoxLayout(inv_page)
        egl.setContentsMargins(10, 10, 10, 10); egl.setSpacing(8)
        inv_head = QHBoxLayout(); inv_head.setContentsMargins(0, 0, 0, 0); inv_head.setSpacing(8)
        self._inv_filter = QLineEdit(); self._inv_filter.setPlaceholderText("Find in your inventory…")
        self._inv_filter.setClearButtonEnabled(True)
        from PySide6.QtGui import QIcon
        _icons.set_action_icon(self._inv_filter.addAction(QIcon(), QLineEdit.LeadingPosition), "search")
        self._inv_filter.setStyleSheet(f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};"
                                       f"border-radius:6px;padding:4px 8px;color:{TEXT};}}")
        self._inv_filter.textChanged.connect(lambda *_: self._apply_inventory_filter())
        inv_head.addWidget(self._inv_filter, 1)
        add_eq = QPushButton("+ Custom item")
        add_eq.setToolTip("Add something that isn't in the Equipment browser")
        add_eq.setStyleSheet(_btn("", TEAL, variant="cta", text_color=TEAL2, radius=6, font_size=FS_SMALL,
                                  padding="0px 12px", min_height0=True).styleSheet()
                             + "QPushButton{min-height:30px;max-height:30px;}")
        add_eq.clicked.connect(self._add_equipment_dialog)
        inv_head.addWidget(add_eq, 0, Qt.AlignVCenter)
        egl.addLayout(inv_head)
        self._gear_equip_tree = QTreeWidget()
        # Item | Eq (tick: hold it, wear it, put it on) | Qty | Wt | Value | view | remove
        self._gear_equip_tree.setHeaderLabels(["Item", "Eq", "Qty", "Wt", "Value", "", ""])
        self._gear_equip_tree.setAlternatingRowColors(True)
        self._gear_equip_tree.setRootIsDecorated(False)
        self._gear_equip_tree.setUniformRowHeights(True)
        self._gear_equip_tree.setStyleSheet(
            # text colour on the widget, not ::item -- an ::item colour would
            # override each row's own (rarity) colour
            f"QTreeWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;"
            f"alternate-background-color:{SURF};color:{TEXT};}}"
            f"QTreeWidget::item{{padding:3px 2px;font-size:{FS_SMALL}px;}}"
            f"QTreeWidget::item:selected{{background:{TEAL};color:#0a0d12;}}")
        self._gear_equip_tree.header().setStyleSheet(
            f"QHeaderView::section{{background:{SURF2};color:{GOLD2};font-weight:700;"
            f"font-size:{FS_TINY}px;padding:4px;border:1px solid {BORDER};}}")
        hdr = self._gear_equip_tree.header()
        # the Item column takes the spare width -- Qt otherwise stretches the
        # (blank) last column and leaves names cut short beside empty space
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in [(1,40),(2,76),(5,32),(6,32)]:
            hdr.setSectionResizeMode(col, QHeaderView.Fixed)
            self._gear_equip_tree.setColumnWidth(col, w)
        # weight and value: always as wide as what's in them, never cut short
        for col in (3, 4):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        hdr.setMinimumSectionSize(32)
        # a magic item's rarity is a coloured bar on the row's left edge
        self._gear_equip_tree.setItemDelegateForColumn(0, RarityBarDelegate(self._gear_equip_tree))
        egl.addWidget(self._gear_equip_tree, 1)
        left_tabs.addTab(inv_page, "Inventory")
        _icons.set_tab_icon(left_tabs, inv_page, "package", 15)
        self._magic_item_rows = []
        left_l.addWidget(left_tabs, 1)

        # ── Money and carrying, under all three
        money_card = _card(qa(GOLD, 0x55))
        money_card.setObjectName("gearFooter")
        mcl = QHBoxLayout(money_card); mcl.setContentsMargins(12, 8, 12, 8); mcl.setSpacing(8)
        self._currency_spins = {}
        for coin, color in [("PP","#b0a0e0"),("GP","#f5c518"),("EP","#a0c8a0"),
                             ("SP","#d0d0d0"),("CP","#c87941")]:
            # each coin's colour, darker on a light theme so it still reads
            color = readable(color, SURF, SURF2)
            col = QVBoxLayout(); col.setSpacing(1)
            col.addWidget(_lbl(coin, color, FS_TINY, bold=True, align=Qt.AlignCenter))
            sp = QSpinBox(); sp.setRange(0,999999); sp.setFixedWidth(68)
            sp.setValue(self.char.get("currency",{}).get(coin,0))
            sp.setAlignment(Qt.AlignCenter)
            sp.setAccessibleName(f"{coin} coins")
            sp.setStyleSheet(f"QSpinBox{{font-size:{FS_BODY}px;font-weight:700;color:{color};"
                             f"border:1px solid {qa(color,0x66)};border-radius:6px;background:{SURF2};padding:2px;}}"
                             + SPIN_NO_BUTTONS)
            sp.valueChanged.connect(lambda v,k=coin: self._on_currency_change(k,v))
            col.addWidget(sp); mcl.addLayout(col)
            self._currency_spins[coin] = sp
        carry = QVBoxLayout(); carry.setSpacing(4); carry.setContentsMargins(12, 0, 0, 0)
        crow = QHBoxLayout(); crow.setSpacing(6)
        self._weight_lbl = _lbl("", TEAL2, FS_SMALL, bold=True, wrap=False)
        self._push_lbl = _lbl("", TEXT3, FS_SMALL, wrap=False)
        crow.addWidget(self._weight_lbl); crow.addStretch(1); crow.addWidget(self._push_lbl)
        carry.addLayout(crow)
        self._carry_bar = QProgressBar(); self._carry_bar.setTextVisible(False)
        self._carry_bar.setFixedHeight(8)
        self._carry_bar.setAccessibleName("Carried weight")
        carry.addWidget(self._carry_bar)
        mcl.addLayout(carry, 1)
        left_l.addWidget(money_card)
        self._update_weight()

        splitter.addWidget(left_w)
        # an item dragged over from a browser lands here (equipment asks how
        # many, as Add does)
        from dnd_app.ui_desktop.widgets import accept_drop
        left_w.setObjectName("inventoryDrop")
        accept_drop(left_w, "equipment", lambda n: self._add_mundane_from_browser(n), TEAL)
        accept_drop(left_w, "magic-item", lambda n: self._add_magic_item_by_name(n), TEAL)

        # ── RIGHT: browser tabs (Mundane | Magic) ─────────────────────────────
        right_tabs = QTabWidget()
        self._gear_tabs_style(right_tabs)

        # ── MUNDANE BROWSER ───────────────────────────────────────────────────
        mundane_tab = QWidget(); mdt = QVBoxLayout(mundane_tab)
        mdt.setContentsMargins(8,8,8,8); mdt.setSpacing(6)

        # Search box across the top; the category filter lives in a sidebar
        # behind the funnel button at the end of the search row
        self._md_search = QLineEdit(); self._md_search.setPlaceholderText("Search equipment…")
        self._md_search.setStyleSheet(f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};"
                                       f"border-radius:6px;padding:4px 8px;color:{TEXT};}}")
        self._md_cat = QComboBox()
        for cat in ["All","Weapons — Simple","Weapons — Martial","Materials (Silvered/Adamantine)","Armor",
                     "Adventuring Gear","Tools"]:
            self._md_cat.addItem(cat)
        self._md_filters = FilterSidebar(mundane_tab)
        self._md_filters.add_combo("Category", self._md_cat)
        mdt.addLayout(self._md_filters.search_row(self._md_search))

        self._md_list = QTreeWidget()
        # the last column is the magnifying glass
        self._md_list.setHeaderLabels(["Name","Category","Damage / AC","Weight","Cost",""])
        self._md_list.setAlternatingRowColors(True)
        self._md_list.setRootIsDecorated(True)
        self._md_list.setStyleSheet(
            f"QTreeWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;"
            f"alternate-background-color:{SURF};}}"
            f"QTreeWidget::item{{padding:4px 2px;font-size:{FS_BODY}px;color:{TEXT};}}"
            f"QTreeWidget::item:selected{{background:{TEAL};color:#0a0d12;font-weight:700;}}"
            f"QTreeWidget::item:selected:!active{{background:{TEAL};color:#0a0d12;}}")
        # Name takes the spare width (the panel's default width leaves it
        # room for the names in full); Damage / AC has room for a weapon's
        # line, weight and cost are as wide as what's in them, and nothing
        # is pushed off the side
        md_hdr = self._md_list.header()
        md_hdr.setStretchLastSection(False)
        md_hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        md_hdr.setSectionResizeMode(1, QHeaderView.Interactive)
        self._md_list.setColumnWidth(1, 120)
        md_hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        self._md_list.setColumnWidth(2, 138)      # "1d8 bludgeoning"; a long armour line shortens
        self._md_list.setIndentation(14)
        self._md_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # weight and cost: as wide as what's in them, never cut short
        for col in (3, 4):
            md_hdr.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        md_hdr.setMinimumSectionSize(32)
        md_hdr.setSectionResizeMode(5, QHeaderView.Fixed)
        self._md_list.setColumnWidth(5, 32)
        # the list is already grouped under category headings, so a
        # Category column only took width from the names
        self._md_list.setColumnHidden(1, True)
        self._md_list.header().setStyleSheet(
            f"QHeaderView::section{{background:{SURF2};color:{GOLD2};font-weight:700;"
            f"font-size:{FS_SMALL}px;padding:6px;border:1px solid {BORDER};}}")
        # a magnifying glass on each item's row (not the category headings)
        self._md_list.setItemDelegateForColumn(5, InspectButtonDelegate(
            self._md_list, self._show_item_details_for, selected_icon="#0a0d12", column=5,
            has_details=lambda name: bool(name) and name != "__section__"))
        self._md_list.itemDoubleClicked.connect(self._add_mundane_from_browser)
        from dnd_app.ui_desktop.widgets import drag_source
        # (dragged onto your inventory to add it)
        drag_source(self._md_list, "equipment",
                    lambda i: (lambda n: n if n and n != "__section__" else "")(i.siblingAtColumn(0).data(Qt.UserRole)))
        self._md_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._md_list.customContextMenuRequested.connect(self._on_mundane_browser_ctx)
        mdt.addWidget(self._md_list,1)
        add_selected = pill_btn("Add Selected to Inventory", TEAL)
        _icons.set_button_icon(add_selected, "arrow_left", 16, color=on_fill(TEAL))
        add_selected.clicked.connect(lambda: self._add_mundane_from_browser(self._md_list.currentItem(),0))
        mdt.addWidget(add_selected)
        right_tabs.addTab(mundane_tab, "Equipment")
        _icons.set_tab_icon(right_tabs, mundane_tab, "package", 15)

        # ── MAGIC ITEM BROWSER ────────────────────────────────────────────────
        magic_tab = QWidget(); mgt = QVBoxLayout(magic_tab)
        mgt.setContentsMargins(8,8,8,8); mgt.setSpacing(6)

        # Search box across the top; slot / rarity / attunement filters in
        # the funnel button's sidebar
        self._mi_search = QLineEdit(); self._mi_search.setPlaceholderText("Search magic items…")
        self._mi_search.setStyleSheet(f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};"
                                        f"border-radius:6px;padding:4px 8px;color:{TEXT};}}")
        self._mi_type_f = QComboBox()
        self._mi_type_f.addItems(["All Slots","Weapon","Armor","Ring","Cloak / Robe",
                                    "Hat / Helm","Boots / Slippers","Bracers / Gauntlets",
                                    "Belt","Potion","Scroll / Wand / Rod / Staff","Other"])
        self._mi_rarity_f = QComboBox()
        self._mi_rarity_f.addItems(["All Rarities","Common","Uncommon","Rare","Very Rare","Legendary","Artifact","Unknown"])
        self._mi_attune_f = QComboBox()
        self._mi_attune_f.addItems(["All","Requires Attunement","No Attunement"])
        self._mi_filters = FilterSidebar(magic_tab)
        self._mi_filters.add_combo("Slot", self._mi_type_f)
        self._mi_filters.add_combo("Rarity", self._mi_rarity_f)
        self._mi_filters.add_combo("Attunement", self._mi_attune_f)
        mgt.addLayout(self._mi_filters.search_row(self._mi_search))

        self._mi_browser = QListWidget()
        self._mi_browser.setStyleSheet(
            # alternate-background-color: the strip beside the rarity bar on
            # alternate rows (otherwise the default, white)
            f"QListWidget{{background:{BG};border:1px solid {BORDER};border-radius:6px;color:{TEXT};"
            f"alternate-background-color:{SURF};}}"
            f"QListWidget::item{{padding:6px 10px;font-size:{FS_BODY}px;}}"
            f"QListWidget::item:selected{{background:{PURP2};color:#15071f;font-weight:700;}}"
            f"QListWidget::item:selected:!active{{background:{PURP2};color:#15071f;}}"
            f"QListWidget::item:alternate{{background:{SURF};}}")
        self._mi_browser.setAlternatingRowColors(True)
        self._mi_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # rarity shown as a coloured bar on the left of each row (text stays
        # the normal text colour -- easier to read), and a magnifying glass
        # on the right for the item's details
        self._mi_browser.setItemDelegate(RarityInspectDelegate(
            self._mi_browser, self._show_item_details_for, selected_icon="#15071f"))
        self._mi_browser.itemDoubleClicked.connect(lambda item: self._add_magic_item_by_name(item.data(Qt.UserRole)))
        from dnd_app.ui_desktop.widgets import drag_source
        drag_source(self._mi_browser, "magic-item", lambda i: i.data(Qt.UserRole) or "")
        self._mi_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self._mi_browser.customContextMenuRequested.connect(self._on_magic_browser_ctx)
        mgt.addWidget(self._mi_browser,1)

        mi_add_btn = pill_btn("Add Selected to Inventory", INDIGO)
        _icons.set_button_icon(mi_add_btn, "arrow_left", 16, color=on_fill(INDIGO))
        mi_add_btn.clicked.connect(self._add_magic_from_browser)
        mgt.addWidget(mi_add_btn)
        right_tabs.addTab(magic_tab, "Magic Items")
        _icons.set_tab_icon(right_tabs, magic_tab, "magic", 15)

        # an Artificer's infusions: the third tab of the left side, beside
        # Loadout and Inventory (infusions.py adds it and takes it away)
        self._gear_side_tabs = self._gear_left_tabs
        if self._has_infuse_item_access():
            infusions_tab = self._build_tab_infusions()
            self._gear_left_tabs.addTab(infusions_tab, "Infusions")
            _icons.set_tab_icon(self._gear_left_tabs, infusions_tab, "infusions", 15)

        splitter.addWidget(right_tabs)
        # yours and the browser half and half (still draggable)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 500])
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
            # Firearms (DMG pp.267-268) are themselves categorized as
            # Martial Ranged in the real rules -- folded into this same
            # section rather than a separate menu entry, same weapon
            # proficiency and same browser as every other mundane
            # martial ranged weapon.
            sections.append(("Martial Ranged", MARTIAL_RANGED + FIREARMS, "wep"))
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
            ranged_weapons = SIMPLE_RANGED + MARTIAL_RANGED + FIREARMS
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
            from dnd_app.data.items import TOOL_STATS
            tool_data = [(t, "Tool") + TOOL_STATS[t] for t in ALL_TOOLS if t in TOOL_STATS]
            sections.append(("Tools",          tool_data,       "tool"))

        from dnd_app.core.inventory import money_text, weight_text
        for section_name, items, kind in sections:
            parent = QTreeWidgetItem([section_name])
            parent.setForeground(0, __import__('PySide6.QtGui',fromlist=['QColor']).QColor(GOLD2))
            # the list's own font in bold, as the carried-items list's groups
            # (QFont("") picked a serif stand-in)
            _sec_font = self._md_list.font(); _sec_font.setBold(True)
            parent.setFont(0, _sec_font)
            parent.setData(0, Qt.UserRole, "__section__")
            added = 0
            for row in items:
                if kind == "wep":
                    name,wcat,dmg,dtype,wt,cost,props = row[0],row[1],row[2],row[3],row[4] if len(row)>4 else 0,row[5] if len(row)>5 else "—",row[6] if len(row)>6 else []
                    display_dmg = f"{dmg} {dtype}"
                    display_cat = wcat
                    display_wt  = weight_text(wt) or "—"
                    display_cost= money_text(cost) if isinstance(cost, (int, float)) else "—"
                elif kind == "arm":
                    name,akind,base_ac,dex_cap = row[0],row[1],row[2],row[3]
                    if name in ("No Armor","Mage Armor (spell)"): continue
                    display_dmg = f"AC {base_ac}" + (f" +DEX(max {dex_cap})" if dex_cap else " +DEX" if akind in ("light","medium") and dex_cap is None else "")
                    display_cat = akind.title()
                    display_wt  = (weight_text(row[6]) or "—") if len(row) > 6 else "—"
                    display_cost= (money_text(row[7]) or "—") if len(row) > 7 else "—"
                elif kind == "gear":
                    name,wt,cost,notes = row[0],row[1],row[2],row[3] if len(row)>3 else ""
                    display_dmg = notes[:30] if notes else "—"
                    display_cat = "Gear"
                    display_wt  = weight_text(wt) or "—"
                    display_cost= money_text(cost) or "—"
                elif kind == "tool":
                    name = row[0]; display_dmg = "—"; display_cat = "Tool"
                    display_wt = weight_text(row[2]) or "—"
                    display_cost = money_text(row[3]) or "—"
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
                    tip_lines.append(f"{display_wt} \u2014 {display_cost}")
                elif kind == "mount":
                    tip_lines.append(f"{display_dmg} \u2014 {display_cost}")
                child.setToolTip(0, "<br>".join(tip_lines))
                parent.addChild(child)
                added += 1

            if added > 0:
                self._md_list.addTopLevelItem(parent)
                parent.setFirstColumnSpanned(True)   # the whole name, across the columns
                parent.setExpanded(True)

    def _on_mundane_browser_ctx(self, pos):
        """Right-click on an item in the Equipment browser: Add, or Show details."""
        item = self._md_list.itemAt(pos)
        name = item.data(0, Qt.UserRole) if item else None
        if not name or name == "__section__": return
        from dnd_app.ui_desktop.widgets import browser_row_menu
        browser_row_menu(self, self._md_list.viewport().mapToGlobal(pos), "Add to Inventory",
                         lambda: self._add_mundane_from_browser(item, 0),
                         lambda: self._show_item_details_for(name))

    def _add_mundane_from_browser(self, item, col=None):
        if not item: return
        name = item.data(0, Qt.UserRole) if hasattr(item,'data') else item
        if not name or name == "__section__": return
        qty, ok = Ask.getInt(self, f"Add {name}", f"How many {name}?", 1, 1, 9999, 1)
        if not ok: return
        # onto its row if it's already carried, with the rules' weight and
        # cost (core/inventory.py, as Android)
        from dnd_app.core.inventory import add_item
        add_item(self.char, name, qty)
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

    _RARITY_ORDER = ["Common","Uncommon","Rare","Very Rare","Legendary","Artifact","Unknown"]
    # dark grey -> amber, the same palette the Android app uses (one source:
    # data/magic_items.py RARITY_COLORS)
    from dnd_app.data.magic_items import RARITY_COLORS as _RARITY_COLORS

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
        # the six standard rarities in order, then any other the catalogue
        # uses (the Gnomengarde Grenade is "Unique") so nothing is hidden
        extra = sorted(r for r in by_rarity if r not in self._RARITY_ORDER)
        for rarity in self._RARITY_ORDER + extra:
            items_in_rarity = by_rarity.get(rarity,[])
            if not items_in_rarity: continue
            colour = self._RARITY_COLORS.get(rarity)
            # Rarity divider header (its bar shows the colour that follows)
            hdr = QListWidgetItem(f"── {rarity} ({len(items_in_rarity)}) ──")
            hdr.setForeground(QColor(TEXT2))
            if colour:
                hdr.setData(RARITY_ROLE, colour)
            f = QFont(); f.setBold(True); f.setPointSize(9)
            hdr.setFont(f)
            hdr.setFlags(Qt.NoItemFlags)  # not selectable
            hdr.setData(Qt.UserRole, None)
            self._mi_browser.addItem(hdr)
            # Items in this rarity
            for item in sorted(items_in_rarity, key=lambda i: i["name"].casefold()):
                attune_tag = " ◆" if item.get("attunement") else ""
                desc = item.get("desc","")
                label = f"  {item['name']}{attune_tag}"
                li = QListWidgetItem(label)
                if colour:
                    li.setData(RARITY_ROLE, colour)
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

    def _on_magic_browser_ctx(self, pos):
        """Right-click on a magic item in the browser: Add, or Show details."""
        item = self._mi_browser.itemAt(pos)
        name = item.data(Qt.UserRole) if item else None
        if not name: return
        from dnd_app.ui_desktop.widgets import browser_row_menu
        browser_row_menu(self, self._mi_browser.viewport().mapToGlobal(pos), "Add to Inventory",
                         lambda: self._add_magic_item_by_name(name),
                         lambda: self._show_item_details_for(name))

    def _show_item_details_for(self, name: str, studied: bool = False, tip: str = ""):
        """An item's magnifying glass (the browsers, the inventory, owned
        magic items) and its Details: the page Android's View button opens
        (core/item_details.py). Something with no rules entry -- a custom
        item, a weapon made +1 here -- shows its row's tooltip instead."""
        from dnd_app.core.item_details import item_detail
        detail = item_detail(self.char, name)
        if detail["subtitle"] == "Item" and tip:
            self._show_item_details(name, tip)
            return
        show_details(self, detail["name"], item_details_markdown(
            detail, "*Studied -- its magic is spent.*" if studied else ""))

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
            reply = Tell.question(
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
                Tell.warning(self, "Unknown Item",
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
                # every scroll carries a spell -- cancelling adds nothing
                if not choices:
                    return
                spell_choice, ok = Ask.getItem(
                    self, "Spell Scroll", f"Which spell is inscribed on this {name}?",
                    choices, 0, False)
                if not ok or not spell_choice:
                    return
                name = f"{name} — {spell_choice}"
            existing = next((e for e in eq if isinstance(e,dict) and e.get("name")==name), None)
            if existing:
                existing["qty"] = existing.get("qty", 1) + 1   # stack
            else:
                eq.append({"name": name, "qty": 1, "weight": 0.5, "notes": "",
                           "magic": True, "rarity": catalog.get("rarity",""),
                           "desc": catalog.get("desc","")})
            self._refresh_gear_equipment(); self._mark_dirty(); return
        # All other magic items (attunable or not) → magic items section.
        # Every copy is its own entry; only magic ammunition stacks.
        from dnd_app.core.magic_items import add_owned_magic_item
        add_owned_magic_item(self.char, name)
        self.ctrl.refresh()
        self._refresh_magic_items()
        self._mark_dirty()

    def _filter_magic_item_combo(self, text: str):
        pass  # legacy — replaced by _populate_magic_browser

    def _add_magic_item(self):
        pass  # legacy — replaced by _add_magic_from_browser

    def _row_icon_btn(self, icon_name: str, tooltip: str, hover_colour: str) -> QPushButton:
        """A small icon button for a table row (view / remove): 28x24 with
        an 18px icon -- big enough to hit, small enough for the row."""
        b = QPushButton()
        b.setFixedSize(28, 24)
        b.setToolTip(tooltip)
        b.setCursor(Qt.PointingHandCursor)
        _icons.set_button_icon(b, icon_name, 18)
        b.setStyleSheet(
            f"QPushButton{{min-height:0;padding:0;background:transparent;border:1px solid transparent;"
            f"border-radius:5px;}}"
            f"QPushButton:hover{{background:{qa(hover_colour, 0x33)};border-color:{hover_colour};}}")
        return b

    def _show_item_details(self, name: str, html: str):
        """The magnifying glass on an owned item: its full details."""
        Tell.information(self, name, html or f"<b>{name}</b>")

    def _fit_gear_split(self):
        """(The left side is in tabs now: nothing to share out.)"""
        return

    def _refresh_magic_items(self):
        """What you hold and wear (Loadout) and what you carry (Inventory)
        after a magic item changes."""
        self._refresh_loadout()
        if hasattr(self, "_gear_equip_tree"):
            self._refresh_gear_equipment()

    # ── Loadout ──────────────────────────────────────────────────────────────
    def _loadout_head(self, title, right=None):
        row = QHBoxLayout(); row.setSpacing(8); row.setContentsMargins(0, 4, 0, 0)
        lbl = _lbl(title.upper(), GOLD, FS_SMALL, bold=True, wrap=False)
        lbl.setStyleSheet(lbl.styleSheet() + "letter-spacing:1px;")
        row.addWidget(lbl)
        rule = QFrame(); rule.setFixedHeight(1); rule.setStyleSheet(f"background:{BORDER};border:none;")
        row.addWidget(rule, 1)
        if right is not None:
            row.addWidget(right)
        return row

    def _loadout_slot(self, s):
        """One slot: its label, the item's name and what it does. Purple and
        a ◆ when attuned, teal when worn, dashed when empty. A click (or
        right-click) offers what can be done with it."""
        st = s["state"]
        colour = {"att": PURP2, "wear": TEAL, "empty": BORDER2}[st]
        if s["key"] == "tattoo":
            colour = AMBER if st != "att" else PURP2
        f = QFrame(); f.setObjectName(f"loadoutSlot_{s['key']}")
        f.setProperty("slotName", s["name"])
        f.setCursor(Qt.PointingHandCursor)
        bg = {"att": qa(PURP2, 0x14), "wear": SURF2, "empty": SURF}[st]
        f.setStyleSheet(f"QFrame#{f.objectName()}{{background:{bg};border:1px {'dashed' if st == 'empty' else 'solid'} "
                        f"{qa(colour, 0xaa)};border-radius:9px;}}"
                        f"QFrame#{f.objectName()}:hover{{border-color:{colour};}}")
        f.setMinimumHeight(60)
        lay = QVBoxLayout(f); lay.setContentsMargins(10, 6, 10, 6); lay.setSpacing(1)
        top = QHBoxLayout(); top.setSpacing(4)
        cap = _lbl((s.get("where") or s["label"]).upper() if s["key"] == "tattoo" else s["label"].upper(),
                   TEXT3, FS_TINY, bold=True, wrap=False)
        top.addWidget(cap); top.addStretch(1)
        if s["attuned"]:
            top.addWidget(_lbl("◆", PURP2, FS_TINY, wrap=False))
        lay.addLayout(top)
        name = QLabel(s["name"] or "Empty")
        name.setStyleSheet(f"color:{(TEXT3 if st == 'empty' else (PURP2 if st == 'att' else TEXT))};"
                           f"font-size:{FS_SMALL + 1}px;font-weight:{600 if st == 'empty' else 700};background:transparent;border:none;")
        lay.addWidget(name)
        what = QLabel(s["what"]); what.setStyleSheet(f"color:{TEXT2};font-size:{FS_TINY}px;background:transparent;border:none;")
        lay.addWidget(what)
        what.setVisible(bool(s["what"]))
        for w in (name, what):
            w.setMinimumWidth(10)
        # long names and lines shorten with "…" (the whole of it on hover)
        from PySide6.QtGui import QFontMetrics
        def _elide(ev=None, lab=name, text=name.text(), w=what, wt=s["what"]):
            for l, t in ((lab, text), (w, wt)):
                l.setText(QFontMetrics(l.font()).elidedText(t, Qt.ElideRight, max(10, f.width() - 22)))
        f.resizeEvent = lambda ev, fn=_elide: fn()
        if s.get("versatile"):
            grip = QPushButton(s.get("grip") or "1H")
            grip.setObjectName("gripToggle")
            grip.setCursor(Qt.PointingHandCursor)
            grip.setToolTip("Held in one hand or two (the Combat page shows both damage dice)")
            grip.setAccessibleName("One or two hands")
            grip.setStyleSheet(f"QPushButton{{background:{qa(TEAL, 0x22)};color:{TEAL2};border:1px solid {qa(TEAL, 0x99)};"
                               f"border-radius:5px;padding:0 6px;min-height:18px;max-height:18px;font-size:{FS_TINY}px;font-weight:800;}}"
                               f"QPushButton:hover{{background:{qa(TEAL, 0x44)};}}")
            grip.clicked.connect(lambda _=False, two=(s.get("grip") != "2H"): self._set_grip(two))
            top.addWidget(grip)
        tip = (f"<b>{s['name']}</b><br>{s['what']}<br><br><i>Click to swap it for something else, "
               f"right-click to take it off</i>" if s["name"]
               else f"{s['label']}: nothing here.<br><i>Click to put something on</i>")
        f.setToolTip(tip)
        f.setAccessibleName(f"{s['label']}: {s['name'] or 'empty'}")
        def _press(ev, slot=s, w=f):
            if ev.button() == Qt.RightButton:
                if slot["name"]:
                    QTimer.singleShot(0, self, lambda: self._take_off_slot(slot))
            elif ev.button() == Qt.LeftButton:
                self._loadout_menu(slot, w, ev.globalPos())
        f.mousePressEvent = _press
        return f

    def _refresh_loadout(self):
        lay = getattr(self, "_loadout_lay", None)
        if lay is None:
            return
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
            elif it.layout() is not None:
                self._clear_layout(it.layout())
        from dnd_app.core.loadout import loadout
        L = loadout(self.char)
        ac = _lbl(f"AC {L['ac']}" + (f"  ·  {L['saves']}" if L["saves"] else ""), IND2, FS_SMALL, bold=True, wrap=False)
        lay.addLayout(self._loadout_head("In hand", ac))
        g = QGridLayout(); g.setSpacing(7)
        col = 0
        for s in L["in_hand"]:
            span = 2 if s["key"] == "both" else 1
            g.addWidget(self._loadout_slot(s), 0, col, 1, span)
            col += span
        for c in range(3):
            g.setColumnStretch(c, 1)
        lay.addLayout(g)
        att = QWidget(); al = QHBoxLayout(att); al.setContentsMargins(0, 0, 0, 0); al.setSpacing(4)
        al.addWidget(_lbl(f"ATTUNED {L['attuned']} / {L['limit']}", PURP2, FS_TINY, bold=True, wrap=False))
        for i in range(L["limit"]):
            dot = QLabel(); dot.setFixedSize(11, 11)
            dot.setStyleSheet(f"border:2px solid {PURP2};border-radius:5px;background:{PURP2 if i < L['attuned'] else 'transparent'};")
            al.addWidget(dot)
        att.setObjectName("attunedPips")
        lay.addLayout(self._loadout_head("Worn", att))
        g = QGridLayout(); g.setSpacing(7)
        for i, s in enumerate(L["worn"]):
            g.addWidget(self._loadout_slot(s), i // 4, i % 4)
        for c in range(4):
            g.setColumnStretch(c, 1)
        lay.addLayout(g)
        if L["other"]:
            lay.addLayout(self._loadout_head("Also in use"))
            g = QGridLayout(); g.setSpacing(7)
            for i, s in enumerate(L["other"]):
                g.addWidget(self._loadout_slot(s), i // 4, i % 4)
            for c in range(4):
                g.setColumnStretch(c, 1)
            lay.addLayout(g)
        # flasks and explosives you carry: tick the ones on your belt, and
        # the Combat page lists them under Ready to throw
        from dnd_app.core.throwables import carried
        th = carried(self.char)
        if th:
            n_on = sum(1 for t in th if t["ready"])
            lay.addLayout(self._loadout_head("Ready to throw",
                          _lbl(f"{n_on} ready", AMBER, FS_TINY, bold=True, wrap=False)))
            g = QGridLayout(); g.setSpacing(7)
            for i, t in enumerate(th):
                g.addWidget(self._throw_chip(t), i // 4, i % 4)
            for c in range(4):
                g.setColumnStretch(c, 1)
            lay.addLayout(g)
        # tattoos: only once there's one
        if L["tattoos"]:
            lay.addLayout(self._loadout_head(f"Tattoos ({len(L['tattoos'])})"))
            g = QGridLayout(); g.setSpacing(7)
            for i, s in enumerate(L["tattoos"]):
                g.addWidget(self._loadout_slot(s), i // 2, i % 2)
            lay.addLayout(g)
        lay.addStretch(1)

    def _throw_chip(self, t):
        """A throwable in the Loadout: click to have it ready to throw (amber,
        ticked) or not (dashed)."""
        on = t["ready"]
        b = QPushButton(("✓  " if on else "") + f"{t['label']}  ×{t['qty']}")
        b.setObjectName("throwChip")
        b.setCursor(Qt.PointingHandCursor)
        b.setCheckable(True); b.setChecked(on)
        b.setToolTip(f"<b>{t['name']}</b><br>" + ("Ready to throw: on the Combat page. Click to put it away."
                                                   if on else "Click to have it ready to throw on the Combat page."))
        b.setAccessibleName(f"{t['label']}, {'ready to throw' if on else 'not ready'}")
        b.setStyleSheet(f"QPushButton{{background:{qa(AMBER, 0x1c) if on else SURF};color:{AMBER if on else TEXT2};"
                        f"border:1px {'solid' if on else 'dashed'} {qa(AMBER, 0xaa) if on else BORDER2};"
                        f"border-radius:9px;min-height:34px;padding:0 10px;font-size:{FS_SMALL}px;font-weight:700;"
                        f"text-align:left;}}QPushButton:hover{{border-color:{AMBER};}}")
        b.clicked.connect(lambda _=False, n=t["name"], v=not on: QTimer.singleShot(0, self, lambda: self._set_ready_throw(n, v)))
        return b

    def _set_ready_throw(self, name: str, on: bool):
        from dnd_app.core.throwables import set_ready
        set_ready(self.char, name, on)
        self._mark_dirty()
        self._refresh_loadout()
        self._refresh_combat_weapons()

    def _clear_layout(self, l):
        while l.count():
            it = l.takeAt(0)
            if it.widget() is not None:
                it.widget().setParent(None); it.widget().deleteLater()
            elif it.layout() is not None:
                self._clear_layout(it.layout())

    def _loadout_menu(self, s, w, pos):
        """Left-click a slot: what you carry that could go there (empty: to
        put on; filled: to swap in, the old one back to your inventory), then
        reading it, attuning, moving a tattoo, swapping hands."""
        from PySide6.QtWidgets import QMenu
        from dnd_app.ui_desktop.widgets import exec_menu
        from dnd_app.core.loadout import slot_options, TATTOO_PLACES
        menu = QMenu(w)
        n, uid = s["name"], s["uid"]
        opts = slot_options(self.char, s["key"]) if s["key"] != "tattoo" else []
        if opts:
            head = menu.addAction(("Replace with" if n else "Put on") + ":")
            head.setEnabled(False)
            for o in opts:
                menu.addAction(_icons.icon("shield" if s["key"] not in ("main", "off", "both") else "combat"),
                               o["name"]).triggered.connect(
                    lambda checked=False, o=o: self._equip_slot(s["key"], o["name"], o["uid"]))
        elif s["key"] != "tattoo":
            none = menu.addAction("Nothing you carry goes here" if not n else "Nothing else you carry goes here")
            none.setEnabled(False)
        if n:
            menu.addSeparator()
            menu.addAction(_icons.icon("search"), f"Details: {n[:36]}").triggered.connect(
                lambda: self._show_item_details_for(n))
            if uid and s["needs"]:
                menu.addAction(_icons.icon("magic"), "End attunement" if s["attuned"] else "Attune").triggered.connect(
                    lambda: self._toggle_attunement(uid, not s["attuned"]))
            from dnd_app.data.magic_items import get_item_effect as _gie
            eff = _gie(n)
            if isinstance(eff, dict) and eff.get("type") == "resistance_choice":
                now = (self.char.get("_choices", {}).get(f"item_dmgtype_{n}") or [""])[0]
                sub = menu.addMenu(_icons.icon("shield"), "Damage type" + (f" (now {now.lower()})" if now else ""))
                for dt in eff.get("pool", []):
                    sub.addAction(dt).triggered.connect(lambda checked=False, d=dt: self._set_item_damage_type(n, d))
            if s["key"] == "tattoo":
                sub = menu.addMenu(_icons.icon("pencil"), "Move it to" + (f" (now {s['where'].lower()})" if s["where"] else ""))
                for place in TATTOO_PLACES:
                    sub.addAction(place).triggered.connect(lambda checked=False, p=place: self._place_tattoo(uid, p))
            if s.get("swap"):
                menu.addAction(_icons.icon("combat"), "Swap hands").triggered.connect(self._swap_hands)
        exec_menu(menu, pos)

    def _equip_slot(self, slot: str, name: str, uid: str = ""):
        from dnd_app.core.loadout import equip_slot, slot_taken_by, put_on, is_tattoo
        if uid and slot not in ("main", "off", "both", "armor"):
            # a worn magic item: as from the inventory (a ring asks which)
            self._put_on_magic(uid)
            return
        off = equip_slot(self.char, slot, name, uid)
        if off:
            self._toast(f"{name} on; {off} is back in your inventory")
        self._after_loadout_change()

    def _take_off_slot(self, s):
        from dnd_app.core.loadout import take_off_slot
        gone = take_off_slot(self.char, s["key"], s["uid"])
        if gone:
            self._toast(f"{gone} is back in your inventory")
        self._after_loadout_change()

    def _set_grip(self, two: bool):
        from dnd_app.core.loadout import set_two_handed_grip
        set_two_handed_grip(self.char, two)
        self._refresh_loadout()
        self._mark_dirty()

    def _after_loadout_change(self):
        self._refresh_combat_weapons()
        update_all(self.char); self.ctrl.refresh()
        self._refresh_magic_items()
        self._refresh_combat()
        self._mark_dirty()

    def _put_on_magic(self, uid: str):
        """A magic item from your inventory onto you: a tattoo asks where it
        is; a slot already full asks which to take off."""
        from dnd_app.core.loadout import slot_taken_by, put_on, is_tattoo, TATTOO_PLACES, set_tattoo_place
        from dnd_app.core.magic_items import find_magic_item
        e = find_magic_item(self.char, uid)
        if not e:
            return
        name = e.get("name", "")
        out = ""
        hand = self._ask_hand(name)
        if hand is None:
            self._refresh_magic_items()
            return
        if is_tattoo(name):
            where, ok = Ask.getItem(self, name, f"Where is your {name}?", TATTOO_PLACES, 0, False)
            if not ok:
                return
            set_tattoo_place(self.char, uid, where)
        taken = slot_taken_by(self.char, uid)
        if taken:
            names = [t.get("name", "") for t in taken]
            pick, ok = Ask.getItem(self, name, f"Take off which, to put on {name}?", names, 0, False)
            if not ok:
                return
            out = taken[names.index(pick)].get("uid", "")
        off = put_on(self.char, uid, out, hand=hand)
        if off:
            self._toast(f"{name} on; {off} is back in your inventory")
        self.ctrl.refresh()
        self._refresh_magic_items()
        self._refresh_combat()
        self._mark_dirty()

    def _place_tattoo(self, uid: str, where: str):
        from dnd_app.core.loadout import set_tattoo_place
        set_tattoo_place(self.char, uid, where)
        self._refresh_loadout()
        self._mark_dirty()

    def _apply_inventory_filter(self):
        """Find in your inventory: rows whose name has every word typed, and
        their groups; a group with none found steps aside."""
        box = getattr(self, "_inv_filter", None)
        tree = getattr(self, "_gear_equip_tree", None)
        if box is None or tree is None:
            return
        words = box.text().casefold().split()
        for i in range(tree.topLevelItemCount()):
            h = tree.topLevelItem(i)
            shown = 0
            for j in range(h.childCount()):
                c = h.child(j)
                hit = all(w in c.text(0).casefold() for w in words)
                c.setHidden(not hit)
                shown += hit
            h.setHidden(h.childCount() > 0 and shown == 0)

    def _pick_weapon_base(self, item_name: str):
        """Which weapon an "any sword" item is: its dice, properties and
        proficiency on the Combat tab follow (core/riders.py)."""
        from dnd_app.core.riders import base_weapon_options, weapon_base_of, set_weapon_base
        opts = base_weapon_options(item_name)
        now = weapon_base_of(self.char, item_name)
        from dnd_app.core.magic_items import armor_base_options
        what = "armor" if armor_base_options(item_name) else "weapon"
        pick, ok = Ask.getItem(self, item_name, f"Which {what} is your {item_name}?",
                                        opts, opts.index(now) if now in opts else 0, False)
        if ok and set_weapon_base(self.char, item_name, pick):
            self._mark_dirty()
            self.ctrl.refresh()
            if hasattr(self, "_refresh_combat"):
                self._refresh_combat()
            self._toast(f"{item_name} is {pick.lower()}" if what == "armor" else f"{item_name} is a {pick.lower()}")

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

    def _toggle_attunement(self, uid: str, on: bool):
        from dnd_app.core.magic_items import set_owned_magic_item_attuned
        why = set_owned_magic_item_attuned(self.char, uid, on)
        if why:
            if "doesn't qualify" in why:
                why += "\n\n(Disable this check under Optional Rules if your table allows it anyway.)"
            Tell.warning(self, "Attunement", why)
            self._refresh_magic_items(); return
        # Deferred: self.ctrl.refresh() -> _on_char_updated() ->
        # _refresh_magic_items() clears and rebuilds the whole tree,
        # including this very checkbox — destroying it while its own
        # stateChanged signal is still on the call stack is a Qt
        # anti-pattern. Running it on the next event loop tick instead
        # lets this signal handler finish cleanly first.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self, self.ctrl.refresh)

    def _toggle_equipped(self, uid: str, on: bool):
        # Syncs equipped_weapons/armor_worn/shield in addition to the
        # item's own bookkeeping flag, so a magic weapon like Armblade
        # or Sun Blade shows up as an attackable weapon in the Combat
        # tab as soon as it's checked "Equipped".
        from dnd_app.core.magic_items import set_owned_magic_item_equipped
        set_owned_magic_item_equipped(self.char, uid, on)
        # Same deferred-refresh fix as _toggle_attunement above, and for
        # the same reason — this checkbox also lives in the tree that
        # _refresh_magic_items() clears and rebuilds.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self, self.ctrl.refresh)
        self._mark_dirty()

    def _remove_magic_item(self, uid: str):
        from dnd_app.core.magic_items import parse_magic_suffix, remove_owned_magic_item
        removed = remove_owned_magic_item(self.char, uid)
        if not removed:
            return
        name = removed.get("name", "")
        if any(e.get("name") == name for e in self.char.get("magic_items", [])):
            # another copy is still owned -- leave the enchanted gear as is
            self.ctrl.refresh(); self._refresh_combat(); self._refresh_magic_items()
            return

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

    def _study_manual(self, uid: str):
        """Study one of the 6 classic ability-score manuals/tomes: permanently
        raises the named ability score by 2 (real 5e rule -- no hard cap on
        this kind of magical increase). The book stays, marked studied --
        each copy works once. Equip-based MAGIC_ITEM_EFFECTS can't represent
        a one-time permanent change, so this writes to char["abilities"]."""
        from dnd_app.core.magic_items import find_magic_item, study_owned_manual
        entry = find_magic_item(self.char, uid)
        done = study_owned_manual(self.char, uid)
        if not done:
            self._toast("You've already studied this book — its magic is spent.")
            return
        ability, score = done
        self._toast(f"{entry['name']} — your {ability} score permanently increases by 2 (now {score})")
        self.ctrl.refresh()
        self._refresh_magic_items()
        self._mark_dirty()

    def _set_magic_ammo_qty(self, uid: str, entry: dict):
        from dnd_app.core.magic_items import set_owned_magic_item_qty
        n, ok = Ask.getInt(self, "Quantity", f"How many {entry.get('name', '')}? (0 removes them)",
                                    entry.get("qty", 1), 0, 9999)
        if not ok:
            return
        set_owned_magic_item_qty(self.char, uid, n)
        self.ctrl.refresh(); self._refresh_magic_items()
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
        """Carried weight against what you can carry: the footer's line and bar."""
        if not hasattr(self,"_weight_lbl"): return
        # the same numbers as Android's: core's total and carrying capacity
        from dnd_app.core.calculator import get_total_weight, get_carry_capacity_detail
        total = get_total_weight(self.char)
        detail = get_carry_capacity_detail(self.char)
        cap, push = detail["carry"], detail["push_drag_lift"]
        col = TEAL2 if total <= cap else (AMBER if total <= push else CRIM2)
        self._weight_lbl.setText(f"{total:g} / {cap} lb")
        self._weight_lbl.setStyleSheet(f"color:{col};font-size:{FS_SMALL}px;font-weight:700;background:transparent;border:none;")
        if hasattr(self, "_push_lbl"):
            self._push_lbl.setText(f"push {push}")
        bar = getattr(self, "_carry_bar", None)
        if bar is not None:
            bar.setRange(0, max(1, int(cap)))
            bar.setValue(int(min(total, cap)))
            bar.setStyleSheet(f"QProgressBar{{background:{SURF3};border:none;border-radius:4px;}}"
                              f"QProgressBar::chunk{{background:{col};border-radius:4px;}}")

    def _refresh_gear_equipment(self):
        from PySide6.QtGui import QColor
        self._refresh_ammo_counters()   # the combat tab's counters read this inventory
        self._gear_equip_tree.clear()

        # Carried equipment: everything in char["equipment"] (mundane gear,
        # plus magic potions and scrolls). Worn/attuned magic items are listed
        # once, in the Magic Items table below -- not repeated here.
        items = list(self.char.get("equipment", []))

        from dnd_app.core.magic_items import owned_magic_items
        from dnd_app.core.loadout import in_inventory
        _carried_magic = [e for e in owned_magic_items(self.char) if in_inventory(self.char, e)]
        if not items and not _carried_magic:
            placeholder = QTreeWidgetItem(["Nothing here: add from the browser on the right →", "", "", "", "", ""])
            placeholder.setForeground(0, QColor(TEXT3))
            self._gear_equip_tree.addTopLevelItem(placeholder)
            return

        from dnd_app.data.items import ADVENTURING_GEAR as _AG_notes
        GEAR_NOTES = {row[0]: (row[3] if len(row) > 3 else "") for row in _AG_notes}

        from dnd_app.data.items import WEAPON_DICT, ARMOR_DICT
        # Grouped like the Android inventory: Weapons / Armor / Magic Items
        # / Consumables / Tools & Gear, each under a header row with a
        # count, by name within each group (equipping doesn't move a row).
        _GROUPS = (("Weapons", "combat"), ("Armor", "shield"), ("Magic Items", "magic"),
                   ("Consumables", "potion"), ("Tools & Gear", "package"))
        _equipped_w = set(self.char.get("equipped_weapons", []))

        def _group_of(eq):
            n = eq.get("name", "")
            t = str(eq.get("type", "")) if eq.get("magic") else ""
            if n in WEAPON_DICT or any(w[0] == n for w in ALL_WEAPONS) or t == "Weapon":
                return 0
            if (n in ARMOR_DICT and n not in ("No Armor", "Mage Armor (spell)")) or t == "Armor":
                return 1
            if eq.get("magic"):
                return 2
            ln = n.lower()
            return 3 if ("potion" in ln or is_scroll_name(n) or is_thrown_consumable(n)) else 4

        def _is_equipped(eq):
            n = eq.get("name", "")
            if n in _equipped_w or self.char.get("armor_worn", "") == n:
                return True
            return ARMOR_DICT.get(n, {}).get("type") == "shield" and bool(self.char.get("shield"))

        def _sort_key(e):
            g = _group_of(e)
            if g == 2 or e.get("magic"):   # magic: rarity first (Common -> Artifact), then name
                r = e.get("rarity", "")
                rank = self._RARITY_ORDER.index(r) if r in self._RARITY_ORDER else len(self._RARITY_ORDER)
                return (g, 1, rank, e.get("name", "").lower())
            return (g, 0, e.get("name", "").lower())

        items.sort(key=_sort_key)
        from dnd_app.core.actions import item_action_cards
        from dnd_app.core.inventory import item_weight, item_cost, money_text, weight_text
        from dnd_app.core.weapons import hand_of as _hand_of
        _item_cards = item_action_cards(self.char)
        # What's in hand or worn is a group of its own, at the top: a row for
        # each weapon held (saying which hand), the armor worn, the shield.
        # The rest of a stack stays in its group -- four daggers with one in
        # hand are "Dagger (off hand)" under Equipped and Dagger x3 under
        # Weapons. (group, entry, what's held: a hand / "worn" / "", count)
        _rows = []
        for eq in items:
            n, qty, g = eq.get("name", ""), eq.get("qty", 1), _group_of(eq)
            held = []
            if g == 0 and n in _equipped_w:
                h = _hand_of(self.char, n)
                hands = ["main hand", "off hand"] if h == "one in each hand" else [h or "main hand"]
                held = (hands * 2)[:min(self.char.get("equipped_weapons", []).count(n), qty)]
            elif g == 1 and _is_equipped(eq):
                held = ["shield" if ARMOR_DICT.get(n, {}).get("type") == "shield" else "worn"]
            # (what's held or worn is on the Loadout tab)
            if qty - len(held) > 0:
                _rows.append((g, eq, "", qty - len(held)))
        _rows.sort(key=lambda r: r[0] >= 0)          # Equipped first; the rest as sorted
        _GROUP_OF = dict(enumerate(_GROUPS)); _GROUP_OF[-1] = ("Equipped", "combat")
        _counts = {}
        for r in _rows:
            _counts[r[0]] = _counts.get(r[0], 0) + 1
        _current_group, _header = None, None
        _hdrs = {}
        _hdr_font = self._gear_equip_tree.font(); _hdr_font.setBold(True)
        for _g, eq, _held, _shown in _rows:
            if _g != _current_group:
                _current_group = _g
                _header = QTreeWidgetItem([f"{_GROUP_OF[_g][0]}   ({_counts[_g]})", "", "", "", "", ""])
                _header.setIcon(0, _icons.icon(_GROUP_OF[_g][1]))
                _header.setForeground(0, QColor(GOLD2))
                _header.setFont(0, _hdr_font)
                _header.setFlags(Qt.ItemIsEnabled)
                self._gear_equip_tree.addTopLevelItem(_header)
                _header.setFirstColumnSpanned(True)
                _header.setExpanded(True)
                _hdrs[_g] = _header
            name = eq.get("name","?")
            is_magic  = bool(eq.get("magic"))
            _mi_type  = str(eq.get("type","")) if is_magic else ""
            is_weapon = (name in WEAPON_DICT or any(w[0]==name for w in ALL_WEAPONS)
                         or _mi_type == "Weapon")
            is_armor  = ((name in ARMOR_DICT and name not in ("No Armor","Mage Armor (spell)"))
                         or _mi_type == "Armor")
            rarity_color = self._RARITY_COLORS.get(eq.get("rarity", "")) if is_magic else None
            # text stays the plain text colour; a magic item's rarity is the
            # coloured bar on the left of its row (RarityBarDelegate)
            accent = TEXT if (is_weapon or is_armor or is_magic) else TEXT2
            _ln = name.lower()
            icon = ("combat" if is_weapon else "shield" if is_armor else "magic" if is_magic
                    else "potion" if "potion" in _ln else "file" if is_scroll_name(name)
                    else gear_icon(name) or "package")

            # one of it, its own or the rules' numbers (core/inventory.py), times how many on this row
            total_wt = item_weight(eq) * _shown
            wt_str = weight_text(total_wt) or "—"
            total_cost = item_cost(eq) * _shown
            cost_str = money_text(total_cost) or ("—" if not is_magic else "")

            # beside the name: which hand (or worn), "dedicated weapon"
            from dnd_app.core.weapons import dedicated_weapon, weapon_base
            _notes = [_held] if _held else []
            if is_weapon and dedicated_weapon(self.char) and weapon_base(name) == dedicated_weapon(self.char):
                _notes.append("dedicated weapon")
            _note = ", ".join(_notes)
            item = QTreeWidgetItem([f"{name}   ({_note})" if _note else name, "", "", wt_str, cost_str, ""])
            item.setIcon(0, _icons.icon(icon))
            is_shield = name in ARMOR_DICT and ARMOR_DICT[name].get("type") == "shield"
            item.setForeground(0, QColor(accent))
            item.setForeground(3, QColor(TEXT3))
            item.setForeground(4, QColor(TEXT3))
            if rarity_color:
                item.setData(0, RARITY_ROLE, rarity_color)

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
                    base += f"<br>{wt_str} \u2014 {cost_str}" if wt_str != "—" else f"<br>{cost_str}"
                if name in _item_cards:          # used from its card, on the Combat tab
                    base += f"<br><br>On the Combat tab: {_item_cards[name][2]}"
                item.setToolTip(0, base)

            _header.addChild(item)

            # Equip toggle (col 1) — only for weapons/armor: ticked on an
            # Equipped row (untick to put it away), unticked on the rest (tick
            # to take one up)
            _held_n = self.char.get("equipped_weapons", []).count(name) if is_weapon else 0
            if is_weapon:
                eq_cb = QCheckBox()
                eq_cb.setToolTip("Put it away" if _held else "Take one in hand")
                eq_cb.setChecked(bool(_held))
                eq_cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                                     f"border:1px solid {TEAL};background:{SURF2};}}"
                                     f"QCheckBox::indicator:checked{{background:{TEAL};border-color:{TEAL2};}}")
                if _held:
                    eq_cb.stateChanged.connect(lambda s, n=name, k=_held_n: QTimer.singleShot(0, self,
                        (lambda: self._put_one_away(n)) if k > 1 else (lambda: self._toggle_weapon_equipped(n, False))))
                else:
                    from dnd_app.core.weapons import can_hold_another
                    _another = _held_n > 0 and can_hold_another(self.char, name, eq.get("qty", 1))
                    eq_cb.stateChanged.connect(lambda s, n=name, an=_another: QTimer.singleShot(0, self,
                        (lambda: self._hold_another(n)) if an else (lambda: self._toggle_weapon_equipped(n, True))))
                self._gear_equip_tree.setItemWidget(item, 1, eq_cb)
            elif is_armor:
                eq_cb = QCheckBox(); eq_cb.setToolTip("Take it off" if _held else "Wear this armor")
                eq_cb.setChecked(bool(_held))
                eq_cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                                     f"border:1px solid {GOLD};background:{SURF2};}}"
                                     f"QCheckBox::indicator:checked{{background:{GOLD};border-color:{GOLD2};}}")
                _is_sh = ARMOR_DICT.get(name, {}).get("type") == "shield"
                eq_cb.stateChanged.connect(lambda s, n=name, sh=_is_sh: QTimer.singleShot(0, self, lambda: (
                    self._set_shield(bool(s)) if sh else self._toggle_armor_worn(n, bool(s)),
                    self._refresh_gear_equipment())))
                self._gear_equip_tree.setItemWidget(item, 1, eq_cb)

            # Quantity spin (col 2): how many on this row -- an Equipped row is
            # the one in hand, the rest of the stack has the count
            if _held:
                one = QLabel("1"); one.setAlignment(Qt.AlignCenter)
                one.setStyleSheet(f"color:{TEXT3};font-size:{FS_TINY}px;font-weight:700;background:transparent;")
                self._gear_equip_tree.setItemWidget(item, 2, one)
            qty_spin = QSpinBox()
            qty_spin.setRange(0, 9999); qty_spin.setValue(_shown)
            qty_spin.setAlignment(Qt.AlignCenter)
            qty_spin.setFixedHeight(22)
            qty_spin.setStyleSheet(
                # min-height:0 -- the theme's 32px input minimum made every row tall
                f"QSpinBox{{min-height:0;background:{SURF2};border:1px solid {BORDER2};border-radius:4px;"
                f"color:{GOLD2 if eq.get('qty',1)>1 else TEXT};font-size:{FS_TINY}px;font-weight:700;padding:0 2px;}}"
                f"QSpinBox::up-button,QSpinBox::down-button{{width:16px;background:{BORDER};}}")
            def _qty_changed(v, eq_ref=eq, in_hand=eq.get("qty", 1) - _shown):
                from dnd_app.core.inventory import set_item_count
                held = list(self.char.get("equipped_weapons", [])), self.char.get("armor_worn"), self.char.get("shield")
                set_item_count(self.char, eq_ref, v + in_hand)
                if v == 0 or held != (self.char.get("equipped_weapons", []), self.char.get("armor_worn"),
                                      self.char.get("shield")):
                    # the row goes, or fewer are left than were in hand:
                    # after this change has finished, the lists are rebuilt
                    self._mark_dirty()
                    QTimer.singleShot(0, self, self._after_items_removed)
                    return
                self._update_weight(); self._refresh_ammo_counters(); self._mark_dirty()
            qty_spin.valueChanged.connect(_qty_changed)
            if not _held:
                self._gear_equip_tree.setItemWidget(item, 2, qty_spin)
            else:
                qty_spin.deleteLater()

            # View (magnifying glass) and remove (trash) -- cols 5 and 6
            view = self._row_icon_btn("search", "Details", INDIGO)
            view.clicked.connect(lambda checked=False, n=name, it=item:
                                 self._show_item_details_for(n, tip=it.toolTip(0)))
            self._gear_equip_tree.setItemWidget(item, 5, view)
            rm = self._row_icon_btn("trash", "Remove one" if eq.get("qty", 1) > 1 else "Remove", CRIMSON)
            rm.clicked.connect(lambda checked=False, e=eq: self._remove_item_row(e))
            self._gear_equip_tree.setItemWidget(item, 6, rm)

            # Right-click context menu for full details (magic items) / removal
            # is handled at the tree level below (customContextMenuRequested),
            # since a per-item mousePressEvent wouldn't fire reliably when a
            # cell widget (checkbox/spinbox/button) is under the cursor.
            item.setData(0, Qt.UserRole, (name, eq, is_magic, is_weapon, is_armor, is_shield))

        self._add_carried_magic_rows(_carried_magic, _hdrs, _hdr_font)
        self._apply_inventory_filter()

        self._gear_equip_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        # Drop the handler from the previous refresh (a bare disconnect()
        # warns on the first refresh, when nothing is connected yet).
        prev = getattr(self, "_gear_tree_ctx_handler", None)
        if prev is not None:
            try:
                self._gear_equip_tree.customContextMenuRequested.disconnect(prev)
            except (RuntimeError, TypeError):
                pass
        def _tree_ctx_menu(pos):
            item = self._gear_equip_tree.itemAt(pos)
            if not item: return
            data = item.data(0, Qt.UserRole)
            if not data: return
            if data[0] == "__owned__":
                self._owned_magic_menu(data[1], self._gear_equip_tree.viewport().mapToGlobal(pos))
                return
            _name, _eq, _is_magic, _is_weapon, _is_armor, _is_shield = data
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self._gear_equip_tree)
            if _is_magic:
                tip = (f"<b>{_name}</b><br><i>{_eq.get('rarity','')} "
                       f"{_eq.get('type','')}</i><br><br>{self._format_multi_para(_eq.get('desc',''))}")
                act = menu.addAction(_icons.icon("features"), f"Details: {_name[:36]}")
                act.triggered.connect(lambda: self._show_item_details_for(_name, tip=tip))
            # "Infuse this item" — only for weapons/armor/shields, only
            # if the character actually knows an applicable Artificer
            # infusion and hasn't hit the active-infusion cap. Most
            # infusions apply to an existing mundane item the character
            # already owns, not a standalone creation.
            if not _is_magic and (_is_weapon or _is_armor or _is_shield):
                applicable = self._get_applicable_infusions(_is_weapon, _is_armor, _is_shield)
                if applicable:
                    infuse_menu = menu.addMenu(_icons.icon("infusions"), f"Infuse {_name[:30]} with...")
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
            # holding two weapons: which is in your main hand and which in
            # your off hand (the off hand's makes the bonus action attack)
            if _is_weapon:
                from dnd_app.core.weapons import can_swap_hands, hand_of
                if can_swap_hands(self.char, _name):
                    sw_act = menu.addAction(_icons.icon("combat"),
                                            f"Swap hands (now in your {hand_of(self.char, _name)})")
                    sw_act.triggered.connect(lambda checked=False: self._swap_hands())
                # two daggers: a second one of the stack in the other hand
                from dnd_app.core.weapons import can_hold_another
                if can_hold_another(self.char, _name, _eq.get("qty", 1)):
                    two_act = menu.addAction(_icons.icon("combat"), "Hold a second one (one in each hand)")
                    two_act.triggered.connect(lambda checked=False, n=_name: self._hold_another(n))
                elif self.char.get("equipped_weapons", []).count(_name) == 2:
                    one_act = menu.addAction(_icons.icon("combat"), "Put one away")
                    one_act.triggered.connect(lambda checked=False, n=_name: self._put_one_away(n))
            # Dedicated Weapon (Monk, Tasha's): pick the weapon that counts
            # as a monk weapon until the next rest
            if _is_weapon:
                from dnd_app.core.weapons import can_dedicate, dedicated_weapon, weapon_base
                if dedicated_weapon(self.char) and weapon_base(_name) == dedicated_weapon(self.char):
                    dw_act = menu.addAction(_icons.icon("dagger"), "Stop using as your Dedicated Weapon")
                    dw_act.triggered.connect(lambda checked=False: self._set_dedicated_weapon(""))
                elif can_dedicate(self.char, _name):
                    dw_act = menu.addAction(_icons.icon("dagger"), f"Make {_name[:30]} your Dedicated Weapon")
                    dw_act.triggered.connect(lambda checked=False, n=_name: self._set_dedicated_weapon(n))
            from dnd_app.core.throwables import is_throwable, ready as _ready_throw, _key as _throw_key
            if is_throwable(_name):
                _on = _throw_key(_name) in _ready_throw(self.char)
                rt_act = menu.addAction(_icons.icon("combat"), "Not ready to throw" if _on else "Ready to throw")
                rt_act.triggered.connect(lambda checked=False, n=_name, v=not _on: self._set_ready_throw(n, v))
            rm_act = menu.addAction(_icons.icon("trash"),
                                    f"Remove one {_name[:36]}" if _eq.get("qty", 1) > 1 else f"Remove {_name[:36]}")
            rm_act.triggered.connect(lambda: self._remove_item_row(_eq))
            if _eq.get("_mi_only"):
                rm_act.setEnabled(False)
                rm_act.setText("(Manage in Magic Items list below)")
            menu.exec(self._gear_equip_tree.viewport().mapToGlobal(pos))
        self._gear_equip_tree.customContextMenuRequested.connect(_tree_ctx_menu)
        self._gear_tree_ctx_handler = _tree_ctx_menu

    def _add_carried_magic_rows(self, entries, hdrs, hdr_font):
        """Magic items you carry but aren't using: under Magic Items, with a
        tick to put one on (or take it up), its glass and its bin."""
        from PySide6.QtGui import QColor
        from dnd_app.core.magic_items import is_magic_ammunition
        from dnd_app.data.magic_items import get_magic_item
        if not entries:
            return
        tree = self._gear_equip_tree
        head = hdrs.get(2)
        if head is None:
            head = QTreeWidgetItem(["Magic Items", "", "", "", "", ""])
            head.setIcon(0, _icons.icon("magic"))
            head.setForeground(0, QColor(GOLD2)); head.setFont(0, hdr_font)
            head.setFlags(Qt.ItemIsEnabled)
            at = sum(1 for g in hdrs if g < 2)
            tree.insertTopLevelItem(at, head)
            head.setFirstColumnSpanned(True); head.setExpanded(True)
        def _key(e):
            r = (get_magic_item(e.get("name", "")) or {}).get("rarity", "")
            rank = self._RARITY_ORDER.index(r) if r in self._RARITY_ORDER else len(self._RARITY_ORDER)
            return (rank, e.get("name", "").casefold())
        for e in sorted(entries, key=_key):
            name, uid = e.get("name", "?"), e.get("uid", "")
            cat = get_magic_item(name) or {}
            label = f"{e.get('qty', 1)}× {name}" if is_magic_ammunition(name) else name
            if e.get("attuned"):
                label += "   (attuned)"
            if e.get("studied"):
                label += "   (studied)"
            row = QTreeWidgetItem([label, "", "", "—", "", ""])
            row.setIcon(0, _icons.icon("bolt" if has_item_effect(name) else "magic"))
            row.setForeground(3, QColor(TEXT3))
            colour = self._RARITY_COLORS.get(cat.get("rarity", ""))
            if colour:
                row.setData(0, RARITY_ROLE, colour)
            desc = cat.get("desc", "")
            tip = (f"<b>{name}</b><br><i>{cat.get('rarity', '')} {cat.get('type', '')}</i>"
                   + ("<br><b>Requires attunement</b>" if cat.get("attunement") else "")
                   + (f"<br><br>{desc[:600]}{'…' if len(desc) > 600 else ''}" if desc else ""))
            row.setToolTip(0, tip)
            row.setData(0, Qt.UserRole, ("__owned__", e))
            head.addChild(row)
            from dnd_app.core.loadout import item_slot
            from dnd_app.core.magic_items import is_magic_shield
            wearable = (item_slot(name) or cat.get("attunement") or cat.get("type") in ("Weapon", "Armor")
                        or is_magic_shield(name))
            cb = QCheckBox(); cb.setToolTip("Put it on, or take it up")
            cb.setVisible(bool(wearable))
            cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                             f"border:1px solid {TEAL};background:{SURF2};}}"
                             f"QCheckBox::indicator:checked{{background:{TEAL};}}")
            cb.stateChanged.connect(lambda s, u=uid: QTimer.singleShot(0, self, lambda: self._put_on_magic(u)))
            tree.setItemWidget(row, 1, cb)
            if is_magic_ammunition(name):
                one = QLabel(str(e.get("qty", 1)))
            else:
                one = QLabel("1")
            one.setAlignment(Qt.AlignCenter)
            one.setStyleSheet(f"color:{TEXT3};font-size:{FS_TINY}px;font-weight:700;background:transparent;")
            tree.setItemWidget(row, 2, one)
            view = self._row_icon_btn("search", "Details", INDIGO)
            view.clicked.connect(lambda checked=False, n=name, t=tip, st=bool(e.get("studied")):
                                 self._show_item_details_for(n, st, t))
            tree.setItemWidget(row, 5, view)
            rm = self._row_icon_btn("trash", "Remove", CRIMSON)
            rm.clicked.connect(lambda checked=False, u=uid: self._remove_magic_item(u))
            tree.setItemWidget(row, 6, rm)
        head.setText(0, f"Magic Items   ({head.childCount()})")

    def _owned_magic_menu(self, entry, pos):
        """Right-click a magic item in your inventory."""
        from PySide6.QtWidgets import QMenu
        from dnd_app.ui_desktop.widgets import exec_menu
        from dnd_app.core.magic_items import is_magic_ammunition, can_study_manual
        from dnd_app.data.magic_items import get_magic_item
        name, uid = entry.get("name", ""), entry.get("uid", "")
        menu = QMenu(self)
        menu.addAction(_icons.icon("search"), f"Details: {name[:36]}").triggered.connect(
            lambda: self._show_item_details_for(name, bool(entry.get("studied"))))
        menu.addAction(_icons.icon("shield"), "Put it on" ).triggered.connect(lambda: self._put_on_magic(uid))
        if (get_magic_item(name) or {}).get("attunement"):
            if entry.get("attuned"):
                menu.addAction(_icons.icon("magic"), "End attunement").triggered.connect(
                    lambda: self._toggle_attunement(uid, False))
            else:
                menu.addAction(_icons.icon("magic"), "Attune").triggered.connect(
                    lambda: self._toggle_attunement(uid, True))
        if can_study_manual(entry):
            menu.addAction(_icons.icon("magic"), f"Study {name[:36]} (48 hrs over 6 days)").triggered.connect(
                lambda: self._study_manual(uid))
        if is_magic_ammunition(name):
            menu.addAction(_icons.icon("ammo"), "Set quantity…").triggered.connect(
                lambda: self._set_magic_ammo_qty(uid, entry))
        from dnd_app.core.riders import base_weapon_options, weapon_base_of
        if base_weapon_options(name):
            from dnd_app.core.magic_items import armor_base_options
            what = "armor" if armor_base_options(name) else "weapon"
            now = weapon_base_of(self.char, name)
            menu.addAction(_icons.icon("shield" if what == "armor" else "combat"),
                           f"Which {what} is it?" + (f" (now {now.lower()})" if now else "")).triggered.connect(
                lambda: self._pick_weapon_base(name))
        menu.addSeparator()
        menu.addAction(_icons.icon("trash"), f"Remove {name[:36]}").triggered.connect(lambda: self._remove_magic_item(uid))
        exec_menu(menu, pos)

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
            Tell.warning(self, "Infusion Limit Reached",
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
            self._toast(f"{item_name} infused with {infusion_name}")
        else:
            self._toast(f"{infusion_name} infused and given to another character "
                        f"(counts against your active infusions, not in your own inventory)")
        self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._mark_dirty()

    def _remove_item_row(self, entry: dict, n: int = 1):
        """Trash on an inventory row: one of that row goes (core/inventory.py)
        -- not every row of the same name -- and a weapon, armor or shield
        no longer owned isn't in hand or worn any more. The lists are rebuilt
        once this click has finished (the button is on the row)."""
        from dnd_app.core.inventory import remove_items
        if not remove_items(self.char, entry, n):
            return   # a display-only row (a magic item's), not in the inventory
        self._mark_dirty()
        QTimer.singleShot(0, self, self._after_items_removed)

    def _after_items_removed(self):
        self._refresh_gear_equipment()
        self._update_weight()
        self._refresh_combat()

    def _remove_equipment(self, name: str):
        """One of the first inventory row called `name` goes."""
        entry = next((e for e in self.char.get("equipment", []) if e.get("name") == name), None)
        if entry is not None:
            self._remove_item_row(entry)

    def _use_potion(self, name: str):
        """Drink one dose of a potion: consumes it from inventory and, if
        it has a lasting effect (EFFECT_TABLE entry), adds it to
        active_effects so it's visible on the combat page immediately —
        the same list Rage/Haste/etc. already use — and can be removed by
        hand or fades automatically on a short/long rest per its
        duration_category."""
        from dnd_app.core.inventory import remove_items
        entry = next((e for e in self.char.get("equipment", []) if e.get("name") == name), None)
        if not entry:
            return
        remove_items(self.char, entry, 1)          # this one dose, not every row of it

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
                from dnd_app.core.roll_log import log_roll     # (the roll history)
                log_roll(self.char, "potion", name, rolled,
                         f"{count}d{sides}" + (f" + {bonus}" if bonus else "") + f": healed {rolled} HP")
            if "damage_dice" in instant:
                count, sides, bonus = instant["damage_dice"]
                rolled = sum(random.randint(1, sides) for _ in range(count)) + bonus
                self.char["current_hp"] = max(0, self.char.get("current_hp", 0) - rolled)
                dtype = instant.get("damage_type", "")
                from dnd_app.core.roll_log import log_roll
                log_roll(self.char, "potion", name, rolled,
                         f"{count}d{sides}" + (f" + {bonus}" if bonus else "") + f": {rolled} {dtype} damage".replace("  ", " "))
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
            self._toast(f"{name} — {summary}")
        else:
            info = EFFECT_TABLE.get(name, {})
            if info:
                fx = self.char.setdefault("active_effects", [])
                if name not in fx:
                    fx.append(name)
                    self._toast(f"{name} — active (see Effects tab)")
                else:
                    self._toast(f"{name} — already active")
            else:
                self._toast(f"Drank {name}")

        self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._refresh_effects_list()
        self._apply_turn_state()
        self._mark_dirty()

    def _use_spell_scroll(self, name: str):
        """Cast the spell on one spell scroll (core/spellcasting.py: the
        class-list rule, the DC 10 + level check, the scroll's own save DC
        and attack). A blank scroll asks which spell is on it first."""
        from dnd_app.core.spellcasting import (parse_spell_scroll, use_spell_scroll,
                                                bind_spell_scroll, spell_for_scroll_level)
        from dnd_app.data.spells import get_spell
        from dnd_app.core.magic_items import start_concentration
        level, spell_name = parse_spell_scroll(name)
        if not spell_name:
            choices = spell_for_scroll_level(level)
            spell_name, ok = Ask.getItem(self, "Spell Scroll", "Which spell is on this scroll?",
                                                  choices, 0, False)
            if not ok or not spell_name:
                return
            name = bind_spell_scroll(self.char, name, spell_name)
            if not name:
                return
        spell = get_spell(spell_name) or {}
        if self.char.get("_wildshape_active") and not self._has_beast_spells():
            self._toast("Can't read a scroll while Wild Shaped — revert to your normal form first")
            return
        res = use_spell_scroll(self.char, name)
        if res["status"] == "cast" and spell:
            if spell.get("concentration"):
                start_concentration(self.char, spell_name)
                self.ctrl.update("concentration", self.char["concentration"], rebuild_char=False)
                self._refresh_concentration()
            fx_msg = self._apply_spell_active_effect(spell, spell.get("level", 0))
            if fx_msg:
                res["message"] += f"\n{fx_msg}"
            self._mark_spell_cast_time(spell)
        elif res["status"] == "failed" and spell:
            self._mark_spell_cast_time(spell)
        self._toast(res["message"])
        self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._apply_turn_state()
        self._mark_dirty()

    def _use_scroll(self, name: str):
        """Read one scroll. A spell scroll casts its spell (see
        _use_spell_scroll); any other scroll (the Scroll of Protection
        family...) is used up and, if it has a lasting effect
        (EFFECT_TABLE entry), added to active_effects the same way
        potions are."""
        from dnd_app.core.spellcasting import parse_spell_scroll
        if parse_spell_scroll(name):
            self._use_spell_scroll(name)
            return
        from dnd_app.core.inventory import remove_items
        entry = next((e for e in self.char.get("equipment", []) if e.get("name") == name), None)
        if not entry:
            return
        remove_items(self.char, entry, 1)          # this one scroll, not every row of it

        from dnd_app.core.effects import EFFECT_TABLE
        info = EFFECT_TABLE.get(name, {})
        if info:
            fx = self.char.setdefault("active_effects", [])
            if name not in fx:
                fx.append(name)
                self._toast(f"{name} — active (see Effects tab)")
            else:
                self._toast(f"{name} — already active")
        else:
            self._toast(f"Read {name}")

        self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._refresh_effects_list()
        self._apply_turn_state()
        self._mark_dirty()

    def _toggle_weapon_equipped(self, name: str, equip: bool):
        # the hands rules are shared with Android (core/weapons.py)
        from dnd_app.core.weapons import equip_weapon, unequip_weapon
        if equip:
            hand = self._ask_hand(name)
            if hand is None:
                self._refresh_gear_equipment()
                return
            equip_weapon(self.char, name, hand=hand)
        else:
            unequip_weapon(self.char, name)
        self._refresh_combat_weapons()
        update_all(self.char); self.ctrl.refresh()
        if hasattr(self,"_update_weight"): self._update_weight()
        self._mark_dirty()

    def _hold_another(self, name: str):
        """A second one of a weapon already in hand (two daggers, one in
        each hand) -- core/weapons.py, the same as Android's."""
        from dnd_app.core.weapons import equip_weapon
        hand = self._ask_hand(name, another=True)
        if hand is None:
            self._refresh_gear_equipment()
            return
        equip_weapon(self.char, name, another=True, hand=hand)
        self._after_hands_change()

    def _ask_hand(self, name: str, another: bool = False):
        """Both hands full and this weapon could go in either (light, or
        any one-handed one with Dual Wielder): which does it replace?
        "main" / "off", "" when there's nothing to ask, None if cancelled."""
        from dnd_app.core.weapons import hand_choice
        opts = hand_choice(self.char, name, another)
        if not opts:
            return ""
        pick, ok = Ask.getItem(self, name, f"Your hands are full. {name} replaces:", opts, 1, False)
        if not ok:
            return None
        return "main" if pick.startswith("Main") else "off"

    def _put_one_away(self, name: str):
        from dnd_app.core.weapons import unequip_weapon
        unequip_weapon(self.char, name, every=False)
        self._after_hands_change()

    def _after_hands_change(self):
        self._refresh_combat_weapons()
        update_all(self.char); self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._mark_dirty()

    def _swap_hands(self):
        """The main-hand weapon to your off hand and back (core/weapons.py,
        the same as Android's Swap hands)."""
        from dnd_app.core.weapons import swap_hands, hands
        off = swap_hands(self.char)
        if not off:
            return
        update_all(self.char); self.ctrl.refresh()
        self._refresh_gear_equipment()
        self._refresh_combat_weapons()
        self._mark_dirty()
        self._toast(f"{hands(self.char)['main']} in your main hand, {off} in your off hand")

    def _set_dedicated_weapon(self, name: str):
        """Dedicated Weapon: `name` counts as a monk weapon from now on
        ("" clears it). The Combat tab picks up Martial Arts for it."""
        if name:
            self.char["dedicated_weapon"] = name
        else:
            self.char.pop("dedicated_weapon", None)
        self._refresh_combat_weapons()
        self._refresh_gear_equipment()
        self._mark_dirty()

    def _set_shield(self, on: bool):
        """A shield's box in the inventory: carried on your arm or not (its
        +2 AC) -- never as the armor you wear."""
        self.char["shield"] = bool(on)
        update_all(self.char); self.ctrl.refresh()
        self._refresh_combat(); self._mark_dirty()

    def _toggle_armor_worn(self, name: str, wear: bool):
        if wear:
            self.char["armor_worn"] = name
        else:
            if self.char.get("armor_worn","") == name:
                self.char["armor_worn"] = "No Armor"
        update_all(self.char); self.ctrl.refresh()
        self._refresh_combat(); self._mark_dirty()

