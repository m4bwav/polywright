# Unity: making and finishing models for a Unity project

Back to [../SKILL.md](../SKILL.md). Axes, budgets and the short Unity note are in [engines.md](engines.md); this
page is the 3D artist's side of the `game-unity` target: what to build, how to export it from Blender, and how
to prove it imports. The editor side (import settings, AssetPostprocessors, batching, verifying in a project) is
[unity-agent](https://github.com/m4bwav/unity-agent)'s (`skills/unity-agent-workflow/references/3d-models.md`).
Sources: [../RESEARCH.md](../RESEARCH.md) R-20261017-3 (Unity 6.6 manual, glTFast 6.14.1, HDRP 17, read 2026-10-17). [verified] = read
in that pass; unmarked = long-standing practice.

## Pick the format

| Asset | Export | Why |
|---|---|---|
| Static prop from a generator or for the web too | GLB | the project needs the glTFast package (`com.unity.cloud.gltfast`), default importer for .glb [verified] |
| Rigged, animated, lightmapped or LOD-grouped | FBX | Unity's own import chain; LOD Group naming and the Rig tab are FBX features [verified] |
| Anything | never `.blend` in `Assets/` | it imports only where Blender is installed on every machine [verified] |

glTFast's editor import uses its own shaders, not URP or HDRP Lit, and its shaders read two UV sets [verified]:
for a prop that must use the project's Lit materials or a lightmap UV, send FBX.

## Before export (in Blender)

1. Real size in metres (Blender's default unit scale 1.0); a 1.8 m person is 1.8 units. `pw.py convert --size-m`.
2. Apply rotation and scale on every mesh (`--apply`): unapplied scale is a `game-unity` fail.
3. Pivot (origin) where Unity will rotate or place it: bottom centre for props, hinge for doors, grid corner
   for kit pieces. Kit pieces sit on a 1, 2 or 4 m grid so they snap with Unity's increment snapping.
4. Front faces -Y in Blender, so it faces +Z (Unity's forward) after export.
5. Triangulate only if the shading depends on the split; Unity triangulates the rest on import [verified].
6. Name objects for the importer: `Name_LOD0`, `Name_LOD1`, ... as siblings in one file (LOD Group) [verified];
   collision proxies as `Name_Collider` (or `UCX_Name` when the same file also goes to Unreal); sockets as empties
   `SOCKET_Name`. unity-agent's postprocessor matches on these names.

## FBX export settings for Unity

| Blender FBX option | Value |
|---|---|
| Apply Scalings | FBX Units Scale, what `pw.py convert` writes (FBX All also works by hand); the 1 m cube test below decides: Scale Factor 1, Convert Units on, root scale 1 |
| Forward / Up | -Z Forward, Y Up |
| Apply Transform (bake space transform) | on for static meshes (`--fbx-bake-axes`), so the root is not rotated -90 on X; test on rigs before trusting it |
| Apply Modifiers | on |
| Armature: Add Leaf Bones | off (Unity does not need them) |
| Bake Animation | on for clips; one take per action, or `model@clip.fbx` files for animation-only exports |
| Path Mode / Embed Textures | Copy and embed for a hand-over, but deliver textures as separate files in `out/` too |

Prove the axes once per pipeline: export a 1 m cube with a facing arrow and check Unity shows scale (1,1,1),
rotation (0,0,0) and a 1 m bounding box.

## Geometry and UVs

- Budgets are the project's choice: the target warns above 50k triangles; mobile props are usually 1k to 10k,
  stylized low-poly props 300 to 5k. Keep materials per mesh to one to three (draw calls).
- UV0: the texture set, at one texel density across the kit (for example 512 px per metre for first-person).
- UV1: lightmap UVs for static props that will be baked: inside 0-1, no overlaps, margins between charts,
  proportional to the surface [verified]. Author them (polywright-blender lightmap recipe) or leave UV1 empty and
  let the developer tick Generate Lightmap UVs.
- LODs: `pw.py lods` writes `<name>_LOD0..n` as separate files; for an automatic LOD Group join them as siblings
  in one FBX. Organic and dense meshes may need no hand LODs: Unity's import-time Mesh LOD builds levels from
  256 triangles up, but not for hard-surface or many-piece meshes and not usefully for skinned ones [verified].

## Collision

Ship a proxy, not the render mesh: boxes, capsules and spheres for moving things, one convex hull of at most
255 triangles where a primitive will not do (Unity's convex limit) [verified], a simplified non-convex mesh only
for static level geometry. Keep proxies as separate objects with no material.

## Texture sets per pipeline

| Pipeline | Deliver |
|---|---|
| URP Lit | `_BaseMap` (sRGB), `_Normal` (OpenGL), `_MetallicSmoothness` (R metallic, A smoothness = 1 - roughness), `_Occlusion` [verified layout] |
| HDRP Lit | `_BaseMap`, `_Normal`, `_MaskMap` (R metallic, G occlusion, B detail mask, A smoothness), linear [verified] |
| GLB | glTF ORM (R occlusion, G roughness, B metalness); unity-agent repacks when it moves to Lit |

From glTF ORM: roughness (G) inverted becomes smoothness (A), metalness (B) moves to R. Normal maps stay OpenGL (Y+), the same as
Blender. Textures in powers of two; 2048 for a hero prop, 512 to 1024 for kit pieces.

Styles: stylized low-poly wants flat or hard-edged normals and one shared palette texture or vertex colours;
toon wants clean silhouettes and edited normals on faces (outlines come from the shader); pixel-3D wants tiny
textures meant for point filtering and no mip-mapped detail; PBR realism wants the full baked set above.

## Rigging for Humanoid

- A two-legged, two-armed, one-headed rig with at least 15 bones that map to Unity's Humanoid avatar [verified]:
  hips as root of the deform chain, spine, chest, neck, head, upper and lower arms and legs, hands, feet.
- T-pose or A-pose at rest with the character at the origin facing -Y in Blender, scale 1 on the armature.
- At most 4 bone influences per vertex (Unity's default Standard skin weights) [verified]; normalise weights.
- Name bones plainly (`LeftUpperArm` or Mixamo names) so the auto-mapping succeeds; no leaf bones.
- Non-human rigs (creatures, vehicles) are Generic: one clear root bone.

## Check and hand over

1. `pw.py check out/<file> --target game-unity --real-size-m X` (size, applied scale, UVs, materials, triangles).
2. `pw.py render` a sheet of the export, not the .blend.
3. `pw.py manifest <dir> --add-output out/<file> --target game-unity --inspect`; list the texture files, which
   pipeline they are packed for, the LOD and collider names, and for rigs Humanoid or Generic.
4. The import test belongs to unity-agent: scale (1,1,1), rotation 0, bounds in metres, no import warnings.
