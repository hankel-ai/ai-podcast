"""Claude Blog source - scrapes https://claude.com/blog"""

import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from .base import Story

logger = logging.getLogger(__name__)

CLUED_BLOG_URL = "https://claude.com/blog"


async def fetch_claude_blog(config: dict) -> list[Story]:
    """Fetch stories from the Claude blog."""
    max_stories = config.get("max_stories", 3)
    source_name = config.get("_source_name", "Claude Blog")

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(CLUED_BLOG_URL, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch Claude blog: {e}")
            return []

    soup = BeautifulSoup(resp.text, "html.parser")
    stories = []
    seen_urls = set()

    # Try multiple selectors to find article cards
    article_cards = (
        soup.select("article")
        or soup.select(".blog-post")
        or soup.select("[class*='blog']")
        or soup.select("[class*='post']")
        or soup.select("a[href*='/blog/']")
        or soup.select("main a")
        or soup.select("a")
    )

    logger.debug(f"Found {len(article_cards)} potential article elements")

    for element in article_cards[
        : max_stories * 3
    ]:  # Check extra to account for duplicates/non-articles
        if len(stories) >= max_stories:
            break

        # Try to find the link
        link_el = element if element.name == "a" else element.find("a")
        if not link_el:
            continue

        href = link_el.get("href", "")
        if not href:
            continue

        # Handle relative URLs
        if href.startswith("/"):
            href = f"https://claude.com{href}"
        elif not href.startswith("http"):
            href = f"https://claude.com/{href}"

        # Skip non-article links and duplicates
        if "/blog/" not in href or href in seen_urls:
            continue

        # Try to extract title
        title_el = element.find(["h1", "h2", "h3", "h4", "h5"]) or link_el
        title = title_el.get_text(strip=True) if title_el else ""

        if not title or len(title) < 5:
            # Try alternative: look for specific text structure
            title = link_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

        # Extract summary if available
        summary = ""
        p = element.find("p")
        if p:
            summary = p.get_text(strip=True)[:300]

        stories.append(
            Story(
                title=title,
                url=href,
                source_name=source_name,
                summary=summary,
                published=datetime.now(timezone.utc),  # Blog doesn't show dates in list
            )
        )

        seen_urls.add(href)
        logger.debug(f"Found Claude blog post: {title[:60]}...")

    logger.info(f"Claude blog: found {len(stories)} stories")
    return stories
