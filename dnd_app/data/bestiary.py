"""Every creature MIMIC knows, for the Bestiary and for whatever a character
turns into or calls up -- read from the stat blocks in docs/reference
(bestiary*.md), and kept as data in bestiary.json beside this file.

Rebuilding the data (after a reference file changes):

    python -m dnd_app.data.bestiary

reads every docs/reference/bestiary*.md, checks each stat block's numbers
against each other, writes bestiary.json, and prints what didn't add up
(and writes it to docs/reference/bestiary-checks.md) so it can be looked
at rather than slipped in quietly.

What a creature looks like (one dict per creature, in BESTIARY by name):

    name, size ("Medium", or "Medium or Small"), type ("Humanoid"),
    type_detail ("Aarakocra", or "" ), swarm_of ("Tiny Beasts", or ""),
    level ("11th-level", for the NPC templates, or ""), alignment,
    ac, ac_note, hp, hp_dice ("8d12 + 8", or the rule for one that scales),
    speed {"walk": 30, "fly": 50, ...}, speed_text, hover,
    initiative, abilities {"STR": 10, ...}, saves {"DEX": 4}, skills
    {"Perception": 5}, gear, vulnerable, resist, immune (damage, as written),
    condition_immune [names], senses, passive, languages,
    cr ("1/8"), cr_value (0.125), xp, pb,
    sections: [{"title": "Traits"|"Actions"|..., "intro": text,
                "entries": [{"name", "text", "attack"?}]}]

An entry's "attack", when it's one, is
    {"kind": "Melee Weapon"..., "to_hit": 4, "reach": "5 ft."|"", "range": "30/120 ft."|"",
     "damage": [{"avg": 4, "dice": "1d4 + 2", "type": "slashing"}], "versatile"?: [...]}
Text keeps the reference's own light markdown (*italic* for spell names).

Two creatures with one name in the reference: an identical copy is kept
once; different creatures each get what tells them apart in brackets --
"Expert (11th level)", "Amphisbaena (Huge Beast)".
"""
import json
import os
import re
from fractions import Fraction

_HERE = os.path.dirname(os.path.abspath(__file__))
_JSON = os.path.join(_HERE, "bestiary.json")

SIZES = ("Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan")
ABILITIES = ("STR", "DEX", "CON", "INT", "WIS", "CHA")
_ABIL_WORD = {"Str": "STR", "Dex": "DEX", "Con": "CON", "Int": "INT", "Wis": "WIS", "Cha": "CHA"}
CONDITION_NAMES = ("Blinded", "Charmed", "Deafened", "Exhaustion", "Frightened", "Grappled",
                   "Incapacitated", "Invisible", "Paralyzed", "Petrified", "Poisoned", "Prone",
                   "Restrained", "Stunned", "Unconscious")
# XP and proficiency bonus by challenge rating (MM p.9)
CR_XP = {"0": 10, "1/8": 25, "1/4": 50, "1/2": 100, "1": 200, "2": 450, "3": 700, "4": 1100,
         "5": 1800, "6": 2300, "7": 2900, "8": 3900, "9": 5000, "10": 5900, "11": 7200,
         "12": 8400, "13": 10000, "14": 11500, "15": 13000, "16": 15000, "17": 18000,
         "18": 20000, "19": 22000, "20": 25000, "21": 33000, "22": 41000, "23": 50000,
         "24": 62000, "25": 75000, "26": 90000, "27": 105000, "28": 120000, "29": 135000,
         "30": 155000}


def pb_for_cr(cr_value: float) -> int:
    return 2 if cr_value < 5 else min(9, 2 + (int(cr_value) - 1) // 4)


def mod(score: int) -> int:
    return (int(score) - 10) // 2


def dice_avg(dice: str) -> int:
    """'2d6 + 4' -> 11 (the stat block's own rounding: down)."""
    total = 0
    for sign, part in re.findall(r"([+-]?)\s*(\d+d\d+|\d+)", dice.replace(" ", "")):
        if "d" in part:
            n, d = part.split("d")
            v = int(n) * (int(d) + 1) / 2
        else:
            v = int(part)
        total += -v if sign == "-" else v
    return int(total // 1)


# ── Reading the reference ───────────────────────────────────────────────
def _clean(line: str) -> str:
    """A stat block line without its '>' and trailing spaces."""
    return line[1:].rstrip() if line.startswith(">") else line.rstrip()


def _fields(lines):
    out = {}
    for line in lines:
        m = re.match(r"- \*\*(.+?)\*\* ?(.*)$", line)
        if m:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def _parse_header(text: str) -> dict:
    """'*11th-level Medium Humanoid (Elf), Neutral Good*' and the like."""
    t = text.strip().strip("*").strip()
    level = ""
    m = re.match(r"(\d+(?:st|nd|rd|th)-level)\s+(.*)$", t)
    if m:
        level, t = m.group(1), m.group(2)
    # alignment: after the last comma (or semicolon, when the brackets
    # hold commas of their own) outside brackets
    depth, cut = 0, -1
    for i, ch in enumerate(t):
        depth += ch == "(" or -(ch == ")")
        if ch in ",;" and depth == 0:
            cut = i
    body, alignment = (t[:cut], t[cut + 1:].strip()) if cut >= 0 else (t, "")
    m = re.match(r"((?:%s)(?: or (?:%s|smaller|larger))*)\s+(.*)$" % ("|".join(SIZES), "|".join(SIZES)),
                 body.strip())
    size, rest = (m.group(1), m.group(2)) if m else ("", body.strip())
    swarm_of = ""
    m = re.match(r"[Ss]warm of (.+)$", rest)
    if m:
        swarm_of, rest = m.group(1).strip(), "Swarm"
    m = re.match(r"(.+?)\s*\((.+)\)\s*$", rest)
    kind, detail = (m.group(1), m.group(2)) if m else (rest, "")
    kind = kind.strip()
    if kind.lower() == "swarm":
        kind = "Swarm"
    return {"level": level, "size": size, "type": kind[:1].upper() + kind[1:], "type_detail": detail,
            "swarm_of": swarm_of, "alignment": alignment}


def _parse_speed(text: str):
    speeds, hover = {}, "hover" in text.lower()
    for part in text.split(","):
        m = re.match(r"\s*([A-Za-z]*)\s*(\d+)\s*ft", part)
        if m:
            speeds[(m.group(1) or "walk").lower()] = int(m.group(2))
    return speeds, hover


def _parse_bonuses(text: str, words) -> dict:
    out = {}
    for name, val in re.findall(r"([A-Z][A-Za-z ]*?)\s*([+-]\d+)", text or ""):
        name = name.strip()
        out[words.get(name, name)] = int(val)
    return out


def _parse_immunities(text: str):
    """'Poison; Poisoned' -> ('Poison', ['Poisoned']); a list of
    conditions alone is all conditions."""
    if not text:
        return "", []
    parts = [p.strip() for p in text.split(";")]
    conds = []
    damage = []
    for p in parts:
        names = [n.strip() for n in re.split(r",\s*", p) if n.strip()]
        if names and all(n.split(" (")[0] in CONDITION_NAMES for n in names):
            conds += names
        else:
            damage.append(p)
    return "; ".join(damage), conds


# The attack line, as the books print it -- and the small ways some
# entries differ: "+6, reach" with no "to hit", "to hit (with advantage
# if ...)", "to hit;", the kind printed twice, no full stop before
# "Hit:", or "Hit:" not in italics.
_ATTACK = re.compile(
    r"\*(?P<kind>(?:Melee|Ranged)(?:\s+or\s+Ranged)?(?:\s+(?:Weapon|Spell))?)\s+Attack:\*\s*"
    r"(?:(?:Melee|Ranged)[^:]*Attack:\s*)?"
    r"(?P<hit>[+-]\d+)(?:\s*to hit)?(?:\s*\([^)]*\))?\s*[,;]\s*(?P<where>.+?),\s*(?P<target>[^*]*?)\.?\s*"
    r"\*?Hit:\*?\s*(?P<on_hit>.*)$", re.S)
_DAMAGE = re.compile(r"(\d+)\s*\((\d+d\d+(?:\s*[+-]\s*\d+)?)\)\s*([a-z]+)\s+damage")
_FLAT = re.compile(r"^\s*(\d+)\s+([a-z]+)\s+damage")


def _parse_attack(text: str):
    m = _ATTACK.search(text)
    if not m:
        return None
    kind = re.sub(r"\s+", " ", m.group("kind")).strip()
    where = m.group("where")
    reach = re.search(r"reach (\d+ ft\.)", where)
    rng = re.search(r"range[sd]? ([\d/]+ ft\.)", where)
    on_hit = m.group("on_hit")
    versatile = None
    vm = re.search(r",?\s*or\s+(\d+\s*\(\d+d\d+(?:\s*[+-]\s*\d+)?\)\s*[a-z]+\s+damage)\s+if used with two hands", on_hit)
    if vm:
        versatile = [{"avg": int(a), "dice": d, "type": t} for a, d, t in _DAMAGE.findall(vm.group(1))]
        on_hit = on_hit[:vm.start()] + on_hit[vm.end():]
    dmg = [{"avg": int(a), "dice": re.sub(r"\s+", " ", d), "type": t} for a, d, t in _DAMAGE.findall(on_hit)]
    flat = _FLAT.match(on_hit)
    if flat and not dmg:                     # "Hit: 1 piercing damage."
        dmg = [{"avg": int(flat.group(1)), "dice": "", "type": flat.group(2)}]
    out = {"kind": kind, "to_hit": int(m.group("hit")), "reach": reach.group(1) if reach else "",
           "range": rng.group(1) if rng else "", "damage": dmg}
    if versatile:
        out["versatile"] = versatile
    return out


def _parse_body(lines) -> list:
    """The traits, then each '### Section': entries that start
    '***Name.***', with the text that follows them; anything before the
    first entry is the section's own introduction."""
    sections = [{"title": "Traits", "intro": "", "entries": []}]
    cur_entry = None
    for raw in lines:
        line = raw.strip()
        if line.startswith("### "):
            sections.append({"title": line[4:].strip(), "intro": "", "entries": []})
            cur_entry = None
            continue
        if line.startswith("## "):          # (a stray heading inside a block)
            continue
        # an entry: "***Name.*** text", or in a legendary, lair or regional
        # list "- **Name.** text"; any other "- text" is a point of the
        # entry (or introduction) it's under
        m = re.match(r"\*\*\*(.+?)\*\*\*\s*(.*)$", line) or re.match(r"-\s+\*\*(.+?)\*\*\s*(.*)$", line)
        if not m and line.startswith("- "):
            line = "• " + line[2:].strip()
        if m:
            name = m.group(1).strip()
            name = name[:-1] if name.endswith(".") else name
            cur_entry = {"name": name.strip(), "text": m.group(2).strip()}
            sections[-1]["entries"].append(cur_entry)
            continue
        sec = sections[-1]
        if cur_entry is None:
            sec["intro"] = (sec["intro"] + ("\n" if sec["intro"] else "") + line) if line else sec["intro"] + ("\n" if sec["intro"] else "")
        else:
            cur_entry["text"] += "\n" + line
    for sec in sections:
        sec["intro"] = re.sub(r"\n{3,}", "\n\n", sec["intro"]).strip()
        for e in sec["entries"]:
            e["text"] = re.sub(r"\n{3,}", "\n\n", e["text"]).strip()
            atk = _parse_attack(e["text"])
            if atk:
                e["attack"] = atk
    return [s for s in sections if s["entries"] or s["intro"]]


def parse_block(block: str) -> dict:
    """One stat block (the text between two '---' rules) -> a creature."""
    lines = [_clean(l) for l in block.splitlines() if l.startswith(">")]
    parts, cur = [], []
    for line in lines:
        if line.strip() == "___":
            parts.append(cur)
            cur = []
        else:
            cur.append(line)
    parts.append(cur)
    head = [l for l in parts[0] if l.strip()]
    name = re.sub(r"^##\s*", "", head[0]).strip()
    c = {"name": name}
    c.update(_parse_header(head[1] if len(head) > 1 else ""))
    f = _fields(parts[1]) if len(parts) > 1 else {}
    table = [l for l in (parts[2] if len(parts) > 2 else []) if l.startswith("|")]
    f.update(_fields(parts[3]) if len(parts) > 3 else {})
    body = [l for p in parts[4:] for l in p]

    m = re.match(r"(\d+)\s*(?:\((.*)\))?", f.get("Armor Class", ""))
    c["ac"] = int(m.group(1)) if m else 0
    c["ac_note"] = (m.group(2) or "").replace("*", "") if m else ""
    hp_text = f.get("Hit Points", "")
    m = re.match(r"(\d+)\s*\((\d+d\d+(?:\s*[+-]\s*\d+)?)\)\s*$", hp_text)
    if m:
        c["hp"], c["hp_dice"] = int(m.group(1)), re.sub(r"\s+", " ", m.group(2))
    else:
        m = re.match(r"(\d+)\s*$", hp_text)
        c["hp"] = int(m.group(1)) if m else int((re.match(r"\d+", hp_text) or ["0"])[0])
        c["hp_dice"] = "" if m else hp_text
    c["speed"], c["hover"] = _parse_speed(f.get("Speed", ""))
    c["speed_text"] = f.get("Speed", "")
    m = re.match(r"([+-]\d+)", f.get("Initiative", ""))
    c["initiative"] = int(m.group(1)) if m else 0
    c["abilities"] = {}
    c["_table_mods"] = {}
    if len(table) >= 3:
        cells = [x.strip() for x in table[2].strip("|").split("|")]
        for ab, cell in zip(ABILITIES, cells):
            m = re.match(r"(\d+)\s*\(([+-−–]?\d+)\)", cell)
            if m:
                c["abilities"][ab] = int(m.group(1))
                c["_table_mods"][ab] = int(m.group(2).replace("−", "-").replace("–", "-"))
    c["saves"] = _parse_bonuses(f.get("Saving Throws", ""), _ABIL_WORD)
    c["skills"] = _parse_bonuses(f.get("Skills", ""), {})
    c["gear"] = f.get("Gear", "").replace("*", "")
    c["vulnerable"] = f.get("Damage Vulnerabilities", "")
    c["resist"] = f.get("Damage Resistances", "")
    c["immune"], c["condition_immune"] = _parse_immunities(f.get("Immunities", ""))
    if f.get("Damage Immunities"):
        c["immune"] = "; ".join(x for x in (c["immune"], f["Damage Immunities"]) if x)
    if f.get("Condition Immunities"):
        c["condition_immune"] += [n.strip() for n in f["Condition Immunities"].split(",") if n.strip()]
    c["senses"] = f.get("Senses", "")
    m = re.search(r"[Pp]assive Perception (\d+)", c["senses"])
    c["passive"] = int(m.group(1)) if m else 10 + mod(c["abilities"].get("WIS", 10))
    c["languages"] = f.get("Languages", "")
    ch = f.get("Challenge", "")
    m = re.match(r"([\d/]+)", ch)
    c["cr"] = m.group(1) if m else "0"
    try:
        c["cr_value"] = float(Fraction(c["cr"]))
    except (ValueError, ZeroDivisionError):
        c["cr_value"] = 0.0
    m = re.search(r"XP ([\d,]+)", ch)
    c["xp"] = int(m.group(1).replace(",", "")) if m else 0
    m = re.search(r"PB \+(\d+)", ch) or re.match(r"\+(\d+)", f.get("Proficiency Bonus", ""))
    c["pb"] = int(m.group(1)) if m else pb_for_cr(c["cr_value"])
    c["sections"] = _parse_body(body)
    return c


def read_reference(text: str) -> list:
    blocks = [b for b in re.split(r"\n---\n", text) if re.search(r"^>## ", b, re.M)]
    return [(parse_block(b), b) for b in blocks]


# ── Checking the numbers ────────────────────────────────────────────────
def check(c: dict) -> list:
    """What doesn't add up in a creature's stat block: one line each."""
    out = []
    for ab, score in c["abilities"].items():
        if c["_table_mods"].get(ab) != mod(score):
            out.append(f"{ab} {score} is shown with modifier {c['_table_mods'].get(ab):+d}")
    if len(c["abilities"]) != 6:
        out.append("ability scores incomplete")
    if c.get("hp_dice") and re.fullmatch(r"\d+d\d+(?: [+-] \d+)?", c["hp_dice"]) and dice_avg(c["hp_dice"]) != c["hp"]:
        out.append(f"HP {c['hp']} but {c['hp_dice']} averages {dice_avg(c['hp_dice'])}")
    if c["cr"] in CR_XP and c["xp"] and c["xp"] != CR_XP[c["cr"]]:
        out.append(f"CR {c['cr']} is {CR_XP[c['cr']]} XP, shown as {c['xp']}")
    if c["pb"] != pb_for_cr(c["cr_value"]) and not c.get("level"):
        out.append(f"CR {c['cr']} has proficiency +{pb_for_cr(c['cr_value'])}, shown as +{c['pb']}")
    dex = mod(c["abilities"].get("DEX", 10))
    if c["initiative"] not in (dex, dex + c["pb"], dex + 2 * c["pb"]):
        out.append(f"initiative {c['initiative']:+d} isn't DEX {dex:+d} (or with proficiency)")
    for ab, v in c["saves"].items():
        if ab in c["abilities"] and v - mod(c["abilities"][ab]) not in (c["pb"], 2 * c["pb"]):
            out.append(f"{ab} save {v:+d} is DEX/ability {mod(c['abilities'][ab]):+d} + {v - mod(c['abilities'][ab])}"
                       .replace("DEX/ability", "ability"))
    mods = {ab: mod(s) for ab, s in c["abilities"].items()}
    for sec in c["sections"]:
        for e in sec["entries"]:
            a = e.get("attack")
            if not a:
                continue
            for d in a["damage"] + a.get("versatile", []):
                if dice_avg(d["dice"]) != d["avg"]:
                    out.append(f"{e['name']}: {d['dice']} averages {dice_avg(d['dice'])}, shown as {d['avg']}")
            base = a["to_hit"] - c["pb"]
            if "Weapon" in a["kind"] and base not in (mods.get("STR"), mods.get("DEX")):
                near = min((mods.get("STR", 0), mods.get("DEX", 0)), key=lambda m: abs(base - m))
                out.append(f"{e['name']}: {a['to_hit']:+d} to hit is {base - near:+d} from "
                           f"STR or DEX + proficiency ({near + c['pb']:+d})")
    return out


# ── Building the data file ──────────────────────────────────────────────
def _tell_apart(group):
    """Different creatures sharing a name: what to put in brackets after
    each -- the first thing that's different for every one of them."""
    def names(c):
        return {_same_text(e["name"].split("(")[0]): e["name"].split(" (")[0]
                for s in c["sections"] for e in s["entries"]}

    def own_entries(c):
        mine = names(c)
        others = set().union(*(set(names(o)) for o in group if o is not c))
        only = sorted(k for k in mine if k not in others)
        return f"with {mine[only[0]]}" if only else ""
    for key in (lambda c: c["level"].replace("-level", " level"),
                lambda c: f"{c['size']} {c['type']}",
                lambda c: f"CR {c['cr']}",
                lambda c: f"AC {c['ac']}, {c['hp']} HP",
                lambda c: c["alignment"],
                lambda c: c["speed_text"] if len(c["speed_text"]) <= 40 else "",
                own_entries):
        tags = [key(c) for c in group]
        if all(tags) and len(set(tags)) == len(tags):
            return tags
    return [f"version {i + 1}" for i in range(len(group))]


def _mpmm_reprint(group):
    """Of two printings of one creature, Monsters of the Multiverse's (as
    a one-item list), or [] if they aren't told apart that way. That book
    wrote "Typically" before alignments, made its people "Any Alignment",
    and moved spellcasting from a trait into the actions."""
    if len(group) != 2:
        return []
    a, b = group

    def typically(c):
        return c["alignment"].lower().startswith("typically")

    def any_align(c):
        return c["alignment"].lower() == "any alignment"

    def innate(c):
        return any(e["name"].startswith("Innate Spellcasting") for s in c["sections"] for e in s["entries"])

    def cast_action(c):
        return any(s["title"] == "Actions" and e["name"].startswith("Spellcasting")
                   for s in c["sections"] for e in s["entries"])
    for test in (typically, any_align):
        if test(a) != test(b):
            return [a if test(a) else b]
    if innate(a) != innate(b):
        newer = b if innate(a) else a
        if cast_action(newer) or not innate(newer):
            return [newer]
    return []


def _same_text(raw: str) -> str:
    """A stat block's words alone: two copies that differ only in
    punctuation, spacing or capitals are the same creature."""
    return re.sub(r"[^a-z0-9]+", "", raw.lower())


def build(ref_dir=None) -> tuple:
    """Every docs/reference/bestiary*.md -> (creatures by name, problems)."""
    ref_dir = ref_dir or os.path.join(_HERE, "..", "..", "docs", "reference")
    found = []
    for fn in sorted(os.listdir(ref_dir)):
        if fn.startswith("bestiary") and fn.endswith(".md") and "checks" not in fn:
            with open(os.path.join(ref_dir, fn), encoding="utf-8") as fh:
                found += read_reference(fh.read())
    by_name = {}
    for c, raw in found:
        by_name.setdefault(c["name"], []).append((c, raw))
    out, problems = {}, {}
    for name, group in by_name.items():
        seen, uniq = set(), []
        for c, raw in group:
            key = _same_text(raw)
            if key not in seen:
                seen.add(key)
                uniq.append(c)
        if len(uniq) > 1:
            # Monsters of the Multiverse's reprint of an older creature is
            # named as the races are ("Allip (MPMM)"); the original keeps
            # the name
            newer = _mpmm_reprint(uniq)
            if newer:
                newer[0]["name"] = f"{name} (MPMM)"
                newer[0]["base_name"] = name
            else:
                for c, tag in zip(uniq, _tell_apart(uniq)):
                    c["name"] = f"{name} ({tag})"
                    c["base_name"] = name
        for c in uniq:
            bad = check(c)
            if bad:
                problems[c["name"]] = bad
            c.pop("_table_mods", None)
            out[c["name"]] = c
    return dict(sorted(out.items())), problems


def write(creatures: dict, problems: dict, ref_dir=None) -> None:
    with open(_JSON, "w", encoding="utf-8") as fh:
        json.dump(creatures, fh, ensure_ascii=False, separators=(",", ":"))
    ref_dir = ref_dir or os.path.join(_HERE, "..", "..", "docs", "reference")
    lines = ["# Bestiary: what didn't add up",
             "",
             "Made by `python -m dnd_app.data.bestiary` from the bestiary reference files.",
             "Each creature's numbers are checked against each other: ability modifiers,",
             "hit points against hit dice, XP and proficiency against CR, initiative and",
             "saves against abilities, attack bonuses and damage averages. A to-hit over",
             "STR or DEX + proficiency is often a magic weapon (+1 to +3) or an attack",
             "made with another ability; the rest are worth a look in the book.",
             "", f"{len(problems)} of {len(creatures)} creatures listed.", ""]
    for name in sorted(problems):
        lines.append(f"- **{name}**")
        lines += [f"  - {p}" for p in problems[name]]
    with open(os.path.join(ref_dir, "bestiary-checks.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ── At run time ─────────────────────────────────────────────────────────
_CACHE = None


def bestiary() -> dict:
    """Every creature by name (loaded the first time it's asked for)."""
    global _CACHE
    if _CACHE is None:
        try:
            with open(_JSON, encoding="utf-8") as fh:
                _CACHE = json.load(fh)
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def get_creature(name: str):
    return bestiary().get(name)


if __name__ == "__main__":
    creatures, problems = build()
    write(creatures, problems)
    n = sum(len(v) for v in problems.values())
    print(f"{len(creatures)} creatures written to {os.path.relpath(_JSON)}; "
          f"{n} things to look at in {len(problems)} of them (docs/reference/bestiary-checks.md)")
