from __future__ import annotations

from dataclasses import replace

from apscheduler.schedulers.blocking import BlockingScheduler

from morning_brief import worker


def test_시작하면_다음_실행_시각을_알리고_예약을_건다(monkeypatch, settings, capsys):
    started = []
    monkeypatch.setattr(worker, "get_settings", lambda: replace(settings, brief_cron="30 7 * * mon-fri"))
    monkeypatch.setattr(worker, "get_db", lambda: None)
    monkeypatch.setattr(BlockingScheduler, "start", lambda self: started.append(self.get_jobs()))

    worker.main()

    assert len(started) == 1 and [job.id for job in started[0]] == ["morning-brief"]
    out = capsys.readouterr().out
    assert "예약: '30 7 * * mon-fri' (KST)" in out
    assert "다음 실행: " in out and "07:30:00+09:00" in out
