# ui_android — MIMIC's touch-first Android UI

MIMIC's Android app: a Qt Quick/QML UI over the same `core/` and
`data/` the desktop app uses, packaged into an APK with buildozer and
python-for-android (see `packaging/android/` and `installer/android/`).

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
  data. Zero Qt dependency in either, so nothing there needs to change
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
  is GENERATED from `ui_desktop/icon_data.py` so both apps draw the
  same icons. Regenerate with `python3 -m dnd_app.ui_desktop.icon_data`
  (the Android clean build does this automatically).

Saving: the in-app list lives in the app's private Documents folder;
characters auto-save on creation, level up/down and confirmed choices;
Export writes a copy anywhere through the system save picker, plus
plain-text and PDF exports. The file format is the desktop's.
