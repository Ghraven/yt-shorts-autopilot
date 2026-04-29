# Contributing to YT Shorts Autopilot

Thanks for your interest! Contributions of all sizes are welcome.

## Ways to contribute

- **Bug reports** — open an issue with your OS, Python version, FFmpeg version, and the full error output
- **Feature requests** — open an issue describing the use case
- **Fixes and improvements** — fork, branch, PR

## Local setup

```bash
git clone https://github.com/Ghraven/yt-shorts-autopilot
cd yt-shorts-autopilot
pip install -r requirements.txt
# Install FFmpeg and add to PATH
python setup.py   # creates folders, checks dependencies
```

You will need a `client_secrets.json` from Google Cloud Console to test real uploads.
For dry-run testing you can mock the `upload_video()` call in `daily_batch.py`.

## Project layout

| File | Purpose |
|---|---|
| `daily_batch.py` | Main entry point — run once per day |
| `config.py` | All settings (loaded from `settings.json`) |
| `setup.py` | Interactive first-run wizard |
| `generate_scripts.py` | Creates `.txt` title/description templates |

## Code style

- Python 3.10+, standard library + `google-api-python-client`
- No external frameworks beyond what's in `requirements.txt`
- Prefer explicit over clever — this runs unattended

## Pull requests

1. Fork and create a branch from `main`
2. Make your change, test it locally
3. Open a PR with a short description

No formal review process — just make sure it runs without errors on a fresh clone.
