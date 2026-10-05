"""Save/Load screen bridge. Reuses dnd_app.core.save_load's JSON
format and validation wholesale -- a character saved on desktop opens
fine on Android and vice versa, since it's the same file format. That
sharing is deliberate and stays that way: core/save_load.py and
core/pdf_export.py hold the one serialization/PDF-export
implementation for both platforms, so the JSON schema and the PDF
output can never drift apart between them. What's platform-specific
(this file, vs. ui_desktop's save/export dialogs) is only the
"where do the bytes come from/go" plumbing -- default folder
resolution, native file pickers, content:// URI handling -- which is
exactly the split already in place, not something to unify further.

Where this differs from the desktop app: desktop always saves under
SAVE_DIR (~/.dnd_characters), a fixed path that makes sense for a
single-user desktop install. Android has no equivalent stable home
directory, and more importantly no runtime "storage permission" to
request for it -- Qt's cross-platform permission types cover
Bluetooth/Camera/Microphone/Location/Contacts/Calendar, but there is no
generic file-storage permission, because modern Android's scoped
storage model doesn't require one for an app writing to its own
Documents-equivalent directory (QStandardPaths.DocumentsLocation). That
directory is sandboxed to this app -- not the same shared folder the
system Files app shows for "Documents" -- but it needs no permission
dialog and is the correct, working answer for "save to a Documents
folder" today. Making saves visible/pickable from the shared system
Documents folder (so e.g. a file manager or another app can see them
directly) is a real, separate feature: it needs the Storage Access
Framework, which requires Java/JNI code Qt doesn't wrap directly --
out of scope here, flagged the same way in packaging/android/README.md.

Loading FROM elsewhere (e.g. a file the player downloaded into their
phone's Downloads folder) goes through loadCharacterFromUrl() below,
fed by a QML native file picker (Qt.labs.platform.FileDialog), which
uses Android's Storage Access Framework itself for the picker UI even
though writing through SAF isn't implemented here. A file picked that
way can come back as either a plain filesystem path or a "content://"
URI depending on Android version/provider -- content:// URIs aren't
real paths Python's open() can read, so that branch goes through Qt's
own QFile (which has a content:// resolver on Android) instead. THIS
BRANCH IS UNTESTED -- there's no real Android device in this sandbox,
only the offscreen/desktop QPA platform, where every picked file is a
plain local path and that branch never runs.
"""
import json
import os

from PySide6.QtCore import QObject, QFile, QIODevice, QStandardPaths, QUrl, Signal, Slot, Property

from dnd_app.core.character import new_character
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters,
    delete_character, validate_character, migrate_character,
    export_character_text, list_character_folders, set_character_folder, character_json,
    rename_character_folder, delete_character_folder,
)
from dnd_app.core.pdf_export import export_official_pdf, TEMPLATE_PATH

_SUBDIR = "MIMIC Characters"


def _documents_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    if not base:
        # No platform Documents location resolved at all (seen on some
        # minimal/headless environments) -- fall back to a directory
        # next to wherever HOME resolves, same as desktop's SAVE_DIR
        # pattern, rather than crashing on save.
        base = os.path.expanduser("~")
    path = os.path.join(base, _SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    name = (name or "Unnamed").strip().replace(" ", "_")
    return "".join(c for c in name if c.isalnum() or c in "_-") or "Unnamed"


class SaveLoadBridge(QObject):
    savedListChanged = Signal()
    errorChanged = Signal()
    characterSaved = Signal()
    characterLoaded = Signal()
    toastRequested = Signal(str)

    def __init__(self, char: dict, parent=None):
        super().__init__(parent)
        self.char = char
        self._error = ""
        self._last_saved_path = ""
        self._clean_snapshot = self._serialize()

    def _serialize(self) -> str:
        # A full JSON snapshot rather than a per-field "dirty" flag
        # threaded through every mutating slot across every bridge
        # (there are dozens, across race/ability/class/equipment
        # wizards and the sheet itself) -- comparing this against a
        # fresh snapshot at "has anything changed since the last
        # load/save" time is the one place that needs to know, and it
        # can't miss a mutation the way a manually-set flag could.
        return json.dumps(self.char, sort_keys=True, default=str)

    @Slot(result=bool)
    def hasUnsavedChanges(self) -> bool:
        return self._serialize() != self._clean_snapshot

    @Property(str, constant=True)
    def documentsDir(self):
        return _documents_dir()

    @Property(str, constant=True)
    def downloadsDir(self):
        base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        return base or os.path.expanduser("~")

    @Property(str, notify=errorChanged)
    def errorMessage(self):
        return self._error

    def _set_error(self, msg: str):
        self._error = msg
        self.errorChanged.emit()

    @Property(str, notify=characterSaved)
    def lastSavedPath(self):
        return self._last_saved_path

    # ── Saved character list ──────────────────────────────────────────
    @Property(list, notify=savedListChanged)
    def savedCharacters(self):
        """List of {name, classesText, modified, filepath, folder} dicts,
        newest first (list_saved_characters() already sorts that way)."""
        out = []
        for entry in list_saved_characters(directory=_documents_dir()):
            classes_text = ", ".join(
                f"{c.get('class','?')} {c.get('level','?')}" for c in entry.get("classes", [])
            )
            out.append({
                "name": entry.get("name", "Unnamed"),
                "classesText": classes_text,
                "modified": entry.get("modified", ""),
                "filepath": entry.get("filepath", ""),
                "folder": entry.get("folder", "") or "",
            })
        return out

    @Property(list, notify=savedListChanged)
    def savedCharacterFolders(self):
        """savedCharacters grouped into
        [{folder, characters: [...]}, ...] sections -- named folders
        sorted alphabetically first, then an "Uncategorized" section
        (folder: "") last for characters with no folder assigned.
        Matches desktop's StartMenu grouping exactly."""
        groups: dict[str, list] = {}
        for entry in self.savedCharacters:
            groups.setdefault(entry["folder"], []).append(entry)
        named = sorted(f for f in groups if f)
        ordered = named + ([""] if "" in groups else [])
        return [{"folder": f, "characters": groups[f]} for f in ordered]

    @Property(list, notify=savedListChanged)
    def folderNames(self):
        """Existing non-empty folder/campaign names, for the "Move to
        folder" picker's list of choices (plus letting the player type
        a brand-new one)."""
        return list_character_folders(directory=_documents_dir())

    @Slot(str, str)
    def moveCharacterToFolder(self, filepath: str, folder: str):
        set_character_folder(filepath, folder)
        self.savedListChanged.emit()

    @Slot(str, str, result=int)
    def renameFolder(self, old_name: str, new_name: str) -> int:
        """Re-tags every character in `old_name` to `new_name` -- returns
        how many were moved, for a confirmation toast."""
        moved = rename_character_folder(_documents_dir(), old_name, new_name)
        self.savedListChanged.emit()
        return moved

    @Slot(str, result=int)
    def deleteFolder(self, folder: str) -> int:
        """Permanently deletes every character currently filed under
        `folder` -- a real bulk delete, not just un-filing them to
        Uncategorized. The QML side is expected to have already
        confirmed this with the player (savedCharacterFolders already
        tells it how many characters are in play) before calling this.
        Returns how many were deleted."""
        deleted = delete_character_folder(_documents_dir(), folder)
        self.savedListChanged.emit()
        return deleted

    @Slot()
    def refresh(self):
        self.savedListChanged.emit()

    # ── Save ───────────────────────────────────────────────────────────
    @Slot(result=bool)
    def saveCharacter(self) -> bool:
        return self._save(quiet=False)

    @Slot(result=bool)
    def autoSave(self) -> bool:
        """Save without being asked: on character creation, level up/down
        and confirmed choices. A character that can't be saved yet (still
        missing something validation needs) is skipped silently rather
        than flashing an error the player didn't cause."""
        return self._save(quiet=True)

    def _save(self, quiet: bool) -> bool:
        ok, errors = validate_character(self.char)
        if not ok:
            if not quiet:
                self._set_error("Can't save yet: " + "; ".join(errors))
            return False
        directory = _documents_dir()
        # Overwrite the exact file this character was loaded from, as
        # long as it's one we manage (inside our own Documents folder) --
        # otherwise (a brand-new character, or one loaded from outside
        # our sandbox, e.g. Downloads or a content:// picker result)
        # fall back to a fresh name-derived path. Always recomputing the
        # path from the current name here used to silently create a
        # second file next to the original whenever "the existing
        # character" wasn't already saved under that exact name in this
        # folder -- exactly the case for any character loaded via
        # "Load from Downloads / Browse" instead of the in-app list.
        if self._last_saved_path and os.path.dirname(self._last_saved_path) == directory:
            filepath = self._last_saved_path
        else:
            filename = _safe_filename(self.char.get("name", "")) + ".json"
            filepath = os.path.join(directory, filename)
        try:
            self._last_saved_path = save_character(self.char, filepath=filepath)
        except OSError as e:
            self._set_error(f"Couldn't save: {e}")
            return False
        self._set_error("")
        self._clean_snapshot = self._serialize()
        self.characterSaved.emit()
        self.savedListChanged.emit()
        # Auto-saves stay silent: they follow a level-up/choice whose own
        # toast ("...go to Choices") shouldn't be replaced, and the Save
        # screen's "All changes saved" status already shows it happened.
        if not quiet:
            self.toastRequested.emit(f"Saved to {os.path.basename(filepath)}")
        return True

    # ── Load ───────────────────────────────────────────────────────────
    @Slot(str, result=bool)
    def loadCharacterFrom(self, filepath: str) -> bool:
        try:
            data = load_character(filepath)
        except (OSError, ValueError) as e:
            self._set_error(f"Couldn't load: {e}")
            return False
        self._apply_loaded(data, loaded_path=filepath)
        self.toastRequested.emit(f"Loaded {os.path.basename(filepath)}")
        return True

    @Slot(str, result=bool)
    def loadCharacterFromUrl(self, url: str) -> bool:
        """Same as loadCharacterFrom(), but takes a QML FileDialog's
        selectedFile (a "file://" or, on Android, sometimes a
        "content://" URI) instead of a plain path -- for loading a
        character from outside this app's own managed folder, e.g. the
        phone's Downloads folder."""
        qurl = QUrl(url)
        if qurl.isLocalFile():
            return self.loadCharacterFrom(qurl.toLocalFile())

        # content:// URI: Python's open() can't read this (it's not a
        # real filesystem path), but Qt's QFile has an Android content
        # resolver built in. Mirrors load_character()'s own body
        # (open -> json.load -> migrate_character) with QFile standing
        # in for the plain open().
        qfile = QFile(qurl.toString())
        if not qfile.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            self._set_error(f"Couldn't open: {qfile.errorString()}")
            return False
        try:
            raw = bytes(qfile.readAll()).decode("utf-8")
        finally:
            qfile.close()
        try:
            data = migrate_character(json.loads(raw))
        except (ValueError, TypeError) as e:
            self._set_error(f"Couldn't load: {e}")
            return False
        self._apply_loaded(data)
        self.toastRequested.emit("Character loaded")
        return True

    # ── Start Menu: begin a brand-new character ─────────────────────
    @Slot()
    def newCharacter(self):
        """Replaces the shared character dict with a fresh
        new_character() -- the Start Menu's "New Character" action.
        Same dict-mutation pattern as loading a file (_apply_loaded);
        every bridge's own non-char-dict state (e.g. AbilityWizardBridge's
        in-progress score entries) still needs its own reset, since this
        bridge only owns the shared dict, not the other screens' local
        UI state -- see AbilityWizardBridge.resetToDefaults(), called
        alongside this from App.qml's Start Menu handler."""
        self._apply_loaded(new_character())

    def _apply_loaded(self, data: dict, loaded_path: str = ""):
        # Every wizard bridge holds a reference to this SAME dict object
        # (see main.py) -- mutate it in place rather than rebinding, or
        # every other bridge would keep pointing at the old, stale one.
        self.char.clear()
        self.char.update(data)
        self._set_error("")
        # Reset (or set) which file counts as "the one this character
        # came from" for saveCharacter() to overwrite -- must happen on
        # every load/new-character, not just loadCharacterFrom(), or a
        # stale path from a PREVIOUSLY loaded character would still pass
        # saveCharacter()'s "inside our own folder" check and silently
        # overwrite that other character's file with this one's data.
        self._last_saved_path = loaded_path
        # A fresh "nothing's changed yet" baseline for hasUnsavedChanges()
        # -- otherwise a character freshly loaded (or a brand-new one)
        # would immediately compare as "dirty" against whatever the
        # PREVIOUS character's snapshot was.
        self._clean_snapshot = self._serialize()
        self.characterLoaded.emit()

    @Slot(str, result=bool)
    def deleteCharacterAt(self, filepath: str) -> bool:
        ok = delete_character(filepath)
        if ok:
            self.savedListChanged.emit()
        return ok

    # ── Character file export ─────────────────────────────────────────
    @Slot(str, result=bool)
    def exportJsonToUrl(self, url: str) -> bool:
        """Export: write a copy of the character file wherever the user
        picked in the system "save as" dialog (a "file://" path, or on
        Android usually a "content://" URI) -- for sharing it or opening
        it in the desktop app. Unlike saveCharacter() this doesn't touch
        the in-app character list or which file Save writes to."""
        ok, errors = validate_character(self.char)
        if not ok:
            self._set_error("Can't export yet: " + "; ".join(errors))
            return False
        data = character_json(self.char).encode("utf-8")
        qurl = QUrl(url)
        target = qurl.toLocalFile() if qurl.isLocalFile() else qurl.toString()
        qfile = QFile(target)
        if not qfile.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate):
            self._set_error(f"Couldn't export: {qfile.errorString()}")
            return False
        try:
            written = qfile.write(data)
        finally:
            qfile.close()
        if written != len(data):
            self._set_error("Couldn't export: the file was only partly written")
            return False
        self._set_error("")
        self.toastRequested.emit("Character file exported")
        return True

    @Property(str, notify=characterSaved)
    def exportFileName(self):
        return _safe_filename(self.char.get("name", "")) + ".json"

    # ── Plain-text export ──────────────────────────────────────────────
    @Slot(result=bool)
    def exportText(self) -> bool:
        """Human-readable summary (.txt) into the same folder as
        everything else -- desktop's ui_desktop/pages/sheet/base.py
        _export_text_dialog() equivalent, same core.save_load function."""
        name = (self.char.get("name") or "Unknown").strip() or "Unknown"
        filepath = os.path.join(_documents_dir(), f"{name} - Character Sheet.txt")
        try:
            text = export_character_text(self.char)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as e:
            self._set_error(f"Couldn't export text: {e}")
            return False
        self._set_error("")
        self.toastRequested.emit(f"Exported {os.path.basename(filepath)}")
        return True

    # ── PDF export ───────────────────────────────────────────────────
    @Slot(result=bool)
    def exportPdf(self) -> bool:
        """Fill the official WotC character sheet PDF and write it into
        the SAME folder saves go to (documentsDir), matching desktop's
        naming convention ("<name> - Character Sheet.pdf") so a saved
        JSON and its exported PDF sit next to each other."""
        if not os.path.exists(TEMPLATE_PATH):
            self._set_error(f"The character sheet template is missing: {TEMPLATE_PATH}")
            return False
        name = (self.char.get("name") or "Unknown").strip() or "Unknown"
        filepath = os.path.join(_documents_dir(), f"{name} - Character Sheet.pdf")
        try:
            export_official_pdf(self.char, filepath)
        except Exception as e:
            self._set_error(f"Couldn't export PDF: {e}")
            return False
        self._set_error("")
        self.toastRequested.emit(f"Exported {os.path.basename(filepath)}")
        return True
