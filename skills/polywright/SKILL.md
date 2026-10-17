---
name: polywright
description: "Start here whenever a task needs a 3D model and no sibling below clearly owns it: a model of a real or imagined thing for a game (Unity, Roblox, Unreal, three.js), a 3D print, AI video or AR, or another plugin asking for a mesh. Picks the route (find, capture, generate, code), scaffolds the asset folder and manifest other plugins read, and runs pw.py (inspect, render a sheet, convert, check a budget, bpy headless, match a picture's camera, army blockouts with depth and pose passes for AI video). Use on 'I need a 3D model of', 'model this for my game and a print', 'army blockout'. Siblings: polywright-references, -capture, -generate, -blender, -finish, -print. Also 'refresh polywright'."
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

## Compose a model into a picture

When an image or video model keeps drawing a designed prop wrong (a storyboard still, a set reference, a
poster), take the composition from the picture and the shape from the model:

1. Pick the picture for composition only: where people stand, the light, the aim. A plain stand-in prop is fine.
2. `pw.py match model.blend --still pic.png --out work/match.png --anchor-px X,Y --anchor-local=X,Y,Z
   --aim-px X,Y --aim-local=X,Y,Z --depth M --horizon ROW --hide BOX --mask-add BOX`: the model's anchor (a
   grip) lands on the hand, its aim point (a tip) on the exact pixel, rendered RGBA with the picture's lens and
   horizon. Set `--depth` so its width in pixels matches the stand-in's (width = f_px x diameter / depth;
   `f_px` is in the result). `--hide` drops the part behind a hand; `--mask-add` adds the hands to the mask.
3. Read `match_paste.png` cropped at 3x: shape, size in frame, aim. Fix depth and pixels, re-run (seconds).
4. Blend inside `match_mask.png` with a masked low-denoise image edit (FLUX.2 Klein or any inpaint model:
   denoise 0.3 to 0.5, low cfg), then paste the result back through the mask so every pixel outside stays the
   picture's own. A whole-picture edit redraws everything (HDR colour, a bigger prop).
5. Check at full size; keep two or more seeds.

Worked example and the reasons: the No-God film's storyboard method (comfyui-gen LEARNINGS L-091
`compose-the-hero-prop`; `nogod/storyboard-method.md` in the owner's video folder). Reference sheets of the
prop come from the model too (polywright-references, Step 2b).

## Crowd and battle blockouts (AI video)

Video models break on crowds; Blender does not. Let Blender place the army and the video model paint the look:

1. `pw.py crowd --out work/crowd --action clash --preview` (or march, advance, charge, hold; `--ranks`,
   `--cols`, `--view side|behind|high`, `--lens`, `--move`), then read `work/crowd/sheet.png`.
2. Drop `--preview` for the full shot: `depth.mp4` (main control), `pose.mp4` (front ranks), `mask.mp4` (side A
   red, side B blue), `clay.mp4`, `camera.json`; 832x480, 81 frames at 16 fps by default (Wan's 4n+1 and /16).
3. Repaint clay frame 1 into an approved start still; drive Wan VACE or Wan 2.2 Fun Control with the depth video
   and that still. Prompt costume, colour per side, light and haze, not the head count.

Depth convention, views, screen direction, your own soldier, two-fighter previs and what is untested:
[references/crowd-blockouts.md](references/crowd-blockouts.md). Shot planning is cinewright's.

A small cast of real figures or toys (sides swapped, an extra figure, markings lost): mesh each from photos, fix
colour and painted markings with `pw.py mark`, give the video model `pw.py turnaround` pictures as references and a
`pw.py lineup` (teams on fixed sides, depth and mask) as its opening: [references/figures-for-video.md](references/figures-for-video.md).

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
