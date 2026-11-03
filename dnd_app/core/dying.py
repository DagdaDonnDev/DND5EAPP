"""Hit points, dying and death -- the rules both apps follow.

Damage, death saving throws, becoming stable and dying all happen here,
so the desktop sheet and the Android sheet can't tell two different
stories about the same character. Each app only does its own screen work
(spin boxes, toasts, the YOU DIED overlay) with what these return.

The rules (PHB p.197-198):
  * Temporary hit points soak damage first.
  * Massive damage: when damage drops you to 0 HP and the damage LEFT
    OVER is at least your hit point maximum, you die outright.
  * At 0 HP you're unconscious and roll death saves: 3 successes and
    you're stable, 3 failures and you die.
  * Taking damage at 0 HP is a failed death save. A stable creature that
    takes damage stops being stable and starts rolling again.
  * Stable means still at 0 HP and still unconscious -- you regain 1 HP
    after 1d4 hours (the player heals 1), or sooner if someone heals you.
  * Any healing at 0 HP wakes you and resets the death saves.

How the state is kept (all of it saved with the character):
  * char["death_saves"] = {"successes": n, "failures": n}
  * stable = 0 HP and 3 successes ticked (they stay ticked until you wake)
  * char["is_dead"] = True once dead, until Revive
"""
import random


def death_saves(char: dict) -> tuple[int, int]:
    """(successes, failures) ticked right now."""
    ds = char.get("death_saves") or {}
    return ds.get("successes", 0), ds.get("failures", 0)


def is_stable(char: dict) -> bool:
    """At 0 HP, alive, with three successes: stable."""
    succ, _ = death_saves(char)
    return (char.get("current_hp", 1) <= 0 and not char.get("is_dead")
            and succ >= 3)


STABLE_MESSAGE = ("Stable -- no more death saves. You stay unconscious at 0 HP until "
                  "healed, or regain 1 HP after 1d4 hours.")


def death_status_text(successes: int, failures: int) -> str:
    """The one-line status shown on the death saves card."""
    if failures >= 3:
        return "DEAD"
    if successes >= 3:
        return "STABLE -- unconscious until healed"
    if failures == 2:
        return "1 more failure = death"
    if successes >= 1 or failures >= 1:
        return f"{successes} success, {failures} failure" + ("s" if failures != 1 else "")
    return "Rolling to live or die"


def set_death_saves(char: dict, successes: int, failures: int) -> str:
    """Store the death save ticks and say what they mean now:
    "dead" (third failure), "stable" (third success, just now) or ""."""
    # 1. Remember whether they were already stable, so a re-tick
    #    doesn't announce it twice.
    was_stable = is_stable(char)
    # 2. Store the ticks, 0 to 3 of each.
    succ = max(0, min(3, successes))
    fail = max(0, min(3, failures))
    char["death_saves"] = {"successes": succ, "failures": fail}
    # 3. Three failures: dead. Three successes: stable, at 0 HP.
    if fail >= 3:
        char["is_dead"] = True
        return "dead"
    if succ >= 3 and not was_stable:
        return "stable"
    return ""


def heal_block_reason(char: dict) -> str:
    """Why healing can't work right now ("" if it can)."""
    if char.get("is_dead"):
        return "The dead can't be healed -- use Revive first"
    return ""


def heal(char: dict, amount: int) -> str:
    """Regain `amount` hit points, up to the maximum, and return what to tell
    the player. Healing at 0 HP wakes you and resets the death saves."""
    # 1. Nothing for no healing, or for the dead (see heal_block_reason).
    if amount <= 0 or heal_block_reason(char):
        return ""
    # 2. Add the hit points, never past the maximum.
    cur = max(0, char.get("current_hp", 0))
    char["current_hp"] = max(cur, min(char.get("max_hp", 0), cur + amount))
    # 3. Back up from 0 HP: conscious again, the death saves start over.
    if cur <= 0 < char["current_hp"]:
        char["death_saves"] = {"successes": 0, "failures": 0}
        return "Back on your feet! Death saves reset"
    return ""


def revive(char: dict) -> None:
    """Back from the dead (Revivify and the like): alive with 1 HP, death
    saves cleared, exhaustion gone."""
    char["is_dead"] = False
    char["current_hp"] = 1
    char["death_saves"] = {"successes": 0, "failures": 0}
    char["exhaustion"] = 0


def death_cause(char: dict) -> str:
    """Why the character died, for the YOU DIED screen."""
    _, fail = death_saves(char)
    if fail >= 3:
        return "Failed three death saves"
    if char.get("exhaustion", 0) >= 6:
        return "Succumbed to exhaustion"
    return "Killed outright by massive damage"


def _rage_keeps_you_up(char: dict, notes: list, rng) -> int:
    """Dropping to 0 HP while raging, and not killed outright. Returns the
    hit points left (0 if nothing saves you):
      * Zealot 14 (2014), Rage Beyond Death: stay at 1 HP. (Simplified --
        the book has you fight on at 0 HP until the rage ends.)
      * Barbarian 11, Relentless Rage: a DC 10 CON save, +5 for each use
        since your last rest. Success: 1 HP (2024: twice your Barbarian
        level)."""
    if "Rage" not in char.get("active_effects", []):
        return 0
    from .character import class_levels
    barb = class_levels(char).get("Barbarian", 0)
    zealot = any("zealot" in (c.get("subclass") or "").lower()
                 for c in char.get("classes", []) if c.get("class") == "Barbarian")
    if barb >= 14 and zealot and char.get("edition", "2014") != "2024":
        notes.append("Rage Beyond Death: damage would drop you to 0, but your rage "
                     "keeps you standing at 1 HP")
        return 1
    if barb >= 11:
        from .calculator import get_saving_throw_bonus
        uses = char.get("_relentless_rage_uses", 0)
        dc = 10 + 5 * uses
        char["_relentless_rage_uses"] = uses + 1
        roll = rng.randint(1, 20)
        bonus = get_saving_throw_bonus(char, "CON")
        total = roll + bonus
        if total >= dc:
            hp = barb * 2 if char.get("edition") == "2024" else 1
            notes.append(f"Relentless Rage: DC {dc} CON save -- rolled {roll}{bonus:+d} = {total}, "
                         f"success: you drop to {hp} HP instead of 0")
            return hp
        notes.append(f"Relentless Rage: DC {dc} CON save -- rolled {roll}{bonus:+d} = {total}, "
                     f"failed: you drop to 0 HP")
    return 0


def take_damage(char: dict, amount: int, rng=None) -> dict:
    """Deal `amount` damage to the character's own hit points (a Wild Shape
    beast form's pool is the apps' business) and report what happened:
      {"absorbed": soaked by temp HP, "taken": what reached real HP,
       "died": True if this killed them, "notes": messages, in order,
       "concentration_dc": DC to keep concentrating (0 = no save needed)}
    """
    rng = rng or random
    out = {"absorbed": 0, "taken": 0, "died": False, "notes": [], "concentration_dc": 0}
    # 1. Nothing happens for no damage, or to the dead.
    if amount <= 0 or char.get("is_dead"):
        return out
    from .magic_items import drop_concentration
    max_hp = max(1, char.get("max_hp", 1))
    cur = max(0, char.get("current_hp", 0))
    was_down = cur <= 0
    concentrating = (char.get("concentration") or {}).get("spell")

    # 2. Temporary hit points soak it first.
    temp = max(0, char.get("temp_hp", 0))
    absorbed = min(temp, amount)
    char["temp_hp"] = temp - absorbed
    left = amount - absorbed
    out["absorbed"], out["taken"] = absorbed, left
    if absorbed and left == 0:
        out["notes"].append(f"Temp HP absorbed all {absorbed} damage")
    elif absorbed:
        out["notes"].append(f"Temp HP absorbed {absorbed}, took {left} damage")

    # 3. Massive damage: what's left after reaching 0 HP is at least the
    #    hit point maximum -- dead outright, no death saves.
    if left - cur >= max_hp:
        char["current_hp"] = 0
        char["is_dead"] = True
        drop_concentration(char)
        out["died"] = True
        return out

    # 4. Already down: any damage is a failed death save, and a stable
    #    character stops being stable (the count starts again from zero).
    if was_down:
        succ, fail = death_saves(char)
        if succ >= 3:
            succ, fail = 0, 0
            out["notes"].append("Hit while stable -- dying again")
        if set_death_saves(char, succ, fail + 1) == "dead":
            out["died"] = True
            drop_concentration(char)
        else:
            out["notes"].append("Damaged at 0 HP -- automatic death save failure")
        return out

    # 5. Hit points down. Reaching 0 while raging may keep you up.
    new_hp = cur - left
    if new_hp <= 0:
        new_hp = _rage_keeps_you_up(char, out["notes"], rng)
    char["current_hp"] = max(0, new_hp)

    # 6. Dropped to 0: unconscious, so a fresh set of death saves, and
    #    concentration ends with no save to roll.
    if char["current_hp"] <= 0:
        char["death_saves"] = {"successes": 0, "failures": 0}
        if concentrating:
            drop_concentration(char)
            out["notes"].append(f"Down to 0 HP -- concentration on {concentrating} ends")
    # 7. Still up and concentrating: a CON save to keep it, DC 10 or half
    #    the damage (temp HP soaking it doesn't spare you the save).
    elif concentrating:
        out["concentration_dc"] = max(10, amount // 2)
    return out
