import asyncio
import logging

from sources.base import Story
from sources.hackernews import fetch_hackernews
from sources.techmeme import fetch_techmeme
from sources.implicator import fetch_implicator
from sources.claude_blog import fetch_claude_blog
from sources.rss_generic import fetch_rss
from sources.reddit import fetch_reddit
from utils.dedup import deduplicate
from utils.tracker import filter_already_used, record_used_stories

logger = logging.getLogger(__name__)

FETCHERS = {
    "hackernews_api": fetch_hackernews,
    "html_scraper": None,  # dispatched by source name
    "rss": fetch_rss,
    "reddit_json": fetch_reddit,
    "claude_blog": fetch_claude_blog,
}

HTML_SCRAPERS = {
    "techmeme": fetch_techmeme,
    "implicator": fetch_implicator,
    "claude_blog": fetch_claude_blog,
}

HTML_SCRAPERS = {
    "techmeme": fetch_techmeme,
    "implicator": fetch_implicator,
}


async def aggregate_news(config: dict) -> list[Story]:
    sources = config.get("sources", {})
    max_stories = config.get("podcast", {}).get("max_stories", 12)

    tasks = []
    task_names = []

    for name, src_config in sources.items():
        if not src_config.get("enabled", True):
            continue

        src_type = src_config.get("type", "rss")
        src_config["_source_name"] = _friendly_name(name)

        if src_type == "html_scraper":
            fetcher = HTML_SCRAPERS.get(name)
            if not fetcher:
                logger.warning(f"No HTML scraper for source: {name}")
                continue
        elif src_type in FETCHERS:
            fetcher = FETCHERS[src_type]
        else:
            logger.warning(f"Unknown source type: {src_type} for {name}")
            continue

        tasks.append(fetcher(src_config))
        task_names.append(name)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_stories = []
    for name, result in zip(task_names, results):
        if isinstance(result, Exception):
            logger.error(f"Source '{name}' failed: {result}")
            continue
        logger.info(f"Source '{name}': {len(result)} stories")
        all_stories.extend(result)

    # Deduplicate
    all_stories = deduplicate(all_stories)

    # Filter out articles already used this week
    all_stories = filter_already_used(all_stories, days=7)

    # Sort: by score (if available) then by recency
    all_stories.sort(
        key=lambda s: (s.score or 0, s.published.timestamp() if s.published else 0),
        reverse=True,
    )

    # Cap at max
    all_stories = all_stories[:max_stories]
    logger.info(f"Aggregated {len(all_stories)} stories after dedup and cap")

    # Record these stories as used for future runs
    if all_stories:
        record_used_stories(all_stories)

    return all_stories


def _friendly_name(source_key: str) -> str:
    names = {
        "hackernews": "Hacker News",
        "techmeme": "Techmeme",
        "implicator": "implicator.ai",
        "claude_blog": "Claude Blog",
        "ars_ai": "Ars Technica",
        "the_batch": "The Batch",
        "mit_tech_review_ai": "MIT Technology Review",
        "reddit_localllama": "r/LocalLLaMA",
        "reddit_machinelearning": "r/MachineLearning",
        "openai_blog": "OpenAI Blog",
        "anthropic_news": "Anthropic",
        "google_ai_blog": "Google AI Blog",
        "huggingface_blog": "Hugging Face",
        "simon_willison": "Simon Willison",
        "the_verge_ai": "The Verge",
        "thomas_wiegold": "Thomas Wiegold",
    }
    return names.get(source_key, source_key.replace("_", " ").title())
