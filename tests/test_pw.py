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

    def test_texture_delight_flattens_a_baked_light_gradient(self):
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            self.skipTest("numpy and Pillow not installed")
        h, w = 128, 256
        yy, xx = np.mgrid[0:h, 0:w]
        lin = np.where((xx // 16 + yy // 16) % 2 == 0, 0.6, 0.3) * np.linspace(1 / 3, 1, w)[None, :]  # light 3:1 across
        srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
        src = os.path.join(self.tmp, "lit.png")
        Image.fromarray((np.dstack([srgb] * 3) * 255).round().astype("uint8")).save(src)

        def spread(path):  # block means over whole checker periods, in linear light
            a = np.asarray(Image.open(path).convert("L"), dtype=float) / 255
            a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
            m = a.reshape(h, w // 32, 32).mean(axis=(0, 2))
            return m.max() / m.min() - 1

        code, out = run("texture", src, "--out", os.path.join(self.tmp, "t"), "--delight")
        self.assertEqual(code, 0, out)
        self.assertGreater(spread(src), 1.0)
        self.assertLess(spread(out["maps"]["albedo_delit"]), 0.10)
        code, plain = run("texture", src, "--out", os.path.join(self.tmp, "p"))
        self.assertNotIn("albedo_delit", plain["maps"])  # off by default

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


EXAMPLE_DUEL = os.path.join(ROOT, "skills", "polywright", "examples", "duel.json")


def duel_spec(**over):
    s = {"camera": {"pos": [-3, 0, 1.6], "aim": [1, 0, 1.2]},
         "fighters": {"A": {"mark": [0, 0], "facing": "B", "weapons": {"right": 0.9}, "keys": [[0, "guard"], [1, "guard_low"]]},
                      "B": {"mark": [2, 0], "facing": 270, "keys": [[0, "stand"]]}}}
    s.update(over)
    return s


class Duel(unittest.TestCase):
    def test_pose_keys_smoothstep_between_held_ends(self):
        pool = dict(pw.DUEL_POSES)
        keys = [[0, "guard"], [1, "guard_low"]]
        z = lambda t: pw.duel_pose_at(keys, t, pool)["rhand"][2]  # noqa: E731
        self.assertAlmostEqual(z(-1), -0.12)  # held before the first key
        self.assertAlmostEqual(z(0.5), (-0.12 - 0.3) / 2)
        self.assertAlmostEqual(z(0.25), -0.12 + (-0.3 + 0.12) * 0.15625)  # smoothstep(0.25)
        self.assertAlmostEqual(z(5), -0.3)  # held after the last key
        self.assertEqual(pw.duel_resolve("guard_low", pool)["pelvis_z"], 0.88)  # inherited from guard

    def test_a_blade_that_goes_switches_halfway(self):
        pool = dict(pw.DUEL_POSES, empty={"base": "guard", "rblade": None})
        keys = [[0, "guard"], [1, "empty"]]
        self.assertEqual(pw.duel_pose_at(keys, 0.4, pool)["rblade"], [1, 0, 0.15])
        self.assertIsNone(pw.duel_pose_at(keys, 0.6, pool)["rblade"])

    def test_frames_for_preview_and_sheet(self):
        render, sheet = pw.duel_frames({"frames": 73, "fps": 24, "check_s": [1.0, 2.0, 9.0]}, preview=True)
        self.assertEqual(sheet, [0, 24, 48, 72])  # first, each check second (clamped), last
        self.assertEqual(render, sheet)
        self.assertEqual(len(pw.duel_frames({"frames": 73, "fps": 24}, preview=False)[0]), 73)

    def test_load_fills_defaults_facing_and_origin(self):
        s, problems = pw.duel_load(duel_spec(origin=[10, -30]))
        self.assertEqual(problems, [])
        self.assertEqual(s["fighters"]["A"]["mark"], [10, -30])
        self.assertAlmostEqual(s["fighters"]["A"]["facing"], 90.0)  # toward B, along +X
        self.assertEqual((s["frames"], s["fps"], s["size"]), (73, 24, [864, 480]))
        self.assertAlmostEqual(pw.bearing((0, 0), (0, -1)), 180.0)

    def test_load_reports_every_problem(self):
        bad = duel_spec(size=[830, 480], frames=80, camera={},
                        poses={"loop1": {"base": "loop2"}, "loop2": {"base": "loop1"}, "half": {"spine": [0, 1]}},
                        fly=[{"fighter": "B", "parts": ["rblade"], "t0": 1, "t1": 2, "to": [0, 0]}])
        bad["fighters"]["A"]["keys"] = [[1, "guard"], [0, "loop1"], [2, "nope"]]
        bad["fighters"]["B"]["keys"] = [[0, "half"]]
        bad["fighters"]["C"] = {"keys": [[0, "stand"]]}
        _, problems = pw.duel_load(bad)
        text = " | ".join(problems)
        for want in ("4n+1", "divisible by 16", "camera needs", "out of time order", "loops", "unknown pose nope",
                     "pose half: spine must be 3 numbers", "C: mark", "B cannot throw rblade"):
            self.assertIn(want, text)

    def test_face_points_hidden_by_the_camera_side(self):
        # a head at (0, 0, 1.6) facing +X: nose, right eye (-Y), left eye, right ear, left ear
        j = [(0, 0, 0)] * 18
        j[0], j[14], j[15] = (0.12, 0, 1.6), (0.1, -0.045, 1.63), (0.1, 0.045, 1.63)
        j[16], j[17] = (0, -0.12, 1.6), (0, 0.12, 1.6)
        self.assertEqual(pw.hidden_face_points(j, (5, 0, 1.6)), [])  # front
        self.assertEqual(pw.hidden_face_points(j, (-5, 0, 1.6)), [0, 14, 15])  # back: no nose, no eyes
        self.assertEqual(pw.hidden_face_points(j, (0, 5, 1.6)), [14, 16])  # profile from the left: far eye and ear

    def test_duel_check_runs_without_blender(self):
        code, out = run("duel", EXAMPLE_DUEL, "--check")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["sheet_frames"], [1, 20, 32, 47, 59, 73])
        self.assertEqual(set(out["fighters"]), {"A", "B"})
        code, out = run("duel", os.path.join(FIX, "missing.json"), "--check")
        self.assertEqual(code, 2)


class TopologyRules(unittest.TestCase):
    def test_pole_rule_only_judges_quad_meshes(self):
        tri = {"quad_share": 0.0, "max_pole_valence": 12, "poles": {"12": 1}}
        quad = {"quad_share": 0.9, "max_pole_valence": 6, "poles": {"6": 3}}
        self.assertEqual(pw.topology_rule("max_pole_valence", 5, tri)[0], "pass")
        self.assertFalse(pw.topology_rule("max_pole_valence", 5, quad)[0])
        self.assertTrue(pw.topology_rule("max_pole_valence", 6, quad)[0])

    def test_uv_spread_and_winding_rules(self):
        self.assertFalse(pw.topology_rule("max_uv_spread", 2.5, {"uv_spread": 3.4})[0])
        self.assertTrue(pw.topology_rule("max_uv_spread", 2.5, {"uv_spread": 1.2})[0])
        self.assertEqual(pw.topology_rule("max_uv_spread", 2.5, {})[0], "pass")
        self.assertFalse(pw.topology_rule("max_winding_mismatch", 0, {"winding_mismatch": 3})[0])
        self.assertTrue(pw.topology_rule("max_winding_mismatch", 0, {"winding_mismatch": 0})[0])

    def test_game_and_web_targets_carry_topology_rules(self):
        t = pw.load_targets()["targets"]
        for k in ("game-roblox", "game-unity", "game-unreal", "web-threejs", "ar-usdz", "commerce-gltf"):
            self.assertEqual(t[k]["rules"].get("max_winding_mismatch"), 0, k)
        self.assertNotIn("max_winding_mismatch", t["print-fdm"]["rules"])


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

    def write_obj(self, name, verts, faces, uvs=None):
        path = os.path.join(self.tmp, name)
        with open(path, "w") as f:
            for v in verts:
                f.write("v %g %g %g\n" % v)
            for t in uvs or []:
                f.write("vt %g %g\n" % t)
            for face in faces:
                f.write("f " + " ".join(("%d/%d" % (i + 1, i + 1)) if uvs else str(i + 1) for i in face) + "\n")
        return path

    def test_topology_finds_a_flipped_face_and_convert_fixes_it(self):
        m = pw.Mesh("box", (1, 1, 1))
        m.v, m.f = pw.prism([(0, 0), (1, 0), (1, 1), (0, 1)], 0, 1)
        good = os.path.join(self.tmp, "good.glb")
        pw.write_glb(good, [m])
        m.f[3] = tuple(reversed(m.f[3]))
        bad = os.path.join(self.tmp, "flipped.glb")
        pw.write_glb(bad, [m])
        code, out = run("inspect", good, "--topology")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["topology"]["winding_mismatch"], 0)
        self.assertEqual(out["topology"]["tris"], 12)
        code, out = run("inspect", bad, "--topology")
        self.assertEqual(out["topology"]["winding_mismatch"], 3)  # the flipped triangle's three edges
        code, chk = run("check", bad, "--target", "web-threejs")
        self.assertEqual({r["rule"]: r["status"] for r in chk["results"]}["max_winding_mismatch"], "warn")
        fixed = os.path.join(self.tmp, "fixed.glb")
        code, out = run("convert", bad, fixed, "--fix-winding")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["faces_flipped"], 1)
        code, out = run("inspect", fixed, "--topology")
        self.assertEqual(out["topology"]["winding_mismatch"], 0)
        self.assertFalse(out.get("inside_out"))

    def test_topology_counts_stacked_faces_ngons_and_uv_spread(self):
        quads = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (2, 0, 0), (2, 1, 0)]
        even = [(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5), (1, 0), (1, 0.5)]
        uneven = [(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5), (0.55, 0), (0.55, 0.5)]  # second quad gets a tenth of the texels
        faces = [(0, 1, 2, 3), (1, 4, 5, 2)]
        code, out = run("inspect", self.write_obj("even.obj", quads, faces, even), "--topology")
        self.assertEqual(code, 0, out)
        t = out["topology"]
        self.assertEqual((t["quads"], t["ngons"], t["duplicate_faces"]), (2, 0, 0))
        self.assertAlmostEqual(t["uv_spread"], 1.0, places=2)
        code, out = run("inspect", self.write_obj("uneven.obj", quads, faces, uneven), "--topology")
        self.assertGreater(out["topology"]["uv_spread"], 5)
        pent = [(0, 0, 0), (1, 0, 0), (1.5, 0.8, 0), (0.5, 1.4, 0), (-0.5, 0.8, 0)]
        # a double-sided copy: its own vertices on the same spots, wound the other way (the importer drops exact repeats)
        code, out = run("inspect", self.write_obj("ngon.obj", pent + pent, [(0, 1, 2, 3, 4), (9, 8, 7, 6, 5)]), "--topology")
        self.assertEqual((out["topology"]["ngons"], out["topology"]["duplicate_faces"]), (2, 1))

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
        self.assertFalse(any(s.startswith("hollow shell") for s in out["steps"]), out["steps"])  # solids are not filled

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
        self.assertFalse(any(s.startswith("hollow shell") for s in out["steps"]), out["steps"])  # a slab is not a shell

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
        try:
            from PIL import Image
        except ImportError:
            Image = None
        if Image:  # Workbench AA is off for masks: only the two side colours and the black ground
            im = Image.open(os.path.join(d, "mask", sorted(os.listdir(os.path.join(d, "mask")))[1])).convert("RGB")
            stray = sum(n for n, c in im.getcolors(1 << 16) if c not in ((255, 0, 0), (0, 0, 255), (0, 0, 0)))
            self.assertEqual(stray, 0)
        if "skipped" not in out["pose"]:
            self.assertGreater(out["pose"]["skeletons"], 0)
        with open(os.path.join(d, "camera.json")) as f:
            self.assertEqual(len(json.load(f)["matrix_world_rows"]), 17)

    def test_crowd_mist_pass_beside_unchanged_depth(self):
        args = ["--size", "320x192", "--frames", "17", "--ranks", "2", "--cols", "4", "--preview"]
        code, plain = run("crowd", "--out", os.path.join(self.tmp, "nomist"), "--passes", "depth", *args)
        self.assertEqual(code, 0, plain)
        d = os.path.join(self.tmp, "mist")
        code, out = run("crowd", "--out", d, "--passes", "depth,mist", *args)
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(os.listdir(os.path.join(d, "mist"))), ["0001.png", "0009.png", "0017.png"])
        for n in ("0001.png", "0017.png"):  # the depth frames do not change when mist rides along
            with open(os.path.join(d, "depth", n), "rb") as f, open(os.path.join(self.tmp, "nomist", "depth", n), "rb") as g:
                self.assertEqual(pw.png_decode(f.read())[3], pw.png_decode(g.read())[3], n)
        with open(os.path.join(d, "mist", "0001.png"), "rb") as f:
            png = f.read()
        self.assertEqual(png[24], 16)  # IHDR bit depth
        self.assertEqual(png[25], 0)  # grey
        try:
            from PIL import Image
            im = Image.open(os.path.join(d, "mist", "0001.png"))
            w, h = im.size
            row = lambda y: sum(im.getpixel((x, y)) for x in range(w)) / w
            self.assertGreater(row(h - 1), row(0) + 20000)  # near ground white, far sky black
        except ImportError:
            pass
        code, only = run("crowd", "--out", os.path.join(self.tmp, "mistonly"), "--passes", "mist", *args)
        self.assertEqual(code, 0, only)
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, "mistonly", "depth")))
        # the hint names only the passes this run wrote (0.4.0 always said depth.mp4 and pose.mp4)
        self.assertIn("mist.mp4", only["next"])
        self.assertNotIn("depth.mp4", only["next"])
        self.assertNotIn("pose.mp4", plain["next"])
        self.assertIn("depth.mp4 or mist.mp4", out["next"])
        self.assertEqual(len(os.listdir(os.path.join(self.tmp, "mistonly", "mist"))), 3)

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

    def test_crowd_scatter_adds_reserves_behind_the_far_side(self):
        def blue(d):
            with open(os.path.join(d, "mask", "0001.png"), "rb") as f:
                w, h, ch, px = pw.png_decode(f.read())
            return sum(1 for i in range(0, len(px), ch) if px[i + 2] > 200 and px[i] < 50)
        args = ["--size", "320x192", "--frames", "17", "--ranks", "2", "--cols", "6", "--view", "behind",
                "--preview", "--passes", "mask"]
        code, plain = run("crowd", "--out", os.path.join(self.tmp, "plain"), *args)
        self.assertEqual(code, 0, plain)
        d = os.path.join(self.tmp, "scatter")
        code, out = run("crowd", "--out", d, "--scatter", "60", *args)
        self.assertEqual(code, 0, out)
        self.assertNotIn("a", out["scatter"])  # the camera stands in side A's rear
        self.assertIn("a", out["scatter_skipped"])
        self.assertTrue(10 <= out["scatter"]["b"] <= 60, out["scatter"])
        self.assertGreater(blue(d), blue(os.path.join(self.tmp, "plain")) * 1.2)

    def test_videos_through_blender_when_ffmpeg_is_missing(self):
        out = os.path.join(self.tmp, "enc")
        os.makedirs(os.path.join(out, "depth"))
        for i in range(5):
            with open(os.path.join(out, "depth", "%04d.png" % (i + 1)), "wb") as f:
                f.write(make_png(64, 48, [[40 * i, 40 * i, 40 * i] * 64] * 48))
        real = shutil.which
        pw.shutil.which = lambda n, *a, **k: None if n == "ffmpeg" else real(n, *a, **k)
        try:
            vids = pw.encode_passes(out, ["depth", "mask"], 16)
        finally:
            pw.shutil.which = real
        self.assertIn("blender", vids.get("encoder", ""), vids)
        self.assertTrue(os.path.getsize(os.path.join(out, "depth.mp4")) > 1000, vids)
        self.assertNotIn("mask", vids)  # no frames, no video
        self.assertFalse([n for n in os.listdir(out) if n.startswith("_pw_encode_")])

    def test_crowd_rejects_sizes_wan_cannot_take(self):
        code, out = run("crowd", "--out", os.path.join(self.tmp, "no"), "--size", "830x480", "--frames", "80")
        self.assertEqual(code, 2)
        self.assertIn("4n+1", out["error"])

    def test_duel_example_preview_writes_every_pass(self):
        d = os.path.join(self.tmp, "duel")
        code, out = run("duel", EXAMPLE_DUEL, "--preview", "--out", d)
        self.assertEqual(code, 0, out)
        for name in ("clay", "canny", "depth", "depth_thick"):
            self.assertEqual(len(os.listdir(os.path.join(d, name))), 6, name)
        self.assertEqual(out["in_frame"]["B"], {"first": 1.0, "last": 1.0})
        with open(os.path.join(d, "joints.json")) as f:
            frames = json.load(f)["frames"]
        near = [fr["people"][-1][1] for fr in frames]  # the nearest skeleton draws last: A, back to the camera
        far = [fr["people"][0][1] for fr in frames]
        self.assertTrue(all(p[0] == [-1, -1] for p in near), "a nose drawn on a back")
        self.assertTrue(all(p[0] != [-1, -1] for p in far), "B faces the lens")
        if out.get("sheet"):
            self.assertTrue(os.path.isfile(out["sheet"]))

    def test_duel_camera_from_a_room_script(self):
        room = os.path.join(self.tmp, "room.py")
        with open(room, "w") as f:
            f.write("import bpy\nbpy.ops.mesh.primitive_plane_add(size=10)\n"
                    "cam = bpy.data.objects.new('ShotCam', bpy.data.cameras.new('ShotCam'))\n"
                    "bpy.context.scene.collection.objects.link(cam)\n"
                    "cam.location = (DUEL['origin'][0] - 4, DUEL['origin'][1], 1.5)\n"
                    "cam.rotation_euler = (1.5708, 0, -1.5708)\n")
        spec = duel_spec(origin=[5, 0], room={"script": "room.py"}, camera={"object": "ShotCam", "lens": 35},
                         size=[320, 192], frames=17, fps=16)
        path = os.path.join(self.tmp, "cam.json")
        with open(path, "w") as f:
            json.dump(spec, f)
        code, out = run("duel", path, "--preview")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["out"], os.path.join(self.tmp, "cam"))
        self.assertGreater(out["in_frame"]["A"]["first"], 0.5)
        with open(os.path.join(self.tmp, "cam", "camera.json")) as f:
            self.assertEqual(json.load(f)["lens_mm"], 35)

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


def diamond(yaw_deg, elev_deg, s, tiles=2, front=(48.0, 90.0), jitter=0.0, seed=1):
    """A ground diamond (front, left, right) projected from a known orthographic sprite camera."""
    import random
    rnd = random.Random(seed)
    y, e = math.radians(yaw_deg), math.radians(elev_deg)
    L = (-math.cos(y) * s * tiles, -math.sin(e) * math.sin(y) * s * tiles)
    R = (math.sin(y) * s * tiles, -math.sin(e) * math.cos(y) * s * tiles)
    j = lambda: rnd.uniform(-jitter, jitter)
    return {"front": {"x": front[0], "y": front[1]},
            "left": {"x": front[0] + L[0] + j(), "y": front[1] + L[1] + j()},
            "right": {"x": front[0] + R[0] + j(), "y": front[1] + R[1] + j()}}


class SpriteCamera(unittest.TestCase):
    def test_fit_recovers_a_known_camera(self):
        r = pw.fit_diamond(diamond(41.0, 31.0, 29.0), 2)
        self.assertAlmostEqual(r["yaw_deg"], 41.0, delta=0.05)
        self.assertAlmostEqual(r["elevation_deg"], 31.0, delta=0.05)
        self.assertAlmostEqual(r["px_per_tile"], 29.0, delta=0.05)
        self.assertLess(r["rms_px"], 0.05)

    def test_spritecam_takes_the_median_of_a_registry_and_drops_misfits(self):
        tmp = tempfile.mkdtemp(prefix="pwtest_sc_")
        try:
            blds = [{"buildingId": "b%d" % i, "size": {"x": 2, "y": 2},
                     "groundBase": diamond(42.0 + (i % 3 - 1), 33.0 + (i % 5 - 2) * 0.5, 30.0, jitter=1.0, seed=i)}
                    for i in range(9)]
            blds.append({"buildingId": "big", "size": {"x": 3, "y": 3}, "groundBase": diamond(10, 70, 50)})
            blds.append({"buildingId": "skewed", "size": {"x": 2, "y": 2},
                         "groundBase": {"front": {"x": 50, "y": 90}, "left": {"x": 0, "y": 89},
                                        "right": {"x": 60, "y": 20}}})
            reg = os.path.join(tmp, "reg.json")
            with open(reg, "w") as f:
                json.dump({"buildings": blds}, f)
            out = os.path.join(tmp, "camera.json")
            code, res = run("spritecam", reg, "--out", out, "--like", "b0")
            self.assertEqual(code, 0, res)
            self.assertIn("9 of 10", res["source"])
            self.assertAlmostEqual(res["yaw_deg"], 42.0, delta=1.0)
            self.assertAlmostEqual(res["elevation_deg"], 33.0, delta=1.0)
            self.assertAlmostEqual(res["px_per_tile"], 30.0, delta=1.0)
            cam = json.load(open(out))
            self.assertEqual(cam["projection"], "orthographic")
            self.assertEqual(cam["canvas_px"], [96, 96])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


SPRITE_SCENE = """
import bpy, bmesh, json, math, sys
from mathutils import Matrix
out = sys.argv[sys.argv.index("--") + 1]
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


@unittest.skipUnless(pw.backend(), "Blender not found")
class SpriteWithBlender(unittest.TestCase):
    def test_sprite_renders_passes_frames_and_a_ground_base_the_camera_fit_recovers(self):
        tmp = tempfile.mkdtemp(prefix="pwtest_sp_")
        try:
            script = os.path.join(tmp, "scene.py")
            with open(script, "w") as f:
                f.write(SPRITE_SCENE)
            blend = os.path.join(tmp, "m.blend")
            r = pw.run_blender_script(script, [blend])
            self.assertTrue(os.path.isfile(blend), r.get("stderr", "")[-800:])
            cam = {"projection": "orthographic", "yaw_deg": 40.0, "elevation_deg": 32.0, "px_per_tile": 30.0,
                   "canvas_px": [96, 96], "render_scale": 2, "tile_m": 5.0, "footprint_tiles": [2, 2],
                   "footprint_centre_px": [48, 66], "sun_dir": [-0.75, -0.35, 0.85]}
            cpath = os.path.join(tmp, "camera.json")
            with open(cpath, "w") as f:
                json.dump(cam, f)
            out = os.path.join(tmp, "r")
            code, res = run("sprite", blend, "--camera", cpath, "--out", out, "--samples", "2",
                            "--passes", "beauty,id,depth,normal,pos", "--frames", "2", "--frame-passes", "id,pos")
            self.assertEqual(code, 0, res)
            self.assertEqual(res["passes"], {"beauty": 1, "id": 3, "depth": 1, "normal": 1, "pos": 3})
            for n in ("beauty.png", "id.png", "pos.tif", "frames/id_001.png", "frames/pos_001.tif", "sprite.json"):
                self.assertTrue(os.path.isfile(os.path.join(out, n)), n)
            with open(os.path.join(out, "pos.tif"), "rb") as f:
                self.assertIn(f.read(2), (b"II", b"MM"))
            meta = json.load(open(os.path.join(out, "sprite.json")))
            back = pw.fit_diamond(meta["groundBase"], 2)
            self.assertAlmostEqual(back["yaw_deg"], 40.0, delta=0.3)
            self.assertAlmostEqual(back["elevation_deg"], 32.0, delta=0.3)
            self.assertAlmostEqual(back["px_per_tile"], 30.0, delta=0.3)
            gb = meta["groundBase"]
            self.assertAlmostEqual((gb["left"]["x"] + gb["right"]["x"]) / 2, 48, delta=0.6)
            self.assertAlmostEqual((gb["left"]["y"] + gb["right"]["y"]) / 2, 66, delta=0.6)
            rim = meta["rings"]["wheel"]["rim_px"]
            self.assertEqual(len(rim), 72)
            xs = [p[0] for p in rim]
            self.assertGreater(max(xs) - min(xs), 10)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def frame_problem(**over):
    """A hero two metres tall to be framed right of centre, a far landmark kept in frame, the UI's text bands
    (centred, top and bottom 15 percent) kept clear of the hero's top and foot."""
    prob = {"size": [1920, 1080],
            "points": {"hero": [0, 0, 2], "hero_top": [0, 0, 4], "hero_bottom": [0, 0, 0], "far": [30, 20, 0]},
            "boxes": {"hero": {"x": [0.6, 0.75], "y": [0.4, 0.6]}},
            "keep_in_frame": ["far", "hero_top", "hero_bottom"],
            "bands": [{"x": [0.25, 0.75], "y": [0, 0.15]}, {"x": [0.25, 0.75], "y": [0.85, 1]}],
            "keep_out_of_bands": ["hero_top", "hero_bottom"],
            "size_measure": ["hero_top", "hero_bottom"],
            "search": {"pos": [[-8, 8, 2], [-30, -10, 2], [1, 5, 1]], "target": [[-4, 4, 1], 0, 2], "lens_mm": [20, 60, 5]}}
    prob.update(over)
    return prob


class FrameCam(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwtest_fc_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def solve(self, prob, *extra):
        path = os.path.join(self.tmp, "prob.json")
        with open(path, "w") as f:
            json.dump(prob, f)
        return run("framecam", path, *extra)

    def test_pinhole_puts_the_aim_at_the_centre_and_scales_with_the_lens(self):
        proj = pw.pinhole((0, -10, 2), (0, 0, 2), 36.0, (1920, 1080))
        x, y, z = proj((0, 0, 2))
        self.assertAlmostEqual(x, 0.5)
        self.assertAlmostEqual(y, 0.5)
        self.assertAlmostEqual(z, 10.0)
        x, y, _ = proj((1, 0, 3))  # 1 m right and up at 10 m: f_px x 0.1 = 192 px
        self.assertAlmostEqual(x * 1920, 960 + 192, places=6)
        self.assertAlmostEqual(y * 1080, 540 - 192, places=6)
        self.assertIsNone(proj((0, -20, 2))[0])
        self.assertIsNone(pw.pinhole((0, 0, 10), (0, 0, 0), 35, (64, 64)))

    def test_framecam_finds_cameras_that_meet_every_rule(self):
        prob = frame_problem()
        out = os.path.join(self.tmp, "cameras.json")
        with open(out, "w") as f:
            json.dump({"sun": {"azimuth_deg": 200}, "cameras": {"old": {"pos": [0, 0, 1], "target": [0, 1, 1]}}}, f)
        code, res = self.solve(prob, "--out", out, "--top", "3")
        self.assertEqual(code, 0, res)
        self.assertEqual(sorted(res["cameras"]), ["framecam_1", "framecam_2", "framecam_3"])
        sizes = [res["cameras"]["framecam_%d" % i]["size_px"] for i in (1, 2, 3)]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        for c in res["cameras"].values():  # check each rule with the projection alone
            proj = pw.pinhole(c["pos"], c["target"], c["lens_mm"], (1920, 1080))
            at = {n: proj(v) for n, v in prob["points"].items()}
            self.assertTrue(0.6 <= at["hero"][0] <= 0.75 and 0.4 <= at["hero"][1] <= 0.6, at["hero"])
            for n in ("far", "hero_top", "hero_bottom"):
                self.assertTrue(0 <= at[n][0] <= 1 and 0 <= at[n][1] <= 1, (n, at[n]))
            for n in ("hero_top", "hero_bottom"):
                x, y, _ = at[n]
                self.assertFalse(0.25 <= x <= 0.75 and (y <= 0.15 or y >= 0.85), (n, x, y))
            top, bot = at["hero_top"], at["hero_bottom"]
            self.assertAlmostEqual(math.hypot((top[0] - bot[0]) * 1920, (top[1] - bot[1]) * 1080), c["size_px"], delta=0.2)
        with open(out) as f:
            saved = json.load(f)
        self.assertIn("old", saved["cameras"])  # merged, not replaced
        self.assertIn("framecam_1", saved["cameras"])
        self.assertEqual(saved["sun"], {"azimuth_deg": 200})

    def test_framecam_names_the_rule_no_camera_can_meet(self):
        prob = frame_problem()
        prob["search"]["target"] = [0, 0, 2]  # aimed at the hero, it is always at the centre, never right of it
        code, res = self.solve(prob)
        self.assertEqual(code, 1, res)
        self.assertFalse(res["ok"])
        self.assertIn("never met: box:hero", res["error"])

    def test_framecam_refuses_unknown_points_and_oversized_searches(self):
        code, res = self.solve(frame_problem(keep_in_frame=["weir"]))
        self.assertEqual(code, 1)
        self.assertIn("unknown point names ['weir']", res["error"])
        code, res = self.solve(frame_problem(), "--max-evals", "1000")
        self.assertEqual(code, 1)
        self.assertIn("over the 1000 limit", res["error"])


class ScenePlumbing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwtest_scn_")
        self.cams = os.path.join(self.tmp, "cameras.json")
        with open(self.cams, "w") as f:
            json.dump({"sun": {"azimuth_deg": 120, "elevation_deg": 20, "energy": 3, "colour": [1, 1, 1]},
                       "sky": {"strength": 0.5},
                       "cameras": {"wide": {"pos": [10, -24, 5], "target": [2, -2, 1.5], "lens_mm": 32,
                                            "depth_near_m": 8}}}, f)
        self.calls = []
        self.saved = pw.bpy_action

        def fake(action, params, timeout=1800, script=pw.BPY_SCRIPT):
            self.calls.append((action, params, script))
            return {"ok": True, "action": action}
        pw.bpy_action = fake

    def tearDown(self):
        pw.bpy_action = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scene_passes_the_preset_sun_size_and_options_to_the_scene_script(self):
        code, res = run("scene", "s.blend", "--cameras", self.cams, "--camera", "wide", "--out", self.tmp,
                        "--size", "1920x1080", "--passes", "clay, depth,id", "--samples", "8", "--hide", "wheel_,race_",
                        "--no-line")
        self.assertEqual(code, 0, res)
        action, params, script = self.calls[0]
        self.assertEqual((action, os.path.basename(script)), ("scene", "pw_scene.py"))
        self.assertEqual(params["camera"]["lens_mm"], 32)
        self.assertEqual(params["camera_name"], "wide")
        self.assertEqual(params["sun"]["azimuth_deg"], 120)
        self.assertEqual(params["world"], {"strength": 0.5})
        self.assertEqual(params["size"], [1920, 1080])
        self.assertEqual(params["passes"], ["clay", "depth", "id"])
        self.assertEqual(params["hide"], ["wheel_", "race_"])
        self.assertEqual(params["samples"], 8)
        self.assertTrue(os.path.isabs(params["file"]))
        self.assertNotIn("line", res)

    def test_scene_refuses_unknown_cameras_passes_and_sizes_before_blender(self):
        code, res = run("scene", "s.blend", "--cameras", self.cams, "--camera", "close", "--out", self.tmp)
        self.assertEqual(code, 2)
        self.assertEqual(res["known"], ["wide"])
        code, res = run("scene", "s.blend", "--cameras", self.cams, "--camera", "wide", "--out", self.tmp,
                        "--passes", "beauty,mist", "--size", "1280")
        self.assertEqual(code, 2)
        self.assertIn("unknown pass mist", res["error"])
        self.assertIn("--size must be WxH", res["error"])
        code, res = run("scene", "s.blend", "--cameras", os.path.join(self.tmp, "none.json"), "--camera", "wide",
                        "--out", self.tmp)
        self.assertEqual(code, 2)
        self.assertEqual(self.calls, [])


SCENE_BUILD = """
import bpy, bmesh, json, sys
from mathutils import Matrix
blend, scripts = sys.argv[sys.argv.index("--") + 1:][:2]
sys.path.insert(0, scripts)
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
bpy.ops.wm.save_as_mainfile(filepath=blend)
"""


@unittest.skipUnless(pw.backend(), "Blender not found")
class SceneWithBlender(unittest.TestCase):
    def test_scene_renders_passes_and_projects_rings_and_points_as_framecam_does(self):
        tmp = tempfile.mkdtemp(prefix="pwtest_sc3_")
        try:
            script = os.path.join(tmp, "build.py")
            with open(script, "w") as f:
                f.write(SCENE_BUILD)
            blend = os.path.join(tmp, "scene.blend")
            r = pw.run_blender_script(script, [blend, os.path.dirname(pw.BPY_SCRIPT)])
            self.assertTrue(os.path.isfile(blend), r.get("stderr", "")[-800:] + r.get("stdout", "")[-800:])
            preset = {"pos": [6, -14, 3], "target": [0, 4, 2], "lens_mm": 30}
            cams = os.path.join(tmp, "cameras.json")
            with open(cams, "w") as f:
                json.dump({"cameras": {"low": preset}}, f)
            out = os.path.join(tmp, "r")
            code, res = run("scene", blend, "--cameras", cams, "--camera", "low", "--out", out, "--size", "192x108",
                            "--samples", "2", "--no-line")
            self.assertEqual(code, 0, res)
            for n in ("clay", "beauty", "depth", "normal", "id"):
                self.assertTrue(os.path.isfile(os.path.join(out, n + ".png")), n)
            with open(os.path.join(out, "scene.json")) as f:
                meta = json.load(f)
            self.assertTrue(meta["depth_range_from"].startswith("measured"))
            near, far = meta["depth_range_m"]
            self.assertGreater(near, 2.0)  # nothing is nearer than the ground at the frame's foot
            self.assertGreater(far, near)
            proj = pw.pinhole(preset["pos"], preset["target"], 30, (192, 108))
            x, y, _ = proj((-3, 4, 1))
            got = meta["points"]["door"]
            self.assertAlmostEqual(got["px"][0], x * 192, delta=0.3)
            self.assertAlmostEqual(got["px"][1], y * 108, delta=0.3)
            self.assertTrue(got["in_frame"])
            self.assertEqual(len(meta["points"]["road"]), 2)
            wheel = meta["rings"]["wheel"]
            self.assertEqual((len(wheel["rim_px"]), len(wheel["hub_px"])), (72, 72))
            cx, cy, _ = proj((3, 3.8, 1.8))  # the face nearer the camera
            self.assertAlmostEqual(wheel["centre_px"][0], cx * 192, delta=0.3)
            self.assertAlmostEqual(wheel["centre_px"][1], cy * 108, delta=0.3)
            with open(os.path.join(out, "id.png"), "rb") as f:
                w, h, ch, px = pw.png_decode(f.read())
            self.assertEqual((w, h, ch), (192, 108, 4))
            self.assertEqual(px[3], 0)  # top-left corner is sky: transparent
            hx, hy, _ = proj((-3, 4, 2))  # the house's front face centre
            i = (int(hy * 108) * 192 + int(hx * 192)) * 4
            self.assertEqual(list(px[i:i + 3]), meta["id_colours_srgb"]["house"])
            self.assertEqual(px[i + 3], 255)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
