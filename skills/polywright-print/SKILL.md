---
name: polywright-print
description: "Use whenever a model is going to a 3D printer or a slicer complains: one watertight solid in millimetres (pw.py printable, union), FDM and resin design rules (walls, overhangs, clearances, text), splitting with pins, multi-colour 3MF (pw.py 3mf), terrain tiles and miniatures, slicer CLIs. Use on 'make this printable', '3D print this', 'as a 100 mm figure', 'game model to STL', 'is this STL watertight', 'non-manifold', 'split to fit the bed', 'multi-colour print'. Printer-specific settings go to a printer or slicer skill when installed. Also 'refresh polywright-print'."
---

# polywright-print

A slicer needs one closed volume with a definite inside, at real size in millimetres, with nothing thinner than
the nozzle can draw. Games and generators give open shells, overlapping parts and paper-thin details.
Back to the hub: [../polywright/SKILL.md](../polywright/SKILL.md). Rules in depth: [references/dfam.md](references/dfam.md).

## Step 1: size first

Pick the finished size before anything else: everything thinner than about 0.9 mm (two perimeters at 0.4 mm)
at that size disappears. Typical: a desk model 80 to 150 mm; a 32 mm miniature (about 1:56); a 200 mm terrain
tile. The build plate limits a single piece (256 x 256 x 256 mm on Bambu P1S/X1-class, smaller on many others).

## Step 2: make it one solid

Already solid and closed (code CAD, a print-site model): check it (Step 4) and skip this.
Anything else:

```
python ../polywright/scripts/pw.py printable in.glb out/model.stl --size-mm 120 [--size-axis height] \
    [--wall-mm 1.0] [--voxel-mm 0.2] [--base-cut-mm 0.6] [--drop interior,glass_inner] [--blend work/print.blend]
```

What it does: drops named parts, flattens the hierarchy, scales to `--size-mm`, gives open shells a wall
(inward, even offset off: even offset makes spikes), voxel-remeshes everything into one closed surface, keeps
the largest part, fills a hollow shell's inside (below), clamps a flat base, decimates, cleans. Voxel size defaults to size/500; smaller keeps
detail and costs memory as (size/voxel)^3. Tested 2026-10-11: a generated 405k-triangle fountain with 3,048
non-manifold edges became one watertight 80 mm solid (45.8 cm3) in seconds.

Image-to-3D meshes are often a thin double-walled shell with air inside, open through small gaps; a remesh
keeps them hollow with walls a slicer drops. `printable` seals gaps up to `--seal-mm` (1 mm), floods the
outside and fills what it cannot reach when that is over a tenth of the volume ("hollow shell: filled" in
`steps`). Grooves narrower than the seal fill too: lower `--seal-mm` to keep them, `--hollow` to skip. Tested
2026-10-17: a TRELLIS.2 figure at 60 mm went from 74% of its surface under 0.9 mm (1.76 cm3) to 4.8% (3.43 cm3).

Several closed parts that should fuse (a body and a base, buildings on terrain): `pw.py union in out.stl`
(Manifold solver, EXACT fallback). Game models with inner skins, missing panels or through-slits need more
than this: drop the inner parts and plug gaps first, then remesh; look at a render after every step.

## Step 3: design for printing (fix in the model, not the slicer)

- Walls 1.2 to 1.6 mm for anything structural; nothing under 0.9 mm; thin spears, swords, antennas thickened.
- Overhangs over about 45 degrees need support; chamfer bed-facing edges (not fillets); teardrop horizontal holes.
- Clearances: 0.3 mm for parts that move, 0.2 to 0.3 mm sliding, 0 to 0.1 mm press fit; holes print small (add
  0.1 to 0.3 mm). Print a tolerance coupon before a tight assembly.
- Text at least 0.5 mm stroke and 0.4 to 0.6 mm deep.
- Orientation for strength: layers are weakest in Z.
- Too big: split along natural lines with pins (3 mm pin, 3.3 mm hole) or dovetails; or the slicer's Cut tool
  with connectors.
- Terrain and towns: exaggerate height (2 to 5 for flat places), base 2 to 3 mm, buildings at least 1.2 mm,
  trees as lollipops on 1.5 mm trunks; `pw.py place --print-mm` does this (polywright-capture).
- Miniatures: heroic scale (bigger heads, hands, weapons); FDM at 0.4 mm loses faces: 0.2 mm nozzle or resin.

## Step 4: check, then hand over

```
python ../polywright/scripts/pw.py check out/model.stl --target print-fdm      # watertight, one part, fits the bed, thin walls
python ../polywright/scripts/pw.py render out/model.stl --out renders/print    # look for thin parts and lumps
python ../polywright/scripts/pw.py 3mf out/model.stl [out/roof.stl ...] --out out/model.3mf   # one object per colour
```

Deliver the STL (the verified artefact) and a 3MF (what slicers prefer; geometry only, the slicer applies its
defaults). A slicer CLI can open, orient, arrange and slice it: Bambu Studio
`bambu-studio --export-3mf out.3mf in.3mf` (also `--orient`, `--arrange 1`, `--slice 0`), PrusaSlicer and
OrcaSlicer have similar CLIs; judge success by the exit code and Bambu's `result.json`, not the console. When a
printer-specific skill or a 3MF-settings skill is installed, hand it the 3MF for plate, filament and process
settings. With Blender found, `check` measures wall thickness (rays inward from 20,000 surface points):
`min_feature` warns when over 0.5% of the surface is thinner than 0.9 mm and lists the thinnest spots
(coordinates in the file's units). Without Blender it says `unchecked`; say so and look at the render.

Physical items made from OpenStreetMap data carry the credit on the base or packaging.

## Maintenance

Evergreen unit, tier `moderate`. Companions: [RESEARCH.md](RESEARCH.md), [CHANGELOG.md](CHANGELOG.md),
[LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md) with `evals/evals.json`, [MAINTENANCE.md](MAINTENANCE.md),
state in `evergreen.json`. Read `evergreen.json` at each use; refresh when due.
