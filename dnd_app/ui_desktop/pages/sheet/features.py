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
from ...widgets import FlowLayout, FlowContainer, FilterSidebar
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
from dnd_app.data.feats import get_feat, feat_summary
from dnd_app.data.spells import get_spell, spells_for_class, ALL_SPELLS
from dnd_app.data.items import (ARMOR, ARMOR_DICT, ALL_WEAPONS, WEAPON_DICT,
    ADVENTURING_GEAR, GEAR_NAMES, MOUNTS, ALL_TOOLS, SIMPLE_MELEE, SIMPLE_RANGED,
    MARTIAL_MELEE, MARTIAL_RANGED, ARTISAN_TOOLS, SPECIAL_ARMOR)
from dnd_app.data.conditions import CONDITIONS
from .base import *
from .base import _lbl, _sep, _card
from dnd_app.ui_desktop import icons as _icons



class FeatureCard(QFrame):
    """One feature on the Features page: its name and tags, a line of what
    it does, and -- once clicked open -- everything it says and the picks
    it holds (Metamagic, invocations...), each with what it does."""

    def __init__(self, card: dict, parent=None):
        super().__init__(parent)
        self.card = card
        self.setObjectName("featureCard")
        self.setProperty("featureId", card["id"])
        self._open = False
        more = bool(card["text"] or card["options"])
        self._more = more
        lay = QVBoxLayout(self); lay.setContentsMargins(12, 9, 12, 9); lay.setSpacing(3)
        head = QHBoxLayout(); head.setSpacing(6)
        self._arrow = QLabel("▸" if more else "")
        self._arrow.setFixedWidth(12)
        self._arrow.setStyleSheet(f"color:{TEXT3 if card['future'] else TEXT2};font-size:{FS_SMALL}px;background:transparent;border:none;")
        head.addWidget(self._arrow, 0, Qt.AlignTop)
        name = QLabel(card["name"])
        name.setObjectName("featureName")
        name.setWordWrap(True)
        name.setStyleSheet(f"color:{TEXT3 if card['future'] else TEXT};font-size:{FS_BODY}px;font-weight:700;"
                           f"background:transparent;border:none;")
        head.addWidget(name, 1)
        colors = {"uses": TEAL2, "action": AMBER, "origin": GOLD2, "sub": GOLD2}
        for t in card["tags"]:
            c = colors.get(t["kind"], TEXT2)
            tag = QLabel(t["text"])
            tag.setObjectName(f"featureTag_{t['kind']}")
            tag.setStyleSheet(f"QLabel{{color:{c};background:{qa(c, 0x1a)};border:1px solid {qa(c, 0x80)};"
                              f"border-radius:5px;padding:1px 7px;font-size:{FS_TINY}px;font-weight:700;}}")
            head.addWidget(tag, 0, Qt.AlignTop)
        lay.addLayout(head)
        self._summary = QLabel(card["summary"])
        self._summary.setObjectName("featureSummary")
        self._summary.setWordWrap(True)
        self._summary.setVisible(bool(card["summary"]))
        self._summary.setStyleSheet(f"color:{TEXT3 if card['future'] else TEXT2};font-size:{FS_SMALL}px;"
                                    f"padding-left:18px;background:transparent;border:none;")
        lay.addWidget(self._summary)
        # what opens: the whole text, then the picks
        self._body = QWidget(); self._body.setObjectName("featureBody")
        self._body.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(self._body); bl.setContentsMargins(18, 4, 0, 2); bl.setSpacing(8)
        if card["text"]:
            full = QLabel(card["text"])
            full.setObjectName("featureText")
            full.setWordWrap(True); full.setTextFormat(Qt.RichText)
            full.setTextInteractionFlags(Qt.TextSelectableByMouse)
            full.setStyleSheet(f"color:{TEXT};font-size:{FS_BODY}px;background:transparent;border:none;")
            bl.addWidget(full)
        for o in card["options"]:
            ob = QFrame(); ob.setObjectName("featureOption")
            ob.setStyleSheet(f"QFrame#featureOption{{background:{SURF};border:1px solid {BORDER};"
                             f"border-left:3px solid {GOLD2};border-radius:6px;}}")
            ol = QVBoxLayout(ob); ol.setContentsMargins(10, 6, 10, 6); ol.setSpacing(2)
            on = QLabel(o["name"]); on.setWordWrap(True)
            on.setStyleSheet(f"color:{GOLD2};font-size:{FS_SMALL}px;font-weight:700;background:transparent;border:none;")
            ol.addWidget(on)
            if o["text"]:
                ot = QLabel(o["text"]); ot.setWordWrap(True); ot.setTextFormat(Qt.RichText)
                ot.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;background:transparent;border:none;")
                ol.addWidget(ot)
            bl.addWidget(ob)
        self._body.setVisible(False)
        lay.addWidget(self._body)
        if more:
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip("Click to read it all")
        self.setAccessibleName(card["name"])
        self._style()

    def _style(self):
        fut = self.card["future"]
        if self._open:
            css = f"QFrame#featureCard{{background:{tint(SURF, GOLD, 0x10)};border:1px solid {GOLD};border-radius:10px;}}"
        else:
            css = (f"QFrame#featureCard{{background:{SURF};border:1px solid {BORDER if not fut else qa(BORDER, 0x80)};"
                   f"border-radius:10px;}}"
                   + (f"QFrame#featureCard:hover{{border-color:{BORDER2};background:{SURF2};}}" if self._more else ""))
        self.setStyleSheet(css)

    def is_open(self):
        return self._open

    def set_open(self, on: bool):
        if not self._more:
            return
        self._open = bool(on)
        self._body.setVisible(self._open)
        self._arrow.setText("▾" if self._open else "▸")
        self._style()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton and self._more:
            self.set_open(not self._open)
            ev.accept()
            return
        super().mousePressEvent(ev)


class FeaturesMixin:
    def _refresh_optional_features(self):
        """Rebuild the Optional Class Features card in the Features tab."""
        # No-op if not yet built; features tab handles this via _rebuild_features.
        pass

    def _build_tab_features(self):
        from PySide6.QtGui import QIcon, QKeySequence
        page = QWidget()
        pl = QVBoxLayout(page); pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(0)
        # Find a feature, and the chips that keep to one section: a bar over
        # the list, which stays put as the list scrolls
        bar = QWidget(); bar.setStyleSheet("background:transparent;")
        bl = QHBoxLayout(bar); bl.setContentsMargins(16, 12, 16, 4); bl.setSpacing(8)
        self._feat_filter = QLineEdit()
        self._feat_filter.setPlaceholderText("Find a feature…")
        _icons.set_action_icon(self._feat_filter.addAction(QIcon(), QLineEdit.LeadingPosition), "search")
        self._feat_filter.setClearButtonEnabled(True)
        self._feat_filter.setAccessibleName("Find a feature")
        self._feat_filter.setToolTip("By its name, or anything in what it does.  ("
                                     + QKeySequence(QKeySequence.Find).toString(QKeySequence.NativeText) + ")")
        self._feat_filter.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:7px;"
            f"padding:6px 10px;color:{TEXT};font-size:{FS_BODY}px;}}")
        self._feat_filter.setFixedWidth(340)
        self._feat_filter.textChanged.connect(lambda *_: self._apply_feature_filter())
        bl.addWidget(self._feat_filter)
        self._feat_chip_box = QWidget(); self._feat_chip_box.setStyleSheet("background:transparent;")
        self._feat_chip_lay = QHBoxLayout(self._feat_chip_box)
        self._feat_chip_lay.setContentsMargins(4, 0, 0, 0); self._feat_chip_lay.setSpacing(6)
        bl.addWidget(self._feat_chip_box)
        bl.addStretch(1)
        self._feat_count = _lbl("", TEXT3, FS_SMALL, wrap=False)
        bl.addWidget(self._feat_count)
        pl.addWidget(bar)
        # (Ctrl+F puts the cursor here: the sheet's own shortcut, which
        # goes to the search box of whichever tab is showing)

        tab = QScrollArea(); tab.setWidgetResizable(True)
        self._feat_scroll = tab
        w = QWidget(); tab.setWidget(w)
        self._feat_tab_lay = QVBoxLayout(w); self._feat_tab_lay.setContentsMargins(16, 10, 16, 16); self._feat_tab_lay.setSpacing(6)
        self._feat_chip = "All"
        self._feat_chips = {}
        self._feat_cards = []      # (FeatureCard, its section's chip, the level row it's in or None)
        self._feat_secs = []       # (section widget, chip, [level rows], [cards])
        self._feat_extras = []     # blocks that aren't features (tables, the DM's browser): hidden while filtering
        self._feat_none = None
        self._feat_open = set()    # the ids of the cards left open, kept across a rebuild
        self._feat_folded = {"dm"} # the sections folded away (the DM's card starts folded)
        self._feat_tab_lay.addStretch()
        pl.addWidget(tab, 1)
        return page

    def _set_feature_chip(self, chip):
        self._feat_chip = chip
        for name, b in self._feat_chips.items():
            b.setChecked(name == chip)
        self._apply_feature_filter()

    def _make_feature_chips(self, chips):
        lay = self._feat_chip_lay
        while lay.count():
            it = lay.takeAt(0)
            if it.widget():
                it.widget().setParent(None); it.widget().deleteLater()
        self._feat_chips = {}
        if self._feat_chip not in chips:
            self._feat_chip = "All"
        for chip in ["All"] + chips:
            b = QPushButton(chip)
            b.setObjectName(f"featureChip_{chip}")
            b.setCheckable(True); b.setChecked(chip == self._feat_chip)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:{SURF2};color:{TEXT2};border:1px solid {BORDER};border-radius:15px;"
                f"padding:0 12px;min-height:30px;max-height:30px;font-size:{FS_SMALL}px;font-weight:700;}}"
                f"QPushButton:hover{{border-color:{BORDER2};color:{TEXT};}}"
                f"QPushButton:checked{{background:{GOLD};color:{on_fill(GOLD)};border-color:{GOLD};}}")
            b.clicked.connect(lambda _=False, c=chip: self._set_feature_chip(c))
            lay.addWidget(b)
            self._feat_chips[chip] = b

    def _apply_feature_filter(self):
        """Show what the chip keeps and the box finds -- every word typed,
        in a feature's name, what it does, its picks or its section's
        heading -- and hide a level, or a section, with nothing left."""
        box = getattr(self, "_feat_filter", None)
        if box is None:
            return
        text = box.text()
        words = text.casefold().split()
        chip = getattr(self, "_feat_chip", "All")
        from dnd_app.core.features import feature_matches
        shown = total = 0
        for sec, sec_chip, rows, cards in self._feat_secs:
            in_chip = chip == "All" or chip == sec_chip
            n = 0
            for card in cards:
                hit = in_chip and feature_matches(card.card["find"], text)
                card.setVisible(hit)
                n += 1 if hit else 0
                if in_chip and not card.card["future"]:
                    total += 1
                    shown += 1 if hit else 0
            for row, row_cards in rows:
                row.setVisible(any(c.isVisibleTo(row) or (c.isVisible()) for c in row_cards)
                               if False else any(not c.isHidden() for c in row_cards))
            sec.setVisible(n > 0)
        for w in self._feat_extras:
            w.setVisible(not words and (chip == "All" or w.property("featureChip") == chip))
        self._feat_count.setText(f"{shown} of {total}" if words else f"{total} feature{'s' if total != 1 else ''}")
        if self._feat_none is not None:
            self._feat_none.setText(f"No feature matches “{text.strip()}”." if words and not shown else "")
            self._feat_none.setVisible(bool(words) and not shown)

    def _feature_section_head(self, sec, body):
        """A section's heading: ▾ NAME, the line beside it, its count and a
        rule; a click folds the section away."""
        head = QPushButton()
        head.setObjectName(f"featureSection_{sec['key']}")
        head.setCursor(Qt.PointingHandCursor)
        head.setFlat(True)
        hl = QHBoxLayout(head); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(8)
        arrow = QLabel("▾"); arrow.setStyleSheet(f"color:{GOLD};font-size:{FS_SMALL}px;background:transparent;")
        name = QLabel(sec["title"].upper())
        name.setStyleSheet(f"color:{GOLD};font-size:{FS_SMALL}px;font-weight:800;letter-spacing:1px;background:transparent;")
        hl.addWidget(arrow); hl.addWidget(name)
        if sec["sub"]:
            sub = QLabel(sec["sub"]); sub.setStyleSheet(f"color:{TEXT2};font-size:{FS_SMALL}px;background:transparent;")
            hl.addWidget(sub)
        if sec.get("count") is not None:
            cnt = QLabel(f"({sec['count']})"); cnt.setStyleSheet(f"color:{TEXT3};font-size:{FS_SMALL}px;background:transparent;")
            hl.addWidget(cnt)
        rule = QFrame(); rule.setFixedHeight(1); rule.setStyleSheet(f"background:{BORDER};border:none;")
        hl.addWidget(rule, 1)
        head.setStyleSheet("QPushButton{background:transparent;border:none;min-height:26px;max-height:26px;padding:0;}")
        head.setAccessibleName(f"{sec['title']} section")

        def _fold(_=False, b=body, a=arrow, k=sec["key"]):
            b.setVisible(b.isHidden())
            a.setText("▸" if b.isHidden() else "▾")
            if b.isHidden():
                self._feat_folded.add(k)
            else:
                self._feat_folded.discard(k)
        head.clicked.connect(_fold)
        if sec["key"] in self._feat_folded:
            body.setVisible(False)
            arrow.setText("▸")
        return head

    def _feature_rail_row(self, row, cards_out):
        """One level of a timeline: the level's number in a circle down the
        left, a line to the next, and its cards beside it."""
        w = QWidget(); w.setObjectName(f"featureLevel_{row['level']}")
        w.setStyleSheet("background:transparent;")
        hl = QHBoxLayout(w); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(12)
        col = QWidget(); col.setFixedWidth(36)
        cl = QVBoxLayout(col); cl.setContentsMargins(0, 6, 0, 0); cl.setSpacing(3)
        dot = QLabel(str(row["level"])); dot.setAlignment(Qt.AlignCenter); dot.setFixedSize(30, 30)
        st = row["state"]
        if st == "now":
            dot.setStyleSheet(f"background:{INDIGO};color:{on_fill(INDIGO)};border:2px solid {IND2};"
                              f"border-radius:15px;font-weight:800;font-size:{FS_SMALL}px;")
        else:
            fg = TEXT3 if st == "next" else IND2
            dot.setStyleSheet(f"background:{SURF2};color:{fg};border:2px solid {BORDER2 if st != 'next' else BORDER};"
                              f"border-radius:15px;font-weight:800;font-size:{FS_SMALL}px;")
        dot.setAccessibleName(f"Level {row['level']}")
        cl.addWidget(dot, 0, Qt.AlignHCenter)
        line = QFrame(); line.setFixedWidth(2); line.setStyleSheet(f"background:{BORDER};border:none;")
        cl.addWidget(line, 1, Qt.AlignHCenter)
        hl.addWidget(col)
        body = QVBoxLayout(); body.setContentsMargins(0, 0, 0, 8); body.setSpacing(6)
        if row["label"]:
            lab = QLabel(row["label"].upper())
            lab.setObjectName("featureLevelLabel")
            c = IND2 if st == "now" else TEXT3
            lab.setStyleSheet(f"color:{c};font-size:{FS_TINY}px;font-weight:800;letter-spacing:1px;"
                              f"background:transparent;margin-top:8px;")
            body.addWidget(lab)
        mine = []
        for card in row["cards"]:
            fc = FeatureCard(card)
            body.addWidget(fc)
            mine.append(fc)
        cards_out.extend(mine)
        hl.addLayout(body, 1)
        return w, mine

    def _rebuild_features(self):
        from dnd_app.core.feature_page import feature_page
        lay = self._feat_tab_lay
        # the cards left open stay open
        for card, *_ in getattr(self, "_feat_cards", []):
            try:
                if card.is_open():
                    self._feat_open.add(card.card["id"])
                else:
                    self._feat_open.discard(card.card["id"])
            except RuntimeError:
                pass
        while lay.count():
            item = lay.takeAt(0)
            old = item.widget()
            if old is not None:
                # (detached first: deleteLater alone leaves it drawn, under
                # the new ones, until the event loop comes round)
                old.setParent(None); old.deleteLater()
        self._feat_cards = []
        self._feat_secs = []
        self._feat_extras = []
        self._feat_none = _lbl("", TEXT3, FS_BODY, align=Qt.AlignCenter)
        self._feat_none.setVisible(False)
        lay.addWidget(self._feat_none)

        sections = feature_page(self.char)
        chips = []
        for sec in sections:
            if sec["chip"] not in chips:
                chips.append(sec["chip"])
            box = QWidget(); box.setObjectName(f"featureGroup_{sec['key']}")
            box.setStyleSheet("background:transparent;")
            bl = QVBoxLayout(box); bl.setContentsMargins(0, 6, 0, 0); bl.setSpacing(6)
            body = QWidget(); body.setStyleSheet("background:transparent;")
            bdl = QVBoxLayout(body); bdl.setContentsMargins(0, 0, 0, 0); bdl.setSpacing(6)
            bl.addWidget(self._feature_section_head(sec, body))
            bl.addWidget(body)
            rows, cards = [], []
            if sec["rail"]:
                for row in sec["levels"]:
                    w, mine = self._feature_rail_row(row, cards)
                    bdl.addWidget(w)
                    rows.append((w, mine))
            else:
                for card in sec["cards"]:
                    fc = FeatureCard(card)
                    bdl.addWidget(fc)
                    cards.append(fc)
            for fc in cards:
                if fc.card["id"] in self._feat_open:
                    fc.set_open(True)
                self._feat_cards.append((fc, sec["chip"]))
            self._feat_secs.append((box, sec["chip"], rows, cards))
            lay.addWidget(box)
            if sec.get("table"):
                tbl = self._add_wild_magic_section(barb=sec["table"] == "barbarian")
                tbl.setProperty("featureChip", sec["chip"])
                bdl.addWidget(tbl)
        self._make_feature_chips(chips)
        self._add_dm_browser(lay)
        lay.addStretch()
        self._apply_feature_filter()

    def _add_dm_browser(self, lay):
        """The DM's card at the foot of the page: give a feat, a gift or a
        character secret outside the levels (folded until it's wanted)."""
        from dnd_app.data.feats import ALL_FEATS, get_feat as _get_feat
        fb_card = QFrame()
        fb_card.setObjectName("dmBrowser")
        fb_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {qa(AMBER,0x44)};border-radius:10px;}}")
        fb_cl = QVBoxLayout(fb_card)
        fb_cl.setContentsMargins(12, 10, 12, 10); fb_cl.setSpacing(6)

        # Header row
        fb_hdr = QHBoxLayout()
        fb_hdr.addWidget(_lbl("A feat, a gift or a secret the DM hands out, outside the levels. "
                              "Double-click one, or choose it and Give it.", TEXT2, FS_SMALL, wrap=True))
        fb_cl.addLayout(fb_hdr)

        # Search + list row
        fb_body = QHBoxLayout(); fb_body.setSpacing(8)

        # Left: search + category filter + list
        # (in a widget of its own so the filter sidebar slides over the
        # list, not over the preview beside it)
        fb_left_w = QWidget(); fb_left = QVBoxLayout(fb_left_w)
        fb_left.setContentsMargins(0, 0, 0, 0); fb_left.setSpacing(4)
        fb_search = QLineEdit(); fb_search.setPlaceholderText("Search feats…")
        fb_search.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;font-size:{FS_SMALL}px;}}"
            f"QLineEdit:focus{{border-color:{AMBER};}}")
        from dnd_app.data.dm_rewards import DM_REWARD_CATEGORIES
        fb_type_filter = QComboBox()
        fb_type_filter.addItems(DM_REWARD_CATEGORIES)
        fb_type_filter.setStyleSheet(
            f"QComboBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;font-size:{FS_SMALL}px;}}")
        fb_type_filter.setToolTip("Filter by feature type")
        # search across the row; the type filter in the funnel's sidebar
        fb_filters = FilterSidebar(fb_left_w)
        fb_filters.add_combo("Feature type", fb_type_filter)
        fb_left.addLayout(fb_filters.search_row(fb_search))

        fb_list = QListWidget()
        fb_list.setMaximumHeight(200)
        fb_list.setStyleSheet(
            f"QListWidget{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;"
            f"color:{TEXT};font-size:{FS_SMALL}px;}}"
            f"QListWidget::item{{padding:3px 8px;}}"
            f"QListWidget::item:selected{{background:{qa(AMBER,0x88)};color:{on_fill(tint(SURF2, AMBER, 0x88))};}}"
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
                f"<b>{ft['name']}</b>" + (f"  [{source}]" if source else "")
                + (f"<br><i>Requires: {prereq}</i>" if prereq else "")
                + (f"<br>{desc}" if desc else ""))
            if already:
                item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(AMBER))
            fb_list.addItem(item)

        # DM Rewards ("Character Secrets" / narrative bonus features) — same
        # list, distinguished by a crystal-ball icon and the second data role, since
        # these are a genuinely different kind of content (mostly narrative
        # hooks with occasional mechanical traits) than standard feats.
        from dnd_app.data.dm_rewards import ALL_DM_REWARDS
        for rw in ALL_DM_REWARDS:
            already_rw = rw["name"] in self.char.get("dm_rewards", [])
            item = QListWidgetItem(("✓ " if already_rw else "") + rw["name"])
            item.setIcon(_icons.icon("orb"))
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
        fb_body.addWidget(fb_left_w, 3)

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
                    f"<b>{fname}</b>" + (f"  <i>[{src_tag}]</i>" if src_tag else "")
                    + (f"<br><span style='color:{AMBER};'>Requires: {pre}</span>" if pre else "")
                    + f"<br><br>{self._format_multi_para(full_desc)}")
        fb_list.currentItemChanged.connect(lambda cur,prev: _on_feat_select(cur))

        btn_add = _btn("＋  Give it", AMBER, variant="danger", border_width=1,
                        font_size=FS_SMALL, padding="6px 12px")
        btn_rem = _btn("Remove", CRIMSON, variant="danger", border_width=1,
                        bg_alpha=0x22, border_alpha=0x55, text_color=CRIM2,
                        hover_text="white", font_size=FS_SMALL, padding="6px 12px")
        _icons.set_button_icon(btn_rem, "trash", 15, color=CRIM2)

        def _grant_feat(lst=fb_list):
            item = lst.currentItem()
            if not item: return
            fname = item.data(Qt.UserRole) or item.text().lstrip("✓ ")
            item_type = item.data(Qt.UserRole + 1) or "feat"
            field = "dm_rewards" if item_type == "dm_reward" else "dm_feats"
            granted_list = self.char.setdefault(field, [])
            if item_type != "dm_reward" and fname in self.char.get("feats", []) and fname not in granted_list:
                self._toast(f"{fname} is already one of your feats")
                return
            if fname not in granted_list:
                granted_list.append(fname)
                # the feat's rules, spells and free casts (core/builder.py
                # rebuild); what it asks waits on the Choices tab
                self.ctrl.refresh()
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
                if item_type == "dm_reward":
                    granted_list.remove(fname)
                else:
                    from dnd_app.core.builder import revoke_dm_feat
                    revoke_dm_feat(self.char, fname)     # and everything it gave
                self.ctrl.refresh()
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
        box = QWidget(); box.setObjectName("featureGroup_dm"); box.setStyleSheet("background:transparent;")
        bxl = QVBoxLayout(box); bxl.setContentsMargins(0, 10, 0, 0); bxl.setSpacing(6)
        bxl.addWidget(self._feature_section_head(
            {"key": "dm", "title": "From the DM", "sub": "give a feat, a gift or a secret", "count": None}, fb_card))
        bxl.addWidget(fb_card)
        lay.addWidget(box)
        self._dm_browser_card = fb_card
        self._feat_extras.append(box)

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
        an HTML-rendered popup. Handles two things Qt's HTML rendering
        won't do on its own: (1) the source text has real '\\n\\n'
        paragraph breaks, but plain newlines are silently collapsed,
        producing one unreadable wall of text; (2) each distinct
        ability starts with "Trait Name. description..." (markdown bold
        flattened to plain text during parsing) — these are re-bolded
        so each ability reads as its own clearly separated block
        instead of blending into running prose."""
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


    def _add_wild_magic_section(self, barb: bool = False):
        from dnd_app.data.classes import WILD_MAGIC_SURGE_TABLE, WILD_MAGIC_BARBARIAN_TABLE
        # Determine which table to use: Barbarian=d8, Sorcerer=d100
        is_barb_wm = barb
        if is_barb_wm:
            table_data = [(i+1, i+1, eff) for i, (_, eff) in enumerate(WILD_MAGIC_BARBARIAN_TABLE)]
            title = "Wild Magic Surge Table  (Barbarian — roll d8 when you enter your rage)"
            die_label = "Roll Wild Magic Surge (d8)"
            die_max = 8
        else:
            table_data = WILD_MAGIC_SURGE_TABLE
            title = "Wild Magic Surge Table  (Sorcerer — roll d100 after casting a spell)"
            die_label = "Roll Wild Magic Surge (d100)"
            die_max = 100

        grp = QGroupBox(title)
        grp.setStyleSheet(f"QGroupBox{{background:{SURF};border:1px solid {qa(PURP2,0x55)};border-radius:10px;margin-top:16px;padding:10px;}}QGroupBox::title{{left:12px;top:0;background:{SURF};color:{PURP2};font-size:{FS_SMALL}px;font-weight:700;padding:0 6px;}}")
        gl = QVBoxLayout(grp)
        roll_row = QHBoxLayout()
        roll_btn = pill_btn(die_label, PURPLE, hover=PURP2)
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
        self._feat_extras.append(grp)
        return grp

    # ══ TAB 6: TRAITS & NOTES ══════════════════════════════════════════════════
