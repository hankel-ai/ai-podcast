import logging
import os
from datetime import datetime

import httpx

from sources.base import Story

logger = logging.getLogger(__name__)


async def send_podcast_discord(audio_path: str, stories: list[Story], config: dict):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        logger.error("DISCORD_WEBHOOK_URL not set in .env")
        raise RuntimeError("Discord webhook URL not configured")

    date_str = datetime.now().strftime("%B %d, %Y")
    title = config.get("podcast", {}).get("title", "AI Daily Briefing")
    dc_config = config.get("discord", {})

    async with httpx.AsyncClient(timeout=120) as client:
        # Send audio file
        if dc_config.get("send_audio", True):
            filename = os.path.basename(audio_path)
            with open(audio_path, "rb") as f:
                resp = await client.post(
                    webhook_url,
                    data={"content": f"**{title} - {date_str}**"},
                    files={"file": (filename, f, "audio/mpeg")},
                )
            if resp.status_code not in (200, 204):
                logger.error(f"Discord audio upload failed: {resp.status_code} {resp.text}")
                resp.raise_for_status()
            logger.info("Audio sent to Discord")

        # Send links message
        if dc_config.get("send_links", True):
            lines = [f"**{title} - {date_str}**\n"]
            for i, story in enumerate(stories, 1):
                lines.append(f"{i}. [{story.title}]({story.url}) ({story.source_name})")

            # Discord webhook messages have a 2000 char limit
            message = "\n".join(lines)
            if len(message) > 2000:
                message = message[:1997] + "..."

            resp = await client.post(
                webhook_url,
                json={"content": message},
            )
            if resp.status_code not in (200, 204):
                logger.error(f"Discord links message failed: {resp.status_code} {resp.text}")
                resp.raise_for_status()
            logger.info("Links sent to Discord")


async def send_failure_notification_discord(message: str):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        return

    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            webhook_url,
            json={"content": f"⚠️ AI Podcast failed: {message}"},
        )
