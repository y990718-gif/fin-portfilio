"""환경변수 설정. 로컬은 루트 .env, 서버는 infra/home-server 의 env 파일에서 들어온다.

값을 코드에 직접 적지 않는다. 새 설정이 필요하면 여기와 루트 .env.example 에 함께 추가한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or default


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongodb_db: str
    openai_api_key: str | None
    openai_model: str
    openai_reasoning_effort: str | None
    # 브리핑 생성 시각(한국 시간, crontab 형식). 요일은 mon-fri 처럼 영문 약어로 적는다.
    brief_cron: str
    vapid_public_key: str | None
    vapid_private_key: str | None
    vapid_subject: str | None
    notion_token: str | None
    notion_database_id: str | None
    # 빌드된 웹(apps/web/dist) 경로. 있으면 API 서버가 웹 화면도 함께 서빙한다.
    # 서버에서는 systemd 서비스 파일이 넣으므로 env 파일에는 적지 않는다 (infra/home-server).
    web_dist: str | None

    @property
    def push_enabled(self) -> bool:
        return bool(self.vapid_public_key and self.vapid_private_key and self.vapid_subject)

    @property
    def notion_enabled(self) -> bool:
        return bool(self.notion_token and self.notion_database_id)


def load_settings() -> Settings:
    return Settings(
        mongodb_uri=_env("MONGODB_URI", "mongodb://localhost:27017"),
        mongodb_db=_env("MONGODB_DB", "morning_brief"),
        openai_api_key=_env("OPENAI_API_KEY"),
        openai_model=_env("OPENAI_MODEL", "gpt-6.1-sol"),
        openai_reasoning_effort=_env("OPENAI_REASONING_EFFORT", "medium"),
        brief_cron=_env("BRIEF_CRON", "30 7 * * mon-fri"),
        vapid_public_key=_env("VAPID_PUBLIC_KEY"),
        vapid_private_key=_env("VAPID_PRIVATE_KEY"),
        vapid_subject=_env("VAPID_SUBJECT"),
        notion_token=_env("NOTION_TOKEN"),
        notion_database_id=_env("NOTION_DATABASE_ID"),
        web_dist=_env("WEB_DIST"),
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings()
