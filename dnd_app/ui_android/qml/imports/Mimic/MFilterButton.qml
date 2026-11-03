import QtQuick
import QtQuick.Controls

// The funnel button at the end of a browser's search row. Tapping it
// opens that browser's MFilterDrawer. While any filter is set it shows
// how many, and its border turns the accent colour, so a filtered list
// never looks like the whole list.
//
//   RowLayout {
//       MTextField { Layout.fillWidth: true; ... }
//       MFilterButton { count: drawer.activeCount; onClicked: drawer.open() }
//   }
Button {
    id: control
    property int count: 0

    topInset: 0
    bottomInset: 0
    leftInset: 0
    rightInset: 0
    padding: 0
    implicitWidth: count > 0 ? 64 : 48
    implicitHeight: 44

    Accessible.name: count > 0 ? "Filters, " + count + " set" : "Filters"

    contentItem: Item {
        Row {
            anchors.centerIn: parent
            spacing: 4
            MIcon {
                name: "filter"
                size: 20
                color: Theme.indigo2
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                visible: control.count > 0
                text: control.count
                color: Theme.indigo2
                font.pixelSize: Theme.fsBody
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    background: Rectangle {
        radius: 8
        color: control.pressed ? Theme.surf3 : Theme.surf
        border.color: control.count > 0 ? Theme.indigo : Theme.border
        border.width: control.count > 0 ? 2 : 1
    }
}
