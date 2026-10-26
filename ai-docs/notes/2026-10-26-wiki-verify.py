"""Wiki verification for polywright: every example on the wiki, run against a published release.

    python ai-docs/notes/2026-10-26-wiki-verify.py VERSION > ai-docs/notes/2026-10-26-wiki-verify.out.txt

0.5.0 (2026-10-26): sections for 0.3.0 (duel --check and --preview on the shipped example), 0.4.0 (spritecam on a
small registry, sprite on a scene built with bpy, crowd --passes depth,mist, crowd --scatter, inspect --topology,
check's winding rule, convert --fix-winding) and 0.5.0 (framecam, a refused framecam, scene on a scene built with
pw_scene's sweep and ribbon, crowd side B options, a two-figure clash with --gap and --far, texture --delight, the
colours of a crowd mask frame). Test meshes for topology are written with the release's own pw.write_glb.
0.2.1 (2026-10-17): printable on the park runs without --hollow again (the 0.2.0 regression is fixed); the
--hollow run is kept as its own section. 0.2.0 additions (2026-10-17): check's wall thickness, printable's hollow-shell fill, convert --level and --tilt-deg,
place with roof shapes and building parts, crowd --preview, turnaround, mark, lineup --preview, match, manifest
--review, bpy options after the script name. The test meshes are binary STLs written here (prisms in millimetres
or metres), so the program needs nothing from the repository.

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

VERSION = sys.argv[1] if len(sys.argv) > 1 else "0.5.0"
WORK = tempfile.mkdtemp(prefix="pwwiki_")
PLUGIN = os.path.join(WORK, "plugin")
url = "https://github.com/m4bwav/polywright/releases/download/v%s/polywright-%s.zip" % (VERSION, VERSION)
zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url, timeout=120).read())).extractall(PLUGIN)
PW = os.path.join(PLUGIN, "skills", "polywright", "scripts", "pw.py")
RUN = os.path.join(WORK, "run")
os.makedirs(RUN)


def mask(text, keep_seconds=False):
    """keep_seconds: duel prints the clip's length as "seconds" (frames / fps), not a timing."""
    for w in (RUN, WORK):
        for form in (w, w.replace("\\", "\\\\"), w.replace("\\", "/")):
            text = text.replace(form + "\\\\", "").replace(form + "\\", "").replace(form + "/", "").replace(form, "<work>")
    text = re.sub(r'"render_seconds": [0-9.]+' if keep_seconds else r'"(render_)?seconds": [0-9.]+',
                  lambda m: '"%sseconds": "<s>"' % ("render_" if keep_seconds or m.group(1) else ""), text)
    text = re.sub(r'"path": "[^"]*blender(\.exe)?"', '"path": "<blender>"', text, flags=re.I)
    return text.rstrip()


def show(label, value):
    print("## " + label)
    print(value)
    print()


def snippet(label, text, keep_seconds=False):
    """Run a page's shell block line by line, as the page shows it, in the scratch run folder."""
    out = []
    for line in text.strip().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        args = shlex.split(line)
        if args[:2] == ["python", "pw.py"]:
            args = [sys.executable, PW] + args[2:]
        p = subprocess.run(args, cwd=RUN, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out.append(mask(p.stdout, keep_seconds))
        if p.stderr.strip():
            out.append("[stderr] " + mask(p.stderr, keep_seconds))
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


def prisms_stl(name, prisms, tilt_deg=0.0):
    """Binary STL of closed prisms: each (ring of (x, y), z0, z1), ring counter-clockwise and convex.
    tilt_deg rotates everything about X (y toward z), as a leaning image-to-3D model."""
    import math
    c, s = math.cos(math.radians(tilt_deg)), math.sin(math.radians(tilt_deg))
    tris = []
    for ring, z0, z1 in prisms:
        n = len(ring)
        lo = [(x, y, z0) for x, y in ring]
        hi = [(x, y, z1) for x, y in ring]
        for i in range(1, n - 1):
            tris.append((lo[0], lo[i + 1], lo[i]))
            tris.append((hi[0], hi[i], hi[i + 1]))
        for i in range(n):
            j = (i + 1) % n
            tris.append((lo[i], lo[j], hi[j]))
            tris.append((lo[i], hi[j], hi[i]))
    rot = [tuple((x, y * c - z * s, y * s + z * c) for x, y, z in t) for t in tris]
    path = os.path.join(RUN, name)
    os.makedirs(os.path.dirname(path) or RUN, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"wiki fixture".ljust(80, b" ") + struct.pack("<I", len(rot)))
        for t in rot:
            f.write(struct.pack("<12fH", 0, 0, 0, *[v for p in t for v in p], 0))


def box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


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
# 0.2.0's default hollow-shell fill broke this open terrain sheet (found by this program); 0.2.1 fixed it, so the
# page shows the default run again, and the --hollow run (which must give the same solid) on Versions and upgrading.
snippet("printable", """
python pw.py printable park/roblox.glb park/solid.stl --size-mm 60 --wall-mm 1.2
python pw.py check park/solid.stl --target print-fdm
""")
snippet("printable terrain --hollow", """
python pw.py printable park/roblox.glb park/solid-hollow.stl --size-mm 60 --wall-mm 1.2 --hollow
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

# =============== 0.2.0 ===============

# ---- check: wall thickness (Blender found). A 20 mm block, then the block with a 0.5 mm fin beside it.
prisms_stl("block.stl", [(box(0, 0, 20, 20), 0, 20)])
prisms_stl("fin.stl", [(box(0, 0, 20, 20), 0, 20), (box(30, 0, 50, 0.5), 0, 20)])
snippet("check thickness pass", """
python pw.py check block.stl --target print-fdm
""")
snippet("check thickness warn", """
python pw.py check fin.stl --target print-fdm
""")
snippet("check no-thickness", """
python pw.py check fin.stl --target print-fdm --no-thickness
""")

# ---- printable: a hollow shell (0.3 mm walls, air inside, a 0.6 mm slot in the lid) comes out filled
W = 0.3
prisms_stl("shell.stl", [(box(0, 0, 20, 20), 0, W), (box(0, 0, 9.7, 20), 20 - W, 20), (box(10.3, 0, 20, 20), 20 - W, 20),
                         (box(0, 0, W, 20), 0, 20), (box(20 - W, 0, 20, 20), 0, 20),
                         (box(0, 0, 20, W), 0, 20), (box(0, 20 - W, 20, 20), 0, 20)])
snippet("printable hollow shell", """
python pw.py printable shell.stl shell-filled.stl --size-mm 20 --base-cut-mm 0 --no-planar --voxel-mm 0.1
python pw.py printable shell.stl shell-hollow.stl --size-mm 20 --base-cut-mm 0 --no-planar --voxel-mm 0.1 --hollow
""")

# ---- convert --level: a 1 x 1 x 2 m block leaning 20 degrees about X (Pixal3D output in a raised camera's frame)
prisms_stl("leaning.stl", [(box(0, 0, 1, 1), 0, 2)], tilt_deg=20)
snippet("convert level", """
python pw.py inspect leaning.stl --fast
python pw.py convert leaning.stl level.glb --level --ground
python pw.py convert leaning.stl given.glb --tilt-deg -20
""")

# ---- place: roofs and building parts (Simple 3D Buildings), on the invented extract plus four buildings
TOWN = json.loads(json.dumps(OSM))
nid = [200]


def ring_nodes(lat0, lon0, lat1, lon1):
    ids = []
    for la, lo in ((lat0, lon0), (lat0, lon1), (lat1, lon1), (lat1, lon0)):
        nid[0] += 1
        TOWN["elements"].append({"type": "node", "id": nid[0], "lat": la, "lon": lo})
        ids.append(nid[0])
    return ids + ids[:1]


for wid, (bb, tags) in enumerate([
        ((40.00075, -74.9992, 40.00085, -74.99902), {"building": "house", "height": "9", "roof:shape": "gabled", "roof:height": "3"}),
        ((40.0006, -74.9998, 40.0007, -74.99962), {"building": "house", "building:levels": "2", "roof:shape": "hipped", "roof:levels": "1"}),
        ((40.0002, -74.9998, 40.0003, -74.99968), {"building": "yes", "roof:shape": "pyramidal"}),
        ((40.0002, -74.9993, 40.0003, -74.9990), {"building": "church", "height": "10"}),
        ((40.0002, -74.9993, 40.0003, -74.99915), {"building:part": "yes", "height": "10", "roof:shape": "gabled"}),
        ((40.0002, -74.99915, 40.0003, -74.9990), {"building:part": "yes", "min_height": "4", "height": "18", "roof:shape": "pyramidal", "roof:height": "6"})],
        start=200):
    TOWN["elements"].append({"type": "way", "id": wid, "nodes": ring_nodes(*bb), "tags": tags})
write("town/data/osm.json", json.dumps(TOWN))
snippet("place roofs", """
python pw.py place --bbox 40.0000,-75.0000,40.0010,-74.9987 --dem flat --res 2 --out town --print-mm 60
""")

# ---- crowd: an army blockout preview (first, middle and last frame) at a small size
snippet("crowd preview", """
python pw.py crowd --out crowd --size 320x192 --frames 17 --ranks 2 --cols 4 --action clash --preview --pose-min-px 10
""")
snippet("crowd bad size", """
python pw.py crowd --out crowd2 --size 830x480 --frames 80
""")

# ---- figures for video: a box figure (0.3 x 0.2 x 0.8 m body, 0.2 m head on top, face toward -Y)
prisms_stl("figure.stl", [(box(-0.15, -0.1, 0.15, 0.1), 0, 0.8), (box(-0.1, -0.1, 0.1, 0.1), 0.8, 1.0)])
snippet("turnaround", """
python pw.py turnaround figure.stl --out turn --views front,3q,back --size 96x144 --samples 2 --height-m 0.13
""")
snippet("turnaround unknown view", """
python pw.py turnaround figure.stl --out turn2 --views top
""")
snippet("mark", """
python pw.py mark figure.stl --out marked.glb --text 2 --colour 0.8,0.1,0.2 --height-m 0.13
""")
LAYOUT = """{
 "size": [192, 112],
 "lens": 35,
 "cam": [0, -0.6, 0.07],
 "aim": [0, 0, 0.065],
 "backdrop_m": 0.6,
 "figures": [
  {"name": "b1", "file": "marked.glb", "at": [0.12, 0], "face": "-60", "team": "b"},
  {"name": "a1", "file": "marked.glb", "at": [-0.12, 0], "face": "60", "team": "a"}
 ]
}
"""
write("layout.json", LAYOUT)
show("layout.json (file)", open(os.path.join(RUN, "layout.json"), encoding="utf-8").read().rstrip())
snippet("lineup", """
python pw.py lineup --layout layout.json --out lineup --preview
""")

# ---- match: a 1 m spear along +X rendered from a picture's camera and pasted into it
prisms_stl("spear.stl", [(box(0, -0.015, 1.0, 0.015), -0.015, 0.015)])
png("street.png", 320, 192)
snippet("match", """
python pw.py match spear.stl --out spear.png --still street.png --anchor-px 120,120 --aim-px 260,80 --aim-local=1,0,0 --depth 2
""")

# ---- manifest --review
snippet("manifest review", """
python pw.py new toy --name "Toy figure" --kind real --route generate --targets video-blockout
python pw.py manifest toy --review turn/sheet.png --verdict "good: front, three-quarter and back read"
""")
with open(os.path.join(RUN, "toy", "manifest.json"), encoding="utf-8") as f:
    show("manifest review (reviews)", mask(json.dumps({"reviews": json.load(f).get("reviews")}, indent=1)))

# ---- bpy: pw.py's options after the script name (0.2.0)
snippet("bpy options after script", """
python pw.py bpy hello_bpy.py --timeout 120 -- 2.5
""")

# =============== 0.3.0 ===============

# ---- duel: the example that ships in skills/polywright/examples (duel.json plus its room script)
for n in ("duel.json", "duel_room.py"):
    shutil.copy(os.path.join(PLUGIN, "skills", "polywright", "examples", n), os.path.join(RUN, n))
snippet("duel check", """
python pw.py duel duel.json --check
""", keep_seconds=True)
snippet("duel preview", """
python pw.py duel duel.json --preview --out duel
""", keep_seconds=True)

# =============== 0.4.0 ===============

sys.path.insert(0, os.path.dirname(PW))
import pw as released  # the release's own writers, for test meshes only

# ---- inspect --topology, check's winding rule, convert --fix-winding: a 1 m box with one triangle wound backwards
m = released.Mesh("box", (1, 1, 1))
m.v, m.f = released.prism([(0, 0), (1, 0), (1, 1), (0, 1)], 0, 1)
m.f[3] = tuple(reversed(m.f[3]))
released.write_glb(os.path.join(RUN, "flipped.glb"), [m])
snippet("inspect topology", """
python pw.py inspect flipped.glb --topology
""")
snippet("check winding", """
python pw.py check flipped.glb --target web-threejs
""")
snippet("convert fix-winding", """
python pw.py convert flipped.glb fixed.glb --fix-winding
python pw.py inspect fixed.glb --topology
""")

# ---- spritecam: a building registry with five 2x2 sprites drawn by one camera (to 0.8 px), one skewed misfit,
# and one 3x3 building
REGISTRY = """{"buildings": [
 {"buildingId": "sawmill", "size": {"x": 2, "y": 2}, "groundBase": {"front": {"x": 48, "y": 66}, "left": {"x": 3.3, "y": 45.0}, "right": {"x": 87.2, "y": 41.0}}},
 {"buildingId": "granary", "size": {"x": 2, "y": 2}, "groundBase": {"front": {"x": 48, "y": 66}, "left": {"x": 2.8, "y": 45.0}, "right": {"x": 88.6, "y": 41.7}}},
 {"buildingId": "smithy", "size": {"x": 2, "y": 2}, "groundBase": {"front": {"x": 48, "y": 66}, "left": {"x": 4.8, "y": 44.1}, "right": {"x": 88.2, "y": 41.1}}},
 {"buildingId": "bakery", "size": {"x": 2, "y": 2}, "groundBase": {"front": {"x": 48, "y": 66}, "left": {"x": 3.0, "y": 44.2}, "right": {"x": 87.9, "y": 41.9}}},
 {"buildingId": "well", "size": {"x": 2, "y": 2}, "groundBase": {"front": {"x": 48, "y": 66}, "left": {"x": 3.0, "y": 43.5}, "right": {"x": 88.0, "y": 41.2}}},
 {"buildingId": "tower", "size": {"x": 2, "y": 2}, "groundBase": {"front": {"x": 50, "y": 90}, "left": {"x": 0, "y": 89}, "right": {"x": 60, "y": 20}}},
 {"buildingId": "hall", "size": {"x": 3, "y": 3}, "groundBase": {"front": {"x": 48, "y": 66}, "left": {"x": -18.9, "y": 33.2}, "right": {"x": 108.2, "y": 29.6}}}
]}
"""
write("registry.json", REGISTRY)
show("registry.json (file)", REGISTRY.rstrip())
snippet("spritecam", """
python pw.py spritecam registry.json --out camera.json --tiles 2 --tile-px 48 --tile-m 5 --like sawmill
""")
show("camera.json (file)", mask(open(os.path.join(RUN, "camera.json"), encoding="utf-8").read()))

# ---- sprite: a small mill (a box building and a six-armed wheel on a pivot) built with bpy, through that camera
SAWMILL = """
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix
out = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def box(name, lo, hi, parent=None, m=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=[b - a for a, b in zip(lo, hi)], verts=bm.verts)
    bmesh.ops.translate(bm, vec=[(a + b) / 2 for a, b in zip(lo, hi)], verts=bm.verts)
    if m is not None:
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    if parent: ob.parent = parent
    return ob
box("bldg_box", (2, 4, 0), (8, 9, 4))
piv = bpy.data.objects.new("pivot_wheel", None); piv.location = (5, 2, 1.6); sc.collection.objects.link(piv)
for k in range(6):
    box("wheel_arm_%d" % k, (0, -0.3, -0.1), (1.5, 0.3, 0.1), piv, Matrix.Rotation(2 * math.pi * k / 6, 4, "Y"))
sc["sprite_parts"] = json.dumps({"wheel": "wheel_", "building": "bldg_"})
sc["footprint_m"] = json.dumps([10, 10])
sc["rings"] = json.dumps({"wheel": {"centre": [5, 2, 1.6], "radius": 1.5, "axis": "Y", "arms": 6, "faces": [1.7, 2.3]}})
sc["loop"] = json.dumps([{"object": "pivot_wheel", "rotate_axis": "Y", "degrees": 60}])
bpy.ops.wm.save_as_mainfile(filepath=out)
"""
write("sawmill_scene.py", SAWMILL.lstrip())
show("sawmill_scene.py (file)", SAWMILL.strip())
snippet("sprite", """
python pw.py bpy sawmill_scene.py -- sawmill.blend
python pw.py sprite sawmill.blend --camera camera.json --out sprite --samples 2 --passes beauty,clay,depth,id --frames 2 --frame-passes id --no-line
""")
with open(os.path.join(RUN, "sprite", "sprite.json"), encoding="utf-8") as f:
    meta = json.load(f)
show("sprite.json groundBase", json.dumps({"groundBase": meta.get("groundBase")}, indent=1))
print("## sprite files")
print("\n".join(sorted(os.path.relpath(os.path.join(dp, n), os.path.join(RUN, "sprite")).replace("\\", "/")
                       for dp, _, ns in os.walk(os.path.join(RUN, "sprite")) for n in ns)))
print()

# ---- crowd: Mist beside depth, and reserves behind the far side (camera behind side A)
snippet("crowd mist", """
python pw.py crowd --out mist --size 320x192 --frames 17 --ranks 2 --cols 4 --passes depth,mist --preview
""")
print("## crowd mist files")
print("mist/: " + ", ".join(sorted(os.listdir(os.path.join(RUN, "mist", "mist")))))
with open(os.path.join(RUN, "mist", "mist", "0001.png"), "rb") as f:
    head = f.read(26)
print("mist/0001.png bit depth %d, colour type %d (0 = grey)" % (head[24], head[25]))
print()
snippet("crowd scatter", """
python pw.py crowd --out reserves --size 320x192 --frames 17 --ranks 2 --cols 6 --view behind --passes mask --scatter 60 --preview
""")

# =============== 0.5.0 ===============

# ---- framecam: a 2 m hero right of centre, a far landmark in frame, the UI's text bands clear
PROBLEM = """{
 "size": [1920, 1080],
 "points": {"hero": [0, 0, 2], "hero_top": [0, 0, 4], "hero_bottom": [0, 0, 0], "far": [30, 20, 0]},
 "boxes": {"hero": {"x": [0.6, 0.75], "y": [0.4, 0.6]}},
 "keep_in_frame": ["far", "hero_top", "hero_bottom"],
 "bands": [{"x": [0.25, 0.75], "y": [0, 0.15]}, {"x": [0.25, 0.75], "y": [0.85, 1]}],
 "keep_out_of_bands": ["hero_top", "hero_bottom"],
 "size_measure": ["hero_top", "hero_bottom"],
 "search": {"pos": [[-8, 8, 2], [-30, -10, 2], [1, 5, 1]], "target": [[-4, 4, 1], 0, 2], "lens_mm": [20, 60, 5]}
}
"""
write("problem.json", PROBLEM)
show("problem.json (file)", PROBLEM.rstrip())
snippet("framecam", """
python pw.py framecam problem.json --out cameras.json --top 3
""")
write("aimed.json", PROBLEM.replace('"target": [[-4, 4, 1], 0, 2]', '"target": [0, 0, 2]'))
snippet("framecam never met", """
python pw.py framecam aimed.json
""")

# ---- scene: ground, a house, a wheel, a river bank (sweep) and a road (ribbon), built with pw_scene's helpers
BUILD = """
import bpy, bmesh, json, os, sys
from mathutils import Matrix
blend, scripts = sys.argv[sys.argv.index("--") + 1:][:2]
sys.path.insert(0, os.path.abspath(scripts))
from pw_scene import sweep, ribbon
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def mesh(name, build):
    bm = bmesh.new(); build(bm)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob
mesh("ground_plane", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60))
def house(bm):
    bmesh.ops.create_cube(bm, size=4.0)
    bmesh.ops.translate(bm, vec=(-3, 6, 2), verts=bm.verts)
mesh("house_body", house)
def wheel(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=1.5, radius2=1.5, depth=0.4)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(1.5708, 3, "X"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(3, 4, 1.8), verts=bm.verts)
mesh("wheel_disc", wheel)
sweep("bank_south", [(-20, -2), (0, -3), (20, -2)], [(-1.5, 0), (0, 0.8), (1.5, 0)])
ribbon("road_track", [(-20, 12), (20, 12)], 1.5, lambda t, p: 0.02)
sc["scene_parts"] = json.dumps({"house": "house_", "wheel": "wheel_", "ground": ["ground_", "bank_", "road_"]})
sc["rings"] = json.dumps({"wheel": {"centre": [3, 4, 1.8], "radius": 1.5, "axis": "Y", "faces": [3.8, 4.2], "arms": 0, "hub_r": 0.3}})
sc["scene_points"] = json.dumps({"door": [-3, 4, 1], "road": [[-10, 12, 0], [10, 12, 0]]})
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
"""
write("build_scene.py", BUILD.lstrip())
show("build_scene.py (file)", BUILD.strip())
SCENECAMS = """{"cameras": {"low": {"pos": [6, -14, 3], "target": [0, 4, 2], "lens_mm": 30}}}
"""
write("scene_cameras.json", SCENECAMS)
show("scene_cameras.json (file)", SCENECAMS.rstrip())
snippet("scene", """
python pw.py bpy build_scene.py -- scene.blend ../plugin/skills/polywright/scripts
python pw.py scene scene.blend --cameras scene_cameras.json --camera low --out scene --size 192x108 --samples 2 --sky 90,140,210:220,230,240
""")
with open(os.path.join(RUN, "scene", "scene.json"), encoding="utf-8") as f:
    meta = json.load(f)
for ring in meta.get("rings", {}).values():  # 72 points each: the page shows the count and the first point
    for k in ("rim_px", "hub_px"):
        if isinstance(ring.get(k), list):
            ring[k] = "%d points, first %s" % (len(ring[k]), ring[k][0])
show("scene.json (abridged)", mask(json.dumps(meta, indent=1)))
snippet("scene unknown camera", """
python pw.py scene scene.blend --cameras scene_cameras.json --camera close --out scene2
""")

# ---- crowd: a loose horde of shorter bare figures against a drilled line
snippet("crowd side b", """
python pw.py crowd --out horde --size 320x192 --frames 17 --ranks 2 --cols 5 --action charge --jitter-b 1.5 --kit-b "" --scale-b 0.8 --stagger-b 0.4 --passes depth,mask --preview
""")

# ---- crowd: a two-figure clash needs a smaller gap and a far plane past the ground in view
snippet("crowd two figures", """
python pw.py crowd --out pair --size 320x192 --frames 17 --ranks 1 --cols 1 --action clash --gap 5 --far 40 --passes depth,mist --preview
""")

# ---- shipped in the 0.5.0 zip although the CHANGELOG lists it under Unreleased: texture --delight, exact mask colours
W2, H2 = 128, 64
raw = b"".join(b"\x00" + bytes(v for x in range(W2) for v in [int((0.25 + 0.75 * x / (W2 - 1)) * (200 if (x // 16 + y // 16) % 2 else 110))] * 3) for y in range(H2))


def _chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)


with open(os.path.join(RUN, "lit.png"), "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", W2, H2, 8, 2, 0, 0, 0)) + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b""))
snippet("texture delight", """
python pw.py texture lit.png --out lit --delight
""")
print("## crowd mask colours")
with open(os.path.join(RUN, "crowd", "mask", "0001.png"), "rb") as f:
    w_, h_, ch_, px_ = released.png_decode(f.read())
cols = {}
for i in range(0, len(px_), ch_):
    cols[tuple(px_[i:i + 3])] = cols.get(tuple(px_[i:i + 3]), 0) + 1
print("crowd/mask/0001.png: %d colours: %s" % (len(cols), ", ".join("%s x%d" % (list(k), v) for k, v in sorted(cols.items(), key=lambda kv: -kv[1])[:6])))
print()

shutil.rmtree(WORK, ignore_errors=True)
