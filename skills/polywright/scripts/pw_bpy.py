"""pw_bpy.py - the Blender side of polywright. Run by pw.py, not by hand:

    blender --background --factory-startup --python-exit-code 3 --python pw_bpy.py -- <action> <params.json> <result.json>

or with any Python that can `import bpy` (the bpy module from PyPI):

    python pw_bpy.py -- <action> <params.json> <result.json>

Actions: inspect, render, match, convert, printable, union, crowd. Each reads its parameters from params.json and writes one
JSON object to result.json. Units: Blender scene units are treated as metres, except in `printable` and
`union`, which work in millimetres because their output is for a slicer.
Checked against Blender 5.2.1 LTS (2026-10-11).
"""
import json
import math
import os
import sys
import time

import bpy
import bmesh
from mathutils import Vector, Matrix

try:
    import numpy as np
except ImportError:  # Blender always ships numpy; the bpy wheel depends on it
    np = None

IMPORTERS = {
    ".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p),
    ".gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p),
    ".obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
    ".stl": lambda p: bpy.ops.wm.stl_import(filepath=p),
    ".ply": lambda p: bpy.ops.wm.ply_import(filepath=p),
    ".fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p),
    ".usd": lambda p: bpy.ops.wm.usd_import(filepath=p),
    ".usda": lambda p: bpy.ops.wm.usd_import(filepath=p),
    ".usdc": lambda p: bpy.ops.wm.usd_import(filepath=p),
    ".usdz": lambda p: bpy.ops.wm.usd_import(filepath=p),
    ".abc": lambda p: bpy.ops.wm.alembic_import(filepath=p),
}


def log(msg):
    print("[pw] " + str(msg), flush=True)


# ---------------------------------------------------------------- scene helpers

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path):
    """Import or open a file. Returns the mesh objects now in the scene."""
    ext = os.path.splitext(path)[1].lower()
    if not os.path.isfile(path):
        raise ValueError("file not found: %s" % path)
    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=path)
    elif ext in IMPORTERS:
        reset()
        IMPORTERS[ext](path)
    else:
        raise ValueError("Blender cannot import %s here (3MF: convert with trimesh or a slicer first)" % ext)
    return mesh_objects()


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def world_coords(obj, me):
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    m = np.array(obj.matrix_world, dtype=np.float64)
    return co @ m[:3, :3].T + m[:3, 3]


def bounds(objs):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        if len(me.vertices):
            w = world_coords(o, me)
            lo = [min(lo[i], float(w[:, i].min())) for i in range(3)]
            hi = [max(hi[i], float(w[:, i].max())) for i in range(3)]
        oe.to_mesh_clear()
    if lo[0] == math.inf:
        return [0, 0, 0], [0, 0, 0]
    return lo, hi


def islands(nverts, edge_verts):
    """Connected components over vertices; returns a label per vertex. Union-find, path halving."""
    parent = list(range(nverts))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in edge_verts:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return [find(i) for i in range(nverts)]


def mesh_stats(obj, me, deep=True):
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    st = {"name": obj.name, "tris": tris, "verts": len(me.vertices), "faces": len(me.polygons),
          "materials": [m.name for m in me.materials if m],
          "uv_layers": [u.name for u in me.uv_layers],
          "color_attributes": [a.name for a in getattr(me, "color_attributes", [])],
          "modifiers": [m.type for m in obj.modifiers],
          "scale": [round(s, 4) for s in obj.scale],
          "shape_keys": len(me.shape_keys.key_blocks) if me.shape_keys else 0}
    if not deep or not len(me.edges):
        return st
    # Topology on welded positions: glTF and STL split vertices per face, which would make every closed
    # mesh look open. Positions are snapped to 1e-6 of the object's size, the way a slicer sees them.
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    span = float(np.ptp(co, axis=0).max()) if len(co) else 1.0
    _, weld = np.unique(np.round(co / max(span * 1e-6, 1e-12)).astype(np.int64), axis=0, return_inverse=True)
    weld = weld.reshape(-1)
    tv = np.empty(tris * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", tv)
    t = weld[tv.reshape(-1, 3)]
    t = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])]
    e = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    _, counts = np.unique(e, axis=0, return_counts=True)
    st["boundary_edges"] = int((counts == 1).sum())
    st["non_manifold_edges"] = int((counts > 2).sum())
    if weld.max(initial=-1) + 1 <= 2_000_000 and len(e):
        labels = islands(int(weld.max()) + 1, np.unique(e, axis=0).tolist())
        used = np.unique(t)
        st["parts"] = len({labels[i] for i in used.tolist()})
    if st["boundary_edges"] == 0 and st["non_manifold_edges"] == 0 and len(t):
        w = world_coords(obj, me)
        tri = w[tv.reshape(-1, 3)]
        vol = float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)
        st["volume"] = vol
        st["inside_out"] = vol < 0
    return st


def select_only(objs, active=None):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or (objs[0] if objs else None)


def flatten_hierarchy():
    """Clear parents keeping world transforms (glTF and FBX often put the axis fix on a parent empty),
    switch to Euler rotation, apply transforms, delete non-mesh objects."""
    meshes = mesh_objects()
    for o in meshes:
        o.rotation_mode = "XYZ"
    select_only(meshes)
    if meshes:
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    return mesh_objects()


def join_all(name="joined"):
    meshes = mesh_objects()
    if not meshes:
        raise ValueError("no mesh objects")
    select_only(meshes, meshes[0])
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj


def apply_modifier(obj, mod):
    select_only([obj], obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def transform_mesh(obj, scale=1.0, offset=(0, 0, 0)):
    obj.data.transform(Matrix.Translation(Vector(offset)) @ Matrix.Scale(scale, 4))
    obj.data.update()


def keep_largest_part(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    labels = islands(len(bm.verts), [(e.verts[0].index, e.verts[1].index) for e in bm.edges])
    sizes = {}
    for lab in labels:
        sizes[lab] = sizes.get(lab, 0) + 1
    if len(sizes) > 1:
        keep = max(sizes, key=sizes.get)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if labels[v.index] != keep], context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    return len(sizes)


def cleanup(obj, merge=0.0):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    if merge > 0:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bad = [e for e in bm.edges if not e.is_manifold]
    if bad:
        bmesh.ops.holes_fill(bm, edges=bad, sides=64)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def decimate_to(obj, max_tris):
    obj.data.calc_loop_triangles()
    tris = len(obj.data.loop_triangles)
    if max_tris and tris > max_tris:
        m = obj.modifiers.new("pw_decimate", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = max(0.001, max_tris / float(tris))
        m.use_collapse_triangulate = True
        apply_modifier(obj, m)
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


# ---------------------------------------------------------------- actions

def act_inspect(p):
    t0 = time.time()
    objs = load(p["file"])
    deep = p.get("deep", True)
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        rows.append(mesh_stats(o, me, deep))
        oe.to_mesh_clear()
    lo, hi = bounds(objs)
    dims = [hi[i] - lo[i] for i in range(3)]
    images = []
    for img in bpy.data.images:
        if img.type == "IMAGE":
            images.append({"name": img.name, "size": list(img.size), "colorspace": img.colorspace_settings.name})
    rows.sort(key=lambda r: -r["tris"])
    tot = lambda k: sum(r.get(k, 0) for r in rows)
    res = {
        "file": p["file"], "objects": len(rows), "tris": tot("tris"), "verts": tot("verts"),
        "bbox_min": [round(v, 5) for v in lo], "bbox_max": [round(v, 5) for v in hi],
        "dims": [round(v, 5) for v in dims],
        "units_note": "Blender units; metres unless the source used other units (an STL in mm reads as 1000x too big)",
        "materials": sorted({m for r in rows for m in r["materials"]}),
        "images": images, "max_image_px": max([max(i["size"]) for i in images] or [0]),
        "uv_missing": [r["name"] for r in rows if not r["uv_layers"]][:20],
        "armatures": len([o for o in bpy.data.objects if o.type == "ARMATURE"]),
        "actions": len(bpy.data.actions),
        "cameras": len([o for o in bpy.data.objects if o.type == "CAMERA"]),
        "lights": len([o for o in bpy.data.objects if o.type == "LIGHT"]),
        "unapplied_scale": [r["name"] for r in rows if any(abs(s - 1) > 1e-4 for s in r["scale"])][:20],
        "seconds": round(time.time() - t0, 2),
    }
    if deep:
        res.update({"boundary_edges": tot("boundary_edges"), "non_manifold_edges": tot("non_manifold_edges"),
                    "parts": tot("parts"),
                    "watertight": all(r.get("boundary_edges", 1) == 0 and r.get("non_manifold_edges", 1) == 0 for r in rows) and bool(rows)})
        if res["watertight"]:
            res["volume"] = round(sum(r.get("volume", 0) for r in rows), 6)
            res["inside_out"] = [r["name"] for r in rows if r.get("inside_out")]
    res["object_rows"] = rows[: p.get("max_rows", 25)]
    return res


VIEW_DIRS = {
    "front": (0, -1, 0), "back": (0, 1, 0), "right": (1, 0, 0), "left": (-1, 0, 0),
    "top": (0, 0, 1), "bottom": (0, 0, -1), "iso": (-1, -1, 0.8), "iso_back": (1, 1, 0.8),
}


def setup_render(p):
    sc = bpy.context.scene
    engines = [e.identifier for e in sc.render.bl_rna.properties["engine"].enum_items]
    want = {"workbench": "BLENDER_WORKBENCH", "eevee": "BLENDER_EEVEE", "cycles": "CYCLES"}[p.get("engine", "workbench")]
    if want not in engines:
        want = next((e for e in engines if e.startswith(want)), "BLENDER_WORKBENCH")
    sc.render.engine = want
    size = int(p.get("size", 640))
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("pw_world")
    sc.world.color = (0.82, 0.83, 0.85)
    if want == "BLENDER_WORKBENCH":
        sh = sc.display.shading
        sh.light = "STUDIO"
        sh.color_type = {"clay": "SINGLE", "material": "MATERIAL", "texture": "TEXTURE"}[p.get("color", "clay")]
        sh.single_color = (0.72, 0.70, 0.66)
        sh.show_cavity = True
        sh.cavity_type = "BOTH"
        sh.show_object_outline = True
        sh.show_specular_highlight = True
        sh.show_shadows = True  # without cast shadows, flat roofs vanish into flat ground in a top view
        sh.shadow_intensity = 0.45
        sc.display.light_direction = (0.45, -0.35, 0.82)
        sc.display.shadow_shift = 0.1
    elif want == "CYCLES":
        sc.cycles.samples = int(p.get("samples", 32))
    if want != "BLENDER_WORKBENCH" and not any(o.type == "LIGHT" for o in sc.objects):
        sun = bpy.data.objects.new("pw_sun", bpy.data.lights.new("pw_sun", "SUN"))
        sun.data.energy = 3.0
        sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
        sc.collection.objects.link(sun)
        sc.world.use_nodes = True
        bg = sc.world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[1].default_value = 0.6
    return size


def scale_cavity(radius):
    """Workbench's world-space cavity distance is in scene units: scale it to the model, or a model in
    millimetres (hundreds of units) gets no ambient occlusion and flat roofs vanish into flat ground."""
    sc = bpy.context.scene
    if sc.render.engine == "BLENDER_WORKBENCH":
        sc.display.matcap_ssao_distance = radius * 0.04
        sc.display.matcap_ssao_attenuation = 1.0
        sh = sc.display.shading
        sh.cavity_ridge_factor = sh.cavity_valley_factor = 1.25
        sh.curvature_ridge_factor = sh.curvature_valley_factor = 1.25


def act_render(p):
    objs = load(p["file"])
    if not objs:
        raise ValueError("no mesh objects to render")
    out = p["out"]
    os.makedirs(out, exist_ok=True)
    size = setup_render(p)
    lo, hi = bounds(objs)
    c = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
    ext = Vector([hi[i] - lo[i] for i in range(3)])
    radius = max(ext.length / 2, 1e-6)
    scale_cavity(radius)
    corners = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new("pw_cam")
    cam = bpy.data.objects.new("pw_cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    shots = []
    for view in p.get("views", ["front", "right", "back", "left", "top", "iso"]):
        if view not in VIEW_DIRS:
            raise ValueError("unknown view %s (known: %s)" % (view, ", ".join(VIEW_DIRS)))
        d = Vector(VIEW_DIRS[view]).normalized()
        rot = (-d).to_track_quat("-Z", "Y")
        cam.rotation_euler = rot.to_euler()
        ortho = view not in ("iso", "iso_back") or p.get("ortho_iso", False)
        if ortho:
            cam_data.type = "ORTHO"
            m = rot.to_matrix()
            right, up = m.col[0], m.col[1]
            w = max(abs((q - c).dot(right)) for q in corners) * 2
            h = max(abs((q - c).dot(up)) for q in corners) * 2
            cam_data.ortho_scale = max(w, h, 1e-6) * 1.08
            cam.location = c + d * (radius * 4 + 1)
            cam_data.clip_end = radius * 10 + 10
        else:
            cam_data.type = "PERSP"
            cam_data.lens = 50
            fov = 2 * math.atan(36 / 2 / 50)
            cam.location = c + d * (radius / math.sin(fov / 2) * 1.05)
            cam_data.clip_end = radius * 20 + 10
        cam_data.clip_start = max(radius / 1000, 1e-4)
        path = os.path.join(out, "view_%s.png" % view)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        shot = {"view": view, "path": path, "projection": "ortho" if ortho else "perspective"}
        if ortho:
            shot["metres_per_px"] = round(cam_data.ortho_scale / size, 6)
        shots.append(shot)
    res = {"shots": shots, "dims": [round(v, 5) for v in ext], "engine": sc.render.engine}
    if p.get("sheet", True) and len(shots) > 1 and np is not None:
        res["sheet"] = stitch([s["path"] for s in shots], os.path.join(out, "sheet.png"), min(int(p.get("cols", 3)), len(shots)))
    return res


def act_match(p):
    """Render a model from the camera of an existing picture, RGBA, so it can be pasted into it.

    The picture's camera is unknown, so fix the lens and the horizon row, then pose the model in camera space:
    the local anchor point (a hand's grip) lands on anchor_px at the guessed depth, and the local aim point (a
    tip) lands exactly on aim_px. The model's forward axis is +X and up is +Z; up stays as near world up as the
    aim allows, then roll turns it about the forward axis."""
    objs = load(p["file"])
    if not objs:
        raise ValueError("no mesh objects to render")
    sc = bpy.context.scene
    W, H = (int(v) for v in p["size"])
    lens = float(p.get("lens", 35.0))
    f_px = W * lens / 36.0
    horizon = p.get("horizon")
    pitch = math.atan(((horizon if horizon is not None else H / 2) - H / 2) / f_px)
    cam_data = bpy.data.cameras.new("pw_match")
    cam_data.lens, cam_data.sensor_width, cam_data.sensor_fit = lens, 36.0, "HORIZONTAL"
    cam_data.clip_start = 0.01
    cam = bpy.data.objects.new("pw_match", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.rotation_euler = (math.pi / 2 + pitch, 0, 0)
    bpy.context.view_layer.update()
    R = cam.matrix_world.to_3x3()

    def ray(px, py):
        return (R @ Vector(((px - W / 2) / f_px, -(py - H / 2) / f_px, -1.0))).normalized()

    def project(q):
        d = R.transposed() @ (q - cam.location)
        return [round(W / 2 + f_px * d.x / -d.z, 1), round(H / 2 - f_px * d.y / -d.z, 1)]

    anchor_l, aim_l = Vector(p["anchor_local"]), Vector(p["aim_local"])
    off = aim_l - anchor_l
    if off.x <= 0:
        raise ValueError("aim_local must lie ahead of anchor_local along +X (the model's forward axis)")
    G = ray(*p["anchor_px"]) * float(p.get("depth", 3.0))
    rt = ray(*p["aim_px"])
    up_w = Vector((0, 0, 1))
    roll = math.radians(float(p.get("roll", 0.0)))

    def frame(u):
        v = (up_w - up_w.dot(u) * u)
        if v.length < 1e-6:
            raise ValueError("the aim points straight up or down; give a different aim_px or depth")
        v = Matrix.Rotation(roll, 3, u) @ v.normalized()
        return v, u.cross(v)

    u = (rt * (G.length + off.length) - G).normalized()
    for _ in range(60):  # fixed point: the axis direction that puts the (off-axis) aim point on its ray
        v, w = frame(u)
        lateral = v * off.z + w * off.y
        b = rt.dot(lateral + G)
        disc = b * b - ((lateral + G).length_squared - off.x ** 2)
        if disc < 0:
            raise ValueError("no pose reaches aim_px from anchor_px at this depth; try a larger depth")
        u = (rt * (b + math.sqrt(disc)) - lateral - G).normalized()
    v, w = frame(u)
    M = Matrix.Translation(G) @ Matrix((u, w, v)).transposed().to_4x4() @ Matrix.Translation(-anchor_l)
    root = bpy.data.objects.new("pw_match_root", None)
    sc.collection.objects.link(root)
    for o in sc.objects:
        if o.parent is None and o not in (cam, root) and o.type != "LIGHT":
            o.parent = root
    root.matrix_world = M
    bpy.context.view_layer.update()

    if not p.get("keep_lights") or not any(o.type == "LIGHT" for o in sc.objects):
        for o in [o for o in sc.objects if o.type == "LIGHT"]:
            bpy.data.objects.remove(o)
        sun = bpy.data.objects.new("pw_key", bpy.data.lights.new("pw_key", "SUN"))
        sun.data.energy = float(p.get("sun_energy", 3.0))
        sun.data.angle = math.radians(12)
        sd = Vector(p.get("sun_dir", (-0.8, 0.6, 0.25))).normalized()  # direction TO the light, world axes
        sun.rotation_euler = (-sd).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(sun)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("pw_world")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*p.get("world_rgb", (0.32, 0.30, 0.27)), 1)
        bg.inputs[1].default_value = float(p.get("world_strength", 0.6))
    engines = [e.identifier for e in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "CYCLES" if p.get("engine", "cycles") == "cycles" else next(e for e in engines if e.startswith("BLENDER_EEVEE"))
    if sc.render.engine == "CYCLES":
        sc.cycles.device = "GPU" if p.get("gpu") else "CPU"  # CPU by default: the GPU is often busy (training, video)
        sc.cycles.samples = int(p.get("samples", 128))
        sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.render.filepath = os.path.abspath(p["out"])  # relative render paths do not land in the working folder
    bpy.ops.render.render(write_still=True)
    aim_w = M @ aim_l
    return {"out": sc.render.filepath, "aim_lands": project(aim_w), "aim_px": list(p["aim_px"]),
            "anchor_lands": project(M @ anchor_l), "aim_depth_m": round((aim_w - cam.location).length, 3),
            "forward_pitch_deg": round(math.degrees(math.asin(max(-1, min(1, u.z)))), 2),
            "forward_yaw_deg": round(math.degrees(math.atan2(u.x, u.y)), 2), "f_px": round(f_px, 1)}


def stitch(paths, out, cols):
    imgs = [bpy.data.images.load(pth) for pth in paths]
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    sheet = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for i, img in enumerate(imgs):
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)
        r, cidx = divmod(i, cols)
        y0 = (rows - 1 - r) * h  # Blender pixel rows run bottom-up
        sheet[y0:y0 + h, cidx * w:(cidx + 1) * w] = px
    im = bpy.data.images.new("pw_sheet", cols * w, rows * h, alpha=True)
    im.pixels.foreach_set(sheet.ravel())
    im.filepath_raw = out
    im.file_format = "PNG"
    im.save()
    return {"path": out, "layout": "%d columns, row-major in the order of shots" % cols}


EXPORT_NOTES = {}


def export(path, p):
    ext = os.path.splitext(path)[1].lower()
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    if ext in (".glb", ".gltf"):
        kw = dict(filepath=path, export_format="GLB" if ext == ".glb" else "GLTF_SEPARATE", export_apply=True)
        if p.get("draco"):
            kw["export_draco_mesh_compression_enable"] = True
        bpy.ops.export_scene.gltf(**kw)
    elif ext == ".obj":
        bpy.ops.wm.obj_export(filepath=path, apply_modifiers=True, export_materials=True, global_scale=p.get("export_scale", 1.0))
    elif ext == ".stl":
        bpy.ops.wm.stl_export(filepath=path, apply_modifiers=True, ascii_format=False, global_scale=p.get("export_scale", 1.0))
    elif ext == ".ply":
        bpy.ops.wm.ply_export(filepath=path, apply_modifiers=True, global_scale=p.get("export_scale", 1.0))
    elif ext == ".fbx":
        bpy.ops.export_scene.fbx(filepath=path, use_mesh_modifiers=True, apply_scale_options="FBX_SCALE_UNITS",
                                 axis_forward="-Z", axis_up="Y", bake_space_transform=bool(p.get("fbx_bake_axes", False)),
                                 path_mode="COPY", embed_textures=True)
    elif ext in (".usd", ".usda", ".usdc", ".usdz"):
        bpy.ops.wm.usd_export(filepath=path)
    elif ext == ".abc":
        bpy.ops.wm.alembic_export(filepath=path)
    elif ext == ".blend":
        bpy.ops.wm.save_as_mainfile(filepath=path)
    else:
        raise ValueError("cannot export %s" % ext)
    return {"path": path, "bytes": os.path.getsize(path) if os.path.isfile(path) else None}


def act_convert(p):
    objs = load(p["file"])
    notes = []
    if p.get("apply") or p.get("join") or p.get("uv") or p.get("size_m") or p.get("ground") or p.get("center") or p.get("max_tris") or p.get("ratio"):
        objs = flatten_hierarchy()
        notes.append("hierarchy flattened, transforms applied, non-mesh objects removed")
    if p.get("join") and len(objs) > 1:
        objs = [join_all(p.get("name") or "joined")]
    scale = float(p.get("scale", 1.0))
    if p.get("size_m"):
        lo, hi = bounds(objs)
        longest = max(hi[i] - lo[i] for i in range(3))
        scale *= float(p["size_m"]) / longest if longest else 1.0
    if scale != 1.0:
        for o in objs:
            transform_mesh(o, scale)
        notes.append("scaled by %.6g" % scale)
    if p.get("ground") or p.get("center"):
        lo, hi = bounds(objs)
        off = [-(lo[0] + hi[0]) / 2 if p.get("center") else 0, -(lo[1] + hi[1]) / 2 if p.get("center") else 0, -lo[2] if p.get("ground") else 0]
        for o in objs:
            transform_mesh(o, 1.0, off)
    if p.get("ratio") or p.get("max_tris"):
        for o in objs:
            o.data.calc_loop_triangles()
        total = sum(len(o.data.loop_triangles) for o in objs)
        for o in objs:
            o.data.calc_loop_triangles()
            n = len(o.data.loop_triangles)
            target = int(n * float(p["ratio"])) if p.get("ratio") else int(n * min(1.0, float(p["max_tris"]) / max(total, 1)))
            decimate_to(o, max(target, 4))
    if p.get("uv"):
        for o in objs:
            select_only([o], o)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
            bpy.ops.object.mode_set(mode="OBJECT")
        notes.append("Smart UV Project on %d object(s)" % len(objs))
    lo, hi = bounds(objs)
    tris = 0
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    res = export(p["out"], p)
    res.update({"tris": tris, "dims": [round(hi[i] - lo[i], 6) for i in range(3)], "notes": notes})
    return res


def act_printable(p):
    """Any mesh to one watertight solid sized in millimetres with a flat base."""
    load(p["file"])
    drop = [d.lower() for d in p.get("drop", []) if d]
    for o in list(mesh_objects()):
        hay = (o.name + " " + " ".join(m.name for m in o.data.materials if m)).lower()
        if any(d in hay for d in drop):
            bpy.data.objects.remove(o, do_unlink=True)
    flatten_hierarchy()
    obj = join_all(p.get("name") or "printable")
    lo, hi = bounds([obj])
    dims = [hi[i] - lo[i] for i in range(3)]
    if p.get("up") == "y":  # a Y-up source that came in unrotated (STL or OBJ from a Y-up tool)
        obj.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
        lo, hi = bounds([obj])
        dims = [hi[i] - lo[i] for i in range(3)]
    size = float(p.get("size_mm", 100))
    key = {"longest": max(dims), "height": dims[2], "width": dims[0], "depth": dims[1]}[p.get("size_axis", "longest")]
    s = size / key if key else 1.0
    transform_mesh(obj, s, (0, 0, 0))
    lo, hi = bounds([obj])
    transform_mesh(obj, 1.0, (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
    steps = ["scaled x%.4g to %.1f mm (%s)" % (s, size, p.get("size_axis", "longest"))]
    obj.data.calc_loop_triangles()
    if len(obj.data.loop_triangles) > int(p.get("pre_tris", 450000)):
        decimate_to(obj, int(p.get("pre_tris", 450000)))
        steps.append("pre-decimated to %d tris" % len(obj.data.loop_triangles))
    st = mesh_stats(obj, obj.data)
    open_mesh = st.get("boundary_edges", 0) > 0 or st.get("non_manifold_edges", 0) > 0
    if open_mesh and p.get("wall_mm", 1.0) > 0:
        m = obj.modifiers.new("pw_solidify", "SOLIDIFY")
        m.thickness = float(p.get("wall_mm", 1.0))
        m.offset = -1.0
        m.use_even_offset = False  # even offset makes spikes at sharp corners (Blender issue 110057)
        m.thickness_clamp = 1.0
        apply_modifier(obj, m)
        steps.append("open surface: solidified %.2f mm inward" % m.thickness)
    voxel = float(p.get("voxel_mm") or max(size / 500.0, 0.05))
    if p.get("remesh", True):
        m = obj.modifiers.new("pw_remesh", "REMESH")
        m.mode = "VOXEL"
        m.voxel_size = voxel
        m.adaptivity = 0.0
        apply_modifier(obj, m)
        steps.append("voxel remesh %.3f mm" % voxel)
    parts = keep_largest_part(obj)
    if parts > 1:
        steps.append("kept the largest of %d parts" % parts)
    lo, hi = bounds([obj])  # solidify can push an open surface below z=0: sit it on the ground again first
    transform_mesh(obj, 1.0, (0, 0, -lo[2]))
    cut = float(p.get("base_cut_mm", 0.6))
    if cut > 0:
        for v in obj.data.vertices:
            if v.co.z < cut:
                v.co.z = cut
        transform_mesh(obj, 1.0, (0, 0, -cut))
        steps.append("flat base: clamped below %.2f mm" % cut)
    tris = decimate_to(obj, int(p.get("max_tris", 400000)))
    cleanup(obj, merge=voxel * 0.01)
    if p.get("planar", True):
        # A voxel remesh tiles flat faces as finely as curves. Try merging coplanar faces on a copy decimated to
        # planar_tris first (dissolve is slow on hundreds of thousands of faces), and keep it only when it stays
        # watertight and the dissolve itself at least halves the faces; organic shapes keep their full-detail mesh.
        keep = obj.data.copy()
        before = len(obj.data.polygons)
        decimate_to(obj, int(p.get("planar_tris", 100000)))
        mid = len(obj.data.polygons)
        m = obj.modifiers.new("pw_planar", "DECIMATE")
        m.decimate_type = "DISSOLVE"
        m.angle_limit = math.radians(float(p.get("planar_deg", 0.5)))
        apply_modifier(obj, m)
        m = obj.modifiers.new("pw_tri", "TRIANGULATE")
        apply_modifier(obj, m)
        cleanup(obj)
        st = mesh_stats(obj, obj.data)
        after = len(obj.data.polygons)
        if st.get("boundary_edges") or st.get("non_manifold_edges") or after > mid / 2:
            obj.data = keep
            steps.append("planar dissolve not kept (%s)" % ("it broke the solid" if st.get("boundary_edges") or st.get("non_manifold_edges") else "little flat area"))
        else:
            steps.append("planar dissolve %.1f deg: %d -> %d faces" % (float(p.get("planar_deg", 0.5)), before, after))
    st = mesh_stats(obj, obj.data)
    lo, hi = bounds([obj])
    out = export(p["out"], p)
    if p.get("blend"):
        bpy.ops.wm.save_as_mainfile(filepath=p["blend"])
    return {"out": out, "steps": steps, "tris": st["tris"], "dims_mm": [round(hi[i] - lo[i], 3) for i in range(3)],
            "boundary_edges": st.get("boundary_edges"), "non_manifold_edges": st.get("non_manifold_edges"),
            "parts": st.get("parts"), "volume_cm3": round(st.get("volume", 0) / 1000.0, 3),
            "watertight": st.get("boundary_edges") == 0 and st.get("non_manifold_edges") == 0}


def act_union(p):
    """Union closed parts (terrain block plus building prisms, a body plus a base) into one solid."""
    load(p["file"])
    flatten_hierarchy()
    objs = mesh_objects()
    if len(objs) == 1:  # an STL arrives as one object holding every shell: split it
        select_only(objs, objs[0])
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
        objs = mesh_objects()
    if p.get("scale"):
        for o in objs:
            transform_mesh(o, float(p["scale"]))
    objs.sort(key=lambda o: -len(o.data.vertices))
    open_parts = [o.name for o in objs if (lambda st: st.get("boundary_edges", 0) or st.get("non_manifold_edges", 0))(mesh_stats(o, o.data))]
    want_lo, want_hi = bounds(objs)
    base = objs[0]
    rest = objs[1:]
    solver = None
    if rest:
        keep = bpy.data.meshes.new_from_object(base)  # to retry with EXACT if MANIFOLD drops operands
        col = bpy.data.collections.new("pw_operands")
        bpy.context.scene.collection.children.link(col)
        for o in rest:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
        m = base.modifiers.new("pw_union", "BOOLEAN")
        m.operation = "UNION"
        m.operand_type = "COLLECTION"
        m.collection = col
        solvers = [e.identifier for e in m.bl_rna.properties["solver"].enum_items]
        solver = "MANIFOLD" if "MANIFOLD" in solvers and p.get("solver", "manifold") == "manifold" else "EXACT"
        m.solver = solver
        apply_modifier(base, m)
        lo, hi = bounds([base])
        lost = any(abs(lo[i] - want_lo[i]) > 1e-3 * max(1.0, abs(want_hi[i] - want_lo[i])) or
                   abs(hi[i] - want_hi[i]) > 1e-3 * max(1.0, abs(want_hi[i] - want_lo[i])) for i in range(3))
        if lost and solver == "MANIFOLD":  # Manifold skips operands it finds non-manifold, silently
            base.data = keep
            m = base.modifiers.new("pw_union", "BOOLEAN")
            m.operation = "UNION"
            m.operand_type = "COLLECTION"
            m.collection = col
            m.solver = solver = "EXACT"
            apply_modifier(base, m)
            solver = "EXACT (MANIFOLD dropped operands)"
        for o in rest:
            bpy.data.objects.remove(o, do_unlink=True)
    st = mesh_stats(base, base.data)
    if (st.get("boundary_edges") or st.get("non_manifold_edges")) and p.get("voxel_fallback_mm"):
        m = base.modifiers.new("pw_remesh", "REMESH")
        m.mode = "VOXEL"
        m.voxel_size = float(p["voxel_fallback_mm"])
        apply_modifier(base, m)
        solver = (solver or "") + "+voxel"
        st = mesh_stats(base, base.data)
    lo, hi = bounds([base])
    out = export(p["out"], p)
    return {"out": out, "solver": solver, "parts_in": len(objs), "open_parts_in": open_parts[:20], "tris": st["tris"],
            "dims": [round(hi[i] - lo[i], 4) for i in range(3)],
            "boundary_edges": st.get("boundary_edges"), "non_manifold_edges": st.get("non_manifold_edges"),
            "watertight": st.get("boundary_edges") == 0 and st.get("non_manifold_edges") == 0}


# ------------------------------------------------------------------------------------------ crowd

# OpenPose COCO-18 order: nose, neck, r shoulder, r elbow, r wrist, l shoulder, l elbow, l wrist, r hip, r knee,
# r ankle, l hip, l knee, l ankle, r eye, l eye, r ear, l ear. A figure faces local +X with up +Z, so its right
# is local -Y.
CROWD_ACTIONS = {  # step cycles per second, metres per second, leg swing (rad), forward lean (rad)
    "hold": (0.0, 0.0, 0.0, 0.02), "march": (0.9, 1.3, 0.35, 0.05), "advance": (1.1, 2.0, 0.45, 0.1),
    "charge": (1.5, 5.0, 0.7, 0.25), "clash": (1.1, 2.0, 0.45, 0.1),
}
CROWD_PARTS = ["torso", "head", "rthigh", "lthigh", "rshin", "lshin", "rupper", "lupper", "rfore", "lfore"]


def crowd_meshes(kit):
    """Low-poly parts shared by every figure. Limbs hang from their origin along -Z."""
    def make(name, build):
        bm = bmesh.new()
        build(bm)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        return me

    def cyl(r, length, segs=6):
        return lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=length,
                                                matrix=Matrix.Translation((0, 0, -length / 2)))

    def box(sx, sy, sz, z0=0.0):
        def b(bm):
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
            bmesh.ops.translate(bm, vec=(0, 0, z0 + sz / 2), verts=bm.verts)
        return b

    m = {"torso": make("pw_torso", box(0.24, 0.40, 0.55)),
         "head": make("pw_head", lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.12)),
         "thigh": make("pw_thigh", cyl(0.075, 0.46)), "shin": make("pw_shin", cyl(0.06, 0.46)),
         "upper": make("pw_upper", cyl(0.055, 0.30)), "fore": make("pw_fore", cyl(0.05, 0.30))}
    if "spear" in kit:
        m["spear"] = make("pw_spear", cyl(0.018, 2.6, 5))
    if "shield" in kit:
        m["shield"] = make("pw_shield", box(0.05, 0.55, 0.75, -0.375))
    if "helmet" in kit:
        m["helmet"] = make("pw_helmet", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.15,
                                                                         radius2=0.03, depth=0.2))
    return m


def seg(top, d):
    """Matrix for a part whose origin is its top end and which hangs along -Z, turned to point along d."""
    return Matrix.Translation(top) @ d.normalized().to_track_quat("-Z", "Y").to_matrix().to_4x4()


def crowd_pose(fig, t):
    """World matrices of each part and the 18 OpenPose joints of one figure at time t (seconds)."""
    cad, speed, amp, lean = CROWD_ACTIONS[fig["action"]]
    t = max(0.0, t - fig["delay"])
    travel = speed * fig["speed"] * t
    stopped = fig["stop"] is not None and travel >= fig["stop"]
    if stopped:  # a clash rank that reached its line: small steps, lean in, spear thrusts
        travel, amp, lean = fig["stop"], 0.08, 0.12
    phase = fig["phase"] + 2 * math.pi * cad * fig["speed"] * t
    sw = amp * math.sin(phase)
    yaw = Matrix.Rotation(fig["yaw"], 4, "Z")
    s = fig["scale"]
    root = Vector(fig["pos"]) + (yaw.to_3x3() @ Vector((travel, 0, 0)))
    Rt = Matrix.Rotation(lean, 3, "Y")

    def Ry(a):
        return Matrix.Rotation(a, 3, "Y")

    down = Vector((0, 0, -1))
    L = {}  # joints relative to the hip centre, metres, before scale
    for side, sgn, ang in (("r", -1, sw), ("l", 1, -sw)):
        hip = Vector((0, 0.1 * sgn, 0))
        knee_bend = 0.15 + amp * 0.9 * max(0.0, math.cos(phase + (0 if sgn < 0 else math.pi)))
        thigh, shin = Ry(-ang) @ down, Ry(-ang + knee_bend) @ down
        L[side + "hip"], L[side + "knee"] = hip, hip + thigh * 0.46
        L[side + "ankle"] = L[side + "knee"] + shin * 0.46
        L[side + "thigh_d"], L[side + "shin_d"] = thigh, shin
    L["neck"] = Rt @ Vector((0, 0, 0.55))
    L["head"] = L["neck"] + Rt @ Vector((0, 0, 0.15))
    thrust = 0.35 * math.sin(phase * 2.2) if stopped else 0.0
    for side, sgn in (("r", -1), ("l", 1)):
        sh = Rt @ Vector((0, 0.22 * sgn, 0.48))
        if side == "r" and "spear" in fig["kit"]:  # spear hand: forearm forward
            up_d, fo_d = Rt @ (Ry(-0.25 - thrust) @ down), Rt @ (Ry(-1.45 - thrust) @ down)
        elif side == "l" and "shield" in fig["kit"]:  # shield arm: forearm across the front
            up_d, fo_d = Rt @ (Ry(-0.3) @ down), Rt @ Vector((0.6, -0.8, 0.05)).normalized()
        else:
            a = (-sw if side == "r" else sw) * 0.8
            up_d, fo_d = Rt @ (Ry(-a) @ down), Rt @ (Ry(-a - 0.35) @ down)
        L[side + "sh"], L[side + "up_d"], L[side + "fo_d"] = sh, up_d, fo_d
        L[side + "elbow"] = sh + up_d * 0.30
        L[side + "wrist"] = L[side + "elbow"] + fo_d * 0.30
    lift = 0.06 - min(L["rankle"].z, L["lankle"].z)  # the lower foot stays on the ground
    base = Matrix.Translation(root) @ yaw @ Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation((0, 0, lift))
    parts = {"torso": base @ Rt.to_4x4(), "head": base @ Matrix.Translation(L["head"])}
    for side in "rl":
        parts[side + "thigh"] = base @ seg(L[side + "hip"], L[side + "thigh_d"])
        parts[side + "shin"] = base @ seg(L[side + "knee"], L[side + "shin_d"])
        parts[side + "upper"] = base @ seg(L[side + "sh"], L[side + "up_d"])
        parts[side + "fore"] = base @ seg(L[side + "elbow"], L[side + "fo_d"])
    if "helmet" in fig["kit"]:
        parts["helmet"] = base @ Matrix.Translation(L["head"] + Rt @ Vector((0, 0, 0.12)))
    if "spear" in fig["kit"]:
        levelled = fig["action"] == "charge" or stopped
        sd = (Rt @ Vector((1, 0, 0.08))).normalized() if levelled else Vector((0.05, 0, 1)).normalized()
        parts["spear"] = base @ seg(L["rwrist"] + sd * 1.0, -sd)
    if "shield" in fig["kit"]:
        parts["shield"] = base @ (Matrix.Translation(L["lwrist"] + Rt @ Vector((0.08, 0.1, 0.25))) @ Rt.to_4x4())
    fwd, hd = Rt @ Vector((1, 0, 0)), L["head"]
    joints = [hd + fwd * 0.12, L["neck"], L["rsh"], L["relbow"], L["rwrist"], L["lsh"], L["lelbow"], L["lwrist"],
              L["rhip"], L["rknee"], L["rankle"], L["lhip"], L["lknee"], L["lankle"],
              hd + fwd * 0.1 + Rt @ Vector((0, -0.045, 0.03)), hd + fwd * 0.1 + Rt @ Vector((0, 0.045, 0.03)),
              hd + Rt @ Vector((0, -0.12, 0)), hd + Rt @ Vector((0, 0.12, 0))]
    return parts, [base @ j for j in joints]


def crowd_gap(p):
    """Metres between the front ranks at frame 1. Default: what both sides close in two thirds of the shot,
    so a clash or charge meets on screen; 30 m when both sides only march or hold."""
    if p.get("gap"):
        return float(p["gap"])
    secs = int(p.get("frames", 81)) / float(p.get("fps", 16))
    acts = [p.get("action", "march"), p.get("action_b") or p.get("action", "march")]
    if not any(a in ("clash", "charge") for a in acts):
        return 30.0
    v = sum(CROWD_ACTIONS[a][1] for a in acts if a in CROWD_ACTIONS)
    return max(4.0, v * secs * 0.66)


def crowd_layout(p):
    """Two blocks facing each other across the battle line x = 0. Side A starts on the left and moves +X (screen
    right in the side view), side B the other way, so screen direction never flips. Every figure gets its own
    step phase, pace, height and jitter: no two read as clones."""
    import random
    rng = random.Random(int(p.get("seed", 1)))
    gap = crowd_gap(p)
    sp, rs = float(p.get("spacing", 1.1)), float(p.get("rank_spacing", 1.4))
    jit = float(p.get("jitter", 0.25))
    kit = set(p.get("kit", ["spear", "shield", "helmet"]))
    figs = []
    sides = [("a", -1, p.get("action", "march")), ("b", 1, p.get("action_b") or p.get("action", "march"))]
    for side, sgn, action in sides[:int(p.get("sides", 2))]:
        if action not in CROWD_ACTIONS:
            raise ValueError("unknown action %s (%s)" % (action, ", ".join(CROWD_ACTIONS)))
        for r in range(int(p.get("ranks", 6))):
            for c in range(int(p.get("cols", 30))):
                x0 = sgn * (gap / 2 + r * rs) + rng.uniform(-jit, jit)
                stop = max(0.0, abs(x0) - (0.45 + r * rs + rng.uniform(0, 2 * jit))) if action in ("clash", "charge") else None  # ranks halt in order
                figs.append({"side": side, "action": action, "kit": kit, "rank": r, "stop": stop,
                             "pos": (x0, c * sp + rng.uniform(-jit, jit), 0.0),
                             "yaw": (0.0 if side == "a" else math.pi) + rng.uniform(-0.1, 0.1),
                             "phase": rng.uniform(0, 2 * math.pi), "speed": rng.uniform(0.9, 1.1),
                             "scale": rng.uniform(0.94, 1.06),
                             "delay": rng.uniform(0, 0.4) if action == "charge" else 0.0})
    return figs


def crowd_camera(p):
    frontage = int(p.get("cols", 30)) * float(p.get("spacing", 1.1))
    reach = crowd_gap(p) / 2 + int(p.get("ranks", 6)) * float(p.get("rank_spacing", 1.4))
    lens = float(p.get("lens", 50))
    # default distance: both armies' depth fits the frame width (half width = distance * 18 / lens)
    dist = float(p.get("cam_dist") or reach * lens / 18 * 0.6)
    h, view = float(p.get("cam_height", 6.0)), p.get("view", "side")
    if p.get("cam"):
        return Vector(p["cam"]), Vector(p.get("aim") or (0, frontage * 0.4, 1.0))
    if view == "side":  # on the battle line, looking down the frontage: both sides, depth stacked by the lens
        return Vector((0, -dist, h)), Vector((0, frontage * 0.25, 0.8))
    if view == "behind":  # behind side A's last rank, looking at the enemy over the shoulders
        back = reach
        return Vector((-back - dist * 0.5, frontage * 0.5, max(h, 2.5))), Vector((0, frontage * 0.5, 1.0))
    if view == "high":  # crane or god's eye
        return Vector((0, -dist * 0.7, max(h, dist))), Vector((0, frontage * 0.4, 0.0))
    raise ValueError("unknown view %s (side, behind, high, or cam and aim points)" % view)


def act_crowd(p):
    """An army blockout and its control passes for a video model, one PNG per frame and pass: depth (inverse
    depth, near white, one range for the whole shot), mask (side A red, side B blue, all else black), clay (a
    lit grey render to repaint as a start frame), and 2D OpenPose joints in joints.json for pw.py to draw."""
    from bpy_extras.object_utils import world_to_camera_view
    reset()
    sc = bpy.context.scene
    W, H = (int(v) for v in p["size"])
    frames, fps = int(p.get("frames", 81)), int(p.get("fps", 16))
    out = os.path.abspath(p["out"])
    kit = set(p.get("kit", ["spear", "shield", "helmet"]))
    figs = crowd_layout(p)
    meshes = crowd_meshes(kit)
    col = bpy.data.collections.new("pw_crowd")
    sc.collection.children.link(col)
    objs = []  # (figure index, part, object)
    for i, f in enumerate(figs):
        for n in CROWD_PARTS + [k for k in ("spear", "shield", "helmet") if k in kit]:
            o = bpy.data.objects.new("f%d_%s" % (i, n), meshes[n[1:]] if n[0] in "rl" else meshes[n])
            col.objects.link(o)
            objs.append((i, n, o))
    ground = bpy.data.objects.new("pw_ground", bpy.data.meshes.new("pw_ground"))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=float(p.get("ground_m", 600)))
    bm.to_mesh(ground.data)
    bm.free()
    sc.collection.objects.link(ground)

    cam_data = bpy.data.cameras.new("pw_cam")
    cam_data.lens, cam_data.sensor_width, cam_data.sensor_fit = float(p.get("lens", 50)), 36.0, "HORIZONTAL"
    cam_data.clip_start, cam_data.clip_end = 0.1, 5000
    cam = bpy.data.objects.new("pw_cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    loc0, aim = crowd_camera(p)
    move, span = p.get("move", "static"), aim - loc0
    if move not in ("static", "push", "crane", "truck"):
        raise ValueError("unknown move %s (static, push, crane, truck)" % move)

    def cam_at(k):
        u = k / max(frames - 1, 1)
        e = u * u * (3 - 2 * u)  # ease in and out
        loc = {"static": loc0, "push": loc0 + span * 0.25 * e,
               "crane": loc0 + Vector((0, 0, span.length * 0.35 * e)),
               "truck": loc0 + Vector((span.length * 0.2 * e, 0, 0))}[move]
        cam.location = loc
        cam.rotation_euler = (aim - loc).to_track_quat("-Z", "Y").to_euler()
        return loc

    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.fps = fps
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    if sc.world is None:
        sc.world = bpy.data.worlds.new("pw_world")

    # One depth range for the whole shot: a range per frame makes the depth video pulse.
    # It spans the nearest ground in frame (bottom edge) to beyond the farthest figure, sampled over the shot.
    near, far = math.inf, 0.0
    for k in list(range(0, frames, max(1, frames // 8))) + [frames - 1]:
        loc = cam_at(k)
        bpy.context.view_layer.update()
        R = cam.matrix_world.to_3x3()
        fwd = R @ Vector((0, 0, -1))
        bottom = R @ Vector((0, -(H / 2) / (W * cam_data.lens / 36.0), -1.0))
        if bottom.z < 0:
            hit = bottom * (-loc.z / bottom.z)
            near = min(near, hit.dot(fwd))
        for f in figs:
            neck = crowd_pose(f, k / fps)[1][1]
            d = (neck - loc).dot(fwd)
            if d > 0:
                near, far = min(near, d - 1.0), max(far, d)
    near = max(0.3, near if near < math.inf else 1.0)
    far = float(p.get("far") or max(far, near + 1) * 1.3)

    depth_mat = bpy.data.materials.new("pw_depth")
    nt = depth_mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    cd, outn = nt.nodes.new("ShaderNodeCameraData"), nt.nodes.new("ShaderNodeOutputMaterial")
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "DIVIDE"
    inv.inputs[0].default_value = 1.0
    nt.links.new(cd.outputs["View Z Depth"], inv.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    mr.inputs["From Min"].default_value = 1.0 / far
    mr.inputs["From Max"].default_value = 1.0 / near
    nt.links.new(inv.outputs[0], mr.inputs["Value"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(mr.outputs["Result"], em.inputs["Strength"])
    nt.links.new(em.outputs[0], outn.inputs["Surface"])

    side_rgb = {"a": (1.0, 0.0, 0.0, 1), "b": (0.0, 0.0, 1.0, 1)}
    clay_rgb = {"a": (0.55, 0.42, 0.36, 1), "b": (0.36, 0.42, 0.52, 1)}
    passes = list(p.get("passes", ["depth", "mask", "clay", "pose"]))
    for d in passes:
        if d != "pose":
            os.makedirs(os.path.join(out, d), exist_ok=True)
    keys = sorted({0, frames // 2, frames - 1}) if p.get("preview") else list(range(frames))
    pose_min = float(p.get("pose_min_px", 40))
    joints_out = []
    t0 = time.time()
    for k in keys:
        cam_at(k)
        for f in figs:
            f["_parts"], f["_j"] = crowd_pose(f, k / fps)
        for i, n, o in objs:
            o.matrix_world = figs[i]["_parts"][n]
        bpy.context.view_layer.update()
        if "pose" in passes:
            people = []
            for f in figs:
                pj = [world_to_camera_view(sc, cam, v) for v in f["_j"]]
                if min(q.z for q in pj) <= 0.1:
                    continue
                px = [(q.x * W, (1 - q.y) * H) for q in pj]
                tall = abs(px[0][1] - (px[10][1] + px[13][1]) / 2)
                if tall < pose_min or not any(0 <= x < W and 0 <= y < H for x, y in px):
                    continue
                people.append([round(sum(q.z for q in pj) / 18, 2), [[round(x, 1), round(y, 1)] for x, y in px]])
            people.sort(key=lambda q: -q[0])  # far first, so near skeletons draw on top
            joints_out.append({"frame": k + 1, "people": people})
        name = "%04d.png" % (k + 1)
        if "depth" in passes:
            sc.render.engine = "CYCLES"
            sc.cycles.device = "GPU" if p.get("gpu") else "CPU"
            sc.cycles.samples = int(p.get("samples", 4))
            sc.cycles.use_denoising = False
            sc.view_settings.view_transform = "Raw"  # write the emission value as it is
            sc.world.color = (0, 0, 0)
            if sc.world.node_tree and sc.world.node_tree.nodes.get("Background"):
                sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
            bpy.context.view_layer.material_override = depth_mat
            sc.render.filepath = os.path.join(out, "depth", name)
            bpy.ops.render.render(write_still=True)
            bpy.context.view_layer.material_override = None
        for pas in ("mask", "clay"):
            if pas not in passes:
                continue
            flat = pas == "mask"
            sc.render.engine = "BLENDER_WORKBENCH"
            sc.view_settings.view_transform = "Standard"
            sh = sc.display.shading
            sh.color_type = "OBJECT"
            sh.light = "FLAT" if flat else "STUDIO"
            sh.show_shadows = sh.show_cavity = sh.show_specular_highlight = not flat
            sh.show_object_outline = False
            sh.shadow_intensity = 0.5
            sc.display.light_direction = (0.45, -0.35, 0.82)
            for i, n, o in objs:
                o.color = (side_rgb if flat else clay_rgb)[figs[i]["side"]]
            ground.color = (0, 0, 0, 1) if flat else (0.48, 0.45, 0.38, 1)
            sc.world.color = (0, 0, 0) if flat else (0.62, 0.66, 0.72)
            sc.render.filepath = os.path.join(out, pas, name)
            bpy.ops.render.render(write_still=True)
    if "pose" in passes:
        with open(os.path.join(out, "joints.json"), "w", encoding="utf-8") as fh:
            json.dump({"size": [W, H], "frames": joints_out}, fh, separators=(",", ":"))
    cams = []
    for k in range(frames):
        cam_at(k)
        bpy.context.view_layer.update()
        cams.append([round(v, 5) for row in cam.matrix_world for v in row])
    with open(os.path.join(out, "camera.json"), "w", encoding="utf-8") as fh:
        json.dump({"lens_mm": cam_data.lens, "sensor_mm": 36.0, "size": [W, H], "fps": fps,
                   "matrix_world_rows": cams}, fh, separators=(",", ":"))
    if p.get("save_blend"):
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "crowd.blend"))
    return {"out": out, "figures": {s: sum(1 for f in figs if f["side"] == s) for s in ("a", "b")},
            "objects": len(objs), "frames_rendered": len(keys), "frames": frames, "fps": fps, "size": [W, H],
            "near_m": round(near, 2), "far_m": round(far, 2), "camera": [round(v, 2) for v in loc0],
            "aim": [round(v, 2) for v in aim], "passes": passes, "render_seconds": round(time.time() - t0, 1)}


ACTIONS = {"inspect": act_inspect, "render": act_render, "match": act_match, "convert": act_convert,
           "printable": act_printable, "union": act_union, "crowd": act_crowd}


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
