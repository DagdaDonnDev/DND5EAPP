"""Starting Equipment step of the touch wizard -- QML-facing bridge
mirroring ui_desktop's Step5Equipment. Each starting-equipment "group"
for the character's class (from get_starting_equipment()) is either a
single fixed grant, or a choice between 2+ options; either kind can
contain "Any X" placeholders (e.g. "Any martial weapon") that need a
concrete pick from that category's weapon/tool pool.
"""
from PySide6.QtCore import QObject, Signal, Slot, Property

from dnd_app.data.phbCommon.backgrounds import get_background
from dnd_app.data.phbCommon.starting_equipment import get_starting_equipment
from dnd_app.data.phbCommon.items import (
    ARMOR, ALL_WEAPONS, WEAPON_DICT, EQUIPMENT_PACKS, weapon_category_pool,
)
from dnd_app.core.builder import rebuild

_ARMOR_DICT = {a[0]: a for a in ARMOR}
_ARMOR_NAMES = set(_ARMOR_DICT)
_WEAPON_NAMES = {w[0] for w in ALL_WEAPONS}


def _is_placeholder(item: str) -> bool:
    return item.lower().startswith("any ")


class EquipmentWizardBridge(QObject):
    groupsChanged = Signal()
    backgroundGearChanged = Signal()
    notesChanged = Signal()
    equipmentConfirmed = Signal()

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self._class_name = ""
        self._groups = []          # raw get_starting_equipment() output
        self._selected_option = {}  # group_index -> option_index
        self._picks = {}           # (group_index, option_index, item_index) -> weapon/tool name
        self._notes = char.get("notes", "")
        self._confirmed_once = False
        self._last_class = None

    # ── Refresh (call when the screen becomes visible) ────────────────
    @Slot()
    def refresh(self):
        """Rebuild the class-specific equipment groups. The player may
        have just picked (or changed) their class on the Class screen
        since this bridge was last shown -- same drawer-nav concern as
        the other wizard steps' refresh()."""
        classes = self.char.get("classes") or []
        cls_name = classes[0]["class"] if classes else ""
        if cls_name != self._last_class:
            self._class_name = cls_name
            self._groups = get_starting_equipment(cls_name)
            self._selected_option = {}
            self._picks = {}
            self._last_class = cls_name
        # Re-derived from the dict for the same New Character reason as
        # ClassWizardBridge.refresh().
        self._confirmed_once = bool(self.char.get("character_created"))
        self.groupsChanged.emit()
        self.backgroundGearChanged.emit()
        self.equipmentConfirmed.emit()

    @Property(str, notify=groupsChanged)
    def className(self):
        return self._class_name

    # ── Equipment choice groups ───────────────────────────────────────
    def _option_view(self, gi: int, oi: int, opt: list, letter: str) -> dict:
        parts = []
        for ii, item in enumerate(opt):
            if _is_placeholder(item):
                key = (gi, oi, ii)
                pool = weapon_category_pool(item)
                value = self._picks.get(key) or (pool[0] if pool else "")
                parts.append({
                    "kind": "combo", "label": item, "pool": pool,
                    "value": value, "itemIndex": ii,
                })
            else:
                parts.append({"kind": "text", "label": item, "itemIndex": ii})
        return {"index": oi, "letter": letter, "parts": parts}

    @Property(list, notify=groupsChanged)
    def groups(self):
        out = []
        for gi, group in enumerate(self._groups):
            options = group["options"]
            has_choice = len(options) > 1
            letters = "abcdefg"
            opt_views = [
                self._option_view(gi, oi, opt, letters[oi] if has_choice else "")
                for oi, opt in enumerate(options)
            ]
            out.append({
                "index": gi,
                "hasChoice": has_choice,
                "options": opt_views,
                "selectedOption": self._selected_option.get(gi, 0),
            })
        return out

    @Slot(int, int)
    def selectOption(self, group_index: int, option_index: int):
        if self._selected_option.get(group_index, 0) == option_index:
            return
        self._selected_option[group_index] = option_index
        self.groupsChanged.emit()

    @Slot(int, int, int, str)
    def setPlaceholderPick(self, group_index: int, option_index: int, item_index: int, name: str):
        key = (group_index, option_index, item_index)
        if self._picks.get(key) == name:
            return
        self._picks[key] = name
        self.groupsChanged.emit()

    # ── Background gear note ──────────────────────────────────────────
    @Property(str, notify=backgroundGearChanged)
    def backgroundGearText(self):
        bg = get_background(self.char.get("background", ""))
        if not bg:
            return ""
        gear = bg.get("equipment", "")
        return str(gear)[:300] if gear else "Standard adventuring gear"

    # ── Notes ──────────────────────────────────────────────────────────
    @Property(str, notify=notesChanged)
    def notes(self):
        return self._notes

    @Slot(str)
    def setNotes(self, value: str):
        if value == self._notes:
            return
        self._notes = value
        self.notesChanged.emit()

    @Property(bool, notify=equipmentConfirmed)
    def equipmentConfirmedOnce(self):
        return self._confirmed_once

    # ── Commit into the character dict (mirrors Step5Equipment.collect()) ──
    @Slot(result=bool)
    def confirmEquipment(self) -> bool:
        # Last line of defense against marking a character finished with
        # earlier steps never confirmed (see ClassWizardBridge.refresh()).
        if not (self.char.get("race") and self.char.get("classes")
                and self.char.get("name")):
            return False
        chosen_items = []
        for gi, group in enumerate(self._groups):
            options = group["options"]
            oi = self._selected_option.get(gi, 0)
            opt = options[oi]
            for ii, item in enumerate(opt):
                if _is_placeholder(item):
                    key = (gi, oi, ii)
                    pool = weapon_category_pool(item)
                    chosen_items.append(self._picks.get(key) or (pool[0] if pool else ""))
                else:
                    chosen_items.append(item)

        char = self.char
        char["armor_worn"] = "No Armor"
        char["shield"] = False
        char["equipped_weapons"] = []
        char["equipment"] = []
        for item in chosen_items:
            base = item.split(" (")[0].strip()
            if base == "Shield":
                char["shield"] = True
                a = _ARMOR_DICT.get("Shield")
                char["equipment"].append({"name": "Shield", "qty": 1,
                                           "weight": a[6] if a else 6, "cost": a[7] if a else 10})
            elif base in _ARMOR_NAMES:
                char["armor_worn"] = base
                a = _ARMOR_DICT.get(base)
                char["equipment"].append({"name": base, "qty": 1,
                                           "weight": a[6] if a else 0, "cost": a[7] if a else 0})
            elif base in _WEAPON_NAMES:
                char["equipped_weapons"].append(base)
                w = WEAPON_DICT.get(base, {})
                char["equipment"].append({"name": base, "qty": 1,
                                           "weight": w.get("weight", 0), "cost": w.get("cost", 0)})
            elif base in EQUIPMENT_PACKS:
                for pack_item, qty in EQUIPMENT_PACKS[base]:
                    char["equipment"].append({"name": pack_item, "qty": qty, "weight": 0, "cost": 0})
            else:
                char["equipment"].append({"name": item, "qty": 1, "weight": 0, "cost": 0})

        bg = get_background(char.get("background", ""))
        bg_eq_text = (bg or {}).get("equipment", "")
        if bg_eq_text and char.get("background") != "Custom Background":
            import re
            parts, depth, current = [], 0, ""
            for ch in bg_eq_text:
                if ch == '(':
                    depth += 1; current += ch
                elif ch == ')':
                    depth -= 1; current += ch
                elif ch == ',' and depth == 0:
                    parts.append(current.strip()); current = ""
                else:
                    current += ch
            if current.strip():
                parts.append(current.strip())
            for p in parts:
                m = re.match(r'^(\d+)\s*(gp|sp|cp|ep|pp)$', p, re.IGNORECASE)
                if m:
                    cur = char.setdefault("currency", {})
                    denom = m.group(2).upper()
                    cur[denom] = cur.get(denom, 0) + int(m.group(1))
                elif p:
                    char["equipment"].append({"name": p, "qty": 1, "weight": 0, "cost": 0})

        if self._notes:
            char["notes"] = self._notes

        # Same as every other wizard step -- armor/weapon proficiencies
        # granted by class/race feed into AC/attack calculations via
        # rebuild(), and armor_worn set above needs it to actually
        # affect get_ac().
        rebuild(char)
        # Marks the character as finished -- this is the last wizard
        # step, and App.qml's drawer switches from wizard-step nav to
        # sheet nav based on this field (CharacterSheetBridge.hasCharacter).
        # A plain (non-underscore) key so it survives save/load like any
        # other real character data, unlike char["_choices"]-style
        # runtime-only fields most of which get stripped on save.
        char["character_created"] = True
        self._confirmed_once = True
        self.equipmentConfirmed.emit()
        return True
