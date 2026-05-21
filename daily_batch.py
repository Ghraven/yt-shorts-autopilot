"""
daily_batch.py — yt-shorts-autopilot  |  Daily Upload Engine
=============================================================
Uploads exactly 4 YouTube Shorts per run, pre-scheduled at:
  7:00 AM | 9:00 AM | 7:00 PM | 9:00 PM  (Philippine Time / UTC+8)

Safe to trigger on every PC startup — a once-per-day guard ensures it
only uploads once per calendar day no matter how many times it runs.

YouTube handles the publishing automatically, so your PC can be off
after the script finishes.

Per-video customisation
───────────────────────
Place a .txt file in scripts/ with the same stem as the video:
  scripts/my_clip.txt  ←→  queue/my_clip.mp4

Format:
  TITLE: Your Custom Title
  ---
  Your description, multiple lines, emojis, hashtags…

If no script file exists the defaults from config.py are used.
"""

import re
import csv
import random
import shutil
import subprocess
import logging
import webbrowser
import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.APP_LOG, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ONCE-PER-DAY GUARD
# ─────────────────────────────────────────────────────────────────────────────

def already_ran_today() -> bool:
    if not config.LAST_RUN.exists():
        return False
    today = datetime.now(config.PHT).strftime("%Y-%m-%d")
    return config.LAST_RUN.read_text(encoding="utf-8").strip() == today


def mark_ran_today():
    today = datetime.now(config.PHT).strftime("%Y-%m-%d")
    config.LAST_RUN.write_text(today, encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# SCRIPT-TO-VIDEO LINKING
# ─────────────────────────────────────────────────────────────────────────────

def read_script(video: Path) -> tuple[str | None, str | None]:
    """
    Look for  scripts/<video_stem>.txt  and parse:
      Line 1 → TITLE: <title>
      Line 2 → ---  (separator)
      Rest   → description

    Returns (title, description) or (None, None) if no script file exists
    or the file is blank / malformed.
    """
    script_file = config.SCRIPTS_DIR / (video.stem + ".txt")
    if not script_file.exists():
        return None, None

    raw = script_file.read_text(encoding="utf-8").strip()
    if not raw:
        return None, None

    lines = raw.splitlines()

    # Parse TITLE line
    title = None
    if lines[0].upper().startswith("TITLE:"):
        title = lines[0][6:].strip() or None

    # Find separator and extract description
    description = None
    try:
        sep_idx = next(i for i, ln in enumerate(lines) if ln.strip() == "---")
        desc_lines = lines[sep_idx + 1:]
        description = "\n".join(desc_lines).strip() or None
    except StopIteration:
        # No separator — treat everything after line 1 as description
        if len(lines) > 1:
            description = "\n".join(lines[1:]).strip() or None

    return title, description


# ─────────────────────────────────────────────────────────────────────────────
# LOGO AUTO-DETECTION
# ─────────────────────────────────────────────────────────────────────────────

_LOGO_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def get_logo() -> Path | None:
    """Return the first image file found in LOGO/, or None."""
    if not config.LOGO_DIR.exists():
        return None
    for f in sorted(config.LOGO_DIR.iterdir()):
        if f.suffix.lower() in _LOGO_EXTS:
            return f
    return None


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO QUEUE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_number(p: Path) -> int:
    """Sort key: extract trailing (NNN) from filename, else 999_999."""
    m = re.search(r"\((\d+)\)", p.name)
    return int(m.group(1)) if m else 999_999


def already_uploaded() -> set[str]:
    done: set[str] = set()
    if config.LOG_FILE.exists():
        with open(config.LOG_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add(row["filename"])
    return done


def get_uploaded_count() -> int:
    if not config.LOG_FILE.exists():
        return 0
    with open(config.LOG_FILE, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def get_next_videos(count: int) -> list[Path]:
    done       = already_uploaded()
    candidates = [
        f for f in config.QUEUE_DIR.rglob("*.mp4")
        if f.name not in done
    ]
    candidates.sort(key=_extract_number)
    return candidates[:count]


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE SLOT CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

def get_last_scheduled_time() -> "datetime | None":
    """
    Parse upload_log.csv and return the latest 'scheduled_for' timestamp.
    Used to prevent double-booking a slot that a previous run already claimed.
    """
    if not config.LOG_FILE.exists():
        return None
    latest = None
    with open(config.LOG_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["scheduled_for"], "%Y-%m-%d %H:%M PHT")
                t = t.replace(tzinfo=config.PHT)
                if latest is None or t > latest:
                    latest = t
            except (ValueError, KeyError):
                pass
    return latest


def get_schedule_slots(total: int) -> list[datetime]:
    """
    Return `total` upcoming PHT time-slots (7AM, 9AM, 7PM, 9PM).

    Always starts AFTER the latest slot already logged, so consecutive
    daily runs never overlap onto the same day slots.
    """
    now       = datetime.now(config.PHT)
    min_start = now + timedelta(minutes=30)

    last_sched = get_last_scheduled_time()
    if last_sched is not None and last_sched >= min_start:
        min_start = last_sched + timedelta(minutes=1)

    slots      = []
    check_date = min_start.date()

    while len(slots) < total:
        for h, m in config.UPLOAD_TIMES:
            candidate = datetime(
                check_date.year, check_date.month, check_date.day,
                h, m, 0, tzinfo=config.PHT,
            )
            if candidate >= min_start:
                slots.append(candidate)
                if len(slots) >= total:
                    break
        check_date += timedelta(days=1)

    return slots


# ─────────────────────────────────────────────────────────────────────────────
# BGM HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_MUSIC_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".mpga"}


def get_random_bgm() -> Path | None:
    # Respect the BGM toggle from setup.py
    if not config.BGM_ENABLED:
        log.info("   🎵 BGM: disabled")
        return None
    if not config.BGM_DIR.exists():
        return None
    tracks = [f for f in config.BGM_DIR.iterdir() if f.suffix.lower() in _MUSIC_EXTS]
    if not tracks:
        return None
    chosen = random.choice(tracks)
    log.info(f"   🎵 BGM: {chosen.name}  (level {int(config.MUSIC_VOLUME * 100)})")
    return chosen


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO PROCESSING  (FFmpeg)
# ─────────────────────────────────────────────────────────────────────────────

def process_video(src: Path, upload_index: int) -> Path | None:
    """Apply watermark + volume boost (+ optional BGM) via FFmpeg."""
    config.PROC_DIR.mkdir(parents=True, exist_ok=True)
    out = config.PROC_DIR / f"proc_{src.name}"
    if out.exists():
        out.unlink()

    logo  = get_logo()
    music = get_random_bgm()

    # Watermark position — mode controlled by config.WATERMARK_MODE (rotate / random / fixed)
    label, coords = config.get_watermark_coords(upload_index)
    log.info(f"   🖼️  Watermark corner: {label}  (mode: {config.WATERMARK_MODE})")

    if logo and music:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(src),
            "-i", str(logo),
            "-stream_loop", "-1", "-i", str(music),
            "-filter_complex", (
                f"[1:v]scale={config.LOGO_WIDTH}:-1[logo];"
                f"[0:v][logo]overlay={coords}[v];"
                f"[0:a]volume={config.VOLUME_BOOST}[orig];"
                f"[2:a]volume={config.MUSIC_VOLUME}[bg];"
                f"[orig][bg]amix=inputs=2:duration=first:dropout_transition=0[a]"
            ),
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out),
        ]
    elif logo:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(src),
            "-i", str(logo),
            "-filter_complex",
            f"[1:v]scale={config.LOGO_WIDTH}:-1[logo];[0:v][logo]overlay={coords}",
            "-af", f"volume={config.VOLUME_BOOST}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out),
        ]
    else:
        # No logo — just boost the audio
        log.warning("   ⚠️  No logo found in LOGO/ — skipping watermark")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(src),
            "-af", f"volume={config.VOLUME_BOOST}",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"   ❌ FFmpeg error:\n{result.stderr[-2000:]}")
        return None

    log.info(f"   ✅ Processed: {out.name}")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# YOUTUBE AUTH & UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

def get_youtube():
    creds = None
    if config.TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(config.TOKEN_FILE), config.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Try to open OAuth in Chrome Profile 1 (Limitless_Minds)
            chrome_exe    = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            original_open = webbrowser.open

            def open_in_profile(url, new=0, autoraise=True):
                try:
                    subprocess.Popen([chrome_exe, "--profile-directory=Profile 1", "--new-window", url])
                    return True
                except FileNotFoundError:
                    return original_open(url, new, autoraise)

            webbrowser.open = open_in_profile
            try:
                flow  = InstalledAppFlow.from_client_secrets_file(str(config.SECRETS_FILE), config.SCOPES)
                creds = flow.run_local_server(port=0)
            finally:
                webbrowser.open = original_open

        with open(config.TOKEN_FILE, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_scheduled(youtube, video_path: Path, title: str, description: str,
                     publish_at: datetime) -> str:
    body = {
        "snippet": {
            "title":       title,
            "description": description,
            "tags":        config.DEFAULT_TAGS,
            "categoryId":  config.CATEGORY_ID,
        },
        "status": {
            "privacyStatus":           "private",   # required for scheduled publish
            "publishAt":               publish_at.isoformat(),
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(
        str(video_path), mimetype="video/mp4",
        resumable=True, chunksize=5 * 1024 * 1024,
    )
    req      = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            log.info(f"   ⬆️  {int(status.progress() * 100)}%")

    vid_id = response.get("id", "UNKNOWN")
    log.info(f"   🎉 Uploaded! https://youtu.be/{vid_id}")
    log.info(f"   🕐 Publishes: {publish_at.strftime('%b %d %Y %I:%M %p')} PHT")
    return vid_id


# ─────────────────────────────────────────────────────────────────────────────
# LOG & CLEANUP
# ─────────────────────────────────────────────────────────────────────────────

def log_upload(filename: str, video_id: str, title: str, publish_at: datetime):
    header = not config.LOG_FILE.exists()
    with open(config.LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["filename", "video_id", "title", "scheduled_for", "uploaded_at"]
        )
        if header:
            writer.writeheader()
        writer.writerow({
            "filename":      filename,
            "video_id":      video_id,
            "title":         title,
            "scheduled_for": publish_at.strftime("%Y-%m-%d %H:%M PHT"),
            "uploaded_at":   datetime.now(config.PHT).strftime("%Y-%m-%d %H:%M:%S"),
        })


def move_to_done(src: Path):
    config.DONE_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.DONE_DIR / src.name
    shutil.move(str(src), str(dest))
    log.info(f"   📦 Moved to done/")


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def send_discord_notification(video_id: str, title: str, publish_at: datetime):
    if not config.DISCORD_WEBHOOK_URL:
        return
        
    url = f"https://youtu.be/{video_id}"
    pub_time = publish_at.strftime('%b %d %Y %I:%M %p PHT')
    
    payload = {
        "content": None,
        "embeds": [
            {
                "title": "🎬 New Short Scheduled!",
                "description": f"**{title}**\n\nScheduled to publish at:\n`{pub_time}`\n\n[Watch Video]({url})",
                "color": 16711680,
                "author": {
                    "name": "YT Shorts Autopilot"
                }
            }
        ]
    }
    
    req = urllib.request.Request(
        config.DISCORD_WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'User-Agent': 'YTShortsAutopilot/1.0', 'Content-Type': 'application/json'}
    )
    
    try:
        urllib.request.urlopen(req)
        log.info("   🔔 Discord notification sent!")
    except Exception as e:
        log.warning(f"   ⚠️ Failed to send Discord notification: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run_daily_batch():
    log.info("=" * 60)
    log.info("  🚀 yt-shorts-autopilot — Daily Batch Upload")
    log.info("=" * 60)

    # Once-per-day guard
    if already_ran_today():
        log.info("✅ Already ran today — nothing to do. Exiting.")
        log.info("=" * 60)
        return

    videos = get_next_videos(config.VIDEOS_PER_RUN)
    if not videos:
        log.info("✅ Queue is empty — no videos left to upload.")
        return

    slots        = get_schedule_slots(len(videos))
    already_done = get_uploaded_count()

    log.info(f"📦 Videos to upload : {len(videos)}")
    log.info(f"📅 First slot       : {slots[0].strftime('%b %d %Y %I:%M %p PHT')}")
    log.info(f"📅 Last slot        : {slots[-1].strftime('%b %d %Y %I:%M %p PHT')}")
    log.info("")

    youtube = get_youtube()
    success = 0

    for i, (src, publish_at) in enumerate(zip(videos, slots)):
        upload_index = already_done + i

        # ── Resolve title & description ───────────────────────────────────
        script_title, script_desc = read_script(src)
        title       = script_title or config.DEFAULT_TITLE_TEMPLATE.format(n=upload_index + 1)
        description = script_desc  or config.DEFAULT_DESCRIPTION

        log.info(f"[{i + 1}/{len(videos)}] {src.name}")
        log.info(f"   📌 Title      : {title}")
        log.info(f"   📝 Script     : {'✅ custom' if script_title else '⬜ default'}")
        log.info(f"   🕐 Publish at : {publish_at.strftime('%b %d %Y %I:%M %p')} PHT")

        processed = process_video(src, upload_index)
        if processed is None:
            log.error("   ❌ Skipping — FFmpeg failed.")
            continue

        try:
            vid_id = upload_scheduled(youtube, processed, title, description, publish_at)
            log_upload(src.name, vid_id, title, publish_at)
            send_discord_notification(vid_id, title, publish_at)
            move_to_done(src)
            success += 1
        except Exception as exc:
            log.exception(f"   ❌ Upload error: {exc}")
        finally:
            if processed.exists():
                processed.unlink()

        log.info("")

    if success > 0:
        mark_ran_today()

    log.info("=" * 60)
    log.info(f"✅ Done! {success}/{len(videos)} videos scheduled on YouTube.")
    log.info("   You can now turn off your PC.")
    log.info("   YouTube will publish at the scheduled times automatically.")
    log.info("=" * 60)


if __name__ == "__main__":
    try:
        run_daily_batch()
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"  ❌ ERROR: {e}")
        print("=" * 60)
        log.exception("Unexpected error in run_daily_batch")
    input("\nPress Enter to exit …")
