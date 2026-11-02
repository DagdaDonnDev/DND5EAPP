"""A note of what went wrong, for fixing it -- the same on both apps.

install(folder) starts mimic_error_log.txt in that folder: every error the
app didn't handle is added with where it happened (the app carries on as
before), and if the app itself goes down, Python's own record of where it
was (faulthandler). A log grown past 1 MB starts again. Returns the file's
path, or "" when the folder can't be written to.
"""
import datetime
import faulthandler
import os
import sys
import traceback

LOG_NAME = "mimic_error_log.txt"
_MAX_BYTES = 1_000_000
_file = None


def install(folder: str) -> str:
    global _file
    if _file is not None:
        return _file.name
    path = os.path.join(folder, LOG_NAME)
    try:
        os.makedirs(folder, exist_ok=True)
        big = os.path.exists(path) and os.path.getsize(path) > _MAX_BYTES
        _file = open(path, "w" if big else "a", encoding="utf-8")
    except OSError:
        return ""
    _file.write(f"\n=== MIMIC started {datetime.datetime.now().isoformat(timespec='seconds')} ===\n")
    _file.flush()
    faulthandler.enable(file=_file, all_threads=True)
    previous = sys.excepthook

    def _hook(kind, value, tb):
        try:
            _file.write(f"\n[{datetime.datetime.now().isoformat(timespec='seconds')}] "
                        + "".join(traceback.format_exception(kind, value, tb)))
            _file.flush()
        except Exception:
            pass
        previous(kind, value, tb)

    sys.excepthook = _hook
    return path
