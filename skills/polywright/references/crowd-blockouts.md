# Crowd and battle blockouts for AI video

Video models break on crowds (clones, merged limbs, armies that swap sides), while Blender places hundreds of
figures with exact perspective in seconds. So let Blender do the crowd and let the video model paint over it:
`pw.py crowd` builds the army and renders the control videos, and the video model (Wan VACE, Wan 2.2 Fun
Control, or a hosted model taking a reference video) only adds the look.

Back to [SKILL.md](../SKILL.md). Command options: [cli.md](cli.md). Building for the shot: [film-and-video.md](film-and-video.md). Checked with Blender 5.2.1 on Windows 11,
2026-10-13 (240 figures, 81 frames, four passes at 832x480 in 81 s on the CPU). The depth video then drove
MiniMax H3 through Fun ControlNet Union 2.0 on a 16 GB card: formation, direction, camera and the moment the
lines meet all followed the blockout (608x352, 56 frames, 27 to 36 s). Wan is untested; see Open below.

## What `pw.py crowd` makes

| Output | What it is | Feed it to |
|---|---|---|
| `depth/` `depth.mp4` | inverse depth, near white, far and sky black, one range for the whole shot | VACE or Fun Control depth input (the main control) |
| `mist/` `mist.mp4` | with `--passes depth,mist`: Blender's Mist pass over the same range, near white, 16-bit grey, from the same render | the depth input instead; one blind H3 test preferred it (film-and-video.md) |
| `pose/` `pose.mp4` | OpenPose COCO-18 skeletons, only figures taller than `--pose-min-px` (40) | pose input, for the front ranks; or blend over depth |
| `mask/` `mask.mp4` | side A red, side B blue, all else black; exact colours only (Workbench anti-aliasing and dither off), so a colour key needs no tolerance | per-side masks for VACE inpainting, per-side prompts, grading |
| `clay/` `clay.mp4` | lit grey render, sides tinted | repaint frame 1 with an image model as the start frame |
| `camera.json` | per-frame `matrix_world`, lens, sensor | camera-control models, matching plates later |
| `joints.json` | 2D joints per frame | redrawing pose with other styles |
| `sheet.png` | first, middle, last frame of each pass | read this one image to check the shot |

Figures are low-poly soldiers (torso, head, limbs, optional spear, shield, helmet) with a procedural walk cycle.
Every figure gets its own step phase, pace (0.9 to 1.1), height (0.94 to 1.06), placement jitter and a small yaw,
so no two move in sync: the clone look comes from synchronised motion as much as from identical faces.

**Two different sides** (a drilled line against a wild horde): side B can have its own placement jitter
(`--jitter-b`, 1.5 m or more breaks its ranks into a scattered swarm, which then runs right up to the line
instead of halting rank by rank), kit (`--kit-b ""` for bare figures), height (`--scale-b 0.8` for figures
shoulder-high to side A) and charge start spread (`--stagger-b` seconds, default 0.4). Tested on 10 spearmen
against 10 creatures (2026-10-25): the swarm read as no formation in the depth video, and the video model kept it
at 0.6 and 0.8 strength; the smaller blockout height did not carry into the render at either strength, so say the
height in words as well and check it.

**Reserves behind the lines** (`--scatter N`): about N standing figures per side, Poisson-scattered behind the
last rank with at least `--scatter-gap` (1.2 m) between them over `--scatter-depth` (25 m), drawn from three
variants (heights 0.95 to 1.05, one without a helmet, one without a shield) with random yaw and scale. They are
Geometry Nodes instances, so they cost no render time (a 3-frame preview took 2.0 s with 160 of them and
without), carry their side's colour in mask and clay, and sit inside the depth range. They hold still and get no
skeletons. Poisson spacing drops some points: 200 asked gave 113 to 160. With `--view behind` the camera stands
in side A's rear, so only side B gets reserves (`scatter_skipped` says so); in the default side and high views
the reserves fall outside the frame unless the camera is widened (`--cam-dist`, `--lens`).

## Defaults that matter

- **Sizes and length**: 832x480 or 1280x720, 4n+1 frames (49, 65, 81) at 16 fps for Wan; for MiniMax H3
  `--fps 24` and 17k+5 frames (56, 73, 209). The command refuses other counts and sizes not divisible by 16
  unless `--any-size`.
- **Screen direction**: side A starts left and moves right, side B the other way, for every view, so a cut
  between shots never flips a side. Keep the camera on one side of the battle line (x = 0) in every shot.
- **Actions**: `hold`, `march` (1.3 m/s), `advance` (2 m/s), `charge` (5 m/s, spears levelled), `clash` (ranks
  halt in turn at the line and thrust). For clash and charge the starting gap defaults to what both sides cover
  in two thirds of the shot, so they meet on screen. A two-figure clash (`--ranks 1 --cols 1`) needs a smaller
  `--gap` (5 m at 9 m back) or both start out of frame, and `--far` past the ground in view, since the default
  far plane stops just past the farthest figure and turns the field behind a duel black like the sky.
- **Views**: `side` (elevated 6 m, looking down the frontage: both armies, ranks stacked in depth), `behind`
  (over side A's shoulders at the enemy), `high` (crane, god's eye), or `--cam x,y,z --aim x,y,z`. Moves:
  `static` (default; the model spends its capacity on bodies, not camera), `push`, `crane`, `truck`.
- **Depth range**: fixed for the whole shot, from the nearest ground in frame to past the farthest figure. A range
  per frame makes the depth video pulse, which the model reads as motion.
- **Depth convention**: inverse depth (1/z), the way Depth Anything and MiDaS output it, which is what VACE's
  and Fun Control's depth preprocessors produce. Unverified whether linear depth does better; compare once.

## Driving the video model (local, 16 GB)

1. Preview first: `pw.py crowd --out work/crowd --action clash --preview`, read `sheet.png`, adjust ranks,
   lens, view and gap, then render the full shot (about a second per frame on a CPU).
2. Start frame: repaint `clay/0001.png` with an image model (a depth or canny ControlNet on the clay frame, or
   an edit model with the costume prompt), approve it as a still, fix faces and limbs there.
3. Video: Wan VACE (`WanVaceToVideo`: control video = `depth.mp4`, reference or first frame = the approved
   still, length = the frame count), Wan 2.2 Fun Control (`Wan22FunControlToVideo`, depth input), or MiniMax
   H3 with Fun ControlNet Union 2.0 (`MiniMaxH3FunControlNetApply`, strength about 0.8, released at 60% of the
   steps so texture comes back). Start with
   depth alone; add pose only if the front ranks lose their limbs.
4. Prompt the look, not the count: costume and banner colour per side, light, haze, dust; "no identical faces";
   the camera words. The blockout already holds the numbers and positions.
5. Faces at 20 px will not hold; carry identity with costume and colour. Detail only the 2 to 5 nearest
   figures (crop, low-denoise V2V, paste back).

Hosted models that take a reference or driving video (Runway Aleph, Luma Modify, Kling) can take `clay.mp4` the
same way. One practitioner rule for those: coarse proxies work better than detailed ones, and name each group by
role in the prompt rather than by its blockout colour.

## Extending it

- Your own soldier: `--save-blend`, then replace the part meshes in `crowd.blend` with a rigged figure, or build
  a bank of 6 to 8 animated variants with offset NLA strips and instance them; Quaternius (CC0 animation library)
  and MPFB (CC0 characters) are the free sources.
- A real or generated set (terrain from `pw.py place`, a splat, a castle) goes in the `.blend` before rendering;
  the depth pass then carries the set too.
- Cavalry, siege engines, arrows: not built in; add them as objects in the saved `.blend`.
- Debris, a falling wall, banners and cloaks: bake rigid bodies and cloth headless in the saved `.blend`, then
  render the passes (recipes `rigidbody-bake`, `cloth-bake` in polywright-blender). Birds or a routed crowd: a
  Boids particle system follows a stack of rules (goal, avoid, separate, flock, follow the leader); the rule
  names exist in 5.2, the behaviour is untested here.

## Two fighters (`pw.py duel`)

A duel needs the bodies, their facing and the blades in the control; a still Canny of the empty set holds only
the room, and video takes then drift to both fighters facing the lens. `pw.py duel shot.json` builds the set,
stands two crowd mannequins at their marks, poses them by two-bone IK to hand and foot targets (knee pole along
the chest, elbow pole down and out) and renders through the shot's camera. Start from
[../examples/duel.json](../examples/duel.json) (with its room script [../examples/duel_room.py](../examples/duel_room.py)).

- **Room**: `{"blend": "set.blend"}`, or `{"script": "room.py", "call": "build"}` (run inside Blender; it reads
  the duel file as `DUEL` and builds geometry only), or nothing for a plain floor. Reuse the set's own blockout
  script so the figures stand in the room the other controls already use.
- **Camera**: `{"pos", "aim", "lens"}` or `{"object": "Name"}` made by the room. `origin` [x, y] is added to every
  mark and landing point, so a set plan's coordinates paste in.
- **Fighters**: `mark`, `facing` (compass degrees, 0 = +Y, 90 = +X, or the other fighter's name), `scale`,
  `tint`, `weapons` {"right": m, "left": m}, `cloak`, and `keys` [[seconds, pose], ...]: held before the first
  and after the last key, smoothstep between.
- **Poses**: a `base` plus overrides in the fighter's frame (faces +X, left +Y): `root`, `yaw`, `pelvis_z`,
  `spine`, `chest`, hands from the shoulder, blade directions (null drops the blade), feet. Built in: stand,
  guard, guard_low, kneel.
- **Thrown props** (`fly`): blades, guards, a hood and cloak go from where they were at `t0` to a floor mark by
  `t1`, arcing and spinning.

Output per shot: `clay/` (Workbench at twice the size, for a start frame), `canny/` (OpenCV's Canny steps in
numpy, thresholds 12/40; it matched OpenCV within one pixel on 97 to 100 percent of edge pixels), `depth/`,
`depth_thick/` (blades `thick_blade_m`, 4.5 cm, square: at a 4 m two-shot the real 1.6 cm blade is a broken
line), `pose/` (COCO-18, nose and eyes left out once turned from the lens, see L-005), `<name>_<pass>.mp4`,
`joints.json`, `camera.json` and `sheet.png` at frame 1, each `check_s` second and the last frame. The result
warns when a fighter has under half its joints in frame at either end. 73 frames at 864x480 take about 30 s.

What each control held on MiniMax H3 with Fun ControlNet Union 2.0 at 0.6 strength ending at 0.4 (field test,
2026-10-17): Canny of the clay with the figures removed a duplicated fighter and held a floor shot's start and
end states, but a standing two-shot still drew both outlines facing the lens; thick-blade depth held the near
fighter's back to the camera through the action, then he turned to the lens. Next to try: key the near fighter's
back to the camera through the last frame, and depth at 0.8 ending at 0.6.

Check every key pose on the sheet before rendering video. A box mannequin reads well standing, kneeling and
kicking, and badly on the floor (a man on his back is a crumpled block); use a rigged figure for falls and rolls.
Check also that each end state is inside the shot's own frame (L-005).

## Open

- Animation principles not yet tried on a video model (after Hess, *Tradigital Blender*, in our words; `duel`
  smoothsteps between held keys today): a wind-up key 2 to 6 frames before each strike, since a pose change with
  no anticipation can read as a jump cut; hands and feet starting one or two frames apart instead of together; a
  small drift (1 to 2 cm, 1 to 2 degrees) through a hold, since a frozen mannequin may freeze the person; hand
  paths bent through an arc instead of a straight line; cloak and blade tip lagging the hand by 2 to 4 frames on
  fast moves; quick light blades, longer settles after heavy blows, a sharp contact key with an ease out after.
  Test one at a time against the same take.

- Control strength (H3, 2026-10-13): 0.8 released at 60% of the steps gave the exact formation with uniform,
  slightly clone-like soldiers; 0.6 released at 40% kept the layout and timing with more varied figures, and a
  few cloaks crossed sides at the clash. Without control the model drew two blocks from words alone but met
  later and looser than planned.
- Not yet run through Wan VACE or Fun Control; not yet tested with pose, or with a repainted clay start frame.
- Whether a gamma on the depth (more tones for the front ranks) beats plain inverse depth.

Sources: Wan VACE (github.com/ali-vilab/VACE), ComfyUI WanVaceToVideo and Wan 2.2 Fun Control docs
(docs.comfy.org, checked 2026-10-13); RunComfy Blender to ComfyUI AI Renderer 2.0 workflow (2026); smixs
visual-skills blockout rules (CC BY 4.0, idea only); seedance.tv ComfyUI crowd workflow (2026-09-13);
House of David season 2 making-of (VP Land, 2025-10-16). Full notes: [RESEARCH.md](../RESEARCH.md) R-20261013-1.
