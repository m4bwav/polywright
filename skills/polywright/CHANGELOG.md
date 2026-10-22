# Changelog: polywright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261022-1 · 2026-10-22 · Hand-off to artwright-judge for concept art and turnarounds
- because: user request (artwright's fork 3, answered 2026-10-21: one-line hand-offs from the owner's image skill and polywright)
- files: references/contract.md "Which plugin takes what" (one row)
- Concept art before image-to-3D and turnaround renders can go to `artwright-judge`, which writes `artwright/verdict.json`; the row links its public contract. The description is unchanged, so the trigger evals were not re-run.

### C-20261019-1 · 2026-10-19 · Lesson L-008: duel passes hold placement, not low poses
- because: L-008 (field use of `pw.py duel` passes as video control)
- files: LEARNINGS.md "Active"
- A new lesson only; SKILL.md and the references are unchanged until the rule is confirmed a second time.

### C-20261017-6 · 2026-10-17 · pw.py duel: two-fighter previs controls
- because: user request (the owner approved building it after a field test: figures in the control removed a duplicated fighter and held a floor shot's states; thick-blade depth held a back to the camera through the action); L-005
- files: SKILL.md "Crowd and battle blockouts" (one paragraph; the crowd steps tightened so the hub stays under its green budget); references/crowd-blockouts.md "Two fighters" (rewritten for the command); references/cli.md; references/film-and-video.md "Commands for film"; scripts/pw.py duel and shared helpers; scripts/pw_bpy.py act_duel and the helpers split out of act_crowd; examples/duel.json, examples/duel_room.py
- The previs route of "Two fighters" became `pw.py duel`. hidden_face_points moved to pw.py (plain maths, tested without Blender). The description is unchanged, so the trigger evals were not re-run.

### C-20261017-5 · 2026-10-17 · Private names and machine paths generalised
- because: user request (public repository: no private project names, no person's name but the author credit, no machine paths; AGENTS.md)
- files: SKILL.md "Compose a model into a picture" (worked example); LEARNINGS.md L-003, L-006 (triggers and evidence); CHANGELOG.md C-20261012-1; references/figures-for-video.md ("Who stands where"); scripts/pw.py lineup hint; TESTS.md in all seven skills; tests/check_skills.py (new guards); tests/run_evals.py (switches off any installed polywright)
- Film and toy names, the owner's name in a ruling, a private skill's name and absolute drive paths became generic descriptions or "the owner's private notes"; the lessons are unchanged. check_skills.py now fails on any absolute drive path with two real segments and on the owner's private project names.

### C-20261017-4 · 2026-10-17 · targets.json advice for web-threejs, game-roblox, game-unity and video-blockout
- because: user request (each plugin carries 3D modelling knowledge for its topic and points to polywright); ../polywright-finish R-20261017-1, R-20261017-2, R-20261017-3; R-20261017-1
- files: references/targets.json advice lines (no rule numbers changed)
- web-threejs adds `--join-named false` to the optimize advice; game-roblox replaces the unverified texture limit with 4096 px uploads, a 1024 px ceiling and 256 px rigid-accessory maps, adds the emissive mask, and replaces "scale by 1/0.28" with studs or the Importer's Scale Unit; game-unity says what pw.py's FBX export writes and leaves the choice to a 1 m cube test, explains that `pw.py lods` files must be joined for an LOD Group, adds the 255-triangle convex hull limit and glTFast's own shaders; video-blockout adds building from the shot cameras and grey passes.

### C-20261017-3 · 2026-10-17 · references/film-and-video.md: models and blockouts for film and AI video
- because: user request (each plugin carries 3D modelling knowledge for its topic and points to polywright); R-20261017-1
- files: references/film-and-video.md (new); SKILL.md "Crowd and battle blockouts" (pointer); references/crowd-blockouts.md and figures-for-video.md (links)
- The 3D artist's side of a film shot: cameras first, detail by largest on-screen size, scale and lens checks, the passes a video model reads, set dressing, figures, and the pw.py commands; shot planning stays with cinewright.

### C-20261017-2 · 2026-10-17 · convert --level and --tilt-deg
- because: ../polywright-generate C-20261017-2
- files: scripts/pw.py convert, scripts/pw_bpy.py level_rotation and act_convert; references/cli.md
- Stands a leaning model on its convex hull's largest flat face near the bottom, or rotates by a given angle.

### C-20261017-1 · 2026-10-17 · cli.md: wall thickness in check, hollow-shell fill in printable
- because: ../polywright-print C-20261017-1 (R-20261017-1, L-004 there)
- files: references/cli.md (command table, output notes); scripts/pw.py, scripts/pw_bpy.py
- The command reference lists `check --thickness-samples/--no-thickness` and `printable --seal-mm/--hollow`.

### C-20261016-2 · 2026-10-16 · pw.py turnaround, mark, lineup; manifest --review; figures for video
- because: L-006, user request (fold the run's processes and scripts into polywright)
- files: SKILL.md (Crowd and battle blockouts, a closing paragraph), references/figures-for-video.md (new), references/cli.md (Commands), scripts/pw.py (cmd_turnaround, cmd_mark, cmd_lineup, manifest --review and in-folder paths, gen host hint), scripts/pw_bpy.py (act_turnaround, act_mark, act_lineup), tests/test_pw.py (four tests)
- Three commands from a run that turned four toy figures into video references: grey turnarounds, marking and colour fixes on generated textures, and a tabletop lineup with depth and team mask; the manifest records reviews and resolves outputs inside the asset folder.

### C-20261016-1 · 2026-10-16 · Pose passes leave out hidden face points; two-fighter previs recipe
because: L-005; user request ("update polywright with whatever would be helpful")
files: scripts/pw_bpy.py (`hidden_face_points`, act_crowd), scripts/pw.py (`draw_pose_frames`), references/crowd-blockouts.md ("Two fighters (previs)"), tests/test_pw.py
The crowd pose pass no longer draws a nose and eyes on figures seen from behind, and the drawer skips joints at (-1, -1); `--passes pose` alone no longer fails for want of its output folder. The reference gains the two-fighter previs route tested for a duel (IK mannequins, rigid and thickened blades, thrown props, end-state check).

### C-20261013-1 · 2026-10-13 · pw.py crowd and "Crowd and battle blockouts"
- because: user request (offload big battle and crowd scenes from video models to Blender); R-20261013-1; L-004
- files: SKILL.md description and new section "Crowd and battle blockouts"; references/crowd-blockouts.md (new); references/cli.md; scripts/pw.py (`crowd`, pose drawing, video encode, sheet); scripts/pw_bpy.py (`act_crowd`); tests/test_pw.py
- New command builds two armies of low-poly soldiers with offset walk cycles and renders depth, mask, clay and OpenPose passes plus camera.json for Wan VACE or Fun Control.

### C-20261012-1 · 2026-10-12 · pw.py match and "Compose a model into a picture"
- because: L-003 (a designed prop pasted into a film's set still from a camera solved from two pixels and a depth); polywright-blender L-004 (bpy option order)
- files: SKILL.md description and new section "Compose a model into a picture"; scripts/pw.py (`match`, `split_bpy_args`), scripts/pw_bpy.py (`act_match`); references/cli.md; tests/test_pw.py
- New command renders a model RGBA from a picture's camera, pastes it, and writes a blend mask; `pw.py bpy` takes its options on either side of the script name.

### C-20261011-2 · 2026-10-11 · Description says when to fire
- because: T-20261011-2 first pass (undertriggering: prompts answered without the skill; hub and finish both claimed game-readiness)
- files: SKILL.md frontmatter description, evals/evals.json trigger-2
- Descriptions open with 'Use whenever ...' and name the requests each skill owns; the hub only takes requests no sibling owns.

### C-20261011-1 · 2026-10-11 · Created as an evergreen unit
- because: user request (an evergreen 3D modelling plugin); research R-20261011-1 to R-20261011-3
- files: SKILL.md, references/, RESEARCH.md, LEARNINGS.md, TESTS.md, evals/evals.json, evergreen.json
- Initial version, tier `fast`, interval 14d, written from the five research notes of 2026-10-11 and the verified runs logged in LEARNINGS.md.
