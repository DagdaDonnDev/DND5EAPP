"""
Save/Load — JSON serialization for character dicts with validation and migration.

Author: Ethan O'Brien
Date: 2026-08-20
"""

import json
import os
from datetime import datetime
from .character import new_character

# The app's own config folder (app_settings.json lives here). Characters
# used to be saved here too; they now default to Documents/MIMIC
# Characters -- see get_save_dir() -- and older saves are copied across
# once by migrate_saves_once().
SAVE_DIR = os.path.join(os.path.expanduser("~"), ".dnd_characters")
LEGACY_SAVE_DIR = SAVE_DIR
SAVES_SUBDIR = "MIMIC Characters"
CURRENT_VERSION = "1.1"

# A platform can supply its own default (the Android app picks shared
# storage, falling back to its private folder) via set_default_save_dir().
_default_save_dir_override = None


def documents_dir() -> str:
    """The user's Documents folder -- on Windows the real one (which may
    be redirected, e.g. into OneDrive), elsewhere ~/Documents."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            # CSIDL_PERSONAL (5) = Documents, SHGFP_TYPE_CURRENT (0)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:
                return buf.value
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def default_save_dir() -> str:
    return _default_save_dir_override or os.path.join(documents_dir(), SAVES_SUBDIR)


def set_default_save_dir(path: str) -> None:
    global _default_save_dir_override
    _default_save_dir_override = path or None


def is_writable_dir(path: str) -> bool:
    """Creates the folder if needed and checks a file can be written in it."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".mimic_write_test")
        with open(probe, "w") as f:
            f.write("")
        os.remove(probe)
        return True
    except OSError:
        return False


def get_save_dir() -> str:
    """Where characters are saved: the folder chosen in Settings, else the
    default (Documents/MIMIC Characters); the old config folder only as
    a last resort if neither can be written."""
    from .app_settings import get_custom_save_dir
    for candidate in (get_custom_save_dir(), default_save_dir()):
        if candidate and is_writable_dir(candidate):
            return candidate
    os.makedirs(LEGACY_SAVE_DIR, exist_ok=True)
    return LEGACY_SAVE_DIR


def copy_saved_characters(src_dir: str, dst_dir: str, move: bool = False) -> int:
    """Copy (or move) every saved character file from one folder to another,
    leaving any that already exist at the destination alone. Returns how
    many were copied. app_settings.json is never a character."""
    import shutil
    if not src_dir or not os.path.isdir(src_dir) or os.path.abspath(src_dir) == os.path.abspath(dst_dir):
        return 0
    os.makedirs(dst_dir, exist_ok=True)
    n = 0
    for fname in os.listdir(src_dir):
        if not fname.endswith(".json") or fname == "app_settings.json":
            continue
        src, dst = os.path.join(src_dir, fname), os.path.join(dst_dir, fname)
        if os.path.exists(dst):
            continue
        try:
            (shutil.move if move else shutil.copy2)(src, dst)
            n += 1
        except OSError:
            continue
    return n


def migrate_saves_once(old_dir: str, key: str) -> int:
    """One-time copy of characters saved in an old location into the
    current save folder (originals are left where they were). `key`
    records in app settings that it's been done."""
    from .app_settings import get_flag, set_flag
    if get_flag(key):
        return 0
    n = copy_saved_characters(old_dir, get_save_dir())
    set_flag(key, True)
    return n


def character_folder_name(char: dict) -> str:
    """A character's own export folder name: their name, minus anything a
    file system (Windows, Android storage) won't take."""
    name = (char.get("name") or "").strip()
    name = "".join(c for c in name if c not in '<>:"/\\|?*' and ord(c) >= 32).strip(" .")
    return name or "Unnamed"


def character_export_dir(char: dict, base: str = None) -> str:
    """<save folder>/<name> -- one folder per character, so its PDF sheet,
    text summary and a copy of its character file sit together. Saves
    themselves stay at the top of the save folder (the character list
    only reads files there), so these never show up as characters."""
    path = os.path.join(base or get_save_dir(), character_folder_name(char))
    os.makedirs(path, exist_ok=True)
    return path


def ensure_save_dir():
    os.makedirs(get_save_dir(), exist_ok=True)


def character_filename(char: dict) -> str:
    name = char.get("name", "Unnamed").replace(" ", "_").replace("/", "-")
    return os.path.join(get_save_dir(), f"{name}.json")


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
    """Upgrade older character saves to current schema. Every save read
    from disk comes through here, so it's also marked as just reopened:
    the sheet then asks about effects left on (core/action_use.py
    leftover_effects). An underscore key, so it's never saved."""
    data = _migrate(data)
    if isinstance(data, dict):
        data["_reopened"] = True
    return data


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
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(character_json(char))
    return filepath


def character_json(char: dict) -> str:
    """The character as save files store it: runtime state (_grants etc.)
    stripped and sets converted. Shared by save_character() and Android's
    Export, which writes the same format somewhere the user picks."""
    to_save = _make_serialisable(char)
    # But _choices is user data — keep it even though it starts with _
    if "_choices" in char:
        to_save["_choices"] = _make_serialisable(char["_choices"])
    return json.dumps(to_save, indent=2, ensure_ascii=False)


def load_character(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return migrate_character(data)


def list_saved_characters(directory: str = None) -> list[dict]:
    """List saved characters in `directory` (default: get_save_dir())."""
    if directory is None:
        directory = get_save_dir()
    os.makedirs(directory, exist_ok=True)
    results = []
    for fname in os.listdir(directory):
        # .autosave.json files are the desktop's crash backups of a
        # character, not separate characters
        if fname.endswith(".json") and fname != "app_settings.json" and not fname.endswith(".autosave.json"):
            fpath = os.path.join(directory, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results.append({
                    "name": data.get("name", fname.replace(".json", "")),
                    "classes": data.get("classes", []),
                    "filepath": fpath,
                    "modified": data.get("modified", ""),
                    "folder": data.get("folder", "") or "",
                })
            except Exception:
                import logging
                logging.getLogger("dnd_app.save_load").exception(
                    "Failed to read saved character %s", fpath)
    return sorted(results, key=lambda x: x.get("modified", ""), reverse=True)


def _norm_name(name: str) -> str:
    return " ".join((name or "").split()).casefold()


def name_in_use(name: str, exclude_path: str = None, directory: str = None) -> bool:
    """Whether another saved character already uses this name (ignoring
    case and extra spaces) -- or would land on the same file. The
    character's own file (exclude_path) doesn't count."""
    directory = directory or get_save_dir()
    target = _norm_name(name)
    if not target:
        return False
    ex = os.path.abspath(exclude_path) if exclude_path else None
    for entry in list_saved_characters(directory):
        if ex and os.path.abspath(entry["filepath"]) == ex:
            continue
        if _norm_name(entry.get("name", "")) == target:
            return True
    path = os.path.join(directory, os.path.basename(character_filename({"name": name.strip()})))
    return os.path.exists(path) and (not ex or os.path.abspath(path) != ex)


def unique_character_name(name: str, directory: str = None) -> str:
    """name, or "name 2", "name 3"... -- the first one no saved character uses."""
    if not name_in_use(name, directory=directory):
        return name
    n = 2
    while name_in_use(f"{name} {n}", directory=directory):
        n += 1
    return f"{name} {n}"


NAME_IN_USE_MESSAGE = ("That name is already being used by another saved character -- "
                       "please choose a different one.")


def list_character_folders(directory: str = None) -> list[str]:
    """Sorted list of distinct non-empty folder/campaign names in use
    among saved characters in `directory` -- for populating a "move to
    folder" picker's list of existing folders. Characters with no
    folder ("" -- shown as "Uncategorized" in the UI) aren't included
    here since it's not something you "move to" via typing a name."""
    folders = {e["folder"] for e in list_saved_characters(directory) if e.get("folder")}
    return sorted(folders)


def set_character_folder(filepath: str, folder: str) -> None:
    """Move a saved character into a different campaign/folder grouping
    by patching just the `folder` field directly on disk, without going
    through save_character() -- a purely organizational edit shouldn't
    bump `modified` or re-run full validation/migration."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["folder"] = (folder or "").strip()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_character(filepath: str) -> bool:
    try:
        os.remove(filepath)
        return True
    except FileNotFoundError:
        return False


def rename_character_folder(directory: str, old_name: str, new_name: str) -> int:
    """Renames a campaign/folder by re-tagging every character currently
    in `old_name` to `new_name` -- there's no separate "folder" entity
    on disk, just a field on each character, so a rename is a bulk
    set_character_folder() over whoever's in it. Returns how many
    characters were moved."""
    new_name = (new_name or "").strip()
    count = 0
    for entry in list_saved_characters(directory):
        if entry.get("folder", "") == old_name:
            set_character_folder(entry["filepath"], new_name)
            count += 1
    return count


def delete_character_folder(directory: str, folder_name: str) -> int:
    """Permanently deletes every character currently filed under
    `folder_name` -- a real, irreversible bulk delete (not just
    un-filing them to Uncategorized). Returns how many were deleted."""
    count = 0
    for entry in list_saved_characters(directory):
        if entry.get("folder", "") == folder_name:
            if delete_character(entry["filepath"]):
                count += 1
    return count


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
        from dnd_app.data.items import WEAPON_DICT
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
        from dnd_app.data.spells import get_spell
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
        from dnd_app.core.actions import build_action_abilities
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

    notes_pages = [p for p in char.get("notes_pages", []) if p.get("text", "").strip()]
    if notes_pages:
        add("── NOTES ──")
        for page in notes_pages:
            add(f"[{page.get('title', 'Notes')}]")
            add(page.get("text", ""))
            add("")
    elif char.get("notes"):
        # Pre-tabs characters that haven't opened the sheet (and so never
        # ran the notes_pages migration) still have their notes here.
        add("── NOTES ──")
        add(char["notes"])

    return "\n".join(lines)


def _merge_coin_spellings(data: dict) -> None:
    """Coins are "GP", "SP"... everywhere. Older desktop saves also kept
    lowercase ones ("gp"): the Gear tab's edits, and the background's gold,
    which rebuild() used to add a second time (the creation wizards already
    add it, as "GP"). For each coin:
      * a lowercase amount set on the Gear tab wins
      * a lowercase "gp" equal to the background's gold is that duplicate --
        dropped, unless it's the only gold there is"""
    cur = data.get("currency")
    if not isinstance(cur, dict):
        return
    from dnd_app.data.backgrounds import get_background
    import re
    bg_text = (get_background(data.get("background", "")) or {}).get("equipment", "")
    m = re.search(r"(\d+)\s*gp", bg_text or "", re.IGNORECASE)
    bg_gold = int(m.group(1)) if m else None
    for coin in ("CP", "SP", "EP", "GP", "PP"):
        low = cur.pop(coin.lower(), None)
        if not isinstance(low, (int, float)):
            continue
        if coin == "GP" and low == bg_gold and cur.get("GP"):
            continue
        cur[coin] = int(low)


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

    # A spell the catalog no longer lists twice ("Tiny Hut" beside
    # "Leomund's Tiny Hut"): a save that stored the other name gets the one
    # the catalog keeps, everywhere a spell name is kept. And the Unearthed
    # Arcana spells it no longer has at all go, rather than sit unseen in a
    # spell list taking up a slot.
    from dnd_app.data.spells import SPELL_ALIASES, SPELL_DICT, REMOVED_SPELLS
    renames = {old: new for old, new in SPELL_ALIASES.items() if old not in SPELL_DICT}

    def _renamed(names):
        return [renames.get(n, n) if isinstance(n, str) else n
                for n in names if not (isinstance(n, str) and n in REMOVED_SPELLS)]
    for key in ("spells_known", "spells_prepared", "quick_spells", "magical_secrets_spells", "bonus_spells",
                "spells_from_full_list", "cantrips"):
        if isinstance(data.get(key), list):
            data[key] = _renamed(data[key])
    for key, picks in list(data["_choices"].items()):
        if isinstance(picks, list):
            data["_choices"][key] = _renamed(picks)

    # 2024 edition is not shipped yet — coerce any saved 2024 chars to 2014
    # so incomplete data paths are never exercised at runtime.
    if data.get("edition") == "2024":
        data["edition"] = "2014"
        data["_edition_coerced_from_2024"] = True

    _merge_coin_spellings(data)

    # Normalize magic_items entries
    normalized = []
    for item in data.get("magic_items", []):
        if isinstance(item, str):
            normalized.append({"name": item, "attunement": False, "equipped": False, "notes": ""})
        elif isinstance(item, dict):
            entry = {
                "name": item.get("name", "Unknown"),
                "attunement": bool(item.get("attunement", False)),
                "equipped": bool(item.get("equipped", False)),
                "notes": item.get("notes", ""),
            }
            # per-copy state (see core/magic_items.owned_magic_items)
            for key in ("uid", "attuned", "studied", "qty"):
                if key in item:
                    entry[key] = item[key]
            normalized.append(entry)
    data["magic_items"] = normalized

    data["version"] = CURRENT_VERSION
    return data
