# Supports and slicing, from the modeller's side

Back to [../SKILL.md](../SKILL.md). Design rules: [dfam.md](dfam.md). Printer settings (support keys, plate,
filament, purge) belong to a printer or slicer skill when one is installed; this page is what the mesh must
get right so those settings have little to fix. Checked 2026-10-17 against the Bambu Lab wiki, BambuHub,
the Prusa knowledge base, Formlabs, Chitubox and Lychee pages ([../RESEARCH.md](../RESEARCH.md) R-20261017-2).

## Choose the orientation before the details

Orientation decides which faces carry support scars, where layer lines run and how much touches the plate.
Decide it in the brief, then model for it:

- Show face up or sideways, never down onto supports. Undersides nobody sees (a car floor, a soffit, the bottom
  of a base) are where scars may go.
- Largest flat face on the plate. A part with no flat face gets one: a base, a plinth, a flat cut.
- Layers are weakest across Z: thin upright stalks (antennas, spears, flagpoles) are thickened or laid flat.
- A slicer's auto-orient minimises support volume, not visible scars; check its pick against the brief.

## Overhangs, bridges and islands

- Faces up to 45 degrees from vertical print without support; Bambu Studio supports anything flatter than
  30 degrees from the horizontal by default (its `threshold angle`). Between the two, slow overhang speeds and
  fans carry it.
- Chamfer a ceiling to 45 degrees where nobody looks; teardrop horizontal holes; chamfer (never fillet)
  bed-facing edges, 0.3 to 0.5 mm, which also hides elephant's foot.
- Bridges up to 10 to 20 mm print clean between two supports. A hollow shell's roof is a bridge: fill it
  (`pw.py printable` does) rather than leave it.
- An island is a point whose lowest layer touches nothing (a chin, a fingertip, a hanging mirror). Give it a
  45-degree cone back to the body, or accept one support branch there and say so.

## Where supports scar, and how tree and normal differ for the model

- Normal (grid) supports fill straight down under the overhang and leave a large rough area; good under
  big flat ceilings. Tree or organic supports grow branches that touch only at their tips and route around
  the model; good under figures, cars and curves. Bambu's hybrid puts a grid under large flat areas and
  branches elsewhere (BambuHub, 2026-10-04).
- Every contact point leaves a mark. Branch tips are small, so a curved underside takes them well; a flat
  ceiling over a show face does not. Move the overhang onto a hidden face, or split there.
- "On build plate only" (a default in some printer profiles) means no support may stand on the model:
  an overhang above another part of the model gets none, so it must be modelled self-supporting.
- The support's air gap (top Z distance, about 0.2 mm in one material) means the supported face prints
  rougher than a top face; do not put fine detail on it.
- Support painting (enforcers, blockers, blocker objects) lives in the slicer, not the mesh. Do not model
  support columns or rafts into an FDM mesh.

## Split instead of supporting

Splitting is the modeller's best support tool: each part gets a flat face down and its show face up.

- Cut along natural seams (waist, sleeve, roof line, body line), not through detail.
- Connectors on the cut faces, which are flat and face down: 3 mm pins in 3.3 mm holes, holes for 1.75 mm
  filament dowels, or dovetails; 0.2 mm clearance for a glued fit.
- Bambu Studio's Cut tool does planar and dovetail cuts with dowel or plug connectors and lists "reduced
  supports" as a reason to cut (wiki 2026-09-15); model the split yourself when it must follow a curve.
- Ship the parts as separate objects in one 3MF (`pw.py 3mf a.stl b.stl --out x.3mf`), named in assembly order.

## Brims and first-layer contact

- The first layer holds everything above it. Small contact (four tyres, two feet, a tall tower) needs a base
  or plinth, or a brim the slicer adds; never model a brim, it is a setting and peels off clean.
- Bambu Studio can add brim ears on painted spots and a brim under tree supports; elephant-foot
  compensation exists, a bottom chamfer still helps.
- The base must be flat to the plate within a tenth of a millimetre; `printable` clamps it (`--base-cut-mm`).

## What the slicer already does, so the model does not fake it

Supports (tree, normal, hybrid, painted), brims and ears, rafts, ironing of flat tops, variable and adaptive
layer height (finer layers on domes and slopes; 0.08 to 0.28 mm on a 0.4 mm nozzle), overhang slow-down, the
prime tower and flushing. Model only what changes the part: chamfers, thicker stalks, splits, pins, a base,
colour parts.

## Multi-colour (AMS and other changers)

- Colours come from separate closed parts in one 3MF (one filament each) or from painting in the slicer.
  Model colour regions as separate solids that touch along clean boundaries.
- Every change purges filament, and the prime tower rises to the last layer that has a change. Put colour
  changes low or in few layers: flipping one part so its colours sat at the bottom cut its tower by about 40%
  in Bambu's example (wiki 2026-02-11). Changes per layer are the colours on that layer minus one, so
  horizontal colour bands (strata) cost less than vertical stripes.
- Objects on one plate with different variable layer heights cannot share a prime tower.

## Resin

- Resin wants hollowing: parts above a few centimetres hollow with 1.5 to 2.5 mm walls (PrusaSlicer's minimum
  is 1 mm), at least two drain holes, one near the plate side.
- Suction cups: a hollow or a cup open toward the plate traps resin and pulls on each layer; vent it or
  orient it away.
- Tilt 30 to 60 degrees (45 is the usual start) so no layer has a large cross-section, with the supports on
  the back and underside; check islands layer by layer (Lychee and Chitubox have detectors).
- Detail to about 0.3 mm survives; supports are many fine tips, so they scar less than FDM supports.
- "Pre-supported" files carry the creator's chosen orientation and supports for resin, often as a Lychee
  project; also ship the unsupported model.

## Miniatures (28 to 32 mm)

- Resin for faces and hands (about 0.05 mm XY against 0.1 mm on FDM); FDM needs a 0.2 mm nozzle and 0.08 mm
  layers for weapons and faces. Heroic proportions (dfam.md); thin gear at least 1 mm or split off.
- Keep a resin mini solid at this size. On FDM, print upright on the base; the base is the contact, so no brim.
- Image-to-3D figures are often double-walled shells: run `printable`, then `check --target print-fdm` and read
  `thickness.thin_fraction`; a large share under 0.9 mm with a small volume is still hollow.

## Hand-off to the slicer

Deliver the STL (verified) and a geometry-only 3MF; say in the hand-off which face is up, where supports are
expected, which parts are separate and which colour each is. Slicer CLIs (table in [dfam.md](dfam.md)) can
open, orient, arrange and slice; Bambu Studio's `--export-3mf out.3mf in.3mf` works headless and reports in
`result.json`. Process, filament and support settings go to a printer or slicer skill when one is installed;
otherwise the user picks them in the slicer.
