import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// View of ui_desktop's Features tab (features.py's _rebuild_features):
// race/subrace traits, background feature, per-class level-by-level
// features, feats, fighting styles, Blood Hunter curses/mutagens,
// Elemental Disciplines, Replicated Magic Items, and optional/
// alternate class features (TCoE) -- plus (below) the interactive
// Wild Magic Surge roll table and the Bonus Feature Browser (DM
// Rewards + feat grants). Full parity with desktop's Features tab.
Page {
    id: root
    readonly property string screenTitle: "Features"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    // Find a feature: every word typed must be in the feature's name,
    // what it does, or its group's heading (the bridge's `find` text)
    property string featureSearch: ""
    function featureFound(row) {
        var words = root.featureSearch.toLowerCase().split(/\s+/)
        for (var i = 0; i < words.length; i++)
            if (words[i].length > 0 && row.find.indexOf(words[i]) < 0)
                return false
        return true
    }
    function foundIn(section) {
        var n = 0
        for (var i = 0; i < section.rows.length; i++)
            if (featureFound(section.rows[i]))
                n++
        return n
    }
    readonly property int featuresFound: {
        var n = 0, all = sheetBridge.featuresSections
        for (var i = 0; i < all.length; i++)
            n += foundIn(all[i])
        return n
    }
    readonly property bool searching: featureSearch.trim().length > 0

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
                placeholderText: "Find a feature\u2026"
                onTextChanged: root.featureSearch = text
            }
            Label {
                objectName: "featureHint"
                visible: sheetBridge.featuresSections.length > 0
                text: root.searching
                      ? (root.featuresFound === 0
                         ? "No feature matches \u201c" + root.featureSearch.trim() + "\u201d."
                         : root.featuresFound + " found")
                      : "Tap a feature with a magnifying glass to read what it does."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                Layout.topMargin: -8
            }

            Repeater {
                model: sheetBridge.featuresSections
                delegate: ColumnLayout {
                    id: featureSection
                    objectName: "featureSection_" + modelData.title
                    // a group with nothing found steps aside
                    visible: root.foundIn(modelData) > 0
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: modelData.title
                        color: Theme.gold
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        Layout.topMargin: 6
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Repeater {
                        model: modelData.rows
                        delegate: Rectangle {
                            id: featureRow
                            objectName: "featureRow_" + modelData.text
                            visible: root.featureFound(modelData)
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.max(itemLabel.implicitHeight + 16, modelData.more ? 44 : 0)
                            radius: 8
                            color: rowTap.pressed ? Theme.surf2 : Theme.surf
                            border.color: Theme.border

                            Label {
                                id: itemLabel
                                x: 10
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 20 - (modelData.more ? 26 : 0)
                                text: modelData.text
                                color: Theme.text
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                            }
                            // more to read: a magnifying glass, and the
                            // whole row opens it
                            MIcon {
                                visible: modelData.more
                                name: "search"
                                size: 17
                                color: Theme.text3
                                anchors.right: parent.right
                                anchors.rightMargin: 10
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            MouseArea {
                                id: rowTap
                                objectName: "featureTap_" + modelData.text
                                anchors.fill: parent
                                enabled: modelData.more
                                onClicked: sheetBridge.showFeatureDetail(modelData.text)
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
                    visible: !root.searching
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
            Label { visible: !root.searching; text: "Bonus Feature Browser -- DM Rewards"; color: Theme.gold; font.pixelSize: Theme.fsBody; font.bold: true; Layout.topMargin: 6 }
            Label {
                visible: !root.searching
                text: "Grant a feat or DM-awarded bonus feature outside normal class progression. Tap the magnifying glass for details."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                visible: !root.searching
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
                visible: !root.searching
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
