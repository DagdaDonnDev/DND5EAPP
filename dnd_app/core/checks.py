"""Ability checks, saving throws, initiative and attack rolls -- every d20
you roll -- worked out once for both apps (desktop: the Abilities, Skills
and Combat tabs and the concentration save; Android: bridge
character_sheet.py rollQuickCheck and rollConcentrationSave; an attack's
roll for core/attacks.py): the d20, what always applies to it, then what
you can add, each with its cost, only what you can pay for now.

    roll_check(char, what, answers, free, rng) -> result
        what    {"kind": "check" | "save" | "initiative" | "concentration",
                 "ability": "DEX", "skill": "Stealth" or "", "label":
                 "Stealth check", "bonus": 7, and for a concentration save
                 "dc" and "spell"}; a check with a tool you're proficient
                 with: {"kind": "check", "tool": "Thieves' tools",
                 "ability": "DEX" or "" -- then it asks which, your DM's
                 call, the usual one first; the bonus is worked out here}
        free    the parts of the turn still free ("Action", "Reaction"...)
        result  {"ask": ...} first, when there's something to decide before
                the roll: cast Guidance or Resistance on yourself, take
                advantage you have (Inspiration, Tides of Chaos, Kenku
                Recall...), use a Portent roll. The same question protocol
                as core/action_use.py; the roll is kept in answers, so it's
                made once.
                {"report": ...} the roll, for the roll dialog (both apps'
                attack dialog shows it), when there's something to add
                {"toast": ...} the roll, said, when there's nothing to add
                "cast": a spell cast before the roll (its action is spent);
                "slots": parts of the turn used; "refresh": something spent
    add_to_check(char, report, key, answers, free, rng) -> result
        The dialog's Add on one option: it's paid for (a superiority die, a
        use, your reaction...) and rolled now, and "report" is the roll as
        it stands, with what's still left to add -- or {"ask"} first (how
        many allies can you see?).
    finish_check(char, report, answers) -> result
        Done: the toast says the total. A concentration save still under
        its DC drops the spell; a die that's spent only on a success
        (Psi-Bolstered Knack) asks whether it succeeded.
    take_check_options(char, report, picked, answers, rng)
        The picked ones added, then Done.

Attack rolls (core/attacks.py) go through the same: attack_state() makes
the roll -- kind "attack" -- and add_option() adds to it; IF IT MISSES
holds what you'd use once you know it missed (Favored by the Gods...).

What's always on the roll, before you see it:
    Halfling Lucky (a 1 is rolled again); Reliable Talent and Silver
    Tongue, Starry Form (Dragon) and Trance of Order (a d20 of 9 or lower
    counts as 10); Glibness (15); Indomitable Might; Bless and Bane;
    Boldness and Bolstering Magic; a dragonmark's intuition and Vedalken
    Tireless Precision (a d4); the Frost Rune's +2; Durable Magic's +2 and
    Bladesong on concentration.
"""
import random

_PHYSICAL = ("STR", "DEX", "CON")


# ── The character ─────────────────────────────────────────────────────────
def _cl(char):
    from dnd_app.core.calculator import class_levels
    return class_levels(char)


def _sub(char, cls):
    from dnd_app.core.character import subclasses
    return (subclasses(char).get(cls) or "").lower()


def _race(char):
    return char.get("species") or char.get("race", "") or ""


def _fx(char):
    return char.get("active_effects", []) or []


def _mod(char, ability):
    from dnd_app.core.character import ability_mod
    return ability_mod(char, ability)


def _skill_prof(char, skill):
    """0 none, 1 half, 2 proficient, 3 expertise -- with a githyanki's or
    astral elf's skill for the day."""
    level = (char.get("skills") or {}).get(skill, 0)
    astral = (char.get("_choices") or {}).get("astral_knowledge_skill") or []
    if astral and astral[0] == skill:
        level = max(level, 2)
    return level


def _res(char, *names):
    """A counter by key or name -- or the one a rule's own uses make
    (core/action_use.py: "use_kenku_recall")."""
    from dnd_app.core import action_use as au
    for n in names:
        for r in char.get("resources", []):
            if r.get("key") == n or str(r.get("name", "")).lower() == n.lower():
                return r
    for n in names:
        spec = au.rule_for(n)
        if spec and spec.get("uses"):
            r = au._uses_resource(char, n, spec)
            if r is not None:
                return r
    return None


def _left(r) -> int:
    if r is None:
        return 0
    if str(r.get("current_max")).lower() == "unlimited":
        return 99
    try:
        return int(r.get("current", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _pool(char, code):
    from dnd_app.core import action_use as au
    if code == "sd":
        # a Battle Master's dice, or Martial Adept's
        for key in ("sup_dice", "martial_adept"):
            r = next((x for x in char.get("resources", []) if x.get("key") == key), None)
            if r is not None and _left(r) > 0:
                return r
        return next((x for x in char.get("resources", []) if x.get("key") in ("sup_dice", "martial_adept")), None)
    return au._find_pool(char, code)


def _noun(code, n):
    from dnd_app.core import action_use as au
    return au._noun(code, n)


def _special_die(char, tok):
    """"1d8" -- a superiority die (SD), a Bardic Inspiration die (BI), a
    Psionic Energy die (PSI)."""
    from dnd_app.core import action_use as au
    return au._special_die(char, tok)


def _known_maneuvers(char) -> set:
    return {m.split(" –")[0].split(" (")[0].strip() for m in char.get("battle_master_maneuvers", []) or []}


def _halfling_lucky(char) -> bool:
    from dnd_app.data.races import keeps_race_traits
    return _race(char).startswith("Halfling") and keeps_race_traits(char)


def _starry_dragon(char) -> bool:
    if "Starry Form" not in _fx(char):
        return False
    return ((char.get("effect_details") or {}).get("Starry Form") or {}).get("choice") == "Dragon"


def _vedalken_skill(char) -> str:
    if not _race(char).startswith("Vedalken"):
        return ""
    pick = (char.get("_choices") or {}).get("race_skill_profs") or []
    return pick[0] if pick else ""


def _vedalken_tool(char) -> str:
    if not _race(char).startswith("Vedalken"):
        return ""
    pick = (char.get("_choices") or {}).get("race_tool_profs") or []
    return pick[0] if pick else ""


_AB_NAMES = {"STR": "Strength", "DEX": "Dexterity", "CON": "Constitution", "INT": "Intelligence",
             "WIS": "Wisdom", "CHA": "Charisma"}


def _tool_ability_options(char, tool) -> list:
    """[(ability, "Dexterity (+7)")] -- the usual one for this tool first."""
    from dnd_app.core.calculator import tool_usual_ability, get_tool_bonus
    first = tool_usual_ability(tool)
    order = [first] + [a for a in _AB_NAMES if a != first]
    return [(a, f"{_AB_NAMES[a]} ({get_tool_bonus(char, tool, a):+d})") for a in order]


def _can_cast(char, name, free) -> bool:
    """You know the cantrip and could cast it now, with your action."""
    from dnd_app.data.spells import get_spell
    from dnd_app.core.calculator import spellcasting_block_reason
    from dnd_app.core.spellcasting import spell_component_block_reason
    spell = get_spell(name)
    if not spell or "Action" not in free:
        return False
    if name not in char.get("spells_known", []) and name not in char.get("bonus_spells", []):
        return False
    if char.get("_wildshape_active") and _cl(char).get("Druid", 0) < 18:
        return False
    return not spellcasting_block_reason(char) and not spell_component_block_reason(char, spell)


# ── Before the roll ───────────────────────────────────────────────────────
def _before_options(char, w, free) -> list:
    """[(key, label)] -- what you'd decide before rolling."""
    kind, skill = w["kind"], w.get("skill") or ""
    fx = _fx(char)
    out = []
    conc = (char.get("concentration") or {}).get("spell")
    for spell, kinds in (("Guidance", ("check",)), ("Resistance", ("save",))):
        if kind in kinds and spell not in fx and _can_cast(char, spell, free):
            out.append((f"cast:{spell}", f"Cast {spell} on yourself first: +1d4 (your action"
                        + (f"; you stop concentrating on {conc})" if conc and conc != spell else ")")))
    # 2014 Inspiration is advantage, chosen before the roll (the 2024 rules'
    # Heroic Inspiration rerolls it after: _after_options)
    if char.get("inspiration") and char.get("edition") != "2024":
        out.append(("inspiration", "Spend your Inspiration: advantage"))
    tides = _res(char, "tides_of_chaos")
    if _left(tides):
        out.append(("tides", "Tides of Chaos: advantage (once a long rest)"))
    if kind == "check" and skill and _skill_prof(char, skill) >= 2 and _race(char).startswith("Kenku (MPMM)"):
        r = _res(char, "Kenku Recall")
        if _left(r):
            out.append(("kenku", f"Kenku Recall: advantage ({_left(r)} left)"))
    if kind == "check" and skill in ("Intimidation", "Persuasion") and "draconblood" in (char.get("subrace") or "").lower():
        r = _res(char, "Forceful Presence")
        if _left(r):
            out.append(("forceful", "Forceful Presence: advantage (once a short or long rest)"))
    if kind in ("save", "concentration") and "Bandit Cunning" in char.get("feats", []) and "Reaction" in free:
        r = _res(char, "Bandit Cunning (Lucky Break)", "bandit_cunning")
        if _left(r):
            out.append(("lucky_break", f"Lucky Break: +{_mod(char, 'INT')} (your reaction, once a long rest)"))
    # Cosmic Omen (Circle of Stars 6): a Weal omen adds a d6 to a roll that's
    # about to be made -- a Woe omen only takes from others' rolls
    if _cl(char).get("Druid", 0) >= 6 and "stars" in _sub(char, "Druid") and "Reaction" in free:
        r = _res(char, "Cosmic Omen")
        if _left(r):
            out.append(("cosmic", f"Cosmic Omen, if your omen is Weal: +1d6 (your reaction; {_left(r)} left)"))
    if kind in ("check", "initiative") and _cursed_luckstone(char) \
            and ((char.get("item_uses") or {}).get("Cursed Luckstone") or {}).get("current", 1) > 0:
        out.append(("luckstone", "Cursed Luckstone: advantage (once a dawn; then your next two checks have "
                                 "disadvantage)"))
    if "Portent" not in (char.get("_turn_uses") or []):
        from dnd_app.core.action_use import portent_rolls
        if _res(char, "portent") is not None:
            for n in sorted(set(portent_rolls(char)), reverse=True):
                out.append((f"portent:{n}", f"Portent: the d20 is a {n}"))
    return out


def _cursed_luckstone(char) -> bool:
    from dnd_app.core.magic_items import _active_item_names
    return "Cursed Luckstone" in _active_item_names(char)


def _pay_before(char, key, state, free):
    """Spend what the choice before the roll costs."""
    from dnd_app.core.action_use import spend_portent
    if key == "cosmic":
        r = _res(char, "Cosmic Omen")
        if r is not None and str(r.get("current_max")).lower() != "unlimited":
            r["current"] = max(0, _left(r) - 1)
        state["auto"].append({"source": "Cosmic Omen", "dice": "1d6", "sign": 1})
        state["slots"].append("Reaction")
        state["spent"].append(f"Cosmic Omen ({_left(r)} left) and your reaction")
    elif key == "luckstone":
        u = char.setdefault("item_uses", {}).setdefault("Cursed Luckstone",
                                                       {"current": 1, "max": 1, "recharge": "dawn"})
        u["current"] = 0
        state["adv"] = "the Cursed Luckstone"
        state["luckstone"] = True
        state["spent"].append("the Cursed Luckstone, until dawn")
        state["notes"].append("Cursed Luckstone: your next two ability checks have disadvantage")
    elif key.startswith("cast:"):
        spell = key[5:]
        conc = (char.get("concentration") or {}).get("spell")
        if conc and conc != spell:
            from dnd_app.core.magic_items import drop_concentration
            drop_concentration(char)
            state["notes"].append(f"you stop concentrating on {conc}")
        state["cast"] = spell
        state["auto"].append({"source": spell, "dice": "1d4", "sign": 1})
    elif key == "inspiration":
        char["inspiration"] = False
        state["adv"] = "your Inspiration"
        state["spent"].append("your Inspiration")
    elif key in ("tides", "kenku", "forceful"):
        name = {"tides": "Tides of Chaos", "kenku": "Kenku Recall", "forceful": "Forceful Presence"}[key]
        r = _res(char, {"tides": "tides_of_chaos", "kenku": "Kenku Recall", "forceful": "Forceful Presence"}[key])
        if r is not None and str(r.get("current_max")).lower() != "unlimited":
            r["current"] = max(0, _left(r) - 1)
        state["adv"] = name
        state["spent"].append(f"{name} ({_left(r)} left)")
    elif key == "lucky_break":
        r = _res(char, "Bandit Cunning (Lucky Break)", "bandit_cunning")
        if r is not None:
            r["current"] = max(0, _left(r) - 1)
        state["flat"].append({"source": "Lucky Break", "value": _mod(char, "INT")})
        state["slots"].append("Reaction")
        state["spent"].append("Lucky Break and your reaction")
    elif key.startswith("portent:"):
        n = int(key.split(":")[1])
        spend_portent(char, n)
        char.setdefault("_turn_uses", []).append("Portent")
        state["portent"] = n
        state["spent"].append(f"the Portent roll {n}")


# ── The roll ──────────────────────────────────────────────────────────────
def _is_check(w):
    return w["kind"] in ("check", "initiative")


def _is_save(w):
    return w["kind"] in ("save", "concentration")


def _is_attack(w):
    return w["kind"] == "attack"


def _adds_proficiency(char, w) -> bool:
    """Does this ability check add your proficiency bonus (Reliable
    Talent's test)? A skill you're proficient in, or initiative when your
    proficiency bonus goes on it (Hare-Trigger, Aura of the Sentinel).
    Half of it (Jack of All Trades, Remarkable Athlete) isn't."""
    if w["kind"] == "initiative":
        from dnd_app.core.calculator import initiative_adds_proficiency
        return initiative_adds_proficiency(char)
    if w.get("tool"):
        return True                     # only a tool you're proficient with is rolled
    skill = w.get("skill") or ""
    return bool(skill) and _skill_prof(char, skill) >= 2


def _floors(char, w, ability) -> list:
    """[(lowest d20, source)] that apply to this roll."""
    out = []
    cl = _cl(char)
    skill = w.get("skill") or ""
    if _is_check(w):
        if cl.get("Rogue", 0) >= 11 and _adds_proficiency(char, w):
            out.append((10, "Reliable Talent"))
        if skill in ("Persuasion", "Deception") and cl.get("Bard", 0) >= 3 and "eloquence" in _sub(char, "Bard"):
            out.append((10, "Silver Tongue"))
        if ability == "CHA" and "Glibness" in _fx(char):
            out.append((15, "Glibness"))
    if _starry_dragon(char) and ((_is_check(w) and ability in ("INT", "WIS")) or w["kind"] == "concentration"):
        out.append((10, "Starry Form (Dragon)"))
    if "Trance of Order" in _fx(char):
        out.append((10, "Trance of Order"))
    return out


def _auto_parts(char, w, ability):
    """What's added to the roll without asking: (dice [{source, dice,
    sign}], flat [{source, value}])."""
    fx = _fx(char)
    dice, flat = [], []
    skill = w.get("skill") or ""
    if _is_attack(w):
        for name, die, sign in (("Bless", "1d4", 1), ("Bane", "1d4", -1), ("Boldness", "1d4", 1),
                                ("Bolstering Magic", "1d3", 1)):
            if name in fx:
                dice.append({"source": name, "dice": die, "sign": sign})
        return dice, flat
    if _is_save(w):
        if "Bless" in fx:
            dice.append({"source": "Bless", "dice": "1d4", "sign": 1})
        if "Bane" in fx:
            dice.append({"source": "Bane", "dice": "1d4", "sign": -1})
        if "Boldness" in fx:
            dice.append({"source": "Boldness", "dice": "1d4", "sign": 1})
    if _is_check(w):
        if "Bolstering Magic" in fx:
            dice.append({"source": "Bolstering Magic", "dice": "1d3", "sign": 1})
        if skill:
            from dnd_app.data.races import DRAGONMARK_INTUITION
            mark = DRAGONMARK_INTUITION.get(char.get("subrace") or "")
            if mark and skill in mark[1]:
                dice.append({"source": mark[0], "dice": "1d4", "sign": 1})
            if skill == _vedalken_skill(char):
                dice.append({"source": "Tireless Precision", "dice": "1d4", "sign": 1})
        tool = w.get("tool") or ""
        if tool:
            from dnd_app.data.races import DRAGONMARK_INTUITION, DRAGONMARK_INTUITION_TOOLS
            sub = char.get("subrace") or ""
            if tool.lower() in {t.lower() for t in DRAGONMARK_INTUITION_TOOLS.get(sub, [])}:
                dice.append({"source": DRAGONMARK_INTUITION[sub][0], "dice": "1d4", "sign": 1})
            if tool.lower() == _vedalken_tool(char).lower():
                dice.append({"source": "Tireless Precision", "dice": "1d4", "sign": 1})
    if ability in ("STR", "CON") and "Frost Rune" in fx:
        flat.append({"source": "Frost Rune", "value": 2})
    concentrating = bool((char.get("concentration") or {}).get("spell"))
    if _is_save(w) and concentrating and _cl(char).get("Wizard", 0) >= 10 and "war magic" in _sub(char, "Wizard"):
        flat.append({"source": "Durable Magic", "value": 2})
    if w["kind"] == "concentration" and "Bladesong" in fx:
        flat.append({"source": "Bladesong", "value": max(1, _mod(char, "INT"))})
    return dice, flat


def _d20(char, rng, notes):
    """One d20 -- a halfling's 1 is rolled again (and that roll stands)."""
    d = rng.randint(1, 20)
    if d == 1 and _halfling_lucky(char):
        d = rng.randint(1, 20)
        notes.append(f"Lucky: you rolled a 1, so it was rolled again: {d}")
    return d


def _settle(char, w, state):
    """The d20 that counts, after advantage and the floors, and the
    total."""
    ability = w.get("ability") or ""
    dice = state["dice"]
    if state.get("portent") is not None:
        raw = state["portent"]
    else:
        raw = max(dice) if state.get("adv") and len(dice) > 1 else dice[0]
    best = max(_floors(char, w, ability), default=None, key=lambda f: f[0])
    d20 = raw
    state["floor"] = ""
    if best and raw < best[0]:
        d20 = best[0]
        state["floor"] = f"{best[1]}: the {raw} counts as {best[0]}"
    if state.get("set20"):
        d20 = 20
    state["raw"], state["d20"] = raw, d20
    total = d20 + int(w.get("bonus", 0) or 0)
    total += sum(p["value"] * p.get("sign", 1) for p in state["auto"] if "value" in p)
    total += sum(p["value"] for p in state["flat"])
    state["mighty"] = ""
    if _is_check(w) and ability == "STR" and _cl(char).get("Barbarian", 0) >= 18:
        from dnd_app.core.character import ability_score
        score = ability_score(char, "STR")
        if total < score:
            state["mighty"] = f"Indomitable Might: your Strength score, {score}, in place of {total}"
            total = score
    state["total"] = total
    return total


def _roll_dice_parts(state, rng):
    """Roll each automatic die once: state["auto"] gets its value."""
    for p in state["auto"]:
        if "value" not in p:
            n, s = map(int, p["dice"].split("d"))
            p["value"] = sum(rng.randint(1, s) for _ in range(n))


def _reminder(char, w):
    from dnd_app.core.calculator import roll_reminder
    kind = w["kind"]
    r = roll_reminder(char, kind, w.get("ability") or "", skill=w.get("skill") or "",
                      extra_adv=w.get("extra_adv") or ())
    if _is_check(w) and char.get("_luckstone_curse"):
        r["disadvantage"] = list(r["disadvantage"]) + ["the Cursed Luckstone's curse"]
    parts = []

    def said(names):
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    if r["advantage"]:
        parts.append(f"advantage from {said(r['advantage'])}")
    if r["disadvantage"]:
        parts.append(f"disadvantage from {said(r['disadvantage'])}")
    return ("Reminder: " + "; ".join(parts) + ".") if parts else "", r


def _start(char, w, pick, free, rng):
    """The roll itself: what was picked before it (a key from
    _before_options) paid for, the d20 -- two with advantage you took --
    what always applies, the reminder, and the total."""
    state = _new_state()
    if w.get("note"):                     # what the roll is for (Set a Trap: its total is the DC)
        state["notes"].append(w["note"][0].upper() + w["note"][1:])
    if pick:
        _pay_before(char, pick, state, free)
    state["dice"] = [_d20(char, rng, state["notes"]) for _ in range(2 if state["adv"] else 1)]
    dice, flat = _auto_parts(char, w, w.get("ability") or "")
    state["auto"] += dice
    state["flat"] += flat
    _roll_dice_parts(state, rng)
    reminder, r = _reminder(char, w)
    if _is_check(w):
        # the Cursed Luckstone's curse: two checks with disadvantage after it's used
        if state.get("luckstone"):
            char["_luckstone_curse"] = 2
        elif char.get("_luckstone_curse"):
            char["_luckstone_curse"] -= 1
    state["reminder"] = reminder
    state["disadvantage"] = bool(r["disadvantage"])
    if state["adv"] and r["disadvantage"]:
        state["notes"].append(f"If you also have disadvantage, the two cancel: your d20 is the first, "
                              f"{state['dice'][0]}")
    state["free"] = list(free)
    _settle(char, w, state)
    return state


def before_question(char, w, free):
    """The question before a roll ({"key": "before", "title", "options"}),
    or None when there's nothing to decide first."""
    before = _before_options(char, w, free)
    if not before:
        return None
    return {"key": "before", "title": f"{w['label']}: before you roll",
            "options": ["Just roll"] + [label for _, label in before]}


def attack_state(char, w, before="", free=("Action", "Bonus Action", "Reaction"), rng=None):
    """An attack roll for core/attacks.py, made the way a check is.
    w: {"kind": "attack", "label", "bonus", "ability", "row": {"name",
    "kind", "base", "melee", "ranged"}, "extra_adv": [...]}; before: the
    answer to before_question ("" or "Just roll": nothing)."""
    pick = next((k for k, label in _before_options(char, w, free) if label == before), None)
    return _start(char, w, pick, list(free), rng or random)


# ── After the roll ────────────────────────────────────────────────────────
def _after_options(char, w, state, free) -> list:
    """What you can add now, each {key, title, dice, cost, section} plus
    how it's paid ("pay") and what it does ("does"): only what you can
    pay for now, each once a roll. Section "add": anytime; "fail": once
    you know the roll fails (an attack's IF IT MISSES)."""
    from dnd_app.core.calculator import effective_conditions
    kind, ability, skill = w["kind"], w.get("ability") or "", w.get("skill") or ""
    cl, fx, feats = _cl(char), _fx(char), char.get("feats", [])
    turn = char.get("_turn_uses") or []
    free = [b for b in free if b not in (state.get("slots") or [])]     # used during this roll
    reaction = "Reaction" in free
    check, save, attack = _is_check(w), _is_save(w), _is_attack(w)
    two = char.get("edition") == "2024"
    row = w.get("row") or {}
    weapon = attack and row.get("kind") != "spell"
    out = []

    def add(key, title, dice, cost, does, pay=(), section="add"):
        out.append({"key": key, "title": title, "dice": dice, "cost": cost, "section": section,
                    "group": "", "needs": "", "head": "", "head_note": "", "does": does, "pay": list(pay)})

    def uses(r, what="use"):
        n = _left(r)
        return f"{n} {what}{'s' if n != 1 else ''} left" if n < 99 else ""

    # spells on you that last until one roll
    if check and "Guidance" in fx:
        add("Guidance", "Guidance", "+1d4", "Guidance ends", ("dice", "1d4"), [("fx_end", "Guidance")])
    if save and "Resistance" in fx:
        add("Resistance", "Resistance", "+1d4", "Resistance ends", ("dice", "1d4"), [("fx_end", "Resistance")])
    if two and char.get("inspiration"):
        add("Heroic Inspiration", "Heroic Inspiration: roll the d20 again, the new roll stands", "",
            "your Heroic Inspiration", ("reroll",), [("inspiration",)])
    # Battle Master maneuvers (and Martial Adept's)
    maneuvers = _known_maneuvers(char)
    sd = _pool(char, "sd")
    if maneuvers and _left(sd):
        die = _special_die(char, "SD")
        cost = f"1 {_noun('sd', 1)} ({_left(sd)} left)"
        if "Ambush" in maneuvers and (skill == "Stealth" or kind == "initiative") \
                and "Incapacitated" not in effective_conditions(char):
            add("Ambush", "Ambush", f"+{die}", cost, ("dice", "SD"), [("pool", "sd", 1)])
        if "Commanding Presence" in maneuvers and skill in ("Intimidation", "Performance", "Persuasion"):
            add("Commanding Presence", "Commanding Presence", f"+{die}", cost, ("dice", "SD"), [("pool", "sd", 1)])
        if "Tactical Assessment" in maneuvers and skill in ("Investigation", "History", "Insight"):
            add("Tactical Assessment", "Tactical Assessment", f"+{die}", cost, ("dice", "SD"), [("pool", "sd", 1)])
        # a weapon attack's roll (2024: any attack roll, once it misses)
        if "Precision Attack" in maneuvers and (weapon or (attack and two)):
            add("Precision Attack", "Precision Attack", f"+{die}", cost, ("dice", "SD"), [("pool", "sd", 1)],
                section="fail" if two else "add")
    # class features
    bi = _pool(char, "bi")
    if check and cl.get("Bard", 0) >= 14 and "lore" in _sub(char, "Bard") and _left(bi):
        add("Peerless Skill", "Peerless Skill", f"+{_special_die(char, 'BI')}",
            f"1 Bardic Inspiration ({_left(bi)} left)", ("dice", "BI"), [("pool", "bi", 1)])
    if not attack and cl.get("Artificer", 0) >= 7 and reaction:
        r = _res(char, "flash_of_genius")
        if _left(r):
            add("Flash of Genius", "Flash of Genius", f"+{_mod(char, 'INT')}", f"your reaction; {uses(r)}",
                ("flat", _mod(char, "INT")), [("res", "flash_of_genius"), ("reaction",)])
    if not attack and cl.get("Warlock", 0) >= 6 and "fiend" in _sub(char, "Warlock"):
        r = _res(char, "use_dark_one_s_own_luck", "Dark One's Own Luck")
        if _left(r):
            add("Dark One's Own Luck", "Dark One's Own Luck", "+1d10", "once a short or long rest",
                ("dice", "1d10"), [("res", r.get("key"))])
    if "Emboldening Bond" in fx and "Emboldening Bond" not in turn:
        add("Emboldening Bond", "Emboldening Bond", "+1d4", "once a turn", ("dice", "1d4"),
            [("turn", "Emboldening Bond")])
    if cl.get("Ranger", 0) >= 7 and "monster slayer" in _sub(char, "Ranger"):
        if save:
            add("Supernatural Defense", "Supernatural Defense: your Slayer's Prey forced this save", "+1d6", "",
                ("dice", "1d6"))
        elif kind == "check" and skill in ("Athletics", "Acrobatics"):
            add("Supernatural Defense", "Supernatural Defense: escaping your Slayer's Prey's grapple", "+1d6", "",
                ("dice", "1d6"))
    if kind == "check" and skill == "Insight" and cl.get("Rogue", 0) >= 3 and "inquisitive" in _sub(char, "Rogue") \
            and state["d20"] <= 7:
        add("Ear for Deceit", "Ear for Deceit: telling whether a creature is lying", f"the {state['d20']} counts as 8",
            "", ("floor", 8))
    if cl.get("Monk", 0) >= 11 and "drunken" in _sub(char, "Monk") and state.get("disadvantage"):
        ki = _pool(char, "ki")
        if _left(ki) >= 2:
            add("Drunkard's Luck", "Drunkard's Luck: no disadvantage on this roll", "", f"2 ki ({_left(ki)} left)",
                ("note", "the disadvantage is cancelled"), [("pool", "ki", 2)])
    if cl.get("Cleric", 0) >= 2 and "strength" in _sub(char, "Cleric") and ability == "STR":
        # Strength Domain: after you see a Strength roll, before you know how it went
        cd = _pool(char, "cd")
        if _left(cd):
            add("Feat of Strength", "Feat of Strength", "+10", f"1 {_noun('cd', 1)} ({_left(cd)} left)", ("flat", 10),
                [("pool", "cd", 1)])
    if kind == "check" and skill in ("Intimidation", "Persuasion") and cl.get("Monk", 0) >= 3 \
            and "ascendant dragon" in _sub(char, "Monk") and reaction:
        r = _res(char, "Draconic Disciple: Reroll")
        if _left(r):
            add("Draconic Presence", "Draconic Presence: roll the check again", "",
                "your reaction; once a long rest, spent only if it then succeeds", ("reroll",),
                [("reaction",), ("defer", ("res", "Draconic Disciple: Reroll"))], section="fail")
    if attack:
        _attack_options(char, w, state, free, add, uses)
    # races and feats
    race = _race(char)
    if race.startswith("Autognome"):
        r = _res(char, "autognome_built_for_success")
        if _left(r):
            add("Built for Success", "Built for Success", "+1d4", uses(r), ("dice", "1d4"),
                [("res", "autognome_built_for_success")])
    if kind == "check" and skill and race.startswith("Reborn"):
        r = _res(char, "reborn_past_life")
        if _left(r):
            add("Knowledge from a Past Life", "Knowledge from a Past Life", "+1d6", uses(r), ("dice", "1d6"),
                [("res", "reborn_past_life")])
    if "Lucky" in feats:
        r = _res(char, "Luck Points")
        if _left(r):
            add("Lucky", "Lucky: roll another d20, keep the higher", "", f"1 luck point ({_left(r)} left)",
                ("extra",), [("res", "Luck Points")])
    if cl.get("Wizard", 0) >= 2 and "chronurgy" in _sub(char, "Wizard") and reaction:
        r = _res(char, "chronal_shift")
        if _left(r):
            add("Chronal Shift", "Chronal Shift: roll again, the new roll stands", "", f"your reaction; {uses(r)}",
                ("reroll",), [("res", "chronal_shift"), ("reaction",)], section="fail")
    # only once you know it fails
    if cl.get("Rogue", 0) >= 20 and (two or kind == "check" or attack):
        r = _res(char, "stroke_luck")
        if _left(r) and attack and not two:
            add("Stroke of Luck", "Stroke of Luck: the miss is a hit", "", "once a short or long rest",
                ("hit",), [("res", "stroke_luck")], section="fail")
        elif _left(r):
            add("Stroke of Luck", "Stroke of Luck: the d20 counts as a 20", "", "once a short or long rest",
                ("set20",), [("res", "stroke_luck")], section="fail")
    if kind == "check":
        if cl.get("Sorcerer", 0) >= 5 and ((char.get("_choices") or {}).get("optional_features", {})
                                           .get("Magical Guidance") or (char.get("optional_rules") or {})
                                           .get("magical_guidance")):
            sp = _pool(char, "sp")
            if _left(sp):
                add("Magical Guidance", "Magical Guidance: roll again, the new roll stands", "",
                    f"1 sorcery point ({_left(sp)} left)", ("reroll",), [("pool", "sp", 1)], section="fail")
        r = _res(char, "pact_of_the_talisman")
        if _left(r):
            add("Pact of the Talisman", "Pact of the Talisman", "+1d4", uses(r), ("dice", "1d4"),
                [("res", "pact_of_the_talisman")], section="fail")
        psi = _pool(char, "psi")
        if (w.get("tool") or (skill and _skill_prof(char, skill) >= 2)) and cl.get("Rogue", 0) >= 3 \
                and "soulknife" in _sub(char, "Rogue") and _left(psi):
            add("Psi-Bolstered Knack", "Psi-Bolstered Knack", f"+{_special_die(char, 'PSI')}",
                f"1 Psionic Energy die, spent only if the check then succeeds ({_left(psi)} left)",
                ("dice", "PSI"), [("defer", ("pool", "psi", 1))], section="fail")
        if two and cl.get("Fighter", 0) >= 2:
            r = _res(char, "second_wind")
            if _left(r):
                add("Tactical Mind", "Tactical Mind", "+1d10",
                    f"a Second Wind use, spent only if the check then succeeds ({uses(r)})",
                    ("dice", "1d10"), [("defer", ("res", "second_wind"))], section="fail")
    if kind != "initiative":
        for name, cap, card in (("Fortune from the Many", 3, "Hobgoblin (MPMM)"), ("Saving Face", 5, "Hobgoblin")):
            if race == card:
                r = _res(char, name)
                if _left(r):
                    add(name, f"{name}: +1 for each ally you can see within 30 ft", f"up to +{cap}", uses(r),
                        ("allies", cap), [("res", name)], section="fail")
    if (save or attack) and cl.get("Sorcerer", 0) >= 1 and "divine soul" in _sub(char, "Sorcerer"):
        r = _res(char, "favored_by_the_gods")
        if _left(r):
            add("Favored by the Gods", "Favored by the Gods", "+2d4", "once a short or long rest",
                ("dice", "2d4"), [("res", "favored_by_the_gods")], section="fail")
    if save:
        if cl.get("Fighter", 0) >= 9:
            r = _res(char, "indomitable")
            if _left(r):
                add("Indomitable", "Indomitable: roll the save again, the new roll stands"
                    + (f" (+{cl['Fighter']})" if two else ""), "", uses(r),
                    ("reroll", cl["Fighter"] if two else 0), [("res", "indomitable")], section="fail")
        if cl.get("Monk", 0) >= 14:
            ki = _pool(char, "ki")
            if _left(ki):
                add("Diamond Soul", "Diamond Soul: roll the save again, take the second", "", f"1 ki ({_left(ki)} left)",
                    ("reroll",), [("pool", "ki", 1)], section="fail")
        if cl.get("Barbarian", 0) >= 6 and "zealot" in _sub(char, "Barbarian") and "Rage" in fx \
                and "Fanatical Focus" not in ((char.get("_once_per") or {}).get("Rage") or []):
            add("Fanatical Focus", "Fanatical Focus: roll the save again, the new roll stands", "", "once a rage",
                ("reroll",), [("once_per", "Rage", "Fanatical Focus")], section="fail")
        if "Living Legend" in fx and reaction:
            add("Living Legend", "Living Legend: roll the save again, the new roll stands", "", "your reaction",
                ("reroll",), [("reaction",)], section="fail")
        if cl.get("Wizard", 0) >= 2 and "war magic" in _sub(char, "Wizard") and reaction:
            add("Arcane Deflection", "Arcane Deflection", "+4",
                "your reaction; only cantrips until the end of your next turn", ("flat", 4), [("reaction",)],
                section="fail")
        r = _res(char, "protection_of_the_talisman")
        if _left(r):
            add("Protection of the Talisman", "Protection of the Talisman", "+1d4", uses(r), ("dice", "1d4"),
                [("res", "protection_of_the_talisman")], section="fail")
        if ability == "DEX" and race.startswith("Harengon") and reaction \
                and "Prone" not in effective_conditions(char):
            add("Lucky Footwork", "Lucky Footwork", "+1d4", "your reaction", ("dice", "1d4"), [("reaction",)],
                section="fail")
        if race.startswith("Kender"):
            r = _res(char, "Fearless")
            if _left(r):
                add("Fearless", "Fearless: a save against being frightened succeeds instead", "", "once a long rest",
                    ("succeed",), [("res", "Fearless")], section="fail")
    used = set(state.get("used") or [])
    out = [o for o in out if o["key"] not in used]
    if attack and state.get("d20") == 1:
        # a natural 1 misses whatever's added to it: only a new d20 can help
        out = [o for o in out if o["does"][0] in ("reroll", "extra", "set20", "hit")]
    return out


def _attack_options(char, w, state, free, add, uses):
    """What only an attack roll takes: Guided Strike, Foe Slayer, and what
    turns a miss around (Focused Aim, Homing Strikes, Unerring Accuracy,
    Curving Shot, Living Legend)."""
    from dnd_app.core.actions import _optional_feature_enabled
    from dnd_app.core.weapons import is_monk_weapon
    cl, fx, turn = _cl(char), _fx(char), char.get("_turn_uses") or []
    two = char.get("edition") == "2024"
    row = w.get("row") or {}
    weapon = row.get("kind") != "spell"
    cd = _pool(char, "cd")
    guided = ((cl.get("Cleric", 0) >= (3 if two else 2) and "war" in _sub(char, "Cleric").split())
              or (cl.get("Paladin", 0) >= 3 and "conquest" in _sub(char, "Paladin")))
    if guided and _left(cd):
        # 2014: after you see the roll, before the DM says; 2024: once it misses
        add("Guided Strike", "Guided Strike", "+10", f"1 {_noun('cd', 1)} ({_left(cd)} left)", ("flat", 10),
            [("pool", "cd", 1)], section="fail" if two else "add")
    if not two and cl.get("Ranger", 0) >= 20 and "Foe Slayer" not in turn:
        wis = max(1, _mod(char, "WIS"))
        add("Foe Slayer", "Foe Slayer: the target is your favored enemy", f"+{wis}", "once a turn",
            ("flat", wis), [("turn", "Foe Slayer")])
    ki = _pool(char, "ki")
    if cl.get("Monk", 0) >= 5 and _left(ki) and _optional_feature_enabled(char, "Focused Aim"):
        n = min(3, _left(ki))
        add("Focused Aim", "Focused Aim: +2 for each ki point you spend", f"up to +{2 * n}",
            f"1 to {n} ki ({_left(ki)} left)" if n > 1 else f"1 ki ({_left(ki)} left)", ("ki_aim", n),
            section="fail")
    psi = _pool(char, "psi")
    if row.get("name") == "Psychic Blade" and cl.get("Rogue", 0) >= 9 and "soulknife" in _sub(char, "Rogue") \
            and _left(psi):
        add("Homing Strikes", "Homing Strikes", f"+{_special_die(char, 'PSI')}",
            f"1 Psionic Energy die, spent only if it then hits ({_left(psi)} left)", ("dice", "PSI"),
            [("defer", ("pool", "psi", 1))], section="fail")
    if cl.get("Monk", 0) >= 17 and "kensei" in _sub(char, "Monk") and "Unerring Accuracy" not in turn \
            and is_monk_weapon(char, row.get("name", "")):
        add("Unerring Accuracy", "Unerring Accuracy: roll the attack again", "", "once a turn", ("reroll",),
            [("turn", "Unerring Accuracy")], section="fail")
    if cl.get("Fighter", 0) >= 7 and "arcane archer" in _sub(char, "Fighter") \
            and row.get("base") in ("Shortbow", "Longbow") and "Bonus Action" in free:
        add("Curving Shot", "Curving Shot: roll again, against another target within 60 ft of this one", "",
            "your bonus action", ("reroll",), [("bonus",)], section="fail")
    if "Living Legend" in fx and weapon and "Living Legend" not in turn:
        add("Living Legend", "Living Legend: the miss is a hit", "", "once a turn", ("hit",),
            [("turn", "Living Legend")], section="fail")


def _report(char, w, state, free):
    """The roll dialog: the roll, then what you can add."""
    kind = w["kind"]
    noun = {"check": "CHECK", "initiative": "ROLL", "save": "SAVE", "concentration": "SAVE"}[kind]
    options = _after_options(char, w, state, free)
    if kind == "concentration" and state["total"] >= w.get("dc", 10):
        options = []                       # it's kept: nothing to add
    # each is added the moment you press its Add: the total updates, and
    # you can add another
    sections = [{"name": n, "title": t, "now": True}
                for n, t in (("add", f"ADD TO THIS {noun}"), ("fail", "IF IT FAILS"))
                if any(o["section"] == n for o in options)]
    line, verdict = _lines(char, w, state)
    rinfo = {"total": state["total"], "d20": state["d20"], "mod": f"{int(w.get('bonus', 0) or 0):+d}",
             "note": "\n".join(x for x in (state.get("reminder", ""), *state["notes"]) if x),
             "crit": state["d20"] == 20 and state["raw"] == 20, "nat1": state["raw"] == 1, "nat20": state["raw"] == 20,
             "line": line, "verdict": verdict}
    public = [dict({k: v for k, v in o.items() if k not in ("does", "pay")}, now=True) for o in options]
    state["free"] = list(free)
    return {"title": w["label"], "kind": "check", "roll": rinfo, "total_label": "total",
            "hit": [], "hit_title": "", "attacks": "", "options": public, "sections": sections,
            "hit_button": "Done", "miss_button": "", "message": _toast_text(char, w, state),
            "state": {"what": dict(w), "roll": copy_state(state)}}


def copy_state(state) -> dict:
    """A roll's state to change without touching the one it came from."""
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in state.items()}
    out["auto"] = [dict(p) for p in state.get("auto") or []]
    out["flat"] = [dict(p) for p in state.get("flat") or []]
    out["pending"] = [list(p) for p in state.get("pending") or []]
    return out


def roll_options(char, w, state, free) -> list:
    """What you can add to this roll now, for a dialog to show (core/attacks.py
    attack_report): {key, title, dice, cost, section ("add"/"fail")...}."""
    return [{k: v for k, v in o.items() if k not in ("does", "pay")} for o in _after_options(char, w, state, free)]


def roll_line(w, state) -> str:
    """"Rolled 14 + 7 + 3 (Bless)" -- how the total was made."""
    d = state["dice"]
    if state.get("portent") is not None:
        first = f"Portent: {state['portent']}"
    elif state.get("adv") and len(d) > 1:
        first = f"Rolled {d[0]} and {d[1]} with advantage ({state['adv']}): {max(d)}"
    else:
        first = f"Rolled {d[0]}"
    if state.get("floor"):
        first += f" ({state['floor']})"
    if state.get("set20"):
        first += " (it counts as a 20)"
    bonus = int(w.get("bonus", 0) or 0)
    parts = [first] + ([f"{bonus:+d}".replace("+", "+ ").replace("-", "− ")] if bonus or not _is_attack(w) else [])
    for p in state["auto"]:
        v = p.get("value", 0) * p.get("sign", 1)
        parts.append(f"{'+' if v >= 0 else '−'} {abs(v)} ({p['source']})")
    for p in state["flat"]:
        parts.append(f"{'+' if p['value'] >= 0 else '−'} {abs(p['value'])} ({p['source']})")
    line = " ".join(parts)
    if state.get("mighty"):
        line += f". {state['mighty']}"
    return line


def _lines(char, w, state):
    """("Rolled 14 + 7 + 3 (Bless)", "Beats a DC of 24 or lower")."""
    line = roll_line(w, state)
    total, kind = state["total"], w["kind"]
    if state.get("succeed"):
        verdict = "It succeeds"
    elif kind == "concentration":
        dc, spell = w.get("dc", 10), w.get("spell") or "the spell"
        verdict = (f"DC {dc}: you keep concentrating on {spell}" if total >= dc
                   else f"DC {dc}: {total} is under it -- add something, or {spell} ends")
    elif kind == "initiative":
        verdict = "Your place in the initiative order"
    elif kind == "save":
        verdict = f"Saves against a DC of {total} or lower"
    else:
        verdict = f"Beats a DC of {total} or lower"
    return line, verdict.replace(" -- ", " — ")


def _toast_text(char, w, state) -> str:
    line, verdict = _lines(char, w, state)
    flair = "  NAT 20!" if state["raw"] == 20 else "  Nat 1…" if state["raw"] == 1 else ""
    out = [f"{w['label']}: {state['total']}{flair}", line.replace(" — ", " -- ")]
    if w["kind"] == "concentration" or state.get("succeed"):
        out.append(verdict.replace(" — ", " -- "))
    if state["spent"]:
        out.append("Spent: " + " · ".join(state["spent"]))
    out += [n for n in state["notes"] if n]
    if state.get("reminder"):
        out.append(state["reminder"])
    return "\n".join(out)


def _new_state():
    """used: what's been added (each once a roll); pending: what's paid
    only if the roll then succeeds (Homing Strikes), as [key, pay];
    succeed: what made it succeed outright (Stroke of Luck), or ""."""
    return {"dice": [], "auto": [], "flat": [], "spent": [], "notes": [], "slots": [], "adv": "",
            "portent": None, "cast": "", "set20": False, "succeed": "", "floor": "", "mighty": "",
            "used": [], "pending": []}


def roll_check(char: dict, what: dict, answers=None, free=("Action", "Bonus Action", "Reaction"), rng=None) -> dict:
    """See the module docstring."""
    from dnd_app.core.calculator import condition_roll_mode
    rng = rng or random
    answers = answers if answers is not None else {}
    w = dict(what)
    if w.get("tool"):
        from dnd_app.core.calculator import get_tool_bonus
        if not w.get("ability"):
            opts = _tool_ability_options(char, w["tool"])
            pick = next((a for a, label in opts if label == answers.get("tool_ability")), None)
            if pick is None:
                return {"ok": False, "ask": {"key": "tool_ability", "title": f"{w['tool']}: which ability? "
                                             f"(your DM says)", "options": [label for _, label in opts]}}
            w["ability"] = pick
        w["bonus"] = get_tool_bonus(char, w["tool"], w["ability"])
        w["label"] = f"{w['tool']} check ({w['ability']})"
    w.setdefault("ability", "DEX" if w["kind"] == "initiative" else "CON" if w["kind"] == "concentration" else "")
    if w["kind"] == "check" and w.get("skill") and not w.get("ability"):
        from dnd_app.core.calculator import SKILL_ABILITY
        w["ability"] = SKILL_ABILITY.get(w["skill"], "")
    free = list(free)
    if "_state" not in answers:
        cm = condition_roll_mode(char, "save" if _is_save(w) else "check", w["ability"])
        if cm["mode"] == "auto_fail":
            out = {"ok": True, "toast": f"{w['label']}: automatic failure ({', '.join(cm['sources'])})",
                   "slots": [], "refresh": False}
            if w["kind"] == "concentration":
                from dnd_app.core.magic_items import drop_concentration
                drop_concentration(char)
                out["toast"] += f" -- you stop concentrating on {w.get('spell') or 'the spell'}"
                out["refresh"] = True
            return out
        ask = before_question(char, w, free)
        if ask and "before" not in answers:
            return {"ok": False, "ask": ask}
        pick = next((k for k, label in _before_options(char, w, free) if label == answers.get("before")), None)
        answers["_state"] = _start(char, w, pick, free, rng)
    state = answers["_state"]
    out = {"ok": True, "slots": list(state["slots"]), "refresh": bool(state["spent"] or state["cast"]),
           "cast": state["cast"]}
    report = _report(char, w, state, free)
    if report["options"]:
        out["report"] = report
        return out
    _finish(char, w, state, out)
    return out


def _finish(char, w, state, out):
    """A concentration save under its DC drops the spell (unless you have
    advantage the sheet knows of: then your second d20 is your call)."""
    if w["kind"] == "concentration" and not state.get("succeed"):
        dc = w.get("dc", 10)
        if state["total"] < dc:
            from dnd_app.core.calculator import roll_reminder
            known_adv = roll_reminder(char, "concentration")["advantage"]
            if known_adv and not state.get("adv"):
                state["notes"].append(f"With advantage ({', '.join(known_adv)}), roll your second d20: if it doesn't "
                                      f"save it either, drop the spell")
            else:
                from dnd_app.core.magic_items import drop_concentration
                drop_concentration(char)
                state["notes"].append(f"You stop concentrating on {w.get('spell') or 'the spell'}")
                out["refresh"] = True
    out["toast"] = _toast_text(char, w, state)


def add_option(char, w, state, key, answers, free, rng) -> dict:
    """One option added to a roll now (a check's, a save's or an attack's):
    asked about first if it needs it (how many allies, how many ki), then
    paid for and rolled, and the total settled -- `state` changes in place.
    {"ok", "slots": parts of the turn it used, "ask"?, "toast"?}"""
    o = {x["key"]: x for x in _after_options(char, w, state, free)}.get(key)
    if o is None:
        return {"ok": False, "toast": f"{key}: you can't add it now", "slots": []}
    does, pay = o["does"], list(o["pay"])
    if does[0] == "allies":
        choices = [str(n) for n in range(1, does[1] + 1)]
        if answers.get(f"{key}:allies") not in choices:
            return {"ok": False, "slots": [], "ask": {"key": f"{key}:allies", "options": choices,
                                                     "title": f"{key}: how many allies can you see within 30 ft?"}}
    if does[0] == "ki_aim":
        choices = [f"{n} ki: +{2 * n}" for n in range(1, does[1] + 1)]
        got = answers.get(f"{key}:ki")
        if got not in choices:
            return {"ok": False, "slots": [], "ask": {"key": f"{key}:ki", "options": choices,
                                                     "title": f"{key}: how many ki points?"}}
        n = int(got.split()[0])
        does, pay = ("flat", 2 * n), [("pool", "ki", n)]
    before = len(state["slots"])
    spent = _pay(char, key, pay, state)
    _apply(char, w, state, key, does, answers, rng)
    if spent:
        state["spent"].append(spent)
    state["used"].append(key)
    _settle(char, w, state)
    return {"ok": True, "slots": list(state["slots"][before:])}


def add_to_check(char: dict, report: dict, key, answers=None, free=None, rng=None) -> dict:
    """See the module docstring."""
    answers = answers if answers is not None else {}
    w = dict(report["state"]["what"])
    state = copy_state(report["state"]["roll"])
    free = list(free) if free is not None else list(state.get("free") or ("Action", "Bonus Action", "Reaction"))
    res = add_option(char, w, state, key, answers, free, rng or random)
    if not res["ok"]:
        return res
    return {"ok": True, "report": _report(char, w, state, free), "slots": res["slots"], "refresh": True,
            "cast": ""}


def pay_pending(char, w, state, succeeded) -> None:
    """What's paid only if the roll succeeds (Homing Strikes, Psi-Bolstered
    Knack): paid now if it did, kept if it didn't."""
    for key, item in state.get("pending") or []:
        if succeeded:
            said = _pay(char, key, [tuple(item)], state)
            if said:
                state["spent"].append(said)
        else:
            state["notes"].append(f"{key}: it {'missed' if _is_attack(w) else 'failed'}, so it isn't spent")
    state["pending"] = []


def finish_check(char: dict, report: dict, answers=None) -> dict:
    """See the module docstring."""
    answers = answers if answers is not None else {}
    w = dict(report["state"]["what"])
    state = copy_state(report["state"]["roll"])
    out = {"ok": True, "slots": [], "refresh": bool(state["spent"] or state["cast"]), "cast": ""}
    if state["pending"]:
        if w["kind"] == "concentration":
            ok = bool(state["succeed"]) or state["total"] >= w.get("dc", 10)
        else:
            choices = ["It succeeded", "It still failed"]
            got = answers.get("succeeded")
            if got not in choices:
                names = " and ".join(k for k, _ in state["pending"])
                return {"ok": False, "ask": {"key": "succeeded", "options": choices,
                                             "title": f"{w['label']}: did it succeed? ({names} is spent only "
                                                      f"if it did)"}}
            ok = got == choices[0]
        pay_pending(char, w, state, ok)
        out["refresh"] = True
    _finish(char, w, state, out)
    return out


def take_check_options(char: dict, report: dict, picked, answers=None, rng=None) -> dict:
    """See the module docstring: each picked option added (rerolls first),
    then Done. `answers` keeps what's been paid between rounds of questions
    (nothing is paid twice)."""
    rng = rng or random
    answers = answers if answers is not None else {}
    cur = answers.setdefault("_report", report)
    slots = answers.setdefault("_slots", [])
    st = cur["state"]["roll"]
    offered = {o["key"]: o for o in _after_options(char, dict(cur["state"]["what"]), st,
                                                   st.get("free") or ("Action", "Bonus Action", "Reaction"))}
    order = {"reroll": 0, "extra": 1, "set20": 2}
    keys = sorted((k for k in picked if k in offered), key=lambda k: order.get(offered[k]["does"][0], 3))
    for key in keys:
        done = f"{key}:done"
        if done in answers:
            continue
        res = add_to_check(char, answers["_report"], key, answers, rng=rng)
        if res.get("ask"):
            return res
        if res.get("ok"):
            answers["_report"] = res["report"]
            slots += res["slots"]
        answers[done] = True
    out = finish_check(char, answers["_report"], answers)
    if out.get("ask"):
        return out
    out["slots"] = list(slots) + out["slots"]
    out["refresh"] = out["refresh"] or bool(keys)
    return out


def _pay(char, key, pay, state) -> str:
    """Spend it; returns what was spent, for the toast."""
    said = []
    for item in pay:
        kind = item[0]
        if kind == "res":
            r = _res(char, item[1])
            if r is not None and str(r.get("current_max")).lower() != "unlimited":
                r["current"] = max(0, _left(r) - 1)
            name = str((r or {}).get("name") or "")
            what = f"{key}: {name}" if name and name.lower() != key.lower() else key
            said.append(f"{what} ({_left(r)} left)" if r is not None and _left(r) < 99 else what)
        elif kind == "pool":
            p = _pool(char, item[1])
            if p is not None and str(p.get("current_max")).lower() != "unlimited":
                p["current"] = max(0, _left(p) - item[2])
            said.append(f"{item[2]} {_noun(item[1], item[2])} ({_left(p)} left)")
        elif kind == "reaction":
            state["slots"].append("Reaction")
            said.append("your reaction")
        elif kind == "bonus":
            state["slots"].append("Bonus Action")
            said.append("your bonus action")
        elif kind == "inspiration":
            char["inspiration"] = False
            said.append("your Heroic Inspiration")
        elif kind == "turn":
            char.setdefault("_turn_uses", []).append(item[1])
            said.append(f"{key} for this turn")
        elif kind == "once_per":
            char.setdefault("_once_per", {}).setdefault(item[1], []).append(item[2])
        elif kind == "defer":
            # paid only if the roll then succeeds (pay_pending)
            state["pending"].append([key, list(item[1])])
        elif kind == "fx_end":
            name = item[1]
            char["active_effects"] = [n for n in _fx(char) if n != name]
            (char.get("effect_details") or {}).pop(name, None)
            conc = char.get("concentration") or {}
            if conc.get("spell") == name:
                conc["spell"], conc["since_round"] = None, 0
            said.append(f"{name} (it ends)")
    return " and ".join(dict.fromkeys(said))


def _apply(char, w, state, key, does, answers, rng):
    from dnd_app.core.action_use import evaluate
    kind = does[0]
    if kind == "dice":
        expr = does[1]
        if expr in ("SD", "BI", "PSI"):
            value, how = evaluate(char, expr, rng=rng)
            die = how or expr
        else:
            n, s = map(int, expr.split("d"))
            value, die = sum(rng.randint(1, s) for _ in range(n)), expr
        state["auto"].append({"source": key, "dice": die, "sign": 1, "value": value})
    elif kind == "flat":
        state["flat"].append({"source": key, "value": does[1]})
    elif kind == "allies":
        state["flat"].append({"source": key, "value": int(answers.get(f"{key}:allies", 1))})
    elif kind == "reroll":
        before = state["dice"][0] if len(state["dice"]) == 1 else max(state["dice"])
        new = _d20(char, rng, state["notes"])
        state["dice"], state["adv"], state["portent"] = [new], "", None
        state["notes"].append(f"{key}: rolled again, {new} (was {before})")
        if len(does) > 1 and does[1]:
            state["flat"].append({"source": key, "value": does[1]})
    elif kind == "extra":
        cur = state["portent"] if state.get("portent") is not None else (
            max(state["dice"]) if state["adv"] else state["dice"][0])
        new = _d20(char, rng, state["notes"])
        keep = max(cur, new)
        state["notes"].append(f"Lucky: your other d20 is {new}; you keep {keep}")
        state["dice"], state["adv"], state["portent"] = [keep], "", None
    elif kind == "set20":
        state["set20"] = True
    elif kind == "floor":
        if state["d20"] < does[1]:
            state["notes"].append(f"{key}: the {state['raw']} counts as {does[1]}")
            state["portent"], state["adv"] = None, ""
            state["dice"] = [does[1]]
    elif kind in ("succeed", "hit"):
        state["succeed"] = key
    elif kind == "note":
        state["notes"].append(f"{key}: {does[1]}")
