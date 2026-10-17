"""Tests for skills/polywright/scripts/pw.py (stdlib unittest, Python 3.9+).

Run from the repository root: python tests/test_pw.py
Pure-Python parts (geometry, file formats, manifest, check, an offline `place`) always run. Tests that need
Blender skip when `pw.py doctor` finds none; set POLYWRIGHT_BLENDER to point at one.
"""
import contextlib
import io
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "polywright", "scripts"))
import pw  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")


def run(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pw.main(list(argv))
    return code, json.loads(buf.getvalue())


def closed_and_outward(verts, faces):
    """Every directed edge appears once and its reverse once; signed volume positive."""
    seen = {}
    for f in faces:
        for i in range(3):
            e = (f[i], f[(i + 1) % 3])
            seen[e] = seen.get(e, 0) + 1
    for (a, b), n in seen.items():
        if n != 1 or seen.get((b, a)) != 1:
            return False, "edge %s->%s used %d times, reverse %s" % (a, b, n, seen.get((b, a)))
    vol = 0.0
    for a, b, c in faces:
        (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = verts[a], verts[b], verts[c]
        vol += x1 * (y2 * z3 - z2 * y3) - y1 * (x2 * z3 - z2 * x3) + z1 * (x2 * y3 - y2 * x3)
    return vol > 0, "volume %.6f" % (vol / 6)


def make_png(w, h, rgb_rows, filt=1):
    raw = b""
    for row in rgb_rows:
        line = bytes(row)
        if filt == 1:  # Sub filter, to exercise un-filtering
            line = bytes((line[i] - (line[i - 3] if i >= 3 else 0)) & 255 for i in range(len(line)))
        raw += bytes([filt]) + line

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def make_tiff(w, h, vals):
    data = struct.pack("<%df" % len(vals), *vals)
    entries = [(256, 3, 1, w), (257, 3, 1, h), (258, 3, 1, 32), (259, 3, 1, 1), (273, 4, 1, 0), (278, 3, 1, h), (279, 4, 1, len(data)), (339, 3, 1, 3)]
    ifd_off = 8
    ifd = struct.pack("<H", len(entries))
    data_off = ifd_off + 2 + 12 * len(entries) + 4
    for tag, typ, n, v in entries:
        if tag == 273:
            v = data_off
        ifd += struct.pack("<HHI", tag, typ, n) + (struct.pack("<HH", v, 0) if typ == 3 else struct.pack("<I", v))
    return b"II*\x00" + struct.pack("<I", ifd_off) + ifd + b"\x00\x00\x00\x00" + data


class Geometry(unittest.TestCase):
    def test_earclip_l_shape_covers_the_area(self):
        ring = [(0, 0), (4, 0), (4, 1), (1, 1), (1, 3), (0, 3)]
        tris = pw.earclip(ring)
        self.assertEqual(len(tris), len(ring) - 2)
        area = sum(abs(pw.poly_area([ring[a], ring[b], ring[c]])) for a, b, c in tris)
        self.assertAlmostEqual(area, abs(pw.poly_area(ring)))

    def test_prism_is_closed_and_outward_for_both_windings(self):
        for ring in ([(0, 0), (2, 0), (2, 1), (0, 1)], [(0, 0), (0, 1), (2, 1), (2, 0)]):
            if pw.poly_area(ring) < 0:
                ring = ring[::-1]
            v, f = pw.prism(ring, 0, 3)
            ok, why = closed_and_outward(v, f)
            self.assertTrue(ok, why)

    def test_terrain_block_is_closed_and_outward(self):
        nx, ny = 5, 4
        vgrid = [(c * 1.0, -r * 1.0, (c * r) % 3 * 0.2) for r in range(ny) for c in range(nx)]
        tile = pw.terrain_block(vgrid, nx, ny, 1.0, lambda z: 2 + z)
        ok, why = closed_and_outward(tile.v, tile.f)
        self.assertTrue(ok, why)

    def test_clip_ring_to_rectangle(self):
        r = pw.clip_ring([(-2, -2), (2, -2), (2, 2), (-2, 2)], 1, 1)
        self.assertAlmostEqual(abs(pw.poly_area(r)), 4.0)
        self.assertEqual(pw.clip_ring([(5, 5), (6, 5), (6, 6)], 1, 1), [])

    def test_clip_line_splits_at_the_edges(self):
        pieces = pw.clip_line([(-3, 0), (3, 0), (3, 5), (0, 0.5)], 1, 1)
        self.assertEqual(len(pieces), 2)
        self.assertAlmostEqual(pieces[0][0][0], -1)
        self.assertAlmostEqual(pieces[0][-1][0], 1)

    def test_stitch_rings_joins_split_members(self):
        rings = pw.stitch_rings([[1, 2, 3], [5, 4, 3], [5, 6, 1], [7, 8]])
        self.assertEqual(len(rings), 1)
        self.assertEqual(rings[0][0], rings[0][-1])
        self.assertEqual(sorted(set(rings[0])), [1, 2, 3, 4, 5, 6])

    def test_clean_ring_drops_repeats_and_collinear_points(self):
        r = pw.clean_ring([(0, 0), (0, 0), (1, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
        self.assertEqual(len(r), 4)

    def test_ribbon_closed_slab(self):
        v, f = pw.ribbon([(0, 0), (5, 0), (8, 3)], 0.5, lambda x, y: 0.0, 0.4, closed_depth=1.0)
        ok, why = closed_and_outward(v, f)
        self.assertTrue(ok, why)


class Formats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwtest_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_png_decode_with_sub_filter(self):
        rows = [[(x * 10 + y) % 256 for x in range(6) for _ in range(3)] for y in range(4)]
        w, h, ch, px = pw.png_decode(make_png(6, 4, rows))
        self.assertEqual((w, h, ch), (6, 4, 3))
        self.assertEqual(list(px[:18]), rows[0])
        self.assertEqual(list(px[-18:]), rows[3])

    def test_tiff_f32_strips(self):
        vals = [float(i) / 4 for i in range(12)]
        w, h, got = pw.read_tiff_f32(make_tiff(4, 3, vals))
        self.assertEqual((w, h), (4, 3))
        self.assertEqual(got, vals)

    def test_glb_and_stl_round_trip(self):
        m = pw.Mesh("box", (1, 0, 0))
        m.v, m.f = pw.prism([(0, 0), (2, 0), (2, 1), (0, 1)], 0, 3)
        g = os.path.join(self.tmp, "b.glb")
        pw.write_glb(g, [m])
        q = pw.glb_quick(g)
        self.assertEqual(q["tris"], 12)
        self.assertEqual([round(x, 4) for x in q["dims_mesh_space"]], [2, 3, 1])  # ENU -> glTF: y is up
        s = os.path.join(self.tmp, "b.stl")
        self.assertEqual(pw.write_stl(s, [m]), 12)
        self.assertEqual([round(x, 4) for x in pw.stl_quick(s)["dims"]], [2, 1, 3])

    def test_grid_bilinear(self):
        g = pw.Grid(0, 0, 1, 1, 2, 2, [0.0, 2.0, 0.0, 2.0])  # row 0 north
        self.assertAlmostEqual(g.at(0.5, 0.5), 1.0)
        self.assertAlmostEqual(g.at(0.5, 1.0), 2.0, places=2)


class UiToApi(unittest.TestCase):
    INFO = {
        "LoadImage": {"input": {"required": {"image": [["a.png"], {"image_upload": True}]}}, "input_order": {"required": ["image"]}},
        "KSampler": {"input": {"required": {"model": ["MODEL", {}], "seed": ["INT", {"control_after_generate": True}], "steps": ["INT", {}],
                                            "latent_image": ["LATENT", {}]}}, "input_order": {"required": ["model", "seed", "steps", "latent_image"]}},
        "Remesh": {"input": {"required": {"mesh": ["MESH", {}], "mode": ["COMFY_DYNAMICCOMBO_V3", {"options": [
            {"key": "udf", "inputs": {"required": {"qef": ["BOOLEAN", {}]}}}]}], "smooth": ["INT", {"default": 2}]}},
                   "input_order": {"required": ["mesh", "mode", "smooth"]}},
        "Blur": {"input": {"required": {"image": ["IMAGE", {}]}}, "input_order": {"required": ["image"]}},
        "PreviewImage": {"input": {"required": {"images": ["IMAGE", {}]}}, "input_order": {"required": ["images"]}},
    }

    def test_widgets_links_bypass_and_defaults(self):
        ui = {"nodes": [
            {"id": 1, "type": "LoadImage", "mode": 0, "widgets_values": ["fountain.png", "image"], "outputs": [{"type": "IMAGE"}]},
            {"id": 2, "type": "Blur", "mode": 4, "inputs": [{"name": "image", "type": "IMAGE", "link": 10}], "outputs": [{"type": "IMAGE"}]},
            {"id": 3, "type": "PreviewImage", "mode": 0, "inputs": [{"name": "images", "type": "IMAGE", "link": 11}]},
            {"id": 4, "type": "KSampler", "mode": 0, "widgets_values": [42, "fixed", 12], "inputs": [{"name": "model", "link": None}]},
            {"id": 5, "type": "Remesh", "mode": 0, "widgets_values": ["udf", True], "inputs": [{"name": "mesh", "link": None}]},
            {"id": 6, "type": "Note", "mode": 0, "widgets_values": ["hello"]}],
            "links": [[10, 1, 0, 2, 0, "IMAGE"], [11, 2, 0, 3, 0, "IMAGE"]]}
        api = pw.ui_to_api(ui, self.INFO)
        self.assertEqual(api["1"]["inputs"], {"image": "fountain.png"})
        self.assertNotIn("2", api)                               # bypassed
        self.assertNotIn("3", api)                               # an unused preview is dropped
        self.assertNotIn("6", api)                               # notes never reach the server
        self.assertEqual(api["4"]["inputs"], {"seed": 42, "steps": 12})  # "fixed" is the seed's control value
        self.assertEqual(api["5"]["inputs"], {"mode": "udf", "mode.qef": True, "smooth": 2})  # default filled in

    def test_bypass_passes_the_link_through(self):
        ui = {"nodes": [
            {"id": 1, "type": "LoadImage", "mode": 0, "widgets_values": ["a.png", "image"], "outputs": [{"type": "IMAGE"}]},
            {"id": 2, "type": "Blur", "mode": 4, "inputs": [{"name": "image", "type": "IMAGE", "link": 10}], "outputs": [{"type": "IMAGE"}]},
            {"id": 3, "type": "Blur", "mode": 0, "inputs": [{"name": "image", "type": "IMAGE", "link": 11}], "outputs": [{"type": "IMAGE"}]}],
            "links": [[10, 1, 0, 2, 0, "IMAGE"], [11, 2, 0, 3, 0, "IMAGE"]]}
        self.assertEqual(pw.ui_to_api(ui, self.INFO)["3"]["inputs"], {"image": ["1", 0]})


class Commands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwtest_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_check_lists_targets(self):
        code, out = run("check", "--list")
        self.assertEqual(code, 0)
        for t in ("game-roblox", "game-unity", "print-fdm", "web-threejs", "ar-usdz", "video-blockout"):
            self.assertIn(t, out["targets"])

    def test_new_and_manifest(self):
        d = os.path.join(self.tmp, "asset")
        code, out = run("new", d, "--name", "Fountain", "--kind", "imagined", "--route", "generate", "--targets", "game-roblox,print-fdm")
        self.assertEqual(code, 0, out)
        for sub in ("refs", "work", "out", "renders"):
            self.assertTrue(os.path.isdir(os.path.join(d, sub)))
        m = pw.Mesh("box", (1, 0, 0))
        m.v, m.f = pw.prism([(0, 0), (1, 0), (1, 1), (0, 1)], 0, 1)
        stl = os.path.join(d, "out", "box.stl")
        pw.write_stl(stl, [m])
        code, out = run("manifest", d, "--add-output", stl, "--target", "print-fdm")
        self.assertEqual(code, 0, out)
        code, out = run("manifest", d, "--add-source", "https://example.org/ref.png", "--what", "reference")
        self.assertEqual(code, 1)  # a source without a licence is a problem
        self.assertTrue(any("licence" in p for p in out["problems"]))
        with open(stl, "ab") as f:
            f.write(b"x")
        code, out = run("manifest", d, "--validate")
        self.assertTrue(any("changed" in p for p in out["problems"]))

    def test_manifest_output_relative_to_the_asset_and_reviews(self):
        d = os.path.join(self.tmp, "fig")
        run("new", d, "--name", "Figure", "--kind", "real", "--route", "generate", "--targets", "video-blockout")
        m = pw.Mesh("box", (1, 0, 0))
        m.v, m.f = pw.prism([(0, 0), (1, 0), (1, 1), (0, 1)], 0, 1)
        pw.write_stl(os.path.join(d, "out", "fig.stl"), [m])
        cwd = os.getcwd()
        try:
            os.chdir(self.tmp)  # out/fig.stl does not exist here, only inside the asset folder
            code, out = run("manifest", d, "--add-output", "out/fig.stl", "--target", "video-blockout",
                            "--review", "renders/turnaround/sheet.png", "--verdict", "good: markings readable")
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 0, out)
        with open(os.path.join(d, "manifest.json")) as f:
            man = json.load(f)
        self.assertEqual(man["outputs"][0]["path"], "out/fig.stl")
        self.assertEqual(man["reviews"][-1]["verdict"], "good: markings readable")
        self.assertEqual(man["reviews"][-1]["render"], "renders/turnaround/sheet.png")

    def test_mark_rejects_a_bad_colour(self):
        code, out = run("mark", os.path.join(self.tmp, "none.glb"), "--out", os.path.join(self.tmp, "x.glb"), "--colour", "1,0")
        self.assertEqual(code, 2)
        self.assertIn("3 comma-separated", out["error"])

    def test_bpy_options_after_script(self):
        import argparse
        a = argparse.Namespace(script="s.py", blend=None, timeout=1800, lines=40,
                               args=["--blend", "x.blend", "--timeout=60", "--", "--out", "v"])
        pw.split_bpy_args(a)
        self.assertEqual((a.blend, a.timeout, a.args), ("x.blend", 60, ["--out", "v"]))
        a = argparse.Namespace(script="s.py", blend="y.blend", timeout=1800, lines=40, args=["--", "--blend", "z"])
        pw.split_bpy_args(a)  # after `--` everything belongs to the script
        self.assertEqual((a.blend, a.args), ("y.blend", ["--blend", "z"]))

    def test_pose_leaves_out_hidden_joints(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")
        pts = [[50, 20], [50, 40], [35, 42], [30, 60], [28, 80], [65, 42], [70, 60], [72, 80], [42, 90], [42, 120],
               [42, 150], [58, 90], [58, 120], [58, 150], [-1, -1], [-1, -1], [44, 22], [56, 22]]
        pts[0] = [-1, -1]  # a figure seen from behind: no nose, no eyes
        jp = os.path.join(self.tmp, "joints.json")
        with open(jp, "w") as f:
            json.dump({"size": [100, 160], "frames": [{"frame": 1, "people": [[5.0, pts]]}]}, f)
        out = pw.draw_pose_frames(jp, os.path.join(self.tmp, "pose"))
        self.assertEqual(out, {"frames": 1, "skeletons": 1})
        im = Image.open(os.path.join(self.tmp, "pose", "0001.png"))
        self.assertEqual(im.getpixel((0, 0)), (0, 0, 0))  # no limb drawn to a hidden joint at (-1, -1)
        self.assertNotEqual(im.getpixel((50, 40)), (0, 0, 0))  # the neck is drawn
        self.assertEqual(im.getpixel((50, 25)), (0, 0, 0))  # nothing where a nose limb would run

    def test_roof_solids_are_closed_and_outward(self):
        ring = [(0, 0), (12, 0), (12, 6), (0, 6)]
        for shape in ("gabled", "hipped", "pyramidal", "skillion"):
            for direction in (None, 0, 90, 180, 270):
                v, f = pw.roof_solid(shape, ring, 5, 3, True, direction)
                ok, why = closed_and_outward(v, f)
                self.assertTrue(ok, "%s %s: %s" % (shape, direction, why))
                self.assertAlmostEqual(max(z for _, _, z in v), 8)
        v, f = pw.roof_solid("pyramidal", [(0, 0), (4, 0), (6, 3), (2, 5), (-1, 3)], 0, 2)  # convex: on the ring
        self.assertTrue(closed_and_outward(v, f)[0])
        self.assertEqual(len(v), 6)
        v, f = pw.roof_solid("hipped", [(0, 0), (5, 0), (5, 5), (0, 5)], 0, 2)  # square: a pyramid
        self.assertTrue(closed_and_outward(v, f)[0])
        # skillion: the low edge faces roof:direction (90 = east, +x)
        v, f = pw.roof_solid("skillion", ring, 0, 3, True, 90)
        self.assertEqual({round(x) for x, _, z in v if z > 0}, {0})

    def test_building_heights_follow_simple_3d_buildings(self):
        ring = [(0, 0), (10, 0), (10, 8), (0, 8)]
        top = lambda v: round(max(z for _, _, z in v), 3)
        v, f, info = pw.building_mesh(ring, 0, {"building": "yes", "height": "12", "roof:shape": "gabled", "roof:height": "4"})
        self.assertEqual((top(v), info["roof"]), (12, "gabled"))  # height includes the roof
        walls = [z for x, y, z in v if (x, y) == (0, 0)]
        self.assertIn(8, [round(z, 3) for z in walls])  # eaves at 12 - 4
        v, f, info = pw.building_mesh(ring, 0, {"building": "yes", "building:levels": "2", "roof:shape": "hipped", "roof:levels": "1"})
        self.assertEqual(top(v), round(2 * pw.LEVEL_M + 1 + pw.LEVEL_M, 3))  # roof levels sit on top
        v, f, info = pw.building_mesh(ring, 0, {"building:part": "yes", "height": "20", "min_height": "15"})
        self.assertEqual(round(min(z for _, _, z in v), 3), 15)  # a part above the ground
        v, f, info = pw.building_mesh(ring, 0, {"building:part": "yes", "height": "20", "min_height": "15"}, bottom=-1)
        self.assertEqual(round(min(z for _, _, z in v), 3), -1)  # prints stand it on the ground
        L = [(0, 0), (10, 0), (10, 3), (3, 3), (3, 10), (0, 10)]
        v, f, info = pw.building_mesh(L, 0, {"building": "yes", "roof:shape": "gabled"})
        self.assertTrue(info["roof"].startswith("flat"), info)  # an L footprint is far from its rectangle
        v, f, info = pw.building_mesh(ring, 0, {"building": "yes", "roof:shape": "dome"})
        self.assertEqual(info["roof"], "dome as pyramidal")

    def test_place_offline_from_fixture(self):
        out = os.path.join(self.tmp, "place")
        os.makedirs(os.path.join(out, "data"))
        shutil.copy(os.path.join(FIX, "osm-small.json"), os.path.join(out, "data", "osm.json"))
        code, res = run("place", "--bbox", "40.0000,-75.0000,40.0010,-74.9987", "--out", out, "--dem", "flat", "--res", "2",
                        "--print-mm", "60", "--no-union")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["counts"]["buildings"], 1)
        self.assertGreaterEqual(res["counts"]["trees"], 1)
        self.assertIn("park", res["counts"]["ground_cells"])
        self.assertTrue(os.path.isfile(res["scene"]))
        self.assertGreater(pw.glb_quick(res["scene"])["tris"], 100)
        self.assertTrue(os.path.isfile(res["print"]["parts_stl"]))
        self.assertTrue(any("OpenStreetMap" in c for c in res["credits"]))


@unittest.skipUnless(pw.backend(), "Blender not found")
class WithBlender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="pwtest_b_")
        a, b = pw.Mesh("a", (1, 0, 0)), pw.Mesh("b", (0, 1, 0))
        a.v, a.f = pw.prism([(0, 0), (2, 0), (2, 2), (0, 2)], 0, 1)
        b.v, b.f = pw.prism([(1, 1), (3, 1), (3, 3), (1, 3)], 0.5, 2)
        cls.glb = os.path.join(cls.tmp, "two.glb")
        pw.write_glb(cls.glb, [a, b])
        cls.stl = os.path.join(cls.tmp, "two.stl")
        pw.write_stl(cls.stl, [a, b])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_match_lands_the_aim_and_writes_paste_and_mask(self):
        rod = pw.Mesh("rod", (0.1, 0.1, 0.1))
        rod.v, rod.f = pw.prism([(0, -0.03), (2, -0.03), (2, 0.03), (0, 0.03)], -0.03, 0.03)
        stl = os.path.join(self.tmp, "rod.stl")
        pw.write_stl(stl, [rod])
        still = os.path.join(self.tmp, "still.png")
        with open(still, "wb") as f:
            f.write(make_png(320, 180, [[128, 128, 130] * 320] * 180))
        out = os.path.join(self.tmp, "m.png")
        code, res = run("match", stl, "--still", still, "--out", out, "--anchor-px", "100,120", "--aim-px", "220,90",
                        "--aim-local", "2,0,0", "--depth", "3", "--samples", "4", "--hide", "0,0,95,180")
        if code and "Pillow" in res.get("error", ""):
            self.skipTest("Pillow not installed")
        self.assertEqual(code, 0, res)
        self.assertAlmostEqual(res["aim_lands"][0], 220, delta=0.5)
        self.assertAlmostEqual(res["aim_lands"][1], 90, delta=0.5)
        self.assertAlmostEqual(res["anchor_lands"][0], 100, delta=0.5)
        for k in ("out", "paste", "mask"):
            self.assertTrue(os.path.isfile(res[k]), k)
        self.assertGreaterEqual(res["mask_bbox"][0], 95 - 10)  # the hidden box stays out of the mask

    def test_inspect(self):
        code, out = run("inspect", self.glb)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["tris"], 24)
        self.assertEqual(out["objects"], 2)
        self.assertTrue(out["watertight"])
        self.assertEqual([round(x, 3) for x in out["dims"]], [3, 3, 2])  # back in Blender's Z-up frame

    def test_union_makes_one_solid(self):
        dst = os.path.join(self.tmp, "u.stl")
        code, out = run("union", self.stl, dst)
        self.assertEqual(code, 0, out)
        self.assertTrue(out["watertight"])
        self.assertEqual(out["parts_in"], 2)
        code, info = run("inspect", dst)
        self.assertEqual(info["parts"], 1)

    def test_convert_scale_uv_and_check(self):
        dst = os.path.join(self.tmp, "c.glb")
        code, out = run("convert", self.glb, dst, "--size-m", "1.5", "--join", "--ground", "--uv")
        self.assertEqual(code, 0, out)
        self.assertAlmostEqual(max(out["dims"]), 1.5, places=3)
        code, chk = run("check", dst, "--target", "game-roblox", "--real-size-m", "1.5")
        self.assertEqual(chk["status"], "warn", chk)  # two materials: Roblox takes one per mesh
        self.assertEqual([r["rule"] for r in chk["results"] if r["status"] != "pass"], ["max_materials"])
        code, info = run("inspect", dst)
        self.assertTrue(info["watertight"], info)  # re-exported glTF splits vertices; topology welds them

    def test_convert_level_stands_a_leaning_model_up(self):
        # a 1 x 1 x 2 block leaning 20 degrees about X (an image-to-3D model in a raised camera's frame)
        box = pw.Mesh("leaning", (0.5, 0.5, 0.5))
        v, box.f = pw.prism([(0, 0), (1, 0), (1, 1), (0, 1)], 0, 2)
        c, s = math.cos(math.radians(20)), math.sin(math.radians(20))
        box.v = [(x, y * c - z * s, y * s + z * c) for x, y, z in v]
        src = os.path.join(self.tmp, "leaning.glb")
        pw.write_glb(src, [box])
        code, out = run("convert", src, os.path.join(self.tmp, "level.glb"), "--level", "--ground")
        self.assertEqual(code, 0, out)
        self.assertAlmostEqual(out["level"]["tilt_deg"], 20, delta=0.1)
        self.assertEqual(sorted(round(d, 3) for d in out["dims"]), [1, 1, 2])
        code, out = run("convert", src, os.path.join(self.tmp, "given.glb"), "--tilt-deg", "-20")
        self.assertEqual(sorted(round(d, 3) for d in out["dims"]), [1, 1, 2], out)

    def test_printable(self):
        dst = os.path.join(self.tmp, "p.stl")
        code, out = run("printable", self.glb, dst, "--size-mm", "40")
        self.assertEqual(code, 0, out)
        self.assertTrue(out["watertight"])
        self.assertAlmostEqual(max(out["dims_mm"]), 40, delta=0.8)

    def test_check_measures_wall_thickness(self):
        # a 20 mm block passes the 0.9 mm FDM wall rule; a 0.5 mm fin standing on it is found and located
        block, fin = pw.Mesh("block", (0.5, 0.5, 0.5)), pw.Mesh("fin", (0.5, 0.5, 0.5))
        block.v, block.f = pw.prism([(0, 0), (20, 0), (20, 20), (0, 20)], 0, 20)
        fin.v, fin.f = pw.prism([(30, 0), (50, 0), (50, 0.5), (30, 0.5)], 0, 20)
        solid, both = os.path.join(self.tmp, "block.stl"), os.path.join(self.tmp, "fin.stl")
        pw.write_stl(solid, [block])
        pw.write_stl(both, [block, fin])
        code, chk = run("check", solid, "--target", "print-fdm", "--thickness-samples", "3000")
        rule = next(r for r in chk["results"] if r["rule"] == "min_feature")
        self.assertEqual(rule["status"], "pass", chk)
        self.assertEqual(chk["inspect"]["thickness"]["thin_fraction"], 0)
        code, chk = run("check", both, "--target", "print-fdm", "--thickness-samples", "3000")
        th = chk["inspect"]["thickness"]
        rule = next(r for r in chk["results"] if r["rule"] == "min_feature")
        self.assertEqual(rule["status"], "warn", chk)
        self.assertAlmostEqual(th["thinnest"], 0.5, delta=0.01)
        # the fin's two big faces are 800 of the 3,240 mm2 of fin and block: about 25% of the surface
        self.assertGreater(th["thin_fraction"], 0.2)
        self.assertLess(th["thin_fraction"], 0.36)
        self.assertGreaterEqual(th["thin_spots"][0]["at"][0], 29.9)
        code, chk = run("check", both, "--target", "print-fdm", "--no-thickness")
        rule = next(r for r in chk["results"] if r["rule"] == "min_feature")
        self.assertEqual(rule["status"], "unchecked")

    def test_printable_fills_a_hollow_shell(self):
        # a box of 0.3 mm walls with air inside, open to the outside through a 0.6 mm slot in the lid (how
        # image-to-3D shells arrive: a fully closed cavity was already dropped as a separate part) comes out
        # solid; --hollow keeps the air
        w, slabs = 0.3, []
        for ring, z0, z1 in [([(0, 0), (20, 0), (20, 20), (0, 20)], 0, w),
                             ([(0, 0), (9.7, 0), (9.7, 20), (0, 20)], 20 - w, 20),
                             ([(10.3, 0), (20, 0), (20, 20), (10.3, 20)], 20 - w, 20),
                             ([(0, 0), (w, 0), (w, 20), (0, 20)], 0, 20), ([(20 - w, 0), (20, 0), (20, 20), (20 - w, 20)], 0, 20),
                             ([(0, 0), (20, 0), (20, w), (0, w)], 0, 20), ([(0, 20 - w), (20, 20 - w), (20, 20), (0, 20)], 0, 20)]:
            m = pw.Mesh("slab%d" % len(slabs), (0.5, 0.5, 0.5))
            m.v, m.f = pw.prism(ring, z0, z1)
            slabs.append(m)
        src = os.path.join(self.tmp, "shell.stl")
        pw.write_stl(src, slabs)
        args = ["--size-mm", "20", "--base-cut-mm", "0", "--no-planar", "--voxel-mm", "0.1"]
        code, out = run("printable", src, os.path.join(self.tmp, "solid.stl"), *args)
        self.assertEqual(code, 0, out)
        self.assertTrue(any(s.startswith("hollow shell: filled") for s in out["steps"]), out["steps"])
        self.assertGreater(out["volume_cm3"], 7.5)  # 20 mm cube: 8 cm3
        code, out = run("printable", src, os.path.join(self.tmp, "kept.stl"), *(args + ["--hollow"]))
        self.assertLess(out["volume_cm3"], 2.0)

    def test_printable_flat_open_surface(self):
        # an open flat sheet sits at z=0; the inward wall pushes it below zero, and the base clamp must not crush it
        m = pw.Mesh("sheet", (0.5, 0.5, 0.5))
        m.v = [(0, 0, 0), (4, 0, 0), (4, 4, 0), (0, 4, 0)]
        m.f = [(0, 1, 2), (0, 2, 3)]
        src = os.path.join(self.tmp, "sheet.glb")
        pw.write_glb(src, [m])
        code, out = run("printable", src, os.path.join(self.tmp, "sheet.stl"), "--size-mm", "40", "--wall-mm", "1.5")
        self.assertEqual(code, 0, out)
        self.assertTrue(out["watertight"], out)
        self.assertGreater(out["dims_mm"][2], 0.5)

    def test_render_sheet(self):
        d = os.path.join(self.tmp, "r")
        code, out = run("render", self.glb, "--out", d, "--views", "front,top,iso", "--size", "128")
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.isfile(out["sheet"]["path"]))
        self.assertEqual(len(out["shots"]), 3)

    def test_crowd_preview_passes_and_pose(self):
        d = os.path.join(self.tmp, "crowd")
        code, out = run("crowd", "--out", d, "--size", "320x192", "--frames", "17", "--ranks", "2", "--cols", "4",
                        "--action", "clash", "--preview", "--pose-min-px", "10")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["figures"], {"a": 8, "b": 8})
        self.assertEqual(out["frames_rendered"], 3)
        for name in ("depth", "mask", "clay"):
            self.assertEqual(len(os.listdir(os.path.join(d, name))), 3, name)
        self.assertLess(out["near_m"], out["far_m"])
        if "skipped" not in out["pose"]:
            self.assertGreater(out["pose"]["skeletons"], 0)
        with open(os.path.join(d, "camera.json")) as f:
            self.assertEqual(len(json.load(f)["matrix_world_rows"]), 17)

    def test_crowd_from_behind_hides_faces(self):
        d = os.path.join(self.tmp, "behind")
        code, out = run("crowd", "--out", d, "--size", "320x192", "--frames", "17", "--ranks", "2", "--cols", "4",
                        "--action", "march", "--sides", "1", "--view", "behind", "--preview", "--pose-min-px", "10",
                        "--passes", "pose")
        self.assertEqual(code, 0, out)
        with open(os.path.join(d, "joints.json")) as f:
            people = [p for fr in json.load(f)["frames"] for _, p in fr["people"]]
        self.assertTrue(people)
        self.assertTrue(all(p[0] == [-1, -1] for p in people), "a nose drawn on a figure marching away")

    def test_crowd_rejects_sizes_wan_cannot_take(self):
        code, out = run("crowd", "--out", os.path.join(self.tmp, "no"), "--size", "830x480", "--frames", "80")
        self.assertEqual(code, 2)
        self.assertIn("4n+1", out["error"])

    def figure(self, name, colour=(0.2, 0.5, 0.5)):
        """A box 'figure': a 0.3 x 0.2 x 1.0 body with a 0.2 head block on top, face flat toward -Y."""
        body, head = pw.Mesh("body", colour), pw.Mesh("head", colour)
        body.v, body.f = pw.prism([(-0.15, -0.1), (0.15, -0.1), (0.15, 0.1), (-0.15, 0.1)], 0, 0.8)
        head.v, head.f = pw.prism([(-0.1, -0.1), (0.1, -0.1), (0.1, 0.1), (-0.1, 0.1)], 0.8, 1.0)
        path = os.path.join(self.tmp, name + ".glb")
        pw.write_glb(path, [body, head])
        return path

    def test_turnaround_views_and_sheet(self):
        d = os.path.join(self.tmp, "turn")
        code, out = run("turnaround", self.figure("t"), "--out", d, "--views", "front,3q,back", "--size", "96x144",
                        "--samples", "2", "--height-m", "0.13")
        self.assertEqual(code, 0, out)
        self.assertEqual([s["view"] for s in out["shots"]], ["front", "3q", "back"])
        self.assertAlmostEqual(out["dims_m"][2], 0.13, places=3)
        self.assertTrue(os.path.isfile(out["sheet"]["path"]))
        code, out = run("turnaround", self.figure("t2"), "--out", d, "--views", "top")
        self.assertEqual(code, 1)
        self.assertIn("unknown view", out["error"])

    def test_mark_puts_the_marking_on_the_head_front(self):
        o = os.path.join(self.tmp, "marked.glb")
        code, out = run("mark", self.figure("m"), "--out", o, "--text", "2", "--colour", "0.8,0.1,0.2",
                        "--height-m", "0.13", "--recolour", "0.5,0.5,0.5")
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.isfile(o))
        self.assertIn("skipped", out["texture"])  # no base colour texture on a plain box
        fw, fh = out["mark"]["face_m"]
        self.assertAlmostEqual(fw, 0.13 * 0.2, delta=0.004)  # the head block's front, not the body's
        self.assertLess(out["mark"]["letter_h_m"], fh)
        code, out = run("inspect", o)
        self.assertGreaterEqual(out["objects"], 2)  # the figure and the marking

    def test_lineup_keeps_teams_on_their_sides(self):
        lay = {"size": [192, 112], "lens": 35, "cam": [0, -0.6, 0.07], "aim": [0, 0, 0.065], "backdrop_m": 0.6,
               "figures": [{"name": "b1", "file": self.figure("b1", (0, 0, 0)), "at": [0.12, 0], "face": "-60", "team": "b"},
                           {"name": "a1", "file": self.figure("a1"), "at": [-0.12, 0], "face": "60", "team": "a"}]}
        lp = os.path.join(self.tmp, "layout.json")
        with open(lp, "w") as f:
            json.dump(lay, f)
        d = os.path.join(self.tmp, "lineup")
        code, out = run("lineup", "--layout", lp, "--out", d, "--preview")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["left_to_right"], ["a1", "b1"])
        self.assertTrue(os.path.isfile(os.path.join(d, "depth.png")))
        self.assertLess(out["near_m"], out["far_m"])

    def test_bpy_runner_reports_tracebacks(self):
        s = os.path.join(self.tmp, "bad.py")
        with open(s, "w") as f:
            f.write("import bpy\nbpy.ops.import_scene.obj(filepath='x.obj')\n")  # removed in Blender 4
        code, out = run("bpy", s)
        self.assertEqual(code, 1)
        self.assertIn("traceback", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
