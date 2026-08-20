#!/usr/bin/env python3
"""
Main module.

Entry point for MIMIC (D&D 5e Character Creator). Adds the project
root to sys.path and launches the PySide6 main window.

Author: Ethan O'Brien
Date: 2026-08-20
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dnd_app.ui.main_window import main
if __name__ == "__main__":
    main()
