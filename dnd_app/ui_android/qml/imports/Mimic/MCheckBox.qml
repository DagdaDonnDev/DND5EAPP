import QtQuick
import QtQuick.Controls

// A themed labeled checkbox. Same rationale as MButton/MSpinBox: relying
// on a custom contentItem's `leftPadding: parent.indicator.width + 6`
// to line up with Material's own default indicator is fragile -- caught
// via a real screenshot showing the (checked-state) indicator glyph
// rendered on top of the first few letters of the label instead of
// beside it. Giving both the indicator AND the contentItem fixed,
// explicit geometry here removes that dependency entirely.
CheckBox {
    id: control

    indicator: Rectangle {
        x: control.leftPadding
        y: (control.height - height) / 2
        width: 20
        height: 20
        radius: 4
        color: control.checked ? Theme.gold : Theme.surf2
        border.color: control.checked ? Theme.gold : Theme.border
        border.width: 1

        Text {
            anchors.centerIn: parent
            visible: control.checked
            text: "✓"
            color: Theme.bg
            font.pixelSize: 14
            font.bold: true
        }
    }

    contentItem: Label {
        text: control.text
        color: Theme.text2
        font.pixelSize: Theme.fsSmall
        leftPadding: control.indicator.width + 8
        verticalAlignment: Text.AlignVCenter
        // Wraps once the control's width is externally constrained
        // (Layout.fillWidth: true) -- without that, availableWidth
        // just tracks the label's own natural (unwrapped) width, same
        // as before, so this is a no-op for existing short-label
        // checkboxes elsewhere in the app. Needed once real option
        // text (Settings' per-rule toggles) got long enough to run
        // the whole control past the screen edge.
        wrapMode: Text.WordWrap
        width: control.availableWidth
    }
}
