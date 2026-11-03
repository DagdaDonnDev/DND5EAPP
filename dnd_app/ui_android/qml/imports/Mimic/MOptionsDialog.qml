import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// The small menu shown when something you own (a known spell, an
// inventory item, a magic item) is pressed and held -- one button per
// option, then Cancel. Fill `options` with {key, text, icon} objects
// just before open(); `picked(key)` fires after it closes.
Dialog {
    id: root

    property string heading: ""
    // an optional line under the heading (a question to answer)
    property string message: ""
    property var options: []
    // border colour -- a magic item's rarity colour, for instance
    property color accent: Theme.border
    // the last button's text ("OK" for a message with no options)
    property string cancelText: "Cancel"

    signal picked(string key)

    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    width: Math.min(parent ? parent.width - 32 : 340, 340)
    padding: 16
    background: Rectangle { color: Theme.surf; radius: 12; border.color: root.accent; border.width: Qt.colorEqual(root.accent, Theme.border) ? 1 : 2 }
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

    contentItem: ColumnLayout {
        spacing: 10
        Label {
            visible: root.heading.length > 0
            text: root.heading
            color: Theme.gold2
            font.pixelSize: Theme.fsHead
            font.bold: true
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        Label {
            visible: root.message.length > 0
            text: root.message
            color: Theme.text
            font.pixelSize: Theme.fsBody
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        // a long list (a druid's Wild Shape forms) scrolls instead of
        // running off the screen
        Flickable {
            id: optionsFlick
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(optionsCol.implicitHeight,
                                             (root.parent ? root.parent.height : 800) * 0.6)
            contentHeight: optionsCol.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollIndicator.vertical: ScrollIndicator {}
            ColumnLayout {
                id: optionsCol
                width: optionsFlick.width
                spacing: 10
                Repeater {
                    model: root.options
                    delegate: MButton {
                        objectName: "option_" + modelData.key
                        Layout.fillWidth: true
                        primary: false
                        wrapText: true
                        iconName: modelData.icon || ""
                        iconSize: 16
                        text: modelData.text
                        onClicked: {
                            var key = modelData.key
                            root.close()
                            root.picked(key)
                        }
                    }
                }
            }
        }
        MButton {
            objectName: "optionsCancel"
            Layout.fillWidth: true
            primary: false
            text: root.cancelText
            onClicked: root.close()
        }
    }
}
