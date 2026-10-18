# Tests: polywright-finish

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the evergreen plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines.

## Runs

### T-20261017-2 · 2026-10-17 · tests/run_evals.py, action and outcome cases three runs each, installed 0.2.1 loaded from the checkout; outcome baselines without polywright · Windows 11 dev machine, Blender 5.2.1 · 6/6
- action-1 3/3, outcome-1 3/3 (trace and answer evidence).
- Baseline without the skill: outcome-1 3/3. The outcome cases do not discriminate: the model answers them from general knowledge. Sharper outcome cases (polywright-specific facts or commands) are owed.
- Whole suite: 42/42 graded plus crowd 3/3 by hand ($16.16); baselines 20/21 ($5.26).
- led to: none (HANDOFF owed: sharper outcome cases)

### T-20261017-1 · 2026-10-17 · tests/run_evals.py: headless claude -p, three runs per case, fresh session in a throwaway copy, this checkout through --plugin-dir, installed polywright off · Windows 11 dev machine, Claude Code 2.1.281 · 11/12
- trigger-1 · trigger · sibling took it: 1 of 3 runs loaded the hub (which routes here) for 'make this 400k model work in Roblox'
- rerun unchanged: trigger-1 3/3
- Trigger and decoy cases only; action and outcome cases and baselines without the skill are still owed. Whole suite: 80/87 first pass ($29), the four weak cases 24/24 after the fixes.
- led to: none (the hub routing to finish is acceptable; watch it)

### T-20261011-2 · 2026-10-11 · headless claude -p, one run per case, fresh session, plugin installed from a local marketplace 0.1.1 · Windows 11 dev machine · 3/4
- trigger-1 · trigger · the hub fired instead and owns the hand-off to finish; acceptable family routing
- First pass the same day (descriptions of 0.1.0) passed 17/28 over all seven skills; the descriptions were made explicit about when to fire (C-20261011-2). A harness bug (subprocess could not start claude.cmd) made an earlier run report 0 invocations; not counted.
- led to: C-20261011-2

### T-20261011-1 · 2026-10-11 · not yet run · skill · 0/0
- Suite written (two triggers, two decoys, one action case with trace evidence, one outcome case); no agent run recorded yet. The scripts it relies on are covered by tests/test_pw.py and tests/test_recipes.py (all passing on Windows 11 with Blender 5.2.1).
- led to: none
