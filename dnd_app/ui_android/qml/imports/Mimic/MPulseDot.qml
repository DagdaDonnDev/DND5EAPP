import QtQuick

// A small dot in the theme's own accent color, with a soft halo that breathes in and out while
// `running` -- marks something that needs the player's attention
// (pending level-up choices: the header's menu button, the drawer's
// Choices row, the Choices tab). Hidden, with its animations stopped,
// when not running, so an idle dot costs nothing.
Item {
    id: root
    property bool running: false
    property color color: Theme.indigo2
    property real diameter: 9
    property int period: 1400

    implicitWidth: diameter * 2.4
    implicitHeight: diameter * 2.4
    visible: running

    // Halo: grows and fades out each cycle.
    Rectangle {
        id: halo
        anchors.centerIn: parent
        width: root.diameter
        height: width
        radius: width / 2
        color: root.color
        opacity: 0
        SequentialAnimation {
            running: root.running
            loops: Animation.Infinite
            ParallelAnimation {
                NumberAnimation { target: halo; property: "width"; from: root.diameter; to: root.diameter * 2.4; duration: root.period; easing.type: Easing.OutCubic }
                NumberAnimation { target: halo; property: "opacity"; from: 0.55; to: 0; duration: root.period; easing.type: Easing.OutCubic }
            }
        }
    }

    // Core dot: brightens and dims in step with the halo.
    Rectangle {
        id: dot
        anchors.centerIn: parent
        width: root.diameter
        height: width
        radius: width / 2
        color: root.color
        SequentialAnimation on opacity {
            running: root.running
            loops: Animation.Infinite
            NumberAnimation { from: 1.0; to: 0.45; duration: root.period / 2; easing.type: Easing.InOutSine }
            NumberAnimation { from: 0.45; to: 1.0; duration: root.period / 2; easing.type: Easing.InOutSine }
        }
    }
}
