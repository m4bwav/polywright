# Reality capture: turning real things into 3D models

Research for the polywright plugin. Written 2026-10-11. Topic: photogrammetry, Gaussian splatting, LiDAR and depth scanning, places and terrain from open data, modelling from measurements, cleanup after capture, practitioner advice, and the academic state of the art.

How to read the citations: "(seen 2026-10-11)" means the source was opened or its search snippet was read on that date. Claims marked "(prior knowledge, not re-verified)" come from the researcher's background knowledge and were not checked against a live source in this session. Treat those as leads, not facts.

Method note: the session hit its web search budget (200 searches shared across agents) partway through. Reddit was reached through its RSS search endpoint (three useful feeds: r/photogrammetry twice, r/GaussianSplatting once) before the loop was stopped. WebFetch on reddit.com is refused, as expected. Later sections lean on primary pages opened directly.

## Bottom line

1. For a real PARK into a GAME level: build the ground from a public DEM (USGS 3DEP 1 m lidar in the US, Copernicus GLO-30 elsewhere), lay paths, water and park outlines from OpenStreetMap (Overpass or osmnx), place buildings from OSM or Overture footprints, and scatter your own tree and bench assets at OSM point locations. Use a drone or phone capture only for hero props (a statue, a fountain, a bandstand). Credit "© OpenStreetMap contributors" in the credits or splash screen.
2. For the same PARK as a PRINTABLE tabletop model: TouchTerrain (free web app, STL/OBJ) or a Blender/Blosm pipeline gives the terrain; exaggerate height (a flat park needs far more vertical exaggeration than a mountain); turn paths, water and lawns into separate 3MF bodies or colour-by-layer bands for the Bambu AMS; model trees as chunky "lollipop" shapes at least 1 mm thick. Never print a raw photogrammetry or splat mesh of a whole park; it is not watertight and its detail is below nozzle size at tabletop scale.
3. Google Photorealistic 3D Tiles cannot be exported, cached, traced or used offline. They are for live, attributed streaming only, and new EEA-billed projects since 2025-07-08 cannot get them at all. Do not build a pipeline that downloads them (Google Map Tiles API policies, seen 2026-10-11).
4. Default object photogrammetry engine for an agent on Windows: RealityScan 2.x (free under USD 1M revenue, `RealityScan.exe -headless ...` CLI, AMD and NVIDIA GPUs since 2.2, Linux CLI under bundled Wine). Fully open-source fallback that runs everywhere: COLMAP 4.x (BSD, global mapper built in) plus OpenMVS for mesh and texture.
5. Metashape is the choice for survey work and georeferenced output; Python and headless use need the Professional licence (USD 3,499, per third-party listings). Standard (USD 179) cannot be scripted, but it can export COLMAP poses for splat training.
6. Gaussian splats are the best way to SHOW a real place (photoreal, fast to capture, a 360 camera is enough). They are not a mesh: no printing, no standard physics, poor relighting. For any use that needs triangles, either capture for photogrammetry or extract a mesh (2DGS, PGSR, MILo, GOF) and expect a clean-up pass.
7. Splat file formats: PLY for training output and interchange, SPZ (Niantic, about 10x smaller) for apps, SOG (PlayCanvas, 15 to 20x smaller, streamable LOD) for the web, and glTF `KHR_gaussian_splatting`, which the Khronos registry now lists as "Complete, Ratified" (seen 2026-10-11). Convert between all of them with `npm i -g @playcanvas/splat-transform` (MIT).
8. Splats in a game: `splat-transform` generates voxel collision and a `.collision.glb` from a splat (`--voxel-floor-fill` outdoors, `--voxel-external-fill --voxel-carve` indoors). Unity has no first-party splat renderer; Unreal relies on plugins (Luma, SplatRenderer, XGRIDS LCC, Cesium); Blender 5.3 (alpha in Sept 2026) imports PLY and SPZ v4 natively.
9. Feed-forward reconstruction (VGGT, MASt3R, Pi3, MapAnything, Depth Anything 3) gives camera poses in seconds and survives sparse or low-overlap photo sets, but COLMAP-style bundle adjustment is still more precise for dense captures. Use VGGT as a fallback when COLMAP fails or as a fast initializer. Licences matter: only the VGGT-1B-Commercial checkpoint is licensed for commercial use; MASt3R and DUSt3R are non-commercial.
10. Capture rules that never change: lock exposure, focus and white balance; shoot sharp, f/8 to f/11; 60 to 80% overlap; move the camera, do not pivot on the spot; no moving subjects or wind-blown trees; add a scale bar or a measured distance; cross-polarise shiny objects; mask turntable backgrounds.
11. Phone LiDAR is room-scale and centimetre-grade (Polycam itself claims about plus or minus half an inch indoors). For printable replacement parts use a structured-light handheld scanner (Revopoint, Creality, Shining 3D; vendor specs 0.02 to 0.1 mm) or careful photogrammetry with scale bars, then verify with calipers.
12. Measured objects (furniture, products, buildings) are often faster and cleaner to MODEL from dimensions and orthographic photos than to scan. Use scans as reference meshes, not final geometry, when the object is mostly flat planes.
13. Scan-to-game-asset cleanup: decimate a copy, retopologise (QuadriFlow or Instant Meshes for props), unwrap, bake normal, AO and colour from the dense scan to the low-poly mesh, de-light the colour map, set real-world scale in metres and put the origin at the base.
14. Licences to track per asset: OSM and Overture buildings are ODbL (attribution, share-alike on the database); Copernicus DEM needs its credit line; USGS 3DEP is public domain; Google tiles are never redistributable; SuperSplat "Downloadable" scenes carry the author's Creative Commons licence.
15. Drone mapping of a park: WebODM (AGPL; split from OpenDroneMap in April 2026, now on its own ODX engine) or OpenDroneMap 3.6.x; fly a crossgrid at 68% overlap and sidelap or more, add oblique passes for trees and buildings, fly on still days. US buyers face FCC restrictions on new DJI models since December 2025.

## 1. Photogrammetry

### What to use now

| Tool | Version seen | Licence and price | OS | Scriptable | Notes |
|---|---|---|---|---|---|
| RealityScan (formerly RealityCapture, Epic) | 2.2 (2026-06-24) | Free under USD 1M annual revenue, students, schools; USD 1,250 per seat per year above | Windows GUI; Linux CLI under bundled Wine (2.1+) | Yes: `RealityScan.exe -headless`, .rscmd files, Remote Command Plugin over gRPC/REST (2.1) | Fastest GPU engine. 2.2 added AMD Radeon RDNA3/3.5/4 on Windows and a 360-camera workflow (Pano2Views). |
| Agisoft Metashape | 2.3.x (2.3.2 named in a 2026-09 Reddit thread) | Standard USD 179, Professional USD 3,499, perpetual (third-party listings) | Windows, macOS, Debian/Ubuntu | Python, stand-alone module and headless: Professional (per comparison tables) | Best for markers, scale bars, GCPs, DEMs, orthomosaics. Standard exports COLMAP poses since 2.1.3. |
| COLMAP | 4.2.0 (article dated 2026-09-01) | BSD | Windows, macOS arm64, Linux; CUDA and non-CUDA binaries | Yes: CLI and pycolmap | 4.0 merged GLOMAP as `global_mapper` / `automatic_reconstructor --mapper GLOBAL`; 4.1 GPU bundle adjustment (Caspar); 4.2 keeps every disconnected component, adds LoMa learned matching, ROCm dense stereo. |
| GLOMAP (standalone) | repo still exists | BSD | all | CLI | Now inside COLMAP 4.x, so prefer COLMAP. |
| OpenMVS | 2.4.0 (NixOS package) | AGPL (prior knowledge, not re-verified) | all | CLI: `DensifyPointCloud`, `ReconstructMesh`, `RefineMesh`, `TextureMesh` | Standard dense, mesh and texture stage after COLMAP. |
| Meshroom / AliceVision | Meshroom 2025.1.0 with AliceVision 3.3.0 (2025-08-18) | MPL-2.0 | Windows, Linux (no macOS CUDA) | `meshroom_batch` (prior knowledge, not re-verified) | Node graph; adds turntable/object, LiDAR E57 import, photometric stereo; MrGSplat splat plugin needs the develop build. Slow: 44 min versus RealityScan's 15 min on the same 40 photos in one user test. |
| Apple Object Capture (RealityKit PhotogrammetrySession) | macOS 12+ | Free with Xcode | macOS (full detail), iOS (reduced only) | Yes, Swift sample CLI (`-d` detail level) | Detail levels preview, reduced, medium, full, raw; custom poly counts clamp to a hardware limit (250k reported on an M1 Max). One 2026 Reddit poster found it made a closed head mesh where RealityScan and Metashape fragmented. |
| Simple Photogrammetry GUI | 1.1.6 | GPL-3.0 | Windows (HIP beta for AMD) | GUI over CLIs | Front end for COLMAP, OpenMVS, PoissonRecon, mvs-texturing and Brush. |
| Polycam | 2026 plans: Free, Basic USD 30/mo or USD 150/yr, Business USD 400/yr per user | Free tier exports glTF only | iOS, Android, web | No | Photo mode, LiDAR mode, splats. |
| KIRI Engine | Pro USD 17.99/mo or USD 79.99/yr | Free tier; export caps reportedly removed in 2025 | iOS, Android, web | API exists (prior knowledge, not re-verified) | Cloud processing; also ships the 3DGS Render Blender add-on. |
| Scaniverse (Niantic Spatial) | 2026 | Free on-device scanning and splats; Plus USD 20/mo, Pro USD 50/mo for cloud and commercial rights | iOS, Android | No | Fastest on-device. Exports SPZ; USDZ (splat plus derived mesh) added 2026-07-06. |

Sources (all seen 2026-10-11):
- RealityScan licence and threshold: https://www.realityscan.com/license and https://radiancefields.com/platforms/realityscan
- RealityScan 2.1 features, Linux CLI under Wine, Remote Command Plugin: https://radiancefields.com/realityscan-version-2-1-released (byline 2025-11-25; Epic's page dates 2.1 to 2026-04-21, conflict unresolved)
- RealityScan 2.2: https://www.cgchannel.com/2026/06/epic-games-releases-realityscan-2-2-with-amd-gpu-support/ and https://www.realityscan.com/news/realityscan-2-2-is-here-with-full-amd-gpu-support-download-today
- RealityScan CLI command list: https://dev.epicgames.com/documentation/realityscan/all-commands and https://dev.epicgames.com/documentation/realityscan/command-line-operations
- RealityCapture legacy licence server closes 2026-08-03: https://www.realityscan.com/ (via search snippet)
- Metashape prices and comparison: https://www.skyebrowse.com/news/posts/metashape-vs-realitycapture (2026-07-03), https://www.agisoft.com/features/compare/ , https://www.agisoft.com/downloads/installer/
- Metashape Standard COLMAP export: https://radiancefields.com/agisoft-metashape-adds-colmap-export-support-to-standard-license
- COLMAP 4.0 and 4.2: https://radiancefields.com/colmap-4.0-introduces-major-performance-and-infrastructure-updates and https://radiancefields.com/colmap-4.2.0-adds-multi-component-global-mapping-and-loma-learned-matching
- Meshroom 2025.1.0: https://github.com/alicevision/Meshroom/releases/tag/v2025.1.0 and https://www.mpcvfx.com/en/news/mpc-celebrates-the-release-of-meshroom-2025-1-0/
- Apple Object Capture detail levels: https://developer.apple.com/documentation/realitykit/photogrammetrysession/request/detail.md and https://developer.apple.com/forums/thread/786083
- Phone app prices: https://www.skyebrowse.com/news/posts/polycam-vs-scaniverse (2026-07-03), https://www.3dmag.com/3d-scanners/best-3d-scanning-apps/ (SEO-heavy, verify on vendor pages)
- Scaniverse USDZ: https://radiancefields.com/scaniverse-adds-usdz-export-to-splats
- Simple Photogrammetry GUI: https://digitalproduction.com/2026/08/31/open-source-photogrammetry-gets-friendlier/

### Agent-scriptable pipelines

RealityScan, Windows (command spellings from Epic's All Commands page, seen 2026-10-11; chaining on one line is the documented pattern in examples, but test it):

```
RealityScan.exe -headless -newScene -addFolder "D:/scan/images" -align -calculateNormalModel -simplify 500000 -calculateTexture -exportModel "Model 1" "D:/scan/out/model.obj" -save "D:/scan/scan.rsproj" -quit
```

COLMAP plus OpenMVS, any OS (prior knowledge for exact flags, not re-verified):

```
colmap automatic_reconstructor --workspace_path ws --image_path images --mapper GLOBAL
colmap image_undistorter --image_path images --input_path ws/sparse/0 --output_path ws/dense
InterfaceCOLMAP -i ws/dense -o scene.mvs
DensifyPointCloud scene.mvs
ReconstructMesh scene_dense.mvs
RefineMesh scene_dense_mesh.mvs
TextureMesh scene_dense_mesh_refine.mvs
```

Metashape Professional: `metashape.sh -r script.py` or the stand-alone `Metashape` Python module (prior knowledge, not re-verified).

### Capture technique (time-honored, still true)

- Overlap 60 to 80% between neighbouring shots; above about 80% mostly adds time. For drone crossgrids, OpenDroneMap's docs ask for 68% overlap and sidelap (equivalent 83%) for good 3D. https://www.pix-pro.com/photogrammetry-settings-checklist and https://github.com/OpenDroneMap/docs (seen 2026-10-11)
- Aperture f/8 to f/11, ISO low, shutter fast enough for zero blur; lock focus, exposure and white balance. Same checklist.
- Move the camera between shots, never rotate on the spot. Fill the frame with the subject. Same checklist.
- Redundant and blurry photos are the most common cause of failed or skewed projects, according to a developer of measuring photogrammetry software: https://www.pix-pro.com/3d-data-mistakes (seen 2026-10-11)
- Turntables: at least 36 photos per full rotation for small objects; mask the background or the static background breaks alignment. https://www.pix-pro.com/small-scale-part2
- Cross-polarisation: polariser on the light, crossed polariser on the lens. It removes specular reflections, which gives flatter, delit albedo, more tie points and better alignment on shiny surfaces. Subtracting a cross-polarised pass from a parallel-polarised pass gives a roughness/specular map. Reddit r/photogrammetry examples, below.
- Scale: place a scale bar or coded targets with a known distance; museum turntable shoots use a 10 cm scale plus a colour checker. https://deepblue.lib.umich.edu/data/downloads/3197xn74f
- Featureless or shiny objects: scanning spray or dry shampoo, or project a texture pattern with a projector.
- Outdoors: overcast light is best (soft, shadowless); avoid wind for foliage.

### Practitioner tips (Reddit and forums)

- Cross-polarised ring flash (Godox AR400 or Flashpoint RF-400 with a polariser kit) is the standard small-object rig. "Cross polarization has been a game changer" posts show clean RealityCapture output straight into Blender. https://www.reddit.com/r/photogrammetry/comments/znh8rj/cross_polarization_has_been_a_game_changer/ (2022-12, seen via RSS 2026-10-11)
- A 2025-11 poster who builds AR400 polarisers says reflections are "one of the main causes of misalignment, poor meshing, and unusable textures, especially when creating game-ready assets." https://www.reddit.com/r/photogrammetry/comments/1p6n1cm/3d_printed_godox_ar400_polarization_filter/
- Budget version works: "a dslm, a flash and dry shampoo" on a compressor wheel beat conventional scanners. https://www.reddit.com/r/photogrammetry/comments/1ospxy0/1st_try_and_omg/ (2025-11-09)
- Typical hero-prop numbers: 140 photos (cross and parallel polarised), 35M-poly mesh decimated to 160k, 8k maps, 15 minutes of capture and about 3 hours of processing. https://www.reddit.com/r/photogrammetry/comments/1ccvvl8/now_getting_all_maps_from_scan_data_pbr_clay/ (2024-04)
- Artec's own tip: when you flip or re-support an object, import that as a separate photo set, process separately, then merge. 578 photos, 10-degree rotations, 18 camera heights for a pair of shoes. https://www.reddit.com/r/photogrammetry/comments/1ql0661/oxford_shoes_captured_with_artec_studio_ai/ (2026-01-23)
- Software disagreement: one game-map maker (900 photos of a chapel, drone plus iPhone) found RealityScan would not make one component despite a dozen control points, and Metashape aligned almost everything first try. https://www.reddit.com/r/photogrammetry/comments/1pgxwf9/first_attempt_at_photogrammetry_for_game_maps/ (2025-12-08). Others prefer RealityScan for speed. Another thread found Metashape's background-ignoring setting better for small turntable work while a commenter preferred RealityCapture for isolating objects (May 2025, https://redlib.ssps.io/r/photogrammetry/comments/1kekjbn/need_help_with_my_process).
- Free-tool shoot-out (2026-02-10): KIRI and RealityScan mobile process in the cloud (2 to 10 min); Scaniverse is on-device and fastest; RealityScan desktop 2.1 took 15 min for 40 photos on a Ryzen 9 5900X and RTX 3060; Meshroom 2025.1.0 took 44 min on the same set. https://www.reddit.com/r/photogrammetry/comments/1r1cr1r/i_tried_all_the_free_photogrammetry_software_and/
- Human heads from phone photos fragment in both RealityScan 2.2 and Metashape Pro 2.3.2 even with every camera aligned, while Apple Object Capture closed the mesh. https://www.reddit.com/r/photogrammetry/comments/1w8c0e4/fully_aligned_humanhead_captures_produce/ (2026-09-05)
- Commercial terrain scanning for print: a "half-ton" motion-control rig scans physical fantasy terrain into printable assets for a Gamefound campaign, which shows the print market values scanned miniatures. https://www.reddit.com/r/photogrammetry/comments/1uw7clk/my_halfton_3d_scanning_beast_doing_what_it_was/ (2026-07-14)

### Failure modes

- Reflective, transparent, or textureless surfaces (glass, chrome, white walls) do not reconstruct. Fix with polarisation, spray, projected texture, or model them by hand.
- Moving things (people, leaves, water, clouds) make holes and ghost geometry.
- Multiple components or a split model: not enough overlap at a transition (for example from drone to ground photos). Add bridging photos.
- Baked lighting and shadows in the texture: needs delighting (section 6).
- Unknown scale: photogrammetry output has arbitrary scale unless you add a scale bar, GPS, or a measured distance.

## 2. Gaussian splatting and NeRF

### What to use now

| Tool | Version seen | Licence and price | OS | Scriptable | Notes |
|---|---|---|---|---|---|
| Jawset Postshot | current (no version on site) | Free (non-commercial, exports camera poses and points only); Indie (commercial, exports PLY and SPZ); Studio (adds CLI, HDR, EXR, AprilTag alignment). Prices load dynamically; historically about EUR 20 and EUR 60 per month (prior knowledge, not re-verified) | Windows 10+, NVIDIA compute 7.5+ | CLI only in Studio | Imports COLMAP and RealityScan. Popular with artists. https://www.jawset.com/ and https://www.jawset.com/shop/pricing |
| Brush | 0.3 (2025-09) newest formal release found | Apache-2.0, free | Windows, macOS, Linux, Android, browser (WebGPU) | Yes, `brush --help` CLI | Any GPU vendor. COLMAP and nerfstudio input, masks folder support. https://github.com/ArthurBrussee/brush , https://radiancefields.com/brush-releases-v0-3 |
| LichtFeld Studio | v0.5.3 (2026-06) | Open source (GPL, prior knowledge); free from source, prebuilt binaries for a USD 30 donation | Windows, Linux | Embedded Python and MCP | Exports PLY, SOG, SPZ and an HTML viewer; MCMC, bilateral grid; Vulkan viewer. https://github.com/MrNeRF/LichtFeld-Studio , https://radiancefields.com/lichtfeld-studio-v0.5.3-drops-its-cuda-renderer-for-a-full-vulkan-viewer |
| gsplat (nerfstudio) | v1.5.3 tag; main has 2026 work | Apache-2.0 | Linux, Windows (CUDA) | Python | Library used by many trainers; VGGT recommends gsplat 1.3.0 for its COLMAP output. https://radiancefields.com/gsplat-1-5-3-released-by-nerfstudio |
| nerfstudio (splatfacto, nerfacto) | not checked | Apache-2.0 | Linux, Windows | CLI `ns-train` | Research framework; status of 2026 maintenance not verified. |
| SuperSplat (PlayCanvas) | 3.0 (WebGPU only) | Editor MIT; hosting proprietary | Browser | REST publishing API | Crop, clean, walk mode, voxel collision, streamed LOD for scenes over 1M Gaussians, SPZ export since 2.29. https://radiancefields.com/playcanvas-releases-supersplat-3.0 , https://developer.playcanvas.com/user-manual/supersplat/ |
| splat-transform (PlayCanvas) | 2.0 added collision (2026-05); 3.x streaming; 3.9.0 faster SOG | MIT | Node, browser, Docker | Yes, CLI and library | Converts PLY, SPZ, SOG, KSPLAT in, GLB (KHR) out, LCC in; filters floaters, decimates, Morton order, collision mesh. https://github.com/playcanvas/splat-transform |
| Scaniverse, Polycam, KIRI, Luma | see section 1 | | phones | No | Phone capture to splat. Scaniverse is free and on-device. |
| DJI Terra 5 | 2026 | Flagship about USD 2,800 to 4,400 per year (vendor-adjacent blog) | Windows | | Drone imagery to splats, 3D Tiles and PLY. https://www.thefuture3d.com/blog/state-of-gaussian-splatting-2026/ (service provider blog, biased) |
| World Labs Marble | 1.1 | Hosted, paid | Web | API | Generates a splat world from text, 1 image, 2 to 8 photos or a video; exports SPZ or PLY plus a collider mesh and visual mesh. Generative, not faithful reconstruction. https://www.uploadvr.com/marble-turns-an-image-into-a-webxr-volumetric-scene-in-minutes/ |
| Apple SHARP | 2025-12 | MIT | CPU, CUDA, Metal | Python | One photo to a metric-scale splat in under a second. https://www.uploadvr.com/apple-sharp-open-source-on-device-gaussian-splatting/ |

### Mesh extraction from splats

| Method | arXiv | What it does | Use when |
|---|---|---|---|
| SuGaR | 2311.12775 | Regularises Gaussians to the surface, Poisson mesh | Old baseline; Blender add-on exists. |
| 2DGS | 2403.17888 | Flattens Gaussians to 2D disks, TSDF fusion of rendered depth | Default "splat with a usable mesh" today; many trainers include it. |
| GOF (Gaussian Opacity Fields) | 2404.10772 | Opacity field level set via marching tetrahedra | Unbounded outdoor scenes, thin structures. |
| PGSR | 2406.06521 | Planar-based Gaussian surface reconstruction (prior knowledge of content) | Buildings, interiors, planar scenes. |
| GS2Mesh | 2404.01810 | Renders stereo pairs from the splat and runs a stereo network | Good geometry from an existing 3DGS. |
| MILo | 2506.24096 (SIGGRAPH Asia 2025, TOG) | Mesh in the training loop via Delaunay on Gaussian pivots; about 10x fewer vertices | Lightweight meshes for physics and animation. |
| AnyGS2Mesh | 2609.03304 (2026-09) | Feed-forward mesh from any 3DGS; T&T F-score of plain 3DGS 0.110 to 0.417 | Very new; watch it. |
| FriendlySplat | toolkit | Training, pruning, TSDF meshing, segmentation in one Apache-2.0 codebase | Research pipeline. https://radiancefields.com/friendlysplat-launches-an-open-toolkit-for-gaussian-splatting |

Sources: arXiv pages listed, seen 2026-10-11. MILo: https://arxiv.org/abs/2506.24096 . AnyGS2Mesh: https://arxiv.org/pdf/2609.03304 .

### File formats and standards

- PLY: the de facto training output. Biggest files. Every tool reads it.
- SPZ: Niantic's open format, quantised plus ZSTD, about 10x smaller than PLY; v4 is current. https://developer.playcanvas.com/user-manual/gaussian-splatting/formats/spz/ ; announcement thread https://www.reddit.com/r/GaussianSplatting/comments/1gf0nsj/introducing_the_spz_format_for_3dgs_its_like_jpg/ (2024-10)
- SOG (Spatially Ordered Gaussians): PlayCanvas, lossy quantisation into WebP images plus metadata, 15 to 20x smaller than PLY, Morton-ordered, single-file `.sog` bundle, streamable LOD. https://developer.playcanvas.com/user-manual/gaussian-splatting/formats/sog/ and https://blog.playcanvas.com/playcanvas-open-sources-sog-format-for-gaussian-splatting/
- glTF `KHR_gaussian_splatting`: release candidate announced 2026-02-03 (https://www.khronos.org/news/permalink/khronos-announces-gltf-gaussian-splatting-extension); the Khronos registry README now lists it under "Ratified Khronos Extensions" and the spec says "Complete, Ratified by the Khronos Group" (https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_gaussian_splatting/README.md , seen 2026-10-11; exact ratification date not shown). Data lives on a POINTS primitive with ROTATION, SCALE, OPACITY and SH attributes; non-supporting viewers fall back to coloured points. No compression in the base extension; compression will come as companion extensions. Known implementations: CesiumJS, Cesium Native, JSplat, 3dgs_ply2gltf. Cesium for Unreal also shipped support (2026-03), as did Babylon.js and PlayCanvas (radiancefields, seen 2026-10-11).
- OpenUSD particle-field schema and MPEG Gaussian splat compression are in progress (thefuture3d blog, 2026-04-04, biased source).
- Blender 5.3 (alpha, article dated 2026-09-16) imports PLY and SPZ v4 as a "3D Gaussian Splats" point cloud type and renders in Workbench, EEVEE and Cycles; no export; Apply Transform mishandles scale, rotation and SH. https://radiancefields.com/blender-5.3-will-bring-native-3d-gaussian-splat-import-and-rendering
- KIRI 3DGS Render add-on for Blender: 5.0 (2026-06) animates splats from a proxy mesh; 5.1.0 adds relighting and mesh shadows; Apache-2.0; moving to community maintenance. https://www.cgchannel.com/2026/06/3dgs-render-5-0-lets-you-animate-gaussian-splats-inside-blender/

### Engines

- Unity: no first-party splat support found. Options: Aras P's open-source UnityGaussianSplatting (prior knowledge, not re-verified), XGRIDS LCC Unity SDK 2.2.0 (2026-08, lights and shadows), SplatBridge (streaming plus colliders for Unity 6), Cesium for Unity splats planned with no date. https://radiancefields.com/splatbridge-brings-streamed-gaussian-splats-and-splat-colliders-to-unity-6 , https://community.cesium.com/t/unity-gaussian-splatting/43681
- Unreal 5.5 to 5.7: no Epic module; use Luma's free plugin, SplatRenderer (Apache-2.0, DX12 Windows only, 4D playback), XGRIDS LCC plugin, or Cesium for Unreal (KHR glTF). Splats do not cast shadows through the standard pipeline, and scenes over a couple of million Gaussians need chunking, which can show seams. https://www.strayspark.studio/blog/gaussian-splatting-unreal-engine-5-capture-to-game-pipeline , https://radiancefields.com/splatrenderer-plugin-for-unreal-engine
- three.js / web: PlayCanvas is the most complete web engine for splats (streaming, collision, relighting, shadows on splats since mid-2025). Spark and other three.js splat renderers exist (prior knowledge, not re-verified).
- Roblox: no splat rendering (prior knowledge). Use meshes.

### Splat-to-game recipe (PlayCanvas example, 2026-04-22)

From https://blog.playcanvas.com/turning-a-gaussian-splat-into-a-videogame/ :
1. Convert the splat to streamed SOG chunks with `splat-transform` (manifest `lod-meta.json`).
2. Generate collision: `splat-transform terrain.ply --filter-cluster --seed-pos 0,0,0 terrain.voxel.json --voxel-floor-fill --collision-mesh` (outdoor) or `--voxel-external-fill --voxel-carve` (indoor). Defaults: 0.05 voxel size, 0.1 opacity. https://developer.playcanvas.com/user-manual/splat-transform/collision/
3. Bake a 1 m grid of light probes from the splat so meshes (weapons, NPCs) match local brightness.
4. Build a navmesh from the collision GLB with recast-navigation.
5. A splat has no surfaces, colliders, navmesh or lights; each must be added.

Unreal equivalent: export a mesh of the scan, set it invisible with "Use Complex Collision as Simple", align it to the splat by hand. https://learn.poly.cam/hc/en-us/articles/42506758152084

### When splats beat meshes, and when they cannot be used

Splats win for: photoreal viewing of a real place, real estate and heritage tours, AI-video backplates and camera moves, quick capture (a USD 500 Insta360 X5 360 camera captured a whole house, https://www.reddit.com/r/GaussianSplatting/comments/1wmlobx/scanning_houses_just_got_10x_cheaper/ , 2026-09-21), foliage, hair, fuzzy and semi-transparent things that meshes handle badly.

Splats fail or need a mesh for: 3D printing (no surface; extract a mesh then make it watertight), physics and navigation (derive collision), dynamic relighting and shadows in standard engines, CAD and GIS measurement (one service provider quotes 7.82 cm mean geometric error, unverified), Roblox and most mobile engines, any pipeline that needs UVs and PBR materials.

### Practitioner notes (r/GaussianSplatting via RSS, seen 2026-10-11)

- SuperSplat voxel collision at 5 cm is "solid enough to climb stairs and walk crossbeams" and smaller than a mesh. https://www.reddit.com/r/GaussianSplatting/comments/1ugbzj6/ (2026-06-26)
- Do not upload a 15M-Gaussian scene with streaming disabled; it loads everything and renders every Gaussian each frame. Same house thread (2026-09-21).
- 293 360-degree panoramas of an office, aligned in Metashape (1M tie points), trained in LichtFeld 60k iterations to 11M Gaussians. https://www.reddit.com/r/GaussianSplatting/comments/1sivmp6/valve_office_rate_quality/ (2026-04-11)
- A Prague street was scanned in 20 minutes and made into an Unreal game in 2 hours with the XGRIDS LCC plugin plus AI-generated props (Tripo). https://www.reddit.com/r/GaussianSplatting/comments/1wjoi65/ (2026-09-18)
- A miniatures game on Kickstarter hand-builds real dioramas and scans them as splats. https://www.reddit.com/r/GaussianSplatting/comments/1wcxnly/ (2026-09-10)
- "Triangle splatting" (same optimisation, triangles with vertex colour) is being tried as a game-friendly alternative. https://www.reddit.com/r/GaussianSplatting/comments/1rfaer5/ (2026-02-26)
- Synthetic splats: render camera arrays in Blender, Unity or Unreal, or use generated video, then train. https://www.reddit.com/r/GaussianSplatting/comments/1q5l2gc/ (2026-01-06)

### Failure modes

- Floaters (stray Gaussians in the air): crop and filter in SuperSplat or `splat-transform` (floater and cluster filters).
- Poor views away from the capture path: splats only look right near where photos were taken.
- Huge files: always convert to SPZ or SOG for delivery.
- Exposure changes in phone video: appearance-model training (bilateral grid in LichtFeld, PPISP) helps.
- Meshes extracted from splats are dense and noisy; plan a decimation and retopology pass.

## 3. LiDAR, depth and handheld scanners

### What to use now

- iPhone or iPad Pro LiDAR apps: Polycam, Scaniverse, KIRI (AI-enhanced LiDAR is Pro), 3D Scanner App, Pix4Dcatch, Modelar. Good for rooms and large objects, poor for small detail.
- Handheld structured light or laser scanners (vendor specs, not independent):
  - Revopoint Inspire 2 about USD 499, up to 0.05 mm; MetroX about USD 1,209, 0.04 mm (one listing says 0.01 mm). https://all3dp.com/1/best-3d-scanner-diy-handheld-app-software/
  - Creality Ferret Pro about USD 359, 0.1 mm; Raptor and Raptor Pro listed at 0.02 mm.
  - Shining 3D Einstar 2 about USD 1,250, up to 0.1 mm. One Reddit commenter calls the original Einstar "old tech. Solid, but old now"; others say its software is better. https://redlib.hackliberty.org/r/3DScanning/comments/1lefepz/help_deciding_on_scanner (via snippet)
  - Artec (Leo, Eva, Spider) and Creaform for professional metrology (prior knowledge).
- Survey-grade handheld SLAM LiDAR: XGRIDS Lixel L2 Pro (LCC output, splats), used for real estate splats. RealityScan 2.1 imports SLAM trajectories and LAS/LAZ classes.

Accuracy expectations (seen 2026-10-11):
- Polycam claims plus or minus half an inch (about 13 mm) on standard interior captures. https://learn.poly.cam/hc/en-us/articles/50434745985556-How-Accurate-Are-Polycam-Scans
- iOS and Android phone scans assessed at 1 to 3 cm in one comparison; Scaniverse errors under 1% of object size for small and medium objects but with local deviations on large flat surfaces; Modelar plus or minus 3 cm horizontal, 7 mm vertical. https://geodetski-vestnik.com/arhiv/70/1/47_Yanchuk.pdf , https://doaj.org/article/713bedcb1a8149668a92c4e4703c42d4
- An ISPRS 2026 study compared Polycam, Pix4Dcatch, KIRI, Modelar and a prototype against 253 coded targets surveyed with a Trimble X9 TLS (results not read). https://isprs-archives.copernicus.org/articles/XLIX-M-1-2026/1/2026/
- SAE 2025: Polycam on an iPhone 15 matched Recon3D on one crashed-vehicle set but was worse on others. https://saemobilus.sae.org/papers/accuracy-mobile-phone-lidar-crashed-vehicles-2025-01-8692

Time-honored: structured light and laser triangulation need matte surfaces (scanning spray), markers or geometry to track, and several passes; merge passes with ICP in CloudCompare or the vendor software.

Failure modes: tracking loss on flat, symmetric or featureless objects (add markers), black and shiny surfaces, sunlight washing out infrared projectors, phone LiDAR melting small details into blobs.

## 4. Places and large sites (parks, towns, terrain)

### Data sources

| Source | What | Licence | Access |
|---|---|---|---|
| OpenStreetMap | Paths, park boundaries (`leisure=park`), water, trees (`natural=tree`), benches, buildings with `height` or `building:levels` | ODbL 1.0, attribution "© OpenStreetMap contributors" | Overpass API, osmnx (`features_from_bbox`, `features_from_place` with tags like `{"leisure": "park"}`), Geofabrik extracts (prior knowledge) |
| Overture Maps | Buildings with estimated height, floors, usage; base, transportation, places | Buildings, base, divisions, transportation: ODbL; places: CDLA Permissive 2.0 (Foursquare Apache-2.0) | `pip install overturemaps`; `overturemaps download --bbox=W,S,E,N -f geojson --type=building -o out.geojson` (experimental CLI); docs list release v2.0.0 |
| Microsoft building footprints | ML footprints | ODbL (per Overture attribution page) | Inside Overture buildings |
| USGS 3DEP | US lidar point clouds, 1 m and 1/3 arc-second DEMs | Public domain (US federal, prior knowledge) | The National Map, USGS LidarExplorer, OpenTopography; baseline acquisition announced complete at Geo Week 2026 (March), 76 trillion points |
| Copernicus GLO-30 DEM | Global 30 m DSM | Copernicus licence, free; credit "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA" | AWS open data, OpenTopography, ESA |
| OpenTopography | DEM and point cloud API | Free key: 200 calls per day academic, 50 non-academic; USGS 1 m via API academic-only (2023 policy); OT+ USD 30/mo | REST API |
| Google Photorealistic 3D Tiles | Photogrammetric city meshes | Streaming only; no caching, offline use, extraction or tracing | Map Tiles API, Cesium ion |
| Cesium ion | Hosting, OSM Buildings, terrain | Community free for non-commercial; commercial from about USD 149/mo (third-party listing) | Cesium for Unity 1.25, Cesium for Unreal 2.29 (UE 5.6+) as of 2026-08 |

Sources (seen 2026-10-11): https://docs.overturemaps.org/attribution/ , https://docs.overturemaps.org/getting-data/overturemaps-py/ , https://www.geoweeknews.com/news/a-billion-points-of-light-3dep-usgs (2026-03-25), https://www.fgdc.gov/ngac/USGS%203DEP%20Update , https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf , https://gee-community-catalog.org/projects/glo30/ , https://opentopography.org/blog/introducing-api-keys-access-opentopography-global-datasets , https://www.opentopography.org/start , https://cesium.com/blog/2026/08/04/cesium-releases-in-august-2026/

### Tools

| Tool | Version and licence | Output | Notes |
|---|---|---|---|
| Blosm (formerly blender-osm) | GPL code; base free on Gumroad (pay what you want), Pro paid; repo active (push 2026-04-17) | Blender scene | Base: OSM buildings, roads, about 30 m terrain. Pro: textured buildings, forests as objects, satellite imagery, 3D Tiles baking. Google 3D Tiles unavailable for EEA-billed projects created after 2025-07-08. https://github.com/vvoovv/blosm , https://prochitecture.gumroad.com/l/blender-osm |
| OSM2World | Open source (LGPL, prior knowledge); 0.5.0 announced with CLI overhaul | glTF, glb, OBJ, POV | glTF is its most complete export; only the OSM id is kept in glTF extras. https://osm2world.org/ , FOSDEM 2026 slides |
| osmnx | Python, MIT (prior knowledge) | GeoDataFrames | Fetch park polygons, paths, water, trees by tag; then extrude in Blender or trimesh. |
| Cadmapper | Free up to 1 km2 with signup; 1 to 100 km2 "small fee" | DXF, SKP, 3DM, 3DS | Output under ODbL, attribution and share-alike. https://www.arch2o.com/cad-mapper-free-cad-files-of-any-area-in-the-world/ |
| TouchTerrain | Free web app and standalone (Iowa State) | STL, OBJ, tiles | Sets physical size, base thickness, vertical exaggeration; web version uses Google Earth Engine DEMs; local version takes your own GeoTIFF. https://public.vrac.iastate.edu/~charding/TouchTerrain%20AGU%202020%20poster.htm |
| Terrain2STL | Free web | STL | Vertical scale 0.5 to 4.0. https://www.mfgrobots.com/Article/mfg/3dprinting/8632.html |
| Map-to-print web tools | CreateYourMap, Map2Model, SebGE CityMap to 3MF (alpha, up to 7 colour objects), PrintPal, Esri City Download Portal fork | STL, 3MF | Check geometry; Map2Model sometimes makes wrong building shapes. https://www.fabbaloo.com/?p=230437 , https://makerworld.com/en/models/2671049 |
| CityMaker (Blender) | Commercial add-on | Blender | Scatters your own assets on OSM layout. https://superhivemarket.com/products/citymaker |
| WebODM | AGPL; v3.2.7 (2026-07-19); split from OpenDroneMap 2026-04-06; engines ODX, MicMac, LGT; outputs maps, point clouds, DEMs, textured meshes and splats | | https://github.com/WebODM/WebODM , https://www.skyebrowse.com/news/posts/webodm-vs-opendronemap |
| OpenDroneMap (ODM, NodeODM) | 3.6.2 (2026-08-12) | | https://en.wikipedia.org/wiki/OpenDroneMap |
| DJI Terra, Pix4D, Metashape Pro, RealityScan | commercial | | Drone mapping alternatives. |

Drone caveat (US): foreign-made drones were added to the FCC Covered List in December 2025; models authorised before then can still be sold; firmware waiver extended to at least 2029-01-01; a 2026-08 proposal may pull approved DJI models (single source); DJI sued in the Ninth Circuit. https://uavcoach.com/dji-ban/ (seen 2026-10-11)

Drone capture tips: OpenDroneMap docs suggest 75/65% overlap at about 40 m and 80/70% at 80 m; crossgrid 68% for 3D; add oblique passes at 30 to 45 degrees around trees so they do not flatten; a nadir pass then a double-grid oblique at about 60 degrees gimbal works for most sites; trees fail in the slightest wind. https://community.opendronemap.org/t/un-flattening-3d-model-elements/14128 , https://support.dronelink.com/hc/en-us/community/posts/21790537340819-3D-Model-with-Dronelink

### Google Photorealistic 3D Tiles: can it be exported? No.

Google's Map Tiles API policies (https://developers.google.com/maps/documentation/tile/policies , seen 2026-10-11):
- "you must not pre-fetch, index, store, or cache any Content except under the limited conditions stated in the terms."
- Offline uses are prohibited.
- "Geodata extraction or resale" is prohibited.
- You may overlay your own 3D objects only "as long as the 3D objects aren't extracted, traced, or otherwise derived by hand or machine from Photorealistic 3D Tiles."
- Attribution from each tile must be aggregated and shown, usually along the bottom of the view.
Cesium staff confirm the tiles cannot be partly downloaded and Cesium's Clips export does not work with them. https://community.cesium.com/t/export-google-3d-tiles-for-unreal/38007 . A game that streams Google tiles live must keep streaming them and show credits; a free Cesium ion Community account only covers non-commercial games (forum answer). EEA billing accounts lost 3D tiles for new or materially modified projects from 2025-07-08 (OSGeo forum report). https://discourse.osgeo.org/t/google-satellite-2d-tiles-stopped-working-for-european-economic-area-eea-developers/149688

Blosm's Google-tiles import exists, but any use beyond live viewing breaks the terms. Polywright must never offer "download Google tiles into a mesh" as a path.

### Best workflow: a real public park into (a) a game level

1. Define the area: get the park polygon from OSM (`leisure=park`) with osmnx or Overpass; buffer it 50 to 100 m for context.
2. Terrain: download the best DEM. US: USGS 3DEP 1 m DEM (The National Map or LidarExplorer). Elsewhere: national lidar if open, else Copernicus GLO-30 (30 m is too coarse for a small park's paths; expect to sculpt by hand). Reproject to a local metric CRS (UTM).
3. Heightmap for the engine (prior knowledge, not re-verified): `gdal_translate -ot UInt16 -scale <min> <max> 0 65535 -of ENVI` to 16-bit RAW; Unity terrain heightmaps are 2^n+1 square (513, 1025, 2049, 4097) and imported in Terrain Settings with Import Raw (16-bit, set byte order and flip); Unreal landscapes prefer sizes like 1009, 2017, 4033, 8129; Roblox Terrain Editor imports a heightmap image. Unity manual: https://docs.unity.com/en-us/engine/6000.6/manual/creating-environments/script-terrain/terrain-heightmaps
4. Paint the ground from OSM: paths (`highway=footway|path`) as splines or decals, water (`natural=water`) as meshes, lawns and woods as terrain layers.
5. Objects: OSM gives many park trees (`natural=tree`), benches, playgrounds as points. Place your own low-poly asset kit at those points. Do not try to scan every tree.
6. Buildings: OSM or Overture footprints extruded by `height` or `building:levels` x 3 m; replace landmarks by hand-modelled or scanned versions.
7. Hero props: photograph a statue, fountain or gazebo for RealityScan or Metashape, retopologise, bake (section 6).
8. Optional photoreal layer: capture the park as a splat (360 camera or drone) for a web viewer or AI-video backplate; generate collision with `splat-transform --voxel-floor-fill`. Keep the mesh terrain as the gameplay truth.
9. Licence: credit "© OpenStreetMap contributors" in credits or splash screen (OSMF attribution guidelines cover games: splash screen, in-game view, credits or menu). https://osmfoundation.org/wiki/Licence/Attribution_Guidelines . Whether distributing OSM-derived 3D models in a game is a "Produced Work" or a database is unsettled; a 2021 legal-talk opinion says ODbL still applies when the derived objects ship. https://lists.openstreetmap.org/pipermail/legal-talk/2021-February/009061.html , https://community.openstreetmap.org/t/odbl-in-the-3d-topic/62486

### Best workflow: the same park as (b) a printable tabletop model (Bambu P1S, FDM)

1. Pick the print size first. The P1S bed is 256 x 256 mm (prior knowledge). A 400 m park at 1:2000 is 200 mm wide. At that scale a 2 m path is 1 mm wide, a 10 m tree is 5 mm tall, a bench vanishes.
2. Terrain: TouchTerrain with your area, or GDAL plus Blender displacement. Vertical exaggeration is the most important setting; a flat park needs a lot (UNM's guide says there is no magic number; x30 was used for a mountain range). Set base thickness explicitly; a hidden 1 mm base gets scaled with Z exaggeration. https://amaranth.unm.edu/projects/3d-pedagogy/terrain/ , https://community.carbide3d.com/t/touch-terrain-import-to-cc/100820 . Prusa suggests printing the exaggeration factor on the model. https://blog.prusa3d.com/cs/jak-vytisknout-svet-nejen-okolo-nas-na-3d-tiskarne/
3. Features as separate bodies: from OSM, extrude paths 0.4 to 0.6 mm above or recessed into the terrain, water recessed, buildings extruded to height. Export as a 3MF with one object per colour so Bambu Studio can assign AMS slots. Exaggerate widths: anything under about 0.8 mm (two 0.4 mm lines) will not print reliably (prior knowledge, rule of thumb).
4. Trees: replace OSM tree points with stylised printable trees (cone or lollipop on a 1.5 mm trunk), or print canopy as raised green blobs. Scanned or splat trees are useless at this scale.
5. Colour: either separate objects (best for AMS) or colour by layer height for strata-style terrain. Creators use 0.16 mm layers for smooth contours, 0.2 mm to cut colour changes; a brim on full-plate prints; one Mont Blanc map needed 117 AMS changes, a painted Japan map 32. https://makerworld.com/models/1174286 and related MakerWorld pages (seen 2026-10-11)
6. Thin features that vanish in the slicer: widen outer wall line width toward 0.4 mm or enable Arachne "Detect thin walls"; a 0.2 mm nozzle helps fine detail. https://makerworld.com/models/1404002
7. Check the mesh: watertight, manifold, no self-intersections (Blender 3D Print Toolbox, PrusaSlicer or Bambu Studio repair). Large areas: tile into puzzle pieces.
8. Attribution on physical items: OSMF guidelines require attribution on packaging for physical merchandise with OSM data, at point of sale, and if possible on the item, with the openstreetmap.org/copyright URL. https://osmfoundation.org/wiki/Licence/Attribution_Guidelines . Several MakerWorld city models also forbid commercial sale; check before reusing others' files.

### Failure modes for places

- OSM building heights missing: footprints extrude to a default; check `height` and `building:levels` coverage.
- DEM is a DSM (Copernicus): trees and buildings are baked into the terrain as bumps. Use a bare-earth DTM (3DEP DEM) where possible.
- CRS errors: lat/long degrees treated as metres gives stretched terrain. Reproject first.
- Seams between DEM tiles, voids in lidar under water.
- Google tiles used in a shipped game: licence breach.

## 5. Objects from measurements and reference

Time-honored and still the most reliable way to get clean, real-scale models of manufactured things:

- Gather dimensions: manufacturer spec sheets, product drawings, patent drawings, building plans, IKEA-style assembly sheets, calipers and a tape measure. Note units.
- Orthographic reference: photograph front, side and top with a long lens from far away (reduces perspective), with a ruler in the plane of the object. Set these up as Blender reference images, scale to the ruler.
- Blueprint setups: align views on a shared scale; model blocks first, then details. Do not trust blueprints from enthusiast sites without checking one known dimension.
- Camera matching from a single photo: fSpy (standalone, open source, cross-platform) solves the camera from vanishing lines; its Blender importer is reported broken or abandoned after Blender 4.0 by users, and Perspective Plotter (Blender Market) is the suggested alternative. Copy camera parameters by hand if the importer fails. https://github.com/stuffmatic/fSpy , https://blenderartists.org/t/install-fspy-on-blender-4-2-2-lts/1561632 (seen 2026-10-11)
- Measuring from photos: a known reference length in the same plane plus a matched camera gives usable dimensions; errors grow with depth from that plane.
- Real scale: model in metres (glTF, Unity, Unreal, three.js use metres; Roblox uses studs, 1 stud is about 0.28 m by common convention; prior knowledge, not re-verified). For printing, millimetres in STL/3MF.
- Hybrid: scan for proportions and organic parts, then model the hard surfaces over the scan.

## 6. Cleanup after capture

Pipeline for a scanned prop that must become a game asset (consensus from tool docs and forum posts, seen 2026-10-11 unless marked):

1. Crop and clean: remove the turntable, floor and floating fragments (RealityScan selection tools, Metashape, MeshLab, Blender).
2. Scale and orient: set real-world scale from the scale bar or measured distance; put the up axis right; origin at the base centre.
3. Fill holes and make watertight if printing: Blender 3D Print Toolbox, PyMeshLab (`meshing_close_holes`), PrusaSlicer or Bambu Studio repair, Poisson reconstruction for a closed surface (prior knowledge for function names).
4. Decimate a copy: quadric edge collapse (MeshLab/PyMeshLab, Blender Decimate, RealityScan `-simplify`). Keep the dense mesh for baking.
5. Retopologise: Instant Meshes or QuadriFlow (in Blender) for props; Quad Remesher (commercial) is popular; hand retopology for characters and deforming meshes. Instant Meshes destroys UVs, so you must bake, not reuse maps. https://sketchfab.com/blogs/community/retopologise-3d-scans-low-poly-game-assets/ ; a BlenderArtists user bakes a 5M-vertex, 16k scan onto a retopo after clearing sharp edges and using an enlarged cage. https://blenderartists.org/t/retopology-keeping-projecting-details-from-the-high-poly-modell-to-the-low-poly/1427780?page=2 . Blender add-ons RetopoGen, RepliBake and Mesh Prep Studio wrap QuadriFlow, Instant Meshes and Cycles baking. https://superhivemarket.com/products/retopogen
6. UV unwrap: Blender Smart UV, RizomUV, or the scanner's own unwrap (RealityScan 2.1 improved UV and defrags textures by default).
7. Bake: normal, AO, colour (and roughness if you have cross/parallel polarised data) from dense to low; Blender Cycles, Marmoset Toolbag, Substance Painter, xNormal (prior knowledge for the last three).
8. Delight: remove baked shadows from the colour map. Options: cross-polarised capture (best, at the source); Agisoft De-Lighter (free, paint lit and shadowed areas, needs a model); Unity's experimental De-Lighting Tool (2017, uses AO, normal, bent normal); Substance Designer node methods; new neural delighters appearing (a Reddit user trained one in 2026-07; a "MATCLONE" PBR capture prototype was shown 2026-09). https://cgpress.org/archives/agisoft-de-lighter-released.html , https://blog.unity.com/en/technology/experimental-feature-de-lighting-tool , https://www.reddit.com/r/photogrammetry/comments/1vb1boz/ai_powered_photogrammetry_delighting/ , https://www.reddit.com/r/photogrammetry/comments/1w7fomu/pbr_software_alpha_test/
9. Texture reprojection: when you edit geometry, re-project the original photos with RealityScan or Metashape texturing onto the new mesh, or bake from the old textured mesh.
10. LODs and export: glTF/GLB for web and Roblox import pipelines, FBX for Unity and Unreal; Draco or meshopt compression for the web.

## 7. What working experts say (summary of tips, failure modes and disagreements)

Tips:
- Light beats software: cross-polarisation or overcast light fixes more than any setting. (Reddit r/photogrammetry, many posts 2021 to 2026)
- Capture more than you think at transitions; missing roof fronts and steps are the classic gaps. (Chapel game-map thread, 2025-12-08)
- Separate passes for different object orientations, merge after. (Artec post, 2026-01-23)
- Stream big splats; never ship PLY to the web. (SuperSplat threads, 2026)
- Splat games: voxel collision plus a baked light grid is the working recipe in 2026. (PlayCanvas posts and threads, 2026-03 to 2026-06)
- For engines, real places are usually rebuilt from map data plus asset kits rather than scanned wholesale; a gamedev.tv hobbyist built low-poly Carcassonne from Blosm data and hand-made modular walls. https://community.gamedev.tv/t/modular-castle-low-poly-carcassonne/215384

Common failure modes reported:
- Fragmented meshes even with good alignment (heads, thin parts). Try another engine; Apple Object Capture handled one case.
- One-component alignment failure in RealityScan on mixed drone and ground sets.
- Trees flatten in drone meshes; wind ruins foliage.
- Reflections baked into textures from phone captures under room light. (2023-10 product-scan thread: https://www.reddit.com/r/photogrammetry/comments/17ci56p/cross_polarisation_and_turntable_setup_help/)
- Cloud phone apps vary 2 to 10 minutes with server load.

Disagreements:
- RealityScan versus Metashape: speed and GPU scaling (RealityScan) versus robustness, survey tools and a friendlier UI (Metashape). Both camps are vocal.
- Splats versus meshes for games: splat enthusiasts call voxel collision "the future of games"; skeptics point to no shadows, no relighting in standard engines, chunk seams, and file size.
- Feed-forward AI reconstruction versus COLMAP: faster and works with few photos, but papers find COLMAP still more precise for dense captures (GASE 2026, GA-GS 2026).
- Handheld scanners: spec sheets claim 0.01 to 0.1 mm; owners report software quality and tracking matter more than the spec.

Coverage gap: Polycount, CGSociety, Hacker News and 80.lv threads could not be found within the search budget; this section is based mainly on Reddit RSS (three feeds), OpenDroneMap and Cesium forums, BlenderArtists, MakerWorld and vendor blogs.

## 8. Academic state of the art (arXiv ids, seen 2026-10-11)

Foundations:
- 3D Gaussian Splatting, Kerbl et al., SIGGRAPH 2023, arXiv 2308.04079 (prior knowledge of id).
- NeRF, Mildenhall et al., 2020, arXiv 2003.08934 (prior knowledge of id).
- COLMAP SfM (Schoenberger and Frahm, CVPR 2016); GLOMAP global SfM, arXiv 2407.20219 (prior knowledge of id).

Feed-forward reconstruction (poses and geometry in one pass):
- DUSt3R arXiv 2312.14132 and MASt3R arXiv 2406.09756 (prior knowledge of ids); CC BY-NC-SA, non-commercial.
- VGGT, CVPR 2025 best paper (prior knowledge), arXiv 2503.11651; code commercial-friendly since 2025-07-29, only the VGGT-1B-Commercial checkpoint is commercial; `demo_colmap.py` exports COLMAP sparse models for gsplat; 2026-05-15 update fits 2 to 3x more frames in the same memory. https://github.com/facebookresearch/vggt
- VGGT-X, arXiv 2509.25191: VGGT for dense novel view synthesis with global alignment and joint pose plus 3DGS training.
- Pi3 (π³), arXiv 2507.13347: permutation-equivariant, no reference view; BSD-2 for academic use, commercial use by contacting authors.
- MapAnything, arXiv 2509.13414 (Meta and CMU): metric 3D from images plus optional intrinsics, poses or depth.
- Depth Anything 3, arXiv 2511.10647: depth plus ray maps, reported to beat VGGT on pose and geometry.
- WorldMirror, arXiv 2510.10726: universal reconstruction with any-prior prompting.
- Apple SHARP: single image to metric splat, MIT.
- Surveys: "Review of Feed-forward 3D Reconstruction: From DUSt3R to VGGT", arXiv 2507.08448; "Advances in Feed-Forward 3D Reconstruction and View Synthesis: A Survey", arXiv 2507.14501 (v4); analysis paper arXiv 2512.11508.
- Head-to-head in practice: GASE (arXiv 2606.17520) and GA-GS (arXiv 2604.04331) report that COLMAP initialisation still beats VGGT, DA3 and Pi3 on precision (gap visible in LPIPS); feed-forward wins on sparse views and speed. Gesplat (arXiv 2510.10097) for pose-free splatting.

Surface reconstruction from splats: SuGaR 2311.12775, 2DGS 2403.17888, GOF 2404.10772, GS2Mesh 2404.01810, PGSR 2406.06521, MILo 2506.24096, OMeGa 2509.24308 (joint mesh and splat), SolidGS 2412.15400 (sparse view), G2SDF 2411.16898, AnyGS2Mesh 2609.03304 (2026-09, feed-forward meshing that lifts 2DGS and GGGS pipelines).

Hybrid photogrammetry and splats: "Combining Photogrammetry and Gaussian Splatting", ISPRS Archives XLIX-B2-2026, p. 1363. https://isprs-archives.copernicus.org/articles/XLIX-B2-2026/1363/2026/

Phone scanning accuracy: ISPRS Archives XLIX-M-1-2026, p. 1 (five iPhone apps against TLS).

## Open questions / unverified

- Postshot plan prices: the pricing page renders EUR 0.00 for all plans in a fetch; real prices load by script. Check in a browser.
- Metashape: is Python scripting truly Professional-only in 2.3? Comparison table columns did not render.
- RealityScan 2.1 release date: radiancefields byline 2025-11-25 versus Epic's page 2026-04-21.
- RealityScan CLI on macOS: none found; Linux CLI only under Wine.
- Brush: no release newer than 0.3 (2025-09) found; GitHub releases section empty in fetch.
- KHR_gaussian_splatting exact ratification date (registry says ratified; announcement of ratification not found). Compression companion extension (SPZ-based) status unknown.
- WebODM after the April 2026 split: does the free installer still exist for Windows, and do splat outputs work in ODX? Not verified.
- OpenMVS licence and the newest release date; Meshroom 2026 stable release (none found beyond 2025.1.0; develop nightly 2026-08-20).
- Overture buildings: license confirmed ODbL on the attribution page, but release cadence and height coverage outside the US not checked.
- OpenTopography: is USGS 1 m via API still academic-only in 2026? Policy text is from 2023.
- Unity heightmap sizes, Unreal landscape sizes, Roblox heightmap import details, GDAL commands, and P1S bed size are prior knowledge, not re-verified this session.
- Handheld scanner accuracy: no independent 2026 head-to-head found (the ISPRS 2026 low-cost scanner preprint was not read: https://isprs-archives.copernicus.org/articles/XLIX-B1-2026/263/2026/isprs-archives-XLIX-B1-2026-263-2026.pdf).
- Whether shipping OSM-derived 3D meshes in a game counts as a Produced Work or a Derivative Database under ODbL: unsettled.
- Practitioner coverage from Polycount, CGSociety, Hacker News and 80.lv is missing (search budget exhausted). Next session: resume the Reddit RSS loop (one request per 50 to 60 s, 429s happen) for r/gis, r/3Dprinting, r/gamedev, r/blender, r/3DScanning.
- A 2026-10-10 Reddit post announces 3DPEER, a WebGPU editor mixing splats and meshes with splat-to-mesh conversion; not evaluated. https://www.reddit.com/r/GaussianSplatting/comments/1x2dtvp/
