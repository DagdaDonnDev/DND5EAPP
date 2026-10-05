import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Proficiencies"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    function joinOrNone(list) {
        return list.length > 0 ? list.join(", ") : "None"
    }

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

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                radius: 10
                color: Theme.surf
                border.color: Theme.border

                MCheckBox {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Inspiration"
                    checked: sheetBridge.inspiration
                    onToggled: sheetBridge.setInspiration(checked)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Label { text: "Skills"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.fillWidth: true }
                MButton {
                    primary: false
                    height: 28
                    text: "Reset"
                    onClicked: sheetBridge.resetSkillProficiencies()
                }
            }
            Label {
                text: "Tap the proficiency marker to cycle it (○ None / ◐ Half / ● Proficient / ★ Expertise); tap the rest of the row to roll a check."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: skillsCol.height + 16
                radius: 10
                color: Theme.surf
                border.color: Theme.border

                Column {
                    id: skillsCol
                    x: 8; y: 8
                    width: parent.width - 16

                    Repeater {
                        model: sheetBridge.skills
                        delegate: Rectangle {
                            id: skillRow
                            readonly property string skillName: modelData.name
                            readonly property int skillBonus: modelData.bonus
                            // Cycle order matches desktop's menu order:
                            // Not Proficient -> Half -> Proficient -> Expertise -> (back to) Not Proficient.
                            readonly property int currentLevel: modelData.expertise ? 3 : (modelData.proficient ? 2 : (modelData.halfProficient ? 1 : 0))
                            width: skillsCol.width
                            height: 36
                            color: "transparent"
                            Row {
                                anchors.fill: parent
                                anchors.leftMargin: 6
                                anchors.rightMargin: 6
                                spacing: 8

                                Rectangle {
                                    width: 28
                                    height: parent.height
                                    color: "transparent"
                                    Label {
                                        anchors.centerIn: parent
                                        text: modelData.expertise ? "★" : (modelData.proficient ? "●" : (modelData.halfProficient ? "◐" : "○"))
                                        color: modelData.expertise ? Theme.gold2 : (modelData.proficient ? Theme.teal2 : Theme.text3)
                                        font.pixelSize: Theme.fsBody
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: sheetBridge.setSkillProficiency(skillRow.skillName, (skillRow.currentLevel + 1) % 4)
                                    }
                                }
                                Label {
                                    text: modelData.name + "  (" + modelData.ability + ")"
                                    color: Theme.text
                                    font.pixelSize: Theme.fsSmall
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width - 80
                                    elide: Text.ElideRight
                                }
                                Label {
                                    text: modelData.bonusText
                                    color: Theme.text2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                            MouseArea {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.leftMargin: 34
                                onClicked: sheetBridge.rollQuickCheck(skillRow.skillName, skillRow.skillBonus)
                            }
                        }
                    }
                }
            }

            Label { text: "Languages, Tools & Combat Training"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.topMargin: 6 }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: profCol.height + 16
                radius: 10
                color: Theme.surf
                border.color: Theme.border

                Column {
                    id: profCol
                    x: 10; y: 8
                    width: parent.width - 20
                    spacing: 10

                    Column {
                        width: parent.width
                        spacing: 2
                        Label { text: "Languages"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                        Label {
                            text: root.joinOrNone(sheetBridge.languages)
                            color: Theme.text
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                            width: parent.width
                        }
                    }
                    Column {
                        width: parent.width
                        spacing: 2
                        Label { text: "Tools"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                        Label {
                            text: root.joinOrNone(sheetBridge.toolProficiencies)
                            color: Theme.text
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                            width: parent.width
                        }
                    }
                    Column {
                        width: parent.width
                        spacing: 2
                        Label { text: "Armor"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                        Label {
                            text: root.joinOrNone(sheetBridge.armorProficiencies)
                            color: Theme.text
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                            width: parent.width
                        }
                    }
                    Column {
                        width: parent.width
                        spacing: 2
                        Label { text: "Weapons"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                        Label {
                            text: root.joinOrNone(sheetBridge.weaponProficiencies)
                            color: Theme.text
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                            width: parent.width
                        }
                    }
                }
            }
        }
    }
}
