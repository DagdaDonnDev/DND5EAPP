"""
D&D 5e 2024 PHB Species
Key 2024 changes:
- Races → Species (official rename)
- No fixed ASI: all species use "Free ASI" (+2/+1 or +1/+1/+1) distributed freely
- No Ability Score penalties
- Subraces replaced by Lineages/Ancestries on most species
- Sunlight Sensitivity removed from Drow
- 10 core species in PHB 2024; others still usable from older books

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ── 2024 PHB Core Species (10 total) ─────────────────────────────────────────
# All 2024 species use free ASI: +2/+1 or +1/+1/+1 distributed to any stats

def species_2024(name, speed=30, size="Medium", free_asi=True, traits=None,
                 languages=None, notes="", source="PHB 2024", creature_type="Humanoid"):
    return dict(name=name, edition="2024", speed=speed, size=size,
                free_asi=free_asi,  # always True for 2024; ASI chosen by player
                traits=traits or [], languages=languages or ["Common"],
                notes=notes, source=source, creature_type=creature_type)


ALL_SPECIES_2024 = [

    species_2024("Aasimar",
        traits=[
            "Celestial Resistance – resistance to Necrotic and Radiant damage",
            "Darkvision 60 ft",
            "Healing Hands – Touch creature: restore HP = Prof bonus; 1/LR",
            "Light Bearer – Light cantrip (CHA)",
            "Celestial Revelation (level 3) – choose Heavenly Wings (fly 10 min/LR) OR "
              "Inner Radiance (radiant aura 10 min/LR; 1d6 Radiant to end-of-turn adjacent) OR "
              "Necrotic Shroud (frighten creatures; 1d6 Necrotic bonus 10 min/LR)",
        ],
        languages=["Common", "one of your choice"],
    ),

    species_2024("Dragonborn",
        traits=[
            "Draconic Ancestry – choose dragon type (acid/cold/fire/lightning/poison)",
            "Breath Weapon – action: 15-ft cone or 30-ft line; 1d10 × (Prof mod / 2 round up) damage; DEX save DC = 8+CON+Prof; uses = Prof bonus/LR",
            "Damage Resistance – matching ancestry type",
            "Darkvision 60 ft",
            "Draconic Flight (level 5) – bonus action, sprout wings; fly speed = walk speed for 10 min; 1/LR",
        ],
        languages=["Common", "Draconic"],
    ),

    species_2024("Dwarf", speed=30,  # 2024 change: speed no longer 25
        traits=[
            "Darkvision 120 ft",
            "Dwarven Resilience – resistance to Poison damage; adv. on saves vs. Poisoned",
            "Dwarven Toughness – HP max +1; +1 per level",
            "Stonecunning – bonus action: Tremorsense 60 ft for 10 min (stone surfaces); uses = Prof bonus/LR",
        ],
        notes="2024: Speed is now 30 ft (was 25). No longer separate Hill/Mountain subraces as hard rules — Dwarven Toughness covers hill/mountain equivalents. Subrace flavor still valid as lore.",
        languages=["Common", "Dwarvish"],
    ),

    species_2024("Elf",
        traits=[
            "Darkvision 60 ft",
            "Elven Lineage – choose one at creation (grants level 1 trait + spells at 3 and 5)",
            "Fey Ancestry – adv. on saves vs. Charmed",
            "Keen Senses – Insight, Perception, or Survival proficiency (choose 1)",
            "Trance – 4-hr meditation = long rest; immune to magic sleep",
        ],
        notes="Elven Lineages replace old subraces. Lineages: Drow (Darkvision 120ft, Dancing Lights/Faerie Fire/Darkness), High Elf (Detect Magic at will at 5; cantrip choice), or Wood Elf (35-ft speed; Druidcraft; Misty Step at 5).",
        languages=["Common", "Elvish"],
    ),

    species_2024("Gnome", speed=30, size="Small",  # 2024 speed is 30 (was 25)
        traits=[
            "Darkvision 60 ft",
            "Gnomish Cunning – adv. on INT/WIS/CHA saves",
            "Gnomish Lineage – choose one:",
            " • Forest Gnome: Minor Illusion cantrip + Speak with Animals 2/LR",
            " • Rock Gnome: Mending + Prestidigitation cantrips; Tinker feature (craft gadgets)",
        ],
        notes="2024: Speed is now 30 ft (was 25). Deep Gnome optional lineage in supplemental material.",
        languages=["Common", "Gnomish"],
    ),

    species_2024("Goliath",
        traits=[
            "Giant Ancestry – choose one (uses = Prof bonus/LR):",
            " • Cloud's Jaunt (Cloud Giant): bonus action teleport 30 ft",
            " • Fire's Burn (Fire Giant): on hit, deal 1d10 extra Fire damage",
            " • Frost's Chill (Frost Giant): on hit, 1d6 Cold + −10 ft speed until your next turn",
            " • Hill's Tumble (Hill Giant): on hit vs. Large or smaller: Prone",
            " • Stone's Endurance (Stone Giant): reaction − 1d12+CON from damage",
            " • Storm's Thunder (Storm Giant): reaction when damaged within 60 ft: 1d8 Thunder",
            "Large Form (level 5) – bonus action: become Large for 10 min; Adv STR; +10 ft speed; 1/LR",
            "Powerful Build – count as Large for carry/push; Adv to end Grappled",
        ],
        languages=["Common", "Giant"],
    ),

    species_2024("Halfling", speed=30, size="Small",  # 2024 speed is 30 (was 25)
        traits=[
            "Brave – adv. on saves vs. Frightened",
            "Halfling Nimbleness – move through space of larger creature",
            "Luck – when you roll 1 on a d20 Test, reroll; must use new roll",
            "Naturally Stealthy – Hide when behind creature one size larger",
        ],
        notes="2024: Speed 30 ft. Removed separate Lightfoot/Stout subraces as mechanical rules; flavor still valid.",
        languages=["Common", "one of your choice"],
    ),

    species_2024("Human",
        traits=[
            "Resourceful – gain Heroic Inspiration on every Long Rest",
            "Skillful – gain proficiency in one skill of your choice",
            "Versatile – gain one Origin Feat of your choice (Skilled recommended); "
                        "Humans are the only species that gain two Origin Feats at creation",
        ],
        notes="2024 Human has significant mechanical changes: Heroic Inspiration every LR, 1 extra skill, 1 Origin Feat (effectively 2 feats with background feat).",
        languages=["Common", "one of your choice"],
    ),

    species_2024("Orc",
        traits=[
            "Adrenaline Rush – bonus action: Dash + gain temp HP = Prof bonus; uses = Prof bonus/LR",
            "Darkvision 120 ft",
            "Powerful Build – count as one size larger for carry; Adv to end Grappled",
            "Relentless Endurance – 1/LR: when reduced to 0 HP, drop to 1 instead",
        ],
        languages=["Common", "Orc"],
    ),

    species_2024("Tiefling",
        traits=[
            "Darkvision 60 ft",
            "Fiendish Legacy – choose one at creation:",
            " • Abyssal: resistance to Poison; Poison Spray cantrip; Ray of Sickness at 3; Hold Person at 5",
            " • Chthonic: resistance to Necrotic; Chill Touch cantrip; False Life at 3; Ray of Enfeeblement at 5",
            " • Infernal: resistance to Fire; Fire Bolt cantrip; Hellish Rebuke at 3; Darkness at 5",
            "Otherworldly Presence – Thaumaturgy cantrip",
        ],
        notes="2024 Tiefling replaces fixed Infernal Legacy with three Fiendish Legacy options. No longer +INT/+CHA fixed — free ASI only.",
        languages=["Common", "Infernal"],
    ),
]

# ── 2024 Origin Feats (granted by Backgrounds) ────────────────────────────────
ORIGIN_FEATS_2024 = [
    dict(name="Alert", category="Origin",
         special="Initiative Proficiency: add Prof bonus to Initiative. "
                 "Initiative Swap: immediately swap Initiative with one willing ally 1/combat."),
    dict(name="Crafter", category="Origin",
         special="Proficiency with 3 Artisan's Tools of your choice. "
                 "10% discount when buying nonmagical items. "
                 "Craft an item during LR for 20 GP value max."),
    dict(name="Healer", category="Origin",
         special="Battle Medic: if you have Healer's Kit, use it to restore 1d8+1+Prof HP as "
                 "a Magic Action (uses kit charge; once per creature per SR). "
                 "Healing Rerolls: when you roll healing dice, treat 1 as 2."),
    dict(name="Lucky", category="Origin",
         special="Luck Points = Prof bonus. Spend 1 to reroll any d20 Test (attack/save/check); "
                 "choose which roll to use. Regain all on LR."),
    dict(name="Magic Initiate", category="Origin", repeatable=True,
         special="Choose Cleric, Druid, or Wizard list. Learn 2 cantrips + 1 level 1 spell (always prepared; "
                 "1/LR free; also cast with slots). Stat: INT/WIS/CHA (choose). Repeatable for different lists."),
    dict(name="Musician", category="Origin",
         special="Proficiency with 3 Musical Instruments of your choice. "
                 "Encouraging Song: after SR, grant Bardic Inspiration (d6) to Prof bonus allies who heard you."),
    dict(name="Savage Attacker", category="Origin",
         special="Once per turn when you hit with a weapon, roll damage dice twice and use either result."),
    dict(name="Skilled", category="Origin", repeatable=True,
         special="Gain proficiency in any combination of 3 skills or tools. Can take this feat multiple times."),
    dict(name="Tavern Brawler", category="Origin",
         special="Enhanced Unarmed Strike: on hit with Unarmed, choose Damage (1d4+STR) or Grapple. "
                 "Improvised Weapons: proficient; unarmed strike damage die = 1d4. "
                 "Throw: 1/turn throw creature you're grappling (5 ft; 1d6+STR)."),
    dict(name="Tough", category="Origin",
         special="HP max increases by 2. Increases by 2 again each level (retroactive)."),
]

# ── 2024 General Feats (level 4+; all grant +1 ASI) ──────────────────────────
GENERAL_FEATS_2024 = [
    dict(name="Ability Score Improvement", prereq="Level 4+", repeatable=True,
         special="+2 to one ability score, or +1 to two scores (max 20 each)."),
    dict(name="Actor", prereq="Level 4+, CHA 13+", asi={"CHA": 1},
         special="Impersonation: Adv on Deception/Performance to pass as someone. "
                 "Mimicry: copy sounds; Insight DC to detect = 8+CHA+Prof."),
    dict(name="Athlete", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Climb Speed = walk speed. Prone: stand from 5 ft. Jump from 5-ft run."),
    dict(name="Charger", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Improved Dash: +10 ft speed when Dashing. "
                 "Charge Attack: move 10 ft before attack: +1d8 dmg OR push 10 ft."),
    dict(name="Chef", prereq="Level 4+, CON or WIS 13+", asi_flex=["CON","WIS"],
         special="Cook's Utensils proficiency. After LR: treat bonus = Prof bonus creatures get 1d8 temp HP. "
                 "After SR: 1d8+Prof HP from hot meal."),
    dict(name="Crossbow Expert", prereq="Level 4+, DEX 13+", asi={"DEX": 1},
         special="Ignore Loading for crossbows. No disadv. within 5 ft with crossbow. "
                 "Bonus action extra hand crossbow attack if you attacked with crossbow."),
    dict(name="Crusher", prereq="Level 4+, STR or CON 13+", asi_flex=["STR","CON"],
         special="Bludgeoning hit: push 5 ft (1/turn). "
                 "Crit with bludgeoning: all attackers have Adv vs target until your next turn."),
    dict(name="Defensive Duelist", prereq="Level 4+, DEX 13+", asi={"DEX": 1},
         special="Reaction: finesse weapon equipped, hit by melee: +Prof bonus to AC until start of next turn."),
    dict(name="Dual Wielder", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Enhanced Dual Wielding: Light weapons: add ability mod to off-hand attacks. "
                 "Can draw/stow 2 one-handed weapons in same interaction. "
                 "Bonus Attack: bonus action attack if you've made Attack action (with Light weapon)."),
    dict(name="Durable", prereq="Level 4+, CON 13+", asi={"CON": 1},
         special="Defy Death: 1/LR when at 0 HP, don't fall unconscious; spend HD to heal. "
                 "Speedy Recovery: bonus action use one HD to recover HP."),
    dict(name="Elemental Adept", prereq="Level 4+, Spellcasting", repeatable=True, asi_flex=["INT","WIS","CHA"],
         special="Choose element (acid/cold/fire/lightning/thunder). Ignore resistance. Treat 1s as 2s on that damage. Repeatable for different element."),
    dict(name="Fey-Touched", prereq="Level 4+", asi_flex=["INT","WIS","CHA"],
         special="Misty Step + one 1st-level Divination/Enchantment spell (always prepared; 1/LR free; or use slots)."),
    dict(name="Fighting Initiate", prereq="Level 4+, martial weapon proficiency", asi_flex=["STR","DEX"],
         special="Learn one Fighting Style Feat. Can swap it on level up."),
    dict(name="Grappler", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Punch and Grab: on Unarmed hit with Attack action: use both Damage and Grapple. "
                 "Adv on attacks vs Grappled creatures. Move Grappled creature (your size or smaller) without extra movement."),
    dict(name="Great Weapon Master", prereq="Level 4+, STR 13+", asi={"STR": 1},
         special="Heavy weapon attacks: +Prof bonus damage. "
                 "Crit or killing blow: bonus action extra melee attack."),
    dict(name="Heavily Armored", prereq="Level 4+, medium armor proficiency", asi={"STR": 1},
         special="Heavy armor proficiency."),
    dict(name="Heavy Armor Master", prereq="Level 4+, heavy armor proficiency", asi={"STR": 1},
         special="While in heavy armor: non-magical B/P/S damage reduced by Prof bonus."),
    dict(name="Inspiring Leader", prereq="Level 4+, CHA or WIS 13+", asi_flex=["CHA","WIS"],
         special="On SR or LR: inspiring speech to up to 5 allies. Each gains temp HP = your level + chosen mod."),
    dict(name="Keen Mind", prereq="Level 4+, INT 13+", asi={"INT": 1},
         special="Choose one from Arcana/History/Investigation/Nature/Religion: gain proficiency or expertise. "
                 "Study action as bonus action."),
    dict(name="Lightly Armored", prereq="Level 4+", asi_flex=["STR","DEX"],
         special="Light armor proficiency. Shield proficiency."),
    dict(name="Mage Slayer", prereq="Level 4+", asi_flex=["STR","DEX","CON"],
         special="Adv on saves vs spells. When a caster within 5 ft casts: reaction to attack. "
                 "Concentration Bane: on damage, target disadv Conc save."),
    dict(name="Magic Initiate", prereq="Level 4+", repeatable=True, asi_flex=["INT","WIS","CHA"],
         special="As Origin version (2 cantrips + 1st-level spell) but now gives +1 ASI. Repeatable for different lists."),
    dict(name="Martial Weapon Training", prereq="Level 4+", asi_flex=["STR","DEX"],
         special="Proficiency with all Martial weapons."),
    dict(name="Medium Armor Master", prereq="Level 4+, medium armor proficiency", asi_flex=["STR","DEX"],
         special="No Stealth disadv. in medium armor. Max DEX bonus = +3."),
    dict(name="Mobile", prereq="Level 4+", asi_flex=["STR","DEX"],
         special="+10 ft speed. Difficult terrain costs no extra movement when Dashing. "
                 "Attackers you've attacked don't get OA vs you."),
    dict(name="Moderately Armored", prereq="Level 4+, light armor proficiency", asi_flex=["STR","DEX"],
         special="Medium armor proficiency. Shield proficiency."),
    dict(name="Mounted Combatant", prereq="Level 4+", asi_flex=["STR","DEX","WIS"],
         special="Adv on attacks vs unmounted creatures smaller than mount. "
                 "Redirect: force attacks targeting mount to target you. Mount evasion on DEX save."),
    dict(name="Observant", prereq="Level 4+", asi_flex=["INT","WIS"],
         special="+5 passive Perception and Investigation. Lip-reading if you see mouth and know language. "
                 "Quick Study: take Search action as bonus action."),
    dict(name="Piercer", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Reroll 1s on piercing damage (1/turn). Extra damage die on piercing crit."),
    dict(name="Poisoner", prereq="Level 4+, DEX or INT 13+", asi_flex=["DEX","INT"],
         special="Poisoner's Kit proficiency. Ignore poison resistance. "
                 "Coat weapon in 1 min (or 1 attack): DC 8+modifier+Prof CON save or Poisoned 1 min; repeated saves."),
    dict(name="Polearm Master", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Bonus action butt-end attack (1d4 bludgeoning; same weapon). "
                 "Opportunity attack when creature enters your reach. "
                 "Works with: glaive, halberd, pike, quarterstaff, spear, lance."),
    dict(name="Resilient", prereq="Level 4+", asi_flex=["STR","DEX","CON","INT","WIS","CHA"],
         special="Gain proficiency in saving throws for the chosen ability score."),
    dict(name="Ritual Caster", prereq="Level 4+, INT/WIS/CHA 13+", asi_flex=["INT","WIS","CHA"],
         special="Ritual Book: 2 first-level rituals from a chosen class. Add more from scrolls/spellbooks. "
                 "Cast only as rituals (not using slots)."),
    dict(name="Savage Attacker", prereq="Level 4+", asi_flex=["STR","DEX"],
         special="1/turn: reroll melee weapon damage dice; use either result. (Also an Origin feat without ASI.)"),
    dict(name="Sentinel", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Opportunity attacks stop movement (speed → 0). Disengage still triggers OA from you. "
                 "Guardian: reaction to attack when adjacent creature attacks someone else."),
    dict(name="Shadow-Touched", prereq="Level 4+", asi_flex=["INT","WIS","CHA"],
         special="Invisibility + one 1st-level Illusion/Necromancy spell (always prepared; 1/LR free; or use slots)."),
    dict(name="Sharpshooter", prereq="Level 4+, DEX 13+", asi={"DEX": 1},
         special="Long range without disadv. Ignore half and three-quarters cover. "
                 "Piercing Shot: 1/turn on ranged hit, push 15 ft (STR save DC = 8+DEX+Prof)."),
    dict(name="Shield Master", prereq="Level 4+, STR 13+", asi={"STR": 1},
         special="Shield Bash: if you attack, bonus action: shield shove 5 ft (STR save or Prone). "
                 "Interpose Shield: reaction DEX save for half: take no damage instead."),
    dict(name="Skill Expert", prereq="Level 4+", asi_flex=["any"],
         special="Gain proficiency in one skill. Gain expertise (double Prof) in one skill you're proficient in."),
    dict(name="Slasher", prereq="Level 4+, STR or DEX 13+", asi_flex=["STR","DEX"],
         special="Slashing damage: −10 ft speed (1/turn). Crit with slashing: disadv attacks next turn."),
    dict(name="Speedy", prereq="Level 4+", asi_flex=["DEX","CON"],
         special="+10 ft speed. Dash for free on LR (not using Dash action). Adv on DEX checks to avoid tripping."),
    dict(name="Spell Sniper", prereq="Level 4+, Spellcasting", asi_flex=["INT","WIS","CHA"],
         special="Blindsight 10 ft. No disadv. on spell attack rolls within 5 ft. "
                 "Ranged spell attacks of 10+ ft: +60 ft range."),
    dict(name="Telekinetic", prereq="Level 4+", asi_flex=["INT","WIS","CHA"],
         special="Mage Hand cantrip (invisible; bonus action control). "
                 "Telekinetic Shove: bonus action push/pull 5 ft (STR save DC=8+stat+Prof)."),
    dict(name="Telepathic", prereq="Level 4+", asi_flex=["INT","WIS","CHA"],
         special="Detect Thoughts 1/LR (or use slots). Telepathy 60 ft (willing creature you can see)."),
    dict(name="War Caster", prereq="Level 4+, Spellcasting", asi_flex=["INT","WIS","CHA"],
         special="Adv on Concentration saves. Somatic with hands full. "
                 "Reactive Spell: reaction cast targeting the attacker as OA (single-target spells)."),
    dict(name="Weapon Master", prereq="Level 4+", asi_flex=["STR","DEX"],
         special="Proficiency with 4 weapons of your choice. Can swap Weapon Mastery on LR."),
]

SPECIES_NAMES_2024 = [s["name"] for s in ALL_SPECIES_2024]
ORIGIN_FEAT_NAMES_2024 = [f["name"] for f in ORIGIN_FEATS_2024]
GENERAL_FEAT_NAMES_2024 = [f["name"] for f in GENERAL_FEATS_2024]

def get_species_2024(name: str) -> dict:
    for s in ALL_SPECIES_2024:
        if s["name"] == name:
            return s
    return None

def get_origin_feat_2024(name: str) -> dict:
    for f in ORIGIN_FEATS_2024:
        if f["name"] == name:
            return f
    return None
