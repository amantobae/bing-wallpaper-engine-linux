from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor, QPainter
from PySide6.QtCore import Qt, Signal, QTimer

from ..config import APP_NAME

def create_default_tray_icon() -> QIcon:
    """Draw a clean vector-like tray icon if no image file is found."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Blue rounded square
    painter.setBrush(QColor("#0078d4"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 14, 14)

    # White 'B' and mountain symbol
    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setPixelSize(34)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(0, 0, 64, 60, Qt.AlignmentFlag.AlignCenter, "B")
    painter.end()

    return QIcon(pix)


class BingTrayIcon(QSystemTrayIcon):
    """System Tray integration for KDE Plasma desktop."""
    open_window_requested = Signal()
    next_wallpaper_requested = Signal()
    auto_change_toggled = Signal(bool)
    quit_requested = Signal()

    def __init__(self, parent=None):
        icon = create_default_tray_icon()
        super().__init__(icon, parent)
        self.setToolTip(APP_NAME)
        self._current_title: str = "Bing Wallpaper"
        self._auto_change_enabled: bool = False
        self._create_menu()
        self.activated.connect(self._on_activated)

    def _create_menu(self):
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #24252a;
                border: 1px solid #3b3e47;
                color: #f4f4f5;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
        """)

        self.action_header = QAction(APP_NAME, self)
        self.action_header.setEnabled(False)
        self.menu.addAction(self.action_header)

        self.action_current = QAction("Current: Loading...", self)
        self.action_current.setEnabled(False)
        self.menu.addAction(self.action_current)

        self.menu.addSeparator()

        self.action_next = QAction("Next Wallpaper", self)
        self.action_next.triggered.connect(self.next_wallpaper_requested.emit)
        self.menu.addAction(self.action_next)

        self.action_auto = QAction("Daily Auto-Change", self)
        self.action_auto.setCheckable(True)
        self.action_auto.triggered.connect(self._on_auto_toggled)
        self.menu.addAction(self.action_auto)

        self.menu.addSeparator()

        self.action_open = QAction("Open Gallery", self)
        self.action_open.triggered.connect(self.open_window_requested.emit)
        self.menu.addAction(self.action_open)

        self.action_quit = QAction("Quit", self)
        self.action_quit.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(self.action_quit)

        self.setContextMenu(self.menu)

    def set_current_title(self, title: str):
        self._current_title = title
        short_title = title if len(title) <= 28 else title[:25] + "..."
        self.action_current.setText(f"Current: {short_title}")
        self.setToolTip(f"{APP_NAME}\n{title}")

    def set_auto_change_state(self, enabled: bool):
        self._auto_change_enabled = enabled
        self.action_auto.setChecked(enabled)

    def _on_auto_toggled(self, checked: bool):
        self._auto_change_enabled = checked
        self.auto_change_toggled.emit(checked)

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.open_window_requested.emit()
