"""매일 아침 브리핑을 만드는 상주 프로세스. 시각은 BRIEF_CRON(한국 시간)을 따른다."""

from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import KST, get_settings
from .db import get_db
from .pipeline import run_once
from .schedule import parse_cron


def _job() -> None:
    try:
        run_once(get_settings(), get_db())
    except Exception as e:  # 오늘 실패해도 내일 예약은 살아 있어야 한다
        print(f"[worker] 브리핑 생성 실패: {e}")


def main() -> None:
    settings = get_settings()
    trigger = parse_cron(settings.brief_cron)
    scheduler = BlockingScheduler(timezone=KST)
    # 서버가 잠깐 꺼져 있다 켜져도 1시간 안이면 그날 것을 한 번만 만든다
    scheduler.add_job(
        _job, trigger, id="morning-brief", coalesce=True, max_instances=1, misfire_grace_time=3600
    )
    get_db()  # 시작할 때 DB 연결과 인덱스를 확인해 설정 오류를 바로 드러낸다
    # start() 전의 작업에는 next_run_time 이 아직 없으므로 트리거에서 직접 계산한다
    next_run = trigger.get_next_fire_time(None, datetime.now(KST))
    print(f"[worker] 예약: '{settings.brief_cron}' (KST). 다음 실행: {next_run}")
    scheduler.start()
