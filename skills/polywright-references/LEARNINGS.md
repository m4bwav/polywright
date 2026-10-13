# Learnings: polywright-references

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · A no-shadow prompt still produced a cast shadow
- Trigger: Z-Image Turbo, 'no cast shadow' in the prompt, fountain reference 2026-10-11
- Hypothesis: Product-photo wording pulls in a ground shadow
- Rule: Keep background removal in the path (pw.py gen uses rembg when installed) and do not reject an otherwise good reference for a soft shadow
- Evidence: T-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11

### L-002 · 2026-10-12 · A designed prop's reference sheet comes from a model, not from prompts
- Trigger: the No-God film's Spear: five text-to-image rounds gave half the head per seed (an S-prong without the crescents, or crescents without the S); the owner then gave six notes (swept forward, tips parallel to the head, the fan sheet's proportions, a trigger, missing wings in two views) and each was a seconds-long rebuild and re-render.
- Hypothesis: a generator samples a plausible object near the words; a model is the object, so every view agrees and each note changes only what it names.
- Rule: when a designed prop fails twice as text, build it (polywright-blender L-003) and render the sheet from it: side (raised 10 to 15 degrees for paired parts) and top orthographic on flat mid-grey, Cycles on the CPU, composited with PIL. Keep each superseded sheet with a version suffix so the owner can point at one ("v5 is good").
- Evidence: 2026-10-12 No-God film: D:/ComfyUI/output/video/nogod/refs/spear/ (build_spear.py, render_views.py, camera_match.py, _sheet_v1..v5c.png); nogod/refs/heron_spear.png, heron_spear_3view.png.
- Scope: skill (Step 2b)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-12
