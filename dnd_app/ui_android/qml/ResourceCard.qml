import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// One resource's card -- its name, where it's from and when it comes back,
// how many are left, and Use / Restore (Portent: its rolls to tap) -- for
// the Actions screen's Resources list and the Spells screen's Spell
// Resources. `res` is one of sheetBridge.resources' rows.
Rectangle {
    id: card
    property var res: ({name: "", sourceClass: "", reset: "", key: "", current: 0, currentMax: 0,
                        unlimited: false, rolls: [], toggleEffect: "", toggleActive: false})
    implicitHeight: resCol.height + 20
    radius: 10
    color: Theme.surf
    border.color: Theme.border

    ColumnLayout {
        id: resCol
        x: 10; y: 10
        width: parent.width - 20
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: res.name
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Label {
                    text: res.sourceClass + (res.reset ? "  ·  " + res.reset : "")
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                }
            }
            Label {
                text: res.unlimited ? "∞" : (res.current + " / " + res.currentMax)
                color: Theme.teal2
                font.pixelSize: Theme.fsBody
                font.bold: true
            }
        }
        // Portent: the foretelling rolls themselves; tapping one uses it
        Label {
            visible: res.key === "portent"
            text: res.rolls.length > 0 ? "Tap a roll to use it as the d20"
                                              : "No rolls left until your next long rest"
            color: Theme.text3
            font.pixelSize: Theme.fsSmall
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        Flow {
            visible: res.key === "portent" && res.rolls.length > 0
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: res.rolls
                delegate: MButton {
                    primary: false
                    height: 32
                    text: String(modelData)
                    onClicked: sheetBridge.usePortentRoll(modelData)
                }
            }
        }
        Flow {
            visible: !res.unlimited && res.key !== "portent"
            Layout.fillWidth: true
            spacing: 8
            MButton {
                primary: false
                height: 32
                text: "Use"
                enabled: res.current > 0
                onClicked: sheetBridge.spendResource(res.key)
            }
            MButton {
                primary: false
                height: 32
                text: "Restore"
                onClicked: sheetBridge.restoreResource(res.key)
            }
            MToggleButton {
                visible: res.toggleEffect.length > 0
                active: res.toggleActive
                onClicked: sheetBridge.toggleResourceEffect(res.key)
            }
        }
    }
}
