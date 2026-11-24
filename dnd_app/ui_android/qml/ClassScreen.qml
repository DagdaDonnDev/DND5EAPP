import QtQuick
import QtQuick.Controls
import Mimic

// Wizard step 3: name and alignment, the classes as tiles, then the
// backgrounds to search and pick from, with the chosen one's feature.
Page {
    id: root
    readonly property string screenTitle: "Class & Background"
    readonly property var wb: Window.window.wizardBridge
    readonly property int rev: wb ? wb.rev : 0
    background: Rectangle { color: Theme.bg }

    WizSteps { id: steps; step: 2; width: parent.width }

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
            MTextField {
                objectName: "nameField"
                width: parent.width
                placeholderText: "Character name"
                Component.onCompleted: text = root.wb ? root.wb.name : ""
                onTextChanged: if (root.wb) root.wb.setName(text)
            }
            ComboBox {
                objectName: "alignmentCombo"
                width: parent.width
                model: root.wb ? root.wb.alignments : []
                currentIndex: root.wb ? Math.max(0, root.wb.alignments.indexOf(root.wb.alignment)) : 0
                onActivated: (i) => root.wb.setAlignment(model[i])
            }
            Label { text: "CLASS"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            Grid {
                width: parent.width
                columns: 4
                spacing: 5
                Repeater {
                    model: root.wb ? root.wb.classTiles : []
                    delegate: WizTile {
                        objectName: "classTile_" + modelData.name
                        width: (content.width - 15) / 4
                        label: modelData.name
                        sub: modelData.hit_die
                        on: root.wb && root.wb.selectedClass === modelData.name
                        onClicked: root.wb.pickClass(modelData.name)
                    }
                }
            }
            Grid {
                width: parent.width
                columns: 2
                spacing: 5
                Repeater {
                    model: { root.rev; return root.wb ? root.wb.classChips() : [] }
                    delegate: WizChip { width: (content.width - 5) / 2; text: modelData }
                }
            }
            Label { text: "BACKGROUND"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            MTextField {
                objectName: "backgroundSearchField"
                width: parent.width
                placeholderText: "⌕  Search backgrounds…"
                Component.onCompleted: text = root.wb ? root.wb.bgSearch : ""
                onTextChanged: if (root.wb) root.wb.setBgSearch(text)
            }
            ListView {
                id: bgList
                width: parent.width
                height: 220
                clip: true
                spacing: 4
                model: { root.rev; return root.wb ? root.wb.bgRows() : [] }
                delegate: WizRow {
                    objectName: "bgItem_" + modelData.name
                    width: ListView.view.width
                    implicitHeight: 38
                    name: modelData.name
                    meta: ""
                    tag: modelData.source
                    selected: root.wb && root.wb.selectedBackground === modelData.name
                    onClicked: root.wb.pickBackground(modelData.name)
                }
            }
            Rectangle {
                readonly property var bc: { root.rev; return root.wb ? root.wb.bgCard() : ({}) }
                visible: bc.name !== undefined
                width: parent.width
                height: bcol.implicitHeight + 20
                radius: 10
                color: Theme.surf; border.color: Theme.border
                Column {
                    id: bcol
                    x: 10; y: 10
                    width: parent.width - 20
                    spacing: 7
                    Row {
                        spacing: 8
                        Label { text: parent.parent.parent.bc.name || ""; color: Theme.gold2; font.pixelSize: Theme.fsHead - 2; font.bold: true }
                        WizChip { text: parent.parent.parent.bc.source || ""; kind: "gold"; height: 22; anchors.verticalCenter: parent.verticalCenter }
                    }
                    Grid {
                        width: parent.width
                        columns: 3
                        spacing: 5
                        Repeater {
                            model: bcol.parent.bc.chips || []
                            delegate: WizChip { width: (bcol.width - 10) / 3; text: modelData.text; kind: modelData.kind; height: 26 }
                        }
                    }
                    Rectangle {
                        visible: (bcol.parent.bc.feature || "").length > 0
                        width: parent.width
                        height: fcol.implicitHeight + 14
                        radius: 8
                        color: Theme.surf2; border.color: Theme.border
                        Column {
                            id: fcol
                            x: 10; y: 7
                            width: parent.width - 20
                            Label { width: parent.width; text: bcol.parent.bc.feature || ""; color: Theme.text; font.pixelSize: Theme.fsBody - 1; font.bold: true; wrapMode: Text.WordWrap }
                            Label { width: parent.width; text: bcol.parent.bc.text || ""; color: Theme.text2; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap }
                        }
                    }
                    Label {
                        visible: (bcol.parent.bc.feats || []).length > 0
                        text: "FEAT  <font color='" + Theme.text3 + "'>pick one</font>"
                        textFormat: Text.RichText
                        color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true
                    }
                    Grid {
                        width: parent.width
                        columns: 2
                        spacing: 5
                        Repeater {
                            model: bcol.parent.bc.feats || []
                            delegate: WizTile {
                                width: (bcol.width - 5) / 2
                                label: modelData
                                on: bcol.parent.bc.feat === modelData
                                onClicked: root.wb.pickBgFeat(modelData)
                            }
                        }
                    }
                    Label { width: parent.width; text: bcol.parent.bc.gear || ""; color: Theme.text3; font.pixelSize: Theme.fsSmall - 1; wrapMode: Text.WordWrap }
                }
            }
        }
    }
    WizNav {
        id: nav
        anchors.bottom: parent.bottom; width: parent.width
        readonly property string why: { root.rev; return root.wb ? root.wb.block(2) : "" }
        ready: why.length === 0
        text: ready ? "Next →" : why
        onBack: Window.window.goToWizardStep(1)
        onNext: if (ready) Window.window.advanceToChoices(); else Window.window.showToast(why)
    }
}
