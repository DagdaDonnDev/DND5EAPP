"""Being another creature: Wild Shape, Polymorph, True Polymorph and
Shapechange, the same on both apps. One form at a time:

    char["_wildshape_active"]  the creature you are (a Bestiary name)
    char["_form_kind"]         how: "Wild Shape" (or none, an older save),
                               "Polymorph", "True Polymorph", "Shapechange"
    char["_wildshape_hp"]      the form's hit points

What each keeps (the 2014 rules):
  Wild Shape     the form's STR, DEX and CON; your own INT, WIS, CHA,
                 proficiencies, class features and racial traits (if the
                 form can use them). No concentration: you can hold a
                 spell. Wild Shape uses.
  Polymorph      everything is the form's, INT/WIS/CHA too: no class
  True Polymorph features, feats or spells; you can't speak or use hands.
                 A spell, held by concentration: when it ends, so does
                 the form.
  Shapechange    the form's physical statistics; your INT, WIS, CHA,
                 class features and spells (if the form can cast). A
                 spell, held by concentration.
In every form you use its hit points; at 0 you change back, and the
damage left over carries on to your own (the apps' Damage buttons).

The form's stat block is data/statblocks.py's (WILDSHAPE_BEASTS: any
Bestiary creature).
"""
from __future__ import annotations

KINDS = ("Wild Shape", "Polymorph", "True Polymorph", "Shapechange")
SPELL_FORMS = ("Polymorph", "True Polymorph", "Shapechange")


def form_name(char: dict) -> str:
    return char.get("_wildshape_active") or ""


def form_kind(char: dict) -> str:
    """"" when you're yourself; else one of KINDS."""
    if not form_name(char):
        return ""
    return char.get("_form_kind") or "Wild Shape"


def statblock(name: str) -> dict | None:
    from dnd_app.data.statblocks import WILDSHAPE_BEASTS
    return WILDSHAPE_BEASTS.get(name) if name else None


def form_statblock(char: dict) -> dict | None:
    return statblock(form_name(char))


def replaces_mind(char: dict) -> bool:
    """Polymorph and True Polymorph: the form's INT, WIS and CHA, its saves
    and skills, and none of your features or spells."""
    return form_kind(char) in ("Polymorph", "True Polymorph")


def keeps_features(char: dict) -> bool:
    return form_kind(char) not in ("Polymorph", "True Polymorph")


def options(char: dict, kind: str, level: int = 0) -> list:
    """The creatures a casting can make you (or another creature of `level`),
    strongest first:
      Polymorph       a beast of CR up to the target's level (or CR)
      True Polymorph  any creature of CR up to the target's level
      Shapechange     any creature of CR up to your level that isn't a
                      construct or undead"""
    from dnd_app.core.calculator import total_level
    from dnd_app.data.bestiary import bestiary
    cap = level or total_level(char)
    out = []
    for name, c in bestiary().items():
        t = (c.get("type") or "")
        if c.get("cr_value", 0) > cap:
            continue
        if kind == "Polymorph" and t != "Beast":
            continue
        if kind == "Shapechange" and t in ("Construct", "Undead"):
            continue
        out.append(name)
    return sorted(out, key=lambda n: (-bestiary()[n].get("cr_value", 0), n))


def take_form(char: dict, name: str, kind: str = "Wild Shape") -> tuple:
    """Become `name`. Returns (ok, message)."""
    from dnd_app.data.statblocks import WILDSHAPE_BEASTS
    sb = statblock(name)
    if not sb:
        return False, f"{name} isn't a creature in the Bestiary"
    name = WILDSHAPE_BEASTS.resolve(name)
    char["_wildshape_active"] = name
    char["_form_kind"] = kind
    char["_wildshape_hp"] = sb.get("hp", 1)
    fx = char.setdefault("active_effects", [])
    if kind == "Wild Shape" and "Wild Shape" not in fx:
        fx.append("Wild Shape")
    from dnd_app.core.hp_undo import clear_hp_undo
    clear_hp_undo(char)
    keeps = ("your Intelligence, Wisdom and Charisma, and your features" if keeps_features(char)
             else "only your alignment and personality: no features or spells, no speech or hands")
    return True, f"{kind}: you're a {name} ({sb['hp']} hit points, AC {sb['ac']}), keeping {keeps}"


def leave_form(char: dict, end_spell: bool = True) -> str:
    """Back to yourself. A spell's form ends that spell too (and the
    concentration it took). Returns what you were ("" if nothing)."""
    name, kind = form_name(char), form_kind(char)
    if not name:
        return ""
    char["_wildshape_active"] = None
    char.pop("_wildshape_hp", None)
    char.pop("_form_kind", None)
    fx = char.setdefault("active_effects", [])
    if "Wild Shape" in fx:
        fx.remove("Wild Shape")
    if end_spell and kind in SPELL_FORMS and kind in fx:
        fx.remove(kind)
        (char.get("effect_details") or {}).pop(kind, None)
        conc = char.get("concentration") or {}
        if conc.get("spell") == kind:
            conc["spell"], conc["since_round"] = None, 0
    from dnd_app.core.hp_undo import clear_hp_undo
    clear_hp_undo(char)
    return name


def keep_in_step(char: dict) -> None:
    """A spell's form lasts as long as the spell: once it's no longer on
    you (concentration broken, its time up, ended), you change back.
    calculator.update_all calls this."""
    kind = form_kind(char)
    if kind in SPELL_FORMS and kind not in (char.get("active_effects") or []):
        leave_form(char, end_spell=False)


def form_cards(char: dict) -> list:
    """The form's own actions, bonus actions, reactions and traits as
    action cards: [(bucket, (name, text, source))]. Its attacks are attack
    rows (core/attacks.py), so only what isn't one is here -- Multiattack,
    a breath weapon, a recharge ability."""
    sb = form_statblock(char)
    if not sb:
        return []
    src = f"{form_name(char)} ({form_kind(char)})"
    attacks = set(sb.get("attack_data") or {})
    out = []
    for bucket, key in (("Action", "actions"), ("Bonus Action", "bonus_actions"), ("Reaction", "reactions")):
        for n, text in sb.get(key, []):
            if n in attacks and (sb["attack_data"][n] or {}).get("to_hit") is not None:
                continue
            out.append((bucket, (n, text, src)))
    for n, text in sb.get("traits", []):
        out.append(("Passive", (n, text, src)))
    return out


def form_save(char: dict, ability: str) -> int | None:
    """Polymorph's saving throw: the form's own (its listed bonus, else
    its ability modifier). None when the form keeps your saves."""
    if not replaces_mind(char):
        return None
    sb = form_statblock(char) or {}
    from dnd_app.data.bestiary import get_creature
    c = get_creature(form_name(char)) or {}
    saves = {k.upper()[:3]: v for k, v in (c.get("saves") or {}).items()}
    if ability in saves:
        return int(saves[ability])
    return ((sb.get("abilities") or {}).get(ability, 10) - 10) // 2


def form_skill(char: dict, skill: str, ability: str) -> int | None:
    """Polymorph's skill check: the form's own (its listed bonus, else its
    ability modifier). None when the form keeps your skills."""
    if not replaces_mind(char):
        return None
    sb = form_statblock(char) or {}
    for n, v in sb.get("skills", []):
        if n.lower() == skill.lower():
            return int(str(v).replace("+", ""))
    return ((sb.get("abilities") or {}).get(ability, 10) - 10) // 2


# ── Polymorphed by someone else ───────────────────────────────────────────
ALLY_FORMS = ("Polymorph", "True Polymorph")


def ally_form_question(char: dict, kind: str, answers: dict):
    """An ally's Polymorph (or True Polymorph) put on you from the Effects
    tab: the creature they chose for you. Returns {"ask": ...} until it's
    picked, then {"form": name}. The caster's level decides the CR, so
    every creature the spell allows is offered."""
    if answers.get("form"):
        return {"form": answers["form"]}
    return {"ask": {"key": "form", "title": f"{kind}: which creature did they make you?",
                    "options": options(char, kind, level=30)}}


def become_ally_form(char: dict, kind: str, form: str) -> str:
    """You're in the form an ally's spell gave you (its effect is on you;
    it ends when they stop concentrating -- end it from the Effects tab).
    Returns the message."""
    fx = char.setdefault("active_effects", [])
    if kind not in fx:
        fx.append(kind)
    char.setdefault("effect_details", {})[kind] = {"form": form, "by": "an ally"}
    ok, msg = take_form(char, form, kind)
    return msg if ok else f"{kind}: {msg}"
