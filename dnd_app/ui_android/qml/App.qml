import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import Mimic

ApplicationWindow {
    id: window
    width: 412
    height: 915
    visible: true
    title: "MIMIC"
    Material.theme: Material.Dark
    Material.accent: Theme.gold
    Material.background: Theme.bg
    Material.foreground: Theme.text
    color: Theme.bg

    // Per-wizard-step Python bridges. These are plain QML properties,
    // set from main.py via win.setProperty(...) AFTER engine.load()
    // completes -- NOT QQmlContext.setContextProperty() before load.
    // With two-or-more setContextProperty() calls before load, screens
    // instantiated by StackView's initialItem/replace() saw their
    // context property permanently resolve to null (confirmed via
    // isolated reproduction: with only one context property registered
    // it eventually resolved; with two, it never did, no matter how
    // long a Timer delayed the retry). A plain property assigned after
    // load doesn't have that failure mode -- QML's normal property
    // binding/notify system correctly retries dependents once it's
    // set. Screens reference these via Window.window.raceBridge /
    // Window.window.abilityBridge rather than a bare identifier.
    property QtObject raceBridge: null
    property QtObject abilityBridge: null
    property QtObject classBridge: null
    property QtObject equipmentBridge: null
    property QtObject saveLoadBridge: null
    property QtObject sheetBridge: null
    property QtObject diceRollerBridge: null
    property QtObject creditsBridge: null
    property QtObject easterEggBridge: null
    property QtObject appSettingsBridge: null

    // Easter egg (matches ui_desktop's main_window.py exactly): naming a
    // character after this app's creator turns the header bar gold,
    // regardless of the active theme.
    readonly property bool creatorNamed: !!(sheetBridge && sheetBridge.name
        && sheetBridge.name.trim().toLowerCase() === "ethan o'brien")

    // Scratch state for content shown inside an MFullPageDialog: that
    // wrapper's default-property mechanism reparents injected content
    // into an Item living inside MFullPageDialog.qml's OWN component,
    // which breaks bare (non-id) property lookups back out to an
    // ancestor id declared at the call site -- reached via
    // Window.window instead, the same way every screen already reaches
    // its own bridge, rather than a bare reference to an outer id's
    // property.
    property var pendingSpellDetail: ({})
    property var pendingItemDetail: ({})
    property var pendingDmRewardDetail: ({})
    property var pendingFeatDetail: ({})

    // Whether a character is actually being viewed right now -- NOT
    // the same as `sheetMode` above, which reads sheetBridge.hasCharacter
    // off the shared character dict and stays true even after
    // goToStartMenu() navigates away from a finished character (the
    // dict itself isn't reset just by navigating, only by
    // startNewCharacter()/loadCharacterIntoSheet() overwriting it).
    // Settings' theme picker needs the real "am I looking at a
    // character's own sheet right now" signal -- see its onPicked.
    property bool characterActive: false

    // Set by the drawer's expandable sub-menu (see NavDrawer.qml's
    // sectionSelected) just before navigating -- consumed once the
    // StackView settles on the new page (see the Connections below),
    // which then scrolls that page to the named section if it exposes
    // a scrollToSection() function.
    property string pendingScrollSection: ""

    // StackView.push()/replace()/initialItem all need an actual
    // Component or Item, not a "Foo.qml" URL string -- passing a URL
    // compiles without error but the pushed page silently never
    // renders any content bound to a context property (confirmed by
    // testing both paths side by side; a Component reference or a
    // direct type instantiation both work correctly).
    //
    // Screens are named by file here and only compiled the first time
    // they're opened (screenComp() below), not all ~11k lines of them
    // before the Start Menu can appear -- the single biggest part of
    // startup. screenComp() still hands StackView a real Component (made
    // with Qt.createComponent and cached), never a bare URL string, for
    // the reason above. Once the Start Menu is up, preloadScreens()
    // compiles the rest in the background so first visits stay quick.
    readonly property string startMenuComp: "StartMenuScreen.qml"
    readonly property string raceListComp: "RaceListScreen.qml"
    readonly property string abilitiesComp: "AbilitiesScreen.qml"
    readonly property string classComp: "ClassScreen.qml"
    readonly property string equipmentComp: "EquipmentScreen.qml"
    readonly property string sheetComp: "SheetCombatScreen.qml"
    readonly property string sheetActionsComp: "SheetActionsScreen.qml"
    readonly property string sheetAbilitiesComp: "SheetAbilitiesScreen.qml"
    readonly property string sheetProficienciesComp: "SheetProficienciesScreen.qml"
    readonly property string sheetSpellsComp: "SheetSpellsScreen.qml"
    readonly property string sheetEquipmentComp: "SheetEquipmentScreen.qml"
    readonly property string sheetCompanionsComp: "SheetCompanionsScreen.qml"
    readonly property string sheetFeaturesComp: "SheetFeaturesScreen.qml"
    readonly property string sheetInfusionsComp: "SheetInfusionsScreen.qml"
    readonly property string sheetChoicesComp: "SheetChoicesScreen.qml"
    readonly property string sheetNotesComp: "SheetNotesScreen.qml"

    property var _screenCache: ({})
    function screenComp(file) {
        if (typeof file !== "string")
            return file
        var c = _screenCache[file]
        // a background preload still in progress is replaced by a
        // synchronous load (which just finishes the same compile)
        if (!c || c.status !== Component.Ready) {
            c = Qt.createComponent(Qt.resolvedUrl(file))
            if (c.status === Component.Error)
                console.warn("[MIMIC] " + file + ": " + c.errorString())
            _screenCache[file] = c
        }
        return c
    }
    function preloadScreens() {
        var files = [sheetComp, raceListComp, abilitiesComp, classComp, equipmentComp,
                     sheetActionsComp, sheetSpellsComp, sheetEquipmentComp, sheetAbilitiesComp,
                     sheetProficienciesComp, sheetFeaturesComp, sheetChoicesComp, sheetNotesComp,
                     sheetCompanionsComp, sheetInfusionsComp]
        for (var i = 0; i < files.length; ++i) {
            if (!_screenCache[files[i]])
                _screenCache[files[i]] = Qt.createComponent(Qt.resolvedUrl(files[i]), Component.Asynchronous)
        }
    }
    Timer { interval: 400; running: true; onTriggered: window.preloadScreens() }

    // The drawer shows a different step list depending on whether the
    // current character is still being built or already finished --
    // "wizard mode" (Race/Abilities/Class/Equipment) vs. "sheet mode"
    // (Combat/Abilities/Proficiencies/Spells/Equipment/Infusions[
    // Artificer only]/Choices/Notes). Driven by
    // CharacterSheetBridge.hasCharacter, which reads a real
    // char["character_created"] field set by the last wizard step
    // (EquipmentWizardBridge.confirmEquipment()) -- not local UI
    // state, so it's correct immediately after a Start Menu "Load" too.
    readonly property bool sheetMode: sheetBridge !== null && sheetBridge.hasCharacter

    // True while the character has level-up choices still to make.
    // Drives the pulsing dot on the header's menu button, the drawer's
    // Choices row and SheetChoicesScreen's Choices tab, so the player is
    // led from wherever they are to the choices waiting for them.
    // Computed once here rather than in each of those bindings.
    readonly property bool choicesPending: sheetMode && sheetBridge.hasPendingChoices

    // Each step is greyed out in the drawer until the previous one is
    // actually confirmed -- the player can still get there via each
    // screen's own bottom "Next" button (see advanceToAbilities() etc.
    // below), which is what advances *Bridge.*ConfirmedOnce in the
    // first place; the drawer is a shortcut back to an already-done
    // step, not a way to skip ahead of one that isn't.
    readonly property var wizardNavItems: [
        { label: "Race", screen: raceListComp, enabled: true },
        { label: "Abilities", screen: abilitiesComp,
          enabled: raceBridge !== null && raceBridge.raceConfirmedOnce },
        { label: "Class", screen: classComp,
          enabled: abilityBridge !== null && abilityBridge.abilitiesConfirmedOnce },
        { label: "Equipment", screen: equipmentComp,
          enabled: classBridge !== null && classBridge.classConfirmedOnce },
    ]
    readonly property var sheetNavItemsBase: [
        { label: "Combat", screen: sheetComp, enabled: true },
        { label: "Actions", screen: sheetActionsComp, enabled: true,
          sections: ["Resources", "Action", "Bonus Action", "Reaction", "Passive / Other"] },
        { label: "Abilities", screen: sheetAbilitiesComp, enabled: true },
        { label: "Proficiencies", screen: sheetProficienciesComp, enabled: true },
        { label: "Spells", screen: sheetSpellsComp, enabled: true,
          sections: ["Spell Slots", "Known Spells", "Add a Spell"] },
        { label: "Equipment", screen: sheetEquipmentComp, enabled: true,
          sections: ["Inventory", "Add Equipment", "Magic Items", "Add a Magic Item"] },
        { label: "Companions", screen: sheetCompanionsComp, enabled: true,
          sections: ["Mounts", "Vehicles", "Summoned Creatures", "Wild Shape"] },
        { label: "Features", screen: sheetFeaturesComp, enabled: true },
    ]
    // Infusions only makes sense for Artificers -- everyone else never
    // sees the entry at all, rather than a permanently "(finish
    // previous step)"-style disabled one that would never unlock.
    readonly property var sheetNavItems:
        (sheetBridge !== null && sheetBridge.isArtificer
            ? sheetNavItemsBase.concat([{ label: "Infusions", screen: sheetInfusionsComp, enabled: true }])
            : sheetNavItemsBase
        ).concat([
            { label: "Choices", screen: sheetChoicesComp, enabled: true,
              pulse: window.choicesPending },
            { label: "Notes", screen: sheetNotesComp, enabled: true,
              sections: ["Personality", "Appearance", "Backstory"].concat(
                  sheetBridge !== null ? sheetBridge.notesPages.map(p => p.title) : []) },
        ])
    readonly property var navItems: sheetMode ? sheetNavItems : wizardNavItems

    // The drawer's own "MIMIC" title row carries a Home button back to
    // the Start Menu (see NavDrawer.qml) instead of it being a regular
    // entry in the step list above -- it's a shortcut to character
    // load/new/delete, not a step in either the wizard or the sheet.
    // Called once from main.py right after appSettingsBridge is
    // assigned (that assignment happens post-engine.load(), same as
    // every other bridge here -- see the property block's comment
    // above -- so this can't just run from Component.onCompleted).
    // Applies the app's own remembered theme (Start Menu / mid-wizard,
    // independent of any character's own char["theme"]) before the
    // Start Menu is ever shown, matching ui_desktop's constructor-time
    // fix in main_window.py.
    function applyStartupTheme() {
        Theme.applyTheme(appSettingsBridge.theme)
    }

    function goToStartMenu() {
        characterActive = false
        // Revert away from whatever character theme was active back to
        // the app's own remembered default -- same reasoning as
        // ui_desktop's _go_menu().
        Theme.applyTheme(appSettingsBridge.theme)
        stackView.replace(screenComp(startMenuComp))
        drawer.close()
    }

    // Entry point for the drawer's Home button -- goToStartMenu() itself
    // stays a plain, unconditional navigation (used elsewhere after a
    // save/load already completes), but jumping to it straight from
    // mid-wizard or an open sheet used to silently discard every
    // unsaved edit with no warning at all. saveLoadBridge owns the
    // shared character dict's "has this changed since the last load/
    // save" snapshot, so it's asked fresh here rather than cached --
    // this only ever runs right when the player taps Home.
    function requestGoToStartMenu() {
        if (saveLoadBridge.hasUnsavedChanges()) {
            unsavedChangesDialog.open()
        } else {
            goToStartMenu()
        }
    }

    // Start Menu / wizard-completion actions -- kept here (rather than
    // inline in StartMenuScreen.qml/EquipmentScreen.qml) since they
    // touch multiple bridges plus the StackView, none of which those
    // screens should need direct Component-id access to. Each one
    // calls sheetBridge.refresh() so `sheetMode` above (and anything
    // else reading CharacterSheetBridge) reflects the new state
    // immediately -- it's a live Python property, but its notify
    // signal only fires when something tells that bridge's own
    // CharacterController to refresh, not just because a DIFFERENT
    // bridge mutated the shared character dict.
    function startNewCharacter() {
        characterActive = false
        saveLoadBridge.newCharacter()
        abilityBridge.resetToDefaults()
        raceBridge.refresh()
        classBridge.refresh()
        equipmentBridge.refresh()
        sheetBridge.refresh()
        stackView.replace(screenComp(raceListComp))
    }
    function loadCharacterIntoSheet(filepath) {
        // A saved character is already complete (confirmRace()/
        // confirmClass()/etc. all require a valid state to save at
        // all), so loading one goes straight to the sheet rather than
        // back through the wizard.
        if (saveLoadBridge.loadCharacterFrom(filepath))
            showLoadedCharacter()
    }
    // After a character is loaded (a save, an imported file or PDF sheet):
    // straight to its sheet, in its own theme.
    function showLoadedCharacter() {
        sheetBridge.refresh()
        // A save from before "theme" existed (or one that
        // otherwise never went through finishCharacterCreation's
        // stamp below) has no theme of its own recorded yet --
        // stamp whatever's currently active rather than silently
        // adopting a later app-level default change next time.
        sheetBridge.stampThemeIfMissing(Theme.currentThemeName)
        Theme.applyTheme(sheetBridge.theme)
        Theme.applyFontScale(sheetBridge.fontScale)
        characterActive = true
        stackView.replace(screenComp(sheetComp))
    }
    function finishCharacterCreation() {
        if (equipmentBridge.confirmEquipment()) {
            sheetBridge.refresh()
            // First time this character is shown -- it has no theme of
            // its own yet, so it inherits whatever was active during
            // the wizard (the app-level default, unless changed
            // mid-wizard) and keeps that from here on, independent of
            // any later app-level default change.
            sheetBridge.stampThemeIfMissing(Theme.currentThemeName)
            Theme.applyTheme(sheetBridge.theme)
            Theme.applyFontScale(sheetBridge.fontScale)
            characterActive = true
            stackView.replace(screenComp(sheetComp))
            saveLoadBridge.autoSave()      // a new character is saved straight away
            return true
        }
        return false
    }

    // Wizard step-to-step "Next" navigation -- each screen's own
    // confirm button calls the matching one of these on success,
    // rather than popping back to a list or just sitting still. Named
    // per-destination (instead of one generic "advance" helper) so
    // each screen states in plain text which step it's headed to.
    function advanceToAbilities() { stackView.replace(screenComp(abilitiesComp)) }
    function advanceToClass() { stackView.replace(screenComp(classComp)) }
    function advanceToEquipment() { stackView.replace(screenComp(equipmentComp)) }
    // App-level destinations, not character-creation steps -- each
    // opens as a full-page modal dialog (see the MFullPageDialog
    // instances below) on top of whatever step screen is showing,
    // rather than a StackView navigation that would replace it. Laid
    // out as a 2x2 tile grid in the drawer's own bottom section.
    readonly property var utilityNavItems: [
        { label: "Dice Roller", icon: "dice", enabled: true, onOpen: function() { diceRollerDialog.open() } },
        { label: "Settings", icon: "settings", enabled: true, onOpen: function() { settingsDialog.open() } },
        { label: "Save & Export", icon: "save", enabled: true, onOpen: function() { saveLoadDialog.open(); window.saveLoadBridge.refresh() } },
        { label: "Credits", icon: "credits", enabled: true, onOpen: function() { creditsDialog.open() } },
    ]

    Popup {
        id: unsavedChangesDialog
        objectName: "unsavedChangesDialog"
        modal: true
        focus: true
        width: 300
        anchors.centerIn: parent
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

        ColumnLayout {
            anchors.fill: parent
            spacing: 12
            Label {
                text: "Unsaved Changes"
                color: Theme.gold
                font.pixelSize: Theme.fsBody
                font.bold: true
            }
            Label {
                text: "This character has changes that haven't been saved yet. Leaving now will lose them."
                color: Theme.text2
                font.pixelSize: Theme.fsSmall
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            MButton {
                objectName: "unsavedSaveAndExitButton"
                Layout.fillWidth: true
                text: "Save & Exit"
                onClicked: {
                    if (saveLoadBridge.saveCharacter()) {
                        unsavedChangesDialog.close()
                        goToStartMenu()
                    }
                    // On failure saveLoadBridge already raised its own
                    // error (see errorMessage/toastRequested) -- leave
                    // the dialog open so the player can fix it (most
                    // likely an incomplete-wizard validation failure)
                    // or fall back to Discard/Cancel instead.
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    objectName: "unsavedDiscardButton"
                    Layout.fillWidth: true
                    primary: false
                    text: "Discard & Exit"
                    onClicked: { unsavedChangesDialog.close(); goToStartMenu() }
                }
                MButton {
                    objectName: "unsavedCancelButton"
                    Layout.fillWidth: true
                    primary: false
                    text: "Cancel"
                    onClicked: unsavedChangesDialog.close()
                }
            }
        }
    }

    MFullPageDialog {
        id: settingsDialog
        objectName: "settingsDialog"
        dialogTitle: "Settings"
        contentSource: Qt.resolvedUrl("SettingsScreen.qml")
    }
    MFullPageDialog {
        id: saveLoadDialog
        objectName: "saveLoadDialog"
        dialogTitle: "Save & Export"
        contentSource: Qt.resolvedUrl("SaveLoadScreen.qml")
    }
    MFullPageDialog {
        id: diceRollerDialog
        objectName: "diceRollerDialog"
        dialogTitle: "Dice Roller"
        contentSource: Qt.resolvedUrl("DiceRollerScreen.qml")
    }
    MFullPageDialog {
        id: creditsDialog
        objectName: "creditsDialog"
        dialogTitle: "Credits"
        contentSource: Qt.resolvedUrl("CreditsScreen.qml")
    }

    // ── Effects still on from last time ─────────────────────────────
    // A saved character opened again with effects a short rest would
    // end (Rage, Bladesong, a potion's hour...): have they ended? The
    // ticked ones end (core/action_use.py leftover_effects). Every way
    // of opening a save ends in characterLoaded, and the question comes
    // once per open.
    function askLeftoverEffects() {
        if (!sheetBridge)
            return
        var left = sheetBridge.takeLeftoverEffects()
        if (left.length > 0) {
            leftoverDialog.effects = left
            leftoverDialog.open()
        }
    }
    Connections {
        target: saveLoadBridge
        function onCharacterLoaded() { Qt.callLater(window.askLeftoverEffects) }
    }
    Dialog {
        id: leftoverDialog
        objectName: "leftoverDialog"
        property var effects: []
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: Math.min(parent ? parent.width - 32 : 360, 360)
        padding: 16
        background: Rectangle { color: Theme.surf; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }
        contentItem: ColumnLayout {
            spacing: 10
            Label {
                text: "Effects still on"
                color: Theme.gold2
                font.pixelSize: Theme.fsHead
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "These were on when this character was last saved. Have they ended? Untick any that are still going."
                color: Theme.text
                font.pixelSize: Theme.fsBody
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Repeater {
                id: leftoverRepeater
                model: leftoverDialog.effects
                delegate: MCheckBox {
                    objectName: "leftover_" + modelData
                    text: modelData
                    checked: true
                    Layout.fillWidth: true
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                MButton {
                    Layout.fillWidth: true
                    primary: false
                    text: "Keep all"
                    onClicked: leftoverDialog.close()
                }
                MButton {
                    id: leftoverEndButton
                    objectName: "leftoverEnd"
                    Layout.fillWidth: true
                    text: "End ticked"
                    onClicked: {
                        var names = []
                        for (var i = 0; i < leftoverRepeater.count; i++) {
                            var box = leftoverRepeater.itemAt(i)
                            if (box && box.checked)
                                names.push(box.text)
                        }
                        sheetBridge.endEffects(names)
                        leftoverDialog.close()
                    }
                }
            }
        }
    }

    // The one-time note the first time either immersive effect shows
    MFullPageDialog {
        id: immersivePrompt
        objectName: "immersivePrompt"
        dialogTitle: "Immersive Effects"
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 14
            Label {
                Layout.fillWidth: true
                text: appSettingsBridge ? appSettingsBridge.immersiveInfo("prompt").what : ""
                color: Theme.text; font.pixelSize: Theme.fsBody; wrapMode: Text.WordWrap
            }
            Repeater {
                model: ["health", "exhaustion"]
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    readonly property var info: appSettingsBridge ? appSettingsBridge.immersiveInfo(modelData) : ({})
                    RowLayout {
                        Layout.fillWidth: true
                        Label { Layout.fillWidth: true; text: info.name || ""; color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true; wrapMode: Text.WordWrap }
                        Label {
                            text: appSettingsBridge ? (modelData === "health" ? appSettingsBridge.immersiveHealth : appSettingsBridge.immersiveExhaustion) : ""
                            color: Theme.text; font.pixelSize: Theme.fsBody; font.bold: true
                        }
                        MButton { primary: false; height: 32; text: "Change"; onClicked: { immersivePicker.kind = modelData; immersivePicker.open() } }
                    }
                    Label { Layout.fillWidth: true; text: info.what || ""; color: Theme.text2; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap }
                }
            }
            Label {
                Layout.fillWidth: true
                text: appSettingsBridge ? appSettingsBridge.immersiveInfo("health").reduced : ""
                color: Theme.text3; font.pixelSize: Theme.fsSmall; wrapMode: Text.WordWrap
            }
            MButton { text: "Done"; Layout.alignment: Qt.AlignRight; onClicked: immersivePrompt.close() }
            Item { Layout.fillHeight: true }
        }
    }
    MPickerDialog {
        id: immersivePicker
        property string kind: "health"
        dialogTitle: kind === "health" ? "Immersive Health" : "Immersive Exhaustion"
        options: appSettingsBridge ? appSettingsBridge.immersiveModes : []
        onPicked: (value) => appSettingsBridge.setImmersive(kind, value)
    }

    RestFlowDialog { id: restFlowDialog; sheetBridge: window.sheetBridge }
    function startRest(restType) { restFlowDialog.start(restType) }

    header: ToolBar {
        Material.background: window.creatorNamed ? "#3a2e05" : Theme.surf
        ToolButton {
            id: hamburgerButton
            objectName: "hamburgerButton"
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 4
            width: 44
            height: 44
            onClicked: drawer.open()

            // Pending level-up choices: a pulsing dot on the menu button,
            // since the drawer's own pulsing Choices row is hidden until
            // it's opened. Not shown on the Choices screen itself --
            // the player is already there.
            MPulseDot {
                objectName: "hamburgerPulse"
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.rightMargin: -2
                anchors.topMargin: 2
                diameter: 8
                running: window.choicesPending
                         && !(stackView.currentItem && stackView.currentItem.isChoicesScreen === true)
            }

            // Drawn instead of a "☰" text glyph -- that Unicode symbol
            // (U+2630) isn't covered by every Android device's font
            // stack (confirmed missing on a real device, unlike true
            // emoji glyphs elsewhere in this app, which ride Android's
            // universal Noto Color Emoji font). Three plain bars can
            // never fail to render since they don't depend on any font.
            contentItem: Column {
                anchors.centerIn: parent
                spacing: 4
                Repeater {
                    model: 3
                    Rectangle {
                        width: 22
                        height: 2
                        radius: 1
                        color: Theme.text
                    }
                }
            }
        }
        Label {
            // Centered on the whole bar (not just the space left of the
            // hamburger button), same as a standard mobile app bar.
            anchors.centerIn: parent
            text: stackView.currentItem && stackView.currentItem.screenTitle
                  ? stackView.currentItem.screenTitle : "MIMIC"
            color: window.creatorNamed ? "#f5cc50" : Theme.gold2
            font.pixelSize: Theme.fsHead
            font.bold: true
            elide: Text.ElideRight
            width: Math.min(implicitWidth, parent.width - 2 * (hamburgerButton.width + 16))
            horizontalAlignment: Text.AlignHCenter
        }
    }

    NavDrawer {
        id: drawer
        height: window.height
        items: window.navItems
        utilityItems: window.utilityNavItems
        onItemSelected: (screen) => {
            if (screen) {
                stackView.replace(screenComp(screen))
            }
            drawer.close()
        }
        onSectionSelected: (screen, sectionName) => {
            window.pendingScrollSection = sectionName
            if (screen) {
                stackView.replace(screenComp(screen))
            }
            drawer.close()
        }
    }

    StackView {
        id: stackView
        anchors.fill: parent
        // Immersive Exhaustion: the page moves in to fit inside the frame
        anchors.margins: window.frameInset
        initialItem: screenComp(startMenuComp)
    }

    // ── Immersive Health & Immersive Exhaustion (core/immersive.py) ─────
    // Checked a few times a second while a character's sheet is open, so
    // every way HP or exhaustion changes is picked up. Off the sheet
    // (Start Menu, wizard) both effects are off.
    property real frameInset: 0
    property int frameLevel: 0
    property string frameSetting: "Off"
    property real healthFade: 0
    property bool healthAnimate: true
    Behavior on healthFade {
        enabled: window.healthAnimate
        NumberAnimation { duration: 500; easing.type: Easing.InOutQuad }
    }
    // the theme only repaints in 1/40 steps, so an easing colour change
    // costs a dozen repaints rather than one every frame
    onHealthFadeChanged: {
        var q = Math.round(healthFade * 40) / 40
        if (Math.abs(q - Theme.fade) > 0.001) Theme.fade = q
    }
    Timer {
        interval: 200; running: true; repeat: true
        onTriggered: {
            var on = window.characterActive && window.sheetMode
            var st = on ? sheetBridge.immersiveState() : null
            window.healthAnimate = !st || st.health === "Full"
            window.healthFade = st ? st.fade : 0
            window.frameLevel = st ? st.level : 0
            window.frameSetting = st ? st.exhaustion : "Off"
            window.frameInset = st ? st.inset : 0
            if (st && !st.promptSeen && (st.fade > 0 || st.level > 0)) {
                sheetBridge.markImmersivePromptSeen()
                immersivePrompt.open()
            }
        }
    }
    // The frame itself: drawn by the same painter as the desktop's
    // (bridge/immersive.py), over the page area, letting every touch through.
    Image {
        id: immersiveFrame
        anchors.fill: parent
        visible: window.frameLevel > 0
        source: visible ? "image://immersive/" + window.frameLevel + "/" + window.frameSetting + "/"
                          + Math.round(width) + "x" + Math.round(height) + "/" + Screen.devicePixelRatio : ""
        fillMode: Image.Stretch
        smooth: true
        cache: false
        // a new frame fades in (not on Reduced)
        onSourceChanged: if (visible && window.frameSetting === "Full") frameFadeIn.restart()
        NumberAnimation { id: frameFadeIn; target: immersiveFrame; property: "opacity"; from: 0; to: 1; duration: 350 }
    }

    // Consumes pendingScrollSection once the page StackView just
    // navigated to has actually finished its push/pop transition (same
    // "wait for busy to clear" timing established for tests -- the new
    // page's Flickable/Repeaters aren't laid out yet while busy).
    Connections {
        target: stackView
        function onBusyChanged() {
            if (stackView.busy || window.pendingScrollSection === "") {
                return
            }
            var target = window.pendingScrollSection
            window.pendingScrollSection = ""
            var page = stackView.currentItem
            if (page && typeof page.scrollToSection === "function") {
                page.scrollToSection(target)
            }
        }
    }

    // App-wide toast, reachable from any screen (drawer rest actions,
    // Save/Load, PDF export). Styling matches ui_desktop's
    // CharacterSheet._toast() exactly: SURF2 background, GOLD text, a
    // semi-transparent AMBER border -- same notification look on both
    // platforms even though the widget toolkits are unrelated.
    function showToast(message) {
        appToastLabel.text = message
        appToast.visible = true
        // long enough to read: longer messages stay up longer
        appToastTimer.interval = Math.min(9000, Math.max(3200, 55 * message.length))
        appToastTimer.restart()
    }

    // A shared rule needs an answer first -- how many ki, which slot, who a
    // spell is on, which weapon -- from whichever screen it came: the pick
    // goes back to the bridge, which carries on (Cancel leaves it undone)
    MOptionsDialog {
        id: actionQuestionDialog
        objectName: "actionQuestionDialog"
        onPicked: (key) => window.sheetBridge.answerActionQuestion(key)
    }
    // After an attack roll (core/attacks.py attack_report, the same as
    // desktop's dialog), top to bottom:
    //   the roll: a card with the total, big; a bar down its left side says
    //   what it was (gold a critical, red a natural 1)
    //   ON A HIT: the damage and what's on now, each with its type and where
    //   it's from; a next-hit effect it used up can be marked here
    //   ADD TO THE ROLL / IF IT MISSES (a check's ADD TO THIS CHECK / IF IT
    //   FAILS): right under the roll, each with an Add button -- it's paid
    //   for and rolled there and then (sheetBridge.addToRoll), and the roll
    //   comes back with its new total (attackReport with "update": ticks stay)
    //   YOU CAN ADD / ALSO THIS TURN: choices with their costs, only what you
    //   can pay for now -- tap a row to pick it (its border turns gold). One
    //   pick per group (a Divine Smite slot); undead or fiend needs a smite.
    // Add pays for the picks through the bridge, which asks if there's more to choose.
    Dialog {
        id: attackDialog
        objectName: "attackDialog"
        property string heading: ""
        property var report: ({})
        property var options: []
        property var ticked: ({})
        // a check or save (core/checks.py): Done takes it, and closing the
        // dialog any other way takes it with nothing added
        property bool taken: false
        readonly property bool isCheck: report.kind === "check"
        readonly property var roll: report.roll || ({})
        onClosed: if (isCheck && !taken) { taken = true; window.sheetBridge.takeCheckOptions([]) }
        function optionByKey(k) {
            for (var i = 0; i < options.length; i++) if (options[i].key === k) return options[i]
            return null
        }
        function groupPicked(g) {
            for (var k in ticked) {
                var o = optionByKey(k)
                if (ticked[k] && o && o.group === g) return true
            }
            return false
        }
        function isLive(o) { return !o.needs || groupPicked(o.needs) }
        function isOn(o) { return ticked[o.key] === true && isLive(o) }
        function toggle(o) {
            var t = Object.assign({}, ticked)
            var now = !t[o.key]
            if (now && o.group)
                for (var i = 0; i < options.length; i++)
                    if (options[i].group === o.group) t[options[i].key] = false
            t[o.key] = now
            ticked = t
        }
        function pickedKeys() {
            var out = []
            for (var i = 0; i < options.length; i++)
                if (isOn(options[i])) out.push(options[i].key)
            return out
        }
        function section(name) { return options.filter(function(o) { return o.section === name }) }
        function sectionsNow(now) {
            return (report.sections || []).filter(function(x) { return (x.now === true) === now })
        }
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: Math.min(parent ? parent.width - 24 : 360, 400)
        height: Math.min(attackCol.implicitHeight + 32, (parent ? parent.height : 800) - 72)
        padding: 16
        background: Rectangle { color: Theme.bg; radius: 12; border.color: Theme.border }
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }
        contentItem: Flickable {
            clip: true
            contentHeight: attackCol.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            ColumnLayout {
                id: attackCol
                width: parent.width
                spacing: 10
                Label {
                    text: attackDialog.heading
                    color: Theme.gold2
                    font.pixelSize: Theme.fsHead
                    font.bold: true
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                // the plain text, for anything reading the dialog
                Label { objectName: "attackMessage"; visible: false; text: attackDialog.report.message || "" }

                // the roll: the total, how it was made, what it hits
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: rollRow.implicitHeight + 22
                    radius: 8
                    color: Theme.surf
                    border.color: Theme.border
                    Rectangle {
                        width: 4; radius: 2
                        anchors { left: parent.left; top: parent.top; bottom: parent.bottom; margins: 1 }
                        color: attackDialog.roll.crit ? Theme.gold : (attackDialog.roll.nat1 ? Theme.crimson2 : Theme.teal2)
                    }
                    RowLayout {
                        id: rollRow
                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter
                                  leftMargin: 16; rightMargin: 12 }
                        spacing: 14
                        ColumnLayout {
                            spacing: 0
                            Label {
                                objectName: "attackTotal"
                                text: attackDialog.roll.total !== undefined ? String(attackDialog.roll.total) : ""
                                color: Theme.text
                                font.pixelSize: Theme.fsTitle + 8
                                font.bold: true
                                Layout.alignment: Qt.AlignHCenter
                            }
                            Label { text: attackDialog.report.total_label || "to hit"; color: Theme.text2
                                    font.pixelSize: Theme.fsSmall; Layout.alignment: Qt.AlignHCenter }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            Label {
                                text: attackDialog.roll.line || ""
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: true
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Label {
                                visible: (attackDialog.roll.note || "") !== ""
                                text: attackDialog.roll.note || ""
                                color: Theme.text2
                                font.pixelSize: Theme.fsSmall
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Label {
                                objectName: "attackVerdict"
                                text: attackDialog.roll.verdict || ""
                                color: Theme.text
                                font.pixelSize: Theme.fsBody
                                font.bold: attackDialog.roll.crit === true || attackDialog.roll.nat1 === true
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }

                // ADD TO THE ROLL, then IF IT MISSES: each with its Add
                Repeater {
                    model: attackDialog.sectionsNow(true)
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Label {
                            text: modelData.title
                            color: Theme.text2
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                            font.letterSpacing: 1
                        }
                        Repeater {
                            model: attackDialog.section(modelData.name)
                            delegate: MAttackOption {
                                Layout.fillWidth: true
                                opt: modelData
                                now: true
                                onAdd: window.sheetBridge.addToRoll(modelData.key)
                            }
                        }
                    }
                }

                // what to roll if it hits: the dice and type on the left,
                // where it's from on the right, what else it does under it
                Label {
                    visible: (attackDialog.report.hit || []).length > 0
                    text: attackDialog.report.hit_title || ""
                    color: Theme.text2
                    font.pixelSize: Theme.fsSmall
                    font.bold: true
                    font.letterSpacing: 1
                }
                Rectangle {
                    visible: (attackDialog.report.hit || []).length > 0
                    Layout.fillWidth: true
                    implicitHeight: hitCol.implicitHeight + 20
                    radius: 8
                    color: Theme.surf
                    border.color: Theme.border
                    ColumnLayout {
                        id: hitCol
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                        spacing: 8
                        Repeater {
                            model: attackDialog.report.hit || []
                            delegate: ColumnLayout {
                                objectName: "attackHitLine_" + modelData.source
                                Layout.fillWidth: true
                                spacing: 2
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Label {
                                        text: modelData.dice === "" ? modelData.source
                                              : (index === 0 ? "" : (modelData.dice.charAt(0) === "-" ? "− " : "+ "))
                                                + modelData.dice.replace(/^-/, "") + " " + modelData.type
                                        color: Theme.text
                                        font.pixelSize: Theme.fsBody
                                        font.bold: true
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    Label {
                                        visible: modelData.dice !== ""
                                        text: modelData.source
                                        color: Theme.text2
                                        font.pixelSize: Theme.fsSmall
                                        horizontalAlignment: Text.AlignRight
                                        wrapMode: Text.WordWrap
                                        Layout.maximumWidth: hitCol.width * 0.45
                                    }
                                }
                                Label {
                                    visible: (modelData.note || "") !== ""
                                    text: modelData.note || ""
                                    color: Theme.text2
                                    font.pixelSize: Theme.fsSmall
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                            }
                        }
                        Label {
                            visible: (attackDialog.report.attacks || "") !== ""
                            text: attackDialog.report.attacks || ""
                            color: Theme.text2
                            font.pixelSize: Theme.fsSmall
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // ADD TO THIS HIT, then WITH YOUR BONUS ACTION
                Repeater {
                    model: attackDialog.sectionsNow(false)
                    delegate: ColumnLayout {
                        property var rows: attackDialog.section(modelData.name)
                        Layout.fillWidth: true
                        spacing: 8
                        Label {
                            text: modelData.title
                            color: Theme.text2
                            font.pixelSize: Theme.fsSmall
                            font.bold: true
                            font.letterSpacing: 1
                        }
                        Repeater {
                            model: rows
                            delegate: ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                // the name over a block of choices (Divine Smite)
                                ColumnLayout {
                                    visible: (modelData.head || "") !== ""
                                    Layout.fillWidth: true
                                    Layout.topMargin: 4
                                    spacing: 1
                                    Label {
                                        text: modelData.head || ""
                                        color: Theme.text
                                        font.pixelSize: Theme.fsBody
                                        font.bold: true
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                    }
                                    Label {
                                        visible: (modelData.head_note || "") !== ""
                                        text: modelData.head_note || ""
                                        color: Theme.text2
                                        font.pixelSize: Theme.fsSmall
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                    }
                                }
                                MAttackOption {
                                    Layout.fillWidth: true
                                    opt: modelData
                                    picked: attackDialog.isOn(modelData)
                                    live: attackDialog.isLive(modelData)
                                    onClicked: attackDialog.toggle(modelData)
                                }
                            }
                        }
                    }
                }

                // Missed (Cancel on a critical hit, which can't miss) and It hit
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    spacing: 8
                    MButton {
                        objectName: "attackMissed"
                        visible: !attackDialog.isCheck
                        text: attackDialog.report.miss_button || "Missed"
                        primary: false
                        Layout.fillWidth: true
                        onClicked: {
                            var keys = attackDialog.pickedKeys()
                            attackDialog.close()
                            if (!attackDialog.roll.crit) window.sheetBridge.takeAttackOptions(keys, false)
                        }
                    }
                    MButton {
                        objectName: "attackHit"
                        visible: (attackDialog.report.hit_button || "") !== ""
                        text: attackDialog.report.hit_button || ""
                        Layout.fillWidth: true
                        onClicked: {
                            var keys = attackDialog.pickedKeys()
                            if (attackDialog.isCheck) {
                                attackDialog.taken = true
                                attackDialog.close()
                                window.sheetBridge.takeCheckOptions(keys)
                                return
                            }
                            attackDialog.close()
                            window.sheetBridge.takeAttackOptions(keys, true)
                        }
                    }
                }
            }
        }
    }
    // A longer message to read (Green-Flame Blade's damage)
    MOptionsDialog {
        id: sheetMessageDialog
        objectName: "sheetMessageDialog"
        cancelText: "OK"
    }
    Connections {
        target: window.sheetBridge
        function onActionQuestion(title, question, options) {
            actionQuestionDialog.heading = title
            actionQuestionDialog.message = question
            actionQuestionDialog.options = options.map(function(o) { return {key: o, text: o} })
            actionQuestionDialog.open()
        }
        function onAttackReport(title, report) {
            // an Add on the roll: the same dialog, its new total; what's
            // ticked stays ticked
            if (report.update === true && attackDialog.visible) {
                var keep = ({})
                for (var i = 0; i < (report.options || []).length; i++) {
                    var k = report.options[i].key
                    if (attackDialog.ticked[k]) keep[k] = true
                }
                attackDialog.report = report
                attackDialog.options = report.options || []
                attackDialog.ticked = keep
                return
            }
            attackDialog.heading = title
            attackDialog.ticked = ({})
            attackDialog.taken = false
            attackDialog.report = report
            attackDialog.options = report.options || []
            attackDialog.open()
        }
        function onSheetMessage(title, text) {
            sheetMessageDialog.heading = title
            sheetMessageDialog.message = text
            sheetMessageDialog.options = []
            sheetMessageDialog.open()
        }
    }
    Connections {
        target: window.sheetBridge
        function onRestToastRequested(message) { window.showToast(message) }
        function onToastRequested(message) { window.showToast(message) }
        // level up/down and confirmed choices save the character quietly
        function onAutosaveRequested() { window.saveLoadBridge.autoSave() }
    }
    Connections {
        target: window.saveLoadBridge
        function onToastRequested(message) { window.showToast(message) }
    }
    Timer {
        id: appToastTimer
        interval: 3200
        onTriggered: appToast.visible = false
    }
    Rectangle {
        id: appToast
        // Popup/Drawer content paints through Qt Quick Controls' own
        // Overlay layer, which always renders above every ordinary
        // window Item regardless of z -- a toast fired while the
        // drawer or any dialog (Settings/Save-Load/spell detail/...)
        // is open was rendering fully hidden behind it. Reparenting
        // into that same Overlay layer (where the drawer/dialogs
        // themselves live) fixes that; z still orders it above them
        // there specifically, since Overlay children paint by z, not
        // just open-order.
        parent: Overlay.overlay
        visible: false
        anchors.top: parent.top
        anchors.topMargin: 8
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width - 32, 360)
        height: appToastLabel.implicitHeight + 20
        radius: 10
        color: Theme.surf2
        // plain text, the gold on the border (as desktop's toast)
        border.color: Theme.gold
        z: 10000
        Label {
            id: appToastLabel
            anchors.centerIn: parent
            width: parent.width - 24
            horizontalAlignment: Text.AlignHCenter
            color: Theme.text
            font.pixelSize: Theme.fsBody
            font.bold: true
            wrapMode: Text.WordWrap
        }
    }

    // Easter egg (matches ui_desktop's main_window.py exactly): typing
    // "cheese" anywhere pops a tiny cheese icon in the corner for 5
    // seconds. easterEggBridge is a QGuiApplication-level event filter
    // (see bridge/easter_eggs.py) so it fires regardless of which
    // control currently has focus, same reasoning as desktop's
    // app.installEventFilter(self).
    Connections {
        target: window.easterEggBridge
        function onCheeseTyped() {
            cheeseLabel.visible = true
            cheeseTimer.restart()
        }
    }
    Timer {
        id: cheeseTimer
        interval: 5000
        onTriggered: cheeseLabel.visible = false
    }
    MCheese {
        id: cheeseLabel
        parent: Overlay.overlay
        visible: false
        pixel: 3
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 46
        anchors.rightMargin: 18
        z: 10000
    }

    // Android hardware/gesture back button (delivered as a window close
    // request): close an open utility dialog first (Settings/Save-Load/
    // Dice Roller/Credits -- same as tapping its own X), then pop real
    // navigation history (e.g. Race List -> Race Detail), otherwise
    // toggle the drawer open/closed. Never lets the window actually
    // close from here -- there's no "nothing left to do" case yet since
    // the drawer is always reachable.
    onClosing: (close) => {
        close.accepted = false
        if (settingsDialog.opened) { settingsDialog.close(); return }
        if (saveLoadDialog.opened) { saveLoadDialog.close(); return }
        if (diceRollerDialog.opened) { diceRollerDialog.close(); return }
        if (creditsDialog.opened) { creditsDialog.close(); return }
        if (stackView.depth > 1) {
            stackView.pop()
        } else {
            drawer.opened ? drawer.close() : drawer.open()
        }
    }
}
