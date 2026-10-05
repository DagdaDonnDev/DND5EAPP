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
    // direct type instantiation both work correctly). Every screen
    // this drawer can navigate to needs its own named Component here
    // for that reason. Only "Race" is real today -- the rest are
    // placeholders so the nav shape (and the drawer itself) doesn't
    // need rebuilding as each one comes online.
    Component { id: startMenuComp; StartMenuScreen {} }
    Component { id: raceListComp; RaceListScreen {} }
    Component { id: abilitiesComp; AbilitiesScreen {} }
    Component { id: classComp; ClassScreen {} }
    Component { id: equipmentComp; EquipmentScreen {} }
    Component { id: sheetComp; SheetCombatScreen {} }
    Component { id: sheetActionsComp; SheetActionsScreen {} }
    Component { id: sheetAbilitiesComp; SheetAbilitiesScreen {} }
    Component { id: sheetProficienciesComp; SheetProficienciesScreen {} }
    Component { id: sheetSpellsComp; SheetSpellsScreen {} }
    Component { id: sheetEquipmentComp; SheetEquipmentScreen {} }
    Component { id: sheetCompanionsComp; SheetCompanionsScreen {} }
    Component { id: sheetFeaturesComp; SheetFeaturesScreen {} }
    Component { id: sheetInfusionsComp; SheetInfusionsScreen {} }
    Component { id: sheetChoicesComp; SheetChoicesScreen {} }
    Component { id: sheetNotesComp; SheetNotesScreen {} }

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
            { label: "Notes", screen: sheetNotesComp, enabled: true },
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
        stackView.replace(startMenuComp)
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
        stackView.replace(raceListComp)
    }
    function loadCharacterIntoSheet(filepath) {
        // A saved character is already complete (confirmRace()/
        // confirmClass()/etc. all require a valid state to save at
        // all), so loading one goes straight to the sheet rather than
        // back through the wizard.
        if (saveLoadBridge.loadCharacterFrom(filepath)) {
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
            stackView.replace(sheetComp)
        }
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
            stackView.replace(sheetComp)
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
    function advanceToAbilities() { stackView.replace(abilitiesComp) }
    function advanceToClass() { stackView.replace(classComp) }
    function advanceToEquipment() { stackView.replace(equipmentComp) }
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
        SettingsScreen {}
    }
    MFullPageDialog {
        id: saveLoadDialog
        objectName: "saveLoadDialog"
        dialogTitle: "Save & Export"
        SaveLoadScreen {}
    }
    MFullPageDialog {
        id: diceRollerDialog
        objectName: "diceRollerDialog"
        dialogTitle: "Dice Roller"
        DiceRollerScreen {}
    }
    MFullPageDialog {
        id: creditsDialog
        objectName: "creditsDialog"
        dialogTitle: "Credits"
        CreditsScreen {}
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
                stackView.replace(screen)
            }
            drawer.close()
        }
        onSectionSelected: (screen, sectionName) => {
            window.pendingScrollSection = sectionName
            if (screen) {
                stackView.replace(screen)
            }
            drawer.close()
        }
    }

    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: startMenuComp
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
        appToastTimer.restart()
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
        border.color: Qt.rgba(Theme.amber.r, Theme.amber.g, Theme.amber.b, 0.53)
        z: 10000
        Label {
            id: appToastLabel
            anchors.centerIn: parent
            width: parent.width - 24
            horizontalAlignment: Text.AlignHCenter
            color: Theme.gold
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
