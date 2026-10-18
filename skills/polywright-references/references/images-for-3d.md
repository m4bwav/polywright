# Images for 3D: what a picture must give the mesher

Back to [../SKILL.md](../SKILL.md). Prompt templates: [reference-kit.md](reference-kit.md). Generators, VRAM and timings:
[../../polywright-generate/references/generators.md](../../polywright-generate/references/generators.md).
This page is the mesh side: what each generator does with a picture, how to judge one before spending GPU
time, and what to fix in the picture rather than in the mesh. Making the picture is the job of an
image-generation skill or ComfyUI. Sources: [../RESEARCH.md](../RESEARCH.md) R-20261017-1.

## What each generator does with the picture

| Generator | Reads | Wants | Breaks on |
|---|---|---|---|
| TRELLIS.2 (single image) | the whole image through DINOv3 features | one object, square, background removed (the ComfyUI template runs BiRefNet and re-centres) | clutter, cast shadows, thin and see-through parts |
| Pixal3D (single image) | pixels back-projected on the model; MoGe estimates depth and field of view | a long-lens picture near eye level: the front copies the input 1:1 | a wide lens or high camera (the mesh leans by the camera's elevation: `pw.py convert --level`) |
| Pixal3D multi-view (`pixal3d_multiview_int8_convrot`, separate download) | one turnaround sheet: front, side and back on one canvas | views at one scale on one ground line, subject separated from the background | views that disagree |
| Hunyuan3D-2 / 2mv | one front image, or front, left, back, right as separate images | background already removed, views at 0, 90, 180, 270 degrees | missing views are fine; wrong ones are not |
| Hosted (Meshy, Tripo, Rodin, Hunyuan 3.x) | 1 to 8 images | Meshy: at least 512 px, near-orthographic or telephoto, even light; front, side, back and 3/4 under one light | cluttered scenes merge into one mesh |

None of the open model cards (TRELLIS.2, Hunyuan3D-2) states input rules; the table comes from the ComfyUI
tutorials, the hosted services' guides and the tests in generators.md.

## Judge the picture before the GPU run

A run costs 100 to 380 s on a 16 GB card. Two minutes of looking saves most failed runs:

1. **Silhouette.** Mat the picture and look at the mask alone. One connected shape, nothing touching the
   frame, no gaps the object does not have. A part hidden behind another will be missing or fused.
2. **Light.** No cast shadow, no dark side darker than the object's darkest colour. Baked shadow becomes
   black patches in the texture and a dent in the shape.
3. **Camera.** Straight edges that should be parallel stay parallel; the horizon of the object sits near
   its middle. Wide-angle pictures make heads big and feet small in the mesh.
4. **Thin parts.** Anything thinner than about 1/100 of the object's height (straps, wires, hair strands,
   staffs, spokes) will melt, fuse or vanish: sparse voxels and Hunyuan's ShapeVAE smooth away what is
   thinner than one voxel.
5. **Materials.** Glass, liquid, chrome, glow, smoke and fur are open failure cases for every current
   generator. Plan to model those parts by code or swap the material.
6. **Views agree** (multi-view only): same proportions and part count, nothing re-aimed, colours close.

## Fix it in the picture or in the mesh

| Problem | Fix in the picture (cheap, before) | Fix in the mesh (after) |
|---|---|---|
| clutter or a second object | re-generate or mask it out | not worth it: separate meshes merge |
| cast shadow, dark side | re-light: flat even light | repaint the texture; the dent stays |
| tilt from a high camera | a lower, long-lens view | `pw.py convert --level` |
| thin parts (staff, strap, antenna) | leave them out or thicken them | add by code (bpy cylinder, curve) |
| glass, liquid, chrome | ask for a matte painted version | swap the material in Blender |
| hair, fur, feathers | sculpted locks or carved tufts | hair cards or a groom: a modelling job |
| wrong back or underside | add views; repaint a blockout (SKILL Step 3) | sculpt or mirror |
| lumpy flat surfaces, soft edges | rarely fixable in the image | remesh, decimate, boolean a clean plane |
| baked light in the albedo | flat light upstream | delight or repaint |

Rule: anything the generator cannot see or cannot resolve is cheaper to fix in the picture; anything
geometric and exact (flat faces, straight edges, thin rods, dimensions) is cheaper to fix in the mesh or
to build by code.

## Styles that mesh well

Mesh well: chunky stylised forms, toy and vinyl figurines, clay or resin statues, painted miniatures,
hand-painted game-asset renders, solid hard-surface props, matte surfaces with clear colour regions.
Mesh badly: wispy hair and fur, lace, chains, wires, glass, liquids, particles, mirror finishes, and
flat-colour line art with no shading (generators make it paper-thin). For a subject in a bad style,
ask the image side for "a painted resin figurine of ..." and keep the design, not the strands.

## Single image or multi-view

- **One image** for props, statues and anything whose back is plain or symmetric. Pick TRELLIS.2 for detail,
  Pixal3D when the front must match the picture exactly.
- **Multi-view** for characters, vehicles and anything with a different back. A wrong view is worse than
  none: drop it and mesh from the rest. When views keep disagreeing, paint them from a blockout render.
- Characters: relaxed A-pose, full length; local generators keep the pose they are shown.

## Background removal

`pw.py gen` pads and mats the picture itself, and the TRELLIS.2/Pixal3D template runs BiRefNet. Still check
the mask: white or pale objects on white lose their interiors, so ask for a light grey backdrop; soft hair
edges leave a halo that becomes a skin on the mesh. Turn the template's matting off only when the picture
already has a clean alpha.
