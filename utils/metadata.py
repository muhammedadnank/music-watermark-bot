"""
Metadata, tags, and artwork extraction helpers using ffprobe/ffmpeg.
"""

import asyncio
import os
from pyrogram import Client
from pyrogram.types import Message

async def get_audio_duration(file_path: str) -> int:
    """
    Get duration of an audio file in seconds using ffprobe.
    """
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        if process.returncode == 0:
            return int(float(stdout.decode().strip()))
    except Exception:
        pass
    return 0


async def get_audio_tags(file_path: str) -> dict:
    """
    Extract title and artist metadata from an audio file format tags.
    """
    tags = {}
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format_tags=title,artist,TITLE,ARTIST,performer,PERFORMER",
            "-of", "default=noprint_wrappers=1:nokey=0",
            file_path
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        if process.returncode == 0:
            for line in stdout.decode('utf-8', errors='ignore').splitlines():
                if "=" in line:
                    key, val = line.split("=", 1)
                    key_lower = key.lower()
                    if key_lower.startswith("tag:"):
                        key_lower = key_lower[len("tag:"):]
                    tags[key_lower] = val.strip()
    except Exception:
        pass
    return tags


async def extract_thumbnail(client: Client, media, job_dir: str, input_path: str) -> str:
    """
    Extracts or downloads the thumbnail of the audio file.
    First tries to download Telegram-provided thumbnail, then falls back to extracting cover art.
    """
    thumb_path = None
    if hasattr(media, "thumbs") and media.thumbs:
        temp_thumb = os.path.join(job_dir, "thumb.jpg")
        try:
            await client.download_media(media.thumbs[0].file_id, file_name=temp_thumb)
            if os.path.exists(temp_thumb) and os.path.getsize(temp_thumb) > 0:
                thumb_path = temp_thumb
        except Exception:
            pass

    if not thumb_path:
        temp_cover = os.path.join(job_dir, "cover.jpg")
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-an",
                "-vcodec", "mjpeg",
                "-vframes", "1",
                "-f", "image2",
                temp_cover
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            if process.returncode == 0 and os.path.exists(temp_cover) and os.path.getsize(temp_cover) > 0:
                thumb_path = temp_cover
        except Exception:
            pass

    return thumb_path
