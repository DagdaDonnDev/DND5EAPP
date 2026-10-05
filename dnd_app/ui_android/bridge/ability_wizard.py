"""Ability Scores step of the touch wizard -- QML-facing bridge over
dnd_app.data.phb2014.races' racial ASI data. Mirrors what ui_desktop's
Step2Abilities reads/writes on the character dict (see collect()/
populate() there), so a character built through either UI ends up with
the same shape.
"""
from PySide6.QtCore import QObject, Signal, Slot, Property

from dnd_app.core.builder import ABILITIES, rebuild
from dnd_app.data.phb2014.races import RACE_DICT, flex_asi_desc, combined_racial_asi

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
        rdata = RACE_DICT.get(self.char.get("race", ""), {})
        flex = rdata.get("asi_flex", 0)
        style = rdata.get("asi_flex_style", "distribute")
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
