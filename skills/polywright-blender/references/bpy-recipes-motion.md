# bpy recipes for hierarchy, motion and repeats (Blender 5.2)

Parenting without a jump, procedural motion with F-modifiers, drivers, keyframing a rigged character, a unit repeated along a curve and an
edge-wear mask bake, hand-painted base layers. Back to [SKILL.md](../SKILL.md);
also [bpy-recipes.md](bpy-recipes.md). Every block is run by `tests/test_recipes.py` in Blender 5.2.1, asserts
its own result and prints `[pw] ok ...`. Ideas after Acampora, *Python Scripting in Blender* (2023); the code is new.

## Parent and keep the world transform

Setting `child.parent` alone moves the child by the parent's transform. Set `matrix_parent_inverse` to the
parent's inverted world matrix to keep it in place. When you write `matrix_world` on many objects, go parents
first (sort by ancestor count), or children move twice.

```python
# recipe: parent-keep-transform
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
p = bpy.data.objects.new("parent", None); c = bpy.data.objects.new("child", None)
for o in (p, c):
    bpy.context.scene.collection.objects.link(o)
p.location = (2, 0, 1); p.rotation_euler = (0, 0, 0.7); c.location = (0, 3, 0)
bpy.context.view_layer.update()
before = c.matrix_world.copy()                       # a live reference without .copy()
c.parent = p
c.matrix_parent_inverse = p.matrix_world.inverted()
bpy.context.view_layer.update()
assert all(abs(a - b) < 1e-5 for ra, rb in zip(before, c.matrix_world) for a, b in zip(ra, rb))
def depth(o):
    n = 0
    while o.parent:
        o, n = o.parent, n + 1
    return n
assert [o.name for o in sorted((c, p), key=depth)] == ["parent", "child"]
print("[pw] ok parent kept world transform")
```

## Procedural motion with F-modifiers

Noise, loops and steps go on the F-curve as modifiers, not as baked keys. Types: GENERATOR, FNGENERATOR,
ENVELOPE, CYCLES, NOISE, LIMITS, STEPPED, SMOOTH. A modifier can be limited to a frame range
(`use_restricted_range`, `frame_start`, `frame_end`). Convert seconds to frames with `scene.render.fps`.

```python
# recipe: procedural-motion
import bpy
from bpy_extras import anim_utils
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; o = bpy.data.objects.new("bob", None); sc.collection.objects.link(o)
fps = sc.render.fps
for f, z in ((1, 0.0), (1 + fps, 1.0)):              # one rise over one second
    o.location.z = z
    assert o.keyframe_insert("location", index=2, frame=f)   # returns False on failure, does not raise
ad = o.animation_data
fc = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves.find("location", index=2)
fc.modifiers.new("CYCLES")                           # repeat the rise forever
n = fc.modifiers.new("NOISE"); n.strength = 0.5
n.use_restricted_range = True; n.frame_start, n.frame_end = 3 * fps, 4 * fps   # shake in second 3 only
plain = fc.evaluate(1 + fps // 2)
assert abs(fc.evaluate(1 + fps + fps // 2) - plain) < 1e-4     # cycled
assert any(abs(fc.evaluate(3 * fps + k) - fc.evaluate(1 + (3 * fps + k - 1) % fps)) > 1e-3 for k in range(1, fps))
print("[pw] ok procedural motion", [m.type for m in fc.modifiers])
```

## Drivers

`driver_add` returns an F-curve; its `.driver` holds the expression. A SCRIPTED expression sees only its own
variables, `frame` and the math functions. Variable types: SINGLE_PROP (one RNA path), TRANSFORMS, ROTATION_DIFF,
LOC_DIFF (distance between two objects), CONTEXT_PROP. A custom property's path is `'["name"]'`. Scripted
expressions that are not "simple" need Python auto-run (see the traps file, Running).

```python
# recipe: drivers
import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
ctl = bpy.data.objects.new("ctl", None); o = bpy.data.objects.new("swing", None)
for x in (ctl, o):
    sc.collection.objects.link(x)
ctl["amp"] = 0.5
d = o.driver_add("rotation_euler", 0).driver
d.type = "SCRIPTED"
v = d.variables.new(); v.name = "amp"; v.type = "SINGLE_PROP"
v.targets[0].id_type = "OBJECT"; v.targets[0].id = ctl; v.targets[0].data_path = '["amp"]'
d.expression = "amp * sin(frame / 10)"
print("simple expression:", d.is_simple_expression)    # True: runs without Python
sc.frame_set(16)
assert abs(o.rotation_euler.x - 0.5 * math.sin(1.6)) < 1e-4, o.rotation_euler.x
print("[pw] ok driver", round(o.rotation_euler.x, 4))
```

## Repeat a unit along a curve (tracks, chains, belts, fences)

Model one unit with its origin at its centre and both it and the curve at the world origin. Array with Fit Curve
comes before the Curve modifier in the stack; the other order bends one unit and then copies it straight. After
Belec, *Blender: Create Incredible Models*; the code is new.

```python
# recipe: curve-array
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.curve.primitive_bezier_circle_add(radius=3); path = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); link = bpy.context.active_object
link.scale = (0.3, 0.6, 0.1)                                       # one track plate, origin at its centre, at the world origin
with bpy.context.temp_override(object=link, active_object=link, selected_objects=[link]):
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
arr = link.modifiers.new("array", "ARRAY"); arr.fit_type = "FIT_CURVE"; arr.curve = path
arr.relative_offset_displace = (1.15, 0, 0)                        # gap between plates along local X
crv = link.modifiers.new("curve", "CURVE"); crv.object = path; crv.deform_axis = "POS_X"
assert [m.type for m in link.modifiers] == ["ARRAY", "CURVE"]       # Array first, or one bent plate
ev = link.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
xs = [v.co.x for v in ev.vertices]; ys = [v.co.y for v in ev.vertices]
assert len(ev.vertices) > 8 * 40 and max(xs) - min(xs) > 5 and max(ys) - min(ys) > 5, (len(ev.vertices), max(xs) - min(xs))
print("[pw] ok curve array, plates", len(ev.vertices) // 8)
```

## Edge-wear mask baked from the Bevel node

The Bevel shader node rounds normals near hard edges; one minus its dot with the true normal is bright only on
the edges. Bevel is Cycles-only, so bake it as Emit into a Non-Color float image, then use it (through a Power
or ColorRamp) to mix worn paint into the base colour, in any engine. Flat-shaded input; the same source.

```python
# recipe: edge-wear-mask
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2); ob = bpy.context.active_object
# flat shading: Bevel rounds the hard edges; the primitive cube already has non-overlapping UVs
img = bpy.data.images.new("wear", 128, 128, float_buffer=True)
img.colorspace_settings.name = "Non-Color"                        # a mask is data, not colour
mat = bpy.data.materials.new("wear"); ob.data.materials.append(mat)
N, L = mat.node_tree.nodes, mat.node_tree.links
for n in list(N):
    N.remove(n)
bev, geo = N.new("ShaderNodeBevel"), N.new("ShaderNodeNewGeometry")
bev.samples = 8; bev.inputs["Radius"].default_value = 0.1
dot = N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
emit, out = N.new("ShaderNodeEmission"), N.new("ShaderNodeOutputMaterial")
tex = N.new("ShaderNodeTexImage"); tex.image = img; N.active = tex   # the bake target is the active image node
L.new(bev.outputs["Normal"], dot.inputs[0]); L.new(geo.outputs["Normal"], dot.inputs[1])
L.new(dot.outputs["Value"], inv.inputs[1]); L.new(inv.outputs[0], emit.inputs["Color"])
L.new(emit.outputs[0], out.inputs["Surface"])
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
    bpy.ops.object.bake(type="EMIT")                              # Bevel only works in Cycles, so bake it
px = list(img.pixels); vals = px[0::4]
hi = sum(1 for v in vals if v > 0.02)
assert 0 < hi < len(vals) * 0.9, (hi, len(vals))                 # edges light up, faces stay dark
img.filepath_raw = os.path.join(OUT, "edge_wear.exr"); img.file_format = "OPEN_EXR"; img.save()
print("[pw] ok edge wear mask, edge texels", hi, "of", len(vals))
```

## Hand-painted base layers baked to one albedo

Paint over baked masks: a top-light gradient (object Z), the edge mask above, a face-selection mask (FACE
attribute), baked as Emit to one sRGB albedo with an 8 px Extend margin; a colour variant is that image through
Hue/Saturation, baked again. Paint with view transform Standard. Strokes and Quick Edit need a viewport
(R-20261117-2).

```python
# recipe: handpaint-base
import bpy, os, tempfile
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"
sc.view_settings.view_transform = "Standard"
bpy.ops.mesh.primitive_cube_add(); ob = bpy.context.active_object  # adapt: your prop
att = ob.data.attributes.new("mask_top", "FLOAT", "FACE")
att.data.foreach_set("value", [1.0 if p.normal.z > 0.9 else 0.0 for p in ob.data.polygons])
mat = bpy.data.materials.new("hp"); ob.data.materials.append(mat); N, L = mat.node_tree.nodes, mat.node_tree.links.new
for n in list(N):
    N.remove(n)
out, em = N.new("ShaderNodeOutputMaterial"), N.new("ShaderNodeEmission"); L(em.outputs[0], out.inputs["Surface"])
tc, sp = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeSeparateXYZ"); L(tc.outputs["Generated"], sp.inputs[0])
grad = N.new("ShaderNodeMix"); grad.data_type = "RGBA"; L(sp.outputs["Z"], grad.inputs["Factor"])
grad.inputs["A"].default_value, grad.inputs["B"].default_value = (0.2, 0.1, 0.05, 1), (0.55, 0.32, 0.15, 1)
att_n = N.new("ShaderNodeAttribute"); att_n.attribute_name = "mask_top"
top = N.new("ShaderNodeMix"); top.data_type = "RGBA"; top.blend_type = "SCREEN"
L(att_n.outputs["Fac"], top.inputs["Factor"]); L(grad.outputs["Result"], top.inputs["A"])
top.inputs["B"].default_value = (0.4, 0.3, 0.2, 1); L(top.outputs["Result"], em.inputs["Color"])
def bake(name):
    img = bpy.data.images.new(name, 128, 128); tex = N.new("ShaderNodeTexImage"); tex.image = img; N.active = tex
    bpy.ops.object.bake(type="EMIT", margin=8, margin_type="EXTEND")
    img.filepath_raw = os.path.join(OUT, name + ".png"); img.file_format = "PNG"; img.save(); return img, tex
alb, alb_tex = bake("albedo")
hs = N.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = 0.85
L(alb_tex.outputs["Color"], hs.inputs["Color"]); L(hs.outputs[0], em.inputs["Color"])
var, _ = bake("albedo_variant")
a, b = list(alb.pixels), list(var.pixels)
assert abs(sum(a[0::4]) - sum(b[0::4])) > 1.0, "variant did not change"
print("[pw] ok albedo + variant, red sums", round(sum(a[0::4])), round(sum(b[0::4])))
```

The same with Ucupaint 3.x (GPL extension, layer stack and baked masks in one node group): node setup,
a layer, a curvature bake, then a bake target baked to one image. Bakes need a 3D view in the context,
so load the factory screens and override. Skips when the extension is not installed (R-20261117-3).

```python
# recipe: handpaint-ucupaint
import bpy, os, tempfile, addon_utils
OUT = os.environ.get("PW_OUT", tempfile.gettempdir())
mod = next((m.__name__ for m in addon_utils.modules() if m.__name__.endswith(".ucupaint")), None)
if not mod:
    print("[pw] ok skipped: Ucupaint not installed"); raise SystemExit
addon_utils.enable(mod, default_set=True)
bpy.ops.wm.read_homefile(use_factory_startup=True)  # its screens give bakes a 3D view
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_cube_add(); ob = bpy.context.active_object  # adapt: your prop
m = ob.modifiers.new("b", "BEVEL"); m.width, m.segments = 0.15, 3; bpy.ops.object.modifier_apply(modifier="b")
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.uv.smart_project(island_margin=0.02); bpy.ops.object.mode_set(mode="OBJECT")
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"
scr, area = next((s, a) for s in bpy.data.screens for a in s.areas if a.type == "VIEW_3D")
ctx = dict(screen=scr, area=area, region=next(r for r in area.regions if r.type == "WINDOW"), object=ob, active_object=ob)
with bpy.context.temp_override(**ctx):  # without it bakes fail: space_data is None
    bpy.ops.wm.y_quick_ypaint_node_setup(type="BSDF_PRINCIPLED")
    bpy.ops.wm.y_new_layer(name="Base", type="COLOR", uv_map="UVMap")
    bpy.ops.wm.y_bake_to_layer(type="CURVATURE", width=128, height=128)  # also AO, CAVITY, DUST
    bpy.ops.wm.y_new_bake_target(); bpy.ops.wm.y_bake_all_targets()  # y_bake_channels is gone in 3.x
img = max((i for i in bpy.data.images if i.has_data), key=lambda i: i.size[0])
r = list(img.pixels)[0::4]
assert max(r) - min(r) > 0.2, "flat bake"
img.filepath_raw = os.path.join(OUT, "ucupaint_color.png"); img.file_format = "PNG"; img.save()
print("[pw] ok", img.name, tuple(img.size), "red %.2f-%.2f" % (min(r), max(r)))
```

## Animate an imported rigged character

For a downloaded rig (FBX, glTF, .blend in a zip): import it, find the armature, key pose bones in an action,
then render a few frames as a sheet before tuning. A live MCP session suits tuning by eye; this runs headless.
Source of the idea: a live Blender MCP run that animated a rigged character from one prompt
([r/aigamedev](https://www.reddit.com/r/aigamedev/comments/1xtgir8/)). The test builds its own two-bone rig.

```python
# recipe: animate-rigged-character
import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
# after a real import: arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
ad = bpy.data.armatures.new("rig"); arm = bpy.data.objects.new("rig", ad); bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
b1 = ad.edit_bones.new("root"); b1.head, b1.tail = (0, 0, 0), (0, 0, 1)
b2 = ad.edit_bones.new("arm"); b2.head, b2.tail = (0, 0, 1), (0, 0, 2); b2.parent = b1
bpy.ops.object.mode_set(mode="POSE")
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 48
pb = arm.pose.bones["arm"]; pb.rotation_mode = "XYZ"
for f, deg in ((1, 0), (24, 60), (48, 0)):                      # pose bones, not edit bones, carry animation
    pb.rotation_euler = (math.radians(deg), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
bpy.ops.object.mode_set(mode="OBJECT")
act = arm.animation_data.action; act.name = "wave"
sc.frame_set(24); bpy.context.view_layer.update()
assert abs(arm.pose.bones["arm"].rotation_euler.x - math.radians(60)) < 1e-4
print("[pw] ok rigged character keyed, action", act.name)
```

Bone names differ per rig (Mixamo `mixamorig:`, Rigify `DEF-`/`ORG-`): list `arm.pose.bones.keys()` first and key
the control bones, never the deform bones of a Rigify rig.
