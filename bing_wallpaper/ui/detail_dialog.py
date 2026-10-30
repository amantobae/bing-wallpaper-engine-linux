import webbrowser
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextBrowser, QFrame, QSizePolicy
)
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtCore import Qt, Signal

from ..models import WallpaperItem

class DetailDialog(QDialog):
    """Windows Spotlight-inspired detail view for Bing Wallpapers."""
    apply_requested = Signal(WallpaperItem)
    save_requested = Signal(WallpaperItem)
    fav_requested = Signal(WallpaperItem, bool)

    def __init__(self, item: WallpaperItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(item.title)
        self.resize(760, 640)
        self.setModal(True)
        self._init_ui()
        self.populate_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Image Preview Frame
        self.image_container = QLabel()
        self.image_container.setFixedHeight(360)
        self.image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_container.setStyleSheet("background-color: #121316; border-radius: 10px;")
        layout.addWidget(self.image_container)

        # 2. Header Info: Title & Subtitle
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.meta_label = QLabel()
        self.meta_label.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(self.meta_label)

        # 3. Description Story
        self.desc_browser = QTextBrowser()
        self.desc_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #24252a;
                border: 1px solid #32343c;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
                color: #e2e8f0;
            }
        """)
        self.desc_browser.setOpenExternalLinks(True)
        self.desc_browser.setFixedHeight(110)
        layout.addWidget(self.desc_browser)

        # 4. Action Buttons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        self.btn_apply = QPushButton("Set as Wallpaper")
        self.btn_apply.setProperty("class", "primary-btn")
        self.btn_apply.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_apply.clicked.connect(self._on_apply)
        btn_bar.addWidget(self.btn_apply)

        self.btn_save = QPushButton("Save to Pictures")
        self.btn_save.setProperty("class", "secondary-btn")
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self._on_save)
        btn_bar.addWidget(self.btn_save)

        self.btn_fav = QPushButton("Add to Favorites")
        self.btn_fav.setProperty("class", "secondary-btn")
        self.btn_fav.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_fav.clicked.connect(self._on_fav)
        btn_bar.addWidget(self.btn_fav)

        self.btn_web = QPushButton("Open in Browser")
        self.btn_web.setProperty("class", "secondary-btn")
        self.btn_web.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_web.clicked.connect(self._on_web)
        btn_bar.addWidget(self.btn_web)

        btn_bar.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.setProperty("class", "secondary-btn")
        self.btn_close.clicked.connect(self.close)
        btn_bar.addWidget(self.btn_close)

        layout.addLayout(btn_bar)

    def populate_data(self):
        self.title_label.setText(self.item.title)

        meta = []
        if self.item.date_str:
            meta.append(self.item.date_str)
        if self.item.country:
            meta.append(self.item.country)
        meta.append("1920x1080 (Full HD)")
        self.meta_label.setText("   •   ".join(meta))

        # Description
        story = self.item.description or "Loading wallpaper story from Bing..."
        self.desc_browser.setText(story)

        # Image preview
        img_path = self.item.local_full or self.item.local_thumb
        if img_path and Path(img_path).is_file():
            pix = QPixmap(img_path)
            if not pix.isNull():
                scaled = pix.scaled(
                    self.image_container.width(), self.image_container.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_container.setPixmap(scaled)
        else:
            self.image_container.setText("Loading high-resolution image...")

        self.btn_fav.setText("Remove from Favorites" if self.item.is_favorite else "Add to Favorites")

    def update_description(self, description: str):
        self.item.description = description
        self.desc_browser.setText(description)

    def _on_apply(self):
        self.apply_requested.emit(self.item)

    def _on_save(self):
        self.save_requested.emit(self.item)

    def _on_fav(self):
        new_fav = not self.item.is_favorite
        self.item.is_favorite = new_fav
        self.btn_fav.setText("Remove from Favorites" if new_fav else "Add to Favorites")
        self.fav_requested.emit(self.item, new_fav)

    def _on_web(self):
        if self.item.link:
            webbrowser.open(self.item.link)
