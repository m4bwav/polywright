---
name: polywright-blender
description: "Drive Blender 5.x from an agent on any OS: headless runs that report errors (pw.py bpy), the bpy API traps models still write, tested recipes (modifiers, booleans, remesh, UVs, bakes, reference images, turntables, depth passes, exports), Blender MCP servers and their risks, and the other 3D tools per OS. Use on 'write a Blender script', 'automate Blender', 'bpy error', a Blender traceback, 'Blender MCP', 'headless Blender', 'which 3D tool on Mac or Linux'. Also 'refresh polywright-blender'."
---

# polywright-blender

Blender is the workhorse: free, every OS, scriptable to the last button. An agent drives it best headless, on
copies, with short text reports, not through screenshots of a live session.
Back to the hub: [../polywright/SKILL.md](../polywright/SKILL.md).
Depth: [references/bpy-api-traps.md](references/bpy-api-traps.md), [references/bpy-recipes.md](references/bpy-recipes.md)
(each recipe is run by the test suite), [references/mcp-bridges.md](references/mcp-bridges.md),
[references/tools-by-os.md](references/tools-by-os.md).

## Step 1: which Blender

`python ../polywright/scripts/pw.py doctor` finds it (POLYWRIGHT_BLENDER, PATH, install folders on Windows,
macOS and Linux) and prints the version. Target the current LTS (5.2, supported to July 2028). Write the version
into the script's first comment; API facts below are for 5.2.

## Step 2: run scripts headless

```
python ../polywright/scripts/pw.py bpy build.py [--blend in.blend] [--timeout 1800] -- <script args>
```

It runs `blender --background --factory-startup --python-exit-code 3 --python build.py -- args`, strips
Blender's log noise and returns `ok`, the script's own output lines and the traceback. Without
`--python-exit-code` a Python error inside Blender still exits 0: never judge success by exit code alone
otherwise. Print your own `[pw]` lines for the numbers you need (sizes, counts, checks).

Script rules:

- Start from `bpy.ops.wm.read_factory_settings(use_empty=True)` or an explicit `.blend`; never depend on a
  user's startup file.
- Prefer `bpy.data` and `bmesh` over `bpy.ops`. When an operator is needed, set the active object and
  selection first, or use `with bpy.context.temp_override(...)`.
- Viewport operators fail headless (`view3d.*`, `screen.screenshot`, `render.opengl`): frame cameras from
  bounds yourself (as `pw.py render` does).
- Read enum items instead of guessing names: `m.bl_rna.properties["solver"].enum_items`.
- Real size in metres; apply transforms before measuring; glTF imports come in quaternion mode with the axis fix
  on a parent: clear parents keeping transforms, then apply, then measure.
- Save a numbered `.blend` per milestone in `work/`; restart from it rather than carrying a long live session.
- Two retries on a traceback; then look up the API (traps file, introspection, the official MCP's docs
  search) instead of guessing a third time.

## Step 3: the traps (short list; full list in the traps file)

| Writes (old) | Use in 5.x |
|---|---|
| `bpy.ops.import_scene.obj`, `import_mesh.stl`, `import_mesh.ply`, `wm.collada_*` | `wm.obj_import`, `wm.stl_import`, `wm.ply_import`; Collada is gone |
| `BLENDER_EEVEE_NEXT` | `BLENDER_EEVEE` |
| `import bgl` | the `gpu` module |
| Principled `Specular`, `Subsurface`, `Transmission`, `Emission`, `Clearcoat` | `Specular IOR Level`, `Subsurface Weight`, `Transmission Weight`, `Emission Color`, `Coat Weight` |
| `action.fcurves` | slotted actions: layers, strips, channelbags |
| `mod["Socket_2"] = x` on Geometry Nodes | `mod.properties.inputs.Socket_2.value = x` |
| `import_image.to_plane` | `image.import_as_mesh_planes` |
| Workbench `shading.show_shadow` | `shading.show_shadows` |

## Step 4: common jobs

`pw.py` already does inspect, render, convert, LODs, printable and union. For anything else take a recipe from
[references/bpy-recipes.md](references/bpy-recipes.md): reference images at scale, modifiers and apply, Boolean
with the Manifold solver and an EXACT fallback, voxel remesh, QuadriFlow, Smart UV and lightmap UVs, normal and
AO bake from high to low, materials with 5.x sockets, turntable stills, depth and normal passes for video,
exports per engine.

## Step 5: live sessions (MCP)

Two servers exist: Blender Lab's official MCP (v1.0.3, Blender 5.1+, scene analysis and API docs search) and the
community mcp-for-blender (formerly blender-mcp; asset search and generator hooks). Both run any Python the
model sends, with no sandbox, on port 9876. Use one, never both; only when the user is watching Blender and
wants live edits; never paste text from downloaded files into its code. Setup and failure modes:
[references/mcp-bridges.md](references/mcp-bridges.md).

## Other tools

Mesh checks and repairs without Blender: trimesh + manifold3d (+ PyMeshLab); web delivery: gltf-transform or
gltfpack; solids: OpenSCAD, build123d, CadQuery, FreeCAD; slicers have CLIs. Versions and what runs on which OS:
[references/tools-by-os.md](references/tools-by-os.md). On macOS, Blender 5.x and the bpy wheel are Apple
Silicon only; the bpy wheel needs exactly the Python Blender bundles (3.13 for 5.2).

## Maintenance

Evergreen unit, tier `moderate` (a Blender release every four months; check at each one). Companions:
[RESEARCH.md](RESEARCH.md), [CHANGELOG.md](CHANGELOG.md), [LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md)
with `evals/evals.json`, [MAINTENANCE.md](MAINTENANCE.md), state in `evergreen.json`. Read `evergreen.json` at
each use; refresh when due.
