# MIMIC Patch Notes

Newest first. Every version has the same sections: Overview, New, Rules,
Quality of Life, Fixes and Known Issues.

---

## Next Update · In progress

*On main; ships with the next version.*

### 🌍 Overview

Adventurers, this one puts your slots in your hands. A spell that does
more from a higher slot asks which slot to use, and what's on your sheet
follows it: Aid's hit points, False Life's and Armor of Agathys's
temporary hit points, the smites' dice. Every creature is in the new
Bestiary, every magic item now does what it says on your sheet, and magic
armor finally counts as the armor it is. Heal no longer freezes when
pressed quickly, and popups suit the light themes.

### ✨ New

- **The Bestiary:** every creature, 2,754 of them, on both apps (Tools →
  Bestiary or Ctrl+B on desktop, the menu on Android). Find one by name or
  type, narrow the list by type, size and challenge rating, and read its
  whole stat block, legendary and lair actions included. Monsters of the
  Multiverse reprints are marked (MPMM), the way the races are.
- **Pick the slot:** casting Cure Wounds, Aid, Fireball, a smite or any
  other spell that does more from a higher slot asks which slot to use,
  when you have more than one level free, and says what the higher slot
  adds. Any other spell uses the lowest slot free, without asking.
- **Temporary hit points from your spells:** False Life (1d4 + 4, and 5
  more for each slot level above 1st) and Armor of Agathys (5 for each
  slot level) give their temporary hit points when cast. Armor of Agathys
  says how much cold damage it deals, and ends when they're gone.
- **Effects at their level:** the Effects tab says the level an effect
  was cast at ("Magic Weapon · 4th level") and what it does at that level
  (+2, not +1). Putting on an ally's Aid, Magic Weapon or Elemental Weapon
  asks the level it was cast at.
- **91 more magic items,** 1,374 in all, each wired to your sheet: the
  Ioun stones of knowledge, the Stones of Creation, Infernal Plate Armor,
  the Silver Sword, the archdevils' weapons, Gauntlets of Rage and more.
  Items the book gives no rarity are listed as Unknown, with a filter of
  their own.
- **Resistances on Android:** your resistances, immunities and now
  vulnerabilities show as badges on the Hit Points card (½, ⊘, ×2), as on
  desktop. Tap one to see where it comes from.

### ⚖️ Rules

- Magic armor is the armor it's made from: Dwarven Plate is plate (AC 18
  and its +2), Elven Chain a chain shirt. An item that can be any armor
  (+1 Armor, Armor of Fire Resistance...) asks which, the way Flame Tongue
  asks which sword.
  - *Designer note: before, magic armor was counted as no armor at all.*
- Ioun stones of knowledge give the skill's proficiency, or +1 if you
  have it already. Vulnerabilities (Infernal Plate Armor, the Canian
  Fork) are tracked and shown.
- An item use that comes back on a rest rather than at dawn (the Knife
  of Stolen Resistance, the Ring of Treachery's charges, the True-Ice
  Shards' Sub-Zero) comes back then, and the card says when.
- Aid raises your hit point maximum and current hit points by 5, and 5
  more for each slot level above 2nd. When it ends, the maximum goes back
  down.
  - *Designer note: before, its note asked you to add it to your maximum
    yourself.*

### 🧰 Quality of Life

- **Rest buttons in reach (Android):** Cancel and Take a Rest stay at the
  bottom of the rest screen, with the cards scrolling above them.
- **Popups in light themes (Android):** a popup or the menu now sits on a
  light veil in your theme's own colour, so the page still shows behind it.

### 🔧 Fixes

- Fixed Heal freezing the window when pressed quickly (desktop). Each
  press now shows at once, and the rest of the sheet catches up when you
  stop.
- Fixed a Heal at full hit points wiping the Undo for the change before it.
- Fixed equipping a magic shield taking off your armor: it's carried as
  your shield now.
- Fixed a suit of magic armor in your pack adding to your AC. Only the
  armor you wear counts.
- Fixed the rest screen's buttons running off the bottom of the screen
  (Android).

### ⚠️ Known Issues

- Spells that last 10 minutes or longer aren't counted in rounds. End
  them yourself.
- PDF import only reads the official character sheet, typed in.
- The 2024 rules aren't supported.

---

## v6.0 · "Keep Your Focus" · 13 November 2026

### 🌍 Overview

Adventurers, this one looks after your character, at the table and
between sessions. Spells and features that last a minute count down
their own rounds, concentration ends when you can't hold it, and the
concentration save takes your own roll if you'd rather throw the die.
Nothing unsaved is lost quietly any more, a slip on the Damage button
can be undone, and your last character is one button away when you open
the app.

### ✨ New

- **Rounds left:** a spell of a minute or less counts its rounds once
  it's cast (Bless, Hold Person, a smite…), and so do Rage and the other
  one-minute class features. Each New Turn takes a round off and ends
  what has run out, and says so. Give any effect or condition a count
  with its hourglass: Poisoned for 3 rounds comes off by itself.
- **Your own roll on a concentration save:** when you take damage while
  concentrating, roll the save on the sheet or type in the number on your
  own d20. Your bonus and everything that applies is added either way.
- **Continue:** the start menu opens the character you played last with
  one button. The rest are listed newest first, each with its race, class
  and when you last played it, and a search box appears once there are
  more than five.
- **Undo for Damage and Heal:** typed 50 for 5? **Undo** on the Hit Points
  card puts your hit points, temp HP, death saves and any concentration
  you lost back as they were, and the YOU DIED screen has it too.
- **Unsaved changes are kept safe:** closing the window, opening another
  character, starting a new one or importing a PDF asks first (desktop).
  While you have unsaved changes, both apps keep a backup next to the
  save and offer it back if the app ends before you've saved.
- **Find a feature:** the Features page has a search box that looks in
  each feature's name and in what it does. Click a feature to read it
  (desktop), or tap it (Android).
  - *Designer note: on Android there was no way to read what a feature
    did. Now there is.*
- **At a Glance (Android):** the Abilities screen shows what desktop's
  Derived Stats do: proficiency bonus, speed, senses, your passive scores,
  attacks per action and carrying capacity.
- **Cast from your spell list (desktop):** every spell on My Spells has
  its own Cast button, and a star that pins it to the Combat tab.

### ⚖️ Rules

- Concentration ends on its own when you're incapacitated, paralyzed,
  petrified, stunned or unconscious (asleep too), raging, or at 0 hit
  points, and the sheet says why.
  - *Designer note: before, only a failed save or dropping to 0 by
    damage ended it. A stunned wizard kept their Hold Person.*
- 89 spells you concentrate on (Bless, Entangle, the summons…) now have
  their real duration, from a round to a day.
  - *Designer note: they were listed as Instantaneous.*

### 🧰 Quality of Life

- **Rounds on the concentration line:** "Concentrating: Bless · 9 rounds
  left", on the Combat and Spells pages.
- **Uses that depend on an ability** show your number, then the rule:
  "Bardic Inspiration (d6, 3/Long Rest (CHA/LR))".
- **Keys (desktop):** Ctrl+1 to Ctrl+9 jump to a tab, and Ctrl+F puts the
  cursor in the search box of the tab you're on.
- **Icons in the menu (Android):** every screen in the drawer has the
  same icon as its desktop tab.
- **Pages that use the width (desktop):** Skills go into two columns on a
  wide window, Abilities spread across the page, and a spell takes one
  short row unless its details need a second. The Gear page gives your
  inventory more room, and its dividers have a grip.
- **Passive Investigation and Insight** sit beside Passive Perception on
  both apps.
- **The window title (desktop)** says whose sheet is open, with a dot when
  there's something unsaved.
- **Chosen options on the Features page** (Metamagic, invocations,
  infusions…) open to what each one does, under larger group headings.

### 🔧 Fixes

- Fixed a Bard's and a Sorcerer's Spellcasting feature showing the
  Paladin's text, and a Druid's and a Ranger's showing the Cleric's.
- Fixed Blade Ward doing nothing: casting it (or an earth genasi's Merge
  with Stone) gives resistance to bludgeoning, piercing and slashing
  through your next turn. Shield now adds its +5 AC until your next turn.
- Fixed Android warning about unsaved changes every time you went Home,
  even when nothing had changed.
- Fixed Android's start menu deleting a character on one tap, and Open in
  Save & Export leaving you on the old character's screen and theme.
- Fixed Android listing a subrace's ability score bonuses as features.
- Fixed Save being refused as "name already used" after Refresh, and the
  sheet forgetting its unsaved changes after a theme or text size change
  (desktop).
- Fixed the white marks between the sheet's tabs, and the tab names no
  longer shortening once an Artificer gained the Infusions tab (desktop).
- Fixed the "Extra Attacks" box showing 1 for a character with none. It's
  the attacks one Attack action makes, and is now labelled so.

### ⚠️ Known Issues

- Spells that last 10 minutes or longer aren't counted in rounds. End
  them yourself.
- PDF import only reads the official character sheet, typed in.
- The 2024 rules aren't supported.

---

## v5.0 · "Catch Your Breath" · 5 November 2026

### 🌍 Overview

Adventurers, this one's about spells, the fight and the rest after it.
MIMIC now tells you what you've still got to learn and lets you swap
spells as you level, keeps every roll you make, the Combat page has been
cleared for action, a rest shows (and does) everything it lets you do,
and every theme is easier on the eyes.

### ✨ New

- **Spells to Learn:** a card on the Choices tab shows the spells and
  cantrips each class can still learn. The Choices and Spells tabs pulse
  until you've picked them.
- **Level-up spell swaps:** Bards, Sorcerers, Warlocks, Rangers, Eldritch
  Knights and Arcane Tricksters can trade a spell when they level up.
  Wizards add two free spells to their spellbook.
- **Spell Resources:** Sorcery Points, Arcane Ward, Bardic Inspiration,
  Channel Divinity, Portent and your free casts sit on the Spells page,
  next to your slots.
- **Roll history:** every roll the sheet makes (checks, saves, initiative,
  attacks and whether they hit, hit dice, what your actions roll,
  potions) is kept with your character, ready to show your DM.
- **A new Dice Roller:** pick dice or type them (2d6 + 1d4 + 3, or 4d6kh3
  for an ability score), add one of your bonuses, take advantage or
  disadvantage on a d20, and tap a roll in the history to roll it again.
- **One Rest:** one button (desktop) and one menu entry (Android). Pick a
  short or long rest, see what it gives back, choose the hit dice to
  spend, and change what that rest lets you (prepared spells, your pact
  weapon…), all in one go.
- **Help on a rest:** tick what else a rest gives you (Song of Rest, a
  Chef's food, Celestial Resilience, Tireless) and what your party gives
  you (a bard's song, a chef's food, an ally's Inspiring Leader).
- **Everything a rest allows:** short and long rests list what else your
  class, feats, race and magic items let you do on them, plus attuning to
  an item or identifying one.
- **Health bar:** the menu bar (desktop) and the top bar (Android) fill
  with your hit points, temp HP after them, and turn amber then red as
  they drop. You can turn it off in Settings.
- **Metamagic on Android:** the Spells screen has the Metamagic card: tick
  what's for your next cast and spend the points.

### ⚖️ Rules

- Eldritch Knights and Arcane Tricksters are only offered spells from their
  own schools of magic, plus their picks from any school.
  - *Designer note: that's how the book has it. Until now they were offered
    every Wizard spell.*
- Grapple and Shove are a contested Athletics check in place of one of
  your attacks.
  - *Designer note: the sheet had the 2024 version, a saving throw.*
- A Circle of the Land druid's Natural Recovery picks the spell slots to
  get back on a short rest, the same as a Wizard's Arcane Recovery.
- Hit Dice follow a Periapt of Wound Closure (twice the hit points) and a
  verdan's Black Blood Healing (a 1 or 2 is rolled again).

### 🧰 Quality of Life

- **Readable everywhere:** every theme meets WCAG AA contrast, coloured
  text included.
- **A cleaner Combat page:** AC sits with your hit points, Initiative and
  Speed have their own card, and the turn tracker sits beside your
  actions (desktop).
- **Conditions and effects** share one card, a tab each. Hover a condition
  for what it does and right-click it to take it off (desktop), or press
  and hold it (Android).
- **Actions in order:** your own come first, then the basic ones everyone
  has, then the optional rules.
- **A tidier top bar (desktop):** your name is on the menu bar,
  Proficiency Bonus and Rest are up top on every page, and the tabs fill
  the width.
- **More room on the Spells page (desktop):** each Metamagic option shows
  what it does, and the side column scrolls when a multiclass caster's
  cards don't fit.
- **Immersive Health is gentler:** the colour only drains near the end.

### 🔧 Fixes

- Fixed the desktop level-up's spell swap and Versatility swaps being lost
  when the window closed.
- Fixed buttons turning green on hover, and some cards showing the wrong
  border colour.
- Fixed the death save circles being cut off.
- Fixed the desktop rest's hit dice leaving out Durable, Dwarven Fortitude
  and Vigor of the Hill Giant.
- Fixed the descriptions of Celestial Resilience (temporary hit points,
  half as many for your allies) and Deft Explorer's Tireless (a level of
  exhaustion off on a short rest).
- Fixed the actions list's item filter, which never found anything.
- Fixed the Metamagic card charging 1 sorcery point for every option:
  Quickened Spell costs 2, Heightened 3 and Twinned the spell's level.

### ⚠️ Known Issues

- PDF import only reads the official character sheet, typed in.
- The 2024 rules aren't supported.

---

## v4.0 · "Roll for Initiative" · 3 November 2026

### 🌍 Overview

Adventurers, the sheet now plays along. Attacks, checks, saves and
initiative roll for you, every action does what it says, and your old
paper characters can come with you.

### ✨ New

- **Rolling from the sheet:** attacks, ability checks, saving throws and
  initiative roll on the sheet, listing everything you can add (Bardic
  Inspiration, Guidance, a superiority die…), paid for in one tap.
- **Before the roll:** cast Guidance or Resistance, take Inspiration or
  Tides of Chaos, or use a Portent roll, asked as you roll.
- **Tool checks:** every tool you carry and know how to use gets its own
  card.
- **Buffs from your party:** add the Bless or Bardic Inspiration someone
  gave you, and it counts on your rolls.
- **PDF import:** turn a filled-in official character sheet into a full
  character.
- **185 Wild Shape forms:** every beast up to CR 6 and the four elementals,
  each with its full stat block. Mounts come with theirs too.
- **Immersive Health and Exhaustion:** optional effects that drain the
  colour as you take damage and close in the edges as exhaustion builds.
- **DM-granted proficiencies:** add any weapon, armour, tool or language
  your DM hands out.

### ⚖️ Rules

- Every action, bonus action and reaction spends its cost and applies its
  effect, for every class.
- The Spell Browser only offers spells your classes can still learn,
  multiclassing included.
  - *Designer note: no more accidentally learning a seventh spell on a
    six-spell Bard.*
- A spell from your race or a feat uses its own ability, save DC and
  attack, and its free casts have their own counter.
- Races, backgrounds, spells and spell slots checked against the books.
  25 spells added (Healing Spirit, Summon Fiend, Tenser's Transformation…),
  4 that were listed twice under a shorter name and 11 playtest spells
  taken out: 521 spells.
  - *Designer note: a new character should start with exactly what its
    book gives it.*

### 🧰 Quality of Life

- **Items show their weight and value**, and the same item is one row
  with how many you have.
- **Items are used from the Actions page**, with everything else you can
  do on a turn. Spell scrolls hold their spell.
- **Level Down and Remove Class** take back everything that level or
  class brought. Level back up and you're asked again.
- **Characters live in Documents/MIMIC Characters**, and Settings →
  Character Folder changes where.
- **Duplicate Character** makes a copy to try a different build on.
- **An error log** to send in if anything goes wrong.

### 🔧 Fixes

- Fixed a crash when changing a race's language.
- Fixed a crash when attacking with Sneak Attack.
- Fixed a crash when deleting an equipped weapon.
- Fixed crashes when using some actions.
- Fixed windows flashing up when loading or creating a character
  (desktop).
- Fixed the action list jumping to the bottom after pressing an action
  (desktop).

### ⚠️ Known Issues

- PDF import only reads the official character sheet, typed in. Scanned or
  handwritten sheets can't be read.
- The 2024 rules aren't supported.

---

## v3.0 · "Travelling Light" · 5 October 2026

### 🌍 Overview

Adventurers, MIMIC is coming with you. The whole app is now on Android, and
your character goes wherever you do.

### ✨ New

- **MIMIC for Android:** the full app on your phone (character creation,
  the whole sheet, combat, levelling up, rests and the dice roller), built
  for touch.
- **One save, both apps:** the same character file opens on your phone and
  your computer.
- **New icon set:** 74 hand-drawn icons in your theme's colours, and a new
  d20 app icon.
- **Notes pages:** personality, backstory, and Campaign Notes split into
  pages of your own.
- **Auto-save:** creating a character, levelling up or down and confirming
  a choice save it for you.
- **Export on both apps:** a character file to share or back up, a
  plain-text summary, or the filled-in official PDF sheet.

### ⚖️ Rules

- Aberrant Mind, Clockwork Soul and Lunar Sorcery sorcerers get their
  origin spells, always prepared.
- Surprised is a condition, with the book's rule: no moving, acting or
  reacting until your first turn ends.
- Items that guard against a damage type you pick (Ring and Armor of
  Resistance, Absorbing Tattoo, Orb of Shielding, Wyrmreaver Gauntlets)
  ask which.

### 🧰 Quality of Life

- **Inventory grouped by kind** (weapons, armour, magic items, consumables,
  tools and gear), with what's equipped first.
- **Items you use get their own icon:** tool kits, instruments,
  tinderboxes and torches, lanterns, flasks, healer's kits.
- **One Remove Page button** for your notes pages, in place of a close
  button on every tab.

### 🔧 Fixes

- Fixed personality traits, backstory and campaign notes being wiped
  after saving or refreshing the sheet.
- Fixed the notes page tabs being sized like the sheet's main tabs.

### ⚠️ Known Issues

- Tool checks can't be rolled from the sheet yet.
- The 2024 rules aren't supported.

---

## v2.0 · "By the Book" · 3 September 2026

### 🌍 Overview

Adventurers, the rules are filled in. Every subclass gets its spells, you
can level by XP, and your character prints onto the official sheet.

### ✨ New

- **XP levelling** as well as milestone. A big award carries you up more
  than one level.
- **PDF export:** print your character onto the official character sheet,
  or save a plain-text summary for your DM.
- **Previews** of what a level-up (hit points, spell slots, features) or a
  rest will give you, before you commit.
- **Ability checks** roll from the sheet, as skills and saves already did.
- **Component Restrictions:** an optional rule where Blinded, Gagged and
  Restrained block the spells that need what they take away. Gagged is a
  new condition.
- **14 new themes**, 26 in all.

### ⚖️ Rules

- Every subclass now gets its spells: every Cleric domain, every
  Warlock patron, and the Ranger conclaves and Druid circles that were
  missing them.
  - *Designer note: five Warlock patrons had no expanded spells at all.*
- Three missing spells added (Evard's Black Tentacles, Leomund's Secret
  Chest, Staggering Smite), and Thundering Smite renamed to Thunderous
  Smite: 511 spells.
- Multiclassing no longer gives the new class's saving throws.
- A githyanki's Astral Knowledge and an astral elf's Astral Trance give
  their skill and tool until the next long rest.

### 🧰 Quality of Life

- **Death saves** have their own card, with larger pips and a line saying
  where you stand.
- **One dialog for a long rest:** the preview and what you can change on
  the rest are together.
- **The Choices tab** is easier to read.

### 🔧 Fixes

- Fixed rests not restoring Wild Shape and some other resources.
- Fixed combat toggles and concentration staying on after a rest.
- Fixed Twilight Domain clerics also getting the Light Domain's spells.
- Fixed Bardic Inspiration and other uses not growing when the ability
  behind them went up.
- Fixed an Artificer's Infused Items counter stuck at 1.
- Fixed three backgrounds with no way to pick their skill or tool.
- Fixed old choices staying behind after changing race, background or
  subclass.
- Fixed actions used from the Action tabs not applying their effect.

### ⚠️ Known Issues

- Tool checks can't be rolled from the sheet yet.
- A few items that guard against a damage type of your choice don't ask
  which yet.
- The 2024 rules aren't supported.

---

## v1.0 · "Session Zero" · 20 August 2026

### 🌍 Overview

Adventurers, welcome to MIMIC: a D&D 5e character creator and sheet for
your computer, offline and free.

### ✨ New

- **Step-by-step character creation:** race, ability scores (point buy,
  standard array or your own), background, class, spells and equipment.
- **The 2014 rules:** 84 races and a custom one, 14 classes with 127
  subclasses, 508 spells, 138 feats, 99 backgrounds and 1,283 magic items.
- **Levelling up and multiclassing**, with each level's choices.
- **A combat sheet** that tracks your HP, your turn, your resources, rests,
  death saves and conditions.
- **Spells, slots and concentration**, with a save prompt when you take
  damage.
- **Magic items and attunement**, with their effects working for over 99%
  of them.
- **Optional class features:** every invocation, maneuver, metamagic,
  fighting style and infusion.
- **A dice roller** with advantage, disadvantage and a history.

### ⚖️ Rules

- Conditions do what they say to your saves, attacks, checks and speed.
- Immunity wins over resistance to the same damage type.
- One leveled spell a turn, with Haste's extra action allowed.

### 🧰 Quality of Life

- **12 themes.**
- **Right-click a feature or trait** for everything it does.
- **Search** spells, feats, items and equipment.
- **Resizable panels** you can drag.

### 🔧 Fixes

- None: this is the first version.

### ⚠️ Known Issues

- Ability checks and tool checks can't be rolled from the sheet yet.
- Some subclasses don't get their spells prepared for them yet.
- The 2024 rules aren't supported.
