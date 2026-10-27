"""The inventory (char["equipment"]), the same on both apps: what each
item weighs and is worth, stacks of the same item, and taking items out.

  catalog_weight_cost(name) -> (lb, gp) each, from the rules' tables:
      weapons (a silvered one costs 100 gp more, an adamantine one 500),
      armor, adventuring gear, tools. (0, 0) for an item that isn't in them.
  item_weight(entry), item_cost(entry) -- one of it: its own number if it
      has one, else the catalog's (starting gear came in with 0s)
  money_text(gp) -> "15 gp", "5 sp", "2 cp"
  merge_stacks(char) -- the same plain item listed twice (a rogue's two
      daggers) becomes one row of 2
  name_tool_kinds(char) -- a background's "Artisan's tools" becomes the
      kind picked for it
  remove_items(char, entry, n) -- n of that row go; a weapon, armor or
      shield that's no longer there is no longer in hand or worn
"""
import re

from dnd_app.data.items import ADVENTURING_GEAR, ARMOR_DICT, TOOL_STATS, WEAPON_DICT

_GEAR = {row[0].lower(): (row[1] or 0, row[2] if len(row) > 2 and row[2] else 0) for row in ADVENTURING_GEAR}
_TOOLS = {name.lower(): stats for name, stats in TOOL_STATS.items()}
# how starting gear and backgrounds word some items -> the gear table's name
_ALIASES = {
    "arrows (20)": "ammunition, arrows (20)", "crossbow bolts (20)": "ammunition, bolts (20)",
    "hempen rope (50 feet)": "rope, hempen (50 ft)", "silk rope (50 feet)": "rope, silk (50 ft)",
    "50 ft hempen rope": "rope, hempen (50 ft)", "50 ft rope": "rope, hempen (50 ft)",
    "50 ft silk rope": "rope, silk (50 ft)", "ball bearings (bag of 1,000)": "ball bearings (1000)",
    "costume": "clothes, costume", "dark common clothes": "clothes, common",
    "dark common clothes with hood": "clothes, common", "commoner's clothes": "clothes, common",
    "common clothes in faction style": "clothes, common", "winter blanket": "blanket",
    "rusty manacles": "manacles", "bottle of ink": "ink (1 oz bottle)", "bottle of black ink": "ink (1 oz bottle)",
    "bottle of blue ink": "ink (1 oz bottle)", "bottle of colored ink": "ink (1 oz bottle)",
    "ink": "ink (1 oz bottle)", "pen": "ink pen", "quill": "ink pen", "blank book": "book",
    "deck of cards": "playing card set", "deck of cards/dice": "playing card set",
    "belaying pin (club)": "club", "belaying pin": "club", "wooden shield": "shield",
    "scholar's robes": "robes", "cracked hourglass": "hourglass",
    "holy water": "holy water (flask)", "flask of holy water": "holy water (flask)",
    "oil": "oil (flask)", "flask of oil": "oil (flask)", "mirror": "mirror, steel",
    "scroll case": "case, map or scroll", "scroll case with notes": "case, map or scroll",
    "house signet ring": "signet ring", "order signet ring": "signet ring",
    "half-empty bottle": "bottle, glass",
    # weapons by another name: a walking staff is a quarterstaff
    "staff": "quarterstaff", "dagger that belonged to a fallen comrade": "dagger",
}
# a book by what's in it ("Book of poetry", "Tome of history", a diary) is a book
_BOOK_WORDS = {"book", "tome", "diary", "ledger"}


def _table_name(name: str) -> str:
    """The rules' own name for an item ("Rope, Hempen (50 ft)" for a pack's
    "Hempen rope (50 feet)"), lower case, or "" if no table has it."""
    n = name.lower().strip()
    n = _ALIASES.get(n, n)
    if n in _GEAR or n in _TOOLS:
        return n
    words = n.split()
    if len(words) > 1:                       # "common clothes" -> "clothes, common"
        flipped = f"{words[-1]}, {' '.join(words[:-1])}"
        if flipped in _GEAR:
            return flipped
    if _BOOK_WORDS & set(re.findall(r"[a-z]+", n)) and not _magic_item(n):
        return "book"                        # not a Tome of Clear Thought
    return ""


_MAGIC_NAMES = set()


def _magic_item(n: str) -> bool:
    if not _MAGIC_NAMES:
        from dnd_app.data.magic_items import ALL_MAGIC_ITEMS
        _MAGIC_NAMES.update(i["name"].lower() for i in ALL_MAGIC_ITEMS)
    return n in _MAGIC_NAMES


def same_item_key(name: str) -> str:
    """One key for every way an item is written: "Holy water" and the gear
    table's "Holy Water (flask)", "Oil" and "Oil (flask)"."""
    return _table_name(name) or name.strip().lower()


def consumable_kind(entry: dict) -> str:
    """"potion" for a potion, "scroll" for a scroll you read (not the case
    that holds one), "" for anything else."""
    from dnd_app.data.items import is_scroll_name
    if not isinstance(entry, dict):
        return ""
    name = str(entry.get("name", ""))
    if entry.get("type") == "Potion" or "potion" in name.lower():
        return "potion"
    return "scroll" if is_scroll_name(name) else ""


def _gear_stats(name: str):
    key = _table_name(name)
    return (_GEAR.get(key) or _TOOLS.get(key)) if key else None


def catalog_weight_cost(name: str) -> tuple:
    """(weight in lb, cost in gp) of one `name`, from the rules' tables."""
    from dnd_app.core.magic_items import parse_magic_suffix, parse_material_prefix
    if not name:
        return 0, 0
    plain, material = parse_material_prefix(name)
    base, bonus = parse_magic_suffix(plain)
    other = _ALIASES.get(base.lower(), "").title()
    if base not in WEAPON_DICT and (other in WEAPON_DICT or other in ARMOR_DICT):
        base = other                          # a belaying pin is a club, a wooden shield a shield
    w = WEAPON_DICT.get(base)
    if w:
        extra = {"Silvered": 100, "Adamantine": 500}.get(material, 0)
        return w.get("weight", 0) or 0, (0 if bonus else (w.get("cost", 0) or 0) + extra)
    a = ARMOR_DICT.get(base)
    if a and a.get("type") != "none":
        return a.get("weight", 0) or 0, (0 if bonus else a.get("cost", 0) or 0)
    stats = _gear_stats(name)
    if stats:
        return stats
    worth = re.search(r"worth (\d[\d,]*) gp", name, re.I)   # "small jewelry piece worth 10 gp"
    return (0, int(worth.group(1).replace(",", ""))) if worth else (0, 0)


def item_weight(entry: dict) -> float:
    """One of this item's weight, in lb."""
    own = entry.get("weight") or 0
    return own if own else catalog_weight_cost(entry.get("name", ""))[0]


def item_cost(entry: dict) -> float:
    """One of this item's cost, in gp."""
    own = entry.get("cost") or 0
    return own if own else catalog_weight_cost(entry.get("name", ""))[1]


def money_text(gp) -> str:
    """A price the way the rules write it: 15 gp, 5 sp, 2 cp ("" for none)."""
    if not gp:
        return ""
    if gp >= 1:
        return f"{gp:,.2f}".rstrip("0").rstrip(".") + " gp"
    cp = round(gp * 100)
    return f"{cp // 10} sp" if cp % 10 == 0 else f"{cp} cp"


def weight_text(lb) -> str:
    return f"{lb:,.2f}".rstrip("0").rstrip(".") + " lb" if lb else ""


_PLAIN_KEYS = {"name", "qty", "weight", "cost", "notes"}


def _plain(entry: dict) -> bool:
    return isinstance(entry, dict) and set(entry) <= _PLAIN_KEYS and not entry.get("notes")


def merge_stacks(char: dict) -> bool:
    """The same plain item in two rows becomes one row with both counted
    (starting equipment lists a rogue's daggers one by one). True if any
    rows were merged."""
    out, seen, merged = [], {}, False
    for e in char.get("equipment", []):
        if _plain(e) and e.get("name"):
            key = e["name"].strip().lower()           # "Holy Symbol" and "Holy symbol" too
            first = seen.get(key)
            if first is not None:
                first["qty"] = first.get("qty", 1) + e.get("qty", 1)
                for k in ("weight", "cost"):
                    if not first.get(k) and e.get(k):
                        first[k] = e[k]
                merged = True
                continue
            seen[key] = e
        out.append(e)
    if merged:
        char["equipment"] = out
    return merged


def fill_catalog_numbers(entry: dict) -> dict:
    """Give an item its weight and cost from the rules' tables when it has none."""
    w, c = catalog_weight_cost(entry.get("name", ""))
    if not entry.get("weight") and w:
        entry["weight"] = w
    if not entry.get("cost") and c:
        entry["cost"] = c
    return entry


def owned_count(char: dict, name: str) -> int:
    """How many of `name` are in the inventory, every row of it counted."""
    return sum(e.get("qty", 1) for e in char.get("equipment", [])
               if isinstance(e, dict) and e.get("name") == name)


def keep_hands_in_step(char: dict, name: str) -> None:
    """After items go: a weapon no longer owned (as many times as it's in
    hand) is put away, armor no longer owned is taken off, and a shield
    no longer owned is put down. A magic copy (char["magic_items"]) still
    counts."""
    owned = owned_count(char, name) + sum(
        1 for e in char.get("magic_items", []) if isinstance(e, dict) and e.get("name") == name)
    held = char.get("equipped_weapons", [])
    while held.count(name) > owned:
        held.remove(name)
    if owned == 0:
        if char.get("armor_worn") == name:
            char["armor_worn"] = "No Armor"
        if ARMOR_DICT.get(name, {}).get("type") == "shield" and char.get("shield") and not _any_shield(char):
            char["shield"] = False


def _any_shield(char: dict) -> bool:
    """A shield is still in the inventory, or a magic one is equipped."""
    from dnd_app.data.magic_items import get_magic_item
    if any(ARMOR_DICT.get(e.get("name", ""), {}).get("type") == "shield"
           for e in char.get("equipment", []) if isinstance(e, dict)):
        return True
    return any(isinstance(e, dict) and e.get("equipped", True)
               and (get_magic_item(e.get("name", "")) or {}).get("type") == "Shield"
               for e in char.get("magic_items", []))


def remove_items(char: dict, entry: dict, n: int = 1) -> int:
    """Take n of this inventory row away (the row goes when none are
    left); returns how many went. Only this row -- another row of the same
    name stays."""
    eq = char.get("equipment", [])
    if not any(e is entry for e in eq):
        return 0
    have = entry.get("qty", 1) or 1         # a row is one of it, at least
    n = max(0, min(n, have))
    if n >= have:
        char["equipment"] = [e for e in eq if e is not entry]
    else:
        entry["qty"] = have - n
    keep_hands_in_step(char, entry.get("name", ""))
    return n


def set_item_count(char: dict, entry: dict, qty: int) -> None:
    """How many of this row you have (0 takes it out)."""
    have = entry.get("qty", 1)
    if qty < have:
        remove_items(char, entry, have - qty)
    elif qty > have:
        entry["qty"] = qty


# a soldier's "deck of cards/dice" is the gaming set picked, either one
_EITHER_SET = {"deck of cards/dice": "Dice set or playing card set"}


def name_tool_kinds(char: dict) -> bool:
    """A background's tools written as a kind ("Artisan's tools", "Musical
    instrument", "Gaming set", "Disguise kit or musical instrument") become
    the one you picked for that background (Smith's tools, a lute), with its
    weight and cost -- and so its check. Until you pick, the row stays as
    written. True if any row was named."""
    from dnd_app.data.backgrounds import _tool_kind_pool
    picks = [p for p in ((char.get("_choices") or {}).get("bg_tool_profs") or []) if isinstance(p, str)]
    if not picks:
        return False
    named = False
    for e in char.get("equipment", []):
        name = e.get("name", "") if _plain(e) else ""
        kind = _EITHER_SET.get(name.lower(), "")
        if not name or not kind and (_table_name(name) or name in WEAPON_DICT or name in ARMOR_DICT):
            continue                         # a real item already
        pool = {t.lower() for t in _tool_kind_pool(kind or name)}
        pick = next((p for p in picks if p.lower() in pool), None)
        if pick:
            picks.remove(pick)
            e["name"] = pick
            e["weight"], e["cost"] = 0, 0
            fill_catalog_numbers(e)
            named = True
    return named


def add_item(char: dict, name: str, qty: int = 1) -> dict:
    """Put qty of `name` in the inventory -- onto its row if there's a
    plain one already -- with the rules' weight and cost. Returns the row."""
    eq = char.setdefault("equipment", [])
    key = name.strip().lower()
    row = next((e for e in eq if _plain(e) and str(e.get("name", "")).strip().lower() == key), None)
    if row is not None:
        row["qty"] = row.get("qty", 1) + qty
        return fill_catalog_numbers(row)
    row = fill_catalog_numbers({"name": name, "qty": qty, "weight": 0, "cost": 0, "notes": ""})
    eq.append(row)
    return row


# ── Starting equipment ────────────────────────────────────────────────────
_COUNT_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twenty": 20}
# how a background counts some items -> the item, one of it
_ONE_OF = {"torches": "Torch", "trinkets": "Trinket", "small knives": "Small knife",
           "sheets of paper": "Paper (one sheet)", "sticks incense": "Incense",
           "sticks of incense": "Incense", "candles": "Candle", "stakes": "Stake", "torch": "Torch"}


def _split_top(text: str) -> list:
    """Split at commas that aren't inside brackets."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def gear_from_text(text: str) -> tuple:
    """A background's equipment ("Holy symbol, 5 sticks incense, vestments,
    15 gp") -> ([(item, how many)], {"GP": 15}). A pack written with its
    contents ("Monster hunter's pack (chest, crowbar, ...)") is its contents."""
    items, coins = [], {}
    for part in _split_top(text or ""):
        part = re.sub(r"^(and|plus)\s+", "", part.strip(), flags=re.I)
        coin = re.match(r"^(\d+)\s*(gp|sp|cp|ep|pp)\b", part, re.I)
        if coin:
            coins[coin.group(2).upper()] = coins.get(coin.group(2).upper(), 0) + int(coin.group(1))
            continue
        if not part:
            continue
        pack = re.match(r"^.*\bpack\s*\((.+,.+)\)$", part, re.I)
        if pack:
            inner, inner_coins = gear_from_text(pack.group(1))
            items += inner
            for denom, n in inner_coins.items():
                coins[denom] = coins.get(denom, 0) + n
            continue
        qty = 1
        count = re.match(r"^(\d+|[a-z]+)\s+(.+)$", part, re.I)
        if count and not _table_name(part):
            word, rest = count.group(1).lower(), count.group(2)
            n = int(word) if word.isdigit() else _COUNT_WORDS.get(word)
            if n and not rest.lower().startswith(("ft ", "feet ")):
                qty, part = n, rest
        part = _ONE_OF.get(part.lower(), part)
        items.append((part[:1].upper() + part[1:], qty))
    return items, coins


def _light(name: str) -> bool:
    return "Light" in (WEAPON_DICT.get(name) or {}).get("properties", [])


def set_starting_inventory(char: dict, chosen: list, background_text: str = "") -> None:
    """The last wizard step, the same on both apps: the class's starting
    equipment as chosen (a pack is its contents) and the background's,
    into the inventory -- one row per item, counted, with the rules'
    weights and costs. Armor is worn, a shield carried, and each weapon in
    hand once (a light one twice, for fighting with two); coins go to the
    purse."""
    from dnd_app.data.items import EQUIPMENT_PACKS
    char["armor_worn"] = "No Armor"
    char["shield"] = False
    char["equipped_weapons"] = []
    char["equipment"] = []
    held = char["equipped_weapons"]
    for item in chosen:
        if not item:
            continue
        base = item.split(" (")[0].strip()
        if base in ("Shield", "Wooden Shield"):            # a druid's is a shield like any other
            char["shield"] = True
            add_item(char, "Shield")
        elif base in ARMOR_DICT and ARMOR_DICT[base].get("type") not in ("none", "shield"):
            char["armor_worn"] = base
            add_item(char, base)
        elif base in WEAPON_DICT:
            add_item(char, base)
            if held.count(base) == 0 or (held.count(base) == 1 and _light(base)):
                held.append(base)
        elif base in EQUIPMENT_PACKS:
            for pack_item, qty in EQUIPMENT_PACKS[base]:
                add_item(char, pack_item, qty)
        else:
            add_item(char, item)
    items, coins = gear_from_text(background_text)
    for name, qty in items:
        add_item(char, name, qty)
    name_tool_kinds(char)
    merge_stacks(char)
    purse = char.setdefault("currency", {})
    for denom, n in coins.items():
        purse[denom] = purse.get(denom, 0) + n
