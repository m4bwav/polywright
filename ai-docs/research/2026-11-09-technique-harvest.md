# Technique harvest, batch 2 (2026-11-09)

Three community posts read for polywright. Nothing reproduced on a GPU yet.

## 1. Game-asset pipeline with review on the game's ground (Reddit 1xhmkis)

A solo developer's pipeline: reference, image-to-3D, retopology to an 876-triangle beetle with 4 clips, about 50 minutes and 3-5 % of a monthly quota per asset; modular characters; each piece of feedback becomes a check. No code (a repo is promised; recheck after 2026-11-11 and harvest again only if it ships with a licence).
Open question: should review renders be shot on the game's own ground at gameplay distance? Backlog: `pw.py render --ground grass|snow|IMAGE --cam gameplay`, only if a CPU Blender test shows it catches defects the plain sheet misses.

## 2. Idol, one image to a splat (speridlabs, 2026-10)

Model card huggingface.co/speridlabs/idol, code github.com/speridlabs/idol-sdk, Apache-2.0 (read 2026-11-09). 3DGS PLY up to 1M Gaussians plus camera, 7.2 GB peak, no ComfyUI node; vendor benchmark beats TRELLIS and LGM. Needs Meta-gated DINOv3 ViT-H+/16 (avoid Meta-gated models unless a measured gain is clear) and the gated FLUX.2-dev VAE (non-commercial licence: not for assets that may be sold). Listed in generators.md, not tested.

## 3. Effigy pipeline and de-lighting (github.com/SifuInTheShell/Effigy v0.1.0)

Root MIT (steps/ included); `blender_ops/` is GPL-3.0, idea only. Worth copying as ideas: Pixal3D as default after their blind A/B, a VRAM pre-flight that refuses jobs that will not fit, sprite sheets rendered from 3D clips.
De-light (`refine.py delight`, MIT): regress base colour against the baked AO and divide the shadowing out, amount 0.5 by default, raw AO (not blurred). A CPU maths test on a synthetic bake cut the error from 12.70 to 0.03. A `pw.py delight --albedo --ao --amount` command waits on a GPU test on three real assets.
