# 3D tools an agent can script, per OS

Back to [SKILL.md](../SKILL.md). Versions and dates from PyPI, npm and GitHub on 2026-10-11 (polywright
research note `2026-10-11-blender-and-tooling.md`). Y official build or wheel, P partial, N none.

| Tool | Version | Licence | Win | Mac | Linux | Install | Use it for |
|---|---|---|---|---|---|---|---|
| Blender | 5.2 LTS (5.2.2 out) | GPL | Y | Y (Apple Silicon) | Y | blender.org, winget, Steam, snap | everything |
| bpy (pip) | 5.2.2 | GPL | Y | Y (arm64) | Y (x86_64) | `pip install bpy` on Python 3.13 only | Blender in a plain Python, CI |
| trimesh | 5.1 | MIT | Y | Y | Y | pip | load, measure, watertight, convert, 3MF |
| manifold3d | 3.5 | Apache-2.0 | Y | Y | Y | pip | guaranteed-manifold booleans, status check |
| PyMeshLab | 2025.7 | GPL-3 | Y | Y | Y | pip | repair, close holes, Poisson, quadric decimation |
| Open3D | 0.20 | MIT | Y | Y | Y | pip | point clouds, registration, TSDF |
| fast-simplification | 0.2 | MIT | Y | Y | Y | pip | quick quadric decimation |
| xatlas | 0.0.11 | MIT | P (to Python 3.13) | P | P | pip | UV packing outside Blender |
| usd-core | 26.8 | Apache-like | Y | Y | Y | pip | USD/USDZ inspection, `usdchecker --arkit` |
| build123d | 0.13 | Apache-2.0 | Y | Y | Y | pip (Python 3.11 to 3.14) | code CAD, STEP |
| CadQuery | 2.8 | Apache-2.0 | Y | Y | Y | pip | code CAD, STEP |
| OpenSCAD | 2021.01 stable; nightlies with Manifold | GPL-2 | Y | Y | Y | openscad.org | CSG solids, fast with Manifold |
| FreeCAD (`freecadcmd`) | 1.1 | LGPL-2 | Y | Y | Y | freecad.org | editing existing CAD |
| gltf-transform | 4.5 | MIT | Y | Y | Y | `npm i -g @gltf-transform/cli` | optimise, meshopt, KTX2, inspect |
| gltfpack | 1.3 | MIT | Y | Y | Y | npm or binary | LODs, meshopt compression |
| glTF-Validator | 2.0.0-dev | Apache-2.0 | Y | Y | Y | `npm i -g gltf-validator` | spec validation, non-zero exit on errors |
| Assimp | 6.0 | BSD | Y | Y | Y | vcpkg, brew, apt | odd formats (pyassimp is stale) |
| Bambu Studio CLI | 2.08 | AGPL-3 | Y | Y | Y | bambulab.com | 3MF, orient, arrange, slice |
| PrusaSlicer CLI | 2.9 | AGPL-3 | Y | Y | Y | prusa3d.com | repair, slice |
| OrcaSlicer | 2.4 | AGPL-3 | Y | Y | Y | GitHub | slice |
| COLMAP | 4.2 | BSD | Y (CUDA) | Y (CPU) | Y | GitHub, `pip install pycolmap` | photogrammetry poses |
| OpenMVS | 2.4 | AGPL-3 | Y (build) | P | Y | GitHub | dense, mesh, texture |
| splat-transform | 3.10 | MIT | Y | Y | Y | npm | splat formats, collision |
| Instant Meshes | 2022 binary | BSD | Y | Y | Y | stale | field-aligned quad remesh |
| Houdini (hython) | commercial | | Y | Y | Y | SideFX (Apprentice limits) | procedural at scale |

Wheel gaps on Python 3.14 (2026-10): libigl, pymeshfix (to 3.12), xatlas (to 3.13). Keep a 3.12 or 3.13 venv
for them.

## Default chains

| Target | Chain | Checks |
|---|---|---|
| Game asset | model, apply transforms, triangulate, UV, bake, GLB; `gltfpack` or `pw.py lods` for LODs | `pw.py check`, gltf_validator |
| Unity | GLB through glTFast, or FBX with baked axes and unit scale | import test in the project (unity-agent) |
| Roblox | FBX, OBJ or glTF per MeshPart, under 20k triangles, one material, OpenGL normals | `pw.py check --target game-roblox` |
| Unreal | FBX, GLB or USD; the importer handles centimetres | scale on import |
| Print | Blender or code CAD, voxel remesh or Manifold union, STL in mm, 3MF through a slicer CLI | `pw.py check --target print-fdm`, slicer report |
| Web | GLB, `gltf-transform optimize --compress meshopt --texture-compress ktx2` | validator, size budget, a page check (threewright) |
| AR iOS | `wm.usd_export` to .usdz with preview surface and downscaled textures | `usdchecker --arkit` |
| AI video | blockout, Workbench or EEVEE renders, depth, normal and mist passes | pass images non-empty, depth normalised |
| CAD | build123d, CadQuery or FreeCAD; STEP plus STL or GLB preview | reopen the STEP, compare volume |
