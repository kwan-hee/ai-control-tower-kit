"""AI 관제탑 키트 설치 스크립트.

질문 몇 개에 답하면 이 폴더를 '나만의 관제탑'으로 바꿔 줍니다.

    python setup.py              # 질문에 답하며 설치
    python setup.py --defaults   # 질문 없이 기본값으로 설치 (나중에 config.json 수정)
    python setup.py --force      # 이미 설치된 파일도 다시 만듦 (내가 고친 내용은 사라짐)

설치가 하는 일:
  1. config.json 을 만든다 (이름, 제목, 색, 노트 폴더 위치).
  2. _templates/ 안의 파일에서 {{OWNER}}, {{ROOT}}, {{VAULT}} 같은 자리를 채워
     CLAUDE.md, guides/, .claude/skills/, routines/ 를 만든다.
  3. 노트 폴더를 지정하지 않았다면 notes/ 에 예시 노트를 만든다.
  4. 대시보드(dashboard/index.html)를 만든다.
예약 작업 등록이나 외부 서비스 연결은 하지 않는다. README의 다음 단계를 따른다.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "_templates"
CONFIG = ROOT / "config.json"
EXAMPLE = ROOT / "config.example.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
PRESET_COLORS = {"1": ("코랄", "#ef6c4d"), "2": ("블루", "#4d8bef"), "3": ("그린", "#3fb37f"),
                 "4": ("퍼플", "#9b6cef"), "5": ("옐로", "#e8b33a")}


def ask(question: str, default: str) -> str:
    try:
        answer = input(f"{question} [{default}]: ").strip()
    except EOFError:
        answer = ""
    return answer or default


def collect(defaults_only: bool) -> dict:
    cfg = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    if CONFIG.exists():
        cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    if defaults_only:
        return cfg

    print("\n=== AI 관제탑 키트 설치 ===  (엔터를 누르면 [ ] 안의 값을 씁니다)\n")
    cfg["owner"] = ask("1. 이름(또는 닉네임)", cfg["owner"])
    cfg["title"] = ask("2. 대시보드 제목", f"{cfg['owner']} 관제탑")
    print("3. 강조 색: " + "  ".join(f"{k}) {n}" for k, (n, _) in PRESET_COLORS.items()) + "  또는 #RRGGBB")
    choice = ask("   선택", "1")
    cfg["accent"] = PRESET_COLORS[choice][1] if choice in PRESET_COLORS else (choice if HEX.match(choice) else cfg["accent"])
    cfg["theme"] = "light" if ask("4. 화면 테마 (dark / light)", cfg.get("theme", "dark")).lower().startswith("l") else "dark"
    print("5. 노트 폴더: Obsidian vault 같은 노트 폴더가 있으면 전체 경로를 적습니다.")
    print("   없으면 엔터 → 이 폴더 안의 notes\\ 에 예시 노트를 만들어 씁니다.")
    vault = ask("   경로", cfg.get("vault_path") or "")
    if vault and not Path(vault).expanduser().is_dir():
        print(f"   ! '{vault}' 폴더를 찾지 못했습니다. notes\\ 를 대신 씁니다.")
        vault = ""
    cfg["vault_path"] = vault
    cfg["obsidian_vault_name"] = Path(vault).name if vault and (Path(vault) / ".obsidian").is_dir() else ""
    cfg["briefing_time"] = ask("6. 모닝 브리핑 시각 (HH:MM)", cfg.get("briefing_time", "09:00"))
    return cfg


def render(text: str, values: dict[str, str], as_json: bool = False) -> str:
    for key, val in values.items():
        # Inside JSON strings a Windows path needs escaped backslashes (C:\\Users).
        text = text.replace("{{" + key + "}}", json.dumps(val, ensure_ascii=False)[1:-1] if as_json else val)
    return text


def install(cfg: dict, force: bool) -> None:
    vault = cfg["vault_path"] or str(ROOT / "notes")
    values = {"OWNER": cfg["owner"], "TITLE": cfg["title"], "ROOT": str(ROOT), "VAULT": vault,
              "BRIEFING_TIME": cfg.get("briefing_time", "09:00")}
    created, kept = 0, 0
    for src in TEMPLATES.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(TEMPLATES)
        if rel.parts[0] == "notes" and cfg["vault_path"]:
            continue  # 사용자가 자기 노트 폴더를 지정했으면 예시 노트는 만들지 않는다
        dst = ROOT / rel
        if dst.exists() and not force:
            kept += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in {".md", ".json", ".txt"}:
            text = render(src.read_text(encoding="utf-8"), values, as_json=src.suffix == ".json")
            if src.suffix == ".json":
                json.loads(text)  # fail loudly instead of writing a file the dashboard can't read
            dst.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(src, dst)
        created += 1
    for d in ("logs/briefings", "logs/skill-reviews", "logs/inbox-reviews"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    print(f"\n파일 {created}개를 만들었습니다." + (f" 이미 있던 {kept}개는 그대로 두었습니다 (--force로 다시 만들 수 있음)." if kept else ""))


def main() -> None:
    args = set(sys.argv[1:])
    cfg = collect("--defaults" in args)
    if not HEX.match(cfg.get("accent", "")):
        cfg["accent"] = "#ef6c4d"
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"설정을 저장했습니다: {CONFIG}")
    install(cfg, "--force" in args)
    sys.stdout.flush()
    subprocess.run([sys.executable, str(ROOT / "dashboard" / "build.py")], check=True)
    print(f"""
=== 설치 완료 ===
다음 단계:
  1. 대시보드 열기:  {ROOT / 'dashboard' / 'index.html'}  (더블클릭)
  2. Claude 데스크톱 앱 → Code 탭에서 이 폴더를 열고 말하기:
       "모닝 브리핑 해줘"
       "routines.json의 루틴을 예약 작업으로 등록해 줘"
  3. 내 취향대로 바꾸기: CUSTOMIZE.md 를 참고하세요.
""")


if __name__ == "__main__":
    main()
