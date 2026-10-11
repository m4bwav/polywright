# Handoff

Last updated 2026-10-11 (first session, 0.1.1 on main, not tagged).

## State

- Seven skills under `skills/`, the CLI `skills/polywright/scripts/pw.py` (+ `pw_bpy.py`), budgets in `skills/polywright/references/targets.json`, research in `research/`.
- Tests: `python tests/check_skills.py`, `python tests/test_pw.py`, `python tests/test_recipes.py`, `python scripts/budget.py` all pass on Windows 11 with Blender 5.2.1 (and with the bpy 5.2.2 wheel through POLYWRIGHT_BPY_PYTHON).
- github.com/m4bwav/polywright (public), CI green on main. Version 0.1.1 in plugin.json; no tag or GitHub release yet (waits for the owner's go-ahead; then `git tag v0.1.1 && git push origin v0.1.1` and the release workflow publishes).
- Evals: triggers 23/28 (all decoys pass), two action cases run; see each skill's TESTS.md. Next session's prompt: [next-session-prompt.md](next-session-prompt.md).

## Owed

1. Evals: three runs per case, the remaining action and outcome cases, baselines without the skill, and the three genuine undertriggers (polywright-blender trigger-1 and -2, polywright-generate trigger-1). Run headless with `claude -p` in a throwaway clone (Windows: start claude through shutil.which, the .cmd shim).
2. TRELLIS.2 / Pixal3D: the native ComfyUI nodes are present on the test host but the seven model files of the template `3d_pixal3d_trellis2_image_to_model` are not; downloading them is the owner's call (several GB). Then export the template in API format and run `pw.py gen --workflow`, and record VRAM and time on a 16 GB card.
3. Blender discovery on macOS and Linux installs (only Windows verified); the CI Blender job uses the bpy wheel.
4. `pw.py place`: building `min_height` and roof shapes, Overture heights where OSM has none, open imagery for ground textures, per-colour 3MF output for multi-colour prints.
5. A wall-thickness measurement for `check --target print-fdm` (now "unchecked").
6. Teach the owner's other plugins to call polywright through the folder contract (threewright, cinewright, roblox-agent, unity-agent, and the private printing and ComfyUI skills): one line each pointing at `skills/polywright/references/contract.md`.
7. Wiki: needs the owner's first-page click on GitHub before wikiwright can push.

Related: [INDEX.md](INDEX.md)
