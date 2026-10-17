# Changelog: polywright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

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
- because: L-003 (a designed prop pasted into the No-God film's set still from a camera solved from two pixels and a depth); polywright-blender L-004 (bpy option order)
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
