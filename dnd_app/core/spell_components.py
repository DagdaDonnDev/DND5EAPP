"""
Component Restrictions (optional rule, default off): a caster who is
Blinded, Gagged, or Restrained can be mechanically unable to cast a
given spell, depending on what that specific spell actually needs --
not a blanket "no spells while condition X" rule, since e.g. a
Blinded caster can still cast a self-only spell with no verbal
component just fine.

This module is the single source of truth for "is THIS spell blocked
by THIS character's current conditions right now" -- shared by the
real cast gate (sheet.py's _cast_spell()/_cast_spell_as_ritual()) and
Immersive Spells' title redaction (ui/immersive_spells.py), so the two
can never drift out of sync (a spell showing "blocked" but still
castable, or vice versa).

Author: Ethan O'Brien
Date: 2026-08-20
"""


def _component_letters(spell: dict) -> set:
    """{'v','s','m'} etc. parsed from a spell's "components" field
    (e.g. "V, S, M (a pinch of salt)")."""
    comps = spell.get("components", "") or ""
    return {part.strip()[:1].lower() for part in comps.split(",") if part.strip()}


def requires_verbal(spell: dict) -> bool:
    return "v" in _component_letters(spell)


def requires_somatic(spell: dict) -> bool:
    return "s" in _component_letters(spell)


def requires_sight(spell: dict) -> bool:
    """No explicit field for this in the spell data -- approximated
    from range: a self-only spell (range "Self", or a "Self (X-foot
    radius)" AOE centered on the caster) doesn't require seeing
    anything, while any other range implies targeting or centering the
    effect on something you must be able to perceive, which for a
    Blinded caster specifically means sight."""
    rng = (spell.get("range") or "").strip().lower()
    return not rng.startswith("self")


# (condition name, requirement-check, short reason) -- checked in this
# order; a spell needing multiple blocked components while multiple
# conditions are active still only needs the first matching reason.
_BLOCK_RULES = (
    ("Blinded",    requires_sight,   "Blinded — can't see a target for this spell"),
    ("Gagged",     requires_verbal,  "Gagged — can't speak this spell's verbal component"),
    ("Restrained", requires_somatic, "Restrained — can't perform this spell's somatic component"),
)


def spell_component_block_reason(char: dict, spell: dict):
    """Returns a short reason string if the "Component Restrictions"
    optional rule is on and an active condition blocks something this
    spell needs, else None."""
    if not char.get("optional_rules", {}).get("component_restrictions", False):
        return None
    conditions = set(char.get("conditions", []))
    for cond_name, check, reason in _BLOCK_RULES:
        if cond_name in conditions and check(spell):
            return reason
    return None
