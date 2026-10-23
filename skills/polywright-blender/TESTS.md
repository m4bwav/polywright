# Tests: polywright-blender

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the evergreen plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines.

## Runs

### T-20261022-1 · 2026-10-22 · tests/test_recipes.py · Windows 11, Blender 5.2.1 · 20/20
- Nine new recipes in bpy-recipes-scenes.md and bpy-recipes-physics.md pass; mutations of three (reversed depth range, unlinked scatter gap, applying location with scale) each fail their recipe.
- led to: C-20261022-1, L-007

### T-20261017-2 · 2026-10-17 · tests/run_evals.py, action and outcome cases three runs each, installed 0.2.1 loaded from the checkout; outcome baselines without polywright · Windows 11 dev machine, Blender 5.2.1 · 6/6
- action-1 3/3, outcome-1 3/3 (trace and answer evidence).
- Baseline without the skill: outcome-1 3/3. The outcome cases do not discriminate: the model answers them from general knowledge. Sharper outcome cases (polywright-specific facts or commands) are owed.
- Whole suite: 42/42 graded plus crowd 3/3 by hand ($16.16); baselines 20/21 ($5.26).
- led to: none (HANDOFF owed: sharper outcome cases)

### T-20261017-1 · 2026-10-17 · tests/run_evals.py: headless claude -p, three runs per case, fresh session in a throwaway copy, this checkout through --plugin-dir, installed polywright off · Windows 11 dev machine, Claude Code 2.1.281 · 10/12
- trigger-1 · trigger · undertrigger: 2 of 3 runs answered the removed-importer AttributeError correctly from memory
- after C-20261017-1: trigger-1 3/3, decoy-2 3/3
- Trigger and decoy cases only; action and outcome cases and baselines without the skill are still owed. Whole suite: 80/87 first pass ($29), the four weak cases 24/24 after the fixes.
- led to: C-20261017-1

### T-20261011-2 · 2026-10-11 · headless claude -p, one run per case, fresh session, plugin installed from a local marketplace 0.1.1 · Windows 11 dev machine · 2/4
- trigger-1 · trigger · undertrigger: the model fixed the bpy import error from its own knowledge
- trigger-2 · trigger · undertrigger: the model wrote a batch-export script without loading the skill
- First pass the same day (descriptions of 0.1.0) passed 17/28 over all seven skills; the descriptions were made explicit about when to fire (C-20261011-2). A harness bug (subprocess could not start claude.cmd) made an earlier run report 0 invocations; not counted.
- led to: C-20261011-2

### T-20261011-1 · 2026-10-11 · not yet run · skill · 0/0
- Suite written (two triggers, two decoys, one action case with trace evidence, one outcome case); no agent run recorded yet. The scripts it relies on are covered by tests/test_pw.py and tests/test_recipes.py (all passing on Windows 11 with Blender 5.2.1).
- led to: none
