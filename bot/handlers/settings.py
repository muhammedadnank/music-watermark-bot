"""
Handlers for Settings Management, dynamic configuration, and Custom Jingle settings.
"""

import os
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ForceReply
)

from config import OWNER_IDS, JINGLE_PATH, CUSTOM_JINGLE_BASE
from utils import (
    load_settings,
    save_settings,
    get_setting,
    set_setting,
    is_supported,
    get_extension
)

# Text & Keyboard Builders

async def make_settings_text() -> str:
    settings = await load_settings()
    mode = settings.get("mode", "both")
    interval = settings.get("interval_seconds", 120)
    tagging_enabled = settings.get("tagging_enabled", True)
    tag_artist = settings.get("tag_artist", "@PFMXBOT")
    tag_title_suffix = settings.get("tag_title_suffix", " @PFMXBOT")
    interval_volume = settings.get("interval_volume", 0.7)
    interval_fade_ms = settings.get("interval_fade_ms", 300)
    mute = settings.get("interval_mute_music", False)

    jingle_status = "🎵 Default (jingle.mp3)"
    for ext in [".mp3", ".m4a"]:
        if os.path.exists(f"{CUSTOM_JINGLE_BASE}{ext}"):
            jingle_status = f"✨ Custom (custom_jingle{ext})"
            break

    mode_icons = {
        "both": "🔁", "start_end": "🎬", "interval": "⏱", "none": "🚫"
    }
    mode_icon = mode_icons.get(mode, "🔧")
    mute_label = "🔇 Full Stop" if mute else "🔊 Mix"
    tagging_label = "✅ Enabled" if tagging_enabled else "❌ Disabled"

    return (
        "⚙️ **Watermark Bot — Settings**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎚 **Watermark Mode**\n"
        f"  {mode_icon} `{mode.upper()}`\n\n"
        "⏱ **Interval Settings**\n"
        f"  ┣ Every: `{interval}s`\n"
        f"  ┣ Mode: {mute_label}\n"
        f"  ┣ Volume: `{interval_volume:.1f}`  Fade: `{interval_fade_ms}ms`\n"
        f"  ┗ _Active for `INTERVAL` and `BOTH` modes_\n\n"
        "🏷 **Metadata Tagging**\n"
        f"  ┣ Status: {tagging_label}\n"
        f"  ┣ Artist: `{tag_artist or 'Not set'}`\n"
        f"  ┗ Title Suffix: `{tag_title_suffix or 'None'}`\n\n"
        "🎵 **Jingle**\n"
        f"  {jingle_status}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "_Use buttons below to configure:_"
    )


async def make_settings_markup() -> InlineKeyboardMarkup:
    settings = await load_settings()
    mode = settings.get("mode", "both")
    interval = settings.get("interval_seconds", 120)
    tagging_enabled = settings.get("tagging_enabled", True)

    mode_icons = {"both": "🔁", "start_end": "🎬", "interval": "⏱", "none": "🚫"}
    mode_icon = mode_icons.get(mode, "🔧")
    tagging_icon = "✅" if tagging_enabled else "❌"

    keyboard = [
        [
            InlineKeyboardButton(f"{mode_icon} Mode: {mode.upper()}", callback_data="toggle_mode"),
        ],
        [
            InlineKeyboardButton(f"⏱ Interval: {interval}s", callback_data="adjust_interval_menu"),
            InlineKeyboardButton("🎛 Jingle Mix", callback_data="interval_settings")
        ],
        [
            InlineKeyboardButton(f"🏷 Tagging: {tagging_icon}", callback_data="toggle_tagging"),
            InlineKeyboardButton("👤 Artist Tag", callback_data="edit_artist"),
        ],
        [
            InlineKeyboardButton("✍️ Title Suffix", callback_data="edit_suffix"),
            InlineKeyboardButton("🎵 Jingle", callback_data="jingle_menu")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def make_interval_text() -> str:
    interval = await get_setting("interval_seconds")
    volume = await get_setting("interval_volume")
    fade_ms = await get_setting("interval_fade_ms")
    mute = await get_setting("interval_mute_music")
    mute_label = "🔇 Full Stop (pauses music)" if mute else "🔊 Mix (overlay music)"
    return (
        "🎛 **Interval & Jingle Mix Settings**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏱ **Interval:** `{interval}s`\n"
        f"  _How often the jingle repeats_\n\n"
        f"🎚 **Mode:** {mute_label}\n"
        f"  _Full Stop = music pauses during jingle_\n\n"
        f"🔊 **Volume** _(Mix mode only)_: `{volume:.1f}`\n"
        f"🌊 **Fade:** `{fade_ms}ms` _(smooth in/out)_\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "_Active for `INTERVAL` and `BOTH` modes only._"
    )


async def make_interval_markup() -> InlineKeyboardMarkup:
    mute = await get_setting("interval_mute_music")
    mute_btn = "🔇 Music: STOP" if mute else "🔊 Music: MIX"
    keyboard = [
        # Mute toggle — most prominent
        [
            InlineKeyboardButton(mute_btn, callback_data="toggle_interval_mute")
        ],
        # Interval presets
        [
            InlineKeyboardButton("30s", callback_data="interval_preset_30"),
            InlineKeyboardButton("60s", callback_data="interval_preset_60"),
            InlineKeyboardButton("90s", callback_data="interval_preset_90"),
            InlineKeyboardButton("120s", callback_data="interval_preset_120"),
        ],
        [
            InlineKeyboardButton("180s", callback_data="interval_preset_180"),
            InlineKeyboardButton("300s", callback_data="interval_preset_300"),
            InlineKeyboardButton("-10s", callback_data="interval_sub_10"),
            InlineKeyboardButton("+10s", callback_data="interval_add_10"),
        ],
        # Volume row (only useful in mix mode)
        [
            InlineKeyboardButton("🔉 Vol -0.1", callback_data="interval_vol_sub"),
            InlineKeyboardButton("🔊 Vol +0.1", callback_data="interval_vol_add"),
        ],
        # Fade row
        [
            InlineKeyboardButton("🌅 Fade -100ms", callback_data="interval_fade_sub"),
            InlineKeyboardButton("🌄 Fade +100ms", callback_data="interval_fade_add"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="settings_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def make_jingle_text() -> str:
    jingle_status = "Default (jingle.mp3)"
    for ext in [".mp3", ".m4a"]:
        if os.path.exists(f"{CUSTOM_JINGLE_BASE}{ext}"):
            jingle_status = f"✨ Custom — `custom_jingle{ext}`"
            break

    return (
        "🎵 **Jingle Configuration**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 **Status:** `{jingle_status}`\n\n"
        "📂 **How to set a custom jingle:**\n"
        "┣ 1. Send your MP3 or M4A clip to the bot\n"
        "┣ 2. Reply to that audio with `/setjingle`\n"
        "┗ The bot registers it as the active watermark\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


def make_jingle_markup() -> InlineKeyboardMarkup:
    has_custom = False
    for ext in [".mp3", ".m4a"]:
        if os.path.exists(f"{CUSTOM_JINGLE_BASE}{ext}"):
            has_custom = True
            break
            
    keyboard = [
        [
            InlineKeyboardButton("📥 Send Current Jingle", callback_data="jingle_send")
        ]
    ]
    if has_custom:
        keyboard.append([
            InlineKeyboardButton("🗑 Delete Custom Jingle", callback_data="jingle_delete")
        ])
    keyboard.append([
        InlineKeyboardButton("🔙 Back to Settings", callback_data="settings_main")
    ])
    return InlineKeyboardMarkup(keyboard)


# Command Handlers

@Client.on_message(filters.command(["default", "settings"]))
async def default_cmd(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        await message.reply_text(
            "🚫 **Access Denied**\n"
            "You are not authorized to use this bot."
        )
        return

    await message.reply_text(
        text=await make_settings_text(),
        reply_markup=await make_settings_markup()
    )


@Client.on_message(filters.command("jingle"))
async def jingle_cmd(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        await message.reply_text("❌ **Access Denied!**\nYou are not authorized to use this bot.")
        return

    await message.reply_text(
        text=make_jingle_text(),
        reply_markup=make_jingle_markup()
    )


@Client.on_message(filters.command("setinterval"))
async def setinterval_cmd(client: Client, message: Message):
    """Set exact interval seconds via /setinterval <seconds>."""
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        await message.reply_text("❌ **Access Denied!**")
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        current = await get_setting("interval_seconds")
        await message.reply_text(
            f"⏱ **Usage:** `/setinterval <seconds>`\n\nCurrent interval: `{current}s`\n"
            "Example: `/setinterval 90`"
        )
        return

    try:
        seconds = int(parts[1])
        if seconds < 5:
            await message.reply_text("❌ Interval must be at least **5 seconds**.")
            return
        await set_setting("interval_seconds", seconds)
        await message.reply_text(
            f"✅ **Interval updated to `{seconds}s`!**\n\n" + await make_settings_text(),
            reply_markup=await make_settings_markup()
        )
    except ValueError:
        await message.reply_text("❌ Please provide a valid integer. Example: `/setinterval 90`")


@Client.on_message(filters.command("setjingle"))
async def setjingle_cmd(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        await message.reply_text("❌ **Access Denied!**\nYou are not authorized to use this bot.")
        return

    reply = message.reply_to_message
    if not reply or not (reply.audio or reply.document):
        await message.reply_text(
            "❌ **Usage:** Reply to an audio file (.mp3 or .m4a) with `/setjingle` to set it as your custom jingle."
        )
        return

    media = reply.audio or reply.document
    filename = media.file_name or "jingle.mp3"
    if not is_supported(filename):
        await message.reply_text("❌ Only **.mp3** and **.m4a** files are supported for jingles.")
        return

    status = await message.reply_text(
        "📥 **Downloading jingle...**\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        # Delete existing custom jingles
        for old_ext in [".mp3", ".m4a"]:
            old_path = f"{CUSTOM_JINGLE_BASE}{old_ext}"
            if os.path.exists(old_path):
                os.remove(old_path)

        ext = get_extension(filename)
        save_path = f"{CUSTOM_JINGLE_BASE}{ext}"
        
        await reply.download(file_name=save_path)
        
        await status.edit_text(
            f"✅ **Custom jingle set!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎵 **File:** `{filename}`\n"
            f"📂 **Saved as:** `custom_jingle{ext}`\n"
            f"✅ Your next watermark will use this jingle!"
        )
    except Exception as e:
        await status.edit_text(
            f"❌ **Failed to set jingle:**\n`{e}`"
        )


# Callback Query Handler

@Client.on_callback_query()
async def handle_settings_callbacks(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in OWNER_IDS:
        await callback_query.answer("❌ You are not authorized.", show_alert=True)
        return

    data = callback_query.data
    
    if data == "settings_main":
        await callback_query.message.edit_text(
            text=await make_settings_text(),
            reply_markup=await make_settings_markup()
        )
        await callback_query.answer()

    elif data == "close_settings":
        await callback_query.message.delete()
        await callback_query.answer("✔️ Settings closed")

    elif data == "interval_settings":
        await callback_query.message.edit_text(
            text=await make_interval_text(),
            reply_markup=await make_interval_markup()
        )
        await callback_query.answer()

    elif data == "toggle_mode":
        current_mode = await get_setting("mode")
        modes = ["both", "start_end", "interval", "none"]
        next_mode = modes[(modes.index(current_mode) + 1) % len(modes)]
        await set_setting("mode", next_mode)
        
        await callback_query.message.edit_text(
            text=await make_settings_text(),
            reply_markup=await make_settings_markup()
        )
        await callback_query.answer(f"Mode set to {next_mode.upper()}")
        
    elif data == "toggle_tagging":
        current_val = await get_setting("tagging_enabled")
        await set_setting("tagging_enabled", not current_val)
        
        await callback_query.message.edit_text(
            text=await make_settings_text(),
            reply_markup=await make_settings_markup()
        )
        await callback_query.answer(f"Metadata Tagging {'Enabled' if not current_val else 'Disabled'}")
        
    elif data == "adjust_interval_menu":
        await callback_query.message.edit_text(
            text=await make_interval_text(),
            reply_markup=await make_interval_markup()
        )
        await callback_query.answer()
        
    elif data == "toggle_interval_mute":
        current_mute = bool(await get_setting("interval_mute_music"))
        await set_setting("interval_mute_music", not current_mute)
        label = "Full Stop 🔇" if not current_mute else "Mix Mode 🔊"
        await callback_query.message.edit_text(
            text=await make_interval_text(), reply_markup=await make_interval_markup()
        )
        await callback_query.answer(f"Music during jingle: {label}")

    elif data.startswith("interval_preset_"):
        # Quick preset buttons e.g. interval_preset_120
        try:
            new_val = int(data.split("_")[-1])
        except ValueError:
            new_val = 120
        await set_setting("interval_seconds", new_val)
        await callback_query.message.edit_text(
            text=await make_interval_text(), reply_markup=await make_interval_markup()
        )
        await callback_query.answer(f"Interval set to {new_val}s")

    elif data.startswith("interval_add_") or data.startswith("interval_sub_"):
        current_val = await get_setting("interval_seconds")
        try:
            diff = int(data.split("_")[-1])
            if "sub" in data:
                diff = -diff
        except ValueError:
            diff = 0
        new_val = max(5, current_val + diff)
        await set_setting("interval_seconds", new_val)
        await callback_query.message.edit_text(
            text=await make_interval_text(), reply_markup=await make_interval_markup()
        )
        await callback_query.answer(f"Interval set to {new_val}s")

    elif data == "interval_vol_add" or data == "interval_vol_sub":
        current_vol = float(await get_setting("interval_volume"))
        delta = 0.1 if data == "interval_vol_add" else -0.1
        new_vol = round(max(0.0, min(1.0, current_vol + delta)), 1)
        await set_setting("interval_volume", new_vol)
        await callback_query.message.edit_text(
            text=await make_interval_text(), reply_markup=await make_interval_markup()
        )
        await callback_query.answer(f"Volume set to {new_vol:.1f}")

    elif data == "interval_fade_add" or data == "interval_fade_sub":
        current_fade = int(await get_setting("interval_fade_ms"))
        delta = 100 if data == "interval_fade_add" else -100
        new_fade = max(0, min(2000, current_fade + delta))
        await set_setting("interval_fade_ms", new_fade)
        await callback_query.message.edit_text(
            text=await make_interval_text(), reply_markup=await make_interval_markup()
        )
        await callback_query.answer(f"Fade set to {new_fade}ms")
        
    elif data == "edit_artist":
        await callback_query.message.reply_text(
            "👤 **Edit Artist Tag**\n\n"
            "Please reply to this message with the new Artist Tag (e.g. `@PFMXBOT`).\n"
            "Send `/cancel` to abort.",
            reply_markup=ForceReply(selective=True)
        )
        await callback_query.answer()
        
    elif data == "edit_suffix":
        await callback_query.message.reply_text(
            "✍️ **Edit Title Suffix**\n\n"
            "Please reply to this message with the suffix to append to the Title tag (e.g. ` @PFMXBOT`).\n"
            "Send `/cancel` to abort.",
            reply_markup=ForceReply(selective=True)
        )
        await callback_query.answer()
        
    elif data == "jingle_menu":
        await callback_query.message.edit_text(
            text=make_jingle_text(),
            reply_markup=make_jingle_markup()
        )
        await callback_query.answer()
        
    elif data == "jingle_send":
        await callback_query.answer("Sending active jingle...")
        jingle_path = JINGLE_PATH
        for ext in [".mp3", ".m4a"]:
            custom_path = f"{CUSTOM_JINGLE_BASE}{ext}"
            if os.path.exists(custom_path):
                jingle_path = custom_path
                break
        
        if os.path.exists(jingle_path):
            await callback_query.message.reply_audio(
                audio=jingle_path,
                caption=f"🎵 **Active jingle:** `{os.path.basename(jingle_path)}`"
            )
        else:
            await callback_query.message.reply_text(
                "⚠️ **No jingle found on server.**\n"
                "Upload one via `/setjingle` or place `jingle.mp3` in the bot folder."
            )
            
    elif data == "jingle_delete":
        deleted = False
        for ext in [".mp3", ".m4a"]:
            custom_path = f"{CUSTOM_JINGLE_BASE}{ext}"
            if os.path.exists(custom_path):
                os.remove(custom_path)
                deleted = True
        
        if deleted:
            await callback_query.answer("🗑 Custom jingle deleted.", show_alert=True)
        else:
            await callback_query.answer("No custom jingle found.", show_alert=True)

        await callback_query.message.edit_text(
            text=make_jingle_text(),
            reply_markup=make_jingle_markup()
        )


# Reply Messages Listener (ForceReply processing)

@Client.on_message(filters.reply & filters.text & filters.private)
async def handle_replies(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in OWNER_IDS:
        return
    
    reply = message.reply_to_message
    if not reply or not reply.text:
        return
        
    if "Edit Artist Tag" in reply.text:
        new_val = message.text.strip()
        if new_val == "/cancel":
            await message.reply_text("❌ Action cancelled.")
            return
        await set_setting("tag_artist", new_val)
        await message.reply_text(
            f"✅ **Artist Tag updated!**\nNew value: `{new_val}`\n\n" + await make_settings_text(),
            reply_markup=await make_settings_markup()
        )
        
    elif "Edit Title Suffix" in reply.text:
        new_val = message.text.strip()
        if new_val == "/cancel":
            await message.reply_text("❌ Action cancelled.")
            return
        await set_setting("tag_title_suffix", new_val)
        await message.reply_text(
            f"✅ **Title Suffix updated!**\nNew value: `{new_val}`\n\n" + await make_settings_text(),
            reply_markup=await make_settings_markup()
        )
