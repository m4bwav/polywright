# Learnings: polywright-blender

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

Archived 2026-11-20 to save install size (full text in the repo at ai-docs/notes/polywright-blender-learnings-archive.md, not installed):
- L-001 · 2026-10-11 · Workbench shadows are show_shadows in 5.x
- L-002 · 2026-10-11 · Multilayer EXR needs media_type first in 5.x
- L-003 · 2026-10-12 · A designed prop from a written description builds best as plain bmesh: lathe, sweep, mirror
- L-004 · 2026-10-12 · `pw.py bpy SCRIPT --blend X` sent --blend to the script, and relative render paths wrote nowhere visible
- L-005 · 2026-10-12 · A true side view hides one of every mirror-image pair
- L-006 · 2026-10-12 · Material.use_nodes and World.use_nodes are deprecated in 5.x
- L-007 · 2026-10-22 · transform_apply(scale=True) also applies location and rotation
- L-008 · 2026-10-22 · Check shading changes by (position, normal) corners, not vertex counts
- L-009 · 2026-10-23 · Workbench shadows on a big coarse terrain streak it with acne that Canny reads as lines

### L-010 · 2026-11-14 · Candidate: warm and cool two-sided light for sheet renders
- Trigger: a modelling book lights review renders with a warm key on one side and a cool fill on the other.
- Hypothesis: it may read better than the current flat sheet light.
- Rule: not adopted; adopt only after a side-by-side judged test on real sheets.
- Evidence: none yet (books track 2026-11-14).
- Scope: global
- Status: candidate · helpful 0 · harmful 0 · last_confirmed 2026-11-14

