import QtQuick
import "IconData.js" as IconData

// The pixel-art cheese for the "type cheese" easter egg (same artwork as
// desktop, from IconData.js). Each art pixel is drawn as a crisp
// `pixel` x `pixel` square.
Canvas {
    id: root
    property int pixel: 3
    readonly property int cols: IconData.cheese[0].length
    readonly property int rows: IconData.cheese.length

    implicitWidth: cols * pixel
    implicitHeight: rows * pixel

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        for (var y = 0; y < rows; ++y) {
            var row = IconData.cheese[y]
            for (var x = 0; x < cols; ++x) {
                var c = IconData.cheesePalette[row[x]]
                if (c) {
                    ctx.fillStyle = c
                    ctx.fillRect(x * pixel, y * pixel, pixel, pixel)
                }
            }
        }
    }
}
