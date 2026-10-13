# Changelog

Plugin versions. Reasoned changes per skill are in each `skills/<name>/CHANGELOG.md`.

## Unreleased

- `pw.py match`: render a model from an existing picture's camera (fixed lens, horizon row, an anchor pixel at a depth, an exact aim pixel), RGBA; with `--still` it also pastes the render and writes a blend mask (`--hide` boxes in front of the model, `--mask-add` for the hands). Hub section "Compose a model into a picture".
- `pw.py bpy SCRIPT --blend X`: options written after the script name went to the script; they now reach pw.py.
- polywright-blender: tested recipe for a designed prop from a written description; polywright-references: Step 2b, sheets from the model.

## 0.1.2 (2026-10-11)

- `pw.py printable`: an open surface lying on the ground (a terrain sheet) was crushed by the base clamp after the inward wall pushed it below zero; the model now sits on the ground again before the clamp. The planar dissolve runs on a 100k-triangle copy and is kept only when it watertightly halves that copy (minutes became seconds; organic models keep full detail).
- `pw.py --version` printed 0.1.0 in 0.1.1; it now matches plugin.json, and `tests/check_skills.py` fails when they differ.
- Both found by the wiki's verification run against the published 0.1.1.
- `pw.py gen --workflow` takes workflows saved by ComfyUI's editor (template files) and converts them with the host's node definitions; `--save-api` writes the graph sent; a rejected graph prints ComfyUI's node_errors. Pixal3D ran through the unmodified TRELLIS.2/Pixal3D template on a 16 GB card in 331 s.
- `check` names its backend when Blender inspected the file; `place` rounds `center`.

## 0.1.1 (2026-10-11)

- Skill descriptions say when to fire; the hub only takes requests no sibling owns. Headless trigger evals went from 17/28 to 23/28 with every decoy passing (each skill's TESTS.md, T-20261011-2).
- `pw.py printable` merges coplanar faces after the remesh (undone when it breaks the solid): two plain boxes went from 381k to 488 triangles; `--no-planar` keeps the old output.
- CI: Mesa EGL so the Linux Blender job can render.

## 0.1.0 (2026-10-11)

First release.

- Seven evergreen skills: polywright (hub), polywright-references, -capture, -generate, -blender, -finish, -print.
- `pw.py`: doctor, inspect, render (contact sheet), convert, lods, printable, union, 3mf, check (ten targets in `targets.json`), new, manifest, bpy, gen (Hunyuan3D-2 built in, any ComfyUI API workflow), place (OpenStreetMap and USGS or terrain-tile elevation into a game scene and a print tile), texture.
- Ten Blender 5.2 recipes, each run by `tests/test_recipes.py`.
- Research notes of 2026-10-11 in `ai-docs/research`.
