# Engines and targets: axes, units, budgets, quirks

Back to [SKILL.md](../SKILL.md). Source: polywright research note `2026-10-11-craft-and-academics.md`
sections 2, 3 and 5. [verified] = an official page read 2026-10-11; [secondary] = a vendor or forum source;
unmarked = long-standing practice.

## Axes and units

| Tool or engine | Up | Handedness | Forward | Unit |
|---|---|---|---|---|
| Blender | +Z | right | front view looks along +Y, so models face -Y | 1 m |
| glTF 2.0 | +Y | right | the asset's front faces +Z [verified, spec 3.4] | 1 m [verified] |
| three.js | +Y | right | camera looks down -Z; glTF models face +Z | metres by convention |
| Unity | +Y | left | +Z | 1 m |
| Unreal | +Z | left | +X | 1 cm |
| Roblox | +Y | right | CFrame.LookVector is -Z | 1 stud = 0.28 m [verified] |
| Godot | +Y | right | nodes look -Z; imported assets face +Z | 1 m |

## Budgets (October 2026, approximate)

| Target | Budget | Source |
|---|---|---|
| Roblox MeshPart | at most 20,000 triangles | Roblox specifications [verified]; vendors say 21,000: test the importer |
| Roblox rigid or layered accessory (UGC) | at most 4,000 triangles | Roblox avatar specifications [verified 2026-10-17] |
| Mobile hero character | 5k to 30k | [secondary] |
| PC or console hero (no Nanite) | 50k to 150k | [secondary] |
| Unreal Nanite static or skeletal | effectively unbounded; measure per scene | Epic docs, UE 5.8 [verified] |
| Quest 3 whole frame | 1.3 to 1.8 million triangles | Meta docs [secondary] |
| VRChat Quest avatar | under 10,000 | VRChat docs [secondary] |
| AR Quick Look | about 100k polygons, one set of 2048 px textures | Apple [secondary] |
| Web or e-commerce GLB | about 100k triangles, under 5 MB (v1.0 figures; the current text has none) | Khronos 3DC [secondary] |

`pw.py check` uses these through `../../polywright/references/targets.json`.

## Engines

**Roblox.** FBX, OBJ or glTF through the 3D Importer. At most 20,000 triangles per mesh, at most 4 bone
influences per vertex, root joint at the origin, bones frozen (scale 1, rotation 0), one animation track per
export, no zero-thickness meshes [verified]. SurfaceAppearance: colour, normal (OpenGL only [verified]),
roughness, metalness, emissive mask. Many MeshParts sharing a MeshId reuse geometry. CollisionFidelity Box or Hull
for props. A 1.8 m person is about 6.4 studs. The full route (styles, UVs, scale, rigs, cages): [roblox.md](roblox.md).

**Unity.** GLB through glTFast or Unity's glTF importer, or FBX with scale 1 and the axis change baked
(`pw.py convert --fbx-bake-axes`) so the root is not rotated -90 on X. OpenGL normals. URP and HDRP mask maps
pack channels differently from glTF ORM. LOD meshes named `<name>_LOD0..n` as siblings in one FBX become an LOD
group; it switches on screen-relative height, so set each level where its removed detail drops under about 2 px. The full route (formats, FBX settings, lightmap UVs, collision, Humanoid): [unity.md](unity.md).

**Unreal.** FBX, GLB or USD; Z-up centimetres (the importer converts). Nanite takes dense opaque and masked
static and skeletal meshes, foliage and tessellation; not translucent materials or morph targets; clamp WPO
[verified]. Collision pieces prefixed UCX_. DirectX normals (or Flip Green Channel). Turn off Generate Lightmap
UVs when lighting is fully dynamic.

**Godot.** glTF first-class; +Y up; imported assets face +Z.

**three.js and the web.** GLB with meshopt or Draco geometry and KTX2 (Basis) textures; real size; origin at the
bottom centre. The threewright plugin checks the page and the model in a browser. The full route (topology,
texture packing, baking, compression): [web-threejs.md](web-threejs.md).

**AR.** iOS: USDZ (Blender `wm.usd_export`, preview surface, downscaled textures; `usdchecker --arkit`).
Android: GLB as for the web.

**AI video.** Real scale and camera agree with the shot; blockouts plus depth, normal and mist passes; a 3D
turnaround of a character keeps it consistent across shots (cinewright).

**E-commerce (Khronos 3D Commerce).** Real size, 1 unit = 1 m, origin at the bottom centre (top centre for
ceiling items), triangles only, metalness 0 or 1, KTX2 for delivery [verified].
