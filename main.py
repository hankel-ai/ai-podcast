#!/usr/bin/env python3
"""AI Daily Briefing - News podcast generator."""

import argparse
import asyncio
import logging
import os
import sys

# Fix Windows console encoding for Unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import yaml
from dotenv import load_dotenv

from pipeline.aggregator import aggregate_news
from pipeline.scriptwriter import generate_script
from pipeline.audio import generate_audio
from delivery.telegram import send_podcast, send_failure_notification
from delivery.discord import send_podcast_discord, send_failure_notification_discord
from utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_sources(config: dict):
    sources = config.get("sources", {})
    print(f"\n{'Source':<30} {'Type':<20} {'Enabled':<10} {'Max Stories'}")
    print("-" * 75)
    for name, src in sources.items():
        enabled = "Yes" if src.get("enabled", True) else "No"
        src_type = src.get("type", "rss")
        max_s = src.get("max_stories", "?")
        print(f"{name:<30} {src_type:<20} {enabled:<10} {max_s}")
    print()


async def run(args):
    # Change to script directory so relative paths work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    load_dotenv()
    config = load_config(args.config)

    if args.verbose:
        config.setdefault("logging", {})["level"] = "DEBUG"
    setup_logging(config)

    if args.sources:
        list_sources(config)
        return

    min_stories = config.get("podcast", {}).get("min_stories", 3)

    try:
        # 1. Aggregate news
        logger.info("Starting AI Daily Briefing generation")
        stories = await aggregate_news(config)

        if len(stories) < min_stories:
            msg = f"Only {len(stories)} stories found (minimum: {min_stories})"
            logger.warning(msg)
            await _notify_failure(msg, config)
            sys.exit(1)

        # 2. Generate script
        script = generate_script(stories, config)
        logger.info(f"Script generated: {len(stories)} stories, {len(script)} chars")

        if args.dry_run:
            print("\n" + "=" * 60)
            print("PODCAST SCRIPT (dry run)")
            print("=" * 60 + "\n")
            print(script)
            print("\n" + "=" * 60)
            print(f"\nStories ({len(stories)}):")
            for i, s in enumerate(stories, 1):
                print(f"  {i}. [{s.source_name}] {s.title}")
                print(f"     {s.url}")
            return

        # 3. Generate audio
        audio_path = await generate_audio(script, config)
        logger.info(f"Audio generated: {audio_path}")

        # 4. Deliver
        if config.get("telegram", {}).get("enabled", True):
            await send_podcast(audio_path, stories, config)
            logger.info("Podcast delivered via Telegram")

        if config.get("discord", {}).get("enabled", False):
            await send_podcast_discord(audio_path, stories, config)
            logger.info("Podcast delivered via Discord")

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        try:
            await _notify_failure(str(e), config)
        except Exception:
            pass
        sys.exit(1)


async def _notify_failure(message: str, config: dict):
    if config.get("telegram", {}).get("enabled", True):
        await send_failure_notification(message)
    if config.get("discord", {}).get("enabled", False):
        await send_failure_notification_discord(message)


def main():
    parser = argparse.ArgumentParser(description="AI Daily Briefing - News Podcast Generator")
    parser.add_argument("--dry-run", action="store_true", help="Generate script only, no audio or Telegram")
    parser.add_argument("--sources", action="store_true", help="List configured sources")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
