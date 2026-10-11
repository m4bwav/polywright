# Learnings: polywright-print

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · Solidify with even offset makes kilometre spikes at sharp corners
- Trigger: Known Blender issue 110057; seen on car meshes in an earlier printing pipeline
- Hypothesis: Even offset divides by the cosine of the corner angle
- Rule: use_even_offset False, thickness_clamp 1.0, offset -1 (inward) in pw.py printable
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11
