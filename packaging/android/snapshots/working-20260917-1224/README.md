Working Android build for MIMIC.
Date captured: see filename.

Key fixes that are load-bearing:
1. p4a_hook.py copies Qt*.abi3.so into libs/arm64-v8a/ (Qt 6.11's
   Android loader expects them there despite the .abi3 suffix).
2. p4a_hook.py preloads Qt6Core before Qt6Quick to prime the JVM cache.
3. p4a.extra_args includes --private=/tmp/mimic-app-staging, and the
   staging dir must contain main.py + dnd_app/ with ui_desktop included.
4. blacklist.txt in the dist includes lib2to3/tests/* so compileall
   doesn't die on Python 2 fixtures.
5. p4a.branch = v2024.01.21 must stay pinned in buildozer.spec.

If any of these regress, the app silently exits with System.exit(-1)
during QtActivity.onCreate.
