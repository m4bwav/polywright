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
- Trigger: the No-God film's set still showed a plain spear where the designed one belonged; text and whole-picture edits redraw the prop (comfyui-gen L-091). The camera was unknown.
- Hypothesis: with a fixed lens (35 mm) and the horizon row for pitch, a hand pixel at a guessed depth plus the exact tip pixel fix the pose; depth alone sets the size in frame (match the stand-in's width in pixels: width = f_px x diameter / depth). Depth 3.3 m drew the Spear twice too thick and crossing the king's head; 6.5 m matched.
- Rule: `pw.py match` (new) renders the model RGBA from that camera, pastes it, drops boxes in front of it (`--hide`, the fist) and writes a blend mask (alpha grown, plus `--mask-add` ellipses for the hands). Then blend inside the mask with a low-denoise edit and paste back through the mask. Hub section "Compose a model into a picture".
- Evidence: 2026-10-12 No-God film: D:/ComfyUI/output/video/nogod/refs/spear/ (build_spear.py, render_views.py, camera_match.py, _sheet_v1..v5c.png); pw.py match reproduced the hand-rolled solve exactly (aim 720,404; yaw 31.9, pitch 5.88).
- Scope: skill (pw.py, hub)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-12
