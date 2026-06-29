"""
Music Watermark Bot Entrypoint
"""

import os
import asyncio
from pyrogram import idle

from config import TEMP_DIR
from bot import app
from server import run_web_server

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

async def main():
    print("Starting Music Watermark Bot...")
    # Start the keep-alive web server
    await run_web_server()
    # Start Pyrogram Bot client
    await app.start()
    print("Music Watermark Bot is running ✅")
    # Keep running until interrupted
    await idle()
    # Graceful stop
    print("Stopping bot...")
    await app.stop()
    print("Bot stopped successfully.")

if __name__ == "__main__":
    try:
        app.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        try:
            from utils.settings_manager import close_db_connection
            close_db_connection()
            print("Database connection closed.")
        except Exception:
            pass
