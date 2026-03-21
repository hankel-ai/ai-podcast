import logging
import os
from datetime import datetime

import httpx

from sources.base import Story

logger = logging.getLogger(__name__)


async def send_podcast(audio_path: str, stories: list[Story], config: dict):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        raise RuntimeError("Telegram credentials not configured")

    base_url = f"https://api.telegram.org/bot{bot_token}"
    date_str = datetime.now().strftime("%B %d, %Y")
    title = config.get("podcast", {}).get("title", "AI Daily Briefing")

    tg_config = config.get("telegram", {})

    async with httpx.AsyncClient(timeout=120) as client:
        # Send audio file
        if tg_config.get("send_audio", True):
            filename = os.path.basename(audio_path)
            with open(audio_path, "rb") as f:
                resp = await client.post(
                    f"{base_url}/sendAudio",
                    data={
                        "chat_id": chat_id,
                        "title": f"{title} - {date_str}",
                        "performer": title,
                    },
                    files={"audio": (filename, f, "audio/mpeg")},
                )
            if resp.status_code != 200:
                logger.error(f"Telegram sendAudio failed: {resp.status_code} {resp.text}")
                resp.raise_for_status()
            logger.info("Audio sent to Telegram")

        # Send links message
        if tg_config.get("send_links", True):
            lines = [f"<b>{title} - {date_str}</b>\n"]
            for i, story in enumerate(stories, 1):
                # Escape HTML special chars in title
                safe_title = (
                    story.title
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                lines.append(f'{i}. <a href="{story.url}">{safe_title}</a> ({story.source_name})')

            resp = await client.post(
                f"{base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "\n".join(lines),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code != 200:
                logger.error(f"Telegram sendMessage failed: {resp.status_code} {resp.text}")
                resp.raise_for_status()
            logger.info("Links sent to Telegram")


async def send_failure_notification(message: str):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        return

    base_url = f"https://api.telegram.org/bot{bot_token}"
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"{base_url}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": f"⚠️ AI Podcast failed: {message}",
            },
        )
