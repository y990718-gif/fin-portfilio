# 아침 경제 브리핑 (Morning Brief)

은행 취업 준비를 위해 매일 아침 **경제 뉴스 · 증시 · 환율**을 모아서, 출근길 5분 안에 읽을 수 있는 보고서를 Notion에 자동으로 올려 주는 프로그램입니다.

평일 오전 8시 30분(KST)에 GitHub 서버에서 자동으로 실행되므로, 9시 전에 Notion에서 바로 읽을 수 있습니다. 내 컴퓨터는 꺼 둬도 됩니다.

## 동작 방식

```
[시세 수집]  yfinance ─ 코스피·코스닥·S&P500·나스닥·다우·닛케이·상하이
                       원/달러·원/100엔·원/유로·원/위안·달러인덱스
                       미 국채 10년·WTI·금
[뉴스 수집]  RSS ───── 연합뉴스·한국경제·매일경제·구글뉴스(은행/금리)·CNBC·MarketWatch
      │
      ▼
[요약]  Claude API ── 3줄 요약 / 증시 / 환율 / 금리 / 뉴스 5선(은행원 관점) /
                      금융권 이슈 / 오늘의 경제 용어 / 면접 대비 질문
      │
      ▼
[저장]  reports/YYYY-MM-DD.md  +  Notion 데이터베이스 새 페이지
```

- 시세 숫자는 AI를 거치지 않고 코드가 직접 표에 넣습니다. AI가 숫자를 잘못 만들어 낼 걱정이 없습니다.
- 보고서 맨 아래에는 **"오늘 내 생각 한 줄"** 칸이 비어 있습니다. 매일 직접 한 줄씩 적어 보세요.

## 파일 구조

| 파일 | 역할 |
|---|---|
| `main.py` | 전체 실행 순서 (수집 → 요약 → 저장 → Notion) |
| `brief/market.py` | 증시·환율·금리·원자재 시세 수집 |
| `brief/news.py` | 경제 뉴스 RSS 수집 (최근 24시간) |
| `brief/report.py` | Claude에게 보내는 지시문과 보고서 작성 |
| `brief/notion.py` | 보고서를 Notion 페이지로 변환해 업로드 |
| `.github/workflows/daily.yml` | 평일 아침 자동 실행 예약 |

## 설치 (처음 한 번만)

### 1. Anthropic API 키 발급
1. https://console.anthropic.com 에 가입하고 결제 수단을 등록합니다.
2. **API Keys → Create Key**로 키를 만들어 복사해 둡니다. (`sk-ant-...`)
3. 하루 한 번 요약이면 비용은 하루 수십 원 정도입니다.

### 2. Notion 연결
1. https://www.notion.so/profile/integrations 에서 **새 API 통합(Internal)**을 만들고, **내부 통합 시크릿**을 복사합니다. (`ntn_...`)
2. Notion에 새 **데이터베이스(표)**를 만듭니다. 이름은 예를 들어 "아침 경제 브리핑"으로 합니다.
   - 기본 제목 열은 그대로 두고, **날짜** 속성을 하나 추가하면 날짜순 정렬이 됩니다. 날짜 속성은 없어도 동작합니다.
3. 데이터베이스 오른쪽 위 **••• → 연결(Connections)**에서 방금 만든 통합을 추가합니다. ← 이걸 빠뜨리면 404 오류가 납니다.
4. 데이터베이스 주소에서 ID를 복사합니다.
   `https://www.notion.so/xxxx/`**`1a2b3c4d5e6f...`**`?v=...` 에서 `?v=` 앞의 32자리입니다.

### 3. GitHub에 올리기
1. GitHub에서 새 저장소를 만들고 이 폴더의 파일을 모두 올립니다. (비공개(Private) 저장소도 괜찮습니다.)
2. 저장소의 **Settings → Secrets and variables → Actions → New repository secret**에 아래 3개를 등록합니다.

| 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | 1단계의 API 키 |
| `NOTION_TOKEN` | 2단계의 통합 시크릿 |
| `NOTION_DATABASE_ID` | 2단계의 데이터베이스 ID |

3. **Actions** 탭 → **아침 경제 브리핑** → **Run workflow**를 눌러 바로 한 번 실행해 봅니다. 1~2분 뒤 Notion에 페이지가 생기면 완료입니다.

이후로는 평일 매일 아침 자동으로 실행됩니다.

## 내 컴퓨터에서 실행해 보기 (선택)

Python 3.9 이상이 필요합니다.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python main.py --no-notion   # reports/ 폴더에만 저장
```

## 바꾸고 싶을 때

- **실행 시간**: `.github/workflows/daily.yml`의 `cron` 값. UTC 기준이므로 한국 시간에서 9시간을 뺍니다. 예를 들어 시드니(AEDT, UTC+11)에서 아침 8시 30분에 받으려면 `30 21 * * 0-4`로 바꿉니다.
- **보고 싶은 지표 추가**: `brief/market.py`의 `TICKERS`에 야후 파이낸스 티커를 추가합니다. 예: 삼성전자 `005930.KS`, KB금융 `105560.KS`.
- **뉴스 출처 추가**: `brief/news.py`의 `FEEDS`에 RSS 주소를 추가합니다.
- **보고서 구성**: `brief/report.py`의 `SYSTEM_PROMPT`를 고칩니다.

## 참고

- 시세는 Yahoo Finance 기준이며, 은행 고시 환율(매매기준율)과는 조금 다를 수 있습니다.
- GitHub 예약 실행은 서버 사정에 따라 10~30분 늦어질 수 있습니다. 그래서 9시보다 30분 이르게 예약해 두었습니다.
