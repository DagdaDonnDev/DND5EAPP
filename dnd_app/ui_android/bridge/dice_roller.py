"""Dice Roller bridge -- the QML side of ui_desktop's DiceRollerPanel: a
dice tray (pick dice, add one of your bonuses, advantage or disadvantage
on a d20, roll) and the roll history -- every roll the sheet makes
(checks, saves, attacks, hit dice, what actions roll) and the tray's own,
kept with the character (core/roll_log.py). The rolling is core/dice.py's,
the same as desktop's.

The character is the app's shared one (main.py hands it in): replaced in
place when a save is opened, so this always has the open one. Before a
character exists (the start menu), the tray's rolls are kept for the
session only.
"""
from PySide6.QtCore import QObject, Signal, Slot, Property

from dnd_app.core import dice as _dice
from dnd_app.core import roll_log as _log

SHOWN = 60          # history rows shown (the character keeps more)


def _sign(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


class DiceRollerBridge(QObject):
    resultChanged = Signal()
    historyChanged = Signal()
    trayChanged = Signal()

    def __init__(self, char: dict = None, parent=None):
        super().__init__(parent)
        self._char = char
        self._session = {"roll_history": []}     # no character yet: kept for the session
        self._expr = ""
        self._mode = "normal"
        self._bonus = 0                          # an index into bonusOptions
        self._fresh = False                      # the next die starts a new roll
        self._total = None
        self._detail = ""
        self._nat = 0
        self._stop = _log.on_roll(self._on_logged)
        self.destroyed.connect(lambda *_: self._stop())

    # whose rolls these are: the open character, or the session's
    def _who(self) -> dict:
        c = self._char
        return c if isinstance(c, dict) and (c.get("character_created") or c.get("name")) else self._session

    def _on_logged(self, char, entry):
        if char is self._who():
            self.historyChanged.emit()

    # ── Your bonus ────────────────────────────────────────────────────
    def _bonuses(self) -> list:
        """[(label, name, bonus)]: none first, then the skills, saves and
        ability checks, as they are now."""
        out = [("No bonus", "", 0)]
        c = self._who()
        if c is self._session or not c.get("abilities"):
            return out
        from dnd_app.core.calculator import all_skill_bonuses, all_saving_throw_bonuses
        from dnd_app.core.character import ability_mod
        try:
            skills, saves = all_skill_bonuses(c), all_saving_throw_bonuses(c)
        except Exception:
            skills, saves = {}, {}
        out += [(f"{s} {_sign(b)}", s, b) for s, b in sorted(skills.items())]
        out += [(f"{a} save {_sign(b)}", f"{a} save", b) for a, b in saves.items()]
        out += [(f"{a} check {_sign(ability_mod(c, a))}", f"{a} check", ability_mod(c, a))
                for a in ("STR", "DEX", "CON", "INT", "WIS", "CHA")]
        return out

    @Property(list, notify=trayChanged)
    def bonusOptions(self):
        return [b[0] for b in self._bonuses()]

    @Property(int, notify=trayChanged)
    def bonusIndex(self):
        return self._bonus

    @Slot(int)
    def setBonus(self, index: int):
        options = self._bonuses()
        self._bonus = max(0, min(index, len(options) - 1))
        expr = self._expr
        if self._fresh or isinstance(_dice.parse(expr), str):
            expr = "1d20"                        # a bonus on its own: a d20 with it
        self._expr = _dice.set_modifier(expr, options[self._bonus][2]) or expr
        self._fresh = False
        self.trayChanged.emit()

    # ── The tray ──────────────────────────────────────────────────────
    @Property(str, notify=trayChanged)
    def expression(self):
        return self._expr

    @Slot(str)
    def setExpression(self, text: str):
        if text != self._expr:
            self._expr = text
            self._fresh = False
            self.trayChanged.emit()

    @Slot(int)
    def addDie(self, sides: int):
        if self._fresh:
            self._expr, self._bonus = "", 0
        self._expr = _dice.add_die(self._expr, sides)
        self._fresh = False
        self.trayChanged.emit()

    @Property(str, notify=trayChanged)
    def mode(self):
        return self._mode

    @Slot(str)
    def setMode(self, mode: str):
        self._mode = mode if mode in ("normal", "advantage", "disadvantage") else "normal"
        self.trayChanged.emit()

    @Slot()
    def clearTray(self):
        self._expr, self._mode, self._bonus, self._fresh = "", "normal", 0, False
        self.trayChanged.emit()

    @Slot()
    def roll(self):
        res = _dice.roll(self._expr, self._mode)
        if res["error"]:
            self._total, self._detail, self._nat = None, res["error"], 0
            self.resultChanged.emit()
            return
        self._expr = res["expr"]
        name = self._bonuses()[self._bonus][1] if self._bonus else ""
        detail = res["text"] + (f"  ({name})" if name else "")
        self._total, self._detail, self._nat = res["total"], detail, res["nat"]
        _log.log_roll(self._who(), "dice", res["expr"], res["total"], detail, nat=res["nat"],
                      result=res["mode"] if res["mode"] != "normal" else "")
        self._fresh = True
        self.trayChanged.emit()
        self.resultChanged.emit()

    # the old one-tap rolls, kept for anything that still calls them
    @Slot(int)
    def quickRoll(self, sides: int):
        self._expr, self._mode, self._bonus, self._fresh = f"1d{sides}", "normal", 0, False
        self.roll()

    @Slot(int, int, int, str)
    def customRoll(self, count: int, sides: int, modifier: int, adv_mode: str):
        self._expr = _dice.set_modifier(f"{max(1, count)}d{max(2, sides)}", modifier)
        self._mode = {"Advantage": "advantage", "Disadvantage": "disadvantage"}.get(adv_mode, "normal")
        self._bonus, self._fresh = 0, False
        self.roll()

    # ── The result ────────────────────────────────────────────────────
    @Property(str, notify=resultChanged)
    def totalText(self):
        return str(self._total) if self._total is not None else "—"

    @Property(str, notify=resultChanged)
    def detailText(self):
        return self._detail or "Pick dice below, then Roll."

    @Property(bool, notify=resultChanged)
    def isNat20(self):
        return self._nat == 20

    @Property(bool, notify=resultChanged)
    def isNat1(self):
        return self._nat == 1

    # ── The history ───────────────────────────────────────────────────
    @Property(list, notify=historyChanged)
    def history(self):
        out = []
        for e in _log.roll_history(self._who())[:SHOWN]:
            out.append({"id": e.get("id", 0), "kind": e.get("kind", ""), "when": _log.when(e),
                        "label": e.get("label") or "", "result": e.get("result") or "",
                        "detail": e.get("detail") or "",
                        "total": "" if e.get("total") is None else str(e["total"]),
                        "nat": e.get("nat") or 0,
                        # (the older text, for anything still reading it)
                        "text": f"{e.get('label') or ''}  →  {e.get('total')}",
                        "crit": "nat20" if e.get("nat") == 20 else "nat1" if e.get("nat") == 1 else None})
        return out

    @Property(str, notify=historyChanged)
    def historyTitle(self):
        who = self._who()
        name = who.get("name") if who is not self._session else ""
        return f"History · {name}" if name else "History"

    @Slot()
    def refresh(self):
        """The screen's opened: the bonuses and history as they are now."""
        self.trayChanged.emit()
        self.historyChanged.emit()

    @Slot(int)
    def reuse(self, rid: int):
        """A tray roll from the history, back in the tray."""
        e = next((x for x in _log.roll_history(self._who()) if x.get("id") == rid), None)
        if e is None or e.get("kind") != "dice":
            return
        self._expr = e.get("label") or ""
        self._mode = e.get("result") if e.get("result") in ("advantage", "disadvantage") else "normal"
        self._bonus, self._fresh = 0, False
        self.trayChanged.emit()

    @Slot()
    def clearHistory(self):
        _log.clear_roll_history(self._who())
        self._total, self._detail, self._nat = None, "", 0
        self.historyChanged.emit()
        self.resultChanged.emit()
