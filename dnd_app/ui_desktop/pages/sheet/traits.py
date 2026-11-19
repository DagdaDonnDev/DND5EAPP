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


class _PickRow(QFrame):
    """A suggestion's row: clicked to use it (a frame, so its words wrap)."""

    def __init__(self, text, on_click):
        super().__init__()
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Use this one")
        self._on_click = on_click

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.rect().contains(ev.position().toPoint()):
            self._on_click()

    def click(self):
        self._on_click()


class SuggestionPopup(QFrame):
    """A box's Suggestions: the background's table, each line clicked to
    use it, and a roll of its die at the bottom."""

    def __init__(self, parent, title: str, rows: list, die: int, on_pick):
        super().__init__(parent, Qt.Popup)
        self.setObjectName("suggestionPopup")
        self.setStyleSheet(f"QFrame#suggestionPopup{{background:{SURF2};border:1px solid {BORDER2};border-radius:10px;}}"
                           f"QLabel{{background:transparent;border:none;}}")
        self.setFixedWidth(470)
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(2)
        lay.addWidget(_lbl(title.upper(), GOLD2, FS_SMALL, bold=True))
        for i, text in enumerate(rows, 1):
            b = _PickRow(text, lambda tx=text: (self.close(), on_pick(tx)))
            b.setObjectName(f"suggestion_{i}")
            row = QHBoxLayout(b); row.setContentsMargins(8, 6, 8, 6); row.setSpacing(10)
            num = _lbl(str(i), TEXT3, FS_SMALL, bold=True, wrap=False); num.setFixedWidth(16)
            num.setAlignment(Qt.AlignRight | Qt.AlignTop)
            row.addWidget(num, 0, Qt.AlignTop)
            t = _lbl(text, TEXT, FS_SMALL); t.setWordWrap(True)
            row.addWidget(t, 1)
            b.setStyleSheet(f"QFrame#suggestion_{i}{{background:transparent;border:1px solid transparent;border-radius:6px;}}"
                            f"QFrame#suggestion_{i}:hover{{background:{qa(TEAL, 0x2a)};border-color:{qa(TEAL, 0x88)};}}")
            lay.addWidget(b)
        foot = QHBoxLayout(); foot.setContentsMargins(4, 6, 4, 0)
        roll = _btn(f"🎲 Roll a d{die}", TEAL, variant="chip", height=28, font_size=FS_SMALL,
                    padding="2px 12px", min_height0=True)
        roll.setObjectName("suggestionRoll")
        roll.clicked.connect(lambda: (self.close(), on_pick(None)))
        foot.addWidget(roll); foot.addStretch()
        foot.addWidget(_lbl("Click one to use it", TEXT3, FS_SMALL, wrap=False))
        lay.addLayout(foot)


class TraitsNotesMixin:
    """The Notes tab: a list of pages down the left -- Character and
    Backstory, then the player's own pages in groups to open and close
    (core/notes.py) -- and the page picked on the right."""

    _TRAIT_NAMES = (("traits", "Personality Traits", "personality_traits"), ("ideals", "Ideals", "ideals"),
                    ("bonds", "Bonds", "bonds"), ("flaws", "Flaws", "flaws"))

    def _build_tab_traits_notes(self):
        from dnd_app.core import notes as N
        tab = QWidget()
        root = QHBoxLayout(tab); root.setContentsMargins(16, 14, 16, 14); root.setSpacing(14)

        # ── the list of pages ──
        side = QFrame(); side.setObjectName("notesSide"); side.setFixedWidth(240)
        side.setStyleSheet(f"QFrame#notesSide{{background:{SURF};border:1px solid {BORDER};border-radius:10px;}}")
        sl = QVBoxLayout(side); sl.setContentsMargins(10, 12, 10, 10); sl.setSpacing(6)
        sl.addWidget(_lbl("NOTES", GOLD, FS_SMALL, bold=True))
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self._notes_list_host = QWidget(); self._notes_list_host.setObjectName("notesList")
        self._notes_list_host.setStyleSheet("QWidget#notesList{background:transparent;}")
        self._notes_list_host.setContextMenuPolicy(Qt.CustomContextMenu)
        self._notes_list_host.customContextMenuRequested.connect(self._notes_empty_menu)
        self._notes_list = QVBoxLayout(self._notes_list_host)
        self._notes_list.setContentsMargins(0, 0, 4, 0); self._notes_list.setSpacing(4)
        scroll.setWidget(self._notes_list_host)
        sl.addWidget(scroll, 1)
        sl.addWidget(_lbl("Drag a page onto a group to move it. Right-click a page or group for more, "
                          "or the space below for a new page or group.", TEXT3, FS_TINY))
        root.addWidget(side)

        # ── the page picked ──
        self._notes_stack = QStackedWidget()
        root.addWidget(self._notes_stack, 1)

        # Character: appearance and background, and the four boxes
        char_page = QFrame(); char_page.setObjectName("notesCharacter")
        char_page.setStyleSheet(f"QFrame#notesCharacter{{background:{SURF};border:1px solid {BORDER2};border-radius:10px;}}")
        grid = QGridLayout(char_page); grid.setContentsMargins(12, 12, 12, 12); grid.setSpacing(12)
        look = _card(); ll = QVBoxLayout(look); ll.setContentsMargins(12, 10, 12, 12); ll.setSpacing(8)
        ll.addWidget(_lbl("APPEARANCE", GOLD, FS_SMALL, bold=True))
        self._appearance_edit = QTextEdit()
        self._appearance_edit.setPlaceholderText("Age, height, build, eyes, notable features…")
        self._appearance_edit.setAcceptRichText(False)
        ll.addWidget(self._appearance_edit, 1)
        ll.addWidget(_lbl("BACKGROUND", GOLD, FS_SMALL, bold=True))
        self._notes_bg_lbl = _lbl("", TEXT, FS_BODY)
        self._notes_bg_lbl.setStyleSheet(self._notes_bg_lbl.styleSheet() +
                                         f"background:{SURF2};border:1px solid {BORDER};border-radius:6px;padding:6px 10px;")
        ll.addWidget(self._notes_bg_lbl)
        grid.addWidget(look, 0, 0, 2, 1)
        self._trait_edits, self._trait_btns = {}, {}
        for n, (kind, label, key) in enumerate(self._TRAIT_NAMES):
            card = _card(); cl = QVBoxLayout(card); cl.setContentsMargins(12, 10, 12, 10); cl.setSpacing(8)
            cl.addWidget(_lbl(label.upper(), GOLD, FS_SMALL, bold=True))
            ed = QTextEdit(); ed.setAcceptRichText(False)
            ed.setObjectName(f"trait_{kind}")
            self._trait_edits[key] = ed
            cl.addWidget(ed, 1)
            row = QHBoxLayout(); row.setSpacing(6); row.addStretch()
            sug = _btn("☰ Suggestions", INDIGO, variant="chip", height=28, font_size=FS_SMALL,
                       padding="2px 12px", min_height0=True)
            sug.setObjectName(f"suggest_{kind}")
            sug.clicked.connect(lambda checked=False, k=kind, b=sug: self._show_suggestions(k, b))
            roll = _btn(f"🎲 Roll d{N.DICE[kind]}", TEAL, variant="chip", height=28, font_size=FS_SMALL,
                        padding="2px 12px", min_height0=True)
            roll.setObjectName(f"roll_{kind}")
            roll.clicked.connect(lambda checked=False, k=kind: self._roll_suggestion(k))
            row.addWidget(sug); row.addWidget(roll)
            cl.addLayout(row)
            self._trait_btns[kind] = (sug, roll)
            grid.addWidget(card, n // 2, 1 + n % 2)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1); grid.setColumnStretch(2, 1)
        self._notes_stack.addWidget(char_page)

        # Backstory, and the player's pages (one editor, the page picked in it)
        def editor_page(name):
            f = QFrame(); f.setObjectName(name)
            f.setStyleSheet(f"QFrame#{name}{{background:{SURF};border:1px solid {BORDER2};border-radius:10px;}}")
            v = QVBoxLayout(f); v.setContentsMargins(14, 12, 14, 14); v.setSpacing(8)
            head = QHBoxLayout(); title = _lbl("", GOLD, FS_SMALL, bold=True, wrap=False)
            head.addWidget(title); head.addStretch()
            v.addLayout(head)
            ed = QTextEdit(); ed.setAcceptRichText(False)
            v.addWidget(ed, 1)
            return f, head, title, ed
        bf, _bh, bt, self._backstory_edit = editor_page("notesBackstory")
        bt.setText("BACKSTORY")
        self._backstory_edit.setPlaceholderText("Where they're from, who they've lost, who they owe…")
        self._notes_stack.addWidget(bf)
        pf, ph, self._notes_page_title, self._notes_page_edit = editor_page("notesPage")
        self._notes_page_edit.setPlaceholderText("Write anything here…")
        entry = _btn("+ New entry · today's date", TEAL, variant="chip", height=28, font_size=FS_SMALL,
                     padding="2px 12px", min_height0=True,
                     tooltip="A heading with today's date at the top, for this session's notes")
        entry.setObjectName("notesNewEntry")
        entry.clicked.connect(self._notes_new_entry)
        ph.addWidget(entry)
        self._notes_page_edit.textChanged.connect(self._on_notes_page_typed)
        self._notes_stack.addWidget(pf)

        # Live-sync the boxes into self.char as the player types
        self._notes_field_edits = dict(self._trait_edits, backstory=self._backstory_edit,
                                       appearance_notes=self._appearance_edit)
        for key, ed in self._notes_field_edits.items():
            ed.textChanged.connect(lambda k=key, e=ed: self._on_notes_field_changed(k, e))
        self._notes_sel = ("character", -1)
        self._rebuild_notes_list()
        self._refresh_notes_character()
        return tab

    def _on_notes_field_changed(self, key: str, edit) -> None:
        self.char[key] = edit.toPlainText()
        self._mark_dirty()

    # ── the list down the left ──────────────────────────────────────────
    def _notes_item(self, text, selected, on_click, menu=None, indent=0, count=""):
        b = QPushButton(); b.setCursor(Qt.PointingHandCursor)
        b.setObjectName("notesItem")
        lay = QHBoxLayout(b); lay.setContentsMargins(12 + indent, 0, 10, 0)
        t = _lbl(text, GOLD2 if selected else TEXT2, FS_BODY, bold=True, wrap=False)
        lay.addWidget(t, 1)
        if count:
            lay.addWidget(_lbl(count, TEXT3, FS_TINY, wrap=False))
        b.setFixedHeight(36)
        edge, fill = (GOLD, qa(GOLD, 0x1c)) if selected else (BORDER, SURF2)
        b.setStyleSheet(f"QPushButton{{background:{fill};border:1px solid {edge};border-radius:8px;"
                        f"min-height:34px;max-height:34px;padding:0;}}QPushButton:hover{{border-color:{GOLD};}}"
                        f"QLabel{{background:transparent;border:none;}}")
        b.clicked.connect(on_click)
        if menu:
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda pos, w=b: menu(w.mapToGlobal(pos)))
        return b

    def _rebuild_notes_list(self):
        from dnd_app.core import notes as N
        lay = self._notes_list
        while lay.count():
            it = lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        kind, idx = self._notes_sel
        lay.addWidget(self._notes_item("Character", kind == "character", lambda: self._open_notes("character")))
        lay.addWidget(self._notes_item("Backstory", kind == "backstory", lambda: self._open_notes("backstory")))
        for g in N.groups(self.char):
            head = QFrame(); head.setObjectName(f"notesGroup_{g['name']}")
            head.setStyleSheet("QFrame{background:transparent;border:none;}")
            head.setContextMenuPolicy(Qt.CustomContextMenu)
            head.customContextMenuRequested.connect(
                lambda pos, nm=g["name"], w=head: self._notes_group_menu(nm, w.mapToGlobal(pos)))
            hl = QHBoxLayout(head); hl.setContentsMargins(0, 8, 0, 0); hl.setSpacing(4)
            tog = QPushButton(("▾  " if g["open"] else "▸  ") + g["name"])
            tog.setObjectName("notesGroupToggle")
            tog.setCursor(Qt.PointingHandCursor)
            tog.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEAL2};font-size:{FS_SMALL}px;"
                              f"font-weight:800;text-align:left;padding:2px 2px;min-height:0px;}}"
                              f"QPushButton:hover{{color:{GOLD2};}}")
            tog.setToolTip("Open or close this group (right-click for more)")
            tog.clicked.connect(lambda checked=False, nm=g["name"]: self._toggle_notes_group(nm))
            tog.setContextMenuPolicy(Qt.CustomContextMenu)
            tog.customContextMenuRequested.connect(
                lambda pos, nm=g["name"], w=tog: self._notes_group_menu(nm, w.mapToGlobal(pos)))
            hl.addWidget(tog, 1)
            if not g["open"]:
                hl.addWidget(_lbl(str(len(g["pages"])), TEXT3, FS_TINY, wrap=False))
            # a page dragged onto the group goes in it
            from dnd_app.ui_desktop.widgets import accept_drop
            accept_drop(head, "notes-page", lambda t, nm=g["name"]: self._drop_notes_page(t, nm), TEAL)
            lay.addWidget(head)
            if g["open"]:
                from dnd_app.ui_desktop.widgets import drag_widget
                for i, page in g["pages"]:
                    item = self._notes_item(
                        page.get("title", "Notes"), kind == "page" and idx == i,
                        lambda checked=False, ii=i: self._open_notes("page", ii),
                        menu=lambda pos, ii=i: self._notes_page_menu(ii, pos), indent=6)
                    item.setObjectName(f"notesPage_{i}")
                    item.setToolTip("Drag onto another group to move it · right-click for more")
                    # dragged to another group; and one dropped on it joins its group
                    drag_widget(item, "notes-page", str(i))
                    accept_drop(item, "notes-page", lambda t, nm=g["name"]: self._drop_notes_page(t, nm), TEAL)
                    lay.addWidget(item)
        lay.addStretch(1)

    def _open_notes(self, kind, index=-1):
        self._notes_sel = (kind, index)
        if kind == "character":
            self._notes_stack.setCurrentIndex(0)
        elif kind == "backstory":
            self._notes_stack.setCurrentIndex(1)
        else:
            pages = self.char.get("notes_pages", [])
            if not (0 <= index < len(pages)):
                return self._open_notes("character")
            page = pages[index]
            self._notes_page_title.setText(page.get("title", "Notes").upper())
            self._notes_page_edit.blockSignals(True)
            self._notes_page_edit.setPlainText(page.get("text", ""))
            self._notes_page_edit.blockSignals(False)
            self._notes_stack.setCurrentIndex(2)
        # (after the click that called this has finished with its button)
        QTimer.singleShot(0, self, self._rebuild_notes_list)

    def _on_notes_page_typed(self):
        from dnd_app.core import notes as N
        kind, idx = self._notes_sel
        if kind == "page":
            N.set_page_text(self.char, idx, self._notes_page_edit.toPlainText())
            self._mark_dirty()

    def _notes_changed(self, open_page=None):
        self._mark_dirty()
        if open_page is not None:
            self._open_notes("page", open_page)
        else:
            kind, idx = self._notes_sel
            if kind == "page" and not (0 <= idx < len(self.char.get("notes_pages", []))):
                self._notes_sel = ("character", -1)
            self._open_notes(*self._notes_sel)

    # ── right-clicks: groups, pages, the empty space ────────────────────
    def _notes_empty_menu(self, pos):
        """Right-click the list's empty space: a new page or a new group."""
        from dnd_app.ui_desktop.widgets import exec_menu
        menu = QMenu(self)
        page = menu.addAction("New page…")
        group = menu.addAction("New group…")
        act = exec_menu(menu, self._notes_list_host.mapToGlobal(pos))
        if act == page:
            self._add_notes_page()
        elif act == group:
            self._add_notes_group()

    def _drop_notes_page(self, text, group):
        from dnd_app.core import notes as N
        try:
            index = int(text)
        except ValueError:
            return
        pages = self.char.get("notes_pages", [])
        if not (0 <= index < len(pages)) or pages[index].get("group") == group:
            return
        # the open page stays open wherever it ends up (indexes shift)
        kind, idx = self._notes_sel
        open_page = pages[idx] if kind == "page" and 0 <= idx < len(pages) else None
        N.move_page(self.char, index, group)
        if open_page is not None:
            self._notes_sel = ("page", next(i for i, p in enumerate(self.char["notes_pages"]) if p is open_page))
        self._notes_changed()
        self._toast(f"Moved to {group}")

    def _notes_group_menu(self, name, global_pos):
        from dnd_app.ui_desktop.widgets import exec_menu
        menu = QMenu(self)
        new_page = menu.addAction("New page…")
        rename = menu.addAction("Rename group…")
        new_group = menu.addAction("New group…")
        menu.addSeparator()
        remove = menu.addAction(_icons.icon("trash"), "Remove group")
        act = exec_menu(menu, global_pos)
        if act == new_page:
            self._add_notes_page(name)
        elif act == rename:
            self._rename_notes_group(name)
        elif act == new_group:
            self._add_notes_group()
        elif act == remove:
            self._remove_notes_group(name)

    def _notes_page_menu(self, index, global_pos):
        from dnd_app.core import notes as N
        from dnd_app.ui_desktop.widgets import exec_menu
        menu = QMenu(self)
        rename = menu.addAction("Rename page…")
        here = self.char["notes_pages"][index].get("group")
        move = menu.addMenu("Move to")
        moves = {move.addAction(g["name"]): g["name"] for g in N.groups(self.char) if g["name"] != here}
        move.setEnabled(bool(moves))
        menu.addSeparator()
        remove = menu.addAction(_icons.icon("trash"), "Remove page")
        act = exec_menu(menu, global_pos)
        if act == rename:
            self._rename_notes_page(index)
        elif act == remove:
            self._remove_notes_page(index)
        elif act in moves:
            self._drop_notes_page(str(index), moves[act])

    def _add_notes_group(self):
        from dnd_app.core import notes as N
        name, ok = QInputDialog.getText(self, "New Group", "Group name (NPCs, Places, an arc…):")
        if not ok:
            return
        why = N.add_group(self.char, name)
        if why:
            self._toast(why); return
        self._notes_changed()

    def _rename_notes_group(self, old):
        from dnd_app.core import notes as N
        name, ok = QInputDialog.getText(self, "Rename Group", "Group name:", text=old)
        if not ok:
            return
        why = N.rename_group(self.char, old, name)
        if why:
            self._toast(why); return
        self._notes_changed()

    def _remove_notes_group(self, name):
        from dnd_app.core import notes as N
        pages = [p for p in self.char.get("notes_pages", []) if p.get("group") == name]
        msg = (f'Remove the group "{name}" and its {len(pages)} page{"s" if len(pages) != 1 else ""}, '
               f"with everything written on them? This can't be undone." if pages
               else f'Remove the empty group "{name}"?')
        if QMessageBox.question(self, "Remove Group", msg, QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        N.remove_group(self.char, name)
        self._notes_changed()

    def _add_notes_page(self, group=None) -> None:
        from dnd_app.core import notes as N
        gs = N.groups(self.char)
        group = group or (gs[0]["name"] if gs else None)
        if group is None:
            self._toast("Make a group first: right-click the space under the list"); return
        title, ok = QInputDialog.getText(self, "New Page", f"Page name (in {group}):")
        if not ok:
            return
        i = N.add_page(self.char, group, title)
        if i >= 0:
            self._notes_changed(i)

    def _remove_notes_page(self, index: int) -> None:
        from dnd_app.core import notes as N
        pages = self.char.get("notes_pages", [])
        if not (0 <= index < len(pages)):
            return
        title = pages[index].get("title", "this page")
        if QMessageBox.question(self, "Remove Page",
                                f'Remove "{title}" and everything written on it? This can\'t be undone.',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        N.remove_page(self.char, index)
        kind, idx = self._notes_sel
        if kind == "page":
            self._notes_sel = ("character", -1) if idx == index else ("page", idx - (idx > index))
        self._notes_changed()

    def _rename_notes_page(self, index: int) -> None:
        from dnd_app.core import notes as N
        pages = self.char.get("notes_pages", [])
        if not (0 <= index < len(pages)):
            return
        title, ok = QInputDialog.getText(self, "Rename Page", "Page name:", text=pages[index].get("title", ""))
        if ok:
            N.rename_page(self.char, index, title)
            self._notes_changed()

    def _toggle_notes_group(self, name):
        from dnd_app.core import notes as N
        N.toggle_group(self.char, name)
        self._mark_dirty()
        QTimer.singleShot(0, self, self._rebuild_notes_list)

    def _notes_new_entry(self):
        from dnd_app.core import notes as N
        kind, idx = self._notes_sel
        if kind != "page":
            return
        N.new_entry(self.char, idx)
        self._open_notes("page", idx)
        from PySide6.QtGui import QTextCursor
        cur = self._notes_page_edit.textCursor(); cur.movePosition(QTextCursor.Start)
        cur.movePosition(QTextCursor.Down); cur.movePosition(QTextCursor.Down)
        self._notes_page_edit.setTextCursor(cur); self._notes_page_edit.setFocus()
        self._mark_dirty()

    # ── the Character page: your background's suggestions ───────────────
    def _refresh_notes_character(self):
        from dnd_app.core import notes as N
        if not hasattr(self, "_trait_btns"):
            return
        bg = self.char.get("background", "") or "No background"
        sug = N.suggestions(self.char)
        for kind, label, _key in self._TRAIT_NAMES:
            rows = sug.get(kind) or []
            self._trait_edits[_key].setPlaceholderText(
                "Write your own, or pick a suggestion…" if rows else "Write your own…")
            for b in self._trait_btns[kind]:
                b.setEnabled(bool(rows))
                b.setToolTip("" if rows else f"The {bg} background's book has no {label.lower()} to suggest")
        from dnd_app.data.backgrounds import get_background
        info = get_background(self.char.get("background", "")) or {}
        skills = info.get("skill_profs") or info.get("skills") or []
        self._notes_bg_lbl.setText(bg + (f"  ·  {', '.join(skills)}" if skills else ""))

    def _show_suggestions(self, kind, button):
        from dnd_app.core import notes as N
        rows = N.suggestions(self.char).get(kind) or []
        if not rows:
            return
        label = dict((k, l) for k, l, _ in self._TRAIT_NAMES)[kind]
        bg = self.char.get("background", "")
        pop = SuggestionPopup(self, f"{bg} · {label} (d{len(rows)})", rows, len(rows),
                              lambda text, k=kind: self._use_suggestion(k, text))
        self._suggestion_popup = pop
        pop.adjustSize()
        pt = button.mapToGlobal(button.rect().bottomRight())
        scr = button.screen().availableGeometry() if button.screen() else None
        x, y = pt.x() - pop.width(), pt.y() + 4
        if scr is not None:
            if y + pop.height() > scr.bottom():
                y = button.mapToGlobal(button.rect().topRight()).y() - pop.height() - 4
            x = max(scr.left() + 4, x); y = max(scr.top() + 4, y)
        pop.move(x, y); pop.show()

    def _use_suggestion(self, kind, text):
        """A suggestion picked (or None: roll for one) into its box."""
        if text is None:
            return self._roll_suggestion(kind)
        from dnd_app.core import notes as N
        new = N.use_suggestion(self.char, kind, text)
        self._set_trait_box(kind, new)

    def _roll_suggestion(self, kind):
        from dnd_app.core import notes as N
        n, text = N.roll_suggestion(self.char, kind)
        if not n:
            return
        self._set_trait_box(kind, N.use_suggestion(self.char, kind, text))
        self._toast(f"🎲 Rolled a {n}: {text}")

    def _set_trait_box(self, kind, text):
        key = dict((k, f) for k, _l, f in self._TRAIT_NAMES)[kind]
        ed = self._trait_edits[key]
        ed.blockSignals(True); ed.setPlainText(text); ed.blockSignals(False)
        self.char[key] = text
        self._mark_dirty()

    # ════════════════════════════════════════════════════════════
    #  LOAD / REFRESH
    # ════════════════════════════════════════════════════════════
