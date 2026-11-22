# Routes: find, code, place, capture, generate

How to choose the way a model gets made, with the sources and their licences. Back to [SKILL.md](../SKILL.md).
Research basis: `ai-docs/research/2026-10-11-*.md` in the repository; checked 2026-10-11.

## Order of attack

1. **Find** a model that already exists and whose licence fits the use.
2. **Code** it (bpy, build123d, CadQuery, OpenSCAD) when it has dimensions, parts that fit or sharp edges.
3. **Place** it from open data when it is a real site: `pw.py place`.
4. **Capture** it (photos, scan, measurements) when it is a real object only you can reach.
5. **Generate** it (reference sheet, then image-to-3D) when it is organic or one-off and nothing fits.

Practitioners and agent benchmarks agree on the split: language models are weak at free-form spatial
reasoning but good at parametric code they can run, render and inspect; generators are good at organic
silhouettes and bad at exact dimensions, sharp edges and clean topology. A recognisable real car came from a
free Sketchfab model in one evening where scratch modelling would still look generic.

## Find: where and under what licence

| Source | What | Licence | Notes |
|---|---|---|---|
| Poly Haven (polyhaven.com, public API) | models, PBR textures, HDRIs | CC0 | best first stop for props, rocks, nature, materials |
| Kenney (kenney.nl) | stylised game kits | CC0 | consistent low-poly sets |
| Quaternius (quaternius.com) | low-poly packs, animated characters | CC0 | |
| ambientCG | PBR materials | CC0 | |
| Sketchfab | everything; many downloadable | per model (CC-BY, CC-BY-NC, CC0, store licences) | login to download; game models are thin shells that need work for printing; ToS bars scraping for AI training |
| Printables, MakerWorld, Thingiverse, Cults3D | printable models | per model, often non-commercial | already solid and print-tested; first stop for print jobs |
| Fab (Epic), Unity Asset Store | game assets | store EULA | check engine and redistribution terms |
| patch.gg toolbox (unverified) | ~50k models, textures, splats, audio, mostly aggregated from open stores; CLI and MCP search | per asset, from its source store | sign-in to download; verify each asset's origin and licence ([post](https://www.reddit.com/r/aigamedev/comments/1xt0uwn/)) |
| vinish.dev/free-3d-models | 469 original models in 42 categories (vehicles, dinosaurs, kitchen, rigged mannequin with 36 clips) | CC BY 4.0, commercial use, credit required | no sign-up; GLB, glTF, OBJ, STL; one small solo site, originality is its own claim (checked 2026-11-21) |
| Poly Pizza (poly.pizza) | ~10k low-poly models, incl. the rescued Google Poly archive | CC0 or CC-BY per model | API; good for stylised placeholders |
| Smithsonian 3D, NASA 3D Resources | scanned artefacts, spacecraft | Smithsonian Open Access CC0; NASA media guidelines | real objects, heavy scans that need decimating |
| BlenderKit | models, materials, HDRIs inside Blender | royalty-free (free tier) or CC0 | add-on and account; no redistribution of raw files |
| Free3D, TurboSquid free, CGTrader free | large mixed free sections of paid stores | store licence per model, often personal-use only | quality and licence vary most here; read each page |
| Objaverse / Objaverse-XL | research datasets | ODC-By dataset, per-object licences in metadata | filter by licence before use |

Before downloading or generating, search packs you already own: [AssetCat](https://github.com/digitalhobbit/assetcat) (MIT, local, read-only; link, do not vendor) finds images by meaning (`assetcat search --meaning "oak barrel" --json`); in a 2026-11-18 test on two 16 px tile packs it put 17 of 25 right hits in the top 5, weak on characters and creatures, so look at the top 10.

Record every download: `pw.py manifest <dir> --add-source <url> --what <what> --author <a> --licence <l>`.
Licence secondary-sourced for Poly Haven, Kenney and Quaternius (CC0); confirm on the site at use. vinish.dev fetched 2026-11-21 (R-20261121-1); the Poly Pizza, Smithsonian, NASA, BlenderKit and store free-section rows are from recall, so confirm each licence on its page.

Biggest libraries by count, for ideas or a fast find: Sketchfab (largest downloadable pool), the print sites, Poly Haven, Poly Pizza, Free3D and the store free sections; for CC0 only, Poly Haven, Kenney, Quaternius, ambientCG, Smithsonian. Any of them is also a reference source for a model you then build yourself (polywright-references).

## Disclosure rules for AI-made content (2026)

| Platform | Rule |
|---|---|
| Fab | tag CreatedWithAI when a material part was made with generative AI; the seller is liable |
| Sketchfab | tag CreatedWithAI; filters for AI and human-made; NoAI tag exists |
| Unity Asset Store | allowed if it has value and does not copy third-party work; must be disclosed in the listing |
| Steam | rules rewritten January 2026: disclose AI in shipped content and marketing; dev tools exempt |
| MakerWorld | tag AIGC; AI images not allowed as photos; since February 2026 at least one real photo of the print |
| Printables | AI-generated models must be tagged (details not verified) |

The manifest's `tools` list (model and version) is what answers these.

## Generators and their licences (short; details in polywright-generate)

- TRELLIS.2 and Pixal3D: MIT. Native ComfyUI nodes since 2026-08-22.
- Hunyuan3D 2.x open weights: Tencent community licence, not licensed in the EU, UK or South Korea, 1M MAU cap,
  outputs may not train other models. 2.5 and 3.x are hosted only.
- Hosted (Meshy, Tripo, Rodin): their terms per plan; record the plan.

Scattering many copies (rocks, trees, crowds) is Geometry Nodes, not hair particles: polywright-blender
`gn-scatter`, with its per-instance vertex budget.

## Never

- Export, cache or trace Google Photorealistic 3D Tiles: their terms forbid it, and new EEA-billed projects
  cannot use them at all since 2025-07-08.
- Strip an author's credit or a licence from a found model.
- Ship research-only weights (MASt3R, DUSt3R, Lyra, CHORD) in a commercial path.
