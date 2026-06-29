"""
Utility package.
"""

from utils.ffmpeg import add_watermark, is_supported, get_extension, WatermarkError
from utils.metadata import get_audio_duration, get_audio_tags, extract_thumbnail
from utils.progress import progress_callback, update_watermark_status
from utils.settings_manager import load_settings, save_settings, get_setting, set_setting

__all__ = [
    "add_watermark",
    "is_supported",
    "get_extension",
    "WatermarkError",
    "get_audio_duration",
    "get_audio_tags",
    "extract_thumbnail",
    "progress_callback",
    "update_watermark_status",
    "load_settings",
    "save_settings",
    "get_setting",
    "set_setting",
]

