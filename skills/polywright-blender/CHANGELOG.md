# Changelog: polywright-blender

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261118-1 · 2026-11-18 · Motion blur for beauty turntables
- because: user request (technique harvest 2026-11-18, Reddit posts 1xum86v and 1xxqbuw)
- files: references/bpy-recipes-scenes.md (passes-one-render)
- Beauty renders turn motion blur on (shutter 0.5) and match scene fps to export fps; no recipe code changed.

### C-20261117-4 · 2026-11-17 · palette-atlas and rigid-skin-boxes recipes
- because: technique-harvest post yt-B-vI6rRxfIk (Back To Code video, ideas only, no code copied), user request
- files: references/bpy-recipes-scenes.md, references/bpy-recipes-motion.md
- Shared palette image with UVs collapsed per swatch; rigid one-bone-per-part boxes with one NLA strip per action. Both pass tests/test_recipes.py headless.

### C-20261117-3 · 2026-11-17 · handpaint-ucupaint recipe and trap
- because: R-20261117-3
- files: references/bpy-recipes-motion.md, references/bpy-api-traps.md

Ucupaint tested headless; recipe skips cleanly when it is absent.

### C-20261117-2 · 2026-11-17 · handpaint-base recipe
- because: R-20261117-2
- files: references/bpy-recipes-motion.md

### C-20261117-1 · 2026-11-17 · Previs fact-list rule, rigged-character recipe
- because: R-20261117-1 (technique harvest)
- files: SKILL.md (Step 4), references/bpy-recipes-motion.md (new: animate-rigged-character), references/mcp-bridges.md (When to use one)
- Previs gets checked fact by fact from scene data; a headless recipe keys pose bones in an action.

### C-20261114-1 · 2026-11-14 · Curve repeats, edge-wear bake, sky-plus-sun and cutter-normals lines
- because: user request (books track blender-books-2026-11-14: *Blender 3D Environment Design*; Belec, *Blender: Create Incredible Models*); R-20261114-1, T-20261114-1
- files: references/bpy-recipes-motion.md (new: curve-array, edge-wear-mask), references/bpy-recipes.md (boolean-fallback recalcs cutter normals; material-5x note on Sky Texture plus sun), references/bpy-recipes-scenes.md (gn-scatter per-instance budget line), SKILL.md (Step 4 link text)
- Both new recipes run in 5.2.1; the edge-wear bake read zero edge texels on a smooth-shaded cube and works flat-shaded. 3.x-era claims (particle scatter, MixRGB, Filmic, Auto Smooth) left out.

Entries 2026-10-11 to 2026-11-09: [ai-docs/archive/polywright-blender-changelog-2026-10-11-to-2026-11-09.md](../../ai-docs/archive/polywright-blender-changelog-2026-10-11-to-2026-11-09.md).
