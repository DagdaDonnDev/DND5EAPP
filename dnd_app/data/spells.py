"""
Spells data module.

D&D 5e spell database: all SRD spells plus major PHB/XGE/TCE
additions. Each spell entry records name, level (0=cantrip), school,
eligible classes, ritual/concentration flags, source, and description.
Also defines BONUS_SPELLS/RACIAL_BONUS_SPELLS and get_bonus_spells(),
the racial/subclass/feat/item spell grants merged into a character's
known spell list at build time.

Author: Ethan O'Brien
Date: 2026-08-20
"""

# school abbreviations
ABJ="Abjuration"; CON="Conjuration"; DIV="Divination"; ENC="Enchantment"
EVO="Evocation"; ILL="Illusion"; NEC="Necromancy"; TRN="Transmutation"

def spell(name, level, school, classes, ritual=False, concentration=False,
          source="PHB", desc="", cast_time="1 action", range_="60 ft",
          duration="Instantaneous", components="V, S"):
    return dict(name=name, level=level, school=school, classes=classes,
                ritual=ritual, concentration=concentration,
                source=source, desc=desc, cast_time=cast_time,
                range=range_, duration=duration, components=components)

# Class abbreviations for readability
ART="Artificer"; BAR="Bard"; CLE="Cleric"; DRU="Druid"; PAL="Paladin"
RAN="Ranger"; SOR="Sorcerer"; WAR="Warlock"; WIZ="Wizard"

ALL_SPELLS = [
# ── Cantrips (level 0) ───────────────────────────────────────────────────────
spell("Acid Splash",       0, CON, [ART,SOR,WIZ],         desc="Hurl a bubble of acid. One or two creatures within 5 ft of each other: 1d6 acid (DEX save)."),
spell("Blade Ward",        0, ABJ, [BAR,SOR,WAR,WIZ], desc="Until end of next turn: resistance to bludgeoning, piercing, slashing from weapons.", duration="1 round", range_="Self"),
spell("Booming Blade",     0, EVO, [ART,SOR,WAR,WIZ], desc="Melee attack; if target moves, takes 1d8 thunder bonus. Scales with level.", source="SCAG/TCE", components="V, M (a weapon worth at least 1 sp)", range_="Self (5-foot radius)"),
spell("Chill Touch",       0, NEC, [SOR,WAR,WIZ],     desc="Ranged spell attack. On hit: 1d8 necrotic; can't regain HP until next turn. Scales.", range_="120 ft"),
spell("Control Flames",    0, TRN, [DRU,SOR,WIZ],     desc="Instantaneously expand/move/extinguish/change color of nonmagical flame within a 5-foot cube.", source="EEPC"),
spell("Create Bonfire",    0, CON, [ART,DRU,SOR,WAR,WIZ], desc="Bonfire in 5-ft cube. 1d8 fire on CON/creatures/objects.", concentration=True, source="EEPC"),
spell("Dancing Lights",    0, EVO, [ART,BAR,SOR,WIZ], desc="Up to 4 torch-size lights, move 60 ft/turn.", concentration=True, range_="120 ft"),
spell("Druidcraft",        0, TRN, [DRU],              desc="Minor nature magic: predict weather, cause flower to bloom, light campfire, create sensory effect.", range_="30 ft"),
spell("Eldritch Blast",    0, EVO, [WAR],              desc="Ranged spell attack: 1d10 force. Extra beams at 5 (×2), 11 (×3), 17 (×4).", range_="120 ft"),
spell("Fire Bolt",         0, EVO, [ART,SOR,WIZ],     desc="Ranged attack: 1d10 fire. Ignites objects. Scales at 5/11/17.", range_="120 ft"),
spell("Friends",           0, ENC, [BAR,SOR,WAR,WIZ], desc="Advantage on CHA checks vs one non-hostile creature. It knows after.", concentration=True, range_="Self"),
spell("Frostbite",         0, EVO, [ART,DRU,SOR,WAR,WIZ], desc="CON save or 1d6 cold + disadvantage on next weapon attack.", source="EEPC"),
spell("Green-Flame Blade", 0, EVO, [ART,SOR,WAR,WIZ], desc="Melee attack; fire leaps to adjacent creature for CHA mod fire.", source="SCAG/TCE", components="V, M (a weapon worth at least 1 sp)", range_="Self (5-foot radius)"),
spell("Guidance",          0, DIV, [ART,CLE,DRU],     desc="Willing creature adds 1d4 to one ability check.", concentration=True, range_="Touch"),
spell("Gust",              0, TRN, [DRU,SOR,WIZ],     desc="Shove creature 5 ft or move Small object.", source="EEPC", range_="30 ft"),
spell("Infestation",       0, CON, [DRU,SOR,WAR,WIZ], desc="CON save or 1d6 poison + forced movement 5 ft.", source="XGE", range_="30 ft"),
spell("Light",             0, EVO, [ART,BAR,CLE,SOR,WIZ], desc="Object sheds bright 20 ft / dim 20 ft light for 1 hour.", duration="1 hour", range_="Touch"),
spell("Lightning Lure",    0, EVO, [ART,SOR,WAR,WIZ], desc="Pull creature within 15 ft toward you; 1d8 lightning if moved.", source="SCAG/TCE", range_="Self (15-foot radius)"),
spell("Mage Hand",         0, CON, [ART,BAR,SOR,WAR,WIZ], desc="Spectral hand can manipulate objects, open doors, retrieve items (up to 10 lb), 30 ft. Can't attack, activate magic items, or carry more than 10 lbs.", range_="30 ft"),
spell("Magic Stone",       0, TRN, [ART,DRU,WAR],     desc="Imbue up to 3 pebbles; can be thrown (spell attack) or slung for 1d6+spell mod bludgeoning.", source="EEPC", range_="Touch"),
spell("Mending",           0, TRN, [ART,BAR,CLE,DRU,SOR,WIZ], desc="Repair a single break or tear in object (up to 1 foot).", range_="Touch"),
spell("Message",           0, TRN, [ART,BAR,SOR,WIZ], desc="Whisper message to creature within 120 ft; it can reply.", range_="120 ft"),
spell("Mind Sliver",       0, ENC, [BAR,SOR,WAR,WIZ],     desc="INT save or 1d6 psychic + −1d4 to next saving throw.", source="TCE"),
spell("Minor Illusion",    0, ILL, [BAR,SOR,WAR,WIZ], desc="Create a static sound or the image of an object within a 5-ft cube, within 30 ft. Can't create creatures or sound+image together (unless upgraded via a feature). Investigation vs spell save to disbelieve.", range_="30 ft"),
spell("Mold Earth",        0, TRN, [DRU,SOR,WIZ],     desc="Excavate, move, or shape 5-ft cube of earth.", source="EEPC", range_="30 ft"),
spell("Poison Spray",      0, CON, [ART,DRU,SOR,WAR,WIZ], desc="CON save or 1d12 poison. Scales.", range_="10 ft"),
spell("Prestidigitation",  0, TRN, [ART,BAR,SOR,WAR,WIZ], desc="Minor magical tricks: sensory effects, clean/soil, chill/warm/flavor, colour mark, small trinket/illusion.", range_="10 ft"),
spell("Primal Savagery",   0, TRN, [DRU],              desc="Melee spell attack: 1d10 acid. Scales.", source="XGE", range_="Self"),
spell("Produce Flame",     0, CON, [DRU],              desc="Flame in hand (light 10 ft bright, 10 ft dim). Can hurl as ranged attack: 1d8 fire. Scales.", range_="Self"),
spell("Ray of Frost",      0, EVO, [ART,SOR,WIZ],     desc="Ranged attack: 1d8 cold + −10 ft speed. Scales."),
spell("Resistance",        0, ABJ, [ART,CLE,DRU],     desc="Willing creature adds 1d4 to one saving throw.", concentration=True, range_="Touch"),
spell("Sacred Flame",      0, EVO, [CLE],              desc="DEX save or 1d8 radiant. Ignores cover. Scales."),
spell("Shape Water",       0, TRN, [DRU,SOR,WIZ],     desc="Move/reshape 5-ft cube of water, change flow, freeze briefly.", source="EEPC", range_="30 ft"),
spell("Shillelagh",        0, TRN, [DRU],              desc="Wooden club/quarterstaff becomes magical; use WIS for attacks; 1d8 damage.", range_="Touch"),
spell("Shocking Grasp",    0, EVO, [ART,SOR,WIZ],     desc="Lightning on touch: 1d8 lightning + can't take reactions. Advantage vs metal-armored. Scales.", range_="Touch"),
spell("Spare the Dying",   0, NEC, [ART,CLE],          desc="Touch a dying creature to stabilize it.", range_="Touch"),
spell("Sword Burst",       0, CON, [ART,SOR,WAR,WIZ], desc="5-ft burst: DEX save or 1d6 force. Scales.", source="SCAG/TCE", range_="Self (5-foot radius)"),
spell("Thaumaturgy",       0, TRN, [CLE],              desc="Manifest minor wonders: voice booms, flames flicker, ground trembles, eyes glow, etc.", range_="30 ft"),
spell("Thunderclap",       0, EVO, [ART,BAR,DRU,SOR,WAR,WIZ], desc="CON save or 1d6 thunder. Audible 100 ft away.", source="EEPC", range_="5 ft"),
spell("Toll the Dead",     0, NEC, [CLE,WAR,WIZ],     desc="WIS save or 1d8 necrotic (1d12 if missing HP). Scales.", source="XGE"),
spell("True Strike",       0, DIV, [BAR,SOR,WAR,WIZ], desc="Advantage on first attack roll vs target next turn.", concentration=True, range_="30 ft"),
spell("Vicious Mockery",   0, ENC, [BAR],              desc="Target within 60 ft that can hear you: WIS save or 1d4 psychic + disadvantage on next attack. Scales."),
spell("Word of Radiance",  0, EVO, [CLE],              desc="CON save or 1d6 radiant (each creature within 5 ft).", source="XGE", range_="5 ft"),

    spell("Thorn Whip",         0, TRN, [ART,DRU],         desc="Melee spell attack: 1d6 piercing + pull target 10 ft toward you if Large or smaller. Scales: 2d6 at Lv5, 3d6 at Lv11, 4d6 at Lv17.", source="PHB", range_="30 ft"),
    spell("Encode Thoughts",    0, ENC, [WIZ],               desc="Extract a memory lasting up to 8 hours and encode it as a Tiny intangible thought strand. Another creature holding it experiences the memory.", source="GGR", range_="Self", components="S"),
    spell("Sapping Sting",      0, NEC, [WIZ],               desc="One creature within 30 ft: CON save or take 1d4 necrotic damage and fall prone. Scales at Lv5/11/17.", source="EGW"),

# ── 1st Level ────────────────────────────────────────────────────────────────
spell("Absorb Elements",   1, ABJ, [ART,DRU,RAN,SOR,WIZ], desc="Reaction: resist triggering element; next attack deals extra 1d6 of that type.", cast_time="Reaction", source="EEPC", range_="Self"),
spell("Alarm",             1, ABJ, [ART,RAN,WIZ],     ritual=True, desc="Ward an area up to a 20-ft cube; alert when tiny+ creature enters.", range_="30 ft"),
spell("Animal Friendship", 1, ENC, [BAR,DRU,RAN],     desc="Charm a beast (WIS save). Must have INT < 4.", range_="30 ft"),
spell("Armor of Agathys", 1, ABJ, [WAR],              desc="Gain 5 temp HP; attacker takes 5 cold damage.", duration="1 hour", range_="Self"),
spell("Arms of Hadar",     1, CON, [WAR],              desc="10-ft burst: STR save or 2d6 necrotic + no reactions.", range_="Self (10-foot radius)"),
spell("Bane",              1, ENC, [BAR,CLE],          concentration=True, desc="Up to 3 creatures: −1d4 to attacks and saves (CHA save).", range_="30 ft"),
spell("Beast Bond",        1, DIV, [DRU,RAN],          concentration=True, desc="Telepathic link + shared senses with a beast you own.", source="EEPC", range_="Touch"),
spell("Bless",             1, ENC, [CLE,PAL],          concentration=True, desc="Up to 3 creatures: +1d4 to attacks and saves.", range_="30 ft"),
spell("Burning Hands",     1, EVO, [SOR,WIZ],          desc="15-ft cone: DEX save or 3d6 fire. Scales.", range_="Self (15-foot cone)"),
spell("Cause Fear",        1, NEC, [WAR,WIZ],          concentration=True, desc="WIS save or Frightened. Can't target undead.", source="XGE"),
spell("Charm Person",      1, ENC, [BAR,DRU,SOR,WAR,WIZ], desc="WIS save or charmed 1 hour. Creature knows it was charmed after.", range_="30 ft"),
spell("Chromatic Orb",     1, EVO, [SOR,WIZ],          desc="Ranged attack: 3d8 (choose acid/cold/fire/lightning/poison/thunder). Scales.", range_="90 ft"),
spell("Color Spray",       1, ILL, [SOR,WIZ],          desc="Cone: blind creatures whose total HP ≤ 6d10 threshold.", range_="Self (15-foot cone)"),
spell("Command",           1, ENC, [CLE,PAL],          desc="WIS save or obey 1-word command: Approach, Drop, Flee, Grovel, Halt."),
spell("Compelled Duel",    1, ENC, [PAL],              concentration=True, desc="WIS save or target has disadvantage vs others and can't move >30 ft from you.", cast_time="Bonus action", range_="30 ft"),
spell("Comprehend Languages", 1, DIV, [BAR,SOR,WAR,WIZ], ritual=True, desc="Understand any spoken/written language for 1 hour.", duration="1 hour", range_="Self"),
spell("Create or Destroy Water", 1, TRN, [CLE,DRU],   desc="Create 10 gal water or destroy equal volume of water.", range_="30 ft"),
spell("Cure Wounds",       1, EVO, [ART,BAR,CLE,DRU,PAL,RAN], desc="Touch: heal 1d8 + spell mod. Scales.", range_="Touch"),
spell("Detect Evil and Good", 1, DIV, [CLE,PAL],       concentration=True, desc="Sense aberrations, celestials, elementals, fey, fiends, undead within 30 ft.", duration="10 min", range_="Self"),
spell("Detect Magic",      1, DIV, [ART,BAR,CLE,DRU,PAL,RAN,SOR,WAR,WIZ], ritual=True, concentration=True, desc="Sense magic within 30 ft; see auras.", duration="10 min", range_="Self"),
spell("Detect Poison and Disease", 1, DIV, [CLE,DRU,PAL,RAN], ritual=True, concentration=True, desc="Sense poison, poisonous creatures, and disease within 30 ft.", duration="10 min", range_="Self"),
spell("Disguise Self",     1, ILL, [ART,BAR,SOR,WIZ], desc="Alter appearance (clothing + features; not shape) for 1 hour.", duration="1 hour", range_="Self"),
spell("Dissonant Whispers", 1, ENC, [BAR],             desc="WIS save or 3d6 psychic + use reaction to flee."),
spell("Divine Favor",      1, EVO, [PAL],              concentration=True, desc="+1d4 radiant on weapon attacks.", cast_time="Bonus action", duration="1 min", range_="Self"),
spell("Earth Tremor",      1, EVO, [BAR,DRU,SOR,WIZ], desc="DEX save or 1d6 bludgeoning + prone on loose earth.", source="EEPC", range_="10 ft"),
spell("Ensnaring Strike",  1, CON, [RAN],              concentration=True, desc="On next hit: STR save or restrained by magical vines; 1d6 piercing/turn.", cast_time="Bonus action", range_="Self"),
spell("Entangle",          1, CON, [DRU,RAN],              concentration=True, desc="20-ft square: STR save or restrained. Plants slow movement.", range_="90 ft"),
spell("Expeditious Retreat", 1, TRN, [ART,SOR,WAR,WIZ], concentration=True, desc="Dash as bonus action.", cast_time="Bonus action", duration="10 min", range_="Self"),
spell("Faerie Fire",       1, EVO, [ART,BAR,DRU],     concentration=True, desc="20-ft cube: DEX save or outlined in light; attacks have advantage."),
spell("False Life",        1, NEC, [ART,SOR,WIZ],     desc="Gain 1d4+4 temporary HP.", duration="1 hour", range_="Self"),
spell("Feather Fall",      1, TRN, [ART,BAR,SOR,WIZ], desc="Up to 5 falling creatures slow to 60 ft/round; no fall damage.", cast_time="Reaction"),
spell("Find Familiar",     1, CON, [ART,WAR,WIZ],     ritual=True, desc="Summon a spirit as animal familiar. Share senses, deliver touch spells.", cast_time="1 hour", range_="10 ft"),
spell("Fog Cloud",         1, CON, [DRU,RAN,SOR,WIZ], concentration=True, desc="20-ft radius sphere of heavy fog.", duration="1 hour", range_="120 ft"),
spell("Goodberry",         1, TRN, [DRU,RAN],          desc="Create up to 10 berries; each heals 1 HP (lasts 24 hr).", range_="Touch"),
spell("Grease",            1, CON, [ART,WIZ],          desc="10-ft square slick: DEX save or prone; difficult terrain.", duration="1 min"),
spell("Guiding Bolt",      1, EVO, [CLE],              desc="Ranged attack: 4d6 radiant; next attack has advantage. Scales.", range_="120 ft"),
spell("Hail of Thorns",    1, CON, [RAN],              concentration=True, desc="On next ranged hit: extra 1d10 piercing burst (DEX save). Scales.", cast_time="Bonus action", range_="Self"),
spell("Healing Word",      1, EVO, [BAR,CLE,DRU],     desc="Bonus action: heal 1d4 + spell mod. Scales.", cast_time="Bonus action"),
spell("Hellish Rebuke",    1, EVO, [WAR],              desc="Reaction: 2d10 fire (DEX save) when damaged. Scales.", cast_time="Reaction"),
spell("Heroism",           1, ENC, [BAR,PAL],          concentration=True, desc="Immune to Frightened; gain temp HP = spell mod/turn.", duration="1 min", range_="Touch"),
spell("Hex",               1, ENC, [WAR],              concentration=True, desc="Bonus action: curse target. Extra 1d6 necrotic on attacks; disadvantage on chosen ability checks.", cast_time="Bonus action", duration="1 hour", range_="90 ft"),
spell("Hunter's Mark",     1, DIV, [RAN],              concentration=True, desc="Bonus action: mark target. Extra 1d6 damage, advantage on tracking checks.", cast_time="Bonus action", duration="1 hour", range_="90 ft"),
spell("Ice Knife",         1, CON, [DRU,SOR,WIZ],     desc="Ranged attack: 1d10 piercing; burst 5 ft: DEX save or 2d6 cold. Scales.", source="EEPC"),
spell("Identify",          1, DIV, [ART,BAR,WIZ],     ritual=True, desc="Learn magic item properties, spells affecting creature, or spell being cast.", cast_time="1 min", range_="Touch"),
spell("Illusory Script",   1, ILL, [BAR,WAR,WIZ],     ritual=True, desc="Write message only intended creature can read (others see gibberish).", cast_time="1 min", duration="10 days", range_="Touch"),
spell("Inflict Wounds",    1, NEC, [CLE],              desc="Touch attack: 3d10 necrotic. Scales.", range_="Touch"),
spell("Jump",              1, TRN, [ART,DRU,RAN,SOR,WIZ], desc="Triple jump distance.", duration="1 min", range_="Touch"),
spell("Longstrider",       1, TRN, [ART,BAR,DRU,RAN,WIZ], desc="+10 ft speed.", duration="1 hour", range_="Touch"),
spell("Mage Armor",        1, ABJ, [SOR,WIZ],          desc="Target not in armor: AC = 13 + DEX mod.", duration="8 hours", range_="Touch"),
spell("Magic Missile",     1, EVO, [SOR,WIZ],          desc="3 darts, each 1d4+1 force. Auto-hits. Scales (+1 dart).", range_="120 ft"),
spell("Protection from Evil and Good", 1, ABJ, [CLE,DRU,PAL,WAR,WIZ], concentration=True, desc="Touch: protection from aberrations, celestials, elementals, fey, fiends, undead.", duration="10 min", range_="Touch"),
spell("Purify Food and Drink", 1, TRN, [ART,CLE,DRU,PAL], ritual=True, desc="Purify non-poisonous food and water in 5-ft sphere.", range_="10 ft"),
spell("Ray of Sickness",   1, NEC, [SOR,WIZ],          desc="Ranged attack: 2d8 poison; CON save or Poisoned 1 turn. Scales."),
spell("Sanctuary",         1, ABJ, [ART,CLE],          desc="Creature attacked? WIS save or pick new target. Ends if creature attacks.", cast_time="Bonus action", duration="1 min", range_="30 ft"),
spell("Shield",            1, ABJ, [SOR,WIZ],          desc="Reaction: +5 AC until start of next turn; immune to Magic Missile.", cast_time="Reaction", range_="Self"),
spell("Shield of Faith",   1, ABJ, [CLE,PAL],          concentration=True, desc="+2 AC bonus.", cast_time="Bonus action", duration="10 min"),
spell("Silent Image",      1, ILL, [BAR,SOR,WIZ],      concentration=True, desc="Create silent visual illusion in 15-ft cube."),
spell("Sleep",             1, ENC, [BAR,SOR,WIZ],      desc="5d8 HP worth of creatures fall unconscious.", duration="1 min", range_="90 ft"),
spell("Snare",             1, ABJ, [ART,DRU,RAN,WIZ], desc="Set a 5-ft-radius magical trap on ground: DEX save or restrained.", cast_time="1 min", source="XGE", range_="Touch"),
spell("Speak with Animals", 1, DIV, [BAR,DRU,RAN],    ritual=True, desc="Understand and communicate with beasts.", duration="10 min", range_="Self"),
spell("Tasha's Hideous Laughter", 1, ENC, [BAR,WIZ],  concentration=True, desc="WIS save or fall prone with laughter.", duration="1 min", range_="30 ft"),
spell("Thunderwave",       1, EVO, [BAR,CLE,DRU,SOR,WIZ], desc="15-ft cube: CON save or 2d8 thunder + pushed 10 ft. Scales.", range_="Self (15-foot cube)"),
spell("Unseen Servant",    1, CON, [BAR,WAR,WIZ],      ritual=True, desc="Invisible mindless servant performs simple tasks.", duration="1 hour"),
spell("Witch Bolt",        1, EVO, [SOR,WAR,WIZ],      concentration=True, desc="Ranged attack: 1d12 lightning; continue for 1d12/turn as action.", duration="1 min", range_="30 ft"),
spell("Wrathful Smite",    1, EVO, [PAL],              concentration=True, desc="On next hit: extra 1d6 psychic; WIS save or Frightened.", cast_time="Bonus action", range_="Self"),
spell("Zephyr Strike",     1, TRN, [RAN],              concentration=True, desc="Move without OA; one attack: advantage + extra 1d8 force + Dash.", cast_time="Bonus action", source="XGE", range_="Self"),

    spell("Catapult",           1, TRN, [ART,SOR,WIZ],    desc="Hurl an object weighing 1-5 lbs up to 90 ft (or throw AT one creature within 60 ft): 3d8 bludgeoning, DEX save for half — if thrown as a line, every creature in that line makes the save.", source="XGE"),
    spell("Ceremony",           1, ABJ, [CLE,PAL],         ritual=True, desc="Perform a religious ritual: bless water (holy water), coming of age, dedication, funeral rite, wedding. Effects vary.", source="XGE"),
    spell("Chaos Bolt",         1, EVO, [SOR],              desc="Ranged spell attack: 2d8 + 1d6 damage (choose type from d8 results — fire, cold, lightning, etc.). On doubles, chain to another creature.", source="XGE"),
    spell("Distort Value",      1, ILL, [BAR,WIZ],          desc="You distort an item's perceived value. Creatures that examine it believe its value is 10× or 1/10× the actual value for 8 hours.", source="AI"),
    spell("Gift of Alacrity",   1, DIV, [WIZ],              concentration=False, desc="A willing creature adds 1d8 to their initiative rolls for 8 hours.", source="EGW"),
    spell("Magnify Gravity",    1, TRN, [SOR,WIZ], desc="Point in space: all creatures within 10 ft sphere must save CON or take 2d8 force damage and have speed halved. Persistent pull each turn.", source="EGW"),
    spell("Searing Smite",      1, EVO, [PAL],              concentration=True, cast_time="Bonus action", desc="Next hit deals +1d6 fire damage and sets target ablaze: 1d6 fire at start of each turn (CON save ends). Target or ally can extinguish with action.", source="PHB"),
    spell("Silvery Barbs",      1, ENC, [BAR,SOR,WIZ],     cast_time="Reaction", desc="When a creature succeeds on an attack/ability check/save, force a reroll (take lower) and grant a different creature advantage on its next d20 roll.", source="SCC"),
    spell("Tasha's Caustic Brew",1,EVO,[ART,SOR,WIZ],      concentration=True, desc="Line 30 ft long 5 ft wide: creatures take 2d4 acid damage (DEX save); coated creatures take 2d4 acid each turn until removed.", source="TCE"),
    spell("Tenser's Floating Disk",1,CON,[WIZ],             ritual=True, desc="Creates a disk of force 3 ft in diameter hovering 3 ft off the ground. Holds 500 lbs. Follows within 20 ft. Lasts 1 hour.", source="PHB"),
    spell("Thunderous Smite",   1, EVO, [PAL],              concentration=True, cast_time="Bonus action", desc="Next melee hit: +2d6 thunder damage, audible 300 ft; target STR save or pushed 10 ft and knocked prone.", source="PHB"),

    spell("Jim's Glowing Coin", 2, ENC, [BAR,WIZ],             desc="Flip a coin that glows for 1 minute. One creature within 30 ft: WIS save or mesmerized until spell ends.", source="AI"),

# ── 2nd Level ─────────────────────────────────────────────────────────────────
spell("Aid",               2, ABJ, [ART,CLE,PAL],     desc="Up to 3 creatures: +5 max and current HP. Scales +5/slot.", range_="30 ft"),
spell("Alter Self",        2, TRN, [ART,SOR,WIZ],     concentration=True, desc="Aquatic Adaptation, Change Appearance, or Natural Weapons.", duration="1 hour", range_="Self"),
spell("Animal Messenger",  2, ENC, [BAR,DRU,RAN],     ritual=True, desc="Send a Tiny beast to deliver a message.", cast_time="1 action", duration="24 hours", range_="30 ft"),
spell("Arcane Lock",       2, ABJ, [ART,WIZ],          desc="Lock a door/window/chest magically.", cast_time="1 action", range_="Touch"),
spell("Augury",            2, DIV, [CLE],              ritual=True, desc="Ask about outcome of planned action in 30 min: Weal/Woe/Both/Neither.", cast_time="1 min", range_="Self"),
spell("Barkskin",          2, TRN, [DRU,RAN],          concentration=True, desc="Target's AC can't be less than 16.", duration="1 hour", range_="Touch"),
spell("Blindness/Deafness",2, NEC, [BAR,CLE,SOR,WIZ], desc="CON save or blinded or deafened 1 minute. Scales (targets).", range_="30 ft"),
spell("Blur",              2, ILL, [ART,SOR,WIZ],     concentration=True, desc="Attacks against you have disadvantage.", duration="1 min", range_="Self"),
spell("Branding Smite",    2, EVO, [PAL],              concentration=True, desc="Next hit: extra 2d6 radiant; target becomes visible.", cast_time="Bonus action", duration="1 min", range_="Self"),
spell("Calm Emotions",     2, ENC, [BAR,CLE],          concentration=True, desc="Suppress fear/charm or pacify hostile creatures in 20-ft radius.", duration="1 min"),
spell("Cloud of Daggers",  2, CON, [BAR,SOR,WAR,WIZ], concentration=True, desc="5-ft cube of spinning blades: 4d4 slashing on entry. Scales.", duration="1 min"),
spell("Crown of Madness",  2, ENC, [BAR,SOR,WAR,WIZ], concentration=True, desc="WIS save or charmed + attacks random adjacent creature.", duration="1 min", range_="120 ft"),
spell("Darkness",          2, EVO, [SOR,WAR,WIZ],     concentration=True, desc="15-ft sphere of magical darkness, blocks Darkvision.", duration="10 min"),
spell("Darkvision",        2, TRN, [ART,DRU,RAN,SOR,WIZ], desc="Grant Darkvision 60 ft.", duration="8 hours", range_="Touch"),
spell("Detect Thoughts",   2, DIV, [BAR,SOR,WIZ],     concentration=True, desc="Read surface thoughts; probe deeper with action (WIS save).", duration="1 min", range_="Self"),
spell("Dragon's Breath",   2, TRN, [SOR,WIZ],          concentration=True, desc="Grant creature 15-ft cone breath weapon (3d6 chosen type). Scales.", cast_time="Bonus action", source="XGE", range_="Touch"),
spell("Dust Devil",        2, CON, [DRU,SOR,WIZ],     concentration=True, desc="5-ft elemental whirlwind: STR save or 1d8 bludgeoning + pulled.", source="EEPC"),
spell("Earthbind",         2, TRN, [DRU,SOR,WAR,WIZ], concentration=True, desc="STR save or speed to 0 and can't fly.", source="EEPC", range_="300 ft"),
spell("Enhance Ability",   2, TRN, [ART,BAR,CLE,DRU,SOR,WIZ], concentration=True, desc="Grant Bull's Strength/Cat's Grace/Bear's Endurance/Fox's Cunning/Eagle's Splendor/Owl's Wisdom.", duration="1 hour", range_="Touch"),
spell("Enlarge/Reduce",    2, TRN, [ART,SOR,WIZ],     concentration=True, desc="Double or halve creature's size and damage.", duration="1 min", range_="30 ft"),
spell("Enthrall",          2, ENC, [BAR,WAR],          desc="WIS save or creature focuses on you; disadv Perception vs others."),
spell("Find Steed",        2, CON, [PAL],              desc="Summon spirit as warhorse/pony/mastiff/camel/elk. Bond with steed.", cast_time="10 min", range_="30 ft"),
spell("Find Traps",        2, DIV, [CLE,DRU,RAN],     desc="Sense traps within 120 ft.", range_="120 ft"),
spell("Flame Blade",       2, EVO, [DRU],              concentration=True, desc="Melee spell weapon: 3d6 fire. Scales.", cast_time="Bonus action", duration="10 min", range_="Self"),
spell("Flaming Sphere",    2, CON, [DRU,WIZ],          concentration=True, desc="5-ft sphere of fire: 2d6 fire/turn adjacent; can ram. Scales.", duration="1 min"),
spell("Gentle Repose",     2, NEC, [CLE,WIZ],          ritual=True, desc="Preserve corpse from decay, delays resurrection timer.", cast_time="1 action", duration="10 days", range_="Touch"),
spell("Gust of Wind",      2, EVO, [DRU,SOR,WIZ],     concentration=True, desc="Line of wind: pushed back or STR save; extinguishes flames.", duration="1 min", range_="Self (60-foot line)"),
spell("Heat Metal",        2, TRN, [ART,DRU],          concentration=True, desc="Metal object sears: 2d8 fire/turn; drop item or disadv attacks. Scales.", duration="1 min"),
spell("Hold Person",       2, ENC, [BAR,CLE,DRU,SOR,WAR,WIZ], concentration=True, desc="WIS save or Paralyzed humanoid. Scales (targets).", duration="1 min"),
spell("Invisibility",      2, ILL, [ART,BAR,SOR,WAR,WIZ], concentration=True, desc="Target invisible until it attacks/casts. Scales (targets).", duration="1 hour", range_="Touch"),
spell("Knock",             2, TRN, [BAR,SOR,WIZ],          desc="Open locked/barred/stuck object. Audible 300 ft."),
spell("Lesser Restoration", 2, ABJ, [ART,BAR,CLE,DRU,PAL,RAN], desc="End disease or condition: blinded/deafened/paralyzed/poisoned.", range_="Touch"),
spell("Levitate",          2, TRN, [ART,SOR,WIZ],     concentration=True, desc="Target rises up to 20 ft; can move up/down 20 ft/turn.", duration="10 min"),
spell("Locate Animals or Plants", 2, DIV, [BAR,DRU,RAN], ritual=True, desc="Sense nearest creature/plant of specific type within 5 miles.", cast_time="1 action", range_="Self"),
spell("Locate Object",     2, DIV, [BAR,CLE,DRU,PAL,RAN,WIZ], concentration=True, desc="Sense specific known object within 1000 ft.", duration="10 min", range_="Self"),
spell("Magic Mouth",       2, ILL, [ART,BAR,WIZ],     ritual=True, desc="Imbue message triggered by condition.", cast_time="1 min", range_="30 ft"),
spell("Magic Weapon",       2, TRN, [ART,PAL,RAN,WIZ],     concentration=True, desc="+1 magic weapon. Scales to +2/+3.", cast_time="Bonus action", duration="1 hour", range_="Touch"),
spell("Maximilian's Earthen Grasp", 2, TRN, [SOR,WIZ], concentration=True, desc="STR save or restrained by hand. Repeating STR save.", source="EEPC", range_="30 ft"),
spell("Melf's Acid Arrow", 2, EVO, [WIZ],              desc="Ranged attack: 4d4 acid + 2d4 end of next turn. Scales.", range_="90 ft"),
spell("Mind Spike",        2, DIV, [SOR,WAR,WIZ],     concentration=True, desc="INT save or 3d8 psychic; know location while concentrating.", source="XGE"),
spell("Mirror Image",      2, ILL, [SOR,WAR,WIZ],     desc="3 illusory duplicates; attacker might hit duplicate instead.", duration="1 min", range_="Self"),
spell("Misty Step",         2, CON, [ART,SOR,WAR,WIZ],     desc="Teleport up to 30 ft to visible unoccupied space.", cast_time="Bonus action", range_="Self"),
spell("Moonbeam",          2, EVO, [DRU],              concentration=True, desc="5-ft column: CON save or 2d10 radiant; shapechangers have disadv. Scales.", duration="1 min", range_="120 ft"),
spell("Nathair's Mischief",2, ILL, [BAR,SOR,WIZ],     concentration=True, desc="20-ft cube each turn: random wacky effect.", source="FTD"),
spell("Pass without Trace", 2, ABJ, [DRU,RAN],         concentration=True, desc="+10 to Stealth; can't be tracked non-magically.", duration="1 hour", range_="Self"),
spell("Prayer of Healing", 2, EVO, [CLE],              desc="Up to 6 creatures heal 2d8 + spell mod. Scales.", cast_time="10 min", range_="30 ft"),
spell("Protection from Poison", 2, ABJ, [ART,CLE,DRU,PAL,RAN], desc="Neutralize poison; resistance to poison damage.", duration="1 hour", range_="Touch"),
spell("Ray of Enfeeblement", 2, NEC, [WAR,WIZ],        concentration=True, desc="Ranged attack; CON save or STR-based attacks deal half damage.", duration="1 min"),
spell("Rope Trick",        2, TRN, [ART,WIZ],          desc="Rope becomes ladder to extradimensional space (8 Medium creatures).", duration="1 hour", range_="Touch"),
spell("Scorching Ray",     2, EVO, [SOR,WIZ],          desc="3 ranged attacks: each 2d6 fire. Scales (+1 ray).", range_="120 ft"),
spell("See Invisibility",  2, DIV, [ART,BAR,SOR,WIZ], desc="See invisible creatures and objects.", duration="1 hour", range_="Self"),
spell("Shadow Blade",      2, ILL, [SOR,WAR,WIZ],     concentration=True, desc="Illusion sword: 2d8 psychic, light finesse; adv in dim/dark. Scales.", cast_time="Bonus action", source="XGE", range_="Self"),
spell("Shatter",            2, EVO, [ART,BAR,SOR,WAR,WIZ], desc="10-ft sphere: CON save or 3d8 thunder. Scales."),
spell("Silence",           2, ILL, [BAR,CLE,RAN],     ritual=True, concentration=True, desc="20-ft radius sphere: no sound, immunity to thunder, V/S spells fail.", duration="10 min", range_="120 ft"),
spell("Skywrite",          2, TRN, [ART,BAR,DRU,WIZ], ritual=True, concentration=True, desc="Write message in clouds visible up to 10 miles.", source="EEPC", range_="Sight"),
spell("Spider Climb",      2, TRN, [ART,SOR,WAR,WIZ], concentration=True, desc="Climb any surface; sticky feet.", duration="1 hour", range_="Touch"),
spell("Spike Growth",      2, TRN, [DRU,RAN],          concentration=True, desc="20-ft radius: difficult terrain + 2d4 piercing per 5 ft moved.", duration="10 min", range_="150 ft"),
spell("Spiritual Weapon",  2, EVO, [CLE],              desc="Bonus action: spectral weapon (2d8+spell mod). Move and attack each turn. Scales.", cast_time="Bonus action", duration="1 min"),
spell("Suggestion",        2, ENC, [BAR,SOR,WAR,WIZ], concentration=True, desc="WIS save or follow reasonable suggestion (not self-harmful) 8 hours.", duration="8 hours", range_="30 ft"),
spell("Summon Beast",      2, CON, [DRU,RAN],          concentration=True, desc="Summon Air/Land/Water bestial spirit. Scales.", source="TCE", range_="90 ft"),
spell("Tasha's Mind Whip",  2, ENC, [SOR,WIZ,BAR,WAR],          desc="INT save or 3d6 psychic + lose reaction + limited next action. Scales.", source="TCE", range_="90 ft"),
spell("Vortex Warp",       2, CON, [ART,SOR,WIZ],     desc="CON save or teleport willing/unwilling creature up to 90 ft.", source="SCC", range_="90 ft"),
spell("Warding Bond",       2, ABJ, [CLE,PAL],              desc="Bonded creature: +1 AC/saves, resistance all dmg. You take same damage.", duration="1 hour", range_="Touch"),
spell("Web",               2, CON, [ART,SOR,WIZ],     concentration=True, desc="20-ft cube: difficult terrain; DEX save or restrained. Flammable.", duration="1 hour"),
spell("Wristpocket",       2, CON, [SOR,WAR,WIZ], ritual=True,     concentration=True, desc="Store one item in extradimensional pocket.", source="EGW", range_="Self"),
spell("Zone of Truth",     2, ENC, [BAR,CLE,PAL],     desc="15-ft sphere: CHA save or can't lie.", duration="10 min"),

    spell("Aganazzar's Scorcher",2,EVO,[SOR,WIZ], desc="30-ft line: 3d8 fire (DEX save). Adjacent creatures: 2d8. Creatures that enter at start of their turn take 3d8.", source="XGE"),
    spell("Beast Sense",        2, DIV, [DRU,RAN],          ritual=True, concentration=True, desc="Touch a willing beast and sense through its senses until the spell ends or you use your own.", source="PHB"),
    spell("Borrowed Knowledge", 2, DIV, [BAR,WAR,WIZ],     desc="You gain proficiency in one skill of your choice for 1 hour.", source="SCC"),
    spell("Continual Flame",    2, EVO, [CLE,WIZ],          desc="A flame equivalent to a torch springs from an object. Creates no heat, uses no oxygen. Can be covered but not smothered.", source="PHB"),
    spell("Fortune's Favor",    2, DIV, [WIZ], desc="Up to 2 willing creatures. Once before the spell ends, each target can reroll one attack, save, or ability check. Take the better roll.", source="EGW"),
    spell("Gift of Gab",        2, ENC, [BAR],               cast_time="Reaction", desc="When you inadvertently reveal a secret, you can make two creatures within 5 ft forget what you said (WIS save).", source="AI"),
    spell("Jim's Magic Missile",1, EVO, [WIZ],               desc="Like Magic Missile, but costs 1 gp material component. Each dart deals 2d4+2 force. Alternatively, all five darts target one creature.", source="AI"),
    spell("Kinetic Jaunt",      2, TRN, [ART,BAR,SOR,WIZ], concentration=True, cast_time="Bonus action", desc="Speed +10 ft. You can move through other creatures' spaces (not difficult terrain). No OA. 1 minute.", source="SCC"),
    spell("Nystul's Magic Aura",2, ILL, [WIZ],              desc="Change what spells such as Detect Magic reveal about a target. Up to 30 days. Mask a magic item as nonmagical or vice versa.", source="PHB"),
    spell("Phantasmal Force",   2, ILL, [BAR,SOR,WAR,WIZ], concentration=True, desc="One creature: INT save or believe in an illusion you describe (max 10-ft cube). Creature takes 1d6 psychic each turn it interacts with it.", source="PHB"),
    spell("Pyrotechnics",       2, TRN, [ART,BAR,SOR,WIZ], desc="Nonmagical fire in 60 ft: choose blinding fireworks (CON save or blinded 1 round, 10-ft radius) or 20-ft obscuring smoke cloud.", source="XGE"),
    spell("Snilloc's Snowball Swarm",2,EVO,[SOR,WIZ],       desc="Swarm of snowballs erupts in 5-ft radius sphere: 3d6 cold (DEX save for half).", source="XGE"),
    spell("Warding Wind",       2, EVO, [BAR,SOR,WIZ],      concentration=True, desc="Deafening 10-mph wind in a 10-ft radius around you: deafened, ranged attacks through it have disadvantage, difficult terrain for others.", source="XGE", range_="Self (10-foot radius)"),
    spell("Wither and Bloom",   2, NEC, [DRU,SOR,WIZ],      desc="Plants in 10-ft radius wither, +1d6 cold per plant. One creature: regain HP equal to your spellcasting modifier + 1d6 per spent HD.", source="SCC"),

# ── 3rd Level ─────────────────────────────────────────────────────────────────
spell("Animate Dead",      3, NEC, [CLE,WIZ],          desc="Animate 1 skeleton/zombie from corpse. Scales (+2/slot).", range_="10 ft"),
spell("Aura of Vitality",   3, EVO, [CLE,DRU,PAL],              concentration=True, desc="30-ft aura; bonus action heal 2d6 once per turn.", cast_time="1 action", duration="1 min", source="PHB", range_="Self (30-foot radius)"),
spell("Beacon of Hope",    3, ABJ, [CLE],              concentration=True, desc="Adv WIS saves and death saves; max healing.", duration="1 min", range_="30 ft"),
spell("Bestow Curse",      3, NEC, [BAR,CLE,WIZ],     concentration=True, desc="Touch; WIS save or cursed with chosen effect.", duration="1 min", range_="Touch"),
spell("Blink",             3, TRN, [ART,SOR,WIZ],     desc="50% chance to vanish to Ethereal each turn. Return start of next.", duration="1 min", range_="Self"),
spell("Call Lightning",    3, CON, [DRU],              concentration=True, desc="Thunderstorm: action to call bolt, 3d10 lightning (DEX save). Scales.", duration="10 min", range_="120 ft"),
spell("Catnap",            3, ENC, [ART,BAR,SOR,WIZ], desc="Up to 3 willing creatures take a short rest in 10 min.", cast_time="1 action", source="XGE", components="S", range_="30 ft"),
spell("Clairvoyance",      3, DIV, [BAR,CLE,SOR,WIZ], concentration=True, desc="Create invisible sensor you see/hear through.", cast_time="10 min", duration="10 min", range_="1 mile"),
spell("Conjure Animals",   3, CON, [DRU,RAN],          concentration=True, desc="Summon 1 CR2 / 2 CR1 / 4 CR1/2 / 8 CR1/4 beasts. Scales.", duration="1 hour"),
spell("Conjure Barrage",   3, CON, [RAN],              desc="60-ft cone of nonmagical ammo: DEX save or 3d8 (weapon type). Scales.", source="PHB", range_="Self (60-foot cone)"),
spell("Counterspell",      3, ABJ, [SOR,WAR,WIZ],     desc="Reaction: interrupt a spell 3rd level or lower (auto) or higher (ability check).", cast_time="Reaction"),
spell("Create Food and Water", 3, CON, [CLE,DRU,PAL], desc="Feed 15 humanoids and 5 horses.", range_="30 ft"),
spell("Daylight",          3, EVO, [CLE,DRU,PAL,RAN,SOR], desc="60-ft radius bright light from object/point.", duration="1 hour"),
spell("Dispel Magic",      3, ABJ, [ART,BAR,CLE,DRU,PAL,SOR,WAR,WIZ], desc="End spell effects of 3rd level or lower; check for higher.", range_="120 ft"),
spell("Elemental Weapon",  3, TRN, [ART,PAL],          concentration=True, desc="+1 magic weapon; extra 1d4 (chosen element) on hits. Scales.", duration="1 hour", range_="Touch"),
spell("Erupting Earth",    3, TRN, [DRU,SOR,WIZ],     desc="20-ft cube: DEX save or 3d12 bludgeoning; difficult terrain. Scales.", source="EEPC", range_="120 ft"),
spell("Fear",              3, ILL, [BAR,SOR,WAR,WIZ], concentration=True, desc="30-ft cone: WIS save or Frightened and must flee.", duration="1 min", range_="Self (30-foot cone)"),
spell("Feign Death",       3, NEC, [BAR,CLE,DRU,WIZ], ritual=True, desc="Willing creature appears dead; resists dmg/disease.", duration="1 hour", range_="Touch"),
spell("Fireball",          3, EVO, [SOR,WIZ],          desc="20-ft sphere: DEX save or 8d6 fire. Scales.", range_="150 ft"),
spell("Fly",               3, TRN, [ART,SOR,WAR,WIZ], concentration=True, desc="Flying speed 60 ft. Scales (targets).", cast_time="1 action", duration="10 min", range_="Touch"),
spell("Gaseous Form",       3, TRN, [ART,SOR,WAR,WIZ],     concentration=True, desc="Transform creature into misty cloud; fly 10 ft.", duration="1 hour", range_="Touch"),
spell("Glyph of Warding",  3, ABJ, [ART,BAR,CLE,WIZ], desc="Inscribe glyph; triggers spell or blast 5d8 (chosen type). Scales.", cast_time="1 hour", range_="Touch"),
spell("Haste",             3, TRN, [ART,SOR,WIZ],     concentration=True, desc="Double speed, +2 AC, extra action (attack/Dash/etc).", duration="1 min", range_="30 ft"),
spell("Hypnotic Pattern",  3, ILL, [BAR,SOR,WAR,WIZ], concentration=True, desc="30-ft cube: WIS save or Incapacitated (charmed).", duration="1 min", range_="120 ft"),
spell("Intellect Fortress", 3, ABJ, [ART,BAR,SOR,WAR,WIZ], concentration=True, desc="Resistance psychic damage; advantage on INT/WIS/CHA saves.", source="TCE", duration="1 minute", range_="30 ft"),
spell("Life Transference", 3, NEC, [CLE,WIZ],          desc="Take 4d8 necrotic; target heals twice that.", source="XGE", range_="30 ft"),
spell("Lightning Arrow",   3, TRN, [RAN],              concentration=True, desc="Next ranged attack: 4d8 lightning + 10-ft burst 2d8 (DEX save). Both the hit damage and burst damage increase by 1d8 per slot level above 3rd.", cast_time="Bonus action", range_="Self"),
spell("Lightning Bolt",    3, EVO, [SOR,WIZ],          desc="100-ft line: DEX save or 8d6 lightning. Scales.", range_="Self (100-foot line)"),
spell("Magic Circle",      3, ABJ, [CLE,PAL,WAR,WIZ], desc="10-ft cylinder: prevent entry/exit of chosen creature type.", cast_time="1 min", duration="1 hour", range_="10 ft"),
spell("Major Image",       3, ILL, [BAR,SOR,WAR,WIZ], concentration=True, desc="Create sensory illusion up to 20-ft cube.", duration="10 min", range_="120 ft"),
spell("Mass Healing Word", 3, EVO, [CLE],              desc="Bonus action: up to 6 creatures heal 1d4+spell mod. Scales.", cast_time="Bonus action", components="V"),
spell("Meld into Stone",   3, TRN, [CLE,DRU],         ritual=True, desc="Step into stone; can emerge or be forced out.", duration="8 hours", range_="Touch"),
spell("Nondetection",       3, ABJ, [ART,BAR,RAN,WIZ],     desc="Target hidden from divination magic.", cast_time="1 action", duration="8 hours", range_="Touch"),
spell("Phantom Steed",     3, ILL, [WIZ],              ritual=True, desc="Create quasi-real steed (speed 100 ft).", cast_time="1 min", duration="1 hour", range_="30 ft"),
spell("Plant Growth",      3, TRN, [BAR,DRU,RAN],     desc="Plants overgrow area (slow traversal) OR enrich acre for a year.", range_="150 ft"),
spell("Protection from Energy", 3, ABJ, [ART,CLE,DRU,RAN,SOR,WIZ], concentration=True, desc="Resistance to chosen energy type.", duration="1 hour", range_="Touch"),
spell("Remove Curse",      3, ABJ, [CLE,PAL,WAR,WIZ], desc="End all curses on a creature or object.", range_="Touch"),
spell("Revivify",          3, NEC, [ART,CLE,PAL],     desc="Restore creature dead ≤ 1 min to 1 HP.", range_="Touch"),
spell("Sending",           3, EVO, [BAR,CLE,WIZ],     desc="Send 25-word message anywhere; recipient can reply.", range_="Unlimited"),
spell("Sleet Storm",       3, CON, [DRU,SOR,WIZ],     concentration=True, desc="40-ft cylinder: heavily obscured, difficult terrain, DEX save or prone.", duration="1 min", range_="150 ft"),
spell("Slow",              3, TRN, [SOR,WIZ],          concentration=True, desc="Up to 6 creatures in a 40-ft cube: WIS save or half speed, −2 AC, no reactions, limited actions.", duration="1 min", range_="120 ft"),
spell("Speak with Dead",   3, NEC, [BAR,CLE],          desc="Ask 5 questions of corpse (max); knows only what it knew.", range_="10 ft"),
spell("Speak with Plants", 3, TRN, [BAR,DRU,RAN],     desc="Communicate with plants; free restrained creatures in plants.", duration="10 min", range_="Self (30-foot radius)"),
spell("Spirit Guardians",  3, CON, [CLE],              concentration=True, desc="15-ft aura: WIS save or half speed; 3d8 radiant/necrotic. Scales.", duration="10 min", range_="Self (15-foot radius)"),
spell("Spirit Shroud",     3, NEC, [CLE,PAL,WAR,WIZ], concentration=True, desc="+1d8 necrotic/radiant/cold on attacks; targets can't regain HP. Scales.", cast_time="Bonus action", source="TCE", range_="Self"),
spell("Stinking Cloud",    3, CON, [BAR,SOR,WIZ],     concentration=True, desc="20-ft sphere: CON save or waste action retching.", duration="1 min", range_="90 ft"),
spell("Summon Fey",        3, CON, [DRU,RAN,WAR,WIZ], concentration=True, desc="Summon fey spirit. Scales.", source="TCE", range_="90 ft"),
spell("Summon Lesser Demons", 3, CON, [WAR,WIZ],       concentration=True, desc="Summon 1d6+2 dretches/manes. Scales.", source="XGE"),
spell("Summon Shadowspawn", 3, CON, [WAR,WIZ],         concentration=True, desc="Summon shadow spirit (Fury/Despair/Fear). Scales.", source="TCE", range_="90 ft"),
spell("Summon Undead",     3, NEC, [WAR,WIZ],          concentration=True, desc="Summon undead spirit (Skeletal/Putrid/Ghostly). Scales.", source="TCE", range_="90 ft"),
spell("Thunder Step",      3, CON, [SOR,WAR,WIZ],     desc="Teleport up to 90 ft; 3d10 thunder burst at origin (CON save). Scales.", source="XGE", range_="90 ft"),
spell("Tidal Wave",        3, CON, [DRU,SOR,WIZ],     desc="30×10×10-ft wave: DEX save or 4d8 bludgeoning + prone.", source="EEPC", range_="120 ft"),
spell("Tongues",           3, DIV, [BAR,CLE,SOR,WAR,WIZ], desc="Touch; creature understands and speaks any language.", duration="1 hour", range_="Touch"),
spell("Vampiric Touch",    3, NEC, [WAR,WIZ],          concentration=True, desc="Melee spell attack: 3d6 necrotic; heal half. Scales.", duration="1 min", range_="Self"),
spell("Wall of Sand",      3, EVO, [WIZ],              concentration=True, desc="Wall of swirling sand blocks visibility; STR/DEX check to pass.", source="EEPC", range_="90 ft"),
spell("Wall of Water",     3, EVO, [DRU,SOR,WIZ],     concentration=True, desc="Wall of water (30-ft long, 10-ft high, 1-ft thick, or a 20-ft-diameter ring) impedes and provides cover.", source="EEPC"),
spell("Water Breathing",   3, TRN, [ART,DRU,RAN,SOR,WIZ], ritual=True, desc="Up to 10 creatures breathe underwater.", duration="24 hours", range_="30 ft"),
spell("Water Walk",        3, TRN, [CLE,DRU,RAN,SOR], ritual=True, desc="Up to 10 creatures walk on liquid surfaces.", duration="1 hour", range_="30 ft"),
spell("Wind Wall",         3, EVO, [DRU,RAN],          concentration=True, desc="Wall of wind: 1d8 bludgeoning; deflects gas/arrows.", duration="1 min", range_="120 ft"),

    spell("Crusader's Mantle",  3, EVO, [PAL],              concentration=True, desc="Aura 30 ft: you and allies' weapon attacks deal +1d4 radiant damage.", source="PHB"),
    spell("Enemies Abound",     3, ENC, [BAR,SOR,WAR,WIZ], concentration=True, desc="One creature: INT save or lose ability to distinguish friend from foe. Randomly attacks nearest creature.", source="XGE"),
    spell("Fast Friends",       3, ENC, [BAR,WAR,WIZ],      concentration=True, desc="One creature that can hear you: WIS save or charmed for 1 hour, willing to perform reasonable tasks.", source="XGE"),
    spell("Flame Arrows",       3, TRN, [DRU,RAN,SOR,WIZ], concentration=True, desc="Up to 12 arrows/bolts become magical; each deals +1d6 fire damage. Lasts until used or 1 hour.", source="XGE"),
    spell("Hunger of Hadar",    3, CON, [WAR],              concentration=True, desc="20-ft sphere of tentacles: deafened, cold damage on enter and end of turn; blinded inside.", source="PHB"),
    spell("Leomund's Tiny Hut", 3, EVO, [BAR,WIZ],          ritual=True, desc="Dome 10-ft radius: movement blocked, mundane weather blocked, inside is comfortable temperature. Holds 9 Medium or smaller creatures. 8 hours.", source="PHB"),
    spell("Maelstrom",          5, EVO, [DRU],              concentration=True, desc="30-ft radius circle of churning water. Moving through it costs 2 extra ft per ft. Creatures start turn: STR save or pulled 10 ft toward center + 6d6 bludgeoning.", source="XGE"),
    spell("Melf's Minute Meteors",3,EVO,[SOR,WIZ],          concentration=True, desc="Six meteors orbit you. Bonus action to send 1-2: each +2 attack to hit, 2d6 fire, 5-ft radius splash DEX save.", source="XGE"),
    spell("Pulse Wave",         3, EVO, [SOR,WIZ],          desc="30-ft cone: push (CON save) or pull, 6d6 force damage. Unshielded flames extinguished.", source="EGW"),
    spell("Tiny Servant",       3, TRN, [ART,WIZ],          desc="Animate a Tiny object for 8 hours. AC 10, 10 HP, STR 4, DEX 16. Speed 30 (climb 30). Can attack (1d4+3). One free, up to 4 with higher spell slots.", source="XGE"),

# ── 4th Level ─────────────────────────────────────────────────────────────────
spell("Arcane Eye",        4, DIV, [ART,WIZ],          concentration=True, desc="Invisible sensor you see through (darkvision 30 ft); move 30 ft/action.", duration="1 hour", range_="30 ft"),
spell("Aura of Life",       4, ABJ, [CLE,PAL],              concentration=True, desc="30-ft aura; resistance necrotic; restore 0-HP creatures to 1 HP at turn start.", duration="10 min", source="PHB", range_="Self (30-foot radius)"),
spell("Aura of Purity",    4, ABJ, [PAL],              concentration=True, desc="30-ft aura; resist poison; immune disease/charm/fear/poisoned.", duration="10 min", source="PHB", range_="Self (30-foot radius)"),
spell("Banishment",        4, ABJ, [CLE,PAL,SOR,WAR,WIZ], concentration=True, desc="CHA save or creature sent to harmless demiplane (banished if sustained)."),
spell("Blight",            4, NEC, [DRU,SOR,WAR,WIZ], desc="CON save or 8d8 necrotic (half fail; quarter pass). Plants get no save.", range_="30 ft"),
spell("Compulsion",        4, ENC, [BAR],              concentration=True, desc="WIS save or controlled movement direction each turn.", duration="1 min", range_="30 ft"),
spell("Confusion",         4, ENC, [BAR,DRU,SOR,WIZ], concentration=True, desc="10-ft sphere: WIS save or random action each turn.", duration="1 min", range_="90 ft"),
spell("Conjure Minor Elementals", 4, CON, [DRU,WIZ],  concentration=True, desc="Summon up to 4 CR1 or 8 CR1/2 or 16 CR1/4 elementals. Scales.", duration="1 hour", range_="90 ft"),
spell("Conjure Woodland Beings", 4, CON, [DRU,RAN],   concentration=True, desc="Summon fey (like minor elementals). Scales.", duration="1 hour"),
spell("Control Water",     4, TRN, [CLE,DRU,WIZ],     concentration=True, desc="Flood/drain/redirect/whirlpool control of water in 100-ft cube.", duration="10 min", range_="300 ft"),
spell("Death Ward",        4, ABJ, [CLE,PAL],          desc="Once: drop to 1 HP instead of 0.", duration="8 hours", range_="Touch"),
spell("Dimension Door",     4, CON, [ART,BAR,SOR,WAR,WIZ], desc="Teleport up to 500 ft, bring 1 willing creature.", range_="500 ft"),
spell("Divination",        4, DIV, [CLE],              ritual=True, desc="Receive truthful answer to one question about event within 7 days.", cast_time="1 action", range_="Self"),
spell("Dominate Beast",    4, ENC, [DRU,RAN,SOR],     concentration=True, desc="WIS save or beast obeys commands.", duration="1 min"),
spell("Evard's Black Tentacles", 4, CON, [WIZ],       concentration=True, desc="20-ft square becomes difficult terrain; entering/starting turn there: DEX save or 3d6 bludgeoning + restrained. Restrained creature can STR/DEX check vs your save DC to break free.", duration="1 min", range_="90 ft", components="V, S, M (a piece of tentacle from a giant octopus or squid)"),
spell("Fabricate",         4, TRN, [ART,WIZ],          desc="Transform 10-cu-ft material into finished product.", cast_time="10 min", range_="120 ft"),
spell("Fire Shield",        4, EVO, [DRU,SOR,WIZ],          desc="Warm shield (cold resist, fire retaliation 2d8) or chill shield (fire resist, cold retaliation).", duration="10 min", range_="Self"),
spell("Freedom of Movement", 4, ABJ, [ART,BAR,CLE,DRU,RAN], desc="Ignore nonmagical difficult terrain; not slowed by magic; free from paralysis.", duration="1 hour", range_="Touch"),
spell("Giant Insect",      4, TRN, [DRU],              concentration=True, desc="Transform insects into giant versions for combat.", duration="10 min", range_="30 ft"),
spell("Grasping Vine",     4, CON, [DRU,RAN],          concentration=True, desc="Vine that grabs and yanks a creature 20 ft each turn.", cast_time="Bonus action", range_="30 ft"),
spell("Greater Invisibility", 4, ILL, [ART,BAR,SOR,WIZ], concentration=True, desc="Target invisible even when attacking/casting.", duration="1 min", range_="Touch"),
spell("Guardian of Faith", 4, CON, [CLE],              desc="Large spectral guardian: radiant damage to enterers (DEX save). Scales.", range_="30 ft"),
spell("Hallucinatory Terrain", 4, ILL, [BAR,DRU,WAR,WIZ], desc="Disguise natural terrain (150-ft cube) as another kind.", duration="24 hours", range_="300 ft"),
spell("Ice Storm",         4, EVO, [DRU,SOR,WIZ],     desc="20-ft cylinder: 2d8 bludgeoning + 4d6 cold (DEX save); difficult terrain. Scales.", range_="300 ft"),
spell("Leomund's Secret Chest", 4, CON, [WIZ],         desc="Hide a chest (up to 12 cu ft) on the Ethereal Plane; recall or re-send it with an action while touching its Tiny replica. 5%/day cumulative chance the effect ends after 60 days.", range_="Touch", components="V, S, M (an exquisite chest worth 5,000+ gp and a Tiny replica worth 50+ gp)"),
spell("Locate Creature",   4, DIV, [BAR,CLE,DRU,PAL,RAN,WIZ], concentration=True, desc="Sense specific creature or type within 1000 ft.", duration="1 hour", range_="Self"),
spell("Phantasmal Killer", 4, ILL, [WIZ],              concentration=True, desc="Nightmare: WIS save or Frightened; 4d10 psychic/turn (WIS save). Scales.", duration="1 min", range_="120 ft"),
spell("Polymorph",          4, TRN, [ART,BAR,DRU,SOR,WIZ], concentration=True, desc="Transform creature into beast whose CR ≤ level/4 (or up to its own CR).", duration="1 hour"),
spell("Resilient Sphere",  4, EVO, [ART,WIZ],          concentration=True, desc="10-ft diameter sphere: can't be harmed, can't exit/enter.", duration="1 min", range_="30 ft"),
spell("Shadow of Moil",    4, NEC, [WAR],              concentration=True, desc="Heavily obscured; 2d8 necrotic aura; resistance cold/necrotic.", duration="1 min", source="XGE", range_="Self"),
spell("Sickening Radiance", 4, EVO, [SOR,WAR,WIZ],    concentration=True, desc="30-ft sphere: CON save or 4d10 radiant + 1 exhaustion.", duration="10 min", source="XGE", range_="120 ft"),
spell("Spirit of Death",   4, NEC, [WAR,WIZ],          concentration=True, desc="Summon reaper spirit. Scales.", source="BOMT"),
spell("Stone Shape",       4, TRN, [ART,CLE,DRU,WIZ], desc="Reshape one stone object (up to 5 cu ft) or form a door.", range_="Touch"),
spell("Staggering Smite",  4, EVO, [PAL],              cast_time="Bonus action", concentration=True, desc="Next melee hit this spell's duration: +4d6 psychic. WIS save or disadvantage on attacks/checks + no reactions until end of its next turn.", duration="1 min", range_="Self", components="V"),
spell("Stoneskin",         4, ABJ, [ART,DRU,RAN,SOR,WIZ], concentration=True, desc="Resistance to nonmagical B/P/S.", duration="1 hour", range_="Touch"),
spell("Storm Sphere",      4, EVO, [SOR,WIZ],          concentration=True, desc="20-ft sphere: bonus ranged attack 4d6 lightning; DEX save 2d6 thunder. Scales.", source="XGE", range_="150 ft"),
spell("Summon Aberration", 4, CON, [WAR,WIZ],          concentration=True, desc="Summon aberrant spirit. Scales.", source="TCE", range_="90 ft"),
spell("Summon Construct",  4, CON, [ART,WIZ],          concentration=True, desc="Summon construct spirit. Scales.", source="TCE", range_="90 ft"),
spell("Summon Elemental",  4, CON, [DRU,RAN,WIZ],     concentration=True, desc="Summon elemental spirit. Scales.", source="TCE", range_="90 ft"),
spell("Vitriolic Sphere",  4, EVO, [SOR,WIZ],          desc="20-ft sphere: DEX save or 10d4 acid + 5d4 next turn. Scales.", source="XGE", range_="150 ft"),
spell("Wall of Fire",      4, EVO, [DRU,SOR,WIZ],     concentration=True, desc="60 ft wall: 5d8 fire to one side (DEX save). Scales.", duration="1 min", range_="120 ft"),
spell("Watery Sphere",     4, CON, [DRU,SOR,WIZ],     concentration=True, desc="Engulf creatures in 5-ft sphere; STR save or restrained.", source="EEPC", range_="90 ft"),

    spell("Charm Monster",      4, ENC, [BAR,DRU,SOR,WAR,WIZ],
          desc="One creature: WIS save or charmed for 1 hour regardless of creature type.", source="XGE"),
    spell("Elemental Bane",     4, TRN, [ART,DRU,SOR,WAR,WIZ], concentration=True,
          desc="One creature: CON save or suffer vulnerability to chosen damage type and can't be immune/resistant to it for 1 min.", source="XGE"),
    spell("Find Greater Steed", 4, CON, [PAL],
          desc="Summon a Pegasus, Peryton, Dire Wolf, Rhinoceros, Saber-toothed Tiger, or Giant Owl as a steed.", source="XGE"),
    spell("Gravity Sinkhole",   4, EVO, [SOR,WIZ],
          desc="20-ft radius sphere: STR save or 5d10 force + pulled 5 ft toward center each turn. Difficult terrain.", source="EGW"),
    spell("Raulothim's Psychic Lance",4,ENC,[SOR,WAR,WIZ],
          desc="Unique creature name or see it: INT save or 7d6 psychic + incapacitated until end of next turn. No save if you know its name.", source="FTD"),
    spell("Summon Greater Demon",4, CON, [WAR,WIZ], concentration=True,
          desc="Summon a demon with CR 5 or lower. Demon makes CHA saves (DC = spell save) each turn or goes berserk.", source="XGE"),
    spell("Temporal Shunt",     5, TRN, [SOR,WIZ],  cast_time="Reaction",
          desc="When a creature makes an attack or casts a spell, send it to the future: vanishes until start of its next turn, losing that attack.", source="EGW"),

# ── 5th Level ─────────────────────────────────────────────────────────────────
spell("Animate Objects",   5, TRN, [ART,BAR,SOR,WIZ], concentration=True, desc="Animate up to 10 Small/Tiny or fewer Larger objects. Scales.", duration="1 min", range_="120 ft"),
spell("Antilife Shell",    5, ABJ, [DRU],              concentration=True, desc="10-ft shell: living creatures can't pass.", duration="1 hour", range_="Self (10-foot radius)"),
spell("Awaken",            5, TRN, [BAR,DRU],          desc="Touch; beast or plant gains sentience (INT 10, speaks 1 language).", cast_time="8 hours", range_="Touch"),
spell("Banishing Smite",   5, ABJ, [PAL],              concentration=True, desc="Next hit: extra 5d10 force; if 50 HP remain, banish.", cast_time="Bonus action", source="PHB", range_="Self"),
spell("Bigby's Hand",      5, EVO, [ART,WIZ],          concentration=True, desc="Arcane Hand variant (official name).", range_="120 ft"),
spell("Circle of Power",   5, ABJ, [PAL],              concentration=True, desc="30-ft aura: advantage on magic saves; no damage on save success.", duration="10 min", range_="Self (30-foot radius)"),
spell("Cloudkill",         5, CON, [SOR,WIZ],          concentration=True, desc="20-ft sphere: CON save or 5d8 poison (half on save); moves 10 ft/round. Scales.", duration="10 min", range_="120 ft"),
spell("Commune",           5, DIV, [CLE],              ritual=True, desc="Ask deity 3 yes/no questions. Truthful answers.", cast_time="1 min", range_="Self"),
spell("Commune with Nature", 5, DIV, [DRU,RAN],        ritual=True, desc="Gain knowledge of land within 3 miles (6 miles underground).", cast_time="1 min", range_="Self"),
spell("Cone of Cold",       5, EVO, [DRU,SOR,WIZ],          desc="60-ft cone: CON save or 8d8 cold. Scales.", range_="Self (60-foot cone)"),
spell("Conjure Elemental", 5, CON, [DRU,WIZ],          concentration=True, desc="Summon CR 5 elemental. Scales.", cast_time="1 min", duration="1 hour", range_="90 ft"),
spell("Contact Other Plane", 5, DIV, [WAR,WIZ],        ritual=True, desc="Commune with planar entity; 5 yes/no questions. INT save (DC 15) or incapacitated.", cast_time="1 min", range_="Self"),
spell("Contagion",         5, NEC, [CLE,DRU],          desc="Touch; CON save ×3 or contracted disease.", duration="7 days", range_="Touch"),
spell("Danse Macabre",      5, NEC, [SOR,WAR,WIZ],          concentration=True, desc="Animate 5 corpses; add spell mod to attack/damage. Scales.", source="XGE"),
spell("Dawn",              5, EVO, [CLE,WIZ],          concentration=True, desc="30-ft cylinder of sunlight; 4d10 radiant/turn entry. Scales.", source="XGE"),
spell("Destructive Wave",  5, EVO, [PAL],              desc="30-ft burst: CON save or 5d6 thunder + 5d6 radiant/necrotic; prone.", source="PHB", range_="Self (30-foot radius)"),
spell("Dispel Evil and Good", 5, ABJ, [CLE,PAL],       concentration=True, desc="Protect against specific creature types; dismiss/break enchantment.", duration="1 min", range_="Self"),
spell("Dominate Person",    5, ENC, [BAR,SOR,WAR,WIZ],     concentration=True, desc="WIS save or controlled humanoid.", duration="1 min"),
spell("Dream",             5, ILL, [BAR,WAR,WIZ],     desc="Enter target's dream with a messenger. Scales.", cast_time="1 min", duration="8 hours", range_="Special"),
spell("Enervation",        5, NEC, [SOR,WAR,WIZ],     concentration=True, desc="Channel necrotic energy: 4d8/turn (DEX save half); heals you half.", source="XGE"),
spell("Far Step",          5, CON, [SOR,WAR,WIZ],     concentration=True, desc="Teleport 60 ft as bonus action each turn.", cast_time="Bonus action", source="XGE", range_="Self"),
spell("Flame Strike",      5, EVO, [CLE],              desc="10-ft cylinder: 4d6 fire + 4d6 radiant (DEX save). Scales."),
spell("Geas",              5, ENC, [BAR,CLE,DRU,PAL,WIZ], desc="CHA save or compelled quest; 5d10 psychic if violated.", cast_time="1 min", duration="30 days"),
spell("Greater Restoration", 5, ABJ, [ART,BAR,CLE,DRU], desc="End one effect: exhaustion, charmed/petrified/cursed, ability score reduction, HP max reduction.", range_="Touch"),
spell("Hallow",            5, EVO, [CLE],              desc="Consecrate area (60-ft sphere); various protections/effects.", cast_time="24 hours", range_="Touch"),
spell("Hold Monster",      5, ENC, [BAR,SOR,WAR,WIZ], concentration=True, desc="WIS save or Paralyzed. Scales (targets).", duration="1 min", range_="90 ft"),
spell("Immolation",         5, EVO, [SOR,WIZ],              concentration=True, desc="DEX save or 8d6 fire + 4d6/turn; spreading flames.", source="EEPC", range_="90 ft"),
spell("Infernal Calling",   5, CON, [WAR,WIZ],              concentration=True, desc="Summon a devil (CR 6 or lower). Scales.", cast_time="1 min", source="XGE", range_="90 ft"),
spell("Insect Plague",     5, CON, [CLE,DRU,SOR],     concentration=True, desc="20-ft sphere of locusts: CON save or 4d10 piercing/turn. Scales.", duration="10 min", range_="300 ft"),
spell("Legend Lore",       5, DIV, [BAR,CLE,WIZ],     desc="Learn legends about person, place, or object.", cast_time="10 min", range_="Self"),
spell("Mass Cure Wounds",  5, EVO, [BAR,CLE,DRU,PAL], desc="Up to 6 creatures in 30-ft sphere heal 3d8 + spell mod. Scales."),
spell("Mislead",           5, ILL, [BAR,WIZ],          concentration=True, desc="Become invisible; create illusory double you control.", duration="1 hour", range_="Self"),
spell("Modify Memory",     5, ENC, [BAR,WIZ],          concentration=True, desc="WIS save or alter memory of last 24 hours (one event, up to 10 min).", duration="1 min", range_="30 ft"),
spell("Passwall",           5, TRN, [ART,SOR,WIZ],              desc="Create passage through wood/plaster/stone (8×5×20 ft).", duration="1 hour", range_="30 ft"),
spell("Planar Binding",    5, ABJ, [BAR,CLE,DRU,WIZ], desc="CHA save or bound to serve you. Scales (duration).", cast_time="1 hour"),
spell("Raise Dead",        5, NEC, [BAR,CLE,PAL],     desc="Restore dead creature (≤ 10 days) to life. −4 to attacks/saves/checks until 4 short/long rests.", cast_time="1 hour", range_="Touch"),
spell("Reincarnate",       5, TRN, [DRU],              desc="Restore dead creature in a random new body.", cast_time="1 hour", range_="Touch"),
spell("Scrying",           5, DIV, [BAR,CLE,DRU,PAL,WAR,WIZ], concentration=True, desc="Observe creature anywhere (WIS save modified by familiarity).", cast_time="10 min", duration="10 min", range_="Self"),
spell("Seeming",           5, ILL, [BAR,SOR,WIZ],     desc="Change appearance of any number of creatures for 8 hours.", duration="8 hours", range_="30 ft"),
spell("Steel Wind Strike", 5, CON, [RAN,WIZ],          desc="Melee attacks vs 5 creatures; 6d10 force each hit; teleport.", source="XGE", range_="30 ft"),
spell("Summon Celestial",  5, CON, [CLE,PAL],          concentration=True, desc="Summon celestial spirit. Scales.", source="TCE", range_="90 ft"),
spell("Summon Draconic Spirit", 5, CON, [DRU,SOR,WIZ], concentration=True, desc="Summon draconic spirit. Scales.", source="FTD"),
spell("Swift Quiver",      5, TRN, [RAN],              concentration=True, desc="Quiver of infinite arrows; bonus action: 2 arrow attacks.", cast_time="Bonus action", range_="Touch"),
spell("Synaptic Static",   5, ENC, [BAR,SOR,WAR,WIZ], desc="20-ft sphere: INT save or 8d6 psychic + −1d6 to attacks/ability checks/concentration 1 min.", source="XGE", range_="120 ft"),
spell("Telekinesis",       5, TRN, [SOR,WIZ],          concentration=True, desc="Move object up to 1000 lb or creature (STR contest) up to 30 ft.", duration="10 min"),
spell("Telepathic Bond",   5, DIV, [WIZ],              ritual=True, desc="Link up to 8 willing creatures telepathically.", duration="1 hour", range_="30 ft"),
spell("Teleportation Circle",5,CON,[ART,BAR,SOR,WIZ],  desc="Create teleportation circle to a permanent circle you know.", cast_time="1 min", range_="10 ft"),
spell("Tree Stride",       5, CON, [DRU,RAN,SOR],     concentration=True, desc="Step into tree; teleport to same species of tree within 500 ft.", duration="1 min", range_="Self"),
spell("Wall of Force",     5, EVO, [WIZ],              concentration=True, desc="Flat/dome/sphere of force (immune to all damage and most spells).", duration="10 min", range_="120 ft"),
spell("Wall of Light",     5, EVO, [SOR,WAR,WIZ],     concentration=True, desc="60×10 ft wall: CON save or 4d8 radiant + blinded; beam attack.", source="XGE", range_="120 ft"),
spell("Wall of Stone",     5, EVO, [DRU,SOR,WIZ],     concentration=True, desc="Create stone wall (up to 10 panels 10×10 ft, 6 in thick). Becomes permanent.", duration="10 min", range_="120 ft"),
spell("Wrath of Nature",   5, EVO, [DRU,RAN],          concentration=True, desc="Animate plants/rocks in 60-ft cube for various attacks.", source="XGE", range_="120 ft"),

    spell("Control Winds",      5, TRN, [DRU,SOR,WIZ], concentration=True,
          desc="Change the wind in a 100-ft cube: calm (fog dispersed, ranged disadvantage), gust (push creatures, fly speed halved), downdraft (flames extinguished, ranged disadvantage).", source="XGE"),
    spell("Creation",           5, ILL, [ART,BAR,SOR,WIZ],
          desc="Conjure a non-living object (up to 5-ft cube) from Shadowfell shadow material. Duration by material: vegetable matter 1 day, stone/crystal 12 hrs, metals 1 hr.", source="PHB"),
    spell("Holy Weapon",        5, EVO, [CLE,PAL],    concentration=True, cast_time="Bonus action",
          desc="Imbue a weapon with radiant power: +2d8 radiant damage on hit. Expend as a reaction to blind creature (CON save) and end spell.", source="XGE"),
    spell("Negative Energy Flood",5,NEC,[SOR,WAR,WIZ],
          desc="60 ft: WIS save or 5d12 necrotic. On kill, creature rises as zombie under your control for 1 hour.", source="XGE"),
    spell("Skill Empowerment",  5, TRN, [ART,BAR,SOR,WIZ], concentration=True,
          desc="A willing creature gains expertise (double proficiency) in one skill it is already proficient in for 1 hour.", source="XGE"),
    spell("Transmute Rock",     5, TRN, [DRU,WIZ],
          desc="Transform rock/mud up to 40-ft cube: Rock to Mud (difficult terrain, creatures inside must save or become restrained) or Mud to Rock (trap creatures, DC 20 STR to break free).", source="XGE"),

# ── 6th Level ─────────────────────────────────────────────────────────────────
spell("Arcane Gate",       6, CON, [SOR,WAR,WIZ],     concentration=True, desc="Create two portals up to 500 ft apart.", duration="10 min", range_="500 ft"),
spell("Blade Barrier",     6, EVO, [CLE],              concentration=True, desc="100-ft wall of blades: 6d10 slashing on entry (DEX save).", duration="10 min", range_="90 ft"),
spell("Bones of the Earth", 6, TRN, [DRU],             desc="Up to 6 pillars of rock (5-ft diameter) erupt; DEX save or 6d6 bludgeoning + restrained.", source="EEPC", range_="120 ft"),
spell("Chain Lightning",   6, EVO, [SOR,WIZ],          desc="Primary target + 3 secondary: 10d8 lightning (DEX save). Scales.", range_="150 ft"),
spell("Circle of Death",   6, NEC, [SOR,WAR,WIZ],     desc="60-ft sphere: CON save or 8d6 necrotic. Scales.", range_="150 ft"),
spell("Conjure Fey",       6, CON, [DRU,WAR],          concentration=True, desc="Summon CR 6 fey or beast. Scales.", cast_time="1 min", range_="90 ft"),
spell("Contingency",       6, EVO, [WIZ],              desc="Pair a 5th-level-or-lower spell to trigger on condition.", cast_time="10 min", duration="10 days", range_="Self"),
spell("Create Homunculus", 6, TRN, [WIZ],              desc="Create an intelligent homunculus familiar from your blood.", cast_time="1 hour", source="XGE", range_="Touch"),
spell("Create Undead",     6, NEC, [CLE,WAR,WIZ],     desc="Create up to 3 ghouls/ghasts/wights/mummies. Scales.", cast_time="1 min", range_="10 ft"),
spell("Disintegrate",      6, TRN, [SOR,WIZ],          desc="Ranged attack: 10d6+40 force; DEX save (half min 0). Turns to dust. Scales."),
spell("Eyebite",           6, NEC, [BAR,SOR,WAR,WIZ], concentration=True, desc="Action: curse one creature with Asleep/Panicked/Sickened (WIS save).", duration="1 min", range_="Self"),
spell("Flesh to Stone",    6, TRN, [SOR,WAR,WIZ],     concentration=True, desc="CON save ×3 or permanently petrified.", duration="1 min"),
spell("Forbiddance",       6, ABJ, [CLE],              ritual=True, desc="Prevent teleportation, planar travel in consecrated area; 5d10 dmg to intruders.", cast_time="10 min", duration="24 hours", range_="Touch"),
spell("Globe of Invulnerability", 6, ABJ, [SOR,WIZ],  concentration=True, desc="10-ft sphere: no 5th-level-or-lower spells affect interior. Scales.", duration="1 min", range_="Self (10-foot radius)"),
spell("Guards and Wards",  6, ABJ, [BAR,WIZ],          desc="Multiple magical wards for large area (up to 2500 sq ft).", cast_time="10 min", duration="24 hours", range_="Touch"),
spell("Harm",              6, NEC, [CLE],              desc="CON save or take 14d6 necrotic (HP max reduced to result)."),
spell("Heal",              6, EVO, [CLE,DRU],          desc="Restore 70 HP; end blinded/deafened/diseases. Scales."),
spell("Heroes' Feast",     6, CON, [CLE,DRU],          desc="10 creatures: immunity poison/frightened; adv WIS saves; +2d10 max HP.", cast_time="10 min", duration="Instantaneous", range_="30 ft"),
spell("Investiture of Flame", 6, TRN, [DRU,SOR,WAR,WIZ], concentration=True, desc="Cloak of fire; immune to fire; 1d10 fire to adjacent creatures.", duration="10 min", source="EEPC", range_="Self"),
spell("Investiture of Ice", 6, TRN, [DRU,SOR,WAR,WIZ], concentration=True, desc="Cold/ice cloak; walk on ice; immunity cold; 4d6 cold burst.", duration="10 min", source="EEPC", range_="Self"),
spell("Investiture of Stone", 6, TRN, [DRU,SOR,WAR,WIZ], concentration=True, desc="Stone skin; move through stone; immunity B/P/S from nonmagical.", duration="10 min", source="EEPC", range_="Self"),
spell("Investiture of Wind", 6, TRN, [DRU,SOR,WAR,WIZ], concentration=True, desc="Wind cloak; fly 60 ft; redirect ranged attacks.", duration="10 min", source="EEPC", range_="Self"),
spell("Magic Jar",         6, NEC, [WIZ], desc="Project soul into container; possess creatures.", duration="Until dispelled", range_="Self"),
spell("Mass Suggestion",   6, ENC, [BAR,SOR,WAR,WIZ], desc="WIS save or up to 12 creatures follow reasonable suggestion.", duration="24 hours"),
spell("Move Earth",        6, TRN, [DRU,SOR,WIZ],     concentration=True, desc="Slowly reshape terrain in 40-ft cube.", duration="2 hours", range_="120 ft"),
spell("Otiluke's Freezing Sphere", 6, EVO, [WIZ],      desc="60-ft sphere: CON save or 10d6 cold + restrained; detonates or is saved.", range_="300 ft"),
spell("Primordial Ward",   6, ABJ, [DRU],              concentration=True, desc="Resistance to acid/cold/fire/lightning/thunder; immunity to one.", cast_time="1 action", source="EEPC", range_="Self"),
spell("Programmed Illusion", 6, ILL, [BAR,WIZ],        desc="Illusion (up to 30-ft cube) triggers on specific condition (up to 5-min performance).", duration="Until dispelled", range_="120 ft"),
spell("Scatter",           6, CON, [SOR,WAR,WIZ],     desc="Up to 5 creatures: WIS save or teleport up to 120 ft away.", source="XGE", range_="30 ft"),
spell("Soul Cage",         6, NEC, [WAR,WIZ],          desc="Reaction: trap recently dead creature's soul for spells and information.", cast_time="Reaction", source="XGE"),
spell("Sunbeam",           6, EVO, [DRU,SOR,WIZ],     concentration=True, desc="60-ft line: CON save or 6d8 radiant + blinded; reusable each turn.", duration="1 min", range_="Self (60-foot line)"),
spell("Tasha's Otherworldly Guise", 6, TRN, [SOR,WAR,WIZ], concentration=True, desc="Transform: resist fire/poison (lower planes) or radiant/necrotic (upper); fly 40 ft; +2 AC; weapon attacks.", source="TCE", range_="Self"),
spell("True Seeing",       6, DIV, [BAR,CLE,SOR,WAR,WIZ], desc="Truesight 120 ft; see hidden doors; see true form of illusions/shapeshifters.", duration="1 hour", range_="Touch"),
spell("Wall of Ice",       6, EVO, [WIZ],              concentration=True, desc="Create ice wall (up to ten 10-ft-square panels, or a hemisphere/sphere up to 10-ft radius); DEX save or 10d6 cold on break.", duration="10 min", range_="120 ft"),
spell("Wall of Thorns",    6, CON, [DRU],              concentration=True, desc="60-ft thorny cylinder; 7d8 piercing to enter/traverse (DEX save half).", duration="10 min", range_="120 ft"),
spell("Wind Walk",         6, TRN, [DRU],              desc="Up to 10 creatures become gaseous; speed 300 ft; fly.", cast_time="1 min", duration="8 hours", range_="30 ft"),
spell("Word of Recall",    6, CON, [CLE],              desc="Instantly return up to 5 creatures to designated sanctuary.", cast_time="1 action", range_="5 ft"),

    spell("Drawmij's Instant Summons", 6, CON, [WIZ], ritual=True,
          desc="Touch a Tiny object. Speak its name to summon it to your hand from anywhere on the same plane. Others must succeed on a CHA save to hold onto it.", source="PHB"),
    spell("Druid Grove",            6, ABJ, [DRU],
          desc="Enchant a natural area up to 90-ft cube for 1 day. Designate safe creatures; others suffer effects: alarm, difficult terrain, darkness, thorns, poison, trees animate.", source="XGE"),
    spell("Find the Path",          6, DIV, [BAR,CLE,DRU], concentration=True,
          desc="Know the shortest path to a named location on the same plane. You have advantage on checks to navigate there.", source="PHB"),
    spell("Mental Prison",          6, ILL, [SOR,WAR,WIZ], concentration=True,
          desc="One creature: INT save or trapped in an illusory cage. 5d10 psychic if it tries to escape. Psychic damage to any who touch the target.", source="XGE"),
    spell("Otto's Irresistible Dance",6,ENC,[BAR],   concentration=True,
          desc="One creature: WIS save or spend all movement dancing, can't take reactions, -4 to AC and DEX saves. Can re-save at end of each turn.", source="PHB"),
    spell("Planar Ally",            6, CON, [CLE],
          desc="Request aid from an extraplanar being (celestial, elemental, or fiend). It appears and you must negotiate payment. It serves for 24 hours.", source="PHB"),
    spell("Transport via Plants",   6, CON, [DRU],
          desc="Step into a Large or larger plant and emerge from any other plant of the same kind anywhere on the same plane.", source="PHB"),

# ── 7th Level ─────────────────────────────────────────────────────────────────
spell("Conjure Celestial", 7, CON, [CLE],              concentration=True, desc="Summon CR 4 celestial.", cast_time="1 min", duration="1 hour", range_="90 ft"),
spell("Crown of Stars",    7, EVO, [SOR,WAR,WIZ],     desc="7 motes orbit you; launch for 4d12 radiant ranged attacks (bonus action).", cast_time="1 action", duration="1 hour", source="XGE", range_="Self"),
spell("Delayed Blast Fireball", 7, EVO, [SOR,WIZ],    concentration=True, desc="20-ft sphere growing fireball (12d6+; delay up to 1 min). Scales.", duration="1 min", range_="150 ft"),
spell("Divine Word",       7, EVO, [CLE],              desc="Celestial utterance: kills <20 HP; stuns/blinds/deafens others by HP threshold.", cast_time="Bonus action", range_="30 ft"),
spell("Etherealness",      7, TRN, [BAR,CLE,SOR,WAR,WIZ], desc="Enter Ethereal Plane. Scales (targets).", duration="8 hours", range_="Self"),
spell("Finger of Death",   7, NEC, [SOR,WAR,WIZ],     desc="CON save or 7d8+30 necrotic; rises as zombie if killed."),
spell("Fire Storm",        7, EVO, [CLE,DRU,SOR],     desc="Ten 10-ft cubes: DEX save or 7d10 fire.", range_="150 ft"),
spell("Forcecage",         7, EVO, [BAR,WAR,WIZ],     desc="Cube of force (up to 20 ft). No teleport/planar travel.", duration="1 hour", range_="100 ft"),
spell("Mirage Arcane",     7, ILL, [BAR,DRU,WIZ],     desc="Transform terrain appearance of up to 1 mile square.", duration="10 days", range_="Sight"),
spell("Mordenkainen's Magnificent Mansion", 7, CON, [BAR,WIZ], desc="Extradimensional mansion for up to 100 creatures.", cast_time="1 min", duration="24 hours", range_="300 ft"),
spell("Mordenkainen's Sword", 7, EVO, [BAR,WIZ],       concentration=True, desc="Summoned sword (bonus action attack: 3d10 force). Scales.", duration="1 min"),
spell("Plane Shift",       7, CON, [CLE,DRU,SOR,WAR,WIZ], desc="Transport 8 creatures to another plane; or banish one (CHA save).", range_="Touch"),
spell("Prismatic Spray",   7, EVO, [SOR,WIZ],          desc="DEX save; random colour beam (1d8) with varied effects.", range_="Self (60-foot cone)"),
spell("Project Image",     7, ILL, [BAR,WIZ],          concentration=True, desc="Illusion of yourself up to 500 miles away; you see/hear through it.", duration="1 day", range_="500 miles"),
spell("Regenerate",        7, TRN, [BAR,CLE,DRU],     desc="Touch: heal 4d8+15 + 1 HP/min; regrow lost limbs.", duration="1 hour", range_="Touch"),
spell("Resurrection",      7, NEC, [BAR,CLE],          desc="Restore creature dead ≤ 100 years to life. Penalty worn off in 4 days.", cast_time="1 hour", range_="Touch"),
spell("Reverse Gravity",   7, TRN, [DRU,SOR,WIZ],     concentration=True, desc="Objects/creatures in 50-ft cylinder fall upward.", duration="1 min", range_="100 ft"),
spell("Sequester",         7, TRN, [WIZ],              desc="Hide creature/object from detection; optionally hibernate.", duration="Until dispelled", range_="Touch"),
spell("Simulacrum",        7, ILL, [WIZ],              desc="Create duplicate from snow/ice at half HP; no spell slots.", cast_time="12 hours", range_="Touch"),
spell("Symbol",            7, ABJ, [BAR,CLE,DRU,WIZ], desc="Inscribe rune (up to 10-ft diameter on a surface); triggers on condition. Various effects.", cast_time="1 min", range_="Touch"),
spell("Temple of the Gods", 7, CON, [CLE],             desc="Create protective temple. Scales.", cast_time="1 hour", source="XGE", range_="120 ft"),
spell("Teleport",          7, CON, [BAR,SOR,WIZ],     desc="Transport yourself + up to 8 willing creatures anywhere on same plane.", range_="10 ft"),
spell("Whirlwind",         7, EVO, [DRU,SOR,WIZ],     concentration=True, desc="10-ft whirlwind: STR save or 2d6+flying 10d6 fall.", duration="1 min", source="EEPC", range_="300 ft"),

    spell("Draconic Transformation",7, TRN, [SOR,WIZ], concentration=True, cast_time="Bonus action",
          desc="Grow draconic features: 60-ft blindsight, spectral wings (fly 60), breath weapon (60-ft cone, 6d6 of your dragon type, CON save for half).", source="FTD"),
    spell("Dream of the Blue Veil",7, CON, [SOR,WAR,WIZ],
          desc="Up to 8 willing creatures travel to another world/setting. They wake at a random location there. Lasts until the caster dismisses it.", source="TCE"),
    spell("Power Word Pain",       7, ENC, [SOR,WAR,WIZ],
          desc="One creature ≤100 HP: CON save or wracked with pain; speed halved, -4 to attack rolls and saves, can't concentrate. Can re-save at end of each turn.", source="XGE"),
    spell("Tether Essence",        7, NEC, [SOR,WAR,WIZ], concentration=True,
          desc="Two creatures: damage dealt to one is also dealt to the other. Each creature also takes 1d12 force when the tether is severed. CON save to resist.", source="EGW"),

# ── 8th Level ─────────────────────────────────────────────────────────────────
spell("Abi-Dalzim's Horrid Wilting", 8, NEC, [SOR,WIZ], desc="30-ft cube: CON save or 12d8 necrotic. Water/plants auto-fail.", source="EEPC", range_="150 ft"),
spell("Antimagic Field",   8, ABJ, [CLE,WIZ],          concentration=True, desc="10-ft sphere: suppresses spells, magic items, magical effects.", duration="1 hour", range_="Self (10-foot radius)"),
spell("Antipathy/Sympathy", 8, ENC, [DRU,WIZ],         desc="Object/area (up to 200-ft cube) repels or attracts a creature type/specific creature (WIS save to resist).", duration="10 days"),
spell("Clone",             8, NEC, [WIZ],              desc="Duplicate grows; soul transfers on death.", cast_time="1 hour", range_="Touch"),
spell("Control Weather",   8, TRN, [CLE,DRU,WIZ],     concentration=True, desc="Control precipitation/temperature/wind in 5-mile radius.", cast_time="10 min", duration="8 hours", range_="Self (5-mile radius)"),
spell("Dark Star",         8, EVO, [WIZ],              concentration=True, desc="40-ft sphere gravitational collapse; void kills magic.", source="EGW", range_="150 ft"),
spell("Demiplane",         8, CON, [WAR,WIZ],          desc="Door to extradimensional room (30-ft cube).", duration="1 hour"),
spell("Dominate Monster",  8, ENC, [BAR,SOR,WAR,WIZ], concentration=True, desc="WIS save or any creature obeys commands.", duration="1 hour"),
spell("Earthquake",        8, EVO, [CLE,DRU,SOR],     concentration=True, desc="100-ft radius: difficult terrain; structures damaged; DEX or prone.", duration="1 min", range_="500 ft"),
spell("Feeblemind",        8, ENC, [BAR,DRU,WAR,WIZ], desc="INT save or INT/CHA drop to 1; can't cast or understand language.", duration="30 days", range_="150 ft"),
spell("Glibness",          8, TRN, [BAR,WAR],          desc="Choose any result for CHA checks; detect thoughts say whatever.", duration="1 hour", range_="Self"),
spell("Holy Aura",         8, ABJ, [CLE],              concentration=True, desc="30-ft aura: adv all saves, adv. attacks vs undead/fiends; blinding on hit.", duration="1 min", range_="Self"),
spell("Illusory Dragon",   8, ILL, [WIZ],              concentration=True, desc="Huge illusory dragon; enemies who see it WIS save or frightened 1 min. Breath: 60-ft cone, INT save or 7d6 (chosen energy), half on save. Examining it (action) vs your spell save DC reveals the illusion.", source="XGE", range_="120 ft"),
spell("Incendiary Cloud",  8, CON, [SOR,WIZ],          concentration=True, desc="20-ft sphere of smoke; 10d8 fire (DEX save half); moves 10 ft/round.", duration="1 min", range_="150 ft"),
spell("Maddening Darkness", 8, EVO, [WAR,WIZ],         concentration=True, desc="60-ft sphere of magical dark: WIS save or 8d8 psychic.", duration="10 min", source="XGE", range_="150 ft"),
spell("Maze",              8, CON, [WIZ],              concentration=True, desc="Trap creature in labyrinthine demiplane. INT DC 20 to escape.", duration="10 min"),
spell("Mind Blank",        8, ABJ, [BAR,WIZ],          desc="Immunity to psychic damage, charm/frighten, mental detection/influence.", duration="24 hours", range_="Touch"),
spell("Power Word Stun",   8, ENC, [BAR,SOR,WAR,WIZ], desc="No save. If ≤150 HP: stunned until CON save passed."),
spell("Sunburst",          8, EVO, [DRU,SOR,WIZ],     desc="60-ft sphere: CON save or 12d6 radiant + blinded 1 min.", range_="150 ft"),
spell("Telepathy",         8, EVO, [WIZ],              desc="Unlimited range telepathic communication with willing creature.", duration="24 hours", range_="Unlimited"),
spell("Tsunami",           8, CON, [DRU],              concentration=True, desc="300-ft tall wave: STR save or 6d10 + 2d10/round; drowning.", duration="6 rounds", range_="Sight"),

    spell("Animal Shapes",         8, TRN, [DRU],      concentration=True,
          desc="Transform any number of willing creatures into Beasts with CR 4 or lower. They retain Intelligence but gain Beast statistics. 24 hours.", source="PHB"),
    spell("Mighty Fortress",       8, CON, [BAR,WIZ],
          desc="Massive castle grows from the ground: up to 120-ft square and 30-ft high, with towers. Equipped with arrow slits, portcullis, and 100 soldiers. Lasts 7 days.", source="XGE"),

# ── 9th Level ─────────────────────────────────────────────────────────────────
spell("Astral Projection", 9, NEC, [CLE,WAR,WIZ],     desc="Project into Astral Plane (up to 9 willing creatures).", cast_time="1 hour", range_="10 ft"),
spell("Blade of Disaster", 9, CON, [SOR,WAR,WIZ],     concentration=True, desc="Create two-bladed weapon; bonus action attack: 4d12 force.", cast_time="Bonus action", source="TCE"),
spell("Foresight",         9, DIV, [BAR,DRU,WAR,WIZ], desc="Touch; target has adv everything, enemies disadv vs target.", duration="8 hours", range_="Touch"),
spell("Gate",              9, CON, [CLE,SOR,WIZ],     concentration=True, desc="Open portal to another plane; call a named creature.", duration="1 min"),
spell("Imprisonment",      9, ABJ, [WAR,WIZ],          desc="WIS save or trapped (Burial/Chaining/Hedged Prison/Minimus Containment/Slumber).", cast_time="1 min", range_="30 ft"),
spell("Invulnerability",   9, ABJ, [WIZ],              concentration=True, desc="Immunity to all damage types.", duration="10 min", source="XGE", range_="Self"),
spell("Mass Heal",         9, EVO, [CLE],              desc="Up to 700 HP distributed among creatures in 60 ft; ends disease/blindness/deafness."),
spell("Mass Polymorph",    9, TRN, [BAR,SOR,WIZ],     concentration=True, desc="Up to 10 creatures: WIS save or transformed to beasts.", duration="1 hour", source="XGE", range_="120 ft"),
spell("Meteor Swarm",      9, EVO, [SOR,WIZ],          desc="4 spheres (40-ft radius each): DEX save or 20d6 fire + 20d6 bludgeoning.", range_="1 mile"),
spell("Power Word Heal",    9, EVO, [BAR,CLE],              desc="Touch; fully heal creature. If stunned/frightened/paralyzed/poisoned: ends.", cast_time="1 action", range_="Touch"),
spell("Power Word Kill",   9, ENC, [BAR,SOR,WAR,WIZ], desc="No save. If ≤100 HP: die instantly."),
spell("Prismatic Wall",    9, ABJ, [WIZ],              desc="Wall of layered colour effects; 7 layers each with unique effects.", duration="10 min"),
spell("Psychic Scream",    9, ENC, [BAR,SOR,WAR,WIZ], desc="INT save or 14d6 psychic + stunned. No save if no INT score.", source="XGE", range_="90 ft"),
spell("Ravenous Void",     9, EVO, [WIZ],              concentration=True, desc="20-ft sphere of gravitational annihilation; objects within 100 ft pulled toward it each turn.", source="EGW", range_="1000 ft"),
spell("Shapechange",       9, TRN, [DRU,WIZ],          concentration=True, desc="Transform into any creature with CR ≤ level.", duration="1 hour", range_="Self"),
spell("Storm of Vengeance", 9, CON, [DRU],             concentration=True, desc="360-ft storm cloud: acid/lightning/thunder/cold/hail rounds.", duration="1 min", range_="Sight"),
spell("Time Ravage",       9, NEC, [WIZ],              desc="CON save or 10d12 necrotic + rapid aging to Exhaustion 5.", source="EGW", range_="90 ft"),
spell("Time Stop",         9, TRN, [SOR,WIZ],          desc="Take 1d4+1 turns in a row before time resumes.", range_="Self"),
spell("True Polymorph",    9, TRN, [BAR,WAR,WIZ],     concentration=True, desc="Transform creature/object into anything of same category. Permanent after 1 hr.", duration="1 hour", range_="30 ft"),
spell("True Resurrection", 9, NEC, [CLE,DRU],          desc="Restore creature dead ≤ 200 years in perfect body. No component cost.", cast_time="1 hour", range_="Touch"),
spell("Weird",             9, ILL, [WIZ],              concentration=True, desc="30-ft sphere: WIS save or Frightened + 4d10 psychic/turn.", duration="1 min", range_="120 ft"),
spell("Wish",              9, CON, [SOR,WIZ],          desc="Duplicate any spell ≤8th level, or attempt to alter reality. Stress risk on non-duplication use.", range_="Self"),

# ── Spells the reference has that the catalog didn't (docs/reference/spells-sublist.md;
#    class lists from it, or from the spell's own book where it gives none) ──
spell("Frost Fingers",     1, EVO, [WIZ],               desc="15-ft cone: CON save or 2d8 cold, half on a save; unworn nonmagical liquids in it freeze. Higher levels: +1d8 per slot level above 1st.", source="IDRotF", range_="Self (15-foot cone)"),
spell("Air Bubble",        2, CON, [ART,DRU,RAN,SOR,WIZ], desc="A globe of fresh air around the head of a willing creature you can see: it can breathe for the duration. Higher levels: two more globes per slot level above 2nd.", source="AAG", duration="24 hours", components="S"),
spell("Cordon of Arrows",  2, TRN, [RAN],               desc="Plant four arrows or bolts: a creature other than you (and those you exclude) that comes within 30 ft of them for the first time on a turn or ends its turn there is struck by one, DEX save or 1d6 piercing. Ends when none are left. Higher levels: two more pieces per slot level above 2nd.", duration="8 hours", range_="5 ft", components="V, S, M (four or more arrows or bolts)"),
spell("Healing Spirit",    2, CON, [DRU,RAN],           concentration=True, desc="A spirit in a 5-ft cube: a creature you can see that moves into it for the first time on a turn or starts its turn there can regain 1d6 HP (no action). It heals 1 + your spellcasting modifier times (at least twice); a bonus action moves it 30 ft. Higher levels: +1d6 per slot level above 2nd.", source="XGE", cast_time="1 bonus action", duration="Concentration, up to 1 minute"),
spell("Immovable Object",  2, TRN, [ART,WIZ],           desc="Fix an object of 10 lb or less in place (you and those you designate can move it; a password suppresses it for 1 minute). In the air it holds up to 4,000 lb; otherwise a STR check against your spell save DC moves it 10 ft. Higher levels: a stronger hold for longer at 4th level and up.", source="EGW", duration="1 hour", range_="Touch", components="V, S, M (gold dust worth at least 25 gp, which the spell consumes)"),
spell("Rime's Binding Ice", 2, EVO, [SOR,WIZ],          desc="30-ft cone: CON save or 3d8 cold and speed 0 for 1 minute (until it or a creature within reach uses an action to break the ice); half damage and no ice on a save. Higher levels: +1d8 per slot level above 2nd.", source="FTD", range_="Self (30-foot cone)", components="S, M (a vial of meltwater)"),
spell("Spray of Cards",    2, CON, [BAR,SOR,WAR,WIZ],   desc="15-ft cone: DEX save or 2d10 force and blinded until the end of its next turn; half damage only on a save. Higher levels: +1d10 per slot level above 2nd.", source="BOMT", range_="Self (15-foot cone)", components="V, S, M (a deck of cards)"),
spell("Warp Sense",        2, DIV, [SOR,WAR,WIZ],       concentration=True, desc="Sense portals, even inactive ones, within 30 ft; an action and a DC 15 spellcasting check on one reveals its destination plane and portal key (a failure: not that portal again this casting).", source="SatO", duration="Concentration, up to 1 minute", range_="Self", components="V, S, M (a razorvine leaf)"),
spell("Antagonize",        3, ENC, [BAR,SOR,WAR,WIZ],   desc="One creature: WIS save or 4d4 psychic and it must use its reaction to make a melee attack against another creature of your choice you can see (if it can't, disadvantage on its next attack roll before your next turn); half damage only on a save. Higher levels: +1d4 per slot level above 3rd.", source="BOMT", range_="30 ft", components="V, S, M (a playing card depicting a rogue)"),
spell("Ashardalon's Stride", 3, TRN, [ART,RAN,SOR,WIZ], concentration=True, desc="Your speed increases by 20 ft and moving doesn't provoke opportunity attacks; a creature or unworn object you move within 5 ft of takes 1d6 fire, once a turn each. Higher levels: +5 ft speed and +1d6 fire per slot level above 3rd.", source="FTD", cast_time="1 bonus action", duration="Concentration, up to 1 minute", range_="Self"),
spell("Blinding Smite",    3, EVO, [PAL],               concentration=True, desc="Your next melee weapon hit deals an extra 3d8 radiant, and the target makes a CON save or is blinded until the spell ends (it repeats the save at the end of each of its turns).", cast_time="1 bonus action", duration="Concentration, up to 1 minute", range_="Self", components="V"),
spell("Incite Greed",      3, ENC, [CLE,WAR,WIZ],       concentration=True, desc="Any number of creatures within range that can see you: WIS save or charmed, using their movement only to approach you safely and staring at the gem once within 5 ft; harming them ends it, and each repeats the save at the end of its turns.", source="AI", duration="Concentration, up to 1 minute", range_="30 ft", components="V, S, M (a gem worth at least 50 gp)"),
spell("Motivational Speech", 3, ENC, [BAR,CLE],         desc="Up to five creatures that can hear you: 5 temporary HP and advantage on WIS saves; when one is hit by an attack, it has advantage on its next attack roll. Ends for a creature once its temporary HP are gone. Higher levels: +5 temporary HP per slot level above 3rd.", source="AI", cast_time="1 minute", duration="1 hour", components="V"),
spell("Gate Seal",         4, ABJ, [SOR,WAR,WIZ],       desc="In a 30-ft cube you can see, portals close and can't open, and planar travel into or out of it (gate, plane shift) fails.", source="SatO", cast_time="1 minute", duration="24 hours", components="V, S, M (a broken portal key, which the spell consumes)"),
spell("Guardian of Nature", 4, TRN, [DRU,RAN],          concentration=True, desc="Become a guardian. Primal Beast: +10 ft speed, darkvision 120 ft, advantage on STR attack rolls, melee weapon attacks deal +1d6 force. Great Tree: 10 temporary HP, advantage on CON saves and on DEX and WIS attack rolls, the ground within 15 ft is difficult terrain for enemies.", source="XGE", cast_time="1 bonus action", duration="Concentration, up to 1 minute", range_="Self", components="V"),
spell("Mordenkainen's Faithful Hound", 4, CON, [ART,WIZ], desc="An invisible phantom watchdog that barks when a Small or larger creature comes within 30 ft without the password; it sees invisible creatures and ignores illusions. At the start of each of your turns it bites a hostile creature within 5 ft: your spellcasting modifier + proficiency bonus to hit, 4d8 piercing.", duration="8 hours", range_="30 ft", components="V, S, M (a tiny silver whistle, a piece of bone, and a thread)"),
spell("Mordenkainen's Private Sanctum", 4, ABJ, [ART,WIZ], desc="Secure a cube 5 to 100 ft on a side, with any of: sound can't pass, vision through it blocked, no divination sensors, creatures inside can't be targeted by divination, no teleporting in or out, no planar travel. Cast on the same spot daily for a year to make it permanent.", cast_time="10 minutes", duration="24 hours", range_="120 ft", components="V, S, M (a thin sheet of lead, a piece of opaque glass, a wad of cotton or cloth, and powdered chrysolite)"),
spell("Conjure Volley",    5, CON, [RAN],               desc="Fire ammunition or throw a weapon at a point: each creature in a 40-ft-radius, 20-ft-high cylinder makes a DEX save, 8d8 damage of the weapon's type, half on a save.", range_="150 ft", components="V, S, M (one piece of ammunition or one thrown weapon)"),
spell("Create Spelljamming Helm", 5, TRN, [ART,WIZ],    desc="Touch an unoccupied Large or smaller chair: it becomes a spelljamming helm.", source="AAG", range_="Touch", components="V, S, M (a crystal rod worth at least 5,000 gp, which the spell consumes)"),
spell("Fizban's Platinum Shield", 6, ABJ, [SOR,WIZ],    concentration=True, desc="A field of silvery light around a creature of your choice (you can choose yourself): half cover, resistance to acid, cold, fire, lightning and poison, and Evasion. A bonus action moves it to another creature within 60 ft of the field.", source="FTD", cast_time="1 bonus action", duration="Concentration, up to 1 minute", components="V, S, M (a platinum-plated dragon scale, worth at least 500 gp)"),
spell("Gravity Fissure",   6, EVO, [WIZ],               desc="A 100-ft line, 5 ft wide: CON save, 8d8 force, half on a save; each creature within 10 ft of the line makes a CON save or takes 8d8 force and is pulled into it. Higher levels: +1d8 per slot level above 6th.", source="EGW", range_="Self (100-foot line)", components="V, S, M (a fistful of iron filings)"),
spell("Summon Fiend",      6, CON, [WAR,WIZ],           concentration=True, desc="Call a fiendish spirit (Demon, Devil or Yugoloth) that uses the Fiendish Spirit stat block; it acts right after you and obeys your commands. Higher levels: use the slot level in its stat block.", source="TCE", duration="Concentration, up to 1 hour", range_="90 ft", components="V, S, M (humanoid blood inside a ruby vial worth at least 600 gp)"),
spell("Tenser's Transformation", 6, TRN, [WIZ],         concentration=True, desc="You can't cast spells, and gain: 50 temporary HP, advantage on simple and martial weapon attack rolls, +2d12 force on weapon hits, proficiency with all armor, shields and simple and martial weapons, proficiency in STR and CON saves, and two attacks with the Attack action (unless you already have Extra Attack). When it ends: DC 15 CON save or one level of exhaustion.", source="XGE", duration="Concentration, up to 10 minutes", range_="Self", components="V, S, M (a few hairs from a bull)"),
spell("Create Magen",      7, TRN, [WIZ],               desc="Over an hour, turn a life-sized doll into a magen of your choice that obeys you; your hit point maximum drops by its challenge rating (minimum 1) until a wish undoes it.", source="IDRotF", cast_time="1 hour", range_="Touch", components="V, S, M (a vial of quicksilver worth 500 gp and a life-sized human doll, both consumed, and an intricate crystal rod worth at least 1,500 gp)"),
spell("Reality Break",     8, CON, [WIZ],               concentration=True, desc="One creature: WIS save or it can't take reactions, and at the start of each of its turns rolls a d10: 1-2, 6d12 psychic and stunned until the end of the turn; 3-5, DEX save or 8d12 force (half on a save); 6-8, teleported up to 30 ft, 10d12 force and prone; 9-10, 10d12 cold and blinded until the end of the turn. It repeats the save at the end of each of its turns.", source="EGW", duration="Concentration, up to 1 minute", components="V, S, M (a crystal prism)"),
]

# Build lookup structures
SPELL_DICT = {s["name"]: s for s in ALL_SPELLS}

# Unearthed Arcana playtest spells the catalogue used to carry. They're
# gone; a save that still lists one drops it when it loads (save_load.py).
REMOVED_SPELLS = frozenset({
    "Auditory Hallucination", "Guiding Hand", "Healing Elixir", "Id Insinuation", "On/Off", "Puppet",
    "Sense Emotion", "Sudden Awakening", "Unearthly Chorus", "Virtue", "Wild Cunning",
})
SPELL_NAMES = [s["name"] for s in ALL_SPELLS]

# Class-to-spell map
CLASS_SPELLS = {c: [] for c in [ART,BAR,CLE,DRU,PAL,RAN,SOR,WAR,WIZ]}
for s in ALL_SPELLS:
    for c in s["classes"]:
        if c in CLASS_SPELLS:
            CLASS_SPELLS[c].append(s)

# Level-to-spell map
SPELLS_BY_LEVEL = {}
for s in ALL_SPELLS:
    SPELLS_BY_LEVEL.setdefault(s["level"], []).append(s)

# Other names a spell goes by: the full name the books use for one the
# catalog keeps under its SRD name, and the SRD name of one it keeps under
# the full name (older saves stored those)
SPELL_ALIASES = {
    "Otiluke's Resilient Sphere": "Resilient Sphere", "Rary's Telepathic Bond": "Telepathic Bond",
    "Tiny Hut": "Leomund's Tiny Hut", "Arcane Hand": "Bigby's Hand",
    "Irresistible Dance": "Otto's Irresistible Dance", "Acid Arrow": "Melf's Acid Arrow",
}


def get_spell(name): return SPELL_DICT.get(name) or SPELL_DICT.get(SPELL_ALIASES.get(name, ""))
def spells_for_class(cls_name): return CLASS_SPELLS.get(cls_name, [])
def spells_for_class_at_level(cls_name, spell_level):
    return [s for s in CLASS_SPELLS.get(cls_name,[]) if s["level"] == spell_level]

# ═══════════════════════════════════════════════════════════════════════════
# Bonus/racial spell grants — merged in from the former bonus_spell_lists.py
#
# Bonus spell lists — spells granted by a subclass (Cleric domain, Paladin
# oath, Warlock patron, Druid circle, etc.) that are always prepared/known
# once the character reaches the listed level, and do not count against
# the normal number of prepared/known spells for the class.
#
# Structure: {(class, subclass): {level: [spell names]}}
# A character gets every entry whose level is <= their current level in
# that class.
#
# Coverage is intentionally partial rather than filled in from memory —
# each entry here has been checked against real source text for that
# specific subclass. Subclasses not yet listed can be added the same way
# once their spell list is verified against a source.
# ═══════════════════════════════════════════════════════════════════════════

BONUS_SPELLS = {
    # ── Barbarian Subclasses ─────────────────────────────────────────────
    ("Barbarian", "Path of the Totem Warrior"): {
        3: ["Beast Sense", "Speak with Animals"],   # Spirit Seeker — ritual only
        10: ["Commune with Nature"],                 # Spirit Walker — ritual only
    },
    ("Barbarian", "Path of the Ancestral Guardian"): {
        10: ["Augury", "Clairvoyance"],  # Consult the Spirits (a 10th-level feature) — 1/SR or LR, no slot/components
    },
    # ── Artificer Subclasses ─────────────────────────────────────────────
    ("Artificer", "Alchemist"): {
        3: ["Healing Word", "Ray of Sickness"],
        5: ["Flaming Sphere", "Melf's Acid Arrow"],
        9: ["Gaseous Form", "Mass Healing Word"],
        13: ["Blight", "Death Ward"],
        17: ["Cloudkill", "Raise Dead"],
    },
    ("Artificer", "Armorer"): {
        3: ["Magic Missile", "Thunderwave"],
        5: ["Mirror Image", "Shatter"],
        9: ["Hypnotic Pattern", "Lightning Bolt"],
        13: ["Fire Shield", "Greater Invisibility"],
        17: ["Passwall", "Wall of Force"],
    },
    ("Artificer", "Artillerist"): {
        3: ["Shield", "Thunderwave"],
        5: ["Scorching Ray", "Shatter"],
        9: ["Fireball", "Wind Wall"],
        13: ["Ice Storm", "Wall of Fire"],
        17: ["Cone of Cold", "Wall of Force"],
    },
    ("Artificer", "Battle Smith"): {
        3: ["Heroism", "Shield"],
        5: ["Branding Smite", "Warding Bond"],
        9: ["Aura of Vitality", "Conjure Barrage"],
        13: ["Aura of Purity", "Fire Shield"],
        17: ["Banishing Smite", "Mass Cure Wounds"],
    },
    # ── Warlock Subclasses ───────────────────────────────────────────────
    # The Celestial/The Undying below combine two distinct 1st-level
    # features: their Bonus Cantrip/Among the Dead grant and their own
    # Expanded Spell List. Char-level-as-spell-level-proxy keying
    # (1/3/5/7/9) is used for every Warlock patron below, matching the
    # level a Warlock actually gains access to that spell slot level.
    ("Warlock", "The Celestial"): {
        1: ["Light", "Sacred Flame", "Cure Wounds", "Guiding Bolt"],
        3: ["Flaming Sphere", "Lesser Restoration"],
        5: ["Daylight", "Revivify"],
        7: ["Guardian of Faith", "Wall of Fire"],
        9: ["Flame Strike", "Greater Restoration"],
    },
    ("Warlock", "The Undying"): {
        1: ["Spare the Dying", "False Life", "Ray of Sickness"],
        3: ["Blindness/Deafness", "Silence"],
        5: ["Feign Death", "Speak with Dead"],
        7: ["Aura of Life", "Death Ward"],
        9: ["Contagion", "Legend Lore"],
    },
    ("Warlock", "The Archfey"): {
        1: ["Faerie Fire", "Sleep"],
        3: ["Calm Emotions", "Phantasmal Force"],
        5: ["Blink", "Plant Growth"],
        7: ["Dominate Beast", "Greater Invisibility"],
        9: ["Dominate Person", "Seeming"],
    },
    ("Warlock", "The Fathomless"): {
        1: ["Create or Destroy Water", "Thunderwave"],
        3: ["Gust of Wind", "Silence"],
        5: ["Lightning Bolt", "Sleet Storm"],
        7: ["Control Water", "Summon Elemental"],
        9: ["Bigby's Hand", "Cone of Cold"],
    },
    ("Warlock", "The Great Old One"): {
        1: ["Dissonant Whispers", "Tasha's Hideous Laughter"],
        3: ["Detect Thoughts", "Phantasmal Force"],
        5: ["Clairvoyance", "Sending"],
        7: ["Dominate Beast", "Evard's Black Tentacles"],
        9: ["Dominate Person", "Telekinesis"],
    },
    ("Warlock", "The Undead"): {
        1: ["Bane", "False Life"],
        3: ["Blindness/Deafness", "Phantasmal Force"],
        5: ["Phantom Steed", "Speak with Dead"],
        7: ["Death Ward", "Greater Invisibility"],
        9: ["Antilife Shell", "Cloudkill"],
    },
    # The Genie's Expanded Spells table has a kind-independent "Genie
    # Spells" column (always granted) plus one of 4 kind-specific columns
    # depending on the genie_kind choice (core/choices.py's chooser,
    # stored in _choices["genie_kind"]) -- that choice-dependent half is
    # read back in get_bonus_spells() below, same pattern as Death
    # Domain's Reaper cantrip. This entry is only the kind-independent
    # half. (The table's extra "9th spell level: wish" row is a 6th tier
    # beyond the normal 1st-5th-spell-level pattern every other patron
    # uses, and is not modeled separately here; Wish remains reachable
    # for a high-level Genie warlock through Mystic Arcanum like any
    # other Warlock.)
    ("Warlock", "The Genie"): {
        1: ["Detect Evil and Good"],
        3: ["Phantasmal Force"],
        5: ["Create Food and Water"],
        7: ["Phantasmal Killer"],
        9: ["Creation"],
    },
    # ── Bard Subclasses ──────────────────────────────────────────────────
    ("Bard", "College of Spirits"): {
        3: ["Guidance"],  # Guidance of the Spirits — cast at will
    },
    # ── Cleric Domains ───────────────────────────────────────────────────
    ("Cleric", "Knowledge Domain"): {
        1: ["Command", "Identify"],
        3: ["Augury", "Suggestion"],
        5: ["Nondetection", "Speak with Dead"],
        7: ["Arcane Eye", "Confusion"],
        9: ["Legend Lore", "Scrying"],
    },
    ("Cleric", "Ambition Domain"): {
        1: ["Bane", "Disguise Self"],
        3: ["Mirror Image", "Ray of Enfeeblement"],
        5: ["Bestow Curse", "Vampiric Touch"],
        7: ["Death Ward", "Dimension Door"],
        9: ["Dominate Person", "Modify Memory"],
    },
    ("Cleric", "Solidarity Domain"): {
        1: ["Bless", "Guiding Bolt"],
        3: ["Aid", "Warding Bond"],
        5: ["Beacon of Hope", "Crusader's Mantle"],
        7: ["Aura of Life", "Guardian of Faith"],
        9: ["Circle of Power", "Mass Cure Wounds"],
    },
    ("Cleric", "Strength Domain"): {
        1: ["Divine Favor", "Shield of Faith"],
        3: ["Enhance Ability", "Protection from Poison"],
        5: ["Haste", "Protection from Energy"],
        7: ["Dominate Beast", "Stoneskin"],
        9: ["Destructive Wave", "Insect Plague"],
    },
    ("Cleric", "Zeal Domain"): {
        1: ["Searing Smite", "Thunderous Smite"],
        3: ["Magic Weapon", "Shatter"],
        5: ["Haste", "Fireball"],
        7: ["Fire Shield", "Freedom of Movement"],
        9: ["Destructive Wave", "Flame Strike"],
    },
    # Core PHB/SCAG domains.
    ("Cleric", "Life Domain"): {
        1: ["Bless", "Cure Wounds"],
        3: ["Lesser Restoration", "Spiritual Weapon"],
        5: ["Beacon of Hope", "Revivify"],
        7: ["Death Ward", "Guardian of Faith"],
        9: ["Mass Cure Wounds", "Raise Dead"],
    },
    ("Cleric", "Light Domain"): {
        1: ["Burning Hands", "Faerie Fire"],
        3: ["Flaming Sphere", "Scorching Ray"],
        5: ["Daylight", "Fireball"],
        7: ["Guardian of Faith", "Wall of Fire"],
        9: ["Flame Strike", "Scrying"],
    },
    ("Cleric", "Nature Domain"): {
        1: ["Animal Friendship", "Speak with Animals"],
        3: ["Barkskin", "Spike Growth"],
        5: ["Plant Growth", "Wind Wall"],
        7: ["Dominate Beast", "Grasping Vine"],
        9: ["Insect Plague", "Tree Stride"],
    },
    ("Cleric", "Tempest Domain"): {
        1: ["Fog Cloud", "Thunderwave"],
        3: ["Gust of Wind", "Shatter"],
        5: ["Call Lightning", "Sleet Storm"],
        7: ["Control Water", "Ice Storm"],
        9: ["Destructive Wave", "Insect Plague"],
    },
    ("Cleric", "Trickery Domain"): {
        1: ["Charm Person", "Disguise Self"],
        3: ["Mirror Image", "Pass without Trace"],
        5: ["Blink", "Dispel Magic"],
        7: ["Dimension Door", "Polymorph"],
        9: ["Dominate Person", "Modify Memory"],
    },
    ("Cleric", "War Domain"): {
        1: ["Divine Favor", "Shield of Faith"],
        3: ["Magic Weapon", "Spiritual Weapon"],
        5: ["Crusader's Mantle", "Spirit Guardians"],
        7: ["Freedom of Movement", "Stoneskin"],
        9: ["Flame Strike", "Hold Monster"],
    },
    ("Cleric", "Death Domain"): {
        1: ["False Life", "Ray of Sickness"],
        3: ["Blindness/Deafness", "Ray of Enfeeblement"],
        5: ["Animate Dead", "Vampiric Touch"],
        7: ["Blight", "Death Ward"],
        9: ["Antilife Shell", "Cloudkill"],
    },
    # Supplement (SCAG/XGE/TCE) domains. "Resilient Sphere"/"Telepathic
    # Bond" are this app's spell-database names for what the source text
    # calls "Otiluke's Resilient Sphere"/"Rary's Telepathic Bond" -- the
    # possessive-prefixed names don't exist as separate entries here.
    ("Cleric", "Arcana Domain"): {
        1: ["Detect Magic", "Magic Missile"],
        3: ["Magic Weapon", "Nystul's Magic Aura"],
        5: ["Dispel Magic", "Magic Circle"],
        7: ["Arcane Eye", "Leomund's Secret Chest"],
        9: ["Planar Binding", "Teleportation Circle"],
    },
    ("Cleric", "Forge Domain"): {
        1: ["Identify", "Searing Smite"],
        3: ["Heat Metal", "Magic Weapon"],
        5: ["Elemental Weapon", "Protection from Energy"],
        7: ["Fabricate", "Wall of Fire"],
        9: ["Animate Objects", "Creation"],
    },
    ("Cleric", "Grave Domain"): {
        1: ["Bane", "False Life"],
        3: ["Gentle Repose", "Ray of Enfeeblement"],
        5: ["Revivify", "Vampiric Touch"],
        7: ["Blight", "Death Ward"],
        9: ["Antilife Shell", "Raise Dead"],
    },
    ("Cleric", "Order Domain"): {
        1: ["Command", "Heroism"],
        3: ["Hold Person", "Zone of Truth"],
        5: ["Mass Healing Word", "Slow"],
        7: ["Compulsion", "Locate Creature"],
        9: ["Commune", "Dominate Person"],
    },
    ("Cleric", "Peace Domain"): {
        1: ["Heroism", "Sanctuary"],
        3: ["Aid", "Warding Bond"],
        5: ["Beacon of Hope", "Sending"],
        7: ["Aura of Purity", "Resilient Sphere"],
        9: ["Greater Restoration", "Telepathic Bond"],
    },
    ("Cleric", "Twilight Domain"): {
        1: ["Faerie Fire", "Sleep"],
        3: ["Moonbeam", "See Invisibility"],
        5: ["Aura of Vitality", "Leomund's Tiny Hut"],
        7: ["Aura of Life", "Greater Invisibility"],
        9: ["Circle of Power", "Mislead"],
    },

    # ── Druid: Circle of the Land (terrain-specific) ────────────────────────
    # Keyed by the exact terrain string used in the land_terrain chooser.
    ("Druid", "Circle of the Land: Arctic"): {
        3: ["Hold Person", "Spike Growth"],
        5: ["Sleet Storm", "Slow"],
        7: ["Freedom of Movement", "Ice Storm"],
        9: ["Commune with Nature", "Cone of Cold"],
    },
    ("Druid", "Circle of the Land: Coast"): {
        3: ["Mirror Image", "Misty Step"],
        5: ["Water Breathing", "Water Walk"],
        7: ["Control Water", "Freedom of Movement"],
        9: ["Conjure Elemental", "Scrying"],
    },
    ("Druid", "Circle of the Land: Desert"): {
        3: ["Blur", "Silence"],
        5: ["Create Food and Water", "Protection from Energy"],
        7: ["Blight", "Hallucinatory Terrain"],
        9: ["Insect Plague", "Wall of Stone"],
    },
    ("Druid", "Circle of the Land: Forest"): {
        3: ["Barkskin", "Spider Climb"],
        5: ["Call Lightning", "Plant Growth"],
        7: ["Divination", "Freedom of Movement"],
        9: ["Commune with Nature", "Tree Stride"],
    },
    ("Druid", "Circle of the Land: Grassland"): {
        3: ["Invisibility", "Pass without Trace"],
        5: ["Daylight", "Haste"],
        7: ["Divination", "Freedom of Movement"],
        9: ["Dream", "Insect Plague"],
    },
    ("Druid", "Circle of the Land: Mountain"): {
        3: ["Spider Climb", "Spike Growth"],
        5: ["Lightning Bolt", "Meld into Stone"],
        7: ["Stone Shape", "Stoneskin"],
        9: ["Passwall", "Wall of Stone"],
    },
    ("Druid", "Circle of the Land: Swamp"): {
        3: ["Darkness", "Melf's Acid Arrow"],
        5: ["Water Walk", "Stinking Cloud"],
        7: ["Freedom of Movement", "Locate Creature"],
        9: ["Insect Plague", "Scrying"],
    },
    ("Druid", "Circle of the Land: Underdark"): {
        3: ["Spider Climb", "Web"],
        5: ["Gaseous Form", "Stinking Cloud"],
        7: ["Greater Invisibility", "Stone Shape"],
        9: ["Cloudkill", "Insect Plague"],
    },
    # Circle of Spores/Wildfire (TCE) each have their own "Circle Spells"
    # table too, not just Circle of the Land. Level 2 also grants a bonus
    # cantrip on top of the table (Chill Touch for Spores; Wildfire's own
    # table starts at level 2).
    ("Druid", "Circle of Spores"): {
        2: ["Chill Touch"],
        3: ["Blindness/Deafness", "Gentle Repose"],
        5: ["Animate Dead", "Gaseous Form"],
        7: ["Blight", "Confusion"],
        9: ["Cloudkill", "Contagion"],
    },
    ("Druid", "Circle of Wildfire"): {
        2: ["Burning Hands", "Cure Wounds"],
        3: ["Flaming Sphere", "Scorching Ray"],
        5: ["Plant Growth", "Revivify"],
        7: ["Aura of Life", "Fire Shield"],
        9: ["Flame Strike", "Mass Cure Wounds"],
    },
    # Star Map: you know Guidance and always have Guiding Bolt prepared
    # (neither counts against your cantrips/prepared spells).
    ("Druid", "Circle of Stars"): {
        2: ["Guidance", "Guiding Bolt"],
    },

    # ── Sorcerer Origins ─────────────────────────────────────────────────
    # Psionic Spells / Clockwork Magic: learned at these sorcerer levels,
    # and they don't count against sorcerer spells known.
    ("Sorcerer", "Aberrant Mind"): {
        1: ["Arms of Hadar", "Dissonant Whispers", "Mind Sliver"],
        3: ["Calm Emotions", "Detect Thoughts"],
        5: ["Hunger of Hadar", "Sending"],
        7: ["Evard's Black Tentacles", "Summon Aberration"],
        9: ["Telepathic Bond", "Telekinesis"],
    },
    ("Sorcerer", "Clockwork Soul"): {
        1: ["Alarm", "Protection from Evil and Good"],
        3: ["Aid", "Lesser Restoration"],
        5: ["Dispel Magic", "Protection from Energy"],
        7: ["Freedom of Movement", "Summon Construct"],
        9: ["Greater Restoration", "Wall of Force"],
    },

    # ── Paladin Oaths ────────────────────────────────────────────────────
    ("Paladin", "Oath of Devotion"): {
        3: ["Protection from Evil and Good", "Sanctuary"],
        5: ["Lesser Restoration", "Zone of Truth"],
        9: ["Beacon of Hope", "Dispel Magic"],
        13: ["Freedom of Movement", "Guardian of Faith"],
        17: ["Commune", "Flame Strike"],
    },
    ("Paladin", "Oath of the Ancients"): {
        3: ["Ensnaring Strike", "Speak with Animals"],
        5: ["Moonbeam", "Misty Step"],
        9: ["Plant Growth", "Protection from Energy"],
        13: ["Ice Storm", "Stoneskin"],
        17: ["Commune with Nature", "Tree Stride"],
    },
    ("Paladin", "Oath of Vengeance"): {
        3: ["Bane", "Hunter's Mark"],
        5: ["Hold Person", "Misty Step"],
        9: ["Haste", "Protection from Energy"],
        13: ["Banishment", "Dimension Door"],
        17: ["Hold Monster", "Scrying"],
    },
    ("Paladin", "Oath of Conquest"): {
        3: ["Armor of Agathys", "Command"],
        5: ["Hold Person", "Spiritual Weapon"],
        9: ["Bestow Curse", "Fear"],
        13: ["Dominate Beast", "Stoneskin"],
        17: ["Cloudkill", "Dominate Person"],
    },
    ("Paladin", "Oath of the Crown"): {
        3: ["Command", "Compelled Duel"],
        5: ["Warding Bond", "Zone of Truth"],
        9: ["Aura of Vitality", "Spirit Guardians"],
        13: ["Banishment", "Guardian of Faith"],
        17: ["Circle of Power", "Geas"],
    },
    ("Paladin", "Oath of Glory"): {
        3: ["Guiding Bolt", "Heroism"],
        5: ["Enhance Ability", "Magic Weapon"],
        9: ["Haste", "Protection from Energy"],
        13: ["Compulsion", "Freedom of Movement"],
        17: ["Commune", "Flame Strike"],
    },
    ("Paladin", "Oath of Redemption"): {
        3: ["Sanctuary", "Sleep"],
        5: ["Calm Emotions", "Hold Person"],
        9: ["Counterspell", "Hypnotic Pattern"],
        13: ["Resilient Sphere", "Stoneskin"],
        17: ["Hold Monster", "Wall of Force"],
    },
    ("Paladin", "Oath of the Watchers"): {
        3: ["Alarm", "Detect Magic"],
        5: ["Moonbeam", "See Invisibility"],
        9: ["Counterspell", "Nondetection"],
        13: ["Aura of Purity", "Banishment"],
        17: ["Hold Monster", "Scrying"],
    },
    ("Paladin", "Oathbreaker"): {
        3: ["Hellish Rebuke", "Inflict Wounds"],
        5: ["Crown of Madness", "Darkness"],
        9: ["Animate Dead", "Bestow Curse"],
        13: ["Blight", "Confusion"],
        17: ["Contagion", "Dominate Person"],
    },

    # ── Ranger Conclaves ─────────────────────────────────────────────────
    ("Ranger", "Horizon Walker"): {
        3: ["Protection from Evil and Good"],
        5: ["Misty Step"],
        9: ["Haste"],
        13: ["Banishment"],
        17: ["Teleportation Circle"],
    },
    ("Ranger", "Monster Slayer"): {
        3: ["Protection from Evil and Good"],
        5: ["Zone of Truth"],
        9: ["Magic Circle"],
        13: ["Banishment"],
        17: ["Hold Monster"],
    },
    ("Ranger", "Swarmkeeper"): {
        3: ["Faerie Fire", "Mage Hand"],
        5: ["Web"],
        9: ["Gaseous Form"],
        13: ["Arcane Eye"],
        17: ["Insect Plague"],
    },
    ("Ranger", "Fey Wanderer"): {
        3: ["Charm Person"],
        5: ["Misty Step"],
        9: ["Dispel Magic"],
        13: ["Dimension Door"],
        17: ["Mislead"],
    },
    ("Ranger", "Gloom Stalker"): {
        3: ["Disguise Self"],
        5: ["Rope Trick"],
        9: ["Fear"],
        13: ["Greater Invisibility"],
        17: ["Seeming"],
    },

    # ── Warlock Patrons ──────────────────────────────────────────────────
    ("Warlock", "The Hexblade"): {
        1: ["Shield", "Wrathful Smite"],
        3: ["Blur", "Branding Smite"],
        5: ["Blink", "Elemental Weapon"],
        7: ["Phantasmal Killer", "Staggering Smite"],
        9: ["Banishing Smite", "Cone of Cold"],
    },
    ("Warlock", "The Fiend"): {
        1: ["Burning Hands", "Command"],
        3: ["Blindness/Deafness", "Scorching Ray"],
        5: ["Fireball", "Stinking Cloud"],
        7: ["Fire Shield", "Wall of Fire"],
        9: ["Flame Strike", "Hallow"],
    },
}

# ── Racial bonus spells ──────────────────────────────────────────────────
# Innate spellcasting traits granted by race (and, where relevant,
# subrace), keyed by CHARACTER (total) level rather than class level,
# since these come from being a member of the race, not from any
# particular class. Several of these have real, specific level gates in
# the source text — Tiefling's Infernal Legacy doesn't grant Hellish
# Rebuke until 3rd level or Darkness until 5th, for instance, not all
# three at 1st level.
#
# Structure: {(race, subrace_match_or_None): {level: [spells]}}
# subrace_match is None for races with no subrace split relevant to
# spellcasting (matches regardless of subrace); otherwise it's matched
# as a substring against char["subrace"], same convention as class/
# subclass matching above.
#
# Deliberately NOT included here: traits that grant a player's CHOICE of
# cantrip (High Elf, Astral Elf, several Half-Elf/Genasi Versatility
# options) — those need a real chooser, not a guessed default, the same
# reasoning applied throughout this file for class features. Also not
# included: a dragonmark's "Spells of the Mark" table, which EXPANDS what
# a spellcasting class can choose from rather than granting an innate
# spell directly (MARK_EXPANDED_SPELLS below).
RACIAL_BONUS_SPELLS = {
    # ── Tiefling bloodlines (PHB base + MToF bloodlines + SCAG variant) ──
    ("Tiefling", "Asmodeus"): {1: ["Thaumaturgy"], 3: ["Hellish Rebuke"], 5: ["Darkness"]},
    ("Tiefling", "Baalzebul"): {1: ["Thaumaturgy"], 3: ["Ray of Sickness"], 5: ["Crown of Madness"]},
    ("Tiefling", "Dispater"): {1: ["Thaumaturgy"], 3: ["Disguise Self"], 5: ["Detect Thoughts"]},
    ("Tiefling", "Fierna"): {1: ["Friends"], 3: ["Charm Person"], 5: ["Suggestion"]},
    ("Tiefling", "Glasya"): {1: ["Minor Illusion"], 3: ["Disguise Self"], 5: ["Invisibility"]},
    ("Tiefling", "Levistus"): {1: ["Ray of Frost"], 3: ["Armor of Agathys"], 5: ["Darkness"]},
    ("Tiefling", "Mammon"): {1: ["Mage Hand"], 3: ["Tenser's Floating Disk"], 5: ["Arcane Lock"]},
    ("Tiefling", "Mephistopheles"): {1: ["Mage Hand"], 3: ["Burning Hands"], 5: ["Flame Blade"]},
    ("Tiefling", "Zariel"): {1: ["Thaumaturgy"], 3: ["Searing Smite"], 5: ["Branding Smite"]},
    ("Tiefling", "Devil's Tongue"): {1: ["Vicious Mockery"], 3: ["Charm Person"], 5: ["Enthrall"]},
    # Hellfire only swaps the 3rd-level spell (Burning Hands instead of
    # Hellish Rebuke, otherwise identical to Asmodeus); Winged drops
    # spellcasting entirely.
    ("Tiefling", "Hellfire"): {1: ["Thaumaturgy"], 3: ["Burning Hands"], 5: ["Darkness"]},
    # Feral only changes the ability scores; Infernal Legacy stays
    ("Tiefling", "Feral"): {1: ["Thaumaturgy"], 3: ["Hellish Rebuke"], 5: ["Darkness"]},

    # ── Elf subraces ─────────────────────────────────────────────────────
    ("Elf", "Drow"): {1: ["Dancing Lights"], 3: ["Faerie Fire"], 5: ["Darkness"]},
    ("Elf", "Pallid"): {1: ["Light"], 3: ["Sleep"], 5: ["Invisibility"]},
    ("Elf", "Mark of Shadow"): {1: ["Minor Illusion"], 3: ["Invisibility"]},

    # ── Half-Elf ─────────────────────────────────────────────────────────
    # (only with Drow Magic as its variant feature: racial_innate_spells)
    ("Half-Elf", "Drow Descent"): {1: ["Dancing Lights"], 3: ["Faerie Fire"], 5: ["Darkness"]},
    ("Half-Elf", "Mark of Detection"): {1: ["Detect Magic", "Detect Poison and Disease"], 3: ["See Invisibility"]},
    ("Half-Elf", "Mark of Storm"): {1: ["Gust"], 3: ["Gust of Wind"]},

    # ── Gnome ────────────────────────────────────────────────────────────
    ("Gnome", "Forest"): {1: ["Minor Illusion"]},
    # (a deep gnome's spells come from the Svirfneblin Magic feat)

    # ── Dwarf, Halfling ──────────────────────────────────────────────────
    ("Dwarf", "Duergar"): {3: ["Enlarge/Reduce"], 5: ["Invisibility"]},
    ("Halfling", "Lotusden"): {1: ["Druidcraft"], 3: ["Entangle"], 5: ["Spike Growth"]},

    # ── Genasi ────────────────────────────────────────────────────────
    ("Genasi", "Air"): {1: ["Levitate"]},
    ("Genasi", "Earth"): {1: ["Pass without Trace"]},
    ("Genasi", "Fire"): {1: ["Produce Flame"], 3: ["Burning Hands"]},
    ("Genasi", "Water"): {1: ["Shape Water"], 3: ["Create or Destroy Water"]},
    ("Genasi (MPMM)", "Air"): {1: ["Shocking Grasp"], 3: ["Feather Fall"], 5: ["Levitate"]},
    ("Genasi (MPMM)", "Earth"): {1: ["Blade Ward"], 5: ["Pass without Trace"]},
    ("Genasi (MPMM)", "Fire"): {1: ["Produce Flame"], 3: ["Burning Hands"], 5: ["Flame Blade"]},
    ("Genasi (MPMM)", "Water"): {1: ["Acid Splash"], 3: ["Create or Destroy Water"], 5: ["Water Walk"]},

    # ── Other races with fixed (non-choice) innate spells ──────────────
    ("Aasimar", None): {1: ["Light"]},
    ("Firbolg", None): {1: ["Detect Magic", "Disguise Self"]},
    ("Fairy", None): {1: ["Druidcraft"], 3: ["Faerie Fire"], 5: ["Enlarge/Reduce"]},
    ("Hexblood", None): {1: ["Disguise Self", "Hex"]},
    ("Yuan-ti Pureblood", None): {1: ["Poison Spray", "Animal Friendship"], 3: ["Suggestion"]},
    ("Githyanki", None): {1: ["Mage Hand"], 3: ["Jump"], 5: ["Misty Step"]},
    ("Githzerai", None): {1: ["Mage Hand"], 3: ["Shield"], 5: ["Detect Thoughts"]},
    ("Triton", None): {1: ["Fog Cloud"], 3: ["Gust of Wind"], 5: ["Wall of Water"]},
    ("Triton (MPMM)", None): {1: ["Fog Cloud"], 3: ["Gust of Wind"], 5: ["Water Walk"]},
    ("Aarakocra (MPMM)", None): {3: ["Gust of Wind"]},
    ("Siren", None): {1: ["Friends"]},
    # ── The other dragonmarks' own spells (docs/reference/races-sublist.md)
    ("Dwarf", "Mark of Warding"): {1: ["Alarm", "Mage Armor"], 3: ["Arcane Lock"]},
    ("Gnome", "Mark of Scribing"): {1: ["Message", "Comprehend Languages"], 3: ["Magic Mouth"]},
    ("Half-Orc", "Mark of Finding"): {1: ["Hunter's Mark"], 3: ["Locate Object"]},
    ("Human", "Mark of Finding"): {1: ["Hunter's Mark"], 3: ["Locate Object"]},
    ("Halfling", "Mark of Healing"): {1: ["Cure Wounds"], 3: ["Lesser Restoration"]},
    ("Halfling", "Mark of Hospitality"): {1: ["Prestidigitation", "Purify Food and Drink", "Unseen Servant"]},
    ("Human", "Mark of Handling"): {1: ["Animal Friendship", "Speak with Animals"]},
    ("Human", "Mark of Making"): {1: ["Mending", "Magic Weapon"]},
    ("Human", "Mark of Passage"): {1: ["Misty Step"]},
    # Mark of Sentinel: Guardian's Shield
    ("Human", "Mark of Sentinel"): {1: ["Shield"]},
}


def race_table_key(species: str, race_keys) -> str | None:
    """Which of a table's race keys a species uses: the longest one the
    species starts with, so "Genasi (MPMM)" takes its own entries over the
    original "Genasi" ones, and "Firbolg (MPMM)" falls back to "Firbolg"
    when the two share their spells. A prefix, never containment -- "Elf"
    is inside "Half-Elf" too."""
    sp = (species or "").lower()
    keys = [k for k in race_keys if sp.startswith(k.lower())]
    return max(keys, key=len) if keys else None


def racial_innate_spells(char: dict) -> list[str]:
    """The fixed spells the character's race gives them at their current
    level (RACIAL_BONUS_SPELLS) -- e.g. a 5th-level Tiefling's Thaumaturgy,
    Hellish Rebuke and Darkness."""
    from dnd_app.core.character import total_level
    out = []
    species = char.get("species") or char.get("race", "")
    char_subrace = char.get("subrace", "") or ""
    if species.strip().lower() == "tiefling" and not char_subrace.strip():
        char_subrace = "Asmodeus"  # PHB default bloodline per the race data
    char_lvl = total_level(char)
    race_key_used = race_table_key(species, {r for (r, _s) in RACIAL_BONUS_SPELLS})
    for (race_key, subrace_key), by_level in RACIAL_BONUS_SPELLS.items():
        if race_key != race_key_used:
            continue
        if subrace_key is not None and not char_subrace.lower().startswith(subrace_key.lower()):
            continue
        if (race_key, subrace_key) == ("Half-Elf", "Drow Descent"):
            from dnd_app.data.races import half_elf_variant
            if half_elf_variant(char) != "Drow Magic":
                continue
        for req_lvl, spells in by_level.items():
            if char_lvl >= req_lvl:
                out.extend(spells)
    return out


# The ability a race casts its spells with (docs/reference/races-sublist.md),
# keyed like RACIAL_BONUS_SPELLS. "choice": INT, WIS or CHA, picked with
# the race (_choices["racial_spell_ability"]); the value is the trait the
# choice card names.
RACIAL_SPELL_ABILITY = {
    ("Tiefling", None): "CHA",
    ("Elf", "High"): "INT", ("Elf", "Drow"): "CHA", ("Elf", "Pallid"): "WIS",
    ("Elf", "Mark of Shadow"): "CHA",
    ("Half-Elf", "Drow Descent"): "CHA", ("Half-Elf", "High Descent"): "INT",
    ("Half-Elf", "Mark of Detection"): "WIS", ("Half-Elf", "Mark of Storm"): "CHA",
    ("Gnome", "Forest"): "INT", ("Gnome", "Mark of Scribing"): "INT",
    ("Dwarf", "Duergar"): "INT", ("Dwarf", "Mark of Warding"): "INT",
    ("Halfling", "Lotusden"): "WIS", ("Halfling", "Mark of Healing"): "WIS",
    ("Halfling", "Mark of Hospitality"): "CHA",
    ("Half-Orc", "Mark of Finding"): "WIS",
    ("Human", "Mark of Finding"): "WIS", ("Human", "Mark of Handling"): "WIS",
    ("Human", "Mark of Making"): "INT", ("Human", "Mark of Passage"): "DEX",
    ("Human", "Mark of Sentinel"): "WIS",
    ("Merfolk", "Green"): "WIS", ("Merfolk", "Blue"): "INT", ("Merfolk", "Emeria"): "WIS",
    ("Merfolk", "Ula"): "INT", ("Merfolk", "Cosi"): "CHA",
    ("Aasimar", None): "CHA",
    ("Firbolg", None): "WIS",
    ("Genasi", None): "CON",
    ("Githyanki", None): "INT",
    ("Githzerai", None): "WIS",
    ("Triton", None): "CHA",
    ("Yuan-ti Pureblood", "Pureblood VGM"): "CHA",
    ("Firbolg (MPMM)", None): ("choice", "Firbolg Magic"),
    ("Genasi (MPMM)", "Air"): ("choice", "Mingle with the Wind"),
    ("Genasi (MPMM)", "Earth"): ("choice", "Merge with Stone"),
    ("Genasi (MPMM)", "Fire"): ("choice", "Reach to the Blaze"),
    ("Genasi (MPMM)", "Water"): ("choice", "Call to the Wave"),
    ("Githyanki (MPMM)", None): ("choice", "Githyanki Psionics"),
    ("Githzerai (MPMM)", None): ("choice", "Githzerai Psionics"),
    ("Triton (MPMM)", None): ("choice", "Control Air and Water"),
    ("Aarakocra (MPMM)", None): ("choice", "Wind Caller"),
    ("Yuan-ti Pureblood", None): ("choice", "Innate Spellcasting"),
    ("Fairy", None): ("choice", "Fairy Magic"),
    ("Hexblood", None): ("choice", "Hex Magic"),
    ("Astral Elf", None): ("choice", "Astral Fire"),
    ("Kobold (MPMM)", None): ("choice", "Draconic Sorcery"),
}

# _choices keys holding a racial spell the player picked
RACIAL_SPELL_PICK_KEYS = ("race_wizard_cantrip", "race_merfolk_cantrip",
                          "astral_elf_cantrip", "race_sorcerer_cantrip")


def racial_spell_ability_entry(char: dict):
    """The RACIAL_SPELL_ABILITY entry for the character's race and subrace:
    "CHA", ("choice", trait) or None. A subrace's own entry wins over the
    race's (a VGM yuan-ti's CHA over the MPMM choice)."""
    species = char.get("species") or char.get("race", "")
    subrace = (char.get("subrace") or "").lower()
    key = race_table_key(species, {r for (r, _s) in RACIAL_SPELL_ABILITY})
    if not key:
        return None
    if key == "Kobold (MPMM)":
        from dnd_app.data.races import kobold_legacy
        if kobold_legacy(char) != "Draconic Sorcery":
            return None
    for (r, sub), val in RACIAL_SPELL_ABILITY.items():
        if r == key and sub and subrace.startswith(sub.lower()):
            return val
    return RACIAL_SPELL_ABILITY.get((key, None))


def racial_spells(char: dict) -> list[str]:
    """Every spell the character's race gives them: the fixed ones and the
    cantrip they picked (a High Elf's wizard cantrip...)."""
    out = list(racial_innate_spells(char))
    choices = char.get("_choices", {})
    for key in RACIAL_SPELL_PICK_KEYS:
        out.extend(sp for sp in choices.get(key, []) if sp not in out)
    return out


# Spells a feat gives you outright: {feat: [fixed spells]}, plus the
# _choices keys holding the ones you pick (core/choices.py asks for them)
# and the ones a pick decides (FEAT_PICKED_SPELLS). How each can be cast
# for free is core/spellcasting.py's.
FEAT_FIXED_SPELLS = {
    "Fey Touched": ["Misty Step"],
    "Shadow Touched": ["Invisibility"],
    "Telepathic": ["Detect Thoughts"],
    "Telekinetic": ["Mage Hand"],
    "Fey Teleportation": ["Misty Step"],
    "Outlands Envoy": ["Misty Step", "Tongues"],
    "Mystic Conflux": ["Identify"],
    "Field Medic": ["Cure Wounds", "Spare the Dying"],
    "Rune Shaper": ["Comprehend Languages"],
    "Cartomancer": ["Prestidigitation"],
    "Strixhaven Mascot": ["Find Familiar"],
    "Wood Elf Magic": ["Longstrider", "Pass without Trace"],
    "Drow High Magic": ["Detect Magic", "Levitate", "Dispel Magic"],
    "Svirfneblin Magic": ["Nondetection", "Blindness/Deafness", "Blur", "Disguise Self"],
    "Flamewoken": ["Produce Flame"],
    "Plantmender": ["Shillelagh", "Barkskin", "Spike Growth"],
    "Gift of the Metallic Dragon": ["Cure Wounds"],
    "Divinely Favored": ["Augury"],
}
FEAT_CHOSEN_SPELL_KEYS = {
    "Fey Touched": ["feat_fey_touched_spell"],
    "Shadow Touched": ["feat_shadow_touched_spell"],
    "Magic Initiate": ["feat_magic_initiate_cantrips", "feat_magic_initiate_spell"],
    "Spell Sniper": ["feat_spell_sniper_cantrip"],
    "Artificer Initiate": ["feat_artificer_initiate_cantrip", "feat_artificer_initiate_spell"],
    "Aberrant Dragonmark": ["feat_aberrant_dragonmark_cantrip", "feat_aberrant_dragonmark_spell"],
    "Wood Elf Magic": ["feat_wood_elf_magic_cantrip"],
    "Divinely Favored": ["feat_divinely_favored_cantrip", "feat_divinely_favored_spell"],
    "Strixhaven Initiate": ["feat_strixhaven_initiate_cantrips", "feat_strixhaven_initiate_spell"],
    "Initiate of High Sorcery": ["feat_initiate_of_high_sorcery_cantrip",
                                 "feat_initiate_of_high_sorcery_spells"],
    "Adept of the Black Robes": ["feat_adept_of_the_black_robes_spell"],
    "Adept of the Red Robes": ["feat_adept_of_the_red_robes_spell"],
    "Adept of the White Robes": ["feat_adept_of_the_white_robes_spell"],
    "Rune Shaper": ["feat_rune_shaper_runes"],
}

# Spells a feat gives by what you picked for it: {feat: (_choices key,
# {pick: [spells]})} -- a Scion of the Outer Planes' cantrip is its plane's
FEAT_PICKED_SPELLS = {
    "Scion of the Outer Planes": ("feat_scion_plane_type", {
        "Chaotic Outer Plane": ["Minor Illusion"], "Evil Outer Plane": ["Chill Touch"],
        "Good Outer Plane": ["Sacred Flame"], "Lawful Outer Plane": ["Guidance"],
        "The Outlands": ["Mage Hand"]}),
}

# What the feats that let you choose pick from (docs/reference/feats-sublist.md)
# Strixhaven Initiate: each college's cantrips (two of them) and the class
# lists its 1st-level spell can come from
STRIXHAVEN_COLLEGES = {
    "Lorehold": (("Light", "Sacred Flame", "Thaumaturgy"), ("Cleric", "Wizard")),
    "Prismari": (("Fire Bolt", "Prestidigitation", "Ray of Frost"), ("Bard", "Sorcerer")),
    "Quandrix": (("Druidcraft", "Guidance", "Mage Hand"), ("Druid", "Wizard")),
    "Silverquill": (("Sacred Flame", "Thaumaturgy", "Vicious Mockery"), ("Bard", "Cleric")),
    "Witherbloom": (("Chill Touch", "Druidcraft", "Spare the Dying"), ("Druid", "Wizard")),
}
# Initiate of High Sorcery: each moon's 1st-level spells (two of them)
HIGH_SORCERY_MOONS = {
    "Nuitari": ("Dissonant Whispers", "False Life", "Hex", "Ray of Sickness"),
    "Lunitari": ("Color Spray", "Disguise Self", "Feather Fall", "Longstrider"),
    "Solinari": ("Comprehend Languages", "Detect Evil and Good", "Protection from Evil and Good", "Shield"),
}
# The Adept of the Robes feats: the schools their 2nd-level spell comes from
ROBES_SCHOOLS = {
    "Adept of the Black Robes": ("Enchantment", "Necromancy"),
    "Adept of the Red Robes": ("Illusion", "Transmutation"),
    "Adept of the White Robes": ("Abjuration", "Divination"),
}
# Rune Shaper: each rune and the spell it gives
RUNE_SHAPER_RUNES = {
    "Cloud": "Fog Cloud", "Death": "Inflict Wounds", "Dragon": "Chromatic Orb",
    "Enemy": "Disguise Self", "Fire": "Burning Hands", "Friend": "Speak with Animals",
    "Frost": "Armor of Agathys", "Hill": "Goodberry", "Journey": "Longstrider",
    "King": "Command", "Mountain": "Entangle", "Stone": "Sanctuary", "Storm": "Thunderwave",
}


def divinely_favored_list(char: dict) -> str:
    """The class list Divinely Favored's 1st-level spell comes from: your
    alignment's -- warlock if evil, cleric if good, druid if neutral."""
    alignment = (char.get("alignment") or "").lower()
    return "Warlock" if "evil" in alignment else "Cleric" if "good" in alignment else "Druid"

# The ability a feat casts its spells with (docs/reference/feats-sublist.md):
#   an ability           "WIS"
#   "increased"          the one the feat's +1 went to (Fey Touched)
#   "class"              that of the class whose list the spells came from
#   "choice"             INT, WIS or CHA, picked with the feat
#                        (_choices["feat_spell_ability_<feat>"])
#   another feat         that feat's (the Adept robes use Initiate of High
#                        Sorcery's)
FEAT_SPELL_ABILITY = {
    "Aberrant Dragonmark": "CON", "Artificer Initiate": "INT",
    "Drow High Magic": "CHA", "Fey Teleportation": "INT", "Field Medic": "WIS",
    "Flamewoken": "CHA", "Plantmender": "WIS", "Svirfneblin Magic": "INT",
    "Wood Elf Magic": "WIS",
    "Fey Touched": "increased", "Shadow Touched": "increased",
    "Telekinetic": "increased", "Telepathic": "increased",
    "Keenness of the Stone Giant": "increased",
    "Magic Initiate": "class", "Spell Sniper": "class",
    "Divinely Favored": "choice", "Gift of the Metallic Dragon": "choice",
    "Initiate of High Sorcery": "choice", "Rune Shaper": "choice",
    "Scion of the Outer Planes": "choice", "Strixhaven Initiate": "choice",
    "Adept of the Black Robes": "Initiate of High Sorcery",
    "Adept of the Red Robes": "Initiate of High Sorcery",
    "Adept of the White Robes": "Initiate of High Sorcery",
    "Outlands Envoy": "Scion of the Outer Planes",
    "Agent of Order": "Scion of the Outer Planes",
}

# Magic Initiate and Spell Sniper: the spell lists to choose from, the
# ability each one casts with, and the _choices key of the class picked
SPELL_LIST_ABILITY = {"Bard": "CHA", "Cleric": "WIS", "Druid": "WIS",
                      "Sorcerer": "CHA", "Warlock": "CHA", "Wizard": "INT"}
FEAT_SPELL_CLASS_KEYS = {"Magic Initiate": "feat_magic_initiate_class",
                         "Spell Sniper": "feat_spell_sniper_class"}

# Cantrips that make a spell attack roll (Spell Sniper's to choose from)
ATTACK_ROLL_CANTRIPS = ("Chill Touch", "Eldritch Blast", "Fire Bolt", "Magic Stone",
                        "Primal Savagery", "Produce Flame", "Ray of Frost",
                        "Shocking Grasp", "Thorn Whip")

_ABILITY_ABBR = {"Strength": "STR", "Dexterity": "DEX", "Constitution": "CON",
                 "Intelligence": "INT", "Wisdom": "WIS", "Charisma": "CHA"}


def feat_slug(feat: str) -> str:
    """"Fey Touched" -> "fey_touched", as the feat's _choices keys use it."""
    return feat.lower().replace(" ", "_")


def feat_spells(char: dict, feat: str) -> list[str]:
    """The spells `feat` gives the character: its fixed ones and the ones
    picked for it."""
    choices = char.get("_choices", {})
    out = list(FEAT_FIXED_SPELLS.get(feat, []))
    for key in FEAT_CHOSEN_SPELL_KEYS.get(feat, []):
        out.extend(sp for sp in choices.get(key, []) if sp not in out)
    if feat in FEAT_PICKED_SPELLS:
        key, by_pick = FEAT_PICKED_SPELLS[feat]
        for pick in choices.get(key, []):
            out.extend(sp for sp in by_pick.get(pick, []) if sp not in out)
    return out


def feat_spell_class(char: dict, feat: str):
    """The class whose list Magic Initiate or Spell Sniper drew from: named
    in the feat ("Magic Initiate (Cleric)", from a background), picked for
    it, or the one list every spell picked with it is on -- else None."""
    for full in [char.get("origin_feat") or ""] + list(char.get("feats", [])):
        if full.startswith(feat + " (") and full.endswith(")"):
            cls = full[len(feat) + 2:-1]
            if cls in SPELL_LIST_ABILITY:
                return cls
    choices = char.get("_choices", {})
    pick = choices.get(FEAT_SPELL_CLASS_KEYS.get(feat, ""), [])
    if pick and pick[0] in SPELL_LIST_ABILITY:
        return pick[0]
    lists = feat_spell_class_options(char, feat)
    picked = [sp for key in FEAT_CHOSEN_SPELL_KEYS.get(feat, []) for sp in choices.get(key, [])]
    return lists[0] if picked and len(lists) == 1 else None


def feat_spell_class_options(char: dict, feat: str) -> list[str]:
    """The classes `feat`'s spells can still be from: those whose list
    holds every spell picked for it so far."""
    choices = char.get("_choices", {})
    options = list(SPELL_LIST_ABILITY)
    if feat == "Spell Sniper":
        options = [c for c in options if any(
            c in (get_spell(sp) or {}).get("classes", []) for sp in ATTACK_ROLL_CANTRIPS)]
    for key in FEAT_CHOSEN_SPELL_KEYS.get(feat, []):
        for sp in choices.get(key, []):
            on = set((get_spell(sp) or {}).get("classes", []))
            options = [c for c in options if c in on]
    return options


def feat_spell_ability(char: dict, feat: str):
    """The ability `feat`'s spells are cast with ("WIS"), or None while it
    still has to be picked (FEAT_SPELL_ABILITY)."""
    rule = FEAT_SPELL_ABILITY.get(feat)
    choices = char.get("_choices", {})
    if rule == "increased":
        chosen = choices.get(f"feat_ability_{feat_slug(feat)}")
        if isinstance(chosen, list):
            chosen = chosen[0] if chosen else None
        if chosen:
            return chosen
        # a feat taken before its ability was stored: the "asi:WIS:1"
        # kept with its pick
        for picks in choices.values():
            if isinstance(picks, list) and f"feat:{feat}" in picks:
                for p in picks:
                    if isinstance(p, str) and p.startswith("asi:"):
                        return p.split(":")[1]
        return None
    if rule == "class":
        return SPELL_LIST_ABILITY.get(feat_spell_class(char, feat) or "")
    if rule == "choice":
        pick = choices.get(f"feat_spell_ability_{feat_slug(feat)}", [])
        return _ABILITY_ABBR.get(pick[0]) if pick else None
    if rule in FEAT_SPELL_ABILITY:
        return feat_spell_ability(char, rule)
    return rule


def feat_granted_spells(char: dict) -> list[str]:
    """Every spell the character's feats give them -- the fixed ones and
    whatever they picked for the feats that let them choose."""
    out = []
    for feat in set(char.get("feats", [])):
        out.extend(feat_spells(char, feat))
    return out


def get_bonus_spells(char: dict) -> list[str]:
    """Return every bonus spell the character currently has access to,
    across all their classes/subclasses and their race, based on current
    level in each."""
    from dnd_app.core.character import class_levels, subclasses, total_level
    cl = class_levels(char)
    subs = subclasses(char)
    out = []
    for (cls_key, sub_key), by_level in BONUS_SPELLS.items():
        lvl = cl.get(cls_key, 0)
        if lvl == 0:
            continue
        actual_sub = subs.get(cls_key, "")
        # Circle of the Land is keyed per-terrain; match on the chosen
        # terrain choice rather than a literal subclass-name match.
        if cls_key == "Druid" and sub_key.startswith("Circle of the Land:"):
            terrain = sub_key.split(":", 1)[1].strip()
            picks = char.get("_choices", {}).get("land_terrain", [])
            if not (actual_sub and "land" in actual_sub.lower() and
                    any(terrain.lower() in p.lower() for p in picks)):
                continue
        else:
            # A prefix check, not "is sub_key anywhere in actual_sub" --
            # containment would match "Light Domain" against "Twilight
            # Domain" too, since "light domain" is a substring of
            # "twilight domain". Every real sub_key here is always the
            # start of actual_sub, with at most a "(SOURCE)" suffix on
            # actual_sub's end, so startswith is the correct check.
            if not actual_sub.lower().startswith(sub_key.lower()):
                continue
        for req_lvl, spells in by_level.items():
            if lvl >= req_lvl:
                out.extend(spells)

    # Death Domain: Reaper's bonus necromancy cantrip is a player CHOICE
    # (any necromancy cantrip from any class's list), not a fixed grant,
    # so it can't live in BONUS_SPELLS above like the other domain spells
    # — read the pick back in from _choices instead, same as Circle of
    # the Land's terrain choice just above.
    if cl.get("Cleric", 0) >= 1 and "death domain" in subs.get("Cleric", "").lower():
        reaper_pick = char.get("_choices", {}).get("death_domain_reaper_cantrip", [])
        out.extend(reaper_pick)

    # The Genie: the OTHER half of the Expanded Spells table (see the
    # ("Warlock", "The Genie") entry above) depends on the genie_kind
    # choice (levelup_panel.py) -- same read-the-pick-back pattern as
    # Death Domain's Reaper just above.
    GENIE_KIND_SPELLS = {
        "dao":     {1: "Sanctuary",   3: "Spike Growth",  5: "Meld into Stone", 7: "Stone Shape",         9: "Wall of Stone"},
        "djinni":  {1: "Thunderwave", 3: "Gust of Wind",  5: "Wind Wall",       7: "Greater Invisibility", 9: "Seeming"},
        "efreeti": {1: "Burning Hands", 3: "Scorching Ray", 5: "Fireball",     7: "Fire Shield",         9: "Flame Strike"},
        "marid":   {1: "Fog Cloud",   3: "Blur",           5: "Sleet Storm",   7: "Control Water",       9: "Cone of Cold"},
    }
    warlock_lvl = cl.get("Warlock", 0)
    if warlock_lvl >= 1 and "genie" in subs.get("Warlock", "").lower():
        kind_pick = char.get("_choices", {}).get("genie_kind", [])
        if kind_pick:
            kind = kind_pick[0].split("–")[0].strip().lower()
            for req_lvl, sp_name in GENIE_KIND_SPELLS.get(kind, {}).items():
                if warlock_lvl >= req_lvl:
                    out.append(sp_name)

    out.extend(racial_innate_spells(char))
    out.extend(feat_granted_spells(char))

    # DM-Granted Bonus Features (dm_rewards.py): unconditional cantrip
    # grants — Gathered Whispers' Spirit Whispers (Message) and Living
    # Shadow's Grasping Shadow (Mage Hand).
    DM_REWARD_CANTRIPS = {"Gathered Whispers": "Message", "Living Shadow": "Mage Hand"}
    for reward_name in char.get("dm_rewards", []):
        if reward_name in DM_REWARD_CANTRIPS:
            out.append(DM_REWARD_CANTRIPS[reward_name])

    # Primal Awareness (Ranger, TCE optional, replaces Primeval Awareness).
    ranger_lvl_pa = cl.get("Ranger", 0)
    pa_enabled = (char.get("_choices", {}).get("optional_features", {}).get("Primal Awareness", False)
                  or char.get("optional_rules", {}).get("primal_awareness", False))
    if pa_enabled:
        PRIMAL_AWARENESS_SPELLS = {
            3: "Speak with Animals", 5: "Beast Sense", 9: "Speak with Plants",
            13: "Locate Creature", 17: "Commune with Nature",
        }
        for req_lvl, sp_name in PRIMAL_AWARENESS_SPELLS.items():
            if ranger_lvl_pa >= req_lvl:
                out.append(sp_name)

    # Player-chosen racial cantrips (High Elf / Half-Elf High Descent /
    # Astral Elf) — the choice itself is made via the level-up panel's
    # race choosers; this just reads back whatever was picked.
    choices = char.get("_choices", {})
    for choice_id in ("race_wizard_cantrip", "astral_elf_cantrip", "race_merfolk_cantrip", "race_sorcerer_cantrip"):
        picked = choices.get(choice_id, [])
        if picked:
            out.append(picked[0])

    # Blessed Warrior (Paladin) / Druidic Warrior (Ranger) fighting styles
    # each grant 2 cantrips from another class's list — stored under keys
    # like "Paladin_cleric_cantrips" / "Ranger_druid_cantrips" by the
    # level-up panel's chooser.
    for key, picked in choices.items():
        if key.endswith("_cantrips") and ("_cleric_" in key or "_druid_" in key):
            out.extend(picked)

    # Pact of the Tome's Book of Shadows cantrips (Warlock) don't count
    # against the normal cantrip limit, per the actual rule text.
    out.extend(choices.get("pact_of_the_tome_cantrips", []))
    out.extend(choices.get("book_of_ancient_secrets_rituals", []))

    # Pact of the Chain (Warlock): grants find familiar as a bonus
    # spell that doesn't count against spells known, per the real rule text.
    pact_choice_val = choices.get("warlock_pact_boon", [])
    if pact_choice_val and "chain" in pact_choice_val[0].lower():
        out.append("Find Familiar")

    # 3 newly-added Eldritch Invocations that grant real, castable
    # spells — use the same bonus_spells mechanism as everything else
    # in this function, so they show up as actual, usable spells rather
    # than a passive note. (Armor of Shadows is handled differently,
    # directly in AC math, since it doesn't need to be "cast.")
    known_invocations = char.get("eldritch_invocations", [])
    inv_names = [inv.split(" (")[0].strip() for inv in known_invocations]
    if "Shroud of Shadow" in inv_names:
        out.append("Invisibility")
    if "Gift of the Depths" in inv_names:
        out.append("Water Breathing")
    if "Thief of Five Fates" in inv_names:
        out.append("Bane")

    # Ritual Caster (feat): 2 chosen 1st-level ritual spells, always prepared.
    out.extend(choices.get("feat_ritual_caster_spells", []))

    # Firbolg Magic.
    if (char.get("species") or char.get("race", "")).lower() == "firbolg":
        out.extend(["Detect Magic", "Disguise Self"])

    # Lunar Sorcery (Sorcerer).
    from dnd_app.core.calculator import class_levels, subclasses
    if "lunar" in subclasses(char).get("Sorcerer", "").lower():
        sorc_lvl = class_levels(char).get("Sorcerer", 0)
        # Moon Fire (1st level): Sacred Flame, doesn't count against
        # cantrips known.
        if sorc_lvl >= 1:
            out.append("Sacred Flame")
        # Lunar Spells table: every spell up to the character's current
        # tier is learned across all three phases, per the actual rule
        # text ("You learn additional spells... each of these spells
        # counts as a sorcerer spell for you").
        LUNAR_SPELLS = {
            1: ["Shield", "Ray of Sickness", "Color Spray"],
            3: ["Lesser Restoration", "Blindness/Deafness", "Alter Self"],
            5: ["Dispel Magic", "Vampiric Touch", "Phantom Steed"],
            7: ["Death Ward", "Confusion", "Hallucinatory Terrain"],
            9: ["Telepathic Bond", "Hold Monster", "Mislead"],   # the SRD name, as in ALL_SPELLS
        }
        for tier, tier_spells in LUNAR_SPELLS.items():
            if sorc_lvl >= tier:
                out.extend(tier_spells)

    # Pact of the Chain's find familiar grant (Warlock) doesn't count
    # against normal spells known, per the actual rule text.
    pact_choice = choices.get("warlock_pact_boon", [])
    if pact_choice and "chain" in pact_choice[0].lower():
        out.append("Find Familiar")

    # Guiding Whispers (Bard, College of Spirits, 3rd level): Guidance,
    # not counted against cantrips known
    for c in char.get("classes", []):
        if c.get("class") == "Bard" and c.get("level", 0) >= 3 and "spirits" in (c.get("subclass") or "").lower():
            out.append("Guidance")

    return list(dict.fromkeys(out))  # dedupe, preserve order


# ── Spells of the Mark ───────────────────────────────────────────────────
# A genuinely different mechanic from everything else in this file: these
# spells aren't granted directly. Per the real text ("If you have the
# Spellcasting or Pact Magic class feature, the spells on the [Mark]
# Spells table are added to the spell list of your spellcasting class"),
# they're ADDED to what a spellcasting class can choose to learn/prepare
# — the character still has to spend a normal known/prepared slot on one
# to actually get it, same as any other spell on their list.
#
# Structure: {(race, subrace): {spell_level: [spell names]}}
MARK_EXPANDED_SPELLS = {
    # (Mordenkainen's Faithful Hound and Private Sanctum aren't in the spell
    # catalog yet, so they can't be picked until they are)
    ("Dwarf", "Mark of Warding"): {
        1: ["Alarm", "Armor of Agathys"], 2: ["Arcane Lock", "Knock"],
        3: ["Glyph of Warding", "Magic Circle"],
        4: ["Leomund's Secret Chest", "Mordenkainen's Faithful Hound"], 5: ["Antilife Shell"],
    },
    ("Elf", "Mark of Shadow"): {
        1: ["Disguise Self", "Silent Image"], 2: ["Darkness", "Pass without Trace"],
        3: ["Clairvoyance", "Major Image"], 4: ["Greater Invisibility", "Hallucinatory Terrain"],
        5: ["Mislead"],
    },
    ("Gnome", "Mark of Scribing"): {
        1: ["Comprehend Languages", "Illusory Script"], 2: ["Animal Messenger", "Silence"],
        3: ["Sending", "Tongues"], 4: ["Arcane Eye", "Confusion"], 5: ["Dream"],
    },
    ("Half-Elf", "Mark of Detection"): {
        1: ["Detect Evil and Good", "Detect Poison and Disease"], 2: ["Detect Thoughts", "Find Traps"],
        3: ["Clairvoyance", "Nondetection"], 4: ["Arcane Eye", "Divination"], 5: ["Legend Lore"],
    },
    ("Half-Elf", "Mark of Storm"): {
        1: ["Feather Fall", "Fog Cloud"], 2: ["Gust of Wind", "Levitate"],
        3: ["Sleet Storm", "Wind Wall"], 4: ["Conjure Minor Elementals", "Control Water"],
        5: ["Conjure Elemental"],
    },
    ("Half-Orc", "Mark of Finding"): {
        1: ["Faerie Fire", "Longstrider"], 2: ["Locate Animals or Plants", "Locate Object"],
        3: ["Clairvoyance", "Speak with Plants"], 4: ["Divination", "Locate Creature"],
        5: ["Commune with Nature"],
    },
    ("Human", "Mark of Finding"): {
        1: ["Faerie Fire", "Longstrider"], 2: ["Locate Animals or Plants", "Locate Object"],
        3: ["Clairvoyance", "Speak with Plants"], 4: ["Divination", "Locate Creature"],
        5: ["Commune with Nature"],
    },
    ("Halfling", "Mark of Healing"): {
        1: ["Cure Wounds", "Healing Word"], 2: ["Lesser Restoration", "Prayer of Healing"],
        3: ["Aura of Vitality", "Mass Healing Word"], 4: ["Aura of Purity", "Aura of Life"],
        5: ["Greater Restoration"],
    },
    ("Halfling", "Mark of Hospitality"): {
        1: ["Goodberry", "Sleep"], 2: ["Aid", "Calm Emotions"],
        3: ["Create Food and Water", "Leomund's Tiny Hut"],
        4: ["Aura of Purity", "Mordenkainen's Private Sanctum"], 5: ["Hallow"],
    },
    ("Human", "Mark of Handling"): {
        1: ["Animal Friendship", "Speak with Animals"], 2: ["Beast Sense", "Calm Emotions"],
        3: ["Beacon of Hope", "Conjure Animals"], 4: ["Aura of Life", "Dominate Beast"], 5: ["Awaken"],
    },
    ("Human", "Mark of Making"): {
        1: ["Identify", "Tenser's Floating Disk"], 2: ["Continual Flame", "Magic Weapon"],
        3: ["Conjure Barrage", "Elemental Weapon"], 4: ["Fabricate", "Stone Shape"], 5: ["Creation"],
    },
    ("Human", "Mark of Passage"): {
        1: ["Expeditious Retreat", "Jump"], 2: ["Misty Step", "Pass without Trace"],
        3: ["Blink", "Phantom Steed"], 4: ["Dimension Door", "Freedom of Movement"],
        5: ["Teleportation Circle"],
    },
    ("Human", "Mark of Sentinel"): {
        1: ["Compelled Duel", "Shield of Faith"], 2: ["Warding Bond", "Zone of Truth"],
        3: ["Counterspell", "Protection from Energy"], 4: ["Death Ward", "Guardian of Faith"],
        5: ["Bigby's Hand"],
    },
}


def get_mark_expanded_spells(char: dict) -> set[str]:
    """Return every spell name added to the character's spellcasting-class
    spell list by a racial Mark, regardless of spell level (the level cap
    for actually learning one is enforced elsewhere, same as any other
    spell) — used to widen the class-spell-list eligibility check, not to
    grant anything directly."""
    species = char.get("species") or char.get("race", "")
    subrace = char.get("subrace", "") or ""
    out = set()
    for (race_key, subrace_key), by_level in MARK_EXPANDED_SPELLS.items():
        # Same prefix check as get_bonus_spells() above -- "Elf" is a
        # substring of "Half-Elf", so a plain containment check could
        # match the wrong race/subrace pair.
        if not species.lower().startswith(race_key.lower()):
            continue
        if not subrace.lower().startswith(subrace_key.lower()):
            continue
        for spells in by_level.values():
            out.update(spells)
    return out
