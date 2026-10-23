# bpy API traps (Blender 5.x)

What models trained on older Blender still write, and the 5.2 replacement. Back to [SKILL.md](../SKILL.md).
Verified on Blender 5.2.1 LTS (Python 3.13.13), Windows 11, 2026-10-11, by probing `bpy` directly unless a row
says otherwise. The developer docs sat behind a browser check that day; these come from the running program.

## Running

| Trap | Fact |
|---|---|
| a failed `--python` script exits 0 | add `--python-exit-code N`; verified: without it, `raise RuntimeError` exits 0 |
| startup file and user add-ons leak into runs | `--factory-startup` (or `read_factory_settings(use_empty=True)`) |
| `--python-expr` with quotes on Windows | write a script file; pass arguments after `--` |
| bpy wheel on the wrong Python | `pip install bpy` works only on the Python Blender bundles (3.13 for 5.2); macOS wheels are arm64 only, Linux x86_64 only |
| `gpu.platform.*` in background | call `gpu.init()` first |

## Import and export

| Old | 5.2 |
|---|---|
| `bpy.ops.import_scene.obj` / `export_scene.obj` | `bpy.ops.wm.obj_import` / `wm.obj_export` |
| `bpy.ops.import_mesh.stl` / `export_mesh.stl` | `wm.stl_import` / `wm.stl_export` (`global_scale`, `apply_modifiers`, `ascii_format`, `export_selected_objects`) |
| `bpy.ops.import_mesh.ply` | `wm.ply_import` / `wm.ply_export` |
| `wm.collada_import` / `wm.collada_export` | removed: convert through another tool |
| FBX | import: `import_scene.fbx` (Python) or `wm.fbx_import` (new C++); export stays `export_scene.fbx` |
| glTF | `import_scene.gltf` / `export_scene.gltf` (`export_format` GLB, `export_apply`, `export_draco_mesh_compression_enable`, `export_meshopt_compression_enable`) |
| USD | `wm.usd_import` / `wm.usd_export` (a `.usdz` path writes USDZ; `usdz_downscale_size`, `generate_preview_surface`) |
| 3MF | not built in; trimesh, a slicer, or an extension |
| `import_image.to_plane` | `image.import_as_mesh_planes`; reference empties: `object.empty_image_add` |

## Rendering

| Old | 5.2 |
|---|---|
| `BLENDER_EEVEE_NEXT` | `BLENDER_EEVEE` (engines: BLENDER_EEVEE, BLENDER_WORKBENCH, CYCLES) |
| `scene.display.shading.show_shadow` | `show_shadows` (learned 2026-10-11: AttributeError otherwise) |
| `render.opengl`, `view3d.view_all`, `screen.screenshot` headless | fail: no viewport; render with a camera and frame from bounds |
| Workbench cavity on a model in millimetres | `scene.display.matcap_ssao_distance` is in scene units: scale it to the model (about 4% of its radius) |
| `import bgl` | removed; `gpu` module |
| `image_settings.file_format = "OPEN_EXR_MULTILAYER"` straight away | set `image_settings.media_type = "MULTI_LAYER_IMAGE"` first; then `OPEN_EXR_MULTILAYER` is the only format allowed (the plain-image list no longer has it; caught by the recipe test 2026-10-11) |

Headless render times on a small scene (RTX 5060 Ti): Workbench about 1 s, EEVEE about 10 s on first run
(shader compile), Cycles OptiX about 2 s.

## Materials

Principled BSDF sockets in 5.2 (32): Base Color, Metallic, Roughness, IOR, Alpha, Thin Wall, Normal, Weight,
Diffuse Roughness, Subsurface Weight / Radius / Scale / IOR / Anisotropy, Specular IOR Level, Specular Tint,
Anisotropic, Anisotropic Rotation, Tangent, Transmission Weight, Coat Weight / Roughness / IOR / Tint / Normal,
Sheen Weight / Roughness / Tint, Emission Color, Emission Strength, Thin Film Thickness, Thin Film IOR.
Gone: `Specular`, `Subsurface`, `Transmission`, `Emission`, `Clearcoat`. `material.use_nodes` is deprecated
in 5.0 (new materials have node trees).

## Animation

`action.fcurves` is gone since 5.0: actions have `layers`, `slots` and channelbags. Use
`anim_utils`-style helpers or keyframe through `obj.keyframe_insert(data_path=..., frame=...)`.

## Geometry Nodes

Modifier inputs in 5.2: `mod.properties.inputs.Socket_2.value = 4.0` works; `mod["Socket_2"] = x` raises
TypeError; `mod.properties.inputs.Socket_2 = x` is read-only. Find identifiers with
`node_group.interface.new_socket(...).identifier` or by listing `mod.properties.inputs`. Node type ids change
between versions: introspect `bpy.types` rather than recall.

## Modifiers and operators

- Enums (5.2): Boolean solver FLOAT, EXACT (default), MANIFOLD; Remesh mode BLOCKS, SMOOTH, SHARP, VOXEL;
  Decimate COLLAPSE, UNSUBDIV, DISSOLVE. Corrective Smooth is `CORRECTIVE_SMOOTH`. Read enums; do not guess.
- MANIFOLD needs manifold, outward operands and **silently skips** ones it cannot use; compare the result's
  bounds with the inputs' and fall back to EXACT (pw.py union does). An inside-out operand is enough to lose
  everything (learned 2026-10-11 on a terrain block).
- Solidify with `use_even_offset=True` makes long spikes at sharp corners (Blender issue 110057): use even
  offset off, `thickness_clamp=1.0`, `offset=-1` for printing.
- Voxel remesh memory grows with (size / voxel)^3: scale to the final size before choosing the voxel; never
  remesh at scene scale.
- glTF and STL imports split vertices per face; topology checks must weld coincident positions first (pw.py
  inspect does), or every closed mesh looks open.
- `object.mode_set`, `mesh.select_all`, `uv.smart_project`, `object.quadriflow_remesh`, `object.bake` work
  headless with an active object.
- mathutils `Vector` is float32: compare its components to float64 bounds with a tolerance.

## Code from 2.7x-era books and tutorials

Calls that books written for Blender 2.78 (Conlan's *The Blender Python API*, 2017, among them) teach, and
models still copy. Each row probed on 5.2.1, 2026-10-22.

| Old | 5.2 |
|---|---|
| `obj.select = True` | `obj.select_set(True)`; the attribute is gone |
| `scene.objects.active = obj` | `bpy.context.view_layer.objects.active = obj` |
| `primitive_cube_add(radius=1)` | `size=` (radius raises TypeError) |
| `modifier_apply(apply_as="DATA", modifier=m)` | `modifier_apply(modifier=m)` (apply_as raises TypeError) |
| `mesh.uv_textures` | `mesh.uv_layers` |
| `scene.update()` | `view_layer.update()` |
| `bpy.app.handlers.scene_update_post` | `depsgraph_update_post` (`frame_change_post` still exists) |
| `mesh.use_auto_smooth`, `auto_smooth_angle` | gone since 4.1: `object.shade_auto_smooth(angle=...)` adds a Smooth by Angle Geometry Nodes modifier (export with `export_apply=True` / `use_mesh_modifiers=True`, or apply it), or `mesh.set_sharp_from_angle(angle=...)` writes sharp edges into the mesh (64 on a 32-sided cylinder at 30 degrees) |
| `scene.use_nodes = True`, `scene.node_tree` (compositor) | `scene.node_tree` is gone: `bpy.data.node_groups.new(name, "CompositorNodeTree")`, then `scene.compositing_node_group = it`. No Composite node: the render itself is the final image |
| File Output node `file_slots` / `layer_slots` | `node.file_output_items.new("FLOAT" or "RGBA", name)`, `node.directory`, `node.file_name` (unset, files come out as `Unsaved<pass>`), `node.format.media_type` before `format.file_format` |
| `scene.sequence_editor.sequences` | `.strips` (and `.strips_all`) |
| `image_settings.file_format = "FFMPEG"` | set `image_settings.media_type = "VIDEO"` first (media types IMAGE, MULTI_LAYER_IMAGE, VIDEO) |
| Grease Pencil `GPENCIL` objects and the v2 data API | object type `GREASEPENCIL`; Line Art through `object.grease_pencil_add(type="LINEART_SCENE")`; strokes at `layer.current_frame().drawing.strokes` on the evaluated object |
| `GeometryNodeGeometryProximity` | `GeometryNodeProximity` |
| Random Value node `outputs[1]` / `outputs[2]` (one socket per type in 3.x) | one output whose type follows `data_type`; take `next(s for s in n.outputs if s.enabled)`, never an index |
| `transform_apply(scale=True)` "to apply the scale" | location and rotation default to True as well: the origin jumps to the world origin. Pass `location=False, rotation=False` (a rigid body's origin is its centre of mass; the recipe's box fell through the floor until this was fixed) |

Two rules from the same books that still hold: never select by index in a script others will run (indices
change between versions and after edits; select by position or attribute), and call
`bm.verts.ensure_lookup_table()` before indexing a bmesh. Leftover `name.001` datablocks from repeated runs go
with `bpy.data.orphans_purge(do_recursive=True)`.

## Extensions

`blender --command extension list|sync|install <id>`; `bpy.app.online_access` is False by default, so a sync
needs `--online-mode` (and the user's OK: it downloads). The 3D Print Toolbox is an extension since 4.2.
