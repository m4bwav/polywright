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

    def test_printable(self):
        dst = os.path.join(self.tmp, "p.stl")
        code, out = run("printable", self.glb, dst, "--size-mm", "40")
        self.assertEqual(code, 0, out)
        self.assertTrue(out["watertight"])
        self.assertAlmostEqual(max(out["dims_mm"]), 40, delta=0.8)

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

    def test_bpy_runner_reports_tracebacks(self):
        s = os.path.join(self.tmp, "bad.py")
        with open(s, "w") as f:
            f.write("import bpy\nbpy.ops.import_scene.obj(filepath='x.obj')\n")  # removed in Blender 4
        code, out = run("bpy", s)
        self.assertEqual(code, 1)
        self.assertIn("traceback", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
