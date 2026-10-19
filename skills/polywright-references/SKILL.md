---
name: polywright-references
description: "Use whenever reference images, views or textures for a 3D model are needed, before modelling or image-to-3D: orthographic front, side and back views with a height bar, A-pose turnarounds, multi-view sets, blockout renders repainted into consistent views, seamless textures and quick normal/height/roughness maps (pw.py texture). Use on 'what references do I need', 'reference sheet', 'front side back views', 'turnaround', 'seamless texture', 'PBR maps from this photo'. Not for flat graphic patterns (wrapping paper, fabric, wallpaper prints). Meshing is polywright-generate. Also 'refresh polywright-references'."
---

# polywright-references

References decide most of a 3D result: an image-to-3D model copies its input's lighting, perspective and
mistakes; a modeller or a bpy script needs dimensions and views. Gather or generate them first, put them in
the asset's `refs/`, record each with `pw.py manifest --add-source` (generated ones name the model and seed).

Back to the hub: [../polywright/SKILL.md](../polywright/SKILL.md). Prompt templates and checks:
[references/reference-kit.md](references/reference-kit.md).

## Step 1: what this model needs

| Model | Collect (real) | Generate (imagined or missing) |
|---|---|---|
| Real object | photos from 6 sides with a ruler in the plane, close-ups, real dimensions (maker's sheet, Wikipedia, a tape) | orthographic clean-ups only if photos are poor |
| Vehicle, product, furniture | blueprints or CAD drawings (check one known dimension), maker's dimensions | front, side, top elevations in technical-drawing style |
| Building | footprint (OSM), height or floor count, photos of each face, roof shape | elevations per face, roof plan |
| Real place | map extract, elevation, aerial photo, ground photos of landmarks | none: places come from data (polywright-capture) |
| Imagined prop | style references | a three-quarter hero image, then front/left/back/right at the same scale |
| Character or creature | style and costume references | turnaround: front, side, back, three-quarter, A-pose, height bar, plain background |
| Surfaces (walls, ground, terrain) | photo of the material, flat and evenly lit | seamless tileable albedo, then maps (Step 4) |

Always add a **scale reference**: a known dimension, a 1.8 m human silhouette, a height bar on the sheet.

**A history research pack** (a folder holding `answer.md`, `refs/index.json` and `anachronism.md`, made by the
historywright plugin) is already a valid asset folder: start from it, do not search again. Read
`refs/index.json`: each reference has the object's own date, place, institution, accession number and licence.
Use only references whose `object_date` fits the brief's period. Keep a reference with `nc: true` out of a
commercial model. Check every generated view against `anachronism.md` before it is meshed.

## Step 2: generate the views (rules that matter)

Ask the image tool for: one object, centred, filling about two thirds of the frame; plain white or light grey
background; flat, even, shadowless light; no strong perspective (long lens or orthographic look); 1024 px or
more; no text. Characters stand in a relaxed A-pose (arms 30 to 45 degrees down, legs slightly apart): T-poses
distort proportions and action poses fail in generators and riggers. Templates per kind are in the kit.

For consistent extra views from one image, an image-edit model with a multi-angle adapter (Qwen Image Edit
with a Multiple Angles LoRA, 2025-2026) keeps identity better than prompting each view; expect colour drift and
colour-match each view to the front. Check every generated view against the front: same proportions, same
number of arms, same items, nothing re-aimed. Drop a view that disagrees; a wrong back view is worse than none.
Name a real object's colour from the photo's pixels (median hue, saturation, value), not from a word: the edit
model follows the word over the picture (L-003). Back views tend to copy a front marking onto the back.

A ready workflow for a Z-Image Turbo host: [references/zimage-reference.api.json](references/zimage-reference.api.json)
(`{SUBJECT}` placeholder; tested 2026-10-11).

## Step 2b: a designed prop's sheet comes from the model

When the prop is designed (a weapon, a tool, a vehicle part described in words or on a fan sheet) and text
prompts keep giving half the shape, stop prompting: build it with a bpy script (polywright-blender recipe
"A designed prop from a written description") and render the sheet from the model, side and top orthographic
on flat mid-grey, Cycles on the CPU when the GPU is busy. A model is exact, re-renders in seconds after each
note, and the same file later composes the prop into pictures (hub: "Compose a model into a picture"). Raise
the side camera 10 to 15 degrees when parts come in mirror-image pairs, or one hides behind the other.

## Step 3: views from a blockout (when views keep disagreeing)

Build a rough blockout (primitives, or a first front-only generated mesh), render it with
`pw.py render <file> --out refs/blockout --views front,right,back,left --color clay`, then have an image-edit
model repaint each grey render in the subject's colours and detail (image-to-image with the render as the
first reference and the front view as the second). Only the camera moves, so nothing can be re-aimed or grow
extra limbs; the back can only show what the blockout implies. Feed the repainted set to multi-view generation.

## Step 4: textures and materials

- Prefer a CC0 material (Poly Haven, ambientCG) over a generated one.
- Generated tileable: ask for "seamless, tileable, top-down, flat even light" at a power of two, then
  `pw.py texture <img> --out refs/tex --seamless` (offset-blend seams) and look at a 2x2 tiling.
- Quick maps from a photo or albedo: `pw.py texture <img> --out refs/tex [--convention opengl|directx]`
  writes height, normal and roughness derived from luminance. Fine for props and terrain, wrong for measured
  materials. Normal maps: OpenGL (Y+) for Blender, Unity, Godot, glTF, three.js, Roblox; DirectX (Y-) for Unreal.
- Baked shadows in a photo become baked shadows in the albedo: fix upstream with flat light, or delight.

## Step 5: put them to work

- In Blender: reference images as empties in front, right and top views, scaled to a known dimension
  (orthographic renders from `pw.py render` report `metres_per_px`); recipe in polywright-blender.
- For image-to-3D: square, padded, 1024 px; `pw.py gen` pads and removes backgrounds itself. Judge the picture
  before the GPU run, and what to fix in it rather than in the mesh: [references/images-for-3d.md](references/images-for-3d.md).
- On a board (PureRef 2.1) for a human: group by view, note dimensions on the board.

## Maintenance

Evergreen unit, tier `fast`. Companions: [RESEARCH.md](RESEARCH.md), [CHANGELOG.md](CHANGELOG.md),
[LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md) with `evals/evals.json`, [MAINTENANCE.md](MAINTENANCE.md),
state in `evergreen.json`. Read `evergreen.json` at each use; refresh when due.
