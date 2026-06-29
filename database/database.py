import os
import json
import time
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

# Path for local fallback of settings
SETTINGS_PATH = "settings.json"

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

class Database:
    def __init__(self, uri, database_name="watermark_bot"):
        self.uri = uri
        self.db_name = database_name
        self.client = None
        self.db = None
        self.users = None
        self.settings = None

        # Local cache for settings
        self._settings_cache = None
        self._last_fetch_time = 0.0
        self.cache_ttl = 60.0  # cache settings for 60 seconds

        if uri:
            try:
                self.client = AsyncIOMotorClient(
                    uri,
                    serverSelectionTimeoutMS=3000,
                    socketTimeoutMS=2000
                )
                self.db = self.client[database_name]
                self.users = self.db.users
                self.settings = self.db.settings
            except Exception as e:
                print(f"⚠️ Failed to connect to MongoDB: {e}. Falling back to settings.json.")
                self.client = None
                self.db = None
                self.users = None
                self.settings = None

    async def ping(self) -> bool:
        """
        Eagerly verify MongoDB connection by pinging.
        """
        if self.client is not None:
            try:
                await self.client.admin.command("ping")
                return True
            except Exception as e:
                print(f"⚠️ MongoDB Ping failed: {e}")
                return False
        return False

    async def get_settings(self) -> dict:
        """
        Retrieve settings asynchronously, checking cache TTL and falling back to local settings.json.
        """
        now = time.time()
        if self._settings_cache is not None and (now - self._last_fetch_time) < self.cache_ttl:
            return self._settings_cache

        # Try to load from MongoDB settings collection
        if self.settings is not None:
            try:
                doc = await self.settings.find_one({"_id": "bot_settings"})
                if doc:
                    doc.pop("_id", None)
                    # Merge defaults for any missing keys
                    for k, v in DEFAULT_SETTINGS.items():
                        if k not in doc:
                            doc[k] = v
                    self._settings_cache = doc
                    self._last_fetch_time = now
                    return self._settings_cache
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
                    self._settings_cache = data
                    self._last_fetch_time = now
                    return self._settings_cache
            except Exception:
                pass

        # Return defaults if everything fails
        self._settings_cache = DEFAULT_SETTINGS.copy()
        self._last_fetch_time = now
        return self._settings_cache

    async def update_setting(self, key: str, value) -> None:
        """
        Atomically update a specific key in settings.
        """
        settings = await self.get_settings()
        settings[key] = value
        self._settings_cache = settings.copy()
        self._last_fetch_time = time.time()

        if self.settings is not None:
            try:
                await self.settings.update_one(
                    {"_id": "bot_settings"},
                    {"$set": {key: value}},
                    upsert=True
                )
                return
            except Exception as e:
                print(f"⚠️ MongoDB update_one error: {e}. Falling back to settings.json.")

        # Fallback to local settings.json
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception:
            pass

    async def save_settings(self, settings: dict) -> None:
        """
        Save full settings dictionary to MongoDB or local JSON fallback.
        """
        self._settings_cache = settings.copy()
        self._last_fetch_time = time.time()

        if self.settings is not None:
            try:
                await self.settings.replace_one(
                    {"_id": "bot_settings"},
                    {"_id": "bot_settings", **settings},
                    upsert=True
                )
                return
            except Exception as e:
                print(f"⚠️ MongoDB replace_one error: {e}. Falling back to settings.json.")

        # Fallback to local settings.json
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception:
            pass

    # User Management matching the Ebook-Search-Bot reference style
    async def add_user(self, user_id: int, name: str) -> None:
        """
        Insert new user into user database.
        """
        if self.users is not None:
            try:
                user = {
                    "id": int(user_id),
                    "name": name,
                    "first_joined": time.time()
                }
                await self.users.update_one(
                    {"id": int(user_id)},
                    {"$set": user},
                    upsert=True
                )
            except Exception as e:
                print(f"⚠️ MongoDB add_user error: {e}")

    async def is_user_exist(self, user_id: int) -> bool:
        """
        Check if user exists in database.
        """
        if self.users is not None:
            try:
                user = await self.users.find_one({"id": int(user_id)})
                return bool(user)
            except Exception as e:
                print(f"⚠️ MongoDB is_user_exist error: {e}")
        return False

    async def total_users_count(self) -> int:
        """
        Get total number of users.
        """
        if self.users is not None:
            try:
                return await self.users.count_documents({})
            except Exception as e:
                print(f"⚠️ MongoDB total_users_count error: {e}")
        return 0

    async def get_all_users(self):
        """
        Get cursor of all users.
        """
        if self.users is not None:
            try:
                return self.users.find({})
            except Exception as e:
                print(f"⚠️ MongoDB get_all_users error: {e}")
        return None

# Instantiate singleton DB matching the style of Ebook-Search-Bot
db = Database(MONGO_URI)
