import QtQuick
import QtQuick.Controls
import Mimic

// The wizard's bottom bar: ← back, and the big button on -- dimmed, and
// saying what's missing, until the step is done.
Rectangle {
    id: nav
    property bool showBack: true
    property string text: "Next →"
    property bool ready: true
    property bool go: false
    signal back()
    signal next()
    implicitHeight: 68
    color: Theme.surf
    Rectangle { width: parent.width; height: 1; color: Theme.border }
    Row {
        x: 14; y: 11
        width: parent.width - 28
        spacing: 10
        Rectangle {
            visible: nav.showBack
            objectName: "wizBackButton"
            width: 56; height: 46; radius: 8
            color: Theme.surf2; border.color: Theme.border
            Label { anchors.centerIn: parent; text: "←"; color: Theme.text; font.pixelSize: Theme.fsBody + 2; font.bold: true }
            MouseArea { anchors.fill: parent; onClicked: nav.back() }
        }
        Rectangle {
            objectName: "wizNextButton"
            width: parent.width - (nav.showBack ? 66 : 0); height: 46; radius: 8
            color: nav.go ? Theme.teal : Theme.gold
            opacity: nav.ready ? 1.0 : 0.55
            Label {
                anchors.centerIn: parent
                width: parent.width - 16
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                text: nav.text
                color: Theme.onFill(nav.go ? Theme.teal : Theme.gold)
                font.pixelSize: Theme.fsBody
                font.bold: true
            }
            MouseArea { anchors.fill: parent; onClicked: nav.next() }
        }
    }
}
