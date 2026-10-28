"""FastAPI 앱. 실행: `uvicorn morning_brief.api:app` (로컬은 `pnpm dev:api`)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from ..config import Settings, get_settings
from .routes import router
from .web import mount_web


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="아침 경제 브리핑 API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.include_router(router)
    if settings.web_dist and (Path(settings.web_dist) / "index.html").is_file():
        mount_web(app, Path(settings.web_dist))
    return app


app = create_app()
