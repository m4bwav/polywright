# Learnings: polywright-finish

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · Generated meshes have no UVs: Roblox check fails until unwrapped
- Trigger: Fountain game GLB failed require_uvs (2026-10-11)
- Hypothesis: Hunyuan3D-2 shape output carries no UV layer
- Rule: convert --uv (Smart UV Project) after decimation, before export
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

### L-002 · 2026-10-22 · A tiny broken fixture can be fixed by hand, so it tests the outcome, not the skill
- Trigger: one of three runs of action-topology never loaded polywright-finish: it parsed the 12-triangle GLB in Python and swapped the flipped triangle itself, correctly.
- Hypothesis: a fault small enough to read in the raw buffer invites a hand fix.
- Rule: grade such a case on the fixed file; use a real-size mesh when the case must prove the command is used.
- Evidence: T-20261022-1
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-22
