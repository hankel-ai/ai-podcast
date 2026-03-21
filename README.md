# AI Daily Briefing

Automated daily AI news podcast generator. Scrapes top AI news from configurable sources, generates a podcast script (AI-powered or template-based), converts to audio with Edge TTS, and delivers via Telegram.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow prompts to create your bot
3. Copy the bot token

### 3. Get your Chat ID

1. Message your new bot (send any message)
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find your `chat_id` in the response JSON

### 4. Configure .env

```bash
cp .env.example .env
# Edit .env with your Telegram credentials
# Optionally add ANTHROPIC_API_KEY for AI script mode
```

### 5. Configure sources

Edit `config.yaml` to enable/disable sources, adjust max stories, change voice, etc.

## Usage

```bash
# Full run: scrape → script → audio → Telegram
python main.py

# Dry run: generate script only, print to console
python main.py --dry-run

# List configured sources
python main.py --sources

# Debug logging
python main.py --verbose
```

## Schedule Daily

Run `schedule_task.cmd` (as Administrator) to register a Windows Task Scheduler job for 9:30 AM daily.

## Script Modes

Set `podcast.script_mode` in `config.yaml`:

- **`ai`**: Claude Haiku writes a natural podcast script (~$0.01/day). Requires `ANTHROPIC_API_KEY`.
- **`template`**: Template-based script. Free, no API key needed.

## Voice Options

Change `podcast.voice` in `config.yaml`. Default: `en-US-AndrewMultilingualNeural`.

Run `edge-tts --list-voices` for 400+ options. See `config.yaml` comments for recommended voices.
