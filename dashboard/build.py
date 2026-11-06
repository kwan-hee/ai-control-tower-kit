"""Build dashboard/index.html from config.json and the files in this kit.

Scans skills, guide files, routines, the notes folder and the briefings,
then injects the data into template.html and writes one self-contained
index.html. Re-run any time:
    python dashboard/build.py
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "dashboard" / "template.html"
OUT = ROOT / "dashboard" / "index.html"
DATA_MARKER = "/*__DASH_DATA__*/null"

DEFAULT_CONFIG = {
    "owner": "나", "title": "AI 관제탑", "subtitle": "AI 에이전트 시스템", "theme": "dark",
    "accent": "#ef6c4d", "vault_path": "", "obsidian_vault_name": "",
    "skill_dirs": ["~/.claude/skills"], "category_rules": {},
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    for name in ("config.example.json", "config.json"):
        p = ROOT / name
        if p.exists():
            try:
                cfg.update(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{p} 형식이 잘못되었습니다: {e}")
    return cfg


CFG = load_config()
VAULT = Path(CFG["vault_path"]).expanduser() if CFG.get("vault_path") else ROOT / "notes"
SKILL_DIRS = [("전역", Path(d).expanduser()) for d in CFG.get("skill_dirs", [])] + [("시스템", ROOT / ".claude" / "skills")]
CATEGORY_RULES = list(CFG.get("category_rules", {}).items())


def categorize(name: str, description: str) -> str:
    text = f"{name} {description[:120]}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(k.lower() in text for k in keywords):
            return category
    return "기타"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def parse_frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    data: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if km:
            key = km.group(1)
            data[key] = km.group(2).strip().strip("'\"")
        elif key and line.startswith((" ", "\t")):
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def scan_skills() -> list[dict]:
    skills, seen = [], set()
    for scope, base in SKILL_DIRS:
        if not base.is_dir():
            continue
        for skill_md in sorted(base.glob("*/SKILL.md")):
            fm = parse_frontmatter(read_text(skill_md))
            name = fm.get("name") or skill_md.parent.name
            if (scope, name) in seen:
                continue
            seen.add((scope, name))
            desc = re.sub(r"\s+", " ", fm.get("description", "")).strip()
            refs = sum(1 for p in skill_md.parent.rglob("*") if p.is_file()) - 1
            skills.append({"name": name, "scope": scope, "description": desc[:400],
                           "category": "시스템" if scope == "시스템" else categorize(name, desc),
                           "refs": max(refs, 0), "path": str(skill_md.parent)})
    return skills


LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[^\]]*)\]\]|`([A-Za-z]:\\[^`]+)`")


def scan_guides() -> list[dict]:
    guides = []
    files = [ROOT / "CLAUDE.md"] + sorted((ROOT / "guides").glob("*.md"))
    for f in files:
        if not f.exists():
            continue
        text = read_text(f)
        title_m = re.search(r"^#\s+(.+)$", text, re.M)
        links, seen = [], set()
        for m in LINK_RE.finditer(text):
            target = (m.group(1) or m.group(2)).strip()
            if target not in seen:
                seen.add(target)
                links.append({"target": target, "kind": "note" if m.group(1) else "path"})
        guides.append({"file": f.name, "id": f.stem, "title": title_m.group(1) if title_m else f.stem,
                       "path": str(f), "links": links})
    return guides


def scan_vault() -> dict:
    if not VAULT.is_dir():
        return {"exists": False, "path": str(VAULT), "folders": [], "notes": [], "recent": [], "recent7": 0}
    notes = []
    for p in VAULT.rglob("*.md"):
        rel = p.relative_to(VAULT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        notes.append((p.stat().st_mtime, rel.as_posix()))
    notes.sort(reverse=True)
    week_ago = datetime.now().timestamp() - 7 * 86400
    return {
        "exists": True,
        "name": CFG.get("obsidian_vault_name") or "",
        "path": str(VAULT),
        "notes": [rel for _, rel in notes],
        "recent": [{"rel": rel, "mtime": datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")} for t, rel in notes[:10]],
        "recent7": sum(1 for t, _ in notes if t >= week_ago),
    }


def scan_routines() -> list[dict]:
    data = read_text(ROOT / "routines" / "routines.json")
    try:
        return json.loads(data).get("routines", []) if data else []
    except json.JSONDecodeError:
        return []


def scan_briefings() -> dict:
    folder = ROOT / "logs" / "briefings"
    md_files = sorted(folder.glob("*.md")) if folder.is_dir() else []
    result: dict = {"dates": [f.stem for f in md_files], "latest": None}
    if not md_files:
        return result
    f = md_files[-1]
    extra: dict = {}
    if f.with_suffix(".json").exists():
        try:
            extra = json.loads(read_text(f.with_suffix(".json")))
        except json.JSONDecodeError:
            extra = {}
    result["latest"] = {"date": f.stem, "path": str(f), "top3": extra.get("top3", []),
                        "events": extra.get("events", []), "emails": extra.get("emails", [])}
    return result


def main() -> None:
    data = {
        "builtAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "root": str(ROOT),
        "config": {k: CFG.get(k) for k in ("owner", "title", "subtitle", "theme", "accent")},
        "skills": scan_skills(),
        "guides": scan_guides(),
        "routines": scan_routines(),
        "vault": scan_vault(),
        "briefings": scan_briefings(),
    }
    template = read_text(TEMPLATE)
    if DATA_MARKER not in template:
        raise SystemExit(f"{TEMPLATE} 에 데이터 자리({DATA_MARKER})가 없습니다.")
    # "</" is escaped so note text can never close the <script> tag early.
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(template.replace(DATA_MARKER, payload), encoding="utf-8")
    print(f"대시보드를 만들었습니다: {OUT}\n  스킬 {len(data['skills'])}개 · 길잡이 {len(data['guides'])}개 · "
          f"루틴 {len(data['routines'])}개 · 노트 {len(data['vault']['notes'])}개")


if __name__ == "__main__":
    main()
