# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for D&D 5e Character Creator
# Windows-compatible: strip disabled (Unix only), no UPX, safe excludes only

import os, sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

# PyInstaller os.chdir()s to the spec file's own directory (SPECPATH,
# injected automatically into this file's execution namespace) before
# running it, so every relative path below resolves against THAT
# directory, not the CWD the `pyinstaller`/build script was invoked from.
# This spec lives in packaging/, one level below the repo root where
# run_dnd_creator.py, dnd_app/, and README.md actually are -- _ROOT makes
# every path explicit and location-independent instead of relying on
# an assumption about CWD that doesn't hold once PyInstaller chdirs.
_ROOT = os.path.dirname(SPECPATH)
# collect_submodules('dnd_app') below needs dnd_app importable -- don't
# rely on however sys.path happened to be set when `pyinstaller`/the
# build script was launched (it worked by incidental luck the one time
# this was tested: `python -m PyInstaller` snapshots sys.path[0] as the
# launch CWD before PyInstaller's own chdir to SPECPATH ever runs, and
# the launch CWD only happened to be the repo root because the build
# script cd's there first). Make it explicit instead.
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')

# ── Strip unused PySide6 payload BEFORE it's bundled ─────────────────────────
# collect_all() walks PySide6's entire install directory and grabs every file
# it finds — it does NOT consult the `excludes` list passed to Analysis()
# below, which only prevents Python-level module imports from being traced.
# That mismatch is why excluding e.g. 'PySide6.QtWebEngineCore' as a module
# had zero effect on bundle size: its 194 MB shared library (libQt6WebEngine
# Core.so, or Qt6WebEngineCore.dll on Windows) was still being collected as a
# raw data/binary file regardless. This app is plain QtWidgets — no embedded
# browser, no QML/Quick, no bundled dev tools — so everything below is dead
# weight that does nothing but slow down onefile's per-launch self-extraction.
_DEAD_WEIGHT_MARKERS = [
    # Chromium-based embedded browser engine (~200 MB) — never used, this
    # app has no WebEngine/WebEngineWidgets/WebEngineQuick usage anywhere.
    'webengine', 'webview',
    # Declarative UI stack (QML/Quick/Quick3D and their shader/controls
    # support) — this app is 100% QtWidgets, never imports QtQml/QtQuick.
    'qml', 'quick', 'qtquick', 'q3d', '3drender', '3dcore', '3danimation',
    '3dextras', '3dinput', '3dlogic', 'shadertools',
    # Data-viz/graphing/multimedia/charting modules this app doesn't use.
    'qtcharts', 'qtgraphs', 'qtdatavis', 'multimedia', 'qtpdf',
    'qtconcurrent', 'qtstatemachine', 'qtscxml', 'qtspatialaudio',
    'qttexttospeech', 'qtasyncio', 'qtaxcontainer', 'qtcanvaspainter',
    'qthttpserver', 'qtnetworkauth',
    # Qt's own developer tools bundled alongside the libraries — Designer,
    # Linguist (+lupdate/lrelease), Assistant. These are standalone GUI
    # apps for Qt developers; nothing at runtime calls into them.
    os.sep + 'designer', os.sep + 'linguist', os.sep + 'lupdate',
    os.sep + 'lrelease', os.sep + 'assistant', os.sep + 'balsamui',
    # Type stubs (.pyi), C++ headers, and Shiboken typesystem XML — all
    # purely for IDE autocomplete / compiling C++ Qt code, never read by
    # a running Python program.
    '.pyi', os.sep + 'include' + os.sep, os.sep + 'typesystems' + os.sep,
    # Qt's own translation catalogs for ITS OWN dialogs (file pickers,
    # message boxes, etc.) in ~30 languages. This app's UI text is all
    # hardcoded English regardless, so there's nothing for these to
    # translate — safe to drop entirely.
    os.sep + 'translations' + os.sep,
    # Plugin binaries for modules already excluded above via QT_EXCLUDES —
    # same collect_all()-bypasses-module-excludes mismatch that motivated
    # this whole marker list in the first place (see the file's top
    # comment), just more instances of it: QtSql/QtPrintSupport/
    # QtPositioning/QtSensors/QtSerialBus/QtNetwork's plugin .dll/.so files
    # get walked and bundled by collect_all() regardless of the module
    # itself being excluded from hiddenimports. Directory-scoped (with
    # path separators) since these are short, generic-sounding names that
    # could otherwise false-match an unrelated file.
    os.sep + 'sqldrivers' + os.sep, os.sep + 'printsupport' + os.sep,
    os.sep + 'position' + os.sep, os.sep + 'sensors' + os.sep,
    os.sep + 'sensorgestures' + os.sep, os.sep + 'canbus' + os.sep,
    os.sep + 'tls' + os.sep, os.sep + 'networkinformation' + os.sep,
    os.sep + 'geoservices' + os.sep, os.sep + 'geometryloaders' + os.sep,
    # SVG support (QtSvg/QtSvgWidgets, also excluded above): this app's
    # icons are .ico/.png/.gif only, with zero .svg/QSvg usage anywhere,
    # so the SVG icon-engine and image-format plugins (iconengines/
    # qsvgicon.*, imageformats/qsvg.*) are dead weight too. os.sep-prefixed
    # so it only matches a path component, not e.g. a data file that
    # happens to contain "qsvg" mid-string.
    os.sep + 'qsvg',
]

def _is_dead_weight(path: str) -> bool:
    low = path.lower()
    return any(marker in low for marker in _DEAD_WEIGHT_MARKERS)

_before_datas, _before_bins, _before_hidden = len(pyside6_datas), len(pyside6_binaries), len(pyside6_hiddenimports)
pyside6_datas = [(s, d) for s, d in pyside6_datas if not _is_dead_weight(s)]
pyside6_binaries = [(s, d) for s, d in pyside6_binaries if not _is_dead_weight(s)]
# hiddenimports is just a list of dotted module name STRINGS (no file path
# to check), but the same lowercased-substring markers still match module
# names fine (e.g. 'qtdatavis' is a substring of 'pyside6.qtdatavisualization').
# This part was missing before — filtering only pyside6_datas/binaries but
# NOT pyside6_hiddenimports meant PyInstaller's own Analysis step would
# re-discover and re-bundle these modules anyway, since hiddenimports
# explicitly tells it "make sure this module and its dependencies are
# included," independent of what was already filtered out of the raw
# collected file lists above.
pyside6_hiddenimports = [m for m in pyside6_hiddenimports if not _is_dead_weight(m)]
print(f"[spec] Trimmed PySide6 payload: datas {_before_datas} -> {len(pyside6_datas)}, "
      f"binaries {_before_bins} -> {len(pyside6_binaries)}, "
      f"hiddenimports {_before_hidden} -> {len(pyside6_hiddenimports)}")

# ── Windows runtime DLLs ─────────────────────────────────────────────────────
extra_binaries = []
if sys.platform == 'win32':
    py_ver = f'{sys.version_info.major}{sys.version_info.minor}'
    for candidate in [
        os.path.join(os.path.dirname(sys.executable), f'python{py_ver}.dll'),
        os.path.join(os.path.dirname(sys.executable), f'python{py_ver[0]}.dll'),
    ]:
        if os.path.exists(candidate):
            extra_binaries.append((candidate, '.'))
            break
    for dll in ['VCRUNTIME140.dll', 'VCRUNTIME140_1.dll', 'MSVCP140.dll']:
        for d in [
            os.path.dirname(sys.executable),
            os.path.join(os.path.dirname(sys.executable), 'DLLs'),
            r'C:\Windows\System32',
        ]:
            p = os.path.join(d, dll)
            if os.path.exists(p):
                extra_binaries.append((p, '.'))
                break

# ── Safe Qt module exclusions (unused by this app) ───────────────────────────
# IMPORTANT: do NOT exclude ast, dis, tokenize, parser — PyInstaller needs them
# during its own analysis phase and they may be pulled in by PySide6 internals.
QT_EXCLUDES = [
    'PySide6.QtBluetooth',
    'PySide6.QtDBus',          # Linux-only anyway
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtLocation',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtNfc',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'PySide6.QtPositioning',
    'PySide6.QtPrintSupport',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickWidgets',
    'PySide6.QtQuick3D',
    'PySide6.QtQuickControls2',
    'PySide6.QtQuickTest',
    'PySide6.QtRemoteObjects',
    'PySide6.QtSensors',
    'PySide6.QtSerialBus',
    'PySide6.QtSerialPort',
    'PySide6.QtSql',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'PySide6.QtTest',
    'PySide6.QtUiTools',
    'PySide6.QtWebChannel',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineQuick',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebView',
    'PySide6.QtWebSockets',
    'PySide6.QtXml',
    # Module-level excludes alone aren't enough to keep these out of the
    # final binary -- see the _DEAD_WEIGHT_MARKERS filter above, which
    # covers the same set of modules at the file level.
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DRender',
    'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic',
    'PySide6.QtAsyncio',
    'PySide6.QtAxContainer',
    'PySide6.QtCanvasPainter',
    'PySide6.QtCharts',
    'PySide6.QtConcurrent',
    'PySide6.QtDataVisualization',
    'PySide6.QtGraphs',
    'PySide6.QtGraphsWidgets',
    'PySide6.QtHttpServer',
    'PySide6.QtNetworkAuth',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    'PySide6.QtScxml',
    'PySide6.QtSpatialAudio',
    'PySide6.QtStateMachine',
    'PySide6.QtTextToSpeech',
]

# Safe stdlib exclusions — these are genuinely unused and safe to drop
STDLIB_EXCLUDES = [
    'unittest',
    'doctest',
    'pdb',
    'profile',
    'pstats',
    'timeit',
    'cProfile',
    'lib2to3',
    'distutils',
    'setuptools',
    'pkg_resources',
    'email',
    'html',
    'http',
    # NOTE: do not add 'urllib' to this list. PyInstaller's own runtime
    # hooks (pyi_rth_inspect -> zipfile._path -> pathlib) import it
    # transitively, so excluding it makes EVERY build fail at startup with
    # "ModuleNotFoundError: No module named 'urllib'" before the app's own
    # code ever runs.
    'xmlrpc',
    'curses',
    'readline',
    'rlcompleter',
    'tkinter',
    'turtle',
    'turtledemo',
    'idlelib',
    'ensurepip',
    'venv',
    # Heavy scientific libs (won't be installed, but explicit helps analysis)
    'numpy',
    'pandas',
    'matplotlib',
    'scipy',
    'sklearn',
    'PIL',
]

EXCLUDES = QT_EXCLUDES + STDLIB_EXCLUDES

_README = os.path.join(_ROOT, 'README.md')
_SPLASH_GIF = os.path.join(_ROOT, 'dnd_app', 'ui', 'splash', 'splash.gif')
_SPLASH_PNG = os.path.join(_ROOT, 'dnd_app', 'ui', 'splash', 'splash.png')

a = Analysis(
    [os.path.join(_ROOT, 'run_dnd_creator.py')],
    pathex=[_ROOT],
    binaries=pyside6_binaries + extra_binaries,
    datas=[
        (os.path.join(_ROOT, 'dnd_app', 'data'), 'dnd_app/data'),
        (os.path.join(_ROOT, 'dnd_app', 'ui', 'icon.ico'), 'dnd_app/ui'),
        *([(_README, '.')] if os.path.isfile(_README) else []),
        # splash.gif/splash.png live in dnd_app/ui/splash alongside the code
        # that reads them. Analysis only auto-bundles .py files it traces
        # through imports, so these binary assets need explicit datas
        # entries same as the old dnd_app/assets dir they moved out of.
        *([(_SPLASH_GIF, 'dnd_app/ui/splash')] if os.path.isfile(_SPLASH_GIF) else []),
        *([(_SPLASH_PNG, 'dnd_app/ui/splash')] if os.path.isfile(_SPLASH_PNG) else []),
        *pyside6_datas,
    ],
    hiddenimports=[
        *pyside6_hiddenimports,
        *collect_submodules('dnd_app'),
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # Ensure these stdlib modules are always included even if analysis
        # doesn't find them via import tracing:
        'ast', 'tokenize', 'dis',
        # pypdf is only ever imported lazily, inside export_official_pdf()
        # in core/pdf_export.py -- a known PyInstaller blind spot (static
        # analysis traces top-level imports far more reliably than ones
        # buried in a function body), so it needs to be declared
        # explicitly or "Export Character" -> "Official character sheet
        # (PDF)" fails with ModuleNotFoundError in the built exe even
        # though `pip install -r packaging/requirements.txt` has it installed.
        *collect_submodules('pypdf'),
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure)

# ── Bootloader-level splash screen (onefile only) ────────────────────────────
# This is PyInstaller's own native splash feature, separate from and in
# addition to the app's own in-process AnimatedSplash (dnd_app/ui/splash/).
# It runs in the PARENT process and can appear WHILE the onefile bootloader
# is still self-extracting the bundle — i.e. during the exact multi-second
# gap that otherwise looks like a frozen/dead window on cold start, since
# nothing the app itself does can run until extraction finishes. Requires a
# static image (no GIF support at this layer); splash.png here is just the
# first frame of dnd_app/ui/splash/splash.gif so the two splashes look
# continuous.
_splash_target = []
_splash_binaries = []
if os.path.isfile(_SPLASH_PNG):
    splash = Splash(
        _SPLASH_PNG,
        binaries=a.binaries,
        datas=a.datas,
        text_pos=None,          # no bootloader-drawn progress text
        always_on_top=True,
    )
    _splash_target = [splash]
    _splash_binaries = [splash.binaries]
else:
    print(f"[spec] {_SPLASH_PNG} not found — building without the bootloader splash screen")

exe = EXE(
    pyz,
    a.scripts,
    *_splash_target,
    *_splash_binaries,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='MIMIC',
    debug=False,
    # strip=True is a Unix/Mac-only option. On Windows it's silently ignored
    # by older PyInstaller but causes errors in some versions — leave False.
    strip=False,
    # UPX deliberately not used: compression adds CPU decompression overhead
    # to every single onefile launch (on top of the self-extraction that's
    # already the main startup-time cost), and UPX-compressed EXEs are a
    # common trigger for antivirus false positives — neither trade-off is
    # worth ~25% smaller disk size for this app.
    upx=False,
    console=False,
    icon=os.path.join(_ROOT, 'dnd_app', 'ui', 'icon.ico'),
)
