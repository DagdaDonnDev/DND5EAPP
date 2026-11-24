import QtQuick
import QtQuick.Controls
import Mimic

// Wizard step 2: the method as tabs, and each ability in one box -- its
// score with − and +, the race's bonus or the +1 you place there, then the
// total and modifier.
Page {
    id: root
    readonly property string screenTitle: "Ability Scores"
    readonly property var wb: Window.window.wizardBridge
    readonly property var view: { wb ? wb.rev : 0; return wb ? wb.abilityView() : ({ cols: [] }) }
    background: Rectangle { color: Theme.bg }

    WizSteps { id: steps; step: 1; width: parent.width }

    Flickable {
        anchors.top: steps.bottom; anchors.bottom: nav.top
        anchors.left: parent.left; anchors.right: parent.right
        contentHeight: content.height + 24
        clip: true
        Column {
            id: content
            x: 12; y: 12
            width: parent.width - 24
            spacing: 10
            Row {
                width: parent.width
                spacing: 4
                Repeater {
                    model: root.wb ? root.wb.methods : []
                    delegate: Rectangle {
                        objectName: "method_" + modelData
                        readonly property bool on: root.wb && root.wb.method === modelData
                        width: (content.width - 12) / 4; height: 36; radius: 8
                        color: on ? Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.12) : Theme.surf2
                        border.color: on ? Theme.gold : Theme.border
                        Label {
                            anchors.centerIn: parent
                            text: modelData === "Standard Array" ? "Array" : modelData === "Enter scores" ? "Enter" : modelData
                            color: parent.on ? Theme.gold2 : Theme.text2
                            font.pixelSize: Theme.fsSmall; font.bold: true
                        }
                        MouseArea { anchors.fill: parent; onClicked: root.wb.setMethod(modelData) }
                    }
                }
            }
            Label {
                width: parent.width
                wrapMode: Text.WordWrap
                textFormat: Text.RichText
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                text: (root.wb && root.wb.method === "Point Buy"
                       ? "Points left <b><font color='" + (root.view.pointBuyLeft >= 0 ? Theme.teal2 : Theme.crimson2) + "'>"
                         + root.view.pointBuyLeft + "</font></b> / 27 · " : "")
                      + (root.view.text || "")
            }
            Row {
                spacing: 8
                visible: root.view.hasFixed || (root.wb && root.wb.method === "Roll")
                MButton {
                    visible: root.wb && root.wb.method === "Roll"
                    primary: false
                    height: 32
                    text: "🎲  Roll all"
                    onClicked: root.wb.rollAll()
                }
                MButton {
                    visible: root.view.hasFixed === true
                    primary: false
                    height: 32
                    text: root.view.moving ? "Put my race bonus back" : "Move my race bonus"
                    onClicked: root.wb.toggleMoved()
                }
            }
            Grid {
                width: parent.width
                columns: 3
                spacing: 8
                Repeater {
                    model: root.view.cols || []
                    delegate: Rectangle {
                        objectName: "abilityBox_" + modelData.ab
                        width: (content.width - 16) / 3
                        height: box.implicitHeight + 16
                        radius: 10
                        color: Theme.surf2; border.color: Theme.border
                        Column {
                            id: box
                            y: 8
                            width: parent.width
                            spacing: 5
                            Label { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.ab; color: Theme.text2; font.pixelSize: Theme.fsSmall - 1; font.bold: true }
                            Row {
                                anchors.horizontalCenter: parent.horizontalCenter
                                spacing: 4
                                Rectangle {
                                    visible: !(root.wb && root.wb.method === "Roll")
                                    width: 26; height: 26; radius: 6; color: Theme.surf; border.color: Theme.border
                                    Label { anchors.centerIn: parent; text: "−"; color: Theme.text; font.bold: true }
                                    MouseArea { anchors.fill: parent; onClicked: root.wb.stepScore(modelData.ab, false) }
                                }
                                Label {
                                    objectName: "abilityBase_" + modelData.ab
                                    width: 26; horizontalAlignment: Text.AlignHCenter
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData.base; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true
                                }
                                Rectangle {
                                    visible: !(root.wb && root.wb.method === "Roll")
                                    width: 26; height: 26; radius: 6; color: Theme.surf; border.color: Theme.border
                                    Label { anchors.centerIn: parent; text: "+"; color: Theme.text; font.bold: true }
                                    MouseArea { anchors.fill: parent; onClicked: root.wb.stepScore(modelData.ab, true) }
                                }
                                Rectangle {
                                    visible: root.wb && root.wb.method === "Roll"
                                    width: 30; height: 26; radius: 6; color: "transparent"; border.color: Theme.border2
                                    Label { anchors.centerIn: parent; text: "🎲"; font.pixelSize: Theme.fsSmall }
                                    MouseArea { anchors.fill: parent; onClicked: root.wb.rollOne(modelData.ab) }
                                }
                            }
                            Row {
                                anchors.horizontalCenter: parent.horizontalCenter
                                spacing: 4
                                height: 24
                                // a Tasha's move: − race +
                                Rectangle {
                                    visible: root.view.moving === true
                                    width: 22; height: 22; radius: 5; color: "transparent"; border.color: Theme.border
                                    Label { anchors.centerIn: parent; text: "−"; color: Theme.text2; font.bold: true }
                                    MouseArea { anchors.fill: parent; onClicked: root.wb.moveBonus(modelData.ab, -1) }
                                }
                                WizChip {
                                    visible: root.view.moving === true || modelData.fixed > 0
                                    height: 22
                                    text: root.view.moving ? (modelData.moved ? "+" + modelData.moved : "race") : "+" + modelData.fixed
                                    kind: (root.view.moving ? modelData.moved : modelData.fixed) ? "teal" : "off"
                                }
                                Rectangle {
                                    visible: root.view.moving === true
                                    width: 22; height: 22; radius: 5; color: "transparent"; border.color: Theme.border
                                    Label { anchors.centerIn: parent; text: "+"; color: Theme.text2; font.bold: true }
                                    MouseArea { anchors.fill: parent; onClicked: root.wb.moveBonus(modelData.ab, 1) }
                                }
                                WizChip {
                                    objectName: "abilityPick_" + modelData.ab
                                    visible: modelData.canPick
                                    height: 22
                                    text: modelData.pick ? "✓ +" + modelData.pick : "+1"
                                    kind: modelData.pick ? "teal" : "off"
                                    MouseArea { anchors.fill: parent; onClicked: root.wb.tapPick(modelData.ab) }
                                }
                            }
                            Label {
                                objectName: "abilityTotal_" + modelData.ab
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.total
                                color: modelData.total !== modelData.base ? Theme.teal2 : Theme.text
                                font.pixelSize: Theme.fsTitle; font.bold: true
                            }
                            WizChip {
                                anchors.horizontalCenter: parent.horizontalCenter
                                height: 22
                                text: modelData.mod
                                kind: modelData.neg ? "red" : "teal"
                            }
                        }
                    }
                }
            }
        }
    }
    WizNav {
        id: nav
        anchors.bottom: parent.bottom; width: parent.width
        readonly property string why: { root.wb ? root.wb.rev : 0; return root.wb ? root.wb.block(1) : "" }
        ready: why.length === 0
        text: ready ? "Next →" : why
        onBack: Window.window.goToWizardStep(0)
        onNext: if (ready) Window.window.advanceToClass(); else Window.window.showToast(why)
    }
}
