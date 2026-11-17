import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// The Notes screen, as desktop's Notes tab: a list of pages -- Character
// and Backstory, then your own pages in groups you open and close
// (core/notes.py) -- and the page you tap, with a way back to the list.
// Press and hold a page or a group for more (desktop's right-click):
// rename it, move a page to another group, remove it.
Page {
    id: root
    readonly property string screenTitle: "Notes"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    // "list", or the page open: "character", "backstory" or "page"
    property string view: "list"
    property int pageIndex: -1
    readonly property var openPage: (view === "page" && sheetBridge.notesPages[pageIndex]) || ({})

    function open(kind, index) {
        pageArea.saveIfChanged()
        backstoryArea.saveIfChanged()
        view = kind
        pageIndex = index === undefined ? -1 : index
        if (kind === "page") pageArea.load()
        if (kind === "backstory") backstoryArea.text = sheetBridge.traitsNotes.backstory
        flick.contentY = 0
    }

    // The drawer's sub-menu: Character, Backstory, or a page by its title
    function scrollToSection(name) {
        if (name === "Character" || name === "Personality" || name === "Appearance") return open("character")
        if (name === "Backstory") return open("backstory")
        var pages = sheetBridge.notesPages
        for (var i = 0; i < pages.length; i++)
            if (pages[i].title === name) return open("page", i)
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

    // one row of the list: a page to open
    component NoteItem: Rectangle {
        id: item
        property string text: ""
        property int indent: 0
        signal tapped()
        signal held()
        Layout.fillWidth: true
        implicitHeight: 44
        radius: 8
        color: tap.pressed ? Theme.surf3 : Theme.surf2
        border.color: Theme.border
        Label {
            anchors { left: parent.left; leftMargin: 14 + item.indent; right: parent.right; rightMargin: 12
                      verticalCenter: parent.verticalCenter }
            text: item.text; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true
            elide: Text.ElideRight
        }
        MouseArea {
            id: tap
            anchors.fill: parent
            pressAndHoldInterval: 450
            onClicked: item.tapped()
            onPressAndHold: item.held()
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
            spacing: 12

            SheetHeader {}

            // ── the list ──────────────────────────────────────────
            ColumnLayout {
                visible: root.view === "list"
                Layout.fillWidth: true
                spacing: 6
                Label { text: "Notes"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
                Label {
                    text: "Tap a page to open it. Press and hold a page or a group to rename, move or remove it."
                    color: Theme.text3; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap; Layout.fillWidth: true
                }
                NoteItem { objectName: "notesItem_Character"; text: "Character"; onTapped: root.open("character") }
                NoteItem { objectName: "notesItem_Backstory"; text: "Backstory"; onTapped: root.open("backstory") }
                Repeater {
                    model: sheetBridge.notesGroups
                    delegate: ColumnLayout {
                        id: grp
                        readonly property string groupName: modelData.name
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle {
                            objectName: "notesGroup_" + grp.groupName
                            Layout.fillWidth: true
                            Layout.topMargin: 6
                            implicitHeight: 36
                            color: "transparent"
                            Label {
                                anchors { left: parent.left; leftMargin: 2; verticalCenter: parent.verticalCenter }
                                text: (modelData.open ? "▾  " : "▸  ") + grp.groupName
                                      + (modelData.open ? "" : "   (" + modelData.pages.length + ")")
                                color: Theme.teal2; font.pixelSize: Theme.fsSmall; font.bold: true
                            }
                            MouseArea {
                                anchors.fill: parent
                                pressAndHoldInterval: 450
                                onClicked: sheetBridge.toggleNotesGroup(grp.groupName)
                                onPressAndHold: root.groupOptions(grp.groupName)
                            }
                        }
                        Repeater {
                            model: modelData.open ? modelData.pages : []
                            delegate: NoteItem {
                                objectName: "notesItem_" + modelData.title
                                text: modelData.title
                                indent: 8
                                onTapped: root.open("page", modelData.index)
                                onHeld: root.pageOptions(modelData.index, modelData.title, grp.groupName)
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    spacing: 8
                    MButton {
                        objectName: "notesNewPage"
                        Layout.fillWidth: true; primary: false; text: "+ New page"
                        onClicked: { nameDialog.mode = "page"; nameDialog.open() }
                    }
                    MButton {
                        objectName: "notesNewGroup"
                        Layout.fillWidth: true; primary: false; text: "+ New group"
                        onClicked: { nameDialog.mode = "group"; nameDialog.open() }
                    }
                }
            }

            // ── a page open: back to the list ─────────────────────
            RowLayout {
                visible: root.view !== "list"
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "notesBack"
                    primary: false; implicitHeight: 36; text: "‹ All notes"
                    onClicked: root.open("list")
                }
                Label {
                    Layout.fillWidth: true
                    text: root.view === "character" ? "Character" : root.view === "backstory" ? "Backstory"
                          : (root.openPage.title || "")
                    color: Theme.gold2; font.pixelSize: Theme.fsHead; font.bold: true; elide: Text.ElideRight
                    horizontalAlignment: Text.AlignRight
                }
            }

            // Character: appearance, background, and the four boxes with
            // your background's suggestions
            ColumnLayout {
                visible: root.view === "character"
                Layout.fillWidth: true
                spacing: 12
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Label { text: "Appearance"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
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
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Label { text: "Background"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
                    Label { text: sheetBridge.notesBackgroundLine; color: Theme.text; font.pixelSize: Theme.fsBody
                            wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
                Repeater {
                    model: [
                        { key: "personalityTraits", label: "Personality Traits", die: 8 },
                        { key: "ideals", label: "Ideals", die: 6 },
                        { key: "bonds", label: "Bonds", die: 6 },
                        { key: "flaws", label: "Flaws", die: 6 },
                    ]
                    delegate: ColumnLayout {
                        id: traitBox
                        readonly property var rows: sheetBridge.traitSuggestions(modelData.key)
                        Layout.fillWidth: true
                        spacing: 6
                        Label { text: modelData.label; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
                        MTextArea {
                            id: traitArea
                            objectName: "trait_" + modelData.key
                            Layout.fillWidth: true
                            Layout.preferredHeight: implicitHeight
                            minimumHeight: 70
                            onCursorRectangleChanged: root.keepCursorVisible(traitArea)
                            text: sheetBridge.traitsNotes[modelData.key]
                            placeholderText: traitBox.rows.length ? "Write your own, or pick a suggestion…" : "Write your own…"
                            onEditingFinished: sheetBridge.setTraitField(modelData.key, text)
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Item { Layout.fillWidth: true }
                            MButton {
                                objectName: "suggest_" + modelData.key
                                primary: false; implicitHeight: 36; text: "☰ Suggestions"
                                enabled: traitBox.rows.length > 0
                                onClicked: root.suggest(modelData.key, modelData.label, traitBox.rows, traitArea)
                            }
                            MButton {
                                objectName: "roll_" + modelData.key
                                primary: false; implicitHeight: 36; text: "🎲 Roll d" + traitBox.rows.length
                                visible: traitBox.rows.length > 0
                                onClicked: {
                                    sheetBridge.setTraitField(modelData.key, traitArea.text)
                                    sheetBridge.rollTraitSuggestion(modelData.key)
                                    traitArea.text = sheetBridge.traitsNotes[modelData.key]
                                }
                            }
                        }
                    }
                }
            }

            // Backstory
            MTextArea {
                id: backstoryArea
                objectName: "backstoryArea"
                visible: root.view === "backstory"
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                minimumHeight: 320
                onCursorRectangleChanged: root.keepCursorVisible(backstoryArea)
                placeholderText: "Where they're from, who they've lost, who they owe…"
                function saveIfChanged() {
                    if (root.view === "backstory" && text !== sheetBridge.traitsNotes.backstory)
                        sheetBridge.setTraitField("backstory", text)
                }
                onEditingFinished: saveIfChanged()
            }

            // One of your pages, with New entry for today's notes
            ColumnLayout {
                visible: root.view === "page"
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "notesNewEntry"
                    Layout.alignment: Qt.AlignRight
                    primary: false; implicitHeight: 36; text: "+ New entry · today's date"
                    onClicked: {
                        pageArea.saveIfChanged()
                        pageArea.text = sheetBridge.notesNewEntry(root.pageIndex)
                        pageArea.boundIndex = root.pageIndex
                    }
                }
                MTextArea {
                    id: pageArea
                    objectName: "notesPageArea"
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    minimumHeight: 320
                    onCursorRectangleChanged: root.keepCursorVisible(pageArea)
                    placeholderText: "Write anything here…"
                    property int boundIndex: -1
                    function load() {
                        text = (sheetBridge.notesPages[root.pageIndex] || {}).text || ""
                        boundIndex = root.pageIndex
                    }
                    function saveIfChanged() {
                        if (boundIndex >= 0 && text !== ((sheetBridge.notesPages[boundIndex] || {}).text || ""))
                            sheetBridge.setNotesPageText(boundIndex, text)
                    }
                    onEditingFinished: saveIfChanged()
                }
            }
        }
    }

    // ── press and hold: a page's options, a group's ──────────────────
    property int _page: -1
    property string _group: ""
    function pageOptions(index, title, group) {
        _page = index; _group = group
        var opts = [{key: "rename", text: "Rename page", icon: ""}]
        var groups = sheetBridge.notesGroups
        for (var i = 0; i < groups.length; i++)
            if (groups[i].name !== group)
                opts.push({key: "move:" + groups[i].name, text: "Move to " + groups[i].name, icon: ""})
        opts.push({key: "remove", text: "Remove page", icon: "trash"})
        notesOptions.heading = title
        notesOptions.options = opts
        notesOptions.open()
    }
    function groupOptions(name) {
        _page = -1; _group = name
        notesOptions.heading = name
        notesOptions.options = [{key: "newpage", text: "New page in " + name, icon: ""},
                                {key: "renamegroup", text: "Rename group", icon: ""},
                                {key: "removegroup", text: "Remove group", icon: "trash"}]
        notesOptions.open()
    }
    MOptionsDialog {
        id: notesOptions
        objectName: "notesOptions"
        onPicked: (key) => {
            if (key === "rename") { nameDialog.mode = "renamepage"; nameDialog.open() }
            else if (key === "remove") confirmRemove.ask("Remove this page and everything written on it?", "page")
            else if (key.indexOf("move:") === 0) {
                var wasOpen = root.view === "page" && root.pageIndex === root._page
                var at = sheetBridge.moveNotesPage(root._page, key.slice(5))
                if (wasOpen) root.open("page", at)
                else if (root.view === "page") root.open("list")
            }
            else if (key === "newpage") { nameDialog.mode = "pagein"; nameDialog.open() }
            else if (key === "renamegroup") { nameDialog.mode = "renamegroup"; nameDialog.open() }
            else if (key === "removegroup") confirmRemove.ask("Remove the group " + root._group + " and all its pages?", "group")
        }
    }
    MOptionsDialog {
        id: confirmRemove
        objectName: "notesConfirmRemove"
        property string what: ""
        function ask(msg, w) { what = w; heading = "Remove"; message = msg
                               options = [{key: "yes", text: "Remove", icon: "trash"}]; open() }
        onPicked: (key) => {
            if (what === "page") sheetBridge.removeNotesPage(root._page)
            else sheetBridge.removeNotesGroup(root._group)
            root.open("list")
        }
    }

    // ── your background's suggestions ───────────────────────────────
    property string _traitKey: ""
    property var _traitArea: null
    function suggest(key, label, rows, area) {
        _traitKey = key; _traitArea = area
        sheetBridge.setTraitField(key, area.text)
        var opts = [{key: "roll", text: "🎲 Roll a d" + rows.length, icon: ""}]
        for (var i = 0; i < rows.length; i++)
            opts.push({key: "s" + i, text: (i + 1) + ".  " + rows[i], icon: ""})
        suggestDialog.heading = label
        suggestDialog.options = opts
        suggestDialog.open()
    }
    MOptionsDialog {
        id: suggestDialog
        objectName: "suggestDialog"
        message: "Tap one to use it."
        onPicked: (key) => {
            if (key === "roll") sheetBridge.rollTraitSuggestion(root._traitKey)
            else sheetBridge.useTraitSuggestion(root._traitKey,
                                                sheetBridge.traitSuggestions(root._traitKey)[parseInt(key.slice(1))])
            if (root._traitArea) root._traitArea.text = sheetBridge.traitsNotes[root._traitKey]
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
        Overlay.modal: Rectangle { color: Theme.scrim }
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
                placeholderText: "Name"
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
        id: nameDialog
        objectName: "notesNameDialog"
        property string mode: "page"
        heading: mode === "group" ? "New Group" : mode === "renamegroup" ? "Rename Group"
                 : mode === "renamepage" ? "Rename Page" : "New Page"
        onAboutToShow: fieldText = mode === "renamegroup" ? root._group
                       : mode === "renamepage" ? ((sheetBridge.notesPages[root._page] || {}).title || "") : ""
        onConfirmed: (text) => {
            if (mode === "group") sheetBridge.addNotesGroup(text)
            else if (mode === "renamegroup") sheetBridge.renameNotesGroup(root._group, text)
            else if (mode === "renamepage") sheetBridge.renameNotesPage(root._page, text)
            else {
                var at = mode === "pagein" ? sheetBridge.addNotesPageIn(root._group, text) : sheetBridge.addNotesPage(text)
                if (at >= 0) root.open("page", at)
            }
        }
    }
}
