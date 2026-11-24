"""The new-character wizard, shared by both apps.

Six steps, the same on desktop (ui_desktop/pages/wizard.py) and Android
(ui_android/bridge/wizard.py):

  1. Race                 race_rows(), race_card()
  2. Abilities            bonus_plan(), totals(), commit_abilities()
  3. Class & Background   class_tiles(), class_chips(), background_rows(),
                          background_card()
  4. Spells & Choices     level1_cards(), apply_level1(), spell_plan()
                          ("Choices" for a class with no spells; skipped
                          when there's nothing at all to pick)
  5. Equipment            equipment_groups(), resolve_equipment(),
                          kit_preview()
  6. Summary              summary()

Everything here works on the character dict the wizard is building; the
apps only lay it out.
"""
import copy
import random
import re

from dnd_app.core.builder import (
    rebuild, apply_choice, get_choices_needed, race_requires_subrace, ABILITIES,
    get_race_skills, get_background_skills,
)
from dnd_app.data.races import (
    RACE_NAMES, RACE_DICT, combined_racial_asi, race_flex, race_languages,
    DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE,
)
from dnd_app.data.classes import CLASS_NAMES, CLASS_DICT
from dnd_app.data.backgrounds import BACKGROUND_NAMES, get_background

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_TOTAL = 27
METHODS = ["Standard Array", "Point Buy", "Roll", "Enter scores"]
ALIGNMENTS = ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "True Neutral",
              "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"]
STEPS = ["Race", "Abilities", "Class & Background", "Spells & Choices", "Equipment", "Summary"]

ELADRIN_SEASONS = [
    ("Autumn", "charm one creature within 5 ft of your destination"),
    ("Winter", "frighten one creature within 5 ft of your destination"),
    ("Spring", "a willing creature within 5 ft can teleport with you"),
    ("Summer", "2d6 fire damage to each creature within 5 ft of your origin"),
]
SIMIC_ENHANCEMENTS = [
    ("Manta Glide", "glide and fall slowly"),
    ("Nimble Climber", "climbing speed equal to walking"),
    ("Underwater Adaptation", "breathe water, swim speed"),
]


def mod_text(score: int) -> str:
    m = (score - 10) // 2
    return f"+{m}" if m >= 0 else str(m)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Race
# ═══════════════════════════════════════════════════════════════════════════
SOURCE_GROUPS = [("All", None), ("PHB", {"PHB"}), ("Volo's", {"VGM"}),
                 ("Multiverse", {"MPMM"}), ("Other", "other")]


def _in_group(source: str, group: str) -> bool:
    want = dict(SOURCE_GROUPS).get(group)
    if want is None:
        return True
    if want == "other":
        return not any(source in s for _, s in SOURCE_GROUPS if isinstance(s, set))
    return source in want


def _asi_short(rdata: dict) -> str:
    asi = rdata.get("asi", {}) or {}
    if len(asi) == 6 and set(asi.values()) == {1}:
        return "+1 to all"
    parts = [f"{ab} +{v}" for ab, v in asi.items()]
    flex = rdata.get("asi_flex", 0)
    if flex:
        if rdata.get("asi_flex_style", "distribute") == "each":
            parts.append(f"+1 ×{flex}")
        else:
            parts.append("+2 · +1 any")
    if not parts and rdata.get("subraces"):
        return "by subrace"
    return " · ".join(parts)


def race_rows(search: str = "", group: str = "All") -> list:
    """The race browser's rows: [{name, source, asi, speed}]."""
    q = (search or "").strip().lower()
    out = []
    for name in RACE_NAMES:
        r = RACE_DICT.get(name, {})
        if q and q not in name.lower():
            continue
        if not _in_group(r.get("source", "PHB"), group):
            continue
        out.append({"name": name, "source": r.get("source", "PHB"),
                    "asi": _asi_short(r), "speed": f"{r.get('speed', 30)} ft"})
    return out


def _subrace_full(race: str, sub: str):
    for s in RACE_DICT.get(race, {}).get("subraces", []):
        if s.split("(")[0].strip() == sub:
            return s
    return None


def _split_trait(t: str) -> tuple:
    for sep in (" – ", " — ", ": "):
        if sep in t:
            a, b = t.split(sep, 1)
            if len(a) <= 40:
                return a.strip(), b.strip()
    return t.strip(), ""


def race_card(race: str, sub: str = "") -> dict:
    """What the race details half (desktop) or page (Android) shows:
      name, source, chips [{text, kind}] (kind teal: its ability bonuses),
      subraces [names], subrace_required, subrace (the chosen one),
      traits [{name, text}], and the extra picks some races have:
      ancestry [{name, sub}] (a dragonborn's), seasons, simic."""
    r = RACE_DICT.get(race, {})
    if not r:
        return {}
    chips = []
    full = _subrace_full(race, sub)
    asi_desc = ""
    sub_traits = []
    if full:
        inner = full[full.find("(") + 1: full.rfind(")")]
        segs = [s.strip() for s in inner.split(";") if s.strip()]
        asi_desc = segs[0].lstrip("–").strip() if segs else ""
        sub_traits = segs[1:]
    if asi_desc:
        for part in re.split(r",\s*(?:and\s+)?", asi_desc):
            if part:
                chips.append({"text": part.strip(), "kind": "teal"})
    else:
        asi = r.get("asi", {}) or {}
        if len(asi) == 6 and set(asi.values()) == {1}:
            chips.append({"text": "+1 to all", "kind": "teal"})
        else:
            for ab, v in asi.items():
                chips.append({"text": f"{ab} +{v}", "kind": "teal"})
        flex = r.get("asi_flex", 0)
        if flex:
            each = r.get("asi_flex_style", "distribute") == "each"
            chips.append({"text": (f"+1 to {'two' if flex == 2 else flex} you pick" if each
                                   else "+2 and +1, you pick"), "kind": "teal"})
        if not asi and not flex and r.get("subraces"):
            chips.append({"text": "bonus by subrace", "kind": "teal"})
    chips.append({"text": f"Speed {r.get('speed', 30)} ft", "kind": ""})
    chips.append({"text": r.get("size", "Medium"), "kind": ""})
    for t in r.get("traits", []):
        m = re.match(r"(Superior )?Darkvision\D*(\d+)", t)
        if m:
            chips.append({"text": f"Darkvision {m.group(2)} ft", "kind": ""})
            break
    langs = [l for l in race_languages(race, sub)]
    extra = any("choice" in l.lower() for l in r.get("languages", []))
    if langs:
        chips.append({"text": ", ".join(langs) + (" +1" if extra else ""), "kind": ""})
    traits = []
    for t in r.get("traits", []):
        n, txt = _split_trait(t)
        traits.append({"name": n, "text": txt})
    for t in sub_traits:
        n, txt = _split_trait(t)
        traits.append({"name": n, "text": txt, "sub": sub})
    card = {"name": race, "source": r.get("source", "PHB"), "chips": chips,
            "subraces": [s.split("(")[0].strip() for s in r.get("subraces", [])],
            "subrace_required": race_requires_subrace(race), "subrace": sub,
            "traits": traits, "ancestry": [], "seasons": [], "simic": []}
    if race == "Dragonborn":
        for anc in ANCESTRY_BY_SUBRACE.get(sub or "Standard", ANCESTRY_BY_SUBRACE["Standard"]):
            card["ancestry"].append({"name": anc.split(" (")[0], "value": anc,
                                     "sub": DRACONIC_ANCESTRY[anc][0].lower()})
    if sub == "Eladrin":
        card["seasons"] = [{"name": n, "value": n, "sub": d} for n, d in ELADRIN_SEASONS]
    if race == "Simic Hybrid":
        card["simic"] = [{"name": n, "value": n, "sub": d} for n, d in SIMIC_ENHANCEMENTS]
    return card


def race_block_reason(race: str, sub: str, picks: dict) -> str:
    """Why Next can't go on from the Race step yet ("" when it can).
    picks: {"ancestry", "season", "simic"}."""
    if not race:
        return "Choose a race."
    if race_requires_subrace(race) and not sub:
        return f"Choose a subrace: the {race}'s ability bonus comes from it."
    card = race_card(race, sub)
    if card.get("ancestry") and not picks.get("ancestry"):
        return "Choose your draconic ancestry."
    if card.get("seasons") and not picks.get("season"):
        return "Choose your Eladrin season."
    if card.get("simic") and not picks.get("simic"):
        return "Choose your animal enhancement."
    return ""


def commit_race(char: dict, race: str, sub: str, picks: dict) -> None:
    char["race"] = race
    char["species"] = race
    char["subrace"] = sub
    card = race_card(race, sub)
    char["draconic_ancestry"] = picks.get("ancestry", "") if card.get("ancestry") else ""
    char["eladrin_season"] = picks.get("season", "") if card.get("seasons") else ""
    char["simic_enhancement_1st"] = picks.get("simic", "") if card.get("simic") else ""
    r = RACE_DICT.get(race, {})
    char["species_traits"] = r.get("traits", [])
    char.setdefault("languages", ["Common"])
    for lang in r.get("languages", []):
        if lang not in char["languages"] and "your choice" not in lang.lower():
            char["languages"].append(lang)
    rebuild(char)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Abilities
# ═══════════════════════════════════════════════════════════════════════════
def bonus_plan(char: dict) -> dict:
    """The race's ability bonuses, as the Abilities card shows them:
      fixed     {ab: n} it simply gives
      points    the +1s you place yourself (0 for none)
      max_per   most of those on one ability (1, or 2 for "+2 and +1")
      exclude   abilities they can't go on
      choice    the Choices id they're kept under ("" when they're added
                to the scores, as a half-elf's are)
      text      "Half-Elf: CHA +2, and +1 to any two others" """
    race, sub = char.get("race", ""), char.get("subrace", "")
    fixed = combined_racial_asi(char)
    flex, style = race_flex(race, sub)
    plan = {"fixed": fixed, "points": 0, "max_per": 1, "exclude": [], "choice": ""}
    if flex:
        if flex == 2 and style == "distribute":
            plan.update(points=3, max_per=2)
        else:   # a half-elf's +1s go on two other abilities
            plan.update(points=flex, max_per=1, exclude=sorted(fixed))
    else:
        from dnd_app.core.choices import _get_race_choices
        for c in _get_race_choices(char):
            if c.get("type") == "asi":
                plan.update(points=c.get("points", 2), max_per=c.get("max_per", 1),
                            exclude=list(c.get("exclude") or []), choice=c["id"])
                break
    who = f"{race} ({sub})" if sub and sub not in ("Standard",) else race
    bits = ", ".join(f"{ab} +{v}" for ab, v in fixed.items())
    if plan["points"]:
        if plan["max_per"] == 2:
            more = "+2 and +1 (or +1 to three), tap where they go"
        elif plan["points"] == 1:
            more = "+1 to one other, tap where it goes"
        else:
            n = 'two' if plan['points'] == 2 else plan['points']
            more = f"+1 to {n} others, tap where they go" if plan["exclude"] else f"+1 to any {n}, tap where they go"
        bits = f"{bits}, and {more}" if bits else more
    plan["text"] = f"{who}: {bits}" if bits else ""
    return plan


def next_pick(plan: dict, picks: dict, ab: str) -> dict:
    """picks after a tap on ab's +1: up one, or back to none once it can't
    go higher (the most on one ability, or no points left)."""
    picks = {k: v for k, v in picks.items() if v}
    if ab in plan["exclude"] or not plan["points"]:
        return picks
    used = sum(picks.values())
    cur = picks.get(ab, 0)
    if cur < plan["max_per"] and used < plan["points"]:
        # "+2 and +1": a second +2 isn't allowed
        if cur + 1 == 2 and any(v == 2 for k, v in picks.items() if k != ab):
            picks.pop(ab, None)
            return picks
        if cur + 1 == 2 and used + 1 > plan["points"]:
            picks.pop(ab, None)
            return picks
        picks[ab] = cur + 1
    else:
        picks.pop(ab, None)
    return picks


def picks_left(plan: dict, picks: dict) -> int:
    return max(0, plan["points"] - sum(picks.values()))


def point_buy_left(base: dict) -> int:
    return POINT_BUY_TOTAL - sum(POINT_BUY_COSTS.get(base.get(ab, 8), 99) for ab in ABILITIES)


def step_score(method: str, base: dict, ab: str, up: bool) -> dict:
    """base after a − or + on one ability. Standard Array swaps with the
    ability that holds the next value, so the six stay the array."""
    base = dict(base)
    v = base.get(ab, 10)
    if method == "Standard Array":
        vals = sorted(STANDARD_ARRAY)
        i = vals.index(v) if v in vals else 0
        j = i + (1 if up else -1)
        if 0 <= j < len(vals):
            other = next((a for a in ABILITIES if base.get(a) == vals[j]), None)
            base[ab] = vals[j]
            if other:
                base[other] = v
        return base
    if method == "Point Buy":
        nv = v + (1 if up else -1)
        if 8 <= nv <= 15:
            trial = dict(base, **{ab: nv})
            if point_buy_left(trial) >= 0:
                base[ab] = nv
        return base
    nv = v + (1 if up else -1)
    if 1 <= nv <= 20:
        base[ab] = nv
    return base


def start_scores(method: str) -> dict:
    if method == "Standard Array":
        return {ab: STANDARD_ARRAY[i] for i, ab in enumerate(ABILITIES)}
    if method == "Point Buy":
        return {ab: 8 for ab in ABILITIES}
    if method == "Roll":
        return {ab: roll_score() for ab in ABILITIES}
    return {ab: 10 for ab in ABILITIES}


def roll_score(rng=random) -> int:
    """4d6, the lowest dropped."""
    d = sorted(rng.randint(1, 6) for _ in range(4))
    return sum(d[1:])


def totals(plan: dict, base: dict, picks: dict, moved: dict = None) -> dict:
    """{ab: {base, bonus, total, mod}}. moved: a Tasha's reassignment of
    the race's fixed bonus ({ab: n}), used in place of it."""
    fixed = moved if moved is not None else plan["fixed"]
    out = {}
    for ab in ABILITIES:
        b = base.get(ab, 10)
        bonus = fixed.get(ab, 0) + picks.get(ab, 0)
        out[ab] = {"base": b, "bonus": bonus, "fixed": fixed.get(ab, 0),
                   "pick": picks.get(ab, 0), "total": b + bonus, "mod": mod_text(b + bonus)}
    return out


def abilities_block_reason(method: str, plan: dict, base: dict, picks: dict, moved: dict = None) -> str:
    if method == "Point Buy" and point_buy_left(base) < 0:
        return "That's more than 27 points."
    if method == "Standard Array" and sorted(base.values()) != sorted(STANDARD_ARRAY):
        return "Use each standard array value once."
    left = picks_left(plan, picks)
    if left:
        return f"Place your race's +1{'s' if left > 1 else ''} ({left} left)."
    if moved is not None:
        need = sum(plan["fixed"].values())
        if sum(moved.values()) != need:
            return f"Move all {need} of your race's points ({sum(moved.values())} placed)."
    return ""


def commit_abilities(char: dict, plan: dict, base: dict, picks: dict, moved: dict = None) -> None:
    char["abilities"] = {ab: base.get(ab, 10) for ab in ABILITIES}
    made = char.setdefault("_choices", {})
    if plan.get("choice"):
        made[plan["choice"]] = [f"asi:{ab}:{n}" for ab, n in picks.items() if n]
    else:
        for ab, n in picks.items():
            char["abilities"][ab] += n
    if moved is not None:
        made["tashas_asi_reassign"] = {ab: n for ab, n in moved.items() if n}
    else:
        made.pop("tashas_asi_reassign", None)
    char["_wizard_abilities"] = {"base": dict(base), "picks": dict(picks),
                                 "moved": dict(moved) if moved is not None else None}
    rebuild(char)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Class & Background
# ═══════════════════════════════════════════════════════════════════════════
SUBCLASS_TITLES = {
    "Artificer": "Artificer Specialist", "Barbarian": "Primal Path", "Bard": "Bard College",
    "Cleric": "Divine Domain", "Druid": "Druid Circle", "Fighter": "Martial Archetype",
    "Monk": "Monastic Tradition", "Paladin": "Sacred Oath", "Ranger": "Ranger Archetype",
    "Rogue": "Roguish Archetype", "Sorcerer": "Sorcerous Origin", "Warlock": "Otherworldly Patron",
    "Wizard": "Arcane Tradition", "Blood Hunter": "Blood Hunter Order",
}


def class_tiles() -> list:
    """[{name, hit_die, main}] in name order."""
    out = []
    for n in sorted(CLASS_NAMES):
        c = CLASS_DICT.get(n, {})
        out.append({"name": n, "hit_die": f"d{c.get('hit_die', 8)}",
                    "main": "/".join((c.get("multiclass_reqs") or {}).keys())})
    return out


def class_chips(name: str) -> list:
    c = CLASS_DICT.get(name)
    if not c:
        return []
    chips = [f"Hit die d{c.get('hit_die', 8)}", "Saves " + ", ".join(c.get("save_profs", []))]
    if c.get("spell_ability") and c.get("has_spells", True):
        chips.append(f"Casts with {c['spell_ability']}")
    n = c.get("skill_count", 2)
    chips.append(f"{n} skills from its list")
    return chips


def background_rows(search: str = "") -> list:
    q = (search or "").strip().lower()
    out = []
    for n in BACKGROUND_NAMES:
        if q and q not in n.lower():
            continue
        b = get_background(n) or {}
        skills = ", ".join(b.get("skills") or [])
        if not skills and b.get("skill_choices"):
            sc = b["skill_choices"]
            skills = sc.get("what") or f"{sc.get('count', 1)} skills you pick"
        out.append({"name": n, "source": b.get("source", ""), "skills": skills})
    return out


def background_card(name: str) -> dict:
    """{name, source, chips [{text, kind}], feature, text, gear, feats}"""
    b = get_background(name)
    if not b:
        return {}
    chips = [{"text": s, "kind": "teal"} for s in (b.get("skills") or [])]
    if b.get("skill_choices"):
        sc = b["skill_choices"]
        chips.append({"text": sc.get("what") or f"{sc.get('count', 1)} skills you pick", "kind": "teal"})
    for t in (b.get("tools") or []):
        chips.append({"text": t, "kind": ""})
    if b.get("tool_choices"):
        chips.append({"text": b["tool_choices"].get("what") or "a tool you pick", "kind": ""})
    gear_bits = []
    if b.get("equipment"):
        gear_bits.append("Gear: " + b["equipment"])
    langs = b.get("languages", 0)
    if isinstance(langs, int) and langs:
        gear_bits.append(f"{langs} language{'s' if langs > 1 else ''}")
    return {"name": name, "source": b.get("source", ""), "chips": chips,
            "feature": b.get("feature", ""), "text": b.get("feature_desc", ""),
            "gear": " · ".join(gear_bits), "feats": list(b.get("feat_choices") or []),
            "origin_feat": b.get("origin_feat") or ""}


def identity_block_reason(name: str, cls: str, bg: str, bg_feat: str = "", current_name: str = "") -> str:
    from dnd_app.core.save_load import name_in_use
    if not (name or "").strip():
        return "Give your character a name."
    if name.strip() != (current_name or "").strip() and name_in_use(name.strip()):
        return "Another saved character already has that name."
    if not cls:
        return "Choose a class."
    if not bg:
        return "Choose a background."
    card = background_card(bg)
    if card.get("feats") and bg_feat not in card["feats"]:
        return f"Choose the feat {bg} gives you."
    return ""


def commit_identity(char: dict, name: str, alignment: str, cls: str, bg: str, bg_feat: str = "") -> None:
    char["name"] = name.strip()
    char["alignment"] = alignment
    char["edition"] = "2014"
    char["background"] = bg
    made = char.setdefault("_choices", {})
    if background_card(bg).get("feats"):
        made["background_feat"] = bg_feat
    else:
        made.pop("background_feat", None)
    if not char.get("classes") or char["classes"][0].get("class") != cls:
        char["classes"] = [{"class": cls, "level": 1, "subclass": "",
                            "hit_die": CLASS_DICT.get(cls, {}).get("hit_die", 8)}]
    rebuild(char)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Spells & Choices
# ═══════════════════════════════════════════════════════════════════════════
# What level 1 asks you to pick, built on the same choices the Choices page
# asks for (core/builder.py get_choices_needed and core/choices.py), so a
# pick made here is the very one the sheet would have asked for. The ASI
# and feat a Variant Human gets aren't here: the +1s are on the Abilities
# step and the feat stays on the Choices page.
_SKIP_TYPES = {"asi", "asi_or_feat", "feat", "info"}
_KIND_ORDER = {"subclass": 0, "skill_prof": 2, "skill_or_tool_prof": 3, "expertise": 4,
               "language": 5, "tool_prof": 6, "weapon_or_tool_prof": 7}


def _raw_choices(char: dict) -> list:
    from dnd_app.core.choices import (
        _get_race_choices, _get_class_tool_choices, _get_feat_choices,
        _get_dm_reward_choices, _get_subclass_choices, ALL_SKILLS,
    )
    from dnd_app.data.items import ALL_TOOLS, WEAPON_NAMES
    out = (get_choices_needed(char) + _get_race_choices(char) + _get_class_tool_choices(char)
           + _get_feat_choices(char) + _get_dm_reward_choices(char) + _get_subclass_choices(char))
    for c in out:
        pool = c.get("pool")
        if c["type"] == "skill_prof" and (not pool or (len(pool) == 1 and "any" in str(pool[0]).lower())):
            c["pool"] = list(ALL_SKILLS)
        elif pool is None:
            if c["type"] == "tool_prof":
                c["pool"] = list(ALL_TOOLS)
            elif c["type"] == "skill_or_tool_prof":
                c["pool"] = list(ALL_SKILLS) + list(ALL_TOOLS)
            elif c["type"] == "weapon_or_tool_prof":
                c["pool"] = list(WEAPON_NAMES) + list(ALL_TOOLS)
            elif c["type"] == "expertise":
                c["pool"] = sorted(s for s, lvl in char.get("skills", {}).items() if lvl >= 2)
                c["pool"] += [t for t in (c.get("extra_pool") or []) if t not in c["pool"]]
    return out


def apply_pick(char: dict, choice_id: str, selected: list, kind: str = "", source_name: str = "") -> None:
    """One choice's picks into the character, as the Choices page keeps
    them (Android's applyLevelUpChoice, desktop's level-up panel)."""
    if kind == "subclass":
        from dnd_app.core.character import set_subclass
        if selected:
            set_subclass(char, source_name, selected[0])
        apply_choice(char, choice_id, list(selected))
        return
    if choice_id.endswith("_fighting_style"):
        fs = char.get("fighting_styles", [])
        for item in selected:
            if item not in fs:
                fs.append(item)
        char["fighting_styles"] = fs
    elif choice_id == "eldritch_invocations":
        char["eldritch_invocations"] = list(selected)
    elif choice_id.endswith("_maneuvers"):
        ex = char.get("battle_master_maneuvers", [])
        char["battle_master_maneuvers"] = ex + [m for m in selected if m not in ex]
    elif "expertise" in choice_id:
        for skill in selected:
            if skill in char.get("skills", {}):
                char["skills"][skill] = 3
        made = char.setdefault("_choices", {})
        made[choice_id] = list(selected)
        allx = []
        for k, v in made.items():
            if "expertise" in k and k != "class_skill_expertise" and isinstance(v, list):
                allx.extend(v)
        made["class_skill_expertise"] = sorted(set(allx))
    apply_choice(char, choice_id, list(selected))


def _with_picks(base: dict, picks: dict, kinds: dict) -> dict:
    scratch = copy.deepcopy(base)
    order = sorted(picks, key=lambda i: 0 if kinds.get(i, ("", ""))[0] == "subclass" else 1)
    for cid in order:
        kind, src = kinds.get(cid, ("", ""))
        if picks[cid]:
            apply_pick(scratch, cid, picks[cid], kind, src)
    rebuild(scratch)
    return scratch


def _title(c: dict) -> str:
    if c["type"] == "subclass":
        return SUBCLASS_TITLES.get(c.get("source_name", ""), "Subclass")
    if c["type"] in ("skill_prof",):
        return "Skills"
    if c["type"] == "expertise":
        return "Expertise"
    if c["type"] == "language":
        return "Languages"
    if c["type"] == "tool_prof":
        return "Tools"
    label = c.get("label", "")
    label = re.sub(r"\s*\([^)]*\)\s*$", "", label)
    label = re.sub(r"^(?:Choose|Pick)\s+(?:a |an |your |\d+ )?", "", label)
    label = label.split(":")[0].strip()
    return label[:1].upper() + label[1:] if label else "Choice"


def _who(c: dict, char: dict) -> str:
    src = c.get("source", "")
    if src == "race":
        return char.get("race", "") or c.get("source_name", "")
    if src == "background":
        return char.get("background", "") or c.get("source_name", "")
    return c.get("source_name", "")


def _sub(c: dict, char: dict, count: int) -> str:
    if c["type"] == "subclass":
        return "your subclass, chosen at level 1"
    if c["type"] == "expertise":
        return f"pick {count} you're proficient in — double your proficiency bonus"
    who = _who(c, char)
    label = c.get("label", "")
    m = re.search(r"\(([^)]*)\)\s*$", label)
    if c["type"] == "tool_prof" and "your" in label:
        what = re.sub(r"^Choose (your )?", "", re.sub(r"\s*\([^)]*\)\s*$", "", label))
        return f"{who}: {'one ' if count == 1 else ''}{what}"
    if c["type"] == "skill_prof" and c.get("source") == "race" and len(c.get("pool") or []) >= 18:
        return f"{who}: any {count}"
    return f"{who}: pick {count}" if who else f"pick {count}"


def _tile(value: str) -> dict:
    """A pick's tile: its name, and a short second line ("Black – acid"
    is Black over acid); a long description goes on hover instead."""
    name, sub, tip = value, "", ""
    for sep in (" – ", " — "):
        if sep in value:
            name, rest = value.split(sep, 1)
            if len(rest) <= 14:
                sub = rest
            else:
                tip = rest
            break
    if not sub and not tip and " (" in name and name.endswith(")"):
        name, tip = name.split(" (", 1)
        tip = tip[:-1]
    return {"value": value, "label": name.strip(), "sub": sub.strip(), "tip": tip.strip()}


def prof_sources(char: dict) -> dict:
    """{skill, tool or language (lowercase): "your background: Gambler"}
    for what the character already has, and where from."""
    out = {}
    race, sub = char.get("race", ""), char.get("subrace", "")
    bg = char.get("background", "")
    for s in get_race_skills(race, sub):
        out[s.lower()] = f"your race: {race}"
    for s in get_background_skills(bg):
        out[s.lower()] = f"your background: {bg}"
    made = char.get("_choices", {}) or {}
    for k, v in made.items():
        if not isinstance(v, list):
            continue
        if k.endswith("_skill_profs") and k not in ("class_skill_profs",):
            if k == "race_skill_profs":
                where = f"your race: {race}"
            elif k == "bg_skill_profs":
                where = f"your background: {bg}"
            else:
                where = f"your {k[:-len('_skill_profs')]} skill picks"
            for s in v:
                out.setdefault(str(s).lower(), where)
        if k == "bg_tool_profs":
            for s in v:
                out.setdefault(str(s).lower(), f"your background: {bg}")
    for l in race_languages(race, sub):
        out.setdefault(l.lower(), f"your race: {race}")
    b = get_background(bg) or {}
    for t in (b.get("tools") or []):
        out.setdefault(t.lower(), f"your background: {bg}")
    cls = (char.get("classes") or [{}])[0].get("class", "")
    for t in (CLASS_DICT.get(cls, {}).get("tools") or []):
        if isinstance(t, str):
            out.setdefault(t.lower(), f"your class: {cls}")
    return out


def _have(char: dict, kind: str, value: str, sources: dict, own: list) -> str:
    """Where the character already has value from ("" if it doesn't, or
    has it only from this very choice)."""
    if value in own:
        return ""
    v = value.lower()
    if kind in ("skill_prof", "skill_or_tool_prof"):
        if char.get("skills", {}).get(value, 0) >= 2:
            return sources.get(v, "your other picks")
    if kind in ("tool_prof", "skill_or_tool_prof", "weapon_or_tool_prof"):
        if any(t.lower() == v for t in char.get("tool_proficiencies", []) or []):
            return sources.get(v, "your other picks")
    if kind == "language":
        if any(l.lower() == v for l in char.get("languages", []) or []):
            return sources.get(v, "your other picks")
    if kind == "expertise" and char.get("skills", {}).get(value, 0) >= 3:
        return "your other Expertise"
    return ""


def level1_cards(base: dict, picks: dict) -> list:
    """The cards of the Choices half, in order: [{id, kind, title, sub,
    count, picked [values], left, tiles [{value, label, sub, tip, have}],
    cols, big (a long pool: picked tiles plus a "＋ Pick" one), parent
    (the subclass card a follow-up sits in)}].
    base: the character before any of these picks. picks: {id: [values]}."""
    first = {c["id"]: c for c in _raw_choices(base)
             if c["type"] not in _SKIP_TYPES and c.get("pool")}
    kinds = {}
    for _ in range(3):   # a subclass's own picks only show once it's chosen
        kinds = {cid: (c["type"], c.get("source_name", "")) for cid, c in first.items()}
        known = {k: v for k, v in picks.items() if k in first}
        full = _with_picks(base, known, kinds)
        for c in _raw_choices(full):
            if c["type"] in _SKIP_TYPES or not c.get("pool"):
                continue
            first.setdefault(c["id"], c)
    kinds = {cid: (c["type"], c.get("source_name", "")) for cid, c in first.items()}
    initial_ids = {c["id"] for c in _raw_choices(base)}
    sub_id = next((cid for cid, c in first.items() if c["type"] == "subclass"), "")
    cards = []
    for cid, c0 in first.items():
        others = {k: v for k, v in picks.items() if k != cid and k in first}
        scratch = _with_picks(base, others, kinds)
        c = next((x for x in _raw_choices(scratch) if x["id"] == cid), None)
        if c is None:
            continue    # no longer asked (a different subclass, say)
        count = c.get("count", 1)
        if c.get("already_chosen") and c["id"] not in picks:
            pass
        own = list(picks.get(cid, []))
        sources = prof_sources(scratch)
        pool = list(c.get("pool") or [])
        tiles = []
        for v in pool:
            t = _tile(v)
            t["have"] = _have(scratch, c["type"], v, sources, own)
            tiles.append(t)
        n = len(tiles)
        longest = max((len(t["label"]) for t in tiles), default=0)
        if c["type"] == "subclass" or (n == 4 and longest <= 16) or (n >= 7 and longest <= 16):
            cols = 4
        elif n == 4:
            cols = 2
        elif n in (5, 10) and longest <= 8:
            cols = 5
        elif longest > 22:
            cols = 2
        else:
            cols = 3
        parent = sub_id if (sub_id and cid not in initial_ids and cid != sub_id) else ""
        cards.append({"id": cid, "kind": c["type"], "source_name": c.get("source_name", ""),
                      "title": _title(c), "sub": _sub(c, scratch, count),
                      "count": count, "picked": own, "left": max(0, count - len(own)),
                      "tiles": tiles, "cols": cols, "big": n > 18, "parent": parent})
    cards.sort(key=lambda d: (_KIND_ORDER.get(d["kind"], 1) if not d["parent"] else 1,
                              0 if d["kind"] == "subclass" else 1))
    # follow-ups straight after their subclass
    if sub_id:
        main = [d for d in cards if not d["parent"]]
        kids = [d for d in cards if d["parent"]]
        out = []
        for d in main:
            out.append(d)
            if d["id"] == sub_id:
                out.extend(kids)
        cards = out
    return cards


def toggle_pick(cards: list, picks: dict, cid: str, value: str) -> dict:
    """picks after a tap on a tile: on, or off again. A one-of choice
    swaps; a full one ignores more."""
    card = next((c for c in cards if c["id"] == cid), None)
    if not card:
        return picks
    tile = next((t for t in card["tiles"] if t["value"] == value), None)
    if tile is None or tile.get("have"):
        return picks
    cur = list(picks.get(cid, []))
    picks = dict(picks)
    if value in cur:
        cur.remove(value)
    elif card["count"] == 1:
        cur = [value]
    elif len(cur) < card["count"]:
        cur.append(value)
    else:
        return picks
    if cur:
        picks[cid] = cur
    else:
        picks.pop(cid, None)
    if card["kind"] == "subclass":   # its follow-ups belong to the old one
        for c in cards:
            if c.get("parent") == cid:
                picks.pop(c["id"], None)
    return picks


def tidy_picks(cards: list, picks: dict) -> dict:
    """Only picks for cards still asked, and still allowed."""
    out = {}
    for c in cards:
        ok = {t["value"] for t in c["tiles"] if not t.get("have")}
        keep = [v for v in picks.get(c["id"], []) if v in ok][:c["count"]]
        if keep:
            out[c["id"]] = keep
    return out


# ── starting spells ──────────────────────────────────────────────────────
def _ordinal(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def spell_plan(char: dict) -> dict:
    """{} for a class that learns no spells at level 1, else
      ability, dc, attack, slots (text),
      tabs [{key: "cantrips"|"spells", title, count, lists, level}]"""
    from dnd_app.core.spellcasting import spell_learners, spellcasting_rows, wizard_book_size
    from dnd_app.core.calculator import update_all
    scratch = copy.deepcopy(char)
    rebuild(scratch)
    update_all(scratch)
    learners = spell_learners(scratch)
    if not learners:
        return {}
    key, ln = next(iter(learners.items()))
    tabs = []
    if ln["cantrips"]:
        tabs.append({"key": "cantrips", "title": "Cantrips", "count": ln["cantrips"],
                     "lists": sorted(ln["lists"]), "level": 0})
    if ln["level"] > 0:
        if key == "Wizard":
            tabs.append({"key": "spells", "title": "Spellbook", "count": wizard_book_size(1),
                         "lists": sorted(ln["lists"]), "level": ln["level"]})
        elif ln["spells"]:
            tabs.append({"key": "spells", "title": f"{_ordinal(ln['level'])} level", "count": ln["spells"],
                         "lists": sorted(ln["lists"]), "level": ln["level"]})
    if not tabs:
        return {}
    rows = spellcasting_rows(scratch)
    row = rows[0] if rows else {}
    slots = scratch.get("spell_slots_max") or []
    if isinstance(slots, dict):
        n1 = slots.get(1) or slots.get("1") or 0
    else:
        n1 = slots[0] if slots else 0
    n1 = n1 or scratch.get("pact_slots_max") or 0
    return {"ability": row.get("ability", ""), "dc": row.get("dc", 0), "attack": row.get("attack", 0),
            "slots": f"{n1} first-level slot{'s' if n1 != 1 else ''}" if n1 else "",
            "tabs": tabs, "label": ln.get("label", key)}


def spell_rows(tab: dict, search: str = "", granted=()) -> list:
    """The spells a tab offers: [{name, school, time, range, conc, ritual}]."""
    from dnd_app.data.spells import ALL_SPELLS
    q = (search or "").strip().lower()
    out = []
    lists = set(tab.get("lists") or [])
    for sp in ALL_SPELLS:
        lvl = sp.get("level", 0)
        if tab["key"] == "cantrips" and lvl != 0:
            continue
        if tab["key"] == "spells" and not (1 <= lvl <= tab.get("level", 1)):
            continue
        if not lists & set(sp.get("classes") or []):
            continue
        if q and q not in sp["name"].lower():
            continue
        if sp["name"] in granted:
            continue
        out.append({"name": sp["name"], "school": sp.get("school", ""),
                    "time": sp.get("cast_time", sp.get("casting_time", "")),
                    "range": sp.get("range", ""), "conc": bool(sp.get("concentration")),
                    "ritual": bool(sp.get("ritual")), "desc": sp.get("desc", "")})
    out.sort(key=lambda r: r["name"])
    return out


def toggle_spell(plan: dict, spells: dict, key: str, name: str) -> dict:
    """spells: {"cantrips": [...], "spells": [...]} after a tap."""
    spells = {k: list(v) for k, v in spells.items()}
    tab = next((t for t in plan.get("tabs", []) if t["key"] == key), None)
    if not tab:
        return spells
    cur = spells.setdefault(key, [])
    if name in cur:
        cur.remove(name)
    elif len(cur) < tab["count"]:
        cur.append(name)
    return spells


def level1_left(cards: list, plan: dict, spells: dict) -> list:
    """What's still to pick, in words: ["1 cantrip", "1 skill", ...]."""
    out = []
    for t in (plan or {}).get("tabs", []):
        n = t["count"] - len(spells.get(t["key"], []))
        if n > 0:
            word = "cantrip" if t["key"] == "cantrips" else "spell"
            out.append(f"{n} {word}{'s' if n > 1 else ''}")
    names = {"skill_prof": "skill", "expertise": "Expertise", "language": "language",
             "tool_prof": "tool", "subclass": "subclass"}
    tally = {}
    for c in cards:
        if c["left"]:
            w = names.get(c["kind"], c["title"].lower())
            tally[w] = tally.get(w, 0) + c["left"]
    for w, n in tally.items():
        plural = "s" if n > 1 and w not in ("Expertise",) else ""
        out.append(f"{n} {w}{plural}")
    return out


def commit_level1(char: dict, base: dict, picks: dict, plan: dict, spells: dict) -> None:
    """The step's picks into the character (from the base it started from,
    so going back and picking again doesn't stack)."""
    cards = level1_cards(base, picks)
    kinds = {c["id"]: (c["kind"], c["source_name"]) for c in cards}
    done = _with_picks(base, tidy_picks(cards, picks), kinds)
    known = [s for s in done.get("spells_known", []) if s not in base.get("_wizard_spells", [])]
    mine = list(spells.get("cantrips", [])) + list(spells.get("spells", []))
    done["spells_known"] = known + [s for s in mine if s not in known]
    done["_wizard_spells"] = mine
    done["_wizard_level1"] = {"picks": picks, "spells": spells}
    char.clear()
    char.update(done)
    rebuild(char)


def level1_base(char: dict) -> dict:
    """The character as it was before the Spells & Choices step's picks
    (kept so the step can be redone)."""
    base = char.get("_wizard_level1_base")
    return copy.deepcopy(base) if base else None


def has_level1_step(char: dict) -> bool:
    return bool(level1_cards(char, {})) or bool(spell_plan(char))


# ═══════════════════════════════════════════════════════════════════════════
# 5. Equipment
# ═══════════════════════════════════════════════════════════════════════════
def _group_title(options: list) -> str:
    from dnd_app.data.items import ARMOR_DICT, WEAPON_DICT, EQUIPMENT_PACKS
    words = " ".join(" ".join(o) for o in options).lower()
    flat = [i.split(" (")[0] for o in options for i in o]
    if any(i in EQUIPMENT_PACKS for i in flat):
        return "PACK"
    if any(i in ARMOR_DICT and ARMOR_DICT[i].get("type") == "shield" for i in flat) and "shield" in words:
        return "WEAPON AND SHIELD" if (any(i in WEAPON_DICT for i in flat) or "weapon" in words) else "SHIELD"
    if any(i in ARMOR_DICT for i in flat):
        return "ARMOR"
    if "focus" in words or "pouch" in words:
        return "FOCUS"
    if "instrument" in words or "lute" in words:
        return "INSTRUMENT"
    if any(i in WEAPON_DICT for i in flat) or "weapon" in words:
        return "WEAPON"
    return "GEAR"


def equipment_groups(cls: str) -> list:
    """[{title, options [{label, items, anys [{name, pool}]}], fixed}]:
    a group with one option is what the class always gets."""
    from dnd_app.data.starting_equipment import get_starting_equipment
    from dnd_app.data.items import weapon_category_pool
    out = []
    for g in get_starting_equipment(cls):
        opts = []
        for o in g["options"]:
            anys = [{"name": i, "pool": weapon_category_pool(i)} for i in o if i.lower().startswith("any ")]
            fixed = [i for i in o if not i.lower().startswith("any ")]
            label = ", ".join(_count_items(fixed)) if fixed else ""
            if anys:
                label = (label + ", " if label else "") + ", ".join(a["name"] for a in anys)
            opts.append({"label": label, "items": list(o), "anys": anys})
        out.append({"title": _group_title(g["options"]), "options": opts, "fixed": len(opts) == 1})
    return out


def _count_items(items: list) -> list:
    seen = {}
    for i in items:
        seen[i] = seen.get(i, 0) + 1
    return [f"{n} ×{k}" if k > 1 else n for n, k in seen.items()]


def resolve_equipment(groups: list, chosen: list) -> list:
    """The items the picks come to. chosen: per group {"option": i,
    "anys": [the weapon picked for each "Any …"]}."""
    items = []
    for gi, g in enumerate(groups):
        sel = chosen[gi] if gi < len(chosen) else {}
        oi = sel.get("option", 0) if not g["fixed"] else 0
        o = g["options"][min(oi, len(g["options"]) - 1)]
        anys = iter(sel.get("anys") or [])
        for it in o["items"]:
            if it.lower().startswith("any "):
                pool = next((a["pool"] for a in o["anys"] if a["name"] == it), [])
                pick = next(anys, None)
                items.append(pick if pick in pool else (pool[0] if pool else it))
            else:
                items.append(it)
    return items


def default_choice(groups: list) -> list:
    return [{"option": 0, "anys": [a["pool"][0] if a["pool"] else "" for a in g["options"][0]["anys"]]}
            for g in groups]


def background_gear(char: dict) -> list:
    from dnd_app.core.inventory import gear_from_text
    if char.get("background") == "Custom Background":
        return []
    text = (get_background(char.get("background", "")) or {}).get("equipment", "")
    items, coins = gear_from_text(text)
    out = [f"{n} ×{q}" if q > 1 else n for n, q in items]
    out += [f"{n} {d}" for d, n in coins.items()]
    return out


def kit_char(char: dict, items: list, extra: str = "") -> dict:
    """A copy of the character with this kit, for the preview and summary."""
    from dnd_app.core.inventory import set_starting_inventory, add_item
    from dnd_app.core.calculator import update_all
    c = copy.deepcopy(char)
    bg = get_background(c.get("background", ""))
    bg_text = "" if c.get("background") == "Custom Background" else (bg or {}).get("equipment", "")
    set_starting_inventory(c, items, bg_text)
    for line in (extra or "").split(","):
        if line.strip():
            add_item(c, line.strip())
    rebuild(c)
    update_all(c)
    return c


def kit_preview(char: dict, items: list, extra: str = "") -> dict:
    """{slots [{label, name, sub, empty}], rows [{name, qty, note}],
    gold, weight}: what the Loadout and Inventory tabs will show."""
    from dnd_app.core.loadout import loadout
    from dnd_app.core.inventory import item_weight, money_text, weight_text
    from dnd_app.core.calculator import get_ac, get_carry_capacity_detail
    c = kit_char(char, items, extra)
    lo = loadout(c)
    slots = []
    for s in lo.get("in_hand", []):
        sub = s.get("what", "") or ""
        slots.append({"label": s.get("label", "").upper(), "name": s.get("name") or "Empty",
                      "sub": sub, "empty": not s.get("name")})
    for s in slots:
        if s["label"] == "ARMOR" and s["empty"]:
            s["name"], s["sub"] = "None", f"AC {get_ac(c)}"
    held = {s["name"] for s in slots if not s["empty"]}
    rows = []
    for e in c.get("equipment", []):
        n = e.get("name", "")
        q = e.get("qty", 1)
        if n in held and q <= 1:
            continue
        rows.append({"name": n, "qty": q, "note": ""})
    gp = _purse_gp(c)
    weight = sum(item_weight(e) * e.get("qty", 1) for e in c.get("equipment", []))
    try:
        cap = get_carry_capacity_detail(c).get("capacity", 0)
    except Exception:
        cap = 0
    return {"slots": slots, "rows": rows, "gold": money_text(gp),
            "weight": f"{weight_text(weight)}" + (f" / {int(cap)} lb" if cap else "")}


# ═══════════════════════════════════════════════════════════════════════════
# 6. Summary
# ═══════════════════════════════════════════════════════════════════════════
def summary(c: dict) -> dict:
    """Everything the Summary step shows, for the finished character c
    (kit_char of it): name, line, sub, sub2, stats [(value, label)],
    abilities [{ab, score, mod, save}], saves_text, skills [(name, bonus)],
    senses, profs [(label, text)], spells {head, cantrips, spells, title} or
    {}, features [names], equipment [(label, text)], gold, weight."""
    from dnd_app.core.calculator import (
        compute_max_hp, get_ac, get_initiative, get_effective_speed, get_prof_bonus,
        get_skill_bonus, get_passive_perception, get_saving_throw_bonus, known_languages,
        sense_list,
    )
    from dnd_app.core.character import ability_score
    from dnd_app.core.choices import ALL_SKILLS
    cls = (c.get("classes") or [{}])[0]
    cname = cls.get("class", "")
    race = c.get("race", "")
    sub = c.get("subrace", "")
    race_txt = f"{sub} {race}".strip() if sub and sub not in ("Standard",) and not sub.startswith("Mark") else race
    sub_line = cls.get("subclass", "")
    if sub_line:
        sub_line = sub_line.split(" (")[0].split(" – ")[0]
        extra = []
        for k, v in (c.get("_choices") or {}).items():
            if k.startswith("sorcerer_dragon_ancestor") and v:
                extra.append(str(v[0]).replace(" – ", ", "))
        if extra:
            sub_line += f" ({extra[0]})"
    saves = [ab for ab in ABILITIES if ab in (CLASS_DICT.get(cname, {}).get("save_profs") or [])]
    speed = get_effective_speed(c).get("walk", 30)
    stats = [(str(compute_max_hp(c)), "HP"), (str(get_ac(c)), "AC"), (f"{speed} ft", "SPEED"),
             (f"{get_initiative(c):+d}", "INITIATIVE"), (f"+{get_prof_bonus(c)}", "PROF BONUS"),
             (f"1d{CLASS_DICT.get(cname, {}).get('hit_die', 8)}", "HIT DIE")]
    abilities = []
    for ab in ABILITIES:
        s = ability_score(c, ab)
        abilities.append({"ab": ab, "score": s, "mod": mod_text(s), "save": ab in saves})
    skills = [(s, f"{get_skill_bonus(c, s):+d}") for s in ALL_SKILLS if (c.get("skills") or {}).get(s, 0) >= 2]
    senses = [f"Passive Perception {get_passive_perception(c)}"]
    for s in sense_list(c):
        if s.get("range"):
            senses.append(f"{s['name']} {s['range']} ft")
    save_txt = ", ".join(f"{ab} {get_saving_throw_bonus(c, ab):+d}" for ab in saves)

    def joined(v):
        if isinstance(v, (list, tuple)):
            seen, out = set(), []
            for x in v:
                if x and str(x).lower() not in seen:
                    seen.add(str(x).lower())
                    out.append(str(x))
            return ", ".join(out) or "none"
        return str(v or "none")
    profs = [("Saves", ", ".join(saves) or "none"),
             ("Armor", joined([a for a in (c.get("armor_proficiencies") or []) if a != "None"])),
             ("Weapons", joined(c.get("weapon_proficiencies"))),
             ("Tools", joined(c.get("tool_proficiencies"))),
             ("Languages", joined(known_languages(c)))]
    spells = {}
    plan = spell_plan(c)
    known = c.get("spells_known", []) or []
    if plan or known:
        from dnd_app.data.spells import get_spell
        cants = [s for s in known if (get_spell(s) or {}).get("level", 0) == 0]
        lvl = [s for s in known if (get_spell(s) or {}).get("level", 0) > 0]
        whole = plan and not any(t["key"] == "spells" for t in plan.get("tabs", []))
        if whole:   # a Cleric, Druid or Artificer prepares from its whole list
            lvl = []
        head = []
        if plan:
            head.append(f"Save DC {plan['dc']} · attack {plan['attack']:+d}")
            if plan.get("slots"):
                head.append(plan["slots"])
        spells = {"head": " · ".join(head), "cantrips": cants, "spells": lvl,
                  "title": "SPELLBOOK" if cname == "Wizard" else "1ST LEVEL",
                  "note": f"Prepares from the whole {cname} list" if whole else ""}
    features = []
    try:
        from dnd_app.core.feature_page import feature_page
        for sec in feature_page(c):
            for card in sec.get("cards", []):
                if card.get("future"):
                    continue
                n = card.get("name", "")
                if n and n not in features:
                    features.append(n)
    except Exception:
        pass
    if len(features) < 3:
        for f in (CLASS_DICT.get(cname, {}).get("features") or {}).get(1, []):
            n = f.split(" (")[0]
            if n not in features:
                features.append(n)
    from dnd_app.core.loadout import loadout
    lo = loadout(c)
    equip = []
    held = set()
    for s in lo.get("in_hand", []):
        if s.get("name"):
            equip.append((s.get("label", "").title(), s["name"]))
            held.add(s["name"])
    worn = [e.get("name") for e in c.get("equipment", []) if "clothes" in e.get("name", "").lower()]
    if worn:
        equip.append(("Worn", ", ".join(worn)))
    carry = []
    for e in c.get("equipment", []):
        n = e.get("name", "")
        if n in worn or (n in held and e.get("qty", 1) <= 1):
            continue
        q = e.get("qty", 1)
        carry.append(f"{n} ×{q}" if q > 1 else n)
    if carry:
        equip.append(("Carrying", ", ".join(carry)))
    prev = kit_preview_numbers(c)
    return {"name": c.get("name", ""), "line": f"{race_txt} {cname} 1".strip(),
            "sub": sub_line, "sub2": " · ".join(x for x in (c.get("background", ""), c.get("alignment", "")) if x),
            "stats": stats, "abilities": abilities, "saves_text": save_txt, "skills": skills,
            "senses": " · ".join(senses), "profs": profs, "spells": spells,
            "features": features, "equipment": equip, "gold": prev["gold"], "weight": prev["weight"]}


def _purse_gp(c: dict) -> float:
    rate = {"pp": 10, "gp": 1, "ep": 0.5, "sp": 0.1, "cp": 0.01}
    return sum(rate.get(str(k).lower(), 0) * (v or 0) for k, v in (c.get("currency") or {}).items())


def kit_preview_numbers(c: dict) -> dict:
    from dnd_app.core.inventory import item_weight, money_text, weight_text
    from dnd_app.core.calculator import get_carry_capacity_detail
    gp = _purse_gp(c)
    weight = sum(item_weight(e) * e.get("qty", 1) for e in c.get("equipment", []))
    try:
        cap = get_carry_capacity_detail(c).get("capacity", 0)
    except Exception:
        cap = 0
    return {"gold": money_text(gp), "weight": weight_text(weight) + (f" / {int(cap)} lb" if cap else "")}


def finish(char: dict, items: list, extra: str = "") -> None:
    """The kit into the character itself, the wizard's last step."""
    c = kit_char(char, items, extra)
    for k in ("_wizard_abilities", "_wizard_level1", "_wizard_spells", "_wizard_level1_base"):
        c.pop(k, None)
    char.clear()
    char.update(c)


# ═══════════════════════════════════════════════════════════════════════════
# A wizard in progress (Android's bridge keeps one; desktop's wizard keeps
# the same state on itself)
# ═══════════════════════════════════════════════════════════════════════════
def fresh_state() -> dict:
    return {
        "race": "", "sub": "", "rpicks": {}, "race_search": "", "race_group": "All",
        "method": "Standard Array", "base": start_scores("Standard Array"), "picks": {}, "moved": None,
        "name": "", "alignment": "True Neutral", "cls": "", "bg": "", "bg_feat": "", "bg_search": "",
        "l1_picks": {}, "spells": {}, "spell_tab": "cantrips", "spell_search": "",
        "equip": None, "equip_cls": "", "extra": "",
    }


class Session:
    """The picks of a wizard in progress, and the character they make."""

    def __init__(self):
        self.state = fresh_state()
        self._cache = {}

    def _key(self, upto):
        import json
        s = self.state
        parts = [s["race"], s["sub"], s["rpicks"]]
        if upto >= 2:
            parts += [s["base"], s["picks"], s["moved"]]
        if upto >= 3:
            parts += [s["name"], s["alignment"], s["cls"], s["bg"], s["bg_feat"]]
        if upto >= 4:
            parts += [s["l1_picks"], s["spells"]]
        return upto, json.dumps(parts, sort_keys=True, default=str)

    def built(self, upto: int) -> dict:
        """A copy of the character with steps 1..upto applied."""
        from dnd_app.core.character import new_character
        k = self._key(upto)
        if k in self._cache:
            return copy.deepcopy(self._cache[k])
        s = self.state
        c = new_character()
        if upto >= 1 and s["race"]:
            commit_race(c, s["race"], s["sub"], s["rpicks"])
        if upto >= 2:
            commit_abilities(c, bonus_plan(c), s["base"], s["picks"], s["moved"])
        if upto >= 3 and s["cls"]:
            commit_identity(c, s["name"] or "?", s["alignment"], s["cls"], s["bg"], s["bg_feat"])
        if upto >= 4 and s["cls"]:
            base = copy.deepcopy(c)
            commit_level1(c, base, s["l1_picks"], spell_plan(base), s["spells"])
        if len(self._cache) > 12:
            self._cache.clear()
        self._cache[k] = copy.deepcopy(c)
        return c

    # ── steps ──
    def has_level1(self) -> bool:
        s = self.state
        if not (s["cls"] and s["bg"]):
            return True
        return has_level1_step(self.built(3))

    def spells_step_name(self) -> str:
        s = self.state
        if s["cls"] and s["bg"] and not spell_plan(self.built(3)):
            return "Choices"
        return "Spells & Choices"

    def block(self, step: int) -> str:
        s = self.state
        if step == 0:
            return race_block_reason(s["race"], s["sub"], s["rpicks"])
        if step == 1:
            return abilities_block_reason(s["method"], bonus_plan(self.built(1)), s["base"], s["picks"], s["moved"])
        if step == 2:
            return identity_block_reason(s["name"], s["cls"], s["bg"], s["bg_feat"])
        if step == 3:
            left = self.level1_left()
            return ("Still to pick: " + " · ".join(left)) if left else ""
        return ""

    # ── race ──
    def pick_race(self, name):
        s = self.state
        if s["race"] != name:
            s.update(race=name, sub="", rpicks={}, picks={}, moved=None, l1_picks={})

    def pick_sub(self, sub):
        s = self.state
        if s["sub"] != sub:
            s.update(sub=sub, picks={}, moved=None, l1_picks={})
            s["rpicks"].pop("ancestry", None)
            s["rpicks"].pop("season", None)

    def pick_rextra(self, field, value):
        self.state["rpicks"] = dict(self.state["rpicks"], **{field: value})

    # ── abilities ──
    def plan(self):
        p = bonus_plan(self.built(1))
        self.state["picks"] = {ab: n for ab, n in self.state["picks"].items() if n and ab not in p["exclude"]}
        return p

    def set_method(self, m):
        s = self.state
        if s["method"] != m:
            s["method"] = m
            s["base"] = start_scores(m)

    def step_score(self, ab, up):
        self.state["base"] = step_score(self.state["method"], self.state["base"], ab, up)

    def roll_all(self):
        self.state["base"] = start_scores("Roll")

    def roll_one(self, ab):
        self.state["base"] = dict(self.state["base"], **{ab: roll_score()})

    def tap_pick(self, ab):
        self.state["picks"] = next_pick(self.plan(), self.state["picks"], ab)

    def toggle_moved(self):
        s = self.state
        s["moved"] = dict(self.plan()["fixed"]) if s["moved"] is None else None

    def move_bonus(self, ab, d):
        s = self.state
        need = sum(self.plan()["fixed"].values())
        cur = dict(s["moved"] or {})
        nv = cur.get(ab, 0) + d
        if nv < 0 or nv > 2 or (d > 0 and sum(cur.values()) >= need):
            return
        cur[ab] = nv
        s["moved"] = {k: v for k, v in cur.items() if v}

    # ── class & background ──
    def pick_class(self, n):
        s = self.state
        if s["cls"] != n:
            s.update(cls=n, l1_picks={}, spells={}, equip=None)

    def pick_bg(self, n):
        s = self.state
        if s["bg"] != n:
            s.update(bg=n, bg_feat="")

    # ── spells & choices ──
    def level1_data(self):
        s = self.state
        base = self.built(3)
        cards = level1_cards(base, s["l1_picks"])
        tidy = tidy_picks(cards, s["l1_picks"])
        if tidy != s["l1_picks"]:
            s["l1_picks"] = tidy
            cards = level1_cards(base, tidy)
        plan = spell_plan(base)
        keep = {}
        for t in plan.get("tabs", []):
            ok = {r["name"] for r in spell_rows(t)}
            keep[t["key"]] = [n for n in s["spells"].get(t["key"], []) if n in ok][:t["count"]]
        s["spells"] = keep
        return base, cards, plan

    def level1_left(self):
        _, cards, plan = self.level1_data()
        return level1_left(cards, plan, self.state["spells"])

    def toggle_choice(self, cid, value):
        _, cards, _ = self.level1_data()
        self.state["l1_picks"] = toggle_pick(cards, self.state["l1_picks"], cid, value)

    def toggle_spell(self, key, name):
        self.state["spells"] = toggle_spell(spell_plan(self.built(3)), self.state["spells"], key, name)

    # ── equipment ──
    def groups(self):
        return equipment_groups(self.state["cls"])

    def equip_choice(self):
        s = self.state
        groups = self.groups()
        if s["equip"] is None or s["equip_cls"] != s["cls"] or len(s["equip"]) != len(groups):
            s["equip"] = default_choice(groups)
            s["equip_cls"] = s["cls"]
        return s["equip"]

    def pick_option(self, gi, oi):
        groups = self.groups()
        ch = self.equip_choice()
        if 0 <= gi < len(groups) and ch[gi].get("option") != oi:
            ch[gi] = {"option": oi, "anys": [a["pool"][0] if a["pool"] else "" for a in groups[gi]["options"][oi]["anys"]]}

    def set_any(self, gi, ai, text):
        ch = self.equip_choice()
        if not 0 <= gi < len(ch):
            return
        anys = list(ch[gi].get("anys") or [])
        while len(anys) <= ai:
            anys.append("")
        anys[ai] = text
        ch[gi]["anys"] = anys

    def items(self):
        return resolve_equipment(self.groups(), self.equip_choice())

    def finished(self) -> dict:
        c = self.built(4)
        finish(c, self.items(), self.state["extra"])
        return c
