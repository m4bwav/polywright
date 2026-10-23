# Topology: meshes that bend, shade and texture well

What a mesh's edge flow must be before it is rigged, simulated, textured or exported, and how to check it.
Back to [SKILL.md](../SKILL.md). The rules follow *Squeaky Clean Topology in Blender* (Packt, 2023) and the
procedural-generation errors in Conlan's *The Blender Python API* (Apress, 2017), in our own words; the numbers
come from `pw.py inspect --topology` on real meshes (2026-10-22).

## Measure first

`pw.py inspect model.glb --topology` reports, on welded positions:

| Field | What it means | Fix |
|---|---|---|
| `tris`, `quads`, `ngons`, `quad_share` | face sides | n-gons: triangulate or quad them before a game export (each importer splits them its own way) |
| `poles` | interior vertices by edge count, other than four | judged on quad meshes only (`quad_share` 0.5 or more): five edges at most near a joint |
| `winding_mismatch` | edges two faces walk the same way: a flipped face | `pw.py convert in out --fix-winding` |
| `duplicate_faces` | faces on the same corners: double-sided copies or stacked faces | delete one; they z-fight and cost twice |
| `zero_area_faces`, `loose_edges`, `loose_verts` | debris from generation or booleans | merge by distance, delete loose |
| `uv_spread` (`uv_texel_p5`, `uv_texel_p95`) | texel density per face against the mesh's mean, area-weighted; 1.0 is even | re-unwrap or scale islands; more density only where a part deserves it |

`pw.py check` warns on these for the game, web and AR targets. On 22 real meshes: flipped faces in 9 of 13
image-to-3D outputs (recalculating normals cleared every one; `--fix-winding` did the same while keeping UVs),
a downloaded car with 479,007 of its 971,730 faces stacked on another (double-sided copies), and UV spread over
2.5 on 3 of 10 UV-mapped meshes (a UV sphere's poles, Suzanne, one car part). The 2.5 line is a starting guess,
not calibrated against a judged set.

## The first three checks

All quads where the mesh bends, no duplicate geometry, every face wound the same way. The other rules cannot be
judged until these pass.

## Edge loops

- A loop either closes on itself or ends at a boundary. It never crosses itself and never spirals down the mesh.
  A spiral comes from a one-face mismatch somewhere; it ruins bevels, UV seams and deformation.
- Where two grids meet, the corner vertices get five edges (a pole). Keep poles at five edges or fewer, and at
  least one row of faces away from any joint.

## Meshes that bend (rigged characters, creatures, cloth)

- Loops run around a limb, parallel to the axis it bends about, and sit denser on the outside of the bend than
  in the crease. Under a bend the faces should stretch into rectangles, not diamonds.
- A limb that twists (a forearm, a neck) needs enough loops along it, or it collapses like a candy wrapper.
- Cloth wants even, nearly square quads and enough of them. Simulate on a moderate mesh and put Subdivision after
  the Cloth modifier, never before (Pearson, *Learn Blender Simulations the Right Way*, agrees).
- Fewer triangles on a deforming mesh: merge loops only where nothing bends (the back, the side of the head) and
  push the triangles that result away from joints. Collapse decimation (`pw.py convert --max-tris`) is for static
  props; on a rigged mesh it scatters triangles through the joints.

## Hard surfaces

- Smooth shading across a 90 degree corner shades wrong. Bevel the edge, mark it sharp, or smooth by angle. In
  Blender 4.1 and later, Smooth by Angle is a Geometry Nodes modifier: export with modifiers applied
  (`export_apply=True` for glTF, `use_mesh_modifiers=True` for FBX) or write the sharp edges into the mesh with
  `mesh.set_sharp_from_angle(angle=...)`.
- On flat panels, loops that carry no shape only cost triangles: remove them.
- No coplanar overlapping faces in a kitbashed set or a blockout: they flicker in renders and in clay, depth and
  edge passes. Nudge one surface, delete the hidden one, or build without the overlap.

## UVs follow topology

Seams go on creases, hard corners and where grids meet. Jagged or spiralling loops make tiling textures
impossible. Check stretch and texel spread before baking: a part that deliberately gets more texels (a face, a
logo) is fine; everything else should sit near 1.0.

## Rigs for games

A Rigify rig is an animation rig, not a game skeleton: a generated human has 706 bones, 160 of them deform, and an
FBX export with `use_armature_deform_only` still came back with 278 (the deform bones' non-deform parents come
along; verified on Blender 5.2.1). Unity Humanoid and Roblox want a deform-only hierarchy: build one from the DEF
bones, or rig with the plain metarig, Mixamo or AccuRIG. Recipe `rigify-export` in
[../../polywright-blender/references/bpy-recipes-physics.md](../../polywright-blender/references/bpy-recipes-physics.md).
