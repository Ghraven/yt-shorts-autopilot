"""
setup.py — yt-shorts-autopilot  |  Interactive Setup Wizard
============================================================
Run this ONCE before using daily_batch.py, or re-run at any time to
change your settings.

  python setup.py

All choices are saved to  settings.json  in the project folder.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
#  ANSI COLOR SYSTEM
#  Works on Windows 10+, macOS, Linux.  Falls back to plain text gracefully.
# ─────────────────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    os.system("")          # enable ANSI escape codes in Windows console

_NO_COLOR = not sys.stdout.isatty() or os.environ.get("NO_COLOR")

def _c(*codes: str) -> str:
    return "" if _NO_COLOR else "\033[" + ";".join(codes) + "m"

# Resets
RESET  = _c("0")
BOLD   = _c("1")
DIM    = _c("2")

# Foreground colours
BLACK  = _c("30")
RED    = _c("91")
GREEN  = _c("92")
YELLOW = _c("93")
BLUE   = _c("94")
MAGENTA= _c("95")
CYAN   = _c("96")
WHITE  = _c("97")

# Bright combos  (most useful for headings)
B_RED    = BOLD + RED
B_GREEN  = BOLD + GREEN
B_YELLOW = BOLD + YELLOW
B_CYAN   = BOLD + CYAN
B_WHITE  = BOLD + WHITE
B_MAGENTA= BOLD + MAGENTA

# Semantic aliases
OK    = B_GREEN          # ✅  success
WARN  = B_YELLOW         # ⚠️  caution
ERR   = B_RED            # ❌  error
INFO  = CYAN             # ℹ️  info
HDR   = B_CYAN           # section heading
NUM   = B_YELLOW         # menu numbers
OPT   = WHITE            # menu option text
DIMW  = DIM + WHITE      # secondary / hint text
STAR  = B_GREEN          # ★  recommended tag
PRM   = B_WHITE          # input prompt

# ─────────────────────────────────────────────────────────────────────────────
#  STATIC DATA
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
SETTINGS_FILE = BASE_DIR / "settings.json"

FOLDERS = {
    "queue":     "Your .mp4 Short videos  (oldest uploaded first)",
    "done":      "Videos are moved here automatically after uploading",
    "processed": "Temporary FFmpeg working folder  (auto-cleaned)",
    "BGM":       "Background music — .mp3 / .wav / .m4a  (optional)",
    "LOGO":      "Your channel watermark image — PNG recommended",
    "scripts":   "Optional per-video title + description .txt files",
}

UNITS_PER_UPLOAD = 1_600
DAILY_QUOTA      = 10_000

TIME_PRESETS: dict[int, list] = {
    2: [(7, 0), (19, 0)],
    4: [(7, 0), (9, 0), (19, 0), (21, 0)],
    6: [(7, 0), (9, 0), (12, 0), (15, 0), (19, 0), (21, 0)],
}

LOGO_SIZES = {
    "Small  (80 px)":   80,
    "Medium (130 px)":  130,
    "Large  (180 px)":  180,
    "Custom …":         None,
}

# YouTube category is fixed to "People & Blogs" (id=22) — best fit for
# motivational Shorts.  Change CATEGORY_ID in config.py if needed.
YT_CATEGORY_ID = "22"


# ─────────────────────────────────────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def clr(text: str, color: str = "") -> str:
    """Wrap text in a colour then reset."""
    return f"{color}{text}{RESET}" if color else text


def banner():
    w = 62
    inner = "  🎬  YT SHORTS AUTOPILOT  ·  Setup Wizard  🚀"
    pad   = " " * max(0, w - 2 - len(inner))
    print()
    print(B_CYAN + "╔" + "═" * w + "╗" + RESET)
    print(B_CYAN + "║" + RESET + inner + pad + B_CYAN + " ║" + RESET)
    print(B_CYAN + "╚" + "═" * w + "╝" + RESET)


def section(step: int, total: int, title: str, icon: str = "⚙️"):
    label = f"  {icon}  STEP {step} OF {total} — {title}"
    bar   = "─" * 60
    print()
    print(HDR + "┌" + bar + "┐" + RESET)
    print(HDR + "│" + RESET + f"{B_WHITE}{label:<60}{RESET}" + HDR + "│" + RESET)
    print(HDR + "└" + bar + "┘" + RESET)
    print()


def ok(msg: str):
    print(f"  {OK}✅{RESET}  {msg}")


def warn(msg: str):
    print(f"  {WARN}⚠️ {RESET}  {msg}")


def err(msg: str):
    print(f"  {ERR}❌{RESET}  {msg}")


def info(msg: str):
    print(f"  {INFO}ℹ️ {RESET}  {msg}")


def divider():
    print(f"  {DIMW}{'─' * 56}{RESET}")


def fmt_time(h: int, m: int) -> str:
    return datetime(2000, 1, 1, h, m).strftime("%I:%M %p").lstrip("0")


def fmt_times(times: list) -> str:
    return "  │  ".join(clr(fmt_time(h, m), B_CYAN) for h, m in times)


# ─────────────────────────────────────────────────────────────────────────────
#  INPUT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _prompt(text: str) -> str:
    return input(f"\n  {PRM}▸ {RESET}{text}: ").strip()


def ask_menu(options: list[str], default: int = 1, stars: set[int] = None) -> int:
    """
    Print a numbered menu and return the chosen 1-based index.
    Items in `stars` get a  ★ recommended  tag.
    """
    stars = stars or set()
    print()
    for i, opt in enumerate(options, 1):
        is_def = (i == default)
        bracket = f"{B_GREEN}[{i}]{RESET}" if is_def else f"  {NUM}{i}{RESET}"
        star_tag = f"  {STAR}★ recommended{RESET}" if i in stars else ""
        dim_hint = f"  {DIMW}← default{RESET}" if is_def else ""
        print(f"  {bracket}  {OPT}{opt}{RESET}{star_tag}{dim_hint}")

    while True:
        raw = _prompt(f"Choose  {DIMW}[1–{len(options)}]  default={default}{RESET}")
        if raw == "":
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw)
        warn(f"Please enter a number between 1 and {len(options)}.")


def ask_int(label: str, lo: int, hi: int, default: int | None = None,
            allow_skip: bool = False) -> int | None:
    """
    Ask for an integer in [lo, hi].
    If allow_skip=True, typing 'skip' returns None.
    """
    hint_parts = [f"{lo}–{hi}"]
    if default is not None:
        hint_parts.append(f"default={default}")
    if allow_skip:
        hint_parts.append("type 'skip' to keep current")
    hint = "  " + DIMW + f"({',  '.join(hint_parts)})" + RESET

    while True:
        raw = _prompt(f"{label}{hint}")
        if raw == "" and default is not None:
            return default
        if allow_skip and raw.lower() == "skip":
            return None
        if raw.isdigit() and lo <= int(raw) <= hi:
            return int(raw)
        warn(f"Enter a number {lo}–{hi}" + (" or type 'skip'" if allow_skip else "") + ".")


def ask_yes_no(label: str, default: bool = True) -> bool:
    hint = clr("Y/n", B_GREEN) if default else clr("y/N", DIMW)
    while True:
        raw = _prompt(f"{label}  [{hint}]")
        if raw == "":
            return default
        if raw.lower() in ("y", "yes"):
            return True
        if raw.lower() in ("n", "no"):
            return False
        warn("Type  Y  or  N.")


def ask_text(label: str, default: str) -> str:
    raw = _prompt(f"{label}  {DIMW}[{default}]{RESET}")
    return raw if raw else default


def ask_time_slot(index: int) -> tuple[int, int]:
    print(f"  {DIMW}Format: HH:MM in 24-hour  (e.g. 07:00 = 7 AM  |  19:30 = 7:30 PM){RESET}")
    while True:
        raw = _prompt(f"Upload {NUM}{index}{RESET} time  HH:MM")
        parts = raw.split(":")
        if len(parts) == 2:
            try:
                h, m = int(parts[0]), int(parts[1])
                if 0 <= h <= 23 and 0 <= m <= 59:
                    return h, m
            except ValueError:
                pass
        warn("Invalid format — use HH:MM  (e.g. 07:00 or 21:30)")


# ─────────────────────────────────────────────────────────────────────────────
#  SETUP STEPS
# ─────────────────────────────────────────────────────────────────────────────

TOTAL_STEPS = 11


def step_install(step: int):
    section(step, TOTAL_STEPS, "Installing Python packages", "📦")
    req = BASE_DIR / "requirements.txt"
    if not req.exists():
        warn("requirements.txt not found — skipping pip install")
        return True
    print(f"  {INFO}Running pip install …{RESET}")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req), "--quiet"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        err(f"pip install failed:\n{result.stderr[-800:]}")
        return False
    ok("All packages installed")
    return True


def step_folders(step: int):
    section(step, TOTAL_STEPS, "Creating folder structure", "📁")
    for name in FOLDERS:
        folder = BASE_DIR / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ".gitkeep").touch(exist_ok=True)
        ok(f"{B_WHITE}{name}/{RESET}")


def step_guide(step: int):
    section(step, TOTAL_STEPS, "Where to put your files", "📂")
    max_len = max(len(k) for k in FOLDERS)
    for name, desc in FOLDERS.items():
        print(f"  {B_CYAN}📂  {B_WHITE}{name:<{max_len}}{RESET}  {DIMW}→{RESET}  {WHITE}{desc}{RESET}")
    print()
    divider()
    print(f"  {DIMW}Tip: Scripts are OPTIONAL.  Run  generate_scripts.py  to auto-create")
    print(f"       title/description templates for each video in queue/.{RESET}")
    _prompt(f"Press {B_WHITE}Enter{RESET} to continue")


def step_uploads_per_day(step: int) -> int:
    section(step, TOTAL_STEPS, "Uploads per day", "📤")
    units = lambda n: clr(f"~{n * UNITS_PER_UPLOAD:,} quota units", DIMW)
    options = [
        f"2 uploads / day     {units(2)}",
        f"4 uploads / day     {units(4)}",
        f"6 uploads / day     {units(6)}",
        f"Custom              (enter your own number)",
    ]
    print(f"  {DIMW}YouTube free quota: {DAILY_QUOTA:,} units / day  ·  ~{UNITS_PER_UPLOAD:,} units per upload{RESET}")
    print(f"  {DIMW}Note: 7 or more uploads/day exceeds the free quota — you'll need to")
    print(f"        request a quota increase at console.cloud.google.com{RESET}")
    choice = ask_menu(options, default=2, stars={2})

    if choice == 1:
        n = 2
    elif choice == 2:
        n = 4
    elif choice == 3:
        n = 6
    else:
        print()
        n = ask_int("How many uploads per day?", 1, 50, default=4)
        if n >= 7:
            print()
            warn(f"{n} uploads/day ≈ {n * UNITS_PER_UPLOAD:,} units  —  exceeds the {DAILY_QUOTA:,} free limit")
            print(f"  {DIMW}To increase your quota:{RESET}")
            print(f"  {DIMW}  1. Go to  {CYAN}https://console.cloud.google.com/{RESET}")
            print(f"  {DIMW}  2. IAM & Admin → Quotas → search 'YouTube Data API v3'{RESET}")
            print(f"  {DIMW}  3. Request an increase  (Google usually approves legit channels){RESET}")

    ok(f"Uploads per day set to  {B_WHITE}{n}{RESET}")
    return n


def step_upload_times(step: int, count: int) -> list:
    section(step, TOTAL_STEPS, "Upload time slots  (Philippine Time / UTC+8)", "🕐")
    print(f"  You chose  {B_WHITE}{count}{RESET}  upload(s) per day.\n")

    if count in TIME_PRESETS:
        preset = TIME_PRESETS[count]
        print(f"  {DIMW}Recommended:{RESET}  {fmt_times(preset)}")
        if ask_yes_no("Use recommended times?", default=True):
            for i, (h, m) in enumerate(preset, 1):
                ok(f"Upload {i}  →  {B_CYAN}{fmt_time(h, m)}{RESET}  PHT")
            return preset

    print()
    info("Enter each time in 24-hour HH:MM format.")
    times, used = [], set()
    for i in range(1, count + 1):
        while True:
            slot = ask_time_slot(i)
            if slot in used:
                warn(f"{fmt_time(*slot)} is already taken — pick a different time.")
            else:
                used.add(slot)
                times.append(slot)
                ok(f"Upload {i}  →  {B_CYAN}{fmt_time(*slot)}{RESET}  PHT")
                break

    times.sort()
    print()
    ok(f"Schedule:  {fmt_times(times)}")
    return times


def step_video_volume(step: int) -> int:
    section(step, TOTAL_STEPS, "Original video volume boost", "🔊")
    print(f"  Increase the volume of the source video audio.")
    print(f"  {DIMW}0%  = no change  ·  30% = max (+30%, recommended for Shorts){RESET}")
    print()
    pct = ask_int("Volume boost", 0, 30, default=30)
    if pct == 0:
        info("Original audio will not be changed.")
    else:
        ok(f"Video audio will be boosted by  {B_WHITE}+{pct}%{RESET}")
    return pct


def step_bgm(step: int) -> tuple[bool, int | None]:
    section(step, TOTAL_STEPS, "Background music (BGM)", "🎵")
    print(f"  Mix a background track from your  {B_CYAN}BGM/{RESET}  folder under the video.")
    print()

    enabled = ask_yes_no("Enable background music?", default=True)
    if not enabled:
        info("BGM disabled — videos will use only the original audio.")
        return False, None

    print()
    print(f"  Set the BGM volume level  {DIMW}(0 = silent  ·  100 = full BGM volume){RESET}")
    print(f"  {DIMW}Typical value: 12–20  (subtle background feel){RESET}")
    print()

    level = ask_int("BGM volume", 0, 100, default=12, allow_skip=True)
    if level is None:
        info(f"BGM volume kept at default  {B_WHITE}(12){RESET}")
        level = 12

    ok(f"BGM enabled  ·  volume level  {B_WHITE}{level}{RESET}")
    return True, level


def step_logo_position(step: int) -> str:
    section(step, TOTAL_STEPS, "Watermark / logo position", "🖼️")
    options = [
        "Bottom-right corner",
        "Bottom-left corner",
        "Top-left corner",
        "Top-right corner",
        "Rotate  —  cycles  bottom-right → bottom-left → top-left → top-right",
        "Random  —  picks a random corner each upload",
    ]
    choice = ask_menu(options, default=5, stars={5})
    mapping = {
        1: "bottom-right",
        2: "bottom-left",
        3: "top-left",
        4: "top-right",
        5: "rotate",
        6: "random",
    }
    pos = mapping[choice]
    ok(f"Logo position:  {B_WHITE}{pos.capitalize()}{RESET}")
    return pos


def step_logo_size(step: int) -> int:
    section(step, TOTAL_STEPS, "Watermark / logo size", "🔍")
    print(f"  {DIMW}Controls how wide the watermark appears on the video.{RESET}")
    options = list(LOGO_SIZES.keys())
    choice  = ask_menu(options, default=2, stars={2})
    label   = options[choice - 1]
    px      = LOGO_SIZES[label]

    if px is None:
        print()
        px = ask_int("Custom logo width in pixels", 40, 400, default=130)

    ok(f"Logo width:  {B_WHITE}{px} px{RESET}")
    return px


def step_channel_info(step: int) -> tuple[str, str]:
    section(step, TOTAL_STEPS, "Channel & title settings", "✏️")
    print(f"  {DIMW}Used in the default video description and title template.{RESET}\n")
    handle   = ask_text("Channel handle  (e.g. @Limitless_Minds)", "@YourChannel")
    template = ask_text(
        f"Title template  {DIMW}(use {{n}} for number){RESET}",
        "Daily Motivation #{n}",
    )
    ok(f"Handle:  {B_WHITE}{handle}{RESET}")
    ok(f"Title template:  {B_WHITE}{template}{RESET}")
    return handle, template


def step_discord_webhook(step: int) -> str:
    section(step, TOTAL_STEPS, "Discord Webhook Notification", "🔔")
    print(f"  {DIMW}If provided, a message will be sent to this Discord channel when a video uploads.{RESET}")
    print(f"  {DIMW}Leave blank to disable.{RESET}\n")
    url = ask_text("Discord Webhook URL", "")
    if url:
        ok(f"Discord Webhook: {B_WHITE}Enabled{RESET}")
    else:
        info("Discord Webhook: Disabled")
    return url


def step_dependencies():
    print()
    print(f"  {HDR}┌{'─' * 54}┐{RESET}")
    print(f"  {HDR}│{RESET}  {'Checking dependencies':<52}  {HDR}│{RESET}")
    print(f"  {HDR}└{'─' * 54}┘{RESET}\n")

    # FFmpeg
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        ok(f"FFmpeg  {DIMW}{ffmpeg}{RESET}")
    else:
        err("FFmpeg NOT found in PATH")
        print(f"  {DIMW}Download: https://www.gyan.dev/ffmpeg/builds/{RESET}")
        print(f"  {DIMW}After install, add the bin/ folder to your Windows PATH.{RESET}")

    # Credentials
    secrets = BASE_DIR / "client_secrets.json"
    if secrets.exists():
        ok("client_secrets.json found")
    else:
        warn("client_secrets.json NOT found")
        print(f"  {DIMW}See README.md → 'Set up YouTube OAuth credentials'{RESET}")

    # Logo
    logo_exts = {".png", ".jpg", ".jpeg", ".webp"}
    logos     = [f for f in (BASE_DIR / "LOGO").iterdir() if f.suffix.lower() in logo_exts]
    if logos:
        ok(f"Logo image  {DIMW}{logos[0].name}{RESET}")
    else:
        warn(f"No logo image in  {B_WHITE}LOGO/{RESET}  — drop a PNG or JPG there.")

    # BGM
    bgm_exts = {".mp3", ".wav", ".m4a", ".aac", ".mpga"}
    tracks   = [f for f in (BASE_DIR / "BGM").iterdir() if f.suffix.lower() in bgm_exts]
    if tracks:
        ok(f"BGM files:  {DIMW}{len(tracks)} track(s) found{RESET}")
    else:
        info(f"No music in  {B_WHITE}BGM/{RESET}  (optional — ok to leave empty)")

    # Queue
    videos = list((BASE_DIR / "queue").rglob("*.mp4"))
    if videos:
        ok(f"Videos in queue:  {DIMW}{len(videos)} .mp4 file(s) ready{RESET}")
    else:
        info(f"Queue is empty — drop your .mp4 Shorts into  {B_WHITE}queue/{RESET}  before uploading")


def save_settings(s: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    print()
    ok(f"Settings saved to  {B_WHITE}settings.json{RESET}")


def print_summary(s: dict):
    print()
    print(B_CYAN + "╔" + "═" * 62 + "╗" + RESET)
    print(B_CYAN + "║" + RESET + f"  {'✅  SETUP COMPLETE — YOUR PIPELINE IS CONFIGURED':<60}  " + B_CYAN + "║" + RESET)
    print(B_CYAN + "╚" + "═" * 62 + "╝" + RESET)
    print()

    n      = s["uploads_per_day"]
    times  = fmt_times([tuple(t) for t in s["upload_times"]])
    vol    = s["video_volume_boost_percent"]
    bgm_on = s["bgm_enabled"]
    bgm_v  = s["bgm_volume"]
    pos    = s["logo_position"].capitalize()
    px     = s["logo_width"]
    hdl    = s["channel_handle"]
    tmpl   = s["default_title_template"]

    rows = [
        ("📤  Uploads per day",    str(n)),
        ("🕐  Schedule (PHT)",     times),
        ("🔊  Video volume boost", f"+{vol}%"),
        ("🎵  BGM",                f"Enabled · level {bgm_v}" if bgm_on else "Disabled"),
        ("🖼️   Logo position",      pos),
        ("🔍  Logo width",          f"{px} px"),
        ("✏️   Channel handle",     hdl),
        ("📝  Title template",      tmpl),
        ("🔔  Discord Webhook",     "Enabled" if s.get("discord_webhook_url") else "Disabled"),
    ]
    for label, value in rows:
        print(f"  {DIMW}{label:<28}{RESET}  {B_WHITE}{value}{RESET}")

    print()
    print(f"  {HDR}{'─' * 58}{RESET}")
    print(f"\n  {B_WHITE}Next steps:{RESET}\n")
    steps = [
        ("client_secrets.json", "Place it in this folder  (see README.md for OAuth setup)"),
        ("queue/",              "Drop your .mp4 Shorts here"),
        ("BGM/",                "Drop background music here  (optional)"),
        ("LOGO/",               "Drop your logo/watermark image here"),
        ("generate_scripts.py", "Run to create title/description templates  (optional)"),
        ("daily_batch.py",      "Run to start uploading!  (first run = one-time browser login)"),
    ]
    for i, (item, desc) in enumerate(steps, 1):
        print(f"  {NUM}{i}.{RESET}  {B_CYAN}{item:<26}{RESET}  {DIMW}{desc}{RESET}")

    print()
    info(f"Schedule  {B_WHITE}daily_batch.py{RESET}  in Windows Task Scheduler to run automatically.")
    print()
    print(B_CYAN + "═" * 64 + RESET)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    banner()
    print(f"\n  {DIMW}Configure your YouTube Shorts upload pipeline step by step.")
    print(f"  Re-run this wizard at any time to update your settings.{RESET}")

    step = 1

    # 1. Packages
    if not step_install(step):
        err("Fix the error above and re-run setup.py.")
        sys.exit(1)
    step += 1

    # 2. Folders
    step_folders(step);  step += 1

    # 3. File guide
    step_guide(step);    step += 1

    # 4. Uploads per day
    uploads = step_uploads_per_day(step);  step += 1

    # 5. Time slots
    times = step_upload_times(step, uploads);  step += 1

    # 6. Video volume
    vol = step_video_volume(step);  step += 1

    # 7. BGM
    bgm_enabled, bgm_volume = step_bgm(step);  step += 1
    if bgm_volume is None:
        bgm_volume = 12

    # 8. Logo position
    logo_pos = step_logo_position(step);  step += 1

    # 9. Logo size
    logo_px = step_logo_size(step);  step += 1

    # 10. Channel info
    handle, title_tmpl = step_channel_info(step);  step += 1

    # 11. Discord webhook
    discord_url = step_discord_webhook(step);  step += 1

    # Dependency check (no step number — informational only)
    step_dependencies()

    # Save
    settings = {
        "uploads_per_day":              uploads,
        "upload_times":                 [list(t) for t in times],
        "video_volume_boost_percent":   vol,
        "bgm_enabled":                  bgm_enabled,
        "bgm_volume":                   bgm_volume,
        "logo_position":                logo_pos,
        "logo_width":                   logo_px,
        "category_id":                  YT_CATEGORY_ID,   # fixed: People & Blogs
        "channel_handle":               handle,
        "default_title_template":       title_tmpl,
        "discord_webhook_url":          discord_url,
    }
    save_settings(settings)
    print_summary(settings)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {WARN}⚠️  Setup cancelled.{RESET}")
    except Exception as exc:
        print(f"\n  {ERR}❌  Unexpected error: {exc}{RESET}")
        raise
    finally:
        input(f"\n  {DIMW}Press Enter to exit …{RESET}")
