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

    // Text never draws outside the button: when it doesn't fit it's cut
    // short with "…", or -- with wrapText -- wraps onto more lines and the
    // button grows taller (for long option text like a fighting style
    // with its description).
    property bool wrapText: false

    contentItem: Item {
        // natural (unwrapped, untruncated) size, so a button with no set
        // width still sizes itself to fit its text
        implicitWidth: (icon.visible ? icon.width + row.spacing : 0) + (label.visible ? label.implicitWidth : 0)
        implicitHeight: Math.max(icon.visible ? icon.height : 0, label.visible ? label.height : 0)
        Row {
            id: row
            // centred on the whole button: Material pads the left side more
            // than the right (24 vs 16), which pushed icons and text right
            anchors.centerIn: parent
            anchors.horizontalCenterOffset: (control.rightPadding - control.leftPadding) / 2
            spacing: 6
            MIcon {
                id: icon
                visible: control.iconName.length > 0
                name: control.iconName
                size: control.iconSize
                color: control.primary ? Theme.bg : Theme.indigo2
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                id: label
                visible: control.text.length > 0
                // may use the button's side padding (small buttons like
                // "View" rely on it) -- only a 6px margin each side is kept
                width: Math.min(implicitWidth,
                                Math.max(0, control.width - 12 - (icon.visible ? icon.width + row.spacing : 0)))
                text: control.text
                font.pixelSize: Theme.fsBody
                font.bold: true
                color: control.primary ? Theme.bg : Theme.text
                wrapMode: control.wrapText ? Text.WordWrap : Text.NoWrap
                elide: control.wrapText ? Text.ElideNone : Text.ElideRight
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
