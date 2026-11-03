import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A browser's filters, in a panel that slides in from the right-hand
// edge -- so the browser itself only needs a search box and a funnel
// button (MFilterButton) above its list.
//
// Using it:
//   1. Declare the drawer in the browser and put its filters inside it,
//      each under an MFilterDrawer-style caption, e.g.
//          MFilterDrawer {
//              id: miFilters
//              activeCount: (slot.currentIndex > 0) + (rarity.currentIndex > 0)
//              onCleared: { slot.currentIndex = 0; rarity.currentIndex = 0 }
//              Label { text: "Rarity"; ... }
//              ComboBox { id: rarity; Layout.fillWidth: true; ... }
//          }
//   2. Point the search row's MFilterButton at it:
//          MFilterButton { count: miFilters.activeCount; onClicked: miFilters.open() }
// The filters are ordinary controls with their usual ids, so the
// browser reads them (and reacts to their changes) exactly as before.
// "Clear filters" emits cleared() -- the browser puts each filter back
// on its first entry; "Done" closes the panel.
Drawer {
    id: root
    // sized against the whole window, wherever the drawer is declared
    parent: Overlay.overlay
    edge: Qt.RightEdge
    modal: true
    width: Math.min(0.82 * (parent ? parent.width : 360), 340)
    height: parent ? parent.height : 640
    // Only drag-to-close while open: a screen can hold several of these,
    // and a closed one listening for a swipe from the right edge would
    // open whichever happened to be declared last.
    interactive: opened

    property string title: "Filters"
    property int activeCount: 0
    signal cleared()
    default property alias content: body.data

    // flat panel, dark fog behind it (like the other drawers and dialogs)
    background: Rectangle { color: Theme.surf }
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.topMargin: 20
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            MIcon { name: "filter"; size: 20; color: Theme.gold }
            Label {
                text: root.title
                color: Theme.gold2
                font.pixelSize: Theme.fsBody
                font.bold: true
                Layout.fillWidth: true
            }
        }

        // the browser's own filters go in here, one under another
        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentHeight: body.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ColumnLayout {
                id: body
                width: parent.width
                spacing: 10
            }
        }

        MButton {
            Layout.fillWidth: true
            primary: false
            text: root.activeCount > 0 ? "Clear filters (" + root.activeCount + ")" : "Clear filters"
            enabled: root.activeCount > 0
            onClicked: root.cleared()
        }
        MButton {
            objectName: "filterDoneButton"
            Layout.fillWidth: true
            text: "Done"
            onClicked: root.close()
        }
    }
}
