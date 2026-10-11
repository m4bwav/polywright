# Learnings: polywright-capture

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · Overpass returns whole ways: clip lines and polygons to the box
- Trigger: First park run put roads hundreds of metres outside a 540 m box (2026-10-11)
- Hypothesis: `>; out skel` recurses to every node of a way that touches the box
- Rule: Clip lines (Liang-Barsky) and polygons (Sutherland-Hodgman) to the box before building meshes
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

### L-002 · 2026-10-11 · A Manifold union silently drops every operand when the base is inside out
- Trigger: Park print tile came out with no buildings; trimesh showed the terrain block with negative volume (2026-10-11)
- Hypothesis: The block's rim runs clockwise seen from above, so walls and bottom were wound inward
- Rule: Wind walls and bottom for a clockwise rim; test blocks closed and outward; compare union bounds with the inputs and fall back to EXACT
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

### L-003 · 2026-10-11 · Overpass: descriptive user agent, narrow queries, is_in for enclosing areas
- Trigger: a Central Park box failed on every mirror (504 and 500); curl with a generic user agent got 406; the park polygon itself never came back
- Hypothesis: overpass-api.de filters generic agents and limits slots per address; an all-elements query in a dense city times out; box filters only match ways with a node inside the box
- Rule: send a descriptive User-Agent, query only the tags used, add `is_in` at the centre for leisure, landuse and natural areas, wait for a free slot (`/api/status`) instead of hammering mirrors
- Evidence: C-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

### L-004 · 2026-10-11 · Multipolygons need stitching; smaller areas paint last; flatten water
- Trigger: Central Park's lake and park polygons were missing or painted over islands; the lake surface was bumpy
- Hypothesis: relation outlines are split across ways; class priority painted water over smaller land areas; lidar returns over water are noise
- Rule: stitch outer and inner member ways into rings (inner = holes), paint areas largest first, flatten each water body to its lowest grid point
- Evidence: C-20261011-1, render of the Bethesda Terrace tile, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

