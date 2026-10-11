# Decision: a hub skill, six siblings, one CLI and a folder contract

Date: 2026-10-11. Status: adopted for v0.1.0.

## Context

The owner makes 3D models with AI for games (Roblox, Unity, three.js), 3D printing, AI video and possibly business uses, and has separate plugins for those targets. Research (ai-docs/research) found two Blender MCP servers, ShapeWright, text-to-cad and a few small "meshwright" repos, but nothing that routes between finding, capturing, generating and coding a model, checks the result against a target, or records provenance and AI use for stores.

## Decision

- One hub skill (`polywright`) that every 3D request starts from: brief, route, the asset folder and `manifest.json`, the inspect-render-check loop.
- Six siblings by job, not by tool: references, capture, generate, blender, finish, print. Descriptions name the sibling that owns nearby requests.
- One stdlib CLI (`pw.py`) with a Blender half (`pw_bpy.py`) that returns one JSON object per command and a single contact sheet per render: the token saving the agent research pointed at.
- Other plugins call polywright through a folder (`brief.md`, `manifest.json`, `refs/`, `work/`, `out/`, `renders/`), never through internals.
- No new MCP server: headless scripts are the default; the existing Blender MCP servers are documented for live, watched sessions only.
- Budgets live in data (`targets.json`) with sources, so `pw.py check` and the skills agree.

## Rejected

- A single large skill: too much loaded per use, and descriptions could not name precise triggers.
- One skill per tool (a TRELLIS skill, a COLMAP skill): tools churn monthly; jobs do not.
- The name "meshwright": two GitHub projects already use it for 3D work.

## Consequences

- Sibling skills reference `../polywright/scripts/pw.py`: the seven install together.
- Public repository: private projects, machines and people are generalised; originals of the research notes are kept in the owner's private notes.
