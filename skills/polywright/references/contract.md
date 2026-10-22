# The asset contract: how other plugins call polywright

Any skill or plugin that needs a 3D model (a three.js page, a film, a Roblox place, a Unity scene, a print job)
asks for it through one folder. polywright fills it; the caller reads `manifest.json` and takes files from
`out/`. Nothing else is promised, so either side can change its insides.

Back to [SKILL.md](../SKILL.md).

## Calling

The caller writes the brief, or asks polywright to:

```
python pw.py new assets/fountain --name Fountain --kind imagined --route generate \
    --targets game-roblox,print-fdm --real-size-m 1.0 --brief "granite park drinking fountain, lion-head spout"
```

then says in plain words what it needs ("a Roblox prop under 20k tris and an 80 mm print"). When polywright is
done, `manifest.json` has `status: delivered` and one `outputs` entry per target.

## Folder

```
<asset>/
  brief.md         what, why, targets, real size, must-haves, can-skips
  manifest.json    the contract (below)
  refs/            reference images, blueprints, measured photos, textures; each one is a `sources` entry
  work/            .blend files (numbered per milestone), intermediates, generator outputs (*.gen.json beside them)
  out/             deliverables, one or more per target
  renders/         review sheets per step (renders/<step>/sheet.png)
```

## manifest.json

```json
{
  "polywright": "1",
  "name": "Fountain",
  "kind": "imagined",            // real | imagined | hybrid
  "route": "generate",           // found | capture | place | generate | procedural | cad | hand | mixed
  "brief": "...",
  "targets": ["game-roblox", "print-fdm"],
  "units": "m",                  // print outputs are in mm; their target says so
  "real_size_m": 1.0,
  "up": "+Z in .blend, +Y in glTF",
  "sources": [{"what": "reference image", "url": "...", "author": "...", "licence": "...", "retrieved": "2026-10-11"}],
  "tools": [{"name": "Hunyuan3D-2 (ComfyUI)", "version": "dit-v2"}],
  "outputs": [{"path": "out/fountain_roblox.glb", "target": "game-roblox", "sha256": "...", "bytes": 0,
               "tris": 14998, "dims": [0.77, 0.76, 1.0], "watertight": false}],
  "reviews": [{"render": "renders/final/sheet.png", "verdict": "...", "by": "agent|user"}],
  "status": "delivered"          // brief | references | blockout | model | review | delivered
}
```

Rules for both sides:

- Paths are relative to the folder, forward slashes.
- `sources` lists every input that came from outside, with its licence; `unknown` is a problem `--validate` reports.
- AI-made parts are named in `tools` (model and version) so stores that require disclosure can be answered.
- `outputs[].sha256` lets the caller see whether a file changed after hand-over (`manifest --validate`).
- A caller that edits an output records it with `--add-output` again (and a review line), so the folder stays
  the single record.

## Which plugin takes what

| Caller | Usual target | Takes |
|---|---|---|
| a three.js page (threewright) | web-threejs | GLB with meshopt or Draco, KTX2 textures, real size |
| film and AI video (cinewright) | video-blockout | blockout GLB or .blend, turntable and camera-path renders, depth and normal passes |
| a Roblox place (roblox-agent) | game-roblox | FBX/GLB/OBJ per MeshPart under 20k triangles, one material, OpenGL normals; places as `scene.glb` plus `place.json` |
| a Unity project (unity-agent) | game-unity | GLB (glTFast) or FBX with baked axes, LODs, a collision proxy |
| a printer or slicer skill | print-fdm, print-resin | watertight STL in mm plus a 3MF when one can be built |
| an image or ComfyUI skill | (input side) | asks it for reference images (polywright-references says which) |
| an art judge (artwright) | (review side) | concept art before image-to-3D and turnaround renders: with artwright installed, `artwright-judge` picks the candidate, checks it against the brief and writes `artwright/verdict.json` ([contract](https://github.com/m4bwav/artwright/blob/main/skills/artwright-judge/references/verdict-contract.md)) |
