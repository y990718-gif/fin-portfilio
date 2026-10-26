"""브리핑 생성 예약(BRIEF_CRON) 해석.

crontab 과 APScheduler 는 요일 숫자가 다르다(crontab 1=월, APScheduler 1=화). 숫자로 적으면
하루씩 밀린 요일에 돌기 때문에 요일은 mon-fri 처럼 영문 약어만 받는다.
"""

from __future__ import annotations

import re

from apscheduler.triggers.cron import CronTrigger

from .config import KST


def parse_cron(expr: str) -> CronTrigger:
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"BRIEF_CRON 은 '분 시 일 월 요일' 다섯 칸이어야 합니다: {expr!r}")
    if re.search(r"\d", fields[4]):
        raise ValueError(f"BRIEF_CRON 의 요일은 mon-fri 처럼 영문 약어로 적으세요: {expr!r}")
    return CronTrigger.from_crontab(expr, timezone=KST)
