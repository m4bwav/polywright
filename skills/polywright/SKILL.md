---
name: polywright
description: "Start here for any job that needs a 3D model, real or imagined, for a game (Unity, Roblox, Unreal, three.js), a 3D print, AI video or AR. Picks the route (find, capture, generate, code), scaffolds the asset folder and manifest other plugins read, and runs pw.py: inspect, render a contact sheet, convert, check against a target's budget, run bpy headless. Use on 'make a 3D model of', 'turn this photo into 3D', 'is this mesh game-ready', 'check this STL', or when another plugin needs a mesh. Siblings: polywright-references, -capture, -generate, -blender, -finish, -print. Also 'refresh polywright'."
---

# polywright

The hub for 3D model work. It decides how a model gets made, keeps every asset in one folder with a
manifest, and proves each step with numbers and a picture. The sibling skills hold the depth.

Script: `scripts/pw.py` in this skill folder (Python 3.9+, standard library, one JSON object per command;
`scripts/pw_bpy.py` is its Blender half, never run by hand).
Run `python <this folder>/scripts/pw.py doctor` once per session: it finds Blender (any OS), the Python mesh
libraries, slicers and ComfyUI hosts, and says what is missing. Full command list: [references/cli.md](references/cli.md).

## Step 1: the brief (ask only what you cannot infer)

- **What**: the object or place, real or imagined, and how recognisable it must be.
- **Targets**: one or more of `pw.py check --list` (game-roblox, game-unity, game-unreal, web-threejs,
  ar-usdz, commerce-gltf, print-fdm, print-resin, video-blockout, cad-step). The target sets the budget.
- **Real size** in metres (a bench is 1.8 m long; a person 1.7 to 1.8 m). Wrong scale is the most common
  silent error; `check --real-size-m` catches it.
- **Inputs**: a prompt, photos, a sketch, measurements, a map location, an existing mesh.
- **Fidelity and budget**: blockout, game-ready, hero; how much time or money a hosted generator may cost.

Scaffold: `pw.py new <dir> --name <Name> --kind real|imagined|hybrid --route <route> --targets a,b --real-size-m X`.
Folder: `refs/` (references, each recorded as a source), `work/` (.blend, intermediates), `out/` (one deliverable
per target), `renders/` (review sheets), `brief.md`, `manifest.json`. Contract for other plugins:
[references/contract.md](references/contract.md).

## Step 2: pick the route (cheapest that meets the brief)

| Situation | Route | Skill |
|---|---|---|
| A common object; licence allows reuse | **find**: Poly Haven, Kenney, Quaternius (CC0), Sketchfab and print sites (check each licence) | this skill, [references/routes.md](references/routes.md) |
| Has dimensions, parts that fit, sharp edges (bracket, case, building, furniture) | **code**: bpy, build123d/CadQuery/OpenSCAD | polywright-generate, polywright-blender |
| A real place (park, street, campus, terrain) | **place**: OSM + elevation (`pw.py place`) | polywright-capture |
| A real object you can photograph or scan | **capture**: photogrammetry, splats, scanner, or model from measurements | polywright-capture |
| Imagined organic or one-off (statue, creature, prop) | **generate**: reference sheet, then image-to-3D | polywright-references, polywright-generate |
| Hero character that deforms | generate or sculpt as a base, then retopology and rig | polywright-generate, polywright-finish |

Most good results mix routes: an OSM park with generated hero props, a code-built house with a generated
statue. Record the route per part in the manifest.

## Step 3: references before geometry

For anything not found ready-made, gather or generate references first (polywright-references): orthographic
views on a shared ground line with a height bar, material swatches, scale references. Generated inputs decide
most of an image-to-3D result.

## Step 4: build, then prove it (every route)

1. **Blockout first** at real size: primitives for silhouette and proportion. Fix scale here; it is cheap now.
2. **Numbers**: `pw.py inspect <file>`: triangles, objects, size, materials, textures, UVs, watertight,
   parts. Read it before and after each destructive step.
3. **Picture**: `pw.py render <file> --out renders/<step>`: six views and one `sheet.png`. Read the sheet,
   not six screenshots. Compare against the references: silhouette, proportion, missing or floating parts,
   shading spikes, wrong axis (lying on its side), wrong scale.
4. **Target**: `pw.py check <file> --target <t> --real-size-m X`. Fail means fix before delivering; warn
   means say it in the hand-over.
5. **Record**: `pw.py manifest <dir> --add-output out/<file> --target <t> --inspect`, every source with
   `--add-source <url> --licence <l> --author <a>`, then `--validate`.

Plan, act and critique are separate passes: after building, look at the sheet as a critic would and list
defects before claiming done. Two rounds of fixing a traceback are worth it; past that, rethink the approach.
Save a numbered `.blend` per milestone (`work/<name>_v03.blend`) so a long job can restart from disk.

## Step 5: finish and hand over

Finishing per target (UVs, LODs, normal-map convention, axis and unit conversion, compression) is
polywright-finish; printing (watertight solid, walls, base, split, 3MF) is polywright-print. Hand the folder to
the plugin that uses it: three.js pages (threewright), film and video (cinewright), Roblox places
(roblox-agent), Unity projects (unity-agent), a printer-specific or slicer skill for print settings, an image
skill for more pictures. They read `manifest.json` and `out/`.

Hand-over message:

```
Model: <name> (<route>) -> out/<file> for <target>: <tris> tris, <size> m, <watertight/parts>
Check: <target> pass|warn (<rules>)   Review: renders/<step>/sheet.png
Sources: <n> with licences; AI-made parts: <which, which model>   Owed: <what is not done>
```

## Rules

- Real size in metres in Blender and glTF (+Z up in Blender, +Y up in glTF); millimetres only in print files.
- Never claim a mesh is fine from its file name or a generator's word: inspect, render, check.
- Every downloaded or generated input gets a source line with its licence. Stores and print sites (Fab, Unity
  Asset Store, Sketchfab, MakerWorld, Printables, Steam) require disclosure of AI-made content; the manifest
  records it.
- Blender bridges over MCP run arbitrary Python: prefer `pw.py bpy` on copies; use a live MCP session only when
  the user is watching (polywright-blender).
- Google Photorealistic 3D Tiles may be viewed, never exported, cached or traced (their terms).

## Maintenance

Evergreen unit, tier `fast` (generators and Blender move monthly). Companions: [RESEARCH.md](RESEARCH.md),
[CHANGELOG.md](CHANGELOG.md), [LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md) with `evals/evals.json`,
[MAINTENANCE.md](MAINTENANCE.md), state in `evergreen.json`. Read `evergreen.json` at each use; if due, do the
task, then refresh (evergreen-refresh). Write lessons to LEARNINGS.md as they happen.
