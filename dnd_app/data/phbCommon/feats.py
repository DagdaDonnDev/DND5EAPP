"""
Official D&D 5e Feats — rebuilt from user-provided official sourcebook text
(2024-07 audit). Every entry's "special" field is transcribed directly from
published text rather than paraphrased from an earlier, partially-corrupted
version of this file, which had both a widespread duplicate-text-fragment
formatting bug and several genuinely invented/wrong mechanics.

Author: Ethan O'Brien
Date: 2026-08-20
"""

def feat(name, source, prereq="", asi=None, asi_flex=None, special="", **kwargs):
    return dict(name=name, source=source, prereq=prereq,
                asi=asi or {}, asi_flex=asi_flex or [],
                special=special, **kwargs)


ALL_FEATS = [

    # ── Player's Handbook ─────────────────────────────────────────────────────
    feat('Actor', 'PHB', asi={'CHA': 1},
         special="Advantage on CHA (Deception)/CHA (Performance) checks to pass as a different "
                 "person. Can mimic another person's speech or a creature's sounds you've heard "
                 "for 1+ minute (WIS (Insight) contested by your CHA (Deception) reveals a fake)."),

    feat('Alert', 'PHB',
         special="+5 to initiative. Can't be surprised while conscious. Other creatures don't "
                 "gain advantage on attack rolls against you from being unseen by you."),

    feat('Athlete', 'PHB', asi_flex=['STR', 'DEX'],
         special="Standing from prone costs only 5 ft. of movement. Climbing costs no extra "
                 "movement. Running long/high jumps need only a 5-ft. running start."),

    feat('Charger', 'PHB',
         special="When you Dash, use a bonus action to make one melee attack or shove a creature. "
                 "If you moved 10+ ft. in a straight line first: +5 to the attack's damage roll, "
                 "or push the shove target up to 10 ft."),

    feat('Crossbow Expert', 'PHB',
         special="Ignore the Loading property on crossbows you're proficient with. Being within "
                 "5 ft. of a hostile creature doesn't impose disadvantage on your ranged attacks. "
                 "When you Attack with a one-handed weapon, bonus action attack with a hand crossbow."),

    feat('Defensive Duelist', 'PHB', prereq='DEX 13+',
         special="While wielding a finesse weapon you're proficient with, reaction when hit by a "
                 "melee attack: add your proficiency bonus to your AC for that attack."),

    feat('Dual Wielder', 'PHB',
         special="+1 AC while wielding a separate melee weapon in each hand. Two-weapon fighting "
                 "works even with non-light one-handed melee weapons. Draw or stow two one-handed "
                 "weapons in the time it would normally take to draw/stow one."),

    feat('Dungeon Delver', 'PHB',
         special="Advantage on WIS (Perception)/INT (Investigation) to find secret doors. "
                 "Advantage on saves to avoid/resist traps. Resistance to trap damage. Traveling "
                 "at a fast pace doesn't impose the usual -5 to passive Perception."),

    feat('Durable', 'PHB', asi={'CON': 1},
         special="+1 CON (max 20). When you roll a Hit Die to heal, the minimum HP regained "
                 "equals twice your CON modifier (min 2)."),

    feat('Elemental Adept', 'PHB', prereq='Spellcasting',
         special="Choose a damage type (acid/cold/fire/lightning/thunder). Your spells of that "
                 "type ignore resistance to it, and you can treat any 1 rolled on a damage die of "
                 "that type as a 2. Repeatable, choosing a different type each time."),

    feat('Grappler', 'PHB', prereq='STR 13+',
         special="Advantage on attack rolls against a creature you're grappling. Action to attempt "
                 "to pin a grappled creature: another grapple check; success restrains both of you "
                 "until the grapple ends."),

    feat('Great Weapon Master', 'PHB',
         special="On a critical hit or reducing a creature to 0 HP with a melee weapon, bonus "
                 "action melee attack. Before attacking with a heavy weapon you're proficient with, "
                 "take -5 to the attack roll for +10 damage on a hit."),

    feat('Healer', 'PHB',
         special="Using a healer's kit to stabilize a dying creature also restores 1 HP to it. "
                 "Action + one use of a healer's kit: restore 1d6+4 HP to a creature, plus HP equal "
                 "to its max Hit Dice; that creature can't benefit again until it rests."),

    feat('Heavily Armored', 'PHB', prereq='Prof. medium armor', asi={'STR': 1},
         special="+1 STR (max 20). Gain proficiency with heavy armor."),

    feat('Heavy Armor Master', 'PHB', prereq='Prof. heavy armor', asi={'STR': 1},
         special="+1 STR (max 20). While wearing heavy armor, reduce nonmagical bludgeoning/"
                 "piercing/slashing damage you take by 3."),

    feat('Inspiring Leader', 'PHB', prereq='CHA 13+',
         special="Spend 10 minutes inspiring up to 6 friendly creatures (incl. yourself) within "
                 "30 ft. who can see/hear and understand you: each gains temp HP = your level + "
                 "CHA modifier. A creature can't benefit again until it rests."),

    feat('Keen Mind', 'PHB', asi={'INT': 1},
         special="+1 INT (max 20). Always know which way is north, and hours until next sunrise/"
                 "sunset. Can accurately recall anything seen or heard in the past month."),

    feat('Lightly Armored', 'PHB', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). Gain proficiency with light armor."),

    feat('Linguist', 'PHB', asi={'INT': 1},
         special="+1 INT (max 20). Learn three languages of your choice. Create written ciphers "
                 "others can't decipher without teaching them, an INT check (DC = your INT score + "
                 "proficiency bonus), or magic."),

    feat('Lucky', 'PHB',
         special="3 luck points/long rest. Spend one to roll an extra d20 for an attack roll, "
                 "ability check, or save (choose after rolling, before the outcome; pick which d20 "
                 "to use). Also usable when a creature attacks you: roll a d20 and choose whether "
                 "the attack uses its roll or yours. If multiple creatures spend luck on the same "
                 "roll, the points cancel out and no extra dice are rolled."),

    feat('Mage Slayer', 'PHB',
         special="Reaction: melee attack a creature within 5 ft. that casts a spell. Damaging a "
                 "concentrating creature gives it disadvantage on that concentration save. "
                 "Advantage on saves against spells cast by creatures within 5 ft. of you."),

    feat('Magic Initiate', 'PHB',
         special="Choose a class (bard/cleric/druid/sorcerer/warlock/wizard). Learn two cantrips "
                 "from its list, plus one 1st-level spell from the same list, castable once at its "
                 "lowest level per long rest (or with a spell slot). Spellcasting ability: CHA for "
                 "bard/sorcerer/warlock, WIS for cleric/druid, INT for wizard."),

    feat('Martial Adept', 'PHB',
         special="Learn two Battle Master maneuvers (save DC = 8 + proficiency bonus + STR or DEX "
                 "modifier, your choice). Gain one d6 superiority die (stacks with others from "
                 "elsewhere), regained on a short or long rest."),

    feat('Medium Armor Master', 'PHB', prereq='Prof. medium armor',
         special="Wearing medium armor no longer imposes disadvantage on DEX (Stealth). With DEX "
                 "16+, add 3 (not 2) to AC from medium armor."),

    feat('Mobile', 'PHB',
         special="+10 ft. speed. Dash ignores difficult terrain. Melee attacking a creature "
                 "doesn't provoke an opportunity attack from it for the rest of the turn, hit or miss."),

    feat('Moderately Armored', 'PHB', prereq='Prof. light armor', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). Gain proficiency with medium armor and shields."),

    feat('Mounted Combatant', 'PHB',
         special="While mounted and not incapacitated: advantage on melee attacks against an "
                 "unmounted creature smaller than your mount. Force an attack on your mount to "
                 "target you instead. Your mount takes no damage on a successful DEX save (half on "
                 "a failure) against an effect that normally halves damage on success."),

    feat('Observant', 'PHB', asi_flex=['INT', 'WIS'],
         special="+1 INT or WIS (max 20). If you can see a creature's mouth while it speaks a "
                 "language you understand, you can read its lips. +5 to passive WIS (Perception) "
                 "and passive INT (Investigation)."),

    feat('Polearm Master', 'PHB',
         special="Attacking with only a glaive/halberd/quarterstaff/spear: bonus action attack "
                 "with the weapon's other end (same ability modifier, 1d4 bludgeoning). While "
                 "wielding a glaive/halberd/pike/quarterstaff/spear, other creatures provoke an "
                 "opportunity attack from you on entering your reach."),

    feat('Resilient', 'PHB', asi_flex=['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'],
         special="+1 to a chosen ability (max 20). Gain proficiency in saving throws using that ability."),

    feat('Ritual Caster', 'PHB', prereq='INT or WIS 13+',
         special="Gain a ritual book with two 1st-level ritual-tagged spells from a chosen class "
                 "list (bard/cleric/druid/sorcerer/warlock/wizard). Spellcasting ability matches "
                 "that class. Can add further ritual spells found in writing (level \u2264 half your "
                 "level rounded up) for 2 hrs + 50 gp per spell level."),

    feat('Savage Attacker', 'PHB',
         special="Once per turn, when you roll damage for a melee weapon attack, reroll the "
                 "weapon's damage dice and use either total."),

    feat('Sentinel', 'PHB',
         special="Hitting with an opportunity attack reduces the target's speed to 0 for the rest "
                 "of the turn. Creatures provoke your opportunity attacks even after Disengaging. "
                 "Reaction: when a creature within 5 ft. attacks a target other than you (who "
                 "doesn't have this feat), melee attack the attacker."),

    feat('Sharpshooter', 'PHB',
         special="No disadvantage at long range. Ranged weapon attacks ignore half and "
                 "three-quarters cover. Before attacking with a proficient ranged weapon, take -5 "
                 "to the attack roll for +10 damage on a hit."),

    feat('Shield Master', 'PHB',
         special="While wielding a shield: if you took the Attack action, bonus action to shove a "
                 "creature within 5 ft. If not incapacitated, add your shield's AC bonus to a DEX "
                 "save against an effect targeting only you. Reaction on a successful DEX save "
                 "that would halve damage: take no damage instead, interposing your shield."),

    feat('Skilled', 'PHB',
         special="Gain proficiency in any combination of three skills or tools of your choice."),

    feat('Skulker', 'PHB', prereq='DEX 13+',
         special="Can attempt to hide when only lightly obscured from the searcher. Missing with "
                 "a ranged attack while hidden doesn't reveal your position. Dim light doesn't "
                 "impose disadvantage on sight-based WIS (Perception)."),

    feat('Spell Sniper', 'PHB', prereq='Spellcasting',
         special="Attack-roll spells you cast have doubled range. Ranged spell attacks ignore "
                 "half and three-quarters cover. Learn one attack-roll cantrip from the bard/"
                 "cleric/druid/sorcerer/warlock/wizard list (spellcasting ability matches that list)."),

    feat('Tavern Brawler', 'PHB', asi_flex=['STR', 'CON'],
         special="+1 STR or CON (max 20). Proficiency with improvised weapons. Unarmed strikes "
                 "deal 1d4. Hitting with an unarmed strike or improvised weapon lets you bonus "
                 "action attempt to grapple the target."),

    feat('Tough', 'PHB',
         special="HP max increases by twice your level immediately on taking this feat, and by an "
                 "additional 2 every level thereafter."),

    feat('War Caster', 'PHB', prereq='Spellcasting',
         special="Advantage on CON saves to maintain concentration when damaged. Perform somatic "
                 "components with weapons/a shield in hand. Reaction to cast a spell (1-action "
                 "casting time, targeting only the provoking creature) instead of an opportunity attack."),

    feat('Weapon Master', 'PHB', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). Gain proficiency with four simple or martial weapons of "
                 "your choice."),

    feat('Crusher', 'TCE', asi_flex=['STR', 'CON'],
         special="+1 STR or CON (max 20). Once per turn on a bludgeoning-damage hit, move the "
                 "target 5 ft. to an unoccupied space (no more than one size larger than you). A "
                 "bludgeoning critical hit grants advantage on attacks against that target until "
                 "the start of your next turn."),

    feat('Fey Touched', 'TCE', asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Learn misty step and one 1st-level divination or "
                 "enchantment spell; cast each once free per long rest (or with a spell slot). "
                 "Spellcasting ability is the one increased."),

    feat('Fighting Initiate', 'TCE', prereq='Prof. martial weapon',
         special="Learn one Fighter Fighting Style (must differ from any you already have). "
                 "Replaceable with a different one whenever you gain an ASI-granting level."),

    feat('Gunner', 'TCE', asi={'DEX': 1},
         special="+1 DEX (max 20). Proficiency with firearms. Ignore the Loading property on "
                 "firearms. No disadvantage on ranged attacks within 5 ft. of a hostile creature."),

    feat('Metamagic Adept', 'TCE', prereq='Spellcasting',
         special="Learn two Sorcerer Metamagic options (only one usable per spell unless it says "
                 "otherwise; replaceable on an ASI-granting level). Gain 2 sorcery points usable "
                 "only on Metamagic, regained on a long rest."),

    feat('Piercer', 'TCE', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). Once per turn on a piercing-damage hit, reroll one "
                 "damage die and use the new result. A piercing critical hit adds one extra "
                 "damage die."),

    feat('Poisoner', 'TCE',
         special="Poison damage you deal ignores resistance. Applying poison to a weapon/"
                 "ammunition is a bonus action instead of an action. Gain poisoner's kit "
                 "proficiency; with 1 hour of work and 50 gp of materials, craft a number of "
                 "potent-poison doses = your proficiency bonus. Applied poison lasts 1 minute or "
                 "until it hits; a creature damaged by it makes a DC 14 CON save or takes 2d8 "
                 "poison damage and is poisoned until the end of your next turn."),

    feat('Shadow Touched', 'TCE', asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Learn invisibility and one 1st-level illusion or "
                 "necromancy spell; cast each once free per long rest (or with a spell slot). "
                 "Spellcasting ability is the one increased."),

    feat('Skill Expert', 'TCE', asi_flex=['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'],
         special="+1 to a chosen ability (max 20). Gain proficiency in one skill of your choice, "
                 "and expertise (double proficiency bonus) in one skill you're already proficient "
                 "in (that isn't already doubled by something else)."),

    feat('Slasher', 'TCE', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). Once per turn on a slashing-damage hit, reduce the "
                 "target's speed by 10 ft. until the start of your next turn. A slashing critical "
                 "hit gives the target disadvantage on all attack rolls until the start of your "
                 "next turn."),

    feat('Telekinetic', 'TCE', asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Learn mage hand (no verbal/somatic components; the "
                 "spectral hand can be invisible; +30 ft. range if already known). Bonus action: "
                 "telekinetically shove a creature within 30 ft. — STR save (DC 8 + proficiency "
                 "bonus + the increased ability's modifier) or move 5 ft. toward or away from you "
                 "(a creature can willingly fail)."),

    feat('Telepathic', 'TCE', asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Speak telepathically to any creature you can see within "
                 "60 ft. (in a language you know; it must know that language to understand you; no "
                 "telepathic reply). Cast detect thoughts once free per long rest (or with a 2nd-"
                 "level+ slot); spellcasting ability is the one increased."),

    # ── Xanathar's Guide to Everything (racial feats) ────────────────────────
    feat('Bountiful Luck', 'XGE', prereq='Halfling',
         special="Reaction: when an ally within 30 ft. rolls a 1 on an attack roll/check/save, "
                 "let them reroll (they must use the new roll). Using this disables your own Lucky "
                 "racial trait until the end of your next turn."),

    feat('Dragon Fear', 'XGE', prereq='Dragonborn', asi_flex=['STR', 'CON', 'CHA'],
         special="+1 STR/CON/CHA (max 20). In place of your Breath Weapon, roar: each creature you "
                 "choose within 30 ft. makes a WIS save (DC 8 + proficiency bonus + CHA modifier; "
                 "automatic success if it can't see/hear you) or is frightened of you for 1 minute "
                 "(repeatable save on taking damage)."),

    feat('Dragon Hide', 'XGE', prereq='Dragonborn', asi_flex=['STR', 'CON', 'CHA'],
         special="+1 STR/CON/CHA (max 20). Unarmored AC = 13 + DEX modifier (shield still usable). "
                 "Grow retractable claws (no action to extend/retract) usable as natural weapons: "
                 "1d4 + STR modifier slashing on an unarmed strike instead of the normal bludgeoning."),

    feat('Drow High Magic', 'XGE', prereq='Elf (drow)',
         special="Cast detect magic at will, no spell slot. Cast levitate and dispel magic each "
                 "once without a spell slot, regained on a long rest. CHA is the spellcasting "
                 "ability for all three."),

    feat('Dwarven Fortitude', 'XGE', prereq='Dwarf', asi={'CON': 1},
         special="+1 CON (max 20). Taking the Dodge action lets you spend a Hit Die: roll it, add "
                 "CON modifier, regain that many HP (min 1)."),

    feat('Elven Accuracy', 'XGE', prereq='Elf or Half-Elf', asi_flex=['DEX', 'INT', 'WIS', 'CHA'],
         special="+1 DEX/INT/WIS/CHA (max 20). Whenever you have advantage on an attack roll using "
                 "DEX, INT, WIS, or CHA, reroll one of the two dice once."),

    feat('Fade Away', 'XGE', prereq='Gnome', asi_flex=['DEX', 'INT'],
         special="+1 DEX or INT (max 20). Reaction immediately after taking damage: become "
                 "invisible until the end of your next turn or until you attack, deal damage, or "
                 "force a save. Once per short or long rest."),

    feat('Fey Teleportation', 'XGE', prereq='Elf (high)', asi_flex=['INT', 'CHA'],
         special="+1 INT or CHA (max 20). Learn Sylvan. Cast misty step once without a spell slot, "
                 "regained on a short or long rest. INT is the spellcasting ability."),

    feat('Flames of Phlegethos', 'XGE', prereq='Tiefling', asi_flex=['INT', 'CHA'],
         special="+1 INT or CHA (max 20). Reroll any 1s on fire-damage dice from your spells (must "
                 "use the new roll, even another 1). Casting a fire-damage spell wreathes you in "
                 "flame until the end of your next turn (bright light 30 ft./dim 30 ft. more; a "
                 "creature that hits you with a melee attack from within 5 ft. takes 1d4 fire)."),

    feat('Infernal Constitution', 'XGE', prereq='Tiefling', asi={'CON': 1},
         special="+1 CON (max 20). Resistance to cold and poison damage. Advantage on saves "
                 "against being poisoned."),

    feat('Orcish Fury', 'XGE', prereq='Half-Orc', asi_flex=['STR', 'CON'],
         special="+1 STR or CON (max 20). Hitting with a simple/martial weapon: reroll one damage "
                 "die and add it as extra damage (once per short or long rest). Immediately after "
                 "using Relentless Endurance: reaction to make one weapon attack."),

    feat('Prodigy', 'XGE', prereq='Half-Elf, Half-Orc, or Human',
         special="Gain one skill proficiency, one tool proficiency, and fluency in one language, "
                 "all of your choice. Gain expertise (double proficiency bonus) in one skill "
                 "you're already proficient in (not already doubled by another feature)."),

    feat('Second Chance', 'XGE', prereq='Halfling', asi_flex=['DEX', 'CON', 'CHA'],
         special="+1 DEX/CON/CHA (max 20). Reaction when a creature you can see hits you with an "
                 "attack roll: force it to reroll. Once per combat (until you roll initiative "
                 "again) or until you finish a short or long rest."),

    feat('Squat Nimbleness', 'XGE', prereq='Dwarf or a Small race', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). +5 ft. walking speed. Gain proficiency in Acrobatics or "
                 "Athletics (choice). Advantage on STR (Athletics)/DEX (Acrobatics) checks to "
                 "escape a grapple."),

    feat('Svirfneblin Magic', 'MTF', prereq='Gnome (deep)',
         special="Cast nondetection on yourself at will, no material component. Cast blindness/"
                 "deafness, blur, and disguise self each once, regained on a long rest. INT is the "
                 "spellcasting ability; all cast at their lowest level."),

    feat('Wood Elf Magic', 'XGE', prereq='Elf (wood)',
         special="Learn one druid cantrip. Learn longstrider and pass without trace, each "
                 "castable once without a spell slot, regained on a long rest. WIS is the "
                 "spellcasting ability for all three."),

    feat('Artificer Initiate', 'TCE',
         special="Learn one artificer cantrip and one 1st-level artificer spell (castable once "
                 "free per long rest, or with a spell slot). INT is the spellcasting ability. Gain "
                 "proficiency with one type of artisan's tools, usable as a spellcasting focus for "
                 "INT-based spells you cast."),

    feat('Chef', 'TCE', asi_flex=['CON', 'WIS'],
         special="+1 CON or WIS (max 20). Gain cook's utensils proficiency. Short rest + "
                 "ingredients/utensils: cook food for 4 + proficiency bonus creatures — eating it "
                 "and spending a Hit Die to heal grants +1d8 extra HP. 1 hour of work or a long "
                 "rest: cook proficiency-bonus treats (last 8 hrs); a creature can bonus-action eat "
                 "one for temp HP = your proficiency bonus."),

    feat('Eldritch Adept', 'TCE', prereq='Spellcasting or Pact Magic',
         special="Learn one Warlock Eldritch Invocation (spellcasting ability: INT/WIS/CHA, your "
                 "choice; invocations with prerequisites require you to actually be a qualifying "
                 "warlock). Replaceable with a different invocation whenever you gain a level."),

    feat('Revenant Blade', 'ERLW', prereq='Elf', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). +1 AC while holding a double-bladed scimitar with two "
                 "hands. A double-bladed scimitar has the finesse property when you wield it."),

    # ── Eberron: Rising from the Last War ─────────────────────────────────────
    feat('Aberrant Dragonmark', 'ERLW', prereq='No other dragonmark', asi={'CON': 1},
         special="+1 CON (max 20). Learn one sorcerer cantrip and one 1st-level sorcerer spell, "
                 "castable through your mark once per short or long rest (or with a spell slot); "
                 "CON is the spellcasting ability. When cast through the mark, you can expend a "
                 "Hit Die and roll it: even = gain that many temp HP; odd = a random creature "
                 "within 30 ft. (not you) takes that much force damage, or you take it if none in "
                 "range. You also gain a random flaw (Aberrant Dragonmark Flaws table, d8)."),

    # ── Astral Adventurer's Guide ─────────────────────────────────────────────
    feat('Scion of the Outer Planes', 'AAG', prereq='Planescape Campaign',
         special="Choose a plane type (Chaotic/Evil/Good/Lawful Outer Plane, or the Outlands). "
                 "Gain resistance to a fixed damage type and a fixed cantrip per the Planar "
                 "Infusion table: Chaotic = poison/minor illusion, Evil = necrotic/chill touch, "
                 "Good = radiant/sacred flame, Lawful = force/guidance, Outlands = psychic/mage "
                 "hand. Cast the cantrip with no material components; spellcasting ability is "
                 "INT, WIS, or CHA (choose when you take this feat)."),

    feat('Agent of Order', 'SatO', prereq='4th level, Scion of the Outer Planes (lawful plane)',
         asi_flex=['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'],
         special="+1 to any ability (max 20). Once per turn on damaging a creature within 60 ft. "
                 "you can see, deal +1d8 force damage and force a WIS save (DC 8 + proficiency "
                 "bonus + your Scion spellcasting modifier) or spectral bindings restrain it until "
                 "the start of your next turn. Uses = proficiency bonus per long rest."),

    feat('Baleful Scion', 'SatO', prereq='4th level, Scion of the Outer Planes (evil plane)',
         asi_flex=['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'],
         special="+1 to any ability (max 20). Once per turn on damaging a creature within 60 ft. "
                 "you can see, also deal 1d6 + proficiency bonus necrotic damage and regain that "
                 "much HP. Uses = proficiency bonus per long rest."),

    feat('Cohort of Chaos', 'SatO', prereq='4th level, Scion of the Outer Planes (chaotic plane)',
         asi_flex=['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'],
         special="+1 to any ability (max 20). Rolling a 1 or 20 on an attack roll or save triggers "
                 "a random Chaotic Flare (d4) lasting until the end of your next turn (a new one "
                 "can't start until the current one ends): (1) Battle Fury — a chosen creature you "
                 "can see gets advantage on attacks, disadvantage on ability checks; (2) Disruption "
                 "Field — creatures starting their turn within 5 ft. of you (or moving into that "
                 "range) take 1d8 force damage; (3) Unbound — you can teleport using your walking "
                 "speed once when you move; (4) Wailing Winds — a 15-ft. sphere centered on you "
                 "gives disadvantage on WIS saves to you and others in it."),

    feat('Outlands Envoy', 'SatO', prereq='4th level, Scion of the Outer Planes (the Outlands)',
         asi_flex=['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'],
         special="+1 to any ability (max 20). Learn misty step and tongues (no material components "
                 "for tongues); cast each once free per long rest (or with a spell slot). "
                 "Spellcasting ability is your Scion of the Outer Planes ability."),

    feat('Planar Wanderer', 'SatO', prereq='4th level, Scion of the Outer Planes',
         special="On finishing a long rest, choose acid/cold/fire resistance until your next long "
                 "rest. Action: DC 20 INT (Arcana) check to force open/closed a portal within 5 ft. "
                 "you're aware of, for 1 hour, without its key (fail: 3d8 psychic damage, can't "
                 "retry on that portal until a long rest; a key-holder needs a DC 20 INT (Arcana) "
                 "action to override it during that hour). Know the direction to the last planar "
                 "portal you used while on its plane; action (usable once until a long rest): "
                 "detect any portals within 30 ft. not behind total cover."),

    feat('Righteous Heritor', 'SatO', prereq='4th level, Scion of the Outer Planes (good plane)',
         asi_flex=['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'],
         special="+1 to any ability (max 20). Reaction when you or a creature within 30 ft. takes "
                 "damage: reduce it by 1d10 + proficiency bonus. Uses = proficiency bonus per long rest."),

    # ── Strixhaven: A Curriculum of Chaos ─────────────────────────────────────
    feat('Strixhaven Initiate', 'SCC',
         special="Choose a college (Lorehold/Prismari/Quandrix/Silverquill/Witherbloom). Learn "
                 "two cantrips and one 1st-level spell per its list (Lorehold: light/sacred flame/"
                 "thaumaturgy + cleric or wizard 1st; Prismari: fire bolt/prestidigitation/ray of "
                 "frost + bard or sorcerer 1st; Quandrix: druidcraft/guidance/mage hand + druid or "
                 "wizard 1st; Silverquill: sacred flame/thaumaturgy/vicious mockery + bard or "
                 "cleric 1st; Witherbloom: chill touch/druidcraft/spare the dying + druid or wizard "
                 "1st). Cast the 1st-level spell once free per long rest (or with a slot). "
                 "Spellcasting ability: INT, WIS, or CHA (choose when you take this feat)."),

    feat('Strixhaven Mascot', 'SCC', prereq='4th level, Strixhaven Initiate',
         special="Cast find familiar as a ritual; the familiar can take the form of your college's "
                 "mascot (Lorehold: spirit statue, Prismari: art elemental, Quandrix: fractal, "
                 "Silverquill: inkling, Witherbloom: pest). When you take the Attack action, forgo "
                 "one attack to let your mascot familiar make a reaction attack. Action: if the "
                 "familiar is within 60 ft., teleport to swap places with it (fails/wasted if your "
                 "destination is too small). Once per long rest, or again by expending a 2nd-level+ "
                 "spell slot."),

    # ── Dragonlance: Shadow of the Dragon Queen ────────────────────────────────
    feat('Divinely Favored', 'DSotDQ', prereq='4th level, Dragonlance Campaign',
         special="Learn one cleric cantrip, augury, and one 1st-level spell by alignment (Evil: a "
                 "warlock 1st-level spell; Good: a cleric 1st-level spell; Neutral: a druid "
                 "1st-level spell). Cast the chosen 1st-level spell and augury each once free per "
                 "long rest (or with a slot). Spellcasting ability: INT, WIS, or CHA (choose when "
                 "you take this feat). Use a holy symbol as a focus for spells using that ability."),

    feat('Initiate of High Sorcery', 'DSotDQ',
         prereq='Dragonlance Campaign; Sorcerer, Wizard, or Mage of High Sorcery',
         special="Choose a moon of Krynn (Nuitari/Lunitari/Solinari). Learn one wizard cantrip and "
                 "two 1st-level spells per the Lunar Spells table (Nuitari: choose two from "
                 "dissonant whispers/false life/hex/ray of sickness; Lunitari: choose two from "
                 "color spray/disguise self/feather fall/longstrider; Solinari: choose two from "
                 "comprehend languages/detect evil and good/protection from evil and good/shield). "
                 "Cast each chosen 1st-level spell once free per long rest (or with a slot). "
                 "Spellcasting ability: INT, WIS, or CHA (choose when you take this feat)."),

    feat('Adept of the Black Robes', 'DSotDQ', prereq='4th level, Initiate of High Sorcery (Nuitari)',
         special="Learn one 2nd-level enchantment or necromancy spell; cast it once free per long "
                 "rest (or with a slot appropriate to its level); spellcasting ability matches "
                 "Initiate of High Sorcery. Life Channel: when a creature you can see within 60 ft. "
                 "fails a save against a damaging spell you cast, expend Hit Dice equal to the "
                 "spell's level, roll and total them, and add that much extra damage."),

    feat('Adept of the Red Robes', 'DSotDQ', prereq='4th level, Initiate of High Sorcery (Lunitari)',
         special="Learn one 2nd-level illusion or transmutation spell; cast it once free per long "
                 "rest (or with a slot appropriate to its level); spellcasting ability matches "
                 "Initiate of High Sorcery. Magical Balance: when you roll 9 or lower on an attack "
                 "roll or ability check, treat it as a 10. Uses = proficiency bonus per long rest."),

    feat('Adept of the White Robes', 'DSotDQ', prereq='4th level, Initiate of High Sorcery (Solinari)',
         special="Learn one 2nd-level abjuration or divination spell; cast it once free per long "
                 "rest (or with a slot appropriate to its level); spellcasting ability matches "
                 "Initiate of High Sorcery. Protective Ward: reaction when you or a creature within "
                 "30 ft. takes damage — expend a spell slot and roll d6s equal to its level, "
                 "reducing the damage by the total + your spellcasting ability modifier."),

    feat('Squire of Solamnia', 'DSotDQ', prereq='Dragonlance Campaign; Fighter, Paladin, or Knight of Solamnia',
         special="Mounting/dismounting costs only 5 ft. of movement. Once per turn on a weapon "
                 "attack roll, give it advantage; if it hits, roll a d8 and add it to the damage "
                 "(use expended only on a hit). Uses = proficiency bonus per long rest."),

    feat('Knight of the Crown', 'DSotDQ', prereq='4th level, Squire of Solamnia', asi_flex=['STR', 'DEX', 'CON'],
         special="+1 STR/DEX/CON (max 20). Bonus action: command an ally within 30 ft. who can see/"
                 "hear you to attack as a reaction; on a hit, they add 1d8 to the damage. Uses = "
                 "proficiency bonus per long rest."),

    feat('Knight of the Rose', 'DSotDQ', prereq='4th level, Squire of Solamnia', asi_flex=['CON', 'WIS', 'CHA'],
         special="+1 CON/WIS/CHA (max 20). Bonus action: a creature you can see within 30 ft. "
                 "(including yourself) who can see/hear you gains temp HP = 1d8 + proficiency bonus "
                 "+ the increased ability's modifier. Uses = proficiency bonus per long rest."),

    feat('Knight of the Sword', 'DSotDQ', prereq='4th level, Squire of Solamnia', asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Once per turn on a weapon attack hit, force a WIS save "
                 "(DC 8 + proficiency bonus + the increased ability's modifier) or frighten the "
                 "target until the end of your next turn (on a success, it has disadvantage on its "
                 "next attack before the end of its next turn). Uses = proficiency bonus per long rest."),

    # ── The Book of Many Things ──────────────────────────────────────────────
    feat('Cartomancer', 'BMT', prereq='4th level, Spellcasting',
         special="Use a card deck as a spellcasting focus. Learn prestidigitation, usable to "
                 "disguise its verbal/somatic components as ordinary conversation and card "
                 "handling. On finishing a long rest, imbue a card with one action-casting-time "
                 "spell you have a slot for from your class list; bonus action to flourish and "
                 "cast it (the card loses its magic after), lasting 8 hours if unused."),

    # ── Fizban's Treasury of Dragons ──────────────────────────────────────────
    feat('Gift of the Chromatic Dragon', 'FTD',
         special="Bonus action: infuse a weapon you touch with acid/cold/fire/lightning/poison "
                 "for 1 minute, adding 1d4 of that type on a hit (once per long rest). Reaction "
                 "when you take acid/cold/fire/lightning/poison damage: gain resistance to that "
                 "instance. Uses = proficiency bonus per long rest."),

    feat('Gift of the Gem Dragon', 'FTD', asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Reaction when a creature within 10 ft. damages you: it "
                 "makes a STR save (DC 8 + proficiency bonus + the increased ability's modifier) "
                 "or takes 2d8 force damage and is pushed 10 ft. (half damage, no push on a "
                 "success). Uses = proficiency bonus per long rest."),

    feat('Gift of the Metallic Dragon', 'FTD',
         special="Learn cure wounds, castable once free per long rest (or with a slot); "
                 "spellcasting ability: INT, WIS, or CHA (choose when you take this feat). Reaction "
                 "when you or a creature within 5 ft. is hit: manifest spectral wings, granting +"
                 "proficiency bonus to the target's AC against that attack. Uses = proficiency "
                 "bonus per long rest."),

    # ── Bigby Presents: Glory of the Giants ──────────────────────────────────
    feat('Strike of the Giants', 'BGG', prereq='Prof. martial weapons or Giant Foundling',
         special="Choose a benefit; once per turn on a melee hit (or a thrown-weapon ranged hit), "
                 "imbue it: Cloud (+1d4 thunder; on a failed WIS save the target can't see you "
                 "until you attack/cast or your next turn starts), Fire (+1d10 fire), Frost (+1d6 "
                 "cold; failed CON save reduces speed to 0 until your next turn), Hill (+1d6 of "
                 "the weapon's type; failed STR save = prone), Stone (+1d6 force; failed STR save "
                 "= pushed 10 ft.), Storm (+1d6 lightning; failed CON save = disadvantage on "
                 "attacks until your next turn). Save DC = 8 + proficiency bonus + STR or CON "
                 "modifier. Uses = proficiency bonus per long rest."),

    feat('Ember of the Fire Giant', 'BGG', prereq='4th level, Strike of the Giants (fire)',
         asi_flex=['STR', 'CON', 'WIS'],
         special="+1 STR/CON/WIS (max 20). Resistance to fire damage. In place of one Attack, "
                 "burst flame in a 15-ft. sphere centered on you: DEX save (DC 8 + proficiency "
                 "bonus + the increased ability's modifier) or 1d8 + proficiency bonus fire "
                 "damage and blinded until your next turn (half damage only on a success). Uses = "
                 "proficiency bonus per long rest (max once/turn)."),

    feat('Fury of the Frost Giant', 'BGG', prereq='4th level, Strike of the Giants (frost)',
         asi_flex=['STR', 'CON', 'WIS'],
         special="+1 STR/CON/WIS (max 20). Resistance to cold damage. Reaction immediately after a "
                 "creature within 30 ft. hits and damages you: it makes a CON save (DC 8 + "
                 "proficiency bonus + the increased ability's modifier) or takes 1d8 + proficiency "
                 "bonus cold damage and its speed is 0 until the end of its next turn. Uses = "
                 "proficiency bonus per long rest."),

    feat('Guile of the Cloud Giant', 'BGG', prereq='4th level, Strike of the Giants (cloud)',
         asi_flex=['STR', 'CON', 'CHA'],
         special="+1 STR/CON/CHA (max 20). Reaction when hit by an attack roll: gain resistance to "
                 "that damage, then teleport to an unoccupied space you can see within 30 ft. Uses "
                 "= proficiency bonus per long rest."),

    feat('Keenness of the Stone Giant', 'BGG', prereq='4th level, Strike of the Giants (stone)',
         asi_flex=['STR', 'CON', 'WIS'],
         special="+1 STR/CON/WIS (max 20). Darkvision 60 ft. (or +60 ft. range if you already have it). "
                 "Bonus action: ranged spell attack with a rock, range 60 ft., using the increased "
                 "ability as the spellcasting ability — 1d10 force damage and STR save (DC 8 + "
                 "proficiency bonus + that modifier) or prone. Uses = proficiency bonus per long rest."),

    feat('Soul of the Storm Giant', 'BGG', prereq='4th level, Strike of the Giants (storm)',
         asi_flex=['STR', 'WIS', 'CHA'],
         special="+1 STR/WIS/CHA (max 20). Bonus action: 10-ft. aura of wind and lightning until "
                 "the start of your next turn (or until incapacitated) that doesn't pass total "
                 "cover; while active you resist lightning/thunder, attackers have disadvantage "
                 "against you, and a creature starting its turn in the aura makes a STR save (DC 8 "
                 "+ proficiency bonus + the increased ability's modifier) or its speed is halved "
                 "until the start of its next turn. Uses = proficiency bonus per long rest."),

    feat('Vigor of the Hill Giant', 'BGG', prereq='4th level, Strike of the Giants (hill)',
         asi_flex=['STR', 'CON', 'WIS'],
         special="+1 STR/CON/WIS (max 20). Reaction when subjected to an effect that would move "
                 "you 5+ ft. or knock you prone: negate it, staying put and standing. Eating during "
                 "a short rest and spending Hit Dice to heal restores extra HP = CON modifier + "
                 "proficiency bonus."),

    feat('Rune Shaper', 'BGG', prereq='Spellcasting or Rune Carver',
         special="Learn comprehend languages, castable once free per long rest (or with a slot). "
                 "Know a number of runes = half your proficiency bonus (rounded down), each of "
                 "which corresponds to a 1st-level spell (Cloud=fog cloud, Death=inflict wounds, "
                 "Dragon=chromatic orb, Enemy=disguise self, Fire=burning hands, Friend=speak with "
                 "animals, Frost=armor of Agathys, Hill=goodberry, Journey=longstrider, King="
                 "command, Mountain=entangle, Stone=sanctuary, Storm=thunderwave). On a long rest, "
                 "inscribe each known rune onto a touched object, temporarily learning its spell "
                 "until your next long rest, castable with a spell slot while carrying the object; "
                 "you can also invoke an inscribed rune's spell once free per long rest without "
                 "components. Spellcasting ability: INT, WIS, or CHA (choose when you take this "
                 "feat). Replace one known rune with another on each level gained."),

    # ── Sigil and the Outlands ────────────────────────────────────────────────
    # (see Scion of the Outer Planes and its 6 follow-up feats above)

    # ── Expanded-content feats (round 1, non-Middle-Earth) ──────────────────────
    feat('Adroit Crafter', 'CRB', prereq="Proficiency in a skill or tool",
         special="Halve the time to craft an item using a proficient skill/tool. If you'd fail "
                 "and lose the components, keep them instead."),

    feat('Aerial Expert', 'CRB', prereq="Glide trait",
         special="Long/high jumps no longer need a 10 ft. running start (choose STR or DEX for "
                 "the jump, double the normal distance). Dash while gliding for extra distance up "
                 "to your speed. Change direction freely while gliding; gain up to 10 ft. of "
                 "altitude once before your descent ends."),

    feat('Bandit Cunning', 'CRB',
         special="Reaction: add your INT modifier to a saving throw you're making (once per long "
                 "rest). Action: INT (Investigation) check (DC 10 + a creature's CR you've seen "
                 "fight) to learn one useful fact about it — a damage resistance/immunity, a "
                 "condition immunity, a damage-related special ability, an attack/legendary/"
                 "reaction option, or a special sense."),

    feat('Blade Barrier', 'CRB', prereq="Proficiency with twinblades",
         special="Using the Whirl bonus action with a twinblade: make one additional melee attack "
                 "(same ability modifier, 1d4 damage die). Until the start of your next turn, "
                 "creatures provoke an opportunity attack from you for entering your reach or "
                 "making a melee attack against you within it."),

    feat('Careful Crafter', 'CRB', prereq="Proficiency in a skill or tool",
         special="Advantage on all crafting ability checks; anyone assisting you also gets "
                 "advantage on theirs. If you fail to craft the item, the time it took is halved."),

    feat("Cat's Caress", 'CRB', prereq="Proficiency with claw",
         special="After using the Attack action with a claw in one hand: bonus action, up to two "
                 "melee attacks with a different claw in the other hand (no ability modifier to "
                 "the bonus attacks' damage unless negative, or you have Two-Weapon Fighting "
                 "Style). Advantage to hit a target you're grappling with a claw. Equip/unequip "
                 "one or a pair of claws as a bonus action or action."),

    feat('Cruel', 'CRB',
         special="Gain d6 cruelty dice = proficiency bonus, regained on a long rest, one rollable "
                 "per turn. Spend one: on damaging a creature, add the roll as extra damage; on a "
                 "critical hit, gain that many temp HP instead; on a CHA (Intimidation) check, add "
                 "the roll to it."),

    feat('Expert Enchanter', 'CRB', asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Double proficiency bonus on Enchanting checks with a "
                 "proficient skill. Apply ±half your proficiency bonus to enchanting quirk rolls. "
                 "Each hour spent enchanting counts as 2 hours toward completion."),

    feat('Expert Forger', 'CRB', asi_flex=['STR', 'DEX', 'CON'],
         special="+1 STR/DEX/CON (max 20). Double proficiency bonus on Manufacturing checks with a "
                 "proficient tool. Apply ±half your proficiency bonus to forging quirk rolls. Each "
                 "hour spent forging counts as 2 hours toward completion."),

    feat('Expert Harvester', 'CRB', asi_flex=['DEX', 'INT'],
         special="+1 DEX or INT (max 20). Double proficiency bonus on Harvesting checks with a "
                 "proficient skill. Add your proficiency bonus even without the required skill. "
                 "Helping another's Harvesting check adds your full proficiency bonus regardless "
                 "of proficiency. No disadvantage for doing Assessment and Carving checks alone."),

    feat('Fearsome Flourisher', 'CRB', prereq="Proficiency with nunchaku",
         special="Attacking with a nunchaku: bonus action, one additional melee attack (same "
                 "ability modifier, 1d4 damage die). Flourishing a nunchaku: bonus action to make "
                 "it intimidating — on a successful DEX check, target makes a WIS save (DC 8 + DEX "
                 "modifier, +proficiency bonus if proficient in Intimidation) or is frightened "
                 "until the start of your next turn."),

    feat('Field Cook', 'CRB',
         special="Gain cook's utensils proficiency. Substitute any ingredient type for another in "
                 "a recipe. Before rolling quirks, replace one boon-table roll with granting "
                 "inspiration to anyone who eats a portion. After rolling quirks, remove one flaw "
                 "or add a boon (your choice)."),

    feat('Field Medic', 'CRB',
         special="See at a glance if a creature is missing HP, and whether it's above/below half. "
                 "Advantage on WIS (Medicine)/INT (Arcana or Religion) checks to identify a curse, "
                 "disease, possession, or blinded/deafened/exhaustion/incapacitated/paralyzed/"
                 "poisoned. Learn spare the dying, castable as a bonus action. Cast cure wounds "
                 "without a slot, uses = half proficiency bonus per long rest; WIS is the "
                 "spellcasting ability."),

    feat('Flamewoken', 'TENDERS',
         special="Speak/read/write Ignan. Learn produce flame (CHA is the spellcasting ability). "
                 "Bonus action: empower your flames — the next fire damage you deal to a creature "
                 "before the end of your next turn adds +2d10 fire (once per short or long rest). "
                 "Bonus action: whisper to nonmagical flames within 30 ft. (fitting a 5-ft. cube) "
                 "to grow 5 ft. in one direction (needs fuel there) or extinguish."),

    feat('Flash Recall', 'STRIX', prereq="Spellcasting feature from a class that prepares spells",
         special="Bonus action: prepare a 1st-level+ spell (from your spellbook if a Wizard, "
                 "otherwise your class list) of a level you have slots for, replacing an "
                 "equal-or-higher-level prepared spell. Once per short or long rest. Only for "
                 "classes that prepare spells (Cleric/Druid/Paladin/Wizard, not Bard/Sorcerer)."),

    feat('Forest Sage', 'TENDERS', prereq="Druid or Wizard", asi_flex=['INT', 'WIS'],
         special="+1 INT or WIS (max 20). Use INT or WIS (your choice) for Animal Handling, "
                 "Arcana, Nature, or Survival checks. Learn two spells from the druid or wizard "
                 "list (of a level you can cast) as spells of your class."),

    feat('Forgemaster', 'CRB', prereq="Expert Forger", asi_flex=['STR', 'DEX', 'CON'],
         special="+1 STR/DEX/CON (max 20). Advantage on Manufacturing checks with a proficient "
                 "tool. Gain proficiency with 2 tools of your choice. Each hour spent forging "
                 "counts as 3 hours toward completion."),

    feat('Heavy Glider', 'CRB', prereq="Glide trait",
         special="Can glide while holding a heavy weapon and wearing heavy armor, as long as "
                 "you're not encumbered. Can land your glide in a Large-or-smaller hostile "
                 "creature's space: opposed STR check — success pushes it 10 ft. and knocks it "
                 "prone; failure lands you in the nearest unoccupied space instead."),

    # ── Expanded-content feats (round 3, non-Middle-Earth) ──────────────────────

    feat('Jack of All Tools', 'CRB', asi_flex=['STR', 'DEX', 'CON'],
         special="+1 STR/DEX/CON (max 20). Gain proficiency with 3 tools. Manufacturing checks "
                 "with a non-proficient tool add half your proficiency bonus and ignore the usual "
                 "disadvantage. Each hour spent manufacturing counts as 2 hours toward completion."),

    feat('Mystic Conflux', 'CRB',
         special="Attune to up to 4 magic items at once. Cast identify without a slot or material "
                 "components, once per long rest."),

    feat('Opportunistic Thief', 'CRB', asi={'DEX': 1},
         special="+1 DEX (max 20). When a creature misses you with a melee attack: DEX (Sleight "
                 "of Hand) check (DC 10 + its DEX modifier) to steal an item it's not holding/"
                 "wearing. Outside combat, a successful Sleight of Hand theft lets you flawlessly "
                 "conceal the item or swap in a substitute instantly."),

    feat('Perfect Landing', 'CRB', asi={'DEX': 1},
         special="+1 DEX (max 20). Fall damage die becomes d4 (from d6). Don't fall prone from "
                 "fall damage. No damage from the first 30 ft. of a fall."),

    feat('Plantmender', 'TENDERS', prereq="WIS 13+",
         special="Action: touch a plant/tree to see visions of what happened to it and its "
                 "vicinity in the last 24 hrs, and learn its current health/blights. Uses = twice "
                 "WIS modifier (min 1) per long rest. Learn mend plants and shillelagh (WIS is the "
                 "spellcasting ability). Cast barkskin or spike growth once per long rest (WIS)."),

    feat('Reapmaster', 'CRB', prereq="Expert Harvester", asi_flex=['DEX', 'INT'],
         special="+1 DEX or INT (max 20). Gain proficiency in Arcana, Investigation, Medicine, "
                 "Nature, or Religion (choice). Advantage on Harvesting checks with a proficient skill."),

    feat('Remarkable Recovery', 'CRB', asi={'CON': 1},
         special="+1 CON (max 20). Stabilizing while dying also regains HP = CON modifier (min "
                 "1). Regaining HP from a spell/potion/class feature (not this feat) regains that "
                 "much extra HP again."),

    feat('Scourge Master', 'CRB', prereq="Proficiency with whip or tetherhooks",
         asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). Hitting with a tetherhooks/whip: bonus action, STR or "
                 "DEX check vs. the target's STR check to disarm a shield or held item, dropping "
                 "it between you. Use your whip/tetherhooks to pull a sub-1-lb. item within reach "
                 "back to yourself."),

    feat('Speech of the Ancient Beasts', 'CRB', asi={'CHA': 1},
         special="+1 CHA (max 20). Large-or-larger beasts are friendly to you unless attacked. "
                 "Advantage on CHA checks against Large-or-larger beasts. Speak/understand Giant "
                 "Eagle, Giant Elk, Giant Owl; any Large-or-larger beast can otherwise understand "
                 "you (INT 4-or-lower beasts only grasp simple concepts)."),

    feat('Spelldriver', 'CRB', prereq="11th level; Spellcasting or Pact Magic feature",
         special="When you cast a 1st-level+ spell as a bonus action, also cast another 1st-level+ "
                 "spell with your action that turn. If casting two-plus spells in one turn, at "
                 "most one can be 3rd level or higher."),

    feat("Spray 'n' Pray", 'CRB', prereq="Proficiency with a magitech firearm or tommybow",
         special="Reload firearms/tommybows as a bonus action or action. No disadvantage on "
                 "ranged attacks within 5 ft. of a hostile creature. Attack action with a "
                 "one-handed weapon: bonus action attack with a one-handed firearm/tommybow. "
                 "After attacking with a tommybow/magitech firearm: bonus action, 1-2 more ranged "
                 "attacks with it (two attacks = -5 to both; no ability modifier on the bonus "
                 "attacks' damage unless negative)."),

    feat('Thrown Arms Master', 'CRB', asi_flex=['STR', 'DEX'],
         special="+1 STR or DEX (max 20). Simple/martial melee weapons without the thrown "
                 "property gain it for you (one-handed: 20/60 ft.; two-handed: 15/30 ft.). "
                 "Weapons that already have it get +20/+40 ft. range. Missing with a thrown light "
                 "weapon: it boomerangs back to your hand at the end of your turn."),

    feat('Vital Sacrifice', 'CRB',
         special="Bonus action: take 1d6 necrotic damage (can't be reduced) for a blood boon "
                 "(lasts 1 hr. or until spent). Spend it: +1d6 on an attack roll; +2d6 necrotic "
                 "damage on a hit with an attack or spell; or reduce a creature's STR/DEX/CON "
                 "save by 1d4."),

    feat('Weavebonder', 'CRB', prereq="Expert Enchanter", asi_flex=['INT', 'WIS', 'CHA'],
         special="+1 INT/WIS/CHA (max 20). Advantage on Enchanting checks with a proficient skill. "
                 "Roll a quirk's random element twice and choose either result. Each hour spent "
                 "enchanting counts as 3 hours toward completion."),

    feat('Woodwise', 'CRB',
         special="Gain proficiency in Survival or Nature (choice). Ignore difficult terrain. Can't "
                 "become lost in natural surroundings except by magic."),
]

FEAT_NAMES = [f["name"] for f in ALL_FEATS]

def get_feat(name: str) -> dict:
    for f in ALL_FEATS:
        if f["name"] == name:
            return f
    return None

def feats_by_source() -> dict:
    result = {}
    for f in ALL_FEATS:
        src = f["source"]
        result.setdefault(src, []).append(f)
    return result
