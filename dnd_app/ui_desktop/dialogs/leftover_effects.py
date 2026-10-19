"""Effects still on from last time (desktop): a saved character opened
again with effects a short rest would end (Rage, Bladesong, a potion's
hour...) asks whether they're over. Ticked ones end. The rules live in
core/action_use.py (leftover_effects); Android asks the same in App.qml."""
from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

TITLE = "Effects still on"
TEXT = ("These were on when this character was last saved. Have they ended? "
        "Untick any that are still going.")


class LeftoverEffectsDialog(QDialog):
    def __init__(self, names, parent=None):
        super().__init__(parent)
        from dnd_app.ui_desktop.style.theme import sync_globals
        t = {}
        sync_globals(t)
        self.setWindowTitle(TITLE)
        self.setMinimumWidth(420)
        self.setStyleSheet(f"QDialog{{background:{t['BG']};}}")
        root = QVBoxLayout(self); root.setContentsMargins(20, 18, 20, 18); root.setSpacing(12)
        title = QLabel(TITLE)
        title.setStyleSheet(f"color:{t['GOLD2']};font-size:{t['FS_HEAD']}px;font-weight:700;")
        root.addWidget(title)
        text = QLabel(TEXT); text.setWordWrap(True)
        text.setStyleSheet(f"color:{t['TEXT']};font-size:{t['FS_BODY']}px;")
        root.addWidget(text)
        self._boxes = []
        for name in names:
            box = QCheckBox(name); box.setChecked(True); box.setObjectName(f"leftover_{name}")
            box.setStyleSheet(f"QCheckBox{{color:{t['TEXT']};font-size:{t['FS_BODY']}px;}}")
            root.addWidget(box)
            self._boxes.append(box)
        btns = QHBoxLayout(); btns.addStretch()
        style = (f"QPushButton{{background:{t['SURF2']};color:{t['TEXT']};border:1px solid {{b}};"
                 f"border-radius:7px;padding:4px 20px;font-size:{t['FS_BODY']}px;font-weight:700;}}"
                 f"QPushButton:hover{{background:{t['SURF3']};}}")
        keep = QPushButton("Keep all"); keep.setFixedHeight(34)
        keep.setStyleSheet(style.replace("{b}", t["BORDER2"]))
        keep.clicked.connect(self.reject)
        end = QPushButton("End ticked"); end.setFixedHeight(34); end.setObjectName("leftoverEnd")
        end.setStyleSheet(style.replace("{b}", t["GOLD"]))
        end.clicked.connect(self.accept)
        btns.addWidget(keep); btns.addWidget(end)
        root.addLayout(btns)

    def ticked(self):
        return [b.text() for b in self._boxes if b.isChecked()]
