---
name: polywright-generate
description: "Use whenever an imagined or hypothetical 3D model must be made from a prompt, a drawing, concept art, photos or a blockout: image-to-3D through ComfyUI (TRELLIS.2, Pixal3D, Hunyuan3D-2 via pw.py gen) or hosted (Meshy, Tripo, Rodin), or code (bpy, build123d, CadQuery, OpenSCAD) when it has dimensions; then texturing and the licence record. Use on 'make me a 3D model of a dragon', 'turn this drawing or concept art into 3D', 'image to 3D', 'text to 3D', 'TRELLIS', 'Hunyuan3D', 'Meshy', 'model a bracket in OpenSCAD'. Also 'refresh polywright-generate'."
---

# polywright-generate

Two engines make imagined models: **code** (exact, editable, sharp, dimensioned) and **generators** (organic,
fast, approximate, messy topology). Choose by the object, not by habit. Back to the hub:
[../polywright/SKILL.md](../polywright/SKILL.md). Model table with licences and VRAM:
[references/generators.md](references/generators.md). Code patterns: [references/code-modeling.md](references/code-modeling.md).

## Step 1: code or generator?

| Object | Engine |
|---|---|
| Has dimensions, fits with something, is mostly planes and cylinders (bracket, case, shelf, building, sign, crate) | **code**: build123d, CadQuery or OpenSCAD for printable and CAD parts; bpy for game kits and buildings |
| Many variations of one thing (fences, houses, rocks, a forest) | **procedural code** (bpy, Geometry Nodes) from a few hero assets |
| Organic or sculptural one-off (statue, creature, character, tree trunk, food) | **generator** from a reference image or multi-view set |
| Character that will animate | generator for the shape, then retopology and a rig (polywright-finish) |
| A real object you have a photo of | try polywright-capture first; a generator guesses the hidden sides |

Diffusion rounds sharp edges and invents dimensions; code cannot sculpt a lion's face. Many good models are both:
a coded pedestal with a generated lion-head spout boolean-joined on.

## Step 2: generators

1. References first (polywright-references): one clean image on white, flat light, little perspective, 1024 px;
   for characters an A-pose; for a better back, a front/left/back/right set at the same scale.
2. `python ../polywright/scripts/pw.py doctor` shows ComfyUI hosts and their 3D checkpoints.
3. Run one:
   - Built-in Hunyuan3D-2 (shape only, about 100 s on a 16 GB card at 30 steps, octree 256):
     `pw.py gen --image refs/front.png [--left L --back B --right R] --out work/raw.glb [--seed N]`
   - Any other ComfyUI workflow, in API format or as saved by the editor (a template file works as is; pw.py
     converts it with the host's node definitions): `pw.py gen --image refs/front.png --workflow <file> --out work/raw.glb`.
     TRELLIS.2 and Pixal3D with PBR textures: ComfyUI's template `3d_pixal3d_trellis2_image_to_model.json` (in the
     ComfyUI install's `comfyui_workflow_templates_json/templates`); its switch picks Pixal3D by default, so add
     `--set 316.value=true` for TRELLIS.2. On a 16 GB card (GPU time): TRELLIS.2 377 s cold (73 to 190 s warm), upright, the best detail;
     Pixal3D 329 s, in the camera's frame (tilted: `pw.py convert IN OUT --level`); both about 700k triangles with 4096 px PBR textures;
     Hunyuan3D-2 99 s, shape only. `--set NODE.input=VALUE` changes any input.
   - Hosted APIs (Meshy has the clearest public price list; Tripo, Rodin, Hunyuan 3.x): through their own API
     or MCP, or ComfyUI's partner nodes. Say the cost before spending it.
4. Every run writes `<out>.gen.json` (host, model, seed, steps). Record the model and its licence:
   `pw.py manifest <dir> --add-tool "<model>" --tool-version <v>`.
5. Look: `pw.py inspect work/raw.glb` then `pw.py render work/raw.glb --out renders/raw`. Compare the sheet with
   the reference: the back and the underside are guesses; extra limbs, melted thin parts and fused gaps are
   common. Regenerate with another seed or better views before fixing by hand. Painted letters and numbers bake
   as smears and colours drift: `pw.py mark` erases and redraws the marking and moves the colour to the photo's
   (L-003; [figures for video](../polywright/references/figures-for-video.md)).

Raw output is unscaled, dense (hundreds of thousands of triangles), often non-manifold, without UVs, Y-up. It is
never game-ready and never print-ready as is: scale and finish it (polywright-finish, polywright-print).

## Step 3: code

Write a script that builds the object from named parts with real dimensions, run it, look at it, fix it:

- bpy: `pw.py bpy build.py -- --out work/model.blend` (traps by Blender version: polywright-blender).
- build123d or CadQuery (Python) or OpenSCAD (`openscad -o out.stl model.scad`, Manifold backend) for solids:
  watertight by construction, exports STEP for CAD and STL or 3MF for printing.

Put checks in the script (overall size, part gaps, wall thickness, part count) and print them; agents fix
crashes from tracebacks well, but shape errors only from measurements and renders. Two retries on a traceback,
then rethink.

## Step 4: textures for a generated or coded mesh

TRELLIS.2 and Pixal3D bake PBR textures in their workflow. For an untextured mesh: TRELLIS.2's
shape-conditioned texture stage, StableGen (Blender add-on on a ComfyUI backend, GPLv3) projecting SDXL or Flux
from cameras, or plain materials from CC0 libraries (polywright-references). Hunyuan 2.1 paint needs about 21 GB.

## Licences (record per run)

TRELLIS.2, Pixal3D, TripoSG, PartCrafter: MIT. Hunyuan3D open weights: Tencent community licence (not licensed
in the EU, UK or South Korea; 1M MAU cap; outputs may not train other models). SF3D and SPAR3D: Stability
community licence (free under USD 1M revenue). Hosted: the plan's terms. Research-only weights (PartPacker, Lyra,
CHORD) stay out of anything shipped. Stores require AI disclosure (polywright routes reference).

## Maintenance

Evergreen unit, tier `fast` (models and licences change monthly). Companions: [RESEARCH.md](RESEARCH.md),
[CHANGELOG.md](CHANGELOG.md), [LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md) with `evals/evals.json`,
[MAINTENANCE.md](MAINTENANCE.md), state in `evergreen.json`. Read `evergreen.json` at each use; refresh when due.
