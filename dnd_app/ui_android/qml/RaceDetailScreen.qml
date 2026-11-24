import QtQuick
import QtQuick.Controls
import Mimic

// A race's details: its bonuses and senses as chips, the subraces as tiles
// (and a dragonborn's ancestry, an eladrin's season...), its traits as
// cards. Next goes on to the Abilities step.
Page {
    id: root
    readonly property var wb: Window.window.wizardBridge
    readonly property var card: { wb ? wb.rev : 0; return wb ? wb.raceCard() : ({}) }
    readonly property string screenTitle: card.name || "Race"
    background: Rectangle { color: Theme.bg }

    WizSteps { id: steps; step: 0; width: parent.width }

    Flickable {
        anchors.top: steps.bottom; anchors.bottom: nav.top
        anchors.left: parent.left; anchors.right: parent.right
        contentHeight: content.height + 24
        clip: true
        Column {
            id: content
            x: 12; y: 12
            width: parent.width - 24
            spacing: 9
            Row {
                spacing: 8
                Label { text: root.card.name || ""; color: Theme.gold2; font.pixelSize: Theme.fsTitle - 2; font.bold: true }
                WizChip { text: root.card.source || ""; kind: "gold"; height: 22; anchors.verticalCenter: parent.verticalCenter }
            }
            Grid {
                width: parent.width
                columns: 2
                spacing: 5
                Repeater {
                    model: root.card.chips || []
                    delegate: WizChip { width: (content.width - 5) / 2; text: modelData.text; kind: modelData.kind }
                }
            }
            Label {
                visible: (root.card.subOptions || []).length > 0
                text: "SUBRACE  <font color='" + Theme.text3 + "'>" + (root.card.subrace_required ? "pick one" : "optional") + "</font>"
                textFormat: Text.RichText
                color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true
            }
            Grid {
                width: parent.width
                columns: 3
                spacing: 5
                Repeater {
                    model: root.card.subOptions || []
                    delegate: WizTile {
                        objectName: "subrace_" + modelData.label
                        width: (content.width - 10) / 3
                        label: modelData.label
                        on: root.card.subrace === modelData.value
                        onClicked: root.wb.selectSubrace(modelData.value)
                    }
                }
            }
            Repeater {
                model: [["ancestry", "DRACONIC ANCESTRY", "ancestry"], ["seasons", "ELADRIN SEASON", "season"],
                        ["simic", "ANIMAL ENHANCEMENT", "simic"]]
                delegate: Column {
                    width: content.width
                    spacing: 6
                    readonly property var opts: root.card[modelData[0]] || []
                    visible: opts.length > 0
                    Label { text: modelData[1]; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
                    Grid {
                        width: parent.width
                        columns: parent.opts.length >= 5 ? 5 : Math.max(1, parent.opts.length)
                        spacing: 5
                        Repeater {
                            model: parent.parent.opts
                            delegate: WizTile {
                                width: (content.width - 5 * (parent.columns - 1)) / parent.columns
                                label: modelData.name
                                sub: modelData.sub.length <= 14 ? modelData.sub : ""
                                tip: modelData.sub.length > 14 ? modelData.sub : ""
                                on: (root.card.rpicks || {})[parent.parent.fieldName] === modelData.value
                                onClicked: root.wb.pickRaceExtra(parent.parent.fieldName, modelData.value)
                            }
                        }
                    }
                    readonly property string fieldName: modelData[2]
                }
            }
            Label { text: "TRAITS"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            Repeater {
                model: root.card.traits || []
                delegate: Rectangle {
                    width: content.width
                    height: tc.implicitHeight + 16
                    radius: 8
                    color: Theme.surf2; border.color: Theme.border
                    Column {
                        id: tc
                        x: 12; y: 8
                        width: parent.width - 24
                        spacing: 2
                        Label { width: parent.width; text: modelData.name; color: Theme.text; font.pixelSize: Theme.fsBody - 1; font.bold: true; wrapMode: Text.WordWrap }
                        Label { visible: modelData.text.length > 0; width: parent.width; text: modelData.text; color: Theme.text2; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap }
                    }
                }
            }
        }
    }
    WizNav {
        id: nav
        anchors.bottom: parent.bottom; width: parent.width
        showBack: false
        readonly property string why: { root.wb ? root.wb.rev : 0; return root.wb ? root.wb.block(0) : "" }
        ready: why.length === 0
        text: ready ? "Next →" : why
        onNext: if (ready) Window.window.advanceToAbilities(); else Window.window.showToast(why)
    }
}
