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


# ── Mounts and vehicles (not in the Bestiary as such) ──────────────────
def _rows(items):
    """Traits or actions as (name, text) pairs, from tuples or dicts."""
    out = []
    for t in items or []:
        if isinstance(t, (list, tuple)) and len(t) >= 2:
            out.append((str(t[0]), str(t[1])))
        elif isinstance(t, dict):
            out.append((str(t.get("name", "")), str(t.get("text") or t.get("desc") or "")))
    return out


def plain_statblock_html(name: str, sb: dict, heading: str) -> str:
    """A mount's or a vehicle's stat block as the glass shows it (vehicles
    aren't in the Bestiary; a mount's numbers are its stat block's)."""
    import html as _html
    e = _html.escape
    lines = [f'<p style="color:{heading}"><b>{e(name)}</b></p>']
    sub = ", ".join(x for x in (sb.get("size", ""), str(sb.get("type", "") or "")) if x)
    if sub:
        lines.append(f"<p><i>{e(sub)}</i></p>")
    facts = [("Armor Class", sb.get("ac")), ("Hit Points", f"{sb.get('hp', '')}" + (f" ({sb['hit_dice']})" if sb.get("hit_dice") else "")),
             ("Speed", sb.get("speed")), ("Crew", sb.get("crew")), ("Passengers", sb.get("passengers")),
             ("Cargo", sb.get("cargo")), ("Damage Immunities", sb.get("damage_immunities")),
             ("Condition Immunities", sb.get("condition_immunities")), ("Senses", sb.get("senses"))]
    lines.append("<p>" + "<br>".join(f"<b>{k}</b> {e(str(v))}" for k, v in facts if v not in (None, "", "—")) + "</p>")
    ab = sb.get("abilities") or {}
    if isinstance(ab, dict) and any(ab.values()):
        lines.append("<p>" + " · ".join(f"<b>{k}</b> {v}" for k, v in ab.items()) + "</p>")
    for title, key in (("Traits", "traits"), ("Actions", "actions"), ("Reactions", "reactions")):
        rows = _rows(sb.get(key))
        if rows:
            lines.append(f'<p style="color:{heading}"><b>{title.upper()}</b></p>')
            lines.append("".join(f"<p><b><i>{e(n)}.</i></b> {e(t)}</p>" for n, t in rows))
    return "".join(lines)


def mount_vehicle_rows(query: str = "") -> list:
    """Both apps' Mounts & Vehicles list: [{"name", "kind" ("mount" |
    "vehicle"), "section", "line"}], mounts first, then vehicles by kind."""
    from dnd_app.data import items as I
    from dnd_app.data.statblocks import get_mount_statblock, get_vehicle_statblock
    q = (query or "").strip().lower()
    secs = [("Mounts", "mount", [r[0] for r in I.MOUNTS]),
            ("Land vehicles", "vehicle", I.VEHICLES_LAND), ("Water vehicles", "vehicle", I.VEHICLES_WATER),
            ("Air vehicles", "vehicle", I.VEHICLES_AIR), ("Spelljamming vessels", "vehicle", I.VEHICLES_SPELLJAMMING),
            ("Astral vehicles", "vehicle", I.VEHICLES_ASTRAL), ("Combat vehicles", "vehicle", I.VEHICLES_BGDIA),
            ("Magic item vehicles", "vehicle", I.VEHICLES_MAGIC)]
    out = []
    for title, kind, names in secs:
        for n in names:
            if q and q not in n.lower():
                continue
            sb = (get_mount_statblock(n) if kind == "mount" else get_vehicle_statblock(n)) or {}
            line = " · ".join(x for x in (title[:-1] if title.endswith("s") else title,
                                          f"Speed {sb['speed']}" if sb.get("speed") else "") if x)
            out.append({"name": n, "kind": kind, "section": title, "line": line})
    return out


def mount_vehicle_statblock(name: str, kind: str) -> dict:
    from dnd_app.data.statblocks import get_mount_statblock, get_vehicle_statblock
    return (get_mount_statblock(name) if kind == "mount" else get_vehicle_statblock(name)) or {}
