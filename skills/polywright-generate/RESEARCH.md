# Research: polywright-generate

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Imagined 3D models: open and hosted image-to-3D and text-to-3D generators, code and procedural modelling, AI texturing, licences. Tier `fast`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Best open local route: TRELLIS.2 (MIT) and Pixal3D (MIT) through ComfyUI's native nodes since 2026-08-22; their weights are separate downloads (seven files in the template).
- Hunyuan3D-2 single and multi-view shape runs on a 16 GB card (100 s at 30 steps, tested 2026-10-11); its licence excludes the EU, UK and South Korea; 2.5 and 3.x are hosted only.
- Raw generator output is dense, lumpy, soft-edged, often non-manifold and without UVs: never game- or print-ready as is.
- Code (bpy, build123d, CadQuery, OpenSCAD) beats diffusion for anything with dimensions; benchmarks show traceback feedback fixes crashes, not shape.

## Open questions

- Does TRELLIS.2 INT8 fit and run at 1024 on a 16 GB RTX 5060 Ti?
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
