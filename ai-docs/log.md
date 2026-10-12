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
