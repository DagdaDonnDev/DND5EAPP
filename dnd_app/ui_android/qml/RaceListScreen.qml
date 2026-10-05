import QtQuick
import QtQuick.Controls
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Choose Your Race"
    background: Rectangle { color: Theme.bg }

    Component.onCompleted: Window.window.raceBridge.refresh()

    // See App.qml's navItems comment: StackView.push() needs an actual
    // Component, not a "Foo.qml" URL string, or the pushed page's
    // context-property bindings silently never resolve.
    Component { id: raceDetailComp; RaceDetailScreen {} }

    Column {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            visible: Window.window.raceBridge.selectedRace.length > 0
            text: "Selected: " + Window.window.raceBridge.selectedRace + (Window.window.raceBridge.raceConfirmedOnce ? "  ✓" : "")
            color: Theme.teal2
            font.pixelSize: Theme.fsBody
            font.bold: true
        }

        MTextField {
            id: search
            objectName: "raceSearchField"
            width: parent.width
            placeholderText: "Search races…"
            onTextChanged: Window.window.raceBridge.raceModel.setFilter(text)
        }

        ListView {
            width: parent.width
            height: parent.height - search.height - 60
            clip: true
            model: Window.window.raceBridge.raceModel
            delegate: ItemDelegate {
                objectName: "raceItem_" + name
                width: ListView.view.width
                height: 56
                contentItem: Row {
                    spacing: 10
                    anchors.verticalCenter: parent.verticalCenter
                    Label {
                        text: name
                        color: Theme.text
                        font.pixelSize: Theme.fsBody
                        font.bold: name === Window.window.raceBridge.selectedRace
                    }
                    Label {
                        text: source
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                    }
                }
                background: Rectangle {
                    color: name === Window.window.raceBridge.selectedRace ? Qt.rgba(Theme.indigo.r, Theme.indigo.g, Theme.indigo.b, 0.18) : "transparent"
                }
                onClicked: {
                    Window.window.raceBridge.selectRace(name)
                    root.StackView.view.push(raceDetailComp)
                }
            }
        }
    }
}
