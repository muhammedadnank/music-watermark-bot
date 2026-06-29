"""
Handler for the /start command.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


@Client.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    from config import OWNER_IDS, MAX_FILE_SIZE_MB
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        await message.reply_text(
            "🚫 **Access Denied**\n\n"
            "This is a private bot. You are not authorized to use it."
        )
        return

    user = message.from_user
    first_name = user.first_name or "there"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Open Settings", callback_data="settings_main")],
        [InlineKeyboardButton("🎵 How to Use", callback_data="how_to_use")]
    ])

    await message.reply_text(
        f"👋 **Hey, {first_name}!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎵 **Music Watermark Bot**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Watermark your audio files with a jingle — at the **start/end**, "
        "at **intervals**, or with **full stop** mode for professional results.\n\n"
        "**🔧 Modes Available:**\n"
        "┣ 🔁 `BOTH` — Start + End + Intervals\n"
        "┣ 🎬 `START_END` — Jingle at start and end only\n"
        "┣ ⏱ `INTERVAL` — Repeated throughout audio\n"
        "┗ 🚫 `NONE` — Metadata tagging only\n\n"
        "**📤 To Watermark:**\n"
        f"Simply send an **MP3** or **M4A** file (up to `{MAX_FILE_SIZE_MB} MB`).\n\n"
        "**⌨️ Commands:**\n"
        "• `/default` — Open settings panel\n"
        "• `/setinterval <s>` — Set exact interval\n"
        "• `/setjingle` — Reply audio to set jingle\n\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=keyboard
    )


@Client.on_callback_query(filters.regex("^how_to_use$"))
async def how_to_use_cb(client, callback_query):
    from config import OWNER_IDS
    if callback_query.from_user.id not in OWNER_IDS:
        await callback_query.answer("Access Denied.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Open Settings", callback_data="settings_main")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
    ])

    await callback_query.message.edit_text(
        "📖 **How to Use**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Step 1 — Configure Mode:**\n"
        "Open `/default` → choose your watermark mode\n\n"
        "**Step 2 — Set Your Jingle:**\n"
        "Send any audio file and reply with `/setjingle`\n"
        "_Or_ place `jingle.mp3` in the bot folder\n\n"
        "**Step 3 — Send Audio:**\n"
        "Send your MP3 or M4A file — the bot will\n"
        "watermark it and send it back automatically!\n\n"
        "**🎚 Interval Mode Tips:**\n"
        "• 🔊 **Mix** — Jingle overlays on music\n"
        "• 🔇 **Full Stop** — Music pauses for jingle\n"
        "• Adjust volume, fade, and frequency in settings\n\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=keyboard
    )
    await callback_query.answer()


@Client.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_cb(client, callback_query):
    from config import OWNER_IDS, MAX_FILE_SIZE_MB
    if callback_query.from_user.id not in OWNER_IDS:
        await callback_query.answer("Access Denied.", show_alert=True)
        return

    user = callback_query.from_user
    first_name = user.first_name or "there"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Open Settings", callback_data="settings_main")],
        [InlineKeyboardButton("🎵 How to Use", callback_data="how_to_use")]
    ])

    await callback_query.message.edit_text(
        f"👋 **Hey, {first_name}!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎵 **Music Watermark Bot**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Watermark your audio files with a jingle — at the **start/end**, "
        "at **intervals**, or with **full stop** mode for professional results.\n\n"
        "**🔧 Modes Available:**\n"
        "┣ 🔁 `BOTH` — Start + End + Intervals\n"
        "┣ 🎬 `START_END` — Jingle at start and end only\n"
        "┣ ⏱ `INTERVAL` — Repeated throughout audio\n"
        "┗ 🚫 `NONE` — Metadata tagging only\n\n"
        "**📤 To Watermark:**\n"
        f"Simply send an **MP3** or **M4A** file (up to `{MAX_FILE_SIZE_MB} MB`).\n\n"
        "**⌨️ Commands:**\n"
        "• `/default` — Open settings panel\n"
        "• `/setinterval <s>` — Set exact interval\n"
        "• `/setjingle` — Reply audio to set jingle\n\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=keyboard
    )
    await callback_query.answer()
