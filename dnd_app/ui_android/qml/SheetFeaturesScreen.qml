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

            Repeater {
                model: sheetBridge.featuresSections
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: modelData.title
                        color: Theme.gold
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        Layout.topMargin: 6
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Repeater {
                        model: modelData.items
                        delegate: Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: itemLabel.implicitHeight + 16
                            radius: 8
                            color: Theme.surf
                            border.color: Theme.border

                            Label {
                                id: itemLabel
                                x: 10; y: 8
                                width: parent.width - 20
                                text: modelData
                                color: Theme.text
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
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
            Label { text: "Bonus Feature Browser -- DM Rewards"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.topMargin: 6 }
            Label {
                text: "Grant a feat or DM-awarded bonus feature outside normal class progression. Tap View for details."
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MTextField {
                    id: dmSearch
                    objectName: "dmSearchField"
                    Layout.fillWidth: true
                    placeholderText: "Search feats / DM rewards…"
                    onTextChanged: dmModel.refreshResults()
                }
                ComboBox {
                    id: dmCategory
                    objectName: "dmCategoryCombo"
                    Layout.preferredWidth: 150
                    model: sheetBridge.dmRewardCategories
                    onCurrentIndexChanged: dmModel.refreshResults()
                }
            }

            QtObject {
                id: dmModel
                property var results: sheetBridge.searchDmRewardBrowser("", "All Types")
                function refreshResults() {
                    results = sheetBridge.searchDmRewardBrowser(dmSearch.text, dmCategory.currentText)
                }
            }
            Connections {
                target: sheetBridge
                function onStatsChanged() { dmModel.refreshResults() }
            }

            Rectangle {
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
                            MIcon {
                                visible: modelData.itemType === "dm_reward"
                                name: "orb"
                                size: 18
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    text: modelData.name
                                    color: modelData.granted ? Theme.amber : Theme.text
                                    font.pixelSize: Theme.fsBody
                                    elide: Text.ElideRight
                                }
                                Label {
                                    text: modelData.category + (modelData.source ? "  ·  " + modelData.source : "")
                                    color: Theme.text3
                                    font.pixelSize: Theme.fsSmall
                                }
                            }
                            MButton {
                                primary: false
                                height: 32
                                text: "View"
                                onClicked: {
                                    Window.window.pendingDmRewardDetail = modelData
                                    dmDetail.open()
                                }
                            }
                            MButton {
                                height: 32
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
