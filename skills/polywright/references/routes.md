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
| Objaverse / Objaverse-XL | research datasets | ODC-By dataset, per-object licences in metadata | filter by licence before use |

Record every download: `pw.py manifest <dir> --add-source <url> --what <what> --author <a> --licence <l>`.
Licence secondary-sourced for Poly Haven, Kenney and Quaternius (CC0); confirm on the site at use.

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

## Never

- Export, cache or trace Google Photorealistic 3D Tiles: their terms forbid it, and new EEA-billed projects
  cannot use them at all since 2025-07-08.
- Strip an author's credit or a licence from a found model.
- Ship research-only weights (MASt3R, DUSt3R, Lyra, CHORD) in a commercial path.
