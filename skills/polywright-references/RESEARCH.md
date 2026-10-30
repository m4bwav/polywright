# Research: polywright-references

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Reference images, multi-view sets, turnarounds, textures and blockouts that 3D models are built from. Tier `fast`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- The input image decides most of an image-to-3D result: one object, centred, plain background, flat light, little perspective, 1024 px; characters in A-pose.
- Multi-angle adapters for image-edit models (Qwen Image Edit Multiple Angles LoRA 2509, 2511, and a Qwen-Image 2.1 v2 adapter of 2026-10-07) keep identity across views better than prompting each view; colour drifts and needs matching.
- Repainting grey renders of a blockout keeps views consistent because only the camera moves.
- A Z-Image Turbo reference prompt produced a usable fountain reference on 2026-10-11 despite a soft cast shadow; background removal (rembg) handled it.

## Open questions

- Which multi-angle adapter gives the most consistent back views for props (not characters)?
- Is there an open delighting model good enough to recommend?

## Search plan

Subject:

- comfyui-wiki.com news for multi-angle and multi-view LoRAs
- Scenario and other turnaround guides

Tooling:

- `path:SKILL.md turnaround` and `path:SKILL.md "reference sheet"` on GitHub
- ComfyUI templates for multi-view generation

Practice:

- r/StableDiffusion and r/comfyui RSS: `turnaround`, `multi view consistent`

Testing:

- image-to-3D quality versus input quality comparisons (vendor tests, arXiv)

Best sources: project repositories' releases and READMEs, official docs, dated practitioner posts. Noisy: vendor SEO comparison pages (mark them third party).

## Findings log

### R-20261030-1 · 2026-10-30 · Quiet check (refresh since 2026-10-11)
- Subject: CharacterSheet TripleView/QuadView LoRAs for FLUX.2 Klein 9B and Krea 2 (comfyui-wiki 2026-07-31, workflow JSON, no custom nodes; licence follows the Civitai listing) are an option for front/side/back sheets; known weak on asymmetric designs and accessories. Nothing newer found for October. Tooling, practice, testing: nothing new.
- sources: https://comfyui-wiki.com/en/news/2026-07-31-charactersheet-multiview-loras, https://huggingface.co/Alissonerdx/CharacterSheet
- magnitude: 0.2 · applied: note only

### R-20261017-1 · 2026-10-17 · Subject: what image-to-3D generators need from a picture
- summary: Input rules gathered for the mesh side. ComfyUI's Pixal3D tutorial: BiRefNet removes the background and the workflow crops the subject to a centred canvas; MoGe estimates depth and field of view for pixel-aligned back-projection (front matches the input 1:1); a separate multi-view model (`pixal3d_multiview_int8_convrot`) takes a front/side/back turnaround on one image, which settles generators.md's "multi-view reported 2026-09" (updated there). Hunyuan3D-2mv: front, left, back, right as separate images, front alone allowed, background pre-removed. Meshy docs: at least 512x512, evenly lit (shadows give black patches), near-orthographic or telephoto, front/side/back/3-4 under one light, clutter merges into one mesh; A-pose and T-pose are output options for humanoids. TRELLIS.2 and Hunyuan3D-2 READMEs give no input rules. Thin, transparent and reflective parts remain failure cases (sub-voxel parts smoothed by sparse voxels and the Hunyuan ShapeVAE; flat-colour illustrations come out paper-thin). Tripo's blog favours a three-quarter view (vendor content).
- track: subject
- sources: https://docs.comfy.org/tutorials/3d/pixal3d ; https://docs.comfy.org/tutorials/3d/hunyuan3D-2 ; https://docs.meshy.ai/en/webapp/image-to-3d ; https://github.com/microsoft/TRELLIS.2 ; https://github.com/Tencent-Hunyuan/Hunyuan3D-2 ; https://www.tripo3d.ai/blog/how-to-turn-an-image-into-a-3d-model-with-ai ; https://arxiv.org/pdf/2504.10466 ; https://arxiv.org/pdf/2609.15639 (all read 2026-10-17)
- magnitude: minor (new reference)
- applied: C-20261017-2; ../polywright-generate C-20261017-3

### R-20261011-2 · 2026-10-11 · Practice: Expert reference practice
- summary: Orthographic views on one ground line with a height bar, PureRef boards, reference empties scaled to a known dimension.
- track: practice
- sources: [2026-10-11-craft-and-academics.md](../../ai-docs/research/2026-10-11-craft-and-academics.md)
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: Reference rules that decide generator quality
- summary: Plain background, flat light, little perspective, 1024 px, A-pose; check every view against the front.
- track: subject
- sources: [2026-10-11-generative-3d.md](../../ai-docs/research/2026-10-11-generative-3d.md)
- magnitude: n/a (initial)
- applied: C-20261011-1
