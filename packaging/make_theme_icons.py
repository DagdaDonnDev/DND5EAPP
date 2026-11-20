"""Writes the app icon in each theme's colours (core/app_icon.py), for the
25 themes other than the default (Dark) Obsidian, which keeps the icon as
drawn. Run from the DND5EAPP folder after changing a theme's colours:

    python packaging/make_theme_icons.py

  dnd_app/core/theme_icons/<theme>.png       the desktop window and taskbar
                                             icon (256 px)
  packaging/android/theme_icons/<theme>/     the Android launcher icon:
      icon_foreground.png, icon_background.png   (Android 8+, 432 px)
      icon.png                                   (older Android, 192 px)
  dnd_app/ui_desktop/splash/splash.png       the .exe's still splash: the
                                             animation's first frame, hard-edged
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
from dnd_app.data.themes import THEMES
from dnd_app.core.app_icon import recolour, slug, DEFAULT, ICON_DIR

ANDROID = os.path.join(ROOT, "packaging", "android")
desk = QIcon(os.path.join(ROOT, "dnd_app", "ui_desktop", "icon.ico")).pixmap(256, 256).toImage()
launcher = QImage(os.path.join(ANDROID, "icon.png")).scaled(192, 192, Qt.KeepAspectRatio, Qt.SmoothTransformation)
fg = QImage(os.path.join(ANDROID, "icon_foreground.png"))
bg = QImage(os.path.join(ANDROID, "icon_background.png"))
os.makedirs(ICON_DIR, exist_ok=True)
for theme in THEMES:
    if theme == DEFAULT:
        continue
    s = slug(theme)
    recolour(desk, theme).save(os.path.join(ICON_DIR, s + ".png"))
    out = os.path.join(ANDROID, "theme_icons", s)
    os.makedirs(out, exist_ok=True)
    recolour(launcher, theme).save(os.path.join(out, "icon.png"))
    recolour(fg, theme).save(os.path.join(out, "icon_foreground.png"))
    recolour(bg, theme).save(os.path.join(out, "icon_background.png"))
    print(theme, "->", s)

from dnd_app.core.splash_art import still
still().save(os.path.join(ROOT, "dnd_app", "ui_desktop", "splash", "splash.png"))
print("splash.png")
