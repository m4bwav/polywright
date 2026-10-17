# polywright

![A small white robot arm placing a 3D printed grey fountain on a printed miniature park with tiny trees and houses, beside a laptop showing a blue wireframe of the same fountain, a sheet of reference drawings, a caliper and filament spools on a wooden workbench](https://raw.githubusercontent.com/m4bwav/polywright/main/.github/images/banner.jpg)

Seven self-maintaining ("evergreen") skills and one command-line tool that let an AI agent make 3D models of
real and imagined things for games, 3D printing, AI video and AR. It is meant to be the 3D layer other skills and
plugins call when they need a mesh. Written 2026-10-11 for Claude Code, GitHub Copilot, Cursor and Codex, from a
five-part research pass (reality capture, generative 3D, Blender and tooling, modelling craft and academics, how
AI agents do 3D) whose dated notes are in [ai-docs/research](ai-docs/research/index.md).

## What it does

Ask for a 3D model and the hub skill picks the cheapest route that meets the brief:

| Route | When | How |
|---|---|---|
| **find** | a common object whose licence fits | Poly Haven, Kenney, Quaternius, print sites, Sketchfab; licence recorded |
| **code** | it has dimensions or parts that fit | bpy, build123d, CadQuery or OpenSCAD scripts with built-in checks |
| **place** | a real park, street or landscape | `pw.py place`: OpenStreetMap plus public elevation into a game scene and a print tile |
| **capture** | a real object you can photograph or measure | photogrammetry, splats, scanners or modelling from measurements |
| **generate** | an organic or one-off imagined thing | a reference sheet, then image-to-3D on ComfyUI (TRELLIS.2, Pixal3D, Hunyuan3D-2) or a hosted service |

Every route ends the same way: inspect the numbers, render a contact sheet and look at it, check against the
target's budget (Roblox, Unity, Unreal, three.js, USDZ, FDM or resin print), and record sources, licences and
AI-made parts in a manifest that the calling plugin reads.

From a prompt to a game prop and a print, in one session on a 16 GB GPU:

![A generated reference photo of a granite park fountain with a lion-head spout](https://raw.githubusercontent.com/m4bwav/polywright/main/.github/images/demo-fountain-ref.jpg)

![Six grey clay views of the fountain model generated from that photo: front, right, back, left, top and three-quarter](https://raw.githubusercontent.com/m4bwav/polywright/main/.github/images/demo-fountain.jpg)

Reference image (Z-Image Turbo), mesh from it (Hunyuan3D-2 through `pw.py gen`, about 100 seconds), then a
15,000-triangle Roblox GLB with UVs that passes `pw.py check --target game-roblox`, and an 80 mm watertight print
solid that Bambu Studio's CLI accepted as a 3MF.

A real place, from open data only:

![A 400 metre square of Central Park around Bethesda Terrace from above and at an angle: the lake, paths, lawns, woods and trees coloured by land use on lidar terrain](https://raw.githubusercontent.com/m4bwav/polywright/main/.github/images/demo-park.jpg)

![The same area as a grey printable tile with exaggerated relief](https://raw.githubusercontent.com/m4bwav/polywright/main/.github/images/demo-park-print.jpg)

`pw.py place --center 40.7740,-73.9712 --size-m 400 --print-mm 150 --exaggerate 2`: USGS 1 m lidar, land use,
paths, the lake (hydro-flattened), trees and buildings into `scene.glb`, and a watertight 150 mm tile. Map data
(c) OpenStreetMap contributors (ODbL); elevation USGS 3DEP (public domain).

## The skills

| Skill | Job | Tier |
|---|---|---|
| [`polywright`](skills/polywright/SKILL.md) | The hub: the brief, the route, the asset folder and manifest, the inspect-render-check loop, and `pw.py` | fast |
| [`polywright-references`](skills/polywright-references/SKILL.md) | What references to gather or generate: orthographic views, A-pose turnarounds, multi-view sets, repainted blockouts, seamless textures and quick PBR maps | fast |
| [`polywright-capture`](skills/polywright-capture/SKILL.md) | Real things and places: OSM and elevation, photogrammetry (RealityScan, COLMAP, OpenMVS), splats, scanners, measurements, scan cleanup | moderate |
| [`polywright-generate`](skills/polywright-generate/SKILL.md) | Imagined things: generators with their licences and VRAM, code modelling, procedural kits, AI texturing | fast |
| [`polywright-blender`](skills/polywright-blender/SKILL.md) | Blender 5.x from an agent: headless runs that report errors, the API traps models still write, ten tested recipes, MCP servers and their risks, tools per OS | moderate |
| [`polywright-finish`](skills/polywright-finish/SKILL.md) | Fit a mesh to its target: scale, pivots, LODs, retopology, UVs, bakes, normal-map conventions, collision, rigging, export per engine | moderate |
| [`polywright-print`](skills/polywright-print/SKILL.md) | Printable solids: watertight remesh, union, design rules, splitting, multi-colour 3MF, terrain and miniatures, slicer CLIs | moderate |

Each skill folder holds `SKILL.md` plus its evergreen companions: `RESEARCH.md` (dated findings and a four-track
search plan), `CHANGELOG.md`, `LEARNINGS.md` (lessons with a trigger and a hypothesis), `TESTS.md` with
`evals/evals.json`, `MAINTENANCE.md` and `evergreen.json` (tier, due date, history). The skills follow whichever
evergreen plugin is installed ([evergreen-protocol](https://github.com/m4bwav/evergreen-protocol)) and work
without it.

## pw.py

`skills/polywright/scripts/pw.py` is standard-library Python 3.9+. It prints one JSON object per command, so an
agent reads numbers instead of 300 lines of Blender log. It drives Blender headless through `pw_bpy.py`.

```
python pw.py doctor                                     # Blender, Python libs, slicers, ComfyUI hosts, what works
python pw.py inspect model.glb                          # tris, size, materials, UVs, watertight, parts
python pw.py render model.glb --out renders/v1          # six views and one sheet.png to look at
python pw.py check model.glb --target game-roblox --real-size-m 1.0
python pw.py convert raw.glb game.glb --size-m 1.0 --ground --center --max-tris 15000 --uv
python pw.py printable raw.glb print.stl --size-mm 80 --size-axis height
python pw.py gen --image front.png --out raw.glb        # Hunyuan3D-2 on ComfyUI; --workflow for any other
python pw.py place --center LAT,LON --size-m 400 --out place --print-mm 150
python pw.py new assets/fountain --name Fountain --kind imagined --targets game-roblox,print-fdm
```

Full list: [skills/polywright/references/cli.md](skills/polywright/references/cli.md). The contract other
plugins use (folder layout, `manifest.json`): [contract.md](skills/polywright/references/contract.md).

## Install

The skills install nothing and spend nothing on their own. Blender, ComfyUI and its model weights, hosted
generators, slicers and MCP servers are yours to install or pay for; `pw.py doctor` says what is missing.

As a Claude Code plugin:

    /plugin marketplace add m4bwav/polywright
    /plugin install polywright@polywright

As plain skills for any agent that reads Agent Skills, clone the repository and link every folder under `skills/`
into the agent's skills directory. Keep all seven together, because the siblings use the hub's `scripts/`.

    git clone https://github.com/m4bwav/polywright
    # Windows (junctions need no admin rights)
    foreach ($s in Get-ChildItem polywright\skills -Directory) { New-Item -ItemType Junction -Path "$HOME\.claude\skills\$($s.Name)" -Target $s.FullName }
    # macOS / Linux
    for s in polywright/skills/*/; do ln -s "$PWD/$s" ~/.claude/skills/; done

Needs: Python 3.9+ and Blender 4.5 or newer (5.2 LTS tested) for most commands. Optional: trimesh (3MF, and
`inspect` without Blender), numpy and Pillow (`texture`), a ComfyUI host with 3D models (`gen`).

## Verified (2026-10-11, Windows 11, Blender 5.2.1, RTX 5060 Ti 16 GB)

These come from real runs, not from a model's say-so:

- `tests/test_pw.py`: 24 tests: geometry, file formats, manifest, an offline `place`, and Blender-backed inspect,
  render, convert, printable, union and the bpy runner. They pass with the Blender executable and with the PyPI
  `bpy` 5.2.2 wheel.
- `tests/test_recipes.py`: all ten recipes in `polywright-blender` run in Blender. The test caught two 5.x API
  changes the research had missed (`show_shadows`, and the multilayer EXR media type).
- The fountain and Central Park runs above, and a 540 x 420 m neighbourhood park (249 buildings). The park run
  caught and fixed four bugs: roads outside the box, an inside-out terrain block that made the Manifold union
  drop every building silently, missing enclosing areas, and water painted over islands.

- Agent evals, headless in fresh sessions with `tests/run_evals.py`: every trigger and decoy case three times,
  80 of 87 on the first pass, and the four weak cases 24 of 24 after their fixes (2026-10-17); the print and
  capture action cases ran `pw.py` for real. Details in each skill's TESTS.md.

- TRELLIS.2 and Pixal3D through ComfyUI's own template, run as is by `pw.py gen --workflow` on the 16 GB card:
  TRELLIS.2 377 s of GPU time for an upright 699k-triangle model with 4096 px PBR textures; Pixal3D 329 s, in the
  camera's frame, stood up by `pw.py convert --level`.

Not verified yet: Blender from Linux snaps and distro packages, any hosted generator, and three runs of the
action and outcome eval cases. The [wiki](https://github.com/m4bwav/polywright/wiki) has every command
with real output.

## Testing

CI (`.github/workflows/tests.yml`):

- Linux, macOS and Windows, Python 3.9 and 3.14: `tests/check_skills.py` (frontmatter, description limits,
  companions, manifests, relative links, public-safety guards) and `tests/test_pw.py` (Blender parts skip).
- A Blender job on Linux with the `bpy` 5.2.2 wheel: the Blender tests and every recipe.
- `scripts/budget.py`: what every session loads (about 1,000 tokens of descriptions) and the installed size stay green.

## Privacy

polywright has no server and collects nothing. `pw.py` runs on your machine and only talks to the network when
you run a command that needs it:

- `place` downloads map data from public Overpass servers and elevation from the USGS 3DEP service or the
  public terrain tiles on AWS, for the area you name.
- `gen` and `doctor` talk to the ComfyUI hosts you configure (default `127.0.0.1:8188`).
- Nothing else: Blender runs locally with `--factory-startup`, and no telemetry is sent.

## If you are an agent asked to analyse this suite

Read, roughly in order: `skills/polywright/SKILL.md` (routing and the proof loop), `skills/*/SKILL.md`,
`skills/*/RESEARCH.md` (dated sources), `skills/polywright/references/targets.json` (budgets with sources), and
`tests/`. The rule running through all of it: a step counts as done when numbers and a picture show it, never on
a generator's or a script's own claim. Repository rules: [AGENTS.md](AGENTS.md).

License: MIT. Security: [SECURITY.md](SECURITY.md). The banner and the fountain reference were made with Z-Image
Turbo in ComfyUI; the banner workflow, prompt and seed are in `.github/images/`.
