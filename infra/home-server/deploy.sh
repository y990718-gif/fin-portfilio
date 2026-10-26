#!/usr/bin/env bash
# 홈서버 배포: origin/main 의 최신 커밋으로 맞추고 의존성 설치·웹 빌드 후 서비스를 재시작한다.
# 서버 관리자가 `sudo bash /opt/morning-brief/infra/home-server/deploy.sh` 로 실행한다.
set -euo pipefail

APP_DIR=/opt/morning-brief
APP_USER=morning-brief
# 서비스 사용자도 읽을 수 있는 곳에 uv 가 Python 을 설치하게 한다 (관리자 홈 아래면 서비스가 못 읽는다)
PYTHON_DIR=/opt/morning-brief-python

as_app() {
  sudo -u "$APP_USER" -H env UV_PYTHON_INSTALL_DIR="$PYTHON_DIR" PATH="/usr/local/bin:/usr/bin:/bin" "$@"
}

echo "[deploy] main 최신 커밋 받기"
as_app git -C "$APP_DIR" fetch --quiet origin main
as_app git -C "$APP_DIR" checkout --quiet --detach origin/main
echo "[deploy] 배포 커밋: $(as_app git -C "$APP_DIR" log --oneline -1)"

echo "[deploy] API 의존성 설치"
as_app uv --directory "$APP_DIR/apps/api" sync --locked --no-dev

echo "[deploy] 웹 빌드"
as_app pnpm --dir "$APP_DIR" install --frozen-lockfile
as_app pnpm --dir "$APP_DIR" build:web

echo "[deploy] 서비스 재시작"
systemctl restart morning-brief-api morning-brief-worker

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null; then
    echo "[deploy] 완료: API 응답 확인"
    systemctl --no-pager --lines=3 status morning-brief-worker | tail -3
    exit 0
  fi
  sleep 1
done
echo "[deploy] API 가 30초 안에 응답하지 않습니다: journalctl -u morning-brief-api -n 50" >&2
exit 1
