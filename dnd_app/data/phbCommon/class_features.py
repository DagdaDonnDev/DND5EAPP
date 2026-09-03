"""
Everything about which named features a class/subclass grants — the
merged home for what used to be three separate files:
  - subclass_features.py: SUBCLASS_FEATURES, the original (class,subclass)
    -> flat feature-name-list data, still the live source the app reads
    from today. Also DIVINE_STRIKE_TYPE (Cleric domain damage types),
    merged in here earlier from its own even-smaller file.
  - class_feature_index.py: CLASS_FEATURE_INDEX + get_class_features(),
    a newer, level-keyed class->{Core/subclass}->features structure.
    NOT YET wired into the app (zero import sites) and only 4 of 14
    classes deep (Artificer, Barbarian, Bard, Fighter) — a work in
    progress intended to eventually replace SUBCLASS_FEATURES above,
    kept side by side with it rather than merged into one shape until
    the newer one has enough coverage to actually take over.
  - tcoe_alternate_features.py: OPTIONAL_CLASS_FEATURES, Tasha's Cauldron
    optional/alternate class features (e.g. Ranger's Deft Explorer
    replacing Natural Explorer) — a genuinely separate system (replaces
    rather than adds), kept as its own clearly-labeled section rather
    than blended into either of the above.

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ═════════════════════════════════════════════════════════════════════════════
# Live subclass feature data (original format, still in active use)
# ═════════════════════════════════════════════════════════════════════════════

SUBCLASS_FEATURES: dict[tuple[str,str], list[str]] = {
    ('Fighter', 'Battle Master'): ['Combat Superiority (Maneuvers + Superiority Dice)', 'Know Your Enemy', 'Improved Combat Superiority', 'Relentless'],
    ('Fighter', 'Champion'): ['Improved Critical', 'Remarkable Athlete', 'Additional Fighting Style', 'Superior Critical', 'Survivor (Champion) – at the start of each of your turns, regain 5 + CON modifier HP if you’re at no more than half your HP max (none of this if at 0 HP)'],
    ('Fighter', 'Eldritch Knight'): ['Spellcasting (EK)', 'Weapon Bond', 'War Magic', 'Eldritch Strike', 'Arcane Charge', 'Improved War Magic'],
    ('Fighter', 'Arcane Archer'): ['Arcane Archer Lore', 'Arcane Shot', 'Magic Arrow', 'Curving Shot', 'Ever-Ready Shot'],
    ('Rogue', 'Thief'): ['Fast Hands', 'Second-Story Work', 'Supreme Sneak', 'Use Magic Device', "Thief's Reflexes"],
    ('Rogue', 'Assassin'): ['Bonus Proficiencies + Assassinate', 'Infiltration Expertise', 'Impostor', 'Death Strike'],
    ('Rogue', 'Arcane Trickster'): ['Spellcasting (AT)', 'Mage Hand Legerdemain', 'Magical Ambush', 'Versatile Trickster', 'Spell Thief'],
    ('Rogue', 'Inquisitive'): ['Ear for Deceit', 'Eye for Detail', 'Insightful Fighting', 'Steady Eye', 'Unerring Eye', 'Eye for Weakness'],
    ('Rogue', 'Mastermind'): ['Master of Intrigue', 'Master of Tactics', 'Insightful Manipulator', 'Misdirection', 'Soul of Deceit'],
    ('Barbarian', 'Totem Warrior'): ['Spirit Seeker + Totem Spirit', 'Aspect of the Beast', 'Spirit Walker', 'Totemic Attunement'],
    ('Barbarian', 'Berserker'): ['Frenzy', 'Mindless Rage', 'Intimidating Presence', 'Retaliation'],
    ('Barbarian', 'Storm Herald'): ['Storm Aura (Lv3)', 'Storm Soul (Lv6)', 'Shielding Storm (Lv10)', 'Raging Storm (Lv14)'],
    ('Barbarian', 'Path of the Wild Magic (TCE)'): ['Magic Awareness + Wild Surge', 'Bolstering Magic', 'Unstable Backlash', 'Controlled Surge'],
    ('Wizard', 'School of Evocation'): ['Evocation Savant', 'Sculpt Spells', 'Potent Cantrip', 'Empowered Evocation', 'Overchannel'],
    ('Wizard', 'School of Abjuration'): ['Abjuration Savant', 'Arcane Ward', 'Projected Ward', 'Improved Abjuration', 'Spell Resistance'],
    ('Wizard', 'School of Illusion'): ['Illusion Savant', 'Improved Minor Illusion', 'Malleable Illusions', 'Illusory Self', 'Illusory Reality'],
    ('Wizard', 'School of Divination'): ['Divination Savant', 'Portent', 'Expert Divination', 'The Third Eye', 'Greater Portent'],
    ('Wizard', 'School of Conjuration'): ['Conjuration Savant', 'Minor Conjuration', 'Benign Transposition', 'Focused Conjuration', 'Durable Summons'],
    ('Wizard', 'School of Necromancy'): ['Necromancy Savant', 'Grim Harvest', 'Undead Thralls', 'Inured to Undeath', 'Command Undead'],
    ('Wizard', 'School of Enchantment'): ['Enchantment Savant', 'Hypnotic Gaze', 'Instinctive Charm', 'Split Enchantment', 'Alter Memories'],
    ('Wizard', 'School of Transmutation'): ['Transmutation Savant', 'Minor Alchemy', "Transmuter's Stone", 'Shapechanger', 'Master Transmuter'],
    ('Cleric', 'Life Domain'): ['Bonus Proficiency (Heavy Armor) + Disciple of Life', 'Blessed Healer', 'Divine Strike', 'Supreme Healing'],
    ('Cleric', 'Light Domain'): ['Bonus Cantrip + Warding Flare', 'Radiance of the Dawn', 'Improved Flare + Potent Spellcasting', 'Corona of Light'],
    ('Cleric', 'Trickery Domain'): ['Blessing of the Trickster + Invoke Duplicity', 'Cloak of Shadows – Channel Divinity: as an action, become invisible until you attack, deal damage, force a saving throw, or 1 minute passes', 'Divine Strike (Trickery)', 'Improved Duplicity'],
    ('Cleric', 'War Domain'): ['War Priest', 'Guided Strike', "War God's Blessing", 'Divine Strike', 'Avatar of Battle'],
    ('Cleric', 'Knowledge Domain'): ['Blessings of Knowledge', 'Channel Divinity: Knowledge of the Ages', 'Channel Divinity: Read Thoughts', 'Potent Spellcasting', 'Visions of the Past'],
    ('Cleric', 'Ambition Domain (Amonkhet)'): ['Warding Flare (Ambition)', 'Channel Divinity: Invoke Duplicity', 'Channel Divinity: Cloak of Shadows', 'Potent Spellcasting', 'Improved Duplicity'],
    # These three are combined into one 1st-level entry, matching every
    # other multi-feature Cleric domain in this file (Life, Light,
    # Trickery, etc.), fitting the 5 level-slots Cleric domain features
    # actually use (1st/2nd/6th/8th/17th).
    ('Cleric', 'Solidarity Domain (Amonkhet)'): ["Bonus Proficiency (Solidarity) + Solidarity's Action", 'Channel Divinity: Preserve Life', "Channel Divinity: Oketra's Blessing", 'Divine Strike', 'Supreme Healing'],
    ('Cleric', 'Strength Domain (Amonkhet)'): ['Bonus Proficiency (Strength) + Acolyte of Strength', 'Channel Divinity: Feat of Strength', "Channel Divinity: Rhonas' Blessing", 'Divine Strike', 'Avatar of Battle'],
    ('Cleric', 'Zeal Domain (Amonkhet)'): ['Bonus Proficiencies (Zeal) + Priest of Zeal', 'Channel Divinity: Consuming Fervor', 'Resounding Strike', 'Divine Strike', 'Blaze of Glory'],
    ('Cleric', 'Nature Domain'): ['Acolyte of Nature', 'Bonus Proficiency (Nature) – proficiency with heavy armor', 'Dampen Elements', 'Divine Strike', 'Master of Nature'],
    ('Cleric', 'Tempest Domain'): ['Bonus Proficiencies (Tempest) – proficiency with martial weapons and heavy armor', 'Wrath of the Storm', 'Destructive Wrath', 'Thunderbolt Strike', 'Divine Strike', 'Stormborn'],
    ('Cleric', 'Death Domain'): ['Bonus Proficiency (Death) – proficiency with martial weapons', 'Reaper', "Touch of Death (Cleric) – when you hit a creature with a melee weapon attack, deal extra necrotic damage equal to 5 + twice your cleric level", 'Inescapable Destruction', 'Divine Strike', 'Improved Reaper'],
    ('Cleric', 'Forge Domain'): ["Bonus Proficiency (Forge) – proficiency with heavy armor and smith's tools", 'Blessing of the Forge', "Artisan's Blessing", 'Soul of the Forge', 'Divine Strike (Forge)', 'Saint of Forge and Fire'],
    ('Druid', 'Circle of the Moon'): ['Combat Wild Shape', 'Circle Forms', 'Primal Strike', 'Elemental Wild Shape', 'Thousand Forms'],
    ('Druid', 'Circle of the Land'): ['Bonus Cantrip', 'Natural Recovery', 'Circle Spells', "Land's Stride", "Nature's Ward", "Nature's Sanctuary"],
    ('Druid', 'Circle of Spores'): ['Halo of Spores', 'Symbiotic Entity', 'Fungal Infestation', 'Spreading Spores', 'Fungal Body'],
    ('Paladin', 'Oath of Devotion'): ['Sacred Weapon + Turn the Unholy', 'Aura of Devotion', 'Purity of Spirit', 'Holy Nimbus'],
    ('Paladin', 'Oath of the Ancients'): ["Nature's Wrath", 'Turn the Faithless', 'Aura of Warding', 'Undying Sentinel', 'Elder Champion'],
    ('Paladin', 'Oath of Vengeance'): ['Abjure Enemy + Vow of Enmity', 'Relentless Avenger', 'Soul of Vengeance', 'Avenging Angel'],
    ('Paladin', 'Oath of the Crown'): ['Champion Challenge', 'Turn the Tide', 'Divine Allegiance', 'Unyielding Saint', 'Exalted Champion'],
    ('Ranger', 'Hunter'): ["Hunter's Prey (Lv3)", 'Defensive Tactics (Lv7)', 'Multiattack (Lv11)', "Superior Hunter's Defense (Lv15)"],
    ('Ranger', 'Beast Master'): ["Ranger's Companion", 'Exceptional Training', 'Bestial Fury', 'Share Spells'],
    ('Ranger', 'Gloom Stalker'): ['Dread Ambusher', 'Umbral Sight', 'Iron Mind', "Stalker's Flurry", 'Shadowy Dodge'],
    ('Monk', 'Way of the Open Hand'): ['Open Hand Technique', 'Wholeness of Body', 'Tranquility', 'Quivering Palm'],
    ('Monk', 'Way of Shadow'): ['Shadow Arts', 'Shadow Step', 'Cloak of Shadows', 'Opportunist'],
    ('Monk', 'Way of the Four Elements'): ['Disciple of the Elements', 'Elemental Disciplines (Lv6)', 'Elemental Disciplines (Lv11)', 'Elemental Disciplines (Lv17)'],
    ('Monk', 'Way of the Long Death'): ['Touch of Death (Monk) – when you reduce a creature to 0 HP with a melee attack, you gain temporary HP equal to 3 + your Ki spent (min 1) + your monk level', 'Hour of Reaping', 'Mastery of Death', 'Touch of the Long Death'],
    ('Warlock', 'The Archfey'): ['Fey Presence', 'Misty Escape', 'Beguiling Defenses', 'Dark Delirium'],
    ('Warlock', 'The Fiend'): ["Dark One's Blessing", "Dark One's Own Luck", 'Fiendish Resilience', 'Hurl Through Hell'],
    ('Warlock', 'The Great Old One'): ['Awakened Mind', 'Entropic Ward', 'Thought Shield', 'Create Thrall'],
    ('Warlock', 'The Hexblade (XGE)'): ["Hexblade's Curse", 'Hex Warrior', 'Accursed Specter', 'Armor of Hexes', 'Master of Hexes'],
    ('Warlock', 'The Celestial (XGE)'): ['Expanded Spell List', 'Bonus Cantrips', 'Healing Light', 'Radiant Soul', 'Celestial Resilience', 'Searing Vengeance'],
    ('Sorcerer', 'Draconic Bloodline'): ['Dragon Ancestor', 'Draconic Resilience', 'Elemental Affinity', 'Dragon Wings', 'Draconic Presence'],
    ('Sorcerer', 'Wild Magic'): ['Wild Magic Surge', 'Tides of Chaos', 'Bend Luck', 'Controlled Chaos', 'Spell Bombardment'],
    ('Sorcerer', 'Shadow Magic'): ['Eyes of the Dark', 'Strength of the Grave', 'Hound of Ill Omen', 'Shadow Walk', 'Umbral Form'],
    ('Bard', 'College of Lore'): ['Bonus Proficiencies + Cutting Words', 'Additional Magical Secrets', 'Peerless Skill'],
    ('Bard', 'College of Valor'): ['Bonus Proficiencies + Combat Inspiration', 'Extra Attack', 'Battle Magic'],
    ('Bard', 'College of Glamour'): ['Mantle of Inspiration', 'Enthralling Performance', 'Mantle of Majesty', 'Unbreakable Majesty'],
    ('Bard', 'College of Swords'): ['Bonus Proficiencies (Swords) – proficiency with medium armor and the scimitar; a simple/martial melee weapon you’re proficient with can serve as a spellcasting focus', 'Fighting Style (Swords) – choose Dueling (+2 damage, one-handed melee weapon with no other weapon drawn) or Two-Weapon Fighting (add ability modifier to your off-hand attack’s damage)', 'Blade Flourish', 'Extra Attack', "Master's Flourish"],
    ('Artificer', 'Alchemist'): ['Tool Proficiency', 'Alchemist Spells', 'Experimental Elixir', 'Alchemical Savant', 'Restorative Reagents', 'Chemical Mastery'],
    ('Artificer', 'Artillerist'): ['Tool Proficiency', 'Artillerist Spells', 'Eldritch Cannon', 'Arcane Firearm', 'Fortified Position', 'Explosive Cannon'],
    ('Artificer', 'Battle Smith'): ['Tool Proficiency', 'Battle Smith Spells', 'Battle Ready', 'Steel Defender', 'Extra Attack', 'Arcane Jolt', 'Improved Defender'],
    ('Artificer', 'Armorer'): ['Tools of the Trade', 'Armorer Spells', 'Arcane Armor', 'Armor Model', 'Extra Attack', 'Armor Modifications', 'Perfected Armor'],
    # ── Blood Hunter ─────────────────────────────────────────────────────────
    ("Blood Hunter", "Order of the Ghostslayer"): [
        "Rite of the Dawn + Curse Specialist",
        "Aether Walk",
        "Brand of Sundering",
        "Blood Curse of the Exorcist (Ghostslayer)",
        "Rite Revival",
    ],
    ("Blood Hunter", "Order of the Lycan"): [
        "Heightened Senses + Hybrid Transformation",
        "Stalker's Prowess",
        "Advanced Transformation",
        "Brand of the Voracious",
        "Hybrid Transformation Mastery",
    ],
    ("Blood Hunter", "Order of the Mutant"): [
        "Mutagencraft",
        "Strange Metabolism",
        "Brand of Axiom",
        "Blood Curse of Corrosion (Mutant)",
        "Exalted Mutation",
    ],
    ("Blood Hunter", "Order of the Profane Soul"): [
        "Otherworldly Patron + Pact Magic + Rite Focus",
        "Mystic Frenzy + Revealed Arcana",
        "Brand of the Sapping Scar",
        "Unsealed Arcana",
        "Blood Curse of the Soul Eater (Profane Soul)",
    ],


    # ─── Auto-added: comprehensive coverage for all 73 subclasses ───────────
    ('Barbarian', 'Path of the Ancestral Guardian'): ['Ancestral Protectors', 'Spirit Shield', 'Consult the Spirits', 'Vengeful Ancestors'],
    ('Barbarian', 'Path of the Battlerager'): ['Battlerager Armor', 'Reckless Abandon', 'Battlerager Charge', 'Spiked Retribution'],
    ('Barbarian', 'Path of the Beast'): ['Form of the Beast', 'Bestial Soul', 'Infectious Fury', 'Call the Hunt'],
    ('Barbarian', 'Path of the Berserker'): ['Frenzy', 'Mindless Rage', 'Intimidating Presence', 'Retaliation'],
    ('Barbarian', 'Path of the Giant'): ["Giant's Havoc", "Giant's Might", 'Elemental Cleaver', 'Mighty Impel', 'Demiurgic Colossus'],
    ('Barbarian', 'Path of the Storm Herald'): ['Storm Aura', 'Storm Soul', 'Shielding Storm'],
    ('Barbarian', 'Path of the Totem Warrior'): ['Spirit Seeker', 'Totem Spirit', 'Aspect of the Beast', 'Spirit Walker', 'Totemic Attunement'],
    ('Barbarian', 'Path of the Wild Magic'): ['Magic Awareness', 'Wild Surge', 'Bolstering Magic', 'Unstable Backlash'],
    ('Barbarian', 'Path of the Zealot'): ['Divine Fury', 'Warrior of the Gods', 'Fanatical Focus', 'Zealous Presence', 'Rage Beyond Death'],
    ('Bard', 'College of Creation'): ['Mote of Potential', 'Performance of Creation', 'Animating Performance'],
    ('Bard', 'College of Eloquence'): ['Silver Tongue', 'Unsettling Words', 'Unfailing Inspiration', 'Universal Speech'],
    ('Bard', 'College of Spirits'): ['Guidance of the Spirits', 'Spirit Session', 'Mystic Chronicle', 'Awakened Spirit'],
    ('Bard', 'College of Whispers'): ['Psychic Blades (Whispers) – when you hit with a weapon attack, expend a Bardic Inspiration die to deal an extra 2d6 psychic damage (scales with level) to a creature whose mind you can perceive', 'Words of Terror', 'Mantle of Whispers', 'Shadow Lore'],
    ('Cleric', 'Arcana Domain'): ['Arcana Domain Spells', 'Arcane Initiate', 'Channel Divinity: Arcane Abjuration', 'Spell Breaker', 'Potent Spellcasting', 'Arcane Mastery'],
    ('Cleric', 'Grave Domain'): ['Grave Domain Spells', 'Circle of Mortality', 'Eyes of the Grave', 'Channel Divinity: Path to the Grave', "Sentinel at Death's Door", 'Keeper of Souls'],
    ('Cleric', 'Order Domain'): ['Order Domain Spells', 'Voice of Authority', "Order's Demand", 'Embolden', 'Divine Strike', "Order's Wrath"],
    ('Cleric', 'Peace Domain'): ['Peace Domain Spells', 'Emboldening Bond', 'Channel Divinity: Balm of Peace', 'Protective Bond', 'Expert Divination (Peace) – at 17th level, when you cast a divination spell using a spell slot, regain one expended spell slot of lower level', 'Improved Emboldening Bond'],
    ('Cleric', 'Twilight Domain'): ['Twilight Domain Spells', 'Eyes of Night', 'Channel Divinity: Twilight Sanctuary', 'Vigilant Blessing', 'Divine Strike', 'Twilight Shroud'],
    ('Druid', 'Circle of Dreams'): ['Balm of the Summer Court', 'Hearth of Moonlight and Shadow', 'Hidden Paths', 'Walker in Dreams'],
    ('Druid', 'Circle of the Shepherd'): ['Speech of the Woods', 'Spirit Totem', 'Mighty Summoner', 'Guardian Spirit'],
    ('Druid', 'Circle of Stars'): ['Star Map', 'Starry Form', 'Cosmic Omen', 'Full of Stars'],
    ('Druid', 'Circle of Wildfire'): ['Summon Wildfire Spirit', 'Enhanced Bond', 'Cauterizing Flames', 'Blazing Revival'],
    ('Fighter', 'Banneret'): ['Rallying Cry', 'Royal Envoy', 'Inspiring Surge', 'Bulwark'],
    ('Fighter', 'Cavalier'): ['Born to the Saddle', 'Unwavering Mark', 'Warding Maneuver', 'Hold the Line', 'Ferocious Charger', 'Vigilant Defender'],
    ('Fighter', 'Echo Knight'): ['Manifest Echo', 'Unleash Incarnation', 'Echo Avatar', 'Shadow Martyr', 'Reclaim Potential'],
    ('Fighter', 'Psi Warrior'): ['Psionic Power – gain Psionic Energy dice (a number of d6s equal to twice your proficiency bonus); spend them to empower a weapon attack with extra force damage, protect yourself with a floating shield (+3 AC), or move yourself/objects telekinetically. Dice refresh on a long rest', 'Telekinetic Adept', 'Guarded Mind', 'Bulwark of Force', 'Telekinetic Master'],
    ('Fighter', 'Rune Knight'): ["Bonus Proficiencies (Rune Knight) – proficiency with smith's tools, and learn to speak/read/write Giant", 'Rune Carver', "Giant's Might", 'Great Stature', 'Master of Runes'],
    ('Fighter', 'Samurai'): ['Bonus Proficiency', 'Fighting Spirit', 'Elegant Courtier', 'Tireless Spirit', 'Rapid Strike', 'Strength Before Death'],
    ('Monk', 'Way of the Ascendant Dragon'): ['Draconic Strike', 'Breath of the Dragon', 'Wings Unfurled', 'Aspect of the Dragon', 'Ascendant Aspect'],
    ('Monk', 'Way of the Astral Self'): ['Arms of the Astral Self', 'Visage of the Astral Self', 'Body of the Astral Self', 'Awakened Astral Self'],
    ('Monk', 'Way of the Drunken Master'): ["Bonus Proficiencies (Drunken Master) – proficiency in Performance and with brewer's supplies (if you don't already have them)", 'Drunken Technique', 'Tipsy Sway', "Drunkard's Luck", 'Intoxicated Frenzy'],
    ('Monk', 'Way of the Kensei'): ['Path of the Kensei', 'Agile Parry', "Kensei's Shot", 'Sharpen the Blade', 'Unerring Accuracy'],
    ('Monk', 'Way of Mercy'): ['Implements of Mercy', 'Hand of Healing', 'Hand of Harm', "Physician's Touch", 'Flurry of Healing and Harm', 'Hand of Ultimate Mercy'],
    ('Monk', 'Way of the Shadow'): ['Shadow Arts', 'Shadow Step', 'Cloak of Shadows', 'Opportunist'],
    ('Monk', 'Way of the Sun Soul'): ['Radiant Sun Bolt', 'Searing Arc Strike', 'Searing Sunburst', 'Sun Shield'],
    ('Paladin', 'Oath of Conquest'): ['Oath of Conquest Spells', 'Channel Divinity: Conquering Presence', 'Channel Divinity: Guided Strike', 'Aura of Conquest', 'Scornful Rebuke', 'Invincible Conqueror'],
    ('Paladin', 'Oath of Glory'): ['Oath of Glory Spells', 'Peerless Athlete', 'Channel Divinity: Inspiring Smite', 'Aura of Alacrity', 'Glorious Defense', 'Living Legend'],
    ('Paladin', 'Oath of Redemption'): ['Oath of Redemption Spells', 'Channel Divinity: Emissary of Peace', 'Channel Divinity: Rebuke the Violent', 'Aura of the Guardian', 'Protective Spirit', 'Emissary of Redemption'],
    ('Paladin', 'Oath of the Watchers'): ['Oath of the Watchers Spells', "Channel Divinity: Watcher's Will", 'Channel Divinity: Abjure the Extraplanar', 'Aura of the Sentinel', 'Vigilant Rebuke', 'Mortal Bulwark'],
    ('Paladin', 'Oathbreaker'): ['Oathbreaker Spells', 'Channel Divinity: Control Undead', 'Channel Divinity: Dreadful Aspect', 'Aura of Despair', 'Supernatural Resistance'],
    ('Ranger', 'Drakewarden'): ['Draconic Gift', 'Summon Drake Companion', 'Bond of Fang and Scale', "Drake's Breath", 'Perfected Bond'],
    ('Ranger', 'Fey Wanderer'): ['Dreadful Strikes', 'Fey Wanderer Spells', 'Otherworldly Glamour', 'Beguiling Twist', 'Fey Reinforcements', 'Misty Wanderer'],
    ('Ranger', 'Horizon Walker'): ['Detect Portal', 'Planar Warrior', 'Ethereal Step', 'Distant Strike', 'Spectral Defense'],
    ('Ranger', 'Monster Slayer'): ["Hunter's Sense", "Slayer's Prey", 'Supernatural Defense', "Magic-User's Nemesis", "Slayer's Counter"],
    ('Ranger', 'Swarmkeeper'): ['Gathered Swarm', 'Swarmkeeper Magic', 'Writhing Tide', 'Mighty Swarm', 'Swarming Dispersal'],
    ('Rogue', 'Phantom'): ['Whispers of the Dead', 'Wails from the Grave', 'Tokens of the Departed', 'Ghost Walk'],
    ('Rogue', 'Scout'): ['Skirmisher', 'Survivalist', 'Superior Mobility', 'Ambush Master'],
    ('Rogue', 'Soulknife'): ['Psionic Power', 'Psychic Blades', 'Soul Blades', 'Psychic Veil', 'Rend Mind'],
    ('Rogue', 'Swashbuckler'): ['Fancy Footwork', 'Rakish Audacity', 'Panache', 'Elegant Maneuver', 'Master Duelist'],
    ('Sorcerer', 'Aberrant Mind'): ['Psionic Spells', 'Telepathic Speech', 'Psionic Sorcery', 'Psychic Defenses', 'Revelation in Flesh', 'Warping Implosion'],
    ('Sorcerer', 'Clockwork Soul'): ['Clockwork Magic', 'Restore Balance', 'Bastion of Law', 'Trance of Order', 'Clockwork Cavalcade'],
    ('Sorcerer', 'Divine Soul'): ['Divine Magic', 'Favored by the Gods', 'Empowered Healing', 'Otherworldly Wings', 'Unearthly Recovery'],
    ('Sorcerer', 'Lunar Sorcery'): ['Lunar Embodiment + Moon Fire', 'Lunar Boons + Waxing and Waning', 'Lunar Empowerment', 'Lunar Phenomenon'],
    ('Sorcerer', 'Pyromancer'): ['Heart of Fire', 'Fire in the Veins', "Pyromancer's Fury", 'Fiery Soul'],
    ('Sorcerer', 'Storm Sorcery'): ['Wind Speaker', 'Tempestuous Magic', 'Heart of the Storm', 'Storm Guide', "Storm's Fury", 'Wind Soul'],
    ('Warlock', 'The Celestial'): ['Bonus Cantrips', 'Healing Light', 'Radiant Soul', 'Celestial Resilience', 'Searing Vengeance'],
    ('Warlock', 'The Fathomless'): ['Tentacle of the Deep', 'Gift of the Sea', 'Oceanic Soul', 'Guardian Coil', 'Grasping Tentacles', 'Fathomless Plunge'],
    ('Warlock', 'The Genie'): ["Genie's Vessel", "Genie's Wrath", 'Elemental Gift', 'Sanctuary Vessel', 'Limited Wish'],
    ('Warlock', 'The Hexblade'): ["Hexblade's Curse", 'Hex Warrior', 'Accursed Specter', 'Armor of Hexes', 'Master of Hexes'],
    ('Warlock', 'The Undead'): ['Form of Dread', 'Grave Touched', 'Necrotic Husk', 'Spirit Projection'],
    ('Warlock', 'The Undying'): ['Among the Dead', 'Defy Death', 'Undying Nature', 'Indestructible Life'],
    ('Wizard', 'Abjuration'): ['Abjuration Savant', 'Arcane Ward', 'Projected Ward', 'Improved Abjuration', 'Spell Resistance'],
    ('Wizard', 'Bladesinging'): ['Training in War and Song', 'Bladesong', 'Extra Attack', 'Song of Defense', 'Song of Victory'],
    ('Wizard', 'Chronurgy Magic'): ['Chronurgy Savant', 'Temporal Awareness', 'Momentary Stasis', 'Arcane Abeyance', 'Convergent Future'],
    ('Wizard', 'Conjuration'): ['Conjuration Savant', 'Minor Conjuration', 'Benign Transposition', 'Focused Conjuration', 'Durable Summons'],
    ('Wizard', 'Divination'): ['Divination Savant', 'Portent', 'Expert Divination', 'The Third Eye', 'Greater Portent'],
    ('Wizard', 'Enchantment'): ['Enchantment Savant', 'Hypnotic Gaze', 'Instinctive Charm', 'Split Enchantment', 'Alter Memories'],
    ('Wizard', 'Evocation'): ['Evocation Savant', 'Sculpt Spells', 'Potent Cantrip', 'Empowered Evocation', 'Overchannel'],
    ('Wizard', 'Graviturgy Magic'): ['Graviturgy Savant', 'Adjust Density', 'Gravity Well', 'Violent Attraction', 'Event Horizon'],
    ('Wizard', 'Illusion'): ['Illusion Savant', 'Improved Minor Illusion', 'Malleable Illusions', 'Illusory Self', 'Illusory Reality'],
    ('Wizard', 'Necromancy'): ['Necromancy Savant', 'Grim Harvest', 'Undead Thralls', 'Inured to Undeath', 'Command Undead'],
    ('Wizard', 'Order of Scribes'): ['Wizardly Quill', 'Awakened Spellbook', 'Manifest Mind', 'Master Scrivener', 'One with the Word'],
    ('Wizard', 'Transmutation'): ['Transmutation Savant', 'Minor Alchemy', "Transmuter's Stone", 'Shapechanger', 'Master Transmuter'],
    ('Wizard', 'War Magic'): ['Arcane Deflection', 'Tactical Wit', 'Power Surge', 'Durable Magic', 'Deflecting Shroud'],
}

# ── Divine Strike damage types per Cleric domain ────────────────────────────
# Merged in from the former divine_strike.py — small (36-line), single-
# purpose file that only ever described one subclass mechanic, moved here
# to live alongside the rest of the subclass mechanic data it belongs to.
# 8th level: +1d8 on a weapon hit once per turn, +2d8 at 14th. The
# converted damage type varies by domain — most domains convert to a fixed
# element, but War Domain's text explicitly deals "the same type dealt by
# the weapon" (no conversion), and Nature Domain lets the caster choose
# cold/fire/lightning each time it's used.
# Source: individual domain pages at dnd5e.wikidot.com/cleric:<domain>.
#
# Each value is one of:
#   - a damage type string, for domains that convert to a fixed element
#   - "weapon", for domains where Divine Strike adds more of the weapon's
#     own damage type rather than converting it
#   - a list of type strings, for domains where the type is chosen by the
#     player each time (the first entry is used as the default for display
#     purposes, since per-use choice isn't tracked at this granularity)
DIVINE_STRIKE_TYPE = {
    "Life Domain": "radiant",
    "Trickery Domain": "psychic",
    "War Domain": "weapon",
    "Nature Domain": ["cold", "fire", "lightning"],
    "Forge Domain": "fire",
    "Order Domain": "psychic",
    "Twilight Domain": "radiant",
    "Tempest Domain": "thunder",
    "Death Domain": "necrotic",
    # The Amonkhet (Plane Shift) domains reference the standard Divine
    # Strike feature without specifying a conversion, so these use the
    # weapon's own damage type rather than assuming a specific element.
    "Solidarity Domain": "weapon",
    "Strength Domain": "weapon",
    "Zeal Domain": "weapon",
    # Domains without Divine Strike (Arcana, Grave, Knowledge, Light,
    # Peace, Ambition) are intentionally absent from this table.
}

# ═════════════════════════════════════════════════════════════════════════════
# Newer, level-keyed class/subclass feature index (work in progress, not yet wired in)
# ═════════════════════════════════════════════════════════════════════════════

CLASS_FEATURE_INDEX: dict[str, dict] = {

    "Artificer": {
        # Level-keyed from classes.py CLASS_DICT["Artificer"]["features"].
        "Core": {
            1: ["Magical Tinkering"],
            2: ["Infuse Item"],
            3: ["The Right Tool for the Job"],
            6: ["Tool Expertise"],
            7: ["Flash of Genius"],
            10: ["Magic Item Adept"],
            11: ["Spell-Storing Item"],
            14: ["Magic Item Savant"],
            18: ["Magic Item Master"],
            20: ["Soul of Artifice"],
        },
        # Artificer subclasses grant features at 3rd, 5th, 9th, and 15th
        # level. Grouped below by that 4-slot pattern where the grouping
        # is confirmable; Armorer and Artillerist's exact within-slot
        # grouping is less certain (kept flat, unverified).
        "Alchemist": {
            3: ["Tool Proficiency", "Alchemist Spells", "Experimental Elixir"],
            5: ["Alchemical Savant"],
            9: ["Restorative Reagents"],
            15: ["Chemical Mastery"],
        },
        "Armorer": {
            3: ["Tools of the Trade", "Armorer Spells", "Arcane Armor", "Armor Model"],
            5: ["Extra Attack"],
            9: ["Armor Modifications"],
            15: ["Perfected Armor"],
        },
        "Artillerist": {
            3: ["Tool Proficiency", "Artillerist Spells", "Eldritch Cannon"],
            5: ["Arcane Firearm"],
            9: ["Fortified Position"],
            15: ["Explosive Cannon"],
        },
        "Battle Smith": {
            3: ["Tool Proficiency", "Battle Smith Spells", "Battle Ready", "Steel Defender"],
            5: ["Extra Attack"],
            9: ["Arcane Jolt"],
            15: ["Improved Defender"],
        },
    },

    "Barbarian": {
        # Level-keyed from classes.py. Brutal Critical improves at 13/17
        # (bigger die) but isn't a new named feature, so it's listed once
        # at its first level (9) rather than duplicated. Extra Attack and
        # Fast Movement were in classes.py's real level table but missing
        # from the original flat list — added here since they're genuine
        # named Core features.
        "Core": {
            1: ["Rage", "Unarmored Defense"],
            2: ["Reckless Attack", "Danger Sense"],
            5: ["Extra Attack", "Fast Movement"],
            7: ["Feral Instinct", "Instinctive Pounce"],
            9: ["Brutal Critical"],
            11: ["Relentless Rage"],
            15: ["Persistent Rage"],
            18: ["Indomitable Might"],
            20: ["Primal Champion"],
        },
        # Subclass levels NOT YET VERIFIED — standard 2014 PHB pattern for
        # most Barbarian paths is 3/6/10/14, but this hasn't been checked
        # feature-by-feature the way Alchemist was, so these stay flat.
        "Path of the Ancestral Guardian": [
            "Ancestral Protectors", "Spirit Shield", "Consult the Spirits",
            "Vengeful Ancestors",
        ],
        "Path of the Battlerager": [
            "Battlerager Armor", "Reckless Abandon", "Battlerager Charge",
            "Spiked Retribution",
        ],
        "Path of the Beast": [
            "Form of the Beast", "Bestial Soul", "Infectious Fury",
            "Call the Hunt",
        ],
        "Path of the Berserker": {
            3: ["Frenzy"],
            6: ["Mindless Rage"],
            10: ["Intimidating Presence"],
            14: ["Retaliation"],
        },
        "Path of the Totem Warrior": {
            3: ["Spirit Seeker", "Totem Spirit"],
            6: ["Aspect of the Beast"],
            10: ["Spirit Walker"],
            14: ["Totemic Attunement"],
        },
        "Path of the Ancestral Guardian": {
            3: ["Ancestral Protectors"],
            6: ["Spirit Shield"],
            10: ["Consult the Spirits"],
            14: ["Vengeful Ancestors"],
        },
        "Path of the Battlerager": {
            3: ["Battlerager Armor"],
            6: ["Reckless Abandon"],
            10: ["Battlerager Charge"],
            14: ["Spiked Retribution"],
        },
        "Path of the Beast": {
            3: ["Form of the Beast"],
            6: ["Bestial Soul"],
            10: ["Infectious Fury"],
            14: ["Call the Hunt"],
        },
        "Path of the Giant": {
            3: ["Giant's Power", "Giant's Havoc"],
            6: ["Elemental Cleaver"],
            10: ["Mighty Impel"],
            14: ["Demiurgic Colossus"],
        },
        "Path of the Storm Herald": {
            3: ["Storm Aura"],
            6: ["Storm Soul"],
            10: ["Shielding Storm"],
            14: ["Raging Storm"],
        },
        "Path of the Wild Magic": {
            3: ["Magic Awareness", "Wild Surge"],
            6: ["Bolstering Magic"],
            10: ["Unstable Backlash"],
            14: ["Controlled Surge"],
        },
        "Path of the Zealot": {
            3: ["Divine Fury", "Warrior of the Gods"],
            6: ["Fanatical Focus"],
            10: ["Zealous Presence"],
            14: ["Rage Beyond Death"],
        },
    },

    "Bard": {
        # Level-keyed from classes.py. Bardic Inspiration/Song of Rest die
        # upgrades (d6->d8->d10->d12) and Magical Secrets' repeat grants
        # are the same named feature scaling, not new features, so each
        # is listed once at its first level.
        "Core": {
            1: ["Bardic Inspiration"],
            2: ["Jack of All Trades", "Song of Rest"],
            3: ["Expertise"],
            5: ["Font of Inspiration"],
            6: ["Countercharm"],
            10: ["Magical Secrets"],
            20: ["Superior Inspiration"],
        },
        # Font of Inspiration's actual level (5th, per classes.py) is
        # added explicitly, since the shared level table lists it
        # alongside the Bardic Inspiration die upgrade rather than as a
        # distinct line, even though it IS a real, separate named
        # feature. Subclass levels below follow the standard 3/6/14
        # pattern (Bard colleges use 3 slots, not 4), unconfirmed feature-by-feature.
        "College of Creation": {
            3: ["Mote of Potential", "Performance of Creation"],
            6: ["Animating Performance"],
            14: ["Creative Crescendo"],
        },
        "College of Eloquence": {
            3: ["Silver Tongue", "Unsettling Words"],
            6: ["Unfailing Inspiration", "Universal Speech"],
            14: ["Infectious Inspiration"],
        },
        "College of Glamour": {
            3: ["Mantle of Inspiration", "Enthralling Performance"],
            6: ["Mantle of Majesty"],
            14: ["Unbreakable Majesty"],
        },
        "College of Lore": {
            3: ["Bonus Proficiencies (Lore Bard)", "Cutting Words"],
            6: ["Additional Magical Secrets"],
            14: ["Peerless Skill"],
        },
        "College of Spirits": {
            3: ["Guidance of the Spirits", "Spirit Session"],
            6: ["Mystic Chronicle"],
            14: ["Awakened Spirit"],
        },
        "College of Swords": {
            3: ["Bonus Proficiencies (Swords)", "Fighting Style (Swords)", "Blade Flourish"],
            6: ["Extra Attack"],
            14: ["Master's Flourish"],
        },
        "College of Valor": {
            3: ["Bonus Proficiencies (Valor Bard)", "Combat Inspiration"],
            6: ["Extra Attack"],
            14: ["Battle Magic"],
        },
        "College of Whispers": {
            3: ["Psychic Blades (Whispers)", "Words of Terror"],
            6: ["Mantle of Whispers"],
            14: ["Shadow Lore"],
        },
    },


    "Fighter": {
        # Level-keyed from classes.py. Action Surge (2/SR at 17),
        # Extra Attack (2nd/3rd attack at 11/20), and Indomitable
        # (2/LR at 13, 3/LR at 17) all scale an existing named feature
        # rather than introduce a new one, so each is listed once at its
        # first level.
        "Core": {
            1: ["Fighting Style", "Second Wind"],
            2: ["Action Surge"],
            5: ["Extra Attack"],
            9: ["Indomitable"],
        },
        # VERIFIED via web search (multiple independent sources agree):
        # Battle Master grants features at 3rd, 7th, 10th, and 15th level.
        "Banneret": {
            3: ["Rallying Cry"],
            7: ["Royal Envoy"],
            10: ["Inspiring Surge"],
            18: ["Bulwark"],
        },
        "Champion": {
            3: ["Improved Critical"],
            7: ["Remarkable Athlete"],
            10: ["Additional Fighting Style"],
            15: ["Superior Critical"],
            18: ["Survivor (Champion)"],
        },
        "Battle Master": {
            3: ["Combat Superiority", "Student of War"],
            7: ["Know Your Enemy"],
            10: ["Improved Combat Superiority"],
            15: ["Relentless"],
            18: ["Improved Combat Superiority (18th)"],
        },
        "Eldritch Knight": {
            3: ["Spellcasting (EK)", "Weapon Bond"],
            7: ["War Magic"],
            10: ["Eldritch Strike"],
            15: ["Arcane Charge"],
            18: ["Improved War Magic"],
        },
        "Arcane Archer": {
            3: ["Arcane Archer Lore", "Arcane Shot"],
            7: ["Magic Arrow", "Curving Shot"],
            10: ["Arcane Shot (10th)"],
            15: ["Ever-Ready Shot"],
            18: ["Arcane Shot (18th)"],
        },
        "Banneret (Purple Dragon Knight)": {
            3: ["Bonus Proficiency (Banneret)", "Rallying Cry"],
            7: ["Royal Envoy"],
            10: ["Inspiring Surge"],
            15: ["Bulwark"],
            18: ["Inspiring Surge (18th)"],
        },
        "Cavalier": {
            3: ["Bonus Proficiency (Cavalier)", "Born to the Saddle", "Unwavering Mark"],
            7: ["Warding Maneuver"],
            10: ["Hold the Line"],
            15: ["Ferocious Charger"],
            18: ["Vigilant Defender"],
        },
        "Echo Knight": {
            3: ["Manifest Echo", "Unleash Incarnation"],
            7: ["Echo Avatar"],
            10: ["Shadow Martyr"],
            15: ["Reclaim Potential"],
            18: ["Legion of One"],
        },
        "Psi Warrior": {
            3: ["Psionic Power"],
            7: ["Telekinetic Adept"],
            10: ["Guarded Mind"],
            15: ["Bulwark of Force"],
            18: ["Telekinetic Master"],
        },
        "Rune Knight": {
            3: ["Bonus Proficiency (Rune Knight)", "Rune Carver", "Giant's Might"],
            7: ["Runic Shield"],
            10: ["Great Stature"],
            15: ["Master of Runes"],
            18: ["Runic Juggernaut"],
        },
        "Samurai": {
            3: ["Bonus Proficiency (Samurai)", "Fighting Spirit"],
            7: ["Elegant Courtier"],
            10: ["Tireless Spirit"],
            15: ["Rapid Strike"],
            18: ["Strength before Death"],
        },
        # Remaining Fighter subclasses NOT YET added — see module docstring.
    },

    "Cleric": {
        # Standard Cleric domain progression is 1st/2nd/6th/8th/17th
        # (PHB p.58). The 2nd-level slot is each domain's own named
        # Channel Divinity option.
        # The following 4 domains are unofficial, third-party content
        # (Plane Shift: Amonkhet) with no single authoritative source —
        # reconstructed from secondary/fan sources, not verified against
        # the original text. Divine Strike at 8th is solid (matches the
        # pre-existing, correct DIVINE_STRIKE_TYPE mapping); other levels
        # are best-effort. See KNOWN_IMPLEMENTATION_GAPS.md.
        "Ambition Domain": {
            1: ["Warding Flare"],
            2: ["Invoke Duplicity"],
            6: ["Cloak of Shadows"],
            8: ["Potent Spellcasting"],
            17: ["Improved Duplicity"],
        },
        "Solidarity Domain": {
            1: ["Bonus Proficiency (Heavy Armor)", "Solidarity's Action"],
            2: ["Preserve Life"],
            6: ["Oketra's Blessing"],
            8: ["Divine Strike"],
            17: ["Supreme Healing"],
        },
        "Strength Domain": {
            1: ["Bonus Proficiency (Heavy Armor)", "Acolyte of Strength"],
            2: ["Feat of Strength"],
            6: ["Rhonas' Blessing"],
            8: ["Divine Strike"],
            17: ["Avatar of Battle"],
        },
        "Zeal Domain": {
            1: ["Bonus Proficiencies (Martial Weapons, Heavy Armor)", "Priest of Zeal"],
            2: ["Consuming Fervor"],
            6: ["Resounding Strike"],
            8: ["Divine Strike"],
            17: ["Blaze of Glory"],
        },
        "War Domain": {
            1: ["Bonus Proficiencies (War Domain)", "War Priest"],
            2: ["Guided Strike"],
            6: ["War God's Blessing"],
            8: ["Divine Strike"],
            17: ["Avatar of Battle"],
        },
        "Nature Domain": {
            1: ["Acolyte of Nature", "Bonus Proficiency (Heavy Armor)"],
            2: ["Charm Animals and Plants"],
            6: ["Dampen Elements"],
            8: ["Divine Strike"],
            17: ["Master of Nature"],
        },
        "Knowledge Domain": {
            1: ["Blessings of Knowledge"],
            2: ["Knowledge of the Ages"],
            6: ["Read Thoughts"],
            8: ["Potent Spellcasting"],
            17: ["Visions of the Past"],
        },
        "Life Domain": {
            1: ["Bonus Proficiency (Heavy Armor)", "Disciple of Life"],
            2: ["Preserve Life"],
            6: ["Blessed Healer"],
            8: ["Divine Strike"],
            17: ["Supreme Healing"],
        },
        "Death Domain": {
            1: ["Bonus Proficiency (Death)", "Reaper"],
            2: ["Touch of Death"],
            6: ["Inescapable Destruction"],
            8: ["Divine Strike"],
            17: ["Improved Reaper"],
        },
        "Light Domain": {
            1: ["Bonus Cantrip (Light Domain)", "Warding Flare"],
            2: ["Radiance of the Dawn"],
            # No distinct 6th-level feature — Light's 6th-level benefit is
            # an upgrade to Warding Flare's range, not a new named feature.
            8: ["Improved Flare", "Potent Spellcasting"],
            17: ["Corona of Light"],
        },
        "Trickery Domain": {
            1: ["Blessing of the Trickster"],
            2: ["Invoke Duplicity"],
            6: ["Cloak of Shadows"],
            8: ["Divine Strike (Trickery)"],
            17: ["Improved Duplicity"],
        },
        "Tempest Domain": {
            1: ["Bonus Proficiencies (Tempest)"],
            2: ["Wrath of the Storm"],
            6: ["Destructive Wrath"],
            8: ["Divine Strike", "Thunderbolt Strike"],
            17: ["Stormborn"],
        },
        "Arcana Domain": {
            1: ["Arcana Domain Spells", "Arcane Initiate"],
            2: ["Arcane Abjuration"],
            6: ["Spell Breaker"],
            8: ["Potent Spellcasting"],
            17: ["Arcane Mastery"],
        },
        "Forge Domain": {
            1: ["Bonus Proficiencies (Forge)", "Blessing of the Forge"],
            2: ["Artisan's Blessing"],
            6: ["Soul of the Forge"],
            8: ["Divine Strike"],
            17: ["Saint of Forge and Fire"],
        },
        "Grave Domain": {
            1: ["Circle of Mortality", "Eyes of the Grave"],
            2: ["Path to the Grave"],
            6: ["Sentinel at Death's Door"],
            8: ["Potent Spellcasting"],
            17: ["Keeper of Souls"],
        },
        "Order Domain": {
            1: ["Bonus Proficiencies (Order)", "Voice of Authority"],
            2: ["Order's Demand"],
            6: ["Embodiment of the Law"],
            8: ["Divine Strike"],
            17: ["Order's Wrath"],
        },
        "Peace Domain": {
            1: ["Implement of Peace", "Emboldening Bond"],
            2: ["Balm of Peace"],
            6: ["Protective Bond"],
            8: ["Potent Spellcasting"],
            17: ["Expansive Bond"],
        },
        "Twilight Domain": {
            1: ["Bonus Proficiencies (Twilight)", "Eyes of Night", "Vigilant Blessing"],
            2: ["Twilight Sanctuary"],
            6: ["Steps of Night"],
            8: ["Divine Strike"],
            17: ["Twilight Shroud"],
        },
    },

    "Monk": {
        # VERIFIED against classes.py's own per-level data cross-referenced
        # with real PHB monastery text: PHB monasteries (Open Hand, Shadow,
        # Four Elements) grant features at 3rd/6th/11th/17th, NOT 14th —
        # the generic "Monastic Tradition Feature" placeholder at 14th in
        # classes.py's shared Monk table applies to other, newer
        # monasteries (Way of Mercy, Astral Self, etc.), not these three.
        "Way of the Open Hand": {
            3: ["Open Hand Technique"],
            6: ["Wholeness of Body"],
            11: ["Tranquility"],
            17: ["Quivering Palm"],
        },
        "Way of the Shadow": {
            3: ["Shadow Arts"],
            6: ["Shadow Step"],
            11: ["Cloak of Shadows"],
            17: ["Opportunist"],
        },
        "Way of the Four Elements": {
            3: ["Disciple of the Elements"],
            6: ["Elemental Disciplines (Lv6)"],
            11: ["Elemental Disciplines (Lv11)"],
            17: ["Elemental Disciplines (Lv17)"],
        },
        "Way of the Kensei": {
            3: ["Path of the Kensei"],
            6: ["One with the Blade"],
            11: ["Sharpen the Blade"],
            17: ["Unerring Accuracy"],
        },
        "Way of the Astral Self": {
            3: ["Arms of the Astral Self"],
            6: ["Visage of the Astral Self"],
            11: ["Body of the Astral Self"],
            17: ["Awakened Astral Self"],
        },
        "Way of the Drunken Master": {
            3: ["Bonus Proficiencies (Drunken Master)", "Drunken Technique"],
            6: ["Tipsy Sway"],
            11: ["Drunkard's Luck"],
            17: ["Intoxicated Frenzy"],
        },
        "Way of the Long Death": {
            3: ["Touch of Death (Long Death)"],
            6: ["Hour of Reaping"],
            11: ["Mastery of Death"],
            17: ["Touch of the Long Death"],
        },
        "Way of Mercy": {
            3: ["Implements of Mercy", "Hand of Harm", "Hand of Healing"],
            6: ["Physician's Touch"],
            11: ["Flurry of Healing and Harm"],
            17: ["Hand of Ultimate Mercy"],
        },
        "Way of the Sun Soul": {
            3: ["Radiant Sun Bolt"],
            6: ["Searing Arc Strike"],
            11: ["Searing Sunburst"],
            17: ["Sun Shield"],
        },
        "Way of the Ascendant Dragon": {
            3: ["Draconic Disciple", "Breath of the Dragon"],
            6: ["Wings Unfurled"],
            11: ["Aspect of the Wyrm"],
            17: ["Ascendant Aspect"],
        },
    },

    "Paladin": {
        # VERIFIED: standard PHB Paladin oath progression is 3rd/7th/15th/
        # 20th — the 10th-level slot in classes.py's shared table is Aura
        # of Courage, a CORE Paladin feature, not oath-specific, so it's
        # correctly absent from these oaths' own level-keyed data.
        "Oath of Devotion": {
            3: ["Sacred Weapon", "Turn the Unholy"],
            7: ["Aura of Devotion"],
            15: ["Purity of Spirit"],
            20: ["Holy Nimbus"],
        },
        "Oath of Vengeance": {
            3: ["Abjure Enemy", "Vow of Enmity"],
            7: ["Relentless Avenger"],
            15: ["Soul of Vengeance"],
            20: ["Avenging Angel"],
        },
        "Oath of Conquest": {
            3: ["Conquering Presence", "Guided Strike"],
            7: ["Aura of Conquest"],
            15: ["Scornful Rebuke"],
            20: ["Invincible Conqueror"],
        },
        "Oath of Redemption": {
            3: ["Emissary of Peace", "Rebuke the Violent"],
            7: ["Aura of the Guardian"],
            15: ["Protective Spirit"],
            20: ["Emissary of Redemption"],
        },
        "Oath of the Crown": {
            3: ["Champion Challenge", "Turn the Tide"],
            7: ["Divine Allegiance"],
            15: ["Unyielding Saint"],
            20: ["Exalted Champion"],
        },
        "Oath of Glory": {
            3: ["Peerless Athlete", "Inspiring Smite"],
            7: ["Aura of Alacrity"],
            15: ["Glorious Defense"],
            20: ["Living Legend"],
        },
        "Oath of the Watchers": {
            3: ["Abjure the Extraplanar", "Watcher's Will"],
            7: ["Aura of the Sentinel"],
            15: ["Vigilant Rebuke"],
            20: ["Mortal Bulwark"],
        },
        "Oath of the Ancients": {
            3: ["Nature's Wrath", "Turn the Faithless"],
            7: ["Aura of Warding"],
            15: ["Undying Sentinel"],
            20: ["Elder Champion"],
        },
        "Oathbreaker": {
            3: ["Control Undead", "Dreadful Aspect"],
            7: ["Aura of Hate"],
            15: ["Supernatural Resistance"],
            20: ["Dread Lord"],
        },
    },

    "Ranger": {
        # PHB Ranger archetype features are at 3rd/7th/11th/15th, per
        # SUBCLASS_FEATURES' own level-labeled names for Hunter
        # ("Hunter's Prey (Lv3)", etc.). The 14th and 17th slots in
        # classes.py's shared table don't apply to these two.
        "Beast Master": {
            3: ["Ranger's Companion"],
            7: ["Exceptional Training"],
            11: ["Bestial Fury"],
            15: ["Share Spells"],
        },
        "Hunter": {
            3: ["Hunter's Prey"],
            7: ["Defensive Tactics"],
            11: ["Multiattack"],
            15: ["Superior Hunter's Defense"],
        },
        "Gloom Stalker": {
            3: ["Dread Ambusher", "Umbral Sight"],
            7: ["Iron Mind"],
            11: ["Stalker's Flurry"],
            15: ["Shadowy Dodge"],
        },
        "Horizon Walker": {
            3: ["Detect Portal", "Planar Warrior"],
            7: ["Ethereal Step"],
            11: ["Distant Strike"],
            15: ["Spectral Defense"],
        },
        "Monster Slayer": {
            3: ["Hunter's Sense", "Slayer's Prey"],
            7: ["Supernatural Defense"],
            11: ["Magic-User's Nemesis"],
            15: ["Slayer's Counter"],
        },
        "Fey Wanderer": {
            3: ["Dreadful Strikes", "Otherworldly Glamour"],
            7: ["Beguiling Twist"],
            11: ["Fey Reinforcements"],
            15: ["Misty Wanderer"],
        },
        "Swarmkeeper": {
            3: ["Gathered Swarm", "Swarmkeeper Magic"],
            7: ["Writhing Tide"],
            11: ["Mighty Swarm"],
            15: ["Swarming Dispersal"],
        },
        "Drakewarden": {
            3: ["Draconic Gift", "Drake Companion"],
            7: ["Bond of Fang and Scale"],
            11: ["Drake's Breath"],
            15: ["Perfected Bond"],
        },
    },

    "Rogue": {
        # VERIFIED: PHB Assassin features are at 3rd/9th/13th/17th — the
        # 15th-level slot in classes.py's shared table doesn't apply here.
        "Thief": {
            3: ["Fast Hands", "Second-Story Work"],
            9: ["Supreme Sneak"],
            13: ["Use Magic Device"],
            17: ["Thief's Reflexes"],
        },
        "Arcane Trickster": {
            3: ["Spellcasting (AT)", "Mage Hand Legerdemain"],
            9: ["Magical Ambush"],
            13: ["Versatile Trickster"],
            17: ["Spell Thief"],
        },
        "Assassin": {
            3: ["Bonus Proficiencies (Assassin)", "Assassinate"],
            9: ["Infiltration Expertise"],
            13: ["Impostor"],
            17: ["Death Strike"],
        },
        "Swashbuckler": {
            3: ["Fancy Footwork", "Rakish Audacity"],
            9: ["Panache"],
            13: ["Elegant Maneuver"],
            17: ["Master Duelist"],
        },
        "Mastermind": {
            3: ["Master of Intrigue", "Master of Tactics"],
            9: ["Insightful Manipulator"],
            13: ["Misdirection"],
            17: ["Soul of Deceit"],
        },
        "Inquisitive": {
            3: ["Ear for Deceit", "Eye for Detail", "Insightful Fighting"],
            9: ["Steady Eye"],
            13: ["Unerring Eye"],
            17: ["Eye for Weakness"],
        },
        "Scout": {
            3: ["Skirmisher", "Survivalist"],
            9: ["Superior Mobility"],
            13: ["Ambush Master"],
            17: ["Sudden Strike"],
        },
        "Phantom": {
            3: ["Whispers of the Dead", "Wails from the Grave"],
            9: ["Tokens of the Departed"],
            13: ["Ghost Walk"],
            17: ["Death's Friend"],
        },
        "Soulknife": {
            3: ["Psionic Power", "Psychic Blades"],
            9: ["Soul Blades"],
            13: ["Psychic Veil"],
            17: ["Rend Mind"],
        },
    },

    "Sorcerer": {
        # VERIFIED: PHB Sorcerous Origin features are at 1st/6th/14th/18th,
        # with two features granted simultaneously at 1st level for both
        # of these origins. The 3rd and 10th slots in classes.py's shared
        # table are Sorcerer CORE features (Metamagic, etc.), not
        # origin-specific, so correctly absent here.
        "Draconic Bloodline": {
            1: ["Dragon Ancestor", "Draconic Resilience"],
            6: ["Elemental Affinity"],
            14: ["Dragon Wings"],
            18: ["Draconic Presence"],
        },
        "Wild Magic": {
            1: ["Wild Magic Surge", "Tides of Chaos"],
            6: ["Bend Luck"],
            14: ["Controlled Chaos"],
            18: ["Spell Bombardment"],
        },
        "Aberrant Mind": {
            1: ["Psionic Spells", "Telepathic Speech"],
            6: ["Psionic Sorcery", "Psychic Defenses"],
            14: ["Revelation in Flesh"],
            18: ["Warping Implosion"],
        },
        "Clockwork Soul": {
            1: ["Clockwork Magic", "Restore Balance"],
            6: ["Bastion of Law"],
            14: ["Trance of Order"],
            18: ["Clockwork Cavalcade"],
        },
        "Divine Soul": {
            1: ["Divine Magic", "Favored by the Gods"],
            6: ["Empowered Healing"],
            14: ["Otherworldly Wings"],
            18: ["Unearthly Recovery"],
        },
        "Pyromancer": {
            1: ["Heart of Fire"],
            6: ["Fire in the Veins"],
            14: ["Pyromancer's Fury"],
            18: ["Fiery Soul"],
        },
        "Shadow Magic": {
            1: ["Eyes of the Dark", "Strength of the Grave"],
            6: ["Hound of Ill Omen"],
            14: ["Shadow Walk"],
            18: ["Umbral Form"],
        },
        "Storm Sorcery": {
            1: ["Wind Speaker", "Tempestuous Magic"],
            6: ["Heart of the Storm", "Storm Guide"],
            14: ["Storm's Fury"],
            18: ["Wind Soul"],
        },
        "Lunar Sorcery": {
            1: ["Lunar Embodiment", "Moon Fire"],
            6: ["Lunar Boons + Waxing and Waning"],
            14: ["Lunar Empowerment"],
            18: ["Lunar Phenomenon"],
        },
    },

    "Warlock": {
        # VERIFIED: PHB Otherworldly Patron features are at 1st/6th/10th/
        # 14th. The 2nd/3rd/9th slots in classes.py's shared table are
        # Warlock CORE features (Eldritch Invocations, Pact Boon, etc.),
        # not patron-specific, so correctly absent here.
        "The Archfey": {
            1: ["Fey Presence"],
            6: ["Misty Escape"],
            10: ["Beguiling Defenses"],
            14: ["Dark Delirium"],
        },
        "The Fiend": {
            1: ["Dark One's Blessing"],
            6: ["Dark One's Own Luck"],
            10: ["Fiendish Resilience"],
            14: ["Hurl Through Hell"],
        },
        "The Great Old One": {
            1: ["Awakened Mind"],
            6: ["Entropic Ward"],
            10: ["Thought Shield"],
            14: ["Create Thrall"],
        },
        "The Hexblade": {
            1: ["Hexblade's Curse", "Hex Warrior"],
            6: ["Accursed Specter"],
            10: ["Armor of Hexes"],
            14: ["Master of Hexes"],
        },
        "The Celestial": {
            1: ["Bonus Cantrips", "Healing Light"],
            6: ["Radiant Soul"],
            10: ["Celestial Resilience"],
            14: ["Searing Vengeance"],
        },
        "The Fathomless": {
            1: ["Gift of the Sea", "Tentacle of the Deep"],
            6: ["Oceanic Soul", "Guardian Coil"],
            10: ["Grasping Tentacles"],
            14: ["Fathomless Plunge"],
        },
        "The Genie": {
            1: ["Genie's Vessel", "Genie's Wrath"],
            6: ["Elemental Gift"],
            10: ["Sanctuary Vessel"],
            14: ["Limited Wish"],
        },
        "The Undead": {
            1: ["Form of Dread"],
            6: ["Grave Touched"],
            10: ["Necrotic Husk"],
            14: ["Spirit Projection"],
        },
        "The Undying": {
            1: ["Among the Dead"],
            6: ["Defy Death"],
            10: ["Undying Nature"],
            14: ["Indestructible Life"],
        },
    },

    "Wizard": {
        # VERIFIED: standard PHB Arcane Tradition progression is 2nd/6th/
        # 10th/14th, with the school's Savant feature and its first unique
        # ability both granted simultaneously at 2nd level for every school.
        "Abjuration": {
            2: ["Abjuration Savant", "Arcane Ward"],
            6: ["Projected Ward"],
            10: ["Improved Abjuration"],
            14: ["Spell Resistance"],
        },
        "Conjuration": {
            2: ["Conjuration Savant", "Minor Conjuration"],
            6: ["Benign Transposition"],
            10: ["Focused Conjuration"],
            14: ["Durable Summons"],
        },
        "Divination": {
            2: ["Divination Savant", "Portent"],
            6: ["Expert Divination"],
            10: ["The Third Eye"],
            14: ["Greater Portent"],
        },
        "Enchantment": {
            2: ["Enchantment Savant", "Hypnotic Gaze"],
            6: ["Instinctive Charm"],
            10: ["Split Enchantment"],
            14: ["Alter Memories"],
        },
        "Evocation": {
            2: ["Evocation Savant", "Sculpt Spells"],
            6: ["Potent Cantrip"],
            10: ["Empowered Evocation"],
            14: ["Overchannel"],
        },
        "Illusion": {
            2: ["Illusion Savant", "Improved Minor Illusion"],
            6: ["Malleable Illusions"],
            10: ["Illusory Self"],
            14: ["Illusory Reality"],
        },
        "Necromancy": {
            2: ["Necromancy Savant", "Grim Harvest"],
            6: ["Undead Thralls"],
            10: ["Inured to Undeath"],
            14: ["Command Undead"],
        },
        "Transmutation": {
            2: ["Transmutation Savant", "Minor Alchemy"],
            6: ["Transmuter's Stone"],
            10: ["Shapechanger"],
            14: ["Master Transmuter"],
        },
        "Bladesinging": {
            2: ["Training in War and Song", "Bladesong"],
            6: ["Extra Attack (Bladesinging)"],
            10: ["Song of Defense"],
            14: ["Song of Victory"],
        },
        "Chronurgy Magic": {
            2: ["Chronal Shift", "Temporal Awareness"],
            6: ["Momentary Stasis"],
            10: ["Arcane Abeyance"],
            14: ["Convergent Future"],
        },
        "Graviturgy Magic": {
            2: ["Adjust Density"],
            6: ["Gravity Well"],
            10: ["Violent Attraction"],
            14: ["Event Horizon"],
        },
        "Order of Scribes": {
            2: ["Wizardly Quill", "Awakened Spellbook"],
            6: ["Manifest Mind"],
            10: ["Master Scrivener"],
            14: ["One with the Word"],
        },
        "War Magic": {
            2: ["Arcane Deflection", "Tactical Wit"],
            6: ["Power Surge"],
            10: ["Durable Magic"],
            14: ["Deflecting Shroud"],
        },
    },

    "Druid": {
        # VERIFIED: PHB Circle of the Land grants Bonus Cantrip, Natural
        # Recovery, and Circle Spells together at 2nd level, then one
        # feature each at 6th/10th/14th. The 18th-level slot in classes.py's
        # shared table is Circle of the Moon-specific (Primal Strike), not
        # Circle of the Land's, so correctly absent here.
        "Circle of the Moon": {
            2: ["Combat Wild Shape", "Circle Forms"],
            6: ["Primal Strike"],
            10: ["Elemental Wild Shape"],
            14: ["Thousand Forms"],
        },
        "Circle of the Land": {
            2: ["Bonus Cantrip (Circle of the Land)", "Natural Recovery", "Circle Spells"],
            6: ["Land's Stride"],
            10: ["Nature's Ward"],
            14: ["Nature's Sanctuary"],
        },
        "Circle of the Shepherd": {
            2: ["Speech of the Woods", "Spirit Totem"],
            6: ["Mighty Summoner"],
            10: ["Guardian Spirit"],
            14: ["Faithful Summons"],
        },
        "Circle of Wildfire": {
            2: ["Circle Spells", "Summon Wildfire Spirit"],
            6: ["Enhanced Bond"],
            10: ["Cauterizing Flames"],
            14: ["Blazing Revival"],
        },
        "Circle of Spores": {
            2: ["Circle Spells", "Halo of Spores", "Symbiotic Entity"],
            6: ["Fungal Infestation"],
            10: ["Spreading Spores"],
            14: ["Fungal Body"],
        },
        "Circle of Dreams": {
            2: ["Balm of the Summer Court"],
            6: ["Hearth of Moonlight and Shadow"],
            10: ["Hidden Paths"],
            14: ["Walker in Dreams"],
        },
        "Circle of Stars": {
            2: ["Star Map", "Starry Form"],
            6: ["Cosmic Omen"],
            10: ["Twinkling Constellations"],
            14: ["Full of Stars"],
        },
    },

    "Blood Hunter": {
        "Core": {
            1: ["Hunter's Bane", "Blood Maledict"],
            2: ["Fighting Style", "Crimson Rite"],
            5: ["Extra Attack"],
            6: ["Brand of Castigation"],
            9: ["Grim Psychometry"],
            10: ["Dark Augmentation"],
            13: ["Brand of Tethering"],
            14: ["Hardened Soul"],
            20: ["Sanguine Mastery"],
        },
        "Order of the Ghostslayer": {
            3: ["Rite of the Dawn", "Curse Specialist"],
            7: ["Aether Walk"],
            11: ["Brand of Sundering"],
            15: ["Blood Curse of the Exorcist"],
            18: ["Rite Revival"],
        },
        "Order of the Lycan": {
            3: ["Heightened Senses", "Hybrid Transformation"],
            7: ["Stalker's Prowess"],
            11: ["Advanced Transformation"],
            15: ["Brand of the Voracious"],
            18: ["Hybrid Transformation Mastery"],
        },
        "Order of the Mutant": {
            3: ["Mutagencraft"],
            7: ["Strange Metabolism"],
            11: ["Brand of Axiom"],
            15: ["Blood Curse of Corrosion"],
            18: ["Exalted Mutation"],
        },
        "Order of the Profane Soul": {
            3: ["Profane Soul Spellcasting", "Otherworldly Patron", "Pact Magic", "Rite Focus"],
            7: ["Mystic Frenzy", "Revealed Arcana"],
            11: ["Brand of the Sapping Scar"],
            15: ["Unsealed Arcana"],
            18: ["Blood Curse of the Souleater"],
        },
    },

}


def get_class_features(char: dict) -> dict[str, list[str]]:
    """For a given character, return {class_name: [feature names...]}
    combining that class's Core features (only those at or below the
    character's current level in that class, if Core is level-keyed —
    see module docstring) with whichever subclass list(s) apply, for
    every class the character currently has. Only includes classes
    present in CLASS_FEATURE_INDEX (partial coverage while this file is
    still being built out)."""
    from ..core.character import class_levels, subclasses
    out = {}
    cl = class_levels(char)
    subs = subclasses(char)
    for cname, lvl in cl.items():
        entry = CLASS_FEATURE_INDEX.get(cname)
        if not entry:
            continue
        core = entry.get("Core", [])
        if isinstance(core, dict):
            feats = [f for feat_lvl, names in core.items() if feat_lvl <= lvl for f in names]
        else:
            feats = list(core)
        sub_name = subs.get(cname, "")
        sub_entry = entry.get(sub_name) if sub_name else None
        if sub_entry:
            if isinstance(sub_entry, dict):
                feats.extend(f for feat_lvl, names in sub_entry.items() if feat_lvl <= lvl for f in names)
            else:
                feats.extend(sub_entry)
        out[cname] = feats
    return out

# ═════════════════════════════════════════════════════════════════════════════
# TCoE optional/alternate class features (a separate, replaces-not-adds system)
# ═════════════════════════════════════════════════════════════════════════════

OPTIONAL_CLASS_FEATURES: dict[str, dict[int, list[dict]]] = {

    # ── RANGER ────────────────────────────────────────────────────────────────
    "Ranger": {
        1: [
            {
                "name": "Favored Foe",
                "replaces": "Favored Enemy",
                "source": "TCoE",
                "desc": (
                    "When you hit a creature with an attack roll, you can call on your mystical "
                    "bond to mark it as your favored enemy until combat ends. Once per turn when "
                    "you hit it, deal extra damage: 1d4 (Lv1–5), 1d6 (Lv6–13), 1d8 (Lv14+). "
                    "Uses = Proficiency Bonus. Recharges on Long Rest."
                ),
                "resource": {"key": "favored_foe", "name": "Favored Foe", "reset": "LR", "formula": "pb"},
            },
            {
                "name": "Deft Explorer",
                "replaces": "Natural Explorer",
                "source": "TCoE",
                "desc": (
                    "Canny (Lv1): Expertise in one skill from the Ranger list. "
                    "Roving (Lv6): Speed +5 ft; gain climb speed and swim speed equal to walking speed. "
                    "Tireless (Lv10): As an action, gain 1d8 + WIS modifier temporary HP. "
                    "Uses = Proficiency Bonus / Long Rest."
                ),
            },
        ],
        3: [
            {
                "name": "Primal Awareness",
                "replaces": "Primeval Awareness",
                "source": "TCoE",
                "desc": (
                    "Cast these spells once each without expending a slot: Speak with Animals (Lv3), "
                    "Beast Sense (Lv5), Speak with Plants (Lv9), Locate Creature (Lv13), "
                    "Commune with Nature (Lv17). Regain all uses on Long Rest."
                ),
            },
        ],
        10: [
            {
                "name": "Nature's Veil",
                "replaces": "Hide in Plain Sight",
                "source": "TCoE",
                "desc": (
                    "As a bonus action, draw on nature magic to become invisible until the start of "
                    "your next turn. Uses = Proficiency Bonus / Long Rest."
                ),
                "resource": {"key": "natures_veil", "name": "Nature's Veil", "reset": "LR", "formula": "pb"},
            },
        ],
        4: [
            {
                "name": "Martial Versatility",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Whenever you reach a level in this class that grants the Ability Score "
                    "Improvement feature, you can replace a fighting style you know with another "
                    "fighting style available to Rangers."
                ),
            },
        ],
    },

    # ── PALADIN ───────────────────────────────────────────────────────────────
    "Paladin": {
        3: [
            {
                "name": "Harness Divine Power",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "As a bonus action, expend one use of Channel Divinity to regain one expended "
                    "spell slot whose level is no greater than half your Proficiency Bonus (round up). "
                    "1×/Long Rest (2× at Lv7, 3× at Lv15)."
                ),
            },
        ],
        4: [
            {
                "name": "Martial Versatility",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Whenever you reach a level in this class that grants the Ability Score "
                    "Improvement feature, you can replace a fighting style you know with another "
                    "fighting style available to Paladins."
                ),
            },
        ],
    },

    # ── CLERIC ────────────────────────────────────────────────────────────────
    "Cleric": {
        2: [
            {
                "name": "Harness Divine Power",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Channel Divinity: as a bonus action, expend one Channel Divinity use to regain "
                    "one expended spell slot whose level ≤ half PB (rounded up). "
                    "1×/Long Rest (2× at Lv6, 3× at Lv18)."
                ),
            },
        ],
    },

    # ── FIGHTER ───────────────────────────────────────────────────────────────
    "Fighter": {
        4: [
            {
                "name": "Martial Versatility",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Whenever you gain an ASI from this class, you can replace one fighting style "
                    "you know with another available to Fighters."
                ),
            },
        ],
    },

    # ── ROGUE ─────────────────────────────────────────────────────────────────
    "Rogue": {
        3: [
            {
                "name": "Steady Aim",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "As a bonus action, give yourself advantage on your next attack roll this turn. "
                    "You must not have moved this turn; after using this feature your speed is 0 "
                    "until the end of the turn."
                ),
            },
        ],
    },

    # ── BARD ──────────────────────────────────────────────────────────────────
    "Bard": {
        4: [
            {
                "name": "Bardic Versatility",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Whenever you gain an ASI from this class, you can replace one bard cantrip "
                    "you know with another, or replace one Expertise skill with a proficient skill "
                    "that isn't currently benefiting from Expertise."
                ),
            },
        ],
    },

    # ── SORCERER ──────────────────────────────────────────────────────────────
    "Sorcerer": {
        5: [
            {
                "name": "Magical Guidance",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "When you make an ability check that fails, you can spend 1 sorcery point to "
                    "reroll the check and take the new result."
                ),
            },
        ],
        4: [
            {
                "name": "Sorcerous Versatility",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Whenever you gain an ASI from this class, you can replace one metamagic option "
                    "you know with another, or replace one sorcerer cantrip with another."
                ),
            },
        ],
    },

    # ── WARLOCK ───────────────────────────────────────────────────────────────
    "Warlock": {
        1: [
            {
                "name": "Eldritch Mind",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "You have advantage on Constitution saving throws that you make to maintain "
                    "concentration on a spell."
                ),
            },
        ],
        4: [
            {
                "name": "Eldritch Versatility",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Whenever you gain an ASI from this class, you can do one: replace a cantrip, "
                    "replace an Eldritch Invocation you qualify for, or replace your Pact Boon "
                    "with another."
                ),
            },
        ],
    },

    # ── MONK ──────────────────────────────────────────────────────────────────
    "Monk": {
        2: [
            {
                "name": "Dedicated Weapon",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "When you finish a short or long rest, choose one weapon. Until your next rest "
                    "that weapon counts as a monk weapon for you even if it normally wouldn't qualify."
                ),
            },
        ],
        3: [
            {
                "name": "Ki-Fueled Attack",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "If you spend 1 or more ki points as part of your action on your turn, you can "
                    "make one attack with a monk weapon as a bonus action."
                ),
            },
        ],
        5: [
            {
                "name": "Focused Aim",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "When you miss with an attack roll, spend 1–3 ki points to increase the roll by "
                    "2 per ki point spent — potentially turning the miss into a hit."
                ),
            },
        ],
    },

    # ── DRUID ─────────────────────────────────────────────────────────────────
    "Druid": {
        2: [
            {
                "name": "Wild Companion",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "You can expend a use of Wild Shape to cast Find Familiar without material "
                    "components. The familiar always has the Fey type and disappears after a "
                    "number of hours equal to half your druid level."
                ),
            },
        ],
        4: [
            {
                "name": "Druidic Warrior",
                "replaces": None,
                "source": "TCoE",
                "desc": (
                    "Additional Fighting Style option: learn two druid cantrips. They count as "
                    "druid spells for you and don't count against your cantrip limit."
                ),
            },
        ],
    },
}

