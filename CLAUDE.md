# ai-podcast

## Purpose
Automated daily AI news podcast generator. Scrapes AI news, generates audio with Edge TTS, delivers via Telegram.

## Tech Stack
- Python 3.10+
- httpx (async HTTP), beautifulsoup4 (HTML parsing), feedparser (RSS)
- edge-tts (text-to-speech, free Microsoft neural voices)
- anthropic (optional, for AI script mode)
- pyyaml, python-dotenv

## Key Commands
- `pip install -r requirements.txt` — install dependencies
- `python main.py` — full pipeline run
- `python main.py --dry-run` — script only, no audio/Telegram
- `python main.py --sources` — list configured sources
- `python main.py --verbose` — debug logging
- `schedule_task.cmd` — register Windows Task Scheduler (run as admin)

## Project Structure
```
main.py              — Entry point, CLI, orchestration
config.yaml          — All configuration (sources, voice, schedule)
.env                 — Secrets (Telegram token, Anthropic key)
sources/             — News source fetchers (HN API, RSS, HTML scrapers, Reddit)
pipeline/            — Aggregation, script generation, audio generation
delivery/            — Telegram bot delivery
utils/               — Dedup, logging
output/              — Generated MP3s and logs (gitignored)
```

## Architecture
1. Aggregate: concurrent async fetch from all enabled sources
2. Deduplicate: URL normalization + title similarity
3. Script: AI mode (Claude Haiku) or template mode
4. Audio: Edge TTS → MP3
5. Deliver: Telegram Bot API (audio + links)

## Conventions
- All source fetchers are async, return list[Story]
- Source failures are non-fatal (logged, skipped)
- Config-driven: sources, voice, max stories all in config.yaml
