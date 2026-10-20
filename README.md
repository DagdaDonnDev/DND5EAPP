<!-- github-only -->
<p align="center">
  <img src="packaging/android/icon.png" width="112" alt="MIMIC's amber d20">
</p>
<!-- /github-only -->

<h1 align="center">MIMIC</h1>

<p align="center">
  <b>A complete D&D 5e character creator and character sheet</b><br>
  for Windows, macOS, Linux and Android — offline, and free
</p>

<!-- github-only -->
<p align="center">
  <img alt="Version 0.3.0" src="https://img.shields.io/badge/version-0.3.0-d4a820?style=for-the-badge">
  <img alt="Runs on Windows, macOS, Linux and Android" src="https://img.shields.io/badge/runs%20on-Windows%20%C2%B7%20macOS%20%C2%B7%20Linux%20%C2%B7%20Android-5b7af5?style=for-the-badge">
  <img alt="D&D 5e, 2014 rules" src="https://img.shields.io/badge/rules-D%26D%205e%20(2014)-d44040?style=for-the-badge">
  <img alt="Works offline" src="https://img.shields.io/badge/works-offline-18b28a?style=for-the-badge">
  <img alt="Built with Python and Qt 6" src="https://img.shields.io/badge/built%20with-Python%20%C2%B7%20Qt%206-8e50d8?style=for-the-badge">
</p>

<p align="center">
  <img src="docs/images/desktop-combat.png" width="72%" alt="The desktop app: a level 5 Sorcerer's Combat tab">
  <img src="docs/images/android-combat.png" width="22%" alt="The Android app: the same character's combat screen">
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#screenshots">Screenshots</a> ·
  <a href="#get-started">Get started</a> ·
  <a href="#build-it-yourself">Build it yourself</a> ·
  <a href="#project-layout">Project layout</a> ·
  <a href="#roadmap">Roadmap</a>
</p>
<!-- /github-only -->

MIMIC puts everything a player needs in one place: races, classes,
subclasses, spells, feats, backgrounds, magic items, companions, Wild Shape
and combat. Build a character, level it up and play it at the table, on
your computer or on your phone, with the same character file.

<!-- github-only -->

| 84 | 14 | 127 | 532 | 138 | 99 | 1,283 | 185 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| races | classes | subclasses | spells | feats | backgrounds | magic items | Wild Shape forms |

<!-- /github-only -->

- **Rules that run** — magic items, invocations, maneuvers, infusions, conditions and rage do what they say, not just show their text
- **One character, both apps** — desktop and Android share one rules engine and one file format
- **Changes clean up after themselves** — level down, swap race or drop a feat, and everything that came with it goes too
- **Dying, resting and casting by the book** — massive damage, death saves, rests, spell slots and concentration
- **Bring your old sheets** — a filled-in official 5e PDF character sheet becomes a full character
- **The sheet feels it too** — colour drains as HP drops, and the screen's edges close in with exhaustion (both optional)
- **Yours, offline** — no account, no internet, free

---

## Features

<details open>
<summary><b>Game content</b> — races, classes, spells, items and more</summary>

- **84 races** with their subraces, plus a custom race. Where a race was reprinted with different rules (Mordenkainen Presents: Monsters of the Multiverse), both versions are there
- **14 classes**, Blood Hunter included, with **127 subclasses**, checked line by line against the source text
- **532 spells** across all nine levels, each on its classes' lists, checked against the reference for level, school, concentration and ritual
- **138 feats** and **99 backgrounds**. The app follows the 2014 rules, so the 2024 origin-feat backgrounds are left out
- **1,283 magic items**, with their mechanics working for over 99% of them
- **Every standard weapon and armour**, with silvered and adamantine versions of each weapon (adamantine for melee weapons only)
- **185 Wild Shape forms**: all 181 beasts from the reference, CR 0 to CR 6, each with its full stat block, plus the four elementals for a Circle of the Moon druid. The list only offers what your druid level and circle allow
- **Companion stat blocks** for the Steel Defender, Wildfire Spirit, Drake Companion, Dancing Item, the Primal Companions and the Eldritch Cannon
- **Natural weapons** for the 11 races that have them (talons, claws, bite, horns, hooves, a Longtooth shifter's fangs), as weapon rows with their attack and damage

</details>

<details>
<summary><b>Building a character</b> — creation, level-ups, multiclassing</summary>

- **A creation wizard** — race, ability scores (point buy, standard array or manual), background, class, spells and equipment
- **Details as you pick** — a subrace updates the ability scores and traits straight away, and a background shows its feature, languages and equipment in full
- **Backgrounds as printed** — what a background lets you choose is asked for on the Choices tab: an Inheritor's second skill, a criminal's gaming set, an entertainer's instrument, a House Agent's house and the two tools it gives
- **Starting equipment** from your class's options and your background, with its gold, straight into your inventory
- **A level-up wizard** for each level's choices, including the ones a choice opens up
- **Multiclassing** with its full rules
- **Level changes stay consistent** — Level Up stops at 20. A class that drops below its subclass level sets the subclass aside, and gets it back when it returns. Buttons that can't apply are greyed out and say why
- **Nothing is left behind** — level down, remove a class, or change race, subrace, background or a feat, and what came with it goes: invocations, maneuvers, infusions, fighting styles, Magical Secrets, a race's cantrip, and any pick those opened up. Level back up and you're asked again
- **Skills follow your character** — expertise and skill picks from a level you no longer have go with it. Your own edits on the Skills tab stay until you reset them
- **Checks add what they should** — Jack of All Trades on plain ability checks, and a Fey Wanderer's skill and Wisdom bonus on Charisma checks
- **DM-granted proficiencies** — any weapon, armour, tool or language your DM gives you, picked from the list or typed in. It counts like any other proficiency

</details>

<details>
<summary><b>Races</b> — traits, skills, languages, dragonmarks</summary>

- **Ability scores as printed** for every race and subrace. Fizban's dragonborn ask for +2/+1 or three +1s
- **Speed as printed** — 25 ft for a dwarf, gnome or halfling, 35 ft for a leonin or satyr, 40 ft for a centaur. Heavy armour you aren't strong enough for costs 10 ft, unless you're a dwarf, and the speed breakdown says so
- **Skills and tools** — the fixed ones are added (a tabaxi's Perception and Stealth, a rock gnome's tinker's tools) and the ones you choose are asked for (Changeling Instincts, Hunter's Lore, a dwarf's artisan's tools, a satyr's instrument)
- **Languages** — the ones your race knows are always there, and the ones of your choice are asked for
- **Variant Human** — +1 to two ability scores of your choice and a feat. Change race and they go, the feat with them
- **Half-elf variants** — a half-elf of elven descent takes one variant feature in place of Skill Versatility; a dragonmarked half-elf has neither
- **Dragonmarks as written** — each mark's ability scores, its spells at the right levels and recharge, its Spells of the Mark added to your class's list, and its d4 intuition as a reminder on the checks it adds to. A mark replaces what its book says (a Mark of Finding half-orc keeps only its darkvision), and the trait list leaves out what's replaced
- **Racial spells as printed** — each race's spells at the right levels, and how its book casts them: a tiefling's 2nd-level Hellish Rebuke, a duergar's enlarge-only Enlarge/Reduce, never in direct sunlight
- **Kobold Legacy** — an MPMM kobold picks Craftiness, Defiance or Draconic Sorcery
- **Weapon and armour training** — Dwarven Combat Training, Elf Weapon Training, a mountain dwarf's armour, Martial Prodigy and more count for your attacks, and a hobgoblin picks its two martial weapons
- **Shifting gives its numbers** — temporary hit points by printing, a Beasthide's +1 AC and extra temporary hit points, a Swiftstride's +10 ft speed, a Longtooth's fangs. The MPMM shifter picks its kind like a subrace

</details>

<details>
<summary><b>Spells</b> — slots, limits, concentration, free casts, scrolls</summary>

- **Spell slots by level**, worked out and tracked, with Pact Magic on its own
- **Your limits, per class** — each casting class shows spells known or prepared against its cap, plus cantrips (e.g. "Cleric Lv5: 3 / 8 prepared (WIS+lvl) · Cantrips 3 / 4"). A multiclass caster is counted per class, never pooled
- **Concentration**, with a save prompt when you take damage
- **Only ready spells cast** — an unprepared spell must be prepared first, and rituals follow each class's own rule (a wizard's from the spellbook, a cleric's or druid's once prepared)
- **Granted spells stay put** — domain, oath, circle, patron, origin, racial and feat spells are always prepared and can't be removed
- **Spells follow your classes** — removing a class or levelling down takes away only what it alone gave. Spells you picked yourself are never touched
- **Every source's own save DC** — the Spellcasting table lists each class, your race and each feat that gives spells, with its ability, save DC and attack bonus, and which spells use it. A tiefling wizard's Hellish Rebuke is CHA, their Fireball INT. Where the book lets you choose the ability (most MPMM races, Strixhaven Initiate) or the class (Magic Initiate, Spell Sniper), it's asked for
- **Free casts** — a racial or feat spell you can cast without a slot (a tiefling's Hellish Rebuke, Fey Touched's Misty Step, Firbolg Magic) has its own counter, back on the right rest, and Cast uses it before a slot. A fighter can still throw their Hellish Rebuke
- **Spell scrolls** — Use casts the scroll's spell with no slot or material components, at the scroll's own save DC and attack bonus. As in the DMG, a spell not on your class list can't be read, and one above the level you can cast needs a check (DC 10 + its level) or the scroll is lost
- **A searchable spell browser** with class and level filters, ritual and concentration markers, and each spell's description on hover

</details>

<details>
<summary><b>Combat</b> — HP, turns, actions, attacks, dying, conditions</summary>

- **HP tracking** — max, current and temporary HP, with one-click damage and healing
- **A turn tracker** — Action, Bonus Action and Reaction, with a one-click New Turn
- **Every action you have**, on the tab its rules say (an action, a bonus action, a reaction, or none: Indomitable, Stroke of Luck), filterable by kind and spell level. One leveled spell per turn is enforced, and Haste's extra action counts
- **Checked against the books** — every class, race and feat action spends what its rules say and shows its numbers: save DCs, dice, temporary hit points, uses
- **Use does what the action does**, the same on both apps — it spends the right thing (ki, Channel Divinity, a Bardic Inspiration die, a spell slot), turns on its effect, heals, and rolls its dice. It asks when there's a choice, and says what it did and what's left
- **Damage is your roll** — every damage ability says what to roll and its damage type ("add 3d8 radiant damage to the hit"). Damage you take for a feature asks what you rolled
- **Attack, then choose what to add** — Hit rolls and shows what it hits ("Hits AC 18 or lower"), what to roll if it hits, and what you can add with its cost: Sneak Attack, Divine Smite, a maneuver, Stunning Strike, an Arcane Shot and more, then what your bonus action can do. Only what you can pay for right now is offered, and on a critical hit the dice shown are already doubled
- **What's on, under each weapon** — by damage type: Hunter's Mark, Divine Favor, a smite, a Crimson Rite, a lit Flame Tongue. Flat bonuses go straight into the numbers
- **Casting a buff turns it on** — asking only what you know (who it's on, which weapon, which damage type). Smites go off on your next hit, ending concentration takes the effect off, and once-a-turn extras come back on New Turn
- **Advantage and disadvantage are reminders** — every roll is one d20 and lists what the sheet knows (exhaustion, Poisoned, Reckless Attack, Steady Aim, Danger Sense, War Caster), since cover, the target and your DM can change it
- **Two-weapon fighting, Green-Flame Blade and Booming Blade** — with the weapon you pick and every damage type
- **Magic weapons are real weapons** — a Sun Blade is a radiant, finesse longsword, an "any sword" item asks which sword it is, and each has its own extra damage, charges and recharge
- **Attacks that aren't a weapon in hand** — Martial Arts, natural weapons, the unarmed strike, Psychic Blades, Shadow Blade, a polearm's butt end, Form of the Beast, armour spikes, an Armorer's armour, a Wild Shape beast's attacks, and a class's own spell attacks
- **Wild Shape from its card** — pick the form (strongest first). It takes an action, or a bonus action with Combat Wild Shape, and an elemental takes two uses. In beast form you can't cast spells until Beast Spells at 18th level, and anything needing hands asks first, since your DM decides
- **Resources and per-rest uses** — Rage, Ki, Sorcery Points, Superiority Dice, Channel Divinity and every "once per rest" action, counted and reset by the right rest
- **Effects end when they should** — turn-long ones at New Turn, minute-long ones on a rest, and opening a saved character with one still on asks whether it has ended
- **Dying by the book** — temporary HP soak damage first, massive damage kills outright, a hit at 0 HP is a failed death save, three successes leave you stable, and the death screen says what killed you
- **Conditions and exhaustion** with their real effects — automatic failures, speed, and their advantage and disadvantage as reminders. Surprised included
- **Rage by the rules** — no casting, it ends concentration, no raging in heavy armour, and Relentless Rage rolls its save
- **AC you can check** — the breakdown adds up to the number shown
- **Honest rests** — a long rest needs at least 1 HP to start, and nothing is left above its maximum after a level change
- **Ammunition from your inventory** — each shot uses one, and a bundle of 20 arrows opens into loose ones so the Gear tab stays right

</details>

<details>
<summary><b>Class features</b> — invocations, maneuvers, metamagic, infusions</summary>

- **Eldritch Invocations** — all 54, each with its mechanics, gated by level, Pact Boon and spell prerequisites
- **Maneuvers, Metamagic, Fighting Styles and Infusions** — every option working
- **Elemental Disciplines, Arcane Shots and Rune Knight runes** as usable entries. Each rune is one card: what invoking it does and what having it carved gives you
- **Eldritch Adept, Metamagic Adept and Martial Adept** give their real choice of invocation, metamagic or maneuver
- **Eldritch Versatility** — swap a cantrip, your Pact Boon or a Mystic Arcanum spell at the right levels
- **Monk weapons follow Martial Arts** — DEX and the Martial Arts die when they're better, with no armour or shield. Kensei weapons and Dedicated Weapon follow their own rules, and Kensei's Shot, Agile Parry, Sharpen the Blade and Deft Strike all work
- **Blood Hunter** — Crimson Rite asks which rite and which weapon and takes the necrotic you rolled. An Order of the Profane Soul hunter has its own Pact Magic slots
- **Portent keeps its rolls** — a long rest rolls a Diviner's d20s and shows them with your other resources, where clicking one uses it
- **Strike of the Giants** asks which giant's strike you learn, and a hit offers it

</details>

<details>
<summary><b>Magic items</b> — attunement, effects, rarity</summary>

- **1,283 magic items** with full descriptions, and their mechanics working for over 99% of them: resistances, immunities, ability score overrides, AC and save bonuses, weapon and damage bonuses, charges, and reminders for effects too situational to automate
- **Attunement** — at most 3 items (4 for an artificer from 10th level), never two copies of the same item
- **Colour means rarity** — grey Common, green Uncommon, blue Rare, purple Very Rare, amber Legendary, crimson Artifact, shown as a bar beside the item (the card's border on Android)
- **Sorted by rarity, then name**, in the browser and in your own list
- **Every copy is its own item** — two Manuals of Bodily Health are two books; only magic ammunition stacks
- **Manuals and tomes work once** — studying one raises the score and its maximum by 2, and marks the book "Studied"
- **You pick the damage type** of a Ring or Armor of Resistance, an Absorbing Tattoo and the like

</details>

<details>
<summary><b>Gear & inventory</b> — equipment, coins, quantities</summary>

- **An equipment browser** with search and category filters
- **Coins** — platinum, gold, electrum, silver and copper
- **Inventory grouped by kind** — weapons, armour, magic items, consumables, tools and gear, in name order, so equipping something never moves it. A stack with one in hand says "1 of 3 equipped"
- **Clear row buttons** — a magnifying glass for details, a bin to remove, and − value + for quantities (hold to go in 5s; 0 removes the item)
- **Tooltips on every item**, in the browser and in your inventory

</details>

<details>
<summary><b>Feats</b> — prerequisites, spells, DM rewards</summary>

- **138 feats**, with their prerequisites checked
- **A feat keeps its +1** — taken at a level-up or by a Variant Human, it asks which ability when it can be more than one (Fey Touched, Resilient with its saving throw), and Elemental Adept asks its damage type. Lose the feat and what it decided goes too
- **Feats that grant spells** — Fey Touched, Shadow Touched and Magic Initiate ask which spell you want, and every feat's spells join your spell list
- **Every feat's action, bonus action and reaction** has its card: Lucky's luck points, the giant feats, the Knights of Solamnia, the dragon gifts and more
- **One-line summaries** on the Features tab, with the full rules on hover or Show Details
- **A DM-granted feats browser** for feats gained outside normal progression

</details>

<details>
<summary><b>Resistances, immunities & movement</b></summary>

- **Resistances and immunities worked out for you** from racial traits, feats, subclass features and attuned magic items
- **Immunity beats resistance** to the same damage type, and "resistance to all damage" or "all except X" expand into every type
- **Every movement speed** — climbing, swimming and flying from racial traits, class features and items

</details>

<details>
<summary><b>Save & share</b> — saves, auto-save, PDF import and export</summary>

- **Saves in `Documents/MIMIC Characters`** on both desktop and Android (change it in Settings), with each character's exported sheets in its own folder
- **Auto-save** when you create a character, level up or down, or confirm a choice
- **One file format** — a character saved on your phone opens on your computer, and back again
- **Import a PDF character sheet** — a character typed into the official 5e sheet (fillable or flattened) becomes a full character: ability scores, proficiencies, HP, spells, gear, magic items and money. Anything it can't match is kept word for word on an "Imported from PDF" notes page
- **Export a copy** — the character file, a plain-text summary, or a filled-in official PDF character sheet

</details>

<details>
<summary><b>Look & feel</b> — 26 themes, a custom icon set, tidy layouts</summary>

- **Immersive Health and Immersive Exhaustion** — colour drains from the sheet as hit points drop and comes back as you heal, and a dark frame closes in from the screen's edges with each level of exhaustion. Each is a setting (Full, Reduced or Off), and the numbers never change
- **26 themes** (16 dark, 10 light), every text colour readable on every background — Obsidian, Dragon's Hoard, Shadowfell, Feywild, Blood Moon, Frostspire, Cinderveil, Tavern Hearth, Mossgrove, Gearworks, Hallowed Stone, Underdark, Astral Sea, Nine Hells, Kraken's Depth, Storm Giant's Eye, Arcane Scroll, Moonlit Vellum, Sunlit Meadow, Elven Grove, Coastal Tide, Rose Chantry, Desert Oasis, Frostlight, Harvest Gold and Sky Citadel
- **75 hand-drawn line icons** for tabs, actions, items, rests and conditions, in your theme's accent and shared by both apps (a few condition icons are nods to famous memes, for anyone who spots them)
- **DM Secrets** — purely cosmetic surprises in Settings, off by default. Try them and see
- **Tabs that fit** — in a narrow window the tab names shorten, with the full name on hover
- **Search first, filters out of the way** — every browser is a full-width search box plus a funnel button that opens its filters in a side panel
- **The Choices tab as one page** — class and level, identity, what was applied for you, features by level and every pending choice
- **Right-click any feature or trait** for its full details, in a resizable window with draggable splitters

</details>

<details>
<summary><b>Dice roller</b></summary>

- **Any combination of dice**, with quick d4, d6, d8, d10, d12, d20 and d100 buttons
- **Advantage and disadvantage** — roll twice, keep the better or the worse
- **Modifiers and a roll history**

</details>

<details>
<summary><b>The Android app</b> — the whole sheet, made for touch</summary>

The Android app runs on the same rules engine and data as the desktop app, so a character builds, levels and saves the same on both.

- **The creation wizard** — race, ability scores, background, class and starting equipment
- **The whole character sheet** — abilities, proficiencies, combat, actions, spells, equipment, features, companions, infusions and notes
- **A combat screen** — HP and temp HP, death saves, every attack you have with what its hits can add, ammunition, favourite spells to cast, conditions, hit dice and Wild Shape
- **A turn tracker** that the Use and Cast buttons follow as you play
- **Level-up and Choices**, with the Choices tab pulsing while you still have picks to make
- **Rests, a dice roller, the same 26 themes, and Save & Export**
- **Made for touch** — a button for what you do often (Cast, Equip, Drink, Use), a magnifying glass for details, and press-and-hold for the rarer actions

</details>

<!-- github-only -->
## Screenshots

<p align="center">
  <img src="docs/images/desktop-abilities.png" width="49%" alt="Desktop: abilities and saving throws">
  <img src="docs/images/desktop-spells.png" width="49%" alt="Desktop: spellcasting, spell slots and metamagic">
</p>
<p align="center">
  <img src="docs/images/desktop-gear.png" width="49%" alt="Desktop: gear, coins and the equipment browser">
  <img src="docs/images/android-spells.png" width="24%" alt="Android: spells">
  <img src="docs/images/android-equipment.png" width="24%" alt="Android: equipment">
</p>
<p align="center"><sub>Mat Cauthon, a level 5 Half-Elf Sorcerer (Wild Magic), on desktop and Android.</sub></p>
<!-- /github-only -->

---

## Get started

### Run it from source

You need **Python 3.10 or newer**.

```bash
pip install -r requirements.txt
python run_dnd_creator.py
```

A splash screen shows straight away and animates while the app loads.

### Build it yourself

- **Windows** — `packaging\windows\build_exe.bat` makes `dist\MIMIC.exe`: one file, no Python needed
- **macOS / Linux** — `./packaging/windows/build_exe.sh` makes `dist/MIMIC`
- **Android** — `packaging\android\clean_build_android.bat` makes `dist\MIMIC.apk`, ready to copy to your phone

The guides — [Windows, macOS & Linux](packaging/windows/README.md) and [Android](packaging/android/README.md) — cover first-time setup. The version, **0.3.0**, is set in one place (`dnd_app/ui_android/buildozer.spec`), and both the APK and the Windows EXE (right-click → Properties → Details) carry it.

### Troubleshooting

- **"No module named 'PySide6'"** — run `pip install -r requirements.txt`.
- **The built program starts and closes straight away** — run it from a terminal to see the error, delete the `build/` and `dist/` folders and rebuild, and check that `dnd_app/ui_desktop/splash/` and `dnd_app/ui_desktop/icon.ico` exist.
- **The splash screen looks frozen** — update to the current source: the startup work runs in the background so the splash keeps moving.

---

<!-- github-only -->
## Project layout

```
dnd_app/
  core/              The rules engine both apps share
    character.py       the character itself, and rests
    builder.py         what race, class, background and feats grant
    calculator.py      AC, saves, skills, HP, slots, speed... (update_all)
    choices.py         what's left to pick, and the clean-up after a change
    actions.py         every action, bonus action and reaction a character has
    action_use.py      what pressing Use on one does
    attacks.py         every attack, its roll and what a hit can add
    riders.py          the extra damage on a weapon hit, by damage type
    spellcasting.py    spell limits, components, free casts, scrolls
    spell_effects.py   what casting a spell does to your own sheet
    effects.py         buffs, conditions and other active effects
    magic_items.py     item effects, attunement, owned copies
    dying.py, ammo.py  damage and death saves; ammunition
    save_load.py       save files, the save folder, old-save upgrades
    pdf_sheet.py       the official 5e PDF sheet, both ways
    readme.py          this file, as both apps' Credits screens show it
  data/              Game data: races, classes, spells, feats, items, stat blocks...
    phb2024/           the 2024 rules' data, for later
    themes.py, icon_data.py, flavor_text.py   shared by both apps' looks
  ui_desktop/        The desktop app (Qt Widgets): pages/, dialogs/, style/
  ui_android/        The Android app (Qt Quick/QML): bridge/, qml/
docs/                The reference lists the game data is checked against
packaging/
  windows/           build_exe.bat / .sh and MIMIC.spec
  android/           the clean build, its one-time setup, p4a_hook.py, icons
run_dnd_creator.py   Desktop entry point
main.py              Android entry point
```

---
<!-- /github-only -->

## Sources covered

| Category | Sources |
|----------|---------|
| **Core rules** | PHB and DMG (2014) |
| **Supplements** | XGE, TCE, VGM, MTF, MPMM, SCAG, EEPC, FTD, BGG, SatO, BMT, AAG, SAiS |
| **Settings** | ERLW, GGR, EGW, MOT, VRGtR, SCC, DSotDQ, AI |
| **Adventures** | Curse of Strahd, Ghosts of Saltmarsh, Tomb of Annihilation, Baldur's Gate: Descent into Avernus, Icewind Dale: Rime of the Frostmaiden, The Wild Beyond the Witchlight |
| **Smaller releases** | One Grung Above (grung), Locathah Rising (locathah), The Tortle Package (tortle) |
| **Plane Shift** (unofficial) | Amonkhet, Ixalan, Zendikar and Kaladesh races, two Kaladesh backgrounds, and the Amonkhet domains (Ambition, Solidarity, Strength, Zeal) |
| **Others** | A few feats from other publishers: the Tenders' Flamewoken, Forest Sage and Plantmender, and crafting and harvesting feats such as Adroit Crafter and Expert Harvester |

---

## Roadmap

- **Clickable cross-references** — a spell, feat or feature named in a description opens its details
- **Monsters and a bestiary** — including the creatures you summon or conjure
- **The 2024 rules** — further off

---

## License

MIMIC is free to use. It is not affiliated with or endorsed by Wizards of the Coast.

D&D 5e content is used under the Open Gaming License (OGL) and/or with permission from Wizards of the Coast.

---

## Credits

**Created by Ethan O'Brien**

**Built with:**
- Python
- PySide6 (Qt), for both the desktop and Android interfaces
- PyInstaller, for packaging the desktop app into a single executable
- Buildozer and python-for-android, for packaging the Android app

Thank you for downloading MIMIC, and for supporting the project.
