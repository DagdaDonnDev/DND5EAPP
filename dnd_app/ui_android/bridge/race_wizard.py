"""Race step of the touch wizard -- QML-facing bridge over
dnd_app.data.phb2014.races. Mirrors what ui_desktop's Step1Race
reads/writes on the character dict (see collect()/populate() there),
so a character built through either UI ends up with the same shape.
"""
from PySide6.QtCore import QObject, QAbstractListModel, QModelIndex, Qt, Signal, Slot, Property

from dnd_app.data.phb2014.races import (
    RACE_NAMES, RACE_DICT, DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE, flex_asi_desc,
)
from dnd_app.core.builder import rebuild

ELADRIN_SEASONS = [
    ("Autumn", "charm one creature within 5 ft of your destination"),
    ("Winter", "frighten one creature within 5 ft of your destination"),
    ("Spring", "a willing creature within 5 ft can teleport with you"),
    ("Summer", "2d6 fire damage to each creature within 5 ft of your origin"),
]

SIMIC_ENHANCEMENTS = [
    ("Manta Glide", "slow falls: subtract 100 ft from fall damage, glide 2 ft horizontal per 1 ft descended"),
    ("Nimble Climber", "climbing speed = walking speed"),
    ("Underwater Adaptation", "breathe air and water, swim speed = walking speed"),
]


class RaceListModel(QAbstractListModel):
    """Searchable list of race names for a QML ListView."""
    NameRole = Qt.UserRole + 1
    SourceRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all = list(RACE_NAMES)
        self._filtered = list(RACE_NAMES)

    def roleNames(self):
        return {self.NameRole: b"name", self.SourceRole: b"source"}

    def rowCount(self, parent=QModelIndex()):
        return len(self._filtered)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._filtered)):
            return None
        name = self._filtered[index.row()]
        if role in (self.NameRole, Qt.DisplayRole):
            return name
        if role == self.SourceRole:
            return RACE_DICT.get(name, {}).get("source", "PHB")
        return None

    @Slot(str)
    def setFilter(self, text: str):
        self.beginResetModel()
        needle = text.strip().lower()
        self._filtered = [n for n in self._all if needle in n.lower()] if needle else list(self._all)
        self.endResetModel()


class RaceWizardBridge(QObject):
    """Selection state + derived display text for the Race screen, and
    the final commit into the character dict (confirmRace)."""

    selectedRaceChanged = Signal()
    raceDetailChanged = Signal()
    raceConfirmed = Signal()

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self._race_model = RaceListModel(self)
        self._selected_race = ""
        self._selected_subrace = ""      # clean name, e.g. "Hill" -- not the full "(None)"/parenthetical text
        self._selected_ancestry = ""
        self._selected_season = ""
        self._selected_simic = ""

    @Slot()
    def refresh(self):
        """Re-sync selection state from the character dict. Needed both
        for the drawer-nav revisit case the other wizard bridges'
        refresh() already handle, and for a character just loaded via
        Save/Load, which mutates the shared char dict in place without
        going through selectRace()/selectSubrace()/etc."""
        self._selected_race = self.char.get("race", "")
        self._selected_subrace = self.char.get("subrace", "")
        self._selected_ancestry = self.char.get("draconic_ancestry", "")
        self._selected_season = self.char.get("eladrin_season", "")
        self._selected_simic = self.char.get("simic_enhancement_1st", "")
        self.selectedRaceChanged.emit()
        self.raceDetailChanged.emit()

    @Property(bool, notify=raceConfirmed)
    def raceConfirmedOnce(self):
        """Whether a race has actually been committed to the character
        dict, as distinct from selectedRace (which changes as the
        player merely browses the list before confirming)."""
        return bool(self.char.get("race"))

    # ── QML-exposed models/constants ────────────────────────────────
    @Property(QObject, constant=True)
    def raceModel(self):
        return self._race_model

    @Property(list, constant=True)
    def eladrinSeasons(self):
        return [f"{name} – {desc}" for name, desc in ELADRIN_SEASONS]

    @Property(list, constant=True)
    def simicEnhancements(self):
        return [f"{name} – {desc}" for name, desc in SIMIC_ENHANCEMENTS]

    # ── Selection ────────────────────────────────────────────────────
    @Property(str, notify=selectedRaceChanged)
    def selectedRace(self):
        return self._selected_race

    @Slot(str)
    def selectRace(self, name: str):
        if name == self._selected_race:
            return
        self._selected_race = name
        self._selected_subrace = ""
        self._selected_ancestry = ""
        self._selected_season = ""
        self._selected_simic = ""
        self.selectedRaceChanged.emit()
        self.raceDetailChanged.emit()

    @Slot(str)
    def selectSubrace(self, clean_name: str):
        self._selected_subrace = clean_name
        self._selected_ancestry = ""
        self._selected_season = ""
        self.raceDetailChanged.emit()

    @Slot(str)
    def selectAncestry(self, ancestry_name: str):
        self._selected_ancestry = ancestry_name
        self.raceDetailChanged.emit()

    @Slot(int)
    def selectSeasonIndex(self, idx: int):
        self._selected_season = ELADRIN_SEASONS[idx][0] if 0 <= idx < len(ELADRIN_SEASONS) else ""
        self.raceDetailChanged.emit()

    @Slot(int)
    def selectSimicIndex(self, idx: int):
        self._selected_simic = SIMIC_ENHANCEMENTS[idx][0] if 0 <= idx < len(SIMIC_ENHANCEMENTS) else ""
        self.raceDetailChanged.emit()

    # ── Derived display data for RaceDetailScreen.qml ──────────────
    def _rdata(self) -> dict:
        return RACE_DICT.get(self._selected_race, {})

    def _selected_subrace_full(self):
        """The subrace's full '(parenthetical)' entry from RACE_DICT,
        matching by its clean leading name (the same lookup ui_desktop's
        _update_subrace_detail does)."""
        for s in self._rdata().get("subraces", []):
            if s.split("(")[0].strip() == self._selected_subrace:
                return s
        return None

    @Property(str, notify=raceDetailChanged)
    def raceSource(self):
        return self._rdata().get("source", "PHB")

    @Property(str, notify=raceDetailChanged)
    def raceSpeedSize(self):
        rdata = self._rdata()
        return f"Speed: {rdata.get('speed', 30)} ft   Size: {rdata.get('size', 'Medium')}"

    @Property(str, notify=raceDetailChanged)
    def raceAsiText(self):
        rdata = self._rdata()
        sub_full = self._selected_subrace_full()
        if sub_full:
            paren = sub_full[sub_full.find("(") + 1: sub_full.rfind(")")]
            segments = [s.strip() for s in paren.split(";") if s.strip()]
            asi_desc = segments[0].lstrip("–").strip() if segments else ""
            if asi_desc:
                return f"ASI: {asi_desc}  (from {self._selected_subrace})"
        asi = rdata.get("asi", {})
        flex = rdata.get("asi_flex", 0)
        style = rdata.get("asi_flex_style", "distribute")
        parts = [f"{ab} +{v}" for ab, v in asi.items()]
        if flex:
            parts.append(flex_asi_desc(flex, style))
        if parts:
            return "ASI: " + ", ".join(parts)
        if rdata.get("subraces"):
            return "ASI: from subrace — pick one below"
        return "ASI: None"

    @Property(list, notify=raceDetailChanged)
    def raceTraits(self):
        rdata = self._rdata()
        base_traits = list(rdata.get("traits", []))
        sub_full = self._selected_subrace_full()
        if not sub_full:
            return base_traits
        paren = sub_full[sub_full.find("(") + 1: sub_full.rfind(")")]
        segments = [s.strip() for s in paren.split(";") if s.strip()]
        sub_traits = segments[1:]
        return base_traits + [f"[{self._selected_subrace}] {t}" for t in sub_traits]

    @Property(list, notify=raceDetailChanged)
    def subraceNames(self):
        """'(None)' first, then each subrace's clean display name --
        matches the desktop combo box's contents/order."""
        names = ["(None)"]
        for s in self._rdata().get("subraces", []):
            names.append(s.split("(")[0].strip())
        return names

    @Property(bool, notify=raceDetailChanged)
    def isDragonborn(self):
        return self._selected_race == "Dragonborn"

    @Property(list, notify=raceDetailChanged)
    def ancestryNames(self):
        if not self.isDragonborn:
            return []
        types = ANCESTRY_BY_SUBRACE.get(self._selected_subrace or "Standard", ANCESTRY_BY_SUBRACE["Standard"])
        out = []
        for anc in types:
            dmg, shape = DRACONIC_ANCESTRY[anc][0], DRACONIC_ANCESTRY[anc][1]
            out.append(f"{anc}  –  {dmg}, {shape}")
        return out

    @Property(bool, notify=raceDetailChanged)
    def isEladrin(self):
        return self._selected_subrace == "Eladrin"

    @Property(bool, notify=raceDetailChanged)
    def isSimicHybrid(self):
        return self._selected_race == "Simic Hybrid"

    # ── Commit into the character dict (mirrors Step1Race.collect()) ──
    @Slot(result=bool)
    def confirmRace(self) -> bool:
        if not self._selected_race:
            return False
        char = self.char
        char["race"] = self._selected_race
        char["species"] = self._selected_race
        char["subrace"] = self._selected_subrace
        char["draconic_ancestry"] = self._selected_ancestry if self.isDragonborn else ""
        char["eladrin_season"] = self._selected_season if self.isEladrin else ""
        char["simic_enhancement_1st"] = self._selected_simic if self.isSimicHybrid else ""
        rdata = self._rdata()
        char["species_traits"] = rdata.get("traits", [])
        char.setdefault("languages", ["Common"])
        for lang in rdata.get("languages", []):
            if lang not in char["languages"] and "your choice" not in lang.lower():
                char["languages"].append(lang)
        # Re-derive ability_bonuses/proficiencies/etc. from the new
        # race+traits, same as the desktop wizard calling this after
        # every step -- without it, ability_score()/get_ac()/etc. never
        # see this race's ASI or granted proficiencies at all.
        rebuild(char)
        self.raceConfirmed.emit()
        return True
