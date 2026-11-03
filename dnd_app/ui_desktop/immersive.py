"""The desktop side of Immersive Health and Immersive Exhaustion. The rules,
the settings and the frame's look are shared with Android in
core/immersive.py; this file puts them on the character sheet.

  * Health: a desaturation filter over the whole sheet -- Qt's
    QGraphicsColorizeEffect in black, which turns colours towards grey
    without darkening them, so text stays as readable as before. It eases
    to its new strength over half a second (straight there on Reduced),
    and is removed entirely at full HP.
  * Exhaustion: the sheet's contents move in from the edges, and an
    overlay that lets every click through paints the frame around them.
  * A light timer checks the character a few times a second, so every way
    HP or exhaustion can change -- damage, healing, rests, typing in a new
    number, Wild Shape, loading -- is picked up without wiring up each one.
  * The first time either effect shows, a short note explains it and
    offers both settings.
"""
from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QTimer, QVariantAnimation, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QComboBox, QDialog, QFrame, QGraphicsColorizeEffect, QHBoxLayout,
                               QLabel, QPushButton, QVBoxLayout, QWidget)

from dnd_app.core import immersive as rules


class _FrameOverlay(QWidget):
    """The exhaustion frame, drawn over the whole sheet. It takes no clicks
    and paints nothing but the frame image from core/immersive.py."""

    def __init__(self, sheet):
        super().__init__(sheet)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._level, self._setting = 0, "Off"
        self._img = self._old = None
        self._mix = 1.0                      # 0 -> 1 while a new frame fades in
        self._fade = QVariantAnimation(self)
        self._fade.setDuration(350)
        self._fade.valueChanged.connect(self._on_fade)
        self._resize_timer = QTimer(self, singleShot=True, interval=80)
        self._resize_timer.timeout.connect(self._render)
        self.hide()

    def set_frame(self, level: int, setting: str, animate: bool):
        self._level, self._setting = level, setting
        old = self._img
        self._render()
        if animate and self._img is not None:
            # the new frame fades in over the old one
            self._old, self._mix = old, 0.0
            self._fade.stop(); self._fade.setStartValue(0.0); self._fade.setEndValue(1.0); self._fade.start()

    def follow(self, rect):
        """Keep covering the sheet; redraw once a resize settles."""
        self.setGeometry(rect)
        if self._level > 0:
            self._resize_timer.start()

    def _render(self):
        if self._level <= 0:
            self._img = None
            self.hide()
            return
        self._img = rules.render_frame(self.width(), self.height(), self._level, self._setting,
                                       phone=False, scale=self.devicePixelRatioF())
        self.show(); self.raise_(); self.update()

    def _on_fade(self, v):
        self._mix = float(v)
        if self._mix >= 1.0:
            self._old = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if self._old is not None and self._mix < 1.0:
            p.setOpacity(1.0 - self._mix)
            p.drawImage(0, 0, self._old)
        if self._img is not None:
            p.setOpacity(self._mix)
            p.drawImage(0, 0, self._img)
        p.end()


class SheetImmersion(QObject):
    """Immersive Health and Immersive Exhaustion for one open sheet."""

    def __init__(self, sheet):
        super().__init__(sheet)
        self.sheet = sheet
        self._frame = _FrameOverlay(sheet)
        self._effect = None            # the colour filter, while there is one
        self._anim = None
        self._fade_target = 0.0
        self._frame_state = (0, "Off")
        self._timer = QTimer(self, interval=200)
        self._timer.timeout.connect(self.update)
        self._timer.start()
        QTimer.singleShot(0, lambda: self.update(animate=False))

    # ── called by the sheet ───────────────────────────────────────────
    def resized(self):
        self._frame.follow(self.sheet.rect())
        self._keep_death_screen_on_top()

    def update(self, animate: bool = True):
        char = self.sheet.char
        # 1. Health: how much colour to take out
        h_setting = rules.mode("health")
        fade = rules.health_fade(char, h_setting)
        if abs(fade - self._fade_target) > 0.004:
            self._fade_target = fade
            self._set_fade(fade, animate and h_setting == "Full")
        # 2. Exhaustion: the frame, and the page moved in to fit inside it
        e_setting = rules.mode("exhaustion")
        level = rules.frame_level(char, e_setting)
        if (level, e_setting) != self._frame_state:
            self._frame_state = (level, e_setting)
            inset = rules.frame_px(level)
            self.sheet.setContentsMargins(inset, inset, inset, inset)
            self._frame.setGeometry(self.sheet.rect())
            self._frame.set_frame(level, e_setting, animate and e_setting == "Full")
            self._keep_death_screen_on_top()
        # 3. the first time either effect shows, explain it (once, ever)
        if (fade > 0 or level > 0) and not rules.prompt_seen():
            rules.mark_prompt_seen()
            QTimer.singleShot(300, self._show_prompt)

    # ── the colour filter ─────────────────────────────────────────────
    def _set_fade(self, value: float, animate: bool):
        if self._anim is not None:
            self._anim.stop()
            self._anim = None
        current = self._effect.strength() if self._effect is not None else 0.0
        if value <= 0 and current <= 0:
            self._drop_effect()
            return
        if self._effect is None:
            self._effect = QGraphicsColorizeEffect()
            self._effect.setColor(QColor(0, 0, 0))     # grey, without darkening
            self._effect.setStrength(0.0)
            self.sheet.setGraphicsEffect(self._effect)  # (the sheet owns it now)
        if not animate:
            self._effect.setStrength(value)
            if value <= 0:
                self._drop_effect()
            return
        self._anim = QPropertyAnimation(self._effect, b"strength", self)
        self._anim.setDuration(500)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim.setStartValue(current)
        self._anim.setEndValue(value)
        if value <= 0:
            self._anim.finished.connect(self._drop_effect)
        self._anim.start()

    def _drop_effect(self):
        # at full HP there's no filter at all, so it costs nothing
        if self._effect is not None:
            self.sheet.setGraphicsEffect(None)       # (deletes it)
            self._effect = None

    def _keep_death_screen_on_top(self):
        for child in self.sheet.children():
            if isinstance(child, QFrame) and child.objectName() == "death_overlay":
                child.raise_()

    def _show_prompt(self):
        if self.sheet.isVisible():
            ImmersivePrompt(self.sheet.window()).exec()
            self.update(animate=False)


def mode_combo(kind: str, on_change=None) -> QComboBox:
    """A Full / Reduced / Off picker for one of the two settings, saved as
    soon as it changes."""
    combo = QComboBox()
    for m in rules.MODES:
        combo.addItem(m)
        combo.setItemData(combo.count() - 1, rules.MODE_HELP[m], Qt.ToolTipRole)
    combo.setCurrentText(rules.mode(kind))

    def changed(value):
        rules.set_mode(kind, value)
        if on_change:
            on_change()
    combo.currentTextChanged.connect(changed)
    return combo


class ImmersivePrompt(QDialog):
    """The one-time note the first time an effect shows: what it is, and
    both settings to change straight away."""

    def __init__(self, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals
        t = {}
        sync_globals(t)
        self.setWindowTitle(rules.PROMPT_TITLE)
        self.setMinimumWidth(460)
        self.setStyleSheet(f"QDialog{{background:{t['BG']};}}")
        root = QVBoxLayout(self); root.setContentsMargins(20, 18, 20, 18); root.setSpacing(12)
        title = QLabel(rules.PROMPT_TITLE)
        title.setStyleSheet(f"color:{t['GOLD2']};font-size:{t['FS_HEAD']}px;font-weight:700;")
        root.addWidget(title)
        text = QLabel(rules.PROMPT_TEXT); text.setWordWrap(True)
        text.setStyleSheet(f"color:{t['TEXT']};font-size:{t['FS_BODY']}px;")
        root.addWidget(text)
        for kind in ("health", "exhaustion"):
            name, what = rules.SETTINGS[kind]
            row = QHBoxLayout(); row.setSpacing(10)
            col = QVBoxLayout(); col.setSpacing(2)
            lbl = QLabel(name); lbl.setStyleSheet(f"color:{t['TEXT']};font-size:{t['FS_BODY']}px;font-weight:700;")
            sub = QLabel(what); sub.setWordWrap(True)
            sub.setStyleSheet(f"color:{t['TEXT2']};font-size:{t['FS_SMALL']}px;")
            col.addWidget(lbl); col.addWidget(sub)
            row.addLayout(col, 1)
            row.addWidget(mode_combo(kind), 0, Qt.AlignTop)
            root.addLayout(row)
        btns = QHBoxLayout(); btns.addStretch()
        ok = QPushButton("Done"); ok.setFixedHeight(34); ok.clicked.connect(self.accept)
        ok.setStyleSheet(f"QPushButton{{background:{t['SURF2']};color:{t['TEXT']};border:1px solid {t['GOLD']};"
                         f"border-radius:7px;padding:4px 24px;font-size:{t['FS_BODY']}px;font-weight:700;}}"
                         f"QPushButton:hover{{background:{t['SURF3']};}}")
        btns.addWidget(ok)
        root.addLayout(btns)
