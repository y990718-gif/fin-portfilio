# 홈서버 운영

서버 관리자(가원)가 보는 문서다. Docker 없이 systemd 서비스 두 개로 돌린다.

| 서비스 | 하는 일 |
|---|---|
| `morning-brief-api` | FastAPI. `/api/*` 와 빌드된 웹 화면을 `127.0.0.1:8000` 에서 서빙 |
| `morning-brief-worker` | `BRIEF_CRON`(기본 평일 07:30 KST)에 브리핑을 만들고 알림을 보냄 |

```
아이폰 ──HTTPS──> 리버스 프록시(도메인) ──> 127.0.0.1:8000 (api)
                                           MongoDB Atlas <── worker (평일 아침)
```

## 처음 한 번

Linux(systemd) 서버 기준이다.

### 1. 도구 설치

```bash
# uv — 서비스 사용자도 쓰도록 /usr/local/bin 에 설치
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh
# Node 22 + pnpm (corepack)
#   배포판 방법대로 Node 22 를 설치한 뒤
sudo corepack enable
```

### 2. 서비스 사용자와 코드

```bash
sudo useradd --system --create-home --home-dir /var/lib/morning-brief --shell /usr/sbin/nologin morning-brief
sudo mkdir -p /opt/morning-brief /opt/morning-brief-python
sudo chown morning-brief:morning-brief /opt/morning-brief /opt/morning-brief-python
sudo -u morning-brief git clone https://github.com/y990718-gif/fin-portfilio.git /opt/morning-brief
```

### 3. 환경 파일

`/etc/morning-brief/app.env` 를 만든다. 항목은 저장소 루트의 `.env.example` 과 같다.

```bash
sudo mkdir -p /etc/morning-brief
sudo cp /opt/morning-brief/.env.example /etc/morning-brief/app.env
sudo chown root:morning-brief /etc/morning-brief/app.env
sudo chmod 640 /etc/morning-brief/app.env   # root 와 서비스 사용자만 읽는다
sudoedit /etc/morning-brief/app.env
```

- `MONGODB_DB=morning_brief` (로컬 개발용 `morning_brief_dev` 와 나눈다)
- `WEB_DIST` 는 적지 않는다. 서비스 파일이 넣는데, env 파일에 빈 줄로라도 있으면 그 값이 이긴다.
- `VAPID_*` 는 `sudo -u morning-brief /opt/morning-brief/apps/api/.venv/bin/morning-brief vapid-keys` 로 한 번 만든다 (4단계 이후). **바꾸면 모든 기기가 알림을 다시 켜야 한다.**
- `OPENAI_API_KEY` 는 이 서버 전용 키로 발급하고 OpenAI 프로젝트에 월 사용 한도를 건다.

### 4. 서비스 등록과 첫 배포

```bash
sudo cp /opt/morning-brief/infra/home-server/morning-brief-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable morning-brief-api morning-brief-worker
sudo bash /opt/morning-brief/infra/home-server/deploy.sh
```

### 5. MongoDB Atlas 접속 허용

- Atlas → **Database & Network Access → IP Access List** 에 홈서버 공인 IP 를 추가한다.
- 서버용 DB 사용자는 `morning_brief` DB 의 `readWrite` 만 주는 것을 따로 만든다.
  Atlas 빠른 설정이 만든 사용자는 Atlas Admin 권한이라 서버에 두지 않는다.

### 6. HTTPS 도메인 (아이폰 알림에 필수)

아이폰 웹 푸시는 HTTPS 주소로 연 홈 화면 앱에서만 동작한다. 이미 쓰는 리버스 프록시가 있으면
`127.0.0.1:8000` 으로 넘기기만 하면 된다. 없으면 Caddy 가 인증서까지 자동으로 처리한다.

```
# /etc/caddy/Caddyfile
brief.<도메인> {
    reverse_proxy 127.0.0.1:8000
}
```

공유기 포트를 열기 어렵다면 Cloudflare Tunnel 로 같은 주소를 `http://127.0.0.1:8000` 에 연결한다.

## 평소 운영

```bash
# main 에 머지된 코드 배포
sudo bash /opt/morning-brief/infra/home-server/deploy.sh

# 로그
journalctl -u morning-brief-worker -f        # 아침 생성 로그, 다음 실행 시각
journalctl -u morning-brief-api -n 100

# 지금 한 번 만들기 (알림까지 보냄. 알림 없이: run --no-push)
sudo -u morning-brief bash -c 'set -a; . /etc/morning-brief/app.env; set +a; \
  /opt/morning-brief/apps/api/.venv/bin/morning-brief run'
```
