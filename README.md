# AI Daily Briefing

Automated daily AI news podcast generator. Scrapes top AI news from configurable sources, generates a podcast script via local LLM (Ollama), cloud API (Claude), or templates, converts to audio with Edge TTS, and delivers via Telegram and/or Discord.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up delivery (Telegram and/or Discord)

You can enable one or both delivery methods in `config.yaml`.

#### Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow prompts to create your bot
3. Copy the bot token
4. Message your new bot (send any message)
5. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Find your `chat_id` in the response JSON

#### Discord Webhook

1. Open your Discord server and go to **Server Settings → Integrations → Webhooks**
2. Click **New Webhook**
3. Name it (e.g., "AI Podcast"), select the target channel, and click **Copy Webhook URL**

### 3. Configure .env

```bash
cp .env.example .env
# Edit .env with your delivery credentials
# Optionally add ANTHROPIC_API_KEY for Claude script mode
```

Required variables depend on which delivery methods you enable:

| Variable | Required when |
|----------|---------------|
| `TELEGRAM_BOT_TOKEN` | `telegram.enabled: true` |
| `TELEGRAM_CHAT_ID` | `telegram.enabled: true` |
| `DISCORD_WEBHOOK_URL` | `discord.enabled: true` |
| `ANTHROPIC_API_KEY` | `podcast.script_mode: "ai"` |

### 4. Configure sources and options

Edit `config.yaml` to enable/disable sources, adjust max stories, change voice, switch script mode, etc.

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

| Mode | Description | Requirements |
|------|-------------|--------------|
| **`ollama`** (default) | Local LLM generates a natural, conversational podcast script | Ollama running locally |
| **`ai`** | Claude Haiku writes the script via Anthropic API (~$0.01/day) | `ANTHROPIC_API_KEY` in `.env` |
| **`template`** | Template-based script with canned transitions. No LLM needed | None |

All modes fall back to `template` automatically if the LLM is unavailable.

### Ollama Configuration

```yaml
ollama:
  url: "http://localhost:11434"
  model: "llama3.1:8b"
```

Change `model` to any model you have pulled. List models with `ollama list`.

## News Sources

13 sources enabled by default, all configurable in `config.yaml`:

| Source | Type | Notes |
|--------|------|-------|
| Hacker News | API | Keyword-filtered (AI/LLM/GPT/Claude/agentic/etc.), min score 50 |
| Techmeme | HTML scrape | AI-related story clusters |
| implicator.ai | HTML scrape | Curated AI news |
| Ars Technica AI | RSS | |
| MIT Technology Review AI | RSS | |
| r/LocalLLaMA | Reddit JSON | Min score 100 |
| r/MachineLearning | Reddit JSON | Min score 50 |
| OpenAI Blog | RSS | |
| Google AI Blog | RSS | |
| Hugging Face Blog | RSS | |
| Simon Willison's Blog | RSS | Agentic coding focus |
| The Verge AI | RSS | |
| Thomas Wiegold's Blog | RSS | Rarely updated |

Each source has `enabled`, `max_stories`, and type-specific options. Set `podcast.max_stories` to control the total article count (default 12).

## Voice Options

Change `podcast.voice` in `config.yaml`. Default: `en-US-AndrewMultilingualNeural`.

| Voice | Description |
|-------|-------------|
| `en-US-AndrewMultilingualNeural` | Deep, authoritative male (default) |
| `en-US-AriaNeural` | Warm, professional female |
| `en-US-GuyNeural` | Classic male news reader |
| `en-US-JennyNeural` | Friendly, clear female |
| `en-US-BrianMultilingualNeural` | Confident male, slightly younger |
| `en-US-EmmaMultilingualNeural` | Polished female, great diction |
| `en-GB-RyanNeural` | British male, BBC-style |
| `en-GB-SoniaNeural` | British female, polished |
| `en-AU-WilliamNeural` | Australian male |
| `en-IN-PrabhatNeural` | Indian English male |

Run `edge-tts --list-voices` for 400+ options.

## Delivery

Enable one or both in `config.yaml`:

```yaml
telegram:
  enabled: true    # Telegram Bot API
discord:
  enabled: false   # Discord Webhook
```

Both deliver:
1. **Audio file** — MP3 podcast ready to play
2. **Story links** — Numbered list with titles, URLs, and source attribution

Each has independent `send_audio` and `send_links` toggles.

## Project Structure

```
main.py              Entry point and CLI
config.yaml          All configuration (sources, voice, LLM, schedule)
.env                 Secrets (Telegram token, Discord webhook, Anthropic key)
sources/             News source fetchers (HN API, RSS, HTML scrapers, Reddit)
pipeline/            Aggregation, script generation, audio generation
delivery/            Telegram Bot + Discord Webhook delivery
utils/               Deduplication, logging
output/              Generated MP3s and logs (gitignored)
```
