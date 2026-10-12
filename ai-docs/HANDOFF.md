# Handoff

Last updated 2026-10-11 (second session: Blender discovery verified on macOS and Linux, PR #6).

## State

- Seven skills under `skills/`, the CLI `skills/polywright/scripts/pw.py` (+ `pw_bpy.py`), budgets in `skills/polywright/references/targets.json`, research in `research/`.
- Tests: `python tests/check_skills.py`, `python tests/test_pw.py`, `python tests/test_recipes.py`, `python scripts/budget.py` all pass on Windows 11 with Blender 5.2.1 (and with the bpy 5.2.2 wheel through POLYWRIGHT_BPY_PYTHON).
- github.com/m4bwav/polywright (public), CI green on main. Releases v0.1.1 and v0.1.2 published (owner's go-ahead 2026-10-11). Wiki live (11 pages, verified against 0.1.2): how to update it is in [notes/2026-10-11-github-wiki.md](notes/2026-10-11-github-wiki.md).
- TRELLIS.2 and Pixal3D models downloaded on the dev PC (owner's go-ahead); both ran through ComfyUI's template via `pw.py gen --workflow`.
- Blender discovery verified on all three systems: Windows (owner's PC), macOS (`/Applications/Blender.app` from the Homebrew cask, CI job `blender-app`), Linux (blender.org tarball in `~`, CI and WSL here). The owner's Mac has no SSH, so it was not used.
- Evals: triggers 23/28 (all decoys pass), two action cases run; see each skill's TESTS.md. Next session's prompt: [next-session-prompt.md](next-session-prompt.md).

## Owed

1. Evals: three runs per case, the remaining action and outcome cases, baselines without the skill, and the three genuine undertriggers (polywright-blender trigger-1 and -2, polywright-generate trigger-1). Run headless with `claude -p` in a throwaway clone (Windows: start claude through shutil.which, the .cmd shim).
2. TRELLIS.2: a skill or pw.py step that levels Pixal3D's camera-frame output; the template's other resolutions on 16 GB; README sentence on TRELLIS.2 ships with the next release.
3. Done 2026-10-11 (PR #6). Still unchecked: Linux snap and distro packages, `~/Applications` on macOS, Steam installs.
4. `pw.py place`: building `min_height` and roof shapes, Overture heights where OSM has none, open imagery for ground textures, per-colour 3MF output for multi-colour prints.
5. A wall-thickness measurement for `check --target print-fdm` (now "unchecked").
6. Teach the owner's other plugins to call polywright through the folder contract (threewright, cinewright, roblox-agent, unity-agent, and the private printing and ComfyUI skills): one line each pointing at `skills/polywright/references/contract.md`.
7. Wiki: update it with each release (procedure in the wiki note).

Related: [INDEX.md](INDEX.md)
