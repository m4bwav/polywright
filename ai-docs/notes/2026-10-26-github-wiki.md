---
title: GitHub wiki updated for 0.5.0 (covers 0.3.0, 0.4.0 and 0.5.0)
kind: note
date: 2026-10-26
verified: 2026-10-26
stale_after: 2027-04-26
tags: [wiki, docs, 0.3.0, 0.4.0, 0.5.0, github]
summary: "the wiki update from 0.2.1 to 0.5.0: pages changed, the extended verification program and its results, what the shipped docs get wrong (the Unreleased section holds shipped changes, 0.3.0 never tagged, stale README counts), and the update procedure"
---

# GitHub wiki for 0.5.0

## Summary

The wiki was updated in update mode with the wikiwright skill, from 0.2.1 (the last wiki pass, 2026-10-17) straight to 0.5.0: 0.3.0 was never tagged and 0.4.0 got no wiki pass. Working copy: the sibling folder `polywright.wiki` of the shared clone, branch `master`, pushed to `https://github.com/m4bwav/polywright.wiki.git`. How the wiki is built is still described in [2026-10-11-github-wiki.md](2026-10-11-github-wiki.md); use the 2026-10-26 program and output for the next update.

## Verification

[2026-10-26-wiki-verify.py](2026-10-26-wiki-verify.py) extends the 0.2.1 program and defaults to 0.5.0. It downloads `polywright-0.5.0.zip` from the release into a temp folder and runs every page command from there. New sections: `duel --check` and `--preview` on the shipped example; `inspect --topology`, `check --target web-threejs` and `convert --fix-winding` on a box with one flipped triangle (written with the release's own `pw.write_glb`); `spritecam` on a seven-entry registry (five 2x2 sprites from one camera within 0.8 px, a skewed misfit, a 3x3 hall); `sprite` on a mill scene built with `pw.py bpy`; `crowd --passes depth,mist` (plus the mist frames' PNG bit depth), `--scatter 60 --view behind`, side B options, a two-figure clash with `--gap 5 --far 40`; `framecam` and a refused `framecam`; `scene` on a scene built with `pw_scene`'s `sweep` and `ribbon`, `scene.json` abridged (ring point lists shortened by the program), an unknown preset; `texture --delight` on a lit checker; the colour count of a crowd mask frame.

`duel` prints the clip length as `"seconds"`, so its two sections keep that key unmasked (`snippet(..., keep_seconds=True)`); every other `seconds` is a timing and is masked.

Output: [2026-10-26-wiki-verify.out.txt](2026-10-26-wiki-verify.out.txt), 67 sections, LF only. Two complete runs: they differ only where the program changed between them (the duel seconds, the abridged scene.json); every other section is identical, so the seeded output is stable. Run on Windows 11, Python 3.14, Blender 5.2.1, about 10 minutes.

Against the saved 0.2.1 output, `wikiwright.py diffout` gave 8 changed sections of 40 (installed, version, check fail, check no-thickness, crowd preview, crowd bad size, turnaround unknown view, manifest review date) and 27 added.

Not run, labelled on the pages: `gen` (GPU), `place` against Overpass, full-size `crowd` and `duel` renders and anything with a video model, the sprite and scene jobs the commands were made for, `tests/run_evals.py` (spends API credit). Placeholder recipe commands carry `snippets: skip`.

Results: `check --version 0.5.0` 11 pages, 0 errors, 0 warnings; `outputs --address ''` 76 checked, 0 missing, 3 skipped; `snippets` 4 blocks, 66 commands, 0 missing, 7 skipped (every page `sh` line was also matched against the program by hand: only Development's repository test commands are not in it); everwrite `tells.py` 0 strong, 62 weak (long sentences). Repository tests at v0.5.0 (Windows 11, Blender 5.2.1): `check_skills.py` ok, `test_pw.py` 69 tests OK (280 s), `test_recipes.py` 20 recipes OK, `budget.py` YELLOW (installed skills folder 767 KB of 800; this pass adds nothing to it).

## Pages changed

_Footer, Home, Getting-Started (zip, version, needs table: commands that need nothing, Blender's FFmpeg fallback), Commands (intro; topology subsection under inspect; check outputs with the topology rows; convert pointer; texture `--delight`; crowd Mist, reserves, side B, two figures, mask colours; new sections duel, spritecam, sprite, framecam, scene; changed outputs of crowd preview, crowd bad size, turnaround unknown view, manifest review date), How-Checks-Decide (four topology rules, a Topology section, the Roblox result with its new rows), Errors-and-Edge-Cases (framecam never met, unknown scene camera, known limits in 0.5.0, changed outputs), Recipes (a horde against a line, a duel previs, a game sprite and a scene illustration from a model, flipped faces, 20 Blender recipes), Versions-and-Upgrading (rows 0.3.0 to 0.5.0, "From 0.4.0 to 0.5.0", "From 0.2.1 to 0.4.0"), The-Skills (hub and finish scope, blender recipes, the 2026-10-22 action runs), Development (layout, tests, the blender-app CI job, eval runs, the new program name), FAQ (macOS and Linux discovery is tested in CI).

## Shipped docs that are wrong (not fixed here)

1. CHANGELOG.md lists the exact-colour crowd masks, `texture --delight` and the LOD switch references under "Unreleased", but PR #34 merged before the v0.5.0 tag and all three are in the tag and in `polywright-0.5.0.zip` (`--delight` ran from the zip). They belong in the 0.5.0 section.
2. CHANGELOG.md has a "0.3.0 (2026-10-18)" section, but no v0.3.0 tag or release exists; `duel` first ships in the 0.4.0 zip. Versions and upgrading says so.
3. README: "ten tested recipes" (polywright-blender row) and "all ten recipes in polywright-blender run in Blender": there are 20 in three files since 0.4.0.
4. README "Verified": `tests/test_pw.py: 24 tests`; there are 69 test methods at v0.5.0.
5. README "Not verified yet: ... three runs of the action and outcome eval cases": T-20261017-2 ran them three times each (42 of 42), and T-20261022-1 ran two new action cases.
6. README "Testing" omits the blender-app CI job (real Blender app on macOS and Linux, install-folder discovery), and "Needs" omits ffmpeg and the Blender FFmpeg fallback.
7. The wiki's own FAQ (since 0.2.1) said install-folder discovery on macOS and Linux was untested; the blender-app job already existed in 0.2.1. Fixed on the wiki.

## Findings in 0.5.0 (not fixed here)

1. `crowd`'s size refusal names its flags without dashes since 0.4.0: "size 830x480: ..." and "frames 80: ..." where 0.2.1 wrote "--size" and "--frames". Cosmetic.
2. `duel` uses `"seconds"` for the clip length, where every other command uses it for run time; its result also lacks the `action` and `blender` fields the other Blender commands carry.
3. `inspect` reports a box with one flipped triangle as `watertight: true`, `volume` 1.0 and no `inside_out` objects; only `--topology` shows the 3 mismatched edges. Documented on the pages, possibly by design.

## Facts verified while writing (not in the README)

- `spritecam` counts only diamonds of the `--tiles` footprint ("5 of 6 2x2 ground diamonds": the 3x3 hall is ignored, the skewed tower dropped at rms 7.75 px); `camera.json` keeps every sprite's own fit; the default `render_scale` is 8.
- `sprite`'s projected `groundBase` lands within 0.7 px of the `--like` sprite's diamond.
- `framecam` reports `passed_alone` per rule and `best_at_search_edge`; on the test problem the hero's box is the binding rule (8,149 of 40,095 cameras alone).
- `scene` without `sun` in cameras.json uses azimuth 200, elevation 14; the depth range is measured over a 48x27 ray grid.
- `crowd --scatter 60` gave 42 reserves on side B and none on side A with `--view behind`.
- A crowd mask frame holds exactly three colours (black, 255,0,0 and 0,0,255).
- Mist frames are 16-bit grey PNGs.

## Update procedure

Unchanged from the 0.1.2 note, with the new file names: `python ai-docs/notes/2026-10-26-wiki-verify.py <version> > new.out.txt` (Blender on the machine), strip CRs, `wikiwright.py diffout ai-docs/notes/2026-10-26-wiki-verify.out.txt new.out.txt`, fix each changed section on its page, then `check --version`, `outputs --address ''`, `snippets`, `live`. Do not use `diffout --save` (it masks the port in `http://127.0.0.1:9`, which the Errors page shows). Pages that name the version: _Footer, Home, Getting-Started (zip name and `--version` output), Commands (intro), Versions-and-Upgrading, Errors-and-Edge-Cases ("Known limits in 0.5.0"). The manifest review date on Commands is the day the program ran.

Related: builds on [2026-10-17-github-wiki.md](2026-10-17-github-wiki.md) and [2026-10-11-github-wiki.md](2026-10-11-github-wiki.md); see also [../HANDOFF.md](../HANDOFF.md), [../log.md](../log.md).
