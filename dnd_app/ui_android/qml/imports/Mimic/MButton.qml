import QtQuick
import QtQuick.Controls

// A themed primary/secondary action button. Doesn't rely on Material's
// default filled-button chrome for `highlighted: true` -- that chrome
// depends on an elevation/shadow effect that renders as a fully
// invisible (no fill, no border) button under this app's offscreen
// test harness, confirmed via isolated reproduction outside any of
// this app's own QML. Painting the fill explicitly sidesteps that
// entirely and keeps every "Confirm X" button on-brand (gold pill)
// instead of Material's generic blue/teal.
Button {
    id: control
    property bool primary: true
    // Optional line icon (see MIcon / IconData.js) shown before the text,
    // or on its own when the button has no text. Same colour as the text
    // on a gold primary button; the theme accent on a secondary one.
    property string iconName: ""
    property real iconSize: 18

    // Material pads every Button with 6px top/bottom insets, so the
    // painted button was 12px shorter than its height -- a "height: 32"
    // button drew at 20px, which made buttons across the app look
    // squashed. Zero insets: a button is drawn at the size it's given
    // (its touch area is unchanged).
    topInset: 0
    bottomInset: 0

    contentItem: Item {
        implicitWidth: row.implicitWidth
        implicitHeight: row.implicitHeight
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 6
            MIcon {
                visible: control.iconName.length > 0
                name: control.iconName
                size: control.iconSize
                color: control.primary ? Theme.bg : Theme.indigo2
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                visible: control.text.length > 0
                text: control.text
                font.pixelSize: Theme.fsBody
                font.bold: true
                color: control.primary ? Theme.bg : Theme.text
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    background: Rectangle {
        implicitHeight: 40
        // Same corner radius as MToggleButton's Active/Inactive button --
        // a blockier, less pill-like rounded-rect reads more consistent
        // across the app than the two shapes sitting side by side with
        // slightly different roundedness (e.g. a Resources row's Use/
        // Restore buttons next to an Active toggle).
        radius: 8
        color: control.primary
            ? (control.pressed ? Qt.darker(Theme.gold, 1.15) : Theme.gold)
            : (control.pressed ? Theme.surf3 : Theme.surf2)
        border.color: control.primary ? "transparent" : Theme.border
        border.width: control.primary ? 0 : 1
        opacity: control.enabled ? 1.0 : 0.5
    }
}
