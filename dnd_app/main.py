#!/usr/bin/env python3
"""Android app entry point.

The Android clean build (packaging/android/clean_build_android.sh) copies
this file to the root of the APK's app folder, next to dnd_app/, as the
main.py python-for-android starts; it only starts dnd_app/ui_android/main.py,
so the app's code stays in one place.
"""
import os
import sys

# the folder dnd_app/ is in: this file's own in the APK, its parent here
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE) == "dnd_app" else _HERE
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dnd_app.ui_android import main as _ui_main

if __name__ == "__main__":
    _ui_main.main()
