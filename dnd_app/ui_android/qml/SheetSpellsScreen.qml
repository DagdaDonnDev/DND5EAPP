import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Spells"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    // Casting a spell with a real active_effects hook (Bless, Haste,
    // Shield of Faith, dozens more) and a non-self-only range prompts
    // self-vs-another -- matches desktop's _apply_spell_active_effect
    // (self-only spells apply directly with no prompt, handled entirely
    // bridge-side).
    Connections {
        target: sheetBridge
        function onSpellEffectPromptRequested(name) {
            effectPromptDialog.spellName = name
            effectPromptDialog.open()
        }
    }
    // A plain themed Popup with MButton actions, not a QtQuick.Controls
    // Dialog with standardButtons -- Dialog's auto-generated buttons are
    // flat/unstyled Material controls that don't match this app's
    // filled MButton look used everywhere else, and (see
    // SaveLoadScreen.qml's moveNewFolderDialog for the same fix) a bare
    // Dialog also paints no unifying background of its own in this
    // app's dark theme. Same shape as SheetChoicesScreen.qml's
    // setXpDialog.
    Popup {
        id: effectPromptDialog
        objectName: "effectPromptDialog"
        property string spellName: ""
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
                text: "Who is " + effectPromptDialog.spellName + " cast on?"
                color: Theme.gold
                font.pixelSize: Theme.fsBody
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "Choose “Someone Else” if you're targeting another creature -- it won't be added to your own Active Effects."
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "effectPromptSomeoneElseButton"
                    text: "Someone Else"
                    primary: false
                    Layout.fillWidth: true
                    onClicked: effectPromptDialog.close()
                }
                MButton {
                    objectName: "effectPromptMyselfButton"
                    text: "Myself"
                    Layout.fillWidth: true
                    onClicked: {
                        sheetBridge.applySpellActiveEffect(effectPromptDialog.spellName)
                        effectPromptDialog.close()
                    }
                }
            }
        }
    }

    // Jump-to-section targets for the drawer's expandable sub-menu (see
    // NavDrawer.qml's sectionSelected).
    function scrollToSection(name) {
        var anchorItem = null
        if (name === "Spell Slots") anchorItem = slotsAnchor
        else if (name === "Known Spells") anchorItem = knownAnchor
        else if (name === "Add a Spell") anchorItem = addSpellAnchor
        if (anchorItem) {
            var pt = anchorItem.mapToItem(flick.contentItem, 0, 0)
            flick.contentY = Math.max(0, pt.y - 8)
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

            // ── Concentration ─────────────────────────────────────────
            Rectangle {
                visible: sheetBridge.isConcentrating
                Layout.fillWidth: true
                Layout.preferredHeight: concCol.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.amber

                Column {
                    id: concCol
                    x: 12; y: 10
                    width: parent.width - 24
                    spacing: 8

                    Label {
                        text: "Concentrating: " + sheetBridge.concentratingSpell
                        color: Theme.amber
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        width: parent.width
                    }
                    Flow {
                        width: parent.width
                        spacing: 8
                        Label {
                            text: "Damage taken:"
                            color: Theme.text2
                            font.pixelSize: Theme.fsSmall
                            height: concDamage.height
                            verticalAlignment: Text.AlignVCenter
                        }
                        MSpinBox {
                            id: concDamage
                            // See SheetEquipmentScreen.qml's eqQty for why
                            // this needs to be >= ~110px.
                            implicitWidth: 110
                            from: 0
                            to: 999
                            value: 10
                        }
                        MButton {
                            primary: false
                            height: 32
                            text: "Save"
                            onClicked: sheetBridge.rollConcentrationSave(concDamage.value)
                        }
                        MButton {
                            primary: false
                            height: 32
                            text: "Drop"
                            onClicked: sheetBridge.dropConcentration()
                        }
                    }
                }
            }

            // ── Slots ─────────────────────────────────────────────────
            Label {
                id: slotsAnchor
                visible: sheetBridge.spellSlots.length > 0 || sheetBridge.pactSlots.max > 0
                text: "Spell Slots"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            Flow {
                Layout.fillWidth: true
                spacing: 8
                Repeater {
                    model: sheetBridge.spellSlots
                    delegate: Rectangle {
                        width: 74; height: 54
                        radius: 8
                        color: Theme.surf
                        border.color: Theme.border
                        Column {
                            anchors.centerIn: parent
                            spacing: 2
                            Label {
                                text: "Lvl " + modelData.level
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                            Label {
                                text: (modelData.max - modelData.used) + " / " + modelData.max
                                color: Theme.teal2
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                        }
                    }
                }
                Rectangle {
                    visible: sheetBridge.pactSlots.max > 0
                    width: 90; height: 54
                    radius: 8
                    color: Theme.surf
                    border.color: Theme.indigo2
                    Column {
                        anchors.centerIn: parent
                        spacing: 2
                        Label {
                            text: "Pact (Lvl " + sheetBridge.pactSlots.level + ")"
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        Label {
                            text: (sheetBridge.pactSlots.max - sheetBridge.pactSlots.used) + " / " + sheetBridge.pactSlots.max
                            color: Theme.indigo2
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }
                }
            }

            // ── Known spells ──────────────────────────────────────────
            Label { id: knownAnchor; text: "Known Spells"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.topMargin: 6 }
            Label {
                visible: sheetBridge.knownSpells.length === 0
                text: "No spells known yet -- search below to add some."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
            }
            Repeater {
                model: sheetBridge.knownSpells
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: knownCol.height + 16
                    radius: 10
                    color: Theme.surf
                    border.color: modelData.prepared ? Theme.teal : Theme.border

                    Column {
                        id: knownCol
                        x: 10; y: 8
                        width: parent.width - 20
                        spacing: 4

                        RowLayout {
                            width: parent.width
                            Label {
                                // Immersive Spells (DM Secrets optional
                                // rule): a purely cosmetic title-only
                                // override (Wild Shape beast noises,
                                // Rage's "SMASH!", a blocked-component
                                // redaction, or a patron/domain/Oath
                                // flavor prefix) -- displayName is just
                                // the real name unchanged when the rule
                                // is off, computed the same way as
                                // ui_desktop's compute_display_spell_title().
                                text: modelData.displayName
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                                Layout.fillWidth: true
                                wrapMode: Text.WordWrap
                            }
                            Label {
                                text: modelData.levelText
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                        }
                        Label {
                            text: modelData.school
                                  + (modelData.concentration ? "  ·  Concentration" : "")
                                  + (modelData.ritual ? "  ·  Ritual" : "")
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                        }
                        // One fixed layout for every card: toggles on the
                        // left, actions on the right with Cast always last,
                        // so the buttons line up from card to card.
                        RowLayout {
                            width: parent.width
                            spacing: 6
                            MCheckBox {
                                visible: modelData.level > 0   // cantrips are never prepared
                                text: "Prepared"
                                checked: modelData.prepared
                                onToggled: sheetBridge.setSpellPrepared(modelData.name, checked)
                            }
                            // Quick spell (desktop's star): pinned spells show up
                            // with Cast buttons on the Combat and Actions screens
                            MButton {
                                objectName: "pinButton_" + modelData.name
                                primary: false
                                implicitWidth: 40
                                implicitHeight: 34
                                iconName: modelData.pinned ? "star_solid" : "star"
                                iconSize: 18
                                onClicked: sheetBridge.toggleQuickSpell(modelData.name)
                            }
                            Item { Layout.fillWidth: true }
                            MButton {
                                visible: modelData.concentration && sheetBridge.concentratingSpell !== modelData.name
                                primary: false
                                implicitHeight: 34
                                text: "Conc."
                                onClicked: sheetBridge.startConcentration(modelData.name)
                            }
                            MButton {
                                visible: modelData.ritual
                                primary: false
                                implicitHeight: 34
                                text: "Ritual"
                                onClicked: sheetBridge.castSpellAsRitual(modelData.name)
                            }
                            MButton {
                                primary: false
                                implicitWidth: 40
                                implicitHeight: 34
                                iconName: "trash"
                                iconSize: 16
                                onClicked: sheetBridge.removeKnownSpell(modelData.name)
                            }
                            MButton {
                                implicitWidth: 68
                                implicitHeight: 34
                                text: "Cast"
                                onClicked: sheetBridge.castSpell(modelData.name)
                            }
                        }
                    }
                }
            }

            // ── Add a spell ───────────────────────────────────────────
            // Browses every one of the character's classes' spell
            // lists (merged, EK/AT mapped to Wizard, Mark-expanded
            // spells included) -- matches ui_desktop's spells.py Spell
            // Browser panel's search + level + class filters, its
            // castable-level cap, its ritual/concentration markers shown
            // on unknown spells too, its Homebrew toggle, and its known/
            // cantrip/prepared cap enforcement at add-time
            // (searchAddableSpells/addKnownSpell/setSpellPrepared in the
            // bridge). The class filter ANDs with (doesn't replace) the
            // character's own class-list restriction, matching desktop
            // exactly -- mainly useful with Homebrew mode on, or to
            // narrow a multiclass character's browser to one class.
            Label { id: addSpellAnchor; text: "Add a Spell"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.topMargin: 6 }
            Label {
                text: "From your class's spell list. Tap a spell to view details."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MTextField {
                    id: spellSearch
                    Layout.fillWidth: true
                    placeholderText: "Search spells…"
                    onTextChanged: addableModel.refreshResults()
                }
                ComboBox {
                    id: levelFilter
                    Layout.preferredWidth: 130
                    model: ["All Levels", "Cantrip", "Level 1", "Level 2", "Level 3", "Level 4",
                            "Level 5", "Level 6", "Level 7", "Level 8", "Level 9"]
                    onCurrentIndexChanged: addableModel.refreshResults()
                }
            }
            ComboBox {
                id: classFilter
                Layout.fillWidth: true
                model: sheetBridge.spellClassFilters
                onCurrentIndexChanged: addableModel.refreshResults()
            }
            MCheckBox {
                Layout.fillWidth: true
                text: "Homebrew mode (ignore class list, castable level, and known/cantrip caps)"
                checked: sheetBridge.spellHomebrewMode
                onToggled: {
                    sheetBridge.setSpellHomebrewMode(checked)
                    addableModel.refreshResults()
                }
            }

            QtObject {
                id: addableModel
                property var results: sheetBridge.searchAddableSpells("", -1, "All Classes")
                function refreshResults() {
                    // classFilter.model[currentIndex] rather than currentText
                    // -- see SheetEquipmentScreen.qml's eqAddModel for why
                    // (currentText can still hold the previous selection at
                    // the exact moment onCurrentIndexChanged fires).
                    results = sheetBridge.searchAddableSpells(
                        spellSearch.text, levelFilter.currentIndex - 1,
                        classFilter.model[classFilter.currentIndex])
                }
            }
            Connections {
                target: sheetBridge
                function onStatsChanged() { addableModel.refreshResults() }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                clip: true

                ListView {
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    model: addableModel.results
                    // A plain Rectangle with its own explicit View/Add
                    // buttons, not an ItemDelegate's whole-row click --
                    // nesting a clickable MButton inside an already-
                    // clickable ItemDelegate risks the tap firing both
                    // the button's own handler and the row's, since the
                    // row's hit area covers the button too.
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 56
                        color: "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 8
                            // fills whatever the fixed-width buttons leave, and
                            // never grows past it -- a long spell name elides
                            // instead of pushing this row's buttons out of line
                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                spacing: 1
                                Label {
                                    text: modelData.name
                                    color: Theme.text
                                    font.pixelSize: Theme.fsBody
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: modelData.levelText + "  ·  " + modelData.school
                                          + (modelData.ritual ? "  ·  R" : "")
                                          + (modelData.concentration ? "  ·  C" : "")
                                    color: Theme.text3
                                    font.pixelSize: Theme.fsSmall
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                            MButton {
                                primary: false
                                implicitWidth: 64
                                height: 34
                                text: "View"
                                onClicked: {
                                    Window.window.pendingSpellDetail = sheetBridge.getSpellDetail(modelData.name)
                                    spellDetail.open()
                                }
                            }
                            MButton {
                                implicitWidth: 64
                                height: 34
                                text: "Add"
                                // Not also calling addableModel.refreshResults()
                                // here: the Connections block above already
                                // refreshes it on statsChanged, and since this
                                // list excludes already-known spells, a second
                                // synchronous refresh mid-click would shrink the
                                // model and destroy this delegate while this
                                // handler is still running (ReferenceError on
                                // any further access to an outer id).
                                onClicked: sheetBridge.addKnownSpell(modelData.name)
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Spell detail popup ───────────────────────────────────────────
    // MFullPageDialog's default property reparents its content into an
    // Item living inside MFullPageDialog.qml's OWN component tree (via
    // "default property alias ... : contentArea.data"), which breaks
    // bare (non-id) property lookups from that injected content back
    // out to an ancestor id declared at the call site -- even a
    // property declared on the FIRST injected child itself isn't
    // reliably visible to ITS OWN descendants once past that boundary.
    // Reached via Window.window.pendingSpellDetail instead (a property
    // on App.qml's root), the same way every screen already reaches
    // its own bridge instance, rather than any bare/scope-chain lookup.
    property var spellData: Window.window.pendingSpellDetail

    MFullPageDialog {
        id: spellDetail
        dialogTitle: (root.spellData && root.spellData.name) || "Spell"

        Flickable {
            anchors.fill: parent
            anchors.margins: 16
            contentWidth: width
            contentHeight: detailCol.height
            clip: true

            ColumnLayout {
                id: detailCol
                width: parent.width
                spacing: 8

                Label {
                    text: (root.spellData.levelText || "") + "  ·  " + (root.spellData.school || "")
                    color: Theme.gold2
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                }
                Label {
                    text: [
                        root.spellData.castTime ? "Casting Time: " + root.spellData.castTime : "",
                        root.spellData.range ? "Range: " + root.spellData.range : "",
                        root.spellData.duration ? "Duration: " + root.spellData.duration : "",
                        root.spellData.components ? "Components: " + root.spellData.components : "",
                    ].filter(s => s.length > 0).join("\n")
                    color: Theme.text2
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Label {
                    visible: !!(root.spellData.ritual || root.spellData.concentration)
                    text: [root.spellData.ritual ? "Ritual" : "", root.spellData.concentration ? "Concentration" : ""]
                          .filter(s => s.length > 0).join("  ·  ")
                    color: Theme.indigo2
                    font.pixelSize: Theme.fsSmall
                    font.bold: true
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
                Label {
                    text: root.spellData.desc || ""
                    color: Theme.text
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Label {
                    visible: !!root.spellData.source
                    text: "Source: " + (root.spellData.source || "")
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                }
            }
        }
    }
}
