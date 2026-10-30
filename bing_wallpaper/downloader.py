import os
import re
import shutil
import logging
from pathlib import Path
from typing import Optional
import requests

from .config import THUMBS_DIR, WALLPAPERS_CACHE_DIR, PICTURES_DIR, DEFAULT_HEADERS
from .models import WallpaperItem

logger = logging.getLogger(__name__)

class ImageDownloader:
    """Handles downloading and local disk caching of thumbnails and high-res wallpapers."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def get_thumb_cache_path(self, item: WallpaperItem) -> Path:
        return THUMBS_DIR / f"{item.id}_thumb.jpg"

    def get_full_cache_path(self, item: WallpaperItem) -> Path:
        return WALLPAPERS_CACHE_DIR / item.filename

    def ensure_thumbnail(self, item: WallpaperItem) -> Optional[str]:
        """Download thumbnail if not already cached. Returns local file path."""
        target_path = self.get_thumb_cache_path(item)
        if target_path.is_file() and target_path.stat().st_size > 0:
            item.local_thumb = str(target_path)
            return item.local_thumb

        if not item.thumb_url:
            return None

        try:
            resp = self.session.get(item.thumb_url, timeout=10, stream=True)
            resp.raise_for_status()
            with open(target_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            item.local_thumb = str(target_path)
            return item.local_thumb
        except Exception as e:
            logger.error("Failed to download thumbnail for '%s': %s", item.title, e)
            if target_path.is_file():
                target_path.unlink(missing_ok=True)
            return None

    def ensure_full_image(self, item: WallpaperItem) -> Optional[str]:
        """Download full high-resolution wallpaper if not already cached."""
        target_path = self.get_full_cache_path(item)
        if target_path.is_file() and target_path.stat().st_size > 50000:
            item.local_full = str(target_path)
            return item.local_full

        if not item.full_url:
            return None

        try:
            resp = self.session.get(item.full_url, timeout=20, stream=True)
            resp.raise_for_status()
            with open(target_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=16384):
                    f.write(chunk)
            item.local_full = str(target_path)
            return item.local_full
        except Exception as e:
            logger.error("Failed to download full image for '%s': %s", item.title, e)
            if target_path.is_file():
                target_path.unlink(missing_ok=True)
            return None

    def save_to_pictures(self, item: WallpaperItem) -> Optional[Path]:
        """Copies high-resolution wallpaper to ~/Pictures/BingWallpapers with clean name."""
        cached_full = self.ensure_full_image(item)
        if not cached_full or not Path(cached_full).is_file():
            return None

        # Clean sanitized filename
        clean_title = re.sub(r'[\\/*?:"<>|]', "", item.title).strip() or item.filename
        if not clean_title.lower().endswith(".jpg"):
            clean_title = f"{clean_title}.jpg"

        dest_path = PICTURES_DIR / clean_title
        try:
            shutil.copy2(cached_full, dest_path)
            logger.info("Saved wallpaper to pictures: %s", dest_path)
            return dest_path
        except Exception as e:
            logger.error("Failed to save wallpaper to pictures: %s", e)
            return None
