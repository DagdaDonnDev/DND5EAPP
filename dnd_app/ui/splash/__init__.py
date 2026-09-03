"""
Startup splash screen.

Shows instant visual feedback while the main window constructs (parsing
~800 magic items, 400+ spells, building every tab widget takes a couple of
seconds on some machines, which otherwise looks like a frozen/dead app).

Drop-in support for a custom splash image:
  - dnd_app/ui/splash/splash.gif  (animated — preferred if present)
  - dnd_app/ui/splash/splash.png  (static — used if no gif)
If neither file exists, falls back to a lightweight branded placeholder so
there's still something on screen immediately, rather than a blank frame.

If a splash.gif is present, callers can wait for one full playback loop
before revealing the main window (see loop_finished / loop_complete below),
so the animation is never cut off mid-cycle even on a fast-loading machine.

Author: Ethan O'Brien
Date: 2026-08-20
"""
import os
from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QMovie, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize, Signal, QObject

# splash.gif/splash.png now live in this same package folder (co-located
# with the code that reads them) instead of a separate top-level assets/
# directory, so no more climbing two dirs up to find them.
_ASSETS = os.path.dirname(__file__)
_GIF = os.path.join(_ASSETS, "splash.gif")
_PNG = os.path.join(_ASSETS, "splash.png")


def _fallback_pixmap(size=QSize(480, 300)) -> QPixmap:
    """A minimal branded placeholder — dark background, gold app title,
    used only if no splash.gif/splash.png has been provided."""
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
    """QSplashScreen with optional QMovie (gif) playback.

    loop_complete: True once the gif has played through every one of its
        frames at least once (or immediately, if there's no gif to wait on
        — a static PNG or the placeholder never blocks the caller).
    loop_finished: Signal emitted exactly once, the moment loop_complete
        first becomes True. Callers that want to hold the splash open for
        a full cycle should check loop_complete first (it may already be
        True) and otherwise connect to this signal.
    """
    loop_finished = Signal()

    def __init__(self):
        self._movie = None
        self._frames_seen = 0
        self.loop_complete = False
        if os.path.exists(_GIF):
            self._movie = QMovie(_GIF)
            self._movie.jumpToFrame(0)
            pm = self._movie.currentPixmap()
            if pm.isNull():
                pm = _fallback_pixmap()
        elif os.path.exists(_PNG):
            pm = QPixmap(_PNG)
            if pm.isNull():
                pm = _fallback_pixmap()
        else:
            pm = _fallback_pixmap()
        super().__init__(pm)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        if self._movie is not None:
            self._movie.frameChanged.connect(self._on_frame)
            self._movie.start()
        else:
            # No animation to wait on (static image or placeholder) —
            # there's nothing to loop, so don't make callers wait for it.
            self.loop_complete = True

    def _on_frame(self, _idx):
        self.setPixmap(self._movie.currentPixmap())
        if self.loop_complete:
            return
        self._frames_seen += 1
        total = self._movie.frameCount()
        # frameCount() can be -1 for a stream Qt hasn't fully parsed yet;
        # treat that defensively as "never completes" rather than raising.
        if total > 0 and self._frames_seen >= total:
            self.loop_complete = True
            self.loop_finished.emit()

    def finish_and_close(self, widget):
        if self._movie is not None:
            self._movie.stop()
        self.finish(widget)
