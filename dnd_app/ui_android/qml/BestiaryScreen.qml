import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Content for the Bestiary MFullPageDialog (see App.qml): every creature
// MIMIC knows, to find by name or type and filter by type, size and
// challenge rating; a tap opens its stat block, and Back returns to the
// list. The same as desktop's Bestiary window (bridge/bestiary.py,
// core/bestiary.py).
Item {
    id: root
    readonly property QtObject bBridge: Window.window ? Window.window.bestiaryBridge : null
    property string shown: ""          // the creature whose stat block is open
    anchors.fill: parent

    function refresh() {
        if (!bBridge) return
        bBridge.search(searchField.text,
                       kindBox.currentIndex > 0 ? kindBox.currentText : "",
                       sizeBox.currentIndex > 0 ? sizeBox.currentText : "",
                       crMinBox.currentIndex > 0 ? crMinBox.currentText : "",
                       crMaxBox.currentIndex > 0 ? crMaxBox.currentText : "")
    }
    Component.onCompleted: refresh()
    Timer { id: typing; interval: 200; onTriggered: root.refresh() }

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
            placeholderText: "Find a creature by name or type…"
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
                              leftMargin: 6; rightMargin: 6 }
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
    onShownChanged: blockFlick.contentY = 0
}
