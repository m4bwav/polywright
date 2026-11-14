# Research: polywright-blender

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md. The full research notes of the first pass are in the repository's [ai-docs/research](../../ai-docs/research/index.md).

Topic: Driving Blender 5.x from agents: headless runs, API traps, tested recipes, MCP bridges, other 3D tools per OS. Tier `moderate`. Last refresh 2026-10-11; next due per `evergreen.json`.

## Current understanding

- Blender 5.2 LTS (2026-07-14, supported to July 2028); 5.3 reported for 2026-11-10.
- A Python error inside `blender --background --python` exits 0 unless --python-exit-code is given (verified 2026-10-11).
- 5.x traps: wm.* importers, no Collada, BLENDER_EEVEE, no bgl, renamed Principled sockets, slotted actions, Geometry Nodes inputs through mod.properties.inputs, show_shadows, multilayer EXR through media_type.
- Two MCP servers (official Blender Lab 1.0.3, community mcp-for-blender 2.1.9) both run unsandboxed code on port 9876.
- Ten recipes in references/bpy-recipes.md pass in Blender 5.2.1 (tests/test_recipes.py, 2026-10-11).

## Open questions

- Which official Blender Lab MCP tools have _for_cli variants usable headless?
- Does pw.py's discovery find Blender on macOS (/Applications) and Linux (snap, tarball)?
- Can CI run Blender tests through the bpy wheel on Python 3.13?

## Search plan

Subject:

- blender.org/download/releases/5-3 and later: Python API changes
- developer.blender.org release notes (behind a browser check: use search snippets plus local probes)

Tooling:

- mcp-for-blender and Blender Lab MCP releases
- `path:SKILL.md bpy` on GitHub; skills.sh `blender`

Practice:

- Blender Artists and Blender Stack Exchange on LLM scripts; HN `blender mcp`

Testing:

- tests/test_recipes.py on each new Blender LTS

Best sources: project repositories' releases and READMEs, official docs, dated practitioner posts. Noisy: vendor SEO comparison pages (mark them third party).

## Findings log

### R-20261114-1 · 2026-11-14 · Subject: two Blender modelling books, checked on 5.2.1
- summary: Array (Fit Curve) before Curve repeats a unit along a path; the Bevel shader node baked as Emit in Cycles gives an edge mask (needs flat shading); `ShaderNodeTexSky` exists with SINGLE_SCATTERING, MULTIPLE_SCATTERING, PREETHAM, HOSEK_WILKIE and `sun_disc`. The double-light warning (sky sun plus a lamp) and cutter normals before a boolean are book rules, unverified here.
- track: subject
- sources: *Blender 3D Environment Design*; Belec, *Blender: Create Incredible Models*; probe scripts in Blender 5.2.1 LTS, 2026-11-14
- magnitude: minor

### R-20261102-1 · 2026-11-02 · Subject: scripting habits from Acampora, probed on 5.2.1
- summary: Context and selection rules, parenting inverse, channelbag key reads (`anim_utils.action_get_channelbag_for_slot` exists and equals `layers[0].strips[0].channelbag(slot)`), `keyframe_insert` returns a bool, F-modifier and driver-variable enums, `driver.is_simple_expression`, auto-exec off by default, `object.delete(confirm=)`. Book written for Blender 3.3; every API claim re-probed in a running 5.2.1.
- track: subject
- sources: Acampora, *Python Scripting in Blender* (Packt, 2023); probe script run in Blender 5.2.1 LTS, 2026-11-02
- magnitude: minor

### R-20261011-2 · 2026-10-11 · Tooling: MCP bridges and per-OS tools
- summary: Official and community MCP compared; per-OS table of 30 tools with versions.
- track: tooling
- sources: [2026-10-11-blender-and-tooling.md](../../ai-docs/research/2026-10-11-blender-and-tooling.md)
- magnitude: n/a (initial)
- applied: C-20261011-1

### R-20261011-1 · 2026-10-11 · Subject: Blender 5.2 API facts probed locally
- summary: Operator presence, enums, Principled sockets, Geometry Nodes inputs, headless render times.
- track: subject
- sources: [2026-10-11-blender-and-tooling.md](../../ai-docs/research/2026-10-11-blender-and-tooling.md)
- magnitude: n/a (initial)
- applied: C-20261011-1
