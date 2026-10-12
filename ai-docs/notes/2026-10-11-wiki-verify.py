"""Wiki verification for polywright: every example on the wiki, run against a published release.

    python ai-docs/notes/2026-10-11-wiki-verify.py VERSION [--blender PATH] > ai-docs/notes/2026-10-11-wiki-verify.out.txt

Downloads polywright-VERSION.zip from the GitHub release into a scratch folder (never the working tree), then runs
each page's commands as the page shows them, from that scratch folder. Output sections are '## label' lines, as
wikiwright's diffout and outputs expect. The scratch path is masked as <work>, timings as <s>, the Blender path as
<blender>. Commands on the pages read `python pw.py ...`; here `pw.py` is the release's skills/polywright/scripts/pw.py.
Needs Blender (POLYWRIGHT_BLENDER or an install pw.py finds), numpy and Pillow for texture, trimesh for 3mf.
"""
import io
import json
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
import zlib

VERSION = sys.argv[1] if len(sys.argv) > 1 else "0.1.1"
WORK = tempfile.mkdtemp(prefix="pwwiki_")
PLUGIN = os.path.join(WORK, "plugin")
url = "https://github.com/m4bwav/polywright/releases/download/v%s/polywright-%s.zip" % (VERSION, VERSION)
zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url, timeout=120).read())).extractall(PLUGIN)
PW = os.path.join(PLUGIN, "skills", "polywright", "scripts", "pw.py")
RUN = os.path.join(WORK, "run")
os.makedirs(RUN)


def mask(text):
    for w in (RUN, WORK):
        for form in (w, w.replace("\\", "\\\\"), w.replace("\\", "/")):
            text = text.replace(form + "\\\\", "").replace(form + "\\", "").replace(form + "/", "").replace(form, "<work>")
    text = re.sub(r'"seconds": [0-9.]+', '"seconds": "<s>"', text)
    text = re.sub(r'"path": "[^"]*blender(\.exe)?"', '"path": "<blender>"', text, flags=re.I)
    return text.rstrip()


def show(label, value):
    print("## " + label)
    print(value)
    print()


def snippet(label, text):
    """Run a page's shell block line by line, as the page shows it, in the scratch run folder."""
    out = []
    for line in text.strip().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        args = shlex.split(line)
        if args[:2] == ["python", "pw.py"]:
            args = [sys.executable, PW] + args[2:]
        p = subprocess.run(args, cwd=RUN, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out.append(mask(p.stdout))
        if p.stderr.strip():
            out.append("[stderr] " + mask(p.stderr))
        out.append("[exit %d]" % p.returncode)
    show(label, "\n".join(out))


def write(name, text):
    path = os.path.join(RUN, name)
    os.makedirs(os.path.dirname(path) or RUN, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def png(name, w=64, h=64):
    raw = b"".join(b"\x00" + bytes(((x * 7 + y * 3) ^ (x * y)) % 256 for x in range(w) for _ in range(3)) for y in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(os.path.join(RUN, name), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


show("installed", "polywright %s from %s" % (VERSION, url))

# ---- Home and Getting started
snippet("version", """
python pw.py --version
""")

# ---- Commands: the asset folder
snippet("new", """
python pw.py new fountain --name Fountain --kind imagined --route generate --targets game-roblox,print-fdm --real-size-m 1.0
""")

# ---- Places: a small invented OSM extract, offline (flat ground), so no server is asked
OSM = {"version": 0.6, "generator": "wiki fixture (invented coordinates)", "elements": [
    {"type": "node", "id": 1, "lat": 40.0001, "lon": -74.99995}, {"type": "node", "id": 2, "lat": 40.0001, "lon": -74.9988},
    {"type": "node", "id": 3, "lat": 40.0009, "lon": -74.9988}, {"type": "node", "id": 4, "lat": 40.0009, "lon": -74.99995},
    {"type": "node", "id": 11, "lat": 40.0004, "lon": -74.9995}, {"type": "node", "id": 12, "lat": 40.0004, "lon": -74.99938},
    {"type": "node", "id": 13, "lat": 40.0005, "lon": -74.99938}, {"type": "node", "id": 14, "lat": 40.0005, "lon": -74.9995},
    {"type": "node", "id": 21, "lat": 40.0002, "lon": -75.0005}, {"type": "node", "id": 22, "lat": 40.0002, "lon": -74.9980},
    {"type": "node", "id": 31, "lat": 40.0007, "lon": -74.9991, "tags": {"natural": "tree", "height": "7"}},
    {"type": "way", "id": 100, "nodes": [1, 2, 3, 4, 1], "tags": {"leisure": "park", "name": "Fixture Park"}},
    {"type": "way", "id": 101, "nodes": [11, 12, 13, 14, 11], "tags": {"building": "yes", "height": "6"}},
    {"type": "way", "id": 102, "nodes": [21, 22], "tags": {"highway": "residential"}}]}
write("park/data/osm.json", json.dumps(OSM))
snippet("place", """
python pw.py place --bbox 40.0000,-75.0000,40.0010,-74.9987 --dem flat --res 2 --out park --print-mm 60
""")

# ---- Commands: looking at a model
snippet("inspect", """
python pw.py inspect park/scene.glb --fast
""")
snippet("check fail", """
python pw.py check park/scene.glb --target game-roblox --real-size-m 110
""")
snippet("convert", """
python pw.py convert park/scene.glb park/roblox.glb --join --uv --max-tris 5000
""")
snippet("check list", """
python pw.py check --list
""")
snippet("render", """
python pw.py render park/print.stl --out park/renders --views front,top,iso --size 256
""")
snippet("lods", """
python pw.py lods park/roblox.glb --out park/lods --ratios 1,0.5,0.25
""")

# ---- Printing
snippet("printable", """
python pw.py printable park/roblox.glb park/solid.stl --size-mm 60 --wall-mm 1.2
python pw.py check park/solid.stl --target print-fdm
""")
snippet("3mf", """
python pw.py 3mf park/print.stl park/solid.stl --out park/two-colours.3mf
""")

# ---- The contract: manifest
snippet("manifest", """
python pw.py manifest fountain --add-output park/solid.stl --target print-fdm
python pw.py manifest fountain --add-source https://example.com/ref.png --what "reference photo" --author "A. Person"
python pw.py manifest fountain --validate
""")

# ---- Recipes: a bpy script
HELLO = """
import bpy, sys
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=float(args[0]))
print("[pw] height", round(bpy.context.active_object.dimensions.z, 3))
"""
write("hello_bpy.py", HELLO.lstrip())
show("hello_bpy.py (file)", open(os.path.join(RUN, "hello_bpy.py"), encoding="utf-8").read().rstrip())
snippet("bpy", """
python pw.py bpy hello_bpy.py -- 2.5
""")
write("old_api.py", """import bpy
bpy.ops.import_scene.obj(filepath="chair.obj")
""")
snippet("bpy traceback", """
python pw.py bpy old_api.py
""")

# ---- Recipes: textures
png("bricks.png")
snippet("texture", """
python pw.py texture bricks.png --out tex --seamless
""")

# ---- Errors and edge cases
snippet("error missing file", """
python pw.py inspect nothing-here.glb
""")
snippet("error unknown target", """
python pw.py check park/solid.stl --target game-godot
""")
snippet("error bad bbox", """
python pw.py place --bbox 40.0010,-75.0000,40.0000,-74.9987 --out park2
""")
snippet("error no comfyui", """
python pw.py gen --image bricks.png --out raw.glb --host http://127.0.0.1:9
""")
write("ui-workflow.json", json.dumps({"nodes": [], "links": []}))
snippet("error workflow no host", """
python pw.py gen --image bricks.png --workflow ui-workflow.json --out raw.glb --host http://127.0.0.1:9
""")

shutil.rmtree(WORK, ignore_errors=True)
