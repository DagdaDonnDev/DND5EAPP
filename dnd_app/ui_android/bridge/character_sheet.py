"""Character Sheet (Overview) bridge -- QML-facing view over a finished
character. This is a first slice, not full desktop parity: desktop's
sheet is 12 tabs (abilities/skills/combat/gear/companions/choices/
infusions/spells/features/traits/action_tabs); this bridge covers just
the "Overview" numbers a player checks constantly -- ability scores,
AC/HP/initiative, saving throws, skills.

Reuses dnd_app.core.controller.CharacterController wholesale for the
rebuild()+update_all() refresh cycle, exactly like every desktop sheet
mixin does (see ui_desktop/pages/sheet/base.py's CharacterSheet.__init__
and _force_full_refresh) -- max_hp/current_hp/AC/etc. are legitimately
computed at sheet-view time, not during the wizard, so this bridge's
refresh() is the Android equivalent of that same call.
"""
import random
import re
import sys

from PySide6.QtCore import QObject, Signal, Slot, Property

from dnd_app.core.controller import CharacterController
from dnd_app.core.app_settings import get_app_theme
from dnd_app.core.character import (
    ability_score, ability_mod, long_rest as _long_rest, short_rest as _short_rest,
    get_class_entry, set_class_level, add_class, set_subclass, add_feat,
    clean_subclass_name, xp_progress, total_level, restore_spell_slot, subclasses,
)
from dnd_app.core.multiclass import get_saving_throw_profs, check_multiclass_prereq
from dnd_app.core.builder import get_choices_needed, apply_choice, rebuild, full_list_dumped_spell_names
from dnd_app.core.calculator import (
    SKILL_ABILITY, get_ac, get_initiative, get_prof_bonus,
    get_passive_perception, get_skill_bonus, get_saving_throw_bonus,
    class_levels, has_weapon_proficiency, get_carry_capacity_detail,
    get_total_weight, get_wild_shape_info, get_available_wildshape_beasts,
    get_available_companions, resolve_companion_statblock,
    get_summonable_but_inactive_companions, companion_max_simultaneous,
    count_active_companion_instances, get_max_active_infusions,
    restore_hit_dice_pool, get_superiority_die, get_infusion_bonus, get_infusion_min_level,
    get_rage_damage, get_onhit_damage_bonuses, get_condition_attack_status,
    spell_preparing_classes, can_ritual_cast, spell_needs_preparing,
    spellcasting_block_reason, effect_start_problem, on_effect_started,
    ability_check_bonus,
)
from dnd_app.data.feature_ui_interactions import TOOLS as SWAP_TOOLS_POOL
from dnd_app.core.magic_items import (
    concentration_save, start_concentration, drop_concentration, parse_magic_suffix,
    parse_material_prefix, ABILITY_SCORE_MANUALS,
)
from dnd_app.core.effects import EFFECT_TABLE, INSTANT_POTION_EFFECTS
from dnd_app.core.riders import base_weapon_options as _base_weapon_options, weapon_base_of as _weapon_base_of
from dnd_app.core.spellcasting import spell_component_block_reason
from dnd_app.core.ammo import ammo_kind, ammo_label, ammo_count, spend_ammo, set_ammo
from dnd_app.core.dying import (
    take_damage, heal, heal_block_reason, set_death_saves,
    revive as _revive_char, death_cause, death_status_text, STABLE_MESSAGE,
)
from dnd_app.core.effects import has_extra_action
from dnd_app.data.themes import THEMES, FONT_SCALES
from dnd_app.core.choices import (
    _get_race_choices, _get_class_tool_choices, _get_feat_choices, _get_dm_reward_choices,
    _get_subclass_choices, feat_prereq_met, ALL_SKILLS as _LEVELUP_ALL_SKILLS,
    FIGHTING_STYLES as _MV_FIGHTING_STYLES, _all_relevant_choice_ids, _prune_stale_choices,
    change_and_prune, RACE_SCOPED_CHOICE_IDS, BACKGROUND_SCOPED_CHOICE_IDS,
)
from dnd_app.core.effects import RESOURCE_POOL_TOGGLES, WILDSHAPE_BLOCKED_FEATURES
from dnd_app.core.character import rest_options, rest_preview_lines
from dnd_app.core.spellcasting import compute_display_spell_title
from dnd_app.core.spellcasting import (
    spell_progression_tables, char_spell_classes, max_castable_spell_level,
    all_caster_classes, known_spell_classes, attribute_known_spells,
    prepared_caster_caps, attribute_prepared_spells, spell_limits,
)
from dnd_app.core.actions import build_action_abilities
from dnd_app.data.items import WEAPON_DICT, ALL_WEAPONS, ARMOR, gear_icon, is_scroll_name, is_thrown_consumable
from dnd_app.data.spells import (
    get_spell, spells_for_class, spells_for_class_at_level, SPELL_DICT, SPELLS_BY_LEVEL,
    get_mark_expanded_spells,
)
from dnd_app.data.conditions import CONDITIONS
from dnd_app.data.statblocks import (
    WILDSHAPE_BEASTS, get_mount_statblock, get_vehicle_statblock,
    FIND_GREATER_STEED_OPTIONS, SCALING_SUMMONS, resolve_scaling_summon,
    COMPANION_STATBLOCKS,
)
from dnd_app.data.items import MOUNTS, VEHICLES, VEHICLES_AIR, VEHICLES_LAND, VEHICLES_BGDIA
from dnd_app.data.classes import (
    CLASS_DICT, ARTIFICER_INFUSION_TARGETS, ARTIFICER_REPLICABLE_ITEMS,
    WILD_MAGIC_SURGE_TABLE, WILD_MAGIC_BARBARIAN_TABLE, BATTLE_MASTER_MANEUVERS,
    METAMAGIC, ARTIFICER_INFUSIONS,
)
from dnd_app.data.races import (
    get_race, RACE_NAMES, RACE_DICT, DRACONIC_ANCESTRY, ANCESTRY_BY_SUBRACE,
)
from dnd_app.data.backgrounds import get_background, BACKGROUND_NAMES
from dnd_app.data.feats import get_feat, ALL_FEATS
from dnd_app.data.class_features import SUBCLASS_FEATURES, CLASS_FEATURE_INDEX, OPTIONAL_CLASS_FEATURES
from dnd_app.data.items import ARMOR_DICT, ADVENTURING_GEAR, ALL_TOOLS, WEAPON_NAMES
from dnd_app.data.items import (
    SIMPLE_MELEE, SIMPLE_RANGED, MARTIAL_MELEE, MARTIAL_RANGED, FIREARMS,
)
from dnd_app.data.magic_items import ALL_MAGIC_ITEMS, get_magic_item, get_item_effect
from dnd_app.core.magic_items import attunement_prereq_met
from dnd_app.core.spellcasting import parse_spell_scroll, use_spell_scroll, bind_spell_scroll
from dnd_app.core.magic_items import (owned_magic_items, add_owned_magic_item, remove_owned_magic_item,
                                      set_owned_magic_item_qty, set_owned_magic_item_equipped,
                                      set_owned_magic_item_attuned, can_study_manual, study_owned_manual,
                                      find_magic_item, is_magic_ammunition)
from dnd_app.data.dm_rewards import ALL_DM_REWARDS, DM_REWARD_CATEGORIES, get_dm_reward

_CURRENCY_ORDER = ["PP", "GP", "EP", "SP", "CP"]

# Ports ui_desktop's gear.py _SLOT_KEYWORDS/_mi_slot exactly, for the
# magic item browser's "Slot" filter.
_MI_SLOT_KEYWORDS = {
    "Weapon":        ["sword", "axe", "bow", "mace", "hammer", "blade", "lance", "dagger", "arrow",
                       "whip", "spear", "trident", "quarterstaff", "club", "flail", "handaxe",
                       "longsword", "shortsword", "scimitar", "rapier", "greatsword", "greataxe"],
    "Armor":         ["armor", "shield", "chain", "plate", "leather", "scale", "breastplate",
                       "bracers of defense", "elven chain"],
    "Ring":          ["ring"],
    "Cloak / Robe":  ["cloak", "mantle", "robe"],
    "Hat / Helm":    ["helm", "hat", "crown", "tiara", "circlet", "cap", "headband"],
    "Boots / Slippers": ["boots", "slippers", "sandal", "shoes"],
    "Bracers / Gauntlets": ["bracers", "gauntlets", "gloves"],
    "Belt":          ["belt", "girdle"],
    "Potion":        ["potion"],
    "Scroll / Wand / Rod / Staff": ["scroll", "wand", "rod", "staff"],
}

_MI_RARITY_ORDER = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact"]


def _mi_sort_key(rarity: str, name: str):
    """Magic items list rarity first (Common -> Artifact, anything else
    after), then by name."""
    rank = _MI_RARITY_ORDER.index(rarity) if rarity in _MI_RARITY_ORDER else len(_MI_RARITY_ORDER)
    return (rank, name.casefold())


def _catalog_entry(name: str):
    """The magic item catalogue entry for an owned item -- a bound spell
    scroll ("Spell Scroll (3rd level) — Fireball") uses its level's entry."""
    from dnd_app.core.spellcasting import parse_spell_scroll, scroll_base_name
    entry = get_magic_item(name)
    if entry is None:
        scroll = parse_spell_scroll(name)
        if scroll:
            entry = get_magic_item(scroll_base_name(scroll[0]))
    return entry


def _magic_item_slot(item_name: str, itype: str) -> str:
    n = item_name.lower()
    for slot, kws in _MI_SLOT_KEYWORDS.items():
        if any(kw in n for kw in kws):
            return slot
    if itype in ("Wand", "Rod", "Staff", "Scroll"):
        return "Scroll / Wand / Rod / Staff"
    if itype == "Potion":
        return "Potion"
    if itype == "Armor":
        return "Armor"
    if itype == "Ring":
        return "Ring"
    if itype == "Weapon":
        return "Weapon"
    return "Other"


ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

# Same wording as ui_desktop/pages/sheet/combat.py's _EXHAUSTION_EFFECTS.
_EXHAUSTION_EFFECTS = {
    0: "",
    1: "Disadvantage on ability checks.",
    2: "Disadvantage on ability checks. Speed halved.",
    3: "Disadvantage on ability checks, attack rolls, and saving throws. Speed halved.",
    4: "Disadvantage on ability checks, attack rolls, and saving throws. "
       "Speed halved. Hit point maximum halved.",
    5: "Disadvantage on ability checks, attack rolls, and saving throws. "
       "Speed 0. Hit point maximum halved.",
    6: "Death.",
}


def _mod_text(mod: int) -> str:
    return f"+{mod}" if mod >= 0 else str(mod)


# Same mapping as ui_desktop's action_tabs.py _build_resource_rows()
# (defined inline there, not an importable module constant) -- a
# resource whose key appears here also gets an on/off toggle against
# char["active_effects"], since these are all "you are currently in
# this form/state" abilities rather than a plain countdown.
_RESOURCE_TOGGLE_MAP = {
    "hybrid_form": "Hybrid Transformation",
    "rage": "Rage",
    "form_of_dread": "Form of Dread",
    "starry_form": "Starry Form",
    "bladesong": "Bladesong",
    "invincible_conqueror": "Invincible Conqueror",
    "exalted_champion": "Exalted Champion",
    "hexblade_curse": "Hexblade's Curse",
    "radiant_soul": "Radiant Soul (Aasimar)",
    "necrotic_shroud": "Necrotic Shroud",
    "gem_flight": "Gem Flight",
    "shifting": "Shifting",
    "vow_of_enmity": "Vow of Enmity",
    "living_legend": "Living Legend",
    "mortal_bulwark": "Mortal Bulwark",
    "elder_champion": "Elder Champion",
    "elemental_gift": "Elemental Gift",
    "writhing_tide": "Writhing Tide",
    "otherworldly_wings": "Otherworldly Wings",
    "trance_of_order": "Trance of Order",
    "umbral_form": "Umbral Form",
    "ghost_walk": "Ghost Walk",
    "steps_of_night": "Steps of Night",
    "arms_of_the_astral_self": "Arms of the Astral Self",
    "awakened_astral_self": "Awakened Astral Self",
    "giants_might": "Giant's Might",
    "giants_might_barb": "Giant's Might",
    "aspect_of_the_wyrm": "Aspect of the Wyrm",
    "spirit_totem": "Spirit Totem",
    "radiant_consumption": "Radiant Consumption",
    "soul_of_the_storm_giant": "Maelstrom Aura",
}


from dnd_app.core.weapons import (can_dedicate as _can_dedicate, weapon_base as _weapon_base,
                                   dedicated_weapon as _dedicated_weapon)


class CharacterSheetBridge(QObject):
    statsChanged = Signal()
    restToastRequested = Signal(str)
    toastRequested = Signal(str)
    # Level up/down and confirmed choices: App.qml saves the character
    # quietly on this (SaveLoadBridge.autoSave()).
    autosaveRequested = Signal()
    # a shared rule needs an answer first -- Use on an action, casting a
    # spell (who is it on? which weapon?): (title, question, options);
    # App.qml asks and calls answerActionQuestion
    actionQuestion = Signal(str, str, list)
    # a longer message to read in a dialog (Green-Flame Blade's damage): title, text
    sheetMessage = Signal(str, str)
    # after an attack roll: (title, the report from core/attacks.py attack_report)
    attackReport = Signal(str, "QVariantMap")
    # a blank spell scroll was used -- QML asks which spell is on it
    # (scroll's equipment name, spell level), then calls bindScrollSpell()
    scrollSpellNeeded = Signal(str, int)

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self.ctrl = CharacterController(char)
        self.ctrl.mark_ui_ready()
        self.ctrl.subscribe(lambda _c: self.statsChanged.emit())
        # Turn tracker -- session-only state (matches ui_desktop's
        # CombatMixin._turn_counts exactly: never saved to the character
        # file, just this-session bookkeeping for the action economy).
        self._turn_counts = {"Action": 0, "Bonus Action": 0, "Reaction": 0}
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        # Session-only, like _turn_counts -- matches ui_desktop's
        # _sp_homebrew checkbox, which is also plain UI state never
        # saved into the character file.
        self._spell_homebrew = False
        # DC of the concentration save the last hit is waiting on (0 = none)
        # -- desktop asks for it straight after the damage; here the
        # combat screen's concentration row shows a Save button.
        self._pending_conc_dc = 0

    @Slot()
    def refresh(self):
        """Recompute every derived stat from the character dict. Call
        this whenever the sheet screen becomes visible -- the player may
        have just finished (or edited) the wizard steps since the sheet
        was last shown."""
        self.ctrl.refresh()

    @Property(str, notify=statsChanged)
    def name(self):
        return self.char.get("name", "")

    @Property(str, notify=statsChanged)
    def raceText(self):
        race = self.char.get("race", "")
        subrace = self.char.get("subrace", "")
        return f"{subrace} {race}".strip() if subrace else race

    @Property(str, notify=statsChanged)
    def classesText(self):
        classes = self.char.get("classes") or []
        return " / ".join(f"{c.get('class','?')} {c.get('level','?')}" for c in classes)

    @Property(str, notify=statsChanged)
    def background(self):
        return self.char.get("background", "")

    @Property(str, notify=statsChanged)
    def alignment(self):
        return self.char.get("alignment", "")

    @Property(bool, notify=statsChanged)
    def hasCharacter(self):
        # Set by EquipmentWizardBridge.confirmEquipment() (the last
        # wizard step) and survives save/load like any other real
        # character field. Also drives App.qml's drawer switching
        # between wizard-step nav and sheet nav.
        return bool(self.char.get("character_created"))

    # ── Quick d20 roll-and-toast -- same as ui_desktop's
    # _quick_roll_toast(), tappable on every ability/save/skill/
    # initiative row rather than a separate Dice Roller screen. ────────
    _AB_SHORT = {"strength": "STR", "dexterity": "DEX", "constitution": "CON",
                 "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA"}

    @Slot(str, int)
    def rollQuickCheck(self, label: str, bonus: int):
        """"<Ability> Save" rolls a save, anything else (ability checks,
        skills, initiative) a check -- with condition rules applied: an
        automatic failure, or two d20s kept high/low."""
        from dnd_app.core.calculator import condition_roll_mode, roll_d20
        first = label.split(" ")[0].strip().lower()
        ability = self._AB_SHORT.get(first, first.upper() if first.upper() in self._AB_SHORT.values() else "")
        kind = "save" if label.lower().endswith(" save") else "check"
        cm = condition_roll_mode(self.char, kind, ability)
        if cm["mode"] == "auto_fail":
            self.toastRequested.emit(f"{label}: automatic failure ({', '.join(cm['sources'])})")
            return
        r = roll_d20(cm["mode"])
        d = r["d20"]
        total = d + bonus
        flair = ""
        if d == 20:
            flair = "  NAT 20!"
        elif d == 1:
            flair = "  Nat 1..."
        sign = f"{bonus:+d}"
        if len(r["rolls"]) == 2:
            tag = "adv" if cm["mode"] == "advantage" else "dis"
            dice = f"[{r['rolls'][0]}/{r['rolls'][1]} {tag}: {', '.join(cm['sources'])}]"
        else:
            dice = f"[{d}]"
        self.toastRequested.emit(f"{label}: {dice} {sign} = {total}{flair}")

    # ── Inspiration ──────────────────────────────────────────────────
    @Property(bool, notify=statsChanged)
    def inspiration(self):
        return bool(self.char.get("inspiration", False))

    @Slot(bool)
    def setInspiration(self, on: bool):
        self.ctrl.update("inspiration", on, rebuild_char=False)
        self.statsChanged.emit()

    # ── Ability scores ──────────────────────────────────────────────
    @Property(list, notify=statsChanged)
    def abilities(self):
        cl = class_levels(self.char)
        save_profs = get_saving_throw_profs(cl)
        out = []
        for ab in ABILITIES:
            score = ability_score(self.char, ab)
            mod = ability_mod(self.char, ab)
            is_save_prof = bool(self.char.get("saving_throws", {}).get(ab, False)) \
                or ab in save_profs
            out.append({
                "ability": ab,
                "score": score,
                "mod": mod,
                "modText": _mod_text(mod),
                # What a plain check of this ability rolls: the modifier,
                # plus anything that adds to every check of it (the Fey
                # Wanderer's Wisdom on Charisma checks).
                "check": ability_check_bonus(self.char, ab),
                "save": get_saving_throw_bonus(self.char, ab),
                "saveText": _mod_text(get_saving_throw_bonus(self.char, ab)),
                "saveProficient": is_save_prof,
            })
        return out

    # ── Combat stats ─────────────────────────────────────────────────
    @Property(int, notify=statsChanged)
    def armorClass(self):
        return get_ac(self.char)

    @Property(str, notify=statsChanged)
    def initiativeText(self):
        return _mod_text(get_initiative(self.char))

    @Property(int, notify=statsChanged)
    def initiative(self):
        return get_initiative(self.char)

    @Property(int, notify=statsChanged)
    def speed(self):
        # walking speed after conditions, exhaustion and effects (Prone
        # halves it, Grappled/Stunned/... zero it) -- what desktop's stat
        # bar shows, not the base number
        from dnd_app.core.calculator import get_effective_speed
        return get_effective_speed(self.char)["walk"]

    @Property(int, notify=statsChanged)
    def maxHp(self):
        # While Wild Shaped, the HP display/controls repurpose to the
        # beast's own pool -- your own HP is untouched and unseen until
        # you revert, matching ui_desktop's combat.py exactly (same
        # spinbox, contextually meaning a different pool).
        beast = self._active_wildshape_beast()
        if beast:
            return beast["hp"]
        return self.char.get("max_hp", 0)

    @Property(int, notify=statsChanged)
    def currentHp(self):
        beast = self._active_wildshape_beast()
        if beast:
            return self.char.get("_wildshape_hp", beast["hp"])
        return self.char.get("current_hp", 0)

    @Property(int, notify=statsChanged)
    def tempHp(self):
        return self.char.get("temp_hp", 0)

    # ── Manual Max HP override -- same as ui_desktop's
    # _on_max_hp_changed/_reset_max_hp_override: hp_max_override, once
    # set, permanently wins over compute_max_hp() on every future
    # refresh (see calculator.py's update_all()) until popped. Not
    # available while Wild Shaped, same as desktop's spinbox going
    # read-only then (the HP controls repurpose to the beast's pool). ──
    @Property(bool, notify=statsChanged)
    def hasMaxHpOverride(self):
        return "hp_max_override" in self.char

    @Property(bool, notify=statsChanged)
    def canOverrideMaxHp(self):
        return self._active_wildshape_beast() is None

    @Slot(int)
    def setMaxHpOverride(self, value: int):
        if not self.canOverrideMaxHp:
            return
        char = self.char
        old_max = char.get("max_hp", value)
        char["hp_max_override"] = value
        char["max_hp"] = value
        diff = value - old_max
        if diff > 0:
            char["current_hp"] = min(char.get("current_hp", value) + diff, value)
        else:
            char["current_hp"] = min(char.get("current_hp", value), value)
        self.statsChanged.emit()

    @Slot()
    def resetMaxHpOverride(self):
        self.char.pop("hp_max_override", None)
        self.ctrl.refresh()
        self.toastRequested.emit("↺ Max HP reset to auto-calculated value")

    # ── Hit Dice spending (short-rest style healing) -- logic copied
    # from ui_desktop's _spend_hit_die() verbatim (it isn't factored
    # into core/, only long_rest()'s recovery side is). ────────────────
    @Property(list, notify=statsChanged)
    def hitDiceList(self):
        out = []
        for die_key in sorted(self.char.get("hit_dice", {}).keys(),
                               key=lambda k: int(k[1:])):
            hd = self.char["hit_dice"][die_key]
            out.append({
                "dieKey": die_key,
                "total": hd.get("total", 0),
                "remaining": hd.get("remaining", 0),
            })
        return out

    @Slot(str)
    def spendHitDie(self, die_key: str):
        hd = self.char.get("hit_dice", {}).get(die_key)
        if not hd or hd.get("remaining", 0) <= 0:
            return
        sides = int(die_key[1:])
        roll = random.randint(1, sides)
        con = ability_mod(self.char, "CON")
        feats = self.char.get("feats", [])
        if "Durable" in feats:
            roll = max(roll, 2 * con, 2)
        heal = max(0, roll + con)
        if "Dwarven Fortitude" in feats:
            heal = max(heal, 1)
        if "Vigor of the Hill Giant" in feats:
            heal += con + get_prof_bonus(self.char)
        hd["remaining"] -= 1
        max_hp = self.char.get("max_hp", 0)
        self.char["current_hp"] = min(max_hp, self.char.get("current_hp", 0) + heal)
        self.toastRequested.emit(f"Spent a {die_key}: healed {heal} HP")
        self.statsChanged.emit()

    @Property(int, notify=statsChanged)
    def proficiencyBonus(self):
        return get_prof_bonus(self.char)

    @Property(int, notify=statsChanged)
    def passivePerception(self):
        return get_passive_perception(self.char)

    # ── Skills ───────────────────────────────────────────────────────
    @Property(list, notify=statsChanged)
    def skills(self):
        # skills dict values: 0=none, 1=half proficiency (e.g. Jack of
        # All Trades-style grants), 2=full proficiency, 3=expertise --
        # see core/calculator.py's get_skill_bonus() for the formula
        # each level maps to.
        out = []
        for skill in sorted(SKILL_ABILITY):
            prof_level = self.char.get("skills", {}).get(skill, 0)
            bonus = get_skill_bonus(self.char, skill)
            out.append({
                "name": skill,
                "ability": SKILL_ABILITY[skill],
                "bonus": bonus,
                "bonusText": _mod_text(bonus),
                "halfProficient": prof_level == 1,
                "proficient": prof_level >= 2,
                "expertise": prof_level >= 3,
            })
        return out

    # ── Manual skill-proficiency editor -- same escape hatch as
    # ui_desktop's _show_skill_prof_menu/_set_skill_prof/
    # _reset_manual_skill_changes: char["skills"] is a pure accumulator
    # rebuild() only ever adds to, never clears, so a manual override
    # (or undoing one) needs this direct path rather than a real grant. ─
    @Slot(str, int)
    def setSkillProficiency(self, skill_name: str, level: int):
        # the player's own setting, kept as an override on top of what's
        # granted (core/builder.py), so a rebuild doesn't undo it
        from dnd_app.core.builder import set_skill_level
        set_skill_level(self.char, skill_name, level)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot()
    def resetSkillProficiencies(self):
        from dnd_app.core.builder import reset_skill_levels
        reset_skill_levels(self.char)
        self.ctrl.refresh()
        self.toastRequested.emit("↺ Skill proficiencies reset to granted baseline")

    # ── Gear ─────────────────────────────────────────────────────────
    @Property(str, notify=statsChanged)
    def armorWorn(self):
        return self.char.get("armor_worn", "No Armor")

    @Property(bool, notify=statsChanged)
    def hasShield(self):
        return bool(self.char.get("shield", False))

    # ── Equip / un-equip armor, shield, and weapons -- ported from
    # ui_desktop's gear.py _toggle_armor_worn/_toggle_weapon_equipped.
    # Candidates are restricted to owned inventory (char["equipment"]),
    # matching desktop exactly. Shields get their OWN toggle here (a
    # real char["shield"] bool) rather than desktop's inventory-checkbox
    # path, which has a pre-existing bug: a mundane "Shield" item is
    # also `is_armor` (it's in ARMOR_DICT), so checking it there calls
    # _toggle_armor_worn("Shield", True) and clobbers armor_worn instead
    # of setting shield=True -- fixed forward here rather than copied.
    @Property(list, notify=statsChanged)
    def equippableArmor(self):
        out = []
        for e in self.char.get("equipment", []):
            name = e.get("name", "")
            adata = ARMOR_DICT.get(name)
            if not adata or adata.get("type") == "shield":
                continue
            out.append({"name": name, "worn": self.char.get("armor_worn", "") == name})
        return out

    @Property(bool, notify=statsChanged)
    def ownsShield(self):
        return any(ARMOR_DICT.get(e.get("name", ""), {}).get("type") == "shield"
                   for e in self.char.get("equipment", []))

    @Property(list, notify=statsChanged)
    def equippableWeapons(self):
        equipped = set(self.char.get("equipped_weapons", []))
        out = []
        for e in self.char.get("equipment", []):
            name = e.get("name", "")
            base_name, _ = parse_magic_suffix(name)
            if base_name not in WEAPON_DICT:
                continue
            out.append({"name": name, "equipped": name in equipped})
        return out

    @Slot(str, bool)
    def toggleArmorWorn(self, name: str, wear: bool):
        if wear:
            self.char["armor_worn"] = name
        elif self.char.get("armor_worn", "") == name:
            self.char["armor_worn"] = "No Armor"
        self.ctrl.refresh()

    @Slot(bool)
    def toggleShieldWorn(self, on: bool):
        self.char["shield"] = on
        self.ctrl.refresh()

    @Slot(str, bool)
    def toggleWeaponEquipped(self, name: str, equip: bool):
        # the hands rules are shared with the desktop (core/weapons.py)
        from dnd_app.core.weapons import equip_weapon, unequip_weapon
        if equip:
            equip_weapon(self.char, name)
        else:
            unequip_weapon(self.char, name)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Property(list, notify=statsChanged)
    def weapons(self):
        """Every attack row on the Combat screen. The numbers come from
        core/attacks.py -- the same as desktop's Combat tab: attacks that
        aren't a weapon in hand (Martial Arts, natural weapons, the unarmed
        strike, Wild Shape...) first, then each weapon in hand
        (weapon_attack). What's on now is listed under the damage
        (onHitBonusText); what you can add is offered after the roll."""
        from dnd_app.core.attacks import other_attacks, weapon_attack
        from dnd_app.core.riders import rider_text
        char = self.char
        cond_status = get_condition_attack_status(char)
        self._attack_rows = {}
        out = []

        def card(row, category, extra):
            self._attack_rows[row["name"]] = row
            d = {
                "name": row["name"], "badge": row.get("badge", ""), "note": row.get("note", ""),
                "category": category, "damageType": row["damage_type"],
                "attackBonusText": _mod_text(row["atk"]) if row["atk"] is not None else "",
                "damageDisplay": row["damage"], "magicBonus": 0, "material": "", "proficient": True,
                "advantage": bool(cond_status.get("advantage")),
                "disadvantage": bool(cond_status.get("disadvantage")),
                "canPowerAttack": False, "powerAttackActive": False,
                "onHitBonusText": rider_text(row["riders"]), "offhandText": "",
                "ammoKind": "", "ammoLabel": "", "ammoCount": 0,
                "attackBonus": row["atk"] if row["atk"] is not None else 0,
            }
            d.update(extra)
            out.append(d)

        for a in other_attacks(char):
            card(a, "Unarmed" if a["kind"] == "unarmed" else "Natural weapon", {})
        for wpn_name in char.get("equipped_weapons", []):
            w = weapon_attack(char, wpn_name)
            card(w, w["category"], {
                "magicBonus": w["magic_bonus"], "material": w["material"] or "",
                "proficient": w["proficient"],
                "canPowerAttack": w["can_power_attack"], "powerAttackActive": w["power_attack"],
                "offhandText": (f"Off-hand attack (a bonus action): {w['offhand']} {w['damage_type']}"
                                if w["offhand"] else ""),
                "ammoKind": w["ammo"], "ammoLabel": ammo_label(w["ammo"]) if w["ammo"] else "",
                "ammoCount": ammo_count(char, w["ammo"]) if w["ammo"] else 0,
            })
        return out

    # ── Weapon roll (Combat screen's Roll to Hit button) ─────────────
    # The roll, then what you can add with each one's cost -- only what you
    # can pay for now -- in App.qml's attack dialog (attackReport); the
    # ticked ones come back through takeAttackOptions (core/attacks.py,
    # the same as desktop's Hit button)
    @Slot(str)
    def rollWeaponAttack(self, name: str):
        from dnd_app.core.attacks import roll_attack, attack_report
        _ = self.weapons                       # the rows as they are now
        row = getattr(self, "_attack_rows", {}).get(name)
        if row is None or row.get("atk") is None:
            return
        # A shot takes one piece of ammunition from the inventory
        if row.get("ammo"):
            label = ammo_label(row["ammo"])
            if not spend_ammo(self.char, row["ammo"]):
                self.toastRequested.emit(f"Out of {label.lower()} -- tap the {label} counter to add more")
                return
            self.statsChanged.emit()
        roll = roll_attack(self.char, row)
        free = [b for b in ("Action", "Bonus Action", "Reaction")
                if self._turn_counts.get(b, 0) < self._turn_limit(b)]
        report = attack_report(self.char, row, roll, free)
        if row.get("ammo"):
            left = f"{ammo_count(self.char, row['ammo'])} {ammo_label(row['ammo']).lower()} left"
            report["message"] += f"\n{left}"
            report["roll"]["note"] = "; ".join(x for x in (report["roll"].get("note"), left) if x)
        self._last_attack_row = row
        self._last_attack_roll = report["roll"]
        self.attackReport.emit(report["title"], report)

    @Slot(list, bool)
    def takeAttackOptions(self, keys, hit):
        """The attack dialog's "It hit" (hit) or "Missed": what's ticked is
        paid for (a slot, ki, a die, once a turn...), asking first when
        there's a choice, and a hit sets off what it carries (a smite)."""
        from dnd_app.core.attacks import take_attack_options
        row = getattr(self, "_last_attack_row", None)
        picked = [str(k) for k in keys]
        if row is None:
            return
        roll = getattr(self, "_last_attack_roll", None)

        def done(res):
            for slot in res.get("slots", []):
                self._mark_turn_used(slot)
            if res.get("toast"):
                self.toastRequested.emit(res["toast"])
            if res.get("refresh"):
                self.ctrl.refresh()
            self.statsChanged.emit()
        self._ask_through(row["name"], lambda a: take_attack_options(self.char, row, picked, a,
                                                                    hit=bool(hit), roll=roll), done)

    @Slot(str, int)
    def setAmmoCount(self, kind: str, n: int):
        """How many pieces of this ammunition you have -- the inventory
        follows (core/ammo.py set_ammo), same as desktop's counter."""
        if not kind or n < 0 or n == ammo_count(self.char, kind):
            return
        total = set_ammo(self.char, kind, n)
        self.toastRequested.emit(f"{ammo_label(kind)}: {total}")
        self.statsChanged.emit()

    @Slot(str)
    def toggleWeaponPowerAttack(self, wpn_name: str):
        pa_list = self.char.setdefault("power_attack_weapons", [])
        if wpn_name in pa_list:
            pa_list.remove(wpn_name)
        else:
            pa_list.append(wpn_name)
        self.statsChanged.emit()

    @Property(list, notify=statsChanged)
    def equipment(self):
        # isPotion/isScroll use the same name-substring detection as
        # ui_desktop's gear.py context menu (no dedicated data flag for
        # "is a potion/scroll" exists beyond a magic item's own "type").
        # category/icon/detail/equip* drive the Equipment screen's
        # grouped inventory (Weapons / Armor / Consumables / Gear), where
        # a weapon is equipped and armor worn straight from its own row.
        out = []
        equipped_weapons = set(self.char.get("equipped_weapons", []))
        worn = self.char.get("armor_worn", "")
        for e in self.char.get("equipment", []):
            name = e.get("name", "")
            lname = name.lower()
            is_potion = e.get("type") == "Potion" or "potion" in lname
            is_scroll = is_scroll_name(name)
            base_name, _ = parse_magic_suffix(name)
            wdata = WEAPON_DICT.get(base_name)
            adata = ARMOR_DICT.get(name)
            if wdata:
                category, icon, equip_kind = "Weapons", "combat", "weapon"
                detail = f"{wdata.get('damage', '')} {wdata.get('dmg_type', '')}".strip()
                equipped = name in equipped_weapons
                # "1 of 3 equipped", "dedicated weapon"
                from dnd_app.core.weapons import inventory_notes
                notes = inventory_notes(self.char, name, e.get("qty", 1))
                detail = " · ".join([detail] + notes) if notes else detail
            elif adata and adata.get("type") == "shield":
                category, icon, equip_kind = "Armor", "shield", "shield"
                detail = f"+{adata.get('ac', 2)} AC"
                equipped = bool(self.char.get("shield"))
            elif adata and adata.get("type") != "none":
                category, icon, equip_kind = "Armor", "shield", "armor"
                detail = f"AC {adata.get('ac')} · {adata.get('type', '').title()}"
                equipped = worn == name
            elif is_potion or is_scroll:
                category, icon, equip_kind = "Consumables", "potion" if is_potion else "file", ""
                detail, equipped = "", False
            else:
                # kits, instruments, lights and thrown flasks get their own
                # icon (gear_icon); flasks that are used up go with Consumables
                category = "Consumables" if is_thrown_consumable(name) else "Tools & Gear"
                icon, equip_kind = gear_icon(name) or "package", ""
                detail, equipped = "", False
            weight = e.get("weight", (wdata or adata or {}).get("weight", 0)) or 0
            cost = e.get("cost", (wdata or adata or {}).get("cost", 0)) or 0
            out.append({
                "name": name,
                "qty": e.get("qty", 1),
                "isPotion": is_potion,
                "isScroll": is_scroll,
                "category": category,
                "icon": icon,
                "detail": detail,
                "weight": weight,
                "cost": cost,
                "equipKind": equip_kind,
                "equipped": equipped,
                # Dedicated Weapon (Monk, Tasha's optional feature)
                "canDedicate": bool(wdata) and _can_dedicate(self.char, name),
                "dedicated": bool(wdata) and _weapon_base(name) == _dedicated_weapon(self.char) != "",
                # magic consumables (potions, scrolls) carry a rarity --
                # their row is bordered in its colour, like magic item cards
                "rarity": (e.get("rarity", "") or (_catalog_entry(name) or {}).get("rarity", ""))
                          if e.get("magic") or parse_spell_scroll(name) else "",
            })
        return out

    @Slot(str)
    def setDedicatedWeapon(self, name: str):
        """Dedicated Weapon: this weapon counts as a monk weapon until you
        pick another ("" = none)."""
        if name:
            self.char["dedicated_weapon"] = name
        else:
            self.char.pop("dedicated_weapon", None)
        self.ctrl.refresh()
        self.statsChanged.emit()

    _INVENTORY_GROUPS = (("Weapons", "combat"), ("Armor", "shield"),
                         ("Consumables", "potion"), ("Tools & Gear", "package"))

    @Property(list, notify=statsChanged)
    def inventoryGroups(self):
        items = self.equipment
        out = []
        for group, icon in self._INVENTORY_GROUPS:
            # by name (equipping doesn't move a row); magic potions/scrolls
            # by rarity (Common -> Artifact) then name, after the mundane ones
            members = sorted((i for i in items if i["category"] == group),
                             key=lambda i: _mi_sort_key(i["rarity"], i["name"]) if i["rarity"] else (-1, i["name"].casefold()))
            if members:
                out.append({"group": group, "icon": icon, "items": members})
        return out

    @Property(dict, notify=statsChanged)
    def carryLoad(self):
        detail = get_carry_capacity_detail(self.char)
        total = get_total_weight(self.char)
        cap = detail["carry"] or 1
        return {"weight": round(total, 1), "capacity": detail["carry"],
                "fraction": min(1.0, total / cap)}

    @Slot(str)
    def usePotion(self, name: str):
        eq = self.char.get("equipment", [])
        entry = next((e for e in eq if e.get("name") == name), None)
        if not entry:
            return
        entry["qty"] = entry.get("qty", 1) - 1
        if entry["qty"] <= 0:
            self.char["equipment"] = [e for e in eq if e.get("name") != name]

        instant = INSTANT_POTION_EFFECTS.get(name)
        if instant:
            msgs = []
            if "heal_dice" in instant:
                count, sides, bonus = instant["heal_dice"]
                rolled = sum(random.randint(1, sides) for _ in range(count)) + bonus
                mx = self.char.get("max_hp", 0)
                cur = self.char.get("current_hp", 0)
                self.char["current_hp"] = min(mx, cur + rolled)
                msgs.append(f"healed {rolled} HP")
            if "damage_dice" in instant:
                count, sides, bonus = instant["damage_dice"]
                rolled = sum(random.randint(1, sides) for _ in range(count)) + bonus
                self.char["current_hp"] = max(0, self.char.get("current_hp", 0) - rolled)
                dtype = instant.get("damage_type", "")
                msgs.append(f"took {rolled} {dtype} damage".replace("  ", " "))
            if "add_condition" in instant:
                conds = self.char.setdefault("conditions", [])
                if instant["add_condition"] not in conds:
                    conds.append(instant["add_condition"])
                msgs.append(f"gained {instant['add_condition']}")
            if "cure_conditions" in instant:
                conds = self.char.get("conditions", [])
                removed = [c for c in instant["cure_conditions"] if c in conds]
                self.char["conditions"] = [c for c in conds if c not in instant["cure_conditions"]]
                if removed:
                    msgs.append(f"cured {', '.join(removed)}")
            summary = "; ".join(msgs) if msgs else instant.get("cure_note", "used")
            self.toastRequested.emit(f"{name} -- {summary}")
        else:
            info = EFFECT_TABLE.get(name, {})
            if info:
                fx = self.char.setdefault("active_effects", [])
                if name not in fx:
                    fx.append(name)
                    self.toastRequested.emit(f"{name} -- active (see Actions tab)")
                else:
                    self.toastRequested.emit(f"{name} -- already active")
            else:
                self.toastRequested.emit(f"Drank {name}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str)
    def useScroll(self, name: str):
        """Spell scrolls cast their spell (core/spellcasting.py: class
        list, the DC 10 + level check, the scroll's own DC/attack); other
        scrolls (Scroll of Protection...) apply their effect."""
        if parse_spell_scroll(name):
            self._use_spell_scroll(name)
            return
        eq = self.char.get("equipment", [])
        entry = next((e for e in eq if e.get("name") == name), None)
        if not entry:
            return
        entry["qty"] = entry.get("qty", 1) - 1
        if entry["qty"] <= 0:
            self.char["equipment"] = [e for e in eq if e.get("name") != name]
        info = EFFECT_TABLE.get(name, {})
        if info:
            fx = self.char.setdefault("active_effects", [])
            if name not in fx:
                fx.append(name)
                self.toastRequested.emit(f"{name} -- active (see Actions tab)")
            else:
                self.toastRequested.emit(f"{name} -- already active")
        else:
            self.toastRequested.emit(f"Read {name}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    def _use_spell_scroll(self, name: str):
        level, spell_name = parse_spell_scroll(name)
        if not spell_name:
            self.scrollSpellNeeded.emit(name, level)
            return
        spell = get_spell(spell_name)
        if spell:
            ct = (spell.get("cast_time") or "1 action").strip().lower()
            bucket = {"1 action": "Action", "bonus action": "Bonus Action", "reaction": "Reaction"}.get(ct)
            if bucket and self._turn_blocked(bucket):
                return
            if self.char.get("_wildshape_active") and not self._has_beast_spells():
                self.toastRequested.emit("Can't read a scroll while Wild Shaped -- revert to your normal form first")
                return
        res = use_spell_scroll(self.char, name)
        if res["status"] == "cast" and spell:
            if spell.get("concentration"):
                start_concentration(self.char, spell_name)
            self._mark_spell_cast_time(spell)
            self._maybe_apply_spell_active_effect(spell, spell.get("level", 0), res["message"])
        elif res["status"] == "failed" and spell:
            self._mark_spell_cast_time(spell)
            self.toastRequested.emit(res["message"])
        else:
            self.toastRequested.emit(res["message"])
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def bindScrollSpell(self, name: str, spell_name: str):
        """Write a spell onto one blank scroll, then read it (it was the Use
        button that asked)."""
        new_name = bind_spell_scroll(self.char, name, spell_name)
        if not new_name:
            self.toastRequested.emit(f"{spell_name} can't go on that scroll")
            return
        self.statsChanged.emit()
        self._use_spell_scroll(new_name)

    @Property(list, notify=statsChanged)
    def currency(self):
        cur = self.char.get("currency", {})
        return [{"denom": d, "amount": cur[d]} for d in _CURRENCY_ORDER if cur.get(d)]

    # ── Currency editing -- same as ui_desktop's _on_currency_change:
    # five fully independent raw integers, no cross-denomination
    # conversion of any kind. ───────────────────────────────────────────
    @Property(list, notify=statsChanged)
    def currencyAll(self):
        cur = self.char.get("currency", {})
        return [{"denom": d, "amount": cur.get(d, 0)} for d in _CURRENCY_ORDER]

    @Slot(str, int)
    def setCurrency(self, denom: str, value: int):
        self.char.setdefault("currency", {})[denom] = max(0, value)
        self.statsChanged.emit()

    @Property(str, notify=statsChanged)
    def carryText(self):
        detail = get_carry_capacity_detail(self.char)
        total = get_total_weight(self.char)
        return f"{total:g} / {detail['carry']} lb"

    # ── Equipment browser (add mundane items) ───────────────────────
    # First slice of ui_desktop's gear.py's mundane browser: search
    # across weapons/armor/adventuring gear/tools/Silvered-Adamantine
    # weapon variants, and add to char["equipment"] with a fixed qty of
    # 1 (desktop prompts for a quantity via a dialog; the QML screen
    # exposes its own quantity spinner instead of a second slot
    # parameter here). Mounts (which get a full Companions-tab stat
    # block on desktop, not a generic equipment line) aren't ported yet.
    # Matches desktop's gear.py mundane browser's category QComboBox
    # exactly (minus "Mounts & Vehicles", which isn't sold through this
    # browser on Android -- see the module docstring above).
    @Property(list, constant=True)
    def equipmentCategories(self):
        return ["All", "Weapons — Simple", "Weapons — Martial",
                "Materials (Silvered/Adamantine)", "Armor", "Adventuring Gear", "Tools"]

    @Slot(str, str, str, result=list)
    def searchAddableEquipment(self, query: str, category: str = "All", sort_by: str = "Name"):
        q = (query or "").strip().lower()
        category = category or "All"
        out = []
        if category in ("All", "Weapons — Simple", "Weapons — Martial"):
            for name, wdata in WEAPON_DICT.items():
                wcat = wdata.get("category", "Weapon")
                if category == "Weapons — Simple" and not wcat.startswith("Simple"):
                    continue
                if category == "Weapons — Martial" and not wcat.startswith("Martial"):
                    continue
                if q and q not in name.lower():
                    continue
                out.append({
                    "name": name, "category": wcat,
                    "detail": f"{wdata.get('damage', '—')} {wdata.get('dmg_type', '')}".strip(),
                    "weight": float(wdata.get("weight", 0) or 0), "cost": float(wdata.get("cost", 0) or 0),
                })
        # Silvered (any weapon, +100gp) / Adamantine (melee weapons
        # only -- ranged weapons can't be adamantine themselves, only
        # their ammunition, per XGE) material variants -- matches
        # desktop's gear.py Materials browser section exactly. Combat's
        # weapon math already resolves these back to their base stats
        # via parse_material_prefix once equipped.
        if category in ("All", "Materials (Silvered/Adamantine)"):
            melee_weapons = SIMPLE_MELEE + MARTIAL_MELEE
            ranged_weapons = SIMPLE_RANGED + MARTIAL_RANGED + FIREARMS
            for base_name, wcat, dmg, dtype, wt, cost, props in melee_weapons + ranged_weapons:
                name = f"Silvered {base_name}"
                if q and q not in name.lower():
                    continue
                out.append({"name": name, "category": wcat, "detail": f"{dmg} {dtype}".strip(),
                            "weight": float(wt or 0), "cost": float(cost or 0) + 100})
            for base_name, wcat, dmg, dtype, wt, cost, props in melee_weapons:
                name = f"Adamantine {base_name}"
                if q and q not in name.lower():
                    continue
                out.append({"name": name, "category": wcat, "detail": f"{dmg} {dtype}".strip(),
                            "weight": float(wt or 0), "cost": float(cost or 0) + 500})
        if category in ("All", "Armor"):
            for name, adata in ARMOR_DICT.items():
                if name == "No Armor":
                    continue
                if q and q not in name.lower():
                    continue
                out.append({
                    "name": name, "category": adata.get("type", "Armor").title(),
                    "detail": f"AC {adata.get('ac', '—')}", "weight": float(adata.get("weight", 0) or 0),
                    "cost": float(adata.get("cost", 0) or 0),
                })
        if category in ("All", "Adventuring Gear"):
            for row in ADVENTURING_GEAR:
                name = row[0]
                if q and q not in name.lower():
                    continue
                weight = float(row[1]) if len(row) > 1 and row[1] is not None else 0.0
                cost = float(row[2]) if len(row) > 2 and row[2] is not None else 0.0
                notes = row[3] if len(row) > 3 else ""
                out.append({"name": name, "category": "Gear", "detail": notes, "weight": weight, "cost": cost})
        if category in ("All", "Tools"):
            for name in ALL_TOOLS:
                if q and q not in name.lower():
                    continue
                out.append({"name": name, "category": "Tool", "detail": "Tool proficiency", "weight": 0.0, "cost": 0.0})

        if sort_by == "Cost":
            out.sort(key=lambda e: (e["cost"], e["name"]))
        elif sort_by == "Weight":
            out.sort(key=lambda e: (e["weight"], e["name"]))
        else:
            out.sort(key=lambda e: e["name"])
        return out

    @Slot(str, int)
    def addEquipmentItem(self, name: str, qty: int):
        qty = max(1, qty)
        weight = 0.0
        base_name, _material = parse_material_prefix(name)
        wd = WEAPON_DICT.get(base_name)
        if wd:
            weight = float(wd.get("weight", 0) or 0)
        elif base_name in ARMOR_DICT:
            weight = float(ARMOR_DICT[base_name].get("weight", 0) or 0)
        else:
            for row in ADVENTURING_GEAR:
                if row[0] == base_name:
                    weight = float(row[1]) if len(row) > 1 and row[1] is not None else 0.0
                    break
        eq = self.char.setdefault("equipment", [])
        existing = next((e for e in eq if isinstance(e, dict) and e.get("name") == name), None)
        if existing:
            existing["qty"] = existing.get("qty", 1) + qty
        else:
            eq.append({"name": name, "qty": qty, "weight": weight, "notes": ""})
        self.statsChanged.emit()

    @Slot(str, int)
    def addCustomEquipmentItem(self, name: str, qty: int):
        """Matches desktop's gear.py _add_equipment_dialog ("Add Custom
        Item"): a free-text item not in any catalog -- DM-given loot,
        homebrew gear, anything the mundane/magic browsers don't cover.
        Recorded with 0 weight, same as desktop (a player can't specify
        a weight for it either)."""
        name = (name or "").strip()
        if not name:
            return
        qty = max(1, qty)
        eq = self.char.setdefault("equipment", [])
        existing = next((e for e in eq if isinstance(e, dict) and e.get("name") == name), None)
        if existing:
            existing["qty"] = existing.get("qty", 1) + qty
        else:
            eq.append({"name": name, "qty": qty, "weight": 0.0, "notes": ""})
        self.statsChanged.emit()

    # ── Ability Score Manuals/Tomes ("Study" action) ────────────────
    @Slot(str, result=bool)
    def canStudyManual(self, uid: str) -> bool:
        """A manual/tome copy you haven't studied yet (each works once)."""
        return can_study_manual(find_magic_item(self.char, uid))

    @Slot(str)
    def studyAbilityManual(self, uid: str):
        """Matches desktop's _study_manual: permanently raises the
        matching ability score by 2 (no cap on this kind of magical
        increase) -- the book stays, marked studied, and can't be
        studied again."""
        entry = find_magic_item(self.char, uid)
        done = study_owned_manual(self.char, uid)
        if not done:
            self.toastRequested.emit("You've already studied this book -- its magic is spent.")
            return
        ability, score = done
        self.ctrl.refresh()
        self.toastRequested.emit(
            f"{entry['name']} -- your {ability} score permanently increases by 2 (now {score})")
        self.statsChanged.emit()

    @Slot(str)
    def removeEquipmentItem(self, name: str):
        eq = self.char.get("equipment", [])
        self.char["equipment"] = [e for e in eq if not (isinstance(e, dict) and e.get("name") == name)]
        self.statsChanged.emit()

    @Slot(str, int)
    def setEquipmentQuantity(self, name: str, qty: int):
        """Set how many of an item you have -- 0 removes it."""
        if qty <= 0:
            self.removeEquipmentItem(name)
            return
        for e in self.char.get("equipment", []):
            if isinstance(e, dict) and e.get("name") == name:
                if e.get("qty", 1) != qty:
                    e["qty"] = qty
                    self.statsChanged.emit()
                return

    # ── Magic items ──────────────────────────────────────────────────
    # Each owned copy is its own entry with a "uid" (core/magic_items.py's
    # owned-copy helpers), so the slots below take that uid, not a name.
    # Full port of ui_desktop's gear.py magic item browser + list:
    # search/add, attunement toggle, equip toggle (synced to
    # equipped_weapons/armor_worn/shield same as desktop's
    # _toggle_equipped), remove, the "+N Weapon/Armor/Shield" enchant
    # flow, the spell-scroll spell-choice prompt, and the resistance-
    # choice damage-type picker (Ring/Armor of Resistance, Absorbing
    # Tattoo, Orb of Shielding).
    @Property(list, notify=statsChanged)
    def magicItems(self):
        out = []
        for entry in owned_magic_items(self.char):
            name = entry.get("name", "")
            catalog = get_magic_item(name) or {}
            eff = get_item_effect(name)
            resistance_pool = list(eff.get("pool", [])) if isinstance(eff, dict) and eff.get("type") == "resistance_choice" else []
            current_dmg = self.char.get("_choices", {}).get(f"item_dmgtype_{name}", [])
            out.append({
                "name": name,
                "rarity": catalog.get("rarity", ""),
                "type": catalog.get("type", ""),
                "uid": entry["uid"],
                "needsAttunement": bool(catalog.get("attunement")),
                "attuned": bool(entry.get("attuned")),
                "equipped": bool(entry.get("equipped", True)),
                "studied": bool(entry.get("studied")),
                "canStudy": can_study_manual(entry),
                "isAmmo": is_magic_ammunition(name),
                "qty": entry.get("qty", 1),
                "resistanceChoicePool": resistance_pool,
                "resistanceChoiceCurrent": current_dmg[0] if current_dmg else "",
                # an "any sword" item (Flame Tongue...): which weapon it is
                "baseOptions": _base_weapon_options(name),
                "base": _weapon_base_of(self.char, name) if _base_weapon_options(name) else "",
            })
        out.sort(key=lambda i: _mi_sort_key(i["rarity"], i["name"]))
        return out

    @Slot(str, bool)
    def setMagicItemEquipped(self, uid: str, on: bool):
        set_owned_magic_item_equipped(self.char, uid, on)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, int)
    def setMagicItemQuantity(self, uid: str, qty: int):
        """Magic ammunition stacks -- 0 removes the stack."""
        set_owned_magic_item_qty(self.char, uid, qty)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def setMagicItemDamageType(self, item_name: str, damage_type: str):
        choices = self.char.setdefault("_choices", {})
        key = f"item_dmgtype_{item_name}"
        if damage_type:
            choices[key] = [damage_type]
        else:
            choices.pop(key, None)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, result="QVariant")
    def classifyMagicItemPick(self, name: str):
        """Decides which follow-up prompt (if any) QML needs before
        actually adding this catalog entry -- a generic "+N Weapon/
        Armor/Shield" needs the enchant-target flow instead of being
        added as a literal catalog item, and a generic "Spell Scroll
        (Nth level)" needs a which-spell prompt so the scroll becomes a
        concrete, castable item."""
        m = re.match(r'^\+([123]) (Weapon|Armor|Shield)$', name)
        if m:
            return {"kind": "enchant", "bonus": int(m.group(1)), "itemKind": m.group(2)}
        m2 = re.match(r'^Spell Scroll \((Cantrip|\d+(?:st|nd|rd|th) level)\)$', name)
        if m2:
            level = 0 if m2.group(1) == "Cantrip" else int(re.match(r'\d+', m2.group(1)).group())
            return {"kind": "scroll", "level": level}
        return {"kind": "plain"}

    @Slot(int, result=list)
    def spellsForScrollLevel(self, level: int):
        return sorted(s["name"] for s in SPELLS_BY_LEVEL.get(level, []))

    @Slot(str, str)
    def addMagicItemWithScrollSpell(self, name: str, spell_name: str):
        """A spell scroll always carries its spell -- never added blank."""
        if not spell_name:
            return
        self.addMagicItem(f"{name} — {spell_name}")

    @Slot(str, int, result=list)
    def enchantCandidates(self, kind: str, bonus: int):
        """Owned/equipped candidates of the right mundane type this +N
        enchantment can apply to -- verbatim port of desktop's
        _open_enchant_dialog candidate-building (Weapon/Armor only;
        Shield is a single binary slot with no candidate list)."""
        char = self.char
        if kind == "Weapon":
            equipped_list = char.get("equipped_weapons", [])
            owned_names = {e.get("name", "") for e in char.get("equipment", []) if isinstance(e, dict)}
            valid_names = {w[0] for w in ALL_WEAPONS}
        else:
            cur_armor = char.get("armor_worn", "No Armor")
            equipped_list = [cur_armor] if cur_armor != "No Armor" else []
            owned_names = {e.get("name", "") for e in char.get("equipment", []) if isinstance(e, dict)}
            valid_names = {a[0] for a in ARMOR if a[0] not in ("No Armor", "Mage Armor (spell)")}
        candidates = []
        seen = set()
        for n in equipped_list:
            base, existing_bonus = parse_magic_suffix(n)
            if base in valid_names and base not in seen:
                candidates.append({"name": base, "equipped": True, "existingBonus": existing_bonus})
                seen.add(base)
        for n in owned_names:
            base, existing_bonus = parse_magic_suffix(n)
            if base in valid_names and base not in seen:
                candidates.append({"name": base, "equipped": False, "existingBonus": existing_bonus})
                seen.add(base)
        candidates.sort(key=lambda c: (not c["equipped"], c["name"]))
        return candidates

    @Slot(str, int, str)
    def applyEnchant(self, kind: str, bonus: int, base_name: str):
        char = self.char
        enchanted_name = f"{base_name} +{bonus}"
        if kind == "Weapon":
            equipped = char.setdefault("equipped_weapons", [])
            for i, n in enumerate(equipped):
                if parse_magic_suffix(n)[0] == base_name:
                    equipped[i] = enchanted_name
                    break
            else:
                equipped.append(enchanted_name)
        else:
            char["armor_worn"] = enchanted_name
        items = char.setdefault("magic_items", [])
        if not any((i.get("name") if isinstance(i, dict) else i) == enchanted_name for i in items):
            items.append({"name": enchanted_name, "attunement": False, "equipped": True, "notes": ""})
        self.ctrl.refresh()
        self.toastRequested.emit(f"{enchanted_name} equipped")
        self.statsChanged.emit()

    @Slot(int)
    def applyShieldEnchant(self, bonus: int):
        char = self.char
        char["shield"] = True
        char["shield_magic_bonus"] = max(bonus, char.get("shield_magic_bonus", 0))
        item_name = f"Shield +{bonus}"
        items = char.setdefault("magic_items", [])
        if not any((i.get("name") if isinstance(i, dict) else i) == item_name for i in items):
            items.append({"name": item_name, "attunement": False, "equipped": True, "notes": ""})
        self.ctrl.refresh()
        self.toastRequested.emit(f"{item_name} equipped")
        self.statsChanged.emit()

    # Matches desktop's gear.py magic item browser's three QComboBoxes.
    @Property(list, constant=True)
    def magicItemSlots(self):
        return ["All Slots"] + list(_MI_SLOT_KEYWORDS.keys())

    @Property(list, constant=True)
    def magicItemRarities(self):
        return ["All Rarities"] + list(_MI_RARITY_ORDER)

    @Property(list, constant=True)
    def magicItemAttunementOptions(self):
        return ["All", "Requires Attunement", "No Attunement"]

    @Slot(str, str, str, str, result=list)
    def searchAddableMagicItems(self, query: str, slot_filter: str = "All Slots",
                                 rarity_filter: str = "All Rarities", attunement_filter: str = "All"):
        q = (query or "").strip().lower()
        slot_filter = slot_filter or "All Slots"
        rarity_filter = rarity_filter or "All Rarities"
        attunement_filter = attunement_filter or "All"
        out = []
        for item in ALL_MAGIC_ITEMS:
            name = item["name"]
            if q and q not in name.lower():
                continue
            rarity = item.get("rarity", "?")
            itype = item.get("type", "?")
            attune = bool(item.get("attunement", False))
            slot = _magic_item_slot(name, itype)
            if slot_filter != "All Slots" and slot != slot_filter:
                continue
            if rarity_filter != "All Rarities" and rarity != rarity_filter:
                continue
            if attunement_filter == "Requires Attunement" and not attune:
                continue
            if attunement_filter == "No Attunement" and attune:
                continue
            out.append({"name": name, "rarity": rarity, "type": itype})
        out.sort(key=lambda i: _mi_sort_key(i["rarity"], i["name"]))
        return out

    @Slot(str)
    def addMagicItem(self, name: str):
        catalog = _catalog_entry(name) or {}
        itype = catalog.get("type", "")
        is_consumable = itype in ("Potion", "Scroll") or "potion" in name.lower() or "scroll" in name.lower()
        if is_consumable:
            eq = self.char.setdefault("equipment", [])
            existing = next((e for e in eq if isinstance(e, dict) and e.get("name") == name), None)
            if existing:
                existing["qty"] = existing.get("qty", 1) + 1
            else:
                eq.append({"name": name, "qty": 1, "weight": 0.5, "notes": "",
                          "magic": True, "rarity": catalog.get("rarity", ""), "desc": catalog.get("desc", "")})
        else:
            # every copy is its own entry (only ammunition stacks)
            add_owned_magic_item(self.char, name)
            self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def setWeaponBase(self, item_name: str, base: str):
        """Which weapon an "any sword" item is (core/riders.py) -- its
        dice, properties and proficiency on the Combat screen follow."""
        from dnd_app.core.riders import set_weapon_base
        if set_weapon_base(self.char, item_name, base):
            self.ctrl.refresh()
            self.toastRequested.emit(f"{item_name} is a {base.lower()}")
            self.statsChanged.emit()

    @Slot(str, bool)
    def setMagicItemAttuned(self, uid: str, on: bool):
        why = set_owned_magic_item_attuned(self.char, uid, on)
        if why:
            self.toastRequested.emit(why)
            return
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str)
    def removeMagicItem(self, uid: str):
        remove_owned_magic_item(self.char, uid)
        self.ctrl.refresh()
        self.statsChanged.emit()

    # ── Simple HP adjustments (damage/heal/temp) ───────────────────
    @Slot(int)
    def applyDamage(self, amount: int):
        """Damage button. A Wild Shape beast form takes it from its own
        pool first; everything about your own hit points (temp HP, massive
        damage, death saves, rage, concentration) is core/dying.py's
        take_damage(), the same rules as desktop's _do_damage()."""
        if amount <= 0:
            return
        char = self.char
        beast = self._active_wildshape_beast()
        if beast:
            # Wild Shape (PHB p.66): the beast's hit points take the hit.
            # Reaching 0 reverts you to your normal form, and the damage
            # left over carries on to your own hit points.
            cur = char.get("_wildshape_hp", beast["hp"])
            if amount < cur:
                char["_wildshape_hp"] = cur - amount
                if self.isConcentrating:
                    self._pending_conc_dc = max(10, amount // 2)
                self.toastRequested.emit(f"Beast form took {amount} damage")
                self.statsChanged.emit()
                return
            excess = amount - cur
            self._revert_wildshape()
            self._show_damage(take_damage(char, excess),
                              f"Beast form dropped to 0 HP -- reverted to normal form, "
                              f"{excess} excess damage carried over")
            return
        self._show_damage(take_damage(char, amount))

    def _show_damage(self, res: dict, lead: str = ""):
        """Tell the player what take_damage() did: one toast (the death
        overlay says the rest), and a concentration save to roll."""
        self._pending_conc_dc = res["concentration_dc"]
        if res["died"]:
            self._maybe_critical_flavor_toast()
        else:
            notes = ([lead] if lead else []) + res["notes"]
            if res["concentration_dc"]:
                notes.append(f"Concentrating on {self.concentratingSpell} -- "
                             f"DC {res['concentration_dc']} CON save to keep it")
            if notes:
                self.toastRequested.emit("\n".join(notes))
        self.statsChanged.emit()

    @Slot(int)
    def applyHealing(self, amount: int):
        if amount <= 0:
            return
        char = self.char
        beast = self._active_wildshape_beast()
        if beast:
            cur = char.get("_wildshape_hp", beast["hp"])
            char["_wildshape_hp"] = min(beast["hp"], cur + amount)
            self.statsChanged.emit()
            return
        # The dead need Revive, not a potion. Otherwise core/dying.py's
        # heal(): up to max HP, and back up from 0 resets the death saves.
        why = heal_block_reason(char)
        if why:
            self.toastRequested.emit(why)
            return
        note = heal(char, amount)
        if note:
            self.toastRequested.emit(note)
        self.statsChanged.emit()

    @Slot(int)
    def setTempHp(self, amount: int):
        self.char["temp_hp"] = max(0, amount)
        self.statsChanged.emit()

    # ── Death saves ──────────────────────────────────────────────────
    # Mirrors ui_desktop's combat.py exactly, both on core/dying.py: 3
    # independent success/failure checkboxes, shown only at 0 HP. Three
    # successes: stable (still 0 HP and unconscious until healed); three
    # failures: dead.
    @Property(bool, notify=statsChanged)
    def showDeathSaves(self):
        return self.char.get("current_hp", 1) <= 0

    @Property(int, notify=statsChanged)
    def deathSaveSuccesses(self):
        return self.char.get("death_saves", {}).get("successes", 0)

    @Property(int, notify=statsChanged)
    def deathSaveFailures(self):
        return self.char.get("death_saves", {}).get("failures", 0)

    @Property(str, notify=statsChanged)
    def deathStatusText(self):
        return death_status_text(self.deathSaveSuccesses, self.deathSaveFailures)

    @Property(bool, notify=statsChanged)
    def isDead(self):
        return bool(self.char.get("is_dead", False))

    @Property(str, notify=statsChanged)
    def deathCauseText(self):
        """What killed them, for the YOU DIED overlay."""
        return death_cause(self.char) if self.char.get("is_dead") else ""

    def _maybe_critical_flavor_toast(self):
        if self.char.get("optional_rules", {}).get("critical_flavor", False):
            from dnd_app.data.flavor_text import random_death_message
            self.toastRequested.emit(random_death_message())

    def _set_death_saves(self, succ: int, fail: int):
        verdict = set_death_saves(self.char, succ, fail)
        if verdict == "dead":
            self._maybe_critical_flavor_toast()
        elif verdict == "stable":
            self.toastRequested.emit(STABLE_MESSAGE)
        self.statsChanged.emit()

    @Slot(int, bool)
    def setDeathSaveSuccess(self, index: int, checked: bool):
        succ = index + 1 if checked else index
        self._set_death_saves(succ, self.deathSaveFailures)

    @Slot(int, bool)
    def setDeathSaveFailure(self, index: int, checked: bool):
        fail = index + 1 if checked else index
        self._set_death_saves(self.deathSaveSuccesses, fail)

    @Slot()
    def revive(self):
        _revive_char(self.char)          # 1 HP, saves and exhaustion cleared
        self.statsChanged.emit()

    # ── Exhaustion ───────────────────────────────────────────────────
    @Property(int, notify=statsChanged)
    def exhaustionLevel(self):
        return self.char.get("exhaustion", 0)

    @Property(str, notify=statsChanged)
    def exhaustionEffectText(self):
        return _EXHAUSTION_EFFECTS.get(self.exhaustionLevel, "")

    @Slot(int)
    def setExhaustionLevel(self, level: int):
        level = max(0, min(6, level))
        self.char["exhaustion"] = level
        self.ctrl.refresh()  # recompute max HP / speed for the new level
        if level >= 6:
            self.char["is_dead"] = True
            self.toastRequested.emit("Exhaustion level 6 -- the character has died")
            self._maybe_critical_flavor_toast()
        elif level >= 4:
            self.toastRequested.emit(f"Exhaustion {level}: hit point maximum halved")
        self.statsChanged.emit()

    # ── Conditions ───────────────────────────────────────────────────
    @Property(list, notify=statsChanged)
    def allConditions(self):
        from dnd_app.core.calculator import implied_conditions
        active = set(self.char.get("conditions", []))
        implied = implied_conditions(self.char)
        return [
            {
                "name": name,
                "icon": data.get("icon", ""),
                "effectText": " ".join(data.get("effects", [])),
                "active": name in active,
                # on because another condition includes it (Stunned ->
                # Incapacitated); shown lit but not ticked
                "impliedBy": ", ".join(implied.get(name, [])),
            }
            for name, data in CONDITIONS.items()
        ]

    @Slot()
    def clearConditions(self):
        """Clear every condition (exhaustion is separate -- it's a level
        that only long rests remove)."""
        if not self.char.get("conditions"):
            return
        self.char["conditions"] = []
        self.ctrl.refresh()
        self.toastRequested.emit("Conditions cleared")
        self.statsChanged.emit()

    @Property(list, notify=statsChanged)
    def activeConditions(self):
        active = set(self.char.get("conditions", []))
        out = [
            {"name": name, "effectText": " ".join(CONDITIONS[name].get("effects", []))}
            for name in sorted(active) if name in CONDITIONS
        ]
        # conditions another one brings with it (Stunned -> Incapacitated,
        # Unconscious -> Prone), so a blocked turn has a visible reason
        from dnd_app.core.calculator import implied_conditions
        for name, causes in implied_conditions(self.char).items():
            out.append({"name": f"{name} (from {', '.join(causes)})",
                        "effectText": " ".join(CONDITIONS.get(name, {}).get("effects", []))})
        lvl = self.exhaustionLevel
        if lvl > 0:
            out.append({"name": f"Exhaustion ({lvl})", "effectText": _EXHAUSTION_EFFECTS.get(lvl, "")})
        return out

    @Slot(str, bool)
    def setConditionActive(self, name: str, active: bool):
        current = set(self.char.get("conditions", []))
        if active:
            current.add(name)
        else:
            current.discard(name)
        self.char["conditions"] = sorted(current)
        # Conditions like Prone/Restrained/Petrified/Grappled feed into
        # AC, speed, and advantage/disadvantage via calculator.py's
        # update_all() -- without this refresh() the toggle only updated
        # the raw list, so the checkbox and "Active" card would show the
        # condition but none of its mechanical effects would actually
        # apply to the sheet (matches setExhaustionLevel's same call
        # just above).
        self.ctrl.refresh()
        self.statsChanged.emit()

    # ── Actions economy + resources ──────────────────────────────────
    # build_action_abilities() is the same pure data/logic function
    # ui_desktop's action_tabs.py calls -- it has no Qt dependency, so
    # it's reused directly rather than re-implementing its class/
    # subclass/feat/item catalog on Android.
    #
    # char["resources"] (ki points, rage uses, second wind, etc.) is
    # fully computed generically by calculator.py's update_all() (via
    # aggregate_resources() in multiclass.py) -- nothing class-specific
    # needs to run here beyond the usual refresh(). What Use does is the
    # shared rules in core/action_use.py (useAbility below).
    _ACTION_BUCKET_LABELS = {
        "Action": "Action",
        "Bonus Action": "Bonus Action",
        "Reaction": "Reaction",
        "Passive": "Passive / Other",
    }

    @Property(list, notify=statsChanged)
    def actionAbilities(self):
        try:
            buckets = build_action_abilities(self.char)
        except Exception:
            # A Property getter that raises leaves QML with an empty
            # list and no visible error at all -- reported as "actions
            # tab goes blank" with nothing in the UI to explain why.
            # Logging here at least gets the real traceback into
            # logcat instead of losing it silently.
            import traceback
            print("actionAbilities: build_action_abilities() raised:", file=sys.stderr)
            traceback.print_exc()
            return []
        out = []
        for key, label in self._ACTION_BUCKET_LABELS.items():
            items = buckets.get(key, [])
            if not items:
                continue
            out.append({
                "bucket": label,
                # Indexed rather than unpacked: spell entries (racial
                # innate spells -- Firbolg, Aasimar, Tiefling, ...) come
                # back as 4-tuples with the spell dict appended, and a
                # strict 3-way unpack blanked the Actions and Abilities
                # tabs for any such character.
                "bucketKey": key,
                "items": [self._action_item(entry, key) for entry in items],
            })
        return out

    def _action_item(self, entry, bucket_key):
        """One Actions-screen card. Spell entries (cantrips, pinned or
        bonus-action/reaction spells, racial innate spells) carry the
        spell's real name for castSpell(); everything else gets a Use
        button that runs useAbility() -- desktop's action-tab Cast/Use."""
        spell = entry[3] if len(entry) > 3 else None
        # desktop marks pinned spells with a "★ " text prefix; here the
        # card shows the star icon from the "pinned" flag instead
        name = entry[0][2:] if spell is not None and entry[0].startswith("★ ") else entry[0]
        # an "Other" card gets Use too when using it does something
        # (Agile Parry, Deft Strike...: core/action_use.py)
        from dnd_app.core.action_use import rule_for
        item = {"name": name,
                "desc": entry[1] if len(entry) > 1 else "",
                "source": entry[2] if len(entry) > 2 else "",
                "bucketKey": bucket_key,
                "usable": bucket_key != "Passive" or rule_for(name) is not None,
                "isSpell": spell is not None}
        if spell is not None:
            item.update({
                "spellName": spell.get("name", entry[0]),
                "spellLevel": spell.get("level", 0),
                "concentration": bool(spell.get("concentration")),
                "pinned": spell.get("name") in self.char.get("quick_spells", []),
            })
        return item

    @Property(list, notify=statsChanged)
    def resources(self):
        out = []
        for res in self.char.get("resources", []):
            if res.get("track") not in ("uses", "pool", "current_max"):
                continue
            current_max = res.get("current_max", 0)
            unlimited = not isinstance(current_max, int)
            # A numeric current_max of 0 means this resource isn't
            # actually available yet at the character's current level
            # (e.g. Indomitable before level 9) -- desktop's action_tabs.py
            # filters these out of the UI entirely rather than showing a
            # permanent "0 / 0" row.
            if not unlimited and current_max <= 0:
                continue
            toggle_effect = _RESOURCE_TOGGLE_MAP.get(res.get("key"))
            out.append({
                "key": res.get("key", ""),
                "name": res.get("name", res.get("key", "")),
                "current": res.get("current", 0),
                "currentMax": current_max if not unlimited else 0,
                "unlimited": unlimited,
                "sourceClass": res.get("source_class", ""),
                "reset": res.get("reset", ""),
                "toggleEffect": toggle_effect or "",
                "toggleActive": bool(toggle_effect) and toggle_effect in self.char.get("active_effects", []),
            })
        # magic item charges (desktop lists them under Resources & Charges too)
        for name, data in self.char.get("item_charges", {}).items():
            if data.get("max", 0) <= 0:
                continue
            out.append({
                "key": f"item:{name}", "name": name,
                "current": data.get("current", 0), "currentMax": data.get("max", 0),
                "unlimited": False, "sourceClass": "Magic item",
                "reset": {"dawn": "Dawn", "dusk": "Dusk"}.get(data.get("recharge", "dawn"), "Never"),
                "toggleEffect": "", "toggleActive": False,
            })
        return out

    @Slot(str)
    def spendResource(self, key: str):
        if key.startswith("item:"):          # a magic item's charge
            data = self.char.get("item_charges", {}).get(key[5:])
            if data:
                data["current"] = max(0, data.get("current", 0) - 1)
            self.statsChanged.emit()
            return
        # Second Wind and Action Surge have a real mechanical effect
        # beyond "decrement a counter" -- matches ui_desktop's
        # action_tabs.py special-casing of these two exactly (every
        # other resource just uses the generic decrement below).
        if key == "second_wind":
            res = next((r for r in self.char.get("resources", []) if r.get("key") == "second_wind"), None)
            if res is None or res.get("current", 0) <= 0:
                self.toastRequested.emit("Second Wind: no uses left (recharges on short/long rest)")
                return
            fighter_lvl = class_levels(self.char).get("Fighter", 0)
            roll = random.randint(1, 10)
            heal = roll + fighter_lvl
            res["current"] = res.get("current", 1) - 1
            cur = self.char.get("current_hp", 0)
            mx = self.char.get("max_hp", 0)
            self.char["current_hp"] = min(mx, cur + heal)
            self.toastRequested.emit(
                f"Second Wind: rolled {roll} + {fighter_lvl} (Fighter level) = {heal} HP healed "
                f"({res['current']}/{res.get('current_max')} left)")
            self.statsChanged.emit()
            return
        for res in self.char.get("resources", []):
            if res.get("key") == key:
                if isinstance(res.get("current_max"), int):
                    res["current"] = max(0, res.get("current", 0) - 1)
                break
        if key == "action_surge":
            self.char["_action_surge_used_this_turn"] = True
            self.toastRequested.emit("Action Surge: gained an extra action this turn")
        self.statsChanged.emit()

    @Slot(str)
    def toggleResourceEffect(self, key: str):
        effect = _RESOURCE_TOGGLE_MAP.get(key)
        if not effect:
            return
        active = self.char.setdefault("active_effects", [])
        if effect in active:
            active.remove(effect)
        else:
            why = effect_start_problem(self.char, effect)   # Rage in heavy armor
            if why:
                self.toastRequested.emit(f"{effect}: {why}")
                self.statsChanged.emit()   # the toggle shows off again
                return
            active.append(effect)
            note = on_effect_started(self.char, effect)    # Rage ends concentration
            if note:
                self.toastRequested.emit(f"{effect}: {note}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str)
    def restoreResource(self, key: str):
        if key.startswith("item:"):          # a magic item's charges
            data = self.char.get("item_charges", {}).get(key[5:])
            if data:
                data["current"] = data.get("max", 0)
            self.statsChanged.emit()
            return
        for res in self.char.get("resources", []):
            if res.get("key") == key:
                if isinstance(res.get("current_max"), int):
                    res["current"] = res["current_max"]
                break
        self.statsChanged.emit()

    # ── Wild Shape ───────────────────────────────────────────────────
    # Same core/calculator.py gating as ui_desktop's combat.py
    # (get_wild_shape_info/get_available_wildshape_beasts, Druid level
    # 2+ only). The transformed-state HP swap (maxHp/currentHp/
    # applyDamage/applyHealing above) matches desktop's actual UX: the
    # SAME hp controls repurpose to the beast's pool rather than a
    # separate widget. STR/DEX/CON already fully replace with the
    # beast's own scores while transformed via core/character.py's
    # ability_score() -- and AC via calculator.py's get_ac() -- so
    # armorClass/abilities above already reflect the transformation
    # with no extra code needed here.
    def _active_wildshape_beast(self):
        active = self.char.get("_wildshape_active")
        return WILDSHAPE_BEASTS.get(active) if active else None

    def _revert_wildshape(self):
        char = self.char
        char["_wildshape_active"] = None
        char.pop("_wildshape_hp", None)
        effects = char.get("active_effects", [])
        if "Wild Shape" in effects:
            effects.remove("Wild Shape")

    @Property(bool, notify=statsChanged)
    def isDruid(self):
        return class_levels(self.char).get("Druid", 0) > 0

    @Property(bool, notify=statsChanged)
    def wildShapeAvailable(self):
        return get_wild_shape_info(self.char) is not None

    @Property(str, notify=statsChanged)
    def wildShapeRestrictionText(self):
        info = get_wild_shape_info(self.char)
        return info["restriction"] if info else ""

    @Property(bool, notify=statsChanged)
    def wildShapeActive(self):
        return self._active_wildshape_beast() is not None

    @Property(str, notify=statsChanged)
    def wildShapeActiveBeast(self):
        return self.char.get("_wildshape_active") or ""

    @Property(list, notify=statsChanged)
    def availableWildShapeBeasts(self):
        return [
            {"name": name, "crLabel": WILDSHAPE_BEASTS.get(name, {}).get("cr_label", "?")}
            for name in get_available_wildshape_beasts(self.char)
        ]

    @Property(int, notify=statsChanged)
    def wildShapeUsesLeft(self):
        res = next((r for r in self.char.get("resources", []) if r.get("key") == "wild_shape"), None)
        if res is None:
            return 0
        current = res.get("current", 0)
        return current if isinstance(current, int) else -1

    @Property(int, notify=statsChanged)
    def wildShapeUsesMax(self):
        res = next((r for r in self.char.get("resources", []) if r.get("key") == "wild_shape"), None)
        if res is None:
            return 0
        current_max = res.get("current_max", 0)
        return current_max if isinstance(current_max, int) else -1

    @Slot(str)
    def transformWildShape(self, beast_name: str):
        beast = WILDSHAPE_BEASTS.get(beast_name)
        if not beast:
            return
        res = next((r for r in self.char.get("resources", []) if r.get("key") == "wild_shape"), None)
        if res is not None and isinstance(res.get("current_max"), int):
            if res.get("current", 0) <= 0:
                self.toastRequested.emit(
                    "No Wild Shape uses remaining -- available again after a short or long rest.")
                return
            res["current"] -= 1
        char = self.char
        char["_wildshape_active"] = beast_name
        char["_wildshape_hp"] = beast["hp"]
        if "Wild Shape" not in char.get("active_effects", []):
            char.setdefault("active_effects", []).append("Wild Shape")
        self.ctrl.refresh()
        self.toastRequested.emit(f"Transformed into {beast_name}")
        self.statsChanged.emit()

    @Slot()
    def revertWildShape(self):
        self._revert_wildshape()
        self.ctrl.refresh()
        self.toastRequested.emit("Reverted to normal form")
        self.statsChanged.emit()

    # ── Features (read-only) ─────────────────────────────────────────
    # Full parity with ui_desktop's features.py _rebuild_features:
    # race/subrace traits, background feature, per-class level-by-level
    # features (using the same verified CLASS_FEATURE_INDEX/
    # SUBCLASS_FEATURES data desktop uses, falling back to CLASS_DICT's
    # raw per-level list), feats, fighting styles, invocations, metamagic,
    # battle master maneuvers, Blood Hunter curses/mutagens, Elemental
    # Disciplines, Replicated Magic Items, optional/alternate class
    # features (TCoE), Wild Magic surge tables (wildMagicTables/
    # rollWildMagicSurge below), and the DM-Reward/feat-grant browser
    # (see SheetFeaturesScreen.qml).
    _SUBCLASS_SLOT_KEYWORDS = (
        'subclass feature', 'archetype feature', 'domain feature',
        'circle feature', 'sacred oath feature', 'primal path feature',
        'order feature', 'college feature', 'ranger archetype feature',
        'ranger archetype', '(subclass)', 'martial archetype',
        'roguish archetype', 'sorcerous origin', 'otherworldly patron',
        'divine domain', 'druid circle', 'monastic tradition',
        'primal path', 'bardic college', 'arcane tradition',
        'sacred oath', 'ranger conclave', 'alchemical homunculus',
        'path feature', 'bard college feature', 'ki feature',
    )

    def _build_features_sections(self):
        char = self.char
        sections = []

        def add_section(title, items):
            if items:
                sections.append({"title": title, "items": list(items)})

        race = char.get("species") or char.get("race", "")
        if race:
            rdata = get_race(race)
            if rdata and rdata.get("traits"):
                add_section(f"Race: {race}", rdata["traits"])
            subrace = char.get("subrace", "")
            if subrace and rdata:
                for sub_str in rdata.get("subraces", []):
                    sub_name = sub_str.split("(")[0].strip()
                    if sub_name == subrace:
                        inner = sub_str[sub_str.find("(") + 1:sub_str.rfind(")")]
                        parts = [p.strip() for p in inner.split(";" if ";" in inner else ",") if p.strip()]
                        add_section(f"Subrace: {subrace}", parts)
                        break

        bg = get_background(char.get("background", ""))
        if bg and bg.get("feature"):
            add_section(f"Background: {char.get('background', '')}",
                        [f"{bg['feature']}: {bg.get('feature_desc', '')}"])

        for c in char.get("classes", []):
            cname = c["class"]
            clvl = c["level"]
            sub = c.get("subclass", "")
            title = cname + (f" -- {sub}" if sub else "") + f"  (Level {clvl})"
            feats = []
            cdata = CLASS_DICT.get(cname, {})
            features = cdata.get("features", {})

            proper_names = SUBCLASS_FEATURES.get((cname, sub), [])
            sub_feat_idx = 0
            sub_index = CLASS_FEATURE_INDEX.get(cname, {}).get(sub)
            if isinstance(sub_index, dict):
                for lvl in sorted(sub_index):
                    if lvl > clvl:
                        break
                    for real_name in sub_index[lvl]:
                        feats.append(f"[Lv {lvl}]  {sub}: {real_name}")
            else:
                for lvl in range(1, clvl + 1):
                    for fname in features.get(lvl, []):
                        is_sub_slot = any(kw in fname.lower() for kw in self._SUBCLASS_SLOT_KEYWORDS)
                        if is_sub_slot and sub and sub_feat_idx < len(proper_names):
                            feats.append(f"[Lv {lvl}]  {sub}: {proper_names[sub_feat_idx]}")
                            sub_feat_idx += 1
                        elif is_sub_slot and sub:
                            feats.append(f"[Lv {lvl}]  {sub} -- Subclass Feature")
                            sub_feat_idx += 1
                        else:
                            feats.append(f"[Lv {lvl}]  {fname}")

            if cname == "Warlock" and char.get("eldritch_invocations"):
                feats.append("[Invocations]  " + ", ".join(
                    i.split("–")[0].strip() for i in char["eldritch_invocations"]))
            if cname == "Sorcerer" and char.get("_choices", {}).get("sorcerer_metamagic"):
                feats.append("[Metamagic]  " + ", ".join(
                    m.split("–")[0].strip() for m in char["_choices"]["sorcerer_metamagic"]))
            if cname == "Artificer" and char.get("artificer_infusions"):
                feats.append("[Infusions]  " + ", ".join(
                    i.split("–")[0].strip() for i in char["artificer_infusions"]))
            if cname == "Fighter" and "battle master" in sub.lower() and char.get("battle_master_maneuvers"):
                feats.append("[Maneuvers]  " + ", ".join(
                    m.split("–")[0].strip() for m in char["battle_master_maneuvers"]))
            if cname == "Blood Hunter" and char.get("_choices", {}).get("blood_hunter_curses"):
                feats.append("[Blood Curses]  " + ", ".join(
                    c.split("–")[0].strip() for c in char["_choices"]["blood_hunter_curses"]))
            if cname == "Blood Hunter" and char.get("_choices", {}).get("blood_hunter_mutagens"):
                feats.append("[Mutagens]  " + ", ".join(
                    m.split("–")[0].strip() for m in char["_choices"]["blood_hunter_mutagens"]))
            if cname == "Monk" and char.get("_choices", {}).get("four_elements_disciplines"):
                feats.append("[Elemental Disciplines]  " + ", ".join(
                    d.split("–")[0].strip() for d in char["_choices"]["four_elements_disciplines"]))
            if cname == "Artificer" and clvl >= 2:
                # The real rule requires explicitly learning each item as
                # its own "Replicate Magic Item" infusion pick, consuming
                # an infusions-known slot -- not every item across every
                # tier the character's level qualifies for. Shows only
                # the specific items actually learned (matches desktop).
                all_replicable = {name for tier in ARTIFICER_REPLICABLE_ITEMS.values() for name, _ in tier}
                learned = [inf.split("–")[0].strip() for inf in char.get("artificer_infusions", [])
                           if inf.split("–")[0].strip() in all_replicable]
                if learned:
                    needs_attunement = {name: att for tier in ARTIFICER_REPLICABLE_ITEMS.values() for name, att in tier}
                    feats.append("[Replicated Magic Items]  " + ", ".join(
                        f"{name} (attunement)" if needs_attunement.get(name) else name for name in learned))

            add_section(title, feats)

        feat_items = []
        for fname in char.get("feats", []):
            fd = get_feat(fname)
            if fd:
                feat_items.append(f"{fname}: {fd.get('special', '')}")
        add_section("Feats", feat_items)

        add_section("Fighting Style", char.get("fighting_styles", []))

        # ── Optional / Alternate Class Features (TCoE) ──────────────────
        # A feature is "on" via either mechanism desktop supports: an
        # explicit per-feature toggle in _choices.optional_features, or
        # a same-named Settings optional-rule toggle (Martial
        # Versatility, Deft Explorer, etc.).
        enabled = char.get("_choices", {}).get("optional_features", {})
        rules = char.get("optional_rules", {})
        for c in char.get("classes", []):
            cname = c["class"]
            clvl = c["level"]
            items = []
            for unlock_lvl, flist in sorted(OPTIONAL_CLASS_FEATURES.get(cname, {}).items()):
                if unlock_lvl > clvl:
                    continue
                for f in flist:
                    rules_key = f["name"].lower().replace(" ", "_")
                    if enabled.get(f["name"], False) or rules.get(rules_key, False):
                        replaces = f.get("replaces")
                        tag = f"(replaces {replaces})" if replaces else "(TCoE optional)"
                        items.append(f"[Lv {unlock_lvl}]  {f['name']} {tag}")
            add_section(f"Optional -- {cname}", items)

        return sections

    @Property(list, notify=statsChanged)
    def featuresSections(self):
        return self._build_features_sections()

    # ── Wild Magic Surge (Barbarian d8 / Sorcerer d100) ──────────────
    # Pure "roll and show the effect" mechanic -- doesn't mutate the
    # character at all (matches desktop: the roll result is display-only,
    # the player applies whatever the table says by hand), so a single
    # Slot returning the result is enough; no character-state Property.
    def _wild_magic_flags(self):
        char = self.char
        wm_sorc = any(c.get("class") == "Sorcerer" and "wild magic" in c.get("subclass", "").lower()
                      for c in char.get("classes", []))
        wm_barb = any(c.get("class") == "Barbarian" and "wild magic" in c.get("subclass", "").lower()
                      for c in char.get("classes", []))
        for cn, v in char.get("_choices", {}).items():
            if "subclass" in cn.lower() and isinstance(v, list) and v:
                val = str(v[0]).lower()
                if "wild magic" in val:
                    if "sorcerer" in cn.lower():
                        wm_sorc = True
                    if "barbarian" in cn.lower():
                        wm_barb = True
        return wm_sorc, wm_barb

    def _wild_magic_rows(self, barb: bool):
        if barb:
            return [(i + 1, i + 1, eff) for i, (_, eff) in enumerate(WILD_MAGIC_BARBARIAN_TABLE)]
        return list(WILD_MAGIC_SURGE_TABLE)

    @Property(list, notify=statsChanged)
    def wildMagicTables(self):
        wm_sorc, wm_barb = self._wild_magic_flags()
        tables = []
        if wm_sorc:
            tables.append({
                "barb": False,
                "title": "Wild Magic Surge Table  (Sorcerer -- roll d100 after casting a spell)",
                "dieLabel": "Roll Wild Magic Surge (d100)",
                "dieMax": 100,
                "rows": [{"lo": lo, "hi": hi, "effect": eff} for lo, hi, eff in self._wild_magic_rows(False)],
            })
        if wm_barb:
            tables.append({
                "barb": True,
                "title": "Wild Magic Surge Table  (Barbarian -- roll d8 when you enter your rage)",
                "dieLabel": "Roll Wild Magic Surge (d8)",
                "dieMax": 8,
                "rows": [{"lo": lo, "hi": hi, "effect": eff} for lo, hi, eff in self._wild_magic_rows(True)],
            })
        return tables

    @Slot(bool, result='QVariant')
    def rollWildMagicSurge(self, barb: bool):
        rows = self._wild_magic_rows(barb)
        die_max = 8 if barb else 100
        r = random.randint(1, die_max)
        for i, (lo, hi, eff) in enumerate(rows):
            if lo <= r <= hi:
                return {"roll": r, "rowIndex": i, "effect": eff}
        return {"roll": r, "rowIndex": -1, "effect": ""}

    # ── Proficiencies (languages, tools, armor, weapons) ────────────
    # All four are set directly by builder.rebuild() from race/class/
    # background/feat grants -- nothing to compute here, just expose
    # them for display.
    @Property(list, notify=statsChanged)
    def languages(self):
        return list(self.char.get("languages", []))

    @Property(list, notify=statsChanged)
    def toolProficiencies(self):
        return list(self.char.get("tool_proficiencies", []))

    @Property(list, notify=statsChanged)
    def armorProficiencies(self):
        return list(self.char.get("armor_proficiencies", []))

    @Property(list, notify=statsChanged)
    def weaponProficiencies(self):
        return list(self.char.get("weapon_proficiencies", []))

    # ── DM-granted proficiencies (core/dm_proficiencies.py) ─────────
    # [{kind, heading, granted: [names]}] for the editor on the
    # Proficiencies screen; rebuild adds them to the lists above.
    @Property(list, notify=statsChanged)
    def dmProficiencies(self):
        from dnd_app.core import dm_proficiencies as dm
        return [{"kind": kind, "heading": heading, "granted": dm.granted(self.char, kind)}
                for kind, heading, _ in dm.KINDS]

    @Slot(str, result=list)
    def dmProficiencySuggestions(self, kind: str):
        from dnd_app.core import dm_proficiencies as dm
        return dm.suggestions(kind)

    @Slot(str, str, result=bool)
    def addDmProficiency(self, kind: str, name: str):
        from dnd_app.core import dm_proficiencies as dm
        added = dm.add(self.char, kind, name)
        if added:
            self.ctrl.refresh()
            self.statsChanged.emit()
        return added

    @Slot(str, str)
    def removeDmProficiency(self, kind: str, name: str):
        from dnd_app.core import dm_proficiencies as dm
        dm.remove(self.char, kind, name)
        self.ctrl.refresh()
        self.statsChanged.emit()

    # ── Spells ───────────────────────────────────────────────────────
    @Property(list, notify=statsChanged)
    def spellSlots(self):
        maxes = self.char.get("spell_slots_max", [0] * 9)
        used = self.char.get("spell_slots_used", [0] * 9)
        return [
            {"level": i + 1, "max": maxes[i], "used": used[i]}
            for i in range(9) if maxes[i] > 0
        ]

    @Property(dict, notify=statsChanged)
    def pactSlots(self):
        return {
            "max": self.char.get("pact_slots_max", 0),
            "used": self.char.get("pact_slots_used", 0),
            "level": self.char.get("pact_slot_level", 0),
        }

    @Slot(int, int)
    def setSlotsUsed(self, level: int, used: int):
        """Tapping a slot square: level 1-9 for ordinary slots, -1 for
        Pact Magic. Clamped to 0..max."""
        if level == -1:
            self.char["pact_slots_used"] = max(0, min(used, self.char.get("pact_slots_max", 0)))
        elif 1 <= level <= 9:
            maxes = self.char.get("spell_slots_max", [0] * 9)
            slots_used = self.char.setdefault("spell_slots_used", [0] * 9)
            slots_used[level - 1] = max(0, min(used, maxes[level - 1]))
        else:
            return
        self.statsChanged.emit()

    @Property(list, notify=statsChanged)
    def knownSpells(self):
        prepared = set(self.char.get("spells_prepared", []))
        quick = set(self.char.get("quick_spells", []))
        granted = set(self.char.get("bonus_spells", []))
        out = []
        # cantrips first, then by spell level, then by name
        names = sorted(self.char.get("spells_known", []),
                       key=lambda n: ((get_spell(n) or {}).get("level", 0), n.casefold()))
        for name in names:
            sp = get_spell(name) or {}
            out.append({
                "name": name,
                "displayName": compute_display_spell_title(self.char, sp) if sp else name,
                "level": sp.get("level", 0),
                "levelText": "Cantrip" if sp.get("level", 0) == 0 else f"Level {sp.get('level')}",
                "school": sp.get("school", ""),
                # granted by a subclass/race/feat: always prepared, can't
                # be removed (the hold menu leaves those options out)
                "granted": name in granted,
                "prepared": name in prepared or name in granted,
                "concentration": bool(sp.get("concentration")),
                "ritual": bool(sp.get("ritual")),
                "pinned": name in quick,
                # False for a spell none of this character's classes
                # prepares (Warlock/Sorcerer/Bard/Ranger) -- no Prepared box
                "preparable": bool(spell_preparing_classes(self.char, sp)),
                # Cast offers "as a ritual" only when this character can
                "canRitual": bool(sp) and can_ritual_cast(self.char, sp),
                # a prepared caster's leveled spell must be prepared first
                "needsPreparing": bool(sp) and spell_needs_preparing(self.char, sp),
            })
        return out

    @Property(list, notify=statsChanged)
    def spellLimits(self):
        """How many spells/cantrips each casting class can know or prepare,
        and how many it has -- the same numbers as desktop's Spells Known /
        Prepared card (SpellsMixin._spell_limits). One map per class:
        label, kind ("known"/"prepared"), current, max, ability,
        cantrips, cantripMax."""
        try:
            rows = spell_limits(self.char)
        except Exception:
            return []
        return [{"label": r["label"], "kind": r["kind"], "current": r["current"], "max": r["max"],
                 "ability": r["ability"], "cantrips": r["cantrips"], "cantripMax": r["cantrip_max"]}
                for r in rows]

    @Property(list, notify=statsChanged)
    def unavailableFavourites(self):
        """Starred spells the Combat screen can't offer a Cast button for,
        with why -- otherwise a starred spell just silently doesn't show
        up there. Same rules as build_action_abilities(): a prepared
        caster's leveled spell must be prepared, and only action / bonus
        action / reaction spells count as combat casts."""
        prepared = set(self.char.get("spells_prepared", []))
        out = []
        for name in sorted(self.char.get("quick_spells", []),
                           key=lambda n: ((get_spell(n) or {}).get("level", 0), n.casefold())):
            sp = get_spell(name)
            if not sp:
                continue
            lvl = sp.get("level", 0)
            cast_time = str(sp.get("cast_time") or "1 action")
            if lvl > 0 and spell_preparing_classes(self.char, sp) and name not in prepared:
                reason = "Not prepared -- prepare it on the Spells screen to cast it here"
            elif not ("bonus" in cast_time.lower() or "reaction" in cast_time.lower()
                      or cast_time == "1 action"):
                reason = f"Casting time {cast_time} -- cast it from the Spells screen"
            else:
                continue
            out.append({"name": name, "level": lvl,
                        "levelText": "Cantrip" if lvl == 0 else f"L{lvl}", "reason": reason})
        return out

    @Property(bool, notify=statsChanged)
    def spellHomebrewMode(self):
        return self._spell_homebrew

    @Slot(bool)
    def setSpellHomebrewMode(self, enabled: bool):
        self._spell_homebrew = enabled
        self.statsChanged.emit()

    # Matches desktop's spells.py browser's class-filter QComboBox exactly.
    @Property(list, constant=True)
    def spellClassFilters(self):
        return ["All Classes", "Wizard", "Cleric", "Druid", "Bard",
                "Sorcerer", "Warlock", "Paladin", "Ranger", "Artificer"]

    @Slot(str, int, str, result=list)
    def searchAddableSpells(self, query: str, level_filter: int = -1, class_filter: str = "All Classes"):
        """Spells from every one of the character's classes' spell
        lists (merged, deduplicated by name, EK/AT correctly mapped to
        Wizard's list) not already known, plus any Mark-expanded spells
        -- matches desktop's browser with Homebrew mode off. With
        Homebrew mode on, every spell in the game is shown and the
        castable-level cap below doesn't apply, matching desktop's
        browser with its Homebrew checkbox on. Ritual/concentration
        markers shown here match desktop's browser (which shows them on
        unknown spells too, not just known ones). level_filter: -1 for
        all levels, 0 for cantrips, 1-9 for that spell level. class_filter
        is an ADDITIONAL filter on top of the class-list/castable-level
        gating below (matches desktop's _filter_spell_browser, where the
        class combo is ANDed with the "mine" restriction, not a
        replacement for it) -- mainly useful with Homebrew mode on, or to
        narrow a multiclass character's browser to one class's list.
        Known/prepared count caps are enforced at add-time
        (addKnownSpell), not here -- matches desktop's own split between
        the browser's castable-level filter and the "+ Add" button's cap
        gate.
        """
        homebrew = self._spell_homebrew
        if homebrew:
            pool = dict(SPELL_DICT)
        else:
            my_classes = char_spell_classes(self.char)
            mark_spells = get_mark_expanded_spells(self.char)
            pool = {}
            for cn in my_classes:
                for sp in spells_for_class(cn):
                    pool[sp.get("name", "")] = sp
            for name in mark_spells:
                sp = get_spell(name)
                if sp:
                    pool[name] = sp
            if not pool:
                pool = dict(SPELL_DICT)
            max_castable = max_castable_spell_level(self.char)
        known = set(self.char.get("spells_known", []))
        q = (query or "").strip().lower()
        class_filter = class_filter or "All Classes"
        out = []
        for name, sp in pool.items():
            if name in known:
                continue
            if q and q not in name.lower():
                continue
            if class_filter != "All Classes" and class_filter not in sp.get("classes", []):
                continue
            lvl = sp.get("level", 0)
            if level_filter >= 0 and lvl != level_filter:
                continue
            if not homebrew and lvl > 0 and lvl > max_castable:
                continue
            out.append({
                "name": name,
                "level": lvl,
                "levelText": "Cantrip" if lvl == 0 else f"Level {lvl}",
                "school": sp.get("school", ""),
                "ritual": bool(sp.get("ritual")),
                "concentration": bool(sp.get("concentration")),
            })
        out.sort(key=lambda s: (s["level"], s["name"].casefold()))   # level, then name
        return out

    # ── Immersive Health / Immersive Exhaustion (core/immersive.py) ──
    @Slot(result="QVariant")
    def immersiveState(self):
        """What App.qml shows for the open character: how much colour to
        take out (fade), the exhaustion frame's level, how far the page
        moves in for it (inset), both settings, and whether the one-time
        note has been shown."""
        from dnd_app.core import immersive as imm
        e_setting = imm.mode("exhaustion")
        level = imm.frame_level(self.char, e_setting)
        return {"fade": imm.health_fade(self.char), "level": level,
                "inset": imm.frame_px(level, phone=True), "exhaustion": e_setting,
                "health": imm.mode("health"), "promptSeen": imm.prompt_seen()}

    @Slot()
    def markImmersivePromptSeen(self):
        from dnd_app.core.immersive import mark_prompt_seen
        mark_prompt_seen()

    @Slot(str, result=dict)
    def getSpellDetail(self, name: str):
        sp = get_spell(name)
        if not sp:
            return {}
        lvl = sp.get("level", 0)
        return {
            "name": sp.get("name", name),
            "levelText": "Cantrip" if lvl == 0 else f"Level {lvl}",
            "school": sp.get("school", ""),
            "castTime": sp.get("cast_time", ""),
            "range": sp.get("range", ""),
            "duration": sp.get("duration", ""),
            "components": sp.get("components", ""),
            "ritual": bool(sp.get("ritual")),
            "concentration": bool(sp.get("concentration")),
            "desc": sp.get("desc", ""),
            "source": sp.get("source", ""),
        }

    @Slot(str, result="QVariant")
    def getItemDetail(self, name: str):
        """Details for any item -- magic item, weapon, armor, gear or tool
        -- for the browsers' View button / press-and-hold. Returns
        {name, subtitle, facts: [str], desc} (+ rarity for magic items)."""
        from dnd_app.data.magic_items import get_magic_item
        from dnd_app.data.items import (WEAPON_DICT as _W, ARMOR_DICT as _A,
                                                   ADVENTURING_GEAR as _G, ALL_TOOLS as _T)
        gp = lambda c: (f"{c:g} gp" if c >= 1 else f"{round(c * 100):g} cp" if c else "")
        scroll = parse_spell_scroll(name)
        if scroll and scroll[1] and get_spell(scroll[1]):
            # a bound scroll: its spell, the scroll's own DC/attack, and
            # whether this character can read it
            from dnd_app.core.spellcasting import scroll_reading, scroll_base_name
            sp = get_spell(scroll[1])
            info = scroll_reading(self.char, scroll[1])
            lvl_txt = "Cantrip" if sp["level"] == 0 else f"Level {sp['level']}"
            facts = [f"{lvl_txt} {sp.get('school', '')}".strip(),
                     f"Casting time: {sp.get('cast_time', '1 action')}", f"Range: {sp.get('range', '')}",
                     f"Duration: {sp.get('duration', '')}" + ("  (concentration)" if sp.get("concentration") else ""),
                     f"Scroll save DC {info['save_dc']}, spell attack +{info['attack']}",
                     ("You can't read this scroll -- the spell isn't on your class's list." if not info["readable"]
                      else f"Above your casting level: {info['check']['ability']} check, DC {info['check']['dc']}, to cast it."
                      if info["check"] else "You can cast this from the scroll.")]
            base = get_magic_item(scroll_base_name(scroll[0])) or {}
            return {"name": name, "subtitle": f"Spell scroll: {scroll[1]}", "facts": facts,
                    "desc": sp.get("desc", ""), "rarity": base.get("rarity", "")}
        mi = get_magic_item(name)
        if mi:
            # rarity goes in the dialog's subtitle (in its colour), not here
            facts = [f for f in (mi.get("type", ""),
                                 "Requires attunement" if str(mi.get("attunement")) == "True" else "",
                                 f"Source: {mi.get('source')}" if mi.get("source") else "") if f]
            return {"name": name, "subtitle": "Magic item", "facts": facts, "desc": mi.get("desc", ""),
                    "rarity": mi.get("rarity", "")}
        unprefixed, material = parse_material_prefix(name)
        base, _ = parse_magic_suffix(unprefixed)
        w = _W.get(base)
        if w:
            facts = [w.get("category", ""), f"{w.get('damage', '')} {w.get('dmg_type', '')}".strip()]
            if w.get("properties"):
                facts.append(", ".join(w["properties"]))
            facts += [f"{w.get('weight', 0):g} lb" if w.get("weight") else "", gp(w.get("cost", 0))]
            desc = {
                "Silvered": "Silvered: gets past a creature's resistance or immunity to nonmagical "
                            "attacks that aren't silvered, such as a lycanthrope's.",
                "Adamantine": "Adamantine: any hit against an object is a critical hit.",
            }.get(material, "")
            return {"name": name, "subtitle": f"{material} weapon".strip().capitalize(),
                    "facts": [f for f in facts if f], "desc": desc}
        a = _A.get(name)
        if a:
            kind = (a.get("type") or "").title()
            ac = f"+{a.get('ac')} AC" if a.get("type") == "shield" else f"AC {a.get('ac')}" + (
                "" if a.get("dex_cap") == 0 else " + DEX" + (f" (max {a['dex_cap']})" if a.get("dex_cap") else ""))
            facts = [f"{kind} armor" if kind and kind != "Shield" else kind, ac,
                     f"Needs STR {a['str_req']}" if a.get("str_req") else "",
                     "Disadvantage on Stealth" if a.get("stealth") else "",
                     f"{a.get('weight', 0):g} lb" if a.get("weight") else "", gp(a.get("cost", 0))]
            return {"name": name, "subtitle": "Armor", "facts": [f for f in facts if f], "desc": ""}
        # Background kits word some gear the other way round
        # ("common clothes" for "Clothes, Common").
        words = name.lower().split()
        flipped = f"{words[-1]}, {' '.join(words[:-1])}" if len(words) > 1 else ""
        for row in _G:
            if row[0].lower() in (name.lower(), flipped):
                facts = [f"{row[1]:g} lb" if row[1] else "", gp(row[2]) if len(row) > 2 else ""]
                return {"name": row[0], "subtitle": "Adventuring gear", "facts": [f for f in facts if f],
                        "desc": row[3] if len(row) > 3 else ""}
        tool = next((t for t in _T if t.lower() == name.lower()), None)
        if tool:
            return {"name": tool, "subtitle": "Tool", "facts": [],
                    "desc": "Lets you add your proficiency bonus to ability checks made with it, if you're proficient."}
        return {"name": name, "subtitle": "Item", "facts": [],
                "desc": "No rules entry for this item -- it's a flavour or custom item."}

    @Slot(str)
    def addKnownSpell(self, name: str):
        # Matches desktop's _add_spell_from_browser gates exactly (class-
        # list/Mark membership, castable spell level, per-class known-
        # spell/cantrip cap), each bypassable via Homebrew mode -- see
        # searchAddableSpells' docstring for why the pool itself doesn't
        # also enforce these (the "+ Add" gate is the actual authority,
        # the browser's own filtering is just a head start).
        char = self.char
        known = char.setdefault("spells_known", [])
        if name in known:
            return
        sp = get_spell(name)
        if sp is None:
            known.append(name)
            self.statsChanged.emit()
            return
        my_classes = char_spell_classes(char)
        if not self._spell_homebrew:
            mark_spells = get_mark_expanded_spells(char)
            if my_classes and name not in mark_spells and not (set(sp.get("classes", [])) & my_classes):
                self.toastRequested.emit(f"{name} isn't on your class spell lists "
                                          f"-- enable Homebrew mode to learn it")
                return
            sp_level = sp.get("level", 0)
            if sp_level > 0:
                max_lvl = max_castable_spell_level(char)
                if sp_level > max_lvl:
                    self.toastRequested.emit(
                        f"{name} is a level {sp_level} spell -- you can only "
                        f"cast up to level {max_lvl} right now -- enable Homebrew mode to exceed it")
                    return

            def _real_name(cn):
                return "Wizard" if cn in ("Fighter (EK)", "Rogue (AT)") else cn

            all_classes = all_caster_classes(char)
            is_cantrip = sp_level == 0
            sp_classes = set(sp.get("classes", []))
            pool = all_classes if is_cantrip else known_spell_classes(char)
            eligible = [cn for cn in pool if _real_name(cn) in sp_classes]
            if eligible:
                attributed = attribute_known_spells(char)

                def _room(cn):
                    cant_max, lvl_max = all_classes[cn]
                    bucket = attributed.get(cn, {"cantrips": [], "leveled": []})
                    used = len(bucket["cantrips"]) if is_cantrip else len(bucket["leveled"])
                    cap = cant_max if is_cantrip else lvl_max
                    return (cap if cap is not None else 999) - used

                best_cn = max(eligible, key=_room)
                if _room(best_cn) <= 0:
                    cap_shown = all_classes[best_cn][0 if is_cantrip else 1]
                    used_shown = cap_shown - _room(best_cn) if cap_shown is not None else "?"
                    kind = "Cantrip" if is_cantrip else "Spells-known"
                    self.toastRequested.emit(
                        f"{kind} limit reached for {_real_name(best_cn)} "
                        f"({used_shown}/{cap_shown}) -- enable Homebrew mode to exceed it")
                    return
        known.append(name)
        # Full-list prepared casters (Cleric/Druid/Paladin/Artificer) have
        # no separate "learn a spell" step in the real rules -- their
        # whole class list is always available, preparing is the only
        # choice. Auto-prepare here so adding one of their spells doesn't
        # also require a separate "mark prepared" tap. Wizard is excluded
        # (also prepared, but genuinely spellbook-limited, so "add" still
        # means something distinct from "prepare" for it).
        if sp.get("level", 0) > 0:
            _, _, _, PREPARE_AB = spell_progression_tables()
            full_list_classes = {c for c in PREPARE_AB if c != "Wizard"}
            if full_list_classes & set(sp.get("classes", [])) & my_classes:
                prepped = char.setdefault("spells_prepared", [])
                if name not in prepped:
                    prepped.append(name)
        self.statsChanged.emit()

    @Slot(str)
    def removeKnownSpell(self, name: str):
        char = self.char
        if name in char.get("bonus_spells", []):
            # a domain/oath/racial/feat spell is part of the character, not a pick
            self.toastRequested.emit(f"{name} comes from your class, race or a feat -- it can't be removed")
            return
        if name in char.get("spells_known", []):
            char["spells_known"].remove(name)
        if name in char.get("spells_prepared", []):
            char["spells_prepared"].remove(name)
        if name in char.get("quick_spells", []):
            char["quick_spells"].remove(name)   # no starring a spell you no longer have
        self.statsChanged.emit()

    @Slot(str, bool)
    def setSpellPrepared(self, name: str, prepared: bool):
        # Matches desktop's _on_prep_toggled: each prepared-caster class
        # gets its own separate prepared-spell cap (ability mod + level,
        # or +half-level for Paladin/Artificer) -- never pooled, and
        # bypassable via Homebrew mode. Cantrips and bonus/domain/circle
        # spells are always prepared, no cap check.
        char = self.char
        prepped = char.setdefault("spells_prepared", [])
        if not prepared:
            if name in prepped:
                prepped.remove(name)
            self.statsChanged.emit()
            return
        if name in prepped:
            return
        sp = get_spell(name)
        if sp and sp.get("level", 0) > 0 and name not in char.get("bonus_spells", []) \
                and not self._spell_homebrew:
            caps = prepared_caster_caps(char)
            sp_classes = set(sp.get("classes", []))
            eligible = [cn for cn in caps if cn in sp_classes]
            if eligible:
                attributed = attribute_prepared_spells(char)
                target = max(eligible, key=lambda cn: caps[cn] - len(attributed.get(cn, [])))
                current = len(attributed.get(target, []))
                cap = caps[target]
                if current >= cap:
                    self.toastRequested.emit(
                        f"{target}'s prepared spell limit reached ({current}/{cap}) "
                        f"-- unprepare another {target} spell first")
                    return
        prepped.append(name)
        self.statsChanged.emit()

    # ── Turn tracker (Action/Bonus Action/Reaction economy) ─────────────
    # Session-only state, never saved -- same as ui_desktop's
    # CombatMixin._turn_counts. Backs the bonus-action-spell rule check
    # in castSpell() below; a full per-turn UI (grey-out ability
    # buttons, Sneak Attack toggle, freeform active-effect add/remove)
    # is a further increment.
    def _turn_limit(self, bucket: str) -> int:
        from dnd_app.core.calculator import get_turn_blocks
        if bucket in get_turn_blocks(self.char):
            return 0          # Incapacitated / Surprised: this part of the turn is gone
        if bucket == "Action" and has_extra_action(self.char):
            return 2
        return 1

    def _turn_blocked(self, bucket: str) -> bool:
        """True (with a toast saying why) if a condition takes this part
        of the turn away -- checked before a Use/Cast spends anything."""
        from dnd_app.core.calculator import get_turn_blocks
        why = get_turn_blocks(self.char).get(bucket)
        if why:
            self.toastRequested.emit(f"Can't use your {bucket.lower()}: {why}")
        return bool(why)

    def _mark_turn_used(self, bucket: str):
        if bucket not in self._turn_counts:
            return
        limit = self._turn_limit(bucket)
        if self._turn_counts[bucket] >= limit:
            return
        self._turn_counts[bucket] += 1
        if bucket == "Action" and limit == 2 and self._turn_counts[bucket] == 1:
            self.toastRequested.emit("Haste: first action used -- one more available")

    def _check_bonus_action_spell_rule(self, is_cantrip: bool, bucket: str) -> bool:
        if has_extra_action(self.char):
            return True
        if bucket == "Bonus Action":
            if self._action_spell_is_cantrip is False:
                return False
        elif bucket == "Action" and not is_cantrip:
            if self._bonus_action_spell_is_cantrip is not None:
                return False
        return True

    @Property(dict, notify=statsChanged)
    def turnCounts(self):
        return {
            "action": self._turn_counts["Action"],
            "actionLimit": self._turn_limit("Action"),
            "bonusAction": self._turn_counts["Bonus Action"],
            "bonusActionLimit": self._turn_limit("Bonus Action"),
            "reaction": self._turn_counts["Reaction"],
            "reactionLimit": self._turn_limit("Reaction"),
            "blocked": self._turn_blocks_for_qml(),
        }

    def _turn_blocks_for_qml(self):
        from dnd_app.core.calculator import get_turn_blocks
        keys = {"Action": "action", "Bonus Action": "bonusAction", "Reaction": "reaction"}
        return {keys[b]: why for b, why in get_turn_blocks(self.char).items()}

    @Slot(str)
    def toggleTurnSlot(self, bucket: str):
        """Tap a turn chip to mark it spent / available again -- same as
        clicking ui_desktop's turn chips (_toggle_turn_slot)."""
        if bucket not in self._turn_counts:
            return
        if self._turn_blocked(bucket):
            return
        limit = self._turn_limit(bucket)
        self._turn_counts[bucket] = 0 if self._turn_counts[bucket] >= limit else limit
        self.statsChanged.emit()

    # ── Use button (Actions screen) ──────────────────────────────────
    # The shared rules decide what Use does (core/action_use.py: what it
    # costs, what it does), the same as desktop. A question they raise
    # (how many ki, which slot, a Wild Shape check...) goes to QML as
    # actionQuestion; the answer comes back through answerActionQuestion
    # and the action is tried again with it.
    @Slot(str, str, str)
    def useAbility(self, bucket: str, display: str, desc: str):
        if bucket in self._turn_counts and self._turn_blocked(bucket):
            return
        from dnd_app.core.action_use import use_action
        self._ask_through(display, lambda a: use_action(self.char, bucket, display, desc, a),
                          self._after_use)

    # The shared rules can ask the player something first (core/action_use.py,
    # core/spell_effects.py): the question goes to App.qml through
    # actionQuestion, the answer comes back through answerActionQuestion, and
    # the rule runs again with it -- until it's done, then `done` gets the result.
    def _ask_through(self, title, call, done):
        self._pending_use = {"title": title, "call": call, "done": done, "answers": {}}
        self._run_pending_use()

    def _after_use(self, res):
        if res.get("toast"):
            self.toastRequested.emit(res["toast"])
        if not res.get("ok"):
            return
        if res.get("slot"):
            self._mark_turn_used(res["slot"])
        if res.get("refresh"):
            self.ctrl.refresh()
        self.statsChanged.emit()

    # A character just opened from a save with effects a short rest would
    # end still on (Rage, Bladesong, a potion...): App.qml asks whether
    # they've ended (core/action_use.py leftover_effects)
    @Slot(result=list)
    def takeLeftoverEffects(self):
        from dnd_app.core.action_use import take_leftover_effects
        return take_leftover_effects(self.char)

    @Slot(list)
    def endEffects(self, names):
        from dnd_app.core.action_use import end_effects
        if end_effects(self.char, [str(n) for n in names]):
            self.ctrl.refresh()
            self.statsChanged.emit()

    @Slot(str)
    def answerActionQuestion(self, choice: str):
        """The player's answer to actionQuestion ("" = cancelled)."""
        pending = getattr(self, "_pending_use", None)
        if not pending or not choice:
            self._pending_use = None
            return
        pending["answers"][pending.pop("key")] = choice
        self._run_pending_use()

    def _run_pending_use(self):
        p = self._pending_use
        res = p["call"](p["answers"])
        ask = res.get("ask")
        if ask:
            p["key"] = ask["key"]
            self.actionQuestion.emit(p["title"], ask["title"], list(ask["options"]))
            return
        self._pending_use = None
        p["done"](res)

    @Slot(str)
    def toggleQuickSpell(self, name: str):
        """Pin/unpin a spell as a quick spell (desktop's ★): pinned leveled
        action spells join the Actions and Combat screens' castable
        spells, alongside cantrips and bonus-action/reaction spells."""
        quick = self.char.setdefault("quick_spells", [])
        if name in quick:
            quick.remove(name)
        else:
            quick.append(name)
        self.statsChanged.emit()

    @Slot()
    def newTurn(self):
        for k in self._turn_counts:
            self._turn_counts[k] = 0
        self._action_spell_is_cantrip = None
        self._bonus_action_spell_is_cantrip = None
        self.char["_action_surge_used_this_turn"] = False
        # what lasted until now ends: Reckless Attack, Dodge, Agile Parry,
        # Kensei's Shot... and once-per-turn uses come back (core/action_use.py)
        from dnd_app.core.action_use import new_turn
        if new_turn(self.char):
            self.ctrl.refresh()
        # Surprise lasts until the end of your first turn -- a new turn
        # means it's over.
        from dnd_app.core.calculator import get_turn_blocks
        if "Surprised" in self.char.get("conditions", []):
            self.char["conditions"] = [c for c in self.char["conditions"] if c != "Surprised"]
            self.ctrl.refresh()
            self.toastRequested.emit("New turn -- no longer surprised; action, bonus & reaction ready")
        elif get_turn_blocks(self.char):
            self.toastRequested.emit("New turn -- still incapacitated, no actions or reactions")
        else:
            self.toastRequested.emit("New turn -- action, bonus & reaction ready")
        self.statsChanged.emit()

    def _has_beast_spells(self) -> bool:
        return any(c.get("class") == "Druid" and c.get("level", 0) >= 18
                   for c in self.char.get("classes", []))

    def _mark_spell_cast_time(self, spell: dict):
        ct = (spell.get("cast_time") or "1 action").strip().lower()
        is_cantrip = spell.get("level", 1) == 0
        from dnd_app.core.action_use import note_spell_cast
        note_spell_cast(self.char, spell.get("name", ""))   # no second spell from the attack dialog
        if ct == "1 action":
            self._mark_turn_used("Action")
            self._action_spell_is_cantrip = is_cantrip
        elif ct == "bonus action":
            self._mark_turn_used("Bonus Action")
            self._bonus_action_spell_is_cantrip = is_cantrip
        elif ct == "reaction":
            self._mark_turn_used("Reaction")

    def _maybe_apply_spell_active_effect(self, spell: dict, level: int = 0, said: str = ""):
        """Casting puts the spell's effect on your Active Effects (Haste,
        Bless, Divine Favor, a smite...) -- the shared rules (core/
        spell_effects.py, as desktop's _apply_spell_active_effect) ask what
        only the player knows: who it's on, which weapon, which damage type.
        `said` is the cast's own toast, shown with what the effect did."""
        from dnd_app.core.spell_effects import cast_effect, effect_names
        name = spell["name"]
        if not effect_names(name):
            if said:
                self.toastRequested.emit(said)
            return

        def done(res):
            if res.get("refresh"):
                self.ctrl.refresh()
            msg = "\n".join(m for m in (said, res.get("toast", "")) if m)
            if msg:
                self.toastRequested.emit(msg)
            self.statsChanged.emit()
        self._ask_through(name, lambda a: cast_effect(self.char, name, level, a), done)

    def _weapon_cantrip(self, spell: dict):
        """Green-Flame Blade and Booming Blade: which melee weapon you
        swing (from the weapon rows), then what to roll -- the weapon's
        damage plus the spell's, each with its type -- in a dialog
        (sheetMessage). The turn is spent once a weapon is picked."""
        from dnd_app.core.spell_effects import weapon_cantrip
        name = spell["name"]
        rows = [{"name": w["name"], "atk": w["attackBonusText"], "damage": w["damageDisplay"],
                 "type": w["damageType"], "melee": "melee" in w["category"].lower(),
                 "riders": w["onHitBonusText"]} for w in self.weapons]

        def done(res):
            if not res.get("ok"):
                if res.get("toast"):
                    self.toastRequested.emit(res["toast"])
                return
            self._mark_spell_cast_time(spell)
            self.sheetMessage.emit(name, res["message"])
            self.statsChanged.emit()
        self._ask_through(name, lambda a: weapon_cantrip(self.char, name, rows, a), done)

    @Slot(str)
    def castSpell(self, name: str):
        """Mirrors ui_desktop's spells.py _cast_spell(): expends the
        real slot/pact slot, enforces the bonus-action-spell rule, blocks
        on missing components, auto-starts concentration, applies the
        active_effects auto-apply hook (see
        _maybe_apply_spell_active_effect), and feeds the turn tracker."""
        spell = get_spell(name)
        if spell is None:
            return
        _ct = (spell.get("cast_time") or "1 action").strip().lower()
        _bucket = {"1 action": "Action", "bonus action": "Bonus Action", "reaction": "Reaction"}.get(_ct)
        if _bucket and self._turn_blocked(_bucket):
            return
        if self.char.get("_wildshape_active") and not self._has_beast_spells():
            self.toastRequested.emit(f"Can't cast {name} while Wild Shaped -- revert to your normal form first")
            return
        block_reason = spell_component_block_reason(self.char, spell)
        if block_reason:
            self.toastRequested.emit(f"Can't cast {name} -- {block_reason}")
            return
        why = spellcasting_block_reason(self.char)   # raging, incapacitated...
        if why:
            self.toastRequested.emit(f"Can't cast {name} -- {why}")
            return
        if spell_needs_preparing(self.char, spell):
            self.toastRequested.emit(f"{name} isn't prepared -- prepare it first to cast it")
            return
        lvl = spell.get("level", 0)
        is_cantrip = (lvl == 0)
        ct = (spell.get("cast_time") or "1 action").strip().lower()
        bucket = {"1 action": "Action", "bonus action": "Bonus Action",
                  "reaction": "Reaction"}.get(ct)
        if bucket in ("Action", "Bonus Action") and not self._check_bonus_action_spell_rule(is_cantrip, bucket):
            self.toastRequested.emit(
                f"Can't cast {name} via {bucket} -- casting a spell with a bonus action "
                f"means the only other spell you can cast this turn is a cantrip")
            return
        if is_cantrip:
            from dnd_app.core.spell_effects import WEAPON_CANTRIPS
            if name in WEAPON_CANTRIPS:
                self._weapon_cantrip(spell)
                return
            self._mark_spell_cast_time(spell)
            self._maybe_apply_spell_active_effect(spell, 0, f"Cast {name} (cantrip -- at will)")
            self.statsChanged.emit()
            return
        # A free daily cast (a racial spell, Fey Touched, Firbolg Magic...)
        # is used before any slot -- see core/spellcasting.py.
        from dnd_app.core.spellcasting import spend_free_cast, free_cast_message
        free = spend_free_cast(self.char, name)
        if free:
            if spell.get("concentration"):
                start_concentration(self.char, name)
            self._mark_spell_cast_time(spell)
            self._maybe_apply_spell_active_effect(spell, lvl, free_cast_message(name, free))
            self.statsChanged.emit()
            return
        slots_used = self.char.setdefault("spell_slots_used", [0] * 9)
        slots_max = self.char.get("spell_slots_max", [0] * 9)
        for i in range(lvl - 1, 9):
            if slots_max[i] > 0 and slots_used[i] < slots_max[i]:
                slots_used[i] += 1
                if spell.get("concentration"):
                    start_concentration(self.char, name)
                self._mark_spell_cast_time(spell)
                self._maybe_apply_spell_active_effect(spell, i + 1, f"Cast {name} -- slot expended")
                self.statsChanged.emit()
                return
        if self.char.get("pact_slots_max", 0) > 0 and self.char.get("pact_slots_used", 0) < self.char["pact_slots_max"]:
            self.char["pact_slots_used"] = self.char.get("pact_slots_used", 0) + 1
            if spell.get("concentration"):
                start_concentration(self.char, name)
            self._mark_spell_cast_time(spell)
            self._maybe_apply_spell_active_effect(spell, self.char.get("pact_slot_level", 0) or lvl,
                                                  f"Cast {name} -- pact slot expended")
            self.statsChanged.emit()
            return
        self.toastRequested.emit(f"Can't cast {name} -- no level-{lvl}+ spell slots available")

    @Slot(str)
    def castSpellAsRitual(self, name: str):
        spell = get_spell(name)
        if spell is None:
            return
        if self.char.get("_wildshape_active") and not self._has_beast_spells():
            self.toastRequested.emit(f"Can't cast {name} while Wild Shaped -- revert to your normal form first")
            return
        block_reason = spell_component_block_reason(self.char, spell)
        if block_reason:
            self.toastRequested.emit(f"Can't cast {name} -- {block_reason}")
            return
        why = spellcasting_block_reason(self.char)   # raging, incapacitated...
        if why:
            self.toastRequested.emit(f"Can't cast {name} -- {why}")
            return
        if not can_ritual_cast(self.char, spell):
            self.toastRequested.emit(f"Can't cast {name} as a ritual -- Cleric, Druid and "
                                     f"Artificer rituals must be prepared first")
            return
        base_time = spell.get("cast_time", "1 action")
        # a ritual casting still needs concentration (Detect Magic, ...)
        if spell.get("concentration"):
            start_concentration(self.char, name)
        self._maybe_apply_spell_active_effect(
            spell, spell.get("level", 0),
            f"Cast {name} as a ritual -- no spell slot used, but casting time is {base_time} + 10 minutes.")
        self.statsChanged.emit()

    # ── Concentration ────────────────────────────────────────────────
    # Same core/magic_items.py helpers as ui_desktop's spells.py (full
    # tracker) and combat.py (small read-only indicator, shown wherever
    # damage tracking happens since a concentration save prompt follows
    # taking damage during combat).
    @Property(str, notify=statsChanged)
    def concentratingSpell(self):
        return self.char.get("concentration", {}).get("spell") or ""

    @Property(bool, notify=statsChanged)
    def isConcentrating(self):
        return bool(self.concentratingSpell)

    @Slot(str)
    def startConcentration(self, spell_name: str):
        start_concentration(self.char, spell_name)
        self._pending_conc_dc = 0
        self.statsChanged.emit()

    @Slot()
    def dropConcentration(self):
        drop_concentration(self.char)
        self._pending_conc_dc = 0
        self.statsChanged.emit()

    @Property(int, notify=statsChanged)
    def concentrationSaveDc(self):
        """DC of the concentration save the last hit asks for (0 = none)."""
        return self._pending_conc_dc if self.isConcentrating else 0

    @Slot()
    def rollPendingConcentrationSave(self):
        """Roll the save the last hit asked for (d20 + CON save bonus)."""
        dc = self.concentrationSaveDc
        if not dc:
            return
        self._pending_conc_dc = 0
        # concentration_save() takes the damage; DC = max(10, damage // 2)
        self.rollConcentrationSave(dc * 2)

    @Slot(int)
    def rollConcentrationSave(self, damage: int):
        maintained, total = concentration_save(self.char, damage)
        dc = max(10, damage // 2)
        if maintained:
            self.toastRequested.emit(f"Concentration maintained ({total} vs DC {dc})")
        else:
            self.toastRequested.emit(f"Concentration failed ({total} vs DC {dc}) -- spell dropped")
        self.statsChanged.emit()

    # ── Identity (race/subrace/ancestry/background, editable post-
    # creation) -- mirrors ui_desktop's Choices tab _edit_identity(). ──
    @Property(str, notify=statsChanged)
    def identityRace(self):
        return self.char.get("race", "")

    @Property(str, notify=statsChanged)
    def identitySubrace(self):
        return self.char.get("subrace", "")

    @Property(str, notify=statsChanged)
    def identityAncestry(self):
        return self.char.get("draconic_ancestry", "")

    @Property(str, notify=statsChanged)
    def identityBackground(self):
        return self.char.get("background", "")

    @Property(bool, notify=statsChanged)
    def isDragonborn(self):
        return self.char.get("race", "") == "Dragonborn"

    @Property(bool, notify=statsChanged)
    def hasSubraces(self):
        race = self.char.get("race", "")
        return bool(RACE_DICT.get(race, {}).get("subraces"))

    @Property(list, constant=True)
    def raceNames(self):
        return list(RACE_NAMES)

    @Property(list, constant=True)
    def backgroundNames(self):
        return list(BACKGROUND_NAMES)

    @Property(list, notify=statsChanged)
    def subraceOptions(self):
        race = self.char.get("race", "")
        subraces_raw = RACE_DICT.get(race, {}).get("subraces", [])
        out = []
        for sub_str in subraces_raw:
            name_part = sub_str.split("(")[0].strip()
            out.append(name_part)
        return out

    @Property(list, notify=statsChanged)
    def ancestryOptions(self):
        subrace = self.char.get("subrace", "Standard") or "Standard"
        avail = ANCESTRY_BY_SUBRACE.get(subrace, ANCESTRY_BY_SUBRACE.get("Standard", []))
        return [f"{a} ({DRACONIC_ANCESTRY[a][0]}, {DRACONIC_ANCESTRY[a][1]})" for a in avail]

    @Slot(str)
    def changeRace(self, name: str):
        old_race = self.char.get("race", "")
        # whatever the old race asked for and the new one doesn't goes
        # (a High Elf's cantrip) -- shared with desktop's identity edit
        change_and_prune(
            self.char, lambda: self.char.update(race=name, species=name, subrace="", draconic_ancestry=""),
            RACE_SCOPED_CHOICE_IDS if name != old_race else ())
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str)
    def changeSubrace(self, subrace_name: str):
        change_and_prune(self.char, lambda: self.char.update(subrace=subrace_name))
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str)
    def changeAncestry(self, choice_text: str):
        # choice_text is "Name (damage, breath weapon)" as built by
        # ancestryOptions -- only the name is stored on the character.
        self.char["draconic_ancestry"] = choice_text.split(" (")[0].strip()
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str)
    def changeBackground(self, name: str):
        old_bg = self.char.get("background", "")
        change_and_prune(self.char, lambda: self.char.update(background=name),
                               BACKGROUND_SCOPED_CHOICE_IDS if name != old_bg else ())
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, result=list)
    def backgroundFeatChoices(self, name: str):
        bg = get_background(name)
        return list((bg or {}).get("feat_choices") or [])

    @Slot(str)
    def applyBackgroundFeatChoice(self, feat_name: str):
        feats = self.char.setdefault("feats", [])
        if feat_name not in feats:
            feats.append(feat_name)
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    # ── Class Manager: level down / remove class -- the inverse of
    # levelUpClass() above, mirroring ui_desktop's _open_level_down/
    # _open_remove_class exactly (same choice-pruning safeguard). ──────
    @Slot(str)
    def levelDownClass(self, class_name: str):
        entry = get_class_entry(self.char, class_name)
        if entry is None or entry["level"] <= 1:
            return
        old_ids = _all_relevant_choice_ids(self.char)
        entry["level"] -= 1
        # below its subclass level, a class can't keep a subclass
        from dnd_app.core.character import drop_subclasses_below_level
        dropped = drop_subclasses_below_level(self.char)
        new_ids = _all_relevant_choice_ids(self.char)
        _prune_stale_choices(self.char, old_ids - new_ids)
        self.ctrl.refresh()
        msg = f"{class_name} is now level {entry['level']}"
        for _cn, sub, need in dropped:
            msg += f" -- {sub} set aside until level {need}"
        self.toastRequested.emit(msg)
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    @Property(bool, notify=statsChanged)
    def atMaxLevel(self):
        """Character level 20: Level Up / Multiclass In are greyed out."""
        from dnd_app.core.character import total_level
        return total_level(self.char) >= 20

    @Property(bool, notify=statsChanged)
    def canRemoveClass(self):
        return len(self.char.get("classes", [])) > 1

    @Slot(str)
    def removeClass(self, class_name: str):
        classes = self.char.get("classes", [])
        if len(classes) <= 1:
            return
        old_ids = _all_relevant_choice_ids(self.char)
        removed = next((c for c in classes if c["class"] == class_name), None)
        self.char["classes"] = [c for c in classes if c["class"] != class_name]
        # Its spells go with it -- only the ones no remaining class could
        # have (core/character.py). Before the prune, which would hide its
        # Magical Secrets picks.
        from dnd_app.core.character import drop_spells_of_removed_class, name_list
        lost = drop_spells_of_removed_class(self.char, removed) if removed else []
        self.char.get("_choices", {}).pop(f"{class_name}_subclass", None)   # re-adding asks again
        new_ids = _all_relevant_choice_ids(self.char)
        _prune_stale_choices(self.char, old_ids - new_ids)
        self.ctrl.refresh()
        self.toastRequested.emit(f"{class_name} removed" + (
            f", along with its spells: {name_list(lost)}" if lost else ""))
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    # ── Experience / leveling mode ──────────────────────────────────────
    @Property(bool, notify=statsChanged)
    def xpLevelingMode(self):
        return self.char.get("leveling_mode", "milestone") == "xp"

    @Slot(bool)
    def setXpLevelingMode(self, enabled: bool):
        self.char["leveling_mode"] = "xp" if enabled else "milestone"
        self.statsChanged.emit()

    @Property(dict, notify=statsChanged)
    def xpProgress(self):
        prog = xp_progress(self.char)
        return {
            "xp": prog["xp"], "floor": prog["floor"], "next": prog["next"],
            "pct": prog["pct"], "eligible": prog["eligible"],
            "levelsDue": prog["levels_due"],
        }

    @Slot(int)
    def addXp(self, amount: int):
        if amount <= 0:
            return
        self.char["experience"] = self.char.get("experience", 0) + amount
        prog = xp_progress(self.char)
        if prog["eligible"]:
            due = prog["levels_due"]
            suffix = "ready to level up!" if due <= 1 else f"ready to level up ×{due}!"
            self.toastRequested.emit(f"+{amount:,} XP -- {suffix}")
        else:
            self.toastRequested.emit(f"+{amount:,} XP")
        self.statsChanged.emit()

    @Slot(int)
    def setTotalXp(self, value: int):
        self.char["experience"] = max(0, value)
        self.statsChanged.emit()

    # ── DM Rewards / Feat grant browser -- grants a feat or DM Reward
    # ("Character Secret" etc.) outside normal class progression, same
    # as ui_desktop's Features tab "Bonus Feature Browser". ─────────────
    @Property(list, constant=True)
    def dmRewardCategories(self):
        return list(DM_REWARD_CATEGORIES)

    @Slot(str, str, result=list)
    def searchDmRewardBrowser(self, query: str, category: str):
        q = (query or "").strip().lower()
        cat = category or "All Types"
        granted_feats = set(self.char.get("dm_feats", []))
        granted_rewards = set(self.char.get("dm_rewards", []))
        out = []
        for f in ALL_FEATS:
            if cat not in ("All Types", "Feat"):
                continue
            if q and q not in f["name"].lower():
                continue
            out.append({
                "name": f["name"], "itemType": "feat", "category": "Feat",
                "source": f.get("source", ""), "prereq": f.get("prereq", ""),
                "desc": f.get("special", ""), "granted": f["name"] in granted_feats,
            })
        for rw in ALL_DM_REWARDS:
            rcat = rw.get("category", "")
            if cat not in ("All Types", rcat):
                continue
            if q and q not in rw["name"].lower():
                continue
            out.append({
                "name": rw["name"], "itemType": "dm_reward", "category": rcat,
                "source": rw.get("source", ""), "prereq": rw.get("prereq", ""),
                "desc": rw.get("desc", ""), "granted": rw["name"] in granted_rewards,
            })
        return out

    @Slot(str, str)
    def grantDmBrowserItem(self, name: str, item_type: str):
        field = "dm_rewards" if item_type == "dm_reward" else "dm_feats"
        granted = self.char.setdefault(field, [])
        if name not in granted:
            granted.append(name)
            self.ctrl.refresh()
            self.toastRequested.emit(f"Granted: {name}")
            self.statsChanged.emit()

    @Slot(str, str)
    def revokeDmBrowserItem(self, name: str, item_type: str):
        field = "dm_rewards" if item_type == "dm_reward" else "dm_feats"
        granted = self.char.get(field, [])
        if name in granted:
            granted.remove(name)
            self.ctrl.refresh()
            self.statsChanged.emit()

    # ── Appearance (theme + font scale) and DM Secrets (Immersive
    # Spells) -- ui_desktop's Settings dialog Appearance/DM Secrets
    # cards. Theme/font-scale names are reused directly from
    # ui_desktop's own THEMES/FONT_SCALES dicts rather than a second
    # hardcoded list; Theme.qml keeps its own copy of the actual color
    # values since QML needs those synchronously at bind time, not
    # fetched from Python. ─────────────────────────────────────────────
    @Property(list, constant=True)
    def themeNames(self):
        return list(THEMES.keys())

    @Property(list, constant=True)
    def fontScaleNames(self):
        return list(FONT_SCALES.keys())

    @Property(str, notify=statsChanged)
    def theme(self):
        return self.char.get("theme") or get_app_theme()

    @Slot(str)
    def setTheme(self, name: str):
        self.char["theme"] = name
        self.statsChanged.emit()

    @Slot(str)
    def stampThemeIfMissing(self, current_theme: str):
        # Called once, the first time a character is shown (a freshly
        # finished wizard, or a save from before "theme" existed) -- so
        # it keeps whatever theme was active at that moment as its own
        # from here on, independent of the app-level default (Start
        # Menu / mid-wizard) changing later. See app_settings.py's
        # module docstring and App.qml's finishCharacterCreation/
        # loadCharacterIntoSheet.
        if not self.char.get("theme"):
            self.char["theme"] = current_theme

    @Property(str, notify=statsChanged)
    def fontScale(self):
        return self.char.get("ui_font_scale", "Medium (default)")

    @Slot(str)
    def setFontScale(self, name: str):
        self.char["ui_font_scale"] = name
        self.statsChanged.emit()

    @Property(bool, notify=statsChanged)
    def immersiveSpells(self):
        return bool(self.char.get("optional_rules", {}).get("immersive_spells", False))

    @Slot(bool)
    def setImmersiveSpells(self, enabled: bool):
        self.char.setdefault("optional_rules", {})["immersive_spells"] = enabled
        self.statsChanged.emit()

    # ── Optional rules (Settings) ────────────────────────────────────
    # The other 12 desktop Settings-dialog toggles (ui_desktop's
    # main_window.py _build_settings_page), matching its exact keys/
    # defaults so a save file round-trips identically between
    # platforms. All 12 are now fully wired: max_hp_per_level and
    # component_restrictions (read directly from shared core --
    # calculator.py/spell_components.py); dmg_xge_optional_actions
    # (actionAbilities calls ui_desktop's own build_action_abilities()
    # directly, which already checks it); harness_divine_power and
    # martial_versatility (gate the Optional Class Features section,
    # see _build_features_sections above); feat_prereqs and
    # multiclass_ability_reqs (searchFeatsForLevelUp/
    # levelUpClassOptions below); critical_flavor
    # (_maybe_critical_flavor_toast, called from every death-trigger
    # call site); eldritch/martial/bardic/sorcerous_versatility
    # (versatilityOptions + the applyXVersatility Slots below --
    # cantrip_versatility needs no dedicated code since a cantrip swap
    # under any of these rules is already just removeKnownSpell +
    # addKnownSpell via the spell browser, see versatilityOptions'
    # docstring).
    _OPTIONAL_RULE_DEFAULTS = {
        "feat_prereqs": True, "multiclass_ability_reqs": True,
        "dmg_xge_optional_actions": True,
        "eldritch_versatility": False, "harness_divine_power": False,
        "martial_versatility": False,
        "cantrip_versatility": False, "bardic_versatility": False,
        "sorcerous_versatility": False, "max_hp_per_level": False,
        "critical_flavor": False, "component_restrictions": False,
    }

    @Property('QVariantMap', notify=statsChanged)
    def optionalRules(self):
        return {**self._OPTIONAL_RULE_DEFAULTS, **self.char.get("optional_rules", {})}

    @Slot(str, bool)
    def setOptionalRule(self, key: str, value: bool):
        self.char.setdefault("optional_rules", {})[key] = value
        self.ctrl.refresh()
        self.statsChanged.emit()

    # ── Choices (read-only view of levelup/feat/background sub-picks) ──
    @Property(list, notify=statsChanged)
    def choicesList(self):
        choices = self.char.get("_choices") or {}
        out = []
        for key, value in sorted(choices.items()):
            if isinstance(value, (list, tuple)):
                text = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                text = ", ".join(f"{k}: {v}" for k, v in value.items())
            else:
                text = str(value)
            out.append({"key": key.replace("_", " ").title(), "value": text})
        return out

    # ── Notes ────────────────────────────────────────────────────────
    # Legacy flat field -- kept for save-file back-compat (a pre-tabs
    # character, or one only ever touched by the Wizard's own starting-
    # notes field, has just this one string). _notes_pages_for_char()
    # below promotes it to a single "General" page the first time the
    # multi-page model is read, matching desktop's own fallback exactly.
    @Property(str, notify=statsChanged)
    def notes(self):
        return self.char.get("notes", "")

    @Slot(str)
    def setNotes(self, text: str):
        self.char["notes"] = text
        self.statsChanged.emit()

    # ── Traits / Backstory / Appearance / Campaign Notes ────────────────
    # Ports ui_desktop's TraitsNotesMixin: 4 short trait fields (flat
    # strings), Appearance (flat string), Backstory (flat string,
    # always present, not part of the removable page list), and
    # Campaign Notes as up to 8 player-named, add/remove/renameable
    # pages (char["notes_pages"], a list of {"title","text"} dicts).
    _NOTES_TRAIT_FIELD_MAP = {
        "personalityTraits": "personality_traits", "ideals": "ideals",
        "bonds": "bonds", "flaws": "flaws",
        "appearanceNotes": "appearance_notes", "backstory": "backstory",
    }
    _MAX_NOTES_PAGES = 8  # excludes the always-present Backstory field

    @Property('QVariantMap', notify=statsChanged)
    def traitsNotes(self):
        char = self.char
        return {qml_key: char.get(real_key, "")
                for qml_key, real_key in self._NOTES_TRAIT_FIELD_MAP.items()}

    @Slot(str, str)
    def setTraitField(self, key: str, text: str):
        real_key = self._NOTES_TRAIT_FIELD_MAP.get(key)
        if real_key is None:
            return
        self.char[real_key] = text
        self.statsChanged.emit()

    def _notes_pages_for_char(self):
        pages = self.char.get("notes_pages")
        if pages:
            return pages
        legacy = self.char.get("notes", "")
        if legacy:
            # Pre-tabs characters (and the Wizard's starting-notes
            # field) only ever wrote a single flat string -- preserved
            # as one page rather than dropped.
            return [{"title": "General", "text": legacy}]
        return [{"title": t, "text": ""} for t in
                ("Session Log", "Quest Log", "Loot & Treasure")]

    @Property(list, notify=statsChanged)
    def notesPages(self):
        return self._notes_pages_for_char()

    @Slot(int, str)
    def setNotesPageText(self, index: int, text: str):
        pages = self._notes_pages_for_char()
        if 0 <= index < len(pages):
            pages[index]["text"] = text
            self.char["notes_pages"] = pages
            self.statsChanged.emit()

    @Slot(str)
    def addNotesPage(self, title: str):
        pages = self._notes_pages_for_char()
        if len(pages) >= self._MAX_NOTES_PAGES:
            self.toastRequested.emit(f"Notes pages are capped at {self._MAX_NOTES_PAGES}")
            return
        title = (title or "").strip() or "Notes"
        pages.append({"title": title, "text": ""})
        self.char["notes_pages"] = pages
        self.statsChanged.emit()

    @Slot(int)
    def removeNotesPage(self, index: int):
        pages = self._notes_pages_for_char()
        if len(pages) <= 1:
            self.toastRequested.emit("Keep at least one notes page")
            return
        if 0 <= index < len(pages):
            pages.pop(index)
            self.char["notes_pages"] = pages
            self.statsChanged.emit()

    @Slot(int, str)
    def renameNotesPage(self, index: int, title: str):
        pages = self._notes_pages_for_char()
        title = (title or "").strip()
        if not title or not (0 <= index < len(pages)):
            return
        pages[index]["title"] = title
        self.char["notes_pages"] = pages
        self.statsChanged.emit()

    # ── Infusions (Artificer only; not grantable until level 2, so an
    # empty list at level 1 is correct, not a gap) ──────────────────
    @Property(bool, notify=statsChanged)
    def isArtificer(self):
        cl = class_levels(self.char)
        return cl.get("Artificer", 0) > 0

    @Property(int, notify=statsChanged)
    def artificerLevel(self):
        return class_levels(self.char).get("Artificer", 0)

    @Property(int, notify=statsChanged)
    def maxActiveInfusions(self):
        return get_max_active_infusions(self.char)

    @Property(int, notify=statsChanged)
    def activeInfusionsCount(self):
        return len(self.char.get("active_infusions", []))

    @Property(list, notify=statsChanged)
    def infusions(self):
        active = self.char.get("active_infusions", [])
        active_by_name = {a["infusion"]: a for a in active}
        at_cap = len(active) >= get_max_active_infusions(self.char)
        out = []
        for inf in self.char.get("artificer_infusions", []):
            base_name = inf.split(" – ")[0].strip()
            info = active_by_name.get(base_name)
            if info:
                status = ("Given to another character" if info.get("given_away")
                          else f"Active on {info.get('target_item', '?')}")
            else:
                status = "Known"
            out.append({
                "name": base_name, "active": info is not None,
                "statusText": status, "canActivate": info is None and not at_cap,
            })
        return out

    @Slot(str, result=list)
    def infusionCandidateItems(self, infusion_name: str):
        """Owned mundane (non-magic) items this infusion's target type
        (weapon/armor/shield/armor_or_shield) can apply to -- verbatim
        port of desktop's _get_applicable_infusions, minus the
        already-known-but-not-yet-activated filtering (that's done by
        infusions() above; this only needs to filter equipment)."""
        target = ARTIFICER_INFUSION_TARGETS.get(infusion_name)
        if target not in ("weapon", "armor", "shield", "armor_or_shield"):
            return []
        out = []
        for eq in self.char.get("equipment", []):
            if eq.get("magic"):
                continue
            name = eq.get("name", "")
            is_weapon = name in WEAPON_DICT
            is_armor = name in ARMOR_DICT and ARMOR_DICT[name].get("type") != "shield" and name != "No Armor"
            is_shield = name in ARMOR_DICT and ARMOR_DICT[name].get("type") == "shield"
            if (target == "weapon" and is_weapon) or (target == "shield" and is_shield) or \
               (target == "armor" and is_armor) or (target == "armor_or_shield" and (is_armor or is_shield)):
                out.append(name)
        return out

    @Slot(str, result=bool)
    def infusionIsStandalone(self, infusion_name: str):
        return ARTIFICER_INFUSION_TARGETS.get(infusion_name) == "standalone"

    @Slot(str)
    def notify(self, message: str):
        """Generic toast trigger for a QML-side guard clause (e.g. "you
        don't own a matching item yet") that decides whether to open a
        dialog at all -- that decision has to live in QML since only it
        knows whether a dialog is about to open, but every toast in this
        app still flows through the same toastRequested signal."""
        self.toastRequested.emit(message)

    def _infuse_item(self, item_name: str, infusion_name: str, give_away: bool = False):
        active = self.char.setdefault("active_infusions", [])
        if len(active) >= get_max_active_infusions(self.char):
            self.toastRequested.emit(f"You can only have {get_max_active_infusions(self.char)} infusions active at once.")
            return
        active.append({"infusion": infusion_name, "target_item": item_name if not give_away else None,
                        "given_away": give_away})
        if not give_away:
            found = False
            for eq in self.char.get("equipment", []):
                if eq.get("name") == item_name:
                    eq["magic"] = True
                    eq["infused_with"] = infusion_name
                    found = True
                    break
            if not found and infusion_name != "Homunculus Servant":
                items = self.char.setdefault("magic_items", [])
                if not any((i.get("name") if isinstance(i, dict) else i) == item_name for i in items):
                    items.append({"name": item_name, "attunement": False,
                                  "equipped": True, "notes": f"Artificer infusion: {infusion_name}"})
            self.toastRequested.emit(f"{item_name} infused with {infusion_name}")
        else:
            self.toastRequested.emit(f"{infusion_name} activated and given to another character")
        self.statsChanged.emit()

    @Slot(str, str)
    def activateInfusionOnItem(self, infusion_name: str, item_name: str):
        self._infuse_item(item_name, infusion_name)

    @Slot(str, bool)
    def activateStandaloneInfusion(self, infusion_name: str, give_away: bool):
        self._infuse_item(infusion_name, infusion_name, give_away=give_away)

    @Slot(str)
    def setResistantArmorDamageType(self, damage_type: str):
        self.char.setdefault("_choices", {})["resistant_armor_type"] = damage_type
        self.statsChanged.emit()

    @Slot(str)
    def deactivateInfusion(self, infusion_name: str):
        active = self.char.get("active_infusions", [])
        entry = next((a for a in active if a["infusion"] == infusion_name), None)
        if not entry:
            return
        target = entry.get("target_item")
        if target:
            for eq in self.char.get("equipment", []):
                if eq.get("name") == target and eq.get("infused_with") == infusion_name:
                    eq["magic"] = False
                    eq.pop("infused_with", None)
                    break
        self.char["active_infusions"] = [a for a in active if a["infusion"] != infusion_name]
        self.toastRequested.emit(f"Deactivated {infusion_name}")
        self.statsChanged.emit()

    # ── Rest (reachable from the drawer on any screen, not just the
    # sheet). Full port of ui_desktop's base.py _preview_short_rest/
    # _preview_long_rest/_short_rest/_long_rest/_apply_rest_options --
    # NOT just the bare core.character.long_rest/short_rest calls this
    # used to make, which silently skipped Font of Inspiration recovery,
    # the Relentless Rage DC reset, expired-effect/active-toggle
    # clearing, and (long rest) exhaustion reduction and dropping
    # concentration. rest_options() and rest_preview_lines() (core/
    # character.py) are the ones desktop's rest dialogs use (both plain
    # staticmethods, no QWidget involved) so the option list and the
    # preview wording can't drift from desktop's.
    #
    # QML-driven flow (App.qml owns the dialog sequence, reachable from
    # any screen via the drawer): show restPreviewLines()+restOptions()
    # -> (short rest only) if hitDiceAvailableForRest>0 and HP<max,
    # prompt a hit-dice-to-spend count -> applyShortRest(n)/
    # applyLongRest() runs the core mechanics -> then, one at a time,
    # each checked option kind resolves via applyRestOptionSimple/
    # applyRestOptionWithValue/applyAstralKnowledgeSwap/
    # applyArcaneRecovery, mirroring desktop's _apply_rest_options.
    def _preview_short_rest(self) -> dict:
        char = self.char
        hd_model = char.get("hit_dice", {})
        hit_dice_available = sum(d.get("remaining", 0) for d in hd_model.values())
        cur, mx = char.get("current_hp", 0), char.get("max_hp", 0)
        resets = []
        for r in char.get("resources", []):
            if r.get("reset") in ("SR", "sr", "SR/LR"):
                target = r.get("current_max") or r.get("max", 0)
                if r.get("current", 0) != target:
                    resets.append((r.get("name", "?"), r.get("current", 0), target))
        if class_levels(char).get("Bard", 0) >= 5:
            for r in char.get("resources", []):
                if "bardic inspiration" in str(r.get("name", "")).lower():
                    target = r.get("current_max") or r.get("max", 0)
                    if r.get("current", 0) != target:
                        resets.append((r.get("name", "?"), r.get("current", 0), target))
        pact_restore = char.get("pact_slots_used", 0) > 0
        fading = [n for n in char.get("active_effects", [])
                  if EFFECT_TABLE.get(n, {}).get("duration_category") == "short" or n in RESOURCE_POOL_TOGGLES]
        return {"hp": cur, "max_hp": mx, "hit_dice_available": hit_dice_available,
                "resets": resets, "pact_restore": pact_restore, "fading": fading}

    def _preview_long_rest(self) -> dict:
        char = self.char
        cur, mx = char.get("current_hp", 0), char.get("max_hp", 0)
        temp_hp = char.get("temp_hp", 0)
        import copy
        hd_before = char.get("hit_dice", {})
        scratch = {"hit_dice": copy.deepcopy(hd_before), "classes": char.get("classes", [])}
        hit_dice_restored = restore_hit_dice_pool(scratch)
        resets = []
        for r in char.get("resources", []):
            if r.get("reset") in ("LR", "lr", "SR", "sr", "SR/LR"):
                target = r.get("current_max") or r.get("max", 0)
                if r.get("current", 0) != target:
                    resets.append((r.get("name", "?"), r.get("current", 0), target))
        slots_used = char.get("spell_slots_used", [0] * 9)
        slot_levels_reset = [i + 1 for i, v in enumerate(slots_used) if v > 0]
        pact_restore = char.get("pact_slots_used", 0) > 0
        death_saves = char.get("death_saves", {})
        death_reset = death_saves.get("successes", 0) > 0 or death_saves.get("failures", 0) > 0
        exhaustion = char.get("exhaustion", 0)
        was_concentrating = char.get("concentration", {}).get("spell")
        fading = [n for n in char.get("active_effects", [])
                  if EFFECT_TABLE.get(n, {}).get("duration_category") in ("short", "long") or n in RESOURCE_POOL_TOGGLES]
        return {"hp": cur, "max_hp": mx, "temp_hp": temp_hp, "hit_dice_restored": hit_dice_restored,
                "resets": resets, "slot_levels_reset": slot_levels_reset, "pact_restore": pact_restore,
                "death_reset": death_reset, "exhaustion": exhaustion, "exhaustion_after": max(0, exhaustion - 1),
                "was_concentrating": was_concentrating, "fading": fading}

    @Slot(str, result=list)
    def restPreviewLines(self, rest_type: str):
        preview = self._preview_short_rest() if rest_type == "short" else self._preview_long_rest()
        return rest_preview_lines(rest_type, preview)

    @Slot(str, result=str)
    def restBlockReason(self, rest_type: str):
        """Why this rest can't be taken right now ("" if it can) -- shown
        as a toast, and RestFlowDialog doesn't open. A long rest needs at
        least 1 HP when it starts (core/character.py)."""
        if rest_type != "long":
            return ""
        from dnd_app.core.character import long_rest_block_reason
        why = long_rest_block_reason(self.char)
        if why:
            self.toastRequested.emit(f"Can't take a long rest -- {why}")
        return why

    @Slot(str, result=list)
    def restOptions(self, rest_type: str):
        return list(rest_options(self.char, rest_type))

    @Property(int, notify=statsChanged)
    def hitDiceAvailableForRest(self):
        return sum(d.get("remaining", 0) for d in self.char.get("hit_dice", {}).values())

    def _clear_active_toggles(self) -> list:
        fx = self.char.get("active_effects", [])
        cleared = [name for name in fx if name in RESOURCE_POOL_TOGGLES]
        for name in cleared:
            fx.remove(name)
        return cleared

    def _clear_expired_active_effects(self, categories: tuple) -> list:
        fx = self.char.get("active_effects", [])
        removed = [n for n in fx if EFFECT_TABLE.get(n, {}).get("duration_category") in categories]
        for n in removed:
            fx.remove(n)
        return removed

    @Slot(int)
    def applyShortRest(self, hit_dice_to_spend: int):
        if not self.hasCharacter:
            return
        char = self.char
        hd_model = char.get("hit_dice", {})
        cur, mx = char.get("current_hp", 0), char.get("max_hp", 0)
        healed = 0
        dice_spent = 0
        con = ability_mod(char, "CON")
        feats = char.get("feats", [])
        for _ in range(max(0, hit_dice_to_spend)):
            for die_key in sorted(hd_model, key=lambda k: -int(k[1:])):
                d = hd_model[die_key]
                if d.get("remaining", 0) > 0:
                    sides = int(die_key[1:])
                    roll = random.randint(1, sides)
                    if "Durable" in feats:
                        roll = max(roll, 2 * con, 2)
                    heal = max(0, roll + con)
                    if "Dwarven Fortitude" in feats:
                        heal = max(heal, 1)
                    if "Vigor of the Hill Giant" in feats:
                        heal += con + get_prof_bonus(char)
                    healed += heal
                    d["remaining"] -= 1
                    dice_spent += 1
                    break
        char["current_hp"] = min(mx, cur + healed)
        for r in char.get("resources", []):
            if r.get("reset") in ("SR", "sr", "SR/LR"):
                r["current"] = r.get("current_max") or r.get("max", 0)
        if class_levels(char).get("Bard", 0) >= 5:
            for r in char.get("resources", []):
                if "bardic inspiration" in str(r.get("name", "")).lower():
                    r["current"] = r.get("current_max") or r.get("max", 0)
        char["pact_slots_used"] = 0
        char["_relentless_rage_uses"] = 0
        expired = self._clear_expired_active_effects(("short",))
        expired += self._clear_active_toggles()
        self.ctrl.refresh()
        if dice_spent:
            self.restToastRequested.emit(f"Short rest: spent {dice_spent} hit dice, healed {healed} HP")
        else:
            self.restToastRequested.emit("Short rest complete -- SR resources restored")
        if expired:
            self.restToastRequested.emit(f"Faded: {', '.join(expired)}")
        self.statsChanged.emit()

    @Slot()
    def applyLongRest(self):
        if not self.hasCharacter:
            return
        char = self.char
        from dnd_app.core.character import long_rest_block_reason
        if long_rest_block_reason(char):   # backstop -- RestFlowDialog checks first
            return
        char["current_hp"] = char.get("max_hp", 0)
        char["temp_hp"] = 0
        restore_hit_dice_pool(char)
        for r in char.get("resources", []):
            if r.get("reset") in ("LR", "lr", "SR", "sr", "SR/LR"):
                r["current"] = r.get("current_max") or r.get("max", 0)
        char["death_saves"] = {"successes": 0, "failures": 0}
        char["spell_slots_used"] = [0] * 9
        char["pact_slots_used"] = 0
        char["_relentless_rage_uses"] = 0
        char["exhaustion"] = max(0, char.get("exhaustion", 0) - 1)
        expired = self._clear_expired_active_effects(("short", "long"))
        expired += self._clear_active_toggles()
        was_concentrating = char.get("concentration", {}).get("spell")
        if was_concentrating:
            drop_concentration(char)
            expired.append(f"concentration on {was_concentrating}")
        # dawn comes: magic items get their charges back (core/magic_items.py)
        from dnd_app.core.magic_items import charges_at_dawn
        dawn = charges_at_dawn(char)
        rebuild(char)
        self.ctrl.refresh()
        from dnd_app.data.flavor_text import random_long_rest_dream
        items = ("\nAt dawn: " + "; ".join(dawn)) if dawn else ""
        if expired:
            self.restToastRequested.emit(f"Faded: {', '.join(expired)}{items}")
        else:
            self.restToastRequested.emit(f"Long rest complete -- HP, slots & resources restored{items}\n{random_long_rest_dream()}")
        self.statsChanged.emit()

    # ── Rest options ("also reconfigure?" checklist) -- one Slot per
    # shape of follow-up needed, matching _apply_rest_options exactly.
    @Slot(str, result=list)
    def restOptionPool(self, kind: str):
        char = self.char
        if kind == "armorer_model":
            return ["Guardian – Thunder Gauntlets (1d8 thunder, target has disadvantage attacking others); "
                    "bonus action: temp HP = artificer level, PB times/long rest",
                    "Infiltrator – Lightning Launcher (ranged 90/300ft, 1d6 lightning + extra 1d6 once/turn); "
                    "+5ft speed; advantage on Stealth checks"]
        if kind == "eladrin_season":
            return ["Autumn – Fey Step charms one creature within 5 ft. of your destination",
                    "Winter – Fey Step frightens one creature within 5 ft. of your destination",
                    "Spring – a willing creature within 5 ft. can teleport with you",
                    "Summer – Fey Step deals 2d6 fire damage to creatures within 5 ft. of your origin"]
        if kind == "guidance_spirits_swap":
            return list(_LEVELUP_ALL_SKILLS)
        if kind == "whispers_dead_swap":
            return list(_LEVELUP_ALL_SKILLS) + list(SWAP_TOOLS_POOL)
        if kind == "lunar_phase_swap":
            return ["Full Moon", "New Moon", "Crescent Moon"]
        if kind == "pact_blade_bond":
            return [n for n in (i.get("name") if isinstance(i, dict) else i
                                 for i in char.get("magic_items", [])) if n]
        if kind == "astral_knowledge_swap":
            return list(_LEVELUP_ALL_SKILLS)
        return []

    @Slot(result=list)
    def astralKnowledgeToolPool(self):
        from dnd_app.data.items import WEAPON_NAMES
        return list(WEAPON_NAMES) + list(ALL_TOOLS)

    @Slot(str)
    def applyRestOptionSimple(self, kind: str):
        """Options needing no follow-up value pick -- unprepare_all
        applies immediately, the two pact-focus replacements are purely
        flavor toasts with no mechanical branch."""
        char = self.char
        if kind == "unprepare_all":
            bonus = set(char.get("bonus_spells", []))
            before = len(char.get("spells_prepared", []))
            char["spells_prepared"] = [n for n in char.get("spells_prepared", []) if n in bonus]
            removed = before - len(char["spells_prepared"])
            if removed:
                self.toastRequested.emit(f"Unprepared {removed} spell(s) -- pick new ones from the Spells tab")
        elif kind == "pact_tome_replace":
            self.toastRequested.emit("Received a replacement Book of Shadows from your patron")
        elif kind == "pact_talisman_replace":
            self.toastRequested.emit("Received a replacement Talisman from your patron")
        else:
            return
        rebuild(char)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def applyRestOptionWithValue(self, kind: str, value: str):
        char = self.char
        choices = char.setdefault("_choices", {})
        if kind == "armorer_model":
            choices["armorer_model_3"] = [value]
            self.toastRequested.emit(f"Arcane Armor model changed to {value.split(' – ')[0]}")
        elif kind == "eladrin_season":
            choices["eladrin_season"] = [value]
            self.toastRequested.emit(f"Eladrin season changed to {value.split(' – ')[0]}")
        elif kind == "guidance_spirits_swap":
            choices["guidance_of_the_spirits_skill"] = [value]
            self.toastRequested.emit(f"Guidance of the Spirits now grants {value}")
        elif kind == "whispers_dead_swap":
            choices["whispers_of_the_dead_prof"] = [value]
            self.toastRequested.emit(f"Whispers of the Dead now grants {value}")
        elif kind == "lunar_phase_swap":
            choices["lunar_phase"] = [value]
            self.toastRequested.emit(f"Lunar phase changed to {value}")
        elif kind == "pact_blade_bond":
            choices["pact_weapon_bond"] = [value]
            self.toastRequested.emit(f"{value} bonded as your pact weapon")
        else:
            return
        rebuild(char)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def applyAstralKnowledgeSwap(self, skill: str, weapon_or_tool: str):
        char = self.char
        choices = char.setdefault("_choices", {})
        choices["astral_knowledge_skill"] = [skill]
        choices["astral_knowledge_weapon_or_tool"] = [weapon_or_tool]
        self.toastRequested.emit(f"Astral Knowledge/Trance: {skill}, {weapon_or_tool}")
        rebuild(char)
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot()
    def applyArcaneRecovery(self):
        """Desktop lets you manually pick which expended slot levels to
        recover (any combination totaling <= the level budget, via a
        dedicated checkbox dialog); simplified here to the single
        obviously-best choice -- greedily recover the highest slot
        levels first within budget -- since a hand-picked combination
        rarely beats "recover the biggest slots you can" and building
        an equivalent budget-constrained multi-select control isn't
        worth the added complexity for a single-class, single-feature
        edge case."""
        from math import ceil
        char = self.char
        wiz_lvl = class_levels(char).get("Wizard", 0)
        budget = ceil(wiz_lvl / 2)
        slots_used = char.get("spell_slots_used", [0] * 9)
        recovered = []
        for lvl in range(5, 0, -1):
            idx = lvl - 1
            while idx < len(slots_used) and slots_used[idx] > 0 and budget >= lvl:
                if restore_spell_slot(char, lvl):
                    recovered.append(lvl)
                    budget -= lvl
                slots_used = char.get("spell_slots_used", [0] * 9)
        if recovered:
            res = next((r for r in char.get("resources", []) if r.get("key") == "arcane_recovery"), None)
            if res:
                res["current"] = 0
            self.toastRequested.emit(
                f"Arcane Recovery: recovered {len(recovered)} slot(s) (levels {', '.join(map(str, sorted(recovered)))})")
        self.ctrl.refresh()
        self.statsChanged.emit()

    # ── Level-up ─────────────────────────────────────────────────────
    # Not full desktop parity: ui_desktop's level-up flow
    # (levelup_multiclass.py + levelup_panel.py, ~3700 lines combined)
    # additionally covers optional/alternate class features (TCoE).
    # Race-specific choices, class tool proficiency choices, and
    # DM-reward grants ARE ported -- they route through the same
    # generic _raw_choices_needed()/apply_choice() pipeline below via
    # _get_race_choices/_get_class_tool_choices/_get_dm_reward_choices.
    # Free-choice-from-full-list choice types (Infusions beyond the
    # existing Infusions tab, Metamagic, Eldritch Invocations, Magical
    # Secrets) aren't surfaced yet either -- their own dedicated
    # catalogs are a further increment. HP is NOT a manual roll-or-
    # average choice: confirmed desktop has no such option either --
    # calculator.py's compute_max_hp() always uses average (or full,
    # under the optional_rules max_hp_per_level rule), applied
    # automatically by the same ctrl.refresh() every other mutation
    # here already uses.
    #
    # get_choices_needed()/apply_choice() (core/builder.py) drive most
    # of this directly and generically -- "subclass" and "asi_or_feat"
    # are the two types that need bespoke handling (a subclass pick
    # calls set_subclass() directly rather than being interpreted from
    # the raw choice string, and asi_or_feat needs one of two very
    # different UIs depending which the player picks), everything else
    # (skill_prof/expertise/language/tool_prof/subclass) is answered
    # via the single generic apply_choice() call.
    @Property(list, notify=statsChanged)
    def levelUpClassOptions(self):
        taken = {c["class"]: c["level"] for c in self.char.get("classes", [])}
        # Matches desktop's _meets_multiclass_reqs: when the optional
        # rule is off, every class is eligible regardless of score.
        enforce = self.char.get("optional_rules", {}).get("multiclass_ability_reqs", True)
        scores = {ab: ability_score(self.char, ab) for ab in ABILITIES}
        out = []
        for cname in taken:
            out.append({"name": cname, "currentLevel": taken[cname], "isNew": False})
        for cname in CLASS_DICT:
            if cname in taken:
                continue
            met, reason = (True, "") if not enforce else check_multiclass_prereq(cname, scores)
            if met:
                out.append({"name": cname, "currentLevel": 0, "isNew": True})
        # Sorted by name, not "taken classes first" -- a class's row
        # must stay in the same visual slot regardless of whether
        # multiclassing into it (or leveling/removing another class)
        # changes which group it's in, or a tap aimed at one class's
        # button can land on a different class's row that just shifted
        # into its place.
        out.sort(key=lambda o: o["name"])
        return out

    @Slot(str)
    def levelUpClass(self, class_name: str):
        from dnd_app.core.character import level_up_block_reason
        why = level_up_block_reason(self.char, class_name)   # level 20, total or class
        if why:
            self.toastRequested.emit(f"Can't gain a level -- {why}")
            return
        entry = get_class_entry(self.char, class_name)
        had_sub = entry.get("subclass", "") if entry else ""
        if entry:
            set_class_level(self.char, class_name, entry["level"] + 1)
        else:
            add_class(self.char, class_name, level=1)
        self.ctrl.refresh()
        entry = get_class_entry(self.char, class_name)
        msg = f"{class_name} is now level {entry['level']}"
        if entry.get("subclass") and not had_sub and entry["level"] > 1:   # set aside by a level down
            msg += f" -- {entry['subclass']} is back"
        if self.hasPendingChoices:
            msg += " -- go to Choices to pick your new options"
        self.toastRequested.emit(msg)
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    @Property(bool, notify=statsChanged)
    def hasPendingChoices(self):
        # "info" entries (Beast Master companion, Ascendant Dragon's
        # Draconic Strike, ...) are notices pre-filled with "ack", not
        # choices -- desktop's own unfinished-filter skips them too.
        # Counting them kept this true forever for those subclasses,
        # which would leave the Choices pulse running with nothing to do.
        return any(c["type"] != "info" for c in self._raw_choices_needed())

    def _raw_choices_needed(self):
        # _get_subclass_choices is the single biggest source here despite
        # its name -- Eldritch Invocations (with the real prereq-filtered
        # pool, unlike get_choices_needed()'s own pool=None placeholder),
        # Sorcerer Metamagic, Bard Magical Secrets, and dozens of other
        # subclass-specific picks (Rune Knight, Kensei weapons, Arcane
        # Archer, Circle of the Land, Totem Warrior, Storm Herald,
        # Armorer, Path of the Beast, Draconic Bloodline, The Genie,
        # Drakewarden, The Fiend, Divine Soul, Acolyte of Strength,
        # Death/Knowledge Domain, Blood Hunter fighting style, etc.) all
        # come from this one function, in the same count+pool shape the
        # generic picker already renders.
        choices = (get_choices_needed(self.char) + _get_race_choices(self.char)
                   + _get_class_tool_choices(self.char) + _get_feat_choices(self.char)
                   + _get_dm_reward_choices(self.char) + _get_subclass_choices(self.char))
        # A handful of choices use pool=None on desktop because their own
        # bespoke widget (a free-text combobox, or a dedicated search
        # list) supplies the real candidate list at render time instead
        # of it living in the choice dict -- the generic pool-of-buttons
        # picker here needs an actual pool up front, so fill in the same
        # candidate list desktop's widget would have used.
        for c in choices:
            # Class skill picks like Rogue's "Any 4 skills" arrive as
            # pool=None and Bard's as the literal placeholder
            # ["Any 3 skills"] -- desktop's _build_skill_chooser swaps
            # both for the full skill list. Without this the Rogue card
            # was hidden (no pool) and the Bard card offered one
            # meaningless "Any 3 skills" option, so neither could ever be
            # completed and hasPendingChoices stayed true for good.
            # Skills already proficient from elsewhere are left out (a
            # wasted pick; desktop greys them out instead), except this
            # choice's own earlier picks.
            pool = c.get("pool")
            if c["type"] == "skill_prof" and (
                    not pool or (len(pool) == 1 and "any" in str(pool[0]).lower())):
                already = set(c.get("already_chosen") or [])
                skills = self.char.get("skills", {})
                c["pool"] = [s for s in _LEVELUP_ALL_SKILLS
                             if s in already or skills.get(s, 0) < 2]
                continue
            if pool is not None:
                continue
            if c["type"] == "tool_prof":
                c["pool"] = list(ALL_TOOLS)
            elif c["type"] == "skill_or_tool_prof":
                c["pool"] = list(_LEVELUP_ALL_SKILLS) + list(ALL_TOOLS)
            elif c["type"] == "weapon_or_tool_prof":
                c["pool"] = list(WEAPON_NAMES) + list(ALL_TOOLS)
            elif c["type"] == "maneuver":
                # Matches desktop's _build_maneuver_chooser: always the
                # full Battle Master list, with the "SD" placeholder
                # resolved to this character's actual superiority die.
                sd = get_superiority_die(self.char)
                c["pool"] = [re.sub(r"\bSD\b", sd, m) for m in BATTLE_MASTER_MANEUVERS]
            elif c["type"] == "magical_secrets":
                # Matches desktop's _build_spell_chooser_generic: no pool
                # given means "any class's spell list" (true Magical
                # Secrets), not just this character's known spells.
                c["pool"] = sorted(SPELL_DICT.keys())
            elif c["type"] == "expertise":
                # Matches desktop's _build_skill_chooser: no explicit pool
                # given means "any skill you're already proficient in"
                # (Expertise doubles an existing proficiency bonus, so it
                # requires one to exist first). Desktop's own pool can
                # still include a skill this exact choice already raised
                # to Expertise (shown greyed-out/re-selectable there,
                # since the generic pool-of-buttons picker here has no
                # such greyed state) -- excluded here instead, since
                # re-picking it would be a pure no-op with no upside.
                already = set(c.get("already_chosen") or [])
                c["pool"] = sorted(s for s, lvl in self.char.get("skills", {}).items()
                                    if lvl >= 2 and s not in already)
            elif c["type"] == "infusion":
                # Matches desktop's _build_infusion_chooser: only
                # infusions this character's Artificer level actually
                # qualifies for (e.g. Arcane Propulsion Armor needs 14th
                # level).
                art_lvl = class_levels(self.char).get("Artificer", 0)
                c["pool"] = [inf for inf in ARTIFICER_INFUSIONS
                             if get_infusion_min_level(inf) <= art_lvl]
        return choices

    @Property(list, notify=statsChanged)
    def pendingLevelUpChoices(self):
        # count is how many MORE picks are needed (already computed as
        # "remaining" by every _get_*_choices source); alreadyChosen is
        # exposed so the multi-select card in QML can show prior picks
        # from an earlier level-up alongside this level-up's new ones,
        # matching desktop's ChoiceWidget seeding self._selected from
        # already_chosen at open time.
        return [
            {"id": c["id"], "label": c["label"], "type": c["type"],
             "count": c["count"], "pool": c.get("pool") or [],
             "alreadyChosen": c.get("already_chosen") or []}
            for c in self._raw_choices_needed()
            if c["type"] not in ("asi_or_feat", "subclass") and c.get("pool")
        ]

    @Property(list, notify=statsChanged)
    def pendingAsiOrFeatChoices(self):
        return [
            {"id": c["id"], "label": c["label"], "sourceName": c["source_name"]}
            for c in self._raw_choices_needed() if c["type"] == "asi_or_feat"
        ]

    @Property(list, notify=statsChanged)
    def pendingSubclassChoices(self):
        return [
            {"id": c["id"], "label": c["label"], "sourceName": c["source_name"],
             "pool": c.get("pool") or []}
            for c in self._raw_choices_needed() if c["type"] == "subclass"
        ]

    @Slot(str, list)
    def applyLevelUpChoice(self, choice_id: str, selected: list):
        # Matches desktop's LevelUpPanel._on_choice_confirmed dispatch:
        # most choice IDs just need the generic _choices[id] = selected
        # (apply_choice's own job), but a handful also have to write
        # into the specific top-level char field other code (Features
        # tab, spell lists, calculator.py) actually reads, since nothing
        # in the shared rebuild() pipeline copies _choices into those
        # fields on its own.
        char = self.char
        if choice_id.endswith("_fighting_style"):
            fs = char.get("fighting_styles", [])
            for item in selected:
                if item not in fs:
                    fs.append(item)
            char["fighting_styles"] = fs
        elif choice_id == "eldritch_invocations":
            char["eldritch_invocations"] = selected
        elif choice_id.endswith("_maneuvers"):
            existing = char.get("battle_master_maneuvers", [])
            for m in selected:
                if m not in existing:
                    existing.append(m)
            char["battle_master_maneuvers"] = existing
        elif (choice_id == "magical_secrets_spells" or choice_id.startswith("bard_magical_secrets")
                or choice_id.startswith("bard_lore_secrets") or choice_id.startswith("mystic_arcanum_")):
            for sp_name in selected:
                if sp_name not in char.get("spells_known", []):
                    char.setdefault("spells_known", []).append(sp_name)
            if choice_id == "magical_secrets_spells":
                char["magical_secrets_spells"] = selected
        elif "expertise" in choice_id:
            for skill in selected:
                char.setdefault("skills", {})[skill] = 3
            # Aggregate into a dedicated key (same pattern as
            # "_skill_profs" -> class_skill_profs) so rebuild() can
            # re-derive every expertise choice from _choices rather than
            # relying solely on the raw skills dict.
            char.setdefault("_choices", {})[choice_id] = selected
            all_expertise = []
            for k, v in char["_choices"].items():
                if "expertise" in k and isinstance(v, list):
                    all_expertise.extend(v)
            char["_choices"]["class_skill_expertise"] = list(set(all_expertise))
        elif choice_id == "artificer_infusions":
            # "Known" and "active" are different -- learning an infusion
            # just adds it to the repertoire; actually infusing an item
            # happens separately via the Infusions tab. If an infusion
            # is un-learned (replaced at a later level-up) while still
            # active on an item, that active assignment is dropped too,
            # since the character can no longer maintain it.
            prev = set(char.get("artificer_infusions", []))
            new = set(selected)
            char["artificer_infusions"] = selected
            removed_names = {inf.split(" – ")[0].strip() for inf in (prev - new)}
            if removed_names:
                char["active_infusions"] = [
                    a for a in char.get("active_infusions", [])
                    if a.get("infusion") not in removed_names]
        apply_choice(char, choice_id, selected)
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    @Slot(str, str)
    def applySubclassLevelUpChoice(self, choice_id: str, subclass_name: str):
        choice = next((c for c in self._raw_choices_needed() if c["id"] == choice_id), None)
        if choice is None:
            return
        set_subclass(self.char, choice["source_name"], subclass_name)
        apply_choice(self.char, choice_id, [subclass_name])
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    @Slot(str, dict)
    def applyAsiLevelUpChoice(self, choice_id: str, allocations: dict):
        selected = [f"asi:{ability}:{amount}" for ability, amount in allocations.items() if amount > 0]
        apply_choice(self.char, choice_id, selected)
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    @Slot(str, str)
    def applyFeatLevelUpChoice(self, choice_id: str, feat_name: str):
        # Safety net, not the primary gate -- searchFeatsForLevelUp
        # already reports metPrereq so the UI can disable ineligible
        # feats the same way desktop's feat list greys them out.
        feat = get_feat(feat_name)
        if feat and not feat_prereq_met(self.char, feat)[0]:
            return
        add_feat(self.char, feat_name)
        apply_choice(self.char, choice_id, [f"feat:{feat_name}"])
        self.statsChanged.emit()
        self.autosaveRequested.emit()

    @Slot(str, result=list)
    def searchFeatsForLevelUp(self, query: str):
        q = (query or "").strip().lower()
        out = []
        for f in ALL_FEATS:
            name = f["name"]
            if q and q not in name.lower():
                continue
            met, reason = feat_prereq_met(self.char, f)
            out.append({"name": name, "source": f.get("source", ""), "special": f.get("special", ""),
                        "desc": f.get("special", ""), "prereq": f.get("prereq", ""), "metPrereq": met})
        return out

    # ── TCE/TCoE Versatility swaps (Eldritch/Martial/Bardic/Sorcerous) ──
    # Desktop's LevelUpMulticlassDialog ties these to the exact instant a
    # character levels into an ASI-granting level; Android instead makes
    # each swap available any time the character has already reached the
    # relevant class's minimum ASI level (4) and the optional rule is on
    # -- a permanent rather than one-shot-per-transition opportunity,
    # which is more permissive but never less capable. The "cantrip" swap
    # kind every one of these rules also offers is deliberately NOT
    # reimplemented here: swapping a known cantrip is already fully
    # possible at any time via removeKnownSpell + addKnownSpell (the
    # spell browser), so only the kinds with no existing equivalent --
    # Pact Boon, Mystic Arcanum, Fighting Style, Battle Master Maneuver,
    # Expertise, and Metamagic -- are surfaced here.
    _PACT_BOONS = [
        "Pact of the Blade (summon a pact weapon)",
        "Pact of the Chain (imp/quasit/pseudodragon/sprite familiar)",
        "Pact of the Tome (Book of Shadows: 3 extra cantrips from any class, cast as rituals if the spell allows)",
        "Pact of the Talisman (amulet: +1d4 to a failed ability check, uses = proficiency bonus per long rest)",
    ]

    @Property('QVariantMap', notify=statsChanged)
    def versatilityOptions(self):
        char = self.char
        opt = char.get("optional_rules", {})
        classes = {c["class"]: c["level"] for c in char.get("classes", [])}
        out = {}

        if opt.get("eldritch_versatility") and classes.get("Warlock", 0) >= 4:
            current = char.get("_choices", {}).get("warlock_pact_boon", [])
            if current:
                pool = [p for p in self._PACT_BOONS if p != current[0]]
                out["pactBoon"] = {"current": current[0], "pool": pool}

            ARCANUM_LEVELS = {11: 6, 13: 7, 15: 8, 17: 9}
            warlock_lvl = classes["Warlock"]
            units = []
            for char_lvl, spell_lvl in sorted(ARCANUM_LEVELS.items()):
                if warlock_lvl >= char_lvl:
                    chosen = char.get("_choices", {}).get(f"mystic_arcanum_{spell_lvl}", [])
                    if chosen:
                        pool = [s["name"] for s in spells_for_class_at_level("Warlock", spell_lvl)
                                if s["name"] != chosen[0]]
                        units.append({"spellLevel": spell_lvl, "old": chosen[0], "pool": pool})
            if units:
                out["arcanum"] = {"units": units}

        mv_classes = ("Fighter", "Paladin", "Ranger")
        mv_cls = next((c for c in mv_classes if classes.get(c, 0) >= 4), None)
        known_styles = char.get("fighting_styles", [])
        if opt.get("martial_versatility") and mv_cls and known_styles:
            pool_full = _MV_FIGHTING_STYLES.get(mv_cls, [])
            new_pool = [s for s in pool_full if not any(
                s.split(" (")[0].strip().lower() == ks.split(" (")[0].strip().lower() for ks in known_styles)]
            if new_pool:
                out["fightingStyle"] = {"class": mv_cls, "current": known_styles, "pool": new_pool}

        known_maneuvers = char.get("battle_master_maneuvers", [])
        if opt.get("martial_versatility") and classes.get("Fighter", 0) >= 4 and known_maneuvers:
            sd = get_superiority_die(char)
            new_pool = [re.sub(r"\bSD\b", sd, m) for m in BATTLE_MASTER_MANEUVERS
                        if not any(m.split(" – ")[0].strip().lower() == km.split(" – ")[0].strip().lower()
                                   for km in known_maneuvers)]
            if new_pool:
                out["maneuver"] = {"current": known_maneuvers, "pool": new_pool}

        if opt.get("bardic_versatility") and classes.get("Bard", 0) >= 4:
            skills = char.get("skills", {})
            expert_skills = sorted(s for s, lvl in skills.items() if lvl == 3)
            proficient_only = sorted(s for s, lvl in skills.items() if lvl == 2)
            if expert_skills and proficient_only:
                out["expertise"] = {"from": expert_skills, "to": proficient_only}

        if opt.get("sorcerous_versatility") and classes.get("Sorcerer", 0) >= 4:
            known_mm = char.get("_choices", {}).get("sorcerer_metamagic", [])
            if known_mm:
                new_pool = [m for m in METAMAGIC if not any(
                    m.split(" – ")[0].strip().lower() == km.split(" – ")[0].strip().lower() for km in known_mm)]
                if new_pool:
                    out["metamagic"] = {"current": known_mm, "pool": new_pool}

        return out

    @Slot(str)
    def applyPactBoonVersatility(self, new_boon: str):
        char = self.char
        char.setdefault("_choices", {})["warlock_pact_boon"] = [new_boon]
        # Cascading Eldritch Invocation re-check, per the actual rule
        # text: if this change makes a Pact-of-the-X-specific invocation
        # ineligible, remove it so the player must re-choose via the
        # existing invocation chooser (which already only offers
        # eligible options).
        new_boon_name = next((b for b in ("blade", "chain", "tome", "talisman") if b in new_boon.lower()), "")
        new_pact_tag = f"(pact of the {new_boon_name})" if new_boon_name else ""
        kept, removed = [], []
        for inv in char.get("eldritch_invocations", []):
            inv_lower = inv.lower()
            if "pact of the" in inv_lower and new_pact_tag and new_pact_tag not in inv_lower:
                removed.append(inv)
            else:
                kept.append(inv)
        char["eldritch_invocations"] = kept
        # ...and out of the pick itself, so the chooser asks again
        held = char["_choices"].get("eldritch_invocations")
        if isinstance(held, list):
            char["_choices"]["eldritch_invocations"] = [i for i in held if i not in removed]
        boon_label = new_boon.split("(")[0].strip()
        if removed:
            self.toastRequested.emit(f"Pact Boon changed to {boon_label} — {len(removed)} "
                                      f"invocation(s) no longer eligible, re-choose them in Choices")
        else:
            self.toastRequested.emit(f"Pact Boon changed to {boon_label}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(int, str, str)
    def applyArcanumVersatility(self, spell_level: int, old_name: str, new_name: str):
        char = self.char
        char.setdefault("_choices", {})[f"mystic_arcanum_{spell_level}"] = [new_name]
        # Also update spells_known, since that's where the initial pick
        # was recorded (see applyLevelUpChoice's mystic_arcanum_ branch) --
        # leaving the old spell known and the new one absent would be a
        # broken result, not a faithful port of a genuine rule nuance.
        known = char.setdefault("spells_known", [])
        if old_name in known:
            known.remove(old_name)
        if new_name not in known:
            known.append(new_name)
        for field in ("spells_prepared", "quick_spells"):
            lst = char.get(field, [])
            if old_name in lst:
                lst.remove(old_name)
        self.toastRequested.emit(f"Eldritch Versatility: swapped Mystic Arcanum {old_name} for {new_name}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def applyFightingStyleVersatility(self, old_style: str, new_style: str):
        from dnd_app.core.builder import swap_choice_pick
        styles = self.char.setdefault("fighting_styles", [])
        if old_style in styles:
            styles.remove(old_style)
        styles.append(new_style)
        swap_choice_pick(self.char, lambda k: "fighting_style" in k, old_style, new_style)
        self.toastRequested.emit(f"Martial Versatility: swapped {old_style.split(' (')[0].strip()} "
                                  f"for {new_style.split(' (')[0].strip()}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def applyManeuverVersatility(self, old_maneuver: str, new_maneuver: str):
        from dnd_app.core.builder import swap_choice_pick
        maneuvers = self.char.setdefault("battle_master_maneuvers", [])
        if old_maneuver in maneuvers:
            maneuvers.remove(old_maneuver)
        maneuvers.append(new_maneuver)
        swap_choice_pick(self.char, lambda k: "maneuvers" in k, old_maneuver, new_maneuver)
        self.toastRequested.emit(f"Martial Versatility: swapped maneuver {old_maneuver.split(' – ')[0].strip()} "
                                  f"for {new_maneuver.split(' – ')[0].strip()}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def applyExpertiseVersatility(self, old_skill: str, new_skill: str):
        from dnd_app.core.builder import move_expertise
        move_expertise(self.char, old_skill, new_skill)       # in the pick, so it stays
        self.toastRequested.emit(f"Bardic Versatility: moved Expertise from {old_skill} to {new_skill}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    @Slot(str, str)
    def applyMetamagicVersatility(self, old_metamagic: str, new_metamagic: str):
        mm = self.char.setdefault("_choices", {}).setdefault("sorcerer_metamagic", [])
        if old_metamagic in mm:
            mm.remove(old_metamagic)
        mm.append(new_metamagic)
        self.toastRequested.emit(f"Sorcerous Versatility: swapped metamagic "
                                  f"{old_metamagic.split(' – ')[0].strip()} for {new_metamagic.split(' – ')[0].strip()}")
        self.ctrl.refresh()
        self.statsChanged.emit()

    # ── Companions (mounts/vehicles/summoned creatures/class-granted
    # companions) -- verbatim port of ui_desktop/pages/sheet/companions.py's
    # data model and mechanics, normalized into camelCase dicts for QML.
    def _normalize_statblock(self, sb: dict, hp_key: str = None) -> dict:
        raw_hp = sb.get("hp")
        max_hp = raw_hp if isinstance(raw_hp, int) else 1
        tracking = self.char.get("summon_hp_tracking", {})
        return {
            "displayName": sb.get("display_name", ""),
            "source": sb.get("source", ""),
            "size": sb.get("size", ""),
            "creatureType": sb.get("creature_type", ""),
            "ac": str(sb.get("ac", "")),
            "hp": raw_hp if raw_hp is not None else "",
            "hitDice": sb.get("hit_dice", ""),
            "speed": sb.get("speed", ""),
            "abilities": [
                {"ability": ab, "score": score, "mod": _mod_text((score - 10) // 2)}
                for ab, score in sb.get("abilities", {}).items()
            ],
            "saves": [{"name": a, "bonus": v} for a, v in sb.get("saves", [])],
            "skills": [{"name": a, "bonus": v} for a, v in sb.get("skills", [])],
            "damageResistances": sb.get("damage_resistances", ""),
            "damageImmunities": sb.get("damage_immunities", ""),
            "conditionImmunities": sb.get("condition_immunities", ""),
            "senses": sb.get("senses", ""),
            "languages": sb.get("languages", ""),
            "traits": [{"name": n, "desc": d} for n, d in sb.get("traits", [])],
            "actions": [{"name": n, "desc": d} for n, d in sb.get("actions", [])],
            "reactions": [{"name": n, "desc": d} for n, d in sb.get("reactions", [])],
            "hpKey": hp_key or "",
            "maxHp": max_hp,
            "currentHp": tracking.get(hp_key, max_hp) if hp_key else max_hp,
            "hasHpTracking": bool(hp_key),
        }

    @Property(list, constant=True)
    def mountOptions(self):
        return [row[0] for row in MOUNTS]

    @Property(list, constant=True)
    def findSteedOptions(self):
        out = [{"label": f"{n} (Find Steed)", "value": n}
               for n in ["Warhorse", "Pony", "Camel", "Elk", "Mastiff"]]
        out += [{"label": f"{n} (Find Greater Steed)", "value": n}
                for n in FIND_GREATER_STEED_OPTIONS]
        return out

    @Property(list, notify=statsChanged)
    def ownedMounts(self):
        out = []
        for i, mount_name in enumerate(self.char.get("owned_mounts", [])):
            sb_data = get_mount_statblock(mount_name)
            if not sb_data:
                continue
            sb = {
                "display_name": mount_name, "source": "Mount",
                "size": sb_data["size"], "creature_type": "beast",
                "ac": str(sb_data["ac"]) + (f" ({sb_data['ac_note']})" if sb_data.get("ac_note") else ""),
                "hp": sb_data["hp"], "hit_dice": sb_data["hit_dice"], "speed": sb_data["speed"],
                "abilities": sb_data["abilities"], "saves": [], "skills": sb_data["skills"],
                "senses": sb_data["senses"], "languages": "—",
                "traits": sb_data["traits"], "actions": sb_data["actions"], "reactions": [],
            }
            entry = self._normalize_statblock(sb, hp_key=f"mount_{mount_name}")
            entry["index"] = i
            out.append(entry)
        return out

    @Slot(str)
    def addMount(self, name: str):
        if not name:
            return
        self.char.setdefault("owned_mounts", []).append(name)
        self.statsChanged.emit()

    @Slot(int)
    def removeMount(self, index: int):
        owned = self.char.get("owned_mounts", [])
        if 0 <= index < len(owned):
            owned.pop(index)
            self.statsChanged.emit()

    @Property(list, constant=True)
    def vehicleOptions(self):
        return list(VEHICLES)

    @Property(list, notify=statsChanged)
    def ownedVehicles(self):
        gear_lookup = {g[0]: g for g in ADVENTURING_GEAR}
        out = []
        for i, vname in enumerate(self.char.get("owned_vehicles", [])):
            vdata = get_vehicle_statblock(vname)
            if vdata:
                extra_traits = [("Cargo", vdata.get("cargo", "—")), ("Crew", vdata.get("crew", "—"))]
                if vdata.get("passengers"):
                    extra_traits.append(("Passengers", vdata["passengers"]))
                if vdata.get("keel_beam"):
                    extra_traits.append(("Keel/Beam", vdata["keel_beam"]))
                no_stats = vdata.get("no_combat_stats", False)
                is_magic_item = vdata.get("is_magic_item", False)
                if vdata.get("keel_beam"):
                    source_label = "Spelljamming Vessel"
                elif vname in VEHICLES_BGDIA:
                    source_label = "Combat Vehicle (Bigby Presents: Glory of the Giants)"
                elif is_magic_item and no_stats:
                    source_label = "Magic Item Vehicle (no official combat stats)"
                elif is_magic_item:
                    source_label = "Magic Item Vehicle"
                elif no_stats:
                    source_label = "Astral Vehicle (no official combat stats)"
                elif vname in VEHICLES_AIR:
                    source_label = "Air Vehicle"
                elif vname in VEHICLES_LAND:
                    source_label = "Land Vehicle"
                else:
                    source_label = "Vehicle"
                sb = {
                    "display_name": vname, "source": source_label,
                    "size": vdata["size"], "creature_type": "vehicle (object)",
                    "ac": "—" if no_stats else str(vdata["ac"]),
                    "hp": "—" if no_stats else vdata["hp"], "hit_dice": "",
                    "speed": vdata["speed"], "abilities": vdata.get("abilities", {}), "saves": [], "skills": [],
                    "damage_immunities": vdata.get("damage_immunities", ""),
                    "condition_immunities": vdata.get("condition_immunities", ""),
                    "senses": "—", "languages": "—",
                    "traits": vdata.get("traits", []) + extra_traits,
                    "actions": vdata.get("actions", []), "reactions": vdata.get("reactions", []),
                }
                card_hp_key = None if no_stats else f"vehicle_{vname}"
                entry = self._normalize_statblock(sb, hp_key=card_hp_key)
                entry["hasStats"] = True
                entry["index"] = i
                out.append(entry)
            else:
                g = gear_lookup.get(vname)
                desc = g[3] if g else ""
                out.append({"hasStats": False, "index": i, "displayName": vname, "desc": desc})
        return out

    @Slot(str)
    def addVehicle(self, name: str):
        if not name:
            return
        self.char.setdefault("owned_vehicles", []).append(name)
        self.statsChanged.emit()

    @Slot(int)
    def removeVehicle(self, index: int):
        owned = self.char.get("owned_vehicles", [])
        if 0 <= index < len(owned):
            owned.pop(index)
            self.statsChanged.emit()

    @Property(list, constant=True)
    def scalingSummonSpellOptions(self):
        return list(SCALING_SUMMONS)

    @Slot(str, result=list)
    def summonLevelOptions(self, spell_name: str):
        spell = SCALING_SUMMONS.get(spell_name, {})
        return list(range(spell.get("base_level", 1), 10))

    @Slot(str, result=list)
    def summonFormOptions(self, spell_name: str):
        spell = SCALING_SUMMONS.get(spell_name, {})
        return list(spell.get("forms", {}))

    @Property(list, notify=statsChanged)
    def ownedSummons(self):
        out = []
        for i, entry in enumerate(self.char.get("owned_summons", [])):
            sb = resolve_scaling_summon(entry.get("spell"), entry.get("level"), entry.get("form"))
            if not sb:
                continue
            norm = self._normalize_statblock(sb, hp_key=f"summon_{i}")
            norm["index"] = i
            out.append(norm)
        return out

    @Slot(str, int, str)
    def addSummonedCreature(self, spell_name: str, level: int, form: str):
        if not (spell_name and level and form):
            return
        self.char.setdefault("owned_summons", []).append(
            {"spell": spell_name, "level": level, "form": form})
        self.statsChanged.emit()

    @Slot(int)
    def removeSummonedCreature(self, index: int):
        owned = self.char.get("owned_summons", [])
        if 0 <= index < len(owned):
            owned.pop(index)
            self.statsChanged.emit()

    @Property(list, notify=statsChanged)
    def activeCompanions(self):
        out = []
        for key in get_available_companions(self.char):
            sb = resolve_companion_statblock(key, self.char)
            if not sb:
                continue
            is_cannon = key == "eldritch_cannon"
            entry = self._normalize_statblock(sb, hp_key=None if is_cannon else f"companion_{key}")
            entry["isEldritchCannon"] = is_cannon
            entry["companionKey"] = "" if is_cannon else key
            if is_cannon:
                entry["notes"] = sb.get("notes", "")
                entry["cannonTypes"] = [{"name": n, "desc": d} for n, d in sb.get("cannon_types", [])]
            out.append(entry)
        return out

    @Property(list, notify=statsChanged)
    def summonablePrompts(self):
        out = []
        active_summons = self.char.get("active_summoned_companions", [])
        for key in get_summonable_but_inactive_companions(self.char):
            tmpl = COMPANION_STATBLOCKS.get(key, {})
            if tmpl.get("summon_uses_wild_shape"):
                res = next((r for r in self.char.get("resources", []) if r.get("key") == "wild_shape"), None)
                if res is None or not isinstance(res.get("current_max"), int):
                    uses_txt = " (Unlimited Wild Shape uses)"
                else:
                    uses_txt = f" ({res.get('current', 0)}/{res['current_max']} Wild Shape uses left)"
            else:
                res_key = tmpl.get("summon_resource_key")
                res = next((r for r in self.char.get("resources", []) if r.get("key") == res_key), None)
                uses_txt = f" ({res['current']}/{res['current_max']} uses left)" if res else ""
            active_n = count_active_companion_instances(key, active_summons)
            cap = companion_max_simultaneous(key, self.char)
            display_name = tmpl.get("display_name", key)
            status_txt = (f"{active_n}/{cap} active.{uses_txt}" if active_n > 0
                          else f"Not currently summoned.{uses_txt}")
            btn_label = f"Summon another {display_name}" if active_n > 0 else f"Summon {display_name}"
            out.append({"key": key, "displayName": display_name, "statusText": status_txt, "buttonLabel": btn_label})
        return out

    @Slot(str)
    def summonCompanion(self, key: str):
        tmpl = COMPANION_STATBLOCKS.get(key)
        if not tmpl:
            return
        active_now = self.char.get("active_summoned_companions", [])
        if count_active_companion_instances(key, active_now) >= companion_max_simultaneous(key, self.char):
            self.toastRequested.emit(f"Already at the maximum number of active {tmpl['display_name']}s.")
            return
        if tmpl.get("summon_uses_wild_shape"):
            res = next((r for r in self.char.get("resources", []) if r.get("key") == "wild_shape"), None)
            if res is not None and isinstance(res.get("current_max"), int):
                if res.get("current", 0) <= 0:
                    self.toastRequested.emit(
                        "No Wild Shape uses remaining -- available again after a short or long rest.")
                    return
                res["current"] -= 1
        else:
            res_key = tmpl.get("summon_resource_key")
            if res_key:
                res = next((r for r in self.char.get("resources", []) if r.get("key") == res_key), None)
                if res is not None and res.get("current", 0) <= 0:
                    self.toastRequested.emit(f"No uses of {res['name']} remaining -- available again after a long rest.")
                    return
                if res is not None:
                    res["current"] = res.get("current", 1) - 1
        active = self.char.setdefault("active_summoned_companions", [])
        if companion_max_simultaneous(key, self.char) > 1:
            used = {int(a.split("#", 1)[1]) for a in active if a.startswith(key + "#")}
            idx = 0
            while idx in used:
                idx += 1
            instance_key = f"{key}#{idx}"
            active.append(instance_key)
        else:
            instance_key = key
            if key not in active:
                active.append(key)
        sb = resolve_companion_statblock(instance_key, self.char)
        self.char.setdefault("summon_hp_tracking", {})[f"companion_{instance_key}"] = sb.get("hp", 1)
        self.toastRequested.emit(f"{tmpl['display_name']} summoned!")
        self.statsChanged.emit()

    @Slot(str)
    def dismissCompanion(self, key: str):
        active = self.char.get("active_summoned_companions", [])
        if key in active:
            active.remove(key)
            self.statsChanged.emit()

    @Slot(str, int, str)
    def setCompanionHp(self, hp_key: str, value: int, companion_key: str = ""):
        """Verbatim port of _build_statblock_card's HP spinbox handler --
        including the death/replacement consequences that fire when a
        class-granted companion's tracked HP reaches 0."""
        if not hp_key:
            return
        tracking = self.char.setdefault("summon_hp_tracking", {})
        tracking[hp_key] = value
        if value <= 0 and companion_key:
            tmpl = COMPANION_STATBLOCKS.get(companion_key.split("#", 1)[0], {})
            display_name = tmpl.get("display_name", companion_key)
            if tmpl.get("requires_summon_action"):
                self.toastRequested.emit(f"{display_name} has fallen -- re-summon it after a long rest.")
                self.dismissCompanion(companion_key)
                return
            elif tmpl.get("requires_active_infusion"):
                req_name = tmpl["requires_active_infusion"]
                self.char["active_infusions"] = [
                    a for a in self.char.get("active_infusions", []) if a.get("infusion") != req_name]
                self.toastRequested.emit(
                    f"{display_name} has vanished, leaving its heart behind -- "
                    f"re-infuse a gem to create a new one.")
            else:
                pending = self.char.setdefault("companion_pending_replacement", [])
                if companion_key not in pending:
                    pending.append(companion_key)
                self.toastRequested.emit(
                    f"{display_name} has perished -- a new one can be made at your next long rest.")
        self.statsChanged.emit()

    @Property(bool, notify=statsChanged)
    def wildShapeBrowseAvailable(self):
        return bool(get_available_wildshape_beasts(self.char))

    @Property(str, notify=statsChanged)
    def wildShapeBrowseInfoText(self):
        info = get_wild_shape_info(self.char)
        return f"Max CR {info['max_cr']} — {info['restriction']}" if info else ""

    @Property(list, notify=statsChanged)
    def wildShapeBrowseOptions(self):
        names = get_available_wildshape_beasts(self.char)
        names.sort(key=lambda n: WILDSHAPE_BEASTS[n]["cr"])
        return [{"name": n, "crLabel": WILDSHAPE_BEASTS[n]["cr_label"]} for n in names]

    @Slot(str, result="QVariant")
    def wildShapeBeastStatblock(self, name: str):
        beast = WILDSHAPE_BEASTS.get(name)
        if not beast:
            return None
        sb = {
            "display_name": name, "source": f"Wild Shape (CR {beast['cr_label']})",
            "size": beast["size"], "creature_type": "beast",
            "ac": str(beast["ac"]) + (f" ({beast['ac_note']})" if beast.get("ac_note") else ""),
            "hp": beast["hp"], "hit_dice": beast["hit_dice"], "speed": beast["speed"],
            "abilities": beast["abilities"], "saves": [], "skills": beast["skills"],
            "damage_resistances": beast.get("damage_resistances", ""),
            "damage_immunities": beast.get("damage_immunities", ""),
            "condition_immunities": beast.get("condition_immunities", ""),
            "senses": beast["senses"], "languages": "—",
            "traits": beast["traits"], "actions": beast["actions"], "reactions": [],
        }
        return self._normalize_statblock(sb)
