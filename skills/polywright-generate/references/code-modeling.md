# Modelling with code

Back to [SKILL.md](../SKILL.md). Sources: polywright research notes `2026-10-11-ai-agents-and-3d.md` (agent
benchmarks: LL3M arXiv 2508.08228, 3DCodeBench 2606.01057, 3DHarnessBench 2609.06535, BlenderGym) and
`2026-10-11-generative-3d.md` section 5.

## Why code

An agent writing code gets exact dimensions, sharp edges, named parts, repeatable output and something it can
edit. Benchmarks found feeding tracebacks back raised scripts that run from 0.70 to 0.97, but shape quality
barely moved: shape errors are fixed by measuring and looking, not by retrying.

## Pattern: named parts plus checks

```python
# build.py: run with  python pw.py bpy build.py -- --out work/bench.blend
import bpy, sys, math
args = sys.argv[sys.argv.index("--") + 1:]
out = args[args.index("--out") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)

DIMS = {"length": 1.8, "seat_h": 0.45, "seat_d": 0.42, "slat_t": 0.035, "leg_w": 0.06}   # metres, real size

def box(name, size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return o

parts = []
for i, y in enumerate((-0.15, -0.05, 0.05, 0.15)):
    parts.append(box("seat_slat_%d" % i, (DIMS["length"], 0.09, DIMS["slat_t"]), (0, y, DIMS["seat_h"])))
for x in (-0.8, 0.8):
    parts.append(box("leg_%+.1f" % x, (DIMS["leg_w"], DIMS["seat_d"], DIMS["seat_h"]), (x, 0, DIMS["seat_h"] / 2)))

# checks, printed for the agent to read
xs = [v.co.x for o in parts for v in o.data.vertices]
zs = [v.co.z for o in parts for v in o.data.vertices]
print("[pw] check length %.3f m (want %.2f)" % (max(xs) - min(xs), DIMS["length"]))
print("[pw] check seat top %.3f m" % max(zs))
print("[pw] parts", len(parts))
bpy.ops.wm.save_as_mainfile(filepath=out)
```

Then `pw.py render work/bench.blend --out renders/v01` and look. Units are metres; origins at the base;
one object per material if it will be painted or printed in colour.

## Solids for printing and CAD

- **build123d** (Python, OCCT): context builders, fillets and chamfers that work, STEP and STL export.
- **CadQuery** (Python, OCCT): fluent API, large example base.
- **OpenSCAD**: CSG language; `openscad -o out.stl model.scad` (and `--backend=manifold` on recent builds for
  speed); watertight by construction.
- **FreeCAD** headless (`freecadcmd`): when an existing FCStd model must be edited.

Rules: model at real size in millimetres; chamfer bed-facing edges; 0.3 mm clearance between parts that
move; walls at least 1.2 mm; export STEP for CAD users and STL or 3MF for slicers; check the STL with
`pw.py check --target print-fdm`.

## Procedural (variations)

Geometry Nodes or plain bpy loops for fences, buildings, scattered rocks and trees. Seeded randomness, so the same
seed rebuilds the same scene. Set a Geometry Nodes input in Blender 5.2 with
`mod.properties.inputs.Socket_2.value = x` (the 4.x `mod["Socket_2"] = x` fails; see polywright-blender).

## Agent loop that works

Plan (named parts and dimensions in the brief), act (script), critique (measure plus a contact sheet against the
reference) as separate passes; save a numbered .blend per milestone; spend more on checking than on generating
when the budget is large (BlenderGym).
