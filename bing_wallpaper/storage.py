import json
import sqlite3
import time
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from .config import DB_PATH, CONFIG_FILE, DEFAULT_SETTINGS
from .models import WallpaperItem

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages SQLite storage for wallpapers, favorites, history, and JSON settings."""

    def __init__(self, db_path: Path = DB_PATH, config_file: Path = CONFIG_FILE):
        self.db_path = db_path
        self.config_file = config_file
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS wallpapers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    link TEXT,
                    thumb_url TEXT,
                    full_url TEXT,
                    date_str TEXT,
                    country TEXT,
                    description TEXT,
                    local_thumb TEXT,
                    local_full TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    category TEXT,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallpaper_id TEXT NOT NULL,
                    applied_at REAL NOT NULL,
                    FOREIGN KEY (wallpaper_id) REFERENCES wallpapers(id)
                );

                CREATE INDEX IF NOT EXISTS idx_wallpapers_fav ON wallpapers(is_favorite);
                CREATE INDEX IF NOT EXISTS idx_history_time ON history(applied_at DESC);
            """)

    def save_wallpaper(self, item: WallpaperItem):
        """Insert or update a wallpaper item."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO wallpapers (
                    id, title, link, thumb_url, full_url, date_str,
                    country, description, local_thumb, local_full,
                    is_favorite, category, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=coalesce(nullif(excluded.title, ''), wallpapers.title),
                    link=coalesce(nullif(excluded.link, ''), wallpapers.link),
                    thumb_url=coalesce(nullif(excluded.thumb_url, ''), wallpapers.thumb_url),
                    full_url=coalesce(nullif(excluded.full_url, ''), wallpapers.full_url),
                    date_str=coalesce(nullif(excluded.date_str, ''), wallpapers.date_str),
                    country=coalesce(nullif(excluded.country, ''), wallpapers.country),
                    description=coalesce(nullif(excluded.description, ''), wallpapers.description),
                    local_thumb=coalesce(nullif(excluded.local_thumb, ''), wallpapers.local_thumb),
                    local_full=coalesce(nullif(excluded.local_full, ''), wallpapers.local_full),
                    category=coalesce(nullif(excluded.category, ''), wallpapers.category),
                    updated_at=excluded.updated_at;
            """, (
                item.id, item.title, item.link, item.thumb_url, item.full_url,
                item.date_str, item.country, item.description, item.local_thumb,
                item.local_full, 1 if item.is_favorite else 0, item.category,
                time.time()
            ))

    def get_wallpaper(self, wallpaper_id: str) -> Optional[WallpaperItem]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM wallpapers WHERE id = ?", (wallpaper_id,)).fetchone()
            if row:
                return self._row_to_item(row)
        return None

    def set_favorite(self, wallpaper_id: str, is_favorite: bool):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE wallpapers SET is_favorite = ? WHERE id = ?",
                (1 if is_favorite else 0, wallpaper_id)
            )

    def is_favorite(self, wallpaper_id: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute("SELECT is_favorite FROM wallpapers WHERE id = ?", (wallpaper_id,)).fetchone()
            return bool(row and row["is_favorite"])

    def get_favorites(self) -> List[WallpaperItem]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM wallpapers WHERE is_favorite = 1 ORDER BY updated_at DESC").fetchall()
            return [self._row_to_item(r) for r in rows]

    def add_to_history(self, wallpaper_id: str):
        with self._get_conn() as conn:
            conn.execute("INSERT INTO history (wallpaper_id, applied_at) VALUES (?, ?)", (wallpaper_id, time.time()))

    def get_history(self, limit: int = 50) -> List[WallpaperItem]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT w.*, h.applied_at FROM history h
                JOIN wallpapers w ON h.wallpaper_id = w.id
                ORDER BY h.applied_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [self._row_to_item(r) for r in rows]

    def _row_to_item(self, row: sqlite3.Row) -> WallpaperItem:
        return WallpaperItem(
            title=row["title"],
            link=row["link"] or "",
            thumb_url=row["thumb_url"] or "",
            full_url=row["full_url"] or "",
            date_str=row["date_str"] or "",
            country=row["country"] or "",
            description=row["description"] or "",
            local_thumb=row["local_thumb"],
            local_full=row["local_full"],
            is_favorite=bool(row["is_favorite"]),
            category=row["category"] or "new"
        )

    # Settings JSON management
    def load_settings(self) -> Dict[str, Any]:
        settings = dict(DEFAULT_SETTINGS)
        if self.config_file.is_file():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    settings.update(data)
            except Exception as e:
                logger.error("Failed to load settings: %s", e)
        return settings

    def save_settings(self, settings: Dict[str, Any]):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save settings: %s", e)
