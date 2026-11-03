import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// One row of spell slots, drawn the same way as ui_desktop's SlotBar:
// a filled rounded square per available slot, a hollow one per spent slot, and
// "remaining/max" on the right. Blue for ordinary slots; pass
// Theme.purple / Theme.purple2 for Pact Magic. Tapping a filled square
// spends a slot, tapping a hollow one gets it back -- `toggled` reports
// the new used count and the screen hands it to the bridge.
RowLayout {
    id: bar

    property string label: ""
    property int max: 0
    property int used: 0
    property color fillColor: Theme.indigo
    property color accentColor: Theme.indigo2

    signal toggled(int newUsed)

    spacing: 6
    visible: max > 0

    Label {
        text: bar.label
        color: Theme.text2
        font.pixelSize: Theme.fsSmall
        font.bold: true
        Layout.preferredWidth: 68
    }

    Row {
        spacing: 2
        Repeater {
            model: bar.max
            delegate: Item {
                // the square is drawn small like desktop's, but the tap
                // target around it is finger-sized
                width: 30; height: 34
                readonly property bool spent: index < bar.used   // spent fill from the left, as on desktop
                Rectangle {
                    anchors.centerIn: parent
                    width: 22; height: 22
                    radius: 6
                    color: parent.spent ? "transparent" : bar.fillColor
                    border.width: 2
                    border.color: parent.spent ? bar.accentColor : bar.fillColor
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: bar.toggled(parent.spent ? bar.used - 1 : bar.used + 1)
                }
            }
        }
    }

    Item { Layout.fillWidth: true }

    Label {
        readonly property int remaining: bar.max - bar.used
        text: remaining + "/" + bar.max
        color: remaining > 0 ? Theme.teal2 : Theme.text3
        font.pixelSize: Theme.fsSmall
    }
}
