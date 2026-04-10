#!/usr/bin/env python3
"""Generate default audio assets (intro, outro, transition) using Edge TTS."""

import asyncio
import os

import edge_tts
from pydub import AudioSegment


ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Use a distinct, warm voice for branding clips
BRAND_VOICE = "en-US-AndrewMultilingualNeural"
BRAND_RATE = "-5%"  # Slightly slower for gravitas


async def generate_asset(text: str, filename: str, voice: str = BRAND_VOICE, rate: str = BRAND_RATE):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        print(f"  Skipping {filename} (already exists)")
        return
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(path)
    # Trim silence from edges
    try:
        audio = AudioSegment.from_mp3(path)
        trimmed = _trim_silence(audio)
        trimmed.export(path, format="mp3")
    except Exception:
        pass  # Keep raw file if trimming fails
    size_kb = os.path.getsize(path) / 1024
    print(f"  Generated {filename} ({size_kb:.0f} KB)")


def _trim_silence(audio: AudioSegment, threshold_db: float = -45.0, chunk_ms: int = 50) -> AudioSegment:
    """Trim leading and trailing silence from an audio segment."""
    start = 0
    end = len(audio)
    for i in range(0, len(audio), chunk_ms):
        if audio[i:i + chunk_ms].dBFS > threshold_db:
            start = i
            break
    for i in range(len(audio), 0, -chunk_ms):
        if audio[i - chunk_ms:i].dBFS > threshold_db:
            end = i
            break
    # Add small padding
    start = max(0, start - 100)
    end = min(len(audio), end + 200)
    return audio[start:end]


async def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    print("Generating default audio assets...")

    await generate_asset(
        "AI Daily Briefing.",
        "intro.mp3",
    )
    await generate_asset(
        "That's all for today. See you next time.",
        "outro.mp3",
    )
    await generate_asset(
        "...",
        "transition.mp3",
    )

    print("Done! Assets are in:", ASSETS_DIR)
    print("Replace any file with your own custom audio.")


if __name__ == "__main__":
    asyncio.run(main())
