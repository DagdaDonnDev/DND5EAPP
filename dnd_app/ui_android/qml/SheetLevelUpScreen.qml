import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// First slice of ui_desktop's level-up flow (levelup_multiclass.py +
// levelup_panel.py, ~3700 lines combined) -- see
// CharacterSheetBridge's Level-up section docstring for what's not
// ported yet (optional/alternate class features, and the free-
// choice-from-full-list types: Infusions beyond the existing tab,
// Metamagic, Invocations, Magical Secrets). Race-specific choices,
// class tool proficiency choices, and DM rewards ARE ported here.
Page {
    id: root
    readonly property string screenTitle: "Level Up"
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

            Label { text: "Level Up a Class"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            Repeater {
                model: sheetBridge.levelUpClassOptions
                delegate: Rectangle {
                    Layout.fillWidth: true
                    // MButton's background implicitHeight is 48 -- this
                    // card must be tall enough for that plus the
                    // RowLayout's margins, or the button overflows past
                    // the Rectangle's (unclipped) bottom edge and visibly
                    // renders on top of the card below it.
                    Layout.preferredHeight: 68
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.border
                    clip: true

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                text: modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                            }
                            Label {
                                text: modelData.isNew ? "New class (multiclass)" : "Currently level " + modelData.currentLevel
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                        }
                        MButton {
                            text: modelData.isNew ? "Multiclass In" : "Level Up"
                            onClicked: sheetBridge.levelUpClass(modelData.name)
                        }
                    }
                }
            }

            // ── Pending: ASI or Feat ──────────────────────────────────
            Repeater {
                objectName: "pendingAsiOrFeatRepeater"
                model: sheetBridge.pendingAsiOrFeatChoices
                delegate: Rectangle {
                    id: asiCard
                    // Captured before the nested Repeaters below shadow
                    // the outer modelData with their own.
                    readonly property string choiceId: modelData.id
                    property var asiAlloc: ({})
                    readonly property int asiTotal: {
                        var t = 0
                        for (var k in asiAlloc) t += asiAlloc[k]
                        return t
                    }

                    Layout.fillWidth: true
                    Layout.preferredHeight: asiCol.height + 20
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.amber

                    ColumnLayout {
                        id: asiCol
                        x: 12; y: 10
                        width: parent.width - 24
                        spacing: 8

                        Label {
                            text: modelData.label
                            color: Theme.amber
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        TabBar {
                            id: asiModeTab
                            objectName: "asiModeTab"
                            Layout.fillWidth: true
                            TabButton { text: "Ability Score" }
                            TabButton { text: "Feat" }
                        }

                        ColumnLayout {
                            visible: asiModeTab.currentIndex === 0
                            Layout.fillWidth: true
                            spacing: 6
                            Label {
                                text: "Pick one ability to +2, or two abilities to +1 each."
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Flow {
                                Layout.fillWidth: true
                                spacing: 8
                                Repeater {
                                    model: ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
                                    delegate: ColumnLayout {
                                        spacing: 2
                                        Label {
                                            text: modelData
                                            color: Theme.text2
                                            font.pixelSize: Theme.fsSmall
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                        RowLayout {
                                            spacing: 2
                                            ToolButton {
                                                text: "−"
                                                implicitWidth: 32
                                                onClicked: {
                                                    var v = asiCard.asiAlloc[modelData] || 0
                                                    if (v > 0) {
                                                        asiCard.asiAlloc[modelData] = v - 1
                                                        asiCard.asiAllocChanged()
                                                    }
                                                }
                                            }
                                            Label {
                                                text: String(asiCard.asiAlloc[modelData] || 0)
                                                color: Theme.teal2
                                                font.bold: true
                                                font.pixelSize: Theme.fsBody
                                                horizontalAlignment: Text.AlignHCenter
                                                Layout.preferredWidth: 20
                                            }
                                            ToolButton {
                                                text: "+"
                                                implicitWidth: 32
                                                enabled: asiCard.asiTotal < 2 && (asiCard.asiAlloc[modelData] || 0) < 2
                                                onClicked: {
                                                    asiCard.asiAlloc[modelData] = (asiCard.asiAlloc[modelData] || 0) + 1
                                                    asiCard.asiAllocChanged()
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            MButton {
                                text: "Confirm Ability Increase"
                                enabled: asiCard.asiTotal === 2
                                onClicked: {
                                    sheetBridge.applyAsiLevelUpChoice(asiCard.choiceId, asiCard.asiAlloc)
                                    asiCard.asiAlloc = ({})
                                }
                            }
                        }

                        ColumnLayout {
                            visible: asiModeTab.currentIndex === 1
                            Layout.fillWidth: true
                            spacing: 6
                            MTextField {
                                id: featSearch
                                Layout.fillWidth: true
                                placeholderText: "Search feats…"
                                onTextChanged: featModel.refreshResults()
                            }
                            QtObject {
                                id: featModel
                                property var results: sheetBridge.searchFeatsForLevelUp("")
                                function refreshResults() {
                                    results = sheetBridge.searchFeatsForLevelUp(featSearch.text)
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 160
                                radius: 8
                                color: Theme.surf2
                                border.color: Theme.border
                                clip: true
                                ListView {
                                    objectName: "featLevelUpListView"
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    clip: true
                                    model: featModel.results
                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: modelData.metPrereq ? 44 : 60
                                        color: "transparent"
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 0
                                            RowLayout {
                                                Layout.fillWidth: true
                                                Label {
                                                    text: modelData.name
                                                    color: modelData.metPrereq ? Theme.text : Theme.text3
                                                    font.pixelSize: Theme.fsBody
                                                    Layout.fillWidth: true
                                                    elide: Text.ElideRight
                                                }
                                                MButton {
                                                    height: 28
                                                    text: "Pick"
                                                    enabled: modelData.metPrereq
                                                    opacity: enabled ? 1.0 : 0.5
                                                    onClicked: sheetBridge.applyFeatLevelUpChoice(asiCard.choiceId, modelData.name)
                                                }
                                            }
                                            // Only shown for a feat this character doesn't
                                            // qualify for yet -- matches desktop's greyed-out
                                            // list item + "Requires: X" tooltip, just always
                                            // visible here instead of hover-only.
                                            Label {
                                                visible: !modelData.metPrereq
                                                text: "Requires: " + modelData.prereq
                                                color: Theme.text3
                                                font.pixelSize: Theme.fsSmall
                                                Layout.fillWidth: true
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── Pending: Subclass ─────────────────────────────────────
            Repeater {
                model: sheetBridge.pendingSubclassChoices
                delegate: Rectangle {
                    id: subCard
                    readonly property string choiceId: modelData.id
                    readonly property var poolData: modelData.pool

                    Layout.fillWidth: true
                    Layout.preferredHeight: subCol.height + 20
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.indigo2

                    ColumnLayout {
                        id: subCol
                        x: 12; y: 10
                        width: parent.width - 24
                        spacing: 8

                        Label {
                            text: modelData.label
                            color: Theme.indigo2
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 8
                            Repeater {
                                model: subCard.poolData
                                delegate: MButton {
                                    primary: false
                                    text: modelData
                                    onClicked: sheetBridge.applySubclassLevelUpChoice(subCard.choiceId, modelData)
                                }
                            }
                        }
                    }
                }
            }

            // ── Pending: generic pool-based choices ───────────────────
            // Every count (including 1) requires a tap-to-select-then-
            // Confirm step, never a submit-on-first-tap -- these pools
            // scroll (a 2-column grid, sometimes dozens of entries, e.g.
            // 95 languages), and a single accidental tap while scrolling
            // must not silently lock in a choice the player didn't mean
            // to make. Taps accumulate into newSelections (toggle to
            // select/deselect; for count 1, selecting a different option
            // replaces the previous one rather than requiring a
            // deselect first), and Confirm submits alreadyChosen +
            // newSelections together -- matching desktop's ChoiceWidget,
            // which seeds self._selected from already_chosen and sends
            // the full list on confirm. modelData.count's exact meaning
            // (a flat per-choice total vs. a total already net of
            // already_chosen) is inconsistent across the different
            // choice-generating functions upstream, so the enable
            // condition matches desktop's own ChoiceWidget exactly
            // (alreadyChosen.length + newSelections.length >= count)
            // rather than guessing which meaning applies -- this is
            // correct for the common case and, for the rare choice
            // where already_chosen alone already meets a "remaining"-
            // style count, inherits desktop's own existing behavior of
            // letting Confirm enable with no new picks (harmless: the
            // resubmit is a no-op since nothing new was selected).
            Repeater {
                model: sheetBridge.pendingLevelUpChoices
                delegate: Rectangle {
                    id: genCard
                    readonly property string choiceId: modelData.id
                    property var poolData: modelData.pool
                    property int wantCount: modelData.count
                    property var alreadyChosen: modelData.alreadyChosen
                    property var newSelections: []
                    readonly property int haveTotal: alreadyChosen.length + newSelections.length

                    function toggleNew(item) {
                        var sel = newSelections.slice()
                        var idx = sel.indexOf(item)
                        if (idx >= 0) {
                            sel.splice(idx, 1)
                        } else if (wantCount === 1) {
                            // Single-select: picking a different option
                            // swaps it in rather than requiring the old
                            // one to be tapped off first.
                            sel = [item]
                        } else if (haveTotal < wantCount) {
                            sel.push(item)
                        }
                        newSelections = sel
                    }

                    Layout.fillWidth: true
                    Layout.preferredHeight: genCol.height + 20
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.teal2

                    ColumnLayout {
                        id: genCol
                        x: 12; y: 10
                        width: parent.width - 24
                        spacing: 8

                        Label {
                            text: modelData.label + " (choose " + modelData.count + ")"
                            color: Theme.teal2
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            visible: genCard.alreadyChosen.length > 0
                            text: "Already chosen: " + genCard.alreadyChosen.join(", ")
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        // A 2-column scrollable grid rather than a Flow --
                        // a Flow's ragged wrapping (each row only as wide
                        // as its own button text) looks uneven and grows
                        // the card without bound for a large pool (e.g.
                        // 95 languages); a fixed-height, evenly-split
                        // 2-column grid stays clean and scrolls instead.
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(320, poolGrid.height + 12)
                            radius: 8
                            color: Theme.surf2
                            border.color: Theme.border
                            clip: true
                            Flickable {
                                anchors.fill: parent
                                anchors.margins: 6
                                contentWidth: width
                                contentHeight: poolGrid.height
                                clip: true
                                GridLayout {
                                    id: poolGrid
                                    width: parent.width
                                    columns: 2
                                    columnSpacing: 8
                                    rowSpacing: 8
                                    Repeater {
                                        model: genCard.poolData
                                        delegate: MButton {
                                            Layout.fillWidth: true
                                            primary: genCard.newSelections.indexOf(modelData) >= 0
                                            text: modelData
                                            onClicked: genCard.toggleNew(modelData)
                                        }
                                    }
                                }
                            }
                        }
                        MButton {
                            text: "Confirm (" + genCard.haveTotal + "/" + genCard.wantCount + " selected)"
                            enabled: genCard.haveTotal >= genCard.wantCount
                            onClicked: {
                                sheetBridge.applyLevelUpChoice(
                                    genCard.choiceId, genCard.alreadyChosen.concat(genCard.newSelections))
                                genCard.newSelections = []
                            }
                        }
                    }
                }
            }

            Label {
                visible: sheetBridge.pendingAsiOrFeatChoices.length === 0
                         && sheetBridge.pendingSubclassChoices.length === 0
                         && sheetBridge.pendingLevelUpChoices.length === 0
                text: "No pending level-up choices."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
            }

            // ── Versatility (TCE/TCoE optional-rule swaps) ─────────────
            // Unlike the pending-choice cards above (fill a slot once),
            // these stay available any time the character has reached
            // the relevant class's ASI level and the optional rule is on
            // -- see versatilityOptions' docstring in the bridge. Each
            // sub-card only appears when its own key is present.
            readonly property var versatility: sheetBridge.versatilityOptions
            Label {
                visible: Object.keys(content.versatility).length > 0
                text: "Versatility (Optional Rules)"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }

            // Pact Boon (Eldritch Versatility)
            Rectangle {
                id: pbCard
                objectName: "versatilityPactBoonCard"
                visible: !!content.versatility.pactBoon
                readonly property var pb: content.versatility.pactBoon || ({})
                Layout.fillWidth: true
                Layout.preferredHeight: pbCol.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.purple2
                ColumnLayout {
                    id: pbCol
                    x: 12; y: 10
                    width: parent.width - 24
                    spacing: 6
                    Label {
                        text: "Eldritch Versatility: Replace Pact Boon"
                        color: Theme.purple2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "Current: " + (pbCard.pb.current || "")
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: pbCard.pb.pool || []
                            delegate: MButton {
                                primary: false
                                text: modelData
                                onClicked: sheetBridge.applyPactBoonVersatility(modelData)
                            }
                        }
                    }
                }
            }

            // Mystic Arcanum (Eldritch Versatility)
            Repeater {
                objectName: "versatilityArcanumRepeater"
                model: (content.versatility.arcanum || {}).units || []
                delegate: Rectangle {
                    id: arcUnitCard
                    readonly property int spellLevel: modelData.spellLevel
                    readonly property string oldName: modelData.old
                    readonly property var newPool: modelData.pool
                    Layout.fillWidth: true
                    Layout.preferredHeight: arcCol.height + 20
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.purple2
                    ColumnLayout {
                        id: arcCol
                        x: 12; y: 10
                        width: parent.width - 24
                        spacing: 6
                        Label {
                            text: "Eldritch Versatility: Replace Mystic Arcanum (Lv" + arcUnitCard.spellLevel + ")"
                            color: Theme.purple2
                            font.pixelSize: Theme.fsBody
                            font.bold: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: "Current: " + arcUnitCard.oldName
                            color: Theme.text3
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 8
                            Repeater {
                                model: arcUnitCard.newPool
                                delegate: MButton {
                                    primary: false
                                    text: modelData
                                    onClicked: sheetBridge.applyArcanumVersatility(
                                        arcUnitCard.spellLevel, arcUnitCard.oldName, modelData)
                                }
                            }
                        }
                    }
                }
            }

            // Fighting Style (Martial Versatility)
            Rectangle {
                id: fsCard
                objectName: "versatilityFightingStyleCard"
                visible: !!content.versatility.fightingStyle
                readonly property var fs: content.versatility.fightingStyle || ({})
                property string oldSel: fs.current && fs.current.length ? fs.current[0] : ""
                onFsChanged: oldSel = fs.current && fs.current.length ? fs.current[0] : ""
                Layout.fillWidth: true
                Layout.preferredHeight: fsCol.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.teal2
                ColumnLayout {
                    id: fsCol
                    x: 12; y: 10
                    width: parent.width - 24
                    spacing: 6
                    Label {
                        text: "Martial Versatility: Replace a Fighting Style"
                        color: Theme.teal2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "Replacing:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: fsCard.fs.current || []
                            delegate: MButton {
                                primary: modelData === fsCard.oldSel
                                text: modelData.split(" (")[0]
                                onClicked: fsCard.oldSel = modelData
                            }
                        }
                    }
                    Label {
                        text: "With:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: fsCard.fs.pool || []
                            delegate: MButton {
                                primary: false
                                text: modelData
                                onClicked: sheetBridge.applyFightingStyleVersatility(fsCard.oldSel, modelData)
                            }
                        }
                    }
                }
            }

            // Battle Master Maneuver (Martial Versatility)
            Rectangle {
                id: manCard
                objectName: "versatilityManeuverCard"
                visible: !!content.versatility.maneuver
                readonly property var man: content.versatility.maneuver || ({})
                property string oldSel: man.current && man.current.length ? man.current[0] : ""
                onManChanged: oldSel = man.current && man.current.length ? man.current[0] : ""
                Layout.fillWidth: true
                Layout.preferredHeight: manCol.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.teal2
                ColumnLayout {
                    id: manCol
                    x: 12; y: 10
                    width: parent.width - 24
                    spacing: 6
                    Label {
                        text: "Martial Versatility: Replace a Maneuver"
                        color: Theme.teal2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "Replacing:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: manCard.man.current || []
                            delegate: MButton {
                                primary: modelData === manCard.oldSel
                                text: modelData.split(" – ")[0]
                                onClicked: manCard.oldSel = modelData
                            }
                        }
                    }
                    Label {
                        text: "With:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: manCard.man.pool || []
                            delegate: MButton {
                                primary: false
                                text: modelData.split(" – ")[0]
                                onClicked: sheetBridge.applyManeuverVersatility(manCard.oldSel, modelData)
                            }
                        }
                    }
                }
            }

            // Expertise (Bardic Versatility)
            Rectangle {
                id: expCard
                objectName: "versatilityExpertiseCard"
                visible: !!content.versatility.expertise
                readonly property var exp: content.versatility.expertise || ({})
                property string oldSel: exp.from && exp.from.length ? exp.from[0] : ""
                onExpChanged: oldSel = exp.from && exp.from.length ? exp.from[0] : ""
                Layout.fillWidth: true
                Layout.preferredHeight: expCol.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.crimson2
                ColumnLayout {
                    id: expCol
                    x: 12; y: 10
                    width: parent.width - 24
                    spacing: 6
                    Label {
                        text: "Bardic Versatility: Move Expertise"
                        color: Theme.crimson2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "From:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: expCard.exp.from || []
                            delegate: MButton {
                                primary: modelData === expCard.oldSel
                                text: modelData
                                onClicked: expCard.oldSel = modelData
                            }
                        }
                    }
                    Label {
                        text: "To:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: expCard.exp.to || []
                            delegate: MButton {
                                primary: false
                                text: modelData
                                onClicked: sheetBridge.applyExpertiseVersatility(expCard.oldSel, modelData)
                            }
                        }
                    }
                }
            }

            // Metamagic (Sorcerous Versatility)
            Rectangle {
                id: mmCard
                objectName: "versatilityMetamagicCard"
                visible: !!content.versatility.metamagic
                readonly property var mm: content.versatility.metamagic || ({})
                property string oldSel: mm.current && mm.current.length ? mm.current[0] : ""
                onMmChanged: oldSel = mm.current && mm.current.length ? mm.current[0] : ""
                Layout.fillWidth: true
                Layout.preferredHeight: mmCol.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.purple2
                ColumnLayout {
                    id: mmCol
                    x: 12; y: 10
                    width: parent.width - 24
                    spacing: 6
                    Label {
                        text: "Sorcerous Versatility: Replace a Metamagic option"
                        color: Theme.purple2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "Replacing:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: mmCard.mm.current || []
                            delegate: MButton {
                                primary: modelData === mmCard.oldSel
                                text: modelData.split(" – ")[0]
                                onClicked: mmCard.oldSel = modelData
                            }
                        }
                    }
                    Label {
                        text: "With:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: mmCard.mm.pool || []
                            delegate: MButton {
                                primary: false
                                text: modelData.split(" – ")[0]
                                onClicked: sheetBridge.applyMetamagicVersatility(mmCard.oldSel, modelData)
                            }
                        }
                    }
                }
            }
        }
    }
}
