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

### L-002 · 2026-10-11 · A voxel remesh tiles flat faces as finely as curves
- Trigger: an action eval made two plain 40 mm boxes printable and got 381k triangles in a 19 MB STL (T-20261011-3)
- Hypothesis: the remesh voxel follows the model size, not its shape, and collapse decimation keeps flat areas dense up to the triangle cap
- Rule: after the final decimation, dissolve coplanar faces (0.5 degrees) and triangulate; undo it if the solid breaks (thin organic parts)
- Evidence: C-20261011-3, confirmed 2026-10-11 (boxes 488 triangles, fountain unchanged and watertight)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11
