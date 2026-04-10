# ai-podcast

## Purpose
Automated daily AI news podcast generator. Scrapes AI news, generates audio with Edge TTS, delivers via Telegram and/or Discord. Supports single-narrator and dual-host conversation formats with production polish (intro/outro, bed music).

## Tech Stack
- Python 3.10+
- httpx (async HTTP), beautifulsoup4 (HTML parsing), feedparser (RSS)
- edge-tts (text-to-speech, free Microsoft neural voices)
- trafilatura (article content extraction)
- pydub (audio mixing — requires ffmpeg on PATH)
- anthropic (optional, for AI script mode)
- pyyaml, python-dotenv

## Key Commands
- `pip install -r requirements.txt` — install dependencies
- `python main.py` — full pipeline run
- `python main.py --dry-run` — script only, no audio/Telegram
- `python main.py --sources` — list configured sources
- `python main.py --verbose` — debug logging
- `python main.py --health` — source health report (success rates, latency, errors)
- `python generate_assets.py` — generate default intro/outro/transition audio
- `schedule_task.cmd` — register Windows Task Scheduler (run as admin)

## Project Structure
```
main.py              — Entry point, CLI, orchestration
generate_assets.py   — Generate default TTS-based audio assets
config.yaml          — All configuration (sources, voice, schedule, production)
.env                 — Secrets (Telegram token, Anthropic key)
assets/              — Audio assets (intro.mp3, outro.mp3, bed_music.mp3, transition.mp3)
sources/             — News source fetchers (HN API, RSS, HTML scrapers, Reddit)
pipeline/
  aggregator.py      — Concurrent fetch, dedup, content scraping
  scriptwriter.py    — Script generation (3 modes x 2 formats)
  audio.py           — TTS generation (single or dual-voice)
  audio_mixer.py     — Post-processing: intro, outro, bed music overlay
delivery/            — Telegram bot + Discord webhook delivery
utils/               — Dedup, logging, content scraper, episode recap tracker
output/              — Generated MP3s, logs, article history, episode recaps (gitignored)
```

## Architecture
1. Aggregate: concurrent async fetch from all enabled sources
2. Deduplicate: URL normalization + title similarity
3. Content scrape: fetch article body text via trafilatura (configurable)
4. Script: AI mode (Claude Haiku), Ollama, or template — with recent episode context for continuity
5. Audio: Edge TTS → MP3 (single voice or two-voice conversation stitching)
6. Production mix: prepend intro, append outro, overlay bed music (via pydub/ffmpeg)
7. Record episode recap for future continuity references
8. Deliver: Telegram Bot API and/or Discord Webhook (audio + links)

## Key Config Options (config.yaml)
- `podcast.conversation: true/false` — dual-host (HOST:/COHOST:) vs single narrator
- `podcast.scrape_content: true/false` — fetch article body text for richer scripts
- `podcast.voice` — host/narrator voice (Edge TTS voice ID)
- `podcast.cohost_voice` — co-host voice (conversation mode only)
- `podcast.script_mode` — "ollama", "ai", or "template"
- `podcast.profile` — "brief", "standard", or "deep" (see below)
- `podcast.production.enabled` — toggle intro/outro/bed music mixing
- `podcast.production.bed_music_volume_db` — bed music volume (-18 default, lower = quieter)
- `podcast.production.assets_dir` — path to audio assets folder

## Episode Length Profiles
Set via `podcast.profile` in config.yaml or `--profile` CLI flag (CLI overrides config).

| Profile    | Max Stories | Solo Duration | Convo Duration | Depth                              |
|------------|-------------|---------------|----------------|-------------------------------------|
| `brief`    | 5           | 2-3 min       | 3-4 min        | Headline + why it matters, punchy   |
| `standard` | 15          | 5-7 min       | 7-10 min       | Natural summary + brief commentary  |
| `deep`     | 8           | 12-15 min     | 15-20 min      | Detailed analysis, 2-3 paragraphs   |

Profile `max_stories` is capped by the lower of profile and `podcast.max_stories` config value.

## Conventions
- All source fetchers are async, return list[Story]
- Source failures are non-fatal (logged, skipped)
- Config-driven: sources, voice, max stories all in config.yaml
- Conversation scripts use `HOST:` / `COHOST:` line prefixes, parsed by audio pipeline
- Article content scraping runs only on final capped stories (not all fetched stories)
- Production mixing gracefully degrades if ffmpeg not on PATH or assets missing
- Episode recaps stored in `output/episode_recaps.json` (last 7 days, auto-pruned)
- LLM prompts include last 3 days of episode recaps for story continuity callbacks
- Source health tracked in `output/source_health.json` (30-day rolling window)
- `--health` classifies sources as healthy (85%+), degraded (50-84%), or broken (<50%)
