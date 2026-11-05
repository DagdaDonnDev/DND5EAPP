import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Content for the Dice Roller MFullPageDialog (see App.qml) -- not a
// Page/StackView destination itself, the dialog supplies the chrome
// (title bar + close button). The same as desktop's DiceRollerPanel: a
// dice tray (pick dice or type them, add one of your bonuses, advantage
// or disadvantage on a d20, roll) and the roll history -- every roll the
// sheet makes and the tray's own, kept with the character
// (bridge/dice_roller.py, core/roll_log.py).
Flickable {
    id: root
    readonly property QtObject drBridge: Window.window.diceRollerBridge
    anchors.fill: parent
    anchors.margins: 16
    contentWidth: width
    contentHeight: content.height
    clip: true
    Component.onCompleted: if (drBridge) drBridge.refresh()

    function rollNow() {
        drBridge.setExpression(exprField.text)
        drBridge.roll()
    }

    Column {
        id: content
        width: parent.width
        spacing: 14

        // ── The result ───────────────────────────────────────────────
        Rectangle {
            width: parent.width
            height: 116
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
                    color: Theme.onFill(drBridge.isNat20 ? Theme.teal : Theme.crimson)
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
                    objectName: "diceTotal"
                    text: drBridge.totalText
                    color: drBridge.isNat20 ? Theme.teal2 : (drBridge.isNat1 ? Theme.crimson2 : Theme.gold2)
                    font.pixelSize: 40
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                Label {
                    objectName: "diceDetail"
                    text: drBridge.detailText
                    color: Theme.text2
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    width: parent.width
                }
            }
        }

        // ── The tray ─────────────────────────────────────────────────
        Rectangle {
            width: parent.width
            radius: 10
            color: Theme.surf
            border.color: Theme.border
            implicitHeight: trayCol.height + 24
            height: implicitHeight
            ColumnLayout {
                id: trayCol
                x: 12; y: 12
                width: parent.width - 24
                spacing: 10
                Label { text: "ROLL"; color: Theme.teal2; font.pixelSize: Theme.fsSmall; font.bold: true }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 4
                    rowSpacing: 8
                    columnSpacing: 8
                    Repeater {
                        model: [4, 6, 8, 10, 12, 20, 100]
                        delegate: MButton {
                            objectName: "addDie_" + modelData
                            Layout.fillWidth: true
                            primary: modelData === 20
                            text: "d" + modelData
                            onClicked: drBridge.addDie(modelData)
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    MTextField {
                        id: exprField
                        objectName: "diceExpression"
                        Layout.fillWidth: true
                        text: drBridge.expression
                        placeholderText: "e.g. 2d6 + 3"
                        // what's typed goes to the tray as it's typed, so
                        // changing the mode or bonus after keeps it
                        onTextChanged: drBridge.setExpression(text)
                        onAccepted: root.rollNow()
                    }
                    MButton { text: "Clear"; primary: false; onClicked: drBridge.clearTray() }
                }
                Label { text: "Your bonus"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                ComboBox {
                    id: bonusCombo
                    objectName: "diceBonus"
                    Layout.fillWidth: true
                    model: drBridge.bonusOptions
                    currentIndex: drBridge.bonusIndex
                    onActivated: (index) => drBridge.setBonus(index)
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Repeater {
                        model: [["normal", "Normal"], ["advantage", "Advantage"], ["disadvantage", "Disadvantage"]]
                        delegate: Button {
                            id: mb
                            objectName: "diceMode_" + modelData[0]
                            Layout.fillWidth: true
                            implicitHeight: 40
                            topInset: 0
                            bottomInset: 0
                            onClicked: drBridge.setMode(modelData[0])
                            contentItem: Text {
                                text: modelData[1]
                                color: drBridge.mode === modelData[0] ? Theme.gold2 : Theme.text2
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 8
                                color: drBridge.mode === modelData[0]
                                       ? Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.2) : Theme.surf2
                                border.width: 2
                                border.color: drBridge.mode === modelData[0] ? Theme.gold : Theme.border2
                            }
                        }
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: "Advantage and disadvantage are for a single d20."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                }
                MButton {
                    objectName: "diceRollButton"
                    Layout.fillWidth: true
                    text: "Roll"
                    onClicked: root.rollNow()
                }
            }
        }

        // ── The history ──────────────────────────────────────────────
        RowLayout {
            width: parent.width
            Label {
                text: drBridge.historyTitle
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            MButton {
                objectName: "diceClearHistory"
                primary: false
                text: "Clear"
                onClicked: clearAsk.open()
                visible: drBridge.history.length > 0
            }
        }
        Label {
            visible: drBridge.history.length === 0
            width: parent.width
            text: "No rolls yet. Your sheet's rolls show here too: checks, saves, attacks, hit dice."
            color: Theme.text3
            font.pixelSize: Theme.fsSmall
            wrapMode: Text.WordWrap
        }
        Repeater {
            objectName: "diceHistory"
            model: drBridge.history
            delegate: Rectangle {
                width: content.width
                radius: 8
                color: Theme.surf
                implicitHeight: rowLay.implicitHeight + 14
                height: implicitHeight
                RowLayout {
                    id: rowLay
                    x: 10; y: 7
                    width: parent.width - 20
                    spacing: 10
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            textFormat: Text.StyledText
                            color: Theme.text
                            font.pixelSize: Theme.fsSmall
                            text: "<font color='" + Theme.text3 + "'>" + modelData.when + "</font>&nbsp;&nbsp;<b>"
                                  + modelData.label.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "</b>"
                                  + (modelData.result ? " · " + modelData.result : "")
                        }
                        Label {
                            Layout.fillWidth: true
                            visible: modelData.detail !== ""
                            text: modelData.detail
                            color: Theme.text2
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                        }
                    }
                    Label {
                        visible: modelData.total !== ""
                        text: modelData.total
                        color: modelData.nat === 20 ? Theme.teal2 : (modelData.nat === 1 ? Theme.crimson2 : Theme.gold2)
                        font.pixelSize: Theme.fsHead
                        font.bold: true
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    enabled: modelData.kind === "dice"
                    onClicked: drBridge.reuse(modelData.id)
                }
            }
        }
    }

    Dialog {
        id: clearAsk
        objectName: "diceClearAsk"
        anchors.centerIn: Overlay.overlay
        modal: true
        title: "Clear history"
        standardButtons: Dialog.Yes | Dialog.No
        Label { text: "Clear this character's roll history?"; color: Theme.text; wrapMode: Text.WordWrap }
        onAccepted: drBridge.clearHistory()
    }
}
