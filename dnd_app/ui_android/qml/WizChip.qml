import QtQuick
import QtQuick.Controls
import Mimic

// A small label in a tinted box: teal for what you gain, gold for a
// background's, grey for quieter facts, blue for the rest.
Rectangle {
    id: c
    property string text: ""
    property string kind: ""
    signal clicked()
    readonly property color tone: kind === "teal" ? Theme.teal2 : kind === "gold" ? Theme.gold2
                                 : kind === "off" ? Theme.text3 : kind === "red" ? Theme.crimson2 : Theme.indigo2
    implicitHeight: 30
    implicitWidth: lbl.implicitWidth + 20
    radius: 6
    color: Qt.rgba(tone.r, tone.g, tone.b, 0.11)
    border.color: Qt.rgba(tone.r, tone.g, tone.b, 0.55)
    Label {
        id: lbl
        anchors.centerIn: parent
        width: Math.min(implicitWidth, parent.width - 10)
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        text: c.text
        color: c.tone
        font.pixelSize: Theme.fsSmall - 1
        font.bold: true
    }
}
