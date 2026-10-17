# Log

Append-only. Newest last.

## 2026-10-11

- Owner's request: an evergreen "ultimate 3D modelling" plugin that agents and other plugins call when they need a model of a real or imagined thing, for games, prints, AI video and business use; research forums, AI practice, academics, the latest and the time-honoured; Blender tooling; push the repo and do the modernisation steps.
- Five research agents wrote ai-docs/research (reality capture, generative 3D, Blender and tooling, craft and academics, AI agents and 3D). Originals with machine specifics are kept in the owner's private notes; the repository copies are generalised.
- Named the plugin polywright ("meshwright" is taken by two 3D projects). Design: decisions/2026-10-11-hub-and-contract.md.
- Built pw.py and pw_bpy.py, seven skills, references, companions and evals; tests (22 unit and Blender tests, ten recipes) pass with Blender 5.2.1 and with the bpy 5.2.2 wheel on Python 3.13.
- Proven end to end: a neighbourhood park and Central Park's Bethesda Terrace through `place` (bugs found and fixed: unclipped ways, inside-out terrain block dropped by the Manifold union, enclosing areas missing from box queries, multipolygon stitching, water over islands, lidar noise on water); a generated fountain (Z-Image reference, Hunyuan3D-2 mesh in 100 s, Roblox GLB passing check after UVs, watertight 80 mm print, 3MF accepted by Bambu Studio's CLI).
- Recipe tests caught two Blender 5.x changes the research missed: Workbench `show_shadows`, and multilayer EXR needing `media_type` first.
- Pushed to github.com/m4bwav/polywright (public). CI: structure on three OS x Python 3.9/3.14, a Blender job with the bpy 5.2.2 wheel (needed Mesa EGL: PR #1), and the budget; all green. Registered the seven units in the evergreen catalog; installed polywright@mark-local.
- Headless trigger evals (`claude -p`, fresh sessions, Skill calls as evidence): 17/28, then 23/28 after explicit descriptions (0.1.1); every decoy passed both times. On Windows, Python's subprocess needs the full path to `claude.cmd` (shutil.which); a bare "claude" fails with WinError 2 and looks like zero invocations.
- Action evals in a throwaway clone: print passed and found the flat-face tessellation problem (fixed with a guarded planar dissolve); capture ran pw.py correctly without loading the skill because the prompt named the command (prompt rewritten).
- Not tagged: tagging and publishing a release wait for the owner's go-ahead.

## 2026-10-11 (release, TRELLIS.2, wiki)

- Owner approved: release v0.1.1, download the TRELLIS.2 models, and saved the wiki's first page. Released v0.1.1, then v0.1.2.
- The wiki's verification run against the published 0.1.1 found `--version` printing 0.1.0, `printable` crushing open flat surfaces (base clamp before re-grounding), and a ten-minute planar dissolve; fixed in 0.1.2 (PR #3) with a regression test and a VERSION check.
- Downloaded the seven TRELLIS.2/Pixal3D template files (14.5 GB) into the local ComfyUI. The browser could not reach the local ComfyUI, and ComfyUI has no conversion endpoint, so pw.py gained `ui_to_api` (PR #4): the unmodified template ran. GPU times: TRELLIS.2 377 s (upright, best detail), Pixal3D 329 s (camera frame, tilted), Hunyuan3D-2 99 s. Another session's video job held the GPU queue for about 25 minutes; it was left alone.
- Wiki: 11 pages, all outputs from the verification program against 0.1.2, gates clean, live check clean (notes/2026-10-11-github-wiki.md).


## 2026-10-11 (Blender on macOS and Linux)

- Owner did not want to install Blender on the Mac by hand. The Mac refuses SSH (port 22), so macOS was tested on GitHub's macOS runner instead (public repo, free): new CI job `blender-app` installs the Homebrew cask and the Linux tarball, runs `tests/check_discovery.py` (the install-folder search must find it with PATH and env vars ignored for the decision) and `tests/test_pw.py`. Both green: macOS found `/Applications/Blender.app/Contents/MacOS/Blender` (5.2.1), 24 tests in 186 s including render; Linux found `~/blender-5.2.2-linux-x64/blender`.
- Also run locally in WSL (Ubuntu 26.04): Blender 5.2.2 tarball unpacked in `~`, discovery, test_pw.py (24) and test_recipes.py (10) pass.
- download.blender.org answers 403 to curl from the home PC (with or without a browser user agent); the official mirror https://mirrors.ocf.berkeley.edu/blender/release/ works. The CI step tries blender.org first and falls back to that mirror.

## 2026-10-13: pw.py crowd (army blockouts for AI video)

- New `pw.py crowd`: two armies of low-poly soldiers with offset walk cycles, rendered per frame to inverse depth (one range per shot), a side mask, clay and OpenPose skeletons; one mp4 per pass, camera.json, joints.json, sheet.png. Reason: video models fail at crowds; the owner wants Blender to carry the crowd and the model to paint it. Research: cinewright ai-docs/research/2026-10-13-battle-crowd-compositing.md.
- Verified: 240 figures, 81 frames, four passes at 832x480 in 81 s on the CPU (Blender 5.2.1, Windows 11). The depth video drove MiniMax H3 through Fun ControlNet Union 2.0 on a 16 GB card (608x352, 56 frames, 27 to 36 s): formation, direction and timing followed the blockout. Wan VACE untested.
- Defaults were derived, not fixed, after three bad previews (polywright LEARNINGS L-004): camera distance from reach and lens, depth range from nearest ground to farthest figure over the whole shot, clash gap from both sides' speed.
- Checks: tests/test_pw.py 28 OK (two new crowd tests), check_skills ok, budget YELLOW: installed skills folder 380 to 418 KB (green to 400), all from the new code.

## 2026-10-16: pose passes leave out hidden face points; two-fighter previs recipe

The owner asked to update polywright with whatever helps, after a study of driving a duel's video from a 3D blockout (cinewright research note 2026-10-16-fight-3d-route). A two-fighter previs built from the crowd mannequins found that the crowd pose pass draws a nose and eyes on figures seen from behind, which tells a pose control the figure faces the camera. Fixed: `hidden_face_points` in pw_bpy.py (nose and eyes once turned away, an ear behind the head), joints written as (-1, -1), skipped by `draw_pose_frames`. The new test also found `--passes pose` alone failing for want of its output folder; fixed. Reference "Two fighters (previs)" in crowd-blockouts.md, lesson L-005. `pw.py duel` stays unbuilt until the first H3 test with figures in the control shows it pays.

## 2026-10-16: real figures as video references (turnaround, mark, lineup)

A run that turned four photographed toy figures and five accessories into TRELLIS.2 meshes for an AI video found three gaps, now commands: `pw.py turnaround` (grey eye-level reference pictures from a textured mesh), `pw.py mark` (generated textures drift in colour and smear painted letters and numbers: recolour to the photo's measured medians, erase the smear on the head's front UV islands, stand a text mesh on the face, real size) and `pw.py lineup` (figures on a table with teams on fixed sides: colour, clay, inverse depth, team mask, looped control videos). `manifest` gained `--review` and resolves a relative `--add-output` inside the asset folder; `gen` says how to reach a server on another port. Reference page references/figures-for-video.md, lessons hub L-006, generate L-003, references L-003. Open: whether a still lineup depth control freezes the action in a fight (the owner's next render tests it). Budget stays YELLOW: installed skills 425 to 469 KB (green to 400, red at 800).

## 2026-10-17: evals harness, wall thickness, hollow shells, levelling, roofs

- `tests/run_evals.py` (new): the eval cases headless through `claude -p` with the checkout loaded by `--plugin-dir` and the installed copy switched off by `--settings`; Skill calls in the stream-json trace are the evidence. Trigger and decoy cases three times each: 80/87 ($29). Misses: generate trigger-1 named a drawing that did not exist (case fixed, `tests/fixtures/dragon.png`), blender trigger-1 answered from memory (description names the removed OBJ importer), references fired on a wrapping-paper decoy once (description excludes flat patterns), finish trigger-1 went to the hub once. Rerun of those four: 24/24 ($10). A decoy that loaded the ComfyUI image skill ran a real 12-minute GPU job, so trigger runs now cannot run commands or write files.
- `pw.py check`: wall thickness measured for print targets (inward rays from area-weighted surface points, the 3D-Print Toolbox method, written fresh: the toolbox is GPL). 20,000 points on a 400k-triangle figure in about 6 s.
- Its first real run found that `printable` made a TRELLIS.2 figure hollow: 74% of the surface under 0.9 mm, legs as tubes with 0.3 to 0.5 mm walls. The generator's mesh is a double-walled shell open through 0.5 to 1 mm gaps; a fully closed cavity was already dropped as a separate part, this one is joined to the outside. Fix: voxelise, seal gaps up to `--seal-mm` 1, flood the outside, fill what it cannot reach when over a tenth of the volume (1.76 to 3.43 cm3, thin 4.8%). Seals of 0.25 and 0.5 mm left 51% and 27% thin. Grooves narrower than the seal fill too; `--hollow` skips.
- `pw.py convert --level`: largest flat convex-hull face within 45 degrees of down turned down. The Pixal3D fountain of 2026-10-11 stood up by 17.7 degrees in 9 s. `--tilt-deg` for a known angle.
- `pw.py place`: Simple 3D Buildings (OSM wiki, edited 2026-10-15): min_height, building:min_level, building:part replacing outlines, gabled/hipped/pyramidal/skillion roofs on the minimum rectangle (others mapped), 3.2 m storeys and a 30 degree pitch as own defaults. A European old town: 229 buildings, 82 roofs, 11 left flat (not rectangular). Its print tile unions through the voxel fallback with 62 non-manifold edges, the same with flat roofs: owed.
- Sibling pointers to the folder contract merged by subagents in fresh clones: threewright #9, cinewright #48, roblox-agent #14 (also fixed its link check, red since 2026-10-13), unity-agent #12, comfyui-gen #72.
- TRELLIS.2 resolutions not run: the GPU held another session's job.
