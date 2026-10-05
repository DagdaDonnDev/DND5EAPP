import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Equipment"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    property string pendingEnchantKind: ""
    property int pendingEnchantBonus: 0
    property string pendingScrollName: ""

    Component.onCompleted: sheetBridge.refresh()

    // Jump-to-section targets for the drawer's expandable sub-menu (see
    // NavDrawer.qml's sectionSelected).
    function scrollToSection(name) {
        var anchorItem = null
        if (name === "Inventory") anchorItem = invAnchor
        else if (name === "Add Equipment") anchorItem = addEqAnchor
        else if (name === "Magic Items") anchorItem = magicAnchor
        else if (name === "Add a Magic Item") anchorItem = addMiAnchor
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

            // ── Armor & load ────────────────────────────────────────────
            MCard {
                title: "Armor & Load"
                iconName: "shield"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label {
                            text: sheetBridge.armorWorn + (sheetBridge.hasShield ? "  +  Shield" : "")
                            color: Theme.text
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: "AC " + sheetBridge.armorClass
                            color: Theme.teal2
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                        }
                    }
                    MButton {
                        primary: false
                        implicitHeight: 36
                        text: "Change"
                        onClicked: armorDialog.open()
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    visible: sheetBridge.armorWorn !== "No Armor" || sheetBridge.ownsShield
                    MCheckBox {
                        visible: sheetBridge.ownsShield
                        text: "Shield"
                        checked: sheetBridge.hasShield
                        onToggled: sheetBridge.toggleShieldWorn(checked)
                    }
                    Item { Layout.fillWidth: true }
                    MButton {
                        primary: false
                        implicitHeight: 36
                        visible: sheetBridge.armorWorn !== "No Armor"
                        text: "Take Off Armor"
                        onClicked: sheetBridge.toggleArmorWorn(sheetBridge.armorWorn, false)
                    }
                }

                // carrying capacity
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Carrying"; color: Theme.text3; font.pixelSize: Theme.fsSmall; Layout.fillWidth: true }
                    Label {
                        text: sheetBridge.carryLoad.weight + " / " + sheetBridge.carryLoad.capacity + " lb"
                        color: sheetBridge.carryLoad.fraction >= 1 ? Theme.crimson2 : Theme.text2
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 6
                    radius: 3
                    color: Theme.surf3
                    Rectangle {
                        width: parent.width * sheetBridge.carryLoad.fraction
                        height: parent.height
                        radius: 3
                        color: sheetBridge.carryLoad.fraction >= 1 ? Theme.crimson
                             : sheetBridge.carryLoad.fraction > 0.66 ? Theme.amber : Theme.teal2
                    }
                }
            }
            MPickerDialog {
                id: armorDialog
                dialogTitle: "Wear Armor"
                options: sheetBridge.equippableArmor.map(a => a.name)
                onPicked: (value) => sheetBridge.toggleArmorWorn(value, true)
            }

            MPickerDialog {
                id: enchantPickerDialog
                property var rawNames: []
                onPicked: (value) => {
                    var idx = options.indexOf(value)
                    var rawName = idx >= 0 ? rawNames[idx] : value
                    sheetBridge.applyEnchant(root.pendingEnchantKind, root.pendingEnchantBonus, rawName)
                }
            }

            MPickerDialog {
                id: scrollSpellDialog
                dialogTitle: "Which spell is inscribed on this scroll?"
                onPicked: (value) => sheetBridge.addMagicItemWithScrollSpell(root.pendingScrollName, value)
            }


            // ── Currency ────────────────────────────────────────────────
            MCard {
                title: "Currency"
                iconName: "coins"

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 10
                    rowSpacing: 8
                    Repeater {
                        model: sheetBridge.currencyAll
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: modelData.denom
                                color: Theme.gold2
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                Layout.preferredWidth: 26
                            }
                            MSpinBox {
                                // the up/down indicators need ~110px+ to leave
                                // room for the number (see MStatblockCard)
                                Layout.fillWidth: true
                                Layout.minimumWidth: 110
                                from: 0
                                to: 999999
                                value: modelData.amount
                                onValueModified: sheetBridge.setCurrency(modelData.denom, value)
                            }
                        }
                    }
                }
            }

            // ── Inventory ───────────────────────────────────────────────
            // Grouped Weapons / Armor / Consumables / Tools & Gear, equipped
            // items first. Weapons are equipped and armor worn straight from
            // their row (this replaces the separate Weapons checklist).
            MCard {
                id: invAnchor
                title: "Inventory"
                iconName: "gear"

                Label {
                    visible: sheetBridge.equipment.length === 0
                    text: "No items yet -- add some below."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                }

                Repeater {
                    model: sheetBridge.inventoryGroups
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        RowLayout {
                            spacing: 6
                            Label {
                                text: modelData.group
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                            }
                            Label {
                                text: modelData.items.length
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                        }

                        Repeater {
                            model: modelData.items
                            delegate: Rectangle {
                                objectName: "invRow_" + modelData.name
                                Layout.fillWidth: true
                                implicitHeight: invRow.implicitHeight + 14
                                radius: 8
                                color: Theme.surf2
                                border.color: modelData.equipped ? Theme.teal : Theme.border

                                RowLayout {
                                    id: invRow
                                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 8 }
                                    spacing: 8
                                    MIcon {
                                        name: modelData.icon
                                        size: 20
                                        color: modelData.equipped ? Theme.teal2 : Theme.indigo2
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: 0
                                        spacing: 1
                                        Label {
                                            text: (modelData.qty > 1 ? modelData.qty + "× " : "") + modelData.name
                                            color: Theme.text
                                            font.pixelSize: Theme.fsBody
                                            font.bold: modelData.equipped
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                        Label {
                                            text: [modelData.detail,
                                                   modelData.weight > 0 ? (modelData.weight * modelData.qty) + " lb" : "",
                                                   modelData.cost > 0 ? (modelData.cost * modelData.qty) + " gp" : ""]
                                                  .filter(function(x) { return x.length > 0 }).join("  ·  ")
                                            visible: text.length > 0
                                            color: Theme.text3
                                            font.pixelSize: Theme.fsSmall
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }
                                    // equip / wear / use, then remove -- same
                                    // column on every row
                                    MButton {
                                        visible: modelData.equipKind !== ""
                                        primary: false
                                        implicitHeight: 34
                                        text: modelData.equipKind === "weapon" ? (modelData.equipped ? "Unequip" : "Equip")
                                              : (modelData.equipped ? "Take off" : (modelData.equipKind === "shield" ? "Equip" : "Wear"))
                                        onClicked: {
                                            if (modelData.equipKind === "weapon")
                                                sheetBridge.toggleWeaponEquipped(modelData.name, !modelData.equipped)
                                            else if (modelData.equipKind === "shield")
                                                sheetBridge.toggleShieldWorn(!modelData.equipped)
                                            else
                                                sheetBridge.toggleArmorWorn(modelData.name, !modelData.equipped)
                                        }
                                    }
                                    MButton {
                                        visible: modelData.isPotion
                                        primary: false
                                        implicitHeight: 34
                                        text: "Drink"
                                        onClicked: sheetBridge.usePotion(modelData.name)
                                    }
                                    MButton {
                                        visible: modelData.isScroll
                                        primary: false
                                        implicitHeight: 34
                                        text: "Read"
                                        onClicked: sheetBridge.useScroll(modelData.name)
                                    }
                                    MButton {
                                        primary: false
                                        implicitWidth: 38
                                        implicitHeight: 34
                                        iconName: "trash"
                                        iconSize: 16
                                        onClicked: sheetBridge.removeEquipmentItem(modelData.name)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── Add Equipment ────────────────────────────────────────
            MCard {
            id: addEqAnchor
            title: "Add Equipment"
            iconName: "package"
            MTextField {
                id: eqSearch
                Layout.fillWidth: true
                placeholderText: "Search weapons, armor, gear, tools…"
                onTextChanged: eqAddModel.refreshResults()
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Label { text: "Qty"; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                MSpinBox {
                    id: eqQty
                    // MSpinBox's up/down indicators are 36px each (72px
                    // total) -- anything narrower than ~110px leaves too
                    // little room for the number, visually mashing the
                    // "-" glyph against the digits (established in
                    // MStatblockCard.qml's HP spinner).
                    implicitWidth: 110
                    from: 1
                    to: 999
                    value: 1
                }
                MButton {
                    Layout.fillWidth: true
                    primary: false
                    height: 36
                    text: "+ Custom Item"
                    enabled: eqSearch.text.trim().length > 0
                    onClicked: {
                        sheetBridge.addCustomEquipmentItem(eqSearch.text.trim(), eqQty.value)
                        eqSearch.text = ""
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ComboBox {
                    id: eqCategoryFilter
                    Layout.fillWidth: true
                    model: sheetBridge.equipmentCategories
                    onCurrentIndexChanged: eqAddModel.refreshResults()
                }
                ComboBox {
                    id: eqSortBy
                    Layout.preferredWidth: 120
                    model: ["Name", "Cost", "Weight"]
                    onCurrentIndexChanged: eqAddModel.refreshResults()
                }
            }

            QtObject {
                id: eqAddModel
                objectName: "eqAddModel"
                property var results: sheetBridge.searchAddableEquipment("", "All", "Name")
                function refreshResults() {
                    // Read the ComboBoxes' selection via model[currentIndex]
                    // rather than currentText -- currentText is a derived
                    // property recomputed by a separate internal binding
                    // that can still be running the OLD value at the exact
                    // moment onCurrentIndexChanged fires, while currentIndex
                    // itself (the property that triggered this handler) is
                    // always already up to date.
                    results = sheetBridge.searchAddableEquipment(
                        eqSearch.text, eqCategoryFilter.model[eqCategoryFilter.currentIndex],
                        eqSortBy.model[eqSortBy.currentIndex])
                }
            }
            Connections {
                target: sheetBridge
                function onStatsChanged() { eqAddModel.refreshResults() }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 180
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                clip: true

                ListView {
                    objectName: "equipmentSearchResultsListView"
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    model: eqAddModel.results
                    delegate: ItemDelegate {
                        width: ListView.view.width
                        height: 48
                        contentItem: RowLayout {
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label { text: modelData.name; color: Theme.text; font.pixelSize: Theme.fsBody }
                                Label { text: modelData.category + (modelData.detail ? "  ·  " + modelData.detail : ""); color: Theme.text3; font.pixelSize: Theme.fsSmall }
                            }
                        }
                        // Refreshing eqAddModel here too (in addition to
                        // the Connections-driven refresh on statsChanged
                        // below) would double-refresh, and for a result
                        // list that excludes already-added items (like
                        // the magic item browser below), a second
                        // refresh mid-click can destroy this very
                        // delegate while onClicked is still running --
                        // let the single Connections-driven refresh
                        // handle it.
                        onClicked: sheetBridge.addEquipmentItem(modelData.name, eqQty.value)
                    }
                }
            }

            }

            // ── Magic Items ──────────────────────────────────────────
            MCard {
            id: magicAnchor
            title: "Magic Items"
            iconName: "magic"
            Label {
                visible: sheetBridge.magicItems.length === 0
                text: "No magic items yet -- search below to add some."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
            }
            Repeater {
                objectName: "magicItemsRepeater"
                model: sheetBridge.magicItems
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: miCol.height + 16
                    radius: 8
                    color: Theme.surf2
                    border.color: modelData.attuned ? Theme.indigo2 : Theme.border

                    Column {
                        id: miCol
                        x: 10; y: 8
                        width: parent.width - 20
                        spacing: 4

                        RowLayout {
                            width: parent.width
                            Label {
                                text: modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                                Layout.fillWidth: true
                                wrapMode: Text.WordWrap
                            }
                            Label {
                                text: modelData.rarity
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                        }
                        Label {
                            text: modelData.type + (modelData.needsAttunement ? "  ·  Requires Attunement" : "")
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                        }
                        RowLayout {
                            width: parent.width
                            visible: modelData.resistanceChoicePool.length > 0
                            spacing: 6
                            Label { text: "Resists:"; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                            ComboBox {
                                Layout.fillWidth: true
                                model: ["— choose damage type —"].concat(modelData.resistanceChoicePool)
                                currentIndex: modelData.resistanceChoiceCurrent
                                             ? modelData.resistanceChoicePool.indexOf(modelData.resistanceChoiceCurrent) + 1
                                             : 0
                                onActivated: (idx) => sheetBridge.setMagicItemDamageType(
                                    modelData.name, idx === 0 ? "" : modelData.resistanceChoicePool[idx - 1])
                            }
                        }
                        RowLayout {
                            width: parent.width
                            spacing: 8
                            Flow {
                                Layout.fillWidth: true
                                spacing: 8
                                MCheckBox {
                                    visible: modelData.needsAttunement
                                    text: "Attuned"
                                    checked: modelData.attuned
                                    onToggled: sheetBridge.setMagicItemAttuned(modelData.name, checked)
                                }
                                MCheckBox {
                                    text: "Equipped"
                                    checked: modelData.equipped
                                    onToggled: sheetBridge.setMagicItemEquipped(modelData.name, checked)
                                }
                            }
                            // Fixed right-hand column -- Remove always lands in the
                            // same place regardless of how many checkboxes this card
                            // shows, instead of trailing directly after them in a
                            // shared wrapping Flow.
                            MButton {
                                primary: false
                                height: 32
                                visible: sheetBridge.canStudyManual(modelData.name)
                                text: "Study"
                                onClicked: sheetBridge.studyAbilityManual(modelData.name)
                            }
                            MButton {
                                primary: false
                                implicitWidth: 38
                                height: 34
                                iconName: "trash"
                                iconSize: 16
                                onClicked: sheetBridge.removeMagicItem(modelData.name)
                            }
                        }
                    }
                }
            }

            }

            // ── Add a Magic Item ─────────────────────────────────────
            MCard {
            id: addMiAnchor
            title: "Add a Magic Item"
            iconName: "magic"
            MTextField {
                id: miSearch
                Layout.fillWidth: true
                placeholderText: "Search magic items…"
                onTextChanged: miAddModel.refreshResults()
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ComboBox {
                    id: miSlotFilter
                    Layout.fillWidth: true
                    model: sheetBridge.magicItemSlots
                    onCurrentIndexChanged: miAddModel.refreshResults()
                }
                ComboBox {
                    id: miRarityFilter
                    Layout.fillWidth: true
                    model: sheetBridge.magicItemRarities
                    onCurrentIndexChanged: miAddModel.refreshResults()
                }
            }
            ComboBox {
                id: miAttuneFilter
                Layout.fillWidth: true
                model: sheetBridge.magicItemAttunementOptions
                onCurrentIndexChanged: miAddModel.refreshResults()
            }

            QtObject {
                id: miAddModel
                objectName: "miAddModel"
                property var results: sheetBridge.searchAddableMagicItems("", "All Slots", "All Rarities", "All")
                function refreshResults() {
                    // See eqAddModel.refreshResults() for why model[currentIndex]
                    // is used instead of currentText here.
                    results = sheetBridge.searchAddableMagicItems(
                        miSearch.text, miSlotFilter.model[miSlotFilter.currentIndex],
                        miRarityFilter.model[miRarityFilter.currentIndex],
                        miAttuneFilter.model[miAttuneFilter.currentIndex])
                }
            }
            Connections {
                target: sheetBridge
                function onStatsChanged() { miAddModel.refreshResults() }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 220
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                clip: true

                ListView {
                    objectName: "magicItemSearchResultsListView"
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    model: miAddModel.results
                    delegate: ItemDelegate {
                        width: ListView.view.width
                        height: 48
                        contentItem: RowLayout {
                            Label {
                                text: modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                            Label {
                                text: modelData.rarity
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                        }
                        // See the equipment browser's onClicked above --
                        // the Connections-driven refresh on statsChanged
                        // already updates miAddModel; a second explicit
                        // refresh here would destroy this delegate mid-
                        // click (this list excludes already-added items,
                        // so adding one always shrinks it).
                        onClicked: {
                            var info = sheetBridge.classifyMagicItemPick(modelData.name)
                            if (info.kind === "enchant") {
                                pendingEnchantKind = info.itemKind
                                pendingEnchantBonus = info.bonus
                                if (info.itemKind === "Shield") {
                                    sheetBridge.applyShieldEnchant(info.bonus)
                                } else {
                                    var candidates = sheetBridge.enchantCandidates(info.itemKind, info.bonus)
                                    if (candidates.length === 0) {
                                        sheetBridge.notify("You don't own a nonmagical " + info.itemKind.toLowerCase() + " to enchant yet.")
                                    } else {
                                        enchantPickerDialog.dialogTitle = "Enchant which " + info.itemKind.toLowerCase() + "?"
                                        enchantPickerDialog.options = candidates.map(function(c) {
                                            var tag = c.equipped ? "  (equipped)" : "  (owned)"
                                            if (c.existingBonus) tag += "  — currently +" + c.existingBonus
                                            return c.name + tag
                                        })
                                        enchantPickerDialog.rawNames = candidates.map(function(c) { return c.name })
                                        enchantPickerDialog.open()
                                    }
                                }
                            } else if (info.kind === "scroll") {
                                pendingScrollName = modelData.name
                                var spells = sheetBridge.spellsForScrollLevel(info.level)
                                if (spells.length === 0) {
                                    sheetBridge.addMagicItem(modelData.name)
                                } else {
                                    scrollSpellDialog.options = spells
                                    scrollSpellDialog.open()
                                }
                            } else {
                                sheetBridge.addMagicItem(modelData.name)
                            }
                        }
                    }
                }
            }
            }
        }
    }
}
