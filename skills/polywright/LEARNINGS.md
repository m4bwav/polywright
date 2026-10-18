# Learnings: polywright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-006 · 2026-10-16 · A small cast of real figures holds in video only when the meshes carry the markings and a lineup carries the sides
- Trigger: a 15 s two-on-two toy fight rendered from photo crops swapped the teams' sides, drew one figure twice and showed a fifth figure for a moment; the figures' painted letter and numbers read small. Meshing each toy (TRELLIS.2) fixed the shapes, but the markings baked as smears and the colours drifted.
- Hypothesis: a video model keeps who stands where and how many only when a picture or control says so; reference crops of figures lying on a table say neither. A generated mesh is only as good a reference as its texture.
- Rule: per figure, mesh the front view, then `pw.py mark` (colour to the photo's medians, erase the smear on the head front, a text mesh for the marking, real size), `pw.py turnaround` for the reference pictures, and one `pw.py lineup` with each team on a fixed side for the opening frame and a depth control. Record each output with `manifest --add-output` written from inside the asset folder (it now resolves there) and `--review`. Pass `--host` to `pw.py gen` when the server is not on 8188.
- Evidence: the 2026-10-16 run: four figures and five accessories, every `mark` and `turnaround` reproduced by the commands (same 5,557 head triangles and 9,396 erased texels on the first figure); lineup `left_to_right` in the planned order; tests `test_turnaround_views_and_sheet`, `test_mark_puts_the_marking_on_the_head_front`, `test_lineup_keeps_teams_on_their_sides`, `test_manifest_output_relative_to_the_asset_and_reviews`. The video re-render with the lineup is still to come.
- Scope: skill (pw.py turnaround, mark, lineup, manifest; references/figures-for-video.md)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-16

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

### L-006 · 2026-10-17 · To take an accessory off a TRELLIS.2 mesh, delete its loose pieces by their texture colour
- Trigger: The owner ruled that one toy figure wears no shoulder pad and has two black legs, though the photo shows a teal pad and a leg that catches the light as silver. A bounding box around the pad, used to grey out its square, also caught the skull and turned half the face teal.
- Hypothesis: TRELLIS.2 output is a soup of thousands of loose pieces (4690 here), not one surface, and an accessory is made of its own pieces, so it can be cut out piece by piece. A box in 3D overlaps whatever sits next to the accessory.
- Rule: label the pieces (`trimesh.graph.connected_component_labels` on the face adjacency, seconds on 700k faces, where `split()` ran past two minutes), sample the base colour at each face's UV centroid, delete the pieces where most faces are the accessory's colour, then the pieces inside its box that hold its other colours (grow the box outward only). Paint any of that colour left in the texture the body's colour, scaled by brightness. A wrong colour on one part (a silver leg) is a texture fix: the part's lower-body UV islands, side chosen by which holds more pale texels. Check with `pw.py turnaround` after each step; the body under the accessory was already modelled, so nothing showed through.
- Evidence: the fix scripts, the failed box try and before-and-after turnarounds (teal skull, then fixed) are in the owner's private notes, 2026-10-17.
- Scope: skill (polywright-generate cleanup of an image-to-3D mesh; pw.py mark has no accessory removal yet)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-17

### L-005 · 2026-10-16 · A pose pass must leave out face points turned from the lens, and a previs checks that each end state is in frame
- Trigger: a two-fighter previs (crowd mannequins posed by IK in a set blockout) for a rapier duel whose video takes kept turning a fighter seen from behind to face the lens. Its pose pass drew his nose and eyes though his back was to the camera, as `pw.py crowd` did for every figure. The previs of a kick card also put the felled fighter below the frame: the card's own camera (1.2 m high, level, 35 mm, 4 m off) sees the floor only beyond about 4.2 m.
- Hypothesis: pose controls are trained on detector output, and a detector finds no nose or eyes on a back; drawn face points tell the model the figure faces the camera. A shot plan places people as points, so it cannot see that a lying body leaves the frame.
- Rule: hide the nose and each eye once turned away from the lens (dot of head-to-point and head-to-camera under -0.2; a profile keeps the nose and near eye) and an ear behind the head (under -0.35): `hidden_face_points` in pw_bpy.py, joints written as (-1, -1), which `draw_pose_frames` leaves out with their limbs. Before rendering video from a previs, read the sheet at every end state and tilt or move the camera where it falls outside the frame.
- Evidence: the duel previs sheets 2026-10-16 (cinewright research note 2026-10-16-fight-3d-route); a side-view crowd keeps all 48 noses, a crowd marching away keeps none (tests `test_crowd_from_behind_hides_faces`, `test_pose_leaves_out_hidden_joints`).
- Scope: skill (pw.py crowd pose pass; any two-fighter previs)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-16

### L-004 · 2026-10-13 · A crowd blockout's defaults decide whether anything is in frame
- Trigger: the first `pw.py crowd` previews showed empty frames (armies starting outside a 14 m camera's view), a white smear of clamped near ground in the depth pass, and a clash whose sides never met in 81 frames.
- Hypothesis: the camera distance, the depth range and the starting gap all depend on the formation and the shot length, so fixed numbers fail for most inputs.
- Rule: derive them: camera distance from the armies' reach and the lens (half width = distance x 18 / lens); depth range from the nearest ground in frame to past the farthest figure, sampled over the whole shot and fixed for it; the clash or charge gap from both sides' speed over two thirds of the shot. Always `--preview` and read `sheet.png` before the full render.
- Evidence: previews in the 2026-10-13 build session; final run 240 figures, 81 frames, four passes in 81 s on the CPU, both sides in frame from frame 1 and meeting at the line.
- Scope: skill (pw.py crowd)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-003 · 2026-10-12 · To fix a prop in a picture, match the picture's camera and paste the model; the solve needs only two pixels and a depth
- Trigger: a film's set still showed a plain spear where the designed one belonged; text and whole-picture edits redraw the prop (the owner's image-generation notes). The camera was unknown.
- Hypothesis: with a fixed lens (35 mm) and the horizon row for pitch, a hand pixel at a guessed depth plus the exact tip pixel fix the pose; depth alone sets the size in frame (match the stand-in's width in pixels: width = f_px x diameter / depth). Depth 3.3 m drew the Spear twice too thick and crossing the king's head; 6.5 m matched.
- Rule: `pw.py match` (new) renders the model RGBA from that camera, pastes it, drops boxes in front of it (`--hide`, the fist) and writes a blend mask (alpha grown, plus `--mask-add` ellipses for the hands). Then blend inside the mask with a low-denoise edit and paste back through the mask. Hub section "Compose a model into a picture".
- Evidence: 2026-10-12 film session: the spear's build, render and camera-match scripts and sheets v1 to v5c, kept in the owner's private notes; pw.py match reproduced the hand-rolled solve exactly (aim 720,404; yaw 31.9, pitch 5.88).
- Scope: skill (pw.py, hub)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-12
