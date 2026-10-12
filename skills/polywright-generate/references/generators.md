# Generators (October 2026)

Back to [SKILL.md](../SKILL.md). Source: polywright research note `2026-10-11-generative-3d.md` (seen
2026-10-11; VRAM figures are the projects' own unless marked; "fits 16 GB" is a judgement, not a test, except
where it says tested). Re-check versions and licences at each refresh: this table ages fastest.

## Open weights

| Model | Input | Output | Licence | VRAM | ComfyUI | Best for |
|---|---|---|---|---|---|---|
| TRELLIS.2 4B (Microsoft, 2025-12) | 1 image | GLB with PBR (base colour, roughness, metallic, opacity), textures to 4096 | MIT | 24 GB stated; the INT8 template ran on 16 GB (tested) | native since 2026-08-22 (with remesh, decimate, UV, bake nodes) | best open all-rounder |
| Pixal3D (Tencent ARC, 2026-05) | 1 image; multi-view reported 2026-09 | GLB with PBR | MIT | low-VRAM mode | native since 2026-08-22 | faithful to the input |
| Hunyuan3D 2.0 / 2mv / turbo | 1 image or 4 views | shape | Tencent community | about 6 GB shape | native | multi-view shape; **tested** on a 16 GB card: 100 s at 30 steps |
| Hunyuan3D 2.1 | 1 image | shape plus PBR paint | Tencent community | 10 GB shape, 21 GB paint | community wrappers | shape plus texture on 24 GB+ |
| Hunyuan3D-Omni | image plus points, voxels, skeleton or box | shape | Tencent community | about 10 GB | not found | following a blockout or pose |
| TripoSG 1.5B | 1 image | untextured GLB | MIT | 8 GB | community | clean shape on small GPUs |
| Direct3D-S2 | 1 image | shape, sparse SDF to 1024 | MIT (mirror) | 10 GB at 512 | community | fine geometric detail |
| Step1X-3D | 1 image | watertight shape plus texture | Apache 2.0 | 27 to 29 GB | not found | Apache licence on big GPUs |
| PartCrafter | 1 image | several part meshes | MIT | 8 GB | not found | objects in parts |
| SF3D / SPAR3D (Stability) | 1 image | UV-unwrapped textured mesh in about a second | Stability community (free under USD 1M) | 6 to 7 GB | community | quick drafts |
| SAM 3D Objects (Meta) | photo plus mask | splat PLY | SAM licence | not stated | not checked | objects in cluttered real photos |

Avoid in shipped work: PartPacker (NVIDIA non-commercial), CraftsMan3D (AGPL), Roblox Cube 3D weights (research
RAIL), anything research-only.

## Hosted

| Service | Notes (2026-10) |
|---|---|
| Meshy (meshy-7.1) | clearest public API prices: 20 to 35 credits per image-to-3D; remesh, UV, auto-rig, printability analysis, multi-colour; free tier outputs CC BY 4.0 (third party) |
| Tripo (v3.1, Smart Mesh P1.0) | tops a community arena (2026-08); quad and low-poly output; rigging; per-task prices not found |
| Rodin Gen-2 / 2.5 (Hyper3D) | very dense raw, quad and smart low-poly modes; up to 5 images |
| Hunyuan 3D 3.0 / 3.1 | hosted only (Tencent, partner nodes, resellers about 0.23 to 0.38 USD per model, third party); up to 8 views; Smart Topology |
| Kaedim | artist-checked meshes; studio pricing |

## Which first

| Job | First | Then |
|---|---|---|
| Hard-surface prop | code; TRELLIS.2 then remesh for detailed ones | Rodin or Tripo quad output |
| Stylised character | reference sheet, Hunyuan3D-2mv shape, texture, rig (UniRig, Tripo, AccuRIG) | Tripo or Meshy end to end |
| Organic creature or statue | TRELLIS.2 or Pixal3D | Hunyuan 3.1 hosted |
| Building or modular kit | code | Hunyuan3D-Omni with a box or blockout |
| Printable figurine | TRELLIS.2 or Hunyuan, then `pw.py printable` | a print site's built-in generator |
| Functional printed part | build123d, CadQuery or OpenSCAD | none |
| Roblox prop | any, then decimate under 20k triangles; Roblox's own in-Studio generator knows the limits | |

## Running on ComfyUI

- Hunyuan3D-2 is built into `pw.py gen`: checkpoints `hunyuan3d-dit-v2(.-turbo|-mv|-mv-turbo).safetensors` in
  `models/checkpoints`. Graph: ImageOnlyCheckpointLoader, CLIPVisionEncode per view, Hunyuan3Dv2Conditioning
  (or MultiView), EmptyLatentHunyuan3Dv2 (resolution 3072), KSampler (euler, normal, cfg 5), VAEDecodeHunyuan3D
  (octree 256), VoxelToMesh (surface net, threshold 0.6), SaveGLB.
- TRELLIS.2 and Pixal3D: ComfyUI's template `3d_pixal3d_trellis2_image_to_model` uses `trellis_2_int8_convrot`,
  the shape and texture VAEs, `dino_v3_L_naf_fp32` (CLIP vision), `moge_2_vitl_normal_fp16` and `birefnet`
  (template read 2026-10-11; 14.5 GB in all, downloaded from Comfy-Org on Hugging Face). Pass the template file itself
  to `pw.py gen --workflow`: editor-format workflows are converted with the host's node definitions (previews whose
  image feeds other nodes are kept; widgets a template predates get the host's defaults). The template's switch
  (node 316, PrimitiveBoolean) picks Pixal3D when false (the default) and TRELLIS.2 when true.
- Tested 2026-10-11 on an RTX 5060 Ti 16 GB, ComfyUI 0.38.2, one fountain reference, GPU time from ComfyUI's history:

  | Model | Time | Result |
  |---|---|---|
  | TRELLIS.2 (template, `--set 316.value=true`) | 377 s | upright, one part, 699k triangles, 4096 px PBR, 610 non-manifold edges; the sharpest lion head of the three |
  | Pixal3D (template default) | 329 s | 700k triangles, 4096 px PBR, 55 MB, 515 non-manifold edges; in the camera's frame, leaning by the camera's elevation: level it |
  | Hunyuan3D-2 (built in) | 99 s | shape only, 405k triangles, 3,048 non-manifold edges |
- `pw.py gen` checks every node class in the workflow against each host's `/object_info` and uses the first host
  that has them all.

## Known output problems

Back and underside are guesses; thin parts melt or fuse; extra or missing limbs on characters; lumpy flat
surfaces; soft edges; textures with baked light. Multi-view input fixes most back-side errors; a repainted
blockout (polywright-references Step 3) fixes view disagreement.
