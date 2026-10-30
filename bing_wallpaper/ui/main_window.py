import random
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QGridLayout,
    QButtonGroup, QStatusBar, QMessageBox, QApplication
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QThreadPool, QRunnable, QObject, Signal, QTimer

from ..config import APP_NAME, VERSION
from ..models import WallpaperItem
from ..scraper import BingPosterScraper
from ..wallpaper_manager import KdeWallpaperManager
from ..storage import StorageManager
from ..downloader import ImageDownloader
from .styles import MODERN_STYLE
from .monitor_preview import HeroMonitorSection
from .wallpaper_card import WallpaperCard
from .detail_dialog import DetailDialog
from .tray_icon import BingTrayIcon, create_default_tray_icon

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(str)
    result = Signal(object)


class FetchPageRunnable(QRunnable):
    """Fetches list of wallpapers from bing.gifposter.com in background."""
    def __init__(self, scraper: BingPosterScraper, category: str, page: int):
        super().__init__()
        self.scraper = scraper
        self.category = category
        self.page = page
        self.signals = WorkerSignals()

    def run(self):
        try:
            items = self.scraper.fetch_page(self.category, self.page)
            self.signals.result.emit(items)
        except RuntimeError:
            pass
        except Exception as e:
            try:
                self.signals.error.emit(str(e))
            except RuntimeError:
                pass
        finally:
            try:
                self.signals.finished.emit()
            except RuntimeError:
                pass


class DownloadThumbRunnable(QRunnable):
    """Downloads thumbnail in background and notifies card to update."""
    def __init__(self, downloader: ImageDownloader, item: WallpaperItem, card: WallpaperCard):
        super().__init__()
        self.downloader = downloader
        self.item = item
        self.card = card
        self.signals = WorkerSignals()

    def run(self):
        try:
            path = self.downloader.ensure_thumbnail(self.item)
            if path:
                self.signals.result.emit(path)
        except RuntimeError:
            pass
        except Exception as e:
            try:
                self.signals.error.emit(str(e))
            except RuntimeError:
                pass
        finally:
            try:
                self.signals.finished.emit()
            except RuntimeError:
                pass


class MainWindow(QMainWindow):
    """Main application window for Bing Wallpaper Manager."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setWindowIcon(create_default_tray_icon())
        self.resize(1180, 840)
        self.setMinimumSize(850, 600)
        self.setStyleSheet(MODERN_STYLE)

        # Core services
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(8)
        self.scraper = BingPosterScraper()
        self.wallpaper_mgr = KdeWallpaperManager()
        self.storage = StorageManager()
        self.downloader = ImageDownloader()
        self.settings = self.storage.load_settings()

        # State
        self.current_category = "hot"  # hot, new, favorites, history
        self.current_page = 1
        self.wallpaper_items: List[WallpaperItem] = []
        self.cards: List[WallpaperCard] = []
        self._active_runnables = set()

        self._init_ui()
        self._init_tray()
        self._init_auto_timer()
        self._load_current_wallpaper()

        # Load initial category
        self._load_category("hot", page=1)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Category / Navigation Bar
        nav_bar = QWidget()
        nav_bar.setObjectName("NavBar")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(16, 8, 16, 8)
        nav_layout.setSpacing(10)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_hot = QPushButton("Hot")
        self.btn_hot.setProperty("class", "nav-btn")
        self.btn_hot.setCheckable(True)
        self.btn_hot.setChecked(True)
        self.nav_group.addButton(self.btn_hot)
        nav_layout.addWidget(self.btn_hot)

        self.btn_new = QPushButton("New")
        self.btn_new.setProperty("class", "nav-btn")
        self.btn_new.setCheckable(True)
        self.nav_group.addButton(self.btn_new)
        nav_layout.addWidget(self.btn_new)

        self.btn_favs = QPushButton("Favorites")
        self.btn_favs.setProperty("class", "nav-btn")
        self.btn_favs.setCheckable(True)
        self.nav_group.addButton(self.btn_favs)
        nav_layout.addWidget(self.btn_favs)

        self.btn_hist = QPushButton("History")
        self.btn_hist.setProperty("class", "nav-btn")
        self.btn_hist.setCheckable(True)
        self.nav_group.addButton(self.btn_hist)
        nav_layout.addWidget(self.btn_hist)

        nav_layout.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setProperty("class", "secondary-btn")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        nav_layout.addWidget(self.btn_refresh)

        main_layout.addWidget(nav_bar)

        # Connect nav buttons
        self.btn_hot.clicked.connect(lambda: self._load_category("hot", page=1))
        self.btn_new.clicked.connect(lambda: self._load_category("new", page=1))
        self.btn_favs.clicked.connect(lambda: self._load_category("favorites", page=1))
        self.btn_hist.clicked.connect(lambda: self._load_category("history", page=1))

        # 2. Hero Section (Monitor & Current Desktop Wallpaper)
        self.hero_section = HeroMonitorSection()
        self.hero_section.set_fill_mode(self.settings.get("fill_mode", "preserveAspectCrop"))
        self.hero_section.set_auto_change(self.settings.get("auto_change_enabled", False))
        self.hero_section.fill_mode_changed.connect(self._on_fill_mode_changed)
        self.hero_section.auto_change_toggled.connect(self._on_auto_change_toggled)
        self.hero_section.random_requested.connect(self._apply_random_wallpaper)
        main_layout.addWidget(self.hero_section)

        # 3. Main Grid Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(20, 16, 20, 20)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area, 1)

        # 4. Bottom Controls: Load More
        bottom_bar = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 6, 20, 8)

        self.btn_load_more = QPushButton("Load More")
        self.btn_load_more.setProperty("class", "secondary-btn")
        self.btn_load_more.setFixedHeight(36)
        self.btn_load_more.clicked.connect(self._load_next_page)
        bottom_layout.addWidget(self.btn_load_more)

        main_layout.addWidget(bottom_bar)

        # 5. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _init_tray(self):
        self.tray = BingTrayIcon(self)
        self.tray.open_window_requested.connect(self._show_and_raise)
        self.tray.next_wallpaper_requested.connect(self._apply_random_wallpaper)
        self.tray.auto_change_toggled.connect(self._on_auto_change_toggled)
        self.tray.quit_requested.connect(QApplication.instance().quit)
        self.tray.set_auto_change_state(self.settings.get("auto_change_enabled", False))
        self.tray.show()

    def _init_auto_timer(self):
        # Check every 15 minutes for daily auto-rotation
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self._check_auto_rotation)
        self.auto_timer.start(15 * 60 * 1000)

    def _show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _load_current_wallpaper(self):
        curr_path = self.wallpaper_mgr.get_current_wallpaper()
        title = Path(curr_path).stem if curr_path else "KDE Wallpaper"
        self.hero_section.set_current_wallpaper(curr_path, title)
        self.tray.set_current_title(title)

    def _start_runnable(self, runnable):
        """Keep strong reference until runnable finishes."""
        self._active_runnables.add(runnable)
        runnable.signals.finished.connect(lambda: self._active_runnables.discard(runnable))
        self.thread_pool.start(runnable)

    def _load_category(self, category: str, page: int = 1):
        self.current_category = category
        self.current_page = page
        self.status_bar.showMessage(f"Loading '{category}' category...")

        if page == 1:
            self._clear_grid()
            self.wallpaper_items = []

        if category in ("hot", "new"):
            self.btn_load_more.setVisible(True)
            self.btn_load_more.setEnabled(False)
            runnable = FetchPageRunnable(self.scraper, category, page)
            runnable.signals.result.connect(self._on_items_fetched)
            runnable.signals.error.connect(lambda err: self.status_bar.showMessage(f"Error: {err}"))
            runnable.signals.finished.connect(lambda: self.btn_load_more.setEnabled(True))
            self._start_runnable(runnable)
        elif category == "favorites":
            self.btn_load_more.setVisible(False)
            items = self.storage.get_favorites()
            self._render_items(items)
            self.status_bar.showMessage(f"Favorites: {len(items)} items")
        elif category == "history":
            self.btn_load_more.setVisible(False)
            items = self.storage.get_history(limit=50)
            self._render_items(items)
            self.status_bar.showMessage(f"History: {len(items)} items")

    def _on_items_fetched(self, items: List[WallpaperItem]):
        if not items:
            self.status_bar.showMessage("No more wallpapers found.")
            self.btn_load_more.setEnabled(False)
            return

        # Synchronize favorites state from DB
        for it in items:
            it.is_favorite = self.storage.is_favorite(it.id)
            self.storage.save_wallpaper(it)

        self.wallpaper_items.extend(items)
        self._render_items(items, append=True)
        self.status_bar.showMessage(f"Loaded {len(self.wallpaper_items)} wallpapers.")

    def _load_next_page(self):
        self.current_page += 1
        self._load_category(self.current_category, page=self.current_page)

    def _on_refresh_clicked(self):
        self._load_current_wallpaper()
        self._load_category(self.current_category, page=1)

    def _clear_grid(self):
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

    def _render_items(self, items: List[WallpaperItem], append: bool = False):
        if not append:
            self._clear_grid()
            self.wallpaper_items = list(items)

        columns = 3  # Responsive columns
        start_idx = len(self.cards)

        for i, item in enumerate(items):
            card = WallpaperCard(item)
            card.apply_clicked.connect(self._apply_wallpaper)
            card.favorite_toggled.connect(self._toggle_favorite)
            card.details_clicked.connect(self._show_details)

            grid_idx = start_idx + i
            row = grid_idx // columns
            col = grid_idx % columns
            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)

            # Kick off async thumbnail loading
            self._start_thumb_download(item, card)

    def _start_thumb_download(self, item: WallpaperItem, card: WallpaperCard):
        runnable = DownloadThumbRunnable(self.downloader, item, card)
        def on_done(path):
            item.local_thumb = path
            card.update_thumbnail()
            self.storage.save_wallpaper(item)
        runnable.signals.result.connect(on_done)
        self._start_runnable(runnable)

    def _apply_wallpaper(self, item: WallpaperItem):
        self.status_bar.showMessage(f"Applying wallpaper '{item.title}'...")
        # Run download in thread to avoid UI freeze
        class ApplyRunnable(QRunnable):
            def __init__(self, downloader, mgr, storage, item, fill_mode):
                super().__init__()
                self.downloader = downloader
                self.mgr = mgr
                self.storage = storage
                self.item = item
                self.fill_mode = fill_mode
                self.signals = WorkerSignals()

            def run(self):
                try:
                    full_path = self.downloader.ensure_full_image(self.item)
                    if not full_path:
                        self.signals.error.emit("Failed to download wallpaper.")
                        return

                    success = self.mgr.set_wallpaper(full_path, self.fill_mode)
                    if success:
                        self.storage.add_to_history(self.item.id)
                        self.signals.result.emit(full_path)
                    else:
                        self.signals.error.emit("KDE Plasma could not apply wallpaper.")
                except RuntimeError:
                    pass
                except Exception as e:
                    try:
                        self.signals.error.emit(str(e))
                    except RuntimeError:
                        pass
                finally:
                    try:
                        self.signals.finished.emit()
                    except RuntimeError:
                        pass

        fill_mode = self.settings.get("fill_mode", "preserveAspectCrop")
        runnable = ApplyRunnable(self.downloader, self.wallpaper_mgr, self.storage, item, fill_mode)

        def on_applied(full_path):
            self.hero_section.set_current_wallpaper(full_path, item.title)
            self.tray.set_current_title(item.title)
            self.tray.showMessage(
                APP_NAME,
                f"New wallpaper applied:\n{item.title}",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
            self.status_bar.showMessage(f"Wallpaper applied successfully: {item.title}")

        runnable.signals.result.connect(on_applied)
        runnable.signals.error.connect(lambda err: QMessageBox.warning(self, "Setting Error", err))
        self._start_runnable(runnable)

    def _apply_random_wallpaper(self):
        if not self.wallpaper_items:
            self.status_bar.showMessage("Please load wallpapers first.")
            return
        item = random.choice(self.wallpaper_items)
        self._apply_wallpaper(item)

    def _toggle_favorite(self, item: WallpaperItem, is_fav: bool):
        item.is_favorite = is_fav
        self.storage.set_favorite(item.id, is_fav)
        self.storage.save_wallpaper(item)
        if self.current_category == "favorites" and not is_fav:
            self._load_category("favorites")

    def _show_details(self, item: WallpaperItem):
        dlg = DetailDialog(item, self)
        dlg.apply_requested.connect(self._apply_wallpaper)
        dlg.fav_requested.connect(self._toggle_favorite)

        def on_save(it):
            dest = self.downloader.save_to_pictures(it)
            if dest:
                QMessageBox.information(self, "Saved", f"Wallpaper saved to:\n{dest}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save file.")
        dlg.save_requested.connect(on_save)

        # Enrich description in background if empty
        if not item.description:
            class EnrichRunnable(QRunnable):
                def __init__(self, scraper, item):
                    super().__init__()
                    self.scraper = scraper
                    self.item = item
                    self.signals = WorkerSignals()
                def run(self):
                    try:
                        self.scraper.enrich_details(self.item)
                        self.signals.result.emit(self.item.description)
                    except RuntimeError:
                        pass
                    except Exception:
                        pass
                    finally:
                        try:
                            self.signals.finished.emit()
                        except RuntimeError:
                            pass
            er = EnrichRunnable(self.scraper, item)
            er.signals.result.connect(lambda desc: dlg.update_description(desc))
            self._start_runnable(er)

        dlg.exec()

    def _on_fill_mode_changed(self, mode: str):
        self.settings["fill_mode"] = mode
        self.storage.save_settings(self.settings)
        # Re-apply current if available
        curr = self.wallpaper_mgr.get_current_wallpaper()
        if curr:
            self.wallpaper_mgr.set_wallpaper(curr, fill_mode=mode)

    def _on_auto_change_toggled(self, enabled: bool):
        self.settings["auto_change_enabled"] = enabled
        self.storage.save_settings(self.settings)
        self.hero_section.set_auto_change(enabled)
        self.tray.set_auto_change_state(enabled)
        state_str = "enabled" if enabled else "disabled"
        self.status_bar.showMessage(f"Daily auto-change is {state_str}")

    def _check_auto_rotation(self):
        if not self.settings.get("auto_change_enabled", False):
            return

        last_change = self.settings.get("last_auto_change", 0)
        interval_secs = self.settings.get("auto_change_interval_hours", 24) * 3600
        now = time.time()

        if now - last_change >= interval_secs:
            logger.info("Executing scheduled daily wallpaper change...")
            self.settings["last_auto_change"] = now
            self.storage.save_settings(self.settings)
            self._apply_random_wallpaper()

    def closeEvent(self, event):
        # Minimize to tray instead of quitting if tray is available
        if self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                APP_NAME,
                "Application minimized to system tray.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
