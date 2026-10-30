# Research: polywright-generate

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Imagined 3D models: open and hosted image-to-3D and text-to-3D generators, code and procedural modelling, AI texturing, licences. Tier `fast`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Best open local route: TRELLIS.2 (MIT) and Pixal3D (MIT) through ComfyUI's native nodes since 2026-08-22; their weights are separate downloads (seven files in the template).
- Hunyuan3D-2 single and multi-view shape runs on a 16 GB card (100 s at 30 steps, tested 2026-10-11); its licence excludes the EU, UK and South Korea; 2.5 and 3.x are hosted only.
- Raw generator output is dense, lumpy, soft-edged, often non-manifold and without UVs: never game- or print-ready as is.
- Code (bpy, build123d, CadQuery, OpenSCAD) beats diffusion for anything with dimensions; benchmarks show traceback feedback fixes crashes, not shape.

## Open questions

- TRELLIS.2 and Pixal3D at the template's other resolutions on 16 GB (only the template defaults were run)
- Tripo per-task API prices
- CSM, Sloyd, Spline, 3D AI Studio and Luma Genie were not researched.

## Search plan

Subject:

- github.com/microsoft/TRELLIS.2, TencentARC/Pixal3D, Tencent-Hunyuan releases and licences
- 3D Arena and other generator rankings

Tooling:

- ComfyUI release notes and templates (3d_*)
- Meshy, Tripo, Rodin API docs and pricing

Practice:

- HN Algolia `image to 3d`, r/aigamedev and r/comfyui RSS

Testing:

- Hi3DEval, GPTEval3D and new benchmarks on arXiv

Best sources: project repositories' releases and READMEs, official docs, dated practitioner posts. Noisy: vendor SEO comparison pages (mark them third party).

## Findings log

### R-20261030-1 · 2026-10-30 · Quiet check (refresh since 2026-10-11)
- Subject: no new open-weights image-to-3D release since StableGen 0.4.0 (R-20261029-1); TRELLIS.2 (MIT) and Pixal3D stay the open picks, Hunyuan3D 3.x hosted-only (open weights stop at 2.1). Testing: 3DCodeBench (Blender 5.0 procedural code, Uni3D scores) noted. Tooling and practice: nothing new.
- sources: https://microsoft.github.io/TRELLIS.2, https://app.cinevva.com/guides/ai-3d-model-generation-timeline-2026 (third party)
- magnitude: 0.1 · applied: note only

### R-20261029-1 · 2026-10-29 · Subject: StableGen 0.4.0
- StableGen 0.4.0 (Blender add-on, ComfyUI backend): prompt to preview gallery to TRELLIS.2 mesh; texturing by projecting Qwen Image 2.1 from 10 cameras (RTX 4080 16 GB in the maker's video) with Marigold V2 PBR maps; new masked edit (regenerate a painted region through the cameras that see it) and SkinTokens auto-rigging with FBX/BVH retargeting; experimental MOSS Image and FIBO 2.0 Edit. Licences per the maker: Qwen Image 2.1 and FIBO 2.0 Edit non-commercial, MOSS Image Apache-2.0. Found in the everscout indie-ai-games scan; not run here.
- Sources: https://www.reddit.com/r/StableDiffusion/comments/1xiolct/qwen_image_21_trellis2_in_blender_from_a_prompt/, https://github.com/sakalond/StableGen
- Applied: SKILL.md Step 4 (StableGen line)

### R-20261011-3 · 2026-10-11 · Testing: Pixal3D through ComfyUI's template on a 16 GB card
- summary: The seven template files (14.5 GB) downloaded from Comfy-Org on Hugging Face; the template ran unmodified through pw.py gen's converter in 331 s on an RTX 5060 Ti 16 GB (ComfyUI 0.38.2), giving a 700k-triangle textured GLB (4096 px PBR, 55 MB, 515 non-manifold edges) that leans by the camera's elevation. The TRELLIS.2 branch (`--set 316.value=true`) ran in 377 s of GPU time: upright, one part, 699k triangles, 4096 px PBR, the best detail of the three models tried; Hunyuan3D-2 took 99 s for shape only.
- track: testing
- sources: local run 2026-10-11; ComfyUI template 3d_pixal3d_trellis2_image_to_model.json
- magnitude: 0.3 ("likely fits 16 GB" is now measured for both; TRELLIS.2 becomes the default local textured route)
- applied: C-20261011-3

### R-20261011-2 · 2026-10-11 · Testing: Hunyuan3D-2 through pw.py gen
- summary: Fountain reference to mesh in 100 s; then a 15k-triangle Roblox GLB and an 80 mm watertight print from it.
- track: testing
- sources: local run 2026-10-11
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: Generator landscape October 2026
- summary: TRELLIS.2 and Pixal3D native in ComfyUI; Hunyuan 2.x open with a region-limited licence; hosted Meshy, Tripo, Rodin, Hunyuan 3.x.
- track: subject
- sources: [2026-10-11-generative-3d.md](../../ai-docs/research/2026-10-11-generative-3d.md)
- magnitude: n/a (initial)
- applied: C-20261011-1
