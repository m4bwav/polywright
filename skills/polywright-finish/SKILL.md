---
name: polywright-finish
description: "Use whenever a mesh must be made ready for a game engine, the web or AR: is it game-ready, too many polygons, LODs, retopology, UVs, baking, PBR and normal-map conventions, collision, rigging, and axis, unit and format export for Roblox, Unity, Unreal, Godot, three.js (meshopt, KTX2), USDZ and video blockouts. Use on 'is this game-ready', 'make this work in Roblox/Unity', 'optimise for the web', 'reduce polygons', 'add LODs', 'retopologise', 'bake normals', 'imports sideways or tiny', 'flip the normal map'. Printing is polywright-print. Also 'refresh polywright-finish'."
---

# polywright-finish

A mesh is finished when it passes its target's check, looks right in a render, and imports at the right size and
orientation. Back to the hub: [../polywright/SKILL.md](../polywright/SKILL.md). Engine details:
[references/engines.md](references/engines.md). Making and finishing for one engine, step by step:
[references/roblox.md](references/roblox.md), [references/unity.md](references/unity.md), [references/web-threejs.md](references/web-threejs.md).

## Step 1: measure, then decide

`pw.py inspect <file>` and `pw.py check <file> --target <t> --real-size-m X`. The failures say what to do:
too many triangles, no UVs, too many materials, wrong size, open edges. Render before and after every
destructive step (`pw.py render`).

## Step 2: scale, orientation, pivot

- Real size in metres: `pw.py convert in out --size-m X --ground --center` (longest side to X; use a known
  dimension for odd shapes). A door is 2.0 to 2.1 m, a chair seat 0.45 m, a table 0.75 m, a person 1.7 to 1.8 m.
- Pivot at the bottom centre for props, at the hinge for doors, the axle for wheels, the grip for weapons.
- Axes: Blender +Z up and the front faces -Y; glTF +Y up and the front faces +Z; Unreal +Z up in centimetres;
  Unity +Y up left-handed; Roblox +Y up, 1 stud = 0.28 m. Test an export with a 1 m cube and a facing arrow
  when in doubt.

## Step 3: geometry for the target

| Need | Do |
|---|---|
| Fewer triangles, static prop | `pw.py convert --max-tris N` (collapse decimation keeps the silhouette); LODs with `pw.py lods` (about half per level) |
| Clean quads for deformation or sculpting | voxel remesh first (closes it), then QuadriFlow (recipe in polywright-blender), Instant Meshes, Quad Remesher (paid), or a hosted quad remesh; characters: by hand |
| Generated mesh (dense, lumpy, soft edges) | static prop: decimate and re-bake; hero or animated: retopology and re-bake; or regenerate with better references |
| Many parts that should be one | `--join`; for a solid, `pw.py union` |
| Collision | a box, capsule or convex hull per part; Unreal UCX_ prefix; Roblox CollisionFidelity Box or Hull; never the render mesh for moving objects |

## Step 4: UVs and textures

- UVs: `pw.py convert --uv` (Smart UV Project) for props; a second non-overlapping set for baked lightmaps
  (recipe); consistent texel density across a kit; trim sheets and atlases to cut materials and draw calls.
- Bake from the dense mesh to the low one: normal, AO, colour (recipe `bake-high-to-low`). Retopology destroys
  UVs, so always re-bake.
- PBR metal-rough: metalness 0 or 1, roughness carries the look, albedo never pure black or white; glTF packs
  occlusion, roughness, metalness into R, G, B (ORM).
- Normal maps: OpenGL (Y+) for Blender, Unity, Godot, glTF, three.js, Roblox; DirectX (Y-) for Unreal. Fix a
  mismatch by inverting green. Textures in powers of two; 1024 to 2048 per material for web and AR.

## Step 5: rig (when it moves)

A-pose input, clean manifold mesh. UniRig (MIT, local, 8 GB) or hosted Tripo, Meshy, AccuRIG (cleanest
humanoid weights), Mixamo (humanoid, best retarget docs). A 2026 comparison found Meshy's hip pivot 5 to 15 cm
off (feet slide) and AccuRIG importing once at 0.01 scale: check scale and pivot after rigging. Roblox: at most
4 bone influences per vertex, root at the origin.

## Step 6: export and verify

`pw.py convert` writes GLB, FBX, OBJ, USD/USDZ, STL. Per target:

| Target | Export | Then |
|---|---|---|
| game-roblox | FBX, OBJ or GLB per MeshPart, under 20k triangles, one material | `check --target game-roblox`; roblox-agent places it |
| game-unity | GLB (glTFast) or FBX `--fbx-bake-axes` | import test in the project (unity-agent) |
| game-unreal | FBX or GLB; Nanite for dense opaque meshes | scale check on import |
| web-threejs | GLB, then `gltf-transform optimize in.glb out.glb --compress meshopt --texture-compress ktx2 --join-named false` | gltf_validator; page check (threewright) |
| ar-usdz | `convert in.glb out.usdz` | `usdchecker --arkit` when usd-core is installed |
| video-blockout | GLB or .blend at real scale, plus turntables and depth/normal passes (recipes) | hand to the video plugin (cinewright) |
| commerce-gltf | GLB, real size, origin bottom centre, triangles only | `check --target commerce-gltf` |

Record each output: `pw.py manifest <dir> --add-output out/<file> --target <t> --inspect`.

## Maintenance

Evergreen unit, tier `moderate`. Companions: [RESEARCH.md](RESEARCH.md), [CHANGELOG.md](CHANGELOG.md),
[LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md) with `evals/evals.json`, [MAINTENANCE.md](MAINTENANCE.md),
state in `evergreen.json`. Read `evergreen.json` at each use; refresh when due.
