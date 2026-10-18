"""Structure checks for the polywright skills (stdlib only, Python 3.8+).

Run from the repository root: python tests/check_skills.py
Exits 1 and prints every problem when a check fails; prints one summary line when all pass.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
COMPANIONS = ["SKILL.md", "RESEARCH.md", "CHANGELOG.md", "LEARNINGS.md", "TESTS.md",
              "MAINTENANCE.md", "evergreen.json", os.path.join("evals", "evals.json")]
MAX_SKILL_LINES = 200          # AGENTS.md: skills stay under 200 lines
MAX_DESCRIPTION = 1024         # Agent Skills spec limit for the description field
SKIP_DIRS = {".git", "__pycache__", "dist", "node_modules", ".claude"}
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Public-safety guards that name nothing private: an absolute path into someone's home folder
# (placeholders such as C:\Users\<you> are allowed) and AI attribution lines.
HOME_PATH = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+(?!<)[a-z0-9._-]+|/home/(?!<)[a-z0-9._-]+/|/Users/(?!<|Shared)[a-z0-9._-]+/")
# The owner's own machine paths and private project folders (generalise lessons before committing them).
PRIVATE = re.compile(r"(?i)\b[a-z]:[\\/]+m4bwa\b|[\\/]Claude[\\/]Projects[\\/]")
# Any absolute Windows drive path with at least two real segments (D:/ComfyUI/output/...). A placeholder
# segment such as D:/<project>/... is allowed, and so is a drive root alone (C:\ in a sentence).
DRIVE_PATH = re.compile(r"(?<![A-Za-z0-9\\])[A-Za-z]:[\\/]+(?!<)[A-Za-z0-9_. -]*[A-Za-z0-9_-][\\/]+(?!<)[A-Za-z0-9_.-]")
# The owner's private project, skill and marketplace names, and his name used for a ruling (the author
# credit "Mark Rogers" stays). Generalise to "a film", "a toy figure", "the owner".
PRIVATE_NAMES = re.compile(r"(?i)\bno-?god\b|\bdummy[ _-]?13(?![0-9])|\bcomfyui-gen\b|\bmark-local\b|\bcrashsite\b|\bmentos\b"
                           r"|(?-i:\bMark (?:ruled|said|asked|wants|wanted|approved|chose|picked)\b)")
ATTRIBUTION = re.compile(r"(?i)co-authored-by:|generated with (claude|chatgpt|copilot)|written by (claude|an ai)")

problems = []


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def walk_files():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for f in fns:
            yield os.path.join(dp, f)


def frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    fields = {}
    for line in text[3:end].strip().splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            fields[m.group(1)] = v
    return fields


def check_skills():
    names = sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))
    if not names:
        problems.append("skills/: no skill folders")
    for name in names:
        d = os.path.join(SKILLS, name)
        for c in COMPANIONS:
            if not os.path.isfile(os.path.join(d, c)):
                problems.append(f"skills/{name}: missing {c.replace(os.sep, '/')}")
        sk = os.path.join(d, "SKILL.md")
        if os.path.isfile(sk):
            text = open(sk, encoding="utf-8").read()
            fm = frontmatter(text)
            if fm is None:
                problems.append(f"skills/{name}/SKILL.md: no YAML frontmatter")
            else:
                if fm.get("name") != name:
                    problems.append(f"skills/{name}/SKILL.md: frontmatter name {fm.get('name')!r} differs from the folder")
                desc = fm.get("description", "")
                if not desc:
                    problems.append(f"skills/{name}/SKILL.md: empty description")
                elif len(desc) > MAX_DESCRIPTION:
                    problems.append(f"skills/{name}/SKILL.md: description is {len(desc)} characters (limit {MAX_DESCRIPTION})")
            n = text.count("\n") + 1
            if n > MAX_SKILL_LINES:
                problems.append(f"skills/{name}/SKILL.md: {n} lines (budget {MAX_SKILL_LINES})")
        eg = os.path.join(d, "evergreen.json")
        if os.path.isfile(eg):
            try:
                st = json.load(open(eg, encoding="utf-8"))
                if st.get("name") != name:
                    problems.append(f"skills/{name}/evergreen.json: name {st.get('name')!r} differs from the folder")
                for k in ("tier", "last_checked", "next_due", "protocol"):
                    if k not in st:
                        problems.append(f"skills/{name}/evergreen.json: missing {k}")
                if st.get("source"):
                    problems.append(f"skills/{name}/evergreen.json: source must be null in the repository (it is a local path)")
            except ValueError:
                pass  # reported by check_json
    return names


def check_json():
    for f in walk_files():
        if f.endswith(".json"):
            try:
                json.load(open(f, encoding="utf-8"))
            except ValueError as e:
                problems.append(f"{rel(f)}: invalid JSON ({e})")
    manifest = os.path.join(ROOT, ".claude-plugin", "plugin.json")
    try:
        m = json.load(open(manifest, encoding="utf-8"))
        if not re.match(r"^\d+\.\d+\.\d+$", str(m.get("version", ""))):
            problems.append(".claude-plugin/plugin.json: version is not X.Y.Z")
        pw = open(os.path.join(SKILLS, "polywright", "scripts", "pw.py"), encoding="utf-8").read()
        v = re.search(r'^VERSION = "([^"]+)"', pw, re.M)
        if not v or v.group(1) != m.get("version"):
            problems.append("skills/polywright/scripts/pw.py: VERSION %s differs from plugin.json %s" % (v and v.group(1), m.get("version")))
    except (OSError, ValueError):
        problems.append(".claude-plugin/plugin.json: missing or unreadable")


def check_links_and_text():
    for f in walk_files():
        if not f.endswith((".md", ".json", ".ps1", ".cs", ".py", ".yml")):
            continue
        text = open(f, encoding="utf-8", errors="replace").read()
        if f.endswith(".md"):
            for target in LINK.findall(text):
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                path = target.split("#", 1)[0]
                if path and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), path))):
                    problems.append(f"{rel(f)}: broken relative link {target}")
        if os.path.abspath(f) == os.path.abspath(__file__):
            continue
        m = HOME_PATH.search(text)
        if m:
            problems.append(f"{rel(f)}: absolute home-folder path {m.group(0)!r}; use a placeholder")
        pv = PRIVATE.search(text)
        if pv:
            problems.append(f"{rel(f)}: private machine path {pv.group(0)!r}; generalise it")
        dp = DRIVE_PATH.search(text)
        if dp and not pv:
            problems.append(f"{rel(f)}: absolute drive path {dp.group(0)!r}; use a placeholder such as D:/<folder>/")
        pn = PRIVATE_NAMES.search(text)
        if pn:
            problems.append(f"{rel(f)}: private name {pn.group(0)!r}; generalise it")
        a = ATTRIBUTION.search(text)
        if a:
            problems.append(f"{rel(f)}: AI attribution {a.group(0)!r}")


if __name__ == "__main__":
    names = check_skills()
    check_json()
    check_links_and_text()
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(" - " + p)
        sys.exit(1)
    print(f"ok: {len(names)} skills, companions, manifests, links and text guards")
