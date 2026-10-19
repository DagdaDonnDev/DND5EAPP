import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// One choice in the attack dialog (App.qml): a box to tick, its name, what
// it adds on the right and its cost under the name. Tap anywhere on it.
// A picked row's border turns gold -- the colour stays on the border, the
// words stay plain. `live` false greys it (undead or fiend, until a Divine
// Smite slot is picked).
Rectangle {
    id: root
    property var opt: ({})
    property bool picked: false
    property bool live: true
    signal clicked()

    objectName: "attackRow_" + (opt.key || "")
    implicitHeight: optCol.implicitHeight + 20
    radius: 8
    color: picked ? Theme.surf2 : Theme.surf
    border.color: picked ? Theme.gold : Theme.border
    border.width: picked ? 2 : 1
    opacity: live ? 1 : 0.5

    RowLayout {
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
        spacing: 10
        Rectangle {
            Layout.alignment: Qt.AlignTop
            Layout.topMargin: 1
            width: 20; height: 20; radius: 4
            color: root.picked ? Theme.gold : Theme.surf2
            border.color: root.picked ? Theme.gold : Theme.border
            Text {
                anchors.centerIn: parent
                visible: root.picked
                text: "✓"
                color: Theme.bg
                font.pixelSize: 14
                font.bold: true
            }
        }
        ColumnLayout {
            id: optCol
            Layout.fillWidth: true
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Label {
                    text: root.opt.title || ""
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Label {
                    visible: (root.opt.dice || "") !== ""
                    text: root.opt.dice || ""
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignRight
                    Layout.maximumWidth: root.width * 0.45
                }
            }
            Label {
                visible: (root.opt.cost || "") !== ""
                text: root.opt.cost || ""
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        enabled: root.live
        onClicked: root.clicked()
    }
}
