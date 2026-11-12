"""What a row on the Features page has behind it: the feature's name and
what it does, looked up the same way by both apps (desktop's hover and
click, Android's tap), and the text a "find a feature" box searches.

A row is plain text as the page shows it:
    "Fey Ancestry"
    "[Lv 1]  Wild Magic: Tides of Chaos"
    "Skill Versatility – you gain proficiency in two skills of your choice"
    "Alert: +5 to initiative. You can't be surprised..."
    "<b>Lucky</b>  [PHB]<br>You have 3 luck points..."     (a DM-granted feat)
"""
import re

_TAG = re.compile(r"<[^>]+>")
_DASHES = (" – ", " — ", " -- ")


def _lookup(name: str) -> str:
    if not name:
        return ""
    from dnd_app.data.feature_tooltips import FEATURE_DESCS
    from dnd_app.data.feature_ui_interactions import FEATURE_CONFIG
    cfg = FEATURE_CONFIG.get(name) or {}
    return FEATURE_DESCS.get(name) or cfg.get("desc", "") or cfg.get("note", "") or ""


def _before_dash(text: str) -> tuple:
    """("Name", "what it does") for "Name – what it does", else ("", "")."""
    cuts = [(text.index(d), d) for d in _DASHES if d in text]
    if not cuts:
        return "", ""
    at, dash = min(cuts)
    return text[:at].strip(), text[at + len(dash):].strip()


def _own_option_text(char: dict, name: str) -> str:
    """What the character's own list says a chosen option does ("Quickened
    Spell \u2013 spend 2 SP: ..." -> "spend 2 SP: ..."): the options a class
    section lists by name only -- Metamagic, invocations, infusions,
    maneuvers, blood curses, mutagens, elemental disciplines."""
    choices = char.get("_choices") or {}
    pools = [char.get("eldritch_invocations"), char.get("artificer_infusions"), char.get("battle_master_maneuvers")]
    pools += [choices.get(k) for k in ("sorcerer_metamagic", "blood_hunter_curses", "blood_hunter_mutagens",
                                       "four_elements_disciplines")]
    for pool in pools:
        for entry in pool or []:
            if isinstance(entry, str):
                own_name, own_text = _before_dash(entry)
                if own_name == name and own_text:
                    return own_text
    return ""


def feature_detail(char: dict, item: str) -> dict:
    """A Features row -> {"tip", "tip_name", "name", "body"}:

      tip       what was looked up for it ("" if nothing was: the row's
                own text is then all there is to read)
      name      the heading for it: the name its text was found under
                ("Tides of Chaos" for "[Lv 1]  Wild Magic: Tides of Chaos",
                "Alert" for "Alert: +5 to initiative...")
      tip_name  the same heading (kept for the hover tooltip)
      body      what a details view says under the heading: tip if there
                is one, else a "Name: what it does" or "Name – what it
                does" row split at its colon or dash ("" for a bare name)
    """
    text = (item or "").strip()
    raw = text[text.index("]") + 1:].strip() if text.startswith("[") and "]" in text else text
    raw_no_paren = raw.split("(")[0].strip()
    raw_no_dash = raw.split("—")[0].strip() if "—" in raw else raw
    raw_no_dash_paren = raw_no_dash.split("(")[0].strip()
    after_colon = raw.split(":", 1)[1].strip() if ":" in raw else ""
    after_colon_no_paren = after_colon.split("(")[0].strip() if after_colon else ""
    # A chosen feat reads "Feat Name: what it does" -- the name comes
    # BEFORE the colon there, the opposite of "Subclass: Feature Name"
    before_colon = raw.split(":", 1)[0].strip() if ":" in raw else ""
    # A DM-granted feat or reward reads "<b>Name</b>  [source]<br>..."
    bold_name = ""
    if "<b>" in text and "</b>" in text:
        bold_name = text.split("<b>", 1)[1].split("</b>", 1)[0].strip()

    tip = ""
    found_as = ""          # the name the text was found under: its heading
    # Unarmored Defense: the looked-up text describes the Barbarian's and
    # the Monk's in one sentence; the character's own AC and what it's
    # made of says more
    if raw_no_paren == "Unarmored Defense":
        from dnd_app.core.calculator import get_ac, get_ac_breakdown
        parts = [(lbl, val) for lbl, val in get_ac_breakdown(char)
                 if "Unarmored Defense" in lbl or "modifier" in lbl.lower()]
        if parts:
            made_of = " + ".join(f"{v:+d} ({lbl})" if i else f"{v} ({lbl})"
                                 for i, (lbl, v) in enumerate(parts))
            tip, found_as = f"Total: AC {get_ac(char)}<br>{made_of}", raw_no_paren
    if not tip:
        for cand in (bold_name, raw, raw_no_paren, raw_no_dash, raw_no_dash_paren,
                     before_colon, after_colon, after_colon_no_paren):
            tip = _lookup(cand)
            if tip:
                found_as = cand
                break
    # "Feature A + Feature B": each one's text, under its name
    if not tip and " + " in (after_colon or raw_no_paren):
        names = [p.strip().split("(")[0].strip() for p in (after_colon or raw_no_paren).split(" + ")]
        found = [f"<b>{n}</b><br>{_lookup(n)}" for n in names if _lookup(n)]
        if found:
            tip, found_as = "<br><br>".join(found), (after_colon_no_paren or raw_no_paren)

    # "[Metamagic]  Quickened Spell, Twinned Spell": a class section's row
    # of chosen options, each one's text under its name (not a "[Lv 3]" row)
    if not tip and text.startswith("[") and "]" in text and not text[1:].lstrip().lower().startswith("lv"):
        names = [n.strip().split("(")[0].strip() for n in raw.split(", ") if n.strip()]
        found = [(n, _lookup(n) or _own_option_text(char, n)) for n in names]
        if names and any(t for _n, t in found):
            tip = "<br><br>".join(f"<b>{n}</b><br>{t}" for n, t in found if t)
            found_as = text[1:text.index("]")].strip()

    # With nothing looked up, the row splits into its name and what it
    # does at whichever comes first, a dash or a colon
    dash_name, dash_body = _before_dash(raw)
    if dash_name and before_colon and len(dash_name) > len(before_colon):
        dash_name = ""
    if tip:
        name, body = found_as, tip
    elif bold_name:
        name, body = bold_name, text.split("</b>", 1)[1].strip()      # (its name heads it: not twice)
    elif dash_name and len(dash_name) <= 60:
        name, body = dash_name, dash_body
    elif before_colon and len(before_colon) <= 60:
        name, body = before_colon, after_colon
    elif len(raw_no_paren) <= 60:
        name, body = raw_no_paren, ""
    else:
        name, body = "Details", raw
    name = _TAG.sub("", name).strip() or "Details"
    return {"tip": tip, "tip_name": name, "name": name, "body": body}


_SOURCE_TAGS = {"PHB", "XGE", "TCE", "SCAG", "MTOF", "FTD", "EGW", "ERLW", "VRGTR", "BGG", "MOT",
                "DSOTDQ", "WBTW", "GGR"}
_ASI = re.compile(r"^\s*[+][A-Z]{3}\s+\d+\s*,?\s*")


def subrace_traits(race_data: dict, subrace: str) -> list:
    """A subrace's own traits, as rows for the Features page -- from its
    "Name (+DEX 2, a trait; another trait, SOURCE)" line in data/races.py,
    less its ability scores (they're with the abilities) and the
    sourcebook tag. Traits are split at semicolons when there are any (a
    trait's own text can hold commas), at commas otherwise."""
    for line in (race_data or {}).get("subraces", []):
        if line.split("(")[0].strip() != subrace or "(" not in line:
            continue
        inner = line[line.find("(") + 1:line.rfind(")")]
        while True:
            m = _ASI.match(inner)
            if not m:
                break
            inner = inner[m.end():]
        inner = inner.strip().rstrip(",").strip()
        last = inner.rfind(",")
        if last >= 0 and inner[last + 1:].strip().upper().replace("/", "") in _SOURCE_TAGS:
            inner = inner[:last].strip()
        return [p.strip() for p in inner.split(";" if ";" in inner else ",") if p.strip()]
    return []


def feature_search_text(item: str, tip: str = "", group: str = "") -> str:
    """What a "find a feature" box looks through for a row: its own text,
    what was looked up for it and its group's heading, in lower case with
    any markup taken out."""
    return " ".join(_TAG.sub(" ", f"{item} {tip} {group}").split()).casefold()


def feature_matches(search_text: str, typed: str) -> bool:
    """Every word typed is somewhere in the row's search text."""
    return all(w in search_text for w in (typed or "").casefold().split())
