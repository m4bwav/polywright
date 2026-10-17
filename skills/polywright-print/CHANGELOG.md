# Changelog: polywright-print

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261017-1 · 2026-10-17 · check measures wall thickness; printable fills hollow shells
- because: R-20261017-1, L-004, HANDOFF owed item 5 (min_feature was "unchecked")
- files: SKILL.md Step 2 and Step 4; ../polywright/scripts/pw_bpy.py wall_thickness, fill_cavities, act_printable; ../polywright/scripts/pw.py check (--thickness-samples, --no-thickness), printable (--seal-mm, --hollow); ../polywright/references/cli.md
- `check` with Blender measures thickness for targets with `min_feature` and warns over 0.5% thin; `printable` fills a hollow shell's inside, which the first measurement found in a generated figure.

### C-20261011-4 · 2026-10-11 · printable re-grounds before the base clamp; faster, stricter planar dissolve
- because: L-003; the wiki verification run of the published 0.1.1 (ai-docs/notes/2026-10-11-wiki-verify.out.txt) made a flat park scene printable and got 59,198 non-manifold edges; the dissolve on 368k faces ran over ten minutes
- files: ../polywright/scripts/pw_bpy.py act_printable, tests/test_pw.py test_printable_flat_open_surface
- The model is moved back to z=0 after the remesh, so the clamp cuts only the bottom 0.6 mm; the dissolve works on a 100k copy and is kept only when it halves that copy without breaking the solid.

### C-20261011-3 · 2026-10-11 · printable merges coplanar faces after the remesh
- because: T-20261011-3 (two 40 mm boxes came out as 381k triangles, 19 MB), L-002
- files: ../polywright/scripts/pw_bpy.py act_printable, ../polywright/scripts/pw.py --no-planar
- A planar dissolve (0.5 degrees) plus triangulate follows the final decimation and is undone when it breaks the solid: the boxes became 488 triangles, the generated fountain kept its 400k and stayed watertight.

### C-20261011-2 · 2026-10-11 · Description says when to fire
- because: T-20261011-2 first pass (undertriggering: prompts answered without the skill; hub and finish both claimed game-readiness)
- files: SKILL.md frontmatter description
- Descriptions open with 'Use whenever ...' and name the requests each skill owns; the hub only takes requests no sibling owns.

### C-20261011-1 · 2026-10-11 · Created as an evergreen unit
- because: user request (an evergreen 3D modelling plugin); research R-20261011-1 to R-20261011-2
- files: SKILL.md, references/, RESEARCH.md, LEARNINGS.md, TESTS.md, evals/evals.json, evergreen.json
- Initial version, tier `moderate`, interval 30d, written from the five research notes of 2026-10-11 and the verified runs logged in LEARNINGS.md.
