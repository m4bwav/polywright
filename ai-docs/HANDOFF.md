# Handoff

Last updated 2026-10-26 (0.5.1 merged, released, archive-verified and wiki published).

## State

- Seven skills under `skills/`, the CLI `skills/polywright/scripts/pw.py` (+ `pw_bpy.py`), budgets in `skills/polywright/references/targets.json`, research in `research/`.
- Local 0.5.1 validation: `check_skills.py` passed; `test_pw.py` 69 tests passed in 254.870 s, including Blender-backed regressions; `test_recipes.py` 20 recipes passed in 40.115 s; `git diff --check` passed. Budget YELLOW: installed skills folder 768 KB (red at 800), descriptions 1,053 tokens, largest SKILL.md 3,272 tokens.
- github.com/m4bwav/polywright (public). [PR #37](https://github.com/m4bwav/polywright/pull/37) merged as 7b589304. [v0.5.1](https://github.com/m4bwav/polywright/releases/tag/v0.5.1) is live, with a green release workflow and zip. The published-zip wiki verifier exited 0 with empty stderr on 2026-10-26. The owner authorizes merging and GitHub releases after checks pass; registry publishing still needs explicit permission.
- [Wiki](https://github.com/m4bwav/polywright/wiki) published for 0.5.1, commit d2d34b150e9a7a48852b302d33f8db699264377f. Final gates: 11 pages, 0 errors; 76 outputs, 0 missing; 66 snippet commands, 0 missing; prose 0 strong/64 weak; live 11 pages and 73 anchors, no failures or broken anchors.
- The local plugin install remains blocked by another session's uncommitted changes in the shared clone. It was not switched, stashed, overwritten or updated by this follow-up.
- Evals: `tests/run_evals.py` runs the cases headless (see its docstring). Trigger and decoy cases, three runs each: 80/87 first pass, then the four weak cases 24/24 after fixes (each TESTS.md, T-20261017-1). Cost about $0.30 to $0.50 per trigger run.
- `pw.py duel` first shipped in 0.4.0; the 0.3.0 changelog section was never tagged. Plan and format: [plans/2026-10-17-pw-duel.md](plans/2026-10-17-pw-duel.md).
- Topic pages shipped in 0.2.1: finish web-threejs.md, roblox.md, unity.md; hub film-and-video.md; references images-for-3d.md; print supports-and-slicing.md. check_skills.py guards drive paths and private names.
- Siblings now point at polywright's folder contract (one line each, merged 2026-10-17): threewright #9 (threewright-assets), cinewright #48 (cinewright-sets, target `video-blockout`), roblox-agent #14 (roblox-agent-workflow), unity-agent #12 (unity-agent-workflow), and a private image-generation skill.

## Books track 7 (2026-10-22)

- Shipped in 0.4.0: `crowd --passes depth,mist` (L-012, L-013), `crowd --scatter`, `inspect --topology`, `convert --fix-winding`, MP4 through Blender, two recipe files, topology.md.
- 2026-10-25: Mist on a second shot type (a duel through crowd, <video output>/depthtest2): both controls close; the owner's blind pick of blind_s11/blind_s23 is still owed (key in depthtest2_key, record the pick with the H3 pair tool).
- Open from it: does a Line Art pass beat Canny of the clay as an edge control; the duel animation principles (crowd-blockouts.md "Open"), one at a time against the same take; a judged set to calibrate the UV spread line; Unity-side checks of FBX takes and axes.

## Round 2 books track 17 (2026-10-25)

- Shipped in 0.5.0: exact-colour crowd masks (Workbench AA and dither off, L-022), `pw.py texture --delight`, LOD switch rule in the finish references, delight and normal-map limits in polywright-references. The root CHANGELOG now places them there. Skipped this round: `pw.py lods` switch estimates, an opt-in hard-edged crowd depth (soft depth edges may suit a control model; no failing case).

## Wiki for 0.5.0 and 0.5.1 (2026-10-26)

- The wiki now describes 0.5.0 (it was at 0.2.1; 0.3.0 was never tagged, 0.4.0 got no wiki pass): [notes/2026-10-26-github-wiki.md](notes/2026-10-26-github-wiki.md), program and saved output beside it. The next wiki update reruns `notes/2026-10-26-wiki-verify.py`.
- The 0.5.1 follow-up corrects the root CHANGELOG and README findings. Crowd refusal messages restore flag dashes. Duel and inspect semantics are documented and preserved; see the follow-up section in the wiki note.
- The published 0.5.1 zip was verified and the wiki updated. Saved output: [notes/2026-10-26-wiki-verify-0.5.1.out.txt](notes/2026-10-26-wiki-verify-0.5.1.out.txt); publication and gate results are in the same wiki note.

## Next single action

Merge the documentation-only publication record. The useful round-2 follow-up is released and its wiki is published; no source fix remains from this pass. Update the local plugin only after the other session has resolved its shared-clone edits.

The hub's evergreen research check is overdue (next_due 2026-10-25); no research freshness claim was changed in this follow-up.

## Owed

1. Evals: every case has run three times (2026-10-17: triggers 80/87 then fixes 24/24; actions and outcomes 42/42 graded plus crowd 3/3 by hand). Owed: outcome cases that discriminate (baselines without polywright pass 20/21), polywright-specific questions or commands.
2. TRELLIS.2 template's other resolutions on the 16 GB card (the GPU was busy with another session's job on 2026-10-17; never queue behind or cancel someone else's job).
3. `pw.py place`: Overture heights where OSM has none, open imagery for ground textures, per-colour 3MF output. A European old-town tile at 150 mm unions through the voxel fallback with 62 non-manifold edges, with or without roofs: find which operand Manifold rejects.
4. Linux snap and distro packages, `~/Applications` on macOS, Steam installs: Blender discovery unchecked there.
5. The private printing skill (miniatures) calls `printable`: its figures were hollow before the fill; re-run one and check walls with `check --target print-fdm`.
6. Done 2026-10-17: the hollow-shell fill fix shipped in 0.2.1 and the wiki is updated for it (wiki commit 8363f76; `--hollow` workaround dropped; [notes/2026-10-17-github-wiki.md](notes/2026-10-17-github-wiki.md)).
7. `pw.py duel` next, when a film test asks for it: per-fighter and weapon masks, layout boxes, a depth-plus-Canny composite pass (one control video carrying both), rigged bodies for falls. The wiki's Commands page has `duel` since 2026-10-26.

Related: [INDEX.md](INDEX.md)

Eval harness caveat (a sibling repo's lesson, 2026-10-17): loading a plugin with `--plugin-dir` instead of the installed copy changed which skill fired in one of its trigger cases. When a polywright trigger result looks odd, re-run it against the installed copy (update the marketplace and plugin first).
