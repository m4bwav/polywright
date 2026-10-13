# Changelog: polywright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261012-1 · 2026-10-12 · pw.py match and "Compose a model into a picture"
- because: L-003 (a designed prop pasted into the No-God film's set still from a camera solved from two pixels and a depth); polywright-blender L-004 (bpy option order)
- files: SKILL.md description and new section "Compose a model into a picture"; scripts/pw.py (`match`, `split_bpy_args`), scripts/pw_bpy.py (`act_match`); references/cli.md; tests/test_pw.py
- New command renders a model RGBA from a picture's camera, pastes it, and writes a blend mask; `pw.py bpy` takes its options on either side of the script name.

### C-20261011-2 · 2026-10-11 · Description says when to fire
- because: T-20261011-2 first pass (undertriggering: prompts answered without the skill; hub and finish both claimed game-readiness)
- files: SKILL.md frontmatter description, evals/evals.json trigger-2
- Descriptions open with 'Use whenever ...' and name the requests each skill owns; the hub only takes requests no sibling owns.

### C-20261011-1 · 2026-10-11 · Created as an evergreen unit
- because: user request (an evergreen 3D modelling plugin); research R-20261011-1 to R-20261011-3
- files: SKILL.md, references/, RESEARCH.md, LEARNINGS.md, TESTS.md, evals/evals.json, evergreen.json
- Initial version, tier `fast`, interval 14d, written from the five research notes of 2026-10-11 and the verified runs logged in LEARNINGS.md.
