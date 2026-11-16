"""The Bestiary, the same on both apps: finding a creature, and its stat
block as simple rich text (bold, italics, line breaks -- what both a
desktop QLabel/QTextBrowser and Android's Text.StyledText show).

The creatures are dnd_app/data/bestiary.py's (from the reference files).
"""
import html
import re
from fractions import Fraction

from dnd_app.data.bestiary import bestiary, get_creature, SIZES, ABILITIES

# Challenge ratings in order, as the filters offer them
CR_ORDER = ["0", "1/8", "1/4", "1/2"] + [str(n) for n in range(1, 31)]

# How it moves, as the movement filter offers it: (label, speed key)
MOVES = [("Flies", "fly"), ("Hovers", "hover"), ("Swims", "swim"), ("Climbs", "climb"), ("Burrows", "burrow")]


def cr_value(cr: str) -> float:
    try:
        return float(Fraction(cr))
    except (ValueError, ZeroDivisionError):
        return 0.0


def kinds() -> list:
    """Every creature type there is ("Aberration" ... "Undead")."""
    return sorted({c["type"] for c in bestiary().values() if c.get("type")})


def summary_line(c: dict) -> str:
    """'Medium Humanoid · CR 1/8' for a list row."""
    size = c.get("size") or ""
    kind = c.get("type") or ""
    if c.get("swarm_of"):
        kind = f"swarm of {c['swarm_of']}"
    return f"{size} {kind}".strip() + f" · CR {c.get('cr', '0')}"


def moves(c: dict, move: str) -> bool:
    """Does it move that way? `move` is a MOVES label ("Flies") or key."""
    key = dict(MOVES).get(move, move)
    if key == "hover":
        return bool(c.get("hover"))
    return bool((c.get("speed") or {}).get(key))


def search(text: str = "", kind: str = "", size: str = "", cr_min: str = "", cr_max: str = "",
           move: str = "") -> list:
    """The names of the creatures that match, sorted: every word of `text`
    in the name (or the type), of that type and size, within the CR range,
    moving that way (flies, swims...). An empty filter matches everything."""
    words = (text or "").casefold().split()
    lo = cr_value(cr_min) if cr_min else None
    hi = cr_value(cr_max) if cr_max else None
    out = []
    for name, c in bestiary().items():
        if kind and c.get("type") != kind:
            continue
        if size and size not in (c.get("size") or ""):
            continue
        v = c.get("cr_value", 0.0)
        if lo is not None and v < lo or hi is not None and v > hi:
            continue
        if move and not moves(c, move):
            continue
        if words:
            hay = f"{name} {c.get('type', '')} {c.get('type_detail', '')}".casefold()
            if not all(w in hay for w in words):
                continue
        out.append(name)
    return sorted(out, key=str.casefold)


def _text(t: str) -> str:
    """The reference's light markdown as rich text: *italic* and **bold**,
    line breaks kept, everything else escaped."""
    t = html.escape(t or "", quote=False)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    return t.replace("\n", "<br>")


def _mod(score: int) -> str:
    m = (int(score) - 10) // 2
    return f"{m:+d}"


def statblock_html(c: dict, heading: str = "") -> str:
    """A creature's whole stat block as rich text (its name is the page's
    own heading, so it isn't repeated). `heading` colours the section
    titles (ACTIONS, LEGENDARY ACTIONS...), e.g. "#e0b030"."""
    def head(t):
        t = html.escape(t.upper())
        return f'<font color="{heading}"><b>{t}</b></font>' if heading else f"<b>{t}</b>"

    def line(label, value):
        return f"<b>{label}</b> {_text(str(value))}<br>" if value not in ("", None, [], {}) else ""

    parts = []
    kind = c.get("type", "")
    if c.get("type_detail"):
        kind += f" ({c['type_detail']})"
    if c.get("swarm_of"):
        kind = f"swarm of {c['swarm_of']}"
    first = " ".join(x for x in (c.get("level", ""), c.get("size", ""), kind) if x)
    parts.append(f"<i>{html.escape(first)}{', ' + html.escape(c['alignment']) if c.get('alignment') else ''}</i><br><br>")
    ac = f"{c.get('ac', '')}" + (f" ({c['ac_note']})" if c.get("ac_note") else "")
    hp = f"{c.get('hp', '')}" + (f" ({c['hp_dice']})" if c.get("hp_dice") else "")
    parts.append(line("Armor Class", ac) + line("Hit Points", hp) + line("Speed", c.get("speed_text", ""))
                 + line("Initiative", f"{c.get('initiative', 0):+d}") + "<br>")
    ab = c.get("abilities") or {}
    if ab:
        parts.append(" · ".join(f"<b>{a}</b> {ab[a]} ({_mod(ab[a])})" for a in ABILITIES if a in ab) + "<br><br>")
    saves = ", ".join(f"{k.title()} {v:+d}" for k, v in (c.get("saves") or {}).items())
    skills = ", ".join(f"{k} {v:+d}" for k, v in (c.get("skills") or {}).items())
    parts.append(line("Saving Throws", saves) + line("Skills", skills)
                 + line("Damage Vulnerabilities", c.get("vulnerable", ""))
                 + line("Damage Resistances", c.get("resist", ""))
                 + line("Damage Immunities", c.get("immune", ""))
                 + line("Condition Immunities", ", ".join(c.get("condition_immune") or []))
                 + line("Gear", c.get("gear", "")) + line("Senses", c.get("senses", ""))
                 + line("Languages", c.get("languages", "")))
    xp = f" ({c['xp']:,} XP)" if c.get("xp") else ""
    parts.append(f"<b>Challenge</b> {html.escape(c.get('cr', '0'))}{xp} · <b>Proficiency Bonus</b> +{c.get('pb', 2)}<br>")
    for sec in c.get("sections", []):
        parts.append("<br>")
        if sec["title"] != "Traits":
            parts.append(head(sec["title"]) + "<br>")
        if sec.get("intro"):
            parts.append(_text(sec["intro"]) + "<br>")
        for e in sec["entries"]:
            parts.append(f"<b><i>{html.escape(e['name'])}.</i></b> {_text(e['text'])}<br>")
    return "".join(parts)


def creature_html(name: str, heading: str = "") -> str:
    c = get_creature(name)
    return statblock_html(c, heading) if c else ""
