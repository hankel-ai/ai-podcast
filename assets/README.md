# Audio Assets

Drop custom audio files here to brand your podcast. All files are optional — the pipeline generates TTS-based defaults if a file is missing.

| File | Purpose | Recommended |
|------|---------|-------------|
| `intro.mp3` | Played before the podcast starts | 3-5 seconds |
| `outro.mp3` | Played after the podcast ends | 3-5 seconds |
| `transition.mp3` | Played between story segments | 1-2 seconds |
| `bed_music.mp3` | Looped underneath narration at low volume | 30-60 sec loop, calm/ambient |

Volume levels are configurable in `config.yaml` under `podcast.production`.

Generate the TTS-based defaults anytime:
```bash
python generate_assets.py
```
