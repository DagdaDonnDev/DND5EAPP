import QtQuick
import "IconData.js" as IconData

// One of the app's line icons (shared with desktop -- see
// dnd_app/ui_desktop/icon_data.py, which generates IconData.js), drawn in
// the theme's accent colour. Replaces the emoji the UI used to show:
// emoji render differently on every phone, often in full colour, and
// don't follow the theme. Repaints whenever the theme or size changes.
Canvas {
    id: root
    property string name: ""
    property color color: Theme.indigo2
    property real size: 20

    implicitWidth: size
    implicitHeight: size

    onNameChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        var d = IconData.paths[root.name]
        var f = IconData.fills[root.name]
        if (!d && !f)
            return
        ctx.scale(width / 24, height / 24)
        if (d) {
            ctx.lineWidth = IconData.stroke
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            ctx.strokeStyle = root.color
            ctx.path = d
            ctx.stroke()
        }
        if (f) {
            ctx.fillStyle = root.color
            ctx.fillRule = Qt.WindingFill
            ctx.path = f
            ctx.fill()
        }
        var c = IconData.cuts[root.name]
        if (c) {
            // carve the detail lines out of the solid shape
            ctx.globalCompositeOperation = "destination-out"
            ctx.lineWidth = IconData.cutWidths[root.name] || IconData.cutWidth
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            ctx.strokeStyle = "black"
            ctx.path = c
            ctx.stroke()
        }
    }
}
