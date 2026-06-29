"""
Settings Manager to load and save bot configuration.
Supports MongoDB database persistence with local JSON file fallback.
"""

import os
import json
from config import MONGO_URI

SETTINGS_PATH = "settings.json"

DEFAULT_SETTINGS = {
    "mode": "both",
    "interval_seconds": 120,
    "interval_volume": 0.7,
    "interval_fade_ms": 300,
    "interval_mute_music": False,   # True = full stop during jingle, False = mix/overlay
    "tagging_enabled": True,
    "tag_artist": "@PFMXBOT",
    "tag_title_suffix": " @PFMXBOT"
}

# In-memory settings cache to avoid network round-trips
_cache = None

# MongoDB Client initialization
client = None
db_collection = None
if MONGO_URI:
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI)
        db = client["watermark_bot"]
        db_collection = db["settings"]
        print("Connected to MongoDB for settings persistence ✅")
    except Exception as e:
        print(f"⚠️ Failed to connect to MongoDB: {e}. Falling back to settings.json.")


def close_db_connection() -> None:
    """
    Close MongoDB connection safely if open.
    """
    global client, db_collection
    if client is not None:
        try:
            client.close()
        except Exception:
            pass
        client = None
        db_collection = None


def load_settings() -> dict:
    """
    Load settings from MongoDB or local JSON file.
    """
    global _cache
    if _cache is not None:
        return _cache

    # Try loading from MongoDB first
    if db_collection is not None:
        try:
            doc = db_collection.find_one({"_id": "bot_settings"})
            if doc:
                doc.pop("_id", None)
                # Ensure all default keys exist
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in doc:
                        doc[k] = v
                _cache = doc
                return _cache
        except Exception as e:
            print(f"⚠️ MongoDB load error: {e}. Trying JSON fallback.")

    # Fallback to local settings.json
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r") as f:
                data = json.load(f)
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                _cache = data
                return _cache
        except Exception:
            pass

    _cache = DEFAULT_SETTINGS.copy()
    return _cache


def save_settings(settings: dict) -> None:
    """
    Save settings to MongoDB or local JSON file.
    """
    global _cache
    _cache = settings.copy()

    # Save to MongoDB if available
    if db_collection is not None:
        try:
            db_collection.replace_one(
                {"_id": "bot_settings"},
                {"_id": "bot_settings", **settings},
                upsert=True
            )
            return
        except Exception as e:
            print(f"⚠️ MongoDB save error: {e}. Saving to JSON fallback.")

    # Fallback to local settings.json
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass


def get_setting(key: str):
    """
    Get a specific setting value.
    """
    settings = load_settings()
    return settings.get(key, DEFAULT_SETTINGS.get(key))


def set_setting(key: str, value) -> None:
    """
    Set a specific setting value.
    """
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
