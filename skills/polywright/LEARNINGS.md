# Learnings: polywright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · Topology checks on glTF or STL must weld coincident positions first
- Trigger: A Blender-exported GLB of two closed boxes reported 12 parts and not watertight (2026-10-11, test_convert_scale_uv_and_check)
- Hypothesis: glTF and STL store vertices per face when normals are split, so edge counting on raw vertices sees every face as its own island
- Rule: Snap positions to 1e-6 of the object's size and count edges on the welded indices (pw_bpy mesh_stats)
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

### L-002 · 2026-10-11 · Workbench cavity distance is in scene units
- Trigger: A 150 mm print tile rendered from the top showed no buildings at all (2026-10-11)
- Hypothesis: matcap_ssao_distance defaults to 0.2 units: nothing at millimetre scale, so flat roofs and flat ground shade identically
- Rule: Scale matcap_ssao_distance to about 4% of the model's radius before rendering (pw_bpy scale_cavity)
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11
