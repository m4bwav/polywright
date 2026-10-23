# Models and blockouts for film and AI video

A film asks less of a model than a game or a print: no topology for an engine, no watertight solid. It asks for
the right size in the right place in front of the right camera, and for passes a video model can read. This page
is the 3D artist's side: how to build for the shot. What to shoot, and which shots need 3D at all, is the
director's side in [cinewright](https://github.com/m4bwav/cinewright) (cinewright-sets, entry `3d-models`).

Back to [../SKILL.md](../SKILL.md). Target: `video-blockout` in [targets.json](targets.json). Hand-over:
[contract.md](contract.md). Crowds: [crowd-blockouts.md](crowd-blockouts.md). A small cast of figures:
[figures-for-video.md](figures-for-video.md). Commands: [cli.md](cli.md).

## Start from the cameras

1. Ask the caller for the shot list with each camera: position in metres, aim, lens in mm, frame size, length
   in frames and fps, and the people's marks per beat. Without cameras there is nothing to size the detail to.
2. Put the cameras in the scene first, at the video model's frame (832x480 or 1280x720 for Wan, 864x480 and
   24 fps for MiniMax H3). Blender's default sensor is 36 mm wide: keep it, so the caller's full-frame lens
   numbers mean the same thing here.
3. Build only what at least one camera sees. Render a quick clay view per camera before modelling anything
   further: a wall or a back no camera reaches is left as a plain box or not built.
4. Check every end state through its own camera: a person who ends lying on the floor at a 1.2 m eye height and
   a 35 mm lens can fall below the frame. Tilt or move the camera in the blockout, and tell the caller.

## Detail by shot distance

| Largest size on screen | Build |
|---|---|
| extreme wide, wide | silhouette only: boxes, cylinders, a terrain; no bevels |
| full, medium full | proportions and main parts; mannequins for people |
| medium close, close | the hero object modelled properly; hands and props at real size |
| extreme close | a separate insert model, built for that one shot |

- One object, one level: the largest size it reaches in any shot. Do not carry close-up detail into a wide.
- Far scenery (skyline, mountains, sky) is a painted plate on a card at the right distance, or a picture
  projected from the camera onto rough geometry (2.5D). It holds while the camera moves little; a large move
  past it needs real geometry.
- Hard-surface sets (machines, ruins, ships) are fastest kitbashed: reuse a small library of parts, scaled and
  rotated, and let the image or video model paint the surface.
- Real places come from capture (polywright-capture: `pw.py place`, photogrammetry, splats). Use a splat for
  scouting and for placing cameras; for passes, a mesh renders cleaner depth.

## Scale and lens checks

- Real size in metres. People 1.7 to 1.8 m, doors 2.0 to 2.1 m, a table 0.75 m, a chair seat 0.45 m.
  `pw.py check --target video-blockout --real-size-m X` on every model brought in.
- Eye-level cameras sit at 1.5 to 1.7 m; say when a shot is lower or higher than that, as the caller's card does.
- Compare a figure's height in pixels with what the caller's storyboard shows at the same lens. If they differ
  by more than about 15 % (polywright's own rule of thumb), the camera distance or the lens is wrong, not the figure.
- Thin things vanish in depth: a blade at real width breaks up at a 4 m two-shot. Add a pass with thin props
  2.5 to 3 times as thick; leave the clay pass at the real width.

## Passes the video model reads

- **Clay** (grey, Workbench or Eevee, one light, cavity on): run Canny on it for an edge control, or repaint
  frame 1 into a start still. Grey, not textured: texture in a control fights the references and gets copied.
- **Depth**: inverse depth (near white), one range for the whole shot, or the video pulses. Blender's Mist pass
  is anti-aliased and normalised but maps plain distance, not 1/z, so the near ranks get fewer tones; for
  inverse depth from a hand-built scene use a shader AOV (recipe `passes-one-render` in polywright-blender).
  Mist on a video model: one blind test on a local H3 graph (crowd push-in, control 0.6, end 0.4, two seeds)
  picked Mist over inverse depth both times, so render both for wide crowds and keep the better take. `crowd`
  writes inverse depth only; for Mist see L-012.
- **Pose**: COCO-18 joints for figures taller than about 40 px; leave out the nose and eyes when a head faces
  away from the camera, or the model turns the person to the lens.
- **Masks**: one colour per side or team, for per-side prompts and inpainting.
- **Camera**: `camera.json` per frame, for camera-control models and for matching plates later. Keep depth of
  field and motion blur off in every control pass; write lens, f-stop and focus distance into the camera record
  and let the prompt name them.
- Render every pass at the shot's exact frame count and fps. Read a contact sheet of the first, middle and last
  frame of each pass before handing over.

## Set dressing

- Hero dressing (the throne, the desk, the car) is placed at the caller's plan positions, to the centimetre,
  and named by role (`throne`, `door_east`), never by colour.
- Background dressing is a few repeated pieces with jitter in yaw and scale; the model fills in the rest.
  A Geometry Nodes scatter places them with a minimum gap (recipe `gn-scatter`; `pw.py crowd --scatter` for
  figures).
- No two faces on the same plane overlapping (kitbashed walls, a floor laid twice): they flicker in clay, depth
  and edge passes.
- No text or signage in the blockout: the model copies it as garble. Signs are added in finishing.
- Keep each set in its own `.blend` with its cameras, so a later shot reuses the room and its lens.

## Figures and turnarounds

- People in a blockout are stand-ins for height, marks and facing. A segmented mannequin with two-bone IK carries
  standing, kneeling and kicking; a rigged body (Mixamo, a CC0 library) is needed for falls and rolls.
- Identity comes from references, not from the blockout's face: for a real figure or toy, mesh it from photos,
  fix colour and markings with `pw.py mark`, and give the video model `pw.py turnaround` pictures.
- Who stands where: `pw.py lineup` writes colour, clay, depth and team masks with each team on a fixed side.
  A still control over a moving action freezes the people at their marks; pass `colour.png` as a guide frame
  instead and keep the control for a short, still section.

## Commands for film

| Need | Command |
|---|---|
| an army or a crowd, with depth, pose, mask and clay videos | `pw.py crowd` ([crowd-blockouts.md](crowd-blockouts.md)) |
| two fighters posed in the set, with Canny, depth, thick-blade depth and pose videos | `pw.py duel` ([crowd-blockouts.md](crowd-blockouts.md), Two fighters) |
| a designed prop placed exactly in a still's hand and lens | `pw.py match` ([../SKILL.md](../SKILL.md), Compose a model into a picture) |
| reference pictures of a model, front to back on grey | `pw.py turnaround` |
| a generated figure's colour, painted marking or size fixed | `pw.py mark` |
| a small cast on fixed sides, with depth and masks | `pw.py lineup` ([figures-for-video.md](figures-for-video.md)) |
| any other pass from a set's `.blend` | `pw.py bpy` with your own script (polywright-blender) |

Hand-over: record each pass as an output with `--target video-blockout`, the contact sheet as a review, and the
shot's camera and lens in `brief.md`. The caller reads `manifest.json` and `out/` and nothing else.

Sources: The Third Floor on previs, techvis and postvis (thethirdfloorinc.com, accessed 2026-10-17); LOD per
shot size (CAVE Academy, 2020); camera projection in Nuke (3dart.it); Gaussian splats for scouting and layout on
a 2026 feature (radiancefields.com, 2026-02-13); a blockout is for spatial reference and too much detail confuses
the model (flick.art, 2026-06); field tests of crowd, set and two-fighter blockouts (2026-10-13 to 10-17,
[../RESEARCH.md](../RESEARCH.md) R-20261017-1).
