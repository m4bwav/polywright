# Changelog: polywright-blender

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261022-1 · 2026-10-22 · 2.7x-era traps, two recipe files, bake and output rules
- because: books track 7 (Conlan, *The Blender Python API*; Packt Geometry Nodes; Pearson, *Learn Blender Simulations the Right Way*; van Gumster, *Blender All-in-One For Dummies*; Simonds, *Blender Master Class*; *Blender 3D By Example*; Brito); L-007, L-008
- files: references/bpy-api-traps.md (new section "Code from 2.7x-era books and tutorials"), references/bpy-recipes-scenes.md (new: gn-scatter, passes-one-render, clay-override, line-art, encode-mp4), references/bpy-recipes-physics.md (new: rigidbody-bake, cloth-bake, rigify-export, volume-remesh), SKILL.md (Depth links, Step 2 bake rule, Step 3 two rows, Step 4), tests/test_recipes.py (reads every bpy-recipes*.md)
- Sixteen trap rows probed on 5.2.1, among them `transform_apply(scale=True)` also applying location (the rigid-body recipe's box fell through the floor until it was fixed). Nine new recipes, each asserting its own result; three mutation-checked. 20 recipes pass. The recipes were split in two files so neither crosses the 3,500-token reference line.

### C-20261017-2 · 2026-10-17 · Private names and machine paths generalised
- because: user request (public repository: no private project names, no person's name but the author credit, no machine paths; AGENTS.md)
- files: LEARNINGS.md L-003 to L-006; CHANGELOG.md C-20261012-1; TESTS.md
- A film's name, its prop file names and a machine path became generic; the lessons are unchanged.

### C-20261017-1 · 2026-10-17 · Description names the removed OBJ importer
- because: T-20261017-1 (trigger-1 1/3: the bpy AttributeError was answered from memory)
- files: SKILL.md frontmatter description
- "any bpy traceback or AttributeError" now adds "(import_scene.obj and other removed operators)".

### C-20261012-1 · 2026-10-12 · Prop-from-description recipe; absolute output paths; options after the script
- because: L-003, L-004, L-005, L-006 (a film's spear, built and revised headless through six owner notes)
- files: SKILL.md Step 2 and Step 4; references/bpy-recipes.md "A designed prop from a written description"; LEARNINGS.md
- New tested recipe `prop-from-description`; Step 2 says pw.py options may follow the script (pw.py fix) and outputs must be absolute paths; Step 4 points at the recipe and the raised side view for paired parts.

### C-20261011-2 · 2026-10-11 · Description says when to fire
- because: T-20261011-2 first pass (undertriggering: prompts answered without the skill; hub and finish both claimed game-readiness)
- files: SKILL.md frontmatter description
- Descriptions open with 'Use whenever ...' and name the requests each skill owns; the hub only takes requests no sibling owns.

### C-20261011-1 · 2026-10-11 · Created as an evergreen unit
- because: user request (an evergreen 3D modelling plugin); research R-20261011-1 to R-20261011-2
- files: SKILL.md, references/, RESEARCH.md, LEARNINGS.md, TESTS.md, evals/evals.json, evergreen.json
- Initial version, tier `moderate`, interval 30d, written from the five research notes of 2026-10-11 and the verified runs logged in LEARNINGS.md.
