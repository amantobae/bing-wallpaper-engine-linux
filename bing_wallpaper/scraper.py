import re
import logging
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, NEW_URL, HOT_URL, DEFAULT_HEADERS
from .models import WallpaperItem

logger = logging.getLogger(__name__)

class BingPosterScraper:
    """Scraper for bing.gifposter.com wallpapers gallery."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def get_category_url(self, category: str, page: int = 1) -> str:
        base = HOT_URL if category.lower() == "hot" else NEW_URL
        if page > 1:
            return f"{base}?p={page}"
        return base

    def fetch_page(self, category: str = "new", page: int = 1) -> List[WallpaperItem]:
        """Fetch list of wallpapers for specified category and page."""
        url = self.get_category_url(category, page)
        try:
            resp = self.session.get(url, timeout=12)
            resp.raise_for_status()
            return self._parse_list_page(resp.text, category)
        except Exception as e:
            logger.error("Failed to fetch %s (page %d): %s", category, page, e)
            return []

    def _parse_list_page(self, html: str, category: str) -> List[WallpaperItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: List[WallpaperItem] = []

        # Find all li elements containing image cards
        for li in soup.find_all("li"):
            a = li.find("a")
            img = li.find("img")
            if not a or not img:
                continue

            thumb_url = img.get("src", "")
            if "bingImages" not in thumb_url:
                continue

            title = (img.get("alt") or "").strip()
            if not title:
                # Fallback to link title or text
                title = (a.get("title") or a.text or "Bing Wallpaper").strip()

            detail_link = a.get("href", "")
            if detail_link.startswith("/"):
                detail_link = BASE_URL + detail_link

            # Clean full URL by stripping preview suffix (_sm or _mb)
            full_url = re.sub(r"_(sm|mb)$", "", thumb_url)

            # Optional extra text in card (often contains date)
            extra_text = li.text.strip()
            date_match = re.search(r"(\w{3,9}\s+\d{1,2},\s+\d{4})", extra_text)
            date_str = date_match.group(1) if date_match else ""

            item = WallpaperItem(
                title=title,
                link=detail_link,
                thumb_url=thumb_url,
                full_url=full_url,
                date_str=date_str,
                category=category
            )
            items.append(item)

        return items

    def enrich_details(self, item: WallpaperItem) -> WallpaperItem:
        """Fetch full description, date and country from the detail page."""
        if not item.link:
            return item

        try:
            resp = self.session.get(item.link, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract detailed title and date from h1/h2
            header = soup.find(["h1", "h2"])
            if header:
                h_text = header.text.strip()
                date_match = re.search(r"(\w{3,9}\s+\d{1,2},\s+\d{4})", h_text)
                if date_match and not item.date_str:
                    item.date_str = date_match.group(1)

            # Description is typically in a <p> with descriptive length
            desc_paragraphs = [
                p.text.strip() for p in soup.find_all("p")
                if len(p.text.strip()) > 40 and not p.text.strip().startswith("Copyright")
            ]
            if desc_paragraphs:
                item.description = desc_paragraphs[0]

            # Country/Market
            spans = [s.text.strip() for s in soup.find_all("span") if s.text.strip()]
            for span in spans:
                if span in ["UNITED STATES", "CANADA", "UNITED KINGDOM", "GERMANY", "FRANCE", "JAPAN", "CHINA", "AUSTRALIA", "BRAZIL"]:
                    item.country = span
                    break

        except Exception as e:
            logger.warning("Failed to enrich details for %s: %s", item.title, e)

        return item
