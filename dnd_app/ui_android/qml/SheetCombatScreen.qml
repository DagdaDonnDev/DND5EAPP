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

    // Castable combat spells, grouped by casting time -- the spell entries
    // of the same action buckets the Actions screen shows (cantrips,
    // bonus-action/reaction spells, and leveled spells pinned with the
    // star on the Spells screen). Pinned first, then by level and name.
    readonly property var combatSpellGroups: {
        if (!sheetBridge)
            return []
        var out = []
        var groups = sheetBridge.actionAbilities
        for (var i = 0; i < groups.length; ++i) {
            if (groups[i].bucketKey === "Passive")
                continue
            var items = groups[i].items.filter(function(it) { return it.isSpell })
            items.sort(function(a, b) {
                return (b.pinned - a.pinned) || (a.spellLevel - b.spellLevel)
                       || a.spellName.localeCompare(b.spellName)
            })
            if (items.length > 0)
                out.push({ bucket: groups[i].bucket, bucketKey: groups[i].bucketKey, items: items })
        }
        return out
    }
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
                        MButton {
                            primary: false
                            implicitHeight: 36
                            text: "Drop"
                            onClicked: sheetBridge.dropConcentration()
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    MSpinBox {
                        id: hpAmount
                        Layout.preferredWidth: 100
                        from: 0
                        to: 999
                        value: 1
                    }
                    MButton {
                        Layout.fillWidth: true
                        primary: false
                        text: "Damage"
                        onClicked: sheetBridge.applyDamage(hpAmount.value)
                    }
                    MButton {
                        Layout.fillWidth: true
                        text: "Heal"
                        onClicked: sheetBridge.applyHealing(hpAmount.value)
                    }
                    MButton {
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
                              used: sheetBridge.turnCounts.action, limit: sheetBridge.turnCounts.actionLimit },
                            { key: "Bonus Action", label: "Bonus", icon: "bonus",
                              used: sheetBridge.turnCounts.bonusAction, limit: sheetBridge.turnCounts.bonusActionLimit },
                            { key: "Reaction", label: "Reaction", icon: "bolt",
                              used: sheetBridge.turnCounts.reaction, limit: sheetBridge.turnCounts.reactionLimit },
                        ]
                        delegate: Rectangle {
                            id: chip
                            objectName: "turnChip_" + modelData.key
                            // captured: the pip Repeater below has its own modelData
                            readonly property int usedCount: modelData.used
                            readonly property int limitCount: modelData.limit
                            readonly property bool spent: usedCount >= limitCount
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            Layout.preferredHeight: 62
                            radius: 10
                            color: spent ? Theme.surf2 : Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.14)
                            border.color: spent ? Theme.border : Theme.teal2
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
                                // one pip per use this turn: filled = still available
                                Row {
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
                                              + (modelData.onHitBonusText !== "" ? "  ·  " + modelData.onHitBonusText : "")
                                        color: Theme.text3
                                        font.pixelSize: Theme.fsSmall
                                        wrapMode: Text.WordWrap
                                        width: parent.width
                                    }
                                }
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
                                MButton {
                                    objectName: "attackButton_" + modelData.name
                                    Layout.fillWidth: true
                                    iconName: "dice"
                                    iconSize: 16
                                    text: "Attack"
                                    onClicked: sheetBridge.rollWeaponAttack(modelData.name)
                                }
                                MButton {
                                    Layout.fillWidth: true
                                    primary: false
                                    text: "Damage"
                                    onClicked: sheetBridge.rollWeaponDamage(modelData.name, false)
                                }
                                MButton {
                                    primary: false
                                    text: "Crit"
                                    onClicked: sheetBridge.rollWeaponDamage(modelData.name, true)
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

                // slot summary: remaining / max per level
                Flow {
                    visible: sheetBridge.spellSlots.length > 0 || sheetBridge.pactSlots.max > 0
                    Layout.fillWidth: true
                    spacing: 6
                    Repeater {
                        model: sheetBridge.spellSlots
                        delegate: Rectangle {
                            readonly property int slotsLeft: modelData.max - modelData.used
                            radius: 6
                            color: Theme.surf2
                            border.color: slotsLeft > 0 ? Theme.indigo2 : Theme.border
                            implicitWidth: slotLbl.implicitWidth + 14
                            implicitHeight: slotLbl.implicitHeight + 8
                            Label {
                                id: slotLbl
                                anchors.centerIn: parent
                                text: "L" + modelData.level + "  " + parent.slotsLeft + "/" + modelData.max
                                color: parent.slotsLeft > 0 ? Theme.text : Theme.text3
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                            }
                        }
                    }
                    Rectangle {
                        visible: sheetBridge.pactSlots.max > 0
                        readonly property int slotsLeft: sheetBridge.pactSlots.max - sheetBridge.pactSlots.used
                        radius: 6
                        color: Theme.surf2
                        border.color: slotsLeft > 0 ? Theme.purple2 : Theme.border
                        implicitWidth: pactLbl.implicitWidth + 14
                        implicitHeight: pactLbl.implicitHeight + 8
                        Label {
                            id: pactLbl
                            anchors.centerIn: parent
                            text: "Pact L" + sheetBridge.pactSlots.level + "  " + parent.slotsLeft + "/" + sheetBridge.pactSlots.max
                            color: parent.slotsLeft > 0 ? Theme.text : Theme.text3
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                        }
                    }
                }

                Label {
                    visible: root.combatSpellGroups.length === 0
                    text: "No combat spells ready. Cantrips and bonus-action/reaction spells appear here "
                          + "automatically; pin other spells with the star on the Spells screen."
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

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    MIcon { name: "cond_exhaustion"; size: 20 }
                    Label {
                        text: "Exhaustion"
                        color: Theme.text2
                        font.pixelSize: Theme.fsSmall
                        Layout.fillWidth: true
                    }
                    MSpinBox {
                        Layout.preferredWidth: 100
                        from: 0
                        to: 6
                        value: sheetBridge.exhaustionLevel
                        onValueModified: sheetBridge.setExhaustionLevel(value)
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

                // active conditions and what they do
                Repeater {
                    model: sheetBridge.activeConditions
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

                // every condition as a tap-to-toggle chip
                Flow {
                    Layout.fillWidth: true
                    spacing: 6
                    Repeater {
                        model: sheetBridge.allConditions
                        delegate: Rectangle {
                            objectName: "conditionChip_" + modelData.name
                            radius: 8
                            color: modelData.active ? Qt.rgba(Theme.crimson.r, Theme.crimson.g, Theme.crimson.b, 0.18) : Theme.surf2
                            border.color: modelData.active ? Theme.crimson2 : Theme.border
                            implicitWidth: chipRow.implicitWidth + 16
                            implicitHeight: 36
                            Row {
                                id: chipRow
                                anchors.centerIn: parent
                                spacing: 6
                                MIcon {
                                    name: modelData.icon
                                    size: 16
                                    color: modelData.active ? Theme.crimson2 : Theme.indigo2
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Label {
                                    text: modelData.name
                                    color: modelData.active ? Theme.crimson2 : Theme.text
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: modelData.active
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: sheetBridge.setConditionActive(modelData.name, !modelData.active)
                            }
                        }
                    }
                }
            }
        }
    }

    // Full-screen death overlay -- matches ui_desktop's combat.py
    // _show_death_screen(), triggered by 3 failed death saves or
    // exhaustion level 6.
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
            Label {
                text: "Instant death: damage ≥ 2× max HP in one hit"
                color: "#aa3333"
                font.pixelSize: Theme.fsSmall
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
