import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Only reachable when sheetBridge.isArtificer (see App.qml's
// sheetNavItems) -- Artificer Infusions aren't granted until level 2
// (PHB), so an empty list at level 1 is correct, not a missing
// feature. Picking a NEW infusion happens via the Level Up screen's
// generic pool-based choice card (type "infusion", id
// "artificer_infusions"); this screen is a read-only view of which
// infusions are known, plus Activate/Deactivate (applying a known
// infusion to an owned item, or ending that), mirroring desktop's
// InfusionsMixin.
Page {
    id: root
    readonly property string screenTitle: "Infusions"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    property string pendingInfusion: ""

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
                visible: sheetBridge.artificerLevel < 2
                text: "Artificer Infusions are granted starting at level 2 (currently level " + sheetBridge.artificerLevel + ")."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Label {
                visible: sheetBridge.artificerLevel >= 2 && sheetBridge.infusions.length === 0
                text: "No infusions recorded yet. Picking a new one happens via the level-up flow, not built for Android yet."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Label {
                visible: sheetBridge.infusions.length > 0
                text: "Known: " + sheetBridge.infusions.length + "  •  Active: " +
                      sheetBridge.activeInfusionsCount + " / " + sheetBridge.maxActiveInfusions
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }

            Repeater {
                model: sheetBridge.infusions
                delegate: Rectangle {
                    Layout.fillWidth: true
                    radius: 10
                    color: Theme.surf
                    border.color: modelData.active ? Theme.indigo2 : Theme.border
                    implicitHeight: infRow.height + 16

                    RowLayout {
                        id: infRow
                        x: 12; y: 8
                        width: parent.width - 24
                        spacing: 10

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Label { text: modelData.name; color: Theme.text; font.bold: true; font.pixelSize: Theme.fsBody; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Label { text: modelData.statusText; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                        }
                        MButton {
                            visible: modelData.active
                            text: "Deactivate"
                            primary: false
                            height: 32
                            onClicked: sheetBridge.deactivateInfusion(modelData.name)
                        }
                        MButton {
                            visible: !modelData.active
                            text: "Activate"
                            enabled: modelData.canActivate
                            height: 32
                            onClicked: {
                                root.pendingInfusion = modelData.name
                                if (sheetBridge.infusionIsStandalone(modelData.name)) {
                                    if (modelData.name === "Homunculus Servant") {
                                        sheetBridge.activateStandaloneInfusion(modelData.name, false)
                                    } else {
                                        giveAwayDialog.open()
                                    }
                                } else {
                                    var items = sheetBridge.infusionCandidateItems(modelData.name)
                                    if (items.length === 0) {
                                        sheetBridge.notify("You don't own a matching mundane item to infuse yet.")
                                    } else {
                                        itemPickerDialog.options = items
                                        itemPickerDialog.open()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    MPickerDialog {
        id: itemPickerDialog
        dialogTitle: "Apply " + root.pendingInfusion + " to which item?"
        onPicked: (value) => {
            sheetBridge.activateInfusionOnItem(root.pendingInfusion, value)
            if (root.pendingInfusion === "Resistant Armor") {
                damageTypeDialog.open()
            }
        }
    }

    MPickerDialog {
        id: giveAwayDialog
        dialogTitle: root.pendingInfusion + " creates its own item -- give it to yourself, or to another character?"
        options: ["Give to Yourself", "Give to Another Character"]
        onPicked: (value) => sheetBridge.activateStandaloneInfusion(root.pendingInfusion, value === "Give to Another Character")
    }

    MPickerDialog {
        id: damageTypeDialog
        dialogTitle: "Choose a damage type to resist"
        options: ["Acid", "Cold", "Fire", "Force", "Lightning", "Necrotic",
                  "Poison", "Psychic", "Radiant", "Thunder", "Bludgeoning",
                  "Piercing", "Slashing"]
        onPicked: (value) => sheetBridge.setResistantArmorDamageType(value)
    }
}
