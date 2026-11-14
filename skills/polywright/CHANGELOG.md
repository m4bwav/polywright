# Changelog: polywright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `C-YYYYMMDD-n · date · summary`, then `because:`, `files:` and what changed.

### C-20261114-1 · 2026-11-14 · routes.md: scatter is Geometry Nodes
- because: user request (books track blender-books-2026-11-14: *Blender 3D Environment Design*)
- files: references/routes.md
- One-line pointer to polywright-blender gn-scatter and its per-instance vertex budget.

### C-20261112-2 · 2026-11-12 · 3DREAL clay-to-real note in crowd-blockouts
- because: user request (technique harvest post 1ugg4tb, GPU test 2026-11-12)
- files: references/crowd-blockouts.md (Driving the video model; Open trimmed)

### C-20261112-1 · 2026-11-12 · place prefers LoD2 CityGML and 1 m DGM where published
- because: user request (technique harvest 2026-11-12, C-20261112-C)
- files: references/cli.md (place row)
- A note only; pw.py unchanged.

### C-20261110-1 · 2026-11-10 · harvest.json: technique-harvest targets for this unit
- because: user request 2026-11-10: plugins store their own technique-harvest targets (evergreen 1.1.0 harvest.json)
- files: harvest.json (new)
- Data file only; no skill text or version changed.

### C-20261109-1 · 2026-11-09 · inspect --interior and convert --drop-interior; critique rules
- because: user request (technique harvest: exterior flood fill after StableGen's "Make Solid", re-implemented from the idea, no code copied; critique rules after blender-asset-studio, MIT)
- files: scripts/pw_bpy.py (interior_faces, drop_interior, act_inspect, act_convert), scripts/pw.py (flags), tests/test_pw.py, SKILL.md (Step 4 critique paragraph)
- A voxel flood from outside marks faces no path reaches; bmesh deletes them, keeping UVs and vertex groups. On three generated meshes (about 0.7M triangles each) it removed 7k to 117k faces in 2 to 3 s, with under 70 changed pixels per 6-view render. Sealing gaps by one cell removed visible faces, so gaps are not sealed.

### C-20261107-1 · 2026-11-07 · crowd: --stab, spears that enter bodies and figures that fall
- because: user request (spearmen should visibly stab; words alone did not move the spears)
- files: scripts/pw_bpy.py (crowd_plan_stabs, crowd_stab_spear, crowd_pose), scripts/pw.py (crowd flags), references/crowd-blockouts.md, tests/test_pw.py
- Adds no random draws, so the same seed keeps its starting layout.

### C-20261026-1 · 2026-10-26 · Restore crowd refusal flag names; document existing result semantics
- because: user request; wiki findings of 2026-10-26
- files: scripts/pw.py (cmd_crowd, VERSION), references/cli.md (result semantics), tests/test_pw.py
- Crowd refusal messages again name `--size` and `--frames`; the test runs without Blender. Duel JSON-key validation keeps bare names. Clip-duration `seconds` and edge-based `watertight` remain unchanged and have regression assertions.

### C-20261025-3 · 2026-10-25 · crowd: per-side jitter, kit, height and stagger for a horde against a line
- because: user request (a wild horde with no formation against a spear line, for a layered-passes test in a private image-generation skill)
- files: scripts/pw.py (crowd flags `--jitter-b`, `--kit-b`, `--scale-b`, `--stagger-b`), scripts/pw_bpy.py (crowd_layout per side; act_crowd builds each figure's own kit), tests/test_pw.py (test_crowd_side_b_loose_bare_and_shorter), references/crowd-blockouts.md
- Side B can be scattered, bare, shorter and staggered while side A keeps its ranks; a loose side B runs up to the line instead of halting rank by rank. The blockout height did not carry into a video model's render.
### C-20261025-2 · 2026-10-25 · Exact-colour crowd masks; texture --delight
- because: R-20261025-1, L-022
- files: scripts/pw_bpy.py (act_crowd mask pass), scripts/pw.py (cmd_texture, texture parser), references/cli.md (texture row), references/crowd-blockouts.md (mask row), tests/test_pw.py (crowd preview mask colours, texture delight)
- The mask pass turns Workbench anti-aliasing and dither off and restores both before the next frame's depth and Mist. `texture --delight` divides the photo by a blur of 1/8 its size in linear light, rescaled to the median, so a baked light gradient leaves the albedo.

Entries 2026-10-17 to 2026-10-25: [ai-docs/archive/polywright-changelog-2026-10-17-to-10-25.md](../../ai-docs/archive/polywright-changelog-2026-10-17-to-10-25.md).
Entries before 2026-10-17: [ai-docs/archive/polywright-changelog-before-2026-10-17.md](../../ai-docs/archive/polywright-changelog-before-2026-10-17.md).
