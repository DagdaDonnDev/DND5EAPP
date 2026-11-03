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

    // Jump-to-section targets for the drawer's sub-menu. Campaign notes
    // pages are listed there by title too: picking one switches to its
    // tab as well as scrolling to it.
    function scrollToSection(name) {
        var anchorItem = null
        if (name === "Personality") anchorItem = personalityAnchor
        else if (name === "Appearance") anchorItem = appearanceAnchor
        else if (name === "Backstory") {
            root.currentPageIndex = 0
            anchorItem = campaignAnchor
        } else {
            var pages = sheetBridge.notesPages
            for (var i = 0; i < pages.length; i++) {
                if (pages[i].title === name) {
                    root.currentPageIndex = i + 1
                    anchorItem = campaignAnchor
                    break
                }
            }
        }
        if (anchorItem) {
            var pt = anchorItem.mapToItem(flick.contentItem, 0, 0)
            flick.contentY = Math.max(0, Math.min(pt.y - 8, flick.contentHeight - flick.height))
        }
    }

    // The text boxes grow with their text rather than scrolling inside
    // themselves, so the page's own Flickable does the scrolling -- this
    // keeps the line being typed on screen as a box grows past the
    // bottom edge.
    function keepCursorVisible(area) {
        if (!area.inputHasFocus) return
        var r = area.cursorRectangle
        var top = area.mapToItem(flick.contentItem, r.x, r.y).y
        var bottom = top + r.height
        if (top < flick.contentY + 8) {
            flick.contentY = Math.max(0, top - 8)
        } else if (bottom > flick.contentY + flick.height - 8) {
            flick.contentY = Math.min(flick.contentHeight - flick.height,
                                      bottom - flick.height + 8)
        }
    }

    Flickable {
        id: flick
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

            Label { id: personalityAnchor; text: "Personality"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }

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
                    MTextArea {
                        id: traitArea
                        Layout.fillWidth: true
                        Layout.preferredHeight: implicitHeight
                        minimumHeight: 70
                        onCursorRectangleChanged: root.keepCursorVisible(traitArea)
                        text: sheetBridge.traitsNotes[modelData.key]
                        placeholderText: "Enter " + modelData.label.toLowerCase() + "…"
                        onEditingFinished: sheetBridge.setTraitField(modelData.key, text)
                    }
                }
            }

            ColumnLayout {
                id: appearanceAnchor
                Layout.fillWidth: true
                spacing: 4
                Label { text: "Appearance"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                MTextArea {
                    id: appearanceArea
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    minimumHeight: 90
                    onCursorRectangleChanged: root.keepCursorVisible(appearanceArea)
                    text: sheetBridge.traitsNotes.appearanceNotes
                    placeholderText: "Age, height, build, eyes, notable features…"
                    onEditingFinished: sheetBridge.setTraitField("appearanceNotes", text)
                }
            }

            // ── Campaign Notes: Backstory (fixed) + up to 8 pages ──────
            ColumnLayout {
                id: campaignAnchor
                Layout.fillWidth: true
                spacing: 8
                Label { text: "Campaign Notes"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Item { Layout.fillWidth: true }
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
                            // Unbind first, so switching back to Backstory
                            // doesn't save the removed page's text into the
                            // page that slides into its slot.
                            pageArea.boundPage = -1
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
            }

            // Page picker: a dropdown rather than tabs, which ran off the
            // side of the screen (and cut titles short) once there were
            // more than a few pages.
            ComboBox {
                id: notesPagePicker
                objectName: "notesPagePicker"
                Layout.fillWidth: true
                model: ["Backstory"].concat(sheetBridge.notesPages.map(function(p) { return p.title }))
                currentIndex: root.currentPageIndex
                onActivated: (index) => root.currentPageIndex = index
                // picking from the list replaces the binding above, and a
                // new model resets the index -- keep it in step either way
                onModelChanged: currentIndex = root.currentPageIndex
                Connections {
                    target: root
                    function onCurrentPageIndexChanged() { notesPagePicker.currentIndex = root.currentPageIndex }
                }
            }

            MTextArea {
                id: pageArea
                objectName: "notesPageArea"
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                minimumHeight: 220
                onCursorRectangleChanged: root.keepCursorVisible(pageArea)
                placeholderText: root.currentPageIndex === 0
                    ? "Character backstory, allies, enemies…"
                    : "Session notes, quest log, treasure…"
                // Re-bind text whenever the active page changes --
                // the text isn't a plain binding, since typing would
                // break it. Whatever was typed on the page being left
                // is saved first, in case the box still had focus when
                // the tab was switched (so editingFinished hasn't fired).
                property int boundPage: -1
                function saveTo(pageIndex) {
                    if (pageIndex === 0) {
                        sheetBridge.setTraitField("backstory", text)
                    } else if (pageIndex > 0) {
                        sheetBridge.setNotesPageText(pageIndex - 1, text)
                    }
                }
                function storedText(pageIndex) {
                    return pageIndex === 0
                        ? sheetBridge.traitsNotes.backstory
                        : (sheetBridge.notesPages[pageIndex - 1] || {}).text || ""
                }
                function syncFromModel() {
                    if (boundPage === root.currentPageIndex) return
                    if (boundPage >= 0 && text !== storedText(boundPage)) {
                        saveTo(boundPage)
                    }
                    text = storedText(root.currentPageIndex)
                    boundPage = root.currentPageIndex
                }
                Component.onCompleted: syncFromModel()
                onEditingFinished: saveTo(boundPage)
                Connections {
                    target: root
                    function onCurrentPageIndexChanged() { pageArea.syncFromModel() }
                }
            }
        }
    }

    // New / rename page -- same themed shape as the other small dialogs
    // (MButton actions rather than Dialog's plain standard buttons).
    component PageNameDialog: Dialog {
        id: dlg
        property string heading: ""
        property alias fieldText: nameField.text
        signal confirmed(string text)
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: Math.min(parent ? parent.width - 32 : 340, 340)
        padding: 16
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }
        onOpened: nameField.forceActiveFocus()

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                text: dlg.heading
                color: Theme.gold2
                font.pixelSize: Theme.fsHead
                font.bold: true
                Layout.fillWidth: true
            }
            MTextField {
                id: nameField
                objectName: "pageNameField"
                Layout.fillWidth: true
                placeholderText: "Page name"
                onAccepted: okButton.clicked()
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    Layout.fillWidth: true
                    primary: false
                    text: "Cancel"
                    onClicked: dlg.close()
                }
                MButton {
                    id: okButton
                    objectName: "pageNameOk"
                    Layout.fillWidth: true
                    text: "OK"
                    onClicked: {
                        var t = nameField.text
                        dlg.close()
                        dlg.confirmed(t)
                    }
                }
            }
        }
    }

    PageNameDialog {
        id: addPageDialog
        objectName: "addPageDialog"
        heading: "New Notes Page"
        onAboutToShow: fieldText = ""
        onConfirmed: (text) => {
            var before = sheetBridge.notesPages.length
            sheetBridge.addNotesPage(text)
            // open the page just made
            if (sheetBridge.notesPages.length > before)
                root.currentPageIndex = sheetBridge.notesPages.length
        }
    }

    PageNameDialog {
        id: renamePageDialog
        objectName: "renamePageDialog"
        heading: "Rename Notes Page"
        onAboutToShow: fieldText = (sheetBridge.notesPages[root.currentPageIndex - 1] || {}).title || ""
        onConfirmed: (text) => sheetBridge.renameNotesPage(root.currentPageIndex - 1, text)
    }
}
