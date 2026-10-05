"""QObject bridge classes exposing dnd_app.core/dnd_app.data to QML.

Each bridge is a thin adapter: it holds no game logic of its own, only
translates between plain Python/dict state (the same character dict
shape ui_desktop reads and writes) and Qt's Property/Signal/Slot
system that QML data-binds against.
"""
