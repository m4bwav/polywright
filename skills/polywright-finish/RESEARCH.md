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

### R-20261115-1 · 2026-11-15 · Quiet check
- Quiet (thin pass); glTF, meshopt, KTX2, Roblox, Unity import: nothing new found; tooling: nothing new; testing: nothing new. m 0.

### R-20261109-1 · 2026-11-09 · Tooling: Effigy de-light (no gain on TRELLIS.2, 2026-11-10)
- sources: [2026-11-09-technique-harvest.md](../../ai-docs/research/2026-11-09-technique-harvest.md)
- magnitude: minor

Archived 2026-11-20 to save install size (full text in the repo at ai-docs/archive/research-findings-2026-10.md, not installed):
- R-20261017-3 · 2026-10-17 · Subject: making and finishing models for Unity 6.6 (formats, FBX axes, LODs, lightmap UVs, collision, texture sets, Humanoid)
- R-20261017-2 · 2026-10-17 · Subject: Roblox model making and finishing (limits, PBR, scale, rigs, cages)
- R-20261017-1 · 2026-10-17 · Subject: making and finishing models for three.js and the web
- R-20261011-2 · 2026-10-11 · Tooling: Retopology, UV and rigging tools for generated meshes
- R-20261011-1 · 2026-10-11 · Subject: Engine conventions and budgets

