"""pw_camplan.py - the planning half of `pw.py camplan` (standard library only).

A shot file holds timed camera operations whose intervals may overlap. Each frame, every operation's progress is
eased with smoothstep over its own interval and the operations are combined by fixed rules: follows move the pivot,
dolly ratios multiply the ground distance to the pivot, orbit angles add around it, truck and pedestal offsets add
after that, pan, tilt and roll angles add to the aim, zoom and frame-subject ratios multiply the lens. Then a pinhole
projection (Blender's: sensor fitted to the width) checks the framing: the subject's screen height as a fraction of
the frame height, its centre against a screen position, and whether any of its points leaves the frame.

The operation names, defaults (dolly in 0.72, dolly out 1.35, orbit 28 deg, pan 20, tilt 15, zoom to 50 mm,
frame subject 0.65), the overlap rules and the smoothstep easing follow FilmFlow (arXiv:2610.30753, CC BY 4.0); the
paper released no code and gives no framing metric, so this executor and the framing check are written fresh.
"""
import math
import random

DEFAULTS = {  # canonical method -> parameter defaults
    "static": {}, "dollyin": {"distance_scale": 0.72}, "dollyout": {"distance_scale": 1.35},
    "truck": {"metres": 1.0, "direction": "right"}, "pedestal": {"metres": 1.0},
    "pedestalup": {"metres": 1.0}, "pedestaldown": {"metres": 1.0},
    "orbit": {"orbit_angle_deg": 28.0, "direction": "right"}, "pan": {"angle_deg": 20.0, "direction": "right"},
    "tilt": {"angle_deg": 15.0, "direction": "up"}, "roll": {"angle_deg": 10.0}, "zoom": {"focal_target": 50.0},
    "aimfollow": {}, "positionfollow": {"strength": 1.0}, "heightfollow": {"strength": 1.0},
    "framesubject": {"height_fraction": 0.65}, "screenpositionlock": {"uv": [0.5, 0.5]},
    "handheld": {"amplitude_deg": 0.5, "amplitude_m": 0.01, "frequency_hz": 1.2, "seed": 1}, "horizonlock": {},
}
ALIASES = {"shake": "handheld", "follow": "positionfollow", "crane": "pedestal", "pushin": "dollyin", "pullout": "dollyout",
           "arc": "orbit", "boom": "pedestal"}


def canon(method):
    m = "".join(ch for ch in str(method).lower() if ch.isalnum())
    return ALIASES.get(m, m)


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def add(a, b, s=1.0):
    return [a[i] + b[i] * s for i in range(3)]


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def subject_at(s, t):
    """Feet point at t seconds: linear between [[t, [x, y, z]], ...] keys, held outside them."""
    keys = s["path"]
    if t <= keys[0][0]:
        return list(keys[0][1])
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            return [p0[i] + (p1[i] - p0[i]) * u for i in range(3)]
    return list(keys[-1][1])


def load(spec, presets=None):
    """Check a shot and fill defaults. Returns (spec, problems)."""
    s, P = dict(spec), []
    vec = lambda v: isinstance(v, (list, tuple)) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v)  # noqa: E731
    s["fps"] = int(s.get("fps", 24))
    s["duration_sec"] = float(s.get("duration_sec", 4))
    size = s.get("size", [1920, 1080])
    s["size"] = [int(v) for v in (size.lower().split("x") if isinstance(size, str) else size)]
    s["sensor_mm"] = float(s.get("sensor_mm", 36.0))
    if s["fps"] < 1 or s["duration_sec"] <= 0:
        P.append("fps and duration_sec must be positive")
    cam = dict(s.get("camera") or {})
    if cam.get("preset"):
        pr = (presets or {}).get(cam["preset"])
        if pr is None:
            P.append("camera preset %r not found (give --presets cameras.json from pw.py framecam)" % cam["preset"])
        else:
            cam = dict(pr, **{k: v for k, v in cam.items() if k != "preset"})
    cam.setdefault("aim", cam.get("target"))
    cam["lens_mm"] = float(cam.get("lens_mm", cam.get("lens", 35)))
    subs = {}
    for name, x in (s.get("subjects") or {}).items():
        x = dict(x)
        if vec(x.get("pos")):
            x["path"] = [[0, list(x["pos"])]]
        if x.get("path"):
            x["path"] = sorted([float(k[0]), [float(v) for v in k[1]]] for k in x["path"])
        elif not x.get("object"):
            P.append("subject %s needs pos [x, y, z], path [[t, [x, y, z]], ...] or object (with --blend)" % name)
        x["height"] = float(x.get("height", 1.8))
        x["width"] = float(x.get("width", 0.5))
        subs[name] = x
    s["subjects"] = subs
    if isinstance(cam.get("aim"), str) and cam["aim"] not in subs:
        P.append("camera aim %r is not a subject" % cam["aim"])
    if not vec(cam.get("pos")) or not (vec(cam.get("aim")) or isinstance(cam.get("aim"), str)):
        P.append("camera needs pos [x, y, z] and aim ([x, y, z] or a subject name), or a framecam preset")
    s["camera"] = cam
    fr = dict(s.get("framing") or {})
    fr.setdefault("subject", next(iter(subs), None))
    fr.setdefault("height_fraction", 0.45)
    fr.setdefault("tolerance", 0.12)
    if fr["subject"] is not None and fr["subject"] not in subs:
        P.append("framing subject %r is not a subject" % fr["subject"])
    s["framing"] = fr
    ops = []
    for i, op in enumerate(s.get("operations") or []):
        m = canon(op.get("method", ""))
        if m not in DEFAULTS:
            P.append("operation %s: unknown method %r (%s)" % (op.get("op_id", i + 1), op.get("method"), ", ".join(sorted(DEFAULTS))))
            continue
        a, b = float(op.get("start_sec", 0)), float(op.get("end_sec", s["duration_sec"]))
        if b < a or (b == a and m != "static"):
            P.append("operation %s: end_sec must come after start_sec" % op.get("op_id", i + 1))
        par = dict(DEFAULTS[m], **(op.get("parameters") or {}))
        who = op.get("subject") or par.get("subject") or fr["subject"]
        if m in ("aimfollow", "positionfollow", "heightfollow", "framesubject", "screenpositionlock") and who not in subs:
            P.append("operation %s: %s needs a subject" % (op.get("op_id", i + 1), op.get("method")))
        ops.append({"op_id": op.get("op_id", i + 1), "method": m, "start_sec": a, "end_sec": b, "parameters": par,
                    "subject": who, "easing": op.get("easing", "step" if m in ("screenpositionlock", "horizonlock") else "smoothstep")})
    s["operations"] = ops
    return s, P


def progress(op, t):
    a, b = op["start_sec"], op["end_sec"]
    if b <= a or op["easing"] == "step":  # locks hold from their start
        return float(t >= a)
    u = min(1.0, max(0.0, (t - a) / (b - a)))
    return u if op["easing"] == "linear" else smoothstep(u)


def centre(s, t):
    f = subject_at(s, t)
    return [f[0], f[1], f[2] + s["height"] / 2]


def basis(yaw, pitch, roll):
    fwd = [math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)]
    right = [math.sin(yaw), -math.cos(yaw), 0.0]
    up = cross(right, fwd)
    c, sn = math.cos(roll), math.sin(roll)
    return fwd, [right[i] * c + up[i] * sn for i in range(3)], [up[i] * c - right[i] * sn for i in range(3)]


def project(cam, p, size, sensor):
    """(u, v, depth): u from the left, v from the bottom, as Blender's world_to_camera_view."""
    d = sub(p, cam["pos"])
    z = dot(d, cam["fwd"])
    if z <= 1e-6:
        return None, None, z
    k = cam["lens_mm"] / sensor
    return 0.5 + dot(d, cam["right"]) / z * k, 0.5 + dot(d, cam["up"]) / z * k * size[0] / size[1], z


def look(pos, aim):
    d = sub(aim, pos)
    return math.atan2(d[1], d[0]), math.atan2(d[2], math.hypot(d[0], d[1]))


def noise(seed, t, freq):
    rng = random.Random(seed)
    out = []
    for _ in range(6):
        ph = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
        out.append(sum(w * math.sin(2 * math.pi * freq * m * t + p) for w, m, p in zip((1, 0.5, 0.25), (1, 2.13, 3.71), ph)) / 1.75)
    return out


def camera_at(s, t):
    cam0, subs, ops = s["camera"], s["subjects"], s["operations"]
    fs = subs.get(s["framing"]["subject"])
    aim0 = centre(subs[cam0["aim"]], 0) if isinstance(cam0["aim"], str) else list(cam0["aim"])
    pivot0 = subject_at(fs, 0) if fs else aim0
    off = sub(cam0["pos"], pivot0)
    r, ang, z = math.hypot(off[0], off[1]), math.atan2(off[1], off[0]), off[2]
    pivot, lens, truck, ped = list(pivot0), cam0["lens_mm"], 0.0, 0.0
    for op in ops:  # position group: follows, then scale channels and orbit angles
        k, m, q = progress(op, t), op["method"], op["parameters"]
        if m in ("positionfollow", "heightfollow"):
            sj = subs[op["subject"]]
            d = sub(subject_at(sj, min(max(t, op["start_sec"]), op["end_sec"])), subject_at(sj, op["start_sec"]))
            if m == "heightfollow":
                d = [0, 0, d[2]]
            pivot = add(pivot, d, float(q["strength"]))
        elif m in ("dollyin", "dollyout"):
            r *= 1 + (float(q["distance_scale"]) - 1) * k
        elif m == "orbit":
            ang += math.radians(float(q["orbit_angle_deg"])) * k * (1 if q["direction"] == "right" else -1)
        elif m == "truck":
            truck += float(q["metres"]) * k * (1 if q["direction"] == "right" else -1)
        elif m.startswith("pedestal"):
            ped += float(q["metres"]) * k * (-1 if m == "pedestaldown" else 1)
        elif m == "zoom":
            lens *= 1 + (float(q["focal_target"]) / cam0["lens_mm"] - 1) * k
    pos = [pivot[0] + r * math.cos(ang), pivot[1] + r * math.sin(ang), pivot[2] + z]
    yaw_h = math.atan2(-math.sin(ang), -math.cos(ang))
    pos = add(pos, [math.sin(yaw_h), -math.cos(yaw_h), 0], truck)
    pos[2] += ped
    aim = add(aim0, sub(pivot, pivot0))
    if isinstance(cam0["aim"], str):
        aim = centre(subs[cam0["aim"]], t)
    for op in ops:
        if op["method"] == "aimfollow":
            aim = add(aim, sub(centre(subs[op["subject"]], t), aim), progress(op, t))
    yaw, pitch = look(pos, aim)
    roll, jit = 0.0, [0.0] * 3
    for op in ops:  # orientation group: lock, then angles add (pan, tilt, roll), shake, horizon
        k, m, q = progress(op, t), op["method"], op["parameters"]
        if m == "screenpositionlock":
            y2, p2 = look(pos, centre(subs[op["subject"]], t))
            u, v = q["uv"]
            y2 += math.atan((u - 0.5) * s["sensor_mm"] / lens)
            p2 += math.atan((v - 0.5) * s["sensor_mm"] * s["size"][1] / s["size"][0] / lens)
            yaw, pitch = yaw + wrap(y2 - yaw) * k, pitch + (p2 - pitch) * k
    for op in ops:
        k, m, q = progress(op, t), op["method"], op["parameters"]
        if m == "pan":
            yaw -= math.radians(float(q["angle_deg"])) * k * (1 if q["direction"] == "right" else -1)
        elif m == "tilt":
            pitch += math.radians(float(q["angle_deg"])) * k * (1 if q["direction"] == "up" else -1)
        elif m == "roll":
            roll += math.radians(float(q["angle_deg"])) * k
        elif m == "handheld" and op["start_sec"] <= t <= op["end_sec"]:
            env = min(1.0, (t - op["start_sec"]) / 0.25, (op["end_sec"] - t) / 0.25)
            n = noise(q["seed"], t, float(q["frequency_hz"]))
            a, mm = math.radians(float(q["amplitude_deg"])) * env, float(q["amplitude_m"]) * env
            yaw, pitch, roll = yaw + n[0] * a, pitch + n[1] * a, roll + n[2] * a
            jit = add(jit, [n[3] * mm, n[4] * mm, n[5] * mm])
    for op in ops:
        if op["method"] == "horizonlock":
            roll *= 1 - progress(op, t)
    pos = add(pos, jit)
    fwd, right, up = basis(yaw, pitch, roll)
    cam = {"pos": pos, "fwd": fwd, "right": right, "up": up, "lens_mm": lens}
    for op in ops:  # framing group last: it needs the final view
        if op["method"] == "framesubject":
            h = measure(cam, subs[op["subject"]], t, s)["height_fraction"]
            if h:
                cam["lens_mm"] *= 1 + (float(op["parameters"]["height_fraction"]) / h - 1) * progress(op, t)
    cam["aim"] = aim
    cam["roll_deg"] = math.degrees(roll)
    return cam


def subject_points(sj, t, cam):
    f = subject_at(sj, t)
    head = [f[0], f[1], f[2] + sj["height"]]
    side = [cam["right"][0], cam["right"][1], 0.0]
    n = math.hypot(side[0], side[1]) or 1.0
    mid = [f[0], f[1], f[2] + sj["height"] / 2]
    w = sj["width"] / 2 / n
    return [f, head, add(mid, side, w), add(mid, side, -w)]


def measure(cam, sj, t, s):
    pts = [project(cam, p, s["size"], s["sensor_mm"]) for p in subject_points(sj, t, cam)]
    out = any(u is None or not (0 <= u <= 1 and 0 <= v <= 1) for u, v, _ in pts)
    if pts[0][0] is None or pts[1][0] is None:
        return {"height_fraction": None, "centre_uv": None, "out": True}
    (uf, vf, _), (uh, vh, _) = pts[0], pts[1]
    h = math.hypot((uh - uf) * s["size"][0] / s["size"][1], vh - vf)
    return {"height_fraction": h, "centre_uv": [(uf + uh) / 2, (vf + vh) / 2], "out": out}


def matrix_rows(cam):
    p, r, u, f = cam["pos"], cam["right"], cam["up"], cam["fwd"]
    rows = [[r[i], u[i], -f[i], p[i]] for i in range(3)] + [[0, 0, 0, 1]]
    return [round(v, 6) for row in rows for v in row]


def plan(s):
    """Per-frame cameras and the framing report for a loaded shot."""
    fps, fr = s["fps"], s["framing"]
    n = int(round(s["duration_sec"] * fps)) + 1
    sj = s["subjects"].get(fr["subject"])
    target, tol = float(fr["height_fraction"]), float(fr["tolerance"])
    uv_t, uv_tol = fr.get("screen_uv"), fr.get("uv_tolerance")
    frames, rows = [], []
    for i in range(n):
        t = i / fps
        cam = camera_at(s, t)
        frames.append({"frame": i + 1, "t": round(t, 4), "pos": [round(v, 5) for v in cam["pos"]],
                       "aim": [round(v, 5) for v in cam["aim"]], "lens_mm": round(cam["lens_mm"], 4),
                       "roll_deg": round(cam["roll_deg"], 4), "matrix_world": matrix_rows(cam)})
        if sj:
            m = measure(cam, sj, t, s)
            h = m["height_fraction"]
            row = {"frame": i + 1, "t": round(t, 4), "height_fraction": None if h is None else round(h, 4),
                   "height_error": None if h is None else round(abs(h - target), 4),
                   "centre_uv": m["centre_uv"] and [round(v, 4) for v in m["centre_uv"]], "out": m["out"]}
            if uv_t and m["centre_uv"]:
                row["uv_error"] = round(math.hypot(m["centre_uv"][0] - uv_t[0], m["centre_uv"][1] - uv_t[1]), 4)
            rows.append(row)
    report = {"frames": n, "subject": fr["subject"]}
    if rows:
        hs = [r["height_fraction"] for r in rows if r["height_fraction"] is not None]
        errs = [r["height_error"] for r in rows if r["height_error"] is not None]
        out = [r["frame"] for r in rows if r["out"]]
        report.update({"target": target, "tolerance": tol,
                       "height_first": hs[0] if hs else None, "height_last": hs[-1] if hs else None,
                       "height_min": min(hs) if hs else None, "height_max": max(hs) if hs else None,
                       "max_height_error": max(errs) if errs else None,
                       "frames_out": len(out), "first_out": out[:5]})
        ok = bool(errs) and max(errs) <= tol + 1e-9 and not out
        if uv_t and uv_tol is not None:
            ue = [r["uv_error"] for r in rows if "uv_error" in r]
            report["max_uv_error"] = max(ue) if ue else None
            ok = ok and bool(ue) and max(ue) <= float(uv_tol)
        report["pass"] = ok
    return frames, rows, report
