from dataclasses import dataclass, asdict
from typing import Optional
import hashlib

@dataclass
class WallpaperItem:
    title: str
    link: str
    thumb_url: str
    full_url: str
    date_str: str = ""
    country: str = ""
    description: str = ""
    local_thumb: Optional[str] = None
    local_full: Optional[str] = None
    is_favorite: bool = False
    is_current: bool = False
    category: str = "new"

    @property
    def id(self) -> str:
        """Stable unique identifier based on full image URL."""
        return hashlib.md5(self.full_url.encode("utf-8")).hexdigest()

    @property
    def filename(self) -> str:
        """Normalized filename extracted from full URL."""
        raw_name = self.full_url.split("/")[-1].split("?")[0]
        if not raw_name.endswith(".jpg") and not raw_name.endswith(".png"):
            raw_name = f"{self.id}.jpg"
        return raw_name

    def to_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        d["filename"] = self.filename
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "WallpaperItem":
        # Filter out derived fields if present
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**filtered)
