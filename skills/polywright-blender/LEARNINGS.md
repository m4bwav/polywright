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

### L-003 · 2026-10-12 · A designed prop from a written description builds best as plain bmesh: lathe, sweep, mirror
- Trigger: a spear for one of the owner's films failed five times as text-to-image; built headless from a paragraph (shaft, S-curved central prong, two mirror-image crescents, gold caps), then a fan model sheet, it went through six owner notes in about 25 minutes at under 10 s per rebuild.
- Hypothesis: revolved profiles, tubes swept with parallel-transport frames and one blade mirrored by `mesh.transform(Matrix.Diagonal((1, -1, 1, 1)))` plus `flip_normals()` give exact, glTF-ready parts with no curve conversion or modifier stack to apply.
- Rule: for a described prop, write the parts as bmesh functions with named dimensions in metres at the top of the script, print the numbers that matter (length, span, tip position), and re-render the sheet after every note. Tilt a paired part (dihedral or anhedral) before mirroring it. Recipe: references/bpy-recipes.md "A designed prop from a written description".
- Evidence: 2026-10-12 film session: the spear's build, render and camera-match scripts and sheets v1 to v5c, kept in the owner's private notes; recipe `prop-from-description` passes tests/test_recipes.py.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-12

### L-004 · 2026-10-12 · `pw.py bpy SCRIPT --blend X` sent --blend to the script, and relative render paths wrote nowhere visible
- Trigger: `pw.py bpy render_views.py --blend spear.blend -- --out views` failed with the script's own "--out is required" (argparse REMAINDER swallowed everything after the script name); separately a render to `views/side.png` reported success and left the folder empty.
- Hypothesis: REMAINDER takes all arguments after the first positional; Blender resolves a relative `render.filepath` against its own idea of the current folder, not the caller's.
- Rule: fixed in pw.py (`split_bpy_args`: pw.py's options may come before or after the script). In bpy scripts make every output path absolute (`os.path.abspath`) and print `os.path.exists` after writing.
- Evidence: 2026-10-12 film session: the spear's build, render and camera-match scripts and sheets v1 to v5c, kept in the owner's private notes; tests/test_pw.py `test_bpy_options_after_script`.
- Scope: skill (pw.py)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-12

### L-005 · 2026-10-12 · A true side view hides one of every mirror-image pair
- Trigger: the owner, twice in one session: "the bottom image only has one wing", then "now the top image is missing a wing": the three-quarter and then the side render each put the left crescent exactly behind the right one.
- Hypothesis: orthographic side views of a model symmetric about XZ overlay its pairs pixel for pixel.
- Rule: for a sheet of a model with paired parts, raise the side camera 10 to 15 degrees (keep a true side render for measuring only) and pick a three-quarter view from above that separates the pair. Check the sheet for each paired part before showing it.
- Evidence: 2026-10-12 film session: the spear's build, render and camera-match scripts and sheets v1 to v5c, kept in the owner's private notes (_sheet_v4.png three-quarter, _sheet_v5b.png side; fixed in _sheet_v5c.png).
- Scope: skill (also polywright-references)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-12

### L-006 · 2026-10-12 · Material.use_nodes and World.use_nodes are deprecated in 5.x
- Trigger: DeprecationWarning "'Material.use_nodes' is expected to be removed in Blender 6.0" on every run of a script that set it.
- Hypothesis: 5.x creates materials with a node tree already.
- Rule: do not set `use_nodes` on new materials; read the Principled node from `node_tree.nodes` (the material-5x recipe never set it). Worlds: still needed for a node background in 5.2, expect it to go in 6.0.
- Evidence: 2026-10-12 film session: the spear's build, render and camera-match scripts and sheets v1 to v5c, kept in the owner's private notes; Blender 5.2.1 stderr.
- Scope: skill (traps table at the next refresh)
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-12
