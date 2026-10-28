# AGENTS.md

이 저장소에서 작업하는 AI 코딩 에이전트(Claude Code, Codex 등)를 위한 안내서입니다.
도구별 진입 파일(`CLAUDE.md`)은 이 파일을 불러오기만 합니다. **규칙을 고칠 때는 이 파일을 고칩니다.**

## 프로젝트 개요

**아침 경제 브리핑**: 은행 취업을 준비하는 사용자를 위해 평일 아침마다 경제 뉴스·증시·환율을 모아
GPT(OpenAI)로 요약하고, MongoDB에 쌓아 아이폰 홈 화면 앱(PWA)으로 보여 주며 알림을 보내는 서비스입니다.
기획은 [PLAN.md](PLAN.md), 사용법은 [README.md](README.md)를 보세요.

- 저장소: https://github.com/y990718-gif/fin-portfilio (레포 이름의 철자는 `portfilio`가 맞습니다)
- 구조: 모노레포. `apps/api`(Python·FastAPI) + `apps/web`(React PWA)
- 실행: 홈서버 LXD 컨테이너 `fin-brief`의 워커가 평일 07:30 KST(`BRIEF_CRON`)에 브리핑을 만들고 알림을 보냅니다
- 배포: `main`에 머지되면 GitHub Actions가 그 컨테이너에 자동으로 배포합니다 (`infra/home-server/`)
- 데이터: MongoDB Atlas `morning_brief` DB

## 사용자와 소통하기

- 사용자에게 하는 말과 문서는 **한국어**로 씁니다.
- 사용자는 개발 입문자입니다. 전문 용어는 쉽게 풀어서 설명하고, 사용자가 직접 해야 하는 일은 클릭할 위치까지 단계별로 안내합니다.
- 실행·검사 명령은 에이전트가 직접 돌리고 결과를 쉬운 말로 알려 줍니다.

## 역할 나누기

| 누가 | 맡는 일 |
|---|---|
| 사용자(김영웅) | 기획, 화면·문구, 뉴스 출처·지표·요약 항목 바꾸기, 서버 컨테이너 운영(배포·로그·env 값) |
| 개발 도우미(김가원) | 홈서버 호스트·컨테이너·Tailscale, DB 구조, CI·배포 워크플로 |

아래 [먼저 확인받을 것](#먼저-확인받을-것)에 해당하는 변경은 바로 하지 말고, 사용자에게 이유를 설명한 뒤
가원에게 확인받도록 안내합니다.

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

| 경로 | 역할 |
|---|---|
| `apps/api/src/morning_brief/collect/market.py` | 시세 수집 (yfinance). 지표 추가는 `TICKERS`에 |
| `apps/api/src/morning_brief/collect/news.py` | 뉴스 RSS 수집. 출처 추가는 `FEEDS`에 |
| `apps/api/src/morning_brief/summarize.py` | GPT 요약. 말투·규칙은 `SYSTEM_PROMPT`, 항목은 `BriefingDraft` |
| `apps/api/src/morning_brief/pipeline.py` | 한 번 실행: 수집 → 요약 → DB 저장 → 알림(·Notion) |
| `apps/api/src/morning_brief/store.py` · `db.py` | MongoDB 읽기·쓰기, 컬렉션과 인덱스 |
| `apps/api/src/morning_brief/api/routes.py` | 앱이 부르는 API (`/api/...`) |
| `apps/api/src/morning_brief/push.py` · `worker.py` | 아이폰 알림 발송, 평일 아침 예약 실행 |
| `apps/api/src/morning_brief/notion.py` | (선택) Notion 게시. `NOTION_*` 값이 있을 때만 |
| `apps/web/src/components/BriefingView.tsx` | 브리핑 화면의 카드 구성 |
| `apps/web/src/pages/` | 오늘 · 지난 브리핑 · 설정 화면 |
| `apps/web/src/styles.css` | 색·간격. 맨 위 변수만 바꾸면 전체에 반영 |
| `infra/home-server/` | 서버 컨테이너 설치·배포·운영 방법 |

### 브리핑에 항목을 추가할 때

1. `summarize.py`의 `BriefingDraft`에 필드를 추가합니다. `Field(description=...)`이 곧 GPT에게 주는 지시입니다.
2. `apps/web/src/lib/api.ts`의 `BriefingContent`에 같은 이름으로 추가합니다. **이미 쌓인 옛 브리핑에는 이 필드가 없으므로** `?`로 두고, 화면에서 없을 때를 처리합니다.
3. `BriefingView.tsx`에 카드를, `markdown.py`(Notion용)에 같은 내용을 추가합니다.
4. `apps/api/tests/test_summarize.py`의 `_draft()`에 값을 넣고 `pnpm check`로 검사합니다.

## 먼저 확인받을 것

- MongoDB 컬렉션·필드 **이름 바꾸기와 지우기**. 이미 쌓인 데이터와 앱이 어긋납니다. 필드 추가는 괜찮습니다.
- `push.py`의 허용 알림 주소 목록과 `store.py`의 기기 수 상한. 서버가 아무 주소로나 요청을 보내지 않게 막는 장치입니다.
- `infra/`, `.github/workflows/`, `.claude/settings.json`
- **`deploy.yml`에 `pull_request` 트리거를 넣는 것은 금지**입니다. 공개 레포라 fork PR 코드가 집 서버에서 돌게 됩니다. 외부인 PR의 워크플로 실행 승인 요청도 가원에게 먼저 보여 줍니다.
- 새 라이브러리 추가. 추가할 때는 `uv add`(apps/api) 또는 `pnpm --filter web add`로 하고 lock 파일을 같이 커밋합니다.
- GPT 모델(`OPENAI_MODEL`)이나 브리핑 시각(`BRIEF_CRON`) 변경. 서버 env 값(`/etc/morning-brief/app.env`)이라 바꾼 뒤 서비스를 다시 시작해야 합니다.

## 개발 규칙

- **숫자는 AI가 만들지 않는다**: 시세 표는 코드가 직접 그립니다(`QuoteBoard.tsx`, `markdown.quote_line`). GPT에게는 제공한 숫자만 쓰도록 지시합니다.
- **링크도 AI가 만들지 않는다**: GPT는 기사 번호(`article_id`)만 고르고, 코드가 실제 링크를 붙입니다(`summarize.attach_links`).
- **일부가 실패해도 브리핑은 나온다**: 시세·뉴스 출처 하나가 실패하면 건너뜁니다. GPT가 실패하면 `status: "fallback"`으로 시세와 헤드라인만 저장합니다.
- **Python은 uv가 따로 설치한다**: Mac 기본 Python(3.9)과 상관없습니다. `pip`·`python3`로 직접 설치하지 말고 `pnpm` 스크립트나 `uv`를 씁니다.
- 시각은 한국 시간(KST)입니다. `BRIEF_CRON`의 요일은 `mon-fri`처럼 영문으로 씁니다(숫자는 거부됩니다).
- 시세 등락 색은 한국 관례대로 상승 빨강, 하락 파랑입니다.
- 주석과 로그 메시지는 기존 코드처럼 한국어로 짧게 씁니다.

## 실행과 검사

처음 한 번: [uv](https://docs.astral.sh/uv/getting-started/installation/), Node 22, pnpm을 설치하고 `pnpm install`, `cp .env.example .env` 후 값을 채웁니다.

```bash
pnpm dev:api              # API     http://localhost:8000  (API 문서: /api/docs)
pnpm dev:web              # 앱 화면  http://localhost:5173
pnpm brief:run --no-push  # 브리핑 한 번 만들기
pnpm check                # 커밋 전에 반드시. CI와 같은 검사(포맷·린트·테스트·빌드)
```

- 화면을 바꾸면 `pnpm dev:api`와 `pnpm dev:web`을 띄우고 브라우저 폭을 아이폰(390px)으로 줄여서 확인합니다.
- `brief:run`은 GPT 요금이 들고 `.env`의 DB에 실제로 저장합니다. 로컬은 `MONGODB_DB=morning_brief_dev`로 서버 데이터와 나눕니다.
- 아이폰 알림은 HTTPS 서버에서만 동작합니다. 로컬에서는 화면만 확인합니다.

## 비밀 정보

- API 키·토큰(`OPENAI_API_KEY`, `MONGODB_URI`의 비밀번호, `VAPID_PRIVATE_KEY`, `NOTION_TOKEN`, GitHub 토큰 등)은 절대 코드, 커밋, 문서, Notion에 적지 않습니다.
- 로컬은 루트 `.env`(커밋되지 않음), 서버는 컨테이너의 `/etc/morning-brief/app.env`에만 둡니다.
- 에이전트는 `.env`를 읽거나 출력하지 않습니다. 값을 넣어야 하면 사용자에게 직접 넣는 방법을 안내합니다.

## Git

- **`main`에 머지되면 곧바로 홈서버에 배포됩니다.** 작업은 브랜치(`<type>/<이름>`, 예: `feat/bank-stocks`)에서 하고, PR의 CI가 초록일 때 `main`에 합칩니다. `main`에 바로 푸시하지 않습니다.
- 작업 전에 `git pull`로 최신 `main`을 받습니다.
- 커밋과 푸시는 사용자가 요청했을 때만 합니다.
- 커밋 메시지는 제목 한 줄 + 불릿입니다. 마지막 불릿은 검증입니다. `Co-Authored-By` 같은 도구 표시는 붙이지 않습니다.

```
<type>(<scope>): <한국어 개조식 제목 — …함/…음>

- 무엇을 바꿨는지 한 줄
- 검증: pnpm check 통과, 화면 확인
```

  `<type>`은 `feat` `fix` `refactor` `docs` `chore` `test` `ci`, `<scope>`는 `api` `web` `infra`처럼 바꾼 곳입니다.
- 작성자 정보(git user)는 각자 설정한 대로 두고 바꾸지 않습니다.
