[app]

title = MIMIC
package.name = mimic
package.domain = org.mimic

source.dir = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP
source.include_exts = py,qml,png,jpg,jpeg,ico,gif,svg,pdf,json,md,ttf
# dnd_app/** and main.py explicit: the --private staging dir (see
# p4a.extra_args below) needs main.py + dnd_app/ (ui_desktop included --
# several ui_android bridges import pure-logic pieces of it, e.g.
# character_sheet.py's theme/flavor-text/level-up-choice-table reuse)
# copied into it, not just whatever source.include_exts happens to
# glob from source.dir.
source.include_patterns = dnd_app/**,main.py,packaging/android/icon.png
source.exclude_dirs = .git,build,dist,deployment,.buildozer,packaging/windows,installer,mimic_app_reference
source.exclude_patterns = *.whl,*.pyc,*.pyo,buildozer.spec,buildozer.spec.*,pysidedeploy.spec

version = 0.2.2
requirements = python3,shiboken6,PySide6

orientation = portrait
fullscreen = 0

android.api = 33
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
# android.debug=1 + android.release_artifact=apk + p4a.build_mode=release
# were briefly added here and removed. Release builds are safe: p4a
# 2024.01.21's build.tmpl.gradle sets no minifyEnabled, so R8 never
# strips the classes p4a_hook.py reaches by reflection. `buildozer
# android release` produces an AAB; deployment/make-android-apk.sh turns
# it into an installable APK.
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

# Build hook (deployment/recipes/p4a_hook.py -- tracked despite living
# under gitignored deployment/, see .gitignore's exception for it):
# before_apk_build bundles libc++_shared.so into the dist (Qt refuses
# to load without it); before_apk_assemble patches the dist's
# PythonActivity.java to replace QtNative.setEnvironmentVariable(...),
# removed in Qt 6.11, with
# android.system.Os.setenv(...) (p4a v2024.01.21's template still
# calls the removed method, which fails the Java compile otherwise).
p4a.hook = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/recipes/p4a_hook.py

# Qt Android platform plugin's jars -- without these, Gradle can't find
# org.qtproject.qt.android.bindings.QtActivity and Java compile fails
# with "package does not exist". Do not list a jar here twice --
# duplicates break Gradle classpath resolution.
#
# Qt6AndroidQuick.jar (org.qtproject.qt.android.QtQuickView and friends,
# from qtdeclarative's src/quick/platform/android/jar/) was missing
# here. libQt6Quick_arm64-v8a.so's own JNI_OnLoad (qandroidquickviewembedding.cpp,
# confirmed against real Qt 6.11.2 source) unconditionally calls
# QtAndroidQuickViewEmbedding::registerNatives(), which registers native
# methods against org.qtproject.qt.android.QtQuickView -- if that class
# isn't on the classpath, registerNatives() fails, JNI_OnLoad returns
# JNI_ERR, and QtLoader aborts its whole load sequence (see BUILD_APK.md's
# troubleshooting table). Added below.
android.add_jars = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/jar/PySide6/jar/Qt6Android.jar,/mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/jar/PySide6/jar/Qt6AndroidBindings.jar,/mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/jar/PySide6/jar/Qt6AndroidQuick.jar

# Extra args to p4a — matches what pysidedeploy.spec passes.
# --private=/tmp/mimic-app-staging: a real, populated staging directory
# (must contain main.py + dnd_app/, ui_desktop included) p4a copies the
# app's Python source from, rather than trusting source.include_* alone
# to have assembled the right tree in source.dir itself.
# --icon: matches android.icon above.
p4a.extra_args = --private=/tmp/mimic-app-staging --load-local-libs=plugins_platforms_qtforandroid --qt-libs=Quick,Core,Qml,Gui,QuickControls2,OpenGL,Network --icon=/mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/packaging/android/icon.png

[buildozer]
log_level = 2
warn_on_root = 0
