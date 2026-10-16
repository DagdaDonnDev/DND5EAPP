"""Character choices, shared by both apps.

  * What a character still has to pick -- subclass, feats, race and tool
    choices, optional class features, DM rewards. Each generator takes the
    character and returns a list of choice dicts: id, label, pool, count,
    and what's already been chosen.
  * Cleaning up after a change -- a level down, a removed class, or a new
    race, subrace or background drops the picks that no longer apply,
    and everything that hangs off them.
"""


# ═══════════════════════════════════════════════════════════════════════════
# Lists the choices draw from
# ═══════════════════════════════════════════════════════════════════════════

ALL_SKILLS = [
    "Acrobatics","Animal Handling","Arcana","Athletics","Deception","History",
    "Insight","Intimidation","Investigation","Medicine","Nature","Perception",
    "Performance","Persuasion","Religion","Sleight of Hand","Stealth","Survival",
]

LANGUAGES = [
    "Aarakocra", "Abanasinian", "Abyssal", "Alzhedo", "Blink Dog", "Bothii", "Bullywug",
    "Celestial", "Chessentan", "Chondathan", "Common", "Daelkyr", "Damaran", "Dambrathan",
    "Deep Crow", "Deep Speech", "Draconic", "Druidic", "Dwarvish", "Elvish", "Ergot",
    "Giant", "Giant Eagle", "Giant Elk", "Giant Owl", "Gith", "Gnoll", "Gnomish", "Goblin",
    "Grell", "Grung", "Guran", "Halfling", "Halruaan", "Hook Horror", "Ice Toad", "Illuskan",
    "Infernal", "Istarian", "Ixitxachitl", "Kenderspeak", "Kharolian", "Khur", "Kothian",
    "Kraul", "Kruthik", "Leonin", "Loross", "Loxodon", "Marquesian", "Merfolk", "Midani",
    "Minotaur", "Modron", "Mulhorandi", "Naush", "Nerakese", "Netherese", "Nordmaarian",
    "Ogre", "Olman", "Orc", "Otyugh", "Primordial", "Qualith", "Quori", "Rashemi", "Riedran",
    "Roushoum", "Sahuagin", "Shaaran", "Shou", "Slaad", "Solamnic", "Sphinx", "Sylvan",
    "Thayan", "Thieves' Cant", "Thri-kreen", "Tlincalli", "Troglodyte", "Tuigan", "Turmic",
    "Uluik", "Umber Hulk", "Undercommon", "Untheric", "Vedalken", "Vegepygmy", "Waelan",
    "Winter Wolf", "Worg", "Yeti", "Yikaria", "Zemnian"
]

FIGHTING_STYLES = {
    "Fighter": ["Archery (+2 to ranged attack rolls)",
                "Blind Fighting (blindsight 10 ft, see through blindness/darkness in range)",
                "Defense (+1 AC while wearing armor)",
                "Dueling (+2 damage on one-handed melee weapon, no other weapon)",
                "Great Weapon Fighting (reroll 1s and 2s on damage dice, two-handed/versatile)",
                "Interception (reaction: reduce damage to a nearby ally by 1d10+PB)",
                "Protection (impose disadvantage on attack vs adjacent ally, requires shield)",
                "Superior Technique (learn 1 Battle Master maneuver + 1 superiority die)",
                "Thrown Weapon Fighting (draw as part of the attack; +2 damage on thrown hits)",
                "Two-Weapon Fighting (add ability modifier to off-hand attack)",
                "Unarmed Fighting (unarmed strikes deal 1d6+STR, or 1d8 with two free hands)"],
    "Paladin": ["Blessed Warrior (learn 2 cleric cantrips, CHA-based)",
                "Defense (+1 AC while wearing armor)",
                "Dueling (+2 damage on one-handed melee weapon, no other weapon)",
                "Great Weapon Fighting (reroll 1s and 2s on damage dice, two-handed/versatile)",
                "Interception (reaction: reduce damage to a nearby ally by 1d10+PB)",
                "Protection (impose disadvantage on attack vs adjacent ally, requires shield)"],
    "Ranger":  ["Archery (+2 to ranged attack rolls)",
                "Blind Fighting (blindsight 10 ft, see through blindness/darkness in range)",
                "Defense (+1 AC while wearing armor)",
                "Druidic Warrior (learn 2 druid cantrips, WIS-based)",
                "Dueling (+2 damage on one-handed melee weapon, no other weapon)",
                "Thrown Weapon Fighting (draw as part of the attack; +2 damage on thrown hits)",
                "Two-Weapon Fighting (add ability modifier to off-hand attack)"],
}

RACE_SKILL_CHOICES = {
    "Half-Elf":  {"count": 2, "pool": ALL_SKILLS, "label": "Skill Versatility (Half-Elf): choose 2 skills"},
    "Kenku":     {"count": 2, "pool": ["Acrobatics","Deception","Stealth","Sleight of Hand"],
                  "label": "Kenku Training: choose 2 of Acrobatics, Deception, Stealth, Sleight of Hand"},
    "Kenku (MPMM)": {"count": 2, "pool": ALL_SKILLS,
                      "label": "Kenku Recall (MPMM): choose 2 skills"},
    "Human (Variant)": {"count": 1, "pool": ALL_SKILLS, "label": "Human Variant: choose 1 skill proficiency"},
    "Centaur":   {"count": 1, "pool": ["Animal Handling","Medicine","Nature","Survival"],
                  "label": "Survivor (Centaur): choose 1 of Animal Handling, Medicine, Nature, Survival"},
    "Leonin":    {"count": 1, "pool": ["Intimidation","Athletics","Perception","Survival"],
                  "label": "Hunter's Instincts (Leonin): choose 1 of Intimidation, Athletics, Perception, Survival"},
    "Minotaur":  {"count": 1, "pool": ["Intimidation","Persuasion"],
                  "label": "Imposing Presence (Minotaur): choose 1 of Intimidation or Persuasion"},
    "Dhampir":   {"count": 2, "pool": ALL_SKILLS,
                  "label": "Ancestral Legacy (Dhampir): choose 2 skill proficiencies"},
    "Hexblood":  {"count": 2, "pool": ALL_SKILLS,
                  "label": "Ancestral Legacy (Hexblood): choose 2 skill proficiencies"},
    "Reborn":    {"count": 2, "pool": ALL_SKILLS,
                  "label": "Ancestral Legacy (Reborn): choose 2 skill proficiencies"},
}


# ═══════════════════════════════════════════════════════════════════════════
# Feat prerequisites
# ═══════════════════════════════════════════════════════════════════════════

def feat_prereq_met(char: dict, feat: dict) -> tuple[bool, str]:
    """Checks a feat's actual prerequisite against the character's real
    data. Returns (met, reason_if_not_met). Campaign-specific prereqs
    (Planescape/Dragonlance) are left unenforced — the app has no way to
    know which campaign a table is using, so those stay informational
    only."""
    prereq = feat.get("prereq", "")
    if not prereq:
        return True, ""
    if not char.get("optional_rules", {}).get("feat_prereqs", True):
        return True, ""
    from dnd_app.core.calculator import total_level, ability_score

    # Ability score minimums, e.g. "DEX 13+", "INT or WIS 13+"
    import re
    m = re.match(r"^((?:STR|DEX|CON|INT|WIS|CHA)(?:\s+or\s+(?:STR|DEX|CON|INT|WIS|CHA))*)\s+(\d+)\+$", prereq)
    if m:
        abs_needed = re.findall(r"STR|DEX|CON|INT|WIS|CHA", m.group(1))
        threshold = int(m.group(2))
        if any(ability_score(char, ab) >= threshold for ab in abs_needed):
            return True, ""
        return False, prereq

    # Armor/weapon proficiency -- the lists hold grant strings like
    # "Light, Medium, Shields" or "Simple weapons, martial weapons"
    from dnd_app.core.calculator import has_armor_proficiency
    for kind in ("medium", "heavy", "light"):
        if f"Prof. {kind} armor" in prereq:
            return (has_armor_proficiency(char, kind), prereq)
    if "Prof. martial weapon" in prereq:
        return (any("martial" in w.lower() for w in char.get("weapon_proficiencies", [])), prereq)

    # Spellcasting / Pact Magic
    if prereq in ("Spellcasting", "Spellcasting or Pact Magic"):
        has_spells = any(c.get("class") in
            ("Bard", "Cleric", "Druid", "Paladin", "Ranger", "Sorcerer", "Warlock", "Wizard", "Artificer")
            for c in char.get("classes", []))
        return (has_spells, prereq)

    # Level minimums (e.g. "4th level, X") — check the level part; the
    # named prior-feat part (if any) is checked separately below.
    lvl_m = re.match(r"^(\d+)(?:st|nd|rd|th) level", prereq)
    if lvl_m and total_level(char) < int(lvl_m.group(1)):
        return False, prereq

    # Previous-feat chains, e.g. "4th level, Scion of the Outer Planes
    # (lawful plane)" — check the base feat name is already known
    # (ignoring the specific sub-choice in parens, since the app doesn't
    # track that level of detail for these chain feats).
    for known_feat in ("Scion of the Outer Planes", "Strike of the Giants", "Squire of Solamnia",
                        "Initiate of High Sorcery", "Strixhaven Initiate"):
        if known_feat in prereq and known_feat != feat.get("name"):
            if known_feat not in char.get("feats", []):
                return False, prereq

    # Race-specific — includes subrace parenthetical matching, e.g.
    # "Elf (drow)", "Elf (high)", "Elf (wood)", "Gnome (deep)".
    race = (char.get("species") or char.get("race", "")).lower()
    subrace = char.get("subrace", "").lower()
    RACE_PREREQS = {
        "Halfling": ["halfling"],
        "Dragonborn": ["dragonborn"],
        "Elf (drow)": ["drow"],
        "Dwarf": ["dwarf"],
        "Elf or Half-Elf": ["elf", "half-elf"],
        "Gnome": ["gnome"],
        "Elf (high)": ["high elf", "elf"],  # "elf" alone with subrace check below
        "Tiefling": ["tiefling"],
        "Half-Orc": ["half-orc"],
        "Prodigy": None,  # handled specially below (multi-race OR)
        "Dwarf or a Small race": ["dwarf", "gnome", "halfling"],
        "Gnome (deep)": ["deep gnome", "gnome"],
        "Elf (wood)": ["wood elf", "elf"],
        "Elf": ["elf"],
    }
    if prereq == "Half-Elf, Half-Orc, or Human":
        ok = any(r in race for r in ("half-elf", "half-orc", "human"))
        return (ok, prereq)
    if prereq in RACE_PREREQS and RACE_PREREQS[prereq] is not None:
        needles = RACE_PREREQS[prereq]
        # Parenthetical subrace variants need the subrace to match too,
        # not just the base race (e.g. Drow specifically, not any elf).
        if "(" in prereq:
            sub_needle = prereq.split("(")[1].rstrip(")").lower()
            ok = sub_needle in subrace or sub_needle in race
        else:
            ok = any(n in race for n in needles)
        return (ok, prereq)

    # Anything else (campaign-specific, "No other dragonmark", etc.) —
    # left unenforced, same as before.
    return True, ""


# ═══════════════════════════════════════════════════════════════════════════
# What a character still has to pick
# ═══════════════════════════════════════════════════════════════════════════

# ── Subclass-conditional choices ─────────────────────────────────────────────
def _get_subclass_choices(char):
    """Extra choices that only appear for specific subclasses."""
    choices = []
    made = char.get("_choices",{})

    for c in char.get("classes",[]):
        cname = c.get("class","")
        clvl  = c.get("level",0)
        sub   = c.get("subclass","").lower()

        # Blood Hunter: Fighting Style (2nd level, core). Uses the
        # exact class-specific wording (e.g. Great Weapon Fighting
        # explicitly excludes rite damage dice, unlike other classes' version).
        if cname == "Blood Hunter" and clvl >= 2:
            key = "blood_hunter_fighting_style_2"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "class", "source_name": "Blood Hunter",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Archery – +2 to attack rolls with ranged weapons",
                             "Dueling – +2 damage with a one-handed melee weapon, wielding no other weapon",
                             "Great Weapon Fighting – reroll 1s and 2s on non-rite damage dice with a "
                             "two-handed/versatile melee weapon",
                             "Two-Weapon Fighting – add your ability modifier to the second attack's damage"],
                    "label": "Choose a Fighting Style (Blood Hunter Lv2)",
                    "already_chosen": already,
                })

        # Lunar Sorcery: Lunar Embodiment phase choice (1st level).
        # Re-chosen every long rest (handled via RestOptionsDialog) and,
        # from 6th level, via a bonus action for 1 sorcery point (Waxing
        # and Waning, handled as a combat action).
        if cname == "Sorcerer" and clvl >= 1 and "lunar" in sub:
            key = "lunar_phase"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "subclass", "source_name": "Lunar Embodiment",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Full Moon", "New Moon", "Crescent Moon"],
                    "label": "Choose your Lunar Embodiment phase (changeable on a long rest, "
                             "or as a bonus action for 1 sorcery point from 6th level)",
                    "already_chosen": already,
                })

        # Otherworldly Glamour (Ranger, Fey Wanderer, 3rd level): proficiency
        # in one of Deception, Performance or Persuasion (its WIS bonus to
        # Charisma checks is calculator.py's fey_wanderer_check_bonus).
        if cname == "Ranger" and clvl >= 3 and "fey wanderer" in sub:
            key = "fey_wanderer_skill_profs"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "subclass", "source_name": "Otherworldly Glamour",
                    "type": "skill_prof", "count": 1,
                    "pool": ["Deception", "Performance", "Persuasion"],
                    "label": "Otherworldly Glamour: choose Deception, Performance or Persuasion",
                    "already_chosen": already,
                })

        # Guidance of the Spirits (Bard, College of Spirits, 3rd level):
        # skill choice, swappable on long rest via RestOptionsDialog.
        if cname == "Bard" and clvl >= 3 and "spirits" in sub:
            key = "guidance_of_the_spirits_skill"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "subclass", "source_name": "Guidance of the Spirits",
                    "type": "skill_prof", "count": 1, "pool": ALL_SKILLS,
                    "label": "Choose a skill for Guidance of the Spirits (swappable on long rest)",
                    "already_chosen": already,
                })

        # Whispers of the Dead (Rogue, Phantom, 3rd level): skill-or-tool
        # choice, swappable on either rest type via RestOptionsDialog.
        if cname == "Rogue" and clvl >= 3 and "phantom" in sub:
            key = "whispers_of_the_dead_prof"
            already = made.get(key, [])
            if not already:
                from dnd_app.data.feature_ui_interactions import TOOLS as ALL_TOOLS
                choices.append({
                    "id": key, "source": "subclass", "source_name": "Whispers of the Dead",
                    "type": "skill_or_tool_prof", "count": 1, "pool": ALL_SKILLS + ALL_TOOLS,
                    "label": "Choose a skill or tool proficiency for Whispers of the Dead "
                             "(swappable on any rest)",
                    "already_chosen": already,
                })

        # Mystic Arcanum (Warlock, 11th/13th/15th/17th): choose one spell
        # of the corresponding level once each. Same kind of gap as
        # Eldritch Invocations and Pact Boon — genuinely missing.
        if cname == "Warlock":
            from dnd_app.data.spells import spells_for_class_at_level
            ARCANUM_LEVELS = {11: 6, 13: 7, 15: 8, 17: 9}
            for char_lvl, spell_lvl in ARCANUM_LEVELS.items():
                if clvl >= char_lvl:
                    key = f"mystic_arcanum_{spell_lvl}"
                    already = made.get(key, [])
                    if not already:
                        pool = [s["name"] for s in spells_for_class_at_level("Warlock", spell_lvl)]
                        choices.append({
                            "id": key,
                            "source": "class", "source_name": "Warlock",
                            "type": "magical_secrets", "count": 1,
                            "pool": pool,
                            "label": f"Mystic Arcanum: choose one {spell_lvl}th-level spell (Lv{char_lvl})",
                            "already_chosen": already,
                        })

        # Pact Boon (Warlock, 3rd level): single choice, same gap in kind
        # as Eldritch Invocations — no offering code existed at all.
        if cname == "Warlock" and clvl >= 3:
            key = "warlock_pact_boon"
            if key not in made:
                choices.append({
                    "id": key,
                    "source": "class", "source_name": "Warlock",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Pact of the Blade (summon a pact weapon)",
                             "Pact of the Chain (imp/quasit/pseudodragon/sprite familiar)",
                             "Pact of the Tome (Book of Shadows: 3 extra cantrips from any class, cast as rituals if the spell allows)",
                             "Pact of the Talisman (amulet: +1d4 to a failed ability check, uses = proficiency bonus per long rest)"],
                    "label": "Choose a Pact Boon",
                    "already_chosen": made.get(key, []),
                })

        # Pact of the Tome's 3 cantrips, from ANY class's spell list per the actual rule text.
        pact_choice = made.get("warlock_pact_boon", [])
        if cname == "Warlock" and clvl >= 3 and pact_choice and "tome" in pact_choice[0].lower():
            key = "pact_of_the_tome_cantrips"
            already = made.get(key, [])
            if len(already) < 3:
                from dnd_app.data.spells import ALL_SPELLS
                pool = sorted({s["name"] for s in ALL_SPELLS if s.get("level", 0) == 0})
                choices.append({
                    "id": key, "source": "class", "source_name": "Pact of the Tome",
                    "type": "magical_secrets", "count": 3,
                    "pool": pool,
                    "label": "Choose 3 cantrips from any class's spell list (Book of Shadows)",
                    "already_chosen": already,
                })

        # Book of Ancient Secrets (Eldritch Invocation, requires Pact of
        # the Tome): a separate invocation from Pact of the Tome itself,
        # granting 2 additional 1st-level ritual spells from any class's
        # list. Gated on the invocation actually being chosen, not just
        # the pact, since a Pact of the Tome warlock who hasn't taken
        # this specific invocation shouldn't get the ritual spells.
        known_invs_for_secrets = [i.split(" (")[0].strip() for i in char.get("eldritch_invocations", [])]
        if "Book of Ancient Secrets" in known_invs_for_secrets:
            key = "book_of_ancient_secrets_rituals"
            already = made.get(key, [])
            if len(already) < 2:
                from dnd_app.data.spells import ALL_SPELLS
                pool = sorted({s["name"] for s in ALL_SPELLS if s.get("level") == 1 and s.get("ritual")})
                choices.append({
                    "id": key, "source": "class", "source_name": "Book of Ancient Secrets",
                    "type": "magical_secrets", "count": 2,
                    "pool": pool,
                    "label": "Choose 2 1st-level ritual spells from any class's spell list (Book of Ancient Secrets)",
                    "already_chosen": already,
                })

        # Eldritch Invocations (Warlock, Core): a working chooser widget
        # and processing path already existed, but nothing ever offered
        # this choice — meaning no Warlock character could ever actually
        # select an invocation. Count scales 2/5/6/7/8/9/10 at Warlock
        # levels 2/5/7/10/12/15/18 (classes.py's own feature table).
        if cname == "Warlock" and clvl >= 2:
            inv_levels = [(2,2),(5,3),(7,4),(9,5),(12,6),(15,7),(18,8)]
            total_needed = max((n for lvl, n in inv_levels if clvl >= lvl), default=0)
            already = char.get("eldritch_invocations", [])
            remaining = max(0, total_needed - len(already))
            if remaining > 0:
                from dnd_app.data.classes import ELDRITCH_INVOCATIONS
                import re
                known_cantrips = char.get("cantrips_known", []) + char.get("spells_known", [])
                has_eldritch_blast = any("eldritch blast" in c.lower() for c in known_cantrips)
                pact_choice2 = made.get("warlock_pact_boon", [])
                pact_lower = pact_choice2[0].lower() if pact_choice2 else ""
                # This pool is filtered by the character's actual level
                # and pact boon, and excludes the 4 entries that are
                # Pact Boons, not invocations. "hex/curse feature" means
                # knowing the Hex spell, OR having a cursing Warlock
                # feature — Hexblade's Curse (an automatic level-1
                # feature of the Hexblade patron, so checking the
                # subclass name is reliable) or the Sign of Ill Omen
                # invocation.
                has_hex_curse = (any("hex" == s.lower() for s in known_cantrips + char.get("spells_known", []))
                                  or "hexblade" in sub.lower()
                                  or "Sign of Ill Omen" in [i.split(" (")[0].strip() for i in already])
                filtered_pool = []
                for inv in ELDRITCH_INVOCATIONS:
                    name_part = inv.split("–")[0].strip()
                    if name_part.startswith("Pact of the"):
                        continue
                    m = re.search(r'\(([^)]*)\)\s*$', name_part)
                    ok = True
                    if m:
                        req = m.group(1).lower()
                        lvl_m = re.match(r'(\d+)(st|nd|rd|th)', req)
                        if lvl_m and clvl < int(lvl_m.group(1)):
                            ok = False
                        if "pact of the blade" in req and "blade" not in pact_lower:
                            ok = False
                        if "pact of the chain" in req and "chain" not in pact_lower:
                            ok = False
                        if "pact of the tome" in req and "tome" not in pact_lower:
                            ok = False
                        if "pact of the talisman" in req and "talisman" not in pact_lower:
                            ok = False
                        if "eldritch blast" in req and not has_eldritch_blast:
                            ok = False
                        if "hex/curse" in req and not has_hex_curse:
                            ok = False
                    if ok:
                        filtered_pool.append(inv)
                choices.append({
                    "id": "eldritch_invocations",
                    "source": "class", "source_name": "Warlock",
                    "type": "invocation", "count": remaining,
                    "pool": filtered_pool,
                    "label": f"Choose {remaining} Eldritch Invocation(s)",
                    "already_chosen": already,
                })

        # Battle Master maneuvers
        if cname == "Fighter" and "battle master" in sub:
            maneuver_levels = [(3,3),(7,2),(10,2),(15,2),(18,2)]
            total_needed = sum(n for lvl, n in maneuver_levels if clvl >= lvl)
            already = char.get("battle_master_maneuvers", [])
            remaining = max(0, total_needed - len(already))
            if remaining > 0:
                choices.append({
                    "id": "fighter_maneuvers",
                    "source": "subclass", "source_name": "Battle Master",
                    "type": "maneuver", "count": remaining,
                    "pool": None,
                    "label": f"Choose {remaining} Battle Master maneuver(s)",
                    "already_chosen": already,
                })

        # Superior Technique fighting style (TCE): grants exactly 1
        # maneuver + 1 superiority die, independent of Battle Master
        # subclass — shares the same battle_master_maneuvers storage so a
        # Battle Master who also somehow had this wouldn't double-track,
        # though realistically this only ever fires for a non-Battle-
        # Master Fighter/Paladin/Ranger who picked this fighting style.
        if any("superior technique" in fs.lower() for fs in char.get("fighting_styles", [])):
            already_st = char.get("battle_master_maneuvers", [])
            # Superior Technique's own 1-maneuver allotment is tracked
            # against a fixed count of 1 rather than the Battle Master
            # progression table above, so it doesn't ask for more just
            # because a Battle Master Fighter later multiclassed in.
            if len(already_st) < 1 and "battle master" not in sub:
                choices.append({
                    "id": "fighter_maneuvers",
                    "source": "fighting_style", "source_name": "Superior Technique",
                    "type": "maneuver", "count": 1,
                    "pool": None,
                    "label": "Superior Technique: choose 1 maneuver",
                    "already_chosen": already_st,
                })

        # College of Lore Bard: 3rd-level Bonus Proficiencies — three skills
        # of your choice. Tracked as its own chooser since the subclass
        # feature list combines this with Cutting Words into one flavor
        # string that has no mechanism of its own to grant proficiencies.
        if cname == "Bard" and "lore" in sub and clvl >= 3:
            already = made.get("bard_lore_skill_profs", [])
            if len(already) < 3:
                choices.append({
                    "id": "bard_lore_skill_profs",
                    "source": "subclass", "source_name": "College of Lore",
                    "type": "skill_prof", "count": 3,
                    "pool": ALL_SKILLS,
                    "label": "Bonus Proficiencies (College of Lore): choose 3 skills",
                    "already_chosen": already,
                })

        # College of Swords: Fighting Style choice (Dueling or Two-Weapon
        # Fighting) — was never collected, so it never applied to the
        # actual weapon damage calculation despite that already
        # supporting these styles for Fighters/Rangers/Paladins.
        if cname == "Bard" and "swords" in sub and clvl >= 3:
            key = "bard_swords_fighting_style"
            if key not in made:
                choices.append({
                    "id": key,
                    "source": "subclass", "source_name": "College of Swords",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Dueling", "Two-Weapon Fighting"],
                    "label": "College of Swords: Choose a Fighting Style",
                    "already_chosen": made.get(key, []),
                })

        # Wild Magic Sorcerer / Barbarian: show surge table reference
        is_wild_magic = (
            (cname == "Sorcerer" or cname == "Barbarian") and
            "wild magic" in sub
        )
        if is_wild_magic and clvl >= 1:
            if "wild_magic_ack" not in made:
                choices.append({
                    "id": "wild_magic_ack",
                    "source": "subclass", "source_name": "Wild Magic",
                    "type": "info",
                    "count": 1,
                    "pool": None,
                    "label": "Wild Magic Surge: see the Features tab for the full d100 table",
                    "already_chosen": ["ack"],
                })

        # ── Ranger subclass choices ──────────────────────────────────────
        if cname == "Ranger":
            # Hunter: Colossus Slayer/Giant Killer/Horde Breaker at Lv3
            if "hunter" in sub and clvl >= 3:
                key = "hunter_prey_3"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",  # radio buttons work for single choice
                        "count": 1,
                        "pool": ["Colossus Slayer – once per turn, extra d8 damage to a damaged target",
                                 "Giant Killer – reaction attack on a Large+ creature within 5ft that hits OR misses you",
                                 "Horde Breaker – once per turn, attack a second creature within 5ft of your original target with the same weapon"],
                        "label": "Hunter: Choose Hunter's Prey (Lv3)",
                        "already_chosen": made.get(key, [])})
            # Hunter: Escape the Horde/Multiattack Defence/Steel Will at Lv7
            if "hunter" in sub and clvl >= 7:
                key = "hunter_defensive_7"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",
                        "count": 1,
                        "pool": ["Escape the Horde – opportunity attacks against you have disadvantage",
                                 "Multiattack Defense – +4 AC against further attacks from a creature that just hit you, rest of the turn",
                                 "Steel Will – advantage on saves against being frightened"],
                        "label": "Hunter: Choose Defensive Tactic (Lv7)",
                        "already_chosen": made.get(key, [])})
            # Hunter: Volley/Whirlwind Attack at Lv11
            if "hunter" in sub and clvl >= 11:
                key = "hunter_multiattack_11"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",
                        "count": 1,
                        "pool": ["Volley – ranged attack against any number of creatures within 10 ft of a point in range (ammo + separate roll per target)",
                                 "Whirlwind Attack – melee attack against any number of creatures within 5 ft (separate roll per target)"],
                        "label": "Hunter: Choose Multiattack (Lv11)",
                        "already_chosen": made.get(key, [])})
            # Hunter: Evasion/Stand Against the Tide/Uncanny Dodge at Lv15.
            if "hunter" in sub and clvl >= 15:
                key = "hunter_defense_15"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Hunter",
                        "type": "fighting_style",
                        "count": 1,
                        "pool": ["Evasion – successful DEX save vs an area effect takes no damage instead of half; failed save takes half instead of full",
                                 "Stand Against the Tide – reaction: a hostile creature that misses you with a melee attack must repeat the attack against another creature of your choice",
                                 "Uncanny Dodge – reaction: halve the damage of an attack that hits you"],
                        "label": "Hunter: Choose Superior Hunter's Defense (Lv15)",
                        "already_chosen": made.get(key, [])})
            # Gloom Stalker: Umbral Sight, Dread Ambusher etc. — info only
            if "gloom" in sub and clvl >= 3:
                key = "gloom_stalker_ack"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Gloom Stalker",
                        "type": "info", "count": 1, "pool": None,
                        "label": "Gloom Stalker features active: Dread Ambusher, Umbral Sight, Iron Mind",
                        "already_chosen": ["ack"]})
            # Gloom Stalker Iron Mind (7th level): only a real choice if the
            # character is already proficient in WIS saves from elsewhere
            # (an unusual multiclass edge case) — otherwise Iron Mind just
            # grants WIS automatically (handled in builder.py, not here).
            if "gloom" in sub and clvl >= 7 and char.get("saving_throws", {}).get("WIS"):
                key = "gloom_stalker_iron_mind"
                if key not in made:
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Iron Mind", "type": "fighting_style",
                        "count": 1, "pool": ["INT", "CHA"],
                        "label": "Already proficient in WIS saves — choose INT or CHA instead (Iron Mind)",
                        "already_chosen": made.get(key, [])})
            # Beastmaster: companion pick
            if ("beast" in sub or "beastmaster" in sub.replace(" ","")) and clvl >= 3:
                key = "beastmaster_companion"
                if not made.get(key):
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Beast Master",
                        "type": "info", "count": 1, "pool": None,
                        "label": "Choose a Medium or smaller beast as your companion (CR ≤ ¼)",
                        "already_chosen": ["ack"]})

        # Fighting Style
        if cname in ("Fighter","Paladin","Ranger"):
            min_lvl = 1 if cname == "Fighter" else 2
            if clvl >= min_lvl:
                key = f"{cname}_fighting_style"
                already = made.get(key,[])
                if not already:
                    pool = FIGHTING_STYLES.get(cname,[])
                    choices.append({
                        "id": key,
                        "source": "class", "source_name": cname,
                        "type": "fighting_style", "count": 1,
                        "pool": pool,
                        "label": f"Choose Fighting Style ({cname})",
                        "already_chosen": already,
                    })
                # Blessed Warrior (Paladin) and Druidic Warrior (Ranger)
                # each grant 2 cantrips from another class's list — a real
                # choice, not something with a sensible default, so it
                # only appears once that specific fighting style has
                # actually been picked.
                fs_pick = " ".join(already).lower()
                if "blessed warrior" in fs_pick or "druidic warrior" in fs_pick:
                    other_class = "Cleric" if "blessed warrior" in fs_pick else "Druid"
                    cantrip_key = f"{cname}_{other_class.lower()}_cantrips"
                    cantrip_already = made.get(cantrip_key, [])
                    if len(cantrip_already) < 2:
                        from dnd_app.data.spells import ALL_SPELLS
                        cantrips = sorted({s["name"] for s in ALL_SPELLS
                                           if s.get("level") == 0 and other_class in s.get("classes", [])})
                        choices.append({"id": cantrip_key, "source": "class",
                            "source_name": f"Blessed Warrior" if other_class=="Cleric" else "Druidic Warrior",
                            "type": "magical_secrets", "count": 2,
                            "pool": cantrips,
                            "label": f"Choose 2 {other_class} cantrips",
                            "already_chosen": cantrip_already})

        # ── Totem Warrior choices ─────────────────────────────────────────
        # Each tier (Totem Spirit at 3rd, Aspect of the Beast at 6th,
        # Totemic Attunement at 14th) has its own pool, since the same
        # animal grants a different, tier-specific benefit at each level —
        # Bear's Totem Spirit is a damage resistance, while Bear's Aspect
        # of the Beast is a carrying-capacity benefit, for example.
        if cname == "Barbarian" and "totem" in sub:
            TOTEM_SPIRIT_3 = [
                "Bear – while raging, resistance to all damage except psychic",
                "Eagle – while raging (and not wearing heavy armor), others have disadvantage on opportunity attacks against you, and you can Dash as a bonus action",
                "Elk – while raging (and not wearing heavy armor), your walking speed increases by 15 ft",
                "Tiger – while raging, add 10 ft to your long jump and 3 ft to your high jump",
                "Wolf – while raging, friends have advantage on melee attack rolls against any creature within 5 ft of you that's hostile to you",
            ]
            TOTEM_ASPECT_6 = [
                "Bear – carrying capacity (and max load/lift) doubled; advantage on STR checks to push/pull/lift/break objects",
                "Eagle – see up to 1 mile away with no difficulty; dim light doesn't impose disadvantage on Perception checks",
                "Elk – your travel pace (and up to 10 companions' within 60 ft) is doubled",
                "Tiger – proficiency in two of: Athletics, Acrobatics, Stealth, Survival",
                "Wolf – track creatures at a fast pace, and move stealthily at a normal pace",
            ]
            TOTEM_ATTUNEMENT_14 = [
                "Bear – while raging, hostile creatures within 5 ft have disadvantage on attacks against anyone but you (or another with this feature), unless immune to being frightened",
                "Eagle – while raging, flying speed equal to your walking speed (you fall if still aloft at end of turn with nothing else holding you up)",
                "Elk – while raging, bonus action during your move to barrel through a Large or smaller creature's space (STR save DC 8+STR+PB or be knocked prone + 1d12+STR bludgeoning)",
                "Tiger – while raging, after moving 20+ ft straight toward a Large or smaller target, bonus action for one extra melee attack against it",
                "Wolf – while raging, bonus action to knock a Large or smaller creature prone when you hit it with a melee weapon attack",
            ]
            totem_levels = [(3,"Choose Totem Spirit","totem_spirit_3", TOTEM_SPIRIT_3),
                           (6,"Choose Aspect of the Beast","totem_aspect_6", TOTEM_ASPECT_6),
                           (14,"Choose Totemic Attunement","totem_attune_14", TOTEM_ATTUNEMENT_14)]
            for lvl, label, key, pool in totem_levels:
                if clvl >= lvl and key not in made:
                    choices.append({"id": key, "source": "subclass",
                        "source_name": "Totem Warrior", "type": "fighting_style",
                        "count": 1, "pool": pool,
                        "label": f"{label} (Totem Warrior Lv{lvl})",
                        "already_chosen": made.get(key, [])})
            # Aspect of the Beast's Tiger option is itself a "choose 2 of 4
            # skills" pick (Athletics/Acrobatics/Stealth/Survival) — the
            # animal choice above just picks Tiger as flavor/mechanics
            # bundle, it doesn't grant any skill by itself. This nested
            # chooser only appears once Tiger has actually been selected,
            # and its id ends in "_skill_profs" so the existing generic
            # skill-proficiency-granting logic picks it up automatically.
            aspect_pick = made.get("totem_aspect_6", [])
            if clvl >= 6 and aspect_pick and "tiger" in " ".join(aspect_pick).lower():
                already_tiger_skills = made.get("totem_tiger_skill_profs", [])
                if len(already_tiger_skills) < 2:
                    choices.append({"id": "totem_tiger_skill_profs", "source": "subclass",
                        "source_name": "Aspect of the Beast (Tiger)", "type": "skill_prof",
                        "count": 2, "pool": ["Athletics","Acrobatics","Stealth","Survival"],
                        "label": "Choose 2 skills (Aspect of the Beast: Tiger)",
                        "already_chosen": already_tiger_skills})

        # ── Circle of the Land terrain choice (Druid) ─────────────────────────
        if cname == "Druid" and "land" in sub:
            if "land_terrain" not in made:
                terrains = ["Arctic","Coast","Desert","Forest","Grassland",
                            "Mountain","Swamp","Underdark"]
                choices.append({"id": "land_terrain", "source": "subclass",
                    "source_name": "Circle of the Land", "type": "fighting_style",
                    "count": 1, "pool": terrains,
                    "label": "Choose your Favored Terrain (Circle of the Land)",
                    "already_chosen": made.get("land_terrain", [])})

        # ── Way of the Four Elements: Elemental Disciplines (Monk) ────────────
        if cname == "Monk" and "four elements" in sub:
            # Elemental Attunement is automatic ("You know the Elemental
            # Attunement discipline AND one other...") so it isn't in this
            # pickable pool at all — only the "one other" (and later
            # additional) discipline choices count against the known total.
            DISCIPLINES = [
                "Breath of Winter (17th+) – spend 6 ki to cast Cone of Cold",
                "Clench of the North Wind (6th+) – spend 3 ki to cast Hold Person",
                "Eternal Mountain Defense (17th+) – spend 5 ki to cast Stoneskin on yourself",
                "Fangs of the Fire Snake – spend 1 ki: unarmed reach +10ft this turn, hits deal fire not bludgeoning; spend 1 more ki on a hit for +1d10 fire",
                "Fist of Four Thunders – spend 2 ki to cast Thunderwave",
                "Fist of Unbroken Air – spend 2 ki (+1d10 dmg per extra ki): target STR save or 3d10+ bludgeoning, pushed 20ft & prone (half dmg, no push/prone on save)",
                "Flames of the Phoenix (11th+) – spend 4 ki to cast Fireball",
                "Gong of the Summit (6th+) – spend 3 ki to cast Shatter",
                "Mist Stance (11th+) – spend 4 ki to cast Gaseous Form on yourself",
                "Ride the Wind (11th+) – spend 4 ki to cast Fly on yourself",
                "River of Hungry Flame (17th+) – spend 5 ki to cast Wall of Fire",
                "Rush of the Gale Spirits – spend 2 ki to cast Gust of Wind",
                "Shape the Flowing River – spend 1 ki: reshape/move up to a 30ft-cube area of ice or water within 120ft",
                "Sweeping Cinder Strike – spend 2 ki to cast Burning Hands",
                "Water Whip – spend 2 ki (+1d10 dmg per extra ki): target DEX save or 3d10+ bludgeoning, knocked prone or pulled 25ft (half dmg, no prone/pull on save)",
                "Wave of Rolling Earth (17th+) – spend 6 ki to cast Wall of Stone",
            ]
            # Real progression: "one other" at 3rd, "one additional" at 6th/
            # 11th/17th — i.e. 1/2/3/4 CHOSEN disciplines at those levels
            # (Elemental Attunement itself doesn't count toward this, since
            # it's free).
            KNOWN_BY_LEVEL = {3: 1, 6: 2, 11: 3, 17: 4}
            known = max((v for lvl, v in KNOWN_BY_LEVEL.items() if clvl >= lvl), default=0)
            already = char.get("_choices", {}).get("four_elements_disciplines", [])
            if clvl >= 3 and len(already) < known:
                choices.append({"id": "four_elements_disciplines", "source": "subclass",
                    "source_name": "Four Elements", "type": "metamagic",
                    "count": known, "pool": DISCIPLINES,
                    "label": f"Choose {known} Elemental Disciplines",
                    "already_chosen": already})

        # ── Bard: Magical Secrets ──────────────────────────────────────────────
        if cname == "Bard":
            MS_LEVELS = {10: 2, 14: 4, 18: 6}
            for ms_lvl, total_count in sorted(MS_LEVELS.items()):
                if clvl >= ms_lvl:
                    key = f"bard_magical_secrets_{ms_lvl}"
                    already = char.get("_choices", {}).get(key, [])
                    batch_count = 2  # each threshold grants 2 more
                    if len(already) < batch_count:
                        choices.append({"id": key, "source": "class",
                            "source_name": "Bard", "type": "magical_secrets",
                            "count": batch_count, "pool": None,
                            "label": f"Magical Secrets: choose {batch_count} spells from any class (Lv{ms_lvl})",
                            "already_chosen": already})

        # ── College of Lore: Bonus Magical Secrets (Lv6) ──────────────────────
        if cname == "Bard" and "lore" in sub and clvl >= 6:
            key = "bard_lore_secrets_6"
            already = made.get(key, [])
            if not already:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "College of Lore", "type": "magical_secrets",
                    "count": 2, "pool": None,
                    "label": "Bonus Magical Secrets: choose 2 spells from any class (Lore Bard Lv6)",
                    "already_chosen": already})

        # ── Eldritch Knight: spells known (uses get_choices_needed for spell slots) ──
        # (handled by existing spell chooser logic)

        # ── Cleric Knowledge Domain: Blessings of Knowledge (Lv1) ───────────────
        # Real text grants proficiency AND doubled proficiency bonus (i.e.
        # expertise) in 2 of 4 listed skills — using the "expertise" chooser
        # type rather than plain "skill_prof" so it grants the doubled
        # bonus, not just ordinary proficiency.
        if cname == "Cleric" and "knowledge" in sub and clvl >= 1:
            already = made.get("knowledge_domain_expertise", [])
            if len(already) < 2:
                choices.append({"id": "knowledge_domain_expertise", "source": "subclass",
                    "source_name": "Knowledge Domain", "type": "expertise",
                    "count": 2, "pool": ["Arcana","History","Nature","Religion"],
                    "label": "Blessings of Knowledge: choose 2 skills (expertise)",
                    "already_chosen": already})
            already_lang = made.get("knowledge_domain_languages", [])
            if len(already_lang) < 2:
                choices.append({"id": "knowledge_domain_languages", "source": "subclass",
                    "source_name": "Knowledge Domain", "type": "skill_prof",
                    "count": 2, "pool": LANGUAGES,
                    "label": "Blessings of Knowledge: choose 2 languages",
                    "already_chosen": already_lang})

        # ── Cleric Death Domain: Reaper bonus necromancy cantrip (Lv1) ──────────
        # Real text: "you learn one necromancy cantrip of your choice from
        # any class's spell list" — doesn't count against cantrips known,
        # handled the same way as other domain bonus spells (get_bonus_spells()
        # reads this choice back in so it survives rebuild()).
        if cname == "Cleric" and "death domain" in sub.lower() and clvl >= 1:
            already = made.get("death_domain_reaper_cantrip", [])
            if not already:
                from dnd_app.data.spells import ALL_SPELLS
                necro_cantrips = [s["name"] for s in ALL_SPELLS
                                   if s["level"] == 0 and s.get("school", "").lower() == "necromancy"]
                choices.append({"id": "death_domain_reaper_cantrip", "source": "subclass",
                    "source_name": "Death Domain", "type": "magical_secrets",
                    "count": 1, "pool": necro_cantrips,
                    "label": "Reaper: choose 1 necromancy cantrip from any class's spell list",
                    "already_chosen": already})

        # ── Cleric Strength Domain (Amonkhet): Acolyte of Strength (Lv1) ────────
        if cname == "Cleric" and "strength domain" in sub.lower() and clvl >= 1:
            already = made.get("acolyte_of_strength_skill_profs", [])
            if not already:
                choices.append({"id": "acolyte_of_strength_skill_profs", "source": "subclass",
                    "source_name": "Acolyte of Strength", "type": "skill_prof",
                    "count": 1, "pool": ["Animal Handling","Athletics","Nature","Survival"],
                    "label": "Acolyte of Strength: choose 1 skill",
                    "already_chosen": already})

        # ── Sorcerer: Metamagic choices ────────────────────────────────────────
        if cname == "Sorcerer" and clvl >= 3:
            METAMAGIC_OPTIONS = [
                "Careful Spell – spend 1 SP: chosen creatures auto-succeed your spell saves",
                "Distant Spell – spend 1 SP: double range, or touch becomes 30 ft",
                "Empowered Spell – spend 1 SP: reroll up to CHA mod damage dice (once per spell)",
                "Extended Spell – spend 1 SP: double duration (max 24h)",
                "Heightened Spell – spend 3 SP: one target has disadv on first save",
                "Quickened Spell – spend 2 SP: change cast time from 1 action to bonus action",
                "Seeking Spell – spend 2 SP: if a spell attack roll misses, reroll it (must use new roll)",
                "Subtle Spell – spend 1 SP: cast without V or S components",
                "Transmuted Spell – spend 1 SP: change damage type to acid/cold/fire/lightning/poison/thunder",
                "Twinned Spell – spend SP = spell level (1 SP if a cantrip): target a second creature",
            ]
            # PHB 2014 progression: 2 at 3rd level, 3 at 10th, 4 at 17th.
            # (The old "+1 every 4 levels" formula was mathematically wrong —
            # it gave 5 options at 15th level and 6 by 19th, both too many.)
            count = 4 if clvl >= 17 else 3 if clvl >= 10 else 2
            already = char.get("_choices", {}).get("sorcerer_metamagic", [])
            if len(already) < count:
                choices.append({"id": "sorcerer_metamagic", "source": "class",
                    "source_name": "Sorcerer", "type": "metamagic",
                    "count": count, "pool": METAMAGIC_OPTIONS,
                    "label": f"Choose {count} Metamagic Options",
                    "already_chosen": already})

        # ── Artificer Armorer: Arcane Armor model (Lv3) ─────────────────────────
        if cname == "Artificer" and "armorer" in sub and clvl >= 3:
            key = "armorer_model_3"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Armorer", "type": "fighting_style", "count": 1,
                    "pool": ["Guardian – Thunder Gauntlets (1d8 thunder, target has disadvantage attacking others); bonus action: temp HP = artificer level, PB times/long rest",
                             "Infiltrator – Lightning Launcher (ranged 90/300ft, 1d6 lightning + extra 1d6 once/turn); +5ft speed; advantage on Stealth checks"],
                    "label": "Choose Arcane Armor Model (Armorer Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Barbarian Path of the Beast: Form of the Beast (Lv3) ────────────────
        if cname == "Barbarian" and "beast" in sub and clvl >= 3:
            key = "beast_form_3"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Path of the Beast", "type": "fighting_style", "count": 1,
                    "pool": ["Bite – reach 5ft, 1d8+STR piercing; once/turn when you hit below half HP, heal PB",
                             "Claws – reach 5ft, 1d6+STR slashing; once/turn, make one extra claw attack as part of the same Attack action",
                             "Tail – reach 10ft, 1d8+STR piercing; reaction: roll a d8 and add it to your AC against one attack"],
                    "label": "Choose Form of the Beast (Path of the Beast Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Barbarian Storm Herald: Storm Aura (Lv3) ────────────────────────────
        if cname == "Barbarian" and "storm herald" in sub and clvl >= 3:
            key = "storm_aura_3"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Storm Herald", "type": "fighting_style", "count": 1,
                    "pool": ["Desert – on activation, all other creatures in your aura take 2 fire damage (scales with level)",
                             "Sea – choose one creature in your aura: DEX save or take 1d6 lightning damage, half on success (scales with level)",
                             "Tundra – choose one creature in your aura to gain 2 temporary HP (scales with level)"],
                    "label": "Choose Storm Aura (Storm Herald Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Fighter Arcane Archer: Arcane Shot options (Lv3, 2 initially) ───────
        if cname == "Fighter" and "arcane archer" in sub and clvl >= 3:
            ARCANE_SHOT_OPTIONS = [
                "Banishing Arrow – CHA save or banished (speed 0, incapacitated) until end of its next turn; +2d6 force at 18th level",
                "Beguiling Arrow – +2d6 psychic; WIS save or charmed by an ally you choose until start of your next turn",
                "Bursting Arrow – +2d6 force to the target AND every creature within 10ft of it",
                "Enfeebling Arrow – +2d6 necrotic; CON save or its weapon damage is halved until start of your next turn",
                "Grasping Arrow – +2d6 poison; speed reduced 10ft, +2d6 slashing the first time it moves each turn (STR check vs your save DC to clear)",
                "Piercing Arrow – no attack roll: 30ft line, 1ft wide, ignores cover; DEX save or full damage +1d6 piercing (half on save)",
                "Seeking Arrow – no attack roll: curving shot ignores 3/4 and half cover; DEX save or full damage +1d6 force and you learn its location (half, no location on save)",
                "Shadow Arrow – +2d6 psychic; WIS save or blinded beyond 5ft until start of your next turn",
            ]
            shots_known = {3:2, 7:3, 10:4, 15:5, 18:6}
            total = max(v for lvl2,v in shots_known.items() if clvl >= lvl2)
            already = made.get("arcane_shot_options", [])
            if len(already) < total:
                choices.append({"id": "arcane_shot_options", "source": "subclass",
                    "source_name": "Arcane Archer", "type": "metamagic",
                    "count": total, "pool": ARCANE_SHOT_OPTIONS,
                    "label": f"Choose {total} Arcane Shot option(s)",
                    "already_chosen": already})

        # ── Fighter Rune Knight: Runes (Lv3, 2 initially) ───────────────────────
        if cname == "Fighter" and "rune knight" in sub and clvl >= 3:
            RUNE_OPTIONS = [
                "Cloud Rune – advantage on Sleight of Hand & Deception; reaction: redirect an attack that hit someone within 30ft to a different creature",
                "Fire Rune – double proficiency bonus on tool checks; on a hit, +2d6 fire and STR save or restrained + 2d6 fire/turn until it saves",
                "Frost Rune – advantage on Animal Handling & Intimidation; bonus action: +2 to STR checks/saves for 10 min",
                "Hill Rune – advantage on saves vs poison + resistance to poison damage; bonus action: resistance to bludgeoning/piercing/slashing for 1 min",
                "Stone Rune – advantage on Insight, darkvision 120ft; reaction: WIS save or charmed (speed 0, incapacitated) for 1 min",
                "Storm Rune (7th+) – advantage on Arcana, can't be surprised; bonus action 1 min: reaction to impose advantage or disadvantage on a roll within 60ft",
            ]
            runes_known = {3:2, 7:3, 10:4, 15:5}
            total = max(v for lvl2,v in runes_known.items() if clvl >= lvl2)
            already = made.get("rune_knight_runes", [])
            if len(already) < total:
                choices.append({"id": "rune_knight_runes", "source": "subclass",
                    "source_name": "Rune Knight", "type": "metamagic",
                    "count": total, "pool": RUNE_OPTIONS,
                    "label": f"Choose {total} Rune(s)",
                    "already_chosen": already})

        # ── Monk Way of the Ascendant Dragon: Draconic Strike is per-attack ─────
        # Not a permanent pick — Draconic Strike lets you change your unarmed
        # strike's damage type to acid/cold/fire/lightning/poison freely each
        # time you hit, so this is an acknowledgment rather than a chooser
        # (a previous version incorrectly forced a one-time permanent choice).
        if cname == "Monk" and "ascendant dragon" in sub and clvl >= 3:
            key = "ascendant_dragon_ack"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Way of the Ascendant Dragon", "type": "info",
                    "count": 1, "pool": None,
                    "label": "Draconic Strike: freely choose acid/cold/fire/lightning/poison each time you hit with an unarmed strike",
                    "already_chosen": ["ack"]})

        # ── Monk Way of the Kensei: Kensei weapons (Lv3, 2 initially) ───────────
        if cname == "Monk" and "kensei" in sub and clvl >= 3:
            # any simple or martial weapon without heavy or special, or a longbow
            from dnd_app.core.weapons import kensei_weapon_options
            KENSEI_WEAPON_OPTIONS = kensei_weapon_options()
            weapons_known = {3:2, 6:3, 11:4, 17:5}
            total = max(v for lvl2,v in weapons_known.items() if clvl >= lvl2)
            already = made.get("kensei_weapons", [])
            if len(already) < total:
                choices.append({"id": "kensei_weapons", "source": "subclass",
                    "source_name": "Way of the Kensei", "type": "metamagic",
                    "count": total, "pool": KENSEI_WEAPON_OPTIONS,
                    "label": f"Choose {total} Kensei weapons (at 3rd level, one melee and one ranged)",
                    "already_chosen": already})

        # ── Sorcerer Divine Soul: Affinity (Lv1) ────────────────────────────────
        # Divine Magic itself (choosing sorcerer cantrips/spells from the
        # Cleric list too) is an ongoing privilege applied whenever spells
        # are picked, not a one-time chooser. The actual permanent 1st-level
        # pick is an affinity, each granting one specific fixed bonus spell.
        if cname == "Sorcerer" and "divine soul" in sub and clvl >= 1:
            key = "divine_soul_affinity"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Divine Soul", "type": "fighting_style", "count": 1,
                    "pool": ["Good – bonus spell: Cure Wounds", "Evil – bonus spell: Inflict Wounds",
                             "Law – bonus spell: Bless", "Chaos – bonus spell: Bane",
                             "Neutrality – bonus spell: Protection from Evil and Good"],
                    "label": "Choose Divine Magic Affinity (Divine Soul Lv1)",
                    "already_chosen": made.get(key, [])})

        # ── Wizard: Spell Mastery (18th) and Signature Spells (20th) ────────────
        # Both had the same shape of gap as Warlock's Mystic Arcanum — never
        # actually offered despite being real, high-level Wizard features.
        # Filtered to the Wizard's own known spells (spells_known) at the
        # correct level, since the real rule specifies spells "from your
        # spellbook," not any spell of that level from the full class list.
        if cname == "Wizard" and clvl >= 18:
            from dnd_app.data.spells import SPELL_DICT
            known_names = char.get("spells_known", [])
            for spell_lvl, key in ((1, "wizard_spell_mastery_1"), (2, "wizard_spell_mastery_2")):
                already = made.get(key, [])
                if already:
                    continue
                pool = [n for n in known_names
                        if SPELL_DICT.get(n, {}).get("level") == spell_lvl]
                if pool:
                    choices.append({
                        "id": key,
                        "source": "class", "source_name": "Wizard",
                        "type": "magical_secrets", "count": 1,
                        "pool": pool,
                        "label": f"Spell Mastery: choose 1 known {spell_lvl}st-level spell to cast at will"
                                 if spell_lvl == 1 else
                                 f"Spell Mastery: choose 1 known {spell_lvl}nd-level spell to cast at will",
                        "already_chosen": already,
                    })
        if cname == "Wizard" and clvl >= 20:
            from dnd_app.data.spells import SPELL_DICT
            known_names = char.get("spells_known", [])
            key = "wizard_signature_spells"
            already = made.get(key, [])
            pool = [n for n in known_names if SPELL_DICT.get(n, {}).get("level") == 3]
            if len(already) < 2 and pool:
                choices.append({
                    "id": key,
                    "source": "class", "source_name": "Wizard",
                    "type": "magical_secrets", "count": 2 - len(already),
                    "pool": pool,
                    "label": f"Signature Spells: choose {2 - len(already)} known 3rd-level spell(s)",
                    "already_chosen": already,
                })

        # ── Sorcerer Draconic Bloodline: Dragon Ancestor (Lv1) ──────────────────
        if cname == "Sorcerer" and "draconic" in sub and clvl >= 1:
            key = "sorcerer_dragon_ancestor"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Draconic Bloodline", "type": "fighting_style", "count": 1,
                    "pool": ["Black – acid", "Blue – lightning", "Brass – fire", "Bronze – lightning",
                             "Copper – acid", "Gold – fire", "Green – poison", "Red – fire",
                             "Silver – cold", "White – cold"],
                    "label": "Choose Dragon Ancestor (Draconic Bloodline Lv1)",
                    "already_chosen": made.get(key, [])})

        # ── Warlock The Genie: Genie's Vessel kind (Lv1) ────────────────────────
        if cname == "Warlock" and "genie" in sub and clvl >= 1:
            key = "genie_kind"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "The Genie", "type": "fighting_style", "count": 1,
                    "pool": ["Dao – bonus attack damage and resistance are bludgeoning",
                             "Djinni – bonus attack damage and resistance are thunder",
                             "Efreeti – bonus attack damage and resistance are fire",
                             "Marid – bonus attack damage and resistance are cold"],
                    "label": "Choose Genie kind (The Genie Lv1)",
                    "already_chosen": made.get(key, [])})

        # ── Ranger Drakewarden: Draconic Essence (Lv3) ──────────────────────────
        # Chosen each time the drake is summoned per the real rules, but
        # tracked as a single persistent choice here for simplicity — it
        # determines both the drake's Infused Strikes damage type and (at
        # 7th level, Bond of Fang and Scale) the character's own resistance.
        if cname == "Ranger" and "drakewarden" in sub and clvl >= 3:
            key = "drake_essence"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "Drakewarden", "type": "fighting_style", "count": 1,
                    "pool": ["Acid", "Cold", "Fire", "Lightning", "Poison"],
                    "label": "Choose Draconic Essence (Drake Companion Lv3)",
                    "already_chosen": made.get(key, [])})

        # ── Warlock The Fiend: Fiendish Resilience (Lv10) ───────────────────────
        # Real text: choose any damage type each time you finish a short or
        # long rest, gain resistance to it (magic/silver weapons bypass).
        # Simplified to a persistent choice, re-pickable via the Choices tab.
        if cname == "Warlock" and "fiend" in sub and clvl >= 10:
            key = "fiendish_resilience"
            if key not in made:
                choices.append({"id": key, "source": "subclass",
                    "source_name": "The Fiend", "type": "fighting_style", "count": 1,
                    "pool": ["Acid","Bludgeoning","Cold","Fire","Force","Lightning",
                             "Necrotic","Piercing","Poison","Psychic","Radiant","Slashing","Thunder"],
                    "label": "Choose Fiendish Resilience damage type (re-choosable each rest)",
                    "already_chosen": made.get(key, [])})

    return choices


def _get_feat_choices(char):
    """Player-chosen proficiency grants from feats (e.g. Skilled's 3
    skill/tool picks). Detects a feat was taken by scanning every
    _choices value for a "feat:Name" entry, the
    same way it's stored when picked via the ASI-or-feat chooser.
    Weapon Master, Skill Expert, and Prodigy need the same kind of
    treatment but are more complex (weapon pools, an additional
    expertise-in-an-existing-skill sub-choice) and aren't covered yet —
    flagged rather than rushed."""
    choices = []
    made = char.get("_choices", {})
    all_feats = set(char.get("feats", []))

    if "Skilled" in all_feats:
        key = "feat_skilled_skill_or_tool_profs"
        already = made.get(key, [])
        if len(already) < 3:
            from dnd_app.data.items import ALL_TOOLS
            choices.append({
                "id": key, "source": "feat", "source_name": "Skilled",
                "type": "skill_or_tool_prof", "count": 3,
                "pool": ALL_SKILLS + ALL_TOOLS,
                "label": "Choose any combination of 3 skills or tools",
                "already_chosen": already,
            })
    if "Woodwise" in all_feats:
        key = "feat_woodwise_skill_prof"
        already = made.get(key, [])
        if len(already) < 1:
            choices.append({
                "id": key, "source": "feat", "source_name": "Woodwise",
                "type": "skill_prof", "count": 1,
                "pool": ["Survival", "Nature"],
                "label": "Choose 1 of Survival or Nature",
                "already_chosen": already,
            })
    if "Forest Sage" in all_feats:
        key = "feat_forest_sage_spells"
        already = made.get(key, [])
        if len(already) < 2:
            # Same max-castable-level formula used in sheet.py/wizard.py's
            # _max_castable_spell_level(), replicated here since this is a
            # standalone function operating on the char parameter directly.
            max_lvl = 0
            for i, count in enumerate(char.get("spell_slots_max", [])):
                if count > 0:
                    max_lvl = i + 1
            if char.get("pact_slots_max", 0) > 0:
                max_lvl = max(max_lvl, char.get("pact_slot_level", 0))
            from dnd_app.data.spells import ALL_SPELLS
            pool = sorted({s["name"] for s in ALL_SPELLS
                           if 1 <= s.get("level", 0) <= max_lvl
                           and ("Druid" in s.get("classes", []) or "Wizard" in s.get("classes", []))})
            choices.append({
                "id": key, "source": "feat", "source_name": "Forest Sage",
                "type": "magical_secrets", "count": 2,
                "pool": pool,
                "label": f"Choose 2 spells (level 1-{max_lvl}) from the Druid or Wizard list",
                "already_chosen": already,
            })
    if "Weapon Master" in all_feats:
        key = "feat_weapon_master_weapons"
        already = made.get(key, [])
        if len(already) < 4:
            from dnd_app.data.items import SIMPLE_MELEE, SIMPLE_RANGED, MARTIAL_MELEE, MARTIAL_RANGED
            weapon_pool = [w[0] for w in (SIMPLE_MELEE + SIMPLE_RANGED + MARTIAL_MELEE + MARTIAL_RANGED)]
            choices.append({
                "id": key, "source": "feat", "source_name": "Weapon Master",
                "type": "magical_secrets", "count": 4,
                "pool": weapon_pool,
                "label": "Choose 4 weapons (simple or martial) to gain proficiency with",
                "already_chosen": already,
            })
    if "Artificer Initiate" in all_feats:
        key = "feat_artificer_initiate_tool_profs"
        already = made.get(key, [])
        if len(already) < 1:
            from dnd_app.data.items import ARTISAN_TOOLS
            choices.append({
                "id": key, "source": "feat", "source_name": "Artificer Initiate",
                "type": "tool_prof", "count": 1,
                "pool": ARTISAN_TOOLS,
                "label": "Choose 1 type of artisan's tools",
                "already_chosen": already,
            })

    if "Scion of the Outer Planes" in all_feats:
        key = "feat_scion_plane_type"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "feat", "source_name": "Scion of the Outer Planes",
                "type": "fighting_style", "count": 1,
                "pool": ["Chaotic Outer Plane", "Evil Outer Plane", "Good Outer Plane",
                         "Lawful Outer Plane", "The Outlands"],
                "label": "Choose your plane type (determines your resistance and cantrip)",
                "already_chosen": already,
            })

    if "Fighting Initiate" in all_feats:
        key = "feat_initiate_fighting_style"
        already = made.get(key, [])
        if not already:
            known_styles_lower = {fs.split(" (")[0].strip().lower()
                                   for fs in char.get("fighting_styles", [])}
            pool = [fs for fs in FIGHTING_STYLES["Fighter"]
                    if fs.split(" (")[0].strip().lower() not in known_styles_lower]
            if pool:
                choices.append({
                    "id": key, "source": "feat", "source_name": "Fighting Initiate",
                    "type": "fighting_style", "count": 1,
                    "pool": pool,
                    "label": "Choose 1 Fighting Style (must differ from any you already know)",
                    "already_chosen": already,
                })

    if "Ritual Caster" in all_feats:
        key = "feat_ritual_caster_spells"
        already = made.get(key, [])
        if len(already) < 2:
            from dnd_app.data.spells import ALL_SPELLS
            pool = sorted({s["name"] for s in ALL_SPELLS if s.get("level") == 1 and s.get("ritual")
                          and any(cn in s.get("classes", []) for cn in ("Cleric", "Druid", "Wizard"))})
            choices.append({
                "id": key, "source": "feat", "source_name": "Ritual Caster",
                "type": "magical_secrets", "count": 2,
                "pool": pool,
                "label": "Choose 2 1st-level ritual spells (Cleric/Druid/Wizard list) — always prepared",
                "already_chosen": already,
            })

    # Feats that give a spell of your choice (plus a fixed one -- see
    # spells.py FEAT_FIXED_SPELLS). The picked spell joins your spell list
    # and, like the fixed one, can be cast once per long rest for free.
    from dnd_app.data.spells import ALL_SPELLS as _ALL_SP
    for feat, key, schools, label in [
        ("Fey Touched", "feat_fey_touched_spell", ("Divination", "Enchantment"),
         "Choose a 1st-level divination or enchantment spell (with Misty Step: each once per long rest, free)"),
        ("Shadow Touched", "feat_shadow_touched_spell", ("Illusion", "Necromancy"),
         "Choose a 1st-level illusion or necromancy spell (with Invisibility: each once per long rest, free)"),
    ]:
        if feat in all_feats:
            already = made.get(key, [])
            if len(already) < 1:
                choices.append({
                    "id": key, "source": "feat", "source_name": feat,
                    "type": "magical_secrets", "count": 1,
                    "pool": sorted(sp["name"] for sp in _ALL_SP
                                   if sp.get("level") == 1 and sp.get("school") in schools),
                    "label": label, "already_chosen": already,
                })
    if "Magic Initiate" in all_feats:
        # the class comes from the feat's name when a background gave it
        # ("Magic Initiate (Cleric)"); otherwise any of the six lists
        mi_cls = ""
        for full in [char.get("origin_feat") or ""] + list(all_feats):
            if full.startswith("Magic Initiate (") and full.endswith(")"):
                mi_cls = full[len("Magic Initiate ("):-1]
        mi_classes = [mi_cls] if mi_cls else ["Bard", "Cleric", "Druid", "Sorcerer", "Warlock", "Wizard"]
        for key, lvl, count, what in [("feat_magic_initiate_cantrips", 0, 2, "2 cantrips"),
                                      ("feat_magic_initiate_spell", 1, 1, "1 1st-level spell (free once per long rest)")]:
            already = made.get(key, [])
            if len(already) < count:
                choices.append({
                    "id": key, "source": "feat", "source_name": "Magic Initiate",
                    "type": "magical_secrets", "count": count,
                    "pool": sorted(sp["name"] for sp in _ALL_SP if sp.get("level") == lvl
                                   and any(c in sp.get("classes", []) for c in mi_classes)),
                    "label": f"Choose {what} from the {' / '.join(mi_classes)} list",
                    "already_chosen": already,
                })

    if "Linguist" in all_feats:
        key = "feat_linguist_languages"
        already = made.get(key, [])
        if len(already) < 3:
            choices.append({
                "id": key, "source": "feat", "source_name": "Linguist",
                "type": "language", "count": 3,
                "label": "Choose 3 languages",
                "already_chosen": already,
            })

    if "Prodigy" in all_feats:
        from dnd_app.data.items import ALL_TOOLS
        key_skill = "feat_prodigy_skill_profs"
        already_skill = made.get(key_skill, [])
        if len(already_skill) < 1:
            choices.append({
                "id": key_skill, "source": "feat", "source_name": "Prodigy",
                "type": "skill_prof", "count": 1,
                "pool": ALL_SKILLS,
                "label": "Choose 1 skill to gain proficiency in",
                "already_chosen": already_skill,
            })
        key_tool = "feat_prodigy_tool_profs"
        already_tool = made.get(key_tool, [])
        if len(already_tool) < 1:
            choices.append({
                "id": key_tool, "source": "feat", "source_name": "Prodigy",
                "type": "tool_prof", "count": 1,
                "pool": ALL_TOOLS,
                "label": "Choose 1 tool to gain proficiency in",
                "already_chosen": already_tool,
            })
        key_lang = "feat_prodigy_language"
        already_lang = made.get(key_lang, [])
        if len(already_lang) < 1:
            choices.append({
                "id": key_lang, "source": "feat", "source_name": "Prodigy",
                "type": "language", "count": 1,
                "label": "Choose 1 language",
                "already_chosen": already_lang,
            })
        key_exp = "feat_prodigy_expertise"
        already_exp = made.get(key_exp, [])
        if len(already_exp) < 1:
            proficient_skills = [s for s, lvl in char.get("skills", {}).items() if lvl >= 2]
            if proficient_skills:
                choices.append({
                    "id": key_exp, "source": "feat", "source_name": "Prodigy",
                    "type": "expertise", "count": 1,
                    "pool": sorted(proficient_skills),
                    "label": "Choose 1 already-proficient skill to gain expertise in",
                    "already_chosen": already_exp,
                })

    if "Skill Expert" in all_feats:
        key_new = "feat_skill_expert_skill_profs"
        already_new = made.get(key_new, [])
        if len(already_new) < 1:
            choices.append({
                "id": key_new, "source": "feat", "source_name": "Skill Expert",
                "type": "skill_prof", "count": 1,
                "pool": ALL_SKILLS,
                "label": "Choose 1 skill to gain proficiency in",
                "already_chosen": already_new,
            })
        key_exp = "feat_skill_expert_expertise"
        already_exp = made.get(key_exp, [])
        if len(already_exp) < 1:
            proficient_skills = [s for s, lvl in char.get("skills", {}).items() if lvl >= 2]
            if proficient_skills:
                choices.append({
                    "id": key_exp, "source": "feat", "source_name": "Skill Expert",
                    "type": "expertise", "count": 1,
                    "pool": sorted(proficient_skills),
                    "label": "Choose 1 already-proficient skill to gain expertise in",
                    "already_chosen": already_exp,
                })

    if "Martial Adept" in all_feats:
        key = "feat_martial_adept_maneuvers"
        already = made.get(key, [])
        if len(already) < 2:
            from dnd_app.data.classes import BATTLE_MASTER_MANEUVERS
            choices.append({
                "id": key, "source": "feat", "source_name": "Martial Adept",
                "type": "maneuver", "count": 2 - len(already),
                "pool": BATTLE_MASTER_MANEUVERS,
                "label": f"Choose {2 - len(already)} Battle Master maneuver(s)",
                "already_chosen": already,
            })
    if "Metamagic Adept" in all_feats:
        key = "feat_metamagic_adept_options"
        already = made.get(key, [])
        if len(already) < 2:
            from dnd_app.data.classes import METAMAGIC
            choices.append({
                "id": key, "source": "feat", "source_name": "Metamagic Adept",
                "type": "metamagic", "count": 2 - len(already),
                "pool": METAMAGIC,
                "label": f"Choose {2 - len(already)} Metamagic option(s)",
                "already_chosen": already,
            })
    if "Eldritch Adept" in all_feats:
        key = "feat_eldritch_adept_invocation"
        already = made.get(key, [])
        if len(already) < 1:
            from dnd_app.data.classes import ELDRITCH_INVOCATIONS
            import re
            is_warlock = char.get("class") == "Warlock" or any(
                c.get("class") == "Warlock" for c in char.get("classes", []))
            warlock_lvl = char.get("level", 0) if char.get("class") == "Warlock" else next(
                (c.get("level", 0) for c in char.get("classes", []) if c.get("class") == "Warlock"), 0)
            # Real rule: "If the invocation has a prerequisite of any
            # kind, you can choose that invocation only if you're a
            # warlock who meets the prerequisite" — reuses the same
            # prerequisite filter already built for real Warlocks
            # rather than duplicating that logic.
            pool = []
            for inv in ELDRITCH_INVOCATIONS:
                name_part = inv.split("–")[0].strip()
                if name_part.startswith("Pact of the"):
                    continue
                m = re.search(r'\(([^)]*)\)\s*$', name_part)
                if not m:
                    pool.append(inv)
                elif is_warlock:
                    req = m.group(1).lower()
                    lvl_m = re.match(r'(\d+)(st|nd|rd|th)', req)
                    if not lvl_m or warlock_lvl >= int(lvl_m.group(1)):
                        pool.append(inv)
            choices.append({
                "id": key, "source": "feat", "source_name": "Eldritch Adept",
                "type": "invocation", "count": 1,
                "pool": pool,
                "label": "Choose 1 Eldritch Invocation",
                "already_chosen": already,
            })
    return choices


def _get_optional_feature_choices(char):
    """TCE optional-feature choices — extensible for future ones.
    Canny (Deft Explorer's foundational 1st-level component) confirmed
    genuinely missing a real choice card, even though its other two
    parts (Roving, Tireless) were already correctly built elsewhere."""
    choices = []
    made = char.get("_choices", {})
    ranger_lvl = sum(c.get("level", 0) for c in char.get("classes", []) if c.get("class") == "Ranger")
    deft_on = (made.get("optional_features", {}).get("Deft Explorer", False)
               or char.get("optional_rules", {}).get("deft_explorer", False))
    if ranger_lvl >= 1 and deft_on:
        already_canny = made.get("deft_explorer_canny", [])
        if not already_canny:
            proficient_only = [s for s, lvl in char.get("skills", {}).items() if lvl == 2]
            if proficient_only:
                choices.append({
                    "id": "deft_explorer_canny", "source": "class", "source_name": "Ranger",
                    "type": "expertise", "count": 1,
                    "pool": sorted(proficient_only),
                    "label": "Canny (Deft Explorer): choose 1 proficient skill for doubled "
                             "proficiency bonus",
                    "already_chosen": already_canny,
                })
        already_canny_lang = made.get("deft_explorer_canny_languages", [])
        if len(already_canny_lang) < 2:
            choices.append({
                "id": "deft_explorer_canny_languages", "source": "class", "source_name": "Ranger",
                "type": "language", "count": 2,
                "label": "Canny (Deft Explorer): choose 2 additional languages",
                "already_chosen": already_canny_lang,
            })

    # Primal Knowledge (Barbarian, TCE optional, genuinely missing
    # entirely): 2 separate choice instances since 3rd and 10th level
    # are independent grants, not one combined choice. Uses Barbarian's
    # real 1st-level skill pool rather than a hardcoded guess.
    from dnd_app.data.classes import CLASS_DICT
    barb_lvl = sum(c.get("level", 0) for c in char.get("classes", []) if c.get("class") == "Barbarian")
    primal_on = (made.get("optional_features", {}).get("Primal Knowledge", False)
                 or char.get("optional_rules", {}).get("primal_knowledge", False))
    if primal_on:
        barb_skill_pool = CLASS_DICT.get("Barbarian", {}).get("skill_choices", [])
        for req_lvl, choice_id in ((3, "primal_knowledge_3_skill_profs"), (10, "primal_knowledge_10_skill_profs")):
            if barb_lvl >= req_lvl:
                already_pk = made.get(choice_id, [])
                if not already_pk:
                    choices.append({
                        "id": choice_id, "source": "class", "source_name": "Barbarian",
                        "type": "skill_prof", "count": 1,
                        "pool": barb_skill_pool,
                        "label": f"Primal Knowledge ({req_lvl}th level): choose 1 skill "
                                 f"proficiency",
                        "already_chosen": already_pk,
                    })
    return choices


def _get_race_choices(char):
    """Race-specific choices not covered by the main builder."""
    choices = []
    made = char.get("_choices",{})
    race = char.get("species") or char.get("race","")

    if race in RACE_SKILL_CHOICES:
        cfg = RACE_SKILL_CHOICES[race]
        already = made.get("race_skill_profs",[])
        if len(already) < cfg["count"]:
            choices.append({
                "id": "race_skill_profs",
                "source": "race", "source_name": race,
                "type": "skill_prof",
                "count": cfg["count"],
                "pool": cfg["pool"],
                "label": cfg["label"],
                "already_chosen": already,
            })

    # Aasimar (MPMM) Celestial Revelation: lets the player select which
    # revelation they get, from the race data's 3 options. Gated to
    # level 3+, and locked in once chosen per the real rule (never re-offered after).
    if race == "Aasimar (MPMM)":
        clvl = sum(c.get("level", 0) for c in char.get("classes", []))
        already_rev = made.get("aasimar_revelation", [])
        if clvl >= 3 and not already_rev:
            choices.append({
                "id": "aasimar_revelation", "source": "race", "source_name": race,
                "type": "skill_prof", "count": 1,
                "pool": ["Necrotic Shroud", "Radiant Consumption", "Radiant Soul"],
                "label": "Celestial Revelation: choose 1 (locked in once chosen)",
                "already_chosen": already_rev,
            })

    # Vedalken's Tireless Precision: a restricted-pool skill choice PLUS
    # a separate tool choice — both required, neither optional, so
    # modeled as two distinct choice cards rather than one combined
    # skill-or-tool pick.
    if race == "Vedalken":
        already_sk = made.get("race_skill_profs", [])
        if len(already_sk) < 1:
            choices.append({
                "id": "race_skill_profs", "source": "race", "source_name": race,
                "type": "skill_prof", "count": 1,
                "pool": ["Arcana","History","Investigation","Medicine","Performance","Sleight of Hand"],
                "label": "Tireless Precision (Vedalken): choose 1 of Arcana, History, Investigation, Medicine, Performance, Sleight of Hand",
                "already_chosen": already_sk,
            })
        already_tl = made.get("race_tool_profs", [])
        if len(already_tl) < 1:
            choices.append({
                "id": "race_tool_profs", "source": "race", "source_name": race,
                "type": "tool_prof", "count": 1, "pool": None,
                "label": "Tireless Precision (Vedalken): choose 1 tool proficiency",
                "already_chosen": already_tl,
            })

    # Warforged's Specialized Design: one skill (any) AND one tool
    # (any) — both required, modeled the same way as Vedalken above.
    if race == "Warforged":
        already_sk = made.get("race_skill_profs", [])
        if len(already_sk) < 1:
            choices.append({
                "id": "race_skill_profs", "source": "race", "source_name": race,
                "type": "skill_prof", "count": 1, "pool": ALL_SKILLS,
                "label": "Specialized Design (Warforged): choose 1 skill proficiency",
                "already_chosen": already_sk,
            })
        already_tl = made.get("race_tool_profs", [])
        if len(already_tl) < 1:
            choices.append({
                "id": "race_tool_profs", "source": "race", "source_name": race,
                "type": "tool_prof", "count": 1, "pool": None,
                "label": "Specialized Design (Warforged): choose 1 tool proficiency",
                "already_chosen": already_tl,
            })

    # Hobgoblin's Martial Training (VGM): two martial weapons of your
    # choice (its light armour comes with the race -- data/races.py)
    if race == "Hobgoblin":
        already = made.get("hobgoblin_martial_weapons", [])
        if len(already) < 2:
            from dnd_app.data.items import WEAPON_DICT
            choices.append({
                "id": "hobgoblin_martial_weapons", "source": "race", "source_name": race,
                "type": "weapon_or_tool_prof", "count": 2,
                "pool": sorted(n for n, w in WEAPON_DICT.items()
                               if str(w.get("category", "")).startswith("Martial")),
                "label": "Martial Training (Hobgoblin): choose 2 martial weapons",
                "already_chosen": already,
            })

    # Githyanki's Decadent Mastery: one skill OR tool of choice — a
    # single combined pick, using the existing skill_or_tool_prof type
    # the picker UI and apply_choice's aggregation already support.
    if race == "Githyanki":
        already = made.get("race_skill_or_tool_profs", [])
        if len(already) < 1:
            choices.append({
                "id": "race_skill_or_tool_profs", "source": "race", "source_name": race,
                "type": "skill_or_tool_prof", "count": 1, "pool": None,
                "label": "Decadent Mastery (Githyanki): choose 1 skill or tool proficiency",
                "already_chosen": already,
            })

    # Githyanki (MPMM)'s Astral Knowledge and Astral Elf's Astral Trance
    # are mechanically identical: "whenever you finish a long rest, you
    # gain proficiency in one skill and with one weapon or tool of your
    # choice ... until the end of your next long rest" — a temporary
    # grant re-chosen every long rest via RestOptionsDialog, not a
    # permanent one-time pick like Githyanki's own Decadent Mastery
    # above. Built as an initial pick at character creation (same
    # simplification already used for Guidance of the Spirits/Whispers
    # of the Dead) so the feature isn't blank until the character's
    # first in-fiction long rest.
    if race in ("Githyanki (MPMM)", "Astral Elf"):
        trait_name = "Astral Knowledge" if race == "Githyanki (MPMM)" else "Astral Trance"
        already_sk = made.get("astral_knowledge_skill", [])
        if not already_sk:
            choices.append({
                "id": "astral_knowledge_skill", "source": "race", "source_name": race,
                "type": "skill_prof", "count": 1, "pool": ALL_SKILLS,
                "label": f"{trait_name}: choose a skill proficiency (re-chosen on each long rest)",
                "already_chosen": already_sk,
            })
        already_wt = made.get("astral_knowledge_weapon_or_tool", [])
        if not already_wt:
            from dnd_app.data.items import WEAPON_NAMES, ALL_TOOLS
            choices.append({
                "id": "astral_knowledge_weapon_or_tool", "source": "race", "source_name": race,
                "type": "weapon_or_tool_prof", "count": 1, "pool": WEAPON_NAMES + ALL_TOOLS,
                "label": f"{trait_name}: choose a weapon or tool proficiency (re-chosen on each long rest)",
                "already_chosen": already_wt,
            })

    # Eladrin: seasonal Fey Step effect. Player picks one season;
    # RestOptionsDialog offers to re-pick after a long rest per the
    # actual rule ("you can change your chosen season after a long rest").
    if "eladrin" in race.lower():
        already_season = made.get("eladrin_season", [])
        if not already_season:
            choices.append({
                "id": "eladrin_season", "source": "race", "source_name": "Eladrin",
                "type": "fighting_style", "count": 1,
                "pool": ["Autumn – Fey Step charms one creature within 5 ft. of your destination",
                         "Winter – Fey Step frightens one creature within 5 ft. of your destination",
                         "Spring – a willing creature within 5 ft. can teleport with you",
                         "Summer – Fey Step deals 2d6 fire damage to creatures within 5 ft. of your origin"],
                "label": "Choose your Eladrin season (changeable after a long rest)",
                "already_chosen": already_season,
            })

    # Human extra language
    if race == "Human":
        already = made.get("human_extra_language",[])
        if not already:
            choices.append({
                "id": "human_extra_language",
                "source": "race", "source_name": "Human",
                "type": "language", "count": 1,
                "pool": LANGUAGES,
                "label": "Human Extra Language: choose 1",
                "already_chosen": already,
            })

    # High Elf / Half-Elf (High Descent): choose any cantrip from the
    # Wizard spell list. A genuine open choice, not a fixed grant — no
    # default can be guessed here any more than a Genie's kind could.
    subrace = char.get("subrace", "") or ""
    is_high_elf = race == "Elf" and "high" in subrace.lower()
    is_high_half_elf = race == "Half-Elf" and "high" in subrace.lower()
    if is_high_elf or is_high_half_elf:
        from dnd_app.data.spells import ALL_SPELLS
        wiz_cantrips = sorted({s["name"] for s in ALL_SPELLS
                                if s.get("level") == 0 and "Wizard" in s.get("classes", [])})
        key = "race_wizard_cantrip"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "race",
                "source_name": "High Elf" if is_high_elf else "Half-Elf (High Descent)",
                "type": "fighting_style", "count": 1,
                "pool": wiz_cantrips,
                "label": "Choose a Wizard cantrip",
                "already_chosen": already,
            })

    # Merfolk: each subrace grants an open cantrip choice from a specific
    # class's list — same open-list pattern as High Elf, just keyed to a
    # different class per subrace rather than always Wizard.
    if race == "Merfolk":
        MERFOLK_CANTRIP_CLASS = {
            "green": "Druid", "blue": "Wizard", "emeria": "Druid",
            "ula": "Wizard", "cosi": "Bard",
        }
        matched_class = next((cls for key, cls in MERFOLK_CANTRIP_CLASS.items()
                               if key in subrace.lower()), None)
        if matched_class:
            from dnd_app.data.spells import ALL_SPELLS
            cantrips = sorted({s["name"] for s in ALL_SPELLS
                                if s.get("level") == 0 and matched_class in s.get("classes", [])})
            key = "race_merfolk_cantrip"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "race", "source_name": f"Merfolk ({matched_class} cantrip)",
                    "type": "fighting_style", "count": 1,
                    "pool": cantrips,
                    "label": f"Choose a {matched_class} cantrip",
                    "already_chosen": already,
                })

    # Astral Elf: choose one of exactly three cantrips (not an open Wizard
    # list like High Elf).
    if race == "Astral Elf":
        key = "astral_elf_cantrip"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "race", "source_name": "Astral Elf",
                "type": "fighting_style", "count": 1,
                "pool": ["Dancing Lights", "Light", "Sacred Flame"],
                "label": "Astral Fire: choose a cantrip",
                "already_chosen": already,
            })

    # Racial spellcasting ability — several races with innate spellcasting
    # let the player choose which of INT/WIS/CHA powers it, rather than
    # fixing one. A real choice, not something with a sensible default, so
    # it's asked for explicitly rather than silently assumed.
    RACES_WITH_ABILITY_CHOICE = {
        "Firbolg": "Firbolg Magic", "Fairy": "Fairy Magic",
        "Astral Elf": "Astral Fire", "Hexblood": "Hex Magic",
    }
    ability_source = RACES_WITH_ABILITY_CHOICE.get(race)
    if not ability_source and race == "Yuan-ti Pureblood" and "mpmm" in subrace.lower():
        ability_source = "Innate Spellcasting"
    if ability_source:
        key = "racial_spell_ability"
        already = made.get(key, [])
        if not already:
            choices.append({
                "id": key, "source": "race", "source_name": ability_source,
                "type": "fighting_style", "count": 1,
                "pool": ["Intelligence", "Wisdom", "Charisma"],
                "label": f"Choose spellcasting ability for {ability_source}",
                "already_chosen": already,
            })

    # Simic Hybrid: Additional Animal Enhancement at 5th (total) level.
    # The 1st-level pick is made in the character-creation wizard
    # (stored as simic_enhancement_1st); this is the second, later pick
    # the real rules grant, deliberately left for this level-up system.
    if race == "Simic Hybrid":
        total_lvl = sum(c.get("level", 0) for c in char.get("classes", []))
        if total_lvl >= 5:
            key = "simic_enhancement_5th"
            already = made.get(key, [])
            if not already:
                choices.append({
                    "id": key, "source": "race", "source_name": "Simic Hybrid",
                    "type": "fighting_style", "count": 1,
                    "pool": ["Grappling Appendages", "Carapace", "Acid Spit"],
                    "label": "Additional Animal Enhancement (5th level): choose one",
                    "already_chosen": already,
                })

    return choices


def _get_class_tool_choices(char):
    """Flexible ('of your choice') portions of class-granted tool
    proficiencies — Bard's 3 musical instruments, Monk's 1 artisan's-
    tool-or-instrument, and Artificer's 1 remaining artisan's tool
    pick. The fixed portions (Rogue's Thieves' tools, Druid's
    Herbalism kit, Artificer's Thieves'/Tinker's tools) are granted
    automatically via get_class_tool_profs() in builder.py and don't
    need a choice card at all."""
    from dnd_app.data.items import ALL_TOOLS, ARTISAN_TOOLS, INSTRUMENT_TOOLS
    choices = []
    made = char.get("_choices", {})
    class_names = [c.get("class", "") for c in char.get("classes", [])]

    if "Bard" in class_names:
        already = made.get("class_bard_tool_profs", [])
        if len(already) < 3:
            choices.append({
                "id": "class_bard_tool_profs", "source": "class", "source_name": "Bard",
                "type": "tool_prof", "count": 3, "pool": INSTRUMENT_TOOLS,
                "label": "Bard: choose 3 musical instruments",
                "already_chosen": already,
            })

    if "Monk" in class_names:
        already = made.get("class_monk_tool_profs", [])
        if len(already) < 1:
            choices.append({
                "id": "class_monk_tool_profs", "source": "class", "source_name": "Monk",
                "type": "tool_prof", "count": 1, "pool": ARTISAN_TOOLS + INSTRUMENT_TOOLS,
                "label": "Monk: choose 1 artisan's tool or musical instrument",
                "already_chosen": already,
            })

    if "Artificer" in class_names:
        already = made.get("class_artificer_tool_profs", [])
        if len(already) < 1:
            choices.append({
                "id": "class_artificer_tool_profs", "source": "class", "source_name": "Artificer",
                "type": "tool_prof", "count": 1, "pool": ARTISAN_TOOLS,
                "label": "Artificer: choose 1 additional artisan's tool",
                "already_chosen": already,
            })

    return choices


def _get_dm_reward_choices(char):
    """Player-chosen proficiency grants from DM-Granted Bonus Features
    (dm_rewards.py) whose reward text names a choice (e.g. "choose one
    skill") rather than a fixed grant."""
    choices = []
    made = char.get("_choices", {})
    rewards = set(char.get("dm_rewards", []))

    if "Echoing Soul" in rewards:
        key_sk = "dmreward_echoing_soul_skills"
        already_sk = made.get(key_sk, [])
        if len(already_sk) < 2:
            choices.append({
                "id": key_sk, "source": "dm_reward", "source_name": "Echoing Soul",
                "type": "skill_prof", "count": 2, "pool": ALL_SKILLS,
                "label": "Channeled Prowess: choose 2 skill proficiencies",
                "already_chosen": already_sk,
            })
        key_lang = "dmreward_echoing_soul_language"
        already_lang = made.get(key_lang, [])
        if len(already_lang) < 1:
            choices.append({
                "id": key_lang, "source": "dm_reward", "source_name": "Echoing Soul",
                "type": "language", "count": 1,
                "label": "Inherent Tongue: choose 1 additional language",
                "already_chosen": already_lang,
            })

    if "Symbiotic Being" in rewards:
        key_sk2 = "dmreward_symbiotic_being_skill"
        already_sk2 = made.get(key_sk2, [])
        if len(already_sk2) < 1:
            choices.append({
                "id": key_sk2, "source": "dm_reward", "source_name": "Symbiotic Being",
                "type": "skill_prof", "count": 1,
                "pool": ["Arcana", "Deception", "History", "Intimidation", "Insight",
                         "Investigation", "Nature", "Religion", "Perception", "Persuasion"],
                "label": "Entwined Existence: choose 1 skill proficiency",
                "already_chosen": already_sk2,
            })

    return choices


# ═══════════════════════════════════════════════════════════════════════════
# Cleaning up after a change
# ═══════════════════════════════════════════════════════════════════════════


def _all_relevant_choice_ids(char_snapshot: dict) -> set:
    """Every pending-choice id structurally relevant to this exact
    character state, regardless of whether it's already been answered
    (computed against a scratch copy with _choices cleared, so an
    already-answered choice still shows up here). Union of every
    choice-generating function the Choices tab actually combines.
    Used to diff "before" vs "after" a race/background/class/subclass/
    level change and prune any choice from the real character's
    _choices that's no longer relevant — without this, changing away
    from something never lets you make its choice differently, and can
    leave an old choice's pool/value silently misapplied to whatever
    replaced it."""
    import copy
    store = char_snapshot.get("_choices", {}) or {}
    plain = copy.deepcopy(char_snapshot)
    plain["_choices"] = {}
    ids = {c["id"] for c in _generate_choices(plain) if "id" in c}
    # a growing choice that's already full (8 invocations at 8) generates
    # nothing above -- so ask again with those lists empty, or it's never
    # "relevant" and never goes when its class or level does
    ids |= {c["id"] for c in _all_relevant_choices(char_snapshot) if "id" in c}
    # a choice offered only once another is answered (Blessed Warrior's
    # cantrips, Pact of the Tome's): keep the relevant answers, and each
    # round adds the choices they open up
    for _ in range(4):
        plain = copy.deepcopy(char_snapshot)
        plain["_choices"] = {k: v for k, v in store.items() if k in ids}
        more = {c["id"] for c in _generate_choices(plain) if "id" in c} - ids
        if not more:
            break
        ids |= more
    return ids


# Choices that hold every pick so far, growing with level, and the
# character lists they also fill
_CUMULATIVE_IDS = ("eldritch_invocations", "artificer_infusions", "fighter_maneuvers",
                   "sorcerer_metamagic", "four_elements_disciplines", "rune_knight_runes",
                   "blood_hunter_mutagens", "blood_hunter_curses", "arcane_shot_options",
                   "kensei_weapons", "magical_secrets_spells")

_CUMULATIVE_LISTS = ("eldritch_invocations", "artificer_infusions",
                     "battle_master_maneuvers", "magical_secrets_spells")


def _generate_choices(scratch: dict) -> list:
    from dnd_app.core.builder import get_choices_needed
    return (get_choices_needed(scratch) + _get_subclass_choices(scratch)
            + _get_race_choices(scratch) + _get_class_tool_choices(scratch)
            + _get_feat_choices(scratch) + _get_dm_reward_choices(scratch)
            + _get_optional_feature_choices(scratch))


def _all_relevant_choices(char_snapshot: dict, keep_choices: bool = False) -> list:
    """Every choice this exact character state has, with its full count and
    pool: generated with the growing choices' picks and lists emptied.
    keep_choices keeps the other picks (a pact boon), so an invocation's
    pool still knows what it may need."""
    import copy
    scratch = copy.deepcopy(char_snapshot)
    if keep_choices:
        for cid in _CUMULATIVE_IDS:
            scratch.setdefault("_choices", {}).pop(cid, None)
    else:
        scratch["_choices"] = {}
    for field in _CUMULATIVE_LISTS:
        scratch[field] = []
    return _generate_choices(scratch)


def _trim_over_count(char: dict) -> dict:
    """After a level down, a growing choice can hold more picks than the
    level allows: keep the oldest that are still allowed (an invocation
    whose level or pact it no longer meets goes first). Returns
    {choice id: the picks dropped}."""
    store = char.get("_choices", {})
    dropped = {}
    # 1. one count (and an invocation's allowed pool) per choice -- the
    #    same choice can come from two generators, one with the real pool
    limits = {}
    for c in _all_relevant_choices(char, keep_choices=True):
        cid = c.get("id")
        if cid not in _CUMULATIVE_IDS:
            continue
        count = c.get("count") or 0
        pool = c.get("pool") if c.get("type") == "invocation" else None
        have = limits.get(cid)
        if have is None:
            limits[cid] = [count, pool]
        else:
            have[0] = min(have[0], count)
            have[1] = have[1] or pool
    # 2. keep the oldest picks still allowed, up to the count
    for cid, (count, pool) in limits.items():
        held = store.get(cid)
        if not isinstance(held, list):
            continue
        keep = [p for p in held if not pool or p in pool][:count]
        if len(keep) < len(held):
            dropped[cid] = [p for p in held if p not in keep]
            store[cid] = keep
    return dropped


# Choice ids from _get_race_choices()/get_choices_needed() that are keyed
# generically (by choice TYPE, e.g. "race_skill_profs") rather than by the
# specific race/background name — so _all_relevant_choice_ids()'s before/
# after diff can't tell "still relevant" from "relevant to a DIFFERENT
# race/background now, with a completely different pool, but the old
# answer looks superficially complete". Astral Elf and Githyanki (MPMM)
# happen to share the same two ids since they're mechanically identical.
RACE_SCOPED_CHOICE_IDS = {
    "race_skill_profs", "race_tool_profs", "race_skill_or_tool_profs",
    "aasimar_revelation", "astral_knowledge_skill",
    "astral_knowledge_weapon_or_tool", "eladrin_season", "human_extra_language",
}

BACKGROUND_SCOPED_CHOICE_IDS = {"bg_languages", "bg_skill_profs", "bg_tool_profs"}


def change_and_prune(char: dict, change, scoped=()) -> set:
    """A race, subrace or background change: make it, then drop every
    choice the old one asked for and the new one doesn't (a High Elf's
    Wizard cantrip, once Human), picks and all -- plus `scoped`, the
    generic ids whose old picks can't carry over to the new pool."""
    old_ids = _all_relevant_choice_ids(char)
    change()
    new_ids = _all_relevant_choice_ids(char)
    return _prune_stale_choices(char, (old_ids - new_ids) | set(scoped))


def _prune_stale_choices(char: dict, stale_ids: set) -> set:
    """Remove the given choice ids from char["_choices"] if present, and
    everything that hangs off them. Returns the ids actually removed."""
    from dnd_app.core.builder import forget_choice_picks
    store = char.get("_choices", {})
    removed, stale = set(), set(stale_ids)
    # 1. take out the stale choices, and the picks a growing choice no
    #    longer has room for (after a level down)
    # 2. their picks leave every list they landed in -- skills, styles,
    #    invocations, spells, feats...
    # 3. dropping a feat or a style can make more choices stale (its own
    #    picks): go round again until nothing changes
    for _ in range(6):
        before = _all_relevant_choice_ids(char)
        gone = {cid for cid in stale if cid in store}
        picks = {cid: store.pop(cid, None) for cid in gone}
        removed |= gone
        picks.update(_trim_over_count(char))
        if not picks:
            break
        forget_choice_picks(char, picks)
        stale = before - _all_relevant_choice_ids(char)
    return removed
