"""
Accessible dark theme — WCAG AA compliant.
Min font: 13px body, 15px labels, 18px headings, 24px+ stat numbers.
Contrast ratios: text on dark bg ≥ 4.5:1

Author: Ethan O'Brien
Date: 2026-08-20
"""

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0f1117"   # page background
SURF    = "#181c28"   # card/panel surface
SURF2   = "#1e2336"   # raised surface
SURF3   = "#252a40"   # hover/selected surface
BORDER  = "#505670"   # subtle border — 2.6:1 on BG (was 1.6:1, too faint to read as an edge)
BORDER2 = "#4a5480"   # active border

TEXT    = "#eeeaf8"   # primary text  — 14.8:1 on BG
TEXT2   = "#b0acc8"   # secondary text — 7.2:1 on BG
TEXT3   = "#908fa9"   # muted text — 6.0:1 on BG, 4.5:1 on SURF3 (was 4.6:1/3.4:1, failed against raised surfaces)

GOLD    = "#d4a820"   # gold accent — 6.8:1 on BG
GOLD2   = "#f5cc50"   # bright gold

INDIGO  = "#5b7af5"   # primary blue — 4.7:1 on SURF
IND2    = "#8fa8ff"   # lighter blue — 7.1:1

TEAL    = "#18b28a"   # success/heal — 5.2:1
TEAL2   = "#22d4a8"   # bright teal

CRIMSON = "#d44040"   # danger — 5.1:1
CRIM2   = "#f06060"   # bright red

PURPLE  = "#8e50d8"   # magic — 4.8:1
PURP2   = "#b87cff"   # bright purple

AMBER   = "#e09020"   # warning — 5.4:1
AMBE2   = "#f5b040"   # bright amber

GREEN   = "#2ea854"   # success
GREEN2  = "#48d470"

PANELDK = "#212949"   # dark accent chrome (tab-bar gap, etc.) -- see THEMES

def qa(color: str, alpha) -> str:
    """Qt-style alpha hex: Qt QSS parses 8-digit hex as #AARRGGBB (alpha FIRST),
    unlike CSS #RRGGBBAA. qa(TEAL, 0x33) -> "#3318b28a"."""
    a = alpha if isinstance(alpha, str) else f"{alpha:02x}"
    return f"#{a}{color.lstrip('#')}"


# ── Font sizes (px) — WCAG compliant ─────────────────────────────────────────
# Base (100%/"Medium") sizes. The module-level FS_* names below are the
# live, scale-adjusted values every other module reads (directly via
# `from .theme import *`, or refreshed via sync_globals()) — set_font_scale()
# recomputes them in place so "Small"/"Large" in Settings actually changes
# rendered text size, instead of only being saved and never applied.
_BASE_FS = {
    "FS_TINY": 11,    # badge labels only
    "FS_SMALL": 13,   # secondary labels, hints
    "FS_BODY": 15,    # primary body text
    "FS_LABEL": 16,   # form labels, skill names
    "FS_HEAD": 18,    # section headers
    "FS_TITLE": 22,   # card titles
    "FS_STAT": 28,    # ability score numbers
    "FS_BIG": 36,     # AC, HP, major stats
}
# name -> scale factor. "Medium (default)" is the reference 1.0 in _BASE_FS.
# Large is deliberately modest (not e.g. 1.3+): a lot of small UI chrome
# (level pills, source badges, reset badges) lives in setFixedHeight/
# setFixedSize containers as tight as 16-18px tall with only 1-2px of
# padding around FS_TINY text -- a bigger jump risks clipped/truncated
# text in exactly those spots. 1.15 keeps body/heading text meaningfully
# larger while staying inside that headroom.
FONT_SCALES = {"Small": 0.85, "Medium (default)": 1.0, "Large": 1.15}
_font_scale = 1.0

FS_TINY, FS_SMALL, FS_BODY, FS_LABEL, FS_HEAD, FS_TITLE, FS_STAT, FS_BIG = (
    _BASE_FS["FS_TINY"], _BASE_FS["FS_SMALL"], _BASE_FS["FS_BODY"], _BASE_FS["FS_LABEL"],
    _BASE_FS["FS_HEAD"], _BASE_FS["FS_TITLE"], _BASE_FS["FS_STAT"], _BASE_FS["FS_BIG"],
)


def set_font_scale(scale_name: str) -> None:
    """Recompute the module-level FS_* globals for the given Settings
    scale name ("Small"/"Medium (default)"/"Large"). Callers must still
    re-apply the theme (apply_theme()) and call sync_globals() in every
    already-built widget module for the change to actually render —
    this function only updates theme.py's own copy of the values.

    FS_TINY is deliberately excluded from scaling: it's used exclusively
    for badge/pill labels (source badges, reset badges, level pills) set
    in fixed-pixel containers as short as 16px tall with almost no
    padding to spare. Scaling it up would clip that text; scaling it
    down would make already-small badge text harder to read for no
    benefit. Every other size (body text, labels, headings, stat
    numbers) lives in normal flow layouts that can absorb the change."""
    global FS_SMALL, FS_BODY, FS_LABEL, FS_HEAD, FS_TITLE, FS_STAT, FS_BIG, _font_scale
    _font_scale = FONT_SCALES.get(scale_name, 1.0)
    FS_SMALL = max(1, round(_BASE_FS["FS_SMALL"] * _font_scale))
    FS_BODY  = max(1, round(_BASE_FS["FS_BODY"] * _font_scale))
    FS_LABEL = max(1, round(_BASE_FS["FS_LABEL"] * _font_scale))
    FS_HEAD  = max(1, round(_BASE_FS["FS_HEAD"] * _font_scale))
    FS_TITLE = max(1, round(_BASE_FS["FS_TITLE"] * _font_scale))
    FS_STAT  = max(1, round(_BASE_FS["FS_STAT"] * _font_scale))
    FS_BIG   = max(1, round(_BASE_FS["FS_BIG"] * _font_scale))


THEMES = {
    # ── 1. Obsidian — sharp indigo/blue on near-black. Clean modern default ─
    "(Dark) Obsidian": {
        "BG":"#0d0f18","SURF":"#161922","SURF2":"#1c2030","SURF3":"#242840",
        "BORDER":"#50556d","BORDER2":"#4a5890",
        "TEXT":"#eae8f5","TEXT2":"#a8a4c8","TEXT3":"#8f8da8",
        "GOLD":"#e0b030","GOLD2":"#f8d060",
        "INDIGO":"#5878f8","IND2":"#90a8ff",
        "TEAL":"#18c090","TEAL2":"#28e8b0",
        "CRIMSON":"#e24f5d","CRIM2":"#e97782",
        "PURPLE":"#a064ea","PURP2":"#b384ee",
        "AMBER":"#e89828","AMBE2":"#f8c048",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#212949",
    },
    # ── 2. Dragon's Hoard — deep emerald + molten gold. Wealth and danger ──
    "(Dark) Dragon's Hoard": {
        "BG":"#060d0a","SURF":"#0c1a12","SURF2":"#12241a","SURF3":"#182e22",
        "BORDER":"#3b5c47","BORDER2":"#286040",
        "TEXT":"#e8f5e0","TEXT2":"#90c898","TEXT3":"#739979",
        "GOLD":"#e8a820","GOLD2":"#ffd050",
        "INDIGO":"#20b860","IND2":"#40e880",
        "TEAL":"#18b8a0","TEAL2":"#30e0c0",
        "CRIMSON":"#e84828","CRIM2":"#f87858",
        "PURPLE":"#a066d9","PURP2":"#b284e1",
        "AMBER":"#e8a820","AMBE2":"#ffd050",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#17352d",
    },
    # ── 3. Shadowfell — cold purple/grey on true black. Gothic and moody ───
    "(Dark) Shadowfell": {
        "BG":"#080610","SURF":"#100e1c","SURF2":"#181528","SURF3":"#201c34",
        "BORDER":"#53506a","BORDER2":"#4a4470",
        "TEXT":"#d8d0f0","TEXT2":"#9888c8","TEXT3":"#8882a0",
        "GOLD":"#c8a838","GOLD2":"#e8c858",
        "INDIGO":"#7a6cdb","IND2":"#a090f8",
        "TEAL":"#4898c8","TEAL2":"#70c0f0",
        "CRIMSON":"#cc5183","CRIM2":"#d6749c",
        "PURPLE":"#9068e0","PURP2":"#c098ff",
        "AMBER":"#c89838","AMBE2":"#e8c050",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#272743",
    },
    # ── 4. Feywild — vibrant teal/pink on rich midnight blue. Magical ─────
    "(Dark) Feywild": {
        "BG":"#080820","SURF":"#0e1030","SURF2":"#141640","SURF3":"#1a1c52",
        "BORDER":"#4c5086","BORDER2":"#303898",
        "TEXT":"#f0ecff","TEXT2":"#b0a8e8","TEXT3":"#8b84ac",
        "GOLD":"#e8c840","GOLD2":"#ffe870",
        "INDIGO":"#28c8d8","IND2":"#60e8f8",
        "TEAL":"#18c898","TEAL2":"#28f0c0",
        "CRIMSON":"#e83888","CRIM2":"#f870b8",
        "PURPLE":"#ab56e9","PURP2":"#cb6aff",
        "AMBER":"#e8a830","AMBE2":"#ffd060",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#183843",
    },
    # ── 5. Blood Moon — gothic vampire crimson/black. Ravenloft horror ────
    "(Dark) Blood Moon": {
        "BG":"#100609","SURF":"#1c0c10","SURF2":"#241016","SURF3":"#30161e",
        "BORDER":"#6e4952","BORDER2":"#8a3048",
        "TEXT":"#f5e0e4","TEXT2":"#c890a0","TEXT3":"#9b7d89",
        "GOLD":"#c89040","GOLD2":"#e8b060",
        "INDIGO":"#d24d68","IND2":"#f85878",
        "TEAL":"#209888","TEAL2":"#40c8b0",
        "CRIMSON":"#f01838","CRIM2":"#ff5068",
        "PURPLE":"#a262c8","PURP2":"#b37fd2",
        "AMBER":"#d87828","AMBE2":"#f89848",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#37222f",
    },
    # ── 6. Frostspire — icy blue/white winter. Frost giant peaks ──────────
    "(Dark) Frostspire": {
        "BG":"#060a12","SURF":"#0c1420","SURF2":"#121c2c","SURF3":"#182438",
        "BORDER":"#40566b","BORDER2":"#406890",
        "TEXT":"#e8f0f8","TEXT2":"#98b8d0","TEXT3":"#798d9f",
        "GOLD":"#c8b060","GOLD2":"#e8d080",
        "INDIGO":"#3888e0","IND2":"#68b0f8",
        "TEAL":"#20b8c8","TEAL2":"#48e0f0",
        "CRIMSON":"#e04848","CRIM2":"#f87878",
        "PURPLE":"#8173cc","PURP2":"#988cd5",
        "AMBER":"#d89840","AMBE2":"#f8b860",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#1b2c44",
    },
    # ── 7. Cinderveil — volcanic orange/black. Molten, infernal ───────────
    "(Dark) Cinderveil": {
        "BG":"#100804","SURF":"#1c1008","SURF2":"#241608","SURF3":"#301c0a",
        "BORDER":"#724b33","BORDER2":"#985018",
        "TEXT":"#f8ecd8","TEXT2":"#d0a878","TEXT3":"#a0825d",
        "GOLD":"#e89818","GOLD2":"#ffc040",
        "INDIGO":"#e85818","IND2":"#ff8848",
        "TEAL":"#189888","TEAL2":"#38c8a8",
        "CRIMSON":"#e83e3e","CRIM2":"#ed6d6d",
        "PURPLE":"#9b709b","PURP2":"#ad8aad",
        "AMBER":"#f8a828","AMBE2":"#ffc858",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#3b2420",
    },
    # ── 8. Tavern Hearth — warm aged wood + firelight. Cozy, welcoming ────
    "(Dark) Tavern Hearth": {
        "BG":"#140d08","SURF":"#1e140c","SURF2":"#281c12","SURF3":"#322418",
        "BORDER":"#655241","BORDER2":"#785030",
        "TEXT":"#f5e8d0","TEXT2":"#c8a878","TEXT3":"#a3886f",
        "GOLD":"#e8a838","GOLD2":"#ffc858",
        "INDIGO":"#c87830","IND2":"#e89850",
        "TEAL":"#5f895f","TEAL2":"#68a068",
        "CRIMSON":"#d75746","CRIM2":"#df7b6e",
        "PURPLE":"#977697","PURP2":"#aa8faa",
        "AMBER":"#f0a828","AMBE2":"#ffc858",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#352925",
    },
    # ── 9. Mossgrove — lighter, earthy olive-green forest ────────────────
    "(Dark) Mossgrove": {
        "BG":"#0e120a","SURF":"#161c10","SURF2":"#1e2616","SURF3":"#26301c",
        "BORDER":"#4e5b3e","BORDER2":"#5c7038",
        "TEXT":"#e8f0d8","TEXT2":"#a8c088","TEXT3":"#8b996f",
        "GOLD":"#b8a038","GOLD2":"#d8c058",
        "INDIGO":"#798939","IND2":"#a0b858",
        "TEAL":"#489878","TEAL2":"#68c098",
        "CRIMSON":"#cc6556","CRIM2":"#d68579",
        "PURPLE":"#8a7da6","PURP2":"#a195b7",
        "AMBER":"#c88838","AMBE2":"#e8a858",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#272c26",
    },
    # ── 10. Gearworks — artificer's workshop. Brass, copper, gunmetal ─────
    "(Dark) Gearworks": {
        "BG":"#0e1012","SURF":"#161a1e","SURF2":"#1e242a","SURF3":"#262e36",
        "BORDER":"#51575e","BORDER2":"#605038",
        "TEXT":"#f0ece0","TEXT2":"#b8a888","TEXT3":"#9d9286",
        "GOLD":"#c88838","GOLD2":"#e8a858",
        "INDIGO":"#5a86aa","IND2":"#70a0c8",
        "TEAL":"#389888","TEAL2":"#58c0a8",
        "CRIMSON":"#db594a","CRIM2":"#e37e72",
        "PURPLE":"#8a7da7","PURP2":"#a095b7",
        "AMBER":"#d89838","AMBE2":"#f8b858",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#212c3a",
    },
    # ── 11. Hallowed Stone — church slate grey + gold. Temple and vestry ──
    "(Dark) Hallowed Stone": {
        "BG":"#0e1014","SURF":"#161a20","SURF2":"#1e242c","SURF3":"#262e38",
        "BORDER":"#4f5763","BORDER2":"#586478",
        "TEXT":"#e8e8f0","TEXT2":"#a8b0c0","TEXT3":"#8e94a0",
        "GOLD":"#d8b840","GOLD2":"#f8d868",
        "INDIGO":"#7281a7","IND2":"#8898c0",
        "TEAL":"#389880","TEAL2":"#58c0a0",
        "CRIMSON":"#c76767","CRIM2":"#d38585",
        "PURPLE":"#8f7aab","PURP2":"#a493ba",
        "AMBER":"#c89840","AMBE2":"#e8b860",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#262b3a",
    },
    # ── 12. Underdark — Bioluminescent violet fungal glow on true black. Deep, alien, subterranean ──
    "(Dark) Underdark": {
        "BG":"#120e14","SURF":"#1c1620","SURF2":"#241c29","SURF3":"#2f2534",
        "BORDER":"#6b5676","BORDER2":"#704785",
        "TEXT":"#eeebef","TEXT2":"#bbacc3","TEXT3":"#9c8fa3",
        "GOLD":"#a77b13","GOLD2":"#c49016",
        "INDIGO":"#bd52e1","IND2":"#cb78e7",
        "TEAL":"#249183","TEAL2":"#2bab99",
        "CRIMSON":"#e44192","CRIM2":"#ea6fac",
        "PURPLE":"#9f66e2","PURP2":"#b284e7",
        "AMBER":"#b17611","AMBE2":"#cf8b14",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#332244",
    },
    # ── 13. Astral Sea — Cosmic navy-black speckled with starlight blue and silver. Vast, serene, otherworldly ──
    "(Dark) Astral Sea": {
        "BG":"#0e0f14","SURF":"#161820","SURF2":"#1c1f29","SURF3":"#252834",
        "BORDER":"#565c76","BORDER2":"#475485",
        "TEXT":"#ebecef","TEXT2":"#acb1c3","TEXT3":"#8f93a3",
        "GOLD":"#9e7f17","GOLD2":"#ba951b",
        "INDIGO":"#537ee3","IND2":"#7598e9",
        "TEAL":"#258f9f","TEAL2":"#2ca7bb",
        "CRIMSON":"#e24c65","CRIM2":"#e97588",
        "PURPLE":"#906ee0","PURP2":"#a58ae6",
        "AMBER":"#a67b15","AMBE2":"#c49118",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#202a45",
    },
    # ── 14. Nine Hells — Brimstone and ash — sulfur, ember-red, scorched black. Infernal bureaucracy and fire ──
    "(Dark) Nine Hells": {
        "BG":"#140e0e","SURF":"#201716","SURF2":"#291e1c","SURF3":"#342725",
        "BORDER":"#765a56","BORDER2":"#855047",
        "TEXT":"#efeceb","TEXT2":"#c3afac","TEXT3":"#a3928f",
        "GOLD":"#9c8011","GOLD2":"#b79714",
        "INDIGO":"#7c8a28","IND2":"#92a22f",
        "TEAL":"#d55f3a","TEAL2":"#de8164",
        "CRIMSON":"#e84b45","CRIM2":"#ed7671",
        "PURPLE":"#c355ce","PURP2":"#d07ad8",
        "AMBER":"#ba720f","AMBE2":"#da8712",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#282d23",
    },
    # ── 15. Kraken's Depth — Crushing oceanic black-teal with bioluminescent cyan. Deep-sea pressure and dread ──
    "(Dark) Kraken's Depth": {
        "BG":"#0e1214","SURF":"#161e20","SURF2":"#1c2629","SURF3":"#253134",
        "BORDER":"#567076","BORDER2":"#477885",
        "TEXT":"#ebeeef","TEXT2":"#acbec3","TEXT3":"#8f9fa3",
        "GOLD":"#a5811b","GOLD2":"#c29720",
        "INDIGO":"#2390b7","IND2":"#2aa9d6",
        "TEAL":"#209591","TEAL2":"#25aea9",
        "CRIMSON":"#df5b47","CRIM2":"#e68171",
        "PURPLE":"#8878d8","PURP2":"#9f93e0",
        "AMBER":"#af7c16","AMBE2":"#ce9219",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#182e3d",
    },
    # ── 16. Storm Giant's Eye — Slate-grey storm clouds shot through with lightning gold. Tempest and thunderheads ──
    "(Dark) Storm Giant's Eye": {
        "BG":"#0e1014","SURF":"#161920","SURF2":"#1c2029","SURF3":"#252a34",
        "BORDER":"#566176","BORDER2":"#475c85",
        "TEXT":"#ebecef","TEXT2":"#acb4c3","TEXT3":"#8f96a3",
        "GOLD":"#988213","GOLD2":"#b39816",
        "INDIGO":"#4384d7","IND2":"#689cdf",
        "TEAL":"#2d8f99","TEAL2":"#34a8b4",
        "CRIMSON":"#e0515c","CRIM2":"#e77882",
        "PURPLE":"#8774d7","PURP2":"#9e8fde",
        "AMBER":"#a17e0d","AMBE2":"#bd940f",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#1d2b43",
    },
    # ── 1. Arcane Scroll — warm parchment. Wizard's library, readable ─────
    # Accent colors (GOLD/INDIGO/TEAL/CRIMSON/PURPLE/AMBER and their *2
    # "bright" variants) were darkened from their original values below
    # 4.5:1 against cards raised above the page (SURF2/SURF3) — the
    # dark-theme convention of "*2 = lighter, for extra pop against a
    # near-black background" is backwards on a light background, where a
    # lighter accent just washes out. *2 variants now target ≥5.3:1 (more
    # saturated/darker than their base, not lighter) so they stay both
    # readable AND visually distinct as the "emphasized" version. TEXT/
    # TEXT2/TEXT3 were already fine (11–16:1) and are unchanged.
    "(Light) Arcane Scroll": {
        "BG":"#f2edd8","SURF":"#e8e0c4","SURF2":"#ddd5b0","SURF3":"#cfc79a",
        "BORDER":"#a69161","BORDER2":"#9a7840",
        "TEXT":"#18100a","TEXT2":"#3a2808","TEXT3":"#6a4820",
        "GOLD":"#724707","GOLD2":"#63400e",
        "INDIGO":"#1e3ea0","IND2":"#153eaa",
        "TEAL":"#0c5c3e","TEAL2":"#0a512f",
        "CRIMSON":"#8c1818","CRIM2":"#8f1414",
        "PURPLE":"#5a1878","PURP2":"#6e1c98",
        "AMBER":"#734606","AMBE2":"#683e0a",
        "GREEN":"#195b2e","GREEN2":"#0e5221",
        "PANELDK":"#171f39",
    },
    # ── 2. Moonlit Vellum — cool silvery-blue-grey parchment. Scholarly, crisp ─
    # Accent colors darkened for contrast — see Arcane Scroll's comment above.
    "(Light) Moonlit Vellum": {
        "BG":"#eef1f6","SURF":"#e2e7f0","SURF2":"#d5dcea","SURF3":"#c7d0e2",
        "BORDER":"#8f96a7","BORDER2":"#77829b",
        "TEXT":"#282e3b","TEXT2":"#495162","TEXT3":"#535967",
        "GOLD":"#6c520c","GOLD2":"#604a12",
        "INDIGO":"#2c4ba8","IND2":"#2e4999",
        "TEAL":"#0b644d","TEAL2":"#0f5946",
        "CRIMSON":"#a3273a","CRIM2":"#8f2938",
        "PURPLE":"#6a3a9e","PURP2":"#643990",
        "AMBER":"#7f4b07","AMBE2":"#6f450b",
        "GREEN":"#1b6231","GREEN2":"#0f5924",
        "PANELDK":"#19213a",
    },
    # ── 3. Sunlit Meadow — warm cream and sage green. Bright, welcoming ──────
    # Accent colors darkened for contrast — see Arcane Scroll's comment above.
    "(Light) Sunlit Meadow": {
        "BG":"#f3f0e2","SURF":"#e9e4cd","SURF2":"#ded6b3","SURF3":"#cfc596",
        "BORDER":"#9f966e","BORDER2":"#8e814b",
        "TEXT":"#312d1b","TEXT2":"#565135","TEXT3":"#585239",
        "GOLD":"#654a08","GOLD2":"#584211",
        "INDIGO":"#354f81","IND2":"#324771",
        "TEAL":"#135a36","TEAL2":"#174f32",
        "CRIMSON":"#8e2f24","CRIM2":"#7b2d22",
        "PURPLE":"#6d3e7b","PURP2":"#5c3867",
        "AMBER":"#6e490c","AMBE2":"#5f410f",
        "GREEN":"#195b2e","GREEN2":"#0e5221",
        "PANELDK":"#1b2233",
    },
    # ── 4. Elven Grove — Pale sage woodland with lavender undertones. Ethereal, ancient, sylvan ──
    "(Light) Elven Grove": {
        "BG":"#edf1ec","SURF":"#dee7dd","SURF2":"#cedccc","SURF3":"#b9ceb6",
        "BORDER":"#87b181","BORDER2":"#60ab54",
        "TEXT":"#182815","TEXT2":"#324c2f","TEXT3":"#466241",
        "GOLD":"#7c5616","GOLD2":"#614311",
        "INDIGO":"#7643b0","IND2":"#5d348a",
        "TEAL":"#1f6944","TEAL2":"#185235",
        "CRIMSON":"#a7314e","CRIM2":"#83263e",
        "PURPLE":"#7c43a4","PURP2":"#613481",
        "AMBER":"#865116","AMBE2":"#683f11",
        "GREEN":"#2d6a23","GREEN2":"#23531c",
        "PANELDK":"#26203c",
    },
    # ── 5. Coastal Tide — Pale seafoam and sea-glass blue-green. Salt air, tidepools, driftwood ──
    "(Light) Coastal Tide": {
        "BG":"#ecf0f1","SURF":"#dde6e7","SURF2":"#ccdadc","SURF3":"#b6cbce",
        "BORDER":"#81adb1","BORDER2":"#54a2ab",
        "TEXT":"#152628","TEXT2":"#2f494c","TEXT3":"#415f62",
        "GOLD":"#775719","GOLD2":"#5c4414",
        "INDIGO":"#2a627f","IND2":"#214c62",
        "TEAL":"#1e6764","TEAL2":"#17504f",
        "CRIMSON":"#a33929","CRIM2":"#7f2d20",
        "PURPLE":"#644bb0","PURP2":"#4e3a88",
        "AMBER":"#8b4d17","AMBE2":"#6c3c12",
        "GREEN":"#276752","GREEN2":"#1f5040",
        "PANELDK":"#192533",
    },
    # ── 6. Rose Chantry — Soft blush parchment with burgundy accents. A temple of healing and devotion ──
    "(Light) Rose Chantry": {
        "BG":"#f1eced","SURF":"#e7dddf","SURF2":"#dccccf","SURF3":"#ceb6bb",
        "BORDER":"#b1818a","BORDER2":"#ab5465",
        "TEXT":"#281519","TEXT2":"#4c2f34","TEXT3":"#624148",
        "GOLD":"#735218","GOLD2":"#553c12",
        "INDIGO":"#8c3971","IND2":"#672a53",
        "TEAL":"#256253","TEAL2":"#1b483d",
        "CRIMSON":"#a52738","CRIM2":"#7a1d29",
        "PURPLE":"#883788","PURP2":"#642964",
        "AMBER":"#894518","AMBE2":"#653312",
        "GREEN":"#29633c","GREEN2":"#1e482c",
        "PANELDK":"#2a1e30",
    },
    # ── 7. Desert Oasis — Warm sand and terracotta with a turquoise spring. Sun-baked stone, palm shade ──
    "(Light) Desert Oasis": {
        "BG":"#f1eeec","SURF":"#e7e1dd","SURF2":"#dcd3cc","SURF3":"#cec1b6",
        "BORDER":"#b19781","BORDER2":"#ab7d54",
        "TEXT":"#281e15","TEXT2":"#4c3c2f","TEXT3":"#625141",
        "GOLD":"#745613","GOLD2":"#58420e",
        "INDIGO":"#27626e","IND2":"#1e4b55",
        "TEAL":"#1d655e","TEAL2":"#164d48",
        "CRIMSON":"#9c3c25","CRIM2":"#782e1c",
        "PURPLE":"#7b4396","PURP2":"#5e3373",
        "AMBER":"#884c11","AMBE2":"#683a0d",
        "GREEN":"#426429","GREEN2":"#324c1f",
        "PANELDK":"#182530",
    },
    # ── 8. Frostlight — Pale icy blue-white, crisp and clean. Glacier peaks and winter daylight ──
    "(Light) Frostlight": {
        "BG":"#eceff1","SURF":"#dde3e7","SURF2":"#ccd6dc","SURF3":"#b6c5ce",
        "BORDER":"#81a0b1","BORDER2":"#548bab",
        "TEXT":"#152128","TEXT2":"#2f414c","TEXT3":"#415662",
        "GOLD":"#6f581c","GOLD2":"#544315",
        "INDIGO":"#3757a4","IND2":"#2a437d",
        "TEAL":"#24636d","TEAL2":"#1c4b53",
        "CRIMSON":"#a43043","CRIM2":"#7e2433",
        "PURPLE":"#594ab5","PURP2":"#43398b",
        "AMBER":"#7f501b","AMBE2":"#613d15",
        "GREEN":"#2b6550","GREEN2":"#214d3d",
        "PANELDK":"#1b2339",
    },
    # ── 9. Harvest Gold — Warm amber and russet autumn tones. Harvest festival, hearth-bread, falling leaves ──
    "(Light) Harvest Gold": {
        "BG":"#f1efec","SURF":"#e7e2dd","SURF2":"#dcd5cc","SURF3":"#cec4b6",
        "BORDER":"#b19d81","BORDER2":"#ab8754",
        "TEXT":"#282015","TEXT2":"#4c402f","TEXT3":"#625441",
        "GOLD":"#775613","GOLD2":"#5c420f",
        "INDIGO":"#3a5d8e","IND2":"#2d476d",
        "TEAL":"#226659","TEAL2":"#1a4f45",
        "CRIMSON":"#a23822","CRIM2":"#7e2b1b",
        "PURPLE":"#804294","PURP2":"#633373",
        "AMBER":"#8e4a10","AMBE2":"#6d390c",
        "GREEN":"#416526","GREEN2":"#324e1e",
        "PANELDK":"#1c2435",
    },
    # ── 10. Sky Citadel — Pale sky blue with gilded accents. A cloud giant's floating fortress ──
    "(Light) Sky Citadel": {
        "BG":"#eceff1","SURF":"#dde2e7","SURF2":"#ccd5dc","SURF3":"#b6c3ce",
        "BORDER":"#819cb1","BORDER2":"#5485ab",
        "TEXT":"#152028","TEXT2":"#2f3f4c","TEXT3":"#415462",
        "GOLD":"#6c5819","GOLD2":"#514313",
        "INDIGO":"#2b5c95","IND2":"#204570",
        "TEAL":"#256368","TEAL2":"#1b4b4e",
        "CRIMSON":"#a2332f","CRIM2":"#7b2724",
        "PURPLE":"#5e4aae","PURP2":"#473883",
        "AMBER":"#7c511a","AMBE2":"#5d3d14",
        "GREEN":"#2d644b","GREEN2":"#224c39",
        "PANELDK":"#192437",
    },

}

_active = dict(THEMES["(Dark) Obsidian"])

def apply_theme(name: str):
    global _active
    global BG,SURF,SURF2,SURF3,BORDER,BORDER2,TEXT,TEXT2,TEXT3
    global GOLD,GOLD2,INDIGO,IND2,TEAL,TEAL2,CRIMSON,CRIM2,PURPLE,PURP2,AMBER,AMBE2
    global GREEN,GREEN2,PANELDK
    t = THEMES.get(name, THEMES["(Dark) Obsidian"])
    _active = dict(t)
    BG=t["BG"]; SURF=t["SURF"]; SURF2=t["SURF2"]; SURF3=t["SURF3"]
    BORDER=t["BORDER"]; BORDER2=t["BORDER2"]
    TEXT=t["TEXT"]; TEXT2=t["TEXT2"]; TEXT3=t["TEXT3"]
    GOLD=t["GOLD"]; GOLD2=t["GOLD2"]
    INDIGO=t["INDIGO"]; IND2=t["IND2"]
    TEAL=t["TEAL"]; TEAL2=t["TEAL2"]
    CRIMSON=t["CRIMSON"]; CRIM2=t["CRIM2"]
    PURPLE=t["PURPLE"]; PURP2=t["PURP2"]
    AMBER=t["AMBER"]; AMBE2=t["AMBE2"]
    # GREEN/GREEN2 are theme-driven like every other accent color (HP
    # bars, the initiative "Adv" badge, healing toasts) rather than a
    # single fixed value, since a bright-on-dark green fails contrast
    # against a light background.
    GREEN=t.get("GREEN", GREEN); GREEN2=t.get("GREEN2", GREEN2)
    PANELDK=t.get("PANELDK", PANELDK)
    # shared.py (button/card/pill/label factories used app-wide) is a
    # plain module of functions, not a widget with its own __init__ --
    # so unlike sheet.py/wizard.py/etc it never gets a per-construction
    # sync_globals(globals()) call of its own. Its `from .theme import *`
    # only ran once, at shared.py's first import, so every color it reads
    # directly rather than receiving as a caller-supplied argument (SURF/
    # SURF2/BORDER/BORDER2/TEXT2/TEXT3/BG inside card()/hline()/_btn()'s
    # "neutral"/"ghost" variants/_pill()/pill_btn()/badge()) needs an
    # explicit sync here, at the one place a theme switch actually
    # happens, to stay current for every caller.
    import dnd_app.ui.shared as _shared
    sync_globals(_shared.__dict__)
    return build_qss(t)


def sync_globals(module_globals: dict) -> None:
    """Re-inject the active theme values into a module's globals.
    Call at the start of any widget __init__ that uses ``from .theme import *``.
    """
    import dnd_app.ui.style.theme as _t
    for name, val in _active.items():
        module_globals[name] = val
    for attr in ('FS_TINY','FS_SMALL','FS_BODY','FS_LABEL','FS_HEAD',
                 'FS_TITLE','FS_STAT','FS_BIG','GREEN','GREEN2','PANELDK'):
        if hasattr(_t, attr):
            module_globals[attr] = getattr(_t, attr)


def build_qss(t=None):  # noqa: C901
    if t is None: t = _active
    b=t["BG"]; s=t["SURF"]; s2=t["SURF2"]; s3=t["SURF3"]
    bo=t["BORDER"]; bo2=t["BORDER2"]
    tx=t["TEXT"]; tx2=t["TEXT2"]; tx3=t["TEXT3"]
    g=t["GOLD"]; g2=t["GOLD2"]
    ind=t["INDIGO"]; ind2=t["IND2"]
    cr=t["CRIMSON"]; cr2=t["CRIM2"]
    tl=t["TEAL"]; tl2=t["TEAL2"]
    pu=t["PURPLE"]; pu2=t["PURP2"]
    am=t["AMBER"]; am2=t["AMBE2"]
    pdk=t.get("PANELDK", PANELDK)
    # Determine if theme is light (Arcane Scroll) or dark
    is_light = int(b.lstrip('#')[:2], 16) > 180

    # ── Scrollbar colours adapt to accent ─────────────────────────────────────
    scroll_handle = bo2
    scroll_hover  = ind

    # Scales every hardcoded pixel size below by the active "UI text size"
    # Settings choice, the same factor applied to the FS_* constants (see
    # set_font_scale()) — without this, native Qt widgets styled directly
    # by this stylesheet (QComboBox, QPushButton, tabs, etc.) would ignore
    # the Settings toggle entirely, even though custom-built labels using
    # FS_* would still respond.
    def px(n):
        return max(1, round(n * _font_scale))

    return f"""
/* ── Reset & Base ────────────────────────────────────────────────────────── */
* {{ font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif; font-size: {px(15)}px; }}
QMainWindow, QDialog {{ background: {b}; color: {tx}; }}
QWidget {{ background: transparent; color: {tx}; }}
QFrame {{ background: transparent; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QSplitter {{ background: {b}; }}

/* ── Tabs ──────────────────────────────────────────────────────────────────── */
/* QTabWidget's own base background (distinct from ::pane, the content
   area below the tabs, and from QTabBar, which only paints its own
   tabs) -- without this, the strip to the right of the last tab (the
   tab bar row doesn't stretch to fill the widget's full width) falls
   back to the OS's raw default widget background, which reads as a
   stray black bar regardless of the active theme.
   Painted with PANELDK (a deliberate dark accent, not the plain page
   background) rather than {b} -- on a light theme, a gap that merely
   matched the page background still read as a stray "hole"/wrong-color
   bar at a glance, and it left every theme's own visual identity out of
   an otherwise-blank strip. PANELDK gives that strip real presence, in
   the same "recessed dark chrome" language as other panel surfaces,
   with a hue unique to each theme (see THEMES/PANELDK's own comment). */
QTabWidget {{ background: {pdk}; }}
QTabWidget::pane {{ border: 1px solid {bo}; background: {b}; border-radius: 0 8px 8px 8px; }}
QTabBar {{ background: {pdk}; border-bottom: 2px solid {bo}; }}
QTabBar::tab {{
    background: {s}; color: {tx2}; padding: 12px 22px;
    border: 1px solid {bo}; border-bottom: none;
    border-radius: 8px 8px 0 0; font-weight: 700; font-size: {px(14)}px;
    margin-right: 2px; min-width: 80px;
}}
QTabBar::tab:selected {{ background: {s2}; color: {g2}; border-color: {bo2}; border-bottom: 2px solid {s2}; }}
QTabBar::tab:hover:!selected {{ background: {s2}; color: {tx}; }}

/* ── Group Boxes ───────────────────────────────────────────────────────────── */
QGroupBox {{
    background: {s}; border: 1px solid {bo}; border-radius: 10px;
    margin-top: 18px; padding: 12px 10px 10px 10px;
    font-weight: 700; font-size: {px(12)}px; color: {g};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 12px; top: 0px; background: {s};
    color: {g}; font-size: {px(12)}px; font-weight: 700; letter-spacing: 1px; padding: 0 6px;
}}

/* ── Input Fields ──────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QListWidget {{
    background: {b}; border: 2px solid {bo};
    border-radius: 6px; color: {tx}; padding: 6px 10px;
    font-size: {px(15)}px; selection-background-color: {ind};
    min-height: 32px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {ind}; background: {s};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {bo}; border: none; width: 20px; border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {ind}; }}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ border: none; width: 26px; background: {bo2}; border-radius: 0 5px 5px 0; }}
QComboBox::down-arrow {{ image: none; }}
QComboBox QAbstractItemView {{
    background: {s2}; border: 2px solid {bo2};
    selection-background-color: {ind}; color: {tx};
    outline: none; font-size: {px(15)}px; padding: 4px;
}}

/* ── Buttons ───────────────────────────────────────────────────────────────── */
QPushButton {{
    background: {s2}; border: 2px solid {bo2};
    border-radius: 7px; color: {tx}; padding: 8px 18px;
    font-weight: 700; font-size: {px(15)}px; min-height: 36px;
}}
QPushButton:hover {{ background: {ind}44; border-color: {ind}; color: {tx}; }}
QPushButton:pressed {{ background: {ind}; color: white; border-color: {ind2}; }}
QPushButton:checked {{ background: {ind}; color: white; border-color: {ind2}; }}
QPushButton:disabled {{ background: {bo}; color: {tx3}; border-color: {bo}; }}

/* ── Checkboxes & Radios ───────────────────────────────────────────────────── */
QCheckBox {{ color: {tx}; spacing: 8px; font-size: {px(15)}px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 4px;
    border: 2px solid {bo2}; background: {b};
}}
QCheckBox::indicator:checked {{ background: {ind}; border-color: {ind2}; }}
QCheckBox::indicator:hover {{ border-color: {ind}; }}
QRadioButton {{ color: {tx}; spacing: 8px; font-size: {px(15)}px; }}
QRadioButton::indicator {{
    width: 18px; height: 18px; border-radius: 9px;
    border: 2px solid {bo2}; background: {b};
}}
QRadioButton::indicator:checked {{ background: {ind}; border-color: {ind2}; }}

/* ── Scrollbars ────────────────────────────────────────────────────────────── */
QScrollBar:vertical {{ background: {s}; width: 10px; border-radius: 5px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {scroll_handle}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {scroll_hover}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; background: none; }}
QScrollBar:horizontal {{ background: {s}; height: 10px; border-radius: 5px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {scroll_handle}; border-radius: 5px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {scroll_hover}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; background: none; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

/* ── Lists & Tables ────────────────────────────────────────────────────────── */
QListWidget {{ background: {b}; border: 2px solid {bo}; border-radius: 6px; outline: none; font-size: {px(15)}px; }}
QListWidget::item {{ padding: 6px 10px; border-radius: 4px; color: {tx}; }}
QListWidget::item:selected {{ background: {ind}; color: white; }}
QListWidget::item:hover:!selected {{ background: {s2}; }}
QTableWidget {{ background: {b}; color: {tx}; border: none; gridline-color: {bo}; font-size: {px(14)}px; }}
QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {bo}; color: {tx}; }}
QTableWidget::item:selected {{ background: {ind}; color: white; }}
QHeaderView::section {{ background: {s2}; color: {g}; font-weight: 700; padding: 8px; border: none; border-bottom: 2px solid {bo}; font-size: {px(13)}px; }}

/* ── Labels ────────────────────────────────────────────────────────────────── */
QLabel {{ color: {tx}; font-size: {px(15)}px; background: transparent; }}
QLabel[heading="true"] {{ font-size: {px(20)}px; font-weight: 700; color: {g2}; }}
QLabel[subheading="true"] {{ font-size: {px(16)}px; font-weight: 700; color: {tx}; }}

/* ── Tooltips ──────────────────────────────────────────────────────────────── */
QToolTip {{
    background: {s2}; color: {tx}; border: 1px solid {bo2};
    border-radius: 6px; padding: 6px 10px; font-size: {px(13)}px;
}}

/* ── Menus ─────────────────────────────────────────────────────────────────── */
QStatusBar {{ background: {s}; border-top: 2px solid {bo}; color: {tx2}; font-size: {px(14)}px; }}
QStatusBar::item {{ border: none; }}
QMenuBar {{ background: {s}; color: {tx}; border-bottom: 1px solid {bo}; font-size: {px(15)}px; }}
QMenuBar::item {{ background: transparent; padding: 6px 12px; }}
QMenuBar::item:selected {{ background: {ind}; color: white; border-radius: 4px; }}
QMenu {{ background: {s2}; border: 2px solid {bo2}; color: {tx}; padding: 4px; font-size: {px(15)}px; }}
QMenu::item {{ padding: 8px 28px 8px 14px; border-radius: 4px; color: {tx}; }}
QMenu::item:selected {{ background: {ind}; color: white; }}
QMenu::separator {{ height: 1px; background: {bo}; margin: 3px 0; }}

/* ── Progress & Sliders ────────────────────────────────────────────────────── */
QProgressBar {{
    background: {b}; border: 2px solid {bo}; border-radius: 8px;
    text-align: center; font-size: {px(13)}px; color: {tx}; min-height: 20px;
}}
QProgressBar::chunk {{ background: {ind}; border-radius: 6px; }}
QSlider::groove:horizontal {{ background: {bo}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {ind}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; border: 2px solid {ind2}; }}
QSlider::sub-page:horizontal {{ background: {ind}; border-radius: 3px; }}

/* ── Splitters ─────────────────────────────────────────────────────────────── */
QSplitter::handle {{ background: {bo}; }}
QSplitter::handle:horizontal {{ width: 3px; }}
QSplitter::handle:vertical {{ height: 3px; }}
QSplitter::handle:hover {{ background: {ind}; }}

/* ── Dialogs ───────────────────────────────────────────────────────────────── */
QDialogButtonBox QPushButton {{ min-width: 80px; }}
QInputDialog QLabel {{ color: {tx}; }}
"""


QSS = build_qss()
