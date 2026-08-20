# MIMIC

### A Complete D&D 5e Character Creator & Management Tool

MIMIC is a desktop application for Dungeons & Dragons 5th Edition that brings together everything a player needs in one place: races, classes, subclasses, spells, feats, backgrounds, magic items, companions, wild shape, and combat tracking. It runs entirely offline, is free to use, and ships as a single portable executable.

---

## What's Included

### Core Database
- **85 races** with subraces from every official sourcebook, including modern (MPMM) revisions kept alongside their original printings where the two differ mechanically
- **138 feats** from PHB (2014 & 2024), XGE, TCE, FTD, and more
- **99 backgrounds** from PHB (2014), plus adventure-specific backgrounds — 2024 Origin Feat backgrounds intentionally excluded, since this app targets the 2014 ruleset only
- **14 classes** including Blood Hunter
- **126 subclass combinations** (2014 ruleset) — audited line-by-line against source text, not filled in from memory
- **508 spells** across all 9 levels with per-class spell lists
- **1,283 magic items**, with real mechanical effects (ability score overrides, resistances, weapon bonuses, resource pools, and more) wired for over 99% of the catalog
- **All standard weapons and armor** with computed attack bonuses and damage, plus browsable Silvered and Adamantine variants of every weapon (correctly restricted to melee weapons only for Adamantine, per the real rule) with accurate cost surcharges and the real mechanical text for each
- **28-beast Wild Shape catalog** spanning CR 1/4 through CR 6, filtered by your actual druid level and any race/beast restrictions
- **Full companion stat blocks** for Steel Defender, Wildfire Spirit, Drake Companion, Dancing Item, Primal Companions (Beast of the Land/Sea/Sky), and Eldritch Cannon
- **11 races with real natural weapons** (Aarakocra Talons, Tabaxi Claws, Lizardfolk Bite, Minotaur Horns, Satyr Ram, Longtooth Shifter's Fangs, and more) rendered as actual weapon rows with computed attack and damage — not just flavor text, and correctly covering both original and MPMM printings where a race has both

### Character Builder
- **Full character creation wizard:** Race, Ability Scores, Background & Class, Spells, Equipment
- **Point Buy, Standard Array, or Manual Entry** for ability scores
- **Live race detail panel** — picking a subrace updates the shown ASI and traits immediately, not just at the end
- **Full background details** — feature descriptions, bonus languages, and starting equipment shown in full, not truncated
- **Starting equipment picker** with class-appropriate options — every chosen item lands correctly in your inventory, alongside your background's own equipment and starting gold
- **Level-up wizard** — walks through each level's choices, including nested sub-choices
- **Multiclassing support** — full rules for combining classes

### Spell Management
- **Prepared/known spell tracking**
- **Spell slots by level** — automatically calculated and tracked
- **Concentration tracking** — with save prompts when you take damage
- **Ritual and quick-cast markers**
- **Searchable spell browser**
- **Auto-prepared spells** for domains, oaths, and circles with a verified spell list
- **Spell descriptions on hover**

### Optional Class Features
- **Eldritch Invocations** — all 54 real options, individually wired with real mechanics and correctly gated by level, Pact Boon, and spell prerequisites
- **Battle Master Maneuvers, Metamagic, Fighting Styles, and Artificer Infusions** — every real option audited and wired
- **Elemental Disciplines, Arcane Shot, and Rune Knight Runes** — fully wired as real, usable entries
- **Eldritch Adept, Metamagic Adept, and Martial Adept feats** — grant a real choice of invocation, metamagic, or maneuver
- **Eldritch Versatility** — swap a cantrip, your Pact Boon, or a Mystic Arcanum spell at the right levels

### Combat Tracker
- **Full HP tracking** — Max, Current, and Temporary HP with one-click damage/heal
- **Turn tracker** — Action, Bonus Action, and Reaction economy with one-click New Turn reset
- **Known Actions filter** — every real, usable action, filterable by category and spell level
- **Correct action-economy consumption** — cantrips and leveled spells consume the right slot based on real casting time
- **The real "one leveled spell per turn" rule enforced**, with Haste's genuine extra action recognized as an exception
- **Casting a spell that matches an existing buff/condition system automatically applies it**
- **Class resource tracking** — Rage, Ki, Sorcery Points, Superiority Dice, Channel Divinity, and every other class resource
- **Short and long rest auto-reset**
- **Death saves, condition tracking, and exhaustion**, with real mechanical effects on saves, attack rolls, ability checks, and movement — not just a checkbox
- **Weapon and armor equipping** with computed attack bonuses and damage
- **On-hit damage bonuses shown separately by type**, since a different damage type genuinely matters against resistance/immunity

### Resistances, Immunities & Movement
- **Automatic resistance/immunity resolution** from racial traits, subraces, feats, subclass features, and attuned magic items
- **Immunity correctly supersedes resistance** to the same damage type
- **"Resistance to all damage" and "all except X" effects** expand into every individual damage type
- **Player-chosen resistance items** get a real dropdown to pick which damage type your copy protects against
- **Full movement tracking** — climbing, swimming, and flying speeds from racial traits and class features

### Magic Item Integration
- **1,283 magic items** with full descriptions
- **Attunement tracking** — max 3 attuned items (4 for Artificers at 10th level)
- **Mechanical effects wired for over 99% of the catalog** — resistances, immunities, ability score overrides, AC/save bonuses, weapon and damage bonuses, resource pools, and reminders for effects too situational to automate
- **Searchable magic item browser** with filtering

### Gear & Inventory
- **Equipment browser** with search and category filtering
- **Quantity tracking** for stackable items
- **Real tooltips on every item**, both in the reference browser and your owned inventory

### Feat Manager
- **138 feats** from all official sources
- **Automatically checked prerequisites**
- **DM-granted feats browser** for feats gained outside normal progression

### Interface & Customization
- **12 themes** — Obsidian, Dragon's Hoard, Shadowfell, Arcane Scroll (light mode), Feywild, Blood Moon, Frostspire, Cinderveil, Tavern Hearth, Mossgrove, Gearworks, Hallowed Stone
- **Resizable window** with draggable splitters between panels
- **Right-click any feature, race trait, or subrace trait** for a full detail popup
- **Search everywhere** — find spells, feats, items, and equipment instantly

### Save & Share
- **Save characters** to `~/.dnd_characters/`
- **Load characters** — pick up where you left off
- **Export and import** character files to share with others

### Dice Roller
- **Built-in dice roller** for any dice combination
- **Quick roll buttons** — d4, d6, d8, d10, d12, d20, d100
- **Advantage/Disadvantage** — roll twice, take the better or worse result
- **Modifier support and roll history**

---

## Quick Start

**Requirements:** Python 3.9+ and pip.

```bash
pip install PySide6
python run_dnd_creator.py
```

A splash screen appears immediately and animates while the app loads in the background, so startup never looks frozen.

---

## Building a Standalone Executable

### Windows
```bat
build_exe.bat
```

### macOS / Linux
```bash
./build_exe.sh
```

**Output:** `dist/MIMIC.exe` (Windows) or `dist/MIMIC` (macOS/Linux). See [`BUILD_EXE.md`](BUILD_EXE.md) for the full guide.

---

## Troubleshooting

### "No module named 'PySide6'"
```bash
pip install PySide6
```

### Executable starts but immediately closes
1. Run from a terminal or command prompt to see error output.
2. Delete the `build/` and `dist/` folders and rebuild.
3. Check that `dnd_app/assets/` and `dnd_app/icon.ico` exist before building.

### Splash screen looks frozen or doesn't animate
Make sure you're on current source — the heavy startup import runs on a background thread specifically so the splash animation keeps playing while it loads.

---

## Project Structure

```
dnd_app/
  data/              # All game data (races, classes, spells, feats, items, etc.)
  core/              # Character model, calculator, builder, save/load
  ui/                # PySide6 widgets (main window, wizard, sheet, theme, etc.)
  assets/            # Splash screen image/GIF
  icon.ico           # App icon
run_dnd_creator.py     # Entry point
requirements.txt
DnD5eCharacterCreator.spec   # PyInstaller build spec
build_exe.bat / build_exe.sh # One-command build scripts
```

---

## Sources Covered

| Category | Sources |
|----------|---------|
| **Core Rules** | PHB (2014 & 2024), DMG |
| **Expansions** | XGE, TCE, SCAG, EEPC |
| **Settings** | ERLW, GGR, EGW, MOT, WBW, AAG, VRGtR, FTD, DLSotDQ, BPGotG, SCC, SCOC, AI, SAiS |
| **Adventures** | Curse of Strahd, Ghosts of Saltmarsh, Tomb of Annihilation, Baldur's Gate: Descent into Avernus |
| **Community Content** | One Grung Above (Grung), Locathah Rising (Locathah), The Tortle Package (Tortle) |
| **Unofficial** | Plane Shift: Amonkhet (Ambition/Solidarity/Strength/Zeal Domains), clearly marked as such in-app |

---

## Roadmap

- Full support for the 2024 ruleset
- Clickable hyperlinks for spell/feat/ability cross-references
- Broader auto-prepared spell coverage across remaining subclasses
- Wider on-hit damage bonus coverage
- Player-choice resistance selection for the few remaining items that need it
- Monster and bestiary integration

---

## License

MIMIC is free to use. It is not affiliated with or endorsed by Wizards of the Coast.

D&D 5e content is used under the Open Gaming License (OGL) and/or with permission from Wizards of the Coast.

---

## Credits

**Created by Ethan O'Brien**

**Built with:**
- Python
- PySide6, for the desktop interface
- PyInstaller, for packaging the app into a single executable

Thank you for downloading MIMIC, and for supporting the project.
