# yt-shorts-autopilot 🚀

Automated YouTube Shorts upload pipeline — edit videos with FFmpeg (watermark + volume boost + BGM), then schedule them directly to YouTube at fixed daily times.

Upload **4 Shorts per day**, automatically, even while your PC is off.

---

## Features

- **Scheduled uploads** — 7 AM, 9 AM, 7 PM, 9 PM (Philippine Time / UTC+8)
- **FFmpeg processing** — logo watermark overlay, volume boost, optional background music
- **Per-video scripts** — custom title & description from a matching `.txt` file
- **Auto-logo detection** — just drop any image into `LOGO/`, no config change needed
- **Slot-safe scheduling** — never double-books the same time slot across daily runs
- **Once-per-day guard** — safe to run on every PC startup; skips if already ran today
- **Upload log** — CSV history of every upload with scheduled publish time
- **First-run setup wizard** — `setup.py` creates all folders and checks dependencies

---

## Requirements

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| FFmpeg | Any recent | [ffmpeg.org](https://ffmpeg.org/download.html) — must be in PATH |
| Google account | — | The YouTube channel you want to upload to |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/yt-shorts-autopilot.git
cd yt-shorts-autopilot
```

### 2. Run the setup wizard

```bash
python setup.py
```

This will:
- Install all pip dependencies
- Create the folder structure (`queue/`, `done/`, `BGM/`, `LOGO/`, `scripts/`)
- Check for FFmpeg and `client_secrets.json`
- Print a "what to do next" summary

### 3. Set up YouTube OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → **APIs & Services** → **Library** → Enable **YouTube Data API v3**
3. **Credentials** → **+ Create Credentials** → **OAuth client ID** → Desktop app
4. Download the JSON → rename it `client_secrets.json` → place it in the project root

### 4. Add your assets

| Folder | What to put here |
|--------|-----------------|
| `queue/` | Your `.mp4` Short videos (oldest uploads first) |
| `LOGO/` | Your channel logo / watermark (PNG recommended) |
| `BGM/` | Background music files — `.mp3`, `.wav`, `.m4a` (optional) |

### 5. Generate script templates (optional)

```bash
python generate_scripts.py
```

Creates a `.txt` template in `scripts/` for every video in `queue/`.  
Open each file and fill in a custom title and description if you want.  
If you skip this step, the defaults from `config.py` are used.

### 6. Upload!

```bash
python daily_batch.py
```

The **first run** will open a browser window asking you to log in with your YouTube account — this is the one-time OAuth flow. After that, `token.json` is saved and future runs are fully automatic.

---

## Folder Structure

```
yt-shorts-autopilot/
├── queue/                  ← Drop your .mp4 videos here
├── done/                   ← Videos are moved here after upload
├── processed/              ← Temporary FFmpeg output (auto-cleaned)
├── BGM/                    ← Background music (optional)
├── LOGO/                   ← Your watermark image
├── scripts/                ← Per-video title + description .txt files
│   └── EXAMPLE_video_name.txt
├── config.py               ← All settings (edit this to customise)
├── daily_batch.py          ← Main upload script
├── generate_scripts.py     ← Creates script templates for queued videos
├── setup.py                ← First-run setup wizard
├── requirements.txt        ← Python dependencies
├── .env.example            ← Credential reference
└── .gitignore
```

---

## Per-Video Scripts

Each video in `queue/` can have a matching `.txt` file in `scripts/` with the **exact same filename stem**:

```
queue/my_motivational_clip.mp4
scripts/my_motivational_clip.txt   ← linked automatically
```

**Script file format:**

```
TITLE: Your Custom Video Title
---
Your description text here.
Can be multiple lines.
Include hashtags, emojis, links — anything you want.

#Shorts #Motivation #YourChannel
```

- If no script file exists → the defaults from `config.py` are used
- If the file is blank → same fallback to defaults
- `generate_scripts.py` pre-creates templates for all queued videos so you can fill them in bulk

---

## Configuration

Open `config.py` to customise everything:

```python
# Upload schedule (PHT / UTC+8)
UPLOAD_TIMES = [(7, 0), (9, 0), (19, 0), (21, 0)]  # 7AM 9AM 7PM 9PM

# Videos per daily run
VIDEOS_PER_RUN = 4

# Audio settings
VOLUME_BOOST = 1.3    # 1.3 = +30% louder
MUSIC_VOLUME = 0.12   # 12% BGM mix level

# Watermark
LOGO_WIDTH = 130      # pixels wide (height auto-scales)

# Default metadata
CHANNEL_HANDLE        = "@YourChannel"
DEFAULT_TITLE_TEMPLATE = "Daily Motivation #{n}"
```

---

## Auto-Run with Windows Task Scheduler

To run `daily_batch.py` automatically every day on PC startup:

1. Open **Task Scheduler** (`Win + S` → search "Task Scheduler")
2. Click **Create Basic Task…**
3. **Name:** `YT Shorts Autopilot`
4. **Trigger:** When the computer starts
5. **Action:** Start a program
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `daily_batch.py`
   - Start in: `C:\Path\To\yt-shorts-autopilot\`
6. Finish — the script will now run silently every time Windows boots

The once-per-day guard in the script ensures it only uploads once even if your PC restarts multiple times.

---

## How It Works

```
PC boots → daily_batch.py runs
    │
    ├─ Already ran today? → Exit silently
    │
    ├─ Get next 4 videos from queue/
    │
    ├─ Calculate 4 time slots (7AM/9AM/7PM/9PM PHT)
    │    └─ Always starts AFTER the last logged slot (no double-booking)
    │
    ├─ For each video:
    │    ├─ Read scripts/<name>.txt for custom title/description
    │    ├─ FFmpeg: add watermark + boost audio + mix BGM
    │    ├─ Upload to YouTube as private + scheduled
    │    ├─ Log to upload_log.csv
    │    └─ Move original to done/
    │
    └─ Write today's date to last_run.txt
         └─ YouTube publishes automatically at the scheduled times
              (PC can be off)
```

---

## Troubleshooting

**`FFmpeg not found`**  
Download from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) and add the `bin/` folder to your Windows PATH.

**`client_secrets.json not found`**  
Follow the OAuth setup steps above. Make sure the file is in the project root (same folder as `daily_batch.py`).

**`quota exceeded` error**  
You've hit YouTube's 10,000-unit daily quota. Each upload costs ~1,600 units, so 4 uploads/day = ~6,400 units — well within the limit under normal use. If you see this, wait until midnight Pacific Time for the quota to reset.

**`token.json` expired / invalid**  
Delete `token.json` and re-run `daily_batch.py`. It will prompt you to log in again.

**Videos uploading to the wrong channel**  
The OAuth login determines which channel is used. If you have multiple Google accounts, make sure you log in with the correct one during the browser prompt.

---

## License

MIT — free to use, modify, and distribute.
