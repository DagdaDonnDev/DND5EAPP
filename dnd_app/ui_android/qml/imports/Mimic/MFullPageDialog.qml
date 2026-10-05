import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A full-height modal overlay for destinations that aren't part of the
// character-creation step sequence (Settings, Save/Load, Dice Roller,
// Credits) -- opened from the drawer's utility section on top of
// whatever screen the player was already on, and dismissed back to
// exactly that screen (an X in the top-right, or the phone's back
// button -- see App.qml's onClosing) rather than a StackView
// navigation that would change what's "underneath". Sized to the full
// window instead of a smaller centered popup so there's always room
// for large text without the cramped-dialog problem a fixed-size
// popup would have (the same reasoning behind this app's earlier
// touch-and-hold tooltip design decision).
Popup {
    id: root
    default property alias dialogContent: contentArea.data
    property string dialogTitle: ""

    modal: true
    focus: true
    x: 0
    y: 0
    width: parent ? parent.width : 400
    height: parent ? parent.height : 800
    padding: 0

    background: Rectangle { color: Theme.bg }
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

    enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 120 } }
    exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 120 } }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            Layout.leftMargin: 16
            Layout.rightMargin: 8

            Label {
                text: root.dialogTitle
                color: Theme.gold2
                font.pixelSize: Theme.fsHead
                font.bold: true
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            ToolButton {
                objectName: "dialogCloseButton"
                width: 40
                height: 40
                onClicked: root.close()

                // Drawn instead of a "✕" text glyph -- that Unicode
                // symbol (U+2715, Dingbats block) isn't guaranteed
                // present in every Android device's font stack, unlike
                // true emoji. Two crossed bars can never fail to render
                // since they don't depend on any font (same fix as
                // App.qml's hamburger button).
                contentItem: Item {
                    anchors.centerIn: parent
                    width: 18
                    height: 18
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width
                        height: 2
                        radius: 1
                        color: Theme.text
                        rotation: 45
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width
                        height: 2
                        radius: 1
                        color: Theme.text
                        rotation: -45
                    }
                }
            }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }

        Item {
            id: contentArea
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }
}
