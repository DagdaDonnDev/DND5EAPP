import QtQuick
import QtQuick.Controls
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Starting Equipment"
    readonly property QtObject eqBridge: Window.window.equipmentBridge
    background: Rectangle { color: Theme.bg }

    Component.onCompleted: eqBridge.refresh()

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: width
        contentHeight: content.height
        clip: true

        Column {
            id: content
            width: parent.width
            spacing: 14

            Label {
                visible: eqBridge.equipmentConfirmedOnce
                text: "Starting equipment confirmed  ✓"
                color: Theme.teal2
                font.pixelSize: Theme.fsBody
                font.bold: true
            }

            Label {
                text: eqBridge.className.length > 0
                      ? "Choose your starting equipment (" + eqBridge.className + "):"
                      : "Choose your starting equipment:"
                color: Theme.text2
                font.pixelSize: Theme.fsBody
                wrapMode: Text.WordWrap
                width: parent.width
            }

            Repeater {
                model: eqBridge.groups
                delegate: Rectangle {
                    id: groupCard
                    required property var modelData
                    width: content.width
                    height: groupCol.height + 24
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.border

                    Column {
                        id: groupCol
                        x: 12; y: 12
                        width: parent.width - 24
                        spacing: 8

                        Repeater {
                            model: groupCard.modelData.options
                            delegate: Column {
                                id: optionCol
                                required property var modelData
                                required property int index
                                width: groupCol.width
                                spacing: 6

                                RadioButton {
                                    id: optRadio
                                    visible: groupCard.modelData.hasChoice
                                    width: groupCol.width
                                    checked: groupCard.modelData.selectedOption === optionCol.index
                                    onClicked: eqBridge.selectOption(groupCard.modelData.index, optionCol.index)
                                    text: "(" + optionCol.modelData.letter + ") " +
                                          optionCol.modelData.parts.map(p => p.label).join(", ")
                                    contentItem: Text {
                                        text: optRadio.text
                                        color: Theme.text
                                        font.pixelSize: Theme.fsBody
                                        wrapMode: Text.WordWrap
                                        leftPadding: optRadio.indicator.width + optRadio.spacing
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }

                                Label {
                                    visible: !groupCard.modelData.hasChoice
                                    width: groupCol.width
                                    text: optionCol.modelData.parts
                                          .filter(p => p.kind === "text")
                                          .map(p => p.label).join(", ")
                                    color: Theme.text
                                    font.pixelSize: Theme.fsBody
                                    font.bold: true
                                    wrapMode: Text.WordWrap
                                }

                                Repeater {
                                    model: optionCol.modelData.parts.filter(p => p.kind === "combo")
                                    delegate: Column {
                                        required property var modelData
                                        width: groupCol.width
                                        spacing: 2
                                        enabled: !groupCard.modelData.hasChoice || groupCard.modelData.selectedOption === optionCol.index
                                        Label {
                                            text: modelData.label + ":"
                                            color: Theme.text2
                                            font.pixelSize: Theme.fsSmall
                                        }
                                        ComboBox {
                                            width: parent.width
                                            model: modelData.pool
                                            currentIndex: modelData.pool.indexOf(modelData.value)
                                            onActivated: (idx) => eqBridge.setPlaceholderPick(
                                                groupCard.modelData.index, optionCol.index,
                                                modelData.itemIndex, modelData.pool[idx])
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                width: parent.width
                height: bgGearCol.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.teal
                Column {
                    id: bgGearCol
                    x: 10; y: 10
                    width: parent.width - 20
                    spacing: 4
                    Label {
                        text: "Starting Gear from Background"
                        color: Theme.teal2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                    }
                    Label {
                        id: bgGearLabel
                        text: eqBridge.backgroundGearText
                        color: Theme.text2
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        width: parent.width
                    }
                }
            }

            Label { text: "Additional Notes / Starting Items"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            TextArea {
                width: parent.width
                height: 80
                placeholderText: "List any other starting equipment, currency, notes…"
                text: eqBridge.notes
                color: Theme.text
                wrapMode: TextArea.Wrap
                onEditingFinished: eqBridge.setNotes(text)
            }

            MButton {
                objectName: "confirmEquipmentButton"
                width: parent.width
                text: "Finish Character"
                onClicked: Window.window.finishCharacterCreation()
            }
        }
    }
}
