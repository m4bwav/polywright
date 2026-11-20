# Research: polywright

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Routing 3D model work for agents: brief, route choice (find, code, place, capture, generate), the asset contract and manifest, the inspect-render-check loop, pw.py. Tier `fast`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Agents waste most tokens on live screenshots and long sessions; a headless runner that returns text reports and one contact sheet is the biggest saving (3DHarnessBench, arXiv 2609.06535; MindStudio donut test, 2026-05).
- Choose the route before modelling: find (CC0 libraries, print sites), code (bpy, build123d, OpenSCAD) for anything dimensioned, place (OSM plus elevation) for real sites, capture for real objects, generate for organic one-offs.
- Feeding tracebacks back fixes crashes (0.70 to 0.97 executable in 3DCodeBench, arXiv 2606.01057) but not shape; shape needs measurements and a visual critique against references.
- Stores and print sites require AI disclosure (Fab, Sketchfab, Unity Asset Store, Steam since January 2026, MakerWorld since February 2026); no other agent tool found writes a provenance manifest.
- pw.py verified on Windows 11 with Blender 5.2.1 on 2026-10-11: 20 unit and Blender tests, a real park (place), a generated fountain (gen, convert, printable, check, 3mf).

## Open questions

- Does pw.py's Blender discovery work on macOS and Linux installs (only Windows verified)?
- Should pw.py use the official Blender Lab MCP's docs search when it is installed?
- Is the 50k Unity prop budget in targets.json a sensible default?

## Search plan

Subject:

- Blender release notes (blender.org/download/releases) for operator and API changes
- glTF and Khronos 3D Commerce guideline changes

Tooling:

- `path:SKILL.md blender` and `path:SKILL.md "3d model"` on GitHub; skills.sh search `3d`, `blender`, `cad`
- registry.modelcontextprotocol.io/v0/servers?search=blender and ?search=3d
- ShapeWright, text-to-cad, meshwright repos: releases and READMEs

Practice:

- HN Algolia `blender agent`, `ai 3d model`; r/blender and r/aigamedev RSS (slow, one request a minute)
- store AI-disclosure policy pages (Fab, Sketchfab, Unity, Steam, MakerWorld, Printables)

Testing:

- new agentic 3D benchmarks on arXiv (`blender agent benchmark`, `3D code generation benchmark`)
- this repository's tests/test_pw.py and tests/test_recipes.py

Best sources: project repositories' releases and READMEs, official docs, dated practitioner posts. Noisy: vendor SEO comparison pages (mark them third party).

## Findings log

### R-20261120-1 · 2026-11-20 · Subject: camera operation plans (FilmFlow)
- FilmFlow (https://arxiv.org/abs/2610.30753, CC BY 4.0, no code): a shot is a JSON list of 22 camera operations with overlapping intervals; translations add, angles add (aim, pan, tilt, roll), radius and focal ratios multiply, orbit and dolly before truck and pedestal, smoothstep easing; defaults dolly 0.72/1.35, orbit 28, pan 20, tilt 15, zoom 50 mm, frame subject 0.65. Ablations: sequential-only and no critic each cost about 0.05 probe score; no framing metric in the paper. applied: `pw.py camplan` with our geometric framing check in place of the VLM critic. magnitude: minor

### R-20261117-1 · 2026-11-17 · Testing: VibePrevisBench and an asset aggregator
- VibePrevisBench (https://arxiv.org/abs/2611.15789): 242 previs tasks in Blender, checked against hidden scene facts and a VLM screen check; agents look at their renders but fail to fix errors. Fact-list rule added to polywright-blender Step 4. Running the benchmark needs Docker and paid VLM calls: not run. m 0.5.
- patch.gg toolbox (https://www.reddit.com/r/aigamedev/comments/1xt0uwn/): vendor claim of ~50k aggregated assets with CLI/MCP search; licences per source store, sign-in to download. Added to routes.md as unverified. applied: routes.md row.

### R-20261115-1 · 2026-11-15 · Blender 5.3 and point releases
- Blender 5.3 released 2026-11-10 (not LTS; Vulkan default on Windows). pw.py verified on 5.2.1 only; re-run Blender tests on 5.3 before claiming it. Track: subject. Sources: https://developer.blender.org/docs/release_notes/5.3/core/ . m 0.3. applied: none (5.2 LTS stays the pinned default; 5.3 test run owed).

### R-20261109-1 · 2026-11-09 · Tooling: Review renders on the game ground (open question)
- sources: [2026-11-09-technique-harvest.md](../../ai-docs/research/2026-11-09-technique-harvest.md)
- magnitude: minor

Archived 2026-11-20 to save install size (full text in the repo at ai-docs/archive/research-findings-2026-10.md, not installed):
- R-20261030-1 · 2026-10-30 · Quiet check (refresh since 2026-10-11)
- R-20261025-1 · 2026-10-25 · Subject: rendering principles for blockout passes and photo textures (round 2 books track)
- R-20261017-1 · 2026-10-17 · Subject: building models and blockouts for film and AI video
- R-20261013-1 · 2026-10-13 · Subject: Crowds and battles: Blender blockout drives the video model
- R-20261011-3 · 2026-10-11 · Testing: pw.py proven end to end
- R-20261011-2 · 2026-10-11 · Tooling: Existing agent 3D tools
- R-20261011-1 · 2026-10-11 · Subject: Route split and the agent loop

