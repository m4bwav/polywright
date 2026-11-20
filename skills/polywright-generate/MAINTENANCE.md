# Maintenance: polywright-generate

This unit is evergreen and follows the same protocol as the hub: [../polywright/MAINTENANCE.md](../polywright/MAINTENANCE.md) (finding the evergreen plugin, Step 0 freshness, refresh, learnings, tests). Files: [SKILL.md](SKILL.md), [RESEARCH.md](RESEARCH.md), [CHANGELOG.md](CHANGELOG.md), [LEARNINGS.md](LEARNINGS.md), [TESTS.md](TESTS.md) with `evals/evals.json`, and `evergreen.json` (state).

Step 0, every use: read `evergreen.json`. If `contradiction` is set or today is on or past `next_due`, say so in one line, do the task, then refresh this unit with the plugin's `evergreen-refresh`. If `tests.failing` is non-empty, say so and run `evergreen-tune` after the task. Below the due date, spend nothing more.

Shortened 2026-11-20 to keep the installed size under the 800 KB limit; the full text was the hub's with this unit's name.
