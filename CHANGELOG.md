# Changelog

Plugin versions. Reasoned changes per skill are in each `skills/<name>/CHANGELOG.md`.

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
