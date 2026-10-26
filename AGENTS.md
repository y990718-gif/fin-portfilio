# AGENTS.md

이 저장소에서 작업하는 AI 코딩 에이전트(Claude Code, Codex 등)를 위한 안내서입니다.

## 프로젝트 개요

**아침 경제 브리핑**: 은행 취업을 준비하는 사용자를 위해 평일 아침마다 경제 뉴스·증시·환율을 모아 Claude API로 요약하고 Notion에 올리는 Python 앱입니다. 자세한 기획은 [PLAN.md](PLAN.md), 설치 방법은 [README.md](README.md)를 보세요.

- 저장소: https://github.com/y990718-gif/fin-portfilio (레포 이름의 철자는 `portfilio`가 맞습니다)
- 실행: GitHub Actions, 평일 08:30 KST (`.github/workflows/daily.yml`)

## 사용자와 소통하기

- 사용자에게 하는 말과 문서는 **한국어**로 씁니다.
- 사용자는 개발 입문자입니다. 전문 용어는 쉽게 풀어서 설명하고, 사용자가 직접 해야 하는 일은 클릭할 위치까지 단계별로 안내합니다.

## 🔴 필수 규칙: 작업 내용은 항상 Notion에 정리한다

작업을 마칠 때마다(파일을 바꾸거나, 커밋·푸시하거나, 설정을 바꾼 경우) 사용자의 Notion 데이터베이스 **"아침 경제 브리핑"**에 작업일지를 남깁니다.

| 항목 | 값 |
|---|---|
| 데이터베이스 | 아침 경제 브리핑 (사용자의 개인 페이지) |
| URL | https://app.notion.com/p/91b4fefbf0964625b7429c61d282e24b |
| 데이터 소스 | `collection://38d7ac18-71de-41df-816f-0defa99512b3` |

**페이지 작성 방법**
- 속성
  - `제목`: `[작업일지] YYYY-MM-DD 작업 요약 한 줄` (예: `[작업일지] 2026-10-26 AGENTS.md·CLAUDE.md 추가`)
  - `날짜`: 작업한 날 (KST)
  - `유형`: `작업일지` (앱이 자동으로 올리는 매일 브리핑은 `브리핑`. 이 값은 절대 쓰지 않습니다)
- 본문 구성
  1. **한 일**: 무엇을 왜 했는지
  2. **바뀐 파일**: 파일 이름과 바뀐 내용 한 줄씩
  3. **커밋**: 커밋 해시와 메시지 (커밋했다면)
  4. **결정한 것**: 사용자와 정한 방향, 선택한 이유
  5. **남은 일**: 다음에 할 일, 사용자가 직접 해야 하는 일
- 같은 날 같은 주제로 작업을 이어서 했다면 새 페이지를 만들지 말고 그날 작업일지에 내용을 덧붙입니다.
- 이 데이터베이스의 `브리핑` 페이지는 앱이 만든 결과물입니다. 사용자가 요청하지 않으면 고치거나 지우지 않습니다.
- Notion 도구를 쓸 수 없는 환경이라면, 사용자에게 그렇다고 알리고 위 형식대로 정리한 작업일지를 대화에 남겨서 사용자가 붙여넣을 수 있게 합니다.

## 코드 구조

| 파일 | 역할 |
|---|---|
| `main.py` | 실행 순서: 수집 → 요약 → `reports/` 저장 → Notion 게시 |
| `brief/market.py` | 시세 수집 (yfinance). 지표 추가는 `TICKERS`에 |
| `brief/news.py` | 뉴스 RSS 수집. 출처 추가는 `FEEDS`에 |
| `brief/report.py` | Claude 요약. 보고서 구성은 `SYSTEM_PROMPT` |
| `brief/notion.py` | 마크다운 → Notion 블록 변환, 페이지 생성 |
| `.github/workflows/daily.yml` | 자동 실행 예약 (cron은 UTC 기준) |

## 개발 규칙

- **Python 3.9 호환**: 사용자의 Mac은 Python 3.9입니다. 모든 모듈 맨 위(독스트링 다음)에 `from __future__ import annotations`를 둡니다. `match` 문처럼 3.10 이상에서만 되는 문법은 쓰지 않습니다. GitHub Actions는 3.12로 실행합니다.
- **숫자는 AI가 만들지 않는다**: 시세 숫자는 `market_markdown()`처럼 코드가 직접 씁니다. Claude에게는 제공한 숫자만 쓰도록 지시합니다.
- **일부가 실패해도 브리핑은 나온다**: 시세·뉴스 출처 하나가 실패하면 로그만 남기고 건너뜁니다. Claude 호출이 실패하면 `fallback_briefing()`으로 대체합니다.
- **Claude 모델**: `brief/report.py`의 `MODEL`(`claude-opus-5-5`). 사용자가 요청하지 않으면 바꾸지 않습니다.
- 주석과 로그 메시지는 기존 코드처럼 한국어로 짧게 씁니다.

## 실행과 테스트

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python main.py --no-notion   # API 키 없이도 동작 (원자료만 정리)
```

- 코드를 바꾸면 위 명령으로 실행해서 시세·뉴스 수집 건수와 `reports/` 결과를 확인합니다.
- 테스트로 생긴 `reports/` 파일은 커밋하지 말고 지웁니다. `reports/`는 GitHub Actions가 매일 커밋합니다.
- Claude 요약과 Notion 게시는 실제 키가 필요해서, GitHub Actions의 **Run workflow**로 확인합니다.

## 비밀 정보

- API 키·토큰(`ANTHROPIC_API_KEY`, `NOTION_TOKEN`, GitHub 토큰 등)은 절대 코드, 커밋, 문서, Notion에 적지 않습니다.
- 키는 GitHub Secrets에만 둡니다. 등록은 사용자가 직접 합니다. 에이전트가 대신 입력하지 않습니다.
- `NOTION_DATABASE_ID`는 비밀 정보가 아니지만, 다른 키와 같이 Secrets로 관리합니다.

## Git

- 기본 브랜치는 `main`이고, `main`에 바로 커밋·푸시합니다.
- 커밋과 푸시는 사용자가 요청했을 때만 합니다.
- 커밋 메시지는 한국어로, 첫 줄에 무엇을 했는지 요약합니다.
- 작성자 정보는 이 저장소에만 설정되어 있습니다(GitHub noreply 이메일). 바꾸지 않습니다.
- 푸시하기 전에 `git pull --rebase origin main`으로 Actions가 커밋한 `reports/`를 먼저 받아옵니다.
