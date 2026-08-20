"""
D&D 5e Races / Species Data
Covers PHB 2014, PHB 2024, Volo's, Mordenkainen's, Xanathar's, Tasha's,
Eberron, Wildemount, Spelljammer, Fizban's, Bigby's, Mythic Odysseys, GGR.
Each race entry: name, speed, size, asi (fixed), asi_flex (# free +1s),
traits (list of strings), languages, size_note, subraces (optional),
source.

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def race(name, speed=30, size="Medium", asi=None, asi_flex=0, traits=None,
         languages=None, source="PHB", notes="", subraces=None, asi_flex_style="distribute"):
    return dict(name=name, speed=speed, size=size,
                asi=asi or {}, asi_flex=asi_flex, asi_flex_style=asi_flex_style,
                traits=traits or [], languages=languages or ["Common"],
                source=source, notes=notes, subraces=subraces or [])


# ── All Races ─────────────────────────────────────────────────────────────────
ALL_RACES = [

    # ── PHB 2014 Core (A–Z) ────────────────────────────────────────────────
    race("Dragonborn", asi={"STR": 2, "CHA": 1},
         traits=["Draconic Ancestry – choose one dragon type and its associated damage type: Black/Copper (acid), Blue/Bronze (lightning), Brass/Gold/Red (fire), Green (poison), Silver/White (cold). This determines your breath weapon's shape and damage type, and your damage resistance",
                 'Breath Weapon – as an action, exhale destructive energy. Area: 5×30-ft line (lightning/acid ancestry) or 15-ft cone (all others). Damage: 2d6 at 1st, 3d6 at 6th, 4d6 at 11th, 5d6 at 16th level. DC = 8 + CON mod + proficiency bonus (DEX save); half on success. Once per short or long rest',
                 'Damage Resistance – you have resistance to the damage type associated with your Draconic Ancestry'],
         languages=["Common", "Draconic"],
         subraces=[
             "Standard (+STR 2, +CHA 1; choose one draconic ancestry — Black, Blue, Brass, Bronze, Copper, Gold, Green, Red, Silver, or White — which sets your breath weapon's shape and damage type and your resistance to that damage type)",
             "Chromatic (+STR 2, +CHA 1; choose Black, Blue, Green, or Red ancestry; Draconic Cry: as a bonus action, roar to frighten enemies within 10 feet for 1 round (WIS save negates); usable a number of times equal to your proficiency bonus, regained after a long rest)",
             "Metallic (+STR 2, +CHA 1; choose Brass, Bronze, Copper, Gold, or Silver ancestry; gain an alternate breath weapon option — Paralyzing Breath (CON save or paralyzed) or Repulsion Breath (STR save or pushed away and knocked prone) — usable once per long rest in place of your normal breath)",
             "Gem (+2 to one ability score and +1 to another, your choice; choose Amethyst, Crystal, Emerald, Sapphire, or Topaz ancestry; Psionic Mind: learn Guidance and Minor Illusion, cast Sending once per long rest; Gem Flight: starting at level 5, gain a flying speed equal to your walking speed for 1 minute once per long rest)",
             "Draconblood (+INT 2, +CHA 1; Darkvision 60 ft; Forceful Presence: advantage on one Intimidation or Persuasion check per long rest)",
             "Ravenite (+STR 2, +CON 1; Darkvision 60 ft; Vengeful Assault: when an ally within 5 feet is hit by an attack, use your reaction to make one melee attack against the attacker if it's within your reach)"]
         ),

    race("Dwarf", asi={"CON": 2},
         traits=["Darkvision 60 ft", 'Dwarven Resilience – you have advantage on saving throws against poison, and you have resistance to poison damage',
                 'Dwarven Combat Training – you have proficiency with the battleaxe, handaxe, light hammer, and warhammer',
                 'Stonecunning – whenever you make an Intelligence (History) check related to the origin of stonework, you are proficient in the History skill and add double your proficiency bonus to the check',
                 "Tool Proficiency – you gain proficiency with one artisan's tool of your choice: smith's tools, brewer's supplies, or mason's tools",
                 "Speed – your speed is not reduced by wearing heavy armor"],
         languages=["Common", "Dwarvish"],
         subraces=["Hill (+CON 2, +WIS 1; Dwarven Toughness: your hit point maximum increases by 1, and increases by 1 again every time you gain a level)",
                   "Mountain (+STR 2, +CON 2; Dwarven Armor Training: proficiency with light and medium armor)",
                   "Duergar (+STR 2, +CON 1; Darkvision 120 ft; Duergar Resilience: advantage on saves against illusions and against being charmed or paralyzed; Duergar Magic: cast Enlarge/Reduce (self only) at 3rd level and Invisibility (self only) at 5th level, once each per long rest; Sunlight Sensitivity: disadvantage on attack rolls and Perception checks that rely on sight while you or the target is in direct sunlight)",
             "Mark of Warding (+INT 2, +CON 1; cast Alarm, Arcane Lock, and Detect Magic each once per long rest without a spell slot, using INT as your spellcasting ability; gain proficiency with one type of artisan's tools)"]),

    race("Elf",
         traits=["Darkvision 60 ft", 'Keen Senses – you have proficiency in the Perception skill',
                 "Fey Ancestry – you have advantage on saving throws against being charmed, and magic can't put you to sleep",
                 "Trance – elves don't need to sleep. Instead, they meditate deeply for 4 hours per day (Elven Trance). After finishing a trance you gain the same benefit that a human gets from 8 hours of sleep. You are aware of your surroundings during the trance",
                 'Elf Weapon Training – you have proficiency with the longsword, shortsword, shortbow, and longbow'],
         languages=["Common", "Elvish"],
         subraces=["High (+DEX 2, +INT 1; learn one extra language of your choice; learn one cantrip from the wizard spell list, using INT as your spellcasting ability)",
                   "Wood (+DEX 2, +WIS 1; base walking speed increases to 35 feet; Mask of the Wild: you can attempt to hide even when only lightly obscured by foliage, heavy rain, falling snow, mist, or other natural phenomena)",
                   "Drow (+DEX 2, +CHA 1; Darkvision 120 ft; Sunlight Sensitivity: disadvantage on attack rolls and Perception checks that rely on sight while you or the target is in direct sunlight; Drow Magic: cast Dancing Lights at will, Faerie Fire once per long rest at 3rd level, and Darkness once per long rest at 5th level, using CHA as your spellcasting ability)",
                   "Eladrin (+DEX 2, +CHA 1; Fey Step: teleport up to 30 feet to an unoccupied space you can see, as a bonus action, once per short or long rest, with an additional effect based on the season you've chosen — Autumn charms one creature within 5 feet of your destination, Winter frightens one creature within 5 feet, Spring lets a willing creature within 5 feet teleport with you, Summer deals 2d6 fire damage to each creature within 5 feet of your origin point; you can change your chosen season after a long rest)",
                   "Eladrin - DMG'14 (+DEX 2, +INT 1; Fey Step: cast Misty Step using this trait once per short or long rest)",
                   "Sea (+DEX 2, +CON 1; swimming speed of 30 feet; Amphibious: you can breathe air and water; Friend of the Sea: you can communicate simple ideas with beasts that have a swimming speed)",
                   "Shadar-kai (+DEX 2, +CON 1; resistance to necrotic damage; Blessing of the Raven Queen: as a bonus action, teleport up to 30 feet to an unoccupied space you can see and gain resistance to all damage until the start of your next turn, usable a number of times equal to your proficiency bonus, regained after a long rest)",
                   "Pallid (– +DEX 2, +WIS 1; Incisive Sense: advantage on Insight checks to determine if a creature is lying; Moonweaver Magic: cast Silent Image once per long rest, using WIS as your spellcasting ability)",
             "Mark of Shadow (+DEX 2, +CHA 1; cast Dancing Lights, Disguise Self, and Darkness each once per long rest without a spell slot, using CHA as your spellcasting ability; gain proficiency in the Stealth skill)"]),

    race("Gnome", speed=25,
         traits=["Darkvision 60 ft",
                 'Gnome Cunning – you have advantage on all Intelligence, Wisdom, and Charisma saving throws against magic'],
         languages=["Common", "Gnomish"],
         subraces=["Forest (+INT 2, +DEX 1; learn the Minor Illusion cantrip, using INT as your spellcasting ability; Speak with Small Beasts: you can communicate simple ideas with Small or smaller beasts)",
                   "Rock (+INT 2, +CON 1; Artificer's Lore: add double your proficiency bonus, instead of your normal bonus, to Intelligence (History) checks related to magic items, alchemical objects, or technological devices; Tinker: using tinker's tools, spend 1 hour and 10 gp of materials to construct a Tiny clockwork device — a clockwork toy, fire starter, or music box — with a simple programmed action)",
                   "Deep Gnome / Svirfneblin (– +INT 2, +DEX 1; Darkvision 120 ft; Stone Camouflage: advantage on Stealth checks made to hide in rocky terrain)",
             "Mark of Scribing (+INT 2, +CHA 1; cast Comprehend Languages, Illusory Script, and Sending each once per long rest without a spell slot, using INT as your spellcasting ability; gain proficiency with calligrapher's supplies)"]),

    race("Half-Elf", asi={"CHA": 2}, asi_flex=2, asi_flex_style="each",
         traits=["Darkvision 60 ft", "Fey Ancestry",
                 'Skill Versatility – you gain proficiency in two skills of your choice',
                 'Extra Language – you can speak, read, and write one additional language of your choice'],
         languages=["Common", "Elvish", "one of your choice"],
         subraces=[
             "Standard (+CHA 2, +1 to two ability scores of your choice; gain two skill proficiencies of your choice)",
             "Aquatic (+CHA 2; swimming speed of 30 feet; Amphibious: you can breathe air and water)",
             "Drow Descent (+CHA 2, +DEX 1; Darkvision 60 ft; learn the Dancing Lights cantrip, using CHA as your spellcasting ability)",
             "High Descent (+CHA 2, +INT 1; learn one cantrip from the wizard spell list, using INT as your spellcasting ability)",
             "Wood Descent (+CHA 2, +WIS 1; base walking speed increases to 35 feet; gain proficiency with the longsword, shortsword, shortbow, and longbow)",
             "Mark of Detection (+CHA 2, +WIS 1; cast Detect Magic and Detect Poison and Disease each once per long rest, and True Seeing once without a spell slot at 9th level, using WIS as your spellcasting ability; gain proficiency in the Investigation skill)",
             "Mark of Storm (+CHA 2, +DEX 1; cast Fog Cloud and Gust of Wind each once per long rest, and Fly once without a spell slot at 9th level, using DEX as your spellcasting ability; gain proficiency with water vehicles)"]),

    race("Half-Orc", asi={"STR": 2, "CON": 1},
         traits=["Darkvision 60 ft", 'Menacing – you gain proficiency in the Intimidation skill',
                 'Relentless Endurance – when you are reduced to 0 hit points but not killed outright, you can drop to 1 hit point instead. Once per long rest',
                 "Savage Attacks – when you score a critical hit with a melee weapon attack, you can roll one of the weapon's damage dice one additional time and add it to the extra damage of the critical hit"],
         subraces=[
             "Mark of Finding (+WIS 2, +CON 1; cast Detect Magic, Hunter's Mark, and Locate Object each once per long rest without a spell slot, using WIS as your spellcasting ability; gain proficiency in the Survival skill)",
         ],
         languages=["Common", "Orc"]),

    race("Halfling", speed=25,
         traits=['Lucky – when you roll a 1 on the d20 for an attack roll, ability check, or saving throw, you can reroll the die and must use the new roll',
                 'Brave – you have advantage on saving throws against being frightened',
                 'Halfling Nimbleness – you can move through the space of any creature that is of a size larger than yours'],
         languages=["Common", "Halfling"],
         subraces=["Lightfoot (+DEX 2, +CHA 1; Naturally Stealthy: you can attempt to hide even when obscured only by a creature at least one size larger than you)",
                   "Stout (+DEX 2, +CON 1; Stout Resilience: advantage on saving throws against poison, and resistance to poison damage)",
                   "Lotusden (– +DEX 2, +WIS 1; Child of the Wood: learn the Druidcraft cantrip; at 3rd level cast Entangle, and at 5th level cast Spike Growth, each once per long rest, using WIS as your spellcasting ability; Timberwalk: moving through nonmagical difficult terrain made of plants costs no extra movement, and you have advantage on saves against being afflicted with disease)",
             "Ghostwise (+DEX 2, +WIS 1; Silent Speech: telepathically communicate simple messages with any creature within 30 feet that understands at least one language)",
             "Mark of Healing (+DEX 2, +WIS 1; cast Cure Wounds and Lesser Restoration each once per long rest, and Mass Cure Wounds once without a spell slot at 9th level, using WIS as your spellcasting ability; gain proficiency with the herbalism kit)",
             "Mark of Hospitality (+DEX 2, +CHA 1; cast Prestidigitation at will, and Purify Food and Drink and Unseen Servant each once per long rest without a spell slot, using CHA as your spellcasting ability; gain proficiency in the Persuasion skill)"]),

    race("Human", asi={"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
         traits=["+1 to all six ability scores", "Extra Language"],
         languages=["Common", "one of your choice"],
         subraces=[
             "Standard (+1 to all six ability scores)",
             "Variant (+1 to two ability scores of your choice; gain one skill proficiency of your choice; gain one feat of your choice, subject to its prerequisites)",
             "Mark of Finding (+WIS 2, +CON 1; cast Detect Magic, Hunter's Mark, and Locate Object each once per long rest without a spell slot, using WIS as your spellcasting ability; gain proficiency in the Survival skill)",
             "Mark of Handling (+WIS 2; cast Animal Friendship and Speak with Animals each once per long rest, and Beast Bond once without a spell slot at 9th level, using WIS as your spellcasting ability; gain proficiency in the Animal Handling skill)",
             "Mark of Making (+INT 2; cast Magic Weapon and Unseen Servant each once per long rest, and Fabricate once without a spell slot at 9th level, using INT as your spellcasting ability; gain proficiency with one type of artisan's tools)",
             "Mark of Passage (+DEX 2; cast Expeditious Retreat and Misty Step each once per long rest, and Teleportation Circle once without a spell slot at 9th level, using DEX as your spellcasting ability; base walking speed increases by 5 feet)",
             "Mark of Sentinel (+WIS 2, +CON 1; cast Compelled Duel and Shield of Faith each once per long rest, and Death Ward once without a spell slot at 9th level, using WIS as your spellcasting ability; gain proficiency in the Perception skill)",
         ]),

    race("Tiefling", asi={"INT": 1, "CHA": 2},
         traits=["Darkvision 60 ft",
                 'Hellish Resistance – you have resistance to fire damage',
                 'Infernal Legacy – you know the Thaumaturgy cantrip. When you reach 3rd level, you can cast Hellish Rebuke as a 2nd-level spell once per long rest without a spell slot. When you reach 5th level, you can cast Darkness once per long rest without a spell slot. Charisma is your spellcasting ability for these spells'],
         languages=["Common", "Infernal"],
         subraces=[
             "Asmodeus (PHB, default – +CHA 2, +INT 1; resistance to fire damage; Infernal Legacy: learn the Thaumaturgy cantrip; cast Hellish Rebuke once per long rest at 3rd level and Darkness once per long rest at 5th level, using CHA as your spellcasting ability)",
             "Baalzebul (+CHA 2, +INT 1; resistance to fire damage; learn Thaumaturgy; cast Ray of Sickness once per long rest at 3rd level and Crown of Madness once per long rest at 5th level, using CHA)",
             "Dispater (+CHA 2, +INT 1; resistance to fire damage; learn Thaumaturgy; cast Disguise Self once per long rest at 3rd level and Detect Thoughts once per long rest at 5th level, using CHA)",
             "Fierna (+CHA 2, +WIS 1; resistance to fire damage; learn Friends; cast Charm Person once per long rest at 3rd level and Suggestion once per long rest at 5th level, using CHA)",
             "Glasya (+CHA 2, +INT 1; resistance to fire damage; learn Minor Illusion; cast Disguise Self once per long rest at 3rd level and Invisibility once per long rest at 5th level, using CHA)",
             "Levistus (+CHA 2, +CON 1; resistance to cold damage; learn Ray of Frost; cast Armor of Agathys once per long rest at 3rd level and Darkness once per long rest at 5th level, using CHA)",
             "Mammon (+CHA 2, +INT 1; resistance to fire damage; learn Mage Hand; cast Tenser's Floating Disk once per long rest at 3rd level and Arcane Lock once per long rest at 5th level, using CHA)",
             "Mephistopheles (+CHA 2, +INT 1; resistance to fire damage; learn Mage Hand; cast Burning Hands once per long rest at 3rd level and Flame Blade once per long rest at 5th level, using CHA)",
             "Zariel (+CHA 2, +STR 1; resistance to fire damage; learn Thaumaturgy; cast Searing Smite once per long rest at 3rd level and Branding Smite once per long rest at 5th level, using CHA)",
             "Feral (+CHA 2, +DEX 2 in place of the usual +CHA 2/+INT 1 array; gain Darkvision 60 ft; resistance to fire damage retained from your fiendish heritage)",
             "Devil's Tongue (replaces your Infernal Legacy spells: learn Vicious Mockery instead of Thaumaturgy, and cast Charm Person and Enthrall in place of your normal 3rd- and 5th-level spells, using CHA)",
             "Hellfire (replaces the Hellish Rebuke granted by Infernal Legacy with Burning Hands, cast once per long rest at 3rd level using CHA)",
             "Winged (replaces your Infernal Legacy spells entirely with a flying speed of 30 feet, gained at 3rd level)"]
         ),

    # ── Exotic & Published (A–Z) ────────────────────────────────────────────
    race("Aarakocra", speed=25, asi={"DEX": 2, "WIS": 1}, source="EEPC",
         traits=["Flight 50 ft – you have a flying speed of 50 feet. To use this speed, you can't be wearing medium or heavy armor. Your wings are natural, not magic — you can fly freely in any non-cramped environment",
                 'Talons – your talons are natural weapons, which you can use to make unarmed strikes. If you hit with them, you deal slashing damage equal to 1d4 + your Strength modifier'],
         languages=["Common", "Aarakocra", "Auran"]),

    race("Aarakocra (MPMM)", speed=30, asi_flex=2, source="MPMM",
         traits=["Flight – flying speed equal to your walking speed; can't use it wearing medium or heavy armor",
                 "Talons – unarmed strikes with your talons deal 1d6 + STR slashing damage instead of the normal bludgeoning",
                 'Wind Caller – starting at 3rd level, cast Gust of Wind (no material component) once per long rest, or with a 2nd-level+ spell slot; spellcasting ability is INT, WIS, or CHA (choose when you select this race)'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Aarakocra (Monsters of the Multiverse) — kept separate from the original EEPC version above; flying speed is now tied to your walking speed rather than a flat 50 ft, and talon damage increases to 1d6."),

    race("Aasimar", asi={"CHA": 2}, source="VGM",
         traits=["Darkvision 60 ft", 'Celestial Resistance – you have resistance to necrotic damage and radiant damage',
                 'Healing Hands – as an action, you can touch a creature and cause it to regain hit points equal to your level. Once per long rest',
                 'Light Bearer – you know the Light cantrip. Charisma is your spellcasting ability for it'],
         languages=["Common", "Celestial"],
         subraces=["Protector (+WIS 1; Radiant Soul: starting at 3rd level, as an action for 1 minute you gain a pair of spectral wings granting a flying speed of 30 feet, and once per turn you can deal extra radiant damage equal to your level on a hit; usable once per long rest)",
                   "Scourge (+CON 1; Radiant Consumption: starting at 3rd level, as an action for 1 minute you glow with a 10-foot radiant aura that deals radiant damage equal to half your level to each creature within it (including you) at the end of your turn, and once per turn you deal extra radiant damage equal to your level on a hit; usable once per long rest)",
                   "Fallen (+STR 1; Necrotic Shroud: starting at 3rd level, as an action for 1 minute you sprout ghostly wings granting a flying speed of 30 feet and radiate a 10-foot frightening aura (CHA save or frightened until the end of your next turn), and once per turn you deal extra necrotic damage equal to your level on a hit; usable once per long rest)"]),

    race("Aasimar (MPMM)", asi_flex=2, source="MPMM",
         traits=["Darkvision 60 ft", "Celestial Resistance – resistance to necrotic and radiant damage",
                 'Healing Hands – action: touch a creature and roll a number of d4s equal to your proficiency bonus; it regains that many hit points. Once per long rest',
                 'Light Bearer – you know the Light cantrip (CHA spellcasting)',
                 'Celestial Revelation – at 3rd level, choose one revelation (locked in once chosen): Necrotic Shroud (bonus action, 1 min: frighten nearby non-allies (CHA save) and deal extra necrotic damage = your PB once per turn on a hit), Radiant Consumption (bonus action, 1 min: shed light, deal PB radiant damage to nearby creatures each turn, and deal extra radiant damage = your PB once per turn on a hit), or Radiant Soul (bonus action, 1 min: flying speed = walking speed, deal extra radiant damage = your PB once per turn on a hit). Once per long rest'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Aasimar (Monsters of the Multiverse) — kept separate from the original VGM version above. Replaces the old Protector/Scourge/Fallen subrace split with a single Celestial Revelation choice any Aasimar can make at 3rd level; can also choose Small size instead of Medium."),

    race("Bugbear", asi={"STR": 2, "DEX": 1}, source="VGM",
         traits=["Darkvision 60 ft",
                 'Long-Limbed – when you make a melee attack on your turn, your reach for it is 5 feet greater than normal',
                 'Powerful Build – count as Large for carrying capacity and the weight you can push, drag, or lift',
                 'Sneaky – you are proficient in the Stealth skill',
                 'Surprise Attack – if you surprise a creature and hit it with an attack on your first turn in combat, the attack deals an extra 2d6 damage. You can use this trait only once per combat'],
         languages=["Common", "Goblin"]),

    race("Bugbear (MPMM)", asi_flex=2, source="MPMM",
         traits=["Darkvision 60 ft",
                 "Fey Ancestry – advantage on saving throws to avoid or end the charmed condition on yourself",
                 'Long-Limbed – your reach with melee attacks on your turn is 5 feet greater than normal',
                 'Powerful Build – count as one size larger for carrying capacity and the weight you can push, drag, or lift',
                 "Sneaky – proficient in Stealth; without squeezing, you can move through and stop in a space large enough for a Small creature",
                 'Surprise Attack – a creature you hit takes an extra 2d6 damage if it hasn\'t yet taken a turn in the current combat'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Bugbear (Monsters of the Multiverse) — kept separate from the original VGM version above; adds Fey Ancestry, and Surprise Attack no longer has the old 'once per combat' limit — it can trigger against any creature that hasn't acted yet, not just once."),

    race("Centaur", speed=40, asi={"STR": 2, "WIS": 1}, source="MOT/GGR",
         traits=["Fey creature type",
                 'Charge – if you move at least 30 feet straight toward a target and hit it with a melee weapon attack on the same turn, you can immediately follow up with a bonus action, making one attack against the target with your hooves',
                 'Hooves – your hooves are natural weapons, which you can use to make unarmed strikes. If you hit with them, you deal bludgeoning damage equal to 1d4 + your Strength modifier',
                 "Equine Build – you count as one size larger when determining your carrying capacity and the weight you can push or drag. Any climb requiring hands and feet is especially difficult for you: each foot of movement costs 4 extra feet instead of the normal 1",
                 'Survivor – proficiency in one of the following skills: Animal Handling, Medicine, Nature, or Survival'],
         languages=["Common", "Sylvan"]),

    race("Centaur (MPMM)", speed=40, asi_flex=2, source="MPMM",
         traits=["Fey creature type",
                 'Charge – if you move at least 30 feet straight toward a target and hit it with a melee weapon attack on the same turn, you can immediately follow up with a bonus action, making one attack against the target with your hooves',
                 'Hooves – your hooves deal 1d6 + STR bludgeoning damage as an unarmed strike (up from 1d4 in the older version)',
                 "Equine Build – count as one size larger for carrying capacity and the weight you can push or drag; climbs requiring hands and feet cost 4 extra feet of movement per foot moved",
                 'Natural Affinity – proficiency in one of: Animal Handling, Medicine, Nature, or Survival'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Centaur (Monsters of the Multiverse) — kept separate from the original MOT/GGR version above; hoof damage increases to 1d6."),

    race("Dhampir", speed=35, asi_flex=2, source="VRGtR",
         traits=["Size – you are Small or Medium, your choice",
                 "Darkvision 60 ft",
                 'Ancestral Legacy – if this lineage replaces a previous race, you can keep any skill proficiencies and any climbing/flying/swimming speed you had from it. Otherwise (or if you decline to keep those), gain proficiency in two skills of your choice',
                 "Deathless Nature – you don't need to breathe",
                 'Spider Climb – you have a climbing speed equal to your walking speed. In addition, at 3rd level, you can move up, down, and across vertical surfaces and upside down along ceilings, while leaving your hands free',
                 "Vampiric Bite – your fanged bite is a natural weapon (simple melee, proficient), using CON instead of STR for attack/damage rolls, dealing 1d4 piercing on a hit. While you have half or fewer of your HP remaining, you have advantage on attack rolls with this bite. When you hit a creature that isn't a Construct or Undead with this bite, you can empower yourself: either regain HP equal to the piercing damage dealt, or gain a bonus to your next ability check or attack roll equal to that damage. Uses = proficiency bonus, all regained on a long rest"],
         languages=["Common", "one of your choice"]),

    race("Fairy", size="Small", asi_flex=2, source="WBW",
         traits=["Fey creature type",
                 'Flight 30 ft (no medium or heavy armor)',
                 "Fairy Magic – Druidcraft cantrip; Faerie Fire 1/LR at 3; Enlarge/Reduce 1/LR at 5 (choose INT/WIS/CHA)"],
         languages=["Common", "Sylvan"]),

    race("Firbolg", asi={"WIS": 2, "STR": 1}, source="VGM",
         traits=['Firbolg Magic – Detect Magic and Disguise Self, each once per short or long rest (WIS spellcasting; Disguise Self can appear as any Medium humanoid)',
                 'Hidden Step – bonus action: invisible until start of next turn (ends if you attack, deal damage, or force a saving throw). Once per short or long rest',
                 "Powerful Build",
                 "Speech of Beast and Leaf – communicate with beasts/plants"],
         languages=["Common", "Elvish", "Giant"]),

    race("Firbolg (MPMM)", asi_flex=2, source="MPMM",
         traits=['Firbolg Magic – Detect Magic and Disguise Self (can seem up to 3 ft shorter or taller), each once per long rest or with any spell slot; spellcasting ability is INT, WIS, or CHA (choose when you select this race)',
                 "Hidden Step – bonus action: invisible until start of next turn (ends if you attack, make a damage roll, or force a saving throw). Uses = proficiency bonus, all regained on a long rest",
                 "Powerful Build",
                 "Speech of Beast and Leaf – communicate with beasts/plants; advantage on CHA checks to influence them"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Firbolg (Monsters of the Multiverse) — kept separate from the original VGM version above. Hidden Step is genuinely different here: it scales with proficiency bonus and resets only on a long rest, not the flat 1-use/short-or-long-rest version above."),

    race("Genasi", asi={"CON": 2}, source="EEPC",
         traits=["Constitution +2 (all subraces)"],
         subraces=["Air (+DEX 1; Unending Breath: you can hold your breath indefinitely while not incapacitated; at 3rd level, cast Levitate on yourself once per long rest, using CON as your spellcasting ability)",
                   "Earth (+STR 1; Earth Walk: you can move across difficult terrain made of earth or stone without extra movement cost; at 3rd level, cast Pass without Trace once per long rest, using CON as your spellcasting ability)",
                   "Fire (+INT 1; Darkvision 60 ft; resistance to fire damage; learn the Produce Flame cantrip; at 3rd level, cast Burning Hands once per long rest, using CON as your spellcasting ability)",
                   "Water (+WIS 1; Amphibious: you can breathe air and water; swimming speed of 30 feet; resistance to acid damage; learn the Shape Water cantrip; at 3rd level, cast Create or Destroy Water once per long rest, using CON as your spellcasting ability)"]),

    race("Genasi (MPMM)", asi_flex=2, source="MPMM",
         traits=["Size – Medium or Small, your choice", "Darkvision 60 ft"],
         subraces=["Air (Speed 35 ft; Unending Breath: hold your breath indefinitely while not incapacitated; Lightning Resistance; Mingle with the Wind: know Shocking Grasp, cast Feather Fall at 3rd level and Levitate at 5th level, each once per long rest or with an appropriate-level spell slot, no material component; spellcasting ability is INT/WIS/CHA, chosen when you select this race)",
                   "Earth (Earth Walk: cross difficult terrain on the ground with no extra movement cost; Merge with Stone: know Blade Ward, usable as a bonus action a number of times equal to your proficiency bonus (regained on a long rest), and cast Pass without Trace at 5th level once per long rest or with a 2nd-level+ slot, no material component; spellcasting ability is INT/WIS/CHA, chosen when you select this race)",
                   "Fire (Fire Resistance; Reach to the Blaze: know Produce Flame, cast Burning Hands at 3rd level and Flame Blade at 5th level (no material component), each once per long rest or with an appropriate-level spell slot; spellcasting ability is INT/WIS/CHA, chosen when you select this race)",
                   "Water (Speed 30 ft, swim equal to walking speed; Acid Resistance; Amphibious: breathe air and water; Call to the Wave: know Acid Splash, cast Create or Destroy Water at 3rd level and Water Walk at 5th level (no material component), each once per long rest or with an appropriate-level spell slot; spellcasting ability is INT/WIS/CHA, chosen when you select this race)"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Genasi (Monsters of the Multiverse) — kept separate from the original EEPC version above; can also choose Small size instead of Medium, and each element's spellcasting now scales further at 5th level."),

    race("Githyanki", asi={"STR": 2, "INT": 1}, source="MTF",
         traits=[
             "Decadent Mastery – you learn one language of your choice, and you gain proficiency with one skill or tool of your choice",
             "Martial Prodigy – proficiency with light and medium armor, shortswords, longswords, greatswords",
             'Githyanki Psionics – Mage Hand (no components) at Lv1; Jump 1/LR at Lv3; Misty Step 1/LR at Lv5 (INT spellcasting)',
         ],
         languages=["Common", "Gith"]),

    race("Githyanki (MPMM)", asi_flex=2, source="MPMM",
         traits=[
             "Astral Knowledge – whenever you finish a long rest, you gain proficiency in one skill and with one weapon or tool of your choice (PHB only) until the end of your next long rest",
             'Githyanki Psionics – Mage Hand (no components); Jump at Lv3 and Misty Step at Lv5, each 1/LR (or with a spell slot); spellcasting ability is INT, WIS, or CHA (choose when you select this race)',
             "Psychic Resilience – resistance to psychic damage",
         ],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Githyanki (Monsters of the Multiverse); kept separate from the original MTF version above."),

    race("Githzerai", asi={"WIS": 2, "INT": 1}, source="MTF",
         traits=[
             "Mental Discipline – advantage on saving throws vs. charmed and frightened",
             'Githzerai Psionics – Mage Hand (no components) at Lv1; Shield 1/LR at Lv3; Detect Thoughts 1/LR at Lv5 (WIS spellcasting)',
         ],
         languages=["Common", "Gith"]),

    race("Githzerai (MPMM)", asi_flex=2, source="MPMM",
         traits=[
             'Githzerai Psionics – Mage Hand (no components); Shield at Lv3 and Detect Thoughts at Lv5, each 1/LR (or with a spell slot); spellcasting ability is INT, WIS, or CHA (choose when you select this race)',
             "Mental Discipline – advantage on saving throws vs. charmed and frightened",
             "Psychic Resilience – resistance to psychic damage",
         ],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Githzerai (Monsters of the Multiverse); kept separate from the original MTF version above."),

    race("Goblin", speed=30, size="Small", asi={"DEX": 2, "CON": 1}, source="VGM",
         traits=["Darkvision 60 ft",
                 "Fury of the Small – when you damage a creature with an attack or a spell and the creature's size is larger than yours, you can cause the attack or spell to deal extra damage to the creature equal to your level. Once per short or long rest",
                 'Nimble Escape – you can take the Disengage or Hide action as a bonus action on each of your turns'],
         languages=["Common", "Goblin"]),

    race("Goblin (MPMM)", speed=30, size="Small", asi_flex=2, source="MPMM",
         traits=["Darkvision 60 ft",
                 "Fey Ancestry – advantage on saving throws to avoid or end the charmed condition on yourself",
                 "Fury of the Small – when you damage a creature larger than you with an attack or spell, you can deal extra damage equal to your proficiency bonus (once per turn). Uses = proficiency bonus, all regained on a long rest",
                 'Nimble Escape – you can take the Disengage or Hide action as a bonus action on each of your turns'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Goblin (Monsters of the Multiverse) — kept separate from the original VGM version above; adds Fey Ancestry entirely, and Fury of the Small changes from level-scaled damage (1 use per short or long rest) to proficiency-bonus-scaled damage and uses (long-rest-only, capped at once per turn)."),

    race("Goliath", asi={"STR": 2, "CON": 1}, source="EEPC/VGTM",
         traits=['Natural Athlete – you have proficiency in the Athletics skill',
                 "Stone's Endurance – you can focus yourself to occasionally shrug off injury. When you take damage, you can use your reaction to roll a d12. Add your Constitution modifier to the number rolled, and reduce the damage by that total. Once per short or long rest",
                 "Powerful Build",
                 "Mountain Born – you're acclimated to high altitude, including elevations above 20,000 feet. You also naturally adapted to cold climates, as described in chapter 5 of the Dungeon Master's Guide. You have resistance to cold damage"],
         languages=["Common", "Giant"]),

    race("Goliath (MPMM)", asi_flex=2, source="MPMM",
         traits=["Little Giant – proficiency in Athletics; count as one size larger for carrying weight and the weight you can push, drag, or lift",
                 "Mountain Born – resistance to cold damage; naturally acclimated to high altitudes, including above 20,000 feet",
                 "Stone's Endurance – reaction on taking damage: roll a d12, add your CON modifier, reduce the damage by that total. Uses = proficiency bonus, all regained on a long rest"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Goliath (Monsters of the Multiverse) — kept separate from the original EEPC/VGTM version above; Stone's Endurance now scales with proficiency bonus and resets only on a long rest, instead of a flat 1 use per short or long rest."),

    # ── Eberron ───────────────────────────────────────────────────────────────

    race("Grung", speed=25, size="Small", asi={"DEX": 2, "CON": 1},
         source="One Grung Above",
         traits=['Arboreal Alertness – life in the treetops has sharpened your senses. You have proficiency in the Perception skill',
                 "Amphibious",
                 'Poisonous Skin – any creature that touches your bare skin (including grappling) takes 1d4 poison damage; CON save (DC 8+CON+proficiency) negates',
                 'Standing Leap – your long jump is up to 25 feet and your high jump is up to 15 feet, with or without a running start',
                 'Water Dependency – if you fail to immerse yourself in water for at least 1 hour during a day, you suffer one level of exhaustion at the end of that day. You can recover from this exhaustion only through magic or by spending at least 1 hour submerged in water'],
         languages=["Grung"]),

    race("Harengon", asi_flex=2, source="WBW",
         traits=["Hare-Trigger – proficiency bonus added to Initiative rolls",
                 'Leporine Senses – your long ears give you remarkable awareness. You have proficiency in the Perception skill',
                 "Lucky Footwork – reaction: add d4 to a failed DEX saving throw",
                 'Rabbit Hop – bonus action: jump Prof × 5 ft without provoking opportunity attacks. PB per long rest'],
         languages=["Common", "one of your choice"]),

    race("Hexblood", asi_flex=2, source="VRGtR",
         traits=["Size – you are Small or Medium, your choice",
                 "Fey creature type",
                 "Darkvision 60 ft",
                 'Ancestral Legacy – if this lineage replaces a previous race, you can keep any skill proficiencies and any climbing/flying/swimming speed you had from it. Otherwise (or if you decline to keep those), gain proficiency in two skills of your choice',
                 "Eerie Token – you can harmlessly remove a lock of hair, a nail, or a tooth to create a magic token (once per long rest; any missing part regrows on a long rest). As an action, using the token, you can either send a telepathic message of up to 25 words to whoever holds it (if within 10 miles), or enter a 1-minute trance to see/hear from the token's location (you're blinded and deafened to your own surroundings meanwhile; the token is destroyed when the trance ends, which you can also do early with no action)",
                 'Hex Magic – you can cast Disguise Self and Hex, each once per long rest without a spell slot (and again using an actual spell slot if you have one). Intelligence, Wisdom, or Charisma (choose when you gain this feature) is your spellcasting ability for these spells'],
         languages=["Common", "one of your choice"]),

    race("Hobgoblin", asi={"CON": 2, "INT": 1}, source="VGM",
         traits=["Darkvision 60 ft",
                 'Martial Training – you are proficient with two martial weapons of your choice and with light armor',
                 'Saving Face – hobgoblins are careful not to show weakness. If you miss with an attack roll or fail an ability check or saving throw, you can gain a bonus to the roll equal to the number of allies you can see within 30 feet of you (max +5). Once per short or long rest'],
         languages=["Common", "Goblin"]),

    race("Hobgoblin (MPMM)", asi_flex=2, source="MPMM",
         traits=["Darkvision 60 ft",
                 "Fey Ancestry – advantage on saving throws to avoid or end the charmed condition on yourself",
                 "Fey Gift – bonus action: take the Help action. Uses = proficiency bonus, all regained on a long rest. Starting at 3rd level, each time you use it choose one: Hospitality (you and the helped creature each gain temp HP = 1d6 + PB), Passage (you and the helped creature each gain +10 ft speed until the start of your next turn), or Spite (the next attack the helped creature hits with gives the target disadvantage on its next attack within 1 minute)",
                 "Fortune from the Many – if you miss with an attack roll or fail an ability check or saving throw, you can gain a bonus to the roll equal to the number of allies you can see within 30 feet of you (max +3). Uses = proficiency bonus, all regained on a long rest"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Hobgoblin (Monsters of the Multiverse) — kept separate from the original VGM version above; entirely different traits (also counts as a goblinoid for any prerequisite or effect requiring one)."),

    race("Kenku", asi={"DEX": 2, "WIS": 1}, source="VGM",
         traits=["Expert Forgery – you can duplicate other creatures' handwriting and craftwork. You have advantage on all checks made to produce forgeries or duplicates of existing objects",
                 "Kenku Training – proficiency in 2 of: Acrobatics, Deception, Stealth, Sleight of Hand",
                 'Mimicry – you can mimic sounds you have heard, including voices. A creature that hears the sounds can tell they are imitations with a successful Wisdom (Insight) check opposed by your Charisma (Deception) check'],
         languages=["Common", "Auran"],
         notes="You can read and write Common and Auran, but you can't speak either language normally — you can only speak by mimicking sounds you've heard, via the Mimicry trait."),

    race("Kenku (MPMM)", size="Medium", asi_flex=2, source="MPMM",
         traits=["Expert Duplication – when you copy writing or craftwork produced by yourself or someone else, you have advantage on ability checks to produce an exact duplicate",
                 "Kenku Recall – proficiency in two skills of your choice. When you make a check using a skill you're proficient in, you can give yourself advantage on it before rolling; you can do this a number of times equal to your proficiency bonus, regaining all uses on a long rest",
                 'Mimicry – you can accurately mimic sounds you have heard, including voices. A creature can tell the sounds are imitations only with a successful Wisdom (Insight) check (DC 8 + your proficiency bonus + CHA mod)'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Kenku (Monsters of the Multiverse) — kept separate from the original VGM version above. You can also choose Small size instead of Medium when selecting this race."),

    race("Kobold", size="Small", asi={"DEX": 2, "INT": 1}, source="VGM",
         traits=["Darkvision 60 ft",
                 'Grovel, Cower, and Beg – as an action, you can cower pathetically to distract nearby foes. Until the end of your next turn, your allies gain advantage on attack rolls against enemies within 10 feet of you that can see you. Once per short or long rest',
                 "Pack Tactics – you have advantage on an attack roll against a creature if at least one of your allies is within 5 feet of the creature and the ally isn't incapacitated",
                 'Sunlight Sensitivity – you have disadvantage on attack rolls and on Wisdom (Perception) checks that rely on sight when you, the target of your attack, or whatever you are trying to perceive is in direct sunlight'],
         languages=["Common", "Draconic"]),

    race("Kobold (MPMM)", size="Small", asi_flex=2, source="MPMM",
         traits=["Darkvision 60 ft",
                 "Draconic Cry – bonus action: enemies within 10 feet who can hear you grant you and your allies advantage on attack rolls against them until the start of your next turn. Uses = proficiency bonus, all regained on a long rest",
                 "Kobold Legacy – choose one (locked in once chosen): Craftiness (proficiency in one of Arcana, Investigation, Medicine, Sleight of Hand, or Survival), Defiance (advantage on saves to avoid or end being frightened), or Draconic Sorcery (know one sorcerer cantrip of your choice; spellcasting ability is INT, WIS, or CHA, chosen when you select this race)"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Kobold (Monsters of the Multiverse) — kept separate from the original VGM version above; entirely different traits, dropping Sunlight Sensitivity and Pack Tactics."),

    race("Leonin", speed=35, asi={"CON": 2, "STR": 1}, source="MOT",
         traits=["Darkvision 60 ft",
                 'Claws – your claws are natural weapons, which you can use to make unarmed strikes. If you hit with them, you deal slashing damage equal to 1d4 + your Strength modifier, instead of the bludgeoning damage normal for an unarmed strike',
                 "Hunter's Instincts – you gain proficiency in one of the following skills of your choice: Intimidation, Athletics, Perception, or Survival",
                 'Daunting Roar – as a bonus action, you let out an especially menacing roar. Creatures of your choice within 10 feet that can hear you must succeed on a Wisdom saving throw (DC 8 + CON mod + proficiency bonus) or be frightened of you until the end of your next turn. Once per short or long rest'],
         languages=["Common", "Leonin"]),

    race("Lizardfolk", asi={"CON": 2, "WIS": 1}, source="VGM",
         traits=['Bite – your fanged maw is a natural weapon. If you hit with an unarmed bite strike, you deal 1d6 + STR piercing damage',
                 'Cunning Artisan – as part of a short rest, you can harvest bone and hide from a slain beast, construct, dragon, monstrosity, or plant creature of Small size or larger to create a shield, club, javelin, or 1d4 darts or blowgun needles. Requires a sharp tool',
                 'Hold Breath – you can hold your breath for up to 15 minutes at a time',
                 "Hunter's Lore – 2 skills from Animal Handling/Nature/Perception/Stealth/Survival",
                 "Natural Armor – you have tough, scaly skin. When not wearing armor, your AC is 13 + your Dexterity modifier. You can use your natural armor to determine your AC if the armor you wear would leave you with a lower AC. A shield's benefits apply as normal",
                 'Hungry Jaws – once per short or long rest, you can use a bonus action to make a special attack with your bite. If the attack hits, it deals its normal damage, and you gain temporary hit points equal to your Constitution modifier (minimum 1 temporary hit point)'],
         languages=["Common", "Draconic"]),

    race("Lizardfolk (MPMM)", asi_flex=2, source="MPMM",
         traits=['Bite – unarmed strike with your fanged maw deals 1d6 + STR slashing damage',
                 'Hold Breath – you can hold your breath for up to 15 minutes at a time',
                 "Hungry Jaws – bonus action: special Bite attack; on a hit, gain temp HP equal to your proficiency bonus. Uses = proficiency bonus, all regained on a long rest",
                 "Natural Armor – when not wearing armor, your AC is 13 + your Dexterity modifier. You can use your natural armor to determine your AC if the armor you wear would leave you with a lower AC. A shield's benefits apply as normal",
                 "Nature's Intuition – proficiency in two of: Animal Handling, Medicine, Nature, Perception, Stealth, or Survival"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Lizardfolk (Monsters of the Multiverse) — kept separate from the original VGM version above. Drops Cunning Artisan entirely; Hungry Jaws now scales with proficiency bonus and resets only on a long rest, instead of a flat 1 use per short or long rest."),

    race("Locathah", asi={"STR": 2, "DEX": 1}, source="LR",
         traits=[
             "Natural Armor – you have tough, scaly skin. When not wearing armor, your AC is 13 + your Dexterity modifier. You can use your natural armor to determine your AC if the armor you wear would leave you with a lower AC. A shield's benefits apply as normal",
             "Leviathan Will – advantage on saves vs. frightened, paralyzed, petrified, poisoned, stunned, unconscious",
             "Limited Amphibiousness – breathe air and water; max 4 hours out of water",
             "Swim Speed 30 ft",
         ],
         languages=["Common", "Aquan"], speed=30),

    race("Loxodon", asi={"CON": 2, "WIS": 1}, source="GGR",
         traits=["Powerful Build",
                 'Loxodon Serenity – you have advantage on saving throws against being charmed or frightened',
                 "Natural Armor – you have thick, leathery skin. When not wearing armor, your AC is 12 + your Constitution modifier. A shield's benefits apply as normal",
                 "Trunk – you can grasp things with your trunk, and it can be used as a snorkel. It has a reach of 5 feet, and can lift a number of pounds equal to 5x your Strength score. You can use it to lift/drop/hold/push/pull an object or creature, open or close a door or container, grapple someone, or make an unarmed strike. It can't wield weapons/shields or do anything requiring manual precision (tools, magic items, spell somatic components)",
                 'Keen Smell – you have advantage on Wisdom (Perception), Wisdom (Survival), and Intelligence (Investigation) checks that involve smell'],
         languages=["Common", "Loxodon"]),

    race("Minotaur", asi={"STR": 2, "CON": 1}, source="MOT/GGR",
         traits=['Horns – your horns are natural weapons you can use to make unarmed strikes dealing 1d6 + STR piercing damage',
                 'Goring Rush – immediately after you use the Dash action on your turn and move at least 20 feet, you can make one melee attack with your Horns as a bonus action',
                 'Hammering Horns – immediately after you hit a creature with a melee attack as part of the Attack action on your turn, you can use a bonus action to attempt to shove that target with your horns (must be within 5 ft and no more than one size larger than you). Unless it succeeds on a Strength saving throw (DC 8 + proficiency bonus + STR mod), you push it up to 10 feet away from you',
                 'Imposing Presence – you have proficiency in one of the following skills of your choice: Intimidation or Persuasion'],
         languages=["Common", "Minotaur"]),

    race("Minotaur (MPMM)", asi_flex=2, source="MPMM",
         traits=['Horns – your horns are natural weapons you can use to make unarmed strikes dealing 1d6 + STR piercing damage',
                 'Goring Rush – immediately after you use the Dash action, you can make one melee attack with your Horns as a bonus action',
                 'Hammering Horns – immediately after you hit a creature with a melee attack, you can use a bonus action to attempt to shove that target with your horns (must be within 5 ft and no more than one size larger than you). Unless it succeeds on a Strength saving throw (DC 8 + proficiency bonus + STR mod), you push it up to 10 feet away from you',
                 'Labyrinthine Recall – you always know which direction is north, and you have advantage on any Wisdom (Survival) check you make to navigate or track'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Minotaur (Monsters of the Multiverse) — kept separate from the original MOT/GGR version above. Trades Imposing Presence for Labyrinthine Recall."),

    race("Orc", asi_flex=2, source="MPMM",
         traits=["Darkvision 60 ft",
                 'Adrenaline Rush – bonus action: Dash + gain temp HP equal to your proficiency bonus. Uses = proficiency bonus, all regained on a long rest',
                 "Powerful Build",
                 "Relentless Endurance – when you are reduced to 0 hit points but not killed outright, you can drop to 1 hit point instead. You can't use this feature again until you finish a long rest"],
         languages=["Common", "one other of your choice"]),

    race("Orc (VGM/MTF)", asi={"STR": 2, "CON": 1}, source="VGM/MTF",
         traits=["Darkvision 60 ft",
                 "Aggressive – as a bonus action, you can move up to your speed toward a hostile creature you can see or hear. You must end this move closer to the enemy than you started",
                 "Primal Intuition – proficiency in two of the following skills of your choice: Animal Handling, Insight, Intimidation, Medicine, Perception, and Survival",
                 "Powerful Build"],
         languages=["Common", "Orc"]),

    race("Owlin", asi_flex=2, source="Strixhaven",
         traits=["Size – you are Small or Medium, your choice",
                 "Flight 30 ft (no medium/heavy armor)",
                 "Darkvision 120 ft",
                 'Silent Feathers – proficiency in the Stealth skill'],
         languages=["Common", "one of your choice"]),

    race("Reborn", asi_flex=2, source="VRGtR",
         traits=["Size – you are Small or Medium, your choice",
                 "Darkvision 60 ft",
                 'Ancestral Legacy – if this lineage replaces a previous race, you can keep any skill proficiencies and any climbing/flying/swimming speed you had from it. Otherwise (or if you decline to keep those), gain proficiency in two skills of your choice',
                 "Deathless Nature – advantage on saving throws against disease and being poisoned, and resistance to poison damage; advantage on death saving throws; you don't need to eat, drink, or breathe; you don't need to sleep, and magic can't put you to sleep (you can finish a long rest in 4 hours if you spend those hours in an inactive, motionless state while remaining conscious)",
                 'Knowledge from a Past Life – when you make an ability check that uses a skill, you can add 1d6 to the roll. Uses = proficiency bonus, all regained on a long rest'],
         languages=["Common", "one of your choice"]),

    # ── Spelljammer / Fizban's / Bigby's ──────────────────────────────────────

    race("Satyr", speed=35, asi={"CHA": 2, "DEX": 1}, source="MOT",
         traits=["Fey creature type",
                 'Ram – unarmed 1d6+STR bludgeoning. If you move 10+ ft in a straight line before hitting, target must make STR save (DC 8+STR+proficiency) or be pushed 5 ft',
                 "Magic Resistance – advantage on saving throws vs. spells",
                 'Mirthful Leaps – whenever you make a long jump or a high jump, you can roll a d8 and add the number rolled to the number of feet you cover, even when making a standing jump. This extra distance costs movement as normal',
                 "Reveler – Persuasion + Performance proficiency; musical instrument"],
         languages=["Common", "Sylvan"]),

    race("Satyr (MPMM)", speed=35, asi_flex=2, source="MPMM",
         traits=["Fey creature type",
                 'Ram – unarmed strike with your head and horns deals 1d6 + STR bludgeoning damage',
                 "Magic Resistance – advantage on saving throws against spells",
                 'Mirthful Leaps – whenever you make a long jump or a high jump, you can roll a d8 and add the number rolled to the number of feet you cover, even when making a standing jump. This extra distance costs movement as normal',
                 "Reveler – proficiency in Performance and Persuasion, and with one musical instrument of your choice"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Satyr (Monsters of the Multiverse) — kept separate from the original MOT version above. Ram drops the charge-and-push mechanic entirely (the older version pushes a target 5 ft on a failed STR save after a 10+ ft charge; this version is just a flat unarmed strike)."),

    race("Simic Hybrid", asi={"CON": 2}, asi_flex=1, source="GGR",
         traits=["Darkvision 60 ft",
                 'Animal Enhancement at 1st level – your body is augmented by Simic biomagy. Choose one of the following at character creation: Manta Glide (ray-like fins slow your fall: when you fall and aren\'t incapacitated, subtract up to 100 ft from the fall for damage purposes, and move up to 2 ft horizontally for every 1 ft you descend), Nimble Climber (climbing speed = walking speed), or Underwater Adaptation (breathe air and water, swim speed = walking speed)',
                 "Additional Animal Enhancement at 5th level – choose another enhancement from a larger list (or repeat a 1st-level option): Grappling Appendages (2 appendages, each a natural weapon dealing 1d6 + STR bludgeoning damage on an unarmed strike; immediately after hitting, try to grapple as a bonus action; can't wield weapons/cast with them), Carapace (+1 AC when not wearing heavy armor), or Acid Spit (action: one creature/object within 30 ft makes a DEX save vs. DC 8 + PB + CON mod, taking 2d10 acid damage on a fail — 3d10 at 11th level, 4d10 at 17th; uses = CON modifier per long rest)"],
         languages=["Common", "Elvish or Vedalken"]),

    race("Tabaxi", asi={"DEX": 2, "CHA": 1}, source="VGM",
         traits=["Darkvision 60 ft",
                 "Feline Agility – double speed for one turn. Recharges when you don't move on a turn (speed 0 doesn't trigger recharge — only a turn where you take no movement)",
                 "Cat's Claws – because of your claws, you have a climbing speed of 20 feet. In addition, your claws are natural weapons you can use to make unarmed strikes. If you hit with them, you deal slashing damage equal to 1d4 + your Strength modifier",
                 "Cat's Talent – you have proficiency in the Perception and Stealth skills"],
         languages=["Common", "one of your choice"]),

    race("Tabaxi (MPMM)", asi_flex=2, source="MPMM",
         traits=["Size – Medium or Small, your choice",
                 "Speed – climbing speed equal to your walking speed",
                 "Darkvision 60 ft",
                 "Cat's Claws – unarmed strikes with your claws deal 1d6 + STR slashing damage",
                 "Cat's Talent – proficiency in Perception and Stealth",
                 "Feline Agility – when you move on your turn in combat, you can double your speed until the end of the turn. Once used, can't be used again until you move 0 feet on one of your turns"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Tabaxi (Monsters of the Multiverse) — kept separate from the original VGM version above; climbing speed now matches your walking speed (previously a flat 20 ft), and you can choose Small size instead of Medium."),

    race("Tortle", asi={"STR": 2, "WIS": 1}, source="The Tortle Package",
         traits=['Claws – your claws are natural weapons you can use to make unarmed strikes. If you hit with them, you deal slashing damage equal to 1d4 + your Strength modifier',
                 'Hold Breath – you can hold your breath for up to 1 hour at a time',
                 "Natural Armor – due to your shell and the shape of your body, you are ill-suited to wearing armor. Your shell provides ample protection: your base AC is 17 (this armor is natural and is never separate from you). The +2 bonus from shields applies normally while you're using your natural armor",
                 "Shell Defense – action: withdraw into your shell. Until you emerge, +4 AC, advantage on STR and CON saving throws, disadvantage on DEX saving throws, prone, speed 0 (can't increase), can't take reactions; the only action you can take is a bonus action to emerge",
                 'Survival Instinct – you gain proficiency in the Survival skill. Tortle are born survivors, and this connection to the natural world is a fundamental part of your upbringing'],
         languages=["Common", "Aquan"]),

    race("Tortle (MPMM)", asi_flex=2, source="MPMM",
         traits=["Size – Medium or Small, your choice",
                 "Claws – unarmed strikes with your claws deal 1d6 + STR slashing damage",
                 'Hold Breath – you can hold your breath for up to 1 hour',
                 "Natural Armor – your shell gives you a base AC of 17 (your Dexterity modifier doesn't affect this). You can't wear light, medium, or heavy armor, but a shield's bonus applies as normal",
                 "Nature's Intuition – proficiency in one of: Animal Handling, Medicine, Nature, Perception, Stealth, or Survival",
                 "Shell Defense – action: withdraw into your shell. Until you emerge, +4 AC, advantage on STR and CON saving throws, disadvantage on DEX saving throws, prone, speed 0 (can't increase), can't take reactions; the only action you can take is a bonus action to emerge"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Tortle (Monsters of the Multiverse) — kept separate from the original Tortle Package version above; claw damage increases to 1d6, Survival Instinct becomes a choice among several skills (Nature's Intuition) instead of always Survival, and you can choose Small size instead of Medium."),

    race("Triton", asi={"STR": 1, "CON": 1, "CHA": 1}, source="VGM",
         traits=["Darkvision 60 ft", "Amphibious", "Swim speed 30 ft",
                 'Control Air and Water – you can cast Fog Cloud once per long rest. At 3rd level, you can also cast Gust of Wind once per long rest. At 5th level, you can also cast Wall of Water once per long rest. Charisma is your spellcasting ability',
                 'Emissary of the Sea – you can communicate simple ideas with beasts that can breathe water. They can understand the meaning of your words, though you have no special ability to understand them in return',
                 'Guardians of the Depths – adapted to the cold, crushing depths of the ocean, you have resistance to cold damage'],
         languages=["Common", "Primordial"]),

    race("Triton (MPMM)", asi_flex=2, source="MPMM",
         traits=["Darkvision 60 ft", "Amphibious",
                 "Swim speed equal to your walking speed",
                 'Control Air and Water – cast Fog Cloud once per long rest (or with a spell slot); at 3rd level also Gust of Wind, and at 5th level also Water Walk, each once per long rest (or with a spell slot). Spellcasting ability is INT, WIS, or CHA (choose when you select this race)',
                 'Emissary of the Sea – you can communicate simple ideas with any Beast, Elemental, or Monstrosity that has a swimming speed. It can understand your words, though you have no special ability to understand it in return',
                 'Guardian of the Depths – adapted to the frigid ocean depths, you have resistance to cold damage'],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Triton (Monsters of the Multiverse) — kept separate from the original VGM version above; Control Air and Water swaps Wall of Water for Water Walk."),

    race("Vedalken", asi={"INT": 2, "WIS": 1}, source="GGR",
         traits=["Vedalken Dispassion – advantage on all Intelligence, Wisdom, and Charisma saving throws",
                 "Tireless Precision – proficiency in one of the following skills of your choice: Arcana, History, Investigation, Medicine, Performance, or Sleight of Hand. You're also proficient with one tool of your choice. Whenever you make an ability check with the chosen skill or tool, roll a d4 and add the result to the check's total",
                 "Partially Amphibious – by absorbing oxygen through your skin, you can breathe underwater for up to 1 hour. Once you've reached that limit, you can't use this trait again until you finish a long rest"],
         languages=["Common", "Vedalken", "1 of your choice"]),

    # ── Tasha's Cauldron / Van Richten's ──────────────────────────────────────

    race("Verdan", asi={"CON": 1, "CHA": 2}, source="AI",
         traits=[
             "Size – you are Small at 1st level; at 5th level, you undergo a growth spurt and become Medium",
             "Telepathic Insight – your mind's connection to the larger psychic web of existence gives you an intuitive read on others. You have advantage on Wisdom and Charisma saving throws",
             "Limited Telepathy – you can mentally communicate simple ideas, emotions, and images to any creature within 30 feet that you can see. The creature understands you, though this doesn't grant it the ability to telepathically respond. The target need not share a language with you",
             'Persuasive – your natural charisma and empathy make you good at bending others to your point of view. You have proficiency in the Persuasion skill',
             "Black Blood Healing – when you roll a 1 or 2 on any Hit Die you spend at the end of a short rest, you can reroll the die and must use the new roll",
         ],
         languages=["Common", "Goblin", "one other of your choice"]),

    # ── DRAGONMARKED RACES (Eberron: Rising from the Last War) ───────────────

    race("Yuan-ti Pureblood", asi_flex=2, source="MPMM/VGM",
         traits=["Darkvision 60 ft",
                 'Innate Spellcasting – you know the Poison Spray cantrip. You can cast Animal Friendship (targeting only snakes) at will. At 3rd level you can cast Suggestion once per long rest without a spell slot. Choose Intelligence, Wisdom, or Charisma as your spellcasting ability for these spells',
                 'Magic Resistance – you have advantage on saving throws against spells and other magical effects'],
         languages=["Common", "Abyssal", "Draconic"],
         subraces=[
             "Pureblood MPMM (default) – flexible ASI; Poison Resilience: advantage on saves against the poisoned condition, and resistance to poison damage",
             "Pureblood VGM – +CHA 2, +INT 1; Poison Immunity: immune to poison damage and the poisoned condition entirely; spellcasting ability for the innate spells is fixed as Charisma",
         ]),

    # ── Elemental Evil / SCAG ─────────────────────────────────────────────────

    # ── Eberron (A–Z) ───────────────────────────────────────────────────────
    race("Changeling", asi={"CHA": 2}, asi_flex=1, source="ERLW",
         traits=["Shapechanger – action: change appearance and voice to any Medium humanoid (height/weight/facial features). You determine specifics. Clothing and equipment don't change",
                 "Changeling Instincts – 2 skills from Deception/Insight/Intimidation/Persuasion"],
         languages=["Common", "2 of your choice"]),

    race("Changeling (MPMM)", asi_flex=2, source="MPMM",
         traits=["Size – Medium or Small, your choice", "Fey creature type",
                 "Changeling Instincts – proficiency in two of: Deception, Insight, Intimidation, Performance, or Persuasion",
                 "Shapechanger – action: change your appearance and voice, including adjusting your height between Medium and Small. You can appear as a member of another race (no game statistics change), but can't duplicate an individual you've never seen, and must keep the same basic limb arrangement. Clothing and equipment don't change. Lasts until you revert as an action or die"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Changeling (Monsters of the Multiverse) — kept separate from the original ERLW version above; adds the Fey creature type and a Small/Medium size choice, drops Performance from the old skill list's absence (now included), and grants one fewer bonus language (1 instead of 2)."),

    race("Kalashtar", asi={"WIS": 2, "CHA": 1}, source="ERLW",
         traits=['Dual Mind – you have advantage on all Wisdom saving throws',
                 'Mental Discipline – you have resistance to psychic damage',
                 "Mind Link – you can speak telepathically to any creature you can see, provided the creature is within a number of feet of you equal to 10 times your level. You don't need to share a language with the creature for it to understand your telepathic utterances, but the creature must be able to understand at least one language. Additionally, you can use your action to give a creature you're speaking to this way the ability to speak telepathically back to you for 1 hour or until you end the effect (no action required); the creature must be able to see you and be within range. You can grant this to only one creature at a time — granting it to a new creature takes it away from whoever had it",
                 "Severed from Dreams – kalashtar sleep but don't connect to the plane of dreams as other creatures do. Instead, their minds draw from the memories of their otherworldly spirit while they sleep. You are immune to spells and other magical effects that require you to dream, like the Dream spell, but not to spells and effects that put you to sleep, like the Sleep spell"],
         languages=["Common", "Quori", "one of your choice"]),

    race("Shifter", source="ERLW",
         traits=["Darkvision 60 ft", 'Keen Senses – you have proficiency in the Perception skill',
                 'Shifting – as a bonus action, you can assume a more bestial appearance. This transformation lasts for 1 minute, until you die, or until you revert as a bonus action. When you shift, you gain temporary hit points equal to your proficiency bonus + your Constitution modifier (minimum 1). Your subrace determines additional benefits while shifted. Once per short or long rest'],
         subraces=["Beasthide (+CON 2, +STR 1; while Shifting, gain +1 AC and temporary HP equal to your CON modifier + your level, and you can take the Dodge action as a bonus action each turn while shifted)",
                   "Longtooth (+STR 2, +CON 1; while Shifting, grow fangs you can use as a natural weapon dealing 1d6 + STR piercing damage, and attack with them as a bonus action)",
                   "Swiftstride (+DEX 2, +CHA 1; base walking speed increases to 35 feet; while Shifting, gain +10 ft speed, and once per turn when a creature hits you with an attack you can use your reaction to move up to half your speed without provoking opportunity attacks)",
                   "Wildhunt (+WIS 2, +DEX 1; you can't be surprised while conscious; while Shifting, gain advantage on WIS checks, and you know the location of any hostile creature within 10 feet even if it's hidden or invisible, provided it isn't behind total cover)"]),

    race("Shifter (MPMM)", asi_flex=2, source="MPMM",
         traits=["Bestial Instincts – proficiency in one of: Acrobatics, Athletics, Intimidation, or Survival",
                 "Darkvision 60 ft",
                 "Shifting – bonus action: assume a more bestial appearance for 1 minute (until you die or revert as a bonus action), gaining temp HP equal to 2 × your proficiency bonus. Uses = proficiency bonus, all regained on a long rest. Choose one benefit when you select this race, active only while shifted: Beasthide (+1d6 more temp HP when you shift; +1 AC), Longtooth (bonus action: fangs deal 1d6 + STR piercing as an unarmed strike), Swiftstride (+10 ft speed; reaction to move up to 10 ft, no opportunity attacks, when a creature ends its turn within 5 ft of you), or Wildhunt (advantage on WIS checks; no creature within 30 ft can attack you with advantage unless you're incapacitated)"],
         languages=["Common", "one other of your choice"],
         notes="A newer, mechanically revised printing of Shifter (Monsters of the Multiverse) — kept separate from the original ERLW version above. Merges the old 4 fixed-ASI subraces into a single flexible-ASI race with one Shifting-benefit choice made at character creation; Shifting's temp HP and uses now scale with proficiency bonus and reset only on a long rest, instead of the old flat, short-or-long-rest version, and several of the per-benefit mechanics changed (e.g. Beasthide grants flat temp HP + AC rather than CON-mod-plus-level HP and a bonus Dodge action)."),

    race("Warforged", asi={"CON": 2}, asi_flex=1, source="ERLW",
         traits=["Constructed Resilience – you were created to have remarkable fortitude, represented by the following benefits: you have advantage on saving throws against being poisoned, you have resistance to poison damage, you are immune to disease, you don't need to eat, drink, or breathe, and you don't need to sleep. Magic can't put you to sleep",
                 "Immune to magical aging effects",
                 "Sentry's Rest – when you take a long rest, you must spend at least 6 hours in an inactive, motionless state, rather than sleeping. In this state you appear inert, but it doesn't render you unconscious, and you can see and hear as normal while in the resting state",
                 "Integrated Protection – your body has built-in defensive layers, which can be enhanced with armor. You gain a flat +1 bonus to Armor Class. You can don only armor with which you have proficiency. To don armor, you must incorporate it into your body over the course of 1 hour, during which you must remain in contact with the armor; to doff armor, you must spend 1 hour removing it (you can rest while donning/doffing). While you live, your armor can't be removed from your body against your will",
                 'Specialized Design – you gain one skill proficiency and one tool proficiency of your choice'],
         languages=["Common", "one of your choice"]),

    # ── Mythic Odysseys of Theros / GGR ───────────────────────────────────────

    # ── Spelljammer (A–Z) ───────────────────────────────────────────────────
    race("Astral Elf", asi_flex=2, source="AAG",
         traits=["Darkvision 60 ft",
                 "Fey Ancestry – advantage on saving throws you make to avoid or end the charmed condition on yourself",
                 "Keen Senses – proficiency in the Perception skill",
                 "Starlight Step – bonus action: teleport up to 30 ft to an unoccupied space you can see. Usable a number of times equal to your proficiency bonus, regained on a long rest",
                 "Astral Trance – you don't need to sleep, and magic can't put you to sleep; you can finish a long rest in 4 hours spent in a trancelike meditation, remaining conscious throughout. Whenever you finish this trance, you gain proficiency in one skill of your choice and with one weapon or tool of your choice, retained until you finish your next long rest",
                 "Astral Fire – you know one of Dancing Lights, Light, or Sacred Flame (your choice); Intelligence, Wisdom, or Charisma is your spellcasting ability for it (your choice)"],
         languages=["Common", "one other language of your choice"]),

    race("Autognome", size="Small", asi_flex=2, source="AAG",
         traits=["Armored Casing – you are encased in thin metal or some other material. While you aren't wearing armor, your base Armor Class is 13 + your Dexterity modifier",
                 "Built for Success – you can add a d4 to one attack roll, ability check, or saving throw you make, choosing to do so after seeing the d20 roll but before the effects are resolved. Uses = proficiency bonus per long rest",
                 "Healing Machine – if Mending is cast on you, you can spend a Hit Die to roll it and regain that many HP + your CON modifier (min 1). You also benefit from Cure Wounds, Healing Word, Mass Cure Wounds, Mass Healing Word, and Spare the Dying, despite normally not affecting Constructs",
                 "Mechanical Nature – you have resistance to poison damage, immunity to disease, advantage on saving throws against being paralyzed or poisoned, and you don't need to eat, drink, or breathe",
                 "Sentry's Rest – when you take a long rest, you spend at least 6 hours in an inactive, motionless state instead of sleeping. You appear inert but remain conscious",
                 'Specialized Design – you gain two tool proficiencies of your choice'],
         languages=["Common", "one of your choice"]),

    race("Giff", asi_flex=2, source="AAG",
         traits=["Speed – you have a swimming speed equal to your walking speed",
                 "Astral Spark – when you hit a target with a simple or martial weapon, you can cause it to take extra force damage equal to your proficiency bonus (once per turn). Uses = proficiency bonus per long rest",
                 "Firearms Mastery – proficiency with all firearms; ignore the loading property of any firearm; attacking at long range with a firearm doesn't impose disadvantage on your attack roll",
                 'Hippo Build – advantage on Strength-based ability checks and Strength saving throws. Additionally, you count as one size larger when determining your carrying capacity and the weight you can push, drag, or lift'],
         languages=["Common", "one of your choice"]),

    race("Hadozee", asi={}, asi_flex=2, source="SAiS",
         traits=[
             "Size – you are Small or Medium, your choice",
             "Speed – you have a climbing speed equal to your walking speed",
             "Glide – when you fall at least 10 ft above the ground, use your reaction to extend your skin membranes and glide horizontally a number of feet equal to your walking speed (you choose the direction), taking 0 damage from the fall",
             'Dexterous Feet – as a bonus action, you can use your feet to manipulate an object, open or close a door or container, or pick up/set down a Tiny object',
             "Hadozee Dodge – when you take damage, use your reaction to roll a d6, add your proficiency bonus, and reduce the damage by that total (min 0). Uses = proficiency bonus per long rest",
         ],
         languages=["Common", "Hadozee"],
         speed=30),

    race("Plasmoid", asi_flex=2, source="AAG",
         traits=["Size – you are Small or Medium, your choice",
                 'Amorphous – you can squeeze through a space as narrow as 1 inch wide, provided you are wearing and carrying nothing. You have advantage on ability checks you make to initiate or escape a grapple',
                 "Darkvision 60 ft",
                 "Hold Breath – you can hold your breath for 1 hour",
                 "Natural Resilience – you have resistance to acid and poison damage, and advantage on saving throws against being poisoned",
                 "Shape Self – as an action (if not incapacitated), reshape your body to give yourself a head, one or two arms, one or two legs, and makeshift hands and feet, or revert to a limbless blob; while humanlike, you can wear clothing/armor made for a Humanoid your size. As a bonus action, extrude (or reabsorb) a pseudopod up to 6 in. wide and 10 ft long, which can manipulate an object, open/close a door or container, or pick up/set down a Tiny object — it has no sensory organs and can't attack, activate magic items, or lift more than 10 lbs"],
         languages=["Common", "one of your choice"]),

    race("Thri-kreen", asi_flex=2, source="AAG",
         traits=["Size – you are Small or Medium, your choice",
                 "Darkvision 60 ft",
                 "Chameleon Carapace – while not wearing armor, your carapace gives you a base AC of 13 + your DEX modifier. As an action, you can change its color to match your surroundings, giving advantage on DEX (Stealth) checks to hide there",
                 'Secondary Arms – 2 smaller secondary arms below your primary pair. They can manipulate an object, open/close a door or container, pick up/set down a Tiny object, or wield a light-property weapon (no attack action granted by this alone)',
                 "Sleepless – you don't require sleep and can remain conscious during a long rest, though you must still refrain from strenuous activity to gain its benefit",
                 "Thri-kreen Telepathy – without magic, you can't speak non-Thri-kreen languages you know; instead you can transmit your thoughts telepathically to willing creatures within 120 ft (they need not share a language, but must understand at least one). The link breaks if you move more than 120 ft apart, either of you is incapacitated, or either of you mentally ends it (no action required)"],
         languages=["Common", "one other of your choice"]),




    # ── Special / Custom ──────────────────────────────────────────────────────

    # ── Plane Shift / Multiverse additions ──────────────────────────────────
    race("Merfolk", asi={"CHA": 1}, source="Plane Shift: Ixalan/Zendikar",
         traits=["Amphibious – you can breathe air and water", "Swim speed 30 ft"],
         languages=["Common", "Merfolk"],
         subraces=[
             "Green (Ixalan) (+WIS 2; Mask of the Wild – hide when lightly obscured by foliage/rain/snow/mist; Cantrip – 1 Druid cantrip of your choice, WIS-based)",
             "Blue (Ixalan) (+INT 2; Lore of the Waters – proficiency in History and Nature; Cantrip – 1 Wizard cantrip of your choice, INT-based)",
             "Emeria/Wind Creed (Zendikar) (+WIS 2; proficiency in Deception and Persuasion; Cantrip – 1 Druid cantrip of your choice, WIS-based)",
             "Ula/Water Creed (Zendikar) (+INT 2; proficiency with navigator's tools and in Survival; Cantrip – 1 Wizard cantrip of your choice, INT-based)",
             "Cosi Creed (Zendikar) (+CHA 1 [total +2], +INT 1; proficiency in Sleight of Hand and Stealth; Cantrip – 1 Bard cantrip of your choice, CHA-based)",
         ]),

    race("Kender", asi_flex=2, source="DLSotDQ",
         traits=["Fearless – advantage on saves to avoid/end frightened; once per long rest, treat a failed save against frightened as a success",
                 "Kender Curiosity – proficiency in one of Insight, Investigation, Sleight of Hand, Stealth, or Survival",
                 "Taunt – bonus action: one creature within 60 ft that can hear/understand you makes a WIS save (DC 8 + PB + INT/WIS/CHA mod, chosen when you select this race) or has disadvantage on attack rolls against targets other than you until the start of your next turn. Usable PB times per long rest"],
         languages=["Common"]),

    race("Naga", asi={"CON": 2, "INT": 1}, source="Plane Shift: Amonkhet",
         traits=["Speed Burst – bonus action, both hands free: +5 ft walking speed until end of turn",
                 "Natural Weapons – Bite (1d4+STR piercing; CON save DC 8+PB+CON mod or take 1d4 poison) and Constrict (1d6+STR bludgeoning; target grappled, escape DC 8+PB+STR mod; restrained while grappled; can't constrict a second target at the same time)",
                 "Poison Immunity – immune to poison damage and the poisoned condition",
                 "Poison Affinity – proficiency with the poisoner's kit"],
         languages=["Common", "Naga"]),

    race("Khenra", asi={"DEX": 2, "STR": 1}, speed=35, source="Plane Shift: Amonkhet",
         traits=["Khenra Weapon Training – proficiency with the khopesh, spear, and javelin",
                 "Khenra Twins – if your twin is alive and you can see them, reroll a natural 1 on an attack roll, ability check, or saving throw (must use the new roll); if your twin is dead or you were born without one, you can't be frightened"],
         languages=["Common", "Khenra"]),

    race("Aven", asi={"DEX": 2}, speed=25, source="Plane Shift: Amonkhet",
         traits=["Flight – flying speed of 30 ft; can't use it while wearing medium or heavy armor"],
         languages=["Common", "Aven"],
         subraces=[
             "Ibis-Headed (+INT 1; Kefnet's Blessing – add half your proficiency bonus, rounded down, to Intelligence checks that don't already include it)",
             "Hawk-Headed (+WIS 2; proficiency in Perception; attacking at long range doesn't impose disadvantage on your ranged weapon attacks)",
         ]),

    race("Vampire", asi={"CHA": 2, "INT": 1}, source="Plane Shift: Ixalan/Zendikar",
         traits=["Darkvision 60 ft",
                 "Vampiric Resistance – resistance to necrotic damage",
                 "Bloodthirst – melee attack against a willing, grappled, incapacitated, or restrained creature: 1 piercing + 1d6 necrotic damage on a hit; target's HP maximum is reduced by the necrotic damage dealt (until it finishes a long rest) and you regain that much HP; a target reduced to 0 max HP this way dies",
                 "Feast of Blood – after using Bloodthirst, your speed increases by 10 ft and you have advantage on Strength and Dexterity checks and saving throws for 1 minute"],
         languages=["Common", "Vampire"]),

    race("Siren", asi={"CHA": 2}, speed=25, source="Plane Shift: Ixalan",
         traits=["Flight – flying speed of 30 ft; can't use it while wearing medium or heavy armor",
                 "Siren's Song – you know the Friends cantrip and can cast it without material components"],
         languages=["Common", "Siren"]),

    race("Kor", asi={"DEX": 2, "WIS": 1}, source="Plane Shift: Zendikar",
         traits=["Kor Climbing – climbing speed of 30 ft as long as you aren't encumbered or wearing heavy armor; proficiency in Athletics and Acrobatics",
                 "Lucky – when you roll a 1 on the d20 for an attack roll, ability check, or saving throw, you can reroll the die and must use the new roll",
                 "Brave – advantage on saving throws against being frightened"],
         languages=["Common"]),

    race("Aetherborn", asi={"CHA": 2}, asi_flex=2, source="Plane Shift: Kaladesh",
         traits=["Darkvision 60 ft",
                 "Born of Aether – resistance to necrotic damage",
                 "Menacing – proficiency in the Intimidation skill"],
         languages=["Common", "two other languages of your choice"]),

    # ── Custom ──────────────────────────────────────────────────────────────
    race("Custom Race", asi_flex=2, source="Homebrew",
         traits=["Enter your custom racial traits in the notes field"],
         languages=["Common"]),
]

RACE_NAMES = [r["name"] for r in ALL_RACES]

def get_race(name: str) -> dict:
    for r in ALL_RACES:
        if r["name"] == name:
            return r
    return None

RACE_DICT = {r["name"]: r for r in ALL_RACES}

# ── Dragonborn Draconic Ancestry choices ────────────────────────────────────
# Merged in from the former draconic_ancestry.py — small (40-line), single-
# purpose file that only ever described one race's sub-choice, moved here
# to live alongside the rest of the racial data it belongs to.
# Each entry: dragon_type -> (damage_type, breath_shape, breath_desc)
# Source: PHB + FTD
DRACONIC_ANCESTRY = {
    # ── Chromatic / PHB ───────────────────────────────────────────────────────
    "Black (Acid)":     ("Acid",       "5x30 ft line",  "5 ft wide, 30 ft long line. DEX save."),
    "Blue (Lightning)": ("Lightning",  "5x30 ft line",  "5 ft wide, 30 ft long line. DEX save."),
    "Green (Poison)":   ("Poison",     "15 ft cone",    "15 ft cone. CON save."),
    "Red (Fire)":       ("Fire",       "15 ft cone",    "15 ft cone. DEX save."),
    "White (Cold)":     ("Cold",       "15 ft cone",    "15 ft cone. CON save."),

    # ── Metallic / PHB ────────────────────────────────────────────────────────
    "Brass (Fire)":     ("Fire",       "5x30 ft line",  "5 ft wide, 30 ft long line. DEX save."),
    "Bronze (Lightning)":("Lightning", "5x30 ft line",  "5 ft wide, 30 ft long line. DEX save."),
    "Copper (Acid)":    ("Acid",       "5x30 ft line",  "5 ft wide, 30 ft long line. DEX save."),
    "Gold (Fire)":      ("Fire",       "15 ft cone",    "15 ft cone. DEX save."),
    "Silver (Cold)":    ("Cold",       "15 ft cone",    "15 ft cone. CON save."),

    # ── Gem / FTD (burst, not line/cone) ─────────────────────────────────────
    "Amethyst (Force)":  ("Force",     "15 ft cone",    "15 ft cone. STR save."),
    "Crystal (Radiant)": ("Radiant",   "15 ft cone",    "15 ft cone. CON save."),
    "Emerald (Psychic)": ("Psychic",   "15 ft cone",    "15 ft cone. INT save."),
    "Sapphire (Thunder)":("Thunder",   "15 ft cone",    "15 ft cone. CON save."),
    "Topaz (Necrotic)":  ("Necrotic",  "15 ft cone",    "15 ft cone. CON save."),
}

# Which types are available by subrace
ANCESTRY_BY_SUBRACE = {
    "Standard":    list(DRACONIC_ANCESTRY.keys())[:10],   # PHB chromatic + metallic
    "Chromatic":   [k for k in DRACONIC_ANCESTRY if any(c in k for c in ["Black","Blue","Green","Red","White"])],
    "Metallic":    [k for k in DRACONIC_ANCESTRY if any(c in k for c in ["Brass","Bronze","Copper","Gold","Silver"])],
    "Gem":         [k for k in DRACONIC_ANCESTRY if any(c in k for c in ["Amethyst","Crystal","Emerald","Sapphire","Topaz"])],
    "Draconblood": list(DRACONIC_ANCESTRY.keys())[:10],   # uses PHB types
    "Ravenite":    list(DRACONIC_ANCESTRY.keys())[:10],   # uses PHB types
}

ANCESTRY_NAMES = list(DRACONIC_ANCESTRY.keys())
