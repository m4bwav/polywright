# Photogrammetry and scanning

Back to [SKILL.md](../SKILL.md). Source: polywright research note `2026-10-11-reality-capture.md` sections 1, 3
and 6 (seen 2026-10-11). Flags marked "prior knowledge" were not re-run this session: run `--help` first.

## Engines

| Engine | Version (2026-10) | Licence | OS | Scriptable |
|---|---|---|---|---|
| RealityScan (formerly RealityCapture, Epic) | 2.2 (2026-06-24) | free under USD 1M revenue; USD 1,250/seat/year above | Windows; Linux CLI under bundled Wine | yes: `-headless`, `.rscmd` files |
| COLMAP | 4.2 | BSD | Windows, macOS arm64, Linux | yes: CLI and pycolmap; GLOMAP is built in as the global mapper |
| OpenMVS | 2.4 | AGPL (prior knowledge) | all | yes: dense, mesh, refine, texture |
| Agisoft Metashape | 2.3 | Standard USD 179, Professional USD 3,499 | Windows, macOS, Linux | Python and headless need Professional (per comparison tables) |
| Meshroom (AliceVision) | 2025.x | MPL | Windows, Linux | node graph, CLI |
| Phone apps (Polycam, KIRI, Scaniverse) | current | freemium | iOS, Android | no; export OBJ/GLB/PLY |

## Commands

RealityScan (Windows):

    RealityScan.exe -headless -newScene -addFolder "<images>" -align -calculateNormalModel -simplify 500000 \
        -calculateTexture -exportModel "Model 1" "<out>/model.obj" -save "<out>/scan.rsproj" -quit

COLMAP + OpenMVS (any OS; prior knowledge for exact flags):

    colmap automatic_reconstructor --workspace_path ws --image_path images --mapper GLOBAL
    colmap image_undistorter --image_path images --input_path ws/sparse/0 --output_path ws/dense
    InterfaceCOLMAP -i ws/dense -o scene.mvs
    DensifyPointCloud scene.mvs
    ReconstructMesh scene_dense.mvs
    RefineMesh scene_dense_mesh.mvs
    TextureMesh scene_dense_mesh_refine.mvs

COLMAP 4.x renamed option groups (`--FeatureExtraction.use_gpu`, `--FeatureMatching.*`, `--SiftMatching.*`);
learned features exist (`ALIKED_N16ROT` with the `ALIKED_LIGHTGLUE` matcher). On Windows the CUDA build ships
no CUDA runtime: the cuBLAS, cudart, cuDNN, cuFFT and cuRAND DLLs must sit next to `colmap.exe` (they can be
copied from the `nvidia-*-cu12` pip wheels). Leave `max_num_matches` at its default; very high values make the
SIFT matcher fail to start. (Learned on a Windows 11 machine, 2026-09.)

## Capture

- Exposure, focus and white balance locked; f/8 to f/11; ISO low; sharp beats many.
- 60 to 80% overlap; circles at two or three heights; move the camera, never pivot in place.
- Turntable: mask the background or the reconstruction locks onto it.
- Shiny or dark: cross-polarised light (polariser on the lights and the lens), or matte spray (where allowed).
- Scale: a scale bar or two coded targets at a measured distance; check a second distance afterwards.
- Outdoors: overcast is best; no wind for plants; no people walking through.

## Failure modes

- Split components: not enough overlap at a corner; add photos, or let COLMAP 4.2 keep components and merge.
- Holes: undersides and occluded parts; plan a base or model it.
- Melted thin parts (railings, leaves): photogrammetry cannot resolve them; model them.
- Baked shadows in the texture: delight (cross-polarised capture, Agisoft De-Lighter, or repaint).

## Scanners

Structured-light handhelds (Revopoint, Creality, Shining 3D Einstar): vendor accuracy 0.02 to 0.1 mm, good for
parts that must fit; verify with calipers. Phone LiDAR (Polycam and others): room-scale, about plus or minus a
centimetre indoors by the vendor's own figure; fine for rooms and furniture blockouts, not for fits.

## After the scan

Crop, scale, orient, decimate a copy, retopologise (QuadriFlow or Instant Meshes for props; Instant Meshes drops
UVs, so bake), unwrap, bake normal, AO and colour from the dense mesh, delight, LODs, export. polywright-finish
covers the steps; polywright-print covers closing a scan for printing.
