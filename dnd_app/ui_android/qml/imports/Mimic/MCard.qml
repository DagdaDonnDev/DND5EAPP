import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// The app's standard content block: a rounded surface card with an
// optional header row -- line icon, gold title, and a slot on the right
// for a header action (e.g. "New Turn"). Children go in a ColumnLayout
// body, so they can use Layout.* properties directly. Keeps every screen
// blocked the same way instead of each one hand-rolling its own
// Rectangle + Column + label combination.
Rectangle {
    id: card
    property string title: ""
    property string iconName: ""
    property color accent: Theme.gold
    property alias headerRight: rightSlot.data
    default property alias content: body.data
    property real bodySpacing: 10

    Layout.fillWidth: true
    implicitHeight: col.implicitHeight + 24
    radius: 12
    color: Theme.surf
    border.color: Theme.border

    ColumnLayout {
        id: col
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 10

        RowLayout {
            visible: card.title.length > 0
            Layout.fillWidth: true
            spacing: 8
            MIcon {
                visible: card.iconName.length > 0
                name: card.iconName
                size: 18
            }
            Label {
                text: card.title
                color: card.accent
                font.pixelSize: Theme.fsSmall
                font.bold: true
                font.capitalization: Font.AllUppercase
                font.letterSpacing: 0.6
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Row { id: rightSlot; spacing: 8 }
        }

        ColumnLayout {
            id: body
            Layout.fillWidth: true
            spacing: card.bodySpacing
        }
    }
}
