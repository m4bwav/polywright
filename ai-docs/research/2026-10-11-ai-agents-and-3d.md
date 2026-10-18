# How AI agents do 3D modeling (state of play, 2026-10-11)

Research for polywright, a planned evergreen plugin for any task that needs a 3D model (games, 3D printing, AI video, business use).
Researched 2026-10-11 with web search, WebFetch, the GitHub API (`gh api`) and the Hacker News Algolia API.
Star counts and push dates come from `gh api` on 2026-10-11 unless a row says otherwise.
The session's shared web-search budget ran out near the end, so a few claims are marked unverified at the bottom.

Related: the owner's other plugins that polywright hands work to or takes it from: threewright (three.js), cinewright (film and AI video), roblox-agent and unity-agent (engines), and private printing, 3MF-settings and ComfyUI image skills.

## Bottom line

1. Do not build another Blender MCP. Two serious ones exist: the official Blender Lab server (GPL-3.0, v1.0.3 on 2026-09-11, scene analysis and docs search, no generation) and the community MCP for Blender by ahujasid (MIT, 30.5k stars, assets and generators). polywright should detect and use whichever is installed, and fall back to its own headless `blender --background` runner.
2. Make the headless Blender runner the core script. Agents waste most tokens on live screenshots and long sessions. A runner that executes a script on a `.blend` or mesh file and prints a short text report (counts, bounds in metres, non-manifold edges, materials, warnings) plus one contact sheet PNG is the biggest token saver.
3. Review renders as one contact sheet, not many screenshots. Normalise the viewport first (object mode, no selection, overlays off) and print camera pose and bounding boxes next to the image. 3DHarnessBench (arXiv 2609.06535, 2026-09-06) found pose metadata and normalised views helped most, and Opus 5 used 328k to 380k output tokens and about $8 to $11 per object with free tool access.
4. Pick the route before modeling: reuse an asset, write code, or generate. Order: search CC0 libraries (Poly Haven, Kenney, Quaternius, then Sketchfab, Objaverse with per-object licences), then code (bpy, build123d, OpenSCAD, a ShapeWright-style YAML), then a generator (TRELLIS.2 local, Meshy, Tripo, Rodin, Hunyuan3D), then cleanup. the owner's private printing skill skill already proved "find it first" beats modeling a car from scratch.
5. Use code for anything with dimensions or parts. Use generators for organic, one-off shapes. Practitioners on HN and in 2026 tests agree: LLMs are weak at spatial reasoning but good at parametric code they can compile, render and inspect. Precise parts belong in CAD (build123d or OpenSCAD), not Blender meshes.
6. Ground every bpy call in the installed Blender version. API mismatch is the top failure cause (3DCodeBench, arXiv 2606.01057). Feeding tracebacks back for up to two retries lifted executability from 0.70 to 0.97. Report the Blender version up front and look up the live API (introspection or the official server's docs search) before writing code.
7. Feeding runtime errors back fixes crashes but not shape. In 3DCodeBench, coding-agent harnesses raised executability by 22.6 points but shape metrics barely moved. Shape quality needs measured checks (bounds, part gaps, floating parts) and a visual critique against a reference.
8. Write checks into the asset, then run them. ShapeWright (billtruong003, Apache-2.0) is the best design reference found: YAML of named parts, parameters and design checks, 8 validation layers, deterministic CPU contact sheets, GLB export per engine with budget profiles. polywright should borrow the idea of named parts plus checks, and call ShapeWright as an optional backend instead of reimplementing it.
9. Keep plan, act and critique as separate roles with a human gate. LL3M (arXiv 2508.08228), the planner-actor-critic paper (arXiv 2601.05016), SceneCraft and BlenderAlchemy all report gains from a separate critic and an iterative render loop. BlenderGym found that with a big budget, spending more on verification than on generation pays off.
10. Save often and restart instead of running long sessions. The MindStudio donut test (2026-05-01) used 60% of a Max 5x session and the model lost track of the scene and declared success. Save a numbered `.blend` per milestone and resume from a written state summary.
11. Every output gets a manifest with provenance and licence. Fab, Unity Asset Store, Sketchfab, MakerWorld, Printables and Steam all require AI-use disclosure (Steam rules rewritten January 2026; MakerWorld needs a real print photo since February 2026). The manifest must record source, licence, author, generator and model version, and whether AI made a material part.
12. Treat Blender MCP servers as risky. Both servers run arbitrary Python with no real sandbox. The community server's maintainer account was reported hacked (HN, 2026-08-10). Pin versions, keep the socket on localhost, prefer headless runs on copies.
13. Offer a stable contract to other plugins: a brief JSON in, a fixed output folder out (`model.glb`, `model.stl` or `.step`, `sheet.png`, `report.json`, `manifest.json`). cinewright, unity-agent, roblox-agent, threewright and the private printing skill should call it through that contract only.
14. Leave whole areas to existing tools: CAD-to-manufacturing (text-to-cad skills: DfAM, DFM, G-code, Bambu send), mesh repair GUI (GeekatplayStudio Meshwright), generator APIs (Meshy MCP and skills), engine editing (Unity MCP, Unreal MCP, Roblox Studio MCP). polywright routes to them and checks their output.

## Existing agent tools for 3D

Stars and dates from `gh api` on 2026-10-11 unless noted. "Push" is the last push date.

| Name | URL | Kind | What it does | Licence | Activity |
|---|---|---|---|---|---|
| Blender Lab MCP server (official) | https://www.blender.org/lab/mcp-server/ | MCP + Blender add-on | 26 tools per a vendor count: run code, scene and object summaries, screenshots, renders, search of bundled bpy API and manual; `_for_cli` variants run background Blender to audit .blend files. No generation. Blender 5.1+ | GPL-3.0-or-later (per StraySpark; page does not state it) | v1.0.0 2026-04-27, v1.0.3 2026-09-11 |
| MCP for Blender (ahujasid, formerly blender-mcp) | https://github.com/ahujasid/mcp-for-blender | MCP + add-on | `execute_blender_code`, `look`, scene info, Poly Haven, Sketchfab, Poly Pizza, `generate_3d` via Rodin, Tripo, Hunyuan3D; `bpy_api_lookup` and `describe_node_type` added 2026-09-15 (vendor report); optional safe mode; telemetry on by default | MIT | 30,480 stars, push 2026-10-06; renamed 2026-09-16 |
| Blender MCP Pro (Youichi Uda) | (vendor site, not checked) | Paid MCP | 120+ tools in 17 categories | Commercial | Per StraySpark 2026-09 |
| StraySpark Blender MCP Server | https://www.strayspark.studio | Paid MCP | 556 tools, code execution off by default, path jails, audit log; also sells an Unreal MCP | Proprietary, source included | v4.0.1 per own blog |
| dcc-mcp (core, blender, maya, 3dsmax, agent-plugins) | https://github.com/dcc-mcp/dcc-mcp-core | MCP framework, 47 host adapters | One gateway and CLI for many DCC apps, typed tools, agent skills for Claude Code and Codex | MIT | core 53 stars, blender 45, maya 58; all pushed 2026-10-10/11 |
| cc-blender-skill (RobLe3) | https://github.com/RobLe3/cc-blender-skill | Claude Code skills (29) | Router skill `text-to-blender`, modeling, materials, lighting, export, reference reconstruction, `multiview-fit-loop`, `quality-refinement-autoloop`; needs blender-mcp on port 9876 | MIT | 88 stars, push 2026-05-01, v1.3.0 |
| ShapeWright (billtruong003) | https://github.com/billtruong003/ShapeWright | Python CLI + MCP (18 tools) + Claude skill | Game assets as YAML (named parts, params, checks); 8 validation layers; deterministic CPU contact sheets; GLB per engine with LODs, collision, budgets; no Blender or GPU | Apache-2.0 | 8 stars, created 2026-09-29, push 2026-10-06 |
| shapewright (anandasatriaadi) | https://github.com/anandasatriaadi/shapewright | MCP over build123d | ~45 tools, named stateful scene, selector strings for edges and faces, `render_views` PNG, `printability` (overhang, supports, bed fit, grams), `export_script` to runnable .py, undo | MIT | 0 stars, created 2026-10-11 |
| build123d-mcp | https://pypi.org/project/build123d-mcp/ | MCP over build123d | `execute` in a persistent session, `measure`, `clearance`, `find_holes`, `analyze_printability`, `render_view`, drawing lint | Not checked | PyPI 0.3.52 to 0.3.68 |
| text-to-cad (earthtojake) | https://github.com/earthtojake/text-to-cad | Agent skills + `cadgen` MCP + viewer | build123d/OCP CAD to STEP, STL, 3MF, GLB; step.parts search; drawings; DXF; URDF/SRDF/SDF; DfAM check; DFM; OrcaSlicer G-code; Bambu send; SendCutSend check | MIT | 19,233 stars, push 2026-10-11; HN front page 2026-05-01 (186 points) |
| Meshwright (seena18) | https://github.com/seena18/meshwright | LangGraph pipeline + MCP + CLI | Prompt to reference image to TRELLIS.2 GLB, with vision review at each step; Blender 4-view turntable plus mesh stats; async job tools | MIT | 0 stars, push 2026-09-30 |
| Meshwright (GeekatplayStudio) | https://github.com/GeekatplayStudio/Meshwright | Desktop app + MCP (14 tools) + Python API | 12 mesh checks, staged repair kept only if diagnostics improve, QuadriFlow retopo, decimation with measured deviation, UV and PBR, print check for 216 printers, ring sizing | MIT core (GitHub says NOASSERTION); optional GPL-3 deps | 54 stars, push 2026-09-26, v1.6.0 |
| Meshy MCP server + meshy-3d-agent skills | https://github.com/meshy-dev/meshy-mcp-server | Official vendor MCP + skills | Text, image, multi-image to 3D; remesh, retexture, rig, animate; send to slicer; credits | MIT | MCP 50 stars push 2026-10-11; skills 98 stars push 2026-09-23 |
| Tripo MCP (VAST-AI-Research) | https://github.com/VAST-AI-Research/tripo-mcp | Official vendor MCP, alpha | Text to 3D through the Tripo Blender add-on | MIT | 212 stars, push 2025-04-14 (stale) |
| Hunyuan3D, Rodin | (inside MCP for Blender) | Generator tools | No standalone official MCP found | Hunyuan3D 2.1: Tencent community licence, excludes EU, UK, South Korea | n/a |
| TRELLIS.2 (Microsoft) | https://github.com/microsoft/TRELLIS.2 | Open model | Image to 3D; native in ComfyUI (Comfy blog) | MIT | 11,849 stars, push 2026-07-10 |
| Roblox Cube | https://github.com/Roblox/cube | Open model + Studio Mesh API | Text to mesh, shape tokens | Custom (NOASSERTION) | 1,271 stars, push 2026-05-28 |
| freecad-mcp (neka-nat) | https://github.com/neka-nat/freecad-mcp | MCP | Drive FreeCAD | MIT | 2,806 stars, push 2026-10-07 |
| OpenSCAD MCPs | https://github.com/RobertCoop/openscad-mcp | MCP | Render .scad to PNG, validate, export STL/3MF | MIT | 150 stars, push 2026-09-10 (others: jkoets, fboldo, dkpoulsen, loom) |
| OpenSCAD skills | mitsuhiko/agent-stuff, iancanderson/openscad-agent, andreahaku/openscad_claude_skill, FradSer/dotclaude | Claude skills | Multi-angle previews, param extraction, STL export, versioned iterations, printability | Apache-2.0 / none / none / MIT | 3,182 / 130 / 22 / 593 stars; pushes 2026-02 to 2026-10 |
| cad-skill (flowful-ai) | https://github.com/flowful-ai/cad-skill | Claude skill | CadQuery script, STL, preview renders for printing | NOASSERTION | 661 stars, push 2026-07-14 |
| Autodesk Fusion connector | Autodesk marketplace | Official MCP | Text to CAD in a live Fusion session (Claude connector, 2026-04-28) | Commercial | Launched 2026-04-28 |
| Autodesk Product Help MCP | cgpress.org report | Official MCP | Read-only help for 100+ Autodesk products | Commercial | April 2026 |
| 3dsmax-mcp (cl0nazepamm) | https://github.com/cl0nazepamm/3dsmax-mcp | MCP | 160 tools, MAXScript docs skill bundled | MIT | 303 stars, push 2026-10-01 |
| Maya MCPs | PatrickPalmer/MayaMCP, chadrik/maya-mcp-server, dcc-mcp-maya | MCP | Run Python, inspect, viewport capture | MIT | 107 (stale 2025-05) / 42 / 58 stars |
| Houdini MCPs | https://github.com/capoomgit/houdini-mcp | MCP | Nodes, params, Python via a plugin on port 9876 | MIT | 305 stars, push 2026-06-11; SideFX showed official MCP for APEX rigging at SIGGRAPH 2026 (preview) |
| Cinema 4D 2026.4 built-in MCP | digitalproduction.com 2026-10-01 | Official MCP | Off by default; auth, tool permissions, undo integration, audit log | Commercial | Released 2026-09-30 |
| Rhino / Grasshopper MCPs | reer-ide/rhino_mcp, alfredatnycu/grasshopper-mcp, dongwoosuk/rhino-grasshopper-mcp | MCP | Run Python in Rhino, place GH components | MIT | 29 / 99 / 17 stars; small |
| Unity MCP (official) | com.unity.ai.assistant | Official MCP | Editor control; a third-party blog says it is deprecated in favour of the Unity CLI (unverified) | Commercial | 2.x in 2026 |
| unity-mcp (CoplayDev), Unity-MCP (IvanMurzak) | github.com/CoplayDev/unity-mcp | Community MCP | Editor control, no mesh generation | MIT / Apache-2.0 | 14,843 / 4,418 stars, pushed 2026-10 |
| Unreal MCP (Epic, UE 5.8) | fortnite.com news 2026-08-20 | Official plugin | Toolsets for Verse, devices, UI, play; no modeling tools documented | Commercial | Shipped with UE 5.8; in UEFN 2026-08-20 |
| Unreal_mcp (ChiR24) | https://github.com/ChiR24/Unreal_mcp | MCP | `manage_geometry` via Geometry Script: primitives, booleans, extrude, Nanite | MIT | 916 stars, push 2026-10-10 |
| Sketchfab and Poly Haven MCPs | gregkop/sketchfab-mcp-server, RN0000/polyhaven-mcp | MCP | Search and download | various | Small; built into MCP for Blender anyway |
| CADAM (Adam, YC W25) | https://github.com/Adam-CAD/CADAM | Open-source AI CAD app | Text to parametric CAD, Onshape and Fusion plugins | Not checked | Launch HN 2026-06-17 (215 points) |

Gaps across the field, as of 2026-10-11:

- Nobody routes between reuse, code and generation. Each tool assumes one route.
- Few tools emit a provenance and licence manifest. None found writes the AI-disclosure fields that stores ask for.
- Target profiles are scattered. ShapeWright has game budgets, text-to-cad has print and CNC, the private printing skill has the P1S. No one tool covers game, print, video and business.
- Most Blender tools assume a live GUI session. Headless, file-in file-out runs are rare outside the official server's `_for_cli` tools and the owner's own scripts.

## 1. Existing skills, plugins and MCP servers

### Blender

**Official Blender Lab MCP server.**
Blender Lab publishes it at https://www.blender.org/lab/mcp-server/ (source at projects.blender.org/lab/blender_mcp, which returned 403 to WebFetch).
The page says Blender "does not have any built-in functionality for connecting to LLMs" and needs the add-on (v1.0.3), an MCP client and the server.
It warns that it runs LLM code "without any guards" and suggests a virtual machine.
Demonstrated uses are scene analysis, renaming, data relations, finding the highest-poly object, and documenting geometry nodes.
A vendor blog (StraySpark, 2026-09) lists the release history: v0.1.0 2026-03-24, .mcpb bundle 2026-04-10, v1.0.0 2026-04-27, v1.0.2 2026-09-08 (pins MCP SDK below 2), v1.0.3 2026-09-11.
The same blog counts 26 tools, including two that search bundled copies of the bpy API reference and the manual, and six `_for_cli` variants that audit .blend files in a background Blender.
Requires Blender 5.1 or newer.
Anthropic shipped it as the Claude Blender connector on 2026-04-28 (develop3d, redsharknews, nofilmschool).
Lifehacker Japan (updated 2026-08-13) used it with Claude Desktop to design printable parts: the docs lookup made outdated property names rare, setting units first made the first print fit, but wall thickness needed several rounds and snap fits near 0.1 mm belong in FreeCAD or Fusion.

**MCP for Blender (ahujasid).**
Formerly blender-mcp. Renamed on 2026-09-16 to avoid confusion with the official server; `uvx blender-mcp` still works (README, fetched 2026-10-11).
30,480 stars, MIT, pushed 2026-10-06.
Tools: `execute_blender_code`, `look` (viewport, camera, angles, frames, renders), `get_scene_info`, Poly Haven (CC0, no key), Sketchfab (key), Poly Pizza (key, about 69% CC-BY), `generate_3d` with Rodin, Tripo, Hunyuan3D.
Known issues from the README: no socket authentication, one server instance only, Poly Haven downloads freeze Blender's main thread, timeouts on complex requests ("break into smaller steps"), Hunyuan3D region mismatches, telemetry on by default with an opt-in that may train AI models.
StraySpark reports 36 tools, a paid Premium plan ($10 or $20 a month), and four 2026 CVEs. I could not verify the CVEs.
HN item 49238028 (2026-08-10) reports the maintainer's GitHub account was hacked.

**cc-blender-skill (RobLe3).**
A pure-skill plugin of 29 Claude Code skills, v1.3.0, tested on Blender 5.1.1, needs blender-mcp on port 9876.
Good ideas worth copying: one entry router skill, a harmoniser skill for precedence, each skill under 500 lines, objects named with prefixes (`GEO-`, `MAT-`, `LGT-`) because each call starts a fresh namespace, manifests and IoU/SSIM gates before export, failure renders published next to successes, a cheap model runs tests and a strong model patches.
Gap: tied to one MCP server and to a live GUI.

**Other Blender skills seen in catalogs.** skills.sh "Blender 3D" (Smithery), claudemarketplaces listings for a Blender export skill and a Blender web pipeline (glTF, decimation, LOD) in freshtechbro/claudedesignskills (1,030 stars, push 2025-11-20).

### Code CAD and 3D printing

**text-to-cad (earthtojake).** 19,233 stars, MIT, pushed 2026-10-11. Skills: CAD (build123d on OCP, STEP first, STL, 3MF, GLB), step.parts, engineering drawing, DXF, URDF, SRDF, SDF, SendCutSend, DfAM check, DFM, G-code via OrcaSlicer, Bambu Labs send. Ships a `cadgen` MCP and a browser viewer that shows cards in Claude Code. Telemetry on by default. Windows Smart App Control can block the unsigned OCP module (same issue the owner hit with his runner). The DfAM skill measures wall thickness, overhangs, supports and orientation from a local script and never slices or uploads by itself.
HN thread 47970497 (2026-05-01, 186 points): commenters say LLMs remain "very weak at spatial reasoning", and that text-to-CAD suits hobby users more than professional engineers.

**shapewright (two projects).** The build123d MCP by anandasatriaadi (created 2026-10-11) answers the main pains of raw build123d for agents: a huge API (about 45 focused tools), edge and face selection (a selector string language), no picture (`render_views`), no print check (`printability`), and no way back to code (`export_script`). The other, ShapeWright by billtruong003, is a game-asset tool covered below.

**build123d-mcp** on PyPI (0.3.52 to 0.3.68) has `execute`, `measure`, `clearance`, `find_holes`, `analyze_printability`, `render_view`, drawing lint.

**OpenSCAD.** Several MCPs render .scad to PNG for the agent to look at (RobertCoop/openscad-mcp 150 stars, loom, jkoets, fboldo, dkpoulsen). Skills: mitsuhiko/agent-stuff openscad (Apache-2.0, a Tessl review flagged broken script references), iancanderson/openscad-agent (versioned .scad files and visual comparison), andreahaku/openscad_claude_skill (STL to parametric .scad, snap-fit and heat-set boss library), FradSer use-openscad.
HN 49405520 (2026-08-23): "I've had great success with asking claude to use openscad for part design", and "It can write code, compile it, render and inspect it."

**FreeCAD.** neka-nat/freecad-mcp (2,806 stars, MIT, pushed 2026-10-07) is the main one. CAD-Assistant (ICCV 2025) used a FreeCAD Python interpreter.

**The owner's own printing skill.** the private printing skill already does find-then-convert for print, with headless Blender scripts and `verify_stl.py`. polywright's print target should delegate to it.

### Generative 3D services

**Meshy.** Official MCP `@meshy-ai/meshy-mcp-server` (MIT, pushed 2026-10-11) and a skills pack `meshy-3d-agent` (`npx skills add meshy-dev/meshy-3d-agent`) that calls REST directly without MCP. Tools cover text, image and multi-image to 3D, remesh, retexture, rig, animate, send to slicer, and credits. The printability tool "currently returns a manual print-readiness checklist". Meshy docs note `meshy-5` retired 2026-10-10 and `lowpoly` retires 2026-10-30. Meshy also runs a "3D Agent" beta in its web app.
**Tripo.** Official MCP is alpha and Blender-only, last pushed 2025-04-14.
**Rodin and Hunyuan3D.** Reached through MCP for Blender. Hunyuan3D 2.1 uses the Tencent Hunyuan 3D Community License, which does not apply in the EU, UK or South Korea and needs a separate licence above 1M MAU.
**TRELLIS.2.** MIT, 11,849 stars. Native in ComfyUI, which removed NVIDIA non-commercial dependencies from the original pipeline (Comfy blog). the owner's private ComfyUI skill hosts can run it.
**Meshwright (seena18).** A LangGraph pipeline wrapped around TRELLIS.2: reference image, background removal, image review, 1024 preview, model review, 1536 final, final review, GLB. Blender records mesh stats and rejects empty or zero-thickness geometry before any vision call, then renders four views for a vision model. Review JSON has `accepted`, `score`, `findings`, `topology_ok`, `all_views_ok`. This stats-before-vision gate is a cheap pattern to copy.

### Mesh repair and preparation

**Meshwright (GeekatplayStudio).** 12 checks, six-stage repair where each stage is kept only if diagnostics improve, QuadriFlow retopology, decimation with measured deviation, UV with xatlas, a 216-printer detail check, Blender for .blend files. Has an MCP with 14 tools and a `MeshService` Python API. MIT core with optional GPL-3 PyMeshLab and pymeshfix. Good candidate to call for heavy repair rather than re-coding it.

**ShapeWright (billtruong003).** Its README states plainly where it is strong (low-poly props, modular kits, re-texturing, stylised creatures) and weak (human characters, sculpted detail). It says "Use Blender for sculpting, hand-made topology and hero renders." An asset is YAML with named parts, params and `checks:`; "The backrest is too narrow" maps to one parameter. The review sheet has orthographic views with scale bars, part colours, texel density and UVs. A fresh agent built a mailbox in 12 tool calls from `llms.txt` alone. Export targets Godot, Unity, Unreal with collision proxies, LODs and 8 budget profiles.

### Other DCC apps and engines

- Autodesk: official Fusion MCP (text to CAD in a live session, Claude connector 2026-04-28) and a read-only Product Help MCP (April 2026). Maya and 3ds Max servers are community projects; cl0nazepamm/3dsmax-mcp (160 tools, bundled MAXScript docs skill) is the most active.
- dcc-mcp: one MIT runtime and gateway with 47 host adapters (Blender, Maya, 3ds Max and others) and official agent plugins for Claude Code and Codex. Young (core 53 stars) but very active. Worth watching as a possible single DCC bridge.
- Houdini: community capoomgit/houdini-mcp (305 stars). SideFX showed an official MCP for APEX rigging scripts at SIGGRAPH 2026 as a SideFX Labs preview (Jon Peddie Research).
- Cinema 4D 2026.4 (released 2026-09-30) has a built-in MCP server, off by default, with authentication, tool permissions, undo and audit logging. This is the safest design seen in a vendor server.
- Rhino and Grasshopper: several small MIT servers, none dominant.
- Unity: official MCP inside `com.unity.ai.assistant` (Unity 6+), plus CoplayDev/unity-mcp (14,843 stars). the owner's unity-agent covers this. No mesh-generation tool found in the official MCP.
- Unreal: Epic's Unreal MCP plugin ships with UE 5.8 and reached UEFN on 2026-08-20; no modeling toolset documented. ChiR24/Unreal_mcp exposes Geometry Script primitives and booleans.
- Roblox: Cube 3D open model and a Mesh Generation API in Studio. the owner's roblox-agent covers Studio.

## 2. How the strongest agent workflows are structured

### The loop that works

Across papers, tools and write-ups the same loop recurs:

1. **Brief.** Pin the target, real dimensions, units, budget and style before any modeling. Lifehacker Japan's print project worked because units were set first. ShapeWright starts with `sw brief`, which picks the closest example and rules.
2. **Route.** Reuse, code or generate (see the decision table below).
3. **Blockout.** Named parts with parameters, primitives only. cc-blender-skill names objects with stable prefixes; ShapeWright and SceneCraft use named parts and a scene graph of relations.
4. **Measure.** Text checks before pictures: bounds in metres, part gaps, floating parts, non-manifold edges, triangle budget. Meshwright (seena18) rejects empty geometry without any vision call.
5. **Look.** One normalised contact sheet with orthographic and 3/4 views, scale bars and camera pose. 3DHarnessBench found pose metadata gave the largest multi-view gain; grid overlays helped less.
6. **Critique.** A separate critic compares the sheet against the brief and a reference, and maps each finding to a parameter. LL3M, the planner-actor-critic paper and BlenderAlchemy all use a separate critic.
7. **Refine.** Change parameters, not vertices. Rerun measure and look.
8. **Target pass.** Game (LOD, collision, pivots, budget), print (watertight, wall thickness, flat base, bed fit), video (scale, materials, turntable), business (clean presentation render).
9. **Hand over.** Files plus a manifest. A human judges before anything ships.

### Search, code or generate

| Need | First choice | Why |
|---|---|---|
| Common prop, nature, HDRI, texture | Poly Haven, Kenney, Quaternius (CC0) | Free, no attribution, often better than generated |
| Specific real object (car model, landmark) | Print sites, Sketchfab, then generator | the private printing skill: a free Sketchfab Pacifica beat scratch modeling |
| Part with dimensions or fits | build123d or OpenSCAD | Manifold by construction; parametric edits; STEP export |
| Game prop set, modular kit | Code (ShapeWright YAML or bpy from params) | Consistent style, budgets, rebuild on change |
| Organic hero shape, creature, statue | Generator (TRELLIS.2, Meshy, Tripo, Rodin) then cleanup | LLMs fail at organic shapes (MindStudio 2026-05-06) |
| Human character for animation | Base mesh or DCC by a person | ShapeWright and practitioners both say generators and SDFs lack edge loops |
| Scene layout | Code placing assets by relations | SceneCraft scene graph; LLMs place approximately, so verify with measurements |
| Material | Poly Haven texture, else procedural node code | VLMaterial shows image-to-procedural material programs work |

### Reported failure modes and fixes

| Failure | Evidence | Fix |
|---|---|---|
| Hallucinated or outdated bpy API | 3DCodeBench: API mismatch dominates failures; StraySpark 2026-09-14 lists `scene.node_tree` removed in 5.0, layered Actions, Grease Pencil v3, `BLENDER_EEVEE_NEXT` renamed back, lower-case enums like `cycles` | Report Blender version first; introspect live RNA and enums; search a version-matched API index; let errors list valid values; retry with traceback up to 2 times |
| Script runs but shape is wrong | 3DCodeBench: disconnected fragments (Gemini 3.1 Pro), simplistic floating primitives (Claude Opus 4.7); harness retries left shape metrics flat | Measure gaps and floating parts; check against reference with a critic; named parts with attachment relations |
| Wrong scale | Donut test: oversized sprinkles, cup clipping into donut | Set units first; print bounds in metres every step; include a 1.75 m or 100 mm scale reference in sheets |
| Silent no-op operators (boolean on empty selection) | StraySpark 2026-09-14 | Report before and after counts for every operator |
| Broken booleans, non-manifold meshes | Practitioner posts; Meshwright repair stages | Prefer code CAD for solids; run manifold check; voxel remesh or Manifold3D as fallback |
| Ugly topology, no edge loops | MindStudio 2026-05-06: Claude "doesn't reason about edge loops"; generator meshes 500K+ triangles | Do not promise animation-ready topology from LLM or generator; QuadriFlow or vendor remesh; human retopo for characters |
| Unrequested changes | Donut test: cup redesigned, scene moved to a desert | Lock finished parts; diff the scene report between steps |
| Long sessions degrade | Donut test used 60% of a Max 5x session, ended with a magenta wash and a false "done" | Save numbered files per milestone; restart with a written state summary |
| Screenshots cost tokens and mislead | Donut test misread the reference as its own render; 3DHarnessBench agents used 18 to 156 MCP calls per object | Text reports first; one contact sheet; label which image is the reference |
| Blender crash loses work | Tom Crawshaw post; README warnings | Work on a copy; headless runs on files; save before every script |
| Node graphs beyond a few nodes break | MindStudio 2026-05-06 | Build node trees from small tested helper functions |

Token note: per Anthropic's vision docs, an image costs about width times height divided by 750 tokens, so a 1092 by 1092 sheet is about 1,600 tokens. Ten separate viewport grabs cost ten times that and give less. A single sheet plus a text report is the cheap path.

## 3. Research systems

| System | arXiv | Venue / date | What it found |
|---|---|---|---|
| 3D-GPT | 2310.12945 | 3DV 2024 (v2 May 2024) | Three agents (dispatch, conceptualise, model) turn text into parameters for procedural generators (Infinigen). Procedural parameters beat raw geometry for LLMs. |
| SceneCraft | 2403.01248 | ICML 2024 | Scene graph as blueprint, then Python constraints for layout; a vision model critiques renders; a library of learned reusable functions. Beat prior LLM agents on constraint adherence. |
| BlenderAlchemy | 2404.17672 | ECCV 2024 (v3 2024-08-02) | Vision-language edit generator plus state evaluator search Blender edit sequences for materials, geometry and lighting. Generating a reference image first helps the VLM read vague text. |
| BlenderLLM | 2412.14203 | 2024-12-16 | Fine-tuned Qwen2.5-Coder-7B with self-improvement on BlendNet; CADBench. Off-the-shelf models struggled with CAD scripts. |
| CAD-Assistant | 2412.13810 | ICCV 2025 | Training-free GPT-4o agent planning actions in a FreeCAD Python interpreter with CAD tools. |
| CADCodeVerify | 2410.05340 | ICLR 2025 | VLM asks and answers yes/no questions about its own render, then fixes the CAD code; CADPrompt benchmark of 200 objects; 7.30% lower point-cloud distance for GPT-4. |
| VLMaterial | 2501.18623 | ICLR 2025 | Fine-tuned VLM turns one image into a Blender procedural material program; 550K image-program pairs released. |
| BlenderGym | 2504.01786 | CVPR 2025 | 245 scene pairs in 5 tasks. Humans beat all 13 VLMs. Scaling the verifier helps; with under 30 queries spend more on generation, with over 100 spend more on verification. Scripts over 80 lines drift from the intended edit. |
| IR3D-Bench | 2506.23329 | 2025-06 | VLM agents recreate a scene from an image with code and rendering tools. |
| LL3M | 2508.08228 | v1 2025-08-11 (code at threedle/ll3m, 554 stars) | Multi-agent plan, retrieve, write, debug, refine Blender code; shared code context; BlenderRAG from API docs; self-critique on code and renders; user refinements. |
| MeshCoder | 2508.14879 | NeurIPS 2025 | Point cloud to structured Blender Python with semantic parts; code makes shapes editable; data and code CC-BY-NC-SA. |
| ShapeCraft | 2510.17603 | 2025-10 | LLM agents for structured, textured, interactive 3D modeling (abstract only seen). |
| Planner-Actor-Critic | 2601.05016 | 2026-01-08 | Planner, actor and critic over Blender MCP with a human advisor beat single-prompt modeling (no numbers on the abstract page). |
| EZBlender | 2601.07143 | 2026-01-12 | Plan-and-ReAct: plan globally, act locally; keeps quality while cutting latency and cost. |
| 3DCodeBench | 2606.01057 | 2026-06-01 (gaoypeng/3dcodebench, Apache-2.0) | 12 VLMs writing Blender 5.0 code. Elo leaders: GPT-5.5 1163, Gemini 3.1 Pro 1147, Gemini 3.5 Flash 1119; Claude Sonnet 4.6 1015, Opus 4.7 1006. Single-turn executability best for Opus 4.7 (0.910). Two traceback retries: 0.702 to 0.974. Shape quality barely moved in coding harnesses. |
| SceneActBench | 2607.22393 | 2026-07 | Agents act on 3D scenes through headless Blender over MCP (abstract only seen). |
| 3DHarnessBench | 2609.06535 | 2026-09-06 | Four harnesses from single view to full 3D interaction via Blender MCP. Every model did best with full interaction; Opus 5 led (Uni3D 0.927). Cost about $6.50 to $10.74 per object for Fable 5 and Opus 5. Pose metadata, normalised viewports and explicit measurements helped. |

What the research agrees on:

- Code is the right representation for agents. It is editable, inspectable and versionable (LL3M, MeshCoder, 3D-GPT, ShapeWright).
- Retrieval of API docs and examples improves correctness (LL3M BlenderRAG; the official server's docs search).
- Runtime-error feedback fixes execution quickly. Visual feedback is weaker and model-dependent (3DCodeBench, 3DHarnessBench, BlenderGym).
- A separate verifier or critic adds value, and its budget should grow with the total budget (BlenderGym).
- Richer, measured access to the 3D state beats more pictures (3DHarnessBench full interaction beat active screenshots).

## 4. Practitioner reaction

Reddit direct access was blocked: the RSS endpoints returned HTTP 429 to every request this session (other agents were polling at the same time), so Reddit views below come from search snippets and secondary write-ups.

**Real wins reported.**
- Batch chores in Blender: renaming, outliner cleanup, exports, scene audits, finding the highest-poly object (MindStudio 2026-05-06; Blender Lab page).
- Hard-surface and architectural blockouts and reference geometry.
- Simple printable parts with real dimensions (Lifehacker Japan 2026-08; HN 49405520 on OpenSCAD).
- A Medium writer put it as "Claude doesn't make the art. Claude operates Blender."
- Generators give base meshes fast; the common pattern is concept art to generator to Blender refinement (multiple 2026 reviews).

**Rejected or weak uses.**
- Organic shapes, animation curves, Geometry Nodes beyond a few nodes, anything needing visual judgment (MindStudio 2026-05-06).
- Game-ready topology and UVs. A r/ClaudeAI thread summary says AI is "weak on game-ready assets like low-poly topology and UVs". Generator meshes need cleanup; vendor auto-retopo claims are contested (stacksheriff, fish.audio, levelup reviews).
- Professional CAD. HN 47970497: text-to-CAD fits hobby users; professionals need functional, manufactured proof. Launch HN Adam (48572553): "Any time I see these 'AI CAD' solutions it's always toys."
- The donut test: "better than nothing" but "worse than what a Blender beginner with a few hours of practice could produce".

**Ethics and community politics.**
- Anthropic became a Blender Development Fund corporate patron (EUR 240,000 a year) with the connector launch on 2026-04-28. After backlash the Foundation turned it into a one-off donation on 2026-05-01 and said "no generative AI functionality is currently available or planned to be integrated in Blender" (CG Channel 2026-05-04; BlenderNation 2026-05-01).
- BlenderArtists thread (2026-04-28): a staff member cancelled his fund donation on principle; others called genAI "fundamentally unethical"; one wanted training-data consent and payment; a moderator said the site's policy (human-majority work allowed) "is not changing".
- polywright should therefore keep generative output clearly labelled, prefer CC0 libraries and code, and never post AI output to community spaces as human work.

**Store and platform rules (AI disclosure).**

| Platform | Rule | Source and date |
|---|---|---|
| Fab (Epic) | Tag "CreatedWithAI" when a material portion is made by genAI; upscaling and content-aware fill exempt; seller liable | Unreal forums quoting Epic policy; 80.lv |
| Sketchfab | Creators tag AI models "CreatedWithAI"; AI Generated / Human Created filter; "NoAI" tag; ToS bars scanning models for AI training | help.sketchfab.com; Fabbaloo |
| Unity Asset Store | AI content allowed if it does not resemble third-party work and has value; must disclose in listing, AI code included; AI Disclosure field; no filter | Unity support article; forum |
| Steam | Rules rewritten January 2026: AI dev tools exempt; disclose AI in shipped content, store and marketing, and live generation | VGC, Gigazine 2026-01-20 |
| MakerWorld (Bambu) | Tag AIGC; AI images not allowed as model photos; since February 2026 at least one real photo of the printed object | Bambu wiki; Fabbaloo 2026-02-10 |
| Printables | Requires AI-generated models to be tagged (details not verified) | All3DP summary |
| Roblox | Generated content goes through normal moderation; creator is responsible; no Creator Store AI rule found | create.roblox.com AI docs |

**Licensing of sources.**
- Poly Haven, Kenney, Quaternius: CC0 (secondary guides; verify on each site).
- Poly Pizza: about 69% CC-BY (MCP for Blender README).
- Objaverse-XL: ODC-By for the dataset, per-object licences in metadata.
- Infinigen: BSD-3-Clause (GitHub API).
- TRELLIS.2: MIT. Hunyuan3D 2.1: regional exclusions and an MAU cap. MeshCoder data: CC-BY-NC-SA.
- Google 3D Tiles may be viewed, not exported (the private printing skill notes).

## 5. Design recommendations for polywright

### Principles

- Route first. The router decides reuse, code or generate, and which backend, from the brief and the target.
- Text before pixels. Every step returns a short text report; images are one contact sheet per review round.
- Parameters over vertices. Every modeled asset keeps a source file (Python, .scad, YAML) that rebuilds it.
- Headless by default. Live GUI MCPs are optional accelerators, not requirements.
- Delegate. Call the private printing skill, text-to-cad skills, Meshy MCP, ShapeWright, GeekatplayStudio Meshwright, unity-agent, roblox-agent, threewright and cinewright when present. polywright owns routing, the contract, checks and the manifest.
- Provenance always. No file leaves without a manifest.

### Suggested skills

| Skill | Job | Calls out to |
|---|---|---|
| `polywright` (router) | Reads the brief, picks route and target, plans steps, owns the contract; the only skill other plugins invoke | All below |
| `polywright-find` (references and assets) | Search CC0 and licensed libraries, record licence and author, fetch reference photos and real dimensions | Poly Haven API, Kenney, Quaternius, Sketchfab, Objaverse, print sites |
| `polywright-generate` | Image or text to mesh via local or hosted generators; makes the reference image first | the private ComfyUI skill (TRELLIS.2, Hunyuan3D on the PC or Mac), Meshy MCP or skills, Tripo, Rodin |
| `polywright-code` | Parametric modeling: bpy builders, build123d or OpenSCAD for solids, ShapeWright YAML for game kits | headless Blender runner, build123d, OpenSCAD, ShapeWright |
| `polywright-blender` | Blender work on files or a live session: version check, API lookup, scene report, materials, lighting, renders | runner script; official Blender MCP or MCP for Blender if installed |
| `polywright-cleanup` | Measure and repair: manifold, scale, origin, decimate, remesh, UV, bake | runner, trimesh, Manifold3D, QuadriFlow, GeekatplayStudio Meshwright |
| `polywright-targets` | Target profiles and gates: game (budgets, LOD, collision, engine export), print (hand to the private printing skill and the private 3MF-settings skill), video (turntable, scale, GLB for cinewright), business (product renders, web GLB for threewright) | unity-agent, roblox-agent, the private printing skill, cinewright, threewright |
| `polywright-review` | Contact sheet plus critic: compares against brief and reference, maps findings to parameters, enforces round limits | runner sheets; a second model as critic |
| `polywright-curate` | Keeps the knowledge base fresh (API breaks per Blender version, store rules, generator models and licences) | evergreen refresh |

A smaller first release could merge `generate` into `find` (both "get a mesh from outside") and fold `review` into the router. Keep the router plus code, blender, cleanup and targets as the minimum.

### Scripts with the biggest token savings

1. **`pw_blender.py run`**: headless Blender runner. Input: a file and a script or a named recipe. Output: a text report (Blender version, objects, triangle counts, bounds in metres, materials, non-manifold count, loose parts, warnings, operator before and after counts) and an exit code. Never returns raw bpy dumps.
2. **`pw_sheet`**: contact sheet renderer. Normalised views (front, side, top, 3/4, plus wireframe or part colours), scale bar, camera pose printed on the sheet, optional reference image in a labelled slot. One PNG at about 1,100 px square.
3. **`pw_check`**: mesh and scene gates per target profile. JSON result with pass or fail per rule and a hint. Uses trimesh and Manifold3D outside Blender so it runs without Blender too.
4. **`pw_api`**: version-matched bpy lookup. Builds an index of RNA types, operators and enum values from the installed Blender once (`bpy.types` introspection) and answers queries in a few lines. Cheaper than pasting docs and not dependent on an MCP.
5. **`pw_fetch`**: asset search and download with licence capture (Poly Haven API, Kenney packs, Sketchfab with key), writing the manifest entry as it downloads.
6. **`pw_export`**: per-target export (GLB with named nodes, STL or 3MF, STEP for CAD, USDZ for business), plus a Khronos glTF validator pass when available.
7. **`pw_manifest`**: write and validate `manifest.json`.

### Contract for other plugins

Input: `brief.json` (or the same fields in the prompt).

```json
{
  "what": "chunky wooden barrel",
  "target": "game",
  "engine": "unity",
  "units": "m",
  "size": {"height": 0.9},
  "budget": {"triangles": 800, "texture_px": 512},
  "style": "stylised low-poly",
  "references": ["refs/barrel_photo.jpg"],
  "route": "auto",
  "licence_needed": "commercial",
  "ai_generation_allowed": true,
  "out": "D:/<project>/assets/barrel"
}
```

Output folder:

```
<out>/
  model.glb            game, video, web, business
  model.stl | .3mf     print target
  model.step           CAD route only
  source/              rebuild source: build.py, part.scad, asset.yaml, .blend
  textures/
  sheet.png            latest contact sheet
  history/             numbered sheets and reports per round
  report.json          last check results per gate
  manifest.json
```

`manifest.json` fields:

```json
{
  "polywright_version": "0.1.0",
  "created": "2026-10-11T18:00:00Z",
  "brief": "brief.json",
  "route": "code",
  "backend": "build123d 0.11 / blender 5.2",
  "target_profile": "game.unity.mobile",
  "units": "m",
  "bounds": [0.62, 0.9, 0.62],
  "triangles": 742,
  "checks_passed": true,
  "sources": [
    {"kind": "asset", "url": "https://polyhaven.com/a/...", "author": "...", "licence": "CC0-1.0", "used_for": "wood texture"}
  ],
  "ai": {
    "generated_geometry": false,
    "generated_textures": false,
    "generator": null,
    "model_version": null,
    "disclosure": "AI-assisted modeling via code; no generative geometry"
  },
  "attribution_text": "",
  "human_review": "pending"
}
```

Rules for callers: pass a brief, read `report.json` and `manifest.json`, never reach into `source/` except to rebuild. polywright never publishes, uploads or prints without the user's go-ahead.

### What to leave to existing tools

- Generator APIs and their auth: Meshy MCP and skills, Tripo, Rodin; local models through the private ComfyUI skill.
- Live Blender bridges: official Blender Lab server, MCP for Blender. Detect and use, never fork.
- Manufacturing chain: text-to-cad skills (DfAM, DFM, G-code, Bambu send) and the owner's private printing and 3MF-settings skills.
- Heavy mesh repair and retopology GUI: GeekatplayStudio Meshwright.
- Game-kit authoring at scale: ShapeWright as an optional backend.
- Engine placement and testing: unity-agent, roblox-agent, Unreal MCPs.
- Web viewing: threewright. Film use: cinewright.

### Evals to write early

- Route choice: ten briefs where the right answer is reuse, code or generate.
- Barrel under 800 triangles for Unity: checks pass, manifest complete, under a token cap.
- Printable bracket with two M3 holes 30 mm apart: STEP and STL, hole spacing measured within 0.1 mm.
- Blender 5.x API trap: a task that needs `scene.compositing_node_group`; pass only if no AttributeError reaches the user.
- Licence trap: a CC-BY asset must produce attribution text in the manifest.

## Open questions / unverified

- Official Blender MCP licence (GPL-3.0-or-later) and the 26-tool count come from StraySpark, a competing vendor. projects.blender.org returned 403. Verify on the repository.
- StraySpark's claim of four 2026 CVEs against MCP for Blender (including "CVE-2026-66004") is unverified. The web-search budget ran out before I could check.
- The HN report of the MCP for Blender maintainer's account hack (2026-08-10) had no detail; I did not check what was pushed or whether releases were affected.
- Whether Unity's official MCP is deprecated in favour of the Unity CLI comes from one third-party blog. unity-agent research may know more.
- Printables' exact AI rules, Fab's current EULA wording and any Roblox Creator Store AI rule were not read from primary pages.
- 3DCodeBench visual-feedback results sit in an appendix I did not read (page was cut at 100k characters). 3DHarnessBench model names (Fable 5, Opus 5, GPT-5.6 Sol) are as printed in its tables.
- A Neural4D blog claims OpenAI released "GPT-6 Astra" on 2026-09-03 with Blender agent demos. Single vendor source; not verified.
- No Anthropic or OpenAI cookbook entry for 3D was found; the search budget ran out before a second try.
- Reddit RSS returned 429 throughout. A later session should pull r/blender, r/gamedev, r/aigamedev, r/3Dmodeling, r/ClaudeAI and r/LocalLLaMA at one request per 60 s for first-hand quotes.
- Tripo's official MCP looks abandoned (last push 2025-04-14). Check whether Tripo now prefers a skills pack like Meshy.
- dcc-mcp is young but covers 47 hosts. Re-check in a month whether it should become polywright's single DCC bridge.

## Sources

Tools and repositories (GitHub API figures fetched 2026-10-11):
- https://github.com/ahujasid/mcp-for-blender
- https://www.blender.org/lab/mcp-server/
- https://www.strayspark.studio/blog/official-blender-mcp-server-comparison-2026 (vendor, 2026-09)
- https://www.strayspark.studio/blog/ai-hallucinating-blender-python-api-bpy-fix (vendor, 2026-09-14)
- https://github.com/earthtojake/text-to-cad
- https://github.com/seena18/meshwright
- https://github.com/GeekatplayStudio/Meshwright
- https://github.com/billtruong003/ShapeWright
- https://github.com/anandasatriaadi/shapewright
- https://pypi.org/project/build123d-mcp/
- https://github.com/RobLe3/cc-blender-skill
- https://docs.meshy.ai/en/api/ai
- https://github.com/VAST-AI-Research/tripo-mcp
- https://github.com/dcc-mcp/dcc-mcp-core
- https://github.com/cl0nazepamm/3dsmax-mcp
- https://github.com/capoomgit/houdini-mcp
- https://github.com/neka-nat/freecad-mcp
- https://github.com/RobertCoop/openscad-mcp
- https://github.com/flowful-ai/cad-skill
- https://github.com/mitsuhiko/agent-stuff
- https://github.com/ChiR24/Unreal_mcp
- https://github.com/CoplayDev/unity-mcp
- https://www.fortnite.com/news/unreal-mcp-is-now-available-in-uefn (2026-08-20)
- https://digitalproduction.com/2026/10/01/cinema-4d-2026-4-mcp/
- https://www.jonpeddie.com/news/sidefx-and-nvidia-bring-mcp-powered-ai-agents-to-houdini-22s-rigging-workflow-at-siggraph-2026/
- https://develop3d.com/ai/claude-for-cad-blender-autodesk-fusion/
- https://blog.comfy.org/p/trellis2-and-pixal3d-are-now-native

Papers:
- arXiv 2310.12945, 2403.01248, 2404.17672, 2410.05340, 2412.13810, 2412.14203, 2501.18623, 2504.01786, 2506.23329, 2508.08228, 2508.14879, 2510.17603, 2601.05016, 2601.07143, 2606.01057, 2607.22393, 2609.06535

Practitioner and policy:
- https://www.mindstudio.ai/blog/claude-blender-mcp-60-percent-tokens-donut-test-results (2026-05-01)
- https://www.mindstudio.ai/blog/claude-blender-mcp-real-world-performance (2026-05-06)
- https://www.lifehacker.jp/article/2606taught-claude-3d-design-prints-real-parts/ (updated 2026-08-13)
- https://pardesco.com/blogs/technology-art-design/3d-design-with-ai (2026-09-23)
- https://blenderartists.org/t/from-blender-mcp-to-3d-agent-anthropic-partners-with-blender-claude-ai-connector-now-official/1639106 (2026-04-28)
- https://www.cgchannel.com/?p=175793 (2026-05-04)
- https://www.blendernation.com/2026/05/01/update-anthropic-joins-the-blender-development-fund/
- Hacker News items 47970497, 48572553, 49238028, 49405520, 47567242 (via hn.algolia.com)
- https://wiki.bambulab.com/en/makerworld/ai-policy and https://www.fabbaloo.com/?p=234795 (2026-02-10)
- https://support.unity.com/hc/en-us/articles/16456407029524
- https://forums.unrealengine.com/t/ai-image-use/2567909
- https://www.videogameschronicle.com/news/valve-has-significantly-rewritten-steams-rules-for-how-developers-much-disclose-ai-use (January 2026)
- https://help.sketchfab.com/en/articles/16152133
- https://create.roblox.com/docs/ai/accelerated-workflows
- https://huggingface.co/datasets/allenai/objaverse-xl
