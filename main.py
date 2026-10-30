#!/usr/bin/env python3
import sys
import os
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from bing_wallpaper.config import APP_NAME, APP_ID, VERSION
from bing_wallpaper.ui.main_window import MainWindow
from bing_wallpaper.wallpaper_manager import KdeWallpaperManager
from bing_wallpaper.scraper import BingPosterScraper
from bing_wallpaper.downloader import ImageDownloader
from bing_wallpaper.storage import StorageManager

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

def handle_cli_next(category: str = "hot"):
    """Quickly fetches and sets a new wallpaper without GUI."""
    print(f"Fetching next wallpaper from '{category}'...")
    scraper = BingPosterScraper()
    items = scraper.fetch_page(category, page=1)
    if not items:
        print("No wallpapers found.")
        sys.exit(1)

    import random
    selected = random.choice(items[:10])
    print(f"Selected: {selected.title}")
    
    downloader = ImageDownloader()
    full_path = downloader.ensure_full_image(selected)
    if not full_path:
        print("Failed to download image.")
        sys.exit(1)

    mgr = KdeWallpaperManager()
    storage = StorageManager()
    success = mgr.set_wallpaper(full_path)
    if success:
        storage.add_to_history(selected.id)
        storage.save_wallpaper(selected)
        print(f"Successfully applied wallpaper: {selected.title}")
    else:
        print("Failed to apply wallpaper to KDE Plasma.")
        sys.exit(1)

def main():
    setup_logging()

    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{VERSION} for Fedora KDE Plasma")
    parser.add_argument("--tray", action="store_true", help="Start minimized directly to the system tray")
    parser.add_argument("--next", action="store_true", help="Apply next random wallpaper immediately from CLI")
    parser.add_argument("--category", choices=["hot", "new"], default="hot", help="Category for CLI mode")
    args = parser.parse_args()

    if args.next:
        handle_cli_next(args.category)
        return

    # Enable high-dpi and desktop identity in KDE
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setDesktopFileName("com.github.bing_wallpaper_kde.desktop")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()

    if not args.tray:
        window.show()
    else:
        logging.info("Starting in background system tray mode.")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
