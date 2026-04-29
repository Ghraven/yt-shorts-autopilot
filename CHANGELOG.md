# Changelog

All notable changes to YT Shorts Autopilot are documented here.

## [Unreleased]

### Planned
- Multi-channel support (switch between YouTube accounts)
- Discord webhook notification on upload
- Dry-run mode (process + log without uploading)

---

## [1.3.0] — 2025-04-30

### Added
- `.gitkeep` files in all empty directories so cloners get the full folder structure out of the box
- `CONTRIBUTING.md` and `CHANGELOG.md`

---

## [1.2.0] — 2025-03-15

### Added
- `setup.py` interactive wizard — installs deps, creates folders, guides first run
- `generate_scripts.py` — batch-creates `.txt` title/description templates for queued videos
- Upload log CSV with full history of scheduled times

### Changed
- `config.py` now loads from `settings.json` written by `setup.py` (no more manual editing)
- Watermark mode: `rotate` | `random` | fixed corner — configurable via `setup.py`

---

## [1.1.0] — 2025-02-01

### Added
- Per-video script files (`scripts/<name>.txt`) for custom titles and descriptions
- Slot-safe scheduling — never double-books the same upload time slot
- Once-per-day guard — safe to add to Windows startup

---

## [1.0.0] — 2025-01-01

### Added
- Initial release
- FFmpeg watermark + audio boost + BGM mixing pipeline
- YouTube Data API v3 OAuth upload with scheduled publish times
- 4 daily upload slots (7AM · 9AM · 7PM · 9PM PHT)
- Automatic move to `done/` after successful upload
