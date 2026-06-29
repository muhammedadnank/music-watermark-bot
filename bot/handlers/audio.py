"""
Handler for audio files and audio documents.
"""

import os
import time
import uuid
import shutil
import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

from config import TEMP_DIR, MAX_FILE_SIZE_MB
from utils import (
    is_supported,
    get_extension,
    add_watermark,
    WatermarkError,
    get_audio_duration,
    get_audio_tags,
    extract_thumbnail,
    progress_callback,
    update_watermark_status,
)

@Client.on_message(filters.audio | filters.document)
async def handle_audio(client: Client, message: Message):
    from config import OWNER_IDS
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        await message.reply_text(
            "🚫 **Access Denied**\n"
            "This is a private bot. You are not authorized."
        )
        return

    media = message.audio or message.document
    if media is None:
        return

    filename = media.file_name or "audio.mp3"

    if not is_supported(filename):
        await message.reply_text(
            "⚠️ **Unsupported Format**\n\n"
            "Only **MP3** and **M4A** files are accepted.\n"
            "Please convert your file and try again."
        )
        return

    size_mb = (media.file_size or 0) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        await message.reply_text(
            f"⚠️ **File Too Large**\n\n"
            f"Your file is `{size_mb:.1f} MB`.\n"
            f"Maximum allowed size is `{MAX_FILE_SIZE_MB} MB`."
        )
        return

    status = await message.reply_text(
        "📥 **Receiving your file...**\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    job_id = uuid.uuid4().hex[:8]
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    ext = get_extension(filename)
    input_path = os.path.join(job_dir, f"in{ext}")
    output_path = os.path.join(job_dir, f"out{ext}")
    final_output_path = None

    try:
        # Start download timer and download with progress
        download_start = time.time()
        last_update = [time.time()]
        await message.download(
            file_name=input_path,
            progress=progress_callback,
            progress_args=(status, "⬇️ Downloading", download_start, last_update)
        )
        download_time = time.time() - download_start

        # Extract tags and thumbnail/album art
        await status.edit_text(
            "🔍 **Reading metadata...**\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )

        
        performer = None
        title = None
        if hasattr(media, "performer") and media.performer:
            performer = media.performer
        if hasattr(media, "title") and media.title:
            title = media.title
            
        tags = await get_audio_tags(input_path)
        if not performer:
            performer = tags.get("artist") or tags.get("performer") or "Unknown Artist"
        if not title:
            title = tags.get("title") or os.path.splitext(filename)[0]

        # Apply settings-based metadata tagging
        from utils import get_setting
        tagging_enabled = await get_setting("tagging_enabled")
        if tagging_enabled:
            tag_artist = await get_setting("tag_artist")
            tag_title_suffix = await get_setting("tag_title_suffix")
            if tag_artist:
                performer = tag_artist
            if tag_title_suffix:
                title = f"{title}{tag_title_suffix}"

        thumb_path = await extract_thumbnail(client, media, job_dir, input_path)

        mode = await get_setting("mode")
        mode_label = {
            "both": "🔁 Both (Start/End + Intervals)",
            "start_end": "🎬 Start & End",
            "interval": "⏱ Intervals",
            "none": "🚫 No Watermark"
        }.get(mode, mode)

        mute = await get_setting("interval_mute_music")
        if mode in ("interval", "both") and mute:
            mode_label += " 🔇"

        await status.edit_text(
            f"🎛 **Applying Watermark...**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Mode: {mode_label}"
        )
        watermark_start = time.time()

        # Start background timer updater for watermark step
        stop_event = asyncio.Event()
        updater_task = asyncio.create_task(
            update_watermark_status(status, watermark_start, stop_event,
                                    f"🎛 **Applying Watermark...**\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                    f"Mode: {mode_label}")
        )
        try:
            await add_watermark(input_path, output_path, title=title, artist=performer)
        finally:
            stop_event.set()
            await updater_task

        watermark_time = time.time() - watermark_start

        # Start upload timer and upload with progress
        await status.edit_text(
            "📤 **Uploading your file...**\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        upload_start = time.time()
        last_update = [time.time()]

        # Rename to original filename
        final_output_path = os.path.join(job_dir, filename)
        os.rename(output_path, final_output_path)

        # Get final duration
        duration = await get_audio_duration(final_output_path)

        total_time = time.time() - download_start
        upload_time = time.time() - upload_start

        await message.reply_audio(
            audio=final_output_path,
            caption=(
                f"✅ **Done! Watermark Applied**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎵 **{title}**\n"
                f"👤 {performer}\n\n"
                f"🔧 **Mode:** {mode_label}\n\n"
                f"⏱ **Processing Time:**\n"
                f"┣ 📥 Download: `{download_time:.1f}s`\n"
                f"┣ 🎛 Watermark: `{watermark_time:.1f}s`\n"
                f"┣ 📤 Upload: `{upload_time:.1f}s`\n"
                f"┗ ⚡ Total: `{total_time:.1f}s`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            ),
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb_path,
            progress=progress_callback,
            progress_args=(status, "⬆️ Uploading", upload_start, last_update)
        )
        await status.delete()

    except WatermarkError as e:
        await status.edit_text(
            f"❌ **Watermarking Failed**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"`{e}`"
        )
    except Exception as e:
        await status.edit_text(
            f"⚠️ **Unexpected Error**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"`{e}`"
        )
    finally:
        # Cleanup temp directory regardless of outcome
        if os.path.exists(job_dir):
            try:
                shutil.rmtree(job_dir)
            except OSError:
                pass
