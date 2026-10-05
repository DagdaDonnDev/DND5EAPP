import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

Page {
    id: root
    readonly property string screenTitle: "Ability Scores"
    background: Rectangle { color: Theme.bg }

    Component.onCompleted: Window.window.abilityBridge.refresh()

    function cardStyle(borderColor) {
        return borderColor
    }

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
                visible: Window.window.abilityBridge.abilitiesConfirmedOnce
                text: "Ability scores confirmed  ✓"
                color: Theme.teal2
                font.pixelSize: Theme.fsBody
                font.bold: true
            }

            Label {
                text: "Set your base ability scores, then apply racial and ASI bonuses below."
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                width: parent.width
            }

            // ── Method selector ──────────────────────────────────────
            Label {
                text: "Method"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            ComboBox {
                id: methodCombo
                width: parent.width
                model: Window.window.abilityBridge.methodNames
                currentIndex: Window.window.abilityBridge.methodIndex
                onActivated: (idx) => Window.window.abilityBridge.selectMethodIndex(idx)
            }

            // ── Manual / Point Buy: editable base scores ─────────────
            Rectangle {
                visible: Window.window.abilityBridge.methodIsManual || Window.window.abilityBridge.methodIsPointBuy
                width: parent.width
                height: abGrid.height + 24
                radius: 10
                color: Theme.surf
                border.color: Theme.border
                Grid {
                    id: abGrid
                    anchors.centerIn: parent
                    columns: 3
                    rowSpacing: 10
                    columnSpacing: 10
                    Repeater {
                        model: Window.window.abilityBridge.abilityNames
                        delegate: Column {
                            spacing: 2
                            width: 110
                            Label {
                                text: modelData
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                            MSpinBox {
                                width: 100
                                from: 1
                                to: 20
                                value: Window.window.abilityBridge.baseScores[modelData]
                                onValueModified: Window.window.abilityBridge.setBaseScore(modelData, value)
                            }
                        }
                    }
                }
            }

            Label {
                visible: Window.window.abilityBridge.methodIsPointBuy
                text: "Points remaining: " + Window.window.abilityBridge.pointBuyRemaining + " / 27"
                color: Window.window.abilityBridge.pointBuyRemaining >= 0 ? Theme.gold2 : Theme.crimson2
                font.pixelSize: Theme.fsBody
                font.bold: true
            }

            // ── Standard Array: assign each value to one ability ─────
            Rectangle {
                visible: Window.window.abilityBridge.methodIsStandardArray
                width: parent.width
                height: saCol.height + 24
                radius: 10
                color: Theme.surf
                border.color: Theme.gold
                Column {
                    id: saCol
                    x: 12; y: 12
                    width: parent.width - 24
                    spacing: 8
                    Label {
                        text: "Assign each value to one ability:"
                        color: Theme.gold
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                    }
                    Repeater {
                        model: Window.window.abilityBridge.abilityNames
                        delegate: RowLayout {
                            width: saCol.width
                            Label {
                                text: modelData
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                                Layout.preferredWidth: 60
                            }
                            ComboBox {
                                Layout.fillWidth: true
                                model: Window.window.abilityBridge.standardArrayValues
                                currentIndex: Window.window.abilityBridge.standardArrayValues.indexOf(Window.window.abilityBridge.standardArrayAssignment[modelData])
                                onActivated: (idx) => Window.window.abilityBridge.setStandardArrayValue(modelData, Window.window.abilityBridge.standardArrayValues[idx])
                            }
                        }
                    }
                }
            }

            // ── Tasha's Reassignment ──────────────────────────────────
            Rectangle {
                visible: Window.window.abilityBridge.methodIsTashas
                width: parent.width
                height: tashasCol.height + 24
                radius: 10
                color: Theme.surf
                border.color: Theme.gold
                Column {
                    id: tashasCol
                    x: 12; y: 12
                    width: parent.width - 24
                    spacing: 8
                    Label {
                        text: "Redistribute your racial ASI points to any abilities. All other racial traits are unchanged."
                        color: Theme.teal2
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        width: parent.width
                    }
                    Label {
                        text: "Points used: " + Window.window.abilityBridge.tashasUsed + " / " + Window.window.abilityBridge.tashasPool
                        color: Window.window.abilityBridge.tashasUsed === Window.window.abilityBridge.tashasPool ? Theme.teal2 : Theme.gold2
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                    }
                    Repeater {
                        model: Window.window.abilityBridge.abilityNames
                        delegate: RowLayout {
                            width: tashasCol.width
                            Label {
                                text: modelData
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                                Layout.preferredWidth: 60
                            }
                            MSpinBox {
                                Layout.fillWidth: true
                                from: 0
                                to: Math.max(1, Window.window.abilityBridge.tashasPool)
                                value: Window.window.abilityBridge.tashasPoints[modelData]
                                onValueModified: Window.window.abilityBridge.setTashasPoints(modelData, value)
                            }
                        }
                    }
                }
            }

            // ── Racial ASI preview ────────────────────────────────────
            Rectangle {
                width: parent.width
                height: raceCol.height + 24
                radius: 10
                color: Theme.surf
                border.color: Theme.teal
                Column {
                    id: raceCol
                    x: 12; y: 12
                    width: parent.width - 24
                    spacing: 4
                    Label {
                        text: "Racial Ability Score Increases"
                        color: Theme.teal2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                    }
                    Label {
                        text: Window.window.abilityBridge.racialAsiText
                        color: Theme.text2
                        font.pixelSize: Theme.fsBody
                        wrapMode: Text.WordWrap
                        width: parent.width
                    }
                }
            }

            // ── Flex ASI picker (each-style, e.g. Half-Elf) ──────────
            Rectangle {
                visible: Window.window.abilityBridge.showFlexPicker
                width: parent.width
                height: flexCol.height + 24
                radius: 10
                color: Theme.surf
                border.color: Theme.indigo
                Column {
                    id: flexCol
                    x: 12; y: 12
                    width: parent.width - 24
                    spacing: 8
                    Label {
                        text: Window.window.abilityBridge.flexLabel
                        color: Theme.indigo2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        width: parent.width
                    }
                    Flow {
                        width: parent.width
                        spacing: 8
                        Repeater {
                            model: Window.window.abilityBridge.abilityNames
                            delegate: MCheckBox {
                                objectName: "flexPick_" + modelData
                                text: modelData
                                checked: Window.window.abilityBridge.flexPicks.indexOf(modelData) >= 0
                                onClicked: Window.window.abilityBridge.toggleFlexPick(modelData)
                            }
                        }
                    }
                }
            }

            // ── Distribute ASI picker (2024/MPMM-style) ──────────────
            Rectangle {
                visible: Window.window.abilityBridge.showDistPicker
                width: parent.width
                height: distCol.height + 24
                radius: 10
                color: Theme.surf
                border.color: Theme.indigo
                Column {
                    id: distCol
                    x: 12; y: 12
                    width: parent.width - 24
                    spacing: 8
                    Label {
                        text: "Ability Score Increase — choose one option:"
                        color: Theme.indigo2
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                        wrapMode: Text.WordWrap
                        width: parent.width
                    }
                    RadioButton {
                        id: distRadioA
                        width: distCol.width
                        checked: Window.window.abilityBridge.distOptionA
                        onClicked: Window.window.abilityBridge.selectDistOptionA(true)
                        text: "(a) +2 to one ability, +1 to a different ability"
                        contentItem: Text {
                            text: distRadioA.text
                            color: Theme.text
                            font.pixelSize: Theme.fsBody
                            wrapMode: Text.WordWrap
                            leftPadding: distRadioA.indicator.width + distRadioA.spacing
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                    RowLayout {
                        width: distCol.width
                        enabled: Window.window.abilityBridge.distOptionA
                        Label { text: "+2:"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                        ComboBox {
                            Layout.fillWidth: true
                            model: Window.window.abilityBridge.abilityNames
                            currentIndex: Window.window.abilityBridge.abilityNames.indexOf(Window.window.abilityBridge.distPlus2Ability)
                            onActivated: (idx) => Window.window.abilityBridge.setDistPlus2(Window.window.abilityBridge.abilityNames[idx])
                        }
                        Label { text: "+1:"; color: Theme.text2; font.pixelSize: Theme.fsSmall }
                        ComboBox {
                            Layout.fillWidth: true
                            model: Window.window.abilityBridge.abilityNames
                            currentIndex: Window.window.abilityBridge.abilityNames.indexOf(Window.window.abilityBridge.distPlus1Ability)
                            onActivated: (idx) => Window.window.abilityBridge.setDistPlus1(Window.window.abilityBridge.abilityNames[idx])
                        }
                    }
                    RadioButton {
                        id: distRadioB
                        width: distCol.width
                        checked: !Window.window.abilityBridge.distOptionA
                        onClicked: Window.window.abilityBridge.selectDistOptionA(false)
                        text: "(b) +1 to three different abilities"
                        contentItem: Text {
                            text: distRadioB.text
                            color: Theme.text
                            font.pixelSize: Theme.fsBody
                            wrapMode: Text.WordWrap
                            leftPadding: distRadioB.indicator.width + distRadioB.spacing
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                    Flow {
                        width: parent.width
                        spacing: 8
                        enabled: !Window.window.abilityBridge.distOptionA
                        Repeater {
                            model: Window.window.abilityBridge.abilityNames
                            delegate: MCheckBox {
                                text: modelData
                                checked: Window.window.abilityBridge.distTriplePicks.indexOf(modelData) >= 0
                                onClicked: Window.window.abilityBridge.toggleDistTriplePick(modelData)
                            }
                        }
                    }
                }
            }

            // ── Totals ─────────────────────────────────────────────────
            Rectangle {
                width: parent.width
                height: totalsGrid.height + 20
                radius: 10
                color: Theme.surf2
                border.color: Theme.border
                Grid {
                    id: totalsGrid
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 10
                    columns: 3
                    rowSpacing: 8
                    columnSpacing: 10
                    Repeater {
                        model: Window.window.abilityBridge.abilityNames
                        delegate: Column {
                            spacing: 2
                            width: 100
                            Label {
                                text: modelData
                                color: Theme.text3
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                            Label {
                                text: Window.window.abilityBridge.totals[modelData] || ""
                                color: Theme.text
                                font.pixelSize: Theme.fsSmall
                                font.bold: true
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                        }
                    }
                }
            }

            Label {
                visible: Window.window.abilityBridge.errorMessage.length > 0
                text: Window.window.abilityBridge.errorMessage
                color: Theme.crimson2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                width: parent.width
            }

            MButton {
                objectName: "confirmAbilitiesButton"
                width: parent.width
                text: "Confirm & Continue"
                onClicked: {
                    if (Window.window.abilityBridge.confirmAbilities()) {
                        Window.window.advanceToClass()
                    }
                }
            }
        }
    }
}
