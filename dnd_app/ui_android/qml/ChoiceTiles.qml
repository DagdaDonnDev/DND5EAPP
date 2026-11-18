import QtQuick
import QtQuick.Controls
import Mimic

// One choice's tiles, in even columns. A long list (any language, say)
// shows what's picked and a "＋ pick" tile that opens a search instead.
Grid {
    id: g
    property var c: ({})
    property int cols: 3
    property var wb: null
    property var picker: null
    columns: cols
    spacing: 5
    readonly property real tileW: (width - spacing * (cols - 1)) / cols
    Repeater {
        model: g.c.big ? g.c.picked : (g.c.tiles || [])
        delegate: WizTile {
            objectName: "tile_" + (g.c.big ? modelData : modelData.label)
            width: g.tileW
            label: g.c.big ? modelData : modelData.label
            sub: g.c.big ? "" : modelData.sub
            tip: g.c.big ? "" : modelData.tip
            have: g.c.big ? "" : modelData.have
            on: g.c.big ? true : modelData.on
            onClicked: g.wb.toggleChoice(g.c.id, g.c.big ? modelData : modelData.value)
        }
    }
    WizTile {
        visible: g.c.big === true && g.c.left > 0
        width: g.tileW
        label: "＋ pick" + ((g.c.picked || []).length ? " another" : "")
        onClicked: {
            var opts = [], vals = {}
            var tl = g.c.tiles || []
            for (var i = 0; i < tl.length; ++i) {
                if (tl[i].have.length || tl[i].on) continue
                opts.push(tl[i].label)
                vals[tl[i].label] = tl[i].value
            }
            g.picker.cardId = g.c.id
            g.picker.values = vals
            g.picker.dialogTitle = g.c.title
            g.picker.options = opts
            g.picker.open()
        }
    }
}
