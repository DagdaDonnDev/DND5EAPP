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
                text: "Tap a skill to roll it. Press and hold its marker to change the proficiency level (○ None / ◐ Half / ● Proficient / ★ Expertise)."
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
                                    // Press and hold to change the level -- a tap was too easy
                                    // to hit by accident while scrolling. A tap rolls the check,
                                    // like the rest of the row.
                                    MouseArea {
                                        anchors.fill: parent
                                        pressAndHoldInterval: 450
                                        onClicked: sheetBridge.rollQuickCheck(skillRow.skillName, skillRow.skillBonus)
                                        onPressAndHold: {
                                            var next = (skillRow.currentLevel + 1) % 4
                                            sheetBridge.setSkillProficiency(skillRow.skillName, next)
                                            Window.window.showToast(skillRow.skillName + ": "
                                                + ["not proficient", "half proficiency", "proficient", "expertise"][next])
                                        }
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

            // anything the DM grants outside the rules
            MButton {
                objectName: "dmProficienciesButton"
                Layout.fillWidth: true
                text: "DM-granted proficiencies"
                primary: false
                onClicked: dmDialog.open()
            }
        }
    }

    // ── DM-granted proficiencies: weapons, armour, tools, languages ──
    // Each kind lists what's granted (the trash can removes one), then
    // Add: a search list of the usual ones that also takes any name
    // typed in. The rules live in core/dm_proficiencies.py.
    MFullPageDialog {
        id: dmDialog
        objectName: "dmProficienciesDialog"
        dialogTitle: "DM-granted proficiencies"

        Flickable {
            anchors.fill: parent
            anchors.margins: 16
            contentWidth: width
            contentHeight: dmCol.height
            clip: true

            ColumnLayout {
                id: dmCol
                width: parent.width
                spacing: 14

                Label {
                    Layout.fillWidth: true
                    text: "Proficiencies your DM gives you outside the usual rules. They count like any other: attack rolls, Dedicated Weapon, feat prerequisites, tools and the exported sheet."
                    color: Theme.text2
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                }

                Repeater {
                    model: sheetBridge.dmProficiencies
                    delegate: Rectangle {
                        id: dmSection
                        required property var modelData
                        objectName: "dmSection_" + modelData.kind
                        Layout.fillWidth: true
                        implicitHeight: secCol.implicitHeight + 24
                        radius: 10
                        color: Theme.surf
                        border.color: Theme.border

                        // a gold bar down the left marks the section (colour stays off the text)
                        Rectangle {
                            width: 3; radius: 1.5
                            color: Theme.gold
                            anchors { left: parent.left; top: parent.top; bottom: parent.bottom; leftMargin: 5; topMargin: 10; bottomMargin: 10 }
                        }

                        ColumnLayout {
                            id: secCol
                            anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 18; rightMargin: 12; topMargin: 12 }
                            spacing: 6

                            Label {
                                text: dmSection.modelData.heading.toUpperCase()
                                color: Theme.text
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                            }
                            Label {
                                visible: dmSection.modelData.granted.length === 0
                                text: "None yet"
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                            Repeater {
                                model: dmSection.modelData.granted
                                delegate: Rectangle {
                                    id: grantRow
                                    required property string modelData
                                    Layout.fillWidth: true
                                    implicitHeight: 44
                                    radius: 8
                                    color: Theme.surf2
                                    border.color: Theme.border
                                    RowLayout {
                                        anchors { fill: parent; leftMargin: 12; rightMargin: 4 }
                                        spacing: 8
                                        Label {
                                            Layout.fillWidth: true
                                            text: grantRow.modelData
                                            color: Theme.text
                                            font.pixelSize: Theme.fsBody
                                            elide: Text.ElideRight
                                        }
                                        MButton {
                                            objectName: "dmRemove_" + dmSection.modelData.kind + "_" + grantRow.modelData
                                            primary: false
                                            implicitWidth: 40
                                            height: 36
                                            iconName: "trash"
                                            onClicked: sheetBridge.removeDmProficiency(dmSection.modelData.kind, grantRow.modelData)
                                        }
                                    }
                                }
                            }
                            MButton {
                                objectName: "dmAdd_" + dmSection.modelData.kind
                                Layout.fillWidth: true
                                Layout.topMargin: 2
                                text: "Add"
                                primary: false
                                onClicked: {
                                    dmPicker.kind = dmSection.modelData.kind
                                    dmPicker.dialogTitle = "Add to " + dmSection.modelData.heading
                                    dmPicker.options = sheetBridge.dmProficiencySuggestions(dmSection.modelData.kind)
                                    dmPicker.open()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    MPickerDialog {
        id: dmPicker
        objectName: "dmProficiencyPicker"
        property string kind: ""
        allowCustom: true
        onPicked: (value) => sheetBridge.addDmProficiency(kind, value)
    }
}
