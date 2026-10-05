import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Shared expandable "stat block" tile -- Android equivalent of desktop's
// CompanionsMixin._build_statblock_card, reused for mounts, vehicles,
// summoned creatures, class-granted companions, and the Wild Shape
// preview card. Collapsed by default (name/AC/HP only); tap the header
// to expand the full block (abilities, saves, skills, traits/actions/
// reactions).
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
    signal removeClicked()

    property bool expanded: startExpanded

    Layout.fillWidth: true
    implicitHeight: col.height
    radius: 10
    color: Theme.surf
    border.color: Theme.teal2

    ColumnLayout {
        id: col
        width: parent.width
        spacing: 0

        MouseArea {
            id: header
            Layout.fillWidth: true
            Layout.preferredHeight: headerCol.height + 24
            cursorShape: Qt.PointingHandCursor
            onClicked: root.expanded = !root.expanded

            // Two rows rather than one -- cramming name+source+AC+HP into
            // a single RowLayout let a long display name (e.g. "Beast of
            // the Land") push the AC/HP group past the card's right edge
            // on a narrow phone width, since RowLayout doesn't shrink
            // non-fillWidth siblings to make room. Name/source get their
            // own elidable row; AC/HP sit on a second row below.
            ColumnLayout {
                id: headerCol
                x: 14; y: 12
                width: parent.width - 28
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    MIcon { name: root.expanded ? "chevron_down" : "chevron_right"; size: 16 }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            Layout.fillWidth: true
                            text: root.displayName; color: Theme.teal2; font.bold: true
                            font.pixelSize: Theme.fsBody; elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: root.source; color: Theme.text3; font.pixelSize: Theme.fsSmall
                            elide: Text.ElideRight
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 24
                    spacing: 14
                    Label { text: "AC " + root.ac; color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsBody }
                    Item { Layout.fillWidth: true }
                    RowLayout {
                        visible: root.hasHpTracking
                        spacing: 3
                        Label { text: "HP"; color: Theme.green2; font.bold: true; font.pixelSize: Theme.fsBody }
                        MSpinBox {
                            id: hpSpin
                            from: 0
                            to: Math.max(root.maxHp, 0)
                            value: root.currentHp
                            // MSpinBox's up/down indicators are 36px each
                            // (72px total) -- anything narrower than
                            // ~110px leaves too little room for the
                            // number, visually mashing a "-" glyph
                            // against the digits (looked like a negative
                            // value at 74px, e.g. "-20" for a value of 20).
                            implicitWidth: 110
                            onValueModified: root.hpEdited(value)
                        }
                        Label { text: "/ " + root.maxHp; color: Theme.text3; font.pixelSize: Theme.fsSmall }
                    }
                    Label {
                        visible: !root.hasHpTracking
                        text: "HP " + root.hp
                        color: Theme.green2; font.bold: true; font.pixelSize: Theme.fsBody
                    }
                }
            }
        }

        ColumnLayout {
            id: details
            visible: root.expanded
            Layout.fillWidth: true
            Layout.leftMargin: 14
            Layout.rightMargin: 14
            Layout.bottomMargin: 12
            spacing: 6

            Label {
                visible: root.size.length > 0 || root.creatureType.length > 0
                text: root.size + " " + root.creatureType
                color: Theme.text2; font.bold: true; font.pixelSize: Theme.fsSmall
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 18
                Label {
                    text: root.hasHpTracking
                          ? ("HP " + root.currentHp + "/" + root.maxHp + (root.hitDice ? "  (" + root.hitDice + ")" : ""))
                          : ("HP " + root.hp + (root.hitDice ? "  (" + root.hitDice + ")" : ""))
                    color: Theme.green2; font.bold: true; font.pixelSize: Theme.fsBody
                }
                Label { text: "Speed " + root.speed; color: Theme.teal2; font.bold: true; font.pixelSize: Theme.fsBody }
                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                visible: root.abilities.length > 0
                Repeater {
                    model: root.abilities
                    delegate: ColumnLayout {
                        spacing: 0
                        Label { text: modelData.ability; color: Theme.text3; font.pixelSize: Theme.fsSmall; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        Label { text: modelData.score + " (" + modelData.mod + ")"; color: Theme.text; font.bold: true; font.pixelSize: Theme.fsSmall; Layout.alignment: Qt.AlignHCenter }
                    }
                }
            }

            Label {
                visible: root.saves.length > 0
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                text: "Saving Throws: " + root.saves.map(function(s) { return s.name + " " + s.bonus }).join(", ")
            }
            Label {
                visible: root.skills.length > 0
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                text: "Skills: " + root.skills.map(function(s) { return s.name + " " + s.bonus }).join(", ")
            }
            Label {
                visible: root.damageResistances.length > 0
                Layout.fillWidth: true; wrapMode: Text.WordWrap
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                text: "Damage Resistances: " + root.damageResistances
            }
            Label {
                visible: root.damageImmunities.length > 0
                Layout.fillWidth: true; wrapMode: Text.WordWrap
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                text: "Damage Immunities: " + root.damageImmunities
            }
            Label {
                visible: root.conditionImmunities.length > 0
                Layout.fillWidth: true; wrapMode: Text.WordWrap
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                text: "Condition Immunities: " + root.conditionImmunities
            }
            Label {
                visible: root.senses.length > 0
                Layout.fillWidth: true; wrapMode: Text.WordWrap
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                text: "Senses: " + root.senses
            }
            Label {
                visible: root.languages.length > 0
                Layout.fillWidth: true; wrapMode: Text.WordWrap
                color: Theme.text2; font.pixelSize: Theme.fsSmall
                text: "Languages: " + root.languages
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
                    Label { text: modelData.label; color: Theme.gold2; font.bold: true; font.pixelSize: Theme.fsSmall }
                    Repeater {
                        model: modelData.entries
                        delegate: Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: Theme.text; font.pixelSize: Theme.fsSmall
                            text: modelData.name + ". " + modelData.desc
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 14
            Layout.rightMargin: 14
            Layout.bottomMargin: 10
            visible: root.removable
            // An explicit spacer, not just Layout.alignment on the lone
            // button -- with only one child, RowLayout has nothing to
            // measure the alignment against and the button ends up
            // flush at the left edge instead of sitting at the right.
            Item { Layout.fillWidth: true }
            MButton {
                text: "Remove"
                primary: false
                height: 28
                onClicked: root.removeClicked()
            }
        }
    }
}
