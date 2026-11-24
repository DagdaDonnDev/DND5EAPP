import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// A creature's card -- desktop's _build_statblock_card on Android, for
// mounts, vehicles, summons, companions and the Wild Shape preview: one
// slim header when closed (a coloured stripe, its name, what it is, and
// AC, HP and speed as chips); tap it for the whole stat block. Press and
// hold for its options: Set max HP, Move to, Remove.
Rectangle {
    id: root
    property string displayName: ""
    property string source: ""
    property string size: ""
    property string creatureType: ""
    property string ac: ""
    property var hp: ""
    property string hitDice: ""
    property string speed: ""
    property var abilities: []      // [{ability, score, mod}]
    property var saves: []          // [{name, bonus}]
    property var skills: []         // [{name, bonus}]
    property string damageResistances: ""
    property string damageImmunities: ""
    property string conditionImmunities: ""
    property string senses: ""
    property string languages: ""
    property var traits: []         // [{name, desc}]
    property var actions: []        // [{name, desc}]
    property var reactions: []      // [{name, desc}]
    property bool hasHpTracking: false
    property int currentHp: 0
    property int maxHp: 1
    property bool removable: false
    property bool startExpanded: false

    signal hpEdited(int value)
    signal removeClicked()      // (kept for older callers; press and hold now)
    signal held()               // press and hold: the card's options (Move to, Remove)

    property bool expanded: startExpanded

    // one more or one less HP, from the chip's + and −
    function stepHp(step) {
        var v = Math.max(0, Math.min(root.maxHp, hpField.value + step))
        if (v !== hpField.value) { hpField.value = v; root.hpEdited(v) }
    }

    Layout.fillWidth: true
    implicitHeight: col.height
    radius: 10
    color: Theme.surf
    border.color: Theme.border
    clip: true

    // the stripe down the left that marks a creature card
    Rectangle {
        width: 3; color: Theme.teal
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom; topMargin: 6; bottomMargin: 6 }
        radius: 1.5
    }

    component Step: MouseArea {
        property string glyph: ""
        property int step: 1
        implicitWidth: 36; implicitHeight: 34
        onClicked: {
            var v = Math.max(0, Math.min(root.maxHp, hpField.value + step))
            if (v !== hpField.value) { hpField.value = v; root.hpEdited(v) }
        }
        Rectangle {
            anchors.centerIn: parent; width: 26; height: 26; radius: 6
            color: parent.pressed ? Qt.rgba(Theme.green2.r, Theme.green2.g, Theme.green2.b, 0.25) : "transparent"
        }
        Label { anchors.centerIn: parent; text: parent.glyph; color: Theme.green2; font.bold: true; font.pixelSize: Theme.fsBody }
    }

    component Chip: Rectangle {
        property alias text: chipLabel.text
        property color tint: Theme.gold2
        radius: 6
        color: Qt.rgba(tint.r, tint.g, tint.b, 0.12)
        border.color: Qt.rgba(tint.r, tint.g, tint.b, 0.45)
        implicitWidth: chipLabel.implicitWidth + 16
        implicitHeight: 30
        Label { id: chipLabel; anchors.centerIn: parent; color: parent.tint; font.bold: true; font.pixelSize: Theme.fsSmall }
    }

    ColumnLayout {
        id: col
        width: parent.width
        spacing: 0

        MouseArea {
            id: header
            objectName: "creatureCardHeader"
            Layout.fillWidth: true
            Layout.preferredHeight: headerCol.height + 20
            cursorShape: Qt.PointingHandCursor
            pressAndHoldInterval: 450
            onClicked: root.expanded = !root.expanded
            onPressAndHold: if (root.removable || root.hasHpTracking) root.held()

            // name and what it is on the first line, AC, HP and speed on the
            // second -- a long name never pushes the numbers off the card
            ColumnLayout {
                id: headerCol
                x: 14; y: 10
                width: parent.width - 26
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    MIcon { name: root.expanded ? "chevron_down" : "chevron_right"; size: 14 }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            Layout.fillWidth: true
                            text: root.displayName; color: Theme.text; font.bold: true
                            font.pixelSize: Theme.fsBody; elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: [[root.size, root.creatureType].filter(function (x) { return x }).join(" "), root.source]
                                  .filter(function (x) { return x }).join(" · ")
                            color: Theme.text3; font.pixelSize: Theme.fsSmall
                            elide: Text.ElideRight
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 22
                    spacing: 8
                    Chip { text: "AC " + root.ac; tint: Theme.gold2 }
                    Rectangle {
                        visible: root.hasHpTracking
                        radius: 6
                        color: Qt.rgba(Theme.green2.r, Theme.green2.g, Theme.green2.b, 0.12)
                        border.color: Qt.rgba(Theme.green2.r, Theme.green2.g, Theme.green2.b, 0.45)
                        implicitWidth: hpRow.implicitWidth + 14
                        implicitHeight: hpRow.implicitHeight + 4
                        RowLayout {
                            id: hpRow
                            anchors.centerIn: parent
                            spacing: 0
                            Label { text: "HP"; color: Theme.green2; font.bold: true; font.pixelSize: Theme.fsSmall; rightPadding: 4 }
                            // the chip's own − and + with the number between
                            // them (typed into too): the stock spin box's
                            // boxes looked out of place in it
                            Step { objectName: "hpLess"; glyph: "−"; step: -1; Accessible.name: "1 less HP" }
                            TextField {
                                id: hpField
                                objectName: "hpField"
                                property int value: root.currentHp
                                text: String(value)
                                implicitWidth: Math.max(34, contentWidth + 10)
                                leftPadding: 0; rightPadding: 0
                                horizontalAlignment: Text.AlignHCenter
                                color: Theme.text
                                font.bold: true
                                font.pixelSize: Theme.fsBody
                                padding: 0
                                inputMethodHints: Qt.ImhDigitsOnly
                                validator: IntValidator { bottom: 0; top: Math.max(root.maxHp, 0) }
                                background: Item {}
                                onEditingFinished: {
                                    var v = Math.max(0, Math.min(root.maxHp, parseInt(text) || 0))
                                    value = v; text = String(v)
                                    root.hpEdited(v)
                                }
                                onValueChanged: text = String(value)
                            }
                            Step { objectName: "hpMore"; glyph: "+"; step: 1; Accessible.name: "1 more HP" }
                            Label { text: "/ " + root.maxHp; color: Theme.text3; font.pixelSize: Theme.fsSmall; leftPadding: 2 }
                        }
                    }
                    Chip { visible: !root.hasHpTracking; text: "HP " + root.hp; tint: Theme.green2 }
                    Item { Layout.fillWidth: true }
                    Label {
                        visible: root.speed.length > 0
                        text: root.speed; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsSmall
                        elide: Text.ElideRight
                        Layout.maximumWidth: 110
                    }
                }
            }
        }

        Rectangle { visible: root.expanded; Layout.fillWidth: true; height: 1; color: Theme.border }

        ColumnLayout {
            id: details
            visible: root.expanded
            Layout.fillWidth: true
            Layout.leftMargin: 14
            Layout.rightMargin: 12
            Layout.topMargin: 10
            Layout.bottomMargin: 12
            spacing: 8

            // the six abilities: a small box each
            GridLayout {
                Layout.fillWidth: true
                visible: root.abilities.length > 0
                columns: 6
                columnSpacing: 4
                rowSpacing: 4
                Repeater {
                    model: root.abilities
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: abCol.implicitHeight + 8
                        radius: 7
                        color: Theme.surf2
                        border.color: Theme.border
                        ColumnLayout {
                            id: abCol
                            anchors.centerIn: parent
                            spacing: 0
                            Label { text: modelData.ability; color: Theme.text3; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                            Label { text: String(modelData.score); color: Theme.text; font.bold: true; font.pixelSize: Theme.fsBody; Layout.alignment: Qt.AlignHCenter }
                            Label { text: String(modelData.mod); color: Theme.teal2; font.pixelSize: Theme.fsSmall; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                }
            }

            // the rest a line each: what it is in bold, then its value
            Repeater {
                model: [["Hit Dice", root.hitDice],
                        ["Saving Throws", root.saves.map(function (s) { return s.name + " " + s.bonus }).join(", ")],
                        ["Skills", root.skills.map(function (s) { return s.name + " " + s.bonus }).join(", ")],
                        ["Resistances", root.damageResistances], ["Immunities", root.damageImmunities],
                        ["Condition Immunities", root.conditionImmunities], ["Senses", root.senses],
                        ["Languages", root.languages === "—" ? "" : root.languages]]
                delegate: Label {
                    visible: modelData[1].length > 0
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    textFormat: Text.StyledText
                    color: Theme.text; font.pixelSize: Theme.fsSmall
                    text: "<b><font color='" + Theme.text2 + "'>" + modelData[0] + "</font></b>&nbsp;&nbsp;" + modelData[1]
                }
            }

            Repeater {
                model: [
                    { label: "TRAITS", entries: root.traits },
                    { label: "ACTIONS", entries: root.actions },
                    { label: "REACTIONS", entries: root.reactions },
                ]
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    visible: modelData.entries.length > 0
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Label { text: modelData.label; color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsSmall }
                        Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.35) }
                    }
                    Repeater {
                        model: modelData.entries
                        delegate: Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            textFormat: Text.StyledText
                            color: Theme.text; font.pixelSize: Theme.fsSmall
                            text: "<b><i>" + modelData.name + ".</i></b> " + modelData.desc
                        }
                    }
                }
            }
        }
    }
}
