"""(선택) 브리핑 마크다운을 Notion 데이터베이스에 새 페이지로 저장.

NOTION_TOKEN·NOTION_DATABASE_ID 가 있을 때만 앱과 함께 Notion 에도 올린다.
"""

from __future__ import annotations

import os
import re

import requests

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_TEXT = 1900  # Notion rich_text 한 조각 최대 2000자
BLOCKS_PER_REQUEST = 100

INLINE = re.compile(r"\*\*(.+?)\*\*|\[([^\]]+)\]\((https?://[^)\s]+)\)")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _text(content: str, bold: bool = False, link: str | None = None) -> list[dict]:
    pieces = []
    for i in range(0, len(content), MAX_TEXT):
        item = {"type": "text", "text": {"content": content[i : i + MAX_TEXT]}}
        if link:
            item["text"]["link"] = {"url": link}
        if bold:
            item["annotations"] = {"bold": True}
        pieces.append(item)
    return pieces


def _rich_text(line: str) -> list[dict]:
    """**굵게** 와 [제목](링크) 만 지원하는 간단한 인라인 변환."""
    parts, pos = [], 0
    for m in INLINE.finditer(line):
        if m.start() > pos:
            parts += _text(line[pos : m.start()])
        if m.group(1):
            parts += _text(m.group(1), bold=True)
        else:
            parts += _text(m.group(2), link=m.group(3))
        pos = m.end()
    if pos < len(line):
        parts += _text(line[pos:])
    return parts


def _block(kind: str, line: str) -> dict:
    return {"object": "block", "type": kind, kind: {"rich_text": _rich_text(line)}}


def markdown_to_blocks(markdown: str) -> list[dict]:
    blocks = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("### "):
            blocks.append(_block("heading_3", line[4:]))
        elif line.startswith("## "):
            blocks.append(_block("heading_2", line[3:]))
        elif line.startswith("# "):
            blocks.append(_block("heading_1", line[2:]))
        elif line.startswith(("- ", "* ")):
            blocks.append(_block("bulleted_list_item", line[2:]))
        elif re.match(r"^\d+\.\s", line):
            blocks.append(_block("numbered_list_item", re.sub(r"^\d+\.\s", "", line)))
        elif line.startswith("> "):
            blocks.append(_block("quote", line[2:]))
        elif line in ("---", "***"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        else:
            blocks.append(_block("paragraph", line))
    return blocks


TYPE_PROP, TYPE_BRIEFING = "유형", "브리핑"  # 같은 DB의 '작업일지'와 구분


def _database_props(database_id: str) -> tuple[str, str | None, bool]:
    """제목 속성 이름, (있다면) 첫 번째 날짜 속성 이름, '유형' 선택 속성 유무."""
    r = requests.get(f"{API}/databases/{database_id}", headers=_headers(), timeout=30)
    r.raise_for_status()
    props = r.json()["properties"]
    title = next(name for name, p in props.items() if p["type"] == "title")
    date = next((name for name, p in props.items() if p["type"] == "date"), None)
    has_type = props.get(TYPE_PROP, {}).get("type") == "select"
    return title, date, has_type


def publish(title: str, date_iso: str, markdown: str) -> str:
    database_id = os.environ["NOTION_DATABASE_ID"]
    title_prop, date_prop, has_type = _database_props(database_id)
    properties = {title_prop: {"title": _text(title)}}
    if date_prop:
        properties[date_prop] = {"date": {"start": date_iso}}
    if has_type:
        properties[TYPE_PROP] = {"select": {"name": TYPE_BRIEFING}}

    blocks = markdown_to_blocks(markdown)
    r = requests.post(
        f"{API}/pages",
        headers=_headers(),
        json={
            "parent": {"database_id": database_id},
            "properties": properties,
            "children": blocks[:BLOCKS_PER_REQUEST],
        },
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"Notion 페이지 생성 실패: {r.status_code} {r.text}")
    page = r.json()

    # 블록이 100개를 넘으면 나머지는 이어 붙인다
    for i in range(BLOCKS_PER_REQUEST, len(blocks), BLOCKS_PER_REQUEST):
        r = requests.patch(
            f"{API}/blocks/{page['id']}/children",
            headers=_headers(),
            json={"children": blocks[i : i + BLOCKS_PER_REQUEST]},
            timeout=30,
        )
        if not r.ok:
            raise RuntimeError(f"Notion 블록 추가 실패: {r.status_code} {r.text}")
    return page.get("url", "")
