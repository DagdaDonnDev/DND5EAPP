"""Spellcasting rules both apps share, one section each:
  * Component restrictions (optional rule) -- what stops a spell being cast
  * Free casts -- racial and feat spells cast without a slot, once per rest
  * Spell scrolls -- reading one, and binding a spell to a blank scroll
  * Immersive Spells (optional rule) -- flavour titles for the spell list
  * Spell limits -- how many spells each class knows or prepares, per class
"""
from __future__ import annotations

import re
import random


# ═══════════════════════════════════════════════════════════════════════════
# Component restrictions (optional rule)
# ═══════════════════════════════════════════════════════════════════════════
# Component Restrictions (optional rule, default off): a caster who is
# Blinded, Gagged, or Restrained can be mechanically unable to cast a
# given spell, depending on what that specific spell actually needs --
# not a blanket "no spells while condition X" rule, since e.g. a
# Blinded caster can still cast a self-only spell with no verbal
# component just fine.
#
# This module is the single source of truth for "is THIS spell blocked
# by THIS character's current conditions right now" -- shared by the
# real cast gate (sheet.py's _cast_spell()/_cast_spell_as_ritual()) and
# Immersive Spells' title redaction (core/spellcasting.py), so the two
# can never drift out of sync (a spell showing "blocked" but still
# castable, or vice versa).
#
# Author: Ethan O'Brien
# Date: 2026-08-20

def _component_letters(spell: dict) -> set:
    """{'v','s','m'} etc. parsed from a spell's "components" field
    (e.g. "V, S, M (a pinch of salt)")."""
    comps = spell.get("components", "") or ""
    return {part.strip()[:1].lower() for part in comps.split(",") if part.strip()}


def requires_verbal(spell: dict) -> bool:
    return "v" in _component_letters(spell)


def requires_somatic(spell: dict) -> bool:
    return "s" in _component_letters(spell)


def requires_sight(spell: dict) -> bool:
    """No explicit field for this in the spell data -- approximated
    from range: a self-only spell (range "Self", or a "Self (X-foot
    radius)" AOE centered on the caster) doesn't require seeing
    anything, while any other range implies targeting or centering the
    effect on something you must be able to perceive, which for a
    Blinded caster specifically means sight."""
    rng = (spell.get("range") or "").strip().lower()
    return not rng.startswith("self")


# (condition name, requirement-check, short reason) -- checked in this
# order; a spell needing multiple blocked components while multiple
# conditions are active still only needs the first matching reason.
_BLOCK_RULES = (
    ("Blinded",    requires_sight,   "Blinded — can't see a target for this spell"),
    ("Gagged",     requires_verbal,  "Gagged — can't speak this spell's verbal component"),
    ("Restrained", requires_somatic, "Restrained — can't perform this spell's somatic component"),
)


def spell_component_block_reason(char: dict, spell: dict):
    """Returns a short reason string if the "Component Restrictions"
    optional rule is on and an active condition blocks something this
    spell needs, else None."""
    if not char.get("optional_rules", {}).get("component_restrictions", False):
        return None
    conditions = set(char.get("conditions", []))
    for cond_name, check, reason in _BLOCK_RULES:
        if cond_name in conditions and check(spell):
            return reason
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Free casts: racial and feat spells
# ═══════════════════════════════════════════════════════════════════════════
# Free daily casts -- spells a race, feat or feature lets you cast without a
# spell slot, a set number of times between rests (a Tiefling's Hellish
# Rebuke once per long rest, Fey Touched's Misty Step, Firbolg Magic...).
#
# Each source is a tracked resource in char["resources"] (shown with the
# other limited-use features, reset by the matching rest). This module
# answers two questions for the Cast button on both apps:
#   1. Which spells can this resource cast?  free_spells_of()
#   2. Is there a free use of this spell left, and spend it.  spend_free_cast()
#
# How a resource names its spells:
#   - an explicit "free_spells" list (the resources built here), or
#   - for older resources, the spell names in its note after "Cast ..."
#     ("Cast misty step and tongues, each once, without a spell slot."), or
#   - a feat whose spell is the player's pick (Magic Initiate) reads it
#     back from _choices.

# Racial spells that are NOT a limited free cast (at will, or only in a
# narrow case), so they get no counter: {(race prefix, spell)}
_NOT_DAILY = {
    ("Yuan-ti", "Animal Friendship"),   # at will, on snakes only
}

# Extra wording for a free cast that isn't quite the plain spell.
_CAST_NOTES = {
    ("Tiefling", "Hellish Rebuke"): "cast as a 2nd-level spell",
    # dragonmarks (only that mark's race gets each of these spells)
    ("Dwarf", "Alarm"): "no material components",
    ("Dwarf", "Mage Armor"): "no material components",
    ("Dwarf", "Arcane Lock"): "no material components",
    ("Half-Elf", "Detect Magic"): "no material components",
    ("Half-Elf", "Detect Poison and Disease"): "no material components",
    ("Half-Elf", "See Invisibility"): "no material components",
    ("Human", "Animal Friendship"): "no material components",
    ("Human", "Speak with Animals"): "no material components",
    ("Human", "Magic Weapon"): "it lasts 1 hour and doesn't need concentration",
}

# Free racial casts that come back on a short rest too (the rest are once
# per long rest): Mark of Scribing's Comprehend Languages, Mark of
# Handling's two spells
_SHORT_REST_CASTS = {
    ("Gnome", "Comprehend Languages"),
    ("Human", "Animal Friendship"), ("Human", "Speak with Animals"),
}

# Resources whose spell is the player's pick: {resource key: _choices key}
_CHOSEN_SPELL_RESOURCES = {
    "magic_initiate": "feat_magic_initiate_spell",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def free_spells_of(char: dict, resource: dict) -> list[str]:
    """The spells `resource` lets the character cast for free."""
    if resource.get("free_spells"):
        return list(resource["free_spells"])
    choice_key = _CHOSEN_SPELL_RESOURCES.get(resource.get("key", ""))
    if choice_key:
        return list(char.get("_choices", {}).get(choice_key, []))
    note = resource.get("note", "")
    m = re.search(r"\bcast\s+(.*?)(?:\swithout\b|\susing\b|\(|\.\s|$)", note, re.IGNORECASE)
    if not m:
        return []
    found = _spells_named(m.group(1))
    if not found:
        # a spell with "without" in its name ("Cast pass without trace without
        # a spell slot"): the rest of the sentence
        whole = re.search(r"\bcast\s+([^.(]*)", note, re.IGNORECASE)
        found = _spells_named(whole.group(1)) if whole else []
    return found


def _spells_named(text: str) -> list[str]:
    """The spells named in `text`, longest names first, so "Greater
    Invisibility" isn't also read as "Invisibility"."""
    from dnd_app.data.spells import SPELL_NAMES
    named = text.lower()
    found = []
    for name in sorted(SPELL_NAMES, key=len, reverse=True):
        pat = r"(?<![a-z])" + re.escape(name.lower()) + r"(?![a-z])"
        if re.search(pat, named):
            found.append(name)
            named = re.sub(pat, " ", named)
    return found


def free_cast_resources(char: dict, spell_name: str) -> list[dict]:
    """Resources with a use left that can cast `spell_name` for free."""
    return [r for r in char.get("resources", [])
            if r.get("current", 0) > 0 and spell_name in free_spells_of(char, r)]


def spend_free_cast(char: dict, spell_name: str):
    """Use one free cast of `spell_name` if there is one; returns the
    resource it came from (or None, and nothing changes)."""
    options = free_cast_resources(char, spell_name)
    if not options:
        return None
    res = options[0]
    res["current"] = res.get("current", 0) - 1
    return res


def reset_phrase(resource: dict) -> str:
    """'long rest' / 'short or long rest', for messages."""
    return "short or long rest" if "SR" in resource.get("reset", "LR") else "long rest"


def free_cast_message(spell_name: str, resource: dict) -> str:
    """The toast after a free cast, e.g. "Cast Darkness for free (Tiefling)
    -- no free casts left until a long rest"."""
    source = resource.get("name", "")
    if "(" in source and source.endswith(")"):
        source = source[source.rfind("(") + 1:-1]      # "Darkness (Tiefling)" -> "Tiefling"
    left = resource.get("current", 0)
    tail = (f"{left} free cast{'s' if left != 1 else ''} left" if left
            else f"no free casts left until a {reset_phrase(resource)}")
    return f"Cast {spell_name} for free ({source}) -- {tail}"


def innate_free_cast_resources(char: dict, existing: list) -> list[dict]:
    """New counters for free casts nothing else tracks yet: each leveled
    racial spell (once per long rest), and Fey Touched / Shadow Touched's
    two spells (each once per long rest). A spell already covered by an
    existing resource (Firbolg Magic, Yuan-ti Suggestion...) is skipped,
    so no spell gets two counters."""
    from dnd_app.data.spells import (get_spell, racial_innate_spells,
                                               FEAT_FIXED_SPELLS, FEAT_CHOSEN_SPELL_KEYS)
    covered = {sp for r in existing for sp in free_spells_of(char, r)}
    species = char.get("species") or char.get("race", "")
    out = []

    def _add(spell, source, key_prefix, note_extra="", reset="LR"):
        sp = get_spell(spell)
        if not sp or sp.get("level", 0) == 0 or spell in covered:
            return   # cantrips are at will; one counter per spell
        covered.add(spell)
        note = f"Cast {spell} once without a spell slot ({source})"
        note += f", {note_extra}." if note_extra else "."
        out.append({
            "name": f"{spell} ({source})", "key": f"{key_prefix}_{_slug(spell)}",
            "reset": reset, "current_max": 1, "track": "uses",
            "note": note, "free_spells": [spell],
            "source_class": "", "subclass": "",
        })

    # a dragonmark's spells are named for the mark ("Shield (Mark of Sentinel)")
    subrace = char.get("subrace") or ""
    source = subrace if subrace.startswith("Mark of") else (species or "racial")
    for spell in racial_innate_spells(char):
        race_prefix = next((r for (r, s) in _NOT_DAILY if species.startswith(r) and s == spell), None)
        if race_prefix:
            continue
        extra = next((n for (r, s), n in _CAST_NOTES.items() if species.startswith(r) and s == spell), "")
        short = any(species.startswith(r) and s == spell for (r, s) in _SHORT_REST_CASTS)
        _add(spell, source, "free_racial", extra, "SR/LR" if short else "LR")

    choices = char.get("_choices", {})
    for feat in ("Fey Touched", "Shadow Touched"):
        if feat not in char.get("feats", []):
            continue
        spells = list(FEAT_FIXED_SPELLS.get(feat, []))
        for key in FEAT_CHOSEN_SPELL_KEYS.get(feat, []):
            spells.extend(choices.get(key, []))
        for spell in spells:
            _add(spell, feat, f"free_{_slug(feat)}")
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Spell scrolls
# ═══════════════════════════════════════════════════════════════════════════
# Spell scrolls (DMG p.200): every scroll carries one specific spell.
#
# Owned scrolls are equipment entries named "Spell Scroll (3rd level) — Fireball".
# A bare "Spell Scroll (3rd level)" (an older save, a PDF import) has no spell
# yet -- the UIs ask for one before it can be used, and bind_spell_scroll()
# gives that one copy its spell.
#
# Using a scroll casts its spell: no slot and no material components, and it
# uses the scroll's own save DC / attack bonus (the table below), not yours.
#   * The spell must be on one of your classes' spell lists (or one you know /
#     have prepared, which covers domain and other expanded lists) -- otherwise
#     the scroll is unintelligible, and it isn't used up.
#   * If the spell is of a higher level than you can normally cast, you make an
#     ability check with your spellcasting ability, DC 10 + the spell's level;
#     on a failure the spell vanishes from the scroll with no other effect.
#   * A Thief rogue's Use Magic Device (13th level) ignores the class-list
#     requirement, checking with Intelligence.

_SCROLL_RE = re.compile(r"^Spell Scroll \((Cantrip|(\d)(?:st|nd|rd|th) level)\)(?:\s*[—–-]\s*(.+))?$")

# DMG Spell Scroll table: spell level -> (save DC, attack bonus)
SCROLL_STATS = {0: (13, 5), 1: (13, 5), 2: (13, 5), 3: (15, 7), 4: (15, 7),
                5: (17, 9), 6: (17, 9), 7: (18, 10), 8: (18, 10), 9: (19, 11)}

# third casters read from the wizard's list
_LIST_FOR = {"Fighter": "Wizard", "Rogue": "Wizard"}
_THIRD_CASTER_SUBCLASS = {"Fighter": "eldritch knight", "Rogue": "arcane trickster"}


def parse_spell_scroll(name: str):
    """(spell level, spell name or None) for a spell scroll, else None."""
    m = _SCROLL_RE.match((name or "").strip())
    if not m:
        return None
    level = 0 if m.group(1) == "Cantrip" else int(m.group(2))
    return level, (m.group(3) or "").strip() or None


def scroll_base_name(level: int) -> str:
    if level == 0:
        return "Spell Scroll (Cantrip)"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(level, "th")
    return f"Spell Scroll ({level}{suffix} level)"


def bound_scroll_name(level: int, spell: str) -> str:
    return f"{scroll_base_name(level)} — {spell}"


def spell_for_scroll_level(level: int) -> list[str]:
    from dnd_app.data.spells import SPELLS_BY_LEVEL
    return sorted(s["name"] for s in SPELLS_BY_LEVEL.get(level, []))


def bind_spell_scroll(char: dict, eq_name: str, spell: str) -> str | None:
    """Give one blank scroll from the stack `eq_name` its spell. Returns the
    bound scroll's equipment name (None if it couldn't)."""
    parsed = parse_spell_scroll(eq_name)
    from dnd_app.data.spells import get_spell
    data = get_spell(spell)
    if not parsed or parsed[1] or not data or data.get("level") != parsed[0]:
        return None
    eq = char.setdefault("equipment", [])
    entry = next((e for e in eq if isinstance(e, dict) and e.get("name") == eq_name), None)
    if not entry:
        return None
    new_name = bound_scroll_name(parsed[0], spell)
    if entry.get("qty", 1) > 1:
        entry["qty"] -= 1
        same = next((e for e in eq if isinstance(e, dict) and e.get("name") == new_name), None)
        if same:
            same["qty"] = same.get("qty", 1) + 1
        else:
            copy = {k: v for k, v in entry.items() if k != "qty"}
            copy.update({"name": new_name, "qty": 1})
            eq.append(copy)
    else:
        same = next((e for e in eq if isinstance(e, dict) and e.get("name") == new_name), None)
        if same:
            same["qty"] = same.get("qty", 1) + 1
            eq.remove(entry)
        else:
            entry["name"] = new_name
    return new_name


def _highest_castable_level(char: dict) -> int:
    slots = char.get("spell_slots_max", []) or []
    best = max((i + 1 for i, n in enumerate(slots) if n), default=0)
    if char.get("pact_slots_max"):
        best = max(best, char.get("pact_slot_level", 0) or 0)
    return best


def scroll_reading(char: dict, spell_name: str) -> dict:
    """Whether this character can use a scroll of `spell_name`, and how:
    {"readable", "reason", "check": None or {"ability", "mod", "dc"},
     "save_dc", "attack", "level"}.

      save DC / attack come from the scroll's level (SCROLL_STATS)
      find a class whose spell list has it (Eldritch Knight / Arcane
        Trickster use the wizard's list) -> that class's casting ability
      else a spell you already know or have prepared (domain and other
        expanded lists) -> your usual casting ability
      else a 13th-level Thief (Use Magic Device) -> Intelligence
      else -> not readable
      readable, but above the highest slot level you have -> an ability
        check is needed, DC 10 + spell level"""
    from dnd_app.data.spells import get_spell, CLASS_SPELLS
    from dnd_app.data.classes import CLASS_DICT
    from .character import ability_mod
    spell = get_spell(spell_name) or {}
    level = spell.get("level", 0)
    save_dc, attack = SCROLL_STATS.get(level, (13, 5))
    out = {"readable": False, "reason": "", "check": None, "save_dc": save_dc,
           "attack": attack, "level": level}
    if not spell:
        out["reason"] = f"{spell_name} isn't a spell this app knows."
        return out

    ability = None
    for c in char.get("classes", []):
        cname = c.get("class", "")
        list_name = cname
        if cname in _LIST_FOR:
            if _THIRD_CASTER_SUBCLASS[cname] not in (c.get("subclass") or "").lower():
                continue
            list_name = _LIST_FOR[cname]
        names = {s["name"] for s in CLASS_SPELLS.get(list_name, [])}
        if spell_name in names:
            ability = CLASS_DICT.get(cname, {}).get("spell_ability") or "INT"
            break
    if ability is None and spell_name in (set(char.get("spells_known", [])) | set(char.get("cantrips", []))
                                          | set(char.get("spells_prepared", []))):
        from .calculator import _detect_spell_ability
        ability = _detect_spell_ability(char) or "INT"
    thief = any(c.get("class") == "Rogue" and c.get("level", 0) >= 13
                and "thief" in (c.get("subclass") or "").lower() for c in char.get("classes", []))
    if ability is None and thief:
        ability = "INT"
    if ability is None:
        out["reason"] = (f"{spell_name} isn't on your class's spell list -- the scroll is "
                         "unintelligible to you.")
        return out

    out["readable"] = True
    if level > _highest_castable_level(char) and level > 0:
        out["check"] = {"ability": ability, "mod": ability_mod(char, ability), "dc": 10 + level}
    return out


def use_spell_scroll(char: dict, eq_name: str, rng=random) -> dict:
    """Read one scroll from the stack `eq_name`. Returns
    {"status": "cast" | "failed" | "unreadable" | "unbound" | "missing",
     "spell", "message", "save_dc", "attack", "roll"}. The scroll is used up
    on "cast" and "failed"; the caller applies the cast itself (concentration,
    effects, the turn tracker) on "cast".

      not a spell scroll, or not owned          -> "missing"
      no spell written on it yet               -> "unbound" (the UI asks
                                                   which spell, binds, retries)
      spell not on any of your lists           -> "unreadable", scroll kept
      spell above the level you can cast:
        roll d20 + spellcasting mod vs 10 + spell level
          below -> "failed", scroll used up, no effect
          else  -> "cast", scroll used up
      otherwise                                -> "cast", scroll used up"""
    parsed = parse_spell_scroll(eq_name)
    eq = char.get("equipment", [])
    entry = next((e for e in eq if isinstance(e, dict) and e.get("name") == eq_name), None)
    if not parsed or not entry:
        return {"status": "missing", "message": f"{eq_name} isn't in your inventory."}
    level, spell = parsed
    if not spell:
        return {"status": "unbound", "level": level,
                "message": "This scroll has no spell written on it yet -- choose one first."}
    info = scroll_reading(char, spell)
    res = {"spell": spell, "save_dc": info["save_dc"], "attack": info["attack"], "roll": None}
    if not info["readable"]:
        return {**res, "status": "unreadable", "message": info["reason"]}

    def consume():
        entry["qty"] = entry.get("qty", 1) - 1
        if entry["qty"] <= 0:
            char["equipment"] = [e for e in eq if e is not entry]

    stats = f"save DC {info['save_dc']}, +{info['attack']} to hit"
    if info["check"]:
        chk = info["check"]
        d20 = rng.randint(1, 20)
        total = d20 + chk["mod"]
        res["roll"] = {"d20": d20, "total": total, "dc": chk["dc"], "ability": chk["ability"]}
        roll_txt = f"{chk['ability']} check {d20}{chk['mod']:+d} = {total} vs DC {chk['dc']}"
        if total < chk["dc"]:
            consume()
            return {**res, "status": "failed",
                    "message": f"{roll_txt} -- failed. The spell fades from the scroll with no effect."}
        consume()
        return {**res, "status": "cast",
                "message": f"{roll_txt} -- success! Cast {spell} from the scroll ({stats})."}
    consume()
    return {**res, "status": "cast", "message": f"Cast {spell} from the scroll ({stats})."}


# ═══════════════════════════════════════════════════════════════════════════
# Immersive Spells (optional rule)
# ═══════════════════════════════════════════════════════════════════════════
# Immersive Spells (optional rule, default OFF): purely cosmetic, purely
# title-only flavor text for the spell list -- never touches the spell's
# real name, description, tooltip, or any casting mechanics, only what's
# shown on a SpellRow's title label. Checked in order (first match wins)
# since a character is realistically only ever in one of these at a time:
#
# 1. Wild Shaped, and not yet able to actually cast in beast form (no
#    Beast Spells -- Circle of the Moon Druid, 18th level): a beast
#    can't speak a human language, so every spell title comes out as
#    the current beast's noise, stretched to roughly the original
#    word's length. "Absorb Elements" as a Brown Bear reads something
#    like "Raaaawr Raaaaaawr"; as a Cat, "Meeow Meeeeow".
#
# 2. Rage active (Barbarian): a raging mind doesn't have room for
#    incantations -- a few iconic spells get a specific exclaimed
#    shorthand, single-word spells just get shouted, and anything else
#    multi-word collapses to "SMASH!".
#
# 3. Component Restrictions (a separate optional rule -- see
#    core/spellcasting.py) actually blocking THIS specific spell
#    right now: Blinded blacks the title out (can't read what you can't
#    see), Gagged muffles it to a word-length-matched "mmmhmmhf", and
#    Restrained turns it into a straining "nngh" -- unlike situations 1
#    and 2 above, this only affects spells that individually need the
#    blocked sense/component, so it's checked per spell rather than as a
#    blanket override, and only when that same optional rule is also on
#    (the visual only ever shows for a spell that's genuinely, mechanically
#    blocked right now -- see spell_component_block_reason()).
#
# 4. Warlock/Sorcerer/Cleric/Paladin: every spell title is prefixed with
#    a short phrase themed to that patron/origin/domain/Oath.

# ── 1. Wild Shape beast noise ────────────────────────────────────────────────

# Each entry: (keywords to substring-match against the beast name,
# lowercased; base sound; index of the character within that base
# sound to repeat when stretching to a longer word). Checked in order,
# first match wins -- more specific keywords (e.g. "sea horse", which
# would otherwise collide with the "horse" family) are listed earlier.
_BEAST_SOUND_FAMILIES = [
    (("sea horse", "seahorse"),                                   "blub",    2),
    (("octopus", "squid", "rocktopus"),                           "squelch", 3),
    (("dolphin", "killer whale", "whale"),                        "eee",     1),
    (("fish", "eel", "shark", "guppy", "quipper", "trout",
      "prawn", "koi"),                                            "blub",    2),
    (("bear",),                                                   "rawr",    1),
    (("cat", "tiger", "panther", "leopard", "lion"),               "meow",    1),
    (("hyena",),                                                  "haha",    3),
    (("fox",),                                                    "ring",    1),
    (("wolf", "dog", "jackal", "mastiff"),                        "ruff",    1),
    (("owl",),                                                    "hoot",    2),
    (("eagle", "hawk", "falcon", "vulture", "raven", "crow",
      "peacock", "rooster", "swan", "canary", "diatryma"),        "caw",     1),
    (("saurus", "raptor", "lizard", "crocodile", "plesiosaur",
      "dimetrodon", "pteranodon", "quetzalcoatlus", "triceratops",
      "deinonychus"),                                             "RAAAWR",  2),
    (("elephant", "mammoth", "rhinoceros", "titanothere"),        "toot",    1),
    (("spider", "scorpion", "steeder"),                           "tsss",    1),
    (("rat", "hamster", "weasel", "hare", "mouse"),                "squeak",  4),
    (("bat",),                                                    "eek",     1),
    (("frog", "toad"),                                            "ribbit",  2),
    (("snake", "amphisbaena", "jaculi"),                          "hiss",    2),
    (("cow", "ox", "aurochs", "yak", "rothe", "rothé", "kow"),     "moo",     1),
    (("sheep", "goat"),                                           "baa",     1),
    (("pig", "boar", "swine"),                                    "oink",    1),
    (("horse", "pony", "mule", "camel", "zebra", "steed"),        "neigh",   1),
    (("crab", "snail", "crayfish"),                               "click",   2),
    (("wasp", "beetle", "dragonfly", "centipede", "stirge"),      "bzzt",    1),
    (("baboon", "ape", "monkey"),                                 "ook",     1),
    (("turtle", "tortoise"),                                      "blip",    2),
    (("deer", "elk", "stag", "reindeer"),                         "gronk",   2),
    (("air elemental",),                                          "whoosh",  2),
    (("water elemental",),                                        "splash",  3),
    (("earth elemental",),                                        "rumble",  1),
    (("fire elemental",),                                         "crackle", 2),
]

# Fallback for anything not covered above (fantastical creatures like
# Almiraj, Clawfoot, Moorbounder, Whirlwyrm, etc. don't have a
# real-world sound to draw on) -- a generic beast noise.
_DEFAULT_SOUND = ("grrr", 2)


def _get_beast_sound_profile(beast_name: str) -> tuple[str, int]:
    name = (beast_name or "").lower()
    for keywords, sound, idx in _BEAST_SOUND_FAMILIES:
        if any(kw in name for kw in keywords):
            return sound, idx
    return _DEFAULT_SOUND


def _stretch_word(word: str, base_sound: str, stretch_idx: int) -> str:
    """Pad base_sound out to (approximately) word's length by repeating
    the character at stretch_idx, capitalized to read as a title. Never
    shrinks the base sound below its own natural length."""
    target_len = len(word)
    if target_len <= len(base_sound):
        result = base_sound
    else:
        extra = target_len - len(base_sound)
        result = (base_sound[:stretch_idx]
                  + base_sound[stretch_idx] * (1 + extra)
                  + base_sound[stretch_idx + 1:])
    return result[:1].upper() + result[1:]


def _stretch_all_words(spell_name: str, base_sound: str, stretch_idx: int) -> str:
    words = spell_name.split()
    if not words:
        return spell_name
    return " ".join(_stretch_word(w, base_sound, stretch_idx) for w in words)


def _wildshape_spell_title(spell_name: str, beast_name: str) -> str:
    base_sound, stretch_idx = _get_beast_sound_profile(beast_name)
    return _stretch_all_words(spell_name, base_sound, stretch_idx)


# ── 2. Barbarian Rage ────────────────────────────────────────────────────────

# A few iconic spells get their own shorthand rather than falling to
# the generic multi-word "SMASH!" rule below.
_RAGE_EXCEPTIONS = {
    "Fireball": "FIRE!",
    "Magic Missile": "MAGIC MISSILE!",
}


def _rage_spell_title(char: dict, spell_name: str) -> str:
    # Path of the Totem Warrior: raging with a Bear/Eagle/Wolf totem
    # spirit chosen (3rd level) reuses the Wild Shape beast-noise
    # mechanic above for that totem animal instead of the flat
    # exclamation table below -- a raging Bear Totem barbarian and a
    # Wild Shaped bear-form Druid are making the same kind of noise.
    from dnd_app.core.character import subclasses
    barb_sub = subclasses(char).get("Barbarian", "").lower()
    if "totem" in barb_sub:
        picks = char.get("_choices", {}).get("totem_spirit_3", [])
        pick_text = " ".join(picks).lower()
        for totem in ("bear", "eagle", "wolf"):
            if totem in pick_text:
                return _wildshape_spell_title(spell_name, totem)
    if spell_name in _RAGE_EXCEPTIONS:
        return _RAGE_EXCEPTIONS[spell_name]
    words = spell_name.split()
    if len(words) <= 1:
        return spell_name.upper() + "!"
    return "SMASH!"


# ── 3. Component Restrictions: Blinded/Gagged/Restrained ────────────────────

def _redact_spell_title(spell_name: str) -> str:
    """Blinded, a sight-required spell, blocked right now: the title is
    blacked out -- can't read what you can't see."""
    return " ".join("█" * len(w) for w in spell_name.split())


def _gagged_spell_title(spell_name: str) -> str:
    """Gagged, a verbal-component spell, blocked right now: muffled to
    a word-length-matched mumble, same mechanic as the Wild Shape beast
    noise above."""
    return _stretch_all_words(spell_name, "mmmhmmhf", 0)


def _restrained_spell_title(spell_name: str) -> str:
    """Restrained, a somatic-component spell, blocked right now: the
    gesture doesn't complete -- a word-length-matched straining grunt,
    same mechanic as the Wild Shape beast noise above."""
    return _stretch_all_words(spell_name, "nngh", 0)


# ── 4. Thematic prefixes: Warlock patron, Sorcerer origin, Cleric domain,
#      Paladin Oath ─────────────────────────────────────────────────────────

_WARLOCK_PATRON_PREFIXES = {
    "archfey":       "By Fey Bargain ",
    "celestial":     "By Radiant Pact ",
    "fathomless":    "By the Deep Pact ",
    "fiend":         "By Infernal Pact ",
    "genie":         "By the Genie's Wish ",
    "great old one": "By the Old One ",
    "hexblade":      "By the Blade Pact ",
    "undead":        "By the Undead King ",
    "undying":       "By Undying Pact ",
}

_SORCERER_ORIGIN_PREFIXES = {
    "aberrant":    "By the Unknowable ",
    "clockwork":   "By the Mechanism ",
    "divine soul": "By Divine Blood ",
    "draconic":    "By Dragon's Blood ",
    "lunar":       "By Moonlight ",
    "shadow":      "By the Shadowfell ",
    "storm":       "By the Storm ",
    "wild magic":  "By Wild Magic ",
}

_CLERIC_DOMAIN_PREFIXES = {
    "arcana":    "By Arcane Lore ",
    "death":     "By Death ",
    "forge":     "By the Forge ",
    "grave":     "By the Grave ",
    "knowledge": "By Wisdom ",
    "life":      "By Life ",
    "light":     "By Radiance ",
    "nature":    "By the Wild ",
    "order":     "By Order ",
    "peace":     "By Peace ",
    "tempest":   "By Storm ",
    "trickery":  "By Deception ",
    "twilight":  "By Twilight ",
    "war":       "By Battle ",
}

_OATH_PREFIXES = {
    "devotion":    "By Honor ",
    "ancients":    "By the Light ",
    "vengeance":   "By the Fallen ",
    "conquest":    "By the Iron ",
    "glory":       "By Glory ",
    "crown":       "By the Crown ",
    "redemption":  "By Mercy ",
    "watchers":    "By the Vigil ",
    "open sea":    "By the Tide ",
    "oathbreaker": "By the Broken ",
}


def _match_prefix(subclass_name: str, prefix_map: dict) -> str | None:
    """Substring-match subclass_name against prefix_map's keys, longest
    keyword first -- e.g. Cleric's "Twilight Domain" must match "twilight"
    before the shorter "light" (Light Domain) gets a chance to, since
    "light" is itself a substring of "twilight"."""
    sub = (subclass_name or "").lower()
    for key in sorted(prefix_map, key=len, reverse=True):
        if key in sub:
            return prefix_map[key]
    return None


# ── Orchestrator ─────────────────────────────────────────────────────────────

def compute_display_spell_title(char: dict, spell: dict) -> str:
    """The text a SpellRow's title label should show for this spell,
    given the character's current state. Returns the real name
    unchanged unless the "Immersive Spells" optional rule is on and one
    of the situations above applies. Checked in order -- a full
    override (can't physically speak, or too enraged to do more than
    shout) outranks a per-spell block, which outranks a merely thematic
    prefix; a character realistically only matches one of these at a
    time, and the per-spell block only ever applies to spells that
    individually need whatever's blocked."""
    spell_name = spell["name"]
    if not char.get("optional_rules", {}).get("immersive_spells", False):
        return spell_name

    beast = char.get("_wildshape_active")
    if beast:
        has_beast_spells = any(
            c.get("class") == "Druid" and c.get("level", 0) >= 18
            for c in char.get("classes", []))
        if not has_beast_spells:
            return _wildshape_spell_title(spell_name, beast)

    if "Rage" in char.get("active_effects", []):
        return _rage_spell_title(char, spell_name)

    block_reason = spell_component_block_reason(char, spell)
    if block_reason:
        if block_reason.startswith("Blinded"):
            return _redact_spell_title(spell_name)
        if block_reason.startswith("Gagged"):
            return _gagged_spell_title(spell_name)
        if block_reason.startswith("Restrained"):
            return _restrained_spell_title(spell_name)

    from dnd_app.core.character import subclasses
    subs = subclasses(char)

    # A multiclass character (e.g. Paladin/Wizard) should only get the
    # Oath prefix on their actual Paladin spells, not their Wizard
    # ones too -- checked against the spell's own "classes" list (which
    # classes can learn it at all), not just "does the character have
    # any levels in this class." A non-Paladin who knows a Paladin
    # spell only through some other source (a feat, a racial grant)
    # correctly never reaches this at all, since subs.get(class_name)
    # is only non-empty for classes the character actually has levels in.
    spell_classes = spell.get("classes", [])
    for class_name, prefix_map in (
        ("Warlock", _WARLOCK_PATRON_PREFIXES),
        ("Sorcerer", _SORCERER_ORIGIN_PREFIXES),
        ("Cleric", _CLERIC_DOMAIN_PREFIXES),
        ("Paladin", _OATH_PREFIXES),
    ):
        sub = subs.get(class_name, "")
        if sub and class_name in spell_classes:
            prefix = _match_prefix(sub, prefix_map)
            if prefix:
                return prefix + spell_name

    return spell_name

# ═══════════════════════════════════════════════════════════════════════════
# Spell limits: how many spells each class knows or prepares
# ═══════════════════════════════════════════════════════════════════════════
# Per class, never pooled (PHB p.164): a Sorcerer/Warlock's two spells-known
# pools are separate, and so are a Cleric/Druid's two prepared allotments.


def spell_progression_tables():
    """Single source of truth for spells-known / cantrips-known
    progression tables, shared by the summary display, the learn-gate,
    and the multiclass attribution logic below — kept as one copy so
    the three call sites can never drift out of sync with each
    other."""
    SPELLS_KNOWN = {
        "Bard":     {1:4,2:5,3:6,4:7,5:8,6:9,7:10,8:11,9:12,10:14,11:15,12:15,
                     13:16,14:18,15:19,16:19,17:20,18:22,19:22,20:22},
        "Sorcerer": {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,12:12,
                     13:13,14:13,15:14,16:14,17:15,18:15,19:15,20:15},
        "Warlock":  {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:10,11:11,12:11,
                     13:12,14:12,15:13,16:13,17:14,18:14,19:15,20:15},
        "Ranger":   {1:0,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6,10:6,11:7,12:7,
                     13:8,14:8,15:9,16:9,17:10,18:10,19:11,20:11},
    }
    CANTRIPS = {
        "Wizard":   {1:3,4:4,10:5},
        "Cleric":   {1:3},
        "Druid":    {1:2,6:3,11:4},
        "Bard":     {1:2,4:3,10:4},
        "Sorcerer": {1:4,4:5,10:6},
        "Warlock":  {1:2,4:3,10:4},
        "Artificer":{1:2},
    }
    EK_AT = {3:3,4:4,7:5,8:6,10:7,11:8,13:9,14:10,16:11,19:12,20:13}
    PREPARE_AB = {"Wizard":"INT","Cleric":"WIS","Druid":"WIS","Paladin":"CHA","Artificer":"INT"}
    return SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB


def char_spell_classes(char: dict) -> set:
    """Class spell-lists this character can learn from (EK/AT → Wizard)."""
    out = set()
    for c in char.get("classes", []):
        cn = c.get("class",""); sub = c.get("subclass","").lower()
        if cn in ("Wizard","Cleric","Druid","Bard","Sorcerer","Warlock",
                  "Paladin","Ranger","Artificer"):
            out.add(cn)
        if cn == "Fighter" and "eldritch knight" in sub: out.add("Wizard")
        if cn == "Rogue"   and "arcane trickster" in sub: out.add("Wizard")
    return out


def max_castable_spell_level(char: dict) -> int:
    """Highest spell level the character can currently cast, combining
    ordinary spell slots and Warlock Pact Magic — the two are tracked
    completely separately in the character data, so checking only one
    would wrongly block (or wrongly allow) a pure-Warlock or
    multiclass Warlock character."""
    max_lvl = 0
    for i, count in enumerate(char.get("spell_slots_max", [])):
        if count > 0:
            max_lvl = i + 1
    if char.get("pact_slots_max", 0) > 0:
        max_lvl = max(max_lvl, char.get("pact_slot_level", 0))
    return max_lvl


def all_caster_classes(char: dict):
    """{class_name: (cantrip_max, leveled_max_or_None)} for EVERY class
    that grants cantrips and/or known spells. leveled_max is None for
    prepared casters (Wizard/Cleric/Druid/Paladin/Artificer) — they
    don't have a 'known' leveled-spell cap, they prepare a subset of
    their full list daily (tracked separately via spells_prepared).
    Cantrips work the same way for every class though, so they're
    covered here regardless of prepared vs. known."""
    SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB = spell_progression_tables()
    out = {}
    for c in char.get("classes", []):
        cname, lvl = c.get("class",""), c.get("level",0)
        sub = c.get("subclass","").lower()
        cant_max = max((v for k,v in CANTRIPS.get(cname,{}).items() if k<=lvl), default=0)
        if cname in SPELLS_KNOWN:
            lvl_max = max((v for k,v in SPELLS_KNOWN[cname].items() if k<=lvl), default=0)
            out[cname] = (cant_max, lvl_max)
        elif cname == "Fighter" and "eldritch knight" in sub:
            lvl_max = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
            out["Fighter (EK)"] = (2 + (1 if lvl>=10 else 0), lvl_max)
        elif cname == "Rogue" and "arcane trickster" in sub:
            lvl_max = max((v for k,v in EK_AT.items() if k<=lvl), default=0)
            out["Rogue (AT)"] = (2 + (1 if lvl>=10 else 0), lvl_max)
        elif cname in PREPARE_AB:
            out[cname] = (cant_max, None)
    return out


def known_spell_classes(char: dict):
    """{class_name: (cantrip_max, leveled_max)} for classes that track
    their OWN known-LEVELED-spells list (Bard, Sorcerer, Warlock,
    Ranger, EK Fighter, AT Rogue) — i.e. all_caster_classes() minus
    the prepared casters, who don't have a known-spells cap at all."""
    return {cn: (c, l) for cn, (c, l) in all_caster_classes(char).items()
            if l is not None}


def attribute_known_spells(char: dict):
    """Partition char['spells_known'] into per-class buckets.

    5e multiclass spellcasting (PHB p.164): each class's spells-known
    is a COMPLETELY SEPARATE pool — a Sorcerer/Warlock doesn't share
    one combined list, and spell slots being shared (multiclass slot
    table) doesn't change that, so a pooled total shown against EACH
    class's own cap would both mis-split multiclass casters and let
    one class's spells count against another's limit. Cantrips are
    attributed across EVERY casting class (prepared casters included,
    since cantrips are
    always "known" regardless of prepared/known spellcasting style);
    leveled spells are only attributed across classes with a genuine
    known-spells pool.

    When a known spell is on more than one of the character's own
    eligible class lists (a genuine overlap), it's assigned to
    whichever eligible class currently has the most room left
    relative to its own cap, keeping the split balanced rather than
    one class eating the other's allowance by list order alone.

    Returns: {class_name: {'cantrips': [...], 'leveled': [...]}}
    """
    from dnd_app.data.spells import get_spell as _gs
    all_classes = all_caster_classes(char)
    known_classes = known_spell_classes(char)
    buckets = {cn: {"cantrips": [], "leveled": []} for cn in all_classes}
    if not all_classes:
        return buckets

    def _real_name(cn):
        return "Wizard" if cn in ("Fighter (EK)", "Rogue (AT)") else cn

    # Racial/subclass bonus spells (Fairy's Druidcraft, a Cleric
    # domain spell, etc.) are merged into spells_known so they're
    # castable, but they're always-known freebies, not a pick that
    # should eat into a class's own known-spells/cantrip cap — so
    # this loop excludes anything in char["bonus_spells"] before
    # counting entries against a class's cap.
    bonus = set(char.get("bonus_spells", []))
    # A prepared caster's (Cleric/Druid/Paladin/Artificer) own
    # full-list access dumps its entire available spell list into the
    # same flat spells_known — a leveled spell there belongs to that
    # class, not to a known-caster class's own pick, even when the
    # name also happens to be on that known-caster's spell list (e.g.
    # "Silence" is both Cleric and Bard). Without this exclusion a
    # Cleric's own domain access got silently counted as "Bard
    # learned it", inflating the Bard's known-spell count/cap.
    from dnd_app.core.builder import full_list_dumped_spell_names
    full_dumped = set()
    for names in full_list_dumped_spell_names(char).values():
        full_dumped.update(names)
    # A leveled spell a prepared caster (Wizard/Cleric/...) can prepare
    # belongs to that class rather than a known-spells pool when it's
    # actually prepared, or when no known-spells class could have it
    # at all -- a Wizard/Warlock preparing Charm Person as a Wizard
    # spell, or keeping Shield in the spellbook, shouldn't use up one
    # of the Warlock's spells known.
    from dnd_app.core.calculator import spell_preparing_classes
    prepared_set = set(char.get("spells_prepared", []))
    for name in char.get("spells_known", []):
        if name in bonus:
            continue
        sp = _gs(name)
        if not sp: continue
        is_cantrip = sp.get("level", 1) == 0
        if not is_cantrip and name in full_dumped:
            continue
        sp_classes = set(sp.get("classes", []))
        if not is_cantrip and spell_preparing_classes(char, sp):
            if name in prepared_set or not any(_real_name(cn) in sp_classes for cn in known_classes):
                continue
        pool = all_classes if is_cantrip else known_classes
        eligible = [cn for cn in pool if _real_name(cn) in sp_classes]
        eligible = list(dict.fromkeys(eligible)) or list(pool.keys())
        if not eligible:
            continue
        if len(eligible) == 1:
            target = eligible[0]
        else:
            def _room(cn):
                cant_max, lvl_max = all_classes[cn]
                bucket = buckets[cn]["cantrips"] if is_cantrip else buckets[cn]["leveled"]
                cap = cant_max if is_cantrip else (lvl_max if lvl_max is not None else 999)
                return cap - len(bucket)
            target = max(eligible, key=_room)
        buckets[target]["cantrips" if is_cantrip else "leveled"].append(name)
    return buckets


def prepared_caster_caps(char: dict) -> dict:
    """{class_name: cap} for each prepared-casting class the character
    has (Wizard/Cleric/Druid: ability mod + class level; Paladin/
    Artificer: ability mod + half class level, rounded down), each with
    a minimum of 1. Per-class, NOT pooled — 5e multiclass spellcasting
    gives each prepared-caster class its own separate prepared-spell
    allotment (PHB p.164, same principle as spells-known being
    per-class for Sorcerer/Bard/Warlock/Ranger). Preparing a Cleric
    spell should never eat into a Druid's separate allotment on the
    same character, or vice versa."""
    from dnd_app.core.character import ability_mod
    _, _, _, PREPARE_AB = spell_progression_tables()
    caps = {}
    for c in char.get("classes", []):
        cname, lvl = c.get("class",""), c.get("level",0)
        if cname not in PREPARE_AB or lvl <= 0:
            continue
        mod = ability_mod(char, PREPARE_AB[cname])
        level_term = (lvl // 2) if cname in ("Paladin", "Artificer") else lvl
        caps[cname] = max(1, mod + level_term)
    return caps


def attribute_prepared_spells(char: dict) -> dict:
    """Partition char['spells_prepared'] into per-class buckets, the
    same way attribute_known_spells() does for spells_known. Only
    ordinary leveled spells count (cantrips and bonus/domain/circle
    spells are always-available and don't draw from any class's
    prepared allotment). When a prepared spell is on more than one of
    the character's own prepared-caster class lists, it's assigned to
    whichever eligible class currently has the most room left, keeping
    the split balanced rather than one class's list winning by order.

    Returns: {class_name: [spell_name, ...]}
    """
    from dnd_app.data.spells import get_spell as _gs
    caps = prepared_caster_caps(char)
    buckets = {cn: [] for cn in caps}
    if not caps:
        return buckets
    bonus = set(char.get("bonus_spells", []))
    for name in char.get("spells_prepared", []):
        if name in bonus:
            continue
        sp = _gs(name)
        if not sp or sp.get("level", 0) == 0:
            continue
        sp_classes = set(sp.get("classes", []))
        eligible = [cn for cn in caps if cn in sp_classes]
        if not eligible:
            continue
        if len(eligible) == 1:
            target = eligible[0]
        else:
            target = max(eligible, key=lambda cn: caps[cn] - len(buckets[cn]))
        buckets[target].append(name)
    return buckets


def spell_limits(char: dict) -> list[dict]:
    """How many spells and cantrips each casting class can know or
    prepare, and how many it has -- plain data, shared by desktop's
    Spells Known / Prepared card and the Android Spells screen.
    One dict per casting class:
      label      "Wizard Lv5" / "EK Fighter Lv3" / "AT Rogue Lv3"
      kind       "known" (Sorcerer/Bard/...) or "prepared" (Wizard/Cleric/...)
      current, max      leveled spells known / prepared vs the cap
      ability    the ability the prepared cap uses ("INT"), else ""
      cantrips, cantrip_max   (cantrip_max 0 = the class gets none)
    Multiclass known-spell casters (Sorcerer/Warlock, Bard/Warlock...)
    are counted SEPARATELY per class -- never pooled into one shared
    count checked against every class's cap. Granted spells (domain,
    racial, feat) don't count, so they're left out of `current`."""
    from dnd_app.core.character import ability_mod as _am
    SPELLS_KNOWN, CANTRIPS, EK_AT, PREPARE_AB = spell_progression_tables()
    attributed = attribute_known_spells(char)
    prepared_attributed = attribute_prepared_spells(char)
    rows = []
    for c in char.get("classes", []):
        cname = c["class"]; lvl = c["level"]
        sub = c.get("subclass", "").lower()
        cmax = max((v for k, v in CANTRIPS.get(cname, {}).items() if k <= lvl), default=0)
        is_ek = cname == "Fighter" and "eldritch knight" in sub
        is_at = cname == "Rogue" and "arcane trickster" in sub
        if is_ek or is_at:
            # EK/AT aren't in the CANTRIPS table (it's keyed by full
            # caster class names) -- 2 cantrips at 3rd level, 3 at 10th
            cmax = 2 + (1 if lvl >= 10 else 0)
        # this class's OWN attributed spells, not the flat spells_known list
        bucket_key = "Fighter (EK)" if is_ek else "Rogue (AT)" if is_at else cname
        mine = attributed.get(bucket_key, {"cantrips": [], "leveled": []})
        row = {"cantrips": len(mine["cantrips"]), "cantrip_max": cmax, "ability": ""}
        if cname in SPELLS_KNOWN:
            best = max((v for k, v in SPELLS_KNOWN[cname].items() if k <= lvl), default=0)
            row.update(label=f"{cname} Lv{lvl}", kind="known", current=len(mine["leveled"]), max=best)
        elif is_ek or is_at:
            best = max((v for k, v in EK_AT.items() if k <= lvl), default=0)
            row.update(label=f"{'EK Fighter' if is_ek else 'AT Rogue'} Lv{lvl}", kind="known",
                       current=len(mine["leveled"]), max=best)
        elif cname in PREPARE_AB:
            ab = PREPARE_AB[cname]
            eff = lvl if cname not in ("Paladin", "Artificer") else max(1, lvl // 2)
            row.update(label=f"{cname} Lv{lvl}", kind="prepared", ability=ab,
                       current=len(prepared_attributed.get(cname, [])),
                       max=max(1, _am(char, ab) + eff))
        else:
            continue
        rows.append(row)
    return rows

