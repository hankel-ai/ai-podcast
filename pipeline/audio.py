import logging
import os
from datetime import datetime

import edge_tts

logger = logging.getLogger(__name__)


async def generate_audio(script: str, config: dict) -> str:
    podcast_config = config.get("podcast", {})
    voice = podcast_config.get("voice", "en-US-AndrewMultilingualNeural")
    rate = podcast_config.get("voice_rate", "+5%")
    output_dir = podcast_config.get("output_dir", "./output")

    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f"ai_briefing_{date_str}.mp3")

    logger.info(f"Generating audio with voice={voice}, rate={rate}")
    communicate = edge_tts.Communicate(script, voice, rate=rate)
    await communicate.save(output_path)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Audio saved: {output_path} ({size_mb:.1f} MB)")

    return output_path
