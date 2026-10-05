import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Combined Choices + Level Up destination: one nav entry, two tabs,
// sharing a single SheetHeader. "Choices" (the default tab) holds
// Identity/Experience editing, every unresolved level-up-time decision
// (ASI/Feat, Subclass picks, generic pool choices, and the TCE/TCoE
// Versatility optional-rule swaps), and a read-only history of choices
// already made -- mirrors ui_desktop's Choices tab. "Level Up" holds
// only the class-level actions (multiclass in/level up/level down/
// remove) -- those aren't "a choice" the way picking a feat or fighting
// style is, and having level buttons that could reorder under a
// player's finger as pending choices appeared alongside them made both
// harder to use, so they're kept on their own tab rather than mixed in.
Page {
    id: root
    readonly property string screenTitle: "Choices"
    // Lets App.qml's menu-button pulse stop once the player is here.
    readonly property bool isChoicesScreen: true
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        SheetHeader {}

        TabBar {
            id: topTabBar
            objectName: "choicesLevelUpTabBar"
            Layout.fillWidth: true
            TabButton {
                objectName: "choicesTab"
                text: "Choices"
                // Pulses while choices are pending and the player is on
                // the Level Up tab -- leveling up there is exactly what
                // creates new choices, and this points them back.
                MPulseDot {
                    objectName: "choicesTabPulse"
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: 10
                    running: !!Window.window && Window.window.choicesPending && topTabBar.currentIndex !== 0
                }
            }
            TabButton { objectName: "levelUpTab"; text: "Level Up" }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // ── Tab 0: Choices ──────────────────────────────────────
            Flickable {
                anchors.fill: parent
                visible: topTabBar.currentIndex === 0
                contentWidth: width
                contentHeight: choicesContent.height
                clip: true

                ColumnLayout {
                    id: choicesContent
                    width: parent.width
                    spacing: 16

                    // ── Identity ──────────────────────────────────────────────
                    Label { text: "Identity"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: idCol.height + 20
                        radius: 10
                        color: Theme.surf
                        border.color: Theme.border

                        ColumnLayout {
                            id: idCol
                            x: 12; y: 10
                            width: parent.width - 24
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: "Race"; color: Theme.text2; font.pixelSize: Theme.fsSmall; Layout.preferredWidth: 90 }
                                Label { Layout.fillWidth: true; text: sheetBridge.identityRace; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true }
                                MButton { primary: false; height: 32; text: "Change"; onClicked: raceDialog.open() }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                visible: sheetBridge.hasSubraces
                                Label { text: "Subrace"; color: Theme.text2; font.pixelSize: Theme.fsSmall; Layout.preferredWidth: 90 }
                                Label { Layout.fillWidth: true; text: sheetBridge.identitySubrace || "(none)"; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true }
                                MButton { primary: false; height: 32; text: "Change"; onClicked: subraceDialog.open() }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                visible: sheetBridge.isDragonborn
                                Label { text: "Ancestry"; color: Theme.text2; font.pixelSize: Theme.fsSmall; Layout.preferredWidth: 90 }
                                Label { Layout.fillWidth: true; text: sheetBridge.identityAncestry || "(none)"; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true }
                                MButton { primary: false; height: 32; text: "Change"; onClicked: ancestryDialog.open() }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: "Background"; color: Theme.text2; font.pixelSize: Theme.fsSmall; Layout.preferredWidth: 90 }
                                Label { Layout.fillWidth: true; text: sheetBridge.identityBackground; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true }
                                MButton { primary: false; height: 32; text: "Change"; onClicked: backgroundDialog.open() }
                            }
                        }
                    }

                    // ── Experience ────────────────────────────────────────────
                    Label { text: "Experience"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.topMargin: 6 }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: xpCol.height + 20
                        radius: 10
                        color: Theme.surf
                        border.color: Theme.border

                        ColumnLayout {
                            id: xpCol
                            x: 12; y: 10
                            width: parent.width - 24
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: "Leveling mode: " + (sheetBridge.xpLevelingMode ? "Experience Points" : "Milestone")
                                    color: Theme.text2
                                    font.pixelSize: Theme.fsSmall
                                    Layout.fillWidth: true
                                }
                                Switch {
                                    checked: sheetBridge.xpLevelingMode
                                    onToggled: sheetBridge.setXpLevelingMode(checked)
                                }
                            }

                            ColumnLayout {
                                visible: sheetBridge.xpLevelingMode
                                Layout.fillWidth: true
                                spacing: 6

                                Label {
                                    text: sheetBridge.xpProgress.xp + " XP  (" + sheetBridge.xpProgress.pct + "% to next level)"
                                    color: Theme.gold2
                                    font.pixelSize: Theme.fsBody
                                    font.bold: true
                                }
                                Label {
                                    visible: sheetBridge.xpProgress.eligible
                                    text: "Ready to level up ×" + sheetBridge.xpProgress.levelsDue + "!"
                                    color: Theme.teal2
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                                Flow {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Label {
                                        text: "Add XP:"
                                        color: Theme.text2
                                        font.pixelSize: Theme.fsSmall
                                        height: xpAddSpin.height
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    MSpinBox {
                                        id: xpAddSpin
                                        width: 130
                                        from: 0
                                        to: 999999
                                        stepSize: 50
                                        value: 0
                                    }
                                    MButton {
                                        primary: false
                                        height: 32
                                        text: "+ Add"
                                        onClicked: { sheetBridge.addXp(xpAddSpin.value); xpAddSpin.value = 0 }
                                    }
                                    MButton {
                                        primary: false
                                        height: 32
                                        text: "Set Total…"
                                        onClicked: { setXpSpin.value = sheetBridge.xpProgress.xp; setXpDialog.open() }
                                    }
                                }
                            }
                        }
                    }

                    // ── Pending: ASI or Feat ──────────────────────────────────
                    Label {
                        visible: sheetBridge.pendingAsiOrFeatChoices.length > 0
                        text: "Pending Choices"
                        color: Theme.gold
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        Layout.topMargin: 6
                    }
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
                                                            Layout.alignment: Qt.AlignVCenter
                                                            height: 28
                                                            primary: false
                                                            text: "View"
                                                            onClicked: {
                                                                Window.window.pendingFeatDetail = modelData
                                                                featDetailDialog.open()
                                                            }
                                                        }
                                                        MButton {
                                                            Layout.alignment: Qt.AlignVCenter
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

                    // ── Versatility (TCE/TCoE optional-rule swaps) ─────────────
                    // Unlike the pending-choice cards above (fill a slot once),
                    // these stay available any time the character has reached
                    // the relevant class's ASI level and the optional rule is on
                    // -- see versatilityOptions' docstring in the bridge. Each
                    // sub-card only appears when its own key is present. Every
                    // swap requires picking both sides, then a Confirm tap --
                    // never applies immediately on the first tap, so an
                    // accidental tap (or one aimed at a button whose text
                    // overflowed into a neighboring one) can be corrected before
                    // it does anything.
                    readonly property var versatility: sheetBridge.versatilityOptions
                    Label {
                        visible: Object.keys(choicesContent.versatility).length > 0
                        text: "Versatility (Optional Rules)"
                        color: Theme.gold
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        Layout.topMargin: 6
                    }

                    // Pact Boon (Eldritch Versatility)
                    Rectangle {
                        id: pbCard
                        objectName: "versatilityPactBoonCard"
                        visible: !!choicesContent.versatility.pactBoon
                        readonly property var pb: choicesContent.versatility.pactBoon || ({})
                        property string newSel: ""
                        onPbChanged: newSel = ""
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
                                        primary: modelData === pbCard.newSel
                                        text: modelData.split(" (")[0]
                                        onClicked: pbCard.newSel = modelData
                                    }
                                }
                            }
                            MButton {
                                text: "Confirm Swap"
                                enabled: pbCard.newSel.length > 0
                                onClicked: {
                                    sheetBridge.applyPactBoonVersatility(pbCard.newSel)
                                    pbCard.newSel = ""
                                }
                            }
                        }
                    }

                    // Mystic Arcanum (Eldritch Versatility)
                    Repeater {
                        objectName: "versatilityArcanumRepeater"
                        model: (choicesContent.versatility.arcanum || {}).units || []
                        delegate: Rectangle {
                            id: arcUnitCard
                            readonly property int spellLevel: modelData.spellLevel
                            readonly property string oldName: modelData.old
                            readonly property var newPool: modelData.pool
                            property string newSel: ""
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
                                            primary: modelData === arcUnitCard.newSel
                                            text: modelData
                                            onClicked: arcUnitCard.newSel = modelData
                                        }
                                    }
                                }
                                MButton {
                                    text: "Confirm Swap"
                                    enabled: arcUnitCard.newSel.length > 0
                                    onClicked: {
                                        sheetBridge.applyArcanumVersatility(
                                            arcUnitCard.spellLevel, arcUnitCard.oldName, arcUnitCard.newSel)
                                        arcUnitCard.newSel = ""
                                    }
                                }
                            }
                        }
                    }

                    // Fighting Style (Martial Versatility)
                    Rectangle {
                        id: fsCard
                        objectName: "versatilityFightingStyleCard"
                        visible: !!choicesContent.versatility.fightingStyle
                        readonly property var fs: choicesContent.versatility.fightingStyle || ({})
                        property string oldSel: fs.current && fs.current.length ? fs.current[0] : ""
                        property string newSel: ""
                        onFsChanged: { oldSel = fs.current && fs.current.length ? fs.current[0] : ""; newSel = "" }
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
                                        primary: modelData === fsCard.newSel
                                        // .split(" (")[0]: these pool entries carry
                                        // a full mechanical description in
                                        // parentheses (e.g. "Protection (impose
                                        // disadvantage on attack vs adjacent ally,
                                        // requires shield)") -- showing the whole
                                        // string overflowed clean off the button.
                                        text: modelData.split(" (")[0]
                                        onClicked: fsCard.newSel = modelData
                                    }
                                }
                            }
                            MButton {
                                text: "Confirm Swap"
                                enabled: fsCard.newSel.length > 0
                                onClicked: {
                                    sheetBridge.applyFightingStyleVersatility(fsCard.oldSel, fsCard.newSel)
                                    fsCard.newSel = ""
                                }
                            }
                        }
                    }

                    // Battle Master Maneuver (Martial Versatility)
                    Rectangle {
                        id: manCard
                        objectName: "versatilityManeuverCard"
                        visible: !!choicesContent.versatility.maneuver
                        readonly property var man: choicesContent.versatility.maneuver || ({})
                        property string oldSel: man.current && man.current.length ? man.current[0] : ""
                        property string newSel: ""
                        onManChanged: { oldSel = man.current && man.current.length ? man.current[0] : ""; newSel = "" }
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
                                        primary: modelData === manCard.newSel
                                        text: modelData.split(" – ")[0]
                                        onClicked: manCard.newSel = modelData
                                    }
                                }
                            }
                            MButton {
                                text: "Confirm Swap"
                                enabled: manCard.newSel.length > 0
                                onClicked: {
                                    sheetBridge.applyManeuverVersatility(manCard.oldSel, manCard.newSel)
                                    manCard.newSel = ""
                                }
                            }
                        }
                    }

                    // Expertise (Bardic Versatility)
                    Rectangle {
                        id: expCard
                        objectName: "versatilityExpertiseCard"
                        visible: !!choicesContent.versatility.expertise
                        readonly property var exp: choicesContent.versatility.expertise || ({})
                        property string oldSel: exp.from && exp.from.length ? exp.from[0] : ""
                        property string newSel: ""
                        onExpChanged: { oldSel = exp.from && exp.from.length ? exp.from[0] : ""; newSel = "" }
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
                                        primary: modelData === expCard.newSel
                                        text: modelData
                                        onClicked: expCard.newSel = modelData
                                    }
                                }
                            }
                            MButton {
                                text: "Confirm Swap"
                                enabled: expCard.newSel.length > 0
                                onClicked: {
                                    sheetBridge.applyExpertiseVersatility(expCard.oldSel, expCard.newSel)
                                    expCard.newSel = ""
                                }
                            }
                        }
                    }

                    // Metamagic (Sorcerous Versatility)
                    Rectangle {
                        id: mmCard
                        objectName: "versatilityMetamagicCard"
                        visible: !!choicesContent.versatility.metamagic
                        readonly property var mm: choicesContent.versatility.metamagic || ({})
                        property string oldSel: mm.current && mm.current.length ? mm.current[0] : ""
                        property string newSel: ""
                        onMmChanged: { oldSel = mm.current && mm.current.length ? mm.current[0] : ""; newSel = "" }
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
                                        primary: modelData === mmCard.newSel
                                        text: modelData.split(" – ")[0]
                                        onClicked: mmCard.newSel = modelData
                                    }
                                }
                            }
                            MButton {
                                text: "Confirm Swap"
                                enabled: mmCard.newSel.length > 0
                                onClicked: {
                                    sheetBridge.applyMetamagicVersatility(mmCard.oldSel, mmCard.newSel)
                                    mmCard.newSel = ""
                                }
                            }
                        }
                    }

                    Label {
                        text: "Other choices made during character creation and leveling up:"
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        Layout.topMargin: 6
                    }

                    Label {
                        visible: sheetBridge.choicesList.length === 0
                        text: "No recorded choices."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }

                    Repeater {
                        model: sheetBridge.choicesList
                        delegate: Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: choiceCol.height + 16
                            radius: 10
                            color: Theme.surf
                            border.color: Theme.border

                            Column {
                                id: choiceCol
                                x: 10; y: 8
                                width: parent.width - 20
                                spacing: 2
                                Label {
                                    text: modelData.key
                                    color: Theme.gold
                                    font.pixelSize: Theme.fsSmall
                                    font.bold: true
                                }
                                Label {
                                    text: modelData.value
                                    color: Theme.text
                                    font.pixelSize: Theme.fsSmall
                                    wrapMode: Text.WordWrap
                                    width: parent.width
                                }
                            }
                        }
                    }
                }
            }

            // ── Tab 1: Level Up ──────────────────────────────────────
            Flickable {
                anchors.fill: parent
                visible: topTabBar.currentIndex === 1
                contentWidth: width
                contentHeight: levelUpContent.height
                clip: true

                ColumnLayout {
                    id: levelUpContent
                    width: parent.width
                    spacing: 16

                    Label { text: "Level Up a Class"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
                    Label {
                        visible: sheetBridge.hasPendingChoices
                        text: "You have pending choices from a previous level-up -- see the Choices tab."
                        color: Theme.teal2
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Repeater {
                        objectName: "levelUpClassRepeater"
                        model: sheetBridge.levelUpClassOptions
                        delegate: Rectangle {
                            id: clsRow
                            readonly property string clsName: modelData.name
                            Layout.fillWidth: true
                            Layout.preferredHeight: clsCol.height + 20
                            radius: 10
                            color: Theme.surf
                            border.color: Theme.border

                            ColumnLayout {
                                id: clsCol
                                x: 12; y: 10
                                width: parent.width - 24
                                spacing: 6

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
                                // A wrapping Flow, not a fixed RowLayout -- three
                                // buttons plus a class name can't reliably fit
                                // one row on a narrow phone screen, and letting
                                // them wrap beats squeezing/clipping them.
                                Flow {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    MButton {
                                        text: "Level Down"
                                        primary: false
                                        height: 36
                                        visible: !modelData.isNew
                                        enabled: modelData.currentLevel > 1
                                        onClicked: sheetBridge.levelDownClass(clsRow.clsName)
                                    }
                                    MButton {
                                        text: "Remove"
                                        primary: false
                                        height: 36
                                        visible: !modelData.isNew && sheetBridge.canRemoveClass
                                        onClicked: sheetBridge.removeClass(clsRow.clsName)
                                    }
                                    MButton {
                                        text: modelData.isNew ? "Multiclass In" : "Level Up"
                                        height: 36
                                        onClicked: sheetBridge.levelUpClass(modelData.name)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    MPickerDialog {
        id: raceDialog
        dialogTitle: "Change Race"
        options: sheetBridge.raceNames
        onPicked: (value) => sheetBridge.changeRace(value)
    }
    MPickerDialog {
        id: subraceDialog
        dialogTitle: "Choose Subrace"
        options: sheetBridge.subraceOptions
        onPicked: (value) => sheetBridge.changeSubrace(value)
    }
    MPickerDialog {
        id: ancestryDialog
        dialogTitle: "Draconic Ancestry"
        options: sheetBridge.ancestryOptions
        onPicked: (value) => sheetBridge.changeAncestry(value)
    }
    MPickerDialog {
        id: backgroundDialog
        dialogTitle: "Change Background"
        options: sheetBridge.backgroundNames
        onPicked: (value) => {
            sheetBridge.changeBackground(value)
            let featChoices = sheetBridge.backgroundFeatChoices(value)
            if (featChoices.length > 0) {
                backgroundFeatDialog.options = featChoices
                backgroundFeatDialog.open()
            }
        }
    }
    MPickerDialog {
        id: backgroundFeatDialog
        dialogTitle: "This background grants a choice of feat -- which one?"
        onPicked: (value) => sheetBridge.applyBackgroundFeatChoice(value)
    }

    Popup {
        id: setXpDialog
        modal: true
        focus: true
        width: 280
        anchors.centerIn: parent
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        // Matches MFullPageDialog.qml's dimming -- the default modal
        // overlay is a much lighter wash than this app's dark theme calls for.
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            Label { text: "Set Total XP"; color: Theme.gold; font.pixelSize: Theme.fsBody; font.bold: true }
            MSpinBox {
                id: setXpSpin
                Layout.fillWidth: true
                from: 0
                to: 999999999
                stepSize: 100
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    text: "Cancel"
                    primary: false
                    Layout.fillWidth: true
                    onClicked: setXpDialog.close()
                }
                MButton {
                    text: "Set"
                    Layout.fillWidth: true
                    onClicked: {
                        sheetBridge.setTotalXp(setXpSpin.value)
                        setXpDialog.close()
                    }
                }
            }
        }
    }

    // Same MFullPageDialog scope-chain workaround as the Features
    // screen's DM Reward detail popup and the Spells screen's spell-
    // detail popup -- reached via Window.window rather than any bare/
    // scope-chain lookup.
    property var featDetailData: Window.window.pendingFeatDetail

    MFullPageDialog {
        id: featDetailDialog
        objectName: "featLevelUpDetailDialog"
        dialogTitle: (root.featDetailData && root.featDetailData.name) || "Detail"

        Flickable {
            anchors.fill: parent
            anchors.margins: 16
            contentWidth: width
            contentHeight: featDetailCol.height
            clip: true

            ColumnLayout {
                id: featDetailCol
                width: parent.width
                spacing: 8

                Label {
                    visible: !!root.featDetailData.source
                    text: root.featDetailData.source || ""
                    color: Theme.gold2
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                }
                Label {
                    visible: !!root.featDetailData.prereq
                    text: "Requires: " + (root.featDetailData.prereq || "")
                    color: Theme.amber
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
                Label {
                    text: root.featDetailData.desc || ""
                    color: Theme.text
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
