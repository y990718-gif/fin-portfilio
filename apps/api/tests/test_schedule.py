from __future__ import annotations

from datetime import datetime

import pytest

from morning_brief.config import KST
from morning_brief.schedule import parse_cron


def test_토요일에_보면_다음_실행은_월요일_7시30분이다():
    trigger = parse_cron("30 7 * * mon-fri")
    saturday = datetime(2026, 10, 31, 9, 0, tzinfo=KST)
    assert trigger.get_next_fire_time(None, saturday) == datetime(2026, 11, 2, 7, 30, tzinfo=KST)


@pytest.mark.parametrize("expr", ["30 7 * * 1-5", "30 7 * *", "30 7 * * 0"])
def test_요일_숫자나_칸수가_틀리면_거부한다(expr):
    with pytest.raises(ValueError):
        parse_cron(expr)
