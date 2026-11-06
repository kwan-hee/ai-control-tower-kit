# AI 관제탑 키트

Claude와 함께 쓰는 **나만의 AI 업무 시스템** 시작 키트입니다.
설치하면 아래 네 가지와 한 화면 대시보드가 만들어집니다.

| 단계 | 하는 일 | 키트에 들어 있는 것 |
|---|---|---|
| 1. 스킬 | 반복 업무를 AI 단축키로 만든다 | 모닝 브리핑, 스킬 개선, 커넥터 찾기 스킬 |
| 2. 세컨드 브레인 | AI가 자료를 스스로 찾게 한다 | `CLAUDE.md`(대문) + `guides/`(길잡이) + 예시 노트 |
| 3. 루틴 | 정해진 시간에 자동으로 일한다 | 매일 브리핑, 주간 Inbox 정리, 주간 스킬 점검 |
| 4. 익스텐션 | 메일·캘린더 같은 외부 서비스와 연결한다 | 연결 목록과 연결 방법 안내 |
| + 대시보드 | 위 내용을 한 화면에서 본다 | `dashboard/index.html` (파일 하나, 서버 필요 없음) |

## 준비물

- Windows PC (macOS에서도 대부분 동작합니다)
- [Python 3.10 이상](https://www.python.org/downloads/) — 설치할 때 "Add python.exe to PATH"를 체크하세요
- [Claude 데스크톱 앱](https://claude.ai/download) (Code 탭 사용)
- 선택: Obsidian 같은 노트 앱 (없어도 됩니다)

## 5분 설치

1. 이 키트를 원하는 곳에 압축 해제합니다. 예: `C:\내 관제탑`
2. 그 폴더에서 터미널(PowerShell)을 열고 실행합니다.

   ```bat
   python setup.py
   ```

3. 질문 6개에 답합니다: 이름, 대시보드 제목, 강조 색, 테마, 노트 폴더, 브리핑 시각. 모르면 엔터를 누르세요.
4. `dashboard\index.html`을 더블클릭해서 대시보드를 엽니다.

## 설치한 다음 할 일

Claude 데스크톱 앱의 **Code 탭**에서 이 폴더를 열고 아래처럼 말합니다.

1. **외부 서비스 연결**: 앱의 설정 → 커넥터에서 Gmail, Google Calendar 등을 연결합니다.
2. **첫 브리핑**: `모닝 브리핑 해줘`
3. **루틴 등록**: `routines.json의 루틴을 예약 작업으로 등록해 줘`
4. **나에 대한 정보 채우기**: `CLAUDE.md의 "꼭 기억할 것"과 guides 길잡이를 내 상황에 맞게 같이 채워 줘`

## 내 취향대로 바꾸기

[CUSTOMIZE.md](CUSTOMIZE.md)에 정리했습니다. 대부분은 Claude에게 말로 시키면 됩니다.

- 제목·색·테마 → `config.json` 수정 후 `python dashboard\build.py`
- 대시보드 배치·디자인 → `dashboard\template.html`
- 길잡이·스킬·루틴 → `guides\`, `.claude\skills\`, `routines\`

## 폴더 구조 (설치 후)

```
config.json          설정 (이름, 제목, 색, 노트 폴더)
CLAUDE.md            대문: Claude가 가장 먼저 읽는 파일
guides\              길잡이 파일 (분야별 링크 모음)
.claude\skills\      이 폴더 전용 스킬 3개
routines\            루틴 정의와 24시간 운영 방법
notes\               예시 노트 (노트 폴더를 지정하지 않았을 때)
dashboard\           build.py · template.html → index.html
logs\                브리핑, 점검 기록
_templates\          설치 원본 (지우지 마세요)
```

## 개인정보 안내

- 브리핑에는 메일 제목과 일정이 들어갑니다. `logs\`, `config.json`, `dashboard\index.html`은 **다른 사람에게 공유하지 마세요.**
- 이 키트를 고쳐서 다시 공유할 때는 `.gitignore`에 적힌 파일이 빠졌는지 확인하세요.

## 만든 사람과 참고

- 만든 사람: Joy ([kwan-hee](https://github.com/kwan-hee))
- 4단계 구조(스킬 · 세컨드 브레인 · 루틴 · 익스텐션)는 유튜브 영상 「클로드는 이렇게 쓰는 겁니다: 나만의 'AI 업무 시스템' 4단계 구축법」(챗대리의 AI연구소)을 보고 따라 만들었습니다. 코드와 문서는 이 키트를 위해 새로 작성했습니다.
- 라이선스: MIT — 자유롭게 고쳐 쓰고 다시 나눠도 됩니다.
