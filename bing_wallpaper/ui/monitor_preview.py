from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QFrame, QPushButton, QComboBox, QCheckBox, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath
from PySide6.QtCore import Qt, Signal

class MonitorDisplayWidget(QWidget):
    """Draws a mini monitor with rounded screen corners and stand."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 160)
        self._pixmap: Optional[QPixmap] = None

    def set_image(self, image_path: Optional[str]):
        if image_path and Path(image_path).is_file():
            self._pixmap = QPixmap(image_path)
        else:
            self._pixmap = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Monitor outer bezel
        bezel_x, bezel_y, bezel_w, bezel_h = 10, 10, 240, 135
        corner_radius = 8

        # Draw stand base
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#2d2f36")))
        # stand neck
        painter.drawRect(120, 140, 20, 12)
        # stand foot
        painter.drawRoundedRect(95, 148, 70, 7, 3, 3)

        # Draw bezel
        painter.setBrush(QBrush(QColor("#18191c")))
        painter.setPen(QColor("#3f3f46"))
        painter.drawRoundedRect(bezel_x, bezel_y, bezel_w, bezel_h, corner_radius, corner_radius)

        # Draw screen image
        screen_x, screen_y, screen_w, screen_h = bezel_x + 6, bezel_y + 6, bezel_w - 12, bezel_h - 12
        screen_path = QPainterPath()
        screen_path.addRoundedRect(screen_x, screen_y, screen_w, screen_h, 4, 4)

        painter.save()
        painter.setClipPath(screen_path)

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                screen_w, screen_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            # Center crop
            crop_x = (scaled.width() - screen_w) // 2
            crop_y = (scaled.height() - screen_h) // 2
            painter.drawPixmap(screen_x, screen_y, scaled, crop_x, crop_y, screen_w, screen_h)
        else:
            # Fallback default desktop gradient
            painter.fillRect(screen_x, screen_y, screen_w, screen_h, QColor("#1e293b"))
            painter.setPen(QColor("#64748b"))
            painter.drawText(screen_x, screen_y, screen_w, screen_h, Qt.AlignmentFlag.AlignCenter, "No active wallpaper")

        painter.restore()


class HeroMonitorSection(QFrame):
    """
    Windows 11 Personalization style top banner displaying the active desktop wallpaper,
    quick controls (Random, Fill Mode, Auto-change toggle).
    """
    random_requested = Signal()
    refresh_requested = Signal()
    fill_mode_changed = Signal(str)
    auto_change_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeroFrame")
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 16, 10)
        main_layout.setSpacing(24)

        # 1. Left: Monitor Display
        self.monitor = MonitorDisplayWidget()
        main_layout.addWidget(self.monitor)

        # 2. Right: Information and Controls
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # Status badge & Title
        status_row = QHBoxLayout()
        self.status_badge = QLabel("Current KDE Plasma Wallpaper")
        self.status_badge.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: bold;")
        status_row.addWidget(self.status_badge)
        status_row.addStretch()
        info_layout.addLayout(status_row)

        self.title_label = QLabel("Loading wallpaper details...")
        self.title_label.setObjectName("HeroTitle")
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        self.path_label = QLabel("")
        self.path_label.setObjectName("HeroSubtitle")
        self.path_label.setWordWrap(True)
        info_layout.addWidget(self.path_label)

        # Controls Row: Fill Mode, Random Button, Auto-change checkbox
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(12)

        ctrl_row.addWidget(QLabel("Fit:"))
        self.combo_fill = QComboBox()
        self.combo_fill.addItem("Crop to Fit", "preserveAspectCrop")
        self.combo_fill.addItem("Fit to Screen", "preserveAspectFit")
        self.combo_fill.addItem("Stretch", "stretch")
        self.combo_fill.currentIndexChanged.connect(self._on_fill_changed)
        ctrl_row.addWidget(self.combo_fill)

        self.btn_random = QPushButton("Random Wallpaper")
        self.btn_random.setProperty("class", "secondary-btn")
        self.btn_random.clicked.connect(self.random_requested.emit)
        ctrl_row.addWidget(self.btn_random)

        self.chk_auto = QCheckBox("Daily Auto-Change")
        self.chk_auto.toggled.connect(self.auto_change_toggled.emit)
        ctrl_row.addWidget(self.chk_auto)

        ctrl_row.addStretch()
        info_layout.addLayout(ctrl_row)

        main_layout.addLayout(info_layout, 1)

    def set_current_wallpaper(self, image_path: Optional[str], title: Optional[str] = None):
        self.monitor.set_image(image_path)
        if image_path:
            clean_name = title or Path(image_path).stem
            self.title_label.setText(clean_name)
            self.path_label.setText(str(image_path))
        else:
            self.title_label.setText("No desktop wallpaper selected")
            self.path_label.setText("")

    def set_fill_mode(self, mode: str):
        idx = self.combo_fill.findData(mode)
        if idx >= 0:
            self.combo_fill.setCurrentIndex(idx)

    def set_auto_change(self, enabled: bool):
        self.chk_auto.blockSignals(True)
        self.chk_auto.setChecked(enabled)
        self.chk_auto.blockSignals(False)

    def _on_fill_changed(self, index: int):
        mode = self.combo_fill.itemData(index)
        self.fill_mode_changed.emit(mode)
