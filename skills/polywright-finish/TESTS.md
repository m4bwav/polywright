# Tests: polywright-finish

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the evergreen plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines.

## Runs

### T-20261011-1 · 2026-10-11 · not yet run · skill · 0/0
- Suite written (two triggers, two decoys, one action case with trace evidence, one outcome case); no agent run recorded yet. The scripts it relies on are covered by tests/test_pw.py and tests/test_recipes.py (all passing on Windows 11 with Blender 5.2.1).
- led to: none
