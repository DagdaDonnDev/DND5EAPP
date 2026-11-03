"""Save/Load screen bridge. Reuses dnd_app.core.save_load's JSON
format and validation wholesale -- a character saved on desktop opens
fine on Android and vice versa, since it's the same file format. That
sharing is deliberate and stays that way: core/save_load.py and
core/pdf_sheet.py hold the one serialization/PDF-export
implementation for both platforms, so the JSON schema and the PDF
output can never drift apart between them. What's platform-specific
(this file, vs. ui_desktop's save/export dialogs) is only the
"where do the bytes come from/go" plumbing -- default folder
resolution, native file pickers, content:// URI handling -- which is
exactly the split already in place, not something to unify further.

Where characters live: both apps save to a "MIMIC Characters" folder in
the shared Documents folder by default (core.save_load.get_save_dir), or
a folder picked in Settings. On Android that's shared storage
(/storage/emulated/0/Documents/...), which the Files app can browse and
the app can write without a permission on Android 11+; older versions
fall back to the app's private Documents folder, where saves used to
live -- those are copied across once on first launch. Exports go into a
folder per character beside the saves. A folder picked in Settings has
to be one Android lets apps write to (Documents or Download).

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
import urllib.parse

from PySide6.QtCore import QObject, QFile, QIODevice, QStandardPaths, QUrl, Signal, Slot, Property
from PySide6.QtGui import QDesktopServices

from dnd_app.core.character import new_character
from dnd_app.core.save_load import (
    save_character, load_character, list_saved_characters,
    delete_character, validate_character, migrate_character,
    export_character_text, list_character_folders, set_character_folder, character_json,
    rename_character_folder, delete_character_folder,
    SAVES_SUBDIR, get_save_dir, set_default_save_dir, is_writable_dir,
    character_folder_name, character_export_dir, copy_saved_characters, migrate_saves_once,
    name_in_use, unique_character_name, NAME_IN_USE_MESSAGE,
)
from dnd_app.core.app_settings import set_custom_save_dir, get_custom_save_dir
from dnd_app.core.pdf_sheet import export_official_pdf, TEMPLATE_PATH

_SUBDIR = SAVES_SUBDIR


def _on_android() -> bool:
    # python-for-android sets these for the app process
    return "ANDROID_PRIVATE" in os.environ or "ANDROID_ARGUMENT" in os.environ


def _android_storage_root() -> str:
    return os.environ.get("EXTERNAL_STORAGE") or "/storage/emulated/0"


def _private_documents_dir() -> str:
    """Qt's Documents location + MIMIC Characters: on Android the app's
    own private folder (Android/data/...), where saves used to live."""
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    if not base:
        base = os.path.expanduser("~")
    return os.path.join(base, _SUBDIR)


def _platform_default_save_dir() -> str:
    """Android: the shared Documents/MIMIC Characters folder, which the
    Files app (and the desktop, over USB) can reach -- the private one
    can't be browsed on Android 11+. Falls back to the private folder
    when shared storage can't be written (older Android versions without
    storage permission). Elsewhere, Qt's Documents location."""
    if _on_android():
        shared = os.path.join(_android_storage_root(), "Documents", _SUBDIR)
        if is_writable_dir(shared):
            return shared
    return _private_documents_dir()


set_default_save_dir(_platform_default_save_dir())


def _documents_dir() -> str:
    """Where characters are saved: the folder picked in Settings, else the
    default above (see core.save_load.get_save_dir)."""
    return get_save_dir()


def _export_dir() -> str:
    """Exports live alongside the saves, in a folder per character."""
    return _documents_dir()


def _character_folder_name(char: dict) -> str:
    return character_folder_name(char)


def _character_export_dir(char: dict) -> str:
    return character_export_dir(char, _documents_dir())


def _path_from_folder_url(url: str) -> str:
    """A picked folder as a file system path. Android's folder picker
    returns a storage tree URI (content://com.android.externalstorage.
    documents/tree/primary%3ADocuments%2FCampaigns) -- primary storage maps
    to /storage/emulated/0/..., an SD card id to /storage/<id>/...."""
    qurl = QUrl(url)
    if qurl.isLocalFile():
        return qurl.toLocalFile()
    text = urllib.parse.unquote(url)
    marker = "com.android.externalstorage.documents/tree/"
    if marker in text:
        doc_id = text.split(marker, 1)[1].split("/document/")[0]
        volume, _, rel = doc_id.partition(":")
        root = _android_storage_root() if volume == "primary" else f"/storage/{volume}"
        return os.path.join(root, rel) if rel else root
    return ""


def _write_export(filepath: str, write) -> str:
    """Run write(path); if Android refuses because an older copy there
    belongs to a previous install of the app, write "name (2).ext"
    alongside it instead. Returns the path actually written."""
    try:
        write(filepath)
        return filepath
    except PermissionError:
        stem, ext = os.path.splitext(filepath)
        for n in range(2, 100):
            alt = f"{stem} ({n}){ext}"
            try:
                write(alt)
                return alt
            except PermissionError:
                continue
        raise


def _folder_url(path: str) -> QUrl:
    """A URL the system can open as a folder. On Android a file:// folder
    URL can't be handed to another app, so a folder in shared storage is
    addressed through the system's storage document provider instead,
    which the Files app opens."""
    root = _android_storage_root().rstrip("/")
    if _on_android() and (path + "/").startswith(root + "/"):
        rel = os.path.relpath(path, root)
        doc_id = urllib.parse.quote("primary:" + rel, safe="")
        return QUrl.fromEncoded(
            f"content://com.android.externalstorage.documents/document/{doc_id}".encode())
    return QUrl.fromLocalFile(path)


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
        self._renamed_on_load = ""
        self._clean_snapshot = self._serialize()
        # Saves used to live in the app's private folder -- copied into the
        # shared one once (originals left where they were).
        migrate_saves_once(_private_documents_dir(), "migrated_android_private_saves")

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

    @Property(str, notify=savedListChanged)
    def documentsDir(self):
        return _documents_dir()

    # ── Where characters are saved (Settings) ───────────────────────────
    @Property(bool, notify=savedListChanged)
    def saveDirIsDefault(self):
        return not get_custom_save_dir()

    def _switch_save_dir(self, new_dir: str) -> bool:
        """Use new_dir ("" = the default), copying the characters saved in
        the current folder across (originals stay where they were)."""
        from dnd_app.core.save_load import default_save_dir
        old_dir = _documents_dir()
        target = new_dir or default_save_dir()
        if not is_writable_dir(target):
            self.toastRequested.emit(
                "MIMIC can't save there -- pick a folder inside Documents or Download")
            return False
        copied = copy_saved_characters(old_dir, target)
        set_custom_save_dir(new_dir)
        self.savedListChanged.emit()
        msg = "Characters are now saved in " + target
        if copied:
            msg += f" ({copied} copied across)"
        self.toastRequested.emit(msg)
        return True

    @Slot(str, result=bool)
    def setSaveDirFromUrl(self, url: str) -> bool:
        """A folder picked in Settings (a file:// URL, or on Android a
        storage tree URI)."""
        path = _path_from_folder_url(url)
        if not path:
            self.toastRequested.emit("That folder can't be used -- pick one inside Documents or Download")
            return False
        return self._switch_save_dir(path)

    @Slot(result=bool)
    def resetSaveDir(self) -> bool:
        return self._switch_save_dir("")

    @Slot(result=bool)
    def openSaveFolder(self) -> bool:
        path = _documents_dir()
        if QDesktopServices.openUrl(_folder_url(path)):
            return True
        self.toastRequested.emit(f"Couldn't open the folder -- characters are saved in {path}")
        return False

    def _has_character(self) -> bool:
        return bool(self.char.get("classes"))

    # Refreshed whenever Save & Export opens (refresh()), so a rename on
    # the sheet shows up here too.
    @Property(str, notify=savedListChanged)
    def exportDir(self):
        """This character's own export folder, or the folder holding every
        character's folder when none is open."""
        if self._has_character():
            return os.path.join(_export_dir(), _character_folder_name(self.char))
        return _export_dir()

    @Slot(result=bool)
    def openExportFolder(self) -> bool:
        """Open this character's export folder (or the parent folder when
        no character is open) in the system's file manager -- the Files
        app on Android."""
        path = _character_export_dir(self.char) if self._has_character() else _export_dir()
        if QDesktopServices.openUrl(_folder_url(path)):
            return True
        self.toastRequested.emit(f"Couldn't open the folder -- your exports are in {path}")
        return False

    # What a PDF sheet import does and can't do -- shown before the picker
    # (the same text as the desktop's, from core/pdf_sheet.py)
    @Property(str, constant=True)
    def pdfImportIntro(self):
        from dnd_app.core.pdf_sheet import PDF_IMPORT_INTRO
        return PDF_IMPORT_INTRO

    @Property(list, constant=True)
    def pdfImportLimits(self):
        from dnd_app.core.pdf_sheet import PDF_IMPORT_LIMITS
        return list(PDF_IMPORT_LIMITS)

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
            # A new file -- never on top of another character's
            if os.path.exists(filepath) or name_in_use(self.char.get("name", ""), directory=directory):
                if not quiet:
                    self._set_error(NAME_IN_USE_MESSAGE)
                    self.toastRequested.emit(NAME_IN_USE_MESSAGE)
                return False
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
        if filepath.lower().endswith(".pdf"):
            try:
                with open(filepath, "rb") as fh:
                    return self._import_pdf(fh.read())
            except OSError as e:
                self._set_error(f"Couldn't open: {e}")
                return False
        try:
            data = load_character(filepath)
        except (OSError, ValueError) as e:
            self._set_error(f"Couldn't load: {e}")
            return False
        self._apply_loaded(data, loaded_path=filepath)
        self.toastRequested.emit(self._renamed_on_load or f"Loaded {os.path.basename(filepath)}")
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
        if not qfile.open(QIODevice.OpenModeFlag.ReadOnly):
            self._set_error(f"Couldn't open: {qfile.errorString()}")
            return False
        try:
            data_bytes = bytes(qfile.readAll())
        finally:
            qfile.close()
        # a content:// link often has no file name to go by -- a PDF
        # announces itself in its first bytes
        if data_bytes.lstrip()[:5] == b"%PDF-":
            return self._import_pdf(data_bytes)
        try:
            raw = data_bytes.decode("utf-8-sig")
            data = migrate_character(json.loads(raw))
        except (ValueError, TypeError) as e:
            self._set_error(f"Couldn't load: {e}")
            return False
        self._apply_loaded(data)
        self.toastRequested.emit(self._renamed_on_load or "Character loaded")
        return True

    def _import_pdf(self, data: bytes) -> bool:
        """A filled-in official 5e character sheet PDF -> a new character
        (see core/pdf_sheet.py), saved straight away like a new one.
        Anything worth checking goes in a toast and on the character's
        "Imported from PDF" notes page."""
        import io
        from dnd_app.core.pdf_sheet import import_character_pdf, SheetImportError
        try:
            char, notes = import_character_pdf(io.BytesIO(data))
        except SheetImportError as e:
            self._set_error(str(e))
            self.toastRequested.emit(str(e))
            return False
        except Exception as e:
            self._set_error(f"Couldn't import that sheet: {e}")
            return False
        if not char.get("name"):
            char["name"] = "Imported Character"
        self._apply_loaded(char)
        self._save(quiet=True)
        msg = self._renamed_on_load or f"Imported {self.char['name']} from the character sheet"
        if notes:
            msg += f" -- {len(notes)} thing{'s' if len(notes) != 1 else ''} to check on the Notes page"
        self.toastRequested.emit(msg)
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
        # A character brought in from outside the save folder whose name
        # another saved character already uses gets a new one -- saving it
        # under the same name would replace that other character's file.
        self._renamed_on_load = ""
        name = (data.get("name") or "").strip()
        inside = bool(loaded_path) and (os.path.dirname(os.path.abspath(loaded_path))
                                        == os.path.abspath(_documents_dir()))
        if data.get("classes") and name and not inside and name_in_use(name):
            new_name = unique_character_name(name)
            self.char["name"] = new_name
            self._renamed_on_load = (f'A character called "{name}" is already saved, '
                                     f'so this one is now "{new_name}"')
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

    @Slot(result=bool)
    def exportJsonToFolder(self) -> bool:
        """Character file (.json) into this character's export folder,
        next to its PDF and text exports."""
        ok, errors = validate_character(self.char)
        if not ok:
            self._set_error("Can't export yet: " + "; ".join(errors))
            return False
        data = character_json(self.char)
        filepath = os.path.join(_character_export_dir(self.char), self.exportFileName)
        try:
            def _write(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(data)
            filepath = _write_export(filepath, _write)
        except OSError as e:
            self._set_error(f"Couldn't export: {e}")
            return False
        self._set_error("")
        self.toastRequested.emit(f"Exported {os.path.basename(filepath)}")
        return True

    @Property(str, notify=characterSaved)
    def exportFileName(self):
        return _safe_filename(self.char.get("name", "")) + ".json"

    # ── Plain-text export ──────────────────────────────────────────────
    @Slot(result=bool)
    def exportText(self) -> bool:
        """Human-readable summary (.txt) into this character's export
        folder (see _character_export_dir) -- desktop's ui_desktop/pages/
        sheet/base.py _export_text_dialog() equivalent, same core.save_load
        function."""
        name = _character_folder_name(self.char)   # file-system-safe
        filepath = os.path.join(_character_export_dir(self.char), f"{name} - Character Sheet.txt")
        try:
            text = export_character_text(self.char)

            def _write(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            filepath = _write_export(filepath, _write)
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
        this character's export folder (see _character_export_dir), with
        desktop's naming convention ("<name> - Character Sheet.pdf")."""
        if not os.path.exists(TEMPLATE_PATH):
            self._set_error(f"The character sheet template is missing: {TEMPLATE_PATH}")
            return False
        name = _character_folder_name(self.char)   # file-system-safe
        filepath = os.path.join(_character_export_dir(self.char), f"{name} - Character Sheet.pdf")
        try:
            filepath = _write_export(filepath, lambda path: export_official_pdf(self.char, path))
        except Exception as e:
            self._set_error(f"Couldn't export PDF: {e}")
            return False
        self._set_error("")
        self.toastRequested.emit(f"Exported {os.path.basename(filepath)}")
        return True
