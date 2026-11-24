import QtQuick
import QtQuick.Controls
import Mimic

// A wizard card: GOLD CAPS title, a quieter line, a count on the right,
// and its content underneath.
Rectangle {
    id: card
    property string title: ""
    property string sub: ""
    property string count: ""
    property bool done: false
    property bool inner: false
    default property alias cardContent: body.data
    implicitHeight: col.implicitHeight + 20
    radius: inner ? 8 : 10
    color: inner ? Theme.surf2 : Theme.surf
    border.color: Theme.border
    Column {
        id: col
        x: 10; y: 10
        width: parent.width - 20
        spacing: 7
        Item {
            width: parent.width
            height: Math.max(head.implicitHeight, pill.height)
            visible: card.title.length > 0
            Row {
                id: head
                spacing: 7
                width: parent.width - (pill.visible ? pill.width + 8 : 0)
                anchors.verticalCenter: parent.verticalCenter
                Label {
                    id: ttl
                    text: card.inner ? card.title : card.title.toUpperCase()
                    color: card.inner ? Theme.text : Theme.gold
                    font.pixelSize: card.inner ? Theme.fsBody - 1 : Theme.fsSmall
                    font.bold: true
                    font.letterSpacing: card.inner ? 0 : 0.5
                }
                Label {
                    width: head.width - ttl.width - head.spacing
                    text: card.sub
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall - 1
                    elide: Text.ElideRight
                    anchors.verticalCenter: ttl.verticalCenter
                }
            }
            Rectangle {
                id: pill
                visible: card.count.length > 0
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                height: 20; width: pc.implicitWidth + 16; radius: 10
                readonly property color tone: card.done ? Theme.teal2 : Theme.gold2
                color: Qt.rgba(tone.r, tone.g, tone.b, 0.15)
                Label { id: pc; anchors.centerIn: parent; text: card.count; color: pill.tone; font.pixelSize: Theme.fsSmall - 2; font.bold: true }
            }
        }
        Column {
            id: body
            width: parent.width
            spacing: 7
        }
    }
}
