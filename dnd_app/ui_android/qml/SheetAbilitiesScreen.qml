import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Abilities"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: width
        contentHeight: content.height
        clip: true

        ColumnLayout {
            id: content
            width: parent.width
            spacing: 16

            SheetHeader {}

            Label {
                text: "A teal border marks a saving throw you're proficient in. Tap the score to roll a check, tap the save line to roll a save."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.width >= 500 ? 3 : 2
                rowSpacing: 10
                columnSpacing: 10

                Repeater {
                    model: sheetBridge.abilities
                    delegate: Rectangle {
                        id: abCard
                        readonly property string abName: modelData.ability
                        readonly property int abMod: modelData.mod
                        readonly property int abSave: modelData.save
                        Layout.fillWidth: true
                        Layout.preferredHeight: 96
                        radius: 10
                        color: Theme.surf
                        border.color: modelData.saveProficient ? Theme.teal : Theme.border
                        clip: true

                        Column {
                            anchors.top: parent.top
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.topMargin: 10
                            spacing: 2
                            Label {
                                text: abCard.abName
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                            Label {
                                text: String(modelData.score)
                                color: Theme.text
                                font.pixelSize: Theme.fsHead
                                font.bold: true
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                            Label {
                                text: modelData.modText
                                color: Theme.gold2
                                font.pixelSize: Theme.fsBody
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                        }
                        // Tapping the score/mod area rolls a check; the
                        // save strip along the bottom is a separate tap
                        // target for the saving throw -- same "tap a
                        // stat to roll it" affordance as ui_desktop's
                        // _quick_roll_toast(), just split into two zones
                        // since a card shows both numbers at once.
                        MouseArea {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.right: parent.right
                            height: parent.height - 22
                            onClicked: sheetBridge.rollQuickCheck(abCard.abName + " Check", abCard.abMod)
                        }
                        Rectangle {
                            anchors.bottom: parent.bottom
                            anchors.left: parent.left
                            anchors.right: parent.right
                            height: 22
                            color: modelData.saveProficient ? Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.18) : "transparent"
                            Label {
                                anchors.centerIn: parent
                                text: "save " + modelData.saveText
                                color: modelData.saveProficient ? Theme.teal2 : Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: sheetBridge.rollQuickCheck(abCard.abName + " Save", abCard.abSave)
                            }
                        }
                    }
                }
            }
        }
    }
}
