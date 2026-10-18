# Real figures and toys as models for AI video

When a video model keeps getting a small cast wrong (sides swapped, an extra figure, a character drawn twice,
markings lost), build each figure as a mesh from photos and hand the video model two things made from the meshes:
clean reference pictures (`pw.py turnaround`) and a blockout of who stands where (`pw.py lineup`). The meshes are
rigid statues; posing them needs a rig (polywright-finish).

Back to [SKILL.md](../SKILL.md). Commands: [cli.md](cli.md). Crowds of dozens or hundreds: [crowd-blockouts.md](crowd-blockouts.md).
Building for the shot: [film-and-video.md](film-and-video.md).
Worked through on 2026-10-16 with four jointed 13 cm toy figures and five accessories photographed lying on a table
(Blender 5.2.1, ComfyUI 0.38.2 with TRELLIS.2 on a 16 GB card).

## Route per figure

1. **Crop the photo** upright, one subject per crop; record the photo as a source.
2. **Clean views** with an image-edit model (FLUX.2 Klein or Qwen Image Edit): front, three-quarter, side and back,
   full length, standing straight, flat grey (polywright-references). A figure photographed lying down or with its
   legs crossed comes back standing straight from the edit; check it against the photo.
3. **Colour from pixels, not words.** Measure the plastic's median hue, saturation and value on the photo and say
   those (or nothing) in the edit prompt: a colour word wins over the picture ("olive" drew khaki for a teal toy).
   Colour-match the chosen view to the photo before meshing.
4. **Mesh the front view** with TRELLIS.2 (`pw.py gen --workflow <template> --set 316.value=true`). Warm runs took
   73 to 190 s each for figures and small props (377 s cold); the shape of jointed figures, claws, horns and
   hooked weapon pegs came out clean and upright, facing -Y.
5. **Fix what the generator bakes wrong** with `pw.py mark`:
   - the texture's colour drifts (teal came back slate blue): `--recolour H,S,V` with the photo's medians;
     limit it with `--from-hue LO,HI`, and on a black figure with one coloured part add `--min-sat 0.35
     --min-val 0.16`, or the black body's faint tint is brightened into speckle;
   - painted markings (a letter, a number) bake as smears, because the head is a few dozen pixels in the 1024 px
     input: `--erase white|red` clears that colour on the head's front faces only (their UV islands), and
     `--text A --colour R,G,B --font F` stands a thin text mesh on the face, seated on its most forward part;
   - real size: `--height-m` for figures, `--longest-m` for props lying any way.
6. **Look** with `pw.py turnaround` next to the photo; re-run a bad prop from another view or seed. A thin, flat
   accessory (a shoulder plate) can grow strap-like bits from a three-quarter view and blob from a front one.

## What goes to the video model

- **References:** `pw.py turnaround out/x.glb --out renders/turnaround` gives front, 3q, side and back on
  mid-grey (sRGB 0.5) with flat light and an 85 mm eye-level camera, plus `sheet.png`. One figure per picture.
  Props: `--views front,3q,side,3q_back --size 768x768 --elev 20`.
- **Who stands where:** `pw.py lineup --layout layout.json --out DIR --frames 107,362 --card standoff` puts the
  meshes on a table with each team on a fixed side and writes `colour.png` (textured: a start or guide frame),
  `clay.png`, `depth.png` (inverse depth, near white, the crowd convention), `mask.png` (team a red, team b blue),
  `lineup.json` (camera, depth range, each figure's screen box, `left_to_right`) and looped control videos. The
  figures do not move, and a looped still control freezes the action: on a four-figure toy fight (2026-10-17) depth
  at 0.6, end 0.3 over a 362-frame fight kept snapping the figures back to their spots while copies fought.
  Pass `colour.png` as an H3 guide at frame 0 instead (four figures and the sides held, the look stayed real
  footage) and let the prompt carry the action; use the control only in a short standoff section of its own.

Layout file (paths relative to it; `face` is +x, -x, +y, -y or a heading in degrees, 90 = +x):

```json
{"size": [864, 480], "lens": 35, "cam": [0, -0.5, 0.065], "aim": [0, 0, 0.07], "backdrop_m": 0.6,
 "table": {"size_m": 1.6, "colour": [0.62, 0.45, 0.30]},
 "figures": [{"name": "a", "file": "a/out/a.glb", "height_m": 0.13, "at": [-0.2, 0.03], "face": "60", "team": "a"},
             {"name": "b", "file": "b/out/b.glb", "height_m": 0.13, "at": [0.2, 0.03], "face": "-60", "team": "b"}]}
```

A camera 0.5 m back and 6.5 cm high with a 35 mm lens fits four 13 cm figures across 0.4 m, each about 45 % of the
frame's height: toy eye level. Colours are sRGB.

## Failure modes seen in the reference views

- A face close-up of a faceless toy head drew a human face under it; drop face views for such figures.
- Back views painted the front marking on the back of the head as well; a side view turned an embossed number red,
  another doubled a painted one. Mesh from the front view only, and check each view before using it as a reference.
- A three-quarter view that barely turns is common; it is still a usable reference.

## Records

Each figure is one asset folder (`pw.py new`); record the photo, the chosen view (model and seed), the tools,
the outputs (`--add-output out/x.glb --inspect`, now resolved inside the asset folder) and the look
(`--review renders/turnaround/sheet.png --verdict "..."`).
