import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Content for the Reference MFullPageDialog (see App.qml, beside
// Settings): what the book codes beside spells, feats, magic items and
// creatures mean -- the same list as desktop's Reference (data/books.py).
Item {
    id: root
    readonly property QtObject bBridge: Window.window ? Window.window.bestiaryBridge : null
    anchors.fill: parent

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        Label {
            text: "The book codes beside spells, feats, magic items and creatures, and the book each one means."
            color: Theme.text2
            font.pixelSize: Theme.fsSmall
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        ListView {
            objectName: "referenceList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.bBridge ? root.bBridge.bookCodes : []
            boundsBehavior: Flickable.StopAtBounds
            ScrollIndicator.vertical: ScrollIndicator {}
            delegate: Rectangle {
                width: ListView.view.width
                height: Math.max(codeLbl.implicitHeight, bookLbl.implicitHeight) + 14
                color: "transparent"
                Label {
                    id: codeLbl
                    x: 6; width: 76
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.code
                    color: Theme.gold2
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                }
                Label {
                    id: bookLbl
                    anchors { left: codeLbl.right; right: parent.right; leftMargin: 8; rightMargin: 6
                              verticalCenter: parent.verticalCenter }
                    text: modelData.book
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    wrapMode: Text.WordWrap
                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.border }
            }
        }
    }
}
