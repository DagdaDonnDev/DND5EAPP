import QtQuick
import QtQuick.Controls
import Mimic

// Wizard step 6: the whole character before it's made -- each card with a
// ✎ back to the step it came from -- and Create Character.
Page {
    id: root
    readonly property string screenTitle: "Summary"
    readonly property var wb: Window.window.wizardBridge
    readonly property var sm: { wb ? wb.rev : 0; return wb ? wb.summary() : ({}) }
    readonly property int choicesStep: wb && wb.hasLevel1() ? 3 : 2
    background: Rectangle { color: Theme.bg }

    component Edit: Rectangle {
        property string label: ""
        property int step: 0
        width: el.implicitWidth + 16; height: 22; radius: 6
        color: "transparent"; border.color: Theme.border2
        Label { id: el; anchors.centerIn: parent; text: "✎ " + parent.label; color: Theme.indigo2; font.pixelSize: Theme.fsSmall - 2; font.bold: true }
        MouseArea { anchors.fill: parent; onClicked: Window.window.goToWizardStep(parent.step) }
    }
    component Head: Item {
        property string title: ""
        property string edit: ""
        property int step: 0
        width: parent ? parent.width : 0
        height: 24
        Label { anchors.verticalCenter: parent.verticalCenter; text: parent.title; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
        Edit { visible: parent.edit.length > 0; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; label: parent.edit; step: parent.step }
    }

    WizSteps { id: steps; step: 5; width: parent.width }

    Flickable {
        anchors.top: steps.bottom; anchors.bottom: nav.top
        anchors.left: parent.left; anchors.right: parent.right
        contentHeight: content.height + 24
        clip: true
        Column {
            id: content
            x: 12; y: 12
            width: parent.width - 24
            spacing: 8
            WizCard {
                width: content.width
                Item {
                    width: content.width - 20; height: 28
                    Label { anchors.verticalCenter: parent.verticalCenter; text: root.sm.name || ""; color: Theme.gold2; font.pixelSize: Theme.fsTitle - 3; font.bold: true }
                    Edit { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; label: "Name"; step: 2 }
                }
                Label { text: root.sm.line || ""; color: Theme.text; font.pixelSize: Theme.fsBody - 1; font.bold: true }
                Label { visible: (root.sm.sub || "").length > 0; text: root.sm.sub || ""; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                Label { text: root.sm.sub2 || ""; color: Theme.text2; font.pixelSize: Theme.fsSmall }
            }
            Grid {
                width: parent.width
                columns: 3
                spacing: 6
                Repeater {
                    model: root.sm.stats || []
                    delegate: Rectangle {
                        objectName: "summaryStat_" + modelData.label
                        readonly property bool pb: modelData.label === "PROF BONUS"
                        width: (content.width - 12) / 3; height: 54; radius: 9
                        color: Theme.surf2; border.color: pb ? Theme.border2 : Theme.border
                        Column {
                            anchors.centerIn: parent
                            Label { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.value; color: parent.parent.pb ? Theme.indigo2 : Theme.text; font.pixelSize: Theme.fsHead; font.bold: true }
                            Label { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.label; color: Theme.text3; font.pixelSize: 10; font.bold: true }
                        }
                    }
                }
            }
            WizCard {
                width: content.width
                Head { title: "ABILITIES"; edit: "Abilities"; step: 1 }
                Grid {
                    width: content.width - 20
                    columns: 3
                    spacing: 5
                    Repeater {
                        model: root.sm.abilities || []
                        delegate: Rectangle {
                            width: (content.width - 30) / 3; height: 76; radius: 9
                            color: Theme.surf2; border.color: Theme.border
                            Rectangle { visible: modelData.save; x: parent.width - 13; y: 6; width: 8; height: 8; radius: 4; color: Theme.teal }
                            Column {
                                anchors.centerIn: parent
                                spacing: 1
                                Label { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.ab; color: Theme.text2; font.pixelSize: 11; font.bold: true }
                                Label { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.score; color: Theme.text; font.pixelSize: Theme.fsHead; font.bold: true }
                                WizChip { anchors.horizontalCenter: parent.horizontalCenter; height: 20; text: modelData.mod; kind: modelData.mod.charAt(0) === "-" ? "red" : "teal" }
                            }
                        }
                    }
                }
                Label { visible: (root.sm.saves_text || "").length > 0; text: "● save proficiency: " + (root.sm.saves_text || ""); color: Theme.text3; font.pixelSize: Theme.fsSmall - 1 }
            }
            WizCard {
                width: content.width
                Head { title: "SKILLS"; edit: "Choices"; step: root.choicesStep }
                Grid {
                    width: content.width - 20
                    columns: 2
                    columnSpacing: 14
                    Repeater {
                        model: root.sm.skills || []
                        delegate: Item {
                            width: (content.width - 34) / 2; height: 26
                            Label { anchors.verticalCenter: parent.verticalCenter; text: modelData.name; color: Theme.text; font.pixelSize: Theme.fsSmall }
                            Label { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; text: modelData.bonus; color: Theme.teal2; font.pixelSize: Theme.fsSmall; font.bold: true }
                            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.surf3 }
                        }
                    }
                }
                Label { width: content.width - 20; text: root.sm.senses || ""; color: Theme.text3; font.pixelSize: Theme.fsSmall - 1; wrapMode: Text.WordWrap }
            }
            WizCard {
                visible: root.sm.spells !== undefined && root.sm.spells.head !== undefined
                width: content.width
                Head { title: "SPELLS"; edit: "Spells"; step: 3 }
                Label { text: root.sm.spells ? (root.sm.spells.head || "") : ""; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                Grid {
                    width: content.width - 20
                    columns: 2
                    spacing: 5
                    Repeater {
                        model: root.sm.spells ? (root.sm.spells.cantrips || []).concat(root.sm.spells.spells || []) : []
                        delegate: WizChip {
                            width: (content.width - 25) / 2
                            text: modelData
                            kind: root.sm.spells.cantrips.indexOf(modelData) >= 0 ? "" : "teal"
                        }
                    }
                }
                Label { visible: root.sm.spells && (root.sm.spells.note || "").length > 0; text: root.sm.spells ? (root.sm.spells.note || "") : ""; color: Theme.text3; font.pixelSize: Theme.fsSmall - 1 }
            }
            WizCard {
                width: content.width
                Head { title: "PROFICIENCIES"; edit: "Choices"; step: root.choicesStep }
                Repeater {
                    model: root.sm.profs || []
                    delegate: Row {
                        width: content.width - 20
                        spacing: 8
                        Label { width: 76; text: modelData.label; color: Theme.text3; font.pixelSize: Theme.fsSmall; font.bold: true }
                        Label { width: parent.width - 84; text: modelData.text; color: Theme.text; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap }
                    }
                }
            }
            WizCard {
                width: content.width
                Head { title: "EQUIPMENT"; edit: "Equipment"; step: 4 }
                Repeater {
                    model: root.sm.equipment || []
                    delegate: Row {
                        width: content.width - 20
                        spacing: 8
                        Label { width: 76; text: modelData.label; color: Theme.text3; font.pixelSize: Theme.fsSmall; font.bold: true }
                        Label { width: parent.width - 84; text: modelData.text; color: Theme.text; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap }
                    }
                }
                Row {
                    spacing: 8
                    WizChip { visible: (root.sm.gold || "").length > 0; text: root.sm.gold || ""; kind: "gold"; height: 24 }
                    Label { anchors.verticalCenter: parent.verticalCenter; text: root.sm.weight || ""; color: Theme.text3; font.pixelSize: Theme.fsSmall - 1 }
                }
            }
            WizCard {
                width: content.width
                title: "Features"
                Grid {
                    width: content.width - 20
                    columns: 2
                    spacing: 5
                    Repeater {
                        model: root.sm.features || []
                        delegate: WizChip { width: (content.width - 25) / 2; text: modelData; kind: "off" }
                    }
                }
            }
        }
    }
    WizNav {
        id: nav
        anchors.bottom: parent.bottom; width: parent.width
        go: true
        text: "Create Character ✓"
        onBack: Window.window.goToWizardStep(4)
        onNext: Window.window.finishCharacterCreation()
    }
}
