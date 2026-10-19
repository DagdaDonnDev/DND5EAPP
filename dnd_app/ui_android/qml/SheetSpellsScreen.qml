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
            // Same pips as desktop's Spells tab: one row per level, blue
            // for ordinary slots, and Pact Magic in its own purple card
            // since it recharges on a short rest. Tap a pip to spend or
            // restore that slot.
            ColumnLayout {
                id: slotsAnchor
                Layout.fillWidth: true
                spacing: 10
                visible: sheetBridge.spellSlots.length > 0 || sheetBridge.pactSlots.max > 0

                MCard {
                    visible: sheetBridge.spellSlots.length > 0
                    title: "Spell Slots"
                    iconName: "spells"
                    bodySpacing: 0
                    Repeater {
                        model: sheetBridge.spellSlots
                        delegate: MSlotBar {
                            Layout.fillWidth: true
                            label: "Level " + modelData.level
                            max: modelData.max
                            used: modelData.used
                            onToggled: (n) => sheetBridge.setSlotsUsed(modelData.level, n)
                        }
                    }
                }

                MCard {
                    visible: sheetBridge.pactSlots.max > 0
                    title: "Pact Magic"
                    iconName: "magic"
                    accent: Theme.purple2
                    border.color: Theme.purple
                    bodySpacing: 0
                    Label {
                        text: "Recharges on a short rest"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    MSlotBar {
                        Layout.fillWidth: true
                        label: "Level " + sheetBridge.pactSlots.level
                        max: sheetBridge.pactSlots.max
                        used: sheetBridge.pactSlots.used
                        fillColor: Theme.purple
                        accentColor: Theme.purple2
                        onToggled: (n) => sheetBridge.setSlotsUsed(-1, n)
                    }
                }
            }

            // ── Spells known / prepared: each casting class's limits ──
            // (the same numbers as desktop's Spells Known / Prepared card)
            Rectangle {
                objectName: "spellLimitsCard"
                visible: sheetBridge.spellLimits.length > 0
                Layout.fillWidth: true
                Layout.preferredHeight: limitsCol.implicitHeight + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                ColumnLayout {
                    id: limitsCol
                    x: 12; y: 10
                    width: parent.width - 24
                    spacing: 6
                    Label {
                        text: "SPELLS KNOWN / PREPARED"
                        color: Theme.purple2
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                    }
                    Repeater {
                        model: sheetBridge.spellLimits
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: modelData.label
                                color: Theme.text
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                            }
                            // over the limit shows in the warning colour
                            Label {
                                Layout.fillWidth: true
                                text: modelData.current + " / " + modelData.max
                                      + (modelData.kind === "prepared"
                                         ? " prepared (" + modelData.ability + "+lvl)" : " known")
                                color: modelData.current > modelData.max ? Theme.amber2 : Theme.text2
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                            }
                            Label {
                                visible: modelData.cantripMax > 0
                                text: "Cantrips " + modelData.cantrips + " / " + modelData.cantripMax
                                color: modelData.cantrips > modelData.cantripMax ? Theme.amber2 : Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
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
                // Just the name, one line of details, and View / Cast. Press
                // and hold the card to prepare, favourite or remove it (see
                // spellOptionsDialog). Concentration starts by itself when
                // cast; Cast asks "normally or as a ritual" only for spells
                // this character can ritual-cast.
                delegate: Rectangle {
                    id: spellCard
                    Layout.fillWidth: true
                    Layout.preferredHeight: knownCol.height + 20
                    radius: 10
                    color: holdArea.pressed ? Theme.surf2 : Theme.surf
                    border.color: Theme.border

                    // behind the buttons, so they keep their own taps
                    MouseArea {
                        id: holdArea
                        objectName: "spellCardHold_" + modelData.name
                        anchors.fill: parent
                        pressAndHoldInterval: 450
                        onPressAndHold: root.openSpellOptions(modelData)
                    }

                    ColumnLayout {
                        id: knownCol
                        x: 12; y: 10
                        width: parent.width - 24
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    Label {
                                        // Immersive Spells (DM Secrets optional
                                        // rule): a purely cosmetic title-only
                                        // override -- displayName is just the
                                        // real name when the rule is off, same
                                        // as ui_desktop's compute_display_spell_title().
                                        text: modelData.displayName
                                        color: Theme.text
                                        font.pixelSize: Theme.fsBody
                                        font.bold: true
                                        wrapMode: Text.WordWrap
                                        Layout.maximumWidth: knownCol.width - 160
                                    }
                                    // Ritual spell: a circled R
                                    Rectangle {
                                        visible: modelData.ritual
                                        implicitWidth: 18
                                        implicitHeight: 18
                                        radius: 9
                                        color: "transparent"
                                        border.color: Theme.teal2
                                        border.width: 1.5
                                        Label {
                                            anchors.centerIn: parent
                                            text: "R"
                                            color: Theme.teal2
                                            font.pixelSize: 10
                                            font.bold: true
                                        }
                                    }
                                    // Favourited (starred spells show on Combat/Actions)
                                    MIcon {
                                        visible: modelData.pinned
                                        name: "star_solid"
                                        size: 14
                                        color: Theme.gold
                                    }
                                    Item { Layout.fillWidth: true }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: modelData.levelText + "  ·  " + modelData.school
                                          + (modelData.concentration ? "  ·  Concentration" : "")
                                    color: Theme.text3
                                    font.pixelSize: Theme.fsSmall
                                    wrapMode: Text.WordWrap
                                }
                                Label {
                                    // granted by a subclass/race/feat: no prep choice, can't be removed
                                    visible: modelData.granted
                                    text: "Always prepared"
                                    color: Theme.teal2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                                Label {
                                    // why Cast is greyed out (or ritual-only)
                                    visible: modelData.needsPreparing
                                    text: modelData.canRitual ? "Not prepared -- castable as a ritual"
                                                              : "Not prepared -- hold to prepare it"
                                    color: Theme.text3
                                    font.pixelSize: Theme.fsSmall
                                }
                                Label {
                                    visible: !modelData.granted && modelData.level > 0
                                             && modelData.preparable && modelData.prepared
                                    text: "Prepared"
                                    color: Theme.teal2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                            }
                            MButton {
                                primary: false
                                implicitWidth: 40
                                implicitHeight: 34
                                iconName: "search"   // View -- a magnifying glass
                                iconSize: 22
                                Accessible.name: "View"
                                onClicked: {
                                    Window.window.pendingSpellDetail = sheetBridge.getSpellDetail(modelData.name)
                                    spellDetail.open()
                                }
                            }
                            MButton {
                                implicitWidth: 64
                                implicitHeight: 34
                                text: "Cast"
                                // an unprepared spell can't be cast -- except as
                                // a ritual (a Wizard's spellbook), which Cast offers
                                enabled: !modelData.needsPreparing || modelData.canRitual
                                onClicked: root.castSpell(modelData)
                            }
                        }
                    }
                }
            }
            Label {
                visible: sheetBridge.knownSpells.length > 0
                text: "Press and hold a spell to prepare, favourite or remove it. Spells marked Always prepared come from your class, race or a feat and stay."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
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
                text: "From your class's spell list. Tap the magnifying glass for a spell's details."
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
                    objectName: "spellSearchField"
                    Layout.fillWidth: true
                    placeholderText: "Search spells…"
                    onTextChanged: addableModel.refreshResults()
                }
                // level and class filters live in the drawer behind this
                MFilterButton {
                    objectName: "spellFilterButton"
                    count: spellFilters.activeCount
                    onClicked: spellFilters.open()
                }
            }
            MFilterDrawer {
                id: spellFilters
                objectName: "spellFilterDrawer"
                title: "Spell filters"
                activeCount: (levelFilter.currentIndex > 0) + (classFilter.currentIndex > 0)
                onCleared: { levelFilter.currentIndex = 0; classFilter.currentIndex = 0 }
                Label { text: "Level"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: levelFilter
                    Layout.fillWidth: true
                    model: ["All Levels", "Cantrip", "Level 1", "Level 2", "Level 3", "Level 4",
                            "Level 5", "Level 6", "Level 7", "Level 8", "Level 9"]
                    onCurrentIndexChanged: addableModel.refreshResults()
                }
                Label { text: "Class"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: classFilter
                    Layout.fillWidth: true
                    model: sheetBridge.spellClassFilters
                    onCurrentIndexChanged: addableModel.refreshResults()
                }
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
                                implicitWidth: 40
                                height: 34
                                iconName: "search"   // View -- a magnifying glass
                                iconSize: 22
                                Accessible.name: "View"
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

    // ── Press-and-hold options for a known spell, and the cast choice
    // for spells that can be cast as a ritual (both the shared menu) ──
    property var optionsSpell: ({})
    function openSpellOptions(sp) {
        var opts = []
        // cantrips are never prepared, and neither is a spell only a
        // Warlock/Sorcerer/Bard/Ranger casts
        // Granted spells (domain/oath/racial/feat) are always prepared and
        // part of the character, so they get neither Prepare nor Remove.
        if (sp.level > 0 && sp.preparable && !sp.granted)
            opts.push({ key: "prepare", text: sp.prepared ? "Unprepare" : "Prepare" })
        opts.push({ key: "favourite", icon: sp.pinned ? "star" : "star_solid",
                    text: sp.pinned ? "Remove from favourites" : "Add to favourites" })
        if (!sp.granted)
            opts.push({ key: "remove", icon: "trash", text: "Remove from spell list" })
        root.optionsSpell = sp
        spellOptionsDialog.heading = sp.displayName || sp.name
        spellOptionsDialog.options = opts
        spellOptionsDialog.open()
    }
    MOptionsDialog {
        id: spellOptionsDialog
        objectName: "spellOptionsDialog"
        onPicked: (key) => {
            var sp = root.optionsSpell
            if (key === "prepare") sheetBridge.setSpellPrepared(sp.name, !sp.prepared)
            else if (key === "favourite") sheetBridge.toggleQuickSpell(sp.name)
            else if (key === "remove") sheetBridge.removeKnownSpell(sp.name)
        }
    }

    // The card's Cast button:
    //   a spell you can cast as a ritual -> ask: normally (a slot) or as a
    //                                       ritual (no slot, +10 minutes)
    //   anything else                    -> cast it (the bridge spends the
    //       slot, starts concentration, applies its effect, uses the action)
    function castSpell(sp) {
        if (!sp.canRitual) {
            sheetBridge.castSpell(sp.name)
            return
        }
        // not prepared: a ritual is the only way to cast it (a Wizard's spellbook)
        if (sp.needsPreparing) {
            sheetBridge.castSpellAsRitual(sp.name)
            return
        }
        root.optionsSpell = sp
        castChoiceDialog.heading = "Cast " + (sp.displayName || sp.name)
        castChoiceDialog.options = [
            { key: "normal", text: "Cast normally (uses a spell slot)" },
            { key: "ritual", text: "Cast as a ritual (no slot, +10 minutes)" },
        ]
        castChoiceDialog.open()
    }
    MOptionsDialog {
        id: castChoiceDialog
        objectName: "castChoiceDialog"
        onPicked: (key) => {
            if (key === "ritual") sheetBridge.castSpellAsRitual(root.optionsSpell.name)
            else sheetBridge.castSpell(root.optionsSpell.name)
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
