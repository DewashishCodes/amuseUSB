#!/usr/bin/env python3
"""
Professional parallel downloader with per-song progress bars (Rich).

Usage:
    python phase3_parallel_downloader_final.py

Config at top of file:
 - USB_PATH: destination folder on your USB
 - RECS_FILE: recommendations JSON
 - MAX_THREADS: concurrency (set to 5 per your request)
 - RETRY_LIMIT: retries per song
 - FFMPEG_PATH: your ffmpeg bin folder (confirmed)
"""

import os
import json
import re
import time
import yt_dlp
import concurrent.futures
import threading
from pathlib import Path
from typing import Optional

from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    SpinnerColumn,
)

# ----------------- CONFIG -----------------
USB_PATH = r"E:\AI_Recommendations"   # Change if needed; folder will be created
RECS_FILE = "music_recommendations.json"
FFMPEG_PATH = r"D:\ffmpeg-8.0-essentials_build\bin"  # confirmed by you
MAX_THREADS = 5   # per your instruction
RETRY_LIMIT = 3
# ------------------------------------------

# Thread-safe mapping of our internal task ids to Rich task ids
task_map_lock = threading.Lock()
task_map = {}  # maps unique_id -> rich_task_id

# sanitize filename
def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180]


# Robust search with fallbacks
def search_youtube(query: str) -> Optional[str]:
    """
    Try several yt-dlp search variants; return first good YouTube watch URL or None.
    """
    search_variants = [
        f"ytsearch10:{query}",
        f"ytsearch5:{query} official audio",
        f"ytsearch5:{query} audio",
        f"ytsearch5:{query} song",
        f"ytsearch5:{query} full song",
        f"ytsearch5:{query} lyric",
        f"ytsearch5:{query} hd audio",
    ]

    ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": "in_playlist"}

    for q in search_variants:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(q, download=False)
        except Exception:
            info = None

        if not info:
            continue

        entries = info.get("entries") if isinstance(info, dict) else None
        # if single result, info may be direct dict
        if entries is None:
            entries = [info]

        if not entries:
            continue

        # prefer entries that look like videos (have id/webpage_url)
        for entry in entries:
            if not entry:
                continue
            vid_id = entry.get("id") or entry.get("url") or entry.get("webpage_url")
            # sometimes extract_flat returns 'url' as video id; try to form watch url
            if not vid_id:
                continue
            # if it's already a full url:
            if vid_id.startswith("http"):
                return vid_id
            # otherwise assume YouTube id
            return f"https://www.youtube.com/watch?v={vid_id}"

    return None


# progress hook to update Rich
def make_progress_hook(unique_id: str, progress: Progress):
    def hook(d):
        # Called by yt-dlp in the download thread
        with task_map_lock:
            rich_task_id = task_map.get(unique_id)
        # sometimes total bytes are unknown; set total only when available
        if rich_task_id is None:
            return
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes") or d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            # update total only if > 0
            if total and progress.tasks[rich_task_id].total != total:
                try:
                    progress.update(rich_task_id, total=total)
                except Exception:
                    pass
            try:
                progress.update(rich_task_id, completed=downloaded)
            except Exception:
                pass
        elif status == "finished":
            # mark done: set completed to total if possible
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or progress.tasks[rich_task_id].total
            if total:
                try:
                    progress.update(rich_task_id, completed=total)
                except Exception:
                    pass
    return hook


# download single song (search + download), updates Rich progress via hooks
def download_one(rec: dict, progress: Progress, overall_task_id: int) -> bool:
    title = rec.get("song") or rec.get("title") or ""
    artist = rec.get("artist", "")
    query = rec.get("search_query") or f"{title} {artist}".strip()
    pretty_name = f"{title} - {artist}" if artist else title
    safe_name = sanitize_filename(pretty_name) or sanitize_filename(title) or "track"

    # Create a Rich task for this file (unknown total initially)
    task_desc = pretty_name if pretty_name else query
    task_id = progress.add_task(f"[cyan]{task_desc}", total=0)

    # register mapping for progress hook
    unique_id = f"{int(time.time() * 1000)}-{threading.get_ident()}-{safe_name}"
    with task_map_lock:
        task_map[unique_id] = task_id

    # ensure USB dir exists
    Path(USB_PATH).mkdir(parents=True, exist_ok=True)

    # attempt download with retries
    last_err = None
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            # Resolve URL
            progress.console.print(f"[bold]Searching:[/] {query} (attempt {attempt})")
            url = search_youtube(query)
            if not url:
                last_err = "No search result"
                progress.console.print(f"[red]No YouTube result for:[/] {query}")
                time.sleep(0.5)
                continue

            # build yt-dlp options with progress hook closure
            outtmpl = os.path.join(USB_PATH, safe_name + ".%(ext)s")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": outtmpl,
                "ffmpeg_location": FFMPEG_PATH,
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [make_progress_hook(unique_id, progress)],
            }

            # perform download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Mark overall progress
            progress.advance(overall_task_id)
            progress.console.print(f"[green]✔ Downloaded:[/] {safe_name}.mp3")
            # cleanup mapping for this task
            with task_map_lock:
                task_map.pop(unique_id, None)
            # remove the task bar
            try:
                progress.remove_task(task_id)
            except Exception:
                pass
            return True

        except Exception as e:
            last_err = str(e)
            progress.console.print(f"[yellow]Error downloading {pretty_name} (attempt {attempt}): {e}[/yellow]")
            time.sleep(1 + attempt * 1.0)

    # final failure
    with task_map_lock:
        task_map.pop(unique_id, None)
    try:
        progress.remove_task(task_id)
    except Exception:
        pass
    progress.console.print(f"[red]Failed:[/] {pretty_name} — {last_err}")
    return False


def main():
    # load recommendations
    if not os.path.exists(RECS_FILE):
        print(f"ERROR: {RECS_FILE} not found. Place the recommendations JSON in the same folder.")
        return

    with open(RECS_FILE, "r", encoding="utf-8") as f:
        obj = json.load(f)

    recs = obj.get("recommendations", [])
    if not recs:
        print("No recommendations found in JSON.")
        return

    total = len(recs)
    Path(USB_PATH).mkdir(parents=True, exist_ok=True)
    print(f"\nStarting downloads: {total} songs → {USB_PATH}\n")

    # Rich progress manager — per-song bars + overall bar
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        expand=True,
    )

    # Use ThreadPoolExecutor for concurrency
    success_count = 0
    fail_count = 0
    with progress:
        overall = progress.add_task("[green]Overall", total=total)
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as exe:
            futures = [exe.submit(download_one, rec, progress, overall) for rec in recs]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    ok = fut.result()
                except Exception as e:
                    ok = False
                    progress.console.print(f"[red]Unhandled exception in worker: {e}[/red]")
                if ok:
                    success_count += 1
                else:
                    fail_count += 1

    print("\n----------------------------------------")
    print(f"Completed: {success_count}")
    print(f"Failed   : {fail_count}")
    print(f"Saved to : {USB_PATH}")
    print("----------------------------------------\n")


if __name__ == "__main__":
    main()
