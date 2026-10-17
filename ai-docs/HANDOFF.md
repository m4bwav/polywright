# Handoff

Last updated 2026-10-17 (evals harness, wall thickness, hollow-shell fill, convert --level, roofs, sibling pointers).

## State

- Seven skills under `skills/`, the CLI `skills/polywright/scripts/pw.py` (+ `pw_bpy.py`), budgets in `skills/polywright/references/targets.json`, research in `research/`.
- Tests: `python tests/check_skills.py`, `python tests/test_pw.py` (40), `python tests/test_recipes.py` (11) and `python scripts/budget.py` pass on Windows 11 with Blender 5.2.1. Budget YELLOW: installed skills folder 501 KB (green to 400, red at 800).
- github.com/m4bwav/polywright (public), CI green on main. Released v0.1.2 (2026-10-11). Everything since is under Unreleased in CHANGELOG.md: crowd, match, turnaround, mark, lineup, wall thickness in check, hollow-shell fill in printable, convert --level, roofs and building parts in place, the eval harness. A release (0.2.0 is the obvious number) waits for the owner's go-ahead; the wiki is updated with each release ([notes/2026-10-11-github-wiki.md](notes/2026-10-11-github-wiki.md)).
- Evals: `tests/run_evals.py` runs the cases headless (see its docstring). Trigger and decoy cases, three runs each: 80/87 first pass, then the four weak cases 24/24 after fixes (each TESTS.md, T-20261017-1). Cost about $0.30 to $0.50 per trigger run.
- Siblings now point at polywright's folder contract (one line each, merged 2026-10-17): threewright #9 (threewright-assets), cinewright #48 (cinewright-sets, target `video-blockout`), roblox-agent #14 (roblox-agent-workflow), unity-agent #12 (unity-agent-workflow), comfyui-gen #72 (private).

## Owed

1. Evals: the action and outcome cases three times each, and baselines without the skill (`--baseline`). Action cases run real tools: run them one skill at a time, with the GPU free, and read the traces.
2. TRELLIS.2 template's other resolutions on the 16 GB card (the GPU was busy with another session's job on 2026-10-17; never queue behind or cancel someone else's job).
3. `pw.py place`: Overture heights where OSM has none, open imagery for ground textures, per-colour 3MF output. A European old-town tile at 150 mm unions through the voxel fallback with 62 non-manifold edges, with or without roofs: find which operand Manifold rejects.
4. Linux snap and distro packages, `~/Applications` on macOS, Steam installs: Blender discovery unchecked there.
5. The private printing skill (miniatures) calls `printable`: its figures were hollow before the fill; re-run one and check walls with `check --target print-fdm`.
6. Release and wiki: ask the owner about 0.2.0; after it, update the wiki (new commands: crowd, match, turnaround, mark, lineup, level, thickness).

Related: [INDEX.md](INDEX.md)
