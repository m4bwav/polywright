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

### L-004 · 2026-10-17 · Image-to-3D figures come out of printable hollow
- Trigger: the first wall-thickness check, on a TRELLIS.2 toy figure made printable at 60 mm, found 74% of the surface under 0.9 mm; rays through the legs crossed four walls 0.3 to 0.5 mm thick with air between
- Hypothesis: the generator's mesh is a thin double-walled shell open through gaps of 0.5 to 1 mm, so the voxel remesh keeps both walls, and the cavity is joined to the outer surface, so keeping the largest part does not drop it (a fully closed cavity was already dropped)
- Rule: after the remesh, voxelise, seal gaps up to 1 mm, flood the outside and fill what it cannot reach when that is over a tenth of the volume; check wall thickness after every printable on a generated model. Seals of 0.25 and 0.5 mm left 51% and 27% thin
- Evidence: C-20261017-1; figure 1.76 to 3.43 cm3, thin 74% to 4.8%; test_printable_fills_a_hollow_shell. Amended C-20261017-2: measure the air as cells reachable through the gaps but not once sealed; counting the whole sealed inside sent a solid terrain slab through the fill and broke it
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-17

### L-003 · 2026-10-11 · Re-ground after thickening, before clamping a flat base
- Trigger: a flat terrain sheet made printable came out with 59,198 non-manifold edges and 0 volume (wiki verification run)
- Hypothesis: the model was grounded before the inward solidify, which pushed the sheet 1.2 mm below z=0; the clamp then flattened the whole slab into one plane
- Rule: measure and move the model back to z=0 after the remesh, then clamp; test with an open flat sheet
- Evidence: C-20261011-4, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11


### L-005 · 2026-10-17 · The default base cut shaves models whose bottom is already flat
- Trigger: two overlapping boxes made printable at 40 mm came out 26.07 mm tall instead of 26.67 mm; `steps` said "flat base: clamped below 0.60 mm" although the bottom was a flat box face
- Hypothesis: `--base-cut-mm 0.6` always removes 0.6 mm from the lowest point, whether or not the base needs flattening
- Rule: for code-CAD or box-like inputs with a flat underside, pass `--base-cut-mm 0`; candidate fix: skip the clamp when the lowest 0.6 mm already holds a flat face covering most of the footprint
- Evidence: rerun with `--base-cut-mm 0` gave 26.667 mm and 22.518 cm3, the exact union volume (9.5 units3 x 13.33^3)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-17
