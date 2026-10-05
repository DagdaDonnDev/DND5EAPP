import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import Mimic

// Content for the Save/Load MFullPageDialog (see App.qml) -- not a
// Page/StackView destination itself, the dialog supplies the chrome
// (title bar + close button).
Flickable {
    id: root
    readonly property QtObject slBridge: Window.window.saveLoadBridge
    anchors.fill: parent
    anchors.margins: 16
    contentWidth: width
    contentHeight: content.height
    clip: true

    Component.onCompleted: slBridge.refresh()

    // Per-folder collapse state -- session-only (not persisted), same
    // as a typical file manager's expand/collapse. Re-assigning a full
    // copy on toggle (rather than mutating in place) is required for
    // QML to notice the change and re-evaluate bindings that read it.
    property var collapsedFolders: ({})
    function toggleFolder(name) {
        var copy = Object.assign({}, root.collapsedFolders)
        copy[name] = !copy[name]
        root.collapsedFolders = copy
    }

    // Native file picker (Android's Storage Access Framework picker on
    // a real device) for loading a character saved somewhere other
    // than this app's own managed folder -- e.g. one the player
    // downloaded into their phone's Downloads folder.
    FileDialog {
        id: loadFileDialog
        title: "Load Character"
        currentFolder: "file://" + slBridge.downloadsDir
        nameFilters: ["Character files (*.json)", "All files (*)"]
        fileMode: FileDialog.OpenFile
        onAccepted: slBridge.loadCharacterFromUrl(selectedFile.toString())
    }

    // "Move to Folder" -- pick an existing campaign, "Uncategorized", or
    // "+ New Folder…" (which opens moveNewFolderDialog below for typing
    // a name) -- matches desktop's StartMenu QInputDialog.getItem(editable)
    // in two steps instead of one, since MPickerDialog is select-only.
    property string pendingMovePath: ""
    MPickerDialog {
        id: moveFolderPicker
        dialogTitle: "Move to Folder"
        options: ["Uncategorized"].concat(slBridge.folderNames).concat(["+ New Folder…"])
        onPicked: (value) => {
            if (value === "+ New Folder…") {
                newFolderField.text = ""
                moveNewFolderDialog.open()
            } else {
                slBridge.moveCharacterToFolder(root.pendingMovePath, value === "Uncategorized" ? "" : value)
            }
        }
    }
    // A plain themed Popup with MButton actions, not a QtQuick.Controls
    // Dialog with standardButtons -- Dialog's auto-generated buttons are
    // flat/unstyled Material controls that don't match this app's
    // filled MButton look used everywhere else, and a bare Dialog also
    // paints no unifying background of its own in this app's dark
    // theme, leaving the gaps between title/field/buttons showing the
    // dimmed overlay through as a mismatched stripe. Same shape as
    // SheetChoicesScreen.qml's setXpDialog.
    Popup {
        id: moveNewFolderDialog
        objectName: "moveNewFolderDialog"
        modal: true
        focus: true
        width: 280
        parent: Overlay.overlay
        anchors.centerIn: parent
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        // Matches MFullPageDialog.qml's dimming -- the default modal
        // overlay is a much lighter wash than this app's dark theme calls for.
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            Label {
                text: "New Campaign"
                color: Theme.gold
                font.pixelSize: Theme.fsBody
                font.bold: true
            }
            MTextField {
                id: newFolderField
                objectName: "newFolderField"
                Layout.fillWidth: true
                placeholderText: "Campaign name…"
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "newFolderCancelButton"
                    text: "Cancel"
                    primary: false
                    Layout.fillWidth: true
                    onClicked: moveNewFolderDialog.close()
                }
                MButton {
                    objectName: "newFolderMoveButton"
                    text: "Move"
                    Layout.fillWidth: true
                    onClicked: {
                        var name = newFolderField.text.trim()
                        if (name.length > 0) {
                            slBridge.moveCharacterToFolder(root.pendingMovePath, name)
                        }
                        moveNewFolderDialog.close()
                    }
                }
            }
        }
    }

    // "Rename Folder" -- same shape as moveNewFolderDialog.
    property string pendingRenameFolder: ""
    Popup {
        id: renameFolderDialog
        objectName: "renameFolderDialog"
        modal: true
        focus: true
        width: 280
        parent: Overlay.overlay
        anchors.centerIn: parent
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        // Matches MFullPageDialog.qml's dimming -- the default modal
        // overlay is a much lighter wash than this app's dark theme calls for.
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            Label {
                text: "Rename “" + root.pendingRenameFolder + "”"
                color: Theme.gold
                font.pixelSize: Theme.fsBody
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            MTextField {
                id: renameFolderField
                objectName: "renameFolderField"
                Layout.fillWidth: true
                placeholderText: "New campaign name…"
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "renameFolderCancelButton"
                    text: "Cancel"
                    primary: false
                    Layout.fillWidth: true
                    onClicked: renameFolderDialog.close()
                }
                MButton {
                    objectName: "renameFolderConfirmButton"
                    text: "Rename"
                    Layout.fillWidth: true
                    onClicked: {
                        var name = renameFolderField.text.trim()
                        if (name.length > 0 && name !== root.pendingRenameFolder) {
                            slBridge.renameFolder(root.pendingRenameFolder, name)
                        }
                        renameFolderDialog.close()
                    }
                }
            }
        }
    }

    // "Delete Folder" -- a real, permanent bulk delete of every
    // character in the folder (not just un-filing them to
    // Uncategorized), so it requires typing the exact folder name to
    // confirm, same as desktop's StartMenu. Shown only when the folder
    // actually has characters in it -- an empty folder can't exist in
    // this UI (a folder is just a field on a character, so it only
    // ever appears here because it has at least one), but the check is
    // kept explicit rather than assumed.
    property string pendingDeleteFolder: ""
    property int pendingDeleteFolderCount: 0
    Popup {
        id: deleteFolderDialog
        objectName: "deleteFolderDialog"
        modal: true
        focus: true
        width: 300
        parent: Overlay.overlay
        anchors.centerIn: parent
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        // Matches MFullPageDialog.qml's dimming -- the default modal
        // overlay is a much lighter wash than this app's dark theme calls for.
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            Label {
                text: "Delete “" + root.pendingDeleteFolder + "”"
                color: Theme.crimson2
                font.pixelSize: Theme.fsBody
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "This will PERMANENTLY delete all " + root.pendingDeleteFolderCount
                      + " character" + (root.pendingDeleteFolderCount === 1 ? "" : "s")
                      + " in this folder. This cannot be undone.\n\nType Delete to confirm:"
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            MTextField {
                id: deleteFolderField
                objectName: "deleteFolderField"
                Layout.fillWidth: true
                placeholderText: "Delete"
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "deleteFolderCancelButton"
                    text: "Cancel"
                    primary: false
                    Layout.fillWidth: true
                    onClicked: deleteFolderDialog.close()
                }
                MButton {
                    objectName: "deleteFolderConfirmButton"
                    text: "Delete"
                    Layout.fillWidth: true
                    enabled: deleteFolderField.text === "Delete"
                    onClicked: {
                        slBridge.deleteFolder(root.pendingDeleteFolder)
                        deleteFolderDialog.close()
                    }
                }
            }
        }
        onOpened: deleteFolderField.text = ""
    }

    // ── Status: "All changes saved" / "Unsaved changes" ───────────────
    // hasUnsavedChanges() compares a JSON snapshot, so there's no change
    // signal to bind to -- re-checked on a short timer while this is open.
    property bool dirty: false
    function updateDirty() { root.dirty = slBridge.hasUnsavedChanges() }
    Timer { interval: 1200; repeat: true; running: root.visible; triggeredOnStart: true; onTriggered: root.updateDirty() }
    Connections {
        target: slBridge
        function onCharacterSaved() { root.updateDirty() }
        function onCharacterLoaded() { root.updateDirty() }
    }

    // Export: the system "save as" picker, so the shareable copy goes
    // wherever the player wants (Downloads, Drive, ...).
    FileDialog {
        id: exportFileDialog
        title: "Export Character File"
        fileMode: FileDialog.SaveFile
        defaultSuffix: "json"
        currentFolder: "file://" + slBridge.downloadsDir
        selectedFile: "file://" + slBridge.downloadsDir + "/" + slBridge.exportFileName
        nameFilters: ["Character files (*.json)"]
        onAccepted: slBridge.exportJsonToUrl(selectedFile.toString())
    }

    // Deleting a saved character asks first -- it used to go on one tap.
    property string pendingDeletePath: ""
    property string pendingDeleteName: ""
    Dialog {
        id: deleteCharacterDialog
        objectName: "deleteCharacterDialog"
        modal: true
        width: Math.min(root.width, 360)
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
                MButton { text: "Cancel"; primary: false; Layout.fillWidth: true; onClicked: deleteCharacterDialog.close() }
                MButton {
                    objectName: "deleteCharacterConfirmButton"
                    text: "Delete"
                    Layout.fillWidth: true
                    onClicked: { slBridge.deleteCharacterAt(root.pendingDeletePath); deleteCharacterDialog.close() }
                }
            }
        }
    }

    // A big tap target for one export format: icon, name, one-line hint.
    component ExportTile: Rectangle {
        id: tile
        property string iconName: ""
        property string title: ""
        property string hint: ""
        signal tapped()
        Layout.fillWidth: true
        Layout.preferredHeight: 104
        radius: 10
        color: tileArea.pressed ? Theme.surf3 : Theme.surf2
        border.color: Theme.border
        ColumnLayout {
            anchors.centerIn: parent
            width: parent.width - 12
            spacing: 4
            MIcon { name: tile.iconName; size: 28; Layout.alignment: Qt.AlignHCenter }
            Label {
                text: tile.title
                color: Theme.text
                font.pixelSize: Theme.fsSmall
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: tile.hint
                color: Theme.text3
                font.pixelSize: Theme.fsSmall - 2
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
        MouseArea { id: tileArea; anchors.fill: parent; onClicked: tile.tapped() }
    }

    ColumnLayout {
        id: content
        width: parent.width
        spacing: 14

        Label {
            visible: slBridge.errorMessage.length > 0
            text: slBridge.errorMessage
            color: Theme.crimson2
            font.pixelSize: Theme.fsSmall
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // ── 1. This character: save it ──────────────────────────────────
        MCard {
            title: "This character"
            iconName: "identity"

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: Window.window.classBridge.name.length > 0 ? Window.window.classBridge.name : "Unnamed character"
                    color: Theme.text
                    font.pixelSize: Theme.fsBody + 2
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Rectangle {
                    objectName: "saveStatusPill"
                    radius: height / 2
                    color: "transparent"
                    border.color: root.dirty ? Theme.gold : Theme.teal2
                    implicitHeight: statusText.implicitHeight + 8
                    implicitWidth: statusText.implicitWidth + 18
                    Label {
                        id: statusText
                        anchors.centerIn: parent
                        text: root.dirty ? "Unsaved changes" : "All changes saved"
                        color: root.dirty ? Theme.gold : Theme.teal2
                        font.pixelSize: Theme.fsSmall
                    }
                }
            }
            MButton {
                objectName: "saveCharacterButton"
                Layout.fillWidth: true
                iconName: "save"
                text: "Save"
                onClicked: { slBridge.saveCharacter(); root.updateDirty() }
            }
            Label {
                text: "Saves to your character list on this phone. MIMIC also saves automatically when you create a character, level up or down, or confirm your choices."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        // ── 2. Export a copy ─────────────────────────────────────────────
        MCard {
            title: "Export a copy"
            iconName: "file"

            Label {
                text: "Make a copy to share, back up, or open in MIMIC on a computer."
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ExportTile {
                    objectName: "exportJsonButton"
                    iconName: "identity"
                    title: "Character file"
                    hint: ".json, opens in MIMIC"
                    onTapped: exportFileDialog.open()
                }
                ExportTile {
                    objectName: "exportTextButton"
                    iconName: "notes"
                    title: "Text"
                    hint: ".txt summary"
                    onTapped: slBridge.exportText()
                }
                ExportTile {
                    objectName: "exportPdfButton"
                    iconName: "file"
                    title: "PDF sheet"
                    hint: "official sheet"
                    onTapped: slBridge.exportPdf()
                }
            }
            Label {
                text: "You choose where the character file goes. Text and PDF copies go to:"
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                objectName: "destinationDirLabel"
                text: slBridge.documentsDir
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WrapAnywhere
                Layout.fillWidth: true
                Layout.topMargin: -6
            }
        }

        // ── 3. Your characters ──────────────────────────────────────────
        MCard {
            title: "Your characters"
            iconName: "folder"
            headerRight: [
                MButton {
                    objectName: "browseLoadButton"
                    primary: false
                    height: 32
                    implicitWidth: 104
                    text: "Import…"
                    onClicked: loadFileDialog.open()
                }
            ]

            Label {
                visible: slBridge.savedCharacters.length === 0
                text: "No saved characters yet. Tap Import… to open a character file from your phone."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            // Grouped by campaign/folder -- named folders sorted
            // alphabetically first, then "Uncategorized" last, matching
            // desktop's StartMenu grouping (savedCharacterFolders does
            // the grouping bridge-side so both platforms agree).
            Repeater {
                model: slBridge.savedCharacterFolders
                delegate: ColumnLayout {
                    id: section
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        ItemDelegate {
                            objectName: "folderHeader_" + section.modelData.folder
                            Layout.fillWidth: true
                            height: 32
                            background: null
                            contentItem: RowLayout {
                                spacing: 6
                                MIcon {
                                    name: root.collapsedFolders[section.modelData.folder] ? "chevron_right" : "chevron_down"
                                    size: 16
                                }
                                Label {
                                    text: (section.modelData.folder.length > 0 ? section.modelData.folder : "Uncategorized")
                                          + "  (" + section.modelData.characters.length + ")"
                                    color: Theme.gold2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                    Layout.fillWidth: true
                                }
                            }
                            onClicked: root.toggleFolder(section.modelData.folder)
                        }

                        // "Uncategorized" (folder === "") isn't a real
                        // campaign -- just the default bucket for
                        // characters with no folder set -- so it can't
                        // be renamed or deleted the way a named folder can.
                        MButton {
                            objectName: "renameFolderButton_" + section.modelData.folder
                            visible: section.modelData.folder.length > 0
                            primary: false
                            implicitWidth: 40
                            height: 32
                            iconName: "pencil"
                            onClicked: {
                                root.pendingRenameFolder = section.modelData.folder
                                renameFolderField.text = section.modelData.folder
                                renameFolderDialog.open()
                            }
                        }
                        MButton {
                            objectName: "deleteFolderButton_" + section.modelData.folder
                            visible: section.modelData.folder.length > 0
                            primary: false
                            implicitWidth: 40
                            height: 32
                            iconName: "trash"
                            onClicked: {
                                root.pendingDeleteFolder = section.modelData.folder
                                root.pendingDeleteFolderCount = section.modelData.characters.length
                                deleteFolderDialog.open()
                            }
                        }
                    }

                    Repeater {
                        model: section.modelData.characters
                        delegate: Rectangle {
                            id: card
                            objectName: "characterCard_" + modelData.name
                            required property var modelData
                            visible: !root.collapsedFolders[section.modelData.folder]
                            Layout.fillWidth: true
                            Layout.preferredHeight: 62
                            radius: 10
                            color: Theme.surf2
                            border.color: Theme.border
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 6

                                ColumnLayout {
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
                                        visible: card.modelData.classesText.length > 0
                                        text: card.modelData.classesText
                                        color: Theme.text2
                                        font.pixelSize: Theme.fsSmall
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }
                                MButton {
                                    objectName: "loadButton_" + card.modelData.name
                                    implicitWidth: 72
                                    height: 36
                                    text: "Open"
                                    onClicked: slBridge.loadCharacterFrom(card.modelData.filepath)
                                }
                                MButton {
                                    objectName: "moveButton_" + card.modelData.name
                                    primary: false
                                    implicitWidth: 40
                                    height: 36
                                    iconName: "folder"
                                    onClicked: {
                                        root.pendingMovePath = card.modelData.filepath
                                        moveFolderPicker.open()
                                    }
                                }
                                MButton {
                                    objectName: "deleteButton_" + card.modelData.name
                                    primary: false
                                    implicitWidth: 40
                                    height: 36
                                    iconName: "trash"
                                    onClicked: {
                                        root.pendingDeletePath = card.modelData.filepath
                                        root.pendingDeleteName = card.modelData.name
                                        deleteCharacterDialog.open()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
