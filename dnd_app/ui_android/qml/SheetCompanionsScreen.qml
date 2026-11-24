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

    // One group of creatures: a header to open or close it (remembered on
    // the character, as on desktop), and its cards under it
    component CreatureGroup: ColumnLayout {
        id: g
        property string name: ""
        property int count: 0
        readonly property bool open: sheetBridge.closedCreatureGroups.indexOf(name) < 0
        default property alias content: body.data
        Layout.fillWidth: true
        visible: count > 0
        spacing: 8
        Rectangle {
            objectName: "creatureGroupHeader_" + g.name
            Layout.fillWidth: true
            implicitHeight: 40
            radius: 8
            color: Theme.surf2
            border.color: Theme.border
            Label {
                anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                text: (g.open ? "▾  " : "▸  ") + g.name + "   (" + g.count + ")"
                color: Theme.gold2
                font.pixelSize: Theme.fsBody
                font.bold: true
            }
            MouseArea {
                anchors.fill: parent
                onClicked: sheetBridge.toggleCreatureGroup(g.name, !g.open)
            }
        }
        ColumnLayout {
            id: body
            Layout.fillWidth: true
            Layout.leftMargin: 4
            visible: g.open
            spacing: 10
        }
    }

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

            // ── Your creatures, in groups to open and close (desktop's
            // Creatures tab): a group with nothing in it isn't shown
            CreatureGroup {
                id: grpMounts
                name: "Mounts"
                count: sheetBridge.ownedMounts.length + sheetBridge.ownedSummons.filter(function (e) { return e.group === "Mounts" }).length
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
                        onHeld: root.creatureOptions(modelData.displayName, "mount", modelData.index, "", modelData)
                    }
                }
                Repeater {
                    model: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Mounts" })
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        MStatblockCard {
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
                            onHeld: root.creatureOptions(modelData.displayName, "summon", modelData.index, modelData.group, modelData)
                        }
                    }
                }
            }
            CreatureGroup {
                id: grpCompanions
                name: "Companions"
                count: sheetBridge.activeCompanions.length + sheetBridge.summonablePrompts.length + sheetBridge.ownedSummons.filter(function (e) { return e.group === "Companions" }).length
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
                                onHeld: root.creatureOptions(modelData.displayName, "companion", -1, "", modelData)
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

                Repeater {
                    model: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Companions" })
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        MStatblockCard {
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
                            onHeld: root.creatureOptions(modelData.displayName, "summon", modelData.index, modelData.group, modelData)
                        }
                    }
                }
            }
            CreatureGroup {
                id: grpFamiliars
                name: "Familiars"
                count: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Familiars" }).length
                Repeater {
                    model: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Familiars" })
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        MStatblockCard {
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
                            onHeld: root.creatureOptions(modelData.displayName, "summon", modelData.index, modelData.group, modelData)
                        }
                    }
                }
            }
            CreatureGroup {
                id: grpSummons
                name: "Summons"
                count: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Summons" }).length
                Repeater {
                    model: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Summons" })
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        MStatblockCard {
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
                            onHeld: root.creatureOptions(modelData.displayName, "summon", modelData.index, modelData.group, modelData)
                        }
                    }
                }
            }
            CreatureGroup {
                id: grpWildShape
                name: "Wild Shape"
                count: sheetBridge.wildShapeBrowseAvailable ? 1 : 0
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

            }
            CreatureGroup {
                id: grpVehicles
                name: "Vehicles"
                count: sheetBridge.ownedVehicles.length
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
                                onHeld: root.creatureOptions(modelData.displayName, "vehicle", modelData.index, "", modelData)
                            }
                        }
                        Component {
                            id: vehicleSimpleComp
                            Rectangle {
                                width: vDelegateLoader.width
                                implicitHeight: simpleRow.height + 16
                                radius: 10
                                color: Theme.surf
                                border.color: Theme.border
                                Rectangle { width: 3; radius: 1.5; color: Theme.gold
                                            anchors { left: parent.left; top: parent.top; bottom: parent.bottom; topMargin: 6; bottomMargin: 6 } }
                                MouseArea {
                                    anchors.fill: parent
                                    pressAndHoldInterval: 450
                                    onPressAndHold: root.creatureOptions(modelData.displayName, "vehicle", modelData.index, "")
                                }
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

                                }
                            }
                        }
                    }
                }
            }
            CreatureGroup {
                id: grpOther
                name: "Other"
                count: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Other" }).length
                Repeater {
                    model: sheetBridge.ownedSummons.filter(function (e) { return e.group === "Other" })
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        MStatblockCard {
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
                            onHeld: root.creatureOptions(modelData.displayName, "summon", modelData.index, modelData.group, modelData)
                        }
                    }
                }
            }
            Label {
                objectName: "noCreatures"
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                visible: grpMounts.count + grpCompanions.count + grpFamiliars.count + grpSummons.count
                         + grpWildShape.count + grpVehicles.count + grpOther.count === 0
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                text: "No creatures yet. Add one from the Bestiary below, buy a mount or vehicle in your Inventory, or cast a spell that summons one."
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
                property var mvResults: sheetBridge.mountVehicleRows("")

                TabBar {
                    id: crTabs
                    objectName: "addCreatureTabs"
                    Layout.fillWidth: true
                    TabButton { text: "Bestiary" }
                    TabButton { objectName: "mountsVehiclesTab"; text: "Mounts && Vehicles" }
                }

                // ── Mounts & Vehicles: a mount into Mounts, a vehicle into Vehicles
                MTextField {
                    objectName: "mountVehicleSearch"
                    visible: crTabs.currentIndex === 1
                    Layout.fillWidth: true
                    placeholderText: "Search mounts and vehicles…"
                    onTextChanged: addCreatureCard.mvResults = sheetBridge.mountVehicleRows(text)
                }
                Rectangle {
                    visible: crTabs.currentIndex === 1
                    Layout.fillWidth: true
                    Layout.preferredHeight: 300
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.border
                    clip: true
                    ListView {
                        objectName: "mountVehicleListView"
                        anchors.fill: parent
                        anchors.margins: 4
                        clip: true
                        model: addCreatureCard.mvResults
                        delegate: Rectangle {
                            id: mvRow
                            // a heading where a new kind starts (Mounts, Water vehicles...)
                            readonly property bool firstOfSection: index === 0
                                || addCreatureCard.mvResults[index - 1].section !== modelData.section
                            width: ListView.view.width
                            height: 52 + (firstOfSection ? 26 : 0)
                            color: "transparent"
                            Label {
                                visible: mvRow.firstOfSection
                                y: 6; x: 4
                                text: modelData.section; color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsSmall
                            }
                            RowLayout {
                                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                                height: 52
                                anchors.margins: 4
                                spacing: 8
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 1
                                    Label { text: modelData.name; color: Theme.text; font.pixelSize: Theme.fsBody; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Label { text: modelData.line; color: Theme.text3; font.pixelSize: Theme.fsSmall; elide: Text.ElideRight; Layout.fillWidth: true }
                                }
                                MButton {
                                    primary: false
                                    implicitWidth: 40
                                    height: 34
                                    iconName: "search"
                                    iconSize: 22
                                    Accessible.name: "View"
                                    onClicked: { creatureView.kind = modelData.kind; creatureView.name = modelData.name; creatureView.open() }
                                }
                                MButton {
                                    objectName: "addMountVehicle_" + modelData.name
                                    implicitWidth: 64
                                    height: 34
                                    text: "Add"
                                    onClicked: sheetBridge.addMountOrVehicle(modelData.name, modelData.kind)
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    visible: crTabs.currentIndex === 0
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
                    visible: crTabs.currentIndex === 0
                    text: addCreatureCard.results.length === 0 ? "No creature matches. Try fewer words or another filter."
                          : addCreatureCard.results.length.toLocaleString(Qt.locale(), "f", 0)
                            + (addCreatureCard.results.length === 1 ? " creature" : " creatures")
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                }
                Rectangle {
                    visible: crTabs.currentIndex === 0
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
                                    onClicked: root.askGroup(modelData.name)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Add from the Bestiary: which group, in a popup -- the creature's
    // name at the top, a button per group, Cancel at the bottom
    property string _adding: ""
    function askGroup(name) {
        _adding = name
        var opts = []
        for (var i = 0; i < sheetBridge.creatureGroups.length; ++i)
            opts.push({key: sheetBridge.creatureGroups[i], text: sheetBridge.creatureGroups[i], icon: "paw"})
        addGroupDialog.heading = name
        addGroupDialog.options = opts
        addGroupDialog.open()
    }
    MOptionsDialog {
        id: addGroupDialog
        objectName: "addGroupDialog"
        message: "Add it to which group?"
        cancelDanger: true
        onPicked: (key) => sheetBridge.addBestiaryCreature(root._adding, key)
    }

    // A card's press and hold: Move to another group (a summoned or added
    // creature), and Remove -- desktop's right-click
    property var _held: ({})
    function creatureOptions(name, kind, index, group, card) {
        _held = {kind: kind, index: index, card: card || {}}
        var opts = []
        if (card && card.hasHpTracking) {
            opts.push({key: "maxhp", text: "Set max HP", icon: "heart"})
            if (card.ownMax)
                opts.push({key: "maxhp:reset", text: "Back to its own max (" + card.baseHp + ")", icon: "heart"})
        }
        if (kind === "summon")
            for (var i = 0; i < sheetBridge.creatureGroups.length; ++i) {
                var g = sheetBridge.creatureGroups[i]
                if (g !== group)
                    opts.push({key: "move:" + g, text: "Move to " + g, icon: "paw"})
            }
        if (kind !== "companion")
            opts.push({key: "remove", text: "Remove", icon: "trash"})
        creatureOptionsDialog.heading = name
        creatureOptionsDialog.options = opts
        creatureOptionsDialog.open()
    }
    MOptionsDialog {
        id: creatureOptionsDialog
        objectName: "creatureOptionsDialog"
        onPicked: (key) => {
            var h = root._held
            if (key === "maxhp") {
                maxHpDialog.card = h.card
                maxHpSpin.value = h.card.maxHp
                maxHpDialog.open()
            } else if (key === "maxhp:reset")
                sheetBridge.setCreatureMaxHp(h.card.hpKey, 0)
            else if (key.indexOf("move:") === 0)
                sheetBridge.setCreatureGroup(h.index, key.slice(5))
            else if (key === "remove") {
                if (h.kind === "mount") sheetBridge.removeMount(h.index)
                else if (h.kind === "vehicle") sheetBridge.removeVehicle(h.index)
                else sheetBridge.removeSummonedCreature(h.index)
            }
        }
    }

    // Set max HP: its hit dice and their average to go by
    Dialog {
        id: maxHpDialog
        objectName: "maxHpDialog"
        property var card: ({})
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: Math.min(parent ? parent.width - 32 : 340, 340)
        padding: 16
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Theme.scrim }
        contentItem: ColumnLayout {
            spacing: 12
            Label {
                text: (maxHpDialog.card.displayName || "") + ": max HP"
                color: Theme.gold2; font.pixelSize: Theme.fsHead; font.bold: true
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            Label {
                text: maxHpDialog.card.hitDice
                      ? "Its hit dice: " + maxHpDialog.card.hitDice + " (average " + maxHpDialog.card.hitDiceAverage + "). Roll them, or set any number."
                      : "Set any number."
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap; Layout.fillWidth: true
            }
            MSpinBox {
                id: maxHpSpin
                objectName: "maxHpSpin"
                Layout.fillWidth: true
                implicitHeight: 48
                from: 1
                to: 9999
                holdStep: 5
                live: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton { Layout.fillWidth: true; primary: false; text: "Cancel"; onClicked: maxHpDialog.close() }
                MButton {
                    objectName: "maxHpSave"
                    Layout.fillWidth: true
                    text: "Save"
                    onClicked: { sheetBridge.setCreatureMaxHp(maxHpDialog.card.hpKey, maxHpSpin.value); maxHpDialog.close() }
                }
            }
        }
    }

    // a creature's stat block, from its magnifying glass
    Dialog {
        id: creatureView
        objectName: "creatureViewDialog"
        property string name: ""
        property string kind: ""          // "" a creature; "mount" / "vehicle"
        onClosed: kind = ""
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
                    text: creatureView.name === "" ? ""
                          : creatureView.kind ? sheetBridge.mountVehicleDetails(creatureView.name, creatureView.kind, Theme.gold2.toString())
                          : addCreatureCard.bBridge ? addCreatureCard.bBridge.statblock(creatureView.name, Theme.gold2.toString()) : ""
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
                    onClicked: {
                        if (creatureView.kind) sheetBridge.addMountOrVehicle(creatureView.name, creatureView.kind)
                        else root.askGroup(creatureView.name)
                        creatureView.close()
                    }
                }
            }
        }
    }
}
