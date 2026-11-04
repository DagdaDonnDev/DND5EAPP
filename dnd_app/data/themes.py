"""Colour themes and text sizes, shared by both apps: the desktop builds
its stylesheet from these (ui_desktop/style/theme.py), and Android's
Theme.qml gets the same palettes through the sheet bridge."""

# name -> scale factor. "Medium (default)" is the reference 1.0 in _BASE_FS.
# Large is deliberately modest (not e.g. 1.3+): a lot of small UI chrome
# (level pills, source badges, reset badges) lives in setFixedHeight/
# setFixedSize containers as tight as 16-18px tall with only 1-2px of
# padding around FS_TINY text -- a bigger jump risks clipped/truncated
# text in exactly those spots. 1.15 keeps body/heading text meaningfully
# larger while staying inside that headroom.
FONT_SCALES = {"Small": 0.85, "Medium (default)": 1.0, "Large": 1.15}


THEMES = {
    # ── 1. Obsidian — sharp indigo/blue on near-black. Clean modern default ─
    "(Dark) Obsidian": {
        "BG":"#0d0f18","SURF":"#161922","SURF2":"#1c2030","SURF3":"#242840",
        "BORDER":"#50556d","BORDER2":"#4a5890",
        "TEXT":"#eae8f5","TEXT2":"#a8a4c8","TEXT3":"#918faa",
        "GOLD":"#e0b030","GOLD2":"#f8d060",
        "INDIGO":"#6f8bf9","IND2":"#90a8ff",
        "TEAL":"#18c090","TEAL2":"#28e8b0",
        "CRIMSON":"#e66a75","CRIM2":"#e97782",
        "PURPLE":"#ad78ed","PURP2":"#b384ee",
        "AMBER":"#e89828","AMBE2":"#f8c048",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#212949",
    },
    # ── 2. Dragon's Hoard — deep emerald + molten gold. Wealth and danger ──
    "(Dark) Dragon's Hoard": {
        "BG":"#060d0a","SURF":"#0c1a12","SURF2":"#12241a","SURF3":"#182e22",
        "BORDER":"#3b5c47","BORDER2":"#286040",
        "TEXT":"#e8f5e0","TEXT2":"#90c898","TEXT3":"#779d7d",
        "GOLD":"#e8a820","GOLD2":"#ffd050",
        "INDIGO":"#20b860","IND2":"#40e880",
        "TEAL":"#18b8a0","TEAL2":"#30e0c0",
        "CRIMSON":"#ec694e","CRIM2":"#f87858",
        "PURPLE":"#ad7cde","PURP2":"#b284e1",
        "AMBER":"#e8a820","AMBE2":"#ffd050",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#17352d",
    },
    # ── 3. Shadowfell — cold purple/grey on true black. Gothic and moody ───
    "(Dark) Shadowfell": {
        "BG":"#080610","SURF":"#100e1c","SURF2":"#181528","SURF3":"#201c34",
        "BORDER":"#53506a","BORDER2":"#4a4470",
        "TEXT":"#d8d0f0","TEXT2":"#9888c8","TEXT3":"#8b85a3",
        "GOLD":"#c8a838","GOLD2":"#e8c858",
        "INDIGO":"#877adf","IND2":"#a090f8",
        "TEAL":"#4898c8","TEAL2":"#70c0f0",
        "CRIMSON":"#d1638f","CRIM2":"#d6749c",
        "PURPLE":"#9873e2","PURP2":"#c098ff",
        "AMBER":"#c89838","AMBE2":"#e8c050",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#272743",
    },
    # ── 4. Feywild — vibrant teal/pink on rich midnight blue. Magical ─────
    "(Dark) Feywild": {
        "BG":"#080820","SURF":"#0e1030","SURF2":"#141640","SURF3":"#1a1c52",
        "BORDER":"#4c5086","BORDER2":"#303898",
        "TEXT":"#f0ecff","TEXT2":"#b0a8e8","TEXT3":"#8d86ae",
        "GOLD":"#e8c840","GOLD2":"#ffe870",
        "INDIGO":"#28c8d8","IND2":"#60e8f8",
        "TEAL":"#18c898","TEAL2":"#28f0c0",
        "CRIMSON":"#eb5097","CRIM2":"#f870b8",
        "PURPLE":"#b469eb","PURP2":"#cb6aff",
        "AMBER":"#e8a830","AMBE2":"#ffd060",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#183843",
    },
    # ── 5. Blood Moon — gothic vampire crimson/black. Ravenloft horror ────
    "(Dark) Blood Moon": {
        "BG":"#100609","SURF":"#1c0c10","SURF2":"#241016","SURF3":"#30161e",
        "BORDER":"#6e4952","BORDER2":"#8a3048",
        "TEXT":"#f5e0e4","TEXT2":"#c890a0","TEXT3":"#9d7f8b",
        "GOLD":"#c89040","GOLD2":"#e8b060",
        "INDIGO":"#d75f77","IND2":"#f85878",
        "TEAL":"#209888","TEAL2":"#40c8b0",
        "CRIMSON":"#f3445d","CRIM2":"#ff5068",
        "PURPLE":"#a96fcc","PURP2":"#b37fd2",
        "AMBER":"#d87828","AMBE2":"#f89848",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#37222f",
    },
    # ── 6. Frostspire — icy blue/white winter. Frost giant peaks ──────────
    "(Dark) Frostspire": {
        "BG":"#060a12","SURF":"#0c1420","SURF2":"#121c2c","SURF3":"#182438",
        "BORDER":"#40566b","BORDER2":"#406890",
        "TEXT":"#e8f0f8","TEXT2":"#98b8d0","TEXT3":"#7a8ea0",
        "GOLD":"#c8b060","GOLD2":"#e8d080",
        "INDIGO":"#438ee2","IND2":"#68b0f8",
        "TEAL":"#20b8c8","TEAL2":"#48e0f0",
        "CRIMSON":"#e46262","CRIM2":"#f87878",
        "PURPLE":"#8e81d1","PURP2":"#988cd5",
        "AMBER":"#d89840","AMBE2":"#f8b860",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#1b2c44",
    },
    # ── 7. Cinderveil — volcanic orange/black. Molten, infernal ───────────
    "(Dark) Cinderveil": {
        "BG":"#100804","SURF":"#1c1008","SURF2":"#241608","SURF3":"#301c0a",
        "BORDER":"#724b33","BORDER2":"#985018",
        "TEXT":"#f8ecd8","TEXT2":"#d0a878","TEXT3":"#a1835e",
        "GOLD":"#e89818","GOLD2":"#ffc040",
        "INDIGO":"#e85818","IND2":"#ff8848",
        "TEAL":"#189888","TEAL2":"#38c8a8",
        "CRIMSON":"#eb5555","CRIM2":"#ed6d6d",
        "PURPLE":"#a37ca3","PURP2":"#ad8aad",
        "AMBER":"#f8a828","AMBE2":"#ffc858",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#3b2420",
    },
    # ── 8. Tavern Hearth — warm aged wood + firelight. Cozy, welcoming ────
    "(Dark) Tavern Hearth": {
        "BG":"#140d08","SURF":"#1e140c","SURF2":"#281c12","SURF3":"#322418",
        "BORDER":"#655241","BORDER2":"#785030",
        "TEXT":"#f5e8d0","TEXT2":"#c8a878","TEXT3":"#a48970",
        "GOLD":"#e8a838","GOLD2":"#ffc858",
        "INDIGO":"#cd7b31","IND2":"#e89850",
        "TEAL":"#6d9a6d","TEAL2":"#68a068",
        "CRIMSON":"#dd6e5f","CRIM2":"#df7b6e",
        "PURPLE":"#a386a3","PURP2":"#aa8faa",
        "AMBER":"#f0a828","AMBE2":"#ffc858",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#352925",
    },
    # ── 9. Mossgrove — lighter, earthy olive-green forest ────────────────
    "(Dark) Mossgrove": {
        "BG":"#0e120a","SURF":"#161c10","SURF2":"#1e2616","SURF3":"#26301c",
        "BORDER":"#4e5b3e","BORDER2":"#5c7038",
        "TEXT":"#e8f0d8","TEXT2":"#a8c088","TEXT3":"#8e9c72",
        "GOLD":"#b8a038","GOLD2":"#d8c058",
        "INDIGO":"#8b9e42","IND2":"#a0b858",
        "TEAL":"#4ea582","TEAL2":"#68c098",
        "CRIMSON":"#d47e71","CRIM2":"#d68579",
        "PURPLE":"#9b90b3","PURP2":"#a195b7",
        "AMBER":"#c88838","AMBE2":"#e8a858",
        "GREEN":"#2faa55","GREEN2":"#48d470",
        "PANELDK":"#272c26",
    },
    # ── 10. Gearworks — artificer's workshop. Brass, copper, gunmetal ─────
    "(Dark) Gearworks": {
        "BG":"#0e1012","SURF":"#161a1e","SURF2":"#1e242a","SURF3":"#262e36",
        "BORDER":"#51575e","BORDER2":"#605038",
        "TEXT":"#f0ece0","TEXT2":"#b8a888","TEXT3":"#9e9387",
        "GOLD":"#c88838","GOLD2":"#e8a858",
        "INDIGO":"#759ab8","IND2":"#70a0c8",
        "TEAL":"#3da694","TEAL2":"#58c0a8",
        "CRIMSON":"#e1776a","CRIM2":"#e37e72",
        "PURPLE":"#9b90b4","PURP2":"#a095b7",
        "AMBER":"#d89838","AMBE2":"#f8b858",
        "GREEN":"#2fab55","GREEN2":"#48d470",
        "PANELDK":"#212c3a",
    },
    # ── 11. Hallowed Stone — church slate grey + gold. Temple and vestry ──
    "(Dark) Hallowed Stone": {
        "BG":"#0e1014","SURF":"#161a20","SURF2":"#1e242c","SURF3":"#262e38",
        "BORDER":"#4f5763","BORDER2":"#586478",
        "TEXT":"#e8e8f0","TEXT2":"#a8b0c0","TEXT3":"#8f95a1",
        "GOLD":"#d8b840","GOLD2":"#f8d868",
        "INDIGO":"#8996b5","IND2":"#8898c0",
        "TEAL":"#3da78c","TEAL2":"#58c0a0",
        "CRIMSON":"#d08080","CRIM2":"#d38585",
        "PURPLE":"#a08eb7","PURP2":"#a493ba",
        "AMBER":"#c89840","AMBE2":"#e8b860",
        "GREEN":"#2fab55","GREEN2":"#48d470",
        "PANELDK":"#262b3a",
    },
    # ── 12. Underdark — Bioluminescent violet fungal glow on true black. Deep, alien, subterranean ──
    "(Dark) Underdark": {
        "BG":"#120e14","SURF":"#1c1620","SURF2":"#241c29","SURF3":"#2f2534",
        "BORDER":"#6b5676","BORDER2":"#704785",
        "TEXT":"#eeebef","TEXT2":"#bbacc3","TEXT3":"#9c8fa3",
        "GOLD":"#b98915","GOLD2":"#c49016",
        "INDIGO":"#c66be5","IND2":"#cb78e7",
        "TEAL":"#28a192","TEAL2":"#2bab99",
        "CRIMSON":"#e860a3","CRIM2":"#ea6fac",
        "PURPLE":"#ab79e6","PURP2":"#b284e7",
        "AMBER":"#c48313","AMBE2":"#cf8b14",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#332244",
    },
    # ── 13. Astral Sea — Cosmic navy-black speckled with starlight blue and silver. Vast, serene, otherworldly ──
    "(Dark) Astral Sea": {
        "BG":"#0e0f14","SURF":"#161820","SURF2":"#1c1f29","SURF3":"#252834",
        "BORDER":"#565c76","BORDER2":"#475485",
        "TEXT":"#ebecef","TEXT2":"#acb1c3","TEXT3":"#8f93a3",
        "GOLD":"#af8c19","GOLD2":"#ba951b",
        "INDIGO":"#688ee6","IND2":"#7598e9",
        "TEAL":"#299eaf","TEAL2":"#2ca7bb",
        "CRIMSON":"#e6677c","CRIM2":"#e97588",
        "PURPLE":"#9d7fe4","PURP2":"#a58ae6",
        "AMBER":"#b88917","AMBE2":"#c49118",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#202a45",
    },
    # ── 14. Nine Hells — Brimstone and ash — sulfur, ember-red, scorched black. Infernal bureaucracy and fire ──
    "(Dark) Nine Hells": {
        "BG":"#140e0e","SURF":"#201716","SURF2":"#291e1c","SURF3":"#342725",
        "BORDER":"#765a56","BORDER2":"#855047",
        "TEXT":"#efeceb","TEXT2":"#c3afac","TEXT3":"#a3928f",
        "GOLD":"#ae8f13","GOLD2":"#b79714",
        "INDIGO":"#8a9a2c","IND2":"#92a22f",
        "TEAL":"#db7656","TEAL2":"#de8164",
        "CRIMSON":"#ec6963","CRIM2":"#ed7671",
        "PURPLE":"#cc6ed5","PURP2":"#d07ad8",
        "AMBER":"#d08011","AMBE2":"#da8712",
        "GREEN":"#2ea854","GREEN2":"#48d470",
        "PANELDK":"#282d23",
    },
    # ── 15. Kraken's Depth — Crushing oceanic black-teal with bioluminescent cyan. Deep-sea pressure and dread ──
    "(Dark) Kraken's Depth": {
        "BG":"#0e1214","SURF":"#161e20","SURF2":"#1c2629","SURF3":"#253134",
        "BORDER":"#567076","BORDER2":"#477885",
        "TEXT":"#ebeeef","TEXT2":"#acbec3","TEXT3":"#8f9fa3",
        "GOLD":"#ba921e","GOLD2":"#c29720",
        "INDIGO":"#27a3cf","IND2":"#2aa9d6",
        "TEAL":"#24a8a4","TEAL2":"#25aea9",
        "CRIMSON":"#e57867","CRIM2":"#e68171",
        "PURPLE":"#9a8dde","PURP2":"#9f93e0",
        "AMBER":"#c68d19","AMBE2":"#ce9219",
        "GREEN":"#2fad56","GREEN2":"#48d470",
        "PANELDK":"#182e3d",
    },
    # ── 16. Storm Giant's Eye — Slate-grey storm clouds shot through with lightning gold. Tempest and thunderheads ──
    "(Dark) Storm Giant's Eye": {
        "BG":"#0e1014","SURF":"#161920","SURF2":"#1c2029","SURF3":"#252a34",
        "BORDER":"#566176","BORDER2":"#475c85",
        "TEXT":"#ebecef","TEXT2":"#acb4c3","TEXT3":"#8f96a3",
        "GOLD":"#a99115","GOLD2":"#b39816",
        "INDIGO":"#5b94dc","IND2":"#689cdf",
        "TEAL":"#32a0ab","TEAL2":"#34a8b4",
        "CRIMSON":"#e56c75","CRIM2":"#e77882",
        "PURPLE":"#9686dc","PURP2":"#9e8fde",
        "AMBER":"#b48d0e","AMBE2":"#bd940f",
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
        "TEXT":"#282e3b","TEXT2":"#495162","TEXT3":"#525866",
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
        "TEXT":"#312d1b","TEXT2":"#544f33","TEXT3":"#554f36",
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
        "TEXT":"#182815","TEXT2":"#324c2f","TEXT3":"#3b5736",
        "GOLD":"#6e4c14","GOLD2":"#614311",
        "INDIGO":"#693c9c","IND2":"#5d348a",
        "TEAL":"#1c5e3d","TEAL2":"#185235",
        "CRIMSON":"#952c46","CRIM2":"#83263e",
        "PURPLE":"#6e3c92","PURP2":"#613481",
        "AMBER":"#774814","AMBE2":"#683f11",
        "GREEN":"#285e1f","GREEN2":"#23531c",
        "PANELDK":"#26203c",
    },
    # ── 5. Coastal Tide — Pale seafoam and sea-glass blue-green. Salt air, tidepools, driftwood ──
    "(Light) Coastal Tide": {
        "BG":"#ecf0f1","SURF":"#dde6e7","SURF2":"#ccdadc","SURF3":"#b6cbce",
        "BORDER":"#81adb1","BORDER2":"#54a2ab",
        "TEXT":"#152628","TEXT2":"#2f494c","TEXT3":"#385659",
        "GOLD":"#6a4d16","GOLD2":"#5c4414",
        "INDIGO":"#255771","IND2":"#214c62",
        "TEAL":"#1b5b59","TEAL2":"#17504f",
        "CRIMSON":"#903324","CRIM2":"#7f2d20",
        "PURPLE":"#59429c","PURP2":"#4e3a88",
        "AMBER":"#7c4414","AMBE2":"#6c3c12",
        "GREEN":"#235c49","GREEN2":"#1f5040",
        "PANELDK":"#192533",
    },
    # ── 6. Rose Chantry — Soft blush parchment with burgundy accents. A temple of healing and devotion ──
    "(Light) Rose Chantry": {
        "BG":"#f1eced","SURF":"#e7dddf","SURF2":"#dccccf","SURF3":"#ceb6bb",
        "BORDER":"#b1818a","BORDER2":"#ab5465",
        "TEXT":"#281519","TEXT2":"#4c2f34","TEXT3":"#624148",
        "GOLD":"#614614","GOLD2":"#553c12",
        "INDIGO":"#773160","IND2":"#672a53",
        "TEAL":"#205347","TEAL2":"#1b483d",
        "CRIMSON":"#8d2130","CRIM2":"#7a1d29",
        "PURPLE":"#732f73","PURP2":"#642964",
        "AMBER":"#753b15","AMBE2":"#653312",
        "GREEN":"#235433","GREEN2":"#1e482c",
        "PANELDK":"#2a1e30",
    },
    # ── 7. Desert Oasis — Warm sand and terracotta with a turquoise spring. Sun-baked stone, palm shade ──
    "(Light) Desert Oasis": {
        "BG":"#f1eeec","SURF":"#e7e1dd","SURF2":"#dcd3cc","SURF3":"#cec1b6",
        "BORDER":"#b19781","BORDER2":"#ab7d54",
        "TEXT":"#281e15","TEXT2":"#4c3c2f","TEXT3":"#5e4d3d",
        "GOLD":"#664b11","GOLD2":"#58420e",
        "INDIGO":"#225661","IND2":"#1e4b55",
        "TEAL":"#195952","TEAL2":"#164d48",
        "CRIMSON":"#893420","CRIM2":"#782e1c",
        "PURPLE":"#6c3b83","PURP2":"#5e3373",
        "AMBER":"#77420f","AMBE2":"#683a0d",
        "GREEN":"#3a5724","GREEN2":"#324c1f",
        "PANELDK":"#182530",
    },
    # ── 8. Frostlight — Pale icy blue-white, crisp and clean. Glacier peaks and winter daylight ──
    "(Light) Frostlight": {
        "BG":"#eceff1","SURF":"#dde3e7","SURF2":"#ccd6dc","SURF3":"#b6c5ce",
        "BORDER":"#81a0b1","BORDER2":"#548bab",
        "TEXT":"#152128","TEXT2":"#2f414c","TEXT3":"#3d525e",
        "GOLD":"#604d18","GOLD2":"#544315",
        "INDIGO":"#304c90","IND2":"#2a437d",
        "TEAL":"#1f565f","TEAL2":"#1c4b53",
        "CRIMSON":"#8f2a3b","CRIM2":"#7e2433",
        "PURPLE":"#4e419e","PURP2":"#43398b",
        "AMBER":"#704618","AMBE2":"#613d15",
        "GREEN":"#265846","GREEN2":"#214d3d",
        "PANELDK":"#1b2339",
    },
    # ── 9. Harvest Gold — Warm amber and russet autumn tones. Harvest festival, hearth-bread, falling leaves ──
    "(Light) Harvest Gold": {
        "BG":"#f1efec","SURF":"#e7e2dd","SURF2":"#dcd5cc","SURF3":"#cec4b6",
        "BORDER":"#b19d81","BORDER2":"#ab8754",
        "TEXT":"#282015","TEXT2":"#4c402f","TEXT3":"#5d4f3c",
        "GOLD":"#694c11","GOLD2":"#5c420f",
        "INDIGO":"#33527e","IND2":"#2d476d",
        "TEAL":"#1e5a4f","TEAL2":"#1a4f45",
        "CRIMSON":"#8f321e","CRIM2":"#7e2b1b",
        "PURPLE":"#713a83","PURP2":"#633373",
        "AMBER":"#7e410e","AMBE2":"#6d390c",
        "GREEN":"#3a5922","GREEN2":"#324e1e",
        "PANELDK":"#1c2435",
    },
    # ── 10. Sky Citadel — Pale sky blue with gilded accents. A cloud giant's floating fortress ──
    "(Light) Sky Citadel": {
        "BG":"#eceff1","SURF":"#dde2e7","SURF2":"#ccd5dc","SURF3":"#b6c3ce",
        "BORDER":"#819cb1","BORDER2":"#5485ab",
        "TEXT":"#152028","TEXT2":"#2f3f4c","TEXT3":"#3d505e",
        "GOLD":"#5e4c16","GOLD2":"#514313",
        "INDIGO":"#254f81","IND2":"#204570",
        "TEAL":"#20565a","TEAL2":"#1b4b4e",
        "CRIMSON":"#8d2d29","CRIM2":"#7b2724",
        "PURPLE":"#524097","PURP2":"#473883",
        "AMBER":"#6c4617","AMBE2":"#5d3d14",
        "GREEN":"#275742","GREEN2":"#224c39",
        "PANELDK":"#192437",
    },

}
