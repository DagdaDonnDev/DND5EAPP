"""
Save/Load — JSON serialization for character dicts with validation and migration.

Author: Ethan O'Brien
Date: 2026-08-20
"""

import json
import os
from datetime import datetime
from .character import new_character

SAVE_DIR = os.path.join(os.path.expanduser("~"), ".dnd_characters")
CURRENT_VERSION = "1.1"


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def character_filename(char: dict) -> str:
    name = char.get("name", "Unnamed").replace(" ", "_").replace("/", "-")
    return os.path.join(SAVE_DIR, f"{name}.json")


def validate_character(char: dict, *, strict: bool = True) -> tuple[bool, list[str]]:
    """Validate character has required fields for save/load."""
    errors: list[str] = []
    required = ["name", "classes", "abilities", "skills"]
    for field in required:
        if field not in char:
            errors.append(f"Missing required field: {field}")

    if not char.get("name", "").strip() and strict:
        errors.append("Character name is empty")

    for i, cls in enumerate(char.get("classes", [])):
        if not isinstance(cls, dict):
            errors.append(f"Class entry {i} is not an object")
            continue
        if "class" not in cls:
            errors.append(f"Class {i} missing 'class' field")
        if "level" not in cls:
            errors.append(f"Class {i} missing 'level' field")

    if "concentration" in char and not isinstance(char["concentration"], dict):
        errors.append("'concentration' must be an object")

    if "_choices" in char and not isinstance(char["_choices"], dict):
        errors.append("'_choices' must be an object")

    return len(errors) == 0, errors


def migrate_character(data: dict) -> dict:
    """Upgrade older character saves to current schema."""
    return _migrate(data)


def _make_serialisable(obj, _strip_private=True):
    """Recursively convert non-JSON types (sets → sorted lists, int keys → str)."""
    if isinstance(obj, set):
        return sorted(list(obj))
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            # Skip private runtime keys (only at top level of char dict)
            if _strip_private and isinstance(k, str) and k.startswith("_"):
                continue
            # JSON requires string keys
            str_k = str(k) if isinstance(k, int) else k
            out[str_k] = _make_serialisable(v, _strip_private=False)
        return out
    if isinstance(obj, (list, tuple)):
        return [_make_serialisable(i, _strip_private=False) for i in obj]
    return obj


def save_character(char: dict, filepath: str = None) -> str:
    ensure_save_dir()
    ok, errors = validate_character(char)
    if not ok:
        raise ValueError("Cannot save invalid character: " + "; ".join(errors))

    char["modified"] = datetime.now().isoformat()
    if not char.get("created"):
        char["created"] = char["modified"]
    char["version"] = CURRENT_VERSION
    if filepath is None:
        filepath = character_filename(char)
    # Strip runtime state (_grants, etc.) and convert sets before serialising
    to_save = _make_serialisable(char)
    # But _choices is user data — keep it even though it starts with _
    if "_choices" in char:
        to_save["_choices"] = _make_serialisable(char["_choices"])
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)
    return filepath


def load_character(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return migrate_character(data)


def list_saved_characters() -> list[dict]:
    ensure_save_dir()
    results = []
    for fname in os.listdir(SAVE_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(SAVE_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results.append({
                    "name": data.get("name", fname.replace(".json", "")),
                    "classes": data.get("classes", []),
                    "filepath": fpath,
                    "modified": data.get("modified", ""),
                })
            except Exception:
                import logging
                logging.getLogger("dnd_app.save_load").exception(
                    "Failed to read saved character %s", fpath)
    return sorted(results, key=lambda x: x.get("modified", ""), reverse=True)


def delete_character(filepath: str) -> bool:
    try:
        os.remove(filepath)
        return True
    except FileNotFoundError:
        return False


def export_character_text(char: dict) -> str:
    """Export character as a human-readable text block."""
    from .character import total_level, class_levels, ability_mod
    from .calculator import (
        get_ac, get_initiative, get_prof_bonus, get_spell_save_dc,
        get_passive_perception, all_skill_bonuses, all_saving_throw_bonuses,
        get_extra_attacks, get_sneak_attack, get_character_senses,
        get_weapon_attack_bonus,
    )

    lines = []
    def add(label, val=""):
        lines.append(f"{label}: {val}" if val != "" else label)

    add("=" * 50)
    add(char.get("name", "Unnamed").upper())
    add("=" * 50)

    cls_str = ", ".join(
        f"{c['class']} {c['level']}" + (f" ({c['subclass']})" if c.get('subclass') else "")
        for c in char.get("classes", [])
    )
    add("Class(es)", cls_str or "None")
    add("Total Level", str(total_level(char)))
    add("Species/Race", char.get("species") or char.get("race", ""))
    add("Background", char.get("background", ""))
    add("Alignment", char.get("alignment", ""))
    add("XP", str(char.get("experience", 0)))
    add("")

    add("── ABILITY SCORES ──")
    from .character import ability_score
    for ab in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
        score = ability_score(char, ab)
        mod = ability_mod(char, ab)
        sign = "+" if mod >= 0 else ""
        add(f"  {ab}", f"{score} ({sign}{mod})")
    add("")

    add("── COMBAT ──")
    add("  AC", str(get_ac(char)))
    add("  HP", f"{char.get('current_hp',0)} / {char.get('max_hp',0)}")
    ini = get_initiative(char)
    add("  Initiative", f"+{ini}" if ini >= 0 else str(ini))
    add("  Speed", f"{char.get('speed',30)} ft")
    add("  Prof Bonus", f"+{get_prof_bonus(char)}")
    add("  Spell Save DC", str(get_spell_save_dc(char)))
    add("  Passive Perception", str(get_passive_perception(char)))
    add("")

    add("── SAVING THROWS ──")
    saves = all_saving_throw_bonuses(char)
    for ab, bonus in saves.items():
        sign = "+" if bonus >= 0 else ""
        prof = " (Prof)" if char.get("saving_throws", {}).get(ab) else ""
        add(f"  {ab}", f"{sign}{bonus}{prof}")
    add("")

    add("── SKILLS ──")
    skills = all_skill_bonuses(char)
    for skill, bonus in sorted(skills.items()):
        sign = "+" if bonus >= 0 else ""
        level = char.get("skills", {}).get(skill, 0)
        marker = {0: "", 1: "(½)", 2: "(P)", 3: "(E)"}.get(level, "")
        adv = " (Adv)" if skill in char.get("skill_advantages", []) else ""
        disadv = " (Disadv)" if skill in char.get("skill_disadvantages", []) else ""
        parts = [p for p in (f"{sign}{bonus}", marker, adv.strip(), disadv.strip()) if p]
        add(f"  {skill}", " ".join(parts))
    add("")

    if char.get("feats"):
        add("── FEATS ──")
        for feat in char["feats"]:
            add(f"  {feat}")
        add("")

    if char.get("fighting_styles"):
        add("── FIGHTING STYLE(S) ──")
        for fs in char["fighting_styles"]:
            add(f"  {fs}")
        add("")

    # ── Proficiencies & Languages ────────────────────────────────────────────
    langs = char.get("languages", [])
    armor_p = char.get("armor_proficiencies", [])
    weapon_p = char.get("weapon_proficiencies", [])
    tool_p = char.get("tool_proficiencies", [])
    if langs or armor_p or weapon_p or tool_p:
        add("── PROFICIENCIES & LANGUAGES ──")
        if langs:
            add("  Languages", ", ".join(sorted(set(langs))))
        if armor_p:
            add("  Armor", ", ".join(armor_p))
        if weapon_p:
            add("  Weapons", ", ".join(weapon_p))
        if tool_p:
            add("  Tools", ", ".join(tool_p))
        add("")

    # ── Senses ────────────────────────────────────────────────────────────────
    senses = get_character_senses(char)
    active_senses = {k: v for k, v in senses.items() if v}
    if active_senses:
        add("── SENSES ──")
        for name, ft in active_senses.items():
            add(f"  {name.capitalize()}", f"{ft} ft")
        add("")

    # ── Conditions ────────────────────────────────────────────────────────────
    conditions = char.get("conditions", [])
    exhaustion = char.get("exhaustion", 0)
    if conditions or exhaustion:
        add("── ACTIVE CONDITIONS ──")
        for c in conditions:
            add(f"  {c}")
        if exhaustion:
            add(f"  Exhaustion", f"level {exhaustion}")
        add("")

    # ── Weapons ───────────────────────────────────────────────────────────────
    equipped = char.get("equipped_weapons", [])
    if equipped:
        from dnd_app.data.phbCommon.items import WEAPON_DICT
        from .magic_items import parse_magic_suffix
        add("── WEAPONS ──")
        for wname in equipped:
            base_name, magic_bonus = parse_magic_suffix(wname)
            wdata = WEAPON_DICT.get(base_name, {})
            props = " ".join(wdata.get("properties", []) or [])
            ranged = "ranged" in wdata.get("category", "").lower()
            finesse = "finesse" in props.lower()
            to_hit = get_weapon_attack_bonus(char, base_name, finesse_dex=finesse, ranged=ranged) + magic_bonus
            sign = "+" if to_hit >= 0 else ""
            dmg = wdata.get("damage", "?")
            dmg_type = wdata.get("dmg_type", "")
            magic_dmg = f"+{magic_bonus}" if magic_bonus else ""
            add(f"  {wname}", f"{sign}{to_hit} to hit, {dmg}{magic_dmg} {dmg_type}".strip())
        add("  (Simplified: doesn't include situational bonuses from active "
            "toggles/effects — see the app's Combat tab for the exact live total.)")
        add("")

    # ── Resources ─────────────────────────────────────────────────────────────
    # Skip anything whose current_max is a non-positive number — a
    # by_level-driven resource with no threshold met yet at the
    # character's current level (e.g. Indomitable before 9th) computes
    # to 0, and a "0/0 (not actually available)" row is just clutter on
    # what's meant to be a clean reference sheet. Non-numeric max values
    # ("Unlimited", e.g. 20th-level Wild Shape) are always kept.
    resources = char.get("resources", [])
    visible_resources = [r for r in resources
                          if not isinstance(r.get("current_max"), (int, float)) or r.get("current_max", 0) > 0]
    if visible_resources:
        add("── RESOURCES ──")
        for r in visible_resources:
            cur = r.get("current", 0)
            mx = r.get("current_max", 0)
            reset = r.get("reset", "")
            add(f"  {r.get('name','?')}", f"{cur}/{mx} (resets: {reset})" if mx not in (None, "") else "")
        add("")

    # ── Hit Dice ──────────────────────────────────────────────────────────────
    hit_dice = char.get("hit_dice", {})
    if hit_dice:
        add("── HIT DICE ──")
        for die, d in hit_dice.items():
            add(f"  {die}", f"{d.get('remaining',0)}/{d.get('total',0)}")
        add("")

    slots = char.get("spell_slots_max", [0] * 9)
    if any(s > 0 for s in slots):
        add("── SPELL SLOTS ──")
        used = char.get("spell_slots_used", [0] * 9)
        for i, (mx, us) in enumerate(zip(slots, used)):
            if mx > 0:
                add(f"  Level {i+1}", f"{mx-us}/{mx}")
        pact_max = char.get("pact_slots_max", 0)
        if pact_max:
            add(f"  Pact (Lv {char.get('pact_slot_level', 0)})",
                f"{pact_max - char.get('pact_slots_used', 0)}/{pact_max}")
        add("")

    # ── Spells known / prepared ───────────────────────────────────────────────
    known = char.get("spells_known", []) + char.get("cantrips", [])
    if known:
        from dnd_app.data.phbCommon.spells import get_spell
        prepared = set(char.get("spells_prepared", []))
        by_level = {}
        for sp in known:
            data = get_spell(sp)
            lvl = data.get("level", 0) if data else -1
            by_level.setdefault(lvl, []).append(sp)
        add("── SPELLS ──")
        for lvl in sorted(by_level):
            label = "Cantrips" if lvl == 0 else (f"Level {lvl}" if lvl > 0 else "Unknown level")
            names = sorted(by_level[lvl])
            tagged = [f"{n} (prepared)" if n in prepared and lvl > 0 else n for n in names]
            add(f"  {label}", ", ".join(tagged))
        add("")

    # ── Magic Items ───────────────────────────────────────────────────────────
    magic_items = char.get("magic_items", [])
    if magic_items:
        add("── MAGIC ITEMS ──")
        for item in magic_items:
            name = item.get("name", "Unknown")
            tags = []
            if item.get("attunement"): tags.append("attuned")
            if item.get("equipped"): tags.append("equipped")
            tag_str = f" ({', '.join(tags)})" if tags else ""
            add(f"  {name}{tag_str}")
        add("")

    # ── Actions / Bonus Actions / Reactions / Passives ───────────────────────
    try:
        from dnd_app.ui.action_abilities import build_action_abilities
        buckets = build_action_abilities(char)
        for bucket in ("Action", "Bonus Action", "Reaction", "Passive"):
            entries = buckets.get(bucket, [])
            if not entries:
                continue
            add(f"── {bucket.upper()}S ──" if not bucket.endswith("s") else f"── {bucket.upper()} ──")
            for entry in entries:
                ename = entry[0] if len(entry) > 0 else "?"
                edesc = entry[1] if len(entry) > 1 else ""
                add(f"  {ename}", edesc)
            add("")
    except Exception:
        # Best-effort — a malformed/edge-case character shouldn't block the
        # rest of the export just because the abilities-list computation
        # (which covers a huge, class-specific surface area) hit something
        # unexpected on this particular build.
        pass

    conc = char.get("concentration", {}).get("spell")
    if conc:
        add("── CONCENTRATION ──")
        add(f"  {conc}")
        add("")

    if char.get("notes"):
        add("── NOTES ──")
        add(char["notes"])

    return "\n".join(lines)


def _migrate(data: dict) -> dict:
    """Upgrade older character saves to current schema."""
    base = new_character()

    for key, default in base.items():
        if key not in data:
            data[key] = default if not isinstance(default, (dict, list)) else (
                dict(default) if isinstance(default, dict) else list(default)
            )

    if "class" in data and not data.get("classes"):
        hit_die_map = {
            "Barbarian": 12, "Fighter": 10, "Paladin": 10, "Ranger": 10,
            "Bard": 8, "Cleric": 8, "Druid": 8, "Monk": 8, "Rogue": 8, "Warlock": 8,
            "Artificer": 8, "Blood Hunter": 10,
            "Sorcerer": 6, "Wizard": 6,
        }
        cls_name = data.pop("class", "Fighter")
        lvl = data.pop("level", 1)
        hd = hit_die_map.get(cls_name, 8)
        data["classes"] = [{
            "class": cls_name,
            "level": lvl,
            "subclass": data.pop("subclass", ""),
            "hit_die": hd,
        }]

    if not isinstance(data.get("_choices"), dict):
        data["_choices"] = {}
    if not isinstance(data.get("concentration"), dict):
        data["concentration"] = {"spell": None, "since_round": 0}
    if not isinstance(data.get("ability_overrides"), dict):
        data["ability_overrides"] = {}
    if not isinstance(data.get("skill_advantages"), list):
        data["skill_advantages"] = []
    if not isinstance(data.get("skill_disadvantages"), list):
        data["skill_disadvantages"] = []
    if not isinstance(data.get("equipped_weapons"), list):
        data["equipped_weapons"] = []

    # 2024 edition is not shipped yet — coerce any saved 2024 chars to 2014
    # so incomplete data paths are never exercised at runtime.
    if data.get("edition") == "2024":
        data["edition"] = "2014"
        data["_edition_coerced_from_2024"] = True

    # Normalize magic_items entries
    normalized = []
    for item in data.get("magic_items", []):
        if isinstance(item, str):
            normalized.append({"name": item, "attunement": False, "equipped": False, "notes": ""})
        elif isinstance(item, dict):
            normalized.append({
                "name": item.get("name", "Unknown"),
                "attunement": bool(item.get("attunement", False)),
                "equipped": bool(item.get("equipped", False)),
                "notes": item.get("notes", ""),
            })
    data["magic_items"] = normalized

    data["version"] = CURRENT_VERSION
    return data
