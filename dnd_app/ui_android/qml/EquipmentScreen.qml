import QtQuick
import QtQuick.Controls
import Mimic

// Wizard step 5: each starting-gear pick as A or B (the chosen one green,
// any weapon picked underneath), what the class always gives, the
// background's gear -- and a page of what you'll start with.
Page {
    id: root
    readonly property string screenTitle: "Starting Equipment"
    readonly property var wb: Window.window.wizardBridge
    readonly property int rev: wb ? wb.rev : 0
    readonly property var view: { rev; return wb ? wb.equipView() : ({ groups: [] }) }
    background: Rectangle { color: Theme.bg }

    Component { id: kitComp; KitScreen {} }

    WizSteps { id: steps; step: 4; width: parent.width }

    Flickable {
        anchors.top: steps.bottom; anchors.bottom: nav.top
        anchors.left: parent.left; anchors.right: parent.right
        contentHeight: content.height + 24
        clip: true
        Column {
            id: content
            x: 12; y: 12
            width: parent.width - 24
            spacing: 8
            Repeater {
                model: root.view.groups || []
                delegate: WizCard {
                    id: gcard
                    readonly property var g: modelData
                    width: content.width
                    title: g.title
                    Repeater {
                        model: gcard.g.options
                        delegate: Rectangle {
                            objectName: "equipOption_" + gcard.g.gi + "_" + index
                            readonly property var o: modelData
                            width: gcard.width - 20
                            height: oc.implicitHeight + 16
                            radius: 8
                            color: o.on ? Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.12) : Theme.surf
                            border.color: o.on ? Theme.teal : Theme.border
                            MouseArea { anchors.fill: parent; enabled: !gcard.g.fixed; onClicked: root.wb.pickOption(gcard.g.gi, index) }
                            Column {
                                id: oc
                                x: 10; y: 8
                                width: parent.width - 20
                                spacing: 6
                                Row {
                                    width: parent.width
                                    spacing: 8
                                    Label { visible: !gcard.g.fixed; text: o.letter; color: Theme.text3; font.pixelSize: Theme.fsSmall; font.bold: true }
                                    Label {
                                        width: parent.width - 20
                                        text: o.label
                                        wrapMode: Text.WordWrap
                                        color: o.on ? Theme.teal2 : Theme.text
                                        font.pixelSize: Theme.fsBody - 1; font.bold: true
                                    }
                                }
                                Repeater {
                                    model: o.on ? o.anys : []
                                    delegate: ComboBox {
                                        width: oc.width
                                        model: modelData.pool
                                        currentIndex: Math.max(0, modelData.pool.indexOf(modelData.value))
                                        onActivated: (i) => root.wb.setAny(gcard.g.gi, index, model[i])
                                    }
                                }
                            }
                        }
                    }
                }
            }
            WizCard {
                visible: (root.view.always || []).length > 0
                width: content.width
                title: "Always"
                Grid {
                    width: content.width - 20
                    columns: 2
                    spacing: 5
                    Repeater {
                        model: root.view.always || []
                        delegate: WizChip { width: (content.width - 25) / 2; text: modelData }
                    }
                }
            }
            WizCard {
                visible: (root.view.bgGear || []).length > 0
                width: content.width
                title: "From " + (root.view.bg || "")
                Grid {
                    width: content.width - 20
                    columns: 2
                    spacing: 5
                    Repeater {
                        model: root.view.bgGear || []
                        delegate: WizChip { width: (content.width - 25) / 2; text: modelData; kind: "gold" }
                    }
                }
            }
            MButton {
                objectName: "seeKitButton"
                width: parent.width
                primary: false
                text: "See what you'll start with ▸"
                onClicked: root.StackView.view.push(kitComp)
            }
        }
    }
    WizNav {
        id: nav
        anchors.bottom: parent.bottom; width: parent.width
        onBack: Window.window.goToWizardStep(root.wb && root.wb.hasLevel1() ? 3 : 2)
        onNext: Window.window.advanceToSummary()
    }
}
