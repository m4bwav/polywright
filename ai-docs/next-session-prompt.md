# Next session prompt

Paste this into a new session opened in the polywright repository.

---

Continue polywright (evergreen 3D modelling skills for AI agents). Read `AGENTS.md`, then `ai-docs/HANDOFF.md` and the newest entries of `ai-docs/log.md`. Work through the HANDOFF "Owed" list in order, skipping anything that needs the owner's decision (downloads of several GB, money, tagging or publishing a release) and asking about those instead.

For each change: research before recall (cite in the skill's RESEARCH.md), log the reason in the skill's CHANGELOG.md, run `python tests/check_skills.py`, `python tests/test_pw.py`, `python tests/test_recipes.py` and `python scripts/budget.py`, and work through a pull request that you merge yourself once CI is green. Trigger and action evals run headless with `claude -p` in a throwaway clone (see the log for how); record runs in each TESTS.md.

Before you finish, update HANDOFF.md and log.md, and rewrite this file for the session after yours, ending it with this same instruction to write the next prompt.
