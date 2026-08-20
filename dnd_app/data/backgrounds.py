"""
D&D 5e Backgrounds
Each background: name, skills (2), tools (list), languages (int = # free),
feature (name + desc), source, equipment.
Personality traits/ideals/bonds/flaws are handled as free-text player
input elsewhere (Backstory tab), not background-specific roll tables.

Author: Ethan O'Brien
Date: 2026-08-20
"""

def bg(name, skills, tools=None, languages=0, feature="", feature_desc="",
       source="PHB 2014", origin_feat=None, equipment="", notes="",
       feat_choices=None):
    return dict(name=name, skills=skills, tools=tools or [], languages=languages,
                feature=feature, feature_desc=feature_desc,
                source=source, origin_feat=origin_feat,
                equipment=equipment, notes=notes,
                feat_choices=list(feat_choices) if feat_choices else [])



ALL_BACKGROUNDS = [

    # ── PHB 2014 ──────────────────────────────────────────────────────────────
    bg("Acolyte",
       skills=["Insight", "Religion"],
       languages=2,
       feature="Shelter of the Faithful",
       feature_desc='You and your adventuring companions can receive free healing and care at a temple, shrine, or other established presence of your faith, though you must provide any material components needed for spells. Those who share your religion will support you at a modest lifestyle. You have ties to a specific temple where you have a residence, and you can call on the priests there for assistance (though they are not obligated to help with anything dangerous or illegal).',
       equipment="Holy symbol, prayer book/wheel, 5 sticks incense, vestments, common clothes, 15 gp"),

    bg("Charlatan",
       skills=["Deception", "Sleight of Hand"],
       tools=["Disguise kit", "Forgery kit"],
       feature="False Identity",
       feature_desc="You have created a second identity including documentation, established "
                    "acquaintances, and disguises that let you assume that persona. You can also "
                    "forge documents, including official papers and personal letters, as long as "
                    "you've seen an example of the kind of document or the handwriting you're "
                    "trying to copy.",
       equipment="Fine clothes, disguise kit, tools of the con, 15 gp"),

    bg("Criminal",
       skills=["Deception", "Stealth"],
       tools=["Gaming set", "Thieves' tools"],
       feature="Criminal Contact",
       feature_desc='You have a reliable and trustworthy contact who acts as your liaison to a network of criminals. You know how to get messages to and from this contact even over great distances. As part of this network, you can arrange to receive criminal services — from information about targets to fences for stolen goods — though such services come at a cost (in gold, favors, or both). The nature of your criminal specialty shapes which services are most accessible to you.',
       equipment="Crowbar, dark common clothes with hood, 15 gp"),

    bg("Entertainer",
       skills=["Acrobatics", "Performance"],
       tools=["Disguise kit", "Musical instrument"],
       feature="By Popular Demand",
       feature_desc="You can always find a place to perform — an inn common room, a tavern, a great lord's court, or wherever people gather. At such a venue, you receive free lodging and food of a modest standard, as long as you perform each night. Your performance also makes you something of a local celebrity, and strangers may recognize you as an entertainer, though this cuts both ways — fans and critics alike may seek you out.",
       equipment="Musical instrument, favor of an admirer, costume, 15 gp"),

    bg("Folk Hero",
       skills=["Animal Handling", "Survival"],
       tools=["Artisan's tools", "Vehicles (land)"],
       feature="Rustic Hospitality",
       feature_desc="Since you come from the ranks of the common folk, you fit in among them "
                    "with ease. You can find a place to hide, rest, or recuperate among other "
                    "commoners, unless you have shown yourself to be a danger to them. They will "
                    "shield you from the law or anyone else searching for you, though they will "
                    "not risk their lives for you.",
       equipment="Artisan's tools, shovel, iron pot, common clothes, 10 gp"),

    bg("Guild Artisan",
       skills=["Insight", "Persuasion"],
       tools=["Artisan's tools (specialty)"],
       languages=1,
       feature="Guild Membership",
       feature_desc="As an established, respected member of a guild, your fellow members provide "
                    "you with lodging and food if necessary, and will pay for your funeral if "
                    "needed. Guilds often wield tremendous political power: if you're accused of a "
                    "crime, your guild will support you if a good case can be made for your "
                    "innocence or the crime is justifiable, and you can gain access to powerful "
                    "political figures through the guild. Such connections might require a "
                    "donation of money or magic items to the guild's coffers. You must pay dues "
                    "of 5 gp per month; missed payments must be made up to remain in good graces.",
       equipment="Artisan's tools, letter of introduction, traveler's clothes, 15 gp"),

    bg("Hermit",
       skills=["Medicine", "Religion"],
       tools=["Herbalism kit"],
       languages=1,
       feature="Discovery",
       feature_desc='The quiet seclusion of your extended hermitage gave you access to a powerful discovery. The exact nature of this revelation depends on your background. It might be a great truth about the cosmos, the deities, the powerful beings of the outer planes, or the forces of nature. It could be a site that no one else has ever seen. You might have uncovered a fact that has long been forgotten, or that was intentionally hidden. Work with your DM to determine the details and how this revelation might reshape society, a faction, or even the planes if the wrong (or right) people were to learn of it.',
       equipment="Scroll case with notes, winter blanket, common clothes, herbalism kit, 5 gp"),

    bg("Noble",
       skills=["History", "Persuasion"],
       tools=["Gaming set"],
       languages=1,
       feature="Position of Privilege",
       feature_desc='Thanks to your noble birth, people are inclined to think the best of you. You are welcome in high society, and people assume you have the right to be wherever you are. The common folk make every effort to accommodate you and avoid your displeasure, and other people of high birth treat you as a member of the same social sphere. You can secure an audience with a local noble if you need to. Your title carries weight even in lands where your family is not known, though earning real trust requires more than a title.',
       equipment="Fine clothes, signet ring, scroll of pedigree, 25 gp"),

    bg("Outlander",
       skills=["Athletics", "Survival"],
       tools=["Musical instrument"],
       languages=1,
       feature="Wanderer",
       feature_desc="You have an excellent memory for maps and geography, and you can always "
                    "recall the general layout of terrain, settlements, and other features around "
                    "you. In addition, you can find food and fresh water for yourself and up to "
                    "five other people each day, provided that the land offers berries, small "
                    "game, water, and so forth.",
       equipment="Staff, hunting trap, animal trophy, traveler's clothes, 10 gp"),

    bg("Sage",
       skills=["Arcana", "History"],
       languages=2,
       feature="Researcher",
       feature_desc='When you attempt to learn or recall a piece of lore, if you do not know the information, you often know where and from whom you can obtain it. Usually, this information comes from a library, scriptorium, university, or a sage or other learned person or creature. Your DM might rule that the knowledge you seek is secreted away in an almost inaccessible place, or that it simply cannot be found. Unearthing the deepest secrets of the multiverse can require an adventure or even a whole campaign.',
       equipment="Bottle of ink, quill, small knife, letter with unanswered question, common clothes, 10 gp"),

    bg("Sailor",
       skills=["Athletics", "Perception"],
       tools=["Navigator's tools", "Vehicles (water)"],
       feature="Ship's Passage",
       feature_desc="When you need to, you can secure free passage on a sailing ship for yourself and your adventuring companions. You might sail on the ship you served on, or another ship you have good relations with. Because you're calling in a favor, you can't be certain of a schedule or route that will meet your every need. In return for free passage, you and your companions are expected to assist the crew during the voyage. The DM determines how far out of the way the ship's ports of call are from your destination, and how long it takes to reach those ports.",
       equipment="Belaying pin (club), 50 ft silk rope, lucky charm, common clothes, 10 gp"),

    bg("Soldier",
       skills=["Athletics", "Intimidation"],
       tools=["Gaming set", "Vehicles (land)"],
       feature="Military Rank",
       feature_desc='You have a military rank from your career as a soldier. Soldiers loyal to your former military organization still recognize your authority and influence, and they defer to you if they are of a lower rank. You can invoke your rank to exert influence over other soldiers and requisition simple equipment or horses for temporary use. You can also usually gain access to friendly military encampments and fortresses where your rank is recognized.',
       equipment="Insignia of rank, enemy trophy, deck of cards/dice, common clothes, 10 gp"),

    bg("Urchin",
       skills=["Sleight of Hand", "Stealth"],
       tools=["Disguise kit", "Thieves' tools"],
       feature="City Secrets",
       feature_desc="You know the secret patterns and flows of cities and can find passages "
                    "through the urban sprawl that others would miss. When you are not in "
                    "combat, you (and companions you lead) can travel between any two locations "
                    "in a city twice as fast as your speed would normally allow.",
       equipment="Small knife, map of home city, pet mouse, token from parents, common clothes, 10 gp"),

    # ── Supplemental (SCAG, XGE, etc.) ───────────────────────────────────────
    bg("Anthropologist", source='ToA',
       skills=["Insight", "Religion"],
       languages=2,
       feature="Adept Linguist",
       feature_desc="You can communicate with humanoids who don't speak any language you know. "
                    "After observing them interact with one another for at least 1 day, you learn "
                    "a handful of important words, expressions, and gestures — enough to "
                    "communicate on a rudimentary level. You've also adopted a foreign culture "
                    "(race of your choice) that shapes your beliefs and customs.",
       equipment="Leather-bound diary, bottle of ink, ink pen, traveler's clothes, a trinket, 10 gp"),

    bg("Archaeologist", source="ToA",
       skills=["History", "Survival"],
       tools=["Cartographer's tools or Navigator's tools"],
       languages=1,
       feature="Historical Knowledge",
       feature_desc="When you enter a ruin or dungeon, you can correctly ascertain its original "
                    "purpose and determine its builders (dwarves, elves, humans, yuan-ti, or "
                    "another known race). You can also determine the monetary value of art "
                    "objects more than a century old.",
       equipment="Wooden case with a map to a ruin or dungeon, bullseye lantern, miner's pick, "
                 "traveler's clothes, shovel, two-person tent, a trinket, 25 gp"),

    bg("City Watch", source="SCAG",
       skills=["Athletics", "Insight"],
       languages=2,
       feature="Watcher's Eye",
       feature_desc="Your experience enforcing the law gives you a feel for local laws and "
                    "criminals. You can easily find the local outpost of the watch or a similar "
                    "organization, and just as easily pick out the dens of criminal activity in a "
                    "community — though you're more likely to be welcome in the former than the "
                    "latter.",
       equipment="Uniform, horn, manacles, 10 gp"),

    bg("Clan Crafter", source="SCAG",
       skills=["History", "Insight"],
       tools=["Artisan's tools"],
       languages=1,
       feature="Respect of the Stout Folk",
       feature_desc='You are respected among dwarves and others who value skilled craft. Non-dwarf artisans treat you as a peer, and dwarves give you special respect. You can find lodging and food among dwarven communities for free. If you bring gifts of well-made goods worth at least 1 gp per day, dwarves will house and feed you for up to a week.',
       equipment="A set of artisan's tools (your choice), maker's mark chisel, traveler's clothes, letter of introduction from your clan, 5 gp"),

    bg("Cloistered Scholar", source="SCAG",
       skills=["History", "one of: Arcana, Nature, Religion"],
       languages=2,
       feature="Library Access",
       feature_desc='Though others must often endure extensive negotiations and research to gain access to libraries and other collections of lore, you have free access to the collection of a specific library you have chosen. Other scholars of the Sword Coast will speak with you as a peer, and you are welcome at most academic institutions. You might need to negotiate access to a particularly restricted section — a rare room, a restricted archive, or a dangerous specimen — but common academic resources are open to you freely.',
       equipment="Writing supplies, letters of introduction, scholar's robes, 10 gp"),

    bg("Courtier", source="SCAG",
       skills=["Insight", "Persuasion"],
       languages=2,
       feature="Court Functionary",
       feature_desc='Your experience navigating court politics gives you access to the rich and powerful. You know the ins and outs of bureaucracy and can always find the right person to talk to. Given a day in a new city, you can identify the most important nobles, merchants, and officials and arrange meetings with them.',
       equipment="Fine clothes, 5 gp"),

    bg("Far Traveler", source="SCAG",
       skills=["Insight", "Perception"],
       tools=["Musical instrument or gaming set"],
       languages=1,
       feature="All Eyes on You",
       feature_desc='Your accent, mannerisms, and clothing mark you as foreign, which makes you a curiosity. People notice you; nobles may invite you to their courts, merchants want to trade exotic goods, and commoners are fascinated by tales of distant lands. You can always secure an audience with a local noble, merchant prince, or mayor who is curious about your homeland — though their reactions are unpredictable.',
       equipment="Traveler's clothes, maps of home, small jewelry piece worth 10 gp, 5 gp"),

    bg("Fisher", source="GoS",
       skills=["History", "Survival"],
       tools=["Vehicles (water)"],
       languages=1,
       feature="Harvest the Water",
       feature_desc="You gain advantage on ability checks made using fishing tackle. If you have "
                    "access to a body of water that sustains marine life, you can maintain a "
                    "moderate lifestyle while working as a fisher, catching enough food to feed "
                    "yourself and up to 10 other people each day. Fishing Tale: once a day, you "
                    "can tell a compelling tale (tall or true) to willing listeners; some may "
                    "become friendly toward you at the DM's discretion.",
       equipment="Fishing tackle, net, favorite fishing lure or wading boots, traveler's clothes, 10 gp"),

    bg("Haunted One", source="CoS",
       skills=["Choose 2: Arcana, Investigation, Religion, or Survival"],
       languages=2,
       feature="Heart of Darkness",
       feature_desc="Those who look into your eyes can see that you have faced unimaginable "
                    "horror and that you are no stranger to darkness. Though they might fear you, "
                    "commoners will extend you every courtesy and do their utmost to help you. "
                    "Unless you have shown yourself to be a danger to them, they will even take up "
                    "arms to fight alongside you, should you find yourself facing an enemy alone.",
       equipment="Monster hunter's pack (chest, crowbar, hammer, 3 stakes, holy symbol, holy water, "
                 "manacles, mirror, oil, tinderbox, 3 torches), common clothes, a trinket, 1 sp",
       notes="Language choice: one must be Abyssal, Celestial, Deep Speech, Draconic, Infernal, "
             "Primordial, Sylvan, or Undercommon.",
       origin_feat=None),

    bg("House Agent", source="ERLW",
       skills=["Investigation", "Persuasion"],
       tools=["Choose two from your House's Tool Proficiencies table"],
       feature="House Connections",
       feature_desc="You can always get food and lodging for yourself and your friends at a house "
                    "enclave. When the house assigns you a mission, it will usually provide the "
                    "necessary supplies and transportation. You have many old friends, mentors, and "
                    "rivals in your house, and may encounter one when interacting with a house "
                    "business — how willing they are to help depends on your current standing.",
       equipment="Fine clothes, house signet ring, identification papers, 20 gp",
       notes="Tool proficiencies depend on your House: Cannith (alchemist's supplies, tinker's "
             "tools); Deneith/Orien (one gaming set, vehicles-land); Ghallanda (brewer's supplies, "
             "cook's utensils); Jorasco (alchemist's supplies, herbalism kit); Kundarak (thieves' "
             "tools, tinker's tools); Lyrandar (navigator's tools, vehicles-sea/air); Medani "
             "(disguise kit, thieves' tools); Phiarlan (disguise kit, one musical instrument); "
             "Sivis (calligrapher's supplies, forgery kit); Tharashk (one gaming set, thieves' "
             "tools); Thuranni (one musical instrument, poisoner's kit); Vadalis (herbalism kit, "
             "vehicles-land)."),

    bg("Investigator", source="VRGtR",
       skills=["Choose 2: Insight, Investigation, or Perception"],
       tools=["Disguise kit", "Thieves' tools"],
       feature="Official Inquiry",
       feature_desc="You're experienced at gaining access to people and places to get the "
                    "information you need. Through fast-talking, determination, and "
                    "official-looking documentation, you can gain access to a place or person "
                    "related to a crime you're investigating. Those uninvolved avoid impeding you "
                    "or pass along your requests. Local law enforcement views you as either a "
                    "nuisance or one of their own.",
       equipment="Magnifying glass, evidence from a past case, common clothes, 10 gp"),

    bg("Knight", source="PHB (variant Noble)",
       skills=["History", "Persuasion"],
       tools=["Gaming set"],
       languages=1,
       feature="Retainers",
       feature_desc='You have three retainers loyal to you: two commoners who serve as servants, and one squire who is a commoner with noble aspirations. Your retainers perform mundane tasks (tending horses, polishing armor, running errands) but will not fight for you and will leave if regularly exposed to danger. They receive modest wages, room, and board from you.',
       equipment="Fine clothes, signet ring, scroll of pedigree, 25 gp"),

    bg("Mercenary Veteran", source="SCAG",
       skills=["Athletics", "Persuasion"],
       tools=["Gaming set", "Vehicles (land)"],
       feature="Mercenary Life",
       feature_desc="You can identify mercenary companies by their emblems, and you know a "
                    "little about any such company, including who has hired them recently. You "
                    "can find the taverns and festhalls where mercenaries abide in any area, as "
                    "long as you speak the language. You can find mercenary work between "
                    "adventures sufficient to maintain a comfortable lifestyle (the Practicing a "
                    "Profession downtime activity).",
       equipment="Uniform, insignia of rank, gaming set, 10 gp"),

    bg("Pirate", source="PHB (variant Sailor)",
       skills=["Athletics", "Perception"],
       tools=["Navigator's tools", "Vehicles (water)"],
       feature="Bad Reputation",
       feature_desc="Your fearsome reputation precedes you. No matter where you go, people let you get away with minor crimes in port cities — intimidating bar patrons, bending harbor regulations, or demanding free drinks. But your reputation also means the authorities watch you closely, and enemies you've made at sea will recognize you on sight.",
       equipment="Belaying pin, 50 ft silk rope, lucky charm, common clothes, 10 gp"),

    bg("Rewarded", source='BOMT',
       skills=["Insight", "Persuasion"],
       languages=1,
       tools=["Gaming set"],
       feature="Fortune's Favor",
       feature_desc="Your unexpected good fortune is reflected by a minor boon. You gain the "
                    "Lucky, Magic Initiate, or Skilled feat (your choice), reflecting the "
                    "transformation that changed your life — an encounter with a genie who "
                    "granted three wishes might manifest as Magic Initiate; paying off your "
                    "family's debts with a fortuitous round of cards might be Lucky; or "
                    "whatever trial secured your new destiny might be represented by Skilled.",
       equipment="Bottle of black ink, ink pen, five sheets of paper, gaming set, signet ring, fine clothes, 18 gp",
       feat_choices=["Lucky", "Magic Initiate", "Skilled"]),

    bg("Ruined", source='BOMT',
       skills=["Stealth", "Survival"],
       languages=1,
       tools=["Gaming set"],
       feature="Still Standing",
       feature_desc="You have weathered ruinous misfortune, and you possess hidden reserves others don't expect. You gain the Alert, Skilled, or Tough feat (your choice). Your choice of feat reflects how you've dealt with the terrible loss that changed your life forever.",
       equipment="Cracked hourglass, rusty manacles, half-empty bottle, hunting trap, gaming set, traveler's clothes, 13 gp",
       feat_choices=["Alert", "Skilled", "Tough"]),

    bg("Sage (Variant: Wizard's Apprentice)", source="PHB",
       skills=["Arcana", "History"],
       languages=2,
       feature="Researcher",
       feature_desc="When you attempt to learn or recall a piece of lore and don't know the information, you know where and from whom you can obtain it. You also have a spellbook with a few spells taught by your master, and you may be able to call on former colleagues for research assistance (though they may want something in return).",
       equipment="Bottle of ink, quill, small knife, common clothes, 10 gp"),

    bg("Sailor (Variant: Pirate)", source="PHB",
       skills=["Athletics", "Perception"],
       tools=["Navigator's tools", "Vehicles (water)"],
       feature="Bad Reputation",
       feature_desc='Your fearsome reputation opens doors that polite society keeps closed. People let you get away with minor crimes in port cities, but your notoriety means the authorities watch you, and enemies from your past recognize you on sight. You know which ports are safe harbors and which have a bounty out for your crew.',
       equipment="Belaying pin, 50 ft rope, common clothes, 10 gp"),

    bg("Shipwright", source="GoS",
       skills=["History", "Perception"],
       tools=["Carpenter's tools", "Vehicles (water)"],
       feature="I'll Patch It!",
       feature_desc="Provided you have carpenter's tools and wood, you can repair a water "
                    "vehicle's hull, restoring hit points equal to 5 \u00d7 your proficiency "
                    "bonus. A vehicle can't be patched by you again until it's been pulled ashore "
                    "and fully repaired.",
       equipment="Carpenter's tools, blank book, ink, ink pen, traveler's clothes, 10 gp"),

    bg("Smuggler", source="GoS",
       skills=["Athletics", "Deception"],
       tools=["Vehicles (water)"],
       feature="Down Low",
       feature_desc="You're acquainted with a network of smugglers willing to help you out of "
                    "tight situations. While in a town, city, or similarly sized community, you "
                    "and your companions can stay for free in safe houses (providing a poor "
                    "lifestyle), and can choose to keep your presence there a secret.",
       equipment="Fancy leather vest or leather boots, common clothes, 15 gp"),

    bg("Urban Bounty Hunter", source="SCAG",
       skills=["Choose 2: Deception, Insight, Persuasion, Stealth"],
       tools=["Choose 2: gaming set, musical instrument, thieves' tools"],
       feature="Ear to the Ground",
       feature_desc="Your work as a bounty hunter in urban environments has left you with an extensive network of contacts in cities — informants, fixers, and people who owe you favors. Through this network you can get in touch with someone in any city you spend at least a day in who knows something about any major criminal or wanted individual you're pursuing. The quality and completeness of information depends on how much coin you're willing to spend.",
       equipment="Clothes appropriate to duties, 20 gp"),

    bg("Uthgardt Tribe Member", source="SCAG",
       skills=["Athletics", "Survival"],
       tools=["Artisan's tools or musical instrument"],
       languages=1,
       feature="Uthgardt Heritage",
       feature_desc="You have an excellent knowledge of not only your tribe's territory, but "
                    "the terrain and natural resources of the rest of the North. You're familiar "
                    "enough with any wilderness area that you can find twice as much food and "
                    "water as you normally would when foraging there. You can also call upon the "
                    "hospitality of your people and those allied with your tribe, often including "
                    "druid circles, tribes of nomadic elves, the Harpers, and priesthoods "
                    "devoted to the gods of the First Circle.",
       equipment="Hunting trap, totemic token or tattoos, traveler's clothes, 10 gp"),

    bg("Waterdhavian Noble", source="SCAG",
       skills=["History", "Persuasion"],
       tools=["Gaming set or musical instrument"],
       languages=1,
       feature="Kept in Style",
       feature_desc="While in Waterdeep or elsewhere in the North, your house sees to your "
                    "everyday needs — your name and signet are sufficient to cover most "
                    "expenses, with inns and taverns recording your debt and sending an "
                    "accounting to your family's estate. This lets you live a comfortable "
                    "lifestyle without paying 2 gp a day for it (or reduces a wealthy/"
                    "aristocratic lifestyle's cost by that much). You can't maintain a less "
                    "affluent lifestyle and pocket the difference — this is a line of credit, "
                    "not an actual monetary reward.",
       equipment="Fine clothes, signet ring, scroll of pedigree, skin of fine zzar or wine, 20 gp"),

    bg("Witchlight Hand", source="WBtW",
       skills=["Performance", "Sleight of Hand"],
       tools=["Disguise kit or one musical instrument"],
       feature="Carnival Fixture",
       feature_desc="The Witchlight Carnival provides you with free, modest lodging and food. "
                    "You may wander the carnival and partake of its many wonders at no cost, "
                    "provided you don't disrupt its shows or cause other trouble.",
       equipment="Disguise kit or musical instrument, deck of cards, costume, a trinket, 8 gp"),

    # ── Adventure-Specific ────────────────────────────────────────────────────
    bg("Astral Drifter",
       skills=["Insight", "Religion"],
       tools=[],
       languages=2,
       feature="Divine Contact",
       feature_desc="You gain the Magic Initiate feat, choosing cleric. In the Astral Sea, you "
                    "crossed paths with a wandering deity who shared one secret or obscure bit of "
                    "cosmic lore with you (work with your DM on the details). Longevity: you are "
                    "20d6 years older than you look, having spent that much time in the Astral Sea "
                    "without aging.",
       origin_feat="Magic Initiate",
       equipment="Traveler's clothes, diary, ink pen, bottle of ink, 10 gp",
       source="SAiS"),

    bg("Faceless",
       skills=["Deception", "Intimidation"],
       tools=["Disguise kit"],
       languages=1,
       feature="Dual Persona",
       feature_desc='You have a well-established alter ego. While using your persona, you have advantage on Charisma (Deception) checks to conceal your true identity. If your persona is publicly known, you can leverage its reputation in social situations — for good or ill. People who know your true identity can spoil the act.',
       equipment="Disguise kit, costume, 10 gp",
       source="BG:DiA"),

    bg("Marine",
       skills=["Athletics", "Survival"],
       tools=["Vehicles (water)", "Vehicles (land)"],
       feature="Steady",
       feature_desc="You can move twice the normal amount of time (up to 16 hours) each day before "
                    "being subject to a forced march's effects. You can also automatically find a "
                    "safe route to land a boat on shore, provided such a route exists.",
       equipment="Dagger that belonged to a fallen comrade, folded flag with your ship/company's symbol, "
                 "traveler's clothes, 10 gp",
       source="GoS"),

    # ── Acquisitions Incorporated ─────────────────────────────────────────────
    bg("Celebrity Adventurer's Scion",
       skills=["Perception", "Performance"],
       tools=["Disguise kit"],
       languages=2,
       feature="Name Dropping",
       feature_desc="You know and have met powerful people across the land, and some might even "
                    "remember you. You might wrangle minor assistance from a major figure in the "
                    "campaign, at the DM's discretion. Common folk treat you with deference, and "
                    "your heritage and stories might be good for a free meal or a place to sleep.",
       equipment="Disguise kit, fine clothes, 30 gp",
       source="AI"),

    bg("Failed Merchant",
       skills=["Investigation", "Persuasion"],
       tools=["Artisan's tools"],
       languages=1,
       feature="Supply Chain",
       feature_desc="From your time as a merchant, you retain connections with wholesalers, "
                    "suppliers, and other merchants and entrepreneurs. You can call upon these "
                    "connections when looking for items or information.",
       equipment="Artisan's tools, merchant's scale, fine clothes, 10 gp",
       source="AI"),

    bg("Gambler",
       skills=["Deception", "Insight"],
       tools=["One gaming set"],
       languages=1,
       feature="Never Tell Me the Odds",
       feature_desc="During downtime activities involving games of chance or figuring odds on the "
                    "best plan, you can get a solid sense of which choice is likely the best one "
                    "and which opportunities seem too good to be true, at the DM's determination.",
       equipment="One gaming set, lucky charm, fine clothes, 15 gp",
       source="AI"),

    bg("Plaintiff",
       skills=["Medicine", "Persuasion"],
       tools=["One type of artisan's tools"],
       languages=1,
       feature="Legalese",
       feature_desc="Your experience with your local legal system gives you a firm knowledge of "
                    "its ins and outs. Even when the law isn't on your side, you can use complex "
                    "legal terms to make people think you know what you're talking about. With "
                    "common folk who don't know better, you might intimidate or deceive your way "
                    "into favors or special treatment.",
       equipment="One set of artisan's tools, fine clothes, 20 gp",
       source="AI"),

    bg("Rival Intern",
       skills=["History", "Investigation"],
       tools=["One type of artisan's tools"],
       languages=1,
       feature="Inside Informant",
       feature_desc="You have connections to your previous employer or other groups you dealt "
                    "with during your previous employment. You can communicate with your contacts, "
                    "gaining information at the DM's discretion.",
       equipment="One set of artisan's tools, a ledger with a useful piece of information, fine clothes, 10 gp",
       source="AI"),

    # ── Explorer's Guide to Wildemount ────────────────────────────────────────
    bg("Grinner",
       skills=["Deception", "Performance"],
       tools=["Musical instrument", "Thieves' tools"],
       feature="Ballad of the Grinning Fool",
       feature_desc="In any city of 10,000+ people on the Menagerie Coast or in the Dwendalian "
                    "Empire, you can play the \"Ballad of the Grinning Fool\" in a major tavern or "
                    "inn; a member of the Golden Grin will find you and shelter you and any "
                    "companions you vouch for (this may be discontinued if it becomes too "
                    "dangerous, at the DM's discretion). Use with caution — not everyone who knows "
                    "the ballad is a friend; some are traitors, counterspies, or agents of tyranny.",
       equipment="Fine clothes, disguise kit, musical instrument, gold-plated smiling-face ring, 15 gp",
       source="EGW"),

    bg("Volstrucker Agent",
       skills=["Deception", "Stealth"],
       tools=["Poisoner's kit"],
       languages=1,
       feature="Shadow Network",
       feature_desc="You have access to the Volstrucker shadow network, letting you communicate "
                    "with other members of the order over long distances. Write a letter in "
                    "special arcane ink (the same ink a wizard uses to scribe spells into a "
                    "spellbook, costing 10 gp per page), address it to a member of the "
                    "Volstrucker, and cast it into a fire — the letter burns to cinders and "
                    "materializes whole again on the person you addressed it to.",
       equipment="Common clothes, black cloak with hood, poisoner's kit, 10 gp",
       source="EGW"),

    # ── Guildmasters' Guide to Ravnica ────────────────────────────────────────
    bg("Azorius Functionary",
       skills=["Insight", "Intimidation"],
       tools=[],
       languages=2,
       feature="Legal Authority",
       feature_desc="Your Azorius status inspires respect and even fear — people mind their "
                    "manners around you and assume you have the right to be wherever you are. "
                    "Showing your insignia gets you an audience with anyone you want to talk to "
                    "(though it may cause problems with lawbreakers). Abusing this privilege can "
                    "get you in serious trouble with your superiors. Azorius Guild Spells (if you "
                    "have Spellcasting or Pact Magic): friends and message are added to your spell "
                    "list, along with command, ensnaring strike, arcane lock, calm emotions, hold "
                    "person, clairvoyance, counterspell, compulsion, divination, and dominate "
                    "person at the appropriate spell levels.",
       equipment="Azorius insignia, scroll of an important law, bottle of blue ink, pen, fine clothes, 10 gp",
       source="GGR"),

    bg("Boros Legionnaire",
       skills=["Athletics", "Intimidation"],
       tools=["Gaming set"],
       languages=1,
       feature="Legion Station",
       feature_desc="You can requisition simple equipment for temporary use, and access any Boros "
                    "garrison in Ravnica to rest safely and receive medical attention. You're paid "
                    "a salary of 1 gp/week which, combined with free garrison lodging, maintains a "
                    "poor lifestyle between adventures. Boros Guild Spells (if you have "
                    "Spellcasting or Pact Magic): fire bolt and sacred flame are added to your "
                    "spell list, along with guiding bolt, heroism, aid, scorching ray, beacon of "
                    "hope, blinding smite, death ward, wall of fire, and flame strike at the "
                    "appropriate spell levels.",
       equipment="Boros insignia, angel feather, tattered Boros banner piece, common clothes, 2 gp",
       notes="Language choice is restricted to one of: Celestial, Draconic, Goblin, or Minotaur.",
       source="GGR"),

    bg("Dimir Operative",
       skills=["Deception", "Stealth"],
       tools=["Disguise kit"],
       languages=1,
       feature="False Identity",
       feature_desc="You have a second identity making you appear to belong to a different guild "
                    "(your secondary guild) — documentation, acquaintances, and disguises to "
                    "assume that persona. You can drop it at will to blend into the guildless "
                    "masses. Dimir Guild Spells (if you have Spellcasting or Pact Magic): encode "
                    "thoughts and mage hand are added to your spell list, along with disguise self, "
                    "sleep, detect thoughts, pass without trace, gaseous form, meld into stone, "
                    "nondetection, arcane eye, freedom of movement, and modify memory at the "
                    "appropriate spell levels.",
       equipment="Dimir insignia, three small knives, dark common clothes, 10 gp",
       source="GGR"),

    bg("Golgari Agent",
       skills=["Nature", "Survival"],
       tools=["Poisoner's kit"],
       languages=1,
       feature="Undercity Paths",
       feature_desc="You know hidden underground pathways to bypass crowds, obstacles, and "
                    "observation. Outside combat, you and companions you lead can travel between "
                    "any two locations in the city at twice normal speed — though the undercity "
                    "has its own dangers, so the journey isn't guaranteed safe. Golgari Guild "
                    "Spells (if you have Spellcasting or Pact Magic): dancing lights and spare the "
                    "dying are added to your spell list, along with entangle, ray of sickness, "
                    "protection from poison, ray of enfeeblement, spider climb, animate dead, "
                    "plant growth, giant insect, grasping vine, cloudkill, and insect plague at "
                    "the appropriate spell levels.",
       equipment="Golgari insignia, poisoner's kit, pet beetle or spider, common clothes, 10 gp",
       notes="Language choice is restricted to one of: Elvish, Giant, or Kraul.",
       source="GGR"),

    bg("Gruul Anarch",
       skills=["Animal Handling", "Athletics"],
       tools=["Herbalism kit"],
       languages=1,
       feature="Rubblebelt Refuge",
       feature_desc="You're intimately familiar with the city's abandoned, overgrown rubblebelts "
                    "and ruined neighborhoods. You can find a place for you and your allies to hide "
                    "or rest there, and can find food and fresh water each day for yourself and up "
                    "to five others. Gruul Guild Spells (if you have Spellcasting or Pact Magic): "
                    "fire bolt and produce flame are added to your spell list, along with compelled "
                    "duel, speak with animals, thunderwave, beast sense, shatter, conjure animals, "
                    "conjure barrage, dominate beast, stoneskin, and destructive wave at the "
                    "appropriate spell levels.",
       equipment="Gruul insignia, hunting trap, herbalism kit, boar skull, beast-hide cloak, traveler's clothes, 10 gp",
       notes="Language choice is restricted to one of: Draconic, Giant, Goblin, or Sylvan.",
       source="GGR"),

    bg("Izzet Engineer",
       skills=["Arcana", "Investigation"],
       tools=["One artisan's tools"],
       languages=1,
       feature="Urban Infrastructure",
       feature_desc="You have a basic knowledge of building structure, including what's behind "
                    "the walls, and can find blueprints of a specific building to learn its "
                    "construction — entry points, structural weaknesses, or secret spaces. Access "
                    "to this information isn't unlimited, and the guild won't shield you from legal "
                    "trouble it causes. Izzet Guild Spells (if you have Spellcasting or Pact Magic): "
                    "produce flame and shocking grasp are added to your spell list, along with "
                    "chaos bolt, create or destroy water, unseen servant, heat metal, rope trick, "
                    "call lightning, elemental weapon, glyph of warding, conjure minor elementals, "
                    "divination, Otiluke's resilient sphere, animate objects, and conjure elemental "
                    "at the appropriate spell levels.",
       equipment="Izzet insignia, artisan's tools, remains of a failed experiment, hammer, block and tackle, common clothes, 5 gp",
       notes="Language choice is restricted to one of: Draconic, Goblin, or Vedalken.",
       source="GGR"),

    bg("Orzhov Representative",
       skills=["Intimidation", "Religion"],
       tools=[],
       languages=2,
       feature="Leverage",
       feature_desc="You can exert leverage over individuals below you in the guild's hierarchy "
                    "and demand their help — carrying a message, procuring a carriage ride, "
                    "cleaning up a mess — subject to DM discretion on what's reasonable and who's "
                    "available. Your influence grows with your guild status. Orzhov Guild Spells "
                    "(if you have Spellcasting or Pact Magic): friends and guidance are added to "
                    "your spell list, along with command, illusory script, enthrall, ray of "
                    "enfeeblement, zone of truth, bestow curse, speak with dead, spirit guardians, "
                    "blight, death ward, Leomund's secret chest, and geas at the appropriate spell "
                    "levels.",
       equipment="Orzhov insignia, gold coin chain, vestments, fine clothes, 1 pp",
       source="GGR"),

    bg("Rakdos Cultist",
       skills=["Acrobatics", "Performance"],
       tools=["Musical instrument"],
       languages=1,
       feature="Fearsome Reputation",
       feature_desc="People recognize you as Cult of Rakdos and are careful not to draw your "
                    "anger. You can get away with minor criminal offenses — refusing to pay for "
                    "food, breaking down a door — as long as no legal authorities witness it; most "
                    "people are too daunted by you to report you. You also have a preferred "
                    "performance style (fire juggling, spikewheel acrobatics, nightmare clowning, "
                    "etc.). Rakdos Guild Spells (if you have Spellcasting or Pact Magic): fire bolt "
                    "and vicious mockery are added to your spell list, along with burning hands, "
                    "dissonant whispers, hellish rebuke, crown of madness, enthrall, flaming "
                    "sphere, fear, haste, confusion, wall of fire, and dominate person at the "
                    "appropriate spell levels.",
       equipment="Rakdos insignia, musical instrument, costume, hooded lantern, spiked chain, tinderbox, 10 torches, common clothes, 10 gp",
       notes="Language choice is restricted to one of: Abyssal or Giant.",
       source="GGR"),

    bg("Selesnya Initiate",
       skills=["Nature", "Persuasion"],
       tools=["Artisan's tools or musical instrument"],
       languages=1,
       feature="Conclave's Shelter",
       feature_desc="You and your companions can find shelter or rest at any Selesnya enclave in "
                    "the city (unless you've proven a danger to them); the enclave will shield you "
                    "from the law or other pursuers, though members won't risk their lives for you. "
                    "You can also receive free healing and care there, though you must provide any "
                    "material components needed. Selesnya Guild Spells (if you have Spellcasting or "
                    "Pact Magic): druidcraft and friends are added to your spell list, along with "
                    "animal friendship, charm person, aid, animal messenger, calm emotions, warding "
                    "bond, plant growth, speak with plants, aura of life, conjure minor elementals, "
                    "awaken, and commune with nature at the appropriate spell levels.",
       equipment="Selesnya insignia, healer's kit, robes, common clothes, 5 gp",
       notes="Language choice is restricted to one of: Elvish, Loxodon, or Sylvan.",
       source="GGR"),

    bg("Simic Scientist",
       skills=["Arcana", "Medicine"],
       tools=[],
       languages=2,
       feature="Researcher",
       feature_desc="When you try to recall a magical or scientific fact you don't know, you know "
                    "where and from whom to obtain it — usually a Simic lab, sometimes an Izzet "
                    "facility, library, university, or independent scholar. Knowing where to look "
                    "doesn't guarantee access; you may need to offer bribes or favors. You're also "
                    "part of a research clade or project (protection, movement, metamagic, guard "
                    "creatures, counterintelligence, or independent research). Simic Guild Spells "
                    "(if you have Spellcasting or Pact Magic): acid splash and druidcraft are added "
                    "to your spell list, along with detect poison and disease, expeditious retreat, "
                    "jump, alter self, enhance ability, enlarge/reduce, gaseous form, water "
                    "breathing, wind wall, freedom of movement, polymorph, and creation at the "
                    "appropriate spell levels.",
       equipment="Simic insignia, commoner's clothes, research notes book, ink pen, various vials and specimens, 10 gp",
       source="GGR"),

    # ── Mythic Odysseys of Theros ─────────────────────────────────────────────
    bg("Athlete",
       skills=["Athletics", "Acrobatics"],
       tools=["Vehicles (land)"],
       languages=1,
       feature="Echoes of Victory",
       feature_desc="When visiting any settlement within 100 miles of where you grew up, there's a "
                    "50% chance you find someone who admires you and offers information or "
                    "temporary shelter. Between adventures, you can compete in athletic events to "
                    "maintain a comfortable lifestyle (as the Practicing a Profession downtime "
                    "activity). You also have a Favored Event — a specific sport or discipline "
                    "(marathon, wrestling, boxing, chariot race, etc.) you especially excel at.",
       equipment="Bronze discus or leather ball, lucky charm or trophy, traveler's clothes, 10 gp",
       source="MOT"),

    # ── Sword Coast Adventurer's Guide ────────────────────────────────────────
    bg("Faction Agent",
       skills=["Insight", "one from: Arcana, Deception, History, Intimidation, Investigation, Medicine, Nature, Perception, Performance, Persuasion, Religion, Survival"],
       tools=[],
       languages=2,
       feature="Safe Haven",
       feature_desc="As a faction agent, you have access to a secret network of supporters and "
                    "operatives who can provide assistance on your adventures. You know a set of "
                    "secret signs and passwords to identify such operatives, who can provide "
                    "access to a hidden safe house, free room and board, or assistance finding "
                    "information. These agents never risk their lives for you or risk revealing "
                    "their true identities.",
       equipment="Faction badge, faction book, common clothes, 15 gp",
       source="SCAG"),

    bg("Inheritor",
       skills=["Survival", "one from: Arcana, History, Religion"],
       tools=["Gaming set or Musical instrument"],
       languages=1,
       feature="Inheritance",
       feature_desc="You are the heir to something of great value — not merely in terms of gold, but in terms of importance to the world. You don't know exactly where the inherited thing came from, why it's important, or who might want it. The DM works with you to determine the specifics. Your inheritance might be a family weapon, an old letter, a map of a dungeon, or a prophecy. Whatever it is, it has made you the target of those who want what you have.",
       equipment="Inheritance item (or clues to it), traveler's clothes, 15 gp",
       source="SCAG"),

    bg("Knight of the Order",
       skills=["Persuasion", "one from: Arcana, History, Nature, Religion"],
       tools=["Gaming set or Musical instrument"],
       languages=1,
       feature="Knightly Regard",
       feature_desc="You receive shelter and succor from members of your knightly order and "
                    "those sympathetic to its aims. If your order is religious, you can gain aid "
                    "from temples and religious communities of your deity; civic orders get help "
                    "from the community they serve; philosophical orders find help from those "
                    "they've aided in pursuit of their ideals. This comes as shelter, meals, and "
                    "healing when appropriate, plus occasionally riskier assistance — local "
                    "citizens rallying to aid a sorely pressed knight, or supporters helping "
                    "smuggle a knight out of town when unjustly hunted.",
       equipment="Order signet ring, order banner, traveler's clothes, 10 gp",
       source="SCAG"),

    # ── Baldur's Gate variants ─────────────────────────────────────────────────
    bg("Baldur's Gate Acolyte", source="BGDiA",
       skills=["Insight", "Religion"],
       languages=2,
       feature="Shelter of the Faithful",
       feature_desc="As an acolyte, you command the respect of those who share your faith, and "
                    "can perform its religious ceremonies. You and your companions can expect "
                    "free healing and care at a temple of your faith (though you must provide "
                    "material components), and those who share your religion support you at a "
                    "modest lifestyle. Baldur's Gate Feature — Religious Community (only in "
                    "Baldur's Gate): you're tightly connected with the city's religious "
                    "community, and know if a deity has a following there, where its faithful "
                    "congregate, and the neighborhoods they typically inhabit.",
       equipment="Holy symbol, prayer book or wheel, incense, vestments, common clothes, 15 gp"),

    bg("Baldur's Gate Charlatan", source="BGDiA",
       skills=["Deception", "Sleight of Hand"],
       tools=["Disguise kit", "Forgery kit"],
       feature="False Identity",
       feature_desc="You've created a second identity including documentation, established "
                    "acquaintances, and disguises to assume that persona, and can forge "
                    "documents as long as you've seen an example of the handwriting or document "
                    "type. Baldur's Gate Feature — Long-Lost Heir (only in Baldur's Gate): you "
                    "imitate Baldurian patriars and nobles smoothly enough to convince even "
                    "suspicious family heads of your authenticity as a long-lost heir to some "
                    "extinguished lineage, and you carry a Watch token letting you alone into "
                    "the Upper City — though a true test of your authenticity is likely to "
                    "reveal the deception.",
       equipment="Fine clothes, disguise kit, tools of the con, 15 gp"),

    bg("Baldur's Gate Criminal", source="BGDiA",
       skills=["Deception", "Stealth"],
       tools=["Gaming set", "Thieves' tools"],
       feature="Criminal Contact",
       feature_desc="You have a reliable, trustworthy contact who acts as your liaison to a "
                    "network of other criminals, and know how to get messages to and from them "
                    "over great distances via local messengers, corrupt caravan masters, and "
                    "seedy sailors. Baldur's Gate Feature — Criminal Connections (only in "
                    "Baldur's Gate): crime is just another business here, so you can arrange a "
                    "meeting with a low-ranking operative of nearly any business, patriar "
                    "family, crew, government institution, or the Guild, who will hear you out "
                    "and may take your request up their chain of command.",
       equipment="Crowbar, dark common clothes with hood, 15 gp"),

    bg("Baldur's Gate Entertainer", source="BGDiA",
       skills=["Acrobatics", "Performance"],
       tools=["Disguise kit", "Musical instrument"],
       feature="By Popular Demand",
       feature_desc="You can always find a place to perform, receiving free lodging and food of "
                    "a modest standard as long as you perform each night, and your performance "
                    "makes you something of a local figure. Baldur's Gate Feature — Backstage "
                    "Pass (only in Baldur's Gate): you can tell what audiences frequent which "
                    "venue, and after a successful performance you may meet an enthusiastic "
                    "member of the crowd — someone of an occupation or social class typical of "
                    "that establishment — who's delighted to talk, and to listen.",
       equipment="Musical instrument, favor of an admirer, costume, 15 gp"),

    bg("Baldur's Gate Folk Hero", source="BGDiA",
       skills=["Animal Handling", "Survival"],
       tools=["Artisan's tools", "Vehicles (land)"],
       feature="Rustic Hospitality",
       feature_desc="You fit in among the common folk with ease, and can find a place to hide, "
                    "rest, or recuperate among commoners, who will shield you from the law "
                    "though not risk their lives for you. Baldur's Gate Feature — Social "
                    "Vengeance (only in Baldur's Gate): having grown up in the Lower or Outer "
                    "City watching patriars flaunt wealth, you know how eager commoners are to "
                    "see a patriar get their due — in a busy part of the Lower or Outer City, "
                    "you can spend 2d10 minutes to convince 1d6 commoners to perform a "
                    "non-illegal act inconveniencing the Watch, the Flaming Fist, a patriar, or "
                    "another wealthy-looking individual.",
       equipment="Artisan's tools, shovel, iron pot, common clothes, 10 gp"),

    bg("Baldur's Gate Guild Artisan", source="BGDiA",
       skills=["Insight", "Persuasion"],
       tools=["Artisan's tools (specialty)"],
       languages=1,
       feature="Guild Membership",
       feature_desc="As a respected guild member, fellow members provide lodging and food if "
                    "necessary and pay for your funeral if needed. Guilds wield political power: "
                    "if accused of a crime, your guild supports you if a good case can be made "
                    "for innocence, and you can gain access to powerful political figures "
                    "through it; you must pay 5 gp/month dues. Baldur's Gate Feature — "
                    "Professional Courtesy (only in Baldur's Gate): choose one of the city's "
                    "three districts (Upper, Lower, or Outer City) where you conduct most "
                    "business — you can seek out crew members there for local gossip and gain "
                    "unimpeded entry to nearly any bank, guild hall, business, workhouse, or "
                    "crew meeting place in that district.",
       equipment="Artisan's tools, letter of introduction, traveler's clothes, 15 gp"),

    bg("Baldur's Gate Hermit", source="BGDiA",
       skills=["Medicine", "Religion"],
       tools=["Herbalism kit"],
       languages=1,
       feature="Discovery",
       feature_desc="Your extended hermitage gave you access to a powerful discovery — a great "
                    "truth, a hidden site, or a long-forgotten fact — whose details you work out "
                    "with your DM. Baldur's Gate Feature — The Real City (only in Baldur's "
                    "Gate): you know the Baldur's Gate most Baldurians ignore — the world of the "
                    "homeless and unfortunate — and where to go in the Lower and Outer City for "
                    "anonymity: a damp bed, a bad meal, and a degree of privacy with no "
                    "questions asked, for as long as you want.",
       equipment="Scroll case with notes, winter blanket, common clothes, herbalism kit, 5 gp"),

    bg("Baldur's Gate Noble", source="BGDiA",
       skills=["History", "Persuasion"],
       tools=["Gaming set"],
       languages=1,
       feature="Position of Privilege",
       feature_desc="Thanks to your noble birth, people assume the best of you and that you "
                    "have the right to be wherever you are; common folk accommodate you, and "
                    "you can secure an audience with a local noble if needed. Baldur's Gate "
                    "Feature — Patriar (only in Baldur's Gate): as a member of one of the "
                    "city's elite families, you pass through the gates without paying tolls, "
                    "mingle among Baldur's Gate nobility unquestioned, and may stay in the "
                    "Upper City after dark without being harassed or evicted; your word is "
                    "accepted over others' without question, and corruption among guards or "
                    "officials tends to work in your favor.",
       equipment="Fine clothes, signet ring, scroll of pedigree, 25 gp"),

    bg("Baldur's Gate Outlander", source="BGDiA",
       skills=["Athletics", "Survival"],
       tools=["Musical instrument"],
       languages=1,
       feature="Wanderer",
       feature_desc="You have an excellent memory for maps and geography, recalling the general "
                    "layout of terrain and settlements, and can find food and fresh water for "
                    "yourself and up to five others each day where the land allows. Baldur's "
                    "Gate Feature — Immigrant Experience (only in Baldur's Gate): you're known "
                    "within the city's immigrant communities, and if you ever need to learn "
                    "about a foreign land, people, tradition, or history, you know where to find "
                    "someone with firsthand experience — likely somewhere in the Outer City.",
       equipment="Staff, hunting trap, animal trophy, traveler's clothes, 10 gp"),

    bg("Baldur's Gate Sage", source="BGDiA",
       skills=["Arcana", "History"],
       languages=2,
       feature="Researcher",
       feature_desc="When you attempt to learn or recall a piece of lore you don't know, you "
                    "often know where and from whom you can obtain it — usually a library, "
                    "scriptorium, university, or a learned person or creature. Baldur's Gate "
                    "Feature — Rumor Monger (only in Baldur's Gate): via your personal rumor "
                    "mill and articles in Baldur's Mouth, you can surmise a great deal about "
                    "Baldurians' secrets. Whenever a noteworthy crime or mysterious happening "
                    "occurs, you immediately have a list of 1d4 suspects who, if not involved, "
                    "have a strong chance of knowing who is.",
       equipment="Bottle of ink, quill, small knife, letter with unanswered question, common clothes, 10 gp"),

    bg("Baldur's Gate Sailor", source="BGDiA",
       skills=["Athletics", "Perception"],
       tools=["Navigator's tools", "Vehicles (water)"],
       feature="Ship's Passage",
       feature_desc="You can secure free passage on a sailing ship for yourself and your "
                    "companions, in exchange for helping the crew during the voyage — though "
                    "you can't be certain of the schedule or route. Baldur's Gate Feature — "
                    "Smuggler's Sense (only in Baldur's Gate): familiar with the docks, "
                    "inspectors, tax collectors, and how cargo and coin flow, you can easily "
                    "hustle cargo ashore or aboard a cooperative ship without attracting "
                    "suspicion or taxation, and you know the movements of the Gray Wavers "
                    "(Flaming Fist harbor guards) and how to operate the city's mechanized "
                    "cranes.",
       equipment="Belaying pin (club), 50 ft silk rope, lucky charm, common clothes, 10 gp"),

    bg("Baldur's Gate Soldier", source="BGDiA",
       skills=["Athletics", "Intimidation"],
       tools=["Gaming set", "Vehicles (land)"],
       feature="Military Rank",
       feature_desc="Soldiers loyal to your former military organization still recognize your "
                    "authority, deferring if of lower rank; you can requisition simple equipment "
                    "or horses for temporary use and access friendly encampments where your "
                    "rank is recognized. Baldur's Gate Feature — City Guard (only in Baldur's "
                    "Gate): you may currently serve in the Flaming Fist or the Watch, gaining "
                    "access to their fortresses/citadel and a line of communication with their "
                    "officers as long as you fulfill regular patrol and training duties (losing "
                    "these benefits, recoverable via a month of renewed service, if you stop). "
                    "You also gain Loyalty Test: from dealing with crooked soldiers, you can "
                    "spot behaviors common to corrupt guards and officers, giving a useful "
                    "(though not foolproof) sense of who might take a bribe, look away from a "
                    "crime, or strictly follow the rules.",
       equipment="Insignia of rank, enemy trophy, deck of cards/dice, common clothes, 10 gp"),

    bg("Baldur's Gate Urchin", source="BGDiA",
       skills=["Sleight of Hand", "Stealth"],
       tools=["Disguise kit", "Thieves' tools"],
       feature="City Secrets",
       feature_desc="You know the secret patterns and flows of cities, letting you (and "
                    "companions you lead) travel between any two locations in a city twice as "
                    "fast as normal when not in combat. Baldur's Gate Feature — Gateguide "
                    "Connection (only in Baldur's Gate): though not a member of the Gateguides "
                    "crew, you've associated with enough of them to know their torch-based "
                    "code — from a torch's lighting, placement, and type on or near a "
                    "structure, you can gather information about those who live or do business "
                    "there, particularly dealings with strangers, Guild or government "
                    "connections, or past history with the Gateguides.",
       equipment="Small knife, map of home city, pet mouse, token from parents, common clothes, 10 gp"),

    # ── Official "Variant" backgrounds ────────────────────────────────────────
    bg("Variant City Watch (Investigator)", source="SCAG",
       skills=["Insight", "Investigation"],
       languages=2,
       feature="Watcher's Eye",
       feature_desc="Your experience enforcing the law gives you a feel for local laws and "
                    "criminals. You can easily find the local outpost of the watch or a similar "
                    "organization, and just as easily pick out the dens of criminal activity in "
                    "a community — though you're more likely to be welcome in the former than "
                    "the latter.",
       equipment="Uniform, horn, manacles, 10 gp"),

    bg("Variant Criminal (Spy)", source="PHB",
       skills=["Deception", "Stealth"],
       tools=["Gaming set", "Thieves' tools"],
       feature="Spy Contact",
       feature_desc="You have a reliable and trustworthy contact who acts as your liaison to a "
                    "network of other spies. You know how to get messages to and from your "
                    "contact, even over great distances — specifically, the local messengers, "
                    "corrupt caravan masters, and seedy sailors who can deliver messages for you.",
       equipment="Crowbar, dark common clothes with hood, 15 gp"),

    bg("Variant Entertainer (Gladiator)", source="PHB",
       skills=["Acrobatics", "Performance"],
       tools=["Disguise kit", "Musical instrument"],
       feature="By Popular Demand",
       feature_desc="You can always find a place to perform in any venue that features combat "
                    "for entertainment — a gladiatorial arena or secret pit fighting club. At "
                    "such a place you receive free lodging and food of a modest or comfortable "
                    "standard, as long as you perform each night, and your performance makes "
                    "you something of a local figure.",
       equipment="Inexpensive but unusual weapon (trident or net), favor of an admirer, costume, 15 gp"),

    bg("Variant Guild Artisan (Guild Merchant)", source="PHB",
       skills=["Insight", "Persuasion"],
       tools=["Artisan's tools, or Navigator's tools, or an additional language"],
       languages=1,
       feature="Guild Membership",
       feature_desc="As an established, respected member of a guild, your fellow members "
                    "provide you with lodging and food if necessary, and will pay for your "
                    "funeral if needed. Guilds often wield tremendous political power: if "
                    "accused of a crime, your guild will support you if a good case can be made "
                    "for your innocence or the crime is justifiable, and you can gain access to "
                    "powerful political figures through the guild. You must pay dues of 5 gp "
                    "per month; missed payments must be made up to remain in good graces.",
       equipment="Artisan's tools (or a mule and cart), letter of introduction, traveler's clothes, 15 gp"),

    bg("Variant Noble (Knight)", source="PHB",
       skills=["History", "Persuasion"],
       tools=["Gaming set"],
       languages=1,
       feature="Retainers",
       feature_desc="You have the service of three retainers loyal to your family, who can be "
                    "attendants or messengers (one might be a majordomo). One retainer is "
                    "specifically a noble who serves as your squire, aiding you in exchange for "
                    "training on their own path to knighthood — a knighthood being among the "
                    "lowest noble titles, but a path to higher status. Your retainers perform "
                    "mundane tasks but don't fight for you, won't follow you into obviously "
                    "dangerous areas, and will leave if frequently endangered or abused.",
       equipment="Fine clothes, signet ring, scroll of pedigree, token from a noble lord/lady, 25 gp"),

    bg("Variant Noble (Retainers)", source="PHB",
       skills=["History", "Persuasion"],
       tools=["Gaming set"],
       languages=1,
       feature="Retainers",
       feature_desc="You have the service of three retainers loyal to your family — commoners "
                    "who can be attendants or messengers (one might be a majordomo). They "
                    "perform mundane tasks for you, but don't fight for you, won't follow you "
                    "into obviously dangerous areas such as dungeons, and will leave if "
                    "frequently endangered or abused.",
       equipment="Fine clothes, signet ring, scroll of pedigree, 25 gp"),

    bg("Variant Sailor (Pirate)", source="PHB",
       skills=["Athletics", "Perception"],
       tools=["Navigator's tools", "Vehicles (water)"],
       feature="Bad Reputation",
       feature_desc="No matter where you go, people are afraid of you due to your reputation. "
                    "In a civilized settlement, you can get away with minor criminal offenses — "
                    "refusing to pay for food, breaking down doors at a local shop — since most "
                    "people won't report your activity to the authorities.",
       equipment="Belaying pin (club), 50 ft silk rope, lucky charm, common clothes, 10 gp"),

    # ── Strixhaven colleges ────────────────────────────────────────────────────
    bg("Lorehold Student", source="SCC",
       skills=["History", "Religion"],
       languages=2,
       feature="Lorehold Initiate",
       feature_desc="You gain the Strixhaven Initiate feat, choosing Lorehold within it. If you "
                    "have Spellcasting or Pact Magic, these spells are added to your "
                    "spellcasting class's spell list (all of them, if multiclassed with "
                    "multiple lists): comprehend languages, identify (1st); borrowed knowledge, "
                    "locate object (2nd); speak with dead, spirit guardians (3rd); arcane eye, "
                    "stone shape (4th); flame strike, legend lore (5th).",
       origin_feat="Strixhaven Initiate",
       equipment="Bottle of ink, ink pen, hammer, hooded lantern, tinderbox, tome of history, school uniform, 15 gp"),

    bg("Prismari Student", source="SCC",
       skills=["Acrobatics", "Performance"],
       tools=["Musical instrument or artisan's tools"],
       languages=1,
       feature="Prismari Initiate",
       feature_desc="You gain the Strixhaven Initiate feat, choosing Prismari within it. If you "
                    "have Spellcasting or Pact Magic, these spells are added to your "
                    "spellcasting class's spell list (all of them, if multiclassed with "
                    "multiple lists): chromatic orb, thunderwave (1st); flaming sphere, kinetic "
                    "jaunt (2nd); haste, water walk (3rd); freedom of movement, wall of fire "
                    "(4th); cone of cold, conjure elemental (5th).",
       origin_feat="Strixhaven Initiate",
       equipment="Bottle of ink, ink pen, artisan's tools or musical instrument, school uniform, 10 gp"),

    bg("Quandrix Student", source="SCC",
       skills=["Arcana", "Nature"],
       tools=["Artisan's tools"],
       languages=1,
       feature="Quandrix Initiate",
       feature_desc="You gain the Strixhaven Initiate feat, choosing Quandrix within it. If you "
                    "have Spellcasting or Pact Magic, these spells are added to your "
                    "spellcasting class's spell list (all of them, if multiclassed with "
                    "multiple lists): entangle, guiding bolt (1st); enlarge/reduce, vortex warp "
                    "(2nd); aura of vitality, haste (3rd); control water, freedom of movement "
                    "(4th); circle of power, passwall (5th).",
       origin_feat="Strixhaven Initiate",
       equipment="Bottle of ink, ink pen, abacus, book of arcane theory, school uniform, 15 gp"),

    bg("Silverquill Student", source="SCC",
       skills=["Intimidation", "Persuasion"],
       languages=2,
       feature="Silverquill Initiate",
       feature_desc="You gain the Strixhaven Initiate feat, choosing Silverquill within it. If "
                    "you have Spellcasting or Pact Magic, these spells are added to your "
                    "spellcasting class's spell list (all of them, if multiclassed with "
                    "multiple lists): dissonant whispers, silvery barbs (1st); calm emotions, "
                    "darkness (2nd); beacon of hope, daylight (3rd); compulsion, confusion "
                    "(4th); dominate person, Rary's telepathic bond (5th).",
       origin_feat="Strixhaven Initiate",
       equipment="Bottle of ink, ink pen, book of poetry, school uniform, 15 gp"),

    bg("Witherbloom Student", source="SCC",
       skills=["Nature", "Survival"],
       tools=["Herbalism kit"],
       languages=1,
       feature="Witherbloom Initiate",
       feature_desc="You gain the Strixhaven Initiate feat, choosing Witherbloom within it. If "
                    "you have Spellcasting or Pact Magic, these spells are added to your "
                    "spellcasting class's spell list (all of them, if multiclassed with "
                    "multiple lists): cure wounds, inflict wounds (1st); lesser restoration, "
                    "wither and bloom (2nd); revivify, vampiric touch (3rd); blight, death ward "
                    "(4th); antilife shell, greater restoration (5th).",
       origin_feat="Strixhaven Initiate",
       equipment="Bottle of ink, ink pen, book on plant identification, iron pot, herbalism kit, school uniform, 15 gp"),

    # ── Unique / setting-specific backgrounds ─────────────────────────────────
    bg("Augen Trust (Spy)", source="GGR",
       skills=["Deception", "Stealth"],
       tools=["Gaming set", "Thieves' tools"],
       feature="Spy Contact",
       feature_desc="You have a reliable and trustworthy contact who acts as your liaison to a "
                    "network of other spies. You know how to get messages to and from your "
                    "contact, even over great distances — specifically, the local messengers, "
                    "corrupt caravan masters, and seedy sailors who can deliver messages for you.",
       equipment="Crowbar, dark common clothes with hood, 15 gp"),

    bg("Cobalt Scholar (Sage)", source="MOT",
       skills=["Arcana", "History"],
       languages=2,
       feature="Researcher",
       feature_desc="When you attempt to learn or recall a piece of lore, if you do not know "
                    "the information, you often know where and from whom you can obtain it — "
                    "usually a library, scriptorium, university, or a sage or other learned "
                    "person or creature. Unearthing the deepest secrets of the multiverse can "
                    "require an adventure or even a whole campaign.",
       equipment="Bottle of ink, quill, small knife, letter with unanswered question, common clothes, 10 gp"),

    bg("Feylost", source="WBtW",
       skills=["Deception", "Survival"],
       tools=["Musical instrument"],
       languages=1,
       feature="Feywild Connection",
       feature_desc="Your mannerisms and knowledge of fey customs are recognized by natives of "
                    "the Feywild, who see you as one of their own — friendly Fey creatures are "
                    "inclined to come to your aid if you're lost or need help there. You also "
                    "bear a Fey Mark, a small physical transformation gained during your stay "
                    "(DM's choice or roll on the Fey Mark table).",
       notes="Language choice: Elvish, Gnomish, Goblin, or Sylvan.",
       equipment="Musical instrument, traveler's clothes, 3 trinkets, 8 gp"),

    bg("Gate Warden", source="PSK",
       skills=["Persuasion", "Survival"],
       languages=2,
       feature="Planar Infusion",
       feature_desc="Living in a gate-town or similar location steeped you in planar energy. "
                    "You gain the Scion of the Outer Planes feat. You also know where to find "
                    "free, modest lodging and food in the community you grew up in.",
       notes="Languages: Abyssal, Celestial, or Infernal recommended.",
       origin_feat="Scion of the Outer Planes",
       equipment="Ring of keys to unknown locks, blank book, ink pen, bottle of ink, traveler's clothes, 10 gp"),

    bg("Giant Foundling", source="BGG",
       skills=["Intimidation", "Survival"],
       languages=2,
       feature="Strike of the Giants",
       feature_desc="You gain the Strike of the Giants feat.",
       notes="Languages: Giant, plus one other of your choice.",
       origin_feat="Strike of the Giants",
       equipment="Backpack, traveler's clothes, small stone or sprig reminding you of home, 10 gp"),

    bg("Knight of Solamnia", source="DSotDQ",
       skills=["Athletics", "Survival"],
       languages=2,
       feature="Squire of Solamnia",
       feature_desc="You gain the Squire of Solamnia feat. The Knights of Solamnia also provide "
                    "you free, modest lodging and food at any of their fortresses or encampments.",
       origin_feat="Squire of Solamnia",
       equipment="Insignia of rank, deck of cards, common clothes, 10 gp"),

    bg("Luxonborn (Acolyte)", source="EGW",
       skills=["Insight", "Religion"],
       languages=2,
       feature="Shelter of the Faithful",
       feature_desc="As an acolyte, you command the respect of those who share your faith, and "
                    "can perform its religious ceremonies. You and your companions can expect "
                    "free healing and care at a temple of your faith (though you must provide "
                    "material components), and those who share your religion support you at a "
                    "modest lifestyle.",
       equipment="Holy symbol, prayer book or wheel, incense, vestments, common clothes, 15 gp"),

    bg("Mage of High Sorcery", source="DSotDQ",
       skills=["Arcana", "History"],
       languages=2,
       feature="Initiate of High Sorcery",
       feature_desc="You gain the Initiate of High Sorcery feat. The Mages of High Sorcery also "
                    "provide free, modest lodging and food indefinitely at any occupied Tower of "
                    "High Sorcery, and for one night at the home of an organization member.",
       origin_feat="Initiate of High Sorcery",
       equipment="Bottle of colored ink, ink pen, common clothes, 10 gp"),

    bg("Myriad Operative (Criminal)", source="AAG",
       skills=["Deception", "Stealth"],
       tools=["Gaming set", "Thieves' tools"],
       feature="Criminal Contact",
       feature_desc="You have a reliable and trustworthy contact who acts as your liaison to a "
                    "network of other criminals. You know how to get messages to and from your "
                    "contact, even over great distances — specifically, the local messengers, "
                    "corrupt caravan masters, and seedy sailors who can deliver messages for you.",
       equipment="Crowbar, dark common clothes with hood, 15 gp"),

    bg("Planar Philosopher", source="PSK",
       skills=["Arcana", "one matching your Sigil faction, or of your choice"],
       languages=2,
       feature="Conviction",
       feature_desc="You gain the Scion of the Outer Planes feat. Members of your organization "
                    "(one of Sigil's twelve factions, or another of your own devising) also "
                    "provide you free, modest lodging and food at any of their holdings or the "
                    "homes of other faction members.",
       origin_feat="Scion of the Outer Planes",
       equipment="Portal key, manifesto of your philosophy, common clothes in faction style, 10 gp (multi-planar coin)"),

    bg("Revelry Pirate (Sailor)", source="SAiS",
       skills=["Athletics", "Perception"],
       tools=["Navigator's tools", "Vehicles (water)"],
       feature="Ship's Passage",
       feature_desc="When you need to, you can secure free passage on a sailing ship for "
                    "yourself and your companions. You might sail on the ship you served on, or "
                    "another ship you have good relations with. In return, you and your "
                    "companions are expected to assist the crew during the voyage.",
       equipment="Belaying pin (club), 50 ft silk rope, lucky charm, common clothes, 10 gp"),

    bg("Rune Carver", source="BGG",
       skills=["History", "Perception"],
       tools=["Artisan's tools"],
       languages=1,
       feature="Rune Shaper",
       feature_desc="You gain the Rune Shaper feat.",
       notes="Language: Giant.",
       origin_feat="Rune Shaper",
       equipment="Artisan's tools, small knife, whetstone, common clothes, 10 gp"),

    bg("Wildspacer", source="AAG",
       skills=["Athletics", "Survival"],
       tools=["Navigator's tools", "Vehicles (space)"],
       feature="Wildspace Adaptation",
       feature_desc="You gain the Tough feat. You also learned to adapt to zero gravity — being "
                    "weightless doesn't impose disadvantage on your melee attack rolls.",
       origin_feat="Tough",
       equipment="Belaying pin (club), traveler's clothes, grappling hook, 50 ft hempen rope, 10 gp"),

]

BACKGROUND_NAMES = [b["name"] for b in ALL_BACKGROUNDS]

def get_background(name: str) -> dict:
    for b in ALL_BACKGROUNDS:
        if b["name"] == name:
            return b
    return None
