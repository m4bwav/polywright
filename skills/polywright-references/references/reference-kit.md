# Reference kit: prompts and checks

Prompt templates for image models, per kind of reference, and the checks to run before a reference is used.
Back to [SKILL.md](../SKILL.md). Sources: polywright research notes of 2026-10-11 (generative-3d section 2,
craft-and-academics section 4); prompt wording from Scenario's turnaround help and template sites (secondary).

## Templates

Replace `<subject>` with a concrete description: material, era, size words, colours. Keep the same seed and
wording across views of one subject.

**Hero image for image-to-3D (one view)**

    <subject>, single object, whole object in frame and centred, filling about two thirds of the frame,
    three-quarter front view from slightly above, neutral studio product photograph, plain solid white
    background, soft even diffuse lighting, no cast shadow, sharp focus, true proportions, no text, no logo

**Orthographic product or vehicle views**

    <subject>, orthographic technical drawing style, <front elevation | side elevation | top plan | back
    elevation>, flat even lighting, plain white background, centred, no perspective, no props, no text

**Character turnaround sheet**

    character turnaround sheet of <subject>, front view, side view, back view, orthographic, neutral A-pose,
    arms 30 degrees down, consistent proportions, same height, aligned on one ground line, plain light grey
    background, even studio lighting, no shadows, no perspective, full body

Generators want one view per image: split a sheet into separate square images, same scale, before meshing.

**Building elevation**

    <building> <north|south|east|west> facade, straight-on orthographic elevation, daylight, no perspective,
    no people, no cars, plain sky

**Seamless material**

    seamless tileable texture of <material>, top-down, flat even light, no shadows, no perspective,
    uniform scale, photographic, 2048x2048

**Terrain height map** (for a made-up landscape)

    top-down greyscale height map of <terrain>, white is high, black is low, smooth gradients, no text

Load it in Blender with a Displace modifier on a subdivided plane, or as a grid in `pw.py`'s place pipeline
(Grid class), and say in the manifest it is invented terrain.

## Checks before use

| Check | How | Fail means |
|---|---|---|
| One object, plain background | look; `pw.py gen` runs rembg if installed | background clutter becomes geometry |
| No strong perspective | straight edges stay parallel | generator bakes in the distortion |
| Flat light | no hard shadow on the object | shadows bake into albedo and dents into shape |
| Views agree | same proportions, limb and item count, nothing re-aimed, colours close | drop or repaint the view |
| Scale known | a dimension or a height bar | the model ends up the wrong size |
| Licence | generated: model and seed in the manifest; found: author and licence | stores and print sites ask |

## Board layout for a human

Front, side, back in one row on a shared ground line; top plan below; material swatches and close-ups to the
right; dimensions written on the board. PureRef 2.1 (February 2026) adds grids and shapes for this.
