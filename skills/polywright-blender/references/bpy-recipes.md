# bpy recipes (Blender 5.2)

Self-contained scripts for jobs `pw.py` does not wrap. Back to [SKILL.md](../SKILL.md). Every block below is
run by `tests/test_recipes.py` in Blender 5.2.1 (last run recorded in TESTS.md); each builds its own test
geometry, writes to the folder in `PW_OUT` (default: the temp folder) and prints `[pw] ok ...` when it works.
Run one with `pw.py bpy recipe.py`; adapt the marked lines to your scene.

## Reference images at real scale

```python
# recipe: reference-images
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
img_path = os.path.join(OUT, "ref_front.png")                     # adapt: your reference image
img = bpy.data.images.new("ref_front", 512, 256)
img.filepath_raw, img.file_format = img_path, "PNG"
img.save()
REAL_WIDTH_M = 1.8                                                # adapt: what the image's full width shows
ref = bpy.data.objects.new("REF_front", None)
ref.empty_display_type = "IMAGE"
ref.data = bpy.data.images.load(img_path)
ref.empty_display_size = REAL_WIDTH_M                            # an image empty's size is its width
ref.rotation_euler = (1.5708, 0, 0)                               # stand it up, facing -Y (Blender's front)
ref.location = (0, 1.0, REAL_WIDTH_M * 256 / 512 / 2)             # behind the model, bottom on the ground
ref.empty_image_depth = "BACK"
ref.color[3] = 0.4                                                # opacity
bpy.context.scene.collection.objects.link(ref)
print("[pw] ok reference empty", ref.name, "width", ref.empty_display_size)
```

Side and top references: rotate to face +X (`(1.5708, 0, 1.5708)`) or lie flat (`(0, 0, 0)`). `pw.py render`
reports `metres_per_px` for orthographic shots, so a rendered blockout can be matched to a reference the same way.

## Modifiers, applied safely

```python
# recipe: modifiers-apply
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1)
obj = bpy.context.active_object
bev = obj.modifiers.new("bevel", "BEVEL"); bev.width = 0.03; bev.segments = 3; bev.limit_method = "ANGLE"
wn = obj.modifiers.new("wn", "WEIGHTED_NORMAL"); wn.keep_sharp = True
for m in list(obj.modifiers):
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=m.name)
print("[pw] ok modifiers applied, faces", len(obj.data.polygons))
```

## Boolean with Manifold, EXACT fallback

```python
# recipe: boolean-fallback
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2); base = bpy.context.active_object
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=3); cutter = bpy.context.active_object
def bounds(o):
    xs = [(o.matrix_world @ v.co) for v in o.data.vertices]
    return [min(v[i] for v in xs) for i in range(3)], [max(v[i] for v in xs) for i in range(3)]
before = len(base.data.polygons)
for solver in ("MANIFOLD", "EXACT"):
    m = base.modifiers.new("cut", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = cutter; m.solver = solver
    with bpy.context.temp_override(object=base, active_object=base, selected_objects=[base]):
        bpy.ops.object.modifier_apply(modifier=m.name)
    if len(base.data.polygons) != before:      # adapt: for a UNION compare bounds with the operands' instead
        break
cutter.hide_render = cutter.hide_viewport = True
print("[pw] ok boolean with", solver, "faces", len(base.data.polygons))
```

## Voxel remesh, then quads

```python
# recipe: remesh-quads
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(); obj = bpy.context.active_object
r = obj.modifiers.new("vox", "REMESH"); r.mode = "VOXEL"; r.voxel_size = 0.04
with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
    bpy.ops.object.modifier_apply(modifier=r.name)
closed = len(obj.data.polygons)
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
res = bpy.ops.object.quadriflow_remesh(target_faces=1500, use_preserve_sharp=True)
print("[pw] ok voxel faces", closed, "quadriflow", res, "faces", len(obj.data.polygons))
```

QuadriFlow fails on non-manifold input, so voxel-remesh first. For production characters, retopologise by hand
or with Quad Remesher (paid).

## UVs: Smart UV and a lightmap set

```python
# recipe: uvs
import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_torus_add(); obj = bpy.context.active_object
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
obj.data.uv_layers.new(name="Lightmap"); obj.data.uv_layers.active_index = 1
bpy.ops.uv.lightmap_pack(PREF_MARGIN_DIV=0.2)
bpy.ops.object.mode_set(mode="OBJECT")
obj.data.uv_layers.active_index = 0
print("[pw] ok uv layers", [u.name for u in obj.data.uv_layers])
```

## Bake normal and AO from high to low (Cycles)

```python
# recipe: bake-high-to-low
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.device = "CPU"
bpy.ops.mesh.primitive_monkey_add(); high = bpy.context.active_object
s = high.modifiers.new("sub", "SUBSURF"); s.levels = 2
bpy.ops.mesh.primitive_monkey_add(); low = bpy.context.active_object      # adapt: your low-poly with UVs
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(island_margin=0.02); bpy.ops.object.mode_set(mode="OBJECT")
img = bpy.data.images.new("low_normal", 512, 512, float_buffer=False)
img.colorspace_settings.name = "Non-Color"
mat = bpy.data.materials.new("low"); low.data.materials.append(mat)
nt = mat.node_tree; tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
nt.nodes.active = tex                                                       # the bake target is the active node
for o in sc.objects: o.select_set(False)
high.select_set(True); low.select_set(True); bpy.context.view_layer.objects.active = low
bpy.ops.object.bake(type="NORMAL", use_selected_to_active=True, cage_extrusion=0.05, normal_space="TANGENT", margin=8)
img.filepath_raw = os.path.join(OUT, "low_normal.png"); img.file_format = "PNG"; img.save()
print("[pw] ok baked", img.filepath_raw)
```

Blender bakes OpenGL (Y+) normals: right for Blender, Unity, glTF, three.js and Roblox; flip green for Unreal.
For AO use `type="AO"`; for colour without lighting `type="DIFFUSE", pass_filter={"COLOR"}`.

## A material with 5.x socket names

```python
# recipe: material-5x
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
mat = bpy.data.materials.new("granite")
bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.53, 1)
bsdf.inputs["Roughness"].default_value = 0.8
bsdf.inputs["Specular IOR Level"].default_value = 0.4    # was "Specular"
bsdf.inputs["Coat Weight"].default_value = 0.0           # was "Clearcoat"
bsdf.inputs["Emission Strength"].default_value = 0.0     # with "Emission Color", was "Emission"
print("[pw] ok material sockets", len(bsdf.inputs))
```

## Turntable stills

```python
# recipe: turntable
import bpy, math, os, tempfile
from mathutils import Vector
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(); obj = bpy.context.active_object       # adapt: your object
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
sc.render.resolution_x = sc.render.resolution_y = 256
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
center = sum((obj.matrix_world @ Vector(c) for c in obj.bound_box), Vector()) / 8
dist = max(obj.dimensions) * 2.2
paths = []
for i in range(8):
    a = math.radians(i * 45)
    cam.location = center + Vector((math.sin(a) * dist, -math.cos(a) * dist, dist * 0.35))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "turn_%02d.png" % i)
    bpy.ops.render.render(write_still=True); paths.append(sc.render.filepath)
print("[pw] ok turntable frames", len(paths))
```

For video, keyframe the camera on a circle instead and render an animation, or hand the stills to the video
plugin as references.

## Depth and normal passes (AI video conditioning)

```python
# recipe: video-passes
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(); bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -1))
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = 320, 180
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -6, 1.5); cam.rotation_euler = (1.35, 0, 0)
vl = sc.view_layers[0]; vl.use_pass_z = True; vl.use_pass_normal = True; vl.use_pass_mist = True
sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"         # 5.x: set the media type first,
sc.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"      # then the format (the only one it allows)
sc.render.filepath = os.path.join(OUT, "passes.exr")
bpy.ops.render.render(write_still=True)
print("[pw] ok passes", sc.render.filepath, os.path.getsize(sc.render.filepath))
```

The multilayer EXR holds Depth, Normal and Mist; most video tools want 8- or 16-bit PNGs, so normalise depth
(near white, far black for most depth ControlNets) when converting.

## Exports per engine

```python
# recipe: exports
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(); obj = bpy.context.active_object
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "web.glb"), export_format="GLB", export_apply=True,
                          export_meshopt_compression_enable=True)                  # web: meshopt (or Draco)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "unity.fbx"), apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                         use_mesh_modifiers=True, path_mode="COPY", embed_textures=True)  # Unity, no -90 X root
bpy.ops.wm.usd_export(filepath=os.path.join(OUT, "ar.usdz"))                       # Apple AR Quick Look
bpy.ops.wm.stl_export(filepath=os.path.join(OUT, "print.stl"), global_scale=1000.0) # metres to millimetres
sizes = {f: os.path.getsize(os.path.join(OUT, f)) for f in ("web.glb", "unity.fbx", "ar.usdz", "print.stl")}
print("[pw] ok exports", sizes)
```

Roblox takes FBX, OBJ or glTF per MeshPart (under 20,000 triangles, one material); Unreal converts metres to
centimetres on import; three.js and model-viewer take the GLB.
