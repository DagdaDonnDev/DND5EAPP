import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// The Features screen: the same sections and cards as desktop's Features
// tab (core/feature_page.py) -- race by character level, background,
// feats with where each came from, the DM's gifts by kind, then each class
// down its levels. A card opens in place to everything it says and the
// picks it holds; the chips keep to one section; the box finds a feature
// by anything in it. Then the Wild Magic surge tables and the DM's browser.
Page {
    id: root
    readonly property string screenTitle: "Features"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    property string featureSearch: ""
    property string chip: "All"
    property var openCards: ({})          // card id -> true: the cards left open
    property bool dmOpen: false
    readonly property bool dmShown: !searching && chip === "All"
    readonly property bool searching: featureSearch.trim().length > 0
    readonly property var chips: {
        var out = ["All"], all = sheetBridge.featuresSections
        for (var i = 0; i < all.length; i++)
            if (out.indexOf(all[i].chip) < 0)
                out.push(all[i].chip)
        return out
    }
    function cardFound(card) {
        var words = root.featureSearch.toLowerCase().split(/\s+/)
        for (var i = 0; i < words.length; i++)
            if (words[i].length > 0 && card.find.indexOf(words[i]) < 0)
                return false
        return true
    }
    function sectionCards(section) {
        if (!section.rail)
            return section.cards
        var out = []
        for (var i = 0; i < section.levels.length; i++)
            out = out.concat(section.levels[i].cards)
        return out
    }
    function foundIn(cards) {
        var n = 0
        for (var i = 0; i < cards.length; i++)
            if (cardFound(cards[i]))
                n++
        return n
    }
    function sectionShown(section) {
        return (root.chip === "All" || root.chip === section.chip) && foundIn(sectionCards(section)) > 0
    }
    readonly property int featuresFound: {
        var n = 0, all = sheetBridge.featuresSections
        for (var i = 0; i < all.length; i++) {
            if (root.chip !== "All" && root.chip !== all[i].chip)
                continue
            var cards = sectionCards(all[i])
            for (var j = 0; j < cards.length; j++)
                if (!cards[j].future && cardFound(cards[j]))
                    n++
        }
        return n
    }
    function toggleCard(id) {
        var o = Object.assign({}, root.openCards)
        if (o[id]) delete o[id]; else o[id] = true
        root.openCards = o
    }
    function tagColor(kind) {
        return kind === "uses" ? Theme.teal2 : kind === "action" ? Theme.amber : Theme.gold2
    }

    // One feature: name and tags, a line of what it does, and -- tapped
    // open -- the whole text and the picks under it
    component FeatureCard: Rectangle {
        id: fc
        property var card
        readonly property bool more: card.text.length > 0 || card.options.length > 0
        readonly property bool opened: more && !!root.openCards[card.id]
        objectName: "featureCard_" + card.name
        visible: root.cardFound(card)
        Layout.fillWidth: true
        implicitHeight: cardCol.implicitHeight + 20
        radius: 10
        color: opened ? Qt.tint(Theme.surf, Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.07))
                      : (cardTap.pressed ? Theme.surf2 : Theme.surf)
        border.color: opened ? Theme.gold : Theme.border
        opacity: card.future ? 0.55 : 1

        MouseArea {
            id: cardTap
            objectName: "featureTap_" + fc.card.name
            anchors.fill: parent
            enabled: fc.more
            onClicked: root.toggleCard(fc.card.id)
        }
        ColumnLayout {
            id: cardCol
            x: 12; y: 10
            width: parent.width - 24
            spacing: 4
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Label {
                    text: fc.more ? (fc.opened ? "▾" : "▸") : ""
                    color: Theme.text2
                    font.pixelSize: Theme.fsSmall
                    Layout.preferredWidth: 12
                    Layout.alignment: Qt.AlignTop
                }
                Label {
                    text: fc.card.name
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
            // the tags wrap under the name on a narrow screen
            Flow {
                visible: fc.card.tags.length > 0
                Layout.fillWidth: true
                Layout.leftMargin: 18
                spacing: 6
                Repeater {
                    model: fc.card.tags
                    delegate: Rectangle {
                        readonly property color c: root.tagColor(modelData.kind)
                        objectName: "featureTag_" + modelData.kind
                        width: tagText.implicitWidth + 14
                        height: tagText.implicitHeight + 6
                        radius: 5
                        color: Qt.rgba(c.r, c.g, c.b, 0.12)
                        border.color: Qt.rgba(c.r, c.g, c.b, 0.55)
                        Label {
                            id: tagText
                            anchors.centerIn: parent
                            text: modelData.text
                            color: parent.c
                            font.pixelSize: Theme.fsSmall - 1
                            font.bold: true
                        }
                    }
                }
            }
            Label {
                visible: fc.card.summary.length > 0
                text: fc.card.summary
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                Layout.leftMargin: 18
            }
            Label {
                objectName: "featureText"
                visible: fc.opened && fc.card.text.length > 0
                text: fc.card.text
                textFormat: Text.StyledText
                color: Theme.text
                font.pixelSize: Theme.fsBody
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                Layout.leftMargin: 18
                Layout.topMargin: 4
            }
            Repeater {
                model: fc.opened ? fc.card.options : []
                delegate: Rectangle {
                    objectName: "featureOption_" + modelData.name
                    Layout.fillWidth: true
                    Layout.leftMargin: 18
                    implicitHeight: optCol.implicitHeight + 12
                    radius: 6
                    color: Theme.surf2
                    border.color: Theme.border
                    Rectangle { width: 3; height: parent.height; radius: 2; color: Theme.gold2 }
                    ColumnLayout {
                        id: optCol
                        x: 12; y: 6
                        width: parent.width - 20
                        spacing: 2
                        Label { text: modelData.name; color: Theme.gold2; font.pixelSize: Theme.fsSmall; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        Label { visible: modelData.text.length > 0; text: modelData.text; textFormat: Text.StyledText; color: Theme.text2; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }
            }
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
            spacing: 10

            SheetHeader {}

            Label {
                visible: sheetBridge.featuresSections.length === 0
                text: "No features recorded."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
            }

            MTextField {
                objectName: "featureFilter"
                visible: sheetBridge.featuresSections.length > 0
                Layout.fillWidth: true
                placeholderText: "Find a feature…"
                onTextChanged: root.featureSearch = text
            }
            Flow {
                objectName: "featureChips"
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: root.chips
                    delegate: Rectangle {
                        readonly property bool on: root.chip === modelData
                        objectName: "featureChip_" + modelData
                        width: chipText.implicitWidth + 26
                        height: 34
                        radius: 17
                        color: on ? Theme.gold : Theme.surf2
                        border.color: on ? Theme.gold : Theme.border
                        Label {
                            id: chipText
                            anchors.centerIn: parent
                            text: modelData
                            color: parent.on ? Theme.onFill(Theme.gold) : Theme.text2
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                        }
                        MouseArea { anchors.fill: parent; onClicked: root.chip = modelData }
                    }
                }
            }
            Label {
                objectName: "featureHint"
                visible: sheetBridge.featuresSections.length > 0
                text: root.searching
                      ? (root.featuresFound === 0
                         ? "No feature matches “" + root.featureSearch.trim() + "”."
                         : root.featuresFound + " found")
                      : "Tap a feature to read it all."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Repeater {
                model: sheetBridge.featuresSections
                delegate: ColumnLayout {
                    id: featureSection
                    property var section: modelData
                    property bool folded: false
                    objectName: "featureSection_" + modelData.key
                    visible: root.sectionShown(modelData)
                    Layout.fillWidth: true
                    spacing: 8

                    // ▾ NAME  the line beside it  (count) ———
                    Item {
                        Layout.fillWidth: true
                        Layout.topMargin: 8
                        implicitHeight: Math.max(36, headRow.implicitHeight)
                        RowLayout {
                            id: headRow
                            anchors.fill: parent
                            spacing: 8
                            Label { text: featureSection.folded ? "▸" : "▾"; color: Theme.gold; font.pixelSize: Theme.fsSmall }
                            Label { text: featureSection.section.title.toUpperCase(); color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; font.letterSpacing: 1 }
                            Label {
                                text: featureSection.section.sub + "  (" + featureSection.section.count + ")"
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                        MouseArea {
                            objectName: "featureSectionHead_" + featureSection.section.key
                            anchors.fill: parent
                            onClicked: featureSection.folded = !featureSection.folded
                        }
                    }

                    // a section without levels: its cards
                    Repeater {
                        model: (!featureSection.folded && !featureSection.section.rail) ? featureSection.section.cards : []
                        delegate: FeatureCard { card: modelData }
                    }
                    // a timeline: each level's number down the left, its cards beside it
                    Repeater {
                        model: (!featureSection.folded && featureSection.section.rail) ? featureSection.section.levels : []
                        delegate: RowLayout {
                            id: levelRow
                            property var row: modelData
                            objectName: "featureLevel_" + modelData.level
                            visible: root.foundIn(modelData.cards) > 0
                            Layout.fillWidth: true
                            spacing: 10
                            Item {
                                Layout.preferredWidth: 34
                                Layout.fillHeight: true
                                Rectangle {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    y: 36; width: 2; height: parent.height - 36
                                    color: Theme.border
                                }
                                Rectangle {
                                    id: dot
                                    readonly property bool now: levelRow.row.state === "now"
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    y: 4
                                    width: 30; height: 30; radius: 15
                                    color: now ? Theme.indigo : Theme.surf2
                                    border.width: 2
                                    border.color: now ? Theme.indigo2 : Theme.border2
                                    opacity: levelRow.row.state === "next" ? 0.55 : 1
                                    Label {
                                        anchors.centerIn: parent
                                        text: levelRow.row.level
                                        color: dot.now ? Theme.onFill(Theme.indigo) : Theme.indigo2
                                        font.pixelSize: Theme.fsSmall
                                        font.bold: true
                                    }
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                Label {
                                    visible: levelRow.row.label.length > 0
                                    text: levelRow.row.label.toUpperCase()
                                    color: levelRow.row.state === "now" ? Theme.indigo2 : Theme.text3
                                    font.pixelSize: Theme.fsSmall - 1
                                    font.bold: true
                                    font.letterSpacing: 1
                                    Layout.topMargin: 6
                                }
                                Repeater {
                                    model: levelRow.row.cards
                                    delegate: FeatureCard { card: modelData }
                                }
                                Item { implicitHeight: 4 }
                            }
                        }
                    }
                }
            }

            // ── Wild Magic Surge Table (Barbarian d8 / Sorcerer d100) ───
            // Pure "roll and show the effect" mechanic, matching desktop:
            // the roll doesn't mutate character state, it's on the player
            // to apply whatever the table says by hand.
            Repeater {
                objectName: "wildMagicTablesRepeater"
                model: sheetBridge.wildMagicTables
                delegate: ColumnLayout {
                    id: wmCard
                    // (the blocks that aren't features step aside while
                    // one's being looked for)
                    visible: !root.searching && (root.chip === "All" || root.chip === (modelData.barb ? "Barbarian" : "Sorcerer"))
                    Layout.fillWidth: true
                    spacing: 8
                    property var lastResult: null

                    Label {
                        text: modelData.title
                        color: Theme.indigo2
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        Layout.topMargin: 6
                    }
                    MButton {
                        objectName: "wildMagicRollBtn_" + (modelData.barb ? "barb" : "sorc")
                        text: modelData.dieLabel
                        primary: false
                        Layout.alignment: Qt.AlignLeft
                        onClicked: {
                            var res = sheetBridge.rollWildMagicSurge(modelData.barb)
                            wmCard.lastResult = res
                            wmRowsList.positionViewAtIndex(res.rowIndex, ListView.Contain)
                        }
                    }
                    Label {
                        text: wmCard.lastResult ? ("Roll " + wmCard.lastResult.roll + ": " + wmCard.lastResult.effect) : "—"
                        color: Theme.indigo2
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 220
                        radius: 10
                        color: Theme.surf
                        border.color: Theme.border
                        clip: true

                        ListView {
                            id: wmRowsList
                            objectName: "wildMagicRowsListView_" + (modelData.barb ? "barb" : "sorc")
                            anchors.fill: parent
                            anchors.margins: 4
                            clip: true
                            model: modelData.rows
                            delegate: Rectangle {
                                width: ListView.view.width
                                height: rowEffectLabel.implicitHeight + 12
                                radius: 4
                                color: (wmCard.lastResult && wmCard.lastResult.rowIndex === index) ? Theme.indigo : "transparent"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    spacing: 8
                                    Label {
                                        text: modelData.lo === modelData.hi ? String(modelData.lo) : (modelData.lo + "–" + modelData.hi)
                                        color: Theme.text2
                                        font.pixelSize: Theme.fsSmall
                                        font.bold: true
                                        Layout.preferredWidth: 44
                                    }
                                    Label {
                                        id: rowEffectLabel
                                        text: modelData.effect
                                        color: Theme.text
                                        font.pixelSize: Theme.fsSmall
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── Bonus Feature Browser (DM Rewards + feat grants) ────────
            // Grants a feat or DM Reward ("Character Secret", "Dark
            // Gift", etc.) outside normal class progression -- desktop's
            // Features tab equivalent card.
            // ▸ FROM THE DM: folded until it's wanted
            Item {
                visible: root.dmShown
                Layout.fillWidth: true
                Layout.topMargin: 8
                implicitHeight: 36
                RowLayout {
                    anchors.fill: parent
                    spacing: 8
                    Label { text: root.dmOpen ? "\u25be" : "\u25b8"; color: Theme.gold; font.pixelSize: Theme.fsSmall }
                    Label { text: "FROM THE DM"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; font.letterSpacing: 1 }
                    Label { text: "give a feat, a gift or a secret"; color: Theme.text2; font.pixelSize: Theme.fsSmall; elide: Text.ElideRight; Layout.fillWidth: true }
                }
                MouseArea { objectName: "dmBrowserHead"; anchors.fill: parent; onClicked: root.dmOpen = !root.dmOpen }
            }
            Label {
                visible: root.dmShown && root.dmOpen
                text: "A feat, a gift or a secret the DM hands out, outside the levels. Tap the magnifying glass to read one."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                visible: root.dmShown && root.dmOpen
                Layout.fillWidth: true
                spacing: 8
                MTextField {
                    id: dmSearch
                    objectName: "dmSearchField"
                    Layout.fillWidth: true
                    placeholderText: "Search feats / DM rewards…"
                    onTextChanged: dmModel.refreshResults()
                }
                // the type filter lives in the drawer behind this
                MFilterButton {
                    objectName: "dmFilterButton"
                    count: dmFilters.activeCount
                    onClicked: dmFilters.open()
                }
            }
            MFilterDrawer {
                id: dmFilters
                objectName: "dmFilterDrawer"
                title: "Feature filters"
                activeCount: dmCategory.currentIndex > 0 ? 1 : 0
                onCleared: dmCategory.currentIndex = 0
                Label { text: "Feature type"; color: Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true }
                ComboBox {
                    id: dmCategory
                    objectName: "dmCategoryCombo"
                    Layout.fillWidth: true
                    model: sheetBridge.dmRewardCategories
                    onCurrentIndexChanged: dmModel.refreshResults()
                }
            }

            QtObject {
                id: dmModel
                property var results: sheetBridge.searchDmRewardBrowser("", "All Types")
                function refreshResults() {
                    results = sheetBridge.searchDmRewardBrowser(dmSearch.text, dmCategory.model[dmCategory.currentIndex])
                }
            }
            Connections {
                target: sheetBridge
                function onStatsChanged() { dmModel.refreshResults() }
            }

            Rectangle {
                visible: root.dmShown && root.dmOpen
                Layout.fillWidth: true
                Layout.preferredHeight: 300
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                clip: true

                ListView {
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    model: dmModel.results
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 56
                        color: "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 8
                            // fixed-width icon slot on every row, so names and
                            // buttons line up whether or not a row has an icon
                            Item {
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                                MIcon {
                                    anchors.centerIn: parent
                                    visible: modelData.itemType === "dm_reward"
                                    name: "orb"
                                    size: 18
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    text: modelData.name
                                    color: modelData.granted ? Theme.amber : Theme.text
                                    font.pixelSize: Theme.fsBody
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: modelData.category + (modelData.source ? "  ·  " + modelData.source : "")
                                    color: Theme.text3
                                    font.pixelSize: Theme.fsSmall
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                            MButton {
                                primary: false
                                height: 32
                                Layout.preferredWidth: 40
                                iconName: "search"   // View -- a magnifying glass
                                iconSize: 22
                                Accessible.name: "View"
                                onClicked: {
                                    Window.window.pendingDmRewardDetail = modelData
                                    dmDetail.open()
                                }
                            }
                            MButton {
                                height: 32
                                Layout.preferredWidth: 84
                                primary: !modelData.granted
                                text: modelData.granted ? "Revoke" : "Grant"
                                // No extra explicit refresh here -- the
                                // Connections block above already
                                // refreshes dmModel on statsChanged
                                // (same reasoning as the equipment/spell
                                // browsers' add lists).
                                onClicked: {
                                    if (modelData.granted)
                                        sheetBridge.revokeDmBrowserItem(modelData.name, modelData.itemType)
                                    else
                                        sheetBridge.grantDmBrowserItem(modelData.name, modelData.itemType)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Same MFullPageDialog scope-chain workaround as the Spells screen's
    // spell-detail popup -- reached via Window.window rather than any
    // bare/scope-chain lookup.
    property var dmRewardData: Window.window.pendingDmRewardDetail

    MFullPageDialog {
        id: dmDetail
        objectName: "dmRewardDetailDialog"
        dialogTitle: (root.dmRewardData && root.dmRewardData.name) || "Detail"

        Flickable {
            anchors.fill: parent
            anchors.margins: 16
            contentWidth: width
            contentHeight: dmDetailCol.height
            clip: true

            ColumnLayout {
                id: dmDetailCol
                width: parent.width
                spacing: 8

                Label {
                    text: (root.dmRewardData.category || "") + (root.dmRewardData.source ? "  ·  " + root.dmRewardData.source : "")
                    color: Theme.gold2
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                }
                Label {
                    visible: !!root.dmRewardData.prereq
                    text: "Requires: " + (root.dmRewardData.prereq || "")
                    color: Theme.amber
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
                Label {
                    text: root.dmRewardData.desc || ""
                    color: Theme.text
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
