"""The character creation wizard's bridges, one per step, in order --
the same steps as desktop's pages/wizard.py: race, ability scores,
background and class, starting equipment.
"""

from PySide6.QtCore import (
    QObject, QAbstractListModel, QModelIndex, Qt, Signal, Slot, Property,
)
from dnd_app.data.races import (
    RACE_NAMES, RACE_DICT, DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE, flex_asi_desc,
    combined_racial_asi,
)
from dnd_app.core.builder import rebuild, race_requires_subrace, ABILITIES
from dnd_app.data.backgrounds import BACKGROUND_NAMES, get_background
from dnd_app.data.classes import CLASS_NAMES, CLASS_DICT
from dnd_app.core.save_load import name_in_use, NAME_IN_USE_MESSAGE
from dnd_app.data.starting_equipment import get_starting_equipment
from dnd_app.data.items import (
    ARMOR, ALL_WEAPONS, WEAPON_DICT, EQUIPMENT_PACKS, weapon_category_pool,
)


# ═══════════════════════════════════════════════════════════════════════════
# Race step
# ═══════════════════════════════════════════════════════════════════════════
# Race step of the touch wizard -- QML-facing bridge over
# dnd_app.data.races. Mirrors what ui_desktop's Step1Race
# reads/writes on the character dict (see collect()/populate() there),
# so a character built through either UI ends up with the same shape.

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
        names = ["(Choose a subrace)" if self.subraceRequired else "(None)"]
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
    @Property(bool, notify=raceDetailChanged)
    def subraceRequired(self):
        return bool(self._selected_race) and race_requires_subrace(self._selected_race)

    @Property(str, notify=raceDetailChanged)
    def confirmBlockReason(self):
        if not self._selected_race:
            return "Choose a race first."
        if self.subraceRequired and not self._selected_subrace:
            return (f"Choose a subrace -- {'an' if self._selected_race[:1] in 'AEIOU' else 'a'} {self._selected_race}'s ability score "
                    f"bonus comes from its subrace.")
        return ""

    @Slot(result=bool)
    def confirmRace(self) -> bool:
        if self.confirmBlockReason:
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


# ═══════════════════════════════════════════════════════════════════════════
# Ability scores step
# ═══════════════════════════════════════════════════════════════════════════
# Ability Scores step of the touch wizard -- QML-facing bridge over
# dnd_app.data.races' racial ASI data. Mirrors what ui_desktop's
# Step2Abilities reads/writes on the character dict (see collect()/
# populate() there), so a character built through either UI ends up with
# the same shape.

METHOD_NAMES = [
    "Manual Entry",
    "Standard Array (15,14,13,12,10,8)",
    "Point Buy (27 points)",
    "Tasha's: Reassign Racial ASIs (keeps all racial traits)",
]
METHOD_MANUAL, METHOD_STANDARD_ARRAY, METHOD_POINT_BUY, METHOD_TASHAS = range(4)

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}


class AbilityWizardBridge(QObject):
    """Ability-score entry state + derived totals for the Abilities
    screen, and the final commit into the character dict
    (confirmAbilities, mirroring Step2Abilities.collect())."""

    methodChanged = Signal()
    scoresChanged = Signal()
    flexChanged = Signal()
    distChanged = Signal()
    tashasChanged = Signal()
    raceInfoChanged = Signal()
    errorChanged = Signal()
    abilitiesConfirmed = Signal()
    totalsChanged = Signal()   # fired alongside scores/flex/dist/raceInfo --
                               # totals depends on all four, and Property only
                               # accepts one notify signal

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self._method = METHOD_MANUAL
        self._base_scores = {ab: 10 for ab in ABILITIES}
        self._sa_assignment = {ab: STANDARD_ARRAY[i] for i, ab in enumerate(ABILITIES)}
        self._flex_picks = set()
        self._dist_option_a = True
        self._dist_plus2 = "STR"
        self._dist_plus1 = "DEX"
        self._dist_triple_picks = set()
        self._tashas_points = {ab: 0 for ab in ABILITIES}
        self._error = ""
        self._confirmed_once = False
        self._last_race_subrace = (None, None)

    @Slot()
    def resetToDefaults(self):
        """Start Menu's "New Character" action: refresh() only resyncs
        race-derived flex/dist state when the race changes, it doesn't
        touch the base-score entry fields themselves, so a fresh
        character would otherwise still show whatever the PREVIOUS
        character's player had typed in (this bridge is constructed
        once and reused for the app's lifetime, same as every other
        wizard bridge -- see main.py)."""
        self._method = METHOD_MANUAL
        self._base_scores = {ab: 10 for ab in ABILITIES}
        self._sa_assignment = {ab: STANDARD_ARRAY[i] for i, ab in enumerate(ABILITIES)}
        self._flex_picks = set()
        self._dist_option_a = True
        self._dist_plus2 = "STR"
        self._dist_plus1 = "DEX"
        self._dist_triple_picks = set()
        self._tashas_points = {ab: 0 for ab in ABILITIES}
        self._error = ""
        self._confirmed_once = False
        self._last_race_subrace = (None, None)
        self.methodChanged.emit()
        self.scoresChanged.emit()
        self.flexChanged.emit()
        self.distChanged.emit()
        self.tashasChanged.emit()
        self.raceInfoChanged.emit()
        self.errorChanged.emit()
        self.totalsChanged.emit()
        self.abilitiesConfirmed.emit()

    @Property(bool, notify=abilitiesConfirmed)
    def abilitiesConfirmedOnce(self):
        """Whether Confirm has actually succeeded this session, as
        distinct from char['abilities'] simply existing (new_character()
        always populates it with default 10s)."""
        return self._confirmed_once

    # ── Method selection ─────────────────────────────────────────────
    @Property(list, constant=True)
    def methodNames(self):
        return METHOD_NAMES

    @Property(int, notify=methodChanged)
    def methodIndex(self):
        return self._method

    @Slot(int)
    def selectMethodIndex(self, idx: int):
        if idx == self._method or not (0 <= idx < len(METHOD_NAMES)):
            return
        self._method = idx
        if idx == METHOD_STANDARD_ARRAY:
            for ab in ABILITIES:
                self._base_scores[ab] = self._sa_assignment[ab]
        if idx == METHOD_TASHAS:
            self._tashas_points = {ab: 0 for ab in ABILITIES}
        self.methodChanged.emit()
        self.scoresChanged.emit()
        self.tashasChanged.emit()
        self.totalsChanged.emit()

    @Property(bool, notify=methodChanged)
    def methodIsManual(self):
        return self._method == METHOD_MANUAL

    @Property(bool, notify=methodChanged)
    def methodIsStandardArray(self):
        return self._method == METHOD_STANDARD_ARRAY

    @Property(bool, notify=methodChanged)
    def methodIsPointBuy(self):
        return self._method == METHOD_POINT_BUY

    @Property(bool, notify=methodChanged)
    def methodIsTashas(self):
        return self._method == METHOD_TASHAS

    # ── Base ability scores (Manual + Point Buy share this pool, same
    # as ui_desktop's editable AbilityBlock widgets) ──────────────────
    @Property(list, constant=True)
    def abilityNames(self):
        return list(ABILITIES)

    @Property(dict, notify=scoresChanged)
    def baseScores(self):
        return dict(self._base_scores)

    @Slot(str, int)
    def setBaseScore(self, ab: str, value: int):
        if ab not in self._base_scores:
            return
        value = max(1, min(20, value))
        if self._base_scores[ab] == value:
            return
        self._base_scores[ab] = value
        self.scoresChanged.emit()
        self.totalsChanged.emit()

    @Property(int, notify=scoresChanged)
    def pointBuyRemaining(self):
        used = sum(POINT_BUY_COSTS.get(self._base_scores[ab], 99) for ab in ABILITIES)
        return 27 - used

    # ── Standard Array assignment ─────────────────────────────────────
    @Property(list, constant=True)
    def standardArrayValues(self):
        return list(STANDARD_ARRAY)

    @Property(dict, notify=scoresChanged)
    def standardArrayAssignment(self):
        return dict(self._sa_assignment)

    @Slot(str, int)
    def setStandardArrayValue(self, ab: str, value: int):
        if ab not in self._sa_assignment or value not in STANDARD_ARRAY:
            return
        self._sa_assignment[ab] = value
        if self._method == METHOD_STANDARD_ARRAY:
            self._base_scores[ab] = value
        self.scoresChanged.emit()
        self.totalsChanged.emit()

    # ── Racial ASI preview + flex/distribute pickers ──────────────────
    def _flex_info(self):
        from dnd_app.data.races import race_flex
        # none for a dragonmark: its mark sets the ability scores
        flex, style = race_flex(self.char.get("race", ""), self.char.get("subrace", ""))
        use_dist = flex == 2 and style == "distribute"
        return flex, style, use_dist

    @Slot()
    def refresh(self):
        """Re-sync race-derived state. Call when the Abilities screen
        becomes visible -- the player may have (re)confirmed a
        different race on the Race screen since this bridge was last
        shown, since navigation here is drawer-based, not a strict
        forward wizard."""
        race = self.char.get("race", "")
        subrace = self.char.get("subrace", "")
        key = (race, subrace)
        if key != self._last_race_subrace:
            self._flex_picks = set()
            self._dist_option_a = True
            self._dist_triple_picks = set()
            self._last_race_subrace = key
        self.raceInfoChanged.emit()
        self.flexChanged.emit()
        self.distChanged.emit()
        self.tashasChanged.emit()
        self.totalsChanged.emit()

    @Property(str, notify=raceInfoChanged)
    def racialAsiText(self):
        asi = combined_racial_asi(self.char)
        parts = [f"{ab} +{v}" for ab, v in sorted(asi.items())]
        flex, style, _ = self._flex_info()
        if flex:
            parts.append(flex_asi_desc(flex, style))
        if parts:
            return ", ".join(parts)
        subrace = self.char.get("subrace", "")
        if subrace:
            return f"Subrace: {subrace}"
        return "None"

    @Property(bool, notify=raceInfoChanged)
    def showFlexPicker(self):
        flex, _, use_dist = self._flex_info()
        return flex > 0 and not use_dist

    @Property(str, notify=raceInfoChanged)
    def flexLabel(self):
        flex, _, _ = self._flex_info()
        race = self.char.get("race", "")
        return f"Choose {flex} abilities to receive +1 (from {race}):"

    @Property(int, notify=raceInfoChanged)
    def flexCount(self):
        flex, _, use_dist = self._flex_info()
        return 0 if use_dist else flex

    @Property(list, notify=flexChanged)
    def flexPicks(self):
        return sorted(self._flex_picks)

    @Slot(str)
    def toggleFlexPick(self, ab: str):
        if ab not in ABILITIES:
            return
        if ab in self._flex_picks:
            self._flex_picks.discard(ab)
        elif len(self._flex_picks) < self.flexCount:
            self._flex_picks.add(ab)
        else:
            return
        self.flexChanged.emit()
        self.totalsChanged.emit()

    @Property(bool, notify=raceInfoChanged)
    def showDistPicker(self):
        _, _, use_dist = self._flex_info()
        return use_dist

    @Property(bool, notify=distChanged)
    def distOptionA(self):
        return self._dist_option_a

    @Slot(bool)
    def selectDistOptionA(self, is_a: bool):
        if is_a == self._dist_option_a:
            return
        self._dist_option_a = is_a
        self.distChanged.emit()
        self.totalsChanged.emit()

    @Property(str, notify=distChanged)
    def distPlus2Ability(self):
        return self._dist_plus2

    @Slot(str)
    def setDistPlus2(self, ab: str):
        if ab not in ABILITIES or ab == self._dist_plus2:
            return
        self._dist_plus2 = ab
        self.distChanged.emit()
        self.totalsChanged.emit()

    @Property(str, notify=distChanged)
    def distPlus1Ability(self):
        return self._dist_plus1

    @Slot(str)
    def setDistPlus1(self, ab: str):
        if ab not in ABILITIES or ab == self._dist_plus1:
            return
        self._dist_plus1 = ab
        self.distChanged.emit()
        self.totalsChanged.emit()

    @Property(list, notify=distChanged)
    def distTriplePicks(self):
        return sorted(self._dist_triple_picks)

    @Slot(str)
    def toggleDistTriplePick(self, ab: str):
        if ab not in ABILITIES:
            return
        if ab in self._dist_triple_picks:
            self._dist_triple_picks.discard(ab)
        elif len(self._dist_triple_picks) < 3:
            self._dist_triple_picks.add(ab)
        else:
            return
        self.distChanged.emit()
        self.totalsChanged.emit()

    # ── Tasha's Reassignment ───────────────────────────────────────────
    @Property(int, notify=raceInfoChanged)
    def tashasPool(self):
        return sum(combined_racial_asi(self.char).values())

    @Property(dict, notify=tashasChanged)
    def tashasPoints(self):
        return dict(self._tashas_points)

    @Slot(str, int)
    def setTashasPoints(self, ab: str, value: int):
        if ab not in self._tashas_points:
            return
        pool = self.tashasPool
        value = max(0, min(value, max(1, pool)))
        others = sum(v for a, v in self._tashas_points.items() if a != ab)
        if others + value > pool:
            value = max(0, pool - others)
        if self._tashas_points[ab] == value:
            return
        self._tashas_points[ab] = value
        self.tashasChanged.emit()

    @Property(int, notify=tashasChanged)
    def tashasUsed(self):
        return sum(self._tashas_points.values())

    # ── Live totals ──────────────────────────────────────────────────
    @Property(dict, notify=totalsChanged)
    def totals(self):
        """ab -> "TOTAL  (MOD)" display string for the current method
        and racial/flex/distribute picks, matching the desktop totals
        row."""
        bases = dict(self._sa_assignment) if self.methodIsStandardArray else dict(self._base_scores)
        racial = combined_racial_asi(self.char)
        flex_bonus = {ab: 1 for ab in self._flex_picks} if self.showFlexPicker else {}
        dist_bonus = {}
        if self.showDistPicker:
            if self._dist_option_a:
                if self._dist_plus2 != self._dist_plus1:
                    dist_bonus[self._dist_plus2] = dist_bonus.get(self._dist_plus2, 0) + 2
                    dist_bonus[self._dist_plus1] = dist_bonus.get(self._dist_plus1, 0) + 1
            else:
                for ab in self._dist_triple_picks:
                    dist_bonus[ab] = dist_bonus.get(ab, 0) + 1
        out = {}
        for ab in ABILITIES:
            total = bases.get(ab, 10) + racial.get(ab, 0) + flex_bonus.get(ab, 0) + dist_bonus.get(ab, 0)
            mod = (total - 10) // 2
            sign = f"+{mod}" if mod >= 0 else str(mod)
            out[ab] = f"{total}  ({sign})"
        return out

    # ── Errors surfaced to QML in place of a desktop QMessageBox ──────
    @Property(str, notify=errorChanged)
    def errorMessage(self):
        return self._error

    def _set_error(self, msg: str):
        self._error = msg
        self.errorChanged.emit()

    # ── Commit into the character dict (mirrors Step2Abilities.collect()) ──
    @Slot(result=bool)
    def confirmAbilities(self) -> bool:
        char = self.char
        if self.methodIsStandardArray:
            vals = list(self._sa_assignment.values())
            if sorted(vals) != sorted(STANDARD_ARRAY):
                self._set_error("Each standard array value must be used exactly once.")
                return False
            for ab in ABILITIES:
                char["abilities"][ab] = self._sa_assignment[ab]
        elif self.methodIsPointBuy:
            used = sum(POINT_BUY_COSTS.get(self._base_scores[ab], 99) for ab in ABILITIES)
            if used > 27:
                self._set_error(f"You've spent {used} points but only have 27.")
                return False
            for ab in ABILITIES:
                char["abilities"][ab] = self._base_scores[ab]
        elif self.methodIsTashas:
            for ab in ABILITIES:
                char["abilities"][ab] = self._base_scores[ab]
            pool = self.tashasPool
            used = self.tashasUsed
            if pool > 0 and used != pool:
                subrace = char.get("subrace", "")
                sub_note = f" ({subrace})" if subrace else ""
                self._set_error(
                    f"You must distribute all {pool} racial ASI point(s) "
                    f"from {char.get('race','')}{sub_note}. Currently placed: {used}")
                return False
            char.setdefault("_choices", {})["tashas_asi_reassign"] = {
                ab: v for ab, v in self._tashas_points.items() if v > 0
            }
        else:
            for ab in ABILITIES:
                char["abilities"][ab] = self._base_scores[ab]

        if self.showFlexPicker:
            needed = self.flexCount
            if needed > 0 and len(self._flex_picks) < needed:
                self._set_error(f"Please choose {needed} abilities to receive +1 (your race grants this).")
                return False
            for ab in self._flex_picks:
                char["abilities"][ab] = char["abilities"].get(ab, 10) + 1

        if self.showDistPicker:
            if self._dist_option_a:
                if self._dist_plus2 == self._dist_plus1:
                    self._set_error("The +2 and +1 must go to two different abilities.")
                    return False
                char["abilities"][self._dist_plus2] = char["abilities"].get(self._dist_plus2, 10) + 2
                char["abilities"][self._dist_plus1] = char["abilities"].get(self._dist_plus1, 10) + 1
            else:
                if len(self._dist_triple_picks) != 3:
                    self._set_error(
                        f"Please choose exactly 3 different abilities to receive +1 "
                        f"(currently {len(self._dist_triple_picks)} chosen).")
                    return False
                for ab in self._dist_triple_picks:
                    char["abilities"][ab] = char["abilities"].get(ab, 10) + 1

        self._set_error("")
        # Same as every other wizard step -- re-derive ability_bonuses/
        # AC/HP/etc. now that base scores + ASI picks are finalized.
        rebuild(char)
        self._confirmed_once = True
        self.abilitiesConfirmed.emit()
        return True


# ═══════════════════════════════════════════════════════════════════════════
# Background and class step
# ═══════════════════════════════════════════════════════════════════════════
# Background + Starting Class step of the touch wizard -- QML-facing
# bridge mirroring ui_desktop's Step3Class. At character-creation time
# this step is simpler than it sounds: no subclass or level-timeline
# picker here (those come later, at whatever level unlocks them, via the
# sheet's own level-up flow) -- just name, alignment, a searchable
# background choice (+ its optional feat), and a starting class.

ALIGNMENTS = [
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil", "Neutral Evil", "Chaotic Evil",
]


class BackgroundListModel(QAbstractListModel):
    """All 99 backgrounds, filterable by name -- same shape as
    RaceListModel so the two searchable pickers behave identically."""

    NameRole = Qt.UserRole + 1
    SourceRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all = list(BACKGROUND_NAMES)
        self._filtered = list(self._all)

    def roleNames(self):
        return {self.NameRole: b"name", self.SourceRole: b"source"}

    def rowCount(self, parent=QModelIndex()):
        return len(self._filtered)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        name = self._filtered[index.row()]
        if role == self.NameRole or role == Qt.DisplayRole:
            return name
        if role == self.SourceRole:
            return (get_background(name) or {}).get("source", "")
        return None

    @Slot(str)
    def setFilter(self, text: str):
        self.beginResetModel()
        t = text.lower().strip()
        self._filtered = [n for n in self._all if t in n.lower()] if t else list(self._all)
        self.endResetModel()


class ClassWizardBridge(QObject):
    nameChanged = Signal()
    alignmentChanged = Signal()
    backgroundChanged = Signal()
    classChanged = Signal()
    errorChanged = Signal()
    classConfirmed = Signal()

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self._name = char.get("name", "")
        self._alignment = char.get("alignment", "True Neutral")
        self._background = char.get("background", "")
        self._background_feat = (char.get("_choices") or {}).get("background_feat", "")
        classes = char.get("classes") or []
        self._class_name = classes[0]["class"] if classes else ""
        self._bg_model = BackgroundListModel()
        self._error = ""
        self._confirmed_once = False

    @Slot()
    def refresh(self):
        """Re-sync all fields from the character dict. Needed for the
        drawer-nav revisit case (consistent with the other wizard
        bridges' refresh()) and for a character just loaded via
        Save/Load, which mutates the shared char dict in place without
        going through setName()/selectBackground()/etc."""
        self._name = self.char.get("name", "")
        self._alignment = self.char.get("alignment", "True Neutral")
        self._background = self.char.get("background", "")
        self._background_feat = (self.char.get("_choices") or {}).get("background_feat", "")
        classes = self.char.get("classes") or []
        self._class_name = classes[0]["class"] if classes else ""
        # Re-derived from the dict (only confirmClass() writes "classes"),
        # same as raceConfirmedOnce -- otherwise it stays True from the
        # previous character after New Character, leaving the drawer's
        # Equipment step unlocked on a blank character.
        self._confirmed_once = bool(classes)
        self.nameChanged.emit()
        self.alignmentChanged.emit()
        self.backgroundChanged.emit()
        self.classChanged.emit()
        self.classConfirmed.emit()

    # ── Static lists ───────────────────────────────────────────────
    @Property(QObject, constant=True)
    def backgroundModel(self):
        return self._bg_model

    @Property(list, constant=True)
    def alignments(self):
        return list(ALIGNMENTS)

    @Property(list, constant=True)
    def classNames(self):
        return list(CLASS_NAMES)

    # ── Name / Alignment ─────────────────────────────────────────────
    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @Slot(str)
    def setName(self, value: str):
        if value == self._name:
            return
        self._name = value
        self.nameChanged.emit()

    @Property(bool, notify=nameChanged)
    def nameInUse(self):
        """Another saved character already has this name -- shown as a
        warning under the name field (confirmClass() refuses it too)."""
        return bool(self._name.strip()) and name_in_use(self._name)

    @Property(str, notify=alignmentChanged)
    def alignment(self):
        return self._alignment

    @Slot(str)
    def setAlignment(self, value: str):
        if value not in ALIGNMENTS or value == self._alignment:
            return
        self._alignment = value
        self.alignmentChanged.emit()

    # ── Background ─────────────────────────────────────────────────
    def _bg_data(self) -> dict:
        return get_background(self._background) or {}

    @Property(str, notify=backgroundChanged)
    def selectedBackground(self):
        return self._background

    @Slot(str)
    def selectBackground(self, name: str):
        if name == self._background:
            return
        self._background = name
        self._background_feat = ""
        self.backgroundChanged.emit()

    @Property(str, notify=backgroundChanged)
    def backgroundSkillsText(self):
        bg = self._bg_data()
        if not bg:
            return ""
        # with the ones to choose (the same text as desktop's)
        from dnd_app.data.backgrounds import background_proficiency_text
        return background_proficiency_text(bg)

    @Property(str, notify=backgroundChanged)
    def backgroundDetailText(self):
        bg = self._bg_data()
        if not bg:
            return ""
        feat = bg.get("feature", "")
        feat_desc = bg.get("feature_desc", "")
        feat_choices = bg.get("feat_choices") or []
        languages = bg.get("languages", 0)
        origin_feat = bg.get("origin_feat")
        equipment = bg.get("equipment", "")
        notes = bg.get("notes", "")
        source = bg.get("source", "")
        parts = []
        if feat:
            parts.append(f"◆ Feature: {feat}\n{feat_desc}" if feat_desc else f"◆ Feature: {feat}")
        if origin_feat:
            parts.append(f"◆ Origin Feat: {origin_feat}")
        if feat_choices:
            parts.append(f"◆ Feat (choose one): {', '.join(feat_choices)}")
        if languages:
            word = "language" if languages == 1 else "languages"
            parts.append(f"◆ Languages: {languages} {word} of your choice")
        if equipment:
            parts.append(f"◆ Equipment: {equipment}")
        if notes:
            parts.append(f"◆ Notes: {notes}")
        if source:
            parts.append(f"Source: {source}")
        return "\n\n".join(parts)

    @Property(list, notify=backgroundChanged)
    def backgroundFeatChoices(self):
        return list(self._bg_data().get("feat_choices") or [])

    @Property(bool, notify=backgroundChanged)
    def showBackgroundFeatPicker(self):
        return bool(self.backgroundFeatChoices)

    @Property(str, notify=backgroundChanged)
    def selectedBackgroundFeat(self):
        return self._background_feat

    @Slot(str)
    def selectBackgroundFeat(self, feat: str):
        if feat == self._background_feat:
            return
        self._background_feat = feat
        self.backgroundChanged.emit()

    # ── Starting Class ─────────────────────────────────────────────
    @Property(str, notify=classChanged)
    def selectedClass(self):
        return self._class_name

    @Slot(str)
    def selectClass(self, name: str):
        if name == self._class_name:
            return
        self._class_name = name
        self.classChanged.emit()

    @Property(str, notify=classChanged)
    def classInfoText(self):
        if not self._class_name:
            return ""
        cdata = CLASS_DICT.get(self._class_name, {})
        hd = cdata.get("hit_die", 8)
        saves = ", ".join(cdata.get("save_profs", []))
        return f"Hit Die: d{hd}  ·  Saving Throws: {saves}"

    # ── Errors / confirmation state ───────────────────────────────
    @Property(str, notify=errorChanged)
    def errorMessage(self):
        return self._error

    def _set_error(self, msg: str):
        self._error = msg
        self.errorChanged.emit()

    @Property(bool, notify=classConfirmed)
    def classConfirmedOnce(self):
        return self._confirmed_once

    # ── Commit into the character dict (mirrors Step3Class.collect()) ──
    @Slot(result=bool)
    def confirmClass(self) -> bool:
        name = self._name.strip()
        if not name:
            self._set_error("Please enter a character name.")
            return False
        if name_in_use(name):
            self._set_error(NAME_IN_USE_MESSAGE)
            return False
        if not self._background:
            self._set_error("Please choose a background.")
            return False
        if not self._class_name:
            self._set_error("Please choose a starting class.")
            return False

        char = self.char
        char["name"] = name
        char["alignment"] = self._alignment
        char["edition"] = "2014"
        char["background"] = self._background

        feat_choices = self._bg_data().get("feat_choices") or []
        if feat_choices:
            if not self._background_feat:
                self._set_error(
                    f"{self._background} grants a feat -- please choose one of: "
                    + ", ".join(feat_choices))
                return False
            if self._background_feat not in feat_choices:
                self._set_error(f"Choose one of: {', '.join(feat_choices)}")
                return False
            char.setdefault("_choices", {})["background_feat"] = self._background_feat
        elif isinstance(char.get("_choices"), dict):
            char["_choices"].pop("background_feat", None)

        cdata = CLASS_DICT.get(self._class_name, {})
        hd = cdata.get("hit_die", 8)
        char.setdefault("classes", [])
        if not char["classes"] or char["classes"][0]["class"] != self._class_name:
            char["classes"] = [{"class": self._class_name, "level": 1, "subclass": "", "hit_die": hd}]

        self._set_error("")
        # Same as every other wizard step -- re-derive ability_bonuses/
        # proficiencies/hit-die-driven max HP/etc. now that background
        # and class are finalized.
        rebuild(char)
        self._confirmed_once = True
        self.classConfirmed.emit()
        return True


# ═══════════════════════════════════════════════════════════════════════════
# Starting equipment step
# ═══════════════════════════════════════════════════════════════════════════
# Starting Equipment step of the touch wizard -- QML-facing bridge
# mirroring ui_desktop's Step5Equipment. Each starting-equipment "group"
# for the character's class (from get_starting_equipment()) is either a
# single fixed grant, or a choice between 2+ options; either kind can
# contain "Any X" placeholders (e.g. "Any martial weapon") that need a
# concrete pick from that category's weapon/tool pool.

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
