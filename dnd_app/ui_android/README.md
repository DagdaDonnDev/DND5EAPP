# ui_android — MIMIC's touch-first Android UI

MIMIC's Android app: a Qt Quick/QML UI over the same `core/` and
`data/` the desktop app uses, packaged into an APK with buildozer and
python-for-android (see `packaging/android/`).

## Plan

- **Framework:** Qt Quick/QML rather than QtWidgets. `ui_desktop/` is
  QtWidgets, which is a poor fit for touch (no gestures, tiny desktop-
  scaled click targets, hover-only tooltips as the sole way to see a
  lot of information) and PyInstaller/Windows-oriented packaging.
  Qt's own Android deployment tooling is built around Qt Quick, not
  QtWidgets, so this is the path of least resistance for actually
  shipping an APK from PySide6.
- **Not a port.** The desktop UI's screen layouts (side-by-side
  multi-column tabs, dense stat bars, double-click-to-rename, hover-
  dependent affordances) don't translate to a phone screen and won't
  be carried over as-is. Each screen gets redesigned for touch and
  small-screen real estate, starting from what the player actually
  needs visible at once on a phone.
- **Shared with desktop:** `dnd_app/core/` and `dnd_app/data/` — the
  character model, calculator, builder, save/load, and all game-rules
  data. Zero Qt dependency in either (core/immersive.py's frame painter
  imports QtGui only when it's called), so nothing there needs to change
  for this to work; both UIs read and write the same character dict
  shape and the same save-file format.
- **Not shared:** everything in `dnd_app/ui_desktop/`. No QtWidgets
  code is reused directly; QML screens are new files here.

## Status

Working and shipping. What's here:

- `main.py` — app entry point; `bridge/` — one QObject bridge per area
  (race/ability/class/equipment wizards, the character sheet, save/load,
  dice roller, settings, credits, easter eggs), each a thin layer over
  `core/`.
- `qml/` — the screens: Start Menu, the creation wizard, every sheet
  tab (abilities, proficiencies, combat, actions, spells, equipment,
  features, companions, infusions, choices/level-up, notes), the dice
  roller, Save & Export, settings and credits.
- `qml/imports/Mimic/` — the theme (all 26 desktop themes), shared
  components (`MButton`, `MCard`, `MIcon`, …) and `IconData.js`, which
  is GENERATED from `data/icon_data.py` so both apps draw the
  same icons. Regenerate with `python3 -m dnd_app.data.icon_data`
  (the Android clean build does this automatically).

Conventions every screen follows:

- **Buttons for what you do often** (Cast, Equip, Drink, Use), a
  **magnifying glass** for details, and **press-and-hold** for the rare
  actions -- a small menu (`MOptionsDialog`) to prepare/favourite/remove
  a spell, attune/study/remove a magic item, or set how many of an item
  you have. Browsers (adding spells/items) keep explicit View + Add.
- **Stacks show their count as a button** beside View; it opens the
  amount dialog (`MSpinBox` with typing, and `holdStep: 5` so holding
  − / + moves in fives). 0 removes the item.
- **Colour means rarity** on magic items (`Theme.rarityColor()`), never
  "equipped" -- equipped rows show a bright icon, bold name and an
  "Equipped" tag instead. The colour goes on a border or a small bar,
  never on text (coloured text, navy on dark especially, is hard to read).
- **Every dialog darkens what's behind it** (`Overlay.modal`), and
  button icons/text are centred on the whole button.
- **Browsers are a search box and a funnel.** The filters (category,
  slot, rarity, level, class...) live in an `MFilterDrawer` that slides
  in from the right; the `MFilterButton` at the end of the search row
  opens it and shows how many filters are set. The filters keep their
  own ids, so each browser reads them exactly as before.

Saving: characters are saved in the shared Documents/MIMIC Characters
folder (the app's private one if shared storage can't be written; saves
from before are copied across once), or a folder picked in Settings
(inside Documents or Download -- the only places Android lets apps
write). They auto-save on creation, level up/down and confirmed choices.
Exports (character file, text summary, PDF sheet) go into a folder per
character beside the saves, so a character's sheet and file stay
together; "Open folder" on Save & Export opens it in the Files app, and
"Save elsewhere…" puts a copy anywhere through the system picker. The
file format is the desktop's.
