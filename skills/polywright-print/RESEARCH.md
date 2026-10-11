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
