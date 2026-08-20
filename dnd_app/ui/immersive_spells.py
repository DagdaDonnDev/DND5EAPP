"""
Immersive Spells (optional rule, default OFF): purely cosmetic, purely
title-only flavor text for the spell list -- never touches the spell's
real name, description, tooltip, or any casting mechanics, only what's
shown on a SpellRow's title label. Three independent situations, each
checked in order (first match wins) since a character is realistically
only ever in one of them at a time:

1. Wild Shaped, and not yet able to actually cast in beast form (no
   Beast Spells -- Circle of the Moon Druid, 18th level): a beast
   can't speak a human language, so every spell title comes out as
   the current beast's noise, stretched to roughly the original
   word's length. "Absorb Elements" as a Brown Bear reads something
   like "Raaaawr Raaaaaawr"; as a Cat, "Meeow Meeeeow".

2. Rage active (Barbarian): a raging mind doesn't have room for
   incantations -- a few iconic spells get a specific exclaimed
   shorthand, single-word spells just get shouted, and anything else
   multi-word collapses to "SMASH!".

3. Paladin with an Oath: every spell title is prefixed with a short
   phrase themed to that Oath.
"""

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


def _wildshape_spell_title(spell_name: str, beast_name: str) -> str:
    base_sound, stretch_idx = _get_beast_sound_profile(beast_name)
    words = spell_name.split()
    if not words:
        return spell_name
    return " ".join(_stretch_word(w, base_sound, stretch_idx) for w in words)


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


# ── 3. Thematic prefixes: Warlock patron, Sorcerer origin, Cleric domain,
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

def compute_display_spell_title(char: dict, spell_name: str) -> str:
    """The text a SpellRow's title label should show for spell_name,
    given the character's current state. Returns spell_name unchanged
    unless the "Immersive Spells" optional rule is on and one of the
    situations above applies. Checked in order -- a full override (can't
    physically speak, or too enraged to do more than shout) outranks a
    merely thematic prefix, and a character realistically only matches
    one of these at a time."""
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

    from dnd_app.core.character import subclasses
    subs = subclasses(char)

    for class_name, prefix_map in (
        ("Warlock", _WARLOCK_PATRON_PREFIXES),
        ("Sorcerer", _SORCERER_ORIGIN_PREFIXES),
        ("Cleric", _CLERIC_DOMAIN_PREFIXES),
        ("Paladin", _OATH_PREFIXES),
    ):
        sub = subs.get(class_name, "")
        if sub:
            prefix = _match_prefix(sub, prefix_map)
            if prefix:
                return prefix + spell_name

    return spell_name
