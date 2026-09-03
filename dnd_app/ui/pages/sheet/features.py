import os
import re
import random
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dnd_app.ui.style.theme import *
from ...shared import *
# `import *` silently skips underscore-prefixed names when a module has no
# __all__ (shared.py doesn't) — _btn/_pill need an explicit import for that
# reason. _lbl/_card/_sep don't (they're defined a few lines down as local
# aliases to h/card/hline, which ARE plain names the wildcard import above
# already brought in).
from ...shared import _btn, _pill
from ...widgets import FlowLayout, FlowContainer
from dnd_app.core.character import (
    ability_score, ability_mod, total_level, class_levels, subclasses,
    long_rest, short_rest, add_class
)
from dnd_app.core.calculator import (
    update_all, get_ac, get_prof_bonus, get_initiative,
    all_skill_bonuses, all_saving_throw_bonuses, get_save_advantage_status,
    get_initiative_advantage_status, get_carry_capacity,
    get_spell_save_dc, get_spell_attack_bonus,
    get_passive_perception, get_sneak_attack, get_martial_arts_die,
    get_rage_damage, _detect_spell_ability, get_ac, has_reliable_talent,
    get_ac_breakdown, get_speed_breakdown, get_effective_speed,
    get_save_dc_breakdown, get_spell_attack_breakdown, get_weapon_attack_breakdown,
    get_onhit_damage_bonuses,
)
from dnd_app.core.multiclass import (
    compute_all_spell_slots, get_extra_attacks, aggregate_resources,
    compute_hit_points, get_saving_throw_profs
)
from dnd_app.core.builder import rebuild
from dnd_app.core.controller import CharacterController
from dnd_app.core.magic_items import concentration_save, start_concentration, drop_concentration
from dnd_app.core.spell_components import spell_component_block_reason
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters, character_filename, validate_character,
)
from dnd_app.core.character import set_subclass, get_class_entry
from dnd_app.data.phbCommon.magic_items import ALL_MAGIC_ITEMS, has_item_effect
from dnd_app.ui.dialogs.levelup_panel import LevelUpPanel
from dnd_app.data.phb2014.classes import CLASS_DICT, CLASS_NAMES, BATTLE_MASTER_MANEUVERS, WILD_MAGIC_SURGE_TABLE
from dnd_app.data.phb2014.races import get_race
from dnd_app.data.phbCommon.backgrounds import get_background
from dnd_app.data.phbCommon.feats import get_feat
from dnd_app.data.phbCommon.spells import get_spell, spells_for_class, ALL_SPELLS
from dnd_app.data.phbCommon.items import (ARMOR, ARMOR_DICT, ALL_WEAPONS, WEAPON_DICT,
    ADVENTURING_GEAR, GEAR_NAMES, MOUNTS, ALL_TOOLS, SIMPLE_MELEE, SIMPLE_RANGED,
    MARTIAL_MELEE, MARTIAL_RANGED, ARTISAN_TOOLS, SPECIAL_ARMOR)
from dnd_app.data.phbCommon.conditions import CONDITIONS
from .base import *
from .base import _lbl, _sep, _card


class FeaturesMixin:
    def _refresh_optional_features(self):
        """Rebuild the Optional Class Features card in the Features tab."""
        # No-op if not yet built; features tab handles this via _rebuild_features.
        pass

    # ── Hit dice / currency event handlers ───────────────────────────────────

    def _build_tab_features(self):
        tab = QScrollArea(); tab.setWidgetResizable(True)
        w = QWidget(); tab.setWidget(w)
        self._feat_tab_lay = QVBoxLayout(w); self._feat_tab_lay.setContentsMargins(16,16,16,16); self._feat_tab_lay.setSpacing(12)
        self._feat_sections = []   # (groupbox, content_lay)
        self._feat_tab_lay.addStretch()
        return tab

    @staticmethod
    def _get_subclass_feature_names(cname, subclass_display, D):
        """Parse actual feature names from the subclass data string.
        
        Subclass strings look like:
          'The Archfey – Fey Presence; Misty Escape; Beguiling Defenses'
        Features after '–' are mapped in order to subclass feature slots.
        """
        if not subclass_display:
            return []
        cdata = D.get(cname, {})
        # Find matching subclass entry (display name match)
        sub_display_norm = subclass_display.lower().strip()
        for sub_full in cdata.get("subclasses", []):
            disp = sub_full.split("–")[0].split("—")[0].strip().lower()
            if disp == sub_display_norm or sub_display_norm in disp or disp in sub_display_norm:
                # Found it — parse features after the dash
                if "–" in sub_full:
                    feat_str = sub_full.split("–", 1)[1]
                elif "—" in sub_full:
                    feat_str = sub_full.split("—", 1)[1]
                else:
                    return []
                return [f.strip() for f in feat_str.split(";") if f.strip()]
        return []

    def _rebuild_features(self):
        lay = self._feat_tab_lay
        while lay.count():
            item = lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        # _add_feature_section() inserts each new section at count()-1, i.e.
        # "just before the last item" — which only produces the intended
        # top-to-bottom order (Race, then Ancestry, then Subrace, then each
        # class...) if a stable trailing placeholder already exists before
        # the FIRST section is added. Without one, count()-1 on an empty
        # layout is -1 (Qt appends at the end — fine for the first section),
        # but then count()-1 on a 1-item layout is 0, which inserts BEFORE
        # that first section instead of after it. Re-adding this stretch
        # here (not just once at initial tab construction) is what keeps
        # every rebuild — not only the first one — in the right order.
        lay.addStretch()

        cls_colors = [IND2, PURP2, AMBE2, TEAL2, CRIM2, GOLD2]
        D = CLASS_DICT

        # Race features
        race = self.char.get("species") or self.char.get("race","")
        if race:
            rdata = get_race(race)
            if rdata and rdata.get("traits"):
                display_traits = rdata["traits"]
                # If the active subrace carries its OWN ability score bonus
                # (Dragonmarks, etc.), it fully REPLACES the base race's ASI
                # per builder.py's actual math — so don't show a contradictory
                # "+1 to all six ability scores"-style line alongside it.
                subrace_now = self.char.get("subrace", "")
                if subrace_now:
                    from dnd_app.core.builder import _get_subrace_asi
                    if _get_subrace_asi(race, subrace_now):
                        _asi_line = re.compile(
                            r'^\s*\+\d.*\b(ability scores?|STR|DEX|CON|INT|WIS|CHA)\b',
                            re.IGNORECASE)
                        display_traits = [t for t in display_traits if not _asi_line.match(t)]
                # Only add the section if there's still something left to
                # show — the check above (rdata.get("traits")) only looked
                # at the UNFILTERED list, so a race whose traits happened to
                # be entirely ASI-only would pass that check but then call
                # _add_feature_section with an empty list here, producing a
                # section with nothing in it (or none at all, depending on
                # how that function handles empty items) sitting above
                # Subrace — which is what "subrace displaying before race"
                # would actually look like, even though the add order was
                # correct the whole time.
                if display_traits:
                    self._add_feature_section(f"Race: {race}", TEAL2, display_traits,
                                              badge_color=TEAL2)
            # Draconic ancestry trait (Dragonborn)
            if race == "Dragonborn":
                anc = self.char.get("draconic_ancestry","")
                if anc:
                    try:
                        from dnd_app.data.phb2014.races import DRACONIC_ANCESTRY
                        anc_data = DRACONIC_ANCESTRY.get(anc)
                        if anc_data:
                            dmg, shape, desc = anc_data
                            self._add_feature_section(
                                f"Draconic Ancestry: {anc}", GOLD2,
                                [f"Damage type: {dmg}  ·  Breath shape: {shape}",
                                 f"Breath Weapon: 2d6 (3d6 Lv6, 4d6 Lv11, 5d6 Lv16)  ·  {desc}",
                                 f"Resistance: {dmg} damage"],
                                badge_color=GOLD2)
                    except ImportError: pass
            # Subrace traits
            subrace = self.char.get("subrace","")
            if subrace and rdata:
                import re as _re_sub
                for sub_str in rdata.get("subraces",[]):
                    sub_name=sub_str.split("(")[0].strip()
                    if sub_name==subrace:
                        inner=sub_str[sub_str.find("(")+1:sub_str.rfind(")")]
                        # Strip leading "+ABC N" ASI clauses (shown elsewhere),
                        # one at a time, from the front of the string.
                        asi_pat = _re_sub.compile(r"^\s*[+][A-Z]{3}\s+\d+\s*,?\s*")
                        remainder = inner
                        while True:
                            m = asi_pat.match(remainder)
                            if not m: break
                            remainder = remainder[m.end():]
                        # Some traits (Eladrin's seasonal Fey Step, Shadar-kai's
                        # Blessing, etc.) contain commas WITHIN a single trait's
                        # description. A blind comma-split shreds those into
                        # meaningless fragments. If the remainder contains a
                        # semicolon, treat semicolons as the trait boundary
                        # instead (preserving internal commas); otherwise fall
                        # back to the original comma-split for simple lists.
                        #
                        # Also strip a trailing sourcebook tag (", ERLW)",
                        # ", SCAG)", etc.) — without this it survives the
                        # comma-split and renders as its own meaningless row
                        # (e.g. a feature row that just says "ERLW").
                        _SOURCE_TAGS = {"PHB","XGE","TCE","SCAG","MTOF","FTD","EGW",
                                        "ERLW","VRGTR","BGG","MOT","DSOTDQ","WBTW","GGR"}
                        remainder = remainder.strip().rstrip(",").strip()
                        _last_comma = remainder.rfind(",")
                        if _last_comma >= 0:
                            _tail = remainder[_last_comma+1:].strip()
                            if _tail.upper().replace("/", "") in _SOURCE_TAGS:
                                remainder = remainder[:_last_comma].strip()
                        if ";" in remainder:
                            parts = [p.strip() for p in remainder.split(";") if p.strip()]
                        else:
                            parts = [p.strip() for p in remainder.split(",") if p.strip()]
                        if parts:
                            self._add_feature_section(
                                f"Subrace: {subrace}", TEAL, parts, badge_color=TEAL)
                        break

        # Background feature
        bg = get_background(self.char.get("background",""))
        if bg and bg.get("feature"):
            self._add_feature_section(f"Background: {self.char.get('background','')}", GOLD,
                                      [f"{bg['feature']}: {bg.get('feature_desc','')}"],
                                      badge_color=GOLD)

        # Per-class features
        for ci, c in enumerate(self.char.get("classes",[])):
            cname = c["class"]; clvl = c["level"]; sub = c.get("subclass","")
            color = cls_colors[ci % len(cls_colors)]
            title = f"{cname}" + (f" — {sub}" if sub else "") + f"  (Level {clvl})"
            feats = []
            cdata = D.get(cname, {}); features = cdata.get("features",{})

            # Load proper subclass feature names from SUBCLASS_FEATURES
            try:
                from dnd_app.data.phbCommon.class_features import SUBCLASS_FEATURES, CLASS_FEATURE_INDEX
                proper_names = SUBCLASS_FEATURES.get((cname, sub), [])
            except ImportError:
                proper_names = []
                CLASS_FEATURE_INDEX = {}
            # Fall back to parsed summary names from CLASS_DICT
            if not proper_names:
                proper_names = self._get_subclass_feature_names(cname, sub, D)
            sub_feat_idx = 0  # pointer into proper names

            # VERIFIED, LEVEL-KEYED override: if this (class, subclass) has
            # been properly indexed in CLASS_FEATURE_INDEX with real,
            # sourced levels (not just a flat unordered list), use that
            # directly instead of the fragile placeholder-position-counting
            # below — the positional system silently misassigns levels any
            # time the number of generic "Archetype Feature"-style
            # placeholders in classes.py's per-level table doesn't exactly
            # match the length of SUBCLASS_FEATURES' flat list (see class_feature_index.py).
            _sub_index = CLASS_FEATURE_INDEX.get(cname, {}).get(sub)
            _has_verified_levels = isinstance(_sub_index, dict)
            if _has_verified_levels:
                for lvl in sorted(_sub_index):
                    if lvl > clvl:
                        break
                    for real_name in _sub_index[lvl]:
                        feats.append(f"[Lv {lvl}]  {sub}: {real_name}")

            if not _has_verified_levels:
                for lvl in range(1, clvl+1):
                    for fname in features.get(lvl, []):
                        is_sub_slot = any(kw in fname.lower() for kw in [
                            'subclass feature', 'archetype feature', 'domain feature',
                            'circle feature', 'sacred oath feature', 'primal path feature',
                            'order feature', 'college feature', 'ranger archetype feature',
                            'ranger archetype', '(subclass)', 'martial archetype',
                            'roguish archetype', 'sorcerous origin', 'otherworldly patron',
                            'divine domain', 'druid circle', 'monastic tradition',
                            'primal path', 'bardic college', 'arcane tradition',
                            'sacred oath', 'ranger conclave', 'alchemical homunculus',
                            'path feature',       # Barbarian Path Feature at Lv6/10/14
                            'sacred oath feature', # Paladin oath feature at Lv7/15/20
                            'bard college feature', # Bard college feature at Lv6/14
                            'ki feature',          # Monk ki features
                        ])
                        if is_sub_slot:
                            # Some slot markers are explicitly optional ("some
                            # domains grant a second 1st-level feature") — only
                            # treat them as real if this subclass's feature list
                            # is actually long enough to have that extra entry.
                            # Baseline is 5 (the normal single-1st-level-feature
                            # count for Cleric domains); domains with a genuine
                            # second 1st-level feature provide 6+ and so do
                            # consume this slot. Without this check, domains
                            # with only 5 features had every feature after 1st
                            # level shift one slot early, ending in a blank
                            # placeholder at the final level.
                            is_optional_slot = "second 1st-level feature" in fname.lower()
                            if is_optional_slot and len(proper_names) <= 5:
                                continue  # phantom slot — this domain doesn't have one
                            if sub and sub_feat_idx < len(proper_names):
                                real_name = proper_names[sub_feat_idx]
                                sub_feat_idx += 1
                                feats.append(f"[Lv {lvl}]  {sub}: {real_name}")
                            elif sub:
                                sub_feat_idx += 1
                                feats.append(f"[Lv {lvl}]  {sub} — Subclass Feature")
                            else:
                                feats.append(f"[Lv {lvl}]  {fname}")
                        else:
                            feats.append(f"[Lv {lvl}]  {fname}")

            # Add invocations
            invocs = self.char.get("eldritch_invocations", [])
            if cname == "Warlock" and invocs:
                feats.append(f"[Invocations]  " + ", ".join(
                    i.split("–")[0].strip() for i in invocs))

            # Totem Warrior: once the 3rd-level Totem Spirit choice has
            # actually been made, replace the generic "Totem Spirit" line
            # (which otherwise always lists all three options — Bear/Eagle/
            # Wolf — with no indication of which one this character has)
            # with the specific animal and its real effect text.
            if cname == "Barbarian" and "totem" in sub.lower():
                totem_pick = self.char.get("_choices", {}).get("totem_spirit_3", [])
                if totem_pick:
                    pick_text = totem_pick[0]
                    animal = pick_text.split("–")[0].split("-")[0].strip()
                    for _i, _f in enumerate(feats):
                        if _f.rstrip().endswith("Totem Spirit"):
                            feats[_i] = f"{_f} ({animal}) – {pick_text.split('–',1)[-1].strip() if '–' in pick_text else pick_text}"
                            break

            # Add metamagic
            metamagic = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
            if cname == "Sorcerer" and metamagic:
                feats.append(f"[Metamagic]  " + ", ".join(
                    m.split("–")[0].strip() for m in metamagic))

            # Add infusions
            infusions = self.char.get("artificer_infusions", [])
            if cname == "Artificer" and infusions:
                feats.append(f"[Infusions]  " + ", ".join(
                    i.split("–")[0].strip() for i in infusions))

            # Add battle master maneuvers
            maneuvers = self.char.get("battle_master_maneuvers", [])
            if cname == "Fighter" and "battle master" in sub.lower() and maneuvers:
                feats.append(f"[Maneuvers]  " + ", ".join(
                    m.split("–")[0].strip() for m in maneuvers))

            # Fix Indomitable display - show uses count clearly
            if cname == "Fighter":
                uses = 1 if clvl >= 9 else 0
                if clvl >= 13: uses = 2
                if clvl >= 17: uses = 3
                # Replace the plain feature text with a clearer version
                feats = [f if "Indomitable" not in f
                         else f"[Lv {([lvl for lvl in [9,13,17] if lvl<=clvl] or [0])[-1]}]  Indomitable — Reroll failed save ({uses}/Long Rest)"
                         for f in feats]

            if feats:
                self._add_feature_section(title, color, feats, badge_color=color)

        # Chosen feats
        feat_items = []
        for fname in self.char.get("feats",[]):
            fd = get_feat(fname)
            if fd:
                chosen_ab = self.char.get("_choices", {}).get(f"feat_ability_{fname.lower().replace(' ','_')}")
                prefix = f"{chosen_ab}-based — " if chosen_ab else ""
                summary = self._summarize_feature_text(fd.get('special', ''))
                feat_items.append(f"{fname}: {prefix}{summary}")
        if feat_items:
            self._add_feature_section("Feats", PURP2, feat_items, badge_color=PURP2)

        # Fighting Style is fully stored and mechanically wired (drives
        # real attack/damage bonuses), but is displayed here for visibility in the Features tab.
        fs_items = self.char.get("fighting_styles", [])
        if fs_items:
            self._add_feature_section("Fighting Style", TEAL2, list(fs_items), badge_color=TEAL2)

        # Battle Master maneuvers
        maneuvers = self.char.get("battle_master_maneuvers",[])
        if maneuvers:
            from dnd_app.core.calculator import get_superiority_die
            import re as _re_sd
            sd = get_superiority_die(self.char)
            maneuvers = [_re_sd.sub(r'\bSD\b', sd, m) for m in maneuvers]
            self._add_feature_section("Battle Master Maneuvers", AMBE2, maneuvers, badge_color=AMBE2)

        # Wild Magic surge table
        # Wild Magic: check if any Sorcerer has Wild Magic subclass stored
        # Both Wild Magic tables if multiclassing both
        wm_sorc = any(c.get("class")=="Sorcerer" and "wild magic" in c.get("subclass","").lower()
                      for c in self.char.get("classes",[]))
        wm_barb = any(c.get("class")=="Barbarian" and "wild magic" in c.get("subclass","").lower()
                      for c in self.char.get("classes",[]))
        # Also from _choices
        for cn,v in self.char.get("_choices",{}).items():
            if "subclass" in cn.lower() and isinstance(v,list) and v:
                val=str(v[0]).lower()
                if "wild magic" in val:
                    if "sorcerer" in cn.lower(): wm_sorc=True
                    if "barbarian" in cn.lower(): wm_barb=True
        if wm_sorc: self._add_wild_magic_section(barb=False)
        if wm_barb: self._add_wild_magic_section(barb=True)

        # Eldritch Invocations
        invocs = self.char.get("eldritch_invocations",[])
        if invocs:
            self._add_feature_section("Eldritch Invocations", PURP2, invocs, badge_color=PURP2)

        # Metamagic (only the options actually chosen — never the full pool)
        metamagic = self.char.get("_choices", {}).get("sorcerer_metamagic", [])
        if metamagic:
            self._add_feature_section("Metamagic", PURP2, metamagic, badge_color=PURP2)

        # Blood Curses Known (Blood Hunter) — only the ones actually chosen
        blood_curses = self.char.get("_choices", {}).get("blood_hunter_curses", [])
        if blood_curses:
            self._add_feature_section("Blood Curses Known", CRIM2, blood_curses, badge_color=CRIM2)

        # Mutagen Formulas Known (Blood Hunter, Order of the Mutant)
        mutagens = self.char.get("_choices", {}).get("blood_hunter_mutagens", [])
        if mutagens:
            self._add_feature_section("Mutagen Formulas Known", CRIM2, mutagens, badge_color=CRIM2)

        # Elemental Disciplines (Way of the Four Elements)
        disciplines = self.char.get("_choices", {}).get("four_elements_disciplines", [])
        if disciplines:
            self._add_feature_section("Elemental Disciplines", PURP2, disciplines, badge_color=PURP2)

        # Replicated Magic Items (Artificer): the real rule requires
        # explicitly learning each one as its own "Replicate Magic
        # Item" infusion pick, consuming an infusions-known slot — not
        # every item across every tier the character's level qualifies
        # for. Shows only the specific items the character has actually learned.
        from dnd_app.core.character import class_levels as _cls_lvls_repl
        art_lvl = _cls_lvls_repl(self.char).get("Artificer", 0)
        if art_lvl >= 2:
            from dnd_app.data.phb2014.classes import ARTIFICER_REPLICABLE_ITEMS
            all_replicable_names = {name for tier_items in ARTIFICER_REPLICABLE_ITEMS.values()
                                     for name, _ in tier_items}
            known_infusions = self.char.get("artificer_infusions", [])
            learned_replicated = [inf.split(" \u2013 ")[0].strip() for inf in known_infusions
                                   if inf.split(" \u2013 ")[0].strip() in all_replicable_names]
            if learned_replicated:
                attunement_lookup = {name: att for tier_items in ARTIFICER_REPLICABLE_ITEMS.values()
                                      for name, att in tier_items}
                display_items = [f"{name} (requires attunement)" if attunement_lookup.get(name) else name
                                 for name in learned_replicated]
                self._add_feature_section("Replicated Magic Items (learned)", TEAL2, display_items, badge_color=TEAL2)

                # ── Optional / Alternate Class Features (TCoE) ──────────────────────
        try:
            from dnd_app.data.phbCommon.class_features import OPTIONAL_CLASS_FEATURES as _OPT
        except ImportError:
            _OPT = {}
        _enabled = self.char.get("_choices",{}).get("optional_features",{})
        _rules = self.char.get("optional_rules", {})
        for _ce in self.char.get("classes",[]):
            _cn=_ce.get("class",""); _cl=_ce.get("level",1)
            _cls_opts=_OPT.get(_cn,{}); _items=[]
            for _ul,_fl in sorted(_cls_opts.items()):
                if _ul>_cl: continue
                for _f in _fl:
                    # Some optional features (Harness Divine Power) have
                    # a Settings-popup toggle; others (Martial
                    # Versatility, Deft Explorer, etc.) only have this
                    # per-feature one. Checks both, so a feature enabled
                    # through either mechanism is recognized consistently.
                    _rules_key = _f["name"].lower().replace(" ", "_")
                    if _enabled.get(_f["name"],False) or _rules.get(_rules_key, False):
                        _rep=_f.get("replaces")
                        _tag=f"(replaces {_rep})" if _rep else "(TCoE optional)"
                        _items.append(f"[Lv{_ul}]  {_f['name']} {_tag}")
            if _items:
                self._add_feature_section(f"✦ Optional — {_cn}",AMBER,_items,badge_color=AMBER)

        # ── DM-Granted Feats Browser ─────────────────────────────────────────
        from dnd_app.data.phbCommon.feats import ALL_FEATS, get_feat as _get_feat
        # Show any already-granted feats
        granted = self.char.get("dm_feats", [])
        if granted:
            feat_items = []
            for fname in granted:
                ft = _get_feat(fname)
                if ft:
                    src_tag = ft.get("source","")
                    pre = ft.get("prereq","")
                    desc = self._summarize_feature_text(ft.get("special",""), max_len=180)
                    feat_items.append(
                        f"<b>{fname}</b>  [{src_tag}]"
                        + (f"  <i>Req: {pre}</i>" if pre else "")
                        + (f"<br>{desc}" if desc else "")
                    )
                else:
                    feat_items.append(fname)
            self._add_feature_section("✦  DM-Granted Feats", AMBER, feat_items, badge_color=AMBER)

        # Show any already-granted DM rewards (Character Secrets / narrative
        # bonus features) — same pattern as DM-Granted Feats above, so a
        # granted reward actually appears on the sheet, not just as a
        # checkmark in the browser below.
        from dnd_app.data.phbCommon.dm_rewards import get_dm_reward as _get_dm_reward
        granted_rewards = self.char.get("dm_rewards", [])
        if granted_rewards:
            reward_items = []
            for rname in granted_rewards:
                rw = _get_dm_reward(rname)
                if rw:
                    pre = rw.get("prereq","")
                    # NOT _summarize_feature_text() here, unlike DM-Granted
                    # Feats above -- DM Rewards (Supernatural Gifts, Dark
                    # Gifts, Iconoclast's tiers, etc.) routinely run several
                    # paragraphs, and a max_len=180 summary truncated mid-
                    # sentence with no way to see the rest: the row label
                    # has no height cap (it just grows), and the right-click
                    # "Show Details" fallback reuses this same string when
                    # there's no separate FEATURE_DESCS lookup for a DM
                    # reward's custom name -- so a truncated summary here
                    # was truncated everywhere, with no path to the full
                    # text at all. _format_multi_para() renders the real
                    # paragraph breaks and bolds each trait's name, same as
                    # the feat browser's detail panel does for these.
                    desc = self._format_multi_para(rw.get("desc",""))
                    cat = rw.get("category",""); src = rw.get("source","")
                    tag = f"{cat} \u2014 {src}" if cat else ""
                    reward_items.append(
                        f"<b>{rname}</b>"
                        + (f"  <i>[{tag}]</i>" if tag else "")
                        + (f"  <i>Req: {pre}</i>" if pre else "")
                        + (f"<br>{desc}" if desc else "")
                    )
                else:
                    reward_items.append(rname)
            self._add_feature_section("✦  DM-Granted Bonus Features", AMBER, reward_items, badge_color=AMBER)

        # Feat browser card — always visible at bottom
        fb_card = QFrame()
        fb_card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1px solid {qa(AMBER,0x44)};border-radius:10px;}}")
        fb_cl = QVBoxLayout(fb_card)
        fb_cl.setContentsMargins(12, 10, 12, 10); fb_cl.setSpacing(6)

        # Header row
        fb_hdr = QHBoxLayout()
        fb_hdr.addWidget(_lbl("✦  BONUS FEATURE BROWSER  —  DM Rewards", AMBER, FS_SMALL, bold=True))
        fb_hdr.addStretch()
        fb_hdr.addWidget(_lbl("Double-click or click Add to grant a feat outside class progression",
                               TEXT3, FS_TINY, wrap=False))
        fb_cl.addLayout(fb_hdr)

        # Search + list row
        fb_body = QHBoxLayout(); fb_body.setSpacing(8)

        # Left: search + category filter + list
        fb_left = QVBoxLayout(); fb_left.setSpacing(4)
        fb_search_row = QHBoxLayout(); fb_search_row.setSpacing(6)
        fb_search = QLineEdit(); fb_search.setPlaceholderText("Search feats…")
        fb_search.setStyleSheet(
            f"QLineEdit{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;font-size:{FS_SMALL}px;}}"
            f"QLineEdit:focus{{border-color:{AMBER};}}")
        fb_search_row.addWidget(fb_search, 2)
        from dnd_app.data.phbCommon.dm_rewards import DM_REWARD_CATEGORIES
        fb_type_filter = QComboBox()
        fb_type_filter.addItems(DM_REWARD_CATEGORIES)
        fb_type_filter.setStyleSheet(
            f"QComboBox{{background:{SURF2};border:1px solid {BORDER2};border-radius:5px;"
            f"color:{TEXT};padding:4px 8px;font-size:{FS_SMALL}px;}}")
        fb_type_filter.setToolTip("Filter by feature type")
        fb_search_row.addWidget(fb_type_filter, 1)
        fb_left.addLayout(fb_search_row)

        fb_list = QListWidget()
        fb_list.setMaximumHeight(200)
        fb_list.setStyleSheet(
            f"QListWidget{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;"
            f"color:{TEXT};font-size:{FS_SMALL}px;}}"
            f"QListWidget::item{{padding:3px 8px;}}"
            f"QListWidget::item:selected{{background:{qa(AMBER,0x88)};color:white;}}"
            f"QListWidget::item:hover:!selected{{background:{SURF3};}}")
        from dnd_app.data.phbCommon.feature_tooltips import FEATURE_DESCS as _FEAT_DESCS
        for ft in ALL_FEATS:
            already = ft["name"] in self.char.get("dm_feats", [])
            item = QListWidgetItem(("✓ " if already else "") + ft["name"])
            item.setData(Qt.UserRole, ft["name"])
            item.setData(Qt.UserRole + 1, "feat")
            item.setData(Qt.UserRole + 2, "Feat")
            prereq = ft.get("prereq","")
            source = ft.get("source","")
            # Full detail from FEATURE_DESCS for the tooltip, falling back to
            # the feature-bar's short special[:250] snippet only if a feat
            # somehow has no dedicated tooltip entry.
            desc = _FEAT_DESCS.get(ft["name"]) or ft.get("special","")[:250]
            item.setToolTip(
                f"<b>{ft['name']}</b>  [{source}]"
                + (f"<br><i>Requires: {prereq}</i>" if prereq else "")
                + (f"<br>{desc}" if desc else ""))
            if already:
                item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(AMBER))
            fb_list.addItem(item)

        # DM Rewards ("Character Secrets" / narrative bonus features) — same
        # list, distinguished by a 🔮 marker and the second data role, since
        # these are a genuinely different kind of content (mostly narrative
        # hooks with occasional mechanical traits) than standard feats.
        from dnd_app.data.phbCommon.dm_rewards import ALL_DM_REWARDS
        for rw in ALL_DM_REWARDS:
            already_rw = rw["name"] in self.char.get("dm_rewards", [])
            item = QListWidgetItem(("✓ " if already_rw else "") + "🔮 " + rw["name"])
            item.setData(Qt.UserRole, rw["name"])
            item.setData(Qt.UserRole + 1, "dm_reward")
            item.setData(Qt.UserRole + 2, rw.get("category", ""))
            prereq = rw.get("prereq","")
            desc = self._summarize_feature_text(rw.get("desc",""), max_len=250).replace("\n\n", "<br><br>").replace("\n", "<br>")
            cat = rw.get("category",""); src = rw.get("source","")
            tag = f"{cat} \u2014 {src}" if cat else ""
            item.setToolTip(
                f"<b>{rw['name']}</b>" + (f"  <i>[{tag}]</i>" if tag else "")
                + (f"<br><i>Requires: {prereq}</i>" if prereq else "")
                + (f"<br>{desc}" if desc else ""))
            if already_rw:
                item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(AMBER))
            fb_list.addItem(item)

        def _filter_feats(_arg=None, lst=fb_list, search=fb_search, type_filter=fb_type_filter):
            text = search.text()
            selected_cat = type_filter.currentText()
            for i in range(lst.count()):
                it = lst.item(i)
                raw = it.data(Qt.UserRole) or it.text()
                cat = it.data(Qt.UserRole + 2) or ""
                text_ok = text.lower() in raw.lower()
                cat_ok = selected_cat == "All Types" or cat == selected_cat
                it.setHidden(not (text_ok and cat_ok))
        fb_search.textChanged.connect(_filter_feats)
        fb_type_filter.currentTextChanged.connect(_filter_feats)
        fb_left.addWidget(fb_list)
        fb_body.addLayout(fb_left, 3)

        # Right: info + add/remove buttons
        fb_right = QVBoxLayout(); fb_right.setSpacing(6)
        # Wrapped in a QScrollArea with a taller viewport rather than a
        # fixed-height QLabel, so a long entry (any DM Reward with more
        # than a couple sentences — Supernatural Gifts, Dark Gifts, and
        # Iconoclast's tiers routinely run several paragraphs) scrolls
        # rather than getting clipped with no way to reach the rest.
        fb_info = QLabel("Select a feat to see details.")
        fb_info.setWordWrap(True)
        fb_info.setStyleSheet(
            f"QLabel{{color:{TEXT2};font-size:{FS_SMALL}px;background:{SURF2};padding:8px;}}")
        fb_info.setMinimumWidth(220)
        fb_info_scroll = QScrollArea()
        fb_info_scroll.setWidget(fb_info)
        fb_info_scroll.setWidgetResizable(True)
        fb_info_scroll.setStyleSheet(
            f"QScrollArea{{background:{SURF2};border:1px solid {BORDER};border-radius:5px;}}")
        fb_info_scroll.setMinimumHeight(120); fb_info_scroll.setMaximumHeight(280)
        fb_right.addWidget(fb_info_scroll)

        def _on_feat_select(item, info=fb_info):
            if not item: return
            fname = item.data(Qt.UserRole) or item.text().lstrip("✓ ")
            item_type = item.data(Qt.UserRole + 1) or "feat"
            if item_type == "dm_reward":
                from dnd_app.data.phbCommon.dm_rewards import get_dm_reward as _gdr2
                rw = _gdr2(fname)
                if rw:
                    pre = rw.get("prereq","")
                    cat = rw.get("category",""); src = rw.get("source","")
                    tag = f"{cat} \u2014 {src}" if cat else ""
                    info.setText(
                        f"<b>{fname}</b>" + (f"  <i>[{tag}]</i>" if tag else "")
                        + (f"<br><span style='color:{AMBER};'>Requires: {pre}</span>" if pre else "")
                        + f"<br><br>{self._format_multi_para(rw.get('desc',''))}")
                return
            from dnd_app.data.phbCommon.feats import get_feat as _gf2
            from dnd_app.data.phbCommon.feature_tooltips import FEATURE_DESCS as _FEAT_DESCS2
            ft = _gf2(fname)
            if ft:
                pre = ft.get("prereq",""); src_tag=ft.get("source","")
                full_desc = _FEAT_DESCS2.get(fname) or ft.get('special','')
                info.setText(
                    f"<b>{fname}</b>  <i>[{src_tag}]</i>"
                    + (f"<br><span style='color:{AMBER};'>Requires: {pre}</span>" if pre else "")
                    + f"<br><br>{self._format_multi_para(full_desc)}")
        fb_list.currentItemChanged.connect(lambda cur,prev: _on_feat_select(cur))

        btn_add = _btn("＋  Grant Feat", AMBER, variant="danger", border_width=1,
                        font_size=FS_SMALL, padding="6px 12px")
        btn_rem = _btn("✕  Remove", CRIMSON, variant="danger", border_width=1,
                        bg_alpha=0x22, border_alpha=0x55, text_color=CRIM2,
                        hover_text="white", font_size=FS_SMALL, padding="6px 12px")

        def _grant_feat(lst=fb_list):
            item = lst.currentItem()
            if not item: return
            fname = item.data(Qt.UserRole) or item.text().lstrip("✓ ")
            item_type = item.data(Qt.UserRole + 1) or "feat"
            field = "dm_rewards" if item_type == "dm_reward" else "dm_feats"
            granted_list = self.char.setdefault(field, [])
            if fname not in granted_list:
                granted_list.append(fname)
                self._rebuild_features()
                self._mark_dirty()

        def _remove_feat(lst=fb_list):
            item = lst.currentItem()
            if not item: return
            fname = item.data(Qt.UserRole) or item.text().lstrip("✓ ")
            item_type = item.data(Qt.UserRole + 1) or "feat"
            field = "dm_rewards" if item_type == "dm_reward" else "dm_feats"
            granted_list = self.char.get(field, [])
            if fname in granted_list:
                granted_list.remove(fname)
                self._rebuild_features()
                self._mark_dirty()

        btn_add.clicked.connect(lambda _: _grant_feat())
        btn_rem.clicked.connect(lambda _: _remove_feat())
        fb_list.itemDoubleClicked.connect(lambda item: _grant_feat())

        fb_right.addWidget(btn_add)
        fb_right.addWidget(btn_rem)
        fb_right.addStretch()
        fb_body.addLayout(fb_right, 1)
        fb_cl.addLayout(fb_body)
        lay.addWidget(fb_card)

        lay.addStretch()

    @staticmethod
    def _inject_ability_modifier(item_str: str, char: dict) -> str:
        """Resolve '+STAT' placeholders — see calculator.resolve_stat_placeholders
        for the exact rules (shared with the level-up preview panel so
        every surface reads the same way)."""
        from dnd_app.core.calculator import resolve_stat_placeholders
        return resolve_stat_placeholders(item_str, char)

    @staticmethod
    def _summarize_feature_text(text: str, max_len: int = 110) -> str:
        """Short summary for a Features tab row label — the full text
        stays available via the existing tooltip/right-click detail
        view, so this is purely about not dumping an entire paragraph
        of rules text inline. Strips a leading boilerplate ASI clause
        (e.g. "+1 INT/WIS/CHA (max 20)." — present in most 2024-style
        feats and not itself the feature's actual unique mechanic),
        then truncates the remainder at a clean word boundary."""
        import re
        t = text.strip()
        # Strip a leading "+N ABILITY[/ABILITY...] (max 20)." clause.
        t = re.sub(r'^\+\d+\s+[A-Z]{3}(?:/[A-Z]{3})*\s*\(max\s*20\)\.\s*', '', t)
        if len(t) <= max_len:
            return t
        cut = t[:max_len]
        last_space = cut.rfind(' ')
        if last_space > max_len * 0.6:
            cut = cut[:last_space]
        return cut.rstrip('.,;: ') + '…'

    @staticmethod
    def _format_multi_para(text: str) -> str:
        """Format a long, multi-ability description (DM rewards like
        Supernatural Gifts, Dark Gifts, Iconoclast's tiers, etc.) for
        an HTML-rendered popup. Handles two things Qt's HTML rendering
        won't do on its own: (1) the source text has real '\\n\\n'
        paragraph breaks, but plain newlines are silently collapsed,
        producing one unreadable wall of text; (2) each distinct
        ability starts with "Trait Name. description..." (markdown bold
        flattened to plain text during parsing) — these are re-bolded
        so each ability reads as its own clearly separated block
        instead of blending into running prose."""
        import re
        if not text:
            return ""
        paras = [p.strip() for p in text.split('\n\n') if p.strip()]
        out_paras = []
        for p in paras:
            # "Trait Name. rest of description" at the start of a
            # paragraph — re-bold just the name, not the whole
            # paragraph. Matches a short (1-6 word), capitalized
            # phrase followed by a period and a space.
            m = re.match(r'^([A-Z][A-Za-z\'\u2019 ]{1,50}?)\.\s+(.*)$', p, re.DOTALL)
            if m and len(m.group(1).split()) <= 6:
                p = f"<b>{m.group(1)}.</b> {m.group(2)}"
            # Some entries embed markdown tables (pipe-delimited rows)
            # as raw text with single \n between rows; each row would
            # otherwise collapse into one unreadable run in the
            # rendered HTML. Converts any remaining single newlines to
            # real line breaks too, after the paragraph-level bolding above already ran.
            p = p.replace('\n', '<br>')
            out_paras.append(p)
        return '<br><br>'.join(out_paras)

    @staticmethod
    def _break_long_tooltip(text: str, chunk_chars: int = 220) -> str:
        """For genuinely run-on text with no \\n\\n breaks at all in the
        source (unlike _format_multi_para's DM Reward entries) — some
        feat descriptions run over 1300 characters as a single,
        unbroken block. Even though Qt's HTML tooltip wrapping handles
        the width correctly, a very long, unstructured block could
        still be clipped by a tooltip's maximum render height. Breaks
        into readable chunks at real sentence boundaries (never mid-
        sentence), each chunk close to but not exceeding chunk_chars."""
        import re
        if not text or len(text) <= chunk_chars:
            return text
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks, current = [], ""
        for s in sentences:
            if current and len(current) + len(s) + 1 > chunk_chars:
                chunks.append(current)
                current = s
            else:
                current = f"{current} {s}".strip()
        if current:
            chunks.append(current)
        return '<br><br>'.join(chunks)

    def _add_feature_section(self, title, color, items, badge_color=None):
        from dnd_app.data.phbCommon.feature_ui_interactions import FEATURE_CONFIG
        try:
            from dnd_app.data.phbCommon.feature_tooltips import FEATURE_DESCS
        except ImportError:
            FEATURE_DESCS = {}
        # Resolve '+STAT' placeholders into real numbers for every item —
        # resolve_stat_placeholders() is a no-op on text with no such
        # placeholder, so it's safe to call unconditionally. (The old
        # pre-filter here only matched "CHA modifier"-style phrasing or a
        # bare "CHA/" pattern, missing plenty of real cases like
        # "1+CHA/LR" shorthand, which never got resolved as a result.)
        items = list(dict.fromkeys(items))   # dedupe (race vs ancestry overlap)
        items = [self._inject_ability_modifier(it, self.char) for it in items]
        grp = QGroupBox(title)
        grp.setStyleSheet(
            f"QGroupBox{{background:{SURF};border:1px solid {qa(color,0x55)};border-radius:10px;"
            f"margin-top:16px;padding:10px 10px 10px 10px;}}"
            f"QGroupBox::title{{left:12px;top:0;background:{SURF};color:{color};"
            f"font-size:{FS_SMALL}px;font-weight:700;letter-spacing:1px;padding:0 6px;}}"
        )
        gl = QVBoxLayout(grp); gl.setSpacing(6)
        for item in items:
            row = QFrame()
            row.setStyleSheet(
                f"QFrame{{background:{SURF2};border:1px solid {BORDER};border-radius:7px;}}"
                f"QFrame:hover{{background:{SURF3};border-color:{BORDER2};}}")
            row.setCursor(Qt.WhatsThisCursor)
            rl = QHBoxLayout(row); rl.setContentsMargins(10,8,10,8); rl.setSpacing(8)
            feat_lbl = _lbl(item, TEXT, FS_BODY, wrap=True)
            feat_lbl.setMinimumHeight(32)
            rl.addWidget(feat_lbl)

            # ── Tooltip lookup (multiple strategies) ──────────────────────────
            _bracket = item.strip()
            if _bracket.startswith("[") and "]" in _bracket:
                raw = _bracket[_bracket.index("]")+1:].strip()
            else:
                raw = _bracket
            raw_no_paren = raw.split("(")[0].strip()
            raw_no_dash = raw.split("\u2014")[0].strip() if "\u2014" in raw else raw
            raw_no_dash_paren = raw_no_dash.split("(")[0].strip()
            after_colon = raw.split(":", 1)[1].strip() if ":" in raw else ""
            after_colon_no_paren = after_colon.split("(")[0].strip() if after_colon else ""
            # "Chosen Feats" format is "FeatName: special text…" — the name
            # comes BEFORE the colon here, the opposite of after_colon above
            # (which is for a different, "Label: Name" style of item).
            before_colon = raw.split(":", 1)[0].strip() if ":" in raw else ""
            # DM-Granted Feats (and similar) format as "<b>Name</b>  [source]
            # <i>Req: ...</i><br>desc…" — the name is wrapped in bold tags
            # rather than prefixed with a leading bracket, so none of the
            # candidates above would ever match it without this.
            bold_name = ""
            if "<b>" in item and "</b>" in item:
                bold_name = item.split("<b>",1)[1].split("</b>",1)[0].strip()
            def _lu(c):
                if not c: return ""
                return (FEATURE_DESCS.get(c) or
                        (FEATURE_CONFIG.get(c) or {}).get("desc","") or
                        (FEATURE_CONFIG.get(c) or {}).get("note","") or "")
            tip = ""
            # Unarmored Defense needs special handling: the generic
            # FEATURE_DESCS entry describes BOTH the Barbarian and Monk
            # versions in one sentence (confusing when you only have one
            # of them), and a bare formula ("10 + DEX + CON") isn't as
            # useful as showing the character's actual current AC total
            # first, with the breakdown of what it's made of underneath.
            if raw_no_paren == "Unarmored Defense":
                from dnd_app.core.calculator import get_ac, get_ac_breakdown
                total = get_ac(self.char)
                parts = [(lbl, val) for lbl, val in get_ac_breakdown(self.char)
                         if "Unarmored Defense" in lbl or "modifier" in lbl.lower()]
                if parts:
                    breakdown_str = " + ".join(f"{v:+d} ({lbl})" if i else f"{v} ({lbl})"
                                                for i, (lbl, v) in enumerate(parts))
                    tip = f"Total: AC {total}<br>{breakdown_str}"
            if not tip:
                for _cand in [bold_name, raw, raw_no_paren, raw_no_dash, raw_no_dash_paren, before_colon, after_colon, after_colon_no_paren]:
                    _d = _lu(_cand)
                    if _d: tip = _d; break
            if not tip and " + " in (after_colon or raw_no_paren):
                _src = after_colon if after_colon else raw_no_paren
                _parts = [p.strip().split("(")[0].strip() for p in _src.split(" + ")]
                _pds = [f"<b>{p}</b><br>{_lu(p)}" for p in _parts if _lu(p)]
                if _pds: tip = "<br><br>".join(_pds)
            # NOTE: intentionally no "len(item) > 80 → tip = raw" fallback here.
            # Background/race/subrace items already show their FULL description
            # inline in the row label; repeating it verbatim in the tooltip is
            # just noise. Only show a tooltip when there's a genuinely
            # different, shorter lookup via FEATURE_DESCS.
            if tip:
                display_name = after_colon_no_paren or raw_no_paren
                tip_formatted = self._break_long_tooltip(tip)
                row.setToolTip(f"<b>{display_name}</b><br><br>{tip_formatted}")
                row.setToolTipDuration(15000)
                feat_lbl.setToolTip(f"<b>{display_name}</b><br><br>{tip_formatted}")
                feat_lbl.setToolTipDuration(15000)

            # ── Right-click context menu ──────────────────────────────────────
            # _tip is deliberately empty for race/subrace/background items
            # (their full text is already inline, so a hover tooltip would
            # just repeat it) — but that meant right-click found nothing to
            # show either, since the menu action was only ever added "if
            # _tip". Fall back to the item's own text so right-click always
            # has something to display, for every feature row without
            # exception, while leaving the hover-tooltip behavior alone.
            def _show_detail_menu(ev, _item=item, _tip=(tip or item), _raw=raw_no_paren, _row=row):
                from PySide6.QtWidgets import QMenu
                menu = QMenu(_row)
                act = menu.addAction(f"📖  Show Details: {_raw[:40]}")
                act.triggered.connect(lambda: QMessageBox.information(
                    _row, _raw,
                    f"<b>{_raw}</b><br><br>{_tip}",
                ))
                menu.exec(ev.globalPos())
            row.mousePressEvent = lambda ev, f=_show_detail_menu: (
                f(ev) if ev.button() == Qt.RightButton else None
            )

            gl.addWidget(row)
        self._feat_tab_lay.insertWidget(self._feat_tab_lay.count()-1, grp)

    def _add_wild_magic_section(self, barb: bool = False):
        from dnd_app.data.phb2014.classes import WILD_MAGIC_SURGE_TABLE, WILD_MAGIC_BARBARIAN_TABLE
        # Determine which table to use: Barbarian=d8, Sorcerer=d100
        is_barb_wm = barb
        if is_barb_wm:
            table_data = [(i+1, i+1, eff) for i, (_, eff) in enumerate(WILD_MAGIC_BARBARIAN_TABLE)]
            title = "Wild Magic Surge Table  (Barbarian — roll d8 when you enter your rage)"
            die_label = "🎲  Roll Wild Magic Surge (d8)"
            die_max = 8
        else:
            table_data = WILD_MAGIC_SURGE_TABLE
            title = "Wild Magic Surge Table  (Sorcerer — roll d100 after casting a spell)"
            die_label = "🎲  Roll Wild Magic Surge (d100)"
            die_max = 100

        grp = QGroupBox(title)
        grp.setStyleSheet(f"QGroupBox{{background:{SURF};border:1px solid {qa(PURP2,0x55)};border-radius:10px;margin-top:16px;padding:10px;}}QGroupBox::title{{left:12px;top:0;background:{SURF};color:{PURP2};font-size:{FS_SMALL}px;font-weight:700;padding:0 6px;}}")
        gl = QVBoxLayout(grp)
        roll_row = QHBoxLayout()
        roll_btn = pill_btn(die_label, PURPLE, hover=PURP2)
        self._wm_result_lbl = _lbl("—", PURP2, FS_BODY, bold=True, wrap=True)
        roll_row.addWidget(roll_btn); roll_row.addWidget(self._wm_result_lbl, 1); roll_row.addStretch()
        gl.addLayout(roll_row)
        table = QTableWidget(len(table_data), 2)
        table.setHorizontalHeaderLabels(["Roll","Effect"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setMaximumHeight(220)
        for i,(lo,hi,eff) in enumerate(table_data):
            table.setItem(i,0,QTableWidgetItem(str(lo) if lo==hi else f"{lo:02d}–{hi:02d}"))
            item = QTableWidgetItem(eff); item.setToolTip(eff)
            table.setItem(i,1,item)
        def _roll(_=None, _max=die_max, _tbl=table_data, _lbl=self._wm_result_lbl):
            r = random.randint(1, _max)
            for i,(lo,hi,eff) in enumerate(_tbl):
                if lo<=r<=hi:
                    table.selectRow(i); table.scrollToItem(table.item(i,0))
                    _lbl.setText(f"Roll {r}: {eff[:120]}{'…' if len(eff)>120 else ''}")
                    break
        roll_btn.clicked.connect(_roll)
        gl.addWidget(table)
        self._feat_tab_lay.insertWidget(self._feat_tab_lay.count()-1, grp)

    # ══ TAB 6: TRAITS & NOTES ══════════════════════════════════════════════════
