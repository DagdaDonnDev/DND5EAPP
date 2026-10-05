import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Background & Class"
    background: Rectangle { color: Theme.bg }
    readonly property QtObject classBridge: Window.window.classBridge

    Component.onCompleted: classBridge.refresh()

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: width
        contentHeight: content.height
        clip: true

        Column {
            id: content
            width: parent.width
            spacing: 14

            Label {
                visible: classBridge.classConfirmedOnce
                text: "Background & class confirmed  ✓"
                color: Theme.teal2
                font.pixelSize: Theme.fsBody
                font.bold: true
            }

            // ── Name ───────────────────────────────────────────────
            Label { text: "Character Name"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            MTextField {
                width: parent.width
                placeholderText: "Enter name…"
                text: classBridge.name
                onEditingFinished: classBridge.setName(text)
            }

            // ── Alignment ──────────────────────────────────────────
            Label { text: "Alignment"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            ComboBox {
                width: parent.width
                model: classBridge.alignments
                currentIndex: classBridge.alignments.indexOf(classBridge.alignment)
                onActivated: (idx) => classBridge.setAlignment(classBridge.alignments[idx])
            }

            // ── Background (searchable) ───────────────────────────
            Label { text: "Background"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            Label {
                visible: classBridge.selectedBackground.length > 0
                text: "Selected: " + classBridge.selectedBackground
                color: Theme.teal2
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            MTextField {
                id: bgSearch
                objectName: "backgroundSearchField"
                width: parent.width
                placeholderText: "Search backgrounds…"
                onTextChanged: classBridge.backgroundModel.setFilter(text)
            }
            Rectangle {
                width: parent.width
                height: 220
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                clip: true
                ListView {
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    model: classBridge.backgroundModel
                    delegate: ItemDelegate {
                        objectName: "bgItem_" + name
                        width: ListView.view.width
                        height: 44
                        contentItem: Row {
                            spacing: 10
                            anchors.verticalCenter: parent.verticalCenter
                            Label {
                                text: name
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: name === classBridge.selectedBackground
                            }
                            Label {
                                text: source
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                            }
                        }
                        background: Rectangle {
                            color: name === classBridge.selectedBackground ? Qt.rgba(Theme.indigo.r, Theme.indigo.g, Theme.indigo.b, 0.18) : "transparent"
                        }
                        onClicked: classBridge.selectBackground(name)
                    }
                }
            }

            Label {
                visible: classBridge.selectedBackground.length > 0
                text: classBridge.backgroundSkillsText
                color: Theme.teal2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                width: parent.width
            }
            Rectangle {
                visible: classBridge.selectedBackground.length > 0
                width: parent.width
                height: bgDetailLabel.height + 20
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                Label {
                    id: bgDetailLabel
                    x: 10; y: 10
                    width: parent.width - 20
                    text: classBridge.backgroundDetailText
                    color: Theme.text
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                }
            }

            // ── Background feat (only for backgrounds that grant one) ──
            Label {
                visible: classBridge.showBackgroundFeatPicker
                text: "Background Feat"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            ComboBox {
                visible: classBridge.showBackgroundFeatPicker
                width: parent.width
                model: classBridge.backgroundFeatChoices
                currentIndex: classBridge.backgroundFeatChoices.indexOf(classBridge.selectedBackgroundFeat)
                onActivated: (idx) => classBridge.selectBackgroundFeat(classBridge.backgroundFeatChoices[idx])
            }

            // ── Starting Class ─────────────────────────────────────
            Label { text: "Starting Class"; color: Theme.gold; font.pixelSize: Theme.fsSmall; font.bold: true }
            ComboBox {
                width: parent.width
                model: classBridge.classNames
                currentIndex: classBridge.classNames.indexOf(classBridge.selectedClass)
                onActivated: (idx) => classBridge.selectClass(classBridge.classNames[idx])
            }
            Label {
                visible: classBridge.selectedClass.length > 0
                text: classBridge.classInfoText
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                width: parent.width
            }

            Label {
                visible: classBridge.errorMessage.length > 0
                text: classBridge.errorMessage
                color: Theme.crimson2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                width: parent.width
            }

            MButton {
                objectName: "confirmClassButton"
                width: parent.width
                text: "Confirm & Continue"
                onClicked: {
                    if (classBridge.confirmClass()) {
                        Window.window.advanceToEquipment()
                    }
                }
            }
        }
    }
}
