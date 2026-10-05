import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Reusable "search a flat string list, tap to pick" popup -- Android
// equivalent of desktop's QInputDialog.getItem(), used for Identity
// edits (Race/Subrace/Ancestry/Background) and similar single-value
// pickers from a known option list.
Popup {
    id: root
    objectName: "pickerDialog_" + dialogTitle
    modal: true
    focus: true
    // Explicitly parent to the Overlay layer rather than relying on
    // whatever Item happens to declare this Popup in QML -- when that
    // declaring Item is inside a scrollable Flickable, the implicit
    // parent scrolls with the page, so anchors.centerIn: parent would
    // center against the scrolled content instead of the real window
    // viewport (pushing the dialog off-screen once the page is scrolled).
    parent: Overlay.overlay
    width: Math.min(360, (parent ? parent.width : 360) * 0.9)
    height: Math.min(460, (parent ? parent.height : 460) * 0.85)
    anchors.centerIn: parent
    padding: 0

    property string dialogTitle: "Choose"
    property var options: []
    signal picked(string value)

    onOpened: search.text = ""

    background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
    // Matches MFullPageDialog.qml's dimming -- Qt Quick Controls'
    // default modal overlay is a much lighter wash that looked glaringly
    // bright against this app's dark theme (direct user report).
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 8

        Label {
            text: root.dialogTitle
            color: Theme.gold
            font.pixelSize: Theme.fsBody
            font.bold: true
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }
        MTextField {
            id: search
            objectName: "pickerSearchField"
            Layout.fillWidth: true
            placeholderText: "Search…"
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 8
            color: Theme.surf2
            border.color: Theme.border
            clip: true

            ListView {
                id: listView
                objectName: "pickerListView"
                anchors.fill: parent
                anchors.margins: 4
                clip: true
                model: root.options.filter(function(o) {
                    return search.text.length === 0 || o.toLowerCase().indexOf(search.text.toLowerCase()) >= 0
                })
                delegate: ItemDelegate {
                    width: ListView.view.width
                    height: 44
                    contentItem: Label {
                        text: modelData
                        color: Theme.text
                        font.pixelSize: Theme.fsBody
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                    }
                    onClicked: {
                        root.picked(modelData)
                        root.close()
                    }
                }
            }
        }
        MButton {
            text: "Cancel"
            primary: false
            Layout.fillWidth: true
            onClicked: root.close()
        }
    }
}
