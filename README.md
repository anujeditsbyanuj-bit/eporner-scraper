# eporner-scraper

Telethon-based async downloader + uploader. Downloads via yt-dlp with aria2c, uploads to a Telegram channel, and tracks completed downloads in an archive file.

## Run

```bash
pip install telethon rich yt-dlp

# Add links to adbatch.txt, then:
python advanced.py
```

## Features

- Disk space checks before download
- Rich progress bars
- Auto-cleanup after upload
- Dedup via archive file

## Files

- `advanced.py` — Main downloader/uploader script
- `adbatch.txt` — Queue of URLs to download
- `adarchive.txt` — Downloaded URL archive
- `downloads/` — Downloaded files (auto-cleaned)
