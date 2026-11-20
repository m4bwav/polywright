# polywright changelog, 2026-11-10 to 2026-11-18

Moved out of [skills/polywright/CHANGELOG.md](../../skills/polywright/CHANGELOG.md) on 2026-11-20 to keep the installed size under the 800 KB limit.

### C-20261118-1 · 2026-11-18 · Find route: search owned packs with AssetCat first
- because: user request (technique-harvest GPU test 2026-11-18, posts 1xsh4xq and 1xuksmh)
- files: references/routes.md (find)

### C-20261117-2 · 2026-11-17 · pw.py texture prints seam_rank
- because: technique-harvest post yt-B-vI6rRxfIk (Back To Code video, ideas only, no code copied), user request
- files: scripts/pw.py (cmd_texture), tests/test_pw.py
- Every texture run reports the seam rank (h, v) and warns above 90%. Triggers unchanged, evals not re-run.

### C-20261117-1 · 2026-11-17 · patch.gg row in routes.md, unverified
- because: R-20261117-1
- files: references/routes.md

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

Entries 2026-10-25 to 2026-11-09: [ai-docs/archive/polywright-changelog-2026-10-25-to-2026-11-09.md](../../ai-docs/archive/polywright-changelog-2026-10-25-to-2026-11-09.md).
Entries 2026-10-17 to 2026-10-25: [ai-docs/archive/polywright-changelog-2026-10-17-to-10-25.md](../../ai-docs/archive/polywright-changelog-2026-10-17-to-10-25.md).
Entries before 2026-10-17: [ai-docs/archive/polywright-changelog-before-2026-10-17.md](../../ai-docs/archive/polywright-changelog-before-2026-10-17.md).
