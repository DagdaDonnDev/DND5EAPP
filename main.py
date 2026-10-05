#!/usr/bin/env python3
"""Android build entry point wrapper.

pyside6-android-deploy requires an `input_file` at the project root
(see packaging/android/pysidedeploy.spec's project_dir + input_file).
The real Android UI entry point lives at dnd_app/ui_android/main.py --
this wrapper just imports and runs it, so the actual app code stays in
one place. Required by packaging/android/pysidedeploy.spec: do not
rename or move this file.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dnd_app.ui_android import main as _ui_main

if __name__ == "__main__":
    _ui_main.main()
