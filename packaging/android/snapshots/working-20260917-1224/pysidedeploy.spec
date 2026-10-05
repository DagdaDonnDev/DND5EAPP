[app]

# title of your application
title = MIMIC

# project root directory. default = The parent directory of input_file
project_dir = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP

# source file entry point path. default = main.py
input_file = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/main.py

# directory where the executable output is generated
exec_directory = .

# path to the project file relative to project_dir
project_file = 

# application icon
icon = /home/eobrien/.pyenv/versions/3.11.9/lib/python3.11/site-packages/PySide6/scripts/deploy_lib/pyside_icon.jpg

[python]

# python path
python_path = /home/eobrien/.pyenv/versions/3.11.9/bin/python3.11

# python packages to install
packages = Nuitka==4.1.1

# buildozer = for deploying Android application
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]

# paths to required qml files. comma separated
# normally all the qml files required by the project are added automatically
# design studio projects include the qml files using qt resources
qml_files = dnd_app/ui_android/qml/AbilitiesScreen.qml,dnd_app/ui_android/qml/App.qml,dnd_app/ui_android/qml/ClassScreen.qml,dnd_app/ui_android/qml/CreditsScreen.qml,dnd_app/ui_android/qml/DiceRollerScreen.qml,dnd_app/ui_android/qml/EquipmentScreen.qml,dnd_app/ui_android/qml/NavDrawer.qml,dnd_app/ui_android/qml/RaceDetailScreen.qml,dnd_app/ui_android/qml/RaceListScreen.qml,dnd_app/ui_android/qml/RestFlowDialog.qml,dnd_app/ui_android/qml/SaveLoadScreen.qml,dnd_app/ui_android/qml/SettingsScreen.qml,dnd_app/ui_android/qml/SheetAbilitiesScreen.qml,dnd_app/ui_android/qml/SheetActionsScreen.qml,dnd_app/ui_android/qml/SheetChoicesScreen.qml,dnd_app/ui_android/qml/SheetCombatScreen.qml,dnd_app/ui_android/qml/SheetCompanionsScreen.qml,dnd_app/ui_android/qml/SheetEquipmentScreen.qml,dnd_app/ui_android/qml/SheetFeaturesScreen.qml,dnd_app/ui_android/qml/SheetInfusionsScreen.qml,dnd_app/ui_android/qml/SheetLevelUpScreen.qml,dnd_app/ui_android/qml/SheetNotesScreen.qml,dnd_app/ui_android/qml/SheetProficienciesScreen.qml,dnd_app/ui_android/qml/SheetSpellsScreen.qml,dnd_app/ui_android/qml/StartMenuScreen.qml,dnd_app/ui_android/qml/imports/Mimic/MButton.qml,dnd_app/ui_android/qml/imports/Mimic/MCheckBox.qml,dnd_app/ui_android/qml/imports/Mimic/MFullPageDialog.qml,dnd_app/ui_android/qml/imports/Mimic/MPickerDialog.qml,dnd_app/ui_android/qml/imports/Mimic/MSpinBox.qml,dnd_app/ui_android/qml/imports/Mimic/MStatblockCard.qml,dnd_app/ui_android/qml/imports/Mimic/MTextField.qml,dnd_app/ui_android/qml/imports/Mimic/MToggleButton.qml,dnd_app/ui_android/qml/imports/Mimic/SheetHeader.qml,dnd_app/ui_android/qml/imports/Mimic/Theme.qml

# excluded qml plugin binaries
excluded_qml_plugins = QtCharts,QtQuick3D,QtSensors,QtTest,QtWebEngine

# qt modules used. comma separated
modules = Quick,Widgets,Core,Qml,Gui,QuickControls2,OpenGL,Network

# qt plugins used by the application. only relevant for desktop deployment
# for qt plugins used in android application see [android][plugins]
plugins = 

[android]

# path to pyside wheel
wheel_pyside = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/pyside6-6.11.2-6.11.2-cp311-cp311-android_aarch64.whl

# path to shiboken wheel
wheel_shiboken = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/shiboken6-6.11.2-6.11.2-cp311-cp311-android_aarch64.whl

# plugins to be copied to libs folder of the packaged application. comma separated
plugins = platforms_qtforandroid

[nuitka]

# usage description for permissions requested by the app as found in the info.plist file
# of the app bundle. comma separated
# eg = extra_args = --show-modules --follow-stdlib
macos.permissions = 

# mode of using nuitka. accepts standalone or onefile. default = onefile
mode = onefile

# specify any extra nuitka arguments
extra_args = --quiet --noinclude-qt-translations

[buildozer]

# build mode
# possible values = ["aarch64", "armv7a", "i686", "x86_64"]
# release creates a .aab, while debug creates a .apk
mode = debug

# path to pyside6 and shiboken6 recipe dir
recipe_dir = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/recipes

# path to extra qt android .jar files to be loaded by the application
jars_dir = /mnt/c/Users/OBRIET/Dev/Projects/Extra/DND/DND5EAPP/deployment/jar/PySide6/jar

# if empty, uses default ndk path downloaded by buildozer
ndk_path = /home/eobrien/.pyside6_android_deploy/android-ndk/android-ndk-r28c

# if empty, uses default sdk path downloaded by buildozer
sdk_path = /home/eobrien/.pyside6_android_deploy/android-sdk

# other libraries to be loaded at app startup. comma separated.
local_libs = plugins_platforms_qtforandroid

# architecture of deployed platform
arch = aarch64

