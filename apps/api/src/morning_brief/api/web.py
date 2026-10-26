"""빌드된 웹 화면(apps/web/dist)을 API 서버가 함께 서빙한다. 서버에 프로세스를 하나 덜 띄우기 위해서다."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

_NO_CACHE = {"Cache-Control": "no-cache"}
# Vite 가 파일 이름에 해시를 붙이므로 assets/ 아래는 오래 캐시해도 된다
_IMMUTABLE = {"Cache-Control": "public, max-age=31536000, immutable"}


def mount_web(app: FastAPI, dist: Path) -> None:
    root = dist.resolve()
    index = root / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404, "없는 API 경로입니다.")
        target = (root / path).resolve()
        if path and target.is_file() and target.is_relative_to(root):
            return FileResponse(target, headers=_IMMUTABLE if path.startswith("assets/") else _NO_CACHE)
        # 화면 주소(/briefings/2026-10-27 등)는 모두 index.html 이 받아 React 가 그린다
        return FileResponse(index, headers=_NO_CACHE)
