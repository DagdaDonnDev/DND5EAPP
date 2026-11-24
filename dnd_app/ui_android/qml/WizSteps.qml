import QtQuick
import QtQuick.Controls
import Mimic

// The wizard's six steps as a bar under the title: done ones teal, this one
// gold, the rest still to come.
Rectangle {
    id: bar
    property int step: 0
    readonly property var names: Window.window.wizardBridge ? Window.window.wizardBridge.stepNames : []
    implicitHeight: 44
    color: Theme.surf
    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.border }
    Row {
        id: row
        x: 14; y: 8
        width: parent.width - 28
        spacing: 4
        Repeater {
            model: bar.names
            delegate: Column {
                width: (row.width - row.spacing * Math.max(0, bar.names.length - 1)) / Math.max(1, bar.names.length)
                spacing: 5
                Rectangle {
                    width: parent.width; height: 5; radius: 3
                    color: index < bar.step ? Theme.teal : index === bar.step ? Theme.gold : Theme.surf3
                }
                Label {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    text: modelData
                    elide: Text.ElideRight
                    font.pixelSize: Theme.fsSmall - 2
                    font.bold: true
                    color: index < bar.step ? Theme.teal2 : index === bar.step ? Theme.gold2 : Theme.text3
                }
            }
        }
    }
}
