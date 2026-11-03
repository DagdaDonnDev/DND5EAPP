import QtQuick

// Multi-line counterpart to MTextField, built the same way (a plain
// TextEdit plus a hand-drawn box and placeholder) to sidestep Material
// TextArea's floating-label placeholder, which sits on top of the
// border once there's text. Grows with its text instead of scrolling
// inside itself -- the page's own Flickable does the scrolling.
Item {
    id: control

    property alias text: edit.text
    property string placeholderText: ""
    property alias font: edit.font
    property color color: Theme.text
    property real minimumHeight: 70
    // Cursor position in this item's own coordinates, so a page can keep
    // the line being typed in view as the box grows.
    readonly property rect cursorRectangle: Qt.rect(
        edit.x + edit.cursorRectangle.x, edit.y + edit.cursorRectangle.y,
        edit.cursorRectangle.width, edit.cursorRectangle.height)
    readonly property bool inputHasFocus: edit.activeFocus

    signal editingFinished()

    implicitWidth: 200
    implicitHeight: Math.max(minimumHeight, edit.contentHeight + 2 * edit.y)

    function forceActiveFocus() { edit.forceActiveFocus() }

    Rectangle {
        anchors.fill: parent
        radius: 8
        color: Theme.surf
        border.color: edit.activeFocus ? Theme.gold : Theme.border
        border.width: edit.activeFocus ? 2 : 1
    }

    Text {
        x: edit.x
        y: edit.y
        width: edit.width
        text: control.placeholderText
        color: Theme.text3
        font: edit.font
        wrapMode: Text.WordWrap
        visible: edit.text.length === 0 && !edit.preeditText
    }

    TextEdit {
        id: edit
        x: 12
        y: 10
        width: parent.width - 24
        wrapMode: TextEdit.Wrap
        selectByMouse: true
        font.pixelSize: Theme.fsBody
        color: control.color
        selectionColor: Theme.indigo
        selectedTextColor: "white"
        onEditingFinished: control.editingFinished()
    }

    // Taps anywhere in the box (not just on existing lines) focus it.
    MouseArea {
        anchors.fill: parent
        z: -1
        onClicked: {
            edit.forceActiveFocus()
            edit.cursorPosition = edit.length
        }
    }
}
