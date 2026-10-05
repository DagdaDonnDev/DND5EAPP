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
from pathlib import Path
from pythonforandroid.logger import info, warning


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


PRELOAD_QT_LIBS = '''        // Qt 6.11 preload: System.loadLibrary() each Qt library in dependency
        // order so its JNI_OnLoad runs on the main thread with JVM cached.
        String[] qtPreloadLibs = {
            "Qt6Core_arm64-v8a",
            "Qt6Network_arm64-v8a",
            "Qt6Gui_arm64-v8a",
            "Qt6OpenGL_arm64-v8a",
            "Qt6Qml_arm64-v8a",
            "Qt6QmlModels_arm64-v8a",
            "Qt6QmlWorkerScript_arm64-v8a",
            "Qt6QmlMeta_arm64-v8a",
            "Qt6QmlNetwork_arm64-v8a",
            "Qt6QuickTemplates2_arm64-v8a",
            "Qt6QuickControls2Impl_arm64-v8a",
            "Qt6QuickControls2_arm64-v8a",
            "Qt6QuickLayouts_arm64-v8a",
            "Qt6QuickEffects_arm64-v8a",
            "Qt6QuickShapes_arm64-v8a",
            "Qt6QuickVectorImage_arm64-v8a",
            "Qt6QuickDialogs2Utils_arm64-v8a",
            "Qt6QuickDialogs2_arm64-v8a",
            "Qt6Quick_arm64-v8a",
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


def _patch_java_file(path):
    p = Path(path)
    if not p.exists():
        return False
    src = p.read_text()
    orig = src

    if STALE_REFLECTION_BLOCK in src:
        src = src.replace(STALE_REFLECTION_BLOCK, "")

    src = src.replace("QtNative.setEnvironmentVariable(", "setEnvironmentVariable(")

    if "QtNative." not in src:
        src = src.replace("import org.qtproject.qt.android.QtNative;\n", "")

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

    if src != orig:
        p.write_text(src)
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
      - PySide6/*.so          — top-level bindings (libpyside6.abi3.so, etc.)
      - shiboken6/*.so        — libshiboken6.abi3.so

    Two kinds of .so file get filtered out from the top-level dirs:
      - Qt*.abi3.so           — Python extension modules, loaded by Python's
                                import system, not by Android's loader
      - Shiboken.abi3.so      — same, Python extension module
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

    def _copy_one(so: Path):
        nonlocal copied
        if not so.is_file() or so.is_symlink():
            return
        name = so.name
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
        info(f"p4a_hook: scanning (Qt*.abi3.so) {src_dir}")
        for so in src_dir.glob("Qt*.abi3.so"):
            _copy_one(so)

    info(f"p4a_hook: copied {copied} native .so files into {dest}")


def before_apk_build(toolchain, *args, **kwargs):
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


def before_apk_assemble(toolchain, *args, **kwargs):
    info("p4a_hook: before_apk_assemble — patching PythonActivity.java")
    dist = _dist_dir(toolchain)
    target = dist / "src/main/java/org/kivy/android/PythonActivity.java"
    if not target.exists():
        warning(f"p4a_hook: PythonActivity.java not found at {target}")
        return
    if _patch_java_file(target):
        info(f"p4a_hook: PATCHED {target}")
    else:
        info(f"p4a_hook: no change needed {target}")
