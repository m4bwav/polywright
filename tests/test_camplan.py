"""Tests for `pw.py camplan` and skills/polywright/scripts/pw_camplan.py (stdlib unittest).

Run from the repository root: python tests/test_camplan.py (tests/test_pw.py runs these too). The plan maths and the
framing check are pure Python; one test keyframes the camera in Blender and skips when none is found.
"""
import contextlib
import copy
import io
import json
import math
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "polywright", "scripts"))
import pw  # noqa: E402
import pw_camplan as cp  # noqa: E402

EXAMPLE = os.path.join(ROOT, "skills", "polywright", "examples", "camplan.json")


def shot(**kw):
    with open(EXAMPLE, encoding="utf-8") as f:
        s = json.load(f)
    s.update(kw)
    return s


def plan(s):
    spec, problems = cp.load(s)
    assert not problems, problems
    return spec, cp.plan(spec)


def runpw(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pw.main(list(argv))
    return code, json.loads(buf.getvalue())


class CamplanMaths(unittest.TestCase):
    def test_walk_with_dolly_orbit_and_pedestal_fails_the_height_target(self):
        # the reader's prototype shot: walk 2 m in 4 s, follow + dolly in 0.72 + orbit 28 from 1 s + pedestal 0.8 from 2 s
        _, (frames, rows, rep) = plan(shot())
        self.assertEqual(len(frames), 97)
        self.assertAlmostEqual(rep["height_first"], 0.459, places=3)
        self.assertAlmostEqual(rep["height_last"], 0.573, places=3)
        self.assertEqual(rep["frames_out"], 0)
        self.assertAlmostEqual(rep["max_height_error"], 0.126, places=3)
        self.assertFalse(rep["pass"])
        self.assertEqual(frames[-1]["pos"], [3.81433, 4.02812, 2.4])
        s = shot()
        s["camera"]["lens_mm"] = 50
        self.assertAlmostEqual(plan(s)[1][2]["max_height_error"], 0.373, places=3)

    def test_paper_defaults_and_ratios_multiply_angles_add(self):
        s = shot(operations=[{"method": "Dolly In"}, {"method": "Dolly Out"}], subjects={"hero": {"pos": [0, 0, 0]}})
        spec, (frames, _, _) = plan(s)
        r = math.hypot(*frames[-1]["pos"][:2])
        self.assertAlmostEqual(r, 6 * 0.72 * 1.35, places=4)
        s["operations"] = [{"method": "Orbit"}, {"method": "orbit", "parameters": {"direction": "left"}}]
        self.assertEqual(plan(s)[1][0][-1]["pos"], [6.0, 0.0, 1.6])
        s["operations"] = [{"method": "Orbit"}]
        p = plan(s)[1][0][-1]["pos"]
        self.assertAlmostEqual(math.degrees(math.atan2(p[1], p[0])), 28.0, places=3)
        s["operations"] = [{"method": "Zoom"}, {"method": "Zoom"}]
        self.assertAlmostEqual(plan(s)[1][0][-1]["lens_mm"], 35 * (50 / 35) ** 2, places=3)

    def test_overlapping_ops_ease_on_their_own_intervals(self):
        s = shot(operations=[{"method": "Pedestal Up", "start_sec": 1, "end_sec": 3}], subjects={"hero": {"pos": [0, 0, 0]}})
        frames = plan(s)[1][0]
        z = [f["pos"][2] for f in frames]
        self.assertEqual(z[0], 1.6)
        self.assertEqual(z[24], 1.6)  # held until 1 s
        self.assertAlmostEqual(z[48], 2.1, places=4)  # smoothstep half way
        self.assertAlmostEqual(z[72], 2.6, places=4)
        self.assertAlmostEqual(z[96], 2.6, places=4)

    def test_frame_subject_brings_the_height_to_its_fraction(self):
        s = shot()
        s["operations"].append({"method": "Frame Subject", "start_sec": 0, "end_sec": 4, "parameters": {"height_fraction": 0.45}})
        rep = plan(s)[1][2]
        self.assertAlmostEqual(rep["height_last"], 0.45, places=3)
        self.assertTrue(rep["pass"])

    def test_screen_position_lock_and_out_of_frame(self):
        s = shot(operations=[{"method": "Screen Position Lock", "parameters": {"uv": [0.33, 0.5]}}],
                 framing={"height_fraction": 0.45, "tolerance": 0.2, "screen_uv": [0.33, 0.5], "uv_tolerance": 0.02})
        s["camera"]["aim"] = [0, 0, 0.81]
        rep = plan(s)[1][2]
        self.assertLess(rep["max_uv_error"], 0.02)
        s["operations"] = [{"method": "Pan", "parameters": {"angle_deg": 60}}]
        rep = plan(s)[1][2]
        self.assertGreater(rep["frames_out"], 0)
        self.assertFalse(rep["pass"])

    def test_handheld_is_seeded_and_horizon_lock_levels_it(self):
        s = shot(operations=[{"method": "Handheld", "parameters": {"seed": 7}}])
        a, b = plan(s)[1][0], plan(copy.deepcopy(s))[1][0]
        self.assertEqual(a, b)
        self.assertNotEqual(a[48]["roll_deg"], 0)
        s["operations"].append({"method": "Horizon Lock"})
        self.assertAlmostEqual(plan(s)[1][0][-1]["roll_deg"], 0, places=6)

    def test_load_reports_every_problem(self):
        s, P = cp.load({"camera": {"pos": [0, 0, 1]}, "subjects": {"x": {}},
                        "operations": [{"method": "Warp"}, {"method": "Pan", "start_sec": 3, "end_sec": 1}]})
        text = " ".join(P)
        for want in ("subject x needs", "unknown method 'Warp'", "end_sec must come after", "camera needs pos"):
            self.assertIn(want, text)
        s, P = cp.load({"camera": {"preset": "framecam_1"}}, {"framecam_1": {"pos": [1, 2, 3], "target": [0, 0, 0], "lens_mm": 28}})
        self.assertEqual(P, [])
        self.assertEqual(s["camera"]["aim"], [0, 0, 0])


class CamplanCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwcp_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_check_exits_1_on_fail_and_out_writes_the_files(self):
        code, out = runpw("camplan", EXAMPLE, "--check")
        self.assertEqual((code, out["verdict"], out["frames"]), (1, "FAIL", 97))
        self.assertNotIn("files", out)
        code, out = runpw("camplan", EXAMPLE, "--out", self.tmp)
        with open(out["files"]["camera"], encoding="utf-8") as f:
            cam = json.load(f)
        self.assertEqual(len(cam["frames"]), 97)
        self.assertEqual(len(cam["frames"][0]["matrix_world"]), 16)
        with open(out["files"]["framing"], encoding="utf-8") as f:
            fr = json.load(f)
        self.assertFalse(fr["report"]["pass"])
        code, out = runpw("camplan", EXAMPLE)
        self.assertEqual(code, 2)
        self.assertIn("--check", out["error"])

    def test_camera_file_reads_camplan_crowd_and_duel_files(self):
        runpw("camplan", EXAMPLE, "--out", self.tmp)
        cf, note = pw.load_camera_file(os.path.join(self.tmp, "camera.json"), 81)
        self.assertEqual(len(cf["frames"]), 97)
        self.assertIn("extra ones are unused", note)
        one = os.path.join(self.tmp, "duel_camera.json")
        with open(one, "w", encoding="utf-8") as f:
            json.dump({"lens_mm": 40, "sensor_mm": 36, "matrix_world_rows": list(range(16))}, f)
        cf, note = pw.load_camera_file(one, 73)
        self.assertEqual((len(cf["frames"]), cf["frames"][0]["lens"]), (1, 40.0))
        self.assertIn("last one holds", note)

    def test_duel_check_takes_a_camera_file_instead_of_its_camera(self):
        runpw("camplan", EXAMPLE, "--out", self.tmp)
        with open(os.path.join(ROOT, "skills", "polywright", "examples", "duel.json"), encoding="utf-8") as f:
            d = json.load(f)
        d.pop("camera")
        d["room"] = {}
        p = os.path.join(self.tmp, "duel.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f)
        code, out = runpw("duel", p, "--check")
        self.assertEqual(code, 2)
        code, out = runpw("duel", p, "--check", "--camera-file", os.path.join(self.tmp, "camera.json"))
        self.assertEqual(code, 0, out)
        self.assertIn("camera file has 97 frames", out["camera_file"])


@unittest.skipUnless(pw.backend(), "Blender not found")
class CamplanWithBlender(unittest.TestCase):
    def test_keyframed_camera_agrees_with_the_pinhole(self):
        tmp = tempfile.mkdtemp(prefix="pwcpb_")
        try:
            code, out = runpw("camplan", EXAMPLE, "--out", tmp, "--blend")
            self.assertEqual(code, 1)  # the framing FAILs; the camera is still written
            self.assertTrue(out["ok"], out)
            self.assertTrue(os.path.isfile(out["blend"]["blend"]))
            self.assertEqual((out["blend"]["frame_start"], out["blend"]["frame_end"]), (1, 97))
            self.assertLess(out["blend"]["max_uv_diff"], 0.01)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
