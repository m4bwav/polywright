# Blender and 3D tooling an agent can drive (research, 2026-10-11)

Research for polywright, the planned all-round 3D modeling plugin. Topic: which tools an agent can script, Blender first, and what runs on Windows, macOS and Linux.

How this was gathered:
- Local probes against Blender 5.2.1 LTS on the owner's Windows 11 PC (RTX 5060 Ti). Exact commands and output are in the "verified locally" section.
- Registry lookups: PyPI JSON API, npm registry, GitHub releases API (via `gh`). All dates are what the registry reported on 2026-10-11.
- Primary pages fetched on 2026-10-11: blender.org release pages, blender.org/lab/mcp-server, extensions.blender.org, create.roblox.com, the Bambu Studio wiki, openscad.org, the glTF-Validator README, the mcp-for-blender README and source.
- Limits: developer.blender.org and docs.blender.org sat behind a Cloudflare challenge (HTTP 403 to fetch and curl; a click-through challenge in Chrome, which an agent must not solve). The 5.0/5.1/5.2 Python API pages were therefore read through search snippets and the blender.org release pages, and the key claims were then checked in the local Blender. The session's shared web-search budget ran out partway, so the practitioner section is thinner than planned. See "Open questions".

## Bottom line

1. Target Blender 5.2 LTS (released 2026-07-14, supported to July 2028). 5.2.2 is out (bpy 5.2.2 on PyPI, 2026-09-15); the owner has 5.2.1. Next feature release 5.3 is reported for 2026-11-10 (secondary source).
2. Always run Blender as `blender --background --factory-startup --python-exit-code 1 --python script.py -- args`. Without `--python-exit-code`, a Python exception still exits 0 (verified locally). This is the single most important flag for an agent.
3. Use the C++ I/O operators: `bpy.ops.wm.obj_import/obj_export`, `wm.stl_import/stl_export`, `wm.ply_import/ply_export`, `wm.usd_import/usd_export`, `wm.fbx_import` (new C++ FBX importer). FBX export is still `export_scene.fbx`; glTF is still `import_scene.gltf` / `export_scene.gltf`. The old `import_scene.obj`, `import_mesh.stl`, `import_mesh.ply` and all Collada operators are gone (verified).
4. Models will emit removed APIs. Guard against: `import bgl` (gone), `BLENDER_EEVEE_NEXT` (gone; it is `BLENDER_EEVEE` again), `action.fcurves` (gone since 5.0; use slots and channelbags), `material.use_nodes` / `scene.node_tree` (deprecated or removed in 5.0), `modifier["Socket_2"] = x` on Geometry Nodes modifiers (fails in 5.2; use `mod.properties.inputs.Socket_2.value = x`, verified).
5. Prefer data-level `bpy.data` and `bmesh` over `bpy.ops`. Operators that need a 3D viewport (`view3d.*`, `screen.screenshot`, `render.opengl`) fail in background mode. Many others (`uv.smart_project`, `object.mode_set`, `object.quadriflow_remesh`, modifiers) work headless (verified for Smart UV).
6. Headless rendering works on Windows for all three engines: Workbench 1.1 s, EEVEE 10.6 s (first-run shader compile), Cycles OptiX 2.2 s at 320x240 (verified). Use Workbench or EEVEE for review sheets, Cycles for bakes.
7. Agent bridges: Blender Lab's official MCP server (v1.0.3, needs Blender 5.1+, GPL) and the community `mcp-for-blender` (formerly blender-mcp, MIT, 30.5k stars, PyPI 2.1.9 on 2026-10-06). Both run arbitrary Python with no real sandbox and both default to port 9876. For polywright, headless scripts are the safer default; MCP is for live, user-watched sessions.
8. For pure mesh work outside Blender, the Python stack is trimesh + manifold3d + fast-simplification + pymeshlab, all with Windows wheels. Check Python version: libigl and pymeshfix have no cp313/cp314 wheels; xatlas stops at cp313; bpy needs exactly 3.13.
9. Print chain: Blender or code-CAD (build123d/OpenSCAD with Manifold backend) -> manifold check (manifold3d status, trimesh `is_watertight`) -> 3MF/STL -> Bambu Studio CLI `--orient --arrange 1 --slice 0 --export-3mf`.
10. Game chain: Blender -> glTF/GLB with Draco or meshopt (Blender 5.2 exporter has `export_meshopt_compression_enable`, verified) -> `gltf-transform` / `gltfpack` for LODs and KTX2 -> `gltf_validator` (non-zero exit on errors). Roblox: 20,000 triangles per mesh, 4 bone influences per vertex, one material per mesh (create.roblox.com, fetched 2026-10-11).
11. AR chain: Blender `wm.usd_export` to `.usdz` (has `usdz_downscale_size`, `generate_preview_surface`), or `usd-core` 26.8 tools. Video chain: Blender renders with depth/normal/mist passes from the compositor for ControlNet-style conditioning.
12. Verification without eyes: numeric checks first (manifold, bodies, extents in mm, tri count, texture sizes, glTF-Validator), then a contact sheet of 6 to 8 Workbench/EEVEE views for a vision model, then silhouette IoU against reference images.
13. macOS: Blender 5.x and the bpy wheel are Apple Silicon only (bpy 5.2.2 ships `macosx_11_0_arm64` only). Linux bpy wheels are x86_64 only. Plan around that.
14. Extensions: the 3D Print Toolbox is now an extension (v1.4.1, 2026-08-05, Blender 4.2+). Install headless with `blender --command extension install`, but online access is off by default (`bpy.app.online_access False`, verified) and the remote repo has never been synced on this machine.

## Per-OS tool availability

Legend: Y = official build or wheel, P = partial, N = none, ? = unverified. Versions and dates from registries on 2026-10-11.

| Tool | Version (date) | Licence | Windows | macOS | Linux | Install route |
|---|---|---|---|---|---|---|
| Blender | 5.2.1 LTS local; 5.2.2 out | GPL | Y | Y (Apple Silicon only, see notes) | Y | blender.org, winget, Steam, snap |
| bpy (pip) | 5.2.2 (2026-09-15) | GPL-3.0 | Y (amd64, arm64) | Y (arm64 only) | Y (x86_64 glibc 2.28+) | `pip install bpy` on Python 3.13 only |
| mcp-for-blender | 2.1.9 (2026-10-06) | MIT | Y | Y | Y | `uvx mcp-for-blender` + addon |
| Blender Lab MCP | 1.0.3 (Sep 2026) | GPL-3.0+ | Y | Y | Y | extension zip + .mcpb bundle, Blender 5.1+ |
| trimesh | 5.1.1 (2026-10-02) | MIT | Y | Y | Y | pip, pure Python |
| manifold3d | 3.5.4 (2026-09-25) | Apache-2.0 | Y | Y | Y | pip, cp39 to cp314 |
| Open3D | 0.20.0 (2026-09-16) | MIT | Y | Y (arm64) | Y | pip, cp310 to cp314 |
| PyMeshLab | 2025.7.post1 (2026-01-30) | GPL-3 | Y | Y | Y | pip, cp310 to cp314 |
| PyVista | 0.49.1 (2026-10-11) | MIT | Y | Y | Y | pip (VTK wheels) |
| libigl (Python) | 2.6.3 (2026-09-01) | MPL-2/GPL parts | P (cp38 to cp312) | P | P | pip, no 3.13/3.14 wheels |
| xatlas (Python) | 0.0.11 (2025-07-04) | MIT | P (to cp313) | P | P | pip |
| pymeshfix | 0.18.1 (2026-04-23) | GPL? | P (to cp312) | P | P | pip |
| fast-simplification | 0.2.0 (2026-08-12) | MIT | Y | Y | Y | pip, cp310 to cp314 |
| pygltflib | 1.16.5 (2025-07-24) | MIT | Y | Y | Y | pip |
| numpy-stl | 4.0.1 (2026-09-07) | BSD-3 | Y | Y | Y | pip |
| usd-core (OpenUSD) | 26.8 (2026-07-20) | TOST-1.0 (Apache-like) | Y | Y | Y (x86_64) | pip, Python below 3.15 |
| build123d | 0.13.0 (2026-09-21) | Apache-2.0 | Y | Y | Y | pip, Python 3.11 to 3.14 |
| CadQuery | 2.8.0 (2026-06-21) | Apache-2.0 | Y | Y | Y | pip, Python 3.11+ |
| OpenSCAD | stable 2021.01; nightly with Manifold default | GPL-2 | Y (nightly, Win 11 x64) | Y (universal) | Y (AppImage, snap) | openscad.org snapshots |
| FreeCAD (`freecadcmd`) | 1.1.4 (2026-09-28) | LGPL-2 | Y | Y | Y | freecad.org, conda |
| Zoo / KittyCAD CLI | v0.2.203 (2026-10-07) | MIT? | Y | Y | Y | GitHub releases; cloud API, paid tiers |
| gltf-transform CLI | 4.5.1 (2026-09-28) | MIT | Y | Y | Y | `npm i -g @gltf-transform/cli` |
| gltfpack | 1.3.0 (2026-09-25) | MIT | Y | Y | Y | `npm i -g gltfpack` or GitHub binary |
| glTF-Validator | npm 2.0.0-dev.3.10 (2024-10-22) | Apache-2.0 | Y | Y | Y | `npm i -g gltf-validator` or build |
| Assimp | 6.0.5 (2026-04-30) | BSD-3 | Y | Y | Y | vcpkg, brew, apt; pyassimp is stale (2023) |
| MeshLab | 2025.07 (2025-07-22) | GPL-3 | Y | Y | Y | GUI; use PyMeshLab for scripting |
| admesh | 0.98.5 (2022-11-21) | GPL-2 | P (build) | Y (brew) | Y (apt) | stale but works |
| Bambu Studio CLI | 02.08.02.61 (2026-08-21) | AGPL-3 | Y (installed locally) | Y | Y (AppImage, flatpak) | bambulab.com, GitHub |
| PrusaSlicer CLI | 2.9.6 (2026-06-25) | AGPL-3 | Y | Y | Y | prusa3d.com |
| OrcaSlicer | 2.4.2 (2026-07-07) | AGPL-3 | Y | Y | Y | GitHub |
| COLMAP | 4.2.1 (2026-09-29) | BSD-3 | Y (CUDA builds) | Y (CPU) | Y | GitHub, `pip install pycolmap` 4.2.1 |
| OpenMVS | 2.4.0 (2026-01-20) | AGPL-3 | Y (build/vcpkg) | P | Y | GitHub |
| Meshroom | 2025.1.0 (2025-08-19) | MPL-2 | Y | N (no official) | Y | GitHub, needs CUDA |
| OpenDroneMap ODM | 3.6.2 (2026-08-12) | AGPL-3 | Y (Docker) | Y (Docker) | Y | Docker |
| splat-transform (PlayCanvas) | 3.10.1 (2026-10-09) | MIT | Y | Y | Y | npm |
| gsplat | 1.5.3 (2025-07-04) | Apache-2.0 | Y (CUDA) | N | Y (CUDA) | pip, needs CUDA |
| Instant Meshes | no release, last push 2022-01-03 | BSD | Y (old binary) | Y | Y | stale |
| Houdini (hython) | ? | commercial | Y | Y | Y | SideFX; Apprentice limits, see text |
| Maya (mayapy) / 3ds Max | ? | commercial | Y | Y (Maya) | Y (Maya) | Autodesk subscription |

Locally present on the owner's PC (checked 2026-10-11): Blender 5.2.1 and 3.6, Bambu Studio, Unity and Epic Games launcher folders, Node via <local path>, Python 3.14 (trimesh 5.1.0, manifold3d 3.5.2, fast-simplification 0.2.0, numpy 2.5.2) and Python 3.11 (trimesh 5.1.0). Not on PATH: openscad, meshlab, colmap, gltf-transform, gltfpack, admesh, freecadcmd, assimp, and blender itself (call by full path). No Python 3.13 in the `py` launcher list (3.14, 3.11, Astral 3.14.7, 3.12.14, 3.9.25), so `pip install bpy` would need a uv-managed 3.13.

## Blender 5.x API facts verified locally

Binary: the Blender 5.2.1 install on a Windows 11 PC. All runs used `--background --factory-startup`. Probe scripts lived in the session scratchpad and are not kept.

Version line printed by `bpy.app`:
```
VERSION 5.2.1 LTS (5, 2, 1) PY 3.13.13 (main, May  8 2026, 12:37:03) [MSC v.1944 64 bit (AMD64)]
BUILD b'2026-08-25' b'9e2066aef7ef'
```

Exit codes:
```
blender --background --factory-startup --python-expr "raise RuntimeError('x')"            -> exit 0
blender --background --factory-startup --python-exit-code 3 --python-expr "raise ..."      -> exit 3
```
A failing `--python` script prints `Error: script failed, file: ..., exiting.` but still exits 0 without the flag.

Operator presence (`hasattr(bpy.ops.<mod>, <op>)` plus `get_rna_type()`):

| Present (True) | Absent (False) |
|---|---|
| wm.obj_import, wm.obj_export | import_scene.obj, export_scene.obj |
| wm.stl_import, wm.stl_export | import_mesh.stl, export_mesh.stl |
| wm.ply_import, wm.ply_export | import_mesh.ply, export_mesh.ply |
| wm.usd_import, wm.usd_export | wm.collada_import, wm.collada_export |
| wm.alembic_import, wm.alembic_export | wm.fbx_export (FBX export stays Python) |
| wm.fbx_import (C++), import_scene.fbx, export_scene.fbx | wm.gltf_import |
| import_scene.gltf, export_scene.gltf | import_image.to_plane (old addon name) |
| image.import_as_mesh_planes, object.empty_image_add | mesh.print3d_check_all (extension not installed) |
| object.quadriflow_remesh, object.voxel_remesh | wm.svg_import |
| uv.smart_project, uv.lightmap_pack, object.bake | geometry.execute_node_group |
| wm.grease_pencil_import_svg, import_curve.svg | |
| extensions.package_install | |

Render engines:
```
default engine BLENDER_EEVEE
ENGINE OK BLENDER_EEVEE / CYCLES / BLENDER_WORKBENCH
ENGINE FAIL BLENDER_EEVEE_NEXT: enum "BLENDER_EEVEE_NEXT" not found in ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES')
RenderEngine subclasses: HydraRenderEngine (Storm), CYCLES
```

Removed or changed modules and data:
```
import bgl                -> No module named 'bgl'
gpu.platform.* in background without init -> SystemError: ... requires the gpu module to be initialized. See gpu.init.
gpu.init()                -> ok, OPENGL, NVIDIA GeForce RTX 5060 Ti/PCIe/SSE2
bpy.data.actions.new("a") -> has .slots True, .layers True, .fcurves False
bpy.data.grease_pencils   -> exists (GP v3 types: GreasePencil, GreasePencilDrawing, ...); no grease_pencils_v3
bpy.context.temp_override -> exists
```

Modifier enums:
```
BOOLEAN solver: ['FLOAT', 'EXACT', 'MANIFOLD']   default EXACT
REMESH mode:    ['BLOCKS', 'SMOOTH', 'SHARP', 'VOXEL']
DECIMATE type:  ['COLLAPSE', 'UNSUBDIV', 'DISSOLVE']
WELD, SOLIDIFY, SHRINKWRAP, SUBSURF, NODES, TRIANGULATE, WEIGHTED_NORMAL all create fine.
```
Note: Corrective Smooth's type id is `CORRECTIVE_SMOOTH`; a guessed `SMOOTH_CORRECTIVE` raised and aborted the probe. Agents should read enum items instead of guessing.

Geometry Nodes modifier inputs in 5.2 (the 5.2 breaking change):
```
socket = node_group.interface.new_socket("Size", in_out="INPUT", socket_type="NodeSocketFloat")
socket.identifier                          -> 'Socket_2'
mod[socket.identifier] = 2.0               -> TypeError: id properties not supported for this type
setattr(mod, 'Socket_2', 2.0)              -> AttributeError
mod.properties.inputs.Socket_2 = 3.0       -> read-only
mod.properties.inputs.Socket_2.value = 4.0 -> OK
mod.properties has: inputs, outputs, panels; each input has value, attribute_name, name, type
```

Principled BSDF inputs in 5.2 (exact names, 32 sockets):
```
Base Color, Metallic, Roughness, IOR, Alpha, Thin Wall, Normal, Weight, Diffuse Roughness,
Subsurface Weight, Subsurface Radius, Subsurface Scale, Subsurface IOR, Subsurface Anisotropy,
Specular IOR Level, Specular Tint, Anisotropic, Anisotropic Rotation, Tangent,
Transmission Weight, Coat Weight, Coat Roughness, Coat IOR, Coat Tint, Coat Normal,
Sheen Weight, Sheen Roughness, Sheen Tint, Emission Color, Emission Strength,
Thin Film Thickness, Thin Film IOR
```
Models trained on 3.x still write `Specular`, `Subsurface`, `Transmission`, `Emission`, `Clearcoat`; those names are gone.

Key operator parameters:
```
export_scene.gltf (110 props) includes: export_format, export_image_format, export_image_add_webp,
  export_meshopt_compression_enable, export_meshopt_extension, export_draco_mesh_compression_enable,
  export_draco_mesh_compression_level, export_draco_*_quantization, export_yup, export_apply
  Log line: "Draco is available" and "MeshOptimizer is available" (bundled bridge DLLs).
wm.stl_export: ascii_format, use_batch, export_selected_objects, collection, global_scale, use_scene_unit,
  forward_axis, up_axis, apply_modifiers, evaluation_mode
wm.stl_import: global_scale, use_scene_unit, use_facet_normal, forward_axis, up_axis, use_mesh_validate
wm.obj_export: apply_modifiers, apply_transform, export_triangulated_mesh, export_pbr_extensions, path_mode, ...
wm.fbx_import: global_scale, mtl_name_collision_mode, use_custom_normals, ignore_leaf_bones, validate_meshes, use_anim
wm.usd_export: generate_preview_surface, generate_materialx_network, export_textures_mode, triangulate_meshes,
  usdz_downscale_size, convert_scene_units, meters_per_unit, root_prim_path, ...
uv.smart_project: angle_limit, margin_method, rotate_method, island_margin, area_weight, correct_aspect, scale_to_bounds
object.quadriflow_remesh: use_mesh_symmetry, use_preserve_sharp, use_preserve_boundary, preserve_attributes,
  smooth_normals, mode, target_ratio, target_edge_length, target_faces, mesh_area, seed
object.bake types: COMBINED, AO, SHADOW, POSITION, NORMAL, UV, ROUGHNESS, EMIT, ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION
object.bake params: use_selected_to_active, cage_extrusion, max_ray_distance, cage_object, normal_space, margin, margin_type, target
image.import_as_mesh_planes: shader, emit_strength, use_transparency, align_axis, size_mode, height, ...
```

Headless render test (default cube plus a monkey, 320x240):
```
RENDER OK BLENDER_WORKBENCH 1.08 s
RENDER OK BLENDER_EEVEE     10.56 s  (includes shader compile)
RENDER OK CYCLES            2.15 s   (OptiX, 16 samples)
glTF export with meshopt: 35,864 bytes
```

Viewport-bound operators in background:
```
view3d.view_all       -> poll() Expected a view3d region
view3d.view_selected  -> poll() Expected a view3d region
screen.screenshot     -> poll() failed, context is incorrect
render.opengl         -> Cannot use OpenGL render in background mode (no opengl context)
object.mode_set + mesh.select_all + uv.smart_project -> OK headless
view3d.camera_to_view_selected -> returned without error (but do the framing math yourself)
```

Cycles devices seen: CUDA and OPTIX (RTX 5060 Ti), HIP (AMD Radeon integrated graphics), ONEAPI none. `METAL` is not an enum value on Windows.

Add-ons enabled with `--factory-startup`: bl_pkg, cycles, io_anim_bvh, io_curve_svg, io_mesh_uv_layout, io_scene_fbx, io_scene_gltf2, pose_library. Available but off: hydra_storm, node_wrangler, rigify, ui_translate, viewport_vr_preview.

Extensions:
```
blender --command help       -> asset_listing, extension, maketx
blender --command extension  -> server-generate, build, validate, list, sync, update, install, install-file,
                                remove, repo-list, repo-add, repo-remove
blender --command extension list -> "Repository data ... blender_org not found, sync required!"
bpy.app.online_access False (override False)
repos: extensions.blender.org (https://extensions.blender.org/api/v1/extensions/), User Default, System
```
Useful CLI flags from `blender --help`: `-E/--engine`, `-t/--threads`, `--cycles-device OPTIX` (after `--`), `--python-expr`, `--python-exit-code`, `--python-use-system-env`, `--addons`, `--online-mode`, `--offline-mode`, `-q/--quiet`, `-X/--factory-startup`, `-noaudio`, `--disable-crash-handler`, `-c/--command`.

Outside Blender, the same day:
```
Blender: bpy.ops.mesh.primitive_monkey_add(); bpy.ops.wm.stl_export(...)  (default cube + monkey)
trimesh 5.1.0: faces 980, watertight False, winding True, bodies 4, extents [2.734 2. 2.]
manifold3d: Manifold(Mesh(...)).status() -> Error.NotManifold
```
Suzanne's open eye shells make it non-manifold, so this is a handy negative test case.

## 1. Blender as of October 2026

Releases and cadence (blender.org release pages, fetched 2026-10-11):
- 5.0: 2025-11-18; 5.0.1 2025-12-16.
- 5.1: 2026-03-17; 5.1.1 2026-04-14; 5.1.2 2026-05-19.
- 5.2 LTS: 2026-07-14, fixes until July 2028. bpy 5.2.2 on PyPI 2026-09-15 implies Blender 5.2.2.
- 5.3: reported for 2026-11-10, alpha makes Vulkan the default on Windows and Linux (cinevva guide, 2026-09-06; secondary).
- Cadence: three releases a year (roughly March, July, November), with the July release being LTS in the 5.x series. Previous LTS: 4.5 (last with Collada, and per memory the last with Intel Mac support).

What 5.0 changed for scripts (blender.org 5.0 page plus search snippets of developer.blender.org/docs/release_notes/5.0/python_api, BlenderArtists 2026-03-21):
- Legacy Action API removed: `action.fcurves`, `action.groups`, `action.id_root`. Replacement: slots and channelbags. Use `bpy_extras.anim_utils.action_ensure_channelbag_for_slot(action, slot)` then `channelbag.fcurves.new()` or `.ensure()`. For reading: `anim_utils.action_get_channelbag_for_slot(action, obj.animation_data.action_slot)`. Slotted actions arrived in 4.4.
- "Use Nodes" removed for render settings; `use_nodes` on scenes, worlds and materials deprecated; `scene.node_tree` removed (compositor now uses node groups). Search snippet from a LuxCore issue; not re-verified locally beyond the material case working.
- Collada import and export removed. FBX C++ importer is default (`wm.fbx_import`).
- Compositor renames: Composite node becomes Group Output, Z Combine becomes Depth Combine.
- Array modifier rebuilt with Geometry Nodes; five new modifiers.
- Grease Pencil annotations API breaking changes (GP v3 landed in 4.3).
- BGL was removed earlier (4.x, Vulkan work); confirmed absent locally. Use the `gpu` module.
- EEVEE Next (4.2) became plain `BLENDER_EEVEE` again; `BLENDER_EEVEE_NEXT` is invalid in 5.2 (verified).

5.1:
- Python 3.13 (VFX Platform 2026). Local 5.2.1 runs 3.13.13.
- User site-packages no longer loaded by default. Packages installed with `pip install --user` into Blender's Python are invisible unless `--python-use-system-env` or explicit `sys.path`.
- `ANIM_OT_convert_legacy_action` removed.
- Exact Boolean over 35 percent faster. Geometry Nodes UV Unwrap gains SLIM.

5.2:
- Geometry Nodes modifier inputs are RNA properties now (verified pattern above).
- `bpy.data.all_ids`, `Window.screenshot`, `gpu.init()` for background mode (verified `gpu.init()`).
- glTF: meshopt compression import/export, point clouds, iridescence and dispersion. STL export can pick viewport or render evaluation (`evaluation_mode`).
- Geometry Nodes: Mesh Bevel node, XPBD solver, Lists, string fields, bundles.

Headless use:
- `blender -b -X --python-exit-code 1 -P script.py -- --in a.glb --out b.glb` and parse args after `--` from `sys.argv`.
- `--python-expr` for one-liners. Quote carefully on Windows; prefer script files.
- `--factory-startup` gives a default scene with a Cube, Camera and Light. Delete them or start from `bpy.ops.wm.read_factory_settings(use_empty=True)`.
- Add `-noaudio` on servers without audio; `--offline-mode` to make sure nothing reaches the network.
- Rendering: `-E CYCLES -f 1` or `bpy.ops.render.render(write_still=True)`. GPU via preferences in script (`compute_device_type = "OPTIX"`, `get_devices()`, `device.use = True`, `scene.cycles.device = "GPU"`) or `-- --cycles-device OPTIX`.
- EEVEE in background works on Windows with a GPU (verified). On a headless Linux server EEVEE needs a GPU context (EGL); Cycles CPU always works. (memory, not re-verified for 5.2)
- `bpy` from PyPI: version 5.2.2, Python `==3.13.*` only, wheels for win_amd64, win_arm64, macosx_11_0_arm64, manylinux_2_28_x86_64. Same system requirements as Blender. Old versions are pulled from PyPI after their LTS window. Good for CI and for importing bpy inside a polywright Python process; heavier than calling the binary (about the size of Blender itself).

## 2. Agent bridges to Blender

Blender Lab official MCP server (blender.org/lab/mcp-server, fetched 2026-10-11; release history from StraySpark's 2026-09-25 comparison, a vendor with a competing product):
- Add-on `mcp-1.0.3.zip`, Blender 5.1+, GPL-3.0-or-later. Source at projects.blender.org/lab/blender_mcp (403 to fetch).
- Pre-release 0.1.0 on 2026-03-24, .mcpb bundle 2026-04-10, 1.0.0 on 2026-04-27, 1.0.2 on 2026-09-08 (pins MCP SDK below 2), 1.0.3 on 2026-09-11 (screenshot fix).
- Architecture: Blender add-on opens a local TCP socket (default 9876); a stdio MCP process relays. About 26 tools: code execution, scene and file summaries, screenshots, viewport navigation, renders, and search over bundled Blender API docs and manual. Six tools have `_for_cli` variants that run in a background Blender. (vendor summary)
- Official page warns it runs LLM code "without any guards in place" and suggests a VM.
- Anthropic announced creative-tool connectors including Blender on 2026-04-28 (vendor quote). Blender Foundation states no generative AI features are planned in Blender itself.

Community mcp-for-blender, formerly blender-mcp (github.com/ahujasid/blender-mcp now resolves to ahujasid/mcp-for-blender; README and server.py read 2026-10-11):
- MIT, 30,481 stars, last push 2026-10-06. PyPI `mcp-for-blender` 2.1.9 (2026-10-06); `blender-mcp` 2.0.0 (2026-09-16) is the compatibility wrapper. Rename on 2026-09-16 per StraySpark.
- Tools seen in `server.py`: `get_scene_info`, `execute_blender_code`, `look` (viewport, camera, wireframe, render captures), `search_assets` / `import_asset` across Poly Haven (CC0), Sketchfab and Poly Pizza, generation through Hyper3D Rodin, Hunyuan3D and Tripo (some behind a paid Premium tier), `open_viewport`, resources for objects, materials and collections, plus `bpy_api_lookup` and `describe_node_type` (added mid-September per StraySpark).
- Safety: socket has no auth or encryption; `execute_blender_code` runs anything; opt-in `BLENDER_MCP_SAFE_MODE=1` validator; anonymous telemetry on by default unless `DISABLE_TELEMETRY=true`.
- StraySpark reports four 2026 CVEs, including a path traversal in the Poly Haven downloader. Not verified against a CVE database.

Other servers (StraySpark comparison, unverified): Blender MCP Pro (Youichi Uda, 120+ tools, paid), StraySpark's own server (paid, code execution off by default, HTTP on 13580).

Known failure modes (StraySpark troubleshooting post, 2026-09-25):
- Port 9876 clash when both official and community add-ons run. On Windows, `WinError 10013` can be a Hyper-V/WSL reserved range (`netsh interface ipv4 show excludedportrange protocol=tcp`).
- First tool call hangs about 4 minutes then `-32001 Request timed out`: unframed JSON on the socket; update both sides.
- Every bpy call runs on Blender's main thread; long booleans or bakes freeze the UI and the bridge.
- Windows `spawn uvx ENOENT`: GUI clients do not inherit PATH; use the full path to `uvx`.
- Extensions must be installed from zip via Get Extensions, not unzipped into the add-ons folder.

Polywright stance:
- Default to headless scripts through the binary: reproducible, no open port, no live state, exit codes, works in CI.
- Offer MCP only when the user is watching Blender and wants live edits. Never run both MCP add-ons at once.
- Treat any MCP code execution as full user-level code execution. Never feed it text from downloaded assets.

Claude/Codex skills for Blender: not surveyed. The web-search budget ran out before this step. See "Open questions".

## 3. Blender techniques with the current API

Modifiers (data API, works headless):
```python
m = obj.modifiers.new("remesh", "REMESH"); m.mode = "VOXEL"; m.voxel_size = 0.005
m = obj.modifiers.new("dec", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = 0.25
m = obj.modifiers.new("weld", "WELD"); m.merge_threshold = 1e-4
m = obj.modifiers.new("solid", "SOLIDIFY"); m.thickness = 0.002
m = obj.modifiers.new("bool", "BOOLEAN"); m.operation = "DIFFERENCE"; m.solver = "MANIFOLD"; m.object = cutter
m = obj.modifiers.new("wrap", "SHRINKWRAP"); m.target = high; m.wrap_method = "PROJECT"
m = obj.modifiers.new("sub", "SUBSURF"); m.levels = 2; m.render_levels = 2
with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
    bpy.ops.object.modifier_apply(modifier=m.name)
```
- Or skip applying: read the evaluated mesh with `obj.evaluated_get(depsgraph).to_mesh()` and build a new mesh from it.
- Boolean solvers: `FLOAT` (fast, fragile), `EXACT` (default, robust, slow), `MANIFOLD` (fast, needs manifold inputs; uses the Manifold library). For print work, run MANIFOLD first and fall back to EXACT.
- Voxel remesh guarantees a closed mesh; good before printing scanned or AI-generated meshes. QuadriFlow (`object.quadriflow_remesh`) gives quads for game or sculpt topology but fails on non-manifold input.

Geometry Nodes from Python:
- Build with `bpy.data.node_groups.new(name, "GeometryNodeTree")`, sockets through `ng.interface.new_socket(...)`, nodes through `ng.nodes.new("GeometryNodeMeshCube")` etc.
- Set modifier inputs in 5.2 with `mod.properties.inputs.<identifier>.value` (verified). Older code using `mod["Socket_2"]` breaks.
- Node type ids change between versions. Look them up with `bpy.types` introspection or the MCP `describe_node_type` tool rather than memory.

UV:
- `bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)` in Edit Mode on selected faces. Works headless after `object.mode_set(mode="EDIT")`.
- `bpy.ops.uv.lightmap_pack()` for a second UV set for lightmaps.
- Outside Blender: xatlas (no 3.14 wheel) for packing.

Baking high to low (Cycles only):
- Select high, then low as active; low needs a UV map and an Image Texture node selected as the active node in its material.
- `bpy.ops.object.bake(type="NORMAL", use_selected_to_active=True, cage_extrusion=0.02, max_ray_distance=0.0, normal_space="TANGENT", margin=16)` then `image.save_render(path)` or `image.filepath_raw` + `image.save()`.
- Types available: COMBINED, AO, SHADOW, POSITION, NORMAL, UV, ROUGHNESS, EMIT, ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION (verified). For DIFFUSE set `pass_filter={"COLOR"}` to drop lighting.
- Roblox and most engines want OpenGL-style (Y+) normal maps; Blender bakes OpenGL style. Unreal wants DirectX (flip green).

Materials, Principled BSDF:
- Use the 5.2 socket names listed above. `mat.use_nodes = True` still works but is deprecated in 5.0; new materials have node trees by default in 5.x (memory).
- For glTF, keep to Base Color, Metallic, Roughness, Normal, Emission Color/Strength, Alpha; the exporter maps these to glTF PBR.

Reference images and camera matching:
- Images as planes is built in: `bpy.ops.image.import_as_mesh_planes(files=[{"name": f}], directory=d, shader="EMISSION")`. The old `import_image.to_plane` add-on operator is gone.
- Reference empties: `bpy.ops.object.empty_image_add(filepath=...)` or create an Empty with `empty_display_type = "IMAGE"` and assign `obj.data = img`.
- Camera matching: set `cam.data.lens` or `sensor_width` from EXIF, and orthographic views (`cam.data.type = "ORTHO"`, `ortho_scale`) for front/side/top references. fSpy importer is a third-party add-on (memory).

Turntables and review renders:
- Parent the camera to an Empty at the object's bounds centre; keyframe Z rotation 0 to 360; or loop in Python setting the camera location per angle and rendering stills.
- Frame the object by computing bounds from `obj.bound_box` and `matrix_world`; do not rely on `view3d.view_selected` (fails headless).
- Use Workbench with `shading.light = "MATCAP"` or `"STUDIO"` and cavity for shape review; it rendered in about 1 s.

3D Print Toolbox:
- Extension, v1.4.1 (2026-08-05), Blender 4.2+, maintained by Mikhail Rachinskiy, GPL-3.0+. Volume, area, bad-geometry checks and Make Manifold.
- Not installed on the owner's machine; its operators (e.g. `mesh.print3d_check_all`) are absent. Install: `blender --online-mode --command extension sync` then `--command extension install print3d_toolbox` (exact package id unverified). Needs the user's OK since it downloads.
- For agent checks, trimesh/manifold3d are simpler than driving the toolbox.

Extensions platform:
- `blender --command extension {list,sync,install,install-file,remove,repo-add,...}` (verified listing).
- `bpy.app.online_access` is False by default; installs need `--online-mode` or the preference.

## 4. Other tools agents can script

Python mesh libraries:
- trimesh (MIT): load/save STL, OBJ, PLY, GLB, 3MF (via lxml, memory), `is_watertight`, `is_winding_consistent`, `split`, `section`, `convex_hull`, ray tests, `scene.save_image` (needs pyglet; flaky headless). Pure Python plus numpy.
- manifold3d (Apache-2.0): robust booleans and `status()` manifold check; same library as Blender's MANIFOLD solver and OpenSCAD's default backend.
- Open3D (MIT): point clouds, Poisson reconstruction, ICP alignment, offscreen rendering (needs EGL on Linux).
- PyMeshLab (GPL-3): MeshLab's filters (repair, close holes, isotropic remesh, quadric decimation with texture) from Python.
- PyVista (MIT): VTK wrapper; offscreen screenshots good for contact sheets.
- libigl (Python): geometry processing; no Python 3.13/3.14 wheels.
- xatlas: UV atlas generation; no 3.14 wheel.
- fast-simplification (MIT): fast quadric decimation, installed locally.
- pygltflib: read/write glTF JSON; good for inspecting extensions and node trees.
- meshoptimizer Python package is a stale alpha (0.2.30a0); use the gltfpack binary instead.

glTF tools (Node, installed globally with npm):
- `gltf-transform` 4.5.1: `inspect`, `validate`, `optimize`, `simplify`, `draco`, `meshopt`, `etc1s`/`uastc` (KTX2, needs KTX-Software `toktx` on PATH, memory), `resize`, `weld`, `dedup`, `prune`.
- `gltfpack` 1.3.0: `-si 0.5` simplify, `-cc` meshopt compression, `-tc` KTX2 textures, LOD chains by running at several ratios.
- `gltf_validator` (Khronos): `-o` JSON report to stdout, non-zero exit when errors are found. npm package is `gltf-validator` 2.0.0-dev.3.10 (2024-10-22, still current).

USD:
- `usd-core` 26.8 (PyPI) gives `pxr` plus `usdcat`, `usdchecker` (memory: `usdchecker --arkit` validates USDZ for AR Quick Look).
- Blender `wm.usd_export` writes `.usdz` directly with preview surfaces and texture downscaling.
- Apple's Reality Converter / `usdzconvert` are macOS only (memory).

Code-CAD:
- build123d 0.13.0 and CadQuery 2.8.0 (OCCT kernel via OCP): exact B-rep, export STEP, STL, 3MF (build123d has a Mesher class, memory). Best for mechanical print parts and anything that needs STEP.
- OpenSCAD: last stable 2021.01; nightly snapshots are the real product. Manifold is the default 3D backend in master (`--backend` help text: "'CGAL' (old/slow) or 'Manifold' (new/fast) [default]"; source read 2026-10-11). Exports STL, OFF, 3MF and PNG from the CLI (`openscad -o out.3mf in.scad`). Windows snapshot needs Windows 11 x64.
- FreeCAD 1.1.4 headless via `freecadcmd script.py`; heavy, but reads and writes STEP, IGES and meshes.
- Zoo (KittyCAD) CLI v0.2.203 (2026-10-07): text-to-CAD and KCL through a cloud API; needs an account and a key (the user must set it up).

Mesh repair:
- MeshLab 2025.07 GUI; script through PyMeshLab.
- Meshmixer is discontinued by Autodesk (memory); do not depend on it.
- admesh 0.98.5: STL check and repair CLI, stale since 2022, packaged on Linux and brew.
- Bambu Studio CLI (wiki, fetched 2026-10-11): `--orient`, `--arrange 1`, `--scale f`, `--slice 0`, `--export-3mf file`, `--load-settings "machine.json;process.json"`, `--load-filaments`, `--info`, `--outputdir`, `--debug 0-5`. No explicit repair flag on the wiki page. On Windows `bambu-studio.exe --help` printed nothing to the console in this session (GUI subsystem); redirect or check exit codes and output files instead.
- PrusaSlicer CLI 2.9.6 has `--repair` and `--export-3mf` (memory, flags unverified for 2.9).

Retopology:
- QuadriFlow inside Blender (verified operator).
- Voxel remesh then Decimate for print or background props.
- Instant Meshes: no releases, last push 2022; old binaries still work (memory).
- Quad Remesher (Exoside) is paid, runs as a Blender add-on; price not checked.

Photogrammetry and splats:
- COLMAP 4.2.1 (2026-09-29) and `pycolmap` 4.2.1 with Windows wheels; CUDA builds for dense stereo on Windows/Linux.
- OpenMVS 2.4.0 for dense mesh and texture after COLMAP.
- Meshroom 2025.1.0 (needs CUDA; no official macOS build).
- OpenDroneMap 3.6.2 via Docker for aerial sets.
- Gaussian splats: `@playcanvas/splat-transform` 3.10.1 (convert, filter, compress PLY/SPZ/SOG), `gsplat` 1.5.3 (CUDA training). Splats do not give printable meshes; mesh extraction is a separate step.

DCC apps:
- Houdini: `hython` is the scripting entry. Apprentice is free but non-commercial with limits; Indie is paid. Whether Apprentice allows `hython` batch was not verified.
- Maya `mayapy` and 3ds Max `pymxs`: commercial; only worth supporting if the user has a licence.

Engines:
- Unity: glTF via `com.unity.cloud.gltfast` package, FBX native (memory). One unit = 1 m; Blender FBX export needs Apply Scalings "FBX All" and forward -Z, up Y conventions (memory). The unity-agent skills in this workspace cover the import side.
- Unreal: Interchange imports glTF and FBX natively (memory). Unreal is Z-up, centimetres.
- Roblox (create.roblox.com, fetched 2026-10-11): 20,000 triangles per mesh; at most 4 bone influences per vertex; root bone at origin with identity transforms; one animation track per export; one material per mesh; one UV set inside 0..1; textures up to 4096x4096 uploaded separately (page also says 1024x1024 for UV texture space, so the page is inconsistent); normal maps must be OpenGL style; SurfaceAppearance maps: albedo, normal, roughness, metalness, emissive mask. The roblox-agent skills cover upload.
- three.js 0.186.1 and model-viewer 4.4.0 load GLB with Draco, meshopt and KTX2 decoders.

Default chains per target:

| Target | Chain | Checks |
|---|---|---|
| Game asset (generic) | Blender model -> apply transforms, triangulate -> UV -> bake -> `export_scene.gltf` GLB -> `gltfpack` or `gltf-transform simplify` at 1.0/0.5/0.25 for LODs | gltf_validator exit 0, tri count per LOD, texture sizes power of two |
| Unity | GLB via glTFast or FBX (`export_scene.fbx`, scale 1, Apply Scalings FBX All) | import test through unity-agent-headless |
| Roblox | FBX or glTF, under 20k tris per mesh, 1 material, OpenGL normals, textures uploaded separately | tri count, bone influences 4 or fewer |
| Unreal | FBX or GLB, units in cm handled by importer | scale check on import |
| Print (Bambu P1S) | Blender or build123d/OpenSCAD -> voxel remesh or Manifold boolean if needed -> `wm.stl_export` or 3MF via trimesh/OpenSCAD -> Bambu Studio CLI orient, arrange, slice, export 3MF | manifold status OK, 1 body (or intended count), extents in mm fit 256 x 256 x 256, wall thickness |
| Web | GLB -> `gltf-transform optimize --compress meshopt --texture-compress ktx2` (or Draco) | validator, file size budget, renders in model-viewer |
| AR (iOS) | Blender `wm.usd_export` to .usdz with preview surface and downscaled textures | `usdchecker --arkit` |
| AR (Android) | GLB as for web | validator |
| AI video | Blender blockout -> Workbench/EEVEE renders plus depth (Z or Mist), normal and object-index passes from view layer passes -> ComfyUI conditioning | pass images non-empty, normalised depth range |
| Business/CAD | build123d/CadQuery or FreeCAD -> STEP plus STL/GLB preview | STEP reopens, volume matches |

Bambu P1S build volume 256 x 256 x 256 mm is from memory; verify against Bambu's spec page when writing the print skill.

## 5. Verification without eyes

Numeric checks (cheap, run first):
- Manifold: `manifold3d.Manifold(Mesh(...)).status() == Error.NoError`; trimesh `is_watertight` and `is_winding_consistent`; body count via `split`.
- Self-intersections: PyMeshLab has a self-intersecting faces filter (memory, exact filter name unverified); manifold3d booleans treat them robustly; Blender 3D Print Toolbox "Intersections" check.
- Scale: extents in metres for Blender/glTF, millimetres for STL/3MF. Blender STL export uses `global_scale` and `use_scene_unit`; agents often export a 2 m object as 2 mm. Always print extents after export and compare with the brief.
- Budgets: triangle count per mesh and per LOD, material count, texture resolution, file size. `gltf-transform inspect` prints these.
- glTF: `gltf_validator -o file.glb` gives a JSON report; non-zero exit on errors.
- USDZ: `usdchecker --arkit`.
- Print: slice with the Bambu CLI and read the result (failure means unprintable); `--info` gives model info.

Visual checks (a vision model as the eyes):
- Render a contact sheet: 6 orthographic views (front, back, left, right, top, bottom) plus 2 three-quarter perspective views, Workbench matcap, neutral background, object framed from its bounds. Tile into one image with labels.
- Add a wireframe or face-orientation pass when topology matters (Workbench can show backfaces in red with a custom approach; memory).
- Ask the vision model specific questions (is the handle on the right side, are there holes, is it symmetric), not "does it look good".
- Silhouette comparison: render a binary alpha mask from the reference camera and compute IoU against a mask from the reference image. Needs the camera matched first.
- The community MCP exposes a `look` tool for the same idea in a live session; the official server has screenshot and render tools.

## 6. What practitioners say

Gathered so far (thin; search budget ran out):
- BlenderArtists, 2026-03-21: a user's 4.5 script broke on `action.fcurves`; answer points to 5.0 notes and the channelbag pattern. Shows how common the slotted-actions break is. The asker blamed 5.1, a typical off-by-one that an agent would also make.
- Blender Artists Pie Menu Editor thread and the LuxCore issue: add-on authors spent weeks on 5.0 property access changes.
- StraySpark troubleshooting post, 2026-09-25: MCP timeouts, port clashes, PATH problems on Windows, main-thread blocking. Issue #339 timeout report on Blender 5.2.1 was open in late September.
- The official Blender Lab page itself says results "depend on the LLM used" and warns about unguarded code execution.

Common LLM failure modes when scripting Blender (from the above plus this session's own probes):
- Hallucinated or outdated API: `bgl`, `BLENDER_EEVEE_NEXT`, `import_scene.obj`, `export_mesh.stl`, old Principled socket names, `action.fcurves`, `modifier["Socket_n"]`, guessed enum ids like `SMOOTH_CORRECTIVE`.
- Context errors: `bpy.ops` calls whose poll needs a 3D view region or a specific active object. Fix: data API, or `with bpy.context.temp_override(...)`, and set `view_layer.objects.active`.
- Silent failure: exceptions exit 0 without `--python-exit-code`; operators return `{'CANCELLED'}` with only a warning (seen: `object.join` printed "No mesh data to join").
- Default scene pollution: `--factory-startup` adds a cube, camera and light that end up in exports (the probe's GLB and STL contained the cube).
- Axis and units: Blender is Z-up metres; glTF is Y-up metres (exporter converts with `export_yup`); STL has no units; Unreal is Z-up cm; Unity is Y-up m with FBX scale quirks.
- Mode: forgetting to return to Object Mode before export or modifier apply.
- User site-packages not loaded since 5.1, so `pip install --user` packages vanish inside Blender.

Mitigations for polywright:
- Ship a tiny preflight script that prints Blender version, Python version, available operators and enum items, and have agents call it rather than recall APIs.
- Wrap every Blender call in a runner that adds `-b -X --python-exit-code 1`, captures stdout, and parses a final JSON line.
- Start scripts with `bpy.ops.wm.read_factory_settings(use_empty=True)`.
- Keep a tested snippet library per Blender minor version and regenerate it when Blender updates.

## Sources (all accessed 2026-10-11)

- Blender 5.2 release page: https://www.blender.org/download/releases/5-2/
- Blender 5.1 release page: https://www.blender.org/download/releases/5-1/
- Blender 5.0 release page: https://www.blender.org/download/releases/5-0/
- Blender 5.x Python API notes (snippets only, page behind Cloudflare): https://developer.blender.org/docs/release_notes/5.2/python_api/ and /5.1/ and /5.0/
- bpy on PyPI: https://pypi.org/project/bpy/
- Blender Lab MCP server: https://www.blender.org/lab/mcp-server/
- mcp-for-blender: https://github.com/ahujasid/mcp-for-blender
- StraySpark comparison (vendor, 2026-09-25): https://www.strayspark.studio/blog/official-blender-mcp-server-comparison-2026
- StraySpark troubleshooting (vendor, 2026-09-25): https://www.strayspark.studio/blog/blender-mcp-not-working-fix-connection-2026
- BlenderArtists fcurves thread (2026-03-21): https://blenderartists.org/t/what-was-bpy-types-action-fcurves-replaced-with-in-blender-5-0/1634809
- Cinevva Blender 5 for game artists (2026-09-06): https://app.cinevva.com/guides/blender-5-for-game-artists
- 3D Print Toolbox extension: https://extensions.blender.org/add-ons/print3d-toolbox/
- Roblox mesh specifications: https://create.roblox.com/docs/art/modeling/specifications
- Roblox texture specifications: https://create.roblox.com/docs/art/modeling/texture-specifications
- Bambu Studio CLI: https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage
- OpenSCAD downloads: https://openscad.org/downloads.html and source `src/openscad.cc` on master (pushed 2026-10-08)
- glTF-Validator: https://github.com/KhronosGroup/glTF-Validator
- Registries: pypi.org JSON API, registry.npmjs.org, GitHub releases API for the repos in the table.

## Open questions / unverified

- Full 5.0, 5.1 and 5.2 Python API breaking-change lists: developer.blender.org was behind a Cloudflare challenge. Read them in a browser by hand, or retry later, before writing polywright's API cheat sheet.
- Whether `scene.node_tree` is fully removed in 5.2 and what compositor scripts must use instead (local probe not run).
- Exact extension id for the 3D Print Toolbox for `--command extension install`, and whether install works headless with `--online-mode`. Needs the user's OK to download.
- Blender Lab MCP tool list and release dates come from a competing vendor's blog; the projects.blender.org repo returned 403.
- The four CVEs against mcp-for-blender (including the named CVE-2026-66004) are unverified.
- Intel Mac support ending with Blender 4.5 is from memory; the arm64-only bpy wheel supports it.
- Blender 5.3 date (2026-11-10) and Vulkan default are from a secondary source.
- Claude/Codex skills and plugins for Blender on GitHub, skills.sh and plugin directories: not surveyed (search budget exhausted). Also not surveyed: Hacker News threads, r/blender and r/blenderhelp (Reddit RSS), Polycount, Blender Stack Exchange.
- Houdini Apprentice hython limits and Indie price; Quad Remesher price; Meshmixer status; PrusaSlicer 2.9 `--repair` flag; PyMeshLab self-intersection filter name; KTX2 needing `toktx` for gltf-transform; trimesh 3MF dependencies; Unity glTFast package name and current version; Bambu P1S build volume. All from memory.
- Bambu Studio CLI on Windows printed nothing for `--help` from Git Bash; test a real slice to learn its exit codes and output files.
- EEVEE in background on headless Linux and macOS for 5.2 not tested here.
- `pip install bpy` was not tried (no Python 3.13 installed and installs were out of scope).
