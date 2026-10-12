"""Checks that pw.py finds an installed Blender app by its install-folder search, not only through PATH or env.

Run from the repository root after installing Blender where users install it (CI's blender-app job):
python tests/check_discovery.py   (exit 0 = found and runs, 1 = not found)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "polywright", "scripts"))
import pw  # noqa: E402

for env in ("POLYWRIGHT_BLENDER", "BLENDER", "POLYWRIGHT_BPY_PYTHON"):
    os.environ.pop(env, None)
cands = pw.blender_candidates()
folder = [p for p, src in cands if src == "install folder"]
be = pw.backend()
print(json.dumps({"candidates": cands, "install_folder": folder, "backend": be}, indent=1))
if not folder:
    sys.exit("no Blender found by the install-folder search")
if not be or be[0] != "blender":
    sys.exit("Blender found but `--version` did not run")
