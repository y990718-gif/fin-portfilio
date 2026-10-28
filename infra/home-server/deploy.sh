#!/usr/bin/env bash
# 홈서버 배포: origin/main 의 최신 커밋으로 맞추고 의존성 설치·웹 빌드 후 서비스를 재시작한다.
# 컨테이너 안에서 root 로 실행한다: GitHub Actions(배포 워크플로)가 sudo 래퍼로 부르거나, 직접
# `bash /opt/morning-brief/infra/home-server/deploy.sh`.
#
# git checkout 이 실행 중인 이 파일을 바꿀 수 있으므로, 본문 전체를 main() 에 넣고 끝에서 exit 한다.
# bash 는 함수 정의를 끝까지 읽은 뒤에 실행하므로 도중에 파일이 바뀌어도 영향을 받지 않는다.
set -euo pipefail

main() {
  local app_dir=/opt/morning-brief
  local app_user=morning-brief
  # 서비스 사용자도 읽을 수 있는 곳에 uv 가 Python 을 설치하게 한다
  local python_dir=/opt/morning-brief-python

  # COREPACK_ENABLE_DOWNLOAD_PROMPT=0: packageManager 의 pnpm 버전이 바뀌어도 비대화형 배포에서 묻지 않고 받는다
  as_app() {
    sudo -u "$app_user" -H env UV_PYTHON_INSTALL_DIR="$python_dir" COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
      PATH="/usr/local/bin:/usr/bin:/bin" "$@"
  }

  echo "[deploy] main 최신 커밋 받기"
  as_app git -C "$app_dir" fetch --quiet origin main
  as_app git -C "$app_dir" checkout --quiet --detach origin/main
  echo "[deploy] 배포 커밋: $(as_app git -C "$app_dir" log --oneline -1)"

  echo "[deploy] API 의존성 설치"
  as_app uv --directory "$app_dir/apps/api" sync --locked --no-dev

  echo "[deploy] 웹 빌드"
  as_app pnpm --dir "$app_dir" install --frozen-lockfile
  as_app pnpm --dir "$app_dir" build:web

  echo "[deploy] 서비스 재시작"
  systemctl restart morning-brief-api morning-brief-worker

  local healthy=false
  for _ in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8000/api/health >/dev/null; then
      healthy=true
      break
    fi
    sleep 1
  done
  if [ "$healthy" != true ]; then
    echo "[deploy] API 가 30초 안에 응답하지 않습니다: journalctl -u morning-brief-api -n 50" >&2
    return 1
  fi
  if ! systemctl is-active --quiet morning-brief-worker; then
    echo "[deploy] 워커가 실행 중이 아닙니다: journalctl -u morning-brief-worker -n 50" >&2
    return 1
  fi
  echo "[deploy] 완료: API 응답과 워커 실행 확인"
  journalctl -u morning-brief-worker -n 3 --no-pager || true
}

main "$@"
exit
