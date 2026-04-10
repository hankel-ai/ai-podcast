"""Fetch and extract clean article body text from URLs."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import httpx
import trafilatura

from sources.base import Story

logger = logging.getLogger(__name__)

_TIMEOUT = 15
_MAX_CONTENT_CHARS = 3000
_executor = ThreadPoolExecutor(max_workers=5)


def _extract_text(html: str) -> str:
    """Extract main article text from raw HTML using trafilatura."""
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    return text or ""


async def fetch_article_content(story: Story, client: httpx.AsyncClient) -> None:
    """Fetch a story's URL and populate its article_content field."""
    if story.article_content:
        return
    try:
        resp = await client.get(story.url, follow_redirects=True, timeout=_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(_executor, _extract_text, html)
        story.article_content = text[:_MAX_CONTENT_CHARS] if text else ""
        if text:
            logger.debug(f"Scraped {len(story.article_content)} chars from {story.url}")
    except Exception as e:
        logger.debug(f"Content scrape failed for {story.url}: {e}")


async def enrich_stories(stories: list[Story]) -> None:
    """Fetch article content for all stories concurrently."""
    if not stories:
        return
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [fetch_article_content(s, client) for s in stories]
        await asyncio.gather(*tasks, return_exceptions=True)
    scraped = sum(1 for s in stories if s.article_content)
    logger.info(f"Article content scraped: {scraped}/{len(stories)} stories")
