import QtQuick
import QtQuick.Controls
import Mimic

Page {
    id: root
    readonly property string screenTitle: Window.window.raceBridge.selectedRace
    background: Rectangle { color: Theme.bg }

    Flickable {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: 76
        contentWidth: width
        contentHeight: content.height
        clip: true

        Column {
            id: content
            width: parent.width
            spacing: 14

            Label {
                text: Window.window.raceBridge.raceAsiText
                color: Theme.teal2
                font.pixelSize: Theme.fsBody
                font.bold: true
                wrapMode: Text.WordWrap
                width: parent.width
            }
            Label {
                text: Window.window.raceBridge.raceSpeedSize
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
            }
            Label {
                text: "Source: " + Window.window.raceBridge.raceSource
                color: Theme.text3
                font.pixelSize: Theme.fsSmall
            }

            // ── Subrace ──────────────────────────────────────────────
            Label {
                visible: Window.window.raceBridge.subraceNames.length > 1
                text: "Subrace"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            ComboBox {
                id: subraceCombo
                visible: Window.window.raceBridge.subraceNames.length > 1
                width: parent.width
                model: Window.window.raceBridge.subraceNames
                onActivated: (idx) => {
                    const v = model[idx]
                    Window.window.raceBridge.selectSubrace(v === "(None)" ? "" : v)
                }
            }

            // ── Draconic Ancestry (Dragonborn only) ─────────────────
            Label {
                visible: Window.window.raceBridge.isDragonborn
                text: "Draconic Ancestry"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            ComboBox {
                visible: Window.window.raceBridge.isDragonborn
                width: parent.width
                model: Window.window.raceBridge.ancestryNames
                onActivated: (idx) => Window.window.raceBridge.selectAncestry(model[idx].split("  –")[0])
            }

            // ── Eladrin Season (Eladrin subrace of Elf only) ────────
            Label {
                visible: Window.window.raceBridge.isEladrin
                text: "Eladrin Season"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            ComboBox {
                visible: Window.window.raceBridge.isEladrin
                width: parent.width
                model: Window.window.raceBridge.eladrinSeasons
                onActivated: (idx) => Window.window.raceBridge.selectSeasonIndex(idx)
            }

            // ── Simic Hybrid Animal Enhancement ──────────────────────
            Label {
                visible: Window.window.raceBridge.isSimicHybrid
                text: "Animal Enhancement"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            ComboBox {
                visible: Window.window.raceBridge.isSimicHybrid
                width: parent.width
                model: Window.window.raceBridge.simicEnhancements
                onActivated: (idx) => Window.window.raceBridge.selectSimicIndex(idx)
            }

            Label {
                text: "Traits"
                color: Theme.gold
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
            Repeater {
                model: Window.window.raceBridge.raceTraits
                delegate: Label {
                    width: content.width
                    text: "•  " + modelData
                    color: Theme.text
                    font.pixelSize: Theme.fsBody
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    MButton {
        objectName: "confirmRaceButton"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 16
        text: "Confirm Race & Continue"
        onClicked: {
            if (Window.window.raceBridge.confirmRace()) {
                Window.window.advanceToAbilities()
            }
        }
    }
}
