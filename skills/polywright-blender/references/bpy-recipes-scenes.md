# bpy recipes for scenes and passes (Blender 5.2)

Scatter, several control passes from one render, clay without touching materials, line passes and video
encoding without ffmpeg. Back to [SKILL.md](../SKILL.md); also [bpy-recipes.md](bpy-recipes.md) and
[bpy-recipes-physics.md](bpy-recipes-physics.md). Every block is run by `tests/test_recipes.py` in Blender
5.2.1, asserts its own result and prints `[pw] ok ...`. Ideas credited to the books they came from; the code is
new.

## Scatter with Geometry Nodes

Poisson points on a surface, one variant from a collection per point, random yaw and scale (after the Packt
*Procedural 3D Modeling Using Geometry Nodes*, the scatter chapters). Instances render cheaply and survive a glTF
export with `export_gpu_instances`; add a Realize Instances node before applying when one mesh is needed (a print,
a boolean, a measurement). `pw.py crowd --scatter` uses this tree for background figures.

```python
# recipe: gn-scatter
import bpy, bmesh, os, tempfile
from mathutils import Matrix
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
bank = bpy.data.collections.new("variants")                       # adapt: your variants, one object each
for i, h in enumerate((1.6, 1.75, 1.9)):
    me = bpy.data.meshes.new("v%d" % i); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.25, radius2=0.2, depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)     # origin at the feet
    bm.to_mesh(me); bm.free(); bank.objects.link(bpy.data.objects.new(me.name, me))
bpy.ops.mesh.primitive_plane_add(size=20); ground = bpy.context.active_object
ng = bpy.data.node_groups.new("scatter", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gap = ng.interface.new_socket("Min Distance", in_out="INPUT", socket_type="NodeSocketFloat")
N, L = ng.nodes, ng.links
gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
pts = N.new("GeometryNodeDistributePointsOnFaces"); pts.distribute_method = "POISSON"
pts.inputs["Density Max"].default_value = 2.0
info = N.new("GeometryNodeCollectionInfo"); info.inputs["Collection"].default_value = bank
info.inputs["Separate Children"].default_value = info.inputs["Reset Children"].default_value = True
inst = N.new("GeometryNodeInstanceOnPoints"); inst.inputs["Pick Instance"].default_value = True
def rnd(kind, lo, hi, seed):
    n = N.new("FunctionNodeRandomValue"); n.data_type = kind
    for s in n.inputs:
        if s.enabled and s.name in ("Min", "Max", "Seed"):
            s.default_value = {"Min": lo, "Max": hi, "Seed": seed}[s.name]
    return next(s for s in n.outputs if s.enabled)                # the output follows data_type
yaw = N.new("ShaderNodeCombineXYZ")
L.new(gi.outputs["Geometry"], pts.inputs["Mesh"]); L.new(gi.outputs["Min Distance"], pts.inputs["Distance Min"])
L.new(pts.outputs["Points"], inst.inputs["Points"]); L.new(info.outputs[0], inst.inputs["Instance"])
L.new(rnd("INT", 0, len(bank.objects) - 1, 1), inst.inputs["Instance Index"])
L.new(rnd("FLOAT", -0.26, 0.26, 2), yaw.inputs["Z"]); L.new(yaw.outputs[0], inst.inputs["Rotation"])
L.new(rnd("FLOAT", 0.94, 1.06, 3), inst.inputs["Scale"])
L.new(inst.outputs[0], go.inputs["Geometry"])
mod = ground.modifiers.new("scatter", "NODES"); mod.node_group = ng
getattr(mod.properties.inputs, gap.identifier).value = 1.2        # 5.x: .value on the modifier's input
dg = bpy.context.evaluated_depsgraph_get()
n = sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == ground)
assert 60 < n < 400, n
real = N.new("GeometryNodeRealizeInstances")                      # one mesh: realize, then apply
L.new(inst.outputs[0], real.inputs[0]); L.new(real.outputs[0], go.inputs["Geometry"])
bpy.context.view_layer.objects.active = ground
bpy.ops.object.modifier_apply(modifier=mod.name)
assert len(ground.data.polygons) >= n * 10, len(ground.data.polygons)
print("[pw] ok scatter", n, "instances,", len(ground.data.polygons), "faces once realized")
```

## Several control passes from one render

One Cycles render writes inverse depth, a per-side mask, Mist and normals as 16-bit PNGs through a compositor
File Output node. Inverse depth comes from a shader AOV (1 / view depth mapped over one range for the shot), so
it is the same signal `pw.py crowd` renders, not Mist: Mist maps plain distance through its falloff, which gives
the near ranks fewer tones. Shader AOVs and the Mist pass after van Gumster, *Blender All-in-One For Dummies*
(rendering in passes). Keep depth of field and motion blur off in control passes; record lens and focus in
`camera.json` instead.

```python
# recipe: passes-one-render
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = 160, 90
NEAR, FAR = 3.0, 30.0                                             # adapt: one range for the whole shot
vl = sc.view_layers[0]; vl.use_pass_mist = vl.use_pass_normal = True
for name, kind in (("side", "COLOR"), ("invdepth", "VALUE")):
    a = vl.aovs.add(); a.name, a.type = name, kind
sc.world = bpy.data.worlds.new("w"); sc.world.mist_settings.start, sc.world.mist_settings.depth = NEAR, FAR - NEAR
sc.world.mist_settings.falloff = "LINEAR"
def team_material(name, rgb):
    m = bpy.data.materials.new(name); nt = m.node_tree
    cd, inv, mr = nt.nodes.new("ShaderNodeCameraData"), nt.nodes.new("ShaderNodeMath"), nt.nodes.new("ShaderNodeMapRange")
    inv.operation = "DIVIDE"; inv.inputs[0].default_value = 1.0; mr.clamp = True
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 1 / FAR, 1 / NEAR
    nt.links.new(cd.outputs["View Z Depth"], inv.inputs[1]); nt.links.new(inv.outputs[0], mr.inputs["Value"])
    for aov_name, sock, value in (("invdepth", "Value", mr.outputs["Result"]), ("side", "Color", None)):
        o = nt.nodes.new("ShaderNodeOutputAOV"); o.aov_name = aov_name
        if value is not None: nt.links.new(value, o.inputs[sock])
        else: o.inputs[sock].default_value = rgb
    return m
for x, y, side in ((-1.5, 6, (1, 0, 0, 1)), (1.5, 18, (0, 0, 1, 1))):  # a near red figure, a far blue one
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=(x, y, 0.75))
    bpy.context.active_object.data.materials.append(team_material("t%d" % y, side))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location, cam.rotation_euler = (0, 0, 1.0), (1.5708, 0, 0)    # looking down +Y
ng = bpy.data.node_groups.new("passes", "CompositorNodeTree"); sc.compositing_node_group = ng
rl, fo = ng.nodes.new("CompositorNodeRLayers"), ng.nodes.new("CompositorNodeOutputFile")
fo.directory, fo.file_name = OUT, "shot_"                         # name it, or files come out as Unsaved<pass>
fo.format.media_type = "IMAGE"; fo.format.file_format = "PNG"; fo.format.color_depth = "16"
for name in ("invdepth", "side", "Mist", "Normal"):
    fo.file_output_items.new("FLOAT" if name in ("invdepth", "Mist") else "RGBA", name)
    ng.links.new(rl.outputs[name], fo.inputs[name])
bpy.ops.render.render(write_still=False)
files = sorted(f for f in os.listdir(OUT) if f.startswith("shot_") and f.endswith(".png"))
assert len(files) == 4, files
img = bpy.data.images.load(os.path.join(OUT, next(f for f in files if "invdepth" in f)))
px, w = list(img.pixels), img.size[0]
val = lambda u, v: px[4 * (int(v * img.size[1]) * w + int(u * w))]
near, far = val(0.25, 0.45), val(0.62, 0.47)                       # centres of the near and the far cube
assert near > far > 0.0, (near, far)
print("[pw] ok passes", files, "near %.2f far %.2f" % (near, far))
```

## Clay without touching materials

A view layer's material override draws every object with one material, so a clay or a flat pass needs no
material swaps (after Simonds, *Blender Master Class*, the clay render).

```python
# recipe: clay-override
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 1; sc.cycles.device = "CPU"
sc.render.resolution_x = sc.render.resolution_y = 32; sc.view_settings.view_transform = "Raw"
bpy.ops.mesh.primitive_plane_add(size=50, rotation=(1.5708, 0, 0), location=(0, 5, 0))
red = bpy.data.materials.new("red"); red.diffuse_color = (1, 0, 0, 1)
bpy.context.active_object.data.materials.append(red)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_euler = (1.5708, 0, 0)
clay = bpy.data.materials.new("clay"); nt = clay.node_tree
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
bpy.context.view_layer.material_override = clay                   # every object, no material edits
sc.render.filepath = os.path.join(OUT, "clay.png"); bpy.ops.render.render(write_still=True)
bpy.context.view_layer.material_override = None
img = bpy.data.images.load(sc.render.filepath); r, g, b = list(img.pixels)[4 * (16 * 32 + 16):][:3]
assert abs(r - g) < 0.02 and abs(g - b) < 0.02 and r > 0.3, (r, g, b)
print("[pw] ok clay override", round(r, 3), round(g, 3), round(b, 3), "red material untouched:", red.users)
```

## Line pass straight from geometry

Grease Pencil Line Art draws silhouettes and creases from the scene's geometry, an alternative to a Canny of
a clay render (Line Art after van Gumster; whether a video model's edge control prefers it is untested).

```python
# recipe: line-art
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 320, 180
bpy.ops.mesh.primitive_monkey_add()
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location, cam.rotation_euler = (0, -5, 0), (1.5708, 0, 0)
bpy.ops.object.grease_pencil_add(type="LINEART_SCENE")            # 5.x: GREASEPENCIL objects, not GPENCIL
gp = bpy.context.active_object
bpy.context.view_layer.update()
drawing = gp.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.layers[0].current_frame().drawing
n = len(drawing.strokes)
assert n > 20, n
sc.render.filepath = os.path.join(OUT, "lines.png"); bpy.ops.render.render(write_still=True)
print("[pw] ok line art", n, "strokes", os.path.getsize(sc.render.filepath), "bytes")
```

## Encode frames to MP4 without ffmpeg

Blender carries its own FFmpeg: the sequencer turns an image sequence into H.264 at an exact frame count and
frame rate. Set the scene's fps to the target video model's first (after Brito, *Blender for Video Production*).

```python
# recipe: encode-mp4
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 64, 48
names = []
for i in range(5):                                                # adapt: your frames
    img = bpy.data.images.new("f%d" % i, 64, 48); img.pixels = [i / 4, 0.2, 1 - i / 4, 1] * (64 * 48)
    img.filepath_raw = os.path.join(OUT, "frame_%04d.png" % (i + 1)); img.file_format = "PNG"; img.save()
    names.append(os.path.basename(img.filepath_raw))
sc.render.fps, sc.frame_start, sc.frame_end = 24, 1, len(names)
ed = sc.sequence_editor_create()
strip = ed.strips.new_image("frames", os.path.join(OUT, names[0]), channel=1, frame_start=1)  # 5.x: strips
for n in names[1:]:
    strip.elements.append(n)
im = sc.render.image_settings; im.media_type = "VIDEO"; im.file_format = "FFMPEG"  # media type first
sc.render.ffmpeg.format, sc.render.ffmpeg.codec = "MPEG4", "H264"
sc.render.filepath = os.path.join(OUT, "frames_")
bpy.ops.render.render(animation=True)
mp4 = [f for f in os.listdir(OUT) if f.startswith("frames_") and f.endswith(".mp4")]
assert mp4 and os.path.getsize(os.path.join(OUT, mp4[0])) > 1000, mp4
print("[pw] ok encoded", mp4[0])
```
