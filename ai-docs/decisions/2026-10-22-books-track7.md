# Books track 7 rulings (2026-10-22)

Small calls made while building the Blender books' items into polywright. Source notes: the book-learnings folder, `blender-polywright.md`.

- J1. One-render passes stay a recipe (`passes-one-render`), not a rewrite of `crowd`, `duel` and `lineup`. The three passes take about 1.4 s a frame together (17 frames at 832x480: depth 9.1 s, mask 7.2 s, clay 7.5 s); one Cycles render would save about a minute per 81-frame shot but would change the Workbench clay look that gets repainted into start frames.
- J2. Inverse depth in the recipe comes from a shader AOV (1 / view depth over one range), the same signal `crowd` renders, so the open question "does Mist do as well as inverse depth on H3" does not block anything. It stays open and is written as untested.
- J3. Topology rules in targets.json are warnings only. Pole valence is reported but not a target rule: every real game or AI mesh checked was triangles, so poles cannot be judged on them; the rule judges only meshes with half or more quads.
- J4. The UV spread line (2.5) is uncalibrated: 3 of 10 real UV-mapped meshes went over it. Published beside the rule.
- J5. `convert --fix-winding` orients faces on welded positions and flips the minority by area per part instead of merging vertices and recalculating, so UVs and split normals stay.
- J6. Scatter reserves hold still and get no skeletons; a side whose rear holds the camera gets none.
- J7. The animation principles (wind-up, offset limbs, moving holds, arcs, overlap, timing by mass) are written as untested proposals in crowd-blockouts.md and cinewright's previs-animation entry, not built into `duel`: no video model test backs them yet.
- J8. Not built: Boids (rule names exist, behaviour unchecked), motion tracking headless, a `--lines` pass in `crowd` and `duel` (Line Art renders; whether H3's edge control likes it is unknown), Mantaflow. Line Art and the bakes are recipes.
- J9. The recipes were split into two files (scenes 3.0k tokens, physics 1.8k) after one file reached 4,748 tokens, past the 3,500 reference line.
