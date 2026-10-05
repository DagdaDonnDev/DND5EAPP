"""Dice Roller bridge -- QML-facing equivalent of ui_desktop's
DiceRollerPanel. Stateless (no character dict needed), so it's reached
from the drawer's utility section rather than tied to any wizard step.

Simplified vs. desktop's dialog: no "roll against a character's
skill/save bonus" picker here (that needs the sheet's computed
bonuses wired in, a later increment) -- quick-roll, a custom N-dice
+ modifier roll, and Advantage/Disadvantage on a single d20, matching
the feature list in the project README.
"""
import random

from PySide6.QtCore import QObject, Signal, Slot, Property

_HISTORY_LIMIT = 20


def _sign(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


class DiceRollerBridge(QObject):
    resultChanged = Signal()
    historyChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = None
        self._detail = ""
        self._nat20 = False
        self._nat1 = False
        self._history = []   # [{"text": str, "crit": "nat20"|"nat1"|None}]

    def _set_result(self, total: int, detail: str, nat20: bool = False, nat1: bool = False):
        self._total = total
        self._detail = detail
        self._nat20 = nat20
        self._nat1 = nat1
        crit = "nat20" if nat20 else ("nat1" if nat1 else None)
        self._history.insert(0, {"text": f"{detail}  →  {total}", "crit": crit})
        del self._history[_HISTORY_LIMIT:]
        self.resultChanged.emit()
        self.historyChanged.emit()

    # ── Quick roll: a single die, no modifier ─────────────────────────
    @Slot(int)
    def quickRoll(self, sides: int):
        result = random.randint(1, sides)
        is_d20 = sides == 20
        self._set_result(result, f"1d{sides}",
                          nat20=(is_d20 and result == 20), nat1=(is_d20 and result == 1))

    # ── Custom roll: N dice of a chosen size + modifier, with
    # Advantage/Disadvantage only meaningful for a single d20 ─────────
    @Slot(int, int, int, str)
    def customRoll(self, count: int, sides: int, modifier: int, adv_mode: str):
        count = max(1, count)
        sides = max(2, sides)
        if adv_mode != "Normal" and count == 1 and sides == 20:
            rolls = [random.randint(1, 20), random.randint(1, 20)]
            roll = max(rolls) if adv_mode == "Advantage" else min(rolls)
            total = roll + modifier
            tag = "Adv" if adv_mode == "Advantage" else "Dis"
            detail = f"1d20 ({tag}: {rolls})" + (f" {_sign(modifier)}" if modifier else "")
            self._set_result(total, detail, nat20=(roll == 20), nat1=(roll == 1))
            return
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        detail = f"{count}d{sides}: {rolls}" + (f" {_sign(modifier)}" if modifier else "")
        single_d20 = count == 1 and sides == 20
        self._set_result(total, detail,
                          nat20=(single_d20 and rolls[0] == 20),
                          nat1=(single_d20 and rolls[0] == 1))

    @Property(str, notify=resultChanged)
    def totalText(self):
        return str(self._total) if self._total is not None else "—"

    @Property(str, notify=resultChanged)
    def detailText(self):
        return self._detail or "Pick a die below to get started."

    @Property(bool, notify=resultChanged)
    def isNat20(self):
        return self._nat20

    @Property(bool, notify=resultChanged)
    def isNat1(self):
        return self._nat1

    @Property(list, notify=historyChanged)
    def history(self):
        return list(self._history)

    @Slot()
    def clearHistory(self):
        self._history = []
        self.historyChanged.emit()
