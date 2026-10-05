"""Background + Starting Class step of the touch wizard -- QML-facing
bridge mirroring ui_desktop's Step3Class. At character-creation time
this step is simpler than it sounds: no subclass or level-timeline
picker here (those come later, at whatever level unlocks them, via the
sheet's own level-up flow) -- just name, alignment, a searchable
background choice (+ its optional feat), and a starting class.
"""
from PySide6.QtCore import QObject, QAbstractListModel, QModelIndex, Qt, Signal, Slot, Property

from dnd_app.data.phbCommon.backgrounds import BACKGROUND_NAMES, get_background
from dnd_app.data.phb2014.classes import CLASS_NAMES, CLASS_DICT
from dnd_app.core.builder import rebuild

ALIGNMENTS = [
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil", "Neutral Evil", "Chaotic Evil",
]


class BackgroundListModel(QAbstractListModel):
    """All 99 backgrounds, filterable by name -- same shape as
    RaceListModel so the two searchable pickers behave identically."""

    NameRole = Qt.UserRole + 1
    SourceRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all = list(BACKGROUND_NAMES)
        self._filtered = list(self._all)

    def roleNames(self):
        return {self.NameRole: b"name", self.SourceRole: b"source"}

    def rowCount(self, parent=QModelIndex()):
        return len(self._filtered)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        name = self._filtered[index.row()]
        if role == self.NameRole or role == Qt.DisplayRole:
            return name
        if role == self.SourceRole:
            return (get_background(name) or {}).get("source", "")
        return None

    @Slot(str)
    def setFilter(self, text: str):
        self.beginResetModel()
        t = text.lower().strip()
        self._filtered = [n for n in self._all if t in n.lower()] if t else list(self._all)
        self.endResetModel()


class ClassWizardBridge(QObject):
    nameChanged = Signal()
    alignmentChanged = Signal()
    backgroundChanged = Signal()
    classChanged = Signal()
    errorChanged = Signal()
    classConfirmed = Signal()

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self._name = char.get("name", "")
        self._alignment = char.get("alignment", "True Neutral")
        self._background = char.get("background", "")
        self._background_feat = (char.get("_choices") or {}).get("background_feat", "")
        classes = char.get("classes") or []
        self._class_name = classes[0]["class"] if classes else ""
        self._bg_model = BackgroundListModel()
        self._error = ""
        self._confirmed_once = False

    @Slot()
    def refresh(self):
        """Re-sync all fields from the character dict. Needed for the
        drawer-nav revisit case (consistent with the other wizard
        bridges' refresh()) and for a character just loaded via
        Save/Load, which mutates the shared char dict in place without
        going through setName()/selectBackground()/etc."""
        self._name = self.char.get("name", "")
        self._alignment = self.char.get("alignment", "True Neutral")
        self._background = self.char.get("background", "")
        self._background_feat = (self.char.get("_choices") or {}).get("background_feat", "")
        classes = self.char.get("classes") or []
        self._class_name = classes[0]["class"] if classes else ""
        # Re-derived from the dict (only confirmClass() writes "classes"),
        # same as raceConfirmedOnce -- otherwise it stays True from the
        # previous character after New Character, leaving the drawer's
        # Equipment step unlocked on a blank character.
        self._confirmed_once = bool(classes)
        self.nameChanged.emit()
        self.alignmentChanged.emit()
        self.backgroundChanged.emit()
        self.classChanged.emit()
        self.classConfirmed.emit()

    # ── Static lists ───────────────────────────────────────────────
    @Property(QObject, constant=True)
    def backgroundModel(self):
        return self._bg_model

    @Property(list, constant=True)
    def alignments(self):
        return list(ALIGNMENTS)

    @Property(list, constant=True)
    def classNames(self):
        return list(CLASS_NAMES)

    # ── Name / Alignment ─────────────────────────────────────────────
    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @Slot(str)
    def setName(self, value: str):
        if value == self._name:
            return
        self._name = value
        self.nameChanged.emit()

    @Property(str, notify=alignmentChanged)
    def alignment(self):
        return self._alignment

    @Slot(str)
    def setAlignment(self, value: str):
        if value not in ALIGNMENTS or value == self._alignment:
            return
        self._alignment = value
        self.alignmentChanged.emit()

    # ── Background ─────────────────────────────────────────────────
    def _bg_data(self) -> dict:
        return get_background(self._background) or {}

    @Property(str, notify=backgroundChanged)
    def selectedBackground(self):
        return self._background

    @Slot(str)
    def selectBackground(self, name: str):
        if name == self._background:
            return
        self._background = name
        self._background_feat = ""
        self.backgroundChanged.emit()

    @Property(str, notify=backgroundChanged)
    def backgroundSkillsText(self):
        bg = self._bg_data()
        if not bg:
            return ""
        parts = []
        skills = bg.get("skills") or []
        tools = bg.get("tools") or []
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")
        if tools:
            parts.append(f"Tools: {', '.join(tools)}")
        return "  ·  ".join(parts)

    @Property(str, notify=backgroundChanged)
    def backgroundDetailText(self):
        bg = self._bg_data()
        if not bg:
            return ""
        feat = bg.get("feature", "")
        feat_desc = bg.get("feature_desc", "")
        feat_choices = bg.get("feat_choices") or []
        languages = bg.get("languages", 0)
        origin_feat = bg.get("origin_feat")
        equipment = bg.get("equipment", "")
        notes = bg.get("notes", "")
        source = bg.get("source", "")
        parts = []
        if feat:
            parts.append(f"◆ Feature: {feat}\n{feat_desc}" if feat_desc else f"◆ Feature: {feat}")
        if origin_feat:
            parts.append(f"◆ Origin Feat: {origin_feat}")
        if feat_choices:
            parts.append(f"◆ Feat (choose one): {', '.join(feat_choices)}")
        if languages:
            word = "language" if languages == 1 else "languages"
            parts.append(f"◆ Languages: {languages} {word} of your choice")
        if equipment:
            parts.append(f"◆ Equipment: {equipment}")
        if notes:
            parts.append(f"◆ Notes: {notes}")
        if source:
            parts.append(f"Source: {source}")
        return "\n\n".join(parts)

    @Property(list, notify=backgroundChanged)
    def backgroundFeatChoices(self):
        return list(self._bg_data().get("feat_choices") or [])

    @Property(bool, notify=backgroundChanged)
    def showBackgroundFeatPicker(self):
        return bool(self.backgroundFeatChoices)

    @Property(str, notify=backgroundChanged)
    def selectedBackgroundFeat(self):
        return self._background_feat

    @Slot(str)
    def selectBackgroundFeat(self, feat: str):
        if feat == self._background_feat:
            return
        self._background_feat = feat
        self.backgroundChanged.emit()

    # ── Starting Class ─────────────────────────────────────────────
    @Property(str, notify=classChanged)
    def selectedClass(self):
        return self._class_name

    @Slot(str)
    def selectClass(self, name: str):
        if name == self._class_name:
            return
        self._class_name = name
        self.classChanged.emit()

    @Property(str, notify=classChanged)
    def classInfoText(self):
        if not self._class_name:
            return ""
        cdata = CLASS_DICT.get(self._class_name, {})
        hd = cdata.get("hit_die", 8)
        saves = ", ".join(cdata.get("save_profs", []))
        return f"Hit Die: d{hd}  ·  Saving Throws: {saves}"

    # ── Errors / confirmation state ───────────────────────────────
    @Property(str, notify=errorChanged)
    def errorMessage(self):
        return self._error

    def _set_error(self, msg: str):
        self._error = msg
        self.errorChanged.emit()

    @Property(bool, notify=classConfirmed)
    def classConfirmedOnce(self):
        return self._confirmed_once

    # ── Commit into the character dict (mirrors Step3Class.collect()) ──
    @Slot(result=bool)
    def confirmClass(self) -> bool:
        name = self._name.strip()
        if not name:
            self._set_error("Please enter a character name.")
            return False
        if not self._background:
            self._set_error("Please choose a background.")
            return False
        if not self._class_name:
            self._set_error("Please choose a starting class.")
            return False

        char = self.char
        char["name"] = name
        char["alignment"] = self._alignment
        char["edition"] = "2014"
        char["background"] = self._background

        feat_choices = self._bg_data().get("feat_choices") or []
        if feat_choices:
            if not self._background_feat:
                self._set_error(
                    f"{self._background} grants a feat -- please choose one of: "
                    + ", ".join(feat_choices))
                return False
            if self._background_feat not in feat_choices:
                self._set_error(f"Choose one of: {', '.join(feat_choices)}")
                return False
            char.setdefault("_choices", {})["background_feat"] = self._background_feat
        elif isinstance(char.get("_choices"), dict):
            char["_choices"].pop("background_feat", None)

        cdata = CLASS_DICT.get(self._class_name, {})
        hd = cdata.get("hit_die", 8)
        char.setdefault("classes", [])
        if not char["classes"] or char["classes"][0]["class"] != self._class_name:
            char["classes"] = [{"class": self._class_name, "level": 1, "subclass": "", "hit_die": hd}]

        self._set_error("")
        # Same as every other wizard step -- re-derive ability_bonuses/
        # proficiencies/hit-die-driven max HP/etc. now that background
        # and class are finalized.
        rebuild(char)
        self._confirmed_once = True
        self.classConfirmed.emit()
        return True
