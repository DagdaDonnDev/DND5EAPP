import QtQuick
import QtQuick.Controls
import Mimic

// What you'll start with, as the Loadout and Inventory will show it.
Page {
    id: root
    readonly property string screenTitle: "You'll Start With"
    readonly property var wb: Window.window.wizardBridge
    readonly property var kit: { wb ? wb.rev : 0; return wb ? wb.kitPreview() : ({ slots: [], rows: [] }) }
    background: Rectangle { color: Theme.bg }

    WizSteps { id: steps; step: 4; width: parent.width }

    Flickable {
        anchors.top: steps.bottom; anchors.bottom: parent.bottom
        anchors.left: parent.left; anchors.right: parent.right
        contentHeight: content.height + 24
        clip: true
        Column {
            id: content
            x: 12; y: 12
            width: parent.width - 24
            spacing: 8
            Label { text: "LOADOUT"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            Grid {
                width: parent.width
                columns: 2
                spacing: 6
                Repeater {
                    model: root.kit.slots || []
                    delegate: Rectangle {
                        width: (content.width - 6) / 2
                        height: sc.implicitHeight + 12
                        radius: 8
                        color: Theme.surf2
                        border.color: Theme.border
                        opacity: modelData.empty ? 0.7 : 1
                        Column {
                            id: sc
                            x: 9; y: 6
                            width: parent.width - 18
                            Label { text: modelData.label; color: Theme.text3; font.pixelSize: Theme.fsSmall - 3; font.bold: true }
                            Label { width: parent.width; text: modelData.name; elide: Text.ElideRight; color: modelData.empty ? Theme.text3 : Theme.text; font.pixelSize: Theme.fsBody - 2; font.bold: true }
                            Label { visible: modelData.sub.length > 0; text: modelData.sub; color: Theme.text2; font.pixelSize: Theme.fsSmall - 2 }
                        }
                    }
                }
            }
            Label { text: "INVENTORY"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            Repeater {
                model: root.kit.rows || []
                delegate: WizRow {
                    width: content.width
                    implicitHeight: 38
                    name: modelData.name
                    meta: modelData.qty > 1 ? "×" + modelData.qty : ""
                }
            }
            Row {
                spacing: 8
                WizChip { visible: (root.kit.gold || "").length > 0; text: root.kit.gold || ""; kind: "gold" }
                Label { anchors.verticalCenter: parent.verticalCenter; text: root.kit.weight ? "Weight " + root.kit.weight : ""; color: Theme.text3; font.pixelSize: Theme.fsSmall }
            }
            MTextField {
                objectName: "kitExtraField"
                width: parent.width
                placeholderText: "+ Anything else to add…"
                Component.onCompleted: text = root.wb ? root.wb.extra : ""
                onEditingFinished: root.wb.setExtra(text)
            }
        }
    }
}
