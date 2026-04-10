"""Post-processing: mix intro, outro, bed music, and transitions into the podcast MP3."""

import logging
import os

from pydub import AudioSegment

logger = logging.getLogger(__name__)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def apply_production(podcast_path: str, config: dict) -> str:
    """Apply production polish to an existing podcast MP3. Returns the output path."""
    prod_config = config.get("podcast", {}).get("production", {})
    if not prod_config.get("enabled", False):
        logger.debug("Production mixing disabled")
        return podcast_path

    try:
        podcast = AudioSegment.from_mp3(podcast_path)
    except Exception as e:
        logger.warning(f"Failed to load podcast for mixing (ffmpeg may not be on PATH): {e}")
        return podcast_path

    assets_dir = prod_config.get("assets_dir", ASSETS_DIR)
    result = AudioSegment.empty()

    # 1. Intro
    intro_path = os.path.join(assets_dir, "intro.mp3")
    if os.path.exists(intro_path):
        try:
            intro = AudioSegment.from_mp3(intro_path)
            intro_vol = prod_config.get("intro_volume_db", 0)
            intro = intro + intro_vol
            result += intro
            # Small gap between intro and content
            result += AudioSegment.silent(duration=400)
            logger.info(f"Intro added ({len(intro)}ms)")
        except Exception as e:
            logger.warning(f"Failed to load intro: {e}")

    # 2. Main podcast content
    result += podcast

    # 3. Outro
    outro_path = os.path.join(assets_dir, "outro.mp3")
    if os.path.exists(outro_path):
        try:
            outro = AudioSegment.from_mp3(outro_path)
            outro_vol = prod_config.get("outro_volume_db", 0)
            outro = outro + outro_vol
            result += AudioSegment.silent(duration=400)
            result += outro
            logger.info(f"Outro added ({len(outro)}ms)")
        except Exception as e:
            logger.warning(f"Failed to load outro: {e}")

    # 4. Bed music (mixed underneath at low volume)
    bed_path = os.path.join(assets_dir, "bed_music.mp3")
    if os.path.exists(bed_path):
        try:
            bed = AudioSegment.from_mp3(bed_path)
            bed_vol = prod_config.get("bed_music_volume_db", -18)
            bed = bed + bed_vol

            # Loop bed music to cover full podcast length
            podcast_len = len(result)
            if len(bed) < podcast_len:
                loops_needed = (podcast_len // len(bed)) + 1
                bed = bed * loops_needed
            bed = bed[:podcast_len]

            # Fade in/out the bed music
            fade_ms = min(3000, podcast_len // 4)
            bed = bed.fade_in(fade_ms).fade_out(fade_ms)

            result = result.overlay(bed)
            logger.info(f"Bed music mixed ({podcast_len}ms, {bed_vol}dB)")
        except Exception as e:
            logger.warning(f"Failed to mix bed music: {e}")

    # Export back to the same path
    try:
        bitrate = prod_config.get("bitrate", "64k")
        result.export(podcast_path, format="mp3", bitrate=bitrate)
        size_mb = os.path.getsize(podcast_path) / (1024 * 1024)
        logger.info(f"Production mix complete: {podcast_path} ({size_mb:.1f} MB)")
    except Exception as e:
        logger.warning(f"Failed to export mixed audio: {e}")

    return podcast_path
