import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// The app's one navigation surface: an expandable (slide-in/out) left
// drawer listing every top-level screen. `items` are the step screens
// (Race/Abilities/.../Character Sheet), navigated to via the
// StackView. `utilityItems` are app-level destinations (Settings,
// Save/Load, Dice Roller, Credits) that AREN'T part of the character-
// creation step sequence -- each one opens as a full-page modal
// dialog on top of whatever step screen is currently showing, rather
// than replacing it, so closing one (its X, or the phone's back
// button) returns to exactly where you were. Laid out as a 2x2 tile
// grid in its own bottom section rather than the step list's vertical
// rows, both to set it visually apart and because it reads better at
// exactly 4 items than a tall list would. Each entry supplies its own
// `onOpen` callback (see App.qml) instead of going through
// `itemSelected`, since opening a dialog has nothing to do with the
// StackView.
Drawer {
    id: root
    objectName: "navDrawer"
    width: Math.min(0.85 * (parent ? parent.width : 320), 340)
    edge: Qt.LeftEdge
    modal: true

    property var items: []
    property var utilityItems: []
    signal itemSelected(var screen)
    // Emitted when a sub-section row (under an expanded nav item) is
    // tapped -- navigates the same as itemSelected, but also tells the
    // destination screen which of its own internal sections to scroll
    // to (see each Sheet*Screen.qml's scrollToSection()).
    signal sectionSelected(var screen, string sectionName)

    // Replaces Material's default Popup background (which draws its
    // own light-toned elevation border in dark theme -- the "white
    // outline" around the drawer) with a flat, borderless panel.
    background: Rectangle {
        color: Theme.surf
    }

    // Material's default modal dim is a light-toned scrim; this makes
    // the screen the drawer covers read as black at partial opacity
    // instead.
    Overlay.modal: Rectangle {
        color: Qt.rgba(0, 0, 0, 0.8)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 20
        anchors.bottomMargin: 12
        spacing: 0

        Label {
            text: "MIMIC"
            color: Theme.gold2
            font.pixelSize: Theme.fsTitle
            font.bold: true
            Layout.leftMargin: 20
            Layout.bottomMargin: 12
        }

        // ── Home / Refresh / Short Rest / Long Rest, all one row ──────
        // Home and Refresh are single-unit icon buttons; Short Rest and
        // Long Rest are double-width (they carry text, not just a
        // glyph) -- six units total split 1:1:2:2 across the row.
        RowLayout {
            id: actionRow
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 12
            spacing: 8

            // Based on the Drawer's own width (root.width), not this
            // RowLayout's -- binding a child's preferredWidth back to
            // this row's own width creates a circular layout
            // dependency (the row can't size itself until its
            // children are sized, which need the row's size first).
            readonly property real unit: (root.width - 24 - spacing * 3) / 6

            ToolButton {
                objectName: "drawerHomeButton"
                Layout.preferredWidth: actionRow.unit
                // Drawn line icons (MIcon) rather than text glyphs or
                // emoji: they never depend on the device's font stack,
                // and follow the theme's accent colour.
                contentItem: Item {
                    MIcon { anchors.centerIn: parent; name: "home"; size: 22 }
                }
                onClicked: Window.window.requestGoToStartMenu()
            }
            MButton {
                Layout.preferredWidth: actionRow.unit * 2
                primary: false
                text: "Short Rest"
                onClicked: {
                    // Start the rest flow BEFORE closing the drawer, not
                    // after -- closing this Popup first left the new
                    // RestFlowDialog's open() call with no visible
                    // effect (confirmed via real-tap testing), some
                    // interaction between two Popups transitioning at
                    // once in this offscreen harness.
                    Window.window.startRest("short")
                    root.close()
                }
            }
            MButton {
                Layout.preferredWidth: actionRow.unit * 2
                primary: false
                text: "Long Rest"
                onClicked: {
                    Window.window.startRest("long")
                    root.close()
                }
            }
            ToolButton {
                objectName: "drawerRefreshButton"
                Layout.preferredWidth: actionRow.unit
                contentItem: Item {
                    MIcon { anchors.centerIn: parent; name: "refresh"; size: 21 }
                }
                onClicked: Window.window.sheetBridge.refresh()
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }

        // ── Main step navigation ──────────────────────────────────────
        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: mainCol.height
            clip: true

            Column {
                id: mainCol
                width: parent.width

                Repeater {
                    model: root.items
                    delegate: Column {
                        id: navRow
                        width: mainCol.width
                        // Captured before the inner Repeater below (over
                        // itemSections, plain section-name strings)
                        // shadows this outer modelData with its own.
                        readonly property var itemScreen: modelData.screen
                        readonly property var itemSections: modelData.sections || []
                        readonly property bool hasSections: itemSections.length > 0
                        property bool expanded: false

                        // An item with `pulse: true` (Choices, while level-up
                        // choices are pending) gets a breathing accent bar on
                        // its left edge, a faint accent tint and a pulsing dot
                        // after its label. The tint stays faint: a stronger
                        // fill turns grey on light themes whose accent is the
                        // complement of their background (Arcane Scroll's
                        // navy over parchment).
                        Item {
                            id: rowBox
                            width: parent.width
                            height: 48   // Android's minimum recommended touch-target size
                            property real glow: 0
                            SequentialAnimation on glow {
                                running: !!modelData.pulse
                                loops: Animation.Infinite
                                NumberAnimation { from: 0.0; to: 1.0; duration: 700; easing.type: Easing.InOutSine }
                                NumberAnimation { from: 1.0; to: 0.0; duration: 700; easing.type: Easing.InOutSine }
                            }

                            Rectangle {
                                anchors.fill: parent
                                color: Theme.indigo
                                visible: !!modelData.pulse
                                opacity: 0.10 * rowBox.glow
                            }
                            Rectangle {
                                width: 4
                                height: parent.height
                                color: Theme.indigo2
                                visible: !!modelData.pulse
                                opacity: 0.35 + 0.65 * rowBox.glow
                            }

                            RowLayout {
                                anchors.fill: parent
                                spacing: 0

                                ItemDelegate {
                                    objectName: "navItem_" + modelData.label
                                    text: modelData.label
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    enabled: modelData.enabled
                                    opacity: enabled ? 1.0 : 0.4
                                    contentItem: RowLayout {
                                        spacing: 8
                                        Label {
                                            text: modelData.enabled ? modelData.label : modelData.label + "  (finish previous step)"
                                            color: modelData.pulse ? Theme.indigo2 : Theme.text
                                            font.pixelSize: Theme.fsBody
                                            font.bold: !!modelData.pulse
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 20
                                        }
                                        MPulseDot {
                                            objectName: "navPulse_" + modelData.label
                                            running: !!modelData.pulse
                                        }
                                        Item { Layout.fillWidth: true }
                                    }
                                    onClicked: root.itemSelected(navRow.itemScreen)
                                }
                                // A separate clickable target (not the same
                                // ItemDelegate) so tapping the row itself
                                // still just navigates -- only tapping this
                                // chevron expands/collapses the sub-list.
                                ToolButton {
                                    objectName: "navExpand_" + modelData.label
                                    visible: navRow.hasSections
                                    Layout.preferredWidth: 40
                                    Layout.fillHeight: true
                                    onClicked: navRow.expanded = !navRow.expanded

                                    // Drawn instead of "▸"/"▾" text glyphs
                                    // (U+25B8/U+25BE, Geometric Shapes block)
                                    // -- not guaranteed present in every
                                    // Android device's font stack, same
                                    // reasoning as App.qml's hamburger
                                    // button. A right-pointing chevron built
                                    // from two crossed bars, rotated 90°
                                    // when expanded to point down instead --
                                    // never depends on any font.
                                    contentItem: Item {
                                        anchors.centerIn: parent
                                        width: 12
                                        height: 12
                                        rotation: navRow.expanded ? 90 : 0
                                        Rectangle {
                                            width: 7; height: 2; radius: 1
                                            color: Theme.text2
                                            anchors.right: parent.right
                                            anchors.verticalCenter: parent.verticalCenter
                                            transformOrigin: Item.Right
                                            rotation: 45
                                        }
                                        Rectangle {
                                            width: 7; height: 2; radius: 1
                                            color: Theme.text2
                                            anchors.right: parent.right
                                            anchors.verticalCenter: parent.verticalCenter
                                            transformOrigin: Item.Right
                                            rotation: -45
                                        }
                                    }
                                }
                            }
                        }

                        Column {
                            width: parent.width
                            visible: navRow.hasSections && navRow.expanded
                            Repeater {
                                model: navRow.itemSections
                                delegate: ItemDelegate {
                                    objectName: "navSection_" + modelData
                                    width: mainCol.width
                                    height: 40
                                    contentItem: Label {
                                        text: modelData
                                        color: Theme.text2
                                        font.pixelSize: Theme.fsSmall
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 44
                                    }
                                    onClicked: root.sectionSelected(navRow.itemScreen, modelData)
                                }
                            }
                        }
                    }
                }
            }
        }

        // ── Utility destinations (Settings, Save/Load, Dice Roller,
        // Credits) as a 2x2 tile grid ──────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border; visible: root.utilityItems.length > 0 }

        GridLayout {
            Layout.fillWidth: true
            Layout.margins: 12
            columns: 2
            rowSpacing: 10
            columnSpacing: 10

            Repeater {
                model: root.utilityItems
                delegate: ItemDelegate {
                    objectName: "utilityTile_" + modelData.label
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    enabled: modelData.enabled
                    opacity: enabled ? 1.0 : 0.4
                    background: Rectangle {
                        radius: 10
                        color: Theme.surf2
                        border.color: Theme.border
                    }
                    contentItem: Column {
                        anchors.centerIn: parent
                        spacing: 2
                        MIcon {
                            name: modelData.icon
                            size: 22
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        Label {
                            text: modelData.enabled ? modelData.label : modelData.label + " (soon)"
                            color: Theme.text
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                            wrapMode: Text.WordWrap
                            horizontalAlignment: Text.AlignHCenter
                            width: 130
                        }
                    }
                    onClicked: {
                        modelData.onOpen()
                        root.close()
                    }
                }
            }
        }
    }
}
