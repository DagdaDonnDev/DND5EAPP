import QtQuick
import QtQuick.Controls
import Mimic

// A pick: its name and a short second line; on (teal, ✓), off, or one you
// already have (dashed -- press and hold to see where it's from).
Rectangle {
    id: t
    property string label: ""
    property string sub: ""
    property bool on: false
    property string have: ""
    property string tip: ""
    signal clicked()
    implicitHeight: sub.length > 0 ? 46 : 40
    radius: 7
    color: on ? Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.14) : have.length > 0 ? "transparent" : Theme.surf2
    border.color: on ? Theme.teal : Theme.border
    border.width: have.length > 0 ? 0 : 1

    Canvas {
        id: dashes
        anchors.fill: parent
        visible: t.have.length > 0
        onPaint: {
            var c = getContext("2d")
            c.reset()
            c.setLineDash([4, 3])
            c.strokeStyle = Theme.border2
            c.lineWidth = 1
            c.beginPath()
            c.roundedRect(0.5, 0.5, width - 1, height - 1, 7, 7)
            c.stroke()
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
    Column {
        anchors.centerIn: parent
        width: parent.width - 8
        Label {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: (t.on ? "✓ " : "") + t.label
            elide: Text.ElideRight
            color: t.on ? Theme.teal2 : t.have.length > 0 ? Theme.text3 : Theme.text2
            font.pixelSize: Theme.fsSmall
            font.bold: true
        }
        Label {
            visible: t.sub.length > 0
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: t.sub
            elide: Text.ElideRight
            color: t.on ? Theme.teal2 : Theme.text3
            font.pixelSize: Theme.fsSmall - 2
        }
    }
    ToolTip {
        id: tipPop
        timeout: 3500
        contentItem: Text {
            text: t.have.length > 0
                  ? "<b><font color='" + Theme.gold2 + "'>You already have " + t.label + "</font></b><br>from " + t.have
                  : t.tip
            textFormat: Text.RichText
            color: Theme.text
            font.pixelSize: Theme.fsSmall
            wrapMode: Text.WordWrap
        }
        background: Rectangle { color: Theme.surf3; border.color: Theme.border2; radius: 7 }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: if (t.have.length === 0) t.clicked()
        onPressAndHold: if (t.have.length > 0 || t.tip.length > 0) tipPop.open()
    }
}
