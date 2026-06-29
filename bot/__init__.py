"""
Bot package initialization.
"""

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# Initialize Client with plugins folder for clean handler separation
app = Client(
    "watermark_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="bot.handlers")
)
