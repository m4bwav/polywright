# Agent rules for polywright

Rules for any AI agent (Claude Code, Copilot, Cursor, Codex, Gemini CLI) working in this repository. `CLAUDE.md` imports this file and `.github/copilot-instructions.md` points here.

Read [README.md](README.md) first. The seven skills live under [skills/](skills/); the hub is `skills/polywright`, which also holds the CLI (`scripts/pw.py`, with its Blender half `scripts/pw_bpy.py`) and the target budgets (`references/targets.json`). Each skill is an evergreen unit with its companions beside it: RESEARCH, CHANGELOG, LEARNINGS, TESTS, `evals/evals.json`, MAINTENANCE and `evergreen.json`. The first research pass is in [ai-docs/research/](ai-docs/research/index.md).

## Rules

- Evergreen units in pointer mode: before editing a skill, read its `evergreen.json`. If `next_due` has passed or `contradiction` is set, say so and refresh after the task (the evergreen plugin's `evergreen-refresh`, otherwise the skill's `MAINTENANCE.md`). Every edit to a SKILL.md gets a CHANGELOG entry with its reason (`R-`, `L-` or `T-` ids, or "user request"). Re-run that skill's `evals/evals.json` (evergreen-test) when the change alters what the skill triggers on, decides or does.
- Research beats recall. Generator models, licences, Blender's Python API, engine limits and store policies move monthly. Never change a version, limit, operator name, licence or price from memory: cite the source in the skill's RESEARCH.md (an `R-` entry) and log the change in CHANGELOG.md.
- Blender API claims are checked against a running Blender, not docs alone: every block in `skills/polywright-blender/references/bpy-recipes.md` must pass `python tests/test_recipes.py`. Add a recipe only with a `# recipe:` line and a `[pw] ok` print.
- `pw.py` stays standard-library Python 3.9+, prints exactly one JSON object per command, fails soft (`ok: false` with `error`), and runs on Windows, macOS and Linux. `pw_bpy.py` runs inside Blender (or a Python with the bpy module) and may use numpy. Every new command or option gets a test in `tests/test_pw.py`.
- Budgets live in `skills/polywright/references/targets.json`; change a number only with a source, and keep the `advice` lines saying where it came from.
- Skills stay under 200 lines, with a description of at most 1,024 characters (Agent Skills spec; this repository's budget is 700) that says what the skill does and names the sibling that owns nearby requests.
- The skills install nothing on their own and spend nothing: Blender, ComfyUI, model weights, hosted generators, slicers and MCP servers are the user's to install, download or pay for, after being told what each is for.
- Never route anyone to export, cache or trace Google Photorealistic 3D Tiles, and never strip a found model's author or licence.
- Before committing, run from the repository root: `python tests/check_skills.py` (structure, companions, manifests, links, public-safety guards), `python tests/test_pw.py`, `python tests/test_recipes.py` (both skip the Blender parts when no Blender is found) and `python scripts/budget.py`. CI runs them on three operating systems.
- Size budget: `scripts/budget.py` sets green, yellow and red limits on what every session loads (descriptions) and on the installed size. Red fails CI. Say so when a change crosses yellow.
- This is a public repository. Nothing in it names a person other than the author credit, a private project, a machine, an absolute path on someone's machine, or a credential. A lesson learned on a particular machine or project is generalised here ("a Windows 11 PC", "a real park"); the specifics belong in the owner's private notes, never in a commit. `tests/check_skills.py` guards home-folder paths and the owner's own paths.
- Versions: when a packaged file changes, bump `.claude-plugin/plugin.json` and the root CHANGELOG.md, and tag `vX.Y.Z`. The release workflow checks the tag against the manifest, runs the checks, zips `skills/` and publishes a GitHub release.
- Work on `main` through pull requests; delete merged branches.
- No AI attribution anywhere: no Co-Authored-By trailers and no "generated with" lines in commits, pull requests or files.

## everlast (session knowledge, load on demand)

- `ai-docs/INDEX.md` lists what past sessions learned here. At the start of a task, scan it and open only the entries that match; read `ai-docs/HANDOFF.md` when continuing unfinished work.
- Before finishing a task that hit a dead end, verified a non-obvious command or made a design choice, record it in `ai-docs/` and rewrite `HANDOFF.md` when work is left unfinished. Say "nothing to record" when that is true.
- Anything naming a person, an internal host or name, a credential, or an opinion about people goes to the owner's private notes, never here.
- Link documents with relative markdown links. Every markdown folder has an index that links its files. No wikilinks in the repository.
