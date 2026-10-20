"""Extra damage on a weapon hit -- what both apps' weapon rows show beside
the weapon's own damage, each with its damage type: spells (Hunter's Mark,
Divine Favor, the smites...), class features (Sneak Attack, Divine Smite,
Crimson Rite, Giant's Might...), race traits and magic items (Flame Tongue,
Holy Avenger...). Nothing here rolls: it says what to add, and the player
rolls it.

    weapon_riders(char, weapon) -> [rider]
        weapon   an equipped weapon's name ("Longsword +1", "Flame Tongue"),
                 or a dict for an attack row that isn't a held weapon:
                 {"name", "kind": "unarmed" or "natural", "melee": True,
                 "damage_type": "bludgeoning", "die": "1d6"}
        rider    {"source", "dice", "type", "when", "flat", "atk", "tip"}
                   dice  what to add: "1d4", "2d8", "3" ("" for an effect
                         with no extra damage on the hit itself)
                   type  its damage type, worked out ("slashing" for one
                         that deals the weapon's own type)
                   when  "" for every hit, or when it applies, said so it
                         follows the dice: "once a turn", "on your next
                         hit", "against undead"
                   flat  True: a plain number on every hit, which the rows
                         add into the weapon's damage (flat_bonus) rather
                         than list
                   atk   a bonus to the attack roll that comes with it
                   tip   the longer explanation (hover / press and hold)

    rider_text(riders)   "+1d4 radiant (Divine Favor) · +1d6 slashing against the
                         marked target (Hunter's Mark)" -- the line under the
                         weapon's damage: only what's on now. What you can
                         choose to add (Sneak Attack, Divine Smite...) is
                         offered after the attack roll, with its cost
                         (core/attacks.py attack_report)
    flat_bonus(riders)   what to add to the damage modifier
    attack_bonus(riders) what to add to the attack bonus
    rider_tip(riders)    every rider, one per line, for the tooltip

Which spell effect goes with which weapon (Magic Weapon, Elemental Weapon,
Holy Weapon, Crimson Rite...) and at what level it was cast is kept in
char["effect_details"] (core/spell_effects.py records it when cast).
"""
import re

DAMAGE_TYPES = ("acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic",
                "piercing", "poison", "psychic", "radiant", "slashing", "thunder")

# ── Named magic weapons: the weapon each one is ───────────────────────────
# "Flame Tongue" is any sword; the rows use the most common one so its
# dice, properties and proficiency are a real weapon's, not a guess.
NAMED_WEAPON_BASES = {
    "Mace of Disruption": "Mace", "Mace of Smiting": "Mace", "Mace of Terror": "Mace",
    "Lightbringer": "Mace", "Javelin of Lightning": "Javelin", "Dagger of Venom": "Dagger",
    "Fate Cutter Shears": "Dagger", "Oathbow": "Longbow", "Dragon Wing Bow": "Longbow",
    "Dwarven Thrower": "Warhammer", "Whelm": "Warhammer", "Hammer of Thunderbolts": "Maul",
    "Trident of Fish Command": "Trident", "Wave": "Trident", "Scimitar of Speed": "Scimitar",
    "Blackrazor": "Greatsword", "Sun Blade": "Longsword", "Berserker Axe": "Battleaxe",
    "Giant Slayer": "Greataxe", "Flame Tongue": "Longsword", "Frost Brand": "Longsword",
    "Holy Avenger": "Longsword", "Dragon Slayer": "Longsword", "Vorpal Sword": "Longsword",
    "Sword of Sharpness": "Longsword", "Sword of Wounding": "Longsword",
    "Sword of Life Stealing": "Longsword", "Nine Lives Stealer": "Longsword",
    "Luck Blade": "Longsword", "Defender": "Longsword", "Dancing Sword": "Longsword",
    "Moon-Touched Sword": "Longsword", "Shatterspike": "Longsword", "Sword of Vengeance": "Longsword",
    "Sword of Kas": "Longsword", "Blade of Avernus": "Longsword", "Fane-Eater": "Battleaxe",
    "Vicious Weapon": "Longsword", "Hellfire Weapon": "Longsword", "Ruidium Weapon": "Longsword",
    "Crystal Blade": "Longsword", "Drown": "Trident", "Bloodshed Blade": "Longsword",
}


# What a named weapon changes about the weapon it is
NAMED_WEAPON_CHANGES = {"Sun Blade": {"damage_type": "radiant", "finesse": True}}


# Items that can be any weapon of a kind: the player picks which
# (char["weapon_bases"][item] -- desktop Gear, Android Equipment)
NAMED_WEAPON_KINDS = {
    "Flame Tongue": "sword", "Frost Brand": "sword", "Holy Avenger": "sword", "Dragon Slayer": "sword",
    "Sword of Wounding": "sword", "Sword of Life Stealing": "sword", "Nine Lives Stealer": "sword",
    "Luck Blade": "sword", "Defender": "sword", "Dancing Sword": "sword", "Moon-Touched Sword": "sword",
    "Sword of Vengeance": "sword", "Vorpal Sword": "slashing sword", "Sword of Sharpness": "slashing sword",
    "Shatterspike": "slashing sword", "Giant Slayer": "axe or sword", "Berserker Axe": "axe",
    "Dragon Wing Bow": "bow", "Vicious Weapon": "weapon", "Hellfire Weapon": "weapon",
    "Ruidium Weapon": "weapon", "Crystal Blade": "sword", "Bloodshed Blade": "sword",
}


def base_weapon_options(name: str) -> list:
    """The weapons an "any sword" (or axe, bow, weapon) item can be; [] for
    an item that's always one weapon (a Mace of Disruption)."""
    from dnd_app.data.items import WEAPON_DICT
    kind = NAMED_WEAPON_KINDS.get((name or "").strip())
    if not kind:
        return []
    out = []
    for wname, w in WEAPON_DICT.items():
        if wname == "Unarmed Strike":
            continue
        n, cat = wname.lower(), str(w.get("category", "")).lower()
        sword = "sword" in n or n in ("rapier", "scimitar", "double-bladed scimitar")
        axe = "axe" in n and "pickaxe" not in n
        if kind == "sword" and sword or kind == "slashing sword" and sword and w.get("dmg_type") == "slashing" \
                or kind == "axe" and axe or kind == "axe or sword" and (axe or sword) \
                or kind == "bow" and n.endswith("bow") and "crossbow" not in n \
                or kind == "weapon" and ("simple" in cat or "martial" in cat):
            out.append(wname)
    return sorted(out)


def weapon_base_of(char: dict, name: str) -> str:
    """The weapon this item is now: the player's pick, or the usual one."""
    picked = (char.get("weapon_bases") or {}).get((name or "").strip())
    return picked if picked in base_weapon_options(name) else named_weapon_base(name)


def set_weapon_base(char: dict, name: str, base: str) -> bool:
    """Which weapon an "any sword" item is (False if it can't be that)."""
    if base not in base_weapon_options(name):
        return False
    char.setdefault("weapon_bases", {})[(name or "").strip()] = base
    return True


def named_weapon(name: str, char: dict = None):
    """(the weapon it is, what it changes) for a named magic weapon --
    ("Longsword", {"damage_type": "radiant", "finesse": True}) for a Sun
    Blade -- or ("", {}) for anything else. An "any sword" item is the
    one the player picked, if they have."""
    from dnd_app.data.items import WEAPON_DICT
    picked = ((char or {}).get("weapon_bases") or {}).get((name or "").strip())
    base = picked if picked in WEAPON_DICT else named_weapon_base(name)
    return base, (dict(NAMED_WEAPON_CHANGES.get((name or "").strip(), {})) if base else {})


def named_weapon_base(name: str) -> str:
    """The weapon a named magic weapon is ("Mace of Disruption" -> "Mace"),
    or "" if it isn't one we know."""
    from dnd_app.data.items import WEAPON_DICT
    base = NAMED_WEAPON_BASES.get((name or "").strip(), "")
    if not base:
        # "Dragon Slayer Greatsword", "Flame Tongue (Shortsword)": a weapon named in it
        for wname in sorted(WEAPON_DICT, key=len, reverse=True):
            if wname != "Unarmed Strike" and re.search(rf"\b{re.escape(wname)}\b", name or "", re.I):
                return wname
    return base


# ── The attack the riders are for ─────────────────────────────────────────
def weapon_profile(char: dict, weapon) -> dict:
    """What the riders need to know about an attack: melee or ranged,
    finesse, thrown, its damage type and die, the magic item it is..."""
    from dnd_app.data.items import WEAPON_DICT
    from dnd_app.data.magic_items import get_magic_item
    from dnd_app.core.weapons import _weapon, kensei_weapons
    if isinstance(weapon, dict):
        p = {"name": weapon.get("name", ""), "base": "", "item": "", "kind": "unarmed", "magic": False,
             "melee": True, "ranged": False, "thrown": False, "finesse": False, "ammo": False,
             "die": "1", "damage_type": "bludgeoning", "kensei": False}
        p.update(weapon)
        return p
    name = weapon or ""
    base, w = _weapon(name)
    item = name if (get_magic_item(name) or {}).get("type") == "Weapon" else ""
    changes = {}
    if not w:
        nb, changes = named_weapon(name, char)
        if nb:
            base, w = nb, WEAPON_DICT.get(nb, {})
    cat = str(w.get("category", "Melee")).lower() if w else "melee"
    props = [str(p).lower() for p in (w.get("properties", []) if w else [])]
    if changes.get("finesse"):
        props.append("finesse")
    if changes.get("damage_type"):
        w = dict(w, dmg_type=changes["damage_type"])
    from dnd_app.core.magic_items import parse_magic_suffix
    magic = bool(item) or bool(parse_magic_suffix(name)[1]) or any(
        i.get("target_item") == name for i in char.get("active_infusions", []))
    return {
        "name": name, "base": base, "item": item, "kind": "weapon", "magic": magic,
        "melee": "melee" in cat, "ranged": "ranged" in cat,
        "thrown": any(p.startswith("thrown") for p in props),
        "finesse": "finesse" in props,
        "ammo": any(p.startswith("ammunition") for p in props),
        "die": (w.get("damage") if w else "") or "1d8",
        "damage_type": (w.get("dmg_type") if w else "") or "slashing",
        "kensei": base in kensei_weapons(char),
    }


def _fits(p: dict, on: str) -> bool:
    """Does a rider for `on` apply to this attack?
         attack           any attack
         weapon attack    a weapon, an unarmed strike or a natural weapon
         melee attack     the same, in melee
         weapon           a held weapon
         melee weapon     a held melee weapon
         ranged           a ranged weapon attack (a thrown one too)
         finesse or ranged, ammo, thrown, unarmed, kensei, kensei ranged"""
    held = p["kind"] == "weapon"
    if on in ("attack", "weapon attack"):
        return True
    if on == "melee attack":
        return p["melee"]
    if on == "weapon":
        return held
    if on == "melee weapon":
        return held and p["melee"]
    if on == "ranged":
        return p["ranged"] or p["thrown"]
    if on == "finesse or ranged":
        return held and (p["finesse"] or p["ranged"])
    if on == "ammo":
        return held and p["ammo"]
    if on == "thrown":
        return held and (p["thrown"] or p["ranged"] and not p["ammo"])
    if on == "unarmed":
        return p["kind"] == "unarmed"
    if on == "kensei":
        return held and p["kensei"]
    if on == "kensei ranged":
        return held and p["kensei"] and p["ranged"]
    return False


def _r(source, dice="", dtype="", when="", flat=False, atk=0, tip="", use="on", cost="", pay=None,
       then="", spend="", instead=False, apart=False, miss="", group="", needs=""):
    """use   "on"      on now: listed under the weapon (an active spell,
                       an always-on property, a flat bonus in the numbers)
             "option"  yours to add when you hit -- offered after the
                       attack roll with its cost (core/attacks.py)
             "crit"    only on a critical hit (or a natural 20)
       cost  what adding it takes, said plainly as a sentence ("Once a
             turn, for 1 ki")
       pay   how the attack dialog spends it: a list of ("turn",) once a
             turn, ("pool", "ki", 1), ("pact",), ("res", key), ("daily",),
             ("action", card name, bucket) -- that action's own rules,
             ("fx", effect) -- the effect's one strike (Zephyr Strike)
       then  what else the hit does ("The target catches fire...")
       spend "hit": a spell your next hit carries goes off with it;
             "shot": hit or miss; "turn": once a turn, gone for the rest
             of the turn after a hit
       instead  its damage replaces the weapon's own (Lightning Arrow)
       apart    its damage is rolled on its own, not added to the hit
       miss  what a missed shot still does (Lightning Arrow)
       group an option's group: one pick per group (also what "needs" names)
       needs an option that only counts with that group picked (Wails
             from the Grave after Sneak Attack)"""
    return {"source": source, "dice": str(dice), "type": dtype, "when": when,
            "flat": flat, "atk": atk, "tip": tip, "use": use, "cost": cost, "pay": pay or [],
            "then": then, "spend": spend, "instead": instead, "apart": apart, "miss": miss,
            "group": group, "needs": needs}


TURN = ("turn",)


def _mods(char):
    from dnd_app.core.character import ability_mod
    return {ab: ability_mod(char, ab) for ab in ("STR", "DEX", "CON", "INT", "WIS", "CHA")}


def _grow(text: str, extra: int) -> str:
    """"{2d8} lightning" with 1 more die -> "3d8 lightning": the dice in
    braces grow with the slot level, like the spell's own."""
    return re.sub(r"\{(\d+d\d+)\}", lambda m: _more_dice(m.group(1), extra), text or "")


def _levels_up(char, name) -> int:
    """How many slot levels above its base the effect was cast (its dice
    grow with each)."""
    spec = EFFECT_RIDERS.get(name)
    details = (char.get("effect_details", {}) or {}).get(name, {}) or {}
    if not spec or not spec[5].get("up") or not details.get("level"):
        return 0
    base_lvl, step = spec[5]["up"]
    return max(0, (int(details["level"]) - base_lvl) // step)


def effect_note(char: dict, name: str) -> str:
    """What a spell on your Active Effects does, as it stands: with its
    dice at the level it was cast ("+2d6 fire" for a Searing Smite cast at
    2nd level), or what's left of it once its hit has landed (the target
    is on fire). "" when the rider table doesn't know it (the effect's own
    note in core/effects.py says it then)."""
    spec = EFFECT_RIDERS.get(name)
    if not spec:
        return ""
    extra = spec[5]
    details = (char.get("effect_details", {}) or {}).get(name, {}) or {}
    more = _levels_up(char, name)
    if details.get("landed"):
        return _grow(extra.get("after", ""), more)
    if not (extra.get("up") or extra.get("next")):
        return ""
    tip = _grow(spec[4], more)
    if tip.startswith(name + ": "):
        tip = tip[len(name) + 2:]
        tip = tip[0].upper() + tip[1:]
    return tip


def _more_dice(dice: str, extra: int) -> str:
    """"1d6" with 2 more dice -> "3d6"."""
    m = re.fullmatch(r"(\d+)d(\d+)", dice)
    return f"{int(m.group(1)) + extra}d{m.group(2)}" if m and extra > 0 else dice


# ── Spells and other effects that are on (char["active_effects"]) ─────────
# name: (dice, type, on, when, tip, extra)
#   when  said so it follows the dice: "+1d6 necrotic against the cursed
#         target (Hex)"
#   type "weapon"  the weapon's own damage type
#   extra up=(base level, levels per die)  one more die per so many slot
#           levels above the base (Searing Smite: (1, 1)); a {1d6} in
#           "then" or "after" grows with it
#         one=True   only the weapon it was cast on (effect_details)
#         pick=(...) the damage types it can be (chosen when cast)
#         next="hit"   it goes off on your next hit ("shot": your next
#                      shot, hit or miss)
#         then="..."   what else that hit does (the target catches fire)
#         after="..."  what's left once it has gone off -- the spell keeps
#                      going (still concentrating); without it, the spell
#                      ends with the hit
#         miss="..."   what a missed shot still does (Lightning Arrow)
#         instead=True its damage replaces the weapon's own
#         apart=True   its damage is rolled on its own, not added to the hit
#         turn=True    once a turn: gone for the rest of the turn once it hits
#         option=(cost) yours to use on an attack, not every one (Zephyr Strike)
EFFECT_RIDERS = {
    "Divine Favor": ("1d4", "radiant", "weapon attack", "", "Divine Favor: your weapon attacks deal an extra 1d4 radiant damage.", {}),
    "Crusader's Mantle": ("1d4", "radiant", "weapon attack", "", "Crusader's Mantle: you and allies within 30 ft deal an extra 1d4 radiant damage with weapon attacks.", {}),
    "Holy Weapon": ("2d8", "radiant", "weapon", "", "Holy Weapon: the weapon you touched deals an extra 2d8 radiant damage on a hit.", {"one": True}),
    "Spirit Shroud": ("1d8", "radiant, necrotic or cold", "attack", "against a target within 10 ft",
                      "Spirit Shroud: your attacks against a creature within 10 ft deal an extra {1d8} radiant, necrotic or cold damage, and it can't regain hit points.",
                      {"up": (3, 2), "pick": ("radiant", "necrotic", "cold")}),
    "Elemental Weapon": ("1d4", "acid, cold, fire, lightning or thunder", "weapon", "",
                         "Elemental Weapon: the weapon you touched is magical: +1 to attack rolls and an extra 1d4 damage of the type you chose.",
                         {"one": True, "pick": ("acid", "cold", "fire", "lightning", "thunder")}),
    "Flame Arrows": ("1d6", "fire", "ammo", "", "Flame Arrows: ammunition drawn from the quiver deals an extra 1d6 fire damage on a hit.", {}),
    # the smites: cast first, then your next hit carries them
    "Searing Smite": ("1d6", "fire", "melee attack", "on your next hit",
                      "Searing Smite: your next melee weapon hit deals an extra {1d6} fire damage and sets the target on fire. "
                      "At the start of each of its turns it makes a CON save: 1d6 fire on a fail, and the fire goes out on a success. "
                      "A creature within 5 ft can use its action to put the fire out.",
                      {"up": (1, 1), "next": "hit",
                       "then": "The target catches fire. At the start of each of its turns it makes a CON save: 1d6 fire on a fail, and the fire goes out on a success.",
                       "after": "The target is on fire. At the start of each of its turns it makes a CON save: 1d6 fire on a fail, and the fire goes out on a success, ending the spell."}),
    "Thunderous Smite": ("2d6", "thunder", "melee attack", "on your next hit",
                         "Thunderous Smite: your next melee weapon hit deals an extra 2d6 thunder damage, and the target makes a STR save or is pushed 10 ft away and knocked prone.",
                         {"next": "hit", "then": "The target makes a STR save or is pushed 10 ft away and knocked prone."}),
    "Wrathful Smite": ("1d6", "psychic", "melee attack", "on your next hit",
                       "Wrathful Smite: your next melee weapon hit deals an extra 1d6 psychic damage, and the target makes a WIS save or is frightened of you until the spell ends.",
                       {"next": "hit",
                        "then": "The target makes a WIS save or is frightened of you. It can use its action on a WIS check against your spell save DC to shake it off.",
                        "after": "The target is frightened of you if it failed its WIS save. It can use its action on a WIS check against your spell save DC to end it."}),
    "Branding Smite": ("2d6", "radiant", "weapon attack", "on your next hit",
                       "Branding Smite: your next weapon hit deals an extra {2d6} radiant damage, and the target sheds dim light and can't turn invisible until the spell ends.",
                       {"up": (2, 1), "next": "hit",
                        "then": "The target sheds dim light in a 5-ft radius and can't turn invisible until the spell ends.",
                        "after": "The target sheds dim light in a 5-ft radius and can't turn invisible."}),
    "Blinding Smite": ("3d8", "radiant", "melee attack", "on your next hit",
                       "Blinding Smite: your next melee weapon hit deals an extra 3d8 radiant damage, and the target makes a CON save or is blinded until the spell ends.",
                       {"next": "hit",
                        "then": "The target makes a CON save or is blinded. It repeats the save at the end of each of its turns.",
                        "after": "The target is blinded if it failed its CON save. It repeats the save at the end of each of its turns."}),
    "Staggering Smite": ("4d6", "psychic", "melee attack", "on your next hit",
                         "Staggering Smite: your next melee weapon hit deals an extra 4d6 psychic damage, and the target makes a WIS save or has disadvantage on attacks and checks, and can't take reactions, until the end of its next turn.",
                         {"next": "hit", "then": "The target makes a WIS save or has disadvantage on attacks and checks, and can't take reactions, until the end of its next turn."}),
    "Banishing Smite": ("5d10", "force", "weapon attack", "on your next hit",
                        "Banishing Smite: your next weapon hit deals an extra 5d10 force damage; if that leaves it at 50 hit points or fewer, it's banished until the spell ends.",
                        {"next": "hit",
                         "then": "If the hit leaves the target at 50 hit points or fewer, it's banished until the spell ends.",
                         "after": "If the hit left the target at 50 hit points or fewer, it's banished until the spell ends."}),
    "Hex": ("1d6", "necrotic", "attack", "against the cursed target", "Hex: your attacks against the cursed creature deal an extra 1d6 necrotic damage.", {}),
    "Hunter's Mark": ("1d6", "weapon", "weapon attack", "against the marked target", "Hunter's Mark: your weapon attacks against the marked creature deal an extra 1d6 damage.", {}),
    "Enlarge": ("1d4", "weapon", "weapon attack", "", "Enlarge: your weapon attacks deal an extra 1d4 damage.", {}),
    "Reduce": ("-1d4", "weapon", "weapon attack", "", "Reduce: your weapon attacks deal 1d4 less damage (minimum 1).", {}),
    "Absorb Elements": ("1d6", "of the absorbed type", "melee attack", "on your next melee hit",
                        "Absorb Elements: your first melee hit before the end of your next turn deals an extra {1d6} damage of the type you absorbed.",
                        {"up": (1, 1), "next": "hit", "pick": ("acid", "cold", "fire", "lightning", "thunder")}),
    "Zephyr Strike": ("1d8", "force", "weapon attack", "",
                      "Zephyr Strike: once while it lasts, one weapon attack on your turn has advantage and deals an extra 1d8 force damage on a hit.",
                      {"option": "Once while it lasts, on an attack you gave advantage", "next": "hit",
                       "after": "Your movement doesn't provoke opportunity attacks."}),
    "Lightning Arrow": ("4d8", "lightning", "ranged", "on your next shot, in place of its damage",
                        "Lightning Arrow: your next ranged weapon attack deals {4d8} lightning in place of its normal damage (half on a miss), and each creature within 10 ft of the target makes a DEX save: {2d8} lightning, or half on a success.",
                        {"up": (3, 1), "next": "shot", "instead": True,
                         "then": "Hit or miss, each creature within 10 ft of the target makes a DEX save: {2d8} lightning, or half on a success.",
                         "miss": "The target takes half of {4d8} lightning, and each creature within 10 ft of it makes a DEX save: {2d8} lightning, or half on a success."}),
    "Hail of Thorns": ("1d10", "piercing", "ranged", "on your next hit, to it and everything within 5 ft",
                       "Hail of Thorns: your next ranged weapon hit also rains thorns: the target and each creature within 5 ft of it make a DEX save, taking {1d10} piercing, or half on a success.",
                       {"up": (1, 1), "next": "hit", "apart": True,
                        "then": "The target and each creature within 5 ft of it make a DEX save: {1d10} piercing, or half on a success."}),
    "Ensnaring Strike": ("", "", "weapon attack", "your next hit can tangle the target in vines",
                         "Ensnaring Strike: when your next weapon attack hits, the target makes a STR save (with advantage if it's Large or bigger) or is restrained by thorny vines, taking {1d6} piercing at the start of each of its turns.",
                         {"up": (1, 1), "next": "hit",
                          "then": "The target makes a STR save (with advantage if it's Large or bigger) or is restrained by vines, taking {1d6} piercing at the start of each of its turns.",
                          "after": "If the target failed its STR save, it's restrained by vines and takes {1d6} piercing at the start of each of its turns. A STR check against your spell save DC frees it."}),
    "Kensei's Shot": ("1d4", "weapon", "kensei ranged", "this turn", "Kensei's Shot: your ranged attacks with kensei weapons deal an extra 1d4 damage this turn.", {}),
    "Precise Strike": ("1d8", "weapon", "weapon attack", "on your next hit",
                       "Precise Strike: your next weapon attack roll this turn has advantage, and +1d8 damage if it hits.",
                       {"next": "hit"}),
    # class features switched on with Use
    "Symbiotic Entity": ("1d6", "necrotic", "melee attack", "", "Symbiotic Entity: your melee weapon attacks deal an extra 1d6 necrotic damage.", {}),
    "Slayer's Prey": ("1d6", "weapon", "weapon attack", "on your first hit each turn against your quarry", "Slayer's Prey: the first time each turn you hit your quarry with a weapon attack, it takes an extra 1d6 damage.", {"turn": True}),
    "Favored Foe": ("FAVOREDFOE", "weapon", "weapon attack", "on your first hit each turn against the marked foe", "Favored Foe: the first time each turn you hit the marked creature, it takes extra damage.", {"turn": True}),
    "Planar Warrior": ("PLANAR", "force", "weapon attack", "on your next hit this turn against the creature you chose",
                       "Planar Warrior: your next hit this turn on the creature you chose deals extra force damage, and all of the hit's damage becomes force.",
                       {"next": "hit", "then": "All of this hit's damage is force damage."}),
    "Giant's Might": ("GIANTSMIGHT", "weapon", "weapon attack", "once a turn", "Giant's Might: once a turn, one weapon attack deals extra damage.", {"turn": True}),
    "Elemental Cleaver": ("CLEAVER", "acid, cold, fire, lightning or thunder", "weapon", "",
                          "Elemental Cleaver: the weapon deals an extra die of the element you chose, and that's its damage type.",
                          {"one": True, "pick": ("acid", "cold", "fire", "lightning", "thunder")}),
    "Radiant Soul (Aasimar)": ("AASIMAR", "radiant", "attack", "once a turn", "Radiant Soul: once a turn, one attack or spell deals extra radiant damage.", {"turn": True}),
    "Necrotic Shroud": ("AASIMAR", "necrotic", "attack", "once a turn", "Necrotic Shroud: once a turn, one attack or spell deals extra necrotic damage.", {"turn": True}),
    "Radiant Consumption": ("AASIMAR", "radiant", "attack", "once a turn", "Radiant Consumption: once a turn, one attack or spell deals extra radiant damage.", {"turn": True}),
    "Flame Tongue": ("2d6", "fire", "weapon", "", "Flame Tongue is ablaze: an extra 2d6 fire damage on a hit.", {"item": "Flame Tongue"}),
    "Chromatic Infusion": ("1d4", "acid, cold, fire, lightning or poison", "weapon", "",
                           "Chromatic Infusion: the weapon deals an extra 1d4 of the type you chose for 1 minute.",
                           {"one": True, "pick": ("acid", "cold", "fire", "lightning", "poison")}),
}


def _effect_dice(char, name, dice, details):
    """The dice for a named amount (FAVOREDFOE, GIANTSMIGHT...), at the
    level it was cast."""
    from dnd_app.core.character import class_levels, total_level, subclasses
    from dnd_app.core.calculator import get_prof_bonus
    cl = class_levels(char)
    if dice == "FAVOREDFOE":
        r = cl.get("Ranger", 0)
        return "1d8" if r >= 14 else "1d6" if r >= 6 else "1d4"
    if dice == "PLANAR":
        return "2d8" if cl.get("Ranger", 0) >= 11 else "1d8"
    if dice == "GIANTSMIGHT":
        f = cl.get("Fighter", 0)
        return "1d10" if f >= 18 else "1d8" if f >= 10 else "1d6"
    if dice == "CLEAVER":
        return "2d6" if cl.get("Barbarian", 0) >= 14 else "1d6"
    if dice == "AASIMAR":
        race = char.get("species") or char.get("race", "")
        return str(get_prof_bonus(char) if "MPMM" in race else total_level(char))
    return dice


def _effect_riders(char, p, out):
    fx = char.get("active_effects", [])
    details_all = char.get("effect_details", {}) or {}
    for name in fx:
        spec = EFFECT_RIDERS.get(name)
        if not spec:
            continue
        dice, dtype, on, when, tip, extra = spec
        if not _fits(p, on):
            continue
        if name == "Elemental Cleaver" and "Rage" not in fx:
            continue                  # only while you rage
        details = details_all.get(name, {}) or {}
        if extra.get("item") and p.get("item") != extra["item"]:
            continue
        if extra.get("one") and details.get("weapon") and details["weapon"] not in (p["name"], p["base"]):
            continue
        # a smite that has gone off: what's left of it is on the target
        if details.get("landed"):
            continue
        dice = _effect_dice(char, name, dice, details)
        more = 0
        if extra.get("up") and details.get("level"):
            base_lvl, step = extra["up"]
            more = max(0, (int(details["level"]) - base_lvl) // step)
            dice = _more_dice(dice, more)
        if details.get("type") and extra.get("pick"):
            dtype = details["type"]
        if name == "Planar Warrior":
            dtype = "force"
        spend = extra.get("next", "") or ("turn" if extra.get("turn") else "")
        kw = dict(tip=_grow(tip, more), then=_grow(extra.get("then", ""), more), spend=spend,
                  instead=bool(extra.get("instead")), apart=bool(extra.get("apart")),
                  miss=_grow(extra.get("miss", ""), more))
        if extra.get("option"):
            # yours to use on one attack: offered after the roll
            out.append(_r(name, dice, dtype, use="option", cost=extra["option"], pay=[("fx", name)], **kw))
        else:
            out.append(_r(name, dice, dtype, when, **kw))
    # Elemental Weapon: +1 to hit (+2 at a 5th-level slot, +3 at 7th), more dice
    if "Elemental Weapon" in fx:
        d = details_all.get("Elemental Weapon", {}) or {}
        if not d.get("weapon") or d["weapon"] in (p["name"], p["base"]):
            lvl = int(d.get("level") or 3)
            n = 3 if lvl >= 7 else 2 if lvl >= 5 else 1
            for r in out:
                if r["source"] == "Elemental Weapon":
                    r["dice"], r["atk"] = f"{n}d4", n
    # Magic Weapon: +1 to attack and damage (+2 at a 4th-level slot, +3 at 6th)
    if "Magic Weapon" in fx and p["kind"] == "weapon":
        d = details_all.get("Magic Weapon", {}) or {}
        if not d.get("weapon") or d["weapon"] in (p["name"], p["base"]):
            lvl = int(d.get("level") or 2)
            n = 3 if lvl >= 6 else 2 if lvl >= 4 else 1
            out.append(_r("Magic Weapon", n, flat=True, atk=n,
                          tip=f"Magic Weapon: +{n} to attack and damage rolls with the weapon you touched."))
    # Oil of Sharpness: +3 to attack and damage with the coated weapon
    if "Oil of Sharpness" in fx and p["kind"] == "weapon" and p["damage_type"] in ("slashing", "piercing"):
        d = details_all.get("Oil of Sharpness", {}) or {}
        if not d.get("weapon") or d["weapon"] in (p["name"], p["base"]):
            out.append(_r("Oil of Sharpness", 3, flat=True, atk=3,
                          tip="Oil of Sharpness: +3 to attack and damage rolls with the coated weapon."))


# ── Class features, race traits and feats ─────────────────────────────────
def _feature_riders(char, p, out):
    from dnd_app.core.character import class_levels, subclasses
    from dnd_app.core.calculator import (get_onhit_damage_bonuses, get_martial_arts_die,
                                         get_hemocraft_die, get_prof_bonus)
    cl, subs, fx = class_levels(char), subclasses(char), char.get("active_effects", [])
    mods = _mods(char)
    held = p["kind"] == "weapon"

    def sub(cls, word):
        return word in subs.get(cls, "").lower()

    # the once-a-turn passives the sheet already knows (Divine Strike,
    # Divine Fury, Hexblade's Curse, Genie's Wrath, Dreadful Strikes,
    # Improved Divine Smite, Aura of Hate, Astral Spark)
    for b in get_onhit_damage_bonuses(char):
        n = b["name"]
        if n in ("Improved Divine Smite",) and not (held and p["melee"]):
            continue
        if n == "Aura of Hate" and not p["melee"]:
            continue
        if n == "Astral Spark" and not held:
            continue
        dtype = b["damage_type"]
        if "weapon" in dtype:
            dtype = "weapon"
        elif "(choice:" in dtype:
            kinds = dtype.split("(choice:")[1].strip(" )").split("/")
            dtype = ", ".join(kinds[:-1]) + " or " + kinds[-1]
        when = {"Divine Fury": "on your first hit each turn", "Genie's Wrath": "on your first hit each turn",
                "Hexblade's Curse": "against the cursed target"}.get(n, "")
        flat = n == "Aura of Hate"
        # on every hit, or on while its effect is (Rage, the curse), or
        # once a turn on the first hit (Divine Fury, Genie's Wrath); the
        # other free once-a-turn ones are yours to add when you hit
        option = n in ("Divine Strike", "Dreadful Strikes", "Astral Spark")
        out.append(_r(n, b["die"], dtype, when, flat=flat,
                      use="option" if option else "on", cost="Once a turn" if option else "",
                      pay=[TURN] if option else None,
                      spend="turn" if n in ("Divine Fury", "Genie's Wrath") else "",
                      tip=f"{n}: +{b['die']} {b['damage_type']}" + (", once a turn" if option else
                                                                    f", {when}" if when else "") + "."))

    # Sneak Attack: a finesse or ranged weapon, once a turn
    if cl.get("Rogue", 0) >= 1 and _fits(p, "finesse or ranged"):
        from dnd_app.core.calculator import get_sneak_attack
        sa = get_sneak_attack(char)
        if sa and sa != "None":
            out.append(_r("Sneak Attack", sa, "weapon", use="option", group="Sneak Attack",
                          cost="Once a turn, when you have advantage or an ally is next to the target",
                          pay=[TURN], tip=f"Sneak Attack: once a turn, +{sa} when you have advantage, or an ally "
                              f"is within 5 ft of the target (and you don't have disadvantage)."))
    # Divine Smite: spend a slot on a melee hit
    if cl.get("Paladin", 0) >= 2 and p["melee"]:
        out.append(_r("Divine Smite", "2d8", "radiant", use="option",
                      cost="For a spell slot: 2d8 radiant, +1d8 for each slot level above 1st",
                      pay=[("smite",)], tip="Divine Smite: when you hit with a melee weapon attack, spend a spell slot for "
                          "2d8 radiant, +1d8 for each slot level above 1st (up to 5d8), and +1d8 more "
                          "against undead or fiends."))
    # Colossus Slayer (Hunter): once a turn vs a hurt creature
    prey = " ".join(char.get("_choices", {}).get("hunter_prey_3", []) or []).lower()
    if cl.get("Ranger", 0) >= 3 and sub("Ranger", "hunter") and "colossus" in prey:
        out.append(_r("Colossus Slayer", "1d8", "weapon", use="option",
                      cost="Once a turn, if the target is already hurt", pay=[TURN], tip="Colossus Slayer: once a turn, +1d8 when you hit a creature that's below its hit point maximum."))
    # Dread Ambusher (Gloom Stalker): the extra attack on your first turn
    if cl.get("Ranger", 0) >= 3 and sub("Ranger", "gloom"):
        out.append(_r("Dread Ambusher", "1d8", "weapon", use="option",
                      cost="Only on the extra attack on your first turn of combat", pay=[TURN], tip="Dread Ambusher: on your first turn of combat, one extra weapon attack; if it hits, +1d8."))
    # Gathered Swarm (Swarmkeeper)
    if cl.get("Ranger", 0) >= 3 and sub("Ranger", "swarm"):
        d = "1d8" if cl.get("Ranger", 0) >= 11 else "1d6"
        out.append(_r("Gathered Swarm", d, "piercing", use="option",
                      cost="Once a turn. Or the swarm moves the target, or you, instead", pay=[TURN], tip=f"Gathered Swarm: once a turn after you hit, the target takes {d} piercing, or the swarm moves it or you."))
    # Psionic Strike (Psi Warrior)
    if cl.get("Fighter", 0) >= 3 and sub("Fighter", "psi warrior") and held:
        f = cl["Fighter"]
        die = "1d12" if f >= 17 else "1d10" if f >= 11 else "1d8" if f >= 5 else "1d6"
        n = max(0, mods["INT"])
        thrust_dc = 8 + get_prof_bonus(char) + mods["INT"]
        thrust = (f". Telekinetic Thrust: a DC {thrust_dc} STR save or you knock the target prone or move it "
                  f"up to 10 ft" if f >= 7 else "")
        out.append(_r("Psionic Strike", f"{die}+{n}" if n else die, "force", use="option",
                      cost="Once a turn, for a Psionic Energy die" + thrust, pay=[("pool", "psi", 1), TURN],
                      then=(f"The target makes a DC {thrust_dc} STR save or you knock it prone or move it up to "
                            f"10 ft (Telekinetic Thrust)" if f >= 7 else ""),
                      tip=f"Psionic Strike: once a turn after you hit within 30 ft, spend a Psionic Energy die: "
                          f"{die} + INT force{thrust}."))
    # Battle Master maneuvers (and Martial Adept)
    if (cl.get("Fighter", 0) >= 3 and sub("Fighter", "battle master")) or "Martial Adept" in char.get("feats", []):
        f = cl.get("Fighter", 0) if sub("Fighter", "battle master") else 0
        die = "1d12" if f >= 18 else "1d10" if f >= 10 else "1d8" if f >= 3 else "1d6"
        out.append(_r("Maneuver", "", "", use="option",
                      cost=f"For a superiority die ({die}): Trip, Pushing, Menacing...",
                      pay=[("action", "Maneuver", "Passive")],
                      tip=f"Maneuvers (Trip, Precision, Menacing...): spend a superiority die ({die}); which one you "
                          f"pick says what the die does."))
    # Eldritch Smite and Lifedrinker (invocations; your pact weapon)
    inv = " ".join(char.get("eldritch_invocations", []) or []).lower()
    if "eldritch smite" in inv and held:
        lvl = char.get("pact_slot_level", 1) or 1
        out.append(_r("Eldritch Smite", f"{1 + lvl}d8", "force", use="option",
                      cost="Once a turn, for a Pact Magic slot. A Huge or smaller target is knocked prone", pay=[("pact",), TURN], tip=f"Eldritch Smite: once a turn when you hit with your pact weapon, spend a Pact Magic slot "
                          f"for 1d8 force, +1d8 per slot level ({1 + lvl}d8 now), and knock a Huge or smaller target prone."))
    if "lifedrinker" in inv and held:
        out.append(_r("Lifedrinker", max(1, mods["CHA"]), "necrotic", "with your pact weapon",
                      tip="Lifedrinker: your pact weapon deals extra necrotic damage equal to your CHA modifier (minimum 1)."))
    # Monks: Deft Strike (Kensei) and Hand of Harm (Mercy), both 1 ki
    ma = get_martial_arts_die(char)
    ma = ma if ma[:1].isdigit() else ("1" + ma if ma.startswith("d") else "")
    if ma and cl.get("Monk", 0) >= 6 and sub("Monk", "kensei") and _fits(p, "kensei"):
        out.append(_r("Deft Strike", ma, "weapon", use="option", cost="Once a turn, for 1 ki",
                      pay=[("action", "Deft Strike", "Passive")], tip=f"Deft Strike: once a turn when you hit with a kensei weapon, spend 1 ki for +{ma}."))
    if ma and cl.get("Monk", 0) >= 3 and sub("Monk", "mercy") and p["kind"] == "unarmed":
        w = mods["WIS"]
        out.append(_r("Hand of Harm", f"{ma}+{w}" if w > 0 else ma, "necrotic", use="option",
                      cost="Once a turn, for 1 ki", pay=[("action", "Hand of Harm", "Passive")], tip=f"Hand of Harm: once a turn when you hit with an unarmed strike, spend 1 ki for {ma} + WIS necrotic."))
    pb = get_prof_bonus(char)
    monk = cl.get("Monk", 0)
    # Stunning Strike (Monk 5th): 1 ki on a melee weapon hit (once a turn in 2024)
    if monk >= 5 and p["melee"]:
        dc = 8 + pb + mods["WIS"]
        out.append(_r("Stunning Strike", use="option",
                      cost=f"For 1 ki. The target makes a DC {dc} CON save or is stunned until the end of your next turn",
                      pay=[("action", "Stunning Strike", "Passive")] + ([TURN] if char.get("edition") == "2024" else []),
                      tip=f"Stunning Strike: when you hit with a melee weapon attack, spend 1 ki: the target makes a "
                          f"DC {dc} CON save or is stunned until the end of your next turn."))
    # Quivering Palm (Open Hand 17th): start the vibrations with an unarmed strike
    if monk >= 17 and sub("Monk", "open hand") and p["kind"] == "unarmed":
        out.append(_r("Quivering Palm", use="option", pay=[("pool", "ki", 3)],
                      cost=f"For 3 ki: lethal vibrations for up to {monk} days",
                      then=f"The vibrations last up to {monk} days. End them with your action (the Quivering Palm "
                           f"card): a CON save, or it drops to 0 hit points",
                      tip="Quivering Palm: when you hit with an unarmed strike, spend 3 ki to start vibrations you "
                          "can end later with your action."))
    # Infectious Fury (Path of the Beast 10th): a natural weapon hit while raging
    if cl.get("Barbarian", 0) >= 10 and sub("Barbarian", "beast") and "Rage" in fx and p["kind"] == "natural":
        dc = 8 + pb + mods["CON"]
        out.append(_r("Infectious Fury", use="option", pay=[("action", "Infectious Fury", "Passive")],
                      cost=f"For one of its uses. A DC {dc} WIS save or 2d12 psychic, or it attacks another creature",
                      tip=f"Infectious Fury: when you hit with your natural weapons while raging, the target makes a "
                          f"DC {dc} WIS save or takes 2d12 psychic damage, or uses its reaction to attack another "
                          f"creature of your choice."))
    rogue = cl.get("Rogue", 0)
    dex_dc = 8 + pb + mods["DEX"]
    # Wails from the Grave (Phantom 3rd): after your Sneak Attack, a second creature
    if rogue >= 3 and sub("Rogue", "phantom") and _fits(p, "finesse or ranged"):
        out.append(_r("Wails from the Grave", use="option", needs="Sneak Attack",
                      pay=[("action", "Wails from the Grave", "Passive")],
                      cost="With Sneak Attack, for one of its uses: half your Sneak Attack dice as necrotic "
                           "damage to a second creature within 30 ft of the first",
                      tip="Wails from the Grave: right after your Sneak Attack, a second creature within 30 ft of "
                          "the first takes necrotic damage: half your Sneak Attack dice."))
    # Rend Mind (Soulknife 17th): Sneak Attack with a psychic blade
    if rogue >= 17 and sub("Rogue", "soulknife") and p["name"] == "Psychic Blade":
        out.append(_r("Rend Mind", use="option", needs="Sneak Attack",
                      pay=[("action", "Rend Mind", "Passive")],
                      cost=f"With Sneak Attack: a DC {dex_dc} WIS save or stunned for 1 minute. Once a long rest "
                           f"(or 3 Psionic Energy dice)",
                      tip=f"Rend Mind: when your psychic blade deals Sneak Attack damage, the target makes a DC "
                          f"{dex_dc} WIS save or is stunned for 1 minute."))
    # Death Strike (Assassin 17th): against a surprised creature
    if rogue >= 17 and sub("Rogue", "assassin"):
        out.append(_r("Death Strike", use="option", pay=[("action", "Death Strike", "Passive")],
                      cost=f"Against a surprised creature: a DC {dex_dc} CON save or this attack's damage is doubled",
                      tip=f"Death Strike: when you hit a surprised creature, it makes a DC {dex_dc} CON save or the "
                          f"attack's damage is doubled."))
    # Song of Victory (Bladesinger 14th): +INT to melee weapon damage while Bladesong is on
    if cl.get("Wizard", 0) >= 14 and sub("Wizard", "blades") and "Bladesong" in fx and held and p["melee"]:
        out.append(_r("Song of Victory", max(1, mods["INT"]), flat=True,
                      tip="Song of Victory: + your INT modifier to melee weapon damage while your Bladesong is on."))
    # Feral Might (Blood Hunter, Lycan): +1/+2/+3 melee damage in hybrid form
    if "Hybrid Transformation" in fx and p["melee"] and not p.get("hybrid"):
        bh = cl.get("Blood Hunter", 0)
        out.append(_r("Feral Might", 3 if bh >= 18 else 2 if bh >= 11 else 1, flat=True,
                      tip="Feral Might: a bonus to melee damage in your hybrid form."))
    # Crimson Rite: the rite's element on the weapon it's on (Blood Hunter)
    if "Crimson Rite" in fx:
        die = get_hemocraft_die(char)
        die = die if die[:1].isdigit() else ("1" + die if die.startswith("d") else "")
        rites = (char.get("effect_details", {}).get("Crimson Rite", {}) or {}).get("rites", {}) or {}
        key = "Unarmed strikes" if p["kind"] == "unarmed" else None
        rite = rites.get(key) if key else (rites.get(p["name"]) or rites.get(p["base"]))
        if die and rite:
            dtype = CRIMSON_RITES.get(rite, "")
            dawn = rite == "Rite of the Dawn"
            out.append(_r(rite, die, dtype, f"and {die} more against undead" if dawn else "",
                          tip=f"{rite}: your hits with this weapon deal an extra {die} {dtype} until your next rest"
                              + (", and one more die against undead." if dawn else ".")))
            if cl.get("Blood Hunter", 0) >= 11 and sub("Blood Hunter", "ghost"):
                out.append(_r("Brand of Sundering", die, dtype, "against your branded target",
                              tip="Brand of Sundering: one more hemocraft die against the branded creature."))
    feats = char.get("feats", [])
    race = (char.get("species") or char.get("race", "") or "").lower()
    # Bard: Psychic Blades (Whispers) and Blade Flourish (Swords), a Bardic Inspiration die each
    bard = cl.get("Bard", 0)
    bi = "1d12" if bard >= 15 else "1d10" if bard >= 10 else "1d8" if bard >= 5 else "1d6"
    if bard >= 3 and sub("Bard", "whispers") and held:
        d = "8d6" if bard >= 15 else "5d6" if bard >= 10 else "3d6" if bard >= 5 else "2d6"
        out.append(_r("Psychic Blades", d, "psychic", use="option",
                      cost="Once a turn, for a Bardic Inspiration die", pay=[("pool", "bi", 1), TURN], tip=f"Psychic Blades: once a turn when you hit with a weapon, spend a Bardic Inspiration die for {d} psychic."))
    if bard >= 3 and sub("Bard", "swords") and held:
        out.append(_r("Blade Flourish", bi, "weapon", use="option",
                      cost="Once a turn, for a Bardic Inspiration die", pay=[("pool", "bi", 1), TURN], tip=f"Blade Flourish: when you take the Attack action, spend a Bardic Inspiration die: +{bi} damage, and a flourish (+AC, push, or hit another)."))
    # Arcane Jolt (Battle Smith): a magic weapon's hit, once a turn
    art = cl.get("Artificer", 0)
    if art >= 9 and sub("Artificer", "battle smith") and p.get("magic"):
        d = "4d6" if art >= 15 else "2d6"
        out.append(_r("Arcane Jolt", d, "force", use="option",
                      cost="Once a turn, for one of its uses. Or heal someone within 30 ft instead",
                      pay=[("res", "arcane_jolt"), TURN], tip=f"Arcane Jolt: once a turn when you hit with a magic weapon, {d} force, or heal a creature within 30 ft that much."))
    # Touch of Death (Death Domain): spend Channel Divinity on a melee hit
    cleric = cl.get("Cleric", 0)
    if cleric >= 2 and sub("Cleric", "death") and p["melee"]:
        out.append(_r("Touch of Death", 5 + 2 * cleric, "necrotic", use="option",
                      cost="For your Channel Divinity", pay=[("pool", "cd", 1)], tip=f"Touch of Death: when you hit with a melee attack, spend Channel Divinity for {5 + 2 * cleric} more necrotic."))
    # Arcane Shot (Arcane Archer): a magic arrow's extra effect
    fighter = cl.get("Fighter", 0)
    if fighter >= 3 and sub("Fighter", "arcane archer") and held and p["ammo"]:
        d = "4d6" if fighter >= 18 else "2d6"
        out.append(_r("Arcane Shot", "", "", use="option",
                      cost="Once a turn, for one of your 2 shots a short rest",
                      pay=[("action", "Arcane Shot", "Passive")],
                      tip=f"Arcane Shot: on a hit with an arrow, one of your shot options -- most add {d} damage of "
                          f"its own type."))
    # Fire Rune (Rune Knight): invoked on a weapon hit, once a short rest
    known = " ".join(char.get("_choices", {}).get("rune_knight_runes", []) or [])
    if cl.get("Fighter", 0) >= 3 and sub("Fighter", "rune knight") and "Fire Rune" in known and held:
        out.append(_r("Fire Rune", "2d6", "fire", use="option",
                      cost="Once a short rest. The target makes a STR save or is restrained, taking 2d6 fire each turn",
                      pay=[("action", "Fire Rune", "Passive")],
                      tip="Fire Rune: when you hit with a weapon, +2d6 fire and fiery shackles (STR save or restrained)."))
    # Foe Slayer (Ranger 20th): once a turn vs your favored enemy
    if cl.get("Ranger", 0) >= 20:
        out.append(_r("Foe Slayer", max(1, mods["WIS"]), "weapon", use="option",
                      cost="Once a turn, against a favored enemy", pay=[TURN], tip="Foe Slayer: once a turn, add your WIS modifier to the attack or the damage against a favored enemy."))
    # Strike of the Giants: a melee or thrown weapon hit, once a turn
    if "Strike of the Giants" in feats and held and (p["melee"] or p["thrown"]):
        out.append(_r("Giant Strike", use="option", pay=[("action", "Giant Strike", "Passive")],
                      cost="Once a turn, for one of its uses: your strike's extra damage and save",
                      tip="Strike of the Giants: once a turn, your chosen strike's extra damage and its save."))
    # Scions of the outer planes and the Knight of the Sword: once a turn on a hit
    if "Agent of Order" in feats:
        out.append(_r("Stasis Strike", "1d8", "force", use="option", pay=[("action", "Stasis Strike", "Passive")],
                      cost="Once a turn, for one of its uses. A WIS save or restrained until the start of your next turn",
                      tip="Stasis Strike: once a turn, +1d8 force and a WIS save or restrained."))
    if "Baleful Scion" in feats:
        out.append(_r("Grasp of Avarice", f"1d6+{get_prof_bonus(char)}", "necrotic", use="option",
                      pay=[("action", "Grasp of Avarice", "Passive")],
                      cost="Once a turn, for one of its uses. You regain hit points equal to the necrotic damage",
                      tip="Grasp of Avarice: once a turn, extra necrotic damage, and you regain that many hit points."))
    if "Knight of the Sword" in feats and held:
        out.append(_r("Demoralizing Strike", use="option", pay=[("action", "Demoralizing Strike", "Passive")],
                      cost="Once a turn, for one of its uses: a WIS save or frightened of you",
                      tip="Demoralizing Strike: once a turn on a weapon hit, a WIS save or frightened of you."))
    # feats: Charger, Poisoner, Orcish Fury
    if "Charger" in feats and p["melee"]:
        out.append(_r("Charger", 5, "weapon", use="option",
                      cost="On your bonus action attack after you Dash", tip="Charger: when you Dash, a bonus action melee attack deals +5 damage (or shove 10 ft)."))
    if "Poisoner" in feats and held:
        out.append(_r("Poisoner", "2d8", "poison", use="option",
                      cost="On a coated weapon (coating it is a bonus action). The target makes a CON save or is poisoned", tip="Poisoner: coat a weapon as a bonus action; a hit deals +2d8 poison and the target makes a CON save or is poisoned."))
    if "Orcish Fury" in feats and held:
        die = p.get("die") or ""
        out.append(_r("Orcish Fury", die if re.fullmatch(r"\d+d\d+", die) else "1 weapon die", "weapon",
                      use="option", cost="Once a short rest", pay=[("res", "Orcish Fury")],
                      tip="Orcish Fury: once a short or long rest, roll one of the weapon's damage dice and add it."))
    # race: Fury of the Small (goblin), Surprise Attack (bugbear)
    from dnd_app.core.character import total_level
    if race.startswith("goblin"):
        n = get_prof_bonus(char) if "mpmm" in race else total_level(char)
        out.append(_r("Fury of the Small", n, "weapon", use="option",
                      cost=("Once a rest" if "mpmm" not in race else "For one of its uses a long rest")
                           + ", against a creature bigger than you",
                      pay=[("action", "Fury of the Small", "Passive")], tip=f"Fury of the Small: when you damage a creature larger than you, +{n} damage."))
    if race.startswith("bugbear"):
        out.append(_r("Surprise Attack", "2d6", "weapon", use="option",
                      cost="Once, against a surprised creature on your first turn", pay=[TURN], tip="Surprise Attack: the first time you hit a surprised creature on your first turn of combat, +2d6."))
    # Brutal Critical (Barbarian) / Savage Attacks (half-orc) / Piercer: more dice on a crit
    if p["melee"] or "Piercer" in feats:
        b = cl.get("Barbarian", 0)
        brutal = 3 if (b >= 17 and p["melee"]) else 2 if (b >= 13 and p["melee"]) else 1 if (b >= 9 and p["melee"]) else 0
        from dnd_app.data.races import keeps_race_traits
        savage = 1 if ("half-orc" in race and p["melee"] and keeps_race_traits(char)) else 0
        piercer = 1 if ("Piercer" in feats and p["damage_type"].startswith("piercing")) else 0
        m = re.fullmatch(r"(\d+)d(\d+)", p.get("die") or "")
        if (brutal or savage or piercer) and m:
            names = (("Brutal Critical", brutal), ("Savage Attacks", savage), ("Piercer", piercer))
            source = " and ".join(n for n, on in names if on)
            n = brutal + savage + piercer
            out.append(_r(source, f"{n}d{m.group(2)}", "weapon", use="crit",
                          tip=f"{source}: on a critical hit, roll {n} more of the weapon's damage dice."))


CRIMSON_RITES = {
    "Rite of the Flame": "fire", "Rite of the Frozen": "cold", "Rite of the Storm": "lightning",
    "Rite of the Dead": "necrotic", "Rite of the Oracle": "psychic", "Rite of the Roar": "thunder",
    "Rite of the Dawn": "radiant",
}


def crimson_rite_options(char) -> list:
    """The rites a Blood Hunter can wake: the primal three, the esoteric
    three from 14th level, and Rite of the Dawn for a Ghostslayer."""
    from dnd_app.core.character import class_levels, subclasses
    bh = class_levels(char).get("Blood Hunter", 0)
    out = ["Rite of the Flame", "Rite of the Frozen", "Rite of the Storm"]
    if bh >= 14:
        out += ["Rite of the Dead", "Rite of the Oracle", "Rite of the Roar"]
    if "ghost" in subclasses(char).get("Blood Hunter", "").lower():
        out.append("Rite of the Dawn")
    return out


# ── Magic items ───────────────────────────────────────────────────────────
# The item's own weapon row: (dice, type, when). Items not here use the
# "extra NdM <type> damage" in their own rules text.
ITEM_RIDERS = {
    "Flame Tongue": ("2d6", "fire", "once it's lit"),
    "Frost Brand": ("1d6", "cold", ""),
    "Holy Avenger": ("2d10", "radiant", "against fiends and undead"),
    "Sun Blade": ("1d8", "radiant", "against undead"),
    "Dragon Slayer": ("3d6", "weapon", "against dragons"),
    "Giant Slayer": ("2d6", "weapon", "against giants, and it makes a STR save or falls prone"),
    "Mace of Disruption": ("2d6", "radiant", "against fiends and undead"),
    "Mace of Smiting": ("2d6", "bludgeoning", "on a 20 (4d6 against a construct)"),
    "Lightbringer": ("1d6", "radiant", "against undead"),
    "Oathbow": ("3d6", "piercing", "against your sworn enemy"),
    "Vicious Weapon": ("7", "weapon", "on a 20"),
    "Dagger of Venom": ("2d10", "poison", "once a day, when it's coated"),
    "Javelin of Lightning": ("4d6", "lightning", "once a day, thrown as a bolt of lightning"),
    "Dwarven Thrower": ("1d8", "bludgeoning", "when thrown (2d8 against giants)"),
    "Whelm": ("1d8", "bludgeoning", "when thrown (2d8 against giants)"),
    "Sword of Sharpness": ("14", "slashing", "on a 20"),
    "Sword of Life Stealing": ("10", "necrotic", "on a 20, unless it's a construct or undead, and you gain 10 temporary HP"),
    "Fane-Eater": ("2d8", "necrotic", "on a 20, and you heal that much"),
    "Fate Cutter Shears": ("1d6", "force", ""),
    "Sword of Wounding": ("", "", "once a turn, a wound that deals 1d4 necrotic at the start of each of its turns"),
    "Wave": ("", "", "on a critical hit, necrotic damage equal to half its hit point maximum"),
    "Nine Lives Stealer": ("", "", "on a 20 against a creature under 100 HP, it makes a CON save or dies"),
    "Vorpal Sword": ("6d8", "slashing", "on a 20 if it can't lose its head (otherwise its head comes off)"),
    "Dragon Wing Bow": ("1d6", "of the dragon's type", ""),
    "Slumbering Dragon's Wrath Weapon": ("", "", "on a 20, 5 damage of the dragon's type to each creature you pick within 5 ft"),
    "Stirring Dragon's Wrath Weapon": ("1d6", "of the dragon's type", ""),
    "Wakened Dragon's Wrath Weapon": ("2d6", "of the dragon's type", ""),
    "Ascendant Dragon's Wrath Weapon": ("3d6", "of the dragon's type", ""),
}

# A weapon's own extra that you choose to use: (cost, how it's paid)
ITEM_OPTIONS = {
    "Dagger of Venom": ("Once a day, after coating it (an action). The target makes a CON save or is poisoned", [("daily",)]),
    "Javelin of Lightning": ("Once a day, when you throw it as a bolt of lightning", [("daily",)]),
    "Sword of Wounding": ("Once a turn. The wound deals 1d4 necrotic at the start of each of its turns", [TURN]),
}

# Items you carry that boost every weapon (or one kind of attack)
#   name: (dice, type, on, when, flat, atk)
CARRIED_ITEM_RIDERS = {
    "Rogue Card": ("6d6", "force", "weapon attack", "Once a day, while you hold the card", False, 0),
    "Insignia of Claws": ("1", "", "unarmed", "", True, 1),
    "+1 Wraps of Unarmed Prowess": ("1", "", "unarmed", "", True, 1),
    "+2 Wraps of Unarmed Prowess": ("2", "", "unarmed", "", True, 2),
    "+3 Wraps of Unarmed Prowess": ("3", "", "unarmed", "", True, 3),
}

_EXTRA_RE = re.compile(r"extra (\d+d\d+|\d+)\s+(?:(" + "|".join(DAMAGE_TYPES) + r")\s+)?damage", re.I)


def _item_riders(char, p, out):
    from dnd_app.core.magic_items import _active_item_names
    from dnd_app.data.magic_items import get_item_effect
    active = set(_active_item_names(char))
    fx = char.get("active_effects", [])
    item = p.get("item")
    if item and item in active:
        spec = ITEM_RIDERS.get(item)
        if spec:
            dice, dtype, when = spec
            tip = f"{item}: " + (f"+{dice} {dtype}" if dice else "") + (f", {when}" if when and dice else when) + "."
            if item == "Flame Tongue":
                if "Flame Tongue" not in fx:     # lit, the effect rider (EFFECT_RIDERS) says so
                    out.append(_r(item, dice, dtype, use="option", cost="Light it first, with your bonus action",
                                  pay=[("action", "Flame Tongue", "Bonus Action")], tip=tip))
            elif item in ITEM_OPTIONS:
                cost, pay = ITEM_OPTIONS[item]
                out.append(_r(item, dice, dtype, use="option", cost=cost, pay=pay, tip=tip))
            elif "on a 20" in when or "on a critical" in when:
                out.append(_r(item, dice, dtype, when, use="crit", tip=tip))
            else:
                out.append(_r(item, dice, dtype, when, tip=tip))
        else:
            effs = get_item_effect(item) or []
            for e in (effs if isinstance(effs, list) else [effs]):
                if e.get("type") != "grant_action":
                    continue
                desc = e.get("description", "")
                for m in _EXTRA_RE.finditer(desc):
                    crit = bool(re.search(r"roll(?:s)? a 20|critical", desc, re.I))
                    out.append(_r(item, m.group(1), (m.group(2) or "weapon").lower(), "on a 20" if crit else "",
                                  use="crit" if crit else "on", tip=f"{item}: {desc}"))
                    break
    for name, (dice, dtype, on, when, flat, atk) in CARRIED_ITEM_RIDERS.items():
        if name in active and _fits(p, on):
            tip = f"{name}: " + (f"+{atk} to attack and damage rolls" if flat else f"+{dice} {dtype}, {when}") + "."
            if flat:
                out.append(_r(name, dice, dtype, when, flat=True, atk=atk, tip=tip))
            else:
                out.append(_r(name, dice, dtype, use="option", cost=when, pay=[("daily",)], tip=tip))
    # weapon-type bonuses (Bracers of Archery: +2 damage with bows)
    for wb in char.get("_weapon_damage_bonuses", []):
        wtype = wb.get("weapon_type", "").lower()
        if wtype and (wtype in p["name"].lower() or wtype in p["base"].lower()):
            out.append(_r(wb.get("source", ""), wb.get("value", 0), flat=True,
                          tip=f"{wb.get('source', '')}: +{wb.get('value', 0)} damage with {wtype}s."))


# ── All of them ───────────────────────────────────────────────────────────
def weapon_riders(char: dict, weapon) -> list:
    p = weapon_profile(char, weapon)
    out = []
    _effect_riders(char, p, out)
    _feature_riders(char, p, out)
    _item_riders(char, p, out)
    for r in out:
        if r["type"] == "weapon":
            r["type"] = p["damage_type"]

    return sorted(live_riders(char, out), key=lambda r: 0 if not r["when"] else 1)


def live_riders(char: dict, riders: list) -> list:
    """Drops a once-a-turn extra that already went off this turn (Divine
    Fury, Favored Foe...): it's back on New Turn."""
    used = set(char.get("_turn_uses", []) or [])
    return [r for r in riders if not (r.get("spend") == "turn" and r["source"] in used)]


# Spells that make an attack roll, by what their text says ("Ranged
# attack: 1d10 fire"), and the few whose short text doesn't say it
_SPELL_ATTACK = re.compile(r"\b(ranged|melee|touch|spell)\s+(spell\s+)?attacks?\b|\bhurl\b.*\battack|"
                           r"\battack (each|on each) turn", re.I)
_SPELL_ATTACK_ALSO = {"Shocking Grasp", "Spiritual Weapon", "Flame Blade", "Steel Wind Strike",
                      "Vampiric Touch", "Chill Touch", "Primal Savagery", "Thorn Whip"}


def is_attack_spell(spell: dict) -> bool:
    """Does casting this spell make an attack roll?"""
    if not spell:
        return False
    if spell.get("name") in _SPELL_ATTACK_ALSO:
        return True
    return bool(_SPELL_ATTACK.search(spell.get("desc") or ""))


def spell_attack_riders(char: dict) -> list:
    """What a spell's attack adds when it hits, as riders: Genie's Wrath
    and Hexblade's Curse (any attack, once a turn / against the cursed
    target), and the effects on any attack (Hex, Spirit Shroud, Radiant
    Soul...). Weapon-only extras (Divine Strike, Divine Fury...) aren't."""
    from dnd_app.core.calculator import get_onhit_damage_bonuses
    out = []
    for b in get_onhit_damage_bonuses(char):
        if b["name"] == "Genie's Wrath":
            out.append(_r(b["name"], b["die"], b["damage_type"], "on your first hit each turn", spend="turn",
                          tip=f"Genie's Wrath: once a turn, +{b['die']} {b['damage_type']} on a hit."))
        elif b["name"] == "Hexblade's Curse":
            out.append(_r(b["name"], b["die"], "", "against the cursed target",
                          tip=f"Hexblade's Curse: +{b['die']} damage against the cursed target."))
    details_all = char.get("effect_details", {}) or {}
    for name in char.get("active_effects", []):
        spec = EFFECT_RIDERS.get(name)
        if not spec or spec[2] != "attack":
            continue
        dice, dtype, _, when, tip, extra = spec
        details = details_all.get(name, {}) or {}
        dice = _effect_dice(char, name, dice, details)
        if extra.get("up") and details.get("level"):
            base_lvl, step = extra["up"]
            dice = _more_dice(dice, max(0, (int(details["level"]) - base_lvl) // step))
        if details.get("type") and extra.get("pick"):
            dtype = details["type"]
        out.append(_r(name, dice, dtype, when, spend="turn" if extra.get("turn") else "", tip=tip))
    return live_riders(char, out)


def spell_hit_note(char: dict, spell) -> str:
    """"On a hit: +3 thunder on your first hit each turn (Genie's Wrath)"
    for a spell that makes an attack roll -- "" for one that doesn't, or
    when nothing adds to it."""
    from dnd_app.data.spells import get_spell
    sp = get_spell(spell) if isinstance(spell, str) else spell
    if not is_attack_spell(sp or {}):
        return ""
    text = rider_text(spell_attack_riders(char))
    return f"On a hit: {text}" if text else ""


def rider_text(riders: list) -> str:
    """The line under a weapon: only what's on now (an option you can add
    is offered after the attack roll instead), each said so it reads on:
    "+1d4 radiant (Divine Favor) · +2d6 fire on your next hit (Searing Smite)"."""
    parts = []
    for r in riders:
        if r["flat"] or r.get("use", "on") != "on":
            continue
        if not r["dice"]:
            parts.append(f"{r['source']}: {r['when']}" if r["when"] else r["source"])
            continue
        sign = "−" if r["dice"].startswith("-") else "+"
        text = f"{sign}{r['dice'].lstrip('-')} {r['type']}".strip()
        if r["when"]:
            text += f" {r['when']}"
        parts.append(f"{text} ({r['source']})")
    return " · ".join(parts)


def flat_bonus(riders: list) -> int:
    return sum(int(r["dice"]) for r in riders if r["flat"] and str(r["dice"]).lstrip("-").isdigit())


def attack_bonus(riders: list) -> int:
    return sum(int(r.get("atk") or 0) for r in riders)


def rider_tip(riders: list) -> str:
    return "\n".join(r["tip"] for r in riders if r.get("tip"))
