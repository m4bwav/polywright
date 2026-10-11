#!/usr/bin/env python3
"""polywright CLI: 3D model work for AI agents, one JSON object per command.

Standard library only (Python 3.9+), Windows, macOS and Linux. Blender does the heavy work through pw_bpy.py;
commands that need it say so in the JSON when Blender is missing instead of crashing.

  python pw.py doctor                                  what is installed: Blender, Python libs, CLIs, ComfyUI hosts
  python pw.py inspect FILE [--fast]                   tris, objects, size, materials, images, UVs, watertight, parts
  python pw.py render FILE --out DIR [--views ..] [--color clay|material|texture] [--size 640]
                                                       orthographic views + contact sheet for a vision model to judge
  python pw.py convert IN OUT [--size-m X] [--scale F] [--ground] [--center] [--join] [--max-tris N] [--draco]
  python pw.py lods IN --out DIR [--ratios 1,0.5,0.25,0.1] [--format glb]
  python pw.py printable IN OUT.stl --size-mm 100 [--wall-mm 1] [--voxel-mm V] [--base-cut-mm 0.6] [--drop a,b]
  python pw.py union IN OUT.stl                        boolean-union closed parts into one solid
  python pw.py 3mf A.stl [B.stl ..] --out X.3mf        one 3MF, one object per input (AMS colours)
  python pw.py check FILE --target T [--real-size-m X] targets: python pw.py check --list
  python pw.py new DIR --name N [--kind real|imagined|hybrid] [--targets game-unity,print-fdm]
  python pw.py manifest DIR [--add-output PATH --target T] [--add-source URL --licence L --author A] [--validate]
  python pw.py bpy SCRIPT.py [--blend FILE] [--timeout S] [-- script args]   run your bpy script headless
  python pw.py gen --image FRONT.png [--left L --back B --right R] --out raw.glb [--host URL] [--steps 30]
  python pw.py gen --image IMG.png --workflow trellis2.api.json --out model.glb [--set NODE.input=VALUE]
  python pw.py place --bbox S,W,N,E --out DIR [--dem auto|usgs|terrarium|flat] [--res M] [--print-mm 200]
  python pw.py texture IMG --out DIR [--seamless] [--strength 2]   quick normal/height/roughness maps

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
import urllib.parse
import urllib.request
import uuid
import zlib

VERSION = "0.1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
BPY_SCRIPT = os.path.join(HERE, "pw_bpy.py")
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


def bpy_action(action, params, timeout=1800):
    tmp = tempfile.mkdtemp(prefix="pw_")
    pp, rp = os.path.join(tmp, "params.json"), os.path.join(tmp, "result.json")
    with open(pp, "w", encoding="utf-8") as f:
        json.dump(params, f)
    r = run_blender_script(BPY_SCRIPT, [action, pp, rp], timeout=timeout)
    if os.path.isfile(rp):
        with open(rp, encoding="utf-8") as f:
            res = json.load(f)
    else:
        res = {"ok": False, "action": action, "error": r.get("error") or "Blender exited %s without a result" % r.get("exit_code"),
               "log": condense((r.get("stdout") or "") + "\n" + (r.get("stderr") or ""))}
    shutil.rmtree(tmp, ignore_errors=True)
    return res


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


def inspect_file(path, fast=False):
    if not os.path.isfile(path):
        return {"ok": False, "error": "file not found: %s" % path}
    ext = os.path.splitext(path)[1].lower()
    if backend() and ext != ".3mf":
        res = bpy_action("inspect", {"file": os.path.abspath(path), "deep": not fast})
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
    res["file_bytes"] = os.path.getsize(path)
    return res


def cmd_inspect(a):
    res = inspect_file(a.file, a.fast)
    return emit(res, 0 if res.get("ok") else 1)


def cmd_render(a):
    params = {"file": os.path.abspath(a.file), "out": os.path.abspath(a.out), "size": a.size, "color": a.color,
              "engine": a.engine, "views": a.views.split(","), "sheet": not a.no_sheet, "cols": a.cols}
    res = bpy_action("render", params)
    if res.get("ok"):
        res["next"] = "Read sheet.png (one image) and judge silhouette, proportions, scale, missing parts, shading artifacts"
    return emit(res, 0 if res.get("ok") else 1)


def cmd_convert(a):
    params = {"file": os.path.abspath(a.input), "out": os.path.abspath(a.output), "scale": a.scale, "size_m": a.size_m,
              "ground": a.ground, "center": a.center, "join": a.join, "max_tris": a.max_tris, "ratio": a.ratio,
              "apply": a.apply, "uv": a.uv, "draco": a.draco, "export_scale": a.export_scale, "fbx_bake_axes": a.fbx_bake_axes}
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


def cmd_check(a):
    targets = load_targets()
    if a.list or not a.target:
        return emit({"targets": {k: v.get("about", "") for k, v in targets["targets"].items()}, "checked": targets.get("checked")})
    if a.target not in targets["targets"]:
        return emit({"ok": False, "error": "unknown target %s" % a.target, "known": list(targets["targets"])}, 2)
    t = targets["targets"][a.target]
    info = inspect_file(a.file)
    if not info.get("ok"):
        return emit(info, 1)
    rules = t.get("rules", {})
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
        rule("min_feature", "unchecked", "not measured here: render it and look for parts thinner than %s %s, or run a wall-thickness check" % (rules["min_feature"], unit), "info")
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
                 "inspect": {k: info.get(k) for k in ("tris", "objects", "dims", "watertight", "parts", "materials", "max_image_px", "backend", "blender")}},
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

def cmd_bpy(a):
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
    res = http_json(host + "/prompt", data=json.dumps({"prompt": graph, "client_id": "polywright"}).encode(), timeout=60,
                    headers={"Content-Type": "application/json"})
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


def run_workflow(a):
    """Any ComfyUI workflow saved in API format (Workflow > Export (API)): TRELLIS.2, Pixal3D, Hunyuan3D 2.1,
    a partner-API node. The image goes into every LoadImage node unless --set says otherwise."""
    graph = json.load(open(a.workflow, encoding="utf-8"))
    if "nodes" in graph and "links" in graph:
        return emit({"ok": False, "error": "this is a UI workflow; export it with Workflow > Export (API) in ComfyUI"}, 2)
    host, tried = None, []
    for h in comfy_hosts(a.host):
        try:
            info = http_json(h + "/object_info", timeout=20)
            missing = sorted({v.get("class_type") for v in graph.values() if v.get("class_type") not in info})
            tried.append({"host": h, "missing_nodes": missing})
            if not missing:
                host = h
                break
        except Exception as e:
            tried.append({"host": h, "up": False, "error": str(e)[:100]})
    if not host:
        return emit({"ok": False, "error": "no ComfyUI host has every node in the workflow", "tried": tried}, 1)
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
    heights, bcount, hsrc = [], 0, {}
    print_prisms = []
    for t, ring, oid in areas:
        if "building" not in t or len(ring) < 3 or t.get("building") in ("no",):
            continue
        if abs(poly_area(ring)) < a.min_building_m2:
            continue
        if poly_area(ring) < 0:
            ring = ring[::-1]
        h, why = parse_height(t)
        hsrc[why] = hsrc.get(why, 0) + 1
        ground = [zf(x, y) for x, y in ring]
        z0, z1 = min(ground) - 0.3, min(ground) + h
        v, f = prism(ring, z0, z1)
        bld.add(v, f)
        print_prisms.append((ring, min(ground), h))
        heights.append(h)
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
    res = {"ok": True, "out": out, "scene": scene_path, "bbox": [s, w, n, e], "center": [loc.lat0, loc.lon0],
           "size_m": [round(width_m, 1), round(height_m, 1)], "grid": [nx, ny], "res_m": res_m, "dem": dem,
           "relief_m": round(relief, 2), "elevation_min_m": round(zmin, 2),
           "counts": {"water_points_flattened": flattened, "buildings": bcount, "building_height_source": hsrc, "road_segments": len(road_lines), "trees": tcount,
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
        for ring, g0, h in print_prisms:
            rr = [(x * k, y * k) for x, y in ring]
            if min(max(p[0] for p in rr) - min(p[0] for p in rr), max(p[1] for p in rr) - min(p[1] for p in rr)) < a.min_feature_mm:
                dropped += 1
                continue
            v, ff = prism(rr, max(0.2, pz(g0) - 1.0), pz(g0) + max(h * k * ex, a.min_feature_mm / 2))
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

    p = sub.add_parser("convert", help="convert, scale, decimate")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--size-m", type=float, help="scale so the longest side is this many metres")
    p.add_argument("--ground", action="store_true", help="lowest point to z=0")
    p.add_argument("--center", action="store_true", help="centre on x and y")
    p.add_argument("--join", action="store_true")
    p.add_argument("--apply", action="store_true", help="flatten hierarchy and apply transforms")
    p.add_argument("--max-tris", type=int)
    p.add_argument("--ratio", type=float, help="decimate ratio 0..1")
    p.add_argument("--uv", action="store_true", help="Smart UV Project every mesh (generated meshes have no UVs)")
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
    p.set_defaults(fn=cmd_manifest)

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
