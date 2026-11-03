import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// The Combat screen: everything needed mid-fight, blocked into cards --
// stats, hit points (with concentration and quick damage/heal), the turn
// tracker (tap a chip to mark it spent/free), attacks with Attack/Damage
// roll buttons, castable spells (Cast buttons, same list as the Actions
// screen), hit dice, Wild Shape, and conditions.
Page {
    id: root
    readonly property string screenTitle: "Combat"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    // The spells starred (favourited) on the Spells screen, grouped by
    // casting time -- only those, so combat shows the player's own picks
    // rather than every castable spell. By level, then name.
    readonly property var combatSpellGroups: {
        if (!sheetBridge)
            return []
        var out = []
        var groups = sheetBridge.actionAbilities
        for (var i = 0; i < groups.length; ++i) {
            if (groups[i].bucketKey === "Passive")
                continue
            var items = groups[i].items.filter(function(it) { return it.isSpell && it.pinned })
            items.sort(function(a, b) {
                return (a.spellLevel - b.spellLevel) || a.spellName.localeCompare(b.spellName)
            })
            if (items.length > 0)
                out.push({ bucket: groups[i].bucket, bucketKey: groups[i].bucketKey, items: items })
        }
        return out
    }
    // the ammunition the count dialog is editing
    property string ammoEditKind: ""
    property string ammoEditLabel: ""

    readonly property real hpFraction: sheetBridge && sheetBridge.maxHp > 0
                                       ? Math.max(0, Math.min(1, sheetBridge.currentHp / sheetBridge.maxHp)) : 0

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: width
        contentHeight: content.height
        clip: true

        ColumnLayout {
            id: content
            width: parent.width
            spacing: 14

            SheetHeader {}

            // ── Stat strip ──────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Repeater {
                    model: [
                        { label: "AC", value: String(sheetBridge.armorClass) },
                        { label: "Initiative", value: sheetBridge.initiativeText, rollBonus: sheetBridge.initiative },
                        { label: "Speed", value: String(sheetBridge.speed) },
                        { label: "Prof", value: "+" + sheetBridge.proficiencyBonus },
                        { label: "Passive", value: String(sheetBridge.passivePerception) },
                    ]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 64
                        radius: 10
                        color: Theme.surf
                        border.color: modelData.rollBonus !== undefined ? Theme.border2 : Theme.border
                        Column {
                            anchors.centerIn: parent
                            width: parent.width - 6
                            spacing: 2
                            Label {
                                text: modelData.value
                                color: Theme.teal2
                                font.pixelSize: Theme.fsHead
                                font.bold: true
                                width: parent.width
                                horizontalAlignment: Text.AlignHCenter
                            }
                            Label {
                                text: modelData.label
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                width: parent.width
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                        }
                        // Initiative is tap-to-roll, same as desktop's
                        // clickable initiative stat.
                        MIcon {
                            visible: modelData.rollBonus !== undefined
                            name: "dice"
                            size: 13
                            anchors { right: parent.right; top: parent.top; margins: 5 }
                        }
                        MouseArea {
                            anchors.fill: parent
                            enabled: modelData.rollBonus !== undefined
                            onClicked: sheetBridge.rollQuickCheck("Initiative", modelData.rollBonus)
                        }
                    }
                }
            }

            // ── Hit points ──────────────────────────────────────────────
            MCard {
                title: "Hit Points"
                iconName: "heart"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Label {
                        text: sheetBridge.currentHp + " / " + sheetBridge.maxHp
                        color: sheetBridge.currentHp > 0 ? Theme.text : Theme.crimson2
                        font.pixelSize: Theme.fsTitle
                        font.bold: true
                    }
                    Rectangle {
                        visible: sheetBridge.tempHp > 0
                        radius: 6
                        color: Qt.rgba(Theme.indigo.r, Theme.indigo.g, Theme.indigo.b, 0.18)
                        border.color: Theme.indigo2
                        implicitWidth: tempLbl.implicitWidth + 14
                        implicitHeight: tempLbl.implicitHeight + 6
                        Label {
                            id: tempLbl
                            anchors.centerIn: parent
                            text: "+" + sheetBridge.tempHp + " temp"
                            color: Theme.indigo2
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                        }
                    }
                    Item { Layout.fillWidth: true }
                }

                // HP bar: green while healthy, amber when bloodied, red near 0
                Rectangle {
                    Layout.fillWidth: true
                    height: 8
                    radius: 4
                    color: Theme.surf3
                    Rectangle {
                        width: parent.width * root.hpFraction
                        height: parent.height
                        radius: 4
                        color: root.hpFraction > 0.5 ? Theme.green2 : (root.hpFraction > 0.25 ? Theme.amber : Theme.crimson)
                    }
                }

                // Concentration: what's being held, and a way to drop it
                Rectangle {
                    visible: sheetBridge.isConcentrating
                    Layout.fillWidth: true
                    radius: 8
                    color: Qt.rgba(Theme.amber.r, Theme.amber.g, Theme.amber.b, 0.12)
                    border.color: Theme.amber
                    implicitHeight: concRow.implicitHeight + 12
                    RowLayout {
                        id: concRow
                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 8 }
                        spacing: 8
                        MIcon { name: "spells"; size: 16; color: Theme.amber2 }
                        Label {
                            text: "Concentrating: " + sheetBridge.concentratingSpell
                            color: Theme.amber2
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        // took damage while concentrating: roll to keep it
                        MButton {
                            visible: sheetBridge.concentrationSaveDc > 0
                            implicitHeight: 36
                            text: "Save DC " + sheetBridge.concentrationSaveDc
                            onClicked: sheetBridge.rollPendingConcentrationSave()
                        }
                        MButton {
                            primary: false
                            implicitHeight: 36
                            text: "Drop"
                            onClicked: sheetBridge.dropConcentration()
                        }
                    }
                }

                // One row on wider phones; on narrow ones the amount gets its
                // own line so Damage / Heal / Temp keep room for their text.
                GridLayout {
                    id: hpGrid
                    Layout.fillWidth: true
                    columns: width >= 400 ? 4 : 3
                    columnSpacing: 8
                    rowSpacing: 8
                    MSpinBox {
                        id: hpAmount
                        Layout.preferredWidth: 100
                        Layout.columnSpan: hpGrid.columns === 4 ? 1 : 3
                        from: 0
                        to: 999
                        value: 1
                    }
                    MButton {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        primary: false
                        text: "Damage"
                        onClicked: sheetBridge.applyDamage(hpAmount.value)
                    }
                    MButton {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        text: "Heal"
                        onClicked: sheetBridge.applyHealing(hpAmount.value)
                    }
                    MButton {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        primary: false
                        text: "Temp"
                        onClicked: sheetBridge.setTempHp(hpAmount.value)
                    }
                }

                // Manual Max HP override (desktop's editable Max HP), tucked
                // behind a toggle so the everyday controls stay uncluttered.
                // Not available while Wild Shaped.
                Label {
                    visible: sheetBridge.canOverrideMaxHp
                    text: maxHpRow.visible ? "Hide max HP adjustment" : "Adjust max HP…"
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    font.underline: true
                    MouseArea { anchors.fill: parent; onClicked: maxHpRow.visible = !maxHpRow.visible }
                }
                Flow {
                    id: maxHpRow
                    visible: sheetBridge.hasMaxHpOverride
                    Layout.fillWidth: true
                    spacing: 10
                    Label {
                        text: "Max HP:"
                        color: Theme.text2
                        font.pixelSize: Theme.fsSmall
                        height: maxHpSpin.height
                        verticalAlignment: Text.AlignVCenter
                    }
                    MSpinBox {
                        id: maxHpSpin
                        width: 100
                        from: 1
                        to: 9999
                        value: sheetBridge.maxHp
                        onValueModified: sheetBridge.setMaxHpOverride(value)
                    }
                    MButton {
                        visible: sheetBridge.hasMaxHpOverride
                        primary: false
                        height: 36
                        text: "Reset to Auto"
                        onClicked: sheetBridge.resetMaxHpOverride()
                    }
                    Label {
                        visible: sheetBridge.hasMaxHpOverride
                        text: "(manual override)"
                        color: Theme.amber
                        font.pixelSize: Theme.fsSmall
                        height: maxHpSpin.height
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }

            // ── Death saves (only at 0 HP, directly under HP so it can't
            // be missed -- same as desktop) ─────────────────────────────
            MCard {
                visible: sheetBridge.showDeathSaves
                title: "Death Saves"
                iconName: "skull"
                accent: Theme.crimson2
                border.color: Theme.crimson

                Label {
                    text: sheetBridge.deathStatusText
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Row {
                    spacing: 24
                    Column {
                        spacing: 4
                        Label { text: "Successes"; color: Theme.teal2; font.pixelSize: Theme.fsSmall }
                        Row {
                            spacing: 6
                            Repeater {
                                model: 3
                                delegate: CheckBox {
                                    checked: sheetBridge.deathSaveSuccesses > index
                                    onToggled: sheetBridge.setDeathSaveSuccess(index, checked)
                                }
                            }
                        }
                    }
                    Column {
                        spacing: 4
                        Label { text: "Failures"; color: Theme.crimson2; font.pixelSize: Theme.fsSmall }
                        Row {
                            spacing: 6
                            Repeater {
                                model: 3
                                delegate: CheckBox {
                                    checked: sheetBridge.deathSaveFailures > index
                                    onToggled: sheetBridge.setDeathSaveFailure(index, checked)
                                }
                            }
                        }
                    }
                }
            }

            // ── Turn tracker ────────────────────────────────────────────
            // Tap a chip to mark it spent (or free again) -- same as
            // desktop's turn chips. Casting a spell and the Actions
            // screen's Use buttons also spend them.
            MCard {
                title: "This Turn"
                iconName: "short_rest"
                headerRight: MButton {
                    primary: false
                    implicitHeight: 36
                    iconName: "refresh"
                    iconSize: 16
                    text: "New Turn"
                    onClicked: sheetBridge.newTurn()
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: [
                            { key: "Action", label: "Action", icon: "combat",
                              used: sheetBridge.turnCounts.action, limit: sheetBridge.turnCounts.actionLimit,
                              blocked: (sheetBridge.turnCounts.blocked || {}).action || "" },
                            { key: "Bonus Action", label: "Bonus", icon: "bonus",
                              used: sheetBridge.turnCounts.bonusAction, limit: sheetBridge.turnCounts.bonusActionLimit,
                              blocked: (sheetBridge.turnCounts.blocked || {}).bonusAction || "" },
                            { key: "Reaction", label: "Reaction", icon: "bolt",
                              used: sheetBridge.turnCounts.reaction, limit: sheetBridge.turnCounts.reactionLimit,
                              blocked: (sheetBridge.turnCounts.blocked || {}).reaction || "" },
                        ]
                        delegate: Rectangle {
                            id: chip
                            objectName: "turnChip_" + modelData.key
                            // captured: the pip Repeater below has its own modelData
                            readonly property int usedCount: modelData.used
                            readonly property int limitCount: modelData.limit
                            readonly property bool spent: usedCount >= limitCount
                            // a condition (Stunned, Surprised, ...) has taken this part of the turn
                            readonly property bool blocked: modelData.blocked.length > 0
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            Layout.preferredHeight: 62
                            radius: 10
                            color: spent ? Theme.surf2 : Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.14)
                            border.color: blocked ? Theme.crimson2 : (spent ? Theme.border : Theme.teal2)
                            border.width: spent ? 1 : 2
                            opacity: spent ? 0.65 : 1.0
                            Column {
                                anchors.centerIn: parent
                                spacing: 4
                                Row {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    spacing: 6
                                    MIcon {
                                        name: modelData.icon
                                        size: 16
                                        color: spent ? Theme.text3 : Theme.teal2
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Label {
                                        text: modelData.label
                                        color: spent ? Theme.text3 : Theme.text
                                        font.pixelSize: Theme.fsSmall
                                        font.bold: true
                                    }
                                }
                                Label {
                                    visible: chip.blocked
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: "Blocked"
                                    color: Theme.crimson2
                                    font.pixelSize: Theme.fsSmall - 2
                                }
                                // one pip per use this turn: filled = still available
                                Row {
                                    visible: !chip.blocked
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    spacing: 5
                                    Repeater {
                                        model: chip.limitCount
                                        delegate: Rectangle {
                                            width: 9; height: 9; radius: 4.5
                                            color: index < chip.limitCount - chip.usedCount ? Theme.teal2 : "transparent"
                                            border.color: index < chip.limitCount - chip.usedCount ? Theme.teal2 : Theme.text3
                                        }
                                    }
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: sheetBridge.toggleTurnSlot(modelData.key)
                            }
                        }
                    }
                }
                Label {
                    objectName: "turnBlockedReason"
                    readonly property var blocks: sheetBridge.turnCounts.blocked || {}
                    visible: text.length > 0
                    text: blocks.action || blocks.bonusAction || blocks.reaction || ""
                    color: Theme.crimson2
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }

            // ── Attacks ─────────────────────────────────────────────────
            MCard {
                title: "Attacks"
                iconName: "combat"

                Label {
                    visible: sheetBridge.weapons.length === 0
                    text: "No weapons equipped -- equip one on the Equipment screen."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Repeater {
                    objectName: "weaponsRepeater"
                    model: sheetBridge.weapons
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: wCol.implicitHeight + 20
                        radius: 10
                        color: Theme.surf2
                        border.color: Theme.border

                        ColumnLayout {
                            id: wCol
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Label {
                                    text: modelData.name
                                    color: Theme.text
                                    font.pixelSize: Theme.fsBody
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                // what it is, for an attack that isn't a held
                                // weapon (Martial Arts, Natural, Hybrid Form...)
                                Label {
                                    visible: modelData.badge !== ""
                                    text: modelData.badge
                                    color: Theme.text2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                                // advantage / disadvantage die (green A / red D)
                                MIcon {
                                    visible: modelData.advantage !== modelData.disadvantage
                                    name: modelData.advantage ? "adv" : "disadv"
                                    color: modelData.advantage ? Theme.green2 : Theme.crimson2
                                    size: 22
                                }
                            }

                            // to-hit and damage, side by side
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 14
                                Column {
                                    Label {
                                        text: modelData.attackBonusText
                                        color: modelData.proficient ? Theme.teal2 : Theme.amber
                                        font.pixelSize: Theme.fsHead
                                        font.bold: true
                                    }
                                    Label { text: "to hit"; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                                }
                                Column {
                                    Layout.fillWidth: true
                                    Label {
                                        text: modelData.damageDisplay
                                        color: Theme.text
                                        font.pixelSize: Theme.fsHead
                                        font.bold: true
                                    }
                                    Label {
                                        text: modelData.damageType
                                        color: Theme.text3
                                        font.pixelSize: Theme.fsSmall
                                        wrapMode: Text.WordWrap
                                        width: parent.width
                                    }
                                }
                            }

                            // the extra damage its hits carry -- spells, features,
                            // items -- each with its damage type (core/riders.py);
                            // plain text, the player rolls it
                            Label {
                                objectName: "weaponRiders_" + modelData.name
                                visible: modelData.onHitBonusText !== ""
                                text: modelData.onHitBonusText
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            // holding two weapons: the off-hand bonus action attack's damage
                            Label {
                                visible: modelData.offhandText !== ""
                                text: modelData.offhandText
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            // what an attack that isn't a held weapon is (desktop shows it on hover)
                            Label {
                                visible: modelData.note !== ""
                                text: modelData.note
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            Flow {
                                Layout.fillWidth: true
                                spacing: 6
                                visible: modelData.magicBonus > 0 || modelData.material !== "" || !modelData.proficient
                                Label {
                                    visible: modelData.magicBonus > 0
                                    text: "+" + modelData.magicBonus + " magic"
                                    color: Theme.amber2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                                Label {
                                    visible: modelData.material !== ""
                                    text: modelData.material
                                    color: Theme.teal2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                                Label {
                                    visible: !modelData.proficient
                                    text: "not proficient"
                                    color: Theme.amber
                                    font.pixelSize: Theme.fsSmall
                                }
                            }

                            MCheckBox {
                                visible: modelData.canPowerAttack
                                text: "Power Attack (-5 to hit / +10 damage)"
                                checked: modelData.powerAttackActive
                                onToggled: sheetBridge.toggleWeaponPowerAttack(modelData.name)
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                // shots left in the inventory (bundles count every
                                // piece) -- tap to change how many; a shot uses one
                                MButton {
                                    objectName: "ammoButton_" + modelData.name
                                    visible: modelData.ammoKind !== ""
                                    primary: false
                                    iconName: "ammo"
                                    iconSize: 14
                                    text: modelData.ammoLabel + ": " + modelData.ammoCount
                                    onClicked: {
                                        root.ammoEditKind = modelData.ammoKind
                                        root.ammoEditLabel = modelData.ammoLabel
                                        ammoQty.value = modelData.ammoCount
                                        ammoDialog.open()
                                    }
                                }
                                MButton {
                                    objectName: "attackButton_" + modelData.name
                                    visible: modelData.attackBonusText !== ""
                                    Layout.fillWidth: true
                                    iconName: "dice"
                                    iconSize: 16
                                    text: "Roll to Hit"
                                    onClicked: sheetBridge.rollWeaponAttack(modelData.name)
                                }
                            }
                        }
                    }
                }
            }

            // ── Spells ──────────────────────────────────────────────────
            MCard {
                visible: sheetBridge.knownSpells.length > 0 || root.combatSpellGroups.length > 0
                title: "Spells"
                iconName: "spells"

                // slot pips, same as the Spells screen (and desktop):
                // tap one to spend or restore it
                ColumnLayout {
                    visible: sheetBridge.spellSlots.length > 0 || sheetBridge.pactSlots.max > 0
                    Layout.fillWidth: true
                    spacing: 0
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
                    MSlotBar {
                        Layout.fillWidth: true
                        label: "Pact L" + sheetBridge.pactSlots.level
                        max: sheetBridge.pactSlots.max
                        used: sheetBridge.pactSlots.used
                        fillColor: Theme.purple
                        accentColor: Theme.purple2
                        onToggled: (n) => sheetBridge.setSlotsUsed(-1, n)
                    }
                }

                Label {
                    visible: root.combatSpellGroups.length === 0
                             && sheetBridge.unavailableFavourites.length === 0
                    text: "No favourite spells yet -- tap the star on a spell on the Spells screen "
                          + "and it'll appear here, ready to cast."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Repeater {
                    model: root.combatSpellGroups
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Label {
                            text: modelData.bucket
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                        }
                        Repeater {
                            model: modelData.items
                            delegate: RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                // level badge: C for cantrips, else the level
                                Rectangle {
                                    implicitWidth: 30
                                    implicitHeight: 24
                                    radius: 6
                                    color: Theme.surf2
                                    border.color: modelData.spellLevel === 0 ? Theme.border : Theme.indigo2
                                    Label {
                                        anchors.centerIn: parent
                                        text: modelData.spellLevel === 0 ? "C" : "L" + modelData.spellLevel
                                        color: modelData.spellLevel === 0 ? Theme.text3 : Theme.indigo2
                                        font.pixelSize: Theme.fsSmall
                                        font.bold: true
                                    }
                                }
                                MIcon {
                                    visible: modelData.pinned
                                    name: "star_solid"
                                    size: 14
                                }
                                Label {
                                    text: modelData.spellName
                                    color: Theme.text
                                    font.pixelSize: Theme.fsBody
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    visible: modelData.concentration
                                    text: "Conc."
                                    color: Theme.amber
                                    font.pixelSize: Theme.fsSmall
                                }
                                MButton {
                                    objectName: "castButton_" + modelData.spellName
                                    implicitHeight: 36
                                    implicitWidth: 72
                                    text: "Cast"
                                    onClicked: sheetBridge.castSpell(modelData.spellName)
                                }
                            }
                        }
                    }
                }

                // Starred spells that can't be cast from here, shown anyway
                // with the reason (usually: a prepared caster hasn't
                // prepared it) rather than silently left out.
                Label {
                    visible: sheetBridge.unavailableFavourites.length > 0
                    text: "Starred, not castable here"
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    font.bold: true
                }
                Repeater {
                    model: sheetBridge.unavailableFavourites
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Rectangle {
                                implicitWidth: 30
                                implicitHeight: 24
                                radius: 6
                                color: Theme.surf2
                                border.color: Theme.border
                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.level === 0 ? "C" : modelData.levelText
                                    color: Theme.text3
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                            }
                            MIcon {
                                name: "star_solid"
                                size: 14
                                color: Theme.text3
                            }
                            Label {
                                text: modelData.name
                                color: Theme.text3
                                font.pixelSize: Theme.fsBody
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                            MButton {
                                implicitHeight: 36
                                implicitWidth: 72
                                text: "Cast"
                                enabled: false
                            }
                        }
                        Label {
                            text: modelData.reason
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                            font.italic: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            Layout.leftMargin: 38
                        }
                    }
                }
            }

            // ── Hit dice ────────────────────────────────────────────────
            MCard {
                visible: sheetBridge.hitDiceList.length > 0
                title: "Hit Dice"
                iconName: "dice"

                Repeater {
                    model: sheetBridge.hitDiceList
                    delegate: RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: modelData.dieKey + "  (" + modelData.remaining + " / " + modelData.total + ")"
                            color: Theme.text
                            font.pixelSize: Theme.fsBody
                            Layout.fillWidth: true
                        }
                        MButton {
                            primary: false
                            implicitHeight: 36
                            iconName: "dice"
                            iconSize: 16
                            text: "Spend"
                            enabled: modelData.remaining > 0
                            onClicked: sheetBridge.spendHitDie(modelData.dieKey)
                        }
                    }
                }
            }

            // ── Wild Shape (Druids only) ────────────────────────────────
            // While transformed, the HP/AC cards above already show the
            // beast's own numbers (CharacterSheetBridge repurposes them).
            MCard {
                visible: sheetBridge.wildShapeAvailable
                title: "Wild Shape"
                iconName: "paw"
                accent: Theme.indigo2

                Column {
                    id: wsCol
                    Layout.fillWidth: true
                    spacing: 10

                    ColumnLayout {
                        visible: sheetBridge.wildShapeActive
                        width: wsCol.width
                        spacing: 6
                        Label {
                            text: "Currently: " + sheetBridge.wildShapeActiveBeast
                            color: Theme.text
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                        }
                        MButton {
                            primary: false
                            text: "Revert to Normal Form"
                            onClicked: sheetBridge.revertWildShape()
                        }
                    }

                    ColumnLayout {
                        visible: !sheetBridge.wildShapeActive
                        width: wsCol.width
                        spacing: 6
                        ComboBox {
                            id: beastPicker
                            Layout.fillWidth: true
                            model: sheetBridge.availableWildShapeBeasts
                            textRole: "name"
                            valueRole: "name"
                            displayText: currentIndex >= 0 && model.length > 0
                                         ? model[currentIndex].name + " (CR " + model[currentIndex].crLabel + ")"
                                         : "No beasts available"
                        }
                        Label {
                            text: sheetBridge.wildShapeUsesLeft < 0
                                  ? "Unlimited uses (Archdruid)"
                                  : sheetBridge.wildShapeUsesLeft + " / " + sheetBridge.wildShapeUsesMax + " uses remaining (short/long rest)"
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                        }
                        Label {
                            text: sheetBridge.wildShapeRestrictionText
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                        }
                        MButton {
                            text: sheetBridge.wildShapeUsesLeft < 0 ? "Transform" : "Transform (" + sheetBridge.wildShapeUsesLeft + " left)"
                            enabled: beastPicker.model.length > 0
                                     && (sheetBridge.wildShapeUsesLeft < 0 || sheetBridge.wildShapeUsesLeft > 0)
                            onClicked: sheetBridge.transformWildShape(beastPicker.currentValue)
                        }
                    }
                }
            }

            // ── Conditions ──────────────────────────────────────────────
            MCard {
                title: "Conditions"
                iconName: "cond_stunned"

                // Every condition in an even 3-column table: 16 conditions,
                // then Exhaustion (a level, set with - / +) and Clear all --
                // 6 rows of 3. Tap a cell to toggle it.
                GridLayout {
                    objectName: "conditionGrid"
                    Layout.fillWidth: true
                    columns: 3
                    columnSpacing: 6
                    rowSpacing: 6

                    Repeater {
                        model: sheetBridge.allConditions.filter(function(c) { return c.name !== "Exhaustion" })
                        delegate: Rectangle {
                            objectName: "conditionChip_" + modelData.name
                            readonly property bool isOn: modelData.active
                            readonly property bool viaOther: !isOn && modelData.impliedBy.length > 0
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            implicitWidth: 0
                            Layout.preferredHeight: 64
                            radius: 8
                            color: isOn ? Qt.rgba(Theme.crimson.r, Theme.crimson.g, Theme.crimson.b, 0.20)
                               : viaOther ? Qt.rgba(Theme.crimson.r, Theme.crimson.g, Theme.crimson.b, 0.08)
                               : Theme.surf2
                            border.color: isOn ? Theme.crimson2 : (viaOther ? Theme.crimson : Theme.border)
                            border.width: isOn ? 2 : 1
                            Column {
                                anchors.centerIn: parent
                                width: parent.width - 8
                                spacing: 3
                                MIcon {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    name: modelData.icon
                                    size: 20
                                    color: isOn || viaOther ? Theme.crimson2 : Theme.indigo2
                                }
                                Label {
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                    text: modelData.name
                                    color: isOn || viaOther ? Theme.crimson2 : Theme.text
                                    font.pixelSize: Theme.fsSmall - 1
                                    font.bold: isOn
                                    elide: Text.ElideRight
                                }
                                Label {
                                    visible: viaOther
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                    text: "via " + modelData.impliedBy
                                    color: Theme.crimson2
                                    font.pixelSize: Theme.fsSmall - 3
                                    elide: Text.ElideRight
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: sheetBridge.setConditionActive(modelData.name, !modelData.active)
                            }
                        }
                    }

                    // Exhaustion: a level, 0-6
                    Rectangle {
                        id: exhCell
                        objectName: "exhaustionCell"
                        readonly property int level: sheetBridge.exhaustionLevel
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        implicitWidth: 0
                        Layout.preferredHeight: 64
                        radius: 8
                        color: level > 0 ? Qt.rgba(Theme.crimson.r, Theme.crimson.g, Theme.crimson.b, 0.20) : Theme.surf2
                        border.color: level > 0 ? Theme.crimson2 : Theme.border
                        border.width: level > 0 ? 2 : 1
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 2
                            spacing: 0
                            Label {
                                objectName: "exhaustionDown"
                                text: "−"
                                color: exhCell.level > 0 ? Theme.text : Theme.text3
                                font.pixelSize: Theme.fsBody + 2
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                Layout.preferredWidth: 26
                                Layout.fillHeight: true
                                MouseArea { anchors.fill: parent; onClicked: sheetBridge.setExhaustionLevel(Math.max(0, sheetBridge.exhaustionLevel - 1)) }
                            }
                            Column {
                                Layout.fillWidth: true
                                spacing: 3
                                MIcon {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    name: "cond_exhaustion"
                                    size: 20
                                    color: exhCell.level > 0 ? Theme.crimson2 : Theme.indigo2
                                }
                                Label {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: "Exhaust. " + exhCell.level
                                    color: exhCell.level > 0 ? Theme.crimson2 : Theme.text
                                    font.pixelSize: Theme.fsSmall - 1
                                    font.bold: exhCell.level > 0
                                }
                            }
                            Label {
                                objectName: "exhaustionUp"
                                text: "+"
                                color: exhCell.level < 6 ? Theme.text : Theme.text3
                                font.pixelSize: Theme.fsBody + 2
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                Layout.preferredWidth: 26
                                Layout.fillHeight: true
                                MouseArea { anchors.fill: parent; onClicked: sheetBridge.setExhaustionLevel(Math.min(6, sheetBridge.exhaustionLevel + 1)) }
                            }
                        }
                    }

                    // Clear all
                    Rectangle {
                        objectName: "clearConditionsCell"
                        readonly property bool any: sheetBridge.activeConditions.some(function(c) { return c.name.indexOf("Exhaustion") !== 0 })
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        implicitWidth: 0
                        Layout.preferredHeight: 64
                        radius: 8
                        color: Theme.surf2
                        border.color: Theme.border
                        opacity: any ? 1.0 : 0.45
                        Column {
                            anchors.centerIn: parent
                            spacing: 3
                            MIcon { anchors.horizontalCenter: parent.horizontalCenter; name: "refresh"; size: 20 }
                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "Clear all"
                                color: Theme.text
                                font.pixelSize: Theme.fsSmall - 1
                            }
                        }
                        MouseArea { anchors.fill: parent; enabled: parent.any; onClicked: sheetBridge.clearConditions() }
                    }
                }

                Label {
                    visible: sheetBridge.exhaustionEffectText.length > 0
                    text: sheetBridge.exhaustionEffectText
                    color: Theme.crimson2
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                // what each active condition does
                Repeater {
                    model: sheetBridge.activeConditions.filter(function(c) { return c.name.indexOf("Exhaustion") !== 0 })
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        radius: 8
                        color: Qt.rgba(Theme.crimson.r, Theme.crimson.g, Theme.crimson.b, 0.10)
                        border.color: Theme.crimson
                        implicitHeight: acCol.implicitHeight + 14
                        Column {
                            id: acCol
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
                            spacing: 2
                            Label {
                                text: modelData.name
                                color: Theme.crimson2
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                            }
                            Label {
                                text: modelData.effectText
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                                width: parent.width
                            }
                        }
                    }
                }
            }

            // ── Effects on you (desktop's Active Effects) ───────────────
            // Bless or Guidance an ally cast, a potion...: what each does,
            // End to take it off, and Add for one put on you. Checks, saves
            // and attacks use them.
            MCard {
                objectName: "effectsCard"
                title: "Effects on You"
                iconName: "effects"

                Label {
                    visible: sheetBridge.activeEffectRows.length === 0
                    text: "Nothing on you. A spell you cast on yourself shows here; add one an ally put on you."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Repeater {
                    model: sheetBridge.activeEffectRows
                    delegate: Rectangle {
                        objectName: "effectRow_" + modelData.name
                        Layout.fillWidth: true
                        radius: 8
                        color: Theme.surf2
                        border.color: Theme.border
                        implicitHeight: Math.max(fxCol.implicitHeight, fxEnd.height) + 14
                        Rectangle {
                            width: 4; radius: 2
                            anchors { left: parent.left; top: parent.top; bottom: parent.bottom; margins: 1 }
                            color: Theme.teal2
                        }
                        Column {
                            id: fxCol
                            anchors { left: parent.left; right: fxEnd.left; top: parent.top
                                      leftMargin: 14; rightMargin: 8; topMargin: 7 }
                            spacing: 2
                            Label {
                                text: modelData.name + (modelData.concentration ? " (concentration)" : "")
                                color: Theme.text
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                wrapMode: Text.WordWrap
                                width: parent.width
                            }
                            Label {
                                text: modelData.note
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall - 1
                                wrapMode: Text.WordWrap
                                width: parent.width
                            }
                        }
                        MButton {
                            id: fxEnd
                            anchors { right: parent.right; top: parent.top; margins: 6 }
                            primary: false
                            height: 32
                            text: "End"
                            onClicked: sheetBridge.removeActiveEffect(modelData.name)
                        }
                    }
                }
                MButton {
                    objectName: "addEffectButton"
                    Layout.fillWidth: true
                    primary: false
                    text: "Add an effect on you"
                    onClicked: effectPicker.open()
                }
            }
        }
    }

    MPickerDialog {
        id: effectPicker
        dialogTitle: "Add an effect on you"
        options: sheetBridge.effectChoices
        onPicked: (value) => sheetBridge.addActiveEffect(value)
    }

    // How much ammunition you have: type a number or use - / + (hold to
    // step by 5); the inventory follows
    Dialog {
        id: ammoDialog
        objectName: "ammoDialog"
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
                text: root.ammoEditLabel
                color: Theme.gold2
                font.pixelSize: Theme.fsHead
                font.bold: true
                Layout.fillWidth: true
            }
            Label {
                text: "How many " + root.ammoEditLabel.toLowerCase() + " do you have?"
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            MSpinBox {
                id: ammoQty
                objectName: "ammoCountSpin"
                Layout.fillWidth: true
                implicitHeight: 48
                from: 0
                to: 9999
                holdStep: 5
                live: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    Layout.fillWidth: true
                    primary: false
                    text: "Cancel"
                    onClicked: ammoDialog.close()
                }
                MButton {
                    objectName: "ammoSave"
                    Layout.fillWidth: true
                    text: "Save"
                    onClicked: {
                        ammoDialog.close()
                        sheetBridge.setAmmoCount(root.ammoEditKind, ammoQty.value)
                    }
                }
            }
        }
    }

    // Full-screen death overlay -- matches ui_desktop's combat.py
    // _show_death_screen(), triggered by 3 failed death saves, massive
    // damage or exhaustion level 6 (and it says which).
    Rectangle {
        anchors.fill: parent
        visible: sheetBridge.isDead
        color: Qt.rgba(0, 0, 0, 0.85)
        z: 1000

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 24

            Label {
                text: "YOU DIED"
                color: "#c00000"
                font.pixelSize: 40
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }
            // What killed them. Plain light text under the title (dark red
            // vanished into the black overlay; fixed colour, since the
            // overlay is black on every theme).
            Label {
                text: sheetBridge.deathCauseText
                color: "#e6d3d3"
                font.pixelSize: Theme.fsBody + 1
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.maximumWidth: root.width - 48
                Layout.alignment: Qt.AlignHCenter
            }
            MButton {
                objectName: "reviveButton"
                text: "Revive"
                Layout.alignment: Qt.AlignHCenter
                onClicked: sheetBridge.revive()
            }
        }
    }
}
