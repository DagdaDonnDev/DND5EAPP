import QtQuick
import QtQuick.Controls
import Mimic

// Wizard step 1: the races, as the app's other browsers -- search, source
// chips, a row each. A tap opens its details (RaceDetailScreen).
Page {
    id: root
    readonly property string screenTitle: "Choose Your Race"
    readonly property var wb: Window.window.wizardBridge
    background: Rectangle { color: Theme.bg }

    Component { id: raceDetailComp; RaceDetailScreen {} }

    WizSteps { id: steps; step: 0; width: parent.width }

    Column {
        id: top
        anchors.top: steps.bottom
        anchors.left: parent.left; anchors.right: parent.right
        anchors.margins: 12
        anchors.topMargin: 10
        spacing: 8
        MTextField {
            objectName: "raceSearchField"
            width: parent.width
            placeholderText: "⌕  Search races…"
            text: root.wb ? root.wb.raceSearch : ""
            onTextChanged: if (root.wb) root.wb.setRaceSearch(text)
        }
        Row {
            width: parent.width
            spacing: 5
            Repeater {
                model: root.wb ? root.wb.raceGroups : []
                delegate: WizChip {
                    width: (top.width - 5 * 4) / 5
                    text: modelData === "Multiverse" ? "MPMM" : modelData
                    kind: root.wb && root.wb.raceGroup === modelData ? "gold" : "off"
                    MouseArea { anchors.fill: parent; onClicked: root.wb.setRaceGroup(modelData) }
                }
            }
        }
    }
    ListView {
        id: list
        anchors.top: top.bottom; anchors.topMargin: 8
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        anchors.leftMargin: 12; anchors.rightMargin: 12
        clip: true
        spacing: 5
        model: { root.wb ? root.wb.rev : 0; return root.wb ? root.wb.raceRows() : [] }
        delegate: WizRow {
            objectName: "raceItem_" + modelData.name
            width: ListView.view.width
            name: modelData.name
            meta: modelData.asi
            tag: modelData.source
            selected: root.wb && root.wb.selectedRace === modelData.name
            onClicked: {
                root.wb.selectRace(modelData.name)
                root.StackView.view.push(raceDetailComp)
            }
        }
    }
}
