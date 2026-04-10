"""Track articles used across the week to prevent duplicates."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set

from .dedup import normalize_url

logger = logging.getLogger(__name__)

HISTORY_FILE = Path(__file__).parent.parent / "output" / "article_history.json"
RECAPS_FILE = Path(__file__).parent.parent / "output" / "episode_recaps.json"
WEEK_IN_DAYS = 7


def load_history() -> dict:
    """Load article history from file."""
    if not HISTORY_FILE.exists():
        return {"articles": [], "last_updated": None}

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load article history: {e}")
        return {"articles": [], "last_updated": None}


def save_history(history: dict):
    """Save article history to file."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save article history: {e}")


def clean_old_entries(history: dict, days: int = WEEK_IN_DAYS) -> dict:
    """Remove entries older than specified days."""
    cutoff = datetime.now() - timedelta(days=days)

    cleaned = []
    for entry in history.get("articles", []):
        try:
            entry_date = datetime.fromisoformat(entry.get("date", ""))
            if entry_date > cutoff:
                cleaned.append(entry)
        except (ValueError, TypeError):
            # Skip entries with invalid dates
            continue

    return {"articles": cleaned, "last_updated": history.get("last_updated")}


def get_used_urls(history: dict) -> Set[str]:
    """Get set of normalized URLs from history."""
    urls = set()
    for entry in history.get("articles", []):
        url = entry.get("url", "")
        if url:
            try:
                urls.add(normalize_url(url))
            except Exception:
                urls.add(url)  # Fallback to raw URL
    return urls


def add_to_history(history: dict, urls: list[str]):
    """Add new URLs to history with current date."""
    today = datetime.now().isoformat()

    for url in urls:
        history["articles"].append({"url": url, "date": today})

    history["last_updated"] = today


def filter_already_used(stories: list, days: int = WEEK_IN_DAYS) -> list:
    """Filter out stories that were already used within the specified days."""
    history = load_history()

    # Clean old entries
    history = clean_old_entries(history, days)

    # Get used URLs
    used_urls = get_used_urls(history)

    # Filter stories
    filtered = []
    for story in stories:
        try:
            norm_url = normalize_url(story.url)
            if norm_url not in used_urls:
                filtered.append(story)
            else:
                logger.debug(f"Skipping already-used article: {story.title[:50]}...")
        except Exception as e:
            logger.warning(f"Error checking URL {story.url}: {e}")
            # Include story if we can't check
            filtered.append(story)

    skipped = len(stories) - len(filtered)
    if skipped > 0:
        logger.info(
            f"Filtered out {skipped} previously used article(s) from the past {days} days"
        )

    return filtered


def record_used_stories(stories: list):
    """Record stories as used in the history."""
    history = load_history()
    urls = [story.url for story in stories if hasattr(story, "url")]
    add_to_history(history, urls)
    save_history(history)
    logger.info(f"Recorded {len(urls)} stories to history")


# --- Episode recap tracking (for story continuity) ---

def load_recaps() -> list[dict]:
    """Load episode recaps from file. Each recap: {date, stories: [{title, source}]}."""
    if not RECAPS_FILE.exists():
        return []
    try:
        with open(RECAPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load episode recaps: {e}")
        return []


def save_recap(stories: list):
    """Save a recap of today's episode (date + story titles/sources)."""
    recaps = load_recaps()

    today = datetime.now().strftime("%Y-%m-%d")
    day_name = datetime.now().strftime("%A")

    recap = {
        "date": today,
        "day": day_name,
        "stories": [
            {"title": s.title, "source": s.source_name}
            for s in stories if hasattr(s, "title")
        ],
    }

    # Replace if we already have a recap for today, otherwise append
    recaps = [r for r in recaps if r.get("date") != today]
    recaps.append(recap)

    # Keep only the last 7 days
    cutoff = (datetime.now() - timedelta(days=WEEK_IN_DAYS)).strftime("%Y-%m-%d")
    recaps = [r for r in recaps if r.get("date", "") >= cutoff]

    try:
        RECAPS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RECAPS_FILE, "w", encoding="utf-8") as f:
            json.dump(recaps, f, indent=2)
        logger.info(f"Saved episode recap: {len(recap['stories'])} stories for {today}")
    except Exception as e:
        logger.error(f"Failed to save episode recap: {e}")


def get_recent_recaps(days: int = 3) -> list[dict]:
    """Get recaps from the last N days (excluding today) for continuity context."""
    recaps = load_recaps()
    today = datetime.now().strftime("%Y-%m-%d")
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [
        r for r in recaps
        if r.get("date", "") >= cutoff and r.get("date") != today
    ]
