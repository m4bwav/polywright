# Learnings: polywright-generate

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · ComfyUI has the TRELLIS.2 nodes but not their weights
- Trigger: object_info on a 0.38.2 host listed Trellis2* and Pixal3D* nodes; models/ had none of the template's files (2026-10-11)
- Hypothesis: Native nodes ship with ComfyUI; models are separate downloads
- Rule: Check the template's model list before promising TRELLIS.2; offer Hunyuan3D-2 or a download (the user's call: several GB)
- Evidence: R-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11
