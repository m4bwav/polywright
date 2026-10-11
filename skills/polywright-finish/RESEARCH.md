# Research: polywright-finish

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Finishing meshes for targets: scale, pivots, decimation, LODs, retopology, UVs, baking, PBR, normal maps, collision, rigging, per-engine export. Tier `moderate`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Roblox: at most 20,000 triangles per mesh, 4 bone influences, OpenGL normals only, 1 stud = 0.28 m (create.roblox.com, 2026-10-11).
- Unreal Nanite takes dense opaque and masked meshes (UE 5.8 docs); not translucent or morph targets.
- Axes: Blender +Z up front -Y; glTF +Y up front +Z; Unreal +Z cm; Unity +Y left-handed.
- Normal maps OpenGL for Blender, Unity, Godot, glTF, three.js, Roblox; DirectX for Unreal (one secondary source disputes Unity).
- Retopology of AI meshes: QuadriFlow often refuses them; voxel remesh first; Quad Remesher is the common paid choice.

## Open questions

- Unity normal-map convention: test it in an import
- Roblox texture size limit (historically 1024 px)
- Roblox UGC accessory triangle limits (4,000 or 10,000)

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
