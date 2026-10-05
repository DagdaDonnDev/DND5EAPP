pragma Singleton
import QtQuick

// Same 26-palette theme system as ui_desktop's style/theme.py (THEMES
// dict, values transcribed programmatically to avoid manual-copy
// error) plus its Small/Medium/Large font-scale factors, so the two
// UIs share the exact same visual identity even though nothing else
// about their code is shared. A singleton's properties are still real
// QML properties -- every file that binds to e.g. Theme.bg re-renders
// automatically the moment applyTheme()/applyFontScale() reassigns it,
// with no other file needing to change.
QtObject {
    id: root

    property string currentThemeName: "(Dark) Obsidian"
    property string currentFontScale: "Medium (default)"

    property color bg: "#0d0f18"
    property color surf: "#161922"
    property color surf2: "#1c2030"
    property color surf3: "#242840"
    property color border: "#50556d"
    property color border2: "#4a5890"
    property color text: "#eae8f5"
    property color text2: "#a8a4c8"
    property color text3: "#8f8da8"
    property color gold: "#e0b030"
    property color gold2: "#f8d060"
    property color indigo: "#5878f8"
    property color indigo2: "#90a8ff"
    property color teal: "#18c090"
    property color teal2: "#28e8b0"
    property color crimson: "#e24f5d"
    property color crimson2: "#e97782"
    property color purple: "#a064ea"
    property color purple2: "#b384ee"
    property color amber: "#e89828"
    property color amber2: "#f8c048"
    property color green: "#2ea854"
    property color green2: "#48d470"
    property color paneldk: "#212949"

    readonly property var _palettes: ({
        "(Dark) Obsidian": {"bg": "#0d0f18", "surf": "#161922", "surf2": "#1c2030", "surf3": "#242840", "border": "#50556d", "border2": "#4a5890", "text": "#eae8f5", "text2": "#a8a4c8", "text3": "#8f8da8", "gold": "#e0b030", "gold2": "#f8d060", "indigo": "#5878f8", "indigo2": "#90a8ff", "teal": "#18c090", "teal2": "#28e8b0", "crimson": "#e24f5d", "crimson2": "#e97782", "purple": "#a064ea", "purple2": "#b384ee", "amber": "#e89828", "amber2": "#f8c048", "green": "#2ea854", "green2": "#48d470", "paneldk": "#212949"},
        "(Dark) Dragon's Hoard": {"bg": "#060d0a", "surf": "#0c1a12", "surf2": "#12241a", "surf3": "#182e22", "border": "#3b5c47", "border2": "#286040", "text": "#e8f5e0", "text2": "#90c898", "text3": "#739979", "gold": "#e8a820", "gold2": "#ffd050", "indigo": "#20b860", "indigo2": "#40e880", "teal": "#18b8a0", "teal2": "#30e0c0", "crimson": "#e84828", "crimson2": "#f87858", "purple": "#a066d9", "purple2": "#b284e1", "amber": "#e8a820", "amber2": "#ffd050", "green": "#2ea854", "green2": "#48d470", "paneldk": "#17352d"},
        "(Dark) Shadowfell": {"bg": "#080610", "surf": "#100e1c", "surf2": "#181528", "surf3": "#201c34", "border": "#53506a", "border2": "#4a4470", "text": "#d8d0f0", "text2": "#9888c8", "text3": "#8882a0", "gold": "#c8a838", "gold2": "#e8c858", "indigo": "#7a6cdb", "indigo2": "#a090f8", "teal": "#4898c8", "teal2": "#70c0f0", "crimson": "#cc5183", "crimson2": "#d6749c", "purple": "#9068e0", "purple2": "#c098ff", "amber": "#c89838", "amber2": "#e8c050", "green": "#2ea854", "green2": "#48d470", "paneldk": "#272743"},
        "(Dark) Feywild": {"bg": "#080820", "surf": "#0e1030", "surf2": "#141640", "surf3": "#1a1c52", "border": "#4c5086", "border2": "#303898", "text": "#f0ecff", "text2": "#b0a8e8", "text3": "#8b84ac", "gold": "#e8c840", "gold2": "#ffe870", "indigo": "#28c8d8", "indigo2": "#60e8f8", "teal": "#18c898", "teal2": "#28f0c0", "crimson": "#e83888", "crimson2": "#f870b8", "purple": "#ab56e9", "purple2": "#cb6aff", "amber": "#e8a830", "amber2": "#ffd060", "green": "#2ea854", "green2": "#48d470", "paneldk": "#183843"},
        "(Dark) Blood Moon": {"bg": "#100609", "surf": "#1c0c10", "surf2": "#241016", "surf3": "#30161e", "border": "#6e4952", "border2": "#8a3048", "text": "#f5e0e4", "text2": "#c890a0", "text3": "#9b7d89", "gold": "#c89040", "gold2": "#e8b060", "indigo": "#d24d68", "indigo2": "#f85878", "teal": "#209888", "teal2": "#40c8b0", "crimson": "#f01838", "crimson2": "#ff5068", "purple": "#a262c8", "purple2": "#b37fd2", "amber": "#d87828", "amber2": "#f89848", "green": "#2ea854", "green2": "#48d470", "paneldk": "#37222f"},
        "(Dark) Frostspire": {"bg": "#060a12", "surf": "#0c1420", "surf2": "#121c2c", "surf3": "#182438", "border": "#40566b", "border2": "#406890", "text": "#e8f0f8", "text2": "#98b8d0", "text3": "#798d9f", "gold": "#c8b060", "gold2": "#e8d080", "indigo": "#3888e0", "indigo2": "#68b0f8", "teal": "#20b8c8", "teal2": "#48e0f0", "crimson": "#e04848", "crimson2": "#f87878", "purple": "#8173cc", "purple2": "#988cd5", "amber": "#d89840", "amber2": "#f8b860", "green": "#2ea854", "green2": "#48d470", "paneldk": "#1b2c44"},
        "(Dark) Cinderveil": {"bg": "#100804", "surf": "#1c1008", "surf2": "#241608", "surf3": "#301c0a", "border": "#724b33", "border2": "#985018", "text": "#f8ecd8", "text2": "#d0a878", "text3": "#a0825d", "gold": "#e89818", "gold2": "#ffc040", "indigo": "#e85818", "indigo2": "#ff8848", "teal": "#189888", "teal2": "#38c8a8", "crimson": "#e83e3e", "crimson2": "#ed6d6d", "purple": "#9b709b", "purple2": "#ad8aad", "amber": "#f8a828", "amber2": "#ffc858", "green": "#2ea854", "green2": "#48d470", "paneldk": "#3b2420"},
        "(Dark) Tavern Hearth": {"bg": "#140d08", "surf": "#1e140c", "surf2": "#281c12", "surf3": "#322418", "border": "#655241", "border2": "#785030", "text": "#f5e8d0", "text2": "#c8a878", "text3": "#a3886f", "gold": "#e8a838", "gold2": "#ffc858", "indigo": "#c87830", "indigo2": "#e89850", "teal": "#5f895f", "teal2": "#68a068", "crimson": "#d75746", "crimson2": "#df7b6e", "purple": "#977697", "purple2": "#aa8faa", "amber": "#f0a828", "amber2": "#ffc858", "green": "#2ea854", "green2": "#48d470", "paneldk": "#352925"},
        "(Dark) Mossgrove": {"bg": "#0e120a", "surf": "#161c10", "surf2": "#1e2616", "surf3": "#26301c", "border": "#4e5b3e", "border2": "#5c7038", "text": "#e8f0d8", "text2": "#a8c088", "text3": "#8b996f", "gold": "#b8a038", "gold2": "#d8c058", "indigo": "#798939", "indigo2": "#a0b858", "teal": "#489878", "teal2": "#68c098", "crimson": "#cc6556", "crimson2": "#d68579", "purple": "#8a7da6", "purple2": "#a195b7", "amber": "#c88838", "amber2": "#e8a858", "green": "#2ea854", "green2": "#48d470", "paneldk": "#272c26"},
        "(Dark) Gearworks": {"bg": "#0e1012", "surf": "#161a1e", "surf2": "#1e242a", "surf3": "#262e36", "border": "#51575e", "border2": "#605038", "text": "#f0ece0", "text2": "#b8a888", "text3": "#9d9286", "gold": "#c88838", "gold2": "#e8a858", "indigo": "#5a86aa", "indigo2": "#70a0c8", "teal": "#389888", "teal2": "#58c0a8", "crimson": "#db594a", "crimson2": "#e37e72", "purple": "#8a7da7", "purple2": "#a095b7", "amber": "#d89838", "amber2": "#f8b858", "green": "#2ea854", "green2": "#48d470", "paneldk": "#212c3a"},
        "(Dark) Hallowed Stone": {"bg": "#0e1014", "surf": "#161a20", "surf2": "#1e242c", "surf3": "#262e38", "border": "#4f5763", "border2": "#586478", "text": "#e8e8f0", "text2": "#a8b0c0", "text3": "#8e94a0", "gold": "#d8b840", "gold2": "#f8d868", "indigo": "#7281a7", "indigo2": "#8898c0", "teal": "#389880", "teal2": "#58c0a0", "crimson": "#c76767", "crimson2": "#d38585", "purple": "#8f7aab", "purple2": "#a493ba", "amber": "#c89840", "amber2": "#e8b860", "green": "#2ea854", "green2": "#48d470", "paneldk": "#262b3a"},
        "(Dark) Underdark": {"bg": "#120e14", "surf": "#1c1620", "surf2": "#241c29", "surf3": "#2f2534", "border": "#6b5676", "border2": "#704785", "text": "#eeebef", "text2": "#bbacc3", "text3": "#9c8fa3", "gold": "#a77b13", "gold2": "#c49016", "indigo": "#bd52e1", "indigo2": "#cb78e7", "teal": "#249183", "teal2": "#2bab99", "crimson": "#e44192", "crimson2": "#ea6fac", "purple": "#9f66e2", "purple2": "#b284e7", "amber": "#b17611", "amber2": "#cf8b14", "green": "#2ea854", "green2": "#48d470", "paneldk": "#332244"},
        "(Dark) Astral Sea": {"bg": "#0e0f14", "surf": "#161820", "surf2": "#1c1f29", "surf3": "#252834", "border": "#565c76", "border2": "#475485", "text": "#ebecef", "text2": "#acb1c3", "text3": "#8f93a3", "gold": "#9e7f17", "gold2": "#ba951b", "indigo": "#537ee3", "indigo2": "#7598e9", "teal": "#258f9f", "teal2": "#2ca7bb", "crimson": "#e24c65", "crimson2": "#e97588", "purple": "#906ee0", "purple2": "#a58ae6", "amber": "#a67b15", "amber2": "#c49118", "green": "#2ea854", "green2": "#48d470", "paneldk": "#202a45"},
        "(Dark) Nine Hells": {"bg": "#140e0e", "surf": "#201716", "surf2": "#291e1c", "surf3": "#342725", "border": "#765a56", "border2": "#855047", "text": "#efeceb", "text2": "#c3afac", "text3": "#a3928f", "gold": "#9c8011", "gold2": "#b79714", "indigo": "#7c8a28", "indigo2": "#92a22f", "teal": "#d55f3a", "teal2": "#de8164", "crimson": "#e84b45", "crimson2": "#ed7671", "purple": "#c355ce", "purple2": "#d07ad8", "amber": "#ba720f", "amber2": "#da8712", "green": "#2ea854", "green2": "#48d470", "paneldk": "#282d23"},
        "(Dark) Kraken's Depth": {"bg": "#0e1214", "surf": "#161e20", "surf2": "#1c2629", "surf3": "#253134", "border": "#567076", "border2": "#477885", "text": "#ebeeef", "text2": "#acbec3", "text3": "#8f9fa3", "gold": "#a5811b", "gold2": "#c29720", "indigo": "#2390b7", "indigo2": "#2aa9d6", "teal": "#209591", "teal2": "#25aea9", "crimson": "#df5b47", "crimson2": "#e68171", "purple": "#8878d8", "purple2": "#9f93e0", "amber": "#af7c16", "amber2": "#ce9219", "green": "#2ea854", "green2": "#48d470", "paneldk": "#182e3d"},
        "(Dark) Storm Giant's Eye": {"bg": "#0e1014", "surf": "#161920", "surf2": "#1c2029", "surf3": "#252a34", "border": "#566176", "border2": "#475c85", "text": "#ebecef", "text2": "#acb4c3", "text3": "#8f96a3", "gold": "#988213", "gold2": "#b39816", "indigo": "#4384d7", "indigo2": "#689cdf", "teal": "#2d8f99", "teal2": "#34a8b4", "crimson": "#e0515c", "crimson2": "#e77882", "purple": "#8774d7", "purple2": "#9e8fde", "amber": "#a17e0d", "amber2": "#bd940f", "green": "#2ea854", "green2": "#48d470", "paneldk": "#1d2b43"},
        "(Light) Arcane Scroll": {"bg": "#f2edd8", "surf": "#e8e0c4", "surf2": "#ddd5b0", "surf3": "#cfc79a", "border": "#a69161", "border2": "#9a7840", "text": "#18100a", "text2": "#3a2808", "text3": "#6a4820", "gold": "#724707", "gold2": "#63400e", "indigo": "#1e3ea0", "indigo2": "#153eaa", "teal": "#0c5c3e", "teal2": "#0a512f", "crimson": "#8c1818", "crimson2": "#8f1414", "purple": "#5a1878", "purple2": "#6e1c98", "amber": "#734606", "amber2": "#683e0a", "green": "#195b2e", "green2": "#0e5221", "paneldk": "#171f39"},
        "(Light) Moonlit Vellum": {"bg": "#eef1f6", "surf": "#e2e7f0", "surf2": "#d5dcea", "surf3": "#c7d0e2", "border": "#8f96a7", "border2": "#77829b", "text": "#282e3b", "text2": "#495162", "text3": "#535967", "gold": "#6c520c", "gold2": "#604a12", "indigo": "#2c4ba8", "indigo2": "#2e4999", "teal": "#0b644d", "teal2": "#0f5946", "crimson": "#a3273a", "crimson2": "#8f2938", "purple": "#6a3a9e", "purple2": "#643990", "amber": "#7f4b07", "amber2": "#6f450b", "green": "#1b6231", "green2": "#0f5924", "paneldk": "#19213a"},
        "(Light) Sunlit Meadow": {"bg": "#f3f0e2", "surf": "#e9e4cd", "surf2": "#ded6b3", "surf3": "#cfc596", "border": "#9f966e", "border2": "#8e814b", "text": "#312d1b", "text2": "#565135", "text3": "#585239", "gold": "#654a08", "gold2": "#584211", "indigo": "#354f81", "indigo2": "#324771", "teal": "#135a36", "teal2": "#174f32", "crimson": "#8e2f24", "crimson2": "#7b2d22", "purple": "#6d3e7b", "purple2": "#5c3867", "amber": "#6e490c", "amber2": "#5f410f", "green": "#195b2e", "green2": "#0e5221", "paneldk": "#1b2233"},
        "(Light) Elven Grove": {"bg": "#edf1ec", "surf": "#dee7dd", "surf2": "#cedccc", "surf3": "#b9ceb6", "border": "#87b181", "border2": "#60ab54", "text": "#182815", "text2": "#324c2f", "text3": "#466241", "gold": "#7c5616", "gold2": "#614311", "indigo": "#7643b0", "indigo2": "#5d348a", "teal": "#1f6944", "teal2": "#185235", "crimson": "#a7314e", "crimson2": "#83263e", "purple": "#7c43a4", "purple2": "#613481", "amber": "#865116", "amber2": "#683f11", "green": "#2d6a23", "green2": "#23531c", "paneldk": "#26203c"},
        "(Light) Coastal Tide": {"bg": "#ecf0f1", "surf": "#dde6e7", "surf2": "#ccdadc", "surf3": "#b6cbce", "border": "#81adb1", "border2": "#54a2ab", "text": "#152628", "text2": "#2f494c", "text3": "#415f62", "gold": "#775719", "gold2": "#5c4414", "indigo": "#2a627f", "indigo2": "#214c62", "teal": "#1e6764", "teal2": "#17504f", "crimson": "#a33929", "crimson2": "#7f2d20", "purple": "#644bb0", "purple2": "#4e3a88", "amber": "#8b4d17", "amber2": "#6c3c12", "green": "#276752", "green2": "#1f5040", "paneldk": "#192533"},
        "(Light) Rose Chantry": {"bg": "#f1eced", "surf": "#e7dddf", "surf2": "#dccccf", "surf3": "#ceb6bb", "border": "#b1818a", "border2": "#ab5465", "text": "#281519", "text2": "#4c2f34", "text3": "#624148", "gold": "#735218", "gold2": "#553c12", "indigo": "#8c3971", "indigo2": "#672a53", "teal": "#256253", "teal2": "#1b483d", "crimson": "#a52738", "crimson2": "#7a1d29", "purple": "#883788", "purple2": "#642964", "amber": "#894518", "amber2": "#653312", "green": "#29633c", "green2": "#1e482c", "paneldk": "#2a1e30"},
        "(Light) Desert Oasis": {"bg": "#f1eeec", "surf": "#e7e1dd", "surf2": "#dcd3cc", "surf3": "#cec1b6", "border": "#b19781", "border2": "#ab7d54", "text": "#281e15", "text2": "#4c3c2f", "text3": "#625141", "gold": "#745613", "gold2": "#58420e", "indigo": "#27626e", "indigo2": "#1e4b55", "teal": "#1d655e", "teal2": "#164d48", "crimson": "#9c3c25", "crimson2": "#782e1c", "purple": "#7b4396", "purple2": "#5e3373", "amber": "#884c11", "amber2": "#683a0d", "green": "#426429", "green2": "#324c1f", "paneldk": "#182530"},
        "(Light) Frostlight": {"bg": "#eceff1", "surf": "#dde3e7", "surf2": "#ccd6dc", "surf3": "#b6c5ce", "border": "#81a0b1", "border2": "#548bab", "text": "#152128", "text2": "#2f414c", "text3": "#415662", "gold": "#6f581c", "gold2": "#544315", "indigo": "#3757a4", "indigo2": "#2a437d", "teal": "#24636d", "teal2": "#1c4b53", "crimson": "#a43043", "crimson2": "#7e2433", "purple": "#594ab5", "purple2": "#43398b", "amber": "#7f501b", "amber2": "#613d15", "green": "#2b6550", "green2": "#214d3d", "paneldk": "#1b2339"},
        "(Light) Harvest Gold": {"bg": "#f1efec", "surf": "#e7e2dd", "surf2": "#dcd5cc", "surf3": "#cec4b6", "border": "#b19d81", "border2": "#ab8754", "text": "#282015", "text2": "#4c402f", "text3": "#625441", "gold": "#775613", "gold2": "#5c420f", "indigo": "#3a5d8e", "indigo2": "#2d476d", "teal": "#226659", "teal2": "#1a4f45", "crimson": "#a23822", "crimson2": "#7e2b1b", "purple": "#804294", "purple2": "#633373", "amber": "#8e4a10", "amber2": "#6d390c", "green": "#416526", "green2": "#324e1e", "paneldk": "#1c2435"},
        "(Light) Sky Citadel": {"bg": "#eceff1", "surf": "#dde2e7", "surf2": "#ccd5dc", "surf3": "#b6c3ce", "border": "#819cb1", "border2": "#5485ab", "text": "#152028", "text2": "#2f3f4c", "text3": "#415462", "gold": "#6c5819", "gold2": "#514313", "indigo": "#2b5c95", "indigo2": "#204570", "teal": "#256368", "teal2": "#1b4b4e", "crimson": "#a2332f", "crimson2": "#7b2724", "purple": "#5e4aae", "purple2": "#473883", "amber": "#7c511a", "amber2": "#5d3d14", "green": "#2d644b", "green2": "#224c39", "paneldk": "#192437"},
    })

    readonly property var themeNames: Object.keys(_palettes)

    function applyTheme(name) {
        var p = _palettes[name]
        if (!p) return
        currentThemeName = name
        bg = p.bg; surf = p.surf; surf2 = p.surf2; surf3 = p.surf3
        border = p.border; border2 = p.border2
        text = p.text; text2 = p.text2; text3 = p.text3
        gold = p.gold; gold2 = p.gold2
        indigo = p.indigo; indigo2 = p.indigo2
        teal = p.teal; teal2 = p.teal2
        crimson = p.crimson; crimson2 = p.crimson2
        purple = p.purple; purple2 = p.purple2
        amber = p.amber; amber2 = p.amber2
        green = p.green; green2 = p.green2
        paneldk = p.paneldk
    }

    // ── Font scale (Small/Medium/Large) ─────────────────────────────────
    readonly property var _fontScales: ({"Small": 0.85, "Medium (default)": 1.0, "Large": 1.15})
    readonly property var fontScaleNames: ["Small", "Medium (default)", "Large"]

    property real _scale: 1.0
    property int fsSmall: 13
    property int fsBody: 15
    property int fsHead: 20
    property int fsTitle: 24

    function applyFontScale(name) {
        var s = _fontScales[name]
        if (s === undefined) return
        currentFontScale = name
        _scale = s
        fsSmall = Math.max(1, Math.round(13 * s))
        fsBody = Math.max(1, Math.round(15 * s))
        fsHead = Math.max(1, Math.round(20 * s))
        fsTitle = Math.max(1, Math.round(24 * s))
    }
}
