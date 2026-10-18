"""Run the skills' eval cases headless with `claude -p` and grade them on trace evidence.

Run from the repository root (stdlib only, Python 3.9+):

    python tests/run_evals.py --kinds trigger --runs 3 --out evals-out
    python tests/run_evals.py --skills polywright-print --ids action-1 --runs 1 --out evals-out
    python tests/run_evals.py --kinds outcome --baseline --out evals-out   # without polywright

Each run starts a fresh session in a throwaway copy of the repository (cases name tests/fixtures)
with this checkout loaded through --plugin-dir and any installed polywright plugin switched off,
so the descriptions under test are the ones on disk. --baseline loads no polywright at all.

Grading, on evidence only (never the final message's claims):
- trigger: passes when the trace has a Skill call naming the skill; a decoy passes when it has none. Trigger
  runs cannot run commands or write files: a decoy that loads another skill (a ComfyUI image skill) once ran
  a real 12-minute GPU job.
- action: an `evidence` dict with `input_match` passes when a tool call's input matches it; a list
  of evidence lines is printed for a person to check against the saved trace and files.
- outcome: an expectation starting "regex on the answer:" is matched against the final message.

Writes OUT/<skill>/<id>-r<n>.jsonl (the stream-json trace) and OUT/results.json, prints a summary.
On Windows, claude is a .cmd shim: it is started through shutil.which, since a bare "claude"
fails with WinError 2 and looks like a run with zero skill calls.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
def installed_copies():
    """Every installed polywright plugin (any marketplace), so the checkout under test is the only copy loaded."""
    names = {"polywright@polywright"}
    try:
        with open(os.path.join(os.path.expanduser("~"), ".claude", "settings.json"), encoding="utf-8") as fh:
            names |= {k for k in json.load(fh).get("enabledPlugins", {}) if k.split("@", 1)[0] == "polywright"}
    except (OSError, ValueError, AttributeError):
        pass
    return {"enabledPlugins": {n: False for n in sorted(names)}}


DISABLE = installed_copies()
DEFAULT_TURNS = {"trigger": 6, "action": 30, "outcome": 12}


def load_cases(skills, kinds, ids):
    out = []
    for name in sorted(os.listdir(SKILLS)):
        if skills and name not in skills:
            continue
        path = os.path.join(SKILLS, name, "evals", "evals.json")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for case in json.load(fh)["evals"]:
                if kinds and case["kind"] not in kinds:
                    continue
                if ids and case["id"] not in ids:
                    continue
                out.append((name, case))
    return out


def throwaway_clone():
    dest = tempfile.mkdtemp(prefix="pw-eval-")
    shutil.copytree(os.path.join(ROOT, "tests", "fixtures"), os.path.join(dest, "tests", "fixtures"))
    shutil.copytree(SKILLS, os.path.join(dest, "skills"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def run_case(claude, skill, case, run, args):
    kind = case["kind"]
    cwd = throwaway_clone()
    cmd = [claude, "-p", case["prompt"], "--output-format", "stream-json", "--verbose",
           "--no-session-persistence", "--max-turns", str(case.get("max_turns", DEFAULT_TURNS[kind])),
           "--settings", json.dumps(DISABLE), "--permission-mode", "bypassPermissions"]
    if kind == "trigger":  # the Skill call is the evidence; a decoy must not run real jobs (a GPU render, a download)
        cmd += ["--disallowed-tools", "Bash", "PowerShell", "Write", "Edit", "NotebookEdit"]
    if not args.baseline:
        cmd += ["--plugin-dir", ROOT]
    if args.model:
        cmd += ["--model", args.model]
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=args.timeout)
        stdout, err = proc.stdout, proc.stderr[-500:]
    except subprocess.TimeoutExpired as exc:
        stdout, err = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""), "timeout"
    trace_dir = os.path.join(args.out, skill)
    os.makedirs(trace_dir, exist_ok=True)
    trace = os.path.join(trace_dir, "%s-r%d%s.jsonl" % (case["id"], run, "-base" if args.baseline else ""))
    with open(trace, "w", encoding="utf-8") as fh:
        fh.write(stdout)
    result = grade(skill, case, stdout)
    result.update(skill=skill, id=case["id"], kind=kind, run=run, baseline=args.baseline,
                  seconds=round(time.time() - started), trace=os.path.relpath(trace, args.out), cwd=cwd,
                  stderr=err if not stdout else "")
    if not args.keep:
        shutil.rmtree(cwd, ignore_errors=True)
    return result


def events(stdout):
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                yield json.loads(line)
            except ValueError:
                pass


def grade(skill, case, stdout):
    skills_called, tool_inputs, final, cost, plugins = [], [], "", None, None
    for ev in events(stdout):
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            plugins = [p.get("name") for p in ev.get("plugins", [])]
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_inputs.append((block.get("name"), json.dumps(block.get("input", {}))))
                    if block.get("name") == "Skill":
                        skills_called.append(str(block.get("input", {}).get("skill", "")))
        if ev.get("type") == "result":
            final, cost = ev.get("result") or "", ev.get("total_cost_usd")
    invoked = any(s == skill or s.endswith(":" + skill) for s in skills_called)
    kind, verdict, notes = case["kind"], None, []
    if kind == "trigger":
        verdict = (not invoked) if case.get("decoy") else invoked
    elif kind == "action":
        ev = case.get("evidence")
        if isinstance(ev, dict) and ev.get("input_match"):
            pat = re.compile(ev["input_match"])
            tools = re.compile(ev.get("tool", ".*"))
            verdict = any(tools.fullmatch(n or "") and pat.search(i) for n, i in tool_inputs)
        else:
            notes.append("check by hand: %s" % ev)
    elif kind == "outcome":
        for exp in case.get("expectations", []):
            if exp.startswith("regex on the answer:"):
                verdict = bool(re.search(exp.split(":", 1)[1].strip(), final, re.S))
        if verdict is None:
            notes.append("check the answer by hand against the expectations")
    return {"passed": verdict, "invoked": invoked, "skills_called": skills_called,
            "tool_calls": len(tool_inputs), "cost_usd": cost, "plugins": plugins, "notes": notes,
            "answer": final[:600]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skills", nargs="*", help="skill folder names (default: all)")
    ap.add_argument("--kinds", nargs="*", choices=["trigger", "action", "outcome"])
    ap.add_argument("--ids", nargs="*", help="case ids, e.g. trigger-1 action-1")
    ap.add_argument("--runs", type=int, default=None, help="runs per case (default: the case's own)")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--baseline", action="store_true", help="run without polywright loaded")
    ap.add_argument("--model", help="model alias passed to claude --model")
    ap.add_argument("--keep", action="store_true", help="keep the throwaway clones")
    ap.add_argument("--out", required=True, help="folder for traces and results.json")
    args = ap.parse_args()
    claude = shutil.which("claude")
    if not claude:
        sys.exit("claude not found on PATH")
    args.out = os.path.abspath(args.out)
    jobs = []
    for skill, case in load_cases(args.skills, args.kinds, args.ids):
        for run in range(1, (args.runs or case.get("runs", 1)) + 1):
            jobs.append((skill, case, run))
    print("running %d jobs, %d at a time" % (len(jobs), args.parallel), flush=True)
    results = []
    with cf.ThreadPoolExecutor(args.parallel) as pool:
        futures = [pool.submit(run_case, claude, s, c, r, args) for s, c, r in jobs]
        for fut in cf.as_completed(futures):
            r = fut.result()
            results.append(r)
            mark = {True: "PASS", False: "FAIL", None: "HAND"}[r["passed"]]
            print("%s %s %s r%d %ss skills=%s" % (mark, r["skill"], r["id"], r["run"], r["seconds"],
                                                  r["skills_called"]), flush=True)
    results.sort(key=lambda r: (r["skill"], r["id"], r["run"]))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    graded = [r for r in results if r["passed"] is not None]
    print(json.dumps({"ok": True, "runs": len(results), "graded": len(graded),
                      "passed": sum(1 for r in graded if r["passed"]),
                      "cost_usd": round(sum(r["cost_usd"] or 0 for r in results), 2)}))


if __name__ == "__main__":
    main()
