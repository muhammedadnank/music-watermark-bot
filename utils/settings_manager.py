"""
Settings Manager wrapper.
Delegates settings management to the asynchronous database manager.
"""

from database import db

DEFAULT_SETTINGS = {
    "mode": "both",
    "interval_seconds": 120,
    "interval_volume": 0.7,
    "interval_fade_ms": 300,
    "interval_mute_music": False,
    "tagging_enabled": True,
    "tag_artist": "@PFMXBOT",
    "tag_title_suffix": " @PFMXBOT"
}


def close_db_connection() -> None:
    """
    Close MongoDB connection safely if open.
    """
    if db.client is not None:
        try:
            db.client.close()
        except Exception:
            pass


async def load_settings() -> dict:
    """
    Load settings asynchronously from the Database.
    """
    return await db.get_settings()


async def save_settings(settings: dict) -> None:
    """
    Save settings asynchronously to the Database.
    """
    await db.save_settings(settings)


async def get_setting(key: str):
    """
    Get a specific setting value asynchronously.
    """
    settings = await db.get_settings()
    return settings.get(key, DEFAULT_SETTINGS.get(key))


async def set_setting(key: str, value) -> None:
    """
    Set a specific setting value atomically and asynchronously.
    """
    await db.update_setting(key, value)
