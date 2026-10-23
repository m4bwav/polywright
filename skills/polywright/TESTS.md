# Tests: polywright

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the evergreen plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines.

## Runs

### T-20261022-1 · 2026-10-22 · tests/run_evals.py, action cases three runs each with the checkout loaded, one baseline each without polywright · Windows 11 dev machine, Blender 5.2.1
- action-scatter (new) 3/3: every run called `pw.py crowd ... --scatter` and read the sheet. Baseline 1/1 too: the throwaway copy holds the repository, and the baseline found `--scatter` in cli.md. Does not discriminate (the known caveat of this harness).
- polywright-finish action-topology (new) 2/3: r2 and r3 ran `inspect --topology` and `convert --fix-winding`; r1 loaded no skill and fixed the 12-triangle fixture by hand, correctly (finish L-002). Baseline 0/1.
- Unit suite: test_pw 56 (7 new), test_recipes 20 (9 new); every new check mutation-tested (12 mutations, all caught).
- Cost $3.73 with the skill, $1.25 baselines.
- led to: C-20261022-4, polywright-finish L-002

### T-20261017-2 · 2026-10-17 · tests/run_evals.py, action and outcome cases three runs each, installed 0.2.1 loaded from the checkout; outcome baselines without polywright · Windows 11 dev machine, Blender 5.2.1 · 9/9
- action-crowd 3/3 by hand (every run called `pw.py crowd --preview` and read sheet.png); action-1 3/3, outcome-1 3/3 (trace and answer evidence).
- Baseline without the skill: outcome-1 2/3. The outcome cases do not discriminate: the model answers them from general knowledge. Sharper outcome cases (polywright-specific facts or commands) are owed.
- Whole suite: 42/42 graded plus crowd 3/3 by hand ($16.16); baselines 20/21 ($5.26).
- led to: none (HANDOFF owed: sharper outcome cases)

### T-20261017-1 · 2026-10-17 · tests/run_evals.py: headless claude -p, three runs per case, fresh session in a throwaway copy, this checkout through --plugin-dir, installed polywright off · Windows 11 dev machine, Claude Code 2.1.281 · 15/15
- Trigger and decoy cases only; action and outcome cases and baselines without the skill are still owed. Whole suite: 80/87 first pass ($29), the four weak cases 24/24 after the fixes.
- led to: none

### T-20261011-2 · 2026-10-11 · headless claude -p, one run per case, fresh session, plugin installed from a local marketplace 0.1.1 · Windows 11 dev machine · 3/4
- trigger-1 · trigger · routed to polywright-capture (a real fountain in a real park: capture owns it); acceptable family routing
- First pass the same day (descriptions of 0.1.0) passed 17/28 over all seven skills; the descriptions were made explicit about when to fire (C-20261011-2). A harness bug (subprocess could not start claude.cmd) made an earlier run report 0 invocations; not counted.
- led to: C-20261011-2

### T-20261011-1 · 2026-10-11 · not yet run · skill · 0/0
- Suite written (two triggers, two decoys, one action case with trace evidence, one outcome case); no agent run recorded yet. The scripts it relies on are covered by tests/test_pw.py and tests/test_recipes.py (all passing on Windows 11 with Blender 5.2.1).
- led to: none
