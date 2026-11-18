"""The new-character wizard's bridge (Android): one object every wizard
screen reads, over core/wizard_flow.py's Session -- the same steps,
picks and words as desktop's pages/wizard.py.

  1. Race                 RaceListScreen, RaceDetailScreen
  2. Abilities            AbilitiesScreen
  3. Class & Background   ClassScreen
  4. Spells & Choices     ChoicesScreen ("Choices" for a class with no
                          spells; skipped when there's nothing to pick)
  5. Equipment            EquipmentScreen, its "You'll start with" page
  6. Summary              SummaryScreen

Screens bind to `rev`, which goes up with every change, and read the rest
through slots (raceRows(), abilityView(), level1Cards() ...).
"""
from PySide6.QtCore import QObject, Signal, Slot, Property

from dnd_app.core import wizard_flow as W
from dnd_app.core.builder import ABILITIES


class WizardBridge(QObject):
    changed = Signal()

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self.s = W.Session()
        self._rev = 0
        self._reached = 0

    def _bump(self):
        self._rev += 1
        self.changed.emit()

    @Property(int, notify=changed)
    def rev(self):
        return self._rev

    # ── the whole wizard ──────────────────────────────────────────────
    @Slot()
    def reset(self):
        self.s = W.Session()
        self._reached = 0
        self._bump()

    # (older names App.qml and SaveLoadScreen.qml still use)
    @Slot()
    def resetToDefaults(self):
        self.reset()

    @Slot()
    def refresh(self):
        self._bump()

    @Property(str, notify=changed)
    def name(self):
        return self.s.state["name"] or self.char.get("name", "")

    @Property(int, notify=changed)
    def reached(self):
        """The furthest step reached (the menu lets you go back to any)."""
        return self._reached

    @Slot(int)
    def reach(self, step: int):
        if step > self._reached:
            self._reached = step
            self._bump()

    @Slot(int, result=str)
    def block(self, step: int) -> str:
        try:
            return self.s.block(step)
        except Exception:
            import traceback; traceback.print_exc()
            return ""

    @Slot(result=bool)
    def hasLevel1(self) -> bool:
        return self.s.has_level1()

    @Property(list, notify=changed)
    def stepNames(self):
        return ["Race", "Abilities", "Class",
                "Spells" if self.s.spells_step_name() != "Choices" else "Choices", "Gear", "Summary"]

    @Property(str, notify=changed)
    def spellsStepName(self):
        return self.s.spells_step_name()

    @Slot(result=bool)
    def finish(self) -> bool:
        """The finished character into the app's own (the sheet's)."""
        if self.block(0) or self.block(1) or self.block(2):
            return False
        try:
            c = self.s.finished()
        except Exception:
            import traceback; traceback.print_exc()
            return False
        c["character_created"] = True
        self.char.clear()
        self.char.update(c)
        self._bump()
        return True

    @Slot(result=bool)
    def confirmEquipment(self) -> bool:
        return self.finish()

    # ── 1. Race ───────────────────────────────────────────────────────
    @Property(list, constant=True)
    def raceGroups(self):
        return [n for n, _ in W.SOURCE_GROUPS]

    @Property(str, notify=changed)
    def raceGroup(self):
        return self.s.state["race_group"]

    @Slot(str)
    def setRaceGroup(self, g: str):
        self.s.state["race_group"] = g
        self._bump()

    @Property(str, notify=changed)
    def raceSearch(self):
        return self.s.state["race_search"]

    @Slot(str)
    def setRaceSearch(self, t: str):
        if t != self.s.state["race_search"]:
            self.s.state["race_search"] = t
            self._bump()

    @Slot(result="QVariant")
    def raceRows(self):
        s = self.s.state
        return W.race_rows(s["race_search"], s["race_group"])

    @Property(str, notify=changed)
    def selectedRace(self):
        return self.s.state["race"]

    @Property(str, notify=changed)
    def selectedSubrace(self):
        return self.s.state["sub"]

    @Slot(str)
    def selectRace(self, name: str):
        self.s.pick_race(name)
        self._bump()

    @Slot(result="QVariant")
    def raceCard(self):
        s = self.s.state
        card = W.race_card(s["race"], s["sub"]) if s["race"] else {}
        if not card:
            return {}
        if card["subraces"]:
            if card["subrace_required"] or "Standard" in card["subraces"]:
                opts = [{"label": n, "value": n} for n in card["subraces"]]
            else:
                opts = [{"label": "Standard", "value": ""}] + [{"label": n, "value": n} for n in card["subraces"]]
            card["subOptions"] = opts
        else:
            card["subOptions"] = []
        card["rpicks"] = dict(s["rpicks"])
        return card

    @Slot(str)
    def selectSubrace(self, v: str):
        self.s.pick_sub(v)
        self._bump()

    @Slot(str, str)
    def pickRaceExtra(self, field: str, value: str):
        self.s.pick_rextra(field, value)
        self._bump()

    # ── 2. Abilities ──────────────────────────────────────────────────
    @Property(list, constant=True)
    def methods(self):
        return list(W.METHODS)

    @Property(str, notify=changed)
    def method(self):
        return self.s.state["method"]

    @Slot(str)
    def setMethod(self, m: str):
        self.s.set_method(m)
        self._bump()

    @Slot(str, bool)
    def stepScore(self, ab: str, up: bool):
        self.s.step_score(ab, up)
        self._bump()

    @Slot()
    def rollAll(self):
        self.s.roll_all()
        self._bump()

    @Slot(str)
    def rollOne(self, ab: str):
        self.s.roll_one(ab)
        self._bump()

    @Slot(str)
    def tapPick(self, ab: str):
        self.s.tap_pick(ab)
        self._bump()

    @Slot()
    def toggleMoved(self):
        self.s.toggle_moved()
        self._bump()

    @Slot(str, int)
    def moveBonus(self, ab: str, d: int):
        self.s.move_bonus(ab, d)
        self._bump()

    @Slot(result="QVariant")
    def abilityView(self):
        s = self.s.state
        plan = self.s.plan()
        tots = W.totals(plan, s["base"], s["picks"], s["moved"])
        cols = []
        for ab in ABILITIES:
            t = tots[ab]
            cols.append({"ab": ab, "base": t["base"], "fixed": t["fixed"], "pick": t["pick"],
                         "total": t["total"], "mod": t["mod"], "neg": t["mod"].startswith("-"),
                         "canPick": bool(plan["points"]) and ab not in plan["exclude"],
                         "moved": (s["moved"] or {}).get(ab, 0)})
        return {"text": plan["text"], "cols": cols, "hasFixed": bool(plan["fixed"]),
                "moving": s["moved"] is not None,
                "pointBuyLeft": W.point_buy_left(s["base"]) if s["method"] == "Point Buy" else 0}

    # ── 3. Class & Background ─────────────────────────────────────────
    @Slot(str)
    def setName(self, t: str):
        if t != self.s.state["name"]:
            self.s.state["name"] = t
            self._bump()

    @Property(list, constant=True)
    def alignments(self):
        return list(W.ALIGNMENTS)

    @Property(str, notify=changed)
    def alignment(self):
        return self.s.state["alignment"]

    @Slot(str)
    def setAlignment(self, a: str):
        self.s.state["alignment"] = a
        self._bump()

    @Property(list, constant=True)
    def classTiles(self):
        return W.class_tiles()

    @Property(str, notify=changed)
    def selectedClass(self):
        return self.s.state["cls"]

    @Slot(str)
    def pickClass(self, n: str):
        self.s.pick_class(n)
        self._bump()

    @Slot(result="QVariant")
    def classChips(self):
        return W.class_chips(self.s.state["cls"]) if self.s.state["cls"] else []

    @Property(str, notify=changed)
    def bgSearch(self):
        return self.s.state["bg_search"]

    @Slot(str)
    def setBgSearch(self, t: str):
        if t != self.s.state["bg_search"]:
            self.s.state["bg_search"] = t
            self._bump()

    @Slot(result="QVariant")
    def bgRows(self):
        return W.background_rows(self.s.state["bg_search"])

    @Property(str, notify=changed)
    def selectedBackground(self):
        return self.s.state["bg"]

    @Slot(str)
    def pickBackground(self, n: str):
        self.s.pick_bg(n)
        self._bump()

    @Slot(result="QVariant")
    def bgCard(self):
        bg = self.s.state["bg"]
        card = W.background_card(bg) if bg else {}
        if card:
            card["feat"] = self.s.state["bg_feat"]
        return card

    @Slot(str)
    def pickBgFeat(self, f: str):
        self.s.state["bg_feat"] = f
        self._bump()

    # ── 4. Spells & Choices ───────────────────────────────────────────
    @Slot(result="QVariant")
    def level1Cards(self):
        try:
            _, cards, _ = self.s.level1_data()
        except Exception:
            import traceback; traceback.print_exc()
            return []
        out = []
        for c in cards:
            d = dict(c)
            d["done"] = not c["left"]
            d["kids"] = [k["id"] for k in cards if k["parent"] == c["id"]]
            for t in d["tiles"]:
                t["on"] = t["value"] in c["picked"]
            out.append(d)
        return out

    @Slot(result="QVariant")
    def level1Left(self):
        try:
            return self.s.level1_left()
        except Exception:
            return []

    @Slot(str, str)
    def toggleChoice(self, cid: str, value: str):
        self.s.toggle_choice(cid, value)
        self._bump()

    @Slot(result="QVariant")
    def spellPlan(self):
        try:
            _, _, plan = self.s.level1_data()
        except Exception:
            return {}
        if not plan:
            return {}
        sp = self.s.state["spells"]
        tabs = [dict(t, picked=len(sp.get(t["key"], []))) for t in plan["tabs"]]
        if self.s.state["spell_tab"] not in [t["key"] for t in tabs]:
            self.s.state["spell_tab"] = tabs[0]["key"]
        return dict(plan, tabs=tabs, tab=self.s.state["spell_tab"])

    @Slot(str)
    def setSpellTab(self, k: str):
        self.s.state["spell_tab"] = k
        self._bump()

    @Slot(str)
    def setSpellSearch(self, t: str):
        if t != self.s.state["spell_search"]:
            self.s.state["spell_search"] = t
            self._bump()

    @Property(str, notify=changed)
    def spellSearch(self):
        return self.s.state["spell_search"]

    @Slot(result="QVariant")
    def spellRows(self):
        plan = W.spell_plan(self.s.built(3))
        tab = next((t for t in plan.get("tabs", []) if t["key"] == self.s.state["spell_tab"]), None)
        if not tab:
            return []
        picked = set(self.s.state["spells"].get(tab["key"], []))
        rows = W.spell_rows(tab, self.s.state["spell_search"])
        for r in rows:
            r["on"] = r["name"] in picked
            r["key"] = tab["key"]
        return rows

    @Slot(str, str)
    def toggleSpell(self, key: str, name: str):
        self.s.toggle_spell(key, name)
        self._bump()

    # ── 5. Equipment ──────────────────────────────────────────────────
    @Slot(result="QVariant")
    def equipView(self):
        s = self.s.state
        if not s["cls"]:
            return {"groups": [], "always": [], "bgGear": [], "bg": ""}
        groups = self.s.groups()
        choice = self.s.equip_choice()
        out, always = [], []
        for gi, g in enumerate(groups):
            if g["fixed"] and not g["options"][0]["anys"]:
                always += W._count_items(g["options"][0]["items"])
                continue
            sel = choice[gi]
            opts = []
            for oi, o in enumerate(g["options"]):
                fixed = [x for x in o["items"] if not x.lower().startswith("any ")]
                label = ", ".join(W._count_items(fixed + [a["name"] for a in o["anys"]]))
                on = g["fixed"] or sel.get("option", 0) == oi
                anys = []
                for ai, a in enumerate(o["anys"]):
                    picked = (sel.get("anys") or [])
                    anys.append({"name": a["name"], "pool": a["pool"],
                                 "value": picked[ai] if on and ai < len(picked) else (a["pool"][0] if a["pool"] else "")})
                opts.append({"letter": "ABCDEFG"[oi], "label": label, "on": on, "anys": anys})
            out.append({"gi": gi, "title": g["title"], "fixed": g["fixed"], "options": opts})
        return {"groups": out, "always": always, "bgGear": W.background_gear(self.s.built(3)), "bg": s["bg"]}

    @Slot(int, int)
    def pickOption(self, gi: int, oi: int):
        self.s.pick_option(gi, oi)
        self._bump()

    @Slot(int, int, str)
    def setAny(self, gi: int, ai: int, text: str):
        self.s.set_any(gi, ai, text)
        self._bump()

    @Property(str, notify=changed)
    def extra(self):
        return self.s.state["extra"]

    @Slot(str)
    def setExtra(self, t: str):
        if t != self.s.state["extra"]:
            self.s.state["extra"] = t
            self._bump()

    @Slot(result="QVariant")
    def kitPreview(self):
        if not self.s.state["cls"]:
            return {"slots": [], "rows": [], "gold": "", "weight": ""}
        return W.kit_preview(self.s.built(4), self.s.items(), self.s.state["extra"])

    # ── 6. Summary ────────────────────────────────────────────────────
    @Slot(result="QVariant")
    def summary(self):
        try:
            c = W.kit_char(self.s.built(4), self.s.items(), self.s.state["extra"])
            sm = W.summary(c)
        except Exception:
            import traceback; traceback.print_exc()
            return {}
        sm["stats"] = [{"value": v, "label": l} for v, l in sm["stats"]]
        sm["skills"] = [{"name": n, "bonus": b} for n, b in sm["skills"]]
        sm["profs"] = [{"label": l, "text": t} for l, t in sm["profs"]]
        sm["equipment"] = [{"label": l, "text": t} for l, t in sm["equipment"]]
        return sm
