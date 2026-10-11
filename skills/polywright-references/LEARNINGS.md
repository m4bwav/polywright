# Learnings: polywright-references

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first. Trigger and Hypothesis are required.

## Active

### L-001 · 2026-10-11 · A no-shadow prompt still produced a cast shadow
- Trigger: Z-Image Turbo, 'no cast shadow' in the prompt, fountain reference 2026-10-11
- Hypothesis: Product-photo wording pulls in a ground shadow
- Rule: Keep background removal in the path (pw.py gen uses rembg when installed) and do not reject an otherwise good reference for a soft shadow
- Evidence: T-20261011-1, confirmed 2026-10-11
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-11
