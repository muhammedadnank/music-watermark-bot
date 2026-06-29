"""
Progress reporting callback and status update helpers.
"""

import time
import asyncio

async def progress_callback(current, total, status_message, action_name, start_time, last_update):
    """
    Limits Pyrogram updates to once per 2 seconds to avoid floodwait/rate-limiting,
    displaying elapsed time, speed, and percent completion.
    """
    now = time.time()
    # Limit update frequency to 2 seconds to avoid Telegram rate limits
    if now - last_update[0] < 2.0:
        return
    last_update[0] = now
    
    elapsed = now - start_time
    current_mb = current / (1024 * 1024)
    
    # Calculate transfer speed
    speed = current / elapsed if elapsed > 0 else 0
    speed_kb = speed / 1024
    if speed_kb > 1024:
        speed_str = f"{speed_kb/1024:.1f} MB/s"
    else:
        speed_str = f"{speed_kb:.1f} KB/s"

    if total > 0:
        percent = (current / total) * 100
        total_mb = total / (1024 * 1024)
        text = (
            f"{action_name}...\n\n"
            f"⏳ Time elapsed: `{elapsed:.1f}s`\n"
            f"📊 Progress: `{percent:.1f}%` (`{current_mb:.1f}`/`{total_mb:.1f}` MB)\n"
            f"⚡ Speed: `{speed_str}`"
        )
    else:
        text = (
            f"{action_name}...\n\n"
            f"⏳ Time elapsed: `{elapsed:.1f}s`\n"
            f"📊 Progress: `{current_mb:.1f}` MB\n"
            f"⚡ Speed: `{speed_str}`"
        )
        
    try:
        await status_message.edit_text(text)
    except Exception:
        pass


async def update_watermark_status(status_message, start_time, stop_event, action_name="🎛 Adding watermark"):
    """
    Runs in the background during watermarking to update the elapsed time.
    """
    while not stop_event.is_set():
        await asyncio.sleep(2.0)
        if stop_event.is_set():
            break
        elapsed = time.time() - start_time
        try:
            await status_message.edit_text(
                f"{action_name}...\n\n"
                f"⏳ Time elapsed: `{elapsed:.1f}s`"
            )
        except Exception:
            pass
