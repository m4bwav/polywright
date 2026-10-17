# Changelog: polywright-generate

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261017-2 · 2026-10-17 · Pixal3D output is levelled by pw.py convert --level
- because: HANDOFF owed item 2 (Pixal3D's camera-frame output leans by the camera's elevation); tested on the 2026-10-11 Pixal3D fountain (17.7 degrees, 9 s, both side views upright)
- files: SKILL.md Step 2; references/generators.md (Running on ComfyUI table); ../polywright/scripts/pw.py, pw_bpy.py level_rotation; ../polywright/references/cli.md
- "level it" now names the command.

### C-20261017-1 · 2026-10-17 · trigger-1 names a real drawing
- because: T-20261017-1 (trigger-1 0/3: "from this drawing" named no file, so every run searched for it and ran out of turns)
- files: evals/evals.json trigger-1; ../../tests/fixtures/dragon.png
- The case now points at a small drawing in the fixtures. No change to SKILL.md.

### C-20261016-1 · 2026-10-16 · Warm TRELLIS.2 timing; markings and colour fixed with pw.py mark
- because: L-003
- files: SKILL.md Step 2 (run times, point 5)
- Warm TRELLIS.2 runs are 73 to 190 s; painted markings and colour drift are fixed with `pw.py mark`.

### C-20261011-3 · 2026-10-11 · Editor-format workflows run as is; Pixal3D tested
- because: L-002, R-20261011-3
- files: SKILL.md Step 2, references/generators.md (Running on ComfyUI), ../polywright/scripts/pw.py (ui_to_api, --save-api, node_errors in failures)
- `pw.py gen --workflow` converts a workflow saved by ComfyUI's editor (a template file) with the host's node definitions; a rejected graph now prints ComfyUI's node_errors; Pixal3D's run and its camera-frame tilt are recorded.

### C-20261011-2 · 2026-10-11 · Description says when to fire
- because: T-20261011-2 first pass (undertriggering: prompts answered without the skill; hub and finish both claimed game-readiness)
- files: SKILL.md frontmatter description
- Descriptions open with 'Use whenever ...' and name the requests each skill owns; the hub only takes requests no sibling owns.

### C-20261011-1 · 2026-10-11 · Created as an evergreen unit
- because: user request (an evergreen 3D modelling plugin); research R-20261011-1 to R-20261011-2
- files: SKILL.md, references/, RESEARCH.md, LEARNINGS.md, TESTS.md, evals/evals.json, evergreen.json
- Initial version, tier `fast`, interval 14d, written from the five research notes of 2026-10-11 and the verified runs logged in LEARNINGS.md.
