[app]

title = MIMIC
package.name = mimic
package.domain = org.mimic

source.dir = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP
source.include_exts = py,qml,png,jpg,jpeg,ico,gif,svg,pdf,json,md,ttf
source.include_patterns = packaging/android/icon.png
source.exclude_dirs = .git,build,dist,deployment,.buildozer,packaging/windows,installer,mimic_app_reference
source.exclude_patterns = *.whl,*.pyc,*.pyo,buildozer.spec,buildozer.spec.*,pysidedeploy.spec

version = 0.1
requirements = python3,shiboken6,PySide6

orientation = portrait
fullscreen = 0

android.api = 31
android.minapi = 21
android.ndk_api = 21
android.sdk_path = /home/eobrien/.pyside6_android_deploy/android-sdk
android.ndk_path = /home/eobrien/.pyside6_android_deploy/android-ndk/android-ndk-r28c
android.archs = arm64-v8a
android.allow_backup = True

android.permissions = android.permission.INTERNET,android.permission.ACCESS_NETWORK_STATE,android.permission.WRITE_EXTERNAL_STORAGE

# NOTE: no inner quotes around the value -- quoting this produces
# android:theme=""@android:style/...""  in the generated manifest,
# which is invalid XML and fails Gradle at processDebugMainManifest.
android.apptheme = @android:style/Theme.NoTitleBar
android.icon = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/packaging/android/icon.png

# PySide6-specific: this is the Qt bootstrap, not SDL2
p4a.bootstrap = qt

# Pinned: p4a's master branch targets Python 3.14, where several of
# its own patches for older Pythons (written for 3.7-3.11) fail to
# apply -- the build dies at "Applying patches for python3" before it
# ever starts compiling. v2024.01.21 targets Python 3.11.5, where they
# all apply cleanly. Never remove this line -- buildozer tracks the
# p4a URL/branch in its own state (not git) and re-clones master on
# every run if this isn't set, silently undoing the pin.
p4a.branch = v2024.01.21

# Local recipes provide the Qt bootstrap glue
p4a.local_recipes = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/recipes

# Which Qt modules the app uses
android.qt_libs = Quick,Core,Qml,Gui,QuickControls2,OpenGL,Network

# Don't run setup.py
p4a.setup_py = false

# Build hook (deployment/recipes/p4a_hook.py, gitignored/local to each
# machine -- not tracked in this repo): before_apk_build bundles
# libc++_shared.so into the dist (Qt refuses to load without it);
# before_apk_assemble patches the dist's PythonActivity.java to replace
# QtNative.setEnvironmentVariable(...), removed in Qt 6.11, with
# android.system.Os.setenv(...) (p4a v2024.01.21's template still
# calls the removed method, which fails the Java compile otherwise).
p4a.hook = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/recipes/p4a_hook.py

# Qt Android platform plugin's jars -- without these, Gradle can't find
# org.qtproject.qt.android.bindings.QtActivity and Java compile fails
# with "package does not exist". Do not list a jar here twice --
# duplicates break Gradle classpath resolution.
android.add_jars = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/jar/PySide6/jar/Qt6Android.jar,/mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/jar/PySide6/jar/Qt6AndroidBindings.jar

# Extra args to p4a — matches what pysidedeploy.spec passes
p4a.extra_args = --load-local-libs=plugins_platforms_qtforandroid --qt-libs=Quick,Core,Qml,Gui,QuickControls2,OpenGL,Network --icon=/mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/packaging/android/icon.png

[buildozer]
log_level = 2
warn_on_root = 0
