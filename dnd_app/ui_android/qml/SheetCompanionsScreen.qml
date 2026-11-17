import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Your creatures -- the Android side of ui_desktop/pages/sheet/companions.py:
// mounts, vehicles, summoned creatures, companions and Wild Shape: the
// sheet's Creatures page, as desktop's Creatures tab.
Page {
    id: root
    readonly property string screenTitle: "Creatures"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

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

            // ── Mounts ───────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                radius: 10
                color: Theme.surf
                border.color: Theme.gold
                implicitHeight: mountsCol.height + 24

                ColumnLayout {
                    id: mountsCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 8

                    Label { text: "Mounts"; color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsTitle }

                    Label { text: "Add a mount:"; color: Theme.text2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        ComboBox {
                            id: mountPicker
                            objectName: "mountPicker"
                            Layout.fillWidth: true
                            model: sheetBridge.mountOptions
                        }
                        MButton {
                            objectName: "addMountBtn"
                            text: "+ Add"
                            onClicked: sheetBridge.addMount(mountPicker.currentText)
                        }
                    }
                    Label { text: "Find Steed:"; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        ComboBox {
                            id: steedPicker
                            objectName: "steedPicker"
                            Layout.fillWidth: true
                            model: sheetBridge.findSteedOptions
                            textRole: "label"
                            valueRole: "value"
                        }
                        MButton {
                            objectName: "addSteedBtn"
                            text: "+ Add"
                            onClicked: sheetBridge.addMount(steedPicker.currentValue)
                        }
                    }

                    Repeater {
                        objectName: "ownedMountsRepeater"
                        model: sheetBridge.ownedMounts
                        delegate: MStatblockCard {
                            Layout.fillWidth: true
                            removable: true
                            displayName: modelData.displayName
                            source: modelData.source
                            size: modelData.size
                            creatureType: modelData.creatureType
                            ac: modelData.ac
                            hp: modelData.hp
                            hitDice: modelData.hitDice
                            speed: modelData.speed
                            abilities: modelData.abilities
                            saves: modelData.saves
                            skills: modelData.skills
                            damageResistances: modelData.damageResistances
                            damageImmunities: modelData.damageImmunities
                            conditionImmunities: modelData.conditionImmunities
                            senses: modelData.senses
                            languages: modelData.languages
                            traits: modelData.traits
                            actions: modelData.actions
                            reactions: modelData.reactions
                            hasHpTracking: modelData.hasHpTracking
                            currentHp: modelData.currentHp
                            maxHp: modelData.maxHp
                            onHpEdited: (value) => sheetBridge.setCompanionHp(modelData.hpKey, value, "")
                            onRemoveClicked: sheetBridge.removeMount(modelData.index)
                        }
                    }
                }
            }

            // ── Vehicles ─────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                radius: 10
                color: Theme.surf
                border.color: Theme.teal
                implicitHeight: vehiclesCol.height + 24

                ColumnLayout {
                    id: vehiclesCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 8

                    Label { text: "Vehicles"; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsTitle }

                    Label { text: "Add a vehicle:"; color: Theme.text2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        ComboBox {
                            id: vehiclePicker
                            objectName: "vehiclePicker"
                            Layout.fillWidth: true
                            model: sheetBridge.vehicleOptions
                        }
                        MButton {
                            objectName: "addVehicleBtn"
                            text: "+ Add"
                            onClicked: sheetBridge.addVehicle(vehiclePicker.currentText)
                        }
                    }

                    Repeater {
                        objectName: "ownedVehiclesRepeater"
                        model: sheetBridge.ownedVehicles
                        delegate: Item {
                            Layout.fillWidth: true
                            implicitHeight: vDelegateLoader.item ? vDelegateLoader.item.implicitHeight : 0
                            Loader {
                                id: vDelegateLoader
                                width: parent.width
                                sourceComponent: modelData.hasStats ? vehicleStatblockComp : vehicleSimpleComp
                            }
                            Component {
                                id: vehicleStatblockComp
                                MStatblockCard {
                                    width: vDelegateLoader.width
                                    removable: true
                                    displayName: modelData.displayName
                                    source: modelData.source
                                    size: modelData.size
                                    creatureType: modelData.creatureType
                                    ac: modelData.ac
                                    hp: modelData.hp
                                    hitDice: modelData.hitDice
                                    speed: modelData.speed
                                    abilities: modelData.abilities
                                    saves: modelData.saves
                                    skills: modelData.skills
                                    damageResistances: modelData.damageResistances
                                    damageImmunities: modelData.damageImmunities
                                    conditionImmunities: modelData.conditionImmunities
                                    senses: modelData.senses
                                    languages: modelData.languages
                                    traits: modelData.traits
                                    actions: modelData.actions
                                    reactions: modelData.reactions
                                    hasHpTracking: modelData.hasHpTracking
                                    currentHp: modelData.currentHp
                                    maxHp: modelData.maxHp
                                    onHpEdited: (value) => sheetBridge.setCompanionHp(modelData.hpKey, value, "")
                                    onRemoveClicked: sheetBridge.removeVehicle(modelData.index)
                                }
                            }
                            Component {
                                id: vehicleSimpleComp
                                Rectangle {
                                    width: vDelegateLoader.width
                                    implicitHeight: simpleRow.height + 16
                                    radius: 10
                                    color: Theme.surf2
                                    border.color: Theme.gold
                                    RowLayout {
                                        id: simpleRow
                                        x: 12; y: 8
                                        width: parent.width - 24
                                        spacing: 10
                                        MIcon { name: "wagon"; size: 22 }
                                        ColumnLayout {
                                            spacing: 0
                                            Layout.fillWidth: true
                                            Label { text: modelData.displayName; color: Theme.text; font.bold: true; font.pixelSize: Theme.fsBody }
                                            Label { text: modelData.desc; color: Theme.text3; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                        }
                                        MButton {
                                            text: "✕ Remove"
                                            primary: false
                                            height: 28
                                            onClicked: sheetBridge.removeVehicle(modelData.index)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── Summoned Creatures ───────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                radius: 10
                color: Theme.surf
                border.color: Theme.teal
                implicitHeight: summonsCol.height + 24

                ColumnLayout {
                    id: summonsCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 8

                    Label { text: "Summoned Creatures"; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsTitle }
                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        text: "For Summon Celestial, Summon Undead, Summon Fiend, Summon Beast, and similar spells -- pick the spell, the level you're casting it at, and its form."
                    }

                    Label { text: "Spell:"; color: Theme.text2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    ComboBox {
                        id: summonSpellPicker
                        objectName: "summonSpellPicker"
                        Layout.fillWidth: true
                        model: sheetBridge.scalingSummonSpellOptions
                        onCurrentTextChanged: {
                            summonLevelPicker.model = sheetBridge.summonLevelOptions(currentText)
                            summonFormPicker.model = sheetBridge.summonFormOptions(currentText)
                        }
                        Component.onCompleted: {
                            summonLevelPicker.model = sheetBridge.summonLevelOptions(currentText)
                            summonFormPicker.model = sheetBridge.summonFormOptions(currentText)
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        ComboBox {
                            id: summonLevelPicker
                            objectName: "summonLevelPicker"
                            Layout.fillWidth: true
                            displayText: currentIndex >= 0 && model.length > 0 ? "Level " + model[currentIndex] : ""
                        }
                        ComboBox {
                            id: summonFormPicker
                            objectName: "summonFormPicker"
                            Layout.fillWidth: true
                        }
                    }
                    MButton {
                        objectName: "addSummonBtn"
                        Layout.fillWidth: true
                        text: "+ Summon"
                        onClicked: sheetBridge.addSummonedCreature(
                            summonSpellPicker.currentText, summonLevelPicker.currentValue, summonFormPicker.currentText)
                    }

                    Repeater {
                        objectName: "ownedSummonsRepeater"
                        model: sheetBridge.ownedSummons
                        delegate: MStatblockCard {
                            Layout.fillWidth: true
                            removable: true
                            displayName: modelData.displayName
                            source: modelData.source
                            size: modelData.size
                            creatureType: modelData.creatureType
                            ac: modelData.ac
                            hp: modelData.hp
                            hitDice: modelData.hitDice
                            speed: modelData.speed
                            abilities: modelData.abilities
                            saves: modelData.saves
                            skills: modelData.skills
                            damageResistances: modelData.damageResistances
                            damageImmunities: modelData.damageImmunities
                            conditionImmunities: modelData.conditionImmunities
                            senses: modelData.senses
                            languages: modelData.languages
                            traits: modelData.traits
                            actions: modelData.actions
                            reactions: modelData.reactions
                            hasHpTracking: modelData.hasHpTracking
                            currentHp: modelData.currentHp
                            maxHp: modelData.maxHp
                            onHpEdited: (value) => sheetBridge.setCompanionHp(modelData.hpKey, value, "")
                            onRemoveClicked: sheetBridge.removeSummonedCreature(modelData.index)
                        }
                    }
                }
            }

            // ── Wild Shape (browse-only preview; the real transform
            // action lives on the Combat tab) ───────────────────────
            Rectangle {
                Layout.fillWidth: true
                visible: sheetBridge.wildShapeBrowseAvailable
                radius: 10
                color: Theme.surf
                border.color: Theme.green
                implicitHeight: wsCol.height + 24

                ColumnLayout {
                    id: wsCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 8

                    Label { text: "Wild Shape"; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsTitle }
                    Label { text: sheetBridge.wildShapeBrowseInfoText; color: Theme.text3; font.pixelSize: Theme.fsSmall }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Label { text: "Turn into:"; color: Theme.text2; font.bold: true; font.pixelSize: Theme.fsSmall }
                        ComboBox {
                            id: wsBeastPicker
                            objectName: "wsBeastPicker"
                            Layout.fillWidth: true
                            model: sheetBridge.wildShapeBrowseOptions
                            textRole: "name"
                            valueRole: "name"
                            displayText: currentIndex >= 0 && model.length > 0
                                         ? model[currentIndex].name + "  (CR " + model[currentIndex].crLabel + ")"
                                         : ""
                        }
                    }

                    MStatblockCard {
                        id: wsPreviewCard
                        Layout.fillWidth: true
                        visible: wsBeastPicker.currentValue !== undefined && wsBeastPicker.currentValue !== ""
                        property var sb: (wsBeastPicker.currentValue && wsBeastPicker.currentValue.length > 0)
                                          ? sheetBridge.wildShapeBeastStatblock(wsBeastPicker.currentValue) : null
                        displayName: sb ? sb.displayName : ""
                        source: sb ? sb.source : ""
                        size: sb ? sb.size : ""
                        creatureType: sb ? sb.creatureType : ""
                        ac: sb ? sb.ac : ""
                        hp: sb ? sb.hp : ""
                        hitDice: sb ? sb.hitDice : ""
                        speed: sb ? sb.speed : ""
                        abilities: sb ? sb.abilities : []
                        saves: sb ? sb.saves : []
                        skills: sb ? sb.skills : []
                        damageResistances: sb ? sb.damageResistances : ""
                        damageImmunities: sb ? sb.damageImmunities : ""
                        conditionImmunities: sb ? sb.conditionImmunities : ""
                        senses: sb ? sb.senses : ""
                        languages: sb ? sb.languages : ""
                        traits: sb ? sb.traits : []
                        actions: sb ? sb.actions : []
                        reactions: sb ? sb.reactions : []
                        hasHpTracking: false
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                visible: sheetBridge.activeCompanions.length === 0 && sheetBridge.summonablePrompts.length === 0
                         && !sheetBridge.wildShapeBrowseAvailable && sheetBridge.ownedSummons.length === 0
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                text: "No creatures yet. Add one from the Bestiary below, or cast a spell that summons one."
            }

            // ── Class-granted companions (Steel Defender, Beast Master
            // beasts, Homunculus Servant, Eldritch Cannon, etc.) ─────
            Repeater {
                objectName: "activeCompanionsRepeater"
                model: sheetBridge.activeCompanions
                delegate: Loader {
                    Layout.fillWidth: true
                    sourceComponent: modelData.isEldritchCannon ? cannonCardComp : companionCardComp

                    Component {
                        id: companionCardComp
                        MStatblockCard {
                            width: parent ? parent.width : 0
                            displayName: modelData.displayName
                            source: modelData.source
                            size: modelData.size
                            creatureType: modelData.creatureType
                            ac: modelData.ac
                            hp: modelData.hp
                            hitDice: modelData.hitDice
                            speed: modelData.speed
                            abilities: modelData.abilities
                            saves: modelData.saves
                            skills: modelData.skills
                            damageResistances: modelData.damageResistances
                            damageImmunities: modelData.damageImmunities
                            conditionImmunities: modelData.conditionImmunities
                            senses: modelData.senses
                            languages: modelData.languages
                            traits: modelData.traits
                            actions: modelData.actions
                            reactions: modelData.reactions
                            hasHpTracking: modelData.hasHpTracking
                            currentHp: modelData.currentHp
                            maxHp: modelData.maxHp
                            onHpEdited: (value) => sheetBridge.setCompanionHp(modelData.hpKey, value, modelData.companionKey)
                        }
                    }
                    Component {
                        id: cannonCardComp
                        Rectangle {
                            width: parent ? parent.width : 0
                            radius: 10
                            color: Theme.surf
                            border.color: Theme.teal2
                            implicitHeight: cannonCol.height + 24
                            ColumnLayout {
                                id: cannonCol
                                x: 14; y: 12
                                width: parent.width - 28
                                spacing: 6
                                Label { text: modelData.displayName; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsTitle }
                                Label { text: modelData.source; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                                Label { text: modelData.size + " " + modelData.creatureType; color: Theme.text2; font.bold: true; font.pixelSize: Theme.fsSmall }
                                RowLayout {
                                    spacing: 18
                                    Label { text: "AC " + modelData.ac; color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsBody }
                                    Label { text: "HP " + modelData.hp; color: Theme.green2; font.bold: true; font.pixelSize: Theme.fsBody }
                                }
                                Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: modelData.notes; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                                Label {
                                    text: "ACTIVATION (bonus action, choose one type each time you create it)"
                                    color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsSmall
                                }
                                Repeater {
                                    model: modelData.cannonTypes
                                    delegate: Label {
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                        color: Theme.text; font.pixelSize: Theme.fsSmall
                                        text: modelData.name + ". " + modelData.desc
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── Summon-gated companions not yet summoned (Drake
            // Companion, Dancing Item, Wildfire Spirit) ─────────────
            Repeater {
                objectName: "summonablePromptsRepeater"
                model: sheetBridge.summonablePrompts
                delegate: Rectangle {
                    Layout.fillWidth: true
                    radius: 10
                    color: Theme.surf2
                    border.color: Theme.teal
                    implicitHeight: promptCol.height + 24
                    ColumnLayout {
                        id: promptCol
                        x: 14; y: 12
                        width: parent.width - 28
                        spacing: 6
                        Label { text: modelData.displayName; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsTitle }
                        Label { text: modelData.statusText; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                        MButton {
                            text: modelData.buttonLabel
                            onClicked: sheetBridge.summonCompanion(modelData.key)
                        }
                    }
                }
            }

            // ── Add a Creature: the Bestiary as a browser, the way Add
            // Equipment and Add a Spell are on their pages ─────────────
            MCard {
                id: addCreatureCard
                objectName: "addCreatureCard"
                Layout.fillWidth: true
                title: "Add a Creature"
                iconName: "paw"
                readonly property QtObject bBridge: Window.window ? Window.window.bestiaryBridge : null
                property var results: []
                function refresh() {
                    if (!bBridge) return
                    function picked(box) { return box.currentIndex > 0 ? String(box.model[box.currentIndex]) : "" }
                    results = bBridge.find(crSearch.text, picked(crKind), picked(crSize),
                                           picked(crMin), picked(crMax), picked(crMove))
                }
                Component.onCompleted: refresh()
                Timer { id: crTyping; interval: 200; onTriggered: addCreatureCard.refresh() }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    MTextField {
                        id: crSearch
                        objectName: "creatureSearchField"
                        Layout.fillWidth: true
                        placeholderText: "Search creatures…"
                        onTextChanged: crTyping.restart()
                    }
                    MFilterButton {
                        objectName: "creatureFilterButton"
                        count: crFilters.activeCount
                        onClicked: crFilters.open()
                    }
                }
                MFilterDrawer {
                    id: crFilters
                    objectName: "creatureFilterDrawer"
                    title: "Creature filters"
                    activeCount: (crKind.currentIndex > 0) + (crSize.currentIndex > 0) + (crMin.currentIndex > 0)
                                 + (crMax.currentIndex > 0) + (crMove.currentIndex > 0)
                    onCleared: { crKind.currentIndex = 0; crSize.currentIndex = 0; crMin.currentIndex = 0
                                 crMax.currentIndex = 0; crMove.currentIndex = 0 }
                    Label { text: "Type"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                    ComboBox {
                        id: crKind; Layout.fillWidth: true
                        model: ["Any type"].concat(addCreatureCard.bBridge ? addCreatureCard.bBridge.kinds : [])
                        onCurrentIndexChanged: addCreatureCard.refresh()
                    }
                    Label { text: "Size"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                    ComboBox {
                        id: crSize; Layout.fillWidth: true
                        model: ["Any size"].concat(addCreatureCard.bBridge ? addCreatureCard.bBridge.sizes : [])
                        onCurrentIndexChanged: addCreatureCard.refresh()
                    }
                    Label { text: "Challenge rating"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                    ComboBox {
                        id: crMin; Layout.fillWidth: true
                        model: ["CR from"].concat(addCreatureCard.bBridge ? addCreatureCard.bBridge.crs : [])
                        displayText: currentIndex > 0 ? "CR " + currentText + " up" : currentText
                        onCurrentIndexChanged: addCreatureCard.refresh()
                    }
                    ComboBox {
                        id: crMax; Layout.fillWidth: true
                        model: ["CR to"].concat(addCreatureCard.bBridge ? addCreatureCard.bBridge.crs : [])
                        displayText: currentIndex > 0 ? "up to CR " + currentText : currentText
                        onCurrentIndexChanged: addCreatureCard.refresh()
                    }
                    Label { text: "Moves"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                    ComboBox {
                        id: crMove; Layout.fillWidth: true
                        model: ["Any movement"].concat(addCreatureCard.bBridge ? addCreatureCard.bBridge.moves : [])
                        onCurrentIndexChanged: addCreatureCard.refresh()
                    }
                }
                Label {
                    text: addCreatureCard.results.length === 0 ? "No creature matches. Try fewer words or another filter."
                          : addCreatureCard.results.length.toLocaleString(Qt.locale(), "f", 0)
                            + (addCreatureCard.results.length === 1 ? " creature" : " creatures")
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 260
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.border
                    clip: true
                    ListView {
                        objectName: "creatureResultsListView"
                        anchors.fill: parent
                        anchors.margins: 4
                        clip: true
                        model: addCreatureCard.results
                        // View and Add buttons, as the other browsers: browsing
                        // can't add a creature by accident
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 52
                            color: "transparent"
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 4
                                spacing: 8
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 1
                                    Label { text: modelData.name; color: Theme.text; font.pixelSize: Theme.fsBody
                                            elide: Text.ElideRight; Layout.fillWidth: true }
                                    Label { text: modelData.line; color: Theme.text3; font.pixelSize: Theme.fsSmall
                                            elide: Text.ElideRight; Layout.fillWidth: true }
                                }
                                MButton {
                                    primary: false
                                    implicitWidth: 40
                                    height: 34
                                    iconName: "search"   // View -- a magnifying glass
                                    iconSize: 22
                                    Accessible.name: "View"
                                    onClicked: { creatureView.name = modelData.name; creatureView.open() }
                                }
                                MButton {
                                    objectName: "addCreature_" + modelData.name
                                    implicitWidth: 64
                                    height: 34
                                    text: "Add"
                                    onClicked: sheetBridge.addBestiaryCreature(modelData.name)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // a creature's stat block, from its magnifying glass
    Dialog {
        id: creatureView
        objectName: "creatureViewDialog"
        property string name: ""
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: parent ? parent.width - 24 : 360
        height: parent ? parent.height - 80 : 600
        padding: 14
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Theme.scrim }
        contentItem: ColumnLayout {
            spacing: 8
            Label {
                text: creatureView.name
                color: Theme.gold2
                font.pixelSize: Theme.fsHead
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Flickable {
                id: viewFlick
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: viewText.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollIndicator.vertical: ScrollIndicator {}
                Label {
                    id: viewText
                    width: viewFlick.width
                    textFormat: Text.StyledText
                    wrapMode: Text.WordWrap
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    text: creatureView.name !== "" && addCreatureCard.bBridge
                          ? addCreatureCard.bBridge.statblock(creatureView.name, Theme.gold2.toString()) : ""
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    Layout.fillWidth: true
                    primary: false
                    text: "Close"
                    onClicked: creatureView.close()
                }
                MButton {
                    Layout.fillWidth: true
                    text: "Add"
                    onClicked: { sheetBridge.addBestiaryCreature(creatureView.name); creatureView.close() }
                }
            }
        }
    }
}
