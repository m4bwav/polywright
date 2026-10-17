---
name: polywright-capture
description: "Use whenever a real place or real object must become a 3D model: a park, street, campus or terrain from OpenStreetMap and public elevation (pw.py place, game scene plus print tile), photos to a model (photogrammetry: RealityScan, COLMAP, OpenMVS), Gaussian splats, scanners, or modelling from measurements; then scan cleanup. Use on 'put this real park in my game', 'make a 3D map of', 'print a model of my town', 'scan this', 'photogrammetry', 'gaussian splat', 'model my house from measurements'. Imagined things are polywright-generate. Also 'refresh polywright-capture'."
---

# polywright-capture

Real things come from data, photos or measurements, never from a generator's guess. Pick the capture route by
subject, record every source with its licence, and keep real size in metres.

Back to the hub: [../polywright/SKILL.md](../polywright/SKILL.md). Depth: [references/places.md](references/places.md),
[references/photogrammetry.md](references/photogrammetry.md), [references/splats.md](references/splats.md).

## Pick the route

| Subject | Route | Why |
|---|---|---|
| A park, street, campus, neighbourhood, landscape | **place**: OSM + elevation (`pw.py place`), hero props captured or modelled | open data is to scale, licensed and covers everything at once |
| A manufactured object (furniture, product, vehicle, building) | **measure**: dimensions + orthographic photos, modelled in code or Blender | mostly flat planes; cleaner and faster than a scan |
| A sculpted or organic object you can walk around (statue, fountain, rock, stump) | **photogrammetry** | detail and colour a modeller cannot match |
| A whole scene to look at, not to play or print (backplate, web tour) | **Gaussian splat** | photoreal, fast to capture; not a mesh |
| A part that must fit (replacement knob, bracket) | **scanner** (structured light) or calipers + code CAD | 0.02 to 0.1 mm vendor accuracy; phone LiDAR is centimetre-grade |

## Places: `pw.py place`

```
python ../polywright/scripts/pw.py place --center LAT,LON --size-m 500 --out assets/<place>/work/place \
    [--dem auto|usgs|terrarium|flat] [--res 2] [--print-mm 200 --exaggerate 2 --base-mm 3 --print-roads]
```

- Data: OSM through Overpass (three mirrors, cached in `data/`), elevation from USGS 3DEP (US, 1 m lidar,
  public domain) or Mapzen terrain tiles (global), resampled to `--res` metres. Max 4 km2 by default.
- `scene.glb`: metres, +Y up, -Z north, origin at the centre, y=0 at the lowest ground. Ground coloured per
  land use (water, pitch, sand, playground, paved, wood, grass, park), buildings from OSM `height` or
  `building:levels` with `min_height`, `building:part` and roof shapes (gabled, hipped, pyramidal, skillion;
  others mapped to the nearest), roads and paths draped on the terrain, waterways, trees (OSM points plus
  scatter in woods).
- `place.json`: counts (how many building heights were guessed, which roofs were built), the elevation source, and the credit lines
  to ship ("Map data (c) OpenStreetMap contributors, ODbL" and the elevation credit).
- `--print-mm`: a closed terrain block with buildings (and roads) unioned into one watertight `print.stl`.
  Flat places need exaggeration (2 to 5 for a park); features under `--min-feature-mm` (1.2) are dropped.

Then: render (`pw.py render work/place/scene.glb --out renders/place --color material`) and compare with an
aerial photo; hand-model or capture the landmarks the data cannot give (a bandstand, a playground structure);
replace default-height buildings that matter. Engine heightmaps, imagery terms and the park checklist are in
[references/places.md](references/places.md).

## Objects from photos (photogrammetry)

Capture rules that never change: lock exposure, focus and white balance; f/8 to f/11, sharp; 60 to 80% overlap;
move around the object, do not pivot on the spot; no wind, no moving people; a scale bar or a measured
distance in frame; cross-polarise shiny things; mask turntable backgrounds.

Default engines: RealityScan 2.x (free under USD 1M revenue, `RealityScan.exe -headless` CLI, Windows) or the
open route COLMAP 4.x + OpenMVS (any OS). Commands, settings and failure modes:
[references/photogrammetry.md](references/photogrammetry.md). When COLMAP fails on sparse photos, a
feed-forward model (VGGT; only the VGGT-1B-Commercial weights allow commercial use) can give poses.

## Splats

Best way to show a real place photoreally; useless for printing, standard physics or relighting until a mesh
is extracted (2DGS, PGSR, MILo). Formats, tools and the splat-to-game recipe: [references/splats.md](references/splats.md).

## From measurements

Model in metres from the maker's dimensions and long-lens orthographic photos with a ruler in the object's
plane, set up as reference images (polywright-references, polywright-blender). Check one known dimension of any
blueprint before trusting it. A single photo can give a camera with fSpy (its Blender importer is reported
broken after 4.0: copy the numbers by hand).

## Cleanup after any scan (before polywright-finish)

1. Crop the floor, turntable and floaters. 2. Set real scale from the scale bar; up axis right; origin at the
base. 3. `pw.py inspect` and `render`. 4. Decimate a copy, keep the dense mesh for baking. 5. Retopologise,
unwrap, bake normal, AO and colour (polywright-finish). 6. Delight the colour map, or capture cross-polarised.
For printing, `pw.py printable` closes and thickens it (polywright-print).

## Never

- Export, cache or trace Google Photorealistic 3D Tiles.
- Print a raw scan or splat of a whole place: detail is below nozzle size and it is not closed.
- Ship OSM-derived models without the credit; physical items need it on the packaging (OSMF guidelines).

## Maintenance

Evergreen unit, tier `moderate`. Companions: [RESEARCH.md](RESEARCH.md), [CHANGELOG.md](CHANGELOG.md),
[LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md) with `evals/evals.json`, [MAINTENANCE.md](MAINTENANCE.md),
state in `evergreen.json`. Read `evergreen.json` at each use; refresh when due.
