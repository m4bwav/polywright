# Learnings: polywright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-009 · 2026-10-22 · From behind, the default camera merges the enemy line and its reserves into one band; raise it and aim past the enemy
- Trigger: `pw.py crowd --view behind --action hold --scatter 450 --preview` put the camera 6 m high and 43 m back (30 m default gap). Side A filled the lower half of the frame, and side B with its 221 reserves was a strip about 60 px tall where the scattered reserves could not be told from the formed ranks. `--cam-height 12 --lens 45 --gap 20` separated them, but tilted so far down that the reserves touched the top edge and there was no horizon.
- Hypothesis: the behind view aims at the battle line (x 0, z 1), so the depth behind the enemy, where `--scatter` puts the reserves, shrinks to a few rows of pixels. Height opens up that depth; aiming beyond the enemy brings the horizon back.
- Rule: for a shot from behind one army toward enemy reserves, start from `--gap 20 --cam=-32,16.5,9 --aim=14,16.5,0 --lens 40` (y = the frontage centre the command reports). That gives a horizon near the top, your own ranks across the bottom, then the enemy's formed line and the loose reserves behind it, separated by the gap. `--scatter` yields about 40 percent of what you ask: 450 gave 221, 650 gave 259.
- Evidence: the 2026-10-22 preview in pw-eval-mr7nfrh6/reserves (the README there has the commands and the review). Second run the same day (pw-eval-l64xbjxo/reserves): a lower, closer framing also works when your own ranks should loom large, `--gap 16 --cam=-21,16.5,4.5 --aim 14,16.5,0 --lens 45` (horizon at about a quarter from the top, enemy line across the full width). But there the reserves sit flush on the last rank and read as a deeper formation; 6.5 m high from 22 m back showed only helmets and almost black enemy depth. 450 asked gave 240. A `--scatter-offset` (space between the last rank and the reserves) is worth adding. Third run (pw-eval-ybkwc8ep/reserves, same day): `--gap 18 --cam=-24,16.5,6.5 --aim=16,16.5,-1 --lens 35 --far 60` put helmeted backs across the bottom third and the loose reserves visibly behind the enemy's formed line in clay; aiming below the ground (z -1) is what brought our ranks back in. Enemy and reserves still sit at grey 30 to 50 of 255 in depth: inverse depth spends the range on the near ranks. 450 asked gave 221.
- Scope: skill (pw.py crowd behind view and --scatter)
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-10-22

### L-008 · 2026-10-19 · A duel's depth or Canny passes hold where the fighters stand and which way they face, but not a low pose
- Trigger: a film's batch rendered `pw.py duel` passes as the video model's control (thick-blade depth 0.8/0.6 on close two-shots, the clay's Canny 0.6/0.4 on a high wide). Over-the-shoulder two-shots that had drifted to face the lens held their framing and a sword's length on both takes. But a fighter posed kneeling came out standing in both takes, a dagger posed in the back came out held upright in front of the chest, and two mannequins lying one across the other came out as two men standing in one take and one standing in the other. A guide still with the two bodies lying gave exactly two lying bodies on both seeds (field lesson 146).
- Hypothesis: the passes' silhouettes say where a body is, how big and which way it faces; the prompt and the full-length character references decide its pose, and a standing figure fits a low silhouette.
- Rule: use `duel` passes for placement, facing and distance on standing two-shots. For kneeling, grappling on the floor or bodies lying, pin the pose with a guide still at frame 0 and no control, and use the duel's clay only to count and place the figures for that still.
- Evidence: the 2026-10-19 review of the batch (21 takes; the takes, strips and full-size frames are in the owner's private film notes); field lessons 128, 144, 145, 146.
- Scope: skill (pw.py duel; hub "army blockouts with depth and pose passes for AI video")
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-19

### L-007 · 2026-10-17 · The crowd command's default side view frames a 30-wide march as a thin band, and --aim needs --cam
- Trigger: `pw.py crowd --action march --kit spear,shield,helmet --preview` with default settings put 360 figures in a band about 60 px tall at 832x480 (camera 6 m high, 50 mm, 39 m back), with half the frame empty ground. On the re-run, `--aim 0,8,1.6` was ignored: the result still reported aim z 0.8.
- Hypothesis: `crowd_camera` sets the distance from the armies' reach, but the 6 m height and the 0.8 m aim make it look down onto the ground. It only reads `aim` when `cam` is also given (pw_bpy.py, `crowd_camera`).
- Rule: for a march, start from `--gap 20 --cam-height 2.2 --lens 35`. That gives figures about 70 px tall with both sides in frame from frame 1. To aim the camera, pass `--cam X,Y,Z` together with `--aim`. Fix to consider: honour `--aim` without `--cam`, or have the help text say it needs `--cam`.
- Evidence: the 2026-10-17 preview in pw-eval-3vogrrzt/crowdtest (the README there has the commands and the review). Second run the same day (pw-eval-ko45dthm/crowdtest): the gap is the main lever. `--cam-height 2.5 --lens 35` with the 30 m default gap made the band thinner and pushed both armies to the frame edges; `--gap 16` alone (default 6 m, 50 mm) gave figures about 100 px tall, both sides on screen and about 1 m apart at frame 81 (march covers 13 m in 81 frames at 16 fps). Also: `sheet.png` tiles frames with no separator, so the gap between two armies can be misread as a frame boundary; open a single frame when in doubt.
- Scope: skill (pw.py crowd defaults and help text)
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-10-17

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

### L-010 · 2026-10-22 · Recalculating normals fixes AI meshes' flipped faces, but only on welded topology
- Trigger: `inspect --topology` found winding mismatches in 9 of 13 image-to-3D meshes; Blender's recalculation cleared them only after merging split vertices, which loses UV seams and split normals.
- Hypothesis: glTF splits vertices per face, so a face has no neighbours to agree with until positions are welded.
- Rule: orient faces on welded positions and flip the minority per connected part, keeping the vertices (`convert --fix-winding`).
- Evidence: C-20261022-4; 288 and 1,030 faces flipped on two real meshes, mismatches to 0, UV spread unchanged.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-22

### L-011 · 2026-10-22 · A scatter behind the far side shows only in some framings
- Trigger: `crowd --scatter 200` changed no mask pixels in the side and high views; in the behind view side A's reserves crowded the lens.
- Hypothesis: the default cameras frame the armies tightly; the behind camera stands inside side A's rear.
- Rule: reserves read from the behind view (the enemy's) or a widened camera; skip a side whose rear holds the camera.
- Evidence: C-20261022-4; blue mask pixels 13,710 to 24,587 behind, red unchanged after the skip.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-22

### L-012 · 2026-10-23 · crowd.blend holds only the last frame's pose: render extra passes inside the frame loop
- Trigger: a Mist pass rendered afterwards from `crowd --save-blend` came out as 73 copies of the last frame. `crowd` poses every figure from Python frame by frame; nothing is keyframed, and the saved file keeps the final pose and the default 250-frame range.
- Hypothesis: the crowd's motion lives in pw_bpy's loop, not in the .blend.
- Rule: for a pass `crowd` does not write (Mist), run the crowd action with that pass added inside the per-frame render: a wrapper that replaces `pw_bpy.render_depth` with one that also enables the Mist pass and a File Output node at the shot's near and far, renames `m_Mist.png` to the frame's name after each render, then calls `pw_bpy.main()`. The depth frames stayed identical byte for byte. A built-in `--passes mist` is the cleaner fix.
- Evidence: depth test 2026-10-23 (73 frames, 608x352, Blender 5.2.1, 29 s for depth and Mist together)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23
