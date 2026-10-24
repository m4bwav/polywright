"""pw_scene.py - the Blender half of `pw.py scene` (scene illustrations from a model). Run by pw.py, not by hand:

    blender --background --factory-startup --python-exit-code 3 --python pw_scene.py -- scene <params.json> <result.json>

It renders a scene through a perspective camera preset (pos, target, lens_mm, depth_near_m, depth_far_m) into
passes: clay (Workbench), beauty (Cycles), depth (inverse distance, near white), normal (camera space) and id (a
flat colour per part, the sky transparent), and writes scene.json with the rings and named points projected to
pixels, for gating a painting against the geometry.

It is also a small library for the scripts that build a scene (run them with `pw.py bpy`):

    sys.path.insert(0, "<polywright>/skills/polywright/scripts")
    from pw_scene import sweep, ribbon

`sweep` runs a 2D (sideways offset, height) profile along a polyline: one continuous bank, dyke, kerb or wall
instead of a row of boxes, which shows its joints in perspective. `ribbon` lays a strip along a path at the height
a function gives (a road, a stream's surface). Checked against Blender 5.2.1.
"""
import json
import math
import os
import sys
import time

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))

ID_COLOURS = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 0.5, 0), (0.5, 0, 1),
              (0.5, 0.5, 0.5), (0, 0.5, 0), (0.5, 0, 0), (0, 0, 0.5)]
ID_OTHER = (0.2, 0.2, 0.2)  # objects in no part
SUN = {"azimuth_deg": 200, "elevation_deg": 14, "energy": 4.0, "colour": [1.0, 0.82, 0.6]}
SKY = {"horizon": [1.0, 0.78, 0.55], "zenith": [0.55, 0.68, 0.85], "strength": 0.8}


# ------------------------------------------------------------------------------------------ building helpers

def resample(pts, step=1.0):
    """A 2D polyline as points no more than `step` apart (z 0)."""
    out = [Vector((pts[0][0], pts[0][1], 0.0))]
    for i in range(len(pts) - 1):
        a, b = Vector((pts[i][0], pts[i][1], 0.0)), Vector((pts[i + 1][0], pts[i + 1][1], 0.0))
        n = max(1, int((b - a).length / step))
        for k in range(1, n + 1):
            out.append(a.lerp(b, k / n))
    return out


def _side(path, k):
    a, b = path[max(0, k - 1)], path[min(len(path) - 1, k + 1)]
    t = (b - a).normalized()
    return Vector((-t.y, t.x, 0.0))  # to the left of the direction of travel


def _object(name, bm, material):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    if material is not None:
        ob.data.materials.append(material)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def sweep(name, pts, profile, material=None, step=0.5, smooth=True):
    """A 2D profile [(offset to the left, z), ...] swept along a polyline [(x, y), ...]: one continuous surface."""
    path = resample(pts, step)
    bm = bmesh.new()
    rings = []
    for k, p in enumerate(path):
        s = _side(path, k)
        rings.append([bm.verts.new((p.x + s.x * o, p.y + s.y * o, z)) for o, z in profile])
    for k in range(len(path) - 1):
        for i in range(len(profile) - 1):
            bm.faces.new((rings[k][i], rings[k][i + 1], rings[k + 1][i + 1], rings[k + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _object(name, bm, material)
    for f in ob.data.polygons:
        f.use_smooth = smooth
    return ob


def ribbon(name, pts, half_w, zfun, material=None, step=1.0):
    """A strip `half_w` either side of a polyline, its height zfun(t, point) with t from 0 to 1 along the path."""
    path = resample(pts, step)
    bm = bmesh.new()
    left, right = [], []
    n = len(path)
    for k, p in enumerate(path):
        s = _side(path, k)
        z = zfun(k / max(1, n - 1), p)
        left.append(bm.verts.new((p.x + s.x * half_w, p.y + s.y * half_w, z)))
        right.append(bm.verts.new((p.x - s.x * half_w, p.y - s.y * half_w, z)))
    for k in range(n - 1):
        bm.faces.new((left[k], right[k], right[k + 1], left[k + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _object(name, bm, material)


# ------------------------------------------------------------------------------------------ the scene action

def _emission(name, build):
    m = bpy.data.materials.new(name)
    if not m.node_tree:
        m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    build(nt, em)
    return m


def depth_material(near, far):
    """Inverse distance, near white: (1/z - 1/far) / (1/near - 1/far), so the foreground keeps contrast over a
    range of metres to kilometres. Clamped: anything nearer than `near` is white."""
    def build(nt, em):
        cd = nt.nodes.new("ShaderNodeCameraData")
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "DIVIDE"
        inv.inputs[0].default_value = 1.0
        nt.links.new(cd.outputs["View Z Depth"], inv.inputs[1])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 1.0 / far
        mr.inputs["From Max"].default_value = 1.0 / near
        nt.links.new(inv.outputs["Value"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], em.inputs["Color"])
    return _emission("pass_depth", build)


def normal_material():
    def build(nt, em):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        vt = nt.nodes.new("ShaderNodeVectorTransform")
        vt.vector_type, vt.convert_from, vt.convert_to = "NORMAL", "WORLD", "CAMERA"
        vm = nt.nodes.new("ShaderNodeVectorMath")
        vm.operation = "MULTIPLY_ADD"
        vm.inputs[1].default_value, vm.inputs[2].default_value = (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)
        nt.links.new(geo.outputs["Normal"], vt.inputs["Vector"])
        nt.links.new(vt.outputs["Vector"], vm.inputs[0])
        nt.links.new(vm.outputs["Vector"], em.inputs["Color"])
    return _emission("pass_normal", build)


def make_camera(sc, C, w, h):
    cd = bpy.data.cameras.new("scene_cam")
    cd.lens = float(C.get("lens_mm", 35))
    cd.sensor_fit = "AUTO"
    cd.sensor_width = float(C.get("sensor_mm", 36))
    cd.clip_start = float(C.get("clip_start_m", 0.1))
    cd.clip_end = float(C.get("clip_end_m", 10000))
    cam = bpy.data.objects.new("scene_cam", cd)
    sc.collection.objects.link(cam)
    pos, tgt = Vector(C["pos"]), Vector(C["target"])
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    return cam


def make_light(sc, sun, world):
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    sd = bpy.data.lights.new("scene_sun", "SUN")
    sd.energy = float(sun["energy"])
    sd.color = sun["colour"]
    sd.angle = math.radians(3)
    ob = bpy.data.objects.new("scene_sun", sd)
    sc.collection.objects.link(ob)
    az, el = math.radians(sun["azimuth_deg"]), math.radians(sun["elevation_deg"])
    towards = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    ob.rotation_euler = towards.to_track_quat("Z", "Y").to_euler()
    wo = bpy.data.worlds.new("scene_sky")
    if not wo.node_tree:
        wo.use_nodes = True
    nt = wo.node_tree
    bg = nt.nodes.get("Background")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*world["horizon"], 1)
    ramp.color_ramp.elements[1].position = 0.35
    ramp.color_ramp.elements[1].color = (*world["zenith"], 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = float(world.get("strength", 0.8))
    wo.color = (0.86, 0.87, 0.88)  # Workbench (clay) draws the world's viewport colour, not its nodes
    sc.world = wo


def measured_depth(sc, cam, w, h, cols=48, rows=27):
    """Nearest and farthest visible surface along the view axis, from a grid of rays through the frame."""
    dg = bpy.context.evaluated_depsgraph_get()
    m = cam.matrix_world
    o = m.translation.copy()
    right, up, fwd = m.col[0].xyz.normalized(), m.col[1].xyz.normalized(), -m.col[2].xyz.normalized()
    k = cam.data.lens / cam.data.sensor_width * max(w, h)
    zs = []
    for j in range(rows):
        for i in range(cols):
            x, y = ((i + 0.5) / cols - 0.5) * w / k, (0.5 - (j + 0.5) / rows) * h / k
            d = (fwd + right * x + up * y).normalized()
            start = o
            for _ in range(4):  # step through objects hidden from the render
                hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, start, d)
                if not hit:
                    break
                if not ob.hide_render:
                    zs.append((loc - o).dot(fwd))
                    break
                start = loc + d * 1e-3
    return (min(zs), max(zs)) if zs else None


def project(sc, cam, p):
    from bpy_extras.object_utils import world_to_camera_view
    v = world_to_camera_view(sc, cam, Vector(p))
    w, h = sc.render.resolution_x, sc.render.resolution_y
    return [round(v.x * w, 2), round((1 - v.y) * h, 2), round(v.z, 3)]


def srgb(c):
    return round(255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055))


def act_scene(p):
    """Render a scene illustration's passes through one perspective camera preset and write scene.json.

    Parts come from the scene property "scene_parts" (name -> object-name prefix or list of prefixes); rings
    (wheels, millstones, clock faces) from "rings" ({name: {centre, radius, axis, faces, arms, hub_r}}); named
    points or paths from "scene_points" ({name: [x, y, z] or [[x, y, z], ...]})."""
    f = p["file"]
    if f.lower().endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=f)
    else:
        sys.path.insert(0, HERE)
        import pw_bpy
        pw_bpy.reset()
        pw_bpy.load(f)
    sc = bpy.context.scene
    C = p["camera"]
    w, h = p["size"]
    out = p["out"]
    os.makedirs(out, exist_ok=True)
    parts = json.loads(sc.get("scene_parts", "{}"))
    colours = {name: ID_COLOURS[i % len(ID_COLOURS)] for i, name in enumerate(parts)}

    def part_of(ob):
        for name, prefix in parts.items():
            if any(ob.name.startswith(q) for q in (prefix if isinstance(prefix, list) else [prefix])):
                return name
        return None
    for ob in sc.objects:
        if any(ob.name.startswith(q) for q in p.get("hide", [])):
            ob.hide_render = True
            ob.hide_viewport = True
        part = part_of(ob)
        ob.color = (*(colours[part] if part else ID_OTHER), 1.0)
    cam = make_camera(sc, C, w, h)
    sun = p.get("sun") or SUN
    if not p.get("keep_lights"):
        make_light(sc, sun, {**SKY, **(p.get("world") or {})})
    near, far = C.get("depth_near_m"), C.get("depth_far_m")
    source = "camera preset"
    if near is None or far is None:
        got = measured_depth(sc, cam, w, h)
        lo, hi = got if got else (1.0, 100.0)
        source = "measured: nearest and farthest surface over a 48x27 ray grid" if got else "no surface hit: 1 to 100 m"
        near = near if near is not None else max(0.05, 0.9 * lo)
        far = far if far is not None else 1.05 * hi
    vl = sc.view_layers[0]

    def view(transform="Standard"):
        vs = sc.view_settings
        vs.view_transform, vs.look, vs.exposure, vs.gamma = transform, "None", 0.0, 1.0

    def workbench(color_type, light):
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light, sh.color_type = light, color_type
        sh.single_color = (0.75, 0.75, 0.75)
        sh.show_object_outline = sh.show_cavity = sh.show_specular_highlight = False
        sh.show_shadows = light != "FLAT"
        sc.display.render_aa = "OFF" if light == "FLAT" else "8"

    def cycles(samples, denoise):
        sc.render.engine = "CYCLES"
        sc.cycles.device = "GPU" if p.get("gpu") else "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = denoise

    written = {}

    def render(name):
        vl.material_override = None
        view()
        transparent = name in ("depth", "normal", "id")
        if name == "clay":
            workbench("SINGLE", "STUDIO")
        elif name == "beauty":
            cycles(int(p.get("samples", 48)), True)
        elif name == "depth":
            cycles(4, False)
            vl.material_override = depth_material(near, far)
        elif name == "normal":
            cycles(4, False)
            vl.material_override = normal_material()
        elif name == "id":
            workbench("OBJECT", "FLAT")
        else:
            raise ValueError("unknown pass %s (clay, beauty, depth, normal, id)" % name)
        path = os.path.join(out, name + ".png")
        sc.render.film_transparent = transparent
        sc.render.filepath = path
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
        sc.render.image_settings.color_depth = "8"
        bpy.ops.render.render(write_still=True)
        if not os.path.isfile(path):
            raise RuntimeError("render wrote nothing: %s" % path)
        written[name] = path

    for name in p.get("passes", ["clay", "beauty", "depth", "normal", "id"]):
        render(name)

    campos = cam.matrix_world.translation
    rings = {}
    for name, r in json.loads(sc.get("rings", "{}")).items():
        ax = "XYZ".index(r["axis"])
        u, v = [i for i in range(3) if i != ax]
        face = sorted(r.get("faces", [r["centre"][ax]]), key=lambda z: abs(z - campos[ax]))[0]

        def circle(radius):
            pts = []
            for j in range(72):
                q = list(r["centre"])
                q[ax] = face
                q[u] += radius * math.cos(2 * math.pi * j / 72)
                q[v] += radius * math.sin(2 * math.pi * j / 72)
                pts.append(project(sc, cam, q)[:2])
            return pts
        c = list(r["centre"])
        c[ax] = face
        rings[name] = {"rim_px": circle(r["radius"]), "centre_px": project(sc, cam, c)[:2], "arms": r.get("arms", 0),
                       "angles": 72, "axis": r["axis"], "radius_m": r["radius"]}
        if r.get("hub_r"):
            rings[name]["hub_px"] = circle(r["hub_r"])

    def placed(q):
        x, y, z = project(sc, cam, q)
        return {"px": [x, y], "depth_m": z, "in_frame": z > 0 and 0 <= x <= w and 0 <= y <= h}
    points = {}
    for name, q in json.loads(sc.get("scene_points", "{}")).items():
        points[name] = [placed(e) for e in q] if q and isinstance(q[0], (list, tuple)) else placed(q)
    meta = {"size": [w, h], "camera_name": p.get("camera_name"), "camera": C,
            "f_px": round(cam.data.lens / cam.data.sensor_width * max(w, h), 3),
            "sun": None if p.get("keep_lights") else sun,
            "depth_range_m": [round(near, 3), round(far, 3)], "depth_range_from": source,
            "depth_encoding": "inverse distance mapped from 1/far (black) to 1/near (white), clamped",
            "id_colours": {k: [round(c, 3) for c in v] for k, v in colours.items()},
            "id_colours_srgb": {k: [srgb(c) for c in v] for k, v in colours.items()},
            "id_other_srgb": [srgb(c) for c in ID_OTHER], "id_sky": "transparent (alpha 0)",
            "rings": rings, "points": points}
    with open(os.path.join(out, "scene.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    return {"out": out, "passes": written, "size": [w, h], "depth_range_m": meta["depth_range_m"],
            "depth_range_from": source, "parts": list(parts), "rings": list(rings), "points": list(points)}


ACTIONS = {"scene": act_scene}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    action, params_path, result_path = argv[:3]
    params = json.load(open(params_path, encoding="utf-8"))
    t0 = time.time()
    try:
        res = ACTIONS[action](params)
        res["ok"] = True
    except Exception as e:  # report, never hang: pw.py reads the result file
        import traceback
        res = {"ok": False, "error": "%s: %s" % (type(e).__name__, e), "trace": traceback.format_exc()[-1500:]}
    res["action"] = action
    res["blender"] = bpy.app.version_string
    res["seconds"] = round(time.time() - t0, 2)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
