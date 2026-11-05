import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// The Rest, as desktop's Rest dialog has it: Short or Long (a switch at
// the top), what it will do, the hit dice to spend on a short rest (and
// what adds to them: Song of Rest, a Chef's food), what can be ticked on
// it (re-preparing spells, a pact weapon, temporary hit points -- yours
// or your party's), and everything else the rest allows. One Confirm does
// the lot; then, one at a time, whichever ticked options need a follow-up
// pick ("which model?") ask for it. Reachable from the drawer on any
// screen (see App.qml/NavDrawer.qml).
MFullPageDialog {
    id: root
    objectName: "restFlowDialog"
    dialogTitle: "Rest"

    // Set explicitly by App.qml (window.sheetBridge) rather than
    // resolved here via the Window.window attached property -- this
    // component's root type is a Popup (via MFullPageDialog), and
    // Window.window is only valid on Item-derived types.
    property QtObject sheetBridge: null
    property string restType: "short"
    property string longBlock: ""
    property var diceNote: ({"left": 0, "can_spend": false, "text": ""})
    property var selectedOptionKinds: []
    property int optionQueueIndex: 0
    property string pendingOptionKind: ""
    property string pendingAstralSkill: ""

    function start(type) {
        // Resets EVERY piece of this dialog's state, so a rest started
        // again (or one backed out of mid-flow) never reads the last
        // one's leftovers. open() is deliberately never preceded by a
        // defensive close(): that's the "two Popups transitioning at
        // once" timing hazard NavDrawer's own rest button works around;
        // open() is a no-op when already open.
        longBlock = sheetBridge.longRestBlock()
        selectedOptionKinds = []
        optionQueueIndex = 0
        pendingOptionKind = ""
        pendingAstralSkill = ""
        setType(type === "long" && longBlock === "" ? "long" : "short")
        open()
    }

    // Short or long: everything below follows the switch
    function setType(kind) {
        restType = kind
        previewLabel.text = sheetBridge.restPreviewLines(kind).join("\n")
        diceNote = sheetBridge.restDiceNote()
        hitDiceSpin.to = diceNote.left
        hitDiceSpin.value = 0
        optionsRepeater.model = sheetBridge.restOptions(kind)
        var extras = sheetBridge.restExtras(kind)
        diceExtrasRepeater.model = extras.filter(function (e) { return e.group === "dice" })
        restExtrasRepeater.model = extras.filter(function (e) { return e.group === "rest" && !e.party })
        partyExtrasRepeater.model = extras.filter(function (e) { return e.group === "rest" && e.party })
        activitiesRepeater.model = sheetBridge.restActivities(kind)
    }

    function diceToSpend() {
        return restType === "short" && diceNote.can_spend ? hitDiceSpin.value : 0
    }

    // {key: the number in its box, or true}, for what was ticked -- what
    // adds to the hit dice only when some are spent
    function chosenExtras() {
        var out = {}
        var reps = [diceExtrasRepeater, restExtrasRepeater, partyExtrasRepeater]
        for (var r = 0; r < reps.length; r++) {
            for (var i = 0; i < reps[r].count; i++) {
                var it = reps[r].itemAt(i)
                if (!it || !it.ticked) continue
                if (it.extra.group === "dice" && diceToSpend() === 0) continue
                out[it.extra.key] = it.extra.ask !== "" ? it.amount : true
            }
        }
        return out
    }

    function confirmRest() {
        var sel = []
        for (var i = 0; i < optionsRepeater.count; i++) {
            var item = optionsRepeater.itemAt(i)
            if (item && item.optChecked) sel.push(item.optKind)
        }
        selectedOptionKinds = sel
        sheetBridge.setRestExtras(chosenExtras())
        if (restType === "short") {
            sheetBridge.applyShortRest(diceToSpend())
        } else {
            sheetBridge.applyLongRest()
        }
        optionQueueIndex = 0
        processNextOption()
    }

    function processNextOption() {
        if (optionQueueIndex >= selectedOptionKinds.length) {
            root.close()
            return
        }
        var kind = selectedOptionKinds[optionQueueIndex]
        optionQueueIndex++
        pendingOptionKind = kind
        if (kind === "unprepare_all" || kind === "pact_tome_replace" ||
            kind === "pact_talisman_replace" || kind === "arcane_recovery" ||
            kind === "natural_recovery") {
            if (kind === "arcane_recovery") sheetBridge.applyArcaneRecovery()
            else if (kind === "natural_recovery") sheetBridge.applyNaturalRecovery()
            else sheetBridge.applyRestOptionSimple(kind)
            processNextOption()
        } else if (kind === "astral_knowledge_swap") {
            astralSkillDialog.options = sheetBridge.restOptionPool(kind)
            astralSkillDialog.open()
        } else {
            var pool = sheetBridge.restOptionPool(kind)
            if (pool.length === 0) {
                sheetBridge.notify("You don't own a matching item for that option yet -- skipped.")
                processNextOption()
            } else {
                valuePickerDialog.dialogTitle = "Choose a new value"
                valuePickerDialog.options = pool
                valuePickerDialog.open()
            }
        }
    }

    // One half of the Short/Long switch
    component TypeButton: Button {
        id: tb
        property string kind: ""
        property string label: ""
        property bool first: false
        Layout.fillWidth: true
        implicitHeight: 40
        topInset: 0
        bottomInset: 0
        enabled: kind === "short" || root.longBlock === ""
        onClicked: root.setType(kind)
        contentItem: Text {
            text: tb.label
            color: root.restType === tb.kind ? Theme.gold2 : (tb.enabled ? Theme.text2 : Theme.text3)
            font.pixelSize: Theme.fsSmall
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 8
            color: root.restType === tb.kind ? Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.2) : Theme.surf
            border.width: 2
            border.color: root.restType === tb.kind ? Theme.gold : Theme.border2
        }
    }

    // One extra (core's rest_extras): a tick; one that needs a number (a
    // die you rolled, an ally's temporary hit points) opens a box for it
    component ExtraRow: ColumnLayout {
        id: er
        property var extra: ({})
        property alias ticked: tick.checked
        property alias amount: amountSpin.value
        Layout.fillWidth: true
        spacing: 4
        MCheckBox {
            id: tick
            objectName: "restExtra_" + er.extra.key
            Layout.fillWidth: true
            text: er.extra.label
            checked: !!er.extra.checked
            enabled: er.extra.group !== "dice" || hitDiceSpin.value > 0
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            visible: tick.checked && er.extra.ask !== ""
            spacing: 8
            Label {
                text: er.extra.ask === "rolled" ? "You rolled" : "How many?"
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
            }
            MSpinBox {
                id: amountSpin
                objectName: "restExtraValue_" + er.extra.key
                Layout.preferredWidth: 150
                from: er.extra.ask === "rolled" ? 1 : 0
                to: er.extra.max || 99
                value: from
            }
            Label {
                Layout.fillWidth: true
                visible: er.extra.ask === "rolled"
                text: er.extra.key === "ally_song_of_rest" ? "(d6 to d12, by their level)" : "(1–" + er.extra.max + ")"
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
            }
        }
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: width
        contentHeight: col.height
        clip: true

        ColumnLayout {
            id: col
            width: parent.width
            spacing: 14

            // Short or long
            RowLayout {
                Layout.fillWidth: true
                spacing: 0
                TypeButton { objectName: "restTypeShort"; kind: "short"; label: "Short Rest · 1 hour" }
                TypeButton { objectName: "restTypeLong"; kind: "long"; label: "Long Rest · 8 hours" }
            }
            Label {
                objectName: "restLongBlock"
                Layout.fillWidth: true
                visible: root.longBlock !== ""
                wrapMode: Text.WordWrap
                text: "Can't take a long rest: " + root.longBlock + "."
                color: Theme.crimson2
                font.pixelSize: Theme.fsSmall
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 10
                color: Theme.surf
                border.color: Theme.teal
                implicitHeight: previewCol.height + 24
                ColumnLayout {
                    id: previewCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 6
                    Label { text: "WHAT THIS WILL DO"; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    Label { id: previewLabel; Layout.fillWidth: true; wrapMode: Text.WordWrap; color: Theme.text; font.pixelSize: Theme.fsBody }
                }
            }

            // Hit dice to spend (a short rest), and what adds to them
            Rectangle {
                objectName: "restDiceCard"
                Layout.fillWidth: true
                visible: root.restType === "short"
                radius: 10
                color: Theme.surf
                border.color: Theme.green
                implicitHeight: diceCol.height + 24
                ColumnLayout {
                    id: diceCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 8
                    Label { text: "SPEND HIT DICE"; color: Theme.green2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    MSpinBox {
                        id: hitDiceSpin
                        objectName: "hitDiceSpin"
                        Layout.fillWidth: true
                        from: 0
                        enabled: root.diceNote.can_spend
                    }
                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: root.diceNote.text
                        color: Theme.text2
                        font.pixelSize: Theme.fsSmall
                    }
                    Repeater {
                        id: diceExtrasRepeater
                        objectName: "restDiceExtrasRepeater"
                        delegate: ExtraRow { extra: modelData; visible: root.diceNote.can_spend }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                visible: optionsRepeater.count + restExtrasRepeater.count + partyExtrasRepeater.count > 0
                radius: 10
                color: Theme.surf
                border.color: Theme.indigo
                implicitHeight: optCol.height + 24
                ColumnLayout {
                    id: optCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 6
                    Label { text: "ALSO ON THIS REST"; color: Theme.indigo2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    Label {
                        Layout.fillWidth: true; wrapMode: Text.WordWrap
                        text: "Tick anything you'd like as part of it."
                        color: Theme.text3; font.pixelSize: Theme.fsSmall
                    }
                    Repeater {
                        id: optionsRepeater
                        objectName: "restOptionsRepeater"
                        delegate: MCheckBox {
                            Layout.fillWidth: true
                            property string optKind: modelData.kind
                            property bool optChecked: checked
                            text: modelData.label
                        }
                    }
                    Repeater {
                        id: restExtrasRepeater
                        objectName: "restExtrasRepeater"
                        delegate: ExtraRow { extra: modelData }
                    }
                    Label {
                        visible: partyExtrasRepeater.count > 0
                        Layout.topMargin: 6
                        text: "FROM YOUR PARTY"
                        color: Theme.text3
                        font.bold: true
                        font.pixelSize: Theme.fsSmall
                    }
                    Repeater {
                        id: partyExtrasRepeater
                        objectName: "restPartyExtrasRepeater"
                        delegate: ExtraRow { extra: modelData }
                    }
                }
            }

            // Everything else the character can do on this rest: their
            // own features', feats', race's and items', and the rules
            // everyone has (core's rest_activities, as desktop's Rest)
            Rectangle {
                objectName: "restActivitiesCard"
                Layout.fillWidth: true
                visible: activitiesRepeater.count > 0
                radius: 10
                color: Theme.surf
                border.color: Theme.gold
                implicitHeight: actCol.height + 24
                ColumnLayout {
                    id: actCol
                    x: 14; y: 12
                    width: parent.width - 28
                    spacing: 8
                    Label { text: "YOU CAN ALSO"; color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    Repeater {
                        id: activitiesRepeater
                        objectName: "restActivitiesRepeater"
                        delegate: Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            textFormat: Text.StyledText
                            color: Theme.text
                            font.pixelSize: Theme.fsSmall
                            text: "<b>" + modelData.source.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "</b> — "
                                  + modelData.text.replace(/&/g, "&amp;").replace(/</g, "&lt;")
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                Item { Layout.fillWidth: true }
                MButton { text: "Cancel"; primary: false; onClicked: root.close() }
                MButton {
                    objectName: "restConfirm"
                    text: root.restType === "long" ? "Take a Long Rest" : "Take a Short Rest"
                    onClicked: root.confirmRest()
                }
            }
        }
    }

    MPickerDialog {
        id: valuePickerDialog
        onPicked: (value) => { sheetBridge.applyRestOptionWithValue(root.pendingOptionKind, value); root.processNextOption() }
    }
    MPickerDialog {
        id: astralSkillDialog
        dialogTitle: "New skill proficiency"
        onPicked: (value) => {
            root.pendingAstralSkill = value
            astralToolDialog.options = sheetBridge.astralKnowledgeToolPool()
            astralToolDialog.open()
        }
    }
    MPickerDialog {
        id: astralToolDialog
        dialogTitle: "New weapon or tool proficiency"
        onPicked: (value) => { sheetBridge.applyAstralKnowledgeSwap(root.pendingAstralSkill, value); root.processNextOption() }
    }
}
