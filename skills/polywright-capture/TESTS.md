# Tests: polywright-capture

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the evergreen plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines.

## Runs

### T-20261017-1 · 2026-10-17 · tests/run_evals.py: headless claude -p, three runs per case, fresh session in a throwaway copy, this checkout through --plugin-dir, installed polywright off · Windows 11 dev machine, Claude Code 2.1.281 · 12/12
- Trigger and decoy cases only; action and outcome cases and baselines without the skill are still owed. Whole suite: 80/87 first pass ($29), the four weak cases 24/24 after the fixes.
- led to: none

### T-20261011-3 · 2026-10-11 · headless claude -p in a throwaway clone, action-1 once · Windows 11 dev machine, Blender 5.2.1 · 0/1
- action-1 · action · no-op of the skill · pw.py place ran correctly but the prompt spelled out the command, so the skill was not loaded; prompt rewritten to a natural request
- led to: case prompt rewritten (C-20261011-2)

### T-20261011-2 · 2026-10-11 · headless claude -p, one run per case, fresh session, plugin installed from mark-local 0.1.1 · Windows 11 dev machine · 4/4
- all trigger and decoy cases passed
- First pass the same day (descriptions of 0.1.0) passed 17/28 over all seven skills; the descriptions were made explicit about when to fire (C-20261011-2). A harness bug (subprocess could not start claude.cmd) made an earlier run report 0 invocations; not counted.
- led to: C-20261011-2

### T-20261011-1 · 2026-10-11 · not yet run · skill · 0/0
- Suite written (two triggers, two decoys, one action case with trace evidence, one outcome case); no agent run recorded yet. The scripts it relies on are covered by tests/test_pw.py and tests/test_recipes.py (all passing on Windows 11 with Blender 5.2.1).
- led to: none
