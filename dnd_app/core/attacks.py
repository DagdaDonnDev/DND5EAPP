"""Every attack you have, worked out once for both apps' Combat screens
(desktop: pages/sheet/combat.py, Android: bridge character_sheet.py
weapons), and what happens when you press its attack button.

    weapon_attack(char, name) -> row     a weapon in your hand
    other_attacks(char) -> [row]         a Monk's unarmed strike, a bite,
                                         armor spikes, a beast's claws...
    roll_attack(char, row) -> roll       the d20, with advantage or
                                         disadvantage from conditions
    attack_report(char, row, roll, free) what to show after the roll: the
                                         total and what it hits, what to
                                         roll if it hits with what's on
                                         now, and what you can add -- only
                                         the ones you can pay for now
    take_attack_options(char, row, picked, answers, hit, roll)
                                         "It hit": pays for the ones
                                         ticked (a slot, ki, a die, once a
                                         turn...), sets off what the hit
                                         carries (a smite) and says what
                                         to roll; "Missed": only the bonus
                                         action ones

    other_attacks(char) -> [attack]
        attack  {"name", "badge", "note", "stat", "atk", "atk_extra", "die",
                 "damage", "damage_type", "kind", "melee", "ranged", "tone",
                 "riders"}
          atk        the attack bonus (int), or None when the stat block
                     gives no roll
          atk_extra  the part of atk that isn't the ability modifier or
                     proficiency (Stalker's Prowess), for the breakdown
          damage     "1d8+3", ready to show
          kind       "unarmed" or "natural" (which riders apply)
          tone       the row's colour family: "monk", "rage", "natural",
                     "armor", "beast"
          riders     the extra damage on a hit (core/riders.py)

In the order the rows are listed: Martial Arts, a Lycan's hybrid form,
race and feat natural weapons, the unarmed strike (Unarmed Fighting,
Tavern Brawler, or the plain one), Form of the Beast, Battlerager armor
spikes, an Armorer's armor model, Longtooth fangs, a vampire's bite, then
a Wild Shape beast's own attacks.
"""
import re


def _mod_text(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def _dmg(die: str, mod: int) -> str:
    """"1d8" + 3 -> "1d8+3"; nothing to add -> just "1d8"; a plain number
    (an unarmed strike's 1) -> the total: "4"."""
    if not die or die == "—":
        return die
    if str(die).isdigit():
        return str(max(1, int(die) + mod))
    return f"{die}{_mod_text(mod)}" if mod else die


def _attack(char, name, die, damage_type, stat, *, badge="", note="", kind="natural", tone="natural",
            melee=True, ranged=False, no_mod=False, atk_extra=0, dmg_extra=0, hybrid=False, extra_riders=(),
            finesse=False, thrown=False, base=""):
    """kind "spell": a spell attack (Radiant Sun Bolt, Luminous Arrow) --
    only what adds to any attack rides on it (Hex, Genie's Wrath...), not
    what needs a weapon."""
    from dnd_app.core.character import ability_mod
    from dnd_app.core.calculator import get_prof_bonus
    from dnd_app.core.riders import weapon_riders, live_riders, spell_attack_riders
    mod = ability_mod(char, stat)
    weapon = {"name": name, "base": base, "kind": kind, "die": die, "damage_type": damage_type.split(" ")[0].rstrip(","),
              "melee": melee, "ranged": ranged, "hybrid": hybrid, "finesse": finesse, "thrown": thrown}
    dmg_mod = mod + dmg_extra
    riders = spell_attack_riders(char) if kind == "spell" else weapon_riders(char, weapon)
    return {
        "name": name, "badge": badge, "note": note, "stat": stat,
        "atk": get_prof_bonus(char) + mod + atk_extra, "atk_extra": atk_extra,
        "die": die, "damage": die if no_mod else _dmg(die, dmg_mod),
        "damage_type": damage_type, "kind": kind, "melee": melee, "ranged": ranged, "tone": tone,
        "riders": riders + live_riders(char, list(extra_riders)),
    }


def _unarmed_blocked(char) -> bool:
    """Wild Shape and a Lycan's hybrid form replace your whole body, so no
    ordinary unarmed strike applies."""
    return bool(char.get("_wildshape_active")) or "Hybrid Transformation" in char.get("active_effects", [])


def _dual_wielding(char) -> bool:
    """Two weapons in hand (two daggers count): no hand free to throw a punch."""
    return len(char.get("equipped_weapons", [])) >= 2


def other_attacks(char: dict) -> list:
    from dnd_app.core.character import ability_mod, subclasses
    from dnd_app.core.calculator import class_levels, get_martial_arts_die, total_level
    from dnd_app.core.riders import _r
    cl, subs, fx = class_levels(char), subclasses(char), char.get("active_effects", [])
    choices = char.get("_choices", {}) or {}
    species = (char.get("species") or char.get("race", "") or "").strip()
    out = []
    ma_die = get_martial_arts_die(char)
    monk = cl.get("Monk", 0) > 0 and ma_die != "—"

    # 1. Martial Arts: STR or DEX, whichever is better, always proficient --
    #    WIS too with the Arms of the Astral Self, which hit for force
    if monk:
        arms = "Arms of the Astral Self" in fx
        pool = ("STR", "DEX", "WIS") if arms else ("STR", "DEX")
        stat = max(pool, key=lambda ab: (ability_mod(char, ab), ab == "DEX"))
        extra = ()
        if "ascendant dragon" in subs.get("Monk", "").lower():
            extra = (_r("Draconic Strike", "", "", "its damage can be acid, cold, fire, lightning or poison instead",
                        tip="Draconic Strike: when you hit with an unarmed strike, its damage can be acid, cold, "
                            "fire, lightning or poison instead."),)
        out.append(_attack(char, "Unarmed Strike", ma_die, "force" if arms else "bludgeoning", stat,
                           badge="Arms of the Astral Self" if arms else "Martial Arts",
                           note=(f"The spectral arms: {stat} for attack and damage, force damage, +5 ft reach."
                                 if arms else
                                 f"Monk unarmed strikes use {stat} and scale with level -- always "
                                 f"proficient, never needs to be equipped."),
                           kind="unarmed", tone="monk", extra_riders=extra))
    # 2. Hybrid Transformation (Blood Hunter, Order of the Lycan): Predatory Strikes
    bh = cl.get("Blood Hunter", 0)
    if bh and "Hybrid Transformation" in fx:
        stat = "DEX" if ability_mod(char, "DEX") > ability_mod(char, "STR") else "STR"
        out.append(_attack(char, "Unarmed Strike", "1d8" if bh >= 11 else "1d6", "bludgeoning or slashing", stat,
                           badge="Hybrid Form", kind="unarmed", tone="rage", hybrid=True,
                           # Stalker's Prowess +1/+2/+3 to hit (7th/11th/18th),
                           # Feral Might +1/+2/+3 damage (3rd/11th/18th)
                           atk_extra=3 if bh >= 18 else 2 if bh >= 11 else 1 if bh >= 7 else 0,
                           dmg_extra=3 if bh >= 18 else 2 if bh >= 11 else 1,
                           note=f"Predatory Strikes: uses {stat}, always proficient. An active Crimson "
                                f"Rite can apply to this attack. You can also make one extra unarmed "
                                f"strike as a bonus action when you take the Attack action."))
    # 3. Race and feat natural weapons (Talons, Claws, Bite...)
    from dnd_app.data.items import RACIAL_NATURAL_WEAPONS
    naturals = list(RACIAL_NATURAL_WEAPONS.get(species, []))
    if species == "Simic Hybrid" and "Grappling Appendages" in choices.get("simic_enhancement_5th", []):
        naturals.append({"name": "Grappling Appendages", "die": "1d6", "damage_type": "bludgeoning", "stat": "STR",
                         "note": "Immediately after hitting, try to grapple as a bonus action. Can't wield "
                                 "weapons or cast with these appendages."})
    if "Dragon Hide" in char.get("feats", []):
        naturals.append({"name": "Dragon Hide Claws", "die": "1d4", "damage_type": "slashing", "stat": "STR",
                         "note": "Retractable claws (no action to extend or retract); slashing instead of "
                                 "an unarmed strike's bludgeoning."})
    if "Touch of Death" in char.get("dm_rewards", []):
        lv = total_level(char)
        d = "4d10" if lv >= 17 else "3d10" if lv >= 11 else "2d10" if lv >= 5 else "1d10"
        naturals.append({"name": "Death Touch", "die": d, "damage_type": "necrotic", "stat": "STR", "no_mod": True,
                         "note": f"Action: an unarmed strike that also deals {d} necrotic on a hit, "
                                 f"ignoring resistance to necrotic damage."})
    for n in naturals:
        out.append(_attack(char, n["name"], n["die"], n["damage_type"], n.get("stat", "STR"), badge="Natural",
                           note="Natural weapon" + (f" -- {n['note']}" if n.get("note") else ""),
                           kind="unarmed" if "unarmed" in n["name"].lower() else "natural",
                           no_mod=n.get("no_mod", False)))
    # 4. The unarmed strike: Unarmed Fighting, Tavern Brawler, or the plain one
    if not monk and not _unarmed_blocked(char) and not _dual_wielding(char):
        styles = " ".join(char.get("fighting_styles", [])).lower()
        if "unarmed fighting" in styles:
            free = not char.get("equipped_weapons") and not char.get("shield")
            out.append(_attack(char, "Unarmed Strike", "1d8" if free else "1d6", "bludgeoning", "STR",
                               badge="Unarmed Fighting", kind="unarmed",
                               note="Unarmed Fighting style: 1d8 with both hands free (no weapon, no shield)."))
        elif "Tavern Brawler" in char.get("feats", []):
            out.append(_attack(char, "Unarmed Strike", "1d4", "bludgeoning", "STR", badge="Tavern Brawler",
                               kind="unarmed", note="Tavern Brawler: a hit with this (or an improvised weapon) "
                                                    "lets you try to grapple as a bonus action."))
        else:
            out.append(_attack(char, "Unarmed Strike", "1", "bludgeoning", "STR", kind="unarmed",
                               note="A punch, kick or headbutt. Instead of damage you can grapple or "
                                    "shove -- see the Actions tab."))
    # Soulknife: Psychic Blades (finesse, thrown 60 ft), a second as a bonus action
    rogue = cl.get("Rogue", 0)
    if rogue >= 3 and "soulknife" in subs.get("Rogue", "").lower():
        stat = "DEX" if ability_mod(char, "DEX") >= ability_mod(char, "STR") else "STR"
        out.append(_attack(char, "Psychic Blade", "1d6", "psychic", stat, badge="Soulknife", kind="weapon",
                           finesse=True, thrown=True, tone="natural",
                           note="A blade of psychic energy: finesse, thrown 60 ft, vanishes after the hit or "
                                "miss. As a bonus action after attacking with one, a second blade: 1d4 psychic."))
    # Spell attacks of a class's own: Radiant Sun Bolt, the Archer's
    # Luminous Arrow, the Fathomless warlock's tentacle
    sab = char.get("spell_attack_bonus", 0) or 0
    if monk and cl.get("Monk", 0) >= 3 and "sun soul" in subs.get("Monk", "").lower():
        out.append(_attack(char, "Radiant Sun Bolt", ma_die, "radiant", "DEX", badge="Sun Soul", kind="spell",
                           melee=False, ranged=True, atk_extra=sab, tone="monk",
                           note="A ranged spell attack, 30 ft, in place of one attack of your Attack action. "
                                "After using it in that action, you can spend 1 ki to make it twice more with "
                                "your bonus action."))
    star = ((char.get("effect_details") or {}).get("Starry Form") or {}).get("choice")
    if "Starry Form" in fx and star == "Archer":
        out.append(_attack(char, "Luminous Arrow", "2d8" if cl.get("Druid", 0) >= 10 else "1d8", "radiant", "WIS",
                           badge="Starry Form", kind="spell", melee=False, ranged=True, atk_extra=sab,
                           note="A ranged spell attack, 60 ft: when you take the form, and with your bonus action "
                                "on later turns while it lasts."))
    if "Tentacle of the Deeps" in fx:
        from dnd_app.core.calculator import _detect_spell_ability
        out.append(_attack(char, "Tentacle of the Deeps", "2d8" if cl.get("Warlock", 0) >= 10 else "1d8", "cold",
                           _detect_spell_ability(char) or "CHA", badge="Fathomless", kind="spell", no_mod=True,
                           atk_extra=sab,
                           note="A melee spell attack against a creature within 10 ft of the tentacle; on a hit "
                                "its speed drops by 10 ft until the start of your next turn. Your bonus action "
                                "moves the tentacle up to 30 ft and attacks again."))
    # Shadow Blade (the spell): a weapon you hold while it lasts
    if "Shadow Blade" in fx:
        lvl = int(((char.get("effect_details", {}) or {}).get("Shadow Blade", {}) or {}).get("level") or 2)
        d = "5d8" if lvl >= 7 else "4d8" if lvl >= 5 else "3d8" if lvl >= 3 else "2d8"
        stat = "DEX" if ability_mod(char, "DEX") >= ability_mod(char, "STR") else "STR"
        out.append(_attack(char, "Shadow Blade", d, "psychic", stat, badge="Spell", kind="weapon",
                           finesse=True, thrown=True, tone="armor",
                           note="Finesse, light, thrown 20/60 ft; advantage on attacks with it in dim light "
                                "or darkness. You're proficient with it."))
    # Polearm Master: the butt end of a glaive, halberd, quarterstaff or spear
    if "Polearm Master" in char.get("feats", []):
        from dnd_app.core.magic_items import parse_magic_suffix
        from dnd_app.core.weapons import weapon_base
        for w in dict.fromkeys(char.get("equipped_weapons", [])):
            if weapon_base(w) in ("Glaive", "Halberd", "Quarterstaff", "Spear"):
                bonus = parse_magic_suffix(w)[1]
                out.append(_attack(char, f"Butt end ({w})", "1d4", "bludgeoning", "STR", badge="Polearm Master",
                                   kind="weapon", base=weapon_base(w), tone="natural",
                                   atk_extra=bonus, dmg_extra=bonus,
                                   note="A bonus action attack after you take the Attack action with it."))
    raging = "Rage" in fx
    barb = subs.get("Barbarian", "").lower()
    # 5. Form of the Beast (Path of the Beast) while raging
    pick = choices.get("beast_form_3", [])
    if raging and "beast" in barb and pick:
        animal = pick[0].split("–")[0].split("-")[0].strip()
        form = {"Bite": ("1d8", "piercing", "Once a turn when you hit a target below half its hit points, "
                                            "regain hit points equal to your proficiency bonus."),
                "Claws": ("1d6", "slashing", "Once a turn, one extra claw attack as part of the same Attack action."),
                "Tail": ("1d8", "piercing", "Reach 10 ft. Reaction: roll a d8 and add it to your AC against one attack."),
                }.get(animal)
        if form:
            out.append(_attack(char, animal, form[0], form[1], "STR", badge="Form of the Beast", note=form[2],
                               tone="rage"))
    # 6. Battlerager armor spikes while raging
    if raging and "battlerager" in barb:
        out.append(_attack(char, "Armor Spikes", "1d4", "piercing", "STR", badge="Battlerager Armor",
                           tone="rage", note="A bonus action attack while raging in spiked armor. When you "
                                             "grapple a creature with the Attack action, the spikes deal it "
                                             "3 piercing damage."))
    # 7. An Armorer's armor model (INT)
    model = " ".join(choices.get("armorer_model_3", []) or []).lower()
    if "armorer" in subs.get("Artificer", "").lower() and ("guardian" in model or "infiltrator" in model):
        g = "guardian" in model
        out.append(_attack(char, "Thunder Gauntlets" if g else "Lightning Launcher", "1d8" if g else "1d6",
                           "thunder" if g else "lightning", "INT", badge="Armor Model", tone="armor",
                           melee=g, ranged=not g,
                           note=("A target you hit has disadvantage on attacks against anyone but you "
                                 "until your next turn." if g else
                                 "Ranged 90/300 ft. Once a turn on a hit, an extra 1d6 lightning."),
                           extra_riders=() if g else (
                               _r("Lightning Launcher", "1d6", "lightning", "once a turn", spend="turn",
                                  tip="Lightning Launcher: once a turn on a hit, an extra 1d6 lightning."),)))
    # 8. Longtooth Shifter's fangs while Shifting
    if ("Shifting" in fx and species.lower() in ("shifter", "shifter (mpmm)")
            and "longtooth" in (char.get("subrace") or "").lower()):
        out.append(_attack(char, "Fangs", "1d6", "piercing", "STR", badge="Longtooth Shifter", tone="rage",
                           note="A bonus action attack while Shifting."))
    # 9. A vampire's bite
    if species.lower() == "vampire":
        out.append(_attack(char, "Bloodthirst", "1", "piercing", "STR", badge="Vampire", tone="rage", no_mod=True,
                           note="Only against a willing, grappled, incapacitated or restrained creature. "
                                "Its hit point maximum drops by the necrotic damage (until it long rests) "
                                "and you regain that much.",
                           extra_riders=(_r("Bloodthirst", "1d6", "necrotic", "against a willing, grappled, "
                                            "incapacitated or restrained target",
                                            tip="Bloodthirst: +1d6 necrotic, draining its hit point maximum."),)))
    # 10. Wild Shape: the beast's own attacks, as its stat block gives them
    active = char.get("_wildshape_active")
    if active:
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        from dnd_app.core.riders import weapon_riders
        beast = WILDSHAPE_BEASTS.get(active) or {}
        for name, desc in beast.get("actions", []):
            if name.lower() == "multiattack":
                continue
            m = re.search(r"([+−-]\d+) to hit", desc)
            dm = re.search(r"Hit: ([\dd+−-]+) (\w+) damage", desc)
            trait = next((f"{tn}: {td}" for tn, td in beast.get("traits", [])
                          if name.lower() in td.lower()
                          and any(k in tn.lower() for k in ("pounce", "charge", "dive", "trampl"))), "")
            dtype = dm.group(2) if dm else ""
            out.append({
                "name": name, "badge": active, "note": desc + (f"\n{trait}" if trait else ""), "stat": "",
                "atk": int(m.group(1).replace("−", "-")) if m else None, "atk_extra": 0, "die": "",
                "damage": dm.group(1).replace("−", "-") if dm else "", "damage_type": dtype,
                "kind": "natural", "melee": True, "ranged": False, "tone": "beast",
                "riders": weapon_riders(char, {"name": name, "kind": "natural", "damage_type": dtype or "bludgeoning"}),
            })
    return out


# ── A weapon in your hand ─────────────────────────────────────────────────
def _owns_as_magic(char, name, base) -> bool:
    """A magic item, or an inventory entry marked magic."""
    names = {(i.get("name") if isinstance(i, dict) else i) for i in char.get("magic_items", [])}
    if name in names or base in names:
        return True
    return any(e.get("name") in (name, base) and e.get("magic") for e in char.get("equipment", []))


def weapon_attack(char: dict, name: str) -> dict:
    """A held weapon's row, step by step:
      1. what it is: "Longsword +1" is a longsword with +1; "Silvered" and
         "Adamantine" are materials; a named magic weapon is the weapon
         underneath (core/riders.py); an infusion can raise the +N
      2. its properties (Thrown Arms Master adds or lengthens Thrown)
      3. proficiency, and which ability: STR, DEX for finesse or ranged,
         CHA with Hex Warrior or INT with Battle Ready when that's better,
         Martial Arts (DEX, its die), Shillelagh (spellcasting, a d8)
      4. the attack: proficiency + ability + magic + Archery + Sacred
         Weapon + power attack + what its riders add
      5. the damage: ability + magic + Dueling + Rage + power attack + the
         flat riders; and, holding two weapons, the off-hand attack's
         damage (light weapons, or any with Dual Wielder): no ability
         modifier unless you have Two-Weapon Fighting or it's negative
    row keys: name, base, category, props, material, proficient, stat,
    atk, magic_bonus, named_bonus, die, damage, damage_type, offhand,
    ranged, thrown, melee, can_power_attack, power_attack, reckless,
    ammo, riders, flat_sources"""
    from dnd_app.core.magic_items import parse_magic_suffix, parse_material_prefix
    from dnd_app.core.character import ability_mod
    from dnd_app.core.calculator import (class_levels, subclasses, get_infusion_bonus, get_prof_bonus,
                                         has_weapon_proficiency, get_rage_damage, _detect_spell_ability)
    from dnd_app.core.riders import named_weapon, weapon_riders, flat_bonus, attack_bonus
    from dnd_app.core.weapons import martial_arts, shillelagh, kensei_bonuses
    from dnd_app.core.ammo import ammo_kind
    from dnd_app.data.items import WEAPON_DICT
    cl, subs = class_levels(char), subclasses(char)
    fx, feats = char.get("active_effects", []), char.get("feats", [])
    styles = " ".join(char.get("fighting_styles", [])).lower()
    # 1. what it is
    base, magic_bonus = parse_magic_suffix(name)
    base, material = parse_material_prefix(base)
    for inf in char.get("active_infusions", []):
        if inf.get("target_item") == name:
            magic_bonus = max(magic_bonus, get_infusion_bonus(inf.get("infusion", ""), cl.get("Artificer", 0)))
    w = WEAPON_DICT.get(base)
    named = False
    if w is None:
        nb, changes = named_weapon(name, char)
        if nb and WEAPON_DICT.get(nb):
            named, base, w = True, nb, dict(WEAPON_DICT[nb])
            if changes.get("damage_type"):
                w["dmg_type"] = changes["damage_type"]
            if changes.get("finesse"):
                w["properties"] = list(w.get("properties", [])) + ["Finesse"]
    fallback = w is None
    if fallback:
        # a named magic weapon we don't know: a generic magic blade, and
        # its own text usually grants proficiency (an Armblade)
        w = {"category": "Melee (magic)", "damage": "1d8",
             "dmg_type": "radiant" if "sun" in name.lower() else "slashing",
             "properties": ["Finesse"] if char.get("_named_weapon_bonuses", {}).get(name) else []}
    category = w.get("category", "")
    die, dtype = w.get("damage", "") or "—", w.get("dmg_type", "")
    props = list(w.get("properties", []) or [])
    # 2. Thrown Arms Master: Thrown for a melee weapon, or 20/40 ft further
    if "Thrown Arms Master" in feats and "melee" in category.lower():
        lowered = [str(x).lower() for x in props]
        if not any(x.startswith("thrown") for x in lowered):
            two = any(x.startswith("two-handed") for x in lowered)
            props.append(f"Thrown ({'15/30' if two else '20/60'} ft, Thrown Arms Master)")
        else:
            for i, x in enumerate(props):
                m = re.search(r"\((\d+)/(\d+)", str(x))
                if "thrown" in str(x).lower() and m:
                    props[i] = re.sub(r"\(\d+/\d+", f"({int(m.group(1)) + 20}/{int(m.group(2)) + 40}", str(x))
    lp = [str(x).lower() for x in props]
    # 3. proficiency and the ability
    proficient = fallback or has_weapon_proficiency(char, base, category)
    finesse = "finesse" in lp or (base == "Double-Bladed Scimitar" and "Revenant Blade" in feats)
    ranged = "ranged" in category.lower()
    thrown = any(x.startswith("thrown") for x in lp)
    two_handed = any(x.startswith("two-handed") for x in lp)
    heavy, light = "heavy" in lp, "light" in lp
    magic = bool(magic_bonus) or fallback or named or _owns_as_magic(char, name, base)
    mod_of = lambda ab: ability_mod(char, ab)
    stat = "DEX" if (finesse and mod_of("DEX") > mod_of("STR")) or ranged else "STR"
    ma = martial_arts(char, name)
    if ma:
        if stat == "STR" and mod_of("DEX") > mod_of("STR"):
            stat = "DEX"
        if ma["die"]:
            die = ma["die"]
        if ma["magical"]:
            dtype = f"{dtype} (magical)"
    sh = shillelagh(char, name)
    if sh:
        die = sh["die"]
        if mod_of(sh["stat"]) > mod_of(stat):
            stat = sh["stat"]
        if "(magical)" not in dtype:
            dtype = f"{dtype} (magical)"
    # Hex Warrior (Hexblade) and Battle Ready (Battle Smith): CHA / INT instead, when it's better
    if cl.get("Warlock", 0) >= 1 and "hexblade" in subs.get("Warlock", "").lower() and not two_handed \
            and mod_of("CHA") > mod_of(stat):
        stat = "CHA"
    if cl.get("Artificer", 0) >= 3 and "battle smith" in subs.get("Artificer", "").lower() and magic \
            and mod_of("INT") > mod_of(stat):
        stat = "INT"
    mod = mod_of(stat)
    # 4. the attack
    named_bonuses = char.get("_named_weapon_bonuses", {})
    named_bonus = named_bonuses.get(name, 0) or named_bonuses.get(base, 0)
    total_bonus = magic_bonus + named_bonus
    total_bonus += kensei_bonuses(char, name, total_bonus).get("bonus", 0)      # Sharpen the Blade
    riders = weapon_riders(char, name)
    archery = 2 if ranged and "archery" in styles else 0
    sacred = max(1, mod_of("CHA")) if "Sacred Weapon" in fx else 0
    can_pa = proficient and (("Great Weapon Master" in feats and not ranged and heavy)
                             or ("Sharpshooter" in feats and ranged))
    pa = can_pa and name in char.get("power_attack_weapons", [])
    pb = get_prof_bonus(char) if proficient else 0
    atk = pb + mod + total_bonus + archery + sacred + (-5 if pa else 0) + attack_bonus(riders)
    # 5. the damage, and the off-hand attack's
    held = char.get("equipped_weapons", [])          # two daggers are two weapons
    dueling = 2 if (not ranged and not two_handed and len(held) == 1 and "dueling" in styles) else 0
    rage = 0
    if "Rage" in fx and not ranged and stat == "STR":
        r = get_rage_damage(char)
        rage = int(r.replace("+", "")) if r not in ("—", "") else 0
    flat = flat_bonus(riders)
    damage = _dmg(die, mod + total_bonus + dueling + rage + (10 if pa else 0) + flat)
    offhand = ""
    if len(held) >= 2 and not ranged and not two_handed and (light or "Dual Wielder" in feats):
        keep = mod if (mod < 0 or "two-weapon fighting" in styles) else 0
        offhand = _dmg(die, keep + total_bonus + rage + flat)
    return {
        "name": name, "base": base, "category": category, "props": props, "material": material,
        "proficient": proficient, "pb": get_prof_bonus(char), "stat": stat, "atk": atk,
        "magic_bonus": total_bonus, "named_bonus": named_bonus, "die": die, "damage": damage,
        "damage_type": dtype, "offhand": offhand, "ranged": ranged, "thrown": thrown,
        "melee": not ranged, "can_power_attack": can_pa, "power_attack": pa,
        "reckless": "Reckless Attack" in fx and not ranged and stat == "STR",
        "ammo": ammo_kind(base, ranged, thrown), "riders": riders,
        "flat_sources": [f"+{r['dice']} {r['source']}" for r in riders if r["flat"]],
        "badge": "", "note": "", "kind": "weapon",
    }


# ── Pressing the attack button ────────────────────────────────────────────
def crit_range(char: dict) -> int:
    """The lowest d20 that's a critical hit: 19 with Improved Critical, 18
    with Superior Critical (Champion)."""
    from dnd_app.core.calculator import class_levels, subclasses
    f = class_levels(char).get("Fighter", 0)
    if "champion" in subclasses(char).get("Fighter", "").lower():
        return 18 if f >= 15 else 19 if f >= 3 else 20
    return 20


def roll_attack(char: dict, row: dict, rng=None) -> dict:
    """The d20 for an attack with this row -- always one: advantage and
    disadvantage are the table's call (cover, the target, your DM), so
    what the sheet knows of them (Reckless Attack, Steady Aim, Poisoned,
    exhaustion...) is a reminder in the note. Steady Aim is for one attack
    roll, so this roll uses it up.
    {"d20", "rolls", "mode", "note", "total", "crit", "nat20", "nat1"}"""
    from dnd_app.core.calculator import roll_d20, roll_reminder
    reminder = roll_reminder(char, "attack", extra_adv=["Reckless Attack"] if row.get("reckless") else [])
    r = roll_d20("normal", rng)
    fx = char.get("active_effects", [])
    if "Steady Aim" in fx:
        char["active_effects"] = [n for n in fx if n != "Steady Aim"]
    atk = row.get("atk") or 0
    return {"d20": r["d20"], "rolls": r["rolls"], "mode": r["mode"], "note": reminder["text"],
            "total": r["d20"] + atk, "crit": r["d20"] >= crit_range(char), "nat20": r["d20"] == 20,
            "nat1": r["d20"] == 1}


def _resource(char, key):
    for r in char.get("resources", []):
        if r.get("key") == key or str(r.get("name", "")).lower() == str(key).lower():
            return r
    return None


def _can_pay(char, r, free) -> bool:
    """Whether every part of an option's cost is there to pay right now --
    an option you can't pay for isn't offered at all."""
    from dnd_app.core import action_use as au
    turn = char.get("_turn_uses", [])
    for item in r.get("pay") or []:
        kind = item[0]
        if kind == "turn" and r["source"] in turn:
            return False
        if kind == "pool":
            pool = au._find_pool(char, item[1])
            if pool is None or (not au._unlimited(pool) and pool.get("current", 0) < item[2]):
                return False
        if kind == "pact" and char.get("pact_slots_max", 0) - char.get("pact_slots_used", 0) <= 0:
            return False
        if kind == "res":
            res = _resource(char, item[1])
            if res is None or (not au._unlimited(res) and res.get("current", 0) <= 0):
                return False
        if kind == "smite" and not _smite_choices(char):
            return False
        if kind == "daily":
            if (char.get("item_uses", {}).get(r["source"]) or {}).get("current", 1) <= 0:
                return False
        if kind == "action":
            card, bucket = item[1], item[2]
            if bucket != "Passive" and bucket not in free:
                return False
            if card == "Maneuver":
                sd = au._find_pool(char, "sd")
                if sd is None or (not au._unlimited(sd) and sd.get("current", 0) < 1):
                    return False
                continue
            if card == "Divine Smite":
                if not any(s[1] == "slot" and s[2] <= 5 for s in au._slots_free(char)):
                    return False
                continue
            spec = au.rule_for(card)
            if spec is None:
                res = au._own_resource(char, card)
                if res is not None and not au._unlimited(res) and res.get("current", 0) <= 0:
                    return False
                continue
            if spec.get("once") and card in turn:
                return False
            if spec.get("needs") and au._need_problem(char, spec["needs"]):
                return False
            if spec.get("once_per") and card in (char.get("_once_per") or {}).get(spec["once_per"], []):
                return False
            uses = au._uses_resource(char, card, spec) if spec.get("uses") else None
            if uses is not None and not au._unlimited(uses) and uses.get("current", 0) <= 0 and not spec.get("alt"):
                return False
            problem, _, _, _ = au._pay(char, card, au._costs(spec), {"n_ki": "1", "slot": ""}, check_only=True)
            if problem:
                return False
    return True


def _ordinal(n):
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"


def _smite_choices(char) -> list:
    """Each spell slot Divine Smite could spend right now, with its dice:
    [(key, label, level, "slot" or "pact", left, d8s)] -- 2d8 at 1st
    level, +1d8 a level, at most 5d8 (2014; the 2024 spell has no cap)."""
    from dnd_app.core import action_use as au
    cap = 99 if char.get("edition") == "2024" else 5
    out = []
    for label, kind, lvl in au._slots_free(char):
        left = int(re.search(r"\((\d+) left\)", label).group(1)) if re.search(r"\((\d+) left\)", label) else 1
        name = f"{_ordinal(lvl)}-level slot" if kind == "slot" else f"Pact Magic slot ({_ordinal(lvl)} level)"
        out.append((f"Divine Smite: {name}", name, lvl, kind, left, min(cap, 1 + lvl)))
    return out


SMITE_FIEND = "Divine Smite: undead or fiend"


def _double(dice) -> str:
    """A critical hit rolls the damage dice twice: "1d6+4" -> "2d6+4"."""
    return re.sub(r"(\d+)d(\d+)", lambda m: f"{2 * int(m.group(1))}d{m.group(2)}", str(dice or ""))


def _sentence(text: str) -> str:
    """"against undead" -> "Against undead." -- for the notes under a line."""
    text = (text or "").strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    return text if text.endswith((".", "!", "?")) else text + "."


def _damage_mod(row) -> str:
    """The number added to the attack's damage ("+3" in "1d8+3"), or ""."""
    m = re.fullmatch(r"\d+d\d+([+-]\d+)", row.get("damage", "") or "")
    return m.group(1) if m else ""


def _followups(char, row, free) -> list:
    """What else this attack's turn allows with your bonus action -- the
    off-hand attack, Flurry of Blows... -- only the ones your bonus action
    (and ki) allow right now, as
    [(key, title, what, sub, pay, said)]:
        what  on the right: its damage, or what you get ("2 unarmed strikes")
        sub   under the name: what else it takes, or where it's from
        said  the line for the toast once it's picked"""
    from dnd_app.core import action_use as au
    from dnd_app.core.calculator import class_levels, subclasses
    from dnd_app.core.character import ability_mod
    from dnd_app.core.weapons import martial_arts, weapon_base
    if "Bonus Action" not in free:
        return []
    cl, fx, feats = class_levels(char), char.get("active_effects", []), char.get("feats", [])
    held = char.get("equipped_weapons", [])
    BA = [("slot", "Bonus Action")]
    out = []
    monk_attack = cl.get("Monk", 0) and (row.get("kind") == "unarmed" or martial_arts(char, row.get("name", "")))
    if monk_attack:
        out.append(("Martial Arts", "Martial Arts", "1 unarmed strike", "",
                    BA, "Martial Arts: 1 unarmed strike with your bonus action"))
        ki = au._find_pool(char, "ki")
        if ki is not None and cl.get("Monk", 0) >= 2 and (au._unlimited(ki) or ki.get("current", 0) >= 1):
            out.append(("Flurry of Blows", "Flurry of Blows", "2 unarmed strikes", "For 1 ki",
                        [("action", "Flurry of Blows", "Bonus Action")], ""))
    if row.get("offhand"):
        dmg = f"{row['offhand']} {row.get('damage_type', '')}".strip()
        out.append(("Off-hand attack", "Off-hand attack", dmg, "With your other light weapon",
                    BA, f"Off-hand attack with your bonus action: {dmg} on a hit"))
    base = weapon_base(row.get("name", "")) if row.get("kind") == "weapon" else ""
    if "Polearm Master" in feats and base in ("Glaive", "Halberd", "Quarterstaff", "Spear"):
        dmg = f"1d4{_damage_mod(row)} bludgeoning"
        out.append(("Polearm Master", "Butt-end attack", dmg, "Polearm Master",
                    BA, f"Butt-end attack with your bonus action: {dmg} on a hit"))
    if "Crossbow Expert" in feats and "Hand Crossbow" in [weapon_base(w) for w in held] and base != "Hand Crossbow":
        out.append(("Crossbow Expert", "Hand crossbow attack", "", "Crossbow Expert",
                    BA, "Hand crossbow attack with your bonus action"))
    if "Frenzy" in fx and row.get("melee"):
        out.append(("Frenzy", "Frenzy", "1 more melee attack", "While your frenzy lasts",
                    BA, "Frenzy: 1 more melee attack with your bonus action"))
    if "Rage" in fx and "battlerager" in subclasses(char).get("Barbarian", "").lower() \
            and row.get("name") != "Armor Spikes":
        dmg = f"{_dmg('1d4', ability_mod(char, 'STR'))} piercing"
        out.append(("Armor spikes", "Armor spikes attack", dmg, "While you rage",
                    BA, f"Armor spikes attack with your bonus action: {dmg} on a hit"))
    if "Hybrid Transformation" in fx and row.get("kind") == "unarmed":
        out.append(("Predatory Strikes", "Predatory Strikes", "1 more unarmed strike", "In your hybrid form",
                    BA, "Predatory Strikes: 1 more unarmed strike with your bonus action"))
    if "Shield Master" in feats and char.get("shield") and char.get("edition") != "2024":
        out.append(("Shield Master", "Shield shove", "", "Knock the target prone, or push it 5 ft away",
                    BA, "Shield shove with your bonus action: knock the target prone, or push it 5 ft away"))
    if "Tavern Brawler" in feats and row.get("kind") == "unarmed":
        out.append(("Tavern Brawler", "Grapple", "", "Tavern Brawler: try to grapple the target",
                    BA, "Grapple with your bonus action (Tavern Brawler)"))
    # Soulknife: a second psychic blade, a d4
    if row.get("name") == "Psychic Blade":
        dmg = f"{_dmg('1d4', ability_mod(char, row.get('stat') or 'DEX'))} psychic"
        out.append(("Second psychic blade", "Second psychic blade", dmg, "With your other hand free",
                    BA, f"A second psychic blade with your bonus action: {dmg} on a hit"))
    # Sudden Strike (Scout 17th): one more attack, Sneak Attack can apply to another target
    if cl.get("Rogue", 0) >= 17 and "scout" in subclasses(char).get("Rogue", "").lower():
        out.append(("Sudden Strike", "Sudden Strike", "1 more attack",
                    "Its Sneak Attack can't be on a creature you've already Sneak Attacked this turn",
                    BA, "Sudden Strike: 1 more attack with your bonus action"))
    # Great Weapon Master: after a critical hit, or a hit that drops a creature to 0 HP
    if "Great Weapon Master" in feats and row.get("kind") == "weapon" and row.get("melee"):
        out.append(("Great Weapon Master", "Great Weapon Master attack", "1 more melee weapon attack",
                    "After a critical hit, or a hit that drops a creature to 0 hit points",
                    BA, "Great Weapon Master: 1 more melee weapon attack with your bonus action"))
    return out


def _hit_lines(row, crit: bool, nat20: bool) -> list:
    """What a hit deals, in the order to read it: the attack's own damage,
    then each extra that's on, then what a critical hit adds -- each
    {"dice", "type", "source", "note", "apart"}. On a critical hit the dice
    are already doubled: the numbers are the ones to roll. A spell that
    replaces the weapon's damage (Lightning Arrow) takes the first line."""
    twice = _double if crit else str
    lines = [{"dice": twice(row.get("damage", "")), "type": row.get("damage_type", ""),
              "source": row.get("name", ""), "note": "", "apart": False}]
    for r in row.get("riders", []):
        if r.get("use", "on") != "on" or r["flat"]:
            continue
        carried = r.get("spend") in ("hit", "shot")      # a spell this hit carries
        when = "" if carried and r["dice"] else _sentence(r["when"])
        note = " ".join(x for x in (when, _sentence(r.get("then", ""))) if x)
        line = {"dice": r["dice"] if r.get("apart") else twice(r["dice"]), "type": r["type"],
                "source": r["source"], "note": note, "apart": bool(r.get("apart"))}
        if r.get("instead"):
            line["note"] = " ".join(x for x in ("In place of the weapon's damage.", note) if x)
            lines[0] = line
        else:
            lines.append(line)
    if crit:
        for r in row.get("riders", []):
            if r.get("use") == "crit" and (nat20 or "on a 20" not in r.get("when", "")):
                lines.append({"dice": r["dice"], "type": r["type"], "source": r["source"],
                              "note": _sentence(r["when"]) or "On a critical hit.", "apart": False})
    return lines


def _roll_text(lines) -> str:
    """"1d8+3 slashing + 1d4 radiant + 2d6 fire" -- what to roll for the
    hit (damage rolled on its own, like Hail of Thorns', isn't in it)."""
    out = ""
    for i, h in enumerate(lines):
        if not h["dice"] or h.get("apart"):
            continue
        part = f"{h['dice'].lstrip('-')} {h['type']}".strip()
        out += part if not out else (f" − {part}" if h["dice"].startswith("-") else f" + {part}")
    return out


def attack_report(char: dict, row: dict, roll: dict, free=("Action", "Bonus Action", "Reaction")) -> dict:
    """What the attack dialog shows, for both apps to lay out the same way:
        title     the attack's name
        roll      {"total", "d20", "mod", "note", "crit", "nat1",
                  "line": "Rolled 14 + 7", "verdict": "Hits AC 21 or lower"}
        hit_title the heading over the damage ("IF IT HITS, ROLL"), "" on
                  a natural 1
        hit       [{"dice", "type", "source", "note", "apart"}] -- the
                  attack's own damage first, then what's on now (a smite
                  your next hit carries, Hunter's Mark...), then what a
                  critical hit adds; dice already doubled on a crit
        attacks   "The Attack action gives you 2 attacks.", or ""
        options   [{"key", "title", "dice", "cost", "group", "needs",
                  "section", "head", "head_note"}] -- section "add": what
                  you can add to this hit; "also": what your bonus action
                  can do. Options in a group are one choice (Divine
                  Smite's slot); "needs" only counts with its group picked
                  (undead or fiend); "head"/"head_note" start a block
                  (Divine Smite). Only what you can pay for right now.
        sections  [{"name", "title"}] -- the ones with options, in order
        hit_button / miss_button  the two buttons' words ("" = no button):
                  "It hit" and "Missed"; a natural 1 has no "It hit", a
                  critical hit has "Cancel" in place of "Missed"
        message   all of it as plain text
    free: the parts of the turn still free. A spell you could add (the
    2024 Divine Smite) isn't offered once you've cast a spell this turn
    (char["_turn_spells"])."""
    from dnd_app.core.multiclass import get_extra_attacks
    from dnd_app.core.calculator import class_levels, subclasses
    atk = row.get("atk") or 0
    nat1 = roll["nat1"]
    crit = bool(roll["crit"]) and not nat1
    twice = _double if crit else str
    riders = row.get("riders", [])
    hit = [] if nat1 else _hit_lines(row, crit, roll.get("nat20", False))
    options = []
    if not nat1:
        # what you can add, with its cost -- only what you can pay for now
        offered = {r.get("group") for r in riders if r.get("use") == "option" and _can_pay(char, r, free)}
        for r in riders:
            if r.get("use") != "option" or not _can_pay(char, r, free):
                continue
            if r.get("needs") and r["needs"] not in offered:
                continue
            if ("smite",) in [tuple(x) for x in r.get("pay") or []]:
                two = char.get("edition") == "2024"
                # the 2024 Divine Smite is a spell, cast with your bonus action
                if two and ("Bonus Action" not in free or char.get("_turn_spells")):
                    continue
                choices = _smite_choices(char)
                for i, (key, name, lvl, kind, left, n) in enumerate(choices):
                    options.append({"key": key, "title": name[0].upper() + name[1:],
                                    "dice": f"+{twice(f'{n}d8')} radiant", "cost": f"{left} left",
                                    "group": "Divine Smite", "needs": "", "section": "add",
                                    "head": "Divine Smite" if i == 0 else "",
                                    "head_note": ("" if i else "A spell: your bonus action and one of these slots"
                                                  if two else "Spend one of these spell slots")})
                if choices:
                    options.append({"key": SMITE_FIEND, "title": "The target is undead or a fiend",
                                    "dice": f"+{twice('1d8')} radiant", "cost": "On top of the slot you pick",
                                    "group": "", "needs": "Divine Smite", "section": "add",
                                    "head": "", "head_note": ""})
                continue
            dice = r["dice"] if r.get("apart") else twice(r["dice"])
            options.append({"key": r["source"], "title": r["source"],
                            "dice": f"+{dice} {r['type']}".strip() if r["dice"] else "",
                            "cost": r.get("cost", ""), "group": r.get("group", ""), "needs": r.get("needs", ""),
                            "section": "add", "head": "", "head_note": ""})
    # what your bonus action can do
    for key, title, what, sub, pay, said in _followups(char, row, free):
        options.append({"key": key, "title": title, "dice": what, "cost": sub,
                        "group": "", "needs": "", "section": "also", "head": "", "head_note": ""})
    sections = [{"name": n, "title": t} for n, t in (("add", "ADD TO THIS HIT"), ("also", "WITH YOUR BONUS ACTION"))
                if any(o["section"] == n for o in options)]
    n = get_extra_attacks(class_levels(char), subclasses(char), char)
    attacks = f"The Attack action gives you {n} attacks." if n > 1 else ""
    mod = "" if not atk else f" + {atk}" if atk > 0 else f" − {-atk}"
    rinfo = {"total": roll["total"], "d20": roll["d20"], "mod": _mod_text(atk), "note": roll.get("note", ""),
             "crit": crit, "nat1": nat1, "nat20": bool(roll.get("nat20")), "line": f"Rolled {roll['d20']}{mod}",
             "verdict": ("A natural 1 always misses" if nat1 else
                         "A critical hit: it hits, and the damage dice are doubled" if crit else
                         f"Hits AC {roll['total']} or lower")}
    # the same, as plain text
    lines = [f"{rinfo['line']} = {roll['total']} to hit. {rinfo['verdict']}."]
    if rinfo["note"]:
        lines.append(rinfo["note"])
    if hit:
        lines.append(("Roll " if crit else "If it hits, roll ") + _roll_text(hit))
        lines += [f"{h['source']}: {h['note']}" for h in hit if h["note"]]
    if attacks:
        lines.append(attacks)
    return {"title": row.get("name", ""), "roll": rinfo,
            "hit_title": "" if nat1 else "ROLL THIS DAMAGE" if crit else "IF IT HITS, ROLL",
            "hit": hit, "attacks": attacks, "options": options, "sections": sections,
            "hit_button": "" if nat1 else "It hit", "miss_button": "Cancel" if crit else "Missed",
            "message": "\n".join(lines)}


def _spell_goes_off(char, r) -> str:
    """A spell your hit carried has gone off: what's left stays on the
    target while you concentrate (Searing Smite's fire), or the spell ends
    (Thunderous Smite). Returns the spell's name."""
    from dnd_app.core.riders import EFFECT_RIDERS
    name = r["source"]
    extra = (EFFECT_RIDERS.get(name) or (None,) * 6)[5] or {}
    if extra.get("after"):
        char.setdefault("effect_details", {}).setdefault(name, {})["landed"] = True
    else:
        char["active_effects"] = [n for n in char.get("active_effects", []) if n != name]
        (char.get("effect_details") or {}).pop(name, None)
        conc = char.get("concentration") or {}
        if conc.get("spell") == name:
            conc["spell"], conc["since_round"] = None, 0
    return name


def take_attack_options(char: dict, row: dict, picked, answers: dict, hit: bool = True,
                        roll=None) -> dict:
    """After the attack: "It hit" (hit=True) or "Missed".
      It hit   the ticked extras are paid for (a slot, ki, a die, once a
               turn...); a spell the hit carried goes off (Searing Smite:
               the target catches fire, and the spell carries on;
               Thunderous Smite ends); a once-a-turn extra is done for the
               turn. The toast says what to roll, what was spent and what
               else happens.
      Missed   only what you do with your bonus action, and a spell that
               goes off either way (Lightning Arrow).
    roll: the report's roll ({"crit", "nat20"}): on a critical hit the
    dice to roll are doubled. Same question protocol as
    core/action_use.py; `answers` keeps what's been paid between rounds
    (nothing is paid twice)."""
    from dnd_app.core import action_use as au
    picked = list(picked)
    crit, nat20 = bool((roll or {}).get("crit")), bool((roll or {}).get("nat20"))
    twice = _double if crit else str
    riders = row.get("riders", [])
    by_name = {r["source"]: r for r in riders if r.get("use") == "option"}
    follow = {f[0]: f for f in _followups(char, row, ("Action", "Bonus Action", "Reaction"))}
    rolls, spent, notes, said, slots = [], [], [], [], []
    refresh = False

    def result(ask=None):
        return {"ok": ask is None, "toast": "" if ask else _toast(),
                "ask": ask, "refresh": refresh, "slots": slots}

    def _toast():
        out = []
        if hit:
            text = _roll_text(_hit_lines(row, crit, nat20) + rolls)
            if text:
                out.append(("Critical hit! Roll " if crit else "Roll ") + text)
        if spent:
            out.append("Spent: " + " · ".join(spent))
        return "\n".join(out + notes + said)

    # 1. Divine Smite: the slot picked, and whether it's undead or a fiend
    smite = next((k for k in picked if k.startswith("Divine Smite: ") and k != SMITE_FIEND), None) if hit else None
    if smite:
        done = f"{smite}:done"
        if done not in answers:
            choice = {c[0]: c for c in _smite_choices(char)}.get(smite)
            if choice is None:
                answers[done] = None                        # that slot's gone
            else:
                _, name, lvl, kind, left, n = choice
                if kind == "pact":
                    char["pact_slots_used"] = char.get("pact_slots_used", 0) + 1
                else:
                    char["spell_slots_used"][lvl - 1] += 1
                fiend = SMITE_FIEND in picked
                bonus = char.get("edition") == "2024"
                answers[done] = {"dice": f"{n + fiend}d8", "spent": f"a {name} ({left - 1} left)"
                                 + (" and your bonus action" if bonus else ""), "bonus": bonus}
                refresh = True
        got = answers[done]
        if got:
            rolls.append({"dice": twice(got["dice"]), "type": "radiant", "source": "Divine Smite", "apart": False})
            spent.append(got["spent"])
            if got["bonus"]:
                slots.append("Bonus Action")
    for key in picked:
        if key.startswith("Divine Smite: "):
            continue
        done = f"{key}:done"
        # 2. what your bonus action does
        if key in follow and key not in by_name:
            if done not in answers:
                _, title, what, sub, pay, line = follow[key]
                for item in pay:
                    if item[0] == "slot":
                        slots.append(item[1])
                    elif item[0] == "action":
                        res = au.use_action(char, item[2], item[1], "", {})
                        if not res.get("ok"):
                            line = res.get("toast") or f"{title}: can't now"
                            break
                        if res.get("slot"):
                            slots.append(res["slot"])
                        line = res.get("toast") or line
                answers[done] = line
                refresh = True
            said.append(answers[done])
            continue
        # 3. an extra you added to the hit
        r = by_name.get(key)
        if r is None or not hit:
            continue
        if r.get("needs") and not any(by_name[k].get("group") == r["needs"] for k in picked if k in by_name):
            continue
        if done not in answers:
            got = {"spent": [], "notes": [], "ok": True}
            for item in r.get("pay") or []:
                kind = item[0]
                if kind == "turn":
                    char.setdefault("_turn_uses", []).append(key)
                    if len(r.get("pay")) == 1:
                        got["spent"].append(f"{key} for this turn")
                elif kind == "pool":
                    pool = au._find_pool(char, item[1])
                    if pool is not None and not au._unlimited(pool):
                        pool["current"] = max(0, pool.get("current", 0) - item[2])
                        got["spent"].append(f"{item[2]} {au._noun(item[1], item[2])} ({pool['current']} left)")
                elif kind == "pact":
                    char["pact_slots_used"] = char.get("pact_slots_used", 0) + 1
                    left = char.get("pact_slots_max", 0) - char["pact_slots_used"]
                    got["spent"].append(f"a Pact Magic slot ({left} left)")
                elif kind == "res":
                    res = _resource(char, item[1])
                    if res is not None and not au._unlimited(res):
                        res["current"] = max(0, res.get("current", 0) - 1)
                        got["spent"].append(f"{key} ({res['current']}/{res.get('current_max')} left)")
                elif kind == "daily":
                    u = char.setdefault("item_uses", {}).setdefault(key, {"current": 1, "max": 1, "recharge": "dawn"})
                    u["current"] = 0
                    got["spent"].append(f"{key}, until dawn")
                elif kind == "fx":
                    # an effect's one strike (Zephyr Strike): what's left stays on
                    _spell_goes_off(char, r)
                    got["spent"].append(f"{key}, once while it lasts")
                elif kind == "action":
                    card, bucket = item[1], item[2]
                    sub = {k.split(":", 1)[1]: v for k, v in answers.items()
                           if k.startswith(key + ":") and k != done}
                    res = au.use_action(char, bucket, card, "", sub)
                    if res.get("ask"):
                        ask = dict(res["ask"])
                        ask["key"] = f"{key}:{ask['key']}"
                        if not ask["title"].startswith(key):
                            ask["title"] = f"{key}: {ask['title']}"
                        return result(ask)
                    if not res.get("ok"):
                        got = {"spent": [], "notes": [res.get("toast") or f"{key}: can't add it now"], "ok": False}
                        break
                    if res.get("slot"):
                        slots.append(res["slot"])
                    toast = res.get("toast") or ""
                    m = re.search(r"\(([^()]*(?:spent|left)[^()]*)\)\s*$", toast)
                    got["spent"].append(f"{key} ({m.group(1)})" if m else key)
                    # what it does, said by its card ("the target makes a DC 15 CON save...")
                    said_it = toast[:m.start()].strip() if m else toast.strip()
                    if not r["dice"] and ":" in said_it:
                        got["said"] = said_it
            answers[done] = got
            refresh = True
        got = answers[done]
        if got["ok"] and r["dice"]:
            rolls.append({"dice": r["dice"] if r.get("apart") else twice(r["dice"]), "type": r["type"],
                          "source": key, "apart": bool(r.get("apart"))})
        if got["ok"] and not r["dice"]:
            # a maneuver or strike that adds dice to the hit (Trip Attack, Fire Strike): they're in the roll
            m = re.search(r"\badd (\d+d\d+(?:\s*\+\s*\d+)?)\s+(?:(acid|bludgeoning|cold|fire|force|lightning|"
                          r"necrotic|piercing|poison|psychic|radiant|slashing|thunder)\s+)?(?:damage\s+)?"
                          r"to the (?:damage|hit)", got.get("said", ""))
            if m:
                rolls.append({"dice": twice(m.group(1).replace(" ", "")),
                              "type": m.group(2) or row.get("damage_type", ""), "source": key, "apart": False})
        if got["ok"] and r.get("then"):
            notes.append(f"{key}: {r['then'][0].lower() + r['then'][1:]}")
        elif got["ok"] and not r["dice"] and (got.get("said") or r.get("cost")):
            notes.append(got.get("said") or f"{key}: {r['cost'][0].lower() + r['cost'][1:]}")
        spent.extend(got["spent"])
        notes.extend(got["notes"])
    # 4. what the hit (or the shot) itself set off -- once
    if "_hit:done" not in answers:
        lines = []
        for r in riders:
            if r.get("use", "on") != "on":
                continue
            if r["source"] == "Precise Strike" and r.get("spend") == "hit":
                # Squire of Solamnia: a use is spent only if the attack hits
                char["active_effects"] = [n for n in char.get("active_effects", []) if n != "Precise Strike"]
                refresh = True
                if hit:
                    res = au._own_resource(char, "Precise Strike")
                    if res is not None and not au._unlimited(res):
                        res["current"] = max(0, res.get("current", 0) - 1)
                        lines.append(f"Precise Strike: a use spent ({res['current']} left)")
                continue
            if r.get("spend") == "shot" or (hit and r.get("spend") == "hit"):
                # a spell this hit carried: it goes off
                _spell_goes_off(char, r)
                refresh = True
                text = r.get("then", "") if hit else r.get("miss", "")
                if text:
                    lines.append(f"{r['source']}: {text[0].lower() + text[1:]}")
            elif hit and r.get("spend") == "turn":
                # once a turn: done until New Turn
                char.setdefault("_turn_uses", []).append(r["source"])
                refresh = True
        answers["_hit:done"] = lines
    notes.extend(answers["_hit:done"])
    return result()
