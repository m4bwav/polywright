# Changelog

Plugin versions. Reasoned changes per skill are in each `skills/<name>/CHANGELOG.md`.

## Unreleased

- `pw.py duel`: a two-fighter previs for AI video controls. A JSON file names the set (a `.blend`, a room script or a floor), the shot's camera, two fighters with marks, facing and poses keyed in seconds (a built-in pose library plus your own, base plus overrides), blades on the wrists and thrown props. Each frame it renders clay, a Canny of the clay, inverse depth with real and with thick blades, and COCO-18 skeletons with face points turned from the lens left out, then one `<name>_<pass>.mp4` per pass and a sheet at chosen seconds; it warns when a fighter's end state is out of frame. `--check` validates a file without Blender. Shared with `crowd`: the mannequin, the depth material, the skeleton drawer (now capped in width, and hidden ankles no longer skew it), the video encoder and the sheet (now labelled). Example `skills/polywright/examples/duel.json`.

## 0.2.1 (2026-10-17)

- `pw.py printable`: 0.2.0's hollow-shell fill also ran on solid models and terrain slabs (it counted the solid's own inside as air) and could leave them open: a park tile that was watertight in 0.1.2 came out with 393k triangles and boundary edges. Only air the outside reaches through the gaps counts now. `check --no-thickness` says it was skipped instead of "needs Blender".
- Six topic pages, each the 3D artist's side of a sibling plugin's subject (sources in each skill's RESEARCH.md, R-20261017): polywright-finish `references/web-threejs.md` (threewright), `references/roblox.md` (roblox-agent) and `references/unity.md` (unity-agent); polywright `references/film-and-video.md` (cinewright); polywright-references `references/images-for-3d.md` (what an image-to-3D generator needs from a picture); polywright-print `references/supports-and-slicing.md` (orientation, supports, splitting, slicing from the modeller's side). Each skill's SKILL.md points at its page.
- `targets.json` advice (no rule numbers changed): web-threejs keeps named parts (`--join-named false`); game-roblox gets the verified texture sizes (4096 px uploads, 1024 px ceiling, 256 px rigid-accessory maps), the emissive mask and stud or Scale Unit export; game-unity says what pw.py's FBX export writes, how LOD files become an LOD Group, the 255-triangle convex hull limit and glTFast's own shaders; video-blockout builds from the shot cameras and keeps passes grey. engines.md: the 4,000-triangle Roblox accessory budget is verified. generators.md names Pixal3D's multi-view model.
- Private names and machine paths generalised across changelogs, lessons, a reference page, the hub skill and the `lineup` hint; `tests/check_skills.py` now also fails on absolute drive paths with two real segments (placeholders such as `D:/<folder>/` pass) and on the owner's private project names. `tests/run_evals.py` switches off any installed polywright plugin instead of one named marketplace.

## 0.2.0 (2026-10-17)

- `pw.py place`: buildings follow OpenStreetMap's Simple 3D Buildings. `min_height` and `building:min_level` lift a part off the ground (a print stands it on the ground), `building:part` areas replace their outline, and `roof:shape` gabled, hipped, pyramidal and skillion are built (other shapes mapped to the nearest) from `roof:height`, `roof:levels`, `roof:angle` or a 30 degree pitch; `counts.roofs` says what was built. A European old town: 229 buildings, 82 roofs.
- `pw.py convert --level`: stands a leaning model on its base, the largest flat face of its convex hull within 45 degrees of down (Pixal3D builds in the camera's frame and leans by the camera's elevation: the test fountain stood up by 17.7 degrees in 9 s). `--tilt-deg D` rotates by a known angle instead.
- `pw.py check`: with Blender found, print targets now measure wall thickness (inward rays from 20,000 area-weighted surface points, the 3D-Print Toolbox method) instead of reporting `min_feature` as unchecked; it warns when over 0.5% of the surface is thinner than the target's minimum and lists the thinnest spots. `--thickness-samples`, `--no-thickness`.
- `pw.py printable`: image-to-3D meshes that are thin double-walled shells came out hollow, with walls of 0.3 to 0.5 mm (found by the new check on a TRELLIS.2 figure). It now seals gaps up to `--seal-mm` (1 mm), floods the outside and fills what the outside cannot reach; `--hollow` keeps the old behaviour.
- `tests/run_evals.py`: runs the skills' eval cases headless with `claude -p` in a throwaway copy, with this checkout loaded and an installed polywright switched off, and grades on trace evidence. Trigger descriptions: polywright-blender names the removed OBJ importer, polywright-references excludes flat graphic patterns; polywright-generate's trigger-1 points at a real drawing (`tests/fixtures/dragon.png`).
- `pw.py lineup`: its closing hint and references/figures-for-video.md now say the looped still control freezes moving figures and doubles them (tested on a four-figure toy fight, 2026-10-17); pass `colour.png` as a guide frame instead. LEARNINGS L-006: taking an accessory off a TRELLIS.2 mesh piece by piece.
- `pw.py turnaround`, `pw.py mark`, `pw.py lineup`: real figures or toys as video references. `turnaround` renders eye-level views of a textured model on flat mid-grey (a video model's reference pictures); `mark` moves a generated texture's colour to measured photo values, erases a smeared painted marking on the head's front UV islands and stands a clean text mesh on the face, at real size; `lineup` stands a few figures on a table with teams on fixed sides and writes colour, clay, inverse depth, a team mask, screen boxes and looped control videos. Reference references/figures-for-video.md.
- `pw.py manifest`: `--review RENDER --verdict V` records a look; a relative `--add-output` path written from inside the asset folder resolves there. `pw.py gen` says how to reach a ComfyUI server on another port.
- `pw.py crowd`: an army blockout for AI video. Two sides of low-poly soldiers (spear, shield, helmet) with offset walk cycles march, advance, charge, clash or hold; per frame it renders inverse depth (one range per shot), a side mask, clay and OpenPose skeletons, then encodes one video per pass and writes camera.json and a contact sheet. Hub section "Crowd and battle blockouts", references/crowd-blockouts.md.
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
