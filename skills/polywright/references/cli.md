# pw.py command reference

`scripts/pw.py` (Python 3.9+, standard library only) prints one JSON object per command and exits 0 on success,
1 on a failed check or error, 2 on a usage error. `scripts/pw_bpy.py` is the Blender half: pw.py runs it as
`blender --background --factory-startup --python-exit-code 3 --python pw_bpy.py -- <action> <params> <result>`
(without `--python-exit-code` a Python error inside Blender still exits 0).

Back to [SKILL.md](../SKILL.md). Checked against Blender 5.2.1 LTS on Windows 11, 2026-10-11.

## Finding tools

| Variable | Use |
|---|---|
| `POLYWRIGHT_BLENDER` | path to `blender` / `blender.exe`; otherwise PATH, then install folders (Program Files on any drive, Steam, `/Applications/Blender*.app`, `/snap/bin`, `/opt/blender*`), newest first |
| `POLYWRIGHT_BPY_PYTHON` | a Python that can `import bpy` (the PyPI `bpy` wheel needs exactly the Python Blender bundles: 3.13 for 5.2) |
| `POLYWRIGHT_COMFYUI` | comma-separated ComfyUI URLs for `gen`; default `http://127.0.0.1:8188` |

## Commands

| Command | Needs | What it does |
|---|---|---|
| `doctor [--host URL]` | nothing | Blender path and version, Python mesh modules, CLIs (gltf-transform, gltfpack, colmap, openscad, slicers, ffmpeg), ComfyUI hosts and their 3D checkpoints, and `can`: which commands will work |
| `inspect FILE [--fast]` | Blender, else trimesh, else stdlib (GLB, binary STL) | triangles, objects, size, materials, images, UV-less objects, unapplied scale, armatures; boundary and non-manifold edges, parts, volume on welded positions (glTF/STL split vertices per face) |
| `render FILE --out DIR [--views front,right,back,left,top,iso] [--color clay\|material\|texture] [--engine workbench\|eevee\|cycles] [--size 640]` | Blender | one PNG per view plus `sheet.png`; orthographic views report metres per pixel (compare with blueprints) |
| `match FILE --out X.png --anchor-px X,Y --aim-px X,Y --aim-local=X,Y,Z [--anchor-local=X,Y,Z] [--still PIC] [--depth M] [--lens 35] [--horizon ROW] [--roll DEG] [--sun-dir X,Y,Z] [--hide BOX]... [--mask-add BOX]... [--grow 10] [--gpu]` | Blender (Pillow for `--still`) | the model rendered RGBA from a picture's camera: the anchor point (a grip) lands on one pixel at `--depth`, the aim point (a tip) exactly on another; with `--still`, also `<out>_paste.png` and a blend mask `<out>_mask.png`. Model forward +X, up +Z. Write negative coordinates as `--aim-local=-0.8,0,0` |
| `convert IN OUT [--size-m X] [--scale F] [--ground] [--center] [--join] [--apply] [--max-tris N \| --ratio R] [--uv] [--draco] [--export-scale F] [--fbx-bake-axes]` | Blender | any of glb/gltf/obj/fbx/stl/ply/usd(a/c/z)/abc/blend in and out; scale, decimate, Smart UV, compress |
| `lods IN --out DIR [--ratios 1,0.5,0.25,0.1]` | Blender | `<name>_LOD0..n` files by decimation |
| `printable IN OUT.stl --size-mm N [--size-axis longest\|height\|width\|depth] [--wall-mm 1] [--voxel-mm V] [--base-cut-mm 0.6] [--drop a,b] [--up y]` | Blender | any mesh to one watertight solid: drop parts, scale, thicken open shells inward, voxel remesh, keep the largest part, flat base, decimate, clean |
| `union IN OUT [--solver manifold\|exact] [--voxel-fallback MM]` | Blender 4.5+ | boolean-union the closed shells of a file; falls back to EXACT when Manifold silently drops operands |
| `check FILE --target T [--real-size-m X]` / `check --list` | as inspect | rules from [targets.json](targets.json): triangles, materials, texture size, UVs, watertight, parts, bed size, unit sanity |
| `new DIR --name N --kind K --route R --targets a,b` | nothing | the asset folder and `manifest.json` ([contract.md](contract.md)) |
| `manifest DIR [--add-source URL --licence L --author A --what W] [--add-output PATH --target T --inspect] [--add-tool N --tool-version V] [--status S] [--validate]` | nothing | record provenance and outputs; validate licences, files on disk and hashes |
| `bpy SCRIPT [--blend FILE] [--timeout S] [-- args]` | Blender | runs your bpy script headless; returns condensed output and the traceback, not 300 lines of Blender log. pw.py's options may come before or after SCRIPT; everything after `--` goes to the script |
| `gen --image FRONT [--left --back --right] --out X.glb [--turbo] [--seed N] [--octree 256]` | ComfyUI with Hunyuan3D-2 checkpoints | built-in Hunyuan3D-2 single or multi-view graph; background removal (rembg if installed), padding; writes `X.gen.json` with host, model, seed, licence note |
| `gen --image IMG --workflow W.json --out X.glb [--set NODE.input=VALUE] [--save-api G.json]` | ComfyUI with the workflow's nodes | any workflow, API format or as saved by the editor (a template file works as is: converted with the host's node definitions); picks a host that has every node; a rejected graph prints ComfyUI's node_errors |
| `place --bbox S,W,N,E \| --center LAT,LON --size-m M --out DIR [--dem auto\|usgs\|terrarium\|flat] [--res M] [--print-mm N --exaggerate 1.5 --base-mm 3 --print-roads]` | network (Overpass, elevation) | `scene.glb` (terrain coloured by land use, buildings with OSM heights, roads, paths, waterways, trees), `place.json` with counts and credits, and a print tile |
| `texture IMG --out DIR [--seamless] [--convention opengl\|directx]` | numpy, Pillow | quick height, normal and roughness maps from a photo; a seamless albedo |

## Reading results

- `ok: false` always carries `error`; Blender failures add `log` or `traceback` (condensed).
- `inspect` sizes are Blender units: metres unless the source used other units. An STL in millimetres reads
  1000 times too big; `check --real-size-m` flags it.
- `render` returns `sheet.path`; read that one image.
- `check` returns `status` pass, warn or fail and one row per rule; `unchecked` rows (minimum feature size)
  need a look at the render or a wall-thickness tool.
