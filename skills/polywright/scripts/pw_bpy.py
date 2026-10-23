"""pw_bpy.py - the Blender side of polywright. Run by pw.py, not by hand:

    blender --background --factory-startup --python-exit-code 3 --python pw_bpy.py -- <action> <params.json> <result.json>

or with any Python that can `import bpy` (the bpy module from PyPI):

    python pw_bpy.py -- <action> <params.json> <result.json>

Actions: inspect (with an optional wall-thickness pass), render, match, convert, printable, union, crowd, duel, turnaround, mark, lineup. Each reads its parameters from params.json and writes one
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
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pw import hidden_face_points  # noqa: E402  plain maths, shared with pw.py and tested there

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


def topology_report(me):
    """Face sides, poles, winding, stacked faces, loose parts and UV texel spread, on welded positions (glTF and
    STL split vertices per face). A winding mismatch is an edge two faces walk the same way: a flipped face,
    which a game or web renderer culls into a hole. Poles count interior vertices with other than four edges;
    they matter on quad meshes that bend (Squeaky Clean Topology: five edges at most near joints)."""
    nf = len(me.polygons)
    if not nf:
        return {}
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    span = float(np.ptp(co, axis=0).max()) if len(co) else 1.0
    _, w = np.unique(np.round(co / max(span * 1e-6, 1e-12)).astype(np.int64), axis=0, return_inverse=True)
    w = w.reshape(-1)
    nv = int(w.max()) + 1
    lt = np.empty(nf, dtype=np.int64)
    ls = np.empty(nf, dtype=np.int64)
    me.polygons.foreach_get("loop_total", lt)
    me.polygons.foreach_get("loop_start", ls)
    lv = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("vertex_index", lv)
    lw = w[lv]
    nxt = np.arange(len(lw)) + 1
    nxt[ls + lt - 1] = ls
    a, b = lw, lw[nxt]
    a, b = a[a != b], b[a != b]
    uk, inv, cnt = np.unique(np.minimum(a, b) * nv + np.maximum(a, b), return_inverse=True, return_counts=True)
    fwd = np.bincount(inv.reshape(-1), weights=(a < b).astype(np.float64), minlength=len(uk))
    two = cnt == 2
    e0, e1 = uk // nv, uk % nv
    val = np.bincount(e0, minlength=nv) + np.bincount(e1, minlength=nv)
    border = np.zeros(nv, bool)
    border[e0[~two]] = border[e1[~two]] = True
    used = np.zeros(nv, bool)
    used[lw] = True
    inner = used & ~border
    vals, vc = np.unique(val[inner], return_counts=True)
    # faces with the same corners: double-sided copies or stacked faces, which z-fight
    small = lt <= 4
    pad = np.full((nf, 4), -1, dtype=np.int64)
    for k in range(4):
        m = small & (lt > k)
        pad[m, k] = lw[ls[m] + k]
    keys = np.sort(pad[small], axis=1)
    dup = len(keys) - len(np.unique(keys, axis=0)) if len(keys) else 0
    seen = set()
    for i in np.nonzero(~small)[0].tolist():
        s = tuple(sorted(lw[ls[i]:ls[i] + lt[i]].tolist()))
        dup += s in seen
        seen.add(s)
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tv = np.empty(nt * 3, dtype=np.int64)
    tp = np.empty(nt, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", tv)
    me.loop_triangles.foreach_get("polygon_index", tp)
    P = co[tv.reshape(-1, 3)]
    farea = np.bincount(tp, weights=0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1), minlength=nf)
    el = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("edge_index", el)
    ev = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", ev)
    rep = {"tris": int((lt == 3).sum()), "quads": int((lt == 4).sum()), "ngons": int((lt > 4).sum()),
           "quad_share": round(float((lt == 4).mean()), 3),
           "poles": {str(int(k)): int(c) for k, c in zip(vals, vc) if k != 4},
           "max_pole_valence": int(val[inner].max()) if inner.any() else 0,
           "winding_mismatch": int((two & ((fwd == 0) | (fwd == 2))).sum()),
           "duplicate_faces": int(dup), "zero_area_faces": int((farea <= span * span * 1e-12).sum()),
           "loose_edges": int(len(me.edges) - len(np.unique(el))),
           "loose_verts": int(len(me.vertices) - len(np.unique(ev)))}
    if me.uv_layers.active and nt:
        uv = np.empty(len(me.loops) * 2, dtype=np.float64)
        me.uv_layers.active.data.foreach_get("uv", uv)
        tl = np.empty(nt * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("loops", tl)
        U = uv.reshape(-1, 2)[tl.reshape(-1, 3)]
        d1, d2 = U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]
        fuv = np.bincount(tp, weights=0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]), minlength=nf)
        ok = (farea > 0) & (fuv > 0)
        rep["uv_area"] = round(float(fuv.sum()), 4)
        rep["uv_zero_faces"] = int((fuv <= 0).sum())
        if ok.any():
            # texel density per face against the mesh's mean (1.0 = even); percentiles weighted by surface area,
            # so seam slivers do not decide
            ratio = (fuv[ok] / fuv[ok].sum()) / (farea[ok] / farea[ok].sum())
            order = np.argsort(ratio)
            cw = np.cumsum(farea[ok][order])
            cw /= cw[-1]
            pick = lambda q: float(ratio[order][min(int(np.searchsorted(cw, q)), len(ratio) - 1)])
            p5, p95 = pick(0.05), pick(0.95)
            rep.update(uv_texel_p5=round(p5, 3), uv_texel_p95=round(p95, 3), uv_spread=round(p95 / p5, 2) if p5 > 0 else None)
    rep["area"] = float(farea.sum())
    return rep


def fix_winding(obj):
    """Flip the faces that wind against their neighbours, on welded positions, without merging vertices (so UVs
    and split normals stay). Per connected part the larger surface keeps its winding. Returns faces flipped."""
    me = obj.data
    nf = len(me.polygons)
    if not nf:
        return 0
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    span = float(np.ptp(co, axis=0).max()) if len(co) else 1.0
    _, w = np.unique(np.round(co / max(span * 1e-6, 1e-12)).astype(np.int64), axis=0, return_inverse=True)
    w = w.reshape(-1)
    nv = int(w.max()) + 1
    lt = np.empty(nf, dtype=np.int64)
    ls = np.empty(nf, dtype=np.int64)
    me.polygons.foreach_get("loop_total", lt)
    me.polygons.foreach_get("loop_start", ls)
    lv = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("vertex_index", lv)
    lw = w[lv]
    nxt = np.arange(len(lw)) + 1
    nxt[ls + lt - 1] = ls
    fl = np.repeat(np.arange(nf), lt)
    a, b = lw, lw[nxt]
    keep = a != b
    a, b, fl = a[keep], b[keep], fl[keep]
    _, inv, cnt = np.unique(np.minimum(a, b) * nv + np.maximum(a, b), return_inverse=True, return_counts=True)
    inv = inv.reshape(-1)
    order = np.argsort(inv, kind="stable")
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])[cnt == 2]
    f1, f2 = fl[order][start], fl[order][start + 1]
    d = (a < b)[order]
    same = (d[start] == d[start + 1]).astype(np.int8)  # same walk: the two faces disagree
    adj = [[] for _ in range(nf)]
    for x, y, s in zip(f1.tolist(), f2.tolist(), same.tolist()):
        if x != y:
            adj[x].append((y, s))
            adj[y].append((x, s))
    me.calc_loop_triangles()
    tv = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    tp = np.empty(len(me.loop_triangles), dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", tv)
    me.loop_triangles.foreach_get("polygon_index", tp)
    P = co[tv.reshape(-1, 3)]
    area = np.bincount(tp, weights=np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1), minlength=nf).tolist()
    flip = [-1] * nf
    out = []
    for seed in range(nf):
        if flip[seed] >= 0:
            continue
        flip[seed] = 0
        part, stack = [seed], [seed]
        while stack:
            f = stack.pop()
            for g, s in adj[f]:
                if flip[g] < 0:
                    flip[g] = flip[f] ^ s
                    part.append(g)
                    stack.append(g)
        a1 = sum(area[f] for f in part if flip[f])
        if a1 * 2 > sum(area[f] for f in part):
            out += [f for f in part if not flip[f]]
        else:
            out += [f for f in part if flip[f]]
    for f in out:
        me.polygons[f].flip()
    me.update()
    return len(out)


def topology_total(reps):
    """One report for the file: counts summed, poles merged, UV spread of the worst object that holds at least
    2% of the surface (each object has its own UV space)."""
    reps = [r for r in reps if r]
    if not reps:
        return {}
    tot = {k: sum(r[k] for r in reps) for k in ("tris", "quads", "ngons", "winding_mismatch", "duplicate_faces",
                                                 "zero_area_faces", "loose_edges", "loose_verts")}
    faces = tot["tris"] + tot["quads"] + tot["ngons"]
    tot["quad_share"] = round(tot["quads"] / float(faces), 3) if faces else 0.0
    poles = {}
    for r in reps:
        for k, c in r["poles"].items():
            poles[k] = poles.get(k, 0) + c
    tot["poles"] = dict(sorted(poles.items(), key=lambda kv: int(kv[0])))
    tot["max_pole_valence"] = max(r["max_pole_valence"] for r in reps)
    area = sum(r["area"] for r in reps) or 1.0
    uv = [r for r in reps if r.get("uv_spread") and r["area"] >= 0.02 * area]
    if uv:
        worst = max(uv, key=lambda r: r["uv_spread"])
        tot.update(uv_spread=worst["uv_spread"], uv_texel_p5=worst["uv_texel_p5"], uv_texel_p95=worst["uv_texel_p95"])
    return tot


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
    rows, topo = [], []
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        rows.append(mesh_stats(o, me, deep))
        if p.get("topology"):
            t = topology_report(me)
            topo.append(t)
            rows[-1]["topology"] = {k: v for k, v in t.items() if k != "area"}
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
    if p.get("topology"):
        res["topology"] = topology_total(topo)
    if p.get("thickness_min"):
        res["thickness"] = wall_thickness(objs, float(p["thickness_min"]), int(p.get("thickness_samples", 20000)))
    return res


def wall_thickness(objs, minimum, samples=20000, seed=7):
    """Local wall thickness by inward rays, the method of Blender's 3D-Print Toolbox thickness check:
    from points on the surface, cast a ray along the inward normal and measure where it leaves the solid
    (the first hit on a face pointing the same way). Points are spread over the surface by area, so
    `thin_fraction` is the share of the surface thinner than `minimum`. Units are the file's."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    verts, tris = [], []
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        me.calc_loop_triangles()
        mw, base = o.matrix_world, len(verts)
        verts.extend(mw @ v.co for v in me.vertices)
        tris.extend(tuple(base + i for i in t.vertices) for t in me.loop_triangles)
        oe.to_mesh_clear()
    if not tris:
        return {"status": "unchecked", "detail": "no faces"}
    tree = BVHTree.FromPolygons(verts, tris, all_triangles=True)
    v = np.array([tuple(x) for x in verts], dtype=np.float64)
    t = np.array(tris, dtype=np.int64)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    cross = np.cross(b - a, c - a)
    area2 = np.linalg.norm(cross, axis=1)
    keep = area2 > 1e-18
    if not keep.any():
        return {"status": "unchecked", "detail": "degenerate faces only"}
    normals = np.zeros_like(cross)
    normals[keep] = cross[keep] / area2[keep, None]
    rng = np.random.default_rng(seed)
    n = int(min(samples, max(len(t), 1) * 4))
    pick = rng.choice(len(t), size=n, p=area2 / area2.sum())
    r1, r2 = rng.random(n), rng.random(n)
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    pts = a[pick] + (b[pick] - a[pick]) * r1[:, None] + (c[pick] - a[pick]) * r2[:, None]
    diag = float(np.linalg.norm(v.max(axis=0) - v.min(axis=0))) or 1.0
    eps, reach = diag * 1e-6, minimum * 4.0
    depth = np.full(n, np.inf)
    for i in range(n):
        nrm = normals[pick[i]]
        if not nrm.any():
            continue
        d = Vector(-nrm)
        origin = Vector(pts[i]) + d * eps
        travelled = 0.0
        for _ in range(8):  # step past faces that point back at the ray (internal or overlapping shells)
            hit, hn, idx, dist = tree.ray_cast(origin, d, reach - travelled)
            if hit is None:
                break
            travelled += dist
            if hn.dot(d) > 0:
                depth[i] = travelled + eps
                break
            origin = hit + d * eps
    thin = depth < minimum
    finite = depth[np.isfinite(depth)]
    res = {"minimum": minimum, "samples": n, "thin_fraction": round(float(thin.mean()), 4),
           "thinnest": round(float(finite.min()), 4) if finite.size else None,
           "p05": round(float(np.percentile(finite, 5)), 4) if finite.size else None,
           "method": "inward rays from %d surface points, area-weighted" % n}
    spots = []
    for i in np.argsort(depth)[:200]:
        if not thin[i]:
            break
        p_ = pts[i]
        if all(np.linalg.norm(p_ - np.array(s["at"])) > minimum * 5 for s in spots):
            spots.append({"at": [round(float(x), 3) for x in p_], "thickness": round(float(depth[i]), 3)})
        if len(spots) == 5:
            break
    res["thin_spots"] = spots
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


def level_rotation(objs, max_tilt_deg=45.0, samples=60000, seed=3):
    """The rotation that stands a model on its base: the largest flat face of its convex hull whose normal is
    within max_tilt_deg of straight down, turned to face straight down. Image-to-3D models built in the camera's
    frame (Pixal3D) lean by the camera's elevation; a pedestal, a plinth or two feet span such a face."""
    pts = []
    for o in objs:
        mw = o.matrix_world
        pts.extend(mw @ v.co for v in o.data.vertices)
    if len(pts) < 4:
        return None, {"error": "too few vertices"}
    if len(pts) > samples:
        rng = np.random.default_rng(seed)
        arr = np.array([tuple(p_) for p_ in pts])
        keep = set(rng.choice(len(pts), samples, replace=False).tolist())
        for ax in range(3):  # keep the extremes so the sampled hull still touches the real base
            keep.update(np.argsort(arr[:, ax])[:200].tolist())
            keep.update(np.argsort(arr[:, ax])[-200:].tolist())
        low = arr[:, 2] < np.percentile(arr[:, 2], 8)
        keep.update(np.nonzero(low)[0][:samples].tolist())
        pts = [pts[i] for i in sorted(keep)]
    bm = bmesh.new()
    for p_ in pts:
        bm.verts.new(p_)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bm.faces.ensure_lookup_table()
    down, best, groups = Vector((0, 0, -1)), None, []
    cos_max = math.cos(math.radians(max_tilt_deg))
    for f in bm.faces:
        n = f.normal
        if n.length < 0.5 or n.dot(down) < cos_max:
            continue
        for g in groups:  # merge nearly coplanar hull faces into one candidate base
            if g["n"].dot(n) > math.cos(math.radians(2.0)):
                g["area"] += f.calc_area()
                g["sum"] += n * f.calc_area()
                break
        else:
            groups.append({"n": n.copy(), "area": f.calc_area(), "sum": n * f.calc_area()})
    total = sum(f.calc_area() for f in bm.faces)
    bm.free()
    if not groups:
        return None, {"error": "no hull face within %.0f degrees of down" % max_tilt_deg}
    best = max(groups, key=lambda g: g["area"])
    n = best["sum"].normalized()
    rot = n.rotation_difference(down).to_matrix().to_4x4()
    return rot, {"tilt_deg": round(math.degrees(n.angle(down)), 2), "base_share": round(best["area"] / total, 4),
                 "base_normal": [round(x, 4) for x in n]}


def act_convert(p):
    objs = load(p["file"])
    notes = []
    if p.get("level") or p.get("tilt_deg"):
        objs = flatten_hierarchy()
        if p.get("tilt_deg"):
            rot = Matrix.Rotation(math.radians(float(p["tilt_deg"])), 4, "X")
            info = {"tilt_deg": float(p["tilt_deg"]), "how": "given"}
        else:
            rot, info = level_rotation(objs, float(p.get("max_tilt_deg", 45)))
            info["how"] = "hull base"
        if rot is not None:
            for o in objs:
                o.data.transform(rot)
                o.data.update()
            notes.append("levelled by %.2f deg (%s)" % (info["tilt_deg"], info["how"]))
        else:
            notes.append("not levelled: %s" % info.get("error"))
        p["_level"] = info
    if p.get("apply") or p.get("join") or p.get("uv") or p.get("size_m") or p.get("ground") or p.get("center") or p.get("max_tris") or p.get("ratio") or p.get("fix_winding"):
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
    if p.get("fix_winding"):
        n = sum(fix_winding(o) for o in objs)
        notes.append("%d face(s) flipped to agree with their neighbours" % n)
        p["_flipped"] = n
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
    if "_level" in p:
        res["level"] = p["_level"]
    if "_flipped" in p:
        res["faces_flipped"] = p["_flipped"]
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
    if p.get("remesh", True) and not p.get("hollow"):
        # image-to-3D meshes are often thin double-walled shells: the remesh above keeps them hollow, with
        # walls a slicer drops. Fill what the outside cannot reach when it is a real share of the volume.
        vol = mesh_stats(obj, obj.data).get("volume", 0) or 0
        filled, cell, core = fill_cavities(obj, float(p.get("seal_mm", 1.0)))
        if core is not None and vol > 0 and filled > float(p.get("fill_ratio", 0.1)) * vol:
            select_only([obj, core], obj)
            bpy.ops.object.join()
            m = obj.modifiers.new("pw_remesh_fill", "REMESH")
            m.mode = "VOXEL"
            m.voxel_size = voxel
            m.adaptivity = 0.0
            apply_modifier(obj, m)
            keep_largest_part(obj)
            steps.append("hollow shell: filled %.0f mm3 the outside cannot reach (seal %.2f mm, %.3f mm cells)" % (
                filled, float(p.get("seal_mm", 1.0)), cell))
        elif core is not None:
            bpy.data.objects.remove(core, do_unlink=True)
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


def _shift_or(a, k=1):
    """Dilate a boolean grid by k voxels, 6-connected (an L1 ball)."""
    for _ in range(k):
        b = a.copy()
        b[1:] |= a[:-1]
        b[:-1] |= a[1:]
        b[:, 1:] |= a[:, :-1]
        b[:, :-1] |= a[:, 1:]
        b[:, :, 1:] |= a[:, :, :-1]
        b[:, :, :-1] |= a[:, :, 1:]
        a = b
    return a


def _flood_outside(free):
    """Cells of `free` connected to the grid's border, by sweeping whole runs of free cells along each axis in
    turn until nothing changes (a few sweeps reach any pocket a path with a few turns can)."""
    out = np.zeros_like(free)
    out[0], out[-1], out[:, 0], out[:, -1], out[:, :, 0], out[:, :, -1] = (free[0], free[-1], free[:, 0], free[:, -1],
                                                                          free[:, :, 0], free[:, :, -1])
    for _ in range(200):
        before = int(out.sum())
        for ax in range(3):
            f = np.moveaxis(free, ax, -1).reshape(-1, free.shape[ax])
            o = np.moveaxis(out, ax, -1).reshape(-1, free.shape[ax])
            start = f.copy()
            start[:, 1:] &= ~f[:, :-1]
            ids = np.cumsum(start.ravel()).reshape(f.shape)
            hit = np.bincount(ids[f], weights=o[f], minlength=int(ids.max()) + 1) > 0
            o = f & hit[ids]
            out = np.moveaxis(o.reshape(np.moveaxis(free, ax, -1).shape), -1, ax).copy()
        if int(out.sum()) == before:
            break
    return out


def fill_cavities(obj, seal_mm=1.0, max_cells=12_000_000):
    """Make a solid out of a model that is a closed or nearly closed thin shell (image-to-3D meshes often are:
    the surface is two thin walls with air between). Voxelise the surface, seal gaps narrower than seal_mm,
    flood the outside from the border, and build a core of every cell the outside cannot reach, ending about a
    cell inside the surface, so a voxel remesh of the two joined unions them. Grooves narrower than seal_mm
    fill too. Returns (mm3 enclosed, cell size, core object or None); the caller joins or deletes the core."""
    me = obj.data
    me.calc_loop_triangles()
    v = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3)
    t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", t)
    t = t.reshape(-1, 3)
    lo, hi = v.min(axis=0), v.max(axis=0)
    ext = hi - lo
    g = max(float(np.cbrt(np.prod(ext + 1e-9) / max_cells)), 1e-6)
    k = max(1, int(round(seal_mm / 2.0 / g)))
    pad = k + 2
    origin = lo - pad * g
    shape = tuple(int(x) for x in np.ceil(ext / g) + 2 * pad + 1)
    surf = np.zeros(shape, dtype=bool)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    longest = np.maximum(np.maximum(np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1)), np.linalg.norm(a - c, axis=1))
    steps = np.clip(np.ceil(longest / (g * 0.5)).astype(np.int64), 1, 400)
    for s in np.unique(steps):  # sample each triangle on a barycentric grid finer than half a cell
        sel = steps == s
        i, j = np.meshgrid(np.arange(s + 1), np.arange(s + 1), indexing="ij")
        m = (i + j) <= s
        u, w = (i[m] / s)[None, :, None], (j[m] / s)[None, :, None]
        pts = a[sel][:, None] + (b[sel] - a[sel])[:, None] * u + (c[sel] - a[sel])[:, None] * w
        idx = np.floor((pts.reshape(-1, 3) - origin) / g).astype(np.int64)
        surf[idx[:, 0], idx[:, 1], idx[:, 2]] = True
    shell = _shift_or(surf, k)
    outside = _flood_outside(~shell)
    core = ~_shift_or(outside, k + 1)
    # air only: cells the outside reaches through the gaps (unsealed) but not once they are sealed. Counting the
    # whole core would count a solid's own inside and send solid models and terrain sheets through the fill.
    reach = _flood_outside(~_shift_or(surf, 1))
    cavity = core & reach
    filled = float(cavity.sum()) * g ** 3
    if not core.any():
        return 0.0, g, None
    # boundary faces of the core cells as quads
    verts, faces, index = [], [], {}

    def vid(x, y, z):
        key = (x, y, z)
        if key not in index:
            index[key] = len(verts)
            verts.append((origin[0] + x * g, origin[1] + y * g, origin[2] + z * g))
        return index[key]

    padded = np.pad(core, 1)
    for ax in range(3):
        for sign in (1, -1):
            nb = np.roll(padded, -sign, axis=ax)[1:-1, 1:-1, 1:-1]
            for x, y, z in np.argwhere(core & ~nb):
                o = [x, y, z]
                o[ax] += 1 if sign > 0 else 0
                e1, e2 = [0, 0, 0], [0, 0, 0]
                e1[(ax + 1) % 3], e2[(ax + 2) % 3] = 1, 1
                quad = [o, [o[i] + e1[i] for i in range(3)], [o[i] + e1[i] + e2[i] for i in range(3)], [o[i] + e2[i] for i in range(3)]]
                if sign < 0:
                    quad.reverse()
                faces.append([vid(*q) for q in quad])
    core_me = bpy.data.meshes.new("pw_core")
    core_me.from_pydata(verts, [], faces)
    core_obj = bpy.data.objects.new("pw_core", core_me)
    bpy.context.scene.collection.objects.link(core_obj)
    core_obj.matrix_world = obj.matrix_world.copy()
    return filled, g, core_obj


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


def make(name, build):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def cyl(r, length, segs=6):
    """A cylinder whose origin is its top end, hanging along -Z."""
    return lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=length,
                                            matrix=Matrix.Translation((0, 0, -length / 2)))


def box(sx, sy, sz, z0=0.0):
    def b(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, z0 + sz / 2), verts=bm.verts)
    return b


def sphere(r, u=8, v=6):
    return lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)


def crowd_meshes(kit):
    """Low-poly parts shared by every figure. Limbs hang from their origin along -Z."""
    m = {"torso": make("pw_torso", box(0.24, 0.40, 0.55)),
         "head": make("pw_head", sphere(0.12)),
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


def scatter_tree(name, bank, gap, density, seed):
    """Geometry Nodes: Poisson points on the carrier's faces (at least `gap` apart), one child of `bank` per
    point picked at random, random yaw and scale. Instances stay instances: cheap to render; realize them only
    for one printable or measurable mesh. The carrier's own faces are not output."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    pts = N.new("GeometryNodeDistributePointsOnFaces")
    pts.distribute_method = "POISSON"
    pts.inputs["Distance Min"].default_value = gap
    pts.inputs["Density Max"].default_value = density
    pts.inputs["Seed"].default_value = seed
    info = N.new("GeometryNodeCollectionInfo")
    info.inputs["Collection"].default_value = bank
    info.inputs["Separate Children"].default_value = True
    info.inputs["Reset Children"].default_value = True
    inst = N.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Pick Instance"].default_value = True

    def rnd(kind, lo, hi, s):
        n = N.new("FunctionNodeRandomValue")
        n.data_type = kind
        for sock in n.inputs:
            if sock.enabled and sock.name in ("Min", "Max", "Seed"):
                sock.default_value = {"Min": lo, "Max": hi, "Seed": s}[sock.name]
        return next(o for o in n.outputs if o.enabled)  # the output follows data_type; never index it

    yaw = N.new("ShaderNodeCombineXYZ")
    L.new(gi.outputs["Geometry"], pts.inputs["Mesh"])
    L.new(pts.outputs["Points"], inst.inputs["Points"])
    L.new(info.outputs[0], inst.inputs["Instance"])
    L.new(rnd("INT", 0, len(bank.objects) - 1, seed + 1), inst.inputs["Instance Index"])
    L.new(rnd("FLOAT", -0.26, 0.26, seed + 2), yaw.inputs["Z"])
    L.new(yaw.outputs[0], inst.inputs["Rotation"])
    L.new(rnd("FLOAT", 0.94, 1.06, seed + 3), inst.inputs["Scale"])
    L.new(inst.outputs[0], go.inputs["Geometry"])
    return ng


def crowd_scatter(p, meshes, kit):
    """Background figures behind each side's last rank: a few standing variants per side, joined into one mesh
    each and scattered by Geometry Nodes (Poisson, a minimum gap). They hold still and draw no skeletons.
    A side whose rear the camera stands in (the behind view) gets none: its figures would block the lens.
    Returns ({side: (carrier object, variant objects)}, [skipped sides])."""
    n = int(p.get("scatter", 0))
    gap, deep = float(p.get("scatter_gap", 1.2)), float(p.get("scatter_depth", 25.0))
    front = crowd_gap(p) / 2 + int(p.get("ranks", 6)) * float(p.get("rank_spacing", 1.4)) + 2.0
    width = int(p.get("cols", 30)) * float(p.get("spacing", 1.1)) + 4.0
    out, skipped = {}, []
    cam_x = crowd_camera(p)[0].x
    for side, sgn in (("a", -1), ("b", 1))[:int(p.get("sides", 2))]:
        if sgn * cam_x > front - 5.0:
            skipped.append(side)
            continue
        bank = bpy.data.collections.new("pw_scatter_bank_" + side)  # not linked to the scene: instanced only
        variants = []
        for v, (scale, drop) in enumerate(((0.95, ""), (1.0, "helmet"), (1.05, "shield"))):
            fk = set(kit) - {drop}
            f = {"side": side, "action": "hold", "kit": fk, "rank": 0, "stop": None, "pos": (0, 0, 0),
                 "yaw": 0.0 if side == "a" else math.pi, "phase": 1.3 * v, "speed": 1.0, "scale": scale, "delay": 0.0}
            parts, _ = crowd_pose(f, 0.0)
            bm = bmesh.new()
            for part, M in parts.items():
                k = len(bm.verts)
                bm.from_mesh(meshes[part[1:]] if part[0] in "rl" else meshes[part])
                bm.verts.ensure_lookup_table()
                bmesh.ops.transform(bm, matrix=M, verts=bm.verts[k:])
            me = bpy.data.meshes.new("pw_bg_%s%d" % (side, v))
            bm.to_mesh(me)
            bm.free()
            o = bpy.data.objects.new(me.name, me)
            bank.objects.link(o)
            variants.append(o)
        carrier = bpy.data.objects.new("pw_scatter_" + side, bpy.data.meshes.new("pw_scatter_" + side))
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        bmesh.ops.scale(bm, vec=(deep, width, 1), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(sgn * (front + deep / 2), width / 2 - 2.0, 0), verts=bm.verts)
        bm.to_mesh(carrier.data)
        bm.free()
        bpy.context.scene.collection.objects.link(carrier)
        mod = carrier.modifiers.new("scatter", "NODES")
        mod.node_group = scatter_tree("pw_scatter_" + side, bank, gap, n / (deep * width), int(p.get("seed", 1)) * 7 + len(out))
        out[side] = (carrier, variants)
    return out, skipped


def count_instances(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    names = {o.name for o in objs}
    return sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original.name in names)


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


def depth_material(near, far):
    """Inverse depth as emission, near white to far black, one range for the whole shot (a range per frame pulses)."""
    mat = bpy.data.materials.new("pw_depth")
    nt = mat.node_tree
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
    return mat


def render_depth(path, mat, p):
    """One depth frame in Cycles with every object drawn by `mat` and the world black."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU" if p.get("gpu") else "CPU"
    sc.cycles.samples = int(p.get("samples", 4))
    sc.cycles.use_denoising = False
    sc.view_settings.view_transform = "Raw"  # write the emission value as it is
    if sc.world is None:
        sc.world = bpy.data.worlds.new("pw_world")
    sc.world.color = (0, 0, 0)
    if sc.world.node_tree and sc.world.node_tree.nodes.get("Background"):
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    bpy.context.view_layer.material_override = mat
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override = None


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
    scat, scat_skipped = crowd_scatter(p, meshes, kit) if int(p.get("scatter", 0)) > 0 else ({}, [])

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
        for carrier, _ in scat.values():  # the far edge of each scatter, so its figures do not clip to black
            lo_c, hi_c = bounds([carrier])
            for x in (lo_c[0], hi_c[0]):
                d = (Vector((x, (lo_c[1] + hi_c[1]) / 2, 1.5)) - loc).dot(fwd)
                if d > 0:
                    far = max(far, d)
    near = max(0.3, near if near < math.inf else 1.0)
    far = float(p.get("far") or max(far, near + 1) * 1.3)

    depth_mat = depth_material(near, far)

    side_rgb = {"a": (1.0, 0.0, 0.0, 1), "b": (0.0, 0.0, 1.0, 1)}
    clay_rgb = {"a": (0.55, 0.42, 0.36, 1), "b": (0.36, 0.42, 0.52, 1)}
    passes = list(p.get("passes", ["depth", "mask", "clay", "pose"]))
    os.makedirs(out, exist_ok=True)  # pose alone writes only joints.json here
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
                for i in hidden_face_points(f["_j"], cam.matrix_world.translation):
                    px[i] = (-1, -1)  # a detector would not see them; drawn, they turn a back into a face
                people.append([round(sum(q.z for q in pj) / 18, 2), [[round(x, 1), round(y, 1)] for x, y in px]])
            people.sort(key=lambda q: -q[0])  # far first, so near skeletons draw on top
            joints_out.append({"frame": k + 1, "people": people})
        name = "%04d.png" % (k + 1)
        if "depth" in passes:
            render_depth(os.path.join(out, "depth", name), depth_mat, p)
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
            for s, (carrier, variants) in scat.items():
                for o in [carrier] + variants:
                    o.color = (side_rgb if flat else clay_rgb)[s]
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
            "aim": [round(v, 2) for v in aim], "passes": passes, "render_seconds": round(time.time() - t0, 1),
            **({"scatter": {s: count_instances([c]) for s, (c, _) in scat.items()}} if scat else {}),
            **({"scatter_skipped": "side %s: the camera stands in its rear" % ",".join(scat_skipped)} if scat_skipped else {})}


# ------------------------------------------------------------------------------------------ duel

def ik(a, t, l1, l2, pole):
    """Two-bone IK: (middle joint, end) of a limb from a toward t with segment lengths l1 and l2, bent toward pole."""
    d = t - a
    dist = max(min(d.length, (l1 + l2) * 0.999), 0.05)
    dn = d.normalized()
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    side = pole - dn * pole.dot(dn)
    if side.length < 1e-6:
        side = Vector((0, 0, 1)) - dn * dn.z
    return a + dn * x + side.normalized() * h, a + dn * dist


def duel_figure(f, q):
    """World matrices of each part and the 18 COCO joints of fighter f in the resolved pose q (pw.py's
    duel_pose_at): the crowd mannequin posed by IK to hand and foot targets, blades rigid on the wrists."""
    s = f["scale"]
    base = (Matrix.Translation((f["mark"][0], f["mark"][1], 0)) @ Matrix.Rotation(math.radians(90 - f["facing"]), 4, "Z")
            @ Matrix.Translation((q["root"][0], q["root"][1], 0)) @ Matrix.Rotation(math.radians(q["yaw"]), 4, "Z")
            @ Matrix.Diagonal((s, s, s, 1.0)))
    up = Vector(q["spine"]).normalized()
    fw = Vector(q["chest"])
    fw = (fw - up * fw.dot(up)).normalized()
    lf = up.cross(fw)
    T3 = Matrix((fw, lf, up)).transposed()
    pelvis = Vector((0, 0, q["pelvis_z"]))
    neck = pelvis + up * 0.55
    head = neck + up * 0.15
    J = {}
    parts = {"torso": base @ Matrix.Translation(pelvis) @ T3.to_4x4(), "head": base @ Matrix.Translation(head)}
    for side, sg in (("r", -1), ("l", 1)):
        hip, sh = pelvis + lf * 0.1 * sg, pelvis + up * 0.48 + lf * 0.2 * sg
        knee, ank = ik(hip, Vector(q[side + "foot"]), 0.46, 0.46, fw + lf * 0.15 * sg)
        elb, wri = ik(sh, sh + Vector(q[side + "hand"]), 0.30, 0.30, T3 @ Vector((-0.3, 0.6 * sg, -1)))
        J.update({side + "hip": hip, side + "knee": knee, side + "ankle": ank, side + "sh": sh, side + "elbow": elb, side + "wrist": wri})
        parts[side + "thigh"], parts[side + "shin"] = base @ seg(hip, knee - hip), base @ seg(knee, ank - knee)
        parts[side + "upper"], parts[side + "fore"] = base @ seg(sh, elb - sh), base @ seg(elb, wri - elb)
        if f["weapons"].get({"r": "right", "l": "left"}[side]) and q[side + "blade"] is not None:
            bd = Vector(q[side + "blade"]).normalized()
            parts[side + "guard"] = base @ Matrix.Translation(wri + bd * 0.06)
            parts[side + "blade"] = base @ seg(wri + bd * 0.08, bd)
    if f.get("cloak"):
        parts["hood"] = base @ Matrix.Translation(head - fw * 0.025 + up * 0.01)
        parts["cloak"] = base @ Matrix.Translation(pelvis + up * 0.52 - fw * 0.15) @ T3.to_4x4()
    joints = [head + fw * 0.12, neck, J["rsh"], J["relbow"], J["rwrist"], J["lsh"], J["lelbow"], J["lwrist"],
              J["rhip"], J["rknee"], J["rankle"], J["lhip"], J["lknee"], J["lankle"],
              head + fw * 0.1 + up * 0.03 - lf * 0.045, head + fw * 0.1 + up * 0.03 + lf * 0.045, head - lf * 0.12, head + lf * 0.12]
    return parts, [base @ j for j in joints]


def duel_room(p):
    """The set: a .blend opened, a script run (it sees the duel file as DUEL; `call` names a function to run
    after it), or a plain floor. Returns the room's objects."""
    reset()
    room = p["spec"].get("room") or {}
    if room.get("blend"):
        bpy.ops.wm.open_mainfile(filepath=room["blend"])
    elif room.get("script"):
        g = {"__file__": room["script"], "__name__": "pw_duel_room", "DUEL": p["spec"]}
        with open(room["script"], encoding="utf-8") as fh:
            exec(compile(fh.read(), room["script"], "exec"), g)
        if room.get("call"):
            g[room["call"]]()
    else:
        floor = bpy.data.objects.new("pw_floor", make("pw_floor", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=15)))
        bpy.context.scene.collection.objects.link(floor)
    return [o for o in bpy.context.scene.objects if o.type in ("MESH", "CURVE", "SURFACE", "META", "FONT")]


def duel_camera(c):
    sc = bpy.context.scene
    if c.get("object"):
        cam = bpy.data.objects.get(c["object"])
        if cam is None or cam.type != "CAMERA":
            raise ValueError("no camera object %r in the room" % c["object"])
    else:
        cam = bpy.data.objects.new("pw_duel_cam", bpy.data.cameras.new("pw_duel_cam"))
        sc.collection.objects.link(cam)
        cam.location = Vector(c["pos"])
        cam.rotation_euler = (Vector(c["aim"]) - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.sensor_width = 36.0
    if c.get("lens"):
        cam.data.lens = float(c["lens"])
    cam.data.sensor_fit = "HORIZONTAL"
    sc.camera = cam
    return cam


def canny(g, lo, hi):
    """Edges (bool) of a grey image (rows top first, 0-255) as OpenCV's Canny after a 3x3 Gaussian: Sobel, L1
    magnitude, non-maximum suppression in four directions, hysteresis between lo and hi."""
    H, W = g.shape

    def conv(a, k):
        pad = np.pad(a, 1, mode="edge")
        return sum(k[i][j] * pad[i:i + H, j:j + W] for i in range(3) for j in range(3) if k[i][j])

    g = conv(g, [[1 / 16, 2 / 16, 1 / 16], [2 / 16, 4 / 16, 2 / 16], [1 / 16, 2 / 16, 1 / 16]])
    gx, gy = conv(g, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]), conv(g, [[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    mag = np.abs(gx) + np.abs(gy)
    ang = np.degrees(np.arctan2(gy, gx)) % 180
    pad = np.pad(mag, 1)
    nb = lambda dy, dx: pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]  # noqa: E731
    thin = np.zeros((H, W), bool)
    for a0, a1, dy, dx in ((0, 22.5, 0, 1), (157.5, 181, 0, 1), (22.5, 67.5, 1, 1), (67.5, 112.5, 1, 0), (112.5, 157.5, 1, -1)):
        thin |= (ang >= a0) & (ang < a1) & (mag > nb(dy, dx)) & (mag >= nb(-dy, -dx))
    weak, edges = thin & (mag >= lo), thin & (mag >= hi)
    for _ in range(2000):  # grow strong edges along weak ones until nothing changes
        e = np.pad(edges, 1)
        grown = weak & np.logical_or.reduce([e[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
        if (grown == edges).all():
            break
        edges = grown
    return edges


def canny_png(src, dst, factor, lo, hi):
    """Canny of a rendered PNG, shrunk by an integer factor first (an area average, as the clay is rendered large)."""
    img = bpy.data.images.load(src, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    g = (px.reshape(h, w, 4)[::-1, :, :3] @ np.array([0.299, 0.587, 0.114], np.float32)) * 255
    g = g[:h - h % factor, :w - w % factor].reshape(h // factor, factor, w // factor, factor).mean(axis=(1, 3))
    e = canny(g, lo, hi)[::-1].astype(np.float32)
    out = bpy.data.images.new("pw_canny", e.shape[1], e.shape[0])
    rgba = np.ones((e.size, 4), np.float32)
    rgba[:, :3] = e.reshape(-1, 1)
    out.pixels.foreach_set(rgba.ravel())
    out.filepath_raw, out.file_format = dst, "PNG"
    out.save()
    bpy.data.images.remove(out)


def act_duel(p):
    """Two (or more) posed fighters in a set, through the shot's camera, one PNG per frame and pass: depth (real
    blades), depth_thick (blades thick_blade_m square, so a far blade stays a bar), clay (Workbench at twice the
    size, fighters tinted) and its Canny, and COCO-18 joints in joints.json with face points turned from the lens
    left out. Poses come resolved per frame from pw.py."""
    from bpy_extras.object_utils import world_to_camera_view
    spec, poses = p["spec"], p["poses"]
    room = duel_room(p)
    sc = bpy.context.scene
    cam = duel_camera(spec["camera"])
    W, H = p["size"]
    fps, out, frames = int(p["fps"]), os.path.abspath(p["out"]), p["render"]
    figs = spec["fighters"]
    mesh = crowd_meshes(())
    mesh.update({"guard": make("pw_guard", sphere(0.05)), "hood": make("pw_hood", sphere(0.155, 12, 8)),
                 "cloak": make("pw_cloak", box(0.10, 0.62, 1.15, -1.15))})
    col = bpy.data.collections.new("pw_duel")
    sc.collection.children.link(col)
    objs = {}  # fighter -> part -> object
    for fn, f in figs.items():
        names = ["torso", "head"] + [s + n for s in "rl" for n in ("thigh", "shin", "upper", "fore")]
        for hand, length in f["weapons"].items():
            mesh["%s_%s" % (fn, hand)] = make("pw_blade", box(0.016, 0.006, length, -length))
            names += [hand[0] + "guard", hand[0] + "blade"]
        names += ["hood", "cloak"] if f.get("cloak") else []
        objs[fn] = {}
        for n in names:
            me = mesh["%s_%s" % (fn, {"r": "right", "l": "left"}[n[0]])] if n.endswith("blade") else mesh[n[1:] if n[1:] in mesh and n[0] in "rl" else n]
            o = bpy.data.objects.new("%s_%s" % (fn, n), me)
            col.objects.link(o)
            objs[fn][n] = o
    rest = {}

    def flown(fn, part, t, held):
        """A part in flight: from where it was at t0 to its mark on the floor, arcing and spinning; its lead part
        (the first listed) carries the others, so a hood stays on its cloak."""
        for i, x in enumerate(spec["fly"]):
            if x["fighter"] != fn or part not in x["parts"]:
                continue
            if t < x["t0"]:
                return held
            if i not in rest:
                rest[i] = duel_figure(figs[fn], x["pose_t0"])[0]
            m0, p0 = rest[i].get(part), rest[i][x["parts"][0]].to_translation()
            if m0 is None:
                return None
            u = min(1.0, (t - x["t0"]) / (x["t1"] - x["t0"]))
            e = u * u * (3 - 2 * u)
            rot = m0.to_quaternion().slerp(Quaternion((0, 1, 0), math.pi / 2) @ Quaternion((0, 0, 1), math.radians(x.get("land_yaw", 0))), e)
            if x.get("spin"):
                rot = Quaternion((0, 0, 1), 2 * math.pi * x["spin"] * e) @ rot
            end = Vector((x["to"][0], x["to"][1], x.get("rest_z", 0.05)))
            pos = p0.lerp(end, e) + Vector((0, 0, x.get("arc", 0.4) * math.sin(math.pi * u))) + (m0.to_translation() - p0) * (1 - e)
            return Matrix.Translation(pos) @ rot.to_matrix().to_4x4()
        return held

    def place(i, thick):
        joints = {}
        for fn, f in figs.items():
            parts, joints[fn] = duel_figure(f, poses[fn][i])
            for n, o in objs[fn].items():
                m = flown(fn, n, frames[i] / fps, parts.get(n))
                o.hide_render = m is None
                if m is not None:
                    o.matrix_world = m @ Matrix.Diagonal((thick / 0.016, thick / 0.006, 1, 1)) if thick and n.endswith("blade") else m
        bpy.context.view_layer.update()
        return joints

    sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = W, H, fps
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    if sc.world is None:
        sc.world = bpy.data.worlds.new("pw_world")
    depth_mat = depth_material(spec["near"], spec["far"])
    for d in ("depth", "depth_thick", "clay", "canny"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    for o in room:
        o.color = (0.75, 0.75, 0.75, 1)
    for fn, f in figs.items():
        for n, o in objs[fn].items():
            o.color = (0.95, 0.95, 0.95, 1) if n.endswith(("blade", "guard")) else tuple(f.get("tint", (0.6, 0.6, 0.6))[:3]) + (1,)
    cpos = cam.matrix_world.translation
    joints_out, in_frame = [], {fn: {} for fn in figs}
    t0 = time.time()
    for i, k in enumerate(frames):
        name = "%04d.png" % (k + 1)
        sc.render.resolution_percentage = 100
        J = place(i, 0)
        render_depth(os.path.join(out, "depth", name), depth_mat, p)
        people = []
        for fn, js in J.items():
            pj = [world_to_camera_view(sc, cam, v) for v in js]
            inside = sum(1 for q in pj if q.z > 0 and 0 <= q.x <= 1 and 0 <= q.y <= 1) / 18.0
            if i in (0, len(frames) - 1):
                in_frame[fn]["first" if i == 0 else "last"] = round(inside, 2)
            hide = set(hidden_face_points(js, cpos))
            people.append([round(sum(q.z for q in pj) / 18, 2),
                           [[round(q.x * W, 1), round((1 - q.y) * H, 1)] if q.z > 0.1 and j not in hide else [-1, -1] for j, q in enumerate(pj)]])
        people.sort(key=lambda q: -q[0])  # far first, so the near skeleton draws on top
        joints_out.append({"frame": k + 1, "people": people})
        sc.render.engine = "BLENDER_WORKBENCH"
        sc.render.resolution_percentage = 200  # clay large: a clean Canny after the shrink, and a sharp start frame
        sc.view_settings.view_transform = "Standard"
        sh = sc.display.shading
        sh.light, sh.color_type, sh.background_type = "STUDIO", "OBJECT", "WORLD"
        sh.show_cavity, sh.show_shadows, sh.show_object_outline = True, True, False
        sh.cavity_type, sh.cavity_ridge_factor, sh.cavity_valley_factor = "BOTH", 1.5, 1.5
        sc.world.color = (0, 0, 0)
        sc.render.filepath = os.path.join(out, "clay", name)
        bpy.ops.render.render(write_still=True)
        canny_png(os.path.join(out, "clay", name), os.path.join(out, "canny", name), 2, *spec["canny"])
        sc.render.resolution_percentage = 100
        place(i, spec["thick_blade_m"])
        render_depth(os.path.join(out, "depth_thick", name), depth_mat, p)
    with open(os.path.join(out, "joints.json"), "w", encoding="utf-8") as fh:
        json.dump({"size": [W, H], "frames": joints_out}, fh, separators=(",", ":"))
    with open(os.path.join(out, "camera.json"), "w", encoding="utf-8") as fh:
        json.dump({"lens_mm": cam.data.lens, "sensor_mm": cam.data.sensor_width, "size": [W, H], "fps": fps,
                   "matrix_world_rows": [round(v, 5) for row in cam.matrix_world for v in row]}, fh)
    if p.get("save_blend"):
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "duel.blend"))
    return {"out": out, "frames_rendered": len(frames), "in_frame": in_frame, "room_objects": len(room),
            "near_m": spec["near"], "far_m": spec["far"], "render_seconds": round(time.time() - t0, 1)}


# ---------------------------------------------------------------- video references from a generated mesh

TURN_AZ = {"front": 0, "3q": 45, "side": 90, "3q_back": 135, "back": 180, "3q_left": -45, "left": -90}


def srgb_to_linear(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def stand_up(objs, yaw=0.0, height_m=None, longest_m=None):
    """Parent everything to one root, turn it by yaw about +Z, scale to a height (or a longest side), stand it on
    z = 0 centred on the origin. Returns the root and the new bounds."""
    sc = bpy.context.scene
    root = bpy.data.objects.new("pw_root", None)
    sc.collection.objects.link(root)
    for o in list(sc.objects):
        if o.parent is None and o is not root and o.type != "CAMERA" and o.type != "LIGHT":
            o.parent = root
    root.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    lo, hi = bounds(objs)
    ext = [hi[i] - lo[i] for i in range(3)]
    s = (longest_m / max(max(ext), 1e-9)) if longest_m else (height_m / max(ext[2], 1e-9)) if height_m else 1.0
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    lo, hi = bounds(objs)
    root.location = Vector((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
    bpy.context.view_layer.update()
    lo, hi = bounds(objs)
    return root, Vector(lo), Vector(hi), s


def grey_studio(grey=0.5, light=1.0):
    """Flat light: a white world lights the model, a mid-grey world is what the camera sees behind it."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("pw_grey")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    lp, lit, bg = nt.nodes.new("ShaderNodeLightPath"), nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeBackground")
    lit.inputs["Color"].default_value = (1, 1, 1, 1)
    lit.inputs["Strength"].default_value = light
    g = srgb_to_linear(grey)
    bg.inputs["Color"].default_value = (g, g, g, 1)
    mix, out = nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(lit.outputs[0], mix.inputs[1])
    nt.links.new(bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])


def act_turnaround(p):
    """Eye-level perspective views of a textured model on flat mid-grey, for a video model's reference pictures
    (MiniMax H3 --ref, Wan or Kling references): long lens, shadowless light, Cycles on the CPU."""
    objs = load(p["file"])
    if not objs:
        raise ValueError("no mesh objects to render")
    _, lo, hi, s = stand_up(objs, p.get("yaw", 0.0), p.get("height_m"))
    ext = hi - lo
    grey_studio(p.get("grey", 0.5))
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU" if p.get("gpu") else "CPU"
    sc.cycles.samples = int(p.get("samples", 48))
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    W, H = (int(v) for v in p.get("size", [768, 1152]))
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    lens = float(p.get("lens", 85))
    cam_data = bpy.data.cameras.new("pw_cam")
    cam_data.lens, cam_data.sensor_fit, cam_data.sensor_width = lens, "AUTO", 36
    cam = bpy.data.objects.new("pw_cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    long_side = 18.0 / lens  # tan of half the field of view across the longer image side
    tan_v = long_side * (min(W, H) / max(W, H) if W > H else 1.0)
    tan_h = long_side * (min(W, H) / max(W, H) if H > W else 1.0)
    foot = math.hypot(ext.x, ext.y)
    dist = max(ext.z / 2 / tan_v, foot / 2 / tan_h) * float(p.get("margin", 1.12)) + foot / 2
    cam_data.clip_start, cam_data.clip_end = dist / 100, dist * 10
    centre = Vector((0, 0, ext.z / 2))
    el = math.radians(float(p.get("elev", 4.0)))
    os.makedirs(p["out"], exist_ok=True)
    shots = []
    for v in p.get("views", ["front", "3q", "side", "back"]):
        if v not in TURN_AZ:
            raise ValueError("unknown view %s (known: %s)" % (v, ", ".join(TURN_AZ)))
        az = math.radians(TURN_AZ[v])
        d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        cam.location = centre + d * dist
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(p["out"], "view_%s.png" % v)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        shots.append({"view": v, "path": path, "azimuth_deg": TURN_AZ[v]})
    res = {"shots": shots, "dims_m": [round(x, 5) for x in ext], "scale": s, "lens": lens, "size": [W, H]}
    if p.get("sheet", True) and len(shots) > 1 and np is not None:
        res["sheet"] = stitch([x["path"] for x in shots], os.path.join(p["out"], "sheet.png"), len(shots))
    return res


def rgb_to_hsv_np(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-9), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    dd = np.maximum(d, 1e-9)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) / 6.0
    h = np.where(d > 0, h, 0)
    return np.stack([h % 1.0, s, mx], -1)


def hsv_to_rgb_np(hsv):
    h, s, v = hsv[..., 0] * 6.0, hsv[..., 1], hsv[..., 2]
    i = np.floor(h).astype(np.int32) % 6
    f = h - np.floor(h)
    pp, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    choices = [(v, t, pp), (q, v, pp), (pp, v, t), (pp, q, v), (t, pp, v), (v, pp, q)]
    out = np.zeros(hsv.shape, dtype=np.float32)
    for k, (r, g, b) in enumerate(choices):
        m = i == k
        out[..., 0][m], out[..., 1][m], out[..., 2][m] = r[m], g[m], b[m]
    return out


def base_colour_nodes(objs):
    """The image texture node feeding each material's Principled Base Color (through mix nodes)."""
    found = []
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.use_nodes:
                continue
            bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            node = bsdf.inputs["Base Color"].links[0].from_node if bsdf and bsdf.inputs["Base Color"].links else None
            while node is not None and node.type != "TEX_IMAGE":
                ins = [l.from_node for i in node.inputs for l in i.links]
                node = ins[0] if ins else None
            if node is not None and node.image is not None and node not in found:
                found.append(node)
    return found


def head_front_mask(objs, img_w, img_h, head_frac, front_dot):
    """Texels inside the UV triangles of front-facing (-Y) faces in the top head_frac of the model."""
    lo, hi = bounds(objs)
    top = hi[2] - head_frac * (hi[2] - lo[2])
    mask = np.zeros((img_h, img_w), dtype=bool)
    tris = 0
    for o in objs:
        me = o.data
        uvl = me.uv_layers.active
        if uvl is None:
            continue
        me.calc_loop_triangles()
        mw = o.matrix_world
        rot = mw.to_3x3()
        for lt in me.loop_triangles:
            c = mw @ Vector(lt.center)
            n = (rot @ Vector(lt.normal)).normalized()
            if c.z < top or -n.y < front_dot:
                continue
            tris += 1
            uv = np.array([uvl.data[li].uv[:] for li in lt.loops]) * [img_w, img_h]
            x0, y0 = np.floor(uv.min(0)).astype(int)
            x1, y1 = np.ceil(uv.max(0)).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, img_w - 1), min(y1, img_h - 1)
            if x1 < x0 or y1 < y0:
                continue
            ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            (ax, ay), (bx, by), (cx, cy) = uv
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-12:
                continue
            px, py = xs + 0.5, ys + 0.5
            w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
            w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
            inside = (w0 >= -0.02) & (w1 >= -0.02) & (w0 + w1 <= 1.02)
            mask[y0:y1 + 1, x0:x1 + 1] |= inside
    return mask, tris


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def fix_base_colour(objs, p, out_png):
    """Recolour the plastic toward measured photo values and erase a smeared painted marking on the head front,
    on the base colour image; saves it as out_png and swaps it into the materials."""
    nodes = base_colour_nodes(objs)
    if not nodes:
        return {"skipped": "no base colour texture"}
    img = nodes[0].image
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    rgb = px[..., :3].copy()
    res = {"size": [w, h]}
    er = p.get("erase")
    if er:
        region, tris = head_front_mask(objs, w, h, float(p.get("head_frac", 0.13)), float(p.get("front_dot", 0.5)))
        hsv = rgb_to_hsv_np(rgb)
        if er == "white":
            mark = (rgb.min(-1) > 0.55) & (hsv[..., 1] < 0.3)
        elif er == "red":
            mark = ((hsv[..., 0] < 0.06) | (hsv[..., 0] > 0.92)) & (hsv[..., 1] > 0.35) & (hsv[..., 2] > 0.2)
        else:
            raise ValueError("--erase takes white or red")
        hit = dilate(mark & region, 3) & region
        rest = region & ~hit
        fill = np.median(rgb[rest], 0) if rest.any() else np.array([0.1, 0.1, 0.1], dtype=np.float32)
        rgb[hit] = fill
        res["erase"] = {"head_triangles": tris, "region_px": int(region.sum()), "erased_px": int(hit.sum()),
                        "fill_rgb": [round(float(x) * 255) for x in fill]}
    rc = p.get("recolour")
    if rc:
        hsv = rgb_to_hsv_np(rgb)
        lo_h, hi_h = rc.get("from_hue", [0.0, 1.0])
        m = (hsv[..., 1] > rc.get("min_sat", 0.12)) & (hsv[..., 2] > rc.get("min_val", 0.0)) & \
            (hsv[..., 0] >= lo_h) & (hsv[..., 0] <= hi_h)
        if m.any():
            ms, mv = float(np.median(hsv[..., 1][m])), float(np.median(hsv[..., 2][m]))
            hsv[..., 0][m] = rc["hue"]
            if rc.get("sat") is not None:
                hsv[..., 1][m] = np.clip(hsv[..., 1][m] * rc["sat"] / max(ms, 1e-6), 0, 1)
            if rc.get("val") is not None:
                hsv[..., 2][m] = np.clip(hsv[..., 2][m] * rc["val"] / max(mv, 1e-6), 0, 1)
            rgb = hsv_to_rgb_np(hsv)
            res["recolour"] = {"texels": int(m.sum()), "from_median_sat_val": [round(ms, 3), round(mv, 3)]}
        else:
            res["recolour"] = {"texels": 0, "note": "no texel matched --from-hue/--min-sat/--min-val"}
    px[..., :3] = rgb
    new = bpy.data.images.new("pw_basecolour", w, h, alpha=True)
    new.pixels.foreach_set(px.ravel())
    new.filepath_raw = out_png
    new.file_format = "PNG"
    new.save()
    saved = bpy.data.images.load(out_png)
    for n in nodes:
        n.image = saved
    res["texture"] = out_png
    return res


def act_mark(p):
    """Finish a generated figure for video: fix its base colour, put a clean painted marking (a letter or number)
    on the head's front face as a thin text mesh, scale it to real size, export."""
    objs = load(p["file"])
    if not objs:
        raise ValueError("no mesh objects")
    res = {}
    out = p["out"]
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    if p.get("recolour") or p.get("erase"):
        res["texture"] = fix_base_colour(objs, p, os.path.splitext(out)[0] + "_basecolor.png")
    _, lo, hi, s = stand_up(objs, p.get("yaw", 0.0), p.get("height_m"), p.get("longest_m"))
    res["dims_m"] = [round(v, 5) for v in hi - lo]
    res["scale"] = s
    text = p.get("text")
    if text:
        sc = bpy.context.scene
        deps = bpy.context.evaluated_depsgraph_get()
        H = hi.z - lo.z
        top = hi.z - float(p.get("head_frac", 0.13)) * H
        hits, N = [], 41
        for i in range(N):
            for j in range(N):
                o = Vector((lo.x + (hi.x - lo.x) * i / (N - 1), lo.y - 1, top + (hi.z - top) * j / (N - 1)))
                ok, loc, nrm, _, _, _ = sc.ray_cast(deps, o, Vector((0, 1, 0)))
                if ok and nrm.y < -0.7:
                    hits.append(loc.copy())
        if len(hits) < 10:
            raise ValueError("head front not found (%d ray hits): check --yaw (the face must look at -Y) and --head-frac" % len(hits))
        yf = sorted(hh.y for hh in hits)[len(hits) // 2]
        face = [hh for hh in hits if abs(hh.y - yf) < 0.04 * H]  # the flat front, not the jaw or neck
        k = max(1, len(face) // 40)
        xs, zs = sorted(hh.x for hh in face), sorted(hh.z for hh in face)
        x0, x1, z0, z1 = xs[k], xs[-k - 1], zs[k], zs[-k - 1]
        yfront = sorted(hh.y for hh in face)[len(face) // 50]  # the most forward part, so no stroke sinks in
        fw, fh = x1 - x0, z1 - z0
        curve = bpy.data.curves.new("pw_mark", "FONT")
        curve.body = text
        if p.get("font"):
            try:
                curve.font = bpy.data.fonts.load(p["font"])
            except Exception as e:
                res["font_error"] = str(e)[:120]
        curve.align_x, curve.align_y = "CENTER", "CENTER"
        curve.extrude = 0.02
        txt = bpy.data.objects.new("pw_mark", curve)
        sc.collection.objects.link(txt)
        select_only([txt], txt)
        bpy.ops.object.convert(target="MESH")
        txt = bpy.context.active_object
        vs = [v.co.copy() for v in txt.data.vertices]
        tx0, tx1 = min(v.x for v in vs), max(v.x for v in vs)
        ty0, ty1 = min(v.y for v in vs), max(v.y for v in vs)
        for v in txt.data.vertices:
            v.co.x -= (tx0 + tx1) / 2
            v.co.y -= (ty0 + ty1) / 2
        tw, th = tx1 - tx0, ty1 - ty0
        sz = min(float(p.get("text_frac", 0.75)) * fh / th, float(p.get("width_frac", 0.92)) * fw / tw)
        txt.scale = (sz, sz, sz * 0.5)
        txt.rotation_euler = (math.radians(90), 0, 0)
        gap = 0.003 * H
        txt.location = Vector(((x0 + x1) / 2 + float(p.get("text_dx", 0)) * fw, yfront - gap - 0.01 * sz,
                               (z0 + z1) / 2 + float(p.get("text_dz", 0)) * fh))
        mat = bpy.data.materials.new("pw_mark_paint")
        mat.use_nodes = True
        col = [srgb_to_linear(float(c)) for c in p.get("colour", [0.95, 0.95, 0.95])]
        bs = mat.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = col + [1]
        bs.inputs["Roughness"].default_value = 0.6
        txt.data.materials.append(mat)
        res["mark"] = {"text": text, "face_m": [round(fw, 5), round(fh, 5)], "letter_h_m": round(th * sz, 5),
                       "ray_hits": len(face)}
    res["export"] = export(out, {})
    return res


def act_lineup(p):
    """A few generated figures stood on a table with teams on fixed sides, and its control passes for a video
    model: colour (textured, Cycles CPU), clay (Workbench), inverse depth (near white, one range), team mask."""
    L = p["layout"]
    out = p["out"]
    os.makedirs(out, exist_ok=True)
    reset()
    sc = bpy.context.scene
    W, H = L.get("size", [864, 480])
    if p.get("preview"):
        W, H = W // 2, H // 2
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "Standard"
    figs = []
    for f in L["figures"]:
        before = set(sc.objects)
        ext = os.path.splitext(f["file"])[1].lower()
        if ext not in IMPORTERS:
            raise ValueError("cannot import %s" % f["file"])
        IMPORTERS[ext](f["file"])
        new = [o for o in sc.objects if o not in before]
        root = bpy.data.objects.new("fig_" + f["name"], None)
        sc.collection.objects.link(root)
        for o in new:
            if o.parent is None:
                o.parent = root
        meshes = [o for o in new if o.type == "MESH"]
        face = str(f.get("face", "+x"))
        heading = {"+x": 90.0, "-x": -90.0, "-y": 0.0, "+y": 180.0}.get(face)
        heading = float(face) if heading is None else heading
        root.rotation_euler = (0, 0, math.radians(float(f.get("yaw", 0.0)) + heading))
        bpy.context.view_layer.update()
        lo, hi = bounds(meshes)
        s = float(f.get("height_m", 0.13)) / max(hi[2] - lo[2], 1e-9)
        root.scale = (s, s, s)
        bpy.context.view_layer.update()
        lo, hi = bounds(meshes)
        x, y = f["at"]
        root.location = Vector((x - (lo[0] + hi[0]) / 2, y - (lo[1] + hi[1]) / 2, -lo[2]))
        bpy.context.view_layer.update()
        figs.append({"cfg": f, "root": root, "meshes": meshes})
    T = L.get("table", {})
    ts = float(T.get("size_m", 1.6))

    def plane(name, loc, rot, colour):
        bpy.ops.mesh.primitive_plane_add(size=ts, location=loc, rotation=rot)
        ob = bpy.context.active_object
        ob.name = name
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = [srgb_to_linear(c) for c in colour] + [1]
        ob.data.materials.append(m)
        return ob

    table = plane("table", (0, 0, 0), (0, 0, 0), T.get("colour", [0.62, 0.45, 0.30]))
    back = None
    if L.get("backdrop_m"):
        back = plane("backdrop", (0, L["backdrop_m"], ts / 2), (math.pi / 2, 0, 0), L.get("backdrop_colour", [0.76, 0.74, 0.70]))
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens, cam_data.sensor_fit, cam_data.sensor_width = float(L.get("lens", 35)), "HORIZONTAL", 36
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = Vector(L["cam"])
    cam.rotation_euler = (Vector(L["aim"]) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.clip_start, cam_data.clip_end = 0.01, 50
    bpy.context.view_layer.update()
    R = cam.matrix_world.to_3x3()
    fwd = R @ Vector((0, 0, -1))
    bottom = R @ Vector((0, -(H / 2) / (W * cam_data.lens / 36.0), -1.0))
    near = 0.05
    if bottom.z < 0:
        near = max(0.02, (bottom * (-cam.location.z / bottom.z)).dot(fwd) * 0.9)
    far = max((fg["root"].location - cam.location).dot(fwd) for fg in figs) * 1.6
    if back is not None:
        far = max(far, (Vector((0, L["backdrop_m"], cam.location.z)) - cam.location).dot(fwd) * 1.05)
    from bpy_extras.object_utils import world_to_camera_view
    boxes = {}
    for fg in figs:
        lo, hi = bounds(fg["meshes"])
        pts = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        uv = [world_to_camera_view(sc, cam, q) for q in pts]
        boxes[fg["cfg"]["name"]] = [round(min(q.x for q in uv) * W), round((1 - max(q.y for q in uv)) * H),
                                    round(max(q.x for q in uv) * W), round((1 - min(q.y for q in uv)) * H)]

    def emission(name, colour=(1, 1, 1), depth=False):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        em, on = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
        em.inputs["Color"].default_value = list(colour) + [1]
        if depth:
            cd, inv, mr = nt.nodes.new("ShaderNodeCameraData"), nt.nodes.new("ShaderNodeMath"), nt.nodes.new("ShaderNodeMapRange")
            inv.operation = "DIVIDE"
            inv.inputs[0].default_value = 1.0
            nt.links.new(cd.outputs["View Z Depth"], inv.inputs[1])
            mr.clamp = True
            mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 1.0 / far, 1.0 / near
            nt.links.new(inv.outputs[0], mr.inputs["Value"])
            nt.links.new(mr.outputs["Result"], em.inputs["Strength"])
        nt.links.new(em.outputs[0], on.inputs["Surface"])
        return m

    def world(colour, strength):
        w = bpy.data.worlds.new("w")
        w.use_nodes = True
        bgn = w.node_tree.nodes["Background"]
        bgn.inputs["Color"].default_value, bgn.inputs["Strength"].default_value = list(colour) + [1], strength
        sc.world = w

    everything = [o for fg in figs for o in fg["meshes"]] + [table] + ([back] if back else [])
    team = {o.name: fg["cfg"].get("team", "a") for fg in figs for o in fg["meshes"]}

    def override(mat_for):
        for o in everything:
            m = mat_for(o)
            if not o.material_slots:
                o.data.materials.append(m)
            for slot in o.material_slots:
                slot.link, slot.material = "OBJECT", m

    def restore():
        for o in everything:
            for slot in o.material_slots:
                slot.link = "DATA"

    def render(name):
        path = os.path.join(out, name + ".png")
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        return path

    passes = {}
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type, sh.single_color = "STUDIO", "SINGLE", (0.6, 0.6, 0.6)
    world((0.05, 0.05, 0.05), 1)
    passes["clay"] = render("clay")
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples, sc.cycles.use_denoising = 1, False
    sc.render.filter_size = 0.01  # hard edges: one sample of flat emission is exact
    world((0, 0, 0), 0)
    dmat = emission("pw_depth", depth=True)
    override(lambda o: dmat)
    passes["depth"] = render("depth")
    if not p.get("preview"):
        mats = {"a": emission("pw_team_a", (1, 0, 0)), "b": emission("pw_team_b", (0, 0, 1)), None: emission("pw_none", (0, 0, 0))}
        override(lambda o: mats[team.get(o.name)])
        passes["mask"] = render("mask")
    restore()
    sc.render.filter_size = 1.5
    if not p.get("preview"):
        sc.cycles.samples, sc.cycles.use_denoising = int(p.get("samples", 64)), True
        world((0.9, 0.92, 1.0), 0.35)
        key = bpy.data.objects.new("key", bpy.data.lights.new("key", "AREA"))
        key.data.energy, key.data.size, key.data.color = 6.0 * (cam.location.length / 0.5) ** 2, 0.8, (1.0, 0.93, 0.82)
        key.location = cam.location + Vector((-0.4, -0.2, 0.7))
        key.rotation_euler = (Vector((0, 0, 0.06)) - key.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(key)
        passes["colour"] = render("colour")
    res = {"size": [W, H], "lens": cam_data.lens, "cam": [round(v, 4) for v in cam.location], "aim": L["aim"],
           "near_m": round(near, 4), "far_m": round(far, 4), "depth": "inverse 1/z from 1/far (black) to 1/near (white)",
           "boxes_px": boxes, "passes": passes}
    with open(os.path.join(out, "lineup.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    return res


ACTIONS = {"inspect": act_inspect, "render": act_render, "match": act_match, "convert": act_convert,
           "printable": act_printable, "union": act_union, "crowd": act_crowd, "duel": act_duel, "turnaround": act_turnaround,
           "mark": act_mark, "lineup": act_lineup}


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
