# Changelog: polywright-references

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261017-3 · 2026-10-17 · Private names generalised
- because: user request (public repository: no private project names, no person's name but the author credit, no machine paths; AGENTS.md)
- files: LEARNINGS.md L-002; CHANGELOG.md C-20261012-1; TESTS.md
- A film's name, its prop file names and a machine path became generic; the lesson is unchanged.

### C-20261017-2 · 2026-10-17 · references/images-for-3d.md: what a picture must give the mesher
- because: user request (each plugin carries 3D modelling knowledge for its topic and points to polywright); R-20261017-1
- files: references/images-for-3d.md (new); SKILL.md Step 5 (pointer); references/reference-kit.md (link)
- What each generator does with a picture, a six-point check before the GPU run, fix-in-picture or fix-in-mesh, styles that mesh well, single image or multi-view, background removal.

### C-20261017-1 · 2026-10-17 · Description excludes flat graphic patterns
- because: T-20261017-1 (decoy-2 'seamless pattern for wrapping paper' fired the skill 1 of 3)
- files: SKILL.md frontmatter description
- Adds "Not for flat graphic patterns (wrapping paper, fabric, wallpaper prints)".

### C-20261016-1 · 2026-10-16 · Colour from the photo's pixels; back views copy front markings
- because: L-003
- files: SKILL.md Step 2
- Say a real object's colour as measured, not as a word; expect back views to copy a front marking.

### C-20261012-1 · 2026-10-12 · Step 2b: a designed prop's sheet comes from the model
- because: L-002 (five failed text rounds for a film's spear; six owner notes each a seconds-long re-render from the model)
- files: SKILL.md Step 2b; LEARNINGS.md
- Build the prop with bpy and render side and top on flat grey; raise the side view for paired parts.

### C-20261011-2 · 2026-10-11 · Description says when to fire
- because: T-20261011-2 first pass (undertriggering: prompts answered without the skill; hub and finish both claimed game-readiness)
- files: SKILL.md frontmatter description
- Descriptions open with 'Use whenever ...' and name the requests each skill owns; the hub only takes requests no sibling owns.

### C-20261011-1 · 2026-10-11 · Created as an evergreen unit
- because: user request (an evergreen 3D modelling plugin); research R-20261011-1 to R-20261011-2
- files: SKILL.md, references/, RESEARCH.md, LEARNINGS.md, TESTS.md, evals/evals.json, evergreen.json
- Initial version, tier `fast`, interval 14d, written from the five research notes of 2026-10-11 and the verified runs logged in LEARNINGS.md.
