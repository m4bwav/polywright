# Changelog: polywright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `C-YYYYMMDD-n · date · summary`, then `because:`, `files:` and what changed.

### C-20261120-2 · 2026-11-20 · `pw.py convert` and `lods`: --clean-first, --verify, tear warning
- because: user request (technique-harvest paper arXiv:2611.20533 RemeshingAgent; written fresh from the paper's description, no code was released)
- files: scripts/pw.py, scripts/pw_bpy.py, tests/test_pw.py
- `--clean-first` welds at `--weld` (default 0.1% of the bounding diagonal) and deletes parts under `--dust` of the faces before collapse; `--verify` measures open and non-manifold edges, parts, faces within 20% of the target and a point-to-surface Chamfer against the input, walks the weld ladder 1e-3, 3e-4, 1e-4, 1e-6, 3e-3, keeps the best and exits 1 when none passes. `--drop-interior` now runs before decimation. Plain decimation prints `warnings` when open edges or parts more than double. Triggers unchanged, evals not re-run.

### C-20261120-1 · 2026-11-20 · pw.py critique: region diff against references, capped fix rounds
- because: user request (technique-harvest verdict #14, Reddit post 1x9z82z; method from blender-asset-studio, MIT, written fresh, no code copied)
- files: SKILL.md (Step 4 critique paragraph), references/cli.md, scripts/pw.py (cmd_critique, Silhouette, region_diff, png_encode), tests/test_pw.py
- New command scores every grid region of each view against its reference, ranks the worst with a hint and crop boxes, writes a diff image and keeps the rounds in a ledger that stops at the cap and names the best model to deliver. Test on our own inputs: a tower model (base plus head) as reference, `--align width`: identical model 0.0, head missing 0.125 (worst region upper centre, "missing"), head shifted 0.073 (upper right, "extra"), head thinner 0.062 (upper centre, "missing"); the old route (read sheet.png) gives no number and no region. `--align bbox` stretches a stump to the reference's square, so a missing top part shows as a proportion change instead; the output says to rerun with width or height. Triggers unchanged, evals not re-run.

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
