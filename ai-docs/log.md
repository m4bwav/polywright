# Log

Append-only. Newest last.

## 2026-10-11

- Owner's request: an evergreen "ultimate 3D modelling" plugin that agents and other plugins call when they need a model of a real or imagined thing, for games, prints, AI video and business use; research forums, AI practice, academics, the latest and the time-honoured; Blender tooling; push the repo and do the modernisation steps.
- Five research agents wrote ai-docs/research (reality capture, generative 3D, Blender and tooling, craft and academics, AI agents and 3D). Originals with machine specifics are kept in the owner's private notes; the repository copies are generalised.
- Named the plugin polywright ("meshwright" is taken by two 3D projects). Design: decisions/2026-10-11-hub-and-contract.md.
- Built pw.py and pw_bpy.py, seven skills, references, companions and evals; tests (22 unit and Blender tests, ten recipes) pass with Blender 5.2.1 and with the bpy 5.2.2 wheel on Python 3.13.
- Proven end to end: a neighbourhood park and Central Park's Bethesda Terrace through `place` (bugs found and fixed: unclipped ways, inside-out terrain block dropped by the Manifold union, enclosing areas missing from box queries, multipolygon stitching, water over islands, lidar noise on water); a generated fountain (Z-Image reference, Hunyuan3D-2 mesh in 100 s, Roblox GLB passing check after UVs, watertight 80 mm print, 3MF accepted by Bambu Studio's CLI).
- Recipe tests caught two Blender 5.x changes the research missed: Workbench `show_shadows`, and multilayer EXR needing `media_type` first.
