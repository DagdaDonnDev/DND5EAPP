import QtQuick
import QtQuick.Controls

// A fixed-size "Inactive"/"Active" toggle button for class/subclass
// forms tracked via active_effects (Rage, Bladesong, Hexblade's Curse,
// etc.). Replaces an earlier CheckBox+label version -- even after
// fixing that checkbox's indicator/label overlap, a plain button reads
// more clearly at a glance and needs no indicator-geometry math at all.
// Static width/height sized to comfortably fit either label so the
// button never resizes when toggled.
Button {
    id: control
    property bool active: false

    implicitWidth: 110
    implicitHeight: 36
    // see MButton: no Material insets, so it draws at its full height
    topInset: 0
    bottomInset: 0

    contentItem: Text {
        text: control.active ? "Active" : "Inactive"
        color: control.active ? Theme.bg : Theme.text2
        font.pixelSize: Theme.fsSmall
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: 8
        color: control.active ? Theme.crimson2 : Theme.surf2
        border.color: control.active ? Theme.crimson2 : Theme.border
        border.width: 1
        opacity: control.pressed ? 0.8 : 1.0
    }
}
