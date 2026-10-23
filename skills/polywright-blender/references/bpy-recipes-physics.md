# bpy recipes for physics, rigs and volumes (Blender 5.2)

Rigid-body and cloth bakes, why a Rigify rig is not a game skeleton, and volume remeshing. Back to
[SKILL.md](../SKILL.md); also [bpy-recipes.md](bpy-recipes.md) and [bpy-recipes-scenes.md](bpy-recipes-scenes.md).
Every block is run by `tests/test_recipes.py` in Blender 5.2.1, asserts its own result and prints
`[pw] ok ...`. Ideas credited to the books they came from; the code is new.

## Rigid bodies, baked headless

Falling debris or a toppled wall for a set piece. Apply scale first and put each origin at the centre of mass,
or collisions misbehave and bodies drift (after Pearson, *Learn Blender Simulations the Right Way*, rigid bodies).
Bake before rendering, with the cache next to the `.blend`, not in the temporary folder.

```python
# recipe: rigidbody-bake
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.frame_end = 60
bpy.ops.mesh.primitive_plane_add(size=10); bpy.ops.rigidbody.object_add(type="PASSIVE")
bpy.context.active_object.rigid_body.collision_shape = "BOX"      # a flat floor: the default hull lets bodies through
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 3)); box = bpy.context.active_object
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)  # all three default to True:
# applying location too moves the origin (the centre of mass) to the world origin, inside the floor
bpy.ops.rigidbody.object_add(type="ACTIVE")
sc.rigidbody_world.point_cache.frame_end = sc.frame_end           # the cache has its own range (250 by default)
with bpy.context.temp_override(scene=sc, point_cache=sc.rigidbody_world.point_cache):
    bpy.ops.ptcache.bake(bake=True)
sc.frame_set(60); z = box.matrix_world.translation.z
assert 0.2 < z < 0.3, z                                           # resting on the floor: half its size up
print("[pw] ok rigid body rests at z %.3f" % z)
```

## Pinned cloth, baked headless

Banners and cloaks: a pin vertex group holds one edge, the Cloth modifier comes before Subdivision, never after
(after Pearson, the cloth chapters; *Squeaky Clean Topology in Blender* wants even, near-square quads for cloth).

```python
# recipe: cloth-bake
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.frame_end = 30
bpy.ops.mesh.primitive_grid_add(x_subdivisions=20, y_subdivisions=20, size=1, location=(0, 0, 2))
flag = bpy.context.active_object
pin = flag.vertex_groups.new(name="pin")
pin.add([v.index for v in flag.data.vertices if v.co.y > 0.49], 1.0, "REPLACE")  # one edge
cloth = flag.modifiers.new("cloth", "CLOTH"); cloth.settings.vertex_group_mass = "pin"
flag.modifiers.new("smooth", "SUBSURF")                            # after the cloth
with bpy.context.temp_override(scene=sc, active_object=flag, point_cache=cloth.point_cache):
    bpy.ops.ptcache.bake(bake=True)
sc.frame_set(30)
me = flag.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
zs = [(flag.matrix_world @ v.co).z for v in me.vertices]
assert min(zs) < 1.8 and max(zs) > 1.99, (min(zs), max(zs))       # it hangs from the pinned edge
print("[pw] ok cloth lowest z %.2f, pinned edge %.2f" % (min(zs), max(zs)))
```

## A Rigify rig is not a game skeleton

Rigify builds a full animation rig in one call (after *Blender 3D By Example*, Rigify), but its export keeps far
more bones than the deform set: the deform bones' non-deform parents come along even with
`use_armature_deform_only`. Unity Humanoid, Roblox and a Madness `Character_Ref` want a deform-only hierarchy:
build one from the DEF bones, or start from the plain metarig, Mixamo or AccuRIG.

```python
# recipe: rigify-export
import bpy, importlib.util, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
if importlib.util.find_spec("addon_utils") is None:               # the bpy module from PyPI ships no add-ons
    print("[pw] ok rigify skipped: needs the Blender app (bundled Rigify add-on)")
else:
    import addon_utils
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("rigify", default_set=True)
    bpy.ops.object.armature_human_metarig_add(); meta = bpy.context.active_object
    bpy.ops.pose.rigify_generate()
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE" and o is not meta)
    deform, total = sum(1 for b in rig.data.bones if b.use_deform), len(rig.data.bones)
    for o in bpy.context.scene.objects:
        o.select_set(o is rig)
    bpy.context.view_layer.objects.active = rig
    path = os.path.join(OUT, "rig.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE"},
                             use_armature_deform_only=True, add_leaf_bones=False)
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=path)
    back = sum(len(o.data.bones) for o in bpy.data.objects if o.type == "ARMATURE")
    assert back > deform, (back, deform)                          # the caveat: more than the deform set
    print("[pw] ok rigify", total, "bones,", deform, "deform,", back, "after a deform-only FBX export")
```

## Volume remesh and smooth merge (prints)

Mesh to Volume then Volume to Mesh rebuilds one closed surface at a chosen voxel size: overlapping parts merge
and gaps under the voxel close (after the Geometry Nodes book, the volume chapters). Keep the exterior band at
its default; a wider band grows the result.

```python
# recipe: volume-remesh
import bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1); a = bpy.context.active_object
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(1.2, 0, 0)); b = bpy.context.active_object
for o in (a, b): o.select_set(True)
bpy.context.view_layer.objects.active = a; bpy.ops.object.join()  # two overlapping shells, one object
ng = bpy.data.node_groups.new("volume_remesh", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
m2v, v2m = ng.nodes.new("GeometryNodeMeshToVolume"), ng.nodes.new("GeometryNodeVolumeToMesh")
m2v.inputs["Voxel Size"].default_value = 0.05                    # adapt: smaller keeps more detail
ng.links.new(gi.outputs[0], m2v.inputs["Mesh"]); ng.links.new(m2v.outputs[0], v2m.inputs["Volume"])
ng.links.new(v2m.outputs[0], go.inputs[0])
mod = a.modifiers.new("remesh", "NODES"); mod.node_group = ng
bpy.ops.object.modifier_apply(modifier=mod.name)
bm = bmesh.new(); bm.from_mesh(a.data)
open_edges = sum(1 for e in bm.edges if not e.is_manifold)
seen, parts = set(), 0
for v in bm.verts:                                                 # connected pieces
    if v in seen:
        continue
    parts += 1; stack = [v]; seen.add(v)
    while stack:
        for e in stack.pop().link_edges:
            for w in e.verts:
                if w not in seen:
                    seen.add(w); stack.append(w)
assert open_edges == 0 and parts == 1, (open_edges, parts)
print("[pw] ok volume remesh", len(bm.faces), "faces, one closed piece")
```
