import logging
import os
import re
import io
from datetime import datetime

import edge_tts

from pipeline.audio_mixer import apply_production

logger = logging.getLogger(__name__)


async def generate_audio(script: str, config: dict) -> str:
    podcast_config = config.get("podcast", {})
    output_dir = podcast_config.get("output_dir", "./output")
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f"ai_briefing_{date_str}.mp3")

    conversation = podcast_config.get("conversation", False)
    if conversation and _has_speaker_labels(script):
        await _generate_conversation_audio(script, config, output_path)
    else:
        await _generate_single_voice_audio(script, config, output_path)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Raw audio saved: {output_path} ({size_mb:.1f} MB)")

    # Post-processing: intro, outro, bed music
    output_path = apply_production(output_path, config)

    return output_path


def _has_speaker_labels(script: str) -> bool:
    return bool(re.search(r'^(HOST|COHOST):', script, re.MULTILINE))


async def _generate_single_voice_audio(script: str, config: dict, output_path: str) -> None:
    podcast_config = config.get("podcast", {})
    voice = podcast_config.get("voice", "en-US-AndrewMultilingualNeural")
    rate = podcast_config.get("voice_rate", "+5%")

    logger.info(f"Generating single-voice audio with voice={voice}, rate={rate}")
    communicate = edge_tts.Communicate(script, voice, rate=rate)
    await communicate.save(output_path)


async def _generate_conversation_audio(script: str, config: dict, output_path: str) -> None:
    podcast_config = config.get("podcast", {})
    host_voice = podcast_config.get("voice", "en-US-AndrewMultilingualNeural")
    cohost_voice = podcast_config.get("cohost_voice", "en-US-EmmaMultilingualNeural")
    rate = podcast_config.get("voice_rate", "+5%")

    logger.info(f"Generating conversation audio: host={host_voice}, cohost={cohost_voice}")

    segments = _parse_conversation(script)
    logger.info(f"Parsed {len(segments)} conversation segments")

    mp3_chunks = []
    for i, (speaker, text) in enumerate(segments):
        voice = host_voice if speaker == "HOST" else cohost_voice
        # Add a small pause between speaker turns for natural pacing
        if i > 0:
            text = f'<break time="400ms"/> {text}'
        chunk = await _tts_to_bytes(text, voice, rate)
        if chunk:
            mp3_chunks.append(chunk)

    # Concatenate all MP3 chunks
    with open(output_path, "wb") as f:
        for chunk in mp3_chunks:
            f.write(chunk)


def _parse_conversation(script: str) -> list[tuple[str, str]]:
    """Parse a HOST:/COHOST: labeled script into (speaker, text) segments."""
    segments = []
    current_speaker = None
    current_lines = []

    for line in script.split("\n"):
        line = line.strip()
        if not line:
            continue

        match = re.match(r'^(HOST|COHOST):\s*(.*)', line)
        if match:
            # Save previous segment
            if current_speaker and current_lines:
                segments.append((current_speaker, " ".join(current_lines)))
            current_speaker = match.group(1)
            current_lines = [match.group(2)] if match.group(2) else []
        elif current_speaker:
            # Continuation line
            current_lines.append(line)

    # Don't forget the last segment
    if current_speaker and current_lines:
        segments.append((current_speaker, " ".join(current_lines)))

    return segments


async def _tts_to_bytes(text: str, voice: str, rate: str) -> bytes:
    """Generate TTS audio and return raw MP3 bytes."""
    if not text.strip():
        return b""
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        return buffer.getvalue()
    except Exception as e:
        logger.warning(f"TTS segment failed for voice={voice}: {e}")
        return b""


