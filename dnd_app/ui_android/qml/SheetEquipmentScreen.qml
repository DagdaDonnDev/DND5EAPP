import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Inventory"
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

    // ── Loadout slots ────────────────────────────────────────────────
    // One slot: its label (a tattoo's place), the item and what it does.
    // Purple and a ◆ when attuned, teal when worn, dashed when empty.
    component SlotTile: Rectangle {
        id: tile
        property var slot
        readonly property bool empty: !slot.name
        readonly property color tone: slot.state === "att" ? Theme.purple2
                                      : (empty ? Theme.border : (slot.key === "tattoo" ? Theme.amber : Theme.teal))
        objectName: "slot_" + slot.key + (slot.name ? "_" + slot.name : "")
        Layout.fillWidth: true
        Layout.preferredWidth: 1
        Layout.columnSpan: slot.key === "both" ? 2 : 1
        implicitHeight: 58
        radius: 9
        color: tileTap.pressed ? Theme.surf3 : (slot.state === "att" ? Qt.rgba(Theme.purple2.r, Theme.purple2.g, Theme.purple2.b, 0.10) : Theme.surf2)
        border.color: tone
        border.width: empty ? 1 : 1.5
        opacity: empty ? 0.75 : 1
        // tap: what could go here; press and hold: take it off
        MouseArea {
            id: tileTap
            objectName: "slotTap_" + tile.slot.key + (tile.slot.name ? "_" + tile.slot.name : "")
            anchors.fill: parent
            pressAndHoldInterval: 450
            onClicked: root.openSlotOptions(tile.slot)
            onPressAndHold: if (tile.slot.name) sheetBridge.takeOffLoadoutSlot(tile.slot.key, tile.slot.uid)
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 0
            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: (tile.slot.key === "tattoo" && tile.slot.where ? tile.slot.where : tile.slot.label).toUpperCase()
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall - 2
                    font.bold: true
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
                Label { visible: tile.slot.attuned; text: "◆"; color: Theme.purple2; font.pixelSize: Theme.fsSmall - 2 }
                // a versatile weapon: in one hand or two
                Rectangle {
                    objectName: "gripToggle"
                    visible: !!tile.slot.versatile
                    width: gripText.implicitWidth + 12
                    height: 20
                    radius: 5
                    color: Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.18)
                    border.color: Theme.teal
                    Label { id: gripText; anchors.centerIn: parent; text: tile.slot.grip || "1H"; color: Theme.teal2; font.pixelSize: Theme.fsSmall - 2; font.bold: true }
                    MouseArea { anchors.fill: parent; onClicked: sheetBridge.setTwoHandedGrip(tile.slot.grip !== "2H") }
                }
            }
            Label {
                text: tile.slot.name || "Empty"
                color: tile.empty ? Theme.text3 : (tile.slot.state === "att" ? Theme.purple2 : Theme.text)
                font.pixelSize: Theme.fsSmall
                font.bold: !tile.empty
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Label {
                visible: tile.slot.what.length > 0
                text: tile.slot.what
                color: Theme.text2
                font.pixelSize: Theme.fsSmall - 2
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }
    }

    property var heldSlot: null
    property var pendingPutOn: null        // {uid, name, ask, uids}
    function magicEntry(uid) {
        var all = sheetBridge.magicItems
        for (var i = 0; i < all.length; i++)
            if (all[i].uid === uid) return all[i]
        return null
    }
    property var slotChoices: []
    function openSlotOptions(slot) {
        heldSlot = slot
        var opts = []
        slotChoices = slot.key === "tattoo" ? [] : sheetBridge.loadoutSlotOptions(slot.key)
        for (var i = 0; i < slotChoices.length; i++)
            opts.push({key: "eq:" + i, text: (slot.name ? "Swap for " : "Put on ") + slotChoices[i].name,
                       icon: (slot.key === "main" || slot.key === "off" || slot.key === "both") ? "combat" : "shield"})
        if (slot.name) {
            opts.push({key: "details", text: "Details", icon: "search"})
            if (slot.uid && slot.needs)
                opts.push({key: "attune", text: slot.attuned ? "End attunement" : "Attune", icon: "magic"})
            var entry = slot.uid ? magicEntry(slot.uid) : null
            if (entry && entry.resistanceChoicePool.length > 0)
                opts.push({key: "dmgtype", icon: "shield",
                           text: "Damage type" + (entry.resistanceChoiceCurrent ? " (now " + entry.resistanceChoiceCurrent.toLowerCase() + ")" : "")})
            if (slot.key === "tattoo")
                opts.push({key: "move", text: "Move it" + (slot.where ? " (now " + slot.where.toLowerCase() + ")" : ""), icon: "pencil"})
            if (slot.swap)
                opts.push({key: "swap", text: "Swap hands", icon: "combat"})
        }
        if (opts.length === 0) {
            sheetBridge.notify("Nothing you carry goes here.")
            return
        }
        slotOptions.heading = slot.name || slot.label
        slotOptions.message = slot.name ? "Press and hold a slot to take it off." : ""
        slotOptions.options = opts
        slotOptions.open()
    }
    // Both hands full and a weapon that could go in either: which it replaces
    property var pendingHand: null          // {name, another, uid}
    function equipWeapon(name, another) {
        var opts = sheetBridge.weaponHandChoice(name, another)
        if (opts.length === 0) {
            if (another) sheetBridge.holdAnotherWeapon(name)
            else sheetBridge.toggleWeaponEquipped(name, true)
            return
        }
        pendingHand = {name: name, another: another, uid: ""}
        askHand(name, opts)
    }
    function askHand(name, opts) {
        handDialog.heading = "Your hands are full"
        handDialog.message = name + " replaces:"
        handDialog.options = [{key: "main", text: opts[0], icon: "combat"}, {key: "off", text: opts[1], icon: "combat"}]
        handDialog.open()
    }
    MOptionsDialog {
        id: handDialog
        objectName: "handDialog"
        onPicked: (key) => {
            var p = root.pendingHand
            if (!p) return
            if (p.uid) sheetBridge.putOnMagicItemInHand(p.uid, key)
            else sheetBridge.equipWeaponInHand(p.name, key, p.another)
        }
    }

    function putOn(uid, name) {
        var r = sheetBridge.putOnMagicItem(uid)
        if (!r || !r.ask) return
        if (r.ask === "hand") {
            pendingHand = {name: name, another: false, uid: uid}
            askHand(name, r.options)
            return
        }
        pendingPutOn = {uid: uid, name: name, ask: r.ask, uids: r.uids || []}
        putOnPicker.dialogTitle = r.ask === "where" ? "Where is your " + name + "?" : "Take off which, to put on " + name + "?"
        putOnPicker.options = r.options
        putOnPicker.open()
    }

    MOptionsDialog {
        id: slotOptions
        objectName: "slotOptionsDialog"
        onPicked: (key) => {
            var s = root.heldSlot
            if (!s) return
            if (key.indexOf("eq:") === 0) {
                var o = root.slotChoices[parseInt(key.slice(3))]
                if (o) sheetBridge.equipLoadoutSlot(s.key, o.name, o.uid)
            }
            else if (key === "details") root.showItemDetail(s.name)
            else if (key === "attune") sheetBridge.setMagicItemAttuned(s.uid, !s.attuned)
            else if (key === "dmgtype") {
                var e = root.magicEntry(s.uid)
                dmgTypePicker.itemName = s.name
                dmgTypePicker.options = e ? e.resistanceChoicePool : []
                dmgTypePicker.open()
            }
            else if (key === "move") { tattooPlacePicker.options = sheetBridge.loadout.places; tattooPlacePicker.open() }
            else if (key === "swap") sheetBridge.swapHands()
            else if (key === "remove") sheetBridge.removeMagicItem(s.uid)
            else if (key === "off") {
                if (s.uid) sheetBridge.takeOffMagicItem(s.uid)
                else if (s.key === "armor") sheetBridge.toggleArmorWorn(s.name, false)
                else if (s.shield) sheetBridge.toggleShieldWorn(false)
                else sheetBridge.putAwayOneWeapon(s.name)
            }
        }
    }
    MPickerDialog {
        id: putOnPicker
        objectName: "putOnPicker"
        onPicked: (value) => {
            var p = root.pendingPutOn
            if (!p) return
            if (p.ask === "where") {
                var r = sheetBridge.setTattooPlace(p.uid, value)
                if (r && r.ask) root.putOn(p.uid, p.name)
            } else {
                var i = options.indexOf(value)
                if (i >= 0) sheetBridge.putOnMagicItemSwapping(p.uid, p.uids[i])
            }
        }
    }
    MPickerDialog {
        id: tattooPlacePicker
        objectName: "tattooPlacePicker"
        dialogTitle: "Where is it?"
        onPicked: (value) => { if (root.heldSlot) sheetBridge.setTattooPlace(root.heldSlot.uid, value) }
    }
    MPickerDialog {
        id: dmgTypePicker
        property string itemName: ""
        dialogTitle: "Which damage type?"
        onPicked: (value) => sheetBridge.setMagicItemDamageType(itemName, value)
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
        // the whole stack, held ones included (a row may be only the spares)
        amountQty.value = Math.max(1, item.total || item.qty || 1)
        amountDialog.open()
    }

    // A weapon a monk could use with Dedicated Weapon: press and hold ->
    //   How many / Make dedicated weapon (or Stop using as dedicated weapon)
    // Anything else goes straight to how many you have.
    function openInventoryHold(item) {
        if (!item.canDedicate && !item.dedicated && !item.canSwapHands) {
            openAmountDialog(item)
            return
        }
        heldItem = item
        weaponOptionsDialog.heading = item.name
        var opts = [{key: "amount", text: "How many", icon: "package"}]
        // holding two weapons: which is in your main hand, which in your off hand
        if (item.canSwapHands)
            opts.push({key: "swap", text: "Swap hands", icon: "combat"})
        if (item.canDedicate || item.dedicated)
            opts.push(item.dedicated
                      ? {key: "undedicate", text: "Stop using as dedicated weapon", icon: "dagger"}
                      : {key: "dedicate", text: "Make dedicated weapon", icon: "dagger"})
        weaponOptionsDialog.options = opts
        weaponOptionsDialog.open()
    }

    MOptionsDialog {
        id: weaponOptionsDialog
        objectName: "weaponOptionsDialog"
        onPicked: (key) => {
            var it = root.heldItem
            if (!it) return
            if (key === "amount") root.openAmountDialog(it)
            else if (key === "swap") sheetBridge.swapHands()
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
        if (item.canSwapHands)
            opts.push({key: "swap", text: "Swap hands (now in your " + item.hand + ")", icon: "combat"})
        if (item.baseOptions && item.baseOptions.length > 0)
            opts.push({key: "base", icon: item.baseKind === "armor" ? "shield" : "combat",
                       text: "Which " + item.baseKind + " is it?" + (item.base ? " (now " + item.base.toLowerCase() + ")" : "")})
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
            else if (key === "swap") sheetBridge.swapHands()
            else if (key === "base") {
                weaponBasePicker.dialogTitle = "Which " + it.baseKind + " is your " + it.name + "?"
                weaponBasePicker.options = it.baseOptions
                weaponBasePicker.open()
            }
        }
    }

    // an "any sword" item: which weapon it is (its dice follow on Combat);
    // searchable, since "any weapon" is a long list
    MPickerDialog {
        id: weaponBasePicker
        objectName: "weaponBasePicker"
        onPicked: (value) => { if (root.heldItem) sheetBridge.setWeaponBase(root.heldItem.name, value) }
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
        Overlay.modal: Rectangle { color: Theme.scrim }

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
                      + (root.heldItem && root.heldItem.heldCount > 0
                         ? " (" + (root.heldItem.heldCount === 1 ? "one is" : "two are") + " in your hands)" : "")
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
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
        if (name === "Loadout") anchorItem = loadoutAnchor
        else if (name === "Inventory") anchorItem = invAnchor
        else if (name === "Add Equipment") anchorItem = addEqAnchor
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

            // ── Loadout: what you hold and wear (core/loadout.py) ─────────
            // In hand, then the worn slots two to a row, then tattoos. Tap a
            // slot for what can be done with it; an empty one offers what you
            // carry that goes there.
            MCard {
                id: loadoutAnchor
                objectName: "loadoutCard"
                title: "Loadout"
                iconName: "shield"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Label {
                        text: "AC " + sheetBridge.loadout.ac + (sheetBridge.loadout.saves ? "  ·  " + sheetBridge.loadout.saves : "")
                        color: Theme.indigo2
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "ATTUNED " + sheetBridge.loadout.attuned + " / " + sheetBridge.loadout.limit
                        color: Theme.purple2
                        font.pixelSize: Theme.fsSmall - 1
                        font.bold: true
                    }
                    Repeater {
                        model: sheetBridge.loadout.limit
                        delegate: Rectangle {
                            width: 10; height: 10; radius: 5
                            border.width: 2
                            border.color: Theme.purple2
                            color: index < sheetBridge.loadout.attuned ? Theme.purple2 : "transparent"
                        }
                    }
                }

                Label { text: "IN HAND"; color: Theme.gold; font.pixelSize: Theme.fsSmall - 1; font.bold: true; font.letterSpacing: 1 }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Repeater {
                        model: sheetBridge.loadout.in_hand
                        delegate: SlotTile { slot: modelData }
                    }
                }
                Label { text: "WORN"; color: Theme.gold; font.pixelSize: Theme.fsSmall - 1; font.bold: true; font.letterSpacing: 1; Layout.topMargin: 4 }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Repeater {
                        model: sheetBridge.loadout.worn
                        delegate: SlotTile { slot: modelData }
                    }
                }
                Label {
                    visible: sheetBridge.loadout.other.length > 0
                    text: "ALSO IN USE"; color: Theme.gold; font.pixelSize: Theme.fsSmall - 1; font.bold: true; font.letterSpacing: 1; Layout.topMargin: 4
                }
                GridLayout {
                    visible: sheetBridge.loadout.other.length > 0
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Repeater {
                        model: sheetBridge.loadout.other
                        delegate: SlotTile { slot: modelData }
                    }
                }
                // flasks and explosives you carry: tap the ones on your
                // belt, and the Combat screen lists them under Ready to throw
                RowLayout {
                    visible: sheetBridge.carriedThrowables.length > 0
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    Label {
                        text: "READY TO THROW"; color: Theme.gold; font.pixelSize: Theme.fsSmall - 1; font.bold: true; font.letterSpacing: 1
                        Layout.fillWidth: true
                    }
                    Label {
                        text: sheetBridge.carriedThrowables.filter(function(t) { return t.ready }).length + " ready"
                        color: Theme.amber2; font.pixelSize: Theme.fsSmall - 1; font.bold: true
                    }
                }
                GridLayout {
                    visible: sheetBridge.carriedThrowables.length > 0
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Repeater {
                        model: sheetBridge.carriedThrowables
                        delegate: Rectangle {
                            objectName: "throwChip_" + modelData.name
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            implicitHeight: 44
                            radius: 9
                            color: modelData.ready ? Qt.rgba(Theme.amber.r, Theme.amber.g, Theme.amber.b, 0.11) : Theme.surf
                            border.color: modelData.ready ? Qt.rgba(Theme.amber.r, Theme.amber.g, Theme.amber.b, 0.67) : Theme.border2
                            Accessible.role: Accessible.CheckBox
                            Accessible.name: modelData.label + (modelData.ready ? ", ready to throw" : ", not ready")
                            Accessible.checked: modelData.ready
                            Label {
                                anchors { fill: parent; leftMargin: 10; rightMargin: 6 }
                                verticalAlignment: Text.AlignVCenter
                                text: (modelData.ready ? "✓  " : "") + modelData.label + "  ×" + modelData.qty
                                color: modelData.ready ? Theme.amber2 : Theme.text2
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                elide: Text.ElideRight
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: sheetBridge.setReadyThrow(modelData.name, !modelData.ready)
                            }
                        }
                    }
                }
                Label {
                    visible: sheetBridge.loadout.tattoos.length > 0
                    text: "TATTOOS (" + sheetBridge.loadout.tattoos.length + ")"
                    color: Theme.gold; font.pixelSize: Theme.fsSmall - 1; font.bold: true; font.letterSpacing: 1; Layout.topMargin: 4
                }
                GridLayout {
                    visible: sheetBridge.loadout.tattoos.length > 0
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Repeater {
                        model: sheetBridge.loadout.tattoos
                        delegate: SlotTile { slot: modelData }
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
                title: "Money & Carrying"
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
                // what you carry against what you can
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Carrying"; color: Theme.text3; font.pixelSize: Theme.fsSmall; Layout.fillWidth: true }
                    Label {
                        objectName: "carryText"
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

            // ── Inventory ───────────────────────────────────────────────
            // Grouped Weapons / Armor / Consumables / Tools & Gear, equipped
            // items first. Weapons are equipped and armor worn straight from
            // their row (this replaces the separate Weapons checklist).
            MCard {
                id: invAnchor
                title: "Inventory"
                iconName: "gear"

                Label {
                    visible: sheetBridge.inventoryGroups.length === 0 && sheetBridge.carriedMagicItems.length === 0
                    text: "Nothing here yet -- add some below. What you hold and wear is on the Loadout."
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
                                text: modelData.count
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                        }

                        Repeater {
                            model: modelData.items
                            delegate: Rectangle {
                                // a weapon in hand has a row for each hand, the rest one of their own
                                objectName: "invRow_" + (modelData.rowKey || modelData.name)
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
                                    objectName: "invHold_" + (modelData.rowKey || modelData.name)
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
                                            // what it is -- cut short first on a narrow row
                                            // in hand: which hand ("Off hand"), or Equipped
                                            text: [modelData.hand ? modelData.hand.charAt(0).toUpperCase() + modelData.hand.slice(1)
                                                   : (modelData.equipped ? "Equipped" : ""), modelData.detail]
                                                  .filter(function(x) { return x.length > 0 }).join("  ·  ")
                                            visible: text.length > 0
                                            color: Theme.text3
                                            font.pixelSize: Theme.fsSmall
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                        Label {
                                            // what the stack weighs and is worth: its own
                                            // line, never cut short ("3 lb  ·  15 gp")
                                            objectName: "invWeightValue_" + modelData.name
                                            text: modelData.weightValue
                                            visible: text.length > 0
                                            color: Theme.text3
                                            font.pixelSize: Theme.fsSmall
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                    // row buttons, right to left: View (magnifier) ·
                                    // the stack's count (×N, opens the amount dialog) ·
                                    // Equip/Wear. Using an item -- a potion, a scroll,
                                    // a tinderbox -- is its card on the Actions screen.
                                    MButton {
                                        objectName: "equipButton_" + (modelData.rowKey || modelData.name)
                                        // the rest of a stack with one in hand: Equip
                                        // only when a second can go in the other hand
                                        visible: modelData.equipKind !== ""
                                                 && !(modelData.heldCount > 0 && !modelData.equipped && !modelData.canHoldAnother)
                                        primary: false
                                        implicitWidth: 86
                                        implicitHeight: 34
                                        text: modelData.equipKind === "weapon" ? (modelData.equipped ? "Unequip" : "Equip")
                                              : (modelData.equipped ? "Take off" : (modelData.equipKind === "shield" ? "Equip" : "Wear"))
                                        onClicked: {
                                            if (modelData.equipKind === "weapon" && modelData.heldRow)
                                                sheetBridge.putAwayOneWeapon(modelData.name)
                                            else if (modelData.equipKind === "weapon" && modelData.heldCount > 0)
                                                root.equipWeapon(modelData.name, true)
                                            else if (modelData.equipKind === "weapon" && !modelData.equipped)
                                                root.equipWeapon(modelData.name, false)
                                            else if (modelData.equipKind === "weapon")
                                                sheetBridge.toggleWeaponEquipped(modelData.name, false)
                                            else if (modelData.equipKind === "shield")
                                                sheetBridge.toggleShieldWorn(!modelData.equipped)
                                            else
                                                sheetBridge.toggleArmorWorn(modelData.name, !modelData.equipped)
                                        }
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

                // magic items you carry but aren't using: tap Put on (press
                // and hold to attune, study or remove)
                ColumnLayout {
                    visible: sheetBridge.carriedMagicItems.length > 0
                    Layout.fillWidth: true
                    spacing: 6
                    RowLayout {
                        spacing: 6
                        Label { text: "Magic Items"; color: Theme.text3; font.pixelSize: Theme.fsSmall; font.bold: true }
                        Label { text: sheetBridge.carriedMagicItems.length; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                    }
                    Repeater {
                        objectName: "carriedMagicRepeater"
                        model: sheetBridge.carriedMagicItems
                        delegate: Rectangle {
                            objectName: "carriedMagic_" + modelData.name
                            Layout.fillWidth: true
                            implicitHeight: cmRow.implicitHeight + 14
                            radius: 8
                            color: cmHold.pressed ? Theme.surf3 : Theme.surf2
                            border.color: Theme.rarityColor(modelData.rarity)
                            border.width: 2
                            MouseArea {
                                id: cmHold
                                anchors.fill: parent
                                pressAndHoldInterval: 450
                                onPressAndHold: root.openMagicItemOptions(modelData)
                            }
                            RowLayout {
                                id: cmRow
                                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 8 }
                                spacing: 8
                                MIcon { name: "magic"; size: 20; color: Theme.indigo2 }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 1
                                    Label {
                                        text: (modelData.isAmmo ? modelData.qty + "× " : "") + modelData.name
                                        color: Theme.text; font.pixelSize: Theme.fsBody
                                        elide: Text.ElideRight; Layout.fillWidth: true
                                    }
                                    Label {
                                        text: modelData.rarity + (modelData.attuned ? "  ·  Attuned" : (modelData.needsAttunement ? "  ·  Needs attuning" : ""))
                                        color: modelData.attuned ? Theme.purple2 : Theme.text3
                                        font.pixelSize: Theme.fsSmall
                                        elide: Text.ElideRight; Layout.fillWidth: true
                                    }
                                }
                                MButton {
                                    objectName: "putOn_" + modelData.name
                                    visible: modelData.type !== "Potion" && modelData.type !== "Scroll"
                                             && (modelData.slot !== "" || modelData.needsAttunement
                                                 || modelData.type === "Weapon" || modelData.type === "Armor")
                                    primary: false
                                    implicitWidth: 86
                                    implicitHeight: 34
                                    text: modelData.type === "Weapon" ? "Equip" : "Put on"
                                    onClicked: root.putOn(modelData.uid, modelData.name)
                                }
                                MButton {
                                    primary: false
                                    implicitWidth: 40
                                    implicitHeight: 34
                                    iconName: "search"
                                    iconSize: 22
                                    Accessible.name: "View"
                                    onClicked: root.showItemDetail(modelData.name)
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
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Label {
                                        // what it is -- cut short first
                                        text: modelData.category + (modelData.detail ? "  ·  " + modelData.detail : "")
                                        color: Theme.text3
                                        font.pixelSize: Theme.fsSmall
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                    Label {
                                        // what one weighs and costs, in full
                                        text: modelData.weightValue || ""
                                        visible: text.length > 0
                                        color: Theme.text3
                                        font.pixelSize: Theme.fsSmall
                                    }
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
