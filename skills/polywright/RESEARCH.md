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

### R-20261011-3 · 2026-10-11 · Testing: pw.py proven end to end
- summary: Park (249 buildings, 1 m lidar, watertight 150 mm tile) and fountain (Hunyuan3D-2 in 100 s, Roblox GLB 15k tris passing check, 80 mm watertight print, 3MF accepted by Bambu Studio CLI).
- track: testing
- sources: local runs 2026-10-11; tests/test_pw.py
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-2 · 2026-10-11 · Tooling: Existing agent 3D tools
- summary: Two Blender MCP servers (official Blender Lab 1.0.3, community mcp-for-blender 2.1.9), ShapeWright, text-to-cad, two small meshwright repos; none writes a provenance manifest. Response: polywright is the routing and verification layer and calls them.
- track: tooling
- sources: [2026-10-11-ai-agents-and-3d.md](../../ai-docs/research/2026-10-11-ai-agents-and-3d.md)
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: Route split and the agent loop
- summary: Code for dimensioned parts, generators for organic shapes; plan, act and critique as separate passes; save numbered .blend files and restart instead of long sessions.
- track: subject
- sources: [2026-10-11-ai-agents-and-3d.md](../../ai-docs/research/2026-10-11-ai-agents-and-3d.md)
- magnitude: n/a (initial)
- applied: C-20261011-1
