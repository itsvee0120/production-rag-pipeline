import html
import os
import re
from typing import List

from dotenv import load_dotenv

from src.schemas import RetrievedChunk

load_dotenv()

MAX_RESULTS = 3
MAX_CHARS = 800

_TAGS = re.compile(r"<[^>]*>")
_DELIM = re.compile(r"</?\s*external_web_source[^>]*>?", re.IGNORECASE)
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def sanitize(text: str) -> str:
    """Untrusted web text -> plain text: strip HTML/delimiter look-alikes, control chars, extra whitespace; truncate."""
    text = html.unescape(text or "")
    text = _DELIM.sub("", text)
    text = _TAGS.sub("", text)
    text = _CTRL.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_CHARS]


def _tavily_key() -> str | None:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    return key if key and not key.startswith("your_") else None


def _search_tavily(query: str, key: str) -> List[dict]:
    from tavily import TavilyClient

    res = TavilyClient(api_key=key).search(query, max_results=MAX_RESULTS, timeout=15)
    return [
        {"url": r.get("url", ""), "title": r.get("title", ""), "body": r.get("content", ""), "score": r.get("score", 0.0)}
        for r in res.get("results", [])
    ]


def _search_ddg(query: str) -> List[dict]:
    from duckduckgo_search import DDGS

    return [
        {"url": r.get("href", ""), "title": r.get("title", ""), "body": r.get("body", ""), "score": 0.0}
        for r in DDGS().text(query, max_results=MAX_RESULTS) or []
    ]


def web_search(query: str) -> List[RetrievedChunk]:
    """Top web snippets as sanitized RetrievedChunks (chunk_id = URL). Tavily if a key is set, else DuckDuckGo. [] on failure."""
    key = _tavily_key()
    try:
        results = _search_tavily(query, key) if key else _search_ddg(query)
    except Exception:
        return []

    chunks = []
    for r in results:
        url = r["url"].strip()
        if not url.startswith(("http://", "https://")):
            continue
        content = sanitize(f"{r['title']}: {r['body']}")
        if content:
            score = min(max(float(r["score"] or 0.0), 0.0), 1.0)
            chunks.append(RetrievedChunk(chunk_id=url, content=content, score=score, source="web"))
    return chunks[:MAX_RESULTS]
