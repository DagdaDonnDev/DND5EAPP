import os as _os
_os.environ["QML_DISABLE_DISK_CACHE"] = "1"

#!/usr/bin/env python3
"""Entry point for MIMIC's touch-first (Qt Quick/QML) UI. Scaffold --
currently launches straight into the Race step of the creation wizard;
see dnd_app/ui_android/README.md for the overall plan.
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
from dnd_app.ui_android.bridge.race_wizard import RaceWizardBridge
from dnd_app.ui_android.bridge.ability_wizard import AbilityWizardBridge
from dnd_app.ui_android.bridge.class_wizard import ClassWizardBridge
from dnd_app.ui_android.bridge.equipment_wizard import EquipmentWizardBridge
from dnd_app.ui_android.bridge.save_load_wizard import SaveLoadBridge
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


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("MIMIC")

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
