import QtQuick
import QtQuick.Controls

// Material's default SpinBox contentItem renders its number invisibly
// in this app (confirmed both in the offscreen test harness and by
// inspection of the Material style's default delegate, which is the
// same class of bug MButton.qml already works around for Button) --
// explicit background/indicators/contentItem here instead of relying
// on Material's defaults, same fix shape as MButton.
SpinBox {
    id: control
    from: 0
    to: 99
    // Lets the player type a value directly (e.g. a big damage number)
    // instead of only tapping +/- one at a time -- the contentItem
    // below was already built to support this (readOnly: !editable),
    // it just never got turned on.
    editable: true

    contentItem: TextInput {
        text: control.textFromValue(control.value, control.locale)
        font.pixelSize: Theme.fsBody
        color: Theme.text
        selectionColor: Theme.indigo
        selectedTextColor: "white"
        horizontalAlignment: Qt.AlignHCenter
        verticalAlignment: Qt.AlignVCenter
        readOnly: !control.editable
        validator: control.validator
        inputMethodHints: Qt.ImhFormattedNumbersOnly
    }

    up.indicator: Rectangle {
        x: control.width - width
        height: control.height
        implicitWidth: 36
        color: control.up.pressed ? Theme.indigo : Theme.surf2
        border.color: Theme.border
        Text {
            text: "+"
            anchors.centerIn: parent
            color: Theme.text
            font.pixelSize: Theme.fsBody
            font.bold: true
        }
    }
    down.indicator: Rectangle {
        x: 0
        height: control.height
        implicitWidth: 36
        color: control.down.pressed ? Theme.indigo : Theme.surf2
        border.color: Theme.border
        Text {
            text: "−"
            anchors.centerIn: parent
            color: Theme.text
            font.pixelSize: Theme.fsBody
            font.bold: true
        }
    }
    background: Rectangle {
        implicitHeight: 40
        color: Theme.surf
        border.color: Theme.border
        radius: 6
    }
}
