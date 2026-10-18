# Research: polywright-finish

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Finishing meshes for targets: scale, pivots, decimation, LODs, retopology, UVs, baking, PBR, normal maps, collision, rigging, per-engine export. Tier `moderate`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Roblox: at most 20,000 triangles per mesh, 4 bone influences, OpenGL normals only, 1 stud = 0.28 m (create.roblox.com, 2026-10-11). Accessories at most 4,000 triangles; textures upload to 4096 px with a 1024 px budget ceiling (R-20261017-2).
- Unreal Nanite takes dense opaque and masked meshes (UE 5.8 docs); not translucent or morph targets.
- Axes: Blender +Z up front -Y; glTF +Y up front +Z; Unreal +Z cm; Unity +Y left-handed.
- Normal maps OpenGL for Blender, Unity, Godot, glTF, three.js, Roblox; DirectX for Unreal (one secondary source disputes Unity).
- Retopology of AI meshes: QuadriFlow often refuses them; voxel remesh first; Quad Remesher is the common paid choice.

## Open questions

- Unity normal-map convention: test it in an import

## Search plan

Subject:

- create.roblox.com/docs/art/modeling/specifications
- Epic Nanite docs; Unity glTFast releases
- Khronos 3D Commerce guidelines

Tooling:

- gltf-transform, gltfpack, UniRig, Quad Remesher releases

Practice:

- Polycount and r/gamedev on AI mesh cleanup

Testing:

- pw.py check targets.json against importer behaviour

Best sources: project repositories' releases and READMEs, official docs, dated practitioner posts. Noisy: vendor SEO comparison pages (mark them third party).

## Findings log

### R-20261017-3 · 2026-10-17 · Subject: making and finishing models for Unity 6.6 (formats, FBX axes, LODs, lightmap UVs, collision, texture sets, Humanoid)
- summary: Unity 6.6 manual (built 2026-10-16): FBX is Unity's import chain; `.blend` imports only with Blender installed. LOD Group from `_LOD0.._LODn` siblings in one FBX. Mesh LOD (import-time, index-buffer LODs, at least 256 triangles, about half per level; not for skinned deformation, static batching draws LOD0). Lightmap UVs go in `Mesh.uv2` ("UV1"): 0-1, no overlaps, margins, proportional. Convex MeshColliders at most 255 triangles. Humanoid needs at least 15 bones; Standard skin weights are 4 bones. URP Lit: smoothness in the Metallic map's alpha by default; HDRP mask map R metallic, G occlusion, B detail mask, A smoothness, sRGB off. glTFast 6.14.1 is the default .gltf/.glb importer; editor import uses its own shaders, not the default Lit, and its shaders read two UV sets. Blender FBX option values are long-standing practice, not re-read this pass; polywright's own FBX exporter writes FBX Units Scale; targets.json game-unity now says so and leaves the choice to a 1 m cube import test.
- track: subject
- sources: https://docs.unity3d.com/Manual/3D-formats.html, https://docs.unity3d.com/6000.2/Documentation/Manual/importing-lod-meshes.html, https://docs.unity3d.com/Manual/lod/mesh-lod-introduction.html, https://docs.unity3d.com/Manual/lod/mesh-lod-generator.html, https://docs.unity3d.com/Manual/LightingGiUvs-GeneratingLightmappingUVs.html, https://docs.unity3d.com/Manual/class-MeshCollider.html, https://docs.unity3d.com/Manual/ConfiguringtheAvatar.html, https://docs.unity3d.com/6000.2/Documentation/Manual/FBXImporter-Rig.html, https://docs.unity3d.com/6000.2/Documentation/Manual/FBXImporter-Model.html, https://docs.unity3d.com/Manual/urp/lit-shader.html, https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.2/manual/Mask-Map-and-Detail-Map.html, https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.14/manual/features.html, https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.14/manual/ImportEditor.html, https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.14/manual/index.html
- magnitude: minor (new reference)
- applied: C-20261017-3; ../polywright C-20261017-4

### R-20261017-2 · 2026-10-17 · Subject: Roblox model making and finishing (limits, PBR, scale, rigs, cages)
- summary: Read Roblox's current modelling, texture, PBR, export, Blender, importer, reimport, units, character-body, rigid and layered accessory, Avatar Setup and UGC validation pages plus dated DevForum posts; wrote the artist's route as references/roblox.md. Confirms 20,000 triangles per mesh (Importer decimates above it), 4,000 for rigid and layered accessories, R15 body budgets (10,742 total), five SurfaceAppearance maps including the emissive mask, OpenGL normals, texture uploads to 4096 px with a 1024 px budget ceiling (256 px for rigid accessory non-colour maps, 2048 px for Marketplace layered clothing), 1 stud = 28 cm, Blender FBX settings (FBX Unit Scale, no leaf bones), Importer Scale Unit default Studs. Settles two open points in engines.md: the 4,000-triangle accessory budget is verified, and the texture limit is no longer unverified.
- track: subject
- sources: https://create.roblox.com/docs/art/modeling/specifications.md, https://create.roblox.com/docs/art/modeling/texture-specifications.md, https://create.roblox.com/docs/art/modeling/surface-appearance.md, https://create.roblox.com/docs/art/modeling/export-requirements.md, https://create.roblox.com/docs/art/blender.md, https://create.roblox.com/docs/studio/importer.md, https://create.roblox.com/docs/art/modeling/reimport.md, https://create.roblox.com/docs/physics/units.md, https://create.roblox.com/docs/avatar/character-bodies/specifications.md, https://create.roblox.com/docs/avatar/rigid-accessories/specifications.md, https://create.roblox.com/docs/avatar/layered-accessories/specifications.md, https://create.roblox.com/docs/avatar-setup/auto-setup-requirements.md, https://create.roblox.com/docs/marketplace/validation-system.md, https://create.roblox.com/docs/performance-optimization/improve.md, https://devforum.roblox.com/t/2057539 (3D Importer full release, 2022-11-17: decimates over 20k), https://devforum.roblox.com/t/4859863 (Auto-Reimport beta, 2026-09-08), https://devforum.roblox.com/t/4878198 (Tunable collision, 2026-09-17)
- magnitude: minor (new reference)
- applied: C-20261017-2; ../polywright C-20261017-4

### R-20261017-1 · 2026-10-17 · Subject: making and finishing models for three.js and the web
- summary: Artist-side rules for web GLBs: draw calls, download size and GPU texture memory decide, not triangles; seams and hard edges split vertices; one material per prop and shared kits; keep named parts code needs (gltf-transform 4.5.1 `optimize` defaults to `--join-named true` and `--flatten true`); Blender glTF exporter: AO only through the `glTF Material Output` group's `Occlusion` input, vertex colours exported by default only when used in the material (`Use Vertex Color: Material`), `+Y Up` and `Apply Modifiers` options; KTX2 needs power-of-two or multiple-of-4 sizes, ETC1S for colour, UASTC for normals and ORM; gltfpack 1.3.0 quantization defaults 14/12/8 bits, `-tc`/`-tu` per class, `-tl`, `-kn`, npm build cannot encode textures; KHR_meshopt_compression is a release candidate (three's loader reads it).
- track: subject
- sources: https://github.com/KhronosGroup/glTF-Blender-IO/blob/main/docs/blender_docs/scene_gltf2.rst, https://github.com/KhronosGroup/3D-Formats-Guidelines/blob/main/KTXArtistGuide.md, https://meshoptimizer.org/gltf/, https://gltf-transform.dev/cli, https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_meshopt_compression/README.md, https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html, https://github.com/m4bwav/threewright/blob/main/kb/topics/models-for-the-web.md
- magnitude: minor (new reference)
- applied: C-20261017-1; ../polywright C-20261017-4

### R-20261011-2 · 2026-10-11 · Tooling: Retopology, UV and rigging tools for generated meshes
- summary: Quad Remesher, QuadriFlow, Instant Meshes, hosted quad remesh; UniRig, Tripo, AccuRIG, Mixamo compared (2026-05 test).
- track: tooling
- sources: [2026-10-11-generative-3d.md](../../ai-docs/research/2026-10-11-generative-3d.md)
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: Engine conventions and budgets
- summary: Axes, units, budgets and per-engine quirks gathered with verification marks.
- track: subject
- sources: [2026-10-11-craft-and-academics.md](../../ai-docs/research/2026-10-11-craft-and-academics.md)
- magnitude: n/a (initial)
- applied: C-20261011-1
