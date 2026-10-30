from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtCore import Qt, Signal

from ..models import WallpaperItem

class ImagePreviewLabel(QLabel):
    """Clickable image preview label."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(264, 150)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #1a1b1f; border-radius: 8px;")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class WallpaperCard(QFrame):
    """Modern card representation of a Bing Wallpaper."""
    apply_clicked = Signal(WallpaperItem)
    favorite_toggled = Signal(WallpaperItem, bool)
    details_clicked = Signal(WallpaperItem)

    def __init__(self, item: WallpaperItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("CardFrame")
        self.setFixedWidth(284)
        self._init_ui()
        self.update_data(item)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Thumbnail Image Preview
        self.img_preview = ImagePreviewLabel()
        self.img_preview.clicked.connect(lambda: self.details_clicked.emit(self.item))
        layout.addWidget(self.img_preview)

        # 2. Title & Date
        self.title_label = QLabel()
        self.title_label.setObjectName("CardTitle")
        self.title_label.setWordWrap(False)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(self.title_label)

        self.date_label = QLabel()
        self.date_label.setObjectName("CardDate")
        layout.addWidget(self.date_label)

        # 3. Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setProperty("class", "primary-btn")
        self.btn_apply.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_apply.clicked.connect(lambda: self.apply_clicked.emit(self.item))
        btn_row.addWidget(self.btn_apply, 1)

        self.btn_fav = QPushButton("Fav")
        self.btn_fav.setProperty("class", "secondary-btn")
        self.btn_fav.setFixedWidth(54)
        self.btn_fav.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_fav.clicked.connect(self._on_fav_clicked)
        btn_row.addWidget(self.btn_fav)

        self.btn_info = QPushButton("Info")
        self.btn_info.setProperty("class", "secondary-btn")
        self.btn_info.setFixedWidth(54)
        self.btn_info.setToolTip("View wallpaper details")
        self.btn_info.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_info.clicked.connect(lambda: self.details_clicked.emit(self.item))
        btn_row.addWidget(self.btn_info)

        layout.addLayout(btn_row)

    def update_data(self, item: WallpaperItem):
        self.item = item
        # Truncate title for card display
        display_title = item.title
        if len(display_title) > 34:
            display_title = display_title[:31] + "..."
        self.title_label.setText(display_title)
        self.title_label.setToolTip(item.title)

        date_country = []
        if item.date_str:
            date_country.append(item.date_str)
        if item.country:
            date_country.append(item.country)
        self.date_label.setText(" • ".join(date_country) if date_country else "Bing Wallpaper")

        self.btn_fav.setText("Saved" if item.is_favorite else "Fav")
        self.btn_fav.setToolTip("Remove from favorites" if item.is_favorite else "Add to favorites")
        self.update_thumbnail()

    def update_thumbnail(self):
        if self.item.local_thumb and Path(self.item.local_thumb).is_file():
            pix = QPixmap(self.item.local_thumb)
            if not pix.isNull():
                scaled = pix.scaled(
                    self.img_preview.width(), self.img_preview.height(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.img_preview.setPixmap(scaled)
                return

        # Placeholder loading state
        self.img_preview.setText("Loading...")

    def _on_fav_clicked(self):
        new_fav = not self.item.is_favorite
        self.item.is_favorite = new_fav
        self.btn_fav.setText("Saved" if new_fav else "Fav")
        self.btn_fav.setToolTip("Remove from favorites" if new_fav else "Add to favorites")
        self.favorite_toggled.emit(self.item, new_fav)
