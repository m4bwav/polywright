# Log

Append-only. Newest last.

## 2026-10-11

- Owner's request: an evergreen "ultimate 3D modelling" plugin that agents and other plugins call when they need a model of a real or imagined thing, for games, prints, AI video and business use; research forums, AI practice, academics, the latest and the time-honoured; Blender tooling; push the repo and do the modernisation steps.
- Five research agents wrote ai-docs/research (reality capture, generative 3D, Blender and tooling, craft and academics, AI agents and 3D). Originals with machine specifics are kept in the owner's private notes; the repository copies are generalised.
- Named the plugin polywright ("meshwright" is taken by two 3D projects). Design: decisions/2026-10-11-hub-and-contract.md.
- Built pw.py and pw_bpy.py, seven skills, references, companions and evals; tests (22 unit and Blender tests, ten recipes) pass with Blender 5.2.1 and with the bpy 5.2.2 wheel on Python 3.13.
- Proven end to end: a neighbourhood park and Central Park's Bethesda Terrace through `place` (bugs found and fixed: unclipped ways, inside-out terrain block dropped by the Manifold union, enclosing areas missing from box queries, multipolygon stitching, water over islands, lidar noise on water); a generated fountain (Z-Image reference, Hunyuan3D-2 mesh in 100 s, Roblox GLB passing check after UVs, watertight 80 mm print, 3MF accepted by Bambu Studio's CLI).
- Recipe tests caught two Blender 5.x changes the research missed: Workbench `show_shadows`, and multilayer EXR needing `media_type` first.
- Pushed to github.com/m4bwav/polywright (public). CI: structure on three OS x Python 3.9/3.14, a Blender job with the bpy 5.2.2 wheel (needed Mesa EGL: PR #1), and the budget; all green. Registered the seven units in the evergreen catalog; installed polywright@mark-local.
- Headless trigger evals (`claude -p`, fresh sessions, Skill calls as evidence): 17/28, then 23/28 after explicit descriptions (0.1.1); every decoy passed both times. On Windows, Python's subprocess needs the full path to `claude.cmd` (shutil.which); a bare "claude" fails with WinError 2 and looks like zero invocations.
- Action evals in a throwaway clone: print passed and found the flat-face tessellation problem (fixed with a guarded planar dissolve); capture ran pw.py correctly without loading the skill because the prompt named the command (prompt rewritten).
- Not tagged: tagging and publishing a release wait for the owner's go-ahead.

