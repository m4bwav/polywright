# Learnings: polywright-blender

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · Workbench shadows are show_shadows in 5.x
- Trigger: AttributeError on shading.show_shadow (2026-10-11)
- Hypothesis: Renamed property
- Rule: Use show_shadows; read bl_rna properties before guessing
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

### L-002 · 2026-10-11 · Multilayer EXR needs media_type first in 5.x
- Trigger: OPEN_EXR_MULTILAYER not in file_format enum; after media_type MULTI_LAYER_IMAGE it is the only format (recipe test, 2026-10-11)
- Hypothesis: 5.x split image settings into media type and format
- Rule: Set image_settings.media_type = MULTI_LAYER_IMAGE, then file_format = OPEN_EXR_MULTILAYER
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11
