import QtQuick
import QtQuick.Controls
import Mimic

// The app's true entry point: load a previous character, delete one
// you don't need any more, or start a brand-new one -- matching
// desktop's Start menu / main window. "New Character" resets the
// shared character dict (and every wizard bridge's own leftover UI
// state) before handing off to the Race step; "Load" reads a saved
// file straight into the finished Character Sheet, since a saved
// character is (by construction -- confirmRace()/confirmClass()/etc.
// all require a valid state to save at all) already complete.
Page {
    id: root
    readonly property string screenTitle: "MIMIC"
    readonly property QtObject slBridge: Window.window.saveLoadBridge
    background: Rectangle { color: Theme.bg }

    Component.onCompleted: slBridge.refresh()

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: width
        contentHeight: content.height
        clip: true

        Column {
            id: content
            width: parent.width
            spacing: 16

            Label {
                text: "MIMIC"
                color: Theme.gold2
                font.pixelSize: Theme.fsTitle
                font.bold: true
            }
            Label {
                text: "A Complete D&D 5e Character Creator & Management Tool"
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                width: parent.width
            }

            MButton {
                objectName: "newCharacterButton"
                width: parent.width
                text: "+ New Character"
                onClicked: Window.window.startNewCharacter()
            }

            Label {
                text: "Your Characters"
                color: Theme.gold
                font.pixelSize: Theme.fsBody
                font.bold: true
            }

            Label {
                visible: slBridge.savedCharacters.length === 0
                text: "No saved characters yet -- start a new one above."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
            }

            Repeater {
                model: slBridge.savedCharacters
                delegate: Rectangle {
                    id: card
                    required property var modelData
                    width: content.width
                    height: cardCol.height + 20
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.border

                    Column {
                        id: cardCol
                        x: 12; y: 10
                        width: parent.width - 24
                        spacing: 4
                        Label {
                            text: card.modelData.name
                            color: Theme.text
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                        }
                        Label {
                            visible: card.modelData.classesText.length > 0
                            text: card.modelData.classesText
                            color: Theme.text2
                            font.pixelSize: Theme.fsSmall
                        }
                        Row {
                            spacing: 10
                            MButton {
                                objectName: "startMenuLoadButton_" + card.modelData.name
                                width: 100
                                height: 36
                                text: "Load"
                                onClicked: Window.window.loadCharacterIntoSheet(card.modelData.filepath)
                            }
                            MButton {
                                objectName: "startMenuDeleteButton_" + card.modelData.name
                                primary: false
                                width: 100
                                height: 36
                                text: "Delete"
                                onClicked: slBridge.deleteCharacterAt(card.modelData.filepath)
                            }
                        }
                    }
                }
            }
        }
    }
}
