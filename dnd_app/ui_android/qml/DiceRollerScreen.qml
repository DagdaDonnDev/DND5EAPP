import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Content for the Dice Roller MFullPageDialog (see App.qml) -- not a
// Page/StackView destination itself, the dialog supplies the chrome
// (title bar + close button). Simplified vs. ui_desktop's
// DiceRollerPanel: no roll-against-a-character-skill picker yet, just
// quick rolls, a custom N-dice + modifier roll, and Advantage/
// Disadvantage on a single d20 -- see bridge/dice_roller.py.
Flickable {
    id: root
    readonly property QtObject drBridge: Window.window.diceRollerBridge
    anchors.fill: parent
    anchors.margins: 16
    contentWidth: width
    contentHeight: content.height
    clip: true

    Column {
        id: content
        width: parent.width
        spacing: 16

        // ── Result ────────────────────────────────────────────────────
        Rectangle {
            width: parent.width
            height: 110
            radius: 10
            color: Theme.surf
            border.width: 2
            border.color: drBridge.isNat20 ? Theme.teal : (drBridge.isNat1 ? Theme.crimson : Theme.border2)

            Column {
                anchors.centerIn: parent
                spacing: 4
                width: parent.width - 20
                Label {
                    visible: drBridge.isNat20 || drBridge.isNat1
                    text: drBridge.isNat20 ? "NATURAL 20" : "NATURAL 1"
                    color: "white"
                    font.pixelSize: Theme.fsSmall
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    padding: 3
                    background: Rectangle {
                        color: drBridge.isNat20 ? Theme.teal : Theme.crimson
                        radius: 4
                    }
                }
                Label {
                    text: drBridge.totalText
                    color: Theme.gold2
                    font.pixelSize: 40
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                Label {
                    text: drBridge.detailText
                    color: Theme.text2
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    width: parent.width
                }
            }
        }

        // ── Quick roll ────────────────────────────────────────────────
        Label { text: "Quick Roll"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
        GridLayout {
            width: parent.width
            columns: 4
            rowSpacing: 8
            columnSpacing: 8
            Repeater {
                model: [4, 6, 8, 10, 12, 20, 100]
                delegate: MButton {
                    Layout.fillWidth: true
                    primary: modelData === 20
                    text: "d" + modelData
                    onClicked: drBridge.quickRoll(modelData)
                }
            }
        }

        // ── Custom roll ───────────────────────────────────────────────
        Label { text: "Custom Roll"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; topPadding: 8 }
        GridLayout {
            width: parent.width
            columns: 2
            rowSpacing: 10
            columnSpacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label { text: "Dice"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                MSpinBox { id: countSpin; Layout.fillWidth: true; from: 1; to: 20; value: 1 }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label { text: "Sides"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                ComboBox {
                    id: sidesCombo
                    Layout.fillWidth: true
                    model: ["4", "6", "8", "10", "12", "20", "100"]
                    currentIndex: 5
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label { text: "Modifier"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                MSpinBox { id: modSpin; Layout.fillWidth: true; from: -20; to: 20; value: 0 }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label { text: "Advantage"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                ComboBox {
                    id: advCombo
                    Layout.fillWidth: true
                    model: ["Normal", "Advantage", "Disadvantage"]
                }
            }
        }
        MButton {
            objectName: "customRollButton"
            width: parent.width
            text: "Roll"
            onClicked: drBridge.customRoll(countSpin.value, parseInt(sidesCombo.currentText),
                                            modSpin.value, advCombo.currentText)
        }

        // ── History ───────────────────────────────────────────────────
        RowLayout {
            width: parent.width
            Label { text: "History"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.fillWidth: true }
            MButton {
                primary: false
                text: "Clear"
                onClicked: drBridge.clearHistory()
                visible: drBridge.history.length > 0
            }
        }
        Label {
            visible: drBridge.history.length === 0
            text: "No rolls yet."
            color: Theme.text3
            font.pixelSize: Theme.fsSmall
        }
        Repeater {
            model: drBridge.history
            delegate: Label {
                width: parent.width
                text: modelData.text
                color: modelData.crit === "nat20" ? Theme.teal2 : (modelData.crit === "nat1" ? Theme.crimson2 : Theme.text)
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
            }
        }
    }
}
