import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Ports ui_desktop's TraitsNotesMixin -- Personality Traits/Ideals/
// Bonds/Flaws, Appearance, and Campaign Notes (Backstory always
// present, plus up to 8 player-named/add/remove/renameable pages).
Page {
    id: root
    readonly property string screenTitle: "Notes"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    // 0 = Backstory (always present), 1+ = notesPages[index-1]
    property int currentPageIndex: 0

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

            Label { text: "Personality"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }

            Repeater {
                model: [
                    { key: "personalityTraits", label: "Personality Traits" },
                    { key: "ideals", label: "Ideals" },
                    { key: "bonds", label: "Bonds" },
                    { key: "flaws", label: "Flaws" },
                ]
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Label { text: modelData.label; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 70
                        radius: 8
                        color: Theme.surf
                        border.color: Theme.border
                        TextArea {
                            id: traitArea
                            anchors.fill: parent
                            anchors.margins: 6
                            text: sheetBridge.traitsNotes[modelData.key]
                            color: Theme.text
                            wrapMode: TextArea.Wrap
                            selectByMouse: true
                            placeholderText: "Enter " + modelData.label.toLowerCase() + "…"
                            onEditingFinished: sheetBridge.setTraitField(modelData.key, text)
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Label { text: "Appearance"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 90
                    radius: 8
                    color: Theme.surf
                    border.color: Theme.border
                    TextArea {
                        id: appearanceArea
                        anchors.fill: parent
                        anchors.margins: 6
                        text: sheetBridge.traitsNotes.appearanceNotes
                        color: Theme.text
                        wrapMode: TextArea.Wrap
                        selectByMouse: true
                        placeholderText: "Age, height, build, eyes, notable features…"
                        onEditingFinished: sheetBridge.setTraitField("appearanceNotes", text)
                    }
                }
            }

            // ── Campaign Notes: Backstory (fixed) + up to 8 pages ──────
            RowLayout {
                Layout.fillWidth: true
                Label { text: "Campaign Notes"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.fillWidth: true }
                MButton {
                    primary: false
                    height: 32
                    text: "Rename"
                    visible: root.currentPageIndex > 0
                    onClicked: renamePageDialog.open()
                }
                MButton {
                    primary: false
                    height: 32
                    text: "Remove"
                    visible: root.currentPageIndex > 0
                    onClicked: {
                        sheetBridge.removeNotesPage(root.currentPageIndex - 1)
                        root.currentPageIndex = 0
                    }
                }
                MButton {
                    height: 32
                    text: "+ Page"
                    onClicked: addPageDialog.open()
                }
            }

            TabBar {
                id: notesTabBar
                Layout.fillWidth: true
                currentIndex: root.currentPageIndex
                onCurrentIndexChanged: root.currentPageIndex = currentIndex
                TabButton { text: "Backstory" }
                Repeater {
                    model: sheetBridge.notesPages
                    delegate: TabButton { text: modelData.title }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 220
                radius: 10
                color: Theme.surf
                border.color: Theme.border

                TextArea {
                    id: pageArea
                    anchors.fill: parent
                    anchors.margins: 8
                    color: Theme.text
                    wrapMode: TextArea.Wrap
                    selectByMouse: true
                    placeholderText: root.currentPageIndex === 0
                        ? "Character backstory, allies, enemies…"
                        : "Session notes, quest log, treasure…"
                    // Re-bind text whenever the active page changes --
                    // TextArea doesn't auto-refresh from a model change
                    // in a plain (non-Repeater) binding once edited once.
                    property int boundPage: -1
                    function syncFromModel() {
                        var newText = root.currentPageIndex === 0
                            ? sheetBridge.traitsNotes.backstory
                            : (sheetBridge.notesPages[root.currentPageIndex - 1] || {}).text || ""
                        if (boundPage !== root.currentPageIndex) {
                            text = newText
                            boundPage = root.currentPageIndex
                        }
                    }
                    Component.onCompleted: syncFromModel()
                    onEditingFinished: {
                        if (root.currentPageIndex === 0) {
                            sheetBridge.setTraitField("backstory", text)
                        } else {
                            sheetBridge.setNotesPageText(root.currentPageIndex - 1, text)
                        }
                    }
                    Connections {
                        target: root
                        function onCurrentPageIndexChanged() { pageArea.syncFromModel() }
                    }
                }
            }
        }
    }

    Dialog {
        id: addPageDialog
        title: "New Notes Page"
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: {
            sheetBridge.addNotesPage(newPageField.text)
            newPageField.text = ""
        }
        MTextField {
            id: newPageField
            width: 240
            placeholderText: "Page name"
        }
    }

    Dialog {
        id: renamePageDialog
        title: "Rename Notes Page"
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        onOpened: renameField.text = (sheetBridge.notesPages[root.currentPageIndex - 1] || {}).title || ""
        onAccepted: sheetBridge.renameNotesPage(root.currentPageIndex - 1, renameField.text)
        MTextField {
            id: renameField
            width: 240
            placeholderText: "Page name"
        }
    }
}
