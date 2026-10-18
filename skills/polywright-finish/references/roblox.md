# Roblox: making and finishing models

Back to [../SKILL.md](../SKILL.md). Axes, units and the cross-engine budget table are in
[engines.md](engines.md); this page is the artist's route to a Roblox-ready file. Placing it in a game,
collision settings, streaming and Open Cloud uploads are the developer's side: the
[roblox-agent](https://github.com/m4bwav/roblox-agent) plugin, whose workflow skill keeps a `references/3d-models.md` for that.
Facts read on create.roblox.com on 2026-10-17 [verified] unless marked; sources in
[../RESEARCH.md](../RESEARCH.md) R-20261017-2.

## Decide the style before the first vertex

| Style | Make it as | Budget feel |
|---|---|---|
| Classic blocky | Mostly Studio parts; model only what parts cannot shape | Hundreds of triangles |
| Smooth plastic, toy | Simple bevelled solids, flat colour (no texture, or `MeshPart.Color`) | Hundreds to low thousands |
| Low-poly stylised | Flat-shaded forms; vertex colours or one shared palette texture across the kit | Low thousands per prop |
| Realistic PBR showcase | Baked high-to-low with the full map set | Up to 20k per MeshPart, split beyond |

Ask the requester which style the game uses; a PBR rock in a blocky game looks wrong however good it is.

## Model to the limits

- At most 20,000 triangles per mesh. The Importer decimates anything bigger by itself, so split first: one
  MeshPart per material, per moving piece (wheel, door, lid) and per chunk of a large building.
- Watertight, no zero-thickness surfaces (Solidify thin cloth and leaves, or the Importer and solid modelling
  reject or mis-shade them), quads where possible, normals facing out. `pw.py check --target game-roblox`
  catches open edges and unapplied scale.
- One material per mesh object. Name objects the way the game will refer to them: Reimport matches meshes by
  name and path, so renaming in Blender later creates new MeshParts instead of updating old ones.
- Kits: model a piece once and let the game duplicate it. Identical mesh plus identical textures draw in one
  call; a scene exported as one file gives every copy its own asset and loses that.
- Pivots where the game expects them: bottom centre for props, hinge for doors, axle for wheels, grip for
  tools. The Importer keeps each object's pivot ("Use Imported Pivot") and puts the model pivot at the scene
  origin by default.

## UVs and the PBR set

- One UV set, all islands inside 0 to 1, overlaps allowed (mirror to save space).
- `SurfaceAppearance` maps: colour (albedo, alpha allowed), normal (OpenGL, tangent space; flip green from
  DirectX bakers), roughness, metalness (single-channel 8-bit), optional emissive mask. Albedo without baked
  lighting; Roblox lights it.
- Size by object: roughly 256 px per 2x2x2 studs, 1024 px for a body-sized object and as the ceiling for
  game textures, even though uploads accept 4096 px. Rigid accessories: non-colour maps at most 256 px.
  Layered clothing for the Marketplace: at most 2048 px.
- Name the files with the map affix and embed them in the FBX (Path Mode Copy, Embed Textures); the Importer
  then builds the `SurfaceAppearance` itself.
- Low-poly stylised: vertex colours import too, and a single palette texture shared by every kit piece keeps
  materials, draw calls and uploads down.

## Scale and export from Blender

- 1 stud = 0.28 m. Either model in studs (Scene Units: Unit System None, 1 unit = 1 stud) or model in metres
  and set the Importer's File Geometry > Scale Unit to metres. A 1.8 m person is about 6.4 studs; classic
  avatars are about 4.75 studs, Rthro Normal 5.75 to 6.5.
- FBX: Apply Scalings = FBX Unit Scale, other scales left at 1, Add Leaf Bones off, Bake Animation off unless
  the file carries an animation (one track per file). glTF needs no scale workaround.
- Apply transforms before export. Test a new pipeline once with a 1 m cube and an arrow pointing forward.
- `pw.py convert in out.fbx` (or `.glb`) writes either; record it with
  `pw.py manifest <dir> --add-output out/<file> --target game-roblox --inspect`.

## Collision geometry is a separate deliverable

Roblox computes collision from the render mesh unless told otherwise. For big or concave models (arches,
interiors, terrain-like rocks), ship simple box-like blockers as their own objects named `<name>_Collision`
(polywright's convention, not Roblox's) so the developer can make them invisible and set the render mesh
to Box or no collision. Bones never change collision.

## Rigs and skinning

- Bones frozen (scale 1, rotation 0), root bone at the origin with no weights, at most 4 influences per
  vertex, symmetric weights.
- R15 bodies: 15 meshes named `<Part>_Geo` (Head_Geo, UpperTorso_Geo ... RightFoot_Geo), each capped
  watertight; the R15 hierarchy Root > HumanoidRootNode > LowerTorso > ...; LowerTorso and Root at
  0,0,0; I, A or T pose. Triangle budgets: head 4,000, torso 1,750, each limb 1,248, 10,742 in all. Advanced
  R15 adds up to 37 optional bones (spine, clavicles, fingers) with fixed names.
- Attachments are small objects suffixed `_Att` (Hat_Att, LeftGrip_Att ...), unrotated, inside the part's
  bounding box.
- For a standard humanoid, a clean unrigged A-pose mesh plus Studio's Avatar Setup often beats a hand rig: it
  rigs, skins, cages and adds the face. Hand-rig custom creatures; Avatar Setup does not cover them.

## Layered clothing cages

- Start from Roblox's layered-accessory template files. `<Name>_InnerCage` and `<Name>_OuterCage` sit beside
  the render mesh; never delete cage vertices or edit cage UVs, since they map cage to cage.
- Inner cage starts identical to the template body cage; push only the outer cage out so it fully covers the
  garment, keeping faces even and the shape symmetric.
- Garment at most 4,000 triangles, skinned to the R15 bones with at most 4 influences.
- Bodies that should wear layered clothing need their own `_OuterCage`.

## Verify before handing over

1. `pw.py check out/<file> --target game-roblox --real-size-m X` and a render sheet (`pw.py render`).
2. In Studio's Importer preview: triangle count, warnings, the object hierarchy, rig type (R15, Custom or No
   Rig) and that cages became WrapLayer or WrapTarget.
3. In the place: size against a default avatar, the collision-fidelity visualiser, PBR under the game's
   lighting.
4. Avatar items: run the UGC validation (it also runs on every Marketplace upload) and fix every error
   before sending anything to the developer.

The developer imports, sets collision and streaming, and uploads through Studio or Open Cloud: hand over the
asset folder and let roblox-agent take it from `manifest.json`.
