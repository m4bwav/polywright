# Handoff

Last updated 2026-10-17 (pw.py duel; evals harness, wall thickness, hollow-shell fill, convert --level, roofs, sibling pointers).

## State

- Seven skills under `skills/`, the CLI `skills/polywright/scripts/pw.py` (+ `pw_bpy.py`), budgets in `skills/polywright/references/targets.json`, research in `research/`.
- Tests: `python tests/check_skills.py`, `python tests/test_pw.py` (49), `python tests/test_recipes.py` (11) and `python scripts/budget.py` pass on Windows 11 with Blender 5.2.1. Budget YELLOW: installed skills folder 566 KB after the six topic pages of 2026-10-17 (green to 400, red at 800).
- github.com/m4bwav/polywright (public), CI green on main. Released v0.2.1 (2026-10-17; 0.2.0 the same day). Under Unreleased in CHANGELOG.md: `pw.py duel`. A release waits for the owner's go-ahead; the wiki is updated with each release ([notes/2026-10-11-github-wiki.md](notes/2026-10-11-github-wiki.md)).
- Evals: `tests/run_evals.py` runs the cases headless (see its docstring). Trigger and decoy cases, three runs each: 80/87 first pass, then the four weak cases 24/24 after fixes (each TESTS.md, T-20261017-1). Cost about $0.30 to $0.50 per trigger run.
- `pw.py duel` (2026-10-17, unreleased): two-fighter previs controls; plan, format and result in [plans/2026-10-17-pw-duel.md](plans/2026-10-17-pw-duel.md). Budget after it: installed skills folder 600 KB (YELLOW), hub SKILL.md 2,499 tokens (green, one token under).
- Topic pages (2026-10-17, unreleased): finish web-threejs.md, roblox.md, unity.md; hub film-and-video.md; references images-for-3d.md; print supports-and-slicing.md. check_skills.py guards drive paths and private names.
- Siblings now point at polywright's folder contract (one line each, merged 2026-10-17): threewright #9 (threewright-assets), cinewright #48 (cinewright-sets, target `video-blockout`), roblox-agent #14 (roblox-agent-workflow), unity-agent #12 (unity-agent-workflow), and a private image-generation skill.

## Owed

1. Evals: every case has run three times (2026-10-17: triggers 80/87 then fixes 24/24; actions and outcomes 42/42 graded plus crowd 3/3 by hand). Owed: outcome cases that discriminate (baselines without polywright pass 20/21), polywright-specific questions or commands.
2. TRELLIS.2 template's other resolutions on the 16 GB card (the GPU was busy with another session's job on 2026-10-17; never queue behind or cancel someone else's job).
3. `pw.py place`: Overture heights where OSM has none, open imagery for ground textures, per-colour 3MF output. A European old-town tile at 150 mm unions through the voxel fallback with 62 non-manifold edges, with or without roofs: find which operand Manifold rejects.
4. Linux snap and distro packages, `~/Applications` on macOS, Steam installs: Blender discovery unchecked there.
5. The private printing skill (miniatures) calls `printable`: its figures were hollow before the fill; re-run one and check walls with `check --target print-fdm`.
6. Done 2026-10-17: the hollow-shell fill fix shipped in 0.2.1 and the wiki is updated for it (wiki commit 8363f76; `--hollow` workaround dropped; [notes/2026-10-17-github-wiki.md](notes/2026-10-17-github-wiki.md)).
7. `pw.py duel` next, when a film test asks for it: per-fighter and weapon masks, layout boxes, a depth-plus-Canny composite pass (one control video carrying both), rigged bodies for falls. The wiki's Commands page gets `duel` at the next release.

Related: [INDEX.md](INDEX.md)

Eval harness caveat (a sibling repo's lesson, 2026-10-17): loading a plugin with `--plugin-dir` instead of the installed copy changed which skill fired in one of its trigger cases. When a polywright trigger result looks odd, re-run it against the installed copy (update the marketplace and plugin first).
