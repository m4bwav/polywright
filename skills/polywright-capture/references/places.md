# Places from open data

Back to [SKILL.md](../SKILL.md). Sources: polywright research note `2026-10-11-reality-capture.md` section 4,
and runs of `pw.py place` on two real parks (2026-10-11): a 540 x 420 m US neighbourhood park (249 buildings, 1 m
lidar, 6 seconds, a watertight 150 mm print tile) and a 400 m box around Central Park's Bethesda Terrace, New York.

## Data sources

| Data | Source | Licence and credit |
|---|---|---|
| Streets, paths, buildings, land use, trees, benches | OpenStreetMap via Overpass (`overpass-api.de`, `overpass.kumi.systems`, `overpass.private.coffee`) | ODbL: "Map data (c) OpenStreetMap contributors" |
| Building footprints with estimated heights | Overture Maps (`pip install overturemaps`; `overturemaps download --bbox=W,S,E,N -f geojson --type=building`) | buildings ODbL; places CDLA Permissive 2.0 |
| US bare-earth elevation, 1 m | USGS 3DEP ImageServer `exportImage` (what `pw.py` uses) or The National Map tiles | public domain |
| Global elevation | Mapzen terrain tiles on AWS (`elevation-tiles-prod/terrarium`, what `pw.py` falls back to) | mixed sources; credit per tilezen/joerd attribution |
| Global 30 m DSM | Copernicus GLO-30 (AWS open data, OpenTopography) | free; long credit line (DLR, Airbus, EU/ESA) |
| Aerial photos | national programmes (US NAIP is public domain); commercial basemap tiles have their own terms | check before shipping a texture |
| Google Photorealistic 3D Tiles | viewing only | never export, cache or trace |

Elevation traps: a DSM (Copernicus) includes trees and roofs as bumps; prefer a bare-earth DTM (3DEP). Lidar has
voids under water. Degrees treated as metres stretch everything: `pw.py` projects to local metres.

## Facts learned running `pw.py place`

- Overpass can answer HTTP 200 with an HTML error page: the first byte must be `{` (the fetcher checks).
- `>; out skel` returns whole ways that run far outside the box: clip lines and polygons to the box
  (`clip_line`, `clip_ring`) or roads stick out of the scene by hundreds of metres.
- In a US city OSM often carries lidar-derived `height` on most buildings (203 of 249 in the test); the rest get
  a default by type. `place.json` says how many were guessed.
- A terrain block whose rim runs clockwise needs its walls and bottom wound the other way; a Manifold union of
  an inside-out block silently drops every operand. The block is now tested closed and outward.
- Workbench top views of a flat-roofed tile need the cavity distance scaled to the model, or roofs vanish into
  the ground (render does this).
- overpass-api.de answers 406 Not Acceptable to generic user agents (curl, "Mozilla/5.0") and accepts a
  descriptive one; it allows about 4 queries at a time per address (`/api/status`). A query for every element in a
  dense city box timed out (504): ask only for the tags you use.
- A box query returns only ways with a node in the box, so a park, wood or lake that encloses the whole box is
  missing; `is_in` at the centre (land-use tags only) brings it back.
- Multipolygon outlines are split over many ways: stitch them end to end into rings; inner rings are holes.
- Paint ground classes from the largest area to the smallest, so islands, pitches and ponds win over the lake,
  park or wood around them.
- Lidar over water is noise: flatten each water body to its lowest grid point (hydro-flattening).

## A park into a game level

1. Area: the park polygon plus 50 to 100 m of context (`--center` and `--size-m`, or `--bbox`).
2. `pw.py place`; look at `scene.glb` against an aerial photo.
3. Engine terrain, when a mesh is not wanted: Unity heightmaps are square 2^n+1 (513, 1025, 2049) 16-bit RAW;
   Unreal landscapes prefer 1009, 2017, 4033; Roblox's terrain editor imports a heightmap image, or build terrain
   from the grid in Luau (prior knowledge for exact sizes; check the engine docs).
4. Objects: place your own low-poly kit at OSM points (trees, benches, bins, lamps); do not scan every tree.
5. Landmarks: model from photos and measurements, or photogrammetry for a statue or fountain.
6. Roblox scale: 1 stud = 0.28 m, so multiply metres by 3.57 (roblox-agent builds places from this kind of data).
7. Credits: OSM in the credits or splash screen.

## The same park as a print

1. Pick the size first: 400 m at 1:2000 is 200 mm; a 2 m path is then 1 mm, a 10 m tree 5 mm, a bench nothing.
2. Exaggerate height: a flat park needs 2 to 5 times or more; print the factor on the base.
3. `--print-mm 200 --exaggerate 3 --base-mm 3 --print-roads` gives one watertight `print.stl`.
4. Colour (AMS): split terrain, buildings, roads and water into separate objects in a 3MF (one per filament),
   or colour by layer height. Features under about 0.8 mm (two lines at 0.4 mm) will not print.
5. Trees: stylised lollipop or cone on a 1.5 mm trunk, or canopy blobs; never scanned trees.
6. Bigger than the bed: tile it into pieces with pins (polywright-print).
7. Attribution goes on the packaging or the base of a physical item with OSM data.
