"""
python-for-android hook:
1. before_apk_build:
   - ensure libc++_shared.so is present in the dist libs dirs
   - copy Qt runtime .so, Qt plugins, QML plugins, and PySide6/shiboken6
     top-level runtime libraries into libs/arm64-v8a/, flattened
2. before_apk_assemble: patch PythonActivity.java for Qt 6.11 compat
   - replace removed QtNative.setEnvironmentVariable with android.system.Os.setenv
   - strip any previously-inserted QtNative.startApplication reflection block
   - preload the Qt Quick dependency closure via System.loadLibrary in
     dependency order, so each library's JNI_OnLoad runs on the main thread
     with the JVM cache primed
"""
import os
import shutil
from fnmatch import fnmatch
import re
import subprocess
from pathlib import Path
from pythonforandroid.logger import info, warning


BUNDLE_PRUNE_PATTERNS = [
    "libav*.so",
    "libQt6Designer*.so",
    "libQt6Pdf*.so",
    "libQt6Charts*.so",
    "libQt6Graphs*.so",
    "libQt6DataVisualization*.so",
    "libQt6ShaderTools*.so",
    "libQt6Quick3D*.so",
    "libQt63D*.so",
    "libQt6Location*.so",
    "libQt6Positioning*.so",
    "libQt6Web*.so",
    "libQt6VirtualKeyboard*.so",
    "libQt6Multimedia*.so",
    "libQt6SpatialAudio*.so",
    "libQt6Test*.so",
    "libQt6Sql*.so",
    "libQt6Help*.so",
    "libQt6Nfc*.so",
    "libQt6Sensors*.so",
    "libQt6Serial*.so",
    "libQt6RemoteObjects*.so",
    "libQt6Scxml*.so",
    "libQt6StateMachine*.so",
    "libQt6TextToSpeech*.so",
    "libQt6UiTools*.so",
    "libQt6PrintSupport*.so",
    "libQt6Concurrent*.so",
    "libQt6DBus*.so",
    "libQt6QuickControls2Imagine*.so",
    "libQt6QuickControls2Universal*.so",
    "libQt6QuickControls2FluentWinUI3*.so",
    "libQt6QuickControls2iOS*.so",
    "libQt6QuickControls2MacOS*.so",
    "libQt6QuickControls2Windows*.so",
    "libqml_QtQuick_Controls_FluentWinUI3_*.so",
    "libqml_QtQuick_Controls_Imagine_*.so",
    "libqml_QtQuick_Controls_Universal_*.so",
    "libplugins_assetimporters_*.so",
]


def _patch_blacklist(bl_path: Path) -> None:
    """Append bundle prune patterns to blacklist.txt, deduped."""
    if not bl_path.exists():
        return
    try:
        lines = bl_path.read_text().splitlines()
    except Exception as e:
        warning(f"p4a_hook: could not read {bl_path}: {e}")
        return
    existing = set(lines)
    added = 0
    for pat in BUNDLE_PRUNE_PATTERNS:
        if pat not in existing:
            lines.append(pat)
            existing.add(pat)
            added += 1
    if added:
        bl_path.write_text("\n".join(lines) + "\n")
        info(f"p4a_hook: added {added} patterns to {bl_path}")


# Qt modules the app does not use. Add to this list as you confirm more
# are unused. Any library NOT on this list is kept unconditionally, so
# the default is safe: unknown libraries stay.
PRUNE_QT_PATTERNS = [
    # FFmpeg stubs
    "libav*.so",
    # Qt Designer
    "libQt6Designer*.so",
    # Qt PDF
    "libQt6Pdf*.so",
    # Charts, Graphs, DataVisualization
    "libQt6Charts*.so",
    "libQt6Graphs*.so",
    "libQt6DataVisualization*.so",
    # ShaderTools, 3D, 3D Render
    "libQt6ShaderTools*.so",
    "libQt6Quick3D*.so",
    "libQt63D*.so",
    # Location, Positioning
    "libQt6Location*.so",
    "libQt6Positioning*.so",
    # Web*
    "libQt6Web*.so",
    # VirtualKeyboard
    "libQt6VirtualKeyboard*.so",
    # Multimedia, SpatialAudio
    "libQt6Multimedia*.so",
    "libQt6SpatialAudio*.so",
    # Misc unused
    "libQt6Test*.so",
    "libQt6Sql*.so",
    "libQt6Help*.so",
    "libQt6Nfc*.so",
    "libQt6Sensors*.so",
    "libQt6Serial*.so",
    "libQt6RemoteObjects*.so",
    "libQt6Scxml*.so",
    "libQt6StateMachine*.so",
    "libQt6TextToSpeech*.so",
    "libQt6UiTools*.so",
    "libQt6PrintSupport*.so",
    "libQt6Concurrent*.so",
    "libQt6DBus*.so",
    # Qt Quick Controls styles we don't use (keep Material, Basic, Fusion)
    "libQt6QuickControls2Imagine*.so",
    "libQt6QuickControls2Universal*.so",
    "libQt6QuickControls2FluentWinUI3*.so",
    "libQt6QuickControls2iOS*.so",
    "libQt6QuickControls2MacOS*.so",
    "libQt6QuickControls2Windows*.so",
    # QML plugin for the FluentWinUI3 style
    "libqml_QtQuick_Controls_FluentWinUI3_*.so",
    "libqml_QtQuick_Controls_Imagine_*.so",
    "libqml_QtQuick_Controls_Universal_*.so",
    # Assimp (3D asset importer)
    "libplugins_assetimporters_*.so",
]


def is_pruned(name: str) -> bool:
    return any(fnmatch(name, pat) for pat in PRUNE_QT_PATTERNS)



HELPER_METHOD = '''    public void setEnvironmentVariable(String key, String value) {
        /** Sets an environment variable using the OS-level API. */
        try {
            android.system.Os.setenv(key, value, true);
            android.util.Log.v("PythonActivity", "setenv " + key + "=" + value);
        } catch (Exception e) {
            android.util.Log.e("Qt bootstrap", "Unable set environment variable:" + key + "=" + value);
            e.printStackTrace();
        }
    }

'''


STALE_REFLECTION_BLOCK = '''        android.util.Log.v("PythonActivity", "->> Returned from super.onCreate(), invoking QtNative.startApplication");
        try {
            java.lang.reflect.Method m = Class.forName("org.qtproject.qt.android.QtNative")
                .getDeclaredMethod("startApplication", String.class, String.class);
            m.setAccessible(true);
            m.invoke(null, "org.kivy.android.PythonActivity", "");
        } catch (Throwable t) {
            android.util.Log.e("PythonActivity", "Failed to call QtNative.startApplication: " + t);
            t.printStackTrace();
        }
        android.util.Log.v("PythonActivity", "->> QtNative.startApplication returned");
'''


# Tried removing this preload entirely (relying on QtLoader's own
# DT_NEEDED-driven load order) -- that regressed to an earlier failure
# point than the Qt6Core-only preload below reaches, so some amount of
# eager preloading is empirically load-bearing, not just insurance.
# Restored to Qt6Core-only.
#
# Qt6Core_arm64-v8a.so is the sole Qt library in this APK confirmed
# (via readelf -sW) to export a real JNI_OnLoad; QuickTemplates2 /
# QuickControls2 / QuickControls2Impl / etc. have none. With this
# preloaded, QtLoader's own subsequent native-side loadLibraries() call
# gets further (past the old QuickTemplates2 failure) before hitting a
# JNI_ERR on libQt6Quick_arm64-v8a.so itself instead -- still
# unresolved, under active investigation.
PRELOAD_QT_LIBS = '''        // Qt 6.11 preload: System.loadLibrary("Qt6Core_arm64-v8a") only.
        String[] qtPreloadLibs = {
            "Qt6Core_arm64-v8a",
        };
        for (String qtLib : qtPreloadLibs) {
            try {
                System.loadLibrary(qtLib);
                android.util.Log.v("PythonActivity", "->> preloaded " + qtLib);
            } catch (Throwable t) {
                android.util.Log.e("PythonActivity", "Failed to preload " + qtLib + ": " + t);
            }
        }

'''



# The block an earlier version of this hook injected -- swapped for the
# current one in a dist that was already patched with it.
OLD_DARK_SYSTEM_BARS_JAVA = '''        // Force dark system bars (status + navigation) to match the app's
        // dark Material theme. Without this, Qt 6.11's default Android
        // appearance applies APPEARANCE_LIGHT_NAVIGATION_BARS and the
        // navigation bar renders white on Android 15+.
        try {
            android.view.Window __w = getWindow();
            if (__w != null) {
                android.view.View __decor = __w.getDecorView();
                if (__decor != null) {
                    if (android.os.Build.VERSION.SDK_INT >= 30) {
                        android.view.WindowInsetsController __ctrl =
                            __decor.getWindowInsetsController();
                        if (__ctrl != null) {
                            __ctrl.setSystemBarsAppearance(
                                0,
                                android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                                    | android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
                            );
                        }
                    }
                    int __flags = __decor.getSystemUiVisibility();
                    __flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                    __flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
                    __decor.setSystemUiVisibility(__flags);
                }
                __w.setNavigationBarColor(android.graphics.Color.BLACK);
                __w.setStatusBarColor(android.graphics.Color.BLACK);
            }
            android.util.Log.v("PythonActivity", "->> dark system bars applied");
        } catch (Throwable __t) {
            android.util.Log.e("PythonActivity", "Failed to set dark system bars: " + __t);
        }
'''

DARK_SYSTEM_BARS_JAVA = '''        // Dark system bars (status + navigation) to match the app's dark
        // theme (Theme.qml's bg, #0d0f18). Three things, all needed:
        //  - clear the LIGHT_* appearance flags: Qt 6.11 sets
        //    APPEARANCE_LIGHT_NAVIGATION_BARS by default;
        //  - paint the window/decor background dark: on Android 15+ apps
        //    are edge-to-edge, so the navigation bar is transparent and
        //    shows the window background -- white by default -- rather
        //    than setNavigationBarColor();
        //  - re-apply after start-up: Qt resets the bar appearance when
        //    its own window comes up, after onCreate has run.
        try {
            final android.app.Activity __act = this;
            final Runnable __darkBars = new Runnable() {
                public void run() {
                    try {
                        android.view.Window __w = __act.getWindow();
                        if (__w == null) return;
                        int __bg = 0xFF0D0F18;
                        __w.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(__bg));
                        android.view.View __decor = __w.getDecorView();
                        if (__decor != null) {
                            __decor.setBackgroundColor(__bg);
                            if (android.os.Build.VERSION.SDK_INT >= 30) {
                                android.view.WindowInsetsController __ctrl =
                                    __decor.getWindowInsetsController();
                                if (__ctrl != null) {
                                    __ctrl.setSystemBarsAppearance(
                                        0,
                                        android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                                            | android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
                                    );
                                }
                            }
                            int __flags = __decor.getSystemUiVisibility();
                            __flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                            __flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
                            __decor.setSystemUiVisibility(__flags);
                        }
                        __w.setNavigationBarColor(__bg);
                        __w.setStatusBarColor(__bg);
                        if (android.os.Build.VERSION.SDK_INT >= 29) {
                            __w.setNavigationBarContrastEnforced(false);
                            __w.setStatusBarContrastEnforced(false);
                        }
                    } catch (Throwable __t) {
                        android.util.Log.e("PythonActivity", "Failed to set dark system bars: " + __t);
                    }
                }
            };
            __darkBars.run();
            android.view.View __d0 = getWindow().getDecorView();
            for (int __ms : new int[] {300, 1000, 2500, 5000}) {
                __d0.postDelayed(__darkBars, __ms);
            }
            android.util.Log.v("PythonActivity", "->> dark system bars applied (and re-applied after start-up)");
        } catch (Throwable __t) {
            android.util.Log.e("PythonActivity", "Failed to set dark system bars: " + __t);
        }
'''


# Resolves mainLib for QtNative.startApplication(). The absolute path
# only exists when Android extracts native libs (true today: minapi 21);
# with minSdk >= 23 bundletool stops extracting, so fall back to the
# soname -- dlopen() matches the already-loaded library by name.
MAIN_LIB_JAVA = (
    '            String __mainLib = getApplicationInfo().nativeLibraryDir + "/libmain_arm64-v8a.so";\n'
    '            if (!new java.io.File(__mainLib).exists()) __mainLib = "libmain_arm64-v8a.so";\n'
)


def _patch_java_file(path):
    p = Path(path)
    if not p.exists():
        return False
    src = p.read_text()
    orig = src

    # Remove any previously-injected preload block -- the old 19-library
    # version, or the later Qt6Core-only version -- if a prior run of
    # this hook injected one. Both variants re-enter Qt6Core's
    # JNI_OnLoad (see PRELOAD_QT_LIBS's comment above); QtLoader handles
    # the real load order correctly on its own, so we no longer inject
    # anything here, but a dist patched by an earlier hook version still
    # has the old block sitting in its PythonActivity.java and needs it
    # stripped back out.
    #
    # Requires two consecutive brace-only lines (the catch block's
    # close, then the for-loop's own close) so the match consumes the
    # whole for-loop rather than stopping at the first inner "}" --
    # stopping early leaves a dangling "}" that prematurely closes
    # onCreate() itself and breaks compilation. Both preload variants
    # share this same for+try/catch shape, so one regex handles either
    # -- a narrower check keyed on the 19-library block's own array
    # contents doesn't fire for the Qt6Core-only variant and was
    # silently leaving IT unremoved.
    if "// Qt 6.11 preload:" in src:
        src = re.sub(
            r"\n[ \t]*// Qt 6\.11 preload:.*?\n[ \t]*\}\n[ \t]*\}\n\n*",
            "\n",
            src,
            count=1,
            flags=re.DOTALL,
        )

    if STALE_REFLECTION_BLOCK in src:
        src = src.replace(STALE_REFLECTION_BLOCK, "")

    # The dist is reused across builds, so a PythonActivity.java patched
    # by an earlier hook version still has the swapped-argument call (see
    # the startApplication comment below). Its "invoking
    # QtNative.startApplication" log line would make the injection guard
    # skip it, so migrate the call in place.
    src = src.replace(
        '            __m.invoke(null, "org.kivy.android.PythonActivity", "");\n',
        MAIN_LIB_JAVA + '            __m.invoke(null, "", __mainLib);\n',
    )
    # ...and one patched by the version that fixed the arguments but had
    # no soname fallback yet (MAIN_LIB_JAVA's first line on its own).
    _main_lib_line = MAIN_LIB_JAVA.splitlines(keepends=True)[0]
    if _main_lib_line in src and "new java.io.File(__mainLib)" not in src:
        src = src.replace(_main_lib_line, MAIN_LIB_JAVA, 1)

    # Ensure QtNative import is present
    if "import org.qtproject.qt.android.QtNative;" not in src:
        if "import android.os.Bundle;\n" in src:
            src = src.replace(
                "import android.os.Bundle;\n",
                "import android.os.Bundle;\nimport org.qtproject.qt.android.QtNative;\n",
                1,
            )

    src = src.replace("QtNative.setEnvironmentVariable(", "setEnvironmentVariable(")

    marker = "    @Override\n"
    if (marker in src
            and "public void setEnvironmentVariable(String key, String value)" not in src):
        src = src.replace(marker, HELPER_METHOD + marker, 1)

    if "preloaded " not in src:
        for opener in (
            "    public void onCreate(Bundle savedInstanceState) {\n",
            "    protected void onCreate(Bundle savedInstanceState) {\n",
        ):
            if opener in src:
                src = src.replace(opener, opener + PRELOAD_QT_LIBS, 1)
                break

    # Inject the reflection-based QtNative.startApplication call AND the
    # dark-bars block after super.onCreate. QtLoader.loadQtLibraries()
    # fails on some OEM ROMs (it looks for QtQuick.abi3.so at a path
    # that Android may not populate). The reflection call bypasses Qt's
    # own loader and invokes the JNI start entry directly.
    #
    # Real signature (confirmed against qtbase 6.11.2's actual
    # QtNative.java): static void startApplication(String params,
    # String mainLib) -- params FIRST, mainLib SECOND. This was
    # previously called as m.invoke(null, "org.kivy.android.PythonActivity", "")
    # -- an Activity class name in the params slot and an empty mainLib.
    # Internally it builds qtParams = mainLib + " " + params, which
    # native code parses to find the library to dlopen -- with mainLib
    # empty, it resolved to "org.kivy.android.PythonActivity" and threw
    # "dlopen failed: library \"org.kivy.android.PythonActivity\" not
    # found" on a background thread, silently (caught internally, no
    # crash) preventing the actual native entry point from ever running
    # -- window drawn, process alive, Python never invoked: exactly the
    # black-screen-no-crash symptom. mainLib must be the main library's
    # real absolute path, matching QtLoader.loadMainLibrary()'s own
    # resolution (getApkNativeLibrariesDir() + "lib" + name + ".so").
    # Guard keys off the reflection log line, not the dark-bars line,
    # so a partial prior injection doesn't cause this to be skipped.
    if "invoking QtNative.startApplication" not in src:
        log_marker = "        super.onCreate(savedInstanceState);"
        if log_marker in src:
            inject = (
                log_marker + "\n"
                "        android.util.Log.v(\"PythonActivity\", "
                "\"->> Returned from super.onCreate(), invoking QtNative.startApplication\");\n"
                "        try {\n"
                + MAIN_LIB_JAVA +
                "            java.lang.reflect.Method __m = Class.forName(\"org.qtproject.qt.android.QtNative\")\n"
                "                .getDeclaredMethod(\"startApplication\", String.class, String.class);\n"
                "            __m.setAccessible(true);\n"
                "            __m.invoke(null, \"\", __mainLib);\n"
                "        } catch (Throwable __t) {\n"
                "            android.util.Log.e(\"PythonActivity\", \"Failed to call QtNative.startApplication: \" + __t);\n"
                "        }\n"
                "        android.util.Log.v(\"PythonActivity\", "
                "\"->> QtNative.startApplication returned\");\n"
                + DARK_SYSTEM_BARS_JAVA
            )
            src = src.replace(log_marker, inject, 1)

    # A dist patched by an earlier hook version has the old dark-bars
    # block (no window background, no re-apply): swap in the current one.
    if OLD_DARK_SYSTEM_BARS_JAVA in src:
        src = src.replace(OLD_DARK_SYSTEM_BARS_JAVA, DARK_SYSTEM_BARS_JAVA, 1)

    if src != orig:
        p.write_text(src)
        return True
    return False


def _patch_libs_xml(dist):
    """Fixes a real bug in p4a's own bootstraps/qt/build/templates/libs.tmpl.xml
    (confirmed against p4a 2024.01.21's actual source and QtLoader.java's
    real source in qtbase, both LGPL/public): its generated libs.xml's
    load_local_libs array registers each Qt module's Python binding as
    "<abi>;Qt<Module>.abi3.so" -- already ending in ".so". QtLoader's
    getLibrariesFullPaths() only prepends "lib" to a name that does NOT
    already end in ".so", so it looks up that literal, unprefixed name in
    the app's real extracted native-library directory -- a name Android's
    PackageManager never actually extracts there (it only extracts
    lib*.so-pattern entries from an APK's lib/<abi>/ directory), causing
    "QtLoader: Can't find '.../QtQuick.abi3.so'" and a hard app-launch
    failure. The adjacent libshiboken6.abi3.so/libpyside6.abi3.so/
    libpyside6qml.abi3.so entries in the same template are already
    correctly prefixed and untouched by this.

    _copy_all_runtime_libs() above renames the matching files on disk to
    add the same "lib" prefix; this rewrites libs.xml so QtLoader's own
    lookup name actually matches what's really on disk.
    """
    libs_xml = dist / "src" / "main" / "res" / "values" / "libs.xml"
    if not libs_xml.exists():
        warning(f"p4a_hook: libs.xml not found at {libs_xml}, skipping")
        return False
    src = libs_xml.read_text()
    orig = src
    src = re.sub(r";(Qt\w+\.abi3\.so)\b", r";lib\1", src)
    if src != orig:
        libs_xml.write_text(src)
        return True
    return False


def _dist_dir(toolchain):
    try:
        dist = getattr(toolchain, "_dist", None)
        if dist is not None:
            return Path(getattr(dist, "dist_dir"))
    except Exception:
        pass
    return Path.cwd()


def _copy_all_runtime_libs(dist):
    """Copy every native runtime .so from the PySide6/shiboken6 bundle into
    libs/arm64-v8a/, flattened, so Android's System.loadLibrary can find them.

    Sources:
      - PySide6/Qt/lib/       — libQt6*.so, libav*.so, FFmpeg stubs
      - PySide6/Qt/plugins/   — Qt plugins (platform, images, styles, etc.)
      - PySide6/Qt/qml/       — QML plugins (each module has a plugin .so)
      - PySide6/*.so          — top-level bindings: lib*.so (e.g.
                                libpyside6.abi3.so) AND the Qt*.abi3.so
                                Python-extension-shaped shims (QtCore.abi3.so,
                                QtQuick.abi3.so, etc.) -- despite the name,
                                Qt 6.11's Android bootstrap loads the latter
                                natively via System.loadLibrary() too, so
                                both are copied and neither should be
                                stripped of symbols later in this function.
      - shiboken6/*.so        — libshiboken6.abi3.so
    """
    dest = dist / "libs" / "arm64-v8a"
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    seen = set()

    # Locations where every .so is a native runtime library.
    full_runtime_dirs = [
        "_python_bundle__arm64-v8a/_python_bundle/site-packages/PySide6/Qt/lib",
        "_python_bundle__arm64-v8a/_python_bundle/site-packages/PySide6/Qt/plugins",
        "_python_bundle__arm64-v8a/_python_bundle/site-packages/PySide6/Qt/qml",
        "_python_bundle/site-packages/PySide6/Qt/lib",
        "_python_bundle/site-packages/PySide6/Qt/plugins",
        "_python_bundle/site-packages/PySide6/Qt/qml",
    ]

    # Locations where we only want the top-level `lib*.so` files, not Python
    # bindings like QtCore.abi3.so.
    top_level_lib_only = [
        "_python_bundle__arm64-v8a/_python_bundle/site-packages/PySide6",
        "_python_bundle__arm64-v8a/_python_bundle/site-packages/shiboken6",
        "_python_bundle/site-packages/PySide6",
        "_python_bundle/site-packages/shiboken6",
    ]

    def _copy_one(so: Path, rename_to: str = None):
        nonlocal copied
        if not so.is_file() or so.is_symlink():
            return
        name = rename_to or so.name
        if is_pruned(name):
            return
        if name in seen:
            return
        target = dest / name
        if target.exists() and target.stat().st_mtime >= so.stat().st_mtime:
            seen.add(name)
            return
        try:
            shutil.copy2(so, target)
            seen.add(name)
            copied += 1
        except Exception as e:
            warning(f"p4a_hook: failed to copy {so} -> {target}: {e}")

    for pattern in full_runtime_dirs:
        src_dir = dist / pattern
        if not src_dir.exists():
            continue
        info(f"p4a_hook: scanning (recursive) {src_dir}")
        for so in src_dir.rglob("*.so"):
            _copy_one(so)

    for pattern in top_level_lib_only:
        src_dir = dist / pattern
        if not src_dir.exists():
            continue
        info(f"p4a_hook: scanning (lib*.so only) {src_dir}")
        for so in src_dir.glob("lib*.so"):
            _copy_one(so)
        # Qt 6.11's Android bootstrap calls System.loadLibrary("QtQuick")
        # during QtActivity.onCreate. Despite the ".abi3" suffix (which
        # normally indicates a Python extension), Qt treats these as
        # native libraries it must find in libs/arm64-v8a/. Copy them.
        #
        # Renamed with a "lib" prefix on the way in (QtQuick.abi3.so ->
        # libQtQuick.abi3.so) -- confirmed against QtLoader.java's real
        # source (org.qtproject.qt.android.QtLoader, part of qtbase,
        # LGPL) and p4a's own qt bootstrap template
        # (bootstraps/qt/build/templates/libs.tmpl.xml): Android's
        # PackageManager only ever extracts lib*.so entries from an
        # APK's lib/<abi>/ directory into the app's real native
        # library dir at install time -- an unprefixed name never gets
        # extracted there at all, regardless of extractNativeLibs.
        # QtLoader's own getLibrariesFullPaths() only adds a "lib"
        # prefix to a name that does NOT already end in ".so"; p4a's
        # libs.tmpl.xml registers these particular entries as
        # "Qt<module>.abi3.so" (already ending in ".so", unlike the
        # correctly-prefixed libshiboken6.abi3.so/libpyside6.abi3.so
        # entries right next to them in the same template) -- so
        # QtLoader looks up that literal, never-extracted, unprefixed
        # name and fails with "Can't find '.../QtQuick.abi3.so'".
        # _patch_libs_xml() below rewrites those specific entries in
        # the generated libs.xml to match this renamed file.
        info(f"p4a_hook: scanning (Qt*.abi3.so, renamed with lib prefix) {src_dir}")
        for so in src_dir.glob("Qt*.abi3.so"):
            _copy_one(so, rename_to="lib" + so.name)

    info(f"p4a_hook: copied {copied} native .so files into {dest}")

    # Strip debug symbols from every .so in libs/. Recovers 50-70% of
    # the size of each library with zero functionality risk.
    ndk = os.environ.get("ANDROIDNDK")
    if not ndk:
        warning("p4a_hook: ANDROIDNDK unset; skipping strip")
        return

    strip_candidates = list(Path(ndk).rglob("llvm-strip"))
    if not strip_candidates:
        warning("p4a_hook: llvm-strip not found in NDK; skipping strip")
        return
    strip_bin = str(strip_candidates[0])

    # Do NOT strip these — Python loads them directly and strip has
    # been observed to break some shiboken entry points.
    SKIP_STRIP = {
        "libshiboken6.abi3.so",
        "libpyside6.abi3.so",
        "libpyside6qml.abi3.so",
        # Diagnostic: this is the one Qt library whose System.loadLibrary()
        # preload consistently fails with "JNI_ERR returned from
        # JNI_OnLoad" (reproduced across multiple cold launches), while
        # every other stripped libQt6*.so preloads fine. Excluding it from
        # stripping to test whether --strip-unneeded is corrupting
        # something JNI_OnLoad depends on. Revert if this doesn't fix it.
        "libQt6QuickTemplates2_arm64-v8a.so",
    }

    info(f"p4a_hook: stripping .so files with {strip_bin}")
    stripped = 0
    for so in dest.glob("*.so"):
        if so.name in SKIP_STRIP:
            continue
        # Also skip every libQt*.abi3.so shim (libQtCore.abi3.so,
        # libQtQuick.abi3.so, etc. -- renamed with a "lib" prefix by
        # _copy_all_runtime_libs() above so Android's PackageManager
        # actually extracts them) -- despite the ".abi3" suffix looking
        # like a plain Python extension module, Qt 6.11's Android
        # bootstrap calls System.loadLibrary()/reads them as real native
        # libraries during onCreate. Stripping one has produced "fail
        # loading Qt*.abi3.so" at runtime -- same risk class as the
        # shiboken/pyside files above, just not caught by the original
        # SKIP_STRIP set.
        if fnmatch(so.name, "libQt*.abi3.so"):
            continue
        try:
            subprocess.run(
                [strip_bin, "--strip-unneeded", str(so)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            stripped += 1
        except Exception as e:
            warning(f"p4a_hook: strip failed on {so}: {e}")
    info(f"p4a_hook: stripped {stripped} .so files")


def before_apk_build(toolchain, *args, **kwargs):
    dist = _dist_dir(toolchain)
    _patch_blacklist(dist / "blacklist.txt")
    info("p4a_hook: before_apk_build — ensuring libc++_shared.so and Qt libs are present")
    dist = _dist_dir(toolchain)
    info(f"p4a_hook: dist = {dist}")

    ndk = os.environ.get("ANDROIDNDK")
    if ndk:
        candidates = list(Path(ndk).rglob("libc++_shared.so"))
        chosen = None
        for c in candidates:
            if "aarch64" in str(c):
                chosen = c
                break
        if chosen is None and candidates:
            chosen = candidates[0]
        if chosen is not None:
            dest_dir = dist / "libs" / "arm64-v8a"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(chosen, dest_dir / "libc++_shared.so")
            info(f"p4a_hook: copied libc++_shared.so from {chosen}")
            stale = dist / "src" / "main" / "jniLibs" / "arm64-v8a" / "libc++_shared.so"
            if stale.exists():
                stale.unlink()
    else:
        warning("p4a_hook: ANDROIDNDK not set; cannot locate libc++_shared.so")

    _copy_all_runtime_libs(dist)

    # qt bootstrap source blacklist (regenerated on re-clone)
    p4a_root = dist.parent.parent.parent.parent  # .../python-for-android
    qt_bl = p4a_root / "pythonforandroid/bootstraps/qt/build/blacklist.txt"
    _patch_blacklist(qt_bl)


ADAPTIVE_ICON_XML = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/icon_background"/>
    <foreground android:drawable="@mipmap/icon_foreground"/>
</adaptive-icon>
"""


def _install_adaptive_icon(dist):
    """Android 8+ shrinks a plain launcher icon and pads it with WHITE.
    An adaptive icon (dark background layer + the die as foreground)
    fills the launcher's own mask instead. p4a's --icon-fg/--icon-bg
    would write this too, but into res/mipmap-anydpi-v26/, which the Qt
    bootstrap doesn't have -- so it's added here, after p4a has copied
    the plain icon.png in and before Gradle reads res/. icon.png stays
    as the pre-Android-8 fallback."""
    src = Path(__file__).resolve().parents[2] / "packaging" / "android"
    fg, bg = src / "icon_foreground.png", src / "icon_background.png"
    if not (fg.exists() and bg.exists()):
        warning(f"p4a_hook: adaptive icon layers missing from {src} -- launcher icon will be padded white")
        return False
    res = dist / "src" / "main" / "res"
    (res / "mipmap").mkdir(parents=True, exist_ok=True)
    (res / "mipmap-anydpi-v26").mkdir(parents=True, exist_ok=True)
    shutil.copy(fg, res / "mipmap" / "icon_foreground.png")
    shutil.copy(bg, res / "mipmap" / "icon_background.png")
    (res / "mipmap-anydpi-v26" / "icon.xml").write_text(ADAPTIVE_ICON_XML)
    return True


def before_apk_assemble(toolchain, *args, **kwargs):
    info("p4a_hook: before_apk_assemble — patching PythonActivity.java")
    dist = _dist_dir(toolchain)

    if _install_adaptive_icon(dist):
        info("p4a_hook: installed the adaptive launcher icon (res/mipmap-anydpi-v26/icon.xml)")

    # p4a's own "Copying libs" step (which runs after our before_apk_build)
    # copies every .so from libs_collections/ into libs/arm64-v8a/, ignoring
    # our prune list. Remove the pruned files here, after that step has run
    # and before Gradle packages them.
    libs_dir = dist / "libs" / "arm64-v8a"
    if libs_dir.exists():
        pruned = []
        for so in libs_dir.glob("*.so"):
            if is_pruned(so.name):
                try:
                    size_kb = so.stat().st_size // 1024
                    so.unlink()
                    pruned.append(f"{so.name} ({size_kb} KB)")
                except Exception as e:
                    warning(f"p4a_hook: failed to remove {so}: {e}")
        if pruned:
            info(f"p4a_hook: removed {len(pruned)} pruned .so files from libs/")
        else:
            info("p4a_hook: no pruned .so files to remove from libs/")

    # See _patch_libs_xml()'s docstring: p4a's own libs.tmpl.xml registers
    # each Qt module's Python binding under an unprefixed name QtLoader
    # can never actually find on disk. Patched here, as late as possible
    # (right before Gradle reads resources), same reasoning as patching
    # PythonActivity.java at this same hook point rather than earlier.
    if _patch_libs_xml(dist):
        info("p4a_hook: PATCHED libs.xml (added missing lib prefix to Qt module abi3.so entries)")
    else:
        info("p4a_hook: no change needed in libs.xml")

    target = dist / "src/main/java/org/kivy/android/PythonActivity.java"
    if not target.exists():
        warning(f"p4a_hook: PythonActivity.java not found at {target}")
        return
    if _patch_java_file(target):
        info(f"p4a_hook: PATCHED {target}")
    else:
        info(f"p4a_hook: no change needed {target}")

    _src = target.read_text()
    for needle in ("Qt6Core_arm64-v8a",
                   "invoking QtNative.startApplication",
                   '__m.invoke(null, "", __mainLib)',
                   "QtNative.startApplication returned",
                   "setNavigationBarContrastEnforced"):
        if needle not in _src:
            raise SystemExit(
                f"FATAL: p4a_hook patch missing from compiled PythonActivity.java: {needle!r}"
            )
    if 'invoke(null, "org.kivy.android.PythonActivity"' in _src:
        raise SystemExit(
            "FATAL: PythonActivity.java still has the swapped-argument "
            "QtNative.startApplication call (black screen at runtime)"
        )
    info("p4a_hook: PythonActivity.java contains all expected patches")
