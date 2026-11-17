"""The Notes page (both apps): Character and Backstory at the top, then the
player's own pages in groups they open and close, name, and add to.

    char["notes_pages"]   [{"title", "text", "group"}] -- every page, in order
    char["notes_groups"]  [{"name", "open"}] -- the groups, in order

A page with no group (an older save, the PDF import's page) goes in the
first group. And each background's suggested traits, ideals, bonds and
flaws (data/background_traits.py), to pick from or roll for."""
import random
import re
from datetime import date

DEFAULT_GROUP = "Campaign"
DEFAULT_PAGES = ("Session Log", "Quest Log", "Loot & Treasure")
TRAIT_FIELDS = {"traits": "personality_traits", "ideals": "ideals", "bonds": "bonds", "flaws": "flaws"}
DICE = {"traits": 8, "ideals": 6, "bonds": 6, "flaws": 6}


def _pages(char: dict) -> list:
    pages = char.get("notes_pages")
    if not pages:
        legacy = char.get("notes", "")
        # (a character from before pages: its one block of notes is a page)
        pages = ([{"title": "General", "text": legacy}] if legacy
                 else [{"title": t, "text": ""} for t in DEFAULT_PAGES])
        char["notes_pages"] = pages
    return pages


def groups(char: dict) -> list:
    """[{"name", "open", "pages": [(index into notes_pages, page)]}], putting
    a page whose group is gone (or that never had one) in the first."""
    pages = _pages(char)
    gs = char.get("notes_groups")
    if not isinstance(gs, list):
        gs = char["notes_groups"] = [{"name": DEFAULT_GROUP, "open": True}]
    names = [g["name"] for g in gs]
    out = [{"name": g["name"], "open": bool(g.get("open", True)), "pages": []} for g in gs]
    for i, p in enumerate(pages):
        if p.get("group") not in names:
            if not out:
                gs.append({"name": DEFAULT_GROUP, "open": True}); names.append(DEFAULT_GROUP)
                out.append({"name": DEFAULT_GROUP, "open": True, "pages": []})
            p["group"] = names[0]
        out[names.index(p["group"])]["pages"].append((i, p))
    return out


def _group(char, name):
    return next((g for g in char.get("notes_groups", []) if g["name"] == name), None)


def add_group(char: dict, name: str) -> str:
    """A new group; returns why not ("" when added)."""
    groups(char)
    name = (name or "").strip()
    if not name:
        return "Give the group a name"
    if _group(char, name):
        return f"There's already a group called {name}"
    char["notes_groups"].append({"name": name, "open": True})
    return ""


def rename_group(char: dict, old: str, new: str) -> str:
    groups(char)
    new = (new or "").strip()
    g = _group(char, old)
    if g is None or not new or new == old:
        return "" if new == old else "Give the group a name"
    if _group(char, new):
        return f"There's already a group called {new}"
    g["name"] = new
    for p in _pages(char):
        if p.get("group") == old:
            p["group"] = new
    return ""


def remove_group(char: dict, name: str) -> int:
    """The group and its pages go; returns how many pages went."""
    groups(char)
    before = len(_pages(char))
    char["notes_pages"] = [p for p in _pages(char) if p.get("group") != name]
    char["notes_groups"] = [g for g in char["notes_groups"] if g["name"] != name]
    return before - len(char["notes_pages"])


def toggle_group(char: dict, name: str) -> None:
    g = _group(char, name)
    if g is not None:
        g["open"] = not g.get("open", True)


def add_page(char: dict, group: str, title: str) -> int:
    """A new empty page at the end of `group` (opened, if closed). Returns
    its index, or -1 without a title or group."""
    groups(char)
    title = (title or "").strip()
    g = _group(char, group)
    if not title or g is None:
        return -1
    g["open"] = True
    pages = _pages(char)
    last = max((i for i, p in enumerate(pages) if p.get("group") == group), default=len(pages) - 1)
    pages.insert(last + 1, {"title": title, "text": "", "group": group})
    return last + 1


def rename_page(char: dict, index: int, title: str) -> None:
    pages = _pages(char)
    title = (title or "").strip()
    if title and 0 <= index < len(pages):
        pages[index]["title"] = title


def remove_page(char: dict, index: int) -> None:
    pages = _pages(char)
    if 0 <= index < len(pages):
        pages.pop(index)


def move_page(char: dict, index: int, group: str) -> int:
    """The page to the end of another group; returns its new index."""
    pages = _pages(char)
    if not (0 <= index < len(pages)) or _group(char, group) is None:
        return index
    page = pages.pop(index)
    page["group"] = group
    last = max((i for i, p in enumerate(pages) if p.get("group") == group), default=len(pages) - 1)
    pages.insert(last + 1, page)
    _group(char, group)["open"] = True
    return last + 1


def set_page_text(char: dict, index: int, text: str) -> None:
    pages = _pages(char)
    if 0 <= index < len(pages):
        pages[index]["text"] = text


def new_entry(char: dict, index: int, today: date | None = None) -> str:
    """A heading at the top of a page for today's notes -- "Session 13 ·
    17 Nov 2026" on a page about sessions (numbered after the last one),
    else just the date. Returns the page's new text."""
    pages = _pages(char)
    if not (0 <= index < len(pages)):
        return ""
    page = pages[index]
    d = today or date.today()
    when = f"{d.day} {d.strftime('%b %Y')}"
    text = page.get("text", "")
    if "session" in page.get("title", "").lower():
        nums = [int(n) for n in re.findall(r"(?m)^Session (\d+)\b", text)]
        head = f"Session {max(nums, default=0) + 1} · {when}"
    else:
        head = when
    page["text"] = f"{head}\n\n\n" + text if text.strip() else f"{head}\n\n"
    return page["text"]


# ── Your background's suggestions ─────────────────────────────────────
def suggestions(char: dict) -> dict:
    """{"traits": [...], "ideals": [...], "bonds": [...], "flaws": [...]} for
    the character's background ({} when its book has none)."""
    from dnd_app.data.background_traits import suggestions as _s
    return _s(char.get("background", ""))


def use_suggestion(char: dict, kind: str, text: str) -> str:
    """Puts a suggestion in its box: under what's written already (on a new
    line), unless it's there. Returns the box's new text."""
    key = TRAIT_FIELDS[kind]
    have = (char.get(key) or "").rstrip()
    if text in have:
        return have
    char[key] = f"{have}\n{text}" if have else text
    return char[key]


def roll_suggestion(char: dict, kind: str, rng=random):
    """Rolls the table's die: (the roll, the suggestion), or (0, "") with no
    table. A d8 table of six rows (some books) rolls a d6."""
    rows = suggestions(char).get(kind) or []
    if not rows:
        return 0, ""
    n = rng.randint(1, len(rows))
    return n, rows[n - 1]
