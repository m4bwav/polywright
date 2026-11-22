# Changelog: polywright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `C-YYYYMMDD-n · date · summary`, then `because:`, `files:` and what changed.

### C-20261121-1 · 2026-11-21 · routes.md: vinish.dev and more free model libraries
- because: user request, R-20261121-1
- files: references/routes.md (five rows, biggest-libraries line), RESEARCH.md. SKILL.md unchanged; triggers unchanged, evals not re-run.

### C-20261120-3 · 2026-11-20 · `pw.py camplan`: timed, overlapping camera moves with a framing check
- because: user request (technique-harvest paper arXiv:2610.30753 FilmFlow, verdict adopt-partly; operation names, defaults, overlap rules and smoothstep from the paper, no code released, written fresh), R-20261120-1, L-023
- files: SKILL.md (crowd section, two lines), references/cli.md, references/crowd-blockouts.md ("Camera moves"), examples/camplan.json, scripts/pw.py (cmd_camplan, load_camera_file, crowd and duel --camera-file), scripts/pw_camplan.py (new), scripts/pw_bpy.py (camtrack, camplan, camfile_set), tests/test_camplan.py
- Test on our own shot (walk 2 m in 4 s; follow + dolly in 0.72 + orbit 28 from 1 s + pedestal 0.8 from 2 s, 35 mm): 97 frames, height 0.459 to 0.573, 0 out of frame, FAIL at 0.45 +-0.12 (max error 0.126); 0.373 at 50 mm; adding Frame Subject 0.45 passes. Blender 5.2.1 keyframed camera matches the planner's projection (max uv difference below 1e-5). The old route (`crowd --move`, a static duel camera) had no timing, no combinations and no framing number. Triggers unchanged, evals not re-run.

### C-20261120-2 · 2026-11-20 · `pw.py convert` and `lods`: --clean-first, --verify, tear warning
- because: user request (technique-harvest paper arXiv:2611.20533 RemeshingAgent; written fresh from the paper's description, no code was released)
- files: scripts/pw.py, scripts/pw_bpy.py, tests/test_pw.py
- `--clean-first` welds at `--weld` (default 0.1% of the bounding diagonal) and deletes parts under `--dust` of the faces before collapse; `--verify` measures open and non-manifold edges, parts, faces within 20% of the target and a point-to-surface Chamfer against the input, walks the weld ladder 1e-3, 3e-4, 1e-4, 1e-6, 3e-3, keeps the best and exits 1 when none passes. `--drop-interior` now runs before decimation. Plain decimation prints `warnings` when open edges or parts more than double. Triggers unchanged, evals not re-run.

### C-20261120-1 · 2026-11-20 · pw.py critique: region diff against references, capped fix rounds
- because: user request (technique-harvest verdict #14, Reddit post 1x9z82z; method from blender-asset-studio, MIT, written fresh, no code copied)
- files: SKILL.md (Step 4 critique paragraph), references/cli.md, scripts/pw.py (cmd_critique, Silhouette, region_diff, png_encode), tests/test_pw.py
- New command scores every grid region of each view against its reference, ranks the worst with a hint and crop boxes, writes a diff image and keeps the rounds in a ledger that stops at the cap and names the best model to deliver. Test on our own inputs: a tower model (base plus head) as reference, `--align width`: identical model 0.0, head missing 0.125 (worst region upper centre, "missing"), head shifted 0.073 (upper right, "extra"), head thinner 0.062 (upper centre, "missing"); the old route (read sheet.png) gives no number and no region. `--align bbox` stretches a stump to the reference's square, so a missing top part shows as a proportion change instead; the output says to rerun with width or height. Triggers unchanged, evals not re-run.

Archived 2026-11-20 to save install size (full text in the repo at ai-docs/archive/polywright-changelog-2026-11-10-to-2026-11-18.md, not installed):
- C-20261118-1 · 2026-11-18 · Find route: search owned packs with AssetCat first
- C-20261117-2 · 2026-11-17 · pw.py texture prints seam_rank
- C-20261117-1 · 2026-11-17 · patch.gg row in routes.md, unverified
- C-20261114-1 · 2026-11-14 · routes.md: scatter is Geometry Nodes
- C-20261112-2 · 2026-11-12 · 3DREAL clay-to-real note in crowd-blockouts
- C-20261112-1 · 2026-11-12 · place prefers LoD2 CityGML and 1 m DGM where published
- C-20261110-1 · 2026-11-10 · harvest.json: technique-harvest targets for this unit
