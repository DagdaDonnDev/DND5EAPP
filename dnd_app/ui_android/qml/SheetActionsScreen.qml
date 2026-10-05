import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Ports ui_desktop's Combat-tab Action/Bonus Action/Reaction/Passive
// cards (action_abilities.py's build_action_abilities(), reused
// directly -- it's pure data logic with no Qt dependency) plus the
// generic resource pool tracker (char["resources"]: ki points, rage
// uses, Second Wind, etc.). Resource *tracking* only -- the handful of
// desktop abilities with an extra mechanical effect on use (Second
// Wind's heal roll, Rage's active_effects toggle, Action Surge's
// turn-economy flag) aren't reproduced yet.
Page {
    id: root
    readonly property string screenTitle: "Actions"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject sheetBridge: Window.window.sheetBridge

    Component.onCompleted: sheetBridge.refresh()

    // Jump-to-section targets for the drawer's expandable sub-menu (see
    // NavDrawer.qml's sectionSelected) -- looked up by name rather than
    // a fixed index since each bucket's ColumnLayout only exists when
    // that character actually has abilities in it.
    function scrollToSection(name) {
        var anchorItem = null
        if (name === "Resources") {
            anchorItem = resourcesAnchor
        } else {
            for (var i = 0; i < bucketRepeater.count; i++) {
                var it = bucketRepeater.itemAt(i)
                if (it && it.bucketName === name) { anchorItem = it; break }
            }
        }
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

            // ── Resources ────────────────────────────────────────────
            Label {
                id: resourcesAnchor
                visible: sheetBridge.resources.length > 0
                text: "Resources"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            Repeater {
                model: sheetBridge.resources
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: resCol.height + 20
                    radius: 10
                    color: Theme.surf
                    border.color: Theme.border

                    ColumnLayout {
                        id: resCol
                        x: 10; y: 10
                        width: parent.width - 20
                        spacing: 6

                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: modelData.name
                                    color: Theme.text
                                    font.pixelSize: Theme.fsBody
                                    font.bold: true
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: modelData.sourceClass + (modelData.reset ? "  ·  " + modelData.reset : "")
                                    color: Theme.text3
                                    font.pixelSize: Theme.fsSmall
                                }
                            }
                            Label {
                                text: modelData.unlimited ? "∞" : (modelData.current + " / " + modelData.currentMax)
                                color: Theme.teal2
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                            }
                        }
                        Flow {
                            visible: !modelData.unlimited
                            Layout.fillWidth: true
                            spacing: 8
                            MButton {
                                primary: false
                                height: 32
                                text: "Use"
                                enabled: modelData.current > 0
                                onClicked: sheetBridge.spendResource(modelData.key)
                            }
                            MButton {
                                primary: false
                                height: 32
                                text: "Restore"
                                onClicked: sheetBridge.restoreResource(modelData.key)
                            }
                            MToggleButton {
                                visible: modelData.toggleEffect.length > 0
                                active: modelData.toggleActive
                                onClicked: sheetBridge.toggleResourceEffect(modelData.key)
                            }
                        }
                    }
                }
            }

            // ── Action economy buckets ───────────────────────────────
            Repeater {
                id: bucketRepeater
                model: sheetBridge.actionAbilities
                delegate: ColumnLayout {
                    // Captured for scrollToSection() to match against by
                    // name via itemAt() -- a bare .children() walk isn't
                    // reliable for Repeater-generated delegates.
                    readonly property string bucketName: modelData.bucket
                    Layout.fillWidth: true
                    spacing: 10

                    Label {
                        text: modelData.bucket
                        color: Theme.gold
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        Layout.topMargin: 6
                    }

                    Repeater {
                        model: modelData.items
                        delegate: Rectangle {
                            id: actCard
                            // Spent this turn (turn tracker) -> greyed, same as
                            // desktop's _apply_turn_state on its Use/Cast buttons.
                            readonly property bool bucketSpent: {
                                var tc = sheetBridge.turnCounts
                                if (modelData.bucketKey === "Action") return tc.action >= tc.actionLimit
                                if (modelData.bucketKey === "Bonus Action") return tc.bonusAction >= tc.bonusActionLimit
                                if (modelData.bucketKey === "Reaction") return tc.reaction >= tc.reactionLimit
                                return false
                            }
                            Layout.fillWidth: true
                            Layout.preferredHeight: cardRow.implicitHeight + 20
                            radius: 10
                            color: Theme.surf
                            border.color: Theme.border

                            RowLayout {
                                id: cardRow
                                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 10 }
                                spacing: 10

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 3
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        MIcon {
                                            visible: modelData.isSpell && modelData.pinned
                                            name: "star_solid"
                                            size: 14
                                        }
                                        Label {
                                            text: modelData.name
                                            color: Theme.text
                                            font.pixelSize: Theme.fsBody
                                            font.bold: true
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                        Label {
                                            text: modelData.source
                                            color: Theme.text3
                                            font.pixelSize: Theme.fsSmall
                                        }
                                    }
                                    Label {
                                        text: modelData.desc
                                        color: Theme.text2
                                        font.pixelSize: Theme.fsSmall
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                        maximumLineCount: 4
                                        elide: Text.ElideRight
                                    }
                                }

                                // Cast for spells, Use for everything else (not
                                // for passive features -- there's nothing to do)
                                MButton {
                                    objectName: "useButton_" + modelData.name
                                    visible: modelData.bucketKey !== "Passive"
                                    Layout.alignment: Qt.AlignVCenter
                                    implicitWidth: 72
                                    implicitHeight: 36
                                    primary: modelData.isSpell
                                    enabled: !actCard.bucketSpent
                                    text: modelData.isSpell ? "Cast" : "Use"
                                    onClicked: modelData.isSpell
                                               ? sheetBridge.castSpell(modelData.spellName)
                                               : sheetBridge.useAbility(modelData.bucketKey, modelData.name, modelData.desc)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
