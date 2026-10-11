"""Runs every `# recipe:` block in skills/polywright-blender/references/bpy-recipes.md in Blender.

Run from the repository root: python tests/test_recipes.py
Skips when no Blender is found (pw.py doctor). A recipe passes when Blender exits cleanly and the script printed
a line starting with "[pw] ok".
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "polywright", "scripts"))
import pw  # noqa: E402

DOC = os.path.join(ROOT, "skills", "polywright-blender", "references", "bpy-recipes.md")
BLOCKS = re.findall(r"```python\n(# recipe: ([\w-]+)\n.*?)```", open(DOC, encoding="utf-8").read(), re.S)


@unittest.skipUnless(pw.backend(), "Blender not found")
class Recipes(unittest.TestCase):
    pass


def make(code, name):
    def test(self):
        tmp = tempfile.mkdtemp(prefix="pwrecipe_")
        try:
            path = os.path.join(tmp, name + ".py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            os.environ["PW_OUT"] = tmp
            r = pw.run_blender_script(path, [], timeout=600)
            out = (r.get("stdout") or "") + (r.get("stderr") or "")
            self.assertTrue(r.get("ok"), "\n".join(pw.condense(out, 30)))
            self.assertRegex(out, r"\[pw\] ok", "\n".join(pw.condense(out, 30)))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return test


for code, name in BLOCKS:
    setattr(Recipes, "test_" + name.replace("-", "_"), make(code, name))


if __name__ == "__main__":
    print("%d recipes in %s" % (len(BLOCKS), os.path.relpath(DOC, ROOT)))
    unittest.main(verbosity=2)
