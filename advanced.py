API_ID = 21347898
API_HASH = "98caf2e4f0c25e142c3cbb2e36e683ef"
BOT_TOKEN = "8946367857:AAGpDdtG2ZFMG2HeZh-Ve_Ey13pyW-_xVaU"
CHAT_ID = -1003824246703

import asyncio
import os
import re
import shutil
import subprocess
import sys

from telethon import TelegramClient
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn

# ========= CONFIG =========

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
BATCH_FILE = "adbatch.txt"
ARCHIVE_FILE = "adarchive.txt"
MIN_FREE_SPACE_GB = 1


console = Console()

client = TelegramClient("session", API_ID, API_HASH)

# ========= UTIL =========

def ensure_download_dir():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_free_space_gb(path):
    total, used, free = shutil.disk_usage(path)
    return free / (1024 ** 3)


def check_disk_space():
    free = get_free_space_gb(DOWNLOAD_DIR)
    console.print(f"[cyan]馃捑 Free:[/cyan] {free:.2f} GB")

    if free < MIN_FREE_SPACE_GB:
        console.print("[red]鉂� Less than 2GB free. Exiting[/red]")
        sys.exit(1)


def extract_url(text):
    match = re.search(r'(https?://\S+)', text)
    return match.group(1) if match else None


def load_batch():
    if not os.path.exists(BATCH_FILE):
        return []

    links = []
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        for line in f:
            url = extract_url(line.strip())
            if url:
                links.append(url)

    return links


def save_batch(links):
    with open(BATCH_FILE, "w", encoding="utf-8") as f:
        for i, link in enumerate(links, 1):
            f.write(f"{i}.{link}\n")


def append_archive(link):
    with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")


def is_downloaded(link):
    if not os.path.exists(ARCHIVE_FILE):
        return False

    with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
        return link in f.read()

# ========= DOWNLOAD =========

def download_sync(url):
    cmd = [
    "yt-dlp",
    url,
    "-P", DOWNLOAD_DIR,
    "-o", "%(title)s.%(ext)s",
    "--newline",
    "--print", "after_move:filepath",

    "--external-downloader", "aria2c",
    "--external-downloader-args",
    "aria2c:-x 16 -s 16 -k 1M"
]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    file_path = None

    progress = Progress(
        TextColumn("[blue]Download"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    )

    task = progress.add_task("download", total=100)

    with progress:
        for line in process.stdout:
            line = line.strip()

            if "[download]" in line:
                m = re.search(r'(\d+(\.\d+)?)%', line)
                if m:
                    progress.update(task, completed=float(m.group(1)))

            if line.startswith(DOWNLOAD_DIR):
                file_path = line

        process.wait()

    if process.returncode == 0 and file_path and os.path.exists(file_path):
        return True, file_path

    return False, None

# ========= UPLOAD =========

async def upload_video(file_path):
    console.print(f"\n[magenta]馃摛 Uploading:[/magenta] {os.path.basename(file_path)}")

    await client.send_file(
        CHAT_ID,
        file_path,
        caption=os.path.basename(file_path),
        supports_streaming=True
    )

    console.print("[green]鉁� Uploaded[/green]")

# ========= MAIN =========

async def main():
    console.print("[bold cyan]馃殌 Telethon Downloader + Uploader[/bold cyan]\n")

    ensure_download_dir()

    links = load_batch()
    if not links:
        console.print("[yellow]鈿狅笍 No links found[/yellow]")
        return

    remaining = links.copy()
    queue = asyncio.Queue()

    async def downloader():
        for link in links:
            console.print(f"\n[white]馃敆 {link}[/white]")

            check_disk_space()

            if is_downloaded(link):
                console.print("[yellow]鈴笍 Skipped[/yellow]")
                remaining.remove(link)
                save_batch(remaining)
                continue

            success, file_path = await asyncio.to_thread(download_sync, link)

            if success:
                console.print("[green]鉁� Downloaded 鈫� queued[/green]")
                await queue.put((file_path, link))
            else:
                console.print("[red]鉂� Failed[/red]")

    async def uploader():
        while True:
            item = await queue.get()

            if item is None:
                break

            file_path, link = item

            try:
                await upload_video(file_path)

                append_archive(link)

                if link in remaining:
                    remaining.remove(link)
                    save_batch(remaining)

                os.remove(file_path)
                console.print("[red]馃棏锔� Deleted[/red]")

            except Exception as e:
                console.print(f"[red]鉂� Upload error:[/red] {e}")

            queue.task_done()

    async with client:
        up_task = asyncio.create_task(uploader())
        await downloader()
        await queue.put(None)
        await queue.join()
        await up_task

    console.print("[bold green]馃帀 Done[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
