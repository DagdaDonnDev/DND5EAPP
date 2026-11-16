import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Content for the Bestiary MFullPageDialog (see App.qml): every creature
// MIMIC knows, to find by name or type and filter by type, size,
// challenge rating and how it moves; a tap opens its stat block, and Back
// returns to the list. The Yours tab is the open character's own
// creatures (SheetCompanionsScreen.qml). The same as desktop's Bestiary
// window (bridge/bestiary.py, core/bestiary.py).
Item {
    id: root
    readonly property QtObject bBridge: Window.window ? Window.window.bestiaryBridge : null
    readonly property bool hasCharacter: Window.window ? Window.window.characterActive : false
    property string shown: ""          // the creature whose stat block is open
    property int tab: 0                // 0 all creatures, 1 yours
    anchors.fill: parent

    TabBar {
        id: tabs
        objectName: "bestiaryTabs"
        anchors { left: parent.left; right: parent.right; top: parent.top }
        currentIndex: root.tab
        onCurrentIndexChanged: root.tab = currentIndex
        TabButton { objectName: "bestiaryTabAll"; text: "All creatures" }
        TabButton { objectName: "bestiaryTabYours"; text: "Yours" }
    }

    // ── yours: the open character's creatures ─────────────────────────
    Loader {
        id: yours
        objectName: "bestiaryYours"
        anchors { left: parent.left; right: parent.right; top: tabs.bottom; bottom: parent.bottom }
        visible: root.tab === 1
        active: root.tab === 1 && root.hasCharacter
        source: "SheetCompanionsScreen.qml"
        onLoaded: item.embedded = true
    }
    Label {
        visible: root.tab === 1 && !root.hasCharacter
        anchors { left: parent.left; right: parent.right; top: tabs.bottom; margins: 16 }
        text: "Open a character to see its creatures here: its mounts and steeds, what it's "
              + "summoned, its companions and its Wild Shape forms."
        color: Theme.text3
        font.pixelSize: Theme.fsSmall
        wrapMode: Text.WordWrap
    }


    function refresh() {
        if (!bBridge) return
        // what's picked, read from the list: a box's currentText still says
        // the last pick while its currentIndex changes
        function picked(box) { return box.currentIndex > 0 ? String(box.model[box.currentIndex]) : "" }
        bBridge.searchMoving(searchField.text, picked(kindBox), picked(sizeBox),
                             picked(crMinBox), picked(crMaxBox), picked(moveBox))
    }
    Component.onCompleted: refresh()
    Timer { id: typing; interval: 200; onTriggered: root.refresh() }

    // ── all creatures ──────────────────────────────────────────────────
    Item {
        id: allPage
        anchors { left: parent.left; right: parent.right; top: tabs.bottom; bottom: parent.bottom }
        visible: root.tab === 0
    // ── the list ───────────────────────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        visible: root.shown === ""

        MTextField {
            id: searchField
            objectName: "bestiarySearch"
            Layout.fillWidth: true
            placeholderText: "Search creatures…"
            onTextChanged: typing.restart()
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 8
            rowSpacing: 6
            ComboBox {
                id: kindBox
                objectName: "bestiaryType"
                Layout.fillWidth: true
                model: ["Any type"].concat(root.bBridge ? root.bBridge.kinds : [])
                onCurrentIndexChanged: root.refresh()
            }
            ComboBox {
                id: sizeBox
                objectName: "bestiarySize"
                Layout.fillWidth: true
                model: ["Any size"].concat(root.bBridge ? root.bBridge.sizes : [])
                onCurrentIndexChanged: root.refresh()
            }
            ComboBox {
                id: crMinBox
                objectName: "bestiaryCrMin"
                Layout.fillWidth: true
                model: ["CR from"].concat(root.bBridge ? root.bBridge.crs : [])
                displayText: currentIndex > 0 ? "CR " + currentText + " up" : currentText
                onCurrentIndexChanged: root.refresh()
            }
            ComboBox {
                id: crMaxBox
                objectName: "bestiaryCrMax"
                Layout.fillWidth: true
                model: ["CR to"].concat(root.bBridge ? root.bBridge.crs : [])
                displayText: currentIndex > 0 ? "up to CR " + currentText : currentText
                onCurrentIndexChanged: root.refresh()
            }
            ComboBox {
                id: moveBox
                objectName: "bestiaryMove"
                Layout.fillWidth: true
                Layout.columnSpan: 2
                model: ["Any movement"].concat(root.bBridge ? root.bBridge.moves : [])
                onCurrentIndexChanged: root.refresh()
            }
        }
        Label {
            objectName: "bestiaryCount"
            text: root.bBridge ? (root.bBridge.results.length === 0
                                  ? "No creature matches. Try fewer words or another filter."
                                  : root.bBridge.results.length.toLocaleString(Qt.locale(), "f", 0)
                                    + (root.bBridge.results.length === 1 ? " creature" : " creatures")) : ""
            color: Theme.text3
            font.pixelSize: Theme.fsSmall
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }
        ListView {
            id: list
            objectName: "bestiaryList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.bBridge ? root.bBridge.results : []
            boundsBehavior: Flickable.StopAtBounds
            ScrollIndicator.vertical: ScrollIndicator {}
            delegate: Rectangle {
                objectName: "bestiaryRow_" + modelData.name
                width: ListView.view.width
                height: rowCol.implicitHeight + 16
                color: rowTap.pressed ? Theme.surf3 : "transparent"
                Column {
                    id: rowCol
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter
                              leftMargin: 6; rightMargin: 40 }
                    spacing: 2
                    Label {
                        text: modelData.name
                        color: Theme.text
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        elide: Text.ElideRight
                        width: parent.width
                    }
                    Label {
                        text: modelData.line
                        color: Theme.text2
                        font.pixelSize: Theme.fsSmall
                        elide: Text.ElideRight
                        width: parent.width
                    }
                }
                // View -- a magnifying glass, as the other browsers' rows have
                MIcon {
                    name: "search"
                    size: 20
                    color: Theme.text3
                    anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.border }
                MouseArea {
                    id: rowTap
                    objectName: "bestiaryTap_" + modelData.name
                    anchors.fill: parent
                    onClicked: root.shown = modelData.name
                }
            }
        }
    }

    // ── one creature's stat block ─────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        visible: root.shown !== ""

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            MButton {
                objectName: "bestiaryBack"
                primary: false
                implicitHeight: 36
                text: "Back"
                onClicked: root.shown = ""
            }
            Label {
                objectName: "bestiaryTitle"
                text: root.shown
                color: Theme.gold2
                font.pixelSize: Theme.fsHead
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
        Flickable {
            id: blockFlick
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: blockText.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollIndicator.vertical: ScrollIndicator {}
            Label {
                id: blockText
                objectName: "bestiaryStatblock"
                width: blockFlick.width
                textFormat: Text.StyledText
                wrapMode: Text.WordWrap
                color: Theme.text
                font.pixelSize: Theme.fsBody
                text: root.shown !== "" && root.bBridge ? root.bBridge.statblock(root.shown, Theme.gold2.toString()) : ""
            }
        }
    }
    }
    onShownChanged: blockFlick.contentY = 0
}
