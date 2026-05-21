"""
generate_scripts.py — Auto-generate script templates for queued videos
=======================================================================
Run this after adding new .mp4 files to queue/.

  python generate_scripts.py

For every video in queue/ that does NOT already have a matching .txt in
scripts/, this tool creates a template like:

  scripts/my_video_name.txt
  ─────────────────────────
  TITLE: my_video_name
  ---
  Welcome to Limitless Minds …   (default description from config.py)

You can then open each .txt and fill in a custom title / description.
If you leave the file as-is, daily_batch.py will use the defaults from
config.py instead — so filling in scripts is entirely optional.

Script file format
──────────────────
  Line 1:          TITLE: <your title here>
  Line 2:          ---
  Remaining lines: description (supports multiple lines, emojis, hashtags)

If the file is blank or missing, daily_batch.py falls back to the default
title template ("Daily Motivation #N") and DEFAULT_DESCRIPTION from config.py.
"""

from pathlib import Path
import config


# ─────────────────────────────────────────────────────────────────────────────

TEMPLATE = """\
TITLE: {title}
---
{description}
"""


def find_videos() -> list[Path]:
    """Return all .mp4 files inside queue/ sorted by filename."""
    return sorted(
        config.QUEUE_DIR.rglob("*.mp4"),
        key=lambda p: p.name.lower(),
    )


def script_path_for(video: Path) -> Path:
    """Return the expected .txt path in scripts/ for a given video."""
    return config.SCRIPTS_DIR / (video.stem + ".txt")


def create_template(video: Path, script_file: Path):
    """Write a blank template .txt for the video."""
    content = TEMPLATE.format(
        title=video.stem,
        description=config.DEFAULT_DESCRIPTION,
    )
    script_file.write_text(content, encoding="utf-8")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate script template .txt files for queued videos."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview which files would be created without writing anything."
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  generate_scripts.py — Script Template Generator")
    if args.dry_run:
        print("  [DRY RUN] No files will be written.")
    print("=" * 60)

    # Ensure scripts/ folder exists
    config.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    videos = find_videos()

    if not videos:
        print("\nℹ️  No .mp4 files found in queue/")
        print("   Add your videos to queue/ first, then re-run this script.")
        input("\nPress Enter to exit …")
        return

    print(f"\n📂 Found {len(videos)} video(s) in queue/\n")

    created  = 0
    skipped  = 0

    for video in videos:
        script = script_path_for(video)
        if script.exists():
            print(f"  ⏭️  Already exists : {script.name}")
            skipped += 1
        else:
            if not args.dry_run:
                create_template(video, script)
                print(f"  ✅ Created         : {script.name}")
            else:
                print(f"  ✅ Would create    : {script.name}")
            created += 1

    print()
    print("=" * 60)
    if args.dry_run:
        print(f"  ✅ {created} new script(s) would be created  |  {skipped} already existed")
    else:
        print(f"  ✅ {created} new script(s) created  |  {skipped} already existed")
    print()
    print("  Next: open scripts/ and customise each .txt file.")
    print("  Format:")
    print("    Line 1  →  TITLE: Your Custom Title")
    print("    Line 2  →  ---")
    print("    Rest    →  Description, hashtags, links …")
    print()
    print("  Tip: leave a file blank to use the defaults from config.py.")
    print("=" * 60)

    input("\nPress Enter to exit …")


if __name__ == "__main__":
    main()
