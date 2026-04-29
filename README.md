<h1 align="center">🎬 YT Shorts Autopilot</h1>

<p align="center">
  Automated YouTube Shorts upload pipeline.<br/>
  FFmpeg post-processing · scheduled publishing · runs on Windows startup · works while your PC is off.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/FFmpeg-required-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/YouTube%20API-v3-red?style=flat-square&logo=youtube" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

---

## What it does

Drop your `.mp4` files into the `queue/` folder, run the script once, and it handles everything else:

1. **Processes each video** with FFmpeg — adds your watermark, boosts audio, optionally mixes background music
2. **Uploads to YouTube** as scheduled private videos set to publish at your chosen times
3. **Moves processed videos** to `done/` and logs every upload to CSV
4. **Runs once per day** — safe to add to Windows startup, it skips if it already ran today

YouTube publishes automatically at the scheduled times — **your PC can be off.**

---

## Features

- 📅 **Scheduled uploads** — 4 slots per day (7 AM · 9 AM · 7 PM · 9 PM Philippine Time by default)
- 🎨 **FFmpeg processing** — watermark overlay · volume boost · optional BGM mixing
- 📝 **Per-video scripts** — custom title & description from a matching `.txt` file
- 🔄 **Rotating watermark** — cycles through all 4 corners automatically
- 🔒 **Slot-safe scheduling** — never double-books the same time slot
- 📊 **Upload log** — full CSV history of every upload with scheduled times
- 🧙 **Setup wizard** — `setup.py` creates folders, checks dependencies, guides first run
- ⚡ **Once-per-day guard** — safe to add to Windows startup

---

## Requirements

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| FFmpeg | Any recent | [ffmpeg.org](https://ffmpeg.org/download.html) — must be in PATH |
| Google account | — | The YouTube channel you want to upload to |

---

## Quick Start

### Step 1 — Clone and run setup

```bash
git clone https://github.com/Ghraven/yt-shorts-autopilot
cd yt-shorts-autopilot
python setup.py
```

The wizard installs pip dependencies, creates all folders, and checks for FFmpeg.

### Step 2 — Get YouTube OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → **APIs & Services** → **Library** → enable **YouTube Data API v3**
3. **Credentials** → **+ Create Credentials** → **OAuth client ID** → Desktop app
4. Download the JSON → rename it `client_secrets.json` → place it in the project root

### Step 3 — Add your assets

| Folder | What to put here |
|---|---|
| `queue/` | Your `.mp4` Short videos (oldest processes first) |
| `LOGO/` | Your channel logo / watermark (PNG recommended) |
| `BGM/` | Background music files — `.mp3` / `.wav` / `.m4a` (optional) |

### Step 4 — (Optional) Generate script templates

```bash
python generate_scripts.py
```

Creates a `.txt` template in `scripts/` for every video in `queue/`. Fill in custom titles and descriptions — or skip this and the defaults from `config.py` will be used.

### Step 5 — Run

```bash
python daily_batch.py
```

First run opens a browser for YouTube login (one-time OAuth). After that, fully automatic.

---

## How It Works

```
PC boots → daily_batch.py runs
    │
    ├─ Already ran today? → Exit silently
    │
    ├─ Get next 4 videos from queue/
    │
    ├─ Calculate 4 upload time slots (no double-booking)
    │
    ├─ For each video:
    │    ├─ Read scripts/<name>.txt for custom title/description
    │    ├─ FFmpeg: watermark + audio boost + BGM mix
    │    ├─ Upload to YouTube as scheduled private video
    │    ├─ Log to upload_log.csv
    │    └─ Move original to done/
    │
    └─ Save today's date → YouTube auto-publishes at scheduled times
```

---

## Per-Video Scripts

Each video in `queue/` can have a matching `.txt` in `scripts/` with the same filename:

```
queue/my_clip.mp4
scripts/my_clip.txt   ← linked automatically
```

**Format:**
```
TITLE: Your Custom Video Title
---
Your description here.
Can be multiple lines.
Include hashtags, emojis, anything you want.

#Shorts #YourChannel
```

If no script file exists → defaults from `config.py` are used.

---

## Configuration (`config.py`)

All settings live in `config.py` — run `setup.py` to change them interactively, or edit directly:

```python
VIDEOS_PER_RUN = 4                          # uploads per day
UPLOAD_TIMES   = [(7,0),(9,0),(19,0),(21,0)] # 7AM 9AM 7PM 9PM PHT
VOLUME_BOOST   = 1.3                         # +30% louder
MUSIC_VOLUME   = 0.12                        # 12% BGM mix
WATERMARK_MODE = "rotate"                    # rotate / random / fixed corner
LOGO_WIDTH     = 130                         # watermark width in pixels
```

---

## Auto-Run on Windows Startup

1. Open **Task Scheduler** → **Create Basic Task**
2. **Trigger:** When the computer starts
3. **Action:** Start a program
   - Program: `C:\Path\To\python.exe`
   - Arguments: `daily_batch.py`
   - Start in: `C:\Path\To\yt-shorts-autopilot\`
4. Done — uploads happen automatically every day

---

## Folder Structure

```
yt-shorts-autopilot/
├── queue/              Drop your .mp4 videos here
├── done/               Videos move here after upload
├── processed/          Temp FFmpeg output (auto-cleaned)
├── BGM/                Background music (optional)
├── LOGO/               Your watermark image
├── scripts/            Per-video title + description .txt files
├── config.py           All settings
├── daily_batch.py      Main script — run this (or add to startup)
├── generate_scripts.py Creates .txt templates for queued videos
├── setup.py            First-run wizard
└── requirements.txt
```

---

## Troubleshooting

**`FFmpeg not found`** — Download from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) and add the `bin/` folder to Windows PATH.

**`client_secrets.json not found`** — Complete the OAuth setup above. File must be in the project root.

**`quota exceeded`** — YouTube's 10,000-unit daily quota resets at midnight Pacific. Each upload costs ~1,600 units, so 4 uploads = ~6,400 units — well within limits under normal use.

**`token.json` expired** — Delete `token.json` and re-run. It will prompt a fresh login.

---

## License

MIT — see [LICENSE](LICENSE)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.
