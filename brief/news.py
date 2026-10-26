"""경제 뉴스 수집 (RSS)."""

from __future__ import annotations

import calendar
import re
import time
from dataclasses import dataclass
from html import unescape
from urllib.parse import quote

import feedparser

GOOGLE_NEWS_BANK = (
    "https://news.google.com/rss/search?q="
    + quote("은행 OR 한국은행 OR 기준금리 OR 금융위원회 when:1d")
    + "&hl=ko&gl=KR&ceid=KR:ko"
)

# (출처 이름, RSS 주소, 최대 기사 수)
FEEDS = [
    ("연합뉴스 경제", "https://www.yna.co.kr/rss/economy.xml", 15),
    ("한국경제 경제", "https://www.hankyung.com/feed/economy", 10),
    ("한국경제 금융", "https://www.hankyung.com/feed/finance", 10),
    ("매일경제 경제", "https://www.mk.co.kr/rss/30100041/", 10),
    ("구글뉴스 은행·금리", GOOGLE_NEWS_BANK, 15),
    ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html", 10),
    ("CNBC Markets", "https://www.cnbc.com/id/20910258/device/rss/rss.html", 10),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories", 10),
]

MAX_AGE_HOURS = 24


@dataclass
class Article:
    source: str
    title: str
    link: str
    summary: str


def _published_ts(entry) -> float | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return calendar.timegm(parsed) if parsed else None


def fetch_news() -> list[Article]:
    cutoff = time.time() - MAX_AGE_HOURS * 3600
    seen_titles = set()
    articles = []
    for source, url, limit in FEEDS:
        try:
            feed = feedparser.parse(url, agent="Mozilla/5.0 (morning-brief)")
        except Exception as e:
            print(f"[news] {source} 실패: {e}")
            continue
        count = 0
        for entry in feed.entries:
            if count >= limit:
                break
            ts = _published_ts(entry)
            if ts is not None and ts < cutoff:
                continue
            title = entry.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            summary = _strip_tags(entry.get("summary", ""))[:300]
            articles.append(Article(source, title, entry.get("link", ""), summary))
            count += 1
        print(f"[news] {source}: {count}건")
    return articles


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(text)).strip()
