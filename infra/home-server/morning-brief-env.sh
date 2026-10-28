#!/usr/bin/env bash
# app.env 비밀값 입력 도우미. 값은 화면에 보이지 않고, 프로세스 인자로도 넘기지 않는다.
# 값은 작은따옴표로 감싸 저장한다: systemd EnvironmentFile 과 `set -a; . app.env` 둘 다 읽을 수 있게.
# 설치: install -m 700 -o root -g root morning-brief-env.sh /usr/local/sbin/morning-brief-env
set -euo pipefail
ENV_FILE=/etc/morning-brief/app.env
[ "$(id -u)" = 0 ] || { echo "root 로 실행하세요"; exit 1; }

changed=0
set_kv() {  # 임시 파일에 쓰고 권한을 맞춘 뒤 한 번에 바꾼다. 값은 환경변수로 넘긴다
  K="$1" V="$2" F="$ENV_FILE" python3 - <<'PY'
import grp, os, pathlib, re
os.umask(0o077)  # 임시 파일이 잠깐이라도 다른 사용자에게 읽히지 않게 처음부터 600 으로 만든다
k, v, p = os.environ["K"], os.environ["V"], pathlib.Path(os.environ["F"])
s = p.read_text()
line = f"{k}='{v}'"
s, n = re.subn(rf"^{re.escape(k)}=.*$", lambda m: line, s, flags=re.M)
if n == 0:
    s = s.rstrip("\n") + f"\n{line}\n"
tmp = p.with_name(p.name + ".tmp")
tmp.write_text(s)
os.chown(tmp, 0, grp.getgrnam("morning-brief").gr_gid)
os.chmod(tmp, 0o640)
os.replace(tmp, p)
PY
}
ask() {  # $1=키 $2=설명 $3=모양(정규식) $4=숨김(1/0)
  local v
  while :; do
    if [ "$4" = 1 ]; then read -rsp "$1 — $2 (입력이 보이지 않음, 엔터만 치면 그대로): " v; echo
    else read -rp "$1 — $2 (엔터만 치면 그대로): " v; fi
    [ -z "$v" ] && { echo "  · 그대로 둠"; return; }
    [[ "$v" =~ $3 && "$v" != *"'"* ]] && break
    echo "  ✗ 모양이 다릅니다. 다시 입력하세요."
  done
  set_kv "$1" "$v"; changed=1; echo "  ✓ 저장"
}

echo "== /etc/morning-brief/app.env 비밀값 입력"
ask MONGODB_URI    "Atlas 서버 전용 사용자 연결 문자열 (mongodb+srv://...)" '^mongodb(\+srv)?://[^<>[:space:]]+$' 1
ask OPENAI_API_KEY "OpenAI 서버 전용 키 (sk-...)"                        '^sk-[^[:space:]]+$'                  1
ask VAPID_SUBJECT  "알림 담당 연락처 (mailto:이메일)"                      '^(mailto:[^[:space:]@]+@[^[:space:]]+|https://[^[:space:]]+)$' 0

[ "$changed" = 1 ] || { echo "바뀐 값이 없어 재시작하지 않습니다."; exit 0; }
echo "== 서비스 재시작"
systemctl restart morning-brief-api morning-brief-worker
sleep 8
code=$(curl -s -o /dev/null -m 5 -w "%{http_code}" http://127.0.0.1:8000/api/health || true)
if [ "$code" = 200 ]; then echo "API 상태 확인: $code 정상"; else echo "API 상태 확인: $code 확인 필요"; fi
echo "워커: $(systemctl is-active morning-brief-worker)"
if [ "$code" != 200 ] || ! systemctl is-active --quiet morning-brief-worker; then
  echo "== 최근 로그"; journalctl -u morning-brief-api -u morning-brief-worker -n 15 --no-pager -o cat | cut -c1-200
fi
