"""The Features page, the same on both apps: the character's features in
sections, each a list of cards.

    feature_page(char) -> [section, ...]

A section:
    key      "race", "background", "feats", "gift:<category>", "class:<name>"
    title    its heading ("Race", "Feats", "Sorcerer 4", "Supernatural Gifts")
    sub      the line beside it ("Half-Elf · Standard", "Draconic Bloodline")
    chip     the filter chip it goes under (its title, a class without its level)
    count    how many of its features the character has (not the ones to come)
    rail     True: its cards come in levels, down a timeline
    levels   [{"level", "label", "state", "cards"}] when rail is True; state is
             "past", "now" or "next" ("next": the next level, shown faded)
    cards    [card, ...] when rail is False
    table    "sorcerer" / "barbarian": a Wild Magic surge table goes with it

A card:
    id       unique on the page
    name     its heading
    summary  one line under it
    text     everything it says, read when the card opens ("" = only the summary)
    tags     [{"text", "kind"}]: kind "uses" (3 / 3, long rest), "action"
             (Action, Bonus action, Reaction), "origin" (where a feat came
             from: "Sorcerer level 4", "Given by the DM"), "sub" (the
             subclass or subrace it's from)
    options  [{"name", "text"}]: the picks a feature asks for (Metamagic,
             invocations, maneuvers...), each with what it does
    future   True: not yet (a race's trait at a later level, the next level)
    find     what a "find a feature" box looks through
"""
import re

from dnd_app.core.features import _lookup, _before_dash, subrace_traits, feature_search_text

_TAG = re.compile(r"<[^>]+>")
_GATE = re.compile(r"^(?:in addition,\s*)?(?:starting |beginning |once you reach |when you reach )?"
                   r"(?:at |from )?(\d+)(?:st|nd|rd|th) level,?\s*", re.IGNORECASE)
_AND_AT = re.compile(r",?\s*and (?=(?:at |from )\d+(?:st|nd|rd|th) level)", re.IGNORECASE)

# A class's per-level line that stands for "your subclass's feature here"
_SLOT_WORDS = (
    'subclass feature', 'archetype feature', 'domain feature', 'circle feature',
    'sacred oath feature', 'primal path feature', 'order feature', 'college feature',
    'ranger archetype feature', 'ranger archetype', '(subclass)', 'martial archetype',
    'roguish archetype', 'sorcerous origin', 'otherworldly patron', 'divine domain',
    'druid circle', 'monastic tradition', 'primal path', 'bardic college',
    'arcane tradition', 'sacred oath', 'ranger conclave', 'alchemical homunculus',
    'path feature', 'bard college feature', 'ki feature',
)

GIFT_TITLES = {"Supernatural Gift": "Supernatural Gifts", "Dark Gift": "Dark Gifts",
               "Character Secret": "Character Secrets"}
GIFT_ORDER = ["Supernatural Gift", "Dark Gift", "Character Secret"]
BY_THE_DM = "Given by the DM"


# ── Small helpers ─────────────────────────────────────────────────────────
def _plain(text: str) -> str:
    return " ".join(_TAG.sub(" ", text or "").split())


def _cap(text: str) -> str:
    text = (text or "").strip()
    return text[:1].upper() + text[1:] if text else text


def _first_sentence(text: str, limit: int = 150) -> str:
    """The first sentence of what a feature does, for its one line."""
    t = _plain(text)
    m = re.match(r"(.+?(?<!ft)(?<!lb)(?<!\bvs)[.!?])(?=\s|$)", t)
    if m:
        t = m.group(1)
    if len(t) > limit:
        cut = t[:limit]
        if cut.rfind(" ") > limit * 0.6:
            cut = cut[:cut.rfind(" ")]
        t = cut.rstrip(".,;: ") + "…"
    return t


def _split_top(text: str, sep: str = " + ") -> list:
    """Split at `sep` where it isn't inside brackets."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if depth == 0 and text.startswith(sep, i):
            out.append(cur); cur = ""; i += len(sep); continue
        cur += ch; i += 1
    out.append(cur)
    return [p.strip() for p in out if p.strip()]


def _name_and_note(entry: str) -> tuple:
    """"Pact Magic (Pact spell slots; recover on SR)" -> ("Pact Magic",
    "Pact spell slots; recover on SR"); "Spellcasting (CHA)" keeps its
    short bracket: ("Spellcasting (CHA)", "")."""
    entry = entry.strip()
    name, note = _before_dash(entry)
    if name:
        return name, note
    if "(" in entry and entry.endswith(")"):
        base, inner = entry.split("(", 1)
        inner = inner[:-1].strip()
        if len(inner) <= 5:
            return entry, ""
        return base.strip(), inner
    if ":" in entry and entry.index(":") <= 60:
        a, b = entry.split(":", 1)
        return a.strip(), b.strip()
    return entry, ""


def _tag(text, kind):
    return {"text": text, "kind": kind}


class _Ctx:
    """What the cards look things up in, worked out once per page."""

    def __init__(self, char):
        self.char = char
        self.resources = list(char.get("resources") or [])
        self.actions = {}
        try:
            from dnd_app.core.actions import build_action_abilities
            from dnd_app.core.action_use import normalize
            self.normalize = normalize
            for bucket, rows in build_action_abilities(char).items():
                if bucket not in ("Action", "Bonus Action", "Reaction"):
                    continue
                for row in rows:
                    self.actions.setdefault(normalize(row[0]), bucket)
        except Exception:
            self.normalize = lambda n: " ".join(re.sub(r"\([^)]*\)", " ", n or "").lower().split())
        self.seen = {}

    def next_id(self, key, name=""):
        """The same card gets the same id each time the page is built (a
        card left open stays open): its section and name, numbered when a
        name comes twice (Infernal Legacy at levels 1, 3 and 5)."""
        base = f"{key}:{name}"
        n = self.seen.get(base, 0) + 1
        self.seen[base] = n
        return base if n == 1 else f"{base}#{n}"

    def uses_tag(self, name, by_key=False):
        n = self.normalize(name)
        key = n.replace(" ", "_")
        keys = (key, "use_" + key) if by_key else ("use_" + key,)
        for r in self.resources:
            if self.normalize(r.get("name", "")) == n or r.get("key") in keys:
                mx, cur = r.get("current_max"), r.get("current", 0)
                if not isinstance(mx, int) or mx <= 0:
                    return None
                if r.get("track") == "pool":
                    unit = "hit points" if "lay on hands" in n else "points"
                    return _tag(f"{cur} / {mx} {unit}", "uses")
                reset = {"LR": "long rest", "SR": "short rest", "SR/LR": "short rest"}.get(r.get("reset", ""), "")
                return _tag(f"{cur} / {mx}" + (f", {reset}" if reset else ""), "uses")
        return None

    def action_tag(self, name, text):
        bucket = self.actions.get(self.normalize(name))
        if not bucket:
            # (only how it starts: "As a bonus action, ..." -- not a
            # bonus action it mentions in passing)
            t = _plain(text).lower().lstrip()
            if re.match(r"(as a |use a |a )?bonus action\b", t):
                bucket = "Bonus Action"
            elif re.match(r"(as an |use your |an |the )?(magic )?action\b", t):
                bucket = "Action"
            elif re.match(r"(as a |use your |a )?reaction\b", t):
                bucket = "Reaction"
        return _tag(bucket[:1] + bucket[1:].lower(), "action") if bucket else None


def _card(ctx, key, name, text="", summary=None, tags=(), options=(), future=False, group="", by_key=False):
    text = text or ""
    if options:
        # (a pick feature opens to your picks, not to every option there is)
        text = ""
    if summary is None:
        summary = _first_sentence(text)
    summary = _cap(summary)
    try:
        # "+CHA" -> the character's own number (the level-up panel does the same)
        from dnd_app.core.calculator import resolve_stat_placeholders
        summary = resolve_stat_placeholders(summary, ctx.char)
        text = resolve_stat_placeholders(text, ctx.char)
    except Exception:
        pass
    if _plain(text) == _plain(summary):
        text = ""
    tags = [t for t in tags if t]
    if not future:
        for t in (ctx.uses_tag(name, by_key), ctx.action_tag(name, f"{summary} {text}")):
            if t and all(x["text"] != t["text"] for x in tags):
                tags.append(t)
    opts = list(options)
    hay = " ".join([name, summary, _plain(text)] + [f"{o['name']} {_plain(o['text'])}" for o in opts]
                   + [t["text"] for t in tags])
    return {"id": ctx.next_id(key, name), "name": name, "summary": summary, "text": text,
            "tags": tags, "options": opts, "future": bool(future),
            "find": feature_search_text(hay, "", group)}


def _options(char, entries, cls=""):
    """Chosen picks, "Name – what it does" each -> [{"name", "text"}]."""
    out = []
    for e in entries or []:
        if not isinstance(e, str) or not e.strip():
            continue
        name, own = _before_dash(e)
        name = name or e.strip()
        text = _lookup(name, cls) or own or _FIGHTING_STYLES.get(name, "")
        out.append({"name": name, "text": _cap(text)})
    return out


def _fighting_styles():
    try:
        from dnd_app.data.classes import FIGHTING_STYLES
    except ImportError:
        return {}
    out = {}
    for line in FIGHTING_STYLES:
        n, t = _before_dash(line)
        if n:
            out[n] = t
    return out


_FIGHTING_STYLES = _fighting_styles()


def _and_list(names):
    names = [n for n in names if n]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


# ── Race ──────────────────────────────────────────────────────────────────
def _race_entries(traits, inherit=True):
    """Trait lines -> [(level, name, text)]: a trait that starts at a later
    level goes there whole; a sentence in one that does ("When you reach
    3rd level, you can cast Hellish Rebuke...") goes there on its own."""
    out, last_name = [], ""
    for line in traits:
        if re.match(r"^\s*\+\d.*\bability scores?\b", line, re.IGNORECASE):
            continue
        if out and re.match(r"^(usable|each |once |using |which |recharg|regain)", line.strip(), re.IGNORECASE):
            lvl, n, t = out[-1]
            out[-1] = (lvl, n, (t.rstrip(". ") + "; " + line.strip()).strip("; "))
            continue
        name, body = _before_dash(line)
        if not name:
            if ":" in line and line.index(":") <= 50:
                name, body = (p.strip() for p in line.split(":", 1))
            elif _GATE.match(line) and inherit and last_name:
                name, body = last_name, line
            else:
                name, body = _cap(line), ""
        last_name = name
        m = _GATE.match(body)
        if m:
            rest = body[m.end():]
            parts = _AND_AT.split(rest)
            out.append((int(m.group(1)), name, _cap(rest if len(parts) == 1 else parts[0])))
            for p in parts[1:]:
                m2 = _GATE.match(p)
                if m2:
                    out.append((int(m2.group(1)), name, _cap(p[m2.end():])))
            continue
        sentences = re.split(r"(?<=[.;])\s+(?=[A-Z])", body) if body else []
        now, later = [], []
        for s in sentences:
            m = _GATE.match(s)
            if m:
                later.append((int(m.group(1)), name, _cap(s[m.end():])))
            else:
                now.append(s)
        out.append((1, name, " ".join(now)))
        out.extend(later)
    return out


def _race_section(ctx):
    char = ctx.char
    race = char.get("species") or char.get("race", "")
    if not race:
        return None
    from dnd_app.data.races import get_race, race_traits_for, DRACONIC_ANCESTRY
    rdata = get_race(race) or {}
    sub = char.get("subrace", "") or ""
    entries = [(lvl, n, t, "") for lvl, n, t in _race_entries(race_traits_for(char))]
    line = next((x for x in rdata.get("subraces", []) if x.split("(")[0].strip() == sub), "")
    if sub and rdata and sub != "Standard" and "default" not in line[:line.find(";") if ";" in line else 40]:
        # (a subrace that's the race as written -- Standard, Asmodeus --
        # says nothing the race's own traits haven't)
        entries += [(lvl, n, t, sub) for lvl, n, t in _race_entries(subrace_traits(rdata, sub))]
    if race == "Dragonborn" and char.get("draconic_ancestry") in DRACONIC_ANCESTRY:
        anc = char["draconic_ancestry"]
        dmg, shape, desc = DRACONIC_ANCESTRY[anc]
        entries.append((1, f"Draconic Ancestry: {anc}",
                        f"{dmg} damage, a {shape}. {desc}. You resist {dmg.lower()} damage.", ""))
    if not entries:
        return None
    from dnd_app.core.character import total_level
    lvl_now = total_level(char) or 1
    levels = {}
    for lvl, name, text, from_sub in entries:
        full = _lookup(name) if lvl == 1 else ""
        if full and len(_plain(full)) < len(_plain(text)):
            full = ""
        card = _card(ctx, "race", name, full or text, summary=_first_sentence(text or full),
                     tags=[_tag(from_sub, "sub")] if from_sub else [], future=lvl > lvl_now, group="Race")
        levels.setdefault(lvl, []).append(card)
    rows = []
    for lvl in sorted(levels):
        state = "next" if lvl > lvl_now else ("now" if lvl == lvl_now and lvl > 1 else "past")
        label = "" if lvl == 1 else (f"At character level {lvl}" if lvl > lvl_now else f"Character level {lvl}")
        rows.append({"level": lvl, "label": label, "state": state, "cards": levels[lvl]})
    sub_line = " · ".join(x for x in (race, sub) if x)
    cards_now = [c for r in rows for c in r["cards"] if not c["future"]]
    if len(rows) == 1:
        return {"key": "race", "title": "Race", "sub": sub_line, "chip": "Race", "count": len(cards_now),
                "rail": False, "levels": [], "cards": rows[0]["cards"], "table": ""}
    return {"key": "race", "title": "Race", "sub": sub_line + " · by character level", "chip": "Race",
            "count": len(cards_now), "rail": True, "levels": rows, "cards": [], "table": ""}


# ── Background ────────────────────────────────────────────────────────────
def _background_section(ctx):
    char = ctx.char
    from dnd_app.data.backgrounds import get_background
    from dnd_app.data.dm_rewards import get_dm_reward
    name = char.get("background", "") or ""
    bg = get_background(name) if name else None
    cards = []
    if bg and bg.get("feature"):
        text = bg.get("feature_desc", "")
        cards.append(_card(ctx, "background", bg["feature"], text, group="Background"))
    for rname in char.get("dm_rewards", []) or []:
        rw = get_dm_reward(rname)
        if rw and rw.get("category") == "Replacement Feature: Background":
            cards.append(_card(ctx, "background", rname, _paras(rw.get("desc", "")),
                               tags=[_tag(BY_THE_DM, "origin"), _tag("Replaces your background feature", "sub")],
                               group="Background"))
    if not cards:
        return None
    return {"key": "background", "title": "Background", "sub": name, "chip": "Background",
            "count": len(cards), "rail": False, "levels": [], "cards": cards, "table": ""}


def _paras(text):
    return "<br><br>".join(p.strip().replace("\n", "<br>") for p in (text or "").split("\n\n") if p.strip())


# ── Feats ─────────────────────────────────────────────────────────────────
def feat_origin(char: dict, feat: str) -> str:
    """Where a feat came from, said plainly: "Sorcerer level 4",
    "Variant Human", "Acolyte background", "Given by the DM" ("" unknown)."""
    if feat in (char.get("dm_feats") or []):
        return BY_THE_DM
    pick = f"feat:{feat}"
    for key, val in (char.get("_choices") or {}).items():
        if not (isinstance(val, list) and (pick in val or (key.endswith("_feat") and feat in val))):
            continue
        m = re.match(r"^(.+)_asi_(\d+)$", key)
        if m:
            return f"{m.group(1).replace('_', ' ')} level {m.group(2)}"
        if key == "variant_human_feat":
            return "Variant Human"
        if key.startswith("dm_feat_"):
            return BY_THE_DM
        if key == "background_feat":
            return f"{char.get('background', '')} background".strip()
        if key.startswith(("race_", "custom_lineage")):
            return char.get("species") or char.get("race", "") or "Race"
    if feat in (char.get("_auto_origin_feat"), char.get("_auto_bg_feat")) and char.get("background"):
        return f"{char['background']} background"
    if (char.get("_choices") or {}).get("background_feat") == feat:
        return f"{char.get('background', '')} background".strip()
    return ""


def _feats_section(ctx):
    char = ctx.char
    from dnd_app.data.feats import get_feat, feat_summary
    from dnd_app.data.feature_tooltips import FEATURE_DESCS
    names = list(dict.fromkeys(list(char.get("feats") or []) + list(char.get("dm_feats") or [])))
    cards = []
    for fname in names:
        fd = get_feat(fname)
        if not fd:
            continue
        text = FEATURE_DESCS.get(fname) or fd.get("special", "")
        tags = []
        origin = feat_origin(char, fname)
        if origin:
            tags.append(_tag(origin, "origin"))
        ab = (char.get("_choices") or {}).get(f"feat_ability_{fname.lower().replace(' ', '_')}")
        if ab:
            tags.append(_tag(f"+1 {ab}", "sub"))
        cards.append(_card(ctx, "feats", fname, text, summary=feat_summary(fd, 150), tags=tags, group="Feats",
                           by_key=True))
    if not cards:
        return None
    return {"key": "feats", "title": "Feats", "sub": "", "chip": "Feats", "count": len(cards),
            "rail": False, "levels": [], "cards": cards, "table": ""}


def _gift_sections(ctx):
    char = ctx.char
    from dnd_app.data.dm_rewards import get_dm_reward
    by_cat = {}
    for rname in char.get("dm_rewards", []) or []:
        rw = get_dm_reward(rname)
        if not rw or rw.get("category") == "Replacement Feature: Background":
            continue
        by_cat.setdefault(rw.get("category") or "Gift", []).append(rw)
    out = []
    for cat in GIFT_ORDER + sorted(c for c in by_cat if c not in GIFT_ORDER):
        if cat not in by_cat:
            continue
        title = GIFT_TITLES.get(cat, cat if cat.endswith("s") else cat + "s")
        cards = []
        for rw in by_cat[cat]:
            tags = [_tag(BY_THE_DM, "origin")]
            cards.append(_card(ctx, "gift", rw["name"], _paras(rw.get("desc", "")),
                               summary=_first_sentence(rw.get("desc", "")), tags=tags, group=title))
        out.append({"key": f"gift:{cat}", "title": title, "sub": "", "chip": title, "count": len(cards),
                    "rail": False, "levels": [], "cards": cards, "table": ""})
    return out


# ── Classes ───────────────────────────────────────────────────────────────
def _short_sub(sub):
    return re.sub(r"\s*\((?:[A-Z][A-Za-z]*)\)\s*$", "", sub or "").strip()


def _subclass_names(cname, sub, D):
    """A subclass's features in order, from its line in data/classes.py."""
    want = (sub or "").lower().strip()
    for line in D.get(cname, {}).get("subclasses", []):
        disp = line.split("–")[0].split("—")[0].strip().lower()
        if disp == want or (want and (want in disp or disp in want)):
            for dash in ("–", "—"):
                if dash in line:
                    return [f.strip() for f in line.split(dash, 1)[1].split(";") if f.strip()]
            return []
    return []


def _subclass_blurb(cname, sub, D):
    want = (sub or "").lower().strip()
    for line in D.get(cname, {}).get("subclasses", []):
        name, rest = _before_dash(line)
        if name and name.split("(")[0].strip().lower() == want:
            return rest
    return ""


def _asi_summary(char, cname, lvl):
    picks = (char.get("_choices") or {}).get(f"{cname}_asi_{lvl}") or []
    feats = [p[5:] for p in picks if isinstance(p, str) and p.startswith("feat:")]
    if feats:
        return f"You took the {feats[0]} feat (see Feats)."
    ups = []
    for p in picks:
        if isinstance(p, str) and p.startswith("asi:"):
            _a, ab, n = (p.split(":") + ["1"])[:3]
            ups.append(f"+{n} {ab}")
    if ups:
        return ", ".join(ups) + "."
    return ""


def _class_options(char, cname, sub, card_name):
    """The picks behind a feature, for its card: (options, short line)."""
    ch = char.get("_choices") or {}
    n = card_name.lower()
    entries = None
    if cname == "Sorcerer" and n.startswith("metamagic"):
        entries = ch.get("sorcerer_metamagic")
    elif cname == "Sorcerer" and n.startswith("dragon ancestor"):
        entries = ch.get("sorcerer_dragon_ancestor")
    elif cname == "Warlock" and n.startswith("eldritch invocations"):
        entries = char.get("eldritch_invocations")
    elif cname == "Warlock" and n.startswith("pact boon"):
        entries = ch.get("warlock_pact_boon")
    elif n.startswith("fighting style"):
        key = "blood_hunter_fighting_style_2" if cname == "Blood Hunter" else f"{cname}_fighting_style"
        entries = ch.get(key)
        if not entries:
            others = [c for c in char.get("classes", []) if c.get("class") in ("Fighter", "Paladin", "Ranger", "Blood Hunter")]
            if len(others) == 1:
                entries = char.get("fighting_styles")
    elif cname == "Fighter" and n.startswith("combat superiority"):
        entries = char.get("battle_master_maneuvers")
        if entries:
            try:
                from dnd_app.core.calculator import get_superiority_die
                sd = get_superiority_die(char)
                entries = [re.sub(r"\bSD\b", sd, m) for m in entries]
            except Exception:
                pass
    elif cname == "Artificer" and n.startswith("infuse item"):
        entries = char.get("artificer_infusions")
    elif cname == "Blood Hunter" and n.startswith("blood maledict"):
        entries = ch.get("blood_hunter_curses")
    elif cname == "Blood Hunter" and ("mutagen" in n or n.startswith("formulas")):
        entries = ch.get("blood_hunter_mutagens")
    elif cname == "Monk" and n.startswith("disciple of the elements"):
        entries = ch.get("four_elements_disciplines")
    elif cname == "Barbarian" and n.startswith("totem spirit"):
        entries = ch.get("totem_spirit_3")
    elif cname == "Barbarian" and n.startswith("aspect of the beast"):
        entries = ch.get("totem_aspect_6")
    elif cname == "Barbarian" and n.startswith("totemic attunement"):
        entries = ch.get("totem_attune_14")
    opts = _options(char, entries, cname)
    if len(opts) == 1 and len(opts[0]["text"]) <= 60:
        # one short pick (a dragon ancestor, a fighting style): said in
        # the card's line, nothing to open
        o = opts[0]
        return [], (f"{o['name']}: {o['text'][:1].lower() + o['text'][1:]}." if o["text"] else f"{o['name']}.")
    return opts, (_and_list([o["name"] for o in opts]) + ".") if opts else ""


def _class_section(ctx, ci, entry, D):
    char = ctx.char
    cname, clvl, sub = entry.get("class", ""), int(entry.get("level", 1) or 1), entry.get("subclass", "") or ""
    cdata = D.get(cname, {})
    features = cdata.get("features", {})
    try:
        from dnd_app.data.class_features import SUBCLASS_FEATURES, CLASS_FEATURE_INDEX, OPTIONAL_CLASS_FEATURES
    except ImportError:
        SUBCLASS_FEATURES, CLASS_FEATURE_INDEX, OPTIONAL_CLASS_FEATURES = {}, {}, {}
    verified = CLASS_FEATURE_INDEX.get(cname, {}).get(sub) if sub else None
    verified = verified if isinstance(verified, dict) else None
    proper = SUBCLASS_FEATURES.get((cname, sub), []) or _subclass_names(cname, sub, D)
    sub_idx = 0
    key = f"class:{cname}"
    group = cname
    short = _short_sub(sub)
    top = min(20, clvl + 1)
    levels = []
    enabled = (char.get("_choices") or {}).get("optional_features", {}) or {}
    rules = char.get("optional_rules", {}) or {}
    for lvl in range(1, top + 1):
        future = lvl > clvl
        cards = []

        def add(name, text="", summary=None, tags=(), options=()):
            cards.append(_card(ctx, key, name, text, summary=summary, tags=tags, options=options,
                               future=future, group=group))

        for raw in features.get(lvl, []):
            for part in _split_top(raw):
                low = part.lower()
                if "(subclass)" in low:
                    base = _name_and_note(re.sub(r"\s*\(subclass\)", "", part, flags=re.IGNORECASE))[0]
                    base = re.sub(r"^choose\s+", "", base, flags=re.IGNORECASE)
                    if sub:
                        blurb = _subclass_blurb(cname, sub, D)
                        add(f"{base}: {sub}", _lookup(base, cname), summary=_cap(blurb) if blurb else None,
                            tags=[_tag(short, "sub")])
                    else:
                        add(base, _lookup(base, cname),
                            summary=("Not chosen yet: choose one on the Choices tab." if not future else None))
                    continue
                if any(w in low for w in _SLOT_WORDS):
                    if verified is not None:
                        continue
                    if "second 1st-level feature" in low and len(proper) <= 5:
                        continue
                    if sub and sub_idx < len(proper):
                        real = proper[sub_idx]
                        sub_idx += 1
                        add(real, _lookup(real, cname), tags=[_tag(short, "sub")])
                    elif sub:
                        sub_idx += 1
                    elif not future:
                        add(_name_and_note(part)[0], summary="Comes with your subclass.")
                    else:
                        add(_name_and_note(part)[0], summary="A feature of your subclass.")
                    continue
                name, note = _name_and_note(part)
                if name.upper().startswith("ASI"):
                    said = "" if future else _asi_summary(char, cname, lvl)
                    add("Ability Score Improvement", _lookup("Ability Score Improvement"),
                        summary=said or ("Not chosen yet: choose on the Choices tab." if not future else None))
                    continue
                text = _lookup(name, cname) or _lookup(name.split("(")[0].strip(), cname) or note
                opts, line = ([], "") if future else _class_options(char, cname, sub, name)
                shown = name.split(" (choose")[0].strip()
                if line and not opts and shown.lower().startswith("fighting style"):
                    shown = f"Fighting Style: {line.split(':')[0].rstrip('.')}"
                add(shown, text, summary=line or None, options=opts)
        if verified is not None:
            for real in verified.get(lvl, []):
                opts, line = ([], "") if future else _class_options(char, cname, sub, real)
                add(real, _lookup(real, cname), summary=line or None, tags=[_tag(short, "sub")], options=opts)
        for opt in (OPTIONAL_CLASS_FEATURES.get(cname, {}) or {}).get(lvl, []):
            rk = opt["name"].lower().replace(" ", "_")
            if enabled.get(opt["name"]) or rules.get(rk):
                tags = [_tag("Optional", "sub")]
                if opt.get("replaces"):
                    tags.append(_tag(f"Replaces {opt['replaces']}", "sub"))
                add(opt["name"], opt.get("desc", ""), tags=tags)
        if cards:
            state = "next" if future else ("now" if lvl == clvl else "past")
            label = "Next level" if future else ("Now" if lvl == clvl else "")
            levels.append({"level": lvl, "label": label, "state": state, "cards": cards})
    # A pick no level line names (an older subclass list): its own card at the
    # class's present level
    names = {c["name"].lower() for r in levels for c in r["cards"]}
    table = ""
    if "wild magic" in sub.lower() and cname in ("Sorcerer", "Barbarian"):
        table = cname.lower()
    count = sum(1 for r in levels for c in r["cards"] if not c["future"])
    return {"key": key, "title": f"{cname} {clvl}", "sub": sub, "chip": cname, "count": count,
            "rail": True, "levels": levels, "cards": [], "table": table, "names": names}


def feature_page(char: dict) -> list:
    """Every section of the Features page, in order: race, background,
    feats, the DM's gifts by kind, then each class."""
    ctx = _Ctx(char)
    if char.get("edition") == "2024":
        try:
            from dnd_app.data.phb2024.classes_2024 import CLASS_DICT_2024 as D
        except ImportError:
            from dnd_app.data.classes import CLASS_DICT as D
    else:
        from dnd_app.data.classes import CLASS_DICT as D
    out = []
    for build in (_race_section, _background_section, _feats_section):
        s = build(ctx)
        if s:
            out.append(s)
    out.extend(_gift_sections(ctx))
    for ci, entry in enumerate(char.get("classes", []) or []):
        s = _class_section(ctx, ci, entry, D)
        s.pop("names", None)
        if s["levels"]:
            out.append(s)
    return out


def page_cards(section: dict) -> list:
    """A section's cards in order, whether or not they come in levels."""
    if section.get("rail"):
        return [c for r in section.get("levels", []) for c in r["cards"]]
    return list(section.get("cards", []))
