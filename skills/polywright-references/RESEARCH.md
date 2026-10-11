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
