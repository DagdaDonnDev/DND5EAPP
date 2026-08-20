"""
Refactor Pass module.

One-off, already-executed maintenance script: split ui/action_abilities.py
out of ui/sheet.py and deduplicated data/feature_tooltips.py's
FEATURE_DESCS dict. Not part of the application and not imported by
it; the hardcoded source path is specific to the machine it originally
ran on. Kept for historical reference only.

Author: Ethan O'Brien
Date: 2026-08-20
"""

from pathlib import Path
import re, ast, collections

root = Path(r"C:\Users\OBRIET\Downloads\mimic_v58\dnd_app")
sheet = root / "ui" / "sheet.py"
src = sheet.read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)

start = None
end = None
for i, line in enumerate(lines):
    if start is None and line.startswith("def _classify_action"):
        start = i
    if start is not None and line.startswith("class CharacterSheet"):
        end = i
        break
assert start is not None and end is not None, (start, end)

chunk = "".join(lines[start:end])

header = '''"""
Action-economy helpers and KNOWN_ACTIONS catalog.

Extracted from ui/sheet.py so combat action cards stay maintainable
outside the CharacterSheet monolith.
"""
from __future__ import annotations

from collections import defaultdict

'''

out = root / "ui" / "action_abilities.py"
out.write_text(header + chunk, encoding="utf-8")
print(f"Wrote {out} ({end-start} lines)")

replacement = (
    "# Action economy helpers live in ui/action_abilities.py\n"
    "from dnd_app.ui.action_abilities import (\n"
    "    build_action_abilities,\n"
    "    _classify_action,\n"
    "    _breath_weapon_desc,\n"
    "    _resolve_dynamic_combat_text,\n"
    "    _append_cantrip_scaling_note,\n"
    "    _feature_matches_char_subclass,\n"
    ")\n\n"
)
new_lines = lines[:start] + [replacement] + lines[end:]
sheet.write_text("".join(new_lines), encoding="utf-8")
print(f"sheet.py now {len(new_lines)} lines (was {len(lines)})")

# Deduplicate FEATURE_DESCS
tips_path = root / "data" / "feature_tooltips.py"
tips_src = tips_path.read_text(encoding="utf-8")
tree = ast.parse(tips_src)
target = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "FEATURE_DESCS":
                target = node
if target and isinstance(target.value, ast.Dict):
    keys = []
    for k in target.value.keys:
        if isinstance(k, ast.Constant):
            keys.append(k.value)
    c = collections.Counter(keys)
    dups = {k: n for k, n in c.items() if n > 1}
    print(f"FEATURE_DESCS keys={len(keys)} unique={len(c)} dups={len(dups)}")
    ns = {}
    exec(compile(tips_src, str(tips_path), "exec"), ns)
    descs = ns["FEATURE_DESCS"]
    tip_lines = tips_src.splitlines(keepends=True)
    start_i = target.lineno - 1
    end_i = target.end_lineno
    parts = ["FEATURE_DESCS = {\n"]
    for k, v in sorted(descs.items(), key=lambda kv: kv[0].lower()):
        parts.append(f"    {k!r}: {v!r},\n")
    parts.append("}\n")
    new_tip = "".join(tip_lines[:start_i] + parts + tip_lines[end_i:])
    tips_path.write_text(new_tip, encoding="utf-8")
    print(f"Rewrote feature_tooltips.py with {len(descs)} unique keys")
else:
    print("FEATURE_DESCS assign not found")

print("done")
