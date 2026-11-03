# bpy recipes for hierarchy and motion (Blender 5.2)

Parenting without a jump, procedural motion with F-modifiers, and drivers. Back to [SKILL.md](../SKILL.md);
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
