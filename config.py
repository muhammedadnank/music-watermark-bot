"""
Configuration for the Music Watermark Bot.

Reads from environment variables first (needed for Docker / Render),
falling back to the defaults below for local runs.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from a .env file if present (local runs)

# Get these from https://my.telegram.org
API_ID = int(os.environ.get("API_ID", "12345678"))
API_HASH = os.environ.get("API_HASH", "your_api_hash_here")

# Get this from @BotFather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token_here")

# Path to your jingle/watermark audio file.
# Place a short mp3 or m4a clip here (your voice tag / sound).
# This SAME jingle is added at both the START and END of every audio
# the user sends.
JINGLE_PATH = os.environ.get("JINGLE_PATH", "jingle.mp3")

# Folder used for temporary downloads/output (auto-created, auto-cleaned)
TEMP_DIR = os.environ.get("TEMP_DIR", "temp")

# Max file size to accept (in MB).
MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "300"))

# Authorized Owner IDs (comma-separated list of Telegram user IDs)
raw_owner_ids = os.environ.get("OWNER_ID", "8123066073")
OWNER_IDS = [
    int(x.strip()) for x in raw_owner_ids.split(",") if x.strip().isdigit()
]

# Path where custom uploaded jingle is saved
CUSTOM_JINGLE_PATH = "custom_jingle.mp3"

# MongoDB Connection String (fallback to empty for local JSON database)
MONGO_URI = os.environ.get("MONGO_URI", "")
