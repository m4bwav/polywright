# Research: polywright-capture

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Real things and places into 3D: OSM and elevation places, photogrammetry, splats, scanners, measurements, scan cleanup. Tier `moderate`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Places: USGS 3DEP 1 m bare-earth (US) or Copernicus GLO-30 (global DSM) plus OSM features; pw.py place does OSM, USGS or terrarium tiles, land-use colouring, building heights, roads, trees and a print tile (verified on two real parks, 2026-10-11).
- Google Photorealistic 3D Tiles cannot be exported, cached or traced; new EEA-billed projects cannot use them at all since 2025-07-08.
- Photogrammetry: RealityScan 2.2 (free under USD 1M, headless CLI) or COLMAP 4.2 plus OpenMVS; feed-forward VGGT and relatives as a fallback for sparse photos (only VGGT-1B-Commercial is licensed for commercial use).
- Splats show places best but are not meshes; KHR_gaussian_splatting is listed as ratified; splat-transform converts formats and builds collision.

## Open questions

- Does Overture's building height beat OSM where OSM has no height tags?
- Is the 4 km2 default limit right for Overpass load?
- Does pw.py place need NAIP or other open imagery for ground textures?

## Search plan

Subject:

- USGS 3DEP and Copernicus DEM news; Overture releases
- Google Map Tiles API policies page

Tooling:

- RealityScan, COLMAP, OpenMVS, Brush, splat-transform releases
- `path:SKILL.md photogrammetry` and `path:SKILL.md openstreetmap` on GitHub

Practice:

- r/photogrammetry and r/GaussianSplatting RSS
- radiancefields.com news

Testing:

- tests/test_pw.py offline place fixture; a real place run per refresh

Best sources: project repositories' releases and READMEs, official docs, dated practitioner posts. Noisy: vendor SEO comparison pages (mark them third party).

## Findings log

### R-20261017-1 · 2026-10-17 · Subject: OSM Simple 3D Buildings (heights, parts, roofs)
- summary: `height` runs from the lowest ground point to the roof top and includes the roof; `min_height` is the clearance under a part and `building:min_level` its levels form; facade height is height minus `roof:height`; `roof:levels` are not counted in `building:levels`; when a building has `building:part` areas its outline is not used for 3D; ridges run along the longest side unless `roof:orientation` says otherwise; `roof:direction` is where the roof's front faces. The page gives no default storey height or roof height (polywright uses 3.2 m and a 30 degree pitch, labelled as its own).
- track: subject
- sources: https://wiki.openstreetmap.org/wiki/Simple_3D_Buildings (last edited 2026-10-15), read 2026-10-17
- magnitude: minor (new feature)
- applied: C-20261017-1

### R-20261011-3 · 2026-10-11 · Testing: pw.py place on a real park
- summary: 249 buildings, 203 with OSM heights, 1 m lidar, 6 s; print tile unioned watertight after two fixes (clipping, block winding).
- track: testing
- sources: local run 2026-10-11
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-2 · 2026-10-11 · Tooling: Capture engines October 2026
- summary: RealityScan 2.2, COLMAP 4.2 with built-in global mapper, OpenMVS 2.4, Postshot, Brush, splat-transform 3.10.
- track: tooling
- sources: [2026-10-11-reality-capture.md](../../ai-docs/research/2026-10-11-reality-capture.md)
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: Places from open data and the Google tiles ban
- summary: DEM plus OSM is the scalable, licensed route; Google tiles are view-only.
- track: subject
- sources: [2026-10-11-reality-capture.md](../../ai-docs/research/2026-10-11-reality-capture.md)
- magnitude: n/a (initial)
- applied: C-20261011-1
