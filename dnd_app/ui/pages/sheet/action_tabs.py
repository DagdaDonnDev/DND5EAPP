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
from dnd_app.ui.action_abilities import build_action_abilities
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


class ActionTabsMixin:
    def _build_resource_rows(self, bl):
        """
        Populate the top of the 'Other' tab with live resource pools: class
        features tracked in char['resources'] (Ki, Lay on Hands, Channel
        Divinity, Sorcery Points, Healing Light, etc.), magic item charges,
        and a few feat-granted pools that aren't otherwise tracked.
        """
        def _pool_row(name, current, maximum, reset_label, tooltip_extra="",
                      res_key=None, is_item=False, item_name=None, toggle_effect=None):
            """Interactive resource row with a spinbox to track uses.
            If toggle_effect is given (an EFFECT_TABLE key), also render an
            on/off toggle next to the counter that adds/removes that effect
            from char['active_effects'] and applies its real mechanical
            changes (AC, resistances, combat-tab attack row) immediately —
            rather than just being a passive usage tracker."""
            row = QWidget()
            pct = (current / maximum) if maximum else 0
            if pct > 0.5: bar_color = TEAL2
            elif pct > 0: bar_color = AMBER
            else: bar_color = CRIM2
            row.setStyleSheet(
                f"QWidget{{background:{qa(bar_color,0x14)};border:1px solid {qa(bar_color,0x44)};"
                f"border-radius:6px;margin:1px;}}")
            rl = QHBoxLayout(row); rl.setContentsMargins(8,5,8,5); rl.setSpacing(6)

            name_l = _lbl(name, TEXT, FS_TINY, bold=True, wrap=False)
            reset_l = _lbl(reset_label, TEXT3, FS_TINY-1, wrap=False)
            reset_l.setFixedWidth(70)  # fits "Short Rest"/"Long Rest" (the longest values) without clipping
            tip = f"{name}: {current}/{maximum}\nRecharges: {reset_label}"
            if tooltip_extra: tip += f"\n{tooltip_extra}"

            # Spinbox for current value — editable in-place
            sp = QSpinBox(); sp.setRange(0, maximum); sp.setValue(current)
            sp.setFixedWidth(48); sp.setAlignment(Qt.AlignCenter)
            sp.setToolTip(f"Current uses of {name}")
            sp.setStyleSheet(
                f"QSpinBox{{background:{SURF2};border:1px solid {qa(bar_color,0x66)};"
                f"border-radius:4px;color:{bar_color};font-size:{FS_TINY}px;"
                f"font-weight:700;padding:1px;}}")
            max_l = _lbl(f"/{maximum}", TEXT3, FS_TINY, wrap=False)

            def _save_res(val, _key=res_key, _iname=item_name, _is_item=is_item):
                if _is_item and _iname:
                    ic = self.char.setdefault("item_charges",{})
                    ic.setdefault(_iname,{})["current"] = val
                elif _key:
                    for res in self.char.get("resources",[]):
                        if res.get("key") == _key or res.get("name") == _key:
                            res["current"] = val; break
                self._mark_dirty()
            sp.valueChanged.connect(_save_res)
            self._resource_widgets.append(row)

            # −/+ buttons for quick spend/restore
            minus = QPushButton("−"); minus.setFixedSize(30,30)
            plus  = QPushButton("+"); plus.setFixedSize(30,30)
            btn_ss = _btn("", bar_color, variant="danger", radius=5, border_width=1,
                          bg_alpha=0x22, border_alpha=0x55, hover_text="white",
                          font_size=16, padding="0px").styleSheet()
            minus.setStyleSheet(btn_ss); plus.setStyleSheet(btn_ss)
            def _on_minus_click(checked=False, _key=res_key):
                # Earth Genasi Blade Ward needs the same gate as real
                # spell-casting — even though Blade Ward is a cantrip,
                # spending this use is "casting a spell with a bonus
                # action," which can be blocked if a leveled spell was
                # already cast via the regular Action that turn.
                if _key == "earth_genasi_blade_ward":
                    if not self._check_bonus_action_spell_rule(True, "Bonus Action"):
                        self._toast("✖ Can't cast Blade Ward via Bonus Action — you've already "
                                    "cast a non-cantrip spell via your Action this turn")
                        return
                    self._bonus_action_spell_is_cantrip = True
                sp.setValue(max(0, sp.value()-1))
                # Harness Divine Power (Cleric/Paladin, TCE optional
                # feature): this feature both has its own limited uses
                # AND separately consumes a normal Channel Divinity
                # charge each time it's used — not two independent
                # pools. Only this one resource needs the linked decrement.
                if _key == "harness_divine_power":
                    for cd_key in ("channel_divinity", "channel_div"):
                        for res in self.char.get("resources", []):
                            if res.get("key") == cd_key:
                                res["current"] = max(0, res.get("current", 0) - 1)
                                self._mark_dirty()
                                QTimer.singleShot(0, self.ctrl.refresh)
                # Action Surge grants an extra action for the current
                # turn per the real rule, tied into the turn-economy
                # system here rather than existing only as a spendable resource.
                if _key == "action_surge":
                    self.char["_action_surge_used_this_turn"] = True
                    self._toast("⚡ Action Surge: gained an extra action this turn")
                    self._apply_turn_state()
            minus.clicked.connect(_on_minus_click)
            plus.clicked.connect(lambda: sp.setValue(min(maximum, sp.value()+1)))

            for w in (row, name_l): w.setToolTip(tip)
            rl.addWidget(name_l, 1)
            if toggle_effect:
                is_active = toggle_effect in self.char.get("active_effects", [])
                tgl = QCheckBox("Active")
                tgl.setChecked(is_active)
                tgl.setStyleSheet(
                    f"QCheckBox{{color:{CRIM2 if is_active else TEXT3};font-size:{FS_TINY}px;font-weight:700;}}"
                    f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                    f"border:2px solid {CRIM2};background:{CRIM2 if is_active else 'transparent'};}}")
                tgl.setToolTip(f"Toggle {name} on/off — applies its AC bonus, "
                               f"damage resistance/immunity, and any other real "
                               f"mechanical effects (like Hybrid Transformation's "
                               f"unarmed-strike row) immediately.")
                def _on_toggle(state, _name=toggle_effect):
                    active = self.char.setdefault("active_effects", [])
                    on = bool(state)
                    if on and _name not in active:
                        active.append(_name)
                    elif not on and _name in active:
                        active.remove(_name)
                    self._mark_dirty()
                    # Deferred: rebuilding the Other tab (which recreates
                    # this very checkbox) must NOT happen synchronously
                    # inside its own stateChanged handler — doing so while
                    # the signal is still being emitted crashes Qt. Let this
                    # callback fully return first, then refresh. The actual
                    # resistance add/remove is handled centrally inside
                    # update_all() (called by ctrl.refresh()), keyed off
                    # active_effects — not done here — so it survives every
                    # future refresh instead of being wiped by the magic
                    # item recompute that resets damage_resistances.
                    QTimer.singleShot(0, self.ctrl.refresh)
                tgl.stateChanged.connect(_on_toggle)
                rl.addWidget(tgl)
            rl.addWidget(minus); rl.addWidget(sp); rl.addWidget(max_l); rl.addWidget(plus)
            rl.addWidget(reset_l)
            bl.insertWidget(bl.count()-1, row)

        has_any = False

        # ── Class/subclass resource pools (Ki, Lay on Hands, Sorcery Points...) ─
        RESET_LABEL = {'SR':'Short Rest','LR':'Long Rest','SR/LR':'SR or LR',
                       'sr':'Short Rest','lr':'Long Rest'}
        seen_keys = set()
        for r in self.char.get('resources', []):
            if r.get('track') not in ('current_max','uses','pool'):
                continue
            key = r.get('key','') + r.get('name','')
            if key in seen_keys:
                continue
            seen_keys.add(key)
            current = r.get('current', 0)
            maximum = r.get('current_max', 0)
            if not isinstance(maximum, int) or maximum <= 0:
                continue
            reset_label = RESET_LABEL.get(r.get('reset',''), r.get('reset','—'))
            TOGGLE_KEY_MAP = {
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
            _pool_row(r['name'], current, maximum, reset_label,
                      f"From: {r.get('source_class','')}",
                      res_key=r.get('key') or r.get('name'),
                      toggle_effect=TOGGLE_KEY_MAP.get(r.get('key')))
            has_any = True

        # Lucky, Martial Adept, and Metamagic Adept are now properly wired
        # through the standard feat-resource system in calculator.py
        # (FEAT_FIXED_USES_RESOURCES) — the FEAT_RESOURCES dict that used
        # to live here has been removed: it hardcoded current=maximum on
        # every refresh, so editing its spinbox never actually persisted
        # anywhere, since these 3 feats had no real char["resources"] entry
        # for _save_res() to find and update.

        # ── Magic item charges ──────────────────────────────────────────────────
        for iname, charge_data in self.char.get('item_charges', {}).items():
            current = charge_data.get('current', 0)
            maximum = charge_data.get('max', 0)
            if maximum <= 0:
                continue
            recharge = charge_data.get('recharge', 'dawn')
            reset_label = {'dawn':'Dawn','dusk':'Dusk'}.get(recharge, recharge.title())
            _pool_row(f"✦ {iname}", current, maximum, reset_label,
                      f"Magic item charges, from: {iname}",
                      is_item=True, item_name=iname)
            has_any = True

        # ── Hit Dice tracker (uses char["hit_dice"] — the canonical model) ─────
        hd_model = self.char.get("hit_dice", {})
        if hd_model:
            hd_hdr = _lbl("HIT DICE  (spend to heal: roll + CON)", GOLD, FS_TINY, bold=True, wrap=False)
            bl.insertWidget(bl.count()-1, hd_hdr)
            con_mod = ability_mod(self.char, "CON")
            for die_key, hd_data in sorted(hd_model.items()):
                total = hd_data.get("total", 0)
                remaining = hd_data.get("remaining", 0)
                if total <= 0: continue
                pct = remaining/total if total else 0
                bar_color = GREEN2 if pct > 0.5 else (AMBER if pct > 0 else CRIM2)
                hd_row = QWidget()
                hd_row.setStyleSheet(f"QWidget{{background:{qa(bar_color,0x14)};border:1px solid "
                                     f"{qa(bar_color,0x44)};border-radius:6px;margin:1px;}}")
                hr = QHBoxLayout(hd_row); hr.setContentsMargins(8,4,8,4); hr.setSpacing(8)
                hr.addWidget(_lbl(f"Hit Dice ({die_key})", TEXT, FS_TINY, bold=True, wrap=False), 1)
                hr.addWidget(_lbl(f"{remaining}/{total}", bar_color, FS_TINY, bold=True, wrap=False))
                spend = QPushButton(f"🎲 Spend")
                spend.setFixedSize(64, 24)
                spend.setEnabled(remaining > 0)
                spend.setToolTip(f"Roll 1{die_key} + {con_mod} CON and heal that much")
                spend.setStyleSheet(
                    _btn("", bar_color, variant="danger", radius=4, border_width=1,
                         bg_alpha=0x22, hover_text="white", font_size=FS_TINY,
                         padding="0px").styleSheet()
                    + f"QPushButton:disabled{{color:{TEXT3};border-color:{BORDER};}}")
                spend.clicked.connect(lambda checked=False, k=die_key: self._spend_hit_die(k))
                hr.addWidget(spend)
                bl.insertWidget(bl.count()-1, hd_row)
            has_any = True

        if has_any:
            sep = _lbl("— Passive Features —", TEXT3, FS_TINY, bold=True, wrap=False, align=Qt.AlignCenter)
            bl.insertWidget(bl.count()-1, sep)

    def _refresh_action_tabs(self):
        """Rebuild the action economy tabs from current character state."""
        if not hasattr(self, '_action_bucket_widgets'):
            return
        buckets = build_action_abilities(self.char)

        for bucket_name, (bw, bl) in self._action_bucket_widgets.items():
            # Clear existing rows — items 0 and 1 are the permanent
            # filter row and level-filter row and must be preserved,
            # along with the stretch at the end.
            while bl.count() > 3:
                item = bl.takeAt(2)
                if item.widget():
                    item.widget().setParent(None)

            # ── "Other" tab gets a Resources & Charges section up top ────────
            if bucket_name == 'Passive':
                self._build_resource_rows(bl)

            CLASS_COLORS = {
                'Universal': TEXT3, 'Fighter': TEAL2, 'Barbarian': CRIM2,
                'Rogue': IND2, 'Monk': TEAL2, 'Paladin': GOLD, 'Ranger': GREEN2,
                'Druid': GREEN2, 'Bard': PURP2, 'Wizard': PURP2, 'Cleric': GOLD,
                'Sorcerer': CRIM2, 'Warlock': IND2, 'Artificer': TEAL2,
                'Blood Hunter': CRIM2,
            }
            rows = buckets.get(bucket_name, [])

            # Conditional filter visibility: only show the chooser for
            # THIS bucket if more than one distinct category is
            # actually present.
            present_cats = {self._classify_action_entry(e) for e in rows}
            self._action_filter_rows[bucket_name].setVisible(len(present_cats) > 1)

            cat_filter = self._action_cat_filters.get(bucket_name, "All")
            if cat_filter != "All":
                rows = [e for e in rows if self._classify_action_entry(e) == cat_filter]
                if cat_filter == "Spell":
                    lvl_filter = self._action_spell_level_filters.get(bucket_name, "All")
                    if lvl_filter != "All":
                        def _entry_level_tag(e):
                            src = e[2] if len(e) > 2 else ""
                            return src  # spell entries already tag source as "Cantrip"/"Spell L1" etc.
                        target = "Cantrip" if lvl_filter == "Cantrip" else f"Spell {lvl_filter}"
                        rows = [e for e in rows if _entry_level_tag(e) == target]
            self._bucket_use_btns = getattr(self, '_bucket_use_btns', {})
            self._bucket_use_btns[bucket_name] = []

            # ── Laptop-friendly 2-column card grid ───────────────────────────
            grid_host = QWidget(); grid_host.setStyleSheet("background:transparent;")
            grid = QGridLayout(grid_host)
            grid.setContentsMargins(0,0,0,0)
            grid.setHorizontalSpacing(8); grid.setVerticalSpacing(6)
            grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)

            for idx, entry in enumerate(rows):
                display, desc, source = entry[0], entry[1], entry[2]
                spell = entry[3] if len(entry) > 3 else None
                is_spell = spell is not None
                if not is_spell:
                    # Spell descriptions come straight from spell data and
                    # don't use these "+STAT" shorthands; class/race/item
                    # feature text does, and was never resolved anywhere
                    # outside the Features tab — combat cards showed the
                    # raw placeholder the whole time.
                    desc = self._inject_ability_modifier(desc, self.char)
                src_color = (IND2 if is_spell
                             else CLASS_COLORS.get(source, AMBE2))
                is_class = source in CLASS_COLORS
                tip_head = (f"<b>{display}</b>" if is_class or is_spell
                            else f"<b>{display}</b><br>Magic item: {source}")
                tooltip_text = f"{tip_head}<br><br>{desc}".replace('\n','<br>')

                card = QFrame()
                card.setCursor(Qt.PointingHandCursor)
                card.setStyleSheet(
                    f"QFrame{{background:{qa(src_color,0x11)};border:1px solid {qa(src_color,0x33)};"
                    f"border-radius:8px;}}"
                    f"QFrame:hover{{background:{qa(src_color,0x1e)};border-color:{qa(src_color,0x77)};}}")
                cl = QHBoxLayout(card); cl.setContentsMargins(10,7,8,7); cl.setSpacing(8)

                src_badge = _lbl(source[:9], src_color, FS_TINY, bold=True, wrap=False)
                src_badge.setFixedWidth(60); src_badge.setAlignment(Qt.AlignCenter)
                src_badge.setStyleSheet(
                    f"background:{qa(src_color,0x22)};border:1px solid {qa(src_color,0x55)};"
                    f"border-radius:4px;color:{src_color};font-size:{FS_TINY}px;"
                    f"font-weight:700;padding:2px 3px;")

                text_col = QVBoxLayout(); text_col.setSpacing(1)
                lbl_name = _lbl(display, GOLD, FS_SMALL, bold=True, wrap=False)
                lbl_desc = _lbl(desc[:170] + ("…" if len(desc)>170 else ""),
                                TEXT2, FS_TINY, wrap=True)
                text_col.addWidget(lbl_name); text_col.addWidget(lbl_desc)

                # ── Cast / Use button ─────────────────────────────────────────
                btn_txt = "Cast" if is_spell else "Use"
                use_btn = QPushButton(btn_txt)
                use_btn.setFixedSize(46, 26)
                use_btn.setStyleSheet(
                    _btn("", src_color, variant="danger", radius=5, border_width=1,
                         hover_text="white", font_size=FS_TINY, padding="0px").styleSheet())
                use_btn.setToolTip(tooltip_text)

                if is_spell:
                    def _cast_from_card(checked=False, _sp=spell):
                        self._cast_spell(_sp)
                    use_btn.clicked.connect(_cast_from_card)
                else:
                    def _use_ability(checked=False, _display=display,
                                     _desc=desc, _src=source, _b=bucket_name):
                        key = _display.split('(')[0].strip().lower()
                        # Wild Shape blocks features that need a holy
                        # symbol/spellcasting focus in hand and/or speech —
                        # the same standard as spellcasting itself, since
                        # neither is physically possible in most beast
                        # forms. Everything else is allowed by default,
                        # per the real rule ("retain the benefit of any
                        # features... if the new form is physically
                        # capable of doing so") — Rage, Unarmored Defense,
                        # Danger Sense, Second Wind, etc. all work fine in
                        # beast form and are deliberately NOT in this list.
                        if self.char.get("_wildshape_active") and any(
                                b in key for b in WILDSHAPE_BLOCKED_FEATURES):
                            self._toast(f"\U0001f43e Can't use {_display} while Wild Shaped — "
                                        f"your beast form can't perform what it requires "
                                        f"(a held item, speech, an unarmed strike, or casting)")
                            return
                        # Wild Shape: unlike a flat toggle (Rage, Reckless
                        # Attack), actually using this requires picking a
                        # beast — something only the dedicated card (top of
                        # this same Combat tab) can do. This generic Use
                        # button used to fall through to the resource
                        # fallback below, which would silently spend a use
                        # and do nothing else: no beast chosen, no HP pool
                        # switched, _wildshape_active left untouched — a
                        # spent charge with no visible effect, which is
                        # exactly what looked like "the counter doesn't
                        # decrement" (a use WAS spent, just with nothing to
                        # show for it). Redirects instead of guessing a beast.
                        if key == "wild shape":
                            self._toast("🐾 Use the Wild Shape card at the top of this tab to "
                                        "pick a beast and transform")
                            return
                        # Reckless Attack: a real toggle rather than a
                        # one-off reminder. Doesn't consume a turn slot —
                        # it modifies an attack you're already making, not
                        # a separate action — and stays on until manually
                        # toggled off or cleared by the New Turn button.
                        if key == "reckless attack":
                            fx = self.char.setdefault("active_effects", [])
                            if "Reckless Attack" in fx:
                                fx.remove("Reckless Attack")
                                self._toast("⚔ Reckless Attack: OFF")
                            else:
                                fx.append("Reckless Attack")
                                msg = ("⚔ Reckless Attack: ON — advantage on your melee "
                                       "attacks, but attacks against you also have advantage")
                                # Reckless Abandon (Battlerager, 2nd level):
                                # gain temp HP equal to CON mod (min 1) when
                                # you use Reckless Attack while wearing
                                # battlerager armor. Can't verify the armor
                                # specifically (not a tracked item), gated
                                # on the subclass alone like Armor Spikes.
                                from dnd_app.core.character import subclasses, class_levels
                                barb_sub = subclasses(self.char).get("Barbarian", "")
                                if (class_levels(self.char).get("Barbarian", 0) >= 2
                                        and "battlerager" in barb_sub.lower()):
                                    con_mod = max(1, ability_mod(self.char, "CON"))
                                    cur_temp = self.char.get("temp_hp", 0)
                                    if con_mod > cur_temp:
                                        self.char["temp_hp"] = con_mod
                                    msg += f"\n🛡 Reckless Abandon: {con_mod} temporary HP"
                                self._toast(msg)
                            self._mark_dirty()
                            self._refresh_combat_weapons()
                            self._refresh_effects_list()
                            self._refresh_combat()
                            return
                        # Berserker's Frenzy: clicking Use must actually turn
                        # the effect on, same as Rage. Requires Rage to
                        # already be active (you can only
                        # frenzy while raging); doesn't consume a turn slot
                        # itself since it's a decision made alongside
                        # raging, not a separate action.
                        # Sacred Weapon (Paladin, Oath of Devotion): draws
                        # from the shared Channel Divinity pool rather than
                        # having its own resource, so the generic
                        # fuzzy-match loop below wouldn't find a match for
                        # "sacred weapon" against a resource named "Channel
                        # Divinity" — needs its own handling.
                        # Second Wind (Fighter, 1st level): the generic
                        # fallback below only decrements the use counter,
                        # it never actually applies HP — meaning every
                        # Fighter's most basic, most-used feature required
                        # manually rolling and updating HP themselves.
                        # Rolls and applies the heal directly, matching
                        # the pattern used for hit-dice spending.
                        if key == "second wind":
                            sw_res = next((r for r in self.char.get("resources", [])
                                           if "second wind" in str(r.get("name","")).lower()), None)
                            if sw_res is None or sw_res.get("current", 0) <= 0:
                                self._toast("✖ Second Wind: no uses left (recharges on short/long rest)")
                                return
                            import random
                            from dnd_app.core.character import class_levels as _class_levels_sw
                            fighter_lvl = _class_levels_sw(self.char).get("Fighter", 0)
                            roll = random.randint(1, 10)
                            heal = roll + fighter_lvl
                            sw_res["current"] = sw_res.get("current", 1) - 1
                            cur, mx = self.char.get("current_hp", 0), self.char.get("max_hp", 0)
                            self.char["current_hp"] = min(mx, cur + heal)
                            if hasattr(self, "_hp_current_hp"):
                                self._hp_current_hp.setValue(self.char["current_hp"])
                            self._toast(f"\U0001f4aa Second Wind: rolled {roll} + {fighter_lvl} "
                                        f"(Fighter level) = {heal} HP healed "
                                        f"({sw_res['current']}/{sw_res.get('current_max')} left)")
                            self._mark_dirty()
                            self._refresh_combat()
                            return
                        if key == "divine smite":
                            avail_levels = [l for l in range(1, 6)
                                           if (bar := self._slot_bars.get(l)) and bar._max > 0
                                           and bar.get_used() < bar._max]
                            if not avail_levels:
                                self._toast("✖ Divine Smite: no available spell slots to expend")
                                return
                            level, ok = QInputDialog.getItem(
                                self, "Divine Smite", "Expend which spell slot level?",
                                [f"{l}{'st' if l==1 else 'nd' if l==2 else 'rd' if l==3 else 'th'}-level"
                                 for l in avail_levels], 0, False)
                            if not ok:
                                return
                            slot_lvl = avail_levels[[f"{l}{'st' if l==1 else 'nd' if l==2 else 'rd' if l==3 else 'th'}-level"
                                                      for l in avail_levels].index(level)]
                            # The undead/fiend bonus is asked about and
                            # added to the computed total here, not just
                            # shown as a static reminder in the toast text.
                            is_undead_fiend = QMessageBox.question(
                                self, "Divine Smite", "Is the target undead or a fiend?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
                            bar = self._slot_bars[slot_lvl]
                            bar.set_used(bar.get_used() + 1)
                            bar._update_count()
                            self._on_slot_change()
                            # 1d8 base + 1d8 per slot level (equivalent to the
                            # standard "2d8 + 1d8 per level above 1st"
                            # phrasing, capped at 5d8 before the undead/fiend
                            # bonus), +1d8 more if the target is undead/fiend.
                            dice = min(5, 1 + slot_lvl)
                            if is_undead_fiend:
                                dice += 1
                            self._toast(f"⚔ Divine Smite: expended a level-{slot_lvl} slot — "
                                        f"{dice}d8 radiant damage"
                                        + (" (includes +1d8 vs. undead/fiend)" if is_undead_fiend else ""))
                            self._mark_dirty()
                            return
                        if key == "sacred weapon":
                            fx = self.char.setdefault("active_effects", [])
                            if "Sacred Weapon" in fx:
                                fx.remove("Sacred Weapon")
                                self._toast("⚔ Sacred Weapon: OFF")
                            else:
                                cd_res = next((r for r in self.char.get("resources", [])
                                               if "channel divinity" in str(r.get("name","")).lower()), None)
                                if cd_res and cd_res.get("current", 0) <= 0:
                                    self._toast("✖ Sacred Weapon: no Channel Divinity uses left "
                                                "(recharges on short/long rest)")
                                    return
                                if cd_res:
                                    cd_res["current"] = cd_res.get("current", 0) - 1
                                fx.append("Sacred Weapon")
                                self._toast("⚔ Sacred Weapon: ON — add CHA mod to attacks with "
                                            "your weapon for 1 minute")
                            self._mark_dirty()
                            self._refresh_combat_weapons()
                            self._refresh_effects_list()
                            return
                        if key == "peerless athlete":
                            # Peerless Athlete is a Channel Divinity
                            # option (Oath of Glory, 3rd level), not its own resource.
                            fx = self.char.setdefault("active_effects", [])
                            if "Peerless Athlete" in fx:
                                fx.remove("Peerless Athlete")
                                self._toast("🏃 Peerless Athlete: OFF")
                            else:
                                cd_res = next((r for r in self.char.get("resources", [])
                                               if "channel divinity" in str(r.get("name","")).lower()), None)
                                if cd_res and cd_res.get("current", 0) <= 0:
                                    self._toast("✖ Peerless Athlete: no Channel Divinity uses left "
                                                "(recharges on short/long rest)")
                                    return
                                if cd_res:
                                    cd_res["current"] = cd_res.get("current", 0) - 1
                                fx.append("Peerless Athlete")
                                self._toast("🏃 Peerless Athlete: ON — doubled carry capacity, "
                                            "advantage on Athletics/Acrobatics, for 10 minutes")
                            self._mark_dirty()
                            self._refresh_combat_weapons()
                            self._refresh_effects_list()
                            return
                        if "frenzi" in key:
                            if "Rage" not in self.char.get("active_effects", []):
                                self._toast("⚠ Frenzy requires an active Rage first")
                                return
                            fx = self.char.setdefault("active_effects", [])
                            if "Frenzy" in fx:
                                fx.remove("Frenzy")
                                self._toast("😤 Frenzy: OFF")
                            else:
                                fx.append("Frenzy")
                                self._toast("😤 Frenzy: ON — bonus action melee attack each turn "
                                            "for the rest of your rage; 1 exhaustion when it ends")
                            self._mark_dirty()
                            self._refresh_effects_list()
                            return
                        # Try to spend a matching tracked resource first
                        for res in self.char.get("resources", []):
                            rname = str(res.get("name","")).lower()
                            if (key and (key in rname or rname in key)
                                    and res.get("current_max", 0) > 0):
                                # Simple toggles (Rage, Bladesong, Invincible
                                # Conqueror, etc. — anything in
                                # RESOURCE_POOL_TOGGLES): don't spend a second
                                # use if already active — the real toggle for
                                # on/off is the "Active" checkbox on this
                                # resource's own row in the Other tab, which
                                # already correctly manages active_effects.
                                # This button is for STARTING the effect, not
                                # re-affirming one already in progress. This
                                # check (and the matching activation below)
                                # must cover every RESOURCE_POOL_TOGGLES
                                # entry, not just Rage, since each shares the
                                # same fallback Use button.
                                if _display in RESOURCE_POOL_TOGGLES and _display in self.char.get("active_effects", []):
                                    self._toast(f"⚡ {_display} already active — use the \"Active\" "
                                                f"checkbox on its resource row (Other tab) to end it")
                                    return
                                cur = res.get("current", 0)
                                if cur <= 0:
                                    self._toast(f"✖ {_display}: no uses left "
                                                f"(recharges on {res.get('reset','rest')})")
                                else:
                                    res["current"] = cur - 1
                                    self._toast(f"⚡ Used {_display} "
                                                f"({res['current']}/{res.get('current_max')} left)")
                                    # The resource spend alone wouldn't
                                    # otherwise turn the effect on — every
                                    # mechanical effect of these toggles reads
                                    # active_effects, and this keeps the two
                                    # in sync with what the Other tab's
                                    # checkbox already does, so starting the
                                    # effect from either place works the same.
                                    if _display in RESOURCE_POOL_TOGGLES:
                                        fx = self.char.setdefault("active_effects", [])
                                        if _display not in fx:
                                            fx.append(_display)
                                        self._refresh_combat_weapons()
                                        self._refresh_effects_list()
                                        # The Other tab's own "Active" checkbox
                                        # for this same toggle calls
                                        # ctrl.refresh() (deferred, same
                                        # reason as there: not synchronously
                                        # inside a signal handler) so that
                                        # update_all() actually applies the
                                        # effect's real mechanics -- AC,
                                        # resistances, etc., all keyed off
                                        # active_effects. This button used to
                                        # skip that and only call the two
                                        # narrow refreshers above, so using
                                        # Rage (or any other toggle) from its
                                        # action-tab card spent the resource
                                        # and flipped active_effects, but
                                        # never actually applied what turning
                                        # it on is supposed to do.
                                        QTimer.singleShot(0, self.ctrl.refresh)
                                    self._mark_dirty()
                                    self._mark_turn_used(_b)
                                    self._refresh_action_tabs()
                                return
                        # No tracked resource → consume the turn slot + summary
                        self._mark_turn_used(_b)
                        self._toast(f"⚔ {_display}: {_desc[:90]}")
                    use_btn.clicked.connect(_use_ability)
                    # Row click → full rules text (button = do it)
                    card.mousePressEvent = (lambda e, _d=display, _s=source, _x=desc:
                        QMessageBox.information(self, _d,
                            f"<b>{_d}</b><br><i>Source: {_s}</i><br><br>{_x}"))

                for w in (card, lbl_name, lbl_desc, src_badge):
                    w.setToolTip(tooltip_text)

                cl.addWidget(src_badge, 0, Qt.AlignTop)
                cl.addLayout(text_col, 1)
                cl.addWidget(use_btn, 0, Qt.AlignTop)
                if bucket_name in ('Action','Bonus Action','Reaction'):
                    self._bucket_use_btns[bucket_name].append(use_btn)
                grid.addWidget(card, idx // 2, idx % 2)

            if rows:
                # Balance odd counts so the last card doesn't stretch full width
                if len(rows) % 2 == 1:
                    filler = QWidget(); filler.setStyleSheet("background:transparent;")
                    grid.addWidget(filler, (len(rows)-1)//2, 1)
                bl.insertWidget(bl.count()-1, grid_host)
            else:
                hint = {"Action": "Universal actions apply — see any missing? "
                                   "Attack, Dash, Dodge and friends live here.",
                        "Bonus Action": "No bonus actions available — class features, "
                                        "feats, and ★-pinned spells appear here.",
                        "Reaction": "Opportunity Attack is always available. Reaction "
                                    "spells like Shield or Counterspell appear here when known.",
                        "Passive": "Passive features, resources and item charges appear here."}
                empty = _lbl(hint.get(bucket_name, "None for this character"),
                             TEXT3, FS_TINY, wrap=True)
                bl.insertWidget(bl.count()-1, empty)

        # ── Update tab labels with live counts ───────────────────────────────
        _ICONS = {"Action":"⚔","Bonus Action":"✦","Reaction":"⚡","Passive":"◎"}
        _LABELS = {"Action":"Action","Bonus Action":"Bonus Action",
                   "Reaction":"Reaction","Passive":"Other"}
        for ti, bname in enumerate(["Action","Bonus Action","Reaction","Passive"]):
            n = len(buckets.get(bname, []))
            self._action_tabs.setTabText(
                ti, f"{_ICONS[bname]} {_LABELS[bname]}" + (f"  ({n})" if n else ""))
        self._refresh_effects_list()
        self._apply_turn_state()

