#!/usr/bin/env python3
"""Entry point for MIMIC's touch-first (Qt Quick/QML) UI: sets up the
bridges over core/, then loads qml/App.qml, which opens on the Start
Menu. See dnd_app/ui_android/README.md for how the app is put together.
"""
import os
import sys

# --- Vendored pure-Python deps -----------------------------------------
# The Android bundler doesn't install pypdf into site-packages, so we
# ship it inside the app package and add it to sys.path at startup.
# pypdf's internal `from pypdf.x import y` imports rely on finding
# itself under its canonical name, so the path shim (rather than a
# renamed package) is the correct approach.
_HERE = os.path.dirname(os.path.abspath(__file__))
_VENDOR = os.path.abspath(os.path.join(_HERE, "..", "_vendor"))
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)
# -------------------------------------

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtQuickControls2 import QQuickStyle
# Must be set before QGuiApplication is created. Without it, Qt Quick
# Controls resolves to a plain desktop-generic style (observed: Fusion)
# on this platform, which ignores the Material.* attached properties
# App.qml sets (theme/accent/background/foreground) -- every input
# control renders with its raw default look (e.g. a plain white
# text field) instead of matching the app's dark theme.
QQuickStyle.setStyle("Material")

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl, QMetaObject, qInstallMessageHandler, QtMsgType

from dnd_app.core.character import new_character
from dnd_app.ui_android.bridge.wizard import (
    RaceWizardBridge, AbilityWizardBridge, ClassWizardBridge, EquipmentWizardBridge,
)
from dnd_app.ui_android.bridge.save_load import SaveLoadBridge
from dnd_app.ui_android.bridge.character_sheet import CharacterSheetBridge
from dnd_app.ui_android.bridge.dice_roller import DiceRollerBridge
from dnd_app.ui_android.bridge.credits import CreditsBridge
from dnd_app.ui_android.bridge.easter_eggs import EasterEggBridge
from dnd_app.ui_android.bridge.app_settings import AppSettingsBridge

_HERE = os.path.dirname(os.path.abspath(__file__))
_QML_DIR = os.path.join(_HERE, "qml")
_IMPORT_DIR = os.path.join(_QML_DIR, "imports")

_QT_MSG_LEVELS = {
    QtMsgType.QtDebugMsg: "DEBUG",
    QtMsgType.QtInfoMsg: "INFO",
    QtMsgType.QtWarningMsg: "WARNING",
    QtMsgType.QtCriticalMsg: "CRITICAL",
    QtMsgType.QtFatalMsg: "FATAL",
}


def _qt_message_handler(msg_type, context, message):
    """Routes Qt's own logging (QML import/parse/type errors, engine
    warnings, etc.) to stderr. Without this, a QML load failure is
    completely silent on Android: it's not a Python exception (no
    traceback), not a native crash (nothing in the crash buffer), and
    Qt's own message logger never reaches logcat on its own -- so
    engine.load() returning with no root objects looks identical to a
    mysterious instant app death with zero diagnostic information."""
    level = _QT_MSG_LEVELS.get(msg_type, "UNKNOWN")
    location = f" ({context.file}:{context.line})" if context.file else ""
    print(f"[MIMIC][QT-{level}] {message}{location}", file=sys.stderr)


qInstallMessageHandler(_qt_message_handler)


def _setup_qml_disk_cache():
    """Keep Qt's compiled-QML cache between launches, so only the first
    launch after an install or update compiles the QML -- every later
    one loads it precompiled, which is most of the UI's startup time.

    The cache lives in a folder named after a hash of the QML files
    themselves, so an update can never pick up stale compiled screens
    (the reason the cache used to be switched off entirely); folders
    left by older versions are removed."""
    import hashlib
    import shutil
    from PySide6.QtCore import QStandardPaths
    digest = hashlib.sha1()
    for dirpath, dirnames, filenames in os.walk(_QML_DIR):
        dirnames.sort()
        for name in sorted(filenames):
            if name.endswith((".qml", ".js")) or name == "qmldir":
                path = os.path.join(dirpath, name)
                digest.update(os.path.relpath(path, _QML_DIR).encode())
                with open(path, "rb") as f:
                    digest.update(f.read())
    base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    if not base:
        os.environ["QML_DISABLE_DISK_CACHE"] = "1"
        return
    root = os.path.join(base, "qmlcache_mimic")
    key = digest.hexdigest()[:16]
    try:
        os.makedirs(os.path.join(root, key), exist_ok=True)
        for old in os.listdir(root):
            if old != key:
                shutil.rmtree(os.path.join(root, old), ignore_errors=True)
    except OSError:
        os.environ["QML_DISABLE_DISK_CACHE"] = "1"
        return
    os.environ.pop("QML_DISABLE_DISK_CACHE", None)
    os.environ["QML_DISK_CACHE_PATH"] = os.path.join(root, key)


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("MIMIC")
    # what goes wrong is noted in mimic_error_log.txt in the save folder
    # (core/error_log.py; the same as desktop's, next to MIMIC.exe)
    from dnd_app.core.error_log import install as _log_errors
    from dnd_app.core.save_load import get_save_dir
    print(f"[MIMIC] error log: {_log_errors(get_save_dir()) or 'none'}", file=sys.stderr)
    # before the engine exists -- Qt reads these when it's created
    _setup_qml_disk_cache()

    # Diagnostics for the "QML fails to load, app silently exits"
    # failure mode -- confirms path resolution (__file__ can behave
    # differently once p4a packages this as .pyc/zipped source) before
    # ever touching the QML engine.
    print(f"[MIMIC] _HERE={_HERE}", file=sys.stderr)
    print(f"[MIMIC] _QML_DIR={_QML_DIR}", file=sys.stderr)
    print(f"[MIMIC] App.qml exists={os.path.exists(os.path.join(_QML_DIR, 'App.qml'))}", file=sys.stderr)
    print(f"[MIMIC] _IMPORT_DIR={_IMPORT_DIR}", file=sys.stderr)
    print(f"[MIMIC] Mimic qmldir exists={os.path.exists(os.path.join(_IMPORT_DIR, 'Mimic', 'qmldir'))}", file=sys.stderr)

    engine = QQmlApplicationEngine()
    engine.addImportPath(_IMPORT_DIR)
    # the Immersive Exhaustion frame (bridge/immersive.py)
    from dnd_app.ui_android.bridge.immersive import ImmersiveFrameProvider
    engine.addImageProvider("immersive", ImmersiveFrameProvider())

    char = new_character()
    race_bridge = RaceWizardBridge(char)
    ability_bridge = AbilityWizardBridge(char)
    class_bridge = ClassWizardBridge(char)
    equipment_bridge = EquipmentWizardBridge(char)
    save_load_bridge = SaveLoadBridge(char)
    sheet_bridge = CharacterSheetBridge(char)
    dice_roller_bridge = DiceRollerBridge()
    credits_bridge = CreditsBridge()
    easter_egg_bridge = EasterEggBridge()
    app.installEventFilter(easter_egg_bridge)
    app_settings_bridge = AppSettingsBridge()

    engine.load(QUrl.fromLocalFile(os.path.join(_QML_DIR, "App.qml")))
    if not engine.rootObjects():
        print("[MIMIC] engine.load() produced NO root objects -- "
              "QML failed to load, exiting", file=sys.stderr)
        sys.exit(1)
    print("[MIMIC] QML loaded successfully, root object obtained", file=sys.stderr)

    # Assigned as plain QML properties AFTER load, not via
    # QQmlContext.setContextProperty() before it -- see App.qml's
    # raceBridge/abilityBridge property comment for why.
    window = engine.rootObjects()[0]
    window.setProperty("raceBridge", race_bridge)
    window.setProperty("abilityBridge", ability_bridge)
    window.setProperty("classBridge", class_bridge)
    window.setProperty("equipmentBridge", equipment_bridge)
    window.setProperty("saveLoadBridge", save_load_bridge)
    window.setProperty("sheetBridge", sheet_bridge)
    window.setProperty("diceRollerBridge", dice_roller_bridge)
    window.setProperty("creditsBridge", credits_bridge)
    window.setProperty("easterEggBridge", easter_egg_bridge)
    window.setProperty("appSettingsBridge", app_settings_bridge)
    # Applies the app's own remembered theme before the Start Menu is
    # ever shown -- can't run from Component.onCompleted since
    # appSettingsBridge is only assigned here, after engine.load().
    QMetaObject.invokeMethod(window, "applyStartupTheme")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
