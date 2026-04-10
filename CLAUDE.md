# ai-podcast

## Purpose
Automated daily AI news podcast generator. Scrapes AI news, generates audio with Edge TTS, delivers via Telegram and/or Discord. Supports single-narrator and dual-host conversation formats.

## Tech Stack
- Python 3.10+
- httpx (async HTTP), beautifulsoup4 (HTML parsing), feedparser (RSS)
- edge-tts (text-to-speech, free Microsoft neural voices)
- trafilatura (article content extraction)
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
delivery/            — Telegram bot + Discord webhook delivery
utils/               — Dedup, logging, content scraper
output/              — Generated MP3s and logs (gitignored)
```

## Architecture
1. Aggregate: concurrent async fetch from all enabled sources
2. Deduplicate: URL normalization + title similarity
3. Content scrape: fetch article body text via trafilatura (configurable)
4. Script: AI mode (Claude Haiku), Ollama, or template — single narrator or dual-host conversation
5. Audio: Edge TTS → MP3 (single voice or two-voice conversation stitching)
6. Deliver: Telegram Bot API and/or Discord Webhook (audio + links)

## Key Config Options (config.yaml)
- `podcast.conversation: true/false` — dual-host (HOST:/COHOST:) vs single narrator
- `podcast.scrape_content: true/false` — fetch article body text for richer scripts
- `podcast.voice` — host/narrator voice (Edge TTS voice ID)
- `podcast.cohost_voice` — co-host voice (conversation mode only)
- `podcast.script_mode` — "ollama", "ai", or "template"

## Conventions
- All source fetchers are async, return list[Story]
- Source failures are non-fatal (logged, skipped)
- Config-driven: sources, voice, max stories all in config.yaml
- Conversation scripts use `HOST:` / `COHOST:` line prefixes, parsed by audio pipeline
- Article content scraping runs only on final capped stories (not all fetched stories)
