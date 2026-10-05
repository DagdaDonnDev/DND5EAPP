import QtQuick

// TextField (QtQuick.Templates) is a QQuickTextInput subclass, not a
// Control -- it has no `contentItem` to override (confirmed: only
// `background`/`placeholderText`/font/color are real properties on it).
// Material's own TextField.qml style draws its floating-label
// placeholder as a second item layered on top of the field's own native
// placeholder rendering, and in this app the two don't line up --
// confirmed via a real screenshot showing "Search magic items…"
// overlapping/running into typed text instead of being replaced by it.
// Bypassing Controls' TextField entirely (a plain Item + TextInput +
// one hand-drawn placeholder Text) sidesteps both layers at once.
Item {
    id: control

    property alias text: input.text
    property string placeholderText: ""
    property alias font: input.font
    property color color: Theme.text
    property color selectionColor: Theme.indigo
    property color selectedTextColor: "white"
    property alias readOnly: input.readOnly
    property alias validator: input.validator
    property alias inputMethodHints: input.inputMethodHints
    property alias horizontalAlignment: input.horizontalAlignment
    readonly property bool inputHasFocus: input.activeFocus

    signal accepted()
    signal editingFinished()

    implicitWidth: 200
    implicitHeight: 44

    function forceActiveFocus() { input.forceActiveFocus() }
    function selectAll() { input.selectAll() }

    Rectangle {
        anchors.fill: parent
        radius: 8
        color: Theme.surf
        border.color: input.activeFocus ? Theme.gold : Theme.border
        border.width: input.activeFocus ? 2 : 1
    }

    Text {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        text: control.placeholderText
        color: Theme.text3
        font: input.font
        elide: Text.ElideRight
        visible: input.text.length === 0
    }

    TextInput {
        id: input
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        verticalAlignment: TextInput.AlignVCenter
        clip: true
        selectByMouse: true
        font.pixelSize: Theme.fsBody
        color: control.color
        selectionColor: control.selectionColor
        selectedTextColor: control.selectedTextColor
        onAccepted: control.accepted()
        onEditingFinished: control.editingFinished()
    }
}
