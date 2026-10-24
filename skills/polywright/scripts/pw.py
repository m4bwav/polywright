#!/usr/bin/env python3
"""polywright CLI: 3D model work for AI agents, one JSON object per command.

Standard library only (Python 3.9+), Windows, macOS and Linux. Blender does the heavy work through pw_bpy.py;
commands that need it say so in the JSON when Blender is missing instead of crashing.

  python pw.py doctor                                  what is installed: Blender, Python libs, CLIs, ComfyUI hosts
  python pw.py inspect FILE [--fast] [--topology]      tris, objects, size, materials, images, UVs, watertight, parts
                                                       (--topology: quads, poles, flipped faces, stacked faces, UV spread)
  python pw.py render FILE --out DIR [--views ..] [--color clay|material|texture] [--size 640]
                                                       orthographic views + contact sheet for a vision model to judge
  python pw.py convert IN OUT [--size-m X] [--scale F] [--ground] [--center] [--level | --tilt-deg D] [--join] [--max-tris N] [--fix-winding] [--draco]
  python pw.py lods IN --out DIR [--ratios 1,0.5,0.25,0.1] [--format glb]
  python pw.py printable IN OUT.stl --size-mm 100 [--wall-mm 1] [--voxel-mm V] [--base-cut-mm 0.6] [--drop a,b] [--seal-mm 1] [--hollow]
  python pw.py union IN OUT.stl                        boolean-union closed parts into one solid
  python pw.py 3mf A.stl [B.stl ..] --out X.3mf        one 3MF, one object per input (AMS colours)
  python pw.py check FILE --target T [--real-size-m X] [--thickness-samples N] targets: python pw.py check --list
  python pw.py new DIR --name N [--kind real|imagined|hybrid] [--targets game-unity,print-fdm]
  python pw.py manifest DIR [--add-output PATH --target T] [--add-source URL --licence L --author A] [--validate]
  python pw.py bpy SCRIPT.py [--blend FILE] [--timeout S] [-- script args]   run your bpy script headless
  python pw.py gen --image FRONT.png [--left L --back B --right R] --out raw.glb [--host URL] [--steps 30]
  python pw.py gen --image IMG.png --workflow trellis2.api.json --out model.glb [--set NODE.input=VALUE]
  python pw.py place --bbox S,W,N,E --out DIR [--dem auto|usgs|terrarium|flat] [--res M] [--print-mm 200]
  python pw.py duel DUEL.json [--out DIR] [--preview] [--check]   two fighters' clay, Canny, depth and pose controls
  python pw.py texture IMG --out DIR [--seamless] [--strength 2]   quick normal/height/roughness maps
  python pw.py framecam PROBLEM.json [--out cameras.json] [--top 3]  grid-search perspective cameras for screen rules
  python pw.py scene FILE --cameras cameras.json --camera NAME --out DIR [--size 1280x720]   scene illustration passes

Environment: POLYWRIGHT_BLENDER (path to blender), POLYWRIGHT_BPY_PYTHON (a Python with the bpy module),
POLYWRIGHT_COMFYUI (comma-separated ComfyUI URLs, default http://127.0.0.1:8188).
"""
import argparse
import glob
import hashlib
import json
import math
import os
import platform
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zlib

VERSION = "0.5.0"
HERE = os.path.dirname(os.path.abspath(__file__))
BPY_SCRIPT = os.path.join(HERE, "pw_bpy.py")
SCENE_SCRIPT = os.path.join(HERE, "pw_scene.py")
REFS = os.path.join(os.path.dirname(HERE), "references")
UA = "polywright/%s (+https://github.com/m4bwav/polywright)" % VERSION


def emit(obj, code=0):
    print(json.dumps(obj, indent=1, default=str))
    return code


# ------------------------------------------------------------------------------------------ finding tools

def _version_key(path):
    m = re.findall(r"(\d+)\.(\d+)(?:\.(\d+))?", path)
    if not m:
        return (0, 0, 0)
    a, b, c = m[-1]
    return (int(a), int(b), int(c or 0))


def blender_candidates():
    cands = []
    for env in ("POLYWRIGHT_BLENDER", "BLENDER"):
        if os.environ.get(env):
            cands.append((os.environ[env], "env " + env))
    w = shutil.which("blender")
    if w:
        cands.append((w, "PATH"))
    system = platform.system()
    pats = []
    if system == "Windows":
        roots = set()
        for v in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
            if os.environ.get(v):
                roots.add(os.environ[v])
        for letter in "CDEFGH":
            for pf in ("Program Files", "Program Files (x86)"):
                p = "%s:\\%s" % (letter, pf)
                if os.path.isdir(p):
                    roots.add(p)
        for r in roots:
            pats.append(os.path.join(r, "Blender Foundation", "Blender*", "blender.exe"))
            pats.append(os.path.join(r, "Steam", "steamapps", "common", "Blender", "blender.exe"))
    elif system == "Darwin":
        pats += ["/Applications/Blender*.app/Contents/MacOS/Blender",
                 os.path.expanduser("~/Applications/Blender*.app/Contents/MacOS/Blender")]
    else:
        pats += ["/snap/bin/blender", "/usr/bin/blender", "/usr/local/bin/blender", "/opt/blender*/blender",
                 os.path.expanduser("~/blender*/blender"), os.path.expanduser("~/.local/bin/blender")]
    found = []
    for pat in pats:
        found += glob.glob(pat)
    for p in sorted(set(found), key=_version_key, reverse=True):
        cands.append((p, "install folder"))
    seen, out = set(), []
    for p, src in cands:
        k = os.path.normcase(os.path.abspath(p))
        if k not in seen and os.path.isfile(p):
            seen.add(k)
            out.append((p, src))
    return out


_BACKEND = None


def backend():
    """('blender', path, version) or ('bpy', python, version) or None."""
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND or None
    py = os.environ.get("POLYWRIGHT_BPY_PYTHON")
    if py:
        try:
            v = subprocess.run([py, "-c", "import bpy;print(bpy.app.version_string)"], capture_output=True, text=True, timeout=120)
            if v.returncode == 0:
                _BACKEND = ("bpy", py, v.stdout.strip().splitlines()[-1])
                return _BACKEND
        except (OSError, subprocess.TimeoutExpired):
            pass
    for path, _src in blender_candidates():
        try:
            v = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=60)
            m = re.search(r"Blender (\d+\.\d+(?:\.\d+)?)", v.stdout or "")
            if m:
                _BACKEND = ("blender", path, m.group(1))
                return _BACKEND
        except (OSError, subprocess.TimeoutExpired):
            continue
    _BACKEND = False
    return None


NOISE = re.compile(r"^(?:\d\d:\d\d\.\d+\s+\w+\s+\|\s+)?(Blender \d|Read prefs|Read blend|Fra:|Saved:|Time:|Info:|Warning: .*unable to open|Blender quit|"
                   r"Color management:|found bundled python|\s*$|register_class|Import finished|Export finished|"
                   r"Writing:|Data are loaded)")


def condense(text, limit=40):
    lines = [ln for ln in (text or "").splitlines() if not NOISE.match(ln)]
    if len(lines) > limit:
        lines = lines[:8] + ["... (%d lines cut) ..." % (len(lines) - limit + 8)] + lines[-(limit - 8):]
    return lines


def run_blender_script(script, script_args, blend=None, timeout=1800):
    be = backend()
    if not be:
        return {"ok": False, "error": "Blender not found. Install Blender (blender.org) or set POLYWRIGHT_BLENDER; `pw.py doctor` shows where it looked."}
    kind, exe, ver = be
    if kind == "blender":
        cmd = [exe, "--background"]
        if blend:
            cmd.append(blend)
        else:
            cmd.append("--factory-startup")
        cmd += ["--python-exit-code", "3", "--python", script, "--"] + script_args
    else:
        cmd = [exe, script, "--"] + script_args
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Blender timed out after %ds" % timeout}
    return {"ok": p.returncode == 0, "exit_code": p.returncode, "seconds": round(time.time() - t0, 1),
            "backend": kind, "blender": ver, "stdout": p.stdout, "stderr": p.stderr}


def bpy_action(action, params, timeout=1800, script=BPY_SCRIPT):
    tmp = tempfile.mkdtemp(prefix="pw_")
    pp, rp = os.path.join(tmp, "params.json"), os.path.join(tmp, "result.json")
    with open(pp, "w", encoding="utf-8") as f:
        json.dump(params, f)
    r = run_blender_script(script, [action, pp, rp], timeout=timeout)
    if os.path.isfile(rp):
        with open(rp, encoding="utf-8") as f:
            res = json.load(f)
    else:
        res = {"ok": False, "action": action, "error": r.get("error") or "Blender exited %s without a result" % r.get("exit_code"),
               "log": condense((r.get("stdout") or "") + "\n" + (r.get("stderr") or ""))}
    shutil.rmtree(tmp, ignore_errors=True)
    return res


# ------------------------------------------------------------------------------------------ sprite camera and passes

def _diamond_residual(base, tiles, s, yaw, elev):
    # front->left edge projects to s*tiles*(-cos yaw, -sin(elev) sin yaw); front->right to s*tiles*(sin yaw, -sin(elev) cos yaw)
    f = base["front"]
    se = math.sin(elev)
    pl = (base["left"]["x"] - f["x"], base["left"]["y"] - f["y"])
    pr = (base["right"]["x"] - f["x"], base["right"]["y"] - f["y"])
    el = (-math.cos(yaw), -se * math.sin(yaw))
    er = (math.sin(yaw), -se * math.cos(yaw))
    return pl, pr, el, er


def fit_diamond(base, tiles):
    """Orthographic sprite camera from one ground diamond (front, left, right corners in image pixels, y down) of a
    square footprint of `tiles` tiles: scale (px per tile), yaw and elevation. Coarse-to-fine search over the two
    angles with the scale solved in closed form; stdlib only."""
    best = None

    def score(yaw, elev):
        pl, pr, el, er = _diamond_residual(base, tiles, 0, yaw, elev)
        num = (pl[0] * el[0] + pl[1] * el[1] + pr[0] * er[0] + pr[1] * er[1]) * tiles
        den = (el[0] ** 2 + el[1] ** 2 + er[0] ** 2 + er[1] ** 2) * tiles * tiles
        s = num / den if den else 0.0
        r2 = sum((pl[i] - s * tiles * el[i]) ** 2 + (pr[i] - s * tiles * er[i]) ** 2 for i in range(2))
        return r2, s

    for step, span, centre in ((1.0, None, None), (0.1, 1.5, None), (0.01, 0.15, None)):
        if best is None:
            yaws = [math.radians(d * step) for d in range(0, int(90 / step) + 1)]
            elevs = [math.radians(5 + d * step) for d in range(0, int(84 / step) + 1)]
        else:
            y0, e0 = math.degrees(best[2]), math.degrees(best[3])
            n = int(span / step)
            yaws = [math.radians(y0 + d * step) for d in range(-n, n + 1)]
            elevs = [math.radians(e0 + d * step) for d in range(-n, n + 1)]
        for yaw in yaws:
            for elev in elevs:
                r2, s = score(yaw, elev)
                if best is None or r2 < best[0]:
                    best = (r2, s, yaw, elev)
    r2, s, yaw, elev = best
    return {"px_per_tile": s, "yaw_deg": math.degrees(yaw), "elevation_deg": math.degrees(elev),
            "rms_px": math.sqrt(r2 / 4.0)}


def _collect_bases(node, path, out, tiles_default):
    if isinstance(node, dict):
        size = node.get("size")
        gb = node.get("groundBase")
        name = node.get("buildingId") or node.get("id") or node.get("name") or path
        if isinstance(gb, dict) and all(k in gb for k in ("front", "left", "right")):
            out.append((name, gb, size))
        elif all(k in node for k in ("front", "left", "right")) and isinstance(node.get("front"), dict):
            out.append((path, node, None))
        for k, v in node.items():
            if k == "levelUpgrades" and isinstance(v, list):
                for i, lv in enumerate(v):
                    if isinstance(lv, dict) and isinstance(lv.get("groundBase"), dict):
                        out.append(("%s@L%d" % (name, i + 2), lv["groundBase"], size))
            elif k != "groundBase":
                _collect_bases(v, "%s.%s" % (path, k), out, tiles_default)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _collect_bases(v, "%s[%d]" % (path, i), out, tiles_default)


def cmd_spritecam(a):
    with open(a.bases, encoding="utf-8") as f:
        data = json.load(f)
    found = []
    _collect_bases(data, "", found, a.tiles)
    rows = []
    for name, gb, size in found:
        if size and isinstance(size, dict) and (size.get("x") != a.tiles or size.get("y") != a.tiles):
            continue
        r = fit_diamond(gb, a.tiles)
        r["name"] = name
        rows.append(r)
    good = [r for r in rows if r["rms_px"] <= a.max_rms]
    if not good:
        return emit({"ok": False, "error": "no %dx%d ground diamonds fit within %.1f px (found %d)" %
                     (a.tiles, a.tiles, a.max_rms, len(rows))}, 1)

    def med(k):
        v = sorted(r[k] for r in good)
        return v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2
    cam = {"source": "pw.py spritecam over %d of %d %dx%d ground diamonds in %s (rms <= %.1f px)" %
                     (len(good), len(rows), a.tiles, a.tiles, os.path.basename(a.bases), a.max_rms),
           "projection": "orthographic", "yaw_deg": round(med("yaw_deg"), 2),
           "elevation_deg": round(med("elevation_deg"), 2), "px_per_tile": round(med("px_per_tile"), 2),
           "yaw_meaning": "angle of the front-left ground edge from screen-left; front corner at world origin, "
                          "footprint along +X (to the right corner) and +Y (to the left corner)",
           "canvas_px": [a.tiles * a.tile_px, a.tiles * a.tile_px], "render_scale": 8, "tile_m": a.tile_m,
           "footprint_tiles": [a.tiles, a.tiles],
           "footprint_centre_px": [a.tiles * a.tile_px / 2, a.tiles * a.tile_px * 0.68],
           "sun_dir": [-0.75, -0.35, 0.85],
           "spread": {k: [round(min(r[k] for r in good), 2), round(max(r[k] for r in good), 2)]
                      for k in ("yaw_deg", "elevation_deg", "px_per_tile")},
           "per_sprite": {r["name"]: {k: round(r[k], 2) for k in ("px_per_tile", "yaw_deg", "elevation_deg", "rms_px")}
                          for r in rows}}
    if a.like:
        hit = [r for r in rows if r["name"] == a.like]
        if hit:
            gb = next(g for n, g, s in found if n == a.like)
            cam["footprint_centre_px"] = [round((gb["left"]["x"] + gb["right"]["x"]) / 2, 1),
                                          round((gb["left"]["y"] + gb["right"]["y"]) / 2, 1)]
            cam["px_per_tile_like"] = round(hit[0]["px_per_tile"], 2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(cam, f, indent=2)
    res = {k: v for k, v in cam.items() if k != "per_sprite"}
    res.update(ok=True, action="spritecam", out=a.out,
               next="pw.py sprite <model.blend> --camera %s --out <dir>: renders through this camera" % (a.out or "camera.json"))
    return emit(res)


def line_pass(out_dir):
    """Line art from a sprite render's id, normal and depth passes: an edge where the part, the surface direction
    or the distance jumps. Needs numpy and Pillow; returns None without them."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return None
    ld = lambda n: np.asarray(Image.open(os.path.join(out_dir, n + ".png")).convert("RGBA")).astype(float) / 255.0
    if not all(os.path.isfile(os.path.join(out_dir, n + ".png")) for n in ("id", "normal", "depth")):
        return None
    idp, nrm, dep = ld("id"), ld("normal"), ld("depth")
    alpha = dep[..., 3] > 0.5

    def jump(arr, thr):
        dx = np.abs(np.diff(arr, axis=1, prepend=arr[:, :1]))
        dy = np.abs(np.diff(arr, axis=0, prepend=arr[:1]))
        m = np.maximum(dx, dy)
        return (m.max(axis=-1) if m.ndim == 3 else m) > thr
    edge = jump(idp[..., :3], 0.2) | jump(nrm[..., :3], 0.25) | jump(dep[..., 0], 0.02)
    inner = np.zeros_like(alpha)
    inner[1:-1, 1:-1] = alpha[1:-1, 1:-1] & alpha[:-2, 1:-1] & alpha[2:, 1:-1] & alpha[1:-1, :-2] & alpha[1:-1, 2:]
    edge = (edge & alpha) | (alpha & ~inner)
    img = np.zeros(dep.shape[:2] + (4,), np.uint8)
    img[..., :3] = 40
    img[..., 3] = edge * 255
    path = os.path.join(out_dir, "line.png")
    Image.fromarray(img).save(path)
    return path


def cmd_sprite(a):
    with open(a.camera, encoding="utf-8") as f:
        cam = json.load(f)
    split = lambda t: [v.strip() for v in (t or "").split(",") if v.strip()]
    params = {"file": os.path.abspath(a.file), "out": os.path.abspath(a.out), "camera": cam,
              "passes": split(a.passes), "frames": a.frames, "frame_passes": split(a.frame_passes),
              "samples": a.samples, "scale": a.scale, "hide": split(a.hide), "gpu": a.gpu, "pos_extent": a.pos_extent}
    if a.footprint_m:
        params["footprint_m"] = floats(a.footprint_m, 2)
    res = bpy_action("sprite", params, timeout=a.timeout)
    if res.get("ok") and "line" in split(a.passes) + ["line"] and not a.no_line:
        res["line"] = line_pass(params["out"]) or "skipped (needs numpy, Pillow and the id, normal, depth passes)"
    if res.get("ok"):
        res["next"] = ("Read the passes at 1x and the beauty at canvas size beside the game's real sprites; paint "
                       "over beauty with Canny of clay as control (an image model with a ControlNet); sprite.json "
                       "carries groundBase, ring rims and ID colours for a geometry check of the painting")
    return emit(res, 0 if res.get("ok") else 1)


# ------------------------------------------------------------------------------------------ scene illustrations

def pinhole(pos, target, lens_mm, size, sensor_mm=36.0):
    """A perspective camera as Blender builds one from a position, an aim point and a lens (+Z up, sensor fit AUTO:
    the sensor spans the longer image side). Returns project(point) -> (x, y, depth): x and y as fractions of the
    image from its top-left corner, depth along the view axis in metres; x and y are None behind the camera.
    Returns None when the aim is straight up or down."""
    d = [target[i] - pos[i] for i in range(3)]
    n = math.sqrt(sum(v * v for v in d))
    rn = math.hypot(d[0], d[1])
    if n == 0 or rn < 1e-9 * n:
        return None
    f = [v / n for v in d]
    r = [d[1] / rn, -d[0] / rn, 0.0]  # forward x world up
    u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]]
    w, h = size
    k = lens_mm / sensor_mm * max(w, h)

    def project(p):
        q = [p[i] - pos[i] for i in range(3)]
        z = sum(q[i] * f[i] for i in range(3))
        if z <= 1e-6:
            return None, None, z
        x = sum(q[i] * r[i] for i in range(3)) / z
        y = sum(q[i] * u[i] for i in range(3)) / z
        return 0.5 + k * x / w, 0.5 - k * y / h, z
    return project


def _axis(spec, what):
    """A search axis: a number (fixed) or [low, high, step]."""
    if isinstance(spec, (int, float)):
        return [float(spec)]
    lo, hi, step = (float(v) for v in spec)
    if step <= 0 or hi < lo:
        raise ValueError("%s: [low, high, step] needs low <= high and step > 0, got %s" % (what, spec))
    return [lo + i * step for i in range(int(round((hi - lo) / step)) + 1)]


def framecam(prob, top=3, max_evals=3_000_000):
    """Grid-search perspective cameras for a scene illustration: every named point in `boxes` must land in its
    screen box (x and y fraction ranges, y down), every `keep_in_frame` point inside the frame (less `margin`),
    every `keep_out_of_bands` point outside every band (the UI's text areas), all in front of the camera. Among the
    cameras that pass, the biggest `size_measure` wins (two points' screen distance in pixels). Returns
    (cameras, stats) or raises ValueError with what blocked the search."""
    pts = {k: [float(c) for c in v] for k, v in prob["points"].items()}
    w, h = prob.get("size", [1920, 1080])
    sensor = float(prob.get("sensor_mm", 36.0))
    boxes = prob.get("boxes", {})
    keep_in = prob.get("keep_in_frame", [])
    bands = prob.get("bands", [])
    keep_out = prob.get("keep_out_of_bands", [])
    measure = prob.get("size_measure")
    margin = float(prob.get("margin", 0.0))
    names = set(boxes) | set(keep_in) | set(keep_out) | set(measure or [])
    unknown = sorted(names - set(pts))
    if unknown:
        raise ValueError("unknown point names %s (points has %s)" % (unknown, sorted(pts)))
    if not measure or len(measure) != 2:
        raise ValueError("size_measure must name two points (their screen distance is maximised)")
    s = prob["search"]
    grid = {"pos": [_axis(v, "search.pos[%d]" % i) for i, v in enumerate(s["pos"])],
            "target": [_axis(v, "search.target[%d]" % i) for i, v in enumerate(s["target"])],
            "lens": _axis(s.get("lens_mm", 35), "search.lens_mm")}
    count = 1
    for ax in grid["pos"] + grid["target"] + [grid["lens"]]:
        count *= len(ax)
    if count > max_evals:
        raise ValueError("search has %d cameras, over the %d limit: use coarser steps, then search again around "
                         "the best" % (count, max_evals))
    rules = (["front"] + ["box:" + n for n in boxes] + ["in_frame:" + n for n in keep_in]
             + ["out_of_bands:" + n for n in keep_out])
    alone = dict.fromkeys(rules, 0)
    hits = []
    for px in grid["pos"][0]:
        for py in grid["pos"][1]:
            for pz in grid["pos"][2]:
                for tx in grid["target"][0]:
                    for ty in grid["target"][1]:
                        for tz in grid["target"][2]:
                            pos, tgt = (px, py, pz), (tx, ty, tz)
                            # the projection scales about the centre with the lens: project once at 36 mm
                            proj = pinhole(pos, tgt, sensor, (w, h), sensor)
                            if proj is None:
                                continue
                            base = {n: proj(pts[n]) for n in names}
                            for lens in grid["lens"]:
                                ok = _framecam_rules(base, lens / sensor, boxes, keep_in, bands, keep_out, margin, alone)
                                if ok:
                                    a, b = (base[m] for m in measure)
                                    size = lens / sensor * math.hypot((a[0] - b[0]) * w, (a[1] - b[1]) * h)
                                    hits.append((size, pos, tgt, lens))
    stats = {"searched": count, "passed": len(hits), "passed_alone": alone}
    if not hits:
        never = [r for r in rules if alone[r] == 0]
        rare = min(rules, key=lambda r: alone[r])
        raise ValueError("no camera in the search meets every rule; %s (%d of %d cameras pass it alone); widen the "
                         "search or relax the rule" % (("never met: " + ", ".join(never)) if never else
                                                       "rarest: " + rare, alone[rare], count))
    hits.sort(key=lambda t: -t[0])
    steps = [ax[1] - ax[0] for ax in grid["pos"] if len(ax) > 1]
    spread = 1.5 * max(steps) if steps else 0.0
    chosen = []
    for size, pos, tgt, lens in hits:
        if spread == 0 or all(math.dist(pos, c[1]) > spread for c in chosen):
            chosen.append((size, pos, tgt, lens))
        if len(chosen) == top:
            break
    best = chosen[0]
    values = list(best[1]) + list(best[2]) + [best[3]]
    labels = ["pos.x", "pos.y", "pos.z", "target.x", "target.y", "target.z", "lens_mm"]
    stats["best_at_search_edge"] = [lab for lab, ax, v in zip(labels, grid["pos"] + grid["target"] + [grid["lens"]], values)
                                    if len(ax) > 1 and v in (ax[0], ax[-1])]
    cams = []
    for size, pos, tgt, lens in chosen:
        proj = pinhole(pos, tgt, lens, (w, h), sensor)
        cams.append({"pos": [round(v, 3) for v in pos], "target": [round(v, 3) for v in tgt], "lens_mm": round(lens, 2),
                     "size_px": round(size, 1),
                     "points_frac": {n: [round(v, 4) for v in proj(pts[n])[:2]] if proj(pts[n])[0] is not None else None
                                     for n in sorted(names)}})
    return cams, stats


def _framecam_rules(base, zoom, boxes, keep_in, bands, keep_out, margin, alone):
    """Check one camera; count each rule it passes in `alone` (to say which rule blocks a search)."""
    def at(n):
        x, y, z = base[n]
        if x is None:
            return None
        return 0.5 + (x - 0.5) * zoom, 0.5 + (y - 0.5) * zoom
    ok = all(base[n][0] is not None for n in base)
    alone["front"] += ok
    for n, b in boxes.items():
        p = at(n)
        good = p is not None and b["x"][0] <= p[0] <= b["x"][1] and b["y"][0] <= p[1] <= b["y"][1]
        alone["box:" + n] += good
        ok = ok and good
    for n in keep_in:
        p = at(n)
        good = p is not None and margin <= p[0] <= 1 - margin and margin <= p[1] <= 1 - margin
        alone["in_frame:" + n] += good
        ok = ok and good
    for n in keep_out:
        p = at(n)
        good = p is not None and not any(b["x"][0] <= p[0] <= b["x"][1] and b["y"][0] <= p[1] <= b["y"][1] for b in bands)
        alone["out_of_bands:" + n] += good
        ok = ok and good
    return ok


def cmd_framecam(a):
    try:
        with open(a.problem, encoding="utf-8") as f:
            prob = json.load(f)
        cams, stats = framecam(prob, top=a.top, max_evals=a.max_evals)
    except (OSError, KeyError, ValueError, TypeError) as e:
        return emit({"ok": False, "action": "framecam", "error": "%s%s" % ("missing key " if isinstance(e, KeyError) else "", e)}, 1)
    presets = {"%s_%d" % (a.name, i + 1): c for i, c in enumerate(cams)}
    if a.out:
        doc = {}
        if os.path.isfile(a.out):
            with open(a.out, encoding="utf-8") as f:
                doc = json.load(f)
        doc.setdefault("cameras", {}).update(presets)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1)
    return emit({"ok": True, "action": "framecam", "out": a.out, "cameras": presets, **stats,
                 "hint": ("the best camera sits on the edge of the search in %s: widen it there"
                          % ", ".join(stats["best_at_search_edge"])) if stats["best_at_search_edge"] else None,
                 "next": "pw.py scene <scene.blend> --cameras %s --camera %s_1 --out <dir> --passes clay: read the clay "
                         "of each before the full passes" % (a.out or "cameras.json", a.name)})


SCENE_PASSES = ("clay", "beauty", "depth", "normal", "id")


def sky_pass(out_dir, top, horizon):
    """Repaint the sky of a scene's beauty with a vertical gradient (top colour overhead to horizon colour at the
    lowest sky row) through the id pass's alpha, 1 px feather. Writes beauty_sky.png; needs numpy and Pillow."""
    try:
        import numpy as np
        from PIL import Image, ImageFilter
    except ImportError:
        return None
    paths = [os.path.join(out_dir, n + ".png") for n in ("beauty", "id")]
    if not all(os.path.isfile(p) for p in paths):
        return None
    beauty = np.asarray(Image.open(paths[0]).convert("RGB")).astype(float)
    ida = Image.open(paths[1]).convert("RGBA").split()[3]
    sky = 1.0 - np.asarray(ida.filter(ImageFilter.GaussianBlur(1.0))).astype(float)[..., None] / 255.0
    h = beauty.shape[0]
    rows = np.flatnonzero((np.asarray(ida) == 0).mean(axis=1) > 0.02)
    low = rows.max() + 1 if rows.size else h // 2
    t = np.clip(np.arange(h) / max(1, low), 0, 1)[:, None, None] ** 1.6
    grad = np.array(top, float) * (1 - t) + np.array(horizon, float) * t
    out = beauty * (1 - sky) + np.broadcast_to(grad, beauty.shape) * sky
    path = os.path.join(out_dir, "beauty_sky.png")
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)
    return path


def cmd_scene(a):
    split = lambda t: [v.strip() for v in (t or "").split(",") if v.strip()]
    try:
        with open(a.cameras, encoding="utf-8") as f:
            cams = json.load(f)
    except (OSError, ValueError) as e:
        return emit({"ok": False, "action": "scene", "error": "cannot read %s: %s" % (a.cameras, e)}, 2)
    presets = cams.get("cameras") or {}
    if a.camera not in presets:
        return emit({"ok": False, "action": "scene", "error": "no camera %r in %s" % (a.camera, a.cameras),
                     "known": sorted(presets)}, 2)
    preset = presets[a.camera]
    problems = ["camera %s has no %s" % (a.camera, k) for k in ("pos", "target") if len(preset.get(k) or []) != 3]
    try:
        size = [int(v) for v in a.size.lower().split("x")]
        if len(size) != 2 or min(size) < 8:
            raise ValueError
    except ValueError:
        problems.append("--size must be WxH, such as 1280x720")
        size = None
    passes = split(a.passes)
    bad = [p for p in passes if p not in SCENE_PASSES]
    if bad or not passes:
        problems.append("unknown pass %s (%s)" % (",".join(bad) or "none given", ", ".join(SCENE_PASSES)))
    sky = None
    if a.sky:
        try:
            sky = [floats(v, 3) for v in a.sky.split(":")]
            if len(sky) != 2:
                raise ValueError
        except ValueError:
            problems.append("--sky must be TOP:HORIZON as R,G,B:R,G,B (0-255)")
    if problems:
        return emit({"ok": False, "action": "scene", "error": "; ".join(problems)}, 2)
    params = {"file": os.path.abspath(a.file), "out": os.path.abspath(a.out), "camera_name": a.camera, "camera": preset,
              "sun": cams.get("sun"), "world": cams.get("sky"), "size": size, "passes": passes, "samples": a.samples,
              "hide": split(a.hide), "gpu": a.gpu, "keep_lights": a.keep_lights}
    res = bpy_action("scene", params, timeout=a.timeout, script=SCENE_SCRIPT)
    if res.get("ok") and not a.no_line:
        res["line"] = line_pass(params["out"]) or "skipped (needs numpy, Pillow and the id, normal, depth passes)"
    if res.get("ok") and sky:
        res["sky"] = sky_pass(params["out"], *sky) or "skipped (needs numpy, Pillow and the beauty and id passes)"
    if res.get("ok"):
        res["next"] = ("Read clay and depth first: is the hero where framecam put it, does the depth pass have contrast "
                       "near the hero? Then paint beauty (or clay) with depth or line as control at this size, and "
                       "gate the painting against scene.json (ring rims, points, id colours)")
    return emit(res, 0 if res.get("ok") else 1)


# ------------------------------------------------------------------------------------------ doctor

PY_MODULES = ["numpy", "PIL", "trimesh", "manifold3d", "pymeshlab", "open3d", "scipy", "shapely", "xatlas",
              "pygltflib", "build123d", "cadquery", "rembg"]
CLIS = ["gltf-transform", "gltfpack", "npx", "colmap", "openscad", "meshlab", "ffmpeg", "glomap",
        "bambu-studio", "prusa-slicer", "orca-slicer", "freecadcmd", "usdzconvert", "assimp"]


def comfy_hosts(explicit=None):
    if explicit:
        return [h.rstrip("/") for h in explicit.split(",") if h.strip()]
    env = os.environ.get("POLYWRIGHT_COMFYUI")
    if env:
        return [h.strip().rstrip("/") for h in env.split(",") if h.strip()]
    return ["http://127.0.0.1:8188"]


def http_json(url, data=None, timeout=10, headers=None):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def cmd_doctor(a):
    import importlib.util
    res = {"polywright": VERSION, "os": platform.platform(), "python": sys.version.split()[0]}
    be = backend()
    res["blender"] = {"backend": be[0], "path": be[1], "version": be[2]} if be else None
    res["blender_candidates"] = [p for p, _ in blender_candidates()]
    res["python_modules"] = {m: bool(importlib.util.find_spec(m)) for m in PY_MODULES}
    clis = {c: shutil.which(c) for c in CLIS}
    if platform.system() == "Windows":
        for c, rel in (("bambu-studio", r"Bambu Studio\bambu-studio.exe"), ("prusa-slicer", r"Prusa3D\PrusaSlicer\prusa-slicer-console.exe"),
                       ("orca-slicer", r"OrcaSlicer\orca-slicer.exe")):
            if not clis[c]:
                for root in ("C:\\Program Files", "D:\\Program Files"):
                    if os.path.isfile(os.path.join(root, rel)):
                        clis[c] = os.path.join(root, rel)
    res["clis"] = {k: v for k, v in clis.items() if v}
    res["clis_missing"] = [k for k, v in clis.items() if not v]
    hosts = []
    for h in comfy_hosts(a.host):
        info = {"url": h, "up": False}
        try:
            st = http_json(h + "/system_stats", timeout=4)
            info["up"] = True
            info["comfyui"] = st.get("system", {}).get("comfyui_version")
            ck = http_json(h + "/models/checkpoints", timeout=6)
            info["3d_checkpoints"] = [c for c in ck if re.search(r"hunyuan3d|trellis|triposg|sf3d|spar3d|step1x", c, re.I)]
        except Exception as e:  # down, refused or not ComfyUI
            info["error"] = str(e)[:120]
        hosts.append(info)
    res["comfyui"] = hosts
    can = {"inspect_render_convert_printable": bool(be),
           "inspect_fallback": res["python_modules"]["trimesh"],
           "gen_image_to_3d": any(h.get("3d_checkpoints") for h in hosts),
           "texture_maps": res["python_modules"]["numpy"] and res["python_modules"]["PIL"],
           "place": True}
    res["can"] = can
    res["next"] = []
    if not be:
        res["next"].append("Install Blender 4.5 LTS or newer (5.2 LTS preferred) or set POLYWRIGHT_BLENDER to blender(.exe)")
    if not can["gen_image_to_3d"]:
        res["next"].append("For local image-to-3D: ComfyUI with the Hunyuan3D-2 checkpoints, or a hosted generator (see polywright-generate)")
    return emit(res)


# ------------------------------------------------------------------------------------------ inspect (with stdlib fallback)

def glb_quick(path):
    """Counts and bounds from a .glb without any library (accessor min/max)."""
    with open(path, "rb") as f:
        magic, _ver, _len = struct.unpack("<4sII", f.read(12))
        if magic != b"glTF":
            raise ValueError("not a GLB")
        clen, ctype = struct.unpack("<I4s", f.read(8))
        g = json.loads(f.read(clen).decode("utf-8"))
    acc = g.get("accessors", [])
    tris, lo, hi = 0, [math.inf] * 3, [-math.inf] * 3
    for m in g.get("meshes", []):
        for pr in m.get("primitives", []):
            pos = acc[pr["attributes"]["POSITION"]]
            if pr.get("indices") is not None:
                tris += acc[pr["indices"]]["count"] // 3
            else:
                tris += pos["count"] // 3
            if "min" in pos:
                lo = [min(lo[i], pos["min"][i]) for i in range(3)]
                hi = [max(hi[i], pos["max"][i]) for i in range(3)]
    return {"tris": tris, "meshes": len(g.get("meshes", [])), "nodes": len(g.get("nodes", [])),
            "materials": [m.get("name", "") for m in g.get("materials", [])],
            "images": len(g.get("images", [])), "dims_mesh_space": [round(hi[i] - lo[i], 5) for i in range(3)] if lo[0] != math.inf else None,
            "note": "stdlib read: node transforms ignored, no topology checks; install Blender or trimesh for more"}


def stl_quick(path):
    with open(path, "rb") as f:
        head = f.read(84)
        n = struct.unpack("<I", head[80:84])[0]
        size = os.path.getsize(path)
        if 84 + n * 50 != size:
            raise ValueError("ASCII STL; install trimesh or Blender to inspect it")
        lo, hi = [math.inf] * 3, [-math.inf] * 3
        for _ in range(n):
            rec = f.read(50)
            v = struct.unpack("<12f", rec[:48])
            for k in range(3):
                for i in range(3):
                    c = v[3 + k * 3 + i]
                    if c < lo[i]:
                        lo[i] = c
                    if c > hi[i]:
                        hi[i] = c
    return {"tris": n, "dims": [round(hi[i] - lo[i], 5) for i in range(3)], "note": "stdlib read; no topology checks"}


def trimesh_inspect(path):
    import trimesh
    sc = trimesh.load(path, force="scene")
    geoms = list(sc.dump()) if hasattr(sc, "dump") else [sc]
    tris = sum(len(g.faces) for g in geoms if hasattr(g, "faces"))
    lo, hi = sc.bounds if sc.bounds is not None else ([0, 0, 0], [0, 0, 0])
    wt = all(getattr(g, "is_watertight", False) for g in geoms) and bool(geoms)
    res = {"backend": "trimesh", "objects": len(geoms), "tris": int(tris), "dims": [round(float(hi[i] - lo[i]), 5) for i in range(3)],
           "watertight": wt}
    if wt:
        res["volume"] = round(float(sum(g.volume for g in geoms)), 6)
        res["parts"] = int(sum(len(g.split(only_watertight=False)) for g in geoms))
    return res


def inspect_file(path, fast=False, thickness_min=None, thickness_samples=20000, topology=False):
    if not os.path.isfile(path):
        return {"ok": False, "error": "file not found: %s" % path}
    ext = os.path.splitext(path)[1].lower()
    if backend() and ext != ".3mf":
        params = {"file": os.path.abspath(path), "deep": not fast, "topology": topology}
        if thickness_min:
            params.update(thickness_min=thickness_min, thickness_samples=thickness_samples)
        res = bpy_action("inspect", params)
        res.setdefault("backend", "blender")
    else:
        try:
            import trimesh  # noqa: F401
            res = trimesh_inspect(path)
            res["ok"] = True
        except ImportError:
            try:
                res = glb_quick(path) if ext == ".glb" else stl_quick(path) if ext == ".stl" else None
                if res is None:
                    return {"ok": False, "error": "no Blender and no trimesh: cannot read %s" % ext}
                res["ok"] = True
                res["backend"] = "stdlib"
            except (ValueError, struct.error, OSError) as e:
                return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": "trimesh failed: %s" % e}
        if topology:
            res["topology"] = None
            res["topology_note"] = "the topology report needs Blender (pw.py doctor)"
    res["file_bytes"] = os.path.getsize(path)
    return res


def cmd_inspect(a):
    res = inspect_file(a.file, a.fast, topology=a.topology)
    return emit(res, 0 if res.get("ok") else 1)


def cmd_render(a):
    params = {"file": os.path.abspath(a.file), "out": os.path.abspath(a.out), "size": a.size, "color": a.color,
              "engine": a.engine, "views": a.views.split(","), "sheet": not a.no_sheet, "cols": a.cols}
    res = bpy_action("render", params)
    if res.get("ok"):
        res["next"] = "Read sheet.png (one image) and judge silhouette, proportions, scale, missing parts, shading artifacts"
    return emit(res, 0 if res.get("ok") else 1)


def cmd_match(a):
    pt = lambda t: [float(v) for v in t.split(",")]
    W, H = (int(v) for v in a.size.lower().split("x"))
    if a.still:
        try:
            from PIL import Image
            W, H = Image.open(a.still).size
        except ImportError:
            return emit({"ok": False, "error": "--still needs Pillow (pip install pillow)"}, 1)
    params = {"file": os.path.abspath(a.file), "out": os.path.abspath(a.out), "size": [W, H],
              "anchor_px": pt(a.anchor_px), "anchor_local": pt(a.anchor_local), "aim_px": pt(a.aim_px),
              "aim_local": pt(a.aim_local), "depth": a.depth, "lens": a.lens, "horizon": a.horizon, "roll": a.roll,
              "samples": a.samples, "engine": a.engine, "gpu": a.gpu, "sun_dir": pt(a.sun_dir), "keep_lights": a.keep_lights}
    res = bpy_action("match", params)
    if res.get("ok") and a.still:
        res.update(paste_and_mask(a.still, res["out"], [pt(b) for b in a.hide], a.grow, [pt(b) for b in a.mask_add]))
    if res.get("ok"):
        res["next"] = ("Read the paste crop at full size: shape, size in frame, aim; then blend inside the mask with a "
                       "low-denoise image edit (polywright hub, 'Compose a model into a picture')")
    return emit(res, 0 if res.get("ok") else 1)


def floats(t, n=None):
    v = [float(x) for x in str(t).split(",")]
    if n and len(v) != n:
        raise ValueError("%r: expected %d comma-separated numbers" % (t, n))
    return v


def cmd_turnaround(a):
    W, H = (int(v) for v in a.size.lower().split("x"))
    params = {"file": os.path.abspath(a.file), "out": os.path.abspath(a.out), "yaw": a.yaw, "height_m": a.height_m,
              "views": [v.strip() for v in a.views.split(",") if v.strip()], "size": [W, H], "lens": a.lens,
              "samples": a.samples, "grey": a.grey, "elev": a.elev, "gpu": a.gpu, "sheet": not a.no_sheet}
    res = bpy_action("turnaround", params, timeout=a.timeout)
    if res.get("ok"):
        res["next"] = ("Read sheet.png next to the source photo: markings, colour, nothing invented. The views are a "
                       "video model's reference pictures (one figure per picture; H3 --ref)")
    return emit(res, 0 if res.get("ok") else 1)


def cmd_mark(a):
    try:
        params = {"file": os.path.abspath(a.file), "out": os.path.abspath(a.out), "yaw": a.yaw,
                  "height_m": a.height_m, "longest_m": a.longest_m, "erase": a.erase, "head_frac": a.head_frac,
                  "front_dot": a.front_dot, "text": a.text, "colour": floats(a.colour, 3), "font": a.font,
                  "text_frac": a.text_frac, "width_frac": a.width_frac, "text_dx": a.text_dx, "text_dz": a.text_dz}
        if a.recolour:
            h, s, v = floats(a.recolour, 3)
            params["recolour"] = {"hue": h, "sat": s, "val": v, "from_hue": floats(a.from_hue, 2),
                                  "min_sat": a.min_sat, "min_val": a.min_val}
    except ValueError as e:
        return emit({"ok": False, "error": str(e)}, 2)
    if not (a.height_m or a.longest_m):
        params["height_m"] = None
    res = bpy_action("mark", params, timeout=a.timeout)
    if res.get("ok"):
        res["next"] = "turnaround the output and compare it with the photo: the marking's size and place, the colour"
    return emit(res, 0 if res.get("ok") else 1)


def loop_still(png, dst, frames, fps):
    ff = shutil.which("ffmpeg")
    if not ff:
        return {"skipped": "ffmpeg not found"}
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(fps), "-i", png,
                        "-frames:v", str(frames), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", dst],
                       capture_output=True, text=True)
    return dst if r.returncode == 0 and os.path.isfile(dst) else {"error": (r.stderr or "")[-300:]}


def cmd_lineup(a):
    try:
        layout = json.load(open(a.layout, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return emit({"ok": False, "error": "layout: %s" % e}, 2)
    base = os.path.dirname(os.path.abspath(a.layout))
    for f in layout.get("figures", []):
        f["file"] = os.path.abspath(os.path.join(base, f.get("file") or f.get("glb", "")))
        if not os.path.isfile(f["file"]):
            return emit({"ok": False, "error": "figure file not found: %s" % f["file"]}, 1)
    if not layout.get("figures") or "cam" not in layout or "aim" not in layout:
        return emit({"ok": False, "error": "layout needs figures, cam and aim (see cli.md)"}, 2)
    out = os.path.abspath(a.out)
    res = bpy_action("lineup", {"layout": layout, "out": out, "samples": a.samples, "preview": a.preview}, timeout=a.timeout)
    if not res.get("ok"):
        return emit(res, 1)
    vids = {}
    for n in [int(x) for x in a.frames.split(",") if x.strip()] if a.frames and not a.preview else []:
        for name in ("depth", "clay", "mask"):
            png = res["passes"].get(name)
            if png:
                vids["%s_%d" % (name, n)] = loop_still(png, os.path.join(out, "control_%s_%s_%df.mp4" % (a.card, name, n)), n, a.fps)
    if vids:
        res["videos"] = vids
    order = sorted(res["boxes_px"].items(), key=lambda kv: (kv[1][0] + kv[1][2]) / 2)
    res["left_to_right"] = [k for k, _ in order]
    res["next"] = ("Read colour.png: who stands where, every marking readable, nothing cut by the frame. colour.png is a "
                   "guide frame at 0 (H3 guides). Do not run the looped depth video as a control over moving action: the figures freeze on their spots and double")
    return emit(res)


def paste_and_mask(still, render, hide, grow, mask_add):
    """Alpha-composite the render over the still (minus `hide` boxes: whatever stands in front of the model,
    such as the fist holding it) and write a blend mask: the render's alpha grown by `grow` px, plus ellipses."""
    from PIL import Image, ImageDraw, ImageFilter
    st = Image.open(still).convert("RGBA")
    r = Image.open(render).convert("RGBA")
    alpha = r.getchannel("A")
    d = ImageDraw.Draw(alpha)
    for b in hide:
        d.rectangle([int(v) for v in b], fill=0)
    r.putalpha(alpha)
    st.alpha_composite(r)
    stem = os.path.splitext(render)[0]
    paste, mask = stem + "_paste.png", stem + "_mask.png"
    st.convert("RGB").save(paste)
    m = alpha.point(lambda v: 255 if v > 8 else 0)
    if grow:
        m = m.filter(ImageFilter.MaxFilter(2 * int(grow) + 1))
    d = ImageDraw.Draw(m)
    for b in mask_add:
        d.ellipse([int(v) for v in b], fill=255)
    m.save(mask)
    return {"paste": paste, "mask": mask, "mask_bbox": m.getbbox()}


def cmd_convert(a):
    params = {"file": os.path.abspath(a.input), "out": os.path.abspath(a.output), "scale": a.scale, "size_m": a.size_m,
              "ground": a.ground, "center": a.center, "join": a.join, "max_tris": a.max_tris, "ratio": a.ratio,
              "apply": a.apply, "uv": a.uv, "draco": a.draco, "export_scale": a.export_scale, "fbx_bake_axes": a.fbx_bake_axes,
              "level": a.level, "tilt_deg": a.tilt_deg, "max_tilt_deg": a.max_tilt_deg, "fix_winding": a.fix_winding}
    res = bpy_action("convert", params)
    return emit(res, 0 if res.get("ok") else 1)


def cmd_lods(a):
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.input))[0]
    out = []
    for i, r in enumerate(float(x) for x in a.ratios.split(",")):
        path = os.path.join(os.path.abspath(a.out), "%s_LOD%d.%s" % (stem, i, a.format))
        res = bpy_action("convert", {"file": os.path.abspath(a.input), "out": path, "ratio": r if r < 1 else None, "apply": True})
        out.append({"lod": i, "ratio": r, "path": path, "ok": res.get("ok"), "tris": res.get("tris"), "error": res.get("error")})
    return emit({"ok": all(o["ok"] for o in out), "lods": out,
                 "note": "Unity: name LOD children <name>_LOD0.. for automatic LOD groups; Unreal: import with Auto Generate LODs off and add these; three.js: THREE.LOD"})


def cmd_printable(a):
    params = {"file": os.path.abspath(a.input), "out": os.path.abspath(a.output), "size_mm": a.size_mm, "size_axis": a.size_axis,
              "wall_mm": a.wall_mm, "voxel_mm": a.voxel_mm, "base_cut_mm": a.base_cut_mm, "max_tris": a.max_tris,
              "drop": [d for d in (a.drop or "").split(",") if d], "up": a.up, "remesh": not a.no_remesh,
              "planar": not a.no_planar, "hollow": a.hollow, "seal_mm": a.seal_mm,
              "blend": os.path.abspath(a.blend) if a.blend else None}
    res = bpy_action("printable", params, timeout=a.timeout)
    if res.get("ok"):
        res["next"] = "render it (pw.py render) and compare with the source; then check --target print-fdm; slicer last"
    return emit(res, 0 if res.get("ok") and res.get("watertight") else 1)


def cmd_union(a):
    res = bpy_action("union", {"file": os.path.abspath(a.input), "out": os.path.abspath(a.output), "scale": a.scale,
                               "voxel_fallback_mm": a.voxel_fallback, "solver": a.solver}, timeout=a.timeout)
    return emit(res, 0 if res.get("ok") and res.get("watertight") else 1)


def cmd_3mf(a):
    """One 3MF from one or more meshes, each its own object (one filament each on a multi-colour printer)."""
    try:
        import trimesh
    except ImportError:
        return emit({"ok": False, "error": "3mf needs trimesh (pip install trimesh); or let the slicer CLI make it"}, 1)
    sc = trimesh.Scene()
    objs = []
    for path in a.inputs:
        m = trimesh.load(path, force="mesh")
        if a.scale != 1.0:
            m.apply_scale(a.scale)
        name = os.path.splitext(os.path.basename(path))[0]
        sc.add_geometry(m, node_name=name, geom_name=name)
        objs.append({"name": name, "tris": int(len(m.faces)), "watertight": bool(m.is_watertight),
                     "dims_mm": [round(float(x), 3) for x in m.extents]})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    sc.export(a.out)
    import zipfile
    with zipfile.ZipFile(a.out) as z:
        bad = z.testzip()
    return emit({"ok": bad is None, "out": os.path.abspath(a.out), "objects": objs, "units": "millimetre",
                 "note": "geometry only: the slicer applies its defaults; set printer, filament and process there"},
                0 if bad is None else 1)


# ------------------------------------------------------------------------------------------ check against a target

def load_targets():
    with open(os.path.join(REFS, "targets.json"), encoding="utf-8") as f:
        return json.load(f)


TOPOLOGY_RULES = ("max_winding_mismatch", "max_duplicate_faces", "max_ngons", "max_pole_valence", "max_uv_spread")


def topology_rule(name, limit, t):
    """(passed, detail) for one topology rule of a target. All are warnings: the fix is a modelling call."""
    if name == "max_winding_mismatch":
        n = t.get("winding_mismatch", 0)
        return n <= limit, ("%d edges where two faces wind against each other (flipped faces: a renderer that culls back "
                            "faces shows holes there); pw.py convert --fix-winding flips them back" % n)
    if name == "max_duplicate_faces":
        n = t.get("duplicate_faces", 0)
        return n <= limit, "%d faces share all corners with another face (double-sided copies or stacked faces: they z-fight and cost twice)" % n
    if name == "max_ngons":
        n = t.get("ngons", 0)
        return n <= limit, "%d faces with more than four sides (importers triangulate them their own way)" % n
    if name == "max_pole_valence":
        if t.get("quad_share", 0) < 0.5:
            return "pass", "not judged: %.0f%% quads; poles matter on quad meshes that bend" % (100 * t.get("quad_share", 0))
        v = t.get("max_pole_valence", 0)
        return v <= limit, "largest pole %d edges (limit %d near joints of a mesh that bends); poles %s" % (v, limit, t.get("poles"))
    if name == "max_uv_spread":
        s = t.get("uv_spread")
        if s is None:
            return "pass", "no UVs to judge"
        return s <= limit, ("texel density p95/p5 = %.2f (limit %s, uncalibrated: 3 of 10 real UV-mapped meshes went over 2.5); "
                            "uneven density blurs some parts and wastes texture on others" % (s, limit))
    return "unchecked", "unknown rule"


def cmd_check(a):
    targets = load_targets()
    if a.list or not a.target:
        return emit({"targets": {k: v.get("about", "") for k, v in targets["targets"].items()}, "checked": targets.get("checked")})
    if a.target not in targets["targets"]:
        return emit({"ok": False, "error": "unknown target %s" % a.target, "known": list(targets["targets"])}, 2)
    t = targets["targets"][a.target]
    rules = t.get("rules", {})
    topo_rules = [k for k in TOPOLOGY_RULES if k in rules]
    info = inspect_file(a.file, thickness_min=rules.get("min_feature") if not a.no_thickness else None,
                        thickness_samples=a.thickness_samples, topology=bool(topo_rules))
    if not info.get("ok"):
        return emit(info, 1)
    unit = t.get("units", "m")
    dims = info.get("dims") or info.get("dims_mesh_space") or [0, 0, 0]
    results = []

    def rule(name, passed, detail, sev="fail"):
        results.append({"rule": name, "status": "pass" if passed is True else (passed or sev), "detail": detail})

    if "max_tris" in rules:
        rule("max_tris", info.get("tris", 0) <= rules["max_tris"], "%s tris (limit %s)" % (info.get("tris"), rules["max_tris"]), rules.get("max_tris_severity", "fail"))
    if "max_tris_per_object" in rules and info.get("object_rows"):
        worst = max(info["object_rows"], key=lambda r: r["tris"])
        rule("max_tris_per_object", worst["tris"] <= rules["max_tris_per_object"], "%s has %d tris (limit %d)" % (worst["name"], worst["tris"], rules["max_tris_per_object"]))
    if "max_objects" in rules and "objects" in info:
        rule("max_objects", info["objects"] <= rules["max_objects"], "%d objects (limit %d)" % (info["objects"], rules["max_objects"]), "warn")
    if "max_materials" in rules and "materials" in info:
        rule("max_materials", len(info["materials"]) <= rules["max_materials"], "%d materials (limit %d)" % (len(info["materials"]), rules["max_materials"]), "warn")
    if "max_image_px" in rules and "max_image_px" in info:
        rule("max_image_px", info["max_image_px"] <= rules["max_image_px"], "largest texture %d px (limit %d)" % (info["max_image_px"], rules["max_image_px"]), "warn")
    if rules.get("require_uvs") and "uv_missing" in info:
        rule("require_uvs", not info["uv_missing"], "objects without UVs: %s" % (", ".join(info["uv_missing"]) or "none"))
    if rules.get("require_watertight"):
        rule("require_watertight", bool(info.get("watertight")), "boundary edges %s, non-manifold edges %s" % (info.get("boundary_edges"), info.get("non_manifold_edges")))
    if rules.get("single_part"):
        rule("single_part", info.get("parts", 1) <= 1, "%s separate parts (loose pieces print as separate islands or fall off)" % info.get("parts"), "warn")
    if rules.get("forbid_unapplied_scale") and info.get("unapplied_scale"):
        rule("forbid_unapplied_scale", False, "unapplied scale on: %s" % ", ".join(info["unapplied_scale"]), "warn")
    if "max_dims" in rules:
        md = sorted(rules["max_dims"], reverse=True)
        ok = all(x <= y + 1e-9 for x, y in zip(sorted(dims, reverse=True), md))
        rule("max_dims", ok, "size %s %s (largest allowed %s %s; rotation is allowed)" % ([round(d, 3) for d in dims], unit, md, unit))
    if "min_feature" in rules:
        th = info.get("thickness") or {}
        if th.get("thin_fraction") is None:
            why = "skipped (--no-thickness)" if a.no_thickness else "not measured (needs Blender)"
            rule("min_feature", "unchecked", "%s: render it and look for parts thinner than %s %s" % (why, rules["min_feature"], unit), "info")
        else:
            spots = "; ".join("%s %s at %s" % (s["thickness"], unit, s["at"]) for s in th.get("thin_spots", [])[:3])
            rule("min_feature", True if th["thin_fraction"] < 0.005 else "warn",
                 "%.1f%% of the surface is thinner than %s %s (thinnest %s, 5th percentile %s; %d sample points)%s" % (
                     100 * th["thin_fraction"], rules["min_feature"], unit, th.get("thinnest"), th.get("p05"), th["samples"],
                     ": " + spots if spots else ""), "warn")
    topo = info.get("topology")
    if topo_rules and not topo:
        rule("topology", "unchecked", info.get("topology_note") or "no faces to check", "info")
    elif topo_rules:
        for k in topo_rules:
            passed, detail = topology_rule(k, rules[k], topo)
            rule(k, passed, detail, "warn")
    if "max_file_mb" in rules:
        mb = info.get("file_bytes", 0) / 1048576.0
        rule("max_file_mb", mb <= rules["max_file_mb"], "%.2f MB (limit %s MB)" % (mb, rules["max_file_mb"]), "warn")
    if a.real_size_m:
        longest = max(dims)
        want = a.real_size_m * (1000.0 if unit == "mm" else 1.0)
        ratio = longest / want if want else 0
        rule("real_scale", 0.9 <= ratio <= 1.1, "longest side %.4g %s vs expected %.4g %s (x%.3g)" % (longest, unit, want, unit, ratio))
    status = "fail" if any(r["status"] == "fail" for r in results) else "warn" if any(r["status"] == "warn" for r in results) else "pass"
    return emit({"ok": status != "fail", "target": a.target, "status": status, "results": results, "advice": t.get("advice", []),
                 "inspect": {k: info.get(k) for k in ("tris", "objects", "dims", "watertight", "parts", "materials", "max_image_px", "backend", "blender", "thickness", "topology") if k in info}},
                0 if status != "fail" else 1)


# ------------------------------------------------------------------------------------------ asset folder and manifest

MANIFEST = "manifest.json"
KINDS = ("real", "imagined", "hybrid")
ROUTES = ("found", "capture", "place", "generate", "procedural", "cad", "hand", "mixed")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_new(a):
    d = os.path.abspath(a.dir)
    for sub in ("refs", "work", "out", "renders"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    mp = os.path.join(d, MANIFEST)
    if os.path.exists(mp) and not a.force:
        return emit({"ok": False, "error": "%s exists (use --force to overwrite)" % mp}, 1)
    man = {"polywright": "1", "name": a.name, "kind": a.kind, "route": a.route, "created": time.strftime("%Y-%m-%d"),
           "brief": a.brief or "", "targets": [t for t in (a.targets or "").split(",") if t], "units": "m",
           "real_size_m": a.real_size_m, "up": "+Z in .blend, +Y in glTF", "sources": [], "tools": [], "outputs": [],
           "reviews": [], "status": "brief"}
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2)
    bp = os.path.join(d, "brief.md")
    if not os.path.exists(bp):
        with open(bp, "w", encoding="utf-8") as f:
            f.write("# %s\n\nWhat: %s\nKind: %s\nTargets: %s\nReal size: %s m\n\n## Must have\n\n## Can skip\n\n## References\n\n"
                    % (a.name, a.brief or "", a.kind, a.targets or "", a.real_size_m or "unknown"))
    return emit({"ok": True, "dir": d, "manifest": mp, "layout": {"refs/": "reference images, blueprints, textures (each listed in sources)",
                 "work/": ".blend and intermediates", "out/": "deliverables, one per target", "renders/": "review sheets"}})


def cmd_manifest(a):
    d = os.path.abspath(a.dir)
    mp = os.path.join(d, MANIFEST)
    if not os.path.isfile(mp):
        return emit({"ok": False, "error": "no manifest.json in %s (pw.py new first)" % d}, 1)
    man = json.load(open(mp, encoding="utf-8"))
    changed = False
    if a.add_source:
        man["sources"].append({"what": a.what or "", "url": a.add_source, "author": a.author or "", "licence": a.licence or "unknown",
                               "retrieved": time.strftime("%Y-%m-%d")})
        changed = True
    if a.add_output:
        p = os.path.abspath(a.add_output)
        if not os.path.isfile(p) and not os.path.isabs(a.add_output) and os.path.isfile(os.path.join(d, a.add_output)):
            p = os.path.join(d, a.add_output)  # out/x.glb written relative to the asset folder
        info = inspect_file(p, fast=False) if a.inspect else {}
        entry = {"path": os.path.relpath(p, d).replace(os.sep, "/"), "target": a.target or "", "sha256": sha256(p),
                 "bytes": os.path.getsize(p), "added": time.strftime("%Y-%m-%d")}
        for k in ("tris", "dims", "watertight", "parts", "materials"):
            if k in info:
                entry[k] = info[k]
        man["outputs"] = [o for o in man["outputs"] if o["path"] != entry["path"]] + [entry]
        changed = True
    if a.add_tool:
        man["tools"].append({"name": a.add_tool, "version": a.tool_version or ""})
        changed = True
    if a.review:
        rp = a.review if os.path.isabs(a.review) else os.path.join(d, a.review)  # relative: inside the asset folder
        rel = os.path.relpath(os.path.abspath(rp), d).replace(os.sep, "/")
        man.setdefault("reviews", [])
        man["reviews"] = [r for r in man["reviews"] if r.get("render") != rel] + [
            {"render": rel, "verdict": a.verdict or "", "by": a.by or "agent", "date": time.strftime("%Y-%m-%d")}]
        changed = True
    if a.status:
        man["status"] = a.status
        changed = True
    if changed:
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=2)
    problems = []
    for k in ("name", "kind", "route", "targets", "sources", "outputs"):
        if k not in man:
            problems.append("missing %s" % k)
    if man.get("kind") not in KINDS:
        problems.append("kind must be one of %s" % ", ".join(KINDS))
    if man.get("route") not in ROUTES:
        problems.append("route must be one of %s" % ", ".join(ROUTES))
    for s in man.get("sources", []):
        if s.get("licence", "unknown") == "unknown":
            problems.append("source without a licence: %s" % s.get("url"))
    for o in man.get("outputs", []):
        fp = os.path.join(d, o["path"])
        if not os.path.isfile(fp):
            problems.append("output missing on disk: %s" % o["path"])
        elif a.validate and sha256(fp) != o.get("sha256"):
            problems.append("output changed since it was recorded: %s" % o["path"])
    return emit({"ok": not problems, "manifest": mp, "status": man.get("status"), "outputs": len(man.get("outputs", [])),
                 "sources": len(man.get("sources", [])), "problems": problems}, 0 if not problems else 1)


# ------------------------------------------------------------------------------------------ run a bpy script

def split_bpy_args(a):
    """`pw.py bpy build.py --blend x.blend -- --out y`: argparse's REMAINDER swallows options written after the
    script name, so pull pw.py's own options out of the part before the first `--`; the rest goes to the script."""
    rest = list(a.args)
    cut = rest.index("--") if "--" in rest else len(rest)
    head, tail = rest[:cut], rest[cut + 1:]
    keep, i = [], 0
    while i < len(head):
        opt = head[i]
        name = opt.split("=", 1)[0]
        if name in ("--blend", "--timeout", "--lines"):
            val = opt.split("=", 1)[1] if "=" in opt else (head[i + 1] if i + 1 < len(head) else None)
            i += 1 if "=" in opt else 2
            setattr(a, name[2:], val if name == "--blend" else int(val))
            continue
        keep.append(opt)
        i += 1
    a.args = keep + tail
    return a


def cmd_bpy(a):
    a = split_bpy_args(a)
    r = run_blender_script(os.path.abspath(a.script), a.args, blend=os.path.abspath(a.blend) if a.blend else None, timeout=a.timeout)
    if "stdout" not in r:
        return emit(r, 1)
    out = {"ok": r["ok"], "exit_code": r["exit_code"], "seconds": r["seconds"], "blender": r["blender"],
           "output": condense(r["stdout"], a.lines), "errors": condense(r["stderr"], 20)}
    tb = [ln for ln in (r["stdout"] + "\n" + r["stderr"]).splitlines() if ln.startswith(("Traceback", "  File", "    ")) or re.match(r"^\w+Error", ln)]
    if tb and not r["ok"]:
        out["traceback"] = tb[-14:]
        out["hint"] = "bpy API traps by Blender version: polywright-blender references/bpy-api-traps.md"
    return emit(out, 0 if r["ok"] else 1)


# ------------------------------------------------------------------------------------------ gen: image to 3D through ComfyUI

HY_SINGLE = ["hunyuan3d-dit-v2.safetensors", "hunyuan3d-dit-v2-turbo.safetensors"]
HY_MV = ["hunyuan3d-dit-v2-mv.safetensors", "hunyuan3d-dit-v2-mv-turbo.safetensors"]


def comfy_upload(host, path):
    name = "pw_%s_%s" % (uuid.uuid4().hex[:8], os.path.basename(path))
    boundary = uuid.uuid4().hex
    data = open(path, "rb").read()
    body = ("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\nContent-Type: image/png\r\n\r\n" % (boundary, name)).encode() \
        + data + ("\r\n--%s--\r\n" % boundary).encode()
    return http_json(host + "/upload/image", data=body, timeout=120,
                     headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})["name"]


def hunyuan_graph(ckpt, views, seed, steps, octree, prefix, cfg=5.0):
    g = {"1": {"class_type": "ImageOnlyCheckpointLoader", "inputs": {"ckpt_name": ckpt}},
         "5": {"class_type": "EmptyLatentHunyuan3Dv2", "inputs": {"resolution": 3072, "batch_size": 1}}}
    cond, n = {}, 10
    for view, name in views.items():
        g[str(n)] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g[str(n + 1)] = {"class_type": "CLIPVisionEncode", "inputs": {"clip_vision": ["1", 1], "image": [str(n), 0], "crop": "center"}}
        cond[view] = [str(n + 1), 0]
        n += 2
    if len(views) == 1 and "front" in views and "-mv" not in ckpt:
        g["4"] = {"class_type": "Hunyuan3Dv2Conditioning", "inputs": {"clip_vision_output": cond["front"]}}
    else:
        g["4"] = {"class_type": "Hunyuan3Dv2ConditioningMultiView", "inputs": cond}
    g["6"] = {"class_type": "KSampler", "inputs": {"model": ["1", 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler",
                                                   "scheduler": "normal", "positive": ["4", 0], "negative": ["4", 1],
                                                   "latent_image": ["5", 0], "denoise": 1.0}}
    g["7"] = {"class_type": "VAEDecodeHunyuan3D", "inputs": {"samples": ["6", 0], "vae": ["1", 2], "num_chunks": 8000, "octree_resolution": octree}}
    g["8"] = {"class_type": "VoxelToMesh", "inputs": {"voxel": ["7", 0], "algorithm": "surface net", "threshold": 0.6}}
    g["9"] = {"class_type": "SaveGLB", "inputs": {"mesh": ["8", 0], "filename_prefix": prefix}}
    return g


def prep_image(path, tmpdir):
    """Square, padded, white background, 1024 px. Needs Pillow; without it the image is sent as is."""
    try:
        from PIL import Image
    except ImportError:
        return path, "sent as is (no Pillow)"
    im = Image.open(path).convert("RGBA")
    note = "padded to a white square"
    try:
        from rembg import remove  # optional
        im = remove(im)
        note = "background removed (rembg), " + note
    except Exception:
        pass
    bbox = im.getbbox() if im.mode == "RGBA" and im.getextrema()[3][0] < 255 else None
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    side = int(max(w, h) * 1.15)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2), im)
    out = os.path.join(tmpdir, os.path.splitext(os.path.basename(path))[0] + "_prep.png")
    canvas.convert("RGB").resize((1024, 1024)).save(out)
    return out, note


def comfy_run(host, graph, timeout):
    try:
        res = http_json(host + "/prompt", data=json.dumps({"prompt": graph, "client_id": "polywright"}).encode(), timeout=60,
                        headers={"Content-Type": "application/json"})
    except urllib.error.HTTPError as e:  # ComfyUI explains a rejected graph in the body
        body = e.read().decode("utf-8", "replace")
        try:
            body = json.loads(body)
            body = {"error": body.get("error"), "node_errors": body.get("node_errors")}
        except ValueError:
            pass
        raise RuntimeError("graph rejected (HTTP %d): %s" % (e.code, json.dumps(body)[:1500]))
    if res.get("node_errors"):
        raise RuntimeError("graph rejected: %s" % json.dumps(res["node_errors"])[:600])
    pid = res["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = http_json("%s/history/%s" % (host, pid), timeout=30)
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError("ComfyUI error: %s" % json.dumps(st.get("messages", []))[-800:])
            return h[pid]["outputs"]
        time.sleep(3)
    raise RuntimeError("timed out after %ds waiting for ComfyUI" % timeout)


def apply_sets(graph, sets, uploaded):
    """--set NODE.input=VALUE where NODE is a node id or a class_type (every node of that type).
    VALUE @path uploads an image first; numbers and true/false are parsed."""
    done = []
    for item in sets or []:
        key, _, val = item.partition("=")
        node, _, inp = key.rpartition(".")
        if not node or not inp:
            raise ValueError("--set wants NODE.input=VALUE, got %r" % item)
        if val.startswith("@"):
            val = uploaded[val[1:]]
        elif re.fullmatch(r"-?\d+", val):
            val = int(val)
        elif re.fullmatch(r"-?\d*\.\d+", val):
            val = float(val)
        elif val in ("true", "false"):
            val = val == "true"
        hits = [k for k, v in graph.items() if k == node or v.get("class_type") == node]
        if not hits:
            raise ValueError("no node %s in the workflow" % node)
        for k in hits:
            graph[k].setdefault("inputs", {})[inp] = val
        done.append("%s.%s (%d node%s)" % (node, inp, len(hits), "" if len(hits) == 1 else "s"))
    return done


WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO", "COLOR", "LOAD_3D", "COMFY_DYNAMICCOMBO_V3"}
UI_ONLY = {"Note", "MarkdownNote", "Reroute", "PrimitiveNode"}
PREVIEWS = {"PreviewImage", "MaskPreview", "Preview3D", "Preview3DAdvanced", "PreviewAny"}


def ui_to_api(ui, info, drop_previews=True):
    """Convert a workflow saved from ComfyUI's editor (nodes and links) into the API format /prompt takes, using
    the host's own node definitions to map each node's widget values to input names. Muted nodes and notes are
    left out; a bypassed node passes its first input of the matching type through; preview nodes are dropped."""
    links = {l[0]: (l[1], l[2]) for l in ui.get("links", [])}  # link id -> (from node, from slot)
    nodes = {n["id"]: n for n in ui.get("nodes", [])}

    def source(link_id, seen=0):
        if link_id is None or link_id not in links or seen > 50:
            return None
        nid, slot = links[link_id]
        n = nodes.get(nid)
        if n is None or n.get("mode") == 2:
            return None
        if n.get("mode") == 4 or n["type"] == "Reroute":  # pass through
            want = (n.get("outputs") or [{}])[slot].get("type") if n.get("outputs") else None
            for i in n.get("inputs", []):
                if i.get("link") is not None and (n["type"] == "Reroute" or i.get("type") == want):
                    return source(i["link"], seen + 1)
            return None
        return [str(nid), slot]

    used = {links[i["link"]][0] for m in nodes.values() for i in m.get("inputs", []) if i.get("link") in links}
    api = {}
    for nid, n in nodes.items():
        t = n["type"]
        if t in UI_ONLY or n.get("mode") in (2, 4) or t not in info:
            continue
        if drop_previews and t in PREVIEWS and nid not in used:  # some previews pass their image on: keep those
            continue
        spec = info[t]["input"]
        order = info[t].get("input_order") or {k: list(spec.get(k, {})) for k in ("required", "optional")}
        inputs = {}
        wv = n.get("widgets_values")
        if isinstance(wv, dict):
            inputs.update({k: v for k, v in wv.items() if not isinstance(v, dict)})
        else:
            vals = list(wv or [])
            for group in ("required", "optional"):
                for name in order.get(group, []):
                    s = spec.get(group, {}).get(name)
                    if not s:
                        continue
                    typ, opts = s[0], (s[1] if len(s) > 1 and isinstance(s[1], dict) else {})
                    if not (isinstance(typ, list) or typ in WIDGET_TYPES) or not vals:
                        continue
                    inputs[name] = vals.pop(0)
                    if typ == "COMFY_DYNAMICCOMBO_V3":  # the chosen option's own widgets follow, as name.sub
                        chosen = next((o for o in opts.get("options", []) if o.get("key") == inputs[name]), {})
                        for sub in chosen.get("inputs", {}).get("required", {}):
                            if vals:
                                inputs["%s.%s" % (name, sub)] = vals.pop(0)
                    if opts.get("control_after_generate") or opts.get("image_upload") or name in ("seed", "noise_seed"):
                        if vals and isinstance(vals[0], str) and (vals[0] in ("fixed", "increment", "decrement", "randomize", "image")):
                            vals.pop(0)
        for name, s_ in spec.get("required", {}).items():  # a template older than the host lacks new widgets
            if name not in inputs and (isinstance(s_[0], list) or s_[0] in WIDGET_TYPES) and len(s_) > 1 and isinstance(s_[1], dict) and "default" in s_[1]:
                inputs[name] = s_[1]["default"]
        for i in n.get("inputs", []):
            src = source(i.get("link"))
            if src is not None and src[0] in {str(k) for k, v in nodes.items() if v["type"] not in UI_ONLY}:
                inputs[i["name"]] = src
        api[str(nid)] = {"class_type": t, "inputs": inputs}
    # inputs pointing at dropped nodes go away; then drop nodes nothing reaches from an output node
    for v in api.values():
        v["inputs"] = {k: x for k, x in v["inputs"].items() if not (isinstance(x, list) and len(x) == 2 and x[0] not in api)}
    return api


def run_workflow(a):
    """Any ComfyUI workflow: API format (Workflow > Export (API)) or the editor's own format (a template, a saved
    workflow), converted with ui_to_api. The image goes into every LoadImage node unless --set says otherwise."""
    graph = json.load(open(a.workflow, encoding="utf-8"))
    ui = graph if ("nodes" in graph and "links" in graph) else None
    host, tried = None, []
    for h in comfy_hosts(a.host):
        try:
            info = http_json(h + "/object_info", timeout=20)
            if ui is not None:
                graph = ui_to_api(ui, info)
            missing = sorted({v.get("class_type") for v in graph.values() if v.get("class_type") not in info})
            tried.append({"host": h, "missing_nodes": missing})
            if not missing:
                host = h
                break
        except Exception as e:
            tried.append({"host": h, "up": False, "error": str(e)[:100]})
    if not host:
        return emit({"ok": False, "error": "no ComfyUI host has every node in the workflow", "tried": tried,
                     "next": "a server on another port: pass --host http://127.0.0.1:PORT or set POLYWRIGHT_COMFYUI "
                             "(the default is only 8188)"}, 1)
    uploaded = {}
    paths = {a.image} | {it.split("=", 1)[1][1:] for it in (a.set or []) if "=@" in it}
    for pth in paths:
        if not os.path.isfile(pth):
            return emit({"ok": False, "error": "image not found: %s" % pth}, 1)
        uploaded[pth] = comfy_upload(host, pth)
    if not any("=@" in it and "LoadImage" in it for it in (a.set or [])):
        for v in graph.values():
            if v.get("class_type") == "LoadImage":
                v["inputs"]["image"] = uploaded[a.image]
    sets = apply_sets(graph, a.set, uploaded)
    if a.save_api:
        with open(a.save_api, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=1)
    if a.seed is not None:
        for v in graph.values():
            if "seed" in v.get("inputs", {}) and not isinstance(v["inputs"]["seed"], list):
                v["inputs"]["seed"] = a.seed
    t0 = time.time()
    outputs = comfy_run(host, graph, a.timeout)
    files = [f for o in outputs.values() for v in o.values() if isinstance(v, list) for f in v
             if isinstance(f, dict) and re.search(r"\.(glb|gltf|obj|ply|stl|fbx|usdz?|spz|sog)$", str(f.get("filename", "")), re.I)]
    if not files:
        return emit({"ok": False, "error": "no mesh or splat file in the outputs", "outputs": str(outputs)[:400]}, 1)
    out_dir = os.path.dirname(os.path.abspath(a.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for i, f0 in enumerate(files):
        url = "%s/view?%s" % (host, urllib.parse.urlencode({"filename": f0["filename"], "subfolder": f0.get("subfolder", ""), "type": f0.get("type", "output")}))
        dest = os.path.abspath(a.out) if i == 0 else os.path.join(out_dir, "%s_%d%s" % (os.path.splitext(os.path.basename(a.out))[0], i, os.path.splitext(f0["filename"])[1]))
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=300) as r:
            open(dest, "wb").write(r.read())
        saved.append(dest)
    res = {"ok": True, "out": saved[0], "all_outputs": saved, "host": host, "workflow": os.path.abspath(a.workflow), "sets": sets,
           "seconds": round(time.time() - t0, 1), "next": "inspect and render; record the model and its licence with pw.py manifest"}
    with open(os.path.splitext(saved[0])[0] + ".gen.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    return emit(res)


def cmd_gen(a):
    if a.workflow:
        return run_workflow(a)
    views = {"front": a.image}
    for v in ("left", "back", "right"):
        if getattr(a, v):
            views[v] = getattr(a, v)
    for v, p in views.items():
        if not os.path.isfile(p):
            return emit({"ok": False, "error": "%s image not found: %s" % (v, p)}, 1)
    multi = len(views) > 1
    want = [a.ckpt] if a.ckpt else (HY_MV if multi else HY_SINGLE)
    if a.turbo and not a.ckpt:
        want = list(reversed(want))
    host, ckpt, tried = None, None, []
    for h in comfy_hosts(a.host):
        try:
            cks = http_json(h + "/models/checkpoints", timeout=6)
            ckpt = next((c for c in want if c in cks), None)
            tried.append({"host": h, "up": True, "has": [c for c in cks if "hunyuan3d" in c.lower()]})
            if ckpt:
                host = h
                break
        except Exception as e:
            tried.append({"host": h, "up": False, "error": str(e)[:100]})
    if not host:
        return emit({"ok": False, "error": "no ComfyUI host with %s" % " or ".join(want), "tried": tried,
                     "next": "start ComfyUI with the Hunyuan3D-2 checkpoints in models/checkpoints, set POLYWRIGHT_COMFYUI, or use a hosted generator (polywright-generate)"}, 1)
    tmp = tempfile.mkdtemp(prefix="pw_gen_")
    notes, names = {}, {}
    for v, p in views.items():
        pp, note = (p, "sent as is") if a.no_prep else prep_image(p, tmp)
        notes[v] = note
        names[v] = comfy_upload(host, pp)
    seed = a.seed if a.seed is not None else random.randint(0, 2 ** 31)
    steps = a.steps or (8 if "turbo" in ckpt else 30)
    t0 = time.time()
    try:
        outputs = comfy_run(host, hunyuan_graph(ckpt, names, seed, steps, a.octree, "polywright/gen"), a.timeout)
    except Exception as e:
        return emit({"ok": False, "error": str(e), "host": host, "checkpoint": ckpt}, 1)
    files = [f for o in outputs.values() for v in o.values() if isinstance(v, list) for f in v if isinstance(f, dict) and str(f.get("filename", "")).endswith(".glb")]
    if not files:
        return emit({"ok": False, "error": "no .glb in the outputs", "outputs": str(outputs)[:400]}, 1)
    f0 = files[0]
    url = "%s/view?%s" % (host, urllib.parse.urlencode({"filename": f0["filename"], "subfolder": f0.get("subfolder", ""), "type": f0.get("type", "output")}))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=300) as r:
        open(a.out, "wb").write(r.read())
    shutil.rmtree(tmp, ignore_errors=True)
    res = {"ok": True, "out": os.path.abspath(a.out), "host": host, "checkpoint": ckpt, "mode": "multi-view" if multi else "single-view",
           "views": list(views), "prep": notes, "seed": seed, "steps": steps, "octree": a.octree, "seconds": round(time.time() - t0, 1),
           "licence_note": "Hunyuan3D-2 community licence: not licensed in the EU, UK or South Korea; check terms before commercial use",
           "next": "untextured and unscaled, Y-up, many open edges: inspect, render, then convert --size-m or printable"}
    with open(os.path.splitext(a.out)[0] + ".gen.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    return emit(res)


# ------------------------------------------------------------------------------------------ texture maps

def cmd_texture(a):
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return emit({"ok": False, "error": "texture needs numpy and Pillow in this Python (pip install numpy pillow)"}, 1)
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.image))[0]
    img = np.asarray(Image.open(a.image).convert("RGB"), dtype=np.float32) / 255.0
    out = {}
    if a.seamless:
        h, w, _ = img.shape
        sh = np.roll(np.roll(img, h // 2, 0), w // 2, 1)
        yy = np.abs(np.linspace(-1, 1, h))[:, None]
        xx = np.abs(np.linspace(-1, 1, w))[None, :]
        wgt = np.clip(np.maximum(xx, yy) * 1.6 - 0.6, 0, 1)[..., None]  # 1 at the edges: use the shifted copy there
        img = img * (1 - wgt) + sh * wgt
        p = os.path.join(a.out, stem + "_seamless.png")
        Image.fromarray((img * 255).astype("uint8")).save(p)
        out["albedo_seamless"] = p
    lum = img @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    hgt = (lum - lum.min()) / max(float(lum.max() - lum.min()), 1e-6)
    p = os.path.join(a.out, stem + "_height.png")
    Image.fromarray((hgt * 255).astype("uint8")).save(p)
    out["height"] = p
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * a.strength
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * a.strength
    n = np.dstack([-gx, gy if a.convention == "opengl" else -gy, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    p = os.path.join(a.out, stem + "_normal_%s.png" % a.convention)
    Image.fromarray(((n * 0.5 + 0.5) * 255).astype("uint8")).save(p)
    out["normal"] = p
    rough = np.clip(0.55 + (0.5 - hgt) * 0.5, 0.05, 1.0)
    p = os.path.join(a.out, stem + "_roughness.png")
    Image.fromarray((rough * 255).astype("uint8")).save(p)
    out["roughness"] = p
    return emit({"ok": True, "maps": out, "convention": a.convention,
                 "note": "luminance-derived approximations (the classic CrazyBump trick), fine for props and terrain, wrong for measured materials; OpenGL = glTF, Blender, Unity; DirectX = Unreal"})


# ------------------------------------------------------------------------------------------ place: real places from open data

OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter"]


def fetch(url, data=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_osm(s, w, n, e, path, refresh=False):
    if os.path.isfile(path) and not refresh:
        return json.load(open(path, encoding="utf-8")), "cache"
    b = "(%f,%f,%f,%f)" % (s, w, n, e)
    parts = ['nwr["building"]', 'way["highway"]', 'way["waterway"]', 'nwr["natural"]', 'nwr["landuse"]', 'nwr["leisure"]',
             'nwr["amenity"="parking"]', 'nwr["water"]', 'way["area:highway"]', 'node["highway"="street_lamp"]']
    # A box query only returns ways with a node in the box: a park or wood that encloses the whole box comes from
    # is_in at the centre (land-use tags only, so city and state boundaries stay out).
    lat0, lon0 = (s + n) / 2, (w + e) / 2
    around = "".join("%s(pivot.c)[%s];" % (kind, tag) for kind in ("way", "rel") for tag in ("leisure", "landuse", "natural"))
    q = ("[out:json][timeout:180];is_in(%f,%f)->.c;(" % (lat0, lon0) + "".join(x + b + ";" for x in parts) + around
         + ");out body;>;out skel qt;")  # only what place uses
    errs = []
    for i, url in enumerate(OVERPASS * 2):
        try:
            raw = fetch(url, data=urllib.parse.urlencode({"data": q}).encode(), timeout=240)
            if raw[:1] != b"{":  # a busy server can answer 200 with an HTML error page
                raise ValueError("not JSON: %r" % raw[:60])
            open(path, "wb").write(raw)
            return json.loads(raw.decode("utf-8")), url
        except Exception as ex:
            errs.append("%s: %s" % (url, str(ex)[:80]))
            time.sleep(5 + 5 * i)
    raise RuntimeError("Overpass failed: " + " | ".join(errs))


def read_tiff_f32(data):
    """Minimal reader for an uncompressed single-band float32 TIFF (strips or tiles)."""
    bo = "<" if data[:2] == b"II" else ">"
    (ifd,) = struct.unpack(bo + "I", data[4:8])
    (count,) = struct.unpack(bo + "H", data[ifd:ifd + 2])
    tags = {}
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8, 16: 8}
    fmts = {1: "B", 3: "H", 4: "I", 11: "f", 12: "d", 16: "Q"}
    for k in range(count):
        off = ifd + 2 + k * 12
        tag, typ, n = struct.unpack(bo + "HHI", data[off:off + 8])
        sz = sizes.get(typ, 1) * n
        voff = off + 8 if sz <= 4 else struct.unpack(bo + "I", data[off + 8:off + 12])[0]
        if typ in fmts:
            tags[tag] = list(struct.unpack(bo + fmts[typ] * n, data[voff:voff + sizes[typ] * n]))
        else:
            tags[tag] = data[voff:voff + sz]
    w, h = tags[256][0], tags[257][0]
    if tags.get(259, [1])[0] != 1:
        raise ValueError("compressed TIFF not supported")
    if tags.get(258, [32])[0] != 32:
        raise ValueError("expected 32-bit samples")
    vals = [0.0] * (w * h)
    if 324 in tags:  # tiled
        tw, th = tags[322][0], tags[323][0]
        across = (w + tw - 1) // tw
        for i, (o, c) in enumerate(zip(tags[324], tags[325])):
            tile = struct.unpack(bo + "%df" % (c // 4), data[o:o + c])
            ty, tx = divmod(i, across)
            for r in range(th):
                y = ty * th + r
                if y >= h:
                    break
                for cc in range(tw):
                    x = tx * tw + cc
                    if x < w:
                        vals[y * w + x] = tile[r * tw + cc]
    else:
        pos = 0
        for o, c in zip(tags[273], tags[279]):
            strip = struct.unpack(bo + "%df" % (c // 4), data[o:o + c])
            vals[pos:pos + len(strip)] = strip
            pos += len(strip)
    return w, h, vals


def png_decode(data):
    """Minimal PNG decoder: 8-bit RGB or RGBA, not interlaced. Returns (w, h, channels, bytes)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, w = 8, b"", None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _c, _f, inter = struct.unpack(">IIBBBBB", chunk)
            if depth != 8 or ctype not in (2, 6) or inter:
                raise ValueError("unsupported PNG (depth %d, colour type %d)" % (depth, ctype))
            ch = 3 if ctype == 2 else 4
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for x in range(stride):
            a_ = line[x - ch] if x >= ch else 0
            b_ = prev[x]
            c_ = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a_) & 255
            elif f == 2:
                line[x] = (line[x] + b_) & 255
            elif f == 3:
                line[x] = (line[x] + ((a_ + b_) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b_ - c_), abs(a_ - c_), abs(a_ + b_ - 2 * c_)
                pr = a_ if pa <= pb and pa <= pc else (b_ if pb <= pc else c_)
                line[x] = (line[x] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, bytes(out)


class Grid:
    """Elevation grid over the bbox in lat/lon; row 0 = north."""

    def __init__(self, s, w, n, e, nx, ny, vals):
        self.s, self.w, self.n, self.e, self.nx, self.ny, self.v = s, w, n, e, nx, ny, vals

    def at(self, lat, lon):
        fx = (lon - self.w) / (self.e - self.w) * (self.nx - 1)
        fy = (self.n - lat) / (self.n - self.s) * (self.ny - 1)
        fx = min(max(fx, 0), self.nx - 1.001)
        fy = min(max(fy, 0), self.ny - 1.001)
        x0, y0 = int(fx), int(fy)
        tx, ty = fx - x0, fy - y0
        v = self.v
        i = y0 * self.nx + x0
        return (v[i] * (1 - tx) * (1 - ty) + v[i + 1] * tx * (1 - ty) + v[i + self.nx] * (1 - tx) * ty + v[i + self.nx + 1] * tx * ty)


def fill_nodata(vals):
    good = [v for v in vals if -1000 < v < 9000]
    fill = min(good) if good else 0.0
    return [v if -1000 < v < 9000 else fill for v in vals], len(vals) - len(good)


def dem_usgs(s, w, n, e, nx, ny):
    url = ("https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?"
           + urllib.parse.urlencode({"bbox": "%f,%f,%f,%f" % (w, s, e, n), "bboxSR": 4326, "imageSR": 4326, "size": "%d,%d" % (nx, ny),
                                     "format": "tiff", "compression": "None", "pixelType": "F32",
                                     "interpolation": "RSP_BilinearInterpolation", "f": "image"}))
    tw, th, vals = read_tiff_f32(fetch(url, timeout=180))
    if (tw, th) != (nx, ny):
        raise ValueError("USGS returned %dx%d, asked %dx%d" % (tw, th, nx, ny))
    return vals


def dem_terrarium(s, w, n, e, nx, ny, res_m):
    lat0 = (s + n) / 2
    z = 15
    while z > 8 and 156543.03 * math.cos(math.radians(lat0)) / 2 ** z < res_m / 2:
        z -= 1

    def merc(lat, lon):
        k = 2 ** z * 256
        return (lon + 180) / 360 * k, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * k

    x0, y0 = merc(n, w)
    x1, y1 = merc(s, e)
    tiles = {}
    for tx in range(int(x0 // 256), int(x1 // 256) + 1):
        for ty in range(int(y0 // 256), int(y1 // 256) + 1):
            tw, th, ch, px = png_decode(fetch("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png" % (z, tx, ty), timeout=60))
            tiles[(tx, ty)] = (ch, px)
    vals = []
    for r in range(ny):
        lat = n - (n - s) * r / max(ny - 1, 1)
        for c in range(nx):
            lon = w + (e - w) * c / max(nx - 1, 1)
            X, Y = merc(lat, lon)
            ch, px = tiles[(int(X // 256), int(Y // 256))]
            i = (int(Y % 256) * 256 + int(X % 256)) * ch
            vals.append(px[i] * 256 + px[i + 1] + px[i + 2] / 256.0 - 32768)
    return vals, z


ROAD_W = {"motorway": 14, "trunk": 12, "primary": 10, "secondary": 9, "tertiary": 8, "residential": 7, "unclassified": 6,
          "living_street": 5, "service": 4, "pedestrian": 4, "track": 3, "cycleway": 2.5, "footway": 2, "path": 1.8,
          "bridleway": 2, "steps": 2}
GROUND = [  # (class, test, colour): the first matching test names an area's class; smaller areas paint over larger
    ("water", lambda t: t.get("natural") == "water" or "water" in t or t.get("waterway") == "riverbank" or t.get("leisure") == "swimming_pool", (0.25, 0.48, 0.70)),
    ("pitch", lambda t: t.get("leisure") in ("pitch", "track"), (0.45, 0.62, 0.35)),
    ("sand", lambda t: t.get("natural") in ("sand", "beach") or t.get("surface") == "sand", (0.84, 0.77, 0.58)),
    ("playground", lambda t: t.get("leisure") == "playground", (0.70, 0.52, 0.38)),
    ("paved", lambda t: t.get("amenity") == "parking" or t.get("area:highway") or (t.get("highway") == "pedestrian" and t.get("area") == "yes"), (0.55, 0.55, 0.55)),
    ("wood", lambda t: t.get("natural") in ("wood", "scrub") or t.get("landuse") == "forest", (0.24, 0.40, 0.22)),
    ("grass", lambda t: t.get("landuse") in ("grass", "meadow", "recreation_ground", "village_green") or t.get("leisure") in ("garden", "dog_park"), (0.44, 0.60, 0.30)),
    ("park", lambda t: t.get("leisure") in ("park", "nature_reserve"), (0.48, 0.62, 0.34)),
]
GROUND_DEFAULT = (0.62, 0.60, 0.52)


class Local:
    """Equirectangular projection around the bbox centre: metres east (x) and north (y). Good to a few km."""

    def __init__(self, lat0, lon0):
        p = math.radians(lat0)
        self.lat0, self.lon0 = lat0, lon0
        self.ky = 111132.92 - 559.82 * math.cos(2 * p) + 1.175 * math.cos(4 * p)
        self.kx = 111412.84 * math.cos(p) - 93.5 * math.cos(3 * p)

    def xy(self, lat, lon):
        return ((lon - self.lon0) * self.kx, (lat - self.lat0) * self.ky)


def poly_area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2.0


def earclip(pts):
    """Triangulate a simple polygon (no holes). Returns index triples into pts (CCW)."""
    n = len(pts)
    if n < 3:
        return []
    idx = list(range(n))
    if poly_area(pts) < 0:
        idx.reverse()

    def inside(p, a, b, c):
        d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
        d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
        d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

    tris, guard = [], 0
    while len(idx) > 3 and guard < n * n:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-12:
                continue
            if any(inside(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    elif len(idx) > 3:  # degenerate leftovers: fan them
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    return tris


def clean_ring(ring, eps=0.05):
    """Drop repeated and collinear points so prisms stay manifold."""
    out = []
    for p in ring:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= eps:
        out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < eps * eps:
                out.pop(i)
                changed = True
                break
    return out


def clip_ring(ring, hw, hh):
    """Sutherland-Hodgman clip of a polygon to the rectangle |x|<=hw, |y|<=hh."""
    def clip(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            cur, prev = pts[i], pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(inter(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(inter(prev, cur))
        return out

    def ix(x0):
        return lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / ((b[0] - a[0]) or 1e-12))

    def iy(y0):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / ((b[1] - a[1]) or 1e-12), y0)

    pts = ring
    for inside, inter in ((lambda p: p[0] >= -hw, ix(-hw)), (lambda p: p[0] <= hw, ix(hw)),
                          (lambda p: p[1] >= -hh, iy(-hh)), (lambda p: p[1] <= hh, iy(hh))):
        if not pts:
            break
        pts = clip(pts, inside, inter)
    return pts


def clip_line(line, hw, hh):
    """Split a polyline into the pieces inside the rectangle (Liang-Barsky per segment)."""
    pieces, cur = [], []
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        dx, dy = x1 - x0, y1 - y0
        t0, t1, ok = 0.0, 1.0, True
        for pp, q in ((-dx, x0 + hw), (dx, hw - x0), (-dy, y0 + hh), (dy, hh - y0)):
            if pp == 0:
                if q < 0:
                    ok = False
            else:
                r = q / pp
                if pp < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
        if not ok or t0 > t1:
            if len(cur) > 1:
                pieces.append(cur)
            cur = []
            continue
        a, b = (x0 + dx * t0, y0 + dy * t0), (x0 + dx * t1, y0 + dy * t1)
        if not cur or cur[-1] != a:
            if len(cur) > 1:
                pieces.append(cur)
            cur = [a]
        cur.append(b)
        if t1 < 1.0:
            pieces.append(cur)
            cur = []
    if len(cur) > 1:
        pieces.append(cur)
    return pieces


def stitch_rings(segments):
    """Join open way node lists end to end into closed rings (multipolygon members are often split)."""
    rings, open_ = [], [list(x) for x in segments if len(x) > 1]
    while open_:
        cur = open_.pop(0)
        grown = True
        while cur[0] != cur[-1] and grown:
            grown = False
            for i, seg in enumerate(open_):
                if seg[0] == cur[-1]:
                    cur += seg[1:]
                elif seg[-1] == cur[-1]:
                    cur += seg[::-1][1:]
                elif seg[-1] == cur[0]:
                    cur = seg + cur[1:]
                elif seg[0] == cur[0]:
                    cur = seg[::-1] + cur[1:]
                else:
                    continue
                open_.pop(i)
                grown = True
                break
        if cur[0] == cur[-1] and len(cur) > 3:
            rings.append(cur)
    return rings


def point_in_poly(x, y, pts):
    ins = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            ins = not ins
        j = i
    return ins


def parse_height(t):
    for k in ("height", "est_height"):
        if t.get(k):
            try:
                return float(re.sub(r"[^0-9.]", "", str(t[k]).split(";")[0])), "osm height"
            except ValueError:
                pass
    if t.get("building:levels"):
        try:
            return float(t["building:levels"]) * 3.2 + 1.0, "levels"
        except ValueError:
            pass
    b = t.get("building", "yes")
    if b in ("garage", "garages", "shed", "carport", "roof", "hut", "kiosk", "toilets"):
        return 3.0, "default"
    if b in ("apartments", "commercial", "retail", "office", "school", "church", "hotel", "industrial", "warehouse", "civic", "public"):
        return 8.0, "default"
    return 5.0, "default"

LEVEL_M = 3.2           # metres per storey, polywright's own default (the OSM wiki suggests none)
ROOF_PITCH_DEG = 30.0   # roof slope when a roof shape has no roof:height, roof:levels or roof:angle (own default)
ROOF_AS = {"gabled": "gabled", "saltbox": "gabled", "gambrel": "gabled", "mansard": "hipped", "half-hipped": "hipped",
           "hipped": "hipped", "pyramidal": "pyramidal", "skillion": "skillion", "dome": "pyramidal", "onion": "pyramidal",
           "round": "gabled"}


def _num(t, k):
    try:
        return float(re.sub(r"[^0-9.]", "", str(t.get(k, "")).split(";")[0]) or "x")
    except ValueError:
        return None


def min_rect(ring):
    """Minimum-area rectangle around a ring: (centre, long axis unit, short axis unit, long side, short side)."""
    best = None
    n = len(ring)
    for i in range(n):
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-9:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        us = [x * ux + y * uy for x, y in ring]
        vs = [-x * uy + y * ux for x, y in ring]
        area = (max(us) - min(us)) * (max(vs) - min(vs))
        if best is None or area < best[0]:
            best = (area, ux, uy, min(us), max(us), min(vs), max(vs))
    _, ux, uy, u0, u1, v0, v1 = best
    cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
    centre = (cu * ux - cv * uy, cu * uy + cv * ux)
    a, b = (ux, uy), (-uy, ux)
    if (u1 - u0) >= (v1 - v0):
        return centre, a, b, u1 - u0, v1 - v0
    return centre, b, (-a[0], -a[1]), v1 - v0, u1 - u0


def is_convex(ring):
    sign = 0
    n = len(ring)
    for i in range(n):
        (x0, y0), (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n], ring[(i + 2) % n]
        c = (x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)
        if abs(c) > 1e-12:
            if sign and (c > 0) != (sign > 0):
                return False
            sign = c
    return True


def roof_solid(shape, ring, z0, rh, along=True, direction=None):
    """Closed, outward roof solid sitting at z0, rh high, on the ring's minimum-area rectangle (on the ring itself
    for a pyramid over a convex footprint). Ridges run along the long side unless along is False; a skillion's
    low edge faces the compass `direction` (degrees), else the long side's left."""
    if shape == "pyramidal" and is_convex(ring):
        n = len(ring)
        cx = sum(x for x, _ in ring) / n
        cy = sum(y for _, y in ring) / n
        verts = [(x, y, z0) for x, y in ring] + [(cx, cy, z0 + rh)]
        tris = [(c, b, a) for a, b, c in earclip(ring)]
        tris += [(i, (i + 1) % n, n) for i in range(n)]
        return verts, tris
    (cx, cy), u, v, L, W = min_rect(ring)
    if not along and shape in ("gabled", "hipped"):
        u, v, L, W = v, (-u[0], -u[1]), W, L

    def at(a, b, z):
        return (cx + u[0] * a + v[0] * b, cy + u[1] * a + v[1] * b, z)

    hl, hw = L / 2, W / 2
    base = [at(-hl, -hw, z0), at(hl, -hw, z0), at(hl, hw, z0), at(-hl, hw, z0)]  # CCW seen from above
    top = z0 + rh
    if shape == "gabled":
        verts = base + [at(-hl, 0, top), at(hl, 0, top)]
        tris = [(0, 2, 1), (0, 3, 2), (0, 1, 5), (0, 5, 4), (2, 3, 4), (2, 4, 5), (1, 2, 5), (3, 0, 4)]
    elif shape == "hipped" and L > W:
        r = hl - hw
        verts = base + [at(-r, 0, top), at(r, 0, top)]
        tris = [(0, 2, 1), (0, 3, 2), (0, 1, 5), (0, 5, 4), (2, 3, 4), (2, 4, 5), (1, 2, 5), (3, 0, 4)]
    elif shape == "skillion":
        side = 0  # index of the low edge: 0 = -v side, 1 = +u, 2 = +v, 3 = -u
        if direction is not None:
            d = (math.sin(math.radians(direction)), math.cos(math.radians(direction)))
            dots = [-(d[0] * v[0] + d[1] * v[1]), d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1], -(d[0] * u[0] + d[1] * u[1])]
            side = dots.index(max(dots))
        hi_a, hi_b = (side + 2) % 4, (side + 3) % 4  # the edge opposite the low one rises
        verts = base + [(base[hi_a][0], base[hi_a][1], top), (base[hi_b][0], base[hi_b][1], top)]
        lo_a, lo_b = side, (side + 1) % 4
        tris = [(0, 2, 1), (0, 3, 2), (lo_a, lo_b, 4), (lo_a, 4, 5), (lo_b, hi_a, 4), (hi_b, lo_a, 5), (hi_a, hi_b, 5), (hi_a, 5, 4)]
    else:  # pyramidal on the rectangle, and hipped on a square
        verts = base + [at(0, 0, top)]
        tris = [(0, 2, 1), (0, 3, 2), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    return verts, tris


def building_mesh(ring, ground, t, bottom=None):
    """One building or building:part (OSM Simple 3D Buildings): walls from min_height up to the eaves and a
    roof solid on top. `height` includes the roof; storeys count LEVEL_M. Returns (verts, tris, info), ENU metres;
    `bottom` overrides the walls' foot (prints stand everything on the ground)."""
    total, why = parse_height(t)
    has_height = why == "osm height"
    shape = str(t.get("roof:shape", "flat")).lower()
    kind = ROOF_AS.get(shape)
    info = {"why": why, "roof": "flat"}
    lo = _num(t, "min_height")
    if lo is None and _num(t, "building:min_level") is not None:
        lo = _num(t, "building:min_level") * LEVEL_M
    lo = lo or 0.0
    rh = 0.0
    if kind:
        (_, _), _, _, L, W = min_rect(ring)
        span = W / 2 if kind != "skillion" else W
        rh = _num(t, "roof:height")
        if rh is None and _num(t, "roof:levels") is not None:
            rh = _num(t, "roof:levels") * LEVEL_M
        if rh is None:
            ang = _num(t, "roof:angle")
            rh = math.tan(math.radians(ang if ang is not None else ROOF_PITCH_DEG)) * span
        fill = abs(poly_area(ring)) / max(L * W, 1e-9)
        if kind == "pyramidal" and is_convex(ring):
            pass
        elif fill < 0.75:
            info["roof"] = "flat (footprint not rectangular)"
            kind, rh = None, 0.0
    if has_height:  # height includes the roof
        eaves = total - rh if total - rh > lo + 0.5 else max(lo + 0.5, total * 0.6)
        rh = total - eaves if kind else 0.0
    elif why == "levels":  # building:levels counts from the ground, min_level storeys included; the roof sits on top
        eaves = max(total, lo + 0.5)
    else:
        eaves = lo + total
    z0 = ground - 0.3 if bottom is None and lo <= 0 else (ground + lo if bottom is None else bottom)
    verts, tris = prism(ring, z0, ground + eaves)
    if kind and rh > 0.05:
        along = str(t.get("roof:orientation", "along")).lower() != "across"
        rv, rt = roof_solid(kind, ring, ground + eaves, rh, along, _num(t, "roof:direction"))
        o = len(verts)
        verts += rv
        tris += [(a + o, b + o, c + o) for a, b, c in rt]
        info["roof"] = kind if kind == shape else "%s as %s" % (shape, kind)
    info["top"] = round(eaves + (rh if kind else 0.0), 2)
    return verts, tris, info


class Mesh:
    def __init__(self, name, color):
        self.name, self.color, self.v, self.f = name, color, [], []

    def add(self, verts, faces):
        o = len(self.v)
        self.v += verts
        self.f += [tuple(i + o for i in f) for f in faces]


def prism(ring, z0, z1):
    """Closed prism over a CCW ring (x, y). Returns (verts, tris) with ENU coordinates."""
    n = len(ring)
    verts = [(x, y, z0) for x, y in ring] + [(x, y, z1) for x, y in ring]
    tris = [(a + n, b + n, c + n) for a, b, c in earclip(ring)]
    tris += [(c, b, a) for a, b, c in earclip(ring)]
    for i in range(n):
        j = (i + 1) % n
        tris += [(i, j, j + n), (i, j + n, i + n)]
    return verts, tris


def ribbon(line, half, zf, lift, closed_depth=None):
    """A strip of width 2*half along a polyline (x, y), draped by zf(x, y) + lift. Optional closed slab."""
    pts = []
    for i, (x, y) in enumerate(line):
        a = line[max(i - 1, 0)]
        b = line[min(i + 1, len(line) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx_, ny_ = -dy / L * half, dx / L * half
        pts.append(((x + nx_, y + ny_), (x - nx_, y - ny_)))
    verts, tris = [], []
    for (l, r) in pts:
        verts += [(l[0], l[1], zf(*l) + lift), (r[0], r[1], zf(*r) + lift)]
    for i in range(len(pts) - 1):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        tris += [(a, b, d), (a, d, c)]
    if closed_depth is not None:
        m = len(verts)
        verts += [(x, y, z - lift - closed_depth) for x, y, z in verts[:m]]
        for i in range(len(pts) - 1):
            a, b, c, d = 2 * i + m, 2 * i + 1 + m, 2 * i + 2 + m, 2 * i + 3 + m
            tris += [(a, d, b), (a, c, d)]
            tris += [(2 * i, 2 * i + 2, c), (2 * i, c, a), (2 * i + 1, b, d), (2 * i + 1, d, 2 * i + 3)]
        last = len(pts) - 1
        tris += [(0, m, m + 1), (0, m + 1, 1), (2 * last, 2 * last + 1, 2 * last + 1 + m), (2 * last, 2 * last + 1 + m, 2 * last + m)]
    return verts, tris


def densify(line, step):
    out = [line[0]]
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L / step))
        for i in range(1, k + 1):
            out.append((x0 + (x1 - x0) * i / k, y0 + (y1 - y0) * i / k))
    return out


def terrain_block(vgrid, nx, ny, k, pz):
    """Closed, outward-facing solid under a height grid (row 0 north): top grid scaled by k with heights pz(z),
    four skirt walls and a flat bottom at z=0."""
    tile = Mesh("tile", GROUND_DEFAULT)
    top = [(x * k, y * k, pz(z)) for x, y, z in vgrid]
    bot = [(x * k, y * k, 0.0) for x, y, z in vgrid]
    tile.v = top + bot
    n = len(top)
    f = []
    for r in range(ny - 1):
        for c in range(nx - 1):
            i = r * nx + c
            f += [(i, i + nx, i + nx + 1), (i, i + nx + 1, i + 1)]
    rim = [0] + [c for c in range(1, nx)] + [r * nx + nx - 1 for r in range(1, ny)]         + [(ny - 1) * nx + c for c in range(nx - 2, -1, -1)] + [r * nx for r in range(ny - 2, 0, -1)]
    for i in range(len(rim)):  # the rim runs clockwise seen from above
        a, b = rim[i], rim[(i + 1) % len(rim)]
        f += [(a, b + n, a + n), (a, b, b + n)]
    for i in range(1, len(rim) - 1):  # bottom: a fan over the rectangle's rim
        f.append((rim[0] + n, rim[i] + n, rim[i + 1] + n))
    tile.f = f
    return tile


def write_glb(path, meshes, enu_to_gltf=True):
    """Meshes in ENU metres -> GLB (Y up, -Z north). One node per mesh, flat-shaded (no normals stored)."""
    bin_, views, accs, gmeshes, nodes, mats = bytearray(), [], [], [], [], []

    def add_view(data, target):
        while len(bin_) % 4:
            bin_.append(0)
        views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data), "target": target})
        bin_.extend(data)
        return len(views) - 1

    for m in meshes:
        if not m.f:
            continue
        vs = [(x, z, -y) for x, y, z in m.v] if enu_to_gltf else m.v
        flat = [c for v in vs for c in v]
        pv = add_view(struct.pack("<%df" % len(flat), *flat), 34962)
        lo = [min(v[i] for v in vs) for i in range(3)]
        hi = [max(v[i] for v in vs) for i in range(3)]
        accs.append({"bufferView": pv, "componentType": 5126, "count": len(vs), "type": "VEC3", "min": lo, "max": hi})
        pa = len(accs) - 1
        idx = [i for f in m.f for i in f]
        iv = add_view(struct.pack("<%dI" % len(idx), *idx), 34963)
        accs.append({"bufferView": iv, "componentType": 5125, "count": len(idx), "type": "SCALAR"})
        mats.append({"name": m.name, "pbrMetallicRoughness": {"baseColorFactor": list(m.color) + [1.0], "metallicFactor": 0.0, "roughnessFactor": 0.9}})
        gmeshes.append({"name": m.name, "primitives": [{"attributes": {"POSITION": pa}, "indices": len(accs) - 1, "material": len(mats) - 1}]})
        nodes.append({"name": m.name, "mesh": len(gmeshes) - 1})
    while len(bin_) % 4:
        bin_.append(0)
    g = {"asset": {"version": "2.0", "generator": "polywright %s" % VERSION}, "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
         "nodes": nodes, "meshes": gmeshes, "materials": mats, "accessors": accs, "bufferViews": views,
         "buffers": [{"byteLength": len(bin_)}]}
    js = json.dumps(g, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js)
        f.write(struct.pack("<I4s", len(bin_), b"BIN\x00") + bytes(bin_))


def write_stl(path, meshes, scale=1.0):
    tris = []
    for m in meshes:
        for a, b, c in m.f:
            tris.append((m.v[a], m.v[b], m.v[c]))
    with open(path, "wb") as f:
        f.write(b"polywright".ljust(80, b" ") + struct.pack("<I", len(tris)))
        for a, b, c in tris:
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx_, ny_, nz_ = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            L = math.sqrt(nx_ * nx_ + ny_ * ny_ + nz_ * nz_) or 1.0
            f.write(struct.pack("<12fH", nx_ / L, ny_ / L, nz_ / L, *(c_ * scale for c_ in a), *(c_ * scale for c_ in b), *(c_ * scale for c_ in c), 0))
    return len(tris)


def cmd_place(a):
    if a.bbox:
        s, w, n, e = [float(x) for x in a.bbox.split(",")]
    elif a.center:
        lat, lon = [float(x) for x in a.center.split(",")]
        half = a.size_m / 2.0
        loc = Local(lat, lon)
        s, n = lat - half / loc.ky, lat + half / loc.ky
        w, e = lon - half / loc.kx, lon + half / loc.kx
    else:
        return emit({"ok": False, "error": "give --bbox S,W,N,E or --center LAT,LON --size-m M"}, 2)
    if not (s < n and w < e):
        return emit({"ok": False, "error": "bbox must be S,W,N,E with S<N and W<E"}, 2)
    out = os.path.abspath(a.out)
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    loc = Local((s + n) / 2, (w + e) / 2)
    width_m, height_m = (e - w) * loc.kx, (n - s) * loc.ky
    if width_m * height_m > a.max_km2 * 1e6:
        return emit({"ok": False, "error": "area %.2f km2 is over --max-km2 %.1f (Overpass load and mesh size); split it or raise the limit" % (width_m * height_m / 1e6, a.max_km2)}, 2)
    notes, credits = [], ["Map data (c) OpenStreetMap contributors, ODbL 1.0 (openstreetmap.org/copyright)"]
    osm, src = fetch_osm(s, w, n, e, os.path.join(out, "data", "osm.json"), a.refresh)
    notes.append("OSM from %s" % src)
    # ---- elevation
    res_m = a.res or max(1.0, round(max(width_m, height_m) / 256.0, 1))
    nx, ny = max(2, min(1024, int(width_m / res_m) + 1)), max(2, min(1024, int(height_m / res_m) + 1))
    dem = a.dem
    in_us = -125 <= w <= -66 and 24 <= s <= 50
    vals = None
    demc = os.path.join(out, "data", "dem_%s_%dx%d.json" % (dem, nx, ny))
    if os.path.isfile(demc) and not a.refresh:
        cached = json.load(open(demc))
        vals, dem = cached["v"], cached["source"]
    else:
        if dem in ("auto", "usgs") and (in_us or dem == "usgs"):
            try:
                vals = dem_usgs(s, w, n, e, nx, ny)
                dem = "usgs"
            except Exception as ex:
                notes.append("USGS 3DEP failed (%s); trying terrarium" % str(ex)[:80])
        if vals is None and dem in ("auto", "usgs", "terrarium"):
            try:
                vals, z = dem_terrarium(s, w, n, e, nx, ny, res_m)
                dem = "terrarium z%d" % z
            except Exception as ex:
                notes.append("terrarium failed (%s); flat ground" % str(ex)[:80])
        if vals is None:
            vals, dem = [0.0] * (nx * ny), "flat"
        vals, holes = fill_nodata(vals)
        if holes:
            notes.append("%d no-data elevation cells filled with the minimum" % holes)
        json.dump({"source": dem, "v": vals}, open(demc, "w"))
    if dem.startswith("usgs"):
        credits.append("Elevation: USGS 3D Elevation Program (public domain)")
    elif dem.startswith("terrarium"):
        credits.append("Elevation: Mapzen Terrain Tiles on AWS (sources include SRTM, 3DEP, ETOPO1, EU-DEM; see github.com/tilezen/joerd attribution)")
    grid = Grid(s, w, n, e, nx, ny, vals)
    zmin = min(vals)

    def zf(x, y):
        return grid.at(loc.lat0 + y / loc.ky, loc.lon0 + x / loc.kx) - zmin

    # ---- OSM elements
    nodes = {el["id"]: el for el in osm.get("elements", []) if el["type"] == "node"}
    ways = {el["id"]: el for el in osm.get("elements", []) if el["type"] == "way"}

    def ring_of(wy):
        return [loc.xy(nodes[i]["lat"], nodes[i]["lon"]) for i in wy.get("nodes", []) if i in nodes]

    areas = []  # (tags, ring, osm id)
    holes = {}  # osm id -> inner rings (islands in a lake, clearings in a wood)
    for wy in ways.values():
        t = wy.get("tags", {})
        nd = wy.get("nodes", [])
        if len(nd) > 3 and nd[0] == nd[-1] and t:
            areas.append((t, ring_of(wy)[:-1], wy["id"]))
    for rel in (el for el in osm.get("elements", []) if el["type"] == "relation"):
        t = rel.get("tags", {})
        if t.get("type") == "multipolygon":
            outer = [ways[m["ref"]]["nodes"] for m in rel.get("members", [])
                     if m["type"] == "way" and m.get("role") == "outer" and m["ref"] in ways]
            for ids in stitch_rings(outer):
                r = [loc.xy(nodes[i]["lat"], nodes[i]["lon"]) for i in ids if i in nodes]
                if len(r) > 3:
                    areas.append((t, r[:-1], rel["id"]))
            inner = [ways[m["ref"]]["nodes"] for m in rel.get("members", [])
                     if m["type"] == "way" and m.get("role") == "inner" and m["ref"] in ways]
            holes[rel["id"]] = [[loc.xy(nodes[i]["lat"], nodes[i]["lon"]) for i in ids if i in nodes] for ids in stitch_rings(inner)]
    hw, hh = width_m / 2, height_m / 2
    clipped = []
    for t, ring, oid in areas:
        r = clean_ring(clip_ring(clean_ring(ring), hw, hh))
        if len(r) >= 3 and abs(poly_area(r)) > 0.5:
            clipped.append((t, r, oid))
    areas = clipped
    # ---- terrain classes per cell
    cls_names = [g[0] for g in GROUND]
    xs = [(-width_m / 2) + width_m * c / (nx - 1) for c in range(nx)]
    ys = [(height_m / 2) - height_m * r / (ny - 1) for r in range(ny)]
    cell_cls = [-1] * ((nx - 1) * (ny - 1))
    # Paint large areas first and smaller ones over them: an island (wood) inside a lake (water) or a pitch inside a
    # park wins because it is smaller, whatever its class.
    for t, ring, _id in sorted(areas, key=lambda a: -abs(poly_area(a[1]))):
        if "building" in t or len(ring) < 3:
            continue
        k = next((i for i, g in enumerate(GROUND) if g[1](t)), None)
        if k is None:
            continue
        bx0, bx1 = min(p[0] for p in ring), max(p[0] for p in ring)
        by0, by1 = min(p[1] for p in ring), max(p[1] for p in ring)
        c0 = max(0, int((bx0 + width_m / 2) / width_m * (nx - 1)))
        c1 = min(nx - 2, int((bx1 + width_m / 2) / width_m * (nx - 1)) + 1)
        r0 = max(0, int((height_m / 2 - by1) / height_m * (ny - 1)))
        r1 = min(ny - 2, int((height_m / 2 - by0) / height_m * (ny - 1)) + 1)
        for r in range(r0, r1 + 1):
            cy = (ys[r] + ys[r + 1]) / 2
            for c in range(c0, c1 + 1):
                i = r * (nx - 1) + c
                cx = (xs[c] + xs[c + 1]) / 2
                if point_in_poly(cx, cy, ring) and not any(point_in_poly(cx, cy, h) for h in holes.get(_id, ())):
                    cell_cls[i] = k
    # Hydro-flatten: lidar over water is noise; set each water body's grid points to its lowest one.
    flattened = 0
    for t, ring, _id in areas:
        if not GROUND[0][1](t) or "building" in t:
            continue
        bx0, bx1 = min(p[0] for p in ring), max(p[0] for p in ring)
        by0, by1 = min(p[1] for p in ring), max(p[1] for p in ring)
        inside = [r * nx + c for r in range(ny) if by0 <= ys[r] <= by1 for c in range(nx) if bx0 <= xs[c] <= bx1
                  and point_in_poly(xs[c], ys[r], ring) and not any(point_in_poly(xs[c], ys[r], h) for h in holes.get(_id, ()))]
        if len(inside) > 2:
            level = min(vals[i] for i in inside)
            for i in inside:
                vals[i] = level
            flattened += len(inside)
    zmin = min(vals)
    vgrid = [(xs[c], ys[r], vals[r * nx + c] - zmin) for r in range(ny) for c in range(nx)]
    terrain = {}
    for r in range(ny - 1):
        for c in range(nx - 1):
            k = cell_cls[r * (nx - 1) + c]
            i = r * nx + c
            terrain.setdefault(k, []).extend([(i, i + nx, i + nx + 1), (i, i + nx + 1, i + 1)])
    meshes = []
    for k, faces in sorted(terrain.items()):
        m = Mesh("ground_" + (cls_names[k] if k >= 0 else "default"), GROUND[k][2] if k >= 0 else GROUND_DEFAULT)
        m.v, m.f = vgrid, faces  # shared vertices; each class is its own primitive
        meshes.append(m)
    # ---- buildings
    bld = Mesh("buildings", (0.80, 0.76, 0.70))
    heights, bcount, hsrc, roofs = [], 0, {}, {}
    print_prisms = []
    parts = [ring for t, ring, _ in areas if "building:part" in t and t.get("building:part") != "no" and len(ring) >= 3]
    part_pts = [(sum(x for x, _ in r) / len(r), sum(y for _, y in r) / len(r)) for r in parts]
    for t, ring, oid in areas:
        is_part = "building:part" in t and t.get("building:part") != "no"
        if not (is_part or "building" in t) or len(ring) < 3 or t.get("building") in ("no",):
            continue
        if abs(poly_area(ring)) < a.min_building_m2:
            continue
        if not is_part and any(point_in_poly(x, y, ring) for x, y in part_pts):
            continue  # Simple 3D Buildings: an outline with parts is drawn by its parts
        if poly_area(ring) < 0:
            ring = ring[::-1]
        g0 = min(zf(x, y) for x, y in ring)
        v, f, info = building_mesh(ring, g0, t)
        hsrc[info["why"]] = hsrc.get(info["why"], 0) + 1
        roofs[info["roof"]] = roofs.get(info["roof"], 0) + 1
        bld.add(v, f)
        print_prisms.append((ring, g0, t))
        heights.append(info["top"])
        bcount += 1
    meshes.append(bld)
    # ---- roads, paths, waterways
    roads, paths, water = Mesh("roads", (0.32, 0.32, 0.34)), Mesh("paths", (0.78, 0.72, 0.60)), Mesh("waterways", (0.25, 0.48, 0.70))
    road_lines = []
    for wy in ways.values():
        t = wy.get("tags", {})
        hwy, ww = t.get("highway"), t.get("waterway")
        if not (hwy in ROAD_W or ww in ("stream", "river", "canal", "ditch", "drain")) or t.get("area") == "yes":
            continue
        width = ROAD_W.get(hwy, 2.0)
        try:
            width = float(t.get("width", width))
        except ValueError:
            pass
        for line in clip_line(ring_of(wy), width_m / 2 - 0.01, height_m / 2 - 0.01):
            line = densify(line, max(res_m, 2.0))
            if ww:
                v, f = ribbon(line, {"river": 8, "canal": 6}.get(ww, 1.5), zf, 0.05)
                water.add(v, f)
                continue
            v, f = ribbon(line, width / 2, zf, 0.08 if width >= 4 else 0.12)
            (roads if width >= 4 else paths).add(v, f)
            road_lines.append((line, width))
    meshes += [roads, paths, water]
    # ---- trees
    trees = Mesh("trees", (0.20, 0.42, 0.18))
    trunks = Mesh("tree_trunks", (0.40, 0.30, 0.20))
    tcount = 0
    if not a.no_trees:
        pts = []
        for nd in nodes.values():
            if nd.get("tags", {}).get("natural") == "tree":
                x, y = loc.xy(nd["lat"], nd["lon"])
                if abs(x) <= width_m / 2 and abs(y) <= height_m / 2:
                    try:
                        th = float(re.sub(r"[^0-9.]", "", nd["tags"].get("height", "")) or 0) or 9.0
                    except ValueError:
                        th = 9.0
                    pts.append((x, y, th))
        rnd = random.Random(7)
        for t, ring, _id in areas:
            if (t.get("natural") == "wood" or t.get("landuse") == "forest") and a.wood_density > 0:
                area = abs(poly_area(ring))
                bx0, bx1 = min(p[0] for p in ring), max(p[0] for p in ring)
                by0, by1 = min(p[1] for p in ring), max(p[1] for p in ring)
                for _ in range(int(area / 100.0 * a.wood_density)):
                    x, y = rnd.uniform(bx0, bx1), rnd.uniform(by0, by1)
                    if point_in_poly(x, y, ring) and abs(x) <= width_m / 2 and abs(y) <= height_m / 2:
                        pts.append((x, y, rnd.uniform(7, 14)))
        for x, y, th in pts:
            gz = zf(x, y)
            r = th * 0.32
            crown = [(x + r * math.cos(k * math.pi / 3), y + r * math.sin(k * math.pi / 3), gz + th * 0.55) for k in range(6)]
            vv = crown + [(x, y, gz + th), (x, y, gz + th * 0.3)]
            ff = [(k, (k + 1) % 6, 6) for k in range(6)] + [((k + 1) % 6, k, 7) for k in range(6)]
            trees.add(vv, ff)
            tv, tf = prism([(x - 0.2, y - 0.2), (x + 0.2, y - 0.2), (x + 0.2, y + 0.2), (x - 0.2, y + 0.2)], gz - 0.2, gz + th * 0.35)
            trunks.add(tv, tf)
            tcount += 1
        meshes += [trees, trunks]
    scene_path = os.path.join(out, "scene.glb")
    write_glb(scene_path, meshes)
    relief = max(vals) - zmin
    res = {"ok": True, "out": out, "scene": scene_path, "bbox": [s, w, n, e], "center": [round(loc.lat0, 7), round(loc.lon0, 7)],
           "size_m": [round(width_m, 1), round(height_m, 1)], "grid": [nx, ny], "res_m": res_m, "dem": dem,
           "relief_m": round(relief, 2), "elevation_min_m": round(zmin, 2),
           "counts": {"water_points_flattened": flattened, "buildings": bcount, "building_height_source": hsrc, "roofs": roofs, "road_segments": len(road_lines), "trees": tcount,
                      "ground_cells": {(cls_names[k] if k >= 0 else "default"): len(v) // 2 for k, v in terrain.items()}},
           "frame": "glTF: metres, +Y up, -Z north, +X east, origin at the bbox centre, y=0 at the lowest ground",
           "credits": credits, "notes": notes}
    # ---- print tile
    if a.print_mm:
        longest = max(width_m, height_m)
        k = a.print_mm / longest
        ex = a.exaggerate
        base = a.base_mm

        def pz(z):
            return base + z * k * ex

        tile = terrain_block(vgrid, nx, ny, k, pz)
        parts = [tile]
        b = Mesh("buildings", (0.8, 0.76, 0.7))
        dropped = 0
        for ring, g0, t in print_prisms:
            rr = [(x * k, y * k) for x, y in ring]
            if min(max(p[0] for p in rr) - min(p[0] for p in rr), max(p[1] for p in rr) - min(p[1] for p in rr)) < a.min_feature_mm:
                dropped += 1
                continue
            # parts above the ground (min_height) stand on it in a print: nothing prints in mid-air
            v, ff, _ = building_mesh(ring, g0, t, bottom=g0 - 1.0 / (k * ex))
            lift = max(0.0, a.min_feature_mm / 2 - (max(z for _, _, z in v) - g0) * k * ex)
            v = [(x * k, y * k, max(0.2, pz(g0) + (z - g0) * k * ex + (lift if z > g0 else 0.0))) for x, y, z in v]
            b.add(v, ff)
        parts.append(b)
        if a.print_roads:
            rd = Mesh("roads", (0.3, 0.3, 0.3))
            for line, width in road_lines:
                ln = [(x * k, y * k) for x, y in line]
                hw = max(width * k / 2, a.min_feature_mm / 2)
                v, ff = ribbon(ln, hw, lambda x, y: pz(zf(x / k, y / k)), a.road_mm, closed_depth=a.road_mm + 0.6)
                rd.add(v, ff)
            parts.append(rd)
        parts_stl = os.path.join(out, "print_parts.stl")
        ntri = write_stl(parts_stl, parts)
        pr = {"parts_stl": parts_stl, "tris": ntri, "size_mm": [round(width_m * k, 1), round(height_m * k, 1), round(pz(relief) + max(heights or [0]) * k * ex, 1)],
              "scale": "1:%d" % round(1 / k * 1000), "exaggerate": ex, "base_mm": base, "buildings_dropped_under_min_feature": dropped,
              "note": "overlapping closed shells; slicers union them, but run union for one manifold solid"}
        if backend() and not a.no_union:
            u = bpy_action("union", {"file": parts_stl, "out": os.path.join(out, "print.stl"), "voxel_fallback_mm": 0.2})
            pr["union"] = {k_: u.get(k_) for k_ in ("ok", "solver", "watertight", "tris", "error", "non_manifold_edges", "boundary_edges")}
            if u.get("ok"):
                pr["print_stl"] = os.path.join(out, "print.stl")
        res["print"] = pr
    with open(os.path.join(out, "place.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    res["next"] = "render scene.glb (pw.py render, --color material) and compare with an aerial photo; hand-detail landmarks; credits go in the game's or print's notes"
    return emit(res)


# ------------------------------------------------------------------------------------------ crowd

# OpenPose COCO-18 limbs (joint index pairs) and colours, the convention the pose ControlNets and Wan's pose
# control were trained on: one colour per limb, drawn at 60 percent over black, joints as dots.
POSE_LIMBS = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
              (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)]
POSE_COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
               (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
               (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


def hidden_face_points(j, cam):
    """COCO-18 indices a pose detector would not find from a camera at `cam`, given 18 world-space joints: the nose
    and each eye once turned away from the lens (a profile keeps the nose and the near eye), an ear behind the head.
    Pose controls read drawn face points as a face to the camera, so a back drawn with them becomes a face.
    Plain maths on (x, y, z) sequences, so pw_bpy passes mathutils vectors and the tests pass tuples."""
    def unit(a, b):
        v = [a[i] - b[i] for i in range(3)]
        n = math.sqrt(sum(c * c for c in v)) or 1.0
        return [c / n for c in v]
    head = [(j[16][i] + j[17][i]) / 2 for i in range(3)]
    to_cam = unit(cam, head)
    away = lambda i: sum(a * b for a, b in zip(unit(j[i], head), to_cam))  # noqa: E731
    return [i for i in (0, 14, 15) if away(i) < -0.2] + [i for i in (16, 17) if away(i) < -0.35]


def video_size_problems(W, H, frames):
    problems = []
    if W % 16 or H % 16:
        problems.append("size %dx%d: Wan wants both sides divisible by 16 (832x480, 1280x720)" % (W, H))
    if (frames - 1) % 4 and (frames - 5) % 17:
        problems.append("frames %d: Wan wants 4n+1 frames (49, 65, 81), MiniMax H3 17k+5 at 24 fps (56, 73, 209)" % frames)
    return problems


def draw_pose_frames(joints_path, out_dir, max_width=None):
    """OpenPose skeleton PNGs from the 2D joints pw_bpy wrote, far figures first so near ones overdraw them.
    Line width scales with each figure's height in pixels, up to `max_width`. A joint at (-1, -1) is hidden (a
    face turned away): it and its limbs are left out."""
    from PIL import Image, ImageDraw
    with open(joints_path, encoding="utf-8") as f:
        data = json.load(f)
    W, H = data["size"]
    os.makedirs(out_dir, exist_ok=True)
    drawn = 0
    for fr in data["frames"]:
        img = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(img)
        for _, pts in fr["people"]:
            seen = [x >= 0 and y >= 0 for x, y in pts]
            top = pts[0] if seen[0] else pts[1]
            feet = [pts[i][1] for i in (10, 13) if seen[i]] or [H]
            width = max(1, int(round(abs(top[1] - sum(feet) / len(feet)) / 45)))
            width = min(width, max_width or width)
            for i, (a, b) in enumerate(POSE_LIMBS):
                if seen[a] and seen[b]:
                    c = tuple(int(v * 0.6) for v in POSE_COLORS[i])
                    d.line([tuple(pts[a]), tuple(pts[b])], fill=c, width=width * 2)
            r = max(1, width)
            for i, (x, y) in enumerate(pts):
                if seen[i]:
                    d.ellipse([x - r, y - r, x + r, y + r], fill=POSE_COLORS[i])
            drawn += 1
        img.save(os.path.join(out_dir, "%04d.png" % fr["frame"]))
    return {"frames": len(data["frames"]), "skeletons": drawn}


def encode_passes(out, passes, fps, prefix=""):
    """One H.264 video per pass, `<prefix><pass>.mp4` (what ComfyUI's video loaders take): ffmpeg when it is on
    PATH, else Blender's own FFmpeg through the sequencer."""
    ff = shutil.which("ffmpeg")
    if not ff:
        jobs = [{"src": os.path.join(out, n), "dst": os.path.join(out, prefix + n + ".mp4")} for n in passes
                if os.path.isdir(os.path.join(out, n)) and any(f.endswith(".png") for f in os.listdir(os.path.join(out, n)))]
        if not jobs:
            return {}
        if not backend():
            return {"skipped": "no ffmpeg and no Blender; load the PNG folders with an image-sequence loader"}
        res = bpy_action("encode", {"jobs": jobs, "fps": fps})
        if not res.get("ok"):
            return {"error": res.get("error")}
        vids = {"encoder": "blender (no ffmpeg on PATH)"}
        for j in jobs:
            vids[os.path.basename(j["dst"])[len(prefix):-4]] = j["dst"] if j["dst"] in res["videos"] else {"error": "not written"}
        return vids
    vids = {}
    for name in passes:
        src = os.path.join(out, name)
        if not os.path.isdir(src) or not any(n.endswith(".png") for n in os.listdir(src)):
            continue
        dst = os.path.join(out, prefix + name + ".mp4")
        cmd = [ff, "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", "1",
               "-i", os.path.join(src, "%04d.png"), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", dst]
        r = subprocess.run(cmd, capture_output=True, text=True)
        vids[name] = dst if r.returncode == 0 and os.path.isfile(dst) else {"error": (r.stderr or "")[-300:]}
    return vids


def crowd_sheet(out, passes, frames=None, fps=None):
    """One image for one look: a row per pass, its first, middle and last rendered frame, or the rendered frames
    nearest each of `frames` (1-based); every cell labelled with the pass and the frame or second."""
    from PIL import Image, ImageDraw
    rows = []
    for name in passes:
        d = os.path.join(out, name)
        fs = sorted(n for n in os.listdir(d) if n.endswith(".png")) if os.path.isdir(d) else []
        if fs:
            pick = ([min(fs, key=lambda n: abs(int(n[:4]) - f)) for f in frames] if frames
                    else sorted({fs[0], fs[len(fs) // 2], fs[-1]}))
            rows.append((name, pick))
    if not rows:
        return None
    w, h = Image.open(os.path.join(out, rows[0][0], rows[0][1][0])).size
    tw, th = w // 2, h // 2
    sheet = Image.new("RGB", (tw * max(len(r) for _, r in rows), th * len(rows)), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    for r, (name, row) in enumerate(rows):
        for c, n in enumerate(row):
            im = Image.open(os.path.join(out, name, n))
            if im.mode.startswith("I"):  # 16-bit grey (mist): RGB conversion would clip it to white
                im = im.point(lambda v: v / 257).convert("L")
            sheet.paste(im.convert("RGB").resize((tw, th)), (c * tw, r * th))
            k = int(n[:4])
            draw.text((c * tw + 6, r * th + 4), "%s %s" % (name, "%.2fs" % ((k - 1) / fps) if fps else "f%d" % k), fill=(0, 200, 255))
    path = os.path.join(out, "sheet.png")
    sheet.save(path)
    return path


def cmd_crowd(a):
    W, H = (int(v) for v in a.size.lower().split("x"))
    problems = video_size_problems(W, H, a.frames)
    if problems and not a.any_size:
        return emit({"ok": False, "error": "; ".join(problems), "hint": "--any-size skips this check"}, 2)
    passes = [x.strip() for x in a.passes.split(",") if x.strip()]
    bad = [x for x in passes if x not in ("depth", "mist", "mask", "clay", "pose")]
    if bad:
        return emit({"ok": False, "error": "unknown pass %s (depth, mist, mask, clay, pose)" % ",".join(bad)}, 2)
    pt = lambda t: [float(v) for v in t.split(",")] if t else None
    out = os.path.abspath(a.out)
    params = {"out": out, "size": [W, H], "frames": a.frames, "fps": a.fps, "sides": a.sides, "ranks": a.ranks,
              "cols": a.cols, "spacing": a.spacing, "rank_spacing": a.rank_spacing, "gap": a.gap, "jitter": a.jitter,
              "action": a.action, "action_b": a.action_b, "kit": [k for k in a.kit.split(",") if k],
              "view": a.view, "lens": a.lens, "cam_dist": a.cam_dist, "cam_height": a.cam_height,
              "cam": pt(a.cam), "aim": pt(a.aim), "move": a.move, "seed": a.seed, "passes": passes,
              "pose_min_px": a.pose_min_px, "samples": a.samples, "gpu": a.gpu, "far": a.far,
              "preview": a.preview, "save_blend": a.save_blend, "scatter": a.scatter, "scatter_gap": a.scatter_gap,
              "scatter_depth": a.scatter_depth}
    res = bpy_action("crowd", params, timeout=a.timeout)
    if not res.get("ok"):
        return emit(res, 1)
    if "pose" in passes:
        try:
            res["pose"] = draw_pose_frames(os.path.join(out, "joints.json"), os.path.join(out, "pose"))
        except ImportError:
            res["pose"] = {"skipped": "drawing skeletons needs Pillow (pip install pillow); joints.json is written"}
    if not a.preview:
        res["videos"] = encode_passes(out, passes, a.fps)
    try:
        res["sheet"] = crowd_sheet(out, passes)
    except ImportError:
        pass
    res["next"] = ("Read sheet.png: both sides in frame, readable ranks, no figure crossing the camera. Then feed "
                   "depth.mp4 (and pose.mp4 for the front ranks) to Wan VACE or Fun Control with a start frame "
                   "repainted from clay frame 1 (polywright hub, 'Crowd and battle blockouts')")
    return emit(res)


# ------------------------------------------------------------------------------------------ duel

# A fighter's frame: faces local +X, left +Y, up +Z. `root` and the feet are in it; hands are relative to their
# shoulder; blade directions are in the same frame (null: no blade in that hand for this pose).
DUEL_FIELDS = {"root": 2, "yaw": 0, "pelvis_z": 0, "spine": 3, "chest": 3, "rhand": 3, "lhand": 3,
               "rblade": 3, "lblade": 3, "rfoot": 3, "lfoot": 3}
DUEL_POSES = {
    "stand": {"root": [0, 0], "yaw": 0, "pelvis_z": 0.95, "spine": [0, 0, 1], "chest": [1, 0, 0],
              "rhand": [0.05, -0.05, -0.58], "lhand": [0.05, 0.05, -0.58], "rblade": [0.3, 0, -1], "lblade": [0.3, 0, -1],
              "rfoot": [0, -0.12, 0.08], "lfoot": [0, 0.12, 0.08]},
    "guard": {"base": "stand", "pelvis_z": 0.88, "spine": [0.08, 0, 1], "chest": [0.8, 0.6, 0],
              "rhand": [0.42, -0.05, -0.12], "rblade": [1, 0, 0.15], "lhand": [0.15, 0.15, -0.25], "lblade": [1, 0.2, 0.4],
              "rfoot": [0.35, -0.1, 0.08], "lfoot": [-0.3, 0.15, 0.08]},
    "guard_low": {"base": "guard", "rhand": [0.35, -0.05, -0.3], "rblade": [1, 0, -0.35],
                  "lhand": [0.25, 0.1, -0.35], "lblade": [1, 0.1, -0.2]},
    "kneel": {"base": "stand", "pelvis_z": 0.6, "rfoot": [-0.42, -0.12, 0.08], "lfoot": [-0.42, 0.12, 0.08]},
}
DUEL_PASSES = ["canny", "depth", "depth_thick", "pose", "clay"]
FLY_PARTS = {"rblade": "right", "rguard": "right", "lblade": "left", "lguard": "left", "hood": "cloak", "cloak": "cloak"}


def duel_resolve(name, pool):
    """A named pose with its base chain applied (base first, overrides last)."""
    chain, seen = [], set()
    while name is not None:
        if name in seen:
            raise ValueError("pose %s: its base chain loops" % name)
        if name not in pool:
            raise ValueError("unknown pose %s" % name)
        seen.add(name)
        chain.append(pool[name])
        name = pool[name].get("base")
    out = {}
    for s in reversed(chain):
        out.update({k: v for k, v in s.items() if k != "base"})
    return out


def duel_mix(a, b, u):
    if a is None or b is None:  # a blade appears or goes: switch halfway
        return a if u < 0.5 else b
    if isinstance(a, list):
        return [x + (y - x) * u for x, y in zip(a, b)]
    return a + (b - a) * u


def duel_pose_at(keys, t, pool):
    """The pose at t seconds from [[seconds, name], ...]: held before the first and after the last key,
    smoothstep between keys."""
    if t <= keys[0][0]:
        return duel_resolve(keys[0][1], pool)
    for (t0, n0), (t1, n1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            a, b = duel_resolve(n0, pool), duel_resolve(n1, pool)
            u = (t - t0) / max(t1 - t0, 1e-6)
            u = u * u * (3 - 2 * u)
            return {k: duel_mix(a[k], b.get(k, a[k]), u) for k in a}
    return duel_resolve(keys[-1][1], pool)


def duel_frames(spec, preview=False):
    """(frames to render, frames for the sheet), 0-based: the sheet shows frame 1, each check second and the last."""
    n, fps = spec["frames"], spec["fps"]
    sheet = sorted({0, n - 1} | {min(n - 1, max(0, int(round(t * fps)))) for t in spec.get("check_s", [])})
    return (sheet if preview else list(range(n))), sheet


def bearing(a, b):
    """Compass bearing in degrees from point a to point b (0 faces +Y, 90 faces +X)."""
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


def duel_load(spec, base_dir=".", any_size=False):
    """Check a duel file and fill its defaults. Returns (spec, problems); paths become absolute."""
    s, P = dict(spec), []
    num = lambda v, n: isinstance(v, (list, tuple)) and len(v) == n and all(isinstance(x, (int, float)) for x in v)  # noqa: E731
    s.setdefault("name", "duel")
    s["size"] = [int(v) for v in s.get("size", [864, 480])]
    s["frames"], s["fps"] = int(s.get("frames", 73)), int(s.get("fps", 24))
    s.setdefault("check_s", [])
    for k, d in (("near", 1.0), ("far", 30.0), ("thick_blade_m", 0.045)):
        s[k] = float(s.get(k, d))
    s["canny"] = list(s.get("canny", [12, 40]))
    if s["frames"] < 1 or s["fps"] < 1:
        P.append("frames and fps must be positive")
    if not any_size:
        P += video_size_problems(s["size"][0], s["size"][1], s["frames"])
    if not 0 < s["near"] < s["far"]:
        P.append("near must be above 0 and below far")
    room = dict(s.get("room") or {})
    for k in ("blend", "script"):
        if room.get(k):
            room[k] = os.path.abspath(os.path.join(base_dir, room[k]))
            if not os.path.isfile(room[k]):
                P.append("room %s not found: %s" % (k, room[k]))
    s["room"] = room
    cam = s.get("camera") or {}
    if not (cam.get("object") or (num(cam.get("pos"), 3) and num(cam.get("aim"), 3))):
        P.append("camera needs pos and aim ([x, y, z]) or the name of a camera object in the room")
    ox, oy = (s.get("origin") or [0, 0])[:2]
    pool = dict(DUEL_POSES, **s.get("poses", {}))
    figs = s.get("fighters") or s.get("figures") or {}
    if not figs:
        P.append("no fighters")
    s["fighters"] = {}
    for name, f in figs.items():
        f = dict(f)
        if not num(f.get("mark"), 2):
            P.append("%s: mark must be [x, y]" % name)
            continue
        f["mark"] = [f["mark"][0] + ox, f["mark"][1] + oy]
        f.setdefault("scale", 1.0)
        f.setdefault("weapons", {})
        if any(h not in ("right", "left") or not v or v <= 0 for h, v in f["weapons"].items()):
            P.append("%s: weapons are {\"right\": metres, \"left\": metres}" % name)
        keys = f.get("keys") or []
        if not keys or any(not isinstance(k, (list, tuple)) or len(k) != 2 for k in keys):
            P.append("%s: keys must be [[seconds, pose name], ...]" % name)
            continue
        if any(b[0] < a[0] for a, b in zip(keys, keys[1:])):
            P.append("%s: keys out of time order" % name)
        for _, pose in keys:
            try:
                q = duel_resolve(pose, pool)
            except ValueError as e:
                P.append("%s: %s" % (name, e))
                continue
            for fld, n in DUEL_FIELDS.items():
                v = q.get(fld, "missing")
                ok = isinstance(v, (int, float)) if n == 0 else (num(v, n) or (v is None and fld.endswith("blade")))
                if not ok:
                    P.append("pose %s: %s must be %s" % (pose, fld, "a number" if n == 0 else "%d numbers" % n))
        s["fighters"][name] = f
    for name, f in s["fighters"].items():
        fc = f.get("facing", 90)
        if isinstance(fc, str):
            if fc not in s["fighters"] or fc == name:
                P.append("%s: facing %r is neither a bearing nor another fighter" % (name, fc))
                fc = 0
            else:
                fc = bearing(f["mark"], s["fighters"][fc]["mark"])
        f["facing"] = float(fc)
    s["fly"] = [dict(x) for x in s.get("fly", [])]
    for i, x in enumerate(s["fly"]):
        x["fighter"] = x.get("fighter") or x.get("figure")
        f = s["fighters"].get(x["fighter"])
        if f is None:
            P.append("fly %d: no fighter %r" % (i, x["fighter"]))
            continue
        bad = [p for p in x.get("parts", []) if FLY_PARTS.get(p) not in list(f["weapons"]) + (["cloak"] if f.get("cloak") else [])]
        if bad or not x.get("parts"):
            P.append("fly %d: %s cannot throw %s" % (i, x["fighter"], ",".join(bad) or "nothing (parts is empty)"))
        if not (num(x.get("to"), 2) and float(x.get("t1", 0)) > float(x.get("t0", 0))):
            P.append("fly %d: needs to [x, y] and t1 after t0" % i)
        else:
            x["to"] = [x["to"][0] + ox, x["to"][1] + oy]
    return s, P


def cmd_duel(a):
    path = os.path.abspath(a.duel)
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError) as e:
        return emit({"ok": False, "error": "cannot read %s: %s" % (a.duel, e)}, 2)
    raw.setdefault("name", os.path.splitext(os.path.basename(path))[0])
    spec, problems = duel_load(raw, os.path.dirname(path), a.any_size)
    if problems:
        return emit({"ok": False, "error": "; ".join(problems), "hint": "--any-size skips the size and frame-count check"}, 2)
    render, sheet = duel_frames(spec, a.preview)
    fps, (W, H) = spec["fps"], spec["size"]
    pool = dict(DUEL_POSES, **spec.get("poses", {}))
    poses = {n: [duel_pose_at(f["keys"], k / fps, pool) for k in render] for n, f in spec["fighters"].items()}
    for x in spec["fly"]:
        x["pose_t0"] = duel_pose_at(spec["fighters"][x["fighter"]]["keys"], float(x["t0"]), pool)
    out = os.path.abspath(a.out or os.path.join(os.path.dirname(path), spec["name"]))
    res = {"ok": True, "name": spec["name"], "out": out, "size": [W, H], "frames": spec["frames"], "fps": fps,
           "seconds": round(spec["frames"] / fps, 2), "frames_to_render": len(render), "sheet_frames": [k + 1 for k in sheet],
           "fighters": {n: {"mark": f["mark"], "facing": round(f["facing"], 1), "keys": len(f["keys"])} for n, f in spec["fighters"].items()}}
    if a.check:
        return emit(dict(res, check="valid; nothing rendered"))
    params = {"out": out, "size": [W, H], "fps": fps, "render": render, "spec": spec, "poses": poses,
              "gpu": a.gpu, "samples": a.samples, "save_blend": a.save_blend}
    r = bpy_action("duel", params, timeout=a.timeout)
    if not r.get("ok"):
        return emit(r, 1)
    res.update({k: r[k] for k in ("in_frame", "near_m", "far_m", "render_seconds") if k in r})
    try:
        res["pose"] = draw_pose_frames(os.path.join(out, "joints.json"), os.path.join(out, "pose"), max_width=3)
    except ImportError:
        res["pose"] = {"skipped": "drawing skeletons needs Pillow (pip install pillow); joints.json is written"}
    if not a.preview:
        res["videos"] = encode_passes(out, DUEL_PASSES, fps, prefix=spec["name"] + "_")
    try:
        res["sheet"] = crowd_sheet(out, DUEL_PASSES, [k + 1 for k in sheet], fps)
    except ImportError:
        pass
    res["warnings"] = ["%s: %d%% of the joints in frame at the %s frame; move the camera or the mark" % (n, v * 100, w)
                       for n, d in res.get("in_frame", {}).items() for w, v in d.items() if v < 0.5]
    res["next"] = ("Read sheet.png: each fighter's facing and the blades at every check time, both ends in frame. Then "
                   "give the video model one control: depth_thick (holds a back to the camera; try 0.8 strength ending "
                   "at 0.6), canny (start and end states), or pose (nose and eyes left out when turned away)")
    return emit(res)


# ------------------------------------------------------------------------------------------ main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="pw.py", description="polywright: 3D model work for AI agents (one JSON object per command)")
    ap.add_argument("--version", action="version", version=VERSION)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("doctor", help="what is installed")
    p.add_argument("--host", help="ComfyUI URL(s), comma-separated")
    p.set_defaults(fn=cmd_doctor)

    p = sub.add_parser("inspect", help="report on a model file")
    p.add_argument("file")
    p.add_argument("--fast", action="store_true", help="skip topology checks (edges, parts, volume)")
    p.add_argument("--topology", action="store_true", help="also report quads, poles, flipped and stacked faces, loose parts, UV texel spread (Blender)")
    p.set_defaults(fn=cmd_inspect)

    p = sub.add_parser("render", help="orthographic views and a contact sheet")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--views", default="front,right,back,left,top,iso")
    p.add_argument("--size", type=int, default=640)
    p.add_argument("--color", choices=["clay", "material", "texture"], default="clay")
    p.add_argument("--engine", choices=["workbench", "eevee", "cycles"], default="workbench")
    p.add_argument("--cols", type=int, default=3)
    p.add_argument("--no-sheet", action="store_true")
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("spritecam", help="fit a game's orthographic sprite camera from ground diamonds (groundBase corners) in a JSON file")
    p.add_argument("bases", help="any JSON holding groundBase {front,left,right} corners (a building registry) or bare {front,left,right} objects")
    p.add_argument("--tiles", type=int, default=2, help="footprint side in tiles of the diamonds to use")
    p.add_argument("--tile-px", type=int, default=48, help="canvas pixels per tile (canvas = tiles x tile-px)")
    p.add_argument("--tile-m", type=float, default=5.0, help="metres per tile in the model")
    p.add_argument("--max-rms", type=float, default=4.0, help="drop diamonds that fit worse than this (px)")
    p.add_argument("--like", help="name of one sprite whose footprint centre and scale the new one should take")
    p.add_argument("--out", help="camera.json to write")
    p.set_defaults(fn=cmd_spritecam)

    p = sub.add_parser("sprite", help="render a model through a sprite camera: beauty, clay, depth, normal, id, pos, line passes, loop frames, groundBase")
    p.add_argument("file", help="the model; a .blend keeps its scene properties sprite_parts, loop, rings, footprint_m")
    p.add_argument("--camera", required=True, help="camera.json from pw.py spritecam")
    p.add_argument("--out", required=True, help="output folder")
    p.add_argument("--passes", default="beauty,clay,depth,normal,id", help="comma list: beauty, clay, depth, normal, id, pos")
    p.add_argument("--frames", type=int, default=0, help="loop frames to render (the scene's loop property)")
    p.add_argument("--frame-passes", default="beauty,id", help="passes per loop frame (add pos for model-driven animation)")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--scale", type=float, default=0, help="render pixels per canvas pixel (default the camera's render_scale; 1024/96 for diffusion input)")
    p.add_argument("--hide", default="", help="comma list of object-name prefixes left out (a plate without the moving part)")
    p.add_argument("--footprint-m", help="X,Y footprint in metres when the scene does not say")
    p.add_argument("--pos-extent", type=float, default=2.5, help="pos pass: object coordinates in [-e, e] m map to 0..1")
    p.add_argument("--no-line", action="store_true", help="skip the line-art pass")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--timeout", type=int, default=1800)
    p.set_defaults(fn=cmd_sprite)

    p = sub.add_parser("framecam", help="grid-search perspective cameras that put named points in screen boxes and keep text bands clear")
    p.add_argument("problem", help="JSON: points, boxes, keep_in_frame, bands, keep_out_of_bands, size_measure, search (cli.md)")
    p.add_argument("--out", help="cameras.json to write or merge the presets into")
    p.add_argument("--name", default="framecam", help="preset name prefix (<name>_1 is the best)")
    p.add_argument("--top", type=int, default=3, help="how many cameras to keep (at least 1.5 position steps apart)")
    p.add_argument("--max-evals", type=int, default=3_000_000, help="refuse searches with more cameras than this")
    p.set_defaults(fn=cmd_framecam)

    p = sub.add_parser("scene", help="render a scene illustration's passes through a perspective camera preset: clay, beauty, depth, normal, id, line, scene.json")
    p.add_argument("file", help="the scene (.blend keeps its scene properties scene_parts, rings, scene_points)")
    p.add_argument("--cameras", required=True, help="cameras.json: {cameras: {NAME: {pos, target, lens_mm, depth_near_m, depth_far_m}}, sun, sky}")
    p.add_argument("--camera", required=True, help="preset name in cameras.json")
    p.add_argument("--out", required=True, help="output folder")
    p.add_argument("--size", default="1280x720", help="WxH; the paint workflow's first-pass size")
    p.add_argument("--passes", default=",".join(SCENE_PASSES), help="comma list: " + ", ".join(SCENE_PASSES))
    p.add_argument("--samples", type=int, default=48, help="Cycles samples for beauty")
    p.add_argument("--hide", default="", help="comma list of object-name prefixes left out (a plate without the hero)")
    p.add_argument("--keep-lights", action="store_true", help="keep the file's lights and world instead of the preset sun and sky")
    p.add_argument("--sky", help="TOP:HORIZON colours R,G,B:R,G,B (0-255): also write beauty_sky.png, the sky repainted through the id alpha")
    p.add_argument("--no-line", action="store_true", help="skip the line-art pass")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--timeout", type=int, default=1800)
    p.set_defaults(fn=cmd_scene)

    p = sub.add_parser("match", help="render a model from an existing picture's camera (RGBA), paste it in, write a blend mask")
    p.add_argument("file", help="the model (.blend, .glb, ...), forward axis +X, up +Z")
    p.add_argument("--out", required=True, help="RGBA render (.png); with --still also <out>_paste.png and <out>_mask.png")
    p.add_argument("--still", help="the picture to match (sets the size) and paste into")
    p.add_argument("--size", default="1344x768", help="WxH when there is no --still")
    p.add_argument("--anchor-px", required=True, help="x,y pixel where the anchor lands (a hand holding it)")
    p.add_argument("--anchor-local", default="0,0,0", help="x,y,z of that point on the model, metres")
    p.add_argument("--aim-px", required=True, help="x,y pixel where the aim point must land (the tip)")
    p.add_argument("--aim-local", required=True, help="x,y,z of the aim point on the model (ahead of the anchor along +X)")
    p.add_argument("--depth", type=float, default=3.0, help="metres from camera to anchor: sets the size in frame (match a known width)")
    p.add_argument("--lens", type=float, default=35.0, help="mm on a 36 mm sensor")
    p.add_argument("--horizon", type=float, help="pixel row of the horizon (camera pitch); default the image centre")
    p.add_argument("--roll", type=float, default=0.0, help="degrees about the forward axis")
    p.add_argument("--sun-dir", default="-0.8,0.6,0.25", help="direction to the key light (x right, y into the picture, z up)")
    p.add_argument("--keep-lights", action="store_true", help="use the .blend's own lights")
    p.add_argument("--engine", choices=["cycles", "eevee"], default="cycles")
    p.add_argument("--gpu", action="store_true", help="Cycles on the GPU (default CPU: the GPU is often busy)")
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--hide", action="append", default=[], help="x0,y0,x1,y1 box of the render to drop (in front of the model); repeatable")
    p.add_argument("--grow", type=int, default=10, help="px to grow the mask around the model")
    p.add_argument("--mask-add", action="append", default=[], help="x0,y0,x1,y1 ellipse added to the mask (the hands); repeatable")
    p.set_defaults(fn=cmd_match)

    p = sub.add_parser("convert", help="convert, scale, decimate")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--size-m", type=float, help="scale so the longest side is this many metres")
    p.add_argument("--ground", action="store_true", help="lowest point to z=0")
    p.add_argument("--center", action="store_true", help="centre on x and y")
    p.add_argument("--level", action="store_true", help="stand it on its base: the largest flat face of its hull near the bottom turned to face down (Pixal3D output leans by the camera's elevation)")
    p.add_argument("--tilt-deg", type=float, help="instead of --level: rotate this many degrees about X (a known camera elevation)")
    p.add_argument("--max-tilt-deg", type=float, default=45.0, help="--level only considers bases within this angle of down")
    p.add_argument("--join", action="store_true")
    p.add_argument("--apply", action="store_true", help="flatten hierarchy and apply transforms")
    p.add_argument("--max-tris", type=int)
    p.add_argument("--ratio", type=float, help="decimate ratio 0..1")
    p.add_argument("--uv", action="store_true", help="Smart UV Project every mesh (generated meshes have no UVs)")
    p.add_argument("--fix-winding", action="store_true", help="flip faces that wind against their neighbours (the flipped faces inspect --topology counts), keeping UVs")
    p.add_argument("--draco", action="store_true")
    p.add_argument("--export-scale", type=float, default=1.0, help="global scale for OBJ/STL/PLY export (1000 for metres to mm)")
    p.add_argument("--fbx-bake-axes", action="store_true", help="FBX: bake the axis change into the mesh (Unity likes this)")
    p.set_defaults(fn=cmd_convert)

    p = sub.add_parser("lods", help="levels of detail by decimation")
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--ratios", default="1,0.5,0.25,0.1")
    p.add_argument("--format", default="glb")
    p.set_defaults(fn=cmd_lods)

    p = sub.add_parser("printable", help="any mesh to one watertight solid in mm")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--size-mm", type=float, default=100.0)
    p.add_argument("--size-axis", choices=["longest", "height", "width", "depth"], default="longest")
    p.add_argument("--wall-mm", type=float, default=1.0, help="thickness given to open surfaces before remeshing")
    p.add_argument("--voxel-mm", type=float, help="remesh voxel; default size/500")
    p.add_argument("--base-cut-mm", type=float, default=0.6)
    p.add_argument("--max-tris", type=int, default=400000)
    p.add_argument("--drop", help="comma-separated name or material substrings to delete first")
    p.add_argument("--up", choices=["z", "y"], default="z", help="y: source is Y-up and was not rotated on import")
    p.add_argument("--no-remesh", action="store_true")
    p.add_argument("--no-planar", action="store_true", help="keep the remesh's even triangles on flat faces")
    p.add_argument("--seal-mm", type=float, default=1.0, help="a hollow shell's openings up to this wide are sealed before its inside is filled (grooves this narrow fill too)")
    p.add_argument("--hollow", action="store_true", help="keep a hollow shell hollow (no cavity fill)")
    p.add_argument("--blend", help="also save the result as a .blend")
    p.add_argument("--timeout", type=int, default=3600)
    p.set_defaults(fn=cmd_printable)

    p = sub.add_parser("union", help="boolean-union the closed parts of a file into one solid")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--scale", type=float)
    p.add_argument("--solver", choices=["manifold", "exact"], default="manifold")
    p.add_argument("--voxel-fallback", type=float, help="voxel size to remesh with if the union is not watertight")
    p.add_argument("--timeout", type=int, default=3600)
    p.set_defaults(fn=cmd_union)

    p = sub.add_parser("3mf", help="pack STL/OBJ/GLB meshes (in mm) into one 3MF, one object each")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--scale", type=float, default=1.0, help="e.g. 1000 when the meshes are in metres")
    p.set_defaults(fn=cmd_3mf)

    p = sub.add_parser("check", help="check a model against a target's budgets")
    p.add_argument("file", nargs="?")
    p.add_argument("--target")
    p.add_argument("--real-size-m", type=float, help="the real object's longest side, to catch unit mistakes")
    p.add_argument("--thickness-samples", type=int, default=20000, help="surface points for the wall-thickness pass (targets with min_feature)")
    p.add_argument("--no-thickness", action="store_true", help="skip the wall-thickness pass")
    p.add_argument("--list", action="store_true")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("new", help="scaffold an asset folder with a manifest")
    p.add_argument("dir")
    p.add_argument("--name", required=True)
    p.add_argument("--kind", choices=KINDS, default="imagined")
    p.add_argument("--route", choices=ROUTES, default="mixed")
    p.add_argument("--targets", default="")
    p.add_argument("--brief")
    p.add_argument("--real-size-m", type=float)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("manifest", help="record sources, outputs, tools; validate")
    p.add_argument("dir")
    p.add_argument("--add-source")
    p.add_argument("--what")
    p.add_argument("--author")
    p.add_argument("--licence")
    p.add_argument("--add-output")
    p.add_argument("--target")
    p.add_argument("--inspect", action="store_true", help="record tris, size and watertightness of the output")
    p.add_argument("--add-tool")
    p.add_argument("--tool-version")
    p.add_argument("--status", choices=["brief", "references", "blockout", "model", "review", "delivered"])
    p.add_argument("--validate", action="store_true", help="also compare output hashes")
    p.add_argument("--review", help="a review render (renders/<step>/sheet.png) to record with --verdict")
    p.add_argument("--verdict", help="what the review found")
    p.add_argument("--by", help="agent or user (default agent)")
    p.set_defaults(fn=cmd_manifest)

    p = sub.add_parser("turnaround", help="eye-level views of a textured model on flat grey, a video model's reference pictures")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--views", default="front,3q,side,back", help="front, 3q, side, 3q_back, back, 3q_left, left")
    p.add_argument("--yaw", type=float, default=0.0, help="degrees about +Z that turn the model's face to -Y")
    p.add_argument("--height-m", type=float, help="scale to this height first (the picture is framed either way)")
    p.add_argument("--size", default="768x1152")
    p.add_argument("--lens", type=float, default=85.0)
    p.add_argument("--elev", type=float, default=4.0, help="camera degrees above the model's middle (20 for props)")
    p.add_argument("--grey", type=float, default=0.5, help="backdrop as an sRGB value (0.5 = mid-grey)")
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--no-sheet", action="store_true")
    p.add_argument("--timeout", type=int, default=1800)
    p.set_defaults(fn=cmd_turnaround)

    p = sub.add_parser("mark", help="finish a generated figure: recolour, erase a smeared painted marking, put a clean one on, real size")
    p.add_argument("file")
    p.add_argument("--out", required=True, help="GLB (or any export format); the fixed texture lands beside it")
    p.add_argument("--recolour", help="H,S,V (0-1) measured on the photo's plastic: matching texels get hue H, "
                                      "saturation and value scaled so their medians become S and V")
    p.add_argument("--from-hue", default="0,1", help="only texels whose hue is in LO,HI")
    p.add_argument("--min-sat", type=float, default=0.12)
    p.add_argument("--min-val", type=float, default=0.0, help="leave darker texels alone (a black body's faint tint)")
    p.add_argument("--erase", choices=["white", "red"], help="clear this colour on the head's front faces only")
    p.add_argument("--head-frac", type=float, default=0.13, help="top share of the model that is the head")
    p.add_argument("--front-dot", type=float, default=0.5)
    p.add_argument("--text", help="the marking, e.g. A or 2, as a thin text mesh on the head's front face")
    p.add_argument("--colour", default="0.95,0.95,0.95", help="sRGB 0-1")
    p.add_argument("--font", help="a .ttf/.otf; Blender's built-in font otherwise")
    p.add_argument("--text-frac", type=float, default=0.75, help="letter height as a share of the face height")
    p.add_argument("--width-frac", type=float, default=0.92, help="and at most this share of its width")
    p.add_argument("--text-dx", type=float, default=0.0)
    p.add_argument("--text-dz", type=float, default=0.0)
    p.add_argument("--yaw", type=float, default=0.0)
    p.add_argument("--height-m", type=float)
    p.add_argument("--longest-m", type=float, help="scale by the longest side instead (props lying any way)")
    p.add_argument("--timeout", type=int, default=1800)
    p.set_defaults(fn=cmd_mark)

    p = sub.add_parser("lineup", help="a few generated figures on a table, teams on fixed sides: colour, clay, depth, mask")
    p.add_argument("--layout", required=True, help="JSON: size, lens, cam, aim, table, backdrop_m, figures (cli.md)")
    p.add_argument("--out", required=True)
    p.add_argument("--frames", default="", help="also loop the passes into control videos of these lengths, e.g. 107,362")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--card", default="lineup", help="control_<card>_<pass>_<n>f.mp4")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--preview", action="store_true", help="clay and depth only, half size")
    p.add_argument("--timeout", type=int, default=1800)
    p.set_defaults(fn=cmd_lineup)

    p = sub.add_parser("bpy", help="run a bpy script headless with condensed output")
    p.add_argument("script")
    p.add_argument("--blend", help="open this .blend first")
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--lines", type=int, default=40)
    p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(fn=cmd_bpy)

    p = sub.add_parser("gen", help="image to 3D with Hunyuan3D-2 on ComfyUI")
    p.add_argument("--image", required=True, help="front view")
    p.add_argument("--left")
    p.add_argument("--back")
    p.add_argument("--right")
    p.add_argument("--out", required=True)
    p.add_argument("--host")
    p.add_argument("--ckpt")
    p.add_argument("--turbo", action="store_true")
    p.add_argument("--steps", type=int)
    p.add_argument("--octree", type=int, default=256)
    p.add_argument("--seed", type=int)
    p.add_argument("--no-prep", action="store_true")
    p.add_argument("--timeout", type=int, default=3600)
    p.add_argument("--workflow", help="any ComfyUI workflow in API format (TRELLIS.2, Pixal3D, ...) instead of the built-in Hunyuan3D-2 graph")
    p.add_argument("--save-api", help="also write the graph as sent (API format), e.g. after converting a UI workflow")
    p.add_argument("--set", action="append", help="NODE.input=VALUE (node id or class_type; @file uploads an image); repeatable")
    p.set_defaults(fn=cmd_gen)

    p = sub.add_parser("place", help="a real place from OpenStreetMap and elevation data")
    p.add_argument("--bbox", help="S,W,N,E in degrees")
    p.add_argument("--center", help="LAT,LON")
    p.add_argument("--size-m", type=float, default=400.0)
    p.add_argument("--out", required=True)
    p.add_argument("--dem", choices=["auto", "usgs", "terrarium", "flat"], default="auto")
    p.add_argument("--res", type=float, help="terrain grid spacing in metres (default size/256, at least 1)")
    p.add_argument("--no-trees", action="store_true")
    p.add_argument("--wood-density", type=float, default=1.0, help="trees per 100 m2 scattered in woods")
    p.add_argument("--min-building-m2", type=float, default=6.0)
    p.add_argument("--max-km2", type=float, default=4.0)
    p.add_argument("--refresh", action="store_true", help="refetch instead of using data/ caches")
    p.add_argument("--print-mm", type=float, help="also build a print tile this many mm on its longest side")
    p.add_argument("--exaggerate", type=float, default=1.5, help="vertical exaggeration for the print tile")
    p.add_argument("--base-mm", type=float, default=3.0)
    p.add_argument("--min-feature-mm", type=float, default=1.2)
    p.add_argument("--print-roads", action="store_true")
    p.add_argument("--road-mm", type=float, default=0.4)
    p.add_argument("--no-union", action="store_true")
    p.set_defaults(fn=cmd_place)

    p = sub.add_parser("crowd", help="an army blockout in Blender with depth, pose, mask and clay passes for a video model")
    p.add_argument("--out", required=True, help="folder: depth/ mask/ clay/ pose/ PNGs, <pass>.mp4, joints.json, camera.json, sheet.png")
    p.add_argument("--size", default="832x480", help="WxH, both divisible by 16 for Wan")
    p.add_argument("--frames", type=int, default=81, help="4n+1 for Wan (49, 65, 81); 17k+5 for MiniMax H3 (56, 73, 209, with --fps 24)")
    p.add_argument("--fps", type=int, default=16)
    p.add_argument("--sides", type=int, choices=[1, 2], default=2)
    p.add_argument("--ranks", type=int, default=6, help="rows deep per side")
    p.add_argument("--cols", type=int, default=30, help="figures across the frontage per side")
    p.add_argument("--spacing", type=float, default=1.1, help="metres between figures in a rank")
    p.add_argument("--rank-spacing", type=float, default=1.4, help="metres between ranks")
    p.add_argument("--gap", type=float, help="metres between the front ranks at frame 1 (default: they meet on screen for clash and charge, 30 otherwise)")
    p.add_argument("--jitter", type=float, default=0.25, help="metres of random placement per figure")
    p.add_argument("--action", choices=["hold", "march", "advance", "charge", "clash"], default="march", help="side A (and B unless --action-b)")
    p.add_argument("--action-b", choices=["hold", "march", "advance", "charge", "clash"])
    p.add_argument("--kit", default="spear,shield,helmet", help="any of spear, shield, helmet; empty for bare figures")
    p.add_argument("--view", choices=["side", "behind", "high"], default="side")
    p.add_argument("--lens", type=float, default=50.0, help="mm on a 36 mm sensor; long lenses stack the ranks")
    p.add_argument("--cam-dist", type=float, help="metres (default: both armies fit the frame)")
    p.add_argument("--cam-height", type=float, default=6.0)
    p.add_argument("--cam", help="x,y,z camera position, overrides --view (battle line x=0, frontage along +y)")
    p.add_argument("--aim", help="x,y,z point the camera looks at")
    p.add_argument("--move", choices=["static", "push", "crane", "truck"], default="static")
    p.add_argument("--passes", default="depth,mask,clay,pose",
                   help="any of depth, mist, mask, clay, pose; mist is Blender's Mist pass, near white, 16-bit")
    p.add_argument("--pose-min-px", type=float, default=40, help="skip skeletons of figures shorter than this on screen")
    p.add_argument("--scatter", type=int, default=0, help="about this many standing background figures per side, scattered behind the last rank (Geometry Nodes instances; no skeletons)")
    p.add_argument("--scatter-gap", type=float, default=1.2, help="metres between scattered figures at least")
    p.add_argument("--scatter-depth", type=float, default=25.0, help="metres deep behind the last rank")
    p.add_argument("--far", type=float, help="metres where depth reaches black (default: past the farthest figure)")
    p.add_argument("--samples", type=int, default=4, help="Cycles samples for the depth pass")
    p.add_argument("--gpu", action="store_true", help="Cycles on the GPU (default CPU: the GPU is often busy)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--preview", action="store_true", help="render only the first, middle and last frame")
    p.add_argument("--save-blend", action="store_true", help="also save crowd.blend")
    p.add_argument("--any-size", action="store_true", help="skip the Wan size and frame-count check")
    p.add_argument("--timeout", type=int, default=3600)
    p.set_defaults(fn=cmd_crowd)

    p = sub.add_parser("duel", help="two posed fighters in a set, through the shot's camera: clay, Canny, depth, thick-blade depth and pose controls")
    p.add_argument("duel", help="the duel file (JSON): room, camera, fighters with marks and keyed poses, thrown props")
    p.add_argument("--out", help="folder (default: <the file's folder>/<name>)")
    p.add_argument("--preview", action="store_true", help="render only frame 1, the check_s frames and the last frame")
    p.add_argument("--check", action="store_true", help="validate the file and print the schedule; no Blender")
    p.add_argument("--gpu", action="store_true", help="Cycles on the GPU for the depth passes")
    p.add_argument("--samples", type=int, default=4)
    p.add_argument("--any-size", action="store_true", help="skip the Wan and H3 size and frame-count check")
    p.add_argument("--save-blend", action="store_true", help="also save duel.blend")
    p.add_argument("--timeout", type=int, default=3600)
    p.set_defaults(fn=cmd_duel)

    p = sub.add_parser("texture", help="quick height, normal and roughness maps from a photo")
    p.add_argument("image")
    p.add_argument("--out", required=True)
    p.add_argument("--seamless", action="store_true")
    p.add_argument("--strength", type=float, default=2.0)
    p.add_argument("--convention", choices=["opengl", "directx"], default="opengl")
    p.set_defaults(fn=cmd_texture)

    a = ap.parse_args(argv)
    if not getattr(a, "fn", None):
        ap.print_help()
        return 2
    if getattr(a, "args", None) and a.args[:1] == ["--"]:
        a.args = a.args[1:]
    try:
        return a.fn(a)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # fail soft: one JSON object, never a bare traceback
        return emit({"ok": False, "error": "%s: %s" % (type(e).__name__, e)}, 1)


if __name__ == "__main__":
    sys.exit(main())
