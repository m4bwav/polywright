# Web and three.js: making and finishing models for a page

Back to [../SKILL.md](../SKILL.md). Axes, units and the cross-engine budget table: [engines.md](engines.md).
The check target is `web-threejs` in [../../polywright/references/targets.json](../../polywright/references/targets.json).
This page is the artist's side: how to build, texture, bake and compress a GLB. The runtime side (loaders,
decoders, materials, page checks, the developer's view of the same model) belongs to the [threewright](https://github.com/m4bwav/threewright) plugin (its knowledge base topic
`models-for-the-web`). Source: research of 2026-10-17 ([../RESEARCH.md](../RESEARCH.md) R-20261017-1). Unmarked lines are long-standing practice.

## What the web punishes

A page downloads the whole model before it shows anything, often over a phone connection, and draws it in a
browser tab with a fraction of a game console's memory. Three things decide whether a model works there:
download size, draw calls (one per mesh and material pair) and GPU memory for textures. Triangle count matters
less than all three. Model for those first.

## Modelling and topology

- Spend triangles on the silhouette. Flat faces need two triangles; curvature that only catches light can come
  from a baked normal map.
- GPUs count vertices, not polygons. A UV seam or a hard edge splits every vertex on it, so a low-poly model
  with all edges hard costs up to three vertices per triangle. Place seams and sharp edges where the shape needs
  them, not everywhere.
- One material per prop where possible, and one shared material across a kit. Ten materials on a chair is ten
  draw calls. Merge parts that never move separately; keep apart (and named) the parts code will pick, hide or
  animate: lids, doors, buttons, wheels.
- Repeated objects (bolts, trees, chairs) stay as one mesh referenced by many nodes, so the exporter and
  `gltf-transform instance` can turn them into GPU instances. Applying the instances into one mesh throws that away.
- Generated meshes (TRELLIS, Hunyuan3D, hosted generators) arrive dense and lumpy with one big texture: decimate
  to budget, then re-bake, before any web compression.
- LODs only for big scenes and repeated props: `pw.py lods` at about half the triangles per level, children named
  `<name>_LOD0`, `_LOD1`. The page builds its own LOD object from them; glTF has no LOD that three.js reads.
- When to switch: by projected size, not a round distance. A level takes over where the detail it removes would
  cover under about 2 pixels, since anything finer only aliases (CGPP 3e §25.4). Geometry a level drops goes into
  the normal map; on the farthest levels soften that normal map and raise roughness, or fine bumps sparkle. The
  distance formula and three.js's hysteresis setting are in threewright's `performance` topic.

## UVs, texel density and texture sets

- Keep texel density consistent across a kit; check with a checker texture in a render.
- Atlases and trim sheets let a whole set of props share one material and one draw call. Trim sheets suit
  architecture and hard-surface kits; atlases suit small props packed together.
- A second, non-overlapping UV set (Blender's second UV map, exported as `TEXCOORD_1`) carries a baked lightmap
  or AO for a static scene. Leave margins of at least 4 to 8 px at the bake size to stop bleeding at mip levels.
- Sizes in powers of two: 512, 1024, 2048. KTX2 requires multiples of 4. Paint and bake at the delivery size or
  double it, never at 4096 by habit: a 4096 px RGBA texture is about 64 MB of GPU memory however small its file.

## Materials and texture packing

- Principled BSDF only, metal-rough: metalness 0 or 1, roughness carries the surface. The Blender glTF exporter
  packs roughness and metalness into the G and B channels of one image.
- Ambient occlusion exports only through a custom node group named `glTF Material Output` with an `Occlusion`
  input (Add > Output > glTF Material Output). glTF reads AO from red, so the full ORM texture (occlusion R,
  roughness G, metalness B) can be one image shared by both inputs.
- Normal maps tangent-space, OpenGL (+Y up). Invert green on any DirectX map from Unreal-oriented tools.
- Vertex colours: Blender exports them only when the material uses them as a Base Color multiplier (the `Use
  Vertex Color` default, `Material`). For a flat-colour low-poly model, wire a Color Attribute node into Base
  Color, or set the option to `Active`.
- Unlit (`KHR_materials_unlit`) only for art whose light is fully baked into the colour (dioramas, stylized
  scenes); it ignores every light on the page.

## Baking

- High to low: normal, AO and colour from the dense mesh onto the web mesh (recipe `bake-high-to-low` in
  polywright-blender). Re-bake after every retopology or decimation that changes UVs.
- Lightmaps for static scenes and isometric dioramas: bake Cycles diffuse lighting (or full combined light for
  unlit art) onto the second UV set at 1024 to 2048 px. Baked light does not move: keep whatever moves out of it.
- Stylized and toon models: bake little or nothing. Flat base colours, clean silhouettes and a few hard normals
  do more than texture detail; the page adds outlines and toon ramps.

## Export from Blender

`pw.py convert in.blend out.glb` or File > Export > glTF 2.0 with: GLB, `+Y Up` on (the glTF convention),
`Apply Modifiers` on, transforms applied first (Ctrl+A: scale and rotation, so the root is not scaled 0.01 or
rotated -90 on X), origin at the bottom centre (props) or the hinge or axle (moving parts), real size in metres.
Leave the exporter's own Draco option off; compress afterwards so one tool decides.

## Compress

Pick one tool. Both write meshopt geometry and KTX2 textures (KTX-Software's `ktx` must be on PATH for KTX2;
the gltfpack npm build cannot write textures, the native binary can).

```sh
# gltf-transform (4.5.1). optimize joins named meshes and flattens the scene by default:
# keep --join-named false when code needs part names.
npx @gltf-transform/cli@4.5.1 optimize in.glb out.glb --compress meshopt \
  --texture-compress ktx2 --texture-size 2048 --join-named false
# finer control: ETC1S for colour, UASTC for normals and ORM
npx @gltf-transform/cli@4.5.1 etc1s out.glb out.glb --slots "{baseColorTexture,emissiveTexture}"
npx @gltf-transform/cli@4.5.1 uastc out.glb out.glb --slots "{normalTexture,occlusionTexture,metallicRoughnessTexture}"

# gltfpack (1.3.0, native binary): meshopt, KTX2 per class, keep named nodes, cap textures
gltfpack -i in.glb -o out.glb -cc -tc -tu normal,attrib -tl 2048 -kn
```

- ETC1S suits broad flat colour (and toon art); UASTC keeps normal maps and packed ORM data clean (Khronos KTX
  Artist Guide). WebP is a smaller download but full size in GPU memory: use it only when KTX2 tools are missing.
- Draco gives the smallest static geometry but compresses meshes only and decodes slower; meshopt also
  compresses animation and morph targets. Default to meshopt.
- Quantization defaults (gltfpack: 14-bit positions, 12-bit UVs, 8-bit normals) are fine for props; raise `-vp`
  for very large scenes or engineering models where millimetres matter across many metres.

## Check and verify

1. `pw.py check out.glb --target web-threejs --real-size-m X`: triangles, image sizes, file size, UVs.
2. `npx @gltf-transform/cli@4.5.1 validate out.glb` (or the Khronos glTF Validator): no errors. KTX2 shows as an
   unsupported-extension info; that is expected.
3. `npx @gltf-transform/cli@4.5.1 inspect out.glb`: material count, texture sizes and their GPU memory.
4. Look at it in a web viewer, not only in Blender: a three.js page (threewright's `tw glb` and `tw check`
   report size, draw calls, decoders and bounds in metres), or model-viewer. Check scale against a 1 m cube,
   the front facing +Z, normal maps not inverted, colours not washed out (sRGB colour, linear data maps).
5. `pw.py manifest <dir> --add-output out/out.glb --target web-threejs --inspect`.

## Styles at a glance

| Style | Make it with |
|---|---|
| Low-poly, flat-shaded | few hundred to few thousand triangles, hard edges, vertex colours or one palette texture, one material |
| Toon or cel | clean silhouette, flat base colours, no baked AO in colour; outlines are the page's job |
| Stylized PBR | hand-painted or trim-sheet colour, simple roughness, atlases shared across the kit |
| Product realism | real size, clean UVs, 2048 px ORM and normal, clearcoat or transmission only where real |
| Isometric diorama | one small scene, one atlas, baked lightmap on UV2, often unlit |
