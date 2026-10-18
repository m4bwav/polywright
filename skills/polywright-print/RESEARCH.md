# Research: polywright-print

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Making models printable: watertight solids, DfAM for FDM and resin, splitting, multi-colour 3MF, terrain and miniatures, slicer CLIs. Tier `moderate`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Two perimeters at 0.4 mm is about 0.9 mm; 1.2 to 1.6 mm for structure; overhangs to 45 degrees; 0.3 mm clearance for moving parts; chamfer bed edges (Prusa KB, 2026-10-11).
- Voxel remesh after an inward solidify closes any game or generated mesh; a generated 405k-triangle fountain became one watertight 80 mm solid (2026-10-11).
- Bambu Studio CLI re-exported a pw.py 3MF with result.json Success (2026-10-11); stock profiles through --load-settings have failed on Windows before.

## Open questions

- A wall-thickness measurement in pw.py (ray casting) instead of 'look at the render'?
- Bambu Studio CLI slicing with a P1S profile from the command line
- Tolerance coupon results on the owner's printer

## Search plan

Subject:

- Prusa and Bambu knowledge bases on design rules

Tooling:

- Bambu Studio, PrusaSlicer, OrcaSlicer CLI release notes; text-to-cad dfam-check

Practice:

- r/3Dprinting and r/PrintedMinis RSS; MakerWorld AI policy

Testing:

- pw.py printable and union on fixtures; slicer exit codes

Best sources: project repositories' releases and READMEs, official docs, dated practitioner posts. Noisy: vendor SEO comparison pages (mark them third party).

## Findings log

### R-20261017-2 · 2026-10-17 · Subject: supports and slicing from the modeller's side
- summary: Bambu Studio defaults (BambuHub, 2026-10-04): supports off, Tree (auto), threshold 30 degrees from horizontal, top Z 0.2 mm (0 only with a support filament), XY 0.35 mm, style resolving to Tree Organic or Tree Hybrid; hybrid puts a grid under large flat areas. Support painting marks enforcers and blockers, paints vertical faces since 1.10.0, and blockers can be placed objects (wiki, 2026-04-16). The Cut tool has planar and dovetail modes with connectors and names reduced supports as a reason to cut (wiki, 2026-09-15). Variable layer height: 0.08 to 0.28 mm on a 0.4 nozzle, adaptive and smooth, one prime tower only when objects share a profile (wiki). Purge: the prime tower rises to the last change layer, flipping a part saved about 40%, changes per layer are colours minus one, flush into infill or objects needs the tower (wiki, 2026-02-11). PrusaSlicer organic supports touch only at branch tips. Resin: at least two drain holes, minimum hollow wall 1 mm in PrusaSlicer, cupping, tilt 30/45/60 compared (Elegoo/Chitubox), Lychee 7.5.4/7.5.5 (2025-12-17) reworked auto support. Miniatures: resin about 0.05 mm XY against 0.1 mm FDM; 32 mm figure designers list a 0.2 mm nozzle at 0.08 mm layers. Pre-supported means creator-chosen orientation and supports, often with a Lychee project.
- track: subject
- sources: https://bambuhub.net/articles/bambu-studio-supports, https://wiki.bambulab.com/en/software/bambu-studio/support-painting, https://wiki.bambulab.com/en/software/bambu-studio/cut-tool, https://wiki.bambulab.com/en/software/bambu-studio/adaptive-layer-height, https://wiki.bambulab.com/en/software/bambu-studio/reduce-wasting-during-filament-change, https://help.prusa3d.com/article/organic-supports_480131, https://help.prusa3d.com/article/hollowing_117285, https://formlabs.com/global/blog/how-to-hollow-out-3d-models/, https://wiki.elegoo.com/mars/model-orientation-and-support-generation-in-chitubox, https://lychee.co/changelogs/lychee-slicer-7-5-4-and-7-5-5, https://evezone.evetech.co.za/build-lab/fdm-vs-resin-for-tabletop-miniatures-which-should-you-print, https://makerworld.com/en/models/3372170-traveler-32mm, https://pixup3d.com/blog/pre-supported-vs-unsupported-stl-which-should-you-download/
- magnitude: minor (new reference)
- applied: C-20261017-3

### R-20261017-1 · 2026-10-17 · Tooling: how Blender's 3D-Print Toolbox measures wall thickness
- summary: the Print3D Toolbox extension (1.4.1, GPL-3.0-or-later) checks thickness by casting a ray from six random points on every face backwards along the face normal, up to the minimum thickness, and marks the face (and the face hit) as thin. polywright's check uses the same idea, written fresh for the MIT licence: area-weighted surface points, a BVH tree over all objects, the first exit-facing hit as the local thickness, faces pointing back at the ray stepped over.
- track: tooling
- sources: https://projects.blender.org/extensions/print3d_toolbox (source/lib.py `bmesh_check_thick_object`, source/blender_manifest.toml), read 2026-10-17
- magnitude: minor (new measurement, method of an established tool)
- applied: C-20261017-1

### R-20261011-2 · 2026-10-11 · Testing: Printable fountain and 3MF into Bambu Studio
- summary: printable gave a watertight single part; 3mf passed testzip; Bambu Studio CLI export returned Success.
- track: testing
- sources: local run 2026-10-11
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: DfAM checklist
- summary: Walls, overhangs, bridges, clearances, holes, text, orientation, splitting, multi-colour, scale models.
- track: subject
- sources: [2026-10-11-craft-and-academics.md](../../ai-docs/research/2026-10-11-craft-and-academics.md)
- magnitude: n/a (initial)
- applied: C-20261011-1
