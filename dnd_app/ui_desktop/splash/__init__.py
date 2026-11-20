"""
Startup splash screen.

Shows instant visual feedback while the main window constructs (parsing
~800 magic items, 400+ spells, building every tab widget takes a couple of
seconds on some machines, which otherwise looks like a frozen/dead app).

What it shows:
  - dnd_app/core/splash.gif in the theme's colours (core/splash_art.py;
    the Android app plays the same frames), when it's there
  - otherwise dnd_app/ui_desktop/splash/splash.png (static)
If neither file exists, falls back to a lightweight branded placeholder so
there's still something on screen immediately, rather than a blank frame.

If a splash.gif is present, callers can wait for one full playback loop
before revealing the main window (see loop_finished / loop_complete below),
so the animation is never cut off mid-cycle even on a fast-loading machine.

Author: Ethan O'Brien
Date: 2026-08-20
"""
import os
from PySide6.QtWidgets import QSplashScreen
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize, Signal, QTimer

# splash.png lives in this package folder; splash.gif in core, beside
# splash_art.py, which themes it for both apps.
_ASSETS = os.path.dirname(__file__)
_GIF = os.path.join(os.path.dirname(os.path.dirname(_ASSETS)), "core", "splash.gif")
_PNG = os.path.join(_ASSETS, "splash.png")


def _fallback_pixmap(size=QSize(480, 300)) -> QPixmap:
    """A minimal branded placeholder — dark background, gold app title,
    used only if neither splash.gif nor splash.png is there."""
    pm = QPixmap(size)
    pm.fill(QColor("#0f1117"))
    p = QPainter(pm)
    p.setPen(QColor("#2e3554"))
    p.drawRect(2, 2, size.width()-4, size.height()-4)
    p.setPen(QColor("#d4a820"))
    f = QFont(); f.setPointSize(22); f.setBold(True)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "MIMIC")
    p.setPen(QColor("#7a7898"))
    f2 = QFont(); f2.setPointSize(10)
    p.setFont(f2)
    p.drawText(pm.rect().adjusted(0, 0, 0, -24), Qt.AlignHCenter | Qt.AlignBottom,
               "Loading…")
    p.end()
    return pm


class AnimatedSplash(QSplashScreen):
    """The startup animation: the mimic chest of splash.gif in the colours of
    the app's theme (core/splash_art.py), at its own speed, its last frame
    carrying the name.

    loop_complete: True once every frame has played at least once (or
        right away when there's no animation to wait on).
    loop_finished: emitted once, the moment loop_complete becomes True.
        Callers holding the splash open for a full cycle check
        loop_complete first, and otherwise connect to this.
    """
    loop_finished = Signal()

    def __init__(self, theme: str = None):
        self._frames = []      # each frame's time on screen; empty: no animation
        self._theme = theme
        self._i = 0
        self.loop_complete = False
        if os.path.exists(_GIF):
            try:
                from dnd_app.core import splash_art
                if theme is None:
                    from dnd_app.core.app_settings import get_app_theme
                    self._theme = get_app_theme()
                self._art = splash_art
                self._frames = splash_art.delays()
                pm = QPixmap.fromImage(splash_art.frame(self._theme, 0))
            except Exception:
                self._frames = []
        if self._frames:
            pass
        elif os.path.exists(_PNG):
            pm = QPixmap(_PNG)
            if pm.isNull():
                pm = _fallback_pixmap()
        else:
            pm = _fallback_pixmap()
        super().__init__(pm)
        # a rounded card (see-through corners) that never takes the focus
        # or sits over other windows: you can carry on elsewhere while it
        # loads
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        if self._frames:
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self._next)
            self._timer.start(self._frames[0])
            # the still image the .exe shows first is Obsidian's first
            # frame (it's fixed when the .exe is built): in another theme
            # the animation starts from it and fades into the theme's
            # colours over half a second, rather than jumping
            self._fade = 0
            if self._theme != "(Dark) Obsidian":
                try:
                    self._still = self._art.frame("(Dark) Obsidian", 0)
                    self.setPixmap(QPixmap.fromImage(self._still))
                    self._fader = QTimer(self)
                    self._fader.timeout.connect(self._fade_step)
                    self._fader.start(50)
                except Exception:
                    pass
        else:
            # nothing to loop, so nothing to wait on
            self.loop_complete = True

    def _fade_step(self):
        """One step of the fade from the .exe's still image into the theme."""
        from PySide6.QtGui import QPainter
        self._fade += 1
        k = min(1.0, self._fade / 10)
        img = self._still.copy()
        p = QPainter(img)
        p.setOpacity(k)
        p.drawImage(0, 0, self._art.frame(self._theme, self._i))
        p.end()
        self.setPixmap(QPixmap.fromImage(img))
        if k >= 1.0:
            self._fader.stop()

    def _next(self):
        last = len(self._frames) - 1
        if self._i >= last:
            # the end: it stays on its last frame, the name showing, a
            # moment longer (splash_art.HOLD) before the app shows
            if not getattr(self, "_held", False):
                self._held = True
                self._timer.start(getattr(self._art, "HOLD", 0))
                return
            if not self.loop_complete:
                self.loop_complete = True
                self.loop_finished.emit()
            return
        self._i += 1
        self._timer.start(self._frames[self._i])
        if getattr(self, "_fader", None) is not None and self._fader.isActive():
            return                       # (the fade draws this frame)
        try:
            self.setPixmap(QPixmap.fromImage(self._art.frame(self._theme, self._i)))
        except Exception:
            pass

    def finish_and_close(self, widget):
        """It fades out (a quarter of a second), then the window it was
        covering for shows."""
        if self._frames:
            self._timer.stop()
        from PySide6.QtCore import QPropertyAnimation
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(250)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)

        def done():
            widget.show()
            self.finish(widget)
        anim.finished.connect(done)
        self._fade_out = anim
        anim.start()
