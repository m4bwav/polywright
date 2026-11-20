# Research findings archive: October 2026

Findings moved out of the installed RESEARCH.md files on 2026-11-20 to keep the installed skills folder under its 800 KB budget. Still the record; each RESEARCH.md keeps a one-line pointer per finding.

## polywright

### R-20261030-1 · 2026-10-30 · Quiet check (refresh since 2026-10-11)
- Subject: Blender 5.3 due November 2026 (5.1 March, 5.2 LTS July); no operator change found that affects pw.py. Testing: new agentic Blender benchmarks BlenderWorld (arXiv 2610.23986) and SceneActBench (arXiv 2607.22393) render submissions from several views and grade with binary rubrics, which matches pw.py sheet + judge. Tooling: mcp-printable (PyPI, alpha, Blender and OpenSCAD backends, ships Claude Code skills) noted, not adopted. Practice: nothing new.
- sources: https://arxiv.org/abs/2610.23986, https://arxiv.org/pdf/2607.22393, https://pypi.org/project/mcp-printable/
- magnitude: 0.2 · applied: note only

### R-20261025-1 · 2026-10-25 · Subject: rendering principles for blockout passes and photo textures (round 2 books track)
- Summary: a pass used as a mask is a label image, so filtering (anti-aliasing) and dither make colours that belong to neither side (CGPP 3e §17.5); albedo is a material map separate from lighting, so light baked into a photo has to be divided out (§27.11, §17.4.5 on linear light). Checked on Blender 5.2.1: `scene.display.render_aa` takes OFF, FXAA, 5, 8, 11, 16, 32 (default 8); the remaining off-colour pixels after AA off were +-1 values from `render.dither_intensity`.
- Track: subject
- Sources: Hughes et al., Computer Graphics: Principles and Practice 3e; a probe through `pw.py bpy` on Blender 5.2.1 LTS
- Magnitude: minor
- Applied: C-20261025-2

### R-20261017-1 · 2026-10-17 · Subject: building models and blockouts for film and AI video
- summary: A film needs size, place and camera, not topology. Build from the shot cameras and only what they see; set detail by the largest on-screen size (an LOD ladder per shot size, EWS to ECU); far scenery as plate cards or 2.5D camera projection; kitbash hard-surface sets; splats for scouting and layout, not final pixels (a 2026 feature used them that way). For AI video the blockout is spatial reference and extra detail confuses the model, so passes stay grey. Field tests (crowd 2026-10-13, set 2026-10-15, two fighters 2026-10-16/17) supply the pass rules: one depth range per shot, pose only above about 40 px, face points left out when a head turns away, thick blades in depth only, end states checked through their camera.
- track: subject
- sources: https://thethirdfloorinc.com/?p=76, https://caveacademy.com/wiki/post-production-assets/modelling/model-lods/, https://www.tripo3d.ai/blog/explore/hd-model-hero-asset-requirements-for-film-vfx, https://3dart.it/camera-projection-in-nuke, https://unity.com/blog/games/realizing-rapid-conceptual-design-with-kitbashing, https://radiancefields.com/jurassic-world-rebirth-and-gaussian-splatting, https://flick.art/blog/blender-ai-filmmaking, https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-vcam-virtual-camera-settings
- magnitude: minor (new reference)
- applied: C-20261017-3, C-20261017-4

### R-20261013-1 · 2026-10-13 · Subject: Crowds and battles: Blender blockout drives the video model
- summary: No open video model holds more than about 4 distinct identities; practitioners build battles from layers and cuts (House of David season 2: under 200 extras, AI crowds and Unreal bases composited). The local route that scales is a 3D crowd blockout rendered to control passes (depth first, pose for the front ranks) for Wan VACE (`WanVaceToVideo`) or Wan 2.2 Fun Control: 4n+1 frames, sides divisible by 16, 81 frames at 16 fps. Paid Blender crowd add-ons (Procedural Crowds, iCrowds) document no scripting API, so plain bpy wins for an agent. Coarse proxies beat detailed ones as driving references (smixs visual-skills, idea only). Depth convention for VACE is unstated anywhere; Depth Anything outputs inverse depth, so pw.py writes that.
- track: subject
- sources: docs.comfy.org (wan-vace-to-video node, wan2-2-fun-control, checked 2026-10-13); github.com/ali-vilab/VACE; runcomfy.com Blender to ComfyUI AI Renderer 2.0; superhivemarket.com procedural-crowds (2026-10-13); vp-land.com House of David season 2 (2025-10-16); seedance.tv/blog/comfyui-crowd-video-workflow (2026-09-13); github.com/smixs/visual-skills; full note in cinewright ai-docs/research/2026-10-13-battle-crowd-compositing.md
- magnitude: minor (new capability, no change to existing claims)
- applied: C-20261013-1

### R-20261011-3 · 2026-10-11 · Testing: pw.py proven end to end
- summary: Park (249 buildings, 1 m lidar, watertight 150 mm tile) and fountain (Hunyuan3D-2 in 100 s, Roblox GLB 15k tris passing check, 80 mm watertight print, 3MF accepted by Bambu Studio CLI).
- track: testing
- sources: local runs 2026-10-11; tests/test_pw.py
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-2 · 2026-10-11 · Tooling: Existing agent 3D tools
- summary: Two Blender MCP servers (official Blender Lab 1.0.3, community mcp-for-blender 2.1.9), ShapeWright, text-to-cad, two small meshwright repos; none writes a provenance manifest. Response: polywright is the routing and verification layer and calls them.
- track: tooling
- sources: [2026-10-11-ai-agents-and-3d.md](../../ai-docs/research/2026-10-11-ai-agents-and-3d.md)
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: Route split and the agent loop
- summary: Code for dimensioned parts, generators for organic shapes; plan, act and critique as separate passes; save numbered .blend files and restart instead of long sessions.
- track: subject
- sources: [2026-10-11-ai-agents-and-3d.md](../../ai-docs/research/2026-10-11-ai-agents-and-3d.md)
- magnitude: n/a (initial)
- applied: C-20261011-1

## polywright-finish

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
