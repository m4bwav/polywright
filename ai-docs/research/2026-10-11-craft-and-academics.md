# The craft and the academics of 3D modeling, for polywright

Research date: 2026-10-11. Scope: how expert modelers work, the foundational algorithms an agent must understand, target-specific requirements (games, 3D printing on a Bambu P1S, AI video, business), reference gathering, quality checks, practitioner wisdom, and the 2024-2026 research front.

Marking used below:
- **[verified 2026-10-11]** means a primary or official page was read today.
- **[secondary]** means a search snippet, vendor blog or forum, not the official source.
- **[known]** means long-standing textbook knowledge, not re-checked today.

Related: other polywright research notes in this folder; the project's ai-docs/HANDOFF.md.

## Bottom line

1. **Block out first, always.** Get scale, proportion and silhouette right with primitives at real-world size (metres) before any detail. Every expert workflow (hard surface, character, environment, print) starts here, and it is the cheapest point to catch errors.
2. **Pick the paradigm by target.** Use polygon or subdivision modeling for games, film and characters. Use CAD (B-rep) or code CAD for anything with dimensions, tolerances or mating parts (printed brackets, enclosures, STEP for business). Use sculpting for organic detail. Use procedural (Geometry Nodes) for variations. Use SDF or voxels for blobby or printed organic shapes.
3. **For an agent, code is the reliable modeling hand.** Blender Python with modifiers, CadQuery or build123d, and OpenSCAD are all inspectable and repeatable. LL3M (arXiv 2508.08228), StepCAD (2610.03799) and ViSculpt (2608.24169) all show agents writing modeling code and checking renders. Generated meshes from image-to-3D are a starting point, not an end product.
4. **Topology serves the use.** Static props for games may be triangulated and need only clean shading. Characters that deform need quad loops around joints, eyes and mouth. Print meshes need only to be watertight and manifold, and edge flow does not matter there.
5. **Respect each engine's axes and units.** glTF is right-handed, +Y up, front faces +Z, 1 unit = 1 m [verified]. Unreal is Z-up, centimetres. Roblox 1 stud = 28 cm [verified]. Blender is Z-up, metres. Export with an explicit axis conversion and test with a 1 m cube and a facing arrow.
6. **Normal maps: OpenGL (Y+) for Blender, Unity, Godot, glTF, three.js and Roblox. DirectX (Y-) for Unreal.** Roblox says it accepts only OpenGL tangent-space maps [verified]. Bake with MikkTSpace and export with the same tangents.
7. **PBR metal-rough is the lingua franca.** In glTF, metalness is in B, roughness in G, occlusion in R (ORM) [known, spec]. Metalness is 0 or 1 except on blends [verified, Khronos 3DC]. Keep albedo out of pure black and pure white.
8. **Budgets (Oct 2026):** Roblox caps a single mesh at 20,000 triangles per its specification page [verified; vendors say 21k]. Unreal Nanite removes manual LODs for opaque and masked static and skeletal meshes, but not translucent ones or morph targets [verified, UE 5.8 docs]. Apple AR Quick Look baseline stays about 100k polygons with one set of 2048 textures [secondary, Apple DTS 2021]. Khronos 3D Commerce wants 1:1 real size, origin at bottom centre and triangles only [verified].
9. **3D print rules for a 0.4 mm nozzle:** walls at least 2 perimeters (about 0.9 mm), better 1.2 to 1.6 mm. Overhangs up to about 45 degrees unsupported. Moving-part clearance at least 0.3 mm. Chamfer rather than fillet on bed-facing edges [verified, Prusa]. The P1S build volume is 256 x 256 x 256 mm [secondary].
10. **References are part of the product.** Generate orthographic front, side and back views on a shared ground line with a height bar, plus material callouts and a scale reference. Put them on a PureRef board and on Blender reference-image empties. Generated images drift between views, so check every view against the front.
11. **Self-check by rendering.** Render a fixed set of views (front, side, top, three-quarter, silhouette in flat black, wireframe, matcap, checker UV, normals) and critique them against the references before saying done. Every agentic 3D paper in 2025-2026 uses some version of this loop.
12. **Experts are sceptical of AI meshes.** Polycount and r/3Dmodeling threads (2026) say AI models lack intentional edge flow and form understanding. They are usable as blockouts or sculpt bases, and need retopology, UVs and rebaking for production [secondary].
13. **Use the research front selectively.** Artist-mesh generators (MeshAnything, Meshtron, DeepMesh, QuadGPT), learned UV seams (PartUV, SeamCrafter, MeshQuery) and learned simplification exist. Classical tools (QEM decimation, Instant Meshes or QuadriFlow, Blender's unwrappers, voxel remesh) remain the dependable defaults.

## 1. Modeling paradigms and when experts pick each

| Paradigm | What it is | Experts pick it for | Avoid when |
|---|---|---|---|
| Polygon / box modeling | Direct editing of vertices, edges and faces from a primitive | Game props, low poly, stylised assets, environment pieces, retopology | You need exact dimensions with fillets and mates (use CAD) |
| Subdivision surface (SubD) | Low cage plus Catmull-Clark smoothing, held by support loops or creases | Smooth hard surface high polys, characters, film | Final game mesh (too dense), parts needing CAD precision |
| NURBS / CAD (B-rep) | Exact parametric surfaces with a feature history (sketch, extrude, fillet) | Products, mechanical parts, printing with tolerances, STEP interchange | Organic characters, game-ready topology |
| Code CAD / CSG / parametric | Boolean trees of primitives driven by parameters (OpenSCAD, CadQuery, build123d) | Agents. Repeatable, diffable, parametric printable parts | Organic shapes |
| Digital sculpting | Dynamic topology or multires brushes on millions of polys (ZBrush, Blender Sculpt) | Organic detail, characters, creatures, high poly for baking, miniatures | Final game topology (needs retopology) |
| Procedural / node-based | Geometry Nodes, Houdini SOPs: graphs that generate geometry | Variations (rocks, buildings, cables, scatter), level kits, anything repeated | One-off hero shapes |
| Implicit surfaces / SDF | Distance functions blended smoothly, meshed by marching cubes or dual contouring | Organic blends, printable sculptural forms, raymarching, AI pipelines | Low poly game meshes without retopology |
| Voxels | Grid of filled cells | Stylised voxel art (MagicaVoxel), remeshing, booleans on messy meshes | Smooth surfaces at low cost |
| Kitbashing | Assembling prebuilt parts | Concept blockouts, sci-fi greebles, fast iteration | When licensing of the kit is unclear |
| Photogrammetry / scanning / splats | Mesh or Gaussian splat from photos | Real objects, environments, digital twins, scan-based textures | Clean topology needs (always retopo), shiny or transparent objects |

Agent rule of thumb: decide the target first, then the paradigm. A printable phone stand is code CAD. A Roblox sword is low poly polygon modeling. A creature for a film is a sculpt plus retopology. A forest is procedural scatter of a few hero assets.

### Classic texts and courses [known]

- Botsch, Kobbelt, Pauly, Alliez, Levy, *Polygon Mesh Processing* (AK Peters, 2010). The standard reference for data structures, smoothing, parameterization, remeshing, simplification and repair.
- Akenine-Moller, Haines, Hoffman et al., *Real-Time Rendering*, 4th ed. (2018). Shading, normal mapping, LOD, PBR in games. Site: https://www.realtimerendering.com
- Pharr, Jakob, Humphreys, *Physically Based Rendering*, 4th ed. (2023), free online at https://pbr-book.org
- Crane, *Discrete Differential Geometry* course notes (CMU 15-458), free.
- Jacobson and Panozzo, libigl tutorial (SGP course) for hands-on geometry processing.
- Polycount wiki (wiki.polycount.com): the practitioner reference for normal maps, texel density and polycount. The site refused connection today; content is summarised from memory and search snippets.

### Foundational algorithms: what an agent must know

**Catmull-Clark subdivision (1978).** Each subdivision step turns every face into quads and moves vertices toward a smooth limit surface. Quads subdivide predictably. Triangles and ngons make pinches. Poles (vertices with 3 or 5+ edges) make slight bumps. Sharp edges need support loops near them, or edge creases. In Blender this is the Subdivision Surface modifier. Model the cage with all-quad topology and evenly spaced loops. Keep poles on flat areas.

**Loop subdivision (Charles Loop, 1987 thesis).** The triangle-mesh counterpart of Catmull-Clark. It matters when smoothing triangulated scans or generated meshes. An agent rarely chooses it for authoring, but it explains why smoothing an AI triangle mesh gives blobby results.

**QEM simplification (Garland and Heckbert, SIGGRAPH 1997).** Collapse the edge whose merged vertex adds the least sum of squared distances to the original planes. This is the engine behind Blender's Decimate (Collapse), meshoptimizer, Simplygon-style LOD tools and most "reduce to N triangles" buttons. It keeps shape well and topology badly (long thin triangles, no edge flow). Fine for static LODs, scans and print meshes. Not for deforming characters. Lock UV seams and borders, or preserve attributes, or the UVs tear.

**Marching cubes (Lorensen and Cline, 1987).** Extracts a triangle mesh from a scalar field (SDF, voxel density, CT scan) cell by cell. Output is dense, uniform, triangle soup with stair steps at low resolution and rounded sharp corners. Dual contouring (Ju et al. 2002) keeps sharp features. FlexiCubes (arXiv 2308.05371) and DMTet (2111.04276) are differentiable versions used inside image-to-3D models. That is why AI meshes look like marching-cubes output: dense, even triangles, no edge flow.

**Poisson surface reconstruction (Kazhdan, Bolitho, Hoppe 2006; Screened Poisson 2013).** Fits a watertight surface to an oriented point cloud by solving for an indicator function. It is the standard way from photogrammetry or lidar points to a mesh (MeshLab, Open3D). It always closes holes, sometimes with balloons where data is missing. Trim low-density areas. Normals must be consistently oriented first.

**Laplacian mesh editing (Sorkine et al., SGP 2004).** Edit a mesh by moving a few handles while preserving local detail coordinates (differential coordinates). As-rigid-as-possible (ARAP, Sorkine and Alexa 2007) is the robust cousin. An agent uses it for "bend this, keep the detail": proportional editing, mesh deform and lattice are simpler relatives in Blender. Laplacian smoothing alone shrinks a mesh. Use Taubin or HC smoothing to avoid shrinkage.

**Parameterization: LSCM and ABF.** LSCM (Levy et al. 2002) is conformal, fast, and needs two pinned points. It is Blender's "Conformal" unwrap. ABF and ABF++ (Sheffer and de Sturler 2001; Sheffer et al. 2005) optimise angles and are Blender's "Angle Based" unwrap. Blender 4.3 added "Minimum Stretch" (SLIM, Rabinovich et al. 2017) [known, worth re-checking]. All of them need seams. Seam placement is the craft: hide seams in natural breaks, cut where curvature is high, straighten islands for trim sheets. Measure distortion with a checker texture.

**Instant Meshes (Jakob, Tarini, Panozzo, Sorkine-Hornung, SIGGRAPH Asia 2015).** Field-aligned remeshing. It computes an orientation field and a position field aligned to curvature and produces quad-dominant meshes in seconds. QuadriFlow (2018) adds better singularity control and is built into Blender's Remesh (Quad). Commercial Quad Remesher (Exoside) is the practitioner favourite. These are the go-to automatic retopology for AI and scan meshes. They are not good enough for deforming characters' faces, where experts hand-retopologise.

**Progressive meshes and LOD (Hoppe 1996).** Sequences of edge collapses give continuous LOD. Today: discrete LOD chains (50 percent steps), impostors at distance, or Nanite clusters.

**Mesh booleans.** Exact booleans (Blender's Exact solver, Manifold library, CGAL) need watertight inputs. They create ngons and long triangles that need cleanup for subdivision. Fine for print and for weighted-normals hard surface.

**Tangent space and MikkTSpace (Mikkelsen 2008).** The tangent basis convention that bakers and engines share. A normal map is only correct when baker and renderer use the same tangents. Blender, Unity, Unreal, Substance and Marmoset all support MikkTSpace. Triangulate before baking, or the engine's triangulation can differ from the baker's and create shading seams.

## 2. Topology and the expert rules

### Rules

- **Quads for anything that subdivides or deforms.** Triangles are fine on flat, static, non-subdivided areas, and every game mesh is triangulated at export anyway. Ngons are fine on flat faces of static meshes and in CAD-style booleans with weighted normals. They are bad on curved or subdivided surfaces.
- **Edge flow follows form and deformation.** Loops follow muscle and silhouette direction. For characters: concentric loops around the eyes and mouth (orbicularis rings), a nasolabial loop, 3 loops at elbows and knees (more on the inside of the bend), shoulders with loops that let the arm raise, fingers with 3 loops per knuckle. Animators want even spacing where things bend and sparse geometry elsewhere.
- **Poles (E-poles with 5 edges, N-poles with 3)** are unavoidable. Place them where the surface is flat and does not deform, away from silhouettes and highlights.
- **Support loops vs bevel plus weighted normals.** SubD high polys hold edges with support loops or creases. Game low polys and "mid poly" assets use a small bevel (2 or 3 segments, or one chamfer) plus face-weighted normals. That gives smooth shading on large faces and crisp edges, often without a normal map. A Polycount practitioner reports fewer vertex splits and gradients that compress better; custom normals can be lost on FBX import, so apply them last in the final package [secondary, Polycount threads]. Blender: Bevel modifier with harden normals, or the Weighted Normal modifier.
- **Hard edges must match UV seams** on baked low polys. Each hard edge splits vertices, and a UV split there costs nothing extra (Polycount wiki rule, from memory).
- **Silhouette gets the polygons.** Spend triangles where the outline is visible. Flat interiors get few. Interior faces that never show get deleted.
- **No hidden junk:** no zero-area faces, no duplicate vertices, no interior faces, no flipped normals, no loose vertices, consistent winding.

### Hard-surface pipeline (game asset)

1. Blockout from primitives at real scale. Check silhouette and proportion against reference in the engine or a scene with a human-scale dummy (1.8 m).
2. High poly: SubD with support loops, or booleans plus bevel shader, or sculpt. Floaters for bolts and panels.
3. Low poly: derived from the blockout. Silhouette-preserving, triangle budget, hard edges at UV seams.
4. UV unwrap the low poly. Straighten, orient, pack with consistent texel density and padding.
5. Bake (normal, AO, curvature, ID, position, thickness) from high to low with a cage.
6. Texture (Substance Painter, Blender, or procedural). Export in the target's convention.
7. Check in engine under neutral lighting and the game's lighting.

### Polycount budgets (Oct 2026, all approximate)

| Target | Typical budget | Source and date |
|---|---|---|
| Roblox single MeshPart | at most 20,000 triangles | Roblox specifications page [verified 2026-10-11]. Vendor blogs (Nilo, Aug 2026) say 21,000; test the importer |
| Roblox rigid accessory (UGC) | about 4,000 triangles | [secondary, conflicting figures; check the avatar specs page] |
| Mobile hero character | 5k to 30k triangles | [secondary, vendor guides disagree] |
| Quest 3 / 3S whole frame | 1.3 to 1.8 million triangles | Meta Horizon OS docs, Oct 2024 [secondary] |
| VRChat Quest avatar | under 10,000 triangles | VRChat creator docs [secondary] |
| PC/console hero character (non-Nanite) | 50k to 150k triangles | [secondary, no authoritative figure] |
| Unreal Nanite static mesh | effectively unbounded. Millions are fine, measure per scene | Epic Nanite docs, UE 5.8 [verified] |
| AR Quick Look (USDZ) | about 100k polygons, one set of 2048 px textures, 10 s animation | Apple WWDC 2018, reaffirmed by Apple DTS 2021 [secondary] |
| Web / e-commerce glTF | about 100k triangles, under 5 MB file | Khronos 3DC guideline quoted on three.js forum [secondary]; the current GitHub text gives no numbers [verified] |
| 3D printing | whatever the slicer handles. 200k to 2M triangles is typical; chord error under 0.01 mm is invisible | [known] |

### Scale, units, pivots, axes

| Tool or engine | Up axis | Handedness | Forward convention | Unit |
|---|---|---|---|---|
| Blender | +Z | right | front view looks along +Y, so characters face -Y | 1 BU = 1 m by default |
| glTF 2.0 | +Y | right | front of asset faces +Z; -X is right [verified spec 3.4] | 1 m (spec text and Khronos 3DC [verified]) |
| three.js | +Y | right | camera looks down -Z; models face +Z (glTF) | metres by convention |
| Unity | +Y | left | +Z forward | 1 unit = 1 m |
| Unreal | +Z | left | +X forward | 1 uu = 1 cm |
| Roblox | +Y | right | CFrame.LookVector is -Z | 1 stud = 28 cm [verified, create.roblox.com physics/units] |
| Godot | +Y | right | -Z is forward for nodes; imported assets face +Z | 1 m |

Rows marked [known] apart from the verified cells. Sources: glTF spec section 3.4 (registry.khronos.org/glTF/specs/2.0/glTF-2.0.html), Godot model export considerations page, Roblox units page.

- **Model at real-world size in metres.** A door is about 2.0 to 2.1 m tall, a chair seat 0.45 m, a table 0.75 m, a human 1.7 to 1.8 m. Apply scale before export (Blender Ctrl+A, scale 1,1,1).
- **Pivots:** props at bottom centre, so they sit on the ground (Khronos 3DC says bottom centre at 0,0,0; top centre for ceiling-mounted items [verified]). Doors at the hinge. Wheels at the axle. Weapons at the grip. Modular kit pieces on a grid corner.
- **Grid and modularity:** modular environment kits snap to a grid (for example 1 m, 2 m or 4 m pieces; Unreal kits often 100 or 400 uu).
- **Naming:** lowercase letters, digits, underscore or hyphen, start with a letter (Khronos 3DC [verified]). Common game prefixes: SM_ static mesh, SK_ skeletal, T_ texture with suffixes _D or _BaseColor, _N, _ORM, M_ material, MI_ material instance, UCX_ or UBX_ Unreal collision, _LOD0, _LOD1. Unity has no enforced prefix; keep one convention per project.

## 3. UVs, texturing, LODs, collision

### UV checklist

- Seams in hidden or natural places. Hard edges split in UV. Islands straightened where possible (better packing, fewer stair-steps).
- Uniform texel density across an asset, and across a scene. Common game targets: 512 px/m for third person PC (some studios 1024 px/m for first person, 256 px/m for mobile or background) [known, practitioner rule; varies by studio]. the owner exceptions (faces, hero details) as deliberate.
- Padding (dilation) at least 4 to 8 px at 2048, more for mip levels; pack with 2 to 16 px margins.
- Mirrored or overlapping UVs save space but break baked AO and lightmaps; offset overlapping shells by 1 UDIM tile before baking.
- Check with a checker texture: squares should be square and the same size everywhere.

### Trim sheets, tileables, atlases, decals

- **Tileables:** seamless textures for large surfaces (walls, ground). UVs exceed 0 to 1.
- **Trim sheets:** a texture with horizontal strips (edges, panels, bolts, rails). The mesh's UV strips map onto them. Used heavily for environment art (Star Citizen, Insomniac). Agent-friendly: an agent can map straightened UV strips to known trim rows by code.
- **Atlases:** many props share one texture to cut draw calls. Important for Roblox, mobile and web.
- **Decals:** projected or mesh-decal details (stains, labels) on top of tileables.
- **UDIMs:** multi-tile UVs for film and hero assets. Not supported by most game engines or glTF.

### PBR metal/rough theory

- Base colour (albedo) holds no lighting. Dielectrics roughly sRGB 30 to 240. Metals' base colour is their reflectance colour (often 180 to 255) [known; Substance PBR guide].
- Metalness is binary (0 or 1). Grey only at transitions or anti-aliasing [verified, Khronos 3DC]. Roblox says the same: metalness usually 0 or 100 percent [verified].
- Roughness carries most of the realism: fingerprints, wear, puddles.
- glTF packs occlusion in R, roughness in G, metalness in B (ORM in one texture) [known, glTF spec 3.9.2-3.9.3]. Unreal commonly uses ORM too. Unity URP/HDRP use their own mask maps (HDRP mask: R metal, G AO, B detail mask, A smoothness; smoothness = 1 - roughness) [known, check per pipeline].
- Normal maps are linear data, not sRGB. Albedo and emissive are sRGB.

### Normal map conventions

| App or engine | Green channel |
|---|---|
| Blender, Unity, Godot, glTF, three.js, Maya, Marmoset default, Roblox | OpenGL, Y+ |
| Unreal, 3ds Max, CryEngine, Substance Painter export default | DirectX, Y- |

Sources: Blender developers list (2017), Reallusion manual, Roblox SurfaceAppearance page ("Roblox only supports OpenGL format - Tangent Space normal maps" [verified 2026-10-11]), Godot forums [secondary]. Fix a mismatch by inverting G (G = 1 - G). Test: on a plane lit from above, bumps should look raised. three.js normalScale scales strength; a negative Y in normalScale flips it, but fixing the texture is cleaner.

### Baking checklist

- Use a cage (pushed-out low poly) or ray distance. Explode the mesh (move parts apart) or bake by matching names to avoid cross-projection.
- Same tangent basis in baker and engine (MikkTSpace). Triangulate the low poly before baking and export the triangulated mesh.
- Hard edges only where UVs split. Smooth low poly plus cage gives the cleanest bake.
- Bake at 2x target and downsample for anti-aliasing, or use supersampling.
- Bake list: normal, AO, curvature, ID, position, thickness, height.

### Texture resolutions

- Powers of two (512, 1024, 2048, 4096). Not square is fine (Khronos 3DC [verified via snippet]).
- Web and AR: 1024 to 2048 per material. Roblox imports: check the current texture requirements page (historically 1024 px max) [unverified today].
- Use KTX2 / Basis Universal for web delivery. Author in PNG, convert automatically (Khronos 3DC [verified]).

### LODs, impostors, collision, lightmaps

- **LOD chain:** LOD0 full, each next level about 50 percent triangles. Switch by screen size. Keep the silhouette. Remove small parts first.
- **Impostors:** billboards or octahedral impostors for distant trees and props.
- **Nanite:** no manual LODs needed for supported meshes. Nanite supports opaque and masked materials, static and skeletal meshes, foliage through Nanite Foliage, and tessellation. It does not support translucent materials or morph targets. WPO must be clamped [verified, Epic docs labelled UE 5.8].
- **Collision:** simple convex hulls or primitive boxes, capsules and spheres. Unreal uses UCX_ prefixed convex pieces. Roblox MeshPart CollisionFidelity (Box, Hull, Default, PreciseConvexDecomposition). Never use the render mesh as a physics mesh for moving objects.
- **Lightmap UVs:** second UV channel with no overlaps and enough padding. Unity and Unreal can generate them. Skip them if lighting is fully dynamic (Epic says to disable Generate Lightmap UVs then [verified]).

## 4. Reference gathering and creation

Experts never model from memory. Reference is the first deliverable.

### What experts collect

- **Mood or style board:** overall look, palette, era.
- **Orthographic blueprints:** front, side, top and back at the same scale. For vehicles and products, real blueprints or CAD drawings.
- **Turnarounds and model sheets:** characters in an A-pose or T-pose from front, side, back and three-quarter, with a height line and head-count scale.
- **Material references:** close-ups of real surfaces under neutral light, wear patterns, edge damage.
- **Scale references:** a person, a hand, a coin or a ruler next to the object. Real dimensions noted.
- **Detail callouts:** zoomed images of joints, fasteners, seams, hinges, logos.
- **Function references:** how mechanisms move (for rigging and for printed mechanical parts).

### Tools

- **PureRef** is the standard board tool. 2.0 shipped May 2024 (drawing on images, GIF playback, notes, groups). 2.1 shipped February 2026 (grid snapping, shapes, batch image processing) [secondary, 80.lv and CG Channel].
- **Blender:** Add > Image > Reference (or Background) as empties. Set Front, Right and Top orthographic views (numpad 1, 3, 7). Align images to the same scale using a known dimension. Set opacity around 0.3 to 0.5 and "Show in front" off for background images. Lock them in a "refs" collection.
- **Scale check:** a 1.8 m human dummy or a measured cube in the scene.

### What an AI should generate to help (the polywright angle)

| Generated artefact | Purpose | Notes |
|---|---|---|
| Concept art (2 to 4 variants) | Choose the design before modeling | Plain background, three-quarter view, even lighting |
| Orthographic views (front, side, back, top) | Blueprints for modeling, input for multi-view image-to-3D | Same scale, same ground line, no perspective, neutral pose |
| Character turnaround sheet | Proportions and costume consistency | A-pose, height bar, panels aligned |
| Silhouette sheet (flat black) | Readability check before detail | Several silhouettes; pick the clearest |
| Material swatches and tileable textures | PBR textures for large surfaces | Ask for "seamless, tileable, top-down, flat lighting"; check with a 2x2 tiling preview |
| Decals and labels | Logos, signage, grime | Alpha background |
| Height maps for terrain or relief prints | Displacement, terrain, lithophanes | 16-bit greyscale preferred; 8-bit gives terraces |
| Blockout model (primitives) | Structure guide for AI video, scale check | Can be code-generated faster than any image |
| Detail callout images | Zoomed reference of complex parts | Label with dimensions |

Prompting advice for reference sheets [secondary: Scenario help, template sites, 2025-2026]:
- Say "character turnaround sheet, front view, side view, back view, orthographic, neutral A-pose, consistent proportions, same height, aligned on one ground line, plain light grey background, even studio lighting, no shadows, no perspective".
- For products: "orthographic technical drawing style, front elevation, side elevation, top plan, flat lighting, white background, centred, no props".
- Give the image model a reference image (image-to-image or a character model) for identity lock. A sketch at high influence keeps structure.
- Expect drift between views (outfit, hair, part counts). Compare each view against the front and regenerate the off view.
- Generate views one at a time with the same seed and a shared reference if the multi-panel sheet drifts; then compose the sheet in code.
- Avoid dramatic lighting, motion blur and depth of field. They bake in shading that ruins textures and image-to-3D.
- For tileables, generate at a power-of-two size and run an offset-by-half check for seams.

## 5. Target requirements checklists

### 5a. Game-ready

**All engines**
- [ ] Real-world scale, scale applied, rotation applied.
- [ ] Pivot at a sensible place (bottom centre for props).
- [ ] Faces correct direction, no non-manifold edges on closed objects, no loose geometry.
- [ ] Triangle count within budget; LODs or Nanite decided.
- [ ] UV0 non-overlapping (or deliberate overlaps), consistent texel density; UV1 for lightmaps if baked lighting.
- [ ] Normal map in the engine's convention; tangents MikkTSpace.
- [ ] Materials per mesh minimal (each material is a draw call).
- [ ] Collision mesh simple.
- [ ] Naming convention applied.

**Unity:** FBX or glTF (glTFast or Unity's glTF importer). Y-up. Scale factor 1 with Blender export "Apply Transform" or use the FBX "Apply Unit"/Unity's "Convert Units" settings so the root is not rotated -90 on X. OpenGL normals. URP/HDRP mask map packing differs from glTF ORM.

**Unreal:** FBX, glTF or USD. Z-up, cm. Nanite for dense static or skeletal meshes with opaque or masked materials. Not for translucent materials (Mesh Decals) or morph targets. Clamp WPO. Turn off Generate Lightmap UVs if lighting is dynamic. Collision with UCX_ prefix [verified UE 5.8 Nanite page]. DirectX normals (or tick "Flip Green Channel" on the texture).

**Roblox:** FBX or OBJ via the 3D Importer. A single mesh at most 20,000 triangles (official spec page; vendors cite 21,000 for single import). At most 4 bone influences per vertex. Root joint at 0,0,0. Bones frozen with scale 1 and rotation 0. One animation track per export. No zero-thickness meshes [all verified 2026-10-11, create.roblox.com/docs/art/modeling/specifications]. SurfaceAppearance uses OpenGL tangent normals, colour, normal, roughness, metalness and emissive mask [verified]. Units: 1 stud = 28 cm, so a 1.8 m human is about 6.4 studs (Roblox avatars are about 5 to 6 studs tall). Keep many MeshParts sharing the same MeshId to reuse geometry. Use CollisionFidelity Box or Hull for props.

**three.js / web:** glTF 2.0 binary (.glb). Draco or meshopt geometry compression, KTX2 textures. Y-up, metres, +Z front. One material per mesh where possible. Total under 5 to 10 MB for product viewers. Test with gltf-validator and gltf-transform inspect.

### 5b. 3D-print-ready (Bambu P1S, FDM, 0.4 mm nozzle)

P1S: 256 x 256 x 256 mm build volume, 0.4 mm stainless steel nozzle as shipped [secondary, Fab Academy 2025 page]. AMS gives up to 4 filaments per unit (16 with 4 units) [known; verify for P1S].

Geometry
- [ ] Watertight and manifold. Every edge belongs to exactly 2 faces. No self-intersections (union overlapping parts), consistent outward normals. Check with Blender 3D-Print Toolbox, or trimesh `is_watertight`, or Bambu Studio's repair.
- [ ] Units in mm (STL has no units; 3MF does). Export 3MF when possible.
- [ ] Wall thickness: at least 2 perimeters. With a 0.4 nozzle and 0.45 mm extrusion that is about 0.9 mm; 3 perimeters 1.35 mm; 4 perimeters 1.8 mm. Walls between 1 and 2 perimeters print badly [verified, Prusa KB]. Practical: 1.2 mm minimum for structural walls, 1.6 mm recommended [secondary, PrintPal].
- [ ] Minimum detail: features under about 0.4 mm in XY vanish. Raised or engraved text at least 0.4 to 0.6 mm deep and stroke width at least 0.5 mm; font size at least about 8 pt bold for FDM [practitioner rule, unverified].
- [ ] Overhangs at most 45 degrees from vertical without supports (45 to 60 possible depending on cooling; some printers to 75) [verified, Prusa]. Use 45-degree chamfers or teardrop holes.
- [ ] Bridges: short bridges print fine. Keep under about 10 to 20 mm for clean results; well-tuned printers bridge 25 mm or more [secondary, Binghamton, MIT CBA].
- [ ] Bed-facing edges: chamfer, not fillet [verified, Prusa]. Account for elephant's foot (0.2 to 0.3 mm chamfer on the first layer edge).
- [ ] Holes print undersized. Add 0.1 to 0.3 mm to the diameter, or drill afterwards [secondary].
- [ ] Clearances: moving parts at least 0.3 mm (Prusa [verified]); sliding fits 0.2 to 0.3 mm; press fits 0.0 to 0.1 mm; print-in-place hinges 0.3 to 0.5 mm. Print a tolerance coupon first; gaps under 0.1 mm fuse [secondary, MakerWorld].
- [ ] Orientation for strength: layers are weakest in Z. Load-bearing parts should put stress along the layers.
- [ ] Splitting: split to fit the bed, to remove supports and to put the best face up. Add alignment keys: pins (for example 3 mm pin with 3.3 mm hole and 0.15 mm clearance per side), dovetails, or printed dowel holes for 1.75 mm filament pieces. Hide seams along natural lines.
- [ ] Hollowing: FDM uses infill, so solid models are fine. Do not hollow for FDM (that is a resin concern).
- [ ] Circle faceting: check real segment count; a cylinder exported with 16 segments prints as a polygon [Prusa, verified].

Miniatures (32 mm heroic scale)
- Tabletop "32 mm" is roughly eye height of a 1.8 m human, so about 1:56 [practitioner convention]. Exaggerate weapons, hands and faces (heroic scale). FDM with 0.4 mm loses faces; 0.2 mm nozzle or resin printers are the norm in r/PrintedMinis. Thicken swords and spears to at least 1.2 mm.

Terrain and building models
- Vertical exaggeration: use 1x to 2x for mountains, more for flat regions or small-scale maps; when in doubt use less [secondary, shadedrelief.com]. Commercial state maps use about 30x at very small scales [secondary, seller listings]. Smooth DEM data before exaggerating; detailed data gets spiky.
- TouchTerrain exposes size, tiling, base thickness and exaggeration [secondary]. Base at least 2 to 3 mm. Tile large maps into bed-sized pieces with alignment keys.
- Buildings: thin walls at small scales vanish. Scale up wall thickness to the 2-perimeter minimum rather than true scale. Window recesses at least 0.4 mm deep.

Multi-colour on AMS
- Assign colour per part (separate objects in one 3MF) or paint faces in Bambu Studio's colour painting. Colour changes per layer are cheapest (one swap per layer change). Colours that alternate on many layers cost purge waste: each change purges about 2 to 5 g [secondary, BambuHub]. Prime tower on by default; check it with print-by-object. Design colour boundaries on horizontal planes where possible.

### 5c. AI video use

- **Blockouts as structure:** primitives or rough models, rendered from the shot camera, give the video model the layout, scale and composition. Render depth, normal, canny (edges), and pose passes. Wan 2.1 VACE workflows in ComfyUI take depth, canny or pose control video [secondary, RunComfy workflow pages, 2026]. Frame counts follow Wan's 4n+1 rule [secondary].
- **Passes from Blender:** Z depth normalised to 0 to 1 (near white), normal pass in camera space, Freestyle or a canny filter on a flat render for edges, Object or Material index for masks. Export as image sequences at the video model's resolution and frame rate.
- **Camera paths:** animate the camera in Blender against the blockout, export the same path for every pass. Keep moves simple (dolly, pan, orbit). Very fast moves and cuts break control conditioning.
- **Consistent characters:** a 3D character turnaround (rendered views of one model) gives image models consistent reference for every angle. Render the model in the shot pose as a pose or depth guide. the owner's crashsite and mentos film notes (vault) list set drift and wrong wheel side as recurring faults, and a 3D blockout fixes set geography.
- **Do not over-detail:** control nets follow edges; noisy geometry adds noisy edges. Clean silhouettes and big shapes work best.

### 5d. Business

- **E-commerce glTF (Khronos 3D Commerce):** 1:1 real size, 1 unit = 1 m, origin bottom centre (top centre for ceiling items), lowercase names, triangles only, UVs 0 to 1 for unique textures, binary metalness, PNG authoring with automated KTX2/WebP conversion [verified 2026-10-11, github.com/KhronosGroup/3DC-Asset-Creation]. Numeric presets (triangles, file size) are marked "coming soon" in the current text; the widely quoted 100k triangles and 5 MB come from the 1.0 guideline [secondary].
- **Product configurators:** separate meshes per swappable part, consistent pivots, material variants (KHR_materials_variants), named nodes the web app can address.
- **AR Quick Look (USDZ):** about 100k polygons, one set of 2048 x 2048 textures, under 10 s animation as the safe baseline; newer devices tolerate more; "too large" errors refer to memory, not file size [secondary, Apple developer forums 2021]. Convert glTF to USDZ with Apple's Reality Converter or usdzconvert; check materials survive.
- **Android AR:** Scene Viewer takes glTF/GLB.
- **Digital twins:** accuracy and metadata matter more than looks. Keep real coordinates and units, stable IDs per object, simplified LODs for web viewers, and the source CAD (STEP) alongside. OpenUSD is the interchange in NVIDIA Omniverse and industrial pipelines.
- **CAD interchange:** STEP (AP214/AP242) for B-rep to other CAD users. Never send a mesh when a STEP is wanted. Tessellate STEP to glTF for the web with controlled chord tolerance.

## 6. Quality criteria and critique

How experts critique a model (paraphrased from Polycount critique threads, CG Cookie and Grant Abbitt videos, r/3Dmodeling critique posts):

1. **Silhouette:** readable as a flat black shape from the main viewing angles. If not, change the form, not the texture.
2. **Proportion and scale:** matches reference and a human dummy. Common AI and beginner faults: oversized details, thin walls, wrong part counts.
3. **Primary, secondary, tertiary forms:** big shapes first, medium shapes next, small details last. Beginners over-detail tertiary forms on weak primaries.
4. **Shading artifacts:** pinches near poles, smoothing errors, normal map seams, faceting on curved surfaces, gradients on flat faces (fix with weighted normals or support).
5. **Texture stretching and texel density mismatches:** checker test.
6. **Wireframe:** density matches importance; no wasted loops; clean flow on deforming areas. A r/3Dmodeling commenter (2026-09) noted a stylised model "a bit too high poly for low poly" with "prominent white lines" from texture seams.
7. **Material plausibility:** roughness variation, no pure black or white albedo, metal vs dielectric correct.
8. **Fit for purpose:** budget, scale, pivot, naming, export in the target.

### AI self-check loop (proposal for polywright)

1. Render a fixed contact sheet: front, side, top orthographic; three-quarter perspective; flat black silhouette; wireframe overlay; matcap or clay; UV checker; normals coloured; and a scene with a 1.8 m human dummy.
2. Show the matching reference views beside each render.
3. Ask a vision model concrete questions: does the silhouette match the reference? Which parts are missing or extra? Are proportions within about 10 percent? Any shading artifacts?
4. Run numeric checks in code: triangle count, bounding box in metres, manifold and watertight, flipped normals, loose parts, UV overlap and texel density spread, material count, naming.
5. Fix and repeat. Stop on numeric pass and visual pass, or after N rounds with a report.

LL3M, ViSculpt and SceneCraft (arXiv 2403.01248) all use variants of render-and-critique. MeshQuery (2610.02507) uses a VLM with edge-selection tools for UV seams. This is the strongest evidence that the loop works for agents.

## 7. Practitioner wisdom

- **Polycount wiki and forums** (wiki.polycount.com, polycount.com): normal map technical details, texel density, polycount, face weighted normals threads. On AI meshes (2026 thread on an AI mushroom run through Quad Remesher): "borderline usable"; replies said the generator does not understand forms; fine as a base for sculpting or blockout, not as a finished model [secondary, search snippet].
- **r/3Dmodeling (2026-09-16, "My friend says the AI generated models are better than mine")**: commenters said AI models are "crap when talking about topology and edge flow", and that AI output "looks generic, clean and soulless". Read via Reddit RSS on 2026-10-11 (https://www.reddit.com/r/3Dmodeling/comments/1vi4w0p/).
- **Vendor view (Meshy docs, Tripo, Neural4D, 2025-2026):** AI meshes have too many triangles and messy topology; remesh before use; retopology destroys UVs, so rebake from the original [secondary]. Polywright should plan for this: generate, then remesh, then unwrap, then bake from the generated high poly.
- **Grant Abbitt and Blender Guru:** blockout first, use reference, keep it simple, work big to small. Blender Guru's donut series remains the onboarding path [known].
- **Ian Hubert's "lazy tutorials":** one-minute fakes (image planes, photo textures, kitbash) for backgrounds. Lesson for agents: detail only what the camera sees, and photo-textured cards beat modelling for far backgrounds [known].
- **CG Cookie:** "Everything new in Blender 5.0" covers new modifiers and UV sync changes [secondary].
- **80.lv interviews:** consistent themes are modular kits, trim sheets, and starting from silhouette and lighting [known, general].
- **r/3Dprinting and r/PrintedMinis:** calibrate before blaming the model; print a tolerance test; orient for strength; 0.2 mm nozzle for minis on FDM; supports from tree supports [known, general].
- **r/gamedev:** the most common mistake is wrong scale or pivot and too many materials, not polycount [known, general].

## 8. Research directions 2024-2026 (arXiv ids checked against the arXiv API on 2026-10-11)

### Mesh generation as token sequences (artist-like meshes)

| Paper | arXiv | Date | Note |
|---|---|---|---|
| PolyGen | 2002.10880 | 2020-02 | First autoregressive mesh model |
| MeshGPT | 2311.15475 | 2023-11 | Decoder-only transformer over learned face tokens |
| MeshAnything | 2406.10163 | 2024-06 | Artist-created mesh conditioned on a shape; up to about 800 faces |
| MeshAnything V2 | 2408.02555 | 2024-08 | Adjacent mesh tokenization |
| EdgeRunner | 2409.18114 | 2024-09 | Autoregressive autoencoder, tree traversal |
| BPT (Scaling Mesh Generation via Compressive Tokenization) | 2411.07025 | 2024-11 | Blocked and patchified tokens; 5k-8k faces |
| Meshtron (NVIDIA) | 2412.09548 | 2024-12 | Hourglass transformer; tens of thousands of faces (Silksong's summary says up to 16k) |
| Nautilus | 2501.14317 | 2025-01 | Locality-aware autoencoder |
| TreeMeshGPT | 2503.11629 | 2025-03 | Autoregressive tree sequencing |
| DeepMesh | 2503.15265 | 2025-03 | Adds DPO preference alignment |
| Mesh Silksong | 2507.02477 | 2025-07 | Each vertex visited once; claims manifold, watertight output |
| QuadGPT | 2509.21420 | 2025-09, ICLR 2026 | Native quad meshes, tDPO fine-tune (HKUST and Tencent Hunyuan) |
| QuadLink | 2605.16813 | 2026-05 | Quad-dominant generation via point relations |
| Strips as Tokens, Nexus | SIGGRAPH 2026 | 2026 | Artist mesh with native UV segmentation; separate vertex and topology diffusion [secondary, Ke-Sen Huang list] |

Take-away: these models reach thousands to tens of thousands of faces with plausible edge flow, and quad output arrived in 2025-2026. They are worth watching as a remesh step after image-to-3D. Most are research code with non-commercial or unclear licences; check before shipping.

### Image-to-3D foundation models

- TRELLIS (2412.01506, 2024-12) and TRELLIS.2 (2512.14692, 2025-12): structured sparse voxel latents; TRELLIS.2 uses "O-Voxel", outputs PBR (base colour, roughness, metallic, opacity), MIT licence per its model card; no polygon count control [secondary].
- Hunyuan3D 2.0 (2501.12202) and 2.1 (2506.15442, production-ready PBR); later 2.5 and 3.x products exist [secondary, no arXiv found].
- PartCrafter (2506.05573): part-structured mesh generation. Parts matter for printing (split) and games (separate pieces).
- SF3D (2408.00653): fast reconstruction with UV unwrapping.

### UV, remeshing, simplification

- ArtUV (2509.20710), SeamCrafter (2509.20725, RL for seams), PartUV (2511.16659, part-based UV for AI meshes), DreamUV (2606.22445, flow matching), SeamFlow (2609.04751), MeshQuery (2610.02507, training-free VLM agent picks seams with tools; 2026-10-01).
- Fast and Robust Mesh Simplification for Generated and Real-World 3D Assets (2605.14029, 2026-05): targets dense non-manifold AI meshes.
- CelloCut (2605.17853, 2026-05): watertight remeshing by tetrahedral cell cuts; relevant to print repair.
- Isotropic Remeshing with Inter-Angle Optimization (2507.13641).
- RADmesh (2608.17182): remesh-aware deformation with visual losses.
- Texture-Aware Remeshing (Knodt and Baek, ACM TOG, SIGGRAPH 2026) [secondary].

### Differentiable rendering and representations

- nvdiffrast (2011.03277): differentiable rasterisation used inside most texture and mesh optimisation.
- DMTet (2111.04276) and FlexiCubes (2308.05371): differentiable iso-surfaces; why generated meshes are dense triangle soup.
- 3D Gaussian Splatting (2308.04079): the dominant capture representation; not a mesh, so conversion is needed for games or printing.

### CAD and code generation (most relevant to an agent that writes code)

- B-rep generation: BrepGen (2401.15563), HoLa (2504.14257), GraphBrep (2507.04765), BrepGPT (2511.22171), AutoBrep (2512.03018), holistic-token B-rep (2601.16771), Autoregressive B-Rep Shape Generation with Parametric Surfaces (2607.17093, SIGGRAPH 2026).
- CAD code: CAD code with VLMs (2410.05340), CAD-Coder (2505.14646), CADmium (2507.09792), EvoCAD (2510.11631), StepCAD (2610.03799, mesh to CAD code with an LLM policy and geometry-guided search, 2026-10-01).
- Agents in Blender: 3D-GPT (2310.12945), SceneCraft (2403.01248), LL3M (2508.08228, multi-agent Blender Python with critique), ViSculpt (2608.24169, visual-centric agentic geometry editing, 2026-08), SimWorlds (2607.01766).
- ALPS: Abstracted Low-Poly Stylization and Fabrication (SIGGRAPH 2026) [secondary].

Take-away for polywright: the 2025-2026 trend is agents that write modeling code and check renders, plus learned post-processing (seams, simplification, quads) for generated meshes. That matches a plugin design of "code-first modeling, generated meshes as optional input, classical cleanup, render-based self-check".

## Open questions / unverified

- Roblox triangle cap: official page says 20,000; Nilo (Aug 2026) says 21,000 with lower batch-import limits. Test with the importer. Roblox texture size limit not checked today.
- Roblox UGC accessory triangle limits conflict (4,000 vs 10,000). Check the avatar specifications pages.
- Nanite page is labelled UE 5.8 but links mention 5.5. Skeletal Nanite status per version (experimental 5.4, stable later) needs the release notes.
- Khronos 3DC numeric presets (100k triangles, 5 MB) come from a secondary quote of the 1.0 guidelines; the current GitHub text marks presets "coming soon".
- Apple AR Quick Look numbers come from 2018 WWDC and a 2021 forum answer; there may be newer visionOS-era guidance.
- Unity normal map convention: one secondary source claimed DirectX; Unity's own docs (not fetched today) and long practice say OpenGL Y+. Confirm with a test.
- Blender 4.3 "Minimum Stretch" (SLIM) unwrap is from memory; confirm in the manual.
- Bambu P1S AMS count and nozzle material not checked against bambulab.com today.
- Text size, pin and press-fit numbers for FDM are practitioner rules; validate with a tolerance coupon on the owner's P1S and record results.
- Polycount wiki refused connections today (socket closed); the normal-map and polycount wiki content above is from memory and snippets.
- Meshtron face counts differ between sources (16k vs 64k). Read the paper before quoting.
- Licences of research mesh generators were not checked.

## Sources (all accessed 2026-10-11)

- glTF 2.0 spec: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- Khronos 3D Commerce guidelines: https://github.com/KhronosGroup/3DC-Asset-Creation/blob/main/asset-creation-guidelines/RealtimeAssetCreationGuidelines.md and blog https://www.khronos.org/blog/3d-commerce-working-group-releases-real-time-asset-creation-guidelines-to-assist-artists-create-efficient-reliable-models-for-retail-and-e-commerce
- three.js forum quote of 3DC numbers: https://discourse.threejs.org/t/maximum-3d-model-size-to-load/46077/7
- Roblox mesh specifications: https://create.roblox.com/docs/art/modeling/specifications
- Roblox SurfaceAppearance: https://create.roblox.com/docs/art/modeling/surface-appearance
- Roblox units: https://create.roblox.com/docs/physics/units
- Nilo Roblox triangle limit: https://nilo.io/articles/vibe-code-roblox-triangle-limit
- Unreal Nanite: https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine
- Godot export considerations: https://docs.godotengine.org/en/4.2/tutorials/assets_pipeline/importing_3d_scenes/model_export_considerations.html
- Blender developers list on normal map conventions: https://lists.blender.org/pipermail/bf-committers/2017-April/048312.html
- Reallusion normal export: https://manual.reallusion.com/Character-Creator-5/Content/ENU/5.0/17-Export/FBX-Advanced-Settings-Normal.htm
- Apple AR Quick Look sizes: https://developer.apple.com/forums/thread/693867
- Prusa, modeling with 3D printing in mind: https://help.prusa3d.com/en/article/modeling-with-3d-printing-in-mind_164135/
- Fab Academy P1S tests: https://fabacademy.org/2025/labs/kannai/Weekly_Group_Assignment/week05/
- Binghamton MakerLab guide: https://www.binghamton.edu/libraries/about/locations/makerlab/services/3d-printing/
- MIT CBA design rules: https://cba.mit.edu/classes/863.25/Architecture/week-3.html
- MakerWorld tolerance test: https://makerworld.com/en/models/107896-tollerance-test-3-grams
- PrintPal design guide: https://printpal.io/docs/3d-printing-design-guide
- Shaded relief vertical exaggeration: https://shadedrelief.com/3D_Terrain_Maps/3dterrainmapsver.html
- TouchTerrain: https://public.vrac.iastate.edu/~charding/TouchTerrain%20AGU%202020%20poster.htm
- BambuHub multi-colour: https://bambuhub.net/guides/multi-color-techniques
- PureRef 2.0 and 2.1: https://80.lv/articles/pureref-2-0-released-with-revamped-ui-drawing-gif-support/ and https://cgpress.org/archives/pureref-2-1-adds-shapes-grids-and-language-support.html
- Blender 5.0: https://cgpress.org/archives/blender-5-0-released.html and https://cgcookie.com/posts/everything-new-in-blender-5-0
- Scenario turnarounds: https://help.scenario.com/en/articles/generate-character-turnarounds/
- Blender to ComfyUI VACE workflow: https://www.runcomfy.com/comfyui-workflows/blender-to-comfyui-ai-renderer-2-0-workflow-cinematic-video-output
- Polycount AI mesh thread: https://polycount.com/discussion/234261/src
- Polycount face weighted normals threads: https://polycount.com/discussion/comment/2587544
- Neural4D retopology guide: https://blog.neural4d.com/user-guide/blender-retopology-ai-3d-models/
- Meshy remesh docs: https://docs.meshy.ai/en/webapp/guides/3d-model/remesh
- r/3Dmodeling thread: https://www.reddit.com/r/3Dmodeling/comments/1vi4w0p/my_friend_says_the_ai_generated_models_are_better/
- SIGGRAPH 2026 papers list: https://kesen.realtimerendering.com/sig2026.html
- arXiv entries: ids listed in section 8 (checked via export.arxiv.org API).
