# Design for printing (FDM first, resin notes)

Back to [SKILL.md](../SKILL.md). Source: polywright research note `2026-10-11-craft-and-academics.md` section
5b; [verified] = Prusa knowledge base read 2026-10-11; [secondary] = vendor or forum; [rule] = practitioner
rule of thumb, unverified.

## Geometry checklist

- [ ] Watertight and manifold: every edge in exactly two faces, normals outward, no self-intersections
      (union overlapping parts). `pw.py check --target print-fdm`.
- [ ] Units in millimetres (STL has none; 3MF does).
- [ ] Walls: two perimeters at 0.4 mm is about 0.9 mm, three 1.35 mm, four 1.8 mm; walls between one and two
      perimeters print badly [verified]. 1.2 mm minimum for structure, 1.6 mm recommended [secondary].
- [ ] Detail: under about 0.4 mm in XY vanishes. Text at least 0.5 mm stroke, 0.4 to 0.6 mm deep, 8 pt bold or
      larger [rule].
- [ ] Overhangs at most 45 degrees from vertical unsupported (45 to 60 with good cooling) [verified]; 45-degree
      chamfers or teardrop holes instead of flat ceilings.
- [ ] Bridges under 10 to 20 mm for clean results [secondary].
- [ ] Bed-facing edges chamfered, not filleted [verified]; a 0.2 to 0.3 mm chamfer on the first layer edge hides
      elephant's foot.
- [ ] Holes undersized by 0.1 to 0.3 mm: enlarge or drill [secondary].
- [ ] Clearances: moving parts at least 0.3 mm [verified]; sliding 0.2 to 0.3; press 0.0 to 0.1; print-in-place
      hinges 0.3 to 0.5; under 0.1 mm fuses [secondary].
- [ ] Orientation: stress along the layers, not across them.
- [ ] Split: to fit the bed, to avoid supports, to put the best face up; pins (3 mm pin in a 3.3 mm hole),
      dovetails or holes for 1.75 mm filament dowels; seams along natural lines.
- [ ] Cylinders: enough segments (a 16-sided cylinder prints as a polygon) [verified].
- [ ] FDM does not need hollowing (infill does it); resin does.

## Scale models

- 32 mm miniatures are about 1:56 to eye height; exaggerate hands, heads and weapons; thicken blades to
  1.2 mm or more; a 0.2 mm nozzle or resin for faces.
- Terrain: smooth the elevation before exaggerating; 1 to 2 times for mountains, more for flat land (30 times
  appears on commercial state maps at tiny scales); base 2 to 3 mm; tile with keys.
- Buildings: thicken walls to the two-perimeter minimum rather than true scale; window recesses 0.4 mm or deeper.
- Cars and game models: one solid body; mirrors and spoilers thickened or printed separately at 1:24 and up.

## Multi-colour (AMS and other changers)

Separate objects in one 3MF (one filament each; `pw.py 3mf a.stl b.stl --out x.3mf`) or paint in the slicer.
Each colour change purges about 2 to 5 g [secondary]: change colours by layer where possible (strata terrain).

## Slicer CLIs (2026-10)

| Slicer | CLI facts |
|---|---|
| Bambu Studio 2.08 | `--orient`, `--arrange 1`, `--scale f`, `--slice 0`, `--export-3mf file`, `--load-settings "machine.json;process.json"`, `--load-filaments`, `--outputdir`, `--debug 0-5`; writes `result.json` (`return_code`, `error_string`). Verified 2026-10-11 on Windows: `--export-3mf` re-exported a pw.py 3MF with "Success." No repair flag. Stock profiles through `--load-settings` have failed on Windows before: export plain, set the profile in the GUI or with a settings skill |
| PrusaSlicer 2.9 | `--repair`, `--export-3mf`, `--export-gcode` (flags from memory; run `--help`) |
| OrcaSlicer 2.4 | Bambu Studio-like CLI |

## Resin

Hollow solids above a few centimetres with 2 to 3 mm walls and drain holes; tilt 30 to 45 degrees; supports on
hidden faces; details to about 0.3 mm. Bed sizes vary widely: put the real one in the brief.
