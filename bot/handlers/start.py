"""
Handler for the /start command.
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from config import MAX_FILE_SIZE_MB

@Client.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    from config import OWNER_IDS, MAX_FILE_SIZE_MB
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        await message.reply_text("❌ **Access Denied!**\nYou are not authorized to use this bot.")
        return

    await message.reply_text(
        "🎵 **Welcome to Music Watermark Bot!**\n\n"
        "This bot helps you quickly apply audio watermarks (jingles) "
        "and edit metadata tags on MP3 and M4A audio files.\n\n"
        "⚡ **Commands:**\n"
        "• `/default` or `/settings` — Customize watermark mode, intervals, and tag formats.\n"
        "• `/jingle` — View current jingle or update it (by replying to any audio with `/setjingle`).\n\n"
        "📨 **To Watermark:**\n"
        f"Just send me any audio file (max `{MAX_FILE_SIZE_MB}MB`). I will process it and send it back instantly!"
    )
