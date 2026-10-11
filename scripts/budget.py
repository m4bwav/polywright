"""Size budget for polywright. Run from the repository root: python scripts/budget.py [--json]

The always-loaded footprint (every skill's description is read in every session) and the installed size must
stay small enough that nobody thinks twice about installing the plugin. Exit 2 at red, 0 otherwise; a yellow
is printed so the maintainer can be told. Tokens are estimated as bytes / 4.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

# measure, green <=, yellow <= (above yellow is red)
BUDGETS = [
    ("largest description characters (always loaded; spec limit 1,024)", 700, 1024),
    ("all descriptions tokens together (always loaded)", 1100, 1500),
    ("largest SKILL.md tokens (loaded on every use)", 2500, 3500),
    ("largest reference tokens (loaded on demand; scripts are run, not read)", 3500, 5000),
    ("installed skills folder KB", 400, 800),
    ("tracked repository KB", 2048, 4096),
]


def measure():
    descs, skill_tokens, extra = [], [], []
    for sk in sorted(SKILLS.glob("*/SKILL.md")):
        text = sk.read_text(encoding="utf-8")
        m = re.search(r'^description:\s*"(.*)"\s*$', text, re.M)
        descs.append((len(m.group(1)) if m else 0, sk.parent.name))
        skill_tokens.append((len(text.encode("utf-8")) // 4, sk.parent.name))
        for f in [r for r in sk.parent.glob("references/*") if r.suffix == ".md"]:
            extra.append((f.stat().st_size // 4, "%s/%s" % (sk.parent.name, f.name)))
    files = [p for p in SKILLS.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    folder_kb = (sum(p.stat().st_size for p in files) // 1024, "")
    try:
        tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.split(b"\0")
        repo_kb = sum((ROOT / t.decode()).stat().st_size for t in tracked if t and (ROOT / t.decode()).exists()) // 1024
    except (OSError, subprocess.CalledProcessError):
        repo_kb = folder_kb[0]
    total_desc_tokens = sum(d for d, _ in descs) // 4
    return [max(descs), (total_desc_tokens, "%d skills" % len(descs)), max(skill_tokens),
            max(extra) if extra else (0, ""), folder_kb, (repo_kb, "")]


def main():
    rows = []
    for (label, g, y), (v, where) in zip(BUDGETS, measure()):
        status = "green" if v <= g else ("yellow" if v <= y else "red")
        rows.append({"measure": label, "value": v, "green": g, "yellow": y, "status": status, "worst": where})
    overall = "red" if any(r["status"] == "red" for r in rows) else ("yellow" if any(r["status"] == "yellow" for r in rows) else "green")
    if "--json" in sys.argv:
        print(json.dumps({"overall": overall, "rows": rows}, indent=2))
    else:
        for r in rows:
            print("%-68s %6s  green<=%-5s yellow<=%-5s %-6s %s" % (r["measure"], r["value"], r["green"], r["yellow"], r["status"], r["worst"]))
        print("budget: %s" % overall.upper())
    return 2 if overall == "red" else 0


if __name__ == "__main__":
    sys.exit(main())
