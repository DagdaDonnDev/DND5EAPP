"""Credits bridge -- Android equivalent of ui_desktop's CreditsDialog
(dnd_app/ui_desktop/pages/main_window.py). Both read the project's root
README.md directly rather than maintaining a separate credits blurb
that would drift out of sync with it -- this file just has its own
path-resolution logic since it lives at a different depth in the repo
than main_window.py does, so the two can't share a single relative-path
constant.
"""
import os
import sys

from PySide6.QtCore import QObject, Property

_FALLBACK_TEXT = (
    "# MIMIC\n\nA Complete D&D 5e Character Creator & Management Tool.\n\n"
    "Created by Ethan O'Brien.\n\nThank you for downloading MIMIC, and for "
    "supporting the project.\n\n(The full README.md could not be found "
    "alongside this build.)"
)


def _find_readme_text() -> str:
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(getattr(sys, "_MEIPASS", ""), "README.md"))
        candidates.append(os.path.join(os.path.dirname(sys.executable), "README.md"))
    # dnd_app/ui_android/bridge/credits.py -> bridge -> ui_android -> dnd_app -> repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    candidates.append(os.path.join(repo_root, "README.md"))
    # On the phone the app runs from its unpacked private directory --
    # the staging root the build copies README.md into, next to main.py.
    main_mod = sys.modules.get("__main__")
    if getattr(main_mod, "__file__", None):
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(main_mod.__file__)), "README.md"))
    candidates.append(os.path.join(os.getcwd(), "README.md"))
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                continue
    return _FALLBACK_TEXT


class CreditsBridge(QObject):
    """Stateless -- the README doesn't change while the app is running,
    so this is read once and exposed as a constant property."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = _find_readme_text()

    @Property(str, constant=True)
    def readmeText(self):
        return self._text
