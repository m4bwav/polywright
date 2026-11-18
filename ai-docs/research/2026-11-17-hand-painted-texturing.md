# Hand-painted texturing in Blender (2026-11-17)

Source video: Craft Reaper, "Complete Guide of Hand Painting Game Assets in Blender with Ucupaint" (https://www.youtube.com/watch?v=5nwoGU_ZmhY), read from its transcript. Tests ran headless in Blender 5.2.1 on a bevelled cube (256 px bakes).

## Bottom line: scores

| Candidate | Score | Reason |
|---|---|---|
| Bake margin, Extend | KEEP | margin 8 Extend reached exactly 8 px past islands (Adjacent Faces 9); margin 0 leaves background at seams. Manual default: 16, ADJACENT_FACES. |
| Curvature from Bevel-normal difference | KEEP | range 0 to 0.65, edges only; already recipe `edge-wear-mask`. |
| Cycles Pointiness | DROP | 0.57 to 0.58 on a low-poly prop: per-vertex, needs dense mesh. |
| Local AO bake (`only_local`) | MAYBE | all white on a convex prop; useful only on crevices and stacked parts. |
| Masks from selected faces | KEEP | FACE float attribute + Attribute node; 11.9% of texels on the top face, as expected. |
| Top-light gradient (object Z) | KEEP | from 80.lv workflows; 0 to 1 cleanly. |
| Colour variants rebaked | KEEP | Hue/Saturation over the baked albedo, baked again (Hue 0.5 = no shift). |
| Standard view transform | KEEP | one line; Standard applies no tone curve (inference; manual gives no reason). |
| Unlit (emission) preview | MAYBE | EEVEE render of emission works; it is a preview habit, not a script. |
| Quick Edit to Krita (`image.project_edit`) | DROP for headless | poll needs a 3D viewport; UI-only. |
| Ucupaint | KEEP (optional) | Tested 2026-11-17 after install: see R-20261117-3 and recipe handpaint-ucupaint. Was MAYBE: | GPL-3.0-or-later, 3.0.2 (2026-11-16), repo ucupumar/ucupaint, Blender >= 4.2. Source shows `wm.y_quick_ypaint_node_setup`, `wm.y_new_layer`, `wm.y_new_layer_mask`, `wm.y_bake_to_layer`, `wm.y_bake_channels` run without a viewport; not installed or tested here (installing changes the user's Blender). |

Built: recipe `handpaint-base` in skills/polywright-blender/references/bpy-recipes-motion.md and a route line in polywright-finish. No pw.py subcommand: one recipe covers it.

## Other workflows (80.lv, 2025)
- Thomas Severi, tavern (2025-11-03): texel density checker, top-down light gradient painted into albedo, Color Dodge light layers, mid saturation/value base colours, warm light cool shadow, 70-20-10 detail rule, mirrored UVs painted then baked to unique UVs, scene AO baked on the floor.
- Cherylynn Lima, stylized character (2025-02-14): paint AO, then highlights, then mid-tones; leave some light to scene lights; fake Fresnel via Color Ramp bands in EEVEE.

## Full findings with sources
# Hand-paint pipeline research findings (checked 2026-11-17)

All claims checked 2026-11-17. Blender docs at docs.blender.org/.../latest are the **5.3** manual and API.

## 1. Ucupaint

- The real repo is **github.com/ucupumar/ucupaint**. `ucupaint/ucupaint` does not exist (git clone returned "Repository not found"). Source: `gh search repos ucupaint`.
- The licence is GPL-3.0-or-later (`license = ["SPDX:GPL-3.0-or-later"]` in blender_manifest.toml; COPYING file in the repo). https://github.com/ucupumar/ucupaint/blob/master/blender_manifest.toml
- Latest version: **3.0.2, released 2026-11-16**. Earlier releases: 3.0.1 on 2026-11-01 and 3.0.0 on 2026-10-23 (`gh release list -R ucupumar/ucupaint`). On the extensions page 3.0.2 is dated Nov 16, 2026, has about 328k downloads, and adds an OpenGL/DirectX normal-map option. https://extensions.blender.org/add-ons/ucupaint/
- Blender support: the manifest sets `blender_version_min = "4.2.0"` and gives **no `blender_version_max`**, so Blender 5.2 and 5.3 are allowed. I did not find an explicit statement that it was tested on 5.2 or 5.3. The extensions page says "4.2 LTS and newer". For Blender older than 4.2, the GitHub release zip is used (it supports back to 2.76; bl_info says 2.80).
- Installing:
  - The extension zip from extensions.blender.org can be installed with `blender --command extension install-file -r REPO [-e] FILE`.
  - From the online repo: `blender --command extension sync`, then `blender --command extension install [-s] [-e] ucupaint`. `-s` syncs first and `-e` enables the extension.
  - Source: https://docs.blender.org/manual/en/latest/advanced/command_line/extension_arguments.html
  - The extension id is `ucupaint`, so in bpy it is `bl_ext.<repo>.ucupaint`. The `bl_ext` part is an inference from Blender's extension naming.
- Operator idnames: all are `wm.*`. I confirmed them by grepping the source at master, 2026-11-17.
  - `wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')` creates the material and the Ucupaint node stack. Poll: `context.object` only (Root.py:312).
  - `wm.y_add_new_ypaint_node`: poll needs `space_data.type == 'NODE_EDITOR'`, so it is **not usable headless**. Use quick setup instead.
  - `wm.y_new_layer(name=, type=, uv_map=, add_mask=, mask_type=?, mask_uv_name=)`. Layer types: IMAGE, BRICK, CHECKER, GRADIENT, MAGIC, MUSGRAVE, NOISE, VORONOI, WAVE, VCOL, BACKGROUND, COLOR, GROUP, HEMI, GABOR, EDGE_DETECT, AO. Poll: `get_active_ypaint_node()`, which looks at the active object's active material (Layer.py).
  - `wm.y_new_layer_mask`: poll returns True (Mask.py). Mask types: IMAGE, BRICK, CHECKER, GRADIENT, MAGIC, MUSGRAVE, NOISE, VORONOI, WAVE, VCOL, HEMI, OBJECT_INDEX, COLOR_ID, BACKFACE, **EDGE_DETECT**, MODIFIER, GABOR, **AO**.
  - EDGE_DETECT and AO masks are live shader nodes (Mask.py:230-233). There is also `wm.y_fix_edge_detect_ao`. These nodes do not exist in a baked texture until they are baked.
  - `wm.y_bake_to_layer` and `wm.y_bake_entity_to_image` bake data to a layer or mask. Bake types: AO, POINTINESS, CAVITY, DUST, PAINT_BASE, BEVEL_NORMAL, BEVEL_MASK, MULTIRES_*, OTHER_OBJECT_*, SELECTED_VERTICES, FLOW, OBJECT_SPACE_NORMAL, THICKNESS, WIREFRAME, CURVATURE. Poll: active Ucupaint node and `context.object.type == 'MESH'`.
  - **"Bake all" / merge to one image**:
    - `wm.y_bake_channels` ("Bake channels to Image", Bake.py:1666) bakes every channel's layer stack into one image per channel.
    - `wm.y_bake_all_targets` ("Bake Ucupaint Node") bakes into bake targets.
    - `wm.y_merge_layer` merges a layer with its neighbour, and `wm.y_merge_mask` merges masks.
    - `wm.y_save_all_baked_images` saves the baked images.
    - Polls for these: Ucupaint node plus a mesh object. y_merge_layer also needs at least one layer.
  - Headless status:
    - Ucupaint's own test, tests/test_quicksetup.py, drives these operators through plain `bpy.ops` calls. Examples: `bpy.ops.wm.y_new_layer(name='Solid Color', type='COLOR', uv_map='UVMap', add_mask=True, mask_uv_name='UVMap')` and `y_open_image_as_layer`.
    - None of the polls listed above needs a 3D viewport. The exception is y_add_new_ypaint_node, which needs the node editor.
    - Baking uses Cycles bake and should run in background mode. I did not run this myself.
    - `get_active_ypaint_node()` reads `bpy.context.window_manager.ypui`, which exists when the add-on is enabled.

## 2. Cycles bake settings, Pointiness, AO, Bevel (manual 5.3)

- Margin: "Type: Extend (extend border pixels outwards) / Adjacent Faces (fill margin using pixels from adjacent faces across UV seams); Size in pixels". https://docs.blender.org/manual/en/latest/render/cycles/baking.html
- bpy:
  - `scene.render.bake.margin` is an int in [0, 32767], **default 16**.
  - `scene.render.bake.margin_type` has the values `'ADJACENT_FACES'` (**default**) and `'EXTEND'`.
  - Sources: https://docs.blender.org/api/current/bpy.types.BakeSettings.html and https://docs.blender.org/api/current/bpy_types_enum_items/bake_margin_type_items.html
- Pointiness is an output of the Geometry node and is marked **"Cycles Only"**: "approximation of the curvature of the mesh per vertex. Lighter = convex, darker = concave." It is vertex based, so it depends on mesh density. https://docs.blender.org/manual/en/latest/render/shader_nodes/input/geometry.html
- Ambient Occlusion node:
  - Settings: Samples, Inside, and Only Local (Cycles only).
  - bpy: `ShaderNodeAmbientOcclusion.only_local` (bool), `.inside` (default False), and `.samples` (in [1, 128], default 16).
  - Sources: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/ao.html and https://docs.blender.org/api/current/bpy.types.ShaderNodeAmbientOcclusion.html
- Bevel node is Cycles only and has a Normal output. bpy: `ShaderNodeBevel.samples` in [2, 128], default 4. https://docs.blender.org/manual/en/latest/render/shader_nodes/input/bevel.html and https://docs.blender.org/api/current/bpy.types.ShaderNodeBevel.html
- 5.x renames: none found for these nodes or properties in the current docs.

## 3. Color management views (manual 5.3)

- The page has moved. It is now https://docs.blender.org/manual/en/latest/render/color_management/displays_views.html (the old color_management.html returns 404).
- Views listed:
  - Standard: "Does no extra conversion besides the conversion for the display. Often used for non-photorealistic results".
  - ACES 1.3 and ACES 2.0 (new).
  - Khronos PBR Neutral.
  - AgX.
  - Filmic: "**deprecated**, superseded by AgX". It is still listed.
  - Filmic Log, False Color, and Raw.
- bpy: `scene.view_settings.view_transform` is a dynamic enum built from the OCIO config, so the API page shows only 'NONE'. https://docs.blender.org/api/current/bpy.types.ColorManagedViewSettings.html
  - The value strings are the display names: `'Standard'`, `'AgX'`, `'Khronos PBR Neutral'`, `'Filmic'`, `'ACES 1.3'`, `'ACES 2.0'`, `'False Color'`, `'Raw'`.
  - These names are inferred from the manual labels. Confirm them with `[i.identifier for i in scene.view_settings.bl_rna.properties['view_transform'].enum_items]`.
- Why texture painting uses Standard: **not stated in the manual (not found)**. My inference from the manual's definition: Standard applies no tone curve, so painted sRGB albedo displays as stored. AgX and Filmic desaturate and compress the colour, so the colours you pick in the viewport would not match the colours in the texture file.

## 4. Quick Edit (project_edit / project_apply)

- `bpy.ops.image.project_edit` and `project_apply` are Python operators in scripts/startup/bl_operators/image.py. https://raw.githubusercontent.com/blender/blender/main/scripts/startup/bl_operators/image.py
- **`image.project_edit`**:
  - It calls `bpy.ops.paint.image_from_view()` (the viewport snapshot).
  - It saves the snapshot as PNG (EXR if float), next to the .blend or in the temp dir, as `<blend>_<object>.png`.
  - It then calls `image.external_edit(filepath=)`.
  - `external_edit` uses **`context.preferences.filepaths.image_editor`**. If that is empty it falls back to `start` on Windows, `open` on macOS and `gimp` on Linux.
  - The pref is documented as "Path to an image editor (default '')" at https://docs.blender.org/api/current/bpy.types.PreferencesFilePaths.html
- **`paint.image_from_view` poll** (source/blender/editors/sculpt_paint/mesh/paint_image_proj.cc:6558):
  - It needs a screen with a big **3D viewport area** ("No 3D viewport found to create image from").
  - It returns false when `G.background || !GPU_is_init()`.
  - So **Quick Edit cannot run headless (`blender -b`)**. It needs a GUI session with a 3D view.
- **`image.project_apply`**:
  - It reloads the image named in the class-level `_proj_hack`, so it only works in the same session after project_edit.
  - It then calls `bpy.ops.paint.project_image(image=name)`.
  - `PAINT_OT_project_image` has no poll. Its exec needs an active mesh object with UVs, a material and a paint slot, plus the image.
  - It projects using the view stored in the snapshot image's properties. This last point is an inference from the "Project Image" description and the exec code.
- Manual: "Quick Edit: Edit a snapshot of the viewport in an external image editor. Apply: Project edited image back onto the object. Apply Camera Image: Project an edited render from the active camera." https://docs.blender.org/manual/en/latest/sculpt_paint/texture_paint/tool_settings/options.html

## 5. Masks from selected faces

- **Ucupaint**:
  - Bake type `SELECTED_VERTICES` ("Selected Vertices/Edges/Faces", common.py:430). Use it via `wm.y_bake_to_layer(type='SELECTED_VERTICES', target_type='MASK')`.
  - It requires **Edit Mode** (bake_common.py:4243 says "Should be in edit mode!"). A MASK target needs an active layer.
  - Alternatives: COLOR_ID masks (flat colour ID vcol) and VCOL masks.
  - Source: ucupumar/ucupaint at master.
- **Native**:
  - Face Selection Masking in Texture, Vertex and Weight Paint (header button; bpy `mesh.use_paint_mask`). Painting affects only the selected faces. Vertex Selection Masking (`use_paint_mask_vertex`) works in Vertex and Weight Paint only. https://docs.blender.org/manual/en/latest/sculpt_paint/selection_visibility.html and https://docs.blender.org/api/current/bpy.types.Mesh.html
  - Edit Mode > Mesh > **Set Attribute** writes a value to the selected elements. You can write a face or corner color attribute, then use it as a mask through the Attribute node. https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/set_attribute.html
  - Stencil Mask (an image mask) and Cavity Mask (vertex-based) are paint-mask options. https://docs.blender.org/manual/en/latest/sculpt_paint/texture_paint/tool_settings/mask.html

## 6. Other recent hand-painted workflows: techniques not in our list

- 80.lv, "Using hand painting techniques to texture a D&D-inspired tavern", Thomas Severi, **2025-11-03** (Blender + 3DCoat + Photoshop). https://80.lv/articles/using-hand-painting-techniques-to-texture-a-d-d-inspired-tavern
  - Texel density checked with the **Texel Density Checker** add-on (px/m); objects sharing a texture set are atlased.
  - **Light-to-dark top-down gradient** painted into albedo. Light is painted with Color Dodge layers, and **no normal maps** are used.
  - Base colours stay at mid saturation and mid value, avoiding a "forbidden zone" of the colour wheel. Lights are warm and shadows cool.
  - The **70-20-10 rule** sets detail density.
  - **Mirror-and-rebake**: mirrored UVs are painted once, then baked onto unique UVs to break the symmetry.
  - Scene AO is baked onto the floor to give contact shadows under the furniture.
  - Tiling planks get detail variation, and floors and walls get lowered contrast so they recede.
  - Unlit check: the texture goes into Base Color + Emission, with roughness 1.
- 80.lv, "How to enhance hand painting with Blender shaders for stylized character art", Cherylynn Lima, **2025-02-14**. https://80.lv/articles/how-to-enhance-hand-painting-with-blender-shaders-for-stylized-character-art
  - Paint AO first, then highlights on protruding forms, then mid-tones to bridge the two.
  - Paint only part of the lighting into the texture and leave the rest to scene lights.
  - **UV direction drives anisotropic shine**: UVs are set by hand to horizontal, vertical or diagonal, and hair cards are unwrapped as strips all facing one way.
  - **Fake Fresnel in EEVEE**: a Fresnel/Facing term goes through a Color Ramp to make bands in Base Color.
  - Sun light for key light plus Area lights for hard rim light.
- Polycount wiki hand-painted guidance: not checked (not found within budget).
- Blender Studio 2024-2026 hand-painted workflow: not found.
