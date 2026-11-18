# Learnings: polywright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason; long entries kept but moved out of the install go to ai-docs/notes/polywright-learnings-archive.md.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

Archived 2026-11-17 to save install size (full text in the repo at ai-docs/notes/polywright-learnings-archive.md, not installed):
- L-022 · 2026-10-25 · Turning off anti-aliasing is not enough for an exact-colour pass: dither adds +-1 noise
- L-021 · 2026-10-25 · A crowd blockout cut down to two figures keeps crowd defaults that hide them
- L-020 · 2026-10-24 · A bank or dyke along a path is one swept profile, not a row of boxes
- L-019 · 2026-10-24 · An inverse-depth pass with a near limit below the nearest surface comes out flat
- L-018 · 2026-10-24 · Take a UI's text bands from its layout file, not from a rule of thumb
- L-017 · 2026-10-24 · At sprite size a thin beam crossing a cylinder's silhouette reads as going through it
- L-016 · 2026-10-24 · A camera fitted to ground diamonds gives the ground scale, not the building's on-screen size
- L-015 · 2026-10-23 · A 16-bit RGBA PNG from Blender reads back as 8 bits in Pillow and imageio; write data passes as TIFF
- L-014 · 2026-10-23 · A game's sprite camera is in its ground diamonds; fit it, do not guess an isometric angle
- L-009 · 2026-10-22 · From behind, the default camera merges the enemy line and its reserves into one band; raise it and aim past the enemy

### L-008 · 2026-10-19 · A duel's depth or Canny passes hold where the fighters stand and which way they face, but not a low pose
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-007 · 2026-10-17 · The crowd command's default side view frames a 30-wide march as a thin band, and --aim needs --cam
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-006 · 2026-10-16 · A small cast of real figures holds in video only when the meshes carry the markings and a lineup carries the sides
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-001 · 2026-10-11 · Topology checks on glTF or STL must weld coincident positions first
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-002 · 2026-10-11 · Workbench cavity distance is in scene units
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-006 · 2026-10-17 · To take an accessory off a TRELLIS.2 mesh, delete its loose pieces by their texture colour
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-005 · 2026-10-16 · A pose pass must leave out face points turned from the lens, and a previs checks that each end state is in frame
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-004 · 2026-10-13 · A crowd blockout's defaults decide whether anything is in frame
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-003 · 2026-10-12 · To fix a prop in a picture, match the picture's camera and paste the model; the solve needs only two pixels and a depth
- archived 2026-11-17: [ai-docs/archive/polywright-learnings-2026-10.md](../../ai-docs/archive/polywright-learnings-2026-10.md)

### L-010 · 2026-10-22 · Recalculating normals fixes AI meshes' flipped faces, but only on welded topology
- moved 2026-11-18 (budget): [ai-docs/notes/polywright-learnings-archive.md](../../ai-docs/notes/polywright-learnings-archive.md)

### L-011 · 2026-10-22 · A scatter behind the far side shows only in some framings
- moved 2026-11-18 (budget): [ai-docs/notes/polywright-learnings-archive.md](../../ai-docs/notes/polywright-learnings-archive.md)

### L-012 · 2026-10-23 · crowd.blend holds only the last frame's pose: render extra passes inside the frame loop
- moved 2026-11-18 (budget): [ai-docs/notes/polywright-learnings-archive.md](../../ai-docs/notes/polywright-learnings-archive.md)

### L-013 · 2026-10-23 · crowd PNGs differ byte for byte between identical runs: compare decoded pixels
- Trigger: two runs of the same `crowd` command on the same build gave different SHA-256 for every depth, mask and clay frame; 30 bytes differed in the header chunks (Blender writes an eXIf chunk), while the decoded pixels were equal.
- Rule: to prove a change leaves a pass untouched, compare decoded pixels (`png_decode` or Pillow `tobytes()`), not file hashes. A 16-bit pass (Mist) opens in Pillow as `I;16` and clips to white through `convert("RGB")`; scale by 1/257 first (`crowd_sheet` does).
- Evidence: 17-frame crowd at 320x192, Blender 5.2.1, before and after the Mist pass: every pass pixel-identical, no file hash equal
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-014 · 2026-10-23 · `pw.py bpy` swallows a script flag that shares a name with its own options
- Trigger: `pw.py bpy build_sets.py -- --blend` never saved the .blend; the script saw no `--blend`, though `--people` passed through.
- Hypothesis: argparse in `pw.py bpy` matches `--blend` (its own "open this .blend first") even after the script name, so the flag is consumed before it reaches the script.
- Rule: give script flags names `pw.py bpy` does not own (`--save-blend`, not `--blend`; avoid `--timeout`, `--lines`); when a flag seems ignored, print `sys.argv` in the script.
- Evidence: siege-news blockout (D:/<folder>/siege_news/sets/blockout/build_sets.py), 2026-10-23: `--blend` wrote nothing, `--save-blend` wrote four .blend files.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23
