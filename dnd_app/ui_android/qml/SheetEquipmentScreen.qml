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

    // How this screen is put together:
    //   Inventory    -- grouped rows; tap a button for the everyday action,
    //                   press and hold a row (or tap its ×N) to set how many
    //   Add Equipment -- search + Qty; "+ Add … as a custom item" under the
    //                   results when nothing fits
    //   Magic Items  -- one card per owned copy, bordered in its rarity;
    //                   press and hold for attune / study / remove
    //   Add a Magic Item -- the browser, sorted rarity then name
    //
    // Adding a magic item from the browser:
    //   "+N Weapon/Armor/Shield" -> pick which owned item to enchant
    //   "Spell Scroll (Nth level)" -> pick the spell on it (never blank)
    //   anything else            -> added as is (a new copy each time)
    function pickMagicItem(name) {
        var info = sheetBridge.classifyMagicItemPick(name)
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
            pendingScrollName = name
            var spells = sheetBridge.spellsForScrollLevel(info.level)
            // every scroll carries a spell -- no blank ones
            if (spells.length === 0) {
                sheetBridge.notify("There are no spells of that level to put on a scroll.")
            } else {
                scrollSpellDialog.options = spells
                scrollSpellDialog.open()
            }
        } else {
            sheetBridge.addMagicItem(name)
        }
    }

    function showItemDetail(name) {
        Window.window.pendingItemDetail = sheetBridge.getItemDetail(name)
        itemDetail.open()
    }

    // ── Press and hold menus (things you don't do often) ─────────────
    property var heldItem: null

    // Inventory: press and hold -> change how many you have (0 removes it).
    // (magic ammunition uses the same dialog -- its stack has a uid)
    function openAmountDialog(item) {
        heldItem = item
        amountQty.value = Math.max(1, item.qty || 1)
        amountDialog.open()
    }

    // A weapon a monk could use with Dedicated Weapon: press and hold ->
    //   How many / Make dedicated weapon (or Stop using as dedicated weapon)
    // Anything else goes straight to how many you have.
    function openInventoryHold(item) {
        if (!item.canDedicate && !item.dedicated) {
            openAmountDialog(item)
            return
        }
        heldItem = item
        weaponOptionsDialog.heading = item.name
        weaponOptionsDialog.options = [
            {key: "amount", text: "How many", icon: "package"},
            item.dedicated
                ? {key: "undedicate", text: "Stop using as dedicated weapon", icon: "dagger"}
                : {key: "dedicate", text: "Make dedicated weapon", icon: "dagger"}
        ]
        weaponOptionsDialog.open()
    }

    MOptionsDialog {
        id: weaponOptionsDialog
        objectName: "weaponOptionsDialog"
        onPicked: (key) => {
            var it = root.heldItem
            if (!it) return
            if (key === "amount") root.openAmountDialog(it)
            else if (key === "dedicate") sheetBridge.setDedicatedWeapon(it.name)
            else if (key === "undedicate") sheetBridge.setDedicatedWeapon("")
        }
    }

    // Magic items: press and hold -> a menu bordered in the item's rarity
    //   Attune / End attunement -- only if it needs attunement
    //   Study                   -- a manual or tome not yet studied
    //   Remove                  -- always
    // Each acts on this one copy (its uid), not every copy of the name.
    function openMagicItemOptions(item) {
        heldItem = item
        var opts = []
        if (item.needsAttunement)
            opts.push({key: "attune", text: item.attuned ? "End attunement" : "Attune", icon: "magic"})
        if (item.canStudy)
            opts.push({key: "study", text: "Study", icon: "spells"})
        opts.push({key: "remove", text: "Remove", icon: "trash"})
        magicOptionsDialog.heading = item.name
        magicOptionsDialog.accent = Theme.rarityColor(item.rarity)
        magicOptionsDialog.options = opts
        magicOptionsDialog.open()
    }

    MOptionsDialog {
        id: magicOptionsDialog
        objectName: "magicOptionsDialog"
        onPicked: (key) => {
            var it = root.heldItem
            if (!it) return
            if (key === "attune") sheetBridge.setMagicItemAttuned(it.uid, !it.attuned)
            else if (key === "study") sheetBridge.studyAbilityManual(it.uid)
            else if (key === "remove") sheetBridge.removeMagicItem(it.uid)
        }
    }

    // How many you have: type a number or use - / + (hold to step by 5)
    Dialog {
        id: amountDialog
        objectName: "amountDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: Math.min(parent ? parent.width - 32 : 340, 340)
        padding: 16
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                text: root.heldItem ? root.heldItem.name : ""
                color: Theme.gold2
                font.pixelSize: Theme.fsHead
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "How many do you have?"
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                Layout.fillWidth: true
            }
            MSpinBox {
                id: amountQty
                objectName: "amountQtySpin"
                Layout.fillWidth: true
                implicitHeight: 48
                from: 0
                to: 9999
                holdStep: 5
                // the typed number counts straight away -- no need to
                // press Enter before tapping Save
                live: true
            }
            Label {
                text: amountQty.value === 0 ? "0 removes it from your inventory."
                                            : "Set it to 0 to remove it."
                color: amountQty.value === 0 ? Theme.crimson2 : Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    Layout.fillWidth: true
                    primary: false
                    text: "Cancel"
                    onClicked: amountDialog.close()
                }
                MButton {
                    objectName: "amountSave"
                    Layout.fillWidth: true
                    iconName: amountQty.value === 0 ? "trash" : ""
                    text: amountQty.value === 0 ? "Remove" : "Save"
                    onClicked: {
                        var name = root.heldItem ? root.heldItem.name : ""
                        var n = amountQty.value
                        amountDialog.close()
                        if (!name) return
                        if (root.heldItem.uid) sheetBridge.setMagicItemQuantity(root.heldItem.uid, n)
                        else sheetBridge.setEquipmentQuantity(name, n)
                    }
                }
            }
        }
    }

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

            // a blank scroll (an older save, a PDF import) being used: which
            // spell is on it -- then it's cast
            MPickerDialog {
                id: scrollBindDialog
                objectName: "scrollBindDialog"
                property string scrollName: ""
                dialogTitle: "Which spell is on this scroll?"
                onPicked: (value) => sheetBridge.bindScrollSpell(scrollName, value)
            }
            Connections {
                target: sheetBridge
                function onScrollSpellNeeded(name, level) {
                    scrollBindDialog.scrollName = name
                    scrollBindDialog.options = sheetBridge.spellsForScrollLevel(level)
                    scrollBindDialog.open()
                }
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
                                color: invHold.pressed ? Theme.surf3 : Theme.surf2
                                // border colour means rarity (magic potions/scrolls),
                                // never "equipped" -- a green border would read as
                                // Uncommon; equipped shows as a bright icon, bold
                                // name and an "Equipped" tag instead
                                border.color: modelData.rarity ? Theme.rarityColor(modelData.rarity) : Theme.border
                                border.width: modelData.rarity ? 2 : 1

                                // press and hold: change how many you have
                                // (or, for a monk, pick the Dedicated Weapon)
                                MouseArea {
                                    id: invHold
                                    objectName: "invHold_" + modelData.name
                                    anchors.fill: parent
                                    pressAndHoldInterval: 450
                                    onPressAndHold: root.openInventoryHold(modelData)
                                }

                                RowLayout {
                                    id: invRow
                                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 8 }
                                    spacing: 8
                                    MIcon {
                                        name: modelData.icon
                                        size: 20
                                        color: modelData.equipped ? Theme.text : Theme.indigo2
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: 0
                                        spacing: 1
                                        Label {
                                            // a stack's count is its own button (below)
                                            text: modelData.name
                                            color: Theme.text
                                            font.pixelSize: Theme.fsBody
                                            font.bold: modelData.equipped
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                        Label {
                                            text: [modelData.equipped ? "Equipped" : "",
                                                   modelData.detail,
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
                                    // row buttons, right to left: View (magnifier) ·
                                    // the stack's count (×N, opens the amount dialog) ·
                                    // the everyday action -- Equip/Wear, Drink, or Use
                                    // (a scroll: casts its spell)
                                    MButton {
                                        visible: modelData.equipKind !== ""
                                        primary: false
                                        implicitWidth: 86
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
                                        implicitWidth: 64
                                        implicitHeight: 34
                                        text: "Drink"
                                        onClicked: sheetBridge.usePotion(modelData.name)
                                    }
                                    MButton {
                                        visible: modelData.isScroll
                                        primary: false
                                        implicitWidth: 64
                                        implicitHeight: 34
                                        // casts the scroll's spell (asks which, on a blank one)
                                        text: "Use"
                                        onClicked: sheetBridge.useScroll(modelData.name)
                                    }
                                    // how many you have -- tap to change it
                                    MButton {
                                        objectName: "qtyButton_" + modelData.name
                                        visible: modelData.qty > 1
                                        primary: false
                                        implicitWidth: Math.max(40, implicitContentWidth + 20)
                                        implicitHeight: 34
                                        text: "×" + modelData.qty
                                        Accessible.name: "Quantity " + modelData.qty
                                        onClicked: root.openAmountDialog(modelData)
                                    }
                                    MButton {
                                        primary: false
                                        implicitWidth: 40
                                        implicitHeight: 34
                                        iconName: "search"   // View -- a magnifying glass
                                        iconSize: 22
                                        Accessible.name: "View"
                                        onClicked: root.showItemDetail(modelData.name)
                                    }
                                }
                            }
                        }
                    }
                }

                Label {
                    visible: sheetBridge.equipment.length > 0
                    text: "Press and hold an item to change how many you have."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }

            // ── Add Equipment ────────────────────────────────────────
            MCard {
            id: addEqAnchor
            title: "Add Equipment"
            iconName: "package"
            // search box across the row; category and sort live in the
            // filter drawer behind the funnel button
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MTextField {
                    id: eqSearch
                    objectName: "eqSearchField"
                    Layout.fillWidth: true
                    placeholderText: "Search weapons, armor, gear, tools…"
                    onTextChanged: eqAddModel.refreshResults()
                }
                MFilterButton {
                    objectName: "eqFilterButton"
                    count: eqFilters.activeCount
                    onClicked: eqFilters.open()
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Label { text: "Qty"; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                MSpinBox {
                    id: eqQty
                    objectName: "addQtySpin"
                    // the whole row: the up/down indicators take 72px, so
                    // a narrow box left the number squashed between them
                    Layout.fillWidth: true
                    from: 1
                    to: 999
                    value: 1
                    holdStep: 5
                    live: true
                }
            }

            MFilterDrawer {
                id: eqFilters
                objectName: "eqFilterDrawer"
                title: "Equipment filters"
                // a changed sort counts too: the list isn't in its usual order
                activeCount: (eqCategoryFilter.currentIndex > 0) + (eqSortBy.currentIndex > 0)
                onCleared: { eqCategoryFilter.currentIndex = 0; eqSortBy.currentIndex = 0 }
                Label { text: "Category"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: eqCategoryFilter
                    Layout.fillWidth: true
                    model: sheetBridge.equipmentCategories
                    onCurrentIndexChanged: eqAddModel.refreshResults()
                }
                Label { text: "Sort by"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: eqSortBy
                    Layout.fillWidth: true
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
                    // Same layout as the spell browser: explicit View/Add
                    // buttons rather than a whole-row tap, so browsing a
                    // list can't add things by accident.
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
                                Label {
                                    text: modelData.name
                                    color: Theme.text
                                    font.pixelSize: Theme.fsBody
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: modelData.category + (modelData.detail ? "  ·  " + modelData.detail : "")
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
                                onClicked: root.showItemDetail(modelData.name)
                            }
                            MButton {
                                implicitWidth: 64
                                height: 34
                                text: "Add"
                                // No explicit eqAddModel refresh here: the
                                // Connections block above already refreshes
                                // on statsChanged, and a second refresh
                                // mid-click can destroy this delegate while
                                // the handler is still running.
                                onClicked: sheetBridge.addEquipmentItem(modelData.name, eqQty.value)
                            }
                        }
                    }
                }
            }

            // nothing in the list fits? add what was typed as a custom item
            MButton {
                objectName: "addCustomItemButton"
                visible: eqSearch.text.trim().length > 0
                Layout.fillWidth: true
                primary: false
                wrapText: true
                text: "+ Add \u201c" + eqSearch.text.trim() + "\u201d as a custom item"
                onClicked: {
                    sheetBridge.addCustomEquipmentItem(eqSearch.text.trim(), eqQty.value)
                    eqSearch.text = ""
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
                // Everyday: View and the Equipped box. Press and hold for the
                // rest -- attune, study (manuals/tomes), remove.
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: miCol.height + 16
                    radius: 8
                    color: miHold.pressed ? Theme.surf3 : Theme.surf2
                    // border = rarity (dark grey common ... amber legendary, crimson artifact)
                    border.color: Theme.rarityColor(modelData.rarity)
                    border.width: 2

                    MouseArea {
                        id: miHold
                        objectName: "magicItemHold_" + modelData.name
                        anchors.fill: parent
                        pressAndHoldInterval: 450
                        onPressAndHold: root.openMagicItemOptions(modelData)
                    }

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
                                // plain text -- the card's border carries the colour
                                text: modelData.rarity
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                            }
                            // magic ammunition stacks: how many -- tap to change
                            MButton {
                                objectName: "miQtyButton_" + modelData.name
                                visible: modelData.isAmmo
                                primary: false
                                implicitWidth: Math.max(40, implicitContentWidth + 20)
                                implicitHeight: 34
                                text: "×" + modelData.qty
                                Accessible.name: "Quantity " + modelData.qty
                                onClicked: root.openAmountDialog(modelData)
                            }
                            MButton {
                                primary: false
                                implicitWidth: 40
                                implicitHeight: 34
                                iconName: "search"   // View -- a magnifying glass
                                iconSize: 22
                                Accessible.name: "View"
                                onClicked: root.showItemDetail(modelData.name)
                            }
                        }
                        Label {
                            width: parent.width
                            text: modelData.type
                                  + (modelData.studied ? "  ·  Studied (its magic is spent)" : "")
                                  + (modelData.attuned ? "  ·  Attuned"
                                     : (modelData.needsAttunement ? "  ·  Requires attunement" : ""))
                            color: modelData.attuned ? Theme.indigo2 : Theme.text3
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
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
                        MCheckBox {
                            text: "Equipped"
                            checked: modelData.equipped
                            onToggled: sheetBridge.setMagicItemEquipped(modelData.uid, checked)
                        }
                    }
                }
            }
            Label {
                visible: sheetBridge.magicItems.length > 0
                text: "Press and hold an item to attune, study or remove it."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            }

            // ── Add a Magic Item ─────────────────────────────────────
            MCard {
            id: addMiAnchor
            title: "Add a Magic Item"
            iconName: "magic"
            // search box across the row; slot / rarity / attunement in the
            // filter drawer behind the funnel button
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MTextField {
                    id: miSearch
                    objectName: "miSearchField"
                    Layout.fillWidth: true
                    placeholderText: "Search magic items…"
                    onTextChanged: miAddModel.refreshResults()
                }
                MFilterButton {
                    objectName: "miFilterButton"
                    count: miFilters.activeCount
                    onClicked: miFilters.open()
                }
            }
            MFilterDrawer {
                id: miFilters
                objectName: "miFilterDrawer"
                title: "Magic item filters"
                activeCount: (miSlotFilter.currentIndex > 0) + (miRarityFilter.currentIndex > 0)
                             + (miAttuneFilter.currentIndex > 0)
                onCleared: {
                    miSlotFilter.currentIndex = 0
                    miRarityFilter.currentIndex = 0
                    miAttuneFilter.currentIndex = 0
                }
                Label { text: "Slot"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: miSlotFilter
                    Layout.fillWidth: true
                    model: sheetBridge.magicItemSlots
                    onCurrentIndexChanged: miAddModel.refreshResults()
                }
                Label { text: "Rarity"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: miRarityFilter
                    Layout.fillWidth: true
                    model: sheetBridge.magicItemRarities
                    onCurrentIndexChanged: miAddModel.refreshResults()
                }
                Label { text: "Attunement"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: miAttuneFilter
                    Layout.fillWidth: true
                    model: sheetBridge.magicItemAttunementOptions
                    onCurrentIndexChanged: miAddModel.refreshResults()
                }
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
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 52
                        color: "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 8
                            // rarity as a coloured bar, not coloured text
                            // (coloured text is hard to read)
                            Rectangle {
                                Layout.preferredWidth: 6
                                Layout.fillHeight: true
                                Layout.topMargin: 4
                                Layout.bottomMargin: 4
                                radius: 2
                                color: Theme.rarityColor(modelData.rarity)
                            }
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
                                    text: modelData.rarity
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
                                onClicked: root.showItemDetail(modelData.name)
                            }
                            MButton {
                                implicitWidth: 64
                                height: 34
                                text: "Add"
                                // See the equipment browser's Add above -- the
                                // Connections-driven refresh on statsChanged
                                // already updates miAddModel.
                                onClicked: root.pickMagicItem(modelData.name)
                            }
                        }
                    }
                }
            }
            }
        }
    }

    // ── Item detail popup ────────────────────────────────────────────
    // Read through Window.window.pendingItemDetail for the same reason
    // the spell detail popup is -- see SheetSpellsScreen.qml.
    property var itemData: Window.window.pendingItemDetail

    MFullPageDialog {
        id: itemDetail
        dialogTitle: (root.itemData && root.itemData.name) || "Item"
        accent: (root.itemData && root.itemData.rarity) ? Theme.rarityColor(root.itemData.rarity) : "transparent"

        Flickable {
            anchors.fill: parent
            anchors.margins: 16
            contentWidth: width
            contentHeight: itemDetailCol.height
            clip: true

            ColumnLayout {
                id: itemDetailCol
                width: parent.width
                spacing: 8

                Label {
                    visible: !!root.itemData.subtitle
                    text: root.itemData.rarity && root.itemData.subtitle === "Magic item"
                          ? root.itemData.rarity + " magic item" : (root.itemData.subtitle || "")
                    // plain gold -- the page's frame carries the rarity colour
                    color: Theme.gold2
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Label {
                    visible: text.length > 0
                    text: (root.itemData.facts || []).join("\n")
                    color: Theme.text2
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Rectangle {
                    visible: !!root.itemData.desc
                    Layout.fillWidth: true
                    height: 1
                    color: Theme.border
                }
                Label {
                    text: root.itemData.desc || ""
                    color: Theme.text
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
