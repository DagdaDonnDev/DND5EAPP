import QtQuick
import QtQuick.Controls
import Mimic

// Content for the Credits MFullPageDialog (see App.qml) -- not a
// Page/StackView destination itself, the dialog supplies the chrome
// (title bar + close button). Renders the project's root README.md
// (see bridge/credits.py) as Markdown, same source of truth desktop's
// CreditsDialog reads.
Flickable {
    id: root
    readonly property QtObject creditsBridge: Window.window.creditsBridge
    anchors.fill: parent
    anchors.margins: 16
    contentWidth: width
    contentHeight: readmeText.height
    clip: true

    Text {
        id: readmeText
        width: parent.width
        textFormat: Text.MarkdownText
        wrapMode: Text.WordWrap
        color: Theme.text
        font.pixelSize: Theme.fsSmall
        text: creditsBridge.readmeText

        onLinkActivated: (link) => Qt.openUrlExternally(link)
    }
}
