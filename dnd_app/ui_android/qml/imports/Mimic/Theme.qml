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
    property color text3: "#918faa"
    property color gold: "#e0b030"
    property color gold2: "#f8d060"
    property color indigo: "#6f8bf9"
    property color indigo2: "#90a8ff"
    property color teal: "#18c090"
    property color teal2: "#28e8b0"
    property color crimson: "#e66a75"
    property color crimson2: "#e97782"
    property color purple: "#ad78ed"
    property color purple2: "#b384ee"
    property color amber: "#e89828"
    property color amber2: "#f8c048"
    property color green: "#2ea854"
    property color green2: "#48d470"
    property color paneldk: "#212949"

    readonly property var _palettes: ({
        "(Dark) Obsidian": {"bg": "#0d0f18", "surf": "#161922", "surf2": "#1c2030", "surf3": "#242840", "border": "#50556d", "border2": "#4a5890", "text": "#eae8f5", "text2": "#a8a4c8", "text3": "#918faa", "gold": "#e0b030", "gold2": "#f8d060", "indigo": "#6f8bf9", "indigo2": "#90a8ff", "teal": "#18c090", "teal2": "#28e8b0", "crimson": "#e66a75", "crimson2": "#e97782", "purple": "#ad78ed", "purple2": "#b384ee", "amber": "#e89828", "amber2": "#f8c048", "green": "#2ea854", "green2": "#48d470", "paneldk": "#212949"},
        "(Dark) Dragon's Hoard": {"bg": "#060d0a", "surf": "#0c1a12", "surf2": "#12241a", "surf3": "#182e22", "border": "#3b5c47", "border2": "#286040", "text": "#e8f5e0", "text2": "#90c898", "text3": "#779d7d", "gold": "#e8a820", "gold2": "#ffd050", "indigo": "#20b860", "indigo2": "#40e880", "teal": "#18b8a0", "teal2": "#30e0c0", "crimson": "#ec694e", "crimson2": "#f87858", "purple": "#ad7cde", "purple2": "#b284e1", "amber": "#e8a820", "amber2": "#ffd050", "green": "#2ea854", "green2": "#48d470", "paneldk": "#17352d"},
        "(Dark) Shadowfell": {"bg": "#080610", "surf": "#100e1c", "surf2": "#181528", "surf3": "#201c34", "border": "#53506a", "border2": "#4a4470", "text": "#d8d0f0", "text2": "#9888c8", "text3": "#8b85a3", "gold": "#c8a838", "gold2": "#e8c858", "indigo": "#877adf", "indigo2": "#a090f8", "teal": "#4898c8", "teal2": "#70c0f0", "crimson": "#d1638f", "crimson2": "#d6749c", "purple": "#9873e2", "purple2": "#c098ff", "amber": "#c89838", "amber2": "#e8c050", "green": "#2ea854", "green2": "#48d470", "paneldk": "#272743"},
        "(Dark) Feywild": {"bg": "#080820", "surf": "#0e1030", "surf2": "#141640", "surf3": "#1a1c52", "border": "#4c5086", "border2": "#303898", "text": "#f0ecff", "text2": "#b0a8e8", "text3": "#8d86ae", "gold": "#e8c840", "gold2": "#ffe870", "indigo": "#28c8d8", "indigo2": "#60e8f8", "teal": "#18c898", "teal2": "#28f0c0", "crimson": "#eb5097", "crimson2": "#f870b8", "purple": "#b469eb", "purple2": "#cb6aff", "amber": "#e8a830", "amber2": "#ffd060", "green": "#2ea854", "green2": "#48d470", "paneldk": "#183843"},
        "(Dark) Blood Moon": {"bg": "#100609", "surf": "#1c0c10", "surf2": "#241016", "surf3": "#30161e", "border": "#6e4952", "border2": "#8a3048", "text": "#f5e0e4", "text2": "#c890a0", "text3": "#9d7f8b", "gold": "#c89040", "gold2": "#e8b060", "indigo": "#d75f77", "indigo2": "#f85878", "teal": "#209888", "teal2": "#40c8b0", "crimson": "#f3445d", "crimson2": "#ff5068", "purple": "#a96fcc", "purple2": "#b37fd2", "amber": "#d87828", "amber2": "#f89848", "green": "#2ea854", "green2": "#48d470", "paneldk": "#37222f"},
        "(Dark) Frostspire": {"bg": "#060a12", "surf": "#0c1420", "surf2": "#121c2c", "surf3": "#182438", "border": "#40566b", "border2": "#406890", "text": "#e8f0f8", "text2": "#98b8d0", "text3": "#7a8ea0", "gold": "#c8b060", "gold2": "#e8d080", "indigo": "#438ee2", "indigo2": "#68b0f8", "teal": "#20b8c8", "teal2": "#48e0f0", "crimson": "#e46262", "crimson2": "#f87878", "purple": "#8e81d1", "purple2": "#988cd5", "amber": "#d89840", "amber2": "#f8b860", "green": "#2ea854", "green2": "#48d470", "paneldk": "#1b2c44"},
        "(Dark) Cinderveil": {"bg": "#100804", "surf": "#1c1008", "surf2": "#241608", "surf3": "#301c0a", "border": "#724b33", "border2": "#985018", "text": "#f8ecd8", "text2": "#d0a878", "text3": "#a1835e", "gold": "#e89818", "gold2": "#ffc040", "indigo": "#e85818", "indigo2": "#ff8848", "teal": "#189888", "teal2": "#38c8a8", "crimson": "#eb5555", "crimson2": "#ed6d6d", "purple": "#a37ca3", "purple2": "#ad8aad", "amber": "#f8a828", "amber2": "#ffc858", "green": "#2ea854", "green2": "#48d470", "paneldk": "#3b2420"},
        "(Dark) Tavern Hearth": {"bg": "#140d08", "surf": "#1e140c", "surf2": "#281c12", "surf3": "#322418", "border": "#655241", "border2": "#785030", "text": "#f5e8d0", "text2": "#c8a878", "text3": "#a48970", "gold": "#e8a838", "gold2": "#ffc858", "indigo": "#cd7b31", "indigo2": "#e89850", "teal": "#6d9a6d", "teal2": "#68a068", "crimson": "#dd6e5f", "crimson2": "#df7b6e", "purple": "#a386a3", "purple2": "#aa8faa", "amber": "#f0a828", "amber2": "#ffc858", "green": "#2ea854", "green2": "#48d470", "paneldk": "#352925"},
        "(Dark) Mossgrove": {"bg": "#0e120a", "surf": "#161c10", "surf2": "#1e2616", "surf3": "#26301c", "border": "#4e5b3e", "border2": "#5c7038", "text": "#e8f0d8", "text2": "#a8c088", "text3": "#8e9c72", "gold": "#b8a038", "gold2": "#d8c058", "indigo": "#8b9e42", "indigo2": "#a0b858", "teal": "#4ea582", "teal2": "#68c098", "crimson": "#d47e71", "crimson2": "#d68579", "purple": "#9b90b3", "purple2": "#a195b7", "amber": "#c88838", "amber2": "#e8a858", "green": "#2faa55", "green2": "#48d470", "paneldk": "#272c26"},
        "(Dark) Gearworks": {"bg": "#0e1012", "surf": "#161a1e", "surf2": "#1e242a", "surf3": "#262e36", "border": "#51575e", "border2": "#605038", "text": "#f0ece0", "text2": "#b8a888", "text3": "#9e9387", "gold": "#c88838", "gold2": "#e8a858", "indigo": "#759ab8", "indigo2": "#70a0c8", "teal": "#3da694", "teal2": "#58c0a8", "crimson": "#e1776a", "crimson2": "#e37e72", "purple": "#9b90b4", "purple2": "#a095b7", "amber": "#d89838", "amber2": "#f8b858", "green": "#2fab55", "green2": "#48d470", "paneldk": "#212c3a"},
        "(Dark) Hallowed Stone": {"bg": "#0e1014", "surf": "#161a20", "surf2": "#1e242c", "surf3": "#262e38", "border": "#4f5763", "border2": "#586478", "text": "#e8e8f0", "text2": "#a8b0c0", "text3": "#8f95a1", "gold": "#d8b840", "gold2": "#f8d868", "indigo": "#8996b5", "indigo2": "#8898c0", "teal": "#3da78c", "teal2": "#58c0a0", "crimson": "#d08080", "crimson2": "#d38585", "purple": "#a08eb7", "purple2": "#a493ba", "amber": "#c89840", "amber2": "#e8b860", "green": "#2fab55", "green2": "#48d470", "paneldk": "#262b3a"},
        "(Dark) Underdark": {"bg": "#120e14", "surf": "#1c1620", "surf2": "#241c29", "surf3": "#2f2534", "border": "#6b5676", "border2": "#704785", "text": "#eeebef", "text2": "#bbacc3", "text3": "#9c8fa3", "gold": "#b98915", "gold2": "#c49016", "indigo": "#c66be5", "indigo2": "#cb78e7", "teal": "#28a192", "teal2": "#2bab99", "crimson": "#e860a3", "crimson2": "#ea6fac", "purple": "#ab79e6", "purple2": "#b284e7", "amber": "#c48313", "amber2": "#cf8b14", "green": "#2ea854", "green2": "#48d470", "paneldk": "#332244"},
        "(Dark) Astral Sea": {"bg": "#0e0f14", "surf": "#161820", "surf2": "#1c1f29", "surf3": "#252834", "border": "#565c76", "border2": "#475485", "text": "#ebecef", "text2": "#acb1c3", "text3": "#8f93a3", "gold": "#af8c19", "gold2": "#ba951b", "indigo": "#688ee6", "indigo2": "#7598e9", "teal": "#299eaf", "teal2": "#2ca7bb", "crimson": "#e6677c", "crimson2": "#e97588", "purple": "#9d7fe4", "purple2": "#a58ae6", "amber": "#b88917", "amber2": "#c49118", "green": "#2ea854", "green2": "#48d470", "paneldk": "#202a45"},
        "(Dark) Nine Hells": {"bg": "#140e0e", "surf": "#201716", "surf2": "#291e1c", "surf3": "#342725", "border": "#765a56", "border2": "#855047", "text": "#efeceb", "text2": "#c3afac", "text3": "#a3928f", "gold": "#ae8f13", "gold2": "#b79714", "indigo": "#8a9a2c", "indigo2": "#92a22f", "teal": "#db7656", "teal2": "#de8164", "crimson": "#ec6963", "crimson2": "#ed7671", "purple": "#cc6ed5", "purple2": "#d07ad8", "amber": "#d08011", "amber2": "#da8712", "green": "#2ea854", "green2": "#48d470", "paneldk": "#282d23"},
        "(Dark) Kraken's Depth": {"bg": "#0e1214", "surf": "#161e20", "surf2": "#1c2629", "surf3": "#253134", "border": "#567076", "border2": "#477885", "text": "#ebeeef", "text2": "#acbec3", "text3": "#8f9fa3", "gold": "#ba921e", "gold2": "#c29720", "indigo": "#27a3cf", "indigo2": "#2aa9d6", "teal": "#24a8a4", "teal2": "#25aea9", "crimson": "#e57867", "crimson2": "#e68171", "purple": "#9a8dde", "purple2": "#9f93e0", "amber": "#c68d19", "amber2": "#ce9219", "green": "#2fad56", "green2": "#48d470", "paneldk": "#182e3d"},
        "(Dark) Storm Giant's Eye": {"bg": "#0e1014", "surf": "#161920", "surf2": "#1c2029", "surf3": "#252a34", "border": "#566176", "border2": "#475c85", "text": "#ebecef", "text2": "#acb4c3", "text3": "#8f96a3", "gold": "#a99115", "gold2": "#b39816", "indigo": "#5b94dc", "indigo2": "#689cdf", "teal": "#32a0ab", "teal2": "#34a8b4", "crimson": "#e56c75", "crimson2": "#e77882", "purple": "#9686dc", "purple2": "#9e8fde", "amber": "#b48d0e", "amber2": "#bd940f", "green": "#2ea854", "green2": "#48d470", "paneldk": "#1d2b43"},
        "(Light) Arcane Scroll": {"bg": "#f2edd8", "surf": "#e8e0c4", "surf2": "#ddd5b0", "surf3": "#cfc79a", "border": "#a69161", "border2": "#9a7840", "text": "#18100a", "text2": "#3a2808", "text3": "#6a4820", "gold": "#724707", "gold2": "#63400e", "indigo": "#1e3ea0", "indigo2": "#153eaa", "teal": "#0c5c3e", "teal2": "#0a512f", "crimson": "#8c1818", "crimson2": "#8f1414", "purple": "#5a1878", "purple2": "#6e1c98", "amber": "#734606", "amber2": "#683e0a", "green": "#195b2e", "green2": "#0e5221", "paneldk": "#171f39"},
        "(Light) Moonlit Vellum": {"bg": "#eef1f6", "surf": "#e2e7f0", "surf2": "#d5dcea", "surf3": "#c7d0e2", "border": "#8f96a7", "border2": "#77829b", "text": "#282e3b", "text2": "#495162", "text3": "#525866", "gold": "#6c520c", "gold2": "#604a12", "indigo": "#2c4ba8", "indigo2": "#2e4999", "teal": "#0b644d", "teal2": "#0f5946", "crimson": "#a3273a", "crimson2": "#8f2938", "purple": "#6a3a9e", "purple2": "#643990", "amber": "#7f4b07", "amber2": "#6f450b", "green": "#1b6231", "green2": "#0f5924", "paneldk": "#19213a"},
        "(Light) Sunlit Meadow": {"bg": "#f3f0e2", "surf": "#e9e4cd", "surf2": "#ded6b3", "surf3": "#cfc596", "border": "#9f966e", "border2": "#8e814b", "text": "#312d1b", "text2": "#544f33", "text3": "#554f36", "gold": "#654a08", "gold2": "#584211", "indigo": "#354f81", "indigo2": "#324771", "teal": "#135a36", "teal2": "#174f32", "crimson": "#8e2f24", "crimson2": "#7b2d22", "purple": "#6d3e7b", "purple2": "#5c3867", "amber": "#6e490c", "amber2": "#5f410f", "green": "#195b2e", "green2": "#0e5221", "paneldk": "#1b2233"},
        "(Light) Elven Grove": {"bg": "#edf1ec", "surf": "#dee7dd", "surf2": "#cedccc", "surf3": "#b9ceb6", "border": "#87b181", "border2": "#60ab54", "text": "#182815", "text2": "#324c2f", "text3": "#3b5736", "gold": "#6e4c14", "gold2": "#614311", "indigo": "#693c9c", "indigo2": "#5d348a", "teal": "#1c5e3d", "teal2": "#185235", "crimson": "#952c46", "crimson2": "#83263e", "purple": "#6e3c92", "purple2": "#613481", "amber": "#774814", "amber2": "#683f11", "green": "#285e1f", "green2": "#23531c", "paneldk": "#26203c"},
        "(Light) Coastal Tide": {"bg": "#ecf0f1", "surf": "#dde6e7", "surf2": "#ccdadc", "surf3": "#b6cbce", "border": "#81adb1", "border2": "#54a2ab", "text": "#152628", "text2": "#2f494c", "text3": "#385659", "gold": "#6a4d16", "gold2": "#5c4414", "indigo": "#255771", "indigo2": "#214c62", "teal": "#1b5b59", "teal2": "#17504f", "crimson": "#903324", "crimson2": "#7f2d20", "purple": "#59429c", "purple2": "#4e3a88", "amber": "#7c4414", "amber2": "#6c3c12", "green": "#235c49", "green2": "#1f5040", "paneldk": "#192533"},
        "(Light) Rose Chantry": {"bg": "#f1eced", "surf": "#e7dddf", "surf2": "#dccccf", "surf3": "#ceb6bb", "border": "#b1818a", "border2": "#ab5465", "text": "#281519", "text2": "#4c2f34", "text3": "#624148", "gold": "#614614", "gold2": "#553c12", "indigo": "#773160", "indigo2": "#672a53", "teal": "#205347", "teal2": "#1b483d", "crimson": "#8d2130", "crimson2": "#7a1d29", "purple": "#732f73", "purple2": "#642964", "amber": "#753b15", "amber2": "#653312", "green": "#235433", "green2": "#1e482c", "paneldk": "#2a1e30"},
        "(Light) Desert Oasis": {"bg": "#f1eeec", "surf": "#e7e1dd", "surf2": "#dcd3cc", "surf3": "#cec1b6", "border": "#b19781", "border2": "#ab7d54", "text": "#281e15", "text2": "#4c3c2f", "text3": "#5e4d3d", "gold": "#664b11", "gold2": "#58420e", "indigo": "#225661", "indigo2": "#1e4b55", "teal": "#195952", "teal2": "#164d48", "crimson": "#893420", "crimson2": "#782e1c", "purple": "#6c3b83", "purple2": "#5e3373", "amber": "#77420f", "amber2": "#683a0d", "green": "#3a5724", "green2": "#324c1f", "paneldk": "#182530"},
        "(Light) Frostlight": {"bg": "#eceff1", "surf": "#dde3e7", "surf2": "#ccd6dc", "surf3": "#b6c5ce", "border": "#81a0b1", "border2": "#548bab", "text": "#152128", "text2": "#2f414c", "text3": "#3d525e", "gold": "#604d18", "gold2": "#544315", "indigo": "#304c90", "indigo2": "#2a437d", "teal": "#1f565f", "teal2": "#1c4b53", "crimson": "#8f2a3b", "crimson2": "#7e2433", "purple": "#4e419e", "purple2": "#43398b", "amber": "#704618", "amber2": "#613d15", "green": "#265846", "green2": "#214d3d", "paneldk": "#1b2339"},
        "(Light) Harvest Gold": {"bg": "#f1efec", "surf": "#e7e2dd", "surf2": "#dcd5cc", "surf3": "#cec4b6", "border": "#b19d81", "border2": "#ab8754", "text": "#282015", "text2": "#4c402f", "text3": "#5d4f3c", "gold": "#694c11", "gold2": "#5c420f", "indigo": "#33527e", "indigo2": "#2d476d", "teal": "#1e5a4f", "teal2": "#1a4f45", "crimson": "#8f321e", "crimson2": "#7e2b1b", "purple": "#713a83", "purple2": "#633373", "amber": "#7e410e", "amber2": "#6d390c", "green": "#3a5922", "green2": "#324e1e", "paneldk": "#1c2435"},
        "(Light) Sky Citadel": {"bg": "#eceff1", "surf": "#dde2e7", "surf2": "#ccd5dc", "surf3": "#b6c3ce", "border": "#819cb1", "border2": "#5485ab", "text": "#152028", "text2": "#2f3f4c", "text3": "#3d505e", "gold": "#5e4c16", "gold2": "#514313", "indigo": "#254f81", "indigo2": "#204570", "teal": "#20565a", "teal2": "#1b4b4e", "crimson": "#8d2d29", "crimson2": "#7b2724", "purple": "#524097", "purple2": "#473883", "amber": "#6c4617", "amber2": "#5d3d14", "green": "#275742", "green2": "#224c39", "paneldk": "#192437"}
    })

    readonly property var themeNames: Object.keys(_palettes)

    // ── Readable text (WCAG AA) -- as ui_desktop's style/theme.py ───────
    // Every palette's text colours pass 4.5:1 on its four surfaces; this
    // picks the text for a solid fill (a badge, a selection): white, the
    // page colour or the text colour, whichever reads best.
    function _lum(c) {
        var q = Qt.color(c)
        function f(v) { return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4) }
        return 0.2126 * f(q.r) + 0.7152 * f(q.g) + 0.0722 * f(q.b)
    }
    function contrast(a, b) {
        var la = _lum(a), lb = _lum(b)
        return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
    }
    function onFill(fill) {
        var best = "#ffffff", bestR = contrast("#ffffff", fill)
        var others = [bg, text]
        for (var i = 0; i < others.length; i++) {
            var r = contrast(others[i], fill)
            if (r > bestR) { best = others[i]; bestR = r }
        }
        return best
    }

    // Magic item rarity colours -- card borders and their dialogs. Fixed
    // across themes so a rarity always reads the same. The same values as
    // RARITY_COLORS in data/magic_items.py (the desktop's) --
    // change both together.
    function rarityColor(rarity) {
        var f = fade
        switch (String(rarity || "").toLowerCase()) {
        case "common":    return _grey("#6e6e6e", f)   // dark grey
        case "uncommon":  return _grey("#2ea854", f)   // green
        case "rare":      return _grey("#3fa0f0", f)   // blue
        case "very rare": return _grey("#a064ea", f)   // purple
        case "legendary": return _grey("#e89828", f)   // amber
        case "artifact":  return _grey("#e24f5d", f)   // crimson
        default:          return border
        }
    }

    function applyTheme(name) {
        var p = _palettes[name]
        if (!p) return
        currentThemeName = name
        _base = p
        _paint()
    }

    // ── Immersive Health (core/immersive.py) ───────────────────────────
    // How much colour is taken out of the theme: 0 at full HP, up to 0.85
    // near 0 HP (App.qml eases it). The theme's colours fade towards grey;
    // the three text colours never change, so text keeps its contrast.
    // The grey is the one Qt's desaturation filter uses on desktop
    // (qGray's 11/16/5 weights), so both apps fade alike.
    property real fade: 0
    property var _base: ({})
    onFadeChanged: _paint()

    function _grey(hex, f) {
        var c = Qt.color(hex)
        if (f <= 0) return c
        var l = (c.r * 11 + c.g * 16 + c.b * 5) / 32
        return Qt.rgba(c.r + (l - c.r) * f, c.g + (l - c.g) * f, c.b + (l - c.b) * f, c.a)
    }

    function _paint() {
        var p = _base, f = fade
        if (!p.bg) return
        bg = _grey(p.bg, f); surf = _grey(p.surf, f); surf2 = _grey(p.surf2, f); surf3 = _grey(p.surf3, f)
        border = _grey(p.border, f); border2 = _grey(p.border2, f)
        text = p.text; text2 = p.text2; text3 = p.text3
        gold = _grey(p.gold, f); gold2 = _grey(p.gold2, f)
        indigo = _grey(p.indigo, f); indigo2 = _grey(p.indigo2, f)
        teal = _grey(p.teal, f); teal2 = _grey(p.teal2, f)
        crimson = _grey(p.crimson, f); crimson2 = _grey(p.crimson2, f)
        purple = _grey(p.purple, f); purple2 = _grey(p.purple2, f)
        amber = _grey(p.amber, f); amber2 = _grey(p.amber2, f)
        green = _grey(p.green, f); green2 = _grey(p.green2, f)
        paneldk = _grey(p.paneldk, f)
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
