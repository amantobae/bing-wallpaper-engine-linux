import os
from pathlib import Path

APP_NAME = "Bing Wallpaper Manager"
APP_ID = "com.github.bing_wallpaper_kde"
VERSION = "1.0.0"

HOME = Path.home()

# Cache and Storage Paths
CACHE_DIR = HOME / ".cache" / "bing-wallpaper"
THUMBS_DIR = CACHE_DIR / "thumbs"
WALLPAPERS_CACHE_DIR = CACHE_DIR / "wallpapers"

DATA_DIR = HOME / ".local" / "share" / "bing-wallpaper"
DB_PATH = DATA_DIR / "wallpapers.db"

PICTURES_DIR = HOME / "Pictures" / "BingWallpapers"
CONFIG_DIR = HOME / ".config" / "bing-wallpaper"
CONFIG_FILE = CONFIG_DIR / "settings.json"

# Ensure essential directories exist
for directory in [CACHE_DIR, THUMBS_DIR, WALLPAPERS_CACHE_DIR, DATA_DIR, PICTURES_DIR, CONFIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Web & Scraping
BASE_URL = "https://bing.gifposter.com"
NEW_URL = f"{BASE_URL}/list/new/desc/classic.html"
HOT_URL = f"{BASE_URL}/list/hot/desc/classic.html"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
}

DEFAULT_SETTINGS = {
    "fill_mode": "preserveAspectCrop",  # preserveAspectCrop, preserveAspectFit, stretch
    "auto_change_enabled": False,
    "auto_change_interval_hours": 24,
    "auto_change_category": "hot",       # hot or new
    "last_auto_change": 0,
    "save_to_pictures": True,
    "notify_on_change": True,
}
