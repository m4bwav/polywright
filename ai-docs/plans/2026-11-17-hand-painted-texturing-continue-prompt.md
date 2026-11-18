# Continue prompt: hand-painted texturing route for polywright

Run this the same way every session. Keep state in `ai-docs/HANDOFF.md` (section "Hand-painted texturing"), never in this file.

## Load state
1. Read `ai-docs/HANDOFF.md`, the 2026-11-17 entry in `ai-docs/log.md`, and `ai-docs/INDEX.md`.
2. Read the skills polywright-blender (SKILL.md, references/bpy-recipes.md, references/bpy-api-traps.md) and polywright-finish.
3. Make a worktree off origin/main before editing anything: `git worktree add ../polywright-handpaint -b handpaint origin/main`. Never switch the shared clone's branch.

## Source
The source is Craft Reaper's "Complete Guide of Hand Painting Game Assets in Blender with Ucupaint" (https://www.youtube.com/watch?v=5nwoGU_ZmhY).
- Get the transcript with `python -m yt_dlp --skip-download --write-auto-subs --sub-langs en` into the scratchpad.
- Gemini can't be used for this video: the flash models return 503 and 3.1 Pro has no free-tier quota. Retry gemini-3.5-flash once with `mediaResolution LOW`, and fall back to the transcript if it fails.

## Gather
Research each candidate below from primary sources: Blender 5.2 LTS and 5.3 manuals, the Ucupaint GitHub repo and the extensions.blender.org page, and the bpy API docs. Also look for 1–2 other recent hand-painted or stylized texturing workflows in Blender, and add anything they do that the video doesn't. Record each finding in `ai-docs/research/hand-painted-texturing.md` with its source and date.

Candidates:
- Ucupaint: licence, version, Blender 5.x support, and whether it can be installed and driven headless (its layer and bake-all operators).
- Standard view transform while painting.
- Bake margin and margin type (extend vs adjacent faces) against UV bleed.
- Curvature bake: Ucupaint's edge detect versus native options (Cycles pointiness, AO, and a bevel-normal difference), used as highlight and cavity layers.
- Masks from selected faces.
- Unlit (emission) preview with flat shading.
- `image.project_edit` / `image.project_apply` round trip to Krita.
- Colour variants made with adjustment layers, then rebaked.

## Test
Testing needs no permission. Use Blender headless through `pw.py bpy`.
- On a low-poly test prop (a shield or crate), script each candidate that can be scripted and prove it with evidence: a baked PNG, numbers measured from it (e.g. no bleed past the island plus margin, the curvature map's range), and a contact sheet.
- Write down which candidates need the UI (Quick Edit, painting strokes) instead of faking them.
- Score each candidate KEEP / MAYBE / DROP with one line of reason.

## Build (KEEP items only)
- Add a short "Hand-painted texturing" recipe section to bpy-recipes.md, with traps going in the traps file.
- Add one line in polywright-finish routing hand-painted requests to that section.
- Add a `pw.py` subcommand only if a bake is repeated enough to be worth it (e.g. `pw.py bake-masks` for curvature + AO with margin), with a test.
- Follow AGENTS.md:
  - Every recipe block gets a `# recipe:` line and a `[pw] ok` print, and must pass `python tests/test_recipes.py`.
  - Claims get an `R-` entry in RESEARCH.md and a CHANGELOG line.
  - Run `tests/check_skills.py`, `tests/test_pw.py` and `scripts/budget.py` before committing.
  - Stay inside the size budget.
  - Keep the repository public-safe: no machine paths or names.

## Stop points and hand-over
- Ship it the normal way: bump the patch version, update the changelog, open a PR, and merge it yourself once checks pass. Then tag and release, and update the installed plugin.
- Questions for Mark go on an askwright page, never in chat. Examples: whether to recommend a third-party extension, or a skipped step that needs a GPU for hours.
- Remove the worktree after the merge.
- At the end: run evergreen-wrapup, update HANDOFF.md, and print the start command for this same file.
