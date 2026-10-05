import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Compact identity strip repeated at the top of every Character Sheet
// sub-page (Combat/Abilities/Proficiencies/Spells/Equipment/Choices/
// Notes/Infusions). Desktop keeps this visible across every tab via
// persistent chrome around a QTabWidget; Android's sheet pages are
// separate StackView destinations with no shared chrome area, so each
// one embeds this instead of losing the "whose sheet am I looking at"
// context when jumping between them via the drawer.
ColumnLayout {
    readonly property QtObject sheetBridge: Window.window.sheetBridge
    Layout.fillWidth: true
    spacing: 2

    Label {
        text: sheetBridge.name || "Unnamed Character"
        color: Theme.gold2
        font.pixelSize: Theme.fsHead
        font.bold: true
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Label {
        text: [sheetBridge.raceText, sheetBridge.classesText, sheetBridge.background]
              .filter(s => s.length > 0).join("  ·  ")
        color: Theme.text2
        font.pixelSize: Theme.fsSmall
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
}
