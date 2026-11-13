import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// The app's true entry point, matching desktop's start menu: Continue
// with the character played last, start a new one, or pick any saved
// one from the list (the newest first; tap a card to open it, search
// once there are more than a few). "New Character" resets the shared
// character dict (and every wizard bridge's own leftover UI state)
// before handing off to the Race step; opening one reads a saved file
// straight into the finished Character Sheet, since a saved character is
// (by construction -- confirmRace()/confirmClass()/etc. all require a
// valid state to save at all) already complete.
Page {
    id: root
    readonly property string screenTitle: "MIMIC"
    // (App.qml: at the start menu there's no character open to ask about)
    readonly property bool isStartMenu: true
    // (null for a moment as the page leaves the window)
    readonly property QtObject slBridge: Window.window ? Window.window.saveLoadBridge : null
    background: Rectangle { color: Theme.bg }

    // The saved characters, the newest first: the first is Continue's
    readonly property var saved: slBridge ? slBridge.savedCharacters : []
    readonly property var latest: saved.length > 0 ? saved[0] : null
    property string search: ""
    property string pendingDeletePath: ""
    property string pendingDeleteName: ""

    // Every word typed must be in the name, race, class, subclass or folder
    function found(entry) {
        var words = root.search.toLowerCase().split(/\s+/)
        var hay = (entry.name + " " + entry.summary + " " + entry.folder).toLowerCase()
        for (var i = 0; i < words.length; i++)
            if (words[i].length > 0 && hay.indexOf(words[i]) < 0)
                return false
        return true
    }
    readonly property int foundCount: {
        var n = 0
        for (var i = 0; i < saved.length; i++)
            if (found(saved[i]))
                n++
        return n
    }

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
            spacing: 12

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

            // Continue: the character played last, one tap away
            MButton {
                objectName: "continueButton"
                visible: root.latest !== null
                width: parent.width
                height: 48
                iconName: "arrow_right"
                text: root.latest !== null ? "Continue  \u00b7  " + root.latest.name : ""
                onClicked: Window.window.loadCharacterIntoSheet(root.latest.filepath)
            }
            MButton {
                objectName: "newCharacterButton"
                width: parent.width
                // the main button until there's a character to continue
                primary: root.latest === null
                text: "+ New Character"
                onClicked: Window.window.startNewCharacter()
            }

            Item { width: 1; height: 2 }
            Label {
                text: "Your Characters"
                color: Theme.gold
                font.pixelSize: Theme.fsBody
                font.bold: true
            }
            // a search box once there are enough to want one
            MTextField {
                id: searchField
                objectName: "startSearch"
                visible: root.saved.length > 5
                width: parent.width
                placeholderText: "Search characters\u2026"
                onTextChanged: root.search = text
                onVisibleChanged: if (!visible) text = ""
            }

            Label {
                objectName: "startNoneSaved"
                visible: root.saved.length === 0
                width: parent.width
                text: "No saved characters yet. Start a new one above, or bring one in from "
                      + "Save & Export in the menu."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
            }
            Label {
                objectName: "startNoneFound"
                visible: root.saved.length > 0 && root.foundCount === 0
                width: parent.width
                text: "No character matches \u201c" + root.search.trim() + "\u201d."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
            }

            Repeater {
                model: root.saved
                delegate: Rectangle {
                    id: card
                    required property var modelData
                    objectName: "startCard_" + modelData.name
                    visible: root.found(modelData)
                    width: content.width
                    height: Math.max(64, cardText.implicitHeight + 20)
                    radius: 10
                    color: tap.pressed ? Theme.surf2 : Theme.surf
                    border.color: Theme.border

                    // the whole card opens the character
                    MouseArea {
                        id: tap
                        objectName: "startMenuLoadButton_" + card.modelData.name
                        anchors.fill: parent
                        onClicked: Window.window.loadCharacterIntoSheet(card.modelData.filepath)
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 4
                        spacing: 4
                        ColumnLayout {
                            id: cardText
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                text: card.modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                            Label {
                                visible: text.length > 0
                                text: card.modelData.summary
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                            Label {
                                // when it was last played, and its folder if it has one
                                visible: text.length > 0
                                text: (card.modelData.played.length > 0 ? "Played " + card.modelData.played : "")
                                      + (card.modelData.played.length > 0 && card.modelData.folder.length > 0 ? "  \u00b7  " : "")
                                      + card.modelData.folder
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                        // Deleting asks first (see deleteDialog)
                        ToolButton {
                            objectName: "startMenuDeleteButton_" + card.modelData.name
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            contentItem: Item {
                                MIcon { anchors.centerIn: parent; name: "trash"; size: 19; color: Theme.text3 }
                            }
                            onClicked: {
                                root.pendingDeletePath = card.modelData.filepath
                                root.pendingDeleteName = card.modelData.name
                                deleteDialog.open()
                            }
                        }
                    }
                }
            }
        }
    }

    // Deleting a saved character asks first -- it used to go on one tap.
    Dialog {
        id: deleteDialog
        objectName: "startDeleteDialog"
        modal: true
        width: Math.min(root.width - 32, 360)
        anchors.centerIn: parent
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }
        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            Label {
                text: "Delete " + root.pendingDeleteName + "?"
                color: Theme.crimson2
                font.pixelSize: Theme.fsBody
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "Their save file is removed from this phone. Exported copies aren't affected. This can't be undone."
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "startDeleteCancel"
                    text: "Cancel"; primary: false; Layout.fillWidth: true
                    onClicked: deleteDialog.close()
                }
                MButton {
                    objectName: "startDeleteConfirm"
                    text: "Delete"
                    Layout.fillWidth: true
                    onClicked: { slBridge.deleteCharacterAt(root.pendingDeletePath); deleteDialog.close() }
                }
            }
        }
    }
}
