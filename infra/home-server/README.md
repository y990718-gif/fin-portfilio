# 홈서버 운영

친구(김영웅)가 직접 운영해 보는 서버다. 가원의 홈서버 안 **LXD 컨테이너 `fin-brief`** 하나에 앱 전체가
들어 있고, 친구는 이 컨테이너 안에서 root 다. 호스트·Tailscale·컨테이너 생성은 가원이 관리한다.

| 컨테이너 안에서 도는 것 | 하는 일 |
|---|---|
| `morning-brief-api` (systemd) | FastAPI. `/api/*` 와 빌드된 웹 화면을 `127.0.0.1:8000` 에서 서빙 |
| `morning-brief-worker` (systemd) | `BRIEF_CRON`(기본 평일 07:30 KST)에 브리핑을 만들고 알림을 보냄 |
| GitHub Actions 러너 (`github-runner` 사용자, 라벨 `fin-brief`) | `main` 에 머지되면 `deploy.sh` 실행 |

```
아이폰 ──HTTPS──> https://gawon-dev.tail7c7524.ts.net:10000   (호스트의 Tailscale Funnel)
                   └─> 호스트 127.0.0.1:8100 ──LXD proxy──> 컨테이너 127.0.0.1:8000 (api)

컨테이너 ──인터넷만──> MongoDB Atlas · OpenAI · 시세·뉴스 · Apple 푸시
          (집 LAN·호스트·tailnet 으로는 나갈 수 없다)
```

## 접속

가원이 공유한 Tailscale 기기로 컨테이너에 ssh 로 들어간다. 접속 정보는 가원이 따로 알려 준다.
들어가면 root 이므로 아래 명령에 `sudo` 가 필요 없다.

## 처음 한 번 (컨테이너 안)

### 1. 도구 설치

```bash
apt-get update && apt-get install -y git curl ca-certificates sudo
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh   # uv
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs  # Node 22
corepack enable                                                                          # pnpm
```

### 2. 서비스 사용자와 코드

```bash
useradd --system --create-home --home-dir /var/lib/morning-brief --shell /usr/sbin/nologin morning-brief
mkdir -p /opt/morning-brief /opt/morning-brief-python
chown morning-brief:morning-brief /opt/morning-brief /opt/morning-brief-python
sudo -u morning-brief git clone https://github.com/y990718-gif/fin-portfilio.git /opt/morning-brief
```

### 3. 환경 파일

항목은 저장소 루트의 `.env.example` 과 같다.

```bash
mkdir -p /etc/morning-brief
cp /opt/morning-brief/.env.example /etc/morning-brief/app.env
chown root:morning-brief /etc/morning-brief/app.env
chmod 640 /etc/morning-brief/app.env   # root 와 서비스 사용자만 읽는다. 러너 사용자는 못 읽는다
nano /etc/morning-brief/app.env
```

- `MONGODB_URI` 는 아래 4단계의 **서버 전용 사용자**로 만든다.
- `MONGODB_DB=morning_brief` (로컬 개발용 `morning_brief_dev` 와 나눈다)
- `OPENAI_API_KEY` 는 서버 전용 키로 발급하고 OpenAI 프로젝트에 월 사용 한도를 건다.
- `VAPID_*` 는 5단계에서 만든다. **한 번 정하면 바꾸지 않는다.** 바꾸면 모든 기기가 알림을 다시 켜야 한다.
- `WEB_DIST` 는 적지 않는다. 서비스 파일이 넣는데, env 파일에 빈 줄로라도 있으면 그 값이 이긴다.

### 4. MongoDB Atlas

- **Network Access** 는 `0.0.0.0/0`(어디서나 접속)으로 열려 있다(가원 설정). 집 공인 IP 가 바뀌어도
  끊기지 않게 하려는 것이다. 그래서 **DB 사용자 비밀번호가 유일한 방어선**이다.
- 서버 전용 사용자를 따로 만든다: Atlas → **Database & Network Access → Database Users →
  Add New Database User** → Password(자동 생성, 길게) → **Specific Privileges** → `readWrite` @ `morning_brief`.
- 클러스터를 만들 때 생긴 빠른 설정 사용자(Atlas Admin 권한)는 서버에 넣지 않는다.

### 5. 서비스 등록과 첫 배포

```bash
cp /opt/morning-brief/infra/home-server/morning-brief-*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable morning-brief-api morning-brief-worker
bash /opt/morning-brief/infra/home-server/deploy.sh

# 알림 키를 만들어 app.env 에 붙여 넣고 다시 시작
sudo -u morning-brief /opt/morning-brief/apps/api/.venv/bin/morning-brief vapid-keys
nano /etc/morning-brief/app.env
systemctl restart morning-brief-api morning-brief-worker
```

### 6. 자동 배포 러너

- 러너는 컨테이너 안 `github-runner` 사용자로 돌고 라벨은 `fin-brief` 다. 설치 절차는 가원이 안내한다.
- **등록 토큰은 레포 주인만 발급할 수 있다**: GitHub 레포 → Settings → Actions → Runners → New self-hosted runner.
- 러너에게 허용된 root 권한은 래퍼 하나뿐이다 (`/etc/sudoers.d/`):
  `github-runner ALL=(root) NOPASSWD: /usr/local/sbin/morning-brief-deploy`
  래퍼 내용은 `exec bash /opt/morning-brief/infra/home-server/deploy.sh` 한 줄이고 root 소유다.

### 7. 레포 주인이 꼭 할 보안 설정

GitHub 레포 → **Settings → Actions → General → Fork pull request workflows from outside collaborators**
→ **Require approval for all outside collaborators** 로 바꾼다.

공개 레포라 누구나 fork 로 PR 을 올릴 수 있고, PR 안에서 워크플로 파일을 고쳐 이 서버의 러너(`fin-brief`)를
지정할 수 있다. 승인 없이 돌면 모르는 사람의 코드가 집 회선에서 실행된다. **외부인 PR 의 "Approve and run"
요청이 오면 누르지 말고 가원에게 먼저 보여 준다.** 배포 워크플로(`deploy.yml`)에 `pull_request` 트리거를
넣지 않는 것도 같은 이유다.

## 평소 운영

```bash
# 배포: PR 이 main 에 머지되면 GitHub Actions "배포" 워크플로가 자동으로 한다.
#       다시 배포하려면 Actions → 배포 → Run workflow, 또는 컨테이너 안에서:
bash /opt/morning-brief/infra/home-server/deploy.sh

# 로그
journalctl -u morning-brief-worker -f        # 아침 생성 로그, 다음 실행 시각
journalctl -u morning-brief-api -n 100

# 지금 한 번 만들기 (알림까지 보냄. 알림 없이: run --no-push)
sudo -u morning-brief bash -c 'set -a; . /etc/morning-brief/app.env; set +a; \
  /opt/morning-brief/apps/api/.venv/bin/morning-brief run'
```

아이폰에서는 `https://gawon-dev.tail7c7524.ts.net:10000` 을 Safari 로 열어 홈 화면에 추가한다.

## 호스트 쪽 구성 (가원 관리)

| 항목 | 값 |
|---|---|
| 컨테이너 | LXD `fin-brief`, Ubuntu 24.04, CPU 2 / RAM 2GiB / 디스크 20GiB |
| 컨테이너 망 | `10.200.0.0/24`. 집 LAN·호스트·tailnet 차단, 인터넷만 허용 |
| 포트 연결 | LXD proxy: 호스트 `127.0.0.1:8100` ↔ 컨테이너 `127.0.0.1:8000` |
| 공개 주소 | Tailscale Funnel `:10000` → `127.0.0.1:8100` |

컨테이너를 만드는 절차는 이 절에 이어서 적는다.
