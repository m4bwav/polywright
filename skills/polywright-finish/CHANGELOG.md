# Changelog: polywright-finish

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261017-3 · 2026-10-17 · references/unity.md: making and finishing models for Unity
- because: user request (each plugin carries 3D modelling knowledge for its topic and points to polywright); R-20261017-3
- files: references/unity.md (new); SKILL.md intro (pointer to the three engine pages); references/engines.md Unity (link, LOD siblings in one FBX)
- Format choice, Blender export settings (FBX Units Scale as pw.py writes it, proven by a 1 m cube), LODs and Mesh LOD, lightmap UVs, collision proxies, URP and HDRP texture sets, Humanoid rigs.

### C-20261017-2 · 2026-10-17 · references/roblox.md: making and finishing models for Roblox; accessory budget verified
- because: user request (each plugin carries 3D modelling knowledge for its topic and points to polywright); R-20261017-2
- files: references/roblox.md (new); SKILL.md intro (pointer); references/engines.md budget table (rigid and layered accessories 4,000 triangles [verified]) and Roblox (link); RESEARCH.md current understanding and open questions
- Styles, the 20k limit and splitting, the PBR set and texture sizes, studs or the Importer's Scale Unit, collision blockers, R15 rigs and layered-clothing cages, verification in Studio; two open questions closed.

### C-20261017-1 · 2026-10-17 · references/web-threejs.md: making and finishing models for the web
- because: user request (each plugin carries 3D modelling knowledge for its topic and points to polywright); R-20261017-1
- files: references/web-threejs.md (new); SKILL.md intro (pointer) and Step 6 web-threejs row (`--join-named false`); references/engines.md three.js (link)
- What the web punishes (download, draw calls, texture memory), topology, UVs and packing, baking, Blender glTF export, meshopt and KTX2 compression with gltf-transform or gltfpack, checks in a web viewer.

### C-20261011-2 · 2026-10-11 · Description says when to fire
- because: T-20261011-2 first pass (undertriggering: prompts answered without the skill; hub and finish both claimed game-readiness)
- files: SKILL.md frontmatter description
- Descriptions open with 'Use whenever ...' and name the requests each skill owns; the hub only takes requests no sibling owns.

### C-20261011-1 · 2026-10-11 · Created as an evergreen unit
- because: user request (an evergreen 3D modelling plugin); research R-20261011-1 to R-20261011-2
- files: SKILL.md, references/, RESEARCH.md, LEARNINGS.md, TESTS.md, evals/evals.json, evergreen.json
- Initial version, tier `moderate`, interval 30d, written from the five research notes of 2026-10-11 and the verified runs logged in LEARNINGS.md.
