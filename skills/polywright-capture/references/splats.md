# Gaussian splats

Back to [SKILL.md](../SKILL.md). Source: polywright research note `2026-10-11-reality-capture.md` section 2
(seen 2026-10-11).

## When

Splats are the best way to show a real place or object photoreally from free viewpoints: fast to capture (a
phone or a 360 camera), fast to view in a browser. They are not triangles: no printing, no standard physics,
poor relighting and editing. Anything that must be played on, printed or lit needs a mesh: capture for
photogrammetry, or extract one and expect cleanup.

## Tools

| Tool | Licence | Notes |
|---|---|---|
| Jawset Postshot | Free (non-commercial, exports poses only), Indie, Studio (CLI) | the common Windows trainer |
| Brush 0.3 | Apache-2.0 | any GPU, CLI, COLMAP input, masks |
| gsplat (nerfstudio) | Apache-2.0 | Python library behind many trainers |
| SuperSplat (PlayCanvas) | MIT | browser editor: crop, floaters, compress |
| splat-transform | MIT | `npm i -g @playcanvas/splat-transform`: PLY, SPZ, SOG, KSPLAT in; GLB (KHR) out; filters, decimation, collision |
| Blender 5.3 (alpha, Sept 2026) | GPL | native PLY and SPZ v4 import reported |

ComfyUI also has `File3DToSplat`, `SplatToFile3D` and `SplatToMesh` nodes (seen on a 0.38 host, 2026-10-11).

## Formats

PLY for training output and interchange; SPZ (about 10x smaller) for apps; SOG (15 to 20x smaller, streamable
LOD) for the web; glTF `KHR_gaussian_splatting`, which the Khronos registry lists as ratified (2026-10-11).

## Mesh extraction

2DGS with TSDF fusion, PGSR, MILo, GOF give meshes from splats; SuGaR is older. Expect noisy, dense, closed-ish
surfaces that need decimation, retopology and baking like a scan.

## Splats in a game

Unity has no first-party splat renderer; Unreal uses plugins (Luma, XGRIDS LCC, Cesium); three.js and PlayCanvas
render them on the web. Keep a mesh terrain as the gameplay truth and generate collision from the splat:

    splat-transform terrain.ply --filter-cluster --seed-pos 0,0,0 terrain.voxel.json --voxel-floor-fill --collision-mesh

(outdoors; indoors `--voxel-external-fill --voxel-carve`). Floaters: crop and filter in SuperSplat or with the
cluster filter.
