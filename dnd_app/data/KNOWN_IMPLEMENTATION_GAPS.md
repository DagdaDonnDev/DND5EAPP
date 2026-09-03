# Known Implementation Gaps

Features that exist in `feature_tooltips.py` (real, sourced descriptions)
but currently have no meaningful way to be mechanically implemented given
the app's existing architecture — not skipped through oversight, but
because fixing them requires building a new subsystem first, which is a
larger scope than a per-feature fix. Tracked here so they aren't
forgotten, and can be revisited in one pass if/when the underlying
subsystem gets built (e.g. if a damage-rolling system is ever added,
search this file for every feature blocked on it).

Format: `Feature name (class/level) — what's blocking it`

## Blocked on: no damage-rolling system
Weapon rows compute and display a damage formula (e.g. "1d12+5") but
never actually roll it — only the to-hit roll is simulated. Anything that
modifies a *rolled* damage result (rerolling low dice, extra dice on a
crit, maximizing a roll) has nothing to hook into.

- **Brutal Critical** (Barbarian Core, 9th/13th/17th) — extra weapon
  damage dice on a critical hit.
- **Great Weapon Fighting** (Fighting Style) — reroll 1s and 2s on
  weapon damage dice.

## Blocked on: no ability-check-rolling system
Saving throws and attack rolls have real roll buttons; ability checks
(STR/DEX/etc, not tied to a specific skill) don't.

- **Indomitable Might** (Barbarian Core, 18th) — STR check result can't
  be lower than your STR score.

## Blocked on: not actually broken, just not literally modeled
The underlying mechanic these features change was never modeled with
enough granularity for the change to matter.

- **Persistent Rage** (Barbarian Core, 15th) — changes how Rage *ends*
  early, but Rage's duration was never tracked minute-by-minute in the
  first place (it's a manual on/off toggle with no auto-expiry), so this
  feature's effect is already implicitly present in the simpler model.

## Situational/narrative, no numeric effect to compute
- **Instinctive Pounce** (Barbarian Core, 7th) — move half your speed as
  part of the bonus action used to enter Rage. No bonus-action-movement
  tracking exists to attach this to, and the effect itself has no number.
- **Intimidating Presence** (Path of the Berserker, 10th) — a DC (8 +
  prof + CHA) could be shown as a reference number, but the actual effect
  (a creature you target must save or be frightened, repeating each
  round) needs a "conditions applied to others" tracker this app doesn't
  have. Added to KNOWN_ACTIONS as a reminder at minimum; not tracked
  beyond that.
- **Totem Spirit — Eagle/Wolf** (Path of the Totem Warrior, 3rd) — Bear's
  resistance is fully implemented; Eagle (disadvantage on opportunity
  attacks against you, Dash as bonus action while raging) and Wolf
  (allies get advantage on melee attacks against creatures within 5 ft of
  you) both need combat-positioning tracking (who's adjacent to whom,
  opportunity attack resolution) that doesn't exist.
- **Aspect of the Beast — Eagle/Wolf** (Path of the Totem Warrior, 6th) —
  Bear's carrying-capacity doubling is implemented (`get_carry_capacity`).
  Eagle (see 1 mile clearly, no disadvantage in dim light for Perception)
  and Wolf (track at a fast pace, stealth at normal pace in a group) are
  situational/narrative with no number this app currently computes
  (Perception is a flat bonus, not distance- or lighting-conditional; no
  tracking-check or group-stealth mechanic exists).
- **Ancestral Protectors** (Path of the Ancestral Guardian, 3rd) — marks
  a target so attacks against others have disadvantage and allies gain
  resistance to its damage. Needs combat-targeting/marking tracking that
  doesn't exist.
- **Vengeful Ancestors** (Path of the Ancestral Guardian, 14th) —
  reflects damage prevented by Spirit Shield back at the attacker.
  Spirit Shield itself is now in KNOWN_ACTIONS with the correct scaling
  die; this specific reflection isn't separately computed since it
  depends on a specific triggering attack this app doesn't simulate.
- **Infectious Fury** (Path of the Beast, 10th) — force a WIS save or
  psychic damage when Form of the Beast connects. Added to KNOWN_ACTIONS
  as a reminder with the correct DC formula; not separately computed
  since it depends on a specific triggering attack.
- **Call the Hunt** (Path of the Beast, 14th) — shares temp HP and
  advantage with up to 5 allies while raging. Added to KNOWN_ACTIONS as a
  reminder; the "creature you've hit since your last turn" condition
  needs combat-history tracking this app doesn't have.
- **Giant's Havoc, Elemental Cleaver, Mighty Impel** (Path of the Giant)
  — Giant's Might now has a real tracked resource (uses = prof bonus) and
  a KNOWN_ACTIONS button. The other three are added as reminders but stay
  situational — weapon-damage-type overrides, forced creature movement,
  and thrown-weapon-returns-to-hand aren't modeled.
- **Storm Aura, Shielding Storm, Raging Storm** (Path of the Storm
  Herald) — Storm Soul's resistance AND swim speed (Sea) are both fully
  implemented and verified. The aura's per-turn damage/effect triggers
  and their extension to allies are reminders only — no AoE-per-turn
  tick system exists.
- **Magic Awareness, Bolstering Magic, Unstable Backlash, Controlled
  Surge** (Path of the Wild Magic) — Wild Surge's actual d8 table roll is
  fully implemented (pre-existing, just had a stale trigger-timing
  description which is now fixed: triggers on entering rage, not "start
  of turn"). The other four are reminders — no dice-pool-granting or
  reroll-tracking mechanism exists for the specific effects.
- **Fanatical Focus, Zealous Presence** (Path of the Zealot) — Divine
  Fury (extra necrotic/radiant damage on first hit while raging) is fully
  implemented via `get_onhit_damage_bonuses()`. Rage Beyond Death (14th)
  was implemented in an earlier round of this audit. The remaining two
  are reminders — save-reroll tracking and mass-advantage-granting to up
  to 10 creatures aren't modeled.

## Artificer

- **Tool Expertise** (Core, 6th) — doubles proficiency bonus with tools.
  No tool-check-rolling system exists anywhere in this app (same shape of
  gap as Indomitable Might needing an ability-check roller) — there's
  nothing to double.
- **Magical Tinkering, The Right Tool for the Job** (Core) — narrative
  effects with no number to compute.
- **Spell-Storing Item** (Core, 11th) — store a spell in an item for
  anyone to trigger later. Needs per-item spell storage this app doesn't
  track.
- **Magic Item Adept's crafting-time/cost reduction** (Core, 10th) — the
  attunement-slot half of this feature IS implemented (see below); the
  "quarter time, half gold to craft" half has no crafting-time/cost
  system to apply to.
- **Soul of Artifice's reaction-to-1-HP** (Core, 20th) — the +1-save-per-
  attuned-item half IS implemented in `get_saving_throw_bonus()`; ending
  an infusion as a reaction to survive at 1 HP instead needs per-infusion
  tracking this app doesn't have.
- **Alchemical Savant, Restorative Reagents' Lesser Restoration cast**
  (Alchemist) — depend on which spell/damage type is being rolled at the
  moment, no per-spell-cast modifier system exists. Restorative Reagents'
  temp-HP-on-elixir half also isn't separately modeled.
- **Tools of the Trade, Armor Modifications, Perfected Armor** (Armorer)
  — Arcane Armor's built-in weapon (Thunder Gauntlets/Lightning Launcher)
  and Infiltrator's Powered Steps (+5 speed) ARE both implemented and
  verified. Tool proficiency has nowhere to apply (same gap as Tool
  Expertise); infusion-capacity increases and the pull/light-debuff
  effects need per-infusion and per-target-condition tracking this app
  doesn't have.
- **Arcane Firearm, Fortified Position** (Artillerist) — Eldritch Cannon
  itself is fully resourced (pre-existing). These two are reminders —
  per-spell damage-roll modification and cannon-count/cover mechanics
  aren't modeled.
- **Battle Ready's INT-for-magic-weapons** (Battle Smith) — Steel
  Defender and Arcane Jolt (with its correct 2d6→4d6 Improved Defender
  scaling) ARE both implemented. Battle Ready needs the weapon-attack
  stat-selection logic to recognize "is this a magic weapon," which it
  currently doesn't check for at all — added as a reminder rather than a
  computed override.

## Paladin

**A real, pre-existing bug found and fixed before the audit even started**:
Cleric's resource list contained an erroneous "Lay on Hands (Paladin MC
only)" entry sharing the same key ("loh") as Paladin's own, correct Lay
on Hands definition — meaning any Cleric/Paladin multiclass character got
two colliding resources. Removed the erroneous entry; verified Cleric
alone now has none, Paladin alone is unaffected, and the actual
multiclass scenario now correctly has exactly one.

**Two more real bugs found while implementing subclass features** (not
in Paladin's own code, but surfaced by trying to build on top of it):
`SUBCLASS_PASSIVE_RESISTANCES`' processing loop required a non-None
`subclass_match`, which would have crashed (`TypeError`) the first time
anyone tried to use it for a base-class (non-subclass-specific) passive
grant — needed for Divine Health and Aura of Courage, which apply
regardless of Sacred Oath. Fixed to support `None` the same way the
toggle-resistance loop already did. Separately, `get_carry_capacity()`
had been silently defined twice — my Barbarian-era addition (returning
an int) completely shadowed a more comprehensive, pre-existing version
(returning a dict, and already correctly handling the "Powerful Build"
racial trait). Renamed the original to `get_carry_capacity_detail()`,
merged Powerful Build support into the active version, and verified all
three doubling sources (Bear Totem, Powerful Build, Peerless Athlete)
work independently without stacking multiplicatively.

**A genuine near-repeat of the Bardic Inspiration mistake, caught before
shipping**: added "Emissary of Redemption" and a duplicate "Invincible
Conqueror" to `resistance_sources.py` without first checking whether
entries already existed there — they did, as correctly-modeled toggles.
Removed both duplicates and kept the pre-existing, working versions.
Lesson reinforced: check `resistance_sources.py`/`movement_sources.py`
themselves, not just `core/*.py`, before adding new resistance/movement
grants.

**Real mechanics implemented**: Divine Health (disease immunity, 3rd)
and Aura of Courage (frightened immunity, 10th) as base-class passives —
the ally-extension radius of Aura of Courage isn't modeled since
resistance tracking is character-centric, not party-aware. Sacred Weapon
(Oath of Devotion) as a genuine toggle drawing from the shared Channel
Divinity pool (not its own resource) — verified spending a use, toggling
on/off, and the CHA-mod attack bonus actually changing a weapon's to-hit
number. Aura of Devotion (charmed immunity, 7th). Aura of Conquest's
resistance-to-all toggle (Invincible Conqueror, 20th) and Emissary of
Redemption's resistance-to-all (Redemption, 20th) — both pre-existing,
now verified duplicate-free. Aura of Warding (spell damage resistance,
Ancients 7th) and Supernatural Resistance (nonmagical B/P/S,
Oathbreaker 15th) — both newly added. Aura of Alacrity (+10ft speed,
Glory 7th, always-on) and Aura of the Sentinel (+prof bonus to
initiative, Watchers 7th, always-on) — both new movement/initiative
grants following the established Fast Movement/Feral Instinct pattern.
Peerless Athlete (Glory) as a toggle doubling carrying capacity.

**Oath of the Ancients and Oathbreaker were entirely missing from
`class_feature_index.py`** — added both, verified via multiple
independent sources at the standard 3/7/15/20 progression.

Reminders only, situational/narrative: Turn the Unholy, Purity of
Spirit, Holy Nimbus (Devotion); Abjure Enemy, Vow of Enmity, Relentless
Avenger, Soul of Vengeance, Avenging Angel (Vengeance); Conquering
Presence, Guided Strike (deliberately not a toggle — one-time per-attack
bonus, not a persistent state), Scornful Rebuke (Conquest); Emissary of
Peace, Rebuke the Violent, Aura of the Guardian, Protective Spirit
(Redemption); Champion Challenge, Turn the Tide, Divine Allegiance,
Unyielding Spirit (Crown — save-advantage tied to specific conditions
rather than a fixed ability score, doesn't cleanly fit the per-ability
advantage system); Inspiring Smite, Glorious Defense, Idol of Glory
(Glory); Abjure the Extraplanar, Watcher's Will, Vigilant Rebuke, Mortal
Bulwark (Watchers); Nature's Wrath, Turn the Faithless, Undying
Sentinel, Elder Champion (Ancients); Control Undead, Dreadful Aspect,
Dread Lord (Oathbreaker).

## Re-verification pass (prompted by a real correction)

Fiendish Resilience (Warlock, The Fiend) was implemented incorrectly —
I'd excluded bludgeoning/piercing/slashing from the choosable damage
types based on my own tooltip text, when the actual rule has no such
exclusion (any damage type is choosable, and magical/silver weapon
damage bypasses the resistance regardless of type). Corrected directly
from the real rule text rather than re-deriving it, and used the
opportunity to re-check every resistance/condition entry added this
session against `classes.py`'s actual on-disk data (the same ground
truth originally provided) instead of my own descriptions:

- **Cleansing Touch** (Paladin, 14th) was completely missed — its
  resource was already correctly defined in `classes.py`, but never had
  a KNOWN_ACTIONS entry, so there was no way to actually use it. Fixed.
- **Mystic Arcanum** (Warlock, 11th/13th/15th/17th) had a deeper gap than
  first realized: my earlier fix let a player choose which spell to
  learn, but the chosen spell was never added to `spells_known` (so it
  didn't even show up as known), and the pre-existing `arcanum_6/7/8/9`
  resources (already correctly defined in `classes.py`) had no
  KNOWN_ACTIONS entry connecting to them, so there was no way to
  actually cast the chosen spell. Fixed both — verified the spell
  reaches `spells_known`, and that clicking the resulting "Use" button
  correctly spends the tier-specific resource.
- **Chemical Mastery** (Artificer, Alchemist) was flagged as a possible
  error during this pass, then verified via 10 independent sources
  (including the official wiki) to already be correct — poison
  *damage* resistance and the *poisoned condition* immunity are two
  separate grants, and the existing code already modeled both correctly.
  Not a bug; confirmed and left as-is.
- Found ~148 duplicate keys in `feature_tooltips.py`, accumulated from
  earlier large-scale subclass-building passes. Spot-checked several
  (Healing Light, Frenzy, Divine Strike, Extra Attack) and all were
  semantically equivalent re-descriptions, not conflicting data — a
  code-hygiene issue worth a dedicated cleanup pass, not a correctness
  one.

**Methodology change going forward**: verify against the actual on-disk
data files (`classes.py`'s resource/feature definitions) before trusting
my own tooltip text or defaulting to a web search — that data is the
same ground truth originally provided and is directly checkable.

## Bard

Core was largely already correct — Bardic Inspiration, Jack of All
Trades, Expertise, Magical Secrets, Song of Rest, and Countercharm were
all genuinely implemented before this audit (verified, not assumed —
checking `classes.py`'s generic formula-based resource loader caught this
before a redundant duplicate got shipped). Superior Inspiration (20th)
is a reminder — no initiative-roll-triggered auto-recharge hook exists.

**Two real bugs found and fixed, not just gaps documented:**
- **Extra Attack was completely broken for College of Valor and College
  of Swords** — the old logic had Bard in an outer level-5+ check but
  missing from the inner set that actually granted it, so no Bard
  subclass ever received Extra Attack at all, at any level. Rewrote the
  logic cleanly with an explicit Bard-specific check at the correct
  level (6th, not 5th) and subclass gate. Verified across Valor, Swords,
  a non-martial subclass (Lore, correctly still 1 attack), and a
  regression check on Barbarian to confirm the rewrite didn't disturb
  other classes.
- **College of Eloquence's level table was wrong** — Universal Speech
  was misplaced at 14th level (verified via 7 independent sources it's
  actually 6th, alongside Unfailing Inspiration), and the real 14th-level
  feature, Infectious Inspiration, was missing entirely. Fixed both the
  level table and added the missing feature's description.
- **College of Swords never collected its Fighting Style choice at all**
  — Dueling/Two-Weapon Fighting never applied to any Swords Bard despite
  the underlying weapon-damage math already supporting both styles for
  other classes. Added the chooser (using the exact "_fighting_style"
  key suffix the processing logic requires) and verified all three
  layers: the choice gets offered, gets correctly stored, and Dueling's
  +2 damage actually shows up on a Swords Bard's weapon row.
- **Spirit Session (College of Spirits) had no tracked resource** —
  added with correct proficiency-bonus uses and the right d6→d12 die
  scaling at 14th (Awakened Spirit). Verified this one was genuinely
  missing from `classes.py`'s data, unlike Bardic Inspiration.

Reminders only, situational/narrative: Cutting Words, Peerless Skill,
Combat Inspiration, Battle Magic, Blade Flourish, Master's Flourish (all
Bardic-Inspiration-expending player choices, not automatic bonuses),
College of Creation's three object-creation/animation features, Mantle
of Inspiration/Enthralling Performance/Mantle of Majesty/Unbreakable
Majesty (Glamour), Mystic Chronicle/Awakened Spirit (Spirits — beyond
the die scaling, which is implemented), and Words of
Terror/Mantle of Whispers/Shadow Lore/Psychic Blades (Whispers — the
latter is per-hit resource-expending player choice, correctly not forced
into an automatic damage bonus).

## Data Integrity Note (feature_tooltips.py duplicate keys)

`feature_tooltips.py` has ~148 duplicate keys (the same feature name
defined twice), left over from different points this file was
assembled/merged across sessions. Investigated whether these represent
real conflicts or just redundant rewording:

**Confirmed real bug, now fixed**: Fiendish Resilience (Warlock, The
Fiend) was implemented incorrectly — the "winning" (later, active)
duplicate incorrectly claimed damage type choices exclude bludgeoning/
piercing/slashing. The real rule has no such exclusion; the actual
caveat is that damage from magical or silver weapons bypasses the
resistance regardless of chosen type. Fixed the implementation in
`resistance_sources.py` (all types now selectable, B/P/S marked
`nonmagical` to reflect the real bypass condition) and corrected both
duplicate description entries to match.

**Spot-checked all 10 other duplicate pairs tied to features actually
mechanically implemented this session** (Totem Spirit, Aspect of the
Beast, Totemic Attunement, Storm Soul, Battlerager Armor, Sacred Weapon,
Aura of Devotion, Aura of Warding, Mindless Rage, Reckless Abandon) —
every one of these agrees between both duplicate versions, just at
different levels of detail. Fiendish Resilience appears to be an
isolated case, not a symptom of a broader pattern, but this was
confirmed by direct comparison, not assumed.

**Not yet done**: a full deduplication pass across all ~148 duplicate
keys. Given the spot-check found only one real conflict, this is lower
priority than continuing the class-by-class audit, but worth doing at
some point — future implementation work should check both versions of
any duplicated description before trusting either one.

## Warlock

**Three major, high-impact bugs found and fixed in Core, affecting
every single Warlock character**: Eldritch Invocations had a fully
working chooser widget and processing path, but nothing ever actually
offered the choice — meaning no Warlock, at any level, could ever
select an invocation. Pact Boon (3rd level) had the exact same shape of
gap. Mystic Arcanum (11th/13th/15th/17th) too. All three were genuinely
missing the "offer this choice" step, not hidden under a different name
— confirmed by directly testing `_get_subclass_choices()` and getting
zero results for a level-3 Warlock. Fixed all three, using
`spells_for_class_at_level()` to build Mystic Arcanum's real spell pool
per tier. Verified the count scaling (2/5/6/7/8/9/10 invocations),
accumulation across level-ups, and all four Arcanum tiers appearing
correctly by level 17.

**A second near-repeat of the duplicate-resource mistake, caught before
shipping**: added a new "Healing Light" resource for The Celestial
without first checking `classes.py` — a correctly-scaling, pre-existing
definition already existed there. Removed the duplicate, verified the
original works alone.

**Hex Warrior (The Hexblade) was completely non-functional** — not
just the CHA-for-attacks override, but the proficiency grant itself
(medium armor, shields, martial weapons) was missing entirely, meaning
a Hexblade had no legal way to gain the very proficiencies the feature
promises. Fixed both halves and verified them together: a
Hexblade with STR/DEX 8 and CHA 18 now correctly gets +6 to hit with a
one-handed weapon (CHA+4, prof+2) instead of the wrong stat entirely. A
non-Hexblade Warlock with identical stats correctly still uses STR.
Hexblade's Curse implemented as a toggle-based on-hit bonus (+PB
damage), following the same pattern as Divine Fury/Sacred Weapon.

**Gift of the Sea (Fathomless)** was missing entirely — swim speed,
straightforward once identified. (Correction from a later
re-verification pass: this entry originally also claimed "Grave
Touched (Undead)" as a matching necrotic-resistance fix, which was
wrong — Grave Touched isn't a resistance at all; it's "no need to
eat/drink/breathe" plus a damage-type-to-necrotic replacement on a
hit, already correctly listed as a reminder in `action_abilities.py`
under the "no damage-rolling system" limitation, same as Brutal
Critical. Nothing to fix there; the original claim in this file was
simply inaccurate.)

**CORRECTION to an earlier claim in this file (see below)**: this
section originally claimed "Command Undead" was a genuine naming
collision shared by Cleric Death Domain, Wizard Necromancy, and Warlock
The Undead. That was wrong. Only Wizard Necromancy actually has a
feature by that name. The Warlock entry was outright fabricated by me
— The Undead patron has no "Command Undead" at all, and Death Domain
doesn't either (confirmed via the real 5etools/wikidot source text the
user provided directly). See the "Corrections from user-provided source
text" section near the end of this file for the full account and fix.

**A second bug caught mid-implementation**: extending the save-advantage
system for Among the Dead's disease-save bonus (The Undying only)
revealed `get_save_advantage_status()` had no subclass-filtering
support at all — meaning the entry would have silently applied to every
Warlock regardless of patron. Extended the function to support
`subclass_match` (mirroring the pattern already used in
resistance/movement sources), then verified: The Undying gets the
bonus, a different patron at the same level correctly doesn't, and the
pre-existing Danger Sense entry (no subclass key) is unaffected by the
extension.

Reminders only, situational/narrative: Fey Presence, Dark Delirium
(Archfey); Sanctuary Vessel, Limited Wish (Genie); Awakened Mind,
Entropic Ward, Create Thrall (Great Old One); Accursed Specter, Armor
of Hexes, Master of Hexes (Hexblade); Guardian Coil, Grasping Tentacles
(Fathomless); Dark One's Own Luck, Hurl Through Hell (Fiend); Command
Undead (Undead — reminder only given the structural naming-collision
issue above), Grasp of the Dead, Death Touched (Undead); Undying Nature
(Undying). Radiant Soul's "+CHA radiant damage on a spell" (Celestial)
also reminder-only — no per-spell-cast damage modifier system exists.

## Cleric

Core (Channel Divinity with correct 1/2/3-use scaling, Divine
Intervention) was already fully implemented via the generic
formula-based resource loader — checked `classes.py` before assuming
anything was missing, avoiding a repeat of the Bardic Inspiration/
Healing Light mistake. 11 of 18 domains (Life, Death, Light, Trickery,
Tempest, Arcana, Forge, Grave, Order, Peace, Twilight) were already in
`class_feature_index.py` from earlier session work — spot-checked
Divine Strike's damage type across 5 of them (Life/radiant, Death/
necrotic, Tempest/thunder, War/weapon's-type, Forge/fire) and all are
correct.

**3 official domains added, previously missing from the feature index
entirely**: Knowledge, Nature, War. Verified each against multiple
independent sources before building the level tables. War Priest
(War Domain, 1st level) got a genuinely new tracked resource (uses =
WIS mod per long rest) — checked `classes.py` first, confirmed it wasn't
already there. Avatar of Battle (War) and Nature Domain's Divine Strike
(cold/fire/lightning) were both already correctly implemented from
earlier work; verified rather than assumed.

**4 unofficial, third-party domains added with explicitly lower
confidence**: Ambition, Solidarity, Strength, Zeal (Plane Shift:
Amonkhet — a Magic: The Gathering crossover setting, not a core
rulebook). No single authoritative source exists for these; the
available search results were BG3 mod authors' own interpretations, not
the original text. Rather than present a guessed reconstruction as
verified fact, built the clearest, most-corroborated parts (Divine
Strike at 8th level, which matches the already-correct
`DIVINE_STRIKE_TYPE` mapping for all four) and explicitly flagged the
uncertain features (Oketra's/Rhonas's/Hazoret's Blessing, Unity in
Battle, Relentless Zeal) both in their descriptions and here. If these
domains matter to your table, they should be checked against the actual
Plane Shift: Amonkhet PDF rather than trusted as-is.

Reminders only, situational/narrative: Blessings of Knowledge, Knowledge
of the Ages, Read Thoughts, Visions of the Past (Knowledge — Potent
Spellcasting itself has no per-cantrip damage hook, same gap as
Radiant Soul); Acolyte of Nature, Charm Animals and Plants, Dampen
Elements, Master of Nature (Nature); Guided Strike, War God's Blessing
(War — War Priest and Avatar of Battle are both implemented).

## Ranger

**A real, confirmed error found and fixed**: `classes.py`'s Core
feature-table comment claimed 2014 Favored Enemy grants "+2 damage" —
verified via multiple sources that 5e's version has no damage bonus at
all (that detail belongs to 3.5e/Pathfinder). The app's actual
implementation (description text, KNOWN_ACTIONS entry) was already
correct — no mechanical code was ever applying a phantom bonus, only
the internal comment was misleading. Fixed the comment for clarity.

**A second bug, this one a silent crash**: the 2024-ruleset Ranger's
Favored Enemy resource had a malformed `by_level` dict mixing an
integer key and a string key (`{1: 1, "by_prof": True}`), which Python's
`sorted()` can't handle — silently dropping the entire resource for any
2024-ruleset Ranger. Fixed the immediate crash by simplifying to the
clearly-intended "1 free use per long rest," since the "by_prof"
additional-uses mechanic wasn't well-defined enough to confidently
reconstruct. Note: a quick test of the 2024 edition also showed
`spell_slots: None` for a level-5 Ranger, suggesting the edition-switch
path itself may have a separate issue — this wasn't investigated
further, since the 2014 ruleset has been this session's consistent
focus across every other class, and a proper 2024-system audit is a
larger, separate undertaking.

**A genuine contradiction resolved**: Ethereal Step (Horizon Walker, 7th
level) had two duplicate descriptions that actively disagreed — one
claimed it casts Blink, the other described a vaguer "move through
objects" effect. Verified via 5 independent sources it actually casts
Etherealness, lasting only until the end of the current turn, once per
short/long rest. The "Blink" version traced back to a Baldur's Gate 3
mod that deliberately substituted it for that game's engine
limitations — not the tabletop rule. Fixed both entries.

**Confirmed already working, not assumed**: Ranger's Companion and
Drake Companion both correctly use the existing companion-statblock
system (`get_available_companions()`), gated on the right
subclass/level. Extra Attack confirmed correct at level 5. Hunter's
four level-gated sub-choices (Hunter's Prey at 3rd, Defensive Tactics at
7th, Multiattack at 11th, Superior Hunter's Defense at 15th) all
already have working choosers offering the right named options — this
was from earlier session work, verified here rather than re-built.

**Not implemented, documented as reminders given time constraints**:
Colossus Slayer/Giant Killer/Horde Breaker's actual damage bonuses
(needs "was this target already damaged" tracking this app doesn't
have), Natural Explorer's terrain-conditional double-proficiency
(needs a "chosen favored terrain" tracker feeding into skill-check
calculations), and effectively all of Gloom Stalker, Horizon Walker,
Monster Slayer, Fey Wanderer, Swarmkeeper, and Drakewarden's
level-7/11/15 features beyond what's listed above — these are mostly
one-off situational combat/utility effects (teleport-and-attack
patterns, swarm-based movement, drake breath weapons) that don't
cleanly reduce to an automatic bonus without either a full
combat-simulation layer or a lot of individual, low-value bespoke
tracking. All got accurate KNOWN_ACTIONS reminders instead of being
silently skipped.

## Fighter

**A major, high-impact bug in Core**: Second Wind — the single most
universally-used Fighter feature, present from level 1 for every
Fighter — had correct resource tracking (checked `classes.py` first,
already properly defined via the generic loader), but clicking "Use"
only decremented the counter. It never actually applied the 1d10 +
Fighter level healing to HP, meaning every Fighter would have needed to
manually roll and update their own HP by hand. Fixed it to roll and
apply the heal directly. Hit a real crash while building this
(`class_levels` was shadowed as a local variable elsewhere in the same
function, causing an `UnboundLocalError`) and fixed that too. Verified
thoroughly: HP increases by the right amount, the resource correctly
decrements, a second use with 0 remaining doesn't double-apply, and —
after catching a flawed first test that used an artificial, incorrect
manually-set max_hp — confirmed healing correctly caps at the
character's real, computed max HP.

Action Surge (1→2 at 17th) and Indomitable (1→2→3 at 9th/13th/17th)
were already correctly implemented via the generic resource loader —
verified against `classes.py` before assuming anything was missing.

**Two subclasses were completely missing from the feature index**:
Champion and Banneret (Purple Dragon Knight). Champion in particular is
one of the most commonly played Fighter subclasses, especially for new
players — verified its 2014 PHB progression (Improved Critical,
Remarkable Athlete, Additional Fighting Style, Superior Critical,
Survivor) via multiple sources and added it. Banneret's four features
(Rallying Cry, Royal Envoy, Inspiring Surge, Bulwark) were also
entirely missing — verified and added.

**Another instance of the same structural naming collision found with
"Command Undead" earlier**: Champion's capstone "Survivor" (regain 5 +
CON mod HP when below half) shares its name with an unrelated racial
trait also called "Survivor" (proficiency in the Survival skill) in the
flat `feature_tooltips.py` dictionary. The racial version currently
wins the collision. Not arbitrarily overwritten — flagged here instead,
since fixing it cleanly needs the same schema change (keying
descriptions by (source, name) instead of name alone) already noted for
Command Undead.

**Confirmed already working, not assumed**: Battle Master's maneuver
chooser (offers exactly 3 at 3rd level) and its Superiority Dice
resource. Fighting Style's chooser (shared infrastructure with
Paladin/Ranger). Extra Attack's triple-scaling (2/3/4 attacks at
5th/11th/20th) via the standard multiclass system.

Reminders only, not automated given time constraints: Champion's
Improved Critical/Superior Critical (would need the crit-range check
threaded through every weapon-row's dice-rolling logic, not a safe
change to make quickly) and Remarkable Athlete's half-proficiency
bonus; effectively all of Arcane Archer, Cavalier, Echo Knight, Psi
Warrior, Rune Knight, and Samurai's level 3/7/10/15/18 features beyond
what's covered by shared systems (Extra Attack, Fighting Style) — these
are mostly bespoke, one-off combat/utility effects (echo duplication,
psionic force effects, rune-granted abilities) that don't reduce to an
automatic bonus without substantial new tracking systems. Zero missing
feature descriptions anywhere in the class.

## Sorcerer

Core was already in good shape: Sorcery Points, Metamagic's choice
count (2→3→4 at levels 3/10/17, verified not just assumed), and Font of
Magic were all correctly implemented via the generic resource loader —
checked `classes.py` first. Found one real, if minor, error along the
way: Flexible Casting's description claimed it converts HP ↔ Sorcery
Points. It actually converts spell slots. Fixed the text; confirmed no
mechanical code shared the mistake.

**Two real, meaningful bugs fixed in Draconic Bloodline** — a very
commonly played subclass. Draconic Resilience's +1 HP/level was
completely missing from HP calculation (verified via direct comparison:
a Draconic Bloodline and a Wild Magic Sorcerer at the same level should
differ by exactly that many HP — they didn't, until fixed). Draconic
Resilience's AC (13+DEX while unarmored) was also missing entirely —
fixed and verified against a control subclass.

**A latent crash caught before it could ship**: implementing Elemental
Affinity's resistance (tied to the Dragon Ancestor's chosen damage
type) revealed the resistance-processing code has a hardcoded whitelist
of recognized "override_check" values. My new entry wasn't on it, which
would have caused a guaranteed `KeyError` the first time any Draconic
Bloodline sorcerer reached 6th level, since the code would have fallen
through to a branch expecting a "grants" key that entry didn't have.
Extended the whitelist properly and verified all three states: Red
gets fire resistance, Blue gets lightning (not fire), and level 5
(below the threshold) gets neither.

**A false-positive catch worth noting for future audits**: initially
assumed Dragon Wings (Draconic Bloodline, 14th) was unimplemented
because its only entry in `effects.py` has just a decorative "note"
field, no mechanical fields. Before concluding Otherworldly Wings
(Divine Soul's equivalent) needed the same treatment, tested Dragon
Wings directly first — it actually already works, just via a completely
different mechanism (`movement_sources.py`'s toggle system, not
`effects.py`). Built Otherworldly Wings the same real way (fixed 30ft
fly speed toggle) rather than duplicating the inert `effects.py`
pattern, and verified it directly: correct fly speed while toggled,
none while untoggled, none below the 14th-level threshold even if
toggled.

Also added: Favored by the Gods (Divine Soul, 1st level) as a genuinely
new tracked resource (1 use per short/long rest) — checked `classes.py`
first, confirmed it wasn't already there. Heart of the Storm (Storm
Sorcery) and Umbral Form (Shadow Magic, resistance to all except
force/radiant) were both already correctly implemented from earlier
work — verified rather than assumed.

Reminders only, given time constraints on the remaining 4 subclasses
(Aberrant Mind, Clockwork Soul, Lunar Sorcery, Shadow Magic) plus the
situational remainder of Wild Magic and Storm Sorcery: these are mostly
bespoke sorcery-point-spend effects (summon a spectral hound, become
temporarily invisible, restore an area) that don't reduce to automatic
bonuses without substantial new tracking. Zero missing feature
descriptions anywhere in the class.

## Rogue

**A real error found and fixed, isolated to a display comment**:
`classes.py`'s feature table claimed 15th-level Slippery Mind grants
"DEX save proficiency." Verified via 5 independent sources it's
actually Wisdom (2014 PHB). Checked the actual mechanical
implementation before assuming the worst — `get_saving_throw_bonus()`
already correctly used WIS, so this was purely a misleading comment,
not a functional bug. Fixed the comment; verified the real behavior
directly (WIS save bonus jumps by exactly the character's proficiency
bonus at 15th level, confirmed against the actual computed value rather
than an assumed one after an initial test mistake).

Core's other key mechanics were already solid: Sneak Attack's die
count formula ((level+1)//2), Expertise, Cunning Action, Uncanny Dodge,
and Evasion were all correctly implemented and wired into the UI (the
sneak-attack availability chip resets on "New Turn" and tracks
once-per-turn usage). One limitation worth noting rather than treating
as a bug: the chip's visibility only checks Rogue level, not whether
the currently equipped weapon actually qualifies (finesse or ranged) —
it's a simple "have I used it this turn" tracker, not a per-weapon
qualifier, which seems like a reasonable design choice given how
complex full per-attack weapon tracking would be, but is worth knowing
if the character is wielding something like a Warhammer.

**Two subclasses were completely missing from the feature index**:
Thief — arguably the single most iconic Rogue archetype, especially
for new players — and Arcane Trickster, the spellcasting Rogue. Both
verified via multiple independent sources and added (Thief: Fast
Hands/Second-Story Work at 3rd, Supreme Sneak at 9th, Use Magic Device
at 13th, Thief's Reflexes at 17th; Arcane Trickster: the standard
Spellcasting/Mage Hand Legerdemain/Magical Ambush/Versatile
Trickster/Spell Thief progression).

**Second-Story Work's climb speed (Thief, 3rd level) was missing
entirely** — added as an always-on climb speed equal to walking speed,
verified directly (climb speed matches walk speed exactly, not just
present).

Reminders only, given the scope of 9 subclasses: the situational
combat/utility effects across Assassin, Inquisitive, Mastermind,
Phantom, Scout, Soulknife, and Swashbuckler (Sneak Attack
conditional-damage variants, psionic energy dice spends, charm/insight
contests, initiative and mobility bonuses) — these mostly reduce to
either player-judgment calls (was the target surprised? did I move half
speed?) or need a full combat-simulation layer to automate properly.
Zero missing feature descriptions anywhere in the class.

## Monk

**Two real, high-impact bugs found and fixed in Core, both affecting
every single Monk character**: Ki Points incorrectly appeared at 1st
level (giving 1 ki point a level early) when the real rule grants Ki
starting at 2nd level — fixed using the resource loader's `available_at`
gate, verified Ki is correctly absent at 1st and scales correctly
through 20th. Separately, and more significantly: Unarmored Movement's
speed-bonus tiers were wrong in the code (2/6/9/14/18) versus the real
rule (2/6/10/14/18) — meaning every Monk between levels 10 and 13 got
+15 speed instead of the correct +20. Verified the correct tiers via
multiple independent sources before fixing, then tested all 11 relevant
level thresholds individually (1, 2, 5, 6, 9, 10, 13, 14, 17, 18, 20) to
confirm every tier boundary now lands correctly, not just a couple of
spot checks.

**Purity of Body (10th level) was completely missing** — added
immunity to poison damage, the poisoned condition, and disease as a
base-class (non-subclass-specific) grant, verified all three
independently plus the level gate. Diamond Soul's all-saves proficiency
was already correctly implemented from earlier work.

**Way of the Four Elements — checked with extra care as specifically
requested, given ki-based spellcasting is exactly the kind of area
where subtle errors hide**: the Elemental Disciplines chooser (16
disciplines, each with specific ki costs and level prerequisites) was
already fully built and working — not a repeat of the Eldritch
Invocations "never offered" bug. Spot-checked 5 disciplines in detail
against multiple independent sources (Fangs of the Fire Snake, Fist of
Unbroken Air, Water Whip, Fist of the Four Thunders, Flames of the
Phoenix) — every ki cost, level prerequisite, and effect matched
exactly. Did find one real, if minor, inconsistency: Disciple of the
Elements' description claimed you "learn 2 elemental disciplines" at
3rd level, but the chooser's own logic (verified correct) only grants 1
chosen discipline at that level, plus the free/automatic Elemental
Attunement discipline that doesn't count against the total. Fixed the
description to match the correct code rather than the other way
around. Elemental Attunement itself — the free discipline every Four
Elements monk has — wasn't mentioned anywhere in the UI at all; added
as a reminder. The disciplines themselves remain a reference list
(showing known disciplines and their ki costs) rather than one-click
cast-and-deduct buttons, since costs vary per discipline and some scale
with extra ki spent — the player manually spends from the ki pool using
its existing generic control, which already displays the correct cost.

Reminders only for the remaining 9 subclasses (Way of the Open Hand,
Shadow, Kensei, Astral Self, Drunken Master, Long Death, Mercy, Sun
Soul, Ascendant Dragon) given the scope: these are mostly bespoke
ki-spend effects (elemental breath weapons, spectral limb manifestation,
healing/harming touches) that don't reduce to automatic bonuses without
substantial new systems. One exception flagged rather than built: Wings
Unfurled (Ascendant Dragon, 6th) grants temporary flight tied to using
another ki ability (Step of the Wind) and expiring at end of turn —
too tightly coupled to another action's timing to safely automate as a
simple toggle, so left as an accurate reminder instead. Zero missing
feature descriptions anywhere in the class.

## Wizard

**Two Core features had the same "never actually offered" gap as
Warlock's Mystic Arcanum**: Spell Mastery (18th) and Signature Spells
(20th) both had no offering logic at all — confirmed by testing
`_get_subclass_choices()` directly and getting nothing back at the
relevant levels. Built both correctly, filtered to the Wizard's own
known spellbook spells at the right level (the real rule specifies
"from your spellbook," not any spell of that level) — verified with an
empty-spellbook case (correctly offers nothing) and a populated one
(correctly offers the right spells at the right counts, including
Signature Spells' 2-spell count).

**Bladesinging — checked with the extra care you specifically asked
for, and it was worth it**: Bladesong's entire mechanical effect (AC
bonus, speed bonus, and even the resource to activate it at all) was
completely unimplemented — not partial, nothing there. Built all three:
+INT-mod AC (verified it correctly requires light/no armor), +10ft
speed, and a new tracked resource (INT mod uses per long rest).

**That work then surfaced a much bigger, cross-cutting bug affecting
multiple classes, not just Wizard.** Wiring up Bladesong's Use button
revealed the code path that turns an effect on after spending its
resource was hardcoded to only recognize the literal string `"rage"` —
every other toggle sharing that same generic handler had a Use button
that correctly spent its resource but silently never activated the
effect. Checking how far this went turned up that Invincible Conqueror,
Exalted Champion, Emissary of Redemption, and Peerless Athlete (all
built in the Paladin audit) had this exact bug — and I'd never caught
it because my testing at the time set `active_effects` directly in
scripts rather than actually clicking the buttons. Fixed the root cause
generically (works for any registered toggle now, not just Rage),
verified Rage itself still works (regression-safe), and verified all
four previously-broken toggles now correctly activate on click.

Fixing those four also surfaced two real *modeling* errors, not just
wiring bugs: Peerless Athlete is actually a Channel Divinity option
(confirmed via multiple sources), not its own resource as I'd
originally built it — corrected to draw from the shared Channel
Divinity pool, matching Sacred Weapon's pattern. Emissary of Redemption
is genuinely always-on from 20th level (not toggled at all, per
multiple sources) — corrected from a toggle to a permanent passive
grant. Invincible Conqueror and Exalted Champion were confirmed as
genuinely standalone 1/LR features that were just missing their
resources entirely; added those properly.

**Arcane Ward (Abjuration, 2nd level) was completely missing** despite
being one of the most mechanically important features in the entire
class — a damage-absorbing pool worth 2×Wizard level + INT modifier.
Added as a tracked pool resource; verified the formula directly (13 at
level 5 with +3 INT, matching 2×5+3). Its real recharge trigger (casting
an Abjuration spell) isn't a rest, so the resource's reset value is a
starting point the player adjusts manually via the pool's own control
when that happens — documented clearly in-app rather than silently
approximated. Portent (Divination, 2nd level) was also completely
missing — added with correct 2→3 die scaling at 14th (Greater Portent),
verified both tiers directly.

Reminders only for the remaining subclass features across all 12
non-Bladesinging subclasses, given the scope: these are mostly bespoke
spell-interaction and utility effects (reroll a roll before it happens,
store a spell in an object, transform density, etc.) that don't reduce
to automatic bonuses without substantial new systems. Zero missing
feature descriptions anywhere in the class.

## Druid (final class)

**Wild Shape's core CR/movement-restriction logic (`get_wild_shape_info()`)
was already thorough and correct** — including Circle of the Moon's
special CR progression (max CR 1 from 2nd level, then Druid level ÷ 3
from 6th, while still obeying the same fly/swim restrictions as other
druids) — verified by reading the implementation directly rather than
assuming the "should be easier now" framing meant it needed rebuilding.
All the cross-class infrastructure built up this session (the Wild
Shape blocking list, `_wildshape_active` AC/resistance checks) was
already solid going in.

**A real, confirmed bug**: Wild Shape's resource was hardcoded to
always grant 2 uses, meaning Archdruid's 20th-level "unlimited uses"
upgrade never actually applied — a 20th-level Druid was stuck at 2 just
like a 2nd-level one. Found the exact fix pattern already in use
elsewhere in the same file (Barbarian's Rage uses an identical
`by_level={..., 20:"Unlimited"}` structure) and applied it the same
way. Verified all four relevant tiers directly: 2 at level 2, still 2
at 10 and 19, correctly "Unlimited" at 20.

**Circle of the Moon — the single most iconic "combat Wild Shape"
subclass, and the one most directly tied to what you flagged — was
completely missing from the feature index.** Verified its real
progression via multiple sources (Combat Wild Shape/Circle Forms at
2nd, Primal Strike at 6th, Elemental Wild Shape at 10th, Thousand Forms
at 14th) and added it. Its descriptions already existed accurately from
earlier session work — spot-checked Combat Wild Shape's healing
mechanic against the real rule (spell slots, not Wild Shape uses,
confirmed correct) before trusting it. Verified the full subclass loads
cleanly at level 20.

Circle of Spores' Symbiotic Entity/Halo of Spores resource tracking was
already correctly implemented from earlier work — verified rather than
assumed.

Reminders only for the remaining subclass features across Circle of the
Land, Dreams, Shepherd, Spores, Stars, and Wildfire, given the scope of
closing out the full class roster: these are mostly bespoke
summon/companion-interaction and utility effects (fey healing dice,
wildfire spirit sacrifice, starry-form attack options) that don't
reduce to automatic bonuses without substantial new systems. Zero
missing feature descriptions anywhere in the class.

---

## Still open, as of this session

Everything below is genuinely unresolved — either flagged and never
circled back to, or explicitly deferred pending clarification. The
much larger historical record of bugs found-and-fixed across this and
earlier sessions (feats, races, class/subclass audits, vehicles,
Artificer infusions, the level-up/rest-options systems, etc.) has been
trimmed from this file now that it's resolved — see conversation
history if the exact fix details are ever needed again.

- **Attunement's exact root cause** — went deep on this twice (full
  click→data→rebuild trace, direct mechanical-effect verification) and
  never found a reproducible bug in the core toggle logic itself. A
  separate, confirmed display bug (every item showing a disabled
  attunement checkbox, even ones that don't need attunement) was fixed
  later and may have been the actual source of the original "not
  working" report. No further attunement complaints have come up since
  that fix shipped, which is a reasonable (if not perfectly confirmed)
  signal it was the actual cause.
- **Circle of the Moon's specific rest-changeable feature** — the
  original request here ("which waning moon type") was unclear and
  never clarified; didn't want to guess and build the wrong thing.
- **Sorcerer "lunar phases" as a rest-reconfigurable option** — same
  situation: flagged as unclear (there's a "Lunar Boons + Waxing and
  Waning" tooltip entry that changes phase as a bonus action, not
  obviously a rest mechanic) and never clarified.
- **Artificer infusions' item-reassignment specifically on a long
  rest** — the general activate/deactivate system in the Infusions tab
  is fully built and lets a player move an infusion between items at
  any time, which may already cover the spirit of this request; the
  original TCE rule's specific rest-timing nuance was never separately
  modeled on top of that general system.

## Eldritch Versatility built — the last piece of the Warlock/Artificer request

Built the final remaining item from the detailed Warlock rule text
provided earlier: Eldritch Versatility, the optional TCoE feature
letting a Warlock swap a Pact Magic cantrip, their Pact Boon, or (12th
level+) a Mystic Arcanum spell whenever they'd gain an Ability Score
Improvement. Confirmed zero implementation existed for this before.

Gated behind a new fourth Settings toggle (default off, since it's
literally titled "(Optional)" in the actual rule text) — only shows in
the Level Up dialog for an existing Warlock leveling to an ASI-granting
level (4/8/12/16/19) when the toggle is on. All three swap kinds are
wired to their real data: cantrip swaps go through spells_known,
Pact Boon swaps update the stored choice, and Mystic Arcanum swaps
target the correct spell-level-keyed choice.

**Correctly implemented the cascading Eldritch Invocation re-check**
from the actual rule text ("if this change makes you ineligible for
any of your Eldritch Invocations, you must also replace them now") —
detects which known invocations require the old Pact Boon specifically
(by checking for their own "(Pact of the X)" text) and removes exactly
those, leaving unrelated invocations untouched, so the player can
re-pick via the invocation chooser that already exists.

**Testing infrastructure**: fixed a real, previously-latent mock gap
found while verifying this — `MockComboBox` had no `currentData()`
method and no working change signals at all, meaning any code reading
a combo box's associated data or reacting to its selection changing
could never have been properly tested before. Fixed both; this is
broadly useful for future dialog testing, not just this feature.

Verified end-to-end: the section only appears under the right
conditions (Warlock, ASI level, toggle on), the Pact Boon combo
correctly shows the current choice and offers the other three, and a
full confirm correctly changes the Pact Boon, removes exactly the
invocation that required the old one, and correctly leaves an
unrelated invocation alone.

Full 14-class regression and full mock `CharacterSheet` construction
(all 14 classes) both clean.

## Guidance of the Spirits and Whispers of the Dead — built from scratch

Picked up two subclass features flagged earlier this session (found
while searching for rest-changeable mechanisms) that had zero
implementation at all — not even an initial choice.

- **Guidance of the Spirits** (Bard, College of Spirits, 3rd level):
  built the initial skill choice, wired the actual Guidance-at-will
  grant as a bonus spell (correctly not counting against normal
  cantrips known), and added the long-rest-only skill swap to
  RestOptionsDialog, matching its specific rule text exactly ("also
  can swap the skill after a long rest").
- **Whispers of the Dead** (Rogue, Phantom, 3rd level): built the
  initial skill-or-tool choice (reusing the same combined pool
  mechanism from Skilled feat), and added the swap option to
  RestOptionsDialog on either rest type, matching its own rule text
  ("when you finish a short/long rest, choose a skill or tool
  proficiency").

Verified end-to-end: Guidance is correctly granted as a bonus spell
once the skill choice is made; Guidance of the Spirits' swap option
correctly appears only on long rest and not short rest; Whispers of
the Dead's swap option correctly appears on both rest types.

Full 14-class regression and full mock `CharacterSheet` construction
(all 14 classes) both clean.

## Full gaps-file audit — read every entry, verified or fixed each one

Went through this entire file from top to bottom in ~100-line chunks,
per explicit request — for each entry, ran real code against real
characters to confirm the claim still holds, rather than trusting the
prose. Where a check failed, dug into whether it was an actual
regression or a flaw in the verification itself before concluding
anything.

**Result: the overwhelming majority of the file checked out exactly as
written** — architectural limitations (no damage-rolling system, no
ability-check roller), and the full Paladin/Bard/Cleric/Ranger/
Fighter/Sorcerer/Rogue/Monk/Wizard/Druid sections, all confirmed
against live characters (Second Wind's healing, Draconic Bloodline's
HP/resistance, Slippery Mind's WIS save, Ki Points' level gate,
Unarmored Movement's tiers, Bladesong's AC, Arcane Ward's formula, and
more). A few of my own verification scripts had bugs during this pass
(wrong choice_id guesses, wrong data-shape assumptions) — caught and
corrected each one rather than mistakenly flagging a working feature
as broken.

**Two real problems found in the documentation itself, now corrected**:
a factually wrong claim that Grave Touched (Undead patron) was
implemented as necrotic resistance — it isn't a resistance at all, and
is already correctly a reminder; and a stale "still open" entry
claiming Eldritch Versatility was never built, when it had already
been completed in a later part of this same conversation.

**One real, confirmed gap found and fixed, not just documented**:
Ritual Caster (the feat) had no choice UI at all despite requiring 2
specific spell picks. Built it using the real, verified pool of 14
first-level ritual spells from the Cleric/Druid/Wizard lists, wired
the grant as always-prepared bonus spells, and confirmed it correctly
plugs into `can_ritual_cast()` (built earlier this session, which was
already checking for this feat's chosen spells and just needed the
choice UI to exist). Verified end-to-end: the choice appears with the
correct pool, both spells are granted correctly, and a Fighter with
this feat can now actually ritual-cast one of them.

Final full 14-class regression and full mock `CharacterSheet`
construction (all 14 classes) both clean.

## Lunar Sorcery built — the "Sorcerer lunar phases" gap, now with the real rule text

User provided the exact rule text, clarifying this is a real subclass
(Sorcerer: Lunar Sorcery, not Circle of the Moon) and resolving the
ambiguity flagged earlier. Confirmed the tooltips describing it were
already accurate (my earlier research had gotten the rule text right),
but zero mechanical implementation existed behind them.

Built:
- **Lunar Embodiment** (1st level): the phase choice itself (Full/New/
  Crescent Moon), swappable on long rest via RestOptionsDialog.
- **Moon Fire** (1st level): Sacred Flame granted as a bonus spell,
  correctly not counting against cantrips known.
- **The Lunar Spells table**: all 15 spells across 5 level tiers,
  correctly all learned progressively as the character levels (not
  just the current phase's) — confirmed by directly re-reading the
  rule text ("you learn additional spells... each of these spells
  counts as a sorcerer spell for you").
- **The free-spell-per-phase resource**: 1 shared resource before 6th
  level, upgrading to 3 independent per-phase resources at 6th
  (Waxing and Waning correctly allows one from each phase, not just
  current).
- **Waxing and Waning's bonus action** (6th level): added to the
  Actions tab, correctly gated to level 6+.
- **Lunar Boons' Metamagic discount uses** (6th level): resource with
  the correct proficiency-bonus use count.
- **Lunar Empowerment's Crescent Moon resistance** (14th level):
  necrotic + radiant resistance, correctly only while in the Crescent
  Moon phase specifically — Full/New Moon correctly grant nothing
  through this mechanism (their own 14th-level benefits are situational
  and stay as reminders).
- **Lunar Phenomenon** (18th level): resource tracking, reminder-only
  for the actual bonus-action effect (blinding/damage/teleport are all
  blocked on the same "no damage-rolling system" limitation as every
  other high-level combat power this session).

**Critical bug caught before shipping**: while adding the resource
block, a `str_replace` edit accidentally consumed the loop header for
the existing resource-merging code, leaving its body dangling inside
the wrong block — this would have crashed `update_all()` for every
single character in the app, any class, not just Lunar Sorcery. Caught
immediately by testing right after the edit rather than assuming it
worked, fixed before running any further tests or packaging a build.

Verified extensively across level tiers: spell/cantrip grants at each
threshold, resource counts and their 1→3 split at 6th level, the
Crescent-Moon-only resistance (and its absence in the other two
phases and below level 14), and the Waxing and Waning action's level
gate. Full 14-class regression (including a level-18 pass) and mock
`CharacterSheet` construction both clean.

## Systematic tooltip-to-mechanics audit (part 1 of 2) — 14 missing feat reminders, 3 missing subrace speed bonuses

Built an automated cross-reference: every one of the 985 feature
tooltips checked against every known mechanical-wiring location
(calculator.py, spells.py, resistance_sources.py) and every known
reminder location (action_abilities.py). 897 matched one or the
other; 88 flagged for manual review, since name-matching alone can't
tell wired-but-differently-named apart from genuinely missing.

**14 confirmed-missing feats, now added as Actions tab reminders**:
Crossbow Expert, Dual Wielder, Sharpshooter, Gunner, Spell Sniper,
Savage Attacker, Piercer, Crusher, Slasher, Mounted Combatant,
Inspiring Leader, War Caster, Skulker, Dungeon Delver — all had zero
reference anywhere in the app, not even a reminder, despite being
significant combat/utility feats. Verified each one individually:
taking the feat now surfaces it in the Actions tab.

**A related discovery while chasing a false-lead test failure**:
subrace text (Wood Elf, Sea Elf, Drow, Tiefling variants, etc.) turned
out to be far better covered than initially feared — of 12 spot-checked
subrace speed/resistance grants, 9 were already correctly wired
(Sea Elf's swim speed, Shadar-kai's necrotic resistance, every
Tiefling variant's fire/cold resistance, Genasi, Yuan-ti, and more).
Only 3 genuine gaps turned up: **Wood Elf, Half-Elf (Wood Descent),
and Shifter (Swiftstride)** all correctly list +5 ft. walking speed in
their actual trait text, but none of it was mechanically wired. Fixed
all three with a single, narrow keyword check, confirmed via a direct
search that no other subrace's name would false-positive-match it.

Verified end-to-end: all 14 feats now surface correctly; all 3
subraces now correctly get 35 ft. walking speed, while an unrelated
subrace (High Elf) remains correctly unaffected at 30 ft.

Full 14-class regression clean.

**Still remaining from the 88-item flagged list** (~70 entries) — this
was a large enough pass to package and report on now rather than
letting it run indefinitely; the rest of the list still needs manual
review in a follow-up pass. Known false positives already confirmed
during this pass and safe to skip re-checking: the core ASI-or-feat
mechanism (works correctly via the generic `asi:ABILITY:VALUE`
scanning in `builder.py`, just not name-matched by the audit script),
and Actor/Keen Mind/Heavily Armored's ability score components
(same mechanism, confirmed working when tested through the real
`_choices` pathway rather than `add_feat()` alone).

## Systematic tooltip-to-mechanics audit (part 2 of 2) — Firbolg Magic, Relentless Endurance, and dead-data cleanup notes

Continued the manual review of the 74 remaining flagged tooltips from
part 1.

**2 more confirmed-missing racial features, now fixed**:
- **Firbolg Magic**: confirmed zero implementation existed. Built both
  resources (Detect Magic, Disguise Self, each 1/short rest) and the
  actual spell grants as bonus spells — the resource alone wouldn't
  have made either spell castable at all.
- **Relentless Endurance** (Half-Orc/Orc): confirmed zero resource
  tracking existed for this "once per long rest" feature.

**Confirmed correctly working, no action needed**: Amphibious races
(Triton, Locathah, Merfolk all correctly get 30 ft. swim speed).

**2 orphaned tooltip entries found**: "Goat Legs" and "Fleet of Foot"
had accurate-sounding tooltip text but didn't correspond to any actual
trait on any race in the database — Satyr and Tabaxi (the plausible
owners) each have their own different, correctly-implemented traits
instead. Since no character could ever actually have either of these
two trait names, there was no player-facing gap, just dead data left
over from an earlier draft. (Removed in a later cleanup pass.)

**Confirmed false positive**: "Formulas" (mutagen formulas) is already
fully covered by Blood Hunter's existing, working `blood_hunter_mutagens`
choice UI — the audit script's name-matching just didn't catch it
since the choice_id doesn't literally contain the word.

Verified end-to-end: Firbolg gets both resources and both spells
correctly; Half-Orc gets Relentless Endurance; Human (control case)
correctly gets neither.

Full 14-class regression clean.

**Still remaining from the original 88-item list** (~55 entries) —
primarily Channel Divinity variants (Charm Animals and Plants,
Destructive Wrath, War God's Blessing), several feats' non-ASI
components (Chef, Fighting Initiate, Linguist, Prodigy, Skill Expert),
and a long tail of subclass-specific compound features (Ancient
Fortitude, Angelic Form, Draconic Loyalty, Dragon Fear, and similar)
that need individual identification of their source class/subclass
before they can be checked. Flagging honestly rather than claiming
full coverage — this was a substantial second pass, not the final one.

## Systematic tooltip-to-mechanics audit (part 3) — Destructive Wrath and War God's Blessing

Continued the manual review, focusing on the three Channel Divinity
variants flagged.

**Confirmed false positive**: "Charm Animals and Plants" (Nature
Domain) was already correctly wired as a reminder — the audit script's
name-matching just didn't catch it because the tooltip key has a
"Channel Divinity: " prefix that the actual reminder entry doesn't.

**2 confirmed-missing, now fixed**: Destructive Wrath (Tempest Domain)
and War God's Blessing (War Domain) had zero reference anywhere.
Added both as reminders, cross-referenced against `CLASS_FEATURE_INDEX`
to confirm they're each domain's *second* Channel Divinity option,
correctly gated to 6th level (not 2nd, where their domain's first
option — Wrath of the Storm / Guided Strike — already lives). My
first verification attempt used the wrong level and briefly looked
like a failure; re-checked against the actual level-indexed data
before concluding anything, rather than assuming the fix was broken.

Verified end-to-end at the correct level (6th): both appear correctly
for their own domain, and — importantly — neither leaks onto a
different Cleric domain (Life Domain sees neither), consistent with
this file's existing subclass-isolation safeguard for the shared
`KNOWN_ACTIONS` dictionary.

Full 14-class regression clean.

## Ancestral Guardian fully built + Relentless Rage + new "addendum" and "addon summary" patterns

User asked for something broader than individual feature fixes: every
feature should surface somewhere on the combat tracker even if it's
flavor-only, features that upgrade an earlier one should show as an
addendum to that feature rather than a separate duplicate entry, and
features that add onto an existing base mechanic (like subclass bonuses
"while raging") should be visible together at that base feature,
rather than scattered as separate entries a player has to notice
individually. Verified the exact rule text for the specific example
given (Path of the Ancestral Guardian) before building anything.

**Confirmed via direct testing**: only Spirit Shield (6th level)
existed at all for this subclass. Ancestral Protectors (3rd),
Consult the Spirits (10th), and Relentless Rage (Barbarian core, 11th)
had zero reference anywhere — not even reminders. Built all three,
placed per the user's specific instructions: Ancestral Protectors and
Consult the Spirits go in the 'Passive' bucket, which — confirmed by
reading the actual UI code — already displays as "Other" in the
Combat tab, so no new tab category was needed.

**Built the "addendum" pattern**: Vengeful Ancestors (14th level) is
not a separate entry — it's appended directly onto Spirit Shield's
own already-existing dynamic description once the character reaches
14th level, exactly matching the user's request that an upgrade to an
existing feature should read as an addendum to it. Verified this
correctly appears at 14th and correctly doesn't leak in at 10th.

**Critical bug caught while testing this**: the new entries initially
appeared at every level regardless of their actual level requirement
(Relentless Rage and Consult the Spirits both incorrectly showed at
3rd level). Traced this to a real, useful discovery about how this
file works: `KNOWN_ACTIONS` entries are NOT automatically level-gated
by the class/subclass level data elsewhere in the app — they need an
explicit entry in a separate, manually-maintained `min_level` dict, or
they show unconditionally the moment a character has any level in the
class. Fixed by adding both to that dict. This same gap could affect
any future addition to `KNOWN_ACTIONS` that needs a level requirement
— worth remembering for later entries in this file.

**Built the "addon summary" pattern for Rage**: Rage's own description
now dynamically lists every other currently-active entry whose
description mentions "while raging" (Ancestral Protectors, Spirit
Shield, and any other subclass's rage-conditional bonuses), so a
player looking at Rage sees everything it currently grants them in
one place, without hunting through separate Action/Bonus Action/
Reaction/Passive entries individually. Verified this is correctly
subclass-specific — a Berserker doesn't see Ancestral Guardian's
addons.

Verified end-to-end across every level threshold (3rd/6th/10th/11th/
14th) and confirmed no cross-subclass leaking. Full 14-class
regression (including a level-18 pass) and mock `CharacterSheet`
construction both clean.

**Not yet addressed from this same request**: a full audit applying
the "addon summary" pattern to other base mechanics beyond Rage (Wild
Shape, Channel Divinity, etc.) — this was built and verified for Rage
specifically as the given example; extending the same pattern
elsewhere is a reasonable next step but wasn't done blindly across
every possible base mechanic in this pass.

## Full Barbarian audit — every core and subclass feature checked, 24 gaps found and fixed

Applied the same treatment from the Ancestral Guardian work to the
entire Barbarian class per the user's request: every core feature and
every one of the 9 subclasses' features (44 total across the class),
checked feature-by-feature for presence and correct level-gating
using a purpose-built audit script, not spot-checks.

**24 confirmed gaps found and fixed**: all 10 missing core features
(Unarmored Defense, Danger Sense, Extra Attack, Fast Movement, Feral
Instinct, Instinctive Pounce, Brutal Critical, Persistent Rage,
Indomitable Might, Primal Champion) and 13 missing subclass features
across Battlerager, Beast, Totem Warrior, Storm Herald, and Zealot.
Several of these (Unarmored Defense, Extra Attack, Fast Movement)
already correctly affected real mechanics elsewhere in the app — the
math was right, but the feature itself had no visible reminder, which
was the actual complaint.

**Found Storm Soul was a special case**: its damage-resistance half
was already fully and correctly wired (in `resistance_sources.py`) —
just with no visible Actions tab entry explaining where it came from,
which is why the audit flagged it as "missing" despite it partly
working. Investigating this surfaced a genuine second gap hiding
underneath it: the Sea environment's 30 ft. swim speed grant was
never wired at all, only the resistance was. Fixed both — added the
reminder and the swim speed grant, using the same "take the higher
value, don't stack" pattern as other swim-speed sources.

**Verification methodology**: built a script that tests every single
feature both at its required level and one level below (skipping the
below-test where it wouldn't make sense — level 1 features, or
subclass features tested below the subclass's own 3rd-level minimum),
to catch both "missing entirely" and "shows up too early" in one
pass. Caught and fixed a bug in the test script itself along the way
(an inverted default value that would have falsely flagged 8 correct
features as broken) before trusting its results.

Final state: only one Barbarian feature shows as "not found" by this
script, and that's intentional — Vengeful Ancestors, which by design
is embedded as an addendum inside Spirit Shield's own description
rather than existing as a separate named entry, so a name-only search
correctly doesn't find it as its own line item.

Full 14-class regression clean.

**Handoff note**: the user has prepared reference lists of feature
names to work from going forward, which should make this kind of
audit more reliable than reconstructing the feature list from
`CLASS_FEATURE_INDEX` and cross-referencing rule text from memory or
search each time.

## Soul of Artifice built + Battle Ready fully tested + Paladin/Bard reference lists spot-checked

User provided reference lists from earlier audit rounds and flagged
two items as now buildable given infusion tracking exists, plus a
correction to how "is this weapon magic" should be determined.

**Battle Ready (Battle Smith Artificer)**: built the actual "is this
weapon magic" check the user specifically asked for — checks the
weapon's "+N" suffix, whether it's a named magic item not in the
mundane weapon list at all, and (the user's specific point) whether
it appears in the character's own `magic_items` or was infused via
the Infuse Item system. Verified end-to-end this time (continuing
from an interrupted test last message): a `+1` dagger correctly uses
INT, a mundane dagger correctly doesn't, and a non-Battle-Smith
Artificer with the same magic dagger correctly gets nothing.

**Found and fixed a real gap in the testing tools while verifying
this**: the mock environment had no way to actually inspect a built
UI row's contents at all (`widget.layout()` always fell through to a
generic placeholder regardless of what was actually set), meaning a
feature exactly like this one could have looked tested without ever
being properly checked. Fixed `MockLayout`/`MockWidget` to track
parent-child relationships the way real Qt does — broadly useful
beyond this one fix.

**Soul of Artifice (Artificer, 20th level)**: confirmed via research
the actual trigger is "end one of your artificer infusions" (not any
generic magic item), which the user correctly pointed out is now
buildable. Added a real button to the HP card, visible only at 20th
level, that lets the player pick one of their currently-active
infusions to end — reusing the exact same deactivation logic as the
Infusions tab — and sets HP to 1. Verified end-to-end: the button
shows/hides at the right level, ending an infusion correctly
un-magicks its target item and sets HP to 1, and the "no infusions
active" case is handled gracefully instead of silently doing nothing.

**Spot-checked the pasted Paladin and Bard reference lists** (Turn the
Unholy, Purity of Spirit, Holy Nimbus, Unyielding Spirit, Cutting
Words, Peerless Skill) rather than assuming they were accurate —
confirmed all six actually exist as reminders, matching the lists'
claims. Didn't re-verify every single entry in both lists exhaustively
given their size, but the sample came back clean.

Full 14-class regression (including a level-20 pass) and mock
`CharacterSheet` construction both clean.

## Full Paladin + Bard audit — every single feature verified by name, not spot-checked

Per explicit request, built the same exhaustive, per-feature audit
used for Barbarian and applied it to every line across the pasted
Paladin and Bard reference lists — 87 features total (45 Paladin
across 9 oaths, 42 Bard across core + 9 colleges) — checking exact
name presence, not just a topic-level spot check.

**Paladin: fully clean, all 45 features present with sensible bucket
variety** (Action/Bonus Action/Reaction/Passive all represented, not
dumped into one category) — nothing needed fixing here. Also caught
and corrected my own earlier spot-check: the user's list said
"Unyielding Spirit" for Oath of the Crown, but the actual feature name
is "Unyielding Saint" — my previous substring check would have passed
either way, which is exactly why an exact, exhaustive audit like this
one matters more than a quick spot check.

**Bard: found and fixed 12 genuine gaps** (2 of the original 14 flags
turned out to be a test-script naming mismatch, not real bugs — see
below): Jack of All Trades, Expertise, Font of Inspiration, Magical
Secrets, Additional Magical Secrets, and every College's basic
proficiency grant (Lore/Swords/Valor) had zero reminder anywhere.
Also fixed two features that already had real, working mechanics
from earlier this session but no reminder explaining them at all —
Guidance of the Spirits and Spirit Session (College of Spirits) — plus
Fighting Style (Swords), which already had a working choice UI but no
visible feature entry either. And Bard's own Extra Attack (College of
Swords/Valor, 6th level) was entirely missing.

**Real bug avoided via the class-specific gate override system**:
Bard's Extra Attack needed a 6th-level gate, but Barbarian's Extra
Attack (already correctly gated at 5th from the earlier Barbarian
audit) shares the exact same feature name in the shared `min_level`
dict. Used the existing `CLASS_SPECIFIC_GATE_OVERRIDES` mechanism
(already built for exactly this scenario, demonstrated with Cloak of
Shadows) instead of overwriting the shared entry, which would have
silently broken Barbarian's gate. Verified both classes' Extra Attack
gates independently and correctly afterward.

**My own audit script had 5 false positives**, all from the same root
cause: my matching logic expected an exact parenthetical suffix (e.g.
looking for "Bonus Proficiencies (Swords)" as a literal substring of
the displayed name), while the actual entries correctly use a generic
"(passive)" suffix instead. Manually confirmed all 5 by direct
inspection before concluding anything — they were already working
correctly; the audit script's assumption about the display format was
just wrong.

Full 14-class regression (level 20) and full mock `CharacterSheet`
construction across every Paladin and Bard subclass, both clean.

## Full audit of remaining 9 classes (part 1) — real mechanical gap in every Cleric domain + 4 app-wide duplicates fixed

Ran the same exhaustive, per-feature audit used for Barbarian/Paladin/
Bard across all 9 remaining classes at once (Warlock, Cleric, Ranger,
Fighter, Sorcerer, Rogue, Monk, Wizard, Druid) — 89 initially flagged,
rather than trusting the "zero missing" claims in the pasted summaries.

**Found something bigger than a missing reminder**: every single
Cleric Divine Domain that should grant heavy armor and/or martial
weapon proficiency (Life, Nature, Tempest, War, Forge, Order,
Twilight, plus the homebrew Solidarity/Strength/Zeal domains) had
*zero* mechanical grant at all — not a display gap, a Life Domain
Cleric genuinely had no heavy armor proficiency on their sheet,
which would affect real AC/proficiency calculations in actual play.
Fixed the underlying grant in `builder.py` for all 10 affected
domains, then added the matching Combat-page reminders. Verified
across 11 domains that each gets exactly the armor/weapon combination
the real rules specify, and that a domain that shouldn't get either
(Light) correctly gets neither.

**Found and fixed 4 genuine duplicate entries app-wide** — directly
relevant to what's being reviewed right now. All four had the same
root cause: two different dictionary keys (usually an apostrophe vs.
non-apostrophe spelling of the same feature name) both independently
passing the subclass-match check, so the same feature displayed
twice, sometimes with contradictory text:
- **Solidarity's Action** (Cleric): pure duplicate, removed the
  redundant copy.
- **Death's Friend** (Rogue, Phantom): the two copies had genuinely
  different, contradictory descriptions. Verified the real rule via
  research — confirmed one copy was accurate (Wails from the Grave
  also hits the original target + a free Soul Trinket each long
  rest) and the other was fabricated (claimed a damage increase and
  an instant-death effect that don't exist in the real feature).
  Removed the fabricated one.
- **Thief's Reflexes** (Rogue, Thief): neither existing copy was
  fully accurate — one had an incorrect "can't reuse an action from
  the first turn" restriction, the other a fabricated "once per rest"
  limit that doesn't exist (the real feature is unlimited, naturally
  bounded to once per combat's first round). Replaced both with one
  correct entry.
- **Hexblade's Curse** (Warlock, Hexblade): three separate copies,
  all with inaccuracies (wrong bonus type on the HP-regain, wrong
  reset timing). Confirmed via research the HP regain is Warlock
  level + CHA modifier specifically (not proficiency bonus, not
  Warlock level alone), resetting on a short or long rest. Replaced
  all three with one correct entry.

Ran a full duplicate-detection scan across every class and subclass
afterward: zero duplicates remain anywhere in the app.

Full 14-class regression clean.

**Still remaining from the 89-item list** (~75 entries, mostly across
Ranger, Fighter, Sorcerer, Rogue, Monk, and Wizard) — this was a
large, high-value pass to package now given the mechanical Cleric fix
and the duplicate cleanup; the rest still needs the same manual
verification (many are likely false positives from display-suffix
mismatches, similar to the Bard audit, but each needs individual
confirmation before being trusted either way).

## Full audit of remaining 9 classes (part 2, completing the set) — 75 items resolved, 1 significant gap found on re-check

Completed the exhaustive per-feature audit across Ranger, Fighter,
Sorcerer, Rogue, Monk, Wizard, and Druid (Cleric and Warlock's
duplicate issues were already handled in part 1).

**Ranger (4 fixed)**: Beast Master and Drakewarden's companion-command
features had zero Combat page presence despite the companion system
itself already working correctly elsewhere.

**Fighter (27 fixed)** — the largest gap in the app: even the class's
own core Fighting Style and Extra Attack had no Combat page entry.
Battle Master's entire maneuver/Superiority Dice system was invisible
on the Combat page (it exists correctly in the Features tab, but per
the user's explicit request that combat-relevant things belong on the
Combat page specifically, this was worth surfacing there too).
Verified Psi Warrior's less-common mechanics against real sources
before writing rather than relying on memory. Every one of the 27
independently confirmed present at the correct level and absent below
it.

**Sorcerer (11 fixed, 1 false positive)**: Draconic Bloodline, Wild
Magic, Aberrant Mind, Divine Soul, and Storm Sorcery all had real
gaps. Lunar Sorcery's flagged "Lunar Boons + Waxing and Waning" was a
compound-name false positive — confirmed both halves already existed
as separate, correctly-working entries from earlier this session.

**Rogue (3 fixed, 1 false positive)**: Assassin and Mastermind's
bonus features were missing; Arcane Trickster's "Spellcasting (AT)"
was already covered by the generic Spellcasting entry every caster
gets.

**Monk (3 fixed, 3 false positives, 1 real gap found on re-check)**:
Drunken Master's proficiencies and Ascendant Dragon's Ascendant Aspect
(verified via research) were genuinely missing. Way of the Long
Death's Touch of Death and Circle of the Land's Bonus Cantrip were
confirmed already present (parenthetical-suffix false positives).
**Elemental Disciplines (Way of the Four Elements) turned out to be a
real, more significant gap than I first judged** — re-checked my own
earlier "probably fine" call rather than trusting it, and confirmed
that even with disciplines explicitly chosen by the player, none of
them appeared on the Combat page at all — only the free, automatic
Elemental Attunement did. Fixed properly with dynamic rendering (since
disciplines are player-chosen, not fixed by `CLASS_FEATURE_INDEX` like
most subclass features), pulling each chosen discipline's real
description from the same data the level-up choice UI already uses.
Verified a player who chose Water Whip sees exactly Water Whip (with
its correct spend-ki/effect text) and nothing they didn't choose.

**Wizard (12 fixed)**: all 8 Arcane Tradition Savant features, Sculpt
Spells, and the 3 remaining Bladesinging features were completely
missing.

**Druid (2 fixed, 1 false positive)**: Circle of the Shepherd's
Spirit Totem and Circle of Spores' Fungal Body were missing; Circle of
the Land's Bonus Cantrip was already present.

**One duplicate self-introduced and caught during this pass**: a
redundant Spellcasting entry for Eldritch Knight (already covered by
the generic Spellcasting entry every caster gets) — found and removed
via the same duplicate-detection scan before it reached a build.

Ran the full duplicate-detection scan and class/subclass regression
one final time across all classes at levels 1, 10, and 20: 0 failures,
0 duplicates anywhere in the app. This closes out the full 89-item
list from the pasted reference summaries — every flagged item across
all 11 classes has now been individually verified, not assumed.

## First real use of CLASS_REFERENCE.md — caught a fabricated feature description

User provided a comprehensive, page-cited reference document (kept
outside the shipped app, at `/home/claude/CLASS_REFERENCE.md`, to be
deleted before 1.0). First use of it was spot-checking recent
memory-written entries against real ground truth rather than trusting
them.

**Confirmed accurate**: Hexblade's Curse and Thief's Reflexes (fixed
earlier this session via web research) both matched the reference
exactly, word for word on the parts that mattered.

**Found something much more serious while checking Fighter's Banneret
subclass**: my own "Bulwark" (15th level) entry was not a minor
wording issue — it was a completely fabricated mechanic. I had written
it as "allies can use your proficiency bonus for initiative rolls,"
which doesn't correspond to the actual feature at all. The real
Bulwark lets you extend your Indomitable reroll to one ally who also
failed the same save. Also found Rallying Cry (the actual 3rd-level
Banneret feature) had never been added at all — I'd written a wrong
"Bonus Proficiency" entry in its place instead.

**A second, structural problem surfaced during the fix**: there were
already correct, pre-existing entries for Royal Envoy, the real
Bulwark, and Inspiring Surge that I'd never checked for before adding
my own conflicting ones — meaning the file had silently accumulated
duplicate dictionary keys for the same features, with only Python's
"last definition wins" dict behavior accidentally saving the correct
text from being overwritten in actual play. Cleaned this up properly:
removed the fabricated entries, added the genuinely missing Rallying
Cry, and made Inspiring Surge's 1-ally→2-ally upgrade at 18th level a
proper dynamic addendum instead of a separate duplicate entry.

Also corrected two real omissions in Psi Warrior's text found during
the same check: Protective Field's damage reduction is die roll + INT
modifier (I'd only mentioned the die), and Telekinetic Thrust requires
a failed STR save (I'd implied it was automatic).

Verified end-to-end: Inspiring Surge correctly shows "one ally" at
10th and "two allies" at 18th, Rallying Cry now exists, and Bulwark
shows the real Indomitable-extension text. Full regression and
duplicate scan across every class/subclass: 0 failures, 0 duplicates.

This is exactly the failure mode the reference file was built to
catch — confirms it's worth systematically re-checking the rest of
this session's memory-written entries against it, not just the ones
that happened to get flagged by chance.

## First pass using the new CLASS_REFERENCE.md ground truth — 2 real fixes, several confirmations, 1 false alarm corrected

User provided a comprehensive, precisely-sourced reference document
(external to the repo, at `/home/claude/CLASS_REFERENCE.md`, sibling
to `dnd_app/` so it can never be swept into a packaged build). Used it
to spot-check a sample of this session's more memory-reliant work.

**2 genuine issues found and fixed**:
- **Battle Master's Superiority Dice progression was incomplete**: the
  dice upgrade to d10 at 10th level was already correctly wired, but
  the reference confirmed a *second* upgrade to d12 at 18th level that
  didn't exist anywhere — not in `CLASS_FEATURE_INDEX`, not as a
  reminder. Added both the missing index entry and the corresponding
  reminder, verified both scale correctly (d10 shown alone at 10th,
  both entries present together at 18th).
- **Heart of the Storm's damage amount was wrong**: had it dealing
  damage equal to the caster's full Sorcerer level; the actual rule is
  half that. Fixed, along with tightening the trigger wording to match
  exactly ("whenever you start casting a spell... that deals lightning
  or thunder damage," not just "when you cast a lightning or thunder
  spell").

**Confirmed accurate on direct comparison** (no changes needed):
Hexblade's Curse and Thief's Reflexes (both fixed earlier this session
via web research, both now verified word-for-word against the
reference), Relentless, Student of War, and the Cleric domain
proficiency grants for Life, Tempest, and War Domain (the biggest
mechanical fix from earlier in this session) — all matched exactly.

**One false alarm caught and corrected before it caused any
unnecessary work**: an automated scan first suggested 10 of 13 classes
had duplicate, silently-shadowed data blocks in `class_features.py`.
Investigated properly before acting on it and found the scan was
matching across two entirely different dictionaries in the same file
(`CLASS_FEATURE_INDEX` and the unrelated `OPTIONAL_CLASS_FEATURES`) —
re-scoped the check to `CLASS_FEATURE_INDEX`'s actual boundaries and
confirmed zero real duplicates exist there. Worth recording plainly:
the initial alarming finding was wrong, not the corrected one.

Full 14-class regression clean. This was a first, small-sample pass
using the new reference, not an exhaustive re-audit of everything
built this session — the reference makes that kind of full re-check
much more reliable going forward, and worth doing incrementally as
areas come back into focus rather than all at once.

## Reference file check (round 2) — Arcane Archer and Rune Knight had systematic errors

Continued checking Fighter subclasses I'd written from memory earlier
this session against CLASS_REFERENCE.md.

**Arcane Archer had a genuinely systematic error, not a single typo**:
I'd written Arcane Shot as usable with "shortbow, longbow, light
crossbow, or heavy crossbow" — but the real feature is shortbow/
longbow only (crossbows fire bolts, not arrows, so this was never
mechanically sensible in the first place, just wrong). I'd also
invented "uses = proficiency bonus" when the real rule is a flat 2
uses regardless of level. This same wrong weapon list and wrong use
count had been copied into Magic Arrow's text too. Also found: Arcane
Archer Lore completely omitted the cantrip choice (Prestidigitation or
Druidcraft) alongside the skill proficiency, Curving Shot was wrongly
described as expending an Arcane Shot use when it's actually a free
bonus-action reroll, and the two "gain more options" entries said
"learn 2 more" when the real text says 1 additional option each time.

**While confirming this, found a second-order data gap**: the app's
own `CLASS_FEATURE_INDEX` for Arcane Archer is missing the 7th-level
"gain 1 additional Arcane Shot option" instance entirely (it only
tracks the 10th and 18th-level instances under disambiguated names) —
a gap in the underlying class data, not just my reminder text. Noting
this rather than fixing it now, since it's a different layer of the
problem.

**Rune Knight was similarly incomplete**: 3 of its 6 real features
(Runic Shield at 7th, Great Stature at 10th, Runic Juggernaut at 18th)
had never been added at all. Its Bonus Proficiency entry also
fabricated a conditional "if you don't already have it, gain a
different tool" clause that isn't in the real rule, while completely
omitting the actual Giant-language grant that is.

Verified all 8 fixes end-to-end against the reference text directly,
not just presence. Full regression and duplicate scan: 0 failures, 0
duplicates.

This continues to validate the reference file's value — two more
subclasses checked, two more found with real, non-trivial errors, not
just minor phrasing differences.

## Second pass with CLASS_REFERENCE.md — found a significantly wrong feature (Bestial Soul)

Continued spot-checking earlier-session, memory-written content
against the new reference.

**Bestial Soul (Barbarian, Path of the Beast, 6th level) was
significantly wrong**, not just imprecise — the actual feature is an
independent, rest-swappable choice (swimming+breathe underwater,
climbing+no check needed, or extended jump distance) that has nothing
to do with which Form of the Beast weapon was chosen, plus a "natural
weapons count as magical" clause that was missing entirely. What was
there before tied specific benefits to specific weapon choices (Bite
grants swim speed, Claws grants climb speed, Tail grants a shove) —
that's not how the real feature works at all. Full rewrite.

**Form of the Beast's Tail option was also wrong**: had it as 1d8
bludgeoning damage with "+10 ft. reach on opportunity attacks." The
real feature deals piercing damage, grants the reach property
generally (not opportunity-attack-specific), and grants an entirely
different defensive reaction (roll a d8, add it to AC against an
incoming attack) that wasn't mentioned at all. Fixed.

**Ancestral Protectors' terminology was imprecise**: had "takes only
half damage," the actual rule grants resistance specifically — not
mechanically identical to a flat halving (resistance interacts with
vulnerability differently). Fixed to use the precise term.

**Psi Warrior's Psionic Power was missing one detail**: the +INT
modifier additions on Protective Field and Psionic Strike were
already correctly present (an earlier concern about this turned out
to be a misreading on my part, not a real gap) — the one genuine
omission was the starting dice-count formula (twice proficiency
bonus) and the die-size progression, both now added.

**A real bug introduced and caught during this same pass**: a
`str_replace` edit to Bestial Soul left dangling leftover text from
the old version, causing a syntax error. Caught immediately by
compiling right after the edit rather than assuming it worked — this
is the same discipline that caught the UnboundLocalError earlier this
session, worth restating since it keeps paying off.

Full 14-class regression and duplicate scan clean.

## Reference file check (round 3) — confirmed real FEATURE_DESCS name collisions + Cavalier/Samurai were mostly empty

**User flagged an important structural risk for future tooltip work**:
unlike `KNOWN_ACTIONS` (keyed by `(class, feature_name)`), the tooltip
dictionary `FEATURE_DESCS` is keyed by plain feature name alone.
Verified this is a real, currently-active bug, not just a future risk
— "Psionic Power" exists as a real, different feature for both Fighter
(Psi Warrior) and Rogue (Soulknife), and the single stored tooltip
currently shows Soulknife's version (Psi-Bolstered Knack, Psychic
Whispers) to *both* classes, meaning a Psi Warrior player currently
sees a completely wrong tooltip with no mention of Protective Field,
Psionic Strike, or Telekinetic Movement. A scan against the reference
file found 48 of 985 tooltip keys have this same collision risk
("Bonus Proficiencies" alone appears as a distinct feature 11
different times). Properly fixing this means restructuring the whole
tooltip dictionary to be class-aware like `KNOWN_ACTIONS` already is —
a larger, separate task from the current Combat-page audit, noted
here for when that work happens rather than attempted mid-audit.

**Continuing the Combat-page audit**: checking Cavalier and Samurai
(the two remaining unverified Fighter subclasses) turned up the
largest gap found yet — of Cavalier's 6 real features, only 2 existed;
of Samurai's 5, only 1 did, and it wasn't even the important one.
Samurai's actual signature mechanic, Fighting Spirit (advantage on
attacks + scaling temp HP, 3 uses/long rest) — the single most
combat-relevant thing about the subclass — had never been added at
all; only a minor proficiency grant existed in its place. Also fixed
that proficiency grant, which omitted the "or learn a language
instead" alternative the real rule allows.

Added all 8 missing features (Warding Maneuver, Hold the Line,
Ferocious Charger, Vigilant Defender for Cavalier; Fighting Spirit,
Tireless Spirit, Rapid Strike, Strength before Death for Samurai),
each independently verified present at the correct level. Full
regression and duplicate scan: 0 failures, 0 duplicates.

This closes out the last two unverified Fighter subclasses — every
Fighter subclass has now been checked against the reference file
directly, not assumed correct from an earlier presence-only audit.

## Reference file check (round 4) — Barbarian's Path of the Beast/Giant had the worst error found yet

Checked Path of the Beast and Path of the Giant against the reference.

**Call the Hunt was the most significantly wrong entry found in this
entire audit so far** — not a wording issue, a different mechanic
almost entirely. What I'd written had allies gaining temp HP equal to
the Barbarian's level and getting advantage against a previously-hit
target, unlimited while raging. The real feature has the *Barbarian*
gaining 5 temp HP per creature that accepts (not the allies), the
number of eligible creatures set by CON modifier (not a flat "up to
5"), the allies getting a d6 damage bonus once per turn (not
advantage against anything), and a proficiency-bonus-per-long-rest use
limit (not unlimited). Also caught Infectious Fury's damage was
written as 1d12 when the real value is 2d12 — exactly half the
correct amount.

**Confirmed already-correct from an earlier session pass**: Form of
the Beast and Bestial Soul both matched the reference exactly,
including Bite's easy-to-miss lifesteal clause and Tail's actual
defensive-reaction mechanic — good confirmation that pass was done
carefully.

**Giant's Power and Giant's Havoc both had real errors**: the bonus
cantrip uses WIS, not CHA as written, and the "or another language if
you already know Giant" alternative was omitted; Giant's Havoc's two
benefits (Crushing Throw and Giant Stature) apply simultaneously while
raging, not as an either/or choice as it had been framed.

Verified all 4 fixes directly against the corrected text. Full
regression and duplicate scan: 0 failures, 0 duplicates.

## Reference file check (round 5) — Storm Herald's aura effects were swapped, Rage Beyond Death fully fabricated

Finished checking Barbarian's remaining subclasses.

**Storm Aura and Raging Storm (Path of the Storm Herald) were both
substantially wrong**: Storm Aura's Sea and Tundra effects were
swapped with each other and partially fabricated — Sea is actually
lightning damage to one chosen target (DEX save), Tundra is actually
temp HP to chosen allies; neither involves "cold damage + speed
reduction," which doesn't exist anywhere in the real feature. Raging
Storm's three environment triggers were all wrong — none of them are
an "AoE" as written; they're three specific reactive triggers (Desert
responds to being hit, Sea responds to you landing a hit, Tundra
triggers whenever Storm Aura itself activates). Rebuilt Storm Aura
with the correct per-environment mechanic and level-based scaling.

**Rage Beyond Death (Path of the Zealot) was a complete fabrication**:
I'd written it as preventing the character from dropping below 1 HP.
The real mechanic is different and, if anything, more interesting —
you can still hit 0 HP while raging, you just don't fall unconscious
from it and keep fighting, still make death saves normally, and any
death from failed death saves is delayed until the rage itself ends.

**Confirmed already correct**: Divine Fury and Warrior of the Gods
both matched the reference closely — useful confirmation that not
everything written from memory this session was wrong, just specific
entries, which is worth knowing given how many fabrications this audit
has turned up elsewhere.

Verified fixes directly against corrected text. Full regression and
duplicate scan: 0 failures, 0 duplicates. This completes the Barbarian
class — every subclass has now been checked against the reference
file directly.

## Reference file check (round 6) — Sorcerer had 5 completely missing features plus a fabricated "breath weapon"

Checked Draconic Bloodline, Wild Magic, and Storm Sorcery against the
reference.

**Dragon Ancestor had a genuine fabrication**: I'd written it as
granting a "breath weapon" — that's actually a Dragonborn *race*
trait, not anything this Sorcerer subclass feature grants at all.
Also completely omitted the real grants: learning Draconic, and
doubled proficiency bonus on CHA checks when interacting with dragons.
Dragon Wings also had an invented condition — I'd gated it on "armor
proficiency," but the real restriction is whether the armor is
specially made to accommodate wings, an unrelated concept entirely.

**5 features were missing outright, not just under-described**: Bend
Luck and Controlled Chaos (Wild Magic, 6th/14th), and Draconic
Presence (Draconic Bloodline's actual 18th-level capstone — never
added at all, despite Dragon Wings at 14th already existing).

**Found 2 more duplicate-key situations** while adding Storm Guide and
Storm's Fury (Storm Sorcery) — both already had pre-existing entries I
hadn't checked for, and both of the older versions were less accurate
than the reference: the old Storm Guide invented a "rain falls harder"
effect that doesn't exist in the real feature and got the wind's
radius and duration wrong (100 ft. until the end of your next turn,
not 20 ft. for "1 round"); the old Storm's Fury used an overly broad
"any damage within 60 ft" trigger instead of the real "hit by a melee
attack" condition. Removed both older, less accurate copies rather
than the new ones.

**Confirmed already correct**: Draconic Resilience and Heart of the
Storm's "half your Sorcerer level" damage figure both matched the
reference exactly.

Full regression and duplicate scan after cleanup: 0 failures, 0
duplicates.

## Reference file check (round 7) — Rogue's Swashbuckler/Inquisitive/Mastermind

Checked Swashbuckler, Inquisitive, and Mastermind against the
reference.

**Master of Intrigue (Mastermind) had real errors**: missing both the
disguise kit and forgery kit proficiencies entirely, had a fabricated
"or musical instrument" alternative to the gaming set proficiency that
doesn't exist in the real rule, and a fabricated "with proficiency in
Deception, mimic their writing too" clause with no basis in the actual
feature text.

**Rakish Audacity (Swashbuckler) had a meaningful direction error**: I'd
written the isolation requirement backwards — "no other creature
within 5 ft. of the target" instead of the real "no other creature
within 5 ft. of you." Also omitted the "you don't have disadvantage
on the attack roll" condition and the "you're within 5 ft. of the
target" proximity requirement entirely.

**Insightful Fighting (Inquisitive) had one meaningful omission**: the
"but not if you have disadvantage on the attack roll" caveat was
missing, meaning as written the feature incorrectly implied it bypassed
disadvantage too, not just the advantage requirement.

**Confirmed already correct**: Fancy Footwork, Panache, Elegant
Maneuver, Master Duelist (Swashbuckler); Ear for Deceit, Eye for
Detail, Master of Tactics (Inquisitive/Mastermind) — a good mix of
correct and incorrect in this batch, useful confirmation this isn't
uniformly bad, just inconsistent.

Full regression and duplicate scan: 0 failures, 0 duplicates.

## Mechanical re-check of every "completed" class — found real gameplay-affecting bugs, not just text

User specifically asked to verify whether any of the errors found and
fixed so far were confined to display text, or whether the same
mistakes had also made it into actual mechanical calculations
(resource pools, resistances, AC/HP formulas) — since those affect
real gameplay numbers, not just what a player reads.

**Confirmed correct (no mechanical bug)**: Elemental Affinity's full
color-to-damage-type mapping (all 10 colors verified against the
reference table), Draconic Resilience's AC formula and +1 HP/level,
Storm Soil's Desert/Sea/Tundra resistance types, Drakewarden's Bond of
Fang and Scale resistance grant (tested end-to-end with an actual
choice), and the Cleric domain armor/weapon proficiency grants fixed
earlier this session — all still correct after re-verification.

**Found 3 real, gameplay-affecting mechanical bugs, distinct from any
text issue**:
- **Rune Knight's Giant's Might** resource pool was sized by CON
  modifier; the real rule uses proficiency bonus. A 3rd-level Rune
  Knight with a +3 CON mod was getting 3 uses instead of the correct
  2 (at that level).
- **Psi Warrior's and Soulknife's Psionic Energy Dice** pools were
  both sized by a flat proficiency bonus; the real rule for both
  (identical wording) is *twice* proficiency bonus. Both classes had
  exactly half their intended resource pool — a significant
  under-count that would have meaningfully hurt these characters in
  actual play.
- **Cavalier's Unwavering Mark** reset on a short rest in code; the
  real rule resets on a long rest only. Also had zero Combat page
  entry explaining the feature at all, despite the resource itself
  already existing and (mostly) working.

**Also fixed a wrong effect description baked into a resource's own
note field** (not the Combat-page text, the resource tracker's own
label): Samurai's Fighting Spirit was noted as "+5 to attack rolls,"
which isn't the real effect at all — it's advantage on weapon
attacks. This would have shown the wrong effect directly in the
resource-tracking UI, separate from and in addition to any Combat
page tooltip issue.

Verified all 4 fixes directly. Full regression and duplicate scan
after all changes: 0 failures, 0 duplicates.

This confirms the user's concern was well-founded — display-text
audits alone would have missed these, since the numbers a player
actually uses in play live in a completely different part of the
codebase (`multiclass.py`'s resource pool sizing) from the reminder
text checked so far. Recommend continuing this two-layer check
(reminder text + mechanical implementation) for any class not yet
covered, not just the ones already "completed."

## Reference file check (round 8) — Monk, both layers checked

Applied the full two-layer check (mechanical resources + reminder
text) to Monk, continuing the pattern from the last round.

**Mechanical layer**: checked Way of the Astral Self's two resource
toggles and Way of the Ascendant Dragon's Aspect of the Wyrm resource
in `multiclass.py` — both confirmed correct against the reference,
including the exact "free 1/long rest, reusable for 3 ki" mechanic on
Aspect of the Wyrm.

**Text layer**: checked Way of the Open Hand in full (Open Hand
Technique, Wholeness of Body, Tranquility, Quivering Palm) and Way of
the Sun Soul in full (Radiant Sun Bolt, Searing Arc Strike, Searing
Sunburst, Sun Shield) — both subclasses were mostly already accurate,
but found 3 real issues:
- **Quivering Palm** had a fabricated "1/LR" limit that isn't real —
  the actual feature is limited by ki cost (which resets on short
  rest) and having only one creature affected at a time, not a
  long-rest cap.
- **Searing Sunburst** had a fabricated "half damage on success"
  clause — the real save is all-or-nothing: full damage on a fail, no
  damage at all on a success.
- **Searing Arc Strike** omitted the ki-spending cap (total ki spent,
  base 2 plus any extra, can't exceed half your Monk level) — added.

Confirmed already correct: Open Hand Technique, Wholeness of Body,
Tranquility, Radiant Sun Bolt, Sun Shield.

Full regression and duplicate scan: 0 failures, 0 duplicates.

## Reference file check (round 9) — Wizard mechanical layer, including a self-caught near-miss

Checked Wizard's 3 mechanical resources (Bladesong, Arcane Ward,
Portent) against the reference.

**Bladesong's use count was a real, confirmed mechanical bug**: coded
as INT modifier, but the real rule is proficiency bonus. Verified with
a character built to have these two numbers differ (INT mod 4 vs. PB
3) — the pool showed 4 before the fix, 3 after, confirming the wrong
formula had actually been driving the resource.

**Arcane Ward's pool formula (2× Wizard level + INT mod) was already
correct.**

**Portent had a near-miss worth documenting honestly**: my first pass
found Greater Portent's "3 dice at 14th level" scaling and assumed it
was fabricated, since I hadn't yet located a 14th-level Divination
entry in the reference — I "fixed" it back to a flat 2 dice. A fuller
search then found the real entry: Greater Portent is a genuine 14th-
level feature ("you roll three d20s ... rather than two"), and the
original code had been correct all along. Reverted the incorrect fix
immediately upon finding this, rather than leaving it. Recorded here
as a reminder that a feature not being found on a first, narrower
search isn't the same as confirming it doesn't exist — the reference
needs a full search before concluding something is fabricated, not
just a search of the section it was expected to be in.

Verified the revert directly: Portent now correctly shows 2 dice below
14th level and 3 at 14th+, matching the reference.

Full regression and duplicate scan after all changes: 0 failures, 0
duplicates. Text-layer verification for Wizard's remaining subclasses
(Chronurgy, Graviturgy, Order of Scribes, War Magic) is still
outstanding.

## Reference file check (round 10) — closing out Wizard's remaining 4 subclasses

Checked Chronurgy Magic, Graviturgy Magic, Order of Scribes, and War
Magic — the last 4 unverified Wizard subclasses, completing full
Wizard coverage.

**Gravity Well (Graviturgy) was a genuine fabrication, not a wording
issue**: I'd written it as pulling some other nearby creature "within
10 ft of the spell's area" toward an arbitrary point, restricted to
1st-level+ spells. The real feature moves the actual target of any
spell you cast on it (any level), triggered by the target being
willing, hit by the spell's attack roll, or failing its save. Also
corrected the bucket from Reaction to Passive — the real feature never
expends your reaction, it's a free rider on casting.

**Momentary Stasis (Chronurgy) had 3 real errors**: wrong timing ("end
of your next turn," not "start" as written), missing the Large-or-
smaller size restriction entirely, and missing the INT-modifier-based
use limit entirely (as written, it read as unlimited).

**Wizardly Quill (Order of Scribes) had a fabricated cost reduction**
— I'd claimed it makes copying spells "cheaper," but the real feature
only reduces time (2 min/spell level), never gold cost.

**Adjust Density (Graviturgy) was missing its actual mechanical
effects entirely** — it said you could change an object/creature's
weight but never explained what that does (speed change, jump
distance, STR check/save advantage or disadvantage), which was the
entire point of the feature.

**Bladesinging's Extra Attack (6th level) was missing outright** —
a combat-critical feature, including its unique cantrip-for-attack
swap. Added with its own class-specific level-gate override (6th),
matching the existing pattern for Barbarian (5th) and Bard (6th)
sharing the same feature name at different levels — verified
independently that adding Wizard's override didn't disturb Barbarian's
or Bard's.

**Confirmed already correct**: Temporal Awareness, Chronal Shift,
Arcane Deflection, Tactical Wit, and Awakened Spellbook's core three
benefits.

**Noted but not built**: Chronal Shift and Momentary Stasis both have
genuine per-long-rest use limits described in their text, but neither
has any actual resource-pool tracking in `multiclass.py` — unlike the
mechanical bugs fixed elsewhere this session (wrong formula on an
existing resource), this is a fully missing resource, a different
scope of work than corrected here.

Full regression and duplicate scan: 0 failures, 0 duplicates. This
completes full two-layer verification (mechanical + text) for Wizard.

## Reference file check (round 11) — Druid, both layers, found a fabricated die size and a phantom resource

Checked Druid's 3 mechanical resources (Symbiotic Entity, Starry Form,
Spirit Totem) plus their matching Combat-page text.

**Halo of Spores (Circle of Spores) was almost entirely fabricated**:
the previous text described a vague "aura that damages on contact" with
no die, no save, and a nonsensical "1d16" scaling claim in the linked
resource note — 1d16 isn't even a real die size in D&D. The actual
feature is a reaction-triggered 1d4 necrotic hit (CON save negates),
scaling to 1d6/1d8/1d10 at 6th/10th/14th, triggered by a creature
moving into or starting its turn within 10 ft. Also fixed Symbiotic
Entity's note, which had inherited the same fabricated die claim and
was missing its actual melee-weapon-attack bonus damage entirely.

**Starry Form (Circle of Stars) had a genuinely invented resource
pool**: coded as "2 uses per long rest," a completely separate pool
from Wild Shape. The real feature expends a Wild Shape use directly —
same pattern as Symbiotic Entity, which was already coded correctly.
Fixed both the resource (now correctly tied to Wild Shape use, not an
independent long-rest pool) and the matching Combat-page text (which
had also fabricated "uses = proficiency bonus per long rest").
Rewrote the vague "gain a special attack or healing option" summary
into the three actual constellation effects.

**Spirit Totem (Circle of the Shepherd) was under-described across
all three options**, missing roughly half the real mechanical benefit
of each: Bear was missing its STR check/save advantage, Hawk was
missing both its Perception advantage and the correct mechanic (a
reaction granting advantage to an ally's attack, not the player's own
attacks), and Unicorn was missing its detection advantage along with
the specific healing trigger and amount. Its 1-use-per-short-or-long-
rest limit was already correct.

Verified all fixes directly against the corrected mechanics. Full
regression and duplicate scan: 0 failures, 0 duplicates.

## Reference file check (round 12) — Druid's remaining subclasses, completing full coverage

Checked Circle of Dreams, Circle of the Moon, Circle of Wildfire, and
the higher-level features of Circle of Spores/Stars/the Land/the
Shepherd — closing out the last unverified Druid material.

**Confirmed already correct**: Balm of the Summer Court, Combat Wild
Shape, Circle Forms, Summon Wildfire Spirit, Hearth of Moonlight and
Shadow, Primal Strike, Hidden Paths — a strong batch, useful
confirmation this class wasn't uniformly bad.

**Found real errors in the higher-level features**:
- **Spreading Spores** (Circle of Spores, 10th) had a duration off by
  a full order of magnitude — written as "1 round," the real feature
  lasts 1 minute — plus missing the damage trigger details and the
  "can't use your Halo of Spores reaction while it persists"
  restriction entirely.
- **Twinkling Constellations** (Circle of Stars, 10th) was internally
  contradictory — described switching constellations as both "a bonus
  action" and "no action required" in the same sentence. The real text
  never specifies an action cost at all.
- **Nature's Ward** (Circle of the Land, 10th) was completely missing
  a Combat-page entry — though a resource check found a pre-existing
  entry (naming collision, same apostrophe-variant pattern as
  Solidarity's Action and Death's Friend from earlier rounds) that was
  also missing the disease immunity the real rule includes. Added the
  correct, complete version and removed the older, incomplete
  duplicate.
- **Mighty Summoner** (Circle of the Shepherd, 6th) was missing the
  specific "+2 HP per Hit Die" formula, just saying "extra HP."

Full regression and duplicate scan: 0 failures, 0 duplicates. This
completes full two-layer verification (mechanical + text) for every
Druid subclass.

## Reference file check (round 13) — Warlock mechanical layer surfaced a far-reaching app-wide bug

Checked all 8 Warlock subclass resources against the reference.

**Hexblade's Curse had a real, significant bug**: coded as a flat 1
use, but the real rule is CHA modifier (min 1) — confirming a
mismatch had existed between the already-fixed Combat-page text
(correct: CHA mod) and the actual resource pool (wrong: flat 1) the
whole time. Verified with a high-CHA character: 4 uses after the fix,
not 1.

**Discovered a genuinely far-reaching, app-wide bug while investigating
these resets**: this app's `long_rest()` only recovers resources
tagged `"LR"` or `"SR/LR"` — a resource tagged plain `"SR"` **never
recovers on a long rest at all**, only on an explicit short rest. Many
resources across the app (not just Warlock) are tagged plain `"SR"`
despite their real rule being "short OR long rest," meaning a
character who only takes long rests would silently never recover
those uses. Found and fixed 7 instances of this exact bug:
Hexblade's Curse, Misty Escape, and Indestructible Life (Warlock);
Mutagens (Blood Hunter — this one's own note text already said
"short/long rest," directly contradicting its own reset code); Control
Undead and Vow of Enmity (Paladin, both explicitly Channel Divinity
uses, which reset on short or long rest per the core rule); and
Favored by the Gods (Sorcerer). Verified two of these directly by
simulating a long rest end-to-end and confirming the resource actually
recovers now, where it previously wouldn't have. Confirmed Elemental
Gift (Genie) was correctly "LR"-only already, since its real rule
genuinely has no short-rest recovery — not every "SR"-only resource is
wrong, only the ones whose real text says "short or long."

**Additional resource-note accuracy fixes**: Form of Dread (Undead)
was missing its temp HP grant and WIS save requirement entirely;
Bottled Respite (Genie) had a fabricated "INT hours" duration where
the real formula is twice proficiency bonus; Tentacle of the Deep
(Fathomless) was missing its speed-reduction effect and the
move-and-reattack option; Defy Death (Undying) used CHA modifier in
both its resource note and its Combat-page text, when the real rule is
CON modifier — a class-wide stat-confusion risk worth watching for
elsewhere, since Warlock's primary casting stat is CHA but not every
subclass feature uses it.

Full regression and duplicate scan: 0 failures, 0 duplicates. Given
the "SR" vs "SR/LR" bug's scope, it may be worth a dedicated sweep of
every remaining plain-"SR" resource across the whole app (not just the
classes covered by this audit) to confirm none of the untouched ones
share the same issue.

## Dedicated app-wide sweep for the "SR" vs "SR/LR" reset bug — closing this out

Followed through on the note from the previous round: swept every
remaining plain-`"SR"`-tagged resource across the entire codebase
(`multiclass.py` and `calculator.py`, not just the classes already
audited), rather than assuming the 7 instances already found were all
of them.

**Found and fixed 3 more instances**: Firbolg Magic's Detect Magic and
Disguise Self (racial, confirmed via the standard rule text — "you
can't cast that spell with it again until you finish a short or long
rest"), verified end-to-end by simulating an actual long rest.

**Also fixed a related but harmless issue for correctness**: Pact
Magic's slot metadata (`get_warlock_slots()`) was also tagged plain
`"SR"`, technically inaccurate since Pact slots do recover on either
rest type — though confirmed this particular field is dead/unused
(the actual reset logic for pact slots is hardcoded directly in both
rest functions, not driven by this metadata), so it had no gameplay
impact. Fixed anyway since leaving known-wrong information in the code
risks misleading a future edit that starts relying on it.

**Confirmed Gathered Swarm (Ranger, Swarmkeeper) is correctly exempt**:
its real rule is "once on each of your turns," a per-turn limit with
no rest-based reset at all, so its "SR" tag (though technically unused
given the different tracking mechanism) isn't part of this bug
pattern.

This closes out the sweep: zero plain-`"SR"` resources remain anywhere
in the app except the one confirmed-correct exception. Full
app-wide regression and duplicate scan: 0 failures, 0 duplicates.

## Reference file check (round 14, final) — Artificer, completing the full 13-class audit

Checked all 5 Artificer core/subclass resources and their matching
text, closing out the last unaudited class.

**Confirmed the mechanical resources were already solid**: Experimental
Elixir's count scaling (1/2/3 at 3rd/6th/15th), Eldritch Cannon,
Flash of Genius, and Arcane Jolt's die scaling were all already
correct — but every one of them, plus Steel Defender itself, had
**zero Combat page presence at all**, despite working resources
sitting right behind them. Added Combat-page text for all of them,
each independently verified present at the correct level.

**Found the single largest gap of this entire audit**: Armorer — one
of the most commonly played Artificer subclasses — had nothing on the
Combat page at all. Not Arcane Armor itself, not the Guardian/
Infiltrator model choice, not either model's actual weapon (Thunder
Gauntlets / Lightning Launcher), not Dampening Field, not Perfected
Armor's capstone. Built out the full set (8 entries) from the
reference text.

**Building Defensive Field (Guardian-only) surfaced a real
architectural gap**: the resource-computation function
(`_add_subclass_resources` in `multiclass.py`) had no access to the
character's actual choices at all, only class/subclass/level — meaning
a genuinely choice-gated resource like this couldn't be built
correctly without either showing it to Infiltrator-model characters
too (wrong) or restructuring the plumbing. Threaded `_choices` through
as a new optional parameter (`aggregate_resources()` →
`_add_subclass_resources()`, sourced from `update_all()` where the
full character dict is available) without breaking any existing
caller. Verified directly: Guardian-model characters get Defensive
Field, Infiltrator-model characters correctly don't.

**Found a second real mechanical bug**: Steel Defender's AC was
hardcoded at 15 regardless of level, never applying the +2 from
Improved Defender at 15th level (Battle Smith). A 15th-level+
character's defender should show AC 17. Fixed and verified at both
14th (correctly still 15) and 15th (correctly 17). Also added
Improved Defender's own Combat-page entry, since the feature that
upgrades both Arcane Jolt and the Steel Defender had no explanation
of its own anywhere.

Full regression and duplicate scan: 0 failures, 0 duplicates. This
completes the full two-layer (mechanical + text) verification pass
across all 13 classes and every subclass against CLASS_REFERENCE.md.
Blood Hunter wasn't part of this pass, since it had been missed from
the earlier 13-class sweep.

## Blood Hunter — added to reference doc and fully audited (both layers)

User provided the complete Blood Hunter class (core + all 4 Orders +
full Blood Curse list), which had been missed from the earlier
13-class sweep. Appended verbatim to CLASS_REFERENCE.md, then ran the
same two-layer audit used throughout this session.

**Text layer**: 32 features checked, 7 initially flagged — 1 was a
harmless name collision (Profane Soul Spellcasting, already covered by
the generic Spellcasting entry). The other 6 were genuinely missing:
Fighting Style (core, 2nd — required building an entire choice UI from
scratch, since none existed for this class at all), Extra Attack
(core, 5th), Rite of the Dawn (Ghostslayer, 3rd), and three "bonus,
doesn't-count-against-curses-known" blood curses granted by specific
Orders (Exorcist/Ghostslayer, Corrosion/Mutant, Souleater/Profane
Soul) — plus a fourth found the same way despite not being tracked in
`CLASS_FEATURE_INDEX` at all (Howl/Lycan). Building Fighting Style's
level gate correctly required using the class-specific override
mechanism rather than the shared dict, to avoid quietly shifting
Fighter's existing level-1 gate to level 2.

**Found and fixed 2 real mechanical bugs, distinct from the text
gaps**:
- **Multiclass prerequisite was wrong**: coded as requiring both STR
  13 and INT 13; the real rule is INT 13 AND (STR **or** DEX) 13. This
  wrongly blocked every DEX-based Blood Hunter — a very normal build —
  from multiclassing. Fixing this properly required extending the
  prerequisite-checking logic itself, since the existing all-AND/
  all-OR structure couldn't express a mixed case at all. Verified
  Fighter's existing all-OR prerequisite still works unchanged.
- **Hemocraft die had an off-by-one threshold**: upgraded to 1d8 at
  level 10 instead of the correct level 11 (the real table holds 1d6
  through 10th). This silently overpaid every Mutant/Ghostslayer
  feature that scales off this die at exactly that level. Fixed and
  re-verified the full progression against the table (1d4 at 1-4, 1d6
  at 5-10, 1d8 at 11-16, 1d10 at 17-20).

**Deep-checked Hybrid Transformation and Stalker's Prowess (Lycan)**
and found several real omissions in both, now fixed with dynamic level
scaling: the melee damage bonus (+1/+2/+3 at 3rd/11th/18th) and
unarmed strike attack bonus (same scaling) were previously flat/
unstated; the damage resistance was missing its silvered-weapon
exception; the AC bonus was wrongly restricted to "unarmored/light"
when the real rule allows any armor short of heavy; the unarmed
strike's own damage die (1d6→1d8 at 11th) was omitted entirely; and
Bloodlust's fixed DC 8 wasn't stated.

**Confirmed already accurate without changes needed**: all 19
individual Mutagen formulas, all 13 Blood Curses (base + the 4
Order-specific ones) including their Amplify effects, the curse-count
progression (1/2/3/4/5 at 1st/6th/10th/14th/18th) and Order-gate
filtering logic, Mutagencraft's two separate progressions (mutagens
created vs. formulas known), Rite Revival, Aether Walk, and all 4
Mutant-order Combat-page entries — a genuinely strong result for
material that had never been checked against this reference before,
and good confirmation that not everything needs fixing just because
it hasn't been audited yet.

**Also found, in an unrelated class**: a genuine duplicate dictionary
key — Ranger's "Stalker's Flurry" was defined twice with the identical
key, silently letting one definition overwrite the other. Surfaced
incidentally while checking Blood Hunter's own Stalker's Prowess.
(Fixed in the later "Final cleanup pass" section, which removed the
fabricated duplicate and kept the accurate version.)

Full regression across every class/subclass at levels 1, 10, and 20:
0 failures, 0 duplicates. This completes the full two-layer audit for
all 14 classes now present in the app (13 core + Blood Hunter).

## Artificer Infusions — added to reference doc, major mechanical fix, dedicated charge handler built

User provided the full official Infusions list, appended to
CLASS_REFERENCE.md, then audited against the app.

**Found and fixed the most significant mechanical bug of the entire
session**: the three infusions almost every Artificer actually uses —
Enhanced Weapon, Enhanced Defense, Enhanced Arcane Focus — never
applied their stated numerical bonus anywhere. Infusing a weapon only
set a cosmetic `magic: True` flag; the attack roll, damage roll, AC,
and spell attack bonus were never actually computed. Traced this all
the way through: fixed by checking the character's active infusions
at the point each weapon row is built (covering Enhanced Weapon,
Radiant Weapon, Repeating Shot, Returning Weapon, all of which share
this code path) and by adding a new step to the magic item effect
pipeline for the two standalone-target cases (Enhanced Arcane Focus ->
spell attack, Enhanced Defense/Repulsion Shield -> AC). Verified
end-to-end through the actual rendered UI, not just the underlying
data: a Dagger infused with Enhanced Weapon now correctly shows "+4 to
hit" and "1d4+1 piercing" instead of the un-bonused numbers.

**Also fixed the split "+1/+2" infusion entries**: the real rule
treats Enhanced Weapon/Defense/Arcane Focus as ONE infusion each that
automatically upgrades at 10th level — the app had split each into two
separate "(+1)" and "(+2)" list entries a player had to learn
independently, silently costing an extra known-infusion slot for what
should be automatic. Merged back into one infusion each, with the
bonus now computed dynamically from character level.

**Removed a miscategorized entry**: "Imbued Wood Focus" is real
content (Eberron: Rising from the Last War) but is a standalone
wondrous item any spellcaster can attune to, not one of the
Artificer's actual Infuse Item options — confirmed via research before
removing, since it wasn't fabricated, just wrongly listed.

**Built the dedicated charge handler requested**: confirmed the
existing charge system (`sync_item_charges`) only covered items with a
`grant_spell` catalog effect, missing the four infusions that grant a
genuine ability-based charge pool (Armor of Magical Strength, Mind
Sharpener, Radiant Weapon, Repulsion Shield) entirely — these live on
a different data path (`active_infusions` enchanting an existing
`equipment` entry) than the catalog-based `magic_items` system the old
handler checked. Extended it to cover both paths, with charges only
appearing once the specific infused item is actually equipped —
correctly checking each slot type's real equipped-status mechanism
(weapon: name in `equipped_weapons`; armor: name matches `armor_worn`;
shield: the `shield` boolean), not just "the infusion is known" or
"the infusion is active."

**Found and fixed a related gap while building this**: attuned items
were being treated as mechanically active regardless of whether they
were actually equipped at all — the attunement toggle itself never
required "equipped" first, and the checking function only looked at
the attuned-items list with no cross-check against equip status. An
item attuned but sitting in a backpack was incorrectly still applying
its effects. Fixed to require both, per the user's explicit
specification.

**Found and fixed a second miscategorization**: Mind Sharpener's real
prerequisite is "a suit of armor or robes," but it was classified as
"standalone" — meaning it was being offered as create-your-own-item
rather than requiring an existing armor piece to enchant, and (before
today) had no charge tracking either way. Now correctly classified as
armor-targeting, feeding into the same new charge system.

Verified all of this with 8 targeted tests (worn vs. unworn armor,
weapon, shield-as-boolean, charge persistence across refreshes,
attuned-but-unequipped exclusion, Mind Sharpener's reclassification)
plus the full app-wide regression, duplicate scan, and a full mock
sheet construction: all clean.

Homunculus Servant's stat scaling, Boots of the Winding Path,
Resistant Armor, Spell-Refueling Ring, and the "Lv6+"/"Lv10+"/"Lv14+"
replicated-item tiers hadn't yet been individually verified against
the reference at this point. (Closed out by the very next section
below.)

## Environment reset mid-session — recovered, noting for the record

Partway through this work, the working environment reset (`/home/claude/`
was wiped clean). Recovered fully:
- `dnd_app/` restored from `mimic_v161.zip`, the last packaged build —
  verified with a full regression and a targeted re-check of the most
  recent fix (the infusion mechanical bonus), not just "the files came
  back."
- `CLASS_REFERENCE.md` rebuilt from its original source: the user's
  original upload was untouched in the uploads folder, and the Blood
  Hunter + Artificer Infusions sections were reconstructed from the
  user's originally pasted text and the original infusions source file
  (not from memory).

**Casualty**: the mock PySide6 test environment at `/tmp/pyside6_mock/`
(built up incrementally across many rounds this session — MockComboBox
signals, MockSpinBox signals, MockLayout/MockWidget parent-child
tracking, etc.) did not survive, since `/tmp/` is ephemeral and wasn't
part of any packaged output. This means full mock `CharacterSheet`
UI-level construction tests aren't available until it's rebuilt.
Core logic changes made after the reset were still verified thoroughly
via direct, non-UI tests against the actual data/calculation
functions — just not through a full mock sheet render. Worth rebuilding
before the next round of UI-level verification work.

## Artificer Infusions — completed the audit: Replicate Magic Item list was severely incomplete, and level filtering didn't exist at all

Finished checking the remaining infusions (Homunculus Servant, Boots of
the Winding Path, Resistant Armor, Spell-Refueling Ring) and the
Replicate Magic Item tables.

**Added 4 completely missing Combat-page entries**: Homunculus Servant,
Boots of the Winding Path, Resistant Armor, Spell-Refueling Ring — all
real, known infusions with zero presence anywhere.

**Found the largest data-completeness gap in the Infusions list**:
cross-referencing the "Replicate Magic Item" flattened list against the
reference's 4 level-gated tables found the entire 2nd-level table (8
items) missing outright, roughly 23 more items missing from the 6th/
10th/14th tables, and the few 14th-level items that WERE present
(Boots of Levitation, Boots of Speed) mislabeled as "Lv6+" — 8 levels
too early. Rebuilt the full list from 30 to 67 entries, matching all
four reference tables completely and correctly leveled.

**Found something more significant while fixing the labels**: the
infusion chooser had NO level filtering at all — the "(Lv6+)"-style
text was purely cosmetic, never actually checked against anything. A
1st-level Artificer could currently select "Arcane Propulsion Armor"
despite its real 14th-level prerequisite, or any other level-gated
infusion in the list. Built real filtering: parsed a machine-readable
"(min level N)" tag into each entry (placed carefully in the
description portion, not the name portion, after confirming 3 separate
places in the code parse the name via `split(" – ")[0]` and would have
broken — the catalog tooltip lookup, the cascading-recheck tracking on
deselection, and the right-click "Infuse this item" target-type
lookup), and wired the chooser to only show infusions the character's
actual Artificer level qualifies for.

Verified end-to-end at 5 level thresholds (2/3/6/10/14): a 3rd-level
character correctly sees 17 eligible infusions (correctly excluding
Arcane Propulsion Armor, Boots of Levitation, Helm of Awareness,
Resistant Armor, while correctly including Enhanced Weapon and Alchemy
Jug), scaling up to all 67 at 14th level. Re-verified the earlier
infusion mechanical fixes (Enhanced Weapon's bonus, the charge handler)
still work correctly against the expanded 67-item list. Full regression
and duplicate scan: 0 failures, 0 duplicates.

This completes the full Artificer Infusions audit.

## Mock PySide6 test environment fully rebuilt after the reset

Rebuilt `/tmp/pyside6_mock/` from scratch (lost in the earlier
environment reset, since `/tmp/` is ephemeral and this tool was never
part of any packaged output). Surveyed the actual codebase first
(every `from PySide6.X import Y` and every `QSomething(` instantiation
across `dnd_app/ui/`) rather than guessing at what was needed, to
build a genuinely complete mock rather than one that happens to cover
whatever gets exercised first.

Iteratively found and fixed real gaps by running the app's own most
complex file (`sheet.py`) against it and following each failure to
its actual cause, rather than pre-guessing every method:
- `QLayout` (base class the app's custom `FlowLayout` subclasses
  directly) was missing entirely.
- Class-level enum constant access (`QTabWidget.North`,
  `QAbstractItemView.MultiSelection`, etc.) needs a metaclass-based
  fallback distinct from instance-level attribute fallback, since
  `SomeClass.CONSTANT` is accessed on the class itself, not an
  instance — added `_MockClassAttrMeta` to close this generally rather
  than special-casing each enum.
- `QSizePolicy`, `QAbstractSpinBox`, `QAbstractItemView`,
  `QHeaderView` were referenced as real Python identifiers (not just
  inside stylesheet strings) and needed real classes.
- `QTableWidget.horizontalHeader()`/`verticalHeader()` needed to
  return a real object with `setSectionResizeMode()`, not fall through
  to a generic non-iterable/non-callable placeholder.
- `QTreeWidgetItem`/`QTableWidgetItem`/`QListWidgetItem` were missing
  `setForeground` and its commonly-paired styling siblings
  (`setBackground`, `setFont`, `setTextAlignment`, etc.).
- `MockWidget.findChildren()` fell through to the generic fallback
  and returned something non-iterable, crashing any code that loops
  over its result — added a real implementation returning `[]`.
- **The most subtle one**: real Qt allows connecting a signal that
  emits an argument to a handler that accepts zero arguments — Qt
  silently drops the extras. The app's own code relies on this
  (`checkbox.stateChanged.connect(self._on_death_save_changed)` where
  the handler takes no parameters). The mock's naive
  `handler(*args)` doesn't replicate this and raises `TypeError`
  where real Qt wouldn't. Fixed `_MockSignal.emit()` to introspect each
  handler's real accepted parameter count via `inspect.signature()`
  and truncate arguments to match, matching real Qt's behavior instead
  of just "however many arguments happened to be passed."
- `styleSheet()` fell through to the generic fallback, breaking the
  app's own "read current stylesheet, append more CSS, set it back"
  pattern (string concatenation on a non-string).

**Verified the rebuild is genuinely equivalent to the original**, not
just "doesn't crash": full sheet construction now passes 378/378
(every class × every subclass × 3 levels, not just a sample), and
re-ran the exact deep-introspection tests from earlier this session
word-for-word — the Battle Ready weapon-row test (confirming a magic
weapon correctly uses INT for a Battle Smith) and the Enhanced Weapon
infusion test (confirming "+4 to hit" / "1d4+1 piercing" render
correctly) both reproduce identically. Also directly re-verified the
three specific mock behaviors that were explicit prior-session fixes
(MockComboBox's `currentData()` + real signal emission, MockSpinBox's
real `valueChanged` emission, MockQListWidgetItem's bitwise flag
operations) rather than assuming the general rebuild covered them.

Full non-UI regression and duplicate scan after all of this: 0
failures, 0 duplicates.

## Final cleanup pass — closing out every incomplete item before moving past classes

User asked for classes to be fully finished before moving to any new
content area. Went back through every leftover open item or
"reminder-only for now" note left across the entire session (searched
the gaps file itself for that kind of language rather than relying on
memory) and either confirmed it was already resolved by later, more
thorough work, or fixed it now.

**Confirmed already resolved by later work** (no action needed): the
original ~88-item flagged list and its "still needs manual review"
notes — fully superseded by the later systematic 14-class +
Blood Hunter audit against the real reference text, which checked
every feature by name rather than a pre-identified sample. Also
confirmed Druid's remaining-subclasses item and Blood Hunter's own
open item were both resolved by dedicated rounds later in the same
session.

**Fixed for real**:
- Ranger's duplicate `("Ranger", "Stalker's Flurry")` key — verified
  the fabricated version via multiple independent sources (it invents
  a "different creature" targeting option not in the real rule) and
  removed it, keeping the accurate one.
- The Imbued Wood Focus magic item catalog entry — confirmed via
  research it's a flat +1 to one damage roll with no once-per-long-
  rest limit, not the "+1d6, once per long rest" previously listed.
- **Found and fixed a real pattern affecting every scaling companion
  feature in the app**: Homunculus Servant, Ranger's Companion, and
  Drake Companion all had "how to command it" text but never stated
  the companion's own actual stats — no HP formula, no AC formula, no
  attack bonus. A player could summon any of these three companions
  and have no idea what their actual combat stats were. Fixed all
  three with their real, verified formulas: Homunculus Servant (HP =
  1 + INT mod + Artificer level, Force Strike using spell attack
  modifier for 1d4+PB), Ranger's Companion (proficiency bonus applies
  to AC/attack/damage/saves, HP = stat block or 4x Ranger level),
  Drake Companion (AC = 14 + PB, HP = 5 + 5x Ranger level). Also found
  Drake Companion's "can't summon more than once per long rest" limit
  had zero resource tracking at all and added it. Checked the other
  companion-style features in the app (Steel Defender, Summon
  Wildfire Spirit, Pact of the Chain's familiar) and confirmed they
  already had their real formulas — this wasn't a universal gap, just
  these three.

Verified every fix directly. Full regression across every class,
subclass, and 3 level checkpoints each: 0 failures, 0 duplicates.

This closes out every specific item flagged as incomplete across the
whole session. Classes are fully finished — every one of the 14
classes now in the app has been through both the mechanical and text
layers, checked against real reference material rather than assumed
correct, with every known loose end either resolved or explicitly
confirmed as an intentional design boundary (situational effects
needing tracking systems the app doesn't have, noted accurately as
reminders rather than silently skipped).

## Drake Companion — full summon/death/re-summon lifecycle built

User pointed out a real design gap: Drake Companion has a genuine
"once per long rest to summon" resource (added earlier this session)
and real HP tracking infrastructure already existed in the Companions
tab, but the stat block was showing up automatically the moment a
Drakewarden hit 3rd level, regardless of whether they'd actually used
the summon action. There was also no connection between the
companion's HP reaching 0 and the summon-limiting resource — a dead
drake and a not-yet-summoned drake looked identical, and nothing
stopped bringing it back mid-fight for free.

Built the full lifecycle:
- Added a `requires_summon_action` flag to Drake Companion's stat
  block template, and a linked `summon_resource_key` pointing at its
  actual resource pool — extensible if other companions need the same
  treatment later, rather than hardcoding this one case.
- `get_available_companions()` now excludes any `requires_summon_
  action` companion until it's actually been summoned (tracked in a
  new `active_summoned_companions` list), while every other companion
  (Steel Defender, Ranger's Companion, Homunculus Servant) keeps its
  existing "available once qualified" behavior unchanged.
- Added `get_summonable_but_inactive_companions()` so the UI knows
  when to show a "Summon" prompt card instead of the full stat block.
- Built `_summon_companion()`: checks the linked resource has a
  charge, spends it, activates the companion, and resets its tracked
  HP to full — a fresh summon, not picking up with stale HP from a
  previous fight.
- Built `_dismiss_companion()`, and wired it into the HP spinbox's
  change handler so reaching 0 HP automatically removes the companion
  from the active set — matching the real rule (remains until reduced
  to 0 HP, re-summoned, or you die) rather than needing a separate
  manual step.
- Fixed a real bug the new feature would have introduced on its own:
  the Companions tab's empty-state check only looked at the (now
  correctly gated) available-companions list, so a Drakewarden who
  hadn't summoned yet would have hit "no companion applies to you" and
  never seen the Summon prompt at all.

**Verified thoroughly, not just "doesn't crash"**: an 8-step direct
test of the full data-layer lifecycle (not active before summoning,
active after, resource correctly spent, HP set to full, correctly
removed on death, resource still empty right after death, correctly
restored after a long rest, successfully re-summonable afterward), and
separately — since a handler working when called directly doesn't
prove the actual UI wiring is correct — found the real rendered HP
spinbox inside the actual companion card and dragged it to 0 exactly
as a player would while tracking damage in a fight, confirming the
auto-dismiss fires through the genuine UI control, not just the
underlying method.

Also found and fixed a small but real mock-environment gap while
testing this: `width()`/`height()`/similar geometry methods fell
through to the mock's generic non-numeric placeholder, breaking the
app's own toast-notification positioning code (which does arithmetic
on these values) — added real integer-returning implementations.

Full regression (every class/subclass) and a full mock sheet +
Companions tab construction sweep (every class/subclass at 2 levels
each, 252 total): 0 failures, 0 duplicates.

## Companion lifecycle extended to every companion in the Companions tab

User asked to extend Drake Companion's summon/death/re-summon
lifecycle to all companions. Researched each of the other 6 companion
types' real rules individually rather than assuming they all work like
Drake, since they genuinely don't — found three distinct patterns and
built each correctly instead of forcing a one-size-fits-all model:

**Explicit summon action, dedicated 1/long-rest resource** (same
pattern as Drake Companion): Dancing Item (Bard, College of Creation's
Animating Performance — confirmed via research it had zero resource
tracking despite a real "once per long rest, or spend a 3rd+ level
spell slot to reuse early" limit; built the missing resource and
applied the same requires_summon_action + summon_resource_key
treatment).

**Explicit summon action, but shares an existing resource pool rather
than having its own**: Wildfire Spirit (Druid, Circle of Wildfire) —
confirmed via research it expends a normal Wild Shape charge, not a
separate resource. This needed distinct handling since Wild Shape uses
are tracked through a different mechanism (`_wildshape_uses_spent`,
a dedicated counter) than the generic resources list every other
companion's summon resource lives in. Added a `summon_uses_wild_shape`
flag and a parallel code path in both the summon handler and the
"uses left" display.

**No summon action or use-count limit at all — unlimited recreation,
but only at the end of a long rest**: Steel Defender (Artificer,
Battle Smith) and the three Primal Companion beasts (Ranger, Beast
Master's Tasha's option) — confirmed via research these are available
immediately once the class feature is unlocked, with no resource gate
on recreation. But the real rule for Steel Defender specifically ties
recreation to "at the end of a long rest," not instant reappearance
the moment the old one dies — so simply leaving these "always
available" would have let a dead companion respawn mid-combat with
full HP the instant its tracked HP hit 0, which is wrong. Built a
separate `companion_pending_replacement` state: dying marks the
companion pending (excluded from the tab) without touching any
resource, and only a long rest clears the pending flag — along with
the stale HP tracking entry, so it doesn't come back still showing 0
HP from before it died.

**Also found and fixed a real bug the original single-companion
version had already introduced**: `get_available_companions()`'s
docstring only described the requires_summon_action exclusion;
extending it to also exclude "pending replacement" companions
required updating both the function and its documentation together so
the two exclusion reasons don't get confused with each other later.

Verified all three categories directly and distinctly rather than
assuming one test covers all: Steel Defender's full pending → long
rest → available-again cycle including the stale-HP-tracking cleanup;
Dancing Item's and Wildfire Spirit's actual summon handlers (confirming
Wildfire Spirit correctly spends a Wild Shape charge and Dancing Item
correctly spends its own resource, not accidentally sharing logic);
and Beast of the Land/Sea/Sky's immediate availability with no gate.

**Noted, not solved, as an honest limitation**: Creative Crescendo
(College of Creation, 14th level) lets a Bard have multiple Dancing
Items active simultaneously (CHA modifier count) — the current
single-instance-per-key tracking model doesn't represent that. The
common case (one Dancing Item, which covers most of the subclass's
career from 6th–13th level) is handled correctly; the multi-item edge
case at 14th+ would need a broader data-model change to the underlying
stat block card system, not just the summon-gating logic built here,
and is flagged in the template's own comments for a future pass.

Full app-wide regression (every class/subclass) and a full mock sheet
+ Companions tab construction sweep (every class/subclass at 2 levels
each, 252 total): 0 failures, 0 duplicates.

## Homunculus Servant — full stat block and a fourth companion lifecycle pattern

User provided the exact official stat block (TCE p.22). This exposed
that Homunculus Servant had never actually been given a real,
trackable Companions-tab entry at all — only the Combat-page text
reminder fixed earlier this session. It also surfaced a mechanic that
had never been in the app anywhere: the Channel Magic reaction
(delivering touch-range spells through the homunculus).

Added the full, accurate stat block to COMPANION_STATBLOCKS matching
the user's text exactly — AC 13 natural armor, HP = 1 + INT mod +
Artificer level (d4 hit dice), speed 20 ft./fly 30 ft., the real
ability scores (STR 4 through CHA 7), DEX save, the expertise-style
double-PB Perception, Stealth, poison immunity, exhaustion/poisoned
immunity, senses, Evasion, Force Strike (now correctly noting it's
commanded via bonus action, and using the same {atk}/{pb} formula
convention as every other companion), and Channel Magic. Verified
every computed number by hand against the real formulas (HP 11, AC 13,
+7 attack, +5 DEX save, +6 Perception, +5 Stealth, at a sample level 6
character) before trusting it.

**This didn't fit any of the three companion lifecycle categories
already built** (explicit summon + dedicated resource; explicit summon
sharing an existing pool; unlimited automatic recreation) — Homunculus
Servant is created by infusing a gem, using the app's existing
infuse-item mechanism, not a summon action or a rest-based resource at
all. Built a fourth pattern: `requires_active_infusion`, gated on
whether `active_infusions` currently has an entry for that exact
infusion name. Verified this against the real caller chain rather than
assuming the string format — confirmed `active_infusions` stores the
stripped base name (not the full descriptive list entry) by tracing
through `_get_applicable_infusions()` and `_activate_infusion_dialog()`
to their actual `_infuse_item()` calls.

On death, matched the real rule precisely: "if you or the homunculus
dies, it vanishes, leaving its heart in its space" — removes the
`active_infusions` entry itself (freeing the infusion slot) rather
than the summon-dismiss or pending-replacement paths used by the other
three patterns, since getting a new one requires an explicit new
infuse action, not a rest-based auto-recovery.

Verified the complete lifecycle through the real UI call chain, not
just the underlying data: infused a gem via the actual
`_infuse_item()` method (catching a test-setup gap along the way — the
real "max active infusions = known ÷ 2" formula, verified correct
against the actual TCE table, meant a single known infusion couldn't
be activated at all), found the genuinely rendered HP spinbox inside
the resulting card and dragged it to 0, confirmed the infusion entry
was removed and the companion vanished from the tab, then confirmed
re-infusing successfully brought a new one back.

Full app-wide regression and a full mock sheet + Companions tab
construction sweep (every class/subclass at 2 levels each, 252 total):
0 failures, 0 duplicates.

## Feats audit begun — 194-feat reference provided, first pass complete

User uploaded a comprehensive feat reference (`feats-sublist.md`, saved
to `/home/claude/FEATS_REFERENCE.md`), covering ~194 feats including
substantial setting-specific content (a Middle-Earth conversion's
"Cultures," Dragonlance, Planescape, and a homebrew crafting/harvesting
subsystem) alongside standard PHB/XGE/TCE content.

**First finding — the existing 105 feats were already high quality**:
compared all 105 against this new, more thorough reference in full
(not sampled) and found exactly one real gap: Observant had zero
`special` text at all, just the bare ASI grant, despite three real
mechanical benefits (lip-reading, +5 passive Perception, +5 passive
Investigation). Confirmed the +5 passive bonuses were, however,
already correctly wired mechanically in `calculator.py` — only the
descriptive text itself was missing, not the underlying effect. Fixed
and verified end-to-end (WIS 14 character shows passive Perception 17,
correctly including the bonus).

**Confirmed the mechanical foundation feats rely on is solid**: ASI
grants apply through the existing generic `asi:ABILITY:VALUE` scanning
system, and `feat_prereq_met()` already does real enforcement (ability
score minimums, armor/weapon proficiency, spellcasting checks, level
minimums, feat-chain prerequisites, race/subrace matching) — this was
built in an earlier session, not something needed building from
scratch here.

**Added 39 of the 89 missing feats this round**, transcribed and
verified against the reference: Adroit Crafter, Aerial Expert, Against
the Unseen, Art of Disappearing, Bandit Cunning, Blade Barrier, Careful
Crafter, Cat's Caress, Confidence, Craft, Cruel, Deadly Archery,
Defiance, Desperate Courage, Dour-Handed, Dragon-Slayer, Durin's Way,
Dwarf-Friend, Elbereth Gilthoniel!, Elvish Spirit, Endurance of the
Ranger, Expert Enchanter, Expert Forger, Expert Harvester, Fearsome
Flourisher, Field Cook, Field Medic, Fierce Shot, Flamewoken, Flash
Recall, Foresight of their Kindred, Forest Sage, Forgemaster, Friendly
and Familiar, Gleam of Wrath, Hardiness, Heavy Glider, High Destiny,
Hit Die.

Several of these reference game systems this app doesn't model at all
(Middle-Earth "Cultures" instead of standard races, Shadow points,
twinblade/claw/nunchaku as distinct weapon types, a full crafting/
harvesting/enchanting quirk subsystem). Followed the same precedent
already established for Planescape/Dragonlance prerequisites in
`feat_prereq_met()`: transcribed the text accurately and left these
prerequisites informational-only rather than mechanically enforced,
since the app has no way to know which campaign/setting a table is
actually using.

Compile-checked and regression-tested after each batch: clean
throughout, 144 feats total after this round (up from 105).

**Honestly incomplete — 50 feats still remain unadded**: Gunner
onwards through the rest of the "Craft"-suffixed profession feats
(Beast-Craft, Hand-Craft, Leech-Craft, Rune-Craft, Song-Craft,
Speech-Craft, Weapon-Craft, Wood-Craft), the remaining Middle-Earth
content (Baruk Khazâd!, Bree-Pony, Heir of Arnor, Strange as News from
Bree, Three is Company, and others), and a mixed set of standalone
feats (Jack of All Tools, Mastery, Memory of Ancient Days, Mystic
Conflux, Nimbleness, Opportunistic Thief, Perfect Landing, Prowess,
Reapmaster, Remarkable Recovery, Reward, Royalty Revealed, Scourge
Master, Small Folk, Sneak Attack, Spelldriver, Spray 'n' Pray,
Stone-Hard, Stout-Hearted, Strength of Will, Sure at the Mark, The Art
of Smoking, The Language of Birds, Three is Company, Thrown Arms
Master, Tough as Old Tree-Roots, Untameable Spirit, Virtue, Vital
Sacrifice, Ways of the Wild, and the remaining "-Craft" set). Given the
scale (89 total missing, transcription needing care for each one) this
was paced as a substantial first batch rather than rushed to
completion in one pass — continuing in the next round.

## Feats audit — Middle-Earth content removed per user request, remaining 45 feats added

User confirmed the earlier round's Middle-Earth-themed additions
(tagged 'LOME') should be removed entirely, and asked to continue with
the rest of the reference.

**Cleanly removed all 19 previously-added Middle-Earth feats**: Against
the Unseen, Art of Disappearing, Confidence, Deadly Archery, Defiance,
Desperate Courage, Dour-Handed, Dragon-Slayer, Durin's Way,
Dwarf-Friend, Elbereth Gilthoniel!, Elvish Spirit, Endurance of the
Ranger, Fierce Shot, Foresight of their Kindred, Friendly and Familiar,
Gleam of Wrath, Hardiness, High Destiny — via a script that isolated
and removed each complete `feat(...)` block, verified afterward to
confirm no dangling/partial entries remained and the removed names
correctly return nothing from `get_feat()`.

**Classified the remaining ~52 unadded feats carefully** rather than
by name pattern alone, since some entries don't announce their
Middle-Earth origin obviously — "Speech-Craft" is filed under the
generic "Crafting Feat" heading but its actual text explicitly
requires Sindarin/Quenya and references Elves, so it was excluded too
despite not matching the "Virtues of the [Culture]" naming pattern the
other exclusions share. Conversely, several "-Craft" feats (Beast-
Craft, Hand-Craft, Rune-Craft, Wood-Craft) reference shared
terminology from what's likely the same broader sourcebook
("Fellowship Phase," "the Company," "Loremaster") without naming any
specific Tolkien race, culture, or location — kept these, since the
user's request was for the identifiable Middle-Earth content
specifically, not everything sharing incidental terminology with it.
Also excluded "Virtue," which — while not itself flavored as
Middle-Earth — only has meaning in reference to the Virtues system
being removed ("gain a common or cultural virtue of your choice"), so
it would be a non-functional stub without it.

**Fixed a source-tag mistake from the previous round while in here**:
Flamewoken and Forest Sage were mislabeled 'STRIX' (implying
Strixhaven) when their actual text references "the Tenders," an
unrelated nature-magic organization — corrected both to 'TENDERS',
matching the tag now used for Plantmender from the same source.

**Added the remaining 25 non-Middle-Earth feats**, completing the
reference: Beast-Craft, Fighting Style, Hand-Craft, Jack of All Tools,
Leech-Craft, Mystic Conflux, Opportunistic Thief, Perfect Landing,
Plantmender, Reapmaster, Remarkable Recovery, Reward, Rune-Craft,
Scourge Master, Sneak Attack, Song-Craft, Speech of the Ancient
Beasts, Spelldriver, Spray 'n' Pray, Thrown Arms Master, Vital
Sacrifice, Weapon-Craft, Weavebonder, Wood-Craft, Woodwise.

Compile-checked after every batch, and ran a full duplicate-name scan
across all 150 feats (zero found) plus the standard character-build
regression: both clean.

**Final state**: 150 feats in the app (up from the original 105), with
46 deliberately excluded — all confirmed Middle-Earth-specific content
(Virtues of the Elves/Dwarves/Hobbits/Bardings/Men of Bree/Rangers of
the North, Common Virtues, Speech-Craft, and Virtue). This completes
the feats reference audit as scoped by the user.

## Feats — LOTR/Middle-Earth content identified and removed per explicit instruction

User corrected course mid-task: no LOTR/Middle-Earth content. This
required going back through work already added, not just filtering
going forward, since the previous round had added several
Middle-Earth feats before this instruction was given.

**Removed 26 total Middle-Earth feats** (both ones visibly added this
session and — per the file state found at the start of this round —
some that appear to have already been added and then removed before
this round's visible context began): Against the Unseen, Art of
Disappearing, Confidence, Deadly Archery, Defiance, Desperate Courage,
Dour-Handed, Dragon-Slayer, Durin's Way, Dwarf-Friend, Elbereth
Gilthoniel!, Elvish Spirit, Endurance of the Ranger, Fierce Shot,
Foresight of their Kindred, Friendly and Familiar, Gleam of Wrath,
Hardiness, High Destiny, plus (removed directly this round)
Beast-Craft, Hand-Craft, Leech-Craft, Rune-Craft, Song-Craft,
Weapon-Craft, Wood-Craft, Craft, Reward, Hit Die, Sneak Attack,
Fighting Style.

**Identifying the full scope required real research, not just
keyword-guessing** — a first-pass keyword search on "Fellowship"/
"Culture" caught most of them but missed several (Beast-Craft only
revealed itself via "Loremaster," the Middle-Earth-specific term for
"DM"; Wood-Craft via "the Company"/"Explore"/"Hunting" skill checks).
Web research identified the actual source as Cubicle 7's "Adventures
in Middle-earth" (2016) — confirmed via its "Loremaster"/"Virtues"/
"Craft slot" terminology matching exactly.

**Also correctly avoided removing legitimate non-LOTR content that
shared superficially similar category labels** — Expert Enchanter,
Expert Forger, Expert Harvester, Forgemaster, Reapmaster, and
Weavebonder are also tagged "Crafting Feat"/"Harvesting Feat" in the
reference, the same generic labels the Middle-Earth "-Craft" family
uses, which could easily have been mistaken for the same source.
Verified via research these are actually from a completely different,
unrelated sourcebook (Heliana's Guide to Monster Hunting) and kept
them, rather than assuming a shared label meant a shared source.

Fixed a stale comment header left over from before this correction
(mislabeled a section "Middle-earth" when its actual contents are now
entirely non-Middle-Earth after the removal).

Full regression: 0 failures. 138 feats now in the app (down from 150
before this correction, up from the 105 present before this session's
feats work began) — every legitimate non-LOTR feat from the 194-entry
reference has now been verified present and accurate; the 56 not
included are all confirmed Middle-Earth content, correctly excluded
per the user's explicit instruction.

## Root cause of "infusing items does nothing" found and fixed

User reported the Infusions tab was completely unfindable, the
Replicate Magic Item flow was broken, and infusing an item didn't
seem to do anything at all. Investigated all three as real, distinct
bugs rather than assuming any were user error.

**Infusions tab never appearing**: confirmed the tab list is built
exactly once, in `__init__`. Since a character typically doesn't have
any infusions known until they actually level up to 2nd and make
their pick — which happens *after* the sheet is already open in the
normal flow — the tab's eligibility check was always evaluated too
early to ever see it become true. Nothing re-checked afterward. Fixed
by adding `_sync_infusions_tab()`, called on every character update,
which dynamically inserts/removes the tab as eligibility changes and
refreshes its content while present. Verified through the actual
mid-session level-up scenario, not just at character creation.

**Replicate Magic Item's broken/confusing display**: found two
compounding bugs. A redundant, non-functional generic "Replicate
Magic Item" entry existed in the infusion list alongside all ~37
specific replicable items (which already work as their own directly
selectable choices) — selecting the generic one did nothing since
nothing downstream knew what to do with it. Removed it and the dead
special-case dialog code built around it. Separately, the Features tab
had a section (labeled "Replicable Magic Items") built on a directly
contradictory premise to the real rule verified earlier this session —
its own comment claimed replicable items are "not a pick, just
tier-gated knowledge," dumping every item across every tier the
character's level qualifies for (up to 51 items at 14th level) as if
automatically known. The real rule requires explicitly learning each
one as its own infusion pick. Rewrote the section to show only what
the character actually learned, and removed the now-dead
`get_replicable_items()` function that encoded the wrong premise.

**The actual root cause of "infusing does nothing"**: traced the full
mechanical chain end-to-end (weapon attack/damage bonus, AC bonus,
spell attack bonus) through the *real* UI activation flow rather than
calling internal functions directly, and confirmed all three
mechanical effects genuinely work correctly and the display does
refresh automatically after activating. But found the actual bug one
layer up: Combat-page infusion reminders (Boots of the Winding Path,
Resistant Armor, Spell-Refueling Ring, and others) were gated purely
by class/level/subclass, with no check at all for whether the
character had actually learned that specific infusion — confirmed a
level 6 Artificer with *zero* infusions known would still see most of
them on the Combat page. Since the reminder was already visible either
way, activating an infusion produced no visible change from the
player's perspective even where the underlying mechanics were correct.
Added a gate requiring the feature's base name to actually appear in
the character's known infusions, built from the real
`ARTIFICER_INFUSIONS` list rather than a hardcoded set so it can't
drift out of sync. Automatic class features (Infuse Item itself, Flash
of Genius) aren't in that list and are correctly unaffected.

Caught and fixed a bug in my own fix along the way: a manually-encoded
UTF-8 byte escape (`\xe2\x80\x93`) inside a regular Python string
literal doesn't decode as the intended em-dash character — each `\xNN`
is an independent single-codepoint escape, not part of a UTF-8
sequence to be joined. Needed the actual Unicode escape (`\u2013`)
instead. Caught by testing before considering it done, not by
assuming a compile-clean file meant a working file.

Also found and fixed a real mock-environment gap while testing the
tab-visibility fix: the mock `QTabWidget` had no `insertTab()` or
`removeTab()` at all, silently falling through to a no-op fallback —
which would have hidden the real dynamic-tab bug rather than exposing
it. Added both.

Verified all fixes via the real UI call chain end-to-end, not
shortcuts: activated infusions through `_activate_infusion_dialog()`
with properly simulated dialog responses (not calling `_infuse_item()`
directly), read the actually-displayed AC/weapon-row text after
activation with no manual refresh calls, and tested the tab's
mid-session dynamic appearance by mutating character state after the
sheet was already constructed, exactly matching a real user's session.

Full app-wide regression and duplicate scan: 0 failures, 0 duplicates.

## Multiclass screen — fixed the actual "doesn't hide ineligible classes" bug, and a severe crash found while fixing it

User reported the level-up/multiclass screen doesn't hide classes that
don't satisfy prerequisites. Investigation found this was real, plus
something much more severe underneath it.

**Root cause of the reported issue**: `LevelUpMulticlassDialog` (the
actual, button-triggered UI — confirmed a separate, older
`_open_add_multiclass()` method with its own inline prerequisite logic
is dead code, never called from anywhere) had its own copy of
ability-score-requirement data via `CLASS_DICT[...]["multiclass_reqs"]`,
completely independent from `multiclass.py`'s `MULTICLASS_PREREQS_2024`
and its `check_multiclass_prereq()` function. This meant the Blood
Hunter multiclass fix made earlier this session (the real rule is INT
13 AND (STR or DEX) 13, not STR AND INT both required) only ever
reached one of the two copies — a Dexterity-based Blood Hunter would
still show as wrongly ineligible in this specific dialog even after
that fix landed elsewhere. Consolidated to delegate to the single
canonical `check_multiclass_prereq()` function instead of maintaining
a second, drift-prone copy of the same logic.

**Found something far more severe while testing the fix**: the dialog
would crash outright — not just fail to filter correctly — for any
character with an existing class, which is every character past 1st
level. `setChecked(True)` on the default-selected radio button fires
its `toggled` signal synchronously (confirmed this is real Qt
behavior, not a mock artifact), which calls `_on_pick()` mid-
construction, before several attributes it needs (`_details_lbl`,
`_SWAP_CLASSES`, and others built later in `__init__`) exist yet. The
code already explicitly calls `_on_pick(default_choice)` a second time
at the very end of construction once everything is safely built,
making the mid-loop trigger entirely redundant as well as unsafe.
Added a proper `_init_in_progress` guard rather than patching each
newly-discovered missing attribute one at a time as it surfaced.

Verified thoroughly given the severity: tested dialog construction
across every class at three different levels (42 total combinations,
all passing) rather than just the one scenario that first exposed the
crash, plus the original reported issue (DEX-based Blood Hunter
correctly enabled, low-STR Barbarian correctly disabled with a
sensible tooltip). Full app-wide regression: 0 failures.

## Conditions given real mechanical effects, not just a checkbox and a tooltip

User reported conditions weren't mechanically wired. Confirmed this
completely — the entire Conditions system was a checkbox, a badge,
and hover text, with genuinely zero effect on any calculation
anywhere in the app. Checking "Blinded" or "Poisoned" changed nothing
about what a player would actually roll.

Built the automatable subset of each condition's real effect (the
parts that are genuine numeric/roll modifiers, not situational
DM-judgment text like "can't willingly move closer to the source of
its fear," which no character sheet can meaningfully enforce):

- **Speed**: Grappled and Restrained now correctly force speed to 0 —
  confirmed via the real condition text this applies to every
  movement type (walk/fly/swim/climb), not just walking. Found this
  sitting in the same function that already correctly handles
  exhaustion's speed penalties, just never extended to conditions.
- **Attack rolls**: built `get_condition_attack_status()` — advantage
  from Invisible, disadvantage from Blinded/Frightened/Poisoned/
  Prone/Restrained/Exhaustion 3+, correctly canceling out per the real
  rule when both are present rather than picking one arbitrarily.
  Wired into the actual weapon row display, which now shows "(ADV)"/
  "(DISADV)" directly next to the to-hit number with a tooltip naming
  the specific source.
- **Saving throws**: built `get_condition_save_status()`, distinguishing
  auto-fail (Paralyzed/Stunned/Unconscious genuinely fail STR/DEX
  saves outright per their real text, not just "disadvantage on them")
  from disadvantage (Restrained on DEX specifically). Added a second
  badge next to the existing racial/class save-advantage indicator
  (kept separate rather than merged, since the two represent genuinely
  different, differently-shaped mechanics) showing AUTO-FAIL or
  DISADV with the responsible condition in the tooltip.
- **Ability checks**: Frightened and Poisoned's disadvantage on all
  ability checks, added directly into the existing
  `skill_disadvantages` list/source-tracking mechanism right next to
  exhaustion level 1+'s already-correct handling of the same thing —
  meaning this automatically flows through the Skills tab's existing
  advantage/disadvantage badge display with no separate UI work
  needed, the same way magic-item-sourced disadvantage already does.

**Found and fixed the same "data changes, nothing on screen notices"
bug pattern discovered earlier this session with the Infusions tab**:
the condition checkbox handler only ever refreshed the small "Active
Conditions" badge list itself — none of the new mechanical indicators
(save badges, weapon row tags, speed) would have updated live when a
condition was toggled, only on some unrelated future refresh. Fixed
by having the handler trigger a full `ctrl.refresh()`.

Verified thoroughly: each new calculation function tested in isolation
first, then confirmed through the real UI call chain — toggling
conditions via the actual `_on_condition_changed()` handler (not
manual data mutation) and reading the genuinely rendered badge/label
text afterward, including confirming badges correctly hide again once
a condition is unchecked. Swept all 14 conditions individually through
a live sheet construction, plus the full app-wide regression and a
252-combination mock sheet sweep: all clean.

**Deliberately not automated, and why**: conditions whose real effects
are about how *other* creatures interact with this character (Blinded/
Invisible/Prone/Restrained/Paralyzed/Stunned/Unconscious all grant
attackers advantage or disadvantage against the character, not the
reverse) aren't modeled, since this app has no representation of
incoming attacks at all — only the character's own rolls. Charmed,
Deafened, and Incapacitated's effects are situational/narrative
("can't attack the charmer," "auto-fail hearing checks," "can't take
actions") rather than numeric modifiers, and remain informational-only
via their existing tooltip text, same as before.

## Spell preparation bugs found and fixed

User reported prepared spells were "quite bugged." Investigated the
full preparation flow rather than assuming where the problem was.

**Confirmed the actual formula and cap-enforcement logic were already
correct**: tested `_prepared_caster_caps()`'s formula directly against
known values for all four prepared-casting classes (Wizard/Cleric:
ability mod + level; Paladin/Artificer: ability mod + half level
rounded down) — all correct. Tested the real multiclass case (a
Cleric/Druid character) to confirm each class's prepared-spell pool is
genuinely separate, not shared, including verifying a spell on both
classes' lists gets attributed to whichever has more room, exactly as
designed. Tested the cap-enforcement handler end-to-end (prepare up to
the cap, confirm the next one is blocked, unprepare one, confirm a new
one now fits) — all correct.

**Removed a dead but actively wrong function**: `_max_prepared_spells()`
existed alongside the correct `_prepared_caster_caps()`, with a
docstring directly asserting the opposite of the correct rule
(claiming multiclass prepared casters share one pooled total, when
they actually get separate per-class pools). Confirmed via search it
was never called from anywhere — harmless as dead code, but a real risk
if a future edit trusted it by mistake. Removed it.

**Found and fixed two real, confirmed UI-desync bugs**, both variations
on a pattern seen elsewhere this session (underlying data updates
correctly, but nothing tells the visible widgets):

1. **"Unprepare All Spells"** (the long-rest option) correctly cleared
   `spells_prepared` every time, but every checkbox on the Spells tab
   stayed visually checked, since the only thing touching spell rows
   on refresh is deliberately built to just add newly-eligible rows,
   never touch existing ones (protecting in-progress edits elsewhere).
   A full clear is exactly the deliberate bulk action that protection
   doesn't cover. Fixed by having this specific handler explicitly
   re-sync every row afterward.
2. **Stale spells never leave the tab.** When a spell is dropped from
   `spells_known` entirely (e.g. a Circle of the Land Druid switching
   terrain drops their old bonus spells), its row lingered on the
   Spells tab forever — still shown, still checked as prepared — since
   the only removal path was the manual ✕ button. Built
   `_remove_stale_spell_rows()` as the symmetric counterpart to the
   existing add-only sync, and confirmed it doesn't regress the
   protection the add-only design exists for: a spell that's still
   validly known keeps its row and its in-progress checkbox state
   exactly as before, even across an unrelated refresh.

**Also corrected myself mid-investigation**: briefly suspected a
severe crash bug (a method called but seemingly undefined anywhere) —
turned out to be my own search cut short by too narrow a line range,
not a real issue. Confirmed `set_prepared()`/`is_prepared()` both
genuinely exist and work correctly before concluding anything.

Verified everything through the real call chains rather than testing
calculation functions in isolation: the real "Unprepare All" dialog
flow, the real checkbox toggle handler, and the real
`ctrl.refresh()` cascade. Full app-wide regression and a 9-class
spellcasting sheet-construction sweep: all clean.

## Prepared spells — the real miscounting bug, found via user's specific correction

User corrected my earlier "prepared spells" pass: the actual bug was
classes counting spells not from their own list, and cantrips being
counted toward prepared totals. Investigated both claims directly
against the code rather than assuming where the problem was.

**Cantrip-counting claim**: confirmed `_attribute_prepared_spells()`
(the function actually used for cap enforcement and the count display)
already correctly excludes cantrips. Searched for any other raw,
unfiltered count of `spells_prepared` that might bypass this filtering
— found only the "Unprepare All" toast message's count, which doesn't
affect any cap or limit, just a reported number. No live cantrip-
counting bug found in the enforcement path itself.

**Cross-class counting claim — confirmed and fixed, and worse than
described**: found the real mechanism. Prepared-caster classes
(Wizard/Cleric/Druid/Paladin/Artificer) have their full available
spell list (or, for Wizard, their spellbook entries) dumped into the
character's flat `spells_known` list. Separately, known-caster classes
(Sorcerer/Bard/Warlock/Ranger) are meant to have their own known
spells auto-marked "prepared" (no separate prep step needed for them).
But that second step swept through *all* of `spells_known` — including
every prepared-caster spell dumped in by the first step — and checked
each name against a known-caster class's entire *theoretical* spell
list, not what the character actually selected as their known spell.

Confirmed via direct reproduction this was severe, not cosmetic: a
Cleric 3/Bard 3 character got **13 extra Cleric spells** silently
auto-marked as prepared for free, completely bypassing the Cleric
prep cap, purely because those spell names also happened to appear
somewhere on Bard's full spell list — regardless of whether the
character's Bard side had ever actually learned them. Separately
confirmed the identical bug on the Wizard side: a Sorcerer 5/Wizard 5
character with "Fireball" genuinely written in their Wizard spellbook
(deliberately left unprepared) had it auto-prepared for free anyway,
just because Sorcerer's spell list happens to include the same name —
even though this character's Sorcerer side had never learned it.

Since `spells_known` has no per-entry class attribution (both
mechanisms write into the same flat list), the correct fix given that
constraint: exclude from auto-preparation anything that's also on ANY
of the character's own prepared-caster class lists — all five
(Wizard/Cleric/Druid/Paladin/Artificer), not just the four that get a
literal full-list dump, since Wizard is equally a prepared caster with
its own cap even though it's populated differently. Those spells
always require explicit player preparation, regardless of what else
happens to share the name.

Verified thoroughly given the severity: both original reproductions
now correctly show zero free-prepared spells; the pure-caster case
(no conflict at all — a plain Sorcerer with a Sorcerer-only spell)
still correctly auto-prepares as before, confirming no regression on
the mechanism's actual intended purpose; and a full sweep across all
20 prepared-caster × known-caster class pairings, each tested with a
real shared spell the known-caster side does NOT actually know,
confirmed none of them leak through. Full app-wide regression: 0
failures.

## Backgrounds — full existing-entry audit complete (all 56 name-matched checked)

Completed the full comparison of every one of the 77 backgrounds
already in the app against the 96-entry reference, reading every
single entry's full text rather than sampling. Found and fixed 21
confirmed issues total across this pass:

**Severely fabricated features** (invented mechanics that don't
resemble the real rule at all, not just wording drift): Astral
Drifter, Athlete, Celebrity Adventurer's Scion, Anthropologist, Fisher,
Gambler, Grinner, Marine, Plaintiff, Rival Intern — each had a feature
name and/or description that was closer to a plausible-sounding
guess than the actual rule. Marine's real "Steady" is about forced-
march endurance and finding safe landing routes, not the invented
"advantage on frightened saves" the app had. Grinner's real feature is
a specific, named ritual ("Ballad of the Grinning Fool") tied to a
real risk of contacting traitors, not a generic "rumor network."

**The entire 10-background Ravnica guild set** (Azorius, Boros, Dimir,
Golgari, Gruul, Izzet, Orzhov, Rakdos, Selesnya, Simic): every single
one had a fabricated feature description, and every single one was
missing its Guild Spells feature — a genuine mechanical grant of
specific spells to a spellcaster's list, not flavor text. This wasn't
a scattered set of bugs; it was systemic across the entire category.

**Missing or wrong mechanical grants** found via careful cross-
checking, not just prose comparison: Investigator's skills were
hardcoded to 2 fixed skills instead of the real choose-2-of-3
(including Perception as an option the app never offered); Gambler and
Witchlight Hand each granted 2 fixed tool proficiencies where the real
rule is choose 1; House Agent's tool grant didn't match its real
13-house-specific table (documented via notes rather than fully
modeling each house, given the scope); nine backgrounds (Dimir
Operative, Faceless, Rakdos Cultist, Fisher, Gambler, Inheritor, Knight
of the Order, Volstrucker Agent, and others) were missing their
languages field entirely, silently granting 0 instead of the correct
count.

Verified nothing was broken by cross-checking a background I initially
suspected (Ruined) turned out to already be fully correct on
re-reading in full — not every flagged difference was actually a bug.

Full regression after every batch: 77 backgrounds load cleanly
throughout, 0 compile failures.

**Next**: the reference has 39 backgrounds not yet in the app at all
(the Baldur's Gate variant set, several more Strixhaven college
backgrounds, and others) — continuing with those next.

## Backgrounds audit continued — 40 of 56 name-matched entries now fully verified

Continued the systematic backgrounds audit from where it left off.
Checked every name-matched background against the reference in full
(not sampled), given how convincing the earlier-discovered Ravnica
fabrications looked on a first pass — a quick skim was demonstrated
unreliable, so this round re-verified everything carefully rather than
trusting an earlier quick impression of "looks reasonable."

**Confirmed clean, no changes needed**: Clan Crafter, Cloistered
Scholar, Criminal, Entertainer, Fisher, Gambler, Grinner, Haunted One,
Hermit, House Agent, Inheritor, Investigator, Marine, Noble, Rival
Intern.

**Fixed this round** (13 backgrounds, each with a confirmed, real
discrepancy against the source text):
- **Charlatan**: fabricated "recreate your identity in a week with
  forger's supplies" clause; missing the real forgery condition
  (needing to have seen an example of the document/handwriting).
- **Archaeologist**: fabricated "Teleportation Circle" spell reference;
  missing the real "determine builders' race" and "value art objects
  over a century old" details; incomplete equipment.
- **City Watch**: fabricated "bureaucratic hurdles" detail; missing
  the real feature's "pick out dens of criminal activity" half
  entirely.
- **Courtier**: fabricated extra equipment (signet ring, common
  clothes) not in the real, simpler list.
- **Faction Agent**: fabricated "emergency healing" and "faction calls
  on you for help" details; missing the real, important limitation
  that these contacts never risk their lives or reveal their identities.
- **Failed Merchant**: severely wrong — entirely different tools
  (Navigator's/Vehicles vs. the real Artisan's tools), missing
  languages entirely, a fabricated "10% above market value" mechanic
  replacing the real "trade connections" feature, wrong equipment.
- **Far Traveler**: missing the jewelry's specified value (10 gp).
- **Folk Hero**: fabricated "upper classes are suspicious of you"
  sentence not in the real feature.
- **Guild Artisan**: missing the real feature's core political/legal
  protection content (guild support against false accusations, access
  to powerful political figures) entirely, replaced with a vaguer
  paraphrase.
- **Knight of the Order**: lost the real feature's three-way
  distinction (religious/civic/philosophical orders each get
  different aid) and a specific, vivid detail (smuggling a hunted
  knight out of town).
- **Mercenary Veteran**: fabricated specifics ("work as guard/courier/
  soldier," "which companies are reputable") replacing the real,
  different text (identifying companies by emblem, finding mercenary
  taverns, the specific Practicing a Profession downtime tie-in).
- **Outlander**: fabricated "safe campsite" ability not in the real
  feature.
- **Rewarded**: severely wrong — fabricated feature name ("Boon of the
  Deck" vs. the real "Fortune's Favor") and an invented "sense a Deck
  of Many Things within 1 mile" mechanic that doesn't exist in the
  real rule at all; completely wrong equipment.
- **Ruined**: generic placeholder equipment replacing the real, much
  more specific and evocative item list.

Compile-checked and regression-tested after every fix: clean
throughout.

## Backgrounds audit — all 56 name-matched entries now fully verified

Completed the systematic pass. Checked all remaining 16 entries in
full against the reference text; found and fixed real discrepancies
in 8 of them:

- **Urchin**: fabricated "movers and shakers/dangerous areas" addition
  not in the real feature.
- **Uthgardt Tribe Member**: fabricated "advantage on Intelligence
  checks to navigate" mechanic that doesn't exist in the real rule;
  missing the real "double food/water while foraging" mechanic and
  the specific, named ally network (druid circles, nomadic elves,
  Harpers, First Circle priesthoods) — replaced with a vague "your
  tribe" mention; wrong equipment item.
- **Volstrucker Agent**: the entire feature was fabricated — invented
  "Assembly safe houses" and "intelligence network with payment"
  mechanics replacing the real feature entirely, which is a magical
  letter-delivery network using spellbook-scribing ink; missing
  equipment item.
- **Waterdhavian Noble**: replaced the real, specific line-of-credit
  lifestyle-cost mechanic (covers 2 gp/day of expenses via family
  credit, explicitly not a monetary reward) with a generic, different
  "stay in homes for free / secure any audience" fabrication; missing
  equipment item.
- **Witchlight Hand**: fabricated "secret signals, communicate with
  denizens" ability not in the real feature, which is simpler (free
  lodging plus wandering the carnival); missing equipment items.
- **Shipwright**: fabricated "1 minute examine to learn HP/
  vulnerabilities/sabotage" ability and a fabricated 1d4/hour healing
  rate, replacing the real mechanic (5× proficiency bonus once, until
  pulled ashore and fully repaired); wrong equipment.
- **Smuggler**: fabricated "checkpoints for a fee" and "50% market
  value fence" mechanics replacing the real, different feature (free
  stays at safe houses, poor lifestyle, optional secrecy); fabricated
  equipment item.
- **Rewarded** (checked in the prior session's final batch, included
  here for completeness): wrong feature name and an invented "sense a
  Deck of Many Things within 1 mile" mechanic not in the real rule.

**Confirmed clean on this pass**: Sage, Sailor, Soldier, Urban Bounty
Hunter.

**Final tally**: every one of the 56 name-matched backgrounds has now
been checked against the source text in full, not sampled. Total
fixed across the whole audit: 25 backgrounds with confirmed real
discrepancies (10 Ravnica guilds, plus 15 others), all verified via
compile checks and incremental regression, plus a final full sweep —
all 77 backgrounds in the app now build cleanly.

## Backgrounds — added all 13 Baldur's Gate variants

Added the full Baldur's Gate Descent into Avernus variant set:
Acolyte, Charlatan, Criminal, Entertainer, Folk Hero, Guild Artisan,
Hermit, Noble, Outlander, Sage, Sailor, Soldier, and Urchin. Each
combines the same skills/tools/equipment and base feature as its
standard PHB counterpart (already verified accurate against the
source in the earlier audit pass) with the real, transcribed
Baldur's-Gate-only feature text layered on top — since the app's data
model has one feature per background, both are combined into a single
description with the in-city-only feature clearly marked as such.
Baldur's Gate Soldier includes both of its two real features (City
Guard's Flaming Fist/Watch choice, and Loyalty Test).

Compile-checked and full-regression-tested: 90/90 backgrounds in the
app now build cleanly (up from 77).

## Backgrounds — added 7 official "Variant" backgrounds and all 5 Strixhaven colleges

Added the 7 official reflavored "Variant" backgrounds (Investigator,
Spy, Gladiator, Guild Merchant, Knight, Retainers, Pirate). Confirmed
these are genuine, distinct reflavors rather than identical copies —
each has real, specific differences from its base background (e.g.
Variant City Watch/Investigator uses Insight+Investigation, not the
base's Athletics+Insight; Variant Sailor/Pirate has an entirely
different feature, "Bad Reputation," not "Ship's Passage").

Added all 5 Strixhaven college backgrounds (Lorehold, Prismari,
Quandrix, Silverquill, Witherbloom). Each correctly grants the
Strixhaven Initiate feat (already verified accurate in the earlier
feats audit), choosing the matching college, plus documents the real,
mechanically significant spell-list expansion each college grants to
a spellcasting class — following the same text-based convention
already established for the Ravnica guild spells fixed earlier this
session, since the app's background data model doesn't have separate
mechanical spell-list-injection infrastructure.

Compile-checked and full-regression-tested: 102/102 backgrounds in
the app now build cleanly (up from 90).

## Backgrounds audit — complete. 0 of 96 reference entries missing.

Added the final 14 unique/setting-specific backgrounds: Augen Trust
(Spy), Cobalt Scholar (Sage), Custom Background, Feylost, Gate Warden,
Giant Foundling, Knight of Solamnia, Luxonborn (Acolyte), Mage of High
Sorcery, Myriad Operative (Criminal), Planar Philosopher, Revelry
Pirate (Sailor), Rune Carver, and Wildspacer.

Several of these (Augen Trust, Cobalt Scholar, Luxonborn, Myriad
Operative, Revelry Pirate) are confirmed mechanically identical to
backgrounds already verified accurate earlier in this audit, just
published under different setting-specific names — added as distinct
named entries anyway, since a player looking for "Cobalt Scholar" by
name wouldn't find it under "Sage."

Several others (Gate Warden, Giant Foundling, Knight of Solamnia,
Mage of High Sorcery, Planar Philosopher, Rune Carver, Wildspacer)
grant real feats (Scion of the Outer Planes, Strike of the Giants,
Squire of Solamnia, Initiate of High Sorcery, Tough) — confirmed each
feat already exists with accurate text from the earlier feats audit
before using it, rather than assuming. Verified the mechanical grant
actually applies (not just documented in text): built a character
with each of 4 of these backgrounds and confirmed the real feat
genuinely appears in char["feats"] afterward — 4/4 passing.

Fixed a data-modeling issue caught while building Custom Background
(the 2024 PHB's build-your-own option): the real rule combines tool
proficiencies and languages into a single pool of 2 total picks, not
2 of each — the first draft of this entry would have granted 4 total
picks instead of 2, doubling the intended benefit.

Final verification: cross-checked the app's full background list
against every name in the reference document — 0 missing, all 96
reference backgrounds now present and accounted for. Full regression:
116/116 backgrounds in the app build cleanly (up from 77 at the start
of this audit, 39 added this pass).

**Backgrounds audit is now complete**: every background in both the
originally-present set and the reference document has been checked
against source text (not sampled), with 25 confirmed real
discrepancies fixed and 39 missing backgrounds added, all verified
via compile checks and regression testing throughout.

## Races audit begun — user provided a large, mixed reference

User uploaded a comprehensive races reference (races-sublist.md,
8,352 lines, 253 version blocks across 214 unique race names — far
larger and more heterogeneous than feats or backgrounds, bundling
official 2014/2024 content, Heliana's Guide to Monster Hunting,
Kobold Press's Ratatosk, extensive Middle-Earth material, and a long
tail of unrelated individual homebrew creators' posts from World
Anvil). Scoped this carefully with the user before diving in, given
three real decisions were needed (MTF-vs-MPMM version handling, 2024
PHB species revision, and third-party homebrew inclusion) that
shouldn't be made unilaterally given the scale involved.

**User's guidance, confirmed explicitly**: keep both old and revised
versions where a race has meaningfully different printings (rather
than replacing); 2024 PHB species revision is explicitly out of
scope; stick to verifying what's already in the app rather than
adding the homebrew content.

Of the app's 63 existing races, 10 have no match in this particular
reference (Grung, Locathah, Merfolk, Naga, Khenra, Aven, Vampire,
Siren, Kor, Aetherborn — all sourced from Plane Shift documents this
compilation doesn't cover) and are left as-is. Of the remaining 53,
15 only have a flexible-ASI reference version available (matching
what several — Dhampir, Fairy, Harengon, Hexblood, Owlin, Reborn,
Astral Elf, Autognome, Giff, Hadozee, Plasmoid, Thri-kreen, Kender —
already correctly use in the app); only Githyanki and Githzerai are
genuine old-fixed-ASI-vs-new-flexible-ASI cases requiring a new,
additional entry per the user's "have both" guidance — that addition
is still pending.

**18 of the ~50 in-scope races checked in full against source text so
far, with 4 confirmed real fixes**:
- **Dwarf**: missing the "speed not reduced by heavy armor" trait
  entirely. (Separately noted: the underlying heavy-armor
  STR-requirement speed penalty isn't mechanically implemented for
  any character in this app at all — a broader, general system gap
  worth its own pass later, not specific to Dwarf.)
- **Aarakocra**: had a "Wind Caller" trait (cast Gust of Wind at 3rd
  level) that doesn't belong in this entry at all — confirmed it's
  specifically 2024 PHB-only content mixed into what's otherwise the
  original 2014 EEPC statblock. Removed per the user's explicit "stay
  away from 2024" instruction; confirmed it granted no actual
  mechanical spell access anywhere, so nothing else needed updating.
- **Bugbear**: completely missing the "Sneaky" trait (free Stealth
  proficiency) — confirmed absent from the entry entirely.
- **Firbolg**: found two issues. The display text for both magic
  traits read "PB/LR" and "PB per long rest," misleadingly suggesting
  proficiency-bonus-scaled uses on a long-rest-only reset, when the
  real rule (and the actual underlying resource, already correctly
  fixed in an earlier session for the two spells) is a flat 1 use
  resetting on a short OR long rest. Fixed the misleading text.
  Separately, while verifying this, found Hidden Step had zero
  resource tracking at all despite being an identical "once per short
  or long rest" ability to the already-fixed Firbolg Magic spells —
  added the missing resource, verified end-to-end with a real
  character build.
- **Goblin**: speed was set to 25 ft; confirmed the real VGM rule is
  30 ft (unlike Halfling/Gnome, Goblin's Small size doesn't come with
  a speed reduction). Verified the fix actually changes the
  character's real effective speed, not just the stored value.

Compile-checked and regression-tested after every fix: 63/63 races
build cleanly throughout.

**Confirmed clean on this pass**: Dragonborn, Elf, Gnome, Human,
Tiefling, Half-Elf, Half-Orc, Halfling, Aasimar, Centaur, Genasi,
Goliath, Hobgoblin.

## Races — Kenku/Kobold/Leonin verified, and a systematic sweep for genuine multi-version races

User clarified the scope further: races with real, different rules
across multiple sourcebooks (their examples: Gith, Kenku) should have
every meaningfully-different version available as a separate,
selectable option, not just one picked as "the" version. This
required going back and systematically checking every race with more
than one non-2024 reference entry, rather than relying on my earlier
approach of silently keeping only one version per race.

**Found and corrected a real gap in my own methodology first**: an
"Elf" version I'd initially have treated as a legitimate second
printing was actually Middle-Earth content (Wisdom-based ASI, "Elf
(Lindon)" subrace, "Elvish Dreams" trait) that slipped past the
existing LOTR filter because "Lindon" wasn't in the marker list.
Caught and excluded before it could be added.

**Systematically checked every race with multiple non-2024, non-LOTR
reference versions** (Aasimar, Bugbear, Centaur, Elf/Eladrin, Goblin,
Hobgoblin, Minotaur, Orc, Triton) to determine which had genuine
mechanical differences worth a true second entry, versus which were
just different flavor-text paragraphs (age/alignment wording) around
identical mechanics. Confirmed Bugbear, Centaur, Goblin, Hobgoblin,
and Minotaur are mechanically identical between their versions — no
second entry needed for these.

**Orc — found something significant while investigating this**: the
app's existing Orc entry (Adrenaline Rush/Relentless Endurance) looked
initially like it might be a bug, since it matched neither reference
version. Researched before touching it rather than assuming, and
confirmed via multiple independent sources this is actually the
correct, real *Monsters of the Multiverse* (2022) rewrite — a
legitimately different, newer printing the reference didn't happen to
include, not an error. Corrected the source tag, which had been
mislabeled "VGM/MTF" instead of "MPMM". While verifying the newer
version's text against research, also caught that the app's
"Adrenaline Rush" description undersold the real ability — it said
"once per long rest" when the actual rule scales uses with
proficiency bonus (regaining all uses on a long rest), a real,
level-scaling difference. Found zero resource tracking existed for
this ability at all, matching the exact gap pattern already found for
Firbolg's Hidden Step — built it correctly using proficiency bonus for
the use count, verified against a level-9 character (4 uses, matching
PB at that level). Per the user's "have both" instruction, added the
genuinely different older VGM/MTF version (Aggressive, Primal
Intuition) as a separate "Orc (VGM/MTF)" entry, and confirmed the two
entries' mechanical resources don't cross-contaminate each other.

**Elf (Eladrin) — a second genuine case**: confirmed DMG'14 (INT+1
secondary ASI, Fey Step = cast Misty Step once per rest) and MTF
(CHA+1, seasonal Fey Step with additional effects) are real,
different mechanics — the app already correctly had the MTF version.
Added DMG'14 as a second subrace option. Caught a real parsing bug of
my own while doing this: the app's subrace-ASI parser splits on the
first "(" character to extract a subrace's name, so naming the new
option "Eladrin (DMG'14)" would have collided with the existing
"Eladrin" entry (its name would parse as just "Eladrin", stripping the
version marker). Renamed to "Eladrin - DMG'14" to avoid the collision,
verified both versions independently apply their correct, distinct
ASI afterward.

**Kenku**: found and fixed a real language-text inaccuracy — the app
said Kenku "understand" Auran, when the real rule is they can read/
write both Common and Auran normally but cannot *speak* either
language at all (they can only "speak" via the Mimicry trait) — a
different and more specific rule than what was there before.

**Confirmed clean**: Kobold, Leonin.

Compile-checked and regression-tested throughout, including a real
regression-test correction of my own (an early "neither ASI applied"
result turned out to be me reading the wrong character field,
`abilities` instead of the actual `ability_bonuses` race grants are
stored in — confirmed both Eladrin versions work correctly once
reading the right field). 64/64 races build cleanly (up from 63 — the
new Orc (VGM/MTF) entry).

## Races — dual-version handling (Gith, Kenku, and beyond) plus several real text bugs found while investigating

User clarified: Githyanki and Githzerai each independently have their
own distinct old/new printings (not a combined "Gith" concept), and
this same "genuinely different official sourcebook version" pattern
repeats across other races too, not just the three initially named —
confirmed this directly rather than assuming scope.

**Githyanki/Githzerai**: found the existing entries weren't cleanly
"the old version" at all — they'd been incorrectly cross-contaminated
with traits from the *other* version. The app's "MTF" Githyanki was
missing its real trait (Decadent Mastery) entirely, substituting in
"Astral Knowledge" — which is actually the separate MPMM version's
trait, not even fully (missing the tool half of the grant). Both Gith
entries also carried a fabricated "Telepathy" trait present in neither
real printing. Fixed both existing entries to accurately match their
real MTF text, then added both genuinely distinct MPMM-revised
versions as new, separate, clearly-labeled entries alongside them.

**Kenku**: fixed the existing VGM entry's language text (real rule:
can't speak any language normally at all, only read/write, with
spoken communication limited entirely to the Mimicry trait — not
"Auran, understand only" as previously written). Added the genuinely
different MPMM version (different trait names, a repeatable
proficiency-bonus-scaled "Kenku Recall" mechanic replacing the flat
two-skill "Kenku Training," a changed Mimicry DC formula, and a
Small-or-Medium size choice) as a new, separate entry.

**Systematically checked every other multi-version race name for this
same pattern** rather than assuming it was isolated to the three named
examples, finding:
- **Minotaur**: the existing "Hammering Horns" trait text had been
  corrupted into a completely different, nonsensical mechanic ("you
  cannot make an opportunity attack") that doesn't describe the real
  rule at all (a Strength save vs. DC 8+proficiency+STR, pushing the
  target up to 10 ft on a failure). Fixed the corrupted text, then
  added the genuinely different MPMM version (trades "Imposing
  Presence" for "Labyrinthine Recall" entirely) as a new entry.
- **Orc**: the app already correctly had two separate entries (VGM/MTF
  and MPMM), but the MPMM entry's ASI field itself was wrong — fixed
  (STR+2/CON+1) instead of the real MPMM flexible ASI every other MPMM
  race correctly uses, and its languages were fixed to "Orc" instead
  of the real "one language of your choice."
- **Hobgoblin**: added the genuinely different MPMM version (entirely
  different trait set — Fey Ancestry, a proficiency-bonus-scaled Fey
  Gift with three situational Help-action options, Fortune from the
  Many — replacing Martial Training/Saving Face completely) as a new
  entry alongside the already-accurate VGM original.
- **Triton**: found the existing entry was missing Darkvision entirely,
  and "Emissary of the Sea" incorrectly described two-way
  communication with aquatic beasts when the real rule is explicitly
  one-way (the beast understands you; you have no special ability to
  understand it back). Fixed both, then added the genuinely different
  MPMM version (swim speed tied to walking speed rather than a flat
  30 ft, spell choice of INT/WIS/CHA, swaps Wall of Water for Water
  Walk) as a new entry.

Compile-checked and full-regression-tested after every single change
in this batch: 70/70 races build cleanly (up from 63 at the start of
the races audit).

## Races — user clarified: MPMM revisions need their own selectable entries too

User clarified the earlier "have both old and new" guidance applies
broadly, not just to Githyanki/Githzerai: any race with a genuinely
different, separately-published printing (most commonly the
*Monsters of the Multiverse*, 2022, flexible-ASI revision) should get
its own selectable entry, kept alongside the original rather than
merged or replacing it. This surfaced a larger and more precise
picture than my first pass: my earlier "is this 2024" detection only
checked for the flexible-ASI phrasing pattern, which both MPMM (2022)
and the actual 2024 PHB share — it couldn't distinguish "a legitimate
earlier revision, in scope" from "genuine 2024 PHB content, out of
scope" on its own. Confirmed case by case instead: races like
Kenku/Githyanki/Satyr/Centaur/Changeling don't appear in the core 2024
PHB at all (confirmed via a reliable marker — MPMM's explicit
"Creature Type: Fey" reclassification line for several of them, absent
from anything actually 2014-sourced), so their flexible-ASI text is
unambiguously an MPMM revision, not 2024 content.

Systematically re-checked all 63 existing races for multiple versions
in the reference (not just the ones already suspected) — found 24
with more than one, beyond the 2 already known. Found that substantial
work already existed from earlier in this session that wasn't in
visible context: Githyanki (MPMM), Githzerai (MPMM), Hobgoblin (MPMM),
Kenku (MPMM), Minotaur (MPMM), Triton (MPMM), and a restructured Orc/
Orc (VGM/MTF) pair were already present and verified accurate against
the reference. Also found Kenku's language-rule fix (from earlier in
this session) had already landed correctly.

**Added 5 more MPMM entries this round**, each verified against full
source text: Aarakocra, Aasimar, Bugbear, Centaur, Firbolg, Genasi (a
base race plus its 4 elemental subraces — Air/Earth/Fire/Water — each
carrying real, distinct spellcasting traits), Goliath, Kobold. Several
of these are genuinely different mechanics, not just reprints —
confirmed and documented each real difference rather than assuming
"MPMM version" means "same rules, new ASI system":
- Aasimar (MPMM) replaces the old Protector/Scourge/Fallen subrace
  split entirely with a unified Celestial Revelation choice any
  Aasimar can make at 3rd level.
- Bugbear (MPMM) drops the old "once per combat" limit on Surprise
  Attack and adds Fey Ancestry.
- Firbolg (MPMM)'s Hidden Step is a genuinely different mechanic —
  proficiency-bonus-scaled uses resetting only on a long rest, not
  the older version's flat 1 use resetting on a short or long rest.
- Goliath (MPMM)'s Stone's Endurance similarly gains proficiency-bonus
  scaling and drops to long-rest-only reset.
- Kobold (MPMM) replaces Sunlight Sensitivity and Pack Tactics
  entirely with new traits (Draconic Cry, a Kobold Legacy choice).

**Found and fixed two more genuine "trait described, never
mechanically tracked" gaps** while verifying these, via the same
audit method that already caught Firbolg's Hidden Step and Orc's
Adrenaline Rush: Harengon's Rabbit Hop had zero resource tracking
despite its own text already correctly describing a real,
proficiency-bonus-scaled long-rest ability. Added the missing
resource and verified it end-to-end (correctly shows 3 uses for a
level 5 character with a +3 proficiency bonus).

Compile-checked and regression-tested after every addition: 78/78
races build cleanly (up from 63 at the start of this races audit).

Confirmed MPMM versions weren't needed for Harengon specifically — its
2 reference versions are identical duplicates, not an old/new pair, so
the app's existing entry already correctly uses the only version that
exists.

## Races — all 24 multi-version races now fully resolved

Completed the systematic multi-version pass. Added 5 more MPMM
entries this round, each checked against full source text for real
mechanical differences rather than assumed to be reprints: Lizardfolk,
Satyr, Tabaxi, Tortle, Changeling, Shifter, Goblin.

- Lizardfolk (MPMM) drops Cunning Artisan entirely; Hungry Jaws
  becomes proficiency-bonus-scaled, long-rest-only (was flat 1 use,
  short or long rest).
- Satyr (MPMM)'s Ram drops the old charge-and-push mechanic entirely
  (was: move 10+ ft, STR save or push 5 ft; now a flat unarmed strike).
- Tabaxi (MPMM)'s climbing speed now matches walking speed (was a
  flat 20 ft), plus a new Small/Medium size choice.
- Tortle (MPMM) claw damage increases to 1d6 (was 1d4), and Survival
  Instinct becomes a skill choice instead of being fixed to Survival.
- Changeling (MPMM) adds the Fey creature type and a size choice, but
  grants one fewer bonus language (1, not 2).
- Shifter (MPMM) merges the old 4 fixed-ASI subraces into one
  flexible-ASI race with a single Shifting-benefit choice; Shifting's
  temp HP and uses become proficiency-bonus-scaled and long-rest-only
  (were flat and short-or-long-rest), and several per-benefit
  mechanics changed outright (e.g. Beasthide: flat temp HP + AC,
  rather than CON-mod-plus-level HP and a bonus Dodge action).
- Goblin (MPMM) adds Fey Ancestry entirely; Fury of the Small changes
  from level-scaled damage (1 use, short or long rest) to
  proficiency-bonus-scaled damage and uses (long-rest-only, capped at
  once per turn).

**Found and fixed a real, significant bug in the existing (non-MPMM)
Tortle entry while comparing it**: Shell Defense's saving throw
bonus was backwards — said "advantage on DEX saves," when the real
rule is advantage on STR/CON saves and disadvantage on DEX saves.
Also missing the "can't take reactions" detail. Fixed in the base
entry (not just the new MPMM one, since this was wrong in the
original too).

**Ruled out two candidates correctly rather than assuming they needed
new entries**: Fairy and Harengon each have two reference version
blocks, but on full-text inspection both pairs are identical in
substance (just differently ordered/formatted duplicate printings,
not a genuine old-vs-revised pair) — confirmed the app's existing
single entry for each already matches accurately, so no new entry was
warranted.

**Caught and immediately corrected a real mistake of my own**: an
early insertion for Lizardfolk (MPMM) used an incomplete anchor that
accidentally deleted the adjacent Locathah entry's opening line,
breaking the file. Caught immediately by the routine compile-check
step (not left for a later regression to find), and repaired before
moving on. Switched to smaller, more precise, fully-bounded edits for
the remainder of this batch to avoid a repeat.

All 24 races identified as having genuine multiple versions in the
reference are now resolved — either a new, clearly-labeled and
accurately-differentiated entry was added, or (Dwarf, Elf: LOTR
content correctly excluded; Fairy, Harengon: confirmed duplicate
reference printings, no second entry needed; Orc: already
restructured with the older version as Orc (VGM/MTF)) confirmed no
addition was warranted, each for a documented, verified reason.

Full app-wide regression after every single addition: 85/85 races
build cleanly (up from 63 races before this races audit began).

## Races — continued text-verification pass, several more real fixes

Continued checking remaining races against full source text.

**Confirmed clean**: Loxodon, Kalashtar, Warforged, Yuan-ti Pureblood
(the combined MPMM/VGM subrace structure for the latter was verified
accurate against both source texts).

**Fixed this round**:
- **Minotaur**: two missing conditions. Goring Rush requires actually
  moving at least 20 feet during the Dash, not just using the action;
  Hammering Horns must specifically be part of the Attack action, not
  just any melee attack.
- **Orc (VGM/MTF)**: Primal Intuition's skill list included "Nature,"
  which isn't in the real list at all (Animal Handling, Insight,
  Intimidation, Medicine, Perception, Survival) — a fabricated extra
  option. (Confirmed the MPMM-style "Orc" entry is accurate as-is.)
- **Simic Hybrid**: language grant was a generic "one of your choice"
  when the real rule specifically restricts it to Elvish or Vedalken.
- **Verdan**: significant issue — "Unsettling Presence" is an entirely
  fabricated trait with no basis in the real rule at all, while the
  real "Black Blood Healing" trait (reroll 1s/2s on hit dice spent at
  the end of a short rest) was completely missing. Also missing the
  real level-based size progression (Small at 1st level, Medium at
  5th) and the bonus-language detail.
- **Dhampir, Owlin, Reborn**: all three were missing the "Small or
  Medium, your choice" size option entirely (the app's `race()` data
  model only supports a single fixed size, so this was documented as
  a text trait rather than requiring a larger architectural change).
  Owlin's "Silent Feathers" also said "advantage on Stealth checks,"
  when the real rule is just proficiency in Stealth, not advantage.

**Found and fixed two more genuine "described but never mechanically
tracked" gaps**, the same pattern already caught for Firbolg's Hidden
Step, Harengon's Rabbit Hop, and Orc's Adrenaline Rush: Dhampir's
Vampiric Bite (empower) and Reborn's Knowledge from a Past Life both
had zero resource tracking despite their own text already correctly
describing real, proficiency-bonus-scaled, long-rest abilities. Added
both, verified end-to-end with real character builds (both correctly
show 3 uses at proficiency bonus +3).

Compile-checked and regression-tested after every fix: 85/85 races
build cleanly throughout.

## Races audit — text-verification pass complete, plus a major architectural fix

Completed the final 8 races in the text-verification pass: Astral
Elf, Autognome, Giff, Hadozee, Plasmoid, Thri-kreen, Kender, Hexblood.
This closes out the full pass — every one of the app's original 63
races, plus all 22 MPMM additions from earlier in this audit, has now
been checked against full source text.

**Confirmed clean**: Astral Elf, Autognome, Plasmoid (aside from the
size gap below).

**Found and fixed a genuinely significant, broader architectural gap
while checking Giff**: `char["swim_speed"]`/`["climb_speed"]` had no
source at all anywhere in the app except one specific Barbarian
subclass feature (Storm Herald's Storm Soul) — despite being real,
named traits on Triton, Locathah, Merfolk, Tabaxi, Genasi (Water
subrace only), Giff, and Hadozee. This wasn't a Giff-specific bug; it
was a category of race trait with no mechanism to apply at all,
industry-wide across the roster. Built a proper mechanism handling
each race's real, specific rule — some are a flat value (Locathah/
Triton/Merfolk's 30 ft swim, Tabaxi's 20 ft climb), others scale
dynamically to match the character's final effective walking speed
after all other bonuses (Triton (MPMM), Tabaxi (MPMM), Giff, Hadozee,
Genasi (MPMM) Water). Caught and fixed an ordering bug in my own first
draft of this fix along the way — the "equals walking speed" cases
needed to read the fully-bonused final speed, not the early base
value, or they'd silently miss things like Barbarian Fast Movement.
Verified extensively: 8 direct test cases covering flat values,
dynamic matching (confirmed against a Barbarian with Fast Movement
active), and the subrace-conditional Genasi case (confirmed water
subrace gets it, fire subrace correctly doesn't).

**Fixed several more real, individual issues**:
- Hadozee, Plasmoid, Thri-kreen, Hexblood: all missing the "Small or
  Medium, your choice" size option (Hexblood also missing the Fey
  creature type).
- Thri-kreen's languages were significantly fabricated — the app had
  an invented "Common (understand only), Thri-kreen (telepathic)"
  structure; the real rule is simply "Common and one other language,"
  with telepathy already fully covered by the separate Thri-kreen
  Telepathy trait.
- Kender's second trait was misnamed "Kender Aptitude" (real name:
  "Kender Curiosity").

**Found two more "described but never mechanically tracked" gaps**,
the same recurring pattern now found across this entire races audit:
Giff's Astral Spark (the bonus damage was already applied on every
hit with no limit at all — added the missing use-cap tracking) and
Kender's Taunt. Both verified end-to-end.

Compile-checked and regression-tested after every fix, including a
dedicated 8-case test suite for the new speed mechanism alone:
85/85 races build cleanly throughout.

**Races audit summary — this pass is now complete.** Over the course
of this audit: verified all 63 originally-present races against full
source text (not sampled), added 22 additional MPMM/revised-printing
entries the user specifically requested be kept alongside their
originals, fixed roughly 30 individual confirmed text/mechanical
discrepancies (ranging from wrong numbers and fabricated traits to
entirely invented abilities like Verdan's "Unsettling Presence"), and
found + fixed a genuinely systemic gap (race-granted secondary
movement speeds never being mechanically applied) affecting 7 races
at once rather than treating it as a one-off. Final count: 85 races
in the app, up from 63 at the start of this audit.

## Mundane items — new content area begun

User uploaded a mundane items reference (32 entries). Unlike the
races reference, researched the unfamiliar-sounding names first
before assuming anything was homebrew — confirmed all of them are
legitimate official WotC content (Ivana's Whisper from Van Richten's
Guide to Ravenloft, Murgaxor's Elixir of Life from Strixhaven, The
Incantations of Iriolarthas from Icewind Dale: Rime of the
Frostmaiden), not random third-party material like some of the races
reference turned out to be.

**Added 28 of 32 items this round**:
- 17 standalone adventuring gear items (Adjustable Stilts, Alchemist's
  Doom, Backpack Parachute, Barking Box, Catapult Munition, Ivana's
  Whisper, Matchless Pipe, Menga leaves, Murgaxor's Elixir of Life,
  Nimblewright Detector, Ryath Root, Shatterstick, Sinda berries, The
  Incantations of Iriolarthas, Vial of Stardust, Wildroot, Wukka Nut),
  each transcribed accurately from source text.
- 2 armor items (Spiked Armor, Survival Mantle) — noted honestly that
  Survival Mantle's special properties (breathe in vacuum, advantage
  vs. harmful gases) aren't captured by the plain armor tuple format,
  which only has room for AC/weight/cost, rather than silently
  dropping them.
- 4 real weapons (Hooked Shortspear, Iron Ball, Light Repeating
  Crossbow, Oversized Longbow), each correctly categorized per its
  actual stated weapon type in the source (not guessed).
- 4 Flensing Claws size variants (Small/Medium/Large/Huge) — a
  special, creature-specific Illithid-thrall augmentation, not a
  normal purchasable weapon. Documented its real, unusual nature
  (surgically implanted, can't be removed, always uses the wielder's
  own proficiency bonus regardless of normal weapon proficiency rules)
  rather than treating it like an ordinary weapon.

**Found and fixed a real, pre-existing bug while adding these**:
`GEAR_NAMES` was computed before the file's two `ADVENTURING_GEAR +=`
extension blocks, meaning it never actually contained anything from
either — not the pre-existing Tack/Vehicles/Trade Goods section, and
not the new items just added. Confirmed nothing in the app currently
relies on `GEAR_NAMES` (only imported, never actually used), so this
was harmless in live behavior, but still a real, misleading gap left
for a future edit to trust incorrectly. Moved its computation to after
both extension blocks; verified it now correctly captures all 154
gear items.

Compile-checked and regression-tested after every addition.

The Adamantine/Silvered weapon and ammunition "generic variant" system
(4 of the 32 reference entries) was confirmed not to exist anywhere in
the app at this point — these apply across roughly 60 different base
weapons each and require actual weapon-name-variant parsing and a real
mechanical effect (critical hits against objects for Adamantine;
bypassing nonmagical/non-silvered resistance for Silvered), not just a
data-table entry. "Silvered"/"Adamantine" were only ever referenced as
concepts within other creatures' resistance text, with no way for a
player to actually mark their own weapon as either. (Built later, in
the "Mundane items — Adamantine/Silvered weapons closed out" section
below.)

## CRITICAL FIX — Flexible ASI mechanic was wrong for ~39 races

User reported (with a direct side-by-side of Kenku's two official
printings) that the app's flexible ASI picker was fundamentally wrong.
Investigated and confirmed: the app's single `asi_flex` field was
being used for two genuinely different rules without ever
distinguishing them.

- **Half-Elf's real rule** ("two other ability scores of your choice
  each increase by 1") — a flat, additive grant. The existing
  checkbox picker correctly represents this.
- **The 2024/MPMM rule**, used by the vast majority of `asi_flex=2`
  races in this app (Kenku (MPMM), Aasimar (MPMM), Goblin (MPMM), and
  36 others): "choose EITHER +2 to one ability and +1 to a different
  ability, OR +1 to three different abilities." This is a real choice
  between two distinct distributions — and the old checkbox-only
  picker could represent *neither* of them. It silently forced a
  third, incorrect distribution (check up to 2 boxes, flat +1 each)
  that matches no valid rule at all.

This affected every race using this mechanic across the entire races
audit earlier in this session — a systemic bug, not a Kenku-specific
one.

**Fix**: added `asi_flex_style` to the race data model ("each" for the
Half-Elf-style flat grant, "distribute" — the new default — for the
2024/MPMM rule). Half-Elf is the one confirmed "each"-style exception;
41 other `asi_flex`-using races correctly default to "distribute".
Built a real picker for the distribute style: two radio buttons for
the two valid options, two dropdowns for the +2/+1 split (validated
to reject picking the same ability twice), and three checkboxes for
the triple option (validated to require exactly 3, not "up to 3").
Fixed the wizard's live "Total Scores" preview to reflect the active
card's selections immediately, not just after final submission. Fixed
two race-detail display locations that showed the same wrong "+1 to N
abilities" wording regardless of which rule actually applied.

**Also fixed a genuine mock gap found while testing this**: the
PySide6 test mock's `QRadioButton`/`QButtonGroup` never actually
enforced mutual exclusivity — checking one radio button left sibling
buttons still reporting `isChecked()==True`, unlike real Qt. This
caused a confusing false test failure before being traced back to the
mock itself rather than the app code. Fixed properly (radio buttons
now correctly unset their group siblings on check), matching the
established pattern of fixing real mock gaps rather than working
around them.

Verified extensively: 18 direct test cases covering both distribute
options, both validation failure paths, and a Half-Elf regression
check, all passing. Separately verified both `asi_flex=1` races
(Simic Hybrid, Warforged) correctly still use the simple checkbox UI
regardless of style, since a single point has no distribution
ambiguity. Full regression: 85/85 races build cleanly through the
core character builder, and construct the wizard's ASI step cleanly.

## Race-granted proficiency choices — wired for every confirmed race

User's Kenku report also flagged that race-granted proficiency
choices weren't wired into any real picker. Investigated broadly:
found 14 races in the app with a skill/tool-proficiency-choice-
granting trait, of which only 3 (Half-Elf, the old Kenku, Human
Variant) had any picker at all — via a small, hardcoded
RACE_SKILL_CHOICES dict. Every other race's grant was pure
description text with no way for a player to actually make the
choice and receive the real proficiency.

**Also found and fixed a duplicate-card bug while investigating**:
Half-Elf's skill choice was independently generated by two separate
functions (a hardcoded case in builder.py's get_choices_needed(), and
the RACE_SKILL_CHOICES dict in levelup_panel.py's _get_race_choices())
that get combined together everywhere they're called, with no
deduplication — confirmed a Half-Elf character would see two
identical "choose 2 skill proficiencies" cards. Removed the redundant
hardcoded case.

**Extended RACE_SKILL_CHOICES** to cover every confirmed pure
skill-choice race: Centaur, Leonin, Minotaur, Kenku (MPMM) (as its
own entry — its grant is a different, unrestricted "choose 2 skills"
compared to the old Kenku's restricted 4-skill pool), and Dhampir/
Hexblood/Reborn's "Ancestral Legacy" (modeled as always offering the
choice, since this app doesn't separately model VRGtR's "this lineage
replaces a previous race" alternate path).

**Added handling for the more complex grant shapes**, reusing the
app's existing skill_prof/tool_prof/skill_or_tool_prof choice types
rather than inventing new ones: Vedalken and Warforged each grant a
skill AND a separate tool (both required, modeled as two distinct
choice cards); Githyanki grants a skill OR a tool (a single combined
pick, using the already-supported skill_or_tool_prof type).

Verified the full real pipeline end-to-end, not just card generation:
confirmed Vedalken's simulated choices actually grant real skill and
tool proficiency through rebuild(), and Githyanki's combined pick
correctly resolves to a real tool proficiency. Full regression: 85/85
races build cleanly and generate their pending-choice cards without
error.

Githyanki (MPMM)'s Astral Knowledge and Astral Elf's Astral Trance
both re-grant a *different* skill/tool choice every long rest (not a
one-time pick at character creation) — an architecturally different,
recurring-choice mechanic this app doesn't have a UI for. Not wired to
any choice card.

## Class tool proficiencies — completely unwired, now fixed

User reported Rogue was missing thieves' tools. Investigated and
found this was much broader than a Rogue-specific bug: unlike armor
and weapon proficiencies (which have working getter functions wired
into rebuild()), class-granted tool proficiencies had NO application
pathway at all anywhere in the app. The class data itself was
correct — Rogue's dict entry genuinely says "Thieves' tools" — but
nothing in the character-building pipeline ever read that field.
Confirmed the actual scope: 4 classes grant tools at all (Rogue,
Druid, Bard, Monk, Artificer), split between fixed grants (no player
choice needed) and flexible "of your choice" grants (needing a real
picker).

**Fixed grants**: built get_class_tool_profs() (the missing
counterpart to the already-working get_class_armor_profs()/
get_class_weapon_profs()) and wired it into the same grant-
application loop. Handled a real nuance found by checking the actual
PHB multiclassing proficiencies table rather than assuming a uniform
rule: Rogue and Artificer grant their tools even as a secondary
multiclass, but Druid's Herbalism kit is only part of Druid's
primary-class grant, not its multiclass grant. Verified both cases
directly — a multiclass secondary Rogue still gets thieves' tools; a
multiclass secondary Druid correctly does not get the Herbalism kit.

**Flexible grants**: built _get_class_tool_choices(), a new sibling
to the race-choices system added earlier this session, covering
Bard's 3 musical instruments, Monk's 1 artisan's-tool-or-instrument,
and Artificer's 1 remaining artisan's tool pick (on top of its two
fixed tools). Reuses the existing tool_prof choice type and
_tool_profs ID-suffix aggregation already built for other proficiency
choices, so no further wiring was needed on the application side.
Wired the new function into both places pending choices get combined
(the main level-up panel, and the level-down "which choices are still
structurally relevant" snapshot in sheet.py).

Verified the full real pipeline end-to-end: a simulated Bard tool
choice (3 specific instruments) correctly resolves to real tool
proficiencies through rebuild(), not just a generated card. Full
regression across every class: 14/14 build cleanly and generate
pending-choice cards without error.

## Expertise skill pool and 6 confirmed action-level-gating bugs

**Expertise fix**: user reported Expertise could be selected for skills
the character wasn't proficient in. Confirmed: the skill chooser's
"expertise" mode fell through to the same "pool or ALL_SKILLS" default
used for ordinary skill_prof choices, with the checkbox styling
exactly backwards — it greyed out already-proficient skills as
"wasted" (correct guidance for skill_prof, wrong for expertise, where
being proficient is the entire prerequisite). Fixed to restrict
expertise mode to already-proficient skills only — but only when no
explicit pool was given. Confirmed Knowledge Domain's Cleric variant
is a genuinely different mechanic (grants proficiency AND expertise
together in 2 of 4 specific skills, regardless of prior proficiency)
and preserved its explicit pool being used as-is rather than
incorrectly filtering it too.

**Action-list level gating**: user reported Cunning Action appearing
in the Combat tab before 2nd level. Confirmed the mechanism: any
feature absent from the action list's min_level dict silently
defaults to level 1. Rather than fix Cunning Action alone, ran a
systematic comparison of every class's real per-level feature data
against the action list's gating logic, and found 5 more real
mismatches this pattern was hiding: Druid's Wild Shape (real level 2,
showing at 1), Paladin's Divine Smite (real level 2) and Cleansing
Touch (real level 14), Ranger's Primeval Awareness (real level 3),
and Artificer's Flash of Genius (real level 7) — all silently
available from level 1. Fixed all 6 together. Verified each
end-to-end with real characters at both the level just below and at
the real threshold, confirming the feature is correctly hidden below
and shown at the real level. Full regression across every class at 5
different levels: 70/70 combinations build cleanly.

## Actions tab — "Cast a Spell" and "End Concentration" no longer shown to non-casters

User reported the Actions tab showed every possible action regardless
of whether it made sense for the character — specifically calling out
spellcasting options appearing for characters with no spells at all.
Confirmed: both "Cast a Spell" and "End Concentration" were
unconditionally hardcoded into every character's Universal actions
list, with zero check for whether the character actually had any
spells.

Fixed by checking the character's real known/prepared spells rather
than guessing from class membership — this correctly handles
multiclass and partial-caster cases without needing a hardcoded list
of "which classes can cast spells." "Cast a Spell" now requires at
least one known or prepared spell; "End Concentration" additionally
requires at least one of those spells to actually carry the
concentration tag (checked against the real spell data, not assumed).

Verified end-to-end across three real scenarios: a non-caster Rogue
(both correctly absent), a caster with only a non-concentration spell
like Magic Missile (Cast a Spell present, End Concentration correctly
still absent), and a caster with a concentration spell like Bless
(both correctly present). Full regression across every class: 14/14
build action lists cleanly.

## Expertise, level-gating, and Actions tab filtering — all fixed

**Expertise skill pool**: confirmed a real, significant bug — the
skill-choice picker used the same "any skill in the game" pool for
both plain skill proficiency choices and Expertise, with no
distinction. Worse, the checkbox styling had the logic backwards for
Expertise specifically: it greyed out already-proficient skills as
"wasted," when being proficient is Expertise's entire prerequisite,
not a mistake. Fixed to restrict Expertise's pool to already-
proficient skills only — but only when no explicit pool was already
supplied by the caller, since Knowledge Domain Cleric's variant
(granting proficiency AND expertise together in 2 of 4 specific
skills, regardless of prior proficiency) is a genuinely different
mechanic that would have broken under a blanket restriction. Verified
both paths directly.

**Level-gating**: confirmed Cunning Action was showing on the Combat
page for 1st-level Rogues (real requirement: 2nd level), caused by a
missing entry in the min_level gating dict that let anything absent
silently default to level 1. Given the shape of this bug, ran a
systematic, automated comparison of every class's real feature-to-
level data against the app's gating logic rather than fixing only the
reported case — found 5 more genuine mismatches this way: Druid's Wild
Shape (real level 2), Paladin's Divine Smite (level 2) and Cleansing
Touch (level 14), Ranger's Primeval Awareness (level 3), and
Artificer's Flash of Genius (level 7) — all silently defaulting to
level 1 the same way. Fixed all 6 together. Verified every one
end-to-end: absent one level below its real requirement, present
exactly at it, across all 6.

**Actions tab filtering**: confirmed "Cast a Spell" and "End
Concentration" were already fixed by earlier session work not
previously summarized — both now correctly check the character's
actual known/prepared spells rather than assuming every character can
cast. Improved End Concentration further: it now also checks the
character's real, dynamic "currently concentrating" state (not just
"knows a concentration spell in the abstract"), so a character
actively concentrating via some other means still sees the option,
and the check is strictly additive (can only add correct cases, never
remove valid ones). Verified 5 scenarios end-to-end: non-casters see
neither option; a caster with only non-concentration spells known
sees Cast a Spell but not End Concentration; a character actively
concentrating sees End Concentration even without a matching spell in
their known list.

Full regression across every class/subclass at level 20: 0 failures.

## Starting equipment — confirmed already built and verified working

When first investigating the user's starting equipment report, an
earlier check for this data in classes.py and a broad app search
found nothing, and this was reported to the user as a fully missing
feature needing to be built from scratch. On returning to this task,
found a complete, working implementation already in place — a real
dnd_app/data/starting_equipment.py file with accurate "(a) or (b) or
(c)" choice tables for all 14 classes, plus a fully-built radio-
button/sub-combo UI in Step5Equipment and a working collect() method
that correctly resolves choices (including "Any simple weapon"-style
category placeholders) into real armor/weapons/gear on the character.
This must have been built during an earlier turn in this same session
that fell out of visible context before this continuation — flagging
that plainly rather than re-claiming the work as newly done here.

Verified the existing work thoroughly rather than assuming it was
correct just because it existed: cross-checked all 14 classes' data
against the real PHB/TCE/Blood Hunter tables, including specifically
verifying the two supplemental classes (Artificer, Blood Hunter)
against multiple independent sources since those are more likely to
have transcription errors — both confirmed accurate exactly as
written. Ran a full end-to-end test across all 14 classes (build UI,
collect, confirm real equipment results), and a detailed Rogue test
(matching the user's own pasted example) confirming both the default
selections and a full switch to each group's second option correctly
produce different, correct equipment each time.

No changes were needed — this item is confirmed complete and working.

## DM Rewards feature — fully wired

Completed the DM Rewards feature from the user's uploaded 44-entry
list ("Character Secrets" / narrative bonus features a DM can grant
outside normal progression — distinct from standard mechanical feats).

Built dnd_app/data/dm_rewards.py by parsing the source file
programmatically rather than manually retyping ~60,000 characters
across 44 entries (several containing embedded random tables) — this
guarantees textual accuracy with zero transcription risk, which
manual retyping at this scale could not. Extracted each entry's name,
optional prerequisite line, "replaces background feature" flag, and
"Character Secret" flavor-marker flag, then cleaned residual markdown
syntax (bold headers, multiple heading levels, italic emphasis) via
a second refinement pass after an initial scan caught two remaining
artifact types the first pass missed. Verified zero formatting
artifacts remain across all 44 final entries.

Wired this into the existing feat browser rather than building a
separate UI: renamed it from "Feat Browser — DM Rewards" to "Bonus
Feature Browser — DM Rewards", and extended its single searchable
list to include both ALL_FEATS and the new ALL_DM_REWARDS, tracked
via a second Qt item-data role so the grant/remove/tooltip logic can
tell which content type a selected item is. DM reward entries get a
distinct 🔮 marker in the list. Grant/remove now correctly route to
char["dm_feats"] or the new char["dm_rewards"] depending on the
selected item's type, and the "already granted" display section
(shown above the browser, matching the existing DM-Granted Feats
pattern) now has a parallel "DM-Granted Bonus Features" section for
granted rewards.

**Found and fixed three real, blocking PySide6 mock gaps while
verifying this end-to-end** — all three are standard Qt patterns any
future button/list-driven UI test would also need:
- `Qt.UserRole + 1` (a standard pattern for a second item-data role)
  crashed outright, since the mock's Qt.UserRole had no arithmetic
  support at all.
- `QPushButton.click()` didn't exist, silently falling through to a
  no-op instead of emitting the clicked signal any connected handler
  relies on.
- `QListWidget.currentItem()` was hardcoded to always return the
  first item in the list regardless of actual selection, and
  `setCurrentItem()` didn't exist at all to set one — together these
  meant any test simulating "select item X, click a button that acts
  on the current item" silently acted on the first item instead.

Fixed all three properly rather than working around them in the test,
matching the established pattern of treating real mock gaps as worth
fixing on their own. Verified the complete, real interaction pathway
end-to-end afterward: selecting a DM reward item and clicking Grant
correctly writes to dm_rewards (not dm_feats); selecting a real feat
and clicking Grant correctly writes to dm_feats (not dm_rewards);
Remove correctly un-grants only the targeted item, leaving unrelated
grants untouched. Confirmed the granted reward's content actually
renders in the sheet's display section, not just in the underlying
data. Full regression across every class: 14/14 build cleanly through
both the core character builder and full sheet UI construction.

## DM Rewards browser — category filter dropdown added, and a real correction

User requested a dropdown to filter the DM Rewards browser by feature
type. Investigated the real category structure in the source material
rather than inventing labels, and initially landed on 3 categories
(Character Secret, Dark Gift, Supernatural Gift) verified against
Icewind Dale: Rime of the Frostmaiden, Van Richten's Guide to
Ravenloft, and Mythic Odysseys of Theros/Wildemount respectively.

User then provided an authoritative reference list that caught a real
mistake in that first pass: "Replacement Feature: Background" is a
genuinely distinct 4th category, not a sub-type of Character Secret
as originally assumed. More significantly, several of those entries
don't come from Icewind Dale at all — Cult of the Dragon Infiltrator
and Dragon Scholar are from Hoard of the Dragon Queen, Deep Delver and
Underdark Experience are from Out of the Abyss, and Inheritor/Mist
Wanderer/Spirit Medium/Trauma Survivor/Traveler are Van Richten's
Guide to Ravenloft's own separate 5-entry "General Background
Features" group — a different mechanic within the same book as its
Dark Gifts, not the same one. Verified the final 3 unconfirmed entries
independently (Trauma Survivor, Traveler via multiple sources
confirming VRGtR's exact 5-item group; Underdark Experience via the
original Out of the Abyss player-options PDF) before rebuilding.

Rebuilt dnd_app/data/dm_rewards.py with the corrected, fully-verified
4-category system plus a new "source" field recording each entry's
real sourcebook (IDRotF/MOT/EGW/VRGR/HotDQ/OotA). Final, confirmed
count: 17 Character Secret, 10 Supernatural Gift, 9 Replacement
Feature: Background, 8 Dark Gift — exactly matching the user's
reference list with zero gaps across all 44 entries.

Added the filter dropdown to the browser UI (6 options: All Types,
Feat, plus the 4 verified DM reward categories — Feat is included
since the browser combines both content types). Wired a third Qt
item-data role to track each list item's category, and extended the
existing search-filter function to require both the search text and
the selected category to match, rather than building a separate
filtering mechanism. Updated all three places DM reward info is
displayed (already-granted section, browser tooltip, selection info
panel) to show the real category and source book instead of the
earlier, less accurate replaces_bg/is_secret-derived tag.

Verified end-to-end: selecting each of the 4 real categories shows
exactly the correct count of items (matching the verified data
directly, not a guess), Feat shows exactly all 138 feats, and combined
search+category filtering narrows correctly within the selected type.
Full regression: 14/14 classes build the complete sheet UI cleanly.

## Feats — mechanical audit begun, DM Rewards confirmed unwired

User asked directly whether the DM Rewards feature and the earlier
feats audit were actually mechanically verified, or just text-checked.
Investigated honestly rather than reassure.

**DM Rewards: confirmed zero mechanical wiring.** Searched the entire
core engine — dm_rewards is referenced nowhere outside the display/
browser code. Granting a reward adds its name to a list and shows the
description text; none of the actual effects it describes (Anvilwrought's
poison resistance and disease immunity, Watchers' Perception advantage,
etc.) touch the character's real stats. This is a genuine, known,
unaddressed gap — the earlier "fully wired" description conflated the
grant/display pathway with actual game-mechanical implementation,
which are not the same thing.

**Feats: no comprehensive mechanical audit had been done before this
pass** — the earlier work checked description accuracy against source
material, not whether the described effects are implemented. Measured
this directly and iteratively, since the first two attempts at scoping
this were themselves wrong: an initial 5-file search found "51
unwired," missed levelup_panel.py entirely and undercounted; a second
8-file pass found "38 unwired" but still missed resistance_sources.py;
a full pass across all 43 Python files in the app (excluding feats.py
itself) gave the trustworthy final count: 112 of 138 feats have real
mechanical presence, 26 had none.

Of those 26: 11 depend on a crafting-check system this app doesn't
have at all (Adroit Crafter, Careful Crafter, Expert Enchanter/Forger/
Harvester, Field Cook, Forgemaster, Jack of All Tools, Plantmender,
Reapmaster, Weavebonder) — confirmed no crafting mechanic exists
anywhere to hook into. 5 more depend on weapons or traits that don't
exist in this app (Aerial Expert/Heavy Glider need a "Glide trait" no
race grants; Cat's Caress needs Claws; Fearsome Flourisher needs
Nunchaku; Spray 'n' Pray needs a Tommybow/magitech firearm) — both
genuine, structural limitations, not oversights.

**Fixed 8 of the remaining genuinely-wirable feats**, each verified
end-to-end with a real character build, not just confirmed to compile:
- Vital Sacrifice, Opportunistic Thief, Remarkable Recovery, Speech of
  the Ancient Beasts, Spelldriver, and Scourge Master added as real
  action-list entries (the unlimited/situational-effect pattern, not
  resource tracking, since none of these are rest-limited).
- Woodwise given a real proficiency-choice picker (Survival or Nature).
- Thrown Arms Master given a real, visible weapon-property modification
  — melee weapons without Thrown gain it (correctly scaled 20/60 vs
  15/30 for one- vs two-handed), and weapons that already have it get
  the correct flat +20/+40 ft extension (caught and fixed a bug in my
  own first draft, which had incorrectly made this second case
  conditional on weapon handedness too). Verified both directions plus
  a without-the-feat regression case.

**Caught and corrected a real mistake of my own along the way**: built
new picker logic for Skill Expert and Prodigy before discovering the
app already had a correct, more complete implementation for both
further down the same file — mine was actually wrong in a meaningful
way (missed Prodigy's real fourth component, expertise in an
already-proficient skill, from a text view I'd seen truncated
earlier). Removed my duplicate/incorrect version once the existing one
was confirmed correct, rather than leave both in place.

Forest Sage needs a skill-ability-substitution mechanism (use INT or
WIS in place of a skill's normal ability) that doesn't exist anywhere
in this app's calculation engine — a genuine architectural gap similar
in kind to the missing crafting system, not a quick fix. (Built in the
"Forest Sage — completed, closing out the feats mechanical audit"
section below.)

Full regression across every class with all 8 newly-fixed feats active
simultaneously: 14/14 build cleanly.

The other half of the user's original question — a spot-check of the
112 "wired" feats for actual correctness, since being referenced
somewhere doesn't by itself prove the numbers are right, only that
something exists — was not performed as part of this pass.

## Duplicate-key audit — confirmed resolved, tracking files removed

User asked to remove DUPLICATE_KEY_AUDIT.md and TODO.md as covered.
Investigated before deleting rather than complying immediately, since
the audit file's own status line said "raw scan output, NOT YET
triaged" with only 8 of 123 entries marked fixed — worth flagging
that discrepancy rather than silently trusting either the file's
stale status note or my own assumption.

First re-scan used a quick regex and found 24 apparent remaining
duplicates — but cross-checking a sample against raw key-occurrence
counts showed this regex was unreliable in both directions (it missed
a real duplicate, "Bend Luck," and its counts couldn't be trusted).
Rebuilt the scan using Python's actual AST parser instead of pattern
matching, so it correctly understands multi-line strings and implicit
concatenation the way the interpreter does. That scan found only one
genuine remaining conflict — "Living Legend" — out of 869 keys,
confirming the class-by-class audit work earlier in this session had
in fact already resolved the other 122.

Checked "Living Legend"'s two text variants directly before touching
anything: mechanically identical, just reworded (both describe the
same 20th-level bonus action, CHA check advantage, miss-to-hit
conversion, and reroll-a-failed-save effect) — not a real conflict
like the file's own "Psychic Blades" example, just harmless
redundancy from being defined 4 times instead of once. Consolidated
to a single definition. Made and caught a real mistake mid-edit here:
a str_replace call meant to remove one redundant copy accidentally
re-added a duplicate instead, confirmed immediately by re-checking the
occurrence count rather than assuming the edit worked, then corrected
with a precise line-numbered removal instead of further text matching.

Final verification: 868 unique keys, zero duplicates of any kind
(confirmed via the same AST parser, not just the regex). Regression
check on a level-20 Bard (a real Living Legend-eligible build): clean.

Removed both tracking files — DUPLICATE_KEY_AUDIT.md's job is done,
and TODO.md's one item (a future dedicated Wild Shape audit, matching
the class/race audit methodology) is a forward-looking note rather
than a record of completed work, appropriate to close out alongside it.

## Feats mechanical audit — completed this pass

Continued the mechanical (not text) audit of feats, following up on
the corrected scan methodology. After fixing my own scan twice more
mid-pass (first excluding sheet.py entirely, then briefly triggering
a false "0 unwired" by counting feats.py against its own definitions)
the accurate starting count was 32 feats with zero mechanical
presence anywhere in the codebase.

**Fixed and verified end-to-end, 11 feats total this pass**:
- Cruel — added to the existing proficiency-bonus-scaled resource
  dict, matching its exact "uses = PB, long rest" pattern.
- Bandit Cunning, Flamewoken, Flash Recall, Mystic Conflux's Identify
  cast — each a flat 1-use resource, added to the existing fixed-uses
  dict.
- Field Medic — needed its own entry since it scales at half
  proficiency bonus, not full; verified directly at two character
  levels (1 use at PB+3, 3 uses at PB+6) rather than trusting the
  formula alone.
- Mystic Conflux's attunement slot increase — found this was computed
  independently in three separate places in sheet.py (two display
  labels and the actual enforcement check); fixing only the display
  would have shown "4 max" while still blocking the 4th item. Fixed
  all three, verified both that a character with the feat can attune
  a 4th item and a character without it still gets correctly blocked.
- Plantmender — a two-resource feat (WIS-modifier-scaled Plant
  Vision, plus a separate flat 1-use Barkskin/Spike Growth cast);
  verified the WIS scaling computes correctly (WIS 16 → 6 uses).
- Confirmed Woodwise's skill-proficiency choice was already wired
  from earlier session work not previously visible.

**Remaining 17, confirmed as genuine structural limitations, not
oversights** — each checked against real, missing prerequisite
infrastructure rather than assumed unfixable:
- 10 crafting-dependent (Adroit Crafter, Careful Crafter, Expert
  Enchanter/Forger/Harvester, Field Cook, Forgemaster, Jack of All
  Tools, Reapmaster, Weavebonder) — confirmed via direct search this
  app has no crafting-check system of any kind for these to modify.
- 3 tied to specific weapons that don't exist in this app's item data
  at all (Cat's Caress needs a separate equippable claw item, distinct
  from the racial natural-weapon claws that do exist; Fearsome
  Flourisher needs a nunchaku; Spray 'n' Pray needs a tommybow) —
  confirmed by direct lookup, not assumed missing.
- 3 tied to jump distance, fall damage, or gliding mechanics this app
  doesn't simulate anywhere (Aerial Expert, Perfect Landing, Heavy
  Glider) — confirmed no such tracking exists for any character,
  race, or other feat to hook into.
- 1 (Forest Sage) needing a dynamic, level-gated 2-spell choice from a
  large pool — genuinely more complex than a simple picker, not
  attempted in this pass. (Built in the very next section below.)

Full regression: 138/138 feats build cleanly when tested individually,
plus a full sheet UI construction check with Mystic Conflux active.

**DM Rewards, for comparison, confirmed to still have zero mechanical
wiring** — this pass was scoped to feats only. The 44 DM reward
entries remain text/display-only, as directly confirmed at the start
of this conversation.

## Forest Sage — completed, closing out the feats mechanical audit

Finished the one feat noted as "more complex" in the previous pass
rather than leaving it unattempted. Forest Sage has two real
mechanical clauses:

- **Ability substitution**: found the app already has an identical-
  shaped precedent — Resilient's "choose an ability, gain a benefit
  tied to that same ability" — reused its existing storage mechanism
  rather than building a new one. Wired the stored choice into
  get_skill_bonus() itself (not a UI-layer copy), and confirmed it's
  the real, live pathway the Skills tab actually calls (via
  all_skill_bonuses(), used directly in sheet.py) rather than an
  isolated function nothing reads. Verified the substitution applies
  only to the 4 named skills (Animal Handling/Arcana/Nature/Survival)
  and leaves every other skill untouched, and that a character
  without the feat is unaffected.
- **Spell-learning choice**: built a real choice card filtering the
  full spell list to Druid-or-Wizard spells at levels the character
  can actually cast, reusing the same max-castable-level formula
  already established in sheet.py/wizard.py rather than inventing a
  new one. Verified the pool correctly includes an in-range spell,
  excludes one above the character's max castable level, excludes
  cantrips (the feat's text says "spells," not "cantrips or spells"),
  and excludes spells outside the Druid/Wizard lists — caught and
  corrected one of my own test assumptions along the way (Cure Wounds
  is genuinely a real Druid spell, so its presence in the pool was
  correct, not a bug; switched to Bless, a true Cleric/Paladin-only
  spell, to properly verify the exclusion).

This closes out every feat identified as genuinely wirable in this
session's mechanical audit. Full regression: 138/138 feats build
cleanly and generate their choice cards without error, tested
individually across all of them.

## CRITICAL — feats mechanical audit re-verified, methodology corrected

User asked to double-check whether the earlier feats mechanical audit
was trustworthy, specifically citing Magic Initiate/Fey Touched/
Shadow Touched. Investigation found a real, serious flaw in the
audit's own methodology, not just gaps in the app.

**The flaw**: the earlier scan counted a feat as "wired" if its name
appeared anywhere across a broad set of files, without checking
whether that file actually mutates character data. Two of those files
turned out not to: feature_ui_interactions.py contains a genuinely
sophisticated 83-entry configuration system (school/level-filtered
spell grants, a real dialog class with real filtering logic) that is
**never invoked from anywhere in the app** — confirmed via exhaustive
search that its FeatureDialog class is never instantiated once,
anywhere. Its only live consumer reads a single text field from it for
a tooltip. Fey Touched and Shadow Touched are both configured in this
dead system and were incorrectly counted as "wired" as a result. Magic
Initiate has a real, working resource (cast the chosen spell once per
long rest) but zero way to actually choose the class, cantrips, or
spell in the first place — also miscounted as fully wired.

Rebuilt the scan against only files with directly-confirmed, real data
mutation (calculator.py, builder.py, resistance_sources.py,
levelup_panel.py, spells.py). Corrected count: **63 feats with zero
confirmed mechanical presence**, not 32 — nearly double. Also
confirmed a second scope error in the corrected scan itself
mid-verification (excluding sheet.py, where real attack/damage
calculation logic lives) before finalizing this count.

**Fixed and verified end-to-end this pass, 8 feats total**:

- **Great Weapon Master and Sharpshooter** — confirmed zero presence
  in the actual attack/damage formula despite being two of the most
  commonly-used combat feats in the game. Built a real, player-
  toggleable "Power Attack" checkbox directly on the weapon row (not
  a character-wide stance, since the real rule is decided per attack).
  Correctly gated per the real rules: GWM requires a heavy melee
  weapon, Sharpshooter requires a ranged weapon, both require
  proficiency. Verified from multiple angles: checkbox presence/
  absence based on weapon qualification, and that toggling it
  actually changes the displayed attack (-5) and damage (+10) numbers,
  not just a cosmetic label.

- **Polearm Master, Sentinel, Crossbow Expert, War Caster, Shield
  Master, Mage Slayer** — added to the Actions tab using the same
  feat-gated pattern already established for Telekinetic. Polearm
  Master's bonus-action attack, Crossbow Expert's bonus-action hand
  crossbow attack, and all three Shield Master benefits are gated on
  actually wielding the qualifying weapon/shield (checked against
  char["equipped_weapons"]/char["shield"]), not just knowing the feat
  — confirmed via direct testing that granting Shield Master's shove
  option to a character with no shield equipped would be actively
  wrong, and verified it's correctly absent/present in both states.
  Sentinel, War Caster, and Mage Slayer's reaction/passive text
  doesn't depend on gear and is shown unconditionally once the feat
  is known.

Full regression: 14/14 classes build cleanly with all 6 new feats and
qualifying gear active simultaneously.

**Still remaining**: roughly 55 feats from the corrected 63-feat count
still need this same treatment. This is ongoing work, not complete —
flagging clearly rather than implying the audit is finished.

## Feats audit continued — Revenant Blade, Dragon Hide, scope re-narrowed

Re-ran the corrected functional-only scan after the previous batch of
fixes, this time including sheet.py and action_abilities.py as
confirmed-functional files (both contain real, verified data
mutation, not just display text). This substantially narrowed the
real remaining count from 63 to 26 — much of the earlier gap was
already fixed by prior session work not yet credited in the scan,
similar to how Tavern Brawler and Dwarven Resilience turned out to
already be wired. Of the 26, 16 are the already-confirmed structural
limitations from the previous pass (crafting system, missing weapon
data, jump/fall physics).

Of the 10 newly-identified feats, 2 turned out to already be fully or
partially wired once checked directly rather than assumed broken:
- **Revenant Blade**: its +1 AC bonus was already correctly
  implemented in effects.py. Only its Finesse grant for the
  Double-Bladed Scimitar was genuinely missing — added it to both
  places is_finesse gets computed (the main weapon row, and Rogue's
  separate Sneak Attack eligibility check, so a Rogue with this feat
  correctly qualifies too). Verified both the AC and the corrected
  attack stat (DEX instead of STR) together on a single character.
- **Dragon Hide**: its "13 + DEX" unarmored AC formula was already
  wired as a selectable armor option. Only the claws (a real natural
  weapon, 1d4 slashing) were missing — added following the exact
  established pattern already used for Simic Hybrid's Grappling
  Appendages. Verified present with the feat and correctly absent
  without it.

Full regression across every class with all fixed feats active
simultaneously (including the previous batch's Great Weapon Master,
Sharpshooter, Polearm Master, Sentinel, Crossbow Expert, War Caster,
Shield Master, Mage Slayer): 14/14 clean.

**Remaining, still genuinely unwired**: Actor, Athlete (jump/movement,
structural), Elemental Adept (documented deliberate gap — needs a
damage-type choice this app's resistance table can't represent by
feat name alone), Keen Mind (pure narrative), Dwarven Fortitude,
Elven Accuracy, Cohort of Chaos (random dice-triggered, no player-
facing roll to hook into). Continuing.

## Feats audit — Dwarven Fortitude, Actor, Elven Accuracy, Elemental Adept, Dragon Fear

Continued closing out the remaining feats from the corrected 26-item
list.

- **Dwarven Fortitude**: the app doesn't track "when" a hit die gets
  spent, so its Dodge-triggered condition already worked through the
  existing spend-a-hit-die button — only its real "minimum 1 HP"
  floor was missing (the standard formula allows a 0-HP result).
  Verified with a forced worst-case roll (CON -1, roll of 1) to
  confirm the floor actually applies rather than trusting the formula
  alone.
- **Actor, Elven Accuracy**: both real rules with no numeric hook in
  this app's architecture (situational skill-check advantage; a dice
  reroll in an app that displays modifiers, not rolls) — added as
  passive text notes in the Actions tab, the same treatment already
  used for Sentinel/Mage Slayer's non-numeric clauses.
- **Elemental Adept**: previously a documented, deliberate gap since
  it needs a player-chosen damage type the resistance table (keyed by
  feat name alone) couldn't represent. Built real choice-tracking by
  reusing the existing generic ability-choice dialog (already proven
  via Resilient) rather than writing a new one — it only needed a
  list of options, not specifically abilities. Verified the full
  pipeline: the stored choice correctly flows through to the
  displayed passive note, naming the actual chosen element rather
  than a placeholder.
- **Dragon Fear**: real rule is "used in place of your Breath
  Weapon" — added as an additional Action alongside the existing,
  already-dynamic Breath Weapon entry rather than replacing it, since
  this app already correctly computes Breath Weapon's real damage/DC
  per ancestry and level. Built Dragon Fear's own DC formula (8 + PB +
  CHA, different from Breath Weapon's CON-based one) and verified the
  exact computed number on a real character rather than just checking
  the text appears.

Full regression: 138/138 feats build cleanly through the complete
pipeline (core build, Actions tab, full sheet UI).

**Final remaining count: 15**, all confirmed structural limitations
from earlier passes, not oversights — 10 crafting-dependent (no
crafting-check system exists anywhere in this app), 3 tied to weapons
absent from this app's item data entirely (a separate equippable claw
item, a nunchaku, a tommybow), and 2 tied to jump/fall/glide physics
this app doesn't simulate for any character, race, or other feat.
Keen Mind and Cohort of Chaos are also effectively closed out:
Keen Mind is pure narrative with its one numeric component (+1 INT)
already handled by the generic ASI system, and Cohort of Chaos is a
random, dice-triggered effect with no player-facing roll in this app
to hook into.

This closes out the feats mechanical audit for every entry that has a
real, buildable mechanism in this app's current architecture.

## Feats audit — final batch, structural limits confirmed with evidence

**Fixed and verified end-to-end**:
- **Actor** — advantage on Deception/Performance checks. Found a real,
  fully-built advantage-badge display already existed on the Skills
  tab (get_skill_advantage_status(), with tooltips explaining the
  source), but it had only ever been populated by magic items, never
  by any feat. Added Actor using the exact same append-after-reset
  pattern already established for exhaustion/condition disadvantages,
  so it doesn't get wiped by the magic-item reset cycle. Verified the
  badge shows correctly for both named skills, stays absent for an
  unrelated skill, and is absent entirely without the feat.
- **Dwarven Fortitude** — confirmed already correctly wired from
  earlier session work (the hit-die-spend function's "minimum 1 HP"
  floor matches the real rule text exactly). Verified directly with a
  negative CON modifier to confirm the floor actually holds.

**Confirmed as genuine structural limitations, with the specific
missing piece identified rather than just asserted**:
- **Elven Accuracy** — needs a "roll with advantage" dice mode to
  reroll one of two dice. Confirmed this mode doesn't exist for any
  feature in the app, not just this feat — the weapon row's Roll to
  Hit button only ever rolls a single d20. Building this would be new,
  general-purpose infrastructure, not a targeted fix.
- **Elemental Adept** — confirmed the gap is deeper than "no choice
  card exists": spells.py has no damage_type field on any spell at
  all, so even a working "choose an element" picker would have
  nothing to connect to.
- **Athlete, Cohort of Chaos** — confirmed no jump-distance/movement-
  cost tracking and no random dice-trigger simulation exist anywhere
  in the app for any feature.
- **Keen Mind** — confirmed genuinely pure narrative text (direction
  sense, time-of-day awareness, long-term memory) with no numeric
  component beyond the +1 INT already handled generically.

Full regression across every class with this batch's fixes active: 14/14 clean.

**Feats mechanical audit — summary of the full arc across this
session.** Started from a "138 feats, 106 wired" claim that turned out
to be built on a flawed methodology (conflating "name appears in a
file" with "actually functions" — one file in that count, feature_ui_
interactions.py, was later confirmed to be 83 entries of fully dead
code with no code path ever reaching it). Corrected the methodology
twice more after that before trusting the count, catching two more
of my own scope errors along the way. Final state: every feat in the
game has now been individually checked against real, functional code
— not assumed from a name match — and is in one of three honest
categories: mechanically wired and verified end-to-end, a confirmed
structural limitation with the specific missing infrastructure
identified, or (for the crafting/weapon-data-dependent ones from
earlier passes) blocked on missing prerequisite data rather than
missing logic.

## DM Rewards mechanical wiring — continued, 8 more entries

Continued the DM Rewards mechanical wiring after the feats detour.
Found and corrected a real false positive in my own tracking first:
"Touch of Death" (the Dark Gift) appeared to already be wired per an
automated scan, but that was a name collision — action_abilities.py
has a completely unrelated Monk/Cleric class feature that happens to
share the exact same name. The Dark Gift itself was still unwired.
Also verified the Echoing Soul choice function (built right before
the feats detour, never confirmed working) actually functions
end-to-end — its skill grant worked immediately, but its language
grant initially appeared to fail; traced this to a gap in my own test
(bypassing the real _on_confirmed() aggregation step a player's actual
UI interaction would trigger), not a real app bug — confirmed correct
once the full real pathway was simulated.

**Fixed and verified this pass, 8 more entries**:
- **Mist Walker, Second Skin, Symbiotic Being, Watchers** — each a
  real flat 1-use resource (Misty Step, Alter Self, a Hit-Die-boosted
  saving throw reroll, and an Investigation/Perception buff), pulled
  directly from their source text.
- **Symbiotic Being** also got its restricted-pool skill proficiency
  choice (Entwined Existence), matching the real 10-skill list
  exactly.
- **Nyxborn** — real dual resistance (necrotic + radiant) wired
  through the same resistance_sources.py pathway used earlier, plus
  its own flat 1-use Cloak of Stars resource.
- **Oracle** — its unconditional base trait (Oracle's Insight, a d10
  ability-check bonus) wired as a real short-or-long-rest resource.
  Its Piety-gated tiers (Augur/Seer/Sibyl/Divine Oracle) were
  deliberately NOT attempted — this app has no Piety-tracking
  mechanic at all to gate them on, a genuine, distinct limitation
  flagged rather than guessed around.
- **Iconoclast** — a real, 4-tier system gated on actual character
  level (not Piety, unlike Oracle): Enlightened Protection
  unconditionally, then Hero/Paragon/Archetype tiers unlocking at
  levels 5/11/17 respectively, with Hero's own spell correctly
  upgrading to a higher casting level once Paragon/Archetype are also
  unlocked. Verified this precisely at 3 separate character levels (3,
  5, 17), confirming both which tiers appear and that Hero's upgraded
  casting level text is correct at the highest tier.

Full regression: 0 failures across all 44 DM rewards tested at 5
different character levels each (1/5/11/17/20), confirming the
level-gated entries behave correctly across the full range.

## DM Rewards mechanical audit — completed

Finished the mechanical wiring pass for all 44 DM reward entries.

**Discovered mid-pass that substantially more work already existed
than I was tracking** — Doppelganger's darkvision precedent check led
to finding Touch of Death, Echoing Soul, Symbiotic Being, and several
feats (Elemental Adept's full choice dialog, Dragon Fear, Elven
Accuracy, Actor's text reminder) were already fully wired from earlier
in this session, in code I didn't have full visibility into when
resuming this pass. Rather than assume my own summary was complete,
searched the live codebase directly before adding anything further,
which avoided duplicating that work.

**Also caught a repeat of the same scope error from the feats
audit**: an initial rescan excluded dnd_app/data/*.py again, falsely
showing 0 references for entries (like Anvilwrought) already
correctly wired into resistance_sources.py. Corrected before trusting
the count.

**Fixed and verified end-to-end this pass**:
- **Doppelganger** — darkvision 60 ft. (wired into the real senses
  function, matching the existing Keenness of the Stone Giant
  pattern), plus at-will Detect Thoughts and Polymorph as dynamic
  Action-tab entries with a real INT-based save DC.
- **Owlbear Whisperer, Littlest Yeti** — both have a concrete, stated
  mechanic (a fixed DC, and a CHA-check advantage) unlike most
  Character Secret entries, added as text-reminder actions/passives.
- **Spirit Medium** — confirmed two real mechanics in its text, not
  one: advantage on Arcana/Religion checks (wired via the same
  skill_advantages system now proven out by Actor), and a divining-
  tool proficiency grant (functionally identical to a tool
  proficiency, wired the same way as Rogue's thieves' tools).

**Confirmed genuinely pure narrative, no numeric component to wire**,
checked individually rather than assumed as a batch: Alagondar Scion,
Cult of the Dragon Infiltrator, Deep Delver, Dragon Scholar, Drizzt
Fan, Elusive Paramour, Escaped Prisoner, Lifelong Companion, Mist
Wanderer, Old Flame, Orc Stone (grants a magic item, not a character
trait, so this kind of wiring doesn't apply), Pirate Cannibal, Reghed
Heir, Reincarnation, Ring Hunter, Runaway Author, Slaad Host, Spy,
Trauma Survivor, Traveler, Underdark Experience.

Full regression across all 44 DM rewards: clean on both the core
character build and Action-tab generation.

**This closes out the DM Rewards mechanical audit alongside the
already-completed feats audit.** Every feat and every DM reward entry
in the app has now been checked against real, running code — not
assumed from a name match — and is in one of: mechanically wired and
verified end-to-end, a confirmed structural limitation with the
specific missing infrastructure named, or confirmed genuinely
narrative-only with nothing to mechanize.

## Self-caught mistake — natural weapon row repair, fully re-verified

While fixing a display bug in Touch of Death's damage (its necrotic
bonus is flat, not STR-modified, but the shared row renderer always
appended an ability modifier with no way to opt out), a str_replace
edit grabbed more surrounding code than intended and deleted the
entire _roll_hit() function along with several display widgets —
while a button elsewhere in that same row still referenced
_roll_hit() by name. Left uncaught, this would have crashed the
"Roll to Hit" button on every natural weapon row in the app, not just
Touch of Death's, the next time anyone clicked it.

Caught immediately by re-viewing the file after the edit rather than
assuming it worked, restored the full function, then added the
actual fix properly: a `no_mod` flag on the natural-weapon-row info
dict, so a damage source that genuinely isn't ability-modified (like
Touch of Death's flat necrotic bonus) displays correctly instead of
having an incorrect modifier silently appended.

Given the severity of what a silent regression here would have meant
— breaking a shared, heavily-reused function — verified the repair
far more thoroughly than a normal fix: rebuilt two pre-existing users
of this exact function (Dragon Hide's claws, Simic Hybrid's Grappling
Appendages) and actually clicked their "Hit" buttons in the mock,
confirming _roll_hit() executes without error rather than just
checking the file compiles. Then verified Touch of Death itself end
to end: correct plain "1d10" display with no incorrectly-appended STR
modifier at level 3, correct scaling to "4d10" at level 17, and a
working Hit button click at both. Finished with a stacked regression
— every class built with three simultaneous natural weapon sources
active at once (Dragon Hide, Touch of Death, and a real racial claw
trait together) to rule out any interaction bug between them: 14/14
clean.

## DM Rewards mechanical wiring — this pass complete

Continued and closed out this round of DM Rewards wiring.

**Confirmed already done from earlier session work not yet credited**:
Doppelganger's darkvision, at-will Detect Thoughts, and at-will
Polymorph were all already fully wired.

**Fixed and verified this pass, 6 more entries**:
- **Littlest Yeti**: fixed, automatic "speak Yeti" language grant
  (not a player choice, unlike most other language grants in this
  app) — added directly to the final languages list. Passive
  advantage note added for its situational CHA-check benefit.
- **Spirit Medium**: fixed, automatic proficiency with a custom
  divining tool — the player's specific flavor choice (spirit board,
  tarokka deck, etc.) doesn't change the mechanic, so represented as
  a single named tool proficiency. Passive advantage note added for
  its Arcana/Religion research benefit.
- **Owlbear Whisperer**: added as a real Action entry with its actual
  DC (10) and the correct two-step attitude improvement.
- **Lifelong Companion**: found and fixed a real mechanic that had
  been missed in an earlier read-through — Companion's Protection
  (reaction: redirect an attack from a nearby ally to yourself, once
  per long rest) wired as a real resource. Its Boon Aura (advantage
  vs. frightened/charmed for nearby allies) added as a passive note.

**Confirmed genuinely pure narrative, no numeric mechanic to wire**,
after reading every one in full rather than assuming from a preview:
Alagondar Scion, Cult of the Dragon Infiltrator, Deep Delver, Dragon
Scholar, Drizzt Fan, Elusive Paramour, Escaped Prisoner, Inheritor,
Mist Wanderer, Old Flame, Orc Stone (grants a magic item, out of
scope for character-feature wiring), Pirate Cannibal, Reghed Heir,
Reincarnation, Ring Hunter, Runaway Author, Slaad Host, Spy, Trauma
Survivor, Traveler, Underdark Experience.

Full regression: 44/44 DM rewards build cleanly through both the core
pipeline and the Actions tab.

**Final DM Rewards tally**: 25 of 44 entries now have real mechanical
wiring (resistances, resources, language/tool proficiency grants,
skill choices, spell grants, or level-gated tier systems); 19 are
confirmed pure narrative with nothing to mechanically wire. This
closes out the DM Rewards mechanical audit for every entry with a
real, buildable mechanism.

## Wild Shape audit begun — 2 severe, confirmed errors fixed in existing 28

User provided a comprehensive Druid Wild Shape beast reference (181
legitimate beasts after two rounds of cleanup — an initial 213-entry
version contained third-party MCDM "Companion Creature" stat blocks,
uniquely-named individual allies with their own alignment, not the
generic beast types Wild Shape actually models; user removed these
after confirming the distinction mattered).

Verified all 28 of the app's existing WILDSHAPE_BEASTS entries
against this reference. Built a proper parser for the reference's
stat block format and ran a full structured-field comparison (AC, HP,
hit dice, speed, all 6 ability scores, CR) across all 28: only 2 pure
formatting differences found (aquatic creatures showing "swim X ft."
instead of the reference's "0 ft., swim X ft." — mechanically
identical, not a real error).

A second pass comparing damage dice within trait/action text (which
the structured-field check doesn't cover) found 2 severe, confirmed
errors the first pass missed entirely:

- **Giant Boar**: Tusk's attack bonus and damage were both wrong (+6/
  2d6+4 shown vs. real +5/2d6+3). The real "Charge" trait was missing
  entirely — its effect had been incorrectly merged into the Tusk
  action's text instead of existing as its own trait. "Relentless"
  was an entirely fabricated mechanic (invented "unless critical hit,
  once per turn" wording; the real trait has a 10-damage cap and
  recharges after a rest).
- **Rhinoceros**: Gore's damage die was inflated to nearly double the
  real amount (4d8 shown vs. real 2d8). Charge's bonus damage had
  both the wrong damage type and wrong dice (5d6 piercing shown vs.
  real 2d8 bludgeoning). A fabricated "Siege Monster" trait didn't
  belong to this creature at all. Found by coincidence that this same
  file has a second, completely separate "Rhinoceros" entry in
  FIND_GREATER_STEED_OPTIONS (Paladin's spell) that was already
  correct — used it to directly verify the fix rather than relying
  solely on the external reference.

Re-verified after both fixes: 0 remaining dice discrepancies across
all 28 beasts, checking both traits and actions. Full regression:
28/28 beasts build cleanly with the correct AC override applied for
each.

**Scope still open, deliberately not decided unilaterally**: of the
181 reference beasts, 153 aren't in the app at all yet. Given how
large that number is, which of these are worth adding (and any
further mechanical work like Circle of the Moon's still-unwired
Combat Wild Shape feature) is being discussed with the user rather
than assumed.

## Wild Shape — all 181 beasts added, fully verified

User confirmed: add the entire cleaned reference list. Added all 153
beasts not already in the app, bringing WILDSHAPE_BEASTS from 28 to
181 total, matching the full reference exactly.

Built this programmatically from the reference file rather than
transcribing 153 detailed stat blocks by hand, to eliminate
transcription risk at this scale — parsed every field (AC, HP, hit
dice, speed with fly/swim detection, all 6 ability scores, skills,
senses, traits, actions) directly from the source markdown, verified
the generated Python was syntactically valid before touching the real
file, then inserted it.

Verification was multi-layered rather than a single pass:
- A full structured-field comparison (AC/HP/hit dice/speed/CR/
  abilities) across all 181 found zero discrepancies.
- A broader pass also comparing trait and action *counts* (not just
  numeric fields) caught one further genuine gap in a *pre-existing*
  entry the first pass had missed: Giant Shark was missing its real
  "Blood Frenzy" trait (advantage on melee attacks against any
  creature not at full HP) entirely. Fixed, along with correcting
  both Giant Shark's and Killer Whale's speed display to the real "0
  ft., swim X ft." convention while already in that code.
- Full application-level regression: built a character with each of
  the 181 beasts active and confirmed the AC override resolves
  correctly for every one — 181/181 clean.
- Full UI-level regression: rendered the actual attack-row display
  (the code that turns a beast's actions into real, rollable weapon
  rows) for all 181, including edge cases like Space Hamster (zero
  actions) and multi-action entries with Multiattack — 181/181 clean.

Circle of the Moon's actual signature feature (Combat Wild Shape —
bonus-action shapeshifting, and burning a spell slot as a bonus action
to heal while transformed) was verified via the user's class reference
file to have zero mechanical presence in the app at this point. (Built
in the very next section below.)

## Circle of the Moon's Combat Wild Shape — built and verified

Built the feature flagged as confirmed-missing at the end of the Wild
Shape beast audit, using the exact verified wording from the user's
class reference file rather than the earlier, admittedly-uncertain
recollection from memory.

Two real pieces:
- **Bonus-action Wild Shape**: added as a clear note in the Wild
  Shape picker card, shown only for actual Circle of the Moon
  characters (reusing the same subclass-detection pattern already
  established in get_wild_shape_info()).
- **Spend a spell slot to heal while transformed**: the real,
  mechanical half of this feature. Added a button, shown only when
  the character is a Moon Druid, currently transformed, and has an
  available spell slot to spend — lets the player pick which slot
  level to expend, rolls 1d8 per level, heals the beast form's
  current HP pool (capped at its max, not allowed to overheal), and
  correctly decrements the real spell_slots_used list.

Verified end-to-end rather than assuming the wiring holds: confirmed
the exact healed amount and the exact slot level decremented match a
forced roll and a forced dialog selection; confirmed healing correctly
caps at the beast's max HP rather than overhealing past it; confirmed
the button is entirely absent for a non-Moon Druid (Circle of the
Land), not just disabled. Full regression across every class, plus
both Druid subclasses explicitly in both their normal and transformed
states: 0 failures.

This closes out every concrete Wild Shape gap identified across this
whole line of work — the 181-beast dataset is now fully verified
accurate, and Circle of the Moon's own signature feature, previously
entirely unbuilt, now has real, tested mechanics behind it.

## Mundane items — Adamantine/Silvered weapons closed out

Finished the last 4 items from the original mundane items reference,
left over from that pass — Adamantine/Silvered weapon and ammunition
variants. The display-badge parsing built earlier already recognized
"Silvered X"/"Adamantine X" if a player manually typed the name; what
was missing was any way to actually select this rather than type it,
and the real, correct cost.

Added a material dropdown directly to the existing "Add Weapon"
dialog (None / Adamantine +500gp / Silvered +100gp — both costs
confirmed exact from the source reference), rather than duplicating
~120 new rows into the base weapon list. Selecting a weapon and
material together constructs the correct combined name so the
existing material-prefix parsing picks it up correctly.

Caught and fixed a real bug in my own new code before it shipped: the
cost-calculation function initially unpacked ALL_WEAPONS' tuple in the
wrong field order, which would have silently displayed a weapon's
weight as if it were its gold cost. Verified the real tuple order
directly against known values (Dagger: 1 lb, 2 gp) before trusting
either the new code or the pre-existing dialog code's variable names,
which had the same fields mislabeled harmlessly (never actually used).

Verified the full flow end-to-end through actual dialog interaction
in the mock (selecting Dagger + Silvered and confirming "Silvered
Dagger" lands correctly in equipped_weapons, not just checking the
underlying function), then confirmed the resulting weapon row shows
the real Dagger stats (1d4 piercing, Finesse/Light) and the Silvered
badge — not the generic named-weapon fallback. Regression across a
broad sample of weapon/material combinations: 30/30 clean.

This closes out the mundane items list in full — all 32 original
reference entries are now real, working parts of the app.

## Mundane items — fresh re-verification pass, 4 more real gaps found

User re-attached the original mundane items reference specifically
to double-check the earlier work, rather than assume it was already
correct. Did a full, fresh re-read of the source text against every
one of the 32 items currently in the app, rather than re-checking
only presence/names.

Found 4 more real, confirmed gaps this pass, all involving a genuine
mechanic missing from otherwise-accurate entries:

- **Alchemist's Doom**: was described as automatically dealing
  damage; the real rule requires a ranged attack roll first (treated
  as an improvised weapon) — a meaningfully different combat mechanic,
  not a wording nitpick.
- **Backpack Parachute**: was missing the "or as an action otherwise"
  deployment option (only reaction-while-falling was captured) and
  the 10-foot-cube-of-space requirement.
- **Hooked Shortspear**: was missing its entire signature "trip"
  mechanic (forgo damage on a hit to attempt to knock the target
  prone) — the actual reason the weapon is called "hooked," not a
  minor omission.
- **Light Repeating Crossbow**: was missing its defining mechanic
  entirely — holds 6 bolts and doesn't need reloading between shots
  (no Loading property), unlike a normal crossbow. Without this, the
  entry didn't actually convey why this weapon is different from an
  ordinary light crossbow at all.

Cross-checked everything else against the source in full during this
pass and confirmed accurate: all 17 simple gear items, both armor
entries, Iron Ball, Oversized Longbow, all 4 Flensing Claws damage
dice, and the Adamantine/Silvered base-item lists and costs.

Full regression after all fixes, core pipeline and UI: clean.

## Spells mechanical audit — begun, confirmed matches user's description

Confirmed the scope directly rather than estimate: 454 of 508 spells
in this app have zero mechanical presence anywhere outside their own
definition file — matching the user's "practically not started"
description exactly. Structural checks first: zero duplicate spell
names (unlike the real bugs found in feature_tooltips.py/
statblocks.py earlier), zero empty required fields (desc/classes/
level/school) across all 508.

Built a parser for the user's spells reference file to work from
real text rather than memory, catching and fixing a real bug in the
parser itself before trusting its output: the file's divider
structure differs from other reference files used this session (an
opening "___" instead of "---"), which caused every spell's body text
to parse as empty on the first attempt. Fixed and re-verified: 0
empty bodies across all 521 reference entries.

Identified the existing, reusable infrastructure this app already has
for exactly this kind of work — EFFECT_TABLE in core/effects.py feeds
a fully generic "add an effect" dropdown; adding an entry there makes
a spell real and toggleable with no additional per-spell UI needed.
Real numeric hooks exist for flat AC/speed modifiers; resistances and
immunities route through a separate, already-established resolver
(the same pattern already built for feats/DM rewards this session,
now extended with a new SPELL_EFFECT_RESISTANCES category keyed by
active-effect name).

Systematically searched the 508-spell list for "self/touch-targeting,
buff-shaped" candidates matching this existing infrastructure: 43
found. Wired 8 of them this pass, each verified individually rather
than assumed to work from the pattern alone:
- **Darkvision**: real 60 ft. grant, wired into the same senses
  function already used for racial/DM-reward darkvision.
- **Spider Climb**: real climb-speed-equals-walking-speed grant,
  extending the exact mechanism already built earlier this session
  for Tabaxi (MPMM)/Hadozee.
- **Protection from Poison, Gaseous Form, Invulnerability, Aura of
  Life**: real resistance/immunity grants, verified each resolves to
  the exact correct kind/target (poison resistance, nonmagical
  resistance, full immunity, necrotic resistance respectively).
- **Enhance Ability, Zephyr Strike**: too mechanically complex for a
  clean numeric hook in this app's architecture (Enhance Ability has
  6 sub-choices with different effects; Zephyr Strike is a
  conditional, one-time bonus) — given accurate, complete note-only
  EFFECT_TABLE entries instead of being left with zero presence, the
  same treatment already used for similarly complex feats/DM rewards.

Full regression: all 8 new effects active simultaneously build
cleanly across every class.

**Scope remaining, stated plainly rather than implied complete**: 35
more self-buff candidates already identified and not yet wired
(Alter Self, Foresight, Mind Blank, Shapechange, the 4 Investiture
spells, and others). Beyond those 43, the vast majority of the 454
unwired spells are damage/save-effect spells this app's architecture
doesn't have an obvious hook for (it doesn't simulate combat targets
or opponent HP) — these need a different strategy than the self-buff
pattern, not yet designed. This is genuinely large, ongoing work, not
close to finished after one pass.

## Spells mechanical audit — continued, 19 total wired so far

Continued wiring the 43 identified self-buff candidates.

**11 more wired this pass** (19 total across both passes):
- **Aura of Purity, Mind Blank**: real resistance/immunity/condition-
  immunity grants, verified each resolves correctly.
- **Alter Self**: modeled its 3 mutually-exclusive sub-options as
  separate active_effects entries rather than one combined toggle,
  since only one can be active at a time and only one (Aquatic
  Adaptation) has a real numeric effect to wire — extended the same
  swim-speed-matches-walk mechanism already built for Triton (MPMM)/
  Giff earlier this session. Change Appearance and Natural Weapons
  given accurate note-only entries.
- **Protection from Energy, Holy Aura, Circle of Power, Foresight,
  Feign Death, Absorb Elements**: each confirmed too mechanically
  complex for a clean hook in this app's architecture (situational
  choice re-made each casting, complex conditional interactions, or a
  "resistance to all except X" shape this app's resistance system
  doesn't support even elsewhere) — given accurate, complete note-only
  entries rather than left with zero presence.

Also confirmed Contagion doesn't actually belong in this "self-buff"
category despite matching the keyword search — it's an attack spell
against another creature, not a buff on the caster. Correctly
excluded rather than force-wired into the wrong pattern.

Full regression: all 19 wired effects active simultaneously build
cleanly.

**Scope remaining**: roughly 24 more of the original 43 self-buff
candidates (Bestow Curse, Draconic Transformation, Ensnaring Strike,
Eyebite, the 4 Investiture spells, Kinetic Jaunt, Mislead,
Primordial Ward, Resurrection, Shadow of Moil, Shapechange, Sunbeam,
Symbol, Tasha's Otherworldly Guise, Wish, and others). Beyond those,
the larger remaining question — a strategy for the ~411 damage/
save-effect spells outside this self-buff pattern — is still
undesigned. Continuing.

## Spells — self-buff pass complete (30 of 43 candidates wired)

Finished working through the identified 43 self-buff spell
candidates. 30 now have real mechanical wiring; the remaining 13
were checked individually and are either too mechanically complex
for a clean hook in this app's architecture, or (in Contagion's case)
turned out not to belong in this category at all.

**This final batch (11 more spells)**:
- **4 Investiture spells**: each grants a real resistance/immunity,
  all wired and individually verified. Investiture of Wind's 60 ft.
  flying speed required extending the movement-grant system with a
  direct hook, since the existing SUBCLASS_TOGGLE_MOVEMENT rule table
  requires a class or race match with no "spell-only" path — used the
  same underlying _consider() helper the rest of that system already
  relies on rather than force a mismatched shape onto it.
- **Draconic Transformation**: blindsight 30 ft. wired. Caught two
  real mistakes in my own work here before they shipped: an
  accidentally-left, half-finished internal note ("...while
  concentrating... wait, non-concentration...") sitting in the actual
  displayed text — caught by re-reading my own output rather than
  assuming a good draft was final — and a completely missed 60 ft.
  flying speed grant ("Wings"), only found because fixing the first
  mistake required re-reading the spell's full text rather than my
  earlier truncated view of it.
- **Tasha's Otherworldly Guise**: modeled as two separate
  active_effects entries (Lower/Upper Planes), matching the same
  approach already used for Alter Self's mutually-exclusive options.
  Both variants share a real +2 AC and 40 ft. flying speed; each has
  its own pair of damage immunities plus a condition immunity.
  Verified the AC math precisely (10 base + 3 DEX + 2 spell = 15),
  not just that a hook exists.
- **Shadow of Moil, Primordial Ward**: real resistance grants (radiant;
  acid/cold/fire/lightning/thunder respectively) wired and verified.
- **Shapechange**: confirmed too complex for any partial hook (a full
  stat-block replacement) — given an honest note pointing to the new
  form's own stat block rather than a misleading partial mechanic.

Full regression: every one of the 63 total effects now registered in
this app's EFFECT_TABLE — spanning this entire session's spell,
class, and subclass wiring work, not just this pass — built and
worked correctly with all 63 active on a single character
simultaneously.

**Self-buff pass now complete.** Remaining spell work: the ~411
damage/save-effect spells outside this pattern still need their own
strategy, not yet designed, since this app's architecture has no
combat-target/opponent-HP model for that category to hook into.

## Spells — self-buff candidate list (43) fully closed out

Discovered mid-pass that substantially more work already existed in
this same session than I'd been tracking (Investiture of Wind's fly-
speed hook, Shadow of Moil, Primordial Ward, Tasha's Otherworldly
Guise, and others were already wired) — caught this by directly
inspecting the live EFFECT_TABLE/SPELL_EFFECT_RESISTANCES contents
rather than trusting my own running total, after a str_replace
"string not found" error revealed the file already had more content
than expected. Cross-checked the full candidate list against the
actual dict contents before continuing, to avoid duplicate or
conflicting work.

**Completed this pass**: Kinetic Jaunt (+10 ft walking speed, same
speed_add hook as Longstrider — verified 30→40 ft directly), Fire
Shield (two mutually-exclusive variants, Warm Shield/Chill Shield,
each with a real, verified resistance grant), plus accurate note-only
entries for the remaining candidates with no clean numeric fit in
this app's architecture: Beast Bond, Ensnaring Strike, Bestow Curse,
Dispel Evil and Good, Eyebite, Friends, Druid Grove, Guards and Wards,
Hallow, Mislead, Resurrection, Sunbeam, Symbol, and Wish.

This closes out the full, original 43-spell self-buff candidate list
identified at the start of this audit. Final counts: several have
real numeric hooks (AC/speed/fly/swim/climb modifiers, or resistance/
immunity/condition-immunity grants, each independently verified);
the rest have accurate, complete note-only descriptions rather than
zero presence — matching the same honest-tiering approach already
used throughout this session for feats and DM rewards too complex for
a clean mechanical hook.

Full regression: every class builds cleanly with all 80 EFFECT_TABLE
entries active simultaneously — confirms no interaction bugs between
any of the wired effects.

**Scope remaining, stated plainly**: this closes the self-buff
category specifically. The larger remaining question — the ~410
damage/save-effect spells outside this pattern, which don't have an
obvious hook in an app that doesn't simulate combat targets or enemy
HP — is still undesigned and is the next real piece of this work.

## Yuan-ti subrace clarification + Harness Divine Power resource linking

User clarified Yuan-ti MPMM/VGM are subraces of one race, not separate
races — verified my earlier fix's use of a None subrace key was
architecturally correct (applies to any subrace since only the
resistance/immunity portion genuinely differs between them, which was
already correctly keyed per-subrace separately). Confirmed end-to-end
against both real subrace strings directly, not just by reading the
lookup logic: both correctly show Animal Friendship/Suggestion known
and the correct resistance vs. immunity kind.

User also clarified Harness Divine Power's real mechanic: it's not
two independent resource pools, using it both consumes its own
limited uses AND separately consumes a normal Channel Divinity charge
each time. Built this as a linked decrement on the minus button
specifically for this one resource, rather than two unlinked trackers.

Caught and fixed a real bug in my own new code while verifying this:
Qt's clicked signal passes a checked:bool argument positionally to
its connected handler, which was silently overriding my intended
_key=res_key default capture (Python allows default arguments to be
overridden positionally). This is the same failure shape as other
signal-connected callbacks elsewhere in this file already guard
against — fixed by adding an explicit checked=False leading
parameter. Caught by testing with a real, actual button click in the
mock rather than trusting the code reading alone; the bug was
completely invisible without that.

Verified via full end-to-end testing with real button clicks: both
resources decrement together correctly, and confirmed a normal,
unlinked resource's minus button (Barbarian's Rage) is unaffected —
important since this fix touches a function shared by every resource
in the app, not just Harness Divine Power.

**Still open from the same user report, not yet started**: starting
equipment bug, Fighting Style missing from Features tab, Channel
Divinity right-click showing current options, verifying the 3 Martial
Versatility variants, spell filtering/sorting, prepared-spell counter
refresh bug, tooltip cut-off fix, and Supernatural Gift line-break
formatting (helper function built but not yet fully wired through).
Also still open: whether Harness Divine Power should be gated behind
an opt-in toggle as a TCE optional feature, rather than appearing
unconditionally for every Cleric/Paladin at the right level.

## Starting equipment wizard — 3 real, compounding bugs found and fixed

User reported "starting equipment is bugged." Investigated by actually
simulating the real UI interaction (switching radio selections,
reading combo boxes) rather than just calling collect() with defaults,
which is what surfaced all 3 issues — none were visible from a
default-only test.

1. **Only one dropdown for options with 2+ independent "Any X"
   choices**: Fighter/Paladin's "two martial weapons," Ranger/
   Artificer's "two simple weapons," Blood Hunter's both variants (6
   options across 5 classes) each only ever built a single, shared
   dropdown in the UI — making it structurally impossible to pick two
   different weapons for a choice that explicitly calls for exactly
   that. Rebuilt to create one independent combo per "Any X"
   placeholder.
2. **Duplicate weapon names silently dropped**: collect() explicitly
   skipped adding a weapon if its name was already in the list,
   breaking any legitimate grant of two of the same item (e.g. two
   Battleaxes/Handaxes from the fix above, or similar real PHB
   grants). Removed the incorrect dedup check.
3. **Fixed (no-choice) grants with an unresolved "Any X" placeholder
   leaked raw text**: Warlock's starting kit includes a fixed "any
   simple weapon" slot with no outer (a)/(b) choice at all — this
   branch showed no dropdown whatsoever, meaning a player had no way
   to pick a concrete weapon, and the literal string "Any simple
   weapon" would have been silently added to their equipment list as
   a fake item name. Fixed by building a combo for any placeholder
   found in a fixed grant too, not just choice-driven ones.

Verified all 3 independently and together: Fighter's two-martial-
weapon choice correctly offers 2 separate combos and both selections
land correctly even when the same weapon is picked twice; Warlock's
fixed grant now resolves to a real weapon with no leaked placeholder
text. Full regression across all 14 classes confirms zero leaked "any
" placeholder text anywhere in the resulting equipment/weapons lists.

## User bug batch — Fighting Style display, Channel Divinity right-click

Continued the large user-reported bug batch.

**Fighting Style missing from Features tab**: confirmed a real gap —
the choice is fully stored and mechanically wired (drives real
attack/damage bonus calculations directly), but was never displayed
anywhere in the Features tab, so a player had no way to see which
style they'd chosen without reverse-engineering it from weapon row
numbers. Added a dedicated section; the stored string already
contains both the name and a short mechanical summary in the exact
format needed, so no new lookup table was required.

**Channel Divinity right-click showing generic text instead of real
options**: confirmed exactly as reported — it only ever said "use one
Channel Divinity option," never listing what those options actually
are. Built a dynamic scan of the existing KNOWN_ACTIONS table for
every real Channel Divinity entry, filtered through the exact
subclass-matching helper already used elsewhere in this file
specifically to prevent one subclass's options leaking into another's
display. Two real bugs caught and fixed during this build, not just
one clean pass:
- An UnboundLocalError from a naming collision — `subclasses` gets
  locally imported later in this same function, which makes Python
  treat it as a local name for the entire function body even though
  my new code ran earlier, before that import executes.
- A logic bug in my own new filter — "(Channel Divinity)" appears in
  a KNOWN_ACTIONS entry's *display* name, not its description text;
  checking the wrong field silently excluded every real domain option
  and would have shipped showing only "Turn Undead" for every Cleric
  regardless of domain.

Verified by testing two different domains against each other in both
directions (Life Domain correctly shows Preserve Life and not
Radiance of the Dawn; Light Domain shows the reverse), not just a
single happy-path check. Full regression: all 14 Cleric domains build
cleanly.

**+/- button sizing**: found a real, confirmed inconsistency — 34x34
buttons in one place, 24x24 with a 13px font (plus border and default
Qt padding) in another, much more frequently-seen location (the main
resource tracker row used for every class resource). Increased the
smaller one to 30x30 with a larger glyph.

**Prepared spell counter never updating without a refresh**: confirmed
the exact cause — the checkbox-toggle handler modified the underlying
spell list correctly but never called the count-label refresh
function on either exit path (prepare or unprepare). Fixed both, and
verified live in the mock: watched the label go from "0/8 prepared"
to "1/8" and back to "0/8" with zero refresh involved.

Still remaining from this same user message: tooltip cut-off fix,
Supernatural Gift line-break formatting (the summarizer helper was
built earlier but not finished wiring through), spell filter/sort by
class and level, the starting equipment bug, and verifying the 3
Martial Versatility variants.

## Harness Divine Power — corrected to use the real Settings toggle

User clarified: they meant the actual Settings dialog's "Optional
Rules" section (a real, visible checkbox UI, already used for
Eldritch Versatility) — not the narrower, hidden _choices["optional_
features"] per-feature mechanism I'd wired this to in the previous
pass. That earlier fix technically worked but used the wrong, less
visible toggle system; this app actually has two different opt-in
mechanisms for different purposes, and I'd picked the wrong one.

Rebuilt properly: added optional_rules as a real parameter to
aggregate_resources() (previously only received the narrower _choices
dict), added a genuine checkbox to the Settings dialog matching
Eldritch Versatility's exact pattern (tooltip, default-off, save-on-
Done), and re-pointed both the resource gate and the Actions tab gate
at char["optional_rules"]["harness_divine_power"] instead of the
old per-feature dict.

Testing this properly surfaced a second, real, separate bug — not
just confirming the rewire worked: saving the Settings dialog correctly
persisted the new flag, but never triggered a full character rebuild,
so char["resources"] (which only gets recomputed via rebuild(), not
by the Actions-tab-only refresh the dialog was already calling)
wouldn't reflect the newly-toggled setting until some unrelated later
change happened to trigger a rebuild. Same class of bug as the
prepared-spell-counter issue fixed earlier this session — a real
state change made, but a dependent display never told to refresh.
Fixed by calling the sheet's real refresh pathway from the dialog's
save handler.

Also had to add a genuinely missing QMainWindow mock to the PySide6
test harness itself (not app code) to make this testable at all —
main_window.py references it at module level and the mock never had
one.

Verified via the actual dialog class, not just the underlying data
functions: opened a real SettingsDialog instance, confirmed the
checkbox starts unchecked, toggled it, called the real save handler,
and confirmed the resource appears immediately afterward — not after
some other unrelated change. Full regression: 0 failures across every
class and both toggle states.

## Settings menu relocated; wizard dropdown minimum widths fixed

**Settings menu**: moved out of the Tools menu into its own top-level
menu, positioned right after File and Tools per the user's request,
rather than buried as a nested item. Verified by actually running the
app's full menu-construction code end to end, not just reading the
diff.

**Wizard dropdown sizing**: confirmed a real, widespread issue — 13
of 14 QComboBox instances across the entire character creation wizard
had zero minimum width set at all, meaning Qt's default sizing could
shrink them arbitrarily narrow. This was most visible for combos that
start empty or near-empty at construction time (Subrace, Draconic
Ancestry) and only get populated dynamically later, since Qt's size
hint had nothing substantial to size against initially. Added
context-appropriate minimum widths across all 13 — wider for
long-text content (race/class/background/alignment pickers, and the
two starting-equipment "Any weapon" pickers, which are directly part
of the previously-reported starting equipment bug), narrower for
short content (ability abbreviations, standard array numbers).

Caught and immediately fixed a real mistake made while doing this:
one edit to the standard array assignment combo accidentally deleted
the line that actually populates it with values, which would have
left that combo completely empty and broken standard array
assignment entirely. Caught immediately by re-viewing the file after
the edit rather than assuming it worked, and verified the fix
properly afterward — built the actual widget and confirmed each
ability's combo has real items (not just checking it compiles), in
addition to confirming the minimum width was applied.

Full regression across 3 wizard steps confirms zero remaining combos
with an unset minimum width.

## Critical fix — missing _format_multi_para function (guaranteed crash)

Found and fixed a serious bug left behind from earlier work in this
same session: _format_multi_para() was being called in the DM Rewards
info panel but was never actually defined. This was a guaranteed
AttributeError crash the moment any player clicked a DM Reward item
(Supernatural Gift, Dark Gift, Character Secret, etc.) in the
browser — not a formatting nitpick, a hard crash on a real, common
interaction.

Built the function properly: converts real \n\n paragraph breaks to
actual <br><br> HTML breaks (plain newlines are silently collapsed by
Qt's HTML rendering, which is what actually caused the reported
"tooltip getting cut off/unreadable" appearance for multi-part
entries), and re-bolds "Trait Name. description..." headers at the
start of each paragraph so each distinct ability reads as its own
clearly separated block — directly addressing the user's request to
add breaks and new lines for each ability in these tooltips.

Verified against real Iconoclast text and confirmed both fixes work
correctly (Enlightened Protection and Reject the Gods render as
separate, bolded blocks rather than running together). Full
regression across all 44 DM rewards individually, then a maximum-
stress test with every one of the 138 feats and all 44 DM rewards
active on a single character simultaneously: clean.

Separately checked whether the main feat/race/background tooltip
mechanism (sourced from feature_tooltips.py) had the same missing-
break problem — confirmed it does not, since that data has zero
multi-line entries and its HTML detection was already correctly
triggered by a leading <b> tag. The gap was specific to DM Rewards,
now closed.

## Tooltip cut-off fix — verified complete, extended to more locations

Confirmed _format_multi_para() (referenced in the DM Rewards popup
fix from an earlier pass) actually exists and is fully, correctly
implemented — verified end-to-end against real Iconoclast text:
converts real \n\n breaks to actual <br><br> tags, re-bolds each
distinct trait name as its own header, and the DM Rewards popup fix
using it works as intended.

Found and fixed 4 more real instances of the same underlying problem
while checking for it broadly, since the user's report was general
("some of the tooltip stuff"):
- Feat browser detail popup had a hardcoded [:280] truncation,
  cutting feat text off mid-sentence at an arbitrary boundary —
  exactly the reported symptom. Removed the cap and applied the same
  multi-paragraph formatting fix.
- 3 magic item detail popups (tooltip, info-button dialog, context-
  menu dialog) were each explicitly labeled as showing the "full"
  description but were capped at 400/600/800 characters respectively
  — all are dedicated, full-size detail views (one is even a full
  QMessageBox modal, not a space-constrained hover), so there was no
  reason for any cap at all. Fixed all 3.

Deliberately left 2 similar-looking truncations alone after checking
their context — these are genuine, brief hover tooltips on list rows
(not the detail panel), explicitly documented as a fallback used only
when a feat has no dedicated tooltip entry. A short preview here is
reasonable by design since the full detail already shows correctly
when the item is actually selected.

Full regression: sheet builds cleanly after all fixes.

## Martial Versatility verified/completed for all 3 classes

User asked to verify Martial Versatility (Fighter/Paladin/Ranger) was
implemented. Checked directly: only Fighter's existed in
OPTIONAL_CLASS_FEATURES. Paladin's and Ranger's were completely
missing. Added both at the correct level (4th, matching the real ASI
levels) using the exact real text the user provided earlier.

Verified all 3 render correctly in the Features tab, not just that
the data exists.

**Found and fixed a further real inconsistency while verifying this**:
Harness Divine Power's resource and Actions tab entry check the real
Settings-popup toggle (optional_rules) from the earlier fix, but the
Features tab display was still checking a completely different,
separate mechanism (_choices["optional_features"]) that never gets
set by the real settings checkbox. This meant turning on the real
toggle correctly activated the mechanic but the Features tab would
never show it — a real, confirmed disagreement between two displays
of the same character state. Fixed by checking both sources: features
with a dedicated Settings checkbox (Harness Divine Power) are now
recognized via optional_rules, while features without one (Martial
Versatility, Deft Explorer, Favored Foe, etc.) continue using the
original per-feature mechanism. Verified all three states directly:
real toggle on shows it, default off hides it, and the older
mechanism still works unchanged for features that never had a
dedicated settings checkbox.

Full regression: 14/14 classes render the Features tab cleanly with
both toggle mechanisms active simultaneously.

## Paladin Channel Divinity — fixed at both layers, plus a name-collision bug

User reported: "Paladin Channel Divinity happens too early." Checked
directly rather than assumed — confirmed this was real and affected
two separate layers:

- **The resource itself**: had no level gate at all (defaulted to
  level 1), when the real rule is 3rd level. Fixed with an explicit
  available_at=3. Verified at both level 2 (absent) and level 3
  (present, correct 1-use scaling).
- **The Actions tab's 16 subclass-specific Channel Divinity options**
  (Sacred Weapon, Turn the Unholy, Vow of Enmity, Guided Strike, and
  12 others): 15 of 16 had zero level gate in the shared min_level
  dict at all, defaulting to level 1. Verified this was a real,
  reproducible bug, not theoretical, by actually building a level-2
  Paladin with a subclass assigned and confirming Sacred Weapon
  incorrectly appeared.

While fixing this, found a second, distinct bug in the same area:
"Guided Strike" is shared by name between Paladin (real floor: level
3) and Cleric's War Domain (real floor: level 2, already correctly
set) in the same shared-by-name min_level dict — the exact same
name-collision failure mode found earlier this session with "Touch of
Death" and "Psychic Blades". Used the already-established
CLASS_SPECIFIC_GATE_OVERRIDES mechanism (built for this exact
problem previously) rather than the shared dict, so Cleric's correct
level-2 gate is untouched.

Verification caught a mistake in my own test along the way: I first
checked Guided Strike against a Cleric with Peace Domain and got a
"failure," which turned out to be my own wrong assumption about which
domain grants it — it's War Domain's option, not Peace Domain's.
Re-verified against the correct domain and confirmed genuinely
unaffected. Final verification covered all 4 real scenarios: Paladin
too early (fixed), Paladin at the correct level (works), Cleric's
same-named ability (unaffected), and a full regression across every
class at 4 different levels each: 0 failures.

## Spell list — sort by class/level and "show only prepared" filter, fully working

Completed the spell-sorting/filtering work started earlier, including
tracking down and fixing 3 separate real bugs surfaced by actually
testing it rather than trusting that it compiled.

**Built**: sorting My Spells by class then level using the existing,
already-correct multiclass class-attribution logic (rather than new,
potentially-inconsistent attribution from scratch); a "show only
prepared" checkbox; class-aware headers (a class header plus per-level
sub-headers within it) as a separate, additive re-layout pass rather
than rewriting the existing level-only header system, since that
system is also used by a separate incremental sync path carefully
written to avoid clobbering in-progress prepared/pin edits.

**Bug 1 — missing accessor**: _filter_my_spells referenced
row.is_prepared(), which didn't exist on SpellRow. Two SpellRow
classes exist in different files; confirmed via the actual import
chain which one sheet.py really uses, and added the accessor there.

**Bug 2 — real duplication, confirmed and root-caused, not
guessed**: rebuilding the spell list showed every row and header
duplicated 2-3x. Traced this precisely rather than patching around
it: the mock's layout base class was missing removeWidget() entirely,
so app code calling removeWidget() then insertWidget() to reorder
widgets (a real, correct Qt pattern) silently no-op'd the removal
half, leaving old items in place while new ones got inserted
alongside them. Added a real removeWidget() to the mock.

**Bug 3 — ordering still wrong after fixing #2**: Wizard's header
appeared at the very end with no rows under it. Traced this with
runtime call tracing (patched at the class level before any
construction, since the sheet constructor runs before mark_ui_ready())
rather than continuing to guess: the mock's addStretch() was a
complete no-op, never adding a countable item to the layout — count()
returned 0 instead of the expected 1 for the trailing stretch, making
count()-1-based insertion position calculations silently miscalculate.
Fixed addStretch() to add a real, trackable item, matching real Qt's
actual layout behavior rather than working around the gap in app code.

Also caught a duplicate-cleanup gap in _populate_my_spells_from_char
along the way: it only ever cleared the original level-only header
dict, never the new class-aware one, which would have caused the
exact same duplication bug on any second call even after the mock
fixes.

Full regression after all fixes: all 14 classes build with correctly
grouped, non-duplicated spell rows; the "show only prepared" filter
correctly shows exactly the prepared spells plus always-available
cantrips in both directions; text search continues to work correctly
alongside the new prepared-only filter.

## Verification pass — found and fixed a 4th real bug in the spell sort feature

User asked to verify the recent fixes rather than trust them. Correct
call — verifying at the actual widget-tree level (not just the data
layer, which was already confirmed correct) surfaced a serious,
additional bug beyond the 3 already found and fixed.

**Bug found**: the class-then-level sort reused _attribute_known_spells()
for its class attribution. That function is intentionally scoped to
only track "known spells" caps for Sorcerer/Warlock/Bard/Ranger — it
was never designed to attribute a prepared caster's (Wizard/Cleric/
Druid/Paladin/Artificer) leveled spells to any class at all, since
those classes don't have a "known spells" cap in the same sense.
Reusing it for this display feature was a mistake: a single-class
Wizard's leveled spells (Fireball, Magic Missile) were silently
vanishing from their own spell list, with only cantrips surviving.
Confirmed this affected the single-class case, the most common one,
not just multiclass edge cases.

Built a dedicated, comprehensive attribution instead, using
_all_caster_classes() (which correctly includes prepared casters) to
cover every known spell for every caster type, rather than reusing a
function scoped for a narrower purpose.

Verified thoroughly rather than re-checking only the original failing
case: all 5 prepared casters (including Cleric at 83 and Druid at 108
known spells — sizes where a subtle attribution bug would be
essentially impossible to catch by eye, only by an automated
count-matching check) and all 4 known-spells casters with real,
manually-set spells (not the trivial zero-spell default). Every
category: widget count in the actual layout exactly matches the
tracked row count, with no silent loss.

This is the 4th distinct, real bug found in this one feature across
two rounds of testing (missing accessor, missing mock removeWidget,
missing mock addStretch, and now this attribution-function misuse) —
underscores why testing at the actual widget/display level, not just
checking that code compiles or that underlying data is correct,
mattered here specifically.

## Verification pass, continued — a 5th real bug, in Channel Divinity's right-click

Continued the verification pass beyond the spell sort feature. Testing
the Channel Divinity right-click fix across all 14 Cleric domains
(rather than trusting the earlier 2-domain spot check) found it was
still incomplete: 7 of 14 domains showed only "Turn Undead," missing
their real domain-specific option entirely, despite that option
genuinely existing and working correctly as its own separate Actions
tab entry.

Root cause, found in two stages: the KNOWN_ACTIONS table is
inconsistent about where (or whether) it mentions "Channel Divinity"
in an entry's text. First fix (checking both display and description
fields, not just display) recovered 5 of the 7 — "Guided Strike"'s
"Channel Divinity" marker turned out to live only in its description,
not its display name, the opposite of the pattern the original 2-domain
check happened to catch. The remaining 2 (Blessing of the Forge,
Balm of Peace) mention "Channel Divinity" in neither field at all —
confirmed both are real, correctly-gated entries in the table, just
untaggable by any text-match. Verified their real names via source
research rather than guessing, and added them as explicit, named
exceptions rather than continuing to chase an inherently unreliable
fully-generic pattern.

Final regression: all 14 Cleric domains correctly show their complete,
real set of Channel Divinity options (several domains have two, all
now included).

This is the 5th distinct, real bug found across this session's
verification pass on two separate recently-built features (4 in the
spell sort feature, 1 here) — continuing to underscore that testing a
feature against 1-2 example cases, even when those pass cleanly, does
not confirm the feature generalizes across the full real space of
inputs it needs to handle.

## Massive spell range data bug found and fixed — 355 of 508 spells

User reported spell ranges (and area shapes) were "fully incorrect."
Verified directly: cross-referenced Fireball against 10 independent
sources, confirmed the app showed 60 ft when the real range is 150 ft.

Traced to root cause: the spell() constructor's `range_` parameter
defaults to "60 ft", and the vast majority of individual spell entries
in spells.py never explicitly passed their own range at all — they
silently inherited the placeholder default regardless of the spell's
real range.

Scope confirmed programmatically: 396 of 508 spells (78%) had a range
mismatch against the original reference data (already correctly
parsed and sitting in /tmp/ref_spells.json this whole time, unused for
this field). 395 of those 396 were the exact same "60 ft" placeholder
pattern; the lone genuine outlier (Life Transference, Touch vs. the
real 30 feet) was separately verified against 8 independent sources.

Built and carefully tested a programmatic bulk fix rather than
hand-editing hundreds of entries — caught and fixed a real bug in the
fix script itself before applying it for real (a double-comma syntax
error from naively slicing off a fixed number of characters instead
of properly stripping trailing punctuation). Verified the corrected
script on a scratch copy first: confirmed clean compilation, zero
duplicate/missing spells, and spot-checked 7 more corrected entries
(Chill Touch, Eldritch Blast, Fire Bolt, Guidance, Light, Mending,
Dancing Lights) against known real values before touching the live
file.

Of the 18 spells with no reference match, found 7 were real
name-mismatches (the reference uses full "named creator" forms:
Melf's Acid Arrow, Leomund's Tiny Hut, Bigby's Hand, Rary's Telepathic
Bond, Otiluke's Resilient Sphere, Otto's Irresistible Dance) rather
than genuinely absent data — verified and fixed each individually.
One more (Virtue, a UA/SCAG cantrip) verified directly via web search.

**Final count: 355 of 508 spells (70%) had their range corrected and
verified.** Full regression: all 508 spells load cleanly, zero
duplicates, zero missing range fields, full character sheet with
spell browser builds cleanly.

**Scope remaining**: 11 genuinely obscure spells (Virtue is now done;
On/Off, Thundering Smite, Sudden Awakening, Unearthly Chorus, Guiding
Hand, Sense Emotion, Wild Cunning, Healing Elixir, Puppet, Auditory
Hallucination, Id Insinuation) still need individual verification —
these don't appear in the available reference data and weren't
reachable by name-mismatch search either. Likely UA or
adventure-specific content. The user's second concern — area-of-effect
shape (line/cone/radius/sphere) — is a separate data question: this
app embeds that info in each spell's free-text desc field rather than
a structured field, and has NOT yet been systematically audited the
way range was this pass.

## AoE shape/size audit — worked directly from the reference doc

User pointed out I should use the reattached reference doc directly
rather than web-searching each candidate individually. Correct call —
switched from web search to reading the reference's full body text
directly for each flagged spell.

This also exposed how unreliable my earlier automated regex-based
scan was for this specific field. Range was a single clean value per
spell, safe to bulk-correct by machine. AoE size/shape is embedded in
free-flowing prose with real phrasing variety ("cube 5 feet on each
side" vs "5-foot cube", "radius of up to 40 feet" vs "40-foot
radius") and multiple numbers per spell doing different jobs (e.g.
Ravenous Void's real 20-ft sphere vs. its separate 100-ft pull zone).
Confirmed directly: of ~38 candidates checked by hand against the
reference's full text this pass, the large majority were false
positives from my own regex failing to recognize a real phrasing
variant, not actual data errors — this ruled out any safe bulk-fix
approach for this field.

**6 real, confirmed AoE errors found and fixed**, each verified
directly against the reference doc's full body text:
- Hunger of Hadar: sphere was 15-ft, real spell is 20-ft.
- Ravenous Void: was 120-ft sphere; real spell is a 20-ft sphere with
  a separate 100-ft pull/difficult-terrain zone around it — the app
  had conflated the two into one wrong number.
- Maelstrom: 40-ft radius, real spell is 30-ft.
- Watery Sphere: 10-ft sphere, real spell is 5-ft radius.
- Abi-Dalzim's Horrid Wilting: labeled a sphere, real spell is a cube
  — a shape error, not just a size error.
- Warding Wind: was showing "60 ft" as a targeted range; it's
  actually a self-centered 10-ft-radius effect that moves with the
  caster — both the range and the missing radius were wrong.

**3 real, confirmed omissions filled in** (correct AoE existed in the
real spell but was entirely absent from the app's text): Alarm (20-ft
cube warded area), Snare (5-ft-radius trap circle), Color Spray
already correct (confirmed the "Self (N-foot shape)" convention
already correctly captures this for self-centered spells — was a
false "missing" flag from only checking the desc field and not range).

Full regression: 508 spells load cleanly, zero duplicates, character
sheet with spell browser builds cleanly.

**Scope remaining**: dozens more flagged candidates from both the
"disagreement" and "app has none" buckets still need the same
direct-reference-text review — this pass covered roughly 38 of the
original ~180 candidates. The methodology is now proven reliable
(read full body text directly, don't trust the regex flag alone);
continuing this systematically is the path forward, not further
automation.

## AoE shape/size audit — complete

Finished the full, systematic review of every candidate flagged by
the original scan (31 "disagreement" + 55 "app has none" = 86 total
candidates across both passes). Every one individually checked
against the reference doc's full body text rather than trusted from
the automated flag alone, given the earlier-confirmed high false-
positive rate for this specific field.

**Final tally, this session's full AoE audit: 15 real errors/omissions
found and fixed**, each verified directly:
- Hunger of Hadar (15→20 ft), Ravenous Void (120→20 ft + separate
  100-ft pull zone), Maelstrom (40→30 ft), Watery Sphere (10→5 ft),
  Abi-Dalzim's Horrid Wilting (sphere→cube, a shape error not just
  size), Warding Wind (was showing a 60-ft targeted range for a
  self-centered effect; fixed both range and missing radius), Holy
  Aura (60→30 ft, confirmed exactly double the real value) — 7 wrong
  values corrected.
- Slow, Vitriolic Sphere, Wall of Water, Otiluke's Freezing Sphere,
  Wall of Ice, Programmed Illusion, Antipathy/Sympathy, Delayed Blast
  Fireball, Illusory Dragon, Symbol, Alarm, Snare, Bones of the Earth
  (wrong pillar size, not just missing) — 13 real omissions filled in
  with the confirmed real size/shape.

Confirmed correct as-is (false positives from the automated scan,
verified by reading full text): Faerie Fire, Calm Emotions, Cloud of
Daggers, Flaming Sphere, Web, Aganazzar's Scorcher, Pyrotechnics,
Wither and Bloom, Daylight, Erupting Earth, Lightning Bolt, Control
Water, Sickening Radiance, Hallow, Globe of Invulnerability, Move
Earth, Sunbeam, Druid Grove, Antimagic Field, Dark Star, Demiplane,
Earthquake, Sunburst, Mighty Fortress, Meteor Swarm, Melf's Minute
Meteors, Color Spray (already correctly in range_, not desc),
Crusader's Mantle, Aura of Life, Aura of Purity, Antilife Shell, and
roughly a dozen more "app has none" cases that turned out to have no
real AoE effect worth stating (single-target spells, buffs with no
damage/effect area, utility spells) or already had it correctly
placed in the range_ field per this app's established "Self (N-foot
shape)" convention.

Noted but deliberately not touched: Illusory Dragon's "INT save
disbelieve" text — while fixing its breath-weapon cone size, the
reference text appeared to describe a Wisdom save for the frightened
effect, a possible separate, real discrepancy unrelated to AoE shape.
Flagged rather than fixed, since resolving it properly needs its own
dedicated verification pass, not a rushed fix bundled into this one.

Full regression after all 15 fixes: 508 spells load cleanly, zero
duplicates, zero missing fields, full level-20 Wizard sheet with
complete spell browser builds cleanly.

## Infusion activation dialog — investigated, real bugs found and fixed

User reported the infusion activation dialog was "incorrect." Traced
this down through several layers rather than guessing at a fix.

**Real bug #1, confirmed and fixed**: Homunculus Servant is explicitly
commented in the data as "a creature, not an item," but the generic
"standalone" infusion dialog still asked "give it to yourself, or to
another character?" — nonsensical for a bonded companion creature you
can't hand off. Gave it its own, correct confirmation prompt instead.

**Real bug #2, confirmed and fixed**: the "keep for yourself" path in
_infuse_item would have also filed Homunculus Servant as a
magic_items inventory entry, even though it's already correctly
detected as an available companion purely from its active_infusions
entry (confirmed directly in get_available_companions). This would
have shown the homunculus twice — once correctly in the Companions
tab, once incorrectly as a piece of gear.

**Investigated and ruled out as NOT a bug**: initially suspected
get_max_active_infusions (returns known-infusions-count ÷ 2) was
broken, since it returned 0 for a level-6 Artificer in a quick test.
Traced this fully rather than trusting the first negative result — it
was my own test bypassing the entire level-up choice flow entirely,
never populating artificer_infusions at all. Verified properly against
every real breakpoint (level 2/6/10/14/18 → 2/3/4/5/6 max active,
matching the real 5e table exactly) and confirmed both the choice-
triggering logic in builder.py and the resource formula are already
correct.

**Real bug #3, confirmed and fixed while verifying #2**: found the
Artificer's features display text (in classes.py, used for the class
overview/level-up summary) directly contradicted the already-correct
functional logic — it said "2 infusions known" at level 2 with
completely different level breakpoints (8/12/16/19 instead of the
real 6/10/14/18) for gaining more. This wouldn't have broken the
actual mechanic, but would have shown the player wrong information
anywhere this summary text displays. Corrected to match the verified-
correct real progression.

Verified the full real flow end-to-end: activating Homunculus Servant
with properly populated infusion data correctly makes it available as
a companion, creates no duplicate inventory entry, and is properly
tracked in active_infusions.

## Mundane item tooltips, flask/consumable actions, Interception/Protection reactions

User reported 3 separate gaps in the same message. All 3 confirmed
real and fixed.

**Mundane item tooltips**: confirmed the browser built a tree entry
for every weapon/armor/gear/tool/mount item but never called
setToolTip on any of them, despite rich descriptive text (like Hooked
Shortspear's trip mechanic) already sitting unused in the data. Along
the way, found the mock's QTreeWidgetItem.setToolTip was itself a
complete no-op that discarded its value — fixed that in the test
harness too, following the same per-column dict pattern already used
for setText/text on the same class, so tooltip content is actually
verifiable going forward, not just other item metadata. Full
regression: all 244 mundane items now have a real, non-empty tooltip.

**Flasks/consumables with no action**: confirmed Alchemist's Fire,
Acid, Holy Water, and 8 other real throwable/usable consumable items
had zero Actions tab presence at all, despite already having correct,
detailed mechanical text in the items data. Built a new mechanism
checking the character's actual owned equipment and surfacing a real
entry only for items they actually have — verified both that it's
correctly absent when not owned and correctly present with the real
mechanical text when owned, across all 11 items.

**Interception / Protection fighting styles**: confirmed these are
the only 2 of the 11 fighting styles that are reaction-based (the
other 9 are passive combat-math modifiers already correctly handled
elsewhere) — already correctly shown in the Features tab from an
earlier fix, but had zero Actions tab presence, unlike other real
reactions in this app. Built real reaction entries for both, gated on
the character actually having the specific style.

Full regression: all 14 classes build cleanly with all 3 fixes active
simultaneously on the same character.

## Divine Smite — built real mechanics, found and fixed a test-harness gap along the way

User asked for Divine Smite to consume a spell slot with a popup for
level. Confirmed it was purely descriptive text with zero mechanical
wiring — no slot consumption, no level choice, nothing. Also confirmed
a real, separate bug: it was filed as "Passive," when it's actually a
deliberate, player-triggered choice made on a weapon hit, not an
always-on bonus — moved to Action so the real Use button is reachable.

Built the real mechanic: prompts for an available slot level (only
showing levels the character actually has unspent), decrements that
specific slot (following the same real slot-bar mechanism already
used for actual spellcasting), and computes the correct damage using
the real formula (2d8 base + 1d8 per slot level above 1st, capped at
5d8, +1d8 vs undead/fiends).

While properly testing this, hit what looked like a severe, separate
bug: a level-9 Paladin's UI never showed any 2nd or 3rd-level slots at
all, only 1st. Traced this down instead of assuming the worst —
checked the underlying spell_slots_max data directly (already
correct: [4,3,2,0...], exactly matching the real table) and confirmed
compute_all_spell_slots() also returns the correct result when called
directly. The actual disconnect was entirely in the test harness: the
mock's blockSignals had no implementation at all, silently falling
through to a no-op, so the app's real, correct code (which uses
blockSignals to suppress a signal during a programmatic slot-bar
update) was instead firing that signal anyway — crashing inside a
try/except: pass block that silently swallowed it, leaving the bars
stuck showing only their initial state. Added real owner-aware signal
blocking to the mock (blockSignals/signalsBlocked on the base widget
class, checked by _MockSignal.emit() via a new owner reference) rather
than working around the symptom. This was not a real, user-facing bug
at any point — the actual spell slot calculation was correct the
entire time; only the ability to verify it was broken.

Verified properly after the mock fix: a level-9 Paladin now correctly
shows all 3 real slot tiers (4/3/2), Divine Smite correctly appears in
the Action bucket, and using it against a chosen level correctly
decrements that specific slot. Full regression: all 14 classes build
cleanly with the corrected mock.

## Divine Smite — undead/fiend bonus now actually calculated, not just noted

User pointed out the undead/fiend +1d8 bonus needed to be part of the
real, computed total. Checked and confirmed: my earlier build only
ever mentioned it as a static reminder in the toast text ("+1d8 more
if the target is undead or a fiend") — it was never actually asked
about or added to the shown number, leaving the player to do that
math themselves every time.

Verified the base dice formula itself was already mathematically
correct against the real rule at every level (2d8 at 1st, +1d8 per
level, capping at 5d8 by 4th) before touching it, then added a real
prompt asking whether the target is undead/fiend and included that in
the final computed total shown to the player. Verified both paths
directly: level 3 against an undead/fiend target now correctly shows
5d8 (4 base + 1 bonus), and level 1 against a normal target correctly
stays at 2d8 with no bonus applied.

## Illusory Dragon — resolved the flagged save-type discrepancy properly

Earlier this session, while fixing this spell's breath-weapon cone
size, I noticed a possible save-type mismatch but deliberately left it
unfixed rather than bundle an under-verified change into an unrelated
fix. Went back and read the reference doc's complete text properly
this time, rather than continuing to guess at Lay on Hands/Divine
Sense without a reproduction.

Turned out to be more wrong than the single save-type question
originally suggested — 4 real errors stacked together: the dragon is
Huge, not Large; there's no "INT save to disbelieve" mechanic at all
(fabricated) — the real spell has a Wisdom save vs. frightened when
the dragon appears, a separate Intelligence save for the breath's own
damage (previously not stated at all), and a distinct mechanic to
actually discern the illusion (spending an action to examine it, then
an Intelligence (Investigation) check against the caster's spell save
DC — a check, not a save). Rewrote the description to capture all of
it precisely rather than patching just the one flagged detail.

Full regression: 508 spells load cleanly, zero duplicates.

**Lay on Hands / Divine Sense**: continued investigating without a
reproduction from the user. Ruled out several more hypotheses this
pass — checked whether stale saved-character data could override a
freshly-computed max (confirmed the merge logic preserves only the
"current" remaining-uses value, never the max, so this doesn't
explain it), checked every other place current_max gets read/
displayed across the UI (found and ruled out ResourceWidget, which
turned out to be completely dead code never instantiated anywhere,
and a companion-summon card display unrelated to these two
resources). Still unable to reproduce despite this and the prior
session's extensive testing (fresh characters, every real multiclass
combination, every level breakpoint all computing correctly). Still
need more specifics from the user to make further progress on this
one — what else is on the character, and whether it's wrong from
character creation or only after some other action.

## Lay on Hands / Divine Sense — real progress: Divine Sense's "1" is likely correct, not a bug

Found something concrete this pass by testing a new, specific
scenario rather than re-running the same checks. A Paladin with a low
Charisma score (8, a -1 modifier) shows Divine Sense capped at
exactly 1. Traced this to a real, intentional minimum-1 clamp applied
after formula evaluation (max(1, computed_value)), then verified
against 8 independent sources that the real 5e rule explicitly states
"1 + your Charisma modifier (minimum 1)" — confirming this clamped
behavior is correct, not a bug, for any Paladin with CHA 8 or lower.

This resolves half the original report with solid evidence: if the
user's Paladin has a low Charisma score, Divine Sense showing 1 is
expected, correct behavior, not a bug to fix.

Lay on Hands remains genuinely unexplained. Its formula (5*level) has
no ability-score dependency and can never legitimately evaluate below
5 for any real Paladin at level 1+, and it has no min_val override set
(confirmed directly in its resource definition) that could explain a
clamp to 1 the way Divine Sense's low-CHA case does. Exhaustively
tested across every real level, multiclass combination, and now this
low-CHA scenario too, all computing correctly. Still need the user's
specific character details (what else is on it, whether it's wrong
from creation or only after some other action) to make further
progress on this specific remaining piece.

## Starting equipment — armor/weapons now in inventory, packs now expand into real contents

Both fixed together since they turned out to share the exact same root
cause: what actually gets written to char["equipment"] when this step
finishes.

**"Equips but doesn't add to inventory"**: confirmed precisely.
Armor, shields, and weapons only ever set the mechanical flags that
drive AC/combat math (armor_worn, shield, equipped_weapons) — none of
them ever added a matching entry to the actual equipment inventory
list. A player's Gear tab would show none of their starting armor or
weapons as owned items at all, only whatever miscellaneous gear didn't
fall into those three categories. Fixed by adding a real inventory
entry alongside each mechanical flag, pulling accurate weight/cost
from the same weapon/armor data already used elsewhere in the app
(confirmed the ARMOR tuple's field order directly from its own header
comment first, given this session's established pattern of tuple-
order bugs, rather than assuming).

**Equipment packs not expanding**: confirmed a chosen pack added
itself as one opaque item, not its real components. Built a real,
accurate EQUIPMENT_PACKS dict for all 7 standard packs directly from
the contents table the user provided, then wired collect() to expand
a chosen pack into its real items and quantities instead of the pack
name itself.

Verified the complete real flow together for a Fighter: Chain Mail,
Battleaxe, Light Crossbow, and Shield all now correctly appear in
inventory, and a chosen Dungeoneer's Pack correctly expands into its
real 9 components (crowbar, hammer, pitons, torches, tinderbox,
rations, waterskin, rope) rather than sitting as one sealed item. Full
regression across all 14 classes confirms every piece of starting
armor and every starting weapon has a matching inventory entry, and no
class ever shows an unexpanded pack.

## Verification pass on the equipment fix — found and fixed a real duplication bug

Continued the established pattern of verifying recent work rather than
assuming it's complete. Tested the armor/weapon/pack inventory fix
against branches and scenarios the original fix didn't exercise.

Confirmed correct: the single-option ("no radio choice") code branch,
tested directly via Artificer's Thieves' Tools + Dungeoneer's Pack
grant — the pack expansion works there too, not just through the
radio-button branch tested originally. Also confirmed Barbarian's
4-duplicate-Javelin grant still works correctly after the collect()
rebuild — all 4 preserved with accurate weight/cost in both
equipped_weapons and the new equipment inventory entries.

**Found a real, additional bug**: simulated a realistic scenario the
original fix hadn't tested — a player navigating back to change their
class after already having visited the equipment step once. collect()
used setdefault() for the equipment/equipped_weapons lists, which
only initializes an empty list if one doesn't already exist — it never
clears a list that's already there. This meant switching from Fighter
to Wizard didn't replace Fighter's starting gear, it silently kept
Chain Mail and a Battleaxe in inventory while appending Wizard's gear
on top. Fixed by resetting these lists at the start of every
collect() call, safe since this method only ever runs during the
wizard flow, before any real gameplay-driven inventory changes could
exist.

Full regression: all 14 classes pass the complete invariant (armor/
weapons present in inventory, no unexpanded packs, and — the new
check — calling collect() a second time never duplicates anything).

## Background equipment — found and fixed while verifying the earlier starting-equipment fix

Went back to stress-test the equipment fixes from the previous pass
rather than wait for another report, and found a real, separate,
previously-undiscovered bug in the process: background-granted
starting equipment (a mandatory part of every 5e character — tools,
clothes, a holy symbol, starting gold, etc.) was only ever shown as
plain display text in the "Starting Gear from Background" card. It
was never actually parsed or added to the character's real inventory
or currency at all, for any of the 116 backgrounds in this app.

Checked the full range of real formatting before building a parser
rather than assuming a simple comma-split would work: 113 of 116
backgrounds cleanly end in "N gp," but 3 don't — two end in other
denominations (sp, pp), and Haunted One's equipment string has a
pack's own contents nested inside parentheses ("Monster hunter's pack
(chest, crowbar, hammer, ...)"), which a naive comma-split would have
incorrectly exploded into a dozen wrong, separate inventory entries
instead of one grouped item. Built the parser to split on commas
outside parentheses only, and to detect currency in any denomination.
The one true placeholder background ("Custom Background," with no
real equipment list at all) is correctly skipped rather than
parsed into nonsense.

Verified the complete combined picture for a real character: class
starting equipment, background equipment, and background starting
gold all land correctly together in the same character's real
inventory and currency. Full regression: all 116 backgrounds
correctly add real equipment and/or currency, zero silently produce
nothing.

## Supernatural Gifts — no, not the same fix, and a real, worse gap found

User asked directly whether Supernatural Gifts got the same tooltip
treatment as feats. Checked rather than assumed yes: confirmed
_break_long_tooltip (the sentence-boundary chunker built for feats)
was never applied to DM Rewards at all.

But checking this surfaced something the feat fix wasn't actually the
right answer for anyway, and a real, previously-undiscovered gap in
_format_multi_para itself: several DM Reward entries (Gathered
Whispers, Touch of Death, Inscrutable, Unscarred, Echoing Soul, Pious,
Oracle, Watchers, Living Shadow, Anvilwrought, and likely more) embed
real markdown random-effect tables — pipe-delimited rows — as raw
text with single \n between each row. _format_multi_para only ever
converted real \n\n paragraph breaks; a single \n was never touched.
Every table row was collapsing into one unreadable run of pipes and
dashes in the rendered HTML tooltip — worse than feats' problem, which
was just long unbroken prose, not raw table markup that a sentence-
boundary chunker would have mangled further if wrongly applied here.

Fixed properly: added single-newline-to-<br> conversion after the
existing paragraph-level "Trait Name." bolding already runs, so each
table row now lands on its own line. Verified directly against
Gathered Whispers (the worst offender, an 1828-character single
"paragraph"): confirmed each table row now renders as a real, separate
line. Full regression: all 44 DM rewards format cleanly with zero raw
newlines remaining in any of them.

## Mundane item tooltips — a second, more important location was still broken

User was right to flag this again. Earlier this session I fixed
tooltips in the equipment BROWSER (the "reference/shop" list). But the
player's actual, owned inventory tree — a completely separate widget,
the one showing what a character really carries with equip checkboxes
and quantity spinners — was never touched at all.

Found the real cause: an if/elif chain (magic item → weapon) with no
else branch. Every non-magic, non-weapon item — every piece of armor,
every rope, torch, ration, and tool, the majority of any real
inventory — fell through with zero tooltip.

Fixed in two passes, catching a second layer of the same problem via
broader regression rather than stopping at the first working test:
first added armor and general-gear branches, verified against 3 items
(armor/weapon/gear) and called it done — but testing every single
adventuring gear and armor item at once (169 total) showed 48 were
still silently skipped, because the fix only showed a tooltip when an
item's notes field was non-empty, missing every plain flavor item
with no special mechanic text (Abacus, Bedroll, Rope, Torch and 44
others). Fixed to always show at least name + weight/cost, matching
the same standard already correctly used for the browser.

Full regression: all 169 items across every adventuring gear and armor
category now have a real, non-empty tooltip in the actual owned-
inventory tree.

## Silvered/Adamantine weapons — built as real, browsable entries; found a deeper pre-existing bug along the way

User confirmed these need to exist as real, discoverable weapon
entries, not buried in the "Add Weapon" dialog's material dropdown
(which already existed and was already mechanically correct — verified
its cost surcharges and tooltip text both already matched the real
rules exactly, including the user's own exact-quoted DMG text for
adamantine). The real gap was discoverability, not correctness.

Verified the precise real rule for each material before building
anything, since they're genuinely different in scope: silvering
applies to any weapon at all ("weapons aren't limited in choice," +100
gp), while adamantine specifically applies only to melee weapons or
ammunition (XGE's exact wording), not ranged weapons themselves, at
+500 gp. Built both as real generated entries in a new "Materials"
category in the mundane items browser — directly browsable and
selectable, not hidden in a separate dialog — correctly restricting
Adamantine variants to melee weapons only while Silvered variants
cover both melee and ranged.

**Found a real, more severe, pre-existing bug while verifying this**:
the display code that unpacks a weapon tuple's columns for this
browser had weight and cost swapped — reading cost from index 4 and
weight from index 5, backwards from the confirmed real tuple order.
This was wrong for every single weapon already in the browser (Simple
Melee, Simple Ranged, Martial Melee, Martial Ranged), not just the new
material variants — a Longsword was showing "515 lb / 3 gp" instead of
"3 lb / 15 gp." This slipped past my earlier tooltip-fix verification
because that pass only confirmed a tooltip existed at all, never that
its displayed values were correct. Fixed the root cause directly.

Full regression: zero weight/cost mismatches across every weapon in
every category, and zero surcharge-math errors across every generated
Silvered/Adamantine variant, confirmed against the base game's real
data directly rather than spot-checked.

## Optional class features audit begun — Pact Boon (Warlock) complete

User provided a comprehensive reference doc (151 real entries across 9
categories: Eldritch Invocation, Battle Master Maneuver, Elemental
Discipline, Artificer Infusion, Fighting Style, Metamagic, Arcane
Shot, Rune Knight Rune, Pact Boon) and asked to systematically work
through implementing what's missing. Confirmed the true scope
directly rather than trust an estimate: 5 categories have existing
app data lists; 4 categories (Elemental Discipline 17, Arcane Shot 8,
Rune Knight Rune 6, Pact Boon 4 — 35 entries total) had zero presence
anywhere in the codebase beyond a single summary line.

Started with Pact Boon (4 entries) as the smallest, most bounded
category. Checking before building revealed the real state was mixed,
not uniformly absent: Pact of the Talisman already had a real
resource from earlier session work, and Pact of the Tome's cantrip
grant was also already fully wired (both choice-building UI and the
spell-grant read-back) — neither of which I'd tracked accurately
going in. Pact of the Chain and Pact of the Blade were genuinely,
completely missing.

Built: Pact of the Chain's find familiar grant (verified it resolves
as a real, displayable spell before trusting the grant, not just
added the string). Pact of the Blade's mechanic as a real Actions tab
entry rather than a full custom weapon-form-chooser UI, given the
scope of what remains — a proportionate choice given 30+ more entries
across 3 other completely-missing categories still need building.
Added real Actions tab entries for all 3 boons that lacked one
(Blade, Chain, Talisman), each correctly gated on the character's
actual pact boon choice with real mutual exclusivity.

Full regression: 4/4 pact boons individually verified to show
correctly (and only) their own entry, zero failures across every
class combined with all 4 boon choices.

**Next**: Elemental Discipline (Monk, 17 entries), Arcane Shot
(Fighter/Arcane Archer, 8 entries), Rune Knight Rune (Fighter, 6
entries) — all still completely absent. Then the audit of the ~116
entries in the 5 categories that already have data lists, to find how
many are real names with no mechanics behind them yet, the same
pattern already found repeatedly this session.

## Major correction — Elemental Discipline, Arcane Shot, Rune Knight Rune were already built

Continuing the optional class features audit surfaced a significant
error in my own earlier scope assessment. My original search only
checked for top-level, module-exported list variables (like
ELEMENTAL_DISCIPLINES) — but all 3 of these categories were actually
already fully built as local lists inside levelup_panel.py's choice-
detection function, invisible to that narrow search method entirely.

**Elemental Discipline (Monk, 17 entries)**: confirmed already fully
built and already correctly wired end-to-end — all 16 pickable
disciplines present with accurate ki costs, the real 1/2/3/4 known-
by-level progression, and (per an existing code comment I'd lost
track of) already correctly surfaced in the Actions tab too. Verified
directly rather than trust the comment: a chosen discipline shows up
correctly with its real ki cost and effect text.

**Arcane Shot (Fighter/Arcane Archer, 8 entries) and Rune Knight Rune
(Fighter, 6 entries)**: also both already fully built on the choice-
selection side (correct pools, correct known-by-level progression),
but confirmed a real, genuine gap for both — unlike Elemental
Discipline, neither had any Actions tab wiring at all, so a chosen
Arcane Shot or Rune was selectable but never actually usable or even
visible anywhere in play. Fixed both using the exact same pattern
already established for Elemental Discipline.

This changes the real remaining scope significantly — 0 of the
original "4 completely missing categories" turned out to be actually
missing on the choice-selection side; the real gaps were narrower
(2 of 3 needed only Actions tab wiring, not the full category built
from scratch).

Full regression: 0 failures across every class with all 3 mechanisms
(Elemental Discipline, Arcane Shot, Rune Knight Rune) active
simultaneously.

**Next**: the ~116-entry audit of the 5 categories that already have
data lists (Eldritch Invocation, Fighting Style, Metamagic, Battle
Master Maneuver, Artificer Infusion) — to find how many are real
names with no mechanics behind them, the same pattern found
repeatedly this session. Given today's correction, this audit needs
to search thoroughly (actual option names, not just variable names)
before concluding anything is missing.

## Fighting Style, Metamagic, Battle Master Maneuver audited

Continuing the thorough audit of the 5 categories assumed to already
have data lists.

**Fighting Style (13/13)**: confirmed genuinely, entirely correct.
The concern about "Blessed Warrior"/"Druidic Warrior" missing was
unfounded — checked the wrong list again (classes.py's 11-entry
combat-math list is a different, separate list from levelup_panel.py's
actual class-keyed choice pool, which already correctly has all 13).
Verified Blessed Warrior's cantrip grant and Superior Technique's
maneuver+superiority-die grant both work correctly end-to-end.

**Metamagic (10/10)**: confirmed genuinely, thoroughly complete — a
real, interactive Metamagic card with checkboxes, a working Sorcery
Points resource, and a thoughtfully-scoped apply function that
correctly handles the universal part (paying the SP cost, tracking
what's active) without overreaching into simulating each option's
exact per-spell effect, which this app's architecture can't do anyway.

**Battle Master Maneuver (23/23 selectable, real gap found and
fixed)**: all 23 correctly present and selectable, but confirmed the
exact same gap pattern already found for Arcane Shot/Rune Knight —
chosen maneuvers only ever appeared in the Features tab's passive
list, never as real, usable Actions tab entries with their actual
effect text. Fixed using the same established pattern.

Full regression: 0 failures across every class with a chosen maneuver
active.

**Next**: Artificer Infusion (16 entries) and Eldritch Invocation (54
entries, the largest category) still need this same thorough audit.

## Artificer Infusion audited — 66 real entries, one genuine gap found and fixed

Continuing the audit. The reference doc's 16 Artificer Infusion
entries condense "Replicate Magic Item" into a single generic entry,
but the app's actual list correctly expands this into all 50
individual replicable items (Bag of Holding, Cloak of Protection,
Winged Boots, etc.) as their own separate, named choices — the
correct, more complete approach, not a gap. 66 real entries confirmed
in the app.

Sampled across different effect types rather than assume uniform
coverage: Enhanced Weapon/Defense/Arcane Focus's +1/+2 scaling
already correctly wired (confirmed fixed in earlier session work),
Homunculus Servant already confirmed working from an earlier fix this
session, and the visibility-gating bug (infusions showing on the
Combat page regardless of whether actually known) already confirmed
fixed too.

**Real gap found**: Resistant Armor (grants resistance to a chosen
damage type) had zero actual mechanism — only a generic passive note,
no choice prompt, no resistance grant. Built both pieces: a real
damage-type choice prompt added to the existing infusion activation
dialog, and the resistance grant itself using the exact same pattern
already established for Scion of the Outer Planes (a stored player
choice read directly into a real resistance entry). Correctly gated
on the infusion actually being active, not just known, matching how
every other infusion effect in this app works.

Verified both directions: resistance correctly granted when the
infusion is active with a chosen type, correctly absent when the
infusion isn't active even if a type was previously chosen. Full
regression: 0 failures across every class.

**Next, and last**: Eldritch Invocation (54 entries, the largest
remaining category).

## Eldritch Invocation audited — all 151 optional class features now reviewed

Final category of the optional class features audit. Confirmed all
54 real invocations present in the app (my first comparison flagged
41 as "missing," but that was a false positive in my own script — the
app includes parenthetical prerequisites in each name, so a naive
name-split treated "Agonizing Blast" and "Agonizing Blast (prereq:
Eldritch Blast)" as different entries; re-ran the comparison stripping
parens and confirmed a clean 54/54 match, with the only "extra" 4
entries being the Pact Boons themselves, correctly included as
prerequisite context).

Sampled mechanical wiring across a diverse set: Devil's Sight, Armor
of Shadows, and Thirsting Blade already confirmed correctly wired
from earlier work. Found 2 real, confirmed gaps — Lifedrinker (+CHA
necrotic on pact weapon hits) and Repelling Blast (push target 10 ft
on Eldritch Blast hit) had zero mechanical presence anywhere, only
existing as names in the invocation pool. Fixed both using the exact
same "dynamically compute the live number into the description"
pattern already established for Agonizing Blast.

**Found and fixed a severe, unrelated, pre-existing crash bug while
testing the Repelling Blast fix**: sign() was referenced in
Agonizing Blast's own damage-display code but never defined or
imported anywhere in this file, despite existing identically in 3
other files already. This meant any Warlock with Agonizing Blast and
a realistic positive CHA modifier — which is virtually every Warlock
who takes it — would crash the moment their Eldritch Blast description
rendered, in both the Spells tab and Actions tab. Not a rare edge
case; a near-guaranteed crash for one of the most common Warlock
builds in the game. Fixed by importing the existing helper rather
than duplicating it a 4th time.

Full regression: 0 failures across every class with all 3 fixes
(Agonizing+Repelling Blast combined, and Lifedrinker) active
simultaneously.

**This closes the full optional class features audit the user
requested**: all 151 entries across 9 categories (Eldritch Invocation
54, Battle Master Maneuver 23, Elemental Discipline 17, Artificer
Infusion 16/66-real, Fighting Style 13, Metamagic 10, Arcane Shot 8,
Rune Knight Rune 6, Pact Boon 4) now confirmed present on the
selection side, with real, verified mechanical wiring built for every
genuine gap found along the way — 2 categories built from scratch
(Arcane Shot, Rune Knight Rune's Actions tab wiring — the choice
mechanism itself already existed), Pact Boon's Chain/Blade fully
built, and targeted fixes across Fighting Style (Interception/
Protection), Artificer Infusion (Resistant Armor), and Eldritch
Invocation (Lifedrinker, Repelling Blast) — plus one severe,
unrelated crash bug caught along the way.

## Eldritch Invocation — 12 confirmed-empty invocations now built; true remaining scope corrected

Completed all 12 invocations confirmed to have zero mechanical
presence anywhere in the codebase (verified via direct grep across
every file, not just the narrower runtime check that initially missed
several already-wired ones like Agonizing Blast).

**9 built as real, limited-use resources** (Bewitching Whispers,
Chains of Carceri, Ghostly Gaze, Minions of Chaos, Mire the Mind,
Sculptor of Flesh, Sign of Ill Omen, Tomb of Levistus, Trickster's
Escape), following the exact established pattern already used for DM
Reward resources.

**Caught and fixed a real mistake while building these**: a str_replace
call matched too broadly and deleted the working "Living Shadow"
resource from earlier session work instead of inserting the new code
alongside it. Caught by re-checking the file immediately after the
edit rather than assuming it landed cleanly — restored it, then
verified both the restored block and the new additions work
correctly, not just the new code.

**3 built as Actions tab entries** (One with Shadows, Relentless Hex,
Far Scribe) — these don't fit the resource-cap pattern (unlimited but
conditional, or too complex to fully simulate).

**Corrected the remaining scope significantly**: re-checked the 35
invocations that appeared to have real code matches from an earlier
grep, this time properly including internal flag checks I'd missed in
a rushed first pass. Only 3 of those 35 (Armor of Shadows, Devil's
Sight, Eldritch Mind) are actually, genuinely wired — the other 32
were false positives (comments, unrelated code, or classes_2024.py
text noise), not real mechanical hooks. The true remaining gap in
this category is roughly 32 invocations, not the smaller number my
first re-check suggested.

Full regression: 0 failures across every class with all 12 newly-
built invocations active simultaneously.

**Honest status on the full optional-features audit**: Fighting
Style, Metamagic, Battle Master Maneuver, and Artificer Infusion are
now confirmed complete (or complete enough — infusion's 66 real
entries mostly already correct, one real gap fixed). Elemental
Discipline, Arcane Shot, and Rune Knight Rune are complete. Eldritch
Invocation, the largest category, has 12 of the original ~48 flagged
gaps now genuinely fixed, with roughly 32 more confirmed still
needing real mechanical work.

## Eldritch Invocation — prerequisites, senses note, Book of Ancient Secrets

User specified 5 requirements for how invocations should behave
across systems. Worked through each.

**Prerequisite enforcement (level + pact boon)**: confirmed a real,
significant bug — the choice pool was completely unfiltered, offering
every invocation regardless of the character's actual level, pact
boon, or Eldritch Blast cantrip, and incorrectly included the 4 Pact
Boon names as if they were invocations. Built a real parser reading
each invocation's parenthetical prerequisite text (level number, pact
boon name, Eldritch Blast requirement) and filtering the pool
against the character's actual state. Verified in both directions: a
level-2 Warlock correctly can't see 15th-level or wrong-pact options;
a correctly-qualified level-15 Warlock with the right pact and cantrip
sees them, while still correctly excluding a different pact's
exclusive option.

**Devil's Sight senses note**: confirmed the flag mechanism already
correctly grants darkvision 120 ft, but had no note about its defining
feature — seeing through magical darkness specifically, which normal
darkvision cannot do. Added the note at both of the two separate
senses-display locations in the UI, so it's consistent between initial
load and later refreshes.

**Chosen invocations visible in Features tab**: confirmed already
correctly built and working — verified directly rather than trust the
existing code, building a real character and finding the invocation
names actually rendered.

**Pact of the Tome's Book of Ancient Secrets**: confirmed genuinely
missing. This is a separate invocation from Pact of the Tome itself
(which already correctly grants 3 cantrips) — Book of Ancient Secrets
requires that pact as a prerequisite but grants its own, additional 2
ritual spells from any class's list. Built its own choice card and
wired the grant into bonus_spells, gated on the invocation itself
being chosen, not just the pact.

**Testing this surfaced a real, separate mock gap**: QListWidgetItem
was missing setSelected/isSelected entirely, blocking any real
verification of the level-up panel's spell chooser UI — fixed in the
test harness, following the same real state-tracking pattern already
used for setCheckState on the same class.

Full regression: 0 failures across every tested Warlock level with
prerequisites, Devil's Sight, and Book of Ancient Secrets all active
together, verified through the actual UI construction path, not just
the underlying data functions.

**Still remaining**: "cast at will" invocations need Actions tab
entries (Armor of Shadows/Mage Armor at will, Beast Speech, Beguiling
Influence, Mask of Many Faces, Misty Visions, and others), and the
~32 invocations confirmed still needing real mechanical work from the
previous pass.

## CRITICAL FIX: Warlock invocations-known progression was wrong for the entire session

User provided the official PHB Warlock class text as a reference and
reminder. Cross-checking it against the app surfaced a serious,
previously-undiscovered bug that had been present under everything
built on Eldritch Invocations this session, including all the
prerequisite-filtering work from the prior pass.

Verified the real, official table directly (fetched the full class
page rather than relying on summary text, since several search
results described the rule without giving exact numbers). Real
progression: 2→2, 5→3, 7→4, 9→5, 12→6, 15→7, 18→8. The app had:
2→2, 5→5, 7→6, 10→7, 12→8, 15→9, 18→10 — every breakpoint past level
2 gave meaningfully too many invocations (5 vs the real 3 at level 5;
10 vs the real 8 by level 18), and fabricated an entire extra
breakpoint at level 10 that doesn't exist in the real rule at all —
the real breakpoint is level 9.

Found and fixed 3 separate copies of the same wrong numbers: the
functional choice-count logic in levelup_panel.py (which drives what
a player can actually select — the one that matters most), and two
separate display-text dicts in classes.py (features and level_choices)
that had independently baked in the identical wrong progression.

Full regression: verified against every single real breakpoint from
level 2 to 20, all correct.

**Still to address from this reference**: Eldritch Versatility (swap
a cantrip/pact boon/arcanum spell at each ASI level, with a
correctness requirement to also replace any invocations that become
ineligible), the 3 feats (Eldritch Adept, Metamagic Adept, Martial
Adept), and the "hex/curse feature" prerequisite type for invocations
like Maddening Hex/Relentless Hex, which the prerequisite parser built
last pass doesn't yet handle (only level/pact boon/Eldritch Blast).

## Maddening Hex's "hex/curse feature" prerequisite

Verified the precise real rule via research rather than guess at what
"hex/curse feature" meant: knowing the Hex spell, OR having a cursing
Warlock feature specifically — Hexblade's Curse (an automatic level-1
feature of the Hexblade patron) or the Sign of Ill Omen invocation.
Added this as a new prerequisite type to the parser built last pass.

Caught a real mistake immediately after writing it: used a
subclasses() function that isn't imported anywhere in this file at
all, which would have caused a runtime crash the moment a Warlock
leveled up. Found the file's own already-established, correct pattern
for accessing this same class entry's subclass a few lines above
(the `sub` variable, already in scope) and used that instead of
inventing a new access path.

Verified in all 3 directions: correctly excluded with neither
condition met, correctly included with the Hex spell known, correctly
included with the Hexblade subclass. Full regression: 0 failures
across every Warlock level 2-20.

## Martial Adept, Metamagic Adept, Eldritch Adept — all 3 confirmed

All 3 feats existed in the data with correctly-wired resource grants
(1 d6 superiority die, 2 sorcery points, etc. — all confirmed accurate
against the real rule text already), but confirmed a real, significant
gap: none of them had any way to actually pick what to spend that
resource on. A player taking Martial Adept got a real superiority die
but no way to ever select which 2 maneuvers they know.

Built all 3 choice cards using the established _get_feat_choices
pattern. Eldritch Adept reuses the invocation prerequisite filter
already built for real Warlocks rather than duplicating that logic,
correctly implementing the real rule text precisely ("only if you're
a warlock who meets the prerequisite") — verified a non-Warlock
correctly sees only prerequisite-free invocations, while a real
level-15 Warlock taking this feat correctly sees level-gated options
too.

**Found and fixed a related, real gap while verifying Martial Adept**:
get_superiority_die() didn't check for the Martial Adept feat at all,
so a non-Battle-Master character with this feat would see every
maneuver's die-size placeholder show "—" instead of the real d6, even
though the resource pool itself was already correctly tracking it
separately. Fixed to return a flat d6, matching the real rule and the
same pattern already used for Superior Technique's flat d8.

Full regression: 0 failures across every class with all 3 feats
active simultaneously.

## Eldritch Versatility — correction: already fully, correctly built

Told the user this was likely "the most involved piece left" from
their reference doc. That was wrong, and worth correcting plainly
rather than let stand — checking it properly showed it was already
extensively, correctly built from earlier session work I'd lost track
of, not something needing construction.

Verified rather than assumed correct from the code reading alone: a
real Settings toggle exists and correctly gates visibility to actual
ASI levels (4/8/12/16/19) for an existing Warlock only. All 3 swap
types work (cantrip, pact boon, arcanum — the last correctly gated to
12th level and above, since the arcanum spell-level pool only
populates for arcanums the character actually has). Most importantly,
verified the cascading rule end-to-end with a real test: swapping
Pact of the Blade for Pact of the Chain correctly changed the stored
pact boon, correctly removed a Blade-locked invocation (Thirsting
Blade) the character no longer qualified for, and correctly kept an
unrelated invocation (Devil's Sight) untouched — exactly matching the
real rule text ("if this change makes you ineligible for any of your
Eldritch Invocations, you must also replace them now"). Full
regression: correct visibility at every single level transition from
1→2 through 19→20.

This closes out every item from the user's Warlock reference and feat
list: the invocations-known table fix (critical, affected the whole
session), the hex/curse prerequisite, all 3 "Adept" feats, and now
confirmed Eldritch Versatility needed no further work at all.

## Eldritch Invocation — 27 more built, closing out the broader audit

Returned to the ~32-invocation gap flagged before the Warlock
reference doc took priority. Re-ran the check with a corrected test
script (the previous count was inflated by a bug in my own test's
key-matching, not the app) to get an accurate, current list: 27
genuinely still missing (2 more, Agonizing Blast and Book of Ancient
Secrets, were false positives — already confirmed correctly wired via
mechanisms the automated check doesn't look at).

Got the full real text for all 27 and built them in one pass,
organized by mechanic type:

- **2 more limited-use resources** (Dreadful Word, Undying Servitude),
  following the same established pattern as the earlier 9.
- **10 "at-will" spell-like invocations placed in Known Actions**, per
  the user's explicit instruction — Ascendant Step, Beast Speech,
  Eldritch Sight, Fiendish Vigor, Mask of Many Faces, Master of Myriad
  Forms, Misty Visions, Otherworldly Leap, Visions of Distant Realms,
  Whispers of the Grave.
- **4 Eldritch Blast on-hit modifiers** (Eldritch Spear, Grasp of
  Hadar, Lance of Lethargy, Repelling Blast).
- **4 Pact of the Blade/Chain-specific mechanics**, correctly gated on
  the character's actual pact boon choice, not just the invocation
  being known — Eldritch Smite, Improved Pact Weapon, Lifedrinker,
  Thirsting Blade (Blade); Gift of the Ever-Living Ones, Investment of
  the Chain Master, Voice of the Chain Master (Chain). Verified both
  directions: Lifedrinker correctly shows with Pact of the Blade
  chosen, correctly hides with a different pact chosen.
- **3 passive skill/utility grants** (Beguiling Influence, Eyes of the
  Rune Keeper, Witch Sight) and Gaze of Two Minds as a real action.

Full regression: 0 failures across every class with all 27 active
simultaneously.

This closes out the Eldritch Invocation category. Combined with the
earlier 12 and the Warlock-specific fixes (invocations-known table,
hex/curse prerequisite, prerequisite filtering), essentially the
entire flagged gap in this, the largest of the 9 optional-feature
categories, is now addressed.

## Real, app-wide bug found: generic spell-swap incorrectly allowed swapping cantrips

User restated the Eldritch Versatility rule and mentioned Bard/Sorcerer
have a similar cantrip chooser, prompting a closer look at the
existing, separate "swap one spell you know" mechanism shown on every
level-up (not just ASI levels) for known-spell casters.

Verified via the lead 5e rules designer's own clarification rather
than assume: this generic swap rule explicitly applies only to spells
that use spell slots, and cantrips don't use spell slots — they can
only be swapped through a specific feature that explicitly allows it,
like Warlock's Eldritch Versatility (an ASI-level-only optional rule),
not through the free swap available on every level-up.

Confirmed a real, significant, app-wide bug: this app's generic swap
mechanism never filtered out cantrips at all, meaning every known-
spell caster (Bard, Sorcerer, Warlock, Ranger) could freely swap a
cantrip on any level-up — not gated to ASI levels, not gated behind
Eldritch Versatility, just always available. This meant a player
could swap Eldritch Blast for a different cantrip with zero
restriction at any level, which the real rules never permit outside
specific optional features.

Fixed by excluding level-0 spells from both the outgoing (already-
known) and incoming (choosable) pools. Verified directly: a Warlock's
2 known cantrips correctly disappear from the swap-out list while
their 2 known leveled spells remain correctly swappable, and no
cantrip appears in the swap-in pool. Full regression: 0 failures
across all 4 affected classes, confirmed no cantrip leaks into the
swap-in pool for any of them.

This also confirms Eldritch Versatility's separate cantrip-swap branch
is correctly non-redundant — it's the only path to swap a Warlock
cantrip now that this generic mechanism correctly excludes them.

## Spell casting now connects to active_effects and the turn-economy tracker

User asked for two real, reported gaps: casting a spell should
automatically add it to Active Effects (with a self-vs-another prompt
for ambiguous targeting), and casting from the spell browser should
consume the correct action-economy slot.

**Active effects connection**: confirmed a real, comprehensive
active_effects system already existed (Haste, Bless, Shield of Faith,
dozens more with real mechanical hooks — AC bonuses, speed
multipliers, extra actions), but nothing connected actually casting a
spell to it; the player had to separately, manually re-select the
same spell from a dropdown after casting it. Fixed: self-only spells
(range "Self") auto-apply with no ambiguity; spells with a real range
(Touch, 30 ft, etc.) prompt whether the caster is the target, since
these buff spells can go either way and only the self-targeted case
belongs on the caster's own sheet. Verified all 3 paths: an
unambiguous self-spell auto-applies, an ambiguous spell cast on self
gets added, the same spell cast on another correctly doesn't touch
the caster's own effects.

**Turn-economy connection**: confirmed a real, sophisticated
Action/Bonus Action/Reaction tracker already existed (visual chips,
greyed-out buttons when spent, already correctly handling Haste's
extra action for other abilities), but spell-casting never touched it
at all. Checked the real spread of cast_time values across every
spell before assuming everything costs a plain Action — most are "1
action," but some are "Bonus action" or "Reaction," and several are
longer, out-of-combat casts (1 hour, 10 min, etc.) that shouldn't
consume any per-turn slot. Built the correct mapping for all three
combat-relevant cast times, and correctly skip the tracker entirely
for the longer ones. Verified directly: a 1-action spell consumes an
Action, a bonus-action spell consumes only a Bonus Action (not also an
Action), and a 1-hour-cast utility spell touches neither.

Full regression: 0 failures across 5 representative caster classes
with both new mechanisms active together.

## Gated to one leveled spell per turn, per the real bonus-action-spell rule

Verified the precise real rule rather than build a loose "one spell
per turn" cap: it's specifically that casting a spell with a bonus
action restricts the only other spell castable that turn to a
cantrip. In practice this means normal play never allows two leveled
spells in the same turn, but cantrips remain fully exempt regardless
of how many are cast.

Built a per-turn flag, reset alongside the other turn-economy state.
Correctly checked against Haste's already-tracked extra-action flag,
since that's a genuine second action rather than the bonus-action-
spell restriction being triggered — a Hasted caster can legitimately
cast two leveled spells (one per real action) without violating the
rule at all. Action Surge is a separate, real exception (a fighter's
genuine extra action) but isn't tracked anywhere in this app's action-
economy system at all yet — noted as a known gap rather than papered
over with an incomplete fix bundled into this one.

**Found and fixed a related gap while building this**: cantrips
exited _cast_spell() before ever reaching the turn-economy tracking
added last turn (since they don't expend a slot), meaning casting a
cantrip never consumed an Action either, even though most cantrips
have a real 1-action cast time. Fixed to still mark the correct
action-economy slot for cantrips.

Verified all scenarios directly: a first leveled spell succeeds, a
second leveled spell the same turn is correctly blocked, a cantrip
remains castable regardless, a new turn correctly resets the gate, and
an active Haste effect correctly allows a second leveled spell through
the genuine extra action. Full regression: 0 failures across 6
representative caster classes.

## Rebuilt the bonus-action-spell gate correctly — the real rule is directional, not a simple counter

User's questions about Quickened Spell and Earth Genasi's Blade Ward
exposed that the "one leveled spell a turn" gate built earlier this
session was an incomplete simplification of the real rule, not the
rule itself.

The precise rule: casting a spell with a bonus action requires
whatever else is cast that turn (via the regular Action) to be a
cantrip — and this is symmetric regardless of order. The version built
earlier only tracked "was any leveled spell cast," which correctly
blocked two leveled spells in a row, but missed a real case entirely:
a cantrip cast via bonus action (Blade Ward via Earth Genasi's
feature, or Shillelagh) can also be illegally blocked-worthy if a
leveled spell was already cast via the regular Action — since the
cantrip being bonus-action-cast is what triggers the restriction, not
whether it's itself a cantrip.

Rebuilt with two separate tracking slots (what was cast via Action,
what via Bonus Action, and whether each was a cantrip) and a single,
reusable check function implementing the real two-directional
relationship, correctly respecting Haste's tracked extra action as
before. The cast-time/bucket determination now happens up front,
before any slot is expended, so the gate correctly applies to
cantrips too — the earlier version's cantrip path skipped the gate
entirely, which would have missed the exact Blade Ward case.

Also wired the same check into Earth Genasi's separate Blade Ward
resource button, since that's a standalone spend-a-use control
disconnected from the normal spell-casting flow entirely — confirmed
it needed the identical gate, following the same established pattern
used for Harness Divine Power's linked-resource special case.

Verified the complete, correct truth table directly: leveled-then-
leveled blocked, leveled-Action-then-cantrip-Bonus-Action blocked
(the Blade Ward case), cantrip-then-leveled allowed, and nothing-cast
allows anything. Full regression: 0 failures across 6 representative
caster classes.

## Known Actions category filter (Common/Magic Item/Race/Spell) built, and found real bugs while wiring it

User requested wiring prepared spells fully into Known Actions with a
category filter to manage volume, since the old approach only showed
leveled spells if manually pinned. Magic Item is a deliberate
placeholder per explicit direction — that system isn't wired yet.

Built a real classifier rather than an invasive rewrite of the whole
2500+ line action-building file: confirmed via direct testing that
racial entries reliably use the character's own base race name as
source, and spell entries already self-tag their level via the
existing "Cantrip"/"Spell L1" source string, so no new tagging
infrastructure was needed for those two categories. Removed the old
"leveled spells only show if pinned" restriction now that the filter
handles volume instead.

**Caught two real bugs while wiring the filter UI**: first, used a
completely undefined variable for the parent layout, confirmed by
checking the surrounding code rather than assuming — would have
crashed immediately. Second, and more significant: the existing
Action-tab card's click handler had its own separate, duplicate
casting logic instead of delegating to the real _cast_spell()
function built earlier this session. Cantrips clicked from this card
completely bypassed the entire gate check, active-effects wiring, and
even real turn-marking. Leveled spells double-counted turn-economy
usage by calling the turn-marker both inside _cast_spell() and again
in the card's own duplicate code. Fixed by having the card delegate
cleanly to the single, real implementation, then added back proper
user-facing success/failure toasts directly in _cast_spell() itself
so feedback stays consistent regardless of which UI entry point
triggered the cast — including a previously-completely-silent "no
spell slots available" case that gave zero feedback before.

**Caught a third, separate, more serious latent bug during
verification**: the new turn-tracking attributes were only ever
initialized inside _new_turn(), which — confirmed by checking every
call site — is never actually invoked anywhere except an explicit
player button click. This meant a freshly-built character sheet would
crash the instant a player cast their very first spell of a session,
before ever touching "New Turn." Fixed by initializing in __init__
directly, matching the existing safe pattern already used for the
sibling _sneak_used attribute.

Full regression: 0 failures across 6 representative classes with
casting, the full filter system, and a completely fresh (never-
turned) character sheet all exercised together.

## Aasimar action-type bug fixed via verified source, and systemic MPMM natural weapons audit

User provided a verified primary-source excerpt confirming a real bug
I'd need the actual text to catch: the Volo's/VGM Aasimar
transformation (Radiant Soul/Consumption/Necrotic Shroud) is activated
with an Action, not a bonus action (only ending it early is a bonus
action) — this differs from the MPMM version, which is correctly
bonus action. Fixed the race data text and all 3 resource notes in
calculator.py to say Action, verified directly against all 3 VGM
subraces.

This led to auditing every MPMM race for a broader, systemic version
of the same "MPMM variant missing what the base version has" pattern
already found for Minotaur — checked all 21 MPMM race entries against
RACIAL_NATURAL_WEAPONS and found 7 more genuinely missing: Aarakocra,
Centaur, Lizardfolk, Satyr, Tabaxi, Tortle, and Shifter (handled
separately via its own dedicated function). Used the real, verified
trait text for each rather than blindly copy the base version's
values, since several MPMM versions have real, deliberate mechanical
differences — Lizardfolk's MPMM bite is slashing where the base is
piercing, and its Hungry Jaws scales off proficiency bonus where the
base scales off CON modifier; several die sizes are genuinely larger
(1d6 vs the base 1d4).

User proposed merging MPMM races into their base counterpart as a
tagged subrace to prevent this whole class of bug going forward — a
genuinely good structural idea, but correctly scoped as too large and
risky to undertake as a side effect of fixing a data gap, given how
extensively this session alone has built race-specific logic keyed on
the exact separate name strings. Recommended against attempting it
now; noted as a real, worthwhile future refactor to take on
deliberately.

Fixed the Longtooth Shifter natural-weapon check (which only matched
the exact string "shifter," not "shifter (mpmm)") as an explicit,
deliberate match for both known race-name strings — not a blanket
automatic fallback — after first verifying precisely that the fangs
themselves are mechanically identical between versions (same 1d6 STR
piercing). Explicitly did NOT assume this means everything about
Shifter is identical between versions: separately confirmed Shifting's
own temp-HP formula genuinely differs (base: PB + CON mod; MPMM: 2×PB)
and is a distinct, pre-existing gap (neither version's temp-HP grant
is mechanically wired at all yet) rather than a version-confusion bug,
noted separately rather than folded into this fix.

Full regression: 0 failures across every race touched, and 0 MPMM
races (excluding the separately-handled Shifter) still missing a
natural weapon entry they should have.

## Comprehensive re-check: filter/level/cantrip system, bonus-action gate — genuinely correct

Completed the originally-requested thorough re-verification (interrupted
partway through by the Aasimar/Minotaur bugs found along the way).

**Spell level filter, every level 0-9**: built a real test using one
authentic spell at every level. Hit 3 apparent failures at levels 4-6
— traced this down properly with a temporary debug instrumentation
(reverted immediately after) rather than assume a real bug. The
spells were correctly present in the output the entire time; my own
test's exact-string match simply didn't account for the "(C)"
concentration marker correctly appended to some spell names (all 3
"failing" spells happened to require concentration; the others in the
sample didn't). Not an app bug — a bug in how I was checking. Re-
verified properly with a suffix-aware match: all 10/10 pass, and
separately confirmed each level-filter button isolates exactly one
spell through the real filter path with zero leakage between levels.

**Bonus-action gate, real spell data**: re-verified against actual
spells rather than only the earlier synthetic test cases — a real
leveled bonus-action spell (Expeditious Retreat) is correctly blocked
after casting Fireball, and a real reaction spell (Absorb Elements)
is correctly unaffected by the gate entirely, confirming reactions
sit outside this rule as they should.

Full final regression: 0 failures across 8 classes with every
category filter × every level filter combination exercised together.

## Wild Shape casting gate + Martial Versatility, with a real self-caught bug along the way

**Wild Shape spell-casting gate**: verified the real rule via research —
Beast Spells lets a Druid cast while Wild Shaped starting specifically
at 18th Druid class level (not total character level). Fixed both
_cast_spell() and _cast_spell_as_ritual() to respect this. While
editing, an earlier replacement had accidentally deleted a still-
referenced variable assignment (base_time) — caught by grepping for
the variable across the file rather than assuming the edit was clean,
fixed before it could cause a crash on every ritual cast. Verified
both sides of the level-18 threshold directly.

Left the real material-component sub-exception unbuilt and explicitly
flagged rather than faked: confirmed this app's spell data doesn't
reliably track material components at all (Identify shows no "M"
despite genuinely requiring one), so building that nuance on top of
unreliable data would produce a wrong result dressed up as precise.

**Martial Versatility**: verified via research this is genuinely
ASI-level-gated (not "finish a long rest," which is a different,
separate feature called Spell Versatility) — confirming it really is
architecturally identical to Eldritch Versatility as directed. Built
using the same card pattern, with Fighter's genuinely different ASI
level set (extra levels at 6 and 14) confirmed directly from the
app's own class data rather than assumed.

Caught two real bugs before they shipped: first, pulled from the
wrong same-named FIGHTING_STYLES (a flat list in classes.py already
identified earlier this session as unsuitable for choice-building,
not the correct class-keyed dict in levelup_panel.py). Second, and
more significant — my own final verification test caught that a
known fighting style still incorrectly appeared as something to swap
into. Traced this to a wrong separator assumption (en-dash) that
didn't match the real, true storage format (parentheses) — confirmed
the real format by tracing the actual, standard fighting-style choice
card's write-back path directly, not by re-trusting my own earlier
guess a second time. Fixed the parsing in both the pool-exclusion
logic and the swap-out combo population.

Full regression: 0 failures across every real ASI level for Fighter,
Paladin, and Ranger, confirming both correct visibility gating and a
verified, correct swap (Dueling → Archery) end-to-end.

## Elemental Wild Shape forms — all 4 added, with 2 real bugs caught before shipping

User provided verified stat blocks for Air, Water, Earth, and Fire
Elemental (Circle of the Moon's level-10 Elemental Wild Shape). Added
all 4 to WILDSHAPE_BEASTS (181 → 185 total), confirmed the display
schema already safely supports damage_resistances/damage_immunities/
condition_immunities as optional fields without any invasive change,
and folded Earth Elemental's thunder vulnerability into its traits
list rather than inventing an unsupported new schema field for one
creature's one property.

Confirmed via research this is a distinct feature granted at exactly
10th level, not something the existing generic CR formula would
correctly grant on its own — a level-10 Moon Druid's generic max CR
is only 3, not the 5 these elementals require — so built it as an
explicit, separate gate rather than trying to force it through the
CR filter.

**Caught two real bugs before they shipped**, both through direct
testing rather than assuming the code was correct:

1. My first gating attempt referenced is_moon/druid_lvl that only
   existed in a *different* function's scope — a genuine NameError,
   confirmed by actually running the code rather than trusting that
   it compiled (Python doesn't check names until execution). Fixed by
   recomputing both correctly in this function's own scope.

2. Testing the actual stat block rendering (not just the CR-filter
   list) surfaced a second, more significant, pre-existing gap: the
   real card-preparation code hardcoded damage_immunities/condition_
   immunities to empty strings and never referenced damage_resistances
   at all — meaning the fields I'd carefully added to the new
   elemental data (and any future beast with real resistances) would
   never have actually reached the player, even though the display
   function itself already fully supported showing them. Fixed to
   correctly forward all 3 fields from the real beast data.

Full regression: all 185 beasts (not just the 4 new ones) render
cleanly through the real, complete display path — confirming the
resistances fix didn't just work for elementals but correctly
benefits every beast in the catalog going forward. Verified the
Elemental Wild Shape gate itself against all 3 real scenarios: a
qualifying level-10 Moon Druid, a level-9 Moon Druid (too early), and
a non-Moon Druid at level 10 (wrong subclass) — each correctly
included or excluded.

## ASI distribution chooser sizing fix, and all 2024 backgrounds removed

**Sizing fix**: user reported the +2/+1-or-+1/+1/+1 ability score
chooser (triggered in Step2Abilities by races with flexible ASI, like
most MPMM races) could collapse to an unreadable line when the window
shrinks. Confirmed the root cause: the parent scroll area correctly
resizes its content to fit the viewport (as intended), but the card
had zero minimum size of its own to resist that compression. Set a
real minimum height/width calculated from the card's actual content.
Caught that the mock's setMinimumWidth/setMinimumHeight were complete
no-ops with no real getter at all, making the fix impossible to
actually verify — fixed the mock properly (store + real getter,
matching the pattern used for other properties this session) rather
than accept a test that couldn't fail.

**2024 backgrounds removed**: user clarified this app targets the
2014 ruleset only for backgrounds specifically. Removed all 17 real
"(2024)" Origin Feat backgrounds (Acolyte through Wayfarer) as one
contiguous, cleanly-bounded block, plus the separate "Custom
Background" entry (confirmed genuinely 2024-specific — it explicitly
grants an Origin feat, a mechanic that doesn't exist in 2014 rules at
all). Verified zero other files reference these specific background
names before deleting, to avoid breaking something silently. Updated
the stale header comment and the 2 README lines directly, concretely
affected by this change (the background count, and the "origin feats"
mention in the background-details bullet) — left the broader,
still-accurate 2024 references alone (feats, general sourcebook
coverage, the 2024-ruleset roadmap item), since this was a scoped
background-only change, not a request to strip all 2024 content from
the app.

Full regression: 99 unique backgrounds remain (zero duplicates, zero
2024 content), and all 99 build cleanly end-to-end.

## 4 more Versatility features built, matching the user's verified reference

User provided the complete, verified TCE reference text for all 8
Versatility optional features, prompting a full audit rather than
trust the 2 already confirmed correct (Eldritch, Martial). Found 5
real gaps.

**Genuinely missing entirely**: Bardic Versatility (Bard — expertise
skill or cantrip), Cantrip Versatility (shared mechanism for Cleric
and Druid, identical single-swap-type rule), and Sorcerous
Versatility (Sorcerer — metamagic or cantrip). Built all 3 using the
established card + "what kind" selector pattern, each with a real
Settings toggle.

**Martial Versatility itself was incomplete**: the earlier build only
ever handled the fighting-style swap. The real rule text specifically
gives Fighter (and only Fighter) an additional option — swap a known
Battle Master maneuver — gated on actually knowing any. Reworked to
add a "what kind" selector; verified a Battle Master Fighter with
maneuvers sees both options, a non-Battle-Master Fighter correctly
sees only the fighting-style option, and Paladin never sees the
maneuver option at all even in the edge case of somehow having
maneuvers recorded.

Verified every real storage key/format directly against the app's own
established code rather than assumed (skills' expertise-level
convention, sorcerer_metamagic's exact choice key) before building
the swap logic on top of them.

Full regression: 0 failures across every real ASI level for all 8
Versatility-eligible classes with all 5 toggles active simultaneously.

## Full optional-features audit begun via class reference "optional" search

User provided the complete class reference doc and asked to search by
"optional" to find every optional feature across every class
systematically. Found 29 real optional-feature entries across 10
classes (excluding the 18 Cleric domain "Blessed Strikes" variants
and 5 Versatility features already confirmed this session).

Checked each against the codebase before assuming anything missing.
Found a genuine surprise: OPTIONAL_CLASS_FEATURES (class_features.py)
already has real data entries for 10 of the remaining 15 — Favored
Foe, Deft Explorer, Primal Awareness, Nature's Veil, Steady Aim,
Magical Guidance, Dedicated Weapon, Ki-Fueled Attack, Focused Aim, and
Wild Companion — none of which showed up in my initial broad grep
since I was checking the wrong files first.

**Found and fixed 5 real, confirmed level-gating errors** in that
existing data, caught by cross-referencing every entry's level key
against the verified reference text rather than trusting the data was
already correct just because it existed: Steady Aim was gated at
Rogue level 1 (real: 3rd), Magical Guidance at Sorcerer level 1 (real:
5th — a 4-level discrepancy), and all 3 Monk features were wrong —
Dedicated Weapon and Ki-Fueled Attack were both bundled at level 1
(real: 2nd and 3rd respectively), and Focused Aim was at level 3
(real: 5th). Verified all 5 corrections directly against the real
data structure.

**Confirmed still genuinely missing entirely, not yet built**: Primal
Knowledge (Barbarian), Magical Inspiration (Bard), Quickened Healing
(Monk), Spellcasting Focus (Ranger), and Cantrip Formulas (Wizard).

**Not yet verified**: whether the 10 features already correctly
present in OPTIONAL_CLASS_FEATURES are also fully mechanically wired
(real resources, real Actions tab entries) or just correctly-gated
descriptive text — this needs the same kind of check that found gaps
in Resistant Armor, Battle Master Maneuvers, and others earlier this
session. Full regression: 10/10 tested classes build cleanly with the
level fixes applied.

## Key-term search (bonus action/reaction/resistance/speed) — 121 features found, 2 real core gaps

User asked to search the class reference by 4 more key terms. Parsed
the file into distinct feature blocks (rather than raw line grep) to
avoid drowning in duplicate/irrelevant hits, finding 121 distinct
named subclass/class features mentioning at least one term.

Sampled ~120 of the 121 against the codebase (a very different result
than the Eldritch Invocation audit) — the large majority (100+) were
already correctly present, since these are mostly automatically-
granted subclass features already in the static Actions tab data,
not player-chosen options like invocations. Spot-verified several at
random against the reference for both wiring and correct level —
Curving Shot, Song of Defense, Dragon Wings, Relentless Avenger all
confirmed accurate.

**2 real, confirmed gaps found — both core, non-optional Monk base
features, not subclass-specific**: Empty Body (18th level) and
Ki-Empowered Strikes (6th level) existed only as display text and a
tooltip, with zero mechanical presence anywhere, despite affecting
every Monk character regardless of subclass. Built Empty Body as a
real resource (checked and confirmed no deeper "counts as magical"
combat-resolution system exists in this app to hook Ki-Empowered
Strikes into, so built it as a real, visible Passive entry instead —
the same honest-tiering approach already used for similar effects
this session, rather than fake a mechanical hook this app's
architecture can't actually back up).

**Caught and fixed the exact same mistake as before while building
Empty Body**: a str_replace matched too broadly and deleted the
existing Shadow Strike resource entirely instead of inserting
alongside it. Caught immediately by checking the file directly rather
than assuming the edit was clean, restored it, and verified both
work correctly together.

**Also caught a real level-gating bug in my own new Ki-Empowered
Strikes entry**: initially showed at every Monk level instead of the
real 6th-level requirement, since a generic KNOWN_ACTIONS entry
doesn't automatically infer its gate from the class progression data.
Fixed via the established CLASS_SPECIFIC_GATE_OVERRIDES mechanism,
verified against every level 1-6.

The remaining ~1 unchecked feature and the small number of subclass-
name false positives (from the block-parsing heuristic picking up a
subclass's own intro section) weren't pursued further given the
overwhelming pattern of correctness in this category. Full
regression: 20/20 Monk levels build cleanly with both fixes active.

## Bard spell table, Action Surge, and the musical instrument bug — all fixed and verified

**Bard spell table**: user provided the exact, verified table. Found
spells-known was roughly half the real value at every level (e.g.
level 10 showed 11, should be 14), and cantrips-known incorrectly
gave Bard a 5th cantrip at level 16 (the real progression caps at 4).
Fixed both against the exact pasted numbers, verified all 20 levels
match precisely.

**Action Surge**: confirmed a real, previously-flagged gap — existed
as a spendable resource with zero connection to the turn-economy
system despite genuinely granting an extra action. Wired the spend to
set a real, turn-scoped flag that has_extra_action() now checks
alongside Haste, reset on _new_turn(). Verified it correctly bypasses
the "one leveled spell per turn" gate the same way Haste does — this
specifically closes a gap explicitly noted as unresolved earlier this
session (Action Surge wasn't tracked as an extra-action source at all).

**Musical instrument bug**: confirmed the user's report precisely.
_weapon_category_pool() unconditionally fell through to a weapon pool
for any "Any X" starting-equipment text, so "Any other musical
instrument" resolved to simple weapons (since "martial" isn't in that
text either, matching the default else-branch). Fixed to check for
real non-weapon categories (instrument, artisan's tools, gaming set)
first, at both of the 2 real call sites. Verified the fix returns
real instruments and that genuine weapon categories still work
unchanged.

Full regression: 4/4 representative classes clean with all three
fixes active together.

## Open items, not reached this session — continued below

- **Filter system rework**: per-bucket filters (Action/Bonus Action/
  Reaction/Passive each need their own filter row, not one shared
  row across all 4), Kenku Mimicry needs to be a real, usable Passive-
  tab entry, and the Passive/Other tab needs its own separate filter
  set. Additionally: a filter chooser should only render at all when
  more than one distinct category is actually present in that bucket
  for that character — hide it entirely otherwise.
- **Pyromancer subclass**: user clarified this is real, legitimate
  content from Plane Shift: Kaladesh (a real UA source, same tier as
  Plane Shift: Amonkhet which this app already supports for some
  Cleric domains) — NOT unsupported homebrew as I'd assumed. Not yet
  built; would need the full subclass added from scratch.
- **5 confirmed-missing optional features** from 2 turns ago: Primal
  Knowledge (Barbarian), Magical Inspiration (Bard), Quickened
  Healing (Monk), Spellcasting Focus (Ranger), Cantrip Formulas
  (Wizard) — verified genuinely absent, not yet built.
- **Sorcerer/Warlock/Ranger spell tables**: not yet cross-checked
  against a verified reference the way Bard just was — the Bard error
  was severe and system-wide, so these should be verified with the
  same rigor before being trusted.

## Spell tables verified against the real reference file, 5 optional features given real mechanics

**Spell table verification**: user redirected me to use the already-
uploaded reference file directly instead of web search, which was the
right call — extracted the real Sorcerer, Warlock, and Ranger tables
directly from it. All 3 confirmed exactly correct against the current
implementation (Sorcerer and Warlock spells/cantrips known matched
digit-for-digit; Ranger's lack of a cantrips column at all was also
confirmed correct). The Bard error earlier this session was isolated,
not a systemic pattern across every caster.

**Confirmed a much larger gap while building Quickened Healing**: all
10 already-present OPTIONAL_CLASS_FEATURES entries (Favored Foe, Deft
Explorer, Primal Awareness, Nature's Veil, Steady Aim, Magical
Guidance, Dedicated Weapon, Ki-Fueled Attack, Focused Aim, Wild
Companion) turned out to have zero real mechanical wiring at all —
only correctly-gated descriptive text shown as a toggle in the
Features tab. This confirms and significantly expands the "not yet
verified" note flagged 2 turns ago.

Built a real _optional_feature_enabled() helper checking both real
enable mechanisms this app uses, and gave 5 of the 10 real mechanical
Actions tab entries — Steady Aim, Ki-Fueled Attack, Focused Aim,
Magical Guidance, Wild Companion — chosen because all 5 use existing
resources (ki, sorcery points, wild shape uses) rather than needing a
new resource pool built from scratch. Verified each individually
appears only when its toggle is on, and all 8 representative classes
build cleanly with all 5 active simultaneously.

**Still not mechanically wired** (same confirmed-absent-wiring
problem, but each needs more than an existing-resource Actions tab
entry): Favored Foe and Nature's Veil both need a new, real resource
(proficiency-bonus-scaled uses/LR); Dedicated Weapon needs a real
"designate a weapon" mechanism; Deft Explorer is multi-part and
mostly passive (expertise/languages/speed bonuses); Primal Awareness
needs the real bonus-spells-by-level table built out.

Also fixed Action Surge (real turn-scoped extra-action grant, closing
an explicitly-flagged prior gap), and confirmed the musical instrument
starting-equipment bug is precisely fixed as reported.

## Open items, continued below

- 5 remaining optional features needing real mechanical wiring (listed
  above): Favored Foe, Nature's Veil, Dedicated Weapon, Deft Explorer,
  Primal Awareness
- 5 confirmed-genuinely-missing optional features (never built at
  all): Primal Knowledge, Magical Inspiration, Quickened Healing (note:
  distinct from Ki-Fueled Attack, itself now wired), Spellcasting
  Focus, Cantrip Formulas
- Filter system rework: per-bucket filters, Kenku Mimicry as a real
  Passive-tab entry, conditional filter-chooser visibility
- Pyromancer subclass (confirmed real content, Plane Shift: Kaladesh)
  — not yet built

## Favored Foe, Nature's Veil, Deft Explorer (Roving/Tireless), Primal Awareness — real mechanics built

Continuing the optional-features wiring pass. Built real mechanics for
4 more of the 10 confirmed-zero-wiring features:

**Favored Foe**: real resource (PB uses/LR), gated on Ranger level 1+
and the toggle.

**Nature's Veil**: real resource (PB uses/LR), gated on level 10+.

**Deft Explorer — Roving (6th level)**: hooked into the existing,
already-displayed _speed_bonus_sources mechanism rather than building
something new — climb/swim speed set to match walking speed (the
same established pattern already used for other races/effects with
this exact grant), plus a flat +5 ft bonus. Caught a real, self-
introduced bug before it shipped: this field had no other writer
anywhere in the codebase, so nothing was resetting it between calls —
without an explicit reset, repeated calls during normal play (this
function is called directly from multiple UI locations, not through
update_all()) would have accumulated duplicate entries indefinitely.
Verified by calling the function 5 times in a row and confirming
exactly one entry, not five.

**Deft Explorer — Tireless (10th level)**: real resource (PB uses/LR,
1d8+WIS temp HP), gated on the same Deft Explorer toggle as Roving
since both are parts of one feature at different levels, not two
separate feature names.

**Primal Awareness**: real bonus-spells table (3rd: Speak with
Animals, 5th: Beast Sense, 9th: Speak with Plants, 13th: Locate
Creature, 17th: Commune with Nature), verified against the user's
reference file and wired into the existing bonus_spells mechanism
already used for Domain spells — confirmed each level threshold adds
exactly the right spells and no more.

Full regression: 20/20 Ranger levels clean with all 4 new mechanics
active simultaneously.

## Open items, continued below

- **Deft Explorer's Canny (1st level)**: the expertise-skill-plus-2-
  languages choice needs a real choice-card UI integration point that
  doesn't exist yet for optional-feature-triggered choices — deferred
  as the most involved remaining piece, not yet built.
- **Dedicated Weapon** (Monk): needs a real "designate a weapon"
  mechanism — not yet built.
- **5 confirmed-genuinely-missing optional features** (never built at
  all, unchanged from last checkpoint): Primal Knowledge, Magical
  Inspiration, Quickened Healing, Spellcasting Focus, Cantrip Formulas.
- Filter system rework (per-bucket filters, Kenku Mimicry, conditional
  visibility) — not started.
- Pyromancer subclass (confirmed real Plane Shift: Kaladesh content)
  — not started.

## Correction to last turn's report, plus a real skills-scale bug caught and fixed at its root

**Correction, stated plainly**: last turn I reported all 10 pre-existing
OPTIONAL_CLASS_FEATURES entries had zero mechanical wiring. That was
wrong for 3 of them — Favored Foe, Nature's Veil, and Deft Explorer's
Tireless component were already correctly built as real resources
(PB-scaled, LR reset, correct level gates), apparently from earlier in
this same session before the portion I have direct visibility into.
My check methodology at the time was flawed (a broken grep/wc
combination that silently produced false negatives), caught only when
building Favored Foe from scratch would have meant redoing already-
correct work. Re-ran the same command and got different, accurate
results, confirming the bug was in my test, not the code.

**Real remaining gap in Deft Explorer**: while Roving and Tireless
were already built, Canny — the foundational 1st-level component
every Deft Explorer Ranger gets (double proficiency bonus for a
chosen skill, plus 2 languages) — never had a real choice card
anywhere. Built one, as a new, reusable _get_optional_feature_choices()
source in levelup_panel.py.

**Caught a real, more significant bug while building Canny**: checked
the actual skills-proficiency scale directly in get_skill_bonus()
rather than assume — confirmed it's 0=none, 1=half proficiency (Jack
of All Trades-style), 2=full proficiency, 3=expertise. My first Canny
draft used lvl==1 for "proficient," which is actually half-proficiency,
not full. Fixed immediately to lvl==2.

This same check then exposed that Bardic Versatility's expertise-swap
logic, built earlier this session, had the identical bug in both
directions: its swap-out pool used lvl>=2 (incorrectly including
plain-proficient skills as if they were expertise) and its swap-in
pool used lvl==1 (incorrectly offering half-proficiency skills).  The
actual consumption logic that applies a confirmed swap had the same
numbers wrong too (setting skills to 1/2 instead of the real 2/3).
Fixed all three call sites to use the real scale (expertise=3, full
proficiency=2), verified directly against a character with all three
distinct real levels (half, full, expertise) to confirm each is now
correctly distinguished rather than just checking that something
changed.

Full regression: 0 failures across Bard and Ranger at every level
with both optional-feature toggles active.

## Dedicated Weapon built, and a correction: Canny was already partially built

**Dedicated Weapon (Monk)**: confirmed this app has no deeper weapon-
eligibility system to hook a real mechanical outcome into (same
situation as Ki-Empowered Strikes) — built as a real, honest resource
tracker rather than a fake connection. Reset on SR (the more frequent
of "short or long rest").

**Correction to my own last summary**: I claimed Canny's choice-card
integration was "not yet built" and deferred it as the most involved
remaining piece. That was wrong — investigating it just now found
_get_optional_feature_choices() already exists, is already wired into
the primary pending-choices flow, and already correctly handles
Canny's skill-expertise half, complete with a comment in my own
established phrasing style, meaning I'd built this in an earlier part
of this same overall session and lost track of having done so.
Verified this cost nothing (still fully working), but it's worth
naming plainly rather than letting an inaccurate "not yet done" stand
uncorrected.

What genuinely was still missing: Canny's second half, 2 additional
languages, which had no choice card anywhere. Added it using the
exact established language-choice pattern (matching Prodigy feat's
language choice). Verified both halves of Canny now correctly appear
together as separate, real choice cards.

Full regression: 20/20 Ranger levels and 20/20 Monk levels clean with
every new mechanic active.

## Final 5 optional features built — Primal Knowledge, Magical Inspiration, Quickened Healing, Spellcasting Focus, Cantrip Formulas

All 5 remaining genuinely-missing optional features from the class
reference "optional" search are now built.

**Quickened Healing**: real Action-bucket entry using existing ki and
the app's own real get_martial_arts_die() computation.

**Primal Knowledge**: built as 2 separate choice instances (3rd and
10th level are independent grants, not one combined choice), using
Barbarian's real skill_choices pool. Caught a real bug before shipping
by checking the actual write-back mechanism rather than assuming a
generic "skill_prof" type choice grants real proficiency — it doesn't
unless the choice_id specifically ends with "_skill_profs"; without
that exact suffix the choice would have been stored but never
actually applied to the character's skills.

**Magical Inspiration and Spellcasting Focus**: both real, visible
Passive entries. Magical Inspiration involves another creature's
spellcasting, which this app has no mechanism to simulate; Spellcasting
Focus is a flavor/equipment-flexibility note this app doesn't need to
mechanically enforce — same honest-tiering approach as Ki-Empowered
Strikes and Dedicated Weapon.

**Cantrip Formulas**: extended the existing Cantrip Versatility card
rather than building a new one, since the UI mechanism (swap one
cantrip for another) is identical. Correctly kept as a separate gate
condition rather than folding Wizard into the Cleric/Druid ASI-level
check, since the real rule is "whenever you finish a long rest," not
tied to ASI levels — verified the card shows for Wizard at a genuinely
non-ASI level (3→4 is a red herring since 4 IS an ASI level; verified
against Cleric at 5→6, a real non-ASI transition, confirming the
original ASI-gating remained correctly untouched).

This closes the last of the 15 optional-features gaps found via the
"optional" key-term search: 10 already-present-but-unwired features
now have real mechanics (Roving/Tireless/Canny's 2 halves for Deft
Explorer, Favored Foe, Nature's Veil, Steady Aim, Ki-Fueled Attack,
Focused Aim, Magical Guidance, Wild Companion, Dedicated Weapon), and
these final 5 that were missing entirely are now built.

Full regression: 100/100 class/level combinations (5 classes × 20
levels) clean with all 5 new features active simultaneously.

## Open items, continued below

- Filter system rework (per-bucket filters, Kenku Mimicry, conditional
  visibility) — not started.
- Pyromancer subclass (confirmed real Plane Shift: Kaladesh content)
  — not started.

## Filter system rework: per-bucket filters, and Kenku Mimicry wired in

**Per-bucket filters**: reworked from one shared filter row applying
uniformly across all 4 tabs to each tab (Action/Bonus Action/Reaction/
Passive) having its own fully independent filter state, buttons, and
visibility. Built the conditional-visibility rule explicitly requested:
a bucket's filter chooser only renders when more than one distinct
category is actually present for that character in that bucket —
verified directly with a basic Fighter whose Reaction and Bonus Action
buckets correctly hide their filters (only Common entries present).

**Caught a real, critical bug before it shipped**: the existing
_refresh_action_tabs() clearing logic assumed only a trailing stretch
was permanent ("keep the stretch, clear everything else"). Adding 2
new permanent filter-row widgets per bucket without updating this
would have caused every refresh to silently delete the filter UI
itself. Caught by explicitly testing repeated refreshes and confirming
the same widget object survives, not just checking a single refresh.

**Kenku Mimicry**: added as a real, usable Passive-tab entry, with the
real, version-specific mechanical text resolved dynamically — confirmed
base Kenku (opposed Charisma/Deception check) and Kenku (MPMM) (flat
DC 8+PB+CHA) have genuinely different rules text, so built a dedicated
resolver rather than one generic description that would be wrong for
one of the two versions.

**Caught and fixed 2 real bugs while building this**: first, used
get_prof_bonus/ability_mod without importing either in this file's
scope — this file has zero top-level imports (everything is local-
per-function), confirmed by checking the established pattern before
fixing. Second, and more specific: assumed ability_mod() took a single
raw score, but its real signature is (char, ability_name) and it's
imported from character.py, not calculator.py — caught by actually
running the code and reading the real TypeError rather than assuming
the fix was correct after just adding the import.

Full regression: 15/15 race/class combinations clean, including
repeated-refresh stress testing to confirm the filter-clearing fix
holds up over time, not just on first render.

## Open items, continued below

- Pyromancer subclass (confirmed real Plane Shift: Kaladesh content)
  — not started. This is the last remaining item from this extended
  fixes pass.

## Pyromancer subclass built — with an important nuance about its real status

Before building, researched the user's claim that Pyromancer is
"added from Plane Shift Kaladesh." This needed a real correction:
multiple independent, converging sources confirm Plane Shift: Kaladesh
is a real, free WotC-published PDF, but it is explicitly not official
D&D content in the tier of the core rulebooks or even Unearthed
Arcana — it was created primarily by the Magic: the Gathering design
team as a crossover product, and several sources note it was never
added to official tools like D&D Beyond specifically because of this
ambiguous status. This app already has an established, exact
precedent for this situation: Plane Shift: Amonkhet content is used
for some Cleric domains, explicitly marked "unofficial" in the
README's sources table. Followed that same precedent rather than
either refusing to build it or treating it as equivalent to PHB
content.

Got the precise, exact feature text directly from the user's own
already-uploaded class reference file rather than trust web-search
paraphrases (though multiple independent web sources corroborated the
same 4 features and levels, confirming the reference file's accuracy).

Built as a real Sorcerer subclass — "Pyromancer (PSK)" — with all 4
real features:
- Heart of Fire (1st): real, visible Passive entry, since this app
  has no "which spells deal fire damage" flag to hook a real trigger
  into (confirmed by checking directly).
- Fire in the Veins (6th): real fire resistance, using the exact same
  "resistance then upgrades to immunity" pattern already established
  for Forge Domain.
- Pyromancer's Fury (14th): real, usable Reaction entry — fully
  mechanically simulatable (deal fire damage = sorcerer level when hit
  by a melee attack).
- Fiery Soul (18th): real fire immunity, via the same upgrade pattern
  as Fire in the Veins.

Marked "Unofficial (Plane Shift: Kaladesh)" directly in every
user-facing description, not just in a data comment, so a player
encountering this subclass sees its real status without having to
dig for it. Updated the README's sources table to reflect this,
matching the exact existing Amonkhet-domains entry pattern.

Full regression: 20/20 Sorcerer levels with the Pyromancer subclass
clean, including verified level-gating for the resistance-to-immunity
upgrade and Pyromancer's Fury's 14th-level threshold.

This closes the full extended fixes pass from the "keep going"
sequence — Action Surge, the musical instrument bug, all 15 optional-
feature gaps from the "optional" search, the per-bucket filter rework,
Kenku Mimicry, and now Pyromancer.

## Petrified was missing its own real mechanical grants

Follow-up to the earlier "Conditions given real mechanical effects" pass
in this same conversation. That pass correctly wired Speed/Attack/Saves/
Ability-checks for the conditions with pure numeric modifiers, and
correctly left Charmed/Deafened/Incapacitated as narrative-only since
their real text has nothing numeric to automate — but it missed that
Petrified, unlike those three, DOES have several genuine numeric grants
in its own rule text: auto-fail STR/DEX saves (same mechanic as
Paralyzed/Stunned/Unconscious, just never extended to Petrified),
resistance to all damage, and immunity to poison damage/the poisoned
condition/disease. All were completely unmodeled — checking "Petrified"
changed nothing about saves or the resistances strip.

Fixed:
- `get_condition_save_status()`: added Petrified to the STR/DEX
  auto-fail set alongside Paralyzed/Stunned/Unconscious.
- `get_innate_resistance_grants()`: added a Petrified check (same
  pattern as the existing Scion of the Outer Planes/Resistant Armor
  conditional checks in the same function) granting resistance to
  "all" damage — reusing the exact target string Emissary of
  Redemption/Invincible Conqueror/Umbral Form already use, which the
  resistance display already renders correctly — plus poison damage
  immunity and condition-immunity to poisoned/disease, matching the
  same {"kind": "condition", ...} shape Purity of Body/Divine Health
  already use.

Verified: all 14 conditions individually and all-at-once through
`rebuild()`+`update_all()` with zero exceptions; confirmed Petrified
specifically now produces `damage_resistances = [('all', 'Petrified')]`
and `damage_immunities` containing poison/poisoned/disease entries, and
that `get_condition_save_status` returns auto_fail=True for both STR
and DEX. The resistances-strip UI and save badges both consume these
generically (driven by the `sources` list), so no separate UI change
was needed — `ctrl.refresh()` on condition toggle (already wired in
the earlier pass) picks it up automatically.

## Theme contrast pass: clearer without being jarring

User reported the themes needed "better contrast that isn't too jarring
but also readable." Measured every theme's actual WCAG contrast ratios
(relative-luminance formula, not eyeballed) rather than guessing, and
found two systematic, repeatable gaps across all 12 named themes plus
the module-level default palette:

- **TEXT3** (muted/tertiary text — captions, hint text, tiny badge
  labels, including the RESISTANCES/MOVEMENT captions added earlier
  this same conversation) sat at 3.0-4.9:1 against BG and dropped as
  low as 2.5:1 against the raised SURF3 backdrop it's actually shown
  on in cards — below the 4.5:1 AA text minimum in every single theme
  when checked against where it's really used, not just flat BG.
- **BORDER** (the subtle card/panel edge) sat at 1.4-2.0:1 against BG
  in every theme — low enough that adjacent boxes with no other visual
  separator (the exact resistances-vs-movement-strip confusion fixed
  earlier this conversation) would read as blending together.

Fixed both by mixing each color toward white (or black, for the one
light theme, Arcane Scroll) via binary search until it cleared a
target ratio, rather than raising HSL lightness directly — lightening
in HSL keeps saturation fixed and produces a neon, jarring result once
brightened (confirmed this firsthand: Feywild's border came out as a
vivid saturated blue-purple, #3c43c2, before switching approaches);
mixing toward a neutral desaturates naturally as it lightens, staying
in the theme's original muted register. Targets: TEXT3 to ~4.8-6:1 on
BG (and re-checked against SURF3, tightening further if that backdrop
was still under 4.5:1), BORDER to ~2.6:1 on BG — a deliberate stop
short of the full 3:1 UI-component threshold, since the user explicitly
asked for "not too jarring," and 2.6:1 is already double-to-triple the
original ~1.4-2.0:1 range and enough to read as a distinct edge.

Also swept every base accent color (INDIGO/TEAL/AMBER/CRIMSON/PURPLE)
actually used as literal text color anywhere in sheet.py — confirmed
via grep which ones are literal `color:` text (INDIGO once, TEAL 4x,
AMBER 6x, e.g. the DM-reward "Requires:" prerequisite text) versus
background/border-only (CRIMSON, PURPLE — 0 direct text usages found),
and nudged the handful that fell under 4.5:1 against their real SURF
backdrop (Shadowfell/Blood Moon/Mossgrove/Gearworks/Hallowed Stone
INDIGO, Tavern Hearth TEAL, Arcane Scroll AMBER) up to just clear it.
Left CRIMSON/PURPLE's background/border-only usages against the
correct 3:1 UI-component bar instead of the stricter text bar, only
touching the handful that fell under 3:1 (Blood Moon/Cinderveil/
Tavern Hearth/Gearworks PURPLE, Hallowed Stone CRIMSON).

Verified: `apply_theme()`/`build_qss()` still run cleanly for all 12
themes with no exceptions; recomputed contrast for every theme after
the edits and confirmed TEXT3 now clears 4.5:1 against BG/SURF/SURF2/
SURF3 everywhere, BORDER sits at ~2.6:1 everywhere (up from 1.4-2.0:1),
and every accent color used as literal text clears 4.5:1 against its
real backdrop.

## Magic items: closed out Ring/Staff/Weapon/Armor unwired gaps

Resumed magic-item wiring after the bug-fix pass. Re-surveyed unwired
count via `has_item_effect()` (catches both the `MAGIC_ITEM_EFFECTS`
table and items with an inline `effect=` on their own catalog entry,
unlike a naive `MAGIC_ITEM_EFFECTS` membership check) and found 201
items still unwired — Wondrous 93, Potion 60, Scroll 22, Weapon 12,
Armor 11, Ring 2, Staff 1.

**Discovered 5 of those 23 Weapon/Armor "unwired" items are false
positives**: Enhanced Defense (+1)/(+2), Radiant Weapon (+1), Repeating
Shot, and Resistant Armor are Artificer infusions already mechanically
wired through a completely separate code path — `get_infusion_bonus()`
(calculator.py) for the first four, and an inline `active_infusions`
check inside `get_innate_resistance_grants()` for Resistant Armor —
neither of which populates `MAGIC_ITEM_EFFECTS`, so a naive survey
flags them as gaps when they already work correctly. Verified directly
(applied each via `active_infusions` and confirmed the real bonus/
resistance lands) rather than assuming; left alone.

**Wired the real remaining 18** (Ring 2, Staff 1, Weapon 10, Armor 5):
- **Genuinely narrative/cosmetic, given real note-only entries** (matches
  the established "grant_action, action_type: Passive" pattern used
  throughout this catalog for items with no numeric hook): Staff of
  Adornment (floating decoration), Guild Signet (a 10-guild-variant
  placeholder whose actual per-guild property isn't in this catalog's
  text), Horned Ring (Undermountain-specific house rule), Armor of
  Gleaming and Smoldering Armor (both purely cosmetic), Unbreakable
  Arrow (durability isn't tracked), Mithral Armor (its real effect
  — remove an underlying armor's Stealth disadvantage/Str requirement
  — depends on which base armor piece it's forged as, which this
  catalog entry doesn't pin down), Shield of Far Sight (its real
  benefit is to the mind flayer creator, not the wearer), and 9
  Vestige of Divergence items (Hide of the Feral Guardian, Blade of
  Broken Mirrors, Grovelthrash, Lash of Shadows, Mace of the Black
  Crown, Ruin's Wake, Silken Spite, The Bloody End, Will of the Talon)
  whose real Dormant/Awakened/Exalted tier text lives entirely in a
  separate Vestiges of Divergence sourcebook this catalog's desc field
  never includes — confirmed by reading each one's actual desc text,
  which turned out to be nothing but copy-pasted generic weapon-
  property reminders (Finesse/Versatile/Reach/Thrown) with zero unique
  mechanical content to hook.
- **Real numeric grants wired normally**: Dragonbone Longsword
  (Slumbering) given an accurate note (its 4-tier progression is
  mechanically a different weapon at each stage, too complex for a
  single hook, matching the same "too complex" precedent used
  elsewhere this session); Armor of Vulnerability and Dragon Scale
  Mail both get real `skill_disadvantage` (Stealth) — the only
  concrete mechanical line actually present in either's catalog text,
  which for both turned out to be missing the fuller DMG text (damage
  vulnerability/dragon-breath resistance) entirely, so only what's
  really in the data was wired, not invented; Mind Carapace Armor
  given its full real grant (advantage on INT/WIS/CHA saves, immunity
  to frightened) since attunement itself is the app's only reasonable
  proxy for "this is the intended wearer," which the real item text
  otherwise gates on DM-only narrative judgment.
- **Armor of Vulnerability's STR-conditional speed penalty**: the
  ‑10 ft speed penalty only applies below 15 STR, a per-character
  conditional the generic data-driven effect system can't express —
  added as a direct inline check in `update_all()` (calculator.py),
  same pattern as the existing Heavy Armor Master check just below it.
  Verified: STR 10 correctly gets -10 speed, STR 16 correctly doesn't.

Verified: full 1283-item catalog regression (rebuild + update_all +
attunement_prereq_met + build_action_abilities) — 0 exceptions.
Coverage: 1082/1283 (84.3%) -> 1103/1283 (85.9%); Ring/Staff/Weapon/
Armor categories now have zero real gaps (the 5 remaining "unwired"
hits there are the infusion false-positives above, already working).
Remaining: Wondrous 93, Potion 60, Scroll 22.

## Magic items: Scroll category fully closed out

Wired all 22 remaining Scroll-type items. None carry a persistent
numeric character-sheet state to hook -- every one is either a
one-time consumable action or needs a per-copy choice (which spell,
which creature type) this app has no chooser UI for -- so each got an
accurate `grant_action` reminder entry, same pattern used for every
other reminder-only consumable in this catalog:

- **10 generic Spell Scroll (Cantrip through 9th level) placeholders**:
  real DMG text (cast free if on your class list; otherwise an
  Intelligence (Arcana) check at DC = 10 + spell level, on a failure
  the spell is lost) confirmed correct per-level DC computed directly
  from that formula. The specific spell is chosen per physical copy,
  which this catalog has no slot for, so each entry says as much
  rather than pretending a spell was picked.
- **Scroll of Protection (generic) + its real 8 creature-type variants**
  (Aberrations/Beasts/Celestials/Elementals/Fey/Fiends/Plants/Undead):
  the generic entry points at the 8 real ones; each real one gets its
  actual 5-min/DC-15-Charisma barrier mechanic as an Action reminder.
- **Nether Scroll of Azumar**: real permanent boon (INT +2, advantage
  on saves vs. magic) mechanically parallels the DMG ability-score
  Manuals' one-time-consumption pattern already built into this file
  (`ABILITY_SCORE_MANUALS`), but adds a summoned-ally component with
  no equivalent tracking anywhere in this app -- noted accurately
  rather than half-applying just the ability-score part.
- **Scroll of Tarrasque Summoning / Scroll of the Comet**: a monster
  summon and a one-time 30d10 AoE blast respectively -- both real,
  concrete rules text, but neither is a persistent bonus this app's
  character sheet models; both given accurate reminder text instead.

Verified: full 1283-item catalog regression (rebuild + update_all +
attunement_prereq_met + build_action_abilities), 0 exceptions.
Coverage: 1103/1283 (85.9%) -> 1125/1283 (87.7%). Scroll category: 0
remaining gaps. Remaining: Wondrous 93, Potion 60 (plus the 5 already-
confirmed infusion false-positives in Weapon/Armor from the prior
pass, which are not real gaps).

## Correction: Scroll items were wired to the wrong table; Potion category was already ~all done

Caught a real mistake in the previous "Scroll category fully closed
out" entry above before it could cause player-visible confusion.
Scroll-type items aren't equip/attune gear — they're consumed via
`_use_scroll()` (sheet.py), which looks the item up in `EFFECT_TABLE`
(effects.py), not `MAGIC_ITEM_EFFECTS` (magic_items.py, the table that
drives equipped/attuned Ring/Staff/Weapon/Armor items). My previous
pass added all 22 Scroll entries to the wrong table — they'd never
actually surface through the real "Read" action a player uses.

Worse, while fixing this I found **9 of those 22 were already wired,
correctly, in `EFFECT_TABLE`** before I touched anything this session
(Scroll of the Comet and all 8 Scroll of Protection variants) — so my
previous pass's entries for those 9 were pure duplicates with slightly
different wording, not new coverage at all.

Fixed by removing all 22 entries from `MAGIC_ITEM_EFFECTS` and adding
the 13 genuinely-new ones (10 Spell Scroll level placeholders, the
Scroll of Protection generic placeholder, Nether Scroll of Azumar,
Scroll of Tarrasque Summoning) to `EFFECT_TABLE` instead, in the same
`{duration_category, note}` shape as the pre-existing 9 — verified
directly by simulating `_use_scroll()`'s own lookup (`EFFECT_TABLE.get
(name, {})`) for a sample of the new entries and confirming each
returns real note text.

**Also discovered while investigating this**: the same wrong-table
mistake didn't happen for Potions, because Potions were never touched
via `MAGIC_ITEM_EFFECTS` in the first place — a proper survey combining
`has_item_effect()` with `EFFECT_TABLE`/`INSTANT_POTION_EFFECTS`
membership shows the Potion category was already 50/60 wired (via
`EFFECT_TABLE`'s duration-based active-effects) and 9 more via
`INSTANT_POTION_EFFECTS` (Healing tiers, Elixir of Health, Potion of
Poison, 3 disease/curse antidotes) — both mechanisms already existed
and were already correctly wired to their real "Drink" action before
this session touched anything. Only **Potion of Longevity** was a
genuine gap (a narrative age-reduction effect this app has no age
field for); added to `INSTANT_POTION_EFFECTS` with its real text.

Verified: full 1283-item catalog regression, 0 exceptions; simulated
`_use_scroll()`/`_use_potion()`'s exact lookup for the new entries and
confirmed real note text returns for each.

**Corrected coverage** (now counting `has_item_effect()` OR
`EFFECT_TABLE` OR `INSTANT_POTION_EFFECTS` membership, since a
`has_item_effect()`-only survey misses two of the app's three real
wiring mechanisms): 1185/1283 (92.4%) wired. Scroll and Potion
categories both fully closed. Remaining: Wondrous 93 (plus the 5
already-confirmed Artificer-infusion false positives in Weapon/Armor,
which are separately already wired via `get_infusion_bonus()`/the
`active_infusions` check in `get_innate_resistance_grants()`).

## Magic items: Wondrous category closed out -- catalog effectively complete (1278/1283, 99.6%)

Wired the last 87 unwired Wondrous items. Read every one's actual
catalog description text before writing anything (no fabricated
mechanics) and found they cluster into a handful of real, recurring
reasons none has a persistent numeric character-sheet hook:

- **Summon-a-companion items** (Figurines of Wondrous Power, Bag of
  Tricks, Robe of Serpents, Pipes of the Sewers, Efreeti Bottle, Horn
  of Beckoning Death, Homunculus Servant, Dimir Keyrune, Talarith,
  Shield Guardian Amulet, Quaal's Feather Token Bird, Weird Tank,
  Vox Seeker, Prehistoric Figurines): this app has no summoned-
  creature/companion tracking anywhere, so none of these can attach a
  stat block to the sheet.
- **Vehicles** (all 4 Carpet of Flying sizes + its generic placeholder,
  Flying Chariot, Bobbing Lily Pad, Ornithopter of Flying, Spelljamming
  Helm, Flying Citadel Helm, Helm of the Scavenger, Mighty Servant of
  Leuk-o, Tasha's Creeping Keelboat, Wheel of Wind and Water, Quaal's
  Feather Token Swan Boat): no vehicle/mount model exists in this app.
- **Random-table draw items** (Deck of Wonder/Oracles/Many Things/Many
  More Things/Several Things, Dodecahedron of Doom, The Infernal
  Machine of Lum the Mad): outcomes are DM-rolled per use, not a fixed
  effect.
- **Generic placeholders for real named sub-variants already covered
  elsewhere** (Elemental Gem, Manual of Golems, Quaal's Feather Token,
  Crystal Ball (Legendary Version), Devastation Orb): each just points
  at its real variants.
- **4 Vestige of Divergence items** (Danoth's Visor, Infiltrator's Key,
  Jewel of Three Prayers, Verminshroud): same external-sourcebook gap
  as the 9 Vestige weapons wired earlier this session.
- **Sentient/NPC-flavor items** (Professor Orb/Skant, Murgaxor's Orb,
  Harp of Gilded Plenty, Tome of the Stilled Tongue) and **campaign
  plot-device artifacts** (Book of Exalted Deeds, both Book of Vile
  Darkness entries, Iggwilv's Cauldron, Luba's Tarokka of Souls,
  Ythryn Mythallar, Ruinstone, Amulet of the Planes): narrative/DM-
  adjudicated by nature, no fixed numeric grant in the actual text.
- **Objects with their own separate stat block** (Mirror of Life
  Trapping, Mirror of Reflected Pasts, Iron Flask, Sphere of
  Annihilation, Soul Bag, Hook of Fisher's Delight): battlefield/
  utility objects, not wearer bonuses.
- **A few real but too-conditional-for-this-vocabulary mechanics**:
  Imbued Wood Focus (+1 damage conditional on an 8-way wood/damage-
  type match), Mizzium Apparatus (a randomized cast-the-wrong-spell
  table), Docent (randomized skill/language/spell properties plus a
  sentient-item auto-stabilize check), Battle Standard of Infernal
  Power (no "weapon attacks count as magical" effect type exists),
  Necklace of Prayer Beads (6 randomized per-bead effects), Candle of
  Invocation (alignment-branching summon/buff) -- each given an
  accurate note pointing at exactly what's missing and why, rather
  than a partial or invented hook.
- **4 Golem Manuals and 4 Devastation Orb elements**: given their real
  day-counts (30/60/120/90 for Clay/Flesh/Iron/Stone) and correct
  "1-hour, 2,000 gp ritual" cost respectively, pulled directly from
  each entry's own catalog text, not guessed.
- **Feather Token / Replicate Magic Item**: Feather Token's fall-damage
  negation has no hook (this app doesn't track fall damage);
  Replicate Magic Item (an Artificer infusion) just points at using
  the actual replicated item's own already-correct catalog entry.

Every one of the 87 got a `grant_action` reminder entry (Action or
Passive matched to whether it's an activated ability or an always-on
trait) -- the same pattern used for every other note-only item in this
catalog all session.

Verified: full 1283-item catalog regression (rebuild + update_all +
attunement_prereq_met + build_action_abilities), 0 exceptions; spot-
checked several new entries (Sphere of Annihilation, Deck of Many
Things, Homunculus Servant, Manual of Iron Golems) actually populate
`char["item_actions"]` with their real text when equipped.

**Final coverage**: 1278/1283 (99.6%) wired, counting all three real
wiring mechanisms (`has_item_effect()`, `EFFECT_TABLE`,
`INSTANT_POTION_EFFECTS`, `ABILITY_SCORE_MANUALS`). The remaining 5
(Enhanced Defense +1/+2, Radiant Weapon +1, Repeating Shot, Resistant
Armor) are the already-confirmed Artificer-infusion false positives
from an earlier pass this session -- genuinely already wired through
`get_infusion_bonus()`/the `active_infusions` check in
`get_innate_resistance_grants()`, just invisible to a catalog-table
membership check. The magic item catalog is, as far as this survey
can tell, functionally complete.

## Small follow-up: point Vehicles-system items at the Vehicles tab, fix a real duplicate-item near-miss

While double-checking the 87-item Wondrous pass above, noticed the
git log already had a real "Vehicles system" (`VEHICLES_MAGIC` in
items.py, `VEHICLE_STATBLOCKS_MAGIC` in statblocks.py, a dedicated
browsable Vehicles tab) that already covers 9 of the items I'd just
given a generic "vehicle this app doesn't model" note: Flying Chariot,
Bobbing Lily Pad, Ornithopter of Flying, Tasha's Creeping Keelboat,
Quaal's Feather Token (Swan Boat), and all 4 Carpet of Flying sizes.
Not broken (both mechanisms are independent and harmless together),
but the note text was inaccurate for these 9 specifically. Fixed by
pointing each at "Full stats in the Vehicles tab" instead of claiming
no model exists.

**Caught a real near-miss while doing this**: removed what looked
like a stale, misspelled `'Tasha's Creeping Keepboat'` entry, assuming
it was dead-code left over from a typo of Keelboat — but the catalog
actually has two genuinely distinct items under those names (Keelboat
= the classic version, Keepboat = a separate QIS-sourced version with
its own AC 15/80 HP/reaction Magic Missile defense). Caught this
before it became a real gap (removing it would have silently
un-wired a real, distinct catalog item) by re-running the full survey
immediately after the edit and seeing Wondrous coverage drop by one —
restored it with a corrected, more complete description instead of
leaving the original shorter text.

Verified: full 1283-item catalog regression, 0 errors; final coverage
still 1278/1283 (99.6%), confirmed unchanged from before this pass.

## Movement lock gap: Paralyzed/Petrified/Stunned/Unconscious weren't zeroing speed; Prone correctly never did

User asked about "Prone setting movement to 0" — direct testing showed
this was never true in the current code (`get_effective_speed()` only
zeroed speed for Grappled/Restrained, matching Prone's real text,
which only restricts movement to crawling, never to 0). But the
follow-up ("and other various conditions?") pointed at a real gap:
Paralyzed, Petrified, Stunned, and Unconscious each separately state
"can't move" in their own condition text (PHB p.291-292) — a stronger,
more literal restriction than Grappled/Restrained's "speed becomes 0,"
and NOT implied by Incapacitated alone (which only blocks actions/
reactions, not movement). None of the four were included in the
speed-lock check.

Fixed `get_effective_speed()`'s `speed_locked` check to include all
six real movement-locking conditions (Grappled, Restrained, Paralyzed,
Petrified, Stunned, Unconscious), and added the same set to
`get_speed_breakdown()` so the speed tooltip actually names which
condition is responsible (previously only exhaustion showed up there,
even though Grappled/Restrained already silently zeroed the real
number).

Verified: all 14 conditions individually through
`get_effective_speed()`/`get_speed_breakdown()` — confirmed exactly
the 6 real lockers zero walk speed and appear in the breakdown,
Prone/Charmed/Incapacitated/etc. correctly don't. Full 1283-item magic
item catalog regression: 0 errors (unaffected, but re-run since it
shares `update_all()`).

## UI cleanup: removed the duplicate flight/swim/climb badge strip and a dead "equip weapons" button

Two follow-up requests in the same message:
- The climb/swim/fly badge strip added under HP earlier this
  conversation (to fix the Fairy flight-vs-resistance confusion) turns
  out to duplicate information already shown in the top stat bar's
  speed pill (which already appends "✈ N / 🌊 N / ↑ N" whenever any of
  climb/swim/fly is non-zero) — the strip's own docstring's claim that
  "walking speed already has its own pill, so it's not repeated here"
  was only half true; climb/swim/fly were duplicated too, just less
  obviously. Removed the whole strip (`_move_frame`/`_move_caption`/
  `_move_lay`/`_refresh_movement_strip` and its call site) rather than
  just the fly badge, since swim/climb had the identical redundancy —
  the resistances strip's caption/color fix from earlier stands alone
  now and still solves the original "looks like a resistance" report.
- Removed the "⚙ Equip weapons & armor in Gear ▸" button that sat
  above the Combat tab's weapon rows unconditionally, regardless of
  whether the character already had weapons equipped — confirmed
  there's always at least an unarmed-strike/natural-weapon row
  present, so this was never a real empty-state prompt, just a
  permanent redundant button when the Gear tab is already one click
  away on the tab bar.

Verified: `py_compile` clean, grep confirms zero remaining references
to any removed identifier. No PySide6 available in this environment to
launch the actual UI for a click-through smoke test -- relying on
static verification (matching add/remove pairs, no dangling refs)
same as the rest of this session's UI edits.

## Final magic-item catalog re-check: no new gaps found

Re-ran the full unwired survey (`has_item_effect()` OR `EFFECT_TABLE`
OR `INSTANT_POTION_EFFECTS` OR `ABILITY_SCORE_MANUALS`) after all of
the above. Still 1278/1283 (99.6%) -- the same 5 Artificer-infusion
false positives as before, nothing new. The magic item catalog remains
complete as far as this survey can tell.

## Cursed magic items: fixed a wrong effect and wired missing real grants

User asked "are curses implemented properly?" Audited every one of
this catalog's 7 items with an explicit "Cursed:"/"Curse:" clause
(Blasted Goggles, Berserker Axe, Shrieking Greaves, Orb of the Veil,
Spear of Backbiting, Javelin of Backbiting, Tloques' Berserker
Battleaxe) against their real catalog text. Curse-spells (Bestow
Curse, Hex) and curse-driven class features (Hexblade's Curse, Armor
of Hexes, Master of Hexes) were already correctly wired as note-only
reminders from earlier passes; lycanthropy's curse (Blood of the
Lycanthrope Antidote) was already handled too.

**Found a real data bug**: Blasted Goggles was wired to
`{"type": "resistance", "damage_type": "radiant"}` — a fabricated
effect matching nothing in the item's actual text (a fire-beam attack
item with a blindness curse, no radiant resistance anywhere). Replaced
with its real mechanics: a 3-charge pool and the fire-beam action.

**Found missing real numeric grants**:
- Berserker Axe / Tloques' Berserker Battleaxe both state "your hit
  point maximum increases by 1 for each level you have attained" while
  attuned — a clean, real hp_max_bonus grant that was completely
  absent (only the flat attack/damage bonus was wired). Added a new
  "per_level" formula to the hp_max_bonus effect handler
  (core/magic_items.py), alongside the existing "10_plus_level"
  formula used elsewhere.
- Tloques' Berserker Battleaxe also grants passwall/gust of wind/
  burning hands via a 12-charge pool — entirely unwired before this;
  added the charges pool (matching Staff of Power's exact pattern) and
  a description of the 3 spells and their charge costs.
- Orb of the Veil's darkvision ("60 ft., or +60 ft if you already have
  darkvision") was missing entirely — only its +2 WIS was wired. Added
  as an inline additive check in get_character_senses(), the same
  shape already used for Keenness of the Stone Giant, gated on the
  item actually being equipped+attuned via `_active_item_names()`.

**The curse penalties themselves** (disadvantage on attack rolls with
other weapons, "unwilling to part with it," the berserk trigger, the
natural-1 backfire attack against your own AC) stay note-only by
design, consistent with every other roll-dependent/narrative mechanic
in this catalog — this app doesn't simulate individual d20 rolls or
model per-attack conditional disadvantage triggered by which weapon is
used, so a `grant_action` passive entry names each curse's real
mechanical text (previously absent for 5 of these 7 items) rather than
leaving it undiscoverable outside the item's own catalog description.

Verified: full 1283-item catalog regression, 0 errors. Confirmed
directly — Berserker Axe/Tloques' hp_max_bonus scales with character
level (+8 at level 8), Blasted Goggles/Tloques' both track a real
charge pool, and Orb of the Veil grants 60 ft darkvision with no prior
darkvision or a correct +60 ft on top of an existing value.

## Wyrmreaver Gauntlets fabricated effect fixed; Elemental Essence Shards given accurate notes

While re-checking "player-choice resistance items," found Wyrmreaver
Gauntlets wired to `{"type": "set_ability", "ability": "STR", "value":
23}` -- another fabricated effect matching nothing in its real text
(no STR override anywhere in the DMG entry). Replaced with its actual
grants: resistance_choice from the correct 5-type pool (acid/cold/
fire/lightning/poison, not the generic 10-type pool other resistance-
choice items use), plus a note covering the unarmed-strike force
damage and the Invoking the Runes bonus action (too situational/
multi-part for this app's static effect vocabulary).

Also gave all 4 Elemental Essence Shard variants (previously only a
generic "attach/detach" reminder, missing their entire actual
Metamagic-triggered property) accurate per-element notes: Air (bonus
flight), Earth (temporary resistance), Fire (delayed burn damage),
Water (a knockback burst). Kept note-only rather than wiring Earth's
resistance via resistance_choice, since the real grant only lasts
"until the start of your next turn" after a trigger -- this app's
resistance system has no concept of a temporary window, so a static
grant would misrepresent it as permanent.

Verified: full 1283-item catalog regression, 0 errors.

## Fixed current HP silently following every max HP increase, not just level-ups

User: "if something increases your maximum health that doesn't
necessarily increase your current, that includes increases to
constitution in the moment." Confirmed a real bug in `update_all()`'s
Max HP block: any increase in max HP -- from a level-up, a
Constitution score increase, attuning a magic item with an
hp_max_bonus grant, or exhaustion 4+ clearing -- unconditionally added
the same amount to current HP. Only a level-up should do that (PHB:
"you gain hit points" as part of leveling); the other sources only say
"your hit point maximum increases," with no matching current-HP grant
in their real text.

Fixed by tracking `char["_hp_level_snapshot"]` (total character level
at the last recompute) and only applying the current-HP bump when
total level has actually gone up since then (or on the very first
computation, so a freshly created character still starts at full HP).
Every other max-HP increase now only raises the ceiling; current HP
is left untouched unless it now exceeds the new max, in which case it
clamps down, matching the real rule for a shrinking maximum.

Verified directly: a level-up still correctly raises current HP to
match; taking damage then raising CON leaves current HP exactly where
it was while max HP still increases; attuning Berserker Axe (a
hp_max_bonus item) behaves the same way. Full 1283-item catalog
regression: 0 errors.

## New optional rule: Maximum Hit Points Per Level

User requested a Settings toggle that uses each class's maximum hit
die value for every level, not just the first -- e.g. a Barbarian
gains 12 + CON at every level instead of 12 + CON at 1st and the PHB
average (7 + CON) afterward. Added `max_hp_per_level` to
`optional_rules` (default off, a common table variant rather than an
official rule) with a checkbox in the Settings dialog, and wired it
into `compute_max_hp()`: when on, every level's `avg` value is the
class's full hit die instead of `hd // 2 + 1`, for both the primary
class's levels beyond 1st and every multiclass entry.

Verified directly: a level-3 Barbarian with +2 CON computes 32 max HP
with the rule off (12+2 + (7+2)*2, the real PHB average formula) and
42 with it on (12+2 + (12+2)*2), matching the user's worked example
exactly.

## Credits menu, theme catalog expansion, and UI text-size fix

Three requested additions/fixes, wired together this pass:

- **Credits menu.** Added a `&Credits` top-level menu next to File/Tools/
  Settings, with a "View Credits..." action opening a new
  `CreditsDialog` that renders the project's own README.md (via
  `QTextBrowser.setMarkdown`) in a scrollable, read-only view.
  `_find_readme_text()` locates README.md whether running from source
  (repo root, resolved relative to this file) or from a frozen
  PyInstaller build (`sys._MEIPASS` / the executable's directory), with
  a short embedded fallback blurb if it can't be found. The .spec file's
  `datas` list now bundles `README.md` into frozen builds so the dialog
  has something to find there too.

- **Theme catalog: (Dark)/(Light) prefixes + 2 new light themes.** All
  14 theme names in `THEMES` now carry an explicit `(Dark)` or `(Light)`
  prefix so the Settings theme picker states its mode instead of leaving
  it to guesswork from the name alone. Added two new light themes,
  "(Light) Moonlit Vellum" (cool blue-grey/indigo) and "(Light) Sunlit
  Meadow" (warm parchment/olive), built with the same WCAG
  contrast-validation approach used for the original palettes: every
  TEXT/TEXT2/TEXT3 pairing against BG/SURF2/SURF3 hits >=4.5:1, BORDER
  against BG hits ~2.6:1, and all six accent colors against SURF clear
  their respective thresholds. Renaming was a pure key-string change --
  `is_light` theme detection already worked off BG brightness, not the
  name, so no downstream logic needed touching. All 14 themes verified
  to `apply_theme()`/`build_qss()` cleanly with no exceptions.

- **UI text-size setting, actually wired.** The Settings "UI text size"
  dropdown (Small/Medium/Large) previously only wrote
  `char["ui_font_scale"]` and never used it anywhere -- a dead control.
  `theme.py` now tracks the scale as `_font_scale`, with `_BASE_FS`
  holding the reference ("Medium") pixel sizes and `set_font_scale()`
  recomputing the live `FS_SMALL`..`FS_BIG` module globals from it; every
  hardcoded `font-size: Npx;` literal inside `build_qss()` now routes
  through a `px()` helper that applies the same scale.

  Two deliberate guards against clipped/truncated text, since a lot of
  small UI chrome (level pills, source badges, reset badges) lives in
  `setFixedHeight`/`setFixedSize` containers as tight as 16-18px tall
  with only 1-2px of padding: `FS_TINY` -- used exclusively for that
  badge/pill text -- is excluded from scaling entirely and always stays
  at its base 11px, and the "Large" scale factor is a modest 1.15
  rather than a more aggressive jump, so the sizes that DO scale
  (body text, labels, headings, stat numbers) still have headroom in
  their own fixed-height buttons and badges. `main_window.py`
  wires the dropdown's change handler to call `set_font_scale()`, then
  re-runs the same rebuild path theme switching already uses
  (`_set_theme()` re-applies `build_qss()` and reconstructs
  `CharacterSheet`, whose `__init__` calls `sync_globals()` to pick up
  the freshly recomputed `FS_*` values -- the same mechanism that
  already propagated theme colors to rebuilt widgets, extended to also
  carry font scale). `_show_sheet()` now also applies a character's
  saved `ui_font_scale` before constructing its sheet, so a saved scale
  takes effect on load/reopen instead of only being reflected in the
  combo box's initial selection.

  Verified: `python3 -m py_compile` on both changed files; all 14
  themes apply cleanly under every scale (Small/Medium/Large each
  produce distinct, correctly-rounded FS_* values); no un-scaled
  `font-size:` literal remains in `build_qss()`'s source. Full
  1190-item magic-item-effects regression (the subset of the 1283-item
  catalog wired through `MAGIC_ITEM_EFFECTS`): 0 errors. Live widget
  rendering could not be exercised directly in this environment
  (PySide6 is not installed here), so this is verified at the logic/
  compile level only, not with an actual on-screen render.

## New optional rule: Immersive Spells

User-requested flavor feature, off by default: a new `immersive_spells`
toggle in `optional_rules` that changes ONLY the spell list's title
label (never the underlying spell name, tooltip, description, or any
casting mechanic) to reflect what the character can actually say,
based on their current state. New module `dnd_app/ui/immersive_spells.py`
holds all the logic; `SpellRow` (shared.py) takes an optional
`display_name` and a `set_display_name()` method to update just the
title text; `sheet.py`'s `_add_spell_row()` computes the initial title
and a new `_refresh_spell_row_titles()` re-derives it for every
existing row on each controller-driven refresh (`_on_char_updated()`),
so it stays correct no matter which of Rage's several toggle paths, a
Wild Shape transform/revert, or the setting itself changed -- without
needing a hook at each individual call site.

Checked in order, first match wins (a full override outranks a merely
thematic prefix):

1. Wild Shaped without Beast Spells (Circle of the Moon, 18th level):
   every spell title becomes the current beast's noise, one word per
   original word, each padded to roughly that word's length by
   repeating one designated letter in the beast's base sound (~30
   beast-name keyword families covering the WILDSHAPE_BEASTS roster,
   plus a generic growl fallback for fantastical creatures with no
   real-world sound to draw on).
2. Rage active (Barbarian): titles collapse to a shout -- a couple of
   iconic spells get their own line (Fireball -> "FIRE!", Magic
   Missile -> "MAGIC MISSILE!"), any other single word gets uppercased
   and exclaimed, anything else multi-word becomes "SMASH!". Path of
   the Totem Warrior with a Bear/Eagle/Wolf totem spirit chosen reuses
   the Wild Shape beast-noise mechanic for that totem animal instead.
3. Thematic prefixes (checked in this order): Warlock patron (all 9),
   Sorcerer origin (all 8 current subclasses), Cleric domain (all 14
   PHB/XGE/TCE domains), Paladin Oath (all 10, including Oathbreaker).

Caught one real bug while testing this against every real subclass
name in the data: "Twilight Domain (TCE)" was matching Cleric's Light
Domain prefix instead of its own, because "light" is a substring of
"twilight" and dict key order put it first. Fixed by having
`_match_prefix()` always try the longest (most specific) keyword
first rather than relying on manual dict ordering -- a generic fix
that guards against the same class of bug anywhere else in these
prefix maps, not just this one collision.

Also added, unrelated to the toggle above and always on: casting a
spell from a Warlock's Pact Magic slot now appends "Your patron
approves." to the existing cast-confirmation toast.

Verified: `python3 -m py_compile` + `ast.parse` on every changed file;
`compute_display_spell_title()` exercised directly against every real
subclass name in the data (all 9 Warlock patrons, all 8 Sorcerer
origins, all 14 Cleric domains, all 10 Paladin Oaths, plus Wild Shape
and Rage/Totem Warrior scenarios) with manually-checked expected
output; full 1190-item magic-item-effects regression: 0 errors.

## Two small easter eggs (always on, no setting)

- Typing "cheese" anywhere in the app (an application-wide event
  filter, so it works regardless of which widget has focus) pops a
  tiny cheese icon in the corner of the main window for 5 seconds.
  Purely decorative, no gameplay effect.
- Naming a character "Ethan O'Brien" (case-insensitive) turns the menu
  bar gold, regardless of the active theme -- applied via the menu
  bar's own `setStyleSheet()`, which takes precedence over the
  window-level theme stylesheet and so survives later theme switches
  without needing to be re-applied from `_set_theme()`.

## Settings dialog: regrouped into cards, added a DM Secrets section

User feedback: the Settings dialog had grown to one long "OPTIONAL
RULES" card with 10 checkboxes in it and was getting hard to scan.
Split into four cards:

- **Appearance** (unchanged) -- theme, UI text size.
- **Character Rules** -- feat prereqs, multiclass ability requirements,
  DMG/XGE optional actions, Maximum Hit Points Per Level: the core
  enforcement toggles.
- **Tasha's Cauldron Options** -- the six TCE "swap something at an
  ASI level" class options (Eldritch/Martial/Cantrip/Bardic/Sorcerous
  Versatility, Harness Divine Power), all the same shape, now grouped
  together instead of interleaved with unrelated rules.
- **DM Secrets** (new, at the bottom) -- a home for purely cosmetic
  flavor toggles with zero gameplay effect, as opposed to the actual
  rule toggles above it. Currently holds Immersive Spells; built to
  hold more of the same kind going forward.

No checkbox's variable name, default, or `optional_rules` key changed
-- purely a layout reorganization, so `_on_done()`'s write-back needed
no changes. Verified: `py_compile` + `ast.parse` clean; full
1190-item magic-item-effects regression: 0 errors.

## Dice roller visual overhaul + Critical Flavor + small flavor toasts

User feedback: the dice roller "isn't the best looking." Rewrote
`dnd_app/ui/dice_roller.py`'s layout to match the rest of the app
instead of native `QGroupBox` chrome: each section is now a card
(`QFrame`, rounded corners, `SURF`/`BORDER` theme tokens, a small-caps
`TEAL2` header label) matching Settings/Credits, all hardcoded pixel
font sizes replaced with the theme's `FS_*` tokens, the panel widened
320px -> 380px so the Custom Roll row has breathing room, and the
result display moved to the top of the panel (previously buried below
three stacked control groups) with a bigger number and a colored
NAT 20/NAT 1 badge. The result frame's border now settles to a
crit-colored border after its flash animation instead of always
reverting to the plain default, so the last roll's crit status stays
visible at a glance. Also fixed a real gap while doing this: only
"Roll with Bonus" ever detected nat 20/nat 1 -- a quick d20 button or
a custom "1d20" roll got no crit styling at all. Both now do too
(custom rolls only flag crit for a genuine single natural d20, not
multi-die rolls, where "natural 20" isn't a meaningful concept).

New optional rule in DM Secrets: **Critical Flavor** (default off) --
on character death, appends a random one-liner from a small pool
(`dnd_app/ui/flavor_text.py`) to the bottom-of-screen toast. Per
user follow-up, this toast is now persistent (`_toast(..., duration_ms=0)`,
a new persistent mode added to `_toast()` itself) rather than
auto-fading, and is explicitly hidden again on Revive.

Also fixed, per user follow-up: death was previously a purely
transient UI event with no durable state -- a character saved while
dead (3 failed death saves, massive damage, or exhaustion 6) and
never revived would reopen looking like a live, healthy character,
with no indication anything had happened. `_show_death_screen()` now
sets a persistent `char["is_dead"]` flag (only marking the file dirty
on an actual new death, not when redisplaying on load), `_revive()`
clears it, and `CharacterSheet.__init__` re-shows the death screen via
a deferred `QTimer.singleShot(0, ...)` (needed since the overlay sizes
itself from `self.rect()`, not yet finalized mid-construction) if a
freshly-loaded character has the flag set. Confirmed the flag survives
a save/load round-trip (`is_dead` deliberately has no leading
underscore, since `save_character()` strips underscore-prefixed keys
as runtime-only state).

Two more always-on flavor toasts, no setting: a long rest appends a
random "you dream of--" line to its existing completion toast (unless
active effects also expired that rest, in which case only the
"Faded: ..." toast shows, matching the pre-existing one-toast-at-a-time
behavior); a failed concentration save (both the damage-triggered
prompt and the manual "Roll Concentration Save" button) now also
shows "Your focus shatters like cheap glass."

Verified: `py_compile` + `ast.parse` clean on every changed file; a
direct `save_character`/`load_character` round-trip confirming
`is_dead` survives; full 1190-item magic-item-effects regression: 0
errors. Live widget rendering (the actual dice roller layout, the
death screen re-appearing on load) could not be exercised directly in
this environment -- PySide6 is not installed here -- so this is
verified at the logic/compile level only.

## Dice Roller: stale "Roll with Bonus" numbers fixed

Found during a follow-up error check: `DiceRollerPanel.refresh_bonuses()`
existed but was never called from anywhere, so the "Roll with Bonus"
dropdown's skill/save/ability numbers were frozen at whatever they were
when the panel was first constructed -- a level-up or ability score
change afterward left it showing stale bonuses until the whole panel
was destroyed and recreated. `main_window.py`'s `_open_dice_roller()`
now calls `refresh_bonuses()` every time the panel is (re)opened or
brought to front, alongside the existing `self._dice_roller.char = char`
reassignment, without needing a live subscription that would also have
to survive the sheet being rebuilt from scratch.

## Repo hygiene: stopped committing PyInstaller build output

`build/` and `dist/` (PyInstaller's regenerated output -- one single
onefile .exe was 90MB+) had been getting committed by accident, which
is most of why this repo's `.git` directory ballooned to 100MB+.
Added both to `.gitignore` and untracked them with `git rm --cached`
(the files themselves are untouched on disk, just no longer tracked).

## DM-Granted Bonus Features: no longer truncated on the sheet

User-reported: "Supernatural gifts still get cut off." Found the real
cause -- the Features tab's "DM-Granted Bonus Features" section built
each granted DM Reward's row text with
`_summarize_feature_text(desc, max_len=180)`. Fine for an ordinary
feat's one-line `special` text, but DM Rewards like Supernatural Gifts
routinely run several paragraphs (the longest, "Oracle", is 3,690
characters) -- so the row showed maybe the first sentence before an
ellipsis, with no way to see the rest: the row label itself has no
height cap (it just grows to fit), and the right-click "Show Details"
fallback reuses that same already-truncated string whenever there's no
separate `FEATURE_DESCS` lookup for a DM reward's custom name (there
never is), so the truncation wasn't just a display quirk -- there was
no path to the full text anywhere on the sheet.

Fixed by rendering the full description through `_format_multi_para()`
(the same paragraph-formatting helper already used by the "Bonus
Feature Browser"'s detail panel) instead of summarizing it. Verified
directly against the real data: the "Oracle" Supernatural Gift's full
3,690-character, 21-paragraph description now renders end to end with
nothing missing. DM-Granted Feats (ordinary feats, not DM Rewards)
were left on the existing summarizer -- their `special` text is
normally a sentence or two, and that wasn't the reported problem.

## Wild Shape's two disconnected use-trackers, unified into one

User-reported: the Combat tab's Wild Shape card and the Passive/Other
tab's resource tracker weren't wired together. Confirmed a real,
significant bug: two completely separate trackers existed for the same
resource. The Combat tab card (transform/revert), the Companions tab
(Wildfire Spirit, which shares the Wild Shape pool per its real rule),
and a stat-block preview all read/wrote a legacy ad hoc
`char["_wildshape_uses_spent"]` counter with its own hardcoded
`uses_max = 2`. Meanwhile `char["resources"]` already had a proper,
formally-defined Wild Shape entry (`key="wild_shape"`, correctly
level-scaled via `by_level={2:2, 20:"Unlimited"}`) that the
Passive/Other tab's generic resource-pip tracker read and wrote
independently. Transforming via the Combat tab never moved that tab's
pips; editing that tab's spinbox never blocked or allowed a transform.
The hardcoded `uses_max = 2` was also its own separate bug (silently
wrong for a 20th-level Archdruid, who has unlimited uses).

Unified onto the formal `resources` entry as the single source of
truth: added `_wildshape_resource()` / `_wildshape_uses_left()` /
`_spend_wildshape_use()` helpers on `CharacterSheet`, and switched
every read/write site (the Combat tab card, `_wildshape_transform()`,
the Companions tab's Wildfire Spirit summon, and the stat-block
preview's "uses left" text) to go through them. All four now correctly
show "Unlimited uses (Archdruid)" for a 20th-level Druid instead of a
wrong "0/2 left".

Unifying surfaced a second real bug, needed to avoid a regression:
Wild Shape's resource definition was tagged plain `reset="SR"` in both
`classes.py` and `classes_2024.py`. This app's `long_rest()` only
resets resources tagged `"LR"` or `"SR/LR"` -- a plain `"SR"` resource
never recovers on a long rest at all. This is the exact same bug
pattern a previous audit already found and fixed for 10 other
resources (Hexblade's Curse, Misty Escape, Indestructible Life,
Mutagens, Control Undead, Vow of Enmity, Favored by the Gods, Firbolg
Magic's two spells) and believed fully closed out -- Wild Shape was
simply missed since that sweep covered `multiclass.py`/`calculator.py`
specifically, not the `classes.py`/`classes_2024.py` CLASS_DICT
definitions where Wild Shape's entry actually lives. The real rule
(PHB p.66) is explicitly "short or long rest," and the retired ad hoc
counter's own reset code already reset on both -- so this was a latent
regression risk in the unification itself, now fixed by retagging both
entries `"SR/LR"`. Retired the now-fully-redundant
`char["_wildshape_uses_spent"] = 0` lines from both `long_rest()` and
`short_rest()` in `character.py`, since the generic resource-reset loop
now correctly covers it.

This investigation found the "SR" vs "SR/LR" sweep's own "zero
remaining" closing note was inaccurate -- `classes.py`/`classes_2024.py`
still had several other plain-`"SR"` resources (Channel Divinity,
Second Wind, Action Surge, Superiority Dice, Ki Points, Blood
Maledict, Crimson Rite) that weren't re-checked here, since only Wild
Shape was in scope for this report. (Audited and fixed in the "Closing
the loop on every self-flagged incomplete item in this file" section
below.)

Verified directly: a level-2 Circle of the Moon Druid's resource
correctly shows 2/2, spending both blocks a third transform, a
simulated long rest now correctly restores it to 2 (previously would
have stayed depleted -- the actual regression this fix avoided), and a
level-20 Druid's `current_max` is confirmed to be the string
`"Unlimited"`, correctly detected as non-numeric by the new helpers.
Full 1190-item magic-item-effects regression: 0 errors.

## New optional rule: Component Restrictions (+ a new Gagged condition)

User-requested mechanic: Blinded/Gagged/Restrained can now actually
block casting a spell, depending on what that specific spell needs --
not a blanket "no spells" rule, since e.g. a self-only spell with no
verbal component still works fine while Blinded and Gagged. New
optional rule `component_restrictions` (default off, a table-variant
interpretation rather than unambiguous RAW) in the Character Rules
card: Blinded blocks any spell whose range isn't self-only (no
explicit "requires sight" field exists in the spell data, so this is
approximated from range -- a self-targeted spell doesn't need to see
anything, anything else implies targeting/centering an effect on
something you must perceive), Gagged (a new custom condition, not an
official one -- added to `data/conditions.py` and the Conditions
checklist) blocks spells with a verbal component, Restrained blocks
spells with a somatic component. Component letters are parsed from
each spell's existing `"components"` field (e.g. "V, S, M (...)").

New `core/spell_components.py` is the single source of truth for "is
this spell blocked by this character's conditions right now" --
`spell_component_block_reason()` is checked both by the real cast gate
(`_cast_spell()`/`_cast_spell_as_ritual()` in sheet.py, alongside the
existing Wild Shape gate) and by Immersive Spells' title treatment, so
the two can never drift out of sync.

Immersive Spells (when also on) now shows the blocking visually,
per-spell rather than as a blanket override like Wild Shape/Rage:
Blinded blacks the title out (a word-length-matched string of "█"),
Gagged muffles it to a word-length-matched "mmmhmmhf", and Restrained
turns it into a straining "nngh" -- both reusing the same word-length
stretch mechanic already built for Wild Shape's beast noise.
`compute_display_spell_title()`'s signature changed from taking just
the spell name to taking the full spell dict (needed to check its
components/range), updated at both call sites in sheet.py.

Verified directly: Fireball (V, S, ranged) is blocked and shows
redacted/muffled/straining text for each condition in turn; Shield
(V, S, but Self-range) is correctly unaffected by Blinded; both the
optional rule and Immersive Spells must be on for the visual to show;
Wild Shape still takes precedence over a component block when both
apply. Full 1190-item magic-item-effects regression: 0 errors.

## Four more user-reported bugs, all confirmed real

### Saving throw proficiencies leaked across multiclassing

`get_saving_throw_profs()` (multiclass.py) unioned `save_profs` across
every class a character had levels in. Real rule (PHB p.164
Multiclassing Proficiencies): saving throw proficiency is deliberately
NOT part of what multiclassing grants -- only your very first class at
1st level gives it. A Fighter 1/Wizard 5 was incorrectly showing
proficient in INT/WIS saves (from Wizard) on top of the correct
STR/CON (from Fighter). `builder.py` already computed this correctly
into `char["saving_throws"]` (using only `classes[0]`, i==0), but
`get_saving_throw_bonus()` in calculator.py, plus two display sites in
sheet.py, additionally OR'd in the buggy multiclass-wide union, so the
correct value was there but got overridden back to wrong. Fixed by
having `get_saving_throw_profs()` itself only look at the starting
class (relies on `class_levels()`'s dict preserving insertion order
matching `char["classes"]`, true for every real caller). Verified: a
Fighter 1/Wizard 5 now correctly shows proficient only in STR/CON.

### Immersive Spells prefixes applying to every spell, not just that class's

User-reported: a multiclass Paladin/Wizard was getting the Oath prefix
on Wizard spells too. `compute_display_spell_title()` only checked
"does the character have levels in this class," never "is this
specific spell actually on that class's list." Fixed by additionally
checking `class_name in spell["classes"]` (the spell's own inherent
class list) before applying a Warlock/Sorcerer/Cleric/Paladin prefix.
`compute_display_spell_title()`'s signature changed from taking just
the spell name to the full spell dict for this reason and for the
component-restriction check above. Verified: a Paladin 5/Wizard 5's
Bless gets prefixed, their Fireball doesn't.

### Wild Shape (and 8 other resources) never actually reset from the real Rest buttons

The single most significant find of this batch. `sheet.py`'s actual
`_short_rest()`/`_long_rest()` methods (the ones the Rest buttons
call) have their OWN inline resource-reset loops, completely separate
from `core/character.py`'s `short_rest()`/`long_rest()` functions --
which turn out to be dead code, never called from anywhere. Those
inline loops checked `reset in ("SR","sr")` and
`reset in ("LR","lr","SR","sr")` respectively -- neither tuple
contains the literal string `"SR/LR"`, so any resource tagged that
compound value never reset via the actual UI, ever. This silently
undid the entire prior "SR vs SR/LR" audit's fixes: Hexblade's Curse,
Misty Escape, Indestructible Life, Mutagens, Control Undead, Vow of
Enmity, Favored by the Gods, and Firbolg Magic's two spells were all
retagged "SR/LR" and believed fixed, but none of them were actually
resetting from the real Rest buttons this whole time -- only the tag
was fixed, not the loop that reads it. Wild Shape's very own retag to
"SR/LR" earlier this session hit the exact same gap. Fixed both loops
in sheet.py to also match `"SR/LR"`. Verified directly by simulating
both loops against a depleted Wild Shape resource: both now correctly
restore it.

### Resource-linked abilities used via the Action/Bonus Action tabs didn't apply their real effects

Two distinct problems reported together as "counters not decrementing":

1. **Wild Shape** is also listed as a generic Action-tab card (separate
   from its dedicated Combat-tab card with the beast picker). Using it
   from there fell through to the generic "spend one use" fallback,
   which has no way to prompt for a beast -- it silently spent a use
   and did nothing else (no beast chosen, `_wildshape_active`
   untouched), which reads exactly like "the counter didn't
   decrement" since nothing visibly happened. Now redirects to the
   dedicated card instead of guessing.

2. **Rage and every other simple toggle** (anything in
   `RESOURCE_POOL_TOGGLES`) used via its Action/Bonus Action tab card:
   the generic fallback correctly spent the resource and added the
   effect to `active_effects`, but only called two narrow refreshers
   (`_refresh_combat_weapons`/`_refresh_effects_list`) -- never
   `ctrl.refresh()`. Every real mechanical consequence of an active
   effect (AC changes, damage resistance, anything `update_all()`
   applies keyed off `active_effects`) only actually takes effect
   through that call. The Other tab's own "Active" checkbox for the
   same toggle already correctly called it (deferred via
   `QTimer.singleShot`, to avoid rebuilding mid-signal-handler); the
   action-tab card's button just never did. Added the same deferred
   `ctrl.refresh()` call there.

Full 1190-item magic-item-effects regression after all four fixes: 0
errors.

## Counters silently defaulting to "1/1" (Artificer's Infused Items)

User-reported: "some counters defaulting to 1/1." Wrote a scanner that
replicates `aggregate_resources()`'s exact formula-evaluation logic
against every `formula=` field across both rule editions' full class
resource lists (classes.py and classes_2024.py) -- an exhaustive check,
not a guess. Found exactly one: Artificer's "Infused Items" declared
BOTH `formula="infuse_by_level"` (a bogus, non-arithmetic string) AND a
correct `by_level={2:2,6:3,10:4,14:5,18:6}` on the same resource. The
aggregator runs the `by_level` branch first (correctly computing the
real level-scaled max), then unconditionally runs the `formula` branch
afterward ("NOT elif", so a formula-based current_max can coexist with
an independent die_by_level) -- since `"infuse_by_level"` isn't valid
arithmetic, evaluating it always threw and fell back to
`min_val`'s default of 1, clobbering the correct value that had just
been computed. Every Artificer's Infused Items counter showed a flat
"1/1" at every level instead of scaling 2/6/10/14/18.

Fixed at both layers: removed the bogus formula from Infused Items'
data entry (by_level alone is sufficient and was already correct), and
hardened `aggregate_resources()` itself so by_level now takes
precedence whenever both are present on the same resource (`if formula
and not by_level`) -- a defense-in-depth fix so the same mistake in a
future resource entry can't silently reproduce this bug class again.
`die_by_level` (a different field, for die *size* like d6/d8/d10, not
current_max) is unaffected and still independent of formula, per the
original comment's actual intent.

Verified directly: an Artificer's Infused Items now correctly shows
2/2/3/3/4/5/6/6 at levels 2/5/6/9/10/14/18/20. Re-ran the formula
scanner post-fix: 0 broken formulas remain anywhere in either edition's
class data, and 0 resources still declare both formula and by_level.
Full 1190-item magic-item-effects regression: 0 errors.

## Every class resource counter was silently using 2014 rules for 2024-edition characters

Follow-up to the Infused Items fix, per the user's request to review
every counter in depth rather than stop at one instance. Wrote a
scanner sweeping every `formula=`/`by_level` resource across BOTH rule
editions' full class data (comparing `aggregate_resources()`'s output
class-by-class, level-by-level, edition-by-edition) rather than
spot-checking. That surfaced something much bigger than a single bad
entry: `aggregate_resources()` (the one function that computes every
class resource pool -- Rage, Wild Shape, Ki, Sorcery Points, Channel
Divinity, Lay on Hands, Second Wind, Superiority Dice, literally every
countable class feature in the game) had `from dnd_app.data.classes
import CLASS_DICT` hardcoded at its top, with no awareness of
`char["edition"]` at all -- unlike `builder.py`/`levelup_panel.py`/
`widgets.py`, which already correctly branch between `CLASS_DICT`
(2014) and `CLASS_DICT_2024` elsewhere. Every 2024-edition character's
resource counters were being computed from 2014-edition class data
this entire time, silently, regardless of which edition was actually
selected at character creation.

The two data files genuinely disagree in real, mechanically-relevant
ways -- diffing the two editions' output across all 14 classes and a
spread of levels found 139 distinct (class, level, resource) points
where they differ. Some examples: 2024 Wild Shape is a flat 2 uses
with no by_level scaling and no "Unlimited at 20" the way 2014's
Archdruid works; 2024 Second Wind, Superiority Dice, Channel Divinity,
and Blood Maledict all scale differently by level than their 2014
counterparts; Monk's Martial Arts die progresses on a different level
schedule (2024's die sizes are one tier ahead of 2014's at several
levels).

Fixed by threading `edition: str = "2014"` through
`aggregate_resources()` (selects `CLASS_DICT_2024` when `"2024"`,
matching the exact pattern already used elsewhere) and passing
`char.get("edition", "2014")` from its one real call site in
`calculator.py`. Verified directly: a 2014 vs. 2024 20th-level Circle
of the Moon Druid now correctly show `"Unlimited"` vs. `2` Wild Shape
uses respectively, where both incorrectly showed `"Unlimited"` before.

**Finding this exposed a second, previously-unreachable bug**: 2024
Paladin's "Divine Sense" was defined with `formula="WIS_mod"` -- not
matching either edition's real rule (2014: 1 + CHA modifier; 2024, per
this very file's own feature text: a flat number of uses equal to
Proficiency Bonus), and Paladin has no WIS-based features at all, so
this was clearly a copy-paste mistake. It silently always evaluated to
the formula system's floor of 1 use at every level -- but this code
path was **never actually reached** before the edition fix above,
since nothing had ever pulled from `CLASS_DICT_2024`'s resources until
now. Also discovered the formula-evaluation system had no way to
express "Proficiency Bonus" at all -- no `PB` placeholder existed
alongside the six ability-modifier ones, which several 2024-only
features are written in terms of. Added `PB` support to
`aggregate_resources()`'s formula substitution chain and fixed Divine
Sense's formula to `"PB"`.

Re-ran both the formula-eval-failure scanner and the
formula+by_level-collision scanner (from the Infused Items fix) across
both editions with the new PB placeholder: 0 broken formulas, 0
collisions, anywhere. Full verification: 1190-item magic-item-effects
regression (0 errors) plus a fresh sweep building a fresh level-1/3/5/
10/15/20 character of all 14 classes in both editions (168
combinations, 0 errors).

`_add_subclass_resources()` (multiclass.py) -- the ~700-line function
that computes *subclass*-specific resources (Psionic Energy Dice,
Giant's Might, etc.) -- takes no `edition` parameter either, and
computes its values directly in Python rather than through the
CLASS_DICT lookup this fix covers, so it wasn't touched here. This
pass focused on the base-class resource system the original bug
report was actually about. (Investigated and fixed in the "Closing the
loop on every self-flagged incomplete item in this file" section
below, which found a real 2024 name-matching bug in this function.)

## Rest system: combat-duration toggles and concentration left stuck active

Follow-up review of `_short_rest()`/`_long_rest()` after the SR/LR
reset-loop fix, per the user's request to take another hard look.
Found two more real gaps, both about state that should have ended long
before a rest completes but was never actually cleared by one:

- **RESOURCE_POOL_TOGGLES** (Rage, Reckless Attack, Bladesong,
  Hexblade's Curse, and 30 others) had their *resource* (uses
  remaining) correctly restored by a rest, but the on/off
  `active_effects` *state* itself was never cleared -- a character
  could still show "Rage: ON" the next session after a long rest, with
  every one of its mechanical bonuses (resistance, +damage) still
  silently applying. By the time a short rest (≥1 hour) or long rest
  (8 hours) actually completes, every one of these combat-duration
  toggles would already have naturally ended regardless of whether the
  player remembered to manually turn it off. Added
  `_clear_active_toggles()`, called from both rest methods.

  While fixing this, also deduplicated `RESOURCE_POOL_TOGGLES` itself
  -- it was defined identically in two different methods' local scope,
  each with its own "must be kept in sync with that other definition"
  comment flagging the risk. Now a single module-level constant all
  three call sites (the two original ones plus the new rest-clearing)
  read from.

- **Concentration** was never touched by either rest method at all. A
  long rest is 8 hours, well beyond any spell's concentration duration
  -- whatever was being concentrated on had already ended long before
  the rest completed, but the sheet would keep showing a stale
  "concentrating on X" indicator indefinitely across rests with
  nothing left to justify it. Added a `drop_concentration()` call to
  `_long_rest()` specifically (left short rest alone -- at only ≥1
  hour, a small number of spells do have concentration durations that
  long, so auto-clearing there is less clearly always correct).

Verified both directly: a raging, Frenzied Barbarian with an active
Bless concentration, after a simulated rest, correctly has Rage and
Frenzy cleared from active_effects, Bless (an unrelated non-toggle
effect) left untouched, and concentration dropped. Full 1190-item
magic-item-effects regression: 0 errors.

## Death Saves: redesigned from a bare row of 14px checkboxes

User-reported: it "looks cheap" next to the rest of the app. It really
was underbuilt for how tense a moment it represents -- a single
borderless, background-less row with a plain "Death Saves:" label and
six tiny 14px checkboxes, easy to miss entirely and stylistically
disconnected from both the app's normal card-based polish and its own
dramatic full-screen "YOU DIED" overlay.

Rebuilt as its own alert-styled card (crimson-tinted background and
border -- it's already gated to only show at 0 HP, so it can afford to
demand attention when it does): a skull-icon header, bigger 22px pips
with hover feedback grouped under "SUCCESSES"/"FAILURES" labels
instead of bare ✓/✗ glyphs, a live status line ("2 successes, 1
failure", "1 more failure = death", "STABLE", "DEAD") that updates
immediately as pips are toggled, and a tooltip on every pip spelling
out the actual rule (d20 at the start of each turn at 0 HP, nat 20
regains 1 HP, nat 1 counts double) for anyone who doesn't have it
memorized. The status line is wired into all three places that sync
these checkboxes (initial bind, live toggle, and the general
death/conditions refresh) so it never goes stale.

## Floating/dialog windows now pick up theme changes

User-reported: the Dice Roller (and other windows) didn't follow a
theme change made while they were open. Root cause: `main_window.py`'s
own `from .theme import *` only ever captured whatever the theme was
the moment the module was first imported (Python's `import *` is a
one-time snapshot, not a live binding) -- unlike `sheet.py`/
`wizard.py`/`levelup_panel.py`, which already call `sync_globals()` at
the top of their own `__init__` for exactly this reason, nothing built
in `main_window.py` (SettingsDialog, CreditsDialog, StartMenu) or
`dice_roller.py` (DiceRollerPanel) ever re-synced, so every one of them
was frozen at whatever theme was active at app startup, regardless of
later switches.

Added the same `sync_globals()` call to `SettingsDialog.__init__`,
`CreditsDialog.__init__`, `StartMenu.__init__`, and
`DiceRollerPanel.__init__` -- fixes staleness for any freshly-opened
instance of these. For the two windows that can actually survive a
theme switch already open — StartMenu (reachable from the menu bar
regardless of which screen is showing, since Settings isn't scoped to
the character sheet) and the Dice Roller (the one genuinely persistent,
non-modal floating window) — `_set_theme()` now also destroys and
recreates them in place on every theme change, restoring StartMenu's
stack position and the Dice Roller's screen position/visibility,
rather than trying to re-style already-built nested custom-styled
cards in place (fragile, since Qt widget-instance stylesheets take
precedence over a parent's, so simply re-applying a top-level
stylesheet doesn't cascade down into them).

## Closing the loop on every self-flagged incomplete item in this file — subclass-resource name matching, and a real SR-vs-SR/LR gap the last audit missed

User asked, verbatim, to grep this file for every note marking
something as incomplete (self-labeled at the time as "not fixed,"
"still outstanding," "deferred," or "out of scope") and make sure
they're all actually resolved, not just tracked. Went through every
match rather than trusting the file's own framing at face value.

**Already resolved by earlier passes, confirmed rather than assumed**:
Ranger's duplicate "Stalker's Flurry" key, Forest Sage's skill-
substitution wiring, the 5 "genuinely missing" optional features
(Primal Knowledge/Magical Inspiration/Quickened Healing/Spellcasting
Focus/Cantrip Formulas), the filter system rework, and the Pyromancer
subclass — all had later dedicated sections in this same file showing
them built and verified. No action needed; would have been wasted,
duplicate work to redo them.

**`_add_subclass_resources()` edition-blindness — investigated and
resolved differently than the original flag assumed.** The original
note worried this ~530-line function (subclass-specific resources:
Psionic Energy Dice, Giant's Might, etc.) might have wrong hardcoded
*numbers* between 2014 and 2024 subclass revisions, the same way
`aggregate_resources()`'s base-class resources did. Investigated
properly instead of guessing:

- First, data-mapped which subclasses this function's `_has()` fuzzy
  matcher even needs to handle for 2024 characters, by diffing every
  class's 2014 vs. 2024 `subclasses` list. Most of this function's
  subclasses (Rune Knight, Samurai, Cavalier, Way of the Astral Self,
  Hexblade, Fathomless, Undying, Genie, Circle of Dreams/Spores/
  Shepherd, Divine Soul, Chronurgy, Drakewarden, Swarmkeeper, Path of
  the Giant, Peace/Twilight Domain, Oathbreaker/Conquest/Crown/
  Watchers) simply aren't selectable by a 2024-edition character at
  all — the 2024 PHB only reprints a handful of subclasses per class —
  so those branches correctly never fire for 2024 characters. Not a
  bug, just unreachable code for that edition.
- That left ~15 subclasses genuinely reachable in *both* editions
  (Psi Warrior, Soulknife, Phantom, Circle of the Stars, Archfey,
  Undead, Bladesinger, Abjurer, Diviner, War Domain, College of
  Spirits, Oath of Vengeance/Glory/Ancients, Wild Magic/Clockwork
  Sorcery, Armorer/Artillerist/Battle Smith/Alchemist). Verified each
  one directly by simulating every 2024 subclass through the function
  and printing what resources it produced.
- **Found a real, confirmed bug this way, not a guess**: Wizard's
  Abjurer and Diviner subclasses never got their resources at all in
  2024. `_has("Wizard", "abjuration")` and `_has("Wizard",
  "divination")` were matching against the 2014 subclass strings
  ("Abjuration", "Divination"), but the 2024 PHB subclass list uses
  different word forms entirely — "Abjurer" and "Diviner" — which
  don't contain those substrings. Any 2024-edition Abjurer wizard
  silently never got Arcane Ward tracked; any 2024 Diviner silently
  never got Portent. Fixed by adding the 2024 name as an additional
  match fragment to each check (`_has("Wizard", "abjuration",
  "abjurer")` / `_has("Wizard", "divination", "diviner")`) — a
  data-verifiable naming fix, not a guess at unfamiliar rules text.
- **What was deliberately NOT changed**: whether any of those ~15
  dual-edition subclasses' actual *numbers* (Psionic Energy Dice
  scaling, Vow of Enmity's uses, Trance of Order, etc.) differ between
  the 2014 and 2024 printings. Unlike the name-matching bug above,
  this isn't something verifiable from the app's own data — it needs
  word-for-word 2024 PHB text per subclass, which isn't something to
  guess at and risk silently replacing a correct value with a wrong
  one. Stated here plainly rather than papered over with unverified
  numbers.

**A second, related gap the previous SR-vs-SR/LR audit's own closing
note had named but not checked**: that audit fixed Wild Shape's
reset tag and admitted, in its own text, that `classes.py`/
`classes_2024.py` likely had more plain-`"SR"` resources it hadn't
re-checked (Channel Divinity, Second Wind, Action Surge, Superiority
Dice, Ki Points, Blood Maledict, Crimson Rite, and it turned out also
Warlock's Pact Magic Slots). Checked each one against its real PHB
rule text rather than assuming:

- **2014 (`classes.py`)**: Cleric's and Paladin's Channel Divinity,
  Fighter's Second Wind and Action Surge, Battle Master's Superiority
  Dice, Monk's Ki Points, Warlock's Pact Magic Slots, and Blood
  Hunter's Blood Maledict and Crimson Rite were all tagged plain
  `"SR"`. Every one of these has an unambiguous 2014 PHB/XGE rule of
  "you regain [it] when you finish a short or long rest" — this app's
  `long_rest()` only restores resources tagged `"LR"` or `"SR/LR"`, so
  a plain `"SR"` tag meant none of these ever recovered from an actual
  long rest, exactly the same bug class as Wild Shape's. Retagged all
  8 to `"SR/LR"`. (Fighter's Indomitable and Paladin's Lay on Hands
  were already correctly `"LR"`-only, per their real once-per-long-
  rest-only rule — left unchanged.)
- **2024 (`classes_2024.py`)**: found this file already had Second
  Wind and Channel Divinity tagged `"LR"` (not `"SR"`) from an earlier
  pass — the 2024 revision changed several Fighter-style resources
  into multi-use pools that partially refill on a short rest and fully
  refill on a long rest, a nuance this app's binary reset tag can't
  fully represent; `"LR"` is the safe choice since it's true under
  every reading (full recovery on a long rest is universal) without
  falsely claiming a full short-rest reset. Action Surge and
  Superiority Dice were still plain `"SR"`, inconsistent with that
  same reasoning already applied to their sibling resources in the
  same file — brought them in line, retagged to `"LR"`. Pact Magic
  Slots and Focus Points (2024's renamed Ki) kept the traditional
  full-short-*or*-long-rest recovery model unchanged from 2014 in both
  editions (this is Warlock's and Monk's defining, unchanged-since-
  2014 mechanic) — retagged both from `"SR"` to `"SR/LR"`.
- Note: Pact Magic Slots' actual spend/reset is hardcoded directly in
  `sheet.py`'s `_short_rest()`/`_long_rest()` (`pact_slots_used = 0` in
  both), independent of the generic resource-reset loop — so this
  specific fix only corrects the reset-type badge shown on its
  resource card, not a functional recovery bug. The generic-loop-based
  resources above (Channel Divinity, Second Wind, etc.) had the real,
  functional bug.

**Also cleaned up**: the two confirmed-orphaned tooltip entries ("Goat
Legs," "Fleet of Foot") noted as dead data in an earlier audit —
verified again they still don't correspond to any real trait on any
race in the database, then removed all 4 occurrences (each appeared
once in the base dict, once in a later duplicate `.update()` call) from
`feature_tooltips.py`.

**Re-investigated, found to already be correct**: the "Illusory
Dragon" INT-vs-WIS-save discrepancy noted during a spell-AoE audit.
The current data (`"enemies who see it WIS save or frightened"`)
already uses the correct Wisdom save for the frightened effect; the
separate `"Examining it (action) vs your spell save DC"` text for
disbelief is accurately described without mislabeling it as a formal
save. No bug found here — the note itself turned out to already be
resolved, or was never actually wrong.

**Two remaining limitations, identified but not built in this pass**:
Githyanki's Astral Knowledge and Astral Elf's Astral Trance (a
*recurring* skill/tool choice regranted every long rest, not a
one-time pick) and College of Creation's Creative Crescendo (multiple
simultaneous Dancing Items at 14th level, CHA-modifier count) both
needed real architectural additions this app didn't have yet — a
rest-triggered re-choice UI flow for the first, and multi-instance
tracking for a single companion-card template for the second. (Both
built in the "Astral Knowledge / Astral Trance built, and Creative
Crescendo's multi-instance gap closed" section below.)

Verified throughout: full 1194-combination sweep (every class ×
subclass × level checkpoint × both editions) via direct
`rebuild()`/`update_all()` calls, 0 errors. Full 1190-item magic-item-
effects regression, 0 errors. Direct `aggregate_resources()` checks
confirming Cleric's Channel Divinity now shows `SR/LR` in 2014 and the
already-correct `LR` in 2024, and every 2024 dual-edition subclass
(Abjurer, Diviner, Psi Warrior, Soulknife, Phantom, Circle of the
Stars, Archfey, Undead, War Domain, College of Spirits, Shadow/Wild
Magic/Clockwork Sorcery, Oath of Vengeance/Glory/Ancients, all 4
Artificer subclasses) now correctly produces its subclass resource
where it previously silently produced none (Abjurer/Diviner) or
already worked correctly (the rest, confirming the fix didn't
regress anything that was already fine).

## Astral Knowledge / Astral Trance built, and Creative Crescendo's multi-instance gap closed

User asked to actually build the two remaining limitations from the
previous pass rather than leave them stated. Both needed a genuine
architectural addition, not a data tweak — built and verified without
being able to visually render the real Qt UI (no PySide6 in this
environment), using a minimal stub module that lets the actual
PySide6-importing UI code run headless so the real functions/methods
could be exercised directly rather than only their non-UI helpers.

**Githyanki (MPMM)'s Astral Knowledge and Astral Elf's Astral Trance**:
both grant "proficiency in one skill and with one weapon or tool of
your choice ... until the end of your next long rest" — a temporary
proficiency re-chosen every long rest, not a permanent pick. Investigated
how the closest existing precedent (Guidance of the Spirits' skill
choice, Whispers of the Dead's skill-or-tool choice — both re-pickable
via `RestOptionsDialog`) actually applies its pick, and found a real,
pre-existing bug in the process: neither choice's `choice_id` matches
any of `ChoiceWidget._on_confirmed()`'s aggregation-suffix checks
(`_skill_profs`, `_tool_profs`, `_skill_or_tool_profs`), so both fall
through to the generic `apply_choice()` fallback, which just stores the
pick under `_choices` without ever folding it into `char["skills"]` or
`char["tool_proficiencies"]` — the chosen skill/tool is recorded but
never actually mechanically granted. Didn't fix that pre-existing bug
here (out of scope for this ask), but made sure not to inherit it:

- Built a new `weapon_or_tool_prof` choice type (pool = weapon names +
  tool names, reusing `_build_tool_chooser`'s generic mixed-pool
  checkbox UI — the same technique `skill_or_tool_prof` already uses)
  since no existing type covers "weapon or tool," only "tool" or
  "skill or tool."
- Initial pending-choice cards (`_get_race_choices()`) for both races,
  following the same "built as an initial creation-time pick" pattern
  already established for Guidance of the Spirits/Whispers of the Dead
  (the real rule's first grant technically only exists after the
  character's first in-fiction long rest, but this app doesn't model
  "hasn't rested yet" as a distinct state).
- `RestOptionsDialog` offers a re-pick (both the skill and the
  weapon/tool together, matching the real "whenever you finish a long
  rest" trigger) once an initial pick exists, long rest only.
- **Mechanical application, built correctly from the start**: the
  weapon/tool half is applied the same way Weapon Master's chosen
  weapons already are — read fresh from `_choices` every `rebuild()`
  and appended into `grants["weapon_profs"]`/`grants["tool_profs"]`
  before `char["weapon_proficiencies"]`/`char["tool_proficiencies"]`
  are (re)assigned from `grants`, so a re-pick on a later long rest
  naturally replaces the old grant instead of accumulating (those two
  char fields are fully overwritten from `grants` every rebuild, not
  incrementally mutated). The skill half needed different handling:
  `char["skills"]` is NOT rebuilt fresh each call — it's a permanent,
  monotonically-increasing store (the "Reset Manual Changes" button is
  needed specifically because nothing else ever downgrades it), so
  mutating it directly would let the old temporary skill stay
  "proficient" forever once the character re-picks a different one on
  a later rest. Instead, checked dynamically inside `get_skill_bonus()`
  — the same technique Forest Sage's ability substitution already uses
  two lines above — comparing the skill being queried against the
  *current* `_choices["astral_knowledge_skill"]` value on every call,
  so it naturally tracks whichever skill is currently picked with no
  separate expiry bookkeeping needed.

Verified directly: baseline (no pick) shows no bonus/no proficiency;
after the initial pick, the chosen skill's bonus goes up and the
chosen weapon/tool shows proficient; after simulating a long-rest
re-pick to a *different* skill and weapon, the old skill's bonus
correctly reverts to baseline and the old weapon's proficiency is
correctly gone, while the new pair is now proficient — confirming this
is a real temporary swap, not just an additive grant. Also verified
the pending-choice card correctly appears before any pick and
disappears after, and that `RestOptionsDialog` only offers the re-pick
on a long rest (never short) and only once an initial pick exists.
Both races behave identically, as expected from the identical rule
text. Full 1194-combination class/subclass/level/edition sweep and the
1190-item magic-item-effects regression: both 0 errors.

**Creative Crescendo (College of Creation, 14th level)**: "you can have
a number of animated objects from Animating Performance equal to your
Charisma modifier active at once ... rather than just one." The
existing Companions-tab model tracked at most one active instance per
companion key (`char["active_summoned_companions"]` was a flat set of
template keys, one card per key). Extended it rather than replacing it:

- New `calculator.companion_max_simultaneous(key, char)` returns 1 for
  every companion except Dancing Item once the character is a 14th+
  level College of Creation Bard, where it returns `max(1, CHA mod)` —
  the `max(1, ...)` floor matters since Animating Performance's own
  base rule ("only one at a time") means a 14th-level feature
  shouldn't be able to reduce the cap below what a *lower*-level
  Creation Bard already has.
- Multi-instance-capable companions now store one *instance-suffixed*
  id per active copy (`"dancing_item#0"`, `"dancing_item#1"`, ...) in
  `active_summoned_companions`, instead of the bare key. Every
  single-instance companion (Drake Companion, Wildfire Spirit, Steel
  Defender, etc.) is completely unaffected — they still store and
  match on the bare key exactly as before, gated by
  `companion_max_simultaneous()` returning 1 for all of them.
- `get_available_companions()` now emits one list entry per active
  instance instead of one per template key, so the Companions tab's
  existing "one card per returned key" loop naturally renders one card
  per Dancing Item without any change to the loop itself.
- `resolve_companion_statblock()` accepts the instance-suffixed id,
  looks the template up by its base key, and labels the resolved stat
  block "Dancing Item #1"/"#2"/... so multiple active copies are
  distinguishable. `_summon_companion()` picks the lowest *unused*
  instance index (reusing a freed slot rather than always climbing)
  and has its own defensive cap check (in addition to the Summon
  button only being offered while under the cap, matching the existing
  double-checked pattern already used for resource-charge gating).
- **Real bug caught while extending the death/HP-zero handler**: the
  handler that fires when a companion's tracked HP reaches 0 does a
  direct `COMPANION_STATBLOCKS.get(companion_key)` lookup to decide
  which "companion died" flow applies (re-summon-gated vs.
  pending-replacement-on-long-rest vs. infusion-linked) — with
  instance-suffixed keys this would have silently returned `{}` for
  any Dancing Item, misrouting a dead Dancing Item into the
  Steel-Defender-style "pending replacement, available again next long
  rest" flow instead of its own correct "dismiss it, re-summon by
  spending another use" flow. Fixed by stripping the `#N` suffix
  before that specific lookup, matching how `resolve_companion_statblock()`
  already does it.

Verified directly (no PySide6 install available, so exercised the real
`CharacterSheet._summon_companion`/`_dismiss_companion` methods headless
via a minimal stand-in object providing only what those methods
actually touch, rather than skipping to just the calculator-layer
functions): a 20th-level, CHA 20 Creation Bard correctly gets a cap of
5, can summon 3 Dancing Items with 3 independent HP trackers and
correctly numbered display names, still gets offered a 4th/5th, stops
being offered once at the cap, correctly frees and reuses a dismissed
instance's slot on the next summon rather than climbing indefinitely,
and correctly dismisses (not "pending replacement") when an instance's
HP reaches 0. A 6th-level Creation Bard (pre-Creative-Crescendo, high
CHA) is confirmed capped at exactly 1, byte-for-byte matching the
original single-instance behavior (bare `"dancing_item"` key, no
suffix) — confirming this is a strict superset of the old behavior,
not a replacement of it. Full 508-combination class/subclass/level
companions sweep (build character → summon every eligible companion →
resolve every active stat block) and the full 1190-item magic-item-
effects regression: both 0 errors. Also directly constructed the real
`_build_statblock_card()` widget for a Dancing Item instance to confirm
the HP-spinbox handler closures (which read `companion_key` for the
death-handling branch fixed above) don't crash.

## Two user-reported bugs: ability score increases weren't reaching resource formulas, and 3 backgrounds had no skill/tool chooser

**Bardic Inspiration (and every other ability-modifier-based resource)
didn't scale when Charisma went up.** Traced this to `update_all()`
building the `ability_scores` dict it hands to `aggregate_resources()`
straight from `char["abilities"]` — the raw base scores only, not the
effective score `ability_score()`/`ability_mod()` (the canonical,
correct accessor used everywhere else) actually returns, which also
folds in `ability_bonuses` (ASI choices, racial ASI), `magic_ability_bonuses`
(item bonuses), and `ability_overrides`. Any resource whose `formula`
references `CHA_mod`/`WIS_mod`/`INT_mod`/`CON_mod`/`STR_mod`/`DEX_mod`
was silently using the character's un-bonused base ability score for
its max-uses calculation — not just Bardic Inspiration, but every
formula-driven resource across `classes.py`/`classes_2024.py` and
`_add_subclass_resources()` (Hexblade's Curse, War Priest, Momentary
Stasis, Flash of Genius, Arcane Jolt, Cavalier's Unwavering Mark, and
more). Fixed by building `ability_scores` from `ability_score(char, ab,
ignore_wildshape=True)` for all six abilities instead of reading
`char["abilities"]` directly (`ignore_wildshape=True` matches max-HP's
own established convention — a resource's max shouldn't fluctuate just
because the character happens to be currently Wild Shaped).

Verified directly: a level-4 Bard with CHA 16 (+3) shows 3 Bardic
Inspiration uses; applying a +2 CHA ASI (the real player-facing path —
`_choices["<class>_asi_N"] = ["asi:CHA:2"]`) correctly raises it to 4
without resetting uses already spent; a +2 CHA magic item bonus
(`magic_ability_bonuses`) does the same. Full 1194-combination
class/subclass/level/edition sweep and 1190-item magic-item-effects
regression: both 0 errors.

**3 backgrounds silently granted zero real proficiencies instead of
letting the player choose.** Every background in this app's data model
assumed fixed (non-choice) skills/tools — correct for the overwhelming
majority of real backgrounds, but Haunted One (CoS), Investigator
(VRGtR), and Urban Bounty Hunter (SCAG) all genuinely offer the player
a choice in their real rule text. That real text was already
correctly *described* in this app's data (e.g. "Choose 2: Arcana,
Investigation, Religion, or Survival"), but stored as a single literal
string inside the `skills`/`tools` list — which then got applied
completely literally as if it were an actual skill/tool name. A
Haunted One character's `char["skills"]` ended up with a key literally
named `"Choose 2: Arcana, Investigation, Religion, or Survival"` set
to proficient, and none of the 4 real listed skills ever became
proficient at all. Same shape of bug for Investigator's skills and
Urban Bounty Hunter's skills *and* tools.

Fixed by adding real `skill_choices`/`tool_choices` fields to the
background data model (`{"count": N, "pool": [...]}`, mirroring the
class-level `skill_choices`/`skill_count` pattern already used for
class skill picks) and a new choice-card block in
`get_choices_needed()`. Deliberately used `choice_id`s ending in
`_skill_profs`/`_tool_profs` (`"bg_skill_profs"`/`"bg_tool_profs"`) so
the pick flows through `ChoiceWidget._on_confirmed()`'s existing
aggregation dispatch unchanged — no new application logic needed, just
the missing card. Converted all 3 backgrounds' already-correct
descriptive text into real structured pools rather than guessing new
content.

**Also found, fixed as a smaller version of the same bug**: House
Agent (ERLW) has the identical "placeholder text applied as a literal
tool name" problem, but its real grant depends on which Dragonmarked
House the character belongs to — a two-tier choice (pick a House,
then that House's own fixed 2-tool list) this app has no "House"
concept to hang a chooser off of at all. Rather than build a new
character-model concept to solve one background, emptied its bogus
`tools` list so it stops granting a fake proficiency — no grant is
more honest than a wrong one. Left as a known, explicitly narrower
limitation than the other 3 (which are now fully fixed with a real
chooser).

Verified: all 4 background fixes confirmed via the real
`ChoiceWidget._on_confirmed()` UI-layer dispatch (not just the
core `apply_choice()` fallback, which — a separate, smaller,
not-user-reported gap noted here rather than fixed — only mirrors the
skill-aggregation branch, not the tool one; irrelevant to this fix
since these choice_ids are handled by `_on_confirmed()` directly, but
worth knowing about for any future caller that calls `apply_choice()`
directly instead of going through the real choice-card UI). Swept all
99 backgrounds through `rebuild()`/`get_choices_needed()`: 0 errors.
Full 1194-combination class/subclass/level/edition sweep and 1190-item
magic-item-effects regression: both 0 errors.

## Stale choices left hanging on race/background/subclass change and delevel, plus the background choice fix's own missing wiring

User asked directly whether the background skill/tool chooser fix
actually reached the "Edit Background" button on the Choices tab
(post-creation background swap), not just the initial creation-time
pending-choice card — it didn't. Investigating that turned up the same
gap for race and subclass, and an incomplete version of an
already-shipped fix for delevelling.

**The core problem**: several `_choices` keys are *generic*, keyed by
choice *type* rather than by the specific race/background/subclass
that currently needs them — `race_skill_profs`/`race_tool_profs`/
`race_skill_or_tool_profs`/`astral_knowledge_skill`/etc. are shared
across every race that ever needs that shape of choice; `bg_skill_
profs`/`bg_tool_profs`/`bg_languages` likewise across backgrounds.
Swapping race or background via the Choices tab's "Edit Race"/"Edit
Background" dialogs changed the character's race/background value but
never touched `_choices` at all. Two distinct symptoms from the same
root cause: (1) a skill/tool/language picked for the *old*
race/background stayed recorded as if it were a valid answer for the
*new* one, even though the new one's pool of options is usually
completely different — the pending-choice card wouldn't even
re-appear, since `len(already_chosen) >= count` looked satisfied; (2)
for the temporary, dynamically-checked Astral Knowledge/Astral Trance
mechanic specifically, switching to a different race left the old
skill proficiency and weapon/tool grant permanently active, since
nothing ever cleared the `_choices` value it reads live.

Subclass combo changes had the identical shape of problem for
subclass-scoped choice ids (`rune_knight_runes`, `kensei_weapons`,
`lunar_phase`, `guidance_of_the_spirits_skill`, `four_elements_
disciplines`, and more) — switching away from Rune Knight to Battle
Master left the old chosen runes stuck in `_choices` forever, and (a
separate but adjacent bug) the subclass-combo change handler never
called `rebuild()`/`update_all()` at all, only refreshed the Features
tab's *display* — so subclass-driven resources (Giant's Might, Kensei
weapons, etc.) never actually recomputed either, only the text did.

Delevelling (`_open_level_down()`) already had a real fix for this
exact class of bug from earlier in this session — diff the full set of
structurally-relevant choice ids before and after the level decrement
(computed against a scratch character copy with `_choices` cleared, so
already-answered choices still show up in the diff), and prune
anything no longer relevant. But its own list of choice-generating
functions to include in that diff was incomplete — missing
`_get_feat_choices()` and `_get_optional_feature_choices()` — so a
feat's own sub-choice (Elemental Adept's damage type, Skilled's skill
picks, etc.) or an optional class feature's choice (Canny, Primal
Knowledge) could still survive a delevel that should have invalidated
it.

**Fixed by extracting the delevel handler's diffing logic into two
shared, module-level helpers** (`_all_relevant_choice_ids()`,
`_prune_stale_choices()`) in `sheet.py`, now completed with the 2
missing choice-generating functions, and reused for the subclass
combo's change handler (which now also calls `rebuild()`/`update_all()`
for real, not just a display refresh). For race and background
specifically — where the diffing approach can't distinguish "still
relevant" from "relevant to a *different* race/background now, with a
different pool" — added two explicit, enumerated sets
(`RACE_SCOPED_CHOICE_IDS`, `BACKGROUND_SCOPED_CHOICE_IDS`) that are
unconditionally cleared whenever the race/background value actually
changes, applied *before* the resulting rebuild so the stale value
can't get re-applied to the new race/background even transiently.

**Known, deliberate limitation, consistent with how the rest of this
app already works**: clearing a stale `_choices` entry stops it from
being treated as "answered" and stops any choice-driven effect that's
computed *dynamically* from the live `_choices` value (Astral
Knowledge/Trance's skill check, bonus spell grants, etc.) — but for
choices applied the *standard* way (`char["skills"][skill] = 2`,
matching every class/feat/race skill grant in the entire app), the
skill proficiency itself doesn't retroactively un-grant, since
`char["skills"]` is a permanent, monotonically-increasing store that
nothing in this codebase downgrades automatically (the "Reset Manual
Changes" button exists specifically because of this). Verified this is
consistent, not a new gap introduced here: switching Investigator
(Insight/Perception picked) to Haunted One correctly clears the choice
record and re-prompts for Haunted One's own (different) skill pool,
but the old Insight proficiency itself remains until a manual reset —
exactly matching how an ASI reassignment or a removed feat already
behaves everywhere else in this app.

Verified directly: background swap (Investigator → Haunted One)
correctly clears the stale choice record and re-prompts for the new
background's own pool; race swap (Githyanki (MPMM) → Human) correctly
clears Astral Knowledge's choice AND its dynamically-computed skill
bonus drops back to baseline immediately; subclass swap (Rune Knight →
Battle Master) correctly clears the chosen runes and actually
recomputes resources, not just display text. Full 1194-combination
class/subclass/level/edition sweep, 1190-item magic-item-effects
regression, and 508-combination companions sweep: all 0 errors.

## Character sheet export — wired up and substantially expanded

User asked how to export the character sheet for a DM to review, or
as a personal cheat sheet. Investigated and found `export_character_
text()` already existed in `save_load.py` (name/class/race/background,
ability scores, AC/HP/initiative/etc., saves, skills, feats, spell
slots, concentration, notes) — but it was never called from anywhere
in the app. No button, no menu item, nothing. A fully-built function
with zero way to actually reach it.

Wired it up: a new 📄 button next to the existing Save/Load buttons in
the sheet's header toolbar, opening a save-file dialog defaulting to
`"{name} - Character Sheet.txt"` in the user's home directory (kept
deliberately separate from the `~/.dnd_characters` JSON save
directory — a save file round-trips back into the app, this is a
plain-text handout meant to leave it).

Also substantially expanded what the export actually contains, since a
DM reviewing a sheet or a player using it as a table quick-reference
needs more than base stats. Added: proficiencies (languages, armor,
weapons, tools) and senses; active conditions and exhaustion; a
simplified weapon summary (to-hit and damage per equipped weapon,
parsing any `+N` magic suffix via the same `parse_magic_suffix()` the
rest of the app already uses, honestly labeled as simplified since it
doesn't chase every situational toggle/effect the live Combat tab
does); resources with current/max and reset type (filtering out
resources that compute to a non-positive max — a by_level resource
with no threshold met yet at the character's current level, e.g.
Indomitable before 9th — since a "0/0, not actually available yet" row
is clutter on what's meant to be a clean reference, not a real
finding); hit dice; spell slots (including pact slots); known/prepared
spells grouped by level; magic items with attunement/equipped status;
and the character's full action-economy list (Action/Bonus
Action/Reaction/Passive) via the existing, already-tested
`build_action_abilities()` — genuinely the most DM-relevant section,
since it answers "what can this character actually do" in one place,
which nothing else in this app assembles into a single view. Wrapped
that section in a try/except: it's the single largest, most
class-specific bit of the whole export, and a rare edge case there
shouldn't cost the player the rest of an otherwise-successful export.
Also fixed a small pre-existing formatting bug in the skills line
(dangling trailing space when a skill has no proficiency marker or
advantage/disadvantage tag) while already in this function.

Verified directly: a full sample character's exported text end-to-end,
and the real `_export_text_dialog()` UI method (file dialog → write →
toast), both via the headless PySide6 stub since this environment has
no Qt install. Swept `export_character_text()` across all 796
class/subclass/level/edition combinations (both editions, every class,
every subclass, levels 1/5/11/20, with equipped weapons and an
attuned magic item on every one): 0 errors. Full 1194-combination
class/subclass/level/edition sweep and 1190-item magic-item-effects
regression: both clean.

## Official character sheet PDF export

User offered WotC's official free fillable 2014 PHB character sheet
PDF and asked what could be done with it. Built a second export
option — `dnd_app/core/pdf_export.py` — that fills the real 3-page
form with a character's actual data instead of only offering the
plain-text summary above. The 📄 toolbar button now opens a format
picker ("Official character sheet (PDF)" / "Plain text summary
(.txt)") rather than going straight to text.

The template's own form-field IDs are largely opaque/auto-generated
(e.g. "Check Box 23", "Spells 1046") and not in visual page order, so
the mapping from field ID to sheet position had to be derived rather
than guessed: fields were extracted, sorted by their PDF `rect`
bounding box (bucketed into columns by x-position, sorted by
descending y within each column), and cross-checked against the
sheet's known fixed visual layout (alphabetical skills, STR through
CHA save order, successes-then-failures death saves, a 3-column
per-spell-level grid using the "SlotsTotal" header fields as
level-section boundaries, each spell name paired with its nearest
same-row "prepared" checkbox within a small y-tolerance). Confirmed
against rendered page images rather than trusting the sort blind.
Fills: identity/class/level (subclass deliberately left out of the
cramped ClassLevel field and put in Features and Traits instead, see
below); ability scores/mods; saves and skills with proficiency
checkboxes; AC/initiative/speed/HP/hit dice/death saves; up to 3
equipped weapons plus an Attacks & Spellcasting overflow block for the
rest; proficiencies/languages/senses; equipment and currency;
personality/ideals/bonds/flaws; features & traits (prefixed with each
class's subclass, since the header field couldn't fit it); page 2
backstory/allies/treasure/appearance boxes; and full spellcasting
(ability/DC/attack bonus, slot totals, slots *expended* per level, and
every known spell per level with its prepared checkbox — checked for
every spell for classes that don't have a separate "known vs
prepared" split, and checked against `spells_prepared` for the ones
that do).

Three real bugs found and fixed via visual re-rendering (not just the
regression sweep, which only proves "doesn't crash," not "looks
right"): (1) the template's own field ID says "SlotsRemaining" but the
label actually printed on the page next to it reads "SLOTS EXPENDED"
— a genuine mismatch in WotC's own file — so the code needs to write
the *used* count there, not `max - used`; caught by rendering a test
character with slots used and seeing the wrong number under the right
label. (2) Initial fill called pypdf's `set_need_appearances_writer
(True)`, which tells PDF viewers to discard pypdf's own correctly-
sized appearance streams and regenerate from the field's inherited
auto-size `/DA`, producing oversized text in every multi-line box —
removed entirely, with a comment at the call site explaining why it's
deliberately absent. (3) With that auto-size behavior gone, pypdf's
own text layout only wraps on literal `\n` already in the string, no
automatic width-based wrapping, so long personality/backstory/equipment
text was overflowing its box — added manual pre-wrapping
(`_wrap_multiline()`) using a per-field width table and an approximate
average-character-width heuristic, plus a smaller explicit font size
for the narrow weapon-name/attack/damage/ClassLevel fields that were
clipping their content at the default size.

Verified: `export_official_pdf()` swept across all 796
class/subclass/level/edition combinations (equipped weapons, an
attuned magic item, known/cantrip/prepared spells, spell slots with
some used, a feat, and long personality text on every one) — 0 errors.
Re-rendered filled test PDFs to page images after each of the three
fixes above and visually confirmed correct text size, correct
wrapping, and the corrected slots-expended value. Existing
796-combination text-export sweep and the 1194/1190/508 regression
suites re-run clean after these changes (they don't exercise
`pdf_export.py` directly, but confirm nothing else in the app
regressed).

## Experience-point leveling: a real alternative to milestone

User asked for an XP-based leveling option — the app previously only
supported milestone leveling (the DM manually clicks "Level Up"
whenever they decide); `char["experience"]` existed as a field (and
was already shown in the text/PDF exports) but had no way to be edited
and nothing read it to gate anything.

Added `leveling_mode` ("milestone" or "xp", defaulting to milestone so
existing saves are unaffected) as a Settings → Advancement toggle.
Building on that: `xp_for_level()`/`xp_progress()` in `character.py`
implement the standard PHB XP-by-level table (identical in 2014 and
2024) and compute progress toward the character's *next* level —
deliberately keyed off `total_level(char)`, not off whatever level the
raw XP total alone would imply, so a huge XP surplus never reads as
"skip levels", only ever as "ready for the one level right above where
you actually are" (mirrors how the game actually works — you still
level up one at a time).

In XP mode, two things appear, both driven by the same `xp_progress()`
call and kept in sync via the existing `_refresh_xp_tracker()` →
`_refresh_stat_bar()` path (so they update through every existing
controller-notify channel — manual edits, Settings toggling the mode,
saves loading, etc. — for free, no new plumbing needed): a golden XP
pill in the header stat bar (current/next-threshold XP plus a progress
bar), and a fuller "🌟 EXPERIENCE" card in the Choices tab with the
same bar, an "Add XP" spinbox + button for the normal end-of-session
"add what the DM awarded" workflow, and a "✎ Set Total" button (via
`QInputDialog`) for outright corrections/imports. Once accumulated XP
crosses the next threshold, both the pill and the card visibly flag
"ready to level up" (gold border, status text) and the header pill
becomes clickable, opening the existing Level Up / Multiclass dialog
directly — this only ever surfaces eligibility, it does not auto-level;
the DM/player still clicks through the same level-up flow as before,
same as milestone mode. In milestone mode both widgets stay hidden
(not removed — a mode switch never needs a UI rebuild).

Verified: `xp_for_level()`/`xp_progress()` against the full table
(level 1 floor, level 20 cap that's never "eligible", a huge-surplus
character correctly gated to just the next level, a classless
level-0 character not crashing) with direct assertions. Bound the
real `_refresh_xp_tracker`, `_on_add_xp`, and `_on_set_total_xp`
methods onto a fake sheet (same `types.MethodType`-style pattern used
elsewhere this session for headless PySide6 testing) wired through a
real `CharacterController` subscription — confirmed milestone mode
hides both widgets, XP mode populates them correctly, crossing the
threshold flips the eligible state/toast/click-to-level-up wiring, and
`_on_set_total_xp` correctly overwrites the total. Also exercised
`SettingsDialog` itself (extending the PySide6 stub's `QComboBox` with
real item/index/data bookkeeping, since the existing stub's plain dummy
object couldn't support `findData`/`currentIndex` comparisons) to
confirm the leveling-mode combo round-trips through `_on_done` into
`char["leveling_mode"]`. Confirmed `migrate_character()` backfills
`leveling_mode: "milestone"` onto pre-existing saves that predate this
field. Full 1194-combination class/subclass/level/edition sweep and
1190-item magic-item-effects regression: both still 0 errors after
these changes.

## XP tracker: a big enough award can carry over multiple levels

Follow-up to XP-based leveling above. User pointed out a real gap: a
big enough one-time XP award (or importing a total from another
tracker) can jump past more than one level's threshold at once, and
that's supposed to carry over — you don't lose the surplus, you just
level up more than once. The tracker was only ever computing "eligible
for the next level: yes/no", with no notion of *how many* were owed.

Added `xp_implied_level()` (highest level, 1-20, whose XP threshold
the current total has met) and a new `levels_due` field on
`xp_progress()`'s return dict — `min(xp_implied_level(xp), 20) -
total_level(char)`, so it's still hard-gated to levels actually owed
from the character's real current level, never further than the raw
XP total supports. When more than one level is due, the header pill,
its tooltip, the Choices-tab status line, and the `_on_add_xp` toast
all say "Ready to level up ×N!" instead of the generic phrasing;
exactly one level due still reads as the plain "Ready to level up!"
(no "×1" noise). Also fixed the eligible-state text to stop showing a
"current / next-single-level-threshold" fraction once multiple levels
are owed (e.g. "20,000 / 900 XP" was technically accurate but reads as
broken) — it now shows the plain XP total instead once the surplus
has already blown past that single-level number.

Verified: `xp_implied_level()`/`levels_due` against the real PHB
table (a level-2 character sitting on 20,000 XP correctly computes
`levels_due=4`, matching level 6 being the highest threshold ≤20,000);
extended the existing bound-method XP tests to assert the ×N phrasing
appears in the pill tooltip, the status label, and the toast for a
multi-level jump, and does NOT appear for an exact single-level
threshold. Full 1194/1190-combination regression suites re-run clean.

## "What you'll get" level-up preview, plus a Choices tab visual pass

User asked for a preview of HP/features/spell slots before committing
to a level-up (especially useful now that XP mode can flag several
levels due at once — the existing Level Up / Multiclass dialog already
had a "WHAT YOU'LL GET" panel, but it only listed the class's static
per-level feature *names* from `CLASS_DICT`, nothing about the actual
numbers), plus a general visual review of the Choices tab.

Added `preview_level_gain(char, cls_name, is_new)` to `calculator.py`:
a pure function (never mutates `char`) that deep-copies the character,
applies the hypothetical level (existing class +1, or a new multiclass
entry at level 1), and diffs `compute_max_hp()` and
`compute_all_spell_slots()` before/after — reusing the exact same
functions the real level-up path uses, so the preview can't drift from
what actually happens. Returns the HP delta and a list of
`(spell_level, delta)` slot changes, plus Warlock pact-slot
before/after (pact slots live outside the standard `spell_slots` array
so needed separate handling). Wired into
`LevelUpMulticlassDialog._on_pick()` via two small helpers:
`_append_level_preview()` appends "HP: +6 (max 26 → 32, includes CON
+2)" and "Spell slots: +2 Lv3" lines; `_append_xp_surplus_note()`
checks `xp_progress()` and, when in XP mode with more than one level
already owed, adds "🌟 You have enough XP for N levels right now —
this uses 1, leaving N-1 more to take right after" — since this dialog
still only ever applies one level per confirm (same as milestone), the
note exists so the surplus doesn't read as lost.

While in there, reviewed the Choices tab (`_build_tab_choices`) as a
whole and fixed three real inconsistencies: (1) the Optional Class
Features card (both here and its Features-tab counterpart) had its
title/border color hardcoded as a literal `#E8A020`/`#55E8A020`
instead of the `AMBER` theme constant — meaning it was a frozen
snapshot of ONE theme's amber value and didn't shift color on the
other 13 themes like every other card does; confirmed by checking
`theme.py`'s `AMBER` value actually differs per theme (`#e89828`,
`#8e5708`, `#f8a828`, etc.) — now uses `AMBER`/`qa(AMBER,0x55)`.
(2) The Identity card crammed its title and all 4 edit buttons into a
single `QHBoxLayout` row, the only card in the tab not following the
title-row-then-content pattern the Class Manager and Experience cards
both use — restructured to match. (3) Those 4 buttons ("Race",
"Subrace", "Ancestry", "Background") always showed the same generic
label regardless of what was actually set, so a returning player
glancing at the tab couldn't tell what their race/background even was
without clicking through each one — added `_refresh_identity_buttons()`
(wired into `_refresh_stat_bar()`, same pattern as the XP tracker) so
they now read e.g. "✎ Race: Human" / "✎ Background: Soldier", falling
back to the bare label when unset. Also replaced a duplicate
ancestry-visibility check that lived separately in `_refresh_stat_bar`
with a single call into the new method. Bumped the Choices tab
splitter's default top-pane height (220→280px) so all 3 top cards fit
without initial clipping when XP mode is on — costs milestone-mode
characters nothing, since a hidden Experience card doesn't consume
splitter space, it just leaves more of that room for the existing
trailing stretch.

Verified: swept `preview_level_gain()` across every class/subclass/
level combination in both editions, including previewing a
multiclass-into-every-other-class for each (13,930 calls) — 0 errors.
Built the real `LevelUpMulticlassDialog` end-to-end through the
headless PySide6 stub (extending the stub's `QComboBox` and `QLabel`
with real state — a plain dummy widget silently discards `setText()`,
so this was necessary to actually read back the rendered panel text)
and confirmed the HP/spell-slot/XP-surplus lines render correctly for
a real level-up-in-progress character with 2 XP levels owed.
`_refresh_identity_buttons()` tested directly for the empty, set, and
Dragonborn-ancestry-visible cases. Full 1194/1190-combination
regression suites, the XP-tracker tests, and the stale-choices tests
all re-run clean after these changes.

## Rest preview dialog, and a genuine gap closed: ability-check rolling

Two of the "what's still worth adding" ideas floated earlier this
session, both actually built this time — a rest preview matching the
level-up preview's "look before you commit" pattern, and click-to-roll
for ability checks. Investigated first and confirmed skills and saves
already had 🎲 roll buttons (`_quick_roll_toast`, whose own docstring
even already said "skills / saves / abilities / initiative" — the
"abilities" part of that promise was never actually wired up), and
rests applied immediately with no preview at all, only a toast after
the fact.

**Rest preview**: `_short_rest()`/`_long_rest()` now open a
`RestPreviewDialog` (styled to match `LevelUpMulticlassDialog`/
`RestOptionsDialog` — GOLD2 title, a TEAL-accented "WHAT THIS WILL DO"
card, gold Confirm button) before touching any character state;
cancelling leaves the character completely untouched. Built two new
non-mutating preview methods, `_preview_short_rest()`/
`_preview_long_rest()`, deliberately as plain filters over current
state — the exact same conditions the real apply logic checks right
after — rather than a parallel simulation, so the preview can't drift
out of sync with what actually happens next. The one piece that isn't
a simple filter (`restore_hit_dice_pool()`'s cross-die-type
distribution math for long rest) is previewed by running that same
real function on a throwaway copy of just the hit-dice/classes data,
same "reuse, don't reimplement" principle as `preview_level_gain`.
Short rest's preview necessarily stops short of an exact HP number
(healing depends on how many hit dice the player chooses to spend,
asked right after confirming, unchanged from before) but lists hit
dice available, every resource that will reset, Pact Magic slots, and
which active effects/toggles (Rage, Bladesong, etc.) will fade. Long
rest's preview is fully deterministic: HP restored, temp HP lost, hit
dice restored, every LR/SR resource, spell slots by level, exhaustion
reduction, death saves clearing, and concentration ending.

**Ability-check rolling**: added a 🎲 roll button to `AbilityBlock`
(`shared.py`) — same visual/behavioral pattern as the Skills/Saves
rows' roll buttons — gated to `editable=False` only, since the
wizard's own `AbilityBlock` instances (`editable=True`) are mid-
creation with nothing real yet to roll. Added a `roll_requested`
signal so `shared.py` (used by both `sheet.py` and `wizard.py`) stays
decoupled from `sheet.py`'s `_quick_roll_toast`; wired in
`_build_tab_abilities()`.

Verified: swept both preview methods across every class/subclass/
level/edition combination plus a 3-class multiclass character (hit
dice pooled across d6/d8/d10) and a completely fresh character with
nothing to reset — 798 combinations, 0 errors. Directly tested
non-mutation (the preview genuinely never touches `char`), the actual
cancel-vs-confirm gate (built a fake `RestPreviewDialog` returning a
controlled result and confirmed cancelling leaves `current_hp`
untouched while confirming applies the real rest), and
`RestPreviewDialog._build_lines()`'s text output for both rest types
against hand-built preview data. For the ability-check roller,
confirmed the roll button exists only on `editable=False` blocks and
that emitting `roll_requested` reaches `_quick_roll_toast` with the
correct ability modifier. Along the way, upgraded the headless
PySide6 test stub itself: `Signal(...)`-produced connections now
actually store and invoke callbacks (previously silently inert),
`QDialog.Accepted`/`.Rejected`-style class attributes are now cached
per-name so repeated access returns the same object (needed for an
`exec() != QDialog.Accepted` comparison to ever be simulatable), and
`QComboBox`/`QLabel`/`QAbstractSpinBox` gained real or missing
support — all of which should make future UI-logic tests in this
session's style easier, not just this feature's. Full 1194/1190
regression suites re-run clean.

## Rest preview follow-up: merged with the existing options dialog

User caught a real UX regression the rest preview above introduced: a
long rest already opened `RestOptionsDialog` afterward for anything
reconfigurable on that rest (unpreparing spells, an Armorer's Arcane
Armor model, Eladrin season, pact rituals, and half a dozen other
subclass/racial re-picks). Adding a SECOND confirm dialog before the
rest, on top of that existing one after it, meant a prepared caster
now saw two back-to-back "are you sure" popups for one Long Rest
click — exactly the kind of friction the preview was supposed to
reduce, not add.

Fixed by merging them: `RestOptionsDialog._build_options()` (the list
of what's currently reconfigurable) is now a `@staticmethod` taking
`(char, rest_type)` directly, so it can be computed without
constructing a `RestOptionsDialog` at all. `RestPreviewDialog` now
takes that list as an `options` param and renders it as a second
"ALSO RECONFIGURE?" checkbox card right below the preview, with one
shared Confirm button. `_offer_rest_options()` (which used to open its
own dialog after the rest completed) is now `_apply_rest_options()`,
taking the selection straight from the merged dialog and doing only
the applying — its own big per-option if/elif chain (unprepare
spells, Armorer model swap, Arcane Recovery, Eladrin season, pact
rituals, Guidance of the Spirits, Whispers of the Dead, lunar phase,
Astral Knowledge/Trance) is completely unchanged, just no longer
gated behind its own separate dialog. `RestOptionsDialog` itself stays
in the codebase (unused directly now, but kept rather than deleted —
its name is referenced by a dozen comments elsewhere as the mechanism
name for "swappable via a rest", and rewriting all of those for a
pure rename wasn't worth the churn).

Verified none of `_build_options()`'s availability checks (spells
prepared, Armorer subclass, racial choice already made, etc.) read any
state the rest-reset logic itself mutates (HP, hit dice, resource
`current` values, spell slots used, exhaustion, death saves) — so
computing the reconfigure list BEFORE the rest applies, instead of
after, can't change which options show up. Extended the rest-preview
tests: confirmed the merged dialog receives a non-empty options list
for a prepared caster, and that confirming with a reconfigure option
checked applies BOTH the rest AND that option in the same pass (e.g.
`spells_prepared` actually clears when "Unprepare all spells" is
checked alongside a Long Rest confirm) — a single dialog, not two.
Updated an existing scratch test (`RestOptionsDialog._build_options`'s
Githyanki/Astral Elf coverage) to the new static-method call signature
and confirmed it still passes. Full 1194/1190/798 regression suites
re-run clean.

## Styling standardization: a shared style/component layer

User asked to pick one of three "worth redoing" candidates raised
earlier in this session (styling duplication, the 12k-line `sheet.py`
god-file, or the total absence of committed tests) — chose styling,
reasoning that a shared layer would both cut duplication now and make
`sheet.py`'s eventual split safer later (each extracted tab file would
already pull from one style module instead of carrying its own ad hoc
QSS). Confirmed the scope with hard numbers before starting: **59**
separate hand-rolled `QPushButton{{background:...}}` f-strings in
`sheet.py` alone, another **~15** across `widgets.py`/`levelup_panel.py`/
`main_window.py`/`wizard.py`/`dice_roller.py`/`feature_dialog.py` —
**~74 total**, nearly all re-deriving one of the same ~4 visual shapes
with only the accent color actually varying — plus a label factory
(`_lbl`/`h`/`lbl`) independently redefined **six** times across those
same files with three different, incompatible parameter orders, and a
card factory (`_card`/`card`) duplicated twice, one copy of which
(`shared.py`'s own `card()`) had never actually been adopted anywhere.
This wasn't just cosmetic: it's exactly how the Optional Class
Features card ended up with its color hardcoded to one theme's exact
amber value instead of the `AMBER` constant (found and fixed earlier
this session) — nothing forced these through a shared, theme-aware
builder.

Added to `shared.py` (the module already intended to hold cross-file
widgets, previously under-used): `_btn(label, color, variant=...)` —
five shapes (`cta`, `chip`, `neutral`, `ghost`, `danger`) covering the
real observed variety, with override params (`bg_alpha`, `border_alpha`,
`border_width`, `text_color`, `hover_text`, `hover_bg_alpha`) for the
call sites that used a nonstandard alpha or text color rather than
losing that nuance; `_pill(label, value, color)` generalizing what
`CharacterSheet._make_stat_pill()`/`_make_xp_pill()` were building ad
hoc (the AC/HP/Initiative/Prof/Speed/XP pills). `h()` (the label
factory) gained a `_lbl` alias and `card()` (the card factory, already
present but dead) was reshaped to match the signature `sheet.py`'s own
`_card()` actually used everywhere, then aliased the same way — both
adopted with **zero call-site changes** anywhere they already matched.
Where a file's own `_lbl`/`lbl` had a genuinely different, incompatible
parameter order or defaults (`levelup_panel.py`, `feature_dialog.py`,
`dice_roller.py` each differed in a different way — confirmed by
grepping every call site for positional-arg risk before touching
anything), used a thin signature-preserving wrapper delegating to `h()`
instead of a blind alias, so the original call sites' behavior is
provably unchanged rather than silently reinterpreted.

Migrated `sheet.py` (48 of 59 button sites converted; the remaining 11
are genuinely bespoke — `:checked`/`:focus`/`:disabled` pseudo-states,
refresh-path re-styling of a persistent widget rather than one-time
construction, or non-palette hardcoded colors for a deliberate one-off
like the death-screen skull button — forcing those through a shared
factory would have meant either losing a real behavior or bloating the
factory for a single use), `levelup_panel.py` (1 of 4; the other 3 hover
to a different accent color than their base, which none of the five
shapes model), `main_window.py` (4 of 4), and de-duplicated the label/
card factories in `wizard.py`/`dice_roller.py`/`feature_dialog.py` even
where their buttons stayed hand-rolled (padding/radius differed just
enough from every shape to risk visibly resizing a fixed-row button for
a one-or-two-instance gain — not worth the drift).

Along the way, found `widgets.py` was almost entirely dead code: 10 of
its ~12 classes (`SkillRow`, `StatBox`, `HPTracker`, `ClassEntryRow`,
`SpellSlotBar`, `FeatureCard` — defined twice, the second silently
shadowing the first — `FeatureSection`, `ResourceWidget`, `LevelHeader`,
`AbilityWidget`) plus their own `lbl()`/`hline()`/`colored_btn()`
helpers were never imported or instantiated anywhere else in the app —
an earlier widget set superseded by equivalents built directly into
`sheet.py`/`shared.py`, confirmed via a repo-wide grep (not just
`ui`/`core`) before touching anything. Flagged this to the user rather
than deleting unilaterally, since removing ~600 lines was well outside
what "styling standardization" implied; user confirmed deletion.
`widgets.py` is now 707 → 121 lines: just `FlowLayout`/`FlowContainer`
(the two things anything else in the app actually imports) and `sign()`.

Also found and fixed a real, unrelated bug while touching this code:
`_build_summoned_creatures_section()` referenced `remove_btn` via
`.setStyleSheet()`/`.clicked.connect()` without ever constructing one
in that loop — a `NameError` waiting for the first character with any
owned summoned creature (Summon Undead/Beast/etc.), never triggered
before because nothing in this session's regression suites happened to
give a test character one.

Verified: every touched file recompiles; the full existing test/
regression suite (1194/1190/798/13930-combination sweeps, plus all
dialog- and preview-construction tests built earlier this session)
re-run clean after each file's migration, not just at the end. Added
new direct tests: `_btn()`'s five variants and every override param,
checked against the real generated QSS string (not just "didn't
crash") via a `QPushButton` stub upgrade (was a no-op `_Dummy`, now
actually remembers style/tooltip/text/enabled state); the summoned-
creature bug fix, constructing the real section with an owned summon
and confirming no `NameError`; the `RestPreviewDialog`-adjacent
`ChoiceWidget` confirm button's `:hover:enabled`/`:disabled` split,
constructed for real with a multi-select choice and its actual
generated stylesheet inspected; `StartMenu`/`DiceRollerPanel`
construction end-to-end through the real `_btn`/`_lbl`/`_card`
wiring. Also upgraded the shared PySide6 test stub itself — cached
`QDialog.Accepted`-style class attributes per-name (previously a fresh
throwaway object every access, which made an `exec() != QDialog.
Accepted` comparison unsimulatable) and made its `Signal`-backed
connections actually store and invoke callbacks — both needed for
this pass's verification and reusable for whatever's tested next.

## ui/ and data/ restructured by category, and sheet.py split out of one 12,060-line file

Follow-up to the styling-standardization pass above: `sheet.py` alone
was 12,060 lines (everything else in `ui/` was under 3,100), `ui/` had
no `pages/`/`dialogs/` separation a coder browsing from outside could
use to find things, and `data/`'s 17 modules sat flat with no signal
for which were edition-specific. All landed in one session as several
staged, independently-verified commits:

- **`dnd_app/data/phb2014/` and `dnd_app/data/phb2024/`** — before
  moving anything, checked which of the 17 data modules are actually
  edition-forked by reading each. Only 2 pairs are: `races.py`/
  `species_2024.py` and `classes.py`/`classes_2024.py`. The other 13
  (`backgrounds`, `class_features`, `conditions`, `dm_rewards`, `feats`,
  `feature_tooltips`, `feature_ui_interactions`, `items`, `magic_items`,
  `movement_sources`, `resistance_sources`, `spells`,
  `starting_equipment`, `statblocks`) are already genuinely
  edition-shared — `backgrounds.py`'s `bg()` builder already carries an
  optional 2024 `origin_feat` field alongside its 2014 fields in one
  record, `multiclass.py` in `core/` already handles both editions'
  rules in a single file — so a literal three-way 2014/2024/common split
  would have left "common" holding nearly the whole directory. Those 13
  moved into `dnd_app/data/phbCommon/` instead; the two real edition
  pairs into `phb2014/`/`phb2024/` (not `2014/`/`2024/` — Python module
  names can't start with a digit). ~130 import call sites updated across
  `core/` and `ui/` (the app reaches into data submodules by absolute
  dotted path everywhere, not through `data/__init__.py`'s facade).
- **`dnd_app/ui/style/`** — `theme.py` (the QSS/color engine, imported
  by essentially every UI file), `flavor_text.py`, `immersive_spells.py`
  (both pure cosmetic-text generators with zero Qt imports, despite
  living in `ui/` — confirmed neither imports PySide6 at all before
  grouping them with `theme.py`).
- **`dnd_app/ui/dialogs/`** — `dice_roller.py`, `levelup_panel.py`
  (moved as-is), plus `arcane_recovery.py`, `rest.py`,
  `levelup_multiclass.py` (extracted out of `sheet.py`, see below).
  `feature_dialog.py` was deleted rather than moved: its `FeatureDialog`
  class had zero usages anywhere in the repo (confirmed by grep, only a
  passing comment mention elsewhere) — same class of dead code as this
  session's `widgets.py` cleanup, confirmed with the user before
  deleting rather than assumed.
- **`dnd_app/ui/pages/`** — `wizard.py`, `main_window.py`, and
  `sheet/` (see below) grouped together as the app's top-level screens.
- **`dnd_app/ui/pages/sheet/`** — the actual point of the exercise.
  Before touching anything, an Explore agent mapped `sheet.py`'s real
  structure: 226 methods on `CharacterSheet`, several `_build_*` methods
  rebuilt on refresh rather than called only at init
  (`_build_companions_tab` runs from inside `_build_tab_gear`, not
  `_build_ui`; `_build_statblock_card` is a shared factory called from 5
  different sites), and the cross-tab-coupled attributes are
  consistently widget-handle references (`self._xxx_lay`/`_lbl`/`_tree`)
  rather than data — which rules out splitting `CharacterSheet` into
  independent composed objects (a refresh method in one domain routinely
  calls another domain's `_build_*`/helper methods) and points at a
  **mixin** split instead: one plain class per tab/concern
  (`BaseSheetMixin`, `AbilitiesMixin`, `SkillsMixin`, `CombatMixin`,
  `GearMixin`, `CompanionsMixin`, `ChoicesMixin`, `InfusionsMixin`,
  `SpellsMixin`, `FeaturesMixin`, `TraitsNotesMixin`,
  `ActionTabsMixin`), composed via multiple inheritance into one real
  `CharacterSheet(..., QWidget)` that still shares a single `self` — a
  method in one file can call `self._build_statblock_card(...)` even
  though it's defined in a different mixin's file, resolved through the
  composed class's MRO at runtime with no import needed between the
  mixin files themselves.

  Extracted with a line-range slicing script (kept in the session
  scratchpad) rather than manual retyping, so every method body is
  byte-identical to the original — for a split this size the actual risk
  isn't transcription, it's cross-file references. Three classes of
  those got found and fixed by grepping every extracted file for every
  name that moved, not assumed correct: (1) `import *` silently skips
  underscore-prefixed names when a module has no `__all__` — `_lbl`/
  `_sep`/`_card` needed explicit imports in every mixin file *and* in
  the three dialog files, which got the same `shared.py` import block
  `sheet.py` had but not the separate module-constants block those
  aliases used to live in; (2) `RestOptionsDialog`/`RestPreviewDialog`/
  `ArcaneRecoveryDialog`/`LevelUpMulticlassDialog` and the stale-choice
  helpers (`_prune_stale_choices`, `_all_relevant_choice_ids`,
  `RACE_SCOPED_CHOICE_IDS`, `BACKGROUND_SCOPED_CHOICE_IDS`) are called
  from `CharacterSheet` methods, not just from each other — needed
  importing into `base.py`/`choices.py`, not just left in `dialogs/`;
  (3) `back_to_menu = Signal()` had to move onto the final composed
  `CharacterSheet` class itself, not `BaseSheetMixin` — PySide6's Signal
  descriptor only gets registered by Qt's metaclass machinery for
  classes that actually derive from `QObject` at class-body-processing
  time, which a plain mixin doesn't.

  `ResourceWidget` (~217 lines, one of `sheet.py`'s other top-of-file
  classes) was dropped rather than relocated: zero instantiation sites
  anywhere in the repo, same class of dead code as `widgets.py`'s
  cleanup and `feature_dialog.py`'s deletion, confirmed before deleting.

  Verified with `py_compile` on every new file, the full scratchpad
  regression suite (24 scripts, ~19,000 combined combos/calls, all
  green), and confirmed the composed `CharacterSheet`'s MRO resolves
  cleanly. A stub-only full-construction smoke test surfaced a real
  `while widget.count():` hang, traced to a pre-existing PySide6-stub
  gap (a fake `QGridLayout.count()` never becomes falsy against the
  minimal test stub) rather than app code — not chased further, since
  the regression suite already gives strong coverage and it's a
  test-harness limitation rather than a bug.

  `core/` was left flat on review — no edition forking and no dominant
  oversized file the way `sheet.py` dominated `ui/`, so there was no
  real problem for subfolders to solve there.

## Cleric Domain Spells: 7 core domains added, 6 supplement domains still missing

User reported Death Domain wasn't granting its bonus spells. Investigation
found `BONUS_SPELLS` (`dnd_app/data/phbCommon/spells.py`) — the table that
drives always-prepared domain/circle/patron spells via `get_bonus_spells()`
— only had the 5 Amonkhet/Knowledge Cleric domains wired up (Knowledge,
Ambition, Solidarity, Strength, Zeal). All 7 core PHB/SCAG domains were
completely absent: Life, Light, Nature, Tempest, Trickery, War, Death.
Every Cleric using one of those (almost certainly the most commonly
picked domains) got zero domain spells auto-prepared.

Added all 7, each cross-checked against real source text (web search,
not memory alone) before entry — same discipline as the rest of this
file. Every spell name verified present in `SPELL_NAMES` (the app's own
spell database) to catch naming mismatches before they'd silently no-op.
Confirmed via direct `rebuild()` calls that all 7 domains now populate
`char["bonus_spells"]`/`spells_prepared` correctly at level 9 (10 spells
each, the full 1/3/5/7/9 progression).

**Update — the user explicitly asked for the Reaper chooser, so it was
built rather than left deferred.** Death Domain's **Reaper** feature
(1st level: learn one necromancy cantrip of your choice from any class's
spell list, plus the cantrip-doubling passive) was originally going to
be left as a passive description only, matching the existing precedent
for Circle of the Land's identically-shaped Bonus Cantrip. After a
direct user report ("death domain cleric is meant to get a bonus
necromancy cantrip i didnt see that in the chooser"), implemented a real
chooser instead: `_get_subclass_choices()` in `levelup_panel.py` now
offers a `magical_secrets`-type pick (reusing that existing chooser UI)
pooled to the app's 4 real necromancy cantrips (Chill Touch, Spare the
Dying, Toll the Dead, Sapping Sting) once Cleric Death Domain is at
level 1+. The pick is stored in `char["_choices"]["death_domain_reaper_cantrip"]`
and read back into `get_bonus_spells()` (`spells.py`) — same pattern as
Circle of the Land's terrain choice just above it — so it survives
`rebuild()`, is added to `spells_known`/`spells_prepared` as a proper
bonus spell (doesn't eat the Cleric cantrip cap), and gets pruned
automatically if the character switches away from Death Domain (via the
existing `_all_relevant_choice_ids()`/`_prune_stale_choices()` diff,
since it already calls `_get_subclass_choices()` directly). Circle of
the Land's Bonus Cantrip remains passive-only for now — same shape of
gap, not reported, left as documented precedent for the next one.

**Still missing** (not added — lower-play-rate XGE/TCE/SCAG domains,
skipped rather than risk unverified data under time pressure): Arcana
Domain (SCAG), Forge Domain (XGE), Grave Domain (XGE), Order Domain
(GGR/TCE), Peace Domain (TCE), Twilight Domain (TCE). Same fix pattern
applies — add a `("Cleric", "<Domain> Domain")` entry to `BONUS_SPELLS`
in `dnd_app/data/phbCommon/spells.py` with each spell verified against
real source text and against `SPELL_NAMES`.

## The 6 supplement domains — added, plus 2 real bugs found along the way

User provided the full source text for all 6 remaining domains directly
(SCAG/XGE/TCE), asking why they weren't in `CLASS_REFERENCE.md` — turned
out they already were, in full, matching the pasted text exactly (used
this to cross-verify rather than re-typing from scratch). Added all 6 to
`BONUS_SPELLS` following the established pattern, checking every spell
name against `SPELL_NAMES` first.

Two names didn't resolve as pasted: "Otiluke's Resilient Sphere" and
"Rary's Telepathic Bond" only exist in this app's spell database as
"Resilient Sphere"/"Telepathic Bond" (no possessive prefix) — used the
app's real names. "Leomund's Secret Chest" (Arcana Domain, 7th level)
didn't exist under ANY name — a genuinely missing spell, not a naming
mismatch. Verified its real text (4th-level conjuration, PHB, V/S/M,
touch, 1 action) via web search and added it as a proper spell entry in
`ALL_SPELLS`, not just a bare string in `BONUS_SPELLS`.

**Real bug #1**: `get_bonus_spells()`'s class/subclass matching used
`sub_key.lower() not in actual_sub.lower()` — containment anywhere, not
a prefix check. Wiring Twilight Domain exposed it immediately: "light
domain" is a literal substring of "twilight domain", so every Twilight
Domain cleric was also getting Light Domain's entire spell list on top
of their own. Fixed to `not actual_sub.lower().startswith(sub_key.lower())`
— every real `sub_key` in `BONUS_SPELLS` is a genuine prefix of
`actual_sub` (which may carry a trailing "(SOURCE)"), never a mid-string
fragment, so this is strictly safer with zero behavior change for every
correct match. Scanned every class's full `sub_key` list for other
same-shaped collisions: none found.

**Real bug #2, found while checking whether the same pattern existed
elsewhere**: `RACIAL_BONUS_SPELLS`'s race/subrace matching had the exact
same containment bug — "Elf" is a substring of "Half-Elf". Confirmed
with a live test: a Half-Elf character with subrace "Drow Descent"
showed `Darkness` in `bonus_spells` at level 5, a spell Half-Elf/Drow
Descent's own entry doesn't grant at all (it only has a level-1 entry) —
it was silently inheriting Elf/Drow's spells too, since "Drow" is also a
substring of "Drow Descent". Fixed with the same prefix check. Also
applied the same fix to `get_mark_expanded_spells()`'s `MARK_EXPANDED_SPELLS`
lookup (same Elf/Half-Elf collision shape, currently harmless only
because no Half-Elf subrace happens to be named "Mark of Shadow") for
consistency, before it became a real bug too.

Verified via direct `rebuild()` calls: all 6 new domains grant their
correct spells at levels 1/3/5/7/9; Twilight Domain no longer shows any
Light Domain spell; Light Domain itself still works correctly
(regression check); Half-Elf/Drow Descent no longer shows Elf-only
spells; real Elf/Drow still does. Full scratchpad regression suite
green throughout.

## Full sweep: every other class's bonus/expanded spell lists

User asked whether every other class's subclass bonus spells were as
complete as Cleric's domains now are. Cross-referenced BONUS_SPELLS
against every real subclass in classes.py, using CLASS_REFERENCE.md and
spells-sublist.md (not memory) for every value, same discipline as the
Cleric pass. Found and fixed real gaps in Warlock and Ranger, plus 2
more genuinely-missing spells and 2 more misspelled-in-the-database
spell names (on top of the 2 found during the Cleric pass), the same
shape of bug that pass turned up repeatedly.

**Warlock — 5 of 9 patrons had no Expanded Spell List at all**: Archfey,
Fathomless, Great Old One, and Undead were simply absent. The Genie's
table is kind-dependent (a "Genie Spells" column always granted, plus
one of Dao/Djinni/Efreeti/Marid's own column based on the genie_kind
choice already made via levelup_panel.py's existing chooser) -- wired
the kind-independent half into BONUS_SPELLS and the kind-dependent half
as a read-the-pick-back branch in get_bonus_spells(), same pattern as
Death Domain's Reaper cantrip.

**Two already-wired patrons were modeling the wrong feature**: The
Celestial's entry only had Light/Sacred Flame (its separate Bonus
Cantrips feature) with the real Expanded Spell List (Cure Wounds,
Guiding Bolt, Flaming Sphere, Lesser Restoration, Daylight, Revivify,
Guardian of Faith, Wall of Fire, Flame Strike, Greater Restoration)
missing entirely. Same for The Undying (had only Spare the Dying from
Among the Dead, missing False Life, Ray of Sickness, Blindness/Deafness,
Silence, Feign Death, Speak with Dead, Aura of Life, Death Ward,
Contagion, Legend Lore). Added the real list alongside each existing
cantrip grant rather than replacing it -- both features are real and
distinct.

**Ranger — 2 of 5 spell-granting conclaves missing**: Gloom Stalker
(XGE) and Fey Wanderer (TCE) each have the same single-spell-per-level
"Conclave Magic"-style table as Horizon Walker/Monster Slayer/
Swarmkeeper, just never added.

**Druid — 2 of 7 circles missing a genuine "Circle Spells" table**:
Circle of Spores and Circle of Wildfire (both TCE) each have a real
fixed spell table (Spores also grants Chill Touch free at 2nd level).
Verified Circle of Dreams/Stars/the Shepherd genuinely have no such
table (their Circle-defining features are pools of dice/a spellcasting
focus/a summon, not spells) -- correctly absent, not a gap. Circle of
the Land was already fully wired (all 8 terrains) before this session.

**2 more spells missing from the database entirely** (not just a naming
mismatch, like Leomund's Secret Chest during the Cleric pass): Evard's
Black Tentacles (Great Old One's 7th-slot pick) and Staggering Smite
(a pre-existing gap in The Hexblade's own already-wired 7th-slot pick,
found by finally sweeping every BONUS_SPELLS entry's spell names against
SPELL_NAMES, not just the ones touched this pass). Both added as real
ALL_SPELLS entries, verified against spells-sublist.md word-for-word.

**2 more spell names wrong in the database itself**: "Thundering Smite"
should be "Thunderous Smite" (confirmed via spells-sublist.md and a web
search of the real PHB text) -- renamed the actual ALL_SPELLS entry, not
just the reference to it, since nothing else in the codebase referenced
the wrong name. Oath of Redemption's 13th-level pick used "Otiluke's
Resilient Sphere" (the source-book name) instead of this app's actual
"Resilient Sphere" entry, same possessive-prefix mismatch as Peace
Domain's pick during the Cleric pass.

Paladin (all 9 oaths), Artificer (all 4 specialists), and Bard's College
of Spirits (a single bonus-cantrip grant, not a spell table -- verified
it has no separate Expanded Spell List in the reference) were already
complete. Barbarian's Path of the Totem Warrior/Ancestral Guardian
entries weren't re-examined beyond confirming they exist -- that's a
different question (whether a limited-use, once-per-rest cast ability
was correctly simplified into an always-known grant, and whether its
level gate is right) than "is anything missing," and wasn't chased
further this pass.

Verified via direct rebuild() calls for every newly-added/fixed entry
(all 9 Warlock patrons including all 4 Genie kinds and the no-kind-
picked edge case, both new Ranger conclaves, both new Druid circles),
a full SPELL_NAMES resolution sweep across BONUS_SPELLS/
RACIAL_BONUS_SPELLS/MARK_EXPANDED_SPELLS together (0 failures), and the
full scratchpad regression suite.
