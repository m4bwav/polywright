# Generative 3D: making imagined models from prompts, images, sketches and blockouts

Research for polywright, seen 2026-10-11. Scope: making a 3D model that does not exist yet from little input (a text prompt, one or a few images, a concept sheet, a sketch, a rough blockout), then making it usable (texture, retopology, UVs, rig, printable solid).

How this was gathered: web search and direct fetches of GitHub READMEs, model cards, vendor docs and Hacker News threads on 2026-10-11. Reddit was not reachable: WebSearch refuses reddit.com, and the RSS feeds returned HTTP 429 for every request over about ten minutes (a background fetcher was tried and stopped). Practitioner views below therefore come from Hacker News, blogs, vendor tests and search snippets, not from Reddit threads. The session's web search budget ran out before CSM, Sloyd, Spline, 3D AI Studio and Luma Genie were checked; see Open questions.

Many comparison pages for this topic are vendor SEO blogs (trellis2.app, triposr.org, 3daistudio.com, cinevva.com, costbench.com). They are cited where nothing better was found and marked "third party".

Related: polywright's other research notes in this folder (none yet at the time of writing).

## Bottom line

1. For local work on the 16 GB RTX 5060 Ti, start with **TRELLIS.2 through ComfyUI's native nodes** (merged into core 2026-08-22, PR #14718, bf16 and INT8 checkpoints, PBR plus baked normal and AO maps, remesh, decimate and UV nodes built in). It is MIT, so outputs and the plugin itself carry no region or revenue strings. Microsoft says 24 GB; a Mac port peaked near 15 GB; test 512 and 1024 on the 5060 Ti before promising it. Sources: https://blog.comfy.org/p/trellis2-and-pixal3d-are-now-native, https://comfyui-wiki.com/en/news/2026-08-22-trellis2-pixal3d-native-comfyui, https://news.ycombinator.com/item?id=47828896 (all seen 2026-10-11).
2. **Pixal3D** (Tencent ARC, MIT, May 2026, SIGGRAPH 2026) shares the same native ComfyUI stages and adds pixel-aligned geometry, a low-VRAM mode and (per a third-party timeline) multi-view inference from September 2026. Treat it as TRELLIS.2's sibling and A/B both. https://huggingface.co/TencentARC/Pixal3D
3. Keep **Hunyuan3D-2mv** (already working on the PC) for the multi-view route: front, left, back, right images in, untextured shape out. Its shape stage fits 16 GB. The Hunyuan3D 2.1 paint model needs about 21 GB and will not fit without offload. All open Hunyuan3D weights use the Tencent community licence, which excludes the EU, UK and South Korea, caps at 1M MAU and forbids using outputs to improve other models. A public plugin must warn users in those regions. https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE
4. Hunyuan3D 2.5, 3.0, 3.1 and PolyGen were never released as weights. Hunyuan 3.x is reachable only through Tencent's site, Tencent Cloud, ComfyUI Partner Nodes and resellers like fal (about 0.23 to 0.38 USD per model, third party). https://triposr.org/blog/hunyuan3d-versions, https://costgoat.com/pricing/hunyuan-3d
5. The **input image decides most of the quality**. Generate a reference sheet first: one object, centred, filling more than half the frame, plain white or light grey background, flat even light, no strong perspective, 1024 px or more, the same size for every view; characters in a relaxed standing pose (A-pose for rigging, not a T-pose). https://lilting.ch/en/articles/ai-3d-generation-tools-comparison (2026-01-16), https://fuser.studio/articles/hunyuan3d-guide
6. Use the Mac for the reference sheet step: Qwen Image Edit with the **Multiple Angles LoRA** (2509, 2511, and a Qwen-Image 2.1 v2 adapter from 2026-10-07 with 72 azimuth and elevation presets) turns one concept into consistent views. Expect colour drift between views; add a colour match step. https://comfyui-wiki.com/en/news/2026-10-07-qwen-image-2-1-multiple-angles-lora, https://weirdwonderfulai.art/comfyui/qwen-edit-2509-lora-camera-multi-angle/
7. For the hosted route, the API with the clearest public price list is **Meshy** (meshy-7.1 default, 20 to 35 credits per image-to-3D, remesh 5, UV unwrap 5, auto-rig 5, printability analysis free, repair and multi-colour 10). Meshy-5 retired 2026-10-10. Tripo v3.1 tops a community arena (ELO 1042, 2026-08-03) but its per-task credit table was not found. https://docs.meshy.ai/en/api/pricing, https://www.sloyd.ai/blog/ai-3d-model-generator-rankings
8. **Never ship raw generator topology** for anything that deforms. Every honest source (Hacker News, vendors' own docs, retopology add-on makers) says outputs are dense, lumpy, triangle soup, soft on sharp edges. Budget a remesh step: Quad Remesher (paid) is the common choice; QuadriFlow often fails on AI meshes; vendor quad remesh (Meshy, Tripo, Hunyuan Smart Topology) is easiest. https://news.ycombinator.com/item?id=47157841
9. For **hard-surface and printable functional parts, write code, not diffusion**: an agent writing OpenSCAD, CadQuery or build123d gives exact dimensions, sharp edges, editability and watertight solids. Verification (query the solid, render, check manifold) matters more than which language. https://news.ycombinator.com/item?id=49676577, https://github.com/tonykoop/makerbench-hwe/pull/864
10. For **figurines and organic prints** (Bambu P1S), diffusion output is fine after a voxel remesh or manifold repair, a flat base and a wall thickness check. MakerWorld already offers Meshy-6 image-to-3D at 2 MakerLab credits per export and a Hunyuan-based PrintU figure tool. https://3dprintingindustry.com/news/meshy-and-makerworld-team-up-to-put-ai-3d-model-generation-in-bambu-lab-users-hands-250281/, https://www.3printr.com/bambu-lab-makerlab-printu-ai-tool-generates-3d-figures-from-photos-for-3d-printing-5185578/
11. For **rigging**, run UniRig locally (MIT, 8 GB) or use Tripo, Meshy, AccuRIG or Mixamo. A 2026 UE5 test found Tripo fastest end to end, AccuRIG cleanest for humanoids, Meshy hips off by 5 to 15 cm. https://www.strayspark.studio/blog/ai-auto-rigging-showdown-2026-tripo-meshy-cascadeur-mixamo (2026-05-14)
12. For **texturing an existing mesh** locally, use TRELLIS.2's shape-conditioned texture stage or StableGen (Blender add-on on a ComfyUI backend, GPLv3) with SDXL or Flux. Ubisoft's CHORD (photo to PBR maps) is research-only; do not ship it in a commercial path. https://blog.comfy.org/p/ubisoft-open-sources-the-chord-model
13. **World generators are not asset generators yet.** Marble exports Gaussian splats on its Standard plan and textured GLB plus commercial rights only on Pro; Genie 3 has no API; Lyra 2.0 weights are research-only. Use them for backdrops and previs, not game props. https://docs.worldlabs.ai/marble/export/gaussian-splat/index.md
14. Record the licence per run. Polywright should write a sidecar with model name, version, licence, seed and input images next to every generated asset, because licences differ sharply (MIT, Apache 2.0, Tencent community, Stability community, SAM licence, research-only).

## Generator comparison

VRAM figures are the project's own unless marked. "Fits 16 GB" is a judgement, not a test on this machine.

| Generator | Type | Input | Output | Licence | VRAM | Fits 16 GB? | ComfyUI | Best for |
|---|---|---|---|---|---|---|---|---|
| TRELLIS.2 4B (Microsoft, 2025-12-16) | Open | 1 image | GLB, PBR (base colour, roughness, metallic, opacity), textures to 4096 | MIT | 24 GB stated; about 15 GB peak on a Mac port | Likely at 512/1024 with INT8 or low-VRAM mode; test | Native since 2026-08-22 | General props, characters, best open all-rounder |
| Pixal3D (Tencent ARC, 2026-05) | Open | 1 image; multi-view added 2026-09 (third party) | GLB, PBR | MIT | Low-VRAM mode, 1024 default there | Likely | Native since 2026-08-22 | Faithful to the input image |
| Hunyuan3D 2.1 (Tencent, 2025-06-13) | Open | 1 image | Shape plus PBR paint | Tencent community: no EU/UK/KR, 1M MAU cap | 10 GB shape, 21 GB paint, 29 GB both | Shape yes, paint no | Community wrappers (kijai 2.0, visualbruno 2.1) | Shape plus strong textures on 24 GB+ |
| Hunyuan3D 2.0, 2mv, mini, turbo (2025-01 to 04) | Open | 1 image or 4 views (2mv) | Shape; 2.0 paint is RGB only | Tencent community | 6 GB shape, 16 GB with texture | Yes for shape | Native for 2.0 and 2mv shape | Multi-view reference sheets |
| Hunyuan3D-Omni (2025-09-25) | Open | Image plus point cloud, voxels, skeleton or bounding box | Shape | Tencent community | about 10 GB | Yes | Not found | Following a blockout or pose |
| Hunyuan3D-Part: P3-SAM, X-Part light (2025-09) | Open | Mesh | Part segmentation, completed parts | Tencent community (third party) | Not stated | Unknown | Not found | Splitting a mesh into parts |
| Hunyuan 3D 3.0 / 3.1 (2025-09, 2026-01) | Hosted | Up to 8 views (3.1) | PBR, 1536 cubed geometry, Smart Topology | Service terms | n/a | n/a | Partner Nodes | High detail when you can pay |
| Step1X-3D (StepFun, 2025-05-13) | Open | 1 image | Watertight shape plus SDXL-based texture | Apache 2.0 | 27 to 29 GB both stages | No (shape alone maybe) | Planned, not found | Apache-licensed alternative on big GPUs |
| TripoSG 1.5B (VAST, 2025-03) | Open | 1 image; scribble model 2025-04 | Untextured GLB | MIT | 8 GB | Yes | Community | Clean shape, small GPU |
| TripoSF (VAST, 2025-04) | Open (VAE only) | n/a | 1024 cubed SparseFlex | Check repo | n/a | n/a | No | Research only |
| Direct3D-S2 (DreamTech, 2025-05-30) | Open | 1 image | Shape, sparse SDF up to 1024 | MIT (mirror) | 10 GB at 512 (third party) | Yes at 512 | Community | Fine detail geometry |
| Hi3DGen / Stable3DGen (2025-03-28) | Open | 1 image | Geometry via normal maps | MIT | Not stated | Probably | Not found | Sharp geometry detail |
| PartCrafter (2025-07-13) | Open | 1 image | Several separate part meshes | MIT | 8 GB | Yes | Not found | Objects needing separate parts |
| PartPacker (NVIDIA, 2025-06-11) | Open | 1 image | Part meshes | NVIDIA non-commercial | about 10 GB | Yes | Not found | Research only |
| SAM 3D Objects (Meta, 2025-11-19) | Open | Photo plus mask | Gaussian splat PLY (mesh not shown in README) | SAM Licence (commercial allowed, trade-control limits) | Not stated | Unknown | Not checked | Objects in real photos |
| SF3D / SPAR3D (Stability, 2024-08, 2025-01) | Open | 1 image, 512 px | UV-unwrapped textured mesh in under 1 s | Stability community: free under 1M USD revenue | about 6 to 7 GB (SF3D, third party) | Yes | Community | Fast drafts |
| InstantMesh (2024) | Open | 1 image | Mesh | Apache 2.0 | Not checked | Yes | Community | Superseded |
| Unique3D (2024) | Open | 1 image | Textured mesh | MIT (unconfirmed) | Not checked | Probably | Community | Superseded |
| CraftsMan3D (2024) | Open | 1 image | Mesh | AGPL-3.0 per its HF Space | Not checked | Probably | No | Avoid: AGPL |
| Roblox Cube 3D (2025-03) | Open | Text | Mesh | Research-only RAIL-MS per Wikipedia | Not checked | Unknown | No | Roblox Studio users use it in Studio |
| Meshy 7.1 / 6 / 6-lite | Hosted | Text, 1 image, up to 4 views | PBR to 8K, remesh, UV, rig, print repair | Paid plans; free tier CC BY 4.0 (third party) | n/a | n/a | Community | Full pipeline API |
| Tripo v3.1, P1.0 Smart Mesh | Hosted | Text, image, multi-view | PBR, quad, low-poly in about 2 s (vendor claim) | Paid to commercialise | n/a | n/a | Community | Top arena ranking, rigging |
| Rodin Gen-2 / Gen-2.5 (Hyper3D) | Hosted | Text, up to 5 images | Above 10M polys raw, quad, Smart Low-Poly | Paid plans | n/a | n/a | Community | High detail, quad output |
| Hitem3D v2 (Sparc3D inside) | Hosted | Image | High detail mesh | Paid | n/a | n/a | No | Detail; trust concerns raised |
| Kaedim | Hosted, human in the loop | Image | Artist-checked mesh | 400 to 1,200 USD a month (third party, conflicting) | n/a | n/a | No | Studios paying for clean topology |

Sources for the table: TRELLIS.2 https://github.com/microsoft/TRELLIS.2; Hunyuan versions https://triposr.org/blog/hunyuan3d-versions (third party, tested 2026-09-08) and https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1; dated timeline https://app.cinevva.com/guides/ai-3d-model-generation-timeline-2026 (third party, 2026-09-06); Step1X-3D https://github.com/stepfun-ai/Step1X-3D; TripoSG https://github.com/VAST-AI-Research/TripoSG; Hi3DGen https://github.com/Stable-X/Hi3DGen; PartCrafter https://github.com/wgsxm/PartCrafter; SAM 3D https://github.com/facebookresearch/sam-3d-objects; Stability licence https://huggingface.co/stabilityai/stable-fast-3d; CraftsMan and InstantMesh licences from their Hugging Face spaces; Cube 3D https://en.wikipedia.org/wiki/Cube_3D; Kaedim https://costbench.com/software/ai-3d-generation/kaedim/. All seen 2026-10-11.

### Which to reach for

| Job | First choice | Second choice | Why |
|---|---|---|---|
| Hard-surface prop (crate, weapon, console) | Code (Blender Python or CadQuery) for simple forms; TRELLIS.2 then remesh for detailed ones | Rodin or Tripo quad output | Diffusion rounds sharp edges; code keeps them |
| Stylised game character | Reference sheet on Mac, then Hunyuan3D-2mv shape, then texture, then UniRig or Tripo rig | Tripo or Meshy end to end | Multi-view fixes the guessed back; rig needs clean A-pose |
| Organic creature or statue | TRELLIS.2 or Pixal3D | Hunyuan 3.1 hosted | Organic forms hide lumpiness |
| Building or modular kit | Code (procedural Blender or a kit) | Hunyuan3D-Omni with a bounding box or blockout | Grid and modularity matter more than detail |
| Printable figurine (P1S) | TRELLIS.2 or Meshy, then voxel remesh, base, wall check | MakerWorld Meshy tool | Organic shape, needs a closed solid |
| Printable functional part | OpenSCAD, CadQuery or build123d by an agent | none | Needs exact sizes and tolerances |
| Real object from a photo | SAM 3D Objects | TRELLIS.2 | SAM 3D handles occlusion in clutter |
| Multi-part object (for kitbashing, print in parts) | PartCrafter | Hunyuan3D-Part on an existing mesh | Separate meshes per part |
| Roblox | Roblox's own Cube 3D / 4D in Studio, or an import kept under the face and triangle limits | Any generator, then decimate | In-engine tool knows the limits |

## 1. Image-to-3D and text-to-3D models

### Open weights

**TRELLIS.2** (Microsoft, arXiv 2512.14692, released 2025-12-16). 4B flow-matching transformer on an "O-Voxel" representation. Image to 3D only; no text-to-3D. Output is a GLB with base colour, roughness, metallic and opacity; alpha is stored but exported OPAQUE, so connect it by hand. H100 timings: 512 cubed about 3 s, 1024 about 17 s, 1536 about 60 s. Official requirement: 24 GB, Linux only. https://github.com/microsoft/TRELLIS.2 (seen 2026-10-11)
- On 2026-08-22 ComfyUI merged native TRELLIS.2 and Pixal3D (PR #14718). No custom nodes or compiled CUDA extensions. Checkpoints come as bf16 and "INT8 ConvRot". Image encoder DINOv3 ViT-L. It ships BiRefNet for background removal and MoGe for camera field-of-view estimation, plus mesh nodes: remesh, decimate, UV unwrap, bake texture, AO and normal map, fill holes, weld, smooth normals, and GLB, splat and point cloud export. Needs ComfyUI 0.34.0 or later. https://comfyui-wiki.com/en/news/2026-08-22-trellis2-pixal3d-native-comfyui, https://blog.comfy.org/p/trellis2-and-pixal3d-are-now-native (2026-08-31)
- Community nodes before that: PozzettiAndrea/ComfyUI-TRELLIS2 (MIT) and visualbruno/ComfyUI-Trellis2 (Windows wheels). A Patreon author hit out-of-memory errors even on a 24 GB 4090 and lowered guidance strength to fix it. https://www.patreon.com/posts/146806567
- Apple Silicon port trellis-mac: about 3.5 min per model on an M4 Pro, peak about 15 GB. https://news.ycombinator.com/item?id=47828896
- Practitioner reception was mixed. One HN user called it "not very good" next to Meshy; others valued MIT and unlimited local runs. https://news.ycombinator.com/item?id=46295295

**Pixal3D** (TencentARC, arXiv 2605.10922, SIGGRAPH 2026). Back-projects pixel features into 3D for tight input fidelity. Main branch uses the TRELLIS.2 backbone; paper branch uses Direct3D-S2. MIT. Low-VRAM mode loads models on demand (1024 default there, 1536 in standard mode). https://huggingface.co/TencentARC/Pixal3D. A comparison page from 3D AI Studio exists (not read): https://www.3daistudio.com/blog/pixal3d-vs-trellis-2-vs-hunyuan-3d-comparison

**Hunyuan3D family** (Tencent).
- 2.0 (arXiv 2501.12202, 2025-01-21): shape 6 GB, 16 GB with RGB texture. Variants mini (0.6B), 2mv (multi-view), turbo and FlashVDM (2025-03 to 04). Native ComfyUI supports 2.0 and 2mv shape only, not texture. The turbo multi-view workflow wants cfg 1.0 plus a FluxGuidance node. https://docs.comfy.org/tutorials/3d/hunyuan3D-2.md, https://blog.comfy.org/p/hunyuan3d-20-and-muitiview-native
- One user report: the 2.0 texture stage fails above 50,000 faces; decimate first. (Reddit snippet via a mirror, https://reddit.fsky.io/r/StableDiffusion/s/evI5QODwEX, unverified.)
- 2.1 (arXiv 2506.15442, 2025-06-13): 3.3B shape plus 2B PBR paint model, training code released. Shape 10 GB, paint 21 GB, both 29 GB. Supports Windows, macOS, Linux per README. https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- Licence for 2.x: "Tencent Hunyuan 3D 2.1 Community License". Territory excludes EU, UK, South Korea. Over 1M MAU needs a separate licence. Tencent claims no rights in outputs. Section 5(b) forbids using outputs to improve other AI models. https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE. (Some pages call 2.0 "Apache 2.0"; that is wrong per the third-party version table, which lists the same community licence.)
- Omni (2025-09-25): controllable generation on the 2.1 architecture with point cloud, voxel, skeleton or bounding box conditions; about 10 GB. Useful for "follow my blockout". https://github.com/Tencent-Hunyuan/Hunyuan3D-Omni (via aggregators)
- Part (2025-09): P3-SAM (native 3D part segmentation of any mesh, with part boxes) and a light X-Part (completes each part). Full X-Part lives in Hunyuan3D Studio. https://github.com/Tencent-Hunyuan/Hunyuan3D-Part
- 2.5 (arXiv 2506.16504), 3.0 (2025-09-16, 1536 cubed), 3.1 (2026-01-28, up to 8 views) and PolyGen (2025-07, autoregressive retopology) are hosted only. GitHub issue #111 asking for 2.5 and PolyGen weights has no maintainer answer. https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/issues/111
- Hunyuan3D Studio (arXiv 2509.12815) describes Tencent's full game-asset pipeline: concept image, geometry, part split, PolyGen retopology, semantic UV, texture, rig. Good map of the stages polywright needs.

**Step1X-3D** (StepFun, arXiv 2505.07747, 2025-05-13). 1.3B geometry (watertight TSDF) plus 3.5B SDXL-based texture model. Apache 2.0. 27 GB (or 29 GB with the label model) for both stages, 152 s at 50 steps. Includes an 800K-asset dataset and watertight preprocessing code. ComfyUI only "planned". https://github.com/stepfun-ai/Step1X-3D

**TripoSG** (VAST, 2025-03). 1.5B rectified-flow MoE transformer over SDF. MIT, 8 GB. TripoSG-scribble (2025-04) takes a scribble plus text. Untextured output. https://github.com/VAST-AI-Research/TripoSG. **TripoSF**: only the VAE was released; full model went into Tripo 3.0. https://www.tripo3d.ai/blog/vast-open-source-month

**Direct3D-S2** (arXiv 2505.17412, 2025-05-30). Sparse SDF with spatial sparse attention, up to 1024 cubed. MIT per a model-card mirror; 10 GB at 512 per a third-party timeline. https://arxiv.org/html/2505.17412v1

**Hi3DGen / Stable3DGen** (arXiv 2503.22236). Image to normal map to geometry, on a TRELLIS base. MIT; the maintainers removed kaolin, nvdiffrast and flexicubes "so it can be used commercially". https://github.com/Stable-X/Hi3DGen

**PartCrafter** (arXiv 2506.05573, NeurIPS 2025). Several part meshes from one image in one pass; scene version too. MIT, 8 GB. Windows guide in a fork. https://github.com/wgsxm/PartCrafter

**SAM 3D Objects** (Meta, 2025-11-19; encoder weights 2026-06-01; "3D Artist Object Set" and HF leaderboard 2026-06-02). Image plus mask in; Gaussian splat PLY out in the README example; meant for objects in real, cluttered photos. SAM Licence allows commercial use subject to trade controls and use bans (weapons, military, etc). https://github.com/facebookresearch/sam-3d-objects, https://www.deeplearning.ai/the-batch/metas-sam-3-image-segmentation-suite-analyzes-and-creates-3d-bodies-and-other-objects

**SF3D and SPAR3D** (Stability). Fast reconstruction (0.5 to 0.7 s) with UV-unwrapped meshes; quality below the native 3D diffusion models. Stability Community Licence: free under 1M USD annual revenue. https://huggingface.co/stabilityai/stable-fast-3d

**Older 2024 multi-view-then-reconstruct models** (InstantMesh, Unique3D, CraftsMan). Superseded in quality by native 3D latent models. CraftsMan is AGPL-3.0 per its own Space, which rules it out for bundling.

**Roblox Cube 3D** (2025-03). Text to mesh, open weights under a research-only RAIL licence (per Wikipedia; check the repo). Roblox's 4D creation (multi-part functional objects like a five-part car) entered open beta 2026-02-04. https://techcrunch.com/2026/02/04/robloxs-4d-creation-feature-is-now-available-in-open-beta/

### Hosted services

**Meshy** (API docs seen 2026-10-11, https://docs.meshy.ai/en/api/pricing).
- Models: meshy-7.1 (alias latest), meshy-7 (legacy), meshy-6, meshy-6-lite, meshy-t2. meshy-5 retired 2026-10-10; "lowpoly" retires 2026-10-30.
- Credits: image-to-3D 20 (mesh only), 30 (2K or 4K texture), 35 (8K); +5 for 2k/4k geometry resolution. Text-to-3D preview 20, refine 10 to 15. Multi-image same as image. Retexture 10 to 15. Remesh 5. UV unwrap 5. Auto-rig 5. Animation 3 per action. Printability analysis free; repair, multi-colour and auto-split 10 each.
- Plan prices are not on the API page. Third parties say Pro is about 20 USD a month for 1,000 credits, but tier names and prices conflict across sources. https://costbench.com/software/ai-3d-generation/meshy/
- Product dates (third party): Meshy 6 GA 2026-01-18 with Low Poly Mode; native 8K textures 2026-07-22; multiview upgrade (main plus three auxiliary views) 2026-08-07; Meshy 7 2026-08-12; 3D Agent beta 2026-06-04. https://app.cinevva.com/guides/ai-3d-model-generation-timeline-2026

**Tripo** (VAST). v3.1 (H3.1) and Smart Mesh P1.0 announced 2026-03-09 for GDC; P1.0 claims engine-ready low-poly in about 2 s (press release only). API bills in credits, frozen on submit and refunded on failure; `/v3/account/usage` reports credits per task. Per-task table not found. An old announcement put API credits at 0.01 USD each. A tracker says the top web plan rose to 329.70 USD a month on 2026-08-24 (unverified). https://developers.tripo3d.com/en/docs/billing, https://www.newsfilecorp.com/release/289472/, https://costbench.com/changelog/tripo-ai-price-increase-2026-08/

**Rodin / Hyper3D** (Deemos). Gen-2 (2025-10-01, 10B, part-based), Gen-2 Edit (2026-03-31, text region edits), Gen-2.5 (2026-05-26: raw output above 10M polygons, tri, quad and Smart Low-Poly). Up to 5 input images, 1536 px or more. Price unclear: about 40 credits at 1.50 USD per download on plans, 0.80 USD per call on a reseller (third party). Blender-MCP integrates Rodin directly. https://www.costbench.com/software/ai-3d-generation/rodin-hyper3d/

**Hunyuan 3D 3.x hosted.** 20 free generations a day on Tencent's global site; about 25 credits per job plus 10 each for multi-view, PBR or face control, about 0.02 USD per credit (third party). fal prices: v3.1 Rapid 0.225 USD, v3/v3.1 Pro 0.375 USD, v2 multi-view turbo 0.015 USD (third party, 2026-08-31). https://costgoat.com/pricing/hunyuan-3d. ComfyUI Partner Nodes expose 3.0 with 2 to 4 views and "Smart Topology". https://docs.comfy.org/tutorials/partner-nodes/hunyuan3d/hunyuan3d-3-0.md

**fal TRELLIS.2**: 0.25 USD at 512, 0.30 at 1024, 0.35 at 1536. https://fal.ai/models/fal-ai/trellis-2 (seen 2026-10-11)

**Others.** Hitem3D (Sparc3D inside; weights promised then never released; one reviewer raised trust concerns). ByteDance Seed3D (enterprise API, resold). Kaedim (human-checked, studio pricing). Adobe's Text to 3D lived in Substance 3D Viewer, which Adobe stopped supporting on 2025-10-16; no current home found. No current OpenAI, Google or NVIDIA object generator was found; NVIDIA's open work is Lyra (worlds) and PartPacker (non-commercial). https://docs.hitem3d.ai/en/api/getting-started/introduction, https://helpx.adobe.com/substance-3d-viewer/interface/generate-workspace.html

### Rankings

- A community "Top 3D AI" arena on 2026-08-03 (186,939 votes): Tripo v3.1 1042, Hitem3D v2.0 1025, Sloyd v3 1015, N4D-2.5 1013, Triverse 3.0 1012, Rodin Gen 2.5 1009, Hitem3D v2.1 1005, Meshy 6 1004. Reported by Sloyd, a vendor that ranks itself third. https://www.sloyd.ai/blog/ai-3d-model-generator-rankings
- Hugging Face 3D Arena paper (arXiv 2506.18787, mid-2025, 123,243 votes, 19 models): textured outputs beat untextured by 144 ELO; splats beat meshes by 17 ELO. Lesson: voters judge looks, not topology. Arena rank is a poor guide for game or print use. https://huggingface.co/papers/2506.18787

## 2. Multi-view generation and the reference sheet step

### Multi-view models

- **Zero123++**, **Era3D** (2024): older single-image to six-view diffusion. Superseded for this use.
- **MV-Adapter** (arXiv 2412.03632, ICCV 2025): plug-in adapter that makes SDXL output consistent multi-views, with checkpoints for text plus geometry (tg2mv), image plus geometry (ig2mv, which is texturing) and image to arbitrary views. Licence not confirmed. https://huggingface.co/biali/mvadapter
- **Hunyuan3D-2mv** takes front, left, back and right images directly. Hunyuan's recommended view order for multi-view: front, left, back, right, top, bottom, left-front, right-front. https://fuser.studio/articles/hunyuan3d-guide
- **Qwen Image Edit Multiple Angles LoRA**: 2509 and 2511 versions rotate, tilt and zoom one image while keeping identity. Qwen-Image 2.1 Multiple-Angles v2 (2026-10-07) offers 72 azimuth and elevation framings; "show the back" prompts tend to keep the subject in place. Users report colour drift between views and that some custom angles do not work. https://comfyui-wiki.com/en/news/2026-10-07-qwen-image-2-1-multiple-angles-lora, https://weirdwonderfulai.art/comfyui/qwen-edit-2509-lora-camera-multi-angle/

### What reference images to make before meshing

From vendor input specs and the January 2026 cross-tool test (https://lilting.ch/en/articles/ai-3d-generation-tools-comparison, 2026-01-16) and Hunyuan's own rules (https://fuser.studio/articles/hunyuan3d-guide):

- One object only, centred, filling more than half the frame. No text, no busy background.
- Plain white or light grey background with clear contrast, or cut out with BiRefNet first.
- Even, flat light. No hard highlights or cast shadows; they get baked into albedo.
- No fisheye and little perspective. A long-lens or orthographic look is best; for multi-view sets keep the same camera distance and size.
- 1024 px or more (Rodin wants 1536+; Hunyuan accepts 128 to 5,000 px, under 8 MB). All views the same size.
- Avoid reflective and transparent materials in the input; describe them in the texture step instead.
- Characters: relaxed standing pose. T-poses distort proportions (Rodin tests); action poses with spread limbs fail; AccuRIG and most riggers want an A-pose facing a set direction. So: A-pose with arms 30 to 45 degrees down, legs slightly apart, fingers spread a little, mouth closed.
- Front-only input makes the model invent a plain back. Either supply back and side views or use a three-quarter view, which gives more depth cues.
- Three or four views are "dramatically better" than one for tools that accept them.
- If results look far worse than the official samples, the input is usually the cause.

Practical recipe for polywright (owner's hardware):
1. Mac: generate the concept (Flux, Z-Image or Klein) with "full body, neutral A-pose, orthographic, plain light grey background, even studio light, centred".
2. Mac: Qwen Image Edit plus Multiple Angles LoRA for left, back and right at the same scale; colour-match to the front.
3. PC: cut out with BiRefNet; check the four silhouettes agree in height.
4. PC: Hunyuan3D-2mv for shape (or TRELLIS.2 / Pixal3D from the best single view); compare.

## 3. Texture generation

### Texturing an existing mesh

- **Hunyuan3D-Paint 2.1**: mesh-conditioned multi-view diffusion making PBR; Tencent's own table beats TEXGen on CLIP-FID (24.78 against 28.24) and LPIPS. 21 GB, so not on 16 GB without offload. https://arxiv.org/pdf/2506.15442
- **TRELLIS.2 texture stage**: the README describes shape-conditioned PBR texturing of an existing shape; in ComfyUI the texture stage plus bake nodes give base colour, roughness, metallic, and baked normal and AO. Probably the best local route on 16 GB. https://github.com/microsoft/TRELLIS.2
- **StableGen** (sakalond/StableGen, GPLv3): Blender 4.2+ add-on on a ComfyUI backend. Projects SDXL or FLUX.1-dev from cameras around the object, sequential mode inpaints view by view with visibility masks, ControlNet for geometry, IPAdapter for style. Windows or Linux, NVIDIA. Qwen Image Edit support was "coming" in November 2025. Fits the owner's split: Blender on the PC, ComfyUI on either host. https://cgworld.jp/flashnews/01-202511-StableGen.html
- **StableProjectorz** (free, Igor Aherne): depth-guided projection keeping the original UVs, inpaint masks, seam painting, AO bake; SD and Flux. Windows GUI, not scriptable. https://cgpress.org/archives/stable-projectorz-an-ai-tool-for-3d-texture-generation.html
- **Meshy Retexture** API: 10 to 15 credits. https://docs.meshy.ai/en/api/pricing
- **Material Anything** (arXiv 2411.15138, 3DTopia): PBR for any mesh via diffusion with confidence masks; licence not confirmed.
- TEXGen, MaterialPalette, MatFuse: research code; not checked this session.

### Tileable PBR materials and maps from a photo

- **CHORD** (Ubisoft La Forge, SIGGRAPH Asia 2025): one RGB texture in, base colour, normal, height, roughness, metalness out, with ComfyUI-Chord nodes. Licence is "Ubisoft Machine Learning License (Research-Only, Copyleft)". Do not use for shipped assets. https://blog.comfy.org/p/ubisoft-open-sources-the-chord-model
- Classic non-AI tools still do most of the job: Materialize (free, Windows) and Material Maker (open source, node-based) derive normal and height from an albedo. Substance 3D Sampler has Firefly text-to-texture and image-to-material (paid).
- Browser tools exist (Sorceress Material Forge, NormalMap AI) but are small vendors; NormalMap AI's roughness is a variance heuristic. https://sorceress.games/blog/etch-an-ai-pbr-texture-generator-free-browser-native
- Seamless albedo: generate with Flux or Z-Image using a tiling (circular padding) setting, then derive maps. Several guides warn that seamless output still needs a cleanup pass. https://zsky.ai/blog/ai-texture-generator

### Delighting

- Inputs with baked shadows give albedo with baked shadows. Fix it upstream: ask the image model for "flat, even, shadowless studio light". TRELLIS.2 and Hunyuan paint produce PBR, which separates lighting better than the 2024 RGB-only models. No dedicated delighting tool was verified this session.

## 4. Post-processing generated meshes

### Why it is needed

Native 3D diffusion models decode a latent to an SDF or voxel field and run marching cubes or similar, then decimate. That gives dense triangle meshes, lumpy flat areas, rounded sharp edges, no edge loops, and non-deterministic edits (change the input and the whole mesh changes). Sources: HN discussion of "An autopsy of AI-generated 3D slop" (aircada.com, about 2026-03, 143 points), https://news.ycombinator.com/item?id=47157841; Kat's Bits guide https://www.katsbits.com/codex/optimising-ai-generated-3d-models/.

### Retopology

- **Quad Remesher** (paid add-on): de facto choice for character retopo in Blender per a render-farm guide; geometry only, so re-bake textures afterwards. https://superrendersfarm.com/article/quad-remesher-blender-retopology
- **QuadriFlow** (built into Blender) often refuses AI meshes; **Instant Meshes** (free) is weaker. A vendor test of 18 AI meshes counted usable results: QuadMend 22, Instant Meshes 4, QuadriFlow only after cleanup (self-reported by a competitor). https://superhivemarket.com/products/quadmend
- Hosted: Meshy Remesh (5 credits), Tripo quad and Smart Low-Poly, Rodin quad and Smart Low-Poly, Hunyuan Smart Topology and PolyGen.
- ComfyUI native: Remesh, Decimate, Fill Holes, Weld, UV unwrap (2026-08). Good enough for static props.
- **Artist-mesh generators** (autoregressive, low face count, artist-like edge flow): MeshAnything V2 (arXiv 2408.02555; under 1,600 faces, 8 GB, about 45 s on A6000; wants a clean input; licence file not checked), BPT (above 8,000 faces), DeepMesh (ICCV 2025, 0.5B weights released), FastMesh, Meshtron (NVIDIA, weights not confirmed), and 2026 papers MeshRipple (2512.07514), MeshFlow (2606.04621) and PolyFlow (2606.30673). One 2025 table gives Chamfer distance FastMesh 47.26, DeepMesh 51.11, BPT 54.78, MeshAnythingV2 68.11 (lower is better). They work for low-poly props; they fail on detailed or high-face-count objects. https://github.com/buaacyw/MeshAnythingV2, https://github.com/zhaorw02/DeepMesh
- Face budgets: the render-farm guide's 80k to 120k for characters and 30k to 60k for props is too high for most games. Set the target from the engine (Roblox has per-mesh limits; mobile Unity much lower).

### UVs

- Generators that output PBR already give UVs (often xatlas, fragmented islands). Retopology destroys them; re-unwrap and re-bake from the high-poly. Tools: ComfyUI's native UV node, xatlas (kijai's wrapper upgraded it), Blender Smart UV Project, Meshy UV Unwrap API (5 credits).

### Rigging

- **UniRig** (VAST, arXiv 2504.12451, SIGGRAPH 2025, MIT): skeleton prediction plus skinning, 8 GB; takes obj, fbx, glb, vrm; outputs FBX and a merged rigged GLB. Successor SkinTokens claims 98 to 133 percent better skinning. Install is fragile (flash-attn, Python 3.11). Refine the skeleton before skinning. https://github.com/VAST-AI-Research/UniRig
- **Puppeteer** (Seed3D, NeurIPS 2025 Spotlight, Apache 2.0): rigging plus video-guided animation; FBX export added 2025-09-10. https://github.com/Seed3D/Puppeteer
- **RigAnything**: research; repo and licence not checked.
- Hosted and free tools, tested in Blender 5.1 and UE 5.7 on the same mesh (https://www.strayspark.studio/blog/ai-auto-rigging-showdown-2026-tripo-meshy-cascadeur-mixamo, 2026-05-14):
  - Tripo: about 3 min, handled a non-humanoid robot, near-UE bone names; over-smoothed shoulder weights, noisy jaw, no face joints.
  - Meshy: about 8 min, tolerant of messy topology; hip pivot 5 to 15 cm off, so feet slide; non-standard spine names.
  - AccuRIG: cleanest humanoid weights; needs an A-pose in a fixed direction; humanoid only; one import came in at 0.01 scale.
  - Mixamo: free, huge library, best documented UE retarget; dated and humanoid only.
  - Cascadeur: animation tool, not a rigger.

### Parts, LOD, watertight for printing

- Parts: Hunyuan3D-Part (P3-SAM segmentation, X-Part completion) on an existing mesh; PartCrafter to generate in parts; Meshy auto-split for printing (10 credits).
- LOD: decimate (ComfyUI Decimate, Blender Decimate, meshoptimizer or Simplygon outside AI). Not AI-specific.
- Watertight: voxel remesh closes holes and fixes non-manifold edges, then decimate. Check non-manifold in Blender (Select All by Trait), or use 3D Builder, Meshmixer, Meshy's STL repair. A watertight mesh can still be unprintable: thin walls, fragile details, tight clearances. https://www.3daistudio.com/3d-generator-ai-comparison-alternatives-guide/can-i-3d-print-ai-generated-models, https://all3dp.com/1/5-free-blender-add-ons-to-fix-3d-print-your-messy-ai-models/
- Step1X-3D outputs watertight TSDF geometry by design and ships its watertight preprocessing code.
- Scriptable repair for polywright (not verified this session, from general knowledge): trimesh, PyMeshLab, manifold3d, Blender bpy voxel remesh in background mode.

## 5. LLM and agent-driven procedural modelling

The controllable, editable route: the model writes code that builds geometry, so every dimension is a parameter and edits are deterministic.

### Blender Python

- **Blender MCP** (ahujasid/blender-mcp): add-on plus MCP server; object and material control, scene inspection, arbitrary Python, viewport screenshots, Poly Haven, Sketchfab, Hyper3D Rodin and Hunyuan3D downloads. Versions on mirrors range 1.4 to 1.8; check GitHub releases. https://glama.ai/mcp/servers/ahujasid/blender-mcp
- **LL3M** (arXiv 2508.08228, UChicago): team of agents that plan, retrieve from Blender API docs (BlenderRAG), write, debug and refine Blender scripts from text. The design pattern polywright should copy: plan, write, run, render, critique, fix.
- **MeshCoder** (arXiv 2508.14879, NeurIPS 2025): point cloud to structured Blender Python. Lets a generated or scanned mesh become editable code.
- BlenderGPT, 3D-GPT, SceneCraft, BlenderLLM: earlier systems (see academic list). Not re-checked this session.

### CAD code (printable and mechanical)

- Backends: OpenSCAD (CSG, simple, fast, no queryable topology), CadQuery (B-rep via OCCT, queryable, STEP export), build123d (more Pythonic successor), Replicad (TypeScript; one commenter says LLMs write it better than Python).
- A HN-discussed benchmark: both CadQuery and OpenSCAD made printable parts. "CadQuery fails loudly and early; OpenSCAD fails silently and late." Rendered previews caught nothing that mattered. Commenters: verify by querying the solid, render and annotate screenshots, and remember 95 percent correct is not enough for tight tolerances. https://news.ycombinator.com/item?id=49676577 (about 2026-09)
- MakerBench backend test (one run, model fixed at Sonnet 5.5): objective pass rates OpenSCAD 1.000, CadQuery 0.778, build123d 0.556, failures mostly watertightness checks. Anecdotal. https://github.com/tonykoop/makerbench-hwe/pull/864
- Research benchmarks 2026: Text2CAD-Bench (arXiv 2605.18430, CadQuery target; models do basic geometry but degrade on complex topology), P3D-Bench (2606.11152), RealCADBench (2609.03773), CADENA reverse engineering (2608.00799), "Clarify Before You Draw" proactive agents (2602.03045). Earlier: CAD-Recode, Text2CAD, CADCodeVerify (not re-checked).
- Mesh-as-text LLMs (LLaMA-Mesh, MeshLLM) write OBJ tokens directly; low face counts, novelty value only for now (not re-checked).

### Scenes and procedural generators

- **Infinigen** (Princeton, BSD-3-Clause): procedural nature, indoor and articulated scenes in Blender; exports OBJ and OpenUSD; 2026 ProcFunc preprint (arXiv 2604.26943). Good for environments and layout; heavy to run. https://github.com/princeton-vl/infinigen
- Holodeck and LayoutGPT: LLM picks and places library assets into rooms (not re-checked).
- Practical layer for polywright: an LLM writes a layout (JSON of objects, sizes, positions) and code places generated or library assets. Keeps the layout editable.

### Which gives the most control

1. CAD code (CadQuery, build123d, OpenSCAD): exact, parametric, printable. Best for functional parts and hard-surface kit.
2. Blender Python by an agent with render feedback: editable, any style, texture and materials included; weaker on organic detail.
3. Diffusion with control (Hunyuan3D-Omni with a blockout or skeleton; TRELLIS.2 from a render of a blockout): organic detail, loose control.
4. Plain image-to-3D: least control, most detail.
A hybrid is common: blockout in code, render it, restyle the render with an image model, generate the detailed mesh from that, and keep the blockout as collision or LOD.

## 6. 3D scene and world generation

- **Marble** (World Labs): text, image or video to a world. Free plan cannot export. Standard: splat (SPZ, PLY), 360 panorama, collider mesh. Pro: textured GLB mesh and commercial rights. Prices quoted as 20, 35 and 95 USD a month (third party). A single newsletter claims AMD is buying World Labs (unverified). https://docs.worldlabs.ai/marble/export/gaussian-splat/index.md
- **HunyuanWorld 1.0** (arXiv 2507.21809, 2025-07-26): panorama-based layered mesh worlds with mesh export and separable foreground objects; Flux-based open version; Tencent community licence assumed. https://github.com/Tencent-Hunyuan/HunyuanWorld-1.0. Voyager outputs point clouds, not meshes.
- **Genie 3** (DeepMind): interactive world model; no API; Project Genie for AI Ultra subscribers with 60-second sessions (dates conflict: 2026-01-29 or 2026-06-23). Not an asset source. https://en.wikipedia.org/wiki/Genie_(AI_model)
- **NVIDIA Lyra 2.0** (2026-04-15; GUI and training code 2026-07-20): image or video to explorable scene, export as splats or meshes into Isaac Sim. Model card forbids production use. https://huggingface.co/nvidia/Lyra-2.0
- Matrix-3D and HunyuanWorld-Mirror: not checked.
- Verdict: usable as backdrops, skyboxes, previs and AI-video sets (splats render well in video). Not usable as game-ready props: merged geometry, no parts, splat output, licences that block production.

## 7. What practitioners say

Reddit could not be read this session (see top). These come from Hacker News, blogs and vendor tests.

- **Topology is the universal complaint.** "Topology is all over the place, but only triangles at least"; "rigging garbage topologies is going to be absolute hell outside of static scenery." https://news.ycombinator.com/item?id=46295295
- **Use it as a base or reference, not a final.** Commenters on the "AI 3D slop" thread use outputs as retopology references, or run "fixer" scripts then a human polish pass, "good enough, but way cheaper". Lengthening a handle takes a modeller 10 seconds and needs a full regenerate with AI. https://news.ycombinator.com/item?id=47157841
- **Disagreement:** one camp says retopo tools are mature and imported CAD is messy too, so topology is overstated; another says even the newest models are "nearly impossible to work with for serious production". Same threads.
- **Static props and background items are where it pays.** 3dfy.ai and 3D AI Studio both frame AI 3D as ideation, background props and blockout, with clean quad flow and animation-ready meshes still manual. https://3dfy.ai/?p=1657
- **Rigging test results** (above): the rig that survives export matters more than the rig quality. https://www.strayspark.studio/blog/ai-auto-rigging-showdown-2026-tripo-meshy-cascadeur-mixamo
- **Printing:** Bambu's MakerWorld built AI image-to-3D into MakerLab (Meshy-6, STL or 3MF for Bambu Studio, 2 credits per export, from 2026-03-17) and PrintU (Hunyuan-based figurines, 10 credits). An earlier PrintMon Maker launch hit monthly caps and overload. https://forum.bambulab.com/t/new-makerlab-tool-image-to-3d-model/76805
- **CAD for prints:** agents with OpenSCAD and Claude for dice and brackets "semi-automated, needs rotation fixes". https://news.ycombinator.com/item?id=47157841
- **Licence attention:** a commenter called CHORD's licence "extremely restrictive"; HN users chose TRELLIS.2 for MIT and unlimited local runs.
- **Sparc3D / Hitem3D trust:** a reviewer flagged that Sparc3D's promised free access became the paid Hitem3D. https://lilting.ch/en/articles/ai-3d-generation-tools-comparison

### Concrete workflows seen

1. Indie prop: concept image, TRELLIS.2 or Hunyuan, decimate to budget, auto-UV, bake, import. Static only.
2. Indie character: turnaround sheet, multi-view generation (Hunyuan 2mv, Tripo, Meshy multi-view), quad remesh, re-bake texture, AccuRIG or Tripo rig, retarget to engine skeleton.
3. Print figurine: image, Meshy or Hunyuan (often via MakerWorld), STL or 3MF, slicer repair, print. Multi-colour via Meshy's multi-colour export.
4. Functional print: agent writes OpenSCAD or CadQuery, renders and checks, exports STL or STEP.
5. E-commerce and product shots: the "slop" article argues against AI meshes here because logos and flat panels break.

## 8. Academic state of the art

Ids marked "verified" were seen on arXiv or in a fetched page this session. Others are from memory and need a check before citing.

| Paper | arXiv | Status |
|---|---|---|
| TRELLIS (structured 3D latents) | 2412.01506 | memory |
| TRELLIS.2 | 2512.14692 | verified (repo) |
| Hunyuan3D 2.0 | 2501.12202 | verified |
| Hunyuan3D 2.1 | 2506.15442 | verified |
| Hunyuan3D 2.5 | 2506.16504 | verified |
| Hunyuan3D Studio | 2509.12815 | verified |
| P3-SAM / X-Part | 2509.06784 / 2509.08643 | verified (repo) |
| Step1X-3D | 2505.07747 | verified |
| Direct3D-S2 | 2505.17412 | verified |
| Hi3DGen | 2503.22236 | verified |
| PartCrafter | 2506.05573 | verified |
| Pixal3D | 2605.10922 | verified (model card) |
| TripoSG | 2502.06608 | memory |
| SPAR3D / SF3D | 2501.04689 / 2408.00653 | memory |
| MV-Adapter | 2412.03632 | verified |
| Zero123++ / Era3D | 2310.15110 / 2405.11616 | memory |
| InstantMesh / Unique3D / CraftsMan | 2404.07191 / 2405.20343 / 2405.14979 | memory |
| Material Anything | 2411.15138 | verified |
| MeshAnything V2 | 2408.02555 | verified |
| BPT / DeepMesh | 2412.09548 / 2503.15265 | memory |
| MeshRipple / MeshFlow / PolyFlow | 2512.07514 / 2606.04621 / 2606.30673 | verified (search) |
| UniRig | 2504.12451 | verified |
| LL3M | 2508.08228 | verified |
| MeshCoder | 2508.14879 | verified |
| LLaMA-Mesh | 2411.09595 | memory |
| BlenderLLM / CAD-Recode / Text2CAD | 2412.14203 / 2412.14042 / 2409.17106 | memory |
| 3D-GPT / SceneCraft / Holodeck / LayoutGPT | 2310.12945 / 2403.01248 / 2312.09067 / 2305.15393 | memory |
| Text2CAD-Bench / P3D-Bench / RealCADBench | 2605.18430 / 2606.11152 / 2609.03773 | verified (search) |
| HunyuanWorld 1.0 | 2507.21809 | verified |
| Infinigen ProcFunc | 2604.26943 | verified (repo) |

Surveys: "Recent Advances in 3D Object and Scene Generation" (2504.11734, 2025-04); "A Comprehensive Survey on 3D Content Generation" (2402.01166); "Diffusion models for 3D generation: a survey" (Computational Visual Media, 2025-02, https://cg.cs.tsinghua.edu.cn/papers/CVMJ-2025-diffusion.pdf). No 2026 survey of native 3D diffusion was found.

Benchmarks:
- 3D Arena (2506.18787): human pairwise votes on image-to-3D; rewards looks.
- Hi3DEval (2508.05609): hierarchical validity evaluation for native 3D generators.
- GPTEval3D (2401.04092, memory) and T3Bench (2310.02977, memory): text-to-3D evaluation with VLM judges.
- SAM 3D "3D Artist Object Set" leaderboard (2026-06-02) on Hugging Face.
- The CAD benchmarks above for code-based modelling.

Trend lines (2024 to 2026): multi-view diffusion plus reconstruction gave way to native 3D latent diffusion (TRELLIS, Hunyuan 2.x, TripoSG, Step1X-3D) and sparse high-resolution voxels (Direct3D-S2, TRELLIS.2 at 1536). Part-aware generation (PartCrafter, X-Part, Rodin Gen-2) and artist-mesh autoregression (MeshAnything, DeepMesh, PolyGen) attack the topology problem. The best commercial models (Hunyuan 2.5 and 3.x, Tripo 3, Rodin Gen-2) stopped releasing weights in mid-2025; the open frontier now comes mainly from Microsoft and Tencent ARC under MIT.

## What fits the owner's 16 GB RTX 5060 Ti

| Model | Fit | Note |
|---|---|---|
| TRELLIS.2 native ComfyUI | Probably at 512 and 1024 with INT8; 1536 doubtful | Test first; Microsoft says 24 GB |
| Pixal3D native ComfyUI | Probably, with low-VRAM mode | Test |
| Hunyuan3D-2mv / 2.0 / mini / turbo shape | Yes | Already working |
| Hunyuan3D 2.1 shape | Yes (10 GB) | |
| Hunyuan3D 2.1 paint | No (21 GB) | Offload might work slowly; unverified |
| Hunyuan3D-Omni | Yes (about 10 GB) | |
| TripoSG, PartCrafter, UniRig, MeshAnything V2 | Yes (8 GB each) | |
| Direct3D-S2 | 512 yes, 1024 unknown | |
| SF3D / SPAR3D | Yes | |
| Step1X-3D | No for both stages | |
| Flux, Qwen Image Edit for reference sheets | On the Mac | Keeps the PC free for 3D |

Note the 5060 Ti is a Blackwell (sm_120) card: community wheels for older 3D repos (flash-attn, nvdiffrast, custom rasterisers) may lack builds for it. ComfyUI's native nodes avoid compiled extensions, which is another reason to prefer them. (Inference from the native-integration notes; not tested here.)

## Open questions / unverified

- Real VRAM and speed of native TRELLIS.2 and Pixal3D at 512, 1024 and 1536 on the 5060 Ti. Run it.
- Whether ComfyUI's native Hunyuan3D-2mv got texture support after the 2025 docs.
- Tripo per-task API credits and current credit price; Rodin's official API price; Meshy plan prices.
- Licences not confirmed from the repo files: MV-Adapter, MeshAnything V2, Material Anything, Hunyuan3D-Part (assumed Tencent community), Direct3D-S2 (MIT from a mirror), Unique3D, Cube 3D.
- SAM 3D Objects mesh export path and VRAM (README example shows splats only).
- Pixal3D multi-view inference date (2026-09) comes from a third-party timeline only.
- CSM, Sloyd, Spline, 3D AI Studio, Luma Genie and NVIDIA object generators: not researched (search budget ran out).
- Reddit practitioner threads (r/StableDiffusion, r/comfyui, r/blender, r/gamedev, r/Unity3D, r/3Dprinting, r/aigamedev): not read; RSS returned 429. Retry from a different session or IP at one request per minute.
- Polycount and BlenderArtists threads: none found by search.
- Whether Blender MCP's Hunyuan3D route uses local weights or the hosted API.
- RigAnything, TEXGen, MaterialPalette, MatFuse, Matrix-3D, HunyuanWorld-Mirror: not checked.
- arXiv ids marked "memory" in section 8.
- The World Labs acquisition claim.
- Adobe's text-to-3D after Substance 3D Viewer ended (2025-10-16).
