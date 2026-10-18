---
title: GitHub wiki updated for 0.2.0 and 0.2.1
kind: note
date: 2026-10-17
verified: 2026-10-17
stale_after: 2027-04-17
tags: [wiki, docs, 0.2.0, 0.2.1, github]
summary: "the wiki update for release 0.2.0: pages changed, the extended verification program and its results, the printable regression it found (terrain sheets need --hollow), and the update procedure (unchanged from the 0.1.2 note); then the 0.2.1 update, which confirmed the fix"
---

# GitHub wiki for 0.2.0

## Summary

The wiki was updated in update mode with the wikiwright skill. Wiki commit aa2bf87, pushed to `https://github.com/m4bwav/polywright.wiki.git` (working copy: the sibling folder `polywright.wiki`, branch `master`). How the wiki is built and updated is still described in [2026-10-11-github-wiki.md](2026-10-11-github-wiki.md); this note records what changed. Use the 2026-10-17 program and output for the next update.

## Verification

[2026-10-17-wiki-verify.py](2026-10-17-wiki-verify.py) extends the 0.1.2 program with the 0.2.0 commands that run offline in seconds. It writes its own small binary STL test meshes, so it needs nothing from the repository. New sections: check with wall thickness (a 20 mm block, the block plus a 0.5 mm fin, `--no-thickness`), printable's hollow-shell fill on a 20 mm box of 0.3 mm walls (filled and `--hollow`), convert `--level` and `--tilt-deg` on a 1 x 1 x 2 m box tilted 20 degrees, place with roof shapes, `min_height` and `building:part` areas (the fixture extract plus six ways), crowd `--preview` at 320x192 and a refused size, turnaround and an unknown view, mark, lineup `--preview`, match with `--still`, manifest `--review`, bpy options after the script name. Its output, [2026-10-17-wiki-verify.out.txt](2026-10-17-wiki-verify.out.txt), has 40 sections; two runs gave identical output (seeded sampling). It ran against the published `polywright-0.2.0.zip` on Windows 11, Python 3.14.6, Blender 5.2.1, numpy 2.5.2, Pillow 12.3.0, trimesh 5.1.0, ffmpeg 9.0.1, in about 3 minutes.

Not run, labelled on the pages as from the development log: `gen` (GPU), `place` against Overpass, `crowd` at full size and with a video model, levelling the Pixal3D fountain, the TRELLIS.2 figure filled by `printable`, `tests/run_evals.py` (spends API credit).

Results: `wikiwright.py check --version 0.2.0`: 11 pages, 0 errors. `outputs --address ''`: 51 checked, 0 missing, 3 skipped. `snippets`: 2 blocks, 48 commands, 0 missing, 4 skipped (commands that need a GPU or API credit). everwrite `tells.py`: 0 strong, 30 weak (long sentences). `live m4bwav/polywright`: 11 pages, 0 failures, sidebar and footer render, anchors 37 links, 0 broken. Repository tests at 0.2.0: `check_skills.py` ok, `test_pw.py` 40 tests, `test_recipes.py` 11 recipes, all pass.

Save the output with LF line endings only (strip the CRs Windows writes). Do not use `diffout --save`: it masks the port in `http://127.0.0.1:9`, which the Errors page shows.

## Pages changed

_Footer, Home, Getting-Started (zip, version, needs table with ffmpeg), Commands (rebuilt from the output: every block, plus crowd, turnaround, mark, lineup, match and the new options), How-Checks-Decide (wall thickness section, `min_feature` row), Errors-and-Edge-Cases (the regression below, crowd size, unknown view, known limits in 0.2.0), Recipes (levelling Pixal3D output, a printable figure from image-to-3D, an army blockout for AI video, eleven bpy recipes), Versions-and-Upgrading (0.2.0 row, "From 0.1.2 to 0.2.0"), The-Skills (the 2026-10-17 eval run, changed descriptions), Development (`tests/run_evals.py`), FAQ, The-Asset-Contract (`reviews` has a date).

## Bug found in 0.2.0 (not fixed here)

1. `printable` regression on open surfaces. `pw.py printable park/roblox.glb park/solid.stl --size-mm 60 --wall-mm 1.2` (the park scene from `place` on `tests/fixtures/osm-small.json`, `--dem flat --res 2`, then `convert --join --uv --max-tris 5000`) gave in 0.1.2 a watertight solid of 4,610 triangles and 2.28 cm3. In 0.2.0 the new hollow-shell fill runs ("hollow shell: filled 2935 mm3 the outside cannot reach (seal 1.00 mm, 0.114 mm cells)"), the planar dissolve is then refused ("planar dissolve not kept (it broke the solid)"), and the result has 393,549 triangles, 2 boundary edges, 1 non-manifold edge, `volume_cm3` 0.0, `watertight` false, exit 1 (with `"ok": true` in the JSON). With `--hollow` the output is identical to 0.1.2. The 2,935 mm3 "cavity" is about the volume of the solidified sheet itself. `test_printable_flat_open_surface` (a 4 x 4 sheet) still passes, so the regression test does not cover this case. Reproduce with the verification program's sections `printable terrain default fill` and `printable`.
2. Smaller: `check --no-thickness` prints "not measured (needs Blender)" when Blender was found; the row text does not tell the two cases apart.

## Facts verified while writing (not in the README)

- The wall-thickness pass uses at most four sample points per triangle (`min(samples, 4 x triangles)`): a 12-triangle block gets 48 points, the park tile 18,440.
- `thinnest` and `p05` are `null` when no ray finds an exit within four times the minimum.
- The park tile that passed `check --target print-fdm` in 0.1.2 now warns: 96% of its surface is thinner than 0.9 mm.
- `place` with a tower `building:part` (`min_height` 4) made the print's union fall back to EXACT plus a voxel pass (451,640 triangles, watertight).
- `turnaround` with an unknown view fails inside Blender and returns the traceback (exit 1).
- `crowd` reports `render_seconds`; the program masks it with the other timings.

## Update for 0.2.1 (2026-10-17)

Wiki commit 8363f76. The program now defaults to 0.2.1, runs the park's `printable` without `--hollow` (section `printable`) and keeps the `--hollow` run as section `printable terrain --hollow` (it replaced `printable terrain default fill`); its saved output was overwritten (41 sections, LF only). Against 0.2.1 the old program's diffout gave 8 changed sections of 40: installed, version, check fail (new Roblox advice lines from targets.json), printable terrain default fill (now 4,610 triangles, watertight, 2.28 cm3, exit 0: bug 1 above is fixed), check no-thickness ("skipped (--no-thickness)": bug 2 fixed), printable hollow shell (fill reads 7003 mm3, was 7076; same volume), turnaround unknown view (pw_bpy.py line numbers), lineup (the `next` hint no longer cites a private lesson). With and without `--hollow` the park gives byte-identical output.

Pages changed: _Footer, Home, Getting-Started, Commands, Errors-and-Edge-Cases (the regression section is now "A terrain sheet in 0.2.0 (fixed in 0.2.1)", known limits in 0.2.1), How-Checks-Decide (Roblox advice), Recipes, The-Skills (table of the six reference pages added in 0.2.1), Versions-and-Upgrading (0.2.1 row, "From 0.2.0 to 0.2.1").

Results: `check --version 0.2.1` 11 pages, 0 errors; `outputs --address ''` 50 checked, 0 missing, 3 skipped; `snippets` 2 blocks, 48 commands, 0 missing, 4 skipped; `tells.py` 0 strong; `live` 11 pages, 0 failures, anchors 39 links, 0 broken. No new bug found.

Related: builds on [2026-10-11-github-wiki.md](2026-10-11-github-wiki.md); see also [../HANDOFF.md](../HANDOFF.md), [../log.md](../log.md).
