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

컨테이너는 가원의 tailnet 이 아니라 **친구 본인의 tailnet** 에 등록한다. 가원 쪽 기기(포트폴리오·관리 패널·Mac)와
완전히 분리되고, 친구는 SSH 키 없이 Tailscale SSH 로 들어간다.

1. 친구: https://tailscale.com/download 에서 앱을 설치하고 본인 계정으로 가입·로그인한다 (Connected 확인).
2. 가원(Mac): `ssh homeserver lxc exec fin-brief -- tailscale up --ssh --hostname=fin-brief`
   → 나오는 `https://login.tailscale.com/a/…` 링크를 친구에게만 보낸다. 먼저 연 사람 계정에 붙는다.
3. 친구: 링크를 열어 본인 계정으로 로그인 → Connect. 가원 터미널에 Success 가 뜨면 끝.
4. 친구: https://login.tailscale.com/admin/machines → `fin-brief` → **Disable key expiry** (안 하면 180일 뒤 끊긴다).
5. 접속: `ssh root@fin-brief`. 처음엔 `yes`, "Tailscale SSH requires an additional check" 가 나오면 링크로 로그인한다.
   이름을 못 찾으면 Tailscale 앱에 보이는 `100.x` 주소로 접속한다.

들어가면 root 이므로 아래 명령에 `sudo` 가 필요 없다.

## 처음 한 번 (컨테이너 안)

### 1. 도구 설치

```bash
apt-get update && apt-get install -y git curl ca-certificates sudo
curl -LsSf https://astral.sh/uv/0.9.26/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh   # uv (CI 와 같은 버전)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs  # Node 22
corepack enable                                                                          # pnpm
curl -fsSL https://tailscale.com/install.sh | sh                                         # Tailscale (접속용)
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

# 비밀값 입력 도우미 설치 (한 번)
install -m 700 -o root -g root /opt/morning-brief/infra/home-server/morning-brief-env.sh /usr/local/sbin/morning-brief-env
```

- **비밀값(`MONGODB_URI`, `OPENAI_API_KEY`, `VAPID_SUBJECT`)은 5단계에서 서비스를 등록한 뒤 `morning-brief-env` 로 넣는다.**
  입력이 화면에 보이지 않고, 모양을 검사한 뒤 작은따옴표로 감싸 저장하고, 서비스를 재시작해 상태까지 보여 준다. 엔터만 치면 기존 값을 둔다.
  가원은 Mac 에서 `ssh -t homeserver lxc exec fin-brief -- morning-brief-env` 로도 실행할 수 있다.
- 그 밖의 값(`MONGODB_DB`, `BRIEF_CRON`, `OPENAI_MODEL` 등)은 `nano /etc/morning-brief/app.env` 로 고친다.
  공백이나 `&` 가 든 값은 작은따옴표로 감싼다(`BRIEF_CRON='30 7 * * mon-fri'`).
- `MONGODB_URI` 는 아래 4단계의 **서버 전용 사용자**로 만든다.
- `MONGODB_DB=morning_brief` (로컬 개발용 `morning_brief_dev` 와 나눈다)
- `OPENAI_API_KEY` 는 서버 전용 키로 발급하고 OpenAI 프로젝트에 월 사용 한도를 건다.
- `VAPID_PUBLIC_KEY`·`VAPID_PRIVATE_KEY` 는 5단계에서 만든다. **한 번 정하면 바꾸지 않는다.** 바꾸면 모든 기기가 알림을 다시 켜야 한다.
- `WEB_DIST` 는 적지 않는다. 서비스 파일이 넣는데, env 파일에 빈 줄로라도 있으면 그 값이 이긴다.

### 4. MongoDB Atlas

- **Network Access** 는 `0.0.0.0/0`(어디서나 접속)으로 열려 있다(가원 설정). 집 공인 IP 가 바뀌어도
  끊기지 않게 하려는 것이다. 그래서 **DB 사용자 비밀번호가 유일한 방어선**이다.
- 서버 전용 사용자를 따로 만든다: Atlas → **Database & Network Access → Database Users →
  Add New Database User** → Password(자동 생성, 길게) → **Specific Privileges** → `readWrite` @ `morning_brief`.
- 클러스터를 만들 때 생긴 빠른 설정 사용자(Atlas Admin 권한)는 서버에 넣지 않는다.
- 새 사용자의 연결 문자열은 `morning-brief-env` 로 넣는다.

### 5. 서비스 등록과 첫 배포

```bash
cp /opt/morning-brief/infra/home-server/morning-brief-*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable morning-brief-api morning-brief-worker
bash /opt/morning-brief/infra/home-server/deploy.sh

# 알림 키를 만들어 app.env 에 붙여 넣기
sudo -u morning-brief /opt/morning-brief/apps/api/.venv/bin/morning-brief vapid-keys
nano /etc/morning-brief/app.env

# 비밀값 입력 → 서비스 재시작 → API·워커 상태 확인까지 한 번에
morning-brief-env
```

### 6. 자동 배포 러너

- 러너는 컨테이너 안 `github-runner` 사용자로 돌고 라벨은 `fin-brief` 다. 프로그램(2.338.1)은 `/opt/actions-runner` 에
  설치돼 있고 등록만 하면 된다.
- **등록 토큰은 레포 주인만 발급할 수 있다**: GitHub 레포 → Settings → Actions → Runners → New self-hosted runner
  → Linux, x64. Download 절은 건너뛰고 Configure 절의 `--token` 값만 복사한다(1시간 유효).

```bash
cd /opt/actions-runner
sudo -u github-runner ./config.sh --unattended --url https://github.com/y990718-gif/fin-portfilio \
  --token <복사한 토큰> --name fin-brief --labels fin-brief
./svc.sh install github-runner
./svc.sh start
./svc.sh status        # active (running)
```

  Runners 화면에 `fin-brief` 가 초록 Idle 로 보이면 등록된 것이다. 친구가 접속하기 어려우면 토큰을 1시간 안에 가원에게
  1:1 로 보내 가원이 `ssh homeserver lxc exec fin-brief -- …` 로 같은 명령을 실행한다.
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

### 컨테이너 만들기 (호스트, sudo)

1. LXD 초기화 (`lxd init --preseed`): `lxdbr0` 는 `ipv4.address=10.200.0.1/24`, `ipv4.nat=true`, `ipv6.address=none`.
   저장소 `default` 는 btrfs 30GiB, default 프로필은 root + eth0.
2. 망 ACL `fin-brief` — 사설망·tailnet·호스트를 막고 인터넷만 연다:

   ```bash
   lxc network acl create fin-brief
   lxc network acl rule add fin-brief egress action=reject destination=192.168.0.0/16,172.16.0.0/12,100.64.0.0/10,169.254.0.0/16,224.0.0.0/4
   lxc network acl rule add fin-brief egress action=reject destination=10.0.0.0/9,10.128.0.0/10,10.192.0.0/13,10.201.0.0/16,10.202.0.0/15,10.204.0.0/14,10.208.0.0/12,10.224.0.0/11
   lxc network acl rule add fin-brief egress action=reject protocol=tcp destination=10.200.0.1/32 destination_port=1-52,54-65535
   lxc network acl rule add fin-brief egress action=reject protocol=udp destination=10.200.0.1/32 destination_port=1-52,54-66,68-65535
   lxc network acl rule add fin-brief egress action=allow
   lxc network acl rule add fin-brief ingress action=allow protocol=udp source=10.200.0.1/32 source_port=67 destination_port=68   # DHCP 응답
   lxc network set lxdbr0 security.acls=fin-brief
   ```

3. 호스트 UFW (INPUT·FORWARD 기본 DROP):

   ```bash
   sudo ufw allow in on lxdbr0 to any port 67 proto udp
   sudo ufw allow in on lxdbr0 to 10.200.0.1 port 53
   sudo ufw route allow in on lxdbr0 out on enp0s31f6
   sudo ufw route allow in on lxdbr0 out on wlp0s20f3
   ```

4. 컨테이너:

   ```bash
   lxc init ubuntu:24.04 fin-brief -c limits.cpu=2 -c limits.memory=2GiB -c limits.memory.enforce=hard \
     -c limits.processes=4096 -c boot.autostart=true -c security.idmap.isolated=true -d root,size=20GiB
   lxc config device override fin-brief eth0 ipv4.address=10.200.0.10
   lxc config device add fin-brief web proxy listen=tcp:127.0.0.1:8100 connect=tcp:127.0.0.1:8000 bind=host
   lxc config device add fin-brief tun unix-char source=/dev/net/tun path=/dev/net/tun   # 컨테이너 안 Tailscale 용
   lxc start fin-brief
   ```

5. 공개 주소: `tailscale funnel --bg --https=10000 http://127.0.0.1:8100`
6. 컨테이너 안에서 위 "처음 한 번" 1~6단계를 진행하고, 시간대는 `Asia/Seoul` 로 둔다.

차단 확인(2026-10-26): 컨테이너에서 공유기·호스트 LAN IP:22·`10.200.0.1:22/8090`·tailnet 관리 패널·도커 망으로는
연결되지 않고, OpenAI·Atlas·Yahoo·Apple 푸시는 응답한다.

되돌리기: `tailscale funnel --https=10000 off` → `lxc delete -f fin-brief` → `lxc network unset lxdbr0 security.acls`
→ `lxc network acl delete fin-brief` → `sudo ufw status numbered` 로 위 규칙을 찾아 지운다.

### main 첫 머지 순서

1. 컨테이너 `app.env` 에 `MONGODB_URI`(서버 전용 사용자), `OPENAI_API_KEY`, `VAPID_SUBJECT` 를 채운다.
2. `systemctl restart morning-brief-api morning-brief-worker` → `curl -fsS 127.0.0.1:8000/api/health` 와 워커 active 확인.
3. 러너 등록(6단계) → PR 머지 → Actions "배포" 성공 확인.

`deploy.sh` 가 워커 실행 여부까지 검사하므로 env 를 먼저 채워야 첫 자동 배포가 성공한다.
