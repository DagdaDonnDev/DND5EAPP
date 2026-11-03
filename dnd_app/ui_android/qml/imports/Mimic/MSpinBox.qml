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

    // Holding + or - steps by holdStep instead of 1 (snapping to its
    // multiples: 1 -> 5 -> 10 ...) -- for quantities. 1 keeps Qt's own
    // one-at-a-time repeat. While holding, stepSize drops to 0 so Qt's
    // built-in repeat does nothing and holdTimer does the stepping.
    property int holdStep: 1
    property bool holding: false
    stepSize: holding ? 0 : 1

    Timer {
        id: holdTimer
        property int ticks: 0
        interval: 150
        repeat: true
        running: control.holdStep > 1 && (control.up.pressed || control.down.pressed)
        onRunningChanged: { ticks = 0; control.holding = false }
        onTriggered: {
            // first step at 300ms -- the same moment Qt's own repeat starts,
            // so a quick tap is still +/- 1
            if (++ticks < 2)
                return
            control.holding = true
            var s = control.holdStep, v = control.value
            var next = control.up.pressed ? (Math.floor(v / s) + 1) * s
                                          : (Math.ceil(v / s) - 1) * s
            next = Math.max(Math.min(control.from, control.to),
                            Math.min(Math.max(control.from, control.to), next))
            if (next !== v) {
                control.value = next
                control.valueModified()
            }
        }
    }

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
        // gold while typing a number, like MTextField
        border.color: control.contentItem.activeFocus ? Theme.gold : Theme.border
        radius: 6
    }
}
