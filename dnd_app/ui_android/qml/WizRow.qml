import QtQuick
import QtQuick.Controls
import Mimic

// A browser row: its name, quieter details and a source tag; the chosen
// one in green.
Rectangle {
    id: r
    property string name: ""
    property string meta: ""
    property string tag: ""
    property bool selected: false
    signal clicked()
    implicitHeight: 42
    radius: 8
    color: selected ? Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.12) : Theme.surf
    border.color: selected ? Theme.teal : Theme.border
    Row {
        anchors.fill: parent
        anchors.leftMargin: 12; anchors.rightMargin: 10
        spacing: 8
        Label {
            width: parent.width - metaL.width - tagR.width - parent.spacing * 2
            anchors.verticalCenter: parent.verticalCenter
            text: r.name
            elide: Text.ElideRight
            color: r.selected ? Theme.teal2 : Theme.text
            font.pixelSize: Theme.fsBody - 1
            font.bold: true
        }
        Label {
            id: metaL
            anchors.verticalCenter: parent.verticalCenter
            text: r.meta
            color: Theme.text2
            font.pixelSize: Theme.fsSmall - 1
        }
        Rectangle {
            id: tagR
            visible: r.tag.length > 0
            width: visible ? tagL.implicitWidth + 12 : 0
            height: 20; radius: 5
            anchors.verticalCenter: parent.verticalCenter
            color: Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.11)
            border.color: Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.5)
            Label { id: tagL; anchors.centerIn: parent; text: r.tag; color: Theme.gold2; font.pixelSize: 11; font.bold: true }
        }
    }
    MouseArea { anchors.fill: parent; onClicked: r.clicked() }
}
