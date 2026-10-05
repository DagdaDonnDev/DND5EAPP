import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Mimic

// Content for the Settings MFullPageDialog (see App.qml) -- not a
// Page/StackView destination itself, the dialog supplies the chrome
// (title bar + close button).
Flickable {
    id: root
    readonly property QtObject slBridge: Window.window.saveLoadBridge
    readonly property QtObject sheetBridge: Window.window.sheetBridge
    readonly property QtObject appSettingsBridge: Window.window.appSettingsBridge
    // Resolved here (root is an Item) rather than inline inside
    // themeDialog's onPicked below -- themeDialog is a Popup, and
    // Window.window only supports Item-derived types.
    readonly property bool characterActive: Window.window.characterActive
    anchors.fill: parent
    anchors.margins: 16
    contentWidth: width
    contentHeight: content.height
    clip: true

    Column {
        id: content
        width: parent.width
        spacing: 16

        Label {
            text: "Appearance"
            color: Theme.gold
            font.pixelSize: Theme.fsSmall
            font.bold: true
        }
        Rectangle {
            width: parent.width
            height: appearCol.height + 20
            radius: 10
            color: Theme.surf
            border.color: Theme.border

            ColumnLayout {
                id: appearCol
                x: 12; y: 10
                width: parent.width - 24
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Theme"; color: Theme.text2; font.pixelSize: Theme.fsSmall; Layout.preferredWidth: 90 }
                    Label {
                        Layout.fillWidth: true
                        // A character's own theme only actually applies
                        // while it's the one being viewed right now --
                        // otherwise (Start Menu, mid-wizard, or a
                        // finished character just navigated away from)
                        // this is the app's own remembered default. See
                        // App.qml's characterActive property comment.
                        text: characterActive ? sheetBridge.theme : appSettingsBridge.theme
                        color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true; elide: Text.ElideRight
                    }
                    MButton { primary: false; height: 32; text: "Change"; onClicked: themeDialog.open() }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Text Size"; color: Theme.text2; font.pixelSize: Theme.fsSmall; Layout.preferredWidth: 90 }
                    Label { Layout.fillWidth: true; text: sheetBridge.fontScale; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true }
                    MButton { primary: false; height: 32; text: "Change"; onClicked: fontScaleDialog.open() }
                }
            }
        }

        Label {
            text: "Character Rules"
            color: Theme.gold
            font.pixelSize: Theme.fsSmall
            font.bold: true
        }
        Rectangle {
            width: parent.width
            height: rulesCol.height + 20
            radius: 10
            color: Theme.surf
            border.color: Theme.border

            ColumnLayout {
                id: rulesCol
                x: 12; y: 10
                width: parent.width - 24
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Enforce feat prerequisites (race, ability scores, etc.)"
                        checked: sheetBridge.optionalRules.feat_prereqs
                        onToggled: sheetBridge.setOptionalRule("feat_prereqs", checked)
                    }
                    Label {
                        text: "When off, any feat can be picked at level-up regardless of its listed prerequisite -- useful for tables that allow feat flexibility."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Enforce multiclass ability score requirements (13+)"
                        checked: sheetBridge.optionalRules.multiclass_ability_reqs
                        onToggled: sheetBridge.setOptionalRule("multiclass_ability_reqs", checked)
                    }
                    Label {
                        text: "When off, any class can be multiclassed into regardless of ability scores -- useful for tables that don't use this restriction."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Show DMG/XGE optional combat actions (Disarm, Overrun, Tumble, Mark, Healing Surge, etc.)"
                        checked: sheetBridge.optionalRules.dmg_xge_optional_actions
                        onToggled: sheetBridge.setOptionalRule("dmg_xge_optional_actions", checked)
                    }
                    Label {
                        text: "When off, hides these variant rules from the Actions tab entirely -- useful for tables that stick to core PHB rules only."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Maximum hit points per level -- use each class's maximum hit die value instead of the average/rolled result"
                        checked: sheetBridge.optionalRules.max_hp_per_level
                        onToggled: sheetBridge.setOptionalRule("max_hp_per_level", checked)
                    }
                    Label {
                        text: "When on, every level (not just 1st) uses the hit die's maximum value + CON modifier instead of the PHB average formula (floor(hd/2)+1 + CON) -- e.g. a Barbarian gains 12 + CON at every level instead of 12 + CON at 1st and 7 + CON afterward. A common table variant, not an official rule."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Component Restrictions -- Blinded/Gagged/Restrained block casting spells needing sight/verbal/somatic components"
                        checked: sheetBridge.optionalRules.component_restrictions
                        onToggled: sheetBridge.setOptionalRule("component_restrictions", checked)
                    }
                    Label {
                        text: "When on, a spell can't be cast if an active condition blocks something it specifically needs: Blinded blocks any non-self-only spell (can't see a target), Gagged (a homebrew condition, not an official one) blocks spells with a verbal component, Restrained blocks spells with a somatic component. Only checked per-spell -- e.g. a self-only spell with no verbal component still works while Blinded and Gagged. A table-variant interpretation, not RAW."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }
        }

        Label {
            text: "Tasha's Cauldron Options"
            color: Theme.gold
            font.pixelSize: Theme.fsSmall
            font.bold: true
        }
        Rectangle {
            width: parent.width
            height: tashaCol.height + 20
            radius: 10
            color: Theme.surf
            border.color: Theme.border

            ColumnLayout {
                id: tashaCol
                x: 12; y: 10
                width: parent.width - 24
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Eldritch Versatility (Warlock, TCoE) -- swap a cantrip/Pact Boon/Mystic Arcanum at each ASI level"
                        checked: sheetBridge.optionalRules.eldritch_versatility
                        onToggled: sheetBridge.setOptionalRule("eldritch_versatility", checked)
                    }
                    Label {
                        text: "When on, adds the option to change your Pact Magic cantrips, Pact Boon, or Mystic Arcanum spells whenever you'd gain an Ability Score Improvement -- an optional Tasha's Cauldron of Everything rule."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Harness Divine Power (TCE) -- Cleric/Paladin: bonus action, expend Channel Divinity to regain a spell slot"
                        checked: sheetBridge.optionalRules.harness_divine_power
                        onToggled: sheetBridge.setOptionalRule("harness_divine_power", checked)
                    }
                    Label {
                        text: "When on, Cleric (2nd level+) and Paladin (3rd level+) gain this optional Tasha's Cauldron of Everything class feature: touch your holy symbol as a bonus action to regain one expended spell slot of level <= half your proficiency bonus (rounded up), a limited number of times per long rest."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Martial Versatility (TCE) -- Fighter/Paladin/Ranger: swap a Fighting Style at any level that grants an Ability Score Improvement"
                        checked: sheetBridge.optionalRules.martial_versatility
                        onToggled: sheetBridge.setOptionalRule("martial_versatility", checked)
                    }
                    Label {
                        text: "When on, Fighter, Paladin, and Ranger characters can replace one Fighting Style they know with another available to their class, at each level that grants an Ability Score Improvement -- a Tasha's Cauldron of Everything optional rule."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Cantrip Versatility (TCE) -- Cleric/Druid: swap a cantrip at any level that grants an Ability Score Improvement"
                        checked: sheetBridge.optionalRules.cantrip_versatility
                        onToggled: sheetBridge.setOptionalRule("cantrip_versatility", checked)
                    }
                    Label {
                        text: "When on, Cleric and Druid characters can replace one cantrip they know with another from their class's spell list, at each level that grants an Ability Score Improvement -- a Tasha's Cauldron of Everything optional rule."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Bardic Versatility (TCE) -- Bard: swap an Expertise skill or a cantrip at any level that grants an Ability Score Improvement"
                        checked: sheetBridge.optionalRules.bardic_versatility
                        onToggled: sheetBridge.setOptionalRule("bardic_versatility", checked)
                    }
                    Label {
                        text: "When on, Bard characters can replace one Expertise skill or one cantrip they know, at each level that grants an Ability Score Improvement -- a Tasha's Cauldron of Everything optional rule."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    MCheckBox {
                        Layout.fillWidth: true
                        text: "Sorcerous Versatility (TCE) -- Sorcerer: swap a Metamagic option or a cantrip at any level that grants an Ability Score Improvement"
                        checked: sheetBridge.optionalRules.sorcerous_versatility
                        onToggled: sheetBridge.setOptionalRule("sorcerous_versatility", checked)
                    }
                    Label {
                        text: "When on, Sorcerer characters can replace one Metamagic option or one cantrip they know, at each level that grants an Ability Score Improvement -- a Tasha's Cauldron of Everything optional rule."
                        color: Theme.text3
                        font.pixelSize: Theme.fsSmall
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }
        }

        Label {
            text: "DM Secrets"
            color: Theme.gold
            font.pixelSize: Theme.fsSmall
            font.bold: true
        }
        Rectangle {
            width: parent.width
            height: dmSecretsCol.height + 20
            radius: 10
            color: Theme.surf
            border.color: Theme.border

            ColumnLayout {
                id: dmSecretsCol
                x: 12; y: 10
                width: parent.width - 24
                spacing: 6

                MCheckBox {
                    Layout.fillWidth: true
                    text: "Immersive Spells"
                    checked: sheetBridge.immersiveSpells
                    onToggled: sheetBridge.setImmersiveSpells(checked)
                }
                Label {
                    // Deliberately vague -- it's a DM Secret, not a
                    // spoiler. Just enough to say it's safe to flip.
                    text: "Purely cosmetic. No gameplay effect -- try it and see."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                MCheckBox {
                    Layout.fillWidth: true
                    text: "Critical Flavor"
                    checked: sheetBridge.optionalRules.critical_flavor
                    onToggled: sheetBridge.setOptionalRule("critical_flavor", checked)
                }
                Label {
                    // Deliberately vague -- see the note above.
                    text: "Purely cosmetic. No gameplay effect -- try it and see."
                    color: Theme.text3
                    font.pixelSize: Theme.fsSmall
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }

        Label {
            text: "Storage"
            color: Theme.gold
            font.pixelSize: Theme.fsSmall
            font.bold: true
        }

        Rectangle {
            width: parent.width
            height: folderCol.height + 20
            radius: 10
            color: Theme.surf
            border.color: Theme.border

            Column {
                id: folderCol
                x: 12; y: 10
                width: parent.width - 24
                spacing: 10

                Column {
                    width: parent.width
                    spacing: 2
                    Label {
                        text: "Default save / export folder"
                        color: Theme.text2
                        font.pixelSize: Theme.fsSmall
                    }
                    Label {
                        objectName: "documentsDirLabel"
                        text: slBridge.documentsDir
                        color: Theme.text
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        wrapMode: Text.WrapAnywhere
                        width: parent.width
                    }
                }

                Column {
                    width: parent.width
                    spacing: 2
                    Label {
                        text: "Downloads folder (browsed when loading)"
                        color: Theme.text2
                        font.pixelSize: Theme.fsSmall
                    }
                    Label {
                        objectName: "downloadsDirLabel"
                        text: slBridge.downloadsDir
                        color: Theme.text
                        font.pixelSize: Theme.fsSmall
                        font.bold: true
                        wrapMode: Text.WrapAnywhere
                        width: parent.width
                    }
                }
            }
        }

        Label {
            text: "This is a sandboxed, app-private folder — not the shared Documents folder a file manager or another app can browse. Saved character JSON files and every export (PDF, plain text) land here, in the same format the desktop app uses. Changing this destination isn't supported yet; it needs Android's Storage Access Framework, a bigger feature than a simple path setting."
            color: Theme.text3
            font.pixelSize: Theme.fsSmall
            wrapMode: Text.WordWrap
            width: parent.width
        }
    }

    MPickerDialog {
        id: themeDialog
        dialogTitle: "Choose Theme"
        options: sheetBridge.themeNames
        onPicked: (value) => {
            // Only actually viewing a character right now saves to
            // that character's own theme -- anywhere else (Start Menu,
            // mid-wizard, or a finished character just navigated away
            // from) this becomes the app's own remembered default
            // instead. See App.qml's characterActive property comment.
            if (characterActive) {
                sheetBridge.setTheme(value)
            } else {
                appSettingsBridge.setTheme(value)
            }
            Theme.applyTheme(value)
        }
    }
    MPickerDialog {
        id: fontScaleDialog
        dialogTitle: "Text Size"
        options: sheetBridge.fontScaleNames
        onPicked: (value) => {
            sheetBridge.setFontScale(value)
            Theme.applyFontScale(value)
        }
    }
}
