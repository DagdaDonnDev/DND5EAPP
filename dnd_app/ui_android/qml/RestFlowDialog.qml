import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Full port of ui_desktop's RestOptionsDialog + RestPreviewDialog flow,
// reachable from the drawer on any screen (see App.qml/NavDrawer.qml).
// A small state machine rather than a single static form, since
// desktop's real flow is genuinely sequential: preview+"also
// reconfigure?" checklist -> (short rest only) how many hit dice to
// spend -> apply the core rest -> then, one at a time, resolve
// whichever reconfigure options were checked (most need their own
// follow-up "pick a new X" dialog).
MFullPageDialog {
    id: root
    objectName: "restFlowDialog"
    dialogTitle: restType === "long" ? "Long Rest" : "Short Rest"

    // Set explicitly by App.qml (window.sheetBridge) rather than
    // resolved here via the Window.window attached property -- this
    // component's root type is a Popup (via MFullPageDialog), and
    // Window.window is only valid on Item-derived types.
    property QtObject sheetBridge: null
    property string restType: "short"
    property var selectedOptionKinds: []
    property int optionQueueIndex: 0
    property string pendingOptionKind: ""
    property string pendingAstralSkill: ""
    // 0 = preview+options, 1 = hit-dice-to-spend prompt
    property int page: 0

    function start(type) {
        // Resets EVERY piece of this dialog's state, not just the
        // preview/options/hit-dice fields -- a rest started again
        // shortly after a previous one (or one backed out of via the
        // phone's back button mid-flow, before its option queue ever
        // finished) used to carry over stale selectedOptionKinds/
        // optionQueueIndex/pendingOptionKind, which could leave the
        // second rest's follow-up option queue reading leftover state
        // from the first. open() itself is deliberately never preceded
        // by a defensive close() here -- that's exactly the "two
        // Popups transitioning at once" timing hazard NavDrawer's own
        // rest buttons already had to work around once (see its
        // onClicked comment); open() is a no-op when already open, so
        // resetting every property below and calling it unconditionally
        // refreshes the visible state either way, with no transition
        // race to depend on.
        // a long rest at 0 HP gains nothing -- the bridge says why (toast)
        if (sheetBridge.restBlockReason(type) !== "")
            return
        restType = type
        page = 0
        selectedOptionKinds = []
        optionQueueIndex = 0
        pendingOptionKind = ""
        pendingAstralSkill = ""
        previewLabel.text = sheetBridge.restPreviewLines(type).join("\n")
        optionsRepeater.model = sheetBridge.restOptions(type)
        hitDiceSpin.to = sheetBridge.hitDiceAvailableForRest
        hitDiceSpin.value = 0
        open()
    }

    function confirmPreview() {
        var sel = []
        for (var i = 0; i < optionsRepeater.count; i++) {
            var item = optionsRepeater.itemAt(i)
            if (item && item.optChecked) sel.push(item.optKind)
        }
        selectedOptionKinds = sel
        if (restType === "short" && sheetBridge.hitDiceAvailableForRest > 0 && sheetBridge.currentHp < sheetBridge.maxHp) {
            page = 1
        } else {
            applyCoreRest(0)
        }
    }

    function applyCoreRest(hitDice) {
        if (restType === "short") {
            sheetBridge.applyShortRest(hitDice || 0)
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
            kind === "pact_talisman_replace" || kind === "arcane_recovery") {
            if (kind === "arcane_recovery") sheetBridge.applyArcaneRecovery()
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

            // ── Page 0: preview + reconfigure checklist ─────────────
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === 0
                spacing: 14

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

                Rectangle {
                    Layout.fillWidth: true
                    visible: optionsRepeater.count > 0
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.indigo
                    implicitHeight: optCol.height + 24
                    ColumnLayout {
                        id: optCol
                        x: 14; y: 12
                        width: parent.width - 28
                        spacing: 6
                        Label { text: "ALSO RECONFIGURE?"; color: Theme.indigo2; font.bold: true; font.pixelSize: Theme.fsSmall }
                        Label {
                            Layout.fillWidth: true; wrapMode: Text.WordWrap
                            text: "Check anything you'd like to change as part of this rest."
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
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    Item { Layout.fillWidth: true }
                    MButton { text: "Skip"; primary: false; onClicked: root.close() }
                    MButton { text: "Confirm " + (root.restType === "long" ? "Long Rest" : "Short Rest"); onClicked: root.confirmPreview() }
                }
            }

            // ── Page 1: short-rest hit-dice-to-spend prompt ─────────
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === 1
                spacing: 14

                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: Theme.text2
                    font.pixelSize: Theme.fsBody
                    text: "HP: " + sheetBridge.currentHp + "/" + sheetBridge.maxHp +
                          "   |   Hit dice remaining: " + sheetBridge.hitDiceAvailableForRest +
                          "\nHow many hit dice do you want to spend? (each heals 1 die + CON modifier)"
                }
                MSpinBox {
                    id: hitDiceSpin
                    objectName: "hitDiceSpin"
                    Layout.fillWidth: true
                    from: 0
                }
                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    MButton { text: "Skip"; primary: false; onClicked: root.applyCoreRest(0) }
                    MButton { text: "Confirm"; onClicked: root.applyCoreRest(hitDiceSpin.value) }
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
