import QtQuick
import QtQuick.Controls
import Mimic

// Wizard step 4: what level 1 asks you to pick (a subclass, skills,
// Expertise, languages, tools...) and, for a class that casts, your
// starting spells -- two tabs, each saying how many are left. Called
// "Choices" for a class with no spells.
Page {
    id: root
    readonly property var wb: Window.window.wizardBridge
    readonly property int rev: wb ? wb.rev : 0
    readonly property string screenTitle: wb ? wb.spellsStepName : "Spells & Choices"
    readonly property var cards: { rev; return wb ? wb.level1Cards() : [] }
    readonly property var plan: { rev; return wb ? wb.spellPlan() : ({}) }
    readonly property bool hasSpells: plan.tabs !== undefined
    readonly property var leftList: { rev; return wb ? wb.level1Left() : [] }
    property string tab: "choices"
    background: Rectangle { color: Theme.bg }

    function kidsOf(id) { return cards.filter(function(c) { return c.parent === id }) }
    function choicesLeft() {
        var n = 0
        for (var i = 0; i < cards.length; ++i) n += cards[i].left
        return n
    }
    function spellsLeft() {
        var n = 0
        var t = plan.tabs || []
        for (var i = 0; i < t.length; ++i) n += Math.max(0, t[i].count - t[i].picked)
        return n
    }
    function androidCols(c) {
        if (c.kind === "subclass") return 2
        if (c.cols === 5) return 5
        if (c.cols === 2) return 2
        return 3
    }

    WizSteps { id: steps; step: 3; width: parent.width }

    Row {
        id: tabs
        visible: root.hasSpells
        anchors.top: steps.bottom; anchors.topMargin: 10
        x: 12
        width: parent.width - 24
        height: visible ? 36 : 0
        spacing: 0
        Repeater {
            model: [["choices", "Choices", root.choicesLeft()], ["spells", "Spells", root.spellsLeft()]]
            delegate: Rectangle {
                objectName: "wizTab_" + modelData[0]
                readonly property bool on: root.tab === modelData[0]
                width: tabs.width / 2; height: 36
                radius: 8
                color: on ? Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.14) : Theme.surf2
                border.color: Theme.border
                Row {
                    anchors.centerIn: parent
                    spacing: 6
                    Label { text: modelData[1]; color: parent.parent.on ? Theme.gold2 : Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                    Rectangle {
                        readonly property color tone: modelData[2] > 0 ? Theme.gold2 : Theme.teal2
                        width: cl.implicitWidth + 12; height: 18; radius: 9
                        color: Qt.rgba(tone.r, tone.g, tone.b, 0.15)
                        anchors.verticalCenter: parent.verticalCenter
                        Label { id: cl; anchors.centerIn: parent; text: modelData[2] > 0 ? modelData[2] + " left" : "done"; color: parent.tone; font.pixelSize: Theme.fsSmall - 2; font.bold: true }
                    }
                }
                MouseArea { anchors.fill: parent; onClicked: root.tab = modelData[0] }
            }
        }
    }

    // ── the picks ──
    Flickable {
        visible: root.tab === "choices" || !root.hasSpells
        anchors.top: tabs.bottom; anchors.bottom: nav.top
        anchors.left: parent.left; anchors.right: parent.right
        contentHeight: content.height + 24
        clip: true
        Column {
            id: content
            x: 12; y: 10
            width: parent.width - 24
            spacing: 8
            Repeater {
                model: root.cards.filter(function(c) { return c.parent === "" })
                delegate: WizCard {
                    id: card
                    objectName: "choiceCard_" + modelData.id
                    width: content.width
                    readonly property var c: modelData
                    title: c.title
                    sub: c.sub
                    count: c.picked.length + " of " + c.count
                    done: c.done
                    ChoiceTiles { width: card.width - 20; c: card.c; cols: root.androidCols(card.c); wb: root.wb; picker: pickerDialog }
                    Repeater {
                        model: root.kidsOf(card.c.id)
                        delegate: WizCard {
                            inner: true
                            width: card.width - 20
                            title: modelData.title
                            count: modelData.done ? "picked" : "pick one"
                            done: modelData.done
                            ChoiceTiles { width: card.width - 40; c: modelData; cols: root.androidCols(modelData); wb: root.wb; picker: pickerDialog }
                        }
                    }
                }
            }
        }
    }

    // ── the spells ──
    Item {
        visible: root.tab === "spells" && root.hasSpells
        anchors.top: tabs.bottom; anchors.bottom: nav.top
        anchors.left: parent.left; anchors.right: parent.right
        Column {
            id: sTop
            x: 12; y: 10
            width: parent.width - 24
            spacing: 8
            Row {
                width: parent.width
                spacing: 6
                Repeater {
                    model: root.plan.tabs || []
                    delegate: Rectangle {
                        objectName: "spellTab_" + modelData.key
                        readonly property bool on: root.plan.tab === modelData.key
                        width: (sTop.width - 6) / 2; height: 34; radius: 8
                        color: on ? Qt.rgba(Theme.gold.r, Theme.gold.g, Theme.gold.b, 0.12) : Theme.surf2
                        border.color: on ? Theme.gold : Theme.border
                        Row {
                            anchors.centerIn: parent
                            spacing: 6
                            Label { text: modelData.title; color: parent.parent.on ? Theme.gold2 : Theme.text2; font.pixelSize: Theme.fsSmall; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                            Rectangle {
                                readonly property color tone: modelData.picked >= modelData.count ? Theme.teal2 : Theme.gold2
                                width: sc.implicitWidth + 12; height: 18; radius: 9
                                color: Qt.rgba(tone.r, tone.g, tone.b, 0.15)
                                anchors.verticalCenter: parent.verticalCenter
                                Label { id: sc; anchors.centerIn: parent; text: modelData.picked + "/" + modelData.count; color: parent.tone; font.pixelSize: Theme.fsSmall - 2; font.bold: true }
                            }
                        }
                        MouseArea { anchors.fill: parent; onClicked: root.wb.setSpellTab(modelData.key) }
                    }
                }
            }
            MTextField {
                width: parent.width
                placeholderText: "⌕  Search " + (root.plan.tab === "cantrips" ? "cantrips…" : "spells…")
                Component.onCompleted: text = root.wb ? root.wb.spellSearch : ""
                onTextChanged: if (root.wb) root.wb.setSpellSearch(text)
            }
        }
        ListView {
            anchors.top: sTop.bottom; anchors.topMargin: 8
            anchors.bottom: parent.bottom
            x: 12
            width: parent.width - 24
            clip: true
            spacing: 4
            model: { root.rev; return root.wb ? root.wb.spellRows() : [] }
            delegate: Rectangle {
                objectName: "spellRow_" + modelData.name
                width: ListView.view.width
                height: 42
                radius: 8
                color: modelData.on ? Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.12) : Theme.surf
                border.color: modelData.on ? Theme.teal : Theme.border
                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 10; anchors.rightMargin: 10
                    spacing: 10
                    Rectangle {
                        width: 18; height: 18; radius: 4
                        anchors.verticalCenter: parent.verticalCenter
                        color: modelData.on ? Theme.teal : "transparent"
                        border.color: modelData.on ? Theme.teal : Theme.border2
                        Label { anchors.centerIn: parent; visible: modelData.on; text: "✓"; color: Theme.onFill(Theme.teal); font.bold: true; font.pixelSize: Theme.fsSmall - 1 }
                    }
                    Label {
                        width: parent.width - 28 - schoolL.width - parent.spacing * 2
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.name
                        elide: Text.ElideRight
                        color: modelData.on ? Theme.teal2 : Theme.text
                        font.pixelSize: Theme.fsBody - 1; font.bold: true
                    }
                    Label { id: schoolL; anchors.verticalCenter: parent.verticalCenter; text: modelData.school; color: Theme.text3; font.pixelSize: Theme.fsSmall - 1 }
                }
                MouseArea { anchors.fill: parent; onClicked: root.wb.toggleSpell(modelData.key, modelData.name) }
            }
        }
    }

    MPickerDialog {
        id: pickerDialog
        property string cardId: ""
        property var values: ({})
        dialogTitle: "Choose"
        onPicked: (value) => root.wb.toggleChoice(cardId, values[value] || value)
    }

    WizNav {
        id: nav
        anchors.bottom: parent.bottom; width: parent.width
        ready: root.leftList.length === 0
        text: ready ? "Next →" : root.leftList.join(", ") + " left"
        onBack: Window.window.goToWizardStep(2)
        onNext: if (ready) Window.window.advanceToEquipment(); else Window.window.showToast("Still to pick: " + root.leftList.join(", "))
    }
}
